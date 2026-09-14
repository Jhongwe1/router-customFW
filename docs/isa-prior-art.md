# What this repository already holds about this core's ISA

**`R1-pub-0`, desk, 2026-09-12. No power, no payload source, no device
reading.**

🔄 **2026-09-14: the route ① column has moved, and the dateline above stays
because the freeze is what makes the rest of this file worth reading.** `R1a`'s
and `R1b`'s payloads ran on the silicon at seating 21
(`bench/2026-09-14/C1-P4j.log`, `bench/2026-09-14/C1-P5j.log`), and **37 of the
39 `R1a` rows and 5 of the 6 `R1b` rows now carry a route-① reading**, where 3
of 45 did at the freeze. The frozen figures are kept verbatim in § 6 and are
what the step's refutation condition was evaluated against; the ordering
property is unchanged and is still checkable the way the paragraph below says.
**What moved is one column, not the population**: every row's ② and ③ flags and
every prior-art sentence in its note are untouched, and where a note made a
present-tense claim the reading has expired, it is struck in place rather than
removed. The two `R1a` rows with no route-① reading are `jalx` and `mtlxc0`,
both excluded from the payload by name and for a stated reason.

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
| `R1a` instruction rows | 37 | 2 | 0 | 0 | **39** |
| `R1b` hazard rows | 5 | 1 | 0 | 0 | **6** |
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
| `COP1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | one `COP1` word in this kernel's text, adjudicated into a non-code island. §1 of `notes/vendor-kernel-isa.md` says in terms that every piece of evidence here is about EMULATION and none of it is evidence about the core: `Status.CU1` on the device is what decides it, and that read has never been taken. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): THE GROUP SPLITS ACROSS TWO EXCEPTIONS. `mfc1` `0x44020000`, `lwc1` `0xC5400000` and `swc1` `0xE5400000` all TRAPS `cause=1000002c` -- ExcCode 11 (CpU) with `CE` 1; `ldc1` `0xD5400000` and `sdc1` `0xF5400000` TRAPS `cause=10000028` -- ExcCode 10 (RI). So the three MIPS-I COP1 opcodes decode as coprocessor accesses and the two MIPS-II ones do not decode at all. ⚠️ `CU1` is NOT set by that payload (`tools/rlxprobe/cells4.S` says so at the `mfc1` word), so a CpU does not separate *no FPU* from *FPU disabled* -- the `Status.CU1` read named above is still the one that decides it, and it has still not been taken. `SPEC.md` `CPU-57` |
| `COP2` | y | . | . | `CPU-57` | `bench/2026-09-14` | `hazlint`'s own comment declares this a gap rather than closing it: MIPS-I A 8.3.3 makes coprocessor 2 optional in the same words as coprocessor 3, and ~~nothing in this repository has looked for CP2 on this part~~ 🔄 **something has**. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): `mfc2` `0x48020000` TRAPS -- `cause=2000002c`, ExcCode 11 (CpU) with the `Cause` `CE` field reading 2 -- so opcode 0x12 decodes as a coprocessor-2 access on this die. ⚠️ `Status.CU2` is not set by that payload, so this says the opcode is in the coprocessor CLASS and NOT that CP2 exists, which is the same limit the `COP1` row states. `SPEC.md` `CPU-57` |
| `SPECIAL2` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | opcode 0x1C as a group: zero in the loader program area, by three independent decoders. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): THE GROUP IS NOT UNIFORMLY ABSENT. `funct 0x00` (`madd`, `0x71090000`) is RIGHT on both halves -- `13526780` in LO and `0BAD0002` in HI, the carry `cells4.S` says a core adding the halves independently gets wrong -- while `funct 0x02` (`mul`), `0x20` (`clz`) and `0x21` (`clo`) all TRAPS `cause=00000028`, ExcCode 10 (RI). ⚠️ Which NAME the retiring word carries is a toolchain question and not a die one: the same word is Lexra `mad` in the public patch this table's `madd` row cites. `SPEC.md` `CPU-57` |
| `SPECIAL3` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | opcode 0x1F as a group: zero in the loader program area. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): opcode 0x1F is not implemented -- `ext` `0x7D023A00`, `ins` `0x7D027A04`, `seb` `0x7C091420` and `wsbh` `0x7C0910A0` all TRAPS `cause=30000028`, ExcCode 10 (RI), four of four. `SPEC.md` `CPU-57` |
| `beql` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | branch-likely: zero in the loader, and the assembler rejects it for every RLX column while accepting it for `mips2`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=30000028`, ExcCode 10 (RI), with the operands chosen so the branch would be TAKEN, so a retiring core could not have read as a trap. The route-3 prediction held, and all four of the family agree. `SPEC.md` `CPU-57` |
| `bgtzl` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | as `bnel`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=30000028`, ExcCode 10 (RI), with the operands chosen so the branch would be TAKEN, so a retiring core could not have read as a trap. The route-3 prediction held, and all four of the family agree. `SPEC.md` `CPU-57` |
| `blezl` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | as `bnel`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=30000028`, ExcCode 10 (RI), with the operands chosen so the branch would be TAKEN, so a retiring core could not have read as a trap. The route-3 prediction held, and all four of the family agree. `SPEC.md` `CPU-57` |
| `bnel` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | branch-likely, zero in the loader, and NOT probed by the assembler instrument at all -- `isa-probe.sh` asks about `beql` alone, so this row's route 3 is one source where `beql`'s is two. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=30000028`, ExcCode 10 (RI), with the operands chosen so the branch would be TAKEN, so a retiring core could not have read as a trap. The route-3 prediction held, and all four of the family agree. `SPEC.md` `CPU-57` |
| `cache` | y | y | y | `CPU-44` | `bench/2026-08-30` | retires, four op values (0x10 IInval, 0x11 DInval, 0x15 DWBInval, 0x19 DWB), n=0 on each. `x-c10`'s untreated twin moved too, so this is *retires* and not *invalidates*. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): a second payload on a second seating repeats it -- `cache10`/`cache11`/`cache15`/`cache19` all RAN, `n=0`, `cause=00000000`. `SPEC.md` `CPU-57` |
| `ldc1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | two `ldc1` words in this kernel's text, both inside the same adjudicated non-code island as the `COP1`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=10000028`, ExcCode 10 (RI) and not CpU, so opcode 0x35 does not decode as a coprocessor access on this die at all. `SPEC.md` `CPU-57` |
| `ll` | y | . | y | `CPU-18`, `CPU-47`, `CPU-57` | `bench/2026-09-14` | the row the plan calls the most important one, because it decides libc. Route 2 is empty BY CONSTRUCTION: `ARCH_CPU_LLSC=n`, so zero in the loader and zero in 2.85 MB of kernel text, ~~and nothing on this die has ever executed one~~ 🔄 **one has**. And the two vendor sources DISAGREE -- the assembler accepts it for `rlx4181`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `gpr 0000A5F0`, `n=0`, the constant written down before power. `tools/rlxprobe/cells4.S` records why that verdict discriminates: opcode 0x30 is `lwc0` on a MIPS-I decoder, and `lwc0` would leave the GPR at its `DEADBEEF` seed, which reads WRONG. ⚠️ It says the word retires and loads the right word and NOTHING about atomicity, so the two disagreeing vendor sources above are not adjudicated by it. `SPEC.md` `CPU-57` |
| `lwc1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | zero in this kernel's text; accepted in all eight assembler columns, which discriminates nothing. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=1000002c`, ExcCode 11 (CpU), `CE` 1. Same `CU1` caveat as the `COP1` row. `SPEC.md` `CPU-57` |
| `lwc3` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | accepted in all eight assembler columns, non-discriminating in exactly the way the ULS row is; 量 zero occurrences in `stage2.bin` or in any payload. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=3000002c`, ExcCode 11 (CpU), `CE` 3, so opcode 0x33 decodes as a coprocessor-3 load on this die. Read it beside the `pref` row, which is the SAME OPCODE with a different destination and got the same answer. `SPEC.md` `CPU-57` |
| `lwl` | y | y | y | `CPU-15`, `CPU-16` | `bench/2026-09-14` | this unit's kernel `memcpy` uses it from `0x80002464`, and `do_ri` has no ULS emulation at all, so a MISSING `lwl` would reach `die_if_kernel`. What route 2 cannot see is a wrong VALUE, and ~~`CPU-15` names the closer: one `lwl` under a handler of ours~~ 🔄 **that closer ran**. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `gpr A5F00D44` against the constant written down before power, `n=0`. `SPEC.md` `CPU-57` |
| `lwr` | y | y | y | `CPU-15`, `CPU-16` | `bench/2026-09-14` | the other half of the idiom pair; 82 of the 101 pairs in this kernel's `.text` are `lwl`/`lwr`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `gpr 1122335A`, `n=0`. `SPEC.md` `CPU-57` |
| `madd` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | SPECIAL2 form: rejected in all eight assembler columns, zero in the loader. 🔴 2026-09-12: that rejection is a SPELLING and not the encoding. The public Lexra patch gives `mad` -- the same word 0x70000000 -- membership RLXA, all six Lexra cores, and leaves `madd` at I32. So a payload for this row must emit the WORD or it measures the assembler's dictionary. `docs/toolchain-prior-art.md` section 7 item 5. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): the payload emitted the WORD as that sentence requires, and it is RIGHT on both halves -- LO `13526780` and HI `0BAD0002` against an accumulator primed to `0BAD0000F00D0000`, `n=0`. So SPECIAL2 `funct 0x00` retires and computes a 64-bit multiply-accumulate on this die. ⚠️ Which name that word carries is still the toolchain question stated above. `SPEC.md` `CPU-57` |
| `mfc1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | accepted in all eight assembler columns; zero in the loader. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=1000002c`, ExcCode 11 (CpU), `CE` 1. Same `CU1` caveat as the `COP1` row. `SPEC.md` `CPU-57` |
| `mfc3` | y | . | y | `CPU-46` | `bench/2026-08-30` | eight reads with `CU3` set and held, `m.traps=00000000`; under qemu all eight trap with ExcCode 0x0B, so the die and the emulator disagree about this row. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): THE MATCHED CONTROL ON THAT READING. The same word `0x4C020000` with `CU3` NOT set traps -- `cause=3000002c`, ExcCode 11 (CpU), and the `Cause` `CE` field reads 3, which names the coprocessor. So the 2026-08-30 retirement is the enable and not the decoder, and the die-vs-emulator disagreement narrows to the CU3-set case. `tools/rlxprobe/cells4.S` says this row is that control, in its own words, at the `0x4C020000` word. `SPEC.md` `CPU-57` |
| `mflxc0` | y | y | y | `CPU-57` | `bench/2026-09-14` | COP0's opcode 0x10 with `rs` 3, which MIPS leaves unassigned -- a THIRD coprocessor register file, and `docs/interrupt-map.md` § 1.1 says in terms that the 2026-08-29 CP3 result must not be carried over to it. 量 2026-09-12: 30 in this unit's decompressed vendor kernel and 14 in each of two images of mine that have booted. Route 2 is sound here for a reason the `movz` row did not have: `arch/rlx` reaches them on every irq-save path, so a trap would stop the kernel dead. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RAN -- `n=0`, `gpr 00000000` against a seed of `DEADBEEF`, so the destination was written and the encoding retires. Per `docs/isa-payload.md` § 0 a RAN says only that it did not trap. In the same capture the five real CP3 encodings all trap ExcCode 11, which is the 2026-09-04 correction -- these are not `mfc3` -- confirmed on the silicon. `SPEC.md` `CPU-57` |
| `movn` | y | y | y | `CPU-17` | `bench/2026-09-14` | as `movz`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `gpr 0000002A`, `n=0`. `SPEC.md` `CPU-57` |
| `movz` | y | y | y | `CPU-17` | `bench/2026-09-14` | 18 in the loader program area, two of them inside `check_image()`, which runs on every boot, with no exception message in 18 captures. ~~§17's blank for this row is exactly route 2's blind spot: implemented, or silently emulated~~ 🔄 **answered, and the answer is implemented**. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `gpr 0000002A`, and `n=0` means no exception was taken at all, so nothing could have emulated it. `SPEC.md` `CPU-57` |
| `mtc3` | y | y | y | `CPU-46` | `bench/2026-09-14` | four `mtc3` at `0x8000227C`-`0x800022E8` set the IMEM/DMEM windows at boot. CP3's READ side is route 1 and its WRITE side is this one, which is the sharpest pair in the table. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=3000002c`, ExcCode 11 (CpU), `CE` 3. ⚠️ `CU3` is not set by that payload, so this reads the ENABLE and not whether CP3 holds the register; the route-2 boot-time writes are unchanged and the pair still stands. `SPEC.md` `CPU-57` |
| `pref` | y | . | y | `CPU-18`, `CPU-57` | `bench/2026-09-14` | rejected in all eight assembler columns, zero in the loader. Its opcode 0x33 was mislabelled `pref` in `hazlint` until 2026-08-27, when it was re-levelled to MIPS-I `lwc3`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): THE SAME WORD IS TWO INSTRUCTIONS AND THE DIE NAMED WHICH. `0xCD400000` TRAPS with `cause=3000002c` -- ExcCode 11 (CpU) and the `Cause` `CE` field reading 3 -- so opcode 0x33 is the MIPS-I coprocessor-3 load on this part and not the MIPS32 `pref` hint, which would have retired. The 2026-08-27 re-levelling recorded above is confirmed on the silicon. `SPEC.md` `CPU-57` |
| `rdhwr` | y | . | y | `CPU-18`, `CPU-47`, `CPU-57` | `bench/2026-09-14` | rejected in all eight assembler columns, and the vendor `#if 0`'d both `simulate_rdhwr` call sites that mainline calls unconditionally. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=30000028`, ExcCode 10 (RI). The route-3 prediction held. `SPEC.md` `CPU-57` |
| `sc` | y | . | y | `CPU-18`, `CPU-47`, `CPU-57` | `bench/2026-09-14` | as `ll`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RAN -- `n=0`, and `m0` reads `5A5A0FF2`, which is `rt` (`$9`), where the scratch word had been `A5A5F00D`. Per `docs/isa-payload.md` § 0 a RAN is not evidence the core has `sc`. 推, on two sources: `cells4.S` says the MIPS-I reading of opcode 0x38 is `swc0`, which would have stored CP0 register 9, and `CPU-42` measured CP0 9 (`Count`) unimplemented and reading zero -- so the stored value is the GPR's and not CP0's. ⚠️ `$9` itself is not recorded, so whether an `sc` success/failure code was written back is untouched, and so is atomicity. `SPEC.md` `CPU-57` |
| `sdc1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | zero in this kernel's text. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=10000028`, ExcCode 10 (RI) and not CpU, so opcode 0x3D does not decode as a coprocessor access. `SPEC.md` `CPU-57` |
| `swc1` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | zero in this kernel's text. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=1000002c`, ExcCode 11 (CpU), `CE` 1, and `m0` is unchanged at `A5A5F00D` so no store happened. Same `CU1` caveat as the `COP1` row. `SPEC.md` `CPU-57` |
| `swc3` | y | . | y | `CPU-47`, `CPU-57` | `bench/2026-09-14` | as `lwc3`, and not probed by the assembler at all. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=3000002c`, ExcCode 11 (CpU), `CE` 3, `m0` unchanged at `A5A5F00D`. The PRE-REGISTERED qemu prediction for this row was ExcCode 0x0A, because 0x3B is unassigned at MIPS32; the die gives 0x0B, so on this part 0x3B is still the MIPS-I coprocessor-3 store. `SPEC.md` `CPU-57` |
| `swl` | y | y | y | `CPU-15`, `CPU-16` | `bench/2026-09-14` | 19 of the 101 pairs are `swl`/`swr`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `m0 A55A5A0F`, `n=0`. `SPEC.md` `CPU-57` |
| `swr` | y | y | y | `CPU-15`, `CPU-16` | `bench/2026-09-14` | as `swl`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): RIGHT -- `m0 5A0FF20D`, `n=0`. `SPEC.md` `CPU-57` |
| `sync` | y | . | y | `CPU-18`, `CPU-47`, `CPU-57` | `bench/2026-09-14` | the ONE row where this project's two-source rule is actually met: the assembler rejects it for `rlx4181` and accepts it for `rlx5281`, which is the same split the board configs make with `ARCH_CPU_SYNC`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=00000028`, ExcCode 10 (RI). The two agreeing vendor sources this row names both predicted that and the silicon is the third. `SPEC.md` `CPU-57` |
| `teq` | y | . | . | `CPU-57` | `bench/2026-09-14` | MIPS-II trap instruction. Not in `CPU-18`'s scan list, not probed by `isa-probe.sh`, absent from §6's table: ~~no evidence of any class exists for this row~~ 🔄 **that expired on 2026-09-14 at 05:39, and the answer is that this core does not have it**. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), with the operands chosen so the trap condition is TRUE, so ExcCode 13 was the reachable alternative and the die did not take it. `tools/rlxprobe/cells4.S` registered all three outcomes at this word before power: *13 if the core has them, 10 if it does not, and a retirement if neither*. `SPEC.md` `CPU-57` |
| `tge` | y | . | . | `CPU-57` | `bench/2026-09-14` | as `teq`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), condition TRUE. All six of the family agree, and the family is not implemented. `SPEC.md` `CPU-57` |
| `tgeu` | y | . | . | `CPU-57` | `bench/2026-09-14` | as `teq`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), condition TRUE. All six of the family agree, and the family is not implemented. `SPEC.md` `CPU-57` |
| `tlt` | y | . | . | `CPU-57` | `bench/2026-09-14` | as `teq`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), condition TRUE. All six of the family agree, and the family is not implemented. `SPEC.md` `CPU-57` |
| `tltu` | y | . | . | `CPU-57` | `bench/2026-09-14` | as `teq`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), condition TRUE. All six of the family agree, and the family is not implemented. `SPEC.md` `CPU-57` |
| `tne` | y | . | . | `CPU-57` | `bench/2026-09-14` | as `teq`. 🔄 量 2026-09-14 (seating 21, `probe4`, `bench/2026-09-14/C1-P4j.log`): TRAPS -- `cause=20000028`, ExcCode 10 (RI), condition TRUE. All six of the family agree, and the family is not implemented. `SPEC.md` `CPU-57` |
| `jalx` | . | y | y | `CPU-09`, `CPU-48` | — | 180 in-image targets in this unit's kernel, one MIPS16 function disassembled with four internal consistency points. Also the one row `isa-probe.sh` probes and §6's committed table has no line for -- 20 probes against 19 table rows. ⚠️ 2026-09-14 (seating 21): STILL NO READING, and the reason is structural. `jalx` has no row in `tools/isa-payload.tsv` at all -- `isapay`'s `DEFERRED_GROUPS` excludes it by name with the `mips16` group, because a retiring `jalx` lands control in MIPS16 mode at an address a 26-bit field chooses and this payload has no MIPS16 return path. With `mtlxc0` it is one of exactly two `r1a` rows seating 21 did not touch |
| `mtlxc0` | . | y | y | — | — | the write side, `rs` 7. 量 2026-09-12: 6 in the vendor kernel and 6 in each booted image of mine. ⚠️ The scan is over 4-byte words with no section filter and its NEGATIVE CONTROL FIRED: 3 MiB of /dev/urandom gives 356-411 of each shape, because the random rate is 1 in 2,048 words -- so the 112/133 read off the COMPRESSED vendor kernel is noise and not a reading. A section-filtered count is what would make this clean. ⚠️ 2026-09-14 (seating 21): STILL NO READING, and deliberately. `tools/isa-payload.tsv`'s `mflxc0` row states the exclusion in its own words -- writing an unidentified CP0 register on the one device this project has is not a measurement worth a board. With `jalx` it is one of exactly two `r1a` rows seating 21 did not touch |
<!-- isacensus:r1a end -->

---

## 4. `R1b` — the hazard rows

<!-- isacensus:r1b begin -->
| row | ① | ② | ③ | `SPEC.md` | reading taken at | what is still open |
|---|:-:|:-:|:-:|---|---|---|
| `a load sitting in a delay slot` | y | . | y | `CPU-54` | `bench/2026-09-14` | 量 zero of `stage2.bin`'s 1,474 loads sit in any delay slot, so the vendor code offers no site at all and ~~this is a payload-only question~~ 🔄 **a payload asked it**. `hazlint` reports `unresolved` for an unresolvable target rather than checking the wrong word. 2026-09-13: this is the ONE shape in BOTH of hazlint's channels, and its main-check record says `jump target of` where every other family's says `next word` -- which is what separates it from `load then a reader`. Its survey presence does NOT depend on the padding, and believing otherwise is the defect `tools/hazdecl.py` caught on its first real build. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): `ds_d0` reads OPEN (`B10CB10C`) with the load in a TAKEN branch delay slot and its consumer at the target, and `ds_d1` reads LOCK -- the same depth as the plain load-use family, so the delay slot does not move where the hazard closes. `SPEC.md` `CPU-54` |
| `load then a reader of the loaded register` | y | . | y | `CPU-14`, `CPU-54` | `bench/2026-09-14` | exposed, no interlock. ~~The ONLY route-1 hazard reading this project holds, and it is not this repository's~~ 🔄 **this repository's own instrument has it now**: the single-variable experiment is upstream's `P9-12`, `upstream/BENCH-LOG.md` `T-89`/`T-90`, on the same physical device. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): `lu_alu_d0` reads OPEN (`B10CB10C`, the pre-load value of `$9`) and hits the PRE-REGISTERED `dev=open` that came from upstream, while `lu_alu_d1` and `lu_alu_d2` read LOCK -- so the hazard closes at ONE instruction, which upstream's own v2 fix (two `nop`s) overshot. The `seat` column moves off `upstream` for that reason and not because the provenance changed; the single-variable experiment named above is still upstream's and is now reproduced here. ⚠️ All three rungs ran on a WARM cache: `probe5` controls neither its operand's nor its own cells' cache state, so the reading is *interlock behaviour on a warm cache* in `docs/isa-hazard.md` § 7's own words -- its FIRST numbered item, and 🔴 `SPEC.md` `CPU-14` cites that as a `§7.1`, which does not exist in that file. `SPEC.md` `CPU-14` |
| `movz or movn write-enable in a load delay slot` | y | . | y | `TC-h`, `TC-22`, `CPU-54` | `bench/2026-09-14` | nothing that has run on this die exercises the shape, and that is 量 rather than inherited: the VENDOR's artefacts hold ZERO sites (this kernel 0 of 3,183 conditional moves, `boa` 0, `busybox` 0, `stage2.bin` 0), and `hazlint` on three images of mine that HAVE booted -- r59 with seventeen boots, `R3`'s `loudm` and `quietm` -- reports 0 violations in 112,505 / 111,801 / 109,922 loads, because `config/rlxfw-cflags`'s `-fno-if-conversion` removes the sites and `hazlint` is a build gate. `TC-22`'s four are in a FLAGLESS build. § 10 ④ is this file getting that wrong and being corrected. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): the shape RAN and it is NOT exposed. `probe5`'s `movrd` family is this row -- its `mr_d0` line names `TC-h` in its own words -- and `mr_d0` and `mr_d1` both read LOCK (`A5A5F00D`), so with the destination freshly loaded and the condition false the move does not leave a stale load standing. ⚠️ The NEIGHBOURING shape does read OPEN and is not this row: `movcond`, which is `movn` with the CONDITION register freshly loaded, gives `mc_d0` OPEN and `mc_d1` LOCK. `SPEC.md` `CPU-54` |
| `mult/div then mfhi/mflo` | y | y | y | `CPU-29`, `CPU-31`, `CPU-54` | `bench/2026-09-14` | 16 sites in the loader with no `nop` between them, running on every boot. `CPU-31`: the count is equally consistent with an interlocked core and with an interlocked core where those sites are bugs. 2026-09-13: `probe5` has this family at d0/d1/d2/d3 and `hl_ctl` beside it, because 量 shows `mult` overwrites both halves of the accumulator -- so without a rung that primes and reads back with NO `mult`, *the prime did not land* and *there is no hazard* would be one capture. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): ANSWERED, and the answer is that this hazard is NOT exposed. `hl_d0` through `hl_d3` all read LOCK (`23456780` four times), so a `mult` followed immediately by `mflo` reads correctly -- and the control the sentence above asks for ran beside them: `hl_ctl` primes LO and HI with NO `mult` at all and reads `CAFE0000` / `aux BEEF0000`, so the four LOCK legs are not a prime that failed to land. `CPU-29`'s sixteen unpadded loader sites are therefore consistent with the silicon rather than sixteen bugs. `SPEC.md` `CPU-31` |
| `store, the class hazlint has no rule for` | y | . | . | `CPU-52`, `CPU-54` | `bench/2026-09-14` | SPECIFIED 2026-09-13 (`R1-pub-2`), and this row's LABEL is imprecise rather than the class being empty: 量 with nine fixtures and both controls, `hazlint` has a rule for a store as a CONSUMER on BOTH operand paths (data `rt` and base `rs`) and no rule for a store as a PRODUCER on either shape tried. So the class splits by the store's role into `storedata`, `storebase` and a producer shape that is NOT MEASURABLE AS A HAZARD with a reason -- MIPS-I requires a load to see a preceding store and every program on this die depends on it at population scale, so an observed violation would be a broken payload and not a reading. It is in `probe5` as the control `st_p`. This row is deliberately NOT split: splitting changes this census's population and that belongs to `R1-pub-0`. `SPEC.md` `CPU-52`, `docs/isa-hazard.md` section 8. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): all three sub-shapes RAN. `storedata` `lu_sd_d0` OPEN and `lu_sd_d1` LOCK; `storebase` `sb_m0_d0` and `sb_m1_d0` both OPEN and `sb_m0_d1` and `sb_m1_d1` both LOCK, with the `m0`/`m1` PAIR as its own control because exactly one of the two addresses can have been written; and the producer control `st_p` reads LOCK. So a store consumes at the same depth as an ALU consumer, and the producer shape behaved as this row says it must. ⚠️ The row is still NOT split -- that belongs to `R1-pub-0` -- so its ① is a reading of the three shapes under one row. `SPEC.md` `CPU-52` |
| `mtc0 then mfc0` | . | y | y | `CPU-30`, `CPU-31`, `CPU-56` | — | three sites in the loader, the first of them a `Status` write read back immediately, running on every boot. `CPU-31` states the limit: countable is not decidable. 🔄 量 2026-09-14 (seating 21, `probe5`, `bench/2026-09-14/C1-P5j.log`): a route-1 attempt RAN and it is VOID with a measured reason, which is not a reading and is why this row's ① stays empty. `c0_d0`/`c0_d1`/`c0_d2` all VOID -- the control word reads `80500270`, neither the `5A5A5A50` written nor the `A5A5A5A0` it held -- because `mtc0 $x,$14` does not write on this die (`SPEC.md` `CPU-56`). So this family cannot be asked through `EPC` at all; asking it needs a CP0 register that is writable, which needs Lexra's CP0 map (`CPU-49`) |
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

🔄 **2026-09-14: both figures above are the 2026-09-12 state and are kept
exactly as they were, because they are what the refutation condition was
evaluated against.** 量 after seating 21: route ① is **42 of 45 (93.3 %)** —
37 `R1a` rows and 5 `R1b` rows — and the three still without it are `jalx`,
`mtlxc0` and the `mtc0`→`mfc0` hazard, the last of which had a route-① attempt
that came back VOID with a measured cause (`SPEC.md` `CPU-56`). **That is not
prior art arriving late; it is this gate's own payloads doing the thing the
gate exists to do**, which is why the refutation condition is still recorded as
not having fired: it asked whether *the rows this repository already holds*
covered the census, and the answer to that question did not change.

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
| the `movz` delay-slot precondition | **answered, and the answer is the negative one** — § 10 ④ | no change to the step count; ~~the row stays route ③~~ 🔄 2026-09-14: route ① from seating 21, and the negative answer held on the die — `mr_d0`/`mr_d1` both LOCK |

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

### 9.1 🔴🔴 2026-09-14: sentence ② is FALSE under this step's own definition, and four other things came out with it

**The contradiction, in three sentences that are all in this repository and
cannot all be true.**

| | claim | where |
|---|---|---|
| A | `R1c` runs as a Linux userspace program **under the vendor kernel** | `PROGRESS.md`'s `R1-pub-4` row |
| B | the ruler is `jiffies` for wraps ＋ `TC0CNT` for the sub-tick residue, read from userspace | § 9 above, decision ③ |
| C | reaching it "is **not** a new driver: `rtl819x-timer` already exposes its own counters" | § 9 ②, the paragraph directly above |

`rtl819x-timer` is a file of **mine**. It reaches a staged tree through
`config/rlxfw-marks.tsv`'s `MK2` row, and its `/proc` entry is created by
`create_proc_entry(RTL819X_PROC_NAME, ...)` in
`config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c`.
**It cannot exist in the vendor kernel.** A and C cannot both hold.

⚠️ **A 量 mark is carrying an inference.** `PROGRESS.md`'s inherited-state
table marks *"The SoC timer is a driver of mine now, so `R1c`'s ruler exists"*
as 量. `CLK-27` is real; the operative clause *so `R1c`'s ruler exists* is
推, and it is the inference that fails. Both halves were written in one commit
(2026-09-11); sentence C was added a day later in `R1-pub-0`'s own commit and
is the only sentence in § 9 carrying no mark at all.

🔴 **A second sign the working model was "my kernel":** § 7's seating
schedule books slot 3 as **"`J` to a kernel of mine"** and books no slot for
the vendor kernel at all.

**Four more findings, none of which had reached any file:**

1. 🔴 **The plan's own fallback ruler is broken too, by a different
   mechanism.** `plan:1058` ② names `0x8040DCE8`. That is a **loader `.data`
   variable**, not a register — `docs/loader-phy-and-switch.md` records its
   single writer as the loader's timer ISR. Under Linux `Status.BEV` is 0, the
   vectors are at `0x80000080`, and the loader's ISR does not run, so **that
   counter does not advance at all**. § 9 above silently substituted the
   *register* `TC0CNT` for the plan's *RAM address* without recording that the
   plan's address was unusable. 推, and nothing in the repo states it.

2. 🔴🔴 **A SIGILL-handler census can PANIC this kernel, and the family it
   would panic on is exactly one of the census's blanks.** 讀,
   `arch/rlx/kernel/traps.c`: `do_tr` **is not defined** and cause 13 gets no
   vector from `set_except_vector`, so a trap exception falls to
   `handle_reserved` → `do_reserved` → **`panic()`**, with no
   `die_if_kernel` guard — so a **user-mode** trap instruction panics the
   board. The MIPS-II trap family `teq`/`tge`/`tgeu`/`tlt`/`tltu`/`tne` is
   precisely § 10's *"six rows have no evidence of any class, and they are all
   the same family"*. **The outcome depends on the unknown being measured**: if
   the core implements them, the probe panics; if not, it raises RI and the
   handler returns SIGILL normally. `R1-pub-4` cannot probe that family without
   a separate decision, ~~and this is written here **before** the payload
   exists~~ 🔄 **2026-09-14: that clause was false at the moment it was
   written.** This item was committed at **16:20:41** on 2026-09-14;
   `tools/isa-payload.tsv` had carried all six rows since 2026-09-13, and
   `bench/2026-09-14/C1-P4j.log` had landed at **05:39** — 10 h 41 min
   earlier. Three amendments, and the first one resolves the item on its own
   stated condition:

   **(a) 🟢 The unknown WAS measured, and it is the safe answer.** 量
   `bench/2026-09-14/C1-P4j.log` (seating 21, `probe4`, bare metal, under a
   handler of ours): all six read **`n=1 cause=20000028` — ExcCode 10,
   Reserved Instruction** — with the operands chosen so the trap condition is
   TRUE, and `tools/rlxprobe/cells4.S` registered all three outcomes at the
   `teq` word before power (*13 if the core has them, 10 if it does not, and a
   retirement if neither*). `SPEC.md` `CPU-57`. **So this core does not
   implement the family, and no `teq`/`tge`/`tgeu`/`tlt`/`tltu`/`tne` can
   reach the missing cause-13 vector by being issued.**

   **(b) 🔴 That is a KERNEL-MODE reading and this item is about USER mode,
   and this repository holds no user-mode `ExcCode` reading of any instruction
   on this die.** The step from one to the other is **推**, and it is not a
   free step — item 3 immediately below is the counterexample for a
   neighbouring class: `ll`/`sc` are `lwc0`/`swc0`, user mode runs with `CU0`
   clear, so from user mode they raise **Coprocessor Unusable (cause 11)**,
   where `probe4` measured them retiring in kernel mode. **A change of
   privilege changed the exception for that pair, so it may change it for any
   other.** One user-mode reading settles it, and `R1-pub-4` is the step that
   could take it.

   **(c) 🔴 Cause 13 is not the only unvectored cause — 21 of 32 are.** 讀
   `arch/rlx/kernel/traps.c`, `trap_init()`: the default loop installs
   `handle_reserved` for `i = 0..31` and exactly **eleven** causes are then
   overwritten —

   ```
   set_except_vector(0, rlx_irq_dispatch);   set_except_vector(8,  handle_sys);
   set_except_vector(1, handle_tlbm);        set_except_vector(9,  handle_bp);
   set_except_vector(2, handle_tlbl);        set_except_vector(10, handle_ri);
   set_except_vector(3, handle_tlbs);        set_except_vector(11, handle_cpu);
   set_except_vector(4, handle_adel);        set_except_vector(12, handle_ov);
   set_except_vector(5, handle_ades);
   ```

   — so **6, 7, 13 and 14–31** all reach `do_reserved` → `panic()`. Mainline's
   `arch/mips/kernel/traps.c` carries `set_except_vector(13, handle_tr)` and is
   the positive control that says the omission is the vendor's. **The hazard
   this item names is therefore a class and not one instruction**: any encoding
   on this die that raises one of those 21 causes panics this kernel, and a
   user-mode census has no list of which encodings those are.

3. ⚠️ **The amplification estimate is anchored to the wrong function.** § 9
   says an emulated instruction *"costs an exception round trip through
   `do_ri`"*. For `ll`/`sc` **from user mode** that is not the handler: `ll` is
   `lwc0`'s opcode and user mode runs with `CU0` clear, so the exception is
   Coprocessor Unusable (cause 11) → `do_cpu`, whose path is shorter. The
   vendor kept mainline's comment saying exactly this. 推.

4. 🟢 **The problem is much smaller than § 9 makes it look.** The census is
   45 rows; the emulation surface is `ll`, `sc`, `sync` and the unaligned
   `lh`/`lhu`/`lw`/`sh`/`sw`. **The two-column DIFF is trap / no-trap and needs
   no clock at all** — the ruler is needed for roughly **four rows of
   forty-five**. Nothing in the repo states this, and it changes the weight of
   the whole problem.

⚠️ **And one prerequisite sits two gates downstream**: `R1c` needs a compiled
userspace C program, and *which toolchain rlxfw's userspace uses* is
`docs/GATE-RESULTS.md`'s open item owned by **`R7`**.

🔴 **This section does NOT pick an option.** The option space — run on
rlxfw's image and correct the step; run on the pristine vendor kernel with a
10 ms ruler and N-amplification; add one read-only `/proc` file to a vendor
config; ship the diff and drop the cost column; derive the cost bare metal;
split the step; or `/dev/mem` + `mmap`, which the repo has **zero** hits for
anywhere — is `R1-pub-4`'s first desk session's work, and the decision is the
owner's. `PROGRESS.md`'s `R1C-1` carries it.

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

**③ ~~Six rows have no evidence of any class~~, and they are all the same
family** — 量 2026-09-12, and 🔄 **the struck half expired on 2026-09-14 (all
six read ExcCode 10 on the die); the second half is why the finding was worth
having.** *(The strike was added on 2026-09-14 by a closeout audit: the
annotation below already said the half had expired, but the heading still read
as current, and a heading is what a reader quotes.)*
`teq`, `tge`, `tgeu`, `tlt`, `tltu`, `tne` — the MIPS-II trap instructions. Not
in `CPU-18`'s scan list, not probed by `isa-probe.sh`, absent from § 6's table.
They are on `hazlint`'s watch list and ~~nothing else in this repository has
ever mentioned them~~ 🔄 **that stopped being true on 2026-09-13 and the
reading landed on 2026-09-14 at 05:39.** `tools/isa-payload.tsv` gave all six a
row in its `traps` group (words `0x01090030`–`0x01090036`) and seating 21 ran
them: **all six TRAPS, `cause=20000028` — ExcCode 10, Reserved Instruction —
with the operands chosen so the trap condition is TRUE**, so ExcCode 13 was the
reachable alternative and the die did not take it. **This core does not
implement the MIPS-II trap family.** 量 `bench/2026-09-14/C1-P4j.log`,
`SPEC.md` `CPU-57`; § 3's rows are route ① from that seating.

⚠️ **The correction is one segment late and that is the finding inside the
finding.** The paragraph above was true when it was committed (2026-09-12
22:36). § 9's item 2, written 2026-09-14 at 16:20, then quoted it as a live
blank and rested a safety argument on it — **10 h 41 min after the capture that
answered it, and 12 commits later**. Nothing in this repository connects a
committed capture to the rows it fills: `isacensus check` compares the table
against the two population instruments and against this document, and **no
check of any kind reads a `bench/` capture**. That is a gap with a name and no
owner yet.

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
