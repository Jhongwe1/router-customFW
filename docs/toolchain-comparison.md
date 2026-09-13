# `R2c` — three toolchains, the same measurements, three columns

**`R1-pub-6`, desk, 2026-09-13. No power. Every run under
`tools/vendor-tripwire.sh`, six trees CLEAN before and after each.**

The plan's `R2c` is *three toolchains each run the same set of measurements, not
pick one and then check it*. `docs/toolchain-prior-art.md` § 6 measured, before
this file existed, that most of that table was already in the repository and had
never been assembled: five files, one table, nobody had written it. This is the
table.

**It is an assembly plus five new readings, and it does not close `R2c`.** The
plan requires one row — the load delay — to run **on the silicon in all three
columns**, and § 3 says where that stands. This file says so at the top rather
than at the bottom.

---

## 0. What this claims, and the four things it does not

**Claims.** For each of the three rsdk releases on this disk: what it is, what
it accepts, what it emits, how big the product is, and whether anything it built
has ever executed on this device — with every cell carrying the file that owns
it.

🔴 **Does not claim ① — that a column is a toolchain.** A column here is a
**package**: a release, a *driver binary inside it*, and a `-march`. § 1 is why,
and it is not a formality: the same filename is the raw compiler driver in one
release and the wrapper in the next, and half of one committed table was
measured through each without saying so.

🔴 **Does not claim ② — that any cell is a statement about the die.** Every row
but one is a property of a program on this disk. The one that is about the die
is marked, and it has one column filled of three.

🔴 **Does not claim ③ — that the three columns are the choice.** The release
that would settle `TC-01` is not on this disk (§ 4). Every column here is a
proxy for it and the table says which.

⚠️ **Does not claim ④ — that a filled row is a finished row.** `notes/` owns the
working for most of these; this file owns the *comparison*, and where a cell
came from one release and was published under a label covering two, § 5 says so.

---

## 1. The columns, and why a column is a package

| | `T1` | `T2` | `T3` |
|---|---|---|---|
| release | `rsdk-1.3.6-4181-EB-2.6.30-0.9.30` | `rsdk-1.3.6-5281-EB-2.6.30-0.9.30` | `rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714` |
| gcc | `3.4.6-1.3.6` | `3.4.6-1.3.6` | `4.4.5-1.5.5p4` |
| binutils | `2.16.94-1.3.6 20060612` | `2.16.94-1.3.6 20060612` | `2.19.92.20091006` |
| the wrapper `rsdk-linux-gcc` accepts | `-march=4181` only | `-march=5281` only | `-march=5281` only |
| the **raw driver** is called | `mips-linux-gcc` | `mips-linux-gcc` | **`mips-linux-xgcc`** |
| `mips-linux-gcc` therefore **is** | the raw driver | the raw driver | **the wrapper** |
| the wrapper hands down | `-EB` | `-EB` | `-ffix-bdsl -fuse-uls -msoft-float -EB` |

量 2026-09-13 for the last three rows, **by behaviour rather than by filename or
size**: `T3/bin/mips-linux-gcc -march=4181` answers `FATAL: -march mismatch.
RSDK is configured for -march=5281 only`, and `T3/bin/mips-linux-xgcc
-march=4181` compiles. The injected flag lists are read from the wrapper's own
`RSDK_LOGFILE`. `SPEC.md` `TC-50`; `notes/vendor-toolchains.md` § 2 and § 5.2.

🔴 **`-EB` is a no-op, so on 1.3.6 the wrapper and the raw driver are the same
experiment** — 量 `readelf -h`: an object built with no `-EB` is already
`2's complement, big endian`. On 1.5.5 they are not: at the one `-march` the
wrapper accepts, the two read **390 / 0 / 0 / 133** and **390 / 1 / 19 / 134**.

**The fourth column is missing and the fifth is the device**, and neither is a
toolchain on this disk:

| | what it is |
|---|---|
| `rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225` | right generation **and** right core. Named by all three drops' `users/Makefile`, shipped by none. `SPEC.md` `TC-20` |
| `gcc 4.4.5-1.5.5p2` | what built the firmware on this unit, known only from its kernel banner. Not a directory here. `SPEC.md` `TC-01` |

---

## 2. The table

🔴 **The plan specifies this table's rows, and a deliverable that does not map
onto its own specification cannot be checked against it.**
`plan/router-rebuild-plan.md:389` is a three-row table headed *what to measure /
how / why this row is on the table*. Here is each row, where it is answered, and
whether it is finished:

| the plan's row | how the plan says to measure it | answered in | finished |
|---|---|---|---|
| **load-delay handling** — the plan's own note on it is *the only cell that can kill the project silently* | `R1f`'s fragment, compiled once per toolchain, **all three run on the silicon** | § 2.2 and § 3 | 🔴 **desk yes, silicon 1 of 3** |
| **`lwl`/`lwr` generation** | a small program containing an unaligned access, counted by disassembly | § 2.3 | 🟢 yes, and by the method the plan names |
| **size, and which hardening flags are available** | compressed rootfs size; whether `-fstack-protector[-strong]` and `_FORTIFY_SOURCE` are there | § 2.4 for the flags, § 2.1 for the sizes | ⚠️ **flags yes, compressed rootfs size NOT measured** |

⚠️ **The third row's size half is about a root filesystem and this table has
none.** § 2.1 gives `vmlinux` and `boa` sizes, which are what this repository has
built three of; the plan's figure is a *compressed rootfs* and it feeds `R7`'s
budget. It is named here rather than quietly substituted, because a size that
answers a different question is the shape § 5 spends five items on.

Cells are 量 at the desk unless marked. A cell that is a committed reading names
its owner; a cell taken on 2026-09-13 for this file is marked 🆕.

### 2.1 What each one will build

| | `T1` | `T2` | `T3` | owner |
|---|---|---|---|---|
| raw `as` `-march` vocabulary | 14 of 14 spellings | 14 of 14 | **12 of 14** — `lx4180` and `lx5280` refused, the numeric forms accepted | `TC-48` |
| 20-instruction matrix at 8 `-march` | the committed 160 cells | **160 of 160** identical to `T1` | **118 of 120** over the six shared columns; the two are `jalx` at `mips1` and `mips2` | `TC-48` |
| `boa` from the RTL8196E drop | ✅ 506,532 B | ✅ 481,332 B | ✅ 363,608 B | `notes/rebuild-vs-shipped.md` § 1 |
| `boa` from either RTL8198 drop | ✅ | ✅ | 🔴 **refused** — `fmget.c:271: static declaration of 'convert_bin_to_str' follows non-static declaration`, which gcc 3.4.6 accepts and 4.4.5 rejects | same |
| a complete `vmlinux` from one source | ✅ 3,340,287 B | ✅ 3,207,595 B | ✅ 3,166,710 B | `TC-16` |
| its entry point | `0x80003600` | `0x800035a0` | `0x80003420` | same |
| host-side: needs an i386 `libz.so.1` | 🆕 **no** — zero `libz` in `ldd` | 🆕 **no** | **yes**, 17 programs | `TC-05`, `notes/vendor-toolchains.md` § 3 |

### 2.2 The load delay slot — the row this table exists for

`tools/hazlint` over `users/dhrystone/dhry_1.c` at `-O2`, through each
release's **raw** driver. loads / nop after load / violations.

| `-march` | `T1` | `T2` | `T3` |
|---|---|---|---|
| `4180` | 421/121/**0** | 421/121/**0** | 388/90/**0** |
| `4181` | 421/121/**0** | 421/121/**0** | 388/90/**0** |
| `5181` | 421/121/**0** | 421/121/**0** | 384/91/**0** |
| `5280` | 425/0/**107** | 425/0/**107** | 390/1/**134** |
| `5281` | 425/0/**162** | 🆕 **424/0/147** | 390/1/**134** |
| `4281` | 425/0/**162** | 🆕 **424/0/147** | 390/1/**134** |

🟢 **The control that makes this comparable with the record**: `T1` at `5281`
reproduces `notes/vendor-toolchains.md` § 5's committed `1.3.6` row cell for
cell, and all three `T3` rows reproduce too. So this is the same instrument, and
the committed `1.3.6` numbers are `T1`'s. 🔴 `T2` had never been on it, and it
differs in exactly the two columns that have violations in them. `SPEC.md`
`TC-51`.

Whole `vmlinux`, same source, same `.config` (767 symbols, differing on none),
bounded below the MIPS16 band — `notes/vendor-toolchains.md` § 5:

| | loads | nop after load | violations |
|---|---:|---:|---:|
| `T1` at `-march=4181` | 61,568 | 17,423 (**28.30 %**) | **4** |
| `T2`-or-`T1` at `-march=5281` — see § 5 | 64,729 | 108 (0.17 %) | **20,201** |
| `T3` at `-march=5281` | 65,740 | 117 (0.18 %) | **21,185** |
| **this unit's own kernel** | 63,298 | 19,419 (30.68 %) | **0** |

Conditional moves whose destination is the register a load just wrote —
`notes/kernel-build.md`:

| | `movz` + `movn` | in a load delay slot, `rd` = the loaded register |
|---|---:|---:|
| `T1` at `4181` | 1,495 | **4** |
| `T2`-or-`T1` at `5281` | 1,523 | 33 |
| `T3` at `5281` | 1,526 | 27 |
| this unit's own kernel | 1,574 | **0** |

### 2.3 Unaligned loads and stores

`lwl` + `lwr` + `swl` + `swr` emitted for a packed-struct access, no flag given
— 量 2026-09-13, and the asymmetry that used to be attributed to the generation
is the wrapper's:

| invoked as | `T1` | `T2` | `T3` |
|---|---|---|---|
| the raw driver | 0 | 0 | 🆕 **0** |
| `rsdk-linux-gcc` (the wrapper) | 0 | 0 | **4** |
| the raw driver with `-fuse-uls` | 4 | 4 | 4 |
| the wrapper with `-fno-use-uls` | — | — | **0** |

`SPEC.md` `CPU-16` and `TC-50`; `notes/lwl-mystery.md` § 3.

### 2.4 Hardening — 🆕 every cell on this row is new

| | `T1` | `T2` | `T3` | `mips-linux-gnu-gcc-12` |
|---|---|---|---|---|
| `-fstack-protector` | **refused**, `unrecognized command line option` | **refused** | **accepted** | accepted |
| `-fstack-protector-all` | **refused** | **refused** | **accepted** | accepted |
| `-fstack-protector-strong` | **refused** | **refused** | **refused** | accepted |
| `__stack_chk` symbols actually emitted | — | — | 🔴 **0** | **2** |
| what it says while doing that | — | — | `warning: -fstack-protector not supported for this target`, **exit 0** | — |
| `__*_chk` entry points in its `libc.a` | **0** | **0** | **0** | — |

🔴 **The older toolchain fails loudly and the newer one fails silently.** gcc
3.4.6 has no such option and refuses the build. gcc 4.4.5-1.5.5p4 accepts it,
warns, emits a plain prologue, and exits 0 — so a build system that passes
`-fstack-protector` and checks the exit status gets a clean build with no
protection. **Controls**: the same fixture through the host gcc emits
`U __stack_chk_fail`, and through `mips-linux-gnu-gcc-12` emits two such
symbols, so the instrument works and this is not *MIPS cannot do it*. A bogus
`-fzzz-not-a-flag` is refused by all three, so *accepted* means recognised.
`_FORTIFY_SOURCE` has nowhere to land in any column: zero `__*_chk` in every
`libc.a`, with `memcpy` present as the denominator. This attributes `SPEC.md`
`FW-18`'s *no mitigations at all* on the shipped artefacts to the library rather
than to a build-flag choice.

### 2.5 Identity and provenance

| | `T1` | `T2` | `T3` | owner |
|---|---|---|---|---|
| `libgcc` soname a build gets | `libgcc_s_4181.so.1` | `libgcc_s_5281.so.1` | `libgcc_s.so.1` | `notes/rebuild-vs-shipped.md` § 4 |
| `PT_*` count of the `boa` it builds | 7 | 7 | **8** | same |
| `binsim` containment vs this unit's 2018 `boa` | 0.2401 | 0.1033 | 0.2522 | `TC-12`, same |
| which drop's `.config` selects it | `rtl819x-toolchain` (RTL8196E) | `saturn49-wecb` **and** `wecb-vz-gpl` (RTL8198) | **none** | `TC-17` |
| uClibc version | 🔴 unmeasured | 🔴 unmeasured | `0.9.30.3` — from the release **string**, not the library | `TC-01`, § 6 |
| **has anything it built ever run on this die** | ✅ three kernels, `hazlint` **0** in each (112,505 / 111,801 / 109,922 loads); one boot timed at **7.260 s** | 🔴 **nothing** | 🔴 **nothing** | `TC-43`, `notes/kernel-build.md` |

---

## 3. 🔴 The row the plan calls the only one that can kill the project quietly

`plan/router-rebuild-plan.md:1141` requires `R2c`'s table to have three rows and
says of the load-delay one that all three columns **must run on the silicon** —
`R1f`'s fragment compiled once per toolchain — and § 389 of the same file marks
that row as the only cell that can kill the project silently.

**§ 2.2 fills it at the desk in all three columns and on the die in one.** Two
of the three columns have never had anything execute on this device, and that is
not a gap this file can close: it needs a seating.

⚠️ **Why the desk half is not a substitute, stated rather than assumed.**
`hazlint` reads a static instruction stream. A violation it reports is a load
whose result is read by the next instruction *in the file*; whether this die
returns the stale value is `CPU-14`'s question and the reason `R1f` exists. The
desk column says *this compiler will emit the shape*; the silicon column would
say *this part computes the wrong answer when it does*.

🟢 **And the cost is bounded rather than argued.** `R1-pub-5` is `R1f` at one
toolchain by two or more `-march` values; this row is `R1f` at three toolchains.
One payload generator taking (toolchain, `-march`) as parameters puts both
steps' bench halves on **one** seating. `PROGRESS.md`'s step table carries that.

---

## 4. 🔴 The column that cannot be filled, and what every other column is a proxy for

`rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225` is named by all three drops'
`users/Makefile` and shipped by none. It is the only release with **both** the
generation that built this unit's firmware and the core this board has. Every
column in § 2 differs from it in at least one of those two axes:

| column | generation | core | so it is a proxy for |
|---|---|---|---|
| `T1` | wrong (3.4.6) | right (4181) | what the *core* wants |
| `T2` | wrong (3.4.6) | wrong (5281) | the `-march` axis at fixed generation |
| `T3` | right family (4.4.5) | wrong (5281) | what the *generation* does |

And the device's own is `4.4.5-1.5.5**p2**` against the `p4` on hand, so even
`T3` is one patch level away. This is why `TC-01`'s identification is 推 and not
量, and no amount of desk work here changes it.

---

## 5. What the assembly found that was on nobody's list

**① A committed method sentence names the wrong binary for half of its own
table.** `notes/vendor-toolchains.md` § 5 says its columns came from
*`mips-linux-gcc`, not `rsdk-linux-gcc`*. On 1.5.5 those are the same file, it
refuses five of that table's six `-march` values, and at the sixth it answers
differently. The 1.5.5 rows are `mips-linux-xgcc`'s, which § 2.2 reproduces cell
for cell. **The sentence is true and harmless for the 1.3.6 half** — there the
wrapper adds only a no-op — which is why nothing caught it.

**② A table labelled by generation was measured on a release, and at two of six
`-march` the two releases of that generation disagree.** `T1` and `T2` are
byte-identical at `-march=4181` — same `.s` sha256 at `-O2` and at `-Os`, which
is stronger than the triples matching — and differ by 106 lines at `-march=5281`,
where they read 425/0/162 and 424/0/147. 🔴 **The published number is `T1`'s, and
`T1` is the release whose wrapper refuses that `-march`.** Since
`arch/rlx/Makefile` sets `CROSS_COMPILE := rsdk-linux-`, the only 1.3.6 build
anyone can perform at `-march=5281` is `T2`'s, and it reads **147**.
⚠️ Whether `notes/kernel-build.md` § 1.1's whole-`vmlinux` delta — *`-march`
alone, generation held at 1.3.6: 4 → 20,201* — carries the same confound is
**undetermined**: neither file records which 1.3.6 built that artefact, and
settling it costs three kernel builds rather than three objects.

**③ Of the three flags the 1.5.5 wrapper injects, only one moves a load-use
reading, and what it moves is not what its name is about.** Nine
single-variable runs; every combination containing `-ffix-bdsl` produces one
object sha256 and every combination without it produces another, with no third
value. `-ffix-bdsl` takes the unresolved-successor count from **19 to 0**:
each of those reads *the load is in the delay slot of a register jump*, and
filling branch delay slots takes the load out of that class. `SOURCES.json`
warns that `-ffix-bdsl` is about the **branch** delay slot and must not be
conflated with the load-use delay. 量: it does not fix a load-use hazard — the
violation count moves by one — and it changes the load-use **reading** anyway,
because `hazlint`'s gate fails an unresolved successor. The two are independent
in what they mean and not in what they measure.

**④ The `lwl` default asymmetry belongs to the wrapper.** On a packed-struct
fixture every raw driver emits zero and only the 1.5.5 wrapper emits four,
because it injects `-fuse-uls`; `-fno-use-uls` through that wrapper takes it
back to zero. `notes/lwl-mystery.md`'s conclusion — *the lever is a build flag
which both generations carry* — survives and gets narrower: **the generations'
own defaults are identical.** ⚠️ 推 that the committed table took the wrapper
route; it does not name its driver, and that route reproduces its three rows
exactly while the raw route reproduces none of them.

**⑤ A hardening flag that is accepted, warns, emits nothing, and exits 0.**
§ 2.4. It is the same shape as ① and ③ — the tool answers, and the answer is
about something other than what was asked.

---

## 6. The rows with no cell in two or more columns

Stated as a list, because a table that quietly omits them reads as complete.

* 🔴 **uClibc version, 2 of 3 empty.** `T3` has `0.9.30.3` from its release
  *string* matched against the device banner. `T1` and `T2` have only a public
  mirror's statement about the 1.3.6 *family*, which names no release.
  ⚠️ **And one route is now known not to work**: `features.h`'s
  `__UCLIBC_MAJOR__` / `__UCLIBC_MINOR__` / `__UCLIBC_SUBLEVEL__` lines are
  inside a **documentation comment** in all three trees, so a grep for them
  returns `0.9.26` for every release and that is the example in the comment, not
  the version. Recorded because it looked like a finding for about two minutes.
* 🔴 **Anything running on this die, 2 of 3 empty.** § 2.5, and § 3 is what it
  would take.
* ⚠️ **The wrapper's injected flag line for `T2`** — recorded for `T1` and `T3`.
  Its `-EB`-only shape is 讀 from `T1`'s, not measured on `T2`'s own log.
* ⚠️ **The published 20-instruction matrix body for `T2` and `T3`.** Only `T1`'s
  160 cells are committed; the others exist as agreement counts (`TC-48`).
* ⚠️ **`-march=5181` and `-march=4281` through the wrapper, all three columns.**
  Tried in 2026-08-28's sweep and deliberately not published
  (`notes/vendor-toolchains.md` § 2).

---

## What could still be wrong

* 🔴 **Every row but one is about a program on this disk, not about the die.**
  § 0 ② says it and § 3 is the consequence. A reader who takes § 2.2's violation
  counts as statements about this silicon has read the table backwards.
* 🔴 **`dhry_1.c` is one source at one `-O` level.** The byte-identity of `T1`
  and `T2` at `-march=4181` is a statement about that source and those flags,
  not a proof that the two code generators are the same program. They are
  measurably different binaries; § 5 ② says only where the difference showed.
* ⚠️ **The whole-`vmlinux` rows are inherited, not re-measured here.** They were
  taken before the driver-naming defect was found, and the release that built
  the `-march=5281` artefact is not recorded. § 5 ② names the experiment.
* ⚠️ **`binsim` containment is a ruler with its own calibration**
  (`TC-11`), and the three values in § 2.5 are quoted from
  `notes/rebuild-vs-shipped.md` rather than recomputed.
* 🔴 **The fourth column's absence is not a gap in this file, it is the shape of
  the problem** (§ 4). Anything here that reads as *which toolchain should rlxfw
  use* is `TC-05`, half of which is still blank, and it is a decision rather
  than a reading.
