# Corrections and results — block 14, seating 17, 2026-09-08

**Three power cycles, not one.** The card predicted one; two more were spent, and
both were spent on the same class of mistake: **a cell whose payload can reset
the board, given no `--esc-after`.** Written here rather than in the frozen card.

`tools/capdate.py`: `OK 2026-09-08b — 68 capture(s), all 2026-09-08`. The
directory name stopped being a prediction at 22:37 and `D1` passes with no `D2`
split.

---

## 1. What the seating established

### 1.1 🟢 The headline is a rate, and it agrees with a number nobody re-measured

**量: `f_wdt(Linux) = 200,180 Hz.**

Two rungs, **32× apart**, each carrying its own 50 ms ruler in the same capture:

| rung | encoding | silence after `RLXFW-W-GO` | ruler | floor |
|---|---|---|---|---|
| `bite 3` (`C2-B`) | `00E00000` | **1,334.723 ms** | 50.517 ms | **0.517 ms** |
| `bite 8` (`R2-B8`) | `00840000` | **41,930.599 ms** | 49.132 ms | **0.868 ms** |

`gap(8) − gap(3) = 40,595.876 ms` over `2^23 − 2^18 = 8,126,464` counts, so
`f = 200,180 Hz` with `d = +25.179 ms` — positive and small, which is the
condition a physical offset has to satisfy and which the first (wrong) two-point
attempt failed.

🟢 **`CLK-17` measured `TC0CNT` under Linux at 200,005 Hz, on a different
register, by a different method, in a different seating. The ratio is 0.999 —
agreement to 0.09 %.**

🔴 **So `CLK-08b`'s 14,965,000 Hz is a LOADER-STATE constant, exactly as
`CLK-17`'s 14,286,057 Hz is.** The watchdog counts what the timer block counts,
and Linux's `CDBR` reprogramming (÷14 → ÷1000) slows both. `CLK-08b` 殘留 asked
*what does the watchdog count* and said it could not be settled by measuring a
timeout again. That was right about the **loader**; the answer came from
measuring a timeout **in the other state**.

### 1.2 🔴 `FW-45` is refuted, six days after it was written, and its downstream claims go with it

`SPEC.md` `FW-45` (2026-09-08, the forty-fifth segment) says this board runs a
**17,517 µs** watchdog under Linux, kicked every 10 ms, with a **7.5 ms** margin,
so *"not one timer interrupt may be lost."*

量: the encoding it names — `0x00600000`, `bsp_timer_init`'s own word — bites at
**1,334.723 ms**. **76× longer.** The margin is ~1.3 s, so roughly **130**
consecutive lost ticks are survivable, not zero.

Two committed sentences fall with it and are retracted in place:

* *"seating 16's three 4 MiB PIO traversals ran under that deadline, so no
  interrupt-blocked window on that path exceeded 17.5 ms"* — the bound is
  **1,310 ms**, i.e. **75× weaker**. The measurement that "meant more" means
  much less.
* *"`bsp_machine_restart` is a bite at `OVSEL` 0 = 2,190 µs"* — `OVSEL` 0 under
  Linux is **163.7 ms**, so `FW-37`'s 2.407 s is re-attributed a third time.

⚠️ **This does not move the DECISION.** `CONFIG_RTL_WTDOG=n` was justified by the
*existence* of an unconditional 100 Hz kick, not by the window's length, and a
watchdog that cannot bite still cannot bite at 1.3 s.

🟢 **It makes this driver safer than designed**, which is the direction one wants
to be wrong in: `kick_ms 250` against `OVSEL` 9 was believed to be a 4.48×
margin; it is **335×** (83.8 s).

### 1.3 🟢 Boot 1, and the predictions that landed exactly

| | predicted at the desk | measured |
|---|---|---|
| boot capture | **1,424** bytes | **1,424**, on **ten** boots |
| `RLXFW-ID0` | `B417A3E7` | `B417A3E7` |
| `wdtcnr_at_probe` | **`A5000000`** | **`A5000000`** |
| `TA5` | `FFFF8D37` ± 2 | **`FFFF8D38`** |
| `W4` | `00240000` **or** `00A40000` | **`00240000`** |
| ten `ovselN` rows | as tabled | all ten exact |
| `map_hashed` / `h601_skipped` / `h601_hashed` | 4186112 / 8192 / 0 | all three |

**`wdtcnr_at_probe A5000000` is the whole proof that `CONFIG_RTL_WTDOG=n` did
what the blast-radius enumeration said**, and it is one field with two possible
values, written down before the build.

🟢 **`W4 = 00240000` is a free reading nobody planned**: the driver wrote
`0x00A40000` (arm **and** `WDTCLR`) and the register reads back `0x00240000`, so
**`WDTCLR` does not read back on this die.** The masked comparison that ignores
it was right to.

🟢 **`ovsel3 enc 00600000`** — a driver written blind, from a split-field decode
the vendor never documented, computes the vendor's own constant.

### 1.4 🟢 Constraint ① is a ratio with no residual

| | Δjiffies | Δn_hw_kick | predicted (Δj/25) |
|---|---|---|---|
| at rest (`C1-P`→`C1-K`) | 343 | **14** | 13.72 |
| across the **armed** 4 MiB traversal (`C1-MA`→`C1-MK`) | 12,143 | **485** | 485.7 |

`map_jiffies` = **1,280** unarmed and **1,280** armed; the 32 digest lines are
**byte-identical between the two runs**. So the timer wheel ran at exactly its
programmed rate through a 12.8 s kernel-mode SPI traversal under a live deadline
— which is far stronger than *"the board survived"*, and `C1-K` is the control
that says what the rate is when nothing else is happening.

🔴 **`jiffies` wrapped through zero inside that measurement** (4,294,955,745 →
592) — Linux's `INITIAL_JIFFIES = −300·HZ` wrap, 300 s after boot. A naive Δ
would have been wrong by 4.29 billion.

### 1.5 🟢 The flash question moves, and it was not the headline

`C1-M0`/`C1-M1` are `rtl819x-spi` 1.1's **first execution on silicon**.
`flashmap compare`: **31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing.** The one
that differs is **group 0** (`0x000000`–`0x01FFFF`), which is where seating 16's
bisection put the first difference (`[0x9000,0xA000)`).

**So `FLS-26`'s undetermined bulk collapses**: 31 groups × 131,072 =
**4,063,232 bytes proven identical to the 2026-08-16 dump**, by an instrument
that shares no code with the bisection. What remains undetermined is inside
group 0's 122,880 hashed bytes, plus `H601`'s 8,192 which are skipped by rule.

⚠️ **A level-0 map cannot say whether group 0 holds one difference or several.**
That needs `map 1 0`, which did not run.

🔴 **The bracket does not move**: zero flash-write commands, zero `FLR`,
`1,024 / 4,194,304 = 0.0244 %` unchanged. `n_writes 0` on the driver's own
counter at `R2-FS`.

### 1.6 🟢 Three refusals, three errnos, one driver

Routed through `cat` so `strerror` prints, rather than through ash's truncated
echo (`FW-41`):

| cell | typed | `cat: write error:` | `n_reject` |
|---|---|---|---|
| `C1-EP` | `wedge` while locked | **Operation not permitted** | 1 |
| `C1-RJ` | `ovsel 5` (the hole) | **Operation not supported** | 2 |
| `C1-RI` | `ovsel 11` (out of range) | **Invalid argument** | 3 |

`hw_ovsel` read **9** after both refusals, so a rejected setting does not
half-apply. This is the driver header's *"distinguishable at the shell"* claim,
tested.

### 1.7 🟢 "Am I the only feeder" — answered, and the answer is yes

🔴 **The carded cell was VOID and the seating's own third cell is what showed
it.** The trap was `kickms 3000` against `OVSEL` 9, believed to be 1.121 s. At
the real 83.8 s the kernel timer would kick **28 times** before the hardware
could bite: the cell tested nothing.

Re-run at `OVSEL` 0 (163.7 ms) against the same 3 s timer, both halves:

| cell | wlan | result |
|---|---|---|
| `R2-SO3` | **down** | board reset, `Reboot Result from Watchdog Timeout!` |
| `R2-SO6` | **up** (`ifconfig wlan0 up` first) | board reset, same line |

**So nothing else on this board writes `WDTCLR` after `late_initcall`, including
with the vendor's wlan driver brought up by hand.** The three surviving vendor
kicks are on `rtl8192cd`'s bring-up path at `__initcall_..._init6`, level 6,
against this driver's level 7 — and a userspace `ifconfig up` does not re-enter
them in a way that feeds the dog. That was 未定 and reading more source could not
settle it.

### 1.8 🔴 Constraint ④ is refuted in BOTH directions

Both `biteraw` words are `OVSEL` 0 in every known bit, plus the candidate bit.
So: if the bit does nothing → **163.7 ms**; if it is `OVSEL[2]` → `OVSEL` 4 =
**2,619 ms**.

| cell | word | ruler | silence | either prediction? |
|---|---|---|---|---|
| `R2-RAW19` | `00080000` | 50.370 ms | **68.647 ms** | no |
| `R2-RAW20` | `00100000` | 50.719 ms | **12.336 ms** | no |

🔴 **Neither bit 19 nor bit 20 is `OVSEL[2]`** — and both **shorten** the timeout
below `OVSEL` 0, by different factors (5.6× apart), which no reading of an
`OVSEL` bit predicts. **The hole stays open with two new facts in it.** The card
anticipated a null result (§6.5) but predicted the wrong null: it said both
would land on 2.19 ms.

### 1.9 🟢 A reset-cause discriminator that has been on disk since 2026-08-24

The loader prints `Reboot Result from Watchdog Timeout!` after a watchdog reset
and prints **nothing there** after a power-on. Both directions were already in
this repository — every `A-catch.log` back to 2026-08-24 is silent, every warm
reset carries the line — and nothing had read it.

量 this seating, **three** cold power-ons (`C1-A`, `R1-A`, `R2-A2`): 0 lines.
**Nine** watchdog resets: 1 line each. It uses no timestamp, and for `R2-RAW19`
/ `R2-RAW20` it is what separates *"the board reset"* from *"the board reset
because of a watchdog timeout"*.

⚠️ **Where the loader reads it is undetermined and this file does not guess.** A
plain-ASCII search of the 4 MiB dump finds nothing — **but the positive control
also fails**: `RealTek`, `ramSize`, `chipName` and `Ethernet init` are all absent
too, and only `Booting` is present (offset 990). **The search is uninformative,
and the failed control is what says so.** The banner is presumably in stage 2;
`$FWRE_WORK/stage2.bin` is where to look. Carried forward.

### 1.10 🟢 `n_state_foreign`'s positive control fired

`R2-WG` ran `wedge` without resetting the board, and `R2-F` reads **`n_wedge 1`,
`n_state_foreign 1`, `shadow_agrees 1`**. Section 5.4 of the driver says that
counter *cannot* fire in the shipping image; this is the only way it is ever
seen to move, and it has now moved.

---

## 2. The defects, and what each cost

### 2.1 🔴 `wedge` bit the board once, and is not reproducible — cost: power cycle 2

`C1-WG` typed `echo wedge > /proc/rtl819x-wdt` and the board reset **mid-echo**,
at `; c` — about 9 ms in, **before the command line was complete**, so the write
had not happened yet. The loader printed the watchdog reset-cause line.

The cell had `--idle 3 --seconds 20` and **no `--esc-after`**, because the driver
header states *"Stopped, so this cannot start a countdown"* and the card
inherited that. The loader was not caught, it autobooted from flash, and the
board ran **vendor firmware** until a power cycle.

🔴 **`R2-WG` re-ran `wedge` on a fresh boot with `--esc-after 20` and it did NOT
bite** — `n_wedge` incremented, the board stayed up. **So the first bite was not
caused by `wedge`.** One observation, unexplained, not reproduced. What it was
is undetermined; the board had by then been up ~5 minutes, had run two 4 MiB
traversals, and had crossed the `jiffies` wrap.

### 2.2 🔴 Rung 8's window was 20 s and the answer was 41.9 s — cost: power cycle 3

`C3-B` armed correctly (`W-BITE=00840000`) and went silent. The card's window
came from `2^23 / 14,965,000 = 560 ms`; the true value is `2^23 / 200,180 =
41.9 s`. The bite happened after the capture closed, so the loader autobooted
again.

**This is the same root cause as §1.2**: every window on the card was computed
from a loader-state constant. The card could not have known — the constant was
refuted by the card's own third cell.

### 2.3 🟢 The guard that stopped the third failure from becoming a fourth

After the second recovery the runner gained a `caught()` check: after every bite,
**prove the loader was caught before handing the board to `looprun`**. It fired
on `C3-B` and aborted, and it fired again on `R2-WG`. Without it, `looprun` would
have run its rescue stage against vendor firmware twice more.

### 2.4 🔴 `rung 0` is not measurable by this method, and the card did not know

`C1-B` shows `RLXFW-W-GO` followed by a corrupt `0x8D`, then the loader's output
with **no silence at all** (1.095 ms). `prom_putchar` fills a UART **FIFO**, not
the wire, so `rlxfw_puts` returns with up to 16 bytes still queued; the arm
happens then, and at 163.7 ms the reset lands mid-drain. §4.3a assumed `puts`
drained to the wire.

**So the ladder has two clean rungs, not four**, and `f` rests on those two.

### 2.5 🔴 Two `cardnum` self-reference defects, caught at gate 4

A `count` row searches the **whole file**, including its own declaration. A regex
that is a pure literal matches itself and the row reads one high. `expansion-reboot-f`
did exactly that. **The fix took two tries**: bracketing the last character fixed
the row, and the row still read 1 — because the *paragraph written to explain the
fix* spelled the command out again. Both are documented in the frozen card.

⚠️ Block 13's equivalent row escaped this only because its regex contained
`[0-9]+`, which cannot match itself. **It passed for the right answer by
accident**, and nobody knew there was a rule.

### 2.6 ⚠️ Off-card cells, declared

The fence is frozen at 42 and **19 of them have captures**. Everything after the
first recovery ran under `R1-*` / `R2-*` names because the card's windows were
computed from a refuted constant, and **editing a frozen card to fit the
experiment is the opposite of what rule 1 is for**. Seating 16 set the precedent
with 19 off-card `BIS-*` rungs.

Off-card, in this directory: `R1-A`, `R1-DV`, `R2-A` (an interrupted 8,157-byte
partial with no loader prompt — vendor-firmware ESC echo), `R2-A2`, `R2-B8`,
`R2-SO1`…`R2-SO6`, `R2-WU`, `R2-U19`, `R2-U20`, `R2-UW`, `R2-RAW19`,
`R2-RAW20`, `R2-WG`, `R2-F`, `R2-FS`, and the `R1`…`R8` `looprun` artefacts.

Fence cells with captures that are **not** what was predicted:
* `C1-WG` — holds the unexplained bite, which is §2.1's evidence rather than a
  `/proc` dump;
* `C1-DV` — holds a **vendor firmware** boot. Void; redone as `R1-DV`
  (`state 1 BOOTGUARD`, `n_user_ping 1`, `n_unclean_close 0` — the magic close
  returns to `BOOTGUARD`, which is the header's deliberate deviation, confirmed);
* `C3-B` — armed rung 8 and holds no bite, for the reason in §2.2.

---

## 3. What did not run

* `C4-B` (rung 9, now ~83.8 s), `C5`–`C10` as carded, the `/dev/watchdog` USER
  bite (`C7-B` — `soft_timeout` 60 s then a hardware bite within 83.8 s, so the
  card's 85 s window was also too short), and `map 1 0`.
* **The `OVSEL` ladder has two rungs**, so `f` has no third point. Rung 9 would
  give one and costs ~90 s plus a boot.
* `D2` — still 0 `.dts` and 0 `.yaml` in the whole tree.

## 4. Zero-write

**Zero flash-write commands, zero `FLR`.** `n_writes 0`. `AUTOBURN` read
`00000000` before every one of the ten uploads (`A0b`, eight assertions per
`looprun`, ten times). The bracket stands at **1,024 / 4,194,304 = 0.0244 %**.

⚠️ **The vendor firmware ran twice**, for roughly two and four minutes, because
two bites were not caught. Seating 8 has the precedent and its bracket was
unchanged, but this is exposure that was not planned and is recorded as such.
