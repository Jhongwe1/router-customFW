# Bring-up — TOTOLINK N150RT / RTL8196E

**Opened 2026-09-09** (forty-ninth segment), during `R5`. `plan` names this
file twice: as the artefact `R5` opens, and as the place `D2`'s *comparison of
the two binding models* goes. It grows through the gate rather than being
written at the end.

`PROGRESS.md` owns which step is active. This file owns **how a driver on this
part is brought up and bound**, and nothing else restates that.

---

## 1. The two binding models, and why there are two

`R5`'s Definition of Done asks each driver for **two** binding models. They are
not alternatives and neither is a draft of the other.

| | model A — `platform_device` | model B — device tree |
|---|---|---|
| kernel | Linux **2.6.30**, the vendor tree this project builds and boots | a modern tree; 6.8 is what the tooling here is checked against |
| where it lives | `config/rlxfw-src/linux-2.6.30/drivers/` | `dt/` |
| how the driver finds its registers | a compiled-in physical address through `CKSEG1ADDR` | a `reg` cell, `ioremap`ed at probe |
| **has it run on the silicon** | 🟢 **yes** — timer, GPIO, SPI+MTD and watchdog have all executed on this die | 🔴 **no, and it cannot**: 2.6.30 has no device tree |
| what it proves | that the register map, the arming order and the failure modes are right, because the part did what the driver said it would | that the hardware has been *described* in the form the rest of Linux expects, and that the description is machine-checkable |
| who checks it | the bench cards under `bench/`, and `check-predictions` | `tools/dtcheck.py`, in CI |

**Why B exists at all when A is what runs.** A `platform_device` binding says
nothing to anyone outside this tree: the addresses are in a `#define` and the
wiring is in a board file nobody else has. A binding says the same facts in the
form that gets reviewed, and it is the artefact `R10a` needs. Writing it while
the driver is still warm costs a fraction of what writing it later costs, and
**it can be marked honestly**: *written, compiled, never probed* is a legal
state, and it is more credible than "I have done device tree" because it names
its own limit.

**Why A is still the mainline here.** The device is one unit with no spare. A
2.6.30 driver that has been arming a watchdog on the silicon for two seatings
is evidence; a 6.8 driver that has never been near the part is not. Model B is
not allowed to make claims model A earned.

### 1.1 What moves between them, and what does not

| | |
|---|---|
| **carries over unchanged** | the register offsets, the reset values, the bit positions, the write-1-to-clear semantics, the arming order, and every measured timing. `SPEC.md` is the owner and both models quote it |
| **is expressed differently** | ownership. Model A has none: the 2.6.30 watchdog derives its rate by reading `TC0DATA` and `CDBR` — registers belonging to the timer — and nothing objects. Model B has to say `clocks = <&timer>`, and the timer has to be a clock provider |
| **does not carry over** | the `/proc` instrumentation. Those files exist so a bench card can read a driver's own state back through a serial console; a modern driver does not want them, and `create_proc_entry`/`read_proc`/`write_proc` are gone anyway (§ 3) |

🔴 **The ownership row is not a style point, and there is a measured price on
it.** `SPEC.md` `CLK-08b` carried 14,965,000 Hz as the watchdog's counting
frequency. That is a **loader-state** constant; under Linux the same counter
runs at 200,180 Hz, and the driver's compiled table was wrong by **76×** for
three segments. It survived because the frequency had no owner — the watchdog
read it out of another device and no layer was in a position to disagree. In
model B the watchdog asks the timer, and there is exactly one place that
number can be wrong.

---

## 2. The three things describing this part in DT actually forced

Written while `dt/rtl8196e.dtsi` was being written, because each one only
appeared then. `notes/device-tree.md` carries them in full.

**① A block can hold two devices, and the tree has to split it.** `WDTCNR` is
at `0x1800311c`; the datasheet's Timer/Counter block starts at `0x18003100`.
Two sibling nodes each claiming the documented block overlap, and the second
`request_mem_region()` returns `-EBUSY`. The tree gives the timer `0x00`–`0x1b`
and the watchdog the word above it: adjacent, disjoint, word granularity.

**② A divider inside one device is a clock the others consume.** See § 1.1.

**③ `dtc` classifies a node by its NAME.** A node called `spi@18001200` is an
SPI *bus* to dtc, which then requires `#size-cells = <0>` on it. This block is
one NOR device behind a fixed chip select plus a 4 MiB read window, not a set
of addressable slaves, so the node is `flash-controller@18001200`. **Found by
the checker on its first run against the real tree, not by reading.**

---

## 3. What model B still owes, and its measured size

`D2`'s row has four acceptance criteria. ①`dtc` compiles, ③`dt-validate`
passes and ④*marked never probed* landed on 2026-09-09. ② — **the driver
compiles in a modern kernel tree** — has not, and is `R5-12`.

量 2026-09-09, against `linux-headers-6.8.0-139`: across all four drivers,
**10** identifiers are kernel API in 2.6.30 and absent from 6.8, and **7 of the
10 are the same three names** — `create_proc_entry`, `read_proc`, `write_proc`.
That is the bench instrumentation, not the driver. The distinct removals are
`clocksource_register`, `cycle_t`, `clock_event_mode`, `clockevents_handle_noop`,
`getnstimeofday` and `add_mtd_device`.

⚠️ **That method cannot see a symbol that still exists with a changed
signature**, and those are the expensive ones — `clocksource.read` gained a
parameter, `mtd->read` became `_read`, the hand-rolled watchdog misc device is
replaced by `watchdog_device`. **10 is a lower bound and ② is neither
confirmed nor refuted.** The cell that settles it compiles **one** driver
against 6.8; `rtl819x-wdt` is the candidate, because it has the smallest
missing set and the largest expected shrink.

🟢 **2026-09-09 (fiftieth segment): that cell ran, and ② is ANSWERED for
one driver.** `rtl819x-wdt` compiles against **6.18.50** — not 6.8, which
量 is not on kernel.org's list at all — for **`+46 / −10` lines against
1,547 = 3.62 % of the file**, over **4 distinct APIs**, producing a
22,696-byte `elf32-tradbigmips` object with all its symbols.

🔴 **And compiling the other three refutes the generalisation, which is
why they were compiled.** `rtl819x-wdt` was chosen for having the
*smallest* missing set. 量, verbatim against 6.18.50 — diagnostics, not
root causes, and only the wdt column has a measured root-cause count:

| driver | lines | census (vs 6.8) | gcc diagnostics (vs 6.18.50) |
|---|---:|---:|---:|
| `rtl819x-timer` | 2,813 | 8 | **1, FATAL** — `asm/rlxregs.h` |
| `rtl819x-gpio` | 673 | 3 | **24** |
| `rtl819x-spi` | 1,738 | 5 | **18** |
| `rtl819x-wdt` | 1,547 | 3 | **6** (4 root causes) |

`gpio` and `spi` are dominated by the census's **declared** blind spot:
**20** of gpio's 24 are `struct gpio_chip` used as an incomplete type —
the name is in both trees; mainline moved the definition to
`<linux/gpio/driver.h>` — with a 21st, `gpiochip_add`, from the same move
and the remaining 3 from `/proc` (🔴 this read *21 … as an incomplete
type* until every diagnostic was assigned and the classes made to sum to
24) — and spi's are `mtd_info has no member named
‘read’; did you mean ‘_read’?`, `erase_info` without `state` or `mtd`,
`MTD_ERASE_FAILED` gone. **`rtl819x-timer` is a third category the census
cannot have a name for**: it stops at an `#include` of `asm/rlxregs.h`,
which 量 exists only under `arch/rlx/include/asm/` — and mainline has no
`arch/rlx` at all. ⚠️ **Its cost is UNMEASURED, not small**, because that
fatal masks everything behind it. **The plan's ~0.3-segment estimate
survives for `rtl819x-wdt` and for no other driver measured here.**

🔴 **And the census under-counted this driver by one, with a mechanism it
had not declared.** It said 3; the true figure against 6.8 is 4. The miss
is `setup_timer`, whose only occurrence under 6.8's and 6.18's `include/`
is `serial_8250.h:97` — `void (*setup_timer)(struct uart_8250_port *)`, a
**member of an unrelated struct in an unrelated subsystem**. The declared
blind spot was *name survives, signature changed*; this one is *name does
not survive as an API at all and collides with something else*. Both
under-count, so the direction of the paragraph above is unchanged.

⚠️ **Compiling is not upstream acceptance**, which is `D1`'s bar: this
driver is still a hand-rolled `miscdevice` on `WATCHDOG_MINOR` where a
modern one registers a `struct watchdog_device`, and neither that nor its
`/proc` file is a compile error. **3.62 % is the floor, not the ceiling.**
`notes/modern-kernel-port.md` has the ladder, the controls and the diff.

---

## 4. Bring-up order on this part, and what each step cost

The order is the standard one — clock, interrupt, timer, everything else — and
`R5` follows it deliberately: `v4` of the plan started at the fourth position
and `v5` put the timer back in front.

| | step | what made it possible | what it cost |
|---|---|---|---|
| 0 | `rtl819x-timer` — clocksource, then clockevent | a `±7 ppm` reference frequency to check against (`CLK-02`), and coexistence with the vendor's timer so the two could be compared before anything was switched | four seatings, split into `R5-1`/`-2`/`-3a`/`-3b-1`/`-3b-2` so that each was a single-variable experiment |
| 1 | `rtl819x-gpio` | one line whose CNR bit the loader had already cleared | one seating; output remains refused by mask |
| 2 | `rtl819x-spi` + MTD | a second, independent path to the same bytes — the loader's own `FLR` — to check a 4 MiB read against | two seatings |
| 3 | `rtl819x-wdt` | the timer, and the fact that a watchdog is the one peripheral whose correct behaviour is *the board resetting* | three seatings |
| 4 | `leds-rtl819x` | 🔴 not written. Its blocker is two masks and a second consumer, § 5 | — |
| 5 | `gpio-keys` | 🔴 not written | — |

🔴 **The irqchip is deliberately not in this list.** 2.6.30 has no
`irq_domain`, so what would be written here is the wrong shape. `R5` delivers
`docs/interrupt-map.md` instead — the routing table and the four arming layers
a timer interrupt needs — and the driver itself is `R10a`'s.

---

## 5. The open blocker, stated where the next reader will look

`R5-7` (`leds-rtl819x`) needs **two** masks changed, not one. `known_mask` is
`0x00000020` — bit 5 only — so `.request` refuses line 6 before
`ALLOW_OUT_MASK` is ever consulted. And the vendor's `rtl_gpio_timer` writes
bit 6 as well, so two consumers want one line.

🟢 **`dt/rtl8196e-totolink-n150rt.dts` is where that conflict became something
to point at.** In a device tree, two consumers of one GPIO line is visible in
the source; on 2.6.30 it is an errno at run time.
