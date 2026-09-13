# `probe4` — the `R1a` instruction sweep, and how each of its answers is checked

`R1-pub-1`. One row per encoding, three verdicts, and every number in the table
derived twice before the board is powered.

This document is the payload's design and its limits. The **table** is
`tools/isa-payload.tsv`; the **instrument** is `tools/isapay.py`; the **payload**
is `tools/rlxprobe/probe4.c` with `cells4.S` and `probe4rows.h` generated from
the table. Nothing here is a second copy of those files — where this document
and the table disagree, the table is right and this document is stale.

---

## 0. What it does not claim

**Does not claim that a row which does not trap is an instruction this core
has.** `plan/router-rebuild-plan.md:716-719` (D14-5) says it in the strongest
terms the plan uses: *「沒有 trap」不構成「支援」的證據*. A row whose expected
constant is `-` can only ever report that it did not trap, and it gets its own
verdict word — `RAN` — rather than being folded into `RIGHT`.

**Does not claim that the qemu arm is evidence about this device.**
`plan:706` (D14-1): *任何在 host、qemu 或 vendor kernel 上通過的測試，不構成
codegen 或 ISA 正確的證據*. What the qemu arm is for is § 4.

**Does not claim the population is the ISA.** It is the plan's nine groups
(`plan:1011-1022`) plus the rows this repository's own instruments already
derive, joined in both directions by `isapay population`. Two groups are
deferred and § 7 names them.

**Does not compare anything in the payload.** `PROGRESS.md:121`'s risk column:
*a payload that compares in-place reports a boolean and throws the value away.*
The expected constants are not in the image at all, so there is nothing there
for a wrong expectation to be silently right against.

---

## 1. The population, against the specification that asked for it

`plan:1011-1022` tables nine groups. This is the row-by-row correspondence —
written because the sixty-second segment learned that *a deliverable that does
not point back at its own specification is a deliverable nobody can check*, and
because the check found a missing half-row the moment it was written.

| plan group | plan's own words for what it changes | rows here |
|---|---|---|
| MIPS-I 基線 | 正控制 | `add` `lw` `sw` `mult` `mult_hi` `beq` `jr` |
| 保留編碼 | 負控制, and the answer checker's own positive control | `special0e` |
| 非對齊 | F51 — whether the 144 sites in the vendor's `boa` execute | `lwl` `lwr` `swl` `swr` |
| MIPS-II | 決定 libc | `ll` `sc` |
| MIPS32R1 | `-march` 下限 | `clz` `clo` `mul` `madd` `madd_hi` `movz` `movn` `sync` `pref` |
| MIPS32R2 | `-march` 上限 | `ext` `ins` `rotr` `seb` `wsbh` `synci` `rdhwr` |
| MIPS16 | D11 做不做 | **deferred, § 7** |
| FPU (cop1) | soft-float | `mfc1` `lwc1` `swc1` `ldc1` `sdc1` |
| Lexra ASE 🏆 | 直接判決 `CPU-04` | `madh` `madl` `mazh` `mazl` `msbh` `msbl` `mszh` `mszl` `ltw` `udi0i` `udi1i` `udi2i` `udi3i` `udi0` `udi1` `udi2` `udi3` `udi4` `udi5` |
| NX | § 8.2 第一列 | **deferred, § 7** |

Four groups carry rows the plan does not name and this repository's instruments
do: `census` (the MIPS-II branch-likely four, the four `cache` op values, and
`mfc2`), `cop3`, `lexra-cp0`, and `traps`. They are listed separately in
`isapay population` rather than folded into the plan's list, so that *the plan
asked for this* and *our instruments derive this* stay distinguishable.

### Why this is not `tools/isa-census.tsv`

`docs/isa-hazard.md` is this document's sibling for `R1b`/`probe5`, which
shares this harness and this register map and asks a different question; where
the two disagree about something both describe, the one whose payload it is
wins.

`docs/isa-prior-art.md` is the prior-art census (`R1-pub-0`), and its § 0 says
in its own words that it *"does not claim … that the population is the ISA"*,
and that *"an instruction this core obviously has, and that the loader executes
thousands of times per boot, gets no row"*.

🔴 **The instructions it excludes by that rule are exactly `R1a`'s positive
control.** `plan:1013` marks the MIPS-I baseline group 正控制 and `:1074` makes
it half of the pass condition. A payload built from the census population alone
would have had no positive control at all, and `plan:1074` is not satisfiable
without one. `isapay population` therefore joins the two tables **in both
directions** and prints the difference on every run: 43 rows here are not in the
census, 7 census rows are not here, 32 are in both.

The 7 the census has and this table does not:

| census row | why it is not a payload row |
|---|---|
| `COP1` `COP2` `SPECIAL2` `SPECIAL3` | opcode GROUPS, not encodings. Their members are rows here |
| `cache` | one census row covers four op values, which are four rows here |
| `jalx` | excluded, § 7 |
| `mtlxc0` | excluded, § 7 |

---

## 2. The cell, and why a generator

Every cell has the same register allocation, and that is the whole argument for
generating them rather than writing 75 by hand: **the encoding's `rs`/`rt`/`rd`
fields and the setup code that fills those registers come out of one place and
cannot drift apart.**

| register | role |
|---|---|
| `$8` | input A — every `rs` field in the table is 8 |
| `$9` | input B — every `rt` operand field is 9 |
| `$10` | the memory operand base — every `base` field is 10 |
| `$2` | the result — every `rd` or destination `rt` is 2 |
| `$11` | the aux result (HI), and the jump target register |
| `$24` | the scratch pointer |

`$24` is never an operand of a probed instruction. A probed instruction that
misbehaves therefore cannot destroy the pointer the cell needs in order to
record that it misbehaved.

Five templates, and which one a row gets is its `shape` column:

| shape | body |
|---|---|
| `alu` `load` `store` | the probed word, two `nop`s, then `$2` and both memory words recorded |
| `hilo` | the probed word, then `mflo $2` and `mfhi $11` with MIPS-I's two-instruction spacing |
| `machilo` | the same, with HI and LO **primed** to `0x0BAD0000` / `0xF00D0000` first |
| `branch` | `TAKEN` and `NOT-TAKEN` written as two different constants into `$2` |
| `jr` | the same, with the target formed in `$11` by `lui`/`addiu` |

`alu`, `load` and `store` emit one template; they are separate names because
`isapay encode` cross-checks a row's declared shape against its own opcode, and
a row that says `alu` and encodes a store has one of the two columns wrong.

### What `machilo` buys, and the second thing was not why it was written

A multiply-accumulate has no single computable answer when the accumulator at
cell entry holds whatever the previous row left. Priming it makes `madd`'s
answer computable — `0x0BAD0000F00D0000` plus the product, which carries out of
the low half, so `madd_hi` is `0x0BAD0002` and not `0x0BAD0001`.

The second thing is worth more. For the eight Lexra MAC encodings, whose
**semantics this project has not read** — the public patch gives encodings and
operand formats, not behaviour — priming makes *the accumulator did not move* a
distinguishable outcome from *the accumulator moved*. That separates "retired as
a no-op" from "did something MAC-shaped" without knowing what the something is.

---

## 3. Three sources for every encoding

| | source | what only it can catch |
|---|---|---|
| 1 | the `word` column, written by hand | — |
| 2 | `isapay encode`, which builds the word from the `fields` column | arithmetic |
| 3 | `isapay verify`, which disassembles the **built artefact** with binutils | a wrong belief about the encoding layout, and a row named for one instruction that encodes another |

(1) and (2) are two computers doing the same sum and they catch slips. Only (3)
is conceptually independent, because it is the only one this repository did not
write — and it is run on the linked ELF, not on the table, so it also catches
anything the assembler or linker did on the way.

🔴 **Source 3 found two things on its first run and one of them was my
normaliser.** The first draft derived the expected mnemonic by stripping
trailing digits, so that `cache10` would reduce to `cache` — and it also reduced
`mfc1` to `mfc`, `lwc3` to `lwc`, `mtc3` to `mtc`. Nine rows reported *binutils
decodes it as `mfc1` and the row is named `mfc1`*, which is what a check looks
like when its own normaliser is wrong: the two strings it printed were
identical. There is no rule that separates a digit that is an operand from a
digit that is part of the name, so each one is written down instead.

### The other direction, and it is the one that matters

Everything above checks that every word the **table** declares is in the
**artefact**. It cannot see the opposite defect: a non-MIPS-I instruction in the
FRAMEWORK code — nothing declared it, and it would execute on every row.

`tools/test-rlxprobe.sh` guards that for `probe0`…`probe3` with a hardcoded list
per payload, and 量 2026-09-13 **that suite passes `probe4` without looking at
it** — 216 of 216, and none of the 216 reads this payload.

`isapay verify --strict` is the guard, and its formulation is not a comparison
of word values:

> **every non-MIPS-I word `hazlint --isa` can see must sit at a declared probe
> symbol.**

Put that way it does not depend on `hazlint` knowing every encoding this table
probes — opcode `0x3C` and opcode `0x1E` are not in its tables at all — and it
still refuses exactly the leak it is for. 量 on the committed artefact: **44
non-MIPS-I words hazlint can see, 75 declared probe sites, 0 strays.**

🟢 **Its positive control is a real payload.** Run against `probe3.elf`, which
declares none of these words, it reports **eight** strays — probe3's `mfc3`
stubs. ⚠️ And its limit, stated rather than left to be found: `hazlint`'s own
ISA table bounds what it can see, so this says *no non-MIPS-I word THAT HAZLINT
RECOGNISES is outside a probe site*, which is weaker than *no such word exists*.

The address predicate is split into a pure function so its control runs in CI
without a cross compiler — a control that only runs where a cross compiler is
installed is a control CI never executes, and this repository has measured that
happening to two whole suites.

### What `objdump -m mips:3000` declines to name is a reading, not a defect

A refusal is only a finding for the groups that claim to *be* MIPS-I
(`baseline`, `unaligned`). Everywhere else, binutils declining to name an
encoding is one more reading of where the MIPS-I boundary sits, and turning it
into a failure would be forcing the instrument to agree with the table. What is
a finding in every group is the decoder actively naming something **else**.

---

## 4. Two sources for every expected constant, and a third for some

| | source |
|---|---|
| 1 | the `expect` column, written by hand |
| 2 | `isapay model`, an implementation of the instruction's semantics written from the ISA definition and **not** from the encoding |

The separation in (2) is deliberate: the model functions take named values, so a
wrong `rs`/`rt` assignment in the table cannot propagate into the expectation.
`ext` and `ins` both put a size in the `rd` field and mean different things by
it (`size-1` against `pos+size-1`), so `rd` and `sh` are passed raw and each
model computes its own.

**The unaligned four are checked a third way, and it is stronger than any single
value.** `lwl A` + `lwr A+3` reconstructs an unaligned word and `swl`/`swr`
write one back; if the shift directions were mirrored, every individual value
could still be defended and the pair would not close. `isapay --self-test`
`T16b` is that pair.

### The qemu arm is an oracle for what the right answer IS, not for what this
### die does

qemu's Malta is a 24Kf — a MIPS32r2 core, by different authors, with an
interlocked load delay slot. For every row whose `qemu` column predicts `run`,
its answer is the MIPS specification's answer, produced by an implementation
this project did not write. That makes it a third source for the expected
constant.

It says nothing about this device, and `plan:706` forbids reading it that way.
The `qemu` column is a **pre-registered prediction** — `run`, `trap`, or
`trap:N` naming the ExcCode — and `isapay verdict --arm qemu` scores it. It is
pre-registered because `plan:738` says *其他任何 ExcCode = 一個要寫下來的發現，
不是一個錯誤*, and a finding you only recognise after the fact is one you argued
yourself into.

---

## 5. The verdict, and where it is computed

The payload records eight words per row and decides nothing:

| word | |
|---|---|
| 0 | the tag, `0x5234` in the top half and the row index in the low — **written before the cell is called**, so a row that hangs names itself |
| 1 | the exception count across the cell |
| 2 | the whole `Cause` word |
| 3 | `EPC` |
| 4..7 | `$2`, memory word 0, memory word 1, and the aux result |

`isapay verdict` reads a capture and applies:

| reading | verdict |
|---|---|
| the tag is not this row's | `NOT-RUN` |
| exception count is non-zero | `TRAPS`, with the ExcCode |
| zero, and the row has no expected constant | `RAN` — **not** a weaker `RIGHT` |
| zero, and the value equals the expected constant | `RIGHT` |
| zero, and it does not | 🔴 `WRONG` |

All four recorded values are kept rather than only the one the row asks about,
because the value that was thrown away is the one that turns out to be needed.

---

## 6. The controls, and the one that is two-sided

| | control | where |
|---|---|---|
| positive | the `baseline` group must read `RIGHT` | `plan:1013`, `:1074` |
| C1 | `break` must trap — the handler is reached and returns | `plan`; 量 `bench/2026-08-25b` |
| C2 | `special0e` must trap, ExcCode 10 | 量 `bench/2026-08-30` |
| C3 | the four `cache` op values must **not** trap, in the same capture | 量 same boot |
| C4 | the qemu arm, run and recorded first | `plan/DAY-ZERO.md:603` |

C1, C2 and C3 together are what make a zero mean something: C1 and C2 prove the
handler catches, C3 proves it does not catch everything, and both halves are in
one capture on one boot.

### The trap laid for the answer checker

`plan:761`: the reserved encoding is fed to the trap check **and** to the answer
check, and *若答案檢查說它「答對」，那是答案檢查寫錯了，整張表作廢*.

The way an answer checker gets that wrong is by reading the recorded value and
not the exception count. So the reserved row sets its `expect` **equal to its
`seed`** — which is what the value still holds after a trap. A checker that
consults the count says `TRAPS`; one that does not says `RIGHT`, and `RIGHT`
there voids the table.

For every other row the same equality is a defect, because *did the right thing*
and *did nothing* would be one reading. **One rule, opposite signs, and the
table parser enforces both** — a reserved row without the equality is refused
just as loudly as an ordinary row with it.

🔴 **And `special0e` retiring is a finding as well as a failure.** If SPECIAL
function `0x0E` is one of Lexra's proprietary operations it retires, the RI path
is then unproven, and the table is void — both sentences are true at once and
neither replaces the other.

---

## 7. What is deferred, by name, with the experiment

A check that is red on every run is a check nobody reads, so these are declared
in `isapay.py`'s `DEFERRED_GROUPS` with a control in the other direction: a
deferred group that has grown rows is an exemption nobody removed, and
`population` says so.

| | why | what closes it |
|---|---|---|
| **MIPS16** | needs a `-mips16`-assembled function and a return path in MIPS16 mode — a second execution context this payload does not have | one `-mips16` function with its own return stub, and `jalx` to enter it |
| **`jalx`** | if it retires, control lands in MIPS16 mode at an address decided by a 26-bit field. The cost of being wrong is a power cycle | the same stub |
| **NX** | needs the I-side flush around a word written into a data region. It is the only row here that would WRITE instructions | `probe1`'s `R1d` sequence applied to one page, in a step whose card can say so |
| **`mtlxc0`** | writes a CP0 register whose identity is unread. Its read-side twin `mflxc0` is a row here | reading the Lexra CP0 map first |
| **`sleep`** | `0x42000038`, RLXA. A bare-metal payload that sleeps does not come back | a payload with a timer already armed |
| **`sc` as a pair** | without a preceding `ll` to the same address, a correct `sc` has an unspecified outcome, so there is no single computable constant | a two-word cell, which the one-word-per-row schema does not express |
| **COP1 with `CU1` set** | this payload writes no CP0 `Status` on a device build, so a `CpU` verdict does not separate *no FPU* from *FPU disabled* | set `CU1`, read it back, repeat the five rows |

---

## 8. Encodings with two names, 量 2026-09-13

Found by source 3 on the built artefact, and reported on every run rather than
absorbed into an alias table.

| opcode | MIPS-I | later | consequence |
|---|---|---|---|
| `0x30` | `lwc0` | `ll` at MIPS-II | 🔴 the row the plan calls *the one that decides libc* |
| `0x38` | `swc0` | `sc` at MIPS-II | the same pair |
| `0x33` | `lwc3` | `pref` at MIPS32 | two rows here, at two different `rt` values |
| `0x3B` | `swc3` | unassigned at MIPS32 | qemu should refuse it where this die may not |

🔴 **`ll` not trapping on this die would not show that `ll` exists.** This is a
MIPS-I core; the same word is `lwc0`, a coprocessor-0 load. The three-way
verdict already separates them — `ll` writes the GPR and reads `RIGHT`, `lwc0`
writes a CP0 register and leaves the GPR at its seed, which reads `WRONG` — so
the discrimination is free. What is not free is the risk: if the core does
implement `lwc0`, that row writes CP0 register 2 with the word at `mem0`. That
word is `0x0000A5F0` and not a full-width pattern for exactly this reason, and
`rlx_reset` is a watchdog bite, which resets CP0 state.

The `sc` direction is safe: `swc0` **reads** a CP0 register and stores it, so
the value landing in `mem0` would itself be a reading of CP0 register 9.

---

## 9. The Lexra ASE rows, and what their membership words say

Encodings read out of `0001-binutils-2.24-add-lexra-support.patch`, the
**32-bit** opcode table (`opcodes/mips-opc.c`, patch lines 1558-1574). The
eight MAC mnemonics also appear in `mips16-opc.c` at 16-bit encodings with mask
`0xf81f`; those are a different instruction set and are not these rows.

The patch's own membership macros:

| macro | expands to |
|---|---|
| `RLX0` | `INSN_4180` |
| `RLX1` | `INSN_5280` |
| `RLX2` | `INSN_4181` or `INSN_5181` |
| `RLX3` | `INSN_4281` or `INSN_5281` |
| `RLXA` | all four |
| `RLXB` | `RLX1` or `RLX2` or `RLX3` |

量 `CPU-04`: this core is `RLX4181`. So `RLXA` and `RLXB` both include it
through `RLX2` — and `ltw`'s membership is neither macro but the literal
`INSN_4181 | INSN_4281`, **this core and its sibling, by name**. That makes
`ltw` the sharpest row in the group.

⚠️ **Semantics are not read.** The opcode table gives encodings and operand
formats, not behaviour, so every ASE row's `expect` is `-` and its verdict can
only be `TRAPS` or `RAN`. What the primed accumulator adds (§ 2) is that for the
eight MAC rows, `RAN` splits into *the accumulator moved* and *it did not*.

`ltw`'s destination fields are left at zero because their layout is not read, so
it writes register zero and only the base is chosen.

---

## 10. What could still be wrong

* **The `cache11` row may invalidate the line it is about to read back.** Hit
  Invalidate D on the scratch line discards it without writing back, so that
  row's `m0` and `m1` are not evidence about memory. Its `gpr` and its exception
  count are.
* **`hilo` rows have no untouched-value check.** HI and LO at cell entry hold
  whatever the previous row left, which is the thing `machilo` exists to fix;
  for `mult` and `mult_hi` the expectations are real products and the collapse
  risk is nil, but the tool cannot say so and does not pretend to.
* **The `udi*` rows execute instructions whose semantics nobody has published.**
  The destination is `$2` in every case, so whatever they compute is contained —
  but *contained* is an argument about the encoding, not a measurement.
* **One scratch block is reused by every row.** A row that corrupted it would
  hand the next row operands nobody chose; `H_SCRATCH_BAD` counts rows whose
  inputs did not read back, and without that count such a reading would look
  exactly like an ordinary `WRONG`.
* **`verify --strict` is bounded by `hazlint`'s ISA table**, and the rest of
  `verify` is bounded by binutils' — both are third-party tables, which is what
  makes them worth having and also what makes them a limit rather than a proof.
* **The `DW` read-back parser is not written.** `isapay verdict` reads the
  payload's own `P4 ` lines, which is the only channel qemu has and a second one
  on the device. The loader-side parser is `R1-pub-3`'s, and writing it now
  against a capture that does not exist would be a second implementation of a
  format nobody has read yet.
