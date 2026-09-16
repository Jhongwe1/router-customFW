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

**Does not compare anything in the payload.** `PROGRESS.md:514`'s risk column:
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

🔄 **2026-09-15: that join is BY NAME, and a name-only join understates
the overlap by twelve rows.** Four of the seven above are opcode groups whose
members ARE rows here, so a join that follows a group to its members gives a
different pair of numbers, and both pairs are right about different questions.
量 2026-09-15 at the desk, over the two committed tables:

| join | in both | payload rows the census does not cover | census `r1a` rows with no payload row |
|---|---:|---:|---:|
| by name, which is what `isapay population` prints | 32 | 43 | 7 |
| by name or GROUP | 44 | 31 | 2 |

The twelve the group join adds are `cache10`/`cache11`/`cache15`/`cache19` to
`cache`, `mfc2` to `COP2`, `clz`/`clo`/`mul` to `SPECIAL2`, and
`ext`/`ins`/`seb`/`wsbh` to `SPECIAL3`. **`COP1` adds none**: its five members
— `mfc1`, `lwc1`, `swc1`, `ldc1`, `sdc1` — are census rows in their own
right and are already among the 32. The two `r1a` rows uncovered under either
join are `jalx` and `mtlxc0`, both excluded by name in § 7.

⚠️ **No instrument derives the second row of that table.** `isapay
population` implements the name join only, and the 44/31 split is written down
in `bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.2 and again in
`docs/emulation-surface.md` § 8.2 — two agreeing hand counts rather
than a derivation, which is the weaker thing and is said out loud rather than
left to be found. `docs/isa-prior-art.md` § 9.2 carries the same
reconciliation from the census side, which is where a reader who has met the
number 45 is sent.

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
| 2 | the whole `Cause` word. 🔄 **On the second arm this word is not `Cause` at all — § 11.2** |
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
| ~~C2~~ **C5** | `special0e` must trap, ExcCode 10 | 量 `bench/2026-08-30`; renumbered 2026-09-15, below |
| C3 | the four `cache` op values must **not** trap, in the same capture | 量 same boot |
| C4 | the qemu arm, run and recorded first | `plan/DAY-ZERO.md:603` |

🔄 **2026-09-15: `C2` is renumbered `C5`, because one id meant two
different controls inside one instrument's documentation.** The second arm
(§ 11) reaches these same 75 encodings from Linux user mode through the
same `tools/isapay.py`, and `notes/userspace-probe.md` § 4 names that
arm's controls `C1a`, `C1b` and `C2` — where its `C2` is *every trapping
row's faulting PC equals that row's own `_w` symbol*, which is not this control
and is not even the same kind of claim.

**Which one moved was decided by measurement rather than by seniority.** 量
2026-09-15 over every frozen `bench/*/PREDICTIONS-*.md`: the user arm's `C2` is
pinned by name in `bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.4 and
is a literal string `tools/isapay.py` prints (`C2 NOT RUN`), so moving it would
strand a frozen card and a tool's own output; **no frozen card names this one
`C2`** — seating 21's card and `SPEC.md` `CPU-57` both call the
reserved-encoding control `D2` — so this is the one that can move.

⚠️ **`C1` and `C4` did not move with it**, although a whole
re-lettering would have read better: seating 21's card names both by their bare
ids (`break.count` is *"this is `C1` and it is mandatory"*, and the forced
anti-control is `C4`), so re-lettering the set would have stranded two
citations to buy tidiness. **The gap left at `C2` is the record and is not
closed up.**

🟢🟢 **量 2026-09-14 (seating 21), `bench/2026-09-14`: every one of them held.**
The `baseline` group read **`RIGHT` on all seven rows** (`add`, `lw`, `sw`,
`mult`, `mult_hi`, `beq`, `jr`); `break.count=00000001` with
`break.cause=00000024` → ExcCode 9; **`special0e` trapped with ExcCode 10**, so
the table is not void; and the four `cache` values retired in the same capture
with `n=0`, so *does not trap* is a reading rather than a dead handler. Tally
over 75 rows: **RAN 16, RIGHT 16, TRAPS 42, WRONG 1.** Two rounds, 75 row lines
and 18 header fields byte-identical, and the `DW` channel agrees word for word
with `seal=AF7A728B` on all three channels.

> 🔴🔴 **2026-09-14 (the sixty-ninth segment, desk): ~~`C2`~~ `C5` is clean by
> EXACTLY ONE FUNCTION CODE, and nothing here knew it.**
> 讀 the vendor's `arch/rlx/kernel/traps.c:454-462`, `simulate_sync` — it
> matches SPECIAL with function field **`0x0F`**, ignoring `rs`, `rt`, `rd` and
> `sa`, and returns 0: a pure no-op with `epc` already advanced.
> `special0e` is SPECIAL function **`0x0E`**. **Adjacent.**
>
> Had this control been `0x0000000F`, it would have trapped, entered `do_ri`,
> been **emulated silently**, sent no signal, and the payload would have reported
> *does not trap* — on a die that may well raise RI for it. **A negative control
> would have come back green while saying nothing**, which is the one failure
> mode a negative control exists to prevent.
>
> ⚠️ **It matters for `R1c` more than for `probe4`.** Under a bare-metal
> handler of ours the kernel's emulation is not in the path at all; `R1c` runs
> this same table in USER mode under ~~the vendor kernel~~ **rlxfw's own kernel (🔄 `R1C-1`, 2026-09-14)**, where `do_ri`'s emulation
> is live for every row. **Any encoding added to this table from now on has to be
> checked against `simulate_llsc` (primary opcodes `0x30` and `0x38`) and
> `simulate_sync` (SPECIAL `0x0F`) before it can be called a control.**
> The whole surface is enumerated in `notes/vendor-kernel-isa.md` § 1.4;
> `docs/isa-prior-art.md` § 9.3 is the decision that rests on it.

### 🔴🔴 The `WRONG` cell is observed, and the value was written down first

`rotr` read **`00123456`** where the table expects **`78123456`**, with no
exception. Input `12345678`, shift 8: a rotate gives `78123456`, a logical shift
right gives `00123456`. The encoding is `0x00291202` — SPECIAL with `rs=1`, and
that one bit in the `rs` field is the whole difference between `rotr` and `srl`.
**This core ignores it and executes `srl`.**

🟢 **`tools/isa-payload.tsv`'s own `why` for that row said so before the board was
powered**: *a core that ignores it computes srl and answers 0x00123456, which is
the WRONG cell doing its job*. The value, the mechanism, and the reason the row
exists were all pre-registered, and the device delivered all three.

🔴 **This is the first-hand evidence for `CLAUDE.md`'s ban on `-march=mips32`.**
That rule's stated reason is *mips32 miscompiles silently — no fault, no warning,
just wrong values*, and until tonight it was inherited rather than measured on
this die. ⚠️ **It is one encoding, not a claim about mips32 as a whole**: the
population is these 75 rows and `WRONG` is 1 of 75.

C1, ~~C2~~ C5 and C3 together are what make a zero mean something: C1 and C5
prove the handler catches, C3 proves it does not catch everything, and both
halves are in one capture on one boot.

### 🔴 A SECOND pre-registered prediction was refuted, and it settles which machine this die is

🆕 **2026-09-14 (sixty-eighth segment, desk, zero power cycles, re-reading
`bench/2026-09-14/C1-P4j.log`).** § 8's table registers the ambiguity in
advance: *`0x33` | `lwc3` | `pref` at MIPS32*. `tools/isa-payload.tsv`'s `pref`
row carries the encoding **`0xCD400000`** and the expected verdict **`run`** —
the MIPS32 hint retires and writes nothing.

**量: it trapped.** `bench/2026-09-14/C1-P4j.log:38` reads
`P4 00000016 pref 52340016 00000001 3000002c 805016ec …` — `n = 1`,
`cause = 3000002C`, so **ExcCode 11 (Coprocessor Unusable) with `CE` = 3**.
A MIPS32 `pref` has no coprocessor field and cannot raise CpU; a MIPS-I `lwc3`
does, from COP3, and `CE` names it. ⇒ **opcode `0x33` decodes as `lwc3` on this
die and the MIPS32 hint is not implemented**, which is exactly the question
`cells4.S` says the row exists to ask.

🟢 **`mfc2` is the row beside it and its prediction HELD**: encoding
`0x48020000`, expected `trap:0x0B`, measured `cause = 2000002C` →
ExcCode 11 with `CE` = **2**. This repository had never looked for CP2 on this
part; `tools/isa-census.tsv`'s `COP2` row was route ④ until tonight.

⚠️ **Both were missing from `SPEC.md` `CPU-57`**, the row that owns this
census, and neither mnemonic appeared in it. The `pref` half is the one worth
the paragraph: a refuted prediction whose refutation is a **positive**
identification of the decoder, not an absence.

🟢 **And the `CE` field itself is a reading — `SPEC.md` `CPU-59`.** Over the 42
rows of this capture that took an exception, `CE` is written **only** on CpU
and it names the coprocessor (3 for `pref`/`mfc3`/`mtc3`/`cfc3`/`lwc3`/`swc3`,
1 for `mfc1`/`lwc1`/`swc1`, 2 for `mfc2`); the 32 RI rows carry the `CE` the
previous CpU row left, with **zero** inconsistencies. The control is the five
RI rows that precede any CpU at all: they read `CE` 0. That is also why the
trap family's cause word is `20000028` where `special0e`'s is `00000028` —
`mfc2` is the row immediately before `teq`.

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
| 🔴 **REGIMM trap-immediate** 🆕 | 🆕 **2026-09-14 (sixty-ninth segment), and this one is ABSENT rather than deferred.** `teqi`, `tnei`, `tgei`, `tgeiu`, `tlti`, `tltiu` -- opcode `0x01` with `rt` in `0x08`-`0x0E` -- have **no row in this table and no entry in `DEFERRED_GROUPS`**, because that dict excludes groups that are present; these were never added. 量: zero occurrences anywhere under `tools/`, `docs/` or `SPEC.md`. `hazlint`'s `ISA_TRAPS` carries the six **SPECIAL** function codes only, and `CPU-57`'s SPECIAL answer does NOT carry across -- the one REGIMM encoding ever probed, `synci` (`0x055F0000`, `rt = 0x1F`, unassigned in MIPS-I), **retired instead of raising RI**, so this core's REGIMM `rt` decode does not funnel unassigned values to RI | one row: `teqi $8,0x2A` with `$8 = 0x2A` so the condition is TRUE, plus one line in `hazlint`'s `ISA_TRAPS`. 推 it is the highest-probability remaining route to the unvectored cause 13. ~~Zero incremental bench cost if it rides an existing card.~~ 🔄 **2026-09-15 (seventy-first segment): refuted the same day it was written and not propagated until now.** Every payload that can survive a trap compiles its row list in and is pinned by a card's sha256, so one more row is a new binary and a new card; without an exception handler a trap parks the board and spends the one power cycle. `PROGRESS.md` `REGIMM-1` owns the cost; `SPEC.md` `CPU-60` carried the same error and is corrected in the same commit. `SPEC.md` `CPU-60`, `PROGRESS.md` `REGIMM-1`, `docs/isa-prior-art.md` § 9.4 ① |

---

> 🔴 **2026-09-14 (sixty-ninth segment): two things break a SIGILL-handler
> payload before any row of it runs, and both are 讀 out of the vendor kernel.**
> They constrain `R1c`, which is this table run again in USER mode, and they
> constrain nothing about the bare-metal payloads above -- which is exactly why
> nothing here had noticed them.
>
> ① **`traps.c:584` rewinds `cp0_epc` to `old_epc` BEFORE signalling.** A
> `SIGILL` handler that returns normally therefore re-executes the faulting
> instruction, forever. The payload must `siglongjmp` out of the handler, or
> advance `uc_mcontext.pc` itself.
>
> ② **The `siginfo` carries nothing.** `force_sig` sends `SEND_SIG_PRIV`, so
> `si_code` is `SI_KERNEL` and there is **no `si_addr`** -- it overlaps
> `si_pid`/`si_uid` in the union and reads **0**, not the faulting PC. A probe
> that identifies which row faulted from `si_addr` identifies every row as
> address zero.
>
> ⚠️ And a third that is not a bug but decides the scoring: `do_cpu` carries
> `simulate_llsc` and **not** `simulate_sync`, so from user mode `ll` and `sc`
> are emulated and return **with no signal at all**. Scoring *no signal implies
> the instruction exists* records them backwards.
> `notes/vendor-kernel-isa.md` § 1.4.


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
  🔄 **2026-09-14: the capture exists now, and the channel was read by hand.**
  `DW 80A03000 641` — `RB_POISON_W`, not the `633` `make show` prints, because
  `LDR-07` rounds up and `633` shows three of the eight margin words while a
  payload that overran its block writes **upward** from the seal. Reply 7,593
  bytes, exactly `tools/reply-size.py`'s prediction. **All three channels read
  `AF7A728B` and 75 of 75 row lines are byte-identical between the UART and the
  read-back**; the eight margin words are all poison. The tool that should do
  this is `tools/rbcheck.py`, and ~~**it cannot yet** — two defects measured at
  the desk before power: its payload tables know `probe1`..`probe3` only, and its
  `UARTSUM` regex matches `sum=` where `probe4` prints `seal=`. Extending it is
  carried forward with tonight's capture as its on-device anchor, which is the
  `C16`/`C39` pattern.~~

  🟢 **2026-09-14 (sixty-eighth segment, `6ccf643`): it can, and that carried-
  forward clause is DISCHARGED on its own terms.** `C45` and `C46` anchor on
  exactly the two captures this section is about — `bench/2026-09-14/C1-P4rb.log`
  with `C1-P4j.log`, and `C1-P5rb.log` with `C1-P5j.log` — so the `C16`/`C39`
  pattern cashed rather than being re-promised. End to end through the CLI:
  three channels agree, `AF7A728B` and `D72EB67D`, `rc 0`, margin 8 words and
  8 poison. 🔴 **And the two defects above were symptoms.** The root cause is
  that `MAGICS`, `PROGRESS`, `SRC` and `UARTSUM` are four copies of one fact —
  which payloads exist and what they print — and nothing had ever compared any
  of them against `tools/rlxprobe/`: the suite was 40 of 40 green on the day
  `probe4` and `probe5` were built and again on the day `probe6` was.
  `C40`…`C44` are the population control and its three positive controls.
  `PROGRESS.md` `RB-1`.

---

## 11. 🟢 The second arm — the same 75 encodings from Linux user mode, and the one word that means something else

**量 2026-09-15, seating 23, one power cycle, one boot.** It sits after
§ 10 for the reason `docs/emulation-surface.md` puts its § 8 after its
own *what could still be wrong*: the arm is newer than that list, and a section
that arrived later should read as later. It carries its own limits in § 11.5.

**What this section is not.** The instrument is
`config/rlxfw-user/isaprobe/uprobe.c`, and `notes/userspace-probe.md` owns it
— its ABI, its build, its six gates. The 45-row two-column table whose second
column this arm fills is `docs/emulation-surface.md`'s, and that file's
§ 3, § 4 and § 8 own every per-row cell. What is owned here is what
this file is for: **the payload's recorded format and its limits**, on an arm
that did not exist when § 5 was written.

### 11.1 The same bytes, and two differences

`uprobe.c` links **this payload's own `cells4.S`**. The encodings are not a
second copy of the table's words; they are the same object, so a row that is
wrong here is wrong on both arms and cannot be wrong on one — which is the
same argument § 2 makes for generating the cells at all, one level up.

| | bare metal, `probe4` | user mode, `uprobe` |
|---|---|---|
| line prefix | `P4 ` | `PU ` |
| row shape | `<idx:8hex> <name>` then eight 8-hex words | the same |
| word 0 | the tag, `0x5234` over the row index | the same |
| word 1 | the exception count across the cell | the signal count across the cell |
| word 2 | the whole CP0 `Cause` word | 🔴 **not `Cause` — § 11.2** |
| word 3 | `EPC` | the faulting PC, from `uc_mcontext.sc_pc` |
| words 4..7 | `$2`, `mem0`, `mem1`, aux | the same |

🔴 **`tools/isapay.py` carries two regexes rather than one `P4|PU`
alternation**, and its own comment says why: with a single pattern a file
holding both arms merges into one result block and the duplicate-index guard
reports *row N appears twice with different values* — corruption's message
for something that is not corruption, which is the worst kind of wrong message.

### 11.2 🔴 Word 2 is not a `Cause` register, and `exccode` over it yields a number that looks like one

A Linux process is not handed `Cause`. The harness packs the signal number into
the high half and `si_code` into the low half — `(signal << 16) | si_code`
— and `isapay verdict --arm user` decodes it through a table rather than
through `exccode`. That line was unguarded until this arm existed.

**量 `bench/2026-09-15/C2-UP.log`: all 46 trapping rows carry the same word,
`00040080`.** That is `SIGILL` over `SI_KERNEL`, and both halves are readings
rather than defaults:

* **`SIGILL` is 4 here and `SIGBUS` is 10**, because this port gives `SIGEMT`
  the number 7 where the generic Linux ABI gives it to `SIGBUS`. A decoder
  table copied from `signal(7)` prints a genuine `SIGBUS` as `SIGEMT` and
  nothing looks wrong. `SPEC.md` `CPU-63`.
* **`SI_KERNEL` (`0x80`) is what a reserved instruction is EXPECTED to carry**,
  because `force_sig` sends `SEND_SIG_PRIV`. `ILL_ILLOPC` would have been the
  surprise.
* 🔴 **The same `SEND_SIG_PRIV` is why `si_addr` reads 0** — it
  overlaps `si_pid` in the union — so a probe that identifies a row by
  `si_addr` identifies every row as address zero. Word 3 is the only handle on
  *which* row faulted, which is the whole reason the user arm carries a
  PC-identity control at all.

⚠️ **One value across 46 rows is a thin reading, and it is stated as one.**
The capture holds no second signal number and no second `si_code`, so nothing
in it separates *the harness decodes both halves* from *the harness prints
whatever one word it was given*. What makes it more than that is the
`raise(SIGILL)` control — `c1a_raise` — which reaches the same handler
by a route that borrows nothing from the encodings under test.

### 11.3 The reading, and the line was frozen before the board was powered

量 `bench/2026-09-15/C2-UP.log`, `/bin/uprobe d73`, under rlxfw's own kernel:

```
verdict (user arm): 75 row(s), RAN 12, RIGHT 16, TRAPS 46, WRONG 1
```

🟢 **`bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.3 carries
that line character for character**, frozen at `9874012` before power. The
result is `SPEC.md` `CPU-64`'s; the per-row cells and the single row on which
the emulation surface is visible are `docs/emulation-surface.md` § 3 and § 4's.

Two readings the row lines carry that no header field reports:

* **46 rows took a signal and 29 did not, and every one of the 46 took exactly
  one.** So the handler's `+4` returned into each cell's own epilogue every
  time rather than re-faulting on the same word, and the escape hatch was never
  approached. 讀 `uprobe.c`: the escape is `n == max_sig + 1` by
  construction and there is deliberately **no escaped-flag bit** in word 1,
  because `isapay.py` decides `TRAPS` on the truthiness of that raw word and a
  flag in it would have made an escaped row that never trapped read `TRAPS`.
  **The count stays a count on both arms**, and a row that re-faulted would be
  visible in it without having to hang first.
* **29 = RAN 12 + RIGHT 16 + WRONG 1**, so the three-way verdict of § 5
  survives the change of arm rather than collapsing to trap/no-trap: `rotr`
  reads `WRONG 00123456` here exactly as it does bare metal, which is
  `SPEC.md` `CPU-55` measured a second time at a second privilege level.

### 11.4 The header and the trailer, which are the instrument judging itself

The header is `rows`, `first`, `last`, `scratch_b`, `uc_pc_lo`, `max_sig`,
`scratch_at`, `install_rc`, `c1a_raise` and `c1b_special0e_n`; the rows are
fenced by `rows begin` and `rows end`; the trailer is `scratch_bad` and `end`.
量 on the seating: `rows=0000004b` (75), `first=00000000`,
`last=0000004a`, `install_rc=00000000`, `c1a_raise=00000001`,
`c1b_special0e_n=00000001`, `scratch_bad=00000000`, terminator present.

`bench/2026-09-15/C2-UPR.log` is the range control, on the same boot and with
its own nonce so the two captures cannot be confused: `/bin/uprobe r73 0 3`
returns four rows with `last=00000003` while `rows` still reads `0000004b`.
**A mistyped range therefore shows up in a header field rather than as a short
capture nobody questions**, which is the same shape as § 5's rule that the
payload records and decides nothing.

### 11.5 What this arm does not establish

* **One seating, one boot, and not one row repeated.** Every cell above rests
  on a single capture. Re-running `uprobe` is the cheapest repeatability
  evidence a later seating can buy.
* 🔴 **The qemu leg measures the instrument and nothing else, and that
  sentence now has a number on it**: 34 of these 75 rows disagree between the
  die and `qemu-mips-static`, in both directions. `SPEC.md` `CPU-65`. A card
  written from the emulator would have been wrong on 34 rows and right on the
  summary line by accident.
* 🔴 **`isapay verify` without `--objdump <the rsdk cross objdump>` is
  a misapplied instrument and not a result**: the host's x86 binutils decodes
  every row as `00000000` and the tool reports **75 of 75** findings. Given the
  right one it reports 0 word mismatches and 0 absent symbols over all 75 rows,
  beside **52 findings of the *binutils declines to name this encoding* kind
  — which § 3 says are a reading rather than a defect, and which
  nothing has audited.**
* ⚠️ **The device's line terminator is not the emulator's.** Every
  device line arrives `CR CR LF` where qemu writes `CR LF` (`SPEC.md`
  `FW-49`), which is why a byte prediction taken off the qemu file read 7,195
  against a capture of 7,305. The parser is unaffected — `isapay.py` folds
  every `CR` to a newline before matching — and `LOG.md` under 2026-09-15
  holds the arithmetic that closes both captures exactly.
* ⚠️ **The census this arm is compared against is not this payload.**
  § 1's join is the bridge, and **31 of these 75 rows have no census row
  under either direction of it.**

---

## 🆕 2026-09-16 (seating 24) — the first repeat of a column-② row, and it is byte-identical

`R1-pub-4a` had one bench, one boot, and no row had ever been repeated. Seating
24 re-ran it.

**`bench/2026-09-15/C2-UP.log`** (seating 23, argument `d73`) against
**`bench/2026-09-16/C2-UP.log`** (seating 24, argument `a91`), both under
rlxfw's own kernel, on different boots of different images:

* **75 `PU` rows, `cmp` IDENTICAL.**
* All eleven header fields equal, including `scratch_at = 00445d88` — the same
  address, so nothing in this userspace moves a static allocation between boots.
* `install_rc` 0, `c1a_raise` 1, `c1b_special0e_n` 1, `scratch_bad` 0 on both.

### Why it is worth anything, and what it cost to keep it that way

Both captures print `BUILD_ID` **`a87be346bb83e7f9`**, which is
`cat uprobe.c cells4.S probe4rows.h rlxasm.h | sha256sum | cut -c1-16`. **A
repeat is only a repeat if the binary is the same one**, so the `special0e` `why`
column's `C2` → `C5` correction in `tools/isa-payload.tsv` was deferred a fourth
time — correcting it regenerates `cells4.S` and moves the digest, and then the
repeat is of a different artefact.

🔴 **The deferral now has an expiry rather than a wish**: the first rebuild after
this repeat. That rebuild has not happened.

**Owner of `SPEC.md` `FW-74`.**

### 🟢 One thing the comparison establishes that neither run alone could

The two runs were given **different arguments** (`d73`, `a91`) and produced
**identical rows**. So the argument is a label carried into the banner and not a
selector over the population — which the tool's own source says, and which had
never been checked from outside.
