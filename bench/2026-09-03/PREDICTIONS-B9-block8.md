# PREDICTIONS — Session B9, `R5-2`, block 8: the two-clocksource reading, and the two defects the desk found in this block's own design before power

**Written at the desk on 2026-09-03, twenty-ninth segment, before power.** Every
number below was re-derived on this host today from a file already committed or
an image already staged. Nothing here is conditional on a reading taken at the
bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in
`CORRECTIONS-block8.md`, beside this one.

⚠️ **The directory name is a prediction and the seating date is not known.**
This block is written on 2026-09-03 and lives in `bench/2026-09-03/`. If the
seating lands on another day the directory is renamed **before power** and the
rename is recorded as a deviation — that is seating 8's Deviation 1, walked once
already, and the cost is known. The alternative considered and rejected was a
date-free directory: `bench/README.md`, `tools/boot-timeline.py` and
`tools/test-boot-timeline.sh` `B2` all read the one-directory-per-power-cycle,
named-for-the-date population, and moving off it to save a rename would move
three readers of that population.

🔴 **This block runs LAST on its seating, and that is the whole safety
argument.** See § 2.

🔴 **This block issues no `FLR`, no `EW`, no `EB`, no `FLW`, no burn and no
upload.** It adds **zero** bytes to the flash bracket's coverage, which stands
at 1,024 of 4,194,304 = **0.0244 %**, and *not one flash byte is written* is
exactly as unsayable after this seating as before it. Said here so that a block
with no bracket is a recorded decision rather than an omission. It follows that
**the `FLR` pre-read containment rule is not inherited by this card**: there is
no `FLR` row to attach it to. The rule itself is `PROGRESS.md`'s closed row plus
its stated residual — *the enforcement only reaches a card that goes through
`flrbracket run`* — and as of today `tools/cardcheck.py` `A19`–`A21` and `B10`
enforce that residual instead of a sentence doing it: an `FLR` typed through
`--send` is reported, the two frozen cards that do so are named one by one, and
`B10` checks that list in **both** directions so it cannot grow into a blanket.

**One power cycle, and it is not this block's** — the seating's, shared with
`SEAM-1`, `GR-1` and whatever `CPU-45` work it carries. Cells are `TM-*`, a stem
no directory under `bench/` uses.

---

## 0. 🔴 This block CORRECTS `notes/timer-driver.md` § 5, twice, and both corrections came out of re-deriving that section's own arithmetic

Neither correction needed a new source. Both are the note's own constants put
back through the note's own model, which is what writing a card is for.

### 0.1 `tc1_ext` cannot be quoted at this block's sampling interval — **and the driver's own trust flag says the opposite**

`rtl819x_ext_advance()` computes `d = (now − last) & MASK` with `MASK = 2²⁷−1`,
so it recovers the true gap only while that gap is under one period. The period
is **134,217,728 counts = 9.395016 s** (量, `CLK-17`). `tc1_ext_trusted` is
`reads > 0 && gap < (MASK >> 1)`, i.e. gap < **67,108,863 counts = 4.697508 s**.

量 today, by putting this block's own sampling interval through that expression:

| gap | true counts | wraps | the `d` the driver computes | `tc1_ext_trusted` |
|---:|---:|---:|---:|---:|
| 4.0 s | 57,144,228 | 0 | 57,144,228 | 1 — correct |
| **9.0 s** | 128,574,513 | 0 | 128,574,513 | **0** — correct refusal |
| **30.0 s** | 428,581,710 | **3** | **25,928,526** | 🔴 **1 — FALSE** |
| **60.0 s** | 857,163,420 | **6** | **51,857,052** | 🔴 **1 — FALSE** |

🔴 **The flag is not merely unhelpful past one period; it aliases back into the
trusted band and reports trusted on data that has silently lost whole wraps.**
A 60 s pair would have given `tc1_ext_trusted=1` and a frequency 16.5× too low,
and § 5.2's `E7` predicted **both** of those as success indicators
(*"`tc1_ext_trusted=1`; `tc1_ext_gap_max` a few million counts for a sub-second
turnaround"*) — two sentences that cannot both be true of the same 60-second
cell.

**What this block does instead**: `tc1_ext` is **not quoted**. `tc1_cycles` —
the raw 27-bit value — is quoted, and the wrap count is recovered **outside the
kernel** from `jiffies`, which is exact. § 4.2 has the arithmetic. § 5.4's
existing stop-if already sanctions this route; what is new is that it is the
**planned** route rather than the fallback.

**And the false `1` is itself a prediction of this block** (`Q5`), so the defect
is confirmed on the silicon rather than only on paper. The fix — refuse when
`Δjiffies × TICK_NSEC` implies more than one period — is `R5-3`'s, because
`config/` is frozen for this image (§ 3).

### 0.2 The kernel's clock is on a 10 ms grid, so **+17.99 ppm is not resolvable against `Δwall`** — and `tc0cnt` is what removes the grid

`CONFIG_GENERIC_TIME=y` and `CONFIG_HZ=100` (讀, both out of the `.config` the
staged image was built from). `getnstimeofday()` returns `xtime` plus
`timekeeping_get_ns()`, and with `clocksource_jiffies` selected the second term
changes only when `jiffies` does. **So `wall` advances in 10 ms steps**, whatever
its nine printed decimal places suggest.

量, the endpoint error a 10 ms grid puts on a ratio:

| span | 10 ms as ppm | vs the +17.99 ppm signal |
|---:|---:|---|
| 30 s | 333.3 | 19× the signal |
| **60 s** | **166.7** | 🔴 **9× the signal** |
| 600 s | 16.7 | comparable |
| 1800 s | 5.6 | 3× the signal |

🔴 **So § 5.2's `E8` — a 60 s pair compared against `Δwall` — could not have
resolved its own headline prediction**, and § 5.3's three branches are not three
outcomes of one cell: *≈0*, *+18* and *lost ticks* need different baselines.
§ 5.3's own second bullet is right and is the one that survives at 60 s: one
lost tick **is** 167 ppm, and 167 ppm is exactly the grid, so a 60 s pair is a
**one-lost-tick detector at the edge of its resolution** and is not an 18 ppm
measurement.

🟢 **The grid is removable, and the thing that removes it was already being
printed.** `TC0CNT` is the tick's own phase. Define

```
TC0_total = jiffies × 142858 + (tc0cnt >> 4)
```

and the kernel's time base becomes a **continuous 14.29 MHz counter** instead of
a 100 Hz one. One count is **0.0012 ppm over 60 s**. Every comparison this block
makes is against `TC0_total`, and the +17.99 ppm then falls out of two measured
constants rather than being chased with a stopwatch.

⚠️ **`>> 4` is the driver's assumption about `TC0CNT`, not the datasheet's**, and
this block tests it — see `E1`'s third prediction. `rtl819x_tc1_cycles()` shifts
`TC1CNT` right by `RTL819X_TC_VALUE_SHIFT = 4`; the `/proc` dump prints `tc0cnt`
**raw**, unshifted, so the reader does the shift and can see whether it was the
right one.

---

## 1. 🟢 What `E8`'s most valuable branch was going to discover, discovered at the desk instead — and its cost is stated

§ 5.3 calls `E8` reading **≈0 ppm** *"the single most valuable byproduct of the
cell"*: it would mean the vendor registered a real clocksource, learned without
reading the vendor's source.

量 2026-09-03, at the desk, on the `vmlinux` this block's image was cut from —
**exactly two `struct clocksource`s exist in it, and neither is the vendor's**:

| route | what was counted | result |
|---|---|---|
| direct transfers to `clocksource_register` (`T` @ `80035700`) | the `jal` and the `j` encodings of that target, over the single `PT_LOAD` | **2**: `j` from `init_jiffies_clocksource+0x4` (a tail call) and `jal` from `rtl819x_tc_write_proc+0x27c` (mine) |
| indirect reachability | `lui`/`addiu` and `lui`/`ori` pairs materialising `clocksource_register`'s address | **0** — nothing can `jalr` to it |
| a module registering one later | `.config` | `# CONFIG_MODULES is not set` |

**Controls, because a scan reporting a number is making a claim.** The first
version of this scan counted `jal` only and found **1**, with its designed
positive control — `init_jiffies_clocksource`, generic Linux, which provably
calls `clocksource_register` — **not firing**, while `panic` (45) and `schedule`
(72) did. 🔴 **The control failing is what found the cause**: `return
clocksource_register(&clocksource_jiffies);` is a tail call and gcc emits `j`,
not `jal`. For the indirect scan the first three positive controls (`panic`,
`do_timer`, `clocksource_get_next`) all read 0 — **their addresses are simply
never taken**, so that scan could not fail either; replaced with
`rtl819x_tc_read_proc` (2), `rtl819x_tc_write_proc` (1) and
`rtl819x_tc1_clocksource` (3), which must fire by construction because
`rtl819x_timer_init` stores them into a `proc_dir_entry` at run time. Negative
controls — an address two bytes off a real one, and an address four bytes into a
function — both **0**.

**What this costs, stated rather than left for a reader to notice**:

* `E8`'s **≈ 0 ppm** branch is **excluded before power**. That is a real loss of
  bench value and it is not recoverable.
* It is a **reading of the vendor's compiled code**, and it goes in
  `docs/blind-write-ledger.md` § 4.3 as one. 🟢 **What limits the damage is the
  order**: `R5-1`'s driver was written, built, linked and pinned into
  `rlxfw-r51-20260903.bin` on 2026-09-03 **before** this scan ran, so nothing in
  the driver can have been shaped by it. The ledger row records that.
* It is an **absence** on the decision layer — *the vendor registers no
  clocksource* — obtained without opening `arch/rlx/kernel/rlx-time.c`, which
  still has **zero** citations in this repository.

🟢 **What it buys**: `E8` stops being a three-way branch and becomes a
prediction with a refutation. If `E8` now reads ≈ 0, it refutes **this desk
scan**, not the vendor's silence — and the card says where to look (`E5`'s
`current_clocksource` would name whatever won).

---

## 2. Where this block sits on the seating, and why LAST converts its worst case to zero

The arm's worst case is not a brick and not a flash byte: it is the board
wedging **after** a shell has already been reached, which costs *the remainder of
the seating*. That quantity is under the card's control.

    …  SEAM-1        --mode bench with no --skip S2,S3     (decided, R5-0)
    …  GR-1          whatever the owner schedules
    …  CPU-45        the second seating its stop-loss allows
    →  THIS BLOCK    last.  A wedge here costs the reset that ends the seating anyway.

⚠️ **The alternative that was rejected, and why.** Stopping after `E6` — arm,
wait one period, read `TCIR`, disarm, skip the comparison — saves ~80 s of board
time and **buys no safety at all**: by the time `E6` has returned, every register
this driver writes has been written and every hazard has either fired or not.
`E7`–`E9` are `cat`s and one `echo`. **A precaution that costs information and
removes no risk is not a precaution.**

⚠️ **The other alternative — read-only, never arm — fails the step.** `R5-2`'s
`D4` asks for a frequency within ±50 ppm, and `E1`–`E3` cannot produce a
frequency.

---

## 3. Before power

| | |
|---|---|
| image | `$FWRE_WORK/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin`, **1,030,144** bytes, sha256-16 `39abf11c2d6fd0ce` — **staged 2026-09-03 03:06**, `rtkload`'s own `nfjrom` renamed |
| its source | `vmlinux` sha256-16 `2b0d1618d9946cc6`, cell `r51quiet`, **recipe `229d2983`**, so the board must print `RLXFW-ID0=229D2983` |
| 🔴 `config/` is FROZEN | `RECIPE_ID` is a sha256 over `config/` — 量 today, **15 files**, re-derived to `229d2983`, matching the staged image. **Any write under `config/` invalidates this image** and the seating would need a rebuild and a re-stage |
| the driver in it | `drivers/clocksource/rtl819x-timer.c`, **642 lines**, in the image via `MK2` (`obj-y += rtl819x-timer.o`) |
| `CAP` | `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0` |
| `OUT` | `--out bench/2026-09-03/` |
| host preflight | the long-lived WSL process, re-reading **both** busids, the NIC at `10.1.1.2/24`, `/usr/bin/python3` — `RUNSHEET` §B5's, **not restated here**. One owner |
| pre-flight | a 3 s capture with the board **off**: 0 bytes, which separates the adapter, the port and the board before a power cycle is spent |
| desk checks | `cardcheck commands` and `cardcheck numbers` on this file; `mkinitramfs verify` against the image the card names — `cardcheck` reads a declaration, not an image, and that is the other half |

**The precondition this whole block inherits**: the seating has already booted
this image and reached a shell, and the boot printed `RLXFW-ID0=229D2983`.
🔴 **A different eight digits and this block does not run** — the tree moved
between build and upload and every expectation below belongs to a different
binary.

---

## 4. The cells

`CAP` and `OUT` as above. Every row carries a terminator; `console-capture.py`
refuses a capture with neither `--seconds` nor `--idle`, and two of these rows
must use `--seconds` **alone** because a `sleep` on the board would trip
`--idle`.

Nine cells, `E1`–`E9`, as `notes/timer-driver.md` § 5.2 numbers them. Ten
captures, because the two `sysfs` files are 70 and 68 characters and the pair
does not fit under `console-capture.py`'s 128-byte line cliff (量: 141).

| capture | cell | typed | **precondition** | expect | 🔴 stop if |
|---|---|---|---|---|---|
| **`TM-1`** | `E1` `E2` | `CAP OUT TM-1 --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20` | at a shell; **nothing armed this power cycle** | 37 lines; `state=idle`, `last_verdict=0`, `mult=1174376947`, `hz_assumed=14286057`, `period_cycles=134217728`, `mask_bits=27`, `shift=24`, `rating=0`; `tccnr=C0000000`, `tcir=80000000`, `cdbr=000E0000`, `tc0data=0022E0A0`, `tc1data=00000000`; `gimr_tc1ie=0`, `gisr_tc1ip=0`, `tc0_undisturbed=1`, `tc1_ext_reads=0` | 🔴 **`gimr_tc1ie=1` is a STOP: do not arm.** Everything else on the seating still runs; the finding *is* the reading. `no such file` → the driver did not register and `MARK-1`'s gap just became a measurement |
| **`TM-2a`** | `E3` | `CAP OUT TM-2a --send 'cat /sys/devices/system/clocksource/clocksource0/available_clocksource' --idle 3 --seconds 15` | before `TM-3` | **`jiffies`** and nothing else | `rtl819x-tc1` present here → the driver registered something it was not asked to, and `L2-f` is wrong |
| **`TM-2b`** | `E3` | `CAP OUT TM-2b --send 'cat /sys/devices/system/clocksource/clocksource0/current_clocksource' --idle 3 --seconds 15` | before `TM-3` | **`jiffies`** | any other name → § 1's desk scan is refuted and that name is the vendor's clocksource |
| **`TM-3`** | `E4` | `CAP OUT TM-3 --send 'echo arm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `TM-1` read `gimr_tc1ie=0` **and** `tc0_undisturbed=1` | no shell error; then `state=armed`, `last_verdict=0`, `arm_delta_100us` in **1300…1600**, `tc0_undisturbed=1`, `tccnr` = `C0000000` with bits 29/28 set per `tccnr_after_arm` | any of the five errnos (§ 4.1 of the note) — **each is a result, none is a driver bug until the register dump says otherwise.** `-EIO`, or `tc0_undisturbed=0` at any point → **disarm and end the timer block for this seating** |
| **`TM-4a`** | `E5` | `CAP OUT TM-4a --send 'cat /sys/devices/system/clocksource/clocksource0/available_clocksource' --idle 3 --seconds 15` | `TM-3` returned `state=armed` | **`jiffies rtl819x-tc1`** — both, in registration order | `rtl819x-tc1` absent → `clocksource_register` returned an error the dump did not show |
| **`TM-4b`** | `E5` | `CAP OUT TM-4b --send 'cat /sys/devices/system/clocksource/clocksource0/current_clocksource' --idle 3 --seconds 15` | as above | **`jiffies`** — still | 🔴 `rtl819x-tc1` → **rating 0 did not keep it out**, `L2-e`'s enqueue analysis is wrong, **and `E8` is void** because the kernel would then be reading time from the thing `E8` compares against. Disarm; the finding is the reading |
| **`TM-5`** | `E6` | `CAP OUT TM-5 --send 'sleep 10 ; cat /proc/rtl819x-timer' --seconds 25` | armed; ≥ one TC1 period (9.395016 s) must elapse | the board still answers; `gisr_tc1ip` and `tcir_tc1ip` each 0 or 1; `tc1_ext_reads=2` | 🔴 **the board not answering is `H2` firing through a path this design says is masked**, and it refutes § 4's whole argument. Power-cycle; do not re-arm |
| **`TM-6`** | `E7` `E8` | `CAP OUT TM-6 --send 'cat /proc/rtl819x-timer ; sleep 30 ; cat /proc/rtl819x-timer ; sleep 30 ; cat /proc/rtl819x-timer' --seconds 80` | armed; `TM-4b` did **not** name `rtl819x-tc1` | three dumps, ~30 s apart, in one capture so one host time base covers all three | fewer than three dumps → the capture was cut; retake, it costs 80 s and no power. **`--idle` must not appear on this row** |
| **`TM-7`** | `E9` | `CAP OUT TM-7 --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | armed | `state=idle`, `last_verdict=0`, **`tccnr` back to `tccnr_at_init`** | `tccnr` not returning to its `at_init` value → the driver cannot undo its own write, and that is worth knowing before `R5-3` |
| **`TM-8`** | `E9` | `CAP OUT TM-8 --send 'cat /sys/devices/system/clocksource/clocksource0/available_clocksource' --idle 3 --seconds 15` | after `TM-7` | **`jiffies`** — `rtl819x-tc1` gone | still present → `clocksource_unregister` did not take, and the block is left in a state `R5-3` has to clean up |

### 4.1 🔴 Three lines are typed with `;` and none of them needs a shell feature `cardcheck` cannot see

`argv0s()` is not a shell. It splits on whitespace, treats `;` as a separator and
drops redirections with their targets — so `cat` / `sleep` / `cat` / `sleep` /
`cat` are all seen, and `echo arm > /proc/rtl819x-timer` is seen as `echo` with
the target exempted because `/proc/` and `/sys/` are the kernel's, not the
initramfs's.

⚠️ **`echo $?` is deliberately NOT used**, and § 5.2's `E4` writes it. `B9`
refuses any `$` in a committed card's `--send`, because that is the tokeniser's
own precondition. **The driver prints `last_verdict` for exactly this reason** —
its own record of the errno, which is strictly better than the shell's, because
it survives into a capture taken afterwards.

量: every typed line above is under the 128-byte cliff — longest is `TM-6` at
**97** characters, then the two `sysfs` reads at 70 and 68.

### 4.2 The arithmetic the reader does, written before the readings exist

For any two of `TM-6`'s three dumps, `i` before `j`:

```
Δjiffies    = jiffies_j − jiffies_i                        (exact, an integer)
ΔTC0_total  = Δjiffies × 142858 + ((tc0cnt_j >> 4) − (tc0cnt_i >> 4))
n_wraps     = round( (ΔTC0_total − ((tc1_cycles_j − tc1_cycles_i) mod 2²⁷)) / 2²⁷ )
ΔTC1        = n_wraps × 2²⁷ + ((tc1_cycles_j − tc1_cycles_i) mod 2²⁷)
```

* **`n_wraps` is safe by a factor of ~470.** Over 30 s it is 3, and the estimate
  would have to be wrong by half a period — 4.7 s in 30 — to round to the wrong
  integer. `Δjiffies` is exact and `CLK-17` is ±7 ppm.
* **`ΔTC1 / ΔTC0_total` is the measurement** (`E7`). Both counters are read in
  the same `spin_lock_irqsave`, a few hundred nanoseconds apart, and the skew is
  the same at both endpoints, so it cancels.
* **`E8` is then arithmetic, not a second measurement**: the kernel reports
  `Δjiffies × 10 ms` and the driver reports `ΔTC1 / 14286057`. With
  `ΔTC1 = ΔTC0_total` those differ by exactly
  `14286057 / (100 × 142858) − 1 = +17.99 ppm`.
* **Three dumps, not two, and that is what makes the jitter measurable**: two
  intervals give two independent values of the same ratio, so the difference
  between them bounds the sampling noise instead of leaving it asserted.

For the host-clock cross-check, each dump's first byte is located in `TM-6.log`
and mapped to the last `.timing` row at or before that offset. ⚠️ **The board's
read-to-first-byte latency is not measured** — it is ~constant and cancels in a
difference, but its *jitter* does not, and the two intervals are what show it.

---

## 5. Predictions, with refutation conditions

| id | prediction | refuted by |
|---|---|---|
| **`Q1`** | `TM-1` prints **37** lines and `gimr_tc1ie=0` | `gimr_tc1ie=1` → Linux unmasked TC1's interrupt. A finding about the vendor's setup obtained without reading it, and the block stops |
| **`Q2`** | `TM-1`'s `tccnr`/`tcir`/`cdbr`/`tc0data`/`tc1data` equal `SPEC.md` `REG-05`…`REG-11` | a difference → **Linux leaves the block in a different state from the loader**, which is a finding about `arch/rlx/kernel/rlx-time.c` obtained without opening it. Those five values were read at the **loader prompt**; this is the first reading of them under a kernel |
| **`Q3`** | `tc0cnt & 0x0F == 0` and `tc0cnt >> 4 < 0x22E0A` in every dump | either failing → `TC0CNT` is **not** value-in-bits-31:4, D Table 22 is being read the wrong way, and § 4.2's `>> 4` is wrong. **This is the only test in this project of that shift** |
| **`Q4`** | `TM-2a` and `TM-2b` both read exactly **`jiffies`** | any other name in `available` → a clocksource § 1's scan says does not exist. That refutes the desk scan, and `TM-2b` names the winner |
| **`Q5`** | 🔴 `TM-6` reports `tc1_ext_trusted=1` **and it is FALSE** — `tc1_ext_gap_max` lands near **25,928,526**, three wraps short of the true 428,581,710 | `tc1_ext_gap_max` above 67,108,863 with `trusted=0`, which would mean the gap did not alias. Either way `tc1_ext` is not quoted; § 0.1 |
| **`Q6`** | **`ΔTC1 / ΔTC0_total` = 1.000000 ± 50 ppm**, and in fact within a few ppm | outside ±50 ppm → **TC1 does not divide the same `CDBR` as TC0**, which is § 2's one 讀-only assumption about this driver's rate. That is a finding about the hardware, not about the driver |
| **`Q7`** | the two intervals of `TM-6` agree with each other to within **20 ppm** | a disagreement → sampling jitter dominates, and `Q6`'s tolerance is not earned. **`Q7` is what makes `Q6` a measurement rather than a number** |
| **`Q8`** | a **step of exactly 142,858 counts** in `ΔTC1 − ΔTC0_total` in either interval — i.e. one lost tick — does **not** occur | its occurrence → the vendor's tick loses jiffies under a shell-idle load, which nothing on this board has ever looked for. **The interval resolves ~0.001 ppm, so a single lost tick is 167 ppm and unmissable** |
| **`Q9`** | 猜, uncalibrated: `arm_delta_100us` lands in **1350…1500** | nothing; it is a guess. The derived value is 1,428.6 and the stop-if window is 1300…1600 |
| **`Q10`** | `TM-5` finds `tcir_tc1ip=1` with `gisr_tc1ip=1` and the board alive | `tcir_tc1ip=0` after ≥ 9.396 s → the pending bit does **not** latch while `TC1IE` is clear, which is a different and equally useful answer. `R5-3` needs whichever it is |

🔴 **`Q6` is the cell the whole block exists for**, and it is the one that
cannot be satisfied by accident: `ΔTC0_total` is built from the vendor's tick and
`ΔTC1` from a counter the vendor does not use, and nothing but a shared divider
makes them equal.

⚠️ **`Q8` is the only cell here that can find a defect in something other than
this driver**, and it is free — it is the same three dumps read a second way.

---

## 6. Abort conditions for the block as a whole

* `TM-1` reads `gimr_tc1ie=1` → **do not arm.** `TM-1` is still a reading and
  `Q1`/`Q2`/`Q3` still answer. The block ends there.
* `TM-1` says `no such file` → the driver is not in the running kernel. Check
  the boot's `RLXFW-ID0`; then this is `MARK-1` turning from a gap into a
  measurement, and it is worth more than the rest of the block.
* `TM-3` returns `-EIO`, or **any** dump reads `tc0_undisturbed=0` → send
  `disarm`, take `TM-7`/`TM-8`, and stop the timer block for this seating.
* The board stops answering after `TM-3` or during `TM-5` → `H2` through an
  unmodelled path. **Power-cycle once; do not re-arm.** That outcome is the most
  valuable thing this block can produce and it is recorded, not retried.
* `TM-4b` names `rtl819x-tc1` → disarm immediately. Nothing after that is
  interpretable, because the kernel would be reading time from the thing under
  test.
* Any capture that opens **after** the board has started talking is void; retake
  it rather than reading it.
* 🔴 **Nothing on this card is retried by re-arming after a wedge.** The disarm
  path has never executed either.

---

## 7. What this block cannot tell you, stated before it runs

1. **It does not make the timer the system time base.** Rating 0 is chosen so
   that nothing switches to it; `R5-3` is the step that changes that and it is
   the first irreversible-feeling one of the gate.
2. **It does not measure the crystal.** `Q6` compares two counters that share
   one base clock, so it tests the *model* — TC0's period, `HZ`, no lost ticks,
   both timers on one divider — and not the oscillator. `CLK-02`'s ±7 ppm is
   still the only reading of that.
3. **It does not exercise the interrupt.** `GIMR` is read and never written, so
   TC1's timeout is never delivered. `Q10` reads a latch, not a handler.
4. **`arch/rlx/kernel/rlx-time.c` is still unopened**, and `Q2` is the closest
   this project will get to reading it without reading it.
5. **The `/proc` interface is an instrument, not a driver.** `create_proc_entry`
   with `read_proc`/`write_proc` is the 2.6.30 idiom for a small file; a driver
   submitted upstream would use `proc_create` and `seq_file`. `D1`'s *accepted
   upstream-style* is claimed for the clocksource half only.
6. **No `.dts` node and no binding yet** — `D2` is not touched here, and the
   `reg` a binding would carry depends on what this block finds the driver
   actually needs to claim.

---

## 8. The machine-readable halves

`cardcheck numbers` re-derives every value below from the artefact named beside
it, rather than comparing it to a transcription. `check-predictions` uses the
cell list to prove each capture's mtime is later than this file's.

```cardnum
img-bytes	1030144	size /home/key/fwre-work/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin
img-sha16	39abf11c2d6fd0ce	sha256-16 /home/key/fwre-work/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin
img-word-18	3C108060	word32 /home/key/fwre-work/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin 24
img-word-1C	2610B800	word32 /home/key/fwre-work/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin 28
prev-img-word-1C	2610AC00	word32 /home/key/fwre-work/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin 28
vmlinux-sha16	2b0d1618d9946cc6	sha256-16 /home/key/fwre-work/rebuild/bench-only/r51-20260903/r51/kroot/vmlinux
drv-lines	642	lines config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c
proc-lines	37	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c scnprintf
```

⚠️ `prev-img-word-1C` is here so that the image discriminator is a **contrast**
and not a lone value: `2610B800` is tonight's, `2610AC00` is seating 10's
`lp-20260902`, and both are re-derived from images on disk. A stop condition that
names only the value it wants cannot say what it would be seeing instead.

⚠️ `proc-lines` is `scnprintf` counted in the driver's source and it equals the
number of lines the `/proc` dump prints, because 量 today **all 37 `scnprintf`
calls in the file are inside `rtl819x_tc_read_proc`**. A dump with fewer lines
means the capture was cut, and this is the number that says so.

⚠️ **`RECIPE_ID` is not in this fence and cannot be**: it is a sha256 over a
whole directory and `cardnum`'s expressions read one file each. It was
re-derived by hand today — `find config -type f | sort | sha256sum | sha256sum`,
15 files, **`229d2983`** — and `§ 3` carries it.

```cells
bench/2026-09-03/TM-1
bench/2026-09-03/TM-2a
bench/2026-09-03/TM-2b
bench/2026-09-03/TM-3
bench/2026-09-03/TM-4a
bench/2026-09-03/TM-4b
bench/2026-09-03/TM-5
bench/2026-09-03/TM-6
bench/2026-09-03/TM-7
bench/2026-09-03/TM-8
```

⚠️ Ten captures for nine cells `E1`–`E9`: `E1` and `E2` are one dump read two
ways, `E7` and `E8` are one capture analysed two ways, and `E3`, `E5` and `E9`
each take two captures because the two `sysfs` paths do not fit on one line.
The mapping is the `cell` column of § 4 and it is written there rather than
inferred, because a reader counting cells against captures would otherwise find
a discrepancy and have to guess which number was wrong.
