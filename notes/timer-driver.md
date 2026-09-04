# `R5-1` — `rtl819x-timer`, a clocksource written blind

**Desk, 2026-09-03. No power, no flash byte, no device reading.**
This file owns the timer driver's **design and its reasons**, and the design of
the reading `R5-2` will take. `SPEC.md` owns the numbers; `PROGRESS.md` owns
where the gate is; `docs/blind-write-ledger.md` owns what was read.

---

## 0. What is here, and the one sentence it is written to defend

`config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c` — 642 lines,
of which about **309 are code** — plus one row (`MK2`) in
`config/rlxfw-marks.tsv`, which is the Kbuild line that links it. Nothing else
in the vendor tree is touched.

The sentence: **no implementation of this timer was read to write it.** What
that is worth rests on `docs/blind-write-ledger.md` § 4.3, frozen and committed
**before** this file existed. 量 2026-09-03:

```
git log --diff-filter=A -- docs/blind-write-ledger.md
  aa89317  2026-09-03   (the ledger)
git log --diff-filter=A -- config/rlxfw-src/linux-2.6.30/drivers/
  bfd624c  2026-09-03   (this driver)
```

⚠️ **The command has to name the driver path, and the ledger's own § 8 says
`config/rlxfw-src/` instead — which is one directory too wide.** That
directory already held `rlxfw_mark.c` and `rlxfw-mark.h` from **2026-08-29**,
months of segments before the ledger; run as written, the check shows a file
of mine added *before* it and looks like a failure. Those two are the boot
ladder, not a driver, and the claim is about drivers. **The claim holds; the
command that checks it is narrowed here.** Today's reads are added to the
ledger, not recorded in this file.

---

## 1. The chain that forced Timer/Counter 1, and it is a chain rather than a preference

**① CP0 has no counter.** `SPEC.md` `CPU-42`, 量: `Count`(9) reads `00000000`
with `count.delta = 0` over 100,000 iterations, both destinations primed
differently first. **So a clocksource here has to come out of the SoC timer
block** — that is the narrow claim, and it is the one that is supported. This
project has readings for no other free-running counter on this part; that is
not the same as there being none.

**② TC0 is the vendor's tick and is unusable as a clocksource anyway.**
`SPEC.md` `CLK-17` records the reason and it is arithmetic, not caution: TC0
wraps every **142,858** counts — 9.9998 ms — and 142,858 **is not a power of
two**, so the two's-complement subtraction the clocksource contract is built
on is wrong for it. 讀 `include/linux/clocksource.h`, which documents `mask` as
*"bitmask for two's complement subtraction of non 64 bit counters"* — that is
the interface's own statement of the requirement, and it is what was read.
⚠️ **An earlier draft of this sentence cited `kernel/time/timekeeping.c`, which
is where the subtraction is actually performed and which was never opened here.**
`ledgerscan check` went red on it. A citation of a file nobody read is the exact
thing this project's ledger exists to stop, and it appeared inside an edit whose
whole purpose was to make a claim narrower. The software alternative is
`if (d < 0) d += 142858`, which is only correct if the counter is read more
often than once per wrap. `CONFIG_HZ=100` in this build, so the kernel's own
fastest periodic activity is *exactly* the wrap period. Nothing in this kernel
can guarantee it.

**③ An extended TC0 built on `jiffies` measures nothing.** `jiffies * 142858 +
TC0CNT` is a valid 64-bit counter and it was the first design considered. It is
**circular for the measurement `R5-2` exists to take**: `jiffies` counts TC0
wraps, so over any interval longer than one tick the ratio of that counter to
the kernel's clock reduces to `14,286,057 / (100 × 142,858)` — two constants,
with the hardware cancelled out. It would also be blind to a lost tick, because
a lost tick moves both sides together.

**④ TC1 is idle on this unit.** 量 `SPEC.md` `REG-06`/`REG-08`/`REG-09`:
`TC1DATA = 0`, `TC1CNT = 0`, `TCCNR = 0xC0000000`, whose `TC1En` (bit 29) and
`TC1Mode` (bit 28) are both clear. `TCIR = 0x80000000` (`REG-10`), so `TC1IE`
is clear too, and `GIMR = 0x00008100` (`REG-01`) has `TC1_IE` clear at the
global controller as well.

**⑤ So: program TC1 with a power-of-two period.** The mask arithmetic becomes
exact, the counter is independent of `jiffies`, and the comparison in § 5 can
see a lost tick.

⚠️ **This is not a new idea in this repository and it is not presented as one.**
`docs/probe3-cells.md` § 8 already weighed *"writing `TC1DATA`/`TCCNR` to get an
18.79 s counter instead of a 10 ms one"*, called it *"strictly better as an
instrument"*, declined it because `probe3`'s windows all fitted inside 3 ms of
the 9.9998 ms wrap, and recorded it as **the upgrade path for `R5-0`**. This is
that path taken. What is new here is the power-of-two period and the guards.

---

## 2. The register facts, with two sources each

`CLAUDE.md`: *no register value enters code on one source.* Everything this
driver touches has the datasheet (**D**) and a reading on this die.

| | address | D | on this die |
|---|---|---|---|
| `TC0DATA` | `0xB8003100` | § 8.2.2 Table 20 — value in bits **31:4**, *"Counter values of 0 and 1 are not allowed"* | `SPEC.md` `REG-05`, `0x0022E0A0` = 142,858 << 4 |
| `TC1DATA` | `0xB8003104` | § 8.2.3 Table 21, same shape | `REG-06`, `0x00000000` |
| `TC0CNT` | `0xB8003108` | § 8.2.4 Table 22 — **R**, *"Count incremented by 1 from 0"* | `REG-07`, live (two reads differ) |
| `TC1CNT` | `0xB800310C` | § 8.2.5 Table 23 — **R** | `REG-08`, `0x00000000` |
| `TCCNR` | `0xB8003110` | § 8.2.6 Table 24 — 31 `TC0En`, 30 `TC0Mode`, 29 `TC1En`, 28 `TC1Mode`; **0 = counter (one-shot), 1 = timer (reload)** | `REG-09`, `0xC0000000` |
| `TCIR` | `0xB8003114` | § 8.2.7 Table 25 — 31 `TC0IE`, 30 `TC1IE`, 29 `TC0IP`, 28 `TC1IP`; both `IP` bits **write-1-to-clear** | `REG-10`, `0x80000000` |
| `CDBR` | `0xB8003118` | § 8.2.8 Table 26 — `DivFactor` in bits **31:16**; *"Base clock = System_clock (Peripheral Lexra Bus)/N"*; *"Both values 0x0000 and 0x0001 disable the clock"* | `REG-11`, `0x000E0000` → N = 14 |
| `GIMR` | `0xB8003000` | § 8.1.1 Table 14 — bit **8 `TC0_IE`**, bit **9 `TC1_IE`** | `REG-01`, `0x00008100` |
| `GISR` | `0xB8003004` | § 8.1.2 Table 15 — bit **8 `TC0_IP`**, bit **9 `TC1_IP`**, both **R** | `REG-02`, `0x88000004` |

🔴 **The bit names above were read from D today and none of them was in this
repository before.** `SPEC.md` carried the nine **values** and, for `GIMR`, one
field name. That is why `TCCNR = 0xC0000000` could sit on the record for ten
days without anybody being able to say whether TC1 was on: bit 30 is `TC0Mode`,
not `TC1En`, so the word means *TC0 enabled in timer mode, TC1 off* — and the
alternative reading, *both timers enabled*, is now excluded rather than merely
unlikely. The rows go into `SPEC.md` in the same commit as this file.

🟢 **And the pair that matters most is `GIMR`/`GISR` bit 9.** This repository
had *"bit 8 `TCIE` — Timer/Counter interrupt enable"* from two sources
(`docs/loader-phy-and-switch.md` § 2: **B** names it and **D** agrees), which is
correct and one bit too coarse. D Table 14/15 give the two timers **separate**
bits at the global controller. That single fact is what turns § 4's second
hazard from *"an interrupt storm nobody can rule out"* into *"a mask bit that
reads 0 and that the driver checks before it writes anything"*.

⚠️ **One inconsistency inside D itself, recorded rather than resolved**:
Table 26 gives the divider field as bits **31:16** and names it
`DivFactor[16:0]` — sixteen bit positions holding a seventeen-bit name. It does
not matter at `N = 14` and it is written down so the next reader does not have
to rediscover it.

⚠️ **A contradiction that was NOT one, recorded because the first reading of it
was wrong.** D Table 27's `OVSEL[1:0]` at bits 22:21 offers four settings, which
appears to contradict `SPEC.md` `CLK-07`'s *"`OVSEL[3:0]` … ten settings"* and
`CLK-08`'s measured `OVSEL=1001`. It does not: the field is **split**, and bits
18:17 are `OVSEL[3:2]`, *"Higher Overflow Select Bits"*, with the combined
`OVSEL[3:0]` running `0000: 2^15` … `1001: 2^24` — ten of them. `CLK-07` and
`CLK-08` are right and nothing there moves. **The lesson is about the
instrument**: a table read to its first page break looked exactly like a
contradiction.

---

## 3. The decisions, which is the layer `driver-diff` compares

`docs/blind-write-ledger.md` § 5 splits the comparison into **L1 fact**
(addresses, reset values, documented bit positions — agreement is guaranteed by
the parts being the same part) and **L2 decision**. § 2 above is L1. This
section is L2: every row is a choice, another implementation can have made it
differently, and each is decidable on the silicon.

| # | decision | what was chosen, and the alternative that was not |
|---|---|---|
| **L2-a** | **which timer** | TC1. TC0 is the vendor's tick. See § 1 |
| **L2-b** | **wrap handling** | Reprogram to a power of two rather than correct in software. `2^27` is the largest power of two the 28-bit `TC1Data` field holds: **134,217,728 counts = 9.39502 s**. The alternative — `CLK-17`'s `if (d < 0) d += 142858` on TC0 — is what `probe3` does and it needs a read faster than 10 ms |
| **L2-c** | **the off-by-one D does not settle** | D does not say whether the period is `TC1Data` counts or `TC1Data + 1`. The driver does not need to know: the two differ by one count in 134,217,728 = **0.0075 ppm**, four orders of magnitude below the ±50 ppm `D4` asks for. If the period is `2^27 + 1`, the raw value `2^27` appears once per wrap and masks to 0 — one count lost per wrap, and the counter never runs backwards |
| **L2-d** | **`mult`/`shift`** | `shift = 24`, `mult = clocksource_hz2mult(14286057, 24) = 1,174,376,947`, i.e. 69.99832 ns per count. 讀 `include/linux/clocksource.h`: `mult` must fit in `u32`, which holds up to `shift = 25` and fails at 26. 24 is chosen over 25 because NTP adjusts `mult` at run time by about ±11 % and 24 leaves the most headroom, while its own rounding error — one part in `2^24` of 69.998 ns = **0.00085 ppm** — is already negligible against the tolerance |
| **L2-e** | **rating** | **0**, and it is outside the band `clocksource.h` documents (1–99). 讀 `kernel/time/clocksource.c`: `clocksource_enqueue()` sorts by rating and `select_clocksource()` takes the list head, so the highest wins. `clocksource_jiffies` (讀 `kernel/time/jiffies.c`) is rating **1** and is always registered. Rating 1 here would tie and rely on `enqueue`'s `cs->rating >= c->rating` to break the tie in jiffies' favour — true today and an implementation detail. **0 needs no tie-break**, which is what makes `R5-2`'s *"zero risk"* a property rather than a hope |
| **L2-f** | **when the hardware is written** | **Never at boot.** Arming is a write of `arm` to `/proc/rtl819x-timer`; `disarm` puts `TCCNR` back and unregisters. See § 4 |
| **L2-g** | **which registers are written, and which are only read** | Written: `TC1DATA`, and `TCCNR` read-modify-write of bits 29/28 only; `TCIR` **once, on disarm**. Read and never written: `TC0DATA`, `TC0CNT`, `TC1CNT`, `CDBR`, `GIMR`, `GISR`. **`CDBR` is never written** — D § 8.2 says one divider feeds both timers *and the watchdog*, so writing it would move the vendor's tick and `CLK-08`'s watchdog together. **`GIMR` is never written** — unmasking TC1 would deliver an interrupt to a handler this driver does not install |
| **L2-h** | **accessor** | `__raw_readl`/`__raw_writel` through `CKSEG1ADDR`, not `readl`/`writel` and not `ioremap`. `readl` is defined to convert a little-endian device word to CPU order; this is a big-endian part with an on-chip register already in CPU order. `CONFIG_SWAP_IO_SPACE` is absent from this build so the two are identical *here* — the raw form is the one that stays right if it ever is not. `CKSEG1ADDR` is uncached and unmapped, so no `ioremap`, and the driver works from any initcall level |
| **L2-i** | **initcall level** | `arch_initcall` (level 3, confirmed in `System.map`: `__initcall_rtl819x_timer_init3`). After `core_initcall`, where jiffies registers; after `start_kernel`'s `time_init()`; and procfs already exists, because `proc_root_init()` runs from `vfs_caches_init()` before any initcall |
| **L2-j** | **the driver's own positive control** | `arm` reads `TC1CNT`, waits `udelay(100)`, reads again, and **refuses with `-ETIME` if the counter has not moved**. A clocksource that returns a constant stops time the moment anything selects it. `CLAUDE.md`: *a tool reporting 0 is making a claim* |

---

## 4. The two hazards, and why arming is a userspace act

**H1 — the read-modify-write of `TCCNR` could disturb TC0.** `TC0En` and
`TC1En` are bits of one word. If the write clears TC0 the system tick stops.
Bounded by: reading the word first and refusing with `-ENODEV` if `TC0En` is
already clear; setting only bits 29/28; reading the word **back** and, if TC0's
two bits moved, writing the saved value and refusing with `-EIO`. The
before/after words are both in the `/proc` dump, so *"TC0 undisturbed"* is a
comparison the reader makes rather than a claim the driver makes.

**H2 — `TC1IP` latches, and where it goes.** 🟢 **This is now bounded, and it
was bounded by reading the specification rather than anybody's driver.** D
Table 14/15: `GIMR` bit **9** is `TC1_IE` and `GISR` bit **9** is `TC1_IP` —
different bits from the bit 8 pair the vendor's tick uses. 量 `SPEC.md`
`REG-01`: `GIMR = 0x00008100`, so **bit 9 is clear** and a latched `TC1_IP`
cannot be delivered.

⚠️ **What that does not settle**: `REG-01` was read at the **loader prompt**,
and what Linux leaves in `GIMR` has never been read.

> 🔄 **2026-09-04: that last clause expired on 2026-09-03 and the
> segment that expired it did not notice.** Seating 11 read `GIMR` under
> Linux in all fourteen dumps: **`00209100`**, bit 9 clear. `R5-10` then
> decoded it bit for bit against `arch/rlx/bsp/bspchip.h` and the built
> `.config` — `TC0_IE \| UART0_IE \| SW_IE \| PCIE_IE`, with every absent
> OR-in's symbol absent (`SPEC.md` `REG-01`, `docs/interrupt-map.md` § 4.1).
> The `-EPERM` refusal is unchanged and is still the right design; what
> changed is that the value it guards against is now known.
> 🔴 And § 9 is what to read about H2 itself: the pending bit did not
> latch because **`TCIR` bit 30 was clear too**, not because of this mask. 量 2026-09-03, by sweep:
every `GIMR` reading in this repository — `RUNSHEET` `E3`, `C5`, `E5`,
`bench/2026-08-23/E.log` and `C5-picocom.log` — is at the prompt, and no
capture holds a `DW B8003000` taken after a `J`. So the driver does not
assume it. It **reads `GIMR` and refuses to arm with `-EPERM` while bit 9 is
set**, and it prints `GIMR`/`GISR` whole plus the four bits by name, so § 5's
cells confirm the mask before the write instead of after it.

🔴 **Arming is still a userspace act, and H2 being narrower does not change
that.** The remaining unknowns — whether Linux unmasks bit 9, whether the
`"Mitigation&Timer1"` block D's Table 24/25 both mention has claimed TC1, what
the vendor's timer code does to `TCCNR` — are all things a boot-time arm would
put in front of the boot, where a failure costs the whole power cycle. Arming
from a shell puts them after a boot that has already succeeded, where the
failure is observed, attributable, reversible with `disarm`, and costs only the
rest of the seating.

⚠️ **The cost of that choice**: this is not yet a driver in the sense `R5-3`
needs, because a clockevent must be armed at boot. `R5-2`'s reading is what
makes the boot-time path safe to write, and that is the intended order rather
than a deferral.

⚠️ **One more property, recorded because it is a footgun and also a tool.**
讀 `kernel/time/clocksource.c`: `clocksource_enqueue()` sets
`clocksource_override = c` when the registering clocksource's name equals
`override_name`. So writing `rtl819x-tc1` into
`/sys/devices/system/clocksource/clocksource0/current_clocksource` **before**
arming would make the rating irrelevant and select it the moment it registers.
`R5-2`'s card must not do that; `R5-3` may want to.

### 4.1 The five refusals, each of which is a reading

| errno | state | what it means if it fires |
|---|---|---|
| `-EBUSY` | `TC1En` already set, or already armed | something else owns TC1. D's own *"Mitigation&Timer1"* note says the SoC has such a user |
| `-ENODEV` | `TC0En` clear | the system tick is not coming from this block, so § 5.1's arithmetic does not hold. `E1`'s register dump is still a reading; `E7`/`E8` are not |
| `-EPERM` | `GIMR` bit 9 set | Linux unmasked TC1's interrupt. A finding about the vendor's setup, obtained without reading it |
| `-EIO` | TC0's two bits moved across the write | `H1` fired; the saved word is written back before the error returns |
| `-ETIME` | `TC1CNT` did not move in 100 µs | the counter is not running, and registering it would be registering a constant |

---

## 5. The reading `R5-2` takes, with its refutation conditions written first

**Prerequisite** — none of this needs a power cycle of its own. It rides the
next seating's boot, and the whole block is `cat` and one `echo`.

🔴 **And it goes LAST on that seating's card. This is the decision, and the
reason is that it converts the failure's cost to zero.**

The arm's worst case is not a brick and not a flash byte: it is the board
wedging *after* a shell that has already been reached, which costs **the
remainder of the seating**. That quantity is under the card's control. Put the
timer block after `SEAM-1`'s `--mode bench` run, after `GR-1`, and after
whatever `CPU-45` work the seating carries, and the remainder is empty — a
wedge then costs the reset that ends the seating anyway.

⚠️ **The alternative that was rejected, and why.** Stopping after `E6` — arm,
wait one period, read `TCIR`, disarm, and skip the 60-second comparison —
saves 60 s of board time and **buys no safety at all**: by the time `E6` has
returned, every register this driver writes has been written and every hazard
has either fired or not. `E7`/`E8` are `cat`s. **A precaution that costs
information and removes no risk is not a precaution.**

⚠️ **The other alternative — read-only, no arm — fails the step.** `R5-2`'s
`D4` is a frequency within ±50 ppm; `E1`–`E3` cannot produce a frequency. It
would leave `R5-3` with nothing new to be safe on.

### 5.1 The arithmetic, before any measurement

Let `B` be the true rate of the timer block's base clock. Then:

* the tick rate is `B / 142858` (TC0's period), one jiffy each;
* the kernel calls one jiffy exactly `1/HZ = 10 ms`, so it reports elapsed
  seconds `= B·t / (100 × 142858) = B·t / 14,285,800`;
* this driver reports `B·t / 14,286,057`, using `CLK-17`.

`B` cancels. So **if the kernel's time base is `clocksource_jiffies`**, the
kernel's elapsed time exceeds this driver's by

```
14,286,057 / 14,285,800  -  1  =  +17.99 ppm
```

and that number is a property of two measured constants, not of the crystal.

#### 5.1.1 🔴 The middle bullet is an assumption, it is not obvious in this tree, and it was checked

*"The kernel calls one jiffy exactly 10 ms"* is not what the code says. 讀
`kernel/time/jiffies.c:37` — `NSEC_PER_JIFFY` is `((u64)NSEC_PER_SEC << 8) /
ACTHZ` — and 讀 `include/linux/jiffies.h:43,54,58`, where **`ACTHZ`** comes from
**`LATCH`** through **`SH_DIV`**, and `LATCH` from **`CLOCK_TICK_RATE`**. So the
chain ends at an **arch constant, not at `HZ`**.

🔴 **`arch/rlx/include/asm/timex.h:21` sets it to `1193182`, which is the
i8253 PIT frequency of an IBM PC.** 讀 for the value; **推** for what it means
here — that it describes nothing on this part and was carried along when the
port was made. What would refute the 推 is a clock on this SoC at 1.193182 MHz,
and no reading in `SPEC.md` § 10 is within 1 % of it.

量, replicating `SH_DIV` in integer arithmetic exactly as the header does:

| `CONFIG_HZ` | `LATCH` | `ACTHZ` | implied Hz | `NSEC_PER_JIFFY` | vs `1e9/HZ` |
|---:|---:|---:|---:|---:|---:|
| 48 | 24,858 | 12,288 | 48.000000 | 20,833,333 | **0 ppm** |
| **100** | **11,932** | **25,600** | **100.000000** | **10,000,000** | **0 ppm** ← this build |
| 128 | 9,322 | 32,767 | 127.996094 | 7,812,738 | +30.5 ppm |
| 250 | 4,773 | 63,996 | 249.984375 | 4,000,250 | **+62.5 ppm** |
| 256 | 4,661 | 65,534 | 255.992188 | 3,906,369 | +30.5 ppm |
| 1000 | 1,193 | 256,039 | 1000.152344 | 999,847 | **−153.0 ppm** |
| 1024 | 1,165 | 262,193 | 1024.191406 | 976,379 | −187.4 ppm |

🟢 **So the assumption holds for this build: `NSEC_PER_JIFFY` is 10,000,000
exactly, and § 5.1's arithmetic stands.**

🔴 **And it holds by luck.** At `HZ=250` this port's kernel would believe a
jiffy is **62.5 ppm** longer than it is, and at `HZ=1000` **153 ppm** shorter —
both from a PC timer chip's frequency, and both larger than the ±50 ppm this
gate's `D4` asks for. **Anyone who changes `CONFIG_HZ` here moves the kernel's
idea of time before touching any hardware**, and `R5-3` is the step that makes
that matter, because it is where this driver becomes the time base.

⚠️ **This is not a defect in `arch/rlx` alone** — mainline MIPS carried the
same constant for years — and it is not a thing to fix in this gate. It is
recorded because `R5-2` subtracts two numbers 18 ppm apart and one of them
comes from here.

### 5.2 The cells

| | command | prediction | refuted by |
|---|---|---|---|
| **E1** | `cat /proc/rtl819x-timer` at a shell, before arming | `state=idle`, `tccnr=C0000000`, `tcir=80000000`, `cdbr=000E0000`, `tc0data=0022E0A0`, `tc0_undisturbed=1`, `mult=1174376947`, `hz_assumed=14286057` | any of those words differing from `SPEC.md` `REG-05`…`REG-11` — which would mean Linux leaves the block in a different state from the loader, and that is a finding about `rlx-time.c` obtained **without reading it** |
| **E2** | the same output, interrupt half | `gimr_tc1ie=0` and `gisr_tc1ip=0` | 🔴 **`gimr_tc1ie=1` is a STOP**: do not arm. It means Linux unmasked TC1 and the driver will refuse anyway with `-EPERM`. Either way the seating's timer work ends here and the finding is the reading |
| **E3** | `cat /sys/devices/system/clocksource/clocksource0/available_clocksource` and `…/current_clocksource` | `rtl819x-tc1` **absent** from `available` | its presence before `arm` — the driver registered something it was not asked to |
| **E4** | `echo arm > /proc/rtl819x-timer; echo $?` | `0`, then `arm_delta_100us` between **1300 and 1600** (100 µs × 14,286,057 = 1,428.6 counts, widened for `udelay`'s calibration error and two uncached register reads) | any of the five errnos in § 4.1. **Each is a result, and none of them is a driver bug until the register dump says otherwise** |
| **E5** | `cat …/available_clocksource` and `…/current_clocksource` again | `rtl819x-tc1` now **in `available`** and **not** `current` | `current_clocksource` reading `rtl819x-tc1` refutes `L2-e`: rating 0 did not keep it out and § 3's enqueue analysis is wrong |
| **E6** | wait ≥ 10 s (one period is 9.395 s), `cat /proc/rtl819x-timer` | the board still answers; `gisr_tc1ip` and `tcir_tc1ip` are each 0 or 1 | the board hanging here is `H2` firing **through a path this design says is masked**, and it would refute § 4's whole argument. `tcir_tc1ip=1` with `gisr_tc1ip=1` and the board alive is the useful outcome: the flags latch, `GIMR` masks them, and `R5-3` knows exactly which bit it has to own |
| **E7** | two `cat`s about **60 s** apart, with the host's clock on both captures | `Δtc1_ext / Δwall` within **±50 ppm** of 14,286,057 Hz; `tc1_ext_trusted=1`; `tc1_ext_gap_max` a few million counts for a sub-second turnaround, far below the `2^26` threshold the flag uses | outside ±50 ppm → either TC1 does not divide the same `CDBR` as TC0 (§ 2's one 讀-only assumption about this driver's rate), or `CLK-17` is wrong. The host clock is the same instrument `CLK-04` was measured with — `.log` mtimes — and its own error is the ±7 ppm already inside `CLK-02` |
| **E8** | the same two samples, kernel side | `(Δwall_kernel / Δtc1_seconds) − 1` = **+17.99 ppm ± the sampling noise** | three named alternatives, below |
| **E9** | `echo disarm > /proc/rtl819x-timer`, then `cat` | `0`; `tccnr` back to `C0000000`; `rtl819x-tc1` gone from `available_clocksource` | `tccnr` not returning to its `at_init` value — the driver cannot undo its own write, and that is worth knowing before `R5-3` |

### 5.2.1 🔴 **2026-09-03, writing `R5-2`'s card: two rows of that table are wrong, and both were found by putting this note's own constants back through this note's own model**

**The rows above are kept as written.** What follows replaces `E7`'s and `E8`'s
*method*; neither cell's question moves, and `bench/2026-09-03/PREDICTIONS-B9-block8.md`
is the card that carries the corrected form.

**① `E7` may not quote `tc1_ext` at a 30 s or 60 s spacing — and
`tc1_ext_trusted` reports `1` on exactly the gaps where it is wrong.**
`rtl819x_ext_advance()` recovers `d = (now − last) & MASK`, which is the true
gap only while the gap is under one period (**134,217,728 counts = 9.395016 s**).
`tc1_ext_trusted` is `gap < (MASK >> 1)` = **4.697508 s**. 量:

| gap | true counts | wraps | the `d` computed | `trusted` |
|---:|---:|---:|---:|---:|
| 4.0 s | 57,144,228 | 0 | 57,144,228 | 1 — correct |
| 9.0 s | 128,574,513 | 0 | 128,574,513 | **0** — correct refusal |
| **30.0 s** | 428,581,710 | **3** | **25,928,526** | 🔴 **1 — FALSE** |
| **60.0 s** | 857,163,420 | **6** | **51,857,052** | 🔴 **1 — FALSE** |

Past one period the residue **aliases back into the trusted band**, so the flag
is not merely uninformative there — it asserts trust over data that has lost
whole wraps. `E7` as written asked for `tc1_ext_trusted=1` *and* for
`tc1_ext_gap_max` to be *"a few million counts for a sub-second turnaround"*,
and those two sentences cannot both describe a 60-second cell.
**The card quotes `tc1_cycles` and recovers the wrap count outside the kernel
from `jiffies`**, which § 5.4's last stop-if already sanctioned as the fallback;
what changed is that it is now the planned route. The driver-side fix — refuse
when `Δjiffies × TICK_NSEC` implies more than one period — belongs to `R5-3`,
because `config/` is frozen for the staged image (§ 6.2).

**② `E8` could not have resolved its own headline.** `CONFIG_GENERIC_TIME=y`
and `clocksource_jiffies` selected means `getnstimeofday()` changes only when
`jiffies` does, so **`wall` advances on a 10 ms grid** whatever its nine printed
decimals suggest. 量, a 10 ms endpoint error as ppm: **333.3** at 30 s,
**166.7** at 60 s, 16.7 at 600 s, 5.6 at 1800 s. The signal is **17.99 ppm**, so
at 60 s the grid is **nine times** the thing being measured, and § 5.3's three
branches are not three outcomes of one cell — they need three different
baselines. 🟢 **§ 5.3's second bullet is the one that survives at 60 s**: one
lost tick is 167 ppm, which *is* the grid, so a 60 s pair is a one-lost-tick
detector at the edge of its resolution and is not an 18 ppm measurement.

🟢 **The grid is removable and the remover was already being printed.**
`TC0CNT` is the tick's own phase, so

```
TC0_total = jiffies × 142858 + (tc0cnt >> 4)
```

is a continuous 14.29 MHz reference — **one count is 0.0012 ppm over 60 s** —
and `ΔTC1 / ΔTC0_total = 1` becomes the measurement. `+17.99 ppm` is then an
arithmetic consequence of `14286057 / (100 × 142858)`, not a quantity to chase
with a stopwatch.

🔴 **2026-09-03, seating 11: the two constants in the paragraph above are the
LOADER's, and Linux does not use them.** 量, `TM-1`: `CDBR` reads `03E80000`
(divisor **1000**, not 14) and `TC0DATA` reads `00007D00` (**2,000** ≪ 4, not
142,858 ≪ 4). Both give 100 Hz; the vendor's ~~`rlx-time.c`~~ **`arch/rlx/bsp/timer.c`** (🔄 2026-09-04, § 9.6) reprograms the
divider at boot. So the reference is a continuous **200.005 kHz** counter and
one count is **0.083 ppm over 60 s** — still 2,000× finer than the ±50 ppm the
step asks for, and 2,008× finer than the 10 ms grid this section exists to
remove, so the *method* survives unchanged and only its numbers move. The
`+17.99 ppm` figure is void: it was `14286057 / (100 × 142858) − 1`, and both
of those constants belonged to the loader.
`bench/2026-09-03/CORRECTIONS-block8.md` § 1.

⚠️ **The `>> 4` is 量 and this line used to say it was not.** *(It read: "the
`>> 4` is the driver's reading of D Table 22 and not the datasheet's words; the
card's `Q3` tests it, and it is the only test of that shift this project has".)*
Both halves were already false when written — `REG-05`'s `0x0022E0A0`,
`REG-07`'s low nibble and `probe3`'s Group T all carry the shift, at the loader
prompt or from bare metal — and seating 11 settled it on a third route:
`ΔTC1 = Δjiffies × (tc0data ≫ 4) + Δ(tc0cnt ≫ 4)` held with **residual exactly
zero** over three intervals, the longest 140,693,532 counts. An integer-exact
identity over 1.4 × 10⁸ counts is not a shift being assumed.

### 5.3 🔴 `E8` is the cell with the most information in it

🔄 **Read with § 5.2.1 ②: the first bullet below was answered at the desk on
2026-09-03 and the second is the one a 60 s baseline can see.**

The three ways it can come out other than `+18 ppm`, each with its own meaning:

* **≈ 0 ppm** → the kernel's time base is **not** `clocksource_jiffies`.
  Something registered a real clocksource, and `E5`'s `current_clocksource`
  names it. **That is the vendor's timer answering a question about itself
  without this project reading its source**, and it is the single most
  valuable byproduct of the cell.

  > 🔴 **2026-09-03: this branch is EXCLUDED at the desk, and the value the
  > sentence above claims for it is therefore spent.** § 6.4: exactly two
  > `struct clocksource`s exist in the linked image and neither is the
  > vendor's. The bench can now only *refute* the desk scan here, which is a
  > smaller thing than discovering the vendor's clocksource would have been.
  > **The trade is recorded rather than presented as a gain**: what was bought
  > is that `E8` stops being a three-way branch and becomes a prediction with a
  > refutation condition, and that a wrong headline was found before a power
  > cycle was spent on it. `docs/blind-write-ledger.md` § 4.3 carries the cost
  > on the ledger side.
* **below +18 ppm** → **ticks are being lost.** One lost tick in a 60 s window
  is 10 ms / 60 s = **167 ppm**, nine times the whole signal, so this is a very
  sensitive lost-tick detector and it has never been pointed at this board.
* **above +18 ppm** → **ticks are being gained.** One spurious tick per TC1
  period is 10 ms / 9.395 s = **1,064 ppm**.

⚠️ **What `E8` is not**: it is not an independent measurement of the crystal.
`E7` is. `E8` compares two derivations that share `B`, so it tests the *model*
— TC0's period, `HZ`, no lost ticks, both timers on one divider — and not the
oscillator.

### 5.4 The stop-ifs

* **`E2` reading `gimr_tc1ie=1`**: do not arm. Everything else on the card runs.
* `E4` returning `-EIO`, or `tc0_undisturbed=0` at any point: **disarm and stop
  the timer block entirely for that seating.**
* The board not answering after `arm`: that is `H2` through an unmodelled path,
  the seating's timer work ends, and the finding is written before the next
  power cycle is spent.
* `tc1_ext_trusted=0`: `tc1_ext` is not quoted. `tc1_cycles` and the wall clock
  are still a reading, with the unwrapping done outside the kernel.

---

## 6. What was measured today

All 量 on this host, 2026-09-03, one build at a time, `-j4`.

⚠️ **Re-derived at the end of the session rather than quoted as first taken.**
The driver was edited twice after the first round of builds — `scnprintf`
with a page bound, and the `GIMR` read — so `r51loud`, the `vmlinux`
`hazlint` run and `rlxfw-marks verify` were all re-run against the source
that is committed. **Two of the three numbers moved**, and the ones that
moved are marked. The driver's own sha256 is
`e08a7838bb16743869a6d40563c9738ce3a83ff4ffeac38d7b9712a30d33e996`.

| | | |
|---|---|---|
| fresh stage + build, vendor board template, `--marks` | **593 `CC`**, 46.5 s | 592 + 1, and the 592 is `INC-1`'s `S0` on the same recipe |
| fresh stage + build, rlxfw's own config, quiet variant | **596 `CC`**, 42.1 s, `vmlinux` 3,969,432 bytes | `.config` from `kconfig-delta.py apply --variant quiet`; the initramfs spec was regenerated and is **byte-identical** to the one the 2026-09-02 image used (`f1cee4484bc3da30`) |
| the same, loud variant | **597 `CC`**, **4,076,348 bytes** | `CONFIG_PRINTK=y`; the driver has no `printk` call and compiles either way. 🔄 **Rebuilt and re-derived after the last two edits to the driver** — the first loud build read 4,076,311, on a source that no longer exists. Not re-timed, so no seconds are quoted for it |
| **the control: the same config and spec with the driver and `MK2` removed** | **595 `CC`**, 3,968,635 bytes | restored by the script's own `trap`, and `git status` confirmed it |
| compiler diagnostics on this file | **0** | under `-Wall -Wstrict-prototypes -Wdeclaration-after-statement -Wundef -Werror-implicit-function-declaration -Os -fno-if-conversion`. Every warning in the 1,023-line build log is a vendor file |
| `hazlint` on `drivers/clocksource/rtl819x-timer.o` | **0 violations in 100 loads**, 15 followed by an explicit `nop`, 0 unresolved, 3,156 bytes scanned | and the controls that could have said otherwise held: `K2` fired its two known violations, `K4` reproduced `stage2.bin`'s 1,474/646/0, `K4b` the vendor kernel's 128,440/40,182/58 |
| `hazlint` on the linked `vmlinux` | **0 violations in 110,241 loads** | on `r51quiet` — the image `R5-2` would boot — re-run after the last edits. 8 `notes`, all of them section-head statements in `.text`/`.iram`, none in this file. *(The first run read 109,694 and was on `r51a`, the board-template build; a different `.config` is a different population and the two numbers are not a change in anything.)* |
| `rlxfw-marks verify` | **12/12 present once, 0 in both vendor artefacts** | `--absent` this unit's own decompressed kernel (3,374,772 B) and the drop's `vmlinux_img` (2,953,660 B) |

### 6.1 🔴 The obvious size number is the wrong one, and the right one is five times bigger

The `vmlinux` ELF grew **797 bytes** (3,968,635 → 3,969,432) and **that is not
what the driver costs.** 讀 `objdump -h` on both: section file offsets in this
link are page-aligned and `.text` has about 73 KiB of slack before `.rodata`'s
fixed start, so growth inside `.text` costs the *file* nothing until a boundary
rolls over.

The loadable content:

| section | base | with driver | Δ |
|---|---:|---:|---:|
| `.text` | 2,449,212 | 2,452,156 | **+2,944** |
| `.rodata` | 109,472 | 110,144 | **+672** |
| `.data` | 119,712 | 119,840 | **+128** |
| `.init.text` | 88,312 | 88,524 | **+212** |
| `.initcall.init` | 576 | 580 | **+4** |
| `.bss` | 2,708,096 | 2,708,160 | **+64** |

**3,960 bytes of loadable content plus 64 of BSS**, against 797 for the file.
The object itself is 8,524 bytes, of which `hazlint` scanned 3,156 as
instructions.

🔴 **And one row of the section table is padding pretending to be content.**
`size -A` reports `__param` growing from 1,076 to 4,500 bytes — 3,424 bytes,
for a driver that declares no module parameter. 量:
`__start___param … __stop___param` is **700 bytes in both**. The section's
`sh_size` runs to the next 4 KiB boundary, and `.rodata`'s growth pushed those
700 real bytes across `0x28b000`, so the pad went to `0x28c000`. **That row
carries no information about this driver at all**, and it is written down
because a reader diffing two `size -A` outputs would otherwise report it.

### 6.2 The image `R5-2` uploads, staged and pinned

`config/` was frozen and `tools/rtkimage.py build` run against the `r51quiet`
tree. **`rlxfw-r51-20260903.bin`, 1,030,144 bytes, sha256
`39abf11c2d6fd0ce2c9dc40f1ba07ad803c2caa82043d4826f6ccb948261bbf9`**, in
`$FWRE_WORK/rebuild/bench-only/r51-20260903/`. `RECIPE_ID` is **`229d2983`**,
which is what the board must print as `RLXFW-ID0=229D2983`.

🔴 **`rtl819x-tc1` occurs ZERO times in that file, and the reason is not the
driver.** The uploadable `nfjrom` carries the kernel **compressed**
(`vmlinux_img` 3,472,384 → `vmlinux_img.gz` 1,018,668), so no string from the
kernel survives a byte search of it. **The control is in the same command**:
`RLXFW-ID0=`, which `rlxfw-marks verify` has just confirmed is present exactly
once in the ELF, also reads **0** in `nfjrom`. In the uncompressed
`vmlinux_img` both read **1**.

⚠️ This is `RUNSHEET` `P10`'s own correction arriving a second time: it
recorded on 2026-08-29 that `--absent r0-vendor-kernel.bin` carried no
information because that file is compressed, so *"a `RLXFW` count over it is 0
for every image including my own"*. **A zero from a compressed artefact is a
statement about compression.**

### 6.3 The negative controls, and one of them is dated

* `rtl819x-tc1` occurs **once** in `r51quiet`'s `vmlinux` and **zero** times in
  `i3` and `r44a` — the two images built on 2026-09-02, *before this file
  existed*. A control that predates the change is stronger than one rebuilt
  beside it.
* The same string is **absent** from the control build made today with the
  driver removed.
* `System.map` carries `rtl819x_tc1_read`, `rtl819x_tc_read_proc`,
  `rtl819x_tc_write_proc`, `rtl819x_tc1_clocksource`, `rtl819x_timer_init` and
  `__initcall_rtl819x_timer_init3` — the last of which is the initcall level,
  read out of the artefact rather than assumed from the source.

### 6.4 🆕 **2026-09-03, later the same day (twenty-ninth segment, `R5-2`'s card): the clocksource census, and the control that caught the scanner**

量 on the `vmlinux` `rlxfw-r51-20260903.bin` was cut from, sha256-16
`2b0d1618d9946cc6`. No vendor binary was executed and no vendor source was
opened: the ELF's single `PT_LOAD` is read straight out of the file and MIPS-I
instruction encodings are matched as 32-bit big-endian words.

**Exactly two `struct clocksource`s are registered in this image, and neither is
the vendor's:**

| route | result |
|---|---|
| direct transfers to `clocksource_register` (`T` @ `80035700`) | **2** — `j` from `init_jiffies_clocksource+0x4` (a tail call) and `jal` from `rtl819x_tc_write_proc+0x27c` |
| `lui`/`addiu` and `lui`/`ori` pairs materialising its address | **0** — nothing can reach it with `jalr` |
| `.config` | `# CONFIG_MODULES is not set` — nothing registers one later |

🔴 **The first version of the scan counted `jal` only, found 1, and its designed
positive control did not fire.** `init_jiffies_clocksource` provably calls
`clocksource_register` — generic Linux — so the scanner had to be wrong, and it
was: `return clocksource_register(&clocksource_jiffies);` is a **tail call** and
gcc emits `j`. `panic` (45) and `schedule` (72) fired throughout, which is what
made *the control* the suspect rather than the tool.

🔴 **And the indirect scan's first three controls were all silent for a second
reason**: `panic`, `do_timer` and `clocksource_get_next` simply never have their
addresses taken, so *that* scan could not fail either. Replaced with three that
must fire by construction — `rtl819x_tc_read_proc` (2),
`rtl819x_tc_write_proc` (1) and `rtl819x_tc1_clocksource` (3), all stored into a
`proc_dir_entry` or read at run time by my own code. Two negative controls (an
address two bytes off a real one; four bytes into a function) both **0**.

⚠️ **What it cost.** It is a reading of the vendor's compiled code and it goes in
`docs/blind-write-ledger.md` § 4.3 as one. 🟢 **The order limits the damage**:
the driver was written, built, linked and pinned into the staged image *before*
this scan ran, so nothing in it can have been shaped by the result. And it is an
**absence** — `arch/rlx/kernel/rlx-time.c` still has zero citations. 🔄 **2026-09-04: no longer.** `R5-10` opened it, and `docs/blind-write-ledger.md` § 4.3's row moves from *none — nothing taken* to **line**. The sentence above is kept because the scan it describes was run before that, and its value is entirely in its date.

⚠️ **What it does not say.** It says nothing about *how* the vendor keeps time.
`clocksource_jiffies` being the only registered source means the kernel's
**time-of-day** is derived from the tick — not that the tick *is* everything;
`arch/rlx` still owns the clockevent that produces it, and this scan says
nothing about that half. It is a fact about registration, not about
`rlx-time.c`'s contents.

---

## 7. 🔴 What this step did not establish

1. ~~**Nothing here has executed.**~~ 🟢 **Stopped being true 2026-09-03 at
   21:20** — the driver ran on the silicon, registered a clocksource, armed
   TC1, was read fourteen times and disarmed twice. § 8 is the reading.
   *(This item read: "Every statement about behaviour in § 5 is a prediction.
   The driver has been compiled, linked, scanned and found in the image; it has
   not run.")* **What it correctly warned about did not survive contact**: two
   of § 5's constants were the loader's and Linux does not use them (§ 5.2.1's
   red block), and § 4's masked-observation safety strategy turns out not to
   work on this part (§ 8.4).
2. **`rlxfw-marks verify` does not cover this driver.** It reads *mark* rows,
   and `MK2` is a build row with no string of its own. A whole file of mine can
   now reach the image and `verify` is silent about it — the gap is real, it is
   `MARK-1` in `PROGRESS.md`, and today it was covered by hand with the string
   count and the dated negative control above.
3. **`hazlint-objs` cannot see this object.** Its sweep is `arch/rlx` and this
   driver is under `drivers/`. `P2` would report 0 over a population that
   excludes it — and, if the remaining five land where the step list puts
   them, excludes those too. That second half is a forward claim about files
   that do not exist yet. `hazlint` was run directly here; the
   sweep is `HAZ-1` in `PROGRESS.md`.
4. **The 642 lines are about twice the step list's estimate of ~300.** The code
   is ~309; the rest is comment, and the comment is where the reasons live. The
   estimate is not renegotiated on one sample — `PROGRESS.md`'s stop-loss says
   that happens if the first driver takes more than six segments.
5. **`H2` is bounded, not closed.** § 4. `GIMR` bit 9 is clear *at the loader
   prompt*; what Linux does with it is `E2`.
6. **The `/proc` interface is not upstream shape.** `create_proc_entry` with
   `read_proc`/`write_proc` is the 2.6.30 idiom for a small file and it is the
   short one; a driver submitted upstream would use `proc_create` and
   `seq_file`. This half of the file is an **instrument**, not a driver, and it
   would not be submitted. `D1`'s *"accepted upstream-style"* is claimed for the
   clocksource half only.
7. **No `.dts` node and no `bindings/*.yaml` yet.** `D2` asks for one per
   driver, compile-tested and marked *not probed on hardware*. It is not here
   because the binding's `reg` should name what the driver actually claims, and
   `R5-2` may still move that — the driver reads two blocks (`0xB8003100` and
   `0xB8003000`) and writes inside one of them.

---

## 8. 🆕 `R5-2`, seating 11 (2026-09-03): the driver on the silicon

One power cycle, 21:15 → 21:55. Fourteen captures under `bench/2026-09-03/`,
ten of them the frozen card's `TM-1`…`TM-8`. Zero flash-write commands, zero
`FLR`; the bracket is untouched at 1,024 of 4,194,304 = 0.0244 %. The full
cell-by-cell verdict, the deviations and the corrections to the card are in
`bench/2026-09-03/CORRECTIONS-block8.md`; this section holds what the driver
itself learned.

### 8.1 🔴 Linux does not run this timer block at the rate the loader left it at

量, `TM-1`, the first reading of these registers under a kernel rather than at
the loader prompt:

| | loader (`REG-05`/`REG-11`) | under Linux |
|---|---|---|
| `CDBR` | `0x000E0000` — divisor 14 | 🔴 **`0x03E80000` — divisor 1000** |
| `TC0DATA` | `0x0022E0A0` = 142,858 ≪ 4 | 🔴 **`0x00007D00` = 2,000 ≪ 4** |
| `TCCNR` `TCIR` `TC1DATA` | `C0000000` `80000000` `00000000` | identical |

```
loader :  200.0049 MHz / 14   = 14,286,057 Hz ;  / 142,858 = 100.0 Hz
Linux  :  200.0049 MHz / 1000 =    200,005 Hz ;  /   2,000 = 100.0 Hz
```

**Two different divider/reload pairs, the same 100 Hz tick.** `cdbr_at_init` and
`tc0data_at_init` already hold the Linux values, so the reprogramming happened
before `rtl819x_timer_init` ran: it is ~~`arch/rlx/kernel/rlx-time.c`~~ **`arch/rlx/bsp/timer.c`**'s (🔄 2026-09-04, § 9.6), not this
driver's. 🟢 **A fact about a vendor file this project has still never opened**,
which is what the cell was written to buy — and it turned out to be a *change*
rather than the match the card predicted.

⚠️ **The driver's `hz_assumed` is therefore wrong by 71.43×** and prints
`14286057` in every dump. It is not used in any arithmetic this project quotes
— every result below is a ratio — but `R5-3` must derive it from `CDBR` and
`TC0DATA` at init rather than compiling it in.

### 8.2 🟢 The measurement: ΔTC1 / ΔTC0_total = 1, residual exactly zero, three intervals

```
interval           Δjiffies   ΔTC0_total          ΔTC1     residual
TM-6 d1 → d2          3,003    6,007,208     6,007,208         0
TM-6 d2 → d3          3,004    6,007,994     6,007,994         0
TM-5b-arm → TM-5b2   70,346  140,693,532   140,693,532         0
```

with `ΔTC0_total = Δjiffies × (tc0data >> 4) + Δ(tc0cnt >> 4)`. The third
interval is 703.46 s and **crosses one 2^27 wrap**, so the wrap-recovery
arithmetic is exercised (`n_wraps = 1`) rather than only asserted at zero.

Both counters are sampled inside one `spin_lock_irqsave` (`:471-489`), so the
match is between two hardware registers at one instant. It establishes in a
single reading: TC1 and TC0 divide the same `CDBR`; `TC0CNT` is
value-in-bits-31:4; `TC0DATA >> 4` is the reload; and the vendor's tick loses no
jiffies over 140.7 M counts.

⚠️ **A ratio, not a frequency.** `wall` derives from `jiffies`, `jiffies` from
TC0, TC0 shares the divider with TC1. What is 量 is *TC1 advances exactly 2,000
counts per jiffy*. **200.005 kHz stays 推**, from `CLK-02` ÷ 1000. The only
independent time base on hand — the host `.timing` — disagreed with itself by
17× its own resolution floor between two identical 30 s intervals
(`CORRECTIONS-block8.md` § 4.1), so it bounds the absolute rate and does not
measure it.

### 8.3 🟢 Registration, coexistence and teardown all behaved

* `TM-2a`/`TM-2b` before arming: **`jiffies`** and nothing else — § 6.4's desk
  clocksource census confirmed on the device.
* `TM-3`: `state=armed`, `last_verdict=0`, `tccnr` `C0000000` → **`F0000000`**,
  i.e. exactly bits 29/28 added, and `tccnr_after_arm` agrees.
  `TC1DATA` reads `0x80000000` = 2^27 << 4 — **so `TCnDATA` is
  value-in-bits-31:4 for TC1 as well**, a register this project had never
  written before.
* `TM-4a`: **`jiffies rtl819x-tc1`** — the driver registered.
  `TM-4b`: **`jiffies`** — rating 0 kept it out, so `L2-e`'s enqueue analysis
  holds and the comparison was never contaminated by the kernel switching to
  the source under test.
* `TM-7` and `TM-5c`: `tccnr` returns to `tccnr_at_init` = `C0000000`, twice —
  the second after a **703-second** arm. **The driver can undo its own write.**
* `TM-8` and `TM-5d`: `rtl819x-tc1` gone from `available_clocksource`, twice —
  `clocksource_unregister` takes.
* `tc0_undisturbed=1` in every one of the fourteen dumps.

### 8.4 🔴 The finding that changes `R5-3`: TC1IP does not latch while TC1IE is clear

§ 4 of this note builds the driver's safety argument on being able to watch
`TCIR`'s pending bit with `GIMR` bit 9 masked. 量, and the reading is
decisive because it has the control the first attempt lacked:

```
armed   wall = 1010.48   tc1_cycles =     1,861
read    wall = 1713.94   tc1_cycles = 6,477,665   <- below its own prior 31.99 M
delta = 703.46 s = 140,693,532 counts = one full 2^27 period plus 6.48 M
tcir_tc1ip = 0    gisr_tc1ip = 0    gimr_tc1ie = 0 throughout
```

`tc1_cycles` reading 6.48 M **is** the proof the period elapsed — without it a
zero is ambiguous, which is why the card's own `TM-5` (`sleep 10`, 1.5 % of a
period at the corrected rate) could not answer this.

🔴 **So the masked-observation strategy does not work on this part.** `R5-3`
cannot verify the interrupt path by watching a latch first and arming second;
it must set `GIMR.TC1IE` with a handler already installed. There is no
intermediate step, and the driver was designed as though there were.

> 🔴 **CORRECTED 2026-09-04, § 9 — the observation stands, the cause named
> above does not, and this paragraph's conclusion is withdrawn.** Two enables
> were clear at once (`TCIR` bit 30 and `GIMR` bit 9) and the reading cannot
> separate them; `RUNSHEET` `C5` (量 2026-08-24) shows a `GISR` pending bit
> latching **while masked in `GIMR`** on this die, which argues the cause is
> `TCIR.TC1IE = 0` — a bit `rtl819x_tc1_arm()` never writes. The paragraph is
> kept verbatim because a negative result stays in place; § 9 is what to read.

Consequence: `Q11` — whether `TC1IP` is write-1-to-clear — is **void**, because
a bit that never latched cannot be shown to clear. It is still the **only**
test this project has of that D Table 25 claim, and `rtl819x_tc1_disarm()`'s
`TCIR` write (`:433-437`) still rests on one source.

### 8.5 🔴 Two defects in tc1_ext, and only one of them was predicted

**(a) wrap aliasing — predicted in § 5.2.1, confirmed at 703 s rather than 30 s.**
`TM-5b-arm` → `TM-5b2`: true gap 140,693,532 counts, `tc1_ext_gap_max` reads
**6,475,672** ~~= that value mod 2^27~~, and `tc1_ext_trusted` reads **1**. 🔴 量 2026-09-04 (`R5-3a`, recomputed from the captures by program rather than re-read): **6,475,672 is NOT 140,693,532 mod 2²⁷ — that is 6,475,804, a difference of 132.** What is exact is the wrapped TC1 delta between the two reads, `(6,477,665 − 1,861) & MASK` = **6,475,804**, and `tc1_ext` accumulated exactly that. **So the aliasing is exact and what was lost is precisely one period, 134,217,728 counts**, with `tc1_ext_trusted` reading 1. `tc1_ext_gap_max = 6,475,672` is the LARGEST SINGLE inter-read gap, not the span: `tc1_ext_reads` goes 1 → 3 across that arm, so two advances happened and they sum to 6,475,804, the other being 132. One
entire period — 134,217,728 counts — lost, with the flag asserting trust.
§ 5.2.1's mechanism is exactly right; only its threshold moved by the same
71.43×.

**(b) read-driven accumulation — not predicted, and arguably worse.**
`TM-5c`, after 462 s in which nothing read `/proc`: `tc1_cycles = 98,840,142`
against `tc1_ext = 6,477,776`, a deficit of 92,362,366, `gap_max` unchanged,
`trusted = 1`. 讀, `:476-477` — the only call site of `rtl819x_ext_advance()`
is inside `rtl819x_tc_read_proc` and guarded by `rtl819x_tc1_armed`. **So
`tc1_ext` is a sum over the intervals somebody happened to read `/proc` in, not
an extension of the counter**; with no reader it silently stops, and
`tc1_ext_trusted` — only `reads > 0 && gap < (MASK >> 1)` — still says 1.

`R5-3` owns both: advance from something guaranteed to run once per period, and
make the trust flag refuse when `Δjiffies × TICK_NSEC` implies more than one.

### 8.6 🔴 tc1_ext_reads counts kernel calls, not user reads — and not even a fixed number of them

量, the printed sequence over eight dumps: `1, 3, 5, 7, 9, 11` then, after a
re-arm, `1, 3, 4`. **`+2` per `cat`.** 讀, `:487` — `reads` is snapshotted after
the advance, and `cat` reads a 2.6 `read_proc` file **twice** (the second call
returns 0 for EOF). Modelling `cat` as exactly two calls reproduces every cell
except `TM-7`, which is **one higher than the model**; `TM-5c`, the other
`disarm ; cat`, matches exactly. One extra `read_proc` call therefore occurred
while armed, between `TM-6`'s third dump and `TM-7`'s disarm, and its **cause is
undetermined**.

🔴 **The card's claim that a different number means an unissued `/proc` read is
false as stated** — it can equally mean `cat` made a different number of kernel
calls. The check found something real; it is not the thing it was advertised to
find. `arm` zeroing the counters is confirmed both ways (讀 `:385-388`; 量,
`TM-5b-arm` reads 1 after a run that had reached 11).

---

## 9. 🔴 2026-09-04 (`R5-10`, desk): § 8.4's finding is right and its cause is wrong, and the correction gives `R5-3` back its safe step

§ 8.4 concluded, from seating 11:

> *So the masked-observation strategy does not work on this part. `R5-3` cannot
> verify the interrupt path by watching a latch first and arming second; it must
> set `GIMR.TC1IE` with a handler already installed. There is no intermediate
> step, and the driver was designed as though there were.*

**The observation stands. The attribution does not, and the last sentence is
exactly backwards: the driver was designed as though the intermediate step
existed, and it does — the driver just never took it.**

### 9.1 Two enables were clear at once

量, `TM-5b2`, unchanged for the whole 703.46 s arm:

```
tcir = 80000000    ->  TC0IE=1  TC1IE=0  TC0IP=0  TC1IP=0     (D Table 25; bspchip.h)
gimr = 00209100    ->  bit 9 TC1_IE = 0
```

`TCIR` bit 30 is the **timer block's own** interrupt enable. `GIMR` bit 9 is the
**global controller's** mask, one layer downstream. § 8.4 named only the second
one. **The experiment cannot separate them**, because both were 0.

### 9.2 🟢 The repository already held the reading that decides it, and it is fourteen days older

`RUNSHEET` `C5`, 量 seating 1, **2026-08-24**: `GIMR` bit 8 (`TC0_IE`) was
cleared **by hand**, a tick elapsed, and `GISR` moved
`88000004` → **`88000104`** → `88000004`. Bit 8 of `GISR` is `TC0_IP`.

**On this die, masking a source in `GIMR` does not stop its pending bit from
latching in `GISR`.** It stops delivery; the latch happens anyway, and
re-enabling the mask let the vendor's handler run and ack it. `C5`'s own
write-up already says so — *"with `TCIE` masked the interrupt could not be taken
so it latched"* — and it is one bit along from the question.

So `GIMR` bit 9 being clear is **not** a sufficient explanation for `GISR` bit 9
and `TCIR` bit 28 both reading 0 across a full `2^27` period. The remaining
clear gate is `TCIR.TC1IE`.

### 9.3 🔴 The driver arms a counter and does not arm an interrupt

讀, `rtl819x-timer.c`. `rtl819x_tc1_arm()` writes `TCCNR` bits 29/28 and
`TC1DATA`. **It never writes `TCIR` bit 30.** The only `TCIR` write in the file
is in `disarm`, and it deliberately *preserves* the IE bits:

```c
ir = rtl819x_tc_rd(RTL819X_TCIR);
rtl819x_tc_wr(RTL819X_TCIR, (ir & RTL819X_TCIR_IE_BITS) | RTL819X_TCIR_TC1IP);
```

`RTL819X_TCIR_TC1IE (1u << 30)` is defined, and used only inside that mask. The
file's own header comment asserts *"`TCIR`'s `TC1IP` (bit 28) latches on a TC1
timeout"* — **推**, never checked, and that assumption is what seating 11
refuted. § 4's hazard analysis is not refuted; its precondition was never met.

### 9.4 What `R5-3` should do instead, and why it is cheaper than § 8.4 implied

`docs/interrupt-map.md` § 3.3 carries the four cells. The one that matters:

**`I2` — set `TCIR` bit 30 alone, leave `GIMR` bit 9 clear, install no handler.**
Wait one TC1 period, then read `TCIR` and `GISR`.

* 🟢 **Zero risk by construction**, and it is `C5` that says so rather than an
  argument: with `GIMR` bit 9 clear, nothing can be delivered.
* `tcir_tc1ip = 1` and `gisr_tc1ip = 1` → § 9.2 is confirmed, the masked-
  observation strategy is back, and **`Q11` becomes testable again** (write 1 to
  bit 28, read it back) — this project's only test of D Table 25's single-source
  write-1-to-clear claim.
* both still 0 → § 9.2 is wrong too, and the block needs something this project
  has not identified. **That is the informative outcome and it is worth the
  cell.**

⚠️ **Shorten `TC1DATA` for this cell.** At the Linux rate one period is
**671.07 s** (`CLK-22`); `2^27` was chosen for the clocksource's wrap margin,
not for an interrupt test.

### 9.5 🔴 And when the interrupt is finally armed, the driver must not write `GIMR` itself

讀, `arch/rlx/bsp/irq.c` — `bsp_ictl_irq_mask`/`unmask` are
`REG32(BSP_GIMR) &= ~(1 << (irq - 16))` and `|= (1 << (irq - 16))`. TC1's Linux
IRQ is **25** (`BSP_TC1_IRQ = BSP_IRQ_ICTL_BASE + 9`), so bit 9 **already has an
owner**: the `irq_chip` `bsp_ictl_irq_init` registers, with `handle_level_irq`.

A driver that writes the bit directly is a second writer of a register whose
owner does an unlocked read-modify-write. **`I4` is `request_irq(25, …)` and
nothing else.** `PROGRESS.md`'s `TMR-2` says *"必須在 handler 已裝好的前提下直接
寫 `GIMR` bit 9"* — the *handler first* half is right; the *write it directly*
half is the part to drop.

🟢 **And no vendor patch is needed**: `bsp_ictl_irq_dispatch` already carries
`else if (pending & BSP_TC1_IP) do_IRQ(BSP_TC1_IRQ);`.

### 9.6 § 8.1's "a vendor file this project has never opened" named the wrong file

`CORRECTIONS-block8.md` § 9 ④ and § 8.1 both point at
`arch/rlx/kernel/rlx-time.c`. 讀 2026-09-04: that file is a **111-line shim**
whose `time_init()` is three lines and calls `bsp_timer_init()`. The
reprogramming lives in **`arch/rlx/bsp/timer.c`**, and it recomputes both
registers exactly — `CDBR = 1000 << 16` and, on the `BSP_REVR`-selected 8196E
arm, `TC0DATA = ((200000000/1000)/100) << 4`. `docs/interrupt-map.md` § 3.5
carries the four-register comparison; all four match the device.

🔴 **The reason neither file was opened is a `grep -r`**, and the interval is
**2026-08-23 → 2026-09-04, 12 days** — the drop's own mtimes and `CLONED.tsv`
date the clone, and this is the first reading of either file:
`arch/rlx/bsp` is a symlink and GNU `grep -r` does not follow one, so every
sweep of `arch/rlx` in this project has been blind to the 13 files that are the
board. `notes/kernel-build.md` § 10 already carried that for `find`;
`docs/interrupt-map.md` § 6.1 records the new instance.

---

## 10. 🆕 2026-09-04 (`R5-3a`, desk, no power): version 2.0 — the interrupt path, and three defects the desk found before the bench could

`R5-10` moved `R5-3` twice and this segment is the desk half of what it moved to.
Four things were forced by a reading rather than chosen, and the order matters
because each was a precondition for the next.

### 10.1 🔴 Fixing `hz_assumed` alone would have shipped a WORSE number than the bug

`CLK-22` says the compiled `RTL819X_TC_HZ = 14,286,057` is the loader's rate and
the Linux rate is 200,000 — a factor of 71.43. The obvious fix is to derive the
rate at init and print it. **That fix, alone, is wrong**, and the reason is not
visible from the driver at all.

量 at the desk, re-deriving `clocksource_hz2mult()`'s integer arithmetic
(`scratchpad/multshift.py`, and the tool is a script rather than a paragraph
because this is exactly the class of thing a paragraph gets wrong):

| `hz` | `shift` | exact mult | as `u32` | ns per count implied |
|---:|---:|---:|---:|---:|
| 14,286,057 | 24 | 1,174,376,947 | 1,174,376,947 | 69.998 ✅ |
| **200,000** | **24** | **83,886,080,000** | **2,281,701,376** | **136.000** ❌ (true: 5,000) |

讀 `include/linux/clocksource.h:253-266`: `clocksource_hz2mult` computes in
`u64` and returns `(u32)tmp`. **The overflow is a cast. There is no diagnostic.**
And 讀 the same file at `:317-322`, `cyc2ns()` is
`((u64)cycles * cs->mult) >> cs->shift` returned as `s64`, so there is a second
bound on `mask × mult`.

🔴 **2.6.30 has no `clocks_calc_mult_shift()`** — the helper that does this
search in later kernels. 讀, the whole header: `clocksource_hz2mult` is the only
thing there. So the driver searches for its own shift, from 31 downwards, taking
the largest that satisfies both bounds and keeps `mult ≥ 2²⁰` (which bounds the
conversion's own rounding error at about 1 ppm). At `hz = 200,000` and
`mask = 2²⁷−1` that is **shift 19, mult 2,621,440,000 — exact**, because
`10⁹ / 200,000 = 5,000` is an integer and the rounding term contributes nothing.

⚠️ **The search runs against the LARGEST mask the driver can be set to**, not
the current one. `period` can shrink the mask later; a smaller mask only relaxes
the `mask × mult` bound, so a shift chosen at the maximum stays valid for every
period, and one chosen at the current period would not survive being widened.

### 10.2 The rate is derived TWO ways, and they are different quantities

```
hz_tick = (TC0DATA >> 4) × HZ           = 2000 × 100   = 200,000
hz_cdbr = BSP_SYS_CLK_RATE / (CDBR>>16) = 200e6 / 1000 = 200,000
```

The first descends from the kernel's own tick and needs **no clock constant at
all**; the second descends from the crystal and needs the 200 MHz figure
(讀 `bspchip.h`, 量 `CLK-02` to ±7 ppm). `hz_used` is the first, because `R5-2`
measured `ΔTC1 = Δjiffies × (TC0DATA >> 4)` with residual **exactly zero** over
three intervals — that identity is what `hz_tick` encodes. `hz_agree` is the
comparison, made by the driver rather than by a reader; a disagreement is a
finding about the SoC's dividers and not about this file.

🟢 **And a third route was already in the record and nobody read it as one.**
`arm_delta_100us` is a `udelay(100)` bracket over the counter. Seating 11 read
**21**. At the loader rate that predicts 1,429; at 200,005 Hz it predicts
**20.0**. The block-8 card's band was 1300…1600 and the field read 21 — so that
number was a measurement of the true rate, sitting in a committed capture,
while the same seating's `hz_assumed` line said something 71× different.

### 10.3 `TMR-1`'s two fixes, and why the broken number is KEPT beside the fixed one

**Aliasing.** `tc1_ext_trusted` was `gap_max < (MASK >> 1)` on a gap already
reduced mod the period. 量 `TM-5b2`: a real gap of 140,693,532 counts reported
as **6,475,804** — exactly that value mod 2²⁷, and exactly what `tc1_ext` accumulated — and trusted. ⚠️ The field that reads 6,475,672 is `tc1_ext_gap_max`, the largest SINGLE inter-read gap of the two that happened, and this note said *that* was the aliased value until it was recomputed. The fix records
`jiffies` at each advance and tests `Δjiffies < period_jiffies`. That is the
owner's stated rule (`Δjiffies × TICK_NSEC` against one period in ns) **with
both sides divided by `TICK_NSEC`**: the same inequality, no 64-bit multiply,
and `period_jiffies` is printed so a reader can redo it.

🔴 **`tc1_ext_gap_max` in counts is still printed, and still aliases.** The pair
is what makes the defect legible: `(6,475,804 counts, 70,346 jiffies)` says *a
whole period was lost* on its face, and either number alone does not. Removing
the broken one would delete the evidence along with the bug.

**Reader-driven accumulation.** `rtl819x_ext_advance()`'s only call site was
inside the `/proc` read, so `tc1_ext` was *the sum of the intervals somebody
looked at* — 量 `TM-5c`: 462 s with no reader, 92,362,366 counts behind, still
trusted. A `timer_list` at **a quarter of a period** now drives it (derived at
arm from `hz_used` and `period_bits`, not a constant), and the interrupt handler
advances it too once one is installed.

⚠️ **Its blind spot, stated:** that timer is driven by the vendor's TC0 tick, so
if the tick dies the extension stops **and** `jiffies` stops, which makes
`Δjiffies` read 0 and look trustworthy. Bounded rather than closed: a board
whose tick has stopped is not running, and `tc1_cycles` is read from the
hardware on every dump, so `tc1_cycles` vs `tc1_ext` still exposes it.

### 10.4 🔴 A defect found by reading, in a path no reading could have reached

`arm()`'s `clocksource_register()` failure branch cleared `armed` and **left TC1
counting**. `disarm` then returned `-EINVAL` because `armed` was 0, so nothing
in the driver could stop it — an unreachable state created by the one path that
is supposed to be the safe failure.

**It has never been reached**: `clocksource_register` returned 0 on the silicon
(量 seating 11), which is exactly why no reading would have found it. Version
2.0 puts `TCCNR` back and stops the extension timer on that path.

### 10.5 The four verbs, and where the stop-if lives

`docs/interrupt-map.md` § 3.3.1 carries the design. The one sentence worth
repeating here: **`reqirq` refuses unless the driver has itself watched `ackip`
take `TC1IP` from 1 to 0**, because 讀 `arch/rlx/bsp/irq.c` the ICTL chip's
`.mask_ack` masks and does not ack the device, and 讀 `kernel/irq/chip.c`
`handle_level_irq()` unmasks after the handler unless `IRQ_DISABLED` — so a
handler that cannot clear the pending bit re-triggers forever. The card cannot
hold that rule, because a rule a human checks off a 38400-baud capture is a rule
whose correctness depends on the experiment behaving.

### 10.6 What version 2.0 does NOT do

1. **No clockevent, no rating change.** The system time base is still `jiffies`.
   That is `R5-3b`.
2. **`ESTATUS` is still unread.** `Status` becomes readable; the LOPI mask lives
   in the `lxc0` file reached by `mflxc0`, and TC0 runs there.
3. **Nothing here has run on the silicon.** Every number in § 10.1–§ 10.3 is a
   desk derivation from committed captures and vendor source. The card is
   `bench/2026-09-04/PREDICTIONS-B10-block9.md`.
