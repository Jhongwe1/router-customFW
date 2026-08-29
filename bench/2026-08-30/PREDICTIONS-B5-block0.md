# PREDICTIONS — Session B5, `R1h-3`, block 0: `probe3`, power cycle 1

**Written at the desk on 2026-08-29, before power, as `R1h-3`'s desk half.**
Every value below was computed on this host before the seating — by
`reply-size.py` for the loader's replies, by the payload's own ELF for the
addresses it will print, and by re-running the arithmetic on committed captures
for anything quoted from a previous seating. **Nothing here was counted in a
terminal.** `tools/check-predictions.py` checks the ordering.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and the check fails, correctly. Corrections go in a new file.

**This is power cycle 1, and it runs first.** `bench/2026-08-30b/` is power
cycle 2 (`loudm`, `R3-8a`) and its block is frozen. Power cycle 3 has no block
yet and that is deliberate: which image it carries is decided by `L-3`.

⚠️ **The directory is named for the seating the card was written for, not for
the day this file was written.** `bench/2026-08-30b/PREDICTIONS-B5-block1.md` is
frozen and names its own sibling; `RUNSHEET` §B5 names both. If the seating
happens on the 29th the name does not move, because moving it would break a
frozen file and a committed card to fix a label.

---

## Why `probe3` goes first, and it is not the schedule

`R3`'s pass state is *a kernel is running*. In that state the loader is gone,
the DRAM is gone, there is no `<RealTek>` prompt to type `J` into and no `DW` to
recover a result block with. **"At the tail of `R3`" names which seating, not
the order inside it** — `PROGRESS.md`'s stop-loss has said so since the gate
opened.

**And `probe3` cannot share `R3`'s upload.** M8, 量 `R1g-4b` 2026-08-25: the
loader re-stages `0x80500000` on a watchdog reset, so a second `J` in the same
cycle runs the *staged vendor image*. One power cycle per `J`.

---

## Cells, in order

```cells
bench/2026-08-30/A-catch
bench/2026-08-30/Q0-ab
bench/2026-08-30/Q1-tc
bench/2026-08-30/Q1-tc2
bench/2026-08-30/Q2-rbhead
bench/2026-08-30/Q2-arena0
bench/2026-08-30/Q2-arena1
bench/2026-08-30/Q2-arena2
bench/2026-08-30/Q3-len
bench/2026-08-30/Q0-ab2
bench/2026-08-30/Q4-head
bench/2026-08-30/QJ
bench/2026-08-30/Q5-rb
```

**Thirteen cells, and what the check will report is itself predicted:**

| the seating reaches | expected report |
|---|---|
| `Q5-rb` | `13 of 13 captures came after the prediction, 0 did not` |
| `QJ` but the block cannot be read | `12 of 13`, and `Q5-rb` is the one |
| `Q0-ab` returns anything but `00000000` | `2 of 13` — `A-catch` and `Q0-ab` — and **that is the correct outcome**, not a failure of this file |
| no prompt at all | `1 of 13`, and `A-catch` is the finding |

**Named but not in the block, on purpose**: `Q5-margin`
(`DW 80A02A04 8`, run only if the free over-run words come back non-poison) and
`Q6-post` (a post-mortem `DW` after a `J` that printed nothing). Naming a
branch that may not run guarantees a violation whichever way the seating goes,
which would make the number meaningless. **The cost is stated rather than
hidden**: if a branch cell runs, its ordering is unenforced — the same gap
`bench/README.md` records for `CONT3`.

**Not captures at all**: `Q0-rescue.json` and the `loader-tftp.py put`
transcript are JSON, have no `.log`, and are checked by `--expect-load` and by
`Q4-head` instead.

---

## 0. 🔴 THE CARD — the only part of this file that is read at the bench

`RUNSHEET` §B5's card says of this power cycle, in its own words: *"`R1h-3` owns
it; it is not on this card."* **So there is no other card, and this section is
it.** Everything below §0 is the reasoning that produced it, and reasoning is
not what you read with a board powered.

Every row is one `console-capture.py` invocation, so every row is one `.log`.
The **bytes** column is `reply-size.py`'s number. 🔴 **Every stop-if names an
ADDRESS, never a word number** — §B5-c8, which is the item on the `loudm` card
that could have aborted a good upload.

Prefix every command with `/usr/bin/python3`, never `python3`.
`CAP` below stands for
`/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **Q-A** | power on with `CAP --out bench/2026-08-30/A-catch --esc 25 --esc-period 0.002` | the ESC window, then `<RealTek>` | — | no prompt → power off. That is the seating |
| **Q-0r** | `/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-08-30/Q0-rescue.json` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **Q-0ab** | `CAP --out …/Q0-ab --send 'DW 8040D4A0 1' --seconds 4` | the word **at `0x8040D4A0`** = **`00000000`** | **71** | ≠ `00000000` → **STOP. Nothing is uploaded** |
| **Q-1a** | `CAP --out …/Q1-tc --send 'DW B8003108 1' --seconds 4` | **four** words: `TC0CNT` · `00000000` · `C0000000` · `80000000` | **71** | word at `0xB800310C` ≠ `00000000`, at `0xB8003110` ≠ `C0000000`, or at `0xB8003114` ≠ `80000000` → M9 is wrong; record and carry on |
| **Q-1b** | `CAP --out …/Q1-tc2 --send 'DW B8003108 1' --seconds 4` | the word **at `0xB8003108`** ≠ `Q-1a`'s | **71** | 🔴 **equal → send it a THIRD time before recording anything.** The counter wraps every 142,858 ticks and two console reads land at an uncontrolled phase, so one equal pair is ~1 in 143,000 on a perfectly live counter. **Two consecutive equal readings** → frozen, and **Group T does not ship**; the rest is unaffected |
| **Q-2r** | `CAP --out …/Q2-rbhead --send 'DW 80A02000 16' --seconds 6` | bias garbage. **Record all sixteen words** | **213** | see §7's six refutation shapes. This is also `Q5-rb`'s before-picture |
| **Q-2a** | `CAP --out …/Q2-arena0 --send 'DW 80A10000 16' --seconds 6` | bias garbage | **213** | as `Q-2r` |
| **Q-2b** | `CAP --out …/Q2-arena1 --send 'DW 80A50000 16' --seconds 6` | bias garbage | **213** | as `Q-2r` |
| **Q-2c** | `CAP --out …/Q2-arena2 --send 'DW 80A8FFC0 16' --seconds 6` | bias garbage | **213** | as `Q-2r`, **and**: any two of the four windows byte-identical → a stuck read path |
| **Q-3** | `CAP --out …/Q3-len --send 'DW 80A00000 2000' --seconds 15` | a complete 500-line reply | **23,527** | `Unknown command !` (≈44 B) or a short whole-line reply → the loader will not take a 4-digit length. **Nothing in this payload depends on the answer** |
| **Q-0ab2** | `CAP --out …/Q0-ab2 --send 'DW 8040D4A0 1' --seconds 4` | the word **at `0x8040D4A0`** = **`00000000`**, still | **71** | ≠ `00000000` → **STOP.** The named mechanism is the 128-byte readline cliff (seating 2 rule 2): a capture that ends without its CR leaves *N* mod 128 bytes in the loader's buffer and the next command is appended to them, so a mistyped or truncated cell can reach the loader as a command nobody sent |
| **Q-put** | `/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe3/probe3.bin --filename probe3 --rescue-report bench/2026-08-30/Q0-rescue.json --expect-load 80500000 --yes` | **29,088** bytes accepted, sha256 `1a0725c0…` in the transcript | — | any refusal → read it. **Never `--allow-autoexec`** |
| **Q-4** | `CAP --out …/Q4-head --send 'DW 80500000 8' --seconds 6` | `80500000: 3C1D8051 27BDB490 3C088050 250871A0` · `80500010: 3C098050 25297490 11090004 00000000` | **118** | 🔴 **the word at `0x80500000` ≠ `3C1D8051`, or the word at `0x8050000C` ≠ `250871A0`** → the wrong image is at `0x80500000`. Decode it with §9's two-level table. ⚠️ **Addresses, not word numbers** |
| **Q-J** | `CAP --out …/QJ --send 'J 80500000' --esc-after 60 --esc-period 0.002 --seconds 120` | the banner, then §10's report, then `rlxprobe: end`, then a reboot into the ESC storm and a prompt | — | **`rb=` ≠ `80a02000`** or **`flags=` ≠ `50010002`** → the wrong image is running. ⚠️ **Neither is a guard and both are diagnoses** — see §10 |
| **Q-5** | `CAP --out …/Q5-rb --send 'DW 80A02000 641' --seconds 15` | 161 lines, last line `80A02A00: <seal> DEADC0DE DEADC0DE DEADC0DE` | **7,593** | word at `0x80A02000` ≠ `524C5833` → the block was never written. §12 has the three-way seal check |

**Total on the wire for the `DW` cells: 32,374 bytes.** `Q-A` and `Q-J` are
dominated by their ESC windows, not by their content.

### 🔴 The `--seconds` on every row is sized against a **measured** rate, not the line rate

`console-capture.py` has no early stop here: `--seconds` is a fixed window, so a
value too small **truncates the reply and the truncation looks like a refusal**.
That matters most on `Q-3`, whose whole purpose is to tell a refusal from a
completed reply.

量 2026-08-29, off the committed `.timing` files — the loader's own `DW` print
loop, measured from first read to last read of one contiguous reply:

| capture | sent | bytes | window | B/s | % of line rate |
|---|---|---:|---:|---:|---:|
| `H2g` | `DW 80A01000 817` | 9,660 | 2.688 s | **3,594** | 93.6 % |
| `H1c` | `DW 80A00000 137` | 1,667 | 0.447 s | **3,726** | 97.0 % |

⚠️ **`B7c` was excluded and here is why**, because a scan that silently drops
its outlier is a scan that can be tuned to agree: it holds 1,272 bytes over a
20 s window for a command whose reply is 71 bytes, so those bytes are an ESC
window's echoes and not one contiguous reply. Excluding it is a judgement about
what the measurement is *of*, and it is stated rather than made quietly.

**Sized against the slower of the two, 3,594 B/s:**

| row | bytes | needs | `--seconds` | margin |
|---|---:|---:|---:|---:|
| `Q-3` | 23,527 | 6.55 s | 15 | **2.29×** |
| `Q-5` | 7,593 | 2.11 s | 15 | **7.10×** |
| the 71/118/213-byte rows | ≤ 213 | ≤ 0.06 s | 4–6 | ≥ 67× |

**And the discriminator if `Q-3` comes back short**: a refusal is
`Unknown command !`, ≈ 44 bytes, arriving at once and followed by a prompt; a
`--seconds` truncation stops **mid-line with no prompt**. The two are not the
same shape and the results table must say which was seen.

🔴 **This rate is a property of the loader's `DW` reply and is NOT the rate
`docs/probe3-cells.md` §4's wall is computed at.** That wall is about the
*payload's* own UART writes draining before the ESC window is eaten, and this
measurement contains the loader's per-line formatting. Using 3,594 there would
be importing a number across the boundary it was measured on.

⚠️ **`--load-addr` takes `0x80500000` **with** the `0x`; `--expect-load` takes
`80500000` **without** it.** Opposite conventions, same session, minutes apart —
量 from `argparse` in both files, and it is on the card because it has bitten.

---

## 1. Three different things here are called `P`, and this file uses none of their numbering

This is the one thing about block 0 that could send the operator to the wrong
page with a board powered, so it is resolved before anything else:

| where | what `P0`…`Pn` means there |
|---|---|
| `RUNSHEET.md:442-446` | the **host** preflight — pyserial, `usbipd`, the NIC, a sha256. `P0`–`P4` |
| `RUNSHEET.md:1982-1992` | **`R3`'s desk checks** — `hazlint`, `kconfig-delta`, the marks ladder. `P1`–`P11`, and **`P7` is `probe3`'s rebuild-on-the-day** |
| `docs/probe3-cells.md` §5 | **`probe3`'s at-the-prompt preflight** — `AUTOBURN`, `TC0CNT`, the arena, the `DW` length ceiling. `P0`–`P3` |

Three namespaces, overlapping numbers, different commands. *"Run `P2`"* names
`bash tools/test-console-capture.sh`, `hazlint-objs.py --tree`, and
`DW 80A02000 16` with equal justification.

**So the card's rows are `Q-*`, and nothing on it is called `P`.** The mapping
to the owner file is here and nowhere else, which is the same device
`RUNSHEET` §B5 used when it made `L-*` the card rows for `K0`–`K8`:

`Q-0ab`/`Q-0ab2` = `P0` · `Q-1a`/`Q-1b` = `P1` · `Q-2r`/`Q-2a`/`Q-2b`/`Q-2c` =
`P2` · `Q-3` = `P3`. `Q-4`, `Q-J` and `Q-5` are not in Group P at all — they are
the upload check, the run, and the read-back.

---

## 2. `P7` — the rebuild-on-the-day, and it is already run

**量 2026-08-29, this host, before the board was touched.** `docs/probe3-cells.md`
§10b's procedure, all three steps, output read line by line:

```
rm -rf tools/rlxprobe/build/probe3
make -C tools/rlxprobe P=probe3 payload RESULT_BASE=0x80A02000
make -C tools/rlxprobe P=probe3 show
```

| the check | what it must say | what it said today |
|---|---|---|
| `make` itself | it **compiles**. `Nothing to be done for 'payload'` is a HARD STOP | it compiled |
| `hazlint` | the build gate passes with its controls | **`0 violations in 804 loads, and the controls that could have said otherwise held`** |
| `sha256` | `1a0725c0e925b8c3857802d01791768f6b8241dbcf271b1dbd391e287a5ecc0b`, **29,088 bytes** | **identical**, and `sha256sum` on the `.bin` independently agrees |
| `result` | `RESULT_BASE=0x80A02000 … DW 80A02000 641` | as recorded |
| `stale check` | `rb=80a02000` | as recorded |
| `vectors` / `uart` | `general 0x80000080`, `THR 0xB8002000`, `CLEAR_BEV=0`, and **no `*** NOT A DEVICE BUILD ***`** | as recorded |

🔴 **The sha256 is byte-identical to the one `R1h-1` recorded on 2026-08-26.**
That is a stronger result than the procedure asked for — the procedure exists
because the binary in the tree on seating day *is not to be trusted*, and what
it found is that this build reproduces across three days on this host. **It does
not generalise to another host and is not claimed to**; `qemu/2026-08-26/probe3.build`
records the toolchain that produced both.

⚠️ **`show` printing a knob is not the same as the image carrying it.** That is
`P10`'s lesson from the marks ladder, in a different tool: `check` reads the
tree and `verify` reads the artefact. The on-the-wire half of this check is
`rb=80a02000` and `flags=50010002` in the banner, and it is on the card.

### The two build-stamp discriminators, derived rather than quoted

`Makefile:239` computes
`FLAGS = 0x50000000 | 0x0002 | (RESET<<16) | (CLEAR_BEV<<17) | (RET_ERET<<18) | (ISC<<19) | (GEOM<<20)`.
Evaluated here rather than copied:

| build | knobs | `flags=` |
|---|---|---|
| **device** | `RESET=1 CLEAR_BEV=0 RET_ERET=0 ISC=0 GEOM=0` | **`50010002`** |
| qemu | `RESET=1 CLEAR_BEV=1 RET_ERET=1 ISC=0 GEOM=0` | `50070002` |

量: the committed qemu capture's first field line reads `flags=50070002`, so the
expression reproduces a measured value before it is used to predict one.
**`flags=50010002` on the wire is the device-build discriminator**, and it is
independent of `rb=`, which catches a different mistake (a `probe1`/`probe2`
`RESULT_BASE`).

---

## 3. The host — already done today, with one thing that will happen again

量 2026-08-29, board off:

| | |
|---|---|
| long-lived WSL process | `wsl -d Ubuntu-24.04 -- sleep 36000`, backgrounded **before** any attach |
| CP2102 | busid **`1-1`** → `/dev/ttyUSB0` (`10c4:ea60`) |
| USB GbE | busid **`2-4`** → `enxfc19286184c9`, driver `r8153_ecm`, host `10.1.1.2/24` |
| the interpreter | `/usr/bin/python3`. `python3` resolves to a venv with no `pyserial` |
| the port opens | one 3-second capture with the board off: **0 bytes in 3.087 s**, and the tool named three causes — the adapter, the port, or the board — rather than one |

🔴 **The CP2102 left the Windows USB bus once today, before any of this.** It
was absent from `usbipd list`'s *Connected* section entirely — not merely
unattached — with no COM port on the Windows side, and it came back only after
being re-seated. That is the drop `CLAUDE.md` records with three unruled-out
causes. **If `/dev/ttyUSB0` disappears mid-seating it is not a new fault**, and
the recovery is re-seat → `usbipd list` → re-attach, never a reused busid.

⚠️ **`carrier` on `enxfc19286184c9` reads `1` with the board unpowered.** So
*link is up* is not evidence of anything on this path until it has been read in
both states. Read it again after power-on; if it is `1` both times, it is a cell
that cannot fail and it carries no information about the board.

---

## 4. `A-catch` — the power-on catch, and what it can and cannot say

`CAP --out …/A-catch --esc 25 --esc-period 0.002`

**Prediction**: from the first `\r\nBooting` in the log, **181 bytes with
sha256 `f5287ff9f64b1035…`**.

### 🔴 This cell has NO negative control, and the block must say so

Block 1 states the prediction as *five* cold power-ons with `2026-08-24e` as the
warm-boot control. **Both halves are wrong and `RUNSHEET` §B5-c12 already owns
the correction.** It was re-measured here anyway — a slice both blocks depend on
is a shared dependency worth breaking — over **every** `A-catch*.log` in
`bench/`, with no hardcoded list:

| capture | prefix | bytes available after `Booting` | 181-byte slice |
|---|---:|---:|---|
| `2026-08-23` | — | — | no `\r\nBooting` at all |
| `2026-08-24` | 0 | 1,306 | `f5287ff9…` |
| `2026-08-24b` | 0 | 1,066 | `f5287ff9…` |
| `2026-08-24c` | 1 | 1,652 | `f5287ff9…` |
| **`2026-08-24d`** | **2,814** | 930 | `f5287ff9…` |
| **`2026-08-24e`** | **4,424** | **118** | 🔴 `5fdecbb6…` — **and only 118 bytes exist** |
| **`2026-08-24f`** (`A-catch2`) | **2,810** | 9,013 | `f5287ff9…` |
| `2026-08-25` | 1 | 8,854 | `f5287ff9…` |
| `2026-08-25b` | 2 | 92,062 | `f5287ff9…` |

**Seven complete slices, one distinct hash.** And 量: `24e`'s 118 bytes are a
**byte-identical prefix** of the canonical 181. **Its different hash is the
length, not the content** — slicing 181 bytes out of a file that holds 118 gives
a short string, and a short string hashes differently for a reason that has
nothing to do with the boot.

🔴 **So `24e` is not a warm-boot control and there is no case in this
repository that makes this cell fire.** `CLAUDE.md`: *a tool that cannot fail
proves nothing*. The honest statement is that the 181-byte slice is a strong
**consistency** reading across seven captures with **no demonstrated negative**,
and it is recorded here as that rather than as a discriminator. A capture that
matched would tell us the boot went as it always has; a capture that did not
would be the first evidence the check works at all.

⚠️ **This block does not fix block 1 and does not re-own the correction.**
§B5-c12 is the list of what the frozen block gets wrong; both rows are already
in it. What is new here is only the sweep over nine files instead of six.

### The prefix is not small, and it is the board rather than the adapter

Block 1 calls the prefix *"0, 1 and 2 bytes … the adapter and not the board"*.
量: three captures carry **2,810–4,424 bytes**, and those bytes are
`0x5E 0x5B` repeated — the literal two characters **`^[`**, caret notation for
ESC, printed by the **loader's own readline** as it echoes the stream `--esc` is
sending. They are the *previous* power cycle's loader, still at the prompt when
the capture opened. `24d`, `24e` and `24f` are all later cycles of a
multi-cycle day, which is exactly when that happens.

**Two consequences, and the second is a control neither block had:**

1. **Find `\r\nBooting` by searching, never by reading the head of the file.**
   A reader who takes "the first 181 bytes" literally reads `^[^[^[…` on three
   of the nine captures.
2. 🔴 **A `^[` run in `Q-A` means the seating did not start from cold.** `Q-A`
   is the first power-on of this seating and the board should be **off** when
   the capture opens, so the prefix should be adapter noise in single bytes
   (`""`, `ff`, `00`, `00 fc` — 量, the six single-byte cases above). Any run of
   `0x5E 0x5B` means a loader was already answering, and then `AUTOBURN`, DRAM
   bias and the staged image are a previous boot's — so **§7's arena reading is
   not power-on bias** and `Q-2*` must be re-read against that.

---

## 5. `Q-0ab` / `Q-0ab2` — `P0`, the gate, read twice

`--send 'DW 8040D4A0 1'`. **71 bytes each** — `reply-size.py predict` gives
`13 + 2 + 47 + 9`, the model fitted on n=91 captures.

**Prediction**, byte for byte, identical to `bench/2026-08-25b/H2a-ab.log`:

```
DW 8040D4A0 1\n\r8040D4A0:\t00000000\t00000000\t00000000\t00000000\n\r<RealTek>
```

🔴 **If the word at `0x8040D4A0` is not `00000000`, STOP. Nothing is uploaded.**
One instruction at `0x80401B9C` is the burn path's own read of it. `AUTOBURN` is
RAM state and every reset puts it back to `1` (量, `bench/2026-08-23/B.log` B6
on a fresh boot; 量 again as `00000001` in `G8b-ab` after a payload's own
reset), which is why the `rescue` in `Q-0r` is not optional.

🔴 **Why it is read twice, and this is not caution.** Block 1 reads it once,
*"after the rescue and before the transfer, because the word that matters is the
one the burn path sees during the transfer"*. Block 0 puts **six commands and
6.4 seconds** between the rescue and the transfer that block 1 does not have.
Reading it again immediately before the `put` costs 71 bytes and 0.02 s and
turns one reading into a **bracket** over everything the preflight sends. A
disagreement between the two is a finding about a `DW` command, which no other
cell here could produce.

---

## 6. `Q-1a` / `Q-1b` — `P1`, and four words come back where the cell asks for one

`--send 'DW B8003108 1'`, twice, seconds apart. **71 bytes each.**

🔴 `LDR-07` rounds the word count **up** to a multiple of four, so this one
command prints four words. **All four are pre-registered**, or a change in the
fourth passes unremarked in the cell whose whole purpose is raising `REG-07` off
n = 1:

| address | field | expected | source |
|---|---|---|---|
| `0xB8003108` | `TC0CNT` | **different between the two reads** | 量 `REG-09` (`TC0En=1`, `TC0Mode=1`) + `CLK-04` (the loader's tick advances at 100.0018 Hz, which requires the counter to count) |
| `0xB800310C` | `TC1CNT` | `00000000` | 量 `REG-08`, `bench/2026-08-23/E.log:15` |
| `0xB8003110` | `TCCNR` | `C0000000` | 量 `REG-09` |
| `0xB8003114` | `TCIR` | `80000000` | 量 `REG-10` |

**Refuted by**: equal `TC0CNT` on the separated pair → the register is frozen,
not a live mirror, and **Group T does not ship**. `TCCNR ≠ C0000000` → something
writes it after `timer_init` and M9 is wrong.

⚠️ **This is not a rate measurement and must never be written up as one.** The
counter wraps every 9.9998 ms; two console reads are seconds apart, so the delta
is uniform mod 142,858 and carries no rate information. At 38,400 the command
echo alone exceeds one wrap.

🔴 **The count field is bits 31:4.** Every reading is shifted right by 4 before
it is a tick count — 量 `REG-05`, `TC0DATA` reads `0x0022E0A0` = `142,858 << 4`,
exactly the compiled-in value, so the shift is measured on silicon. `REG-07`'s
single reading `0x0010B960` is 68,502 counts, not 1,096,032.

---

## 7. `Q-2r` … `Q-2c` — `P2`, the arena, and the one window that is also a control

Four commands, **213 bytes each** (`14 + 2 + 4×47 + 9`), reading the head of the
result block and the head / middle / tail of the arena.

| capture | address | what it is |
|---|---|---|
| `Q2-rbhead` | `0x80A02000` | **the result block's head, before the run.** Also `Q5-rb`'s before-picture |
| `Q2-arena0` | `0x80A10000` | arena head |
| `Q2-arena1` | `0x80A50000` | arena middle |
| `Q2-arena2` | `0x80A8FFC0` | arena tail — the last 16 words of `0x80A10000`–`0x80A8FFFF` |

**Expected: high-entropy bias garbage.** 量 `MEM-16`: uninitialised DRAM on this
board is 89.5 % reproducible across a 16 h power-off against a **measured** null
of 55.98 % — so it looks like structure and is not.

**Refuted by any of** (`docs/probe3-cells.md` §5, verbatim):

* a word equal to its own address or to another address in the window
  (`MEM-11`'s signature — uninitialised DRAM cannot produce its own address);
* any aligned pointer-shaped word `80xxxxxx` / `81xxxxxx` / `A0xxxxxx` /
  `B8xxxxxx` (`G0`'s pre-written condition, verbatim: *"any one pointer-shaped
  word and the address is re-picked"*);
* a repeating period;
* sixteen zero bytes — on this board zeros are not power-on bias;
* any known magic: `5A5AA5A5`, `00000144`, `DEADC0DE`, `524C5831`, `524C5832`;
* **any two of the four windows byte-identical** → a stuck read path, and
  nothing else in this list catches it, because bias garbage is *supposed* to
  look like structure.

🔴 **`DEADC0DE` on this list is `probe3`'s own poison, and today is the only
seating where that is unambiguous.** `RB_POISON` is `0xDEADC0DE` (讀,
`probe3.c:94`) and the payload poisons `w0`–`w648` before its first cell. So
from the second seating onward, `DEADC0DE` at `0x80A02000` has two readings —
*the arena choice is bad* and *the previous run's block survived the power-off*
— and M7 is the standing proof that the second is possible (`MEM-10`: a two-word
canary survived three warm resets). **`probe3` has never run on this silicon**,
so today it can only be the first. Recorded because the ambiguity arrives with
the next seating and will not announce itself.

⚠️ **`524C5833` (`'RLX3'`) is deliberately NOT on the refutation list** — it is
what `Q5-rb` must find at `0x80A02000` afterwards. Before the run it would mean
the same thing `DEADC0DE` does; the list inherited from §5 predates the block
being placed here and it is left as written rather than quietly extended.

---

## 8. `Q-3` — `P3`, and it is the one preflight cell nothing depends on

`--send 'DW 80A00000 2000'`. **23,527 bytes, 6.13 s** — `reply-size.py`:
`16 + 2 + 47×500 + 9`.

**What it tests**: whether the loader's `DW` accepts a **4-digit decimal
length**. The largest `DW` ever executed on this device is 820 words / 9,661
bytes (量, `H2g`).

**Refuted by** `Unknown command !` (≈44 B) or a short whole-line reply → the
read-back must stay ≤ 999 words for every future payload.

🔴 **And it changes nothing about today.** `DW 80A02000 641` is three digits.
`docs/probe3-cells.md` §4, the `Makefile`'s `RB_WORDS_probe3` comment and
`probe3.c`'s compile-time assertion all say so independently. **This cell is
reconnaissance for `R5-0` and later payloads, bought on a seating already paid
for**, and it is placed last among the preflight cells so that a failure costs
nothing that mattered.

⚠️ **Its content is not predicted, only its length.** The window
`0x80A00000`–`0x80A01F3F` covers `probe1`'s and `probe2`'s old result blocks;
`MEM-15` measured a 548-byte chosen-value block **not** surviving ~3.9 h, so
after a cold boot those are bias garbage and `P2`'s shapes apply to them too.

---

## 9. `Q-4` — which image is at `0x80500000`, and here the head **does** answer

`--send 'DW 80500000 8'`. **118 bytes.**

🔴 **Read §B5-c1 before reading this cell, and then read this paragraph.**
§B5-c1 measured that the head does **not** discriminate — 16 bytes
byte-identical on the device across three captures, 24 across five files — and
`K2`'s premise was refuted on it. **That result is about `nfjrom` files**, which
all share the same `rtkload` `start.o`. `probe3` is not an `nfjrom`; it is a
flat payload linked by `rlxprobe.lds`, and its first word is the first
instruction of `_start`. **The head discriminates here for the same reason it
did not there, and quoting §B5-c1 against this cell would be quoting a
measurement outside the corpus it was taken on.**

**Prediction, both lines, 量 on the image built today:**

```
80500000:	3C1D8051	27BDB490	3C088050	250871A0
80500010:	3C098050	25297490	11090004	00000000
```

**Two independent things are checked by those eight words**, and both were
derived rather than transcribed:

| words | decode | why it is a check |
|---|---|---|
| `0x80500000`–`0x80500004` | `lui $29,0x8051` / `addiu $29,$29,-0x4B70` → `$29 = 0x8050B490` | the stack top. **`3C1D8051`** vs `probe2`'s `3C1D8050` |
| `0x80500008`–`0x8050000C` | `lui $8,0x8050` / `addiu $8,$8,0x71A0` → **`0x805071A0`** | `_bss_start` = `0x80500000 + 29,088`, and 29,088 is the size `make show` printed |
| `0x80500010`–`0x80500014` | `lui $9,0x8050` / `addiu $9,$9,0x7490` → **`0x80507490`** | `_bss_end`. `0x80507490 − 0x805071A0` = **752**, and 752 is the `.bss` size the build printed |

**Three numbers from three places agreeing: the linker's constants in the image,
the byte count of the file, and the `.bss` figure the build reported.**

🔴 **And this is the same mechanism §B5-c1 found for the kernels, with a
different linker.** There, the word at `0x8050001C` carries `__vmlinux_end` =
`0x80500000 + size`. Here, the word at `0x8050000C` carries `_bss_start` =
`0x80500000 + size`. **A two-level decode covers every image this project can
put at `0x80500000`:**

| word at `0x80500000` | then look at | table |
|---|---|---|
| `3C1D80xx` | **`0x8050000C`** | below |
| `00000000` | **`0x8050001C`** | §B5-c1's, in `PREDICTIONS-B5-block1.md` — it is an `nfjrom` |

| `0x80500000` · `0x8050000C` | = | that would be |
|---|---|---|
| `3C1D8051` · **`250871A0`** | `0x805071A0` | 🟢 **`probe3`, 29,088 bytes. The pass** |
| `3C1D8051` · `25084D50` | `0x80504D50` | 🔴 `probe1`, 19,792 bytes — the wrong payload |
| `3C1D8050` · `250824B0` | `0x805024B0` | 🔴 `probe2`, 9,392 bytes — the wrong payload |
| `00000000` · `00000000` | — | 🔴 **an `nfjrom` — the transfer did not land and the staged vendor image is still there** |

⚠️ **Word 1 alone is not enough**: `probe1` and `probe3` share `3C1D8051`. That
is why this cell reads eight words and not one, and why `LDR-07`'s round-up (a
length of 1 through 4 still prints four words) does not remove the need for it.

🔴 **There is no tail check in this block, and the reason is arithmetic.**
Block 1 gets a before/after pair on `0x806013F0` because `loudm` is 1,053,696
bytes and ends **66,542 bytes above** the staged image. `probe3` is 29,088 bytes
and ends at `0x805071A0` — **958,050 bytes below** the staged image's end at
`0x805F1002`. The whole payload lies inside the fallback. **So the head is the
only discriminator here, and in block 1 it was the tail. The two blocks are
mirror images of each other and neither method transfers.**

### The filename, and why `--filename probe3` is passed explicitly

讀, this unit's own `stage2.bin` at `0x80401208` (§B5-c2): the loader
substring-searches the **WRQ filename** for `nfjrom` (→ auto-execute) and for
`boot.img` (→ auto-execute **and** force `0x80000000`). `--image` is a local
path the loader never sees; the default `--filename` is `image`. `probe3`
contains neither string. **The default would have been safe and it is passed
explicitly anyway**, because the card's rule is that a procedure relying on a
default is a procedure that cannot be checked from its own transcript.

---

## 10. `Q-J` — the run. `--send 'J 80500000' --esc-after 60 --seconds 120`

⏱ Reference: `probe2` on this silicon, `bench/2026-08-25b/H2a` — 36,314 bytes
over 120.09 s, of which **the payload's own report is the first 2,948 bytes** and
the remaining 33,366 (91.9 %) is the post-reset ESC storm, 209 repetitions of
`Unknown command !`. 量, recomputed on the committed file today. **The storm,
not the report, is what sizes this capture.**

### The pinned prefix

讀 `bench/2026-08-25b/H2a.log`, `probe2` entered the same way:

```
J 80500000
---Jump to address=80500000

*** rlxprobe P3 7e41c9d0 ***
```

`7e41c9d0` is `RLX_NONCE`, a compile-time constant (讀, `probe3.c:63`), so it is
the same on both builds and it is **not** a discriminator. ⚠️ **There is no
`decompressing kernel:` line here** — that is `rtkload`'s, and `probe3` is not
wrapped. Its absence is expected; in block 1 it is D1.

### The header, field by field. **qemu and device are separate columns**

🔴 **A qemu run that looks like the device is the run to distrust.** The column
marked ⚠️ below is where the two agree, and every one of those is a cell whose
qemu pass was earned for a different reason than the device's would be.

| UART line | 量 qemu (`qemu/2026-08-26/probe3.txt`) | expected on the device | source for the device column |
|---|---|---|---|
| `WARNING RLX_CLEAR_BEV=1` | **present** | 🔴 **ABSENT** | `CLEAR_BEV=0`, 量 in today's `make show` |
| `pc=` | `80502ca4` | 🔴 **`80502c74`** | 算 from today's ELF: the single `jal rlx_pc` is at `0x80502c6c`, and `jal` sets `$31 = PC+8`. **Anything outside `0x80500000`–`0x805071A0` means the image is not running where it was linked** |
| `rb=` | `80a02000` | **`80a02000`**, **lower case** | `report.c`'s digit table is `0123456789abcdef`, the loader's is upper, so `rb=80A02000` is a string a correct run never produces |
| `flags=` | `50070002` | 🔴 **`50010002`** | §2's expression, evaluated |
| `status=` | `00000000` | **`1000fc00`** | 量 `probe2`, `H2a.log:8` — the loader's `Status` at entry on this silicon |
| `arena=` | `80a10000` | `80a10000` | a build constant; `arena_moved` says if `m-imem` forced it elsewhere |
| `tmpl=` | `03e00008` | `03e00008` | the victim guard word, `jr $31` |
| `kseg0=` | `00000001` | `00000001` | the loader jumps to `0x80500000`, which is KSEG0. **`0` here voids every cache cell** |
| `handler_words=` | `00000019` (25) | 🔴 **`00000016`** (22) | 算 from today's ELF: `rlx_exc_end − rlx_exc_entry` = `0x58` = 22 words. **`probe2` measured the same 22 on this silicon**; qemu's 25 is `RET_ERET=1`'s three extra |
| `install.changed=` | `0000001e` (30) | **non-zero, and ≤ 44.** No exact value is predicted | 🔴 **This row said `0000002b` (43) *"with the identical handler"* until the adversarial pass, and the handler is not identical.** 量: `exc.S` was committed 2026-08-25 **23:19**, four hours *after* `H2a`'s seating at 19:03, and the 22 emitted handler words hash differently between the `probe2` and `probe3` builds in the tree today. Same **size**, different **content** — so `probe2`'s 43 is a *reference for the ceiling*, not a prediction. The ceiling is 2 × 22 = 44 because the count runs over both vectors, and 43 means exactly one installed word already matched what the loader had there |
| `install.bad=` | `00000000` | **`00000000`** | the read-back of what was just written. **Anything else and every M and X cell is void** |
| `break.count=` | `00000001` | ⚠️ **`00000001`** | 量 M3, `bench/2026-08-25b/H2a.log` |
| `break.cause=` | `00000024` | ⚠️ **`00000024`** | 量 M3 — ExcCode 9, `Bp` |
| `break.epc=` | `8050029c` | an address inside the image, **not** `probe2`'s `80500270` | different build, different offset. Only its range is predicted |

⚠️ **`break.count` / `break.cause` are the two header fields where qemu and the
device are predicted to be identical.** They are `h-brk`, the gate for Groups M
and X. The agreement is not evidence: qemu earns it with a 24Kf and `eret`, the
device earns it with 量 M3 on a `break` at `0x80000080` under `rfe`. **A qemu
pass on this cell says nothing about the device, and the device column is
licensed by a device measurement, not by the emulator.**

### 🔴 `rb=` and `flags=` are diagnoses, not guards, and the card says so

Stage 0 of the running order is *poison the result block; initialise the arena;
header; banner*. **The poison happens before the banner prints**, so by the time
`rb=80a02000` reaches the wire the block has already been written. Reading it at
the bench cannot prevent anything; it tells you what a wrong build just did.

**The guards are upstream and there are three of them, in this order:**

1. `P7` at the desk, already run — and since 2026-08-26 `make` refuses at parse
   time to produce a `probe1`/`probe2` `RESULT_BASE` for `P=probe3`, so that
   particular mistake cannot reach a `.bin`;
2. `Q-4`, which reads the image out of DRAM **before** the `J` and decodes its
   size from `0x8050000C`;
3. only then the banner.

⚠️ **And the stake that was written here first was overstated.** The natural
sentence — *"a wrong `rb=` is about to poison a block that holds a
measurement"* — is inherited from a seating where two payloads ran in one power
cycle. **On this seating nothing live is in DRAM to destroy**: `probe1`'s and
`probe2`'s blocks are from 2026-08-25 and the board has been off since. What a
wrong `rb=` actually means here is *the wrong payload is running*, which is a
different and smaller claim.

⚠️ **`rb=` and `flags=` are also not independent of `Q-4`.** The qemu build
differs from the device build by more than three immediates — 量, its `pc` is
48 bytes further along — so its `_bss_start` differs and `Q-4` would already
have caught it at `0x8050000C`. The banner pair is a **second reading of the
same question from the running code rather than from DRAM**, and it is on the
card because the two fail differently: `Q-4` could in principle be defeated by a
same-size image, and the banner cannot be read until stage 0 has run.

### The groups, qemu column against device column

| group | 量 qemu | expected on the device | refuted by |
|---|---|---|---|
| **T** — the timer | 🔴 **every read of `0xB8003108` = `FFFFFFFF`**; all brackets `0`; `Group T VOID -- ... there is no timer at that address on this machine`. *Nothing is there* and *the register is frozen* are different claims and the payload separates them | `t.live`/`t.live2`/`t.sep.a`/`t.sep.b` are **live counter values**, `t.tccnr=C0000000`. **`t.cal.hi` ≈ 14,286 ticks and `t.cal.lo` ≈ 7,143** — 算 from 量 `CLK-03` (1.408e8 iter/s) × 14,286,057 Hz, and 10.0 % of the wrap, so no wrap | `t.cal.hi` ≈ 0 → TC0 stopped under the payload, every timing cell void. **`hi/lo` ≉ 2** → the loop was elided, or the bracket measures itself. `hi/lo` ≈ 2 but the values ~2× or ~0.5× → **CPI is not 3, and this cell has separated what `CLK-03` could not** |
| **W** — the I-side walk | 🔴 **all FRESH at every N and every S.** TCG keys TB invalidation on the *physical* address, so the KSEG1 alias buys nothing. `w.line.bits=22222222`, `w.size` fresh = n at all seven points | `w.line`: **`+8` STALE, `+16` FRESH** → a 16-byte line. `w.size`: **all STALE up to 16 KiB, FRESH appears at 32 KiB** | 🔴 **any FRESH at 1 KiB → 否證 ⓐ, the size is VOID, not approximate.** 🔴 **no FRESH at 64 KiB → the walk cannot evict; the tool could not have failed and the size is void the other way.** `V0` itself FRESH → the block is void |
| `w-line0` | all FRESH | ⚠️ **all FRESH** | any STALE → the patch is not landing or the arena is contaminated, and `w-line` is void |
| `w-back` / `w-back2` | all FRESH | `w-back`: STALE set exactly `[128,144)`. `w-back2` separates `L=32` (stales `[128,160)`) from `L=16`+prefetch (stales `[144,176)`) — **the two readings are disjoint** | any other pattern → the fill granularity is neither and `w-line`'s number is void |
| `w-assoc` | ran, `w.assoc.tm=000000ff` (the M=1 self-evict abort) | **留白 — no source.** The cell reports (T, M); the write-up derives K | **M=1 at every T must read all-STALE** (one victim cannot self-evict) and **the largest M at the smallest T must show FRESH**. Neither firing → (T,M) is a number with nothing behind it |
| `w-imem` — `CCTL 0x020` | `w.imem.differs=00000000` and the payload prints `IDENTICAL -- and that is also the no-op reading` | **未定 unless `m-imem` returned a window and the arena is provably outside it.** M4: CP0 20 is write-only and reads zero, so **no cell here can confirm a `CCTL` was accepted** | **differs** → the unqualified walk was measuring the 16 KiB scratchpad. **That is a result, not a failure** |
| **M** — the scratchpads | 🔴 `m.cu3.before=0`, `m.cu3.set=0` — **bit 31 does not stick**; all eight `mfc3` trap, `m.cause=1000042C` (ExcCode 0x0B, CpU). ⚠️ **On qemu the two explanations are CONFOUNDED** and the payload prints that it cannot separate them | `m-cu3`: **bit 31 SET** in the read-back (讀, this unit's kernel sets exactly this bit at `0x8000221C` before its first `mtc3`). `m-imem`: **留白.** A base/top pair differing by `0x3FFF` corroborates a 16 KiB I-MEM | each read equal to its own prime → the destination was never written (`F50b`'s failure, and the whole reason there are two primes). Both differing from their primes but from each other → unstable. A trap with `CU3` set → CP3 unreachable |
| **C** — coherence | 🔴 **A = A′ = B = C = D = E.** `alias.load2` returns the *second* value (no stale line), `c E l2=00000000` is immediately visible (no dirty line), `c F/B/C/G VOID`. **否證 ⓑ is *inapplicable* under qemu, not merely unmet** | `c-A0`: **`P1`** (the negative control, and it runs first). `c-A`: **`l2 = P0`** → a stale line, the DMA-stale case with no DMA engine (讀 ×1, LX4189 §5.2). `c-E`: **`P0`** → write-back. `c-F`: **`l2 = P0`** (`DWB` does not invalidate). `c-B`/`c-C`: **`l2 = P1`**. `c-G`: **`l3 = P1`** → an uncached read invalidates | `c-A0` returns `P0` → **every cell in Group C is void and so is Group V**. `c-A` returns `l2 = P1` → `c-B`/`c-C`/`c-D`/`c-F`/`c-G` are recorded **`void — no stale line to act on`, not as passes**, and `c-E`/`c-E0`/`c-E2` as `void — residency not established`. 🔴 **`c-E0` returning `P1` voids the write-policy verdict and `c-E2` does not run** — after a `DWB` the buffer has drained under both hypotheses, so `c-E2` alone cannot fail. 🔴 **`c-F` reporting that `0x100` does not write back → `c-C` DOES NOT RUN**, and that is a safety interlock: `DInval` discards this payload's own spilled `$31` without writeback |
| **V** — the D-side walk | 🔴 `Group V VOID -- c-A negative` | armed **iff** `c-A` was positive. `v-line`: `+4/+8/+12` STALE, `+16` FRESH → 16-byte line, **4-byte resolution, finer than the I side**. `v-size`: **all STALE up to 8 KiB, FRESH at 16 KiB**. `v-assoc`: 留白 | `+0` FRESH → the block is void (it was demonstrably loaded). `+64` STALE → the run exceeds any plausible line. Same two controls as `w-size` at 1 KiB and 32 KiB |
| **X** — the `cache` instruction | 🔴 `x c11`/`c10`/`c15`/`c19` **all retire, `n=0`** — and so do all 32 op-field values, **including ones MIPS32 leaves undefined. qemu does not decode the op field at all.** `x ri` traps with `cause=10000428` (ExcCode 0x0A) | ⚠️ **留白, in both directions, and the disjunction is the answer.** 讀: this unit's kernel holds 37 D-side `cache` ops and **zero** I-side ones | 🔴 **the scratch word or a neighbour changed** → the op decodes as something else on this core; the cell is void for ⓒ and is itself a finding. **`Cause.BD` set** → M3″, the instruction was in a delay slot, cell void. **`x-10` retiring but the twin's untreated victim going FRESH** → six intervening `CCTL` stages explain it as readily as `cache 0x10` does |
| **S** — `Status.IsC` | 🔴 `s.before=0`, `s.set=0`, `s.restored=0`, `s.vd=0`. All three bits masked on Malta's 24Kf, and the same run proves `Status` writes land there. **qemu is a worked example of a core WITH a write mask** | ⚠️ **bit 16 CLEAR and both control bits (6 and 24) CLEAR** — 讀 ×1, LX4189 §3.4.1 puts all three inside a written-as-zero field | **control bits set** → `Status` has no write mask, *bit 16 sticks* carries no information, cell reports **未定**. **The two control bits disagreeing** → a partial write mask, which no single control bit could have shown. **The restore not returning `Status` to its entry value** → the cell changed state it does not own and everything after it is suspect |

⚠️ 🔴 **The five cells where qemu and the device are predicted to read the
same, listed together because that is the list this file exists to make
suspect**: `h-brk` (`break.count`/`break.cause`), `w-line0`, `s-isc`,
`m-imem`'s eight traps, and every `x-*` retirement. **In each one the emulator
reaches the reading through a mechanism the device does not have** — no
D-cache, physical-address TB invalidation, a 24Kf write mask, `CU3` masked, and
no op-field decoding at all. `docs/probe3-cells.md` §6.4 states it for Group X
in advance: *"If the device also retires, the qemu run will read as agreement
and will be nothing of the kind."* **None of these five may be written up as
corroborated by the qemu run.**

### The report's length, computed per branch

The line-length model below reproduces a **measured** line exactly before it is
used to predict one: the same formula applied to `w.size` gives 68 bytes, and
all seven `w.size` lines in the committed qemu capture are 68 bytes.

| branch | bytes | lines | how it differs from the qemu capture |
|---|---:|---:|---|
| 量 **qemu** | **5,893** | **126** | the measurement everything below is built from |
| device, timer live + Group V full | **6,256** | 135 | −59 (the `CLEAR_BEV` warning) −106 (`Group T VOID`) −141 (`Group V VOID`) +669 (Group V's twelve lines) |
| … and `x-11` traps | **6,070** | 131 | −186 more: `x c15`/`x c19`, two lines each |
| … `c-A` negative, Group V stays void | **5,728** | 124 | Group V's one line survives |
| … and the timer is dead too | **5,834** | 125 | `Group T VOID` comes back |

**The worst branch is 6,256 bytes = 1.63 s at 3,840 B/s, which is 3.00 % of
`docs/probe3-cells.md` §4's wall of 208,834.** That file's §4 estimated
*推 ≈ 7 KB / 1.9 s*
before the cells were laid out; the computed figure is inside that.

⚠️ **The wall is the ESC window, not the capture.** `(60 − 5.616) × 3,840 =
208,834` bytes of report before the ~4.9 s ESC window is eaten and the vendor
kernel boots — which the operator would read as *"the payload hung"*.
⚠️ **And `5.616` is carried from §B4's budget box rather than derived**;
`LDR-15`'s window is 4.886 s and the remaining 0.730 s is named nowhere in this
repository. Marked here as it is marked there.

### What is deliberately not predicted

⚠️ **`t-ovh`'s slope, `t-hit`'s two legs, `w-assoc`'s (T, M), `v-assoc`'s, and
`m-imem`'s window.** 留白 — no file in this repository contains a measurement of
an uncached KSEG1 register-read latency, and no source of any kind gives the
associativity of either cache on this die. **A number invented here would be
decoration.** What is predicted for those cells is their *controls*: `t-ovh`
failing to scale when K doubles means the bracket measures itself; a slope of
exactly 0 is **not** a refutation, because tick quantisation forbids it.

⚠️ **`break.epc`, `bmp.point`, `bmp.count`, `bmp.firstbad`, `cells.run`,
`cells.void` and `sum`** all depend on which branches ran. They are recorded,
not predicted, and `cells.run + cells.void` is the arithmetic that says the
payload accounted for every cell.

---

## 11. The stop-loss, restated so it is on the page at the bench

| if | then |
|---|---|
| the payload **hangs** — no `rlxprobe: end`, no reboot | 🔴 **That refutes the handler, not the instruction.** Every cell writes its result to the block **before** the next one starts, and word 2 is the monotone progress marker. Power-cycle, re-enter the prompt, and read the block: `DW 80A02000 641`. The progress word says where it stopped. `P_HEADER=0x10 · P_HANDLER=0x20 · P_TIMER=0x30 · P_WALK_I=0x40 · P_IMEM_OFF=0x50 · P_SCRATCH=0x60 · P_COHERE=0x70 · P_WALK_D=0x80 · P_CACHEOP=0x90 · P_ISC=0xA0 · P_RESTORED=0xB0 · P_SEALED=0xC0` |
| `cache 0x11` traps | **That is an answer, not a failure.** `CPU-44` closes negative, the D-invalidate candidates reduce to `CCTL 0x001`/`0x200`, and **this unit's own kernel becomes a puzzle worth its own row** — it contains 37 instructions its own silicon will not execute |
| the walk returns a size that is not a power of two | record **未定** rather than the number. Rounding it to the nearest plausible value is how a build constant gets laundered into a measurement |
| two seatings and `c-A` still cannot be made to hold | `CPU-45` is **未定** and `R6` carries the conservative cost |
| `Q-J` produces nothing at all after `---Jump to address=` | the jump did not land, or `_start` faulted before the UART was touched. **`Q6-post`**: power-cycle, then `DW 80500000 8` — if it reads `00000000 …` the loader re-staged and the payload is gone, which is M8 and not new information; if it still reads `3C1D8051 …` the image was there and did not run |
| anything writes flash | **impossible by construction here.** `AUTOBURN` is read `00000000` at two points and the payload issues no burn command. Zero flash bytes is a DoD line, not an aspiration |

---

## 12. `Q-5` — the read-back, and the DoD's *"agrees on both channels"* made mechanical

`--send 'DW 80A02000 641'`. **7,593 bytes, 1.98 s** — `reply-size.py`:
`15 + 2 + 47×161 + 9`. 79 % of the largest `DW` this loader has already
executed (820 words / 9,661 bytes, 量 `H2g`), and **three digits**, so it does
not depend on `Q-3`'s answer.

### The block, from `probe3.c`'s own constants

| region | words | address range |
|---|---|---|
| header | `w0`–`w63` | `0x80A02000`–`0x80A020FF` |
| cell results | `w64`–`w255` | `0x80A02100`–`0x80A023FF` |
| 16 named rows | `w256`–`w383` | `0x80A02400`–`0x80A025FF` |
| bitmap | `w384`–`w639` | `0x80A02600`–`0x80A029FF` |
| **seal** | `w640` | `0x80A02A00` |

`RB_WORDS = 641`, and the payload carries a compile-time assertion that it is
641 while the `Makefile` computes the same figure independently.

### 🔴 The over-run control is free, and the owner file did not know until today

`LDR-07` rounds the word count **up** to a multiple of four, so
`DW 80A02000 641` prints **161 lines = 644 words**. The block is 641 words. The
payload poisons `w0`–`w648` (`RB_POISON_W = RB_WORDS + 8`, 讀 `probe3.c:107`).

**So the last reply line carries three margin words that no command asked for:**

```
80A02A00:	<the seal>	DEADC0DE	DEADC0DE	DEADC0DE
```

**Refuted by**: any of `w641`/`w642`/`w643` ≠ `DEADC0DE` → **the run wrote past
its own block.** That is what the margin exists for, and it is checked without a
second command. If it fires, `Q5-margin` (`DW 80A02A04 8`, **118 bytes**) reads
the remaining five margin words; it is not in the ```cells``` block because it
must not run on a good seating.

⚠️ **This is a finding about the read-back encoding, so it does not stay here.**
`docs/probe3-cells.md` §4 owns that encoding and now carries it, along with the
`DEADC0DE` ambiguity below — a prediction block is frozen and is not where a
fact about the instrument should live.

### The three-way agreement, and it was validated on silicon today

**量 2026-08-29**, run against `probe2`'s committed seating —
`bench/2026-08-25b/H2g.log` (the `DW`) against `bench/2026-08-25b/H2a.log` (the
UART) — **a different payload, a different block, already on this silicon**:

| | probe2, 量 today | on probe3 |
|---|---|---|
| (1) the UART's own `rlxprobe: sum=` line | `EC84408D` | the `sum=` line in `QJ` |
| (2) the seal word | `w808` = `EC84408D` | `w640`, first word of the `80A02A00:` line |
| (3) `sum(w0 … w_seal−1)` of the read-back **− `0x10`** | `EC84409D − 0x10` = `EC84408D` | `sum(w0…w639) − 0x10` |
| all three agree | **PASS** | the DoD line |

🔴 **The `− 0x10` is not a fudge.** `progress(P_SEALED)` re-stamps word 2 *after*
the sum is taken, so a straight re-sum of a recovered block is high by exactly
`P_SEALED − P_RESTORED = 0x10` on every complete run. `probe3.c` says so in a
comment, `H_SEAL_KIND = 1` says so in the block so the desk does not have to
read the comment, and **today the arithmetic was reproduced on probe2's real
capture rather than taken on trust.**

🔴 **The negative control fired.** Flipping one bit of `w0` in the recovered
block changes the re-sum and the check fails. **A checksum comparison that
cannot fail is not a checksum comparison**, and this one was shown to fail
before it was written down.

⚠️ **The first attempt at this check FAILED, and the failure was mine, not the
procedure's**: `probe2`'s `RB_WORDS` is **809**, not the 817 that `H2g` read —
817 is `RB_POISON_W`, the poisoned extent, and `docs/probe3-cells.md` §3
describes probe2's block by that figure. Reading the seal at `w816` returned
`DEADC0DE`, which is poison, and the check correctly said FAIL. **Recorded
because the same off-by-the-margin is available at `w640` versus `w648` here**,
and because a control that fails first and passes after a stated correction is
worth more than one that passed immediately.

### What the head must say

| address | expected | why |
|---|---|---|
| `0x80A02000` | **`524C5833`** — `'RLX3'` | `RB_MAGIC`. **Not `524C5831` or `524C5832`** — those are `probe1` and `probe2`, and they are the same two constants `P2`'s refutation list names |
| `0x80A02004` | **`7E41C9D0`** | `RLX_NONCE_W`, the same value the banner printed. Two channels, one constant |
| `0x80A02008` | **`000000C0`** | `P_SEALED`. Anything lower is where the run stopped |

### The cross-check table — one UART line, one word, one line of the reply

Derived from `probe3.c`'s `#define H_*` list, not transcribed from it. The reply
prints four words per line, so word `w` is on reply line `⌊w/4⌋`, column `w mod
4`, and that line's own address label is `0x80A02000 + 16⌊w/4⌋`.

| UART line | word | address | reply line label | col |
|---|---:|---|---|---:|
| `pc=` | 3 | `0x80A0200C` | `80A02000:` | 3 |
| `flags=` | 5 | `0x80A02014` | `80A02010:` | 1 |
| `rb=` | 6 | `0x80A02018` | `80A02010:` | 2 |
| `status=` | 7 | `0x80A0201C` | `80A02010:` | 3 |
| `handler_words=` | 9 | `0x80A02024` | `80A02020:` | 1 |
| `install.changed=` | 10 | `0x80A02028` | `80A02020:` | 2 |
| `install.bad=` | 11 | `0x80A0202C` | `80A02020:` | 3 |
| `break.count=` | 13 | `0x80A02034` | `80A02030:` | 1 |
| `break.cause=` | 14 | `0x80A02038` | `80A02030:` | 2 |
| `break.epc=` | 15 | `0x80A0203C` | `80A02030:` | 3 |
| `arena=` | 16 | `0x80A02040` | `80A02040:` | 0 |
| `tmpl=` | 19 | `0x80A0204C` | `80A02040:` | 3 |
| `bmp.point=` | 22 | `0x80A02058` | `80A02050:` | 2 |
| `bmp.count=` | 23 | `0x80A0205C` | `80A02050:` | 3 |
| `restore.mismatch=` | 24 | `0x80A02060` | `80A02060:` | 0 |
| `restore.stillhandler=` | 25 | `0x80A02064` | `80A02060:` | 1 |
| `status_end=` | 26 | `0x80A02068` | `80A02060:` | 2 |
| `g.ca=` | 28 | `0x80A02070` | `80A02070:` | 0 |
| `g.cf=` | 29 | `0x80A02074` | `80A02070:` | 1 |
| `cells.run=` | 44 | `0x80A020B0` | `80A020B0:` | 0 |
| `cells.void=` | 45 | `0x80A020B4` | `80A020B0:` | 1 |
| `kseg0=` | 48 | `0x80A020C0` | `80A020C0:` | 0 |
| `g.timer=` | 49 | `0x80A020C4` | `80A020C0:` | 1 |
| `t.sep.a=` | 50 | `0x80A020C8` | `80A020C0:` | 2 |
| `t.sep.b=` | 51 | `0x80A020CC` | `80A020C0:` | 3 |

**All 25 pairings resolve, and every one of the 45 defined header words is
`rb_put()` somewhere in the source** — checked mechanically, so a word that is
named and never written would have been caught here rather than at the bench.

**Refuted by**: any pairing disagreeing between the two channels → one of them
is not reporting the run that happened. That is a stronger statement than either
channel alone can make, and it is the whole reason 16 rows go out on **both**
channels rather than only into RAM.

---

## 13. What this block does not do

* **It writes no flash byte.** `AUTOBURN` is read `00000000` at two points, one
  of them immediately before the transfer, and the payload issues no burn
  command. `GEOM=0`, so `rlx_r3k_size` — which can write 1 MiB — is not linked.
* **It does not answer ⓐ on one number.** The walk's number and the kernel's
  number are two different claims, and `R1h-4`'s write-up says so **even when
  they agree**. A build constant that agrees with a measurement is
  corroboration; a build constant quoted as a measurement is a geometry number
  wearing a measurement's clothes.
* **It cannot separate a 16 KiB I-cache from the 16 KiB I-MEM by size.** They
  are the same size, so no size measurement can tell them apart. `w-imem` is the
  discriminator and **M4 makes even that 未定 unless `m-imem` returned a
  window**, because CP0 20 is write-only and *identical* is also the no-op
  reading.
* **It says nothing about `R3`.** That is power cycle 2, `bench/2026-08-30b/`,
  and its block is frozen. The only thing the two share is the seating and the
  order within it.
* **It does not test this die's load-delay behaviour.** `hazlint` gated the
  build with 0 violations in 804 loads; a payload that runs is consistent with a
  hazard that has not been hit.
* **`check-predictions.py` cannot be satisfied today.** Run at the desk on the
  day this was written it reports `0 of 13`, because control `N2` — *a predicted
  cell whose capture does not exist* — fires on all thirteen. What the desk run
  establishes is that the file parses, the ```cells``` block is non-empty, and
  the controls hold. The ordering claim is established by the same command
  **after** the seating.
* **mtime is not a cryptographic timestamp.** `touch -d` rewrites it, and
  **git does not store it at all** — 量 2026-08-29, on a fresh clone 128 of 156
  cells read as out of order. This proves ordering to a cooperative auditor
  standing at the machine the captures were taken on. It proves nothing after a
  push.
