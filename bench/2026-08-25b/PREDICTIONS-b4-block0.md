# PREDICTIONS — Session B4, `R1g-4b`, block 0

**Written 2026-08-25, at the desk, before power is applied.**
`tools/check-predictions.py` checks that claim against this file's mtime and each
capture's `.log` mtime. Nothing here may be edited after the block has run — even
a typo fix moves the mtime and the check fails, correctly. Corrections go in a
new file.

**Instrument: `tools/console-capture.py` `1.3`** — 量 tonight, `TOOL_VERSION` read
out of the file. (`R1g-4a`'s sealed block said `1.2` and the tree was already
`1.3`; a stale version number costs one failed prediction against the instrument,
which is noise in the column that has to stay signal.)

**Nothing in this block uploads or executes anything: eight reads and one ESC
stream, zero bytes written to the device.**

## The directory rule, generalised — because the file that needed it cannot be edited

`bench/2026-08-26/PREDICTIONS-b4-block0.md` is sealed and says: *if the seating
slips past 2026-08-26, this file is not edited.* **The seating went earlier, not
later, and its rule covered only later.** The general form, which
`bench/2026-08-26/README.md` also carries:

> A prediction block is bound to a directory; a directory is bound to one power
> cycle. **If the run happens on any power cycle other than the one the directory
> names — earlier, later, or a different unit — the file is neither edited nor
> moved.** A new block is written for the directory the run actually uses, and
> the orphaned directory records that it holds a prediction with no run.

**This seating is `bench/2026-08-25b/` and no capture may ever be written into
`bench/2026-08-26/`.** 量 tonight: `check-predictions.py` on that sealed file
reports `0 of 9 captures came after the prediction, 9 did not`, exit 1, and it
will report that forever. If tonight's captures landed there instead, three of
its nine cells — `A-catch`, `A0`, `H0d-b` — would flip to `ok` against a run the
file was not written for, because their expected values are power-cycle
invariant. **Three passes out of nine is worse than nine failures**, because the
three look like evidence. It is the `D2c` / `E10d` defect class.

## What this block is for, and what changed since the sealed one

`R1g-4a`'s block 0 ran nine cells on 2026-08-25. This one is **not** a repeat of
it. Four of those nine are re-taken and two are deliberately not, and the
division is the point:

| class | what it rests on | re-take? |
|---|---|---|
| (a) | a property of the **loader** — `trap_init`, `.bss`, the command table. Re-derived identically on every boot | cheap corroboration |
| (b) | a property of the **core** — instruction encodings, cache behaviour | no |
| (c) | **DRAM content that no boot rewrites** — power-on bias, or a previous payload's leftovers | 🔴 **mandatory** |

🔴 **`H0c` is class (c), and this is the measurement that says so.** Three cold
power-ons, eight words at `0x80A00000`, an address nothing had written before
each read:

```
24b  55617135 0077BF55 11744D3C E1553515 75576793 732111E3 1D187415 0501F751
24c  75693930 00F7BF55 13344D3C A1573115 75036293 322913E3 191A3415 0520F351
25   55617135 00F73F55 11744D3C E1553515 75576793 332111E3 1D187415 0521F751

24b vs 24c:  27/256 bits differ, 8/8 words      positive control (self):      0/256
24b vs 25 :   4/256 bits differ, 3/8 words      negative control (vs H0a):  123/256
24c vs 25 :  25/256 bits differ, 8/8 words
```

**量 2026-08-25 at the desk, from `bench/2026-08-24b/G4-addr-probe.log`,
`bench/2026-08-24c/G0-head.log` and `bench/2026-08-25/H0d-a.log`.** Both controls
fire, so the 4–27 range is a reading and not an artefact of the comparator — the
mistake `R1g-4a`'s own error 3 was.

**So this DRAM's power-on bias is reproducible but not deterministic.** The
consequence for tonight: `probe2` saves 22 words of `0x80000000`, overwrites
them and restores them from a copy taken **tonight**. `§H2h` compares the result
against `H0c`. Against 2026-08-25's `H0c` that comparison would show of order
sixteen differing bits **on a perfect run**, and `§H2h` calls a difference a
failure. **The false alarm reads as *`probe2` corrupted physical 0*** — the one
outcome that would stop the gate. `H0c` therefore runs tonight, and at `32`
words rather than `8`.

🆕 **And 32 words buys a second thing that 8 does not.** `install.changed` stops
being *non-zero* and becomes a number written before the run — see the `H0c`
row below.

`H0a2` (`DW 8040054C 32`) and `H0a3` (`DW A0000080 32`) are **not** repeated.
`H0a2` is a RAM-to-RAM identity proving `trap_init`'s copy landed — class (a),
and it needs no predicted value, so a second instance adds nothing a third boot
of the same code could fail. `H0a3` is about the D-cache being coherent for that
page, which `H1` settled on 2026-08-25 as a property of the core: **the D-cache
is write-through** (cell 1 against cell 5, `ma = 240222b2` both). Class (b).

---

## Cells, in order

```cells
bench/2026-08-25b/A-catch
bench/2026-08-25b/A0
bench/2026-08-25b/SPI-cold
bench/2026-08-25b/H0a
bench/2026-08-25b/H0b
bench/2026-08-25b/H0c
bench/2026-08-25b/H0d-a
bench/2026-08-25b/H0d-b
```

Every command is `/usr/bin/python3 tools/console-capture.py capture --port
/dev/ttyUSB0 --baud 38400 --out bench/2026-08-25b/<cell>` plus the arguments in
the row. **No line reaches 128 characters**; the longest is 15
(`DW 80A01000 817`, and that one is block 2's).

**Every byte count below came out of `python3 tools/reply-size.py predict`, not
out of a person.** Both of `R1g-4a`'s arithmetic errors were in blocks written
at the bench and neither was in the block written at the desk; `LDR-07`'s
formula has been a tool since, and `check-predictions.py` verifies ordering, not
arithmetic.

---

### A-catch — `--esc 180 --esc-period 0.002 --seconds 200 --cr-settle 3`

The capture starts **first**; power is applied while ESC is streaming. `180` and
not `45`: a 45 s window was missed on 2026-08-24 with the boot beginning at
t = 64.2 s, and it cost a power cycle.

| | prediction |
|---|---|
| byte 0 | **not predicted** — the CP2102's framing artifact, `0x00` on 2026-08-25 and `0xFF` on `24c`, the two idle polarities of a line not yet driven. It is not noise: `CLK-14` uses it as the cold-boot `t=0` anchor |
| bytes 1–181 | 🔴 **byte-identical to `bench/2026-08-24c/A-catch.log` and `bench/2026-08-25/A-catch.log`** — the cold boot text through the full `<RealTek>` prompt. 量 tonight: those two agree on bytes 1–181 (and in fact to byte 1621), and the negative control — the same comparator against `H1b.log` — separates at byte 0. This would be the **fourth** consecutive |
| byte 182 | the first ESC echo, in both archived captures |
| the `C-8` marker | a **space** at `ramSize: 32M\n\r \n\r`, where a warm boot prints `Reboot Result from Watchdog Timeout!`. That is what `boot-timeline.py` splits cold from warm on, and it must be the cold form |
| after the prompt | *n* × (128 ESC → `Unknown command !` → `<RealTek>`). *n* is **not** predicted; it depends on when power is applied |
| last bytes | a prompt, not a run of ESC — `terminate_esc_line` writes its own CR. `cr.esc.prompt_seen: true` |
| metadata | `tool_version: "1.3"`, `esc.esc.requested_period_s: 0.002`, and `esc.esc.achieved_period_s` ≈ **0.0021** — 量 precedent `bench/2026-08-25/H3c-D4` got **2.118 ms** against a requested 2.000, because the quotient includes this process's own scheduling |
| **file size** | ⚠️ **≈100–120 KB, ten times any previous `A-catch.log`, and that is the instrument and not a fault.** ~1.24 bytes of log per ESC written (128 echoed + a 31-byte `Unknown command !` cycle), 500 ESC/s, ~165 s after the prompt. `esc.esc.writes` in the metadata is the check |

🔴 **What `--esc-period 0.002` can and cannot settle here, because the sheet's
reason for it does not survive reading the instrument.** `SPEC.md` §17
`CLK-15 殘留` proposes it to test whether the within-group 2.5 % / 2.7 % spread is
the instrument. **The mechanism does not connect.** 讀,
`tools/console-capture.py:373`: `drain()` waits in `select()` and timestamps a
chunk the moment it arrives, with a timeout of `min(remaining, 0.05)` — the ESC
period bounds how often an ESC is *written*, not how promptly a device byte is
*read*. The 20.35 ms grid that blocked `CLK-08b` quantised intervals measured
**between ESC echoes**; `CLK-14`'s and `CLK-15`'s endpoints are both bytes the
**device** sent. **And n = 1 cannot measure a spread in any case.**

What it can give, and this is what it is being run for:

1. **A one-point bias check.** If tonight's cold `Booting… → chipName` falls
   outside `CLK-15`'s published cold range **348.0–356.9 ms**, the grid mattered
   after all and that is a finding. Inside it, the reading is compatible with
   both and says nothing about the spread.
2. **A second `CLK-03` data point on a different grid**, from block 1's
   `J 80500000` capture. `CLK-03` has exactly one experiment and one point
   (Δ = 123.7 ms, 2026-08-25) and it is load-bearing for the `--esc-after`
   budget.

**The spread question is desk work and needs no power**: the nine `.timing`
files are on disk, and the term to look at is chunk boundaries — `drain()`
records one timestamp per chunk at `offset` before the chunk, so a first byte
delivered together with the ten after it carries the arrival time of the group.
That is the experiment §17 should carry, and it is not this one.

**Refutes**: nothing about the device. It is the window, and a
`prompt_seen: false` beside a full settle is what a missed one looks like from
the instrument's side.

---

### A0 — `--send 'DW 8040DBC0 1' --seconds 4`

| | prediction |
|---|---|
| bytes | **71** |
| content | `8040DBC0:` then `8040B070 00000000 80409A9C 8040B074`, then the prompt — **byte-identical to `bench/2026-08-24b/A0.log`, `24c/A0.log` and `2026-08-25/A0.log`.** This would be the fourth consecutive, same load base, same table address, same stride |

**Two jobs, and the second is why it is first.** Rule 1: one command with a
precomputed answer, re-establishing that re-opening the port did not disturb the
board. And it **spends the post-re-enumeration throwaway** — `C-19`: the first
command after the console adapter re-enumerates is echoed and not acted on,
signature *echo + prompt + no data line*, 24 bytes
(`reply-size.py` classifies it `ECHO-ONLY`).

🔴 **That signature is indistinguishable at the bench from `H0a` finding
nothing**, and `H0a` is the cell that forbids `probe2`. Any `Unknown command !`
here, or a reply with no data line, and the cell is re-sent before anything is
read into.

---

### SPI-cold — `--send 'DW B8001200 4' --seconds 4` 🆕

Four words: `SFCR` `0xB8001200`, `SFCR2` `0xB8001204`, `SFCSR` `0xB8001208`,
`SFDR` `0xB800120C` (`SPEC.md` `REG-13`, `MAP-05`,
`docs/loader-flash-write.md` §2, three independent sources on the addresses).
**`SPEC.md` `REG-13` records this window as 未讀 — never read on this device.**

| | prediction |
|---|---|
| bytes | **71**, 1 line, 4 words |
| `SFCR`, `SFCR2` | 🔴 **not predicted.** These are the cold/warm comparison itself; a predicted value here would be the map the cell is testing |
| `SFCSR` | `w & 0xF8000000 == 0xF8000000` — `CSB0`=1 and `CSB1`=1 (both chip selects **inactive**, reset 1), `LEN`=`11` (4 bytes, reset), `SPI_RDY`=1 (ready, not busy). 讀, D table 10 via `docs/loader-flash-write.md` §2. Bits 26:16 not predicted |
| `SFDR` | 🆕 **the positive control, and it is what makes this cell able to fail.** Predicted to contain the byte sequence `1C 70 16` — i.e. `1C701600` or `001C7016` |

**Why `SFDR` is predictable at all.** `ComSrlCmd_RDID()` at `0x804058bc` runs
**twice on every boot of this board** and its last act is `lw s0,0(s0)` from
`SFDR` — 讀, `docs/loader-flash-write.md` §2's disassembly. Nothing writes `SFDR`
after that on the idle path. And `SPEC.md` `REG-21` (量, `B2`) holds the flash
chip descriptor at `0x8040FBD4` as `001C7016 1C701600 …` — **the same three
bytes, stored two ways**: EON `0x1C`, type `0x70`, capacity `0x16` = 4 MiB.

So this one read either **confirms the JEDEC ID at the register that produced
it**, closing a loop `docs/loader-flash-write.md` left open with *"the value is
still not known"*, or it disagrees with `REG-21` — which is worth more.

⚠️ **If `SFDR` reads `00000000` or `FFFFFFFF`, the register does not retain**,
the positive control is void, and the cell degrades to `SFCR`/`SFCR2`/`SFCSR`
for the cold/warm comparison only. That is a reading, not a fault, and it is
written here so it is not read as one.

🔴 **Safety, stated before it is typed.** `DW` issues **loads only**. On this
controller a command is issued by **writing** `SFDR` (`sw v0,0(s0)` with
`0x9F000000`, 讀, the `RDID` disassembly); reading it fetches the answer. No
`sw`, no `EW`, no flash write, and `CLAUDE.md`'s zero-write rule is about flash
bytes.

⚠️ **You cannot read only the three safe registers.** `LDR-07` rounds the word
count **up** to a multiple of four, so `DW B8001200 1` through `4` all print the
same four words. The choice is four or none, and it is four.

**Refutes**: `CLK-15 冷暖差`. This is the cold half; `SPI-warm` in block 2 is the
warm half, after `probe2`'s own watchdog reset. **If the four words are identical
cold and warm, the SPI-divider hypothesis is excluded** and the next candidate
is the NOR's own power-on wake-up. If `SFCR` differs, the divider is the
mechanism and the differing field names itself.

---

### H0a — `--send 'DW 80000080 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | **byte-identical to `bench/2026-08-25/H0a.log`**, the loader printing upper-case hex, tab separated |

```
80000080:  401B6800  00000000  00000000  3C1A8041
80000090:  275AEB40  337B007C  035BD021  8F5A0000
800000A0:  00000000  03400008  00000000  00000000
800000B0:  00000000  401A6000  00000000  001AD0C0
800000C0:  07400003  03A0D821  3C1B8041  8F7BDD40
800000D0:  03A0D021  277DFF50  AFBA008C  AFA30024
800000E0:  AFA00018  40036000  AFA20020  AFA300A8
800000F0:  AFA40028  40036800  AFA5002C  AFA300AC
```

🔴 **Words 0–10 are the gate** — `mfc0 k1,c0_cause` / nop / nop /
`lui k0,0x8041` / `addiu k0,k0,-5312` / `andi k1,k1,0x7c` / `addu` /
`lw k0,0(k0)` / nop / `jr k0` / nop. **If they are not there, `probe2` must not
be run**: its handler would go where the core does not fetch from. Words 11–31
are the tail of `trap_init`'s 128-byte copy and are **not zero**; word 13
`401A6000` is `mfc0 k0,c0_status`, the first instruction of the loader's IRQ
handler at `0x80400580`. An operator who reads nonzero words past index 10 as a
mismatch would abort for nothing.

**Why it is re-taken although it is class (a).** `trap_init` re-makes this copy
on every boot, so carrying it across a power cycle is defensible — but it is the
one cell that **forbids the payload**, and a gate satisfied on a different power
cycle is 讀 for this run and not 量. It costs 401 bytes.

**What each miss means** is in `RUNSHEET.md` § Session B4 under *If `H0a` does
not match*, written before this file and not restated here. The row that matters
most: **`42000018` (`eret`) anywhere in the 32** refutes the R3000 reading
outright, `probe2` must not run, and it is the most valuable outcome available
tonight at zero cost.

⚠️ **It does not settle which base the core fetches from.** That is
`Status.BEV`, no loader command reads CP0, and `probe2` is the instrument.

---

### H0b — `--send 'DW 8040EB40 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | **byte-identical to `bench/2026-08-25/H0b.log`**: `[0] = 80400580`, `[23] = 804007C0`, **the other thirty = 80400BE8** |

Line by line: line 0 is `80400580 80400BE8 80400BE8 80400BE8`; lines 1–4 are four
`80400BE8` each; line 5 is `80400BE8 80400BE8 80400BE8 804007C0`; lines 6–7 are
four `80400BE8` each.

**Runs whatever `H0a` did**, and it is what separates the failures: `.bss` is
zeroed at boot by the loop at `0x8040046C`, so an **all-zero `H0b` means
`trap_init` never ran**, distinguishable from every other reading.

**Why it is re-taken.** `exception_handlers[9] == 0x80400BE8` is the single link
the whole `SAFE_A0` argument rests on, and tonight is the seating that
deliberately executes a `break`. If our handler is not installed, `break` falls
through to entry 9 and this word is what decides whether the failure **prints**
or is silent. The safety net's own check, on the boot it protects.

---

### H0c — `--send 'DW 80000000 32' --seconds 6` 🔄 **32, not 8**

The UTLB refill vector. `notes/cache-model.md` records the loader as **never
populating it**, so almost all of it is DRAM power-on bias — class (c), the
reason this whole block exists.

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| word 0 | **`5A5AA5A5`** — 量 2026-08-25, and class (a): stage 1's DRAM-sizing probe writes it on every boot |
| words 1–31 | 🔴 **not predicted, and predicted NOT to match 2026-08-25.** The measurement at the head of this file says the bias moves by 4–27 bits per 256 across power cycles |

🔴 **The escalation, and it is `cache.S`'s.** If word 0's top six bits are
`000010` (`j`) or `000011` (`jal`), the no-demonstrated-brick-path argument is
void and nothing may be run until it has been re-made. `5A5AA5A5 >> 26` =
`010110` = 22 = `BLEZL` — safe, and that is the reading to reproduce.

🆕 **What the 32 words buy: `install.changed` becomes a number instead of a
threshold.** `§H2a`'s expected value is *non-zero*, which nothing can fail.
`install_handler()` writes 22 words to **both** vectors and counts, per position,
whether the read-back differs from the pre-install word. So:

```
install.changed = 21  (general vector: 22 positions, ONE coincidence at index 10,
                       where the handler's third nop meets H0a word 10 = 00000000)
                + 22 - z   (UTLB vector: z = how many of the seven nop positions
                            {5,6,9,10,13,17,18} of THIS boot's H0c read 00000000)
```

The 22 emitted handler words are 量 tonight from `build/probe2/probe2.elf`
(`0x80500210`–`0x80500267`):

```
3C1A8050 275A25B0 3C1B2000 035BD025 401B6800 00000000 00000000 AF5B0004
401B7000 00000000 00000000 AF5B0008 8F5B0000 00000000 277B0001 AF5B0000
401A7000 00000000 00000000 275A0004 03400008 42000010
```

**Predicted `install.changed = 0000002B` (43)**, i.e. `z = 0` — no UTLB word in
0–21 reads exactly zero. `H0c` is what turns that from a prediction into an
arithmetic identity, and it is checkable from this block's own capture.

✅ **The model has a positive control and it already passed.** The qemu build is
25 handler words × 2 vectors = 50 positions, with the vector page starting as
zeros, so the same model predicts `50 − 20` (ten nops × two vectors) = **30**.
量 tonight under qemu: `install.changed=0000001e` = **30**, exact.

---

### H0d-a — `--send 'DW 80A00000 8' --seconds 4`

| | prediction |
|---|---|
| bytes | **118**, 2 lines |
| content | 🔴 **`524C5831 9D34F1C7 00010001 80500634 / 0000000D 00000010 00000001 80500C00`** — `probe1`'s block header from `bench/2026-08-25/H1c.log`, **if `MEM-15`'s retention holds across tonight's power-off** |

🔴 **The rule for this address is reversed tonight and the reversal is the
point.** `§H0d` says *word 0 is neither `DEADC0DE` nor `524C5831`/`524C5832`*.
That was written when `0x80A00000` had never held a block. It has held one since
2026-08-25. **So `524C5831` here tonight is the CORRECT reading and not the
failure.**

What it is worth: `MEM-15` currently rests on a **two-word** canary surviving
three warm resets. This is **137 words with a valid seal, a per-build nonce and
thirteen filled rows, across a real power-off** — a chosen-value remanence
measurement, and the strongest form of `MEM-15` this project can get without
spending anything.

Either outcome is informative:

| reading | what it says |
|---|---|
| `524C5831 9D34F1C7 …` | the block survived. `MEM-15` upgrades from a canary to a 548-byte chosen value. **And it is exactly the hazard `H0d` exists for**: a `DW 80A00000 137` typed after a hang tonight would return this and look like a completed run |
| DRAM bias | the power-off was long enough to clear it. Note the bias itself is not deterministic — see the head of this file — so *this is bias* is a judgement about shape, not a comparison against a stored value |

---

### H0d-b — `--send 'DW 80A01000 8' --seconds 4`

`probe2`'s `RESULT_BASE`. **Read before anything is uploaded, because `probe2`
poisons 817 words from here as its first act.**

| | prediction |
|---|---|
| bytes | **118**, 2 lines |
| required | 🔴 **word 0 is neither `DEADC0DE` nor `524C5832`.** The rule stands unchanged **at this address**, where nothing has ever written a block: `probe2` has never run on this device |
| content | close to `55711135 40775555 17344D7C E1553115 / 15577213 71311143 15543515 0520F351` — 量 2026-08-25, and nothing has written here since. Expect a handful of differing bits, on the head of this file's measurement, **not** a byte-identical match |

**Refutes**: that a result block read after the run belongs to this run.
`0x80A01000` had never been read on this device before 2026-08-25 and has still
never been written. **If word 0 is `524C5832`, a `probe2` has run on this device
and nothing in the record says so** — stop, and find out what did it before
anything else is typed.

⚠️ `probe1`'s block at `0x80A00000` is 137 words = `0x224` bytes, so it ends at
`0x80A00224` and does not reach here. The two blocks are 4 KiB apart by design
and both are recoverable from the same seating.

---

## What this block does not do

- **It writes nothing.** Eight `DW` reads and one ESC stream. No `EW`, no `EB`,
  no `put`, no `J`, no flash.
- It cannot measure `Status.BEV`, and therefore cannot say which vector base the
  core fetches from. Only `probe2` can, and `probe2` is safe to launch on that
  question: it reads `Status` itself and refuses to install if `BEV` is 1 —
  `progress = 00000010` at block word 2 and bit 22 set in `status` at word 6,
  which is two independent signals. **It does not stamp `0xBE71BAD1`**; that
  constant is in no payload source (量, `grep -rin be71bad1 tools/` with
  `DEADC0DE` as the positive control) and three files published it until tonight.
- `SPI-cold` is half a cell. Without `SPI-warm` it is four unpredicted words at
  an address never read, and only `SFDR`'s `1C 70 16` can fail on its own.
- Nothing here is a CP0 reading, a cache-geometry reading or a timing
  measurement. `CPU-25` is **not** measured this seating either — `GEOM=1` is
  refuted by `probe1` cell 4's own result, because `rlx_r3k_size` needs
  isolation to work and this core does not isolate, so it can only return `0`,
  which is its own *the core does not answer* value. The census's `Config` /
  `Config1` rows are the free route and a `probe3` eviction walk is the real
  one; both are block 1's and the desk's, not this block's.
