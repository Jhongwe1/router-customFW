# The blind-write ledger

**`R5-0`, desk, 2026-09-02. No power, no flash byte, no device reading.**

`R5` writes six drivers **blind**, and `docs/driver-diff.md` — the deliverable
the plan calls rarer than the drivers themselves — is worth writing only if that
word means something. This file freezes what this repository had read of each
external implementation **before the first line of driver source exists**,
because afterwards *"I had not read it"* is unverifiable.

Its ordering is checkable: `git log` shows this file committed before any file
under `config/rlxfw-src/` that is a driver. Its **contents** are checkable a
different way — see § 2.

---

## 0. What this ledger claims, and the three things it does not

**Claims.** For each of the **thirty-two** external implementation sources this
repository cites, in scope for one of `R5`'s six drivers *(twenty-seven when
this file was written at `R5-0`; `R5-1` added five and the number moves every
time this repository cites a source it had not cited before — which is exactly
the event this file exists to catch)*: which tree it belongs
to, how deep the contact went, what was taken, and whether what was taken lands
on the layer `driver-diff` compares.

🔴 **Does not claim ① — that it is a record of what I read.** It is a record of
what this repository **wrote down**. A file read and never mentioned is
invisible to it. This is a **lower bound on contamination**, and the whole
ledger is to be read that way. What makes the bound useful rather than
decorative is that this project writes its greps down:
`notes/vendor-kernel-isa.md` is an entire file of them, and it is where the
citation this ledger was nearly written without came from.

🟢 **The bound was tightened by one measurable amount, and the result is
that nothing in scope is lost.** `ledgerscan` reads the working tree at `HEAD`.
A path written in some commit and later edited out would still be evidence of
reading, and it would be invisible. 量 2026-09-02, over **167 commits and
24,797,072 bytes** of `git log --all -p` (added lines only, `upstream/`
excluded, this tool's fixtures excluded): **92 paths appear anywhere in
history, 95 at `HEAD`, and exactly 2 are in history and not at `HEAD`** —
`arch/rlx/include/asm/processor.h` and `lib/decompress_inflate.c`, **both
out-of-scope**.

> **The `HEAD`-only scan loses nothing in scope.**

🔴 **And this reading refuted itself the moment it was written down, which
is a property of it rather than a defect.** Naming those two paths put them
*into* `HEAD`; 量 immediately afterwards, the same scan finds both at `HEAD`
and the difference is now **0**. The quantity is a statement about the state of
this repository at an instant, and recording it changed that state.

> **Re-deriving it requires checking out a commit from before this one.** It is
> the same shape as the citation counts in § 4 — a number that moves when you
> write about it — and it is the sharper instance, because here the *writing*
> is what moved it rather than the discussion around it.

⚠️ That closes one gap and not the general one: a file read and never written
about at all is still invisible, and no amount of history scanning reaches it.
The sweep is not yet a `ledgerscan` action — see `PROGRESS.md` `LEDGER-1` — so
this reading is a one-off with its method stated rather than a check that
re-runs.

🔴 **Does not claim ② — that a citation's absence proves a file was not read.**
Three domains — `gpio`, `wdt`, `led` — have **zero** cited paths, and `keys`
has one that is an example rather than a reading (§ 4.1). That is
this ledger's strongest row and its weakest guarantee at the same time. It is
strong because those four drivers are the ones whose independence is best
supported; it is weak because it rests on ① . `tools/ledgerscan.py` `P15` makes
each of those four domain rules fire on a synthetic tree, so the zero is a
reading and not a rule that cannot report.

🔴 **Does not claim ③ — that reading only the vendor tree leaves the diff
intact.** See § 6. Whether the third-party ports derive from the vendor's
`arch/rlx` is **undetermined here and cannot be determined without cloning
them**, which is the act the ledger exists to date.

---

## 1. The measurement that made this a tool and not a paragraph

量 2026-09-02, before `tools/ledgerscan.py` existed. A hand-typed
`grep -ril rlx-time` over this tree returned **0 files**, and the sentence about
to be written from it was *"this repository has never read the vendor's
timer"*.

That sentence is false.

🔴 **And the first account of why was also wrong, which makes the lesson
sharper rather than weaker.** The first version of this section said *the
needle was wrong — the vendor's timer is `rlx-cevt.c`, not `rlx-time.c`*. 量
2026-09-02, a directory listing with no file opened: `arch/rlx/kernel/` carries
**both** `rlx-time.c` **and** `rlx-cevt.c`.

**So the grep named a real file and `0` was the correct answer.** This
repository has never cited `rlx-time.c`. What was wrong was the *inference* —
and it is the inference this whole ledger has to defend against:

> **Zero citations is not zero reading, and a zero on one spelling says nothing
> about another.**

🔄 **2026-09-06: the sentence below is history.** § 4.3's row for this file
now reads `full`, and `R5-3b-1` is the segment that opened it. The paragraph
is kept because it is what bounded the claim for version 1.0's source, which
is the version `git log` can still date.

What this repository *has* cited is `arch/rlx/kernel/rlx-cevt.c`, **to the
line** (`notes/vendor-kernel-isa.md:33`, `:139,226`). `CLAUDE.md`: *a tool
reporting `0` is making a claim; every sweep needs a positive control.*
`ledgerscan`'s `P1` is that control and it is this citation, chosen because it
is the one that was nearly missed.

---

## 2. Method — what is computed and what is judged

| | who | what |
|---|---|---|
| **completeness** | `tools/ledgerscan.py scan` | every path-shaped citation of an external source, in `git ls-files` (**1,448** on 2026-09-03 after `R5-2`, **1,447** earlier the same day at `R5-1`, 1,445 at `R5-0`; the number grows with the repository, and `ledgerscan scan` prints it rather than this table fixing it) and in `upstream/` (302, walked — `git ls-files` cannot see inside a submodule) |
| **domain** | the tool | which of `R5`'s drivers a path could belong to. Over-inclusive by design: `dt` and `bsp` are cross-domain, because a device tree and a board file each describe every peripheral |
| **origin** | the tool's path rules, restated per row below | *generic Linux* / *vendor Realtek* / *third-party port*. **Only the last two can cost independence** |
| **depth** | the tool | `name` (a path appears) or `line` (a line number travels with it) |
| **what was taken, and on which layer** | **me** | a judgement. It is not computable and it is not delegated to a keyword |
| **the join** | `ledgerscan check` | every in-scope path the scan finds must have a row here. A path in the tree and not in this file is a ledger that has gone stale, and it exits 1 |

That last row is what makes this file survive the gate. Writing about a new
vendor file in `LOG.md` — which is how reading gets recorded here — makes
`check` fail until this ledger says what was taken from it.

### 2.1 The rule this ledger follows about re-reading, and the version of it that was wrong

`boards/rtl8196e/bsp/setup.c:134-175` is quoted in `notes/kernel-build.md`
§ 11.2 as a 42-line extract with an elision. Whether those 42 lines also contain
a timer or GPIO initialisation is **not recorded anywhere**, and the obvious way
to find out is to open the file again.

🔴 **That is the wrong move and it is written here because it was the first one
considered.** I read those lines on 2026-08-28; I do not remember what was in
them beyond the extract. *"Read and not remembered"* and *"not read"* are not
the same state, but re-reading converts the first into *"read and remembered"*,
which is new contamination bought to make a ledger tidier.

**The rule, therefore: this ledger records RANGES, not contents.** A cited range
is treated as fully read. Nothing is re-opened to make a row more precise. The
direction of the resulting error is conservative — the ledger over-reports
contact — and that is the correct direction for a document whose purpose is to
constrain a later claim.

---

## 3. The quarantine, and what it is not

Five public trees are recorded in `SOURCES.json` with `"fetch": "later"`. 量
2026-09-02, `ledgerscan quarantine`: **all five absent from `src-vendor/`.**

| tree | destination | needed by | state |
|---|---|---|---|
| `shibajee-linux-rtl8196e` | `src-vendor/shibajee-linux-rtl8196e` | **`R5` (driver-diff)**, `R10a/b` | absent |
| `ggbruno-openwrt` | `src-vendor/ggbruno-openwrt` | `R10b` | absent |
| `openwrt-rtk` | `src-vendor/openwrt-rtk` | `R6`, `R10a/b` | absent |
| `utessel-edimax` | `src-vendor/edimax` | `R6` | absent |
| `vankel-rtl819x-sdk` | `src-vendor/rtl819x-sdk-3.4.9.3` | `R10a` | absent |

`ledgerscan --self-test` `P13` reads `SOURCES.json` and requires this table to
be exactly its `fetch: later` set, so a sixth tree added there cannot be
silently outside the quarantine.

⚠️ **A clone is not a reading, and this check does not pretend otherwise.** What
it establishes is narrower and still worth having: as of this commit, reading
those trees was not *possible* without a network fetch that would appear in the
shell history. It is a boundary with a date, not a proof of abstinence.

⚠️ **It stands down on a runner**, where `src-vendor/` — a symlink into
`$FWRE_WORK` — does not exist. It prints the skip rather than passing silently;
`P12`/`P12b` are the controls on that.

---

## 4. What was read, by driver

🔄 **Fifty in-scope paths** *(32 at `R5-3b-1`, twenty-seven at `R5-0`)* — 量
2026-09-06, `ledgerscan scan`, and **54 are declared**, because § 2.1's stated
direction of error is to over-report. `out-of-scope` (🔄 **75** paths, 71
before, 68 at `R5-0`) is listed by `ledgerscan scan` and is not
reproduced here: those are generic kernel files —
`init/main.c`, `kernel/bounds.c`, `arch/rlx/kernel/traps.c` — that no
peripheral driver's register map passes through.

🔴 **A note on which numbers here are stable, written because this file's own
first draft got it wrong.** A **path count** is stable: it moves only when this
repository first mentions a source it had not mentioned before, which is
exactly the event the ledger exists to catch. A **citation count** is not: it
grows every time anything is written *about* a path already declared. Between
this file's first draft and its commit, `spi_mtd` went 45 → 66 citations and
`bsp` 40 → 55 with **no new reading whatsoever** — the increase is this file,
`LOG.md` and `CHANGELOG.md` discussing them.

**So the per-domain citation counts are dropped from the tables below**, and
the path counts stay. This is the same lesson `notes/leak-surface.md` records
twice about its own three file counts: quote the split and the verdict, not the
total.

### 4.1 🔄 `R5-7` LEDs — **zero**; `R5-8` gpio-keys — one, and it is not a reading; 🔴 **`R5-4` GPIO left this section on 2026-09-06 and `R5-6` watchdog left it on 2026-09-08**

**No path in the `led` domain is cited anywhere in this repository or in
`upstream/`.**

🔴 **`wdt` left on 2026-09-08 and it did not leave the way `gpio` did.**
`R5-4` acquired one *artefact* reading by accident of what it needed;
`R5-6` read the vendor's watchdog code **on purpose and in full**, because
the step's central decision is `CONFIG_RTL_WTDOG=n` and nobody can decide
to remove code they have not read. § 4.10 is the whole list, and the
consequence for `D3` is stated there rather than left to be inferred.

🔴 **This read `gpio`, `wdt` or `led` until 2026-09-06, and the
sentence is corrected rather than deleted because its date was the whole
value of it.** `R5-4` ran that day and § 4.9 is what replaced it:
eleven framework paths — `gpio_chip` cannot be written without knowing what
a `gpio_chip` is — plus **one `artefact` reading of the VENDOR's**
`drivers/char/rtl_gpio.c`, which is the expensive one because it carries
register addresses and bit numbers. 🟢 **`led` is untouched and still
zero**, and neither `R5-4` nor `R5-6` spent anything of any THIRD-PARTY
port: `ggbruno/openwrt` is still not fetched, and no other RTL8196E
watchdog implementation has been opened. *(This said "`wdt` and `led` are
untouched and still zero" and it was true for two days.)*

🔴 **`keys` has exactly one, and it is this ledger's first
`origin: none` row — a citation that is not a reading at all:**

| path | depth | origin | what was taken |
|---|---|---|---|
| `drivers/input/keyboard/gpio_keys.c` | name | **none — an example** | `tools/ci-expected.tsv:232`, inside this ledger's own instrument row, describing the classification bug where *keyboard* contains *board*. **Nothing was read.** The file is mainline Linux and has never been opened here |

⚠️ **This is the mechanism working, on its first day, and it is written up
rather than tidied away.** The scanner cannot tell a citation from an example.
The cheap fix — rewrite that sentence so no path appears in it — makes a
checker green by editing prose, which is the failure this repository has
recorded under other names. The ledger declares the citation instead.

🔴 **`origin: none` is an exemption and exemptions get abused, so it
carries a constraint:** such a row must name the exact file and line, and that
location must itself be about tooling or classification rather than about the
device. A reader can check both. If `origin: none` ever outnumbers the real
rows in a domain, the category has stopped being an exemption and become a
habit.

What this project knows about them came from two places that are not anyone's
driver:

* the datasheet — `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf`, `讀`;
* this die — `BRD-05` (the reset button is a GPIO on `PABCD` bit 5, active low,
  **not** `RESET#`) and `REG-12` (`WDTCNR` at `0xB800311C`, reset value
  `A5000000`) are both `量`, read through `probe`/`DW` at the loader prompt.

🟢 **`R5-7` and `R5-8` are the drivers whose blind-write claim is
strongest**, and the claim is *"no implementation of these peripherals, by
anyone, has been read"*. 🔴 **`R5-6` no longer belongs in that sentence**,
and its narrower claim is *"no THIRD-PARTY implementation has been read"* —
which is still worth something and is not the same thing.

🔴 *(This read "These four" from `aa89317`, where it was correct because this
section covered four drivers, and it was still reading it after `48a7a2a` moved
`R5-4` out of the section on 2026-09-06: the header was rewritten and the count
beside it was not. It is replaced by the names rather than simply deleted the
way `docs/FINDINGS.md:375`'s "These four" was, because unlike that one this
count is load-bearing -- read as four it awards the STRONGEST independence
claim to the one driver in the group that has a vendor `artefact` reading
carrying register addresses and bit numbers, and § 8's table in this same file
says the opposite: `gpio` is 🟡 "no longer blind of the vendor's". So the two
halves of one file disagreed, and the section was the stale half. Found
2026-09-07 by `git log -S`, not by re-reading. § 8 owns which domains are in
which state; this line names the drivers and states no count.)*

⚠️ Bounded by § 0 ① and by § 4.2: a board file initialises GPIOs, and
`boards/rtl8196e/bsp/setup.c` **has** been read.

### 4.2 🔴 `bsp` — 11 paths — cross-domain, and the one that bounds § 4.1

| path | depth | origin | what was taken |
|---|---|---|---|
| `boards/rtl8196e/bsp/setup.c` | line | vendor | 🔴 **the deepest reading in this ledger.** `notes/kernel-build.md` § 11.2 quotes `bsp_setup()` at `:134-175` verbatim: `bsp_serial_init()`, `_imem_dmem_init()`, `ret = bsp_swcore_init(version)`, `if (ret != 0) bsp_machine_halt();` and that `bsp_machine_halt` is a bare `while(1)`. Also `:32` (`prom_putchar`, `static`, no caller in the file). **Per § 2.1 the whole 134-175 range counts as read**, and whether it contains a GPIO or timer init is not recorded |
| `arch/rlx/bsp/bspcpu.h` | line | vendor | `:12-22`, the BSP clock/base constants |
| `boards/rtl8196e/bsp/bspcpu.h` | name | vendor | the board's copy of the same header |
| `arch/rlx/bsp/setup.c` | line | vendor | `:34`, `UART0_BASE`; and that a string is printed from this file before the console exists |
| `arch/rlx/bsp/vmlinux.lds` | name | vendor | the link script — where `R3`'s `start address: 0x80003600` comes from |
| `arch/rlx/kernel/setup.c` | line | vendor | the anchors for marks `B01`/`B02`/`B03`/`B08` (`config/rlxfw-marks.tsv`), and `:546` (`setup_early_printk`) |
| `boards/rtl8196e/bsp/prom.c` | line | vendor | `bsp_init()` computes `mem_size` by reading the DRAM configuration register at `BSP_MC_MTCR0` — bank/bus-width/row/column decode |
| `arch/rlx/bsp/prom.c` | name | vendor | the same file through the `arch/rlx/bsp` symlink |
| `arch/rlx/bsp/timer.c` | 🔴 **line** | 🔴 **vendor** | 🆕 **2026-09-04, `R5-10`, and it is the deepest timer reading in this ledger.** `bsp_timer_init()` **in full**: `REG32(BSP_TCCNR)=0` before touching `CDBR`; `REG32(BSP_CDBR)=(BSP_DIVISOR)<<BSP_DIVF_OFFSET`; the **runtime** `(REG32(BSP_REVR) & 0xFFFFF000)==BSP_RTL8196E` branch selecting `<<4` over `<<BSP_TCD_OFFSET`; `rlx_clockevent_init(BSP_TC0_IRQ)`; and the two closing **assignments** `REG32(BSP_TCCNR)=BSP_TC0EN\|BSP_TC0MODE_TIMER` and `REG32(BSP_TCIR)=BSP_TC0IE`. Also `bsp_timer_ack()` and the `CONFIG_RTL_TIMER_ADJUSTMENT` block's `rtl865x_setupTimer1()`, which writes `TC1DATA`/`TCCNR`/`TCIR` for TC1. 🔴 **2026-09-04, seating 12: `bsp_timer_ack()` was recorded here as a write and its CONSEQUENCE was not drawn, and the consequence is the finding.** It is `REG32(BSP_TCIR) \|= BSP_TC0IP;` — a read-modify-write on a register whose `IP` bits are write-1-to-clear — called on every 100 Hz tick, so it clears **every** pending bit in `TCIR`, including one belonging to a driver it has never heard of. `TI-3` read `TC1IP = 0` after sixteen full TC1 periods because of it. 量: the reading was in this ledger one segment before the cell it explains ran, and no sentence anywhere in the tree had connected them. **A ledger row that records a write without its effect is a reading that has been banked and not spent.** `SPEC.md` `IRQ-09`, `docs/interrupt-map.md` § 3.6. ⚠️ **`R5-1`'s driver source predates this reading by one day** (`config/rlxfw-src/…/rtl819x-timer.c`, 2026-09-03; this, 2026-09-04), so the blind-write claim for the *timer driver as written* survives — **but `driver-diff`'s timer section may not be written as blind from here on**, and § 4.3's contamination sentence is bounded by this row rather than by itself |
| `arch/rlx/bsp/irq.c` | 🔴 **line** | 🔴 **vendor** | 🆕 **2026-09-04, `R5-10`, in full.** `bsp_irq_init()` (`GIMR=0`, the three domain inits, `:222-225` writing all four `IRR` registers from `BSP_IRR*_SETTING`); `bsp_ictl_irq_mask`/`unmask` (`GIMR &= ~(1<<(irq-16))` / `\|=`); `bsp_ictl_irq_init` (`set_irq_chip_and_handler` over 32 lines, `setup_irq(BSP_ICTL_IRQ)`); `bsp_ictl_irq_dispatch` (`pending = GIMR & GISR`, the UART0/UART1/**TC1** chain, and the `else` that masks what it cannot name); `bsp_irq_dispatch` (`read_c0_cause() & read_c0_status()`, `CAUSEF_IP2` first). 🔴 **Decision layer, not fact layer** — it is where the routing policy lives |
| `arch/rlx/bsp/bspchip.h` | 🔴 **line** | 🔴 **vendor** | 🆕 **2026-09-04, `R5-10`.** The whole interrupt and timer block: the three IRQ bases and counts, the `Source/EXT_INT/CPU INT/LOPI/IRQ` comment table, every `BSP_*_IRQ`, every `BSP_*_RS`, `BSP_DIVISOR 1000`, `BSP_DIVF_OFFSET 16`, `BSP_TCD_OFFSET 8`, `BSP_SYS_CLK_RATE`, `BSP_REVR`/`BSP_RTL8196E`, the full `GIMR`/`GISR` bit lists, the four `BSP_IRR*_SETTING` macros, and the `TCCNR`/`TCIR` bit names. 🟢 **It is a second source for D Tables 24 and 25** (`REG-09`, `REG-10`) and for the divisor (`REG-11`) — three findings that stood on the leaked draft alone until today |

🔴 **This is the block that keeps § 4.1 from being an unqualified claim.** None
of the eight is a peripheral driver, and none of the extracts records a GPIO,
timer, LED or watchdog register.

> 🔴 **CORRECTED 2026-09-04: the second half of that sentence is now false, and
> it was made false by this segment rather than found wrong.** `arch/rlx/bsp/timer.c`
> is a full reading of the vendor's **timer** initialisation, register by
> register, and `arch/rlx/bsp/irq.c` is a full reading of its **interrupt**
> routing policy. The sentence is kept because it was true of the eight rows it
> was written about; what replaces it is narrower and dated: **of the eleven,
> none records a GPIO, LED or watchdog register, and two record timer and
> interrupt ones.**
>
> 🔴 **CORRECTED AGAIN 2026-09-08, and the watchdog half is now false too —
> made false by `R5-6` rather than found wrong.** `boards/rtl8196e/bsp/timer.c`
> is the same file as `arch/rlx/bsp/timer.c` under its other name (`target` is
> a symlink to `boards/rtl8196e`, the same pair as `prom.c` two rows up), and
> the range read on 2026-09-04 stopped short of its `CONFIG_RTL_WTDOG` block.
> That block is now read: `REG32(BSP_WDTCNR) = 0x00600000`. **Of the eleven,
> none records a GPIO or LED register; two record timer and interrupt ones;
> and one records a watchdog one.** § 4.10.
>
> `R5-4` and `R5-7` are unaffected; `R5-6` is not; `R5-1` is
> unaffected as written (its source predates the reading by a day) and
> `driver-diff`'s timer and interrupt sections are not. But `bsp_setup()` is where a board brings its
peripherals up, and 42 of its lines are inside a range this ledger counts as
read.

**Verdict:** the four drivers in § 4.1 are written blind *of any driver*, with a
recorded exposure to the board file that would initialise them. `driver-diff`
carries that sentence rather than omitting it.

### 4.3 🟢 `R5-1` timer — 9 rows, 8 of them in the scan's `timer` domain, and the contamination is nil where it matters

🔄 **2026-09-03, `R5-1`: five paths added, and they were added because
`ledgerscan check` went RED and named them.** That is the join in § 2 doing
the only job it has: the driver was written, `check` was run, and it refused
to stay green until this section said what had been taken. Four are generic
Linux — the clocksource subsystem's interface and core, and the two files
that decide how long this kernel thinks a jiffy is. 🔴 **The fifth is the
vendor's**, `arch/rlx/include/asm/timex.h`, and it is one constant that
describes a PC rather than this SoC.

⚠️ **One of the nine rows below is declared here and is NOT in scope.**
量: `ledgerscan scan --domain timer` counts **8**, and
`include/linux/jiffies.h` is not one of them — the domain rules put it
out-of-scope. It is declared anyway. That is § 2.1's direction of error on
purpose: this file **over-reports** contact, because its job is to constrain
a later claim, and a path the scan would not have asked for is exactly the
kind that a reader should be able to see rather than take on trust.

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/rlx/kernel/rlx-cevt.c` | **line** (unchanged as a WORD — § 4.8.1) | vendor | 🆕 **2026-09-06 (`R5-3b-1`): OPENED IN FULL, 244 lines, and everything in `rtl819x-timer` 3.0 was written after it.** What was taken is stated so a reader of `docs/driver-diff.md` can discount it: **the rating `100`** (`:234`) and **`.features = CLOCK_EVT_FEAT_PERIODIC` alone** (`:140`) — both facts about what this driver must *coexist with*, not about how to drive TC1 — plus `set_mode`/`set_next_event` being empty stubs (`:122`–`:132`), which is what makes the exchange safe, and the watchdog pet at `:159`. 🟢 **What was NOT taken, and could not be**: the vendor's clockevent programs **no timer register at all**. There is no reload sequence in it to copy. The register writes are in `arch/rlx/bsp/timer.c` (§ 4.2, read 2026-09-04) and this driver does not repeat them. ⚠️ **The blind claim for the TIMER now has three dates and they are not the same claim**: version 1.0 (2026-09-03) was written with this file cited at two string literals only; version 2.0 (2026-09-04) after `bsp/timer.c` and `rlx-time.c`; version 3.0 (2026-09-06) after this one. `git log` can check each, and this comment cannot. ⟶ 🟢 **the string literal `"rlx timer"` and the two lines it is on (`:139,226`) — nothing else.** The context is `notes/vendor-kernel-isa.md`'s proof that *this unit runs `arch/rlx` and not `arch/mips`*, which needed three literals unique to files that exist only under `arch/rlx`. **No register, no sequence, no divisor, no interrupt number** |
| `kernel/sched_clock.c` | line | **generic** | `:39`, the weak generic `(jiffies - INITIAL_JIFFIES) * (NSEC_PER_SEC / HZ)`, read to establish that `arch/rlx` defines no `sched_clock` (zero hits) and that `printk_time` therefore has 10 ms resolution. **Generic Linux — every port in existence uses this file** |
| `include/linux/clocksource.h` | 🔄 **line** (was **name**) | **generic** | 🆕 2026-09-03, `R5-1`: the `struct clocksource` field list, `clocksource_hz2mult()`, `CLOCKSOURCE_MASK()`, the `read(struct clocksource *)` signature, and the rating band comment (*1–99 unfit for real use*). **The subsystem's interface**, which a clocksource for any part must be written against. It says nothing about this SoC. 🆕 **2026-09-04, `R5-3a`: a second and deeper visit, and the depth moved with it.** `clocksource_hz2mult()` `:253-266` **in full** — the `u64 tmp` and the `(u32)` cast that truncates without a diagnostic — and `cyc2ns()` `:317-322`, `((u64)cycles * cs->mult) >> cs->shift` returned as `s64`. Those two bodies are where `CLK-24`'s two overflow bounds come from. 🔴 **And the ABSENCE of `clocks_calc_mult_shift()` from this file is itself the finding**: the driver has to search for its own shift because a kernel of this vintage has no helper for it |
| `include/linux/jiffies.h` | 🔄 **line** (was **name**) | **generic** | 🆕 2026-09-03, `R5-1`: `LATCH`, `ACTHZ`, `SH_DIV`, `NSEC_PER_JIFFY` and `TICK_NSEC` — read to check, rather than assume, that this build treats one jiffy as exactly 10,000,000 ns. It does, and the check is `notes/timer-driver.md` § 5.1.1. **Generic Linux**. 🔴 **2026-09-04, `R5-3a`: the depth was wrong and `ledgerscan check` found it on the first run it could.** `LOG.md:14391` cites this file as `:43,54,58` — three line numbers — and the extract above names five macros, which is a reading of the code and not of a name. **The row was written by hand and no checker compared it to anything until `LEDGER-2` shipped**; that is the whole content of that carried-forward row, arriving as its own first result |
| `kernel/time/jiffies.c` | 🔄 **line** | **generic** | 🆕 2026-09-03, `R5-1`: `clocksource_jiffies`'s **rating 1** and its `mult`/`shift`, which is the number `L2-e`'s choice of rating 0 is measured against. **Generic Linux.** 🔄 **Depth corrected 2026-09-03 (`R5-2`), and by the scan rather than by a re-read**: this row said `name`, and `ledgerscan scan --domain timer` reports **`line`** because `notes/timer-driver.md:273` cites `kernel/time/jiffies.c:37`. ⚠️ **`ledgerscan check` did not and cannot catch that** — it compares the set of cited paths against the set of declared paths and never looks at the depth column, so a row can be under-declared in depth and stay green. § 7 ⑧ |
| `arch/rlx/include/asm/timex.h` | line | 🔴 **vendor** | 🆕 2026-09-03, `R5-1`: `:21`, one constant — `CLOCK_TICK_RATE = 1193182`. 🟢 **It is the i8253 PIT frequency of an IBM PC and describes no part of this SoC**, so what it costs on the decision layer is nil; what it bought is § 5.1.1's table, which says the jiffy length is exact at `HZ=100` and off by tens of ppm at every other `HZ` this port offers. **No register, no sequence, no divisor, no interrupt number** |
| `kernel/time/timekeeping.c` | name | 🟡 **none — a correction** | 🆕 2026-09-03, and it is this ledger's **second** `origin: none` row. `notes/timer-driver.md:41` names this file *inside a note saying it was never opened*: a draft sentence cited it from memory as the place `(now - cycle_last) & mask` is performed, `ledgerscan check` went RED, and the sentence was rewritten to cite `include/linux/clocksource.h`'s `@mask` documentation — which is what was actually read. **Nothing was taken from this file.** The location is about the instrument, not about the device, which is the constraint § 4.1 puts on this category |
| `kernel/time/clocksource.c` | name | **generic** | 🆕 2026-09-03, `R5-1`: `clocksource_enqueue()`, `select_clocksource()`, `clocksource_register()`, `clocksource_unregister()` — read to settle **one decision**, `L2-e`: whether a rating below `clocksource_jiffies`' 1 keeps a source out of the selection, and which way a tie breaks. Generic Linux, identical in every 2.6.30 tree. 🔴 **It touches the decision layer even so**, because a second implementation's rating choice would be reading the same code; `notes/timer-driver.md` `L2-e` cites it by name rather than presenting that choice as arrived at alone |

🔴 **And a file that is NOT cited, listed here because its absence from the
scan is the ledger's claim and a reader should be able to see what was
absent:**

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/rlx/kernel/rlx-time.c` | 🔴 **line** (was **none — nothing taken**) | vendor | 🆕 **2026-09-04, `R5-10`: opened, in full, and it is not what this ledger and `CORRECTIONS-block8.md` § 9 ④ took it for.** 111 lines, MontaVista-derived; `time_init()` is three lines and calls `bsp_timer_init()`, so **the register writes are in `arch/rlx/bsp/timer.c`** (§ 4.2). Also `clockevent_set_clock()`'s shift search, `update_persistent_clock`, and 🟢 **that `clocksource_set_clock()` in this file sits inside an `#if 0`** — which **partly answers this section's own closing question**: the vendor's clocksource half is *not* here. Whether `rlx-cevt.c` has one is still unknown; that file is still cited at two string literals only. ~~**Nothing.**~~ It exists (量 2026-09-02, directory listing, no file opened). 🔴 It is listed because § 1's first account of the grep was that this file did not exist; it does. `ledgerscan` cannot report a file nobody has mentioned, so this row is written by hand and is exactly the § 0 ① limit made visible. 🔄 **2026-09-03 (`R5-2`): the depth used to read *"zero citations"*, and that is now false as a count and was always the wrong measurement.** `ledgerscan scan --domain timer` reports **6 citations across 4 files** — this row, the driver's own comments, `notes/timer-driver.md` and the `R5-2` card — every one of which is *this project saying it did not open the file*. **The claim is that nothing was TAKEN, and a mention is not a taking**; the count was never the evidence and citing it invited exactly the confusion it now causes. 🟢 **2026-09-03, seating 11: a fact about what this file DOES was obtained, and the file is still unopened — which is the distinction this ledger exists to make legible, arriving in the direction that supports the claim rather than weakening it.** 量, `TM-1`, reading the timer block's registers under Linux for the first time: `CDBR` is `03E80000` (divisor **1000**) where the loader left `000E0000` (divisor 14), and `TC0DATA` is `00007D00` (reload **2,000**) where the loader left `0022E0A0` (142,858) — both give exactly 100 Hz. `cdbr_at_init`/`tc0data_at_init` already hold the Linux values, so the reprogramming precedes `rtl819x_timer_init` and belongs to this file. ~~**The depth stays `none`**: nothing was read out of the source, the finding is a device reading, and it entered no design decision~~ — the driver was written, built, linked and pinned into `rlxfw-r51-20260903.bin` before the board was powered. **Recorded here because a reader who later sees this project describe `rlx-time.c`'s behaviour is entitled to know which route the description came from.** 🔴 **2026-09-04 (`R5-3a`): that struck sentence expired one segment ago and nothing caught it.** `R5-10` opened this file in full on 2026-09-04 and the depth cell above says `line`; the paragraph still said `none`, so **this row contradicted itself for one segment**. The half that survives is the dated one: the depth was `none` **when `rlxfw-r51-20260903.bin` was built**, which is what bounds the blind-write claim for *that* image and for nothing later. ⚠️ `ledgerscan check` did **not** find this — it compares the cell against the scan, and the cell was already right. **What found it was reading the row's prose against its own first column**, which is the same shape as `docs/interrupt-map.md` § 0 saying *five gates* over a table of seven: no checker in this repository compares a document's prose to its own table |

⚠️ `arch/rlx/kernel/rlx-csrc.c` — the *clocksource* half, guessed from
`cevt` — **does not exist** in the built drop. So whatever the vendor does for
a clocksource is in one of the two files above, and which one is **unknown
here**: finding out means opening one, which is what `R5-1` is written without.

🟢 **The numbers `R5-1` will be built on are `量` on this die and owe nothing to
anyone's driver:**

* `CLK-17` — `TC0CNT` increments at **14,286,057 Hz**, period 69.9983 ns —
  derived from **two measured quantities only**: `CLK-04`'s 100.0018 Hz tick ×
  `REG-05`'s `TC0DATA = 142,858`. **It needs no `CDBR`, no divisor semantics
  and no 200 MHz figure.**
* `REG-11` — `CDBR` at `0xB8003118` reads `0x000E0000`; the **value** is `量`,
  only the **name** is `讀`.
* `CPU-42` — CP0 `Count`/`Compare` are not implemented on this die, `量`.

🔴 **And the one thing that is not measured is exactly the thing a diff would be
worth having on.** `CLK-06` — *the divisor field's semantics*, i.e. whether
`0x000E` means divide-by-14 or divide-by-15 — is marked **推** in `SPEC.md`: an
inference from *"15 would give 213.7 MHz, and nobody clocks a part at that"*.
That is a decision, it is unresolved, and it is a register-semantics question a
second implementation can disagree with me about. **It is `driver-diff`'s best
row and it exists because the timer was not read.**

> 🔴 **2026-09-03, `R5-1`: the paragraph above is wrong, and it is kept
> because being wrong in a stated way is what this file is for.** `CLK-06`
> is **not** unresolved. D § 8.2.8 Table 26 states it: *"Assume
> DivFactor=N, Base clock = System_clock (Peripheral Lexra Bus)/N"* — the
> field holds `N` — and *"Both values 0x0000 and 0x0001 disable the clock"*
> excludes the `N−1` reading, under which `0x0000` would mean divide-by-one
> rather than *disable*.
>
> **No new source was read to find that.** `SPEC.md` `CLK-02` has cited that
> exact sentence since 2026-08-26, and used it only to answer a *naming*
> question — which end of the divider the words *base clock* mean. It never
> travelled to the row that depends on it. Same shape as `CPU-27`: one fact,
> one owner, and it never reached the second file.
>
> **What it costs this document.** `CLK-06` moves from **L2 decision** to
> **L1 fact** (§ 5), and L1 agreement between implementations is guaranteed
> by the parts being the same part — so *the diff's best row* is not this
> one. `SPEC.md` `CLK-06`'s name mark moves 推 → 讀 with the 213.7 MHz
> derivation kept as its second source.
>
> 🟢 **L2 is not left empty, and the replacement rows are named rather than
> asserted**: `notes/timer-driver.md` § 3 carries ten, of which the ones a
> second implementation can genuinely differ on are the wrap handling for a
> non-power-of-two modulus (`L2-b`), `mult`/`shift` (`L2-d`), rating and
> coexistence (`L2-e`), when the hardware is written at all (`L2-f`), and
> which registers are written (`L2-g`). **This correction makes `D3` harder
> to pass, not easier** — which is the same test § 5 applies to itself.

#### 4.3.1 🔴 **2026-09-03, `R5-2`'s card: a reading of the vendor's code that is not a reading of a source file, and this ledger had no shape for it**

量, on `vmlinux` sha256-16 `2b0d1618d9946cc6` — **my own build**, the one
`rlxfw-r51-20260903.bin` was cut from — plus its `System.map` and its `.config`.
No vendor binary was executed and no vendor source file was opened. What was
counted: direct `jal`/`j` transfers to `clocksource_register`, and `lui`/`addiu`
and `lui`/`ori` pairs materialising its address. Result: **exactly two
clocksources are registered in the image — `clocksource_jiffies` and mine — and
the vendor registers none.** `notes/timer-driver.md` § 6.4 carries the controls.

| path | depth | origin | what was taken |
|---|---|---|---|
| *(no source path)* — the vendor's `arch/rlx` **object code**, as linked into my own `vmlinux` | **artefact** | 🔴 **vendor, by absence** | 🆕 2026-09-03, `R5-2`: **one bit of information — that no code under `arch/rlx` calls `clocksource_register`.** No register, no sequence, no divisor, no interrupt number, no file opened. It is an *absence*, and it was obtained by counting instruction encodings in a binary I produced |

🔴 **Why it is declared even though `ledgerscan` cannot see it.** The scan reads
prose for path citations; this reading cites no path, so it is invisible to the
tool by construction — the § 0 ① limit, in a new shape. Declaring it is § 2.1's
direction of error on purpose: this file **over-reports** contact.

🟢 **What keeps it off the decision layer, and it is an order rather than an
argument.** `R5-1`'s driver was written, compiled, linked and pinned into the
staged image on 2026-09-03 **before** this scan ran. A reading taken after the
artefact is frozen cannot have shaped it, and the artefact's sha256 is the
witness. **That protection does not extend to `R5-3`**, which is not yet
written: from here on, *the vendor registers no clocksource* is something this
project knows, and a coexistence decision in `R5-3` that leans on it is leaning
on the vendor's code. `R5-3`'s rating decision must say so in place.

⚠️ **The general rule this row adds, because a second instance is likely.**
A *binary* of mine that contains the vendor's compiled code is a source of
findings about the vendor, and the three earlier categories in this file —
`line`, `name`, `none` — all assume a file was opened. **`artefact` is the fourth
depth**, and its test is the same as the others': what was taken, and could it
have shaped a decision. It is not a loophole; a disassembly of the vendor's
timer routine would be a `line` reading whatever file it was printed from.

### 4.4 🟡 `R5-10` interrupt map — 4 paths in this section, and three more in § 4.2

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/rlx/kernel/irq_vec.c` | line | vendor | `:36`, the string literal `"RLX LOPI"` — the same `arch/rlx`-vs-`arch/mips` proof as § 4.3. ~~**No routing, no mask register**~~ 🔴 **2026-09-04, `R5-10`: that clause is now false and the file is read in full.** `unmask_rlx_vec_irq`/`mask_rlx_vec_irq` (`set_lxc0_estatus(0x10000 << (irq - BSP_IRQ_LOPI_BASE))`), the `rlx_vec_irq_controller` chip, `rlx_vec_irq_init` (`clear_lxc0_estatus(EST0_IM)`, `write_lxc0_intvec(&rlx_vec_dispatch)`, and the **assignment** `REG32(BSP_GIMR) = BSP_TC0_IE \| BSP_UART0_IE` with every conditional `\|=` after it), and `rlx_do_lopi_IRQ`. **Mask register and dispatch both** |
| `arch/rlx/kernel/irq_cpu.c` | line | vendor | 🆕 **2026-09-04, `R5-10`.** `:44,51` — `set_c0_status(0x100 << (irq - BSP_IRQ_CPU_BASE))` / `clear_c0_status(...)`, the `rlx_cpu_irq_controller` chip, and `:69,73` (`clear_c0_status(ST0_IM)`, `set_irq_chip_and_handler`). **This is what says the CPU domain is masked in the ORDINARY `Status.IM` while LOPI is masked in `ESTATUS`** |
| `arch/rlx/include/asm/mach-generic/irq.h` | line | **generic** | 🆕 **2026-09-04, `R5-10`.** `NR_IRQS 48` and the `MIPS_CPU_IRQ_BASE` block. Generic Linux, unmodified upstream text |
| `arch/rlx/include/asm/rlxregs.h` | line | 🔴 **vendor** | 🆕 **2026-09-04, `R5-10`. Declared although `ledgerscan check` did not ask for it**, on § 2.1's direction of error — the scan's domain rules put it out of scope and over-reporting contact is this file's job. `LXCP0_ESTATUS $0` / `ECAUSE $1` / `INTVEC $2` / **`CCTL $20`**, the `CCTL_*` operation bits, `EST0_IM 0x00ff0000`, the `ESTATUSF_IP*`/`ECAUSEF_IP*` lists, and the `__read_32bit_lxc0_register`/`__write_32bit_lxc0_register` macros that emit `mflxc0`/`mtlxc0` |
| `bootcode/boot/init/irq.c` | line | **loader** | `:228` and around it. This is the **bootloader's** interrupt code, not Linux's; read for `docs/loader-command-semantics.md` and `notes/cache-model.md` |

⚠️ `R5-10` ships `docs/interrupt-map.md`, **not** an irqchip driver — three
stated reasons in `PROGRESS.md`. A map is a description of hardware, so its
independence matters less than a driver's; this block is recorded for `R6`,
which will write the driver.

### 4.7 🟢 `R5-3a` interrupt path — 6 paths, **all six generic Linux**, and that is the point

`R5-3a` writes an interrupt handler and the four `/proc` verbs that gate it. The
question `driver-diff` will ask is whether that design came from anyone else's
RTL8196E driver. **It did not, and this table is why: every file opened for it
is generic kernel infrastructure, not a Realtek peripheral driver.** The three
vendor files this step leans on — `arch/rlx/bsp/irq.c`, `bspchip.h`,
`arch/rlx/include/asm/rlxregs.h` — were read on 2026-09-04 by `R5-10` and are
declared in § 4.2 and § 4.4; nothing new of the vendor's was opened today.

| path | depth | origin | what was taken |
|---|---|---|---|
| `kernel/irq/chip.c` | line | **generic** | 🆕 **2026-09-04, `R5-3a`, and it is the file the handler's whole safety argument rests on.** `mask_ack_irq()` at `:291-300` — `desc->chip->mask_ack` if present, else `mask()` then `ack()` — and `handle_level_irq()`'s body: `mask_ack_irq` first, then `handle_IRQ_event`, then `if (!(desc->status & IRQ_DISABLED) && desc->chip->unmask) desc->chip->unmask(irq)`. **That closing condition is what makes `disable_irq_nosync()` a working storm guard rather than a hope.** Generic Linux, unmodified |
| `kernel/irq/manage.c` | line | **generic** | 🆕 **2026-09-04, `R5-3a`.** `__setup_irq`'s `if (!(desc->status & IRQ_NOAUTOEN)) { desc->depth = 0; desc->status &= ~IRQ_DISABLED; desc->chip->startup(irq); }` at `:621-628` — which is why `request_irq(25, …)` sets `GIMR` bit 9 through the irqchip and this driver never writes it; `disable_irq_nosync` at `:212`, which takes `desc->lock`; and `__free_irq`'s `WARN(in_interrupt(), …)` opener and its *last handler → IRQ_DISABLED + shutdown* branch. Generic Linux |
| `kernel/irq/spurious.c` | line | **generic** | 🆕 **2026-09-04, `R5-3a`.** `note_interrupt()` at `:252,256`: `desc->irq_count < 100000` and `desc->irqs_unhandled > 99900`. Read to say what an `IRQ_NONE` return actually costs, and the answer went into a comment as *the backstop, not the guard* — 100,000 interrupts is not a bound this project would rely on. Generic Linux |
| `include/linux/interrupt.h` | line | **generic** | 🆕 **2026-09-04, `R5-3a`.** `IRQF_DISABLED 0x00000020` at `:53`, the `request_irq` prototypes at `:113,123`, `free_irq` at `:143`, `disable_irq_nosync` at `:181`. Generic Linux |
| `include/linux/timer.h` | name | **generic** | 🆕 **2026-09-04, `R5-3a`.** That `setup_timer`, `mod_timer` and `del_timer_sync` exist with these signatures — the extension timer `TMR-1` asked for. No body was read. Generic Linux |
| `include/linux/kernel.h` | line | **generic** | 🆕 **2026-09-04, `R5-3a`.** `BUILD_BUG_ON` at `:686`, used to make `RTL819X_TC1_IRQ < NR_IRQS` a build failure rather than a run-time surprise. Generic Linux |

🔴 **One deeper reading of `include/linux/clocksource.h`, and its row is in § 4.3.** `clocksource_hz2mult()` at `:253-266` and `cyc2ns()` at `:317-322` were read in full today, and **the absence of `clocks_calc_mult_shift()` in this tree is itself the finding** (`CLK-24`): the shift has to be searched for by the driver because the kernel of this vintage has no helper for it. That file was already declared at `line` by `R5-1`; this is a second, deeper visit to the same file and the row is not duplicated.

⚠️ **And a `name`-depth contact recorded because it would otherwise be invisible.** 量 today, deciding whether a driver may include `asm/rlxregs.h`: `grep -Rn 'asm/rlxregs.h' drivers/` returns four files under `drivers/net/wireless/`, of which `drivers/net/wireless/rtl8192cd/romeperf.c` is one. **Nothing was opened** — the grep's output is the whole of the contact, and it settled one question (a vendor driver does include that header, so doing so is not unusual). Declared at `name` because § 2.1's direction of error is to over-report.

| path | depth | origin | what was taken |
|---|---|---|---|
| `drivers/net/wireless/rtl8192cd/romeperf.c` | name | vendor | 🆕 **2026-09-04, `R5-3a`: the PATH appeared in a `grep -Rn` result and the file was not opened.** It answered one question — whether a driver in this tree includes `asm/rlxregs.h` — and nothing else. 🔴 It is a **wireless** file and `R5` writes no wireless driver, so the contamination it could cause is nil; it is here because a ledger that only records the contacts that matter is a ledger whose omissions cannot be audited |

### 4.8 🆕 `R5-3b-1` clockevent — 3 paths, two generic and one the port's own, and the checker is what found them

**`ledgerscan check` reported all three as cited-and-undeclared** on the run
that closed this segment, before any of them reached a commit. They are the
files version 3.0's design decisions are read out of.

| path | depth | origin | what was taken |
|---|---|---|---|
| `kernel/time/tick-internal.h` | **line** | **generic** | 🆕 **2026-09-10, `R5-12`, and this row exists because `ledgerscan check` refused the commit that cited it.** 6.18.50, line 63: `extern void clockevents_handle_noop(struct clock_event_device *dev);` — **that is the whole of what was taken**, and it is the file's only relevance here. 🔴 **The order was wrong and is recorded that way**: the write-up asserted "declared only in `kernel/time/tick-internal.h`, so no driver may name it" from a *negative* grep of `include/linux/clockchips.h`, i.e. from where it is NOT, and the gate is what made it be read. The claim survived reading (`grep -rn` over `include/` returns nothing; that line is the sole declaration), so what the gate caught is a **citation without a reading**, not a wrong statement. ⚠️ **Scope: `kernel/`, not `arch/`, and mainline, not the vendor tree** — it bears on `rtl819x-timer`'s port only, where it is why `.event_handler = clockevents_handle_noop` had to be dropped from the initialiser (`notes/modern-kernel-port.md` § 9.5 ②). It bears on **nothing** that has run on the silicon. |
| `kernel/time/tick-common.c` | **line** | **generic** | 🆕 **2026-09-06, `R5-3b-1`, and it decides the whole step.** `tick_check_new_device()`: `if ((curdev->features & CLOCK_EVT_FEAT_ONESHOT) && !(newdev->features & CLOCK_EVT_FEAT_ONESHOT)) goto out_bc;` then `if (curdev->rating >= newdev->rating) goto out_bc;` — **so the vendor's 100 must be beaten strictly, and the oneshot test only blocks, never promotes.** `tick_setup_device()`: `td->evtdev->event_handler = clockevents_handle_noop;` on the OLD device — which is why the vendor's TC0 interrupt keeps arriving and stops advancing `jiffies`. `tick_setup_periodic()`: `CLOCK_EVT_FEAT_PERIODIC` → `clockevents_set_mode(dev, CLOCK_EVT_MODE_PERIODIC)`, and the `else` branch's `for (;;)` around `clockevents_program_event()` — which is why `set_next_event` returns 0 rather than an error. `tick_periodic()`: `do_timer(1)` and `update_process_times(user_mode(get_irq_regs()))`. Generic Linux, unmodified |
| `kernel/time/clockevents.c` | **line** | **generic** | 🆕 **2026-09-06, `R5-3b-1`.** `clockevents_register_device()` — its two `BUG_ON`s, which 量 compile to nothing here because `CONFIG_BUG` is not set, so this driver's own `-EBUSY` is the only thing between a second `cevt` and a corrupted list. `clockevents_exchange_device()` — `set_mode(old, UNUSED)` then `clockevents_shutdown(new)`, which is why `set_mode` is called SHUTDOWN-then-PERIODIC and why SHUTDOWN must not stop the counter. `clockevents_set_mode()`'s `if (dev->mode != mode)` guard. `clockevents_handle_noop`, used by name as this driver's initial `event_handler`. Generic Linux |
| `arch/rlx/include/asm/irq_regs.h` | **line** | vendor | 🆕 **2026-09-06, `R5-3b-1`, 21 lines, and what it settled is a NON-question.** `#define ARCH_HAS_OWN_IRQ_REGS` and `get_irq_regs()` returning `current_thread_info()->regs`. Opened because `set_irq_regs()` is called nowhere in `arch/rlx` and `tick_periodic()` dereferences `get_irq_regs()` on every tick — so the alarm was that the handover would oops. **Nothing was taken into the driver**: it holds no register, no sequence and no number, and the file's whole content is the classic MIPS route that `arch/rlx/kernel/genex.S:84-85` fills. Declared at `full` because it was read in full, and § 2.1's direction of error is to over-report |

#### 4.8.1 🔴 The depth vocabulary cannot say what changed about `rlx-cevt.c`, and that is a hole in `LEDGER-2`'s fix

讀 `tools/ledgerscan.py:364`: `DEPTHS = ("none", "name", "line")`, deepest last.
There is no word for *the whole file*.

So this segment's reading of `arch/rlx/kernel/rlx-cevt.c` — from **two string
literals** (`:139`, `:226`, taken for an `arch/rlx`-vs-`arch/mips` proof) to
**all 244 lines** — leaves the machine-readable cell reading `line` before and
`line` after. 🔴 **`ledgerscan check` cannot see the largest single change this
ledger has recorded for that file.** The prose says it; nothing checks the
prose.

⚠️ **And the first draft of § 4.8 wrote `full` in all three new rows.** The
checker reported them, which is `LEDGER-2`'s fix working — but it reported them
as *unrecognised*, not as *wrong*, and an unrecognised depth is skipped rather
than failed. A row that declared `ful1` would be skipped the same way.
**`LEDGER-3` is that pair of gaps**, and it is carried forward rather than
fixed here: adding a fourth depth word moves `scan`'s own computation
(`ledgerscan.py:505` derives `line` or `name` from whether a citation carries a
line number, and nothing can derive *whole file* from a citation), so it is a
design change to the tool and not a table edit.

⚠️ **`arch/rlx/kernel/genex.S` is cited beside it and is NOT declared**, because
the citation is to two lines quoted out of `ledgerscan`'s own report of
`TI_REGS` stores rather than to a reading of the file — no instruction sequence
was followed and no register meaning taken. **If a later step opens it, the row
belongs in § 4.2.**

### 4.9 🆕 `R5-4` GPIO — 11 paths **+ 1 `artefact`**, and the artefact is the expensive one

🔴 **This section is why § 4.1's "zero" and § 8's `gpio` row moved, and the
move happened in one segment.** Before 2026-09-06 the `gpio` domain was the
cleanest blind-write claim in the gate: no third-party RTL8196E GPIO driver
cloned, opened or read, and `ggbruno/openwrt` — the port whose author claims
gpio works — not even fetched. **That part is unchanged.** What changed is that
writing a `gpio_chip` at all required reading the framework, and that answering
one safety question required reading the vendor's own GPIO driver *as compiled
code*.

**The source of `rtl819x-gpio.c` predates every row below** — `git log` on
`config/rlxfw-src/linux-2.6.30/drivers/gpio/rtl819x-gpio.c` against this
file's commit is the check, and it is the same argument § 4.3 makes for the
timer's version 1.0. Anything added to that driver from here on is **not**
blind, and `docs/driver-diff.md`'s gpio section must say so rather than
inherit the word.

#### The framework, which cannot be avoided

A `gpio_chip` cannot be written without knowing what a `gpio_chip` is. Every
one of these is mainline Linux and none of them says which register drives
which pin on this die, which is the layer `driver-diff` compares.

| path | depth | origin | what was taken |
|---|---|---|---|
| `include/asm-generic/gpio.h` | **line** | **generic** | `struct gpio_chip`'s member list — and one member decided the driver's shape: `.set` returns **void**, so a refusal inside it cannot reach the caller as an errno. Also `gpiochip_add()`'s prototype and `ARCH_NR_GPIOS = 256` |
| `drivers/gpio/gpiolib.c` | **line** | **generic** | which ops the framework dispatches to, which is what makes `.request` the right place for the policy: `:804` `gpio_request()` calls `chip->request`, `:994` `gpio_direction_output()` calls `chip->direction_output`, and 🔴 `:967` fails early unless **both** `.set` and `.direction_output` exist — so omitting `.set` to make writing impossible is not available, and `:1065` `__gpio_set_value()` dispatches with no NULL check, which would be an oops rather than a refusal. Also `:1155`'s `gpio_to_irq()` call and the `#ifdef CONFIG_DEBUG_FS` at `:1133` that compiles it out. 🔴 **2026-09-06, seating 15: this row was already open at `line` depth on the very function that refuted the card, and the relevant call was not taken.** `:994` is recorded above as *calls `chip->direction_output`*, and it also calls `gpio_ensure_requested()` — 2.6.30's compatibility path, which sets `FLAG_REQUESTED` and calls `chip->request` for a caller that never asked. So `tryout 5` left line 5 held and `B1-C`'s `claim` was refused by the framework with `EBUSY` before this driver's `.request` was reached, against a card predicting `n_req_ok = 2`. ⚠️ **Confirmed at `artefact` depth rather than by re-reading the source, deliberately** — `gpio_direction_output` at `0x800d637c` calls `gpio_ensure_requested` (`0x800d5b00`) at `0x800d642c` in this image's own `vmlinux` — and the errno was **measured on the board**, not read: routing the write through `cat` made `strerror` print `Device or resource busy`. **A file being open at `line` depth is not the same as its behaviour being known**, which is the general form of this and is why the depth column is not a coverage claim |
| `drivers/gpio/Kconfig` | **line** | **generic** | `:27` `menuconfig GPIOLIB`'s `depends on`, the two `ARCH_*_GPIOLIB` declarations at `:5`/`:15`, and `:31`'s `select GENERIC_GPIO`. This is what `FW-38` measured and what `config/host-compat/0005` acts on |
| `drivers/gpio/Makefile` | **name** | **generic** | the `obj-$(CONFIG_GPIOLIB) += gpiolib.o` line, used only as the `MK3` anchor |
| `drivers/Makefile` | **line** | **generic** | `:8` `obj-y += gpio/` — an unconditional descent, which is why `MK3` can be `obj-y` and why removing `CONFIG_GPIOLIB=y` fails at link instead of silently shipping no driver |
| `drivers/Kconfig` | **line** | **generic** | `:55` `source "drivers/gpio/Kconfig"` — asked because a `menuconfig` that is never sourced would have made `FW-38`'s whole question moot |
| `drivers/input/keyboard/Kconfig` | **line** | **generic** | `:292-294` `KEYBOARD_GPIO` `depends on GENERIC_GPIO`. Read to decide `R5-4`'s shape, not `R5-8`'s: it is what makes the gpiolib route forced rather than preferred |
| `drivers/leds/Kconfig` | **line** | **generic** | `:121-123` `LEDS_GPIO` `depends on LEDS_CLASS && GENERIC_GPIO`, for the same reason |
| `arch/rlx/include/asm/mach-generic/gpio.h` | **full** | vendor | **21 lines, and it decided the route.** Under `CONFIG_GPIOLIB` it aliases three `gpio_*` to `__gpio_*`; the `#else` branch declares **six** `gpio_*` functions the arch must define and `arch/rlx` defines none — so "no gpiolib" is not the cheap option it looks like. 🔴 `:16-17` declare `gpio_to_irq()`/`irq_to_gpio()` **outside** both branches, unaliased and undefined here, which is the link hazard recorded in the driver's header |
| `arch/rlx/include/asm/gpio.h` | **full** | vendor | 6 lines, `#include <gpio.h>`. Read to confirm the mach- header above is the one that is reached |
| `arch/rlx/Kconfig` | **line** | vendor | `:12-15` `config MIPS` with its `select EMBEDDED` — the site `0005` patches — and `:275` `config GENERIC_GPIO`, a promptless `bool` nothing in the arch selects |

⚠️ **`arch/mips/Kconfig` and `arch/x86/Kconfig` were also read**, one line each
(`:601`/`:884` and `:29`), to settle which of the two `ARCH_*_GPIOLIB` symbols
is the precedent. They are declared here rather than as rows because they are
other architectures' code that this build never compiles; the reading is in
`config/host-compat/0005`'s preamble, and 🔴 **it corrected a claim that file's
first draft made from a partial view** — a `grep -l` that matched *either*
symbol was read as "both arches select the optional one", and only x86 does.

#### The artefact, and it is a reading of the vendor's GPIO driver

| path | depth | origin | what was taken |
|---|---|---|---|
| `drivers/char/rtl_gpio.c` | **`artefact`** | vendor | 🔴 **The `.c` was never opened. Its compiled form was.** Disassembly of this project's own `vmlinux` (cell `r54b`) with a distribution `objdump`: `rtl_gpio_init` at `0x802B1670` writes `0xB8000040`, then `PABCD_CNR &= ~0x74`, then `PABCD_DIR &= ~0x04 / ~0x10 / ~0x20`, then `PABCD_DIR \|= 0x40`. `SPEC.md` `REG-35` owns the reading; `System.map` supplies the initcall levels (mine 4, the vendor's 6). 🔄 **2026-09-06, seating 15: the same file was read at the same depth again and MUCH further, because the board asked a question the desk had not.** `PABCD_DAT` bit 6 moved under the operator's hand, so the **nine** functions that materialise `0xB800350C` were located — 🔴 *this row said FOUR until the count was re-derived off the eleven `ori` sites; it had been written from five resolved addresses* — and **three of them were actually read**: `reset_button_pressed` (`0x800e59d8`), `rtl_gpio_timer` (`0x800e5c48`) and `rtl_gpio_init`. The other six (`autoconfig_gpio_init`, `_off`, `_on`, `_blink`, `_slow_blink`, `read_proc`) plus `rf_switch_read_proc` were seen and not read, and **that distinction is the whole point of this column**. What was taken is a one-second `mod_timer`, a three-way branch on the hold count (`< 2`, `2`–`4` → `kill_pid(find_vpid(1), 15, 1)`, `≥ 5` → `sb 49` into `default_flag` at `0x80296478`), the `count & 1` blink on bit 6, and the three `/proc` names read out of the ELF at `0x80276150`/`0x80276160`/`0x8027616c`. `SPEC.md` `FW-40` owns it. ⚠️ **This is the deepest read of a vendor driver this project has taken and it is still `artefact`** — no `.c`, no header, no symbol names beyond `System.map`'s. 🔴 **Two of the four functions were SEEN and not read**, and that is written down rather than left to look like coverage: `autoconfig_gpio_init` and `rf_switch_read_proc` also touch `PABCD_DAT` |

🔴 **This is the most expensive single reading in this ledger for its size, and
the reason is what it contains.** § 4.3.1's `artefact` precedent — the
`clocksource_register` transfer count — took a *negative* fact about the
vendor's compiled code. **This one takes register addresses and bit numbers,
which is exactly the layer `driver-diff` scores.** So the honest accounting is:

* the driver was written and **compiled** before this reading, and the image's
  sha256 is the witness — the same ordering argument § 4.3 uses;
* 🔴 **`RTL819X_GPIO_KNOWN_MASK` was deliberately NOT widened** from `BIT(5)`
  to the `0x74` this reading implies. Taking the vendor's bit numbers into the
  driver is precisely what would spend the diff. The bench card predicts the
  post-boot register values from this reading and lets **the board** be the
  arbiter, which keeps the driver blind and uses the artefact only as a source
  of predictions;
* the question it was asked to answer was a **safety** question — *does
  anything else write the block this driver reads* — and the answer is yes,
  at `device_initcall`, after this driver's `subsys_initcall`. There was no
  cheaper instrument: nothing in `SPEC.md` recorded that a vendor GPIO driver
  existed at all until the build log printed `CC drivers/char/rtl_gpio.o`.

⚠️ **`ledgerscan` is structurally blind to this row**, the same way it is to
§ 4.3.1's: the path is never cited as a source file, so the scan cannot find
it. It is declared by hand, and § 7 ⑦ already carries that hole.

### 4.10 🔴 `R5-6` watchdog — 7 new paths, and the vendor side is spent ON PURPOSE

**2026-09-08.** Unlike § 4.9's `gpio`, nothing here was acquired by accident.
The step's central decision is `CONFIG_RTL_WTDOG=n` — removing the vendor's
watchdog arm and its 100 Hz kick — and **a decision to delete code is a
decision that cannot be made blind.** The blast radius had to be enumerated
before the switch was thrown, and enumerating it is reading it.

| path | depth | origin | what was taken | layer |
|---|---|---|---|---|
| `include/asm-rlx/rtl865x/rtl865xc_asicregs.h` | line | vendor | `:2993-3025` — the whole watchdog field block: `WDTCNR (0x01C + TIMER_BASE)`, `WDTE_OFFSET 24`, `WDSTOP_PATTERN 0xA5`, `WDTCLR (1 << 23)`, `OVSEL_15`/`_16`/`_17`/`_18`, `WDTIND (1 << 20)`. It is the second source that pins `OVSEL[0]` at bit 21 against `CLK-08`'s two measured points | **L1 fact** |
| `boards/rtl8196e/bsp/timer.c` | line | vendor | `:75-84`, the `CONFIG_RTL_WTDOG` block inside `bsp_timer_init()`: `REG32(BSP_WDTCNR) = 0x00600000`, and the `CONFIG_RTK_VOIP` arm that calls `bsp_enable_watchdog()` instead. 🔴 **The value is a DECISION**: OVSEL 3, against nine other settings the hardware offers. *(This read "OVSEL 3 = 17.5 ms" until 2026-09-09; 量 seating 17 it is **1,334.723 ms** — the 17.5 ms came from `CLK-08b`'s loader-state constant and is wrong by 76×. The row's point, that the vendor chose one of ten, does not move.)* | 🔴 **L2 decision** |
| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | 🔄 already declared in the `timer` domain; the watchdog half is new. `:146-182` `rlx_timer_interrupt()`: the `WDTCNR \|= 1 << 23` kick **inside the tick ISR**, the `is_fault` branch's `WDTCNR = 0; for(;;)`, and the `CONFIG_RTK_VOIP` variant that ORs the stop pattern back in. 🔴 **Two decisions, not one**: *where* to kick from, and that the kick is a read-modify-write | 🔴 **L2 decision** |
| `boards/rtl8196e/bsp/setup.c` | line | vendor | 🔄 already declared in § 4.2 at `:134-175`; this is `:104-118`, a different range in the same file. `bsp_machine_restart()`: `REG32(GIMR)=0`, `local_irq_disable()`, `shutdown_netdev()`, `REG32(BSP_WDTCNR) = 0`, `while(1)`, and the unreachable `back_to_prom()` after it. 🔴 **This is how `reboot` works on this board** and it is a watchdog bite at OVSEL 0 | 🔴 **L2 decision** |
| `drivers/char/rtl_gpio.c` | line | vendor | 🔄 already declared in § 4.9 as an **artefact** (object-code) reading of the reset-button path; this is a **source** reading of a different function. `:2178-2199` `write_watchdog_reboot()` — `count < 2` → `-EFAULT`, `tmp[0] == '1'`, `local_irq_disable()`, `panic_printk("reboot...")`, `WDTCNR = 0`, `for(;;)`; and `:2611-2616`, `create_proc_entry("watchdog_reboot", 0, NULL)` | 🔴 **L2 decision** |
| `include/linux/watchdog.h` | line | generic Linux | the userspace ABI: `WDIOC_GETSUPPORT`/`GETSTATUS`/`GETBOOTSTATUS`/`KEEPALIVE`/`SETTIMEOUT`/`GETTIMEOUT`/`GETTIMELEFT`/`SETOPTIONS`, the `WDIOF_*` capability bits, `WDIOS_DISABLECARD`, `struct watchdog_info`. **Mainline, and not an implementation of this SoC** — the same category as § 4.9's gpiolib rows | neither |
| `include/linux/miscdevice.h` | line | generic Linux | `:15`, `WATCHDOG_MINOR 130`, and `MISC_MAJOR 10`. Two constants that decide a device node number | neither |

⚠️ **Also read and NOT given rows above, because they are build plumbing rather
than anything about this die**: `drivers/watchdog/Kconfig` (every entry and its
`depends on`, for the `(NEW)` enumeration), `drivers/watchdog/Makefile` (the
MIPS section, for `MK6`'s anchor), `drivers/Makefile:79`, `drivers/gpio/Kconfig:51`
(`GPIO_SYSFS`, for a correction that is not about the watchdog at all), and
`kernel/panic.c:98-106` / `kernel/exit.c:921-949` (where `is_fault` is stored,
to establish what `=n` also removes). None carries a register or a peripheral
decision. **They are listed here rather than omitted** because § 7's own warning
is that a ledger's silence is indistinguishable from a ledger's blindness.

⚠️ **And the wlan kick sites** — `drivers/net/wireless/rtl8192cd/8192cd_hw.c`,
`8192cd_osdep.c`, `8192d_hw.c`, `Hal8192CDMOutSrc.c`, `HalDMOutSrc.c` — were
read for their `#if` gates and nothing else. They record a watchdog *kick*,
which is a use rather than a policy, and they are the reason § 4.4 of
`notes/watchdog-driver.md` exists.

#### 4.10.1 🔴 What this does to `D3`, said plainly

`PROGRESS.md`'s refutation clause for `D3` fires **per driver**, and it fired
for `R5-5` on exactly this ground: *"§ 4.5 records the vendor's MTD map read on
the decision layer, so `R5-5`'s L2 rows are void unless the derivation check
clears them"*.

**The same now holds for `R5-6`**, and more sharply, because four of the seven
rows above are L2:

* `docs/driver-diff.md`'s watchdog section **may not be written as a blind
  diff.** Its L2 rows are *informed contrast*: this driver's decisions were
  taken **knowing** the vendor's, and in three cases were chosen to be the
  opposite of them — kick from a kernel timer rather than the tick ISR;
  compose a full word rather than `|=`; refuse four OVSEL settings the vendor's
  code would happily encode.
* 🟢 **That is not worthless, and the document must say which kind of value it
  is.** An informed contrast with the reason for each divergence written down
  is a legitimate engineering artefact; it is simply not *evidence of
  independent convergence*, which is what a blind diff buys.
* 🟢 **The L1 rows are unaffected** and were never worth much: three
  implementations describing one piece of silicon are expected to agree.

🔴 **The honest summary, and it is narrower than § 4.1's old sentence**: `R5-6`
is blind of every third-party implementation and of nothing else.

### 4.5 🔴 `R5-5` SPI + MTD — 11 paths — **the diff's vendor side is spent**

| path | depth | origin | what was taken |
|---|---|---|---|
| `drivers/mtd/maps/rtl819x_flash.c` | line | **vendor** | 🔴 **decision-layer, repeatedly.** `:62-73` — `rtl8196_map_copy_from` copies **at most 1024 bytes** when `from > 0x10000` and **returns `void`**, so a short read reports success (`LOG.md:9796`). `map->virt = 0xbd000000` (`FLS-11`, `MAP-12`). **Three same-named `rtl8196_parts1[]` tables** and which `CONFIG_` branch selects which (`FW-11`). The partition arithmetic `size = WINDOW_SIZE - CONFIG_RTL_ROOT_IMAGE_OFFSET` (`FW-28`) |
| `include/linux/mtd/map.h` | line | generic | `:425-442` — without `CONFIG_MTD_COMPLEX_MAPPINGS`, `map_copy_from` expands as a macro and `simple_map_init` is a `BUG_ON`, so **the driver's own function pointer is never consulted**. Generic, and it is the fact that decided which of the two implementations above is live |
| `drivers/mtd/mtdchar.c` | name | generic | the `minor & 1` read-only convention behind `/dev/mtd0ro` |
| `drivers/mtd/mtdblock.c` | name | generic | — |
| `include/linux/mtd/mtd.h` | line | generic | `:113` via `config/rlxfw-initramfs.tsv` |
| `drivers/mtd/mtdpart.c` | line | generic | partition registration |
| `drivers/mtd/mtdcore.c` | line | generic | — |
| `drivers/mtd/chips/rtl819x/spi_common.c` | name | **vendor** | named in `SPEC.md`; no extract recorded |
| `drivers/mtd/chips/rtl819x/spi_common.h` | line | **vendor** | `notes/kernel-build.md:3471` |
| `drivers/mtd/chips/rtl819x/spi_probe.c` | line | **vendor** | `bench/2026-08-31/PREDICTIONS-B5-block3.md:448` |
| `bootcode/boot/flash/spi_common.c` | name | **loader** | the loader's SPI, `docs/loader-flash-write.md` |
| `drivers/mtd/chips/rtl819x/spi_probe.c` | **line** | **vendor** | 🔴 **added 2026-09-07 (`R5-5`).** `:101-103` -- `spi_chip_setup()` installs `mtd->read = mtd_spi_read`, `mtd->write`, `mtd->erase` UNCONDITIONALLY, and `:67-71` registers the chip driver as `flash_bank_1`, which is the name `rtl819x_flash.c` hands `do_map_probe`. This is the reading that showed the map layer is not on the path |
| `drivers/mtd/chips/rtl819x/spi_flash.c` | **line** | **vendor** | 🔴 **added 2026-09-07.** `:28-34` `do_spi_read` dispatching through `spi_flash_info[chip].pfRead`; `:141-143` the three function pointers. **decision-layer** |
| `drivers/mtd/chips/rtl819x/spi_common.c` | **line** | **vendor** | 🔴 **deepened 2026-09-07 from `name` to `line`.** `ComSrlCmd_InputCommand` (the command/address/dummy phase order), `ComSrlCmd_ComRead`, `SFCSR_CS_L`/`SFCSR_CS_H`, `spi_regist`'s UNKNOWN fallback (`SpiRead_11110B`, `PageWrite_111002`), `setFSCR`'s `#ifndef SPI_KERNEL`, and `ComSrlCmd_RDID`'s `SFCR` write. **The transaction ORDER in `rtl819x-spi.c` is this file's, and saying otherwise would be a worse driver told as a better story** |
| `drivers/mtd/mtdchar.c` | **line** | generic | 🔄 **deepened 2026-09-07 from `name`.** `:73` odd-minor refusal, `:94` `!MTD_WRITEABLE` refusal, `:419-457` MEMERASE calling `mtd->erase` with **no NULL check**. Generic Linux, and it is what refuted this driver's first draft of layer L2 |
| `drivers/mtd/mtdblock.c` | **line** | generic | 🔄 **deepened 2026-09-07.** `:421` `!(mtd->flags & MTD_WRITEABLE)` -> `dev->readonly = 1` |
| `drivers/mtd/mtdcore.c` | **line** | generic | 🔄 **deepened 2026-09-07.** `add_mtd_device` `:216-246`: `BUG_ON(mtd->writesize == 0)`, first free slot, `mtd->index = i`. That is where the `mtd_index 2` prediction comes from |
| `crypto/algapi.c` | line | generic | 🆕 **2026-09-07.** `:284-293` `crypto_wait_for_test()` -- the `NOTIFY_DONE` branch calling `crypto_alg_tested()` directly, which is why `crypto_alloc_shash` works with `CONFIG_CRYPTO_MANAGER` unset and why the driver carries its own KAT |
| `include/crypto/hash.h` | line | generic | 🆕 **2026-09-07.** the `crypto_shash` API surface |
| `arch/rlx/kernel/rlx-cevt.c` | line | **the port's own** | 🆕 **2026-09-07.** `:156-179` the watchdog kick and `=0` reset comment. Already in § 4.8 for `R5-3b-1`; cited here because `FW-45` is what bounds this driver's traversal |

🔄 **2026-09-08 (forty-fourth segment): `rtl819x-spi` 1.1 added NOTHING to this
table, and that is a claim rather than an omission.** 1.1 adds
`verify <n> <off>`, a two-level `map` and an in-kernel `jiffies` timestamp. The
only files opened to write it were this driver, `tools/flashwin.py` (mine),
this repository's own `.timing`/`.log` captures, and 2.6.30's `read_proc_t`
interface in the tree already staged. **No vendor source and no public port was
read**, so the 20 paths below stand unchanged at 20. Said here because a ledger
that only ever grows is a ledger nobody would notice stopping.

🔴 **Verdict: `R5-5` cannot be claimed as blind against the vendor.** Its
partition layout, its map function's short-read behaviour, its virtual base and
its `CONFIG_` branching have all been read, and three of them are decision-layer
rather than fact-layer.

🔴 **2026-09-07, when the driver was actually written, that verdict got worse
rather than better, and the count is the honest way to say so: 11 paths → 20.**
The transaction order, the phase lengths, the Fast Read opcode with one dummy
byte, and the UNKNOWN-chip fallback are all the vendor's, read out of
`spi_common.c`. **There was never a version of this driver that could have been
written blind against the vendor**, because the vendor's code is the tree it is
compiled into. What `driver-diff` can still score is the layer that is mine:
the bounded spin, the save/restore/read-back guard, the endianness-independent
byte assembly, and the three write-refusal layers — and `notes/spi-mtd-driver.md`
§ 4 and § 5 are where those four are written down as claims a diff can test.

🟢 **Nothing in this block is a third-party port**, so the *diff against
`shibajee`/`ggbruno`* is not directly spoiled — subject to § 6, which is the
part of this that is undetermined.

**`driver-diff`'s SPI/MTD section is written knowing this**, and the correct
outcome may be that the section says so instead of claiming a comparison it
cannot support. `R5`'s `否證 D3` already provides for exactly that.

### 4.6 🟢 `dt` (`D2`, all six bindings) — 2 paths

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/mips/boot/dts/realtek/rtl8196e_totolink_n100re.dts` | name | **third-party (`shibajee`)** | 🟢 **the file NAME only.** It appears in `SOURCES.json`'s description of that tree and in `LOG.md:2788` quoting it — *a device tree for a TOTOLINK board on this SoC*. Not fetched, not opened; the tree is in quarantine (§ 3). ⚠️ It is the **more** relevant of the two to `D2`, being the board file rather than the SoC file, and nothing of it has been seen |
| `arch/mips/boot/dts/realtek/rtl8196e.dtsi` | name | **third-party (`shibajee`)** | 🟢 **the `cpu@0` node only**: `compatible = "lexra,rlx4181"`, `d-cache-size <8192>`, `i-cache-size <16384>`, both line sizes `<16>`, `tlb-entries <32>`. Fetched and read 2026-08-25 for `CPU-25`'s advance cache-geometry prediction (`notes/cache-model.md` § 386, § 488) |

🟢 **The thing that would have spoiled the diff is recorded as absent, and it
was recorded eight days before `R5` opened** — `PROGRESS.md:1353`, 2026-08-25:
*"that file's register addresses are placeholders and `dtc` refuses to parse
it"*. `driver-diff` compares register maps; the register map was not there to
take.

⚠️ **One row in this ledger is marked `third-party`, and it is this one** — one
node of one file, about the CPU rather than about any peripheral. ⚠️ The count
is a hand tally: `origin` is a judgement column, so unlike the domain counts it
is **not** re-derivable by `ledgerscan`, and a reader checking it counts the
`third-party` cells in § 4.

⚠️ It is also the ledger's one **cross-check obligation**: `rtl8196e.dtsi`'s
cache geometry agreed with the vendor build constants and, on 2026-08-31,
`probe3` measured 16 KiB / 16-byte lines / 2-way on this die. A prediction taken
from a third-party tree and then confirmed by measurement is the strongest form
this contact could have taken, and it is why it was worth taking.

🆕 **2026-09-09 (forty-ninth segment): `D2` was written, and this row's count
did not move.** Six bindings and two source files landed under `dt/` —
`notes/device-tree.md` owns them — and **no third-party file was fetched,
opened or searched for while they were written**. The two paths above are
still the two paths.

🔴 **The one place it was tempting is recorded rather than taken.**
`dt-validate` reports a node whose `compatible` matches no schema, so
`lexra,rlx4181` on the `cpu@0` node had to be answered one of two ways: give
it a binding, or declare it. It is declared, in `dt/unmatched-allow.tsv`, with
the reason — **writing a binding for that string would turn a recorded, dated
contact into an artefact of this project**, and a reader six months from now
would find a `lexra,rlx4181` binding in `dt/` with nothing saying where the
string came from. The *value* behind it is independent: 量 `PRId 0x0000CD01`
on this die, mapped through the vendor's own `arch/rlx/include/asm/cpu.h`.

🟢 **And `D2` put two decisions on the L2 layer § 5 describes, both of them
mine and both refutable.** ① the timer's `reg` is `0x1c` and the watchdog's is
the word above it, rather than the two nodes overlapping the documented block;
② the timer is a **clock provider** and the watchdog takes `clocks = <&timer>`,
rather than the watchdog reading `CDBR` out of another device as the 2.6.30
driver does. Both are choices a second implementation can be found to have
made differently, which is what makes them worth `R5-9`'s diff — and ② has a
measured motive rather than an aesthetic one: `CLK-08b`'s 14,965,000 Hz
survived into a shipped driver's table, wrong by 76×, because the rate had no
owner.

⚠️ **What § 6's ordering constraint now also covers.** When the trees are
cloned at `R5-9`, the derivation check is still the first operation — and the
second is that `dt/`'s `compatible` strings are compared against theirs
**as a finding, not as a correction**. A collision or a divergence in those
names is exactly the kind of difference the diff exists to report; silently
renaming to match would destroy the only independent naming this project has.

---

## 5. 🔴 What `driver-diff` compares — the two layers, and why the definition moved

The gate opened with `R5-9` written as *"blind first, then **register by
register** against both public trees"*. That comparison surface cannot measure
what it was chosen to measure, and the ledger is what makes that visible.

| layer | what is on it | why |
|---|---|---|
| **L1 — fact** | register addresses, reset values, bit positions as documented | Three implementations describing **one piece of silicon**. Agreement is *expected* and carries no information about independence; disagreement means somebody transcribed wrong. Worth checking as a **cross-check**, worthless as a diff |
| **L2 — decision** | divisor semantics (`CLK-06`, 推); wrap handling for a modulus that is **not** a power of two (142,858, so `if (d < 0) d += 142858`, single-wrap only); interrupt number and the four arming layers; which bits are write-1-to-clear; initialisation order; `clocksource` `mult`/`shift` selection; rating and coexistence | These are **choices**. Two independent implementations really do differ here, and each difference is decidable on the silicon. **This is the layer the ledger protects** |

🔴 **This changes the gate's `D3`, and the change is written with the objection
against it stated first.** `docs/GATE-RESULTS.md`'s operating clause warns that
*changing a rule because it failed to produce the answer you had already reached
is how such a rule stops being an instrument*. The distinction claimed here:

* No conclusion has been reached. What was found is that **L1 agreement is
  guaranteed by the parts being the same part**, which is an instrument-validity
  problem and not a result.
* **The test:** the new `D3` is *easier* to fail, not harder. *Register by
  register* passes almost by construction, because the addresses will match. The
  two-layer form requires every L2 row to carry a verdict or an explicit 未定
  with the experiment that settles it — and § 4.5 lets the ledger **void** rows
  outright. A change that makes a DoD more refutable is not a target being moved.

---

## 6. 🔴 The question this ledger cannot answer, and the order that keeps it answerable

`driver-diff` compares **me against the third-party ports**. § 4.5 records deep
reading of the **vendor**. Those are different trees, so on the face of it the
diff survives.

**Unless the third-party ports derive from the vendor's `arch/rlx`.** If
`shibajee`'s or `ggbruno`'s peripheral drivers are ports of Realtek's, then
reading the vendor is reading their ancestor, and the independence is gone
without a single third-party file having been opened.

🔴 **This cannot be settled now** — settling it requires cloning, which is the
act this ledger dates. And it cannot be settled *after* reading them either,
because by then the reading has happened.

**So it becomes an ordering constraint on `R5-9`, recorded here while it is
still free to impose:**

> When the trees are cloned at `R5-9`, the **first** operation on each is a
> **derivation check** — file headers, copyright lines, SPDX tags, function and
> symbol names against `arch/rlx`'s — performed **before any register map is
> read**, and its result written down before proceeding. Where a driver is
> derived from the vendor's, that driver's `driver-diff` row is **void**, and
> the ledger's § 4 entry for the corresponding vendor file is the reason.

⚠️ Weak in a stated way: a derivation check is itself a reading, and a
sufficiently careful one drifts into the register map. It is bounded by being
written down in advance and by naming what it may look at.

---

## 7. Where this ledger will fail

1. 🔴 **It is a lower bound (§ 0 ①).** Nothing here can rule out a file read in
   2026-08 and never mentioned.
2. 🔴 **§ 6 is open**, and it is the largest single threat to `D3`.
3. ⚠️ **`ledgerscan`'s regex sees paths, not prose.** *"the vendor's clockevent
   driver"* names no path. `scan --topics` is a second net over subsystem
   keywords, reported separately and **never merged**, because a keyword hit is
   not a citation.
4. ⚠️ **Domain assignment is keyword-based and has already been wrong twice**,
   both caught by its own controls on the first real run: a device tree landed
   in `out-of-scope` because its path says `boot/dts` and every `bsp` needle
   wanted `board`; and `drivers/input/keyboard/gpio_keys.c` landed in `bsp`
   because *keyboard* contains *board*. Both are fixed and both have a control.
   A third of the same kind is likely.
5. ⚠️ **`upstream/` is mine too.** It is pinned at `4d3ff26` (2026-08-22), so
   its reading is history rather than current behaviour, and `ledgerscan`
   reports it separately. Two paths are cited only there —
   `arch/mips/kernel/unaligned.c`, `kernel/sysctl.c` — and both are
   out-of-scope.
6. 🔴 **A ranking in this file goes stale silently, and one already did.**
   § 4.3 called `CLK-06` *the diff's best row*. That is not a fact about a
   source, it is a **comparison among rows**, and it can be falsified by
   anything that changes any other row — here, by reading one page of a
   datasheet this repository had already cited. It survived exactly one
   segment. **The rule from here: this file records what was read and what was
   taken from it, and does not rank rows against each other.** A row that
   deserves emphasis gets it from the experiment that would settle it, which
   is checkable, rather than from a superlative, which is not.
7. 🔴 **A binary of mine carries the vendor's compiled code, and until
   2026-09-03 this file had no shape for a finding taken out of one.** § 4.3.1
   is the first: *no code under `arch/rlx` calls `clocksource_register`*, read
   by counting instruction encodings in my own `vmlinux`. `ledgerscan` cites
   paths and this reading cites none, **so the tool is structurally blind to
   this whole category** — every such row will be written by hand or not at all.
   The `artefact` depth is defined in § 4.3.1 and its test is unchanged: what
   was taken, and could it have shaped a decision.
8. 🔴 **`ledgerscan check` compares SETS OF PATHS and never the depth column, so
   a row can be under-declared and stay green.** 量 2026-09-03: `check` reported
   *ok* over 32 in-scope paths while `kernel/time/jiffies.c` was declared `name`
   and `scan` had it as `line` (`notes/timer-driver.md:273` cites `:37`). The
   depth is what distinguishes *saw the interface* from *read the code*, which
   is the distinction the whole file exists to make, and **the only thing
   checking it is a human reading two outputs side by side**. Fixed in the row;
   the checker is not fixed, and the next under-declared depth will be found the
   same way or not at all.
9. ⚠️ **It says nothing about the toolchain or the datasheets.** Reading
   `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` is not contamination — a datasheet
   is the *specification*, and two implementations reading the same
   specification are still two implementations. That is an argument, not a
   measurement, and it is stated so it can be disputed.

---

## 8. The reading, in one table

🔄 量 2026-09-06 (`R5-4`), `ledgerscan scan`, re-derived at commit. Population: 🔄 **2,054**
tracked files (excluding `upstream/`) and 302 in `upstream/` — both of which
grow with this repository and are quoted for scale, not as findings.
*(1,445 and 302 at `R5-0`, 2026-09-02; **1,447** at `R5-1`, earlier on
2026-09-03.)*

🔄 **The `R5-1` → `R5-2` move is one file — this gate's own card — and it was
found by re-deriving rather than noticed**: the segment that wrote the card left
**1,447** standing in two places while the tool printed 1,448, which is `CNT-1`'s
class inside the file whose whole job is to be re-derivable. ⚠️ **A third number
is also correct and is not this one**: `git ls-files | grep -v '^upstream/'`
returns **1,449**, because the `upstream` submodule's own gitlink entry has no
trailing slash and survives that filter. `ledgerscan` drops it; the two numbers
differ by exactly that entry, and neither is wrong.

**Paths only.** Citation counts are deliberately absent; see the note in § 4.

| domain | paths | for | verdict |
|---|---:|---|---|
| `gpio` | 🔄 **11** paths **+ 1 `artefact`** | `R5-4` | 🟡 **blind of any third-party implementation, and no longer blind of the vendor's.** Eight of the eleven are generic Linux framework plumbing that says nothing about this die; three are `arch/rlx`'s own gpio headers and Kconfig. 🔴 The `+1` is `drivers/char/rtl_gpio.c` read as OBJECT code (§ 4.9), and unlike § 4.3.1's it carries register addresses and bit numbers — the layer the diff scores. The driver source predates it and `KNOWN_MASK` was not widened to match |
| `wdt` | 🔄 **7** | `R5-6` | 🔴 **0 → 7 on 2026-09-08, and NOT by accident.** Blind of any third-party implementation; **not** blind of the vendor's. Four of the seven are on the DECISION layer, so `driver-diff`'s watchdog section is an informed contrast and not a blind diff — § 4.10.1 says so in place. Two of the seven are the mainline `/dev/watchdog` ABI, which says nothing about this die. **A decision to delete code cannot be made blind**, and `CONFIG_RTL_WTDOG=n` is this step's central decision |
| `led` | **0** | `R5-7` | 🟢 blind of any implementation |
| `keys` | 1 | `R5-8` | 🟢 blind — the one citation is `origin: none`, an example inside this tool's own census row (§ 4.1) |
| `timer` | 🔄 **8** paths **+ 1 `artefact`** | `R5-1`, `R5-2` | 🟢 one string literal of the vendor's, plus `rlx-time.c` 🔄 **read 2026-09-04 (`R5-10`), so the *zero citations* clause below is now historical** — with **zero** citations until this file named it, plus **five** generic-Linux paths and **one more of the vendor's** — 2026-09-03 added the clocksource subsystem's header and core, the two files that fix the jiffy length, and `arch/rlx/include/asm/timex.h`, whose single constant is a PC's timer chip (§ 4.3). 🔴 **`CLK-06` is no longer the diff's best row**: D Table 26 states the divisor semantics, so it is L1. The replacement L2 rows are `notes/timer-driver.md` § 3. 🔴 **And the `+1` is not a path**: § 4.3.1, one bit taken out of the vendor's *object* code in my own `vmlinux` — no code under `arch/rlx` calls `clocksource_register` — which `ledgerscan` is structurally blind to (§ 7 ⑦) |
| `dt` | 2 | `D2` | 🟢 one `cpu@0` node, plus the board `.dts` by name only; the register addresses in the `.dtsi` are placeholders, recorded 2026-08-25 |
| `irq` | 2 | `R5-10` | 🟡 two string literals; one is the loader's, not Linux's |
| `bsp` | 8 | all six | 🔴 cross-domain exposure; `bsp_setup():134-175` counts as fully read |
| `spi_mtd` | **20** | `R5-5` | 🔴 **11 → 20 on 2026-09-07**, when the driver was written. The vendor side was already spent; the transaction order is the vendor's and the write-up says so |
| **in scope** | 🔄 **50** *(32 at `R5-3b-1`)* | | `ledgerscan check` requires every one to have a row above, and on 2026-09-03 it went RED **three** times — 29 found against 27 declared; again after the jiffy check read three more; and 🔴 **once on a file that was never opened**, named from memory inside an edit whose purpose was to make a claim narrower (§ 4.3, the `timekeeping.c` row). **33 are declared**: the extra is `include/linux/jiffies.h`, which the scan classes out-of-scope and which is declared anyway |
| `out-of-scope` | 68 | — | generic kernel; no peripheral register map passes through them |

**Committed before any driver source exists.** `git log --diff-filter=A` over
`config/rlxfw-src/` is the check.
