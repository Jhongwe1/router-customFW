# PREDICTIONS — Session B6, `R3-9`, block 4: `probe3` on the silicon, and the first card this project has run a machine over before power

**Written at the desk on 2026-08-31, before power.** Every value below was
measured on this host today or read out of a capture already committed, and none
of it is conditional on a reading taken at the bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in a new
file — `CORRECTIONS-block4.md`, beside this one.

**One power cycle.** `probe3` is the last thing in `R3` that needs one, and the
`FLR` bracket rides it because the bracket costs no cycle of its own.

⚠️ **This card was written on 2026-08-31 and the directory is named
`2026-09-01`, which is a PREDICTION of the seating day rather than a record of
anything.** A `bench/` directory carries the day its captures were taken —
block 3's card was written on 2026-08-30 into `bench/2026-08-31/`, and that
seating did happen on 2026-08-31. **If this one slips, the directory is
renamed before the first capture lands**, and every `--out` on this card with
it. Stating it because a date in a path reads like a fact, and this one is a
guess.

**What block 4 carries that block 3 could not.** Five things, and three of them
are instruments rather than readings:

| | |
|---|---|
| the **`M(T)` ladder** and the **retained bitmap**, `R3-9`'s two carried-forward instruments | `w-assoc` reported only the argmin, and *nothing evicted* and *this stride was never swept* were the same observation. The bitmap's boundary-point pattern was advertised in the block header and washed away by `bmp_clear()` before the read-back. Both are in the block now, and `docs/probe3-cells.md` § 6.2a owns their predictions |
| **Group F**, the memory-mapped SPI window | `SPEC.md` §17's last `FW-34` row. `LDR-42` closed the loader route on 2026-08-31 — the loader's only mention of `0xBD000000` is a `printf` argument — so a bare-metal payload with a calibrated timer is the only instrument left. § 6.8 owns it |
| the bracket driven by **`flrbracket run`** rather than by eye | the bracket has never been machine-driven. Its predecessor was a scratchpad script that got the six-digit/eight-digit comparison wrong on its first run, and the only direction it was ever shown to work in was the safe one |
| **the seconds between power off and power on**, written down | `MEM-17` measured DRAM keeping a previous cycle's `FLR` output across a power cycle and the retention window is **unbounded in both directions**, because the off duration was never recorded. It costs nothing |
| a card that a **machine has read before power** | `cardcheck commands` against the image's own declaration, `cardcheck numbers` against the artefacts, `check-predictions` for the mtime rule. § 10 |

---

## §0 THE CARD — every line that gets typed, in order

**This is the only part of this file that is read at the bench.** Everything
below it is the reasoning that produced it.

🔴 **Every row carries a terminator.** `console-capture.py capture` with neither
`--seconds` nor `--idle` **refuses** as of 2026-08-30. The numbers are sized
against the loader's *marginal* reply rate, **3,458–3,497 B/s** (`SPEC.md`
`LDR-40`, as corrected by `bench/2026-08-30/CORRECTIONS-block0.md` §7).

### The day before — the dry run, and it is not optional

```
/usr/bin/python3 tools/flrbracket.py --self-test
  50 passed, 0 failed

/usr/bin/python3 tools/flrbracket.py run --port /dev/ttyUSB0 \
    --stem K --suffix 0 --dst 80A00400 --src 000000 --bytes 100 \
    --echo-dir bench/2026-09-01 --dw-dir bench/2026-09-01 \
    --pre-dir /home/key/fwre-work/rebuild/bench-only/b6-20260901
  (no --go: it must print what it would send and exit without opening the port)
```

🔴 **The dry run is a containment test, not a rehearsal.** `run` refuses,
**before it opens the port**, to write an `H601`-overlapping read-back anywhere
inside this repository, and the pre-read anywhere inside it at all whatever the
window is. Those refusals are what the `h` and `c` rows below depend on, and a
refusal discovered at the bench costs a power cycle.

🟢 **量 2026-08-31, all four windows, `rc=0` each — and it needed no board,
which is the point: without `--go` the tool prints what it would send and never
opens the port, so this is desk work and not something to carry to the bench.**
What it confirmed, per window:

| | `0` / `6` | `h` / `c` |
|---|---|---|
| pre-read | `…/b6-20260901/K-p0`, `K-p6` — **outside** | `K-ph`, `K-pc` — **outside** |
| `FLR` echo | `bench/2026-09-01/K-flr0`, `K-flr6` | `bench/2026-09-01/K-flrh`, `K-flrc` — **inside, and correctly**: an echo holds addresses and no flash bytes |
| read-back | `bench/2026-09-01/K-rd0`, `K-rd6` | `…/b6-20260901/K-rdh`, `K-rdc` — **outside** |

🆕 **It also named a cell this card's § 2 does not list**: `K-no0`/`K-no6`/
`K-noh`/`K-noc`, the `N` the tool sends on a wrong echo. They are **not** in the
`cells` fence for the same reason block 3's `W-no` was not — they run only on a
branch, and a predicted cell that never ran is not a pass.

### Before power — at the desk, and it is four commands

```
sha256sum tools/rlxprobe/build/probe3/probe3.bin
  fc7b21d479478fcb925723237323176adc7946502a0e71588ae799a626e2824e

stat -c %s tools/rlxprobe/build/probe3/probe3.bin
  31536

/usr/bin/python3 tools/cardcheck.py numbers bench/2026-09-01/PREDICTIONS-B6-block4.md
  every row re-derived, 0 mismatched

/usr/bin/python3 tools/check-predictions.py bench/2026-09-01/PREDICTIONS-B6-block4.md
  0 of N captures came after the prediction   <- the correct answer before power
```

⚠️ **`cardcheck commands` is NOT on this list, and the reason is that it cannot
run here.** It reads `config/rlxfw-initramfs.tsv` — the declaration of an
*initramfs* — and `probe3` is a bare-metal payload with no filesystem and no
applets. Every line this card types at the prompt is a **loader** command, and
`cardcheck`'s loader verb table is what covers those. It is run as part of
`cardcheck --self-test`'s `B2` census and is not a per-card step here. **Stating
this is the point**: a card that quietly skipped a check it advertises would be
the shape `flashwin` cost this project a session over.

The host preflight — the long-lived WSL process, re-reading both busids, the NIC
at `10.1.1.2/24`, `/usr/bin/python3` and the board-off 3-second capture — is
`RUNSHEET` §B5's and is not restated here. One owner.

### 🔴 Write this down before the power switch, and it is a reading

```
power off at   __:__:__      power on at   __:__:__      seconds off: ____
```

`MEM-17` is *DRAM kept a previous cycle's written data across a power cycle* and
its own row says the duration was not recorded, so it has **no bound in either
direction**. `K-p*` below reads the same addresses on the other side of this
number. It costs no power cycle and no `FLR`.

### Power cycle 8 — `probe3`, the bracket, and the read-back. `bench/2026-09-01/`

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`OUT X` = `--out bench/2026-09-01/X` — **one token**, not two.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **K-A** | `CAP OUT K-A --esc 25 --esc-period 0.002 --seconds 40` | the ESC window, then `<RealTek>`; the 181-byte cold slice | — | no prompt → power off. That is the seating |
| **K-0r** | `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-01/K0-rescue.json` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **K-P0** | `CAP OUT K-P0 --send 'DW 8040D4A0 1' --seconds 4` | the word at `0x8040D4A0` = **`00000000`** | **71** | ≠ `00000000` → **STOP. Nothing is uploaded.** This is `R0`'s flash-write control and it is not optional |
| **K-P1a** | `CAP OUT K-P1a --send 'DW B8003108 1' --seconds 4` | four words — `TC0CNT`, `TC1CNT` = `00000000`, `TCCNR` = `C0000000`, `TCIR` = `80000000` | **71** | `TCCNR ≠ C0000000` → something writes it after `timer_init` and `M9` is wrong |
| **K-P1b** | `CAP OUT K-P1b --send 'DW B8003108 1' --seconds 4` | as `K-P1a` but with a **different** `TC0CNT` | **71** | 🔴 `TC0CNT` equal to `K-P1a`'s → the register is frozen and **Group T does not ship**. `probe3` still runs; Group F's timing legs come back as poison and § 6.8 says so |
| **K-P2a** | `CAP OUT K-P2a --send 'DW 80A02000 16' --seconds 5` | the head of the result block. ⚠️ **`524C5833` here is NOT a failure** — see § 3.1 | **213** | any of `5A5AA5A5` / `00000144` / `524C5831` / `524C5832` → an earlier payload's block is at this address and the block moves |
| **K-P2b** | `CAP OUT K-P2b --send 'DW 80A10000 16' --seconds 5` | high-entropy bias garbage: no word equal to an address in the window, no aligned `80xxxxxx`/`81xxxxxx`/`A0xxxxxx`/`B8xxxxxx`, no period, not sixteen zero bytes, no known magic | **213** | 🔴 any one of those → **the arena moves and `K-P2*` is re-run.** `MEM-14` is the standing proof that *"nothing has read it"* is not *"nothing writes it"* |
| **K-P2c** | `CAP OUT K-P2c --send 'DW 80A50000 16' --seconds 5` | as `K-P2b`, the middle of the arena | **213** | as above |
| **K-P2d** | `CAP OUT K-P2d --send 'DW 80A8FFC0 16' --seconds 5` | as `K-P2b`, the tail of the arena | **213** | as above |
| **K-P3** | `CAP OUT K-P3 --send 'DW 80A00000 2000' --seconds 20` | **23,527 bytes**, ≈6.13 s of reply | **23527** | `Unknown command !` (≈44 B) or a short whole-line reply → the loader will not take a four-digit decimal length. **The read-back below is 718 and three digits, so this seating is unaffected either way** — the cell is `P3`'s and it costs no cycle |
| **K-p0** | *(inside `K-P3`)* | the pre-`FLR` state of `0x80A00400`–`0x80A00700`, free, because `K-P3` spans them | — | — |
| **K-1** | `loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/bench-only/b6-20260901/probe3.bin --filename probe3 --rescue-report bench/2026-09-01/K0-rescue.json --expect-load 80500000 --yes` | **31,536** bytes accepted | — | any refusal → read it. **Never `--allow-autoexec`** |
| **K-2a** | `CAP OUT K-2a --send 'DW 80500000 8' --seconds 6` | `80500000: 3C1D8051 27BDBE20 3C088050 25087B30` · `80500010: 3C098050 25297E20 11090004 00000000` | **118** | any word differs → the wrong image, or a short transfer. § 4 decodes every one |
| **K-2b** 🔴 | `CAP OUT K-2b --send 'DW 8050000C 1' --seconds 4` | `8050000C: 25087B30 3C098050 25297E20 11090004` | **71** | ≠ → **STOP, do not `J`.** § 4.2: this is the head method and the two symbols it carries |
| **K-flr0 / K-yes0 / K-rd0** | `flrbracket.py run --port /dev/ttyUSB0 --stem K --suffix 0 --dst 80A00400 --src 000000 --bytes 100 --echo-dir bench/2026-09-01 --dw-dir bench/2026-09-01 --pre-dir /home/key/fwre-work/rebuild/bench-only/b6-20260901 --go` | **exit 0**, and `K-rd0.log` normalises equal to `bench/2026-08-24d/G8a-rd0.log` | 104 / 35 / **777** | 🔴 **exit 3/4/5/6 → read § 5.2's table before typing anything.** Exit 4 means the tool sent `N` and the loader confirmed the abort; the window was NOT read and that is the tool working |
| **K-flr6 / K-yes6 / K-rd6** | as above, `--suffix 6 --dst 80A00500 --src 060000` | `K-rd6` normalises equal to `bench/2026-08-24d/G8a-rd6.log` | 104 / 35 / **777** | as above |
| **K-flrh / K-yesh / K-rdh** 🔴 | as above, `--suffix h --dst 80A00600 --src 006000`, **`--dw-dir /home/key/fwre-work/rebuild/bench-only/b6-20260901`** | `K-rdh` normalises equal to `expect-h601-6000.txt` | 104 / 35 / **777** | 🔴 **`--dw-dir` is NOT under `bench/`.** These bytes are this unit's MAC and radio calibration. The tool refuses before opening the port if it is |
| **K-flrc / K-yesc / K-rdc** 🔴 | as above, `--suffix c --dst 80A00700 --src 006400`, **`--dw-dir` outside the repo** | `K-rdc` normalises equal to `expect-h601-6400.txt` | 104 / 35 / **777** | 🔴 **the canary page.** A difference here is a **finding, not a failure** — it is the page `FLS-21` saw move. Record it, do not `J`, and stop |
| **K-2d** | `CAP OUT K-2d --send 'DW 80500000 8' --seconds 6` | **byte-identical to `K-2a`** | **118** | changed → the `FLR` block reached the payload's head. Do not `J`. ⚠️ **32 bytes of 31,536 — this cannot find an arbitrary clobber** |
| — | — | — | — | — |
| **K-J** 🔴 | `CAP OUT K-J --send 'J 80500000' --seconds 90` | the banner, then every `rlxprobe:` line, then `rlxprobe: end` and the loader prompt back (`RESET=1` arms the watchdog and hands it back with no power cycle) | ≈**7,000** | no `rlxprobe: end` → read `H_PROGRESS` out of the block: it is a monotone ladder and says where the run stopped. § 7.4 |
| **K-rb** 🔴 | `CAP OUT K-rb --send 'DW 80A02000 718' --seconds 20` | **8,486 bytes**, 180 lines, ≈2.21 s of reply | **8486** | a short reply → **do not power off**; re-send. A truncated read-back is a capture defect that looks exactly like a payload defect, and `rbcheck` refuses rather than reporting on it |
| **K-rbp** | `CAP OUT K-rbp --send 'DW 80A02000 726' --seconds 20` | the same 718 words **plus the whole poison margin**: `w718`–`w725` all `DEADC0DE` | **8580** | any of `w718`–`w725` ≠ `DEADC0DE` → **the payload wrote past its own block.** § 6.2 |
| **K-off** | *record the time*, power off | — | — | — |

⚠️ **`K-rb` and `K-rbp` overlap on purpose.** `K-rb` is the read-back every tool
below parses; `K-rbp` is the over-run control and it is a second command because
`DW 80A02000 718` returns only `w718` and `w719` of the margin (`DW` rounds a
word count up to a multiple of four, `LDR-07`). Two commands, 0.06 s of reply
between them, and the alternative is a single 726-word read whose first 718
words are what every tool parses — which would make the control and the reading
the same capture, and a truncation would then take both.

## §1 The prefixes

`K` for this power cycle. **`N` and `Y` are skipped**, as in blocks 2 and 3:
they are the literal characters typed at the `FLR` confirmation prompt, and a
cell named `Y-…` beside a `--send 'Y'` is a reading waiting to be misfiled.
`Q` is `bench/2026-08-30`'s and is not reused, because a sweep that walks
captures back to predictions has to be able to tell them apart.

## §2 Cells, in order

```cells
bench/2026-09-01/K-A
bench/2026-09-01/K-P0
bench/2026-09-01/K-P1a
bench/2026-09-01/K-P1b
bench/2026-09-01/K-P2a
bench/2026-09-01/K-P2b
bench/2026-09-01/K-P2c
bench/2026-09-01/K-P2d
bench/2026-09-01/K-P3
bench/2026-09-01/K-2a
bench/2026-09-01/K-2b
bench/2026-09-01/K-flr0
bench/2026-09-01/K-yes0
bench/2026-09-01/K-rd0
bench/2026-09-01/K-flr6
bench/2026-09-01/K-yes6
bench/2026-09-01/K-rd6
bench/2026-09-01/K-flrh
bench/2026-09-01/K-yesh
bench/2026-09-01/K-flrc
bench/2026-09-01/K-yesc
bench/2026-09-01/K-2d
bench/2026-09-01/K-J
bench/2026-09-01/K-rb
bench/2026-09-01/K-rbp
```

🔴 **`K-rdh` and `K-rdc` are NOT in this list and that is the containment rule,
not an omission.** They are read-backs of `H601` windows; they land outside this
repository and `check-predictions` may never be pointed at them. `K-flrh` and
`K-flrc` — the echoes — are here, because an echo holds addresses and no flash
bytes, which is why `bench/2026-08-31/W-flrh.log` names `00006000` and is
correctly committed.

---

## §3 Group P — the preflight, and the one cell whose expectation changed

### §3.1 🔴 `524C5833` at `0x80A02000` is retention, not a failure

**`docs/probe3-cells.md` § 9's `P2` row owns this and it is not restated here.**
The magics that void `P2` are `5A5AA5A5`, `00000144`, `DEADC0DE`, `524C5831` and
`524C5832`; `524C5833` — `probe3`'s own — is not among them, and § 9 says why.

**`MEM-17` (量 2026-08-31) is that DRAM keeps written data across a power
cycle.** The last `probe3` seating was 2026-08-29 and the board has been powered
several times since, so:

> **PREDICTED: `K-P2a` reads bias garbage.** Three days and several boots is far
> outside anything `MEM-17` bounds, and the loader's own network stack has run
> over this region since.
>
> **If it reads `524C5833` instead, that is a `MEM-17` reading and a large
> one** — DRAM retention measured in days rather than in one power cycle — and
> the seating continues, because stage 0 poisons the whole block before the
> first cell. **It is not a stop.** Record the header words and carry on.
>
> **REFUTATION of the cell, not of the run:** `524C5831` or `524C5832` at
> `0x80A02000` means the block is on top of `probe1`'s or `probe2`'s, both of
> which hold measurements recovered from DRAM, and the base moves.

### §3.2 `K-P1a`/`K-P1b` and what an equal `TC0CNT` costs today

`P1`'s refutation is written against the **separated** pair and these two reads
are seconds apart, so equal readings mean the register is frozen. On 2026-08-29
Group T shipped (`t.cal` hi/lo came out **2.0003** against a predicted 2).

🆕 **What changed is the consequence.** Group F's seven timing legs are now
**gated on Group T** (`probe3.c`, `if (g_timer)`), so a frozen counter leaves
them at stage 0's poison rather than at a number. 量 (qemu) 2026-08-31: Malta
has no timer at `0xB8003108`, `g_timer` came back 0, and all seven legs read
`deadc0de` while `f.alias` and `f.live` still ran. **The emulator is the worked
example of this branch and it is the only environment that drives it.**

---

## §4 Which image landed, and why the head and not the tail

### §4.1 `K-2a`: the first eight words, and every one of them is decodable

| addr | word | instruction | what it pins |
|---|---|---|---|
| `80500000` | `3C1D8051` | `lui $29, 0x8051` | `_start`'s first instruction. The Makefile's `show` prints it and refuses to build if byte 0 is anything else |
| `80500004` | `27BDBE20` | `addiu $29, $29, -0x41E0` | `$29` = `0x8050BE20` = **`_stack_top`** |
| `80500008` | `3C088050` | `lui $8, 0x8050` | |
| `8050000C` | `25087B30` | `addiu $8, $8, 0x7B30` | `$8` = `0x80507B30` = **`_bss_start`** |
| `80500010` | `3C098050` | `lui $9, 0x8050` | |
| `80500014` | `25297E20` | `addiu $9, $9, 0x7E20` | `$9` = `0x80507E20` = **`_bss_end`** |
| `80500018` | `11090004` | `beq $8, $9, +4` | the `.bss` clear loop's exit test |
| `8050001C` | `00000000` | `nop` | the branch delay slot, filled by hand |

### §4.2 🔴 Why `K-2b` is a head cell and the tail method does not transfer

`bench/2026-08-31`'s image check read the **tail** — the last words before
`image_end` — and that works for a staged kernel image, which is a megabyte of
compressed payload followed by a known zero run. **`probe3` has no such tail**:
its image ends exactly at `_bss_start`, because `.bss` is not in the file, so
"the last word of the image" is an ordinary instruction with nothing to
distinguish it.

**The head carries what the tail was for.** `0x8050000C` and `0x80500014` are
the two halves of the linker's `.bss` extent, materialised into `addiu`
immediates by the assembler. **They move on every build that changes the size of
anything** — 量 2026-08-31: Group F took `_bss_start` from `0x80507230` to
`0x80507B30` — so a stale image is caught by the same word that proves the
transfer's head landed.

🟢 **And the two cells cross-check, because `_bss_start` IS the size.**
`docs/FINDINGS.md` row 60: the word at `0x8050000C` carries
`_bss_start = 0x80500000 + size`, exactly as `0x8050001C` carries
`__vmlinux_end` in an `nfjrom` — one linker constant, two linkers. So
`0x80507B30 − 0x80500000 = 31,536` is the **same number** `K-1` must report as
accepted, arrived at by a different route: the linker's symbol table on one side
and the loader's TFTP counter on the other.

⚠️ **What neither of them catches on its own: truncation.** A short transfer has
a correct head, and the head word states the size the image *should* be rather
than the number of bytes that landed. **It is the pair that closes it** — the
head says *this image is 31,536 bytes long* and `K-1` says *31,536 bytes were
accepted*, and a disagreement is a short transfer. Stated here because reading
`K-2b` alone as an upload check is the mistake this row exists to prevent.

🔴 **And `LDR-07`'s rounding is why `K-2b` is one command and not four.**
`DW 8050000C 1` rounds the word count up to a multiple of four and prints
`0x8050000C`–`0x80500018` — both symbols and the branch that uses them, for the
price of a one-word request.

---

## §5 The bracket, and it is machine-driven for the first time

### §5.1 What changes, and what does not

The four windows, the four RAM destinations and the expectation files are block
3's, unchanged: `0x000000` (loader head), `0x060000` (the `cr6c` header),
`0x006000` (`H601`) and `0x006400` (the canary page `FLS-21` measured moving).
**What changes is who reads the echo.**

`tools/flrbracket.py` (2026-08-31, 50 controls over seating 7's own nine echoes,
41 mutants) classifies the confirmation reply as `PROCEED` / `ABORT` / `REFUSE`
and sends `Y`, `N` or nothing. Its predecessor was a scratchpad script that
**compared the six-digit source as typed against the loader's eight-digit echo**
and aborted a correct read; that defect is `M2` in the mutation suite and it
must turn `P1` red.

🔴 **The untested direction is the dangerous one and it stays untested here.**
Nothing has shown the tool refuses a *wrong* echo **on the device** — only that
it refuses one in a fixture, against nine recorded replies. This seating does
not test that either, because a wrong echo is not something the card can ask for.
What it does is put a machine between a human and four `Y` keystrokes.

### §5.2 The exit codes, and only one of them means the window was read

| exit | meaning | what to do |
|---:|---|---|
| **0** | `PROCEED`, `Flash Read Successed!`, read-back taken | next window |
| **3** | `REFUSE` — nothing was sent; the board may still be at a confirm prompt | 🔴 **the board is mid-command.** Capture the port before typing: `CAP OUT K-stuck --seconds 6`. Do not `J` |
| **4** | `ABORT` — the echo named another transfer, `N` was sent, `Abort!` came back | a finding about the loader or the arguments. Record and stop the bracket; the rest of the card may continue |
| **5** | `ABORT` — `N` was sent and the abort was **not** confirmed | 🔴 needs a person. Capture the port. Do not `J` |
| **6** | `PROCEED` but no `Flash Read Successed!` | the region did not read. That is the finding; record it |
| **2** | refused before anything was sent (bad arguments, containment) | a card error or a path inside the repository. Fix it at the desk; nothing was spent |

### §5.3 Ordering, and it is binding

🔴 **`FLR` writes the TFTP length global, so the bracket must come after `K-1`
and no `put` may follow it.** `J` needs no TFTP global, so `put` → bracket → `J`
is legal on one cycle. **If `K-2a` or `K-2b` disagrees, power off** — the fix is
a second `put` and the bracket has not run yet, so nothing has been spent.

---

## §6 The read-back, and the two words that are a control

### §6.1 `DW 80A02000 718` — the arithmetic

`RB_WORDS` is **718**: 64 header + 205 cell results + 16 rows × 8 + 256
scratchpad bitmap words + 64 retained bitmap words + the seal. It was 707 until
this session and 641 before that; `tools/rbcheck.py` reads the layout out of the
block's own `H_LAYOUT_*` header words, so all three parse.

`LDR-07`'s model gives **8,486 bytes**, 180 lines, **2.210 s** at 3,840 B/s —
0.04 s more than the 707-word block and 88 % of the largest `DW` this loader has
ever executed (820 words / 9,661 bytes, 量 `H2g`). Three digits, so it does not
depend on `K-P3`'s answer.

### §6.2 🔴 The poison margin stopped being luck this session

`DW` rounds a word count **up** to a multiple of four. 641 returned 644 and
`w641`–`w643` of the poison margin came back free; 707 returned 708 and only
`w707` did; **718 returns 720 and `w718`–`w719` do.** Each of those was the
remainder falling out that way.

🆕 `probe3.c` now carries `rb_readback_shows_poison` — a compile-time assertion
that **refuses to build a layout whose `RB_WORDS` is a multiple of four**,
because such a block returns no poison word at all and the over-run control
stops existing without saying so. `tools/test-rlxprobe.sh` `SM3b` is the
mutation that proves it fires, and `SM3c` is its population control.

> **PREDICTED: `w718` and `w719` = `DEADC0DE`, and `K-rbp` shows `w718`–`w725`
> all `DEADC0DE`.**
>
> **REFUTATION:** any of them holding data means the payload wrote **past** its
> own block. The overrun goes upward from the seal, so `w718` is the first word
> it reaches — that is why one visible poison word is enough and eight is
> better.

---

## §7 The three groups this seating exists for

### §7.1 The `M(T)` ladder — one discriminator reported four ways

Copied from `docs/probe3-cells.md` § 6.2a, which owns it. **Not re-derived
here**: a second derivation in a card is a second owner.

> **PREDICTED: `w.assoc.mt = 09 05 03 03`.** Direct-mapped predicts
> `09 05 03 02`. **One byte carries the whole difference** — at `C/8`, `C/4` and
> `C/2` the two geometries give the same minimum `M`, and only `T = C` separates
> them (two-way needs 3, direct-mapped needs 2).
>
> **PREDICTED: `w.assoc.mtcap = 00 00 00 00`.** `A_ASSOC_SPAN` is `0x38000` =
> 229,376 B and the largest request is 12 × 16,384 = 196,608 B, so the arena
> refuses nothing. 量 2026-08-29 `w.assoc.capped=00000000` agrees, computed by
> different code from the same span.
>
> **REFUTATION:** any byte outside {2, 3, 5, 9, `0xFE`} at its own stride, or a
> ladder that is not monotonically non-increasing in `T`, and the eviction model
> behind `CPU-25` is wrong rather than the associativity. A `0` at `C/2` or `C`
> would mean twelve victims all mapping to one set evicted nothing, which
> refutes the whole walk.

⚠️ **This does not make `CPU-25` more certain and the write-up must not say it
does.** 量 2026-08-29 `w.assoc.tm = (8192, 3)` already excluded direct-mapped —
the search keeps the strictly smaller `M`, so a direct-mapped part would have
reported `(16384, 2)`. What changes is that a reader can now check that in the
block instead of following an argument about tie-breaking.

### §7.2 The retained bitmap — the second route, and it is a shape not a count

> **PREDICTED, two-way: the FRESH victims arrive in `{k, k+256}` pairs.** At the
> boundary point the victims are 32 B apart, so the set index advances by two
> per victim; under two-way (512 sets) victims `k` and `k+256` share a set, and
> under direct-mapped (1,024 sets) no two ever do. 量 2026-08-29
> `bmp.rerun.fresh = 20`, so **ten pairs**.
>
> **PREDICTED, direct-mapped: the same 20 arrive as isolated singletons.**
>
> **PREDICTED: `bmp.kept = 00000200`** (512 nibbles, the whole boundary point)
> and **`bmp.rerun.fresh` agrees with the recount over `O_BMPK`** — two numbers
> over one region, computed by different code at different times.
>
> **REFUTATION:** 20 FRESH as 10 pairs versus 20 singletons is a difference no
> summary count can show, and the two hypotheses give the **same** count. **If
> the FRESH victims are neither — some paired, some not — the pairing model is
> wrong and the ladder above is the only route left.** An odd
> `bmp.rerun.fresh` refutes pure pairing immediately.

### §7.3 Group F — and the answer is asymmetric, so write it asymmetrically

Copied from `docs/probe3-cells.md` § 6.8.2 and § 6.8.3.

> **PREDICTED `f.sfcr = 3FC00000`** (量 `REG-13`, at the prompt: `SPI_CLK_DIV`
> `001B` = DIV 4, written by stage 2).
> **PREDICTED `f.alias = 00000000`** — `0xBD000000` and `0xBFC00000` are the
> same flash. **PREDICTED both bytes of `f.live` ≥ 10.**
> **PREDICTED `f.faults = 00000000`.**
> **PREDICTED `f.win.str` ≈ 21,300–21,700 ticks**, because a 1,024-byte stride
> defeats any buffer this controller plausibly has. **`f.win.seq` is the
> reading.**

| `R = f.win.str / f.win.seq` | what it establishes |
|---|---|
| **≤ 1.15** | **no buffering.** `FW-34`'s last row CLOSES: §19.7.2's ≤9× is 9× |
| **1.15 – 1.8** | indeterminate, and it is reported as that |
| **≥ 1.8** | the window buffers; implied burst ≈ **4 R bytes**. `FW-34` NARROWS |

🔴 **The control on the verdict:** `f.dram.str / f.dram.seq` must be **strictly
less** than `R`. A strided DRAM read crosses SDRAM rows and is expected to be
slower on its own account; if the DRAM ratio is as large, the difference belongs
to the loop and this cell says nothing about the window.

🔴 **THE ASYMMETRY.** Group F times **data-side** `lw`; §19.7.2's amplification
is **instruction-fetch side**. They meet because stage 1 executes in KSEG1, so
its fetches are single-word uncached bus reads exactly like these loads — but
*exactly like* is an argument, not a measurement. So **`R ≤ 1.15` closes
`FW-34`** and **`R ≥ 1.8` only narrows it**.

🟢 **And the same six words answer a second question.** `f.win.str / 1024` at
**20.6 ticks ± 15 %** establishes *72 SPI clocks*, *DIV 4* **and** *the
datasheet's `DRAM Clock` is `CLK-02`'s 200 MHz* — all three at once, and
`notes/kernel-build.md` § 20.5 records that nothing in this repository has ever
asserted that last identification. ≈82 means DIV 16 is still in force; ≈9 means
the strided leg is buffered too and `R` is void rather than small.

⚠️ **It does not replace § 20.5's `FLR` cell.** `LDR-42`: `FLR` reads through
`SFDR` and Group F reads through the memory-mapped window — **two ports of one
controller.**

🔴 **And a reading that WRAPPED aliases to a small number.** `TC0CNT` wraps every
142,858 ticks and `tc_ticks` is valid for one wrap; Group F's predicted band is
1.5 ms, and the worst case the model allows — DIV 16, per-word re-issue — is
**84,275 ticks = 5.9 ms**, 59 % of a wrap. **Any leg below `f.dram.str`, or a
`f.win.str` under ~5,000 ticks, is consistent with a wrap** and the reading is
not a duration. Read `f.sfcr` first: `3FC00000` is DIV 4 and the 1.5 ms band
applies. § 6.8.3.

### §7.4 If `K-J` does not reach `rlxprobe: end`

`H_PROGRESS` (word 2) is a monotone ladder and the block says where the run
stopped rather than leaving it to be inferred. `0xA8` is **new this session** —
`P_FLASHWIN`, appended between `P_ISC` (`0xA0`) and `P_RESTORED` (`0xB0`) rather
than renumbering, so every older block still compares word for word.
`tools/rbcheck.py` names the stage.

**Group F is stage 10, last before the restore**, because it is the first time
this payload reads an address space outside DRAM and the SoC register block.
Everything Groups H…S measured is in the block before it starts.

---

## §8 What this block cannot show

| | |
|---|---|
| **the flash byte count** | the bracket samples **1,024 of 4,194,304 bytes = 0.0244 %** and reads 512 of `H601`'s 8,192. It cannot see two writes that cancel and it cannot see a write outside the four windows. `RUNSHEET` `G8b` forbids *"not one flash byte is written"* without a full re-dump, and this seating runs none |
| **the D-side geometry** | Group V is armed only if `c-A` shows a stale line, and `c-A` came back negative on 2026-08-29. `CPU-25`'s 8 KiB D-cache is still a build constant |
| **whether `0xBFC00000` decodes the whole 4 MiB** | Group F masks every leg to 64 KiB precisely because that extent is measured nowhere. A buffer of 64 KiB or more would be inside the mask; the absolute table in § 7.3 is what would show it |
| **that `flrbracket` refuses a WRONG echo on the device** | § 5.1 |

---

## §9 The numbers this card states, and where each comes from

```cardnum
probe3.bytes	31536	size tools/rlxprobe/build/probe3/probe3.bin
probe3.sha256	fc7b21d479478fcb925723237323176adc7946502a0e71588ae799a626e2824e	sha256 tools/rlxprobe/build/probe3/probe3.bin
probe3.w0	3C1D8051	word32 tools/rlxprobe/build/probe3/probe3.bin 0x00
probe3.w1	27BDBE20	word32 tools/rlxprobe/build/probe3/probe3.bin 0x04
probe3.w2	3C088050	word32 tools/rlxprobe/build/probe3/probe3.bin 0x08
probe3.w3	25087B30	word32 tools/rlxprobe/build/probe3/probe3.bin 0x0C
probe3.w4	3C098050	word32 tools/rlxprobe/build/probe3/probe3.bin 0x10
probe3.w5	25297E20	word32 tools/rlxprobe/build/probe3/probe3.bin 0x14
probe3.w6	11090004	word32 tools/rlxprobe/build/probe3/probe3.bin 0x18
probe3.w7	00000000	word32 tools/rlxprobe/build/probe3/probe3.bin 0x1C
rb.reply	8486	dwreply 718
rbp.reply	8580	dwreply 726
p3.reply	23527	dwreply 2000
```

🔴 **Every row above is re-derived by `cardcheck numbers`, not transcribed.**
The nine image words are read out of the `.bin` the card names, at the byte
offsets the loader will print them from; the three reply sizes go through
`tools/reply-size.py`'s model, which is the one owner of `LDR-07`.

⚠️ **Three numbers on this card are deliberately NOT in the fence**, because
nothing here can compute them: `31,536` appears twice (once as `probe3.bytes`,
once in `K-1`'s expectation) and the second is a transcription; the **181-byte
cold slice** is `bench/2026-08-30`'s reading, not this session's artefact; and
the `≈7,000` for `K-J` is **推**, labelled as one: 量 **6,439 bytes** of UART
under qemu this session (`qemu/2026-08-31b/probe3.txt`, prefixes stripped), and
the device run is longer because Group V is void under qemu and will run on
silicon. `docs/probe3-cells.md` §4's own estimate is ≈7 KB / 1.9 s and this
agrees with it. **The `--seconds 90` terminator is ~4× that at 3,840 B/s**, so
the cell does not depend on the estimate being right.

## §10 The check

```
/usr/bin/python3 tools/cardcheck.py numbers bench/2026-09-01/PREDICTIONS-B6-block4.md
/usr/bin/python3 tools/check-predictions.py bench/2026-09-01/PREDICTIONS-B6-block4.md
```

**`0 of 25` before the seating, and that is the correct answer.** A block written
before its power cycle must report that none of its captures came after it.

🆕 **This is the first card in this project that a machine has read before the
board was plugged in.** `cardcheck numbers` re-derives every row of § 9 from the
artefacts the card names; `check-predictions` enforces the mtime rule. Neither
existed when block 3 was written, and block 3's own §10 records that its 36-of-36
re-derivation was done by an uncommitted scratchpad script with no controls.
