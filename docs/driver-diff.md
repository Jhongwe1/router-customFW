# The driver diff

**`R5-9`, desk, 2026-09-10 (the fifty-seventh segment). No power, no flash byte,
no device reading.**

`R5` wrote six drivers for this SoC **blind** — `rtl819x-timer`,
`rtl819x-gpio`, `rtl819x-spi` + MTD, `rtl819x-wdt`, upstream `leds-gpio` bound
to my chip, and `rtl819x-keys`. `docs/blind-write-ledger.md` froze, before the
first line of driver source existed, what this repository had already read of
every external implementation. This file is what that was for.

**It is worth writing only if *blind* means something**, and the ledger's § 6
names the one thing that could make it mean nothing. That is what § 1 settles,
and § 1 was written and committed **before either tree was cloned**.

---

## 0. What this file is, and the three things it is not

It compares **my six drivers** against **third-party ports of the same SoC**,
on the two layers `docs/blind-write-ledger.md` § 5 defines. Those definitions
are not restated here; a second copy of a definition is a second owner of it,
and this repository has closed that shape before (`P4b-1`, 2026-09-01).

Briefly, so this page is readable on its own — the owner is the ledger:

* **L1 — fact.** Register addresses, reset values, documented bit positions.
  Three implementations describing **one piece of silicon**. Agreement carries
  no information about independence. This layer is a **cross-check**.
* **L2 — decision.** Divisor semantics, wrap handling, interrupt number,
  which bits are write-1-to-clear, initialisation order, `clocksource`
  `mult`/`shift`, rating and coexistence. **These are choices.** This is the
  layer the ledger protects and the only layer on which a diff means anything.

🔴 **Not ① — a claim that my drivers are better.** A difference on L2 is a
difference. Where the silicon decides which one is right, the experiment that
decides it is named; where it does not, the row says 未定 and stays there.

🔴 **Not ② — a review of the third-party ports.** They are read as evidence
about *decisions*, at the depth § 1 permits and no deeper.

🔴 **Not ③ — independent of the ledger's own limits.** `docs/blind-write-ledger.md`
§ 0 ① states that it is a **lower bound** on contamination: a file read in
2026-08 and never written about is invisible to it. Everything below inherits
that. Two domains are already **not** blind of the vendor and say so in place —
`wdt` (§ 4.10.1 of the ledger, four of seven paths on the decision layer) and
`spi_mtd` (§ 4.5, *the diff's vendor side is spent*).

---

## 1. The derivation check, pre-registered

### 1.1 Why this section is dated, and why it is a commit of its own

`docs/blind-write-ledger.md` § 6, committed **2026-09-02**, states the problem
and imposes the order:

> `driver-diff` compares **me against the third-party ports**. § 4.5 records
> deep reading of the **vendor**. […] **Unless the third-party ports derive
> from the vendor's `arch/rlx`.** If `shibajee`'s or `ggbruno`'s peripheral
> drivers are ports of Realtek's, then reading the vendor is reading their
> ancestor, and the independence is gone without a single third-party file
> having been opened.
>
> When the trees are cloned at `R5-9`, the **first** operation on each is a
> **derivation check** — file headers, copyright lines, SPDX tags, function and
> symbol names against `arch/rlx`'s — performed **before any register map is
> read**, and its result written down before proceeding.

That rule is eight days older than the clone and is in this repository's
history, which is stronger evidence than anything this section could assert
about itself. **What § 1 adds is the operational form** — the exact instrument,
the exact controls, and the verdict rule — and it adds it *before* the data
exists, so the thresholds cannot be chosen to produce an answer.

🔴 **The commit that creates this file contains § 0 and § 1 and nothing else.**
`git log --diff-filter=A -- docs/driver-diff.md` against the clone timestamps
recorded in § 2 is the check, and it is the same shape as the ledger's own
(*committed before any driver source exists*, § 8).

### 1.2 What the check may look at, and what it may not

A derivation check is itself a reading, and a careless one drifts into the
register map it exists to protect. The ledger says so (§ 6, *weak in a stated
way*). The bound is therefore **enforced by the instrument rather than
remembered by the operator**, which is the shape `tools/flashwin.py` already
has for a different forbidden thing.

| may | may not |
|---|---|
| C identifier **names** — functions, macros, structs, enums, typedefs | any **value**: no hex literal, no decimal constant, no bit number |
| file **paths** and directory structure | any **line of source**, in full or in part |
| copyright lines, licence headers, SPDX tags | any **comment body** beyond the copyright block |
| **counts** and set intersections over the above | any register **map**, in any form |

`tools/derivcheck.py` prints identifiers, paths, headers and counts. It has no
code path that prints a source line or a numeric literal, and a case asserts
that on a fixture containing both.

### 1.3 The instrument

For a **reference** tree R and a **candidate** tree C, restricted to a named
set of paths:

1. Extract the identifier set of each — the names a C compiler would see
   defined: `#define` names, function definitions, `struct`/`union`/`enum`
   tags, `typedef` names.
2. Report `|R|`, `|C|`, `|R ∩ C|`.
3. Subtract a **generic baseline** G — identifiers that also occur in the same
   kernel's own `arch/mips` and `include/linux` — and report the
   **distinctive** intersection `|(R ∩ C) \ G|` with the names themselves.
4. Report, separately, the count of files in C whose copyright block names
   Realtek, and the count whose path contains `rlx`.

Step 3 is the one that matters. Two independent ports of Linux to the same SoC
**will** share `init_module`, `platform_driver_register` and `HZ`; they will
not both invent `bsp_tc_init`.

### 1.4 The controls, written before the run

🔴 **A tool reporting *independent* is making a claim.** Two controls, and the
run is void if either fails:

* **Positive control — a known-derived pair must read DERIVED.**
  `src-vendor/wecb-vz-gpl/rtl819x/linux-2.6.30` against
  `src-vendor/rtl819x-toolchain/linux-2.6.30`. `SOURCES.json`'s own entry for
  `wecb-vz-gpl` records that these two *"agree by descent and are ONE vote, not
  two"*. If the instrument cannot see derivation there, every green below is
  worthless.
* **Negative control — an unrelated platform in the same kernel must read
  INDEPENDENT.** `arch/mips/<a non-Realtek platform>` against
  `arch/rlx`, both inside the vendor's own `linux-2.6.30`. Same kernel version,
  same coding era, same subsystem headers, different silicon vendor. If this
  reads DERIVED, the instrument is measuring *generic Linux 2.6.30* and its
  verdicts mean nothing.

⚠️ **Both controls live inside trees this repository has already cloned**, so
they can be run — and were run — **before** either third-party tree arrived.
An instrument validated after the fact is an instrument whose thresholds saw
the data.

### 1.5 The verdict rule, written before the data

Per **tree** and then per **driver domain**:

| verdict | rule |
|---|---|
| **DERIVED** | the candidate contains a directory named `rlx`, **or** ≥ 1 file whose copyright block names Realtek, **or** the distinctive intersection for that domain is non-empty |
| **INDEPENDENT** | none of the three, **and** the domain has an implementation in the candidate at all |
| **ABSENT** | the candidate has no implementation for that domain — no verdict is possible and none is written |

🔴 **What each verdict does to this document, decided now:**

* **DERIVED** for a domain ⇒ that domain's **L2 rows are void** against that
  tree, and the ledger's § 4 entry for the corresponding vendor file is the
  reason. The rows are **not deleted** — they are written and struck, because
  a diff that quietly omits its void rows is a diff whose scope was chosen
  after the fact.
* **INDEPENDENT** ⇒ the domain's L2 rows carry verdicts against that tree.
* **ABSENT** ⇒ the domain is scored against the other tree only, and if both
  are ABSENT the domain has **no diff** and this file says so.

🔴 **The outcome that would make this whole file not worth writing is written
down here, before it is known**: if **both** trees read DERIVED for **all six**
domains, `docs/driver-diff.md` reduces to § 1 plus one sentence, and `R5`'s
`D3` is reported as **not established**. `PROGRESS.md`'s `R5` refutation
condition already says this in the form *"if `R5-0`'s ledger shows the register
maps were already read, `driver-diff.md` **is not written**, and the gate says
so"*. This section is that clause made runnable.

⚠️ **A verdict of INDEPENDENT is not a claim that the port's author never saw
Realtek's code.** It is a claim about what is *in the tree*, which is the only
thing an instrument can reach. The distinction is stated because a reader who
takes INDEPENDENT as *clean-room* is taking more than was measured.

---

*§ 2 onward is written after the clone. Nothing below this line existed when
the commit that created this file was made.*

---

## 2. The derivation check, run

**2026-09-10, the fifty-seventh segment.** Written before any register map was
read, which is what § 1.1 committed to and what `git log` on this file dates.

### 2.1 What was cloned, and when

| tree | branch | commit | its date | files | size |
|---|---|---|---|---|---|
| `shibajee/linux-rtl8196e` | `RTL8196E` (its default) | `ef14875f9dd70d45c1de79a2bee0d26263039b35` | 2020-03-28 | 65,721 | 1.2 G |
| `ggbruno/openwrt` | `master` (its default) | `ee69f81ca5032f13e39ce7c2515ae9c5ee0a78f1` | 2024-03-09 | 10,127 | 97 M |
| `ggbruno/openwrt` | `Realtek` *(fetched second, see § 2.2)* | `8a0ccb93f3431bcf8f5c5d03d4acc2c8e442de67` | 2020-08-04 | 9,226 | — |
| `ggbruno/openwrt` | `lexra` *(fetched second)* | `b3715bde8369f224fc9473c3116967ac1e53d23e` | 2022-09-12 | 9,075 | — |

🟢 **The order is measured, not asserted.** `docs/driver-diff.md` § 0 and § 1
were committed as `161862e` at **2026-09-10T15:26:24Z**; the clone script's own
first line reads `CLONE-RUN-START 2026-09-10T15:27:49Z`, with both trees on disk
by **15:28:58Z** and the extra branches at **15:51:10Z**. **The pre-registration
entered this repository's history eighty-five seconds before the first byte of
either tree reached disk.** The rule it operationalises is older still —
`docs/blind-write-ledger.md` § 6, **2026-09-02**, eight days earlier — so what
the fifty-seventh segment contributed is the instrument and the threshold, and
it contributed them before the instrument was pointed at anything.
*(The first draft of this paragraph said the commit came after the clone. It
was written from memory and the timestamps refute it; the correction is in the
direction that makes the claim stronger, which is exactly why it was measured
rather than recalled.)*

⚠️ **`--depth 1`, so each tree is one commit of one branch.** `git ls-remote`
was used to enumerate what else exists, and is why § 2.2 happened.

### 2.2 🔴 The first defect was in the clone, not in the trees

`ggbruno/openwrt`'s default branch is `master`, and 量 on it: **one** path
anywhere in 10,127 files matches `8196`, and it is
`target/linux/ipq40xx/patches-6.1/700-net-ipqess-...patch` — a **Qualcomm**
driver whose patch text happens to contain those digits. 🟢 The grep's control
fires: the same search for `8367` returns **154** files.

So on `master` the verdict for every domain would have been **ABSENT** — and
that would have been a fact about **which branch the clone script took**, not
about the repository. `git ls-remote --heads` shows **10** branches, two of
which are `Realtek` and `lexra`. `lexra` is the name of this SoC's **CPU
core**.

> **The clone script took each repository's default branch and nothing checked
> that the default branch was the right one.** It was right for `shibajee`
> (whose default *is* `RTL8196E`) and wrong for `ggbruno`. One tree out of two
> is not a rule, it is a coin that came up heads.

Fetched, and the two branches are different SoCs: `Realtek` carries
`target/linux/realtek/files-4.14/` with **RTL8196E** support; `lexra` is
*"Initial RTL8197f"* and its files are `arch/mips/rtl838x/`. Everything below
uses `origin/Realtek`.

### 2.3 The controls, run before any candidate was compared

`tools/derivcheck.py`, self-test **22 passed, 0 failed**. Baseline: the vendor
kernel's `include/linux` and `arch/mips/include`, plus `shibajee`'s own
`include/linux` and `arch/mips/include` — **178,038 identifiers from 5,081
files** — subtracted from every intersection below.

| control | pair | required | measured |
|---|---|---|---|
| **positive** | `wecb-vz-gpl` vs `rtl819x-toolchain`, the same file `drivers/char/rtl_gpio.c` | DERIVED | **175** distinctive of 176 candidate identifiers |
| **negative A** | vendor `arch/rlx/bsp` vs vendor `arch/mips/mti-malta` — two board directories in one kernel | INDEPENDENT | **0** |
| **negative B** | vendor `arch/rlx/bsp` vs `shibajee` `arch/mips/lantiq` — cross-tree, cross-era, another vendor's MIPS router SoC | INDEPENDENT | **0** |
| **negative C** | `shibajee` `arch/mips/lantiq` vs `arch/mips/ath79` — two router SoC board directories, neither Realtek | INDEPENDENT | **0** |

⚠️ **The positive control is narrower than § 1.4 wrote it.** § 1.4 named the two
whole trees; what ran is one file present in both, chosen because a whole-tree
pair would have been dominated by the mainline kernel they share and would have
measured almost nothing about Realtek. The narrowing is recorded rather than
silently taken, and it makes the control **harder**: one 70 KB file against one
70 KB file, with no shared mainline bulk to inflate the intersection.

🟢 **The positive control is not byte-identical to its reference** — 71,494
bytes against 66,608, two SDK generations of the same file — so the instrument
had to see derivation *through divergence*, which is the case that matters.

🔴 **And the controls found a defect in the instrument before any candidate was
looked at, which is the entire reason they run first.** On the first pass both
negative controls read **2**, and both times the same two names:
`get_system_type` and `prom_putchar`. Those are mainline `arch/mips` platform
API — every MIPS board **defines** them because a generic header **declares**
them — and the extractor skips declarations on purpose (self-test `E5`). So
the baseline was under-inclusive for exactly the class of name two unrelated
boards are obliged to share.

**The fix is to the baseline, not to the threshold**, and its own refutation
condition was written before it was applied: *if the positive control's
distinctive intersection falls below 100, the fix has destroyed the
instrument's sensitivity and must be reverted.* 量 after: negative A, B and C
all went to **0** and the positive control read **175 — unchanged to the
identifier**, across a baseline that grew from 71,469 to 178,038.

⚠️ **A threshold was never introduced.** The floor is **0**, measured on three
negative controls rather than chosen, and every verdict below is *zero or
non-zero*.

### 2.4 🔴 The verdict rule as frozen has a defect, and running it is what found it

§ 1.5 says a tree reads DERIVED if it contains *"≥ 1 file whose copyright block
names Realtek"*. 量, applied to the whole tree as written:

| tree | files whose copyright block names Realtek |
|---|---|
| `shibajee` | **809** |
| `ggbruno` `master` | **120** |

and they are `rtsx_pci.h`, `rt5668.h`, `rtl8366rb.c`, `rtl8367c` — **mainline
Realtek card-reader, audio-codec, PHY and switch drivers that ship in every
kernel**. The clause fires on any modern Linux tree and carries no information.

**It is not rewritten here.** § 1.5's own framing is *"Per **tree** and then per
**driver domain**"*, and applied per domain — to the files that implement that
domain for *this* SoC — the clause is meaningful and is what § 2.5 uses. What
is recorded is that the whole-tree form is defective, that the defect was found
by **running** the rule rather than by reading it, and that a rule which cannot
come out either way is not a rule. `docs/GATE-RESULTS.md`'s operating clause is
the reason this paragraph exists instead of a quiet edit to § 1.5.

### 2.5 The verdicts

Reference throughout: the vendor's `linux-2.6.30/arch/rlx/bsp` (11 files, 397
identifiers) and `boards/rtl8196e/bsp` — the tree `docs/blind-write-ledger.md`
§ 4.2 records as **fully read** on the decision layer.

| tree | domain | candidate | idents | distinctive | verdict |
|---|---|---|---|---|---|
| `shibajee` | board / bsp | `arch/mips/rtl8196e/` (4 files) | 26 | **0** | 🟢 INDEPENDENT |
| `shibajee` | SoC register header | `arch/mips/include/asm/mach-rtl8196e/` | 21 | **0** *(raw intersection also 0)* | 🟢 INDEPENDENT |
| `shibajee` | **timer** | `drivers/clocksource/timer-rtl8196e.c` | 29 | **0** | 🟢 INDEPENDENT |
| `shibajee` | **irq** | `drivers/irqchip/irq-rtl8196e.c` | 8 | **0** | 🟢 INDEPENDENT |
| `shibajee` | gpio, spi/mtd, wdt, leds, keys | — | — | — | ⚪ ABSENT |
| `ggbruno` | **timer** | `arch/mips/realtek/rtl819x-timer.c` | 27 | **0** | 🟢 INDEPENDENT |
| `ggbruno` | **gpio** | `arch/mips/realtek/gpio.c` | 10 | **0** | 🟢 INDEPENDENT |
| `ggbruno` | **irq** | `arch/mips/realtek/irq.c` | 33 | **0** | 🟢 INDEPENDENT |
| `ggbruno` | **spi** | `drivers/spi/spi-realtek.c` | 30 | **0** | 🟢 INDEPENDENT |
| `ggbruno` | setup | `arch/mips/realtek/setup.c` | 9 | **0** | 🟢 INDEPENDENT |
| `ggbruno` | **prom / early console** | `arch/mips/realtek/prom.c` | 11 | **4** | 🔴 **DERIVED** |
| `ggbruno` | SoC headers | `arch/mips/include/asm/mach-realtek/` (4 files) | 118 | **0** *(raw 0)* | 🟢 INDEPENDENT |
| `ggbruno` | wdt, leds, keys, mtd | — | — | — | ⚪ ABSENT |

🔴 **The one DERIVED row is `ggbruno`'s `prom.c`, and the four names are the
vendor's own prefix**: `BSP_LSR_THRE`, `BSP_TXRST`, `BSP_UART0_FCR`,
`BSP_UART0_LSR`. Four UART register macros in the early-console path.

🟢 **The file's own copyright block agrees with the instrument, and nobody
arranged that.** `rtl819x-timer.c`, `gpio.c` and `irq.c` carry
*Copyright (C) 2019 Gaspare Bruno*; `spi-realtek.c` carries *Copyright (C) 2017
Weijie Gao*; and **`prom.c` and `setup.c` carry no copyright line at all** —
the file with no attribution is the file carrying the vendor's names.

> **No `driver-diff` row of mine is voided.** The early UART is not one of
> `R5`'s six drivers, so the DERIVED verdict lands outside every domain this
> document scores. `R5`'s `D3` survives, and § 3 is worth writing.

### 2.6 🟢 Two things the check found that it was not looking for

**① A third party names this SoC's core the same way this project does.**
`shibajee`'s `arch/mips/boot/dts/realtek/rtl8196e.dtsi` carries
`compatible = "lexra,rlx4181"`. This repository reached `RLX4181` from
`PRId = 0x0000CD01` measured on the die against the assignment table in
`arch/rlx/include/asm/cpu.h` (`CLAUDE.md`'s *Never write `RLX5281`* row,
lifted 2026-08-27), and the three weaknesses recorded with it still stand — one
source, three byte-identical copies, no code reads the table. **This is a
fourth source and it is not one of the three**, written by someone with no
connection to this project.

**② `shibajee` has a board file for a TOTOLINK.**
`arch/mips/boot/dts/realtek/rtl8196e_totolink_n100re.dts`. The N100RE is not
the N150RT this project owns, and nothing here treats it as one — but it is the
closest published board description to this device that exists, and `D2`'s
bindings have a second opinion available for the first time.

### 2.7 What this check does **not** establish

1. 🔴 **It reads names, not structure.** Two implementations can be derived and
   renamed. The instrument cannot see that and neither can this section.
2. 🔴 **A verdict of INDEPENDENT is not clean-room.** It is a statement about
   what is in the tree. Both authors could have read Realtek's code and
   reimplemented from it; nothing here reaches that.
3. ⚠️ **Candidate sets are small** — 8 to 33 identifiers, against the positive
   control's 176. A small file has fewer chances to intersect. What bounds the
   worry is *which* names are there: `shibajee`'s 26 are sixteen `GPIO_A0`
   style pin names, eight mainline platform hooks (`plat_time_init`,
   `arch_init_irq`, `prom_init`, `get_system_type`, …) and two of its own
   (`rtl8196e_machine_restart`, `rtl8196e_totolink_n100re_setup_leds`).
   **The vendor calls that first function `bsp_machine_restart`.** Two
   implementations of one operation with two different names is the signature
   the instrument is built to see, and here it is visible without the
   instrument.
4. ⚠️ **`arch/mips/rtl8196e/time.c` is ten lines and `irq.c` is eight.** Those
   two per-file comparisons are underpowered and are not what the verdict rests
   on; the real drivers are under `drivers/clocksource/` and `drivers/irqchip/`
   and were compared separately, both at **0**.
5. ⚠️ **One branch of one repository each**, at `--depth 1`. `ls-remote` bounds
   what else exists but nothing here reads it.
6. 🔴 **A name collision that looks like evidence and is not.** `ggbruno`'s
   timer file is `arch/mips/realtek/rtl819x-timer.c` and mine is
   `rtl819x-timer`. Neither of us saw the other: `rtl819x` is the vendor's own
   family prefix, visible in `src-vendor/wecb-vz-gpl/rtl819x/` and in every
   board directory of the SDK, and two people naming a driver after the family
   is convergence on a public label. It is written down because a hostile
   reader would find it and it would look worse unexplained than explained.

---

## 3. The diff

Written **after** § 2 and after the commit that carries it, which is the order
`docs/blind-write-ledger.md` § 6 imposed. Everything below reads the
third-party implementations at full depth; nothing above did.

### 3.0 The three sides, and what each one is

| | what it is | depth |
|---|---|---|
| **mine** | `rtl819x-timer` 4.1, `rtl819x-gpio` 1.1, `rtl819x-spi` 1.1, `rtl819x-wdt` 1.0, upstream `leds-gpio` bound to my chip, `rtl819x-keys` 1.0 — six drivers written blind of any third-party port, all six run on the silicon | the source, mine |
| **`shibajee`** | a **modern-kernel** port: `drivers/clocksource/timer-rtl8196e.c` (237 lines), `drivers/irqchip/irq-rtl8196e.c` (104), a DT `.dtsi`, a board `.dts` for a TOTOLINK N100RE, and one 35-line SoC header | full source read |
| **`ggbruno`** | an **OpenWrt 4.14 target**: `arch/mips/realtek/{rtl819x-timer,gpio,irq,setup,prom}.c`, `drivers/spi/spi-realtek.c`, `arch/mips/mm/c-lexra.c` | full source read |

⚠️ **`shibajee` has no gpio, spi, wdt, led or keys driver**, and `ggbruno` has
no wdt, led, keys or MTD driver. Four of my six drivers therefore have **at
most one** partner, and two have none. That is a fact about what exists in
public, and it is why the scoreboard in § 3.7 has as many ABSENT cells as it
does.

### 3.1 L1 — the timer block, and three implementations agree on every field

Base `0xB8003100`. `docs/blind-write-ledger.md` § 5 says agreement here is
expected and carries no information about independence; it is a **cross-check
of my register map**, and that is what it delivers.

| field | mine | `shibajee` | `ggbruno` |
|---|---|---|---|
| `TC0DATA` | `+0x00` | `+0x00` | `+0x00` |
| `TC1DATA` | `+0x04` | `+0x04` | `+0x04` |
| `TC0CNT` | `+0x08` | `+0x08` | `+0x08` |
| `TC1CNT` | `+0x0c` | `+0x0c` | `+0x0c` |
| `TCCNR` | `+0x10` | `+0x10` | `+0x10` |
| `TCIR` | `+0x14` | `+0x14` | `+0x14` |
| `CDBR` | `+0x18` | *(not used)* | `+0x18` |
| `TC0EN` / `TC0MODE` / `TC1EN` / `TC1MODE` | 31 / 30 / 29 / 28 | 31 / 30 / 29 / 28 | 31 / 30 / 29 / 28 |
| `TC0IE` / `TC1IE` / `TC0IP` / `TC1IP` | 31 / 30 / 29 / 28 | 31 / 30 / 29 / 28 | 31 / 30 / 29 / 28 |

**Fourteen fields, three implementations, no disagreement.** 🟢 The row that is
worth something beyond the cross-check is the last one: `SPEC.md` `IRQ-08` and
`IRQ-09` rest on `TCIR` bit 30 being TC1's interrupt *enable* and bit 28 being
its *pending* flag, and this project reached that from one datasheet table plus
readings on the die. **Two independent implementations now say the same thing**,
and neither of them is the datasheet.

### 3.2 L1 — the rest of the map, and eleven registers this project has never named

`shibajee`'s 35-line `arch/mips/include/asm/mach-rtl8196e/rtl8196e.h` is a bare
address list, and it lines up with this project's readings exactly:

| register | this project | `shibajee` |
|---|---|---|
| `PABCD_CNR` | `0xB8003500` (`REG-26`, 量) | `0x3500` |
| `PABCD_DIR` | `0xB8003508` (`REG-27`, 量) | `0x3508` |
| `PABCD_DAT` | `0xB800350C` (`BRD-05`, 量) | `0x350C` |
| `CDBR` | `0xB8003118` (`REG-11`, 量) | `0x3118` |
| `WDTCNR` | `0xB800311C` (`REG-12`, 量) | `0x311C` |
| `UART0` | `0xB8002000` | `0x2000` |

🟢 **Five addresses this project measured on the die, confirmed by a source
that is not the datasheet, not the vendor SDK, and not this project.**

🔴 **And it carries ELEVEN this repository has never named, in six rows:**

| register | offset | what it is for |
|---|---|---|
| `GPABCDTYPE` | `0x3504` | the port-type word, between `CNR` and `DIR` |
| `GPABCDISR` | `0x3510` | GPIO interrupt status |
| `GPABIMR` | `0x3514` | interrupt mask, ports A and B |
| `GPCDIMR` | `0x3518` | interrupt mask, ports C and D |
| `GPEFGHCNR` / `TYPE` / `DIR` / `DATA` / `ISR` | `0x351C`–`0x352C` | a **second** four-port bank |
| `GPEFIMR` / `GPGHIMR` | `0x3530` / `0x3534` | its two mask registers |

⚠️ **This is 讀 from one source and nothing here measures it.** It is written
down because two of this project's open items point straight at it:
`docs/KNOWN-ISSUES.md`'s *`.to_irq` is NULL* (the three GPIO-interrupt
registers are `0x3510`/`0x3514`/`0x3518`), and `GPIO-1`, *which of `PABCD`'s
four ports bit 5 belongs to* — a second bank named `EFGH` makes the packing
question sharper rather than answering it.

### 3.3 🔴 L1's one disagreement, and this project has already measured the answer

`shibajee` treats `TC0CNT`/`TC1CNT` as **plain 32-bit** counters:
`clocksource_mmio_init(base + TC0_CNT, …, 32, clocksource_mmio_readl_down)`,
and it seeds them with `0xFFFFFFFF`. `ggbruno` says *"two clocks of 28 bits"*
and applies `RTLADJ_TICK(x) = x >> 4` on every read and `delta << 4` on every
write. Mine uses `RTL819X_TC_VALUE_SHIFT 4` with the same shape.

**Two say the count sits in bits 31:4; one says there is no shift.**

🟢 **The die settles it, and the reading is already in this repository.**
`SPEC.md` `REG-05`: `TC0DATA` reads `0x0022E0A0`, which is `142,858 << 4`, and
142,858 is the reload that produces the measured 100.0018 Hz tick. `TM-3`
(seating 11) is the other direction: this driver *wrote* a period of `2^27` and
`TC1DATA` read back **`0x80000000`** = `0x08000000 << 4`.

> **`shibajee`'s clocksource reads a register that is sixteen times its own
> count.** 推, and stated as such: its rate comes from the device tree, so the
> clocksource would advance sixteen times too fast unless the DT clock is
> scaled to compensate. The experiment that settles it is one boot of that
> image on this part, which this project has not run and does not plan to.

⚠️ `ggbruno` and I agree on the shift and differ on the field width — it calls
the field **28** bits and my driver's ceiling is `2^27`. That is not a
disagreement: my `RTL819X_TC1_BITS_MAX 27` is a **period** ceiling and the
comment beside it already says *"the ceiling is the 28-bit `TC1Data[27:0]`
field"*. Two sources, one number.

### 3.4 L2 — the decision layer

#### 3.4.1 Which timer is which, and the two ports choose opposite

| | clocksource | clockevent |
|---|---|---|
| mine | TC1, **rating 0** | TC1, **rating 300** |
| `shibajee` | **TC0**, rating 500 | **TC1**, rating 200 |
| `ggbruno` | **TC1**, rating 200 | **TC0**, rating 100 |

🔴 **`shibajee` and `ggbruno` assign the two timers to opposite roles.** The
silicon does not prefer either — the two timers are the same block twice — so
this is a pure decision and it is exactly the kind of row § 5 of the ledger
says the diff exists to find. **Neither is wrong.**

🔴 **Mine is different from both, and for a reason neither of them has.** My
driver runs *beside* a vendor kernel whose tick already owns TC0 and whose
handler writes `TCIR` a hundred times a second (`IRQ-09`). So TC1 is not a
choice: it is the only timer available. And the clocksource sits at **rating 0**
— below `jiffies`' 1 — deliberately, so the kernel will not switch to it, while
the clockevent sits at 300 so the tick core will. **The two third parties
replace the vendor; I coexist with it.** That is a different problem, not a
better answer, and this row would read as a quality judgement if it did not say
so.

#### 3.4.2 🔴🔴 The interrupt acknowledge — and this is the row the silicon decided

`TCIR`'s two `IP` bits are **write-1-to-clear**.

| | what the handler writes |
|---|---|
| the **vendor** | `REG32(BSP_TCIR) \|= BSP_TC0IP` — read, OR, write back |
| `shibajee` | `status = readl(TCIR); writel(status, TCIR);` — *"Clear all interrupts"* |
| `ggbruno` | `tc0_irs = tc_r32(IR); tc0_irs \|= TC0_PENDING; tc_w32(tc0_irs, IR);` |
| **mine** | `ackip` writes **one bit**, `1u << 28`, and reads it back |

**Three of the four commit the same read-modify-write on a write-1-to-clear
register**, and each of the three therefore clears *every* pending bit that
happened to be set — including one belonging to a driver it has never heard of.

🟢 **This project measured the consequence rather than arguing it.**
`SPEC.md` `IRQ-09`, seating 12: the vendor's tick handler clears my `TC1IP`
about a hundred times a second, so **a `TCIR` pending bit on this part has a
lifetime of at most one 10 ms tick**, which bounds every single-sample reading
of that register this project has ever taken. The card's own decision cell came
out `0|0` and the reading was right while the assignment was wrong.

> **Two independent third parties, written years apart, in different kernels,
> reproduce the vendor's defect; the one implementation that does not is the
> one whose author had the register's behaviour measured in front of him.** The
> row is not *my code is better* — it is that a measurement bought a decision
> that reading the datasheet did not.

⚠️ And the honest half: my single-bit write is only safe because `TCIR`'s `IP`
bits are documented write-1-to-clear *and* because `ackip` proves it at run time
before `reqirq` is allowed to proceed. The driver's own comment says a proof at
one instant is not a proof at every instant, and the handler carries the guard
again.

#### 3.4.3 The divider, and a third source for `CLK-06`

`ggbruno` writes `div_fac << 16` into `CDBR` at `+0x18`, with
`div_fac = 200000000 / timer_rate` — so **the divisor occupies the high 16 bits
and the base clock is 200 MHz**.

🟢 Both halves cross-check against readings this project already has.
`SPEC.md` `TM-1` (seating 11): under Linux `CDBR` reads `0x03E80000` and
`0x03E8` is **1000**; the loader leaves `0x000E0000` and `0x000E` is **14**.
Both are the high half. And `CLK-02` measured the base clock at
**200.0049 MHz ± 7 ppm**.

`CLK-06` was 讀 from the draft datasheet's Table 26 and this repository has one
copy of that datasheet. **It now has a second, independent 讀** — and `shibajee`
supplies neither, because its driver never touches `CDBR` at all and takes its
rate from the device tree.

#### 3.4.4 Wrap handling, and mine is the one with a recorded failure

| | how the wrap is handled |
|---|---|
| mine | software extension `tc1_ext`, with a `tc1_ext_trusted` flag and a reported maximum sample gap |
| `shibajee` | none — `clocksource_mmio_readl_down`, 32-bit mask, the core does it |
| `ggbruno` | none — `CLOCKSOURCE_MASK(28)`, the core does it |

🔴 **The two third parties took the simpler option and mine is the one whose
extension has a measured failure on the record.** `SPEC.md` `CLK-22`: over a
703.46 s arm the real gap was **140,693,532** counts, a full `2^27` period was
lost, and `tc1_ext_trusted` read **1** while claiming the reading was
trustworthy. Handing the wrap to the clocksource core, as both of them do,
cannot fail that way because it never claims anything about a gap it did not
see.

⚠️ It is not a free swap. The core's mask-based unwrap needs the clocksource to
be *read* more often than half a wrap, which is exactly what my rating-0
registration prevents: nothing reads it. The row is a genuine trade and it is
recorded as one.

#### 3.4.5 GPIO interrupts — `ggbruno` shows they are implementable and I do not implement them

`docs/KNOWN-ISSUES.md` carries *`.to_irq` is NULL* for `rtl819x-gpio`, on the
stated ground that no GPIO interrupt has been measured on this part.
`ggbruno`'s `arch/mips/realtek/gpio.c` (301 lines) has a full `irq_chip` with a
chained parent handler, `irq_data_get_irq_chip_data` and
`irq_desc_get_handler_data`.

🟢 **So it is not that the part cannot; it is that this project has not.** With
§ 3.2's `GPABCDISR` / `GPABIMR` / `GPCDIMR` addresses beside it, that item stops
being *unknown how* and becomes *unmeasured*, which is a smaller claim and a
different piece of work. **This does not close it** — nothing here is 量, and
one boot of `ggbruno`'s image on this board is not an experiment this project
is going to run.

#### 3.4.6 The three rows where nothing can be compared

`wdt`, `leds` and `keys`: both third-party trees are **ABSENT**. For `leds` and
`keys` that is expected and correct — my `R5-7` and `R5-8` bind **unmodified
upstream drivers** to my chip, so there is nothing SoC-specific to diff and the
comparison that matters (does upstream bind?) was answered on the silicon.
For `wdt` there is genuinely nothing: neither port implements one, and
`docs/blind-write-ledger.md` § 4.10.1 already records that my watchdog's
**vendor** side is spent, so that domain has no blind diff available from any
direction.

### 3.5 Two defects found by reading, and both were measured before being written down

🔴 **Neither of these is a claim about this board.** They are claims about C,
and each was reproduced with a compiled control before it entered this file —
because the first version of one of them was wrong.

**① `shibajee`'s four `TCCNR` bit-setters cannot set any of the four bits they
exist to set.** Each is `u16 tccnr; tccnr = readl(base + TCCNR); … tccnr |=
TCCNR_TC0_EN_BIT; writel(tccnr, base + TCCNR);` with the four control bits at
31:28. The read truncates to sixteen bits; the `|=` promotes to `int`, ORs, and
converts back to `u16`, discarding bit 31 again.

量, the same function body compiled twice with one type changed, which is the
control:

| | operation | result |
|---|---|---|
| `u16` | `enable(1)` on `TCCNR = 0` | **`0x00000000`** — the enable bit never arrives |
| `u16` | `disable(0)` on `TCCNR = 0xC0000000` | **`0x00000000`** — it also clears `TC0MODE`, which it was not asked to touch |
| `u32` | `enable(1)` on `TCCNR = 0` | `0x80000000` ✅ |
| `u32` | `disable(0)` on `TCCNR = 0xC0000000` | `0x40000000` ✅ |

🔴 **And `-Wall` on the MIPS cross compiler reports zero warnings.** It takes
`-Wconversion`, which the kernel does not use. **It is silent.**

⚠️ **My driver does not have it, and the reason is not foresight.** I used
`u32` because the registers are 32 bits wide, which is the obvious choice; the
avoidance is a consequence. 量, before this paragraph was written: the five
drivers' only narrow types are two byte arrays for a digest comparison, one
struct field, and two explicitly-cast ring-buffer fields. **No narrow type is
the destination of a register read anywhere in my tree.**

**② `shibajee`'s interrupt dispatcher shifts by 128, and the value comes out
right anyway — which is the more interesting outcome.**
`#define RTL8196E_NR_IRQS 128` and then
`pending = gimr & gisr & ((1 << RTL8196E_NR_IRQS) - 1)`. `1 << 128` on an `int`
is undefined behaviour.

🔴 **The first draft of this row said the mask folds to zero and every interrupt
would be reported spurious. 量 refutes it**: GCC constant-folds
`(1 << 128) - 1` to **`0xffffffff`** — the value the author meant — on the host
and on the big-endian MIPS cross compiler alike, and warns
`-Wshift-count-overflow` in both.

What survives is narrower and still real: **the code is wrong and works, and
what makes it work is the compiler's choice rather than anything in the
language.** A fold to `0` is equally permitted, and then `pending` is always
zero and every interrupt is spurious. In a kernel built `-Werror` the warning
is a build failure. `RTL8196E_NR_IRQS 128` against a 32-bit `GIMR`/`GISR` is a
separate, plain inconsistency.

> **That row nearly went in as a confident false claim.** The ten seconds it
> took to compile it is the whole difference, and it is recorded here rather
> than quietly corrected.

### 3.6 The scoreboard

| driver | `shibajee` | `ggbruno` | L1 | L2 rows with a verdict | L2 rows 未定 |
|---|---|---|---|---|---|
| `rtl819x-timer` | INDEPENDENT | INDEPENDENT | 14 fields agree, **1 disagrees** (§ 3.3) | § 3.4.1, § 3.4.2, § 3.4.3, § 3.4.4 | — |
| `rtl819x-gpio` | ABSENT | INDEPENDENT | 3 agree, **7 new addresses** (§ 3.2) | § 3.4.5 | which port bit 5 is on (`GPIO-1`) |
| `rtl819x-spi` + MTD | ABSENT | INDEPENDENT | not compared | — | the transaction order is the vendor's; ledger § 4.5 voids the blind claim |
| `rtl819x-wdt` | ABSENT | ABSENT | 1 agrees (`WDTCNR`) | — | ledger § 4.10.1: informed contrast, not a blind diff |
| `leds-gpio` (upstream) | ABSENT | ABSENT | — | nothing SoC-specific to diff | — |
| `rtl819x-keys` | ABSENT | ABSENT | — | nothing SoC-specific to diff | — |

### 3.7 What this diff does not establish

1. 🔴 **It is not a claim that my drivers are better.** § 3.4.1 is a difference
   in *problem*; § 3.4.4 is a trade my side loses on simplicity; § 3.5's two
   defects are C, not engineering judgement, and one of them I nearly got
   wrong.
2. 🔴 **Neither third-party image has been run on this board and neither will
   be.** Every statement about what their code *would do* on this part is 推
   and says so.
3. 🔴 **Two of six drivers have no partner at all** and two more have exactly
   one. A diff over six drivers where four cells are ABSENT is thinner than the
   plan imagined, and the ledger's own § 4.10.1 and § 4.5 had already removed
   the blind claim from two of them for a different reason.
4. ⚠️ **The L1 agreement is worth exactly what § 5 says it is worth.** Three
   implementations describing one part agree because it is one part. What it
   buys is a cross-check on my transcription, and it delivered that on fourteen
   timer fields and five addresses.
5. ⚠️ **`spi` was not compared field by field.** `ggbruno`'s
   `drivers/spi/spi-realtek.c` (340 lines) is a full SPI-master driver and mine
   is a read-only MTD path sharing a controller with the vendor's. The two
   solve different problems and the comparison would have been shaped by that
   rather than by either implementation. It is left as an explicit gap.
