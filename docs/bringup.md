# Bring-up — TOTOLINK N150RT / RTL8196E

**Opened 2026-09-09** (forty-ninth segment), during `R5`. `plan` named this
file twice then: as the artefact `R5` opens, and as the place `D2`'s
*comparison of the two binding models* goes. It names it a third time as `P3`,
the board bring-up report, whose ten sections are §§ 6–15 below. It grows
through the gates rather than being written at the end.

`PROGRESS.md` owns which step is active. **§ 0 says what this file owns and
what it does not claim; read it before quoting any number out of §§ 6–15.**

---

## 0. What this file is, and the seven things it does not claim

**Every sentence about the machine carries a mark**: **量** measured on this
device · **讀** read out of code, a dump or the draft datasheet · **推**
inferred, pending a measurement. **未定** is an open value and **殘留** is the
question left after a value was settled. Mixed together they are worth neither,
so a cell that would need two marks is split or left open.

**This file owns two things and no more.** §§ 1–5 own the comparison of the two
binding models and the three things describing this part in a device tree
actually forced — they were written here first and `D2` asks for them here.
§ 13.1 owns the 2026-10-04 peripheral census; `SPEC.md` `FW-193` names it as
its owner. **§§ 6–15 own nothing.** They are an assembly: every number in them
is traceable to the row that owns it — `SPEC.md` for values, `docs/` and
`notes/` for the findings, `bench/` for the captures — and where this file and
an owner file disagree, **the owner file is right and this page is stale**.
What the assembly is for is the *act*: putting the board-level results in one
order that a reader who has never seen this repository can follow, with the
control that licensed each one beside it.

🔴 **Does not claim ① — that any value here is valid in both machine states.**
This part is brought up twice: the vendor loader programmes it, then Linux
reprogrammes it. The two disagree on registers a reader would expect to be
settled — `CDBR`'s divisor is 14 under the loader and 1000 under Linux
(`REG-11`), `TC0DATA` is 142,858 under the loader and 2,000 under Linux
(`REG-05`), the watchdog's counting clock is 14.9650 MHz under the loader and
200,180 Hz under Linux (`CLK-08b`), and `PABCD`'s `CNR` and `DIR` are both
rewritten (`REG-35`, `REG-37`, `FW-193`). **So every register row below carries
a state column**, and a row with a value in one column says nothing about the
other. A loader-state constant has produced a driver table wrong by 76× in
this project once already (§ 1.1), and that is the failure this column exists
to stop.

🔴 **Does not claim ② — that it is a specification of the RTL8196E.** It is a
description of **one board**, one die, one flash part, with no spare. Nothing
here distinguishes *this part does X* from *this instance, at this revision,
with this loader in it, does X*. The draft datasheet this project holds is for
the `-VE1/2/3-CG` variants with embedded DRAM; this unit has external SDRAM
(`MEM-01` 量), so **every 文 mark is a statement about a family and not about
this die** (`SOURCES.json`'s caveat on source `D`).

🔴 **Does not claim ③ — a measured power tree.** § 7 is the section the plan
asks to be 實測 and it is not. The only rail voltages on file were taken
through a programmer clip, with the board's own 3.3 V net sitting at ~1.79 V
(量, `notes/power-and-programmer.md` §§ 1–2); the regulator's output pins have
never been probed, `BRD-01`'s part is unidentified, and `S0b` is `⊘` by a
recorded decision. **§ 7 is a desk reconstruction with two surviving
hypotheses, and it says so in its own first line.**

🔴 **Does not claim ④ — completeness of the peripheral census.** § 13 enumerates
the blocks this project has *touched*. `NET-35` records that the switch-register
population here is *what the loader wrote*, not *what configures a switch*;
`RF-04` is `⊘` so the radio's attachment to the SoC has never been traced; and
the `MCR` memory controller at `0xB8001000` has never been read on this device
(`MEM-07`, `MEM-08`). A block nobody thought to ask about is invisible to § 13.

⚠️ **Does not claim ⑤ — that the register values in § 15 are good because they
are there.** § 15 is *values this device has returned*, with the state they were
returned in. It is not a known-good *configuration*: nothing in it was derived
from a specification of what the register should hold, several rows are a single
reading, and a row whose two sources are both Realtek downstream is one source
seen twice (`CPU-04`'s three recorded weaknesses are the worked example).

⚠️ **Does not claim ⑥ — that the strapping fields are decoded.** § 9 has the
word this device returns at the strapping address (量) and the datasheet's
initial value (文) and **no field layout from any source**. Reading a word is
not reading a strap.

⚠️ **Does not claim ⑦ — that four `⊘` rows were reopened by being named.** Four
`SPEC.md` § 17 rows name a section of *this* report as their reopen condition:
`CLK-03` (if § 8 writes ÷2 as 量), `MEM-08` (if § 15 lists it), `RF-04` (if
§ 13 lists it) and `BRD-01` (if § 7 is written as 量). **None of them is
reopened here.** Each is named as open, with its reopen condition quoted, and
§ 16 lists them; the decision to reopen belongs to the gate board and to the
owner, not to this file.

---

## Contents — the plan's ten sections, and where each one landed

The left column is `plan/router-rebuild-plan.md` § 6, block *`P3` — Board
Bring-Up 報告*, which lists exactly ten sections. §§ 1–5 and § 13.1 predate
`P3` and keep their numbers, because `docs/FINDINGS.md` cites `§ 3a` and a
`SPEC.md` row owns § 13.1 — so `P3`'s ten start at § 6.

| plan § | plan's own name | here | what state its numbers are in |
|---:|---|---|---|
| — | *(predates `P3`)* | § 1 | the two binding models, and § 1.1's 76× price |
| — | *(predates `P3`)* | § 2 | three things a device tree forced |
| — | *(predates `P3`)* | § 3 · **§ 3a** | what model B owes; `§ 3a` is cited by `docs/FINDINGS.md` |
| — | *(predates `P3`)* | § 4 | bring-up order and what each step cost |
| — | *(predates `P3`)* | § 5 | the GPIO blocker, closed in place |
| 1 | 板級概觀 — board overview | **§ 6** | identity and parts; state-independent |
| 2 | 電源樹（實測，含 `S0b`）— power tree | **§ 7** | 🔴 **not 實測**; clip-side 量 only, `S0b` `⊘` |
| 3 | 時脈樹 — clock tree | **§ 8** | both states, split per row |
| 4 | Strapping（datasheet § 6.1） | **§ 9** | loader state only |
| 5 | Pinmux 表 — pinmux table | **§ 10** | loader and Linux, three states read |
| 6 | 記憶體映射 — memory map | **§ 11** | physical / KSEG / flash offset, marked per row |
| 7 | 開機流程 — boot flow | **§ 12** | per stage, each stage named |
| 8 | 周邊盤點 — peripheral census | **§ 13** · **§ 13.1** | Linux state; § 13.1 is the 2026-10-04 reading |
| 9 | Errata / 陷阱 — errata and traps | **§ 14** | per trap; `F46` is `§ 14.1` |
| 10 | 已知良好的暫存器值 — known-good values | **§ 15** | **state column is the point of the table** |
| — | *(this file's own)* | § 16 | what the whole document does not establish |

🔴 **§ 14 is the section this report exists for.** The plan's own note on it:
*一份只有「規格」的 bring-up 報告是抄的；一份有「這顆的坑在哪、我怎麼撞到的、
怎麼繞過」的才是做過的* — a bring-up report that holds only specification was
copied; one that holds where the part bites, how it was hit and how it was
worked around was done. Every row in § 14 therefore carries how it was hit
and how it was worked around — or says that it was not.

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
passes and ④*marked never probed* landed on 2026-09-09. ~~② — **the driver
compiles in a modern kernel tree** — has not, and is `R5-12`.~~
🟢 **② landed on 2026-09-10 and `R5-12` is closed: all four drivers compile
clean against 6.18.50**, each through its own ladder, each producing an object.
The rest of this section is kept as it was written, because the order in which
its two answers arrived is the finding — read § 3a for what the second one
changed about the first.

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

### 3a.  🟢 2026-09-10 (fifty-first segment): all four, and the counts above are floors

| driver | ladder, each rung predicted before it ran | code churn | object |
|---|---|---:|---:|
| `rtl819x-timer` | 1 fatal → 25 → 20 → 19 → 18 → 7 → 6 → 4 → 3 → **0** | 4.19 % | 37,300 B |
| `rtl819x-gpio` | 24 → 5 → 4 → 1 → **0** | 6.98 % | 11,512 B |
| `rtl819x-spi` | 18 → 11 → 6 → 5 → 4 → **0** | 4.66 % | 27,572 B |
| `rtl819x-wdt` | 6 → 5 → 4 → 3 → 4 → **0** | 2.84 % | 22,696 B |

*Code churn* excludes added comment lines; the `+46 / −10 = 3.62 %` published
above is the figure that includes them, and both are given in
`notes/modern-kernel-port.md` § 6 because these ports are heavily commented on
purpose.

🟢 **`rtl819x-timer`'s cost is now measured and it is not the large one.**
The `arch/rlx` coupling is **one line** and costs **zero diagnostics**:
`<asm/mipsregs.h>` supplies all three symbols the vendor header was included
for, because mainline still supports R3000-class parts and keeps `ST0_IEC`
beside `ST0_IE` at the same value. ⚠️ The sentence above — *UNMEASURED, not
small* — was correct when written and is not retroactively upgraded into
*it was hard*.

🟢 **The estimate question has a magnitude now.** Code churn across the four
spans **2.84 %–6.98 %**, a factor of **2.46**, and `rtl819x-wdt` is indeed the
cheapest — so the warning above was right and the spread is 2.46×, not an
order of magnitude. ⚠️ On n = 4, churn does **not** track file size: the
largest file is the second cheapest and the smallest is the dearest.

🔴 **And the diagnostic counts in § 3's table are FLOORS, by two measured
mechanisms.** ① gcc reports an implicitly declared function once per
translation unit, so one diagnostic stood for two `del_timer_sync` call sites
in `timer`; ② while a struct is an incomplete type the compiler cannot check
the signatures of things assigned to its members, so `gpio_chip.set` changing
from `void` to `int` in 6.15 was invisible in **all 24** of gpio's.
Both were found by a ladder rung **missing its prediction**. So `24 / 18 / 6`
bound the work from below, and the `8 / 3 / 5 / 3` identifier census is a floor
on a floor. `notes/modern-kernel-port.md` § 9.4.

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
| 4 | 🔄 upstream **`leds-gpio`** *(this said `leds-rtl819x` until 2026-09-10)* | 🔴 not written. Its blocker is two masks and a second consumer, § 5 — and the risk argument for opening them is `notes/gpio-driver.md` | — |
| 5 | `gpio-keys` | 🔴 not written | — |

🔴 **The irqchip is deliberately not in this list.** 2.6.30 has no
`irq_domain`, so what would be written here is the wrong shape. `R5` delivers
`docs/interrupt-map.md` instead — the routing table and the four arming layers
a timer interrupt needs — and the driver itself is `R10a`'s.

---

## 5. The open blocker, stated where the next reader will look

🔄 **2026-09-10, later the same day: this section is no longer the open
blocker, and the paragraph it opened with is kept because the two masks are
what changed.** `rtl819x-gpio` **1.1** carries `known_mask 0x60` and
`ALLOW_OUT_MASK (1u << 6)`, `arch/rlx/kernel/rlxfw-devices.c` registers the
`platform_device` upstream `leds-gpio` binds to, and image `r58`
(`RECIPE_ID` `083b1cb8`) is built and gated. ⚠️ **What is open is now a
seating and not a decision**: ~~nothing of this has run, `n_writes` has never~~ 🔄 **2026-09-10, seating 20: it ran, and this clause is what was left stale.** `r59` (`RECIPE_ID` `692a2801`), seventeen boots: `allow_out_mask` reads `00000040` in every dump, `n_writes` reads **2** at rest and **4** after the LED boot with all four accounted for, an unmodified upstream `leds-gpio` produced **light** from a sysfs write, and the guard was exercised in both directions. The eight refutation conditions did not fire. *(The struck clause read:)* `n_writes` has never
read anything but 0 on the device, and the eight refutation conditions in
`notes/gpio-driver.md` § 8 are all unanswered. The original text:

*(`R5-7` (🔄 upstream **`leds-gpio`**, *not* `leds-rtl819x` — the step's driver
was decided by measurement on 2026-09-10 and the reasons are in
`notes/gpio-driver.md` § 9) needs **two** masks changed, not one. `known_mask` is
`0x00000020` — bit 5 only — so `.request` refuses line 6 before
`ALLOW_OUT_MASK` is ever consulted. And the vendor's `rtl_gpio_timer` writes
bit 6 as well, so two consumers want one line.)*

🔴 **The contention that paragraph names is not solved and is not claimed to
be.** Nothing arbitrates between `gpiolib` and the vendor's `rtl_gpio_timer`,
because the vendor's driver does not go through `gpiolib`. What 1.1 adds is an
instrument rather than an arbiter — a foreign-write detector counting how often
the live `PABCD_DAT` bit 6 differs from the value this driver last wrote — and
its positive control is a button held for ten seconds against a 1 Hz writer.
`notes/gpio-driver.md` § 6.

🟢 **`dt/rtl8196e-totolink-n150rt.dts` is where that conflict became something
to point at.** In a device tree, two consumers of one GPIO line is visible in
the source; on 2.6.30 it is an errno at run time.

## 6. Board overview

`plan` § 6 `P3` section 1 — 板級概觀. Every row's owner is a `SPEC.md` id;
this table is an index into §§ 1–7 of that file and holds no value of its own.
**State: these rows are state-independent** — they are parts and markings, not
register contents.

| what | value | V | N | owner row |
|---|---|:-:|:-:|---|
| product | TOTOLINK N150RT, hardware `V2.0` | 量 | — | `IDN-01`, `IDN-02` |
| SoC | Realtek RTL8196E | 量 | 量 | `CPU-01` — **three sources**: package, boot banner, and the boot code's own id comparison |
| CPU core | Lexra **RLX4181** rev 1, `PRId 0x0000CD01` | 量 | 讀 | `CPU-04`; the name must be quoted with its three recorded weaknesses (`CLAUDE.md`). ⚠️ `CPU-04`'s own V cell reads `—` while its value text records `PRId` 量 2026-08-25b; this row follows the value text, and the mark cell is `SPEC.md`'s to correct |
| CPU clock | 400 MHz | 量 | — | `CPU-11`, `CLK-01` — banner string plus `D`; see § 8 for what is and is not measured |
| SDRAM | Winbond W9825G6KH-6, 256 Mbit, 16M × 16, 16-bit bus | 量 | 讀 | `MEM-01`, `MEM-03` |
| SDRAM fitted / seen | **32 MiB** fitted; loader reports `32M`; Linux is given **26,052 kB** | 量 | 量 | `MEM-04`, `MEM-05`, `MEM-06` |
| memory controller | `MCR` at `0xB8001000` | 讀 | 讀 | `MEM-07` — 🔴 **never read on this device**; its settings are `MEM-08` `⊘` |
| NOR flash part | Eon (cFeon) EN25QH32B, SOP-8, board `U19` | 量 | 讀 | `FLS-01` |
| NOR flash size | **4 MiB / 32 Mbit** | 量 | 量 | `FLS-03` — three sources for the size |
| flash JEDEC id | `0x1C7016` | 量 | 讀 | `FLS-04`; re-read under Linux 2026-10-04 as `rdid_id 1C7016` (`FW-191`) |
| switch | 5-port 10/100, integrated in the SoC | 量 | 讀 | `NET-01`; 4 × LAN + 1 × WAN sockets (`NET-03`) |
| PHYs | exactly five, at MDIO addresses 0–4 | 量 | 讀 | `NET-39` — four registers that share no line of code |
| radio | Realtek RTL8188ER, 1T1R 802.11n 2.4 GHz, separate part | 量 | 讀 | `RF-01` — ⚠️ **one source only (package ink)**; the driver banner prints a version, not a part number |
| antenna | silkscreen `ANT1` and `ANT2`; **one fitted** | 量 | 推 | `RF-05` |
| radio calibration | in `H601` at flash `0x006000`; a factory reset does not restore it | 讀 | 讀 | `RF-06` — permanently write-forbidden (`CLAUDE.md`) |
| external supply | **one 3.3 V rail**; core 1.0 V from the built-in SWR or LDO | 讀 | 讀 | `BRD-02` — § 7 |
| regulator | `LSC LSP5526`, 8-pin, `D3` beside it | 量 (ink) | 推 | `BRD-01` — **unidentified**; buck is inferred from position, output pins never probed |
| front-panel button | a GPIO on `PABCD` bit 5, active low — **not `RESET#`** | 量 | 讀 | `BRD-05` — three sources; its loader-state `XOR 00000020` must be masked `& 0x20` under Linux |
| console | 4-pin 2.54 mm header, factory-fitted, `VCC` · `TX` · `RX` · `GND`, **38400 8N1** at 3.3 V | 量 | 量 | `BRD-08`, `BRD-09`, `BRD-10` — no soldering anywhere in this project |
| EJTAG | datasheet says 5-signal P1149.1 | 文 | 讀 | `BRD-11` — **never located on the board**, no adapter |
| PCB marks | `0422C` beside the SDRAM; `JL-2` · UL `94V-0` | 量 | — | `IDN-04`, `IDN-05` |
| PCB date code | `18.15` — 2018, week 15 | 量 | 推 | `IDN-06`; assembly **not earlier than 2018-09** (推, five agreeing date codes, `IDN-07`) |
| serial number | *deliberately absent* | — | — | `IDN-03` — it identifies this unit (`SPEC.md` § 18) |

⚠️ **What this section does not establish.** `BRD-01` and `RF-01` each rest on a
single source, and a single-source row has not met this project's two-source
threshold — they are listed so that the gap is visible, not because they are
settled. `BRD-04`'s claim that `J2` sits in the DC loop is a layout inference
from a photograph (推) that a continuity check would close. Nothing here was
measured with the board open and powered except the console parameters and the
button; the rest is package ink, boot text and the datasheet.

---

## 7. Power tree — 🔴 what the plan asks for is 實測, and this is not it

`plan` § 6 `P3` section 2 — 電源樹（實測，含 `S0b`）. **The plan asks for a
measured power tree. This section is a desk reconstruction, and the measurement
it would need has a recorded decision not to take it.** `S0b` is `⊘`;
`notes/power-and-programmer.md` is the owner of every number below and § 4 of
that file is the decision.

### 7.1 The topology, as far as any source states it

| node | what is known | V | N | owner |
|---|---|:-:|:-:|---|
| external input | **one 3.3 V rail**, and only one — the part *"requires only a 3.3 V external power supply"* | 讀 | 讀 | `BRD-02`, datasheet § 1 |
| core rail | **1.0 V**, from the SoC's *"built-in SWR or LDO 3.3 V to 1.0 V"* | 讀 | 讀 | `BRD-02` — 🔴 **never probed on this board** |
| barrel jack | board's top-left corner, a button beside it | 量 | — | `BRD-03` |
| `J2` | 2-pin header at the jack; the case switch's pigtail plugs in here. **"in series with the DC loop" is a layout inference from a photograph** | 量 | 推 | `BRD-04` — a continuity check settles it |
| regulator | `LSP5526`, 8-pin, **part unidentified**; "buck" is inferred from position | 量 (ink) | 推 | `BRD-01` `⊘` |

### 7.2 The only rail numbers on file, and what instrument took them

量, `upstream` `BENCH-LOG.md` `T-85` / `P9-5` — **not with the board on its own
supply**: a SOIC-8 clip on `U19`, USB in, ten seconds, flash pin 4 as ground.
`notes/power-and-programmer.md` § 1 owns the per-pin table. The two readings
that matter:

* flash `VCC` (pin 8) sat at **1.70 V** 量, against a nominal 3.3 V.
* `WP#` and `HOLD#` read **1.79 V** 量 — **90 mV *above* `VCC`**. On this part
  they are tied to the supply rail, so 讀 **the board's 3.3 V net was itself at
  about 1.79 V** and the flash's `VCC` pin was 90 mV below it.

🟢 **What that settles, out of numbers that were already on file:** the missing
1.5 V is dropped **between the injection point and the board's rail**, not
inside the board. Ruled out by the same readings: inrush (still 1.70 V after
ten seconds, so it is steady state) and the programmer's own regulator (an
external injection held 3.3 V at the injection point while the chip still sat
at 1.70 V, across three supply configurations).

🔴 **What it leaves open is a two-way split and it is not resolved.** `H1`,
current budget: the board draws more than the source can supply and the source
folds back — predicts the drop is *at the source*. `H2`, series resistance: the
clip contact and ribbon are a few ohms and the board's ordinary draw develops
1.5 V across them — predicts the drop is *across the wiring*. **They are not
separated.** The datasheet makes `H1` plausible without measuring anything —
one external rail means injecting through the flash's `VCC` pin supplies the
SoC core, the SDRAM, the five-port switch and the WLAN through one clip contact
and one flash-pin trace — but plausible is not measured.

### 7.3 Why the measurement was not taken, and what it would take

讀 `notes/power-and-programmer.md` § 4, two reasons in the order that decides:

1. the industry-standard in-system read is *board on its own supply, the
   programmer's `VCC` line not connected*, and **this clip's far end is
   soldered, so its `VCC` line cannot be opened**;
2. with the board powered and the programmer driving `CLK` and `CS#`, those two
   pins are SoC **outputs** (`BRD-07` 讀) and the datasheet does not say reset
   releases them. That is output-against-output contention on **the only
   device**, and only a logic-analyser measurement of `SF_CS0#`/`SF_SCK` while
   reset is held would remove it.

⚠️ **The zero-risk remainder was dropped with the rest, on purpose**: a contact
check, an IR-drop walk and a continuity check are all zero-risk, and mainline
reaches the flash only through the loader at every step through `R9`, so none of
them is on the critical path. What they would have added is the `H1`/`H2`
separation, **and that is recorded as unmeasured rather than guessed**.

### 7.4 What § 7 does not establish, and what would close it

**未定 — the rail voltages with the board on its own supply.** Nothing in this
project has measured the regulator's output, the core rail, or the 3.3 V net
with the board powered normally. `BRD-01` `⊘` names the method — *量 its output
pin against ground, thirty seconds* — and its recorded reopen condition is
**"`P3` wants the power tree written as 量, or a seating that is already powered
does it in passing, with the owner's nod"**. This section does not reopen it: it
is written as 讀 and 推 with one clip-side 量, which is what the evidence
supports. 🔴 **The plan's 實測 for this section is not delivered**: the owner
decided on 2026-10-05 that `R8b`'s seating takes no multimeter readings, and the
multimeter work touches pins on the only powered board, so it needed that word.
This is recorded here rather than hidden behind the numbers that do exist.

⚠️ `MEM-09` 讀: the power-on strapping pins are the DRAM pins — `MA[10:8]` at
44/52/53 and `RAS#`/`CAS#` at 51 — **not the `SF_*` pins**. That is a datasheet
reading (D § 6.1) and belongs to § 9; it is repeated here only because it is the
one place where power sequencing and strapping touch, and it has never been
measured on this board.

---

## 8. Clock tree

`plan` § 6 `P3` section 3 — 時脈樹. 🔴 **Every row carries the state it was
measured in. A loader-state rate does not predict the Linux-state rate on this
part, and § 1.1 is the 76× price this project already paid for blending them.**

### 8.1 The rates, per state

| node | loader state | Linux state | V | owner |
|---|---|---|:-:|---|
| CPU clock | 400 MHz, from the boot banner and `D` | *(same banner; not re-measured under Linux)* | 量 | `CPU-11`, `CLK-01` |
| peripheral Lexra bus | **200.0049 MHz ±0.0015** (±7 ppm on a 2,080 s baseline), against a compiled-in `0x0BEBC200` = 200,000,000 — **+24 ppm** | *(the same bus; `BSP_SYS_CLK_RATE` is 讀 200,000,000)* | 量 | `CLK-02` |
| `CDBR` divisor | **14** (`0x000E0000`) | **1000** (`0x03E80000`) | 量 both | `REG-11`, `CLK-06` |
| divider output — `D`'s *"base clock"* | **14,286,057 Hz**, period 69.9983 ns | **≈200,005 Hz**; the driver's own two derivations both read **200,000** | 推 from two 量 | `CLK-17` |
| `TC0DATA` reload | **142,858** — `0x0022E0A0`, the count field being bits 31:4 | **2,000** — `0x00007D00` | 量 both | `REG-05` |
| system tick | 100.0018 Hz | 100.0 Hz — `200,005 / 2,000` | 量 both | `CLK-04`, `REG-05` |
| watchdog counting clock | **14.9650 MHz ±0.02** | **≈200,180 Hz**, and ⚠️ a four-rung ladder falsified the model it came from — § 14.4 ① | 量 both | `CLK-08b` |
| a jiffy | *(no loader equivalent)* | `NSEC_PER_JIFFY` = 10,000,000 ns = exactly 10 ms, and **讀 it is not computed from `CONFIG_HZ`** | 讀 | `CLK-20` |

🔴 **The two states reach 100 Hz down two different paths**, and that is the
single most useful sentence in this section: the loader divides 14,286,057 by
142,858, Linux divides 200,005 by 2,000. **Both give 100 Hz, so a tick rate that
looks right proves nothing about which state you are in.** `REG-05` and `REG-11`
each have the vendor source that writes the Linux value — `arch/rlx/bsp/timer.c`
with `BSP_DIVISOR 1000` — so each is 量 plus 讀 ×2, and the rewrite happens
before `rtl819x_timer_init`, i.e. the vendor does it, not rlxfw.

⚠️ **`CLK-17` is `推`, not `量`, and the row says so.** Both numbers are derived
from two measured quantities — the tick (`CLK-04`) and `TC0DATA` (`REG-05`) —
and the row warns that `200.0049 / 14` agreeing to six figures is **not**
independent confirmation, because 200.0049 MHz was itself derived from
`tick × 14 × 142,858`. It is the same equation rearranged. ⚠️ And **do not
substitute 14.9650 MHz**: that is `CLK-08b`'s *watchdog* clock, a different
clock on the same die, 4.75 % away, and `CLK-08b` is precisely the row that
refuted treating `f_timer / 14` as the watchdog's rate.

🟢 **The two Linux-side numbers, 200,005 and 200,000, are not a contradiction
and the difference is worth knowing.** 200,005 comes from the measured bus
(`CLK-02` ÷ `CDBR`); 200,000 is what `rtl819x-timer` 2.0 computes at init from
`hz_tick = (TC0DATA >> 4) × HZ` and `hz_cdbr = BSP_SYS_CLK_RATE / (CDBR >> 16)`,
where `BSP_SYS_CLK_RATE` is the 讀 constant 200,000,000. Both derivations agree
with each other (the driver reports `hz_agree 1`), `hz_used` takes the first,
**and the driver needs no clock constant at all**. 🔴 `CLK-24` is why doing only
half of that ships a worse image: the `shift` must be derived too, or
`clocksource_hz2mult()`'s `u32` return silently truncates at 200,000 Hz.

### 8.2 What is above the bus, and it is 未定

🔴 **未定 — the relationship between 200.0049 MHz and 400 MHz.** `CLK-03` `⊘`:
*"not measured; ÷2 is a reading, not a measurement"*. What exists is one
experiment's constraint, not the ratio: 量 `bench/2026-08-25/H1b.timing`, a
reset-to-first-byte interval of **123.7 ms** against three pre-registered
candidates — 130.4 ms (400 MHz at 3 cycles/loop) **survived**, 5.1 % low;
172.3 ms (4 cycles) refuted at 1.39×; 256.2 ms (200 MHz at 3 cycles) refuted at
2.07×. ⚠️ **It measures `f/CPI`, not `f`**: 400 MHz with 6 cycles and 200 MHz
with 3 cycles are indistinguishable, so what survived is the *combination*, and
the 400 MHz itself is still a banner string. `n = 1`.

🔴 **And `CLK-03`'s reopen condition is this very section**: *"a gate wants to
make a claim in CPU cycles, or `P3`'s clock-tree section wants ÷2 written as
量"*. **This section does not write ÷2 as 量.** Separating `f` from CPI needs a
method that does not go through CPI, and this core has no CP0 `Count`
(`CPU-42`), which is why the row was suspended rather than scheduled.

### 8.3 There is no crystal row

🔴 **未定 — the reference oscillator, `CLK-50` 殘留.** 量 by grep over `SPEC.md`:
there is **no value row for a crystal, oscillator or reference frequency** — the
one row that names the oscillator is `CLK-50`, the § 17 entry recording that
absence. `CLK-02` mentions
ordinary crystal tolerance only to explain its own +24 ppm; no source in this
project names the part, the frequency or the multiplier chain that produces
either 400 MHz or 200 MHz. ⚠️ So § 8 is a tree **read downward from the
peripheral bus** and it has no root. What would close it: a package marking on
the oscillator (量, P — a photograph of the board), or a datasheet clock-tree
diagram, neither of which this project holds.

⚠️ **What § 8 does not establish.** `CLK-02`'s ±7 ppm is an interval over one
set of baselines taken from capture mtimes, not a calibrated frequency
standard; `CLK-19` records that whether `TCnDATA`'s period is `N` or `N+1`
counts is **未定 and its size is 7 ppm — exactly `CLK-02`'s own error bar**, so
the fifth significant figure of every rate above is inside an open question.
`CLK-08b`'s loader-state 14.9650 MHz was closed on **two points and two
unknowns** (量 `H3c-D4`, `H3c-D4c`), which is the shape `CLAUDE.md` forbids
taking a constant from, so it is quoted with its interval and never bare. Its
Linux-state 200,180 Hz comes from a two-rung difference that cancels the
unknown offset, `(2²³ − 2¹⁸) / 40,595.876 ms` (`docs/FINDINGS.md`) — 🔴 **but a
four-rung ladder then falsified the model that figure assumes**, so § 14.4 ①
is the row to read before quoting it, and `CLK-08b`'s own `N` mark is `—`.
⚠️ **The integer relation between 14.965 MHz and 200.0049 MHz is 未定**, so the
two clocks on this die are not known to share a divider.

---

## 9. Strapping

`plan` § 6 `P3` section 4 — Strapping, pointing at the draft datasheet's
**§ 6.1, *Configuration upon Power-On Strapping*** (讀 `SOURCES.json`, which
records that section's title and `§ 6.2 Shared I/O Pin Mapping` beside it).
🔴 **This section is a set of readings, not a strap table: no source in this
repository gives a field layout for the strapping register.** Every row is
loader state unless it says otherwise.

### 9.1 Where the straps physically are, and why that closes a door

讀 D § 6.1, owner `notes/power-and-programmer.md` § 3, `SPEC.md` `MEM-09`: the
power-on strapping pins are **the DRAM pins** — `MA[10:8]` on 44/52/53 and
`RAS#`/`CAS#` on 51 — **and not the `SF_*` pins**. ⚠️ That is a useful negative
for a reader with a flash clip in hand: nothing about the straps can be read or
influenced from the SPI flash pins, so the one harness this project owns cannot
reach them. 量 **zero**: no strap pin has ever been probed on this board.

### 9.2 The two strap words this device has returned

| address | reading | state | V | N | owner |
|---|---|---|:-:|:-:|---|
| `0xB8000000` | `0x8196E001` | loader | 量 | 讀 (`8196E`) · 推 (how the version field is cut) | `REG-29`, `CPU-32` |
| *(same dump, word 2)* | `0x00000002` | loader | 量 | **none — the word has no name in any source** | `REG-29` |
| *(same dump, word 3)* | `0x00100200` | loader | 量 | **none** | `REG-29` |
| `0xB800000C` | `0x0000000F` | loader | 量 | 讀 | `REG-30` |

🔴 **The third word's address is an inference, and no file in this repository
but this one states it.** 量 2026-10-05, `git grep B8000008` over every tracked
file outside `upstream/` returns **this file alone**: what is recorded is *word 3
of a `DW B8000000 1` dump*.
`LDR-07` 讀 gives `DW` word semantics — four words to a line, length counted in
words — so the address is `0xB8000008` **推**. ⚠️ Anyone quoting `0xB8000008` is
quoting an inference; the honest citation is `REG-29`'s word 3.

🟢 **And the word is not nameless — the name is in a source this project
already holds, and nothing had connected them.** 讀 the draft datasheet
§ 8.2.9, in `WDTCNR`'s own table, under bit 19 `NRFRstType`: *"This bit has
been taken over by System_Register hw_strap. Offset: 0xB800_0008h~B800_000bh"*.
**So `D` places a register called `hw_strap` at exactly the address of word 3**,
and `SPEC.md` `REG-29` calls that word 無名 — unnamed. ⚠️ 量 2026-10-05 by
`git grep`: outside `upstream/`, `hw_strap` and `NRFRstType` appear only in this
file and in `SPEC.md`'s `REG-40` 殘留, which the commit that landed this file
added, so the link is new here and § 9.5 says what it owes. 🔴 **This does not make the
word's contents known**: D names exactly one field in it, bit 19, the NOR-flash
reset type, and gives an initial value that this unit's reading **does not
match** — which is § 0 ①'s whole point, since D is a draft for a different
variant.

🟢 **The value has a second reading, thirty-four days apart, and `SPEC.md` does
not cite it.** 量: `bench/2026-08-24b/B7b.log` (`DW B8000000 1`, 2026-08-24) and
`bench/2026-09-27d/AL-D01.log` (`DW B8000000 4`, 2026-09-27) return the **same
four words**, and `bench/2026-09-27d/CELLS-A.md` § 5 puts the second at the cold
loader prompt with a gate that fails the capture if it contains `Booting...`,
`---RealTek` or `Linux version`. ⚠️ `REG-29`'s source cell names only `B7b`, so
**this row is `n = 2` and its owner says `n = 1`** — a debt on that cell, still
unpaid on 2026-10-05 and `SPEC.md`'s to pay, not a finding this file may hold.

🟢 **`REG-30` is the one strap on this board whose field, value and consequence
are all established**, and it is worth the space because it is what a strap
reading is *for*. 量 `0x0000000F`: the low nibble is `0xF`. 讀 A, the loader at
`0x80408DE4` takes the alternate button-source path — fetching button state from
`[0x8040DD4C]+0x44` instead of the GPIO — **only when that nibble equals 13**,
so on this unit that branch is dead. 讀 `docs/loader-phy-and-switch.md`: the
same nibble gates a switch-side branch, *"selected by a strap read from
`0xB800000C & 0xF` compared against 13"*, and the whole strap-gated branch is
likewise not taken. **So one 4-bit strap decides two unrelated code paths on
this part, and on this unit both are the not-taken side.**

### 9.3 The software strap, which is the one this project actually uses

量 and 讀, `SPEC.md` `REG-22`, `LDR-21`, owner `docs/mfgtest.md`:
`gCHKKEY_HIT` at `0x8040DBA4` is *"a genuine console-key-at-power-on strap"*.
When ESC is streamed from **before** power-on it reads **`1`**, and
`check_image()` then returns *no image* immediately — the checksum loop never
runs. Its only writer reads `0xB8002014` bit 24 and the top byte of
`0xB8002000` (讀 A), i.e. **the UART**: the strap is a console key, not a pin.
⚠️ This is the mechanism every seating in this project depends on, and it is
also why a `check_image()` result taken during an ESC-interrupted boot says
nothing about the image.

### 9.4 The reset button is not a strap pin, and the timing that matters

量 `BRD-05`, three sources: the front-panel button is a GPIO on `PABCD` bit 5,
active low with a pull-up, **not `RESET#`**. Holding it does not reset the
board (`B7c.log` has no `Booting...` and no banner). 讀 `BRD-06`: the SoC's
`RESET#` is pin 49 and is **shared with `LED_PORT3` and `GPIOB[5]`**, so on this
design it may be an LED drive pin — which is how a reset pin ends up not being
the reset button. ⚠️ `CLAUDE.md`, `FW-62`: a reset-button hold meant to reach
the vendor's timer must be **the boot's first hold over ~2 s**, and the
loader-state `XOR 00000020` for this button must be masked `& 0x20` under Linux,
because the vendor sets bit 6 of `PABCD_DIR` and turns it into a moving output
(`REG-37`, and the whole-word XOR becomes `00000060`).

### 9.5 What § 9 does not establish

🔴 **未定 — `hw_strap`'s field layout and its reset value, `REG-40` 殘留.** 量
2026-10-05 by `git grep` over every tracked file outside `upstream/`:
`hw_strap`, `NRFRstType`, `reg_iocfg` and D § 6.1's own strap-function names —
`ck_cpu_freq_sel`, `ck_freq_sel`, `Bootpinsel`, `DDR_TYPE`, `DRAM_TYPE`,
`External_Reset`, `Sel_40M` — appear in **no file but this one and `SPEC.md`**,
whose hits are the § 17 rows `REG-40` and `NET-170` recording this same
absence. So the layout exists in a document this project holds and **has never
been transcribed**, and `SPEC.md` has **no definition row** for the register —
only `REG-40` 殘留, which says what one needs. ⚠️ The initial value is 文 ×1 from a *draft* for a
*different variant* (§ 0 ②), below the two-source bar, so **this file names the
register and its address and deliberately does not print its initial value** —
doing that needs a new `SPEC.md` row in the same commit (`CLAUDE.md`).

⚠️ **And `MEM-09` is narrower than the source it cites.** It names `MA[10:8]` on
44/52/53 and `RAS#`/`CAS#` on 51 from D § 6.1; **D § 6.1's own table lists more
strap functions than that**, across more pins, and not one of their names is in
any file here. So `MEM-09` is a correct subset, not the strap list.

🟢 **Two strap bits are reported by a register, and reading them is one `DW`.**
讀 D § 7.4.1: `MCR` at `0xB8001000` carries two **read-only** bits that *report
the hardware strapping initial value* — the DRAM type and the boot-flash type.
🔴 **`MCR` has never been read on this device**: 量, `grep B8001000` over all of
`bench/` returns **zero files**, and the only `0xB8001xxx` address any capture
has ever touched is `0xB8001200`, the SPI controller. **So the cheapest
strapping measurement this project has not taken is a single `DW B8001000` at
the prompt**, and it would turn two 推 straps into 量.

🔴 **未定 — the SDRAM timing the loader programmes.** `MEM-08` is `⊘`: *"SDRAM
timing — read the loader's writes to the memory controller"*, suspended
2026-09-30 because no open gate needed it. ⚠️ **It is cheaper than its row
implies, because the writes are already located**: 讀
`docs/loader-command-semantics.md` records that **stage 1.5 holds a literal
register table containing `b8001050` and `b8001008`**, and 量 by `git grep`,
**no file decodes that table's contents** — nor does any file name the registers
D puts at those offsets. ⚠️ Its reopen condition is *"`P3`'s
known-good-register section wanting to list it"*; § 15.5 lists it **as an
address with no reading**, which is what a census of readings can honestly say,
and § 16.3 hands the decision to the gate board.

⚠️ **One reading is not a strap, in either direction.** Nothing above
distinguishes a bit that a strap pin set from a bit the loader wrote before the
prompt was reachable. `CLK-11`'s method — searching the loader binary for every
writer of an address, with a positive control that finds a write the device has
confirmed — is the technique that would separate them, and it has not been run
on `0xB8000000` or `0xB800000C`.

---

## 10. Pinmux

`plan` § 6 `P3` section 5 — Pinmux 表, pointing at the draft datasheet's
**§ 6.2 *Shared I/O Pin Mapping*** beside § 6.1 (讀 `SOURCES.json`). 🔴 **This
is a reading of the two mux words, not a pin table**: no source in this project
decodes which bit selects which pin.

### 10.1 The two words, and the state column that is not the usual one

| register | address | reading | states read | V | N | owner |
|---|---|---|---|:-:|:-:|---|
| `PIN_MUX_SEL` | `0xB8000040` | **`00000006`** | all three, identical | 量 | 讀 | `NET-162`, `NET-134` |
| `PIN_MUX_SEL2` | `0xB8000044` | **`00000000`** | all three, identical | 量 | 讀 | `NET-162` |

⚠️ **"Three states" here is not loader against Linux, and the letters are not
defined in the row that uses them.** They are `NET-160`'s hand-over ladder,
defined in `notes/switch-driver.md` §§ 16.1–16.2: **L** — the cold loader
prompt; **V** — vendor-configured Linux, after the vendor's probe and before any
rlxfw write or interface open; **R** — after `reset vendor`. 🔴 **`L` is the
loader prompt and `V`/`R` are Linux**, so this *is* a loader-against-Linux
comparison — it just happens to come out equal. ⚠️ And `NET-162`'s `V` collides
with `SPEC.md`'s `V` mark column, which is a reading hazard rather than an
error.

🟢 **Four readings, two instruments, two power-ons.** 量: `L` is
`bench/2026-09-27d/AL-D02.log` (`DW B8000040 4` at the prompt); `V` and `R` are
`bench/2026-09-28/AV-P15.log` and `AR-P15.log` through `/proc/rtl819x-view`'s
`peek`; and the `V` state was read a **second** time by a different instrument,
the vendor's own `/proc/rtl865x/memory` (`AV-M18.log`). `L` is a different
power-on from `V`/`R`. **This was the first time either word was read on this
die**, and two stale sentences predate it — `notes/switch-driver.md` saying the
pair *has no reading at all*, and `rtl819x-view.c`'s comment *No reading on this
die yet*.

⚠️ **The `L` dump returned four words and the last two are unowned.** The line
reads `00000006 00000000 2702DFF1 0A8D8ED0`, so `0xB8000048` and `0xB800004C`
have 量 readings and **no name, no owner and no `SPEC.md` value row** — the same
shape as § 9.2's words 2 and 3, and `REG-40` 殘留 names both among the
neighbours its desk read would settle.

🟢 **The names are 讀 and they came from a committed instrument rather than from
a guess.** `tools/hdrcensus.py` (in CI since 2026-09-17) reads the register
header the build tree **actually compiles** —
`drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h` — and `NET-134` records
that `0xB8000040` is `PIN_MUX_SEL` there; `rtl819x-view`'s own table carries
both words with `B :3115-:3116` and `D` Tables 35–36 as the two sources.
⚠️ `CLAUDE.md`'s rule applies and was satisfied: the header consulted is the one
in the tree that builds.

### 10.2 🟢 Three writers, and all three are no-ops on this unit

**This is the useful result of § 10, and it is a measurement rather than a
reading of code.** Three pieces of code write these words, and the measured
values say none of them changes anything here:

* 讀 `REG-35`: the vendor's `rtl_gpio_init` ORs `0x6` into `0xB8000040` at
  `device_initcall`. 量 the word already reads `00000006` in the **L** column —
  **so the OR is idempotent on this unit.**
* 讀 `rtl865x_asicL2.c:4568`–`4569`: the vendor clears `~0x8F18` from
  `PIN_MUX_SEL` and `~0x3B6DB` from `PIN_MUX_SEL2`
  (`docs/blind-write-ledger.md` records both as vendor rows). 量 **neither
  value changes** across `L` → `V`.
* rlxfw's `8d` build writes neither word (讀, `NET-162`).

🔴 **So on this board the pin mux is whatever the loader left, and nothing after
the loader moves it.** That is worth stating because it is the opposite of the
usual bring-up assumption — and because it means a pinmux bug on this part
would have to be chased in `stage2.bin`, not in Linux.

### 10.3 What § 10 does not establish

🔴 **未定 — the field layout, `NET-170` 殘留, and 量 2026-10-05 by `git grep`
the token `reg_iocfg` — the prefix D uses for every field in these two words —
appears outside `upstream/` only in this file and in `SPEC.md`'s § 17 rows that
record its absence.** So `00000006` means bits 1 and 2 are set and **nothing in
this repository says which pins those bits select.** The datasheet has
Tables 35–36 for it, cited by `rtl819x-view`'s own table, and the layout has
never been transcribed. The row is a value with a name and no decode.

🔴 **推, with its refutation condition, because it would explain another row.**
If D Table 35's lowest field is the three-bit JTAG/UART1/GPIO selector that its
field names suggest, then `00000006` selects **GPIO** on those pins — which
would explain `BRD-11`, where the datasheet promises a 5-signal EJTAG and **the
board has never had one located on it**. ⚠️ **This is 推 on a 文 ×1 source for a
different variant and nothing here has tested it.** The refutation is cheap and
is a desk read: transcribe D Tables 35–36 into a `SPEC.md` row, with the vendor
header's own bit masks as the second source — the clears of `~0x8F18` and
`~0x3B6DB` are already 讀 and between them name a dozen bit positions. **Until
that row exists, § 10 states the values and not the decode.**

⚠️ **Two 讀 sources that agree can still be one source.** The header is Realtek's
and the datasheet is Realtek's; `CPU-04`'s three recorded weaknesses are the
worked example of what that costs. What makes these two rows stronger than that
is the **量** — the words were read on the die, three times each.

⚠️ **Related, and not the same thing:** `NET-162` read `PCRP7` `1C7F0038` and
`PCRP8` `207F0038` in the same three columns with `EnablePHYIf` clear, and
`PCRP8` had **never been read on this die** before. Those are switch port
registers, not mux words; § 15.3 has the `PCRP0`–`PCRP4` loader-state row and
`NET-162` owns the rest.

---

## 11. Memory map

`plan` § 6 `P3` section 6 — 記憶體映射. **Three kinds of address appear below
and they are never mixed in one column**: a **KSEG** virtual address (what code
dereferences), a **physical** address, and a **flash offset** (what a
programmer or the loader's `FLR` addresses). `SPEC.md` § 8 owns the first two
and `SPEC.md` § 13 owns the third.

### 11.1 The address space, as code sees it

| address | what is there | V | N | owner row |
|---|---|:-:|:-:|---|
| `0x80000000` | KSEG0 — cached RAM | 文 | 文 | `MAP-01` — ⚠️ **no file in this repository owns this row**; `spec-check` C5 is how that was found |
| `0xA0000000` | KSEG1 — uncached alias. **The loader runs here**: at `0x804004a8` it jumps to the KSEG1 alias of its own next instruction | 讀 | 讀 | `MAP-02`, `notes/cache-model.md` |
| `0xB8000000` | SoC peripheral register space | 讀 | 讀 | `MAP-03` |
| `0xB8001000` | memory controller `MCR` | 讀 | 讀 | `MAP-04` — 🔴 never read on this device (§ 13) |
| `0xB8001200` | SPI flash controller | 讀 | 讀 | `MAP-05` — **three sources** |
| `0xB8002000` | UART; DLAB switches at `0xB8002100`/`2000` | 讀 | 讀 | `MAP-06` — one register in `0xB8002000`–`0xB80020FF` has been read here, the loader-state `LCR` (§ 13.2) |
| `0xB8003000` | interrupt controller | 讀 | 讀 | `MAP-07` |
| `0xB8003100` | timer / watchdog | 讀 | 讀 | `MAP-08` |
| `0xB8003500` | GPIO — `PABCD_CNR` `3500`, **`3504` unnamed**, `PABCD_DIR` `3508`, `PABCD_DAT` `350C` | 文 · 量 | 讀 | `MAP-09`; `3504`'s first reading is `REG-36` |
| `0xB8B01000` | PCIe host mode. **Not a network MAC** | 文 | 讀 | `MAP-10` |
| `0xBB804000` | switch core | 讀 | 讀 | `MAP-11` |
| `0xBD000000` | the SPI flash's memory-mapped window, KSEG1 | 量 | 讀 | `MAP-12` — § 11.3 is the evidence, which was re-pointed twice |
| `0xBFC00000` | reset vector — `J BFC00000` *is* the reset command | 讀 | 讀 | `MAP-13` |
| `0x80400000`–`0x8040DD10` | the loader's own image and `.data`; `.bss` from `0x8040DD10`, stack below it | 讀 | 讀 | `MAP-14` — the load base was recovered from a pointer sequence, not assumed |
| `0x80500000` | where this unit's kernel image is staged — its own container header's `startAddr` | 量 | 讀 | `MAP-15` |
| `0x81000000` | *(chosen)* bench scratch, 16 MiB into SDRAM | — | — | `MAP-16` — 🔴 **the reason for the choice was refuted**: `C7-pre` read a live descriptor table at `0x81000400` |
| `0x80A00000`–`0x80AF1002` | *(chosen)* upload address and canary, above the staged kernel's end (`0x805F1002`) and below the 16 MiB structures | — | — | `MAP-17` |

🔴 **`MAP-16` is the worked example of why a chosen address is not a safe
address.** It was picked to be far from the loader and the staged kernel, and a
pre-read found live data in it anyway. `CLAUDE.md`'s rule that a `FLR`
destination must be pre-read, and that DRAM survives a power cycle (`MEM-17`),
is the generalisation of that one reading.

⚠️ **The loader runs uncached and that is not a detail.** `MAP-02` 讀: the
loader jumps to the KSEG1 alias of its own next instruction, so every loader-state
reading in this document was taken with the caches out of the picture, while
every Linux-state reading was not. `notes/cache-model.md` owns the consequence.

⚠️ **Four rows in that table have an ownership problem, and it is visible rather
than fixed.** `MAP-01` **has no owner file at all** — `spec-check`'s C5 is how
that was found. `MAP-03`'s owner is in `plan/`, which is gitignored, so it cannot
be checked in a clone. `MAP-07` and `MAP-08` point at `SPEC.md` § 10 rather than
at a file. And **`MAP-04` and `MAP-10` have the draft datasheet as their only
source** — `MAP-10` is marked 文 accordingly, while `MAP-04` is marked 讀 though
`SPEC.md` § 0 files that source under 文. Per § 0 ②, both are statements about a
family.

### 11.2 The flash map, by offset

量/讀 over the 2026-08-16 dump of this unit; `SPEC.md` § 13 owns every row and
`upstream/notes/flash-layout.md` is the finding. **Offsets, not addresses** —
flash offset `N` is visible at KSEG1 `0xBD000000 + N` (`notes/rlxboot.md` § 2).

| offset | what is there | length | V | owner |
|---|---|---:|:-:|---|
| `0x000000` | boot loader, MIPS code: `0b f0 00 04` is a `j`, then the chip-id compare | — | 量 | `FLM-01` |
| `0x006000` | 🔴 **`H601`** — this unit's MAC and RF calibration. **Permanently write-forbidden**, and no reset restores it | — | 讀 | `FLM-02`, `RF-06`, `CLAUDE.md` |
| `0x008000` | `COMPDS`, factory defaults | `0x1D39` (7,481) | 讀 | `FLM-03` |
| `0x00A000` | written zeros — **allocated, not the erased state** | — | 讀 | `FLM-04` |
| `0x00C000` | `COMPCS`, current settings (this is `config.dat`) | `0x1D36` (7,478) | 讀 | `FLM-05` |
| `0x00E000` | written zeros | — | 讀 | `FLM-06` |
| `0x010000` | `w6cg` header + bzip2 web assets | `0x043A14` (277,012) | 讀 | `FLM-07` |
| `0x053A24` | filler, one repeated value | 50,652 | 讀 | `FLM-08` |
| `0x060000` | `cr6c` header + kernel; the header's `startAddr` is `0x80500000` | `0x0F1002` (987,138) | 讀 | `FLM-09`, `MAP-15` |
| `0x060028` | the kernel's self-decompress stub — `3c 10 80 5f` is `lui s0,0x805f` | — | 讀 | `FLM-10` |
| `0x151012` | filler, one repeated value | 192,494 | 讀 | `FLM-11` |
| `0x180000` | SquashFS 4.0 / LZMA, **no container header**, so it must land exactly on a partition boundary | used 1,876,033 | 讀 | `FLM-12` |
| `0x34A041` | image end — **3.29 MiB**, which the public spec's 2 MB cannot hold | — | 讀 | `FLM-13`, `PUB-03` |
| `0x350000`–`0x3FFFFF` | erased, all `FF`, the whole tail | — | 量 | `FLM-14` |

⚠️ **`FLM-07`'s and `FLM-09`'s lengths exclude the 16-byte container header.**
`FW-12` 讀: `IMG_HEADER_T` is 16 bytes big-endian — `signature[4]`, `startAddr`,
`burnAddr`, `len` — and this unit's `cr6c` extent on flash is
`987,154 = 16 + 987,136 + 2`, the two trailing bytes being what zeroes
`LDR-18`'s halfword sum. **`J 80500000` receives the payload, not the file**,
which is why the staged kernel ends at `0x805F1002`.

🟢 **The device reports its own partition table, and it is a second source for
the offsets — but not for the erase geometry.** 量 2026-10-04 under Linux
(`FW-187`): `mtd0 00130000` *boot+cfg+linux* = `0x000000`–`0x12FFFF`;
`mtd1 002d0000` *root fs* = `0x130000`–`0x3FFFFF`; `mtd2 00400000` the whole
4 MiB; `/proc/partitions` agrees at 1216 / 2880 / 4096 KiB. 🔴 **All three report
`erasesize 00001000`, and that is a software constant, not a chip
measurement** — the kernel's chip table has no `1c7016` entry, so 4 KiB is the
**fallback** sector size (`FLS-23`). **The erase block being 4,096 or 65,536
bytes is 未定** (`FW-187` 殘留, `FW-191` 殘留, gate `R8b`), and `FW-191`'s
identification of the part did not settle it.

⚠️ **The vendor's layout and the kernel's MTD view must not be merged.** The
vendor `cr6c` extent `0x060000`–`0x151011` **crosses** the `mtd0`/`mtd1`
boundary at `0x130000`, and SquashFS at `0x180000` is **not** at `mtd1`'s start.
A tool that writes a vendor-layout region through one MTD device is writing
across a boundary.

### 11.3 🔴 `MAP-12`'s evidence was re-pointed twice, and the window has never been read at the loader prompt

**Worth its own subsection because the value never changed while its support
changed twice**, and both rejections are the useful part.

* ✗ **Rejected 2026-08-31.** The loader's `FLW` print of `0xbd3f0000` is a
  **compile-time constant** — `lui 0xbd00` occurs exactly once in the loader,
  inside that `printf` — not a reading.
* ✗ **Rejected 2026-09-07.** `FW-34`'s 4,194,304-byte read went through
  `mtd_spi_read` programmed I/O, **not through this window**.
* 🟢 **What supports 量 now, in two states.** Bare metal: `probe3` Group F,
  seating 8 — 1,024 uncached loads via `0xBD000000`, stride 4 and stride 1,024
  both 30,354 ticks, `R = 1.0000`, with `faults`, `alias` and `live` controls.
  Linux: 2026-09-08, `rtl819x-spi`'s `verify` walked all 4,194,304 bytes and the
  window matched the PIO path byte for byte, **with a negative control that
  fired** — injecting one byte at 1,048,576 moved `cmp_first_diff` there and
  flipped `cmp_equal` 1 → 0.
* 🔴 **Never accessed at the loader prompt.** The loader's own `FLR` reads
  through `SFDR` programmed I/O (`LDR-42`), so **loader-state decode of this
  window is unmeasured**, and `notes/rlxboot.md` § 10 says the same for
  `0xBD3F0000` specifically — 4,128,768 bytes into the window, 4,124,672 past
  the end of the 4,096 the bare-metal cell covered, and where *erased* and
  *undecoded* both read `ctr=0`.

### 11.4 What § 11 does not establish

⚠️ **The flash rows describe the reference dump, not the live part.** `FLS-26`
量 found the live flash differing from that dump at `[0x9000, 0xA000)` and
`[0xD000, 0xE000)`; § 14.5 is the row. Its final accounting, seating 18 on
2026-09-09, is **4,177,920 B (99.61 %) proven the same as the dump, 8,192 B
(0.195 %) proven different and 8,192 B (0.195 %) undetermined** — the last being
`H601`, skipped by rule. *Proven the same* is a digest match: it cannot see two
writes that cancel, and no whole-part `FLR` re-read was run.

⚠️ **No row here states a physical address.** Everything is KSEG0, KSEG1 or a
flash offset. The physical numbers this project has are elsewhere: the kernel's
own map `memory: 02000000 @ 00000000` (量, Linux) and `FW-34`'s
`0x1FC00000`/`0x1D000000` decode comparison.

⚠️ **`MAP-16` and `MAP-17` have `V = —`**: their value cell carries 選定
(*chosen*), which `SPEC.md` § 0 treats as not a value to be measured. Neither is
an independent source for anything — `MAP-17`'s bound is `0x80A00000` plus the
same `0x0F1002` that `FLM-09` gives.

⚠️ **`MEM-06`'s 26,052 kB is the *vendor* kernel's `MemTotal`.** rlxfw's own
kernel reports **26,984 kB** (`MEM-19`, `MEM-20`), and `TGT-09` budgets RAM
from the vendor figure. Quoting one for the other is a 932 kB error.

## 12. Boot flow

`plan` § 6 `P3` section 7 — 開機流程. **Every number is labelled with the stage
it belongs to and the reset class it was taken in** (cold = after a power press,
warm = a reset with no power cycle). `docs/boot-time-table.md` §§ 2–5 own the
per-class tables and `tools/boot-timeline.py` is the instrument; this section
owns the *order* and points at them.

🔴 **The stage boundary is not where the console text suggests.** 量 2026-08-25:
the string `Booting` occurs **zero** times in `stage2.bin` and once in the 4 MiB
dump at flash offset `0x3DE`; **`Booting...` is printed by stage 1**, at
`0xBFC003A4`–`0xBFC003D0`, by a byte loop that does not poll `THRE`. So the
first console line of every boot comes from the ROM-resident stage, and the
≈350 ms after it is stage 1 **loading stage 2** — not a jump to the kernel.
`CLK-15` owns that interval. ⚠️ Stage naming is not uniform across this
repository: `LDR-02` puts `stage2.bin`'s load base at `0x80400000` while
`notes/kernel-build.md` § 19.7.1 annotates stage 1's `jr` into `0x80100000` as
*into stage 2*, and `docs/loader-command-semantics.md` § 10 names an undefined
*stage 1.5*.

### 12.1 The stages, in the order the console shows them

| # | stage | what it does on this part | state | owner |
|---:|---|---|---|---|
| 0 | reset / stage 1 | runs from the reset vector `0xBFC00000`; prints **`Booting...`**; then its copy loop at `0xBFC001D0`–`0xBFC001EC` moves flash `0x0004F0`–`0x0056AB` — **20,924 bytes, 5,231 iterations** — one word at a time into RAM, every instruction and every source word an **uncached KSEG1 read of memory-mapped SPI NOR**. That copy is the dominant term of the ≈350 ms | loader | `CLK-15`, `MAP-13` |
| 1 | stage 2 — the `<RealTek>` loader | `stage2.bin`, 56,592 bytes, `sha256 f88869d1…c9c1b4ee`, load base `0x80400000`. Prints `chipName:` … `ramSize: 32M`, then the banner | loader | `LDR-02`, `MAP-14` |
| 2 | reset-cause line | immediately **after** `ramSize: 32M`: **`Reboot Result from Watchdog Timeout!`** on a warm reset, **a single space** on a cold power-on | loader | `CLK-13` |
| 3 | image location | **it scans**: flash `0x010000`, `0x020000`, `0x030000` fixed, then `[0x030000, 0x060000]` in `0x10000` steps skipping those three — six kernel candidates, and **this unit's kernel is at `0x060000`, the last one tried** | loader | `LDR-17` |
| 4 | image check | `check_image()` at `0x80407D50`: signature `cs6c` → 1, `cr6c` → 2, then a 16-bit halfword sum over the **RAM copy** which must be zero; only `2` satisfies the caller | loader | `LDR-18` |
| 5 | staging | `check_image()` itself copies flash `0x060010` to `0x80500000` **before the ESC window and before any `FLR`**, the destination read out of the flash header (`jal 0x80404f38` at `0x80407E44`) | loader | `LDR-22`, `MAP-15` |
| 6 | ESC window | `doBooting()` at `0x80408690` calls `user_interrupt(0x3B023380)`. On ESC: prints `---Escape booting by user`, sets `GIMR0 = 0`, enters the `<RealTek>` prompt. Without ESC: `goToLocalStartMode()` and `Jump to image start=0x80500000...` | loader | `LDR-15`, `LDR-20` |
| 7 | kernel self-decompress | the `rtkload` stub: `decompressing kernel:` → `done decompressing kernel.`, then `start address: 0x…` | decompress | `docs/boot-time-table.md` § 2, `FLM-10` |
| 8 | kernel init | the three interrupt domains come up in `rlx_cpu_irq_init`, `rlx_vec_irq_init`, `bsp_ictl_irq_init`; `bsp_timer_init` reprogrammes `CDBR` and `TC0DATA` **before** `rtl819x_timer_init`, so § 8's Linux column is the vendor's doing | Linux | `IRQ-05`, `REG-05`, `REG-11`, `docs/interrupt-map.md` § 3.5 |
| 9a | userspace, the vendor's image | BusyBox `init` → `rcS`, and 讀 `FW-04`: the compiled-in command line is `console=ttyS0,38400 root=/dev/mtdblock1` with **no `init=`**, and the string `Kernel command line` is absent so the boot log never prints it | Linux | `FW-04` |
| 9b | userspace, rlxfw's image | 量 2026-09-30, image `r78a` from RAM (`R7`): **PID 1 is rlxfw's compiled `/init`**, and `ps` reads `brokerd` as root, `httpd` under user `httpd`, `dnsfwd` under `dnsfwd`, and `udhcpd` and `sh` as root. The boot prints `rlxfw: lan up, rlx0 10.1.1.1/24`, `httpd: uid=100 gid=100 root=/srv/www …`, `brokerd: listening on /srv/www/run/broker.sock mode 0666`, `dnsfwd: running as uid 101 gid 101; setuid(0) refused (Operation not permitted)` — the drop checked by trying to undo it — and two `*** BENCH PROFILE: A ROOT SHELL IS ENABLED ON /dev/console ***` lines. The order `/init` works in — console, rung-1 discriminator, signals, mounts, config store, hostname, LAN, `udhcpd.conf`, then the child table — is 讀 from its source | Linux | `FW-175`, `FW-181`, `docs/GATE-RESULTS.md` entry 17; the design is `notes/init.md` § 2 |

⚠️ `CLAUDE.md`, `FW-37`: a reset must be `busybox reboot -f` — a watchdog bite —
because plain `reboot` signals PID 1, **which on the vendor image is a shell
script**.

### 12.2 The timings, with their state, class and population

| quantity | value | state / class | owner |
|---|---|---|---|
| `Booting...` → `chipName:` (stage 1 loading stage 2) | 🔄 **cold 325.9–358.3 ms (n=18, mean 350.0, range 9.2 %) · warm 338.2–357.2 ms (n=11, mean 343.6, 5.5 %)** | loader, both classes | `CLK-15` |
| cold-only silence **before** `Booting...` | 0.349 / 0.340 s (n=2), from the CP2102's framing artifact byte — the moment the line is driven. **A warm reset has neither the artifact byte nor the gap** (0.001 / 0.010 s) | loader, cold | `CLK-14` |
| reset → first console byte | **2.07 ms** exact (`D1`, `J BFC00000`, same capture); then n=27 at **1.7–2.8 ms, mean 2.4 ms** | loader, warm | `CLK-14` |
| power-on → a typable `<RealTek>` prompt | 🔄 **2.095–2.315 s (n=15, range 0.220 s, largest gap 0.075 s)**, measured from `Booting` | loader, cold | `CLK-18` |
| the ESC window | **~4.886 s** banner → `Jump to image start`; ⚠️ **not reconciled** with this repo's own 5.036 s warm / 5.210 s cold (n=1 each) or the RAW-clock 5.2388 / 5.2378 (n=1 each) | loader | `LDR-15`, `docs/boot-time-table.md` § 2 |
| kernel decompress | vendor 1.0601 s · rlxfw quiet 1.2180 s · rlxfw loud 1.2481 s (medians, RAW clock) | decompress | `docs/boot-time-table.md` § 2 |
| kernel entry → userinit | vendor 7.0980 s · rlxfw quiet 9.4455 s · rlxfw loud 11.1556 s (cold medians) | Linux | `docs/boot-time-table.md` § 2 |
| userinit → ready | vendor **18.68 s** (`boa: starting server`) · rlxfw **0.1166 s** (first shell prompt) | userspace | `docs/boot-time-table.md` §§ 2, 5 |
| watchdog timeout, `OVSEL` 8 | 41.9 s — a pending bite keeps the console **silent** until it fires | Linux | `CLAUDE.md`, `notes/watchdog-driver.md` |

🔴 **Three traps live inside that table, and quoting a number without them is
how this project has been wrong before.**

**① `CLK-15`'s two ranges used to be disjoint and now overlap.** The published
n=7/n=7 pair had cold strictly slower than warm; the 2026-08-31 re-run over all
of `bench/` made it n=18/n=11 and **the per-sample rule no longer holds**. ⚠️
And the population's *definition* changed in a way a count cannot show: three of
the four new cold samples followed only minutes of power-off, where every
earlier cold sample was a seating's first power-up after hours or days — **and
there is no monotonic relation** (17.72 h off gave the fastest 325.9 ms; 35.1 min
off gave the slowest 355.4 ms). So this is **a new variable nobody has
separated**, not a clean refutation. The mean gap, 6.4 ms, survives.

**② The anchor is part of the definition.** Four defensible start bytes for that
silence differ by up to 1.7 ms, and only **the NUL after `Booting...\r\n` →
the first byte of `chipName:`** reproduces the published numbers;
`tools/test-boot-timeline.sh` `B1` requires the other three anchors **not** to
match, so that *anchor C is the one in use* is measured rather than assumed.
⚠️ Two loose ends are not hidden: **who writes that NUL is 未定** (the byte loop
exits on it), and the within-class scatter is still unexplained.

**③ Every figure here is a host arrival stamp, and the host clock moved.**
Seating A used `CLOCK_MONOTONIC`, measured slow at r = 0.9726–0.9861; seating B
used `CLOCK_MONOTONIC_RAW`, and the `docs/boot-time-table.md` figures quoted
above are the RAW column. `CLK-31`: `loader.booting` drifted **9.7 %** across
sixteen seatings. ⚠️ **Prefer the RAW column and treat older millisecond values
as unverified**, and note that intervals anchored on `J` read short because
`J`'s own stamp is 0.9–6.8 ms late. 🔴 **Nothing stamps the power press**, so no
figure here is referenced to power-on; a `.meta.json`-derived interval carries
±1 s.

🟢 **The reset cause is printable, and nobody had read it for weeks.** `CLK-13`:
both directions were already on disk — every `A-catch.log` since 2026-08-24
lacks the line, every warm reset has it — and it became the only observable for
*a watchdog reset happened* once `REG-12`'s `WatchDogIND` turned out not to read
back `1` on this die (`REG-12` 殘留 `⊘`). 🟢 It reads a **hardware** bit, not a
software flag: the watchdog was armed by `EW` from the prompt, the loader ran no
instruction afterwards, and the line still appeared. ⚠️ The row's own sample
count is internally inconsistent — its prose says six, it names seven captures,
and its source cell says 量 ×3.

### 12.3 The three places this flow is hostile

🔴 **① The ESC window has no grace, and the loader's own reasoning about it was
wrong.** `LDR-15`: it is open from power-on, so an attempt that starts after the
banner has already lost. `LDR-16` 量 ×3: a queued ESC then **poisons the next
command**, which answers `Unknown command !` — so a bare CR is sent first to
re-read the prompt. ⚠️ And `docs/loader-command-semantics.md` § a's 推 that
*the ESC window is the one in `doBooting` and nowhere earlier* is **contradicted
by two 量**: `B5` found `gCHKKEY_HIT` = 1 with ESC streamed from before power-on,
and `A2` saw no `---Escape booting by user`. **§ a was not amended**, so a reader
of that section needs this paragraph.

🔴 **② A bad image goes straight to a rescue prompt, silently.** `LDR-20`,
`doBooting()` at `0x80408690`: flag 0 sets `GIMR0 = 0` and calls
`goToDownMode()` **without waiting for ESC and without printing anything**.
`LDR-19`: the check is silent rather than missing — this build has
`no sys signature at %X!`, `sys checksum error at %X!` **and**
`no rootfs signature at %X!` compiled out, keeping only
`rootfs checksum error at %X!` (`0x8040AF50`) and `burn()`'s
`imgage checksum error at %X!` (`0x8040A7C7`). ⚠️ `LDR-19`'s own prose says
*two* rootfs sentences; **its owner file lists one, and the owner wins**.
⚠️ **And a corrupted image actually reaching the prompt has never been measured
on the device** — it is 讀 only, and the test is a precondition of `R8b`.

🔴 **③ `check_image()` stages the kernel before any `FLR`, and it does it again
after a warm reset.** `LDR-22`: the copy runs inside the check, at
`0x80407E44`. 量: a second `J 80500000` in the same power cycle printed
`decompressing kernel:` again — **so a payload cannot be run twice in one power
cycle without re-uploading**. `CLAUDE.md`'s rule follows directly: *before
`J 80500000`, read back the staged head, because a reset re-stages that address
from flash*. And `MEM-17` 量 is the other half — DRAM survives a power cycle, so
a pre-read that equals flash proves nothing.

### 12.4 What § 12 does not establish

⚠️ **Decompression is not the 350 ms, and that was settled by measurement rather
than argument.** The same LZMA parameters took **1.0132 / 1.0233 s** to expand
976,877 → 3,374,772 bytes, which scales to **17.1 / 18.1 ms** — about 5 % of the
interval. DRAM read-window training (`0xBFC001FC`, ≤32 loops) and the BSS clear
are each under 2 ms. ⚠️ An earlier guess of *DRAM init / calibration* was wrong
and is recorded as wrong.

⚠️ **The mechanism of cold-against-warm is 未定.** The candidates named are the
SPI NOR controller's divider differing between a cold power-up and a
watchdog/ROM reset, and the NOR part's own power-on wake. **The deciding
experiment costs no bench time**: read `SFCR` and its three neighbours once after
a cold boot and once after a warm reset and compare — two `DW`s, zero risk.
⚠️ `CLK-15`'s two `⊘` residuals were parked out of scope on 2026-09-30, carrying
a 推 that the old scatter was the host clock; on the RAW clock warm reads
0.356060 s (n=13) against cold 0.355865 s (n=12), **so cold is not slower** —
and that comparison is unverified.

⚠️ **No instruction of stage 0 has been disassembled in this project.** The
stage-1 UART setting is 讀 ×2 and 量 once at the loader prompt — `LCR` reads
`0x03000000`, 8N1 (`FW-70`, § 13.2); Linux's own `LCR` is 讀 only.

⚠️ **`loader.esc` is `n = 1` in each class** and `docs/boot-time-table.md` calls
it *not stable*. `FW-04` is single-source (C) and describes the **vendor**
kernel, not rlxfw's.

⚠️ **Stage 9b is two boots from RAM on one day** — `r78a`, `RLXFW-ID0`
`BF182DE2`, then its rebuild, `0E45C61D` — and no rlxfw userspace has started
from flash. The privilege separation's refusal half was never returned on the
board: the only peers in those captures are in the authorisation table, so a
refusal rests on the host's matrix (`docs/GATE-RESULTS.md` entry 17, claim ②).

---

## 13. Peripheral census

`plan` § 6 `P3` section 8 — 周邊盤點. **State: every row says which state it
was read in.** § 13.1 below is the 2026-10-04 reading, kept where it was
written because `SPEC.md` `FW-193` names it as its owner.

### 13.0 The blocks, and what each one has shown on this die

A block is listed here if this project has read a register in it or run a
driver against it. ⚠️ **The population is "what has been touched", not "what
the part has"** — `NET-35` records the same limitation for the switch
registers, where the population is *what the loader wrote*, not *what
configures a switch*.

| block | base | state(s) read | what has run against it | owner |
|---|---|---|---|---|
| chip id | `0xB8000000` | loader | three words read; the loader's own log prints `chipName: UNKNOWN` beside them | `REG-29`, `CPU-32` |
| pin mux | `0xB8000040` | loader + Linux (three columns) | read only; nothing writes it | `REG-35`, `NET-162` — § 10 |
| memory controller `MCR` | `0xB8001000` | **none** | 🔴 **never read on this device**; its settings are `MEM-08` `⊘` | `MEM-07` |
| SPI flash controller | `0xB8001200`–`0x1210` | loader + Linux, **and they differ** | `rtl819x-spi` + MTD, 4 MiB read checked against the loader's own `FLR` | `REG-13`, `REG-38`, `REG-39` |
| CPU-port DMA engine | `0xB8010000` | Linux | `rtl819x-nic`; descriptor layout closed on the die | `NET-32`, `NET-49` |
| interrupt controller | `0xB8003000`–`0x3014` | loader + Linux, **and they disagree completely** | `GIMR`/`GISR`/`IRR0`–`IRR3`; 119,818 deliveries counted, 0 spurious | `REG-01`–`REG-04`, `REG-32`, `REG-33`, `IRQ-07`, `IRQ-08` |
| timer / counter | `0xB8003100`–`0x3118` | loader + Linux | `rtl819x-timer` — clocksource and clockevent; the system tick is rlxfw's | `REG-05`–`REG-11`, `CLK-26`, `CLK-27` |
| watchdog | `0xB800311C` | loader + Linux | `rtl819x-wdt`; the board has been reset by it | `REG-12`, `CLK-07`–`CLK-10` |
| GPIO `PABCD` | `0xB8003500`–`0x350C` | loader + Linux, **CNR and DIR differ** | `rtl819x-gpio`, upstream `leds-gpio` (light 量), `rtl819x-keys` (polled) | `REG-26`–`REG-28`, `REG-35`–`REG-37`, `BRD-13` |
| UART | *(see § 11's `MAP-06`)* | loader + Linux | the console itself, 38400 8N1 量 | `BRD-10`, `notes/console-link.md` |
| switch — port control | `0xBB804100`–`0x4144` | loader + Linux | `rtl819x-switch`; MIB counters agree with Linux netdev counts | `REG-15`–`REG-19b`, `NET-33`, `NET-46` |
| five PHYs via MDIO | MDIO addresses 0–4 | loader (量, the loader's `MDIOR`) | `rtl819x-switch` 1.3 registers the `mii_bus` named `rtl819x-mdio` and sends **no MDIO command at boot** — 🔴 so **rlxfw has never read a PHY id** (§ 13.1) | `NET-05`, `NET-06`, `NET-24`, `NET-39`, `NET-135` |
| radio RTL8188ER | *(未定)* | **none** | 🔴 **nothing**: how it attaches to the SoC has never been traced | `RF-04` `⊘` |

🔴 **`RF-04` is `⊘` and is not reopened here.** Its recorded reopen condition is
*"`R10d`, or any work touching the radio, reaching the gate board — or `P3`'s
peripheral-census section wanting to list it"*. This table lists the radio as a
block with **no reading in any state**, which is the honest entry for a census;
whether that counts as the reopen trigger is the gate board's call and § 16
carries it as an open item. The radio's own identification is `RF-01`, also
`⊘`, and also single-source.

### 13.0.1 The interrupt domains, because a census that omits them is wrong

讀 `arch/rlx/bsp/bspchip.h` and `arch/rlx/include/asm/mach-generic/irq.h`,
owner `docs/interrupt-map.md` § 1. **`NR_IRQS` is 48 = 8 + 8 + 32**, in three
domains that are masked in three different places:

| Linux IRQ | domain | the mask lives in | instruction |
|---:|---|---|---|
| **0 – 7** | CPU | `Status.IM`, bit `8 + n` | `mfc0` / `mtc0` |
| **8 – 15** | LOPI | **`ESTATUS[23:16]`**, bit `16 + (n − 8)` | **`mflxc0` / `mtlxc0`** |
| **16 – 47** | ICTL | **`GIMR`** bit `n − 16` | an ordinary `sw` |

🔴 **The middle row is the trap, and it is in § 14.** `SPEC.md` `IRQ-04` named
*"`Status.IM[7:2]` unmasked"* as the CPU-side layer; that is right for the ICTL
cascade and **wrong for anything on a LOPI line**, the vendor's own system tick
(`BSP_TC0_IRQ` 13) included. The two timer interrupts this board runs are
therefore in different domains: IRQ 13 `rlx timer` is LOPI, IRQ 25
`rtl819x-timer` is ICTL (`FW-190`).

⚠️ **Two 100 Hz counters agreeing is not evidence.** 量 2026-10-04,
`bench/2026-10-04/PRE-IRQ`: over ~8 h 59 min the two agreed to **8 ppm**, and
`FW-190` 殘留 records that this establishes only that both are 100 Hz. The
experiment that would separate them changes one of the rates, which changes the
tick, so it needs a gate of its own.

### 13.1 🆕 2026-10-04 (120th segment) — the peripheral census, read off the running board

This file has been a driver-binding document. This section is the first of what
`P3`'s report needs for its 周邊盤點 and 已知良好的暫存器值 sections: every
driver's own `/proc` state, read on one boot of `f184a` that had been up 10 h 15
m with no reset. 量 2026-10-04 05:29, `bench/2026-10-04/PER-CPU`, `PER-VIEW`,
`PER-NIC`, `PER-SW`, `PER-GPIO`, `PER-KEYS`, `PER-TMR`, `PER-MDIO`. All reads.

#### Three independent confirmations

| reading | value | what it confirms |
|---|---|---|
| `/proc/cpuinfo` `cpu model` | **52481** = `0xCD01` | a THIRD source for `PRId`: `RLX4181` rev 1, with `RLX5281` (`0xdc01`) positively excluded. Also `system type RTL819xD`, `tlb_entries 32`, `mips16 implemented yes`, `BogoMIPS 398.95` |
| `rtl819x-timer` `period_cycles` | **2000** | a THIRD source for `TC0DATA`'s count field being 2,000 — `REG-05` reads the field as bits 31:4 and the raw register prints `0x00007D00`, which is the pair that nearly produced a false contradiction against `CLAUDE.md` earlier in this segment |
| `rtl819x-timer` `jiffies` / `wall` | `4298640981` / `37036.85` | these look inconsistent and are not. 4,298,640,981 − 4,294,937,296 (Linux's `INITIAL_JIFFIES`, −300×HZ at HZ=100) = **3,703,685**, which is 37,036.85 × 100 exactly. The large value is the kernel's negative start, not a defect |

`rtl819x-timer` also carries `hz_assumed 14286057` beside `hz_tick 200000`,
`hz_cdbr 200000`, `hz_used 200000` and `hz_agree 1`: the base clock and two
derivations of the real one, with the driver stating that the two derivations
agree rather than assuming it.

#### Three gaps, each of which would be wrong to paper over

* **MDIO has never read a PHY id.** `rtl819x-mdio`: all five ports `id - rc 1
  xrc 1`, `mdio_rd 0`, `mdio_wr 0`, bus `unlocked 0`, `scanned 00000000`. So any
  claim that this driver identifies the PHYs is unsupported. `NET-136` 殘留
  already records that nothing reads PHY register 31.
* **The key driver has no interrupt.** `rtl819x-keys`: `irq_probe -6`,
  `irq_live -6`, `enxio -6` — `-ENXIO` — so it polls, `poll_ms 50`,
  `poll_jiffies 5`. `nbuttons 1`, `b0_gpio 5`, `b0_code 408`, and `n_ev 0`: no
  key event on this boot. A claim that the button is interrupt-driven is false.
* **GPIO's live CNR and DIR do not match the spec.** `rtl819x-gpio`:
  `cnr FFFFFF8B` against `boot_cnr FFFFFFDF`, `dir FF000040` against
  `boot_dir FF000000`, and the driver says so itself with `cnr_as_spec 0` and
  `dir_as_spec 0`. `dat 0000007C` equals `boot_dat`. `btn_raw 1`,
  `btn_pressed 0`. This is the shape `CLAUDE.md` warns of: Linux reprograms
  `PABCD`'s CNR and DIR, so a loader-state constant does not predict it.

#### One row this handed to `R9`

`rtl819x-view` reports `admit 311`, `n_mib 0`, `n_tbl 0`, `n_peek 0`,
`refused 0`, `busy 0`. rlxfw ships a register viewer with a **bounded
311-entry allow-list**, and nothing had peeked through it on this boot. That is
the design answer to `FW-67`'s vendor finding of an unbounded peek/poke, and
this section proposed the differential row as 有界化 with an rlxfw reading.
🔄 **`R9`, closed 2026-10-04, did not record it that way.** 讀
`config/fix-cases.toml`: the two register rows that name `FW-67` are `FC-079`
(服務不存在, whose residual calls the vendor's peek/poke *the asymmetry rlxfw
has NOT removed*) and `FC-105` (不適用, tier `V-D`, rlxfw cell pending, same-instrument pair
incomplete), and neither carries this reading. The vendor half is `V-D` there
as it was here: reading `/proc` on the vendor firmware needs a shell, which it
has not got.

#### What this section does not establish

It is one boot of one image, and `admit 311` is a count the driver reports about
itself — it is not an audit that the allow-list is correct, only that it exists
and refused nothing because nothing asked. `refused 0` beside `n_peek 0` is a
guard that has never been exercised, which is weaker than a guard shown
refusing. The three gaps are absences of readings, not evidence that the
hardware cannot do those things.

### 13.2 What the census as a whole does not establish

§ 13.1's own closing paragraph states what its one boot does not establish.
Two more limits belong to the census rather than to that reading:

⚠️ **A block having a driver is not the block being characterised.** Every
driver § 13.0's *what has run against it* column names has executed on this die
— `rtl819x-timer`, `-gpio`, `-spi`, `-wdt`, `-nic`, `-switch` and `-keys`, and
upstream `leds-gpio` — as has § 13.1's `rtl819x-view`, and each one's limits
are its own file's. (§ 4's table is `R5`'s text, kept byte-identical,
and its steps 4 and 5 still read *not written*: § 5's 🔄 line and § 13.0
supersede them.) `docs/KNOWN-ISSUES.md` owns what depends on rlxfw's drivers,
and it is the place to read before quoting any row of § 13.0 as a capability.

🔴 **Two blocks in the table have no reading in any state, and they are not
the same kind of gap.** `MCR` at `0xB8001000` has never been read although it is
reachable from the loader prompt with one `DW` (`MEM-07`, `MEM-08` `⊘`); the
radio's attachment has never been traced and would need new work (`RF-04` `⊘`).
⚠️ **The UART has exactly one register reading.** 量 2026-09-15 at the loader
prompt, `bench/2026-09-15/C1-LCR`: `DW B800200C 1` returned `03000000` — `LCR`,
top byte `03`, 8N1, with neither refutation value (`07`, `0B`) — and the
loader's `DW` printed three more words, `+0x10`–`+0x18` `00000000 00000000
10000000`, uninterpreted (`FW-70`; `notes/console-link.md` § 2b owns it). 量
2026-10-05, it is the only `DW`/`DB` into `0xB8002000`–`0xB80020FF` anywhere in
`bench/`. So the loader's line setting is 讀 ×2 and 量 ×1; Linux's `LCR` and
the divisor latch are 讀 only, and § 15.5 says why no shell reaches them. The
**link** — 38400 8N1 at 3.3 V (量 `BRD-10`) — is a different claim from the
register contents, and it is measured in both states.

---

## 14. Errata and traps

`plan` § 6 `P3` section 9 — Errata / 陷阱, and the plan calls it this report's
soul: a bring-up report holding only specification was copied, one holding where
the part bites, how it was hit and how it was worked around was done. **So every
row below carries how it was hit and how it was worked around — *not worked
around* is an answer, and it is given where it is the true one — and where the
project's own first statement of a trap was later narrowed, the narrowing is in
the row.**

### 14.1 `F46` — the load delay slot is architecturally exposed

🔴 **The trap.** On MIPS-I the instruction after a load is architecturally not
guaranteed to see the loaded value, and whether an implementation interlocks
anyway is unspecified. **This core does not interlock at distance 0.**
`SPEC.md` `CPU-14` is the row; its owners are `tools/hazlint` and
`docs/isa-hazard.md` § 5.3, and `docs/rlx-isa.md` § 5 is the consolidated
write-up.

⚠️ **`CPU-14` *is* `F46`, and no tracked file pairs the two ids.** 量 2026-10-05
by `git grep` outside `upstream/`: `F46` appears **nowhere in `SPEC.md`** or
`docs/rlx-isa.md`, while `docs/isa-hazard.md` — one of `CPU-14`'s owners — and
`qemu/README.md` name it for the substance, *qemu interlocks the load delay slot
and this core does not*, without the `SPEC.md` id. The pairing is settled by git
history — in the commit that created the table, `CPU-14`'s owner cell named
`F46` in `plan/` — and `F`-ids live in `plan/`, which is gitignored, so **a
reader with only a clone cannot check the pairing.** That is why this section
leads with the `SPEC.md` id.

**How it was hit.** Not by reading a manual — by a **16-byte truncation** that
made no sense. The tracked statements of it are `tools/hazlint`'s own docstring
— a payload *printed exactly 16 bytes per iteration for ten minutes*, with
`andi t2,t2,0x60` sitting in the load delay slot of `lbu t2,0(t1)` — and
`docs/FINDINGS.md`: *exactly 16 bytes per iteration, one 16550 FIFO, 272 times
over ten minutes*. The chain from that one anomaly runs: an exposed slot means
`-march=mips32` **silently miscompiles**, which is `CPU-28`, derived from this
row, which means the toolchain itself has to be verified on the silicon.

**量 2026-09-14 (seating 21).** `probe5`, 24 rows over 10 families, each row a
*sequence* computing a value that differs under interlock and without — never a
signal test. `lu_alu_d0` read **OPEN** (`B10CB10C`, `$9`'s previous value),
hitting a pre-registration whose source was `upstream`'s `P9-12` `T-89`/`T-90`
and **not this repository** — so this is the first independent acquisition by
this project's own instrument. 🟢 **`lu_alu_d1` read LOCK (`A5A5F00D`) and
`lu_alu_d2` LOCK too: the exposure is one instruction deep.** The 24-row tally
— **LOCK 15, OPEN 6, VOID 3** — belongs to `CPU-54`, not to this row.

🟢 **So one `nop` is enough, and that corrects upstream.** `docs/rlx-isa.md`
§ 5: upstream's payload used two `nop`s where rsdk 1.3.6 under `-fuse-uls`
emits one, *"Upstream is the one that is wrong — one is enough."*

**The workaround is a build rule rather than a code habit.** `CLAUDE.md` forbids
`-march=mips32` outright and forbids asm under `.set reorder`; `tools/hazlint`
enforces it over the whole image (量 on `stage2.bin`: 1,474 loads, 646 followed
by a `nop`, **0 that read the just-loaded register**); and for `probe5` the gate
is **inverted** — `hazlint` exiting 0 is a *build failure*, because a hazard
payload with no hazard left in it is one the compiler already fixed.

⚠️ **What it does not establish.** The ladder closes **per family**, not
globally: `loaduse`, `storedata`, `storebase`, `movcond` and `dslot` close at
d1, `hilo` and `movrd` at **d0**, and the whole `cp0` family reads VOID
(§ 14.2 ②). ⚠️ Store-data is `CPU-58`, not this row — a frozen bench card once
cited `CPU-14` for it and the correction is recorded. ⚠️ And `CPU-47` is why
none of this can be re-measured under Linux.

### 14.2 The core's other four

| # | the trap | how it was hit | how it was worked around | V | owner |
|---:|---|---|---|:-:|---|
| ① | 🔴🔴 **`rotr` is decoded as `srl` — no exception, and a wrong value.** Encoding `0x00291202` (SPECIAL, `rs=1`, `sh=8`); input `12345678` should rotate to `78123456` and read **`00123456`** instead. MIPS32r2 separates `rotr` from `srl` by one bit of the `rs` field and **this core ignores it** | `probe4`, 量 2026-09-14 (seating 21), `cause` column **empty**. 🟢 Value, mechanism and purpose were written into `tools/isa-payload.tsv` **before power-on**, and the same value was then reproduced in Linux **user** mode, so it is not a privilege artefact. ⚠️ The row warns it is **one encoding** — WRONG is 1 of 75 — not a verdict on all of mips32 | **By a build rule, not a code habit**: `CLAUDE.md` forbids `-march=mips32`, and this row is that ban's first-hand evidence — its reason, *mips32 miscompiles silently*, was inherited until this reading (`CPU-55`) | 量 | `CPU-55`, `docs/isa-payload.md` § 6 |
| ② | 🔴🔴 **`mfc0 $x,$14` reads `EPC` and `mtc0 $x,$14` does not write it**, so `EPC` cannot be used as scratch and the whole `cp0` hazard family is **not measurable with this register on this part** | `probe5`'s `cp0` family, three rungs all **VOID**, control word `80500270` — neither the `5A5A5A50` written nor the old `A5A5A5A0`. Identified by disassembly as **the address of the image's one `break`**, so the hardware wrote `EPC` on that exception and every later `mtc0` left it alone. Five independent readings, one value. ⚠️ The payload's own `aux.zero` check was blind here because it tests `== 0` | **Not worked around — recorded.** The `cp0` family's verdict is *not measurable with this register on this part*: `Status` has reserved bits, so its read-back is no self-contained constant, and writing an unidentified CP0 register is refused by `tools/isa-payload.tsv`'s own doctrine. The safety half held — nothing trapped and the handler was not misled (`docs/isa-hazard.md` § 7, item 4) | 量 | `CPU-56`, `docs/isa-hazard.md` § 7 |
| ③ | 🔴 **CP0 `Count` (9) and `Compare` (11) are not implemented and read 0 without trapping**, so any timing method built on them silently measures nothing | 量 2026-08-25b, bare metal. `Count` reads `00000000` with `S_ZERO`; across a 100,000-iteration loop `before == after`, `delta = 0`, `traps = 0`. 🟢 **The zero is a real zero**: both destinations were primed with *different* values first, `CPU-38`'s `nowrite = 0` covers all 256 rows, and the **positive control** is row `0x08`, `Random`, reading `S_MOVES` | Time from the SoC's own timer/counter block instead (§ 8): `CPU-42` records that this made `R5-0`'s SoC timer driver a prerequisite rather than an extra, and cost `R1c` its first timing route | 量 | `CPU-42` |
| ④ | 🟢 **`lwl`/`lwr`/`swl`/`swr` all exist on this die — which contradicts the public Lexra claim that the family lacks them.** A decision built on that public claim is wrong for this part | `probe4`, 量 2026-09-14, four rows all `RIGHT` computing the desk-derived constants; the negative control `special0e` trapped with `ExcCode 10` in the same capture and the seven MIPS-I baseline rows were all `RIGHT`. ⚠️ The LX5280 claim is untouched | **None needed on this die**: the trap is the public claim, so a decision is taken from `probe4`'s reading. ⚠️ An aligned load or store at an *unaligned address* is a different case — `AdEL`, emulated in Linux user mode at 915.5 ns a round trip (`CPU-15`, `CPU-75`) | 量 | `CPU-15`, `notes/lwl-mystery.md` |

🔴 **① is the shape that matters most for bring-up**: no fault, no warning,
wrong arithmetic. It is the same shape as § 14.1 one layer up, and it is why
`CLAUDE.md`'s toolchain bans are bans rather than preferences.

⚠️ **③ is also the reason § 8.2 cannot close.** With no CP0 `Count` there is no
way to separate `f` from CPI, which is exactly what `CLK-03` `⊘` records.

### 14.3 The loader will write anything you ask it to, and some things you did not

| # | the trap | how it was hit | how it was worked around | V | owner |
|---:|---|---|---|:-:|---|
| ① | 🔴 **`EW` writes four bytes anywhere with no bound check, completely silently**, writes exactly `argc − 1` words, and **rounds an unaligned address UP** — so a write to the wrong place looks identical to success | 量 2026-08-24: `C3` sent `EW 81000102 11111111` and it landed at `0x81000104`. `C7a`/`C7b` sent twelve and eleven values; both landed in order and both guard words (`0x81000430`, `0x8100046C`) were byte-identical before and after, with the refutation conditions written before the cells ran. | Align the address yourself and confirm every write with a separate `DW` read-back | 量 | `LDR-08` |
| ② | 🔴 **`EB` writes one byte, no bound check, silent, and never rounds** — **the opposite of `EW`, and the asymmetry is the thing to remember**: the two write primitives disagree about what an unaligned address means | 量: `C4` sent `EB 81000200 41 42 43` and the three bytes landed at `…200`/`…201`/`…202` | As ①: confirm every byte with a separate `DW`. `CLAUDE.md` § Flash counts `EB` among the verbs that can write flash, because it writes any address with no bound check, so it needs the owner's dated yes and `cardcheck` refuses it without one | 量 | `LDR-09` |
| ③ | 🔴🔴 **Half the command table does not check its argument count, and a bare `PHYR` hangs the board until a power cycle.** The table at `0x8040DBC0` is 17 entries × 16 bytes, `{char *name; int argc; int (*func)(int,char**); char *help}` — and **the `argc` field is dead**: the dispatcher at `0x80409144` reads only offsets 0 and 8 | 讀 2026-09-19 over `stage2.bin`, **and then measured**: `bench/2026-09-19/X11-phyr.log`, 82 bytes, printed `cp0_cause=00000028, cp0_epc=80000000, ra=00000000Undefined Exception happen.` (`ExcCode` 10) and then went silent; an 8 s ESC probe returned **0 bytes** with the link healthy. Unchecked: `EB`, `EW`, `AUTOBURN`, `LOADADDR`, `FLR`, `FLW`, `PHYR`, `PHYW`. Checked: `DB`, `DW`, `CMP`, `IPCONFIG`, `J`, `MDIOR`, `MDIOW`. ⚠️ `PHYR <phyid> <reg>` is safe and parses base 16; `MDIOR` parses base **10** | Never type the unchecked commands bare: `RUNSHEET.md`'s *Do not type* list names them with the price, a power cycle (`LDR-12`), and `PHYR` is only ever typed as `PHYR <phyid> <reg>` | 讀 + 量 | `LDR-44`, `LDR-12` |
| ④ | 🔴 **`AUTOBURN` starts at `1`, and exactly one instruction in the whole image reads it** (`0x80401B9C`), on the upload-complete path. **Finish an upload without having typed `AUTOBURN 0` first and it is burned into flash** | 量 `B6`: `DW 8040D4A0 1` read `00000001` at the prompt, single writer `0x80409944`. | `LDR-23b`: `AUTOBURN 0` with a space — `AUTOBURN: 0` answers `Unknown command !` — and confirm *both* the `AutoBurning=0` echo and a `0x8040D4A0` readback of `00000000`, because every reset restores `1`; `CLAUDE.md` § Flash makes the readback the evidence, not the echo (`C-6`) | 量 | `LDR-23`, `LDR-23b`, `REG-23` |
| ⑤ | 🔴 **A line of exactly 128 characters is left unterminated.** `readline` at `0x8040708C` has three exits and only the CR one writes a NUL (`0x804070FC`); the LF exit and the length-exhausted exit (`0x80407194`, `count < 128`) do not. The caller's `memset` only saves lines **shorter** than 128. So the tokenizer at `0x80407248` scans past `sp+143` into an 8-byte stack gap and then into the saved `s0` at `sp+152` | 讀 the disassembly, re-derived 2026-08-30 — and it **caught a 173-character `EW` line in `RUNSHEET.md` `C7` before it ran**, which was rewritten to twelve values and 119 characters. The 128-byte buffer size itself surfaced when ESC streaming was answered `Unknown command !` after exactly 128 bytes, seven times (`LDR-06c`). ⚠️ **The row was right while its own owner file was wrong** — both exits of the three-way branch had been annotated with the same empty character, so *only one writes a terminator* named neither; found by `spec-check` C9 | No command line anywhere may be exactly 128 characters, and `CLAUDE.md` caps a `--send` at 127 | 讀 | `LDR-06d` |
| ⑥ | 🔴 **`DB`/`DW` mix bases**: the address is hexadecimal and **the length is decimal**, and `DW <addr> N` prints `4 × ceil(N/4)` words — the length rounds **up** silently, while the start address is **not** rounded down | 讀 + 量 at the prompt. It is why `DW … 1` returns four words, which is what § 9.2's third word rests on. ⚠️ An address with bit 31 clear is forced into KSEG0 | Predict every reply's length before reading it: `tools/reply-size.py` derives it from the command, 598 of 598 with 0 unexplained on 2026-09-19 (`LDR-07`), so a length that rounded up shows as a reply of the wrong size. Over a register block whose reads have side effects, a card fixes the **start address**, not the word count (`FW-70`) | 量 | `LDR-07` |
| ⑦ | 🔴 **An MDIO read is not read-only.** `phy_read()` writes `MDCIOCR` **and sets `GIMR` bit 8 (`TCIE`, at `0x80402FB8`), and never restores it** | 讀 the code — and the planned read-only test `E5` was **void on arrival**, because `GIMR` already read `00008100` at the prompt. `C5` recovered it as a *write* experiment: `DW` → `EW B8003000 8000` → `DW` → `PHYR 0 2` → `DW` returned `00008100` · (silent) · `00008000` · `UID=0x0000001c` · `00008100`, with `GISR` moving `88000004` → `88000104` → `88000004`. **A bit cleared by hand came back** — the causal control, predicted from the code before the visit | **Not avoidable at the prompt — ordered around.** Take loader-state `GIMR` before the session's first PHY access, or record what was typed before it (§ 15.6), because the loader never restores bit 8 | 讀 | `NET-16` |
| ⑧ | 🔴 **The MDIO completion wait has no timeout and no loop bound** — a `bltz v1` at `0x80402FD8` spinning on `MDCIOSR` bit 31. **An address that never answers would end the seating** | 讀 the disassembly, **never hit**: the risky cell (`PHYR 5 2`) was deliberately run last, and `NET-24`'s 32-point scan shows addresses 0–4 reading `0x001c`, 5–31 reading `0x0000`, and **every read completing** — under Linux's `mdiobus_read` as well | **By ordering**: the one risky cell (`PHYR 5 2`) went last in its seating, so a hang would have cost only that cell. Nothing of rlxfw's depends on this loop: `rtl819x-switch` sends no MDIO command at boot (§ 13.0) | 讀 | `NET-17` |

⚠️ **⑦ has a consequence for § 15 that is easy to miss**: `GIMR`'s loader-state
value is **not a constant** — it reads `00008100` after any PHY read, and the
project's planned "before" reading did not exist to be taken. A known-good
loader-state `GIMR` therefore depends on what was typed earlier in the session.

### 14.4 The drivers' traps, measured under Linux

| # | the trap | how it was hit, and how the first statement of it was narrowed | how it was worked around | V | owner |
|---:|---|---|---|:-:|---|
| ① | 🔴 **A loader-state clock constant produced a watchdog table wrong by 76×.** `RTL819X_WDT_HZ` carried 14,965,000 — the loader-state rate — while under Linux the same counter runs near **200,180 Hz** | 量 at the bench over two `OVSEL` points. 🔴 **It survived three segments because the frequency had no owner**: the watchdog read it out of the timer's registers and no layer was in a position to disagree (§ 1.1). | The timer carries no clock constant: `rtl819x-timer` 2.0 derives its rate at init and reports `hz_agree 1` (§ 8.1). The watchdog's table is kept wrong **on purpose** — `/proc` prints it and bench cards predict against it, so it must not be "fixed" (`CLAUDE.md`) — and its error runs the safe way: `kick_ms 250` against `OVSEL` 9 is a 335× margin, not the 4.48× believed (`notes/watchdog-driver.md` § 10.2) | 量 | `CLK-08b`, `docs/KNOWN-ISSUES.md` |
| ② | 🔴 **Re-opening an already-open `rlx0` does not re-arm the descriptor bases**, so the DMA engine resumes from its old position — outside the ring — and can write frame data into arbitrary DRAM | 量 2026-09-20 (`X12`): `ifconfig down ; ifconfig … up` printed `N-ENGOFF`, `N-NDSTOP`, `N-ENGON=C4000000`, `N-NDOPEN` and **neither `N-ALLOC` nor `N-ARM`** — `ndo_open` skips both when `nic_allocated`/`nic_armed` are set. 量 `X23`: `rpdcr0_pos` walked `A15B1C00` → `A15B1C64` while `rx_ring` is `A15B8000`. | `engine off ; arm ; engine on`, *not* `ndo_stop`/`ndo_open` — `X16` re-broke an interface that had already been recovered | 量 | `NET-58` |
| ③ | 🔴🔴 **A multi-frame burst desynchronises the engine's two RX position registers while the driver indexes both with one `i`**, so a frame is delivered carrying another frame's length | 量 2026-09-20 (seating 30): a datagram lost exactly one fragment, `seen_iisr` moved `0000320E` → `0001320E` (`MBUF_RUNOUT`), and `InTruncatedPkts` read 1250 — one per failed datagram — while switch port 3 counted 13,541 clean frames. 🔴 **Two first statements were struck.** *Δ is always 4* is **retracted**: seating 31 saw 1/2/3 and transient, committed dumps show `dsync_last_d` taking every value 1–7, and a single sample is a **lower bound**. *Permanent* is retracted too. ⚠️ **And on an 8-entry ring, 4 is its own negative** (`C16` is rp 6 / rm 2, `C17` rp 1 / rm 5), so *which* ring lags is **未定**. 🔄 The trigger's first bracket — six frames do **not** do it, fourteen do — narrowed twice: seating 31's ladder, zeroed by `arm` before each level, read Δ`n_dsync` 0 at 7 frames and 1 at **8 = `NIC_RX_DESC`** (9 → 4, 10 → 3, 14 → 5, one burst per level), and block 46 fired it with **two** loopback frames per run at seven wrong lengths, +1 each, and not at 60, 276, 1,513 or 1,514 — so burst size is not the only trigger. Block 47 confirmed that length prediction at E2's eleven lengths; which ring lags stays ⊘ (`NET-61` 殘留). ⚠️ A draft also misused 1.88 MB/s as a copy rate — it is a ping-bound lower bound | Two layers, neither a cure. Since `rtl819x-nic` 1.3 the harvest follows `ph_mbuf` (`NET-102`), so which position register lags no longer decides which buffer is read — 量 `n_ph_bad 0` over 107,041 frames (block 45, `D1-N4`); and since 1.6 the vendor's length convention is the driver's default (`docs/GATE-RESULTS.md` entry 14), under which block 47 read Δ`n_dsync` 0 at all eleven of E2's lengths. ⚠️ Neither establishes that the fault class is gone under `ph_follow 1` (`NET-61` 殘留 ②) | 量 | `NET-61` |
| ④ | 🔴 **A flood-induced inbound stall survived a watchdog reset**, and the one time it happened only a cold power-on cleared it | 量 2026-09-19, by elimination: TX fine (the workstation captured both raw frames), interrupts fine (`n_irq 2`), the host really sending (15,004 packets, 0 errors), the port's `PSRP3` reading `000000F9` with `LinkUp` set. 🔴 **The clause that the vendor's own driver was the control is STRUCK** — `eth4`'s counters *are* port 3's MIB counters, so it is not an independent control, and the location survives only as *at or below port 3's receive counters*. ⚠️ `n = 1`: *the flood caused it* was never proven, and `NET-56` offers a competing re-attribution to a marginal cable | **Not worked around.** A cold power-on cleared it the one time it happened; the flood half was re-run twice without a stall (`L2-after`, `M7-after`), and the mechanism is ⊘ — so what exists is an order of readings for the next time, not a rule that avoids it (`NET-54` 殘留) | 量 | `NET-54` |
| ⑤ | 🟢 **And ④'s sweeping half is refuted: a fresh `arm` takes a wedged TX ring back, so *only a cold boot clears it* is false for that fault** | 量 2026-09-21 on an already-wedged board, at zero cost: after `engine off ; arm ; engine on` all four TX descriptors' bit 0 cleared and returned to the CPU, `tx_stopped` 1 → 0, `n_tx_wake` 0 → 1, `n_tx` 26 → 31. 🔄 **And this row's own *recovery is not durable / only 2 of 4* was then narrowed**: `NET-72` attributes that to the ordering of *that* seating rather than to `arm`, reaching 4 of 4 at 1.307 ms on its third rung, and block 50 ran arm 12 / fire 12 / ok 12 / fail 0 under 120 s of load. ⚠️ Still *until the next fault* | This row *is* a recovery — ②'s `engine off ; arm ; engine on` — and it holds until the next fault; it is not a cure for ④'s inbound stall | 量 | `NET-68`, `NET-72` |
| ⑥ | 🔴 **`PABCD_DAT` bit 6 is a vendor-driven output under Linux**: it alternates with a 1 s half-period while the button is held, rests at 1 released, and **after a long-press release latches 0 or 1 by the parity of the last pressed tick** | 量 seating 15, three states with one instrument. 🔴 **The card predicted a released-against-held XOR of `00000020` and both boots read `00000060`** — because bit 6 moved too. Released: 27 samples all `0000007C`; held at 1 s: `5C 1C 5C 1C…`; 15 no-gap samples all `1C`; after a ~8 s hold the word read `0000003C`. ⚠️ `C1-L2` read `0000007C` minutes after release and is **unexplained**; the stable interval was corrected from 152.1 s to 139.251 s | Mask bit 5 only — `(dat ^ dat) & 0x20` gives `00000020` — and use the driver's single-bit `btn_raw`/`btn_pressed` fields; **do not predict the post-release latch** | 量 | `REG-37`, `BRD-13` |

🔴 **③, ④ and ⑤ together are the pattern this section exists to show.** Each
began as a confident statement and each was narrowed by a later measurement:
④'s control turned out not to be a control, ⑤ refuted ④'s generalisation at zero
cost on a board that was already broken, and ③'s own headline number was
retracted when more samples arrived. ⚠️ **Do not read ⑤ as fixing ④** —
`NET-54` 殘留 `⊘` keeps the inbound stall's mechanism open, and `NET-67` rather
than `NET-68` is what refuted its *ingress wedge* label.

⚠️ **① is narrower than it looks, and the row says so.** 200,180 Hz is a
two-rung fit. A four-rung Linux ladder (`OVSEL` 0/3/8/9 → 163.911 / 1,340.982 /
41,910.358 / 84,001.412 ms) **falsified** the single-clock-plus-fixed-offset
model with residuals of +3.5 / +32.5 / −71.0 / +35.0 ms against 1.456 ms
repeatability, and **`OVSEL` 3 reads about 2 % high, reproducibly and
unexplained**. So what is established is that the loader constant is wrong by
76× under Linux — not that the Linux clock is a clean 200,180 Hz. `CLK-08b`'s
own `N` mark is `—`, and the integer relation between 14.965 MHz and
200.0049 MHz is **未定**.

### 14.5 The flash traps, and the two that are not about rlxfw

🔴 **Never write *"not one flash byte is written"*.** `CLAUDE.md` says so because
`FLS-26` proved it false for this device, and the shape of the proof is the
useful part. 量 2026-09-08 (seating 16), by prefix digest: `verify 32768` and
`verify 36864` matched, **`verify 40960` did not** — and between 36,864 and
40,960 lies only `[0x9000, 0xA000)`, so **the first difference is those 4,096
bytes**, exactly one erase sector, inside `mtd0`'s *boot+cfg+linux* and
immediately above `H601`. 🟢 Then 量 2026-09-09 (seating 18), the two-level
`map`: **30 same, 2 DIFFER, 0 scope, 0 extra, 0 missing**, giving the final
accounting — **proven same 4,177,920 B (99.61 %), proven different 8,192 B
(0.195 %), undetermined 8,192 B (0.195 %)** — where the undetermined 8,192 is
exactly `H601` and is skipped **by rule**, not for want of an instrument.

🔴 **The two changed sectors have no attributed writer.** The change falls
between the 2026-08-16 dump and 2026-09-08; it was **not** that night (ten boots
went loader → rlxfw's image, the factory firmware never executed, and no
`FLW`/`EW`/`EB`/burn was issued). The factory firmware *did* run on this unit
after the dump, for about two minutes, and `[0x9000, 0xA000)` is where it keeps
settings — ⚠️ **but that is a mechanism-bearing hypothesis, not a
measurement, and the row writes it as one.** 🟢 **The workaround is an
instrument**: bracket every vendor-firmware run with `map 0` before and after,
comparing the map **body** and excluding `map_jiffies` — a whole-log `cmp`
falsely reported a difference, 1279 against 1280 bytes.

⚠️ **The claimable sentence, and what it cannot see.** *Commands issued, rlxfw's
own `n_writes`, and the bracket's reach against the named dump* — never a global
negative. 🔴 And `n_writes` reading 0 is **only a counter not moving**: what
actually stands, in every committed image, is that this driver's write and
erase paths are **refusing stubs** (`FW-142`, `FW-210` ③). Since 2026-10-04
the write path exists in source behind `CONFIG_MTD_RTL819X_WRITE`, which
`config/rlxfw-kernel.delta` pins `n`, so no committed image links it (`FW-207`);
in an image built `=y`, `rtl819x_spi_note_write()` increments the counter and
its 0 starts to carry information — and it stays blind to the vendor's own
write path (`FW-210` ③). ⚠️ A prefix digest finds the **first** difference and
nothing past it (`CLAUDE.md`), and `FLS-26` `⊘` keeps `[0x9000, 0xA000)`'s and
`0x00D000`'s contents open.

🔴 **`n_writes` is three different counters, and two of them are not flash.** 量
2026-10-04: `/proc/rtl819x-spi`'s `n_writes` is **0** and is the one
`CLAUDE.md` § Flash means; `/proc/rtl819x-nic`'s is 14 and
`/proc/rtl819x-switch`'s is 6, and both count **register** writes. ⚠️ **A census
that greps `n_writes` under `/proc` reads three numbers, two of them nonzero and
neither about flash** — a false-alarm generator. `FW-194`.

🔴🔴 **The vendor firmware writes flash on an *unauthenticated* request.** 讀
2026-10-04, instruction by instruction, over `upstream/notes/auth-flow.md` at
pin `4d3ff26`: inside boa's unauthenticated branch there is a path that, once a
boot-time-based threshold is crossed, calls a settings write, and that write
lands on flash. **The mechanism belongs to a held disclosure (`D-18`), so this
row records the class and the operational consequence and nothing more.**
⚠️ **And rlxfw's `n_writes` cannot see it**, because it is the vendor's write
path. The consequence: a zero-flash-write claim about a seating that boots the
vendor firmware **does not stand without containment**, and `R9-6` applied
both on 2026-10-04: *path* — a probe list using only names that branch skips —
and *time* — the whole vendor HTTP episode finished inside the post-boot
threshold (`docs/GATE-RESULTS.md` entry 19, claim ③). `FW-196`,
`docs/threat-model.md`.

### 14.6 What § 14 does not establish

⚠️ **Each row is one die.** Nothing here distinguishes an erratum of the part
from a property of this instance (§ 0 ②), and `docs/rlx-isa.md` § 0 makes the
same statement for the instruction set with the same force.

⚠️ **The ISA rows cannot be re-measured under Linux and were not.** `CPU-47`
讀 is the reason: this kernel emulates `ll`/`sc` and emulates `sync` as a
no-op, has **no FPU emulator at all** (`do_cpu` handles only `cpid == 0` and
otherwise raises SIGILL), does **not** emulate `rdhwr`, and emulates misaligned
access only for `lh`/`lhu`/`lw`/`sh`/`sw`. 🔴 So a *no signal means implemented*
census records `ll`/`sc` **backwards**. ⚠️ `CPU-47` itself is **user mode only
and silent on kernel mode**.

⚠️ **Two loader rows are 讀 and were deliberately never triggered**:
`LDR-06d`'s 128-character line and `NET-17`'s unbounded MDIO wait. The rest of
§ 14.3 carries a 量. ⚠️ `LDR-44`'s chain from a NULL argument to `0x80000000`
is 推 and refutable by one `DW 80000000`.

⚠️ **Four owner cells in these rows say 同上** — `LDR-06d`, `LDR-09`, `NET-16`,
`NET-17` — which is relative, not a path, so the owner must be resolved by
reading the row above. ⚠️ And two source tags look wrong: `LDR-44` tags `B`
where its owner file says `A` only, and `FW-196` tags `S` for an `upstream/`
artefact where `SPEC.md` § 0 defines `C`. **The owner file wins in both.**

⚠️ **This list is not ordered by severity and is not complete.** It is the set
of traps this project hit or read while doing something else;
`docs/KNOWN-ISSUES.md` owns what currently depends on rlxfw's drivers, and
`SPEC.md` § 17 owns what is still open — including `FLS-26`, `CLK-08b` 殘留,
`NET-54` 殘留 and `NET-61` 殘留, all `⊘`.

---

## 15. Known-good register values — meaning *values this device returned*, per state

`plan` § 6 `P3` section 10 — 已知良好的暫存器值. 🔴 **The title the plan gives
this section cannot be delivered as written, because nothing in this project
defines *good*.** What exists is a set of readings taken off this die, each in a
known machine state. This section is those readings. It is **not** a
configuration to write, and § 16.4 says why that distinction decides whether a
reader can use it.

### 15.1 How to read the table, and the one sentence that makes it safe

讀 `SPEC.md` § 9's own header: *"only rows that really have a reading are marked
量. The value column is what this unit returned at the `<RealTek>` prompt;
undated entries are 2026-08-23."* **So `SPEC.md` § 9's default state is loader
state**, and every row below that carries a Linux-state value says so
explicitly and names the capture it came from.

🔴 **A value in one state is not a prediction of the other, and this project has
the scar.** `CLAUDE.md`'s Never-table names four registers Linux reprogrammes —
`CDBR`, `TC0DATA`, the watchdog's clock, and `PABCD`'s `CNR` and `DIR` — and
§ 1.1 above is what it cost when the watchdog derived its rate from a
loader-state constant: a compiled table wrong by **76×** for three segments.
**§ 15.2 is that list, measured.**

### 15.2 🔴 The registers whose value differs between the two states

**This is the table to read first.** Each row has been read in both states on
this die, and the two readings differ. A tool, a driver or a bench card that
predicts one column from the other is wrong by construction.

| register | address | loader state | Linux state | owner |
|---|---|---|---|---|
| `TC0DATA` | `0xB8003100` | `0x0022E0A0` | **`0x00007D00`** | `REG-05` |
| `CDBR` | `0xB8003118` | `0x000E0000` | **`0x03E80000`** | `REG-11` |
| `IRR0` | `0xB8003008` | `00000000` | **`22222222`** | `REG-32` |
| `IRR1` | `0xB800300C` | `30050004` | **`C222FA2D`** | `REG-03` |
| `IRR2` | `0xB8003010` | `00000000` | **`2EB29F22`** | `REG-04` |
| `IRR3` | `0xB8003014` | `00000000` | **`22222022`** | `REG-33` |
| `GIMR` | `0xB8003000` | `00008100` — ⚠️ **not a constant**, § 14.3 ⑦ | **`00209100`** | `REG-01` |
| `PABCD_CNR` | `0xB8003500` | `0xFFFFFFDF` | **`FFFFFF8B`** | `REG-26`, `FW-193` |
| `PABCD_DIR` | `0xB8003508` | `0xFF000000` | **`FF000040`** | `REG-27`, `REG-35`, `FW-193` |
| `PABCD_DAT` | `0xB800350C` | `0x0000003C` released · `0x0000001C` held | **`0000007C`** | `REG-28`, `BRD-05`, `FW-193` |
| `SFCR` | `0xB8001200` | `3FC00000` — divisor 4 | **`FFC00000`** — divisor 16, ten boots identical | `REG-13`, `REG-38` |
| `SFCSR` | `0xB8001208` | `D8050000` | **`C8000000`** | `REG-13`, `REG-38`, `REG-39` |

🟢 **The `IRR` block is the strongest row in this document and it was predicted
before it was read.** 量 2026-09-04, seating 12: `TI-L` at the loader prompt and
`TI-0` under Linux, **the same power cycle 90 seconds apart**. All four Linux
words were recomputed from `bspchip.h`'s `_RS` macros **before** the seating and
all four landed byte-for-byte. `IRR0`, `IRR2` and `IRR3` had never been read on
this die in either state; `IRR1`'s loader value reproduced `REG-03` byte for
byte eleven days later, taking it from `n = 1` to `n = 2`.
`docs/interrupt-map.md` § 4.3.

🔴 **`PABCD`'s two Linux-state words are the ones a driver author will get
wrong.** `rtl819x-gpio` reports `cnr_as_spec 0` and `dir_as_spec 0` itself —
the driver states the disagreement rather than hiding it — and § 13.1 is the
reading. The cause is named: the vendor's `rtl_gpio_init` writes both registers
at `device_initcall` (`REG-35` 讀), and it sets bit 6 of `DIR` (`REG-37`).

### 15.3 Loader-state readings

讀 `SPEC.md` § 9's header, in translation: *only rows that really have a reading
are marked 量; the value column is what this unit returned at the `<RealTek>`
prompt, and undated entries are 2026-08-23.* **So these are 量 at the prompt**,
and `SPEC.md` § 9 carries each row's V and N marks — this table does not restate
them.

| register | address | reading | owner |
|---|---|---|---|
| `GISR` | `0xB8003004` | `0x88000004` — bit 8 `TCIP` latches while masked and clears after delivery | `REG-02` |
| `TC0CNT` | `0xB8003108` | `0x0010B960`; two later reads gave `001BD530` and `000425D0` — **it moves**, which is what left `n = 1` behind | `REG-07` |
| `TC1CNT` | `0xB800310C` | `0x00000000` | `REG-08` |
| `TC1DATA` | `0xB8003104` | `0x00000000` in **both** states while unarmed | `REG-06` |
| `TCCNR` | `0xB8003110` | `0xC0000000` — byte-identical to what `timer_init` writes | `REG-09` |
| `TCIR` | `0xB8003114` | `0x80000000` | `REG-10` |
| `WDTCNR` | `0xB800311C` | `0xA5000000` — `WDTE[7:0]` = `0xA5`, the **stop** pattern. 🔴 **A hardware reset default, not written by the loader**: its only two writers are `sw zero` followed immediately by a self-loop | `REG-12`, `CLK-11` |
| `PABCD` + 4 | `0xB8003504` | `0x00000000` — 🟢 first read ever on 2026-09-06, seating 15; **still a value with no name** in D § 8.3 or in any of the GPL drops | `REG-36`, `MAP-09` |
| `SFCR`…`SFDR2` | `0xB8001200`–`0x1210` | cold `3FC00000 0BA08000 D8050000 FFFF0002` · after a watchdog reset `3FC00000 0BA08000 D8050000 FFFF0000` | `REG-13` |
| `PITCR` | `0xBB804100` | `0x00000000` | `REG-15` |
| `PCRP0`–`PCRP4` | `0xBB804104`–`0x4114` | `007F0039` `047F0039` `087F0039` `0C7F0039` `107F0039` — 🔴 **prompt only**: the loader's `J` handler clears `EnablePHYIf` (bit 0) before jumping, so a `J`-entered payload sees `…38` | `REG-16`, `notes/switch-driver.md` § 8.3 |
| `PSRP0`–`PSRP4` | `0xBB804128`–`0x4138` | `10E0` `10E0` **`1099`** `10E0` `10E0` — one port differs, and that is the link | `REG-17` |
| *(B calls it `PSRP5`; D's Table 62 skips `0x3C`)* | `0xBB80413C` | `0x000000E2` — ⚠️ **N mark is `—`: the two documents disagree on the name** | `REG-18` |
| *(D calls it `PSRP6`)* | `0xBB804140` | `0x0000007A` | `REG-19` |
| *(next port by `PSRP` spacing — 推, **no source states it**)* | `0xBB804144` | `0x0000007A` | `REG-19b` |
| chip id | `0xB8000000` | `0x8196E001`, with words 2 and 3 `00000002` and `00100200`, both unnamed | `REG-29`, § 9.2 |
| button-source mux | `0xB800000C` | `0x0000000F` — § 9.2 | `REG-30` |

⚠️ **Three loader-state rows are RAM, not registers**, and they are listed
because a bring-up reader will meet them at the same prompt: the command table
at `0x8040DBC0` (`REG-20`), the flash chip descriptor at `0x8040FBD4`
(`REG-21`), and the timer tick counter at `0x8040DCE8` (`REG-25`). `AUTOBURN` at
`0x8040D4A0` (`REG-23`) and `gCHKKEY_HIT` at `0x8040DBA4` (`REG-22`) are the
same kind of thing and are the two that can cost the device — § 14.3 ④ and
§ 9.3.

### 15.4 Linux-state readings not already in § 15.2

量 2026-10-04 unless noted; § 13.1 is the capture and the owner.

| what | reading | owner |
|---|---|---|
| `/proc/cpuinfo` `cpu model` | `52481` = `0xCD01` — a **third** source for `PRId` | `FW-193`, `CPU-04` |
| `rtl819x-timer` `period_cycles` | `2000` — a **third** source for `TC0DATA`'s count field | `FW-193`, `REG-05` |
| `rtl819x-timer` `hz_tick` / `hz_cdbr` / `hz_used` | `200000` each, with `hz_agree 1` and `hz_assumed 14286057` beside them | `FW-193` |
| `GIMR` bit accounting | `00209100` = bits 8 `TC0_IE`, 12 `UART0_IE`, 15 `SW_IE`, 21 `PCIE_IE`, **and no fifth bit lit** — each with its own source line | `REG-01` |
| CP0 `Status` | `0x10000401`: `IM2` (bit 10) = 1, `BEV` (bit 22) = 0, `IEc` (bit 0) = 1 | `IRQ-10` |
| TC1's Linux IRQ | **25** = `BSP_TC1_IRQ`; route `TCIR` bit 30 → `GISR` bit 9 → `GIMR` bit 9 → `IRR1` bits 7:4 → CPU `IP2` | `IRQ-06` |
| interrupt deliveries | **119,818**, with `irq_spurious 0` and `irq_stuck 0` | `IRQ-08` |
| flash JEDEC id, read by rlxfw | `rdid_id 1C7016` — and the pre-action control was `rdid_ran 0`, `rdid_id 000000` | `FW-191`, `FW-186` |

### 15.5 Addresses on the map with **no** reading in any state

**A census of readings has to say where it has none.** These are the rows a
reader should not mistake for absent hardware.

| address / row | status | what settles it |
|---|---|---|
| `0xB8001000` `MCR` | 🔴 **never read**; `MEM-08` `⊘` for the timing settings | one `DW B8001000 …` at the prompt for the words; reading the loader's writes, at the desk, for the settings |
| `0xB8001208` bit 27 `SPI_RDY` | *(未讀)*, `V = —` — ⚠️ but **this unit's own `ComSrlCmd_RDID()` waits on this bit**, which is code depending on the semantics rather than a document asserting them. ⚠️ And `REG-13`'s decode of `D8050000` **already reads this bit as 1**, so § 17's framing is the precise one: *nobody has seen it flip* | `REG-14`, `REG-13` |
| `0xB8001210` `SFDR2` | *(未讀)* — the `DW B8001200 4` that produced `REG-13`'s four words stops at `0x120C` | `REG-13` |
| `0xB8000048`, `0xB800004C` | 量 `2702DFF1` and `0A8D8ED0` at the prompt, **and no name, no owner and no `SPEC.md` value row** — the same shape as § 9.2's words 2 and 3 | § 10.1; `REG-40` 殘留 |
| `0xB8002000`–`0xB80020FF` UART, apart from `LCR` | 🔴 **no other register read**: 量 2026-10-05, the only `DW`/`DB` into this range in all of `bench/` is 2026-09-15's `DW B800200C 1`, which read the loader-state `LCR` as `03000000` — 8N1 — and printed `+0x10`–`+0x18` beside it, uninterpreted (§ 13.2) | Linux's `LCR` and the divisor latch have no path from the shell: no applet reads a register (`FW-70`), and 讀 2026-10-05 `rtl819x-view.c` admits no address in this block. ⚠️ Never a `DW` from `+0x00` or `+0x08`: reading `RBR` pops a received byte and reading `IIR` clears the pending interrupt id (`FW-70`) |
| the strapping register's layout | 未定, `REG-40` 殘留 — datasheet § 6.1 exists, **no layout or initial value is in any file here** | § 9.5; it needs a § 9 definition row before the number can be quoted, and `REG-40` says what settles one |
| the radio's attachment | `RF-04` `⊘` | § 13.0 |
| the reference oscillator | 未定, `CLK-50` 殘留 — **there is no value row** | § 8.3 |
| `0xB8003504`'s name | 量 `0x00000000` but **N = `—`** | `REG-36` — a value with no name is not a known-good register |

### 15.6 What § 15 does not establish

🔴 **It is not a configuration.** Nothing in § 15 says which of these values is
*required*. They are what this unit returned while working, and § 16.4 is the
general statement.

⚠️ **Several rows are a single reading, and the table does not hide which.**
`REG-07` left `n = 1` only when a second read was taken; `REG-19b`'s name is 推
with **no source**; `REG-18`'s name is contested between two documents. A row's
own V and N marks live in `SPEC.md` § 9 and are the authority — this table
restates neither.

⚠️ **The loader-state column has a hidden parameter: what was typed before.**
§ 14.3 ⑦ is the measured case — `GIMR` bit 8 is set by any PHY read and never
restored — and `REG-23`'s `AUTOBURN` is the other: it reads `1` at power-on,
`0` after `AUTOBURN 0`, and **`1` again after every reset**. A loader-state
reading is a reading of a *session*, not of a reset state, unless the row says
the dump was the first command.

🔴 **And "loader state" is really two states, which the `PCRP` row above makes
visible.** The loader's `J` handler changes registers *after* the prompt and
*before* the payload runs, so a value read at the prompt is not what a
`J`-entered payload or the kernel inherits. `notes/switch-driver.md` § 16.2 is
the only place that carries the Linux counterparts for the `REG-15`–`REG-19b`
class, in its own `L`/`V`/`R` columns.

🔴 **Three `SPEC.md` § 9 rows have shifted cells, and that is why this table
does not restate their marks.** In `REG-03`, `REG-04` and `REG-32` the value
narrative and the `V`/`N` marks sit one column away from where the header puts
them, so a tool indexing by column reads the wrong cell — the defect class
`CLAUDE.md` describes as *a row silently exempted by two checks*. ⚠️ `REG-39`
has an unescaped `|` inside a code span, which splits its cell, **so that row
passes the cell-count check by accident**. ⚠️ `REG-34`'s address cell reads
`0xB8003100`, which is `TC0DATA`'s, while `REG-09` and the datasheet put
`TCCNR` at `0xB8003110`. **None of these four is repaired by this document**;
they are named so that a reader who disagrees with a mark checks the row rather
than this page.

⚠️ **`REG-12`'s `WatchDogIND` is the one row where three explanations remain
open.** Bit 20 never read back `1` on this die across a real watchdog reset,
with the negative control holding, so *not implemented*, *something cleared it*
and *D's bit position is wrong for this part* are not separated (`REG-12` 殘留
`⊘`). § 12.2's printed reset-cause line is the only observable that survived.

---

## 16. What this whole document does not establish

§ 0 lists the seven things the file does not claim. This section is the same
discipline applied to the assembly rather than to the sections: **what a reader
would be wrong to take away after reading all fifteen.**

### 16.1 It is not a second source for anything

Every number above was already in an owner file before it was copied here, so
**this page cannot raise any row's source count.** A row that was single-source
in `SPEC.md` is single-source here — `BRD-01`, `RF-01`, `REG-19b` and the
`hw_strap` initial value are the named examples — and this document appearing
to agree with them is this document quoting them. `CLAUDE.md`'s two-source rule
is enforced in `SPEC.md` by hand, and § 15's table is not that enforcement.

### 16.2 Nine of the ten sections closed without touching the board

量: the only new measurement this report needed was the power tree's, and it was
not taken (§ 7.4). §§ 6, 8–15 are **assembly from captures already committed**,
which is a statement about cost, not about quality: it means every reading they
rest on was taken for some other gate's question, in that gate's state, with
that gate's controls. **A number taken to answer a different question can be
right and still be the wrong number to quote**, and the state column in § 8 and
§ 15 is the only defence this file has against that.

### 16.3 Four `⊘` rows are named open and none is reopened

| row | what it would take | its recorded reopen condition names |
|---|---|---|
| `CLK-03` `⊘` | a method for `f` that does not go through CPI; this core has no CP0 `Count` (`CPU-42`) | § 8 writing ÷2 as 量 — **§ 8.2 does not** |
| `MEM-08` `⊘` | reading the loader's writes to the memory controller, at the desk | § 15 listing it — **§ 15 lists it as 未定 with no value** |
| `RF-04` `⊘` | tracing the radio's attachment to the SoC | § 13 listing it — **§ 13.0 lists it with no reading in any state** |
| `BRD-01` `⊘` | a multimeter on the regulator's output pin, on a powered board | § 7 written as 量 — **§ 7 is written 讀 and 推** |

🔴 **Whether naming a row is the same as listing it is the gate board's
question, not this file's.** Each of the four is entered above as open, with
the thing that settles it, and none of the four has a value in this document
that it did not already have in `SPEC.md`. If the owner reads any of these four
entries as the reopen trigger, the `SPEC.md` § 17 row changes and this table is
what points at it.

### 16.4 It cannot tell a working board from a configured one

Every 量 above was taken on a board that boots. **Nothing here establishes the
minimum configuration**: no row says which of these register writes is
necessary, and where this project has measured necessity at all it was a
single-variable A/B (`NET-52`, the switch's `TRXRDY`). A reader bringing up a
second board from
this document would be reproducing a state, not deriving one — and § 15's title
is *values this device returned*, not *values to write*.

### 16.5 It is one unit, and the family question is open in both directions

The draft datasheet is for the `-VE1/2/3-CG` variants with embedded DRAM and
this unit has external SDRAM (`MEM-01` 量), so the peripheral register map
being shared is **an assumption this project records as an assumption**
(`SOURCES.json`, source `D`). In the other direction, `CPU-04`'s `RLX4181` rests
on a header that three vendor trees carry byte-identically, that no code reads,
and whose own encoding breaks for two of its entries — three weaknesses
`CLAUDE.md` requires quoting with the name, and they are quoted in § 6 and
§ 14.

### 16.6 What would make this document wrong rather than incomplete

Stated so that the difference is checkable:

* a register value in § 15 read back differently **in the state its row names** —
  that is this file being wrong, and the state column is what makes it falsifiable;
* a § 14 trap that does not reproduce on this die with its own stated trigger;
* any row here disagreeing with its owner file, which makes **this page** stale
  by § 0's rule and not the owner;
* the § 8 tick arithmetic failing to close in either state: loader
  `14,286,057 / 142,858` and Linux `200,005 / 2,000` must both give 100 Hz, and
  if one of them stops doing so, one of the four numbers in it has moved.

⚠️ **And one thing that would not make it wrong:** a reader finding a peripheral
block this document does not list. § 0 ④ says the census is of what has been
touched. An absent block is a gap in the project's coverage, which is what
§ 13.0 is for, and `PROGRESS.md` owns what happens next.
