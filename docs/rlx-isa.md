# The Lexra RLX4181 instruction set, measured on one die

**`R1-pub-7`, desk, 2026-09-15. Written while the gate is still open, deliberately —
§ 8 is the reason, and it is a pre-registration rather than an apology.**

This is the consolidation page for everything this project has established about the
instruction set of the CPU core inside a Realtek RTL8196E, the SoC in a TOTOLINK
N150RT router. The core is a **Lexra RLX4181**: MIPS-shaped, not MIPS, and
documented by nobody in public. Every statement below was produced by running code
on one physical device, or by reading a file this repository can name.

**Every sentence carries a mark**: **量** measured on the device · **讀** read out of
code, a dump or a document · **推** inferred, pending a measurement. Mixed together
they are worth neither. `量` in this file always means *on the silicon*, never *on
this desk*; where a desk measurement is meant it says so.

---

## § 0. What this file is, and the five things it does not claim

**This file owns nothing.** Every number below is traceable to the file that owns it
— `SPEC.md` for values, `docs/` and `notes/` for the findings, `bench/` for the
captures. What it owns is the *act*: putting the instruction-set results in one
place, in an order a reader who has never seen this repository can follow, with the
control that licensed each one beside it. Where this file and an owner file
disagree, **the owner file is right and this page is stale**.

🔴 **Does not claim ① — that it is a specification of the RLX4181.** It is a
description of **one die**, in one router, with no spare. Nothing here distinguishes
*this core implements X* from *this instance of this core, at this revision,
implements X*. Where a second unit exists in this project it is a different board
and has never run any of these payloads.

🔴 **Does not claim ② — that the gate behind it is closed.** `R1-pub` has five open
steps as of this dateline. Two of its Definition-of-Done rows are unmeasured, and
§ 8 names them, says what this page will be able to say when they land, and states
what outcome would refute that. **The write-up is early on purpose.** A document
written after the evidence can only agree with it.

🔴 **Does not claim ③ — a cost.** Every *how much does the emulation cost* question
is `R1-pub-4b` (`D-cost`), which needs a clock and a seating and has not run.
§ 4 says which rows are on the surface; it does not say what any of them costs.

⚠️ **Does not claim ④ — completeness of the population.** The instruction census is
derived from this repository's own instruments — `tools/hazlint`'s `ISA_OPS` and
`ISA_TRAPS` lists and `tools/isa-probe.sh` — and is 45 census rows expanded into 75
payload encodings. An instruction nobody thought to ask about is invisible to it,
and § 10 names two families that are known to be outside it.

⚠️ **Does not claim ⑤ — that the emulator agrees.** 量 2026-09-15 at the desk:
**34 of the 75 payload rows have a different verdict on `qemu-mips-static` than on
this die** (`SPEC.md` `CPU-65`, owner `docs/emulation-surface.md` § 8.1). A page
written from an emulator would be wrong on 34 rows and its summary line would
happen to be right. Nothing below is taken from qemu; where qemu appears it is as
an instrument under test.

---

## § 1. Why the question exists at all

**An instruction set is the list of 32-bit numbers a CPU will accept, and what each
one means.** MIPS is such a list. The core in this SoC is a **Lexra** core: a
MIPS-compatible design that is not a MIPS design, carrying vendor extensions MIPS
never had and — by the public account of it — missing instructions MIPS does have.
No complete programmer's manual for it is public.

🔴 **And the public record disagrees with this die about four instructions,
which is the shortest demonstration of why the question has to be answered by
experiment.** 讀, from sources this repository already held: MIPS Technologies
sued Lexra over **US Patent 4,814,976**, which covers the four unaligned load and
store instructions `lwl`, `lwr`, `swl` and `swr`; the public account is that
Lexra's cores implement MIPS I **except** those four; the LKML patch for the
LX5280 says outright that that part does not have them; and — the part worth
knowing — an earlier trademark suit had already been settled **on the condition
that Lexra describe its products as not implementing unaligned loads and
stores**. So the public description of this core family is, in part, a
description a settlement required.

量 2026-09-14 (seating 21), with a bare-metal exception handler of this project's
own: **`lwl`, `lwr`, `swl` and `swr` all retired and all computed the expected
constant.**

⚠️ **What that establishes is narrow and is worth stating narrowly.** It is one
RLX4181 die. It does not contradict the LX5280 claim, which is about a different
part, and it does not say the description was false when it was written — a core
sold later may carry what an earlier one did not, and this project has no dated
account of which Lexra cores did. **What is measured is that the public
description says these four are absent and this die has them.**
`SPEC.md` `CPU-15`'s own closing condition, written down on 2026-08-27, was
*running one `lwl` under a bare-metal RI handler*; § 3 is that run.

So *which instructions does this chip actually execute* is a question that can only
be answered by experiment, and the answer matters in three concrete places:

* **A compiler flag.** Building this project's kernel at `-march=mips32` produces
  code this core mis-executes. § 3.1 is the first measurement, on this die, of what
  that looks like — and it is the worst shape: no fault, no warning, a wrong value.
* **A driver's atomics.** If the core has no `ll`/`sc`, every lock in the kernel is
  someone's emulation, and § 4 measures whose.
* **Every line of hand-written assembly.** MIPS-I exposes the load delay slot
  architecturally: the instruction after a load may not see the loaded value. § 5
  measures how deep that goes on this part, and finds that two vendor sources
  disagree about it and one of them is wrong.

---

## § 2. The core, named

| | | mark |
|---|---|---|
| `PRId` reads `0x0000CD01` | 量 2026-08-25b, `bench/2026-08-25b/H2a.log`, CP0 census row `0x78`. Read twice with two different primes, both returning the same value; a second channel (`H2g.log`, block words 400–402) agrees word for word. **The value was written down in `bench/2026-08-25b/PREDICTIONS-b4-block1.md` before the run and hit unchanged.** | 量 |
| `PRID_IMP_RLX4181 = 0xcd00` | 讀, `arch/rlx/include/asm/cpu.h` in the vendor's own GPL kernel drop. Bits 15:8 of the measured `PRId` are `0xCD` ⇒ the core is **RLX4181, revision 1**. `RLX5281` is `0xdc01` and is therefore **positively excluded**, not merely unproven. | 讀 |
| `Config.M = 0` | 量 2026-08-25b. `Config` (CP0 rd 16) reads `00000000`, and in the same run `nowrite = 0` over all 256 census rows proves `mfc0` always writes its destination — so that zero is a real zero. **There is no `Config1`, so this is not a MIPS32 core.** | 量 |

🔴 **Three weaknesses travel with the name and must not be dropped when it is
quoted.** ① The three GPL drops this project holds are **byte-identical** in that
header — one source read three times, not three sources. ② **No code in the vendor
port ever reads that table**, so it is a comment as far as the running system is
concerned. ③ Its own encoding scheme breaks for `0xdc01`/`0xdc02`. The name is 讀
and the value is 量, and those are different kinds of thing. `SPEC.md` `CPU-04`;
owner `notes/vendor-kernel-isa.md` § 5.

⚠️ A corroborating third-party data point exists and does **not** settle it: the
core vendor's own **LX4189** datasheet, Table 2, states that part's `PRID` reads
`0x0000c401` (讀, `SOURCES.json` `ds-lexra-lx4189`). That is a different part in the
same family, and it establishes the *shape* of the field, not this core's identity.

---

## § 3. What this die executes — 75 encodings, three verdicts

**The instrument.** `tools/rlxprobe/probe4`, a bare-metal payload delivered over
TFTP and entered from the loader prompt, with an exception handler of its own
installed at `0x80000080` and read back word for word before it is trusted. One row
per encoding. Each row carries an operand whose correct answer is a **single
computable constant**, derived at the desk and printed beside the reading rather
than compared on the device — so a row can return *does not trap and computes the
wrong answer* instead of collapsing into pass/fail.

**Three verdicts, and the third one is the point:**

| verdict | meaning |
|---|---|
| `TRAPS` | the instruction raised an exception; the `ExcCode` is printed |
| `RAN` | it retired and there is no single correct answer to compare against |
| `RIGHT` | it retired and produced the expected constant |
| 🔴 `WRONG` | **it retired and produced a different one** |

**The reading.** 量 2026-09-14 (seating 21), `bench/2026-09-14/C1-P4j.log`:

> **RAN 16, RIGHT 16, TRAPS 42, WRONG 1** — over 75 rows.

`SPEC.md` `CPU-57`; owner `docs/isa-payload.md` § 6.

**What is present**, 量: the MIPS-I baseline; `madd`, `madd_hi`, `movz`, `movn`; and
`lwl`, `lwr`, `swl`, `swr` — the unaligned family — **all `RIGHT`**.

🟢 **That last group closes a row, and it closes it against public
information.** `SPEC.md` `CPU-15` asked *does the
silicon have `lwl`/`lwr`/`swl`/`swr`*, carried the value `(未定)` with both marks
empty, and named its own closing condition: *running one `lwl` under a bare-metal RI
handler*. Its ⚠️ counter-argument was that the public Lexra account says the family
removed them and the LKML LX5280 patch says that part does not have them. **All four
read `RIGHT` on this die.** The supporting evidence it had been leaning on was 推 —
this unit's own `memcpy` uses `lwl`/`lwr` and its `do_ri` carries no emulation for
them, so *either the core has them or the device would not boot, and it boots*. That
inference is now unnecessary. ⚠️ **The refutation is about this part**, not about
LX5280 or about the family; nothing here contradicts the LKML patch's claim about a
different core.

**What is absent**, 量: MIPS-II's four branch-likely encodings (`beql`, `bnel`,
`blezl`, `bgtzl`) and all six SPECIAL-form trap instructions (`teq`, `tne`, `tge`,
`tgeu`, `tlt`, `tltu`) **all `TRAPS`** — none of them is implemented. So are `clz`,
`clo`, `mul`, `sync`, `ext`, `ins`, `seb`, `wsbh`, `rdhwr`, and all ten `udi*`
encodings.

### 3.1 🔴🔴 The one row that does not trap and computes the wrong answer

**`rotr` read `00123456` where the table expects `78123456`, with no exception.**
量 2026-09-14.

The input is `12345678` and the shift is 8. A rotate gives `78123456`. A logical
shift right gives `00123456`. The encoding is `0x00291202` — SPECIAL, with `rs = 1`,
and **that one bit in the `rs` field is the entire difference between `rotr` and
`srl`**. This core ignores it and executes `srl`.

🟢 **The value, the mechanism and the reason the row exists were all written down
before the board was powered**, in `tools/isa-payload.tsv`'s own `why` column for
that row: *a core that ignores it computes srl and answers 0x00123456, which is the
WRONG cell doing its job*. The device delivered all three.

🔴 **This is the first-hand evidence for this project's standing ban on
`-march=mips32`.** The ban's stated reason is *mips32 miscompiles silently — no
fault, no warning, just wrong values*, and until that seating it was **inherited
rather than measured on this die**. ⚠️ It is one encoding, not a claim about
`mips32` as a whole: the population is these 75 rows and `WRONG` is 1 of 75.

### 3.2 The Lexra multiply-accumulate extension is on this silicon

量 2026-09-14: the eight Lexra ASE encodings — `madh`, `madl`, `mazh`, `mazl`,
`msbh`, `msbl`, `mszh`, `mszl` — **all retired (`RAN`) with sane values**. They are
not MIPS at any level; they are the vendor extension this core family was built
around. `SPEC.md` `CPU-57`; owner `docs/isa-payload.md` § 9.

⚠️ `madd` and the Lexra `mad` share the word `0x70000000`, which is why the payload
carries both under separate names and why binutils' answer for that word depends on
which patch set it was built with (讀, `docs/toolchain-prior-art.md` § 7 item ⑤).

### 3.3 What the decoder said about itself, twice, unprompted

🟢 **A refuted pre-registration, and its refutation is a positive identification
rather than an absence.** `pref` (`0xCD400000`) was registered as `run`. It
**TRAPPED**, `cause = 3000002c` — **`ExcCode 11` (CpU), `CE` 3**. MIPS32's `pref` is
a hint with no coprocessor field and cannot raise CpU; MIPS-I's `lwc3` can, and its
`CE` names coprocessor 3. ⇒ **opcode `0x33` decodes as `lwc3` on this die, and
MIPS32's hint is not implemented.** 量 2026-09-14.

🟢 **The FPU access encodings split across two different exceptions**: `mfc1`,
`lwc1`, `swc1` raise `ExcCode 11` (CpU) while `ldc1`, `sdc1` raise `ExcCode 10`
(RI). 量. And `mfc2` (`0x48020000`) traps with `CE` 2 — the first time this project
has looked at CP2 on this part.

🟢 **`mflxc0` retired while every real CP3 access — `mfc3`, `mtc3`, `cfc3`, `lwc3`,
`swc3` — trapped with `ExcCode 11`**, in the same capture. That confirms this
project's own 2026-09-04 correction: `mflxc0`/`mtlxc0` are **not** `mfc3`. They are
COP0's opcode with the MIPS-unassigned `rs` values 3 and 7 — built words
`0x40620000` and `0x40e20000`, against `mfc3`'s `0x4c020000` — a **third**
coprocessor register file. 讀 ＋ 量; owner `docs/interrupt-map.md` § 1.1.

⚠️ 🔴 **`ll` reading `RIGHT` does not prove `ll` exists.** Opcode `0x30` is `lwc0`
in MIPS-I and only becomes `ll` at MIPS-II (讀, `SPEC.md` `CPU-49`, verified against
binutils 2.42's `mips:3000` decoder over `probe4`'s own built artefact). The
three-way verdict separates them for free — `ll` writes the GPR and reads `RIGHT`,
while `lwc0` writes a CP0 register and leaves the GPR at its seed, reading `WRONG` —
and the reading was `RIGHT`. **What that establishes is that the encoding did not
trap and the right word reached the register. It says nothing at all about
atomicity**, which no row in this census asks.

### 3.4 The controls that make a zero mean something

A census whose entire output is a column of verdicts can fail in a way that looks
like a result. Two controls are mandatory and both are in the same capture, on the
same boot:

* 🟢 **Positive (`D2b`).** The seven MIPS-I baseline encodings — `add`, `lw`, `sw`,
  `mult`, `mult_hi`, `beq`, `jr` — must all read `RIGHT`. They did. Without this,
  a payload that never executed anything would look like a core that implements
  nothing.
* 🟢 **Negative (`D2`).** The reserved encoding `special0e` must trap with
  `ExcCode 10` (RI). It did. Without this, *no trap* and *the handler is broken* are
  the same observation. **The gate's own wording is that any control which does not
  fire voids the whole table rather than part of it.**

And the reading is licensed in a third way: in the same run, four `cache` op values
retired with `n = 0`, so *did not trap* is a reading rather than a dead processor.

**Three independent channels.** The 75 rows arrived over the UART, were read back a
second time through the loader's `DW` command word for word, and are covered by a
checksum computed on the device (`seal = AF7A728B`) that agrees on all three.

---

## § 4. What the kernel emulates, and the one row where you can see it

An instruction that the hardware does not implement can still work, because the
operating system can catch the exception, do the work itself, and return as though
nothing happened. The set of instructions for which that is true is the **emulation
surface**, and it is invisible to any program that does not go looking.

**What the vendor's kernel emulates**, 讀 over `arch/rlx` in the GPL drop:
`do_ri()` at `arch/rlx/kernel/traps.c:546` calls `simulate_llsc` under
`#ifndef CONFIG_CPU_HAS_LLSC` and `simulate_sync` under `#ifndef CONFIG_CPU_HAS_SYNC`;
`simulate_rdhwr`'s two call sites are `#if 0`'d **by the vendor** (mainline `arch/mips`
calls it unconditionally); there is **no `math-emu` directory under `arch/rlx` at
all**, with `arch/mips/math-emu` and `arch/x86/math-emu` present as the control that
`ls` was looking in the right place; and `do_cpu` handles `cpid == 0` only, giving
`SIGILL` for every other coprocessor. `SPEC.md` `CPU-47`; owner
`notes/vendor-kernel-isa.md` § 1.4.

**The measurement.** The same 75 encodings were run a second time — as an ordinary
Linux userspace process, under **this project's own kernel**, with a `SIGILL`
handler. 量 2026-09-15 (seating 23), `bench/2026-09-15/C2-UP.log`:

> **RAN 12, RIGHT 16, TRAPS 46, WRONG 1** — and the frozen card
> `bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.3, committed at `9874012`
> **before the board was powered**, carries that line word for word.

`SPEC.md` `CPU-64`; owner `docs/emulation-surface.md` § 3 / § 4 / § 8.

**The surface is one row.** 量:

* 🟢 **`sync` is the whole visible surface.** On bare metal it raises `ExcCode 10`
  (RI). In user mode it returns silently — `do_ri` reaches `simulate_sync`, SPECIAL
  funct `0x0F` matches, and the process never learns. **A difference between the two
  columns in trap/no-trap is exactly what an emulated instruction looks like, and
  this is the only row that shows one.**
* ⚠️ **`ll` and `sc` are emulated and *invisible*.** They already retire on this die,
  so both columns read *no signal*. The kernel's emulation is real and unobservable
  **in the verdict**.

🔴🔴 **And that last sentence is exactly as narrow as it has to be, because `sc`'s
*value* is not invisible — found 2026-09-15, by an instrument built to confirm the
table rather than to add to it.** The payload records one scratch word per row, and
for `sc` that word is seeded `A5A5F00D` by `tools/isa-payload.tsv`'s own `mem0`
column — **one table, one seed, and the user-mode probe links the same `cells4.S`
bytes**, so the two arms start from the same value by construction rather than by
coincidence. 量:

| | ① bare metal, `CU0 = 1` | ② Linux user mode |
|---|---|---|
| verdict | `RAN` | `RAN` |
| the scratch word | **`5A5A0FF2`** — the value in `rt` | **`A5A5F00D`** — the seed, untouched |

**On the die the store happened. Under Linux it did not.** 讀, the same table's own
`why` column for that row, written long before either reading: *without a preceding
`ll` to the same address a correct `sc` has an unspecified outcome* — and this
payload has none, because `ll` and `sc` are separate rows with separate scratch
words. So what is measured is the **direction**: the die stored where the kernel's
emulation refused, and **the die is the permissive one**.

⚠️ **This payload cannot say why.** *No link semantics at all* and *link semantics
with no address check* both predict what the die did, and nothing here separates
them. ⚠️ And it does not make § 4's headline wrong: *invisible* was a statement
about the **verdict**, and as a verdict surface this is still one row. **As a value
surface it is two.** `ll` is identical on both arms in both senses.

🟢 **The instrument that found it is `tools/emupredict.py`, and it found it by being
made falsifiable.** The tool derives column ② from column ① by the rule set alone;
its case `C21` asserts that every rule-covered row carries the same value on both
arms, which is a claim that can fail — and the one row that fails it is `sc`.
* 🔴 **`cache`×4 and `mflxc0` are a *privilege* artefact, not emulation.** They move
  from retiring to `SIGILL`, but column ① was taken with `Status.CU0 = 1` and column
  ② is user mode. Reading those five rows as emulation would be the single easiest
  mistake to make here, and `docs/emulation-surface.md` § 2 puts the confound before
  the table for that reason.

🔴 **The refutation condition was written first and did not fire.** It was *`sync`
reads `SIGILL`*. It is struck through in place in `docs/emulation-surface.md` § 4
rather than deleted, on the stated ground that a refutation condition quietly
removed once it fails to fire was never a refutation condition.

🟢 **The 31 payload rows outside the census were registered as one rule, not a
table.** Before power: **R-a** ① retired ⇒ ② the same verdict and value, no signal ·
**R-b** ① `ExcCode 10` ⇒ ② `SIGILL`/`SI_KERNEL` · **R-c** ① `ExcCode 11` with
`CE ≠ 0` ⇒ ② `SIGILL`/`SI_KERNEL`. **All 31 held.** A rule is the stronger form:
thirty-one independent chances to fail, and no way to repair it row by row after the
reading, which a 31-row table would have allowed.

⚠️ **One seating, one boot, no row repeated.** Every cell of column ② rests on a
single capture. ⚠️ **And of the eight instructions known to be on the surface, this
table can see three** — `ll`, `sc`, `sync`. The unaligned five (`lh`, `lhu`, `lw`,
`sh`, `sw`) have **no census row**, a population defect declared where it was found
and deliberately not repaired there.

---

## § 5. The load delay slot, and how deep it goes

On MIPS-I the instruction immediately after a load is **architecturally not
guaranteed** to see the loaded value. Whether a given implementation interlocks
anyway is unspecified — so it is a property of the silicon, and it is the one this
project's build rules are written around.

**The instrument.** `tools/rlxprobe/probe5`: 24 rows over 10 families. Each row is a
*sequence*, not a single instruction, and each computes a value that **differs**
under interlock and without — never a signal test. The reading is the *distance* at
which the consumer stops seeing the stale value. Every row carries two expected
constants: the interlocked one (which the ISA specifies) and the exposed one (which
is a hypothesis about this implementation).

🔴 **Its build gate is inverted, and that is the point.** For `probe5`,
**`tools/hazlint` exiting 0 is a build failure** — a hazard payload with no hazard
violation in it is a payload the compiler has already fixed. `tools/hazdecl.py`
adjudicates unmodified `hazlint`'s output over the whole image in both directions,
twelve checks. Owner `docs/isa-hazard.md` § 4.

**The reading.** 量 2026-09-14 (seating 21), `bench/2026-09-14/C1-P5j.log`:

> **LOCK 15, OPEN 6, VOID 3** — over 24 rows. `SPEC.md` `CPU-54`.

**The ladder**, 量 — the distance at which each family closes:

| family | closes at |
|---|---|
| `loaduse` | **d1** |
| `storedata` | d1 |
| `storebase` | d1 |
| `hilo` | **d0** — no exposure at any distance |
| `movcond` | d1 |
| `movrd` | **d0** |
| `dslot` | d1 |
| `cp0` | 🔴 **every rung `VOID`** — see § 6 |

🟢🟢 **The headline is the `d1` cell, and it adjudicates between two vendor
sources.** `lu_alu_d0` read **OPEN** (`B10CB10C`, `$9`'s previous value) — hitting a
pre-registration whose source was the *upstream* reverse-engineering project's
`P9-12` `T-89`/`T-90` and **not** this repository's, so it is the first independent
acquisition of that fact by this project's own instrument. `lu_alu_d1` read
**LOCK** (`A5A5F00D`), so **load-use closes at one instruction**. That row's device
prediction was deliberately left blank, because two vendor sources contradict each
other: **upstream's `P9-12` v2 fixes it with two `nop`s; rsdk 1.3.6 under
`-fuse-uls` emits one.** 🔴 **Upstream is the one that is wrong — one is enough.**
`SPEC.md` `CPU-14`.

🟢 **A cross-instrument control fired from the reverse direction.** Reading the same
device capture through the *qemu* arm's expectations produced **9 findings** — the
device and qemu disagree on 9 of the 24 rows. 🟢 **And the report length is an
equation, not an estimate**: 2,974 bytes between `*** rlxprobe` and `rlxprobe: end`,
byte-identical to the same window of the qemu run.

---

## § 6. The CP0 side, because it bounds what an ISA experiment can even ask

CP0 is the MIPS coprocessor that holds the exception state. A census that installs
its own exception handler is making claims about CP0 whether it means to or not, so
CP0 was measured first. 量 2026-08-25b, `bench/2026-08-25b/H2a.log`, via 256 stubs
covering rd 0..31 × sel 0..7. Owner `docs/rlx-cache-and-cp0.md`.

* 🔴 **There is no select field.** `moves = 8`, and all eight are rd 1's eight
  selects — that is `Random`, which moves on its own. **This core ignores `mfc0`'s
  bits 2:0.** `SPEC.md` `CPU-36`.
* 🔴 **Reading an unimplemented CP0 register returns 0 and does not trap.**
  `traps = 0` over all 256 rows. Architecturally this is UNDEFINED; this part's
  choice is now measured. `SPEC.md` `CPU-37`.
* 🟢 **`mfc0` always writes its destination.** `nowrite = 0` over all 256. Every row
  is read twice with two different primes (`0xC0DE00nn`, `0xD1CE00nn`), so *`mfc0`
  retired but did not write `rt`* has a state of its own and it never appeared.
  **This is the cell that turns every other zero into a real zero**, and it is the
  answer to an adversarial audit's must-fix item. `SPEC.md` `CPU-38`.
* 🔴 **`Count` (CP0 9) is not implemented**, and neither is `Compare` (11). A SoC
  timer driver is therefore a **prerequisite** for this project rather than a bonus,
  and the instruction census lost its first candidate timing route.
  `SPEC.md` `CPU-42`.
* 🔴 **`mtc0 $x, $14` does not write.** 量 2026-09-14: `probe5`'s `cp0` family read
  `VOID` at all three distances, with the control word reading `80500270` — neither
  the value written nor the previous one. **That value is identified rather than
  guessed**: disassembling the whole image, it is the address of the `break`
  instruction itself, and there is exactly one `break`. `SPEC.md` `CPU-56`.
* 🟢 **`rfe` pops the KU/IE stack correctly** — `status_end == status == 0x1000FC00`,
  bit for bit, against a derivation written before the run. `SPEC.md` `CPU-41`.

**Caches and local memories**, because § 8's open row is here:

* **I-cache: 16 KiB, 16-byte lines, two-way.** 量, by an eviction walk that needs no
  cache isolation, with both refutation controls firing. The two-way half has a
  second, independent route: at the walk's boundary point the victims that miss on
  re-execution arrive as **ten `{k, k+256}` pairs with no singleton**, a shape
  direct-mapped cannot produce although it predicts the same *count*.
  `SPEC.md` `CPU-25`; owner `docs/probe3-cells.md`.
* **D-cache: 8 KiB** — 讀 only, from the part datasheet's own first page. **Its
  capacity has never been measured.** § 8 is where that goes.
* 🔴 **There is a local scratchpad beside the caches: I-MEM 16 KiB, D-MEM 8 KiB**
  (讀 ×2 — the datasheet, and this unit's own kernel writing `+0x3FFF`/`+0x1FFF`
  into four CP3 registers at boot). **I-MEM is the same size as the I-cache and
  D-MEM is the same size as the D-cache**, and the core vendor's LX4189 manual § 5.2
  says the I-cache serves that region only while IMEM is *disabled*. ⚠️ **So a
  measurement of "size" cannot, by itself, separate a cache from a scratchpad of the
  same size.** `SPEC.md` `CPU-46`.
* 🔴 **`Status.IsC` does not isolate on this part** — its byte stores reach DRAM.
  That is the path this SoC's Linux uses and its own bootcode never does.
* 🟢 **CP3 is reachable on this part**, where the emulator traps every `mfc3`.

---

## § 7. What the vendor's own toolchains believe about this core

A binary that avoids an instruction is evidence about the compiler that produced it,
not about the hardware that runs it. But a compiler that *changes its behaviour per
`-march`* is evidence that someone with the specification made a decision, and that
is readable. Owner `docs/toolchain-comparison.md` and `notes/vendor-toolchains.md`.

* 🔴 **The vendor's compiler pads load delay slots for `-march=4180/4181/5181` and
  not for `5280/5281/4281`**, and the rsdk-1.5.5 assembler warns on exactly the first
  set while 1.3.6 has no checker at all. 讀. Two independent implementations drawing
  the same line — and `notes/vendor-toolchains.md` § 8 says explicitly why that is
  **one vendor decision read twice**, not two sources.
* 🔴 **`-fuse-uls`, the flag that controls unaligned-load emission, is in no drop's
  build system.** It is injected by the rsdk-1.5.5 *wrapper* and by neither 1.3.6
  wrapper — so it separates toolchain **generations**, not releases. 讀.
* 🔴 **The padding follows the flag, not the release, and the ELF header cannot tell
  them apart.** 量 at the desk, `docs/toolchain-comparison.md` § 5b.
* 🟢 **`mflxc0`/`mtlxc0` assemble at `rlx4181`, `rlx4281`, `rlx5181`, `lx5280` and
  `rlx5281`, and are rejected at `lx4180` and at `mips32`.** 量 on the rsdk
  assembler. These are the instructions this project's interrupt code uses to mask a
  LOPI interrupt and the only way to reach `ESTATUS`/`ECAUSE`/`INTVEC`/`CCTL`. **So
  the `mips32` ban is not only about wrong values: at `mips32` the interrupt-mask
  primitive does not build.** That is the second, non-silent reason, and it is
  independent of § 3.1.

---

## § 8. 🔴 What is NOT measured — and this section is a pre-registration

This page is being written with `R1-pub` open. That is deliberate and it costs
something, so it has to buy something. What it buys is this section: **for each
still-open row, what this page will be able to say when the measurement lands is
written down now, before it is taken, together with what would refute it.** When
those seatings run, this page is either **cashed** or **struck in place**. A
write-up composed afterwards can only agree with its own evidence.

### 8.1 The D-cache capacity — `R1-pub-3` slot 2

§ 6 records the D-cache as **8 KiB, 讀 from the datasheet, never measured**. The
experiment is already specified (owner `docs/rlx-cache-and-cp0.md`): a `t-hit` walk
repeated at footprints of **1, 2, 4, 8, 16 and 32 KiB** with `passes` scaled so the
load count is constant, plus a KSEG0 → KSEG1 → KSEG0 sequence.

**推, registered now:** the per-load cost stays at the hit floor through 8 KiB and
rises toward the miss cost above it, so **the knee lands at 8 KiB and confirms the
datasheet's number by measurement for the first time**.

**Refuted if** the cost is flat across all six footprints, or rises immediately, or
the knee lands anywhere other than 8 KiB.

🔴 ⚠️ **And this page registers a confound that the experiment's own specification
does not mention.** § 6 records that **D-MEM is also 8 KiB**, and that the core
vendor's manual makes the scratchpad and the cache serve the same region under
different conditions. **A knee at 8 KiB is therefore consistent with an 8 KiB
D-cache and with an 8 KiB D-MEM**, and nothing in the ladder as specified
distinguishes them. Whether that confound is live depends on whether the *loader*
enables D-MEM before the payload runs — this unit's own **kernel** does, at boot,
and slot 2 runs bare metal from the loader prompt. **That is a desk question and it
must be answered before the card is frozen, not at the bench.**

### 8.2 The cost of the emulation surface — `R1-pub-4b` (`D-cost`)

§ 4 establishes the surface. It does not price it. `D-cost` was scoped at
*"roughly four rows of forty-five"* before `4a` ran.

**推, registered now:** `4a` measured the *visible* surface at **one row** (`sync`),
with `ll`/`sc` emulated but already retiring on this die. So **`D-cost` will find
exactly one row with a measurable cost**, and the estimate of four will turn out to
have been an upper bound taken before the surface was known.

**Refuted if** more than one row shows a cost, or if `sync`'s cost cannot be
resolved against the chosen ruler (`TC0CNT` read through this project's own `/proc`
file), in which case the ruler and not the surface is what the seating measured.

### 8.3 The three-toolchain comparison — `R1-pub-6`, desk half

The silicon row is done; the desk half is not. Its DoD says the choice, if one is
made, is **made by the table**. **推:** the table will select one toolchain and the
selecting criterion will be the one already written (`hazlint` clean over the whole
`libc.a`), not a new one. **Refuted if** a new criterion has to be introduced to
break a tie — which would mean the table was chosen to fit a decision already made.

### 8.4 What closing the gate adds, and what it removes

When `R1-pub` closes, `docs/GATE-RESULTS.md` gains its **ninth** entry — one line,
three claims that stand, and what the gate did not establish — and its operating
clause is re-run over nine entries. 🔴 **That entry is not written here and must
not be**: that file's contract is *one entry per closed gate*, and `R1-pub` has five
open steps as of this dateline. Writing it now would be a claim that the gate
closed.

---

## § 9. How to check any of it, from a clone

Nothing above asks to be believed. Each group of claims names an instrument, a
capture committed in this repository, and the command that re-derives the reading
from it.

| § | the claim | the instrument | the capture |
|---|---|---|---|
| 2 | `PRId`, `Config.M` | `probe1`/`probe2` CP0 census | `bench/2026-08-25b/H2a.log`, `H2g.log` |
| 3 | the 75-row census | `tools/isapay.py verdict` | `bench/2026-09-14/C1-P4j.log` |
| 4 | the emulation surface | `tools/isapay.py verdict --arm user --elf` | `bench/2026-09-15/C2-UP.log` |
| 5 | the hazard ladder | `tools/hazpay.py`, `tools/hazdecl.py` | `bench/2026-09-14/C1-P5j.log` |
| 6 | the CP0 census | `tools/rlxprobe/exc.S`'s `CP0STUB` | `bench/2026-08-25b/H2a.log` |
| 7 | the toolchain rows | `tools/hazlint`, `tools/tcpay.py` | the built artefacts under `$FWRE_WORK` |

⚠️ **One command in that table will mislead you if you get it wrong**, and it is
worth stating because this project got it wrong once: `tools/isapay.py verify`
**must** be given `--objdump <the rsdk cross objdump>`. Run without it, the host's
x86 binutils decodes every row as `00000000` and the tool reports **75 of 75**
findings. That is a misapplied instrument, not a result. 量 at the desk,
2026-09-15.

🟢 **And the same discipline is applied to this project's own claims about itself.**
`tools/spec-check.py` verifies that every value in `SPEC.md` still appears in the
file that owns it, and refuses to report at all if its own eight controls do not
pass first.

---

## § 10. What could still be wrong

* 🔴 **One die.** Every 量 above is `n = 1` in the population of RLX4181 parts, and
  `n = 1` in the population of *this* part's power-ups for most rows. Seating 21 and
  seating 23 are one boot each. **No row in either census has ever been repeated.**
* 🔴 **The population is derived from this repository's own instruments**, so an
  instruction nobody thought to ask about is invisible. Two families are known to be
  outside it and are recorded rather than quietly absent: the **REGIMM
  trap-immediate** family (`teqi`, `tnei`, `tgei`, `tgeiu`, `tlti`, `tltiu`) has zero
  hits in every tool, every doc and `SPEC.md` (`SPEC.md` `CPU-60`); and **five of the
  eight instructions on the emulation surface have no census row** (§ 4).
  ⚠️ The REGIMM answer cannot be extrapolated from § 3 — those are a different
  opcode decoding a different field, and the one REGIMM encoding that *was* probed
  (`synci`, `rt = 0x1F`, unassigned in MIPS-I) **retired without raising RI**, so
  this core's REGIMM `rt` decode does not route unassigned values to RI.
* 🔴 **The core's name rests on a header the port never reads**, byte-identical
  across all three vendor drops (§ 2).
* 🔴 **Nothing here measures atomicity, ordering or coherence.** `ll` read `RIGHT`
  and `sync` is emulated; neither statement is about what either instruction is
  *for*. Whether a DMA write is visible to a cached CPU read has never been measured
  in any direction.
* ⚠️ **The emulator disagrees on 34 of 75 rows** (§ 0 ⑤). Any future row taken from
  qemu rather than from the die inherits that error rate.
* ⚠️ **`docs/emulation-surface.md` § 3's column ② covers 39 rows; the payload that
  ran covers 75; the census is 45.** Those are three populations with three
  boundaries, and § 4's summary line is over the 75.

---

**Owner files, for anything this page compresses:** `docs/isa-prior-art.md` (the
census population and what each row already had before any of this ran) ·
`docs/isa-payload.md` (`probe4`'s design) · `docs/isa-hazard.md` (`probe5`'s design)
· `docs/emulation-surface.md` (the two-column diff) · `docs/rlx-cache-and-cp0.md`
(the CP0 census and the cache model) · `docs/toolchain-comparison.md` and
`docs/toolchain-prior-art.md` (the toolchain axis) · `notes/vendor-kernel-isa.md`
(what the vendor's kernel does about all of it) · `SPEC.md` (every value, with its
own two marks and its owner).
