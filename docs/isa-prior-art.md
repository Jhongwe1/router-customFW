# What this repository already holds about this core's ISA

**`R1-pub-0`, desk, 2026-09-12. No power, no payload source, no device
reading.**

`R1-pub`'s claim is *this is not in public data*. That claim is only worth
making if it is also true that it is not already in **this** data, and
afterwards *"we had not measured it"* is unverifiable. So this file freezes,
before a line of `R1a` or `R1b` payload source exists, every instruction row
and every hazard row this repository already holds — with the route the
evidence came by, the `SPEC.md` id that owns it, and the seating it was taken
at.

Its ordering is checkable the same way `docs/blind-write-ledger.md` § 1 is:
`git log` shows this file committed before any `R1a`/`R1b` payload source. Its
**contents** are checkable a different way — `tools/isacensus.py check` derives
both populations from this repository's own instruments and joins them against
`tools/isa-census.tsv` in both directions, and the three tables below are
generated blocks that the same command re-derives and compares.

---

## 0. What this claims, and the four things it does not

**Claims.** For every instruction whose presence on this die is in question,
and for every hazard shape this repository has an instrument for: which of four
evidence routes it already has, what that route cannot see, and what is left
for a payload to do.

🔴 **Does not claim ① — that it is a record of what has been measured.** It is
a record of what this repository has **written down**, joined to what its
instruments derive. A reading taken and never recorded is invisible to it. That
is the same bound `docs/blind-write-ledger.md` § 0 states about itself, and it
is a **lower** bound on prior art.

🔴 **Does not claim ② — that the population is the ISA.** It is *"what this
core is not known to implement"*, which is a much smaller set and is derived
rather than chosen — see § 1. An instruction this core obviously has, and that
the loader executes thousands of times per boot, gets no row.

🔴 **Does not claim ③ — that a route-③ row is undecided.** For most of the 22
route-③ rows the vendor's own assembler *rejects* the instruction for this
core's `-march` and the vendor's own binaries contain *zero* of it. The
expected answer is written down in advance. What is missing is the reading, not
the prediction.

⚠️ **Does not claim ④ — anything about the vendor kernel's behaviour.** That is
`R1c`, one gate step later, and it is a different table with a different
instrument. This file is about the die.

---

## 1. The population, and why it is derived rather than chosen

A hand-written list of instructions to probe is a claim about judgement. Both
populations here are computed from instruments that already exist and were
written for other reasons:

| | instrument | what it contributes | why it is the right source |
|---|---|---|---|
| **`R1a`** | `tools/hazlint`'s `ISA_OPS` and `ISA_TRAPS` | 27 mnemonics | the tool states its own membership rule: MIPS-I **minus** the four unaligned ones, because a Lexra core is MIPS-I minus those; everything above MIPS-I; and MIPS-I's own optional coprocessors 2 and 3 |
| **`R1a`** | `tools/isa-probe.sh`'s probe rows | 20 mnemonics | what the vendor's own assembler was actually asked about, per `-march`, across six Lexra architectures |
| **`R1b`** | `tools/hazlint`'s `survey()` keys | 3 shapes | its docstring: these are the shapes it counts and **refuses** to give a verdict on, because *"the shapes are what R1b goes and measures"* |

🟢 **Neither `R1a` instrument covers the other, and that is measured rather than
assumed.** 量 2026-09-12: 16 mnemonics come only from `hazlint` — the six MIPS-II
trap instructions, three of the four branch-likely forms, the `SPECIAL2`/
`SPECIAL3` opcode groups, four FPU load/stores and `swc3` — and 9 come only
from `isa-probe.sh`, because `movz`, `movn`, `sync`, `madd`, `rdhwr`, `mfc1`,
`mfc3`, `mtc3` and `pref` are not opcodes in `ISA_OPS`'s table. The union is
the population, `isacensus check` fires when either instrument grows, and
`isacensus --self-test` `T14` fires if either instrument's exclusive
contribution ever falls to zero, because a redundant instrument should have its
cost re-argued rather than kept.

**Six** rows are **declared** rather than derived, each carrying a citation
that must still be present in the file it names, or the population would be
tunable by whoever edits the table. On the `R1a` side: `COP2` (`hazlint`'s own
comment says coprocessor 2 is a gap nothing here has looked for) and
**`mflxc0`/`mtlxc0`** (`docs/interrupt-map.md` § 1.1 — COP0's opcode with `rs`
3 and 7, a third coprocessor register file neither instrument knows about). On
the `R1b` side: the load-use shape itself (`hazlint`'s main check, which is not
a `survey()` key), the `movz` write-enable hazard (`SPEC.md` `TC-h`), and the
store hazard class (`hazlint`'s `C-9`/`F47` note).

🔴 **This sentence said *three* until the closeout audit, and both halves of
that were wrong.** Two rows arrived from the audit rather than from the
derivation (§ 10 ⑥) — and the original three had already missed the `R1b`
load-use row, which is declared and was never listed. 量: the count is
recomputed from the table by the patch that writes this paragraph, and that
recomputation is what refused the first number.

<!-- isacensus:counts begin -->
| | ① bare metal, ours | ② vendor code on the die | ③ vendor material only | ④ nothing | total |
|---|---:|---:|---:|---:|---:|
| `R1a` instruction rows | 2 | 10 | 20 | 7 | **39** |
| `R1b` hazard rows | 1 | 2 | 2 | 1 | **6** |
<!-- isacensus:counts end -->

---

## 2. The four evidence routes

This repository already marks with all four. Three of them are not a
bare-metal reading, and one of those three is the reason `R1a` exists at all.

| route | what it is | what it cannot see |
|---|---|---|
| **①** | 量 on the die, by a payload of ours, under a handler of ours | nothing about the vendor kernel — that is `R1c` |
| **②** | 量 on the die **indirectly**: code that has run on this part contains the encoding, and the boot completes with no exception message. On every row here that code is the loader's or the vendor kernel's, and § 10 ④ is this file measuring the one candidate for an exception and finding none | § 2.1 |
| **③** | 讀 vendor material: the assembler's per-`-march` answer, a Kconfig knob, a count in a binary. Never the die | what Realtek's toolchain and kernel *believe*. § 6 of `notes/vendor-kernel-isa.md` records the two vendor sources **disagreeing** about `ll`/`sc` |
| **④** | nothing | — |

Route ② is not a weaker version of route ①. `SPEC.md` `CPU-17` already carries
exactly this mark and splits it correctly: 讀 for the count of `movz` sites in
the loader, **量 for the absence of an exception message** across eighteen
captures. The absence is a reading. What it is a reading *of* is the question.

### 2.1 🔴 What route ② cannot see is the cell `R1a` exists to fill

An instruction the core does not implement **traps**, and route ② sees that.
An instruction the core decodes as a `nop`, or as something else, **retires** —
no fault, no warning, wrong value. Route ② sees nothing.

That is not a hypothetical shape. It is `F46`'s, and this project's own
`CLAUDE.md` bans `-march=mips32` on that exact ground: *mips32 miscompiles
silently — no fault, no warning, just wrong values.* It is also why `R1a`'s
verdict is **three-way** and not two-way, and why the third cell — *does not
trap and computes the WRONG answer* — is the one the step list calls the
easiest to lose.

> **Route ② is sound for *does not trap* and silent on *computes the right
> answer*.** Every one of the twelve route-② rows below is a row where the first
> half is settled and the second half is untouched.

Route ② has a second limit, and it is narrower and worth stating separately: it
is evidence about **the encoding the vendor's code actually contains**, not
about the instruction. The vendor kernel's `movz` sites all have one register
shape; a `movz` with a different operand pattern is not covered by them.

### 2.2 🔴 For a hazard row, route ② is evidence of the SHAPE and never of the absence of the hazard

`SPEC.md` `CPU-29` counts 16 sites in the loader where `mult`/`div` is followed
immediately by `mfhi`/`mflo`, with no `nop`. `CPU-30` counts three where `mtc0`
is followed immediately by `mfc0`. Both run on every boot and the board boots.

`SPEC.md` `CPU-31` states the limit in its own words: *數得出來不等於判得出來*
— countable is not decidable. The count is equally consistent with an
interlocked core, and with an interlocked core in which those nineteen sites
are latent bugs whose wrong values happen not to matter. Only a payload that
varies the number of intervening `nop` instructions and watches when the read
becomes correct decides it.

So in the `R1b` table below, a `y` in column ② means *this shape executes on
this die in vendor code on every boot*. It never means *the hazard is absent*.
⚠️ **This sentence was widened to *"in code that has run"* and then narrowed
back inside one segment** — § 10 ④ is the measurement that did both, and the
record of it is kept because the wider wording is what a reader would reach for
next.

---

## 3. `R1a` — the instruction rows

Sorted by route, strongest first. `y` in a route column means evidence of that
class exists; the rightmost column says what is still open, which for a
route-② row is always the third verdict cell.

<!-- isacensus:r1a begin -->
| row | ① | ② | ③ | `SPEC.md` | reading taken at | what is still open |
|---|:-:|:-:|:-:|---|---|---|
| `cache` | y | y | y | `CPU-44` | `bench/2026-08-30` | retires, four op values (0x10 IInval, 0x11 DInval, 0x15 DWBInval, 0x19 DWB), n=0 on each. `x-c10`'s untreated twin moved too, so this is *retires* and not *invalidates* |
| `mfc3` | y | . | y | `CPU-46` | `bench/2026-08-30` | eight reads with `CU3` set and held, `m.traps=00000000`; under qemu all eight trap with ExcCode 0x0B, so the die and the emulator disagree about this row |
| `jalx` | . | y | y | `CPU-09`, `CPU-48` | — | 180 in-image targets in this unit's kernel, one MIPS16 function disassembled with four internal consistency points. Also the one row `isa-probe.sh` probes and §6's committed table has no line for -- 20 probes against 19 table rows |
| `lwl` | . | y | y | `CPU-15`, `CPU-16` | — | this unit's kernel `memcpy` uses it from `0x80002464`, and `do_ri` has no ULS emulation at all, so a MISSING `lwl` would reach `die_if_kernel`. What route 2 cannot see is a wrong VALUE, and `CPU-15` names the closer: one `lwl` under a handler of ours |
| `lwr` | . | y | y | `CPU-15`, `CPU-16` | — | the other half of the idiom pair; 82 of the 101 pairs in this kernel's `.text` are `lwl`/`lwr` |
| `mflxc0` | . | y | y | — | — | COP0's opcode 0x10 with `rs` 3, which MIPS leaves unassigned -- a THIRD coprocessor register file, and `docs/interrupt-map.md` § 1.1 says in terms that the 2026-08-29 CP3 result must not be carried over to it. 量 2026-09-12: 30 in this unit's decompressed vendor kernel and 14 in each of two images of mine that have booted. Route 2 is sound here for a reason the `movz` row did not have: `arch/rlx` reaches them on every irq-save path, so a trap would stop the kernel dead |
| `movn` | . | y | y | `CPU-17` | — | as `movz` |
| `movz` | . | y | y | `CPU-17` | — | 18 in the loader program area, two of them inside `check_image()`, which runs on every boot, with no exception message in 18 captures. §17's blank for this row is exactly route 2's blind spot: implemented, or silently emulated |
| `mtc3` | . | y | y | `CPU-46` | — | four `mtc3` at `0x8000227C`-`0x800022E8` set the IMEM/DMEM windows at boot. CP3's READ side is route 1 and its WRITE side is this one, which is the sharpest pair in the table |
| `mtlxc0` | . | y | y | — | — | the write side, `rs` 7. 量 2026-09-12: 6 in the vendor kernel and 6 in each booted image of mine. ⚠️ The scan is over 4-byte words with no section filter and its NEGATIVE CONTROL FIRED: 3 MiB of /dev/urandom gives 356-411 of each shape, because the random rate is 1 in 2,048 words -- so the 112/133 read off the COMPRESSED vendor kernel is noise and not a reading. A section-filtered count is what would make this clean |
| `swl` | . | y | y | `CPU-15`, `CPU-16` | — | 19 of the 101 pairs are `swl`/`swr` |
| `swr` | . | y | y | `CPU-15`, `CPU-16` | — | as `swl` |
| `COP1` | . | . | y | `CPU-47` | — | one `COP1` word in this kernel's text, adjudicated into a non-code island. §1 of `notes/vendor-kernel-isa.md` says in terms that every piece of evidence here is about EMULATION and none of it is evidence about the core: `Status.CU1` on the device is what decides it, and that read has never been taken |
| `SPECIAL2` | . | . | y | `CPU-18` | — | opcode 0x1C as a group: zero in the loader program area, by three independent decoders |
| `SPECIAL3` | . | . | y | `CPU-18` | — | opcode 0x1F as a group: zero in the loader program area |
| `beql` | . | . | y | `CPU-18` | — | branch-likely: zero in the loader, and the assembler rejects it for every RLX column while accepting it for `mips2` |
| `bgtzl` | . | . | y | `CPU-18` | — | as `bnel` |
| `blezl` | . | . | y | `CPU-18` | — | as `bnel` |
| `bnel` | . | . | y | `CPU-18` | — | branch-likely, zero in the loader, and NOT probed by the assembler instrument at all -- `isa-probe.sh` asks about `beql` alone, so this row's route 3 is one source where `beql`'s is two |
| `ldc1` | . | . | y | `CPU-47` | — | two `ldc1` words in this kernel's text, both inside the same adjudicated non-code island as the `COP1` |
| `ll` | . | . | y | `CPU-18`, `CPU-47` | — | the row the plan calls the most important one, because it decides libc. Route 2 is empty BY CONSTRUCTION: `ARCH_CPU_LLSC=n`, so zero in the loader and zero in 2.85 MB of kernel text, and nothing on this die has ever executed one. And the two vendor sources DISAGREE -- the assembler accepts it for `rlx4181` |
| `lwc1` | . | . | y | `CPU-47` | — | zero in this kernel's text; accepted in all eight assembler columns, which discriminates nothing |
| `lwc3` | . | . | y | `CPU-47` | — | accepted in all eight assembler columns, non-discriminating in exactly the way the ULS row is; 量 zero occurrences in `stage2.bin` or in any payload |
| `madd` | . | . | y | `CPU-18` | — | SPECIAL2 form: rejected in all eight assembler columns, zero in the loader. 🔴 2026-09-12: that rejection is a SPELLING and not the encoding. The public Lexra patch gives `mad` -- the same word 0x70000000 -- membership RLXA, all six Lexra cores, and leaves `madd` at I32. So a payload for this row must emit the WORD or it measures the assembler's dictionary. `docs/toolchain-prior-art.md` section 7 item 5 |
| `mfc1` | . | . | y | `CPU-47` | — | accepted in all eight assembler columns; zero in the loader |
| `pref` | . | . | y | `CPU-18` | — | rejected in all eight assembler columns, zero in the loader. Its opcode 0x33 was mislabelled `pref` in `hazlint` until 2026-08-27, when it was re-levelled to MIPS-I `lwc3` |
| `rdhwr` | . | . | y | `CPU-18`, `CPU-47` | — | rejected in all eight assembler columns, and the vendor `#if 0`'d both `simulate_rdhwr` call sites that mainline calls unconditionally |
| `sc` | . | . | y | `CPU-18`, `CPU-47` | — | as `ll` |
| `sdc1` | . | . | y | `CPU-47` | — | zero in this kernel's text |
| `swc1` | . | . | y | `CPU-47` | — | zero in this kernel's text |
| `swc3` | . | . | y | `CPU-47` | — | as `lwc3`, and not probed by the assembler at all |
| `sync` | . | . | y | `CPU-18`, `CPU-47` | — | the ONE row where this project's two-source rule is actually met: the assembler rejects it for `rlx4181` and accepts it for `rlx5281`, which is the same split the board configs make with `ARCH_CPU_SYNC` |
| `COP2` | . | . | . | — | — | `hazlint`'s own comment declares this a gap rather than closing it: MIPS-I A 8.3.3 makes coprocessor 2 optional in the same words as coprocessor 3, and nothing in this repository has looked for CP2 on this part |
| `teq` | . | . | . | — | — | MIPS-II trap instruction. Not in `CPU-18`'s scan list, not probed by `isa-probe.sh`, absent from §6's table: no evidence of any class exists for this row |
| `tge` | . | . | . | — | — | as `teq` |
| `tgeu` | . | . | . | — | — | as `teq` |
| `tlt` | . | . | . | — | — | as `teq` |
| `tltu` | . | . | . | — | — | as `teq` |
| `tne` | . | . | . | — | — | as `teq` |
<!-- isacensus:r1a end -->

---

## 4. `R1b` — the hazard rows

<!-- isacensus:r1b begin -->
| row | ① | ② | ③ | `SPEC.md` | reading taken at | what is still open |
|---|:-:|:-:|:-:|---|---|---|
| `load then a reader of the loaded register` | y | . | y | `CPU-14` | `upstream/` | exposed, no interlock. The ONLY route-1 hazard reading this project holds, and it is not this repository's: the single-variable experiment is upstream's `P9-12`, `upstream/BENCH-LOG.md` `T-89`/`T-90`, on the same physical device |
| `mtc0 then mfc0` | . | y | y | `CPU-30`, `CPU-31` | — | three sites in the loader, the first of them a `Status` write read back immediately, running on every boot. `CPU-31` states the limit: countable is not decidable |
| `mult/div then mfhi/mflo` | . | y | y | `CPU-29`, `CPU-31` | — | 16 sites in the loader with no `nop` between them, running on every boot. `CPU-31`: the count is equally consistent with an interlocked core and with an interlocked core where those sites are bugs |
| `a load sitting in a delay slot` | . | . | y | — | — | 量 zero of `stage2.bin`'s 1,474 loads sit in any delay slot, so the vendor code offers no site at all and this is a payload-only question. `hazlint` reports `unresolved` for an unresolvable target rather than checking the wrong word |
| `movz or movn write-enable in a load delay slot` | . | . | y | `TC-h`, `TC-22` | — | nothing that has run on this die exercises the shape, and that is 量 rather than inherited: the VENDOR's artefacts hold ZERO sites (this kernel 0 of 3,183 conditional moves, `boa` 0, `busybox` 0, `stage2.bin` 0), and `hazlint` on three images of mine that HAVE booted -- r59 with seventeen boots, `R3`'s `loudm` and `quietm` -- reports 0 violations in 112,505 / 111,801 / 109,922 loads, because `config/rlxfw-cflags`'s `-fno-if-conversion` removes the sites and `hazlint` is a build gate. `TC-22`'s four are in a FLAGLESS build. § 10 ④ is this file getting that wrong and being corrected |
| `store, the class hazlint has no rule for` | . | . | . | — | — | no instrument in this repository has counted a store hazard shape, and the shape itself is unspecified. Specifying it is the first thing `R1-pub-2` has to do, before any payload |
<!-- isacensus:r1b end -->

---

## 5. What `R1d` and `R1e` already closed, so that `R1a` does not re-measure it

These are not population rows — none of them is an instruction whose existence
is in question — and they are here because a census that re-measured them and
presented the total as new work would be exactly the résumé failure this
project keeps naming. All 量, all on this die.

| | what it settled | where | seating |
|---|---|---|---|
| `CPU-36` | the core **ignores** `mfc0`'s bits 2:0 — there is no select field. 256 stubs, `moves = 8` and all eight are rd 1 | `SPEC.md` | `bench/2026-08-25b` |
| `CPU-37` | reading an unimplemented CP0 register returns 0 and does **not** trap. `traps = 0` on all 256 rows | `SPEC.md` | `bench/2026-08-25b` |
| `CPU-38` | `mfc0` **always** writes its destination. `nowrite = 0` on all 256 rows, each read twice with a different prime — this is the row that makes every other zero a real zero | `SPEC.md` | `bench/2026-08-25b` |
| `CPU-41` | `rfe` pops the KU/IE stack correctly, `status_end == status` bit for bit | `SPEC.md` | `bench/2026-08-25b` |
| `CPU-42` | CP0 `Count`(9) and `Compare`(11) are **not implemented**, `count.delta = 0` over 100,000 iterations. This is what kills `R1c`'s original ruler — see § 9 | `SPEC.md` | `bench/2026-08-25b` |
| `CPU-25` | I-cache 16 KiB, 16-byte lines, **2-way**, by two independent routes — a geometry walk and the shape of the eviction walk's victims | `SPEC.md` | `bench/2026-08-31c` |
| `CPU-19` | `CCTL 0x002` alone makes a rewritten instruction visible; the cache-management model | `notes/cache-model.md` | `bench/2026-08-25` |
| `CPU-39` | CP0 20 is a write-only command register that reads zero | `SPEC.md` | `bench/2026-08-25` + `-25b` |

⚠️ One of them is a **constraint on `R1a`'s payload** rather than a result:
`CPU-38` is what licenses reading a zero as a zero. Any `R1a` row that reports
*does not trap and the value is 0* rests on it, and it must be cited rather
than assumed, because the `S_NOWRITE` state it excluded was invented for
exactly that purpose.

---

## 6. 🔴 The honest answer to the scope question

The step's refutation condition, written before this census ran:

> if `R1-pub-0` finds that the rows this repository already holds cover most of
> the census, the gate is **re-scoped in the open before a payload is
> written**, not padded out to 20 段.

**It did not fire, and here is the number that would have fired it.**

* On route ①, the route `R1a` and `R1b` actually measure: **3 of 45 rows**
  (6.7 %) have a reading. Two of the three are `cache` and `mfc3`, which came
  free inside `probe3` because it needed them for other cells; the third is the
  load hazard, and it is **upstream's reading, not this repository's**.
* Counting any evidence at all: **37 of 45 rows** (82.2 %) have something, and
  only 8 have nothing. **A reader who defines *already measured* that way is
  entitled to say this gate is mostly done, and that reading has to be answered
  rather than ignored.**

The answer is § 2.1, and it is a measurement rather than an argument: 22 of
those 37 rows are route ③, which is *what Realtek's toolchain believes*, and
§ 6 of `notes/vendor-kernel-isa.md` records the two vendor sources **flatly
disagreeing** about `ll`/`sc` — the single row the plan calls the most
important, because it decides libc. A table built on route ③ contains a
contradiction it cannot resolve. The remaining 12 are route ②, where the first
half of the question is settled and the third verdict cell is untouched.

🔴 **And the gate does not shrink in 段 either, which is the part that would
have been convenient to get wrong.** What the census changes, item by item:

| | change | direction |
|---|---|---|
| ③'s reserved-opcode control | **already exists and has fired on this die** — § 8 | one instrument fewer |
| `R1b`'s store row | its **shape is unspecified**, by no instrument, and the plan does not name the task | one design task more |
| `R1c`'s ruler | decided here, § 9, from readings already taken | no change to the step count |
| the `movz` delay-slot precondition | **answered, and the answer is the negative one** — § 10 ④ | no change to the step count; the row stays route ③ |

One instrument fewer and one design task more is not a re-scope. **The
calibrated band stays at 7–28 段 with a median of 17, and claiming a shrink on
this evidence would be unearned.**

⚠️ **A second accounting exists and it disagrees with both numbers above, which
is why it is stated rather than left to be found.** `SPEC.md` § 17 is the owner
of *every blank and what fills it*, and it says `R1a` and `R1b` owe exactly
**four** rows — `CPU-15` (`lwl` on the silicon), `CPU-17` (`movz` implemented
or silently emulated), `CPU-31` (the `HI`/`LO` and CP0 hazard rules) and `TC-h`
(`movz` write-enable in a delay slot). Forty-five population rows against four
blanks. The difference is not a defect in either file: § 17 counts the rows
whose *answers* `SPEC.md` is missing, and this file counts the rows a *payload
must carry*. The 41 rows in the gap are ones `SPEC.md` already considers
answered, on routes ② and ③.

> **Which means the four `SPEC.md` blanks are the gate's deliverable and the
> other 41 rows are its evidence.** That is the sentence a hostile reader
> should be handed first, and it did not exist before this census.

---

## 7. Decision ② — the seating schedule

The step list requires this in writing rather than discovered at the bench:

> `R1-pub` needs **bare metal**, and bare metal now competes with a board that
> boots my firmware. Every seating from 11 to 20 has been Linux.

**They do not compete, and that is measured on both sides.**

| | how a boot hands the board back to the loader | evidence |
|---|---|---|
| a bare-metal payload | its own watchdog bite — `rlx_reset` drains the UART, writes `WDTCNR = 0` and spins | 量, three payload generations, `probe1`/`probe2`/`probe3` |
| a Linux boot | `busybox reboot -f`, **2.407 s** to the loader prompt. `bsp_machine_restart` is itself `WDTCNR = 0` then spin, so it is the same mechanism | 量 `SPEC.md` `FW-37`; 讀 for the mechanism |

So one seating holds both, and the only question is the order.

🔴 **The order is fixed by a reading nobody took it for: the loader knows
whether it was reset or powered on.** It prints `Reboot Result from Watchdog
Timeout!` after every watchdog reset and never after a cold power-on (量; and
that line had been on disk since 2026-08-24 with nothing reading it). So the
**first** boot of a seating is not the same machine as any later one, and
whichever half of the seating cares about *the machine as only the loader has
set it* must have it.

The bare-metal half cares and the Linux half does not:

* `CLK-17` measured `TC0CNT` at **14,286,057 Hz at the loader prompt** and
  **200,005 Hz under Linux** — Linux reprograms `CDBR`, a **71.4×** change to
  the clock every bare-metal timing cell is taken against. 量.
* Linux also reprograms the cache, the interrupt controller and the watchdog
  (量 `WDT-1`, `IRQ-13`, `REG-35`), and a watchdog reset is not a power-on
  reset. That the loader's own init undoes all of it is **推**, and a payload's
  readings should not rest on 推 when the cold slot is free.

**Decision, for `R1-pub-3`'s seating:**

| slot | what runs | why it is there |
|---|---|---|
| **1 (cold)** | `R1a`'s payload, then `R1b`'s payload, each returning to the loader by its own bite | the only boot whose machine state no kernel has touched |
| **1 (cold), free** | the loop's `S2` → `S7` seam | 量 `notes/dev-loop.md` § 10.6: **no additional power cycle**, ~39 s of board idle, and it rides the opening cold boot |
| **2** | `CPU-45`'s cells A–G | needs one power cycle of its own by its stop-loss, and `bench/2026-08-30`'s round came back `c-A` negative with B/C/D/F/G void, so this is the allowed second attempt |
| **3** | `J` to a kernel of mine | after this the loader is gone for that boot; `reboot -f` is the way back |
| **4** | `FW-65`'s two `echo` writes bracketing one long hold | one boot, both arms on it |
| **5** | `FW-63`'s bit-6 transition timestamps, on a **fresh** boot | 🔴 `FW-62`: the vendor's `rtl_gpio_timer` acts **once per boot**, so a hold that consumed it in slot 4 leaves slot 5 with nothing to time |

⚠️ **Slots 3–5 cost no power cycle**: `reboot -f` is 2.407 s, so the Linux half
is three boots for the price of one seating. The two carried-forward residuals
therefore ride `R1-pub-3` at zero marginal cost, which is what the owner's
decision of 2026-09-12 selected.

🔴 **One thing this schedule does not solve**: `R1-pub-3`'s own stop-loss allows
**no more than two seatings**, and the table above already spends the second on
`CPU-45`. If `R1a`'s or `R1b`'s payload needs a re-run, `CPU-45` is what gives
way — written down now, because at the bench it would be decided by whichever
was on the card.

---

## 8. Decision ③ — the negative controls, and one of them has already fired on this die

The plan states this requirement in the strongest terms it uses anywhere: *a
reserved opcode must trap, and every hazard test must be shown able to produce
the wrong answer; any negative control that does not fire voids the whole
table.* `R1-pub-0` has to decide what those controls are, not defer them.

🟢 **The first one already exists, and it has fired on this die.** 量
2026-08-29, `bench/2026-08-30/QJ.log`, `probe3` cell `x-ri`:

```
rlxprobe: x ri ISSUING
rlxprobe: x ri n=00000001 cause=00000028 epc=80501874 dw=00000000
```

`0x28 >> 2 & 0x1F = 0x0A` — ExcCode 10, Reserved Instruction. The encoding is
`0x0000000E`, SPECIAL with function `0x0E`. One exception, and the payload
continued, so the handler returned.

🟢 **Its inverse control is in the same capture and on the same boot**, which
is what makes *no trap* a reading rather than a broken handler: `x c11`,
`x c10`, `x c15`, `x c19` — the four `cache` op values — all came back
`n=00000000`.

⚠️ **What that reading is, precisely.** It establishes that **an encoding
exists which traps on this die, and that the RI path through our own handler
works end to end**. It does **not** establish that `0x0000000E` is
architecturally reserved: `docs/probe3-cells.md`'s row for the cell records
留白 against exactly that, because no Lexra ISA document exists in this
repository and the RTL8196E datasheet's *"Supports MIPS-1 ISA, MIPS16 ISA"*
cannot be read as *"therefore everything else is reserved"* — MIPS16 needs
`JALX` at opcode `0x1D`. The control's job is to prove the instrument, and for
that the die's behaviour is the whole requirement.

**Decision, the ~~three~~ **FOUR** controls `R1-pub-1` through `-3` carry:** 🔄 **2026-09-13: corrected in place.** The caption said *three* and the table below it has always listed four; `R1-pub-1` implemented all four and the count was read off the table rather than off this line, so the prose was wrong and harmless until somebody quoted it.

| | control | what it proves | precedent |
|---|---|---|---|
| **C1** | `break` | the handler is reached and returns | 量 `bench/2026-08-25b`, `break.count=1`, `cause=00000024` (ExcCode 9), `restore.mismatch=0` |
| **C2** | `0x0000000E` | the **RI** path specifically, not just any exception | 量 `bench/2026-08-30`, above. Re-run rather than quoted, because it costs one cell |
| **C3** | four `cache` op values | a `n=0` verdict is a reading and not a dead handler | 量 same capture, same boot |
| **C4** | every `R1b` row under **qemu** | the *interlocked* arm. qemu interlocks the load delay slot, so a hazard test that returns the same value on both machines has not measured a hazard | 量 `probe1` cell 1 came back STALE on the die and FRESH under qemu — the opposite answer, which is the shape this demands |

🔴 **C4 is the one with a trap in it, and it is `probe1`'s own lesson
inverted.** *A device run that looks like the qemu run is the run that refutes
the experiment, not the one that confirms it.* For `R1b` that means the qemu leg
must be run and recorded **before** the device leg, so the expected difference
is on paper rather than reconstructed afterwards.

⚠️ **And C4 does not cover the store row**, because that row has no shape yet
(§ 4). A control cannot be written for an experiment that has not been
specified, and the step table's *not measurable is a legal recorded outcome* is
what that row will use if `R1-pub-2` cannot specify it.

---

## 9. `R1c`'s ruler, now that `CPU-42` killed CP0 `Count`

`R1c` is the same table run again as a Linux userspace program under the
**vendor** kernel, and its deliverable is the two-column diff — the emulation
surface — *with each difference's cost measured*. A cost needs a clock, and the
plan's clock does not exist on this part: `CPU-42` is 量, CP0 `Count` reads
`00000000` and `count.delta = 0` over 100,000 iterations.

Three candidates, and two of them are refuted by readings already taken:

| | candidate | verdict |
|---|---|---|
| ① | `gettimeofday` | 🔴 **refuted.** The system's clock**source** is still `jiffies` — `rating` read **0** in all eleven dumps of seating 14 and the clocksource half of `R5` is untouched by design. That is 10 ms granularity, 量 |
| ② | TC1, my own clockevent's counter | 🔴 **refuted as the primary ruler.** Its reload is the system tick. 量: at reload 20000 a `sleep 5` took **50 real seconds** and nothing in the kernel could notice. The ruler and the scheduler would be the same device |
| ③ | **`jiffies` for the wraps, `TC0CNT` for the sub-tick residue** | 🟢 **chosen** |

**Why ③, in measured terms.** TC0 is the vendor's timer, it is free-running,
and nothing of mine writes it — 量 seating 13: over 30.10 real seconds the
vendor's line 13 advanced 3,009 while my line 25 advanced 301, so TC0 is still
at 100 Hz with my clockevent driving the tick. Under Linux it counts at
**200,005 Hz** (量 `CLK-17`) with `TC0DATA` reloading at **2,000** (量), so it
wraps every 10.0 ms and `jiffies × 2000 + TC0CNT` is a monotonic clock with
**5 µs** resolution and zero effect on the system.

🟢 **And the composition carries its own cross-check, which is why it is worth
the arithmetic.** `Δjiffies`, `Δirq_count` and `Δce_cycles ÷ 2000` were
measured equal to **26,373** three ways over 263.73 s, and again to **65,476**
over 654.76 s, both with residual 0. So a `R1c` interval computed from
`jiffies` and `TC0CNT` can be checked against TC1's cycle count on the same
interval, and a disagreement is visible rather than silently absorbed.

⚠️ **Two things this decision leaves open, stated rather than left to be
found.** ① The **amplification factor** is 推: an emulated instruction costs an
exception round trip through `do_ri` — microseconds — and a native one costs
nanoseconds, so N must be chosen per row so the total clears ~100 counts, and
the first cell of `R1-pub-4` measures the empty loop as its own control.
② Reaching `TC0CNT` from userspace needs `/dev/mem` or a `/proc` file, and
which one is `R1-pub-4`'s decision, not this one — but it is **not** a new
driver: `rtl819x-timer` already exposes its own counters.

---

## 10. 🔴 What this census found that was on nobody's list

Six things, each of which existed in this repository before tonight and was
not joined up.

**① The mandatory negative control was already measured, and the document that
owns the cell says 留白 in a column that means something else.** § 8. The
reading is recorded — `docs/probe3-cells.md` and `docs/rlx-cache-and-cp0.md`
both carry the `epc=80501874` line — but nothing had ever said *this is `R1a`'s
control and it has fired*. The first draft of this file called the 留白 a
defect; reading the table's header first is what stopped that, and the
distinction it turns on is worth keeping: the die's behaviour is 量, and *that
the encoding is architecturally reserved* has no source at all.

**② `isa-probe.sh` probes 20 mnemonics and § 6's committed table has 19 rows.**
量 2026-09-12, both directions: the missing one is `jalx`, and the reverse
difference is empty. It matters because `CPU-09`/`CPU-48` establish that this
kernel *runs* MIPS16 code on this die, so the assembler's answer for `jalx` is
worth having — and it is the same non-discriminating shape as the ULS row,
accepted in all eight columns including `mips1`, which is precisely why § 6
warns that the ULS row proves nothing.

**③ Six rows have no evidence of any class, and they are all the same family.**
`teq`, `tge`, `tgeu`, `tlt`, `tltu`, `tne` — the MIPS-II trap instructions. Not
in `CPU-18`'s scan list, not probed by `isa-probe.sh`, absent from § 6's table.
They are on `hazlint`'s watch list and nothing else in this repository has ever
mentioned them.

**④ 🔴🔴 One `R1b` row was classified route ② in this file's own first
version, that was WRONG, and the correction is here rather than in the history
because it is the most instructive thing in the census.**

The first version reasoned: `SPEC.md` `TC-22` says a build of this project's
holds four sites of the shape *conditional move in a load delay slot, rd = the
loaded register*, and `notes/kernel-build.md` § 1.2 marks **two of them on `R3`'s
boot path** — `__add_preferred_console`, reached because that build's
`CONFIG_CMDLINE` carries `console=ttyS0,38400`, and `load_elf_binary`, reached on
every `execve`. `R3`'s kernel has booted on this die. Therefore the shape has
executed here.

**Every clause of that is true and the conclusion is false.** 量 2026-09-12,
`hazlint` on three images of this project's that have actually booted:

| image | loads | load-use violations |
|---|---:|---:|
| `r59`, the seventeen-boot image of seating 20 | 112,505 | **0** |
| `R3`'s `loudm`, booted 2026-08-29 | 111,801 | **0** |
| `R3`'s `quietm`, booted 2026-08-30 | 109,922 | **0** |

`TC-22`'s four sites **are** load-use violations — § 1.2 of
`notes/kernel-build.md` is titled *The four violations are one shape* — so an
image with zero of them contains none of the four. `config/rlxfw-cflags` is the
file that settles why: every image `rlxfw-kbuild.sh` builds carries
`-fno-if-conversion`, which removes 98.8 % of this gcc's conditional moves
(2,597 → 31) and takes `hazlint` from seven violations to zero, and **`hazlint`
is a build gate**, so an image carrying them could not have been produced.
`TC-22`'s four are in a **flagless** build that has never been on the device.

🔴 **So `notes/kernel-build.md` § 1.2's own sentence — *"the sites my chosen
toolchain produces **would be** the first code of this shape to execute on this
silicon"* — is right, and has been right since it was written on
2026-08-28.** The row is route ③ and the table says so.

⚠️ **Why this is worth the space.** The error was not a missing measurement; the
measurement took three minutes and was available the whole time. It was **reading
a count out of one file and supplying the conclusion myself**, without reading
the owner file's own next sentence, which is in the future tense, and without
opening `config/rlxfw-cflags` at all. `CLAUDE.md`'s standing hazard is *quoting a
partial view instead of re-deriving*; this is that hazard applied to a
**conclusion** rather than to a number, which is the harder form to see, because
a number that looks wrong invites a check and a conclusion that looks sharp does
not.

🟢 **And it is what the second round of the closeout audit is for.** The gates
were green over the pushed file; the question *"is everything that should have
been written, written?"* is what sent a reader back into
`notes/kernel-build.md`, and the sentence two paragraphs past the table is where
the answer was.

**⑤ A count taken one way was wrong by one, in the direction that reads as more
coverage.** `grep -c '^row ' tools/isa-probe.sh` returns **21**; the file
probes **20**. The extra is the shell function *definition*, `row () { # label
insn`. It was caught only because the same quantity was counted a second way
and the members were listed — and the rule it instances is
`CLAUDE.md`'s: ask an instrument what its atomic unit is, and count a
quantity in two units before quoting it. `isacensus.py`'s probe-row regex has
that shape for this reason, and `--self-test` `T12` is the control: an
`isa-probe.sh` whose only `row` line is the definition must make the tool
**refuse**, not report a population of zero.

**⑥ 🔴 Two rows are missing from the derived population, and the audit put them
there by hand.** `mflxc0` and `mtlxc0` are COP0's opcode `0x10` with `rs` 3 and
7 — encodings MIPS leaves unassigned, reaching a **third** coprocessor register
file that `docs/interrupt-map.md` § 1.1 warns must not be confused with the CP3
this project measured on 2026-08-29. They are in neither `hazlint`'s tables nor
`isa-probe.sh`'s rows, so **the derivation cannot see them**, and § 1's whole
argument is that a derived population beats a chosen one. It does — and this is
the price: what the instruments do not know about is invisible, and only a
complete enumeration of the tracked `.md` found it.

量 2026-09-12, with a negative control that fired and a positive one that held:

| artefact | `mfc0` rs 0 | **`mflxc0` rs 3** | `mtc0` rs 4 | **`mtlxc0` rs 7** |
|---|---:|---:|---:|---:|
| this unit's decompressed vendor kernel | 6,390 | **30** | 6,264 | **6** |
| `r59` `vmlinux`, seventeen boots | 5,235 | **14** | 5,176 | **6** |
| `R3`'s `loudm`, booted 2026-08-29 | 5,064 | **14** | 5,006 | **6** |
| 🔴 NEG: 3 MiB of `/dev/urandom` | 411 | 356 | 372 | 377 |

🔴 **The negative control's own prediction was wrong by four hundred times** —
it said random data would give essentially zero, and the rate is **1 in 2,048
words**, so ~384 of each shape per 3 MiB. The `mfc0`/`mtc0` columns are the
positive control and they hold far above it. **The consequence is a rule**: the
same scan over the *compressed* `r0-vendor-kernel.bin` returns 114/112/111/133,
which is exactly its random rate and is **not a reading**.

They are route ② rows, and here the justification route ② needed for the `movz`
row in ④ is available: `arch/rlx` reaches these on every irq-save path, so a
trap would stop the kernel dead rather than produce a wrong value — and both
encodings are counted in two images that have booted. ⚠️ The count has **no
section filter**, which is what would make it clean.

---

## What could still be wrong

* 🔴 **The population is as good as its two instruments, and this is not
  hypothetical: it fired on the first day.** If a Lexra ASE operation is in
  neither `hazlint`'s watch list nor `isa-probe.sh`'s rows, it has no row here —
  and `mflxc0`/`mtlxc0` were exactly that, added as declared rows by the
  closeout audit (§ 10 ⑥) rather than by the derivation. **`x-ri`'s own comment
  already names this as the way that cell could retire**, so the gap is known,
  it is now measured once, and it is not closed.
  🔄 **2026-09-12, the next segment: the size of that gap is measured and it is
  14, not "more than a hundred."** This bullet's original wording — *the
  binutils Lexra patch adds more than a hundred proprietary mnemonics to these
  cores and this project has not downloaded it* — traced to `SOURCES.json`'s
  description of the patch and was a **read count, never a count**. 量, the
  patch downloaded: **148** new mnemonics over two opcode files, of which
  **16** are claimed for `RLX4181` by the patch's own membership words and
  **14** are new to this repository (`mflxc0` and `mtlxc0` being the two § 10 ⑥
  already added). The other 132 are gated on flags that exclude `INSN_4181` —
  the RADIAX set, claimed for 5181/5280/5281 — so they are **not a statement
  about this core**. The fourteen are `ltw`, `madh`, `madl`, `mazh`, `mazl`,
  `msbh`, `msbl`, `mszh`, `mszl`, `sleep`, `udi0i`, `udi1i`, `udi2i`, `udi3i`.
  ⚠️ They are deliberately **not** added to this census: it was frozen with an
  ordering property, and growing its population by 36 % on evidence from the
  toolchain axis would muddy the only thing that makes it worth anything.
  ~~Whether they become `R1a` payload rows is `R1-pub-1`'s decision, and the
  number it needs now exists.~~ 🔄 **2026-09-13: the decision is made and it is THIRTEEN of the fourteen.** `probe4` carries `madh` `madl` `mazh` `mazl` `msbh` `msbl` `mszh` `mszl` `ltw` `udi0i` `udi1i` `udi2i` `udi3i`, plus six more the same patch adds (`udi0`..`udi5`) that this list did not name. **`sleep` is excluded by name**: a bare-metal payload that sleeps does not come back. 🔴 **And the encodings are NOT the ones a reader would take from the mnemonics** -- the eight MAC names appear twice in that patch, once at 16-bit encodings in `mips16-opc.c` (mask `0xf81f`) and once at 32-bit in `mips-opc.c` (mask `0xFC00FFFF`), and only the second set is what a 32-bit payload can issue. This census is still not grown: the rows live in `tools/isa-payload.tsv` and `isapay population` joins the two in both directions. `SPEC.md` `CPU-50`, `docs/isa-payload.md` § 9. `docs/toolchain-prior-art.md` § 7 ⑦.
* **Route ② rests on *no exception message in a capture*.** That is an absence,
  and an absence in a capture is only as strong as the capture's coverage.
  `SPEC.md` `CPU-17` says eighteen captures; `FW-41` and `FW-47` measured two
  separate ways a mark the board printed can be missing from a `grep`.
* **The adjudication is a judgement.** `isacensus check` verifies that every
  derived row is present, that no row is invented, that every cited `SPEC.md`
  id exists, and that a seating is named only where there is a route-① reading.
  It does **not** verify that a `y` in column ② is the right call for that row.
  Nine mutation controls fire on the checkable half; the judgement half is a
  person's, and it is this file.
* **`R2c`'s prior art is not in this census** and the gate's step list caps
  `R2c` at 2 段. `notes/vendor-toolchains.md` and `SPEC.md` § 14 already hold a
  great deal of it — `TC-15`, `TC-19`, `TC-22`, `TC-23` are all 讀 and all
  about the toolchains. A census of that is the same shape as this one and it
  has not been done, which is a stated risk to the cap rather than a
  deferral without a reason.
