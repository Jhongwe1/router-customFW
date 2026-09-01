# PREDICTIONS — Session B7, `R4-2`, block 6: the operator's card for this seating, the `FLR` bracket that rides it, and the loop closed without touching power

**Written at the desk on 2026-09-01, twenty-fourth segment, before power.**
Every number below was re-derived on this host tonight from a file already
committed, or from an image already staged. Nothing here is conditional on a
reading taken at the bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in
`CORRECTIONS-block6.md`, beside this one.

**One power cycle**, shared with `bench/2026-09-01/PREDICTIONS-B7-block5.md`,
which was frozen earlier the same day and is **not touched by this file**.

---

## 0. What this file is, and the three defects it exists to repair

**① Block 5 froze 24 cells and no command rows — the first card in this project
with none.** 量: `grep -c -- --send bench/2026-09-01/PREDICTIONS-B7-block5.md`
returns **0**, against 30 for block 2, 31 for block 3 and 15 for block 4. Its
`sent` column names what goes on the wire (`DW 8040D4A0 1`, `J BFC00000`) but
not the instrument, the output path or the terminator. **This file is the sole
owner of what gets typed this seating**, for block 5's cells and its own.
It does **not** restate block 5's predictions: those have exactly one owner and
it is block 5.

**② The stem `Y` collides with the `FLR` confirmation character**, and seating
8's card had already written the rule. `bench/2026-08-31c/PREDICTIONS-B6-block4.md`
§1: *"`N` and `Y` are skipped, as in blocks 2 and 3: they are the literal
characters typed at the `FLR` confirmation prompt, and a cell named `Y-…`
beside a `--send 'Y'` is a reading waiting to be misfiled."* Block 5 froze
`Y-*` anyway. **The 24 frozen names do not move** — a frozen block is frozen —
but nothing new is added under that stem: **this block's cells are `T-*`**, so
`T-yes0` is the only kind of cell in this seating whose name means *the letter
`Y` was typed*. ⚠️ The collision is recorded, not fixed; block 5's names stand
as written.

**③ A card that is not named `PREDICTIONS-*.md` is outside the population its
own checker sweeps.** 讀 `tools/cardcheck.py`: `B1`/`B2`/`B9` walk `bench/` and
select `fn.startswith("PREDICTIONS-") and fn.endswith(".md")`.
`tools/check-predictions.py` `sweep` globs `**/PREDICTIONS-*.md` on the same
rule. A file called `CARD-B7.md` would be checkable only when named explicitly
on a command line and would vanish from both sweeps **silently** — which is the
failure mode this repository writes controls to prevent. Hence the name. ⚠️
**The glob is still a filter that drops silently for anyone who picks another
name**, and widening it is carried forward rather than done in the hour before
power.

---

## 1. The terminator on every row is a measured quantity, not a habit

🔴 **`console-capture.py`'s own docstring says `--idle` is a trap**, and it is
right: *"the interval `D1` measures is a silence … an `--idle` shorter than
that silence ends the capture inside the gap and the reading becomes `the
banner never came`."* `LOOP-2` asks for `--idle` anyway, because `V-3`, `W-3`
and `X-3` each held the port **45.1 s** for a boot that ends in 7.26 s.

**Both are right, and the way to have both is to measure the silence first.**
量 2026-09-01 at the desk, over every committed capture that carries a boot,
from the `.timing` files (`<byte-offset> <seconds-since-start>` per read):

| population | n | largest silence **inside** the wanted region | where |
|---|---:|---:|---|
| cold power-up to `<RealTek>` (`A-catch`, `V/Z/W/X/K*-A`) | 14 | **1.644 s** | byte ≈118, immediately after the `---RealTek(RTL8196E)…` banner line |
| watchdog-reset boot to `<RealTek>` (`D1`, `H3a`, `H1b`, `H2a`, `K2-J`) | 5 | **1.565 s** | the same gap, at a different absolute offset |
| `quietm`/`quietmc` boot to a shell (`V-3`, `W-3`, `X-3`) | 3 | 🔴 **4.576 s** | byte **350**, four fifths of the way through an 849-byte log |
| a one-line `DW` reply (`K-P0`, `K-2a`, `W-5b`) | 3 | **0.015 s** | — |

🔴 **The third row is the one that matters and it refutes the obvious choice.**
An `--idle 3` on the boot cell — the number the cold and warm rows would
justify — **truncates `T-3` at byte 350 and loses 497 of its 849 bytes**, and
the log would look like a boot that stopped rather than an instrument that
gave up. The threshold is a property of the *cell shape*, not of the tool.

**So every row below carries `--idle` sized against its own population, AND a
`--seconds` ceiling.** The ceiling is not belt-and-braces: `--idle` cannot
terminate a capture that is still receiving bytes, and the one failure this
seating can actually produce — a missed ESC window, after which the vendor
firmware talks for about two minutes — is exactly that case.

| cell shape | `--idle` | ratio to the largest silence measured | `--seconds` ceiling |
|---|---:|---:|---:|
| one-line `DW` | 2 | 133× | 6–8 |
| loader boot behind an ESC phase | 3 | 1.82× the 1.644 s gap | 25–45 |
| `quietmc` to a shell (`T-3`) | **8** | **1.75×** the 4.576 s gap | 45 |
| a shell command (`T-5b`) | 3 | 200× | 15 |

⚠️ **Where `--idle` does *not* save anything on this card, said plainly.**
On every cell that catches an ESC window the hold is `--esc`/`--esc-after` plus
the idle tail, and the ESC phase is a fixed loop that runs to its deadline
whatever the board does. `LOOP-2`'s 37.8 s of waste was measured on `V-3`,
`W-3` and `X-3`, which stream **no ESC at all** (`esc: {}` in all three
`.meta.json`). **`T-3` is the cell shaped like those, and it is the one this
card actually shortens** — 45.1 s to about 15.3 s. On the twenty reset cells
the saving is real but smaller, and the ESC window is the term that dominates.
🔴 **Stating it because "the card now uses `--idle`" would otherwise read as a
claim that the whole 37.8 s came back, and it does not.**

**`--esc-after 10` on every reset**, which is **2.47×** the largest
watchdog-reset time-to-prompt this project has measured (4.051 s, `K2-J`;
the other four are 2.200, 2.241, 2.747, 3.154). The failure it buys margin
against is a missed ESC window, and that costs a power cycle — the most
expensive unit here — so the margin is bought on purpose.

**Refutation of this section, written now**: any `Y-*` or `T-*` capture whose
`.meta.json` `stop_reason` reads `--idle …` **and** whose `.log` does not
contain the string that cell predicted → the threshold was too small and the
whole table is wrong. That is a defect in this card, not in the board, and it
is recorded as one.

---

## 2. Block 5's twenty-four cells, as the operator runs them

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
`OUT X` = `--out bench/2026-09-01/X` — **one token, not two.**

🔴 **Predictions for these cells live in block 5 and are not repeated here.**
This table is commands, expected reply **sizes**, and stop conditions.

| # | typed | bytes | 🔴 stop if |
|---|---|---:|---|
| **`Y-A`** | `CAP OUT Y-A --esc 25 --esc-period 0.002 --idle 3 --seconds 45` | — | no `<RealTek>` → power off; that is the seating. Vendor boot text instead → the ESC window was missed; power-cycle and retry once |
| **`Y-ab`** | `CAP OUT Y-ab --send 'DW 8040D4A0 1' --idle 2 --seconds 6` | **71** | ≠ `00000000` → **STOP. Nothing else runs.** Block 5 §5 |
| **`Y-wd0`** | `CAP OUT Y-wd0 --send 'DW B800311C 1' --idle 2 --seconds 6` | **71** | bit 20 already set → `Y-wd1` is uninterpretable. Run it anyway, record the pair, close that row 未定 |
| **`Y-j1`** 🔴 | `CAP OUT Y-j1 --send 'J BFC00000' --esc-after 12 --esc-period 0.002 --idle 3 --seconds 30` | — | nothing but the echo → **the board is wedged. Power-cycle, and do not repeat `J BFC00000`.** That is the most valuable outcome in block 5 and it is recorded, not retried |
| **`Y-wd1`** | `CAP OUT Y-wd1 --send 'DW B800311C 1' --idle 2 --seconds 6` | **71** | — |
| **`Y-r02` … `Y-r20`** | `CAP OUT Y-rNN --send 'J BFC00000' --esc-after 10 --esc-period 0.002 --idle 3 --seconds 25`, **nineteen times**, `NN` = `02`…`20` | — | any capture with **no `<RealTek>`**: a short log (echo only) is a wedge, a long one is a missed ESC window. Either way **stop the run and record which `NN`** — the count is the cell |

⚠️ **`Y-j1` gets `--esc-after 12` and the repeats get 10.** The first one is
the one that can wedge, and 12 s of silence in its log is a cleaner reading of
*wedged* than 10 s is. It is two seconds, spent once.

⚠️ **The `--esc-after` stream and block 5 §2.1's timing cell.** ESC goes on the
wire within about 2 ms of the send, while the board is still spinning at
`0x804092EC`, so it cannot be echoed until after the reset. **The gap §2.1
wants is therefore read to the first byte that is not `0x1B`**, and that rule
is written here rather than decided while reading the file.

---

## 3. The `FLR` bracket — new claim: twenty watchdog resets change no flash

Runs **after `Y-r20`**, at the `<RealTek>` prompt, on the same power cycle.

**Why it belongs on this seating and not the next one.** `R4` builds a loop
that will issue this reset hundreds of times unattended. *A scripted reset
writes no flash* is a sentence that loop leans on and nothing in this
repository has measured. The bracket costs no power cycle of its own.

### 3.1 The windows, and why the destinations are new

| suffix | flash source | RAM destination | what it is |
|---|---|---|---|
| `0` | `0x000000`+256 | `0x80A00C00` | the loader head |
| `6` | `0x060000`+256 | `0x80A00D00` | the `cr6c` header |
| `h` 🔴 | `0x006000`+256 | `0x80A00E00` | `H601` — this unit's MAC and radio calibration |
| `c` 🔴 | `0x006400`+256 | `0x80A00F00` | the canary page `FLS-21` measured moving |

**The four sources are the same four as seating 8**, deliberately: the claim is
a comparison against the 2026-08-16 dump and against `bench/2026-08-31c`, and a
comparison needs the same windows.

🔴 **The four destinations have never been an `FLR` destination in this
project.** 量: `grep -rl 80A00C00 bench/` returns nothing, and every committed
bracket used `0x80A00400`–`0x80A00700`. This is not tidiness. `MEM-17` measured
DRAM retaining a previous cycle's `FLR` output across a power cycle, which is
what voided seating 8's carded round on cycle 6 — four pre-reads came back
equal to the flash and *the `FLR` wrote* stopped being measurable. **A
destination that has never held this content cannot be pre-filled with it.**

### 3.2 The rows

Driven by `tools/flrbracket.py run`, which does the pre-read, the `FLR`, the
`Y` and the read-back itself, and refuses **before it opens the port** if a
capture is aimed somewhere it may not go.

```
/usr/bin/python3 tools/flrbracket.py run --port /dev/ttyUSB0 \
    --stem T --suffix <s> --dst <dst> --src <src> --bytes 100 \
    --echo-dir bench/2026-09-01 --dw-dir <dw> \
    --pre-dir /home/key/fwre-work/rebuild/bench-only/b7-20260901 --go
```

| suffix | `--dst` | `--src` | `--dw-dir` | predicted |
|---|---|---|---|---|
| `0` | `80A00C00` | `000000` | `bench/2026-09-01` | `T-rd0` normalises equal to `bench/2026-08-24d/G8a-rd0.log` and to `bench/2026-08-31c/K-rd0.log` |
| `6` | `80A00D00` | `060000` | `bench/2026-09-01` | `T-rd6` normalises equal to `bench/2026-08-24d/G8a-rd6.log` and to `bench/2026-08-31c/K-rd6.log` |
| `h` 🔴 | `80A00E00` | `006000` | `/home/key/fwre-work/rebuild/bench-only/b7-20260901` | `T-rdh` normalises equal to `…/b7-20260901/expect-h601-6000.txt` |
| `c` 🔴 | `80A00F00` | `006400` | `/home/key/fwre-work/rebuild/bench-only/b7-20260901` | `T-rdc` normalises equal to `…/b7-20260901/expect-h601-6400.txt` |

Per window: `T-p<s>` **104**-byte `FLR` echo → wrong: `T-flr<s>` 104,
`T-yes<s>` 35, `T-rd<s>` and `T-p<s>` **777** bytes each.

🟢 **The dry run ran at the desk tonight, all four windows, `rc=0` each, and
both containment negative controls fired `rc=2`** — the `h` read-back aimed
inside the repository was refused by name, and so was a pre-read aimed inside
it whatever the window. `flrbracket --self-test`: **50 ok, 0 FAIL**.

🟢 **The comparison targets were checked at the desk too, and the check has a
positive control**: `flashwin normalise` makes `K-rd0` and `G8a-rd0` **equal**
(576 bytes each), `K-rd6` and `G8a-rd6` **equal**, and window `0` and window
`6` **different from each other** — so normalisation is not erasing the
content it is being asked to compare.

### 3.3 What this bracket can and cannot say

* **Can**: after `Y-A` through `Y-r20` — one cold boot and twenty watchdog
  resets — 1,024 flash bytes in four windows are byte-identical to the
  2026-08-16 dump.
* 🔴 **Cannot**: *not one flash byte is written.* 1,024 of 4,194,304 is
  **0.0244 %**. It sees no write outside the windows, it cannot see two writes
  that cancel, and **no full re-dump runs on this seating**. `RUNSHEET` `G8b`
  is unchanged and the forbidden sentence stays forbidden.
* ⚠️ **`H601` reach is unchanged at 512 of 8,192 = 6.3 %**, because these are
  the same two `H601` pages seating 7 and 8 read. The other 93.7 % is still
  unchecked.

**否證**: any window that does not normalise equal → **stop, do not `J`**,
record it. On `c` a difference is a **finding, not a failure** — it is the page
`FLS-21` saw move.

**The pre-read is the control and it can void the bracket.** If `T-p<s>`
normalises **equal** to the expectation before the `FLR` has run, that window's
read-back proves nothing; `flrbracket` prints the warning and the window is
recorded void with `MEM-17` as its reason, exactly as cycle 6 was.

---

## 4. Closing the loop — `edit → result` with the power switch never touched

Runs **after the bracket**. This is the half of `D2` that *the prompt is
reachable* does not reach.

🔴 **Why this order is the only one that works.** `FLR` writes the loader's
TFTP length global, so a `put` after it is broken; and after `J 80500000` the
loader is gone. One power cycle cannot hold both — **unless a scripted reset
restores the loader**, which is precisely what block 5 is testing. So the
bracket runs first, `T-rz` resets, and the upload happens on a loader that came
back without the power switch.

| # | typed | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **`T-rz`** | `CAP OUT T-rz --send 'J BFC00000' --esc-after 10 --esc-period 0.002 --idle 3 --seconds 25` | `Reboot Result from Watchdog Timeout!`, then `<RealTek>` | — | no prompt → power off. The bracket and block 5 are already recorded |
| **`T-ab`** | `CAP OUT T-ab --send 'DW 8040D4A0 1' --idle 2 --seconds 6` | `00000000` | **71** | ≠ → **STOP, upload nothing.** The one command on this card that could write flash is the one that follows |
| **`T-0r`** | `/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-01/T0-rescue.json` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **`T-0t`** | `CAP OUT T-0t --send 'DW 805FB3F0 8' --idle 2 --seconds 8` | two lines of DRAM. **Record both.** Line 1 must **not** be sixteen zero bytes | **118** | line 1 already all-zero → `T-2c`'s first half is void this seating; say so and carry on |
| **`T-1`** | `/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin --filename rlxfw-quietmc --rescue-report bench/2026-09-01/T0-rescue.json --expect-load 80500000 --yes` | **1,029,120** bytes accepted | — | any refusal → read it. **Never `--allow-autoexec`** |
| **`T-2a`** | `CAP OUT T-2a --send 'DW 80500000 8' --idle 2 --seconds 8` | `80500000: 00000000 00008021 40906000 00000000` · `80500010: 00000000 00000000 3C108060 2610B400` | **118** | the word at **`0x8050001C`** ≠ `2610B400`, or **`0x80500018`** ≠ `3C108060` → the wrong image |
| **`T-2b`** | `CAP OUT T-2b --send 'DW 80540000 1' --idle 2 --seconds 6` | `80540000: 162DC569 E3ADCA96 CDB49F15 69045643` | **71** | `AFBD0BEE …` → `quietm`, not `quietmc`. Anything else → neither |
| **`T-2c`** | `CAP OUT T-2c --send 'DW 805FB3F0 8' --idle 2 --seconds 8` | line 1 = **sixteen zero bytes**; line 2 **byte-identical to `T-0t`'s line 2** | **118** | line 1 ≠ 0 → short transfer. line 2 moved → the write ran past `image_end` |
| **`T-3`** 🟢 | `CAP OUT T-3 --send 'J 80500000' --idle 8 --seconds 45` | 🔴 **byte-identical to `bench/2026-08-31b/X-3.log`, 849 bytes**, sha256-16 `8317e7c9fe6eb60f` | **849** | a difference in the bytes is a finding about the image |
| **`T-5b`** | `CAP OUT T-5b --send 'cat /proc/version' --idle 3 --seconds 15` | `… (key@K) … #1 Sun Aug 30 18:56:00 CST 2026`, sha256-16 `af2981649f1eb541` | **111** | `18:56:50` → `loudmc` booted. `23:39:33` → `quietm`. `#1526` / `admin@office.hopeiot` → **the vendor's**, and the whole loop closure is unattributed |

### 4.1 What `T-2a` proves here that it did not prove in block 3

🔴 **A watchdog reset re-stages `0x80500000` from flash** (seating 8, reel
segment 7). So when `T-2a` runs, the alternative to *my image is there* is not
an empty address — it is **the vendor's image, freshly written by the loader on
the reset a minute earlier**. The two head words `3C108060 2610B400` therefore
discriminate *the upload landed* against *the reset's own staging is still
there*, which is a stronger reading than the same cell gave on any previous
seating. Written here because the cell looks unchanged and is not.

### 4.2 The claim, and its refutation

> **主張**: from a board at a `<RealTek>` prompt, a committed script can reset
> it, recover the loader, upload a kernel and boot it to a shell, **with no
> physical contact**. `T-rz` → `T-3` is that sequence and every step is a
> capture.

> **否證 ①** — `T-rz` returns no prompt. The reset does not survive an `FLR`,
> and the loop needs a power cycle between a flash read and an upload.
> **否證 ②** — `T-1` is refused, or `T-2a` shows the vendor's staged image.
> The TFTP length global is **not** re-initialised by a watchdog reset, and
> `FLR`-then-`put` needs power. That is the specific model this cell tests.
> **否證 ③** — `T-3` is not byte-identical to `X-3.log`. Then the loop
> completed but did not reproduce, and `D3`'s *reports a number* has no stable
> reference to assert against.

⚠️ **What it is not.** The *edit* is not in this sequence: the image was built
at the desk on 2026-08-30 and `R4-0` already measured the build stages
(38–58 s). **This closes the upload-and-boot half**, which is the half no desk
measurement can reach, and it says so rather than calling itself end-to-end.

---

## 5. Abort conditions, in the order they can fire

1. `Y-ab` ≠ `00000000` → **stop**, nothing else runs.
2. `Y-j1` wedges → **power-cycle, do not repeat `J BFC00000`.** Block 5 §5:
   that outcome refutes `LDR-33` and is the most valuable result in the block.
   Nothing in this file runs afterwards.
3. Any `Y-rNN` fails → stop the repeat run, record `NN`, and **go straight to
   §3**. The bracket does not need the reset to have worked twenty times.
4. Any `FLR` echo wrong → `flrbracket` sends `N` itself and exits non-zero.
   Read `§5.2` of block 4's table before typing anything.
5. Any read-back that does not normalise equal → **stop, do not `J`**.
6. `T-rz` returns no prompt → power off; §4 is recorded 未定 and §3 stands.
7. `T-ab` ≠ `00000000` → **stop, upload nothing.**
8. A missed ESC window anywhere boots the vendor firmware, about two minutes.
   **Let it finish, then power-cycle; do not interrupt it.**

---

## 6. Flash

The only flash commands on this card are four `FLR` reads, each 256 bytes,
each preceded by an `AUTOBURN` read that must be `00000000`. **No `EW`, `EB`,
`FLW` or burn appears anywhere in this file or in block 5.** `J BFC00000`
touches `WDTCNR` and nothing else; `J 80500000` enters RAM.

🔴 **`0.0244 %` is not `0 %`.** See §3.3.

---

## 7. The numbers, declared so a machine re-derives them

```cardnum
dw-1word	71	dwreply 1
dw-8words	118	dwreply 8
dw-64words	777	dwreply 64
boot-bytes	849	size bench/2026-08-31b/X-3.log
boot-sha16	8317e7c9fe6eb60f	sha256-16 bench/2026-08-31b/X-3.log
boot-bytes-w	849	size bench/2026-08-31/W-3.log
boot-sha16-w	8317e7c9fe6eb60f	sha256-16 bench/2026-08-31/W-3.log
boot-bytes-v	849	size bench/2026-08-30c/V-3.log
boot-sha16-v	8317e7c9fe6eb60f	sha256-16 bench/2026-08-30c/V-3.log
version-bytes	111	size bench/2026-08-31/W-5b.log
version-sha16	af2981649f1eb541	sha256-16 bench/2026-08-31/W-5b.log
readback-bytes-0	777	size bench/2026-08-31c/K-rd0.log
readback-bytes-6	777	size bench/2026-08-31c/K-rd6.log
readback-bytes-g0	777	size bench/2026-08-24d/G8a-rd0.log
readback-bytes-g6	777	size bench/2026-08-24d/G8a-rd6.log
img-bytes	1029120	size /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin
img-sha16	08b088135c62cbef	sha256-16 /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin
img-zerotail	652	zerorun-tail /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin
img-word-18	3C108060	word32 /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin 24
img-word-1C	2610B400	word32 /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin 28
img-word-40000	162DC569	word32 /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin 262144
block5-cells	24	count bench/2026-09-01/PREDICTIONS-B7-block5.md ^bench/2026-09-01/Y-
block5-sends	0	count bench/2026-09-01/PREDICTIONS-B7-block5.md --send
```

⚠️ **`img-*` names an absolute path outside this repository**, so
`cardcheck numbers` re-derives those five rows **only when it is run inside
WSL**, where `/home/key/…` exists; from Git Bash on the Windows side
`os.path.join(ROOT, rel)` sends it to a path that is not there. The run of
record for this card is the WSL one, and this is stated rather than left to
produce a puzzling failure.

---

## 8. Cells

**Block 5 owns its own 24 and they are not repeated here.** These are this
block's, and only the ones that land **inside** the repository: the four
pre-reads and the two `H601` read-backs go to
`/home/key/fwre-work/rebuild/bench-only/b7-20260901/` and may not be committed.

```cells
bench/2026-09-01/T-flr0
bench/2026-09-01/T-yes0
bench/2026-09-01/T-rd0
bench/2026-09-01/T-flr6
bench/2026-09-01/T-yes6
bench/2026-09-01/T-rd6
bench/2026-09-01/T-flrh
bench/2026-09-01/T-yesh
bench/2026-09-01/T-flrc
bench/2026-09-01/T-yesc
bench/2026-09-01/T-rz
bench/2026-09-01/T-ab
bench/2026-09-01/T-0t
bench/2026-09-01/T-2a
bench/2026-09-01/T-2b
bench/2026-09-01/T-2c
bench/2026-09-01/T-3
bench/2026-09-01/T-5b
```
