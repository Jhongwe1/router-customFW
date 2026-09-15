# Block 22 — `R1-pub-3` slot 2 and `R1-pub-4b` on one power cycle, and the first cell in this project whose two predictions come from two of its own documents

**Frozen before power.** Seating 24. One power cycle, budget one.

---

## 0. What this block is, in one paragraph

Two payloads on one power cycle. **Bare metal first**: `probe3` carrying a new
Group L — a D-cache footprint ladder at six sizes and **two arena bases**, plus
a five-leg A–B–A — which is simultaneously `R1-pub-3` slot 2 and **`CPU-45`'s
pre-registration**; those are not two riders sharing a seating, they are one
`J`. **Then Linux**: `uc1`, carrying `ucost`, which prices the emulation
surface `R1-pub-4a` found — and, in one cell, asks a question two tracked files
in this repository answer differently. Plus a `map 0` that brackets seating 23,
and a re-run of one `4a` row, which is the first time any column-② row has ever
been repeated.

🔴 **If the seating does not happen on 2026-09-16**, this directory is named for
a day the seating did not happen on — which is `bench/2026-08-30`'s defect,
still in the record, unfixable after the fact. **Nothing here has been measured
yet, so the fix before power is free**: recreate the directory under the right
date, move the card and re-point § 10 and § 11, and freeze again. After power it
is not free. `tools/capdate.py` is the checker.

---

## 1. The two images, pinned

| what | value |
|---|---|
| `probe3.bin` | `tools/rlxprobe/build/probe3/probe3.bin`, **33,616** bytes |
| `probe3` sha256 | `c2069e250794ee7fc934787bd2516fb56b6e85830b3f8e8dc1ef12c0263323af` |
| `probe3` read-back | `DW 80A02000 762` — that is `RB_POISON_W` = 754 + 8, **not** the 754 `make show` prints |
| `uc1` `RECIPE_ID` | **`efa93621`** — the board must print `RLXFW-ID0=EFA93621` |
| `uc1` vmlinux | 4,141,974 bytes, sha256 `0e8a452283b093d9…` |
| `uc1` `nfjrom` | `$FWRE_WORK/rebuild/bench-only/uc1-work-20260916/uc1-20260916/kroot/rtkload/nfjrom`, **1,059,840** bytes |
| `nfjrom` sha256 | `d66155754c2716483a4c13aa93c8e567c650313fec9ca3ac76e1c93b6097b0d6` |
| `ucost` | `build_id` **`8403799745aeb189`**, 16,692 bytes stripped, static, no `PT_INTERP` |
| `uprobe` | `BUILD_ID` **`a87be346bb83e7f9`** — **unchanged**, and § 7 is why |

🔴 **PIN `probe3` BY sha256 AND NEVER BY ITS BANNER.** `RLX_NONCE` is a
hard-coded literal in the source and the Makefile never overrides it, so this
image's banner is **byte-identical** to the 2026-08-31 build's. A banner check
would pass on the wrong image. The `DW 80500000 8` head cell is the check that
works.

---

## 2. What the desk settled today, with zero power

1. **The ladder leaf exists and its timed region is `rlx_tc_walk`'s.** 量,
   objdump over `cells.o`: the five-instruction inner body is **byte-identical**
   (`8d630000 256b0010 2739ffff 1720fffc 00000000`), both outer-loop spans are
   10 instructions, and exactly **four** words differ in the whole routine — the
   raw-pointer register, two prime constants, and the reload, which is `addu`
   where the walk has `addiu`, at the same position and the same cost. That is
   what licenses § 5's exact predictions rather than approximate ones.
   `tools/test-rlxprobe.sh` § `L1` is the standing gate; suite **233 passed, 0
   failed**.
2. **It is not a copy of `rlx_tc_stride`, and that was the decision.** 量: that
   leaf's inner body is **seven** instructions, floor `0.25007` ticks against
   the five's `0.17862` — **40 % higher**. A ladder built from it would have
   carried a floor that is not the `~0.07 ns` both owner files quote.
3. 🔴 **The A–B–A's pre-registered prediction was wrong by 8.9×** and is
   corrected in place — § 5.3.
4. 🔴 **`4b`'s ruler was wrong** and is corrected — § 6.2.
5. **`uprobe`'s digest did not move**, checked after every edit — § 7.

---

## 3. The order, and it is forced rather than chosen

**Bare metal first, on the cold boot, before any `J` to a kernel.**

* `probe3`'s every result word is a `TC0CNT` count, and `CLK-17` measured that
  register at **14,286,057 Hz at the loader prompt** and **200,005 Hz under
  Linux** — 71.4× apart. `TC_WRAP = 142858` and *one tick is 69.998321 ns* are
  **loader-state constants**. Run after a Linux boot and every tick in Group L
  is wrong by 71.4× with nothing in the payload able to notice.
* After `J` to a kernel **the loader is gone for that boot**. `reboot -f` is the
  way back and costs 2.407 s — but it is a **watchdog bite, not a power-on
  reset**, and *that the loader's own init undoes all of it* is 推.
* So: **power-on → loader → probe3 → `DW` → upload `uc1` → boot → Linux cells.**
  Never the reverse.

⚠️ **Group T runs before Group L inside the one `J`, and that ordering is
load-bearing.** `l.a.w4k` is required to reproduce `t.hit.ks0` *in the same
capture*; if the ladder ran first it would warm the arena `t-hit` then measures
and the cross-check would be circular. Stage 2 then stage 2b.

---

## 4. The guards

* **Zero flash writes. Zero `FLR`. Zero `EW`/`EB`/`FLW`/burn.** Decided here,
  before power. The `cardnum` rows in § 10.1 are what enforce it.
* **`DW 8040D4A0 1` must read `00000000` before either upload.** An echo is not
  the burn flag; `C-6` is the measurement that says so.
* **`DW 80500000 8` must match `probe3.bin`'s own first eight words, or DO NOT
  JUMP.** `first word 3c1d8051`.
* **`DW 80A02000 4` before the upload** is the negative control on the write:
  the block must NOT already hold this run's values.
* 🔴 **If `c-A` reads `P0` (positive) this seating, Group V's result is VOID for
  a stated reason**: `A_LAD1` is `A_VSIZE`, Group V's own arena, and Group L
  pre-warms 32 KiB of it at stage 2b where Group V runs at stage 7. Group V has
  always been void because `c-A` has read negative three times, so this has
  never arisen — and it would arise silently. ⚠️ Narrower than it sounds:
  `t-hit` already walked 4 KiB of that arena on every previous seating, so this
  is a widening from 4 KiB to 32 KiB, not a new class.

---

## 5. Slot 2 — and it is `CPU-45`'s pre-registration, not a rider on it

`docs/rlx-cache-and-cp0.md`'s own section heading says so: *"The experiment that
would pre-register it, and it is `R1-pub-3` slot 2"*. One `J` runs both.

### 5.1 The ladder — the warm column

Load count **held at 8,192** at every footprint. 算 from `t.hit.warm`/`ks0`,
three power cycles, 0.075 % spread:

| footprint | lines × passes | predicted ticks |
|---|---|---:|
| 1 KiB | 64 × 128 | **1,472** |
| 2 KiB | 128 × 64 | **1,472** |
| 4 KiB | 256 × 32 | **1,472** |
| 8 KiB | 512 × 16 | **1,472** |
| 16 KiB | 1024 × 8 | **17,664** |
| 32 KiB | 2048 × 4 | **17,664** |

**Flat, then a step of 12.00×. The knee is the D-cache size.**

### 5.2 The cold column — a control, not a second reading

One pass, every line a compulsory miss, so it must be **linear in the
footprint** at every rung, knee or no knee:

**138 / 276 / 552 / 1,104 / 2,208 / 4,416** — doubling each rung.

🔴 **A cold column that is not linear voids the warm column**, because the walk
is then not walking what this card says.

### 5.3 The A–B–A — five legs, and the specification's own number was wrong

| leg | what it is | predicted |
|---|---|---:|
| `l.aba.0` | KSEG0, 32 passes, warm | **1,472** (= `t.hit.ks0`) |
| `l.aba.w1` | KSEG0, **1 pass**, still warm | **46** |
| `l.aba.1` | KSEG1, 32 passes | **13,698** (= `t.hit.ks1`) |
| `l.aba.c1` | KSEG0, **1 pass**, immediately after | **552** invalidated / **46** not |
| `l.aba.2` | KSEG0, 32 passes, re-warmed | **1,472** either way |

🔴🔴 **The owner file predicted the second KSEG0 leg would read *"cold, ~138
ns/load"* = 17,664 ticks. 算: over 32 passes only the FIRST is cold, so an
invalidating read gives 256 misses + 7,936 hits = 1,978 — a separation of
1.34×, not 8.9×.** A reader comparing a measured 1,978 against *"~138 ns/load"*
would have called it warm and concluded **no invalidation**, the opposite of the
truth. **One pass separates them 12.00×.** Corrected in place in
`docs/rlx-cache-and-cp0.md` before this card existed.

### 5.4 The discriminator, and the two refutations that are NOT the same

| outcome | what it means |
|---|---|
| base 2 identical to base 1 at every footprint | the structure follows the data, not the address ⇒ a **cache**, and the knee is the D-cache size |
| a hit floor at **one** base and not the other | ⇒ a **scratchpad**; the knee is the D-MEM size and § 5.1's headline is **void** |
| neither base shows a floor | the run says nothing and refutes neither |

🔴 **A knee at 8 KiB does not by itself decide it.** `CPU-46`: D-MEM is 8 KiB
and the D-cache is 8 KiB — the same number. What separates them is the second
base, not the knee.

⚠️ **The bases are 320 KiB apart, which is 40× the scratchpad's size AS READ,
not as measured.** If D-MEM were wider than 320 KiB this discriminator is blind
and nothing in it could say so. **Group M's `m.dmembase`/`m.dmemtop`, read on
the same boot, is the independent second answer** — at the loader prompt they
have read `20000000`/`00000000`, and a base with no top above it is not a window
by `docs/probe3-cells.md` block 0's own rule.

### 5.5 🔴 The leaf check, and it comes before any knee is read

* `l.a.w4k` must be **1,472 ± 1**. It is `t-hit`'s KS0 leg to the instruction —
  same base, same 4 KiB, same 32 passes, same five words.
* `l.a.c4k` must be **552 ± 2**, which is `t.hit.warm`.

**If either misses, the LEAF is wrong and no knee may be read off the other ten
rungs.** This is the one cell on the card that can void the rest of its own
section.

### 5.6 Within-boot repeatability, which this project has never had for a timing rung

`l.rep.a8k` and `l.rep.b8k` re-run the 8 KiB warm rung at both bases, each with
its own warming pass. Predicted **equal to `l.a.w8k` / `l.b.w8k`**. Every
previous timing repeat in this project is **across** power cycles, where a
difference has two explanations.

### 5.7 Two tracked files define "slot 2" differently, and this card names which it runs

`docs/isa-prior-art.md`'s seating-schedule row calls slot 2 *"`CPU-45`'s cells
A–G"* — that is **Group C**. `docs/rlx-cache-and-cp0.md` calls it the ladder —
that is **Group L**. 🟢 One payload satisfies both: Group L runs at stage 2b and
Group C unchanged at stage 6 of the same `J`. **This card's § 5 DoD is
`docs/rlx-cache-and-cp0.md`'s.** Group C's rows are scored against
`docs/probe3-cells.md` as they always have been.

---

## 6. `R1-pub-4b` — `D-cost`

### 6.1 The rows, and their twins

| row | twin | why the twin |
|---|---|---|
| `sync` | `nop_a` | one word, no operands, no memory |
| `ll` | `lw` | same load, same registers, same address |
| `sc` | `sw` | same store, same registers, same address |
| `lwu2` | `lw` | **the same word**, base + 2 |
| `nop_a` | `nop_b` | the zero control, and the only control here that can fail |

Every probed word is `tools/isa-payload.tsv`'s and `tools/ucostcheck.py` checks
all of them **in both directions** — 量: 8 cells, 6 matched, 2 exempt by name.
`nop` has no census row and cannot have one, so the exemption is a list by NAME
and the check requires the set that took it to be exactly that list.

### 6.2 🔴 The ruler, corrected before it was used

`jiffies` on this image counts **TC1** — my own clockevent since `R5-3b-2` — and
not TC0's wraps. 量 over twelve committed captures spanning 655 s:
`((tc0cnt>>4) − tc1_cycles) mod 2000` is **716 or 717 in all twelve**.

🟢 **Two results fall out and one is free**: TC0 and TC1 are **phase-locked to
±1 count over 655 s**, which nobody had checked from outside.
🔴 And the offset is **716 counts = 3.58 ms and is not zero**, so a naive
`jiffies × 2000 + (TC0CNT>>4)` is wrong by exactly one reload — 10.0 ms — on
roughly **46 %** of intervals. `ucost` emits **both** composites per rung and
lets the capture's own `mode=` / `ce_live=` decide, because the polarity flips
when `ce_live=0`.

⚠️ `tc0cnt` is printed **raw** and the count is bits 31:4 — it must be shifted
right by 4. The wrap is 2,000 counts and is **not a power of two**, so masking is
wrong.

### 6.3 It is a slope, never a point

Two ladders, because one cannot serve both classes — the costs are expected to
differ by ~1,000×:

* native rows: **16,384 / 65,536 / 262,144 / 1,048,576**
* emulated rows: **4,096 / 16,384 / 65,536 / 262,144**

The emulated ladder's bottom rung is sized for the **native** hypothesis, because
a ladder that only works if the answer is the expected one is not an experiment.
**No fitting happens on the board** — the raw (N, counts) pairs go in the
capture.

### 6.4 The DoD, in clauses that can fail

* **`E1`** every quoted cost comes from ≥ 3 rungs; a row with fewer is *not
  measured*, with the reason, and no number is quoted.
* **`E2`** `|slope(nop_a) − slope(nop_b)|` is printed, and the smallest quoted
  cost must be **≥ 10×** it. **If not, the whole table is void** — not partially
  valid.
* **`E3`** at least one measured row and its twin are read on **two independent
  boots**. Every column-② cell in this project rests on one capture on one boot,
  and a step that repeats that has not noticed it.
* **`E4`** linearity is checked and can fail: largest residual under
  `max(2 counts, 1 % of the largest Δ)`. Outside that the row is **non-linear**,
  its residuals are reported, and its slope is **not** quoted as a cost.
* **`E5`** `Δirq_count == Δjiffies` on every rung, and the two composites agree
  or differ by exactly one reload. More than ¼ of rungs failing voids the
  seating and the finding is about the **ruler**.
* **`E6`** the `ll`/`sc` question is answered in a direction chosen **before the
  capture is read** — see § 6.5.
* **`E7`** the surface is **8** instructions and this prices **4**. The number
  goes in the write-up rather than being discovered by a reader.

### 6.5 🔴🔴 `docs/rlx-isa.md` § 8.2 predicts ONE costed row, and this card does not edit it

That file, dated before this one, registers that *`D-cost` will find exactly one
row with a measurable cost*. **It is left exactly as written.** If `ll` and `sc`
cost anything, that prediction is **refuted** and the refutation is this seating's
result. If they do not, *"emulated in user mode"* is refuted as a statement about
the **executing machine**, the source reading is re-attributed, and § 8.2 is
**confirmed**. **Both outcomes are results and both are written here, before
power.**

A document written before its measurement is the rarest thing this repository
has. Editing it now to agree with what the instrument is about to say would
spend that for nothing.

### 6.6 🔴 `lwu2` — the cell two of this repository's own files disagree about

Same `lw` word as its twin; the only difference is **two added to a base
register, outside the loop**.

* `SPEC.md` `CPU-15`, 量 on this die at the loader prompt: **all four unaligned
  load/store instructions execute and compute the right answer** — the reading
  that refuted the public record of the Lexra settlement. ⇒ the kernel's
  unaligned handler never fires and **`lwu2` costs what `lw` costs**: a slope
  difference at the zero control.
* `docs/emulation-surface.md` lists **five unaligned forms among the eight
  entries on the emulation surface**. ⇒ `lwu2` costs an exception round trip —
  the most expensive emulation on this kernel and the only one ordinary programs
  hit.

**Those are different numbers and this cell reads one of them.** Neither
document is edited to agree with the other before the board answers.

⚠️ The census excludes the unaligned forms by rule, which is why `4a` could not
reach this; `ucost` writes its own `.word`s and can.

### 6.7 ⚠️ What `hazlint` does not say here

Its load set is MIPS-I and `ll` is opcode `0x30`, so **a green gate is not
evidence about the `ll` cell**. Recorded, not waived. The gate is green: **0
violations in 642 loads**.

---

## 7. The `4a` repeat, and why `BUILD_ID` had to stay still

`R1-pub-4a` has **one bench, one boot, and no row has ever been repeated**.
Seating 24 re-runs it.

🔴 **That is why `tools/isa-payload.tsv`'s `special0e` `why` column still says
`C2` where the documentation says `C5`.** 量: `cat uprobe.c cells4.S
probe4rows.h rlxasm.h | sha256sum` is `a87be346bb83e7f9`, which is the
`BUILD_ID` seating 23's capture printed. Correcting that column regenerates
`cells4.S` and moves the digest — and then the repeat is of a **different
artefact**.

**The fix is deferred a fourth time, and this time with an expiry rather than a
wish: the first rebuild AFTER this repeat lands.** `ucost` was deliberately
built as a separate product with its own `UCOST_BUILD_ID` over its own two files
so that it could not touch those four.

⚠️ The recorded positive control for that digest — *adding one comment line
gives `4ac4cd1f6c0b61ed`* — **does not reproduce**, because the comment's text
was never written down. The mechanism is sound; that constant is not
reproducible by anyone and should not be quoted again.

---

## 8. `map 0`

First Linux cell. 🔴 **It does not close `FLS-26`'s attribution bracket — that
closed at seating 18.** What it buys is a bracket over **seating 23**, which ran
zero `map`. Free, and it is the right first cell either way.

⚠️ `map_jiffies` varies by a tick, so a whole-file `cmp` is wrong; compare the
unit digests.

---

## 9. What this block does NOT claim

1. It does not measure the D-MEM window's location. That is `w-imem` and
   `w-imem` is **未定**.
2. It does not price the five unaligned forms as a class — it prices **one**.
3. `E2`'s zero control bounds the instrument's noise; it does not bound I-cache
   **index** conflict between a cell's body and the exception handler's own
   lines. `.align 4` removes line straddle and not that. **No control here
   catches it.** The experiment that would — four forced offsets per cell, slope
   must be flat — is named and not run.
4. It does not claim `ll`/`sc` are emulated. That is what § 6.5 is for.
5. **No flash.**

---

## 10. The cells

`H` = host, `L` = at the loader prompt, `S` = at the Linux shell.

```
#-- the ESC window.  THE OPERATOR PRESSES POWER INSIDE THIS WINDOW.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-A --esc 150 --esc-period 0.002 --seconds 165
#-- the positive control on the adapter path: 0 bytes with the board off, the help text now.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-Q --send '?' --idle 3 --seconds 12
#-- NEGATIVE CONTROL ON THE WRITE: the block must NOT already hold this run's values.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-P3pre --send 'DW 80A02000 4' --idle 2 --seconds 8
#-- word 1 must be 00000000 or NOTHING IS UPLOADED.  An echo is not the burn flag.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-P3bf --send 'DW 8040D4A0 1' --idle 2 --seconds 8
#-- the eight words must be probe3.bin's own head or DO NOT JUMP.  first word 3c1d8051.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-P3sh --send 'DW 80500000 8' --idle 2 --seconds 8
#-- the run.  Group L then the rest, then the payload's own bite, then the prompt.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-P3j --send 'J 80500000' --esc-after 60 --esc-period 0.002 --until '<RealTek>' --seconds 120
#-- the second channel.  762 = RB_POISON_W, not the 754 make show prints.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C1-P3rb --send 'DW 80A02000 762' --idle 3 --seconds 40
```

The rescue and the upload are **not captures** and are therefore **not in the
fence**, so `N of N` still means the whole seating:

```
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-16/C1-P3-rescue.json
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe3/probe3.bin --filename probe3 --rescue-report bench/2026-09-16/C1-P3-rescue.json --expect-load 80500000 --yes
```

Then the Linux half:

| # | where | command |
|---|---|---|
| `LOOP` | H | `looprun.py --mode bench --cell uc1 --skip S2,S3 --image <nfjrom> --image-sha256 d6615575… --cell-top <cells/uc1/top> --label uc1-20260916 --work <bench-only/uc1-work-20260916> --recipe-override efa93621 --out-dir bench/2026-09-16` |
| `C2-M0` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C2-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180` |
| `C2-UC` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C2-UC --send '/bin/ucost a91' --seconds 240` |
| `C2-UP` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C2-UP --send '/bin/uprobe a91' --seconds 45` |
| `C2-UC2` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-16/C2-UC2 --send '/bin/ucost b17' --seconds 240` |

🔴 **`C2-UC2` is on the SECOND boot, not the second run of the first boot.**
`E3` asks for two independent boots and a second invocation inside one boot is
not that. `busybox reboot -f` between them; it does reset this board and it
costs 2.407 s.

⚠️ **No `--idle` on the `ucost` cells.** `--idle N` is N seconds since the last
byte, and a ladder rung at 1,048,576 iterations can be silent for longer than
any plausible `--idle`; five cells of seating 20's card would have stopped 11–21
seconds before their own output for exactly this reason. `--seconds` only.

### 10.1 The numbers this card states, and where each is re-derived FROM

```cardnum
probe3-bytes	33616	size tools/rlxprobe/build/probe3/probe3.bin
probe3-sha16	c2069e250794ee7f	sha256-16 tools/rlxprobe/build/probe3/probe3.bin
probe3-head	3C1D8051	word32 tools/rlxprobe/build/probe3/probe3.bin 0
ucost-bytes	16692	size build/rlxfw-user/isaprobe/ucost
ucost-sha16	76c7e23180214849	sha256-16 build/rlxfw-user/isaprobe/ucost
dw762-bytes	9003	dwreply 762
cells-fence	11	count bench/2026-09-16/PREDICTIONS-B23-block22.md ^bench/2026-09-16/C[12]-[A-Za-z0-9]+$
send-over-127	0	count bench/2026-09-16/PREDICTIONS-B23-block22.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-16/PREDICTIONS-B23-block22.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
no-flr	0	count bench/2026-09-16/PREDICTIONS-B23-block22.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-16/PREDICTIONS-B23-block22.md -{2}send '[^']*(EW |EB |FLW )
no-autoexec	0	count bench/2026-09-16/PREDICTIONS-B23-block22.md ^/usr/bin/python3 .*(allow-autoexec|boot[.]img)
```

---

## 11. The fence

```cells
bench/2026-09-16/C1-A
bench/2026-09-16/C1-Q
bench/2026-09-16/C1-P3pre
bench/2026-09-16/C1-P3bf
bench/2026-09-16/C1-P3sh
bench/2026-09-16/C1-P3j
bench/2026-09-16/C1-P3rb
bench/2026-09-16/C2-M0
bench/2026-09-16/C2-UC
bench/2026-09-16/C2-UP
bench/2026-09-16/C2-UC2
```

---

## 12. The drop order, if the window closes

1. `C2-UC2` — `E3`'s second boot. The cost table then rests on one boot and
   **says so**, which is what `4a` did and what `E3` exists to stop repeating.
2. `C2-UP` — the `4a` repeat. Cheapest to re-take on any later seating, because
   `BUILD_ID` is frozen for exactly that purpose.
3. `C2-M0` — the seating-23 bracket. Free, but it buys the least.

🔴 **Nothing in § 5 may be dropped.** `R1-pub-3`'s stop-loss allows **two
seatings** and slot 1 spent one. This is the second.
