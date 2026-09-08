# Corrections — block 15, seating 18, 2026-09-09

**The card is frozen. Nothing above is edited; everything the seating
refuted is here.** Every number in this file is computed from the committed
captures by `scratchpad/gencorr.py`, not transcribed.

One power cycle, thirteen carded boots plus one off-card, **828 s** of
chained cells with no operator gap. `check-predictions` **27 of 27**;
`capdate` **78 captures, all 2026-09-09**; every boot capture **1,424 bytes**.

---

## 1. 🔴 The card's own refutations, in the order they landed

### 1.1 §3.1 predicted TWO differing boot fields. There are THREE, and the
third is not noise

量, all thirteen: **1,424 bytes** every time — the length half of the control
holds exactly. But the fields that differ from seating 17's `C1-boot` are
`RLXFW-ID0`, `RLXFW-TA5` **and `RLXFW-TA6`**.

`TA6` is `rtl819x_boot_pre_dj - rtl819x_boot_pre_dc`: the number of TC1
interrupts LOST over the driver-init pre-check window, which is `IRQ-13`'s
quantity. Seating 17: **11** on nine boots, 12 on one. Seating 18:
**8 on all thirteen.**

🔴 **It is systematic and it is not this driver's added code.** `WDT-1` adds
two uncached register reads and a `do_div` — microseconds — and three
interrupts is 30 ms. 推, and it is the only candidate this segment can name:
`vmlinux` grew **233 bytes**, which shifts everything after it and changes
which I-cache lines the vendor's NIC initialisation occupies (16 KiB,
16-byte lines, 2-way — `probe3`, 2026-08-29). **Refuted by** a third image
with a different size giving 8 again, or by `TA6` moving without a size
change.

🟢 And the split into two sha256 groups is `FW-40` seen a third time: `C6`–
`C13` carry `RLXFW-G3=0000007C` where `C1`–`C5` carry seating 17's
`0000003C`. The difference is `0x40` — **bit 6, the LED the vendor's
`rtl_gpio_timer` blinks**.

### 1.2 🔴 §3.3's `WDTCNR` column is wrong on every row

The card tabled `00000000` / `00600000` / `00040000` / `00240000`. 量, from
the marks the board printed: **`00800000` / `00E00000` / `00840000` /
`00A40000`**. `rtl819x_wdt_verb_bite` composes with `kick = 1`, so every
`bite` word carries `WDTCLR`. The OVSEL encoding is unchanged; the column
was written from the table rather than from the code path.

🟢 **That mistake is what made the seating's best result possible**, because
it means `bite` CLEARS the counter and `biteraw` does not — see § 3.

### 1.3 🔴 §3.7 predicted ONE differing unit in group 0. There are TWO

`flashmap compare` on `C1-M1`: **30 same, 2 DIFFER, 0 scope, 0 extra,
0 missing**, with `006000` and `007000` `SKIPPED` on both sides by the `H601`
rule. The two are **`009000`** — where seating 16's prefix bisection put the
first difference — and **`00D000`**, which nothing had ever seen.

🟢 The card said why in advance: *a prefix digest finds the first difference
and nothing past it*. This is the cell that looked past it, and there was
something there.

### 1.4 🔴 §3.5 called bit 23 an unknown. It is a control

`biteraw 0x00800000` is `WDTCLR` with every OVSEL bit clear — **the same word
`bite 0` composes**. It could never have been an unknown, and labelling it
one was an error in the card, not in the scan.

### 1.5 🔴 The per-capture `mdelay(50)` ruler is not readable in half the
bite cells

`rlxfw_mark()` interleaves character-by-character with busybox ash's echo
(`FW-47`, `FW-41`'s family). 量: `C3-B8` and `C4-B9` keep `-BITE=` contiguous;
`C1-B0` reads `W-w-dBt\rITE=00800000` and `C2-B3` reads `0\x1b\x000[E00000`.
**So two of the four rungs have no floor of their own**, and the card assumed
all four would. The GAP is unaffected — `RLXFW-W-GO` is written with
interrupts disabled and is contiguous in every capture.

### 1.6 🔴 §6 claims `n_writes` is 0 in every dump and NO CELL READS IT

A claim with no cell. It was closed **off-card** afterwards, and this is the
declaration of that: `OFF`, `OFF-SPI`, `OFF-WDT`, `OFF-IRQ` are outside §5's
fence on purpose, so `check-predictions 27 of 27` keeps meaning what it says.
量 `OFF-SPI`: `n_writes 0`, `n_write_refused 0`, `n_reg_writes 0`, `n_xfer 0`.

⚠️ **That is one boot, not thirteen.** The thirteen carded boots never had
the counter read. The stronger evidence for the flash sentence is § 2.

---

## 2. 🟢 `FLS-26`: the attribution bracket closed, and the ledger moved

`C1-M0` was the first command of the seating, before anything else could
touch the part. 量:

```
cmp bench/2026-09-08b/C1-M0.log bench/2026-09-09/C1-M0.log   ->  identical
```

**Byte-identical**, 3,013 bytes. Between the two readings: seating 17's
`map 0` at 22:45 on 2026-09-08, **the vendor firmware running twice** (~2 and
~4 minutes, the accident that seating recorded), a cold power-off, a cold
power-on, and `r57` booting.

🔴 **So those two vendor-firmware runs wrote nothing to the 4,186,112 bytes
this covers.** That is the second half of a bracket whose first half already
existed, closed at zero cost exactly as `PROGRESS.md` predicted.

**And the ledger moves for the first time since seating 16**, from `map 0`'s
31 identical groups plus `map 1 0`'s 28 identical units inside group 0:

| | seating 16 | seating 18 |
|---|---|---|
| proven identical | 28,672 B (0.684 %) | **4,177,920 B (99.61 %)** |
| proven different | 4,096 B (0.098 %) | **8,192 B (0.195 %)** |
| undetermined | 4,153,344 B (**99.02 %**) | **8,192 B (0.195 %)** |

⚠️ **The undetermined 8,192 B is exactly `H601`**, which is skipped by rule
in the tool and not by omission. ⚠️ And *proven identical* means *digests
agree with the 2026-08-16 dump*: it cannot see two writes that cancel, and
**no `FLR` full re-dump ran**.

---

## 3. 🟢🟢 The mechanism the seating found, which nobody carded

### 3.1 The ladder does not fit a straight line

Four rungs, `gap = 2^(15+OVSEL)/f + d`, least squares:

```
f = 199,800.1 Hz   d = -3.591 ms
  OVSEL 0  2^15 =     32,768   measured      163.911 ms   residual    +3.498 ms
  OVSEL 3  2^18 =    262,144   measured    1,340.982 ms   residual   +32.542 ms
  OVSEL 8  2^23 =  8,388,608   measured   41,910.358 ms   residual   -71.048 ms
  OVSEL 9  2^24 = 16,777,216   measured   84,001.412 ms   residual   +35.009 ms
```

Residuals of tens of milliseconds against an instrument whose repeatability
§3.3 measures at **1.456 ms**. The linear model is refuted.

### 3.2 🟢 `WDTCLR` decides whether the counter starts at zero, and that is
the whole explanation

`verb_bite` **disarms** (`WDTE = 0xA5`), waits `mdelay(50)`, then arms with
the word it was given. `bite N` composes that word with `kick = 1`, so
`WDTCLR` is set and the counter is cleared. `biteraw <raw>` passes the word
through, so `WDTCLR` is clear and **the counter continues from wherever
`BOOTGUARD`'s last kick left it**.

That bounds the deficit at `kick_ms × f` = `0.250 s × 199,903 Hz` =
**49,976 counts**, and a period `2^n` is admissible for a reading of
`c` counts iff `−tol ≤ 2^n − c ≤ bound`.

```
 bit      word       gap ms      implied  admissible 2^n (deficit)
  16     10000      153.640       30,713  2^15 (2,055), 2^16 (34,823)   ambiguous
  17     20000    2,475.923      494,944  2^19 (29,344)   UNIQUE
  18     40000   41,892.932    8,374,523  2^23 (14,085)   UNIQUE
  19     80000       21.906        4,379  2^15 (28,389)   UNIQUE
  20    100000       91.146       18,220  2^15 (14,548), 2^16 (47,316)   ambiguous
  21    200000      161.013       32,187  2^15 (581), 2^16 (33,349)   ambiguous
  22    400000      580.538      116,051  2^17 (15,021)   UNIQUE
  23    800000      165.367       33,057  2^15 (-289), 2^16 (32,479)   ambiguous
```

### 3.3 🟢🟢 The control that says it, and it is a factor of ninety

`C13-X23` and `C1-B0` send **the same word**, `0x00800000`, on two different
boots. `C6-X16`, `C9-X19` and `C10-X20` are all `OVSEL` 0 without `WDTCLR`.

| same period, `2^15` | readings | spread |
|---|---|---|
| **with** `WDTCLR` (counter cleared) | 163.911, 165.367 ms | **1.456 ms (0.89 %)** |
| **without** (counter not cleared) | 153.640, 21.906, 91.146 ms | **131.734 ms (148 %)** |

**A factor of 90.** Same silicon, same
period, one bit of difference in the arming word.

---

## 4. 🔴🔴 `OVSEL[2]` IS BIT 17, and `FW-53`'s conclusion is refuted

`FW-53` (seating 17) says: *neither bit 19 nor bit 20 is `OVSEL[2]` — both
shorten the timeout below `OVSEL` 0, which no `OVSEL` reading predicts.*

🟢 **Bit 17 is `OVSEL[2]`.** Its reading is the only one in the scan for
which exactly one power of two is admissible above `2^17`, and the
discriminating form needs no clock constant at all:

    bit 17 / bit 16 = 16.1151   against 2^19/2^15 = 16

Both cells are `biteraw`, so both carry a deficit; the ratio is therefore a
bound rather than an identity, and the **uniqueness** argument in § 3.2 is
what actually decides it.

🔴 **And the shortening `FW-53` could not explain is explained**: bits 19 and
20 are inert for the timeout — `2^15` is the only admissible period for bit
19 — and what shortens them is the uncleared counter. **The proof is that
the two seatings disagree**:

| bit | seating 17 | seating 18 | delta |
|---|---|---|---|
| 19 | 68.647 ms | 21.906 ms | -68.1 % |
| 20 | 12.336 ms | 91.146 ms | +638.9 % |

A hardware divider bit does not change value between seatings. **A random
starting count does.**

⚠️ **What the scan CANNOT say, and the card did not know it**: the deficit
bound (49,976) exceeds `2^15` (32,768), so a single un-cleared reading
cannot tell `OVSEL` 0 from `OVSEL` 1. Bits 16, 20, 21 and 23 stay ambiguous
by this method. **A `kickms 5000` before the `biteraw` would fix it** and
costs one extra command per cell.

---

## 5. 🔴 The host clock, and the hypothesis that got worse

`C1-R`, one capture, two `/proc` reads, both timestamps in one `.timing`:

```
Djiffies = 12,003  ->  board 120.030 s
Dt(host)                  120.0882 s
board/host = 0.999515731  =  -484.3 ppm
quantisation floor 83.3 ppm    timestamp floor ~8.3 ppm
```

`H2` needed **~900 ppm** to explain the watchdog's 0.09 % excess over the
timer. It is **-484 ppm**, and the sign is the wrong way.

🔴 **The correction makes the discrepancy larger, not smaller.** Both
quantities are measured against the same host clock, so its error cancels in
their ratio. Against that clock:

    f_tick = 12,003 jiffies x 2,000 counts / 120.0882 s = 199,903 Hz
    f_wdt  = 200,180 Hz  (seating 17's two-rung fit)
    excess = +0.138 %  where the nominal comparison gave +0.090 %

⚠️ **This seating's own ladder does not give a single `f_wdt` to put in that
line** — that is § 3.1's whole point. The comparison above uses seating 17's
figure and is therefore across seatings.

---

## 6. 🟢 What held

* **`WDT-1`, seven fields for seven**, at `C1-P`: `tc0data_at_init 00007D00`,
  `cdbr_at_init 03E80000`, `hz_tick 200000`, `hz_cdbr 200000`, `hz_agree 1`,
  `hz_derived 200000`, `hw_timeout_derived_us 83886080` — every one derived
  at the desk from registers `TM-1` measured on 2026-09-03, computed on the
  die by a driver written blind. Beside them the dump still prints
  `wdt_hz 14965000` and `hw_timeout_us 1121101`: **the 76× on one page**.
* **The `/dev/watchdog` USER path, end to end.** `C5-UB` held the device open
  with `sleep 400 > /dev/watchdog` and the board reset at **143.563 s**
  against a predicted 143.886 s — **-0.22 %**. 🟢 The evidence that the open reached
  `WDT_USER` is the bite itself: `BOOTGUARD` is fed every 250 ms and cannot
  bite. **A consequence, not a field.**
* **`--until` on every cell that needed it.** `C1-M0` came back at
  **13.684 s** with `--until matched at offset 2997` and **3,013 bytes**
  — the same byte count seating 17 took **120.106 s** to produce.
* **The recovery cells were the no-ops they were designed to be**: every
  `C*-Z*` matched `<RealTek>` in ~0.23 s because the bite had already left
  the board at the loader.
* `looprun` closed on all fourteen boots; `A3` — *the board printed the id
  the build computed* — held every time, `f67eed22`, typed by nobody.

---

## 7. What this seating did NOT establish

* **`f_wdt` is not measured by this seating.** Four rungs, no single `(f, d)`
  fits them, and `OVSEL` 3 is ~2 % long in **both** seatings while 0, 8 and 9
  agree within 0.22 %. That is an open, reproducible anomaly with no
  explanation, and it is the reason `CLK-08b`'s residual stays open.
* **The clocksource is still not mine.** `rating` 0 in every dump.
* **No flash byte count.** No `FLR`, no full re-dump; `map` compares digests
  against a dump and cannot see two writes that cancel.
* **`OVSEL` 0 vs 1 is undecidable by `biteraw`** at `kick_ms 250`.

