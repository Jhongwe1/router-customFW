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

**Claims.** For each of the twenty-seven external implementation sources this
repository cites, in scope for one of `R5`'s six drivers: which tree it belongs
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

What this repository *has* cited is `arch/rlx/kernel/rlx-cevt.c`, **to the
line** (`notes/vendor-kernel-isa.md:33`, `:139,226`). `CLAUDE.md`: *a tool
reporting `0` is making a claim; every sweep needs a positive control.*
`ledgerscan`'s `P1` is that control and it is this citation, chosen because it
is the one that was nearly missed.

---

## 2. Method — what is computed and what is judged

| | who | what |
|---|---|---|
| **completeness** | `tools/ledgerscan.py scan` | every path-shaped citation of an external source, in `git ls-files` (1,445 at commit; the number grows with the repository) and in `upstream/` (302, walked — `git ls-files` cannot see inside a submodule) |
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

**Twenty-seven in-scope paths.** `out-of-scope` (68 paths) is listed by
`ledgerscan scan` and is not reproduced here: those are generic kernel files —
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

### 4.1 🟢 `R5-4` GPIO, `R5-6` watchdog, `R5-7` LEDs — **zero**; `R5-8` gpio-keys — one, and it is not a reading

**No path in the `gpio`, `wdt` or `led` domains is cited anywhere in this
repository or in `upstream/`.**

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

🟢 **These four are the drivers whose blind-write claim is strongest**, and the
claim is *"no implementation of these peripherals, by anyone, has been read"*.

⚠️ Bounded by § 0 ① and by § 4.2: a board file initialises GPIOs, and
`boards/rtl8196e/bsp/setup.c` **has** been read.

### 4.2 🔴 `bsp` — 8 paths — cross-domain, and the one that bounds § 4.1

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

🔴 **This is the block that keeps § 4.1 from being an unqualified claim.** None
of the eight is a peripheral driver, and none of the extracts records a GPIO,
timer, LED or watchdog register. But `bsp_setup()` is where a board brings its
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
| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | 🟢 **the string literal `"rlx timer"` and the two lines it is on (`:139,226`) — nothing else.** The context is `notes/vendor-kernel-isa.md`'s proof that *this unit runs `arch/rlx` and not `arch/mips`*, which needed three literals unique to files that exist only under `arch/rlx`. **No register, no sequence, no divisor, no interrupt number** |
| `kernel/sched_clock.c` | line | **generic** | `:39`, the weak generic `(jiffies - INITIAL_JIFFIES) * (NSEC_PER_SEC / HZ)`, read to establish that `arch/rlx` defines no `sched_clock` (zero hits) and that `printk_time` therefore has 10 ms resolution. **Generic Linux — every port in existence uses this file** |
| `include/linux/clocksource.h` | name | **generic** | 🆕 2026-09-03, `R5-1`: the `struct clocksource` field list, `clocksource_hz2mult()`, `CLOCKSOURCE_MASK()`, the `read(struct clocksource *)` signature, and the rating band comment (*1–99 unfit for real use*). **The subsystem's interface**, which a clocksource for any part must be written against. It says nothing about this SoC |
| `include/linux/jiffies.h` | name | **generic** | 🆕 2026-09-03, `R5-1`: `LATCH`, `ACTHZ`, `SH_DIV`, `NSEC_PER_JIFFY` and `TICK_NSEC` — read to check, rather than assume, that this build treats one jiffy as exactly 10,000,000 ns. It does, and the check is `notes/timer-driver.md` § 5.1.1. **Generic Linux** |
| `kernel/time/jiffies.c` | name | **generic** | 🆕 2026-09-03, `R5-1`: `clocksource_jiffies`'s **rating 1** and its `mult`/`shift`, which is the number `L2-e`'s choice of rating 0 is measured against. **Generic Linux** |
| `arch/rlx/include/asm/timex.h` | line | 🔴 **vendor** | 🆕 2026-09-03, `R5-1`: `:21`, one constant — `CLOCK_TICK_RATE = 1193182`. 🟢 **It is the i8253 PIT frequency of an IBM PC and describes no part of this SoC**, so what it costs on the decision layer is nil; what it bought is § 5.1.1's table, which says the jiffy length is exact at `HZ=100` and off by tens of ppm at every other `HZ` this port offers. **No register, no sequence, no divisor, no interrupt number** |
| `kernel/time/timekeeping.c` | name | 🟡 **none — a correction** | 🆕 2026-09-03, and it is this ledger's **second** `origin: none` row. `notes/timer-driver.md:41` names this file *inside a note saying it was never opened*: a draft sentence cited it from memory as the place `(now - cycle_last) & mask` is performed, `ledgerscan check` went RED, and the sentence was rewritten to cite `include/linux/clocksource.h`'s `@mask` documentation — which is what was actually read. **Nothing was taken from this file.** The location is about the instrument, not about the device, which is the constraint § 4.1 puts on this category |
| `kernel/time/clocksource.c` | name | **generic** | 🆕 2026-09-03, `R5-1`: `clocksource_enqueue()`, `select_clocksource()`, `clocksource_register()`, `clocksource_unregister()` — read to settle **one decision**, `L2-e`: whether a rating below `clocksource_jiffies`' 1 keeps a source out of the selection, and which way a tie breaks. Generic Linux, identical in every 2.6.30 tree. 🔴 **It touches the decision layer even so**, because a second implementation's rating choice would be reading the same code; `notes/timer-driver.md` `L2-e` cites it by name rather than presenting that choice as arrived at alone |

🔴 **And a file that is NOT cited, listed here because its absence from the
scan is the ledger's claim and a reader should be able to see what was
absent:**

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/rlx/kernel/rlx-time.c` | **none — zero citations** | vendor | **Nothing.** It exists (量 2026-09-02, directory listing, no file opened) and this repository has never cited it, in any spelling. 🔴 It is listed because § 1's first account of the grep was that this file did not exist; it does. `ledgerscan` cannot report a file nobody has mentioned, so this row is written by hand and is exactly the § 0 ① limit made visible |

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

### 4.4 🟡 `R5-10` interrupt map — 2 paths

| path | depth | origin | what was taken |
|---|---|---|---|
| `arch/rlx/kernel/irq_vec.c` | line | vendor | `:36`, the string literal `"RLX LOPI"` — the same `arch/rlx`-vs-`arch/mips` proof as § 4.3. **No routing, no mask register** |
| `bootcode/boot/init/irq.c` | line | **loader** | `:228` and around it. This is the **bootloader's** interrupt code, not Linux's; read for `docs/loader-command-semantics.md` and `notes/cache-model.md` |

⚠️ `R5-10` ships `docs/interrupt-map.md`, **not** an irqchip driver — three
stated reasons in `PROGRESS.md`. A map is a description of hardware, so its
independence matters less than a driver's; this block is recorded for `R6`,
which will write the driver.

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

🔴 **Verdict: `R5-5` cannot be claimed as blind against the vendor.** Its
partition layout, its map function's short-read behaviour, its virtual base and
its `CONFIG_` branching have all been read, and three of them are decision-layer
rather than fact-layer.

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
6. ⚠️ **It says nothing about the toolchain or the datasheets.** Reading
   `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` is not contamination — a datasheet
   is the *specification*, and two implementations reading the same
   specification are still two implementations. That is an argument, not a
   measurement, and it is stated so it can be disputed.

---

## 8. The reading, in one table

量 2026-09-03, `ledgerscan scan`, re-derived at commit. Population: **1,447**
tracked files (excluding `upstream/`) and 302 in `upstream/` — both of which
grow with this repository and are quoted for scale, not as findings.
*(1,445 and 302 at `R5-0`, 2026-09-02.)*

**Paths only.** Citation counts are deliberately absent; see the note in § 4.

| domain | paths | for | verdict |
|---|---:|---|---|
| `gpio` | **0** | `R5-4` | 🟢 blind of any implementation |
| `wdt` | **0** | `R5-6` | 🟢 blind of any implementation |
| `led` | **0** | `R5-7` | 🟢 blind of any implementation |
| `keys` | 1 | `R5-8` | 🟢 blind — the one citation is `origin: none`, an example inside this tool's own census row (§ 4.1) |
| `timer` | 🔄 **8** | `R5-1` | 🟢 one string literal of the vendor's, plus `rlx-time.c` with **zero** citations until this file named it, plus **five** generic-Linux paths and **one more of the vendor's** — 2026-09-03 added the clocksource subsystem's header and core, the two files that fix the jiffy length, and `arch/rlx/include/asm/timex.h`, whose single constant is a PC's timer chip (§ 4.3). 🔴 **`CLK-06` is no longer the diff's best row**: D Table 26 states the divisor semantics, so it is L1. The replacement L2 rows are `notes/timer-driver.md` § 3 |
| `dt` | 2 | `D2` | 🟢 one `cpu@0` node, plus the board `.dts` by name only; the register addresses in the `.dtsi` are placeholders, recorded 2026-08-25 |
| `irq` | 2 | `R5-10` | 🟡 two string literals; one is the loader's, not Linux's |
| `bsp` | 8 | all six | 🔴 cross-domain exposure; `bsp_setup():134-175` counts as fully read |
| `spi_mtd` | 11 | `R5-5` | 🔴 the vendor side is spent, three findings on the decision layer |
| **in scope** | 🔄 **32** | | `ledgerscan check` requires every one to have a row above, and on 2026-09-03 it went RED **three** times — 29 found against 27 declared; again after the jiffy check read three more; and 🔴 **once on a file that was never opened**, named from memory inside an edit whose purpose was to make a claim narrower (§ 4.3, the `timekeeping.c` row). **33 are declared**: the extra is `include/linux/jiffies.h`, which the scan classes out-of-scope and which is declared anyway |
| `out-of-scope` | 68 | — | generic kernel; no peripheral register map passes through them |

**Committed before any driver source exists.** `git log --diff-filter=A` over
`config/rlxfw-src/` is the check.
