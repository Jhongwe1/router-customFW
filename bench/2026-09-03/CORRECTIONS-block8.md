# CORRECTIONS — block 8, `R5-2`, seating 11

**Written after the seating, 2026-09-03 evening into 2026-09-04.**
`PREDICTIONS-B9-block8.md` is frozen and was not edited. Everything below is a
correction to it, or a deviation from it, recorded here because that is the only
place a correction may go once a capture has landed.

The seating: **one power cycle**, 21:15 → 21:55 on 2026-09-03. Zero `FLR`, zero
`EW`/`EB`/`FLW`, zero burn, zero upload beyond `S6`'s TFTP into RAM. The flash
bracket is untouched and stands at **1,024 of 4,194,304 = 0.0244 %**.

---

## 1. 🔴 The correction that mattered, and it was caught between two cells rather than after the block

**`TM-1` refuted `Q2`, and two of the five registers it refuted are the two that
set the timer's rate.** The card's § 4.2 arithmetic is built on one of them.

| register | loader prompt (`SPEC.md` `REG-05`/`REG-11`) | **under Linux, `TM-1`** |
|---|---|---|
| `CDBR` | `0x000E0000` — divisor **14** | 🔴 **`0x03E80000` — divisor 1000** |
| `TC0DATA` | `0x0022E0A0` = **142,858** ≪ 4 | 🔴 **`0x00007D00` = 2,000 ≪ 4** |
| `TCCNR` | `0xC0000000` | ✓ same |
| `TCIR` | `0x80000000` | ✓ same |
| `TC1DATA` | `0x00000000` | ✓ same |

Both combinations produce exactly 100 Hz:

```
loader :  200.0049 MHz / 14   = 14,286,057 Hz ;  14,286,057 / 142,858 = 100.0 Hz
Linux  :  200.0049 MHz / 1000 =    200,005 Hz ;     200,005 /   2,000 = 100.0 Hz
```

**So the vendor's `arch/rlx/kernel/rlx-time.c` reprograms the divider at boot**,
and `Q2` bought exactly what it was written to buy — a finding about a file this
project has still never opened. `cdbr_at_init` and `tc0data_at_init` both already
read the Linux values, so the change happened before `rtl819x_timer_init` ran and
is the vendor's, not this driver's.

### 1.1 What it broke, before it was used

§ 4.2 writes the reference counter as

```
ΔTC0_total = Δjiffies × 142858 + ((tc0cnt_j >> 4) − (tc0cnt_i >> 4))
```

**142,858 is the loader's reload.** Under Linux the constant is **2,000**. Using
the card's number would have made `ΔTC1 / ΔTC0_total ≈ 0.0140` and "refuted"
`Q6` by a factor of 71.4 — as a pure artefact of the reader's own arithmetic,
with the hardware innocent.

🟢 **The correction was applied before `TM-6` ran, not after**, because the block
was executed as three runs (`TM-1`–`TM-2b`; `TM-3`–`TM-4b`; `TM-5`–`TM-8`) with
the card's two decision points as the split. The analyser now reads the reload
out of each dump's own `tc0data` field instead of carrying a constant.

### 1.2 What else the same factor moved

`CLK-22`'s period is derived from the 14.29 MHz rate, so **everything the card
says about TC1's timescale is off by 71.43×**:

| quantity | card | corrected |
|---|---:|---:|
| one TC1 period (2²⁷ counts) | 9.395016 s | **671.07 s** |
| `tc1_ext_trusted` threshold (MASK≫1) | 4.697508 s | **335.53 s** |
| `arm_delta_100us` derived value | 1,428.6 | **20.0** |
| one `tc0cnt` count over 60 s | 0.0012 ppm | **0.083 ppm** |

The last row is the only one that could have hurt `Q6`, and it does not:
0.083 ppm is still 2,000× finer than `Q6`'s ±50 ppm tolerance and 2,008× finer
than the 166.7 ppm jiffies grid § 0.2 set out to remove.

---

## 2. Cell-by-cell, against the card's own table

| id | card | outcome | note |
|---|---|---|---|
| `Q1` | 37 lines, `gimr_tc1ie=0` | 🟢 **HOLDS** | 37 lines exactly; `proc-lines` re-derived from source as 37 `scnprintf`, all in `rtl819x_tc_read_proc` |
| `Q2` | five registers equal `REG-05`…`REG-11` | 🔴 **REFUTED** | § 1 above. The most informative outcome the card allowed for |
| `Q3` | `tc0cnt & 0x0F == 0`, `tc0cnt >> 4 < 0x22E0A` | 🟢 **HOLDS**, and upgraded | Low nibble zero in all eight dumps. The bound is now `tc0data >> 4 = 2,000` rather than the card's `0x22E0A`; every reading is under it. `Q6` then proves the shift **to the count** |
| `Q4` | `TM-2a`/`TM-2b` both `jiffies` | 🟢 **HOLDS** | § 1 of the card — the desk clocksource census — confirmed on the silicon |
| `Q5` | `trusted=1` and FALSE, gap ≈ 25,928,526 | 🔴 **refuted as written** / 🟢 **mechanism CONFIRMED** | § 3 below |
| `Q6` | `ΔTC1 / ΔTC0_total` = 1 ± 50 ppm | 🟢🟢 **HOLDS at 0.000 ppm**, three intervals, integer-exact | § 4 |
| `Q7` | two intervals agree within 20 ppm | 🟢 **HOLDS** (0.000 vs 0.000) | |
| `Q8` | no step of one lost tick | 🟢 **HOLDS to the count** | residual exactly 0 in all three intervals |
| `Q9` | `arm_delta_100us` in 1350…1500 | 🔴 **refuted** (20, 21) | declared *猜, refuted by nothing*, so it cost nothing — and it independently confirms § 1 |
| `Q10` | `TM-5` finds `tcir_tc1ip=1` | 🔴 **ANSWERED, negative** | § 5 — but not by `TM-5`, which was void |
| `Q11` | `TM-7` reads `tcir_tc1ip=0` | 🔴 **VOID**, by the card's own clause | a bit that never latched cannot be shown to clear |

### 2.1 `Q9` is refuted and the refutation is a confirmation

```
card's derived value:  14,286,057 Hz × 100 µs  = 1,428.6 counts
measured             : 21 (TM-3), 20 (TM-5b-arm)
21 counts / 200,005 Hz                         = 105.0 µs
```

**The card's model of how long the arm takes was right to within 5 %; only its
clock constant was wrong.** `1428.6 / 21 = 68.0` against the clock ratio 71.43,
and the residual is the arm genuinely taking 105 µs rather than 100. Two
independent quantities — a register field and an elapsed-time count — now say
the same thing about the divider.

---

## 3. 🟢 `Q5`'s mechanism is confirmed, at the timescale the corrected rate implies — and a SECOND defect was found that § 0.1 did not identify

§ 0.1 predicted `tc1_ext_trusted` would report `1` on data that had lost whole
wraps, because `rtl819x_ext_advance()` computes `d = (now − last) & MASK`. The
card put the failure at a 30 s sampling gap. **At 200 kHz a 30 s gap is 6.0 M
counts — well inside one 134.2 M period — so no aliasing occurred at 30 s and
`Q5` as written is refuted.**

🔴 **It occurred at 703 s instead, and the reading is decisive.** `TM-5b-arm` →
`TM-5b2`:

```
true elapsed  = 2^27 + 6,477,665 − 1,861 = 140,693,532 counts
tc1_ext_gap_max                          =   6,475,672  = 140,693,532 mod 2^27
tc1_ext_trusted                          =           1
lost                                     = 134,217,728 counts — exactly one period
```

**Same mechanism, same failure, threshold off by the same 71.43×.** `TMR-1`
stands and is now 量 on the device rather than derived at the desk.

### 3.1 🔴 The second defect, which is not aliasing and is arguably worse

`TM-5c`, after 462 s in which nothing read `/proc`:

```
tc1_cycles = 98,840,142        tc1_ext = 6,477,776        deficit = 92,362,366
tc1_ext_gap_max = 6,475,672 — unchanged, so no advance computed a large d
tc1_ext_trusted = 1
```

讀, `rtl819x-timer.c:476-477` — the **only** call site of `rtl819x_ext_advance()`:

```c
if (rtl819x_tc1_armed)
        rtl819x_ext_advance(cyc);
```

It is inside `rtl819x_tc_read_proc`. **So `tc1_ext` is a sum over the intervals
somebody happened to read `/proc` in, not an extension of the counter.** With no
reader it silently stops, and `tc1_ext_trusted` — which is only
`reads > 0 && gap < (MASK >> 1)` — still reports `1`.

**A clocksource's software extension must be advanced by something guaranteed to
run at least once per period**, which is what a `clocksource`'s own `.read()`
under an active timekeeping loop, or a periodic timer, provides. `R5-3` owns
both fixes; § 0.1 identified one of them.

---

## 4. 🟢 `Q6`, the cell the block exists for: three intervals, residual exactly zero

```
interval        Δjiffies   ΔTC0_total     ΔTC1          residual   ratio
TM-6 d1→d2        3,003     6,007,208     6,007,208         0      1.000000000
TM-6 d2→d3        3,004     6,007,994     6,007,994         0      1.000000000
TM-5b-arm→5b2    70,346   140,693,532   140,693,532         0      1.000000000
```

The third interval was not on the card. It is **703.46 s — 23× the card's — and
it crosses one 27-bit wrap**, so § 4.2's `n_wraps` recovery is exercised and
correct (`n_wraps = 1`) rather than merely asserted at `n_wraps = 0`.

An integer-exact match of two hardware counters read under one
`spin_lock_irqsave` establishes, in one reading: TC1 and TC0 are driven by the
same divided clock; `tc0cnt` is value-in-bits-31:4; `tc0data ≫ 4` is the reload;
and the vendor's tick loses no jiffies (`Q8`).

⚠️ **It is a RATIO and not a frequency, and the card's § 7 ② is therefore still
true in a way worth restating.** `Δwall` comes from `jiffies`, `jiffies` comes
from TC0, TC0 shares the divider with TC1. What is measured is *TC1 advances
exactly 2,000 counts per jiffy*. **The absolute 200.005 kHz remains 推**, from
`CLK-02 ÷ 1000`.

### 4.1 🔴 § 4.2's host-clock cross-check failed, and the card's own control is what says so

§ 4.2's last paragraph maps each dump's first byte to the last `.timing` row at
or before that offset. Offsets landed exactly on read boundaries (102 / 778 /
1454, each dump 676 bytes), so the mapping itself is clean. The result is not:

```
interval 1   dt_host = 29.714630 s   →  f_TC1 = 202,163.3 Hz  → base 202.163 MHz
interval 2   dt_host = 29.995845 s   →  f_TC1 = 200,294.2 Hz  → base 200.294 MHz
```

**Two nominally identical `sleep 30` intervals disagree by 9,332 ppm**, which is
**17× the cross-check's own stated resolution floor** (one 16 ms latency-timer
tick over 30 s = 538 ppm). The board's two intervals, by contrast, agree to one
jiffy and its two counters to zero counts.

🟢 § 4.2 says *"the two intervals are what show it"*. They did — **and what they
showed is jitter on the HOST side.** The honest output is a bound, not a
measurement: base clock somewhere in ~200.3–202.2 MHz by this route, which
`CLK-02`'s ±7 ppm beats by three orders of magnitude.

**This is a third committed reader of `.timing` producing a number that does not
reconcile**, after `looptime.to_prompt` and `boot-timeline.py`. It goes to
`TOOL-1`.

---

## 5. 🔴 `Q10` is answered and the answer is negative — and it changes `R5-3`

The card's `TM-5` could not answer it: `sleep 10` is **1.5 % of a period** at the
corrected rate, so `tcir_tc1ip=0` there means nothing. Across the entire original
block TC1 never exceeded 31,992,325 of 134,217,728 counts — **23.8 % of one
period, never a wrap.**

**`TM-5b`/`TM-5b2` satisfied the card's own stated precondition** — *"≥ one TC1
period must elapse"* — which `sleep 10` never did. That is completing a cell
whose precondition the card mis-computed, not adding one.

```
armed at   wall = 1010.48   tc1_cycles =     1,861
read at    wall = 1713.94   tc1_cycles = 6,477,665      ← the POSITIVE CONTROL
Δ = 703.46 s = 140,693,532 counts = one wrap plus 6.48 M
tcir_tc1ip = 0      gisr_tc1ip = 0      gimr_tc1ie = 0 throughout
```

🟢 **`tc1_cycles` reading 6.48 M — far below its own previous 31.99 M and far
below 2²⁷ — is what proves the period elapsed.** That control is exactly what the
original `TM-5` lacked, and its absence is why `Q10` was void rather than
answered the first time.

**Finding: `TC1IP` does not latch in `TCIR` while `TC1IE` is clear in `GIMR` on
this die.**

🔴 **The consequence is larger than the reading.** `notes/timer-driver.md` § 4
builds the driver's whole safety argument on observing the pending bit with the
interrupt masked. **That strategy does not work on this part.** `R5-3` cannot
watch the latch first and arm the interrupt second; it must set `GIMR.TC1IE`
with a handler already installed, and there is no intermediate step. This is the
single most valuable thing block 8 produced for the next step, and the card did
not anticipate it.

`Q11` is void by the card's own clause. It is **the only test this project has**
of the D Table 25 write-1-to-clear claim, and it remains untaken — now for a
measured reason rather than an unmet precondition.

⚠️ **What that sentence is not claiming, checked by `git grep` before it was
written.** This repository holds a *second* write-1-to-clear claim, and it is
about a different register: `WDTCNR`'s `WatchDogIND` at bit 20, D § 8.2.9
Table 27 (`SPEC.md` `CLK-10`, `RUNSHEET` § 518, and two 2026-08-24 prediction
blocks). That one is 推 as well and is equally untested — writing `0` to it is
a no-op *if* the bit is write-1-to-clear, which is the same unverified premise
one register along. **The claim above is scoped to `TCIR`'s `IP` bits**, and it
is written with the table named for exactly this reason.

---

## 6. 🔴 The card's "free ordering check" does not have the power the card claims

The card, § 4: *"`arm` zeroes the counter and only `rtl819x_tc_read_proc`
advances it … So `TM-3` prints 1, `TM-5` prints 2, and `TM-6`'s three dumps print
3, 4, 5. A different number means a `/proc` read happened that this card did not
issue."*

量, the printed sequence across eight dumps:

```
TM-3  1      TM-5  3      TM-6  5, 7, 9      TM-7  11
TM-5b-arm 1  TM-5b2 3     TM-5c 4
```

**`+2` per `cat`, not `+1`.** 讀, `rtl819x-timer.c:487` — `reads` is snapshotted
*after* the advance, and a 2.6 `read_proc` file is read **twice** by `cat` (the
second call returns 0 to signal EOF). So the counter counts *kernel calls*, not
user reads.

🔴 **And it is not even a constant.** Modelling `cat` as exactly two calls
reproduces every cell except `TM-7`, which is **one higher than the model**
(11 where 10 is predicted); `TM-5c`, the other `disarm ; cat`, matches the model
exactly at 4. So one extra `read_proc` call occurred, while armed, between
`TM-6`'s third dump and `TM-7`'s disarm. **Cause undetermined**, and it is
written down rather than explained away.

**So the card's inference is false as stated**: a different number can also mean
`cat` made a different number of kernel calls. The check found something real —
it is just not the thing the card said it would find. `arm` zeroing the counters
is confirmed (讀 `:385-388`; 量, `TM-5b-arm` reads 1 after a run that reached 11).

---

## 7. Deviations from the card, each with its reason

| # | deviation | why |
|---|---|---|
| **D1** | `SEAM-1` ran `--skip S2,S3 --recipe-override 229d2983 --image <the pinned file>`, **not** the unskipped `--mode bench` its carried-forward row decided on | 🔴 `RECIPE_ID` is a digest over `config/` **only** (讀, `rlxfw-kbuild.sh:203-204`); `--config`, `--initramfs`, `--cflags-kernel`, `--oldconfig` and `--id-scope` are outside it. So the board printing `229D2983` cannot distinguish the pinned image from a differently-configured sibling — and `notes/timer-driver.md` § 6 records `r51a` and `r51quiet` as exactly that pair, same day, same frozen `config/`. The pinned image's own `--config`/`--initramfs` argv is not recoverable from the record. 🟢 With `--image` on the pinned file, `S6b`'s `assert_staged` became the discriminator the id is not: **8 words read back from `0x80500000`, every one derived from that file**, covering the card's own `img-word-18`/`img-word-1C` (`3C108060`/`2610B800`), which the contrast value `2610AC00` would have failed |
| **D2** | `looprun --cell SM`, not `TM` | looprun's `S6b` writes `<out-dir>/<cell>-2a`, and **`TM-2a` is one of the card's ten cells**. `--cell TM` would have overwritten `E3`'s sysfs read. Caught before power |
| **D3** | four captures beyond the card's ten: `TM-5b-arm`, `TM-5b` (void), `TM-5b2`, `TM-5c`, `TM-5d` | § 5 — satisfying `TM-5`'s own stated precondition. No re-arm followed a wedge; there was no wedge |
| **D4** | `TM-5b` is committed with **no `.meta.json`** | § 8 — it is the record of the CP2102 drop, and negative results stay in place |

---

## 8. 🔴 The CP2102 dropped mid-capture, and `C-19`'s signature was complete

At ~21:36, inside `TM-5b`'s 720 s window:

* `TM-5b.log` — **37 bytes**, `od -c` shows exactly
  `sleep 700 ; cat /proc/rtl819x-timer\r\n`, the echo and nothing of the board's
* **no `TM-5b.meta.json`** — the process never reached its own footer
* `/dev/ttyUSB0` mtime moved **20:56 → 21:36** — the node was re-created, so the
  device re-enumerated
* `usbipd list` read `1-1 … Attached` afterwards

🟢 **It did not cost the reading, and the reason is worth writing down.** The
board does not participate in USB: it was still executing `sleep 700 ; cat`, and
`TCIR`'s `TC1IP` is a sticky latch, so the answer was waiting rather than
passing. The recovery was to kill the stale capture, open a capture that **sends
nothing**, and receive the board's own output when the sleep completed at
21:47:4x. `TM-5b2` is therefore the card's own cell arriving late, not a
substitute for it — it ran the command the card wrote.

**Cost: 0 power cycles, ~11 minutes of board time.** `C-19` remains
undetermined as to root cause; this instance adds one more occurrence and no new
discrimination among its three candidates.

---

## 9. What block 8 did not establish

1. **No absolute frequency.** § 4.1 — the only non-board time base available
   disagreed with itself by 17× its own floor.
2. **`Q11` untaken.** The single-source write-1-to-clear claim is still a single
   source, now for a measured reason.
3. **The interrupt was never delivered.** `GIMR` was read and never written, in
   all ten dumps (`gimr=00209100`, `gimr_tc1ie=0`). `R5-3` owns it.
4. **`arch/rlx/kernel/rlx-time.c` is still unopened**, and `Q2` is the closest
   this project has come to reading it without reading it — closer than the card
   expected, because the answer turned out to be a change rather than a match.
5. **One `read_proc` call is unexplained** (§ 6).
6. **`CPU-45` did not run**, and it was not a scheduling choice: no probe3
   payload has been staged since `bench-only/b6-20260831c` (2026-08-31),
   `probe3.c`'s Group V is still the `c-A`-armed version that returned negative
   on 2026-08-29, and the residual needs a variant that makes a line resident.
   No such payload exists and no card was frozen for it.
