# The emulation surface — two columns over 45 rows, one row of difference, and the five instructions that have no row

**`R1-pub-4`'s part `4a` (`D-diff`).** Opened 2026-09-15, seventy-first
segment, at the desk. One row per census row; **column ①** is the verdict when
the encoding runs bare metal under this project's own exception handler,
**column ②** is the verdict when the same encoding is issued from Linux user
mode. **The rows where the two differ are the kernel's emulation surface** —
what Linux on a Lexra silently does for you that the silicon does not.

Cited **by id, never by `FILE:NNN`**. `CITE-2` measured eleven of thirteen
pinned line numbers already wrong before a board was powered, and this file is
new enough to start correct.

---

## § 0. What this claims, and the four things it does not

**Claims:** that for each row of `tools/isa-census.tsv` there is a bare-metal
verdict and a user-mode verdict, and that the difference set is the surface.

**Does not claim ①** anything about the **vendor's shipped** kernel. `R1C-1`
(2026-09-14) replaced the vendor kernel with rlxfw's own as column ②'s host,
on the measured ground that the two have the same emulation surface — the
derived-population argument lives in `docs/isa-prior-art.md` § 9.3 and the
checker that keeps it true is `tools/emueq.py`. Column ②'s generality rests on
that equivalence and not on this file.

~~**Does not claim ②** a cost. Every "how much does the emulation cost"
question is `4b` (`D-cost`), which needs a clock and a seating.~~ 🔄
**2026-09-16, seating 24: `4b` ran, and this file now claims four costs.** They
are in the 2026-09-16 section at the foot of this page, and `E7` there states
the gap in the same breath: the surface is **eight** entries and `4b` prices
**four**. 🔴 This project's DoD row `D4` bundled the cost into the same
sentence until 2026-09-15 and was corrected in place; a finished `4a` does not
satisfy the old wording and never could. *(That half is unchanged and still
governs — it is why `4a` and `4b` are two steps and not one.)*

**Does not claim ③** completeness over the emulation surface. It is complete
over *the census*, and § 6 is the measured difference between those two
things.

~~**Does not claim ④** that column ② has ever been measured. It has not — for
any row.~~ 🔄 **2026-09-15, seating 23: measured, all 75 payload rows, and this
paragraph expired at 20:12:38.** `bench/2026-09-15/C2-UP.log`, one power
cycle, `/bin/uprobe d73` under rlxfw's own kernel. **Column ② is 量 from here
on** and § 3's cells are what a frozen card predicted before the board was
powered — which is worth more than the same cells written afterwards, and is
the only reason the distinction was kept this carefully.

*(The sentence this replaces was accurate when written: every reading the
repository held was kernel-mode, under its own handler, at
`Status = 0x1000FC00`.)*

---

## § 1. The population, and the four decisions taken to define it

量 2026-09-15, counted from `tools/isa-census.tsv`: **46 non-comment lines =
1 header + 45 data rows**, splitting **39 `r1a` + 6 `r1b`**. The `r1` coverage
flag reads **42 `y` and 3 `.`**.

Four things had to be decided before a table could exist. They are engineering
decisions, taken here, with the alternative and the reason:

**① 45 rows, not 39.** The six `r1b` rows are hazard *shapes*, not
instructions, and a trap/no-trap harness cannot ask their question (§ 5).
Dropping them would make a clean table by deleting the part that is hard.
They stay, each carrying an explicit cell that says which question this
instrument cannot ask — which is `docs/toolchain-comparison.md` § 6's shape,
the house form for exactly this.

**② `jalx` gets a row with an EXCLUDED cell, not a blank.** 讀: MIPS16 is
implemented on this part, so a user-mode `jalx` does **not** trap — it
succeeds, and lands control in MIPS16 mode at an address a 26-bit field
chooses. That is worse than a panic, because it is non-deterministic and it
spends the power cycle. A blank cell reads as *not done yet*; an EXCLUDED cell
with its reason reads as *decided*.

**③ The five unaligned instructions are a declared gap, not a silent one.**
§ 6.

**④ This file, not `docs/rlx-isa.md`.** ~~That file does not exist and is~~
🔄 **2026-09-15: `R1-pub-7` opened that file the same day, in its own
segment.** It is `R1-pub-7`'s deliverable; creating it here would have claimed
another step's artefact. `docs/isa-prior-art.md` § 0 ④ explicitly refuses the
job of saying anything about the vendor kernel's behaviour, so the table does
not belong there either. ~~`R1-pub-7` will cite this file.~~ 🔄 **It does**:
`docs/rlx-isa.md` cites § 2, § 3, § 4 and § 8.1 rather than restating any of
them.

---

## § 2. 🔴 The confound that has to come before the table

**Column ①'s readings were all taken at `Status = 0x1000FC00`. That is
`CU0 = 1`. Column ② is user mode, where `CU0 = 0`.**

So every coprocessor-0-class encoding in the census differs between the two
columns **for a reason that has nothing to do with emulation** — it differs
because the second run is unprivileged. `cache`, `mflxc0`, `ll` and `sc` are
all in that set: on the die they retire because CU0 is set, and from user mode
they take CpU(11) with CE 0.

🔴 **A difference column that does not separate *privilege* from *emulation*
is not the emulation surface.** It is the union of two unrelated things, and
the larger of the two is an artefact of how column ① was measured. Every row
below therefore carries a **why** — `same`, `emulation`, or `privilege` — and
only the `emulation` rows are the surface.

⚠️ This was not in `R1c`'s definition anywhere. The plan, `docs/isa-prior-art.md`
§ 9 and `PROGRESS.md`'s `D4` all say *bare metal against the kernel*; none of
them says that one of those is privileged and the other is not.

---

## § 3. The table — 39 `r1a` rows

Column ① is **量**, from `bench/2026-09-14/C1-P4j.log` (`probe4`, 75 payload
rows, header `trapped=0x2a` = 42, `ran=0x21` = 33) unless noted.
Column ② was **推** when this table was written — a prediction registered here
before any harness existed — and is **量** from 2026-09-15,
`bench/2026-09-15/C2-UP.log`, seating 23. 🟢 **Every cell below was read back
as written**: the tool's own summary line over all 75 payload rows is
`RAN 12, RIGHT 16, TRAPS 46, WRONG 1`, which
`bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.3 states **verbatim** and
which was committed at `9874012` before the board had power. **No cell in this
table changed**, so § 7 ①'s *the cell stays and the disagreement is the result*
was never invoked.

🔴 **That summary line is four counts, and four counts are not thirty-nine
cells.** `RAN 12, RIGHT 16, TRAPS 46, WRONG 1` reads the same if two rows swap
verdicts, so quoting it as the evidence that *every cell below was read back as
written* is weaker than the sentence it is offered for. 量 2026-09-15 at the
desk, per row, over both captures through `tools/isapay.py verdict` —
`--arm device` on `bench/2026-09-14/C1-P4j.log` and `--arm user` on
`bench/2026-09-15/C2-UP.log`, **75 of 75 rows parsed on each side** — and
grouped back onto the census rows they realise:

* **34** of the 37 census rows that have a payload row agree between the two
  columns in the trap/no-trap sense, and `SPECIAL2`'s internal mixture of one
  `retire` and three `RI` agrees member by member;
* **`sync` alone** is die-traps-and-user-runs — the surface, one row, § 4;
* **`cache` (its four payload rows) and `mflxc0`** are die-runs-and-user-traps
  — the privilege pair, § 2;
* `jalx` and `mtlxc0` have no payload row on either side, which is rows 3 and
  32's `none` read back from the other end.

**That is the per-cell statement the summary line cannot make**, and it is what
§ 4's result rests on.

⚠️ **The two columns do not observe the same quantity, and every mechanism
clause in column ② is 讀 rather than 量.** Column ① reads `Cause.ExcCode` under
this project's own handler. Column ② is an unprivileged process: 讀
`config/rlxfw-user/isaprobe/uprobe.c`, whose per-row record is
`w[2] = (up_sig << 16) | (up_code & 0xffff)` — a **signal number and an
`si_code`**, nothing more — and nothing in user mode can read `Cause` at all.
So in every column-② cell below, `SIGILL` / `SI_KERNEL` / *no signal* is 量,
and the arrow in front of it (`CpU(11) CE 0 → do_cpu → simulate_llsc …`) is 讀,
out of the vendor's `traps.c`. **The seating measured the endpoint; the path to
it is still a reading of source**, and a different path arriving at the same
signal would be indistinguishable here.

| # | row | ① on the die | ② 量 from user mode, `C2-UP.log` | why |
|---|---|---|---|---|
| 1 | `cache` | retire (4 of 4 ops, n=0) | CpU(11) CE 0 → `do_cpu` cpid 0 → `simulate_llsc` no match → **SIGILL** | 🔴 privilege |
| 2 | `mfc3` | exc 11 CpU CE 3 | SIGILL | same |
| 3 | `jalx` | **none** | 🔴 **EXCLUDED — must not be run.** MIPS16 is implemented, so it retires into MIPS16 at an address a 26-bit field picks | — |
| 4 | `lwl` | retire, gpr `A5F00D44` | retire | same |
| 5 | `lwr` | retire, gpr `1122335A` | retire | same |
| 6 | `movn` | retire, gpr `0000002A` | retire | same |
| 7 | `movz` | retire, gpr `0000002A` | retire | same |
| 8 | `mtc3` | exc 11 CpU CE 3 | SIGILL | same |
| 9 | `swl` | retire, m0 `A55A5A0F` | retire | same |
| 10 | `swr` | retire, m0 `5A0FF20D` | retire | same |
| 11 | `COP1` | **mixed** — CpU CE 1 ×3 (`mfc1`/`lwc1`/`swc1`), RI ×2 (`ldc1`/`sdc1`) | SIGILL for all five; no `math-emu` exists under `arch/rlx` | same |
| 12 | `SPECIAL2` | **mixed** — retire (`madd`), RI ×3 (`mul`/`clz`/`clo`) | retire / SIGILL, matching ① | same |
| 13 | `SPECIAL3` | exc 10 RI (4 of 4) | SIGILL | same |
| 14 | `beql` | exc 10 RI | SIGILL | same |
| 15 | `bgtzl` | exc 10 RI | SIGILL | same |
| 16 | `blezl` | exc 10 RI | SIGILL | same |
| 17 | `bnel` | exc 10 RI | SIGILL | same |
| 18 | `ldc1` | exc 10 RI | SIGILL | same |
| 19 | **`ll`** | retire, gpr `0000A5F0` | CpU(11) CE 0 → `do_cpu` cpid 0 → **`simulate_llsc` MATCHES opcode `0x30` → emulated, no signal** | 🔴 emulation, **invisible** |
| 20 | `lwc1` | exc 11 CpU CE 1 | SIGILL | same |
| 21 | `lwc3` | exc 11 CpU CE 3 | SIGILL | same |
| 22 | `madd` | retire, LO `13526780` / HI `0BAD0002` | retire | same |
| 23 | `mfc1` | exc 11 CpU CE 1 | SIGILL | same |
| 24 | `pref` | exc 11 CpU CE 3 (the die names `0x33` as MIPS-I `lwc3`) | SIGILL | same |
| 25 | `rdhwr` | exc 10 RI | SIGILL — `simulate_rdhwr`'s two call sites are `#if 0` and **the function is not defined in this tree** | same |
| 26 | **`sc`** | retire, m0 = rt's value | CpU(11) CE 0 → **`simulate_llsc` MATCHES opcode `0x38` → emulated, no signal** | 🔴 emulation, **invisible** |
| 27 | `sdc1` | exc 10 RI | SIGILL | same |
| 28 | `swc1` | exc 11 CpU CE 1, m0 unchanged | SIGILL | same |
| 29 | `swc3` | exc 11 CpU CE 3, m0 unchanged | SIGILL | same |
| 30 | **`sync`** | exc 10 RI | `do_ri` → **`simulate_sync` MATCHES SPECIAL funct `0x0F` → emulated, no signal** | 🟢 **emulation, VISIBLE** |
| 31 | `mflxc0` | retire, gpr `00000000` from a `DEADBEEF` seed | CpU(11) CE 0 → `simulate_llsc` no match → SIGILL | 🔴 privilege |
| 32 | `mtlxc0` | **none** — never given a payload row, deliberately | SIGILL, by the same argument as `mflxc0` | — |
| 33 | `COP2` | exc 11 CpU CE 2 | SIGILL | same |
| 34 | `teq` | exc 10 RI — condition deliberately TRUE, and ExcCode 13 (Tr) was reachable | SIGILL | same |
| 35 | `tge` | exc 10 RI | SIGILL | same |
| 36 | `tgeu` | exc 10 RI | SIGILL | same |
| 37 | `tlt` | exc 10 RI | SIGILL | same |
| 38 | `tltu` | exc 10 RI | SIGILL | same |
| 39 | `tne` | exc 10 RI | SIGILL | same |

量 counts over column ①: **11 retire, 9 CpU(11), 15 RI(10), 2 mixed, 2 none,
0 void.** Non-`none` = 37; with the five `r1b` rows that have a route-① reading
(§ 5) that is **42**, which is exactly the census's own 42 `y` flags —
derived independently from the raw logs and from the flag column, and they
agree.

🔴 **A disagreement, reported rather than resolved.** `mfc3` reads CpU CE 3 at
`Status = 0x1000FC00` (CU3 clear), and a different 2026-08-30 payload that set
and held CU3 read **retire, eight times, `traps = 0`**. Both are in the record.
Route ① as scoped here is the `0x1000FC00` reading, and the other one is why
row 2's cell says nothing about whether CP3 holds a register.

---

## § 4. 🔴 The result the table produces, and it is one row

Of 39 census rows, ~~**exactly one — `sync` — is predicted to show the
emulation surface as a trap/no-trap difference.**~~ 🔄 **2026-09-15: exactly
one — `sync` — does show it**, and the difference set was re-derived row by row
rather than read off the summary line (§ 3).

🟢 **量 2026-09-15, seating 23, and the prediction held: `sync` read `RAN` —
no signal.** It takes `ExcCode 10` on the die and returns silently from user
mode, so `do_ri` reaches `simulate_sync`, SPECIAL funct `0x0F` matches, and
**the emulation surface is visible on this part**. The ⚠️ at the foot of this
section named `SIGILL` as the outcome that would have refuted § 1.4's whole
reading — that is `notes/vendor-kernel-isa.md` § 1.4, where the surface is
enumerated, and **not** § 1 ④ of this file; it did not happen.

`ll` and `sc` are emulated in user mode and the test **cannot see it**: they
already retire on the die, so both columns read *no signal* and the difference
is invisible to the instrument. It is real and it is in the mechanism column,
which is why every row carries a *why* rather than only a verdict.

🔴🔴 **That sentence is about the VERDICT, and it has to be, because `sc`'s
VALUE is not invisible.** 量 2026-09-15 at the desk, found by
`tools/emupredict.py`'s `C21` — a case that asserts every rule-covered row
carries the same value on both arms, and therefore a case that can fail:

| | ① bare metal, `CU0 = 1` | ② Linux user mode |
|---|---|---|
| verdict | `RAN` | `RAN` |
| the scratch word (`read = m0`) | **`5A5A0FF2`** — the value in `rt` | **`A5A5F00D`** — the seed, untouched |

The seed is `tools/isa-payload.tsv`'s own `mem0` column for that row, and
`uprobe` links `cells4.S` verbatim, so **the two arms start from the same value
by construction and not by coincidence**. So on the die the store happened and
under Linux it did not.

🟢 **And the table already says why the two are allowed to differ**, in the
same row's `why` column, written before either reading: *without a preceding
`ll` to the same address a correct `sc` has an unspecified outcome*. This
payload has none — `ll` and `sc` are separate rows with separate scratch words.
**So what is measured is the DIRECTION: the die stored where the kernel's
emulation refused, and the die is the permissive one.**

⚠️ **This payload cannot say why.** *No link semantics at all* and *link
semantics with no address check* both predict what the die did, and nothing
here separates them. A row that reads `rt` after the `sc`, or an `ll` to the
same scratch word immediately before it, would.

⚠️ **It does not make the yield sentence below wrong.** As a **verdict**
surface this is still one row. **As a value surface it is two**, and `ll` is
identical on both arms in both senses. `SPEC.md` `CPU-66`.

`cache` and `mflxc0` differ, and **not because of emulation** — they differ
because column ① was privileged.

> **So `D-diff`, run over this population, yields a one-row surface with two
> invisible entries and two privilege artefacts.** That is the honest yield,
> it is known before a board is powered, and it is the strongest possible
> argument for § 6's population gap.

~~⚠️ 推 throughout. If the seating reads `sync` as SIGILL, `simulate_sync` is
not reached from this path and the whole § 1.4 reading is wrong — that is the
single most informative outcome available, and it is worth the seating on its
own.~~ 🔄 **2026-09-15: 量 throughout, and the yield is
exactly the sentence above.** All four legs read as predicted in one capture:
`sync` `RAN`; `ll` `RIGHT` `0000A5F0` and `sc` `RAN`, both **invisible**
because they already retire on the die; `cache10`/`11`/`15`/`19` and `mflxc0`
all `SIGILL`/`SI_KERNEL`, which is the **privilege** column and not the
emulation one.

🔴 **The value of this section is that the yield was small and was said so
first.** A one-row surface is a thin result, and the thin result was written
into a frozen artefact before power rather than discovered afterwards and
dressed up. *(The refutation condition it carried — "if the seating reads
`sync` as SIGILL, the whole § 1.4 reading is wrong" — is kept above, struck
rather than deleted, because a refutation condition that is quietly removed
once it fails to fire was never a refutation condition.)*

🔴 **And that sentence was false for three commits, in the section that
states the rule.** 量 2026-09-15, `git show` on this file's first commit
`cbd1d0d` against `0ff8c3c`: the seating's edit struck the three words
`⚠️ 推 throughout.` and **deleted the refutation condition itself**, leaving the
parenthetical above to assert that a sentence was kept which was not on the
page. `SPEC.md` `CPU-64` (*那個條件原樣留在 `docs/emulation-surface.md`
§4,劃掉而不刪掉*) and `R1-pub-7`'s `docs/rlx-isa.md` (*struck through in
place in `docs/emulation-surface.md` § 4*) both describe this file by that
sentence, so **three files asserted it and none of them was checked against
the page** — the two consumers because they were quoting a local view of it,
and this one because a file cannot notice its own omission. The condition is
restored above, verbatim from `cbd1d0d`.

⚠️ **No checker in this repository can see this class of defect.**
Strike-through is prose; nothing joins a claim that some text was kept to the
text itself, and `spec-check`, `citecheck`, `xcheck` and `ledgerscan` were all
green over this file while the sentence was false.

---

## § 5. The six rows this instrument cannot ask

The `r1b` rows are `load then a reader of the loaded register`, `mtc0 then
mfc0`, `mult/div then mfhi/mflo`, `a load sitting in a delay slot`, `movz or
movn write-enable in a load delay slot`, and `store, the class hazlint has no
rule for`.

Their verdict vocabulary is **exposed / not exposed / not measurable** — a
question about whether the pipeline hazard is architecturally visible. A
SIGILL harness reads *did a signal arrive*, which is a different question with
a different answer set. 🔴 **Nothing in the repository had decided what these
six rows do in a trap/no-trap table**, and the count `45` was quoted without
anyone noticing that six of the rows have no cell to fill.

They keep their rows and their column-① readings; column ② carries **`n/a —
different question`** with a pointer here. Giving them a real column ② needs a
second instrument, and that is not `4a`.

---

## § 6. 🔴 Five of the eight instructions on the surface have no row, and cannot have one

讀, the emulation surface as `docs/isa-prior-art.md` states it: `ll`, `sc`,
`sync`, **and the unaligned `lh`, `lhu`, `lw`, `sh`, `sw`**.

量 2026-09-15, by name against `tools/isa-census.tsv`:

| instruction | on the surface | has a census row |
|---|---|---|
| `ll` | yes | **yes** |
| `sc` | yes | **yes** |
| `sync` | yes | **yes** |
| `lh` `lhu` `lw` `sh` `sw` | yes | 🔴 **no, all five** |

**And they cannot have one by rule.** `docs/isa-prior-art.md` § 0's *"does not
claim ②"* excludes any instruction the loader obviously executes, and a Lexra
loader executes `lw` on every other line. So the census's own admission rule
removes five of the eight instructions the table exists to expose.

**This is a population defect, not a table defect**, and the population is
`R1-pub-0`'s. It is declared here rather than repaired here because widening
the census would move a table two frozen artefacts join against. What `4a` can
do is say the number out loud: **this table can show 3 of the 8 known
emulated instructions.**

⚠️ It is also the likeliest source of the `~4` in `4b`'s row count — the cost
side has always been about a handful of instructions, and nobody wrote down
which handful or why it was not eight.

---

## § 7. What could still be wrong

1. ~~**Column ② is a prediction.** Every cell is 推 until a seating runs~~
   🔄 **2026-09-15: the seating ran and every cell held.** The rule the
   sentence carried is unchanged and still governs: *a prediction that turns
   out right is worth something only because it was written first*, and *if a
   later reading disagrees with a cell here, the cell stays and the
   disagreement is the result*. What is gone is only the word 推. ⚠️ ~~**One
   seating is one seating**: every column-② cell rests on a single capture on
   a single die, and nothing here has been repeated on a second boot.~~
   🔄 **2026-09-16 (seating 24): the repeat exists and it is
   byte-identical.** `bench/2026-09-15/C2-UP.log` (seating 23, argument `d73`)
   against `bench/2026-09-16/C2-UP.log` (seating 24, argument `a91`): **75 `PU`
   rows `cmp` IDENTICAL**, eleven header fields equal, the same `BUILD_ID`
   `a87be346bb83e7f9`. `SPEC.md` `FW-74`, and it is the first time this project
   has repeated any column-② row. ⚠️ **What the repeat does not buy**: one
   die, one image, one operator — two boots of the same unit bound this
   instrument's reproducibility and say nothing about a second part. 🟢 The
   two invocations differ in their argument and the rows do not, which is what
   makes that argument a label rather than a selector.
2. **The equivalence column ② rests on is `R1C-1`'s, not this file's.**
   ~~If `tools/emueq.py` ever goes red, every column-② cell inherits the
   doubt.~~ 🔄 **2026-09-15: narrower now that the cells are 量.** The
   readings were taken under **rlxfw's own** kernel and inherit nothing from
   an argument — a signal that arrived, arrived. What rests on
   `tools/emueq.py` is their **generality**: the claim that they also describe
   the vendor's shipped kernel, which is § 0 ①'s and not this file's. If it
   goes red the readings stand and the word *Linux* in them shrinks to *this
   image*.
3. **Two rows reach `do_cpu` on a path the obvious model misses.** 讀: from
   user mode `CU0` is clear, and `ll`/`sc` encode as `lwc0`/`swc0`, so they
   take **CpU(11)** rather than RI — and `do_cpu`'s `cpid == 0` arm carries
   `simulate_llsc`. A harness scoring *no signal ⇒ the instruction is
   implemented* would record `ll` and `sc` as present on this die, which is
   backwards. `mflxc0`/`mtlxc0` are the same shape: COP0 opcode with an
   unassigned `rs`, so `simulate_llsc` is *attempted* before SIGILL.
4. **A SIGILL probe has two failure modes before any row runs.** 讀: the
   vendor's `traps.c` rewinds `cp0_epc` before signalling, so a handler that
   simply returns re-executes forever — the harness must `siglongjmp` or
   advance `uc_mcontext.pc`; and `force_sig` sends `SEND_SIG_PRIV`, so
   `si_code` is `SI_KERNEL` and **`si_addr` reads 0**, not the faulting PC.
   Any design that identifies the faulting row by `si_addr` is dead on
   arrival.
5. ~~**The harness does not exist and its toolchain is undecided.**~~ 🔄
   **2026-09-15 (seventy-second segment): it exists, it is gated six ways,
   and it is in an image.** `config/rlxfw-user/isaprobe/uprobe.c` links
   `tools/rlxprobe/cells4.S` VERBATIM -- the same file `probe4` links -- so
   columns ① and ② are the same `.word` bytes at two privilege levels
   rather than two tables that happen to agree. `notes/userspace-probe.md`
   owns it. The toolchain was decided by `TC-05`'s already-written
   criterion, applied and measured: `rsdk-1.3.6-4181` reads 0 `hazlint`
   violations over its whole `libc.a` where the two 5281 toolchains read
   4,574 and 3,741. ⚠️ **`R7`'s gate decision is still `R7`'s** -- what
   this settles is which toolchain `R1c`'s harness uses.
   ~~🔴 **Column ② is still 推 for every row**: nothing of this has run on
   the silicon~~ 🔄 **2026-09-15, seating 23: it ran.** The clause that
   survives is the one about the emulator — `qemu-mips-static` is an
   instrument test and not a reading — and § 8 puts a number on how far
   from a reading it was.
6. ~~**`R1C-1-b`'s build gate is written down and not built.**~~ 🔄
   **2026-09-15: built, and the artefact does not meet it as written.**
   The linked binary must contain **zero `break`** -- gcc emits `break 7`
   for integer division by zero, and a `break` in the harness is an
   exception the harness did not intend. 量: it contains **two**, both
   `break 0xff` inside `__GI_abort`, which `__uClibc_main.os` pulls into
   the link. Zero needs `-nostdlib` and a hand-written `_start`,
   `rt_sigaction`, `sigsetjmp` and `siglongjmp`; that trade was declined
   because a hand-written MIPS `sigsetjmp` that saves the wrong
   callee-saved register is SILENT and this instrument is a signal
   handler. The gate is therefore **bounded rather than waived**:
   `G1` is zero in code this project wrote, `G1b` is *exactly two, both
   inside `__GI_abort`*, and a third would be red.
   🔴 And the count is taken **by opcode**, never from objdump's
   mnemonic: 量 2026-09-15 the rsdk objdumps decline to name `movz` and
   `movn` and print the raw word. `tools/elfops.py` decodes.

---

## § 8. The seating, 2026-09-15, and the two things it measured that this table could not

**Seating 23, one power cycle, budget one.** Card
`bench/2026-09-15/PREDICTIONS-B22-block21.md`, frozen at `9874012` before
power; `check-predictions` scored **14 of 14 captures after the prediction**.
The board printed `RLXFW-ID0=5ABEFD82`, the id the build computed and nobody
typed, and `PU a87be346bb83e7f9`, a digest over the probe's own four source
files — so the image and the probe each name themselves in the capture.

### 8.1 🔴 34 of the 75 payload rows disagree between the die and `qemu-mips-static`

量 2026-09-15 at the desk, before power, over
`bench/2026-09-14/C1-P4j.log` against `qemu/2026-09-15/uprobe-user.txt`.
`notes/userspace-probe.md` § 7 already said the qemu arm measures the
instrument and nothing else; **this is that sentence with a number on it**, and
it is the reason every column-② cell in § 3 is derived from column ① rather
than from the emulator.

The disagreements are not noise and they run in both directions: six trap
instructions are `SIGTRAP` under qemu and `SIGILL` here (this part implements
no trap instruction, so column ① reads RI); four branch-likely, three
`SPECIAL2`, four `SPECIAL3` and five `COP1` rows retire under qemu and trap on
the die; four `cache` rows and eight Lexra ASE multiply-accumulates retire on
the die and trap under qemu. **A card written from the emulator would have been
wrong on 34 of 75 rows and right on the summary line by accident.**

### 8.2 🟢 The 31 payload rows outside the census, predicted as ONE rule, and it held 31 times

`cells4.S` emits 75 rows; 44 are census rows with cells in § 3. The other 31 —
the seven baseline controls, `special0e`, `madd_hi`, `rotr`, `synci`, `cfc3`,
`ltw`, the eight ASE multiply-accumulates and the ten `udi*` — were registered
on the card as three arms rather than as a table:

* **R-a** ① retired (`RIGHT`, `RAN` or `WRONG`) ⇒ ② the same verdict, same
  value, no signal;
* **R-b** ① `ExcCode 10` (RI) ⇒ ② `SIGILL` / `SI_KERNEL`;
* **R-c** ① `ExcCode 11` (CpU, CE ≠ 0) ⇒ ② `SIGILL` / `SI_KERNEL`.

**量: all 31 hold.** The reason one rule covers them without a special case is
that the encodings needing `CU0` or reaching an emulator are exactly `cache`,
`mflxc0`, `ll` and `sc` — all four census rows with their own frozen cells in
§ 3. **A rule is the stronger form here**: thirty-one independent chances to
fail, and no way to repair it row by row after the reading, which a 31-row
table would have allowed.

### 8.3 What this file still does not establish, and it is the section to read last

Unchanged by the seating: § 5's six `r1b` rows still have no cell a
trap/no-trap harness can fill, and § 6's population gap is untouched — **this
table shows 3 of the 8 known emulated instructions**, because the five
unaligned ones cannot have a census row under
`docs/isa-prior-art.md` § 0's admission rule. Measuring column ② does not
widen the population it is measured over.

🔴 ~~**No cost was measured and nothing here is timed.** The surface on this
part is one row; **what that row costs is `4b` (`D-cost`), which needs a clock
and a seating and has not been opened.** § 0 ② is the standing form of this and
the seating did not touch it. A reader who leaves this file with a number
attached to `sync` took it from somewhere else.~~ 🔄 **2026-09-16 (seating
24): `4b` opened, ran, and the number attached to `sync` is now in this file,
about thirty lines below this paragraph** — **988.6 / 989.5 ns** per iteration,
on two independent boots. 🟢 **One clause survives and it is worth separating
out**: *the surface on this part is one row* is a statement about **the
census**, and it is still true, because the second priced row — `lwu2` — has no
census row and cannot have one (§ 6).

🔴🔴 **The paragraph above is struck rather than edited, because what it now
records is the defect that produced it.** The seating-24 write-up was appended
with **zero deletions**, so that paragraph and the one below it went on
asserting the opposite of the same page for as long as nobody read the page end
to end. **That is the class `CPU-64` already records against this same file** —
*three files asserted a sentence and none of them was checked against the page*
— repeated inside the same seating that recorded it. ⚠️ **And no checker in
this repository can see it**: strike-through is prose, `spec-check` reads tables
and backtick parity, and an append that contradicts a page is neither.

🔴 ~~**One seating, one boot, and no row repeated.** Every column-② cell rests
on a single capture — `bench/2026-09-15/C2-UP.log` — taken on one power cycle
on one die. `C2-UPR` is a range control on the same boot, not a second reading.
Nothing here has a repeat, a second board or a second image behind it, and
§ 7 ① is where that is carried.~~ 🔄 **2026-09-16: two of those three are
false now and the third is not.** *No row repeated* — `FW-74`, 75 rows
byte-identical across seatings 23 and 24. *One boot* — `4b`'s four costs are
each read on **two** independent boots, which is `D-cost`'s `E3` and was
over-achieved: all four rows **and** all four twins, each boot with its own
rescue, upload and `J`. ⚠️ **A second board is still what nothing here has**,
and that clause does not expire: one die is one die, and § 7 ① carries it.

⚠️ **The instrument reads signals, not exception codes.** § 3's preamble states
the bound and it governs § 4 as well: column ②'s verdicts are 量 and column
②'s *mechanisms* are 讀. This file names `simulate_sync`, `simulate_llsc` and
`do_cpu`'s `cpid == 0` arm because they were read in the vendor's source —
**nothing on the die reported any of them**, and a different path reaching the
same signal would read identically.

🔴 **This instrument cannot find a ninth emulated instruction that already
retires on the die, and *one row* must not be read as a count of what the
kernel emulates.** Over the 37 census rows with a payload row, exactly one
shows the trap/no-trap difference and all 37 were looked at — so *no second
visible one* is a real negative result rather than an absence of looking. But
the difference is invisible **whenever column ① already retires**, which is
exactly `ll` and `sc` (§ 4): an instruction the silicon implements and the
kernel also emulates reads *no signal* in both columns. So a ninth could sit
**inside this table unseen**, as well as outside it in § 6's five, in § 5's
six, or in whatever the census never admitted. **One row is what this
instrument can see in this population.**

---

## 🆕 2026-09-16 (seating 24) — the surface is PRICED, and it is a slope

`R1-pub-4b`'s instrument is `/bin/ucost`, `UCOST_BUILD_ID`
**`8403799745aeb189`**, run under rlxfw's own kernel on **two independent
boots** — `bench/2026-09-16/C2-UC.log` (boot 1) and `C2-UC2.log` (boot 2), each
boot its own rescue, upload and `J`.

Each row is a slope over four iteration counts, and each cost is **that row's
slope minus its twin's**. The twins share the memory shape, the cell prologue
and the loop, so only the probed word differs. **No fitting happens on the
board**: it emits raw snapshots and the desk recomputed both composites from
them, 64 rungs, **0 disagreements**.

### The four costs

| row | twin | boot 1 | boot 2 | agreement | verdict |
|---|---|---:|---:|---:|---|
| `sync` | `nop_a` | **988.6 ns/it** | **989.5 ns/it** | 0.09 % | **emulated** |
| `lwu2` | `lw` | **915.6 ns/it** | **915.4 ns/it** | 0.02 % | **emulated** |
| `ll` | `lw` | 5.0 ns/it | 4.8 ns/it | 4 % | native, +2 cycles |
| `sc` | `sw` | +0.2 ns/it | **−0.2 ns/it** | **sign flips** | native, indistinguishable |

The slopes fall into two clusters about **90×** apart:

```
native  : nop_a .00205  nop_b .00205  lw .00205  sw .00212  sc .00216  ll .00306
emulated: lwu2  .18513  sync  .19978              (counts per iteration)
```

**`E2`'s zero control** — two `nop` cells at two different addresses, because
`x − x` is a tool that cannot fail — is **0.001 ns/it** on boot 1 and 0.011 on
boot 2. Every quoted cost is at least 84,000× it.

### 🟢 The exception round trip on this kernel

**~900–990 ns, i.e. 366–396 cycles at 400 MHz**, measured two independent ways:
two different instructions through two different handlers, agreeing to **7.4 %**.
The dominant term is therefore the trap and the return, not the handler body.
This number did not exist in this repository before tonight.

### 🟢 `sc` costs nothing, and the evidence is the sign

A quantity that reads +0.2 ns/it on one boot and −0.2 on another is the
instrument finding zero. That is a stronger statement than either number, and it
is the reason `sc` is reported as a bound rather than as a cost.

⚠️ `ll`'s +2 cycles failed `E4`'s linearity clause on boot 2 and `sc`'s twin
`sw` failed it on boot 1 — a different row each time, which is what a threshold
inside the noise looks like. **Both are therefore reported as bounds**: neither
pays an exception, and that conclusion does not depend on either fit, because
the clusters are 90× apart.

### 🔴 `docs/rlx-isa.md` § 8.2 is REFUTED, and not by the rows it named

§ 8.2 registered *"`D-cost` will find exactly one row with a measurable cost"*,
**refuted if more than one row shows a cost**. 量: **two**, `sync` and `lwu2`,
both at the exception scale.

🔴 **The reason is in § 8.2's own sentence.** It reasoned from `4a`'s *visible*
surface — and this document's own § 481 records that the census **excludes the
unaligned forms by rule**. It was a prediction derived from an instrument that
was blind to the thing that refutes it.

**§ 8.2 is left exactly as written.** A document written before its measurement
is the rarest thing this repository has.

### 🟢 The `ll`/`sc` half, and the re-attribution

`ll` and `sc` **do not pay an exception in user mode**. So *"emulated in user
mode"* is refuted as a statement about the **executing machine**, and the source
reading is re-attributed: `simulate_llsc` exists in this kernel and, for these
two instructions on this die, is never reached.

⚠️ Narrow twice: this says nothing about kernel mode, and `ucost` times an
instruction without checking that its semantics are correct — whether `ll`/`sc`
actually implement atomicity is a different question and this cell does not ask
it.

### 🔴 `lwu2`, and the two rows of this repository that appeared to disagree

The card's § 6.6 set `SPEC.md` `CPU-15` against this document, and they are not
in conflict once two things are separated:

* **`CPU-15` is about four unaligned INSTRUCTIONS** — `lwl`, `lwr`, `swl`,
  `swr`. They execute. 量 in the same seating: `bench/2026-09-16/C2-UP.log` rows
  8, 9 and `0a` raise **no signal**, agreeing with this table's column ② for
  those rows.
* **This document's five unaligned forms are the aligned `lh`, `lhu`, `lw`,
  `sh`, `sw` at unaligned ADDRESSES.** That is an address error, not a reserved
  instruction, and `lwu2` — the same `lw` word as its twin with two added to a
  base register outside the loop — is one. 量 **915.5 ns**. **This document's
  prediction is confirmed.**

🔴 **What is still open, and it is a state difference rather than a
disagreement**: `CPU-15` was measured at the loader prompt and this under Linux
in user mode. Two states of one machine; neither refutes the other. **The
experiment that decides it is `lwu2` timed bare metal**, which needs a `probe3`
row and a seating.

**Owner of `SPEC.md` `CPU-73` (the four costs and the exception round trip), `CPU-74` (§ 8.2 refuted) and `CPU-75` (`CPU-15` and this document are about two different things).**

### ⚠️ What this does not price

The surface is **eight** entries and this prices **four**. The other four are
unpriced, and that is a declared scope limit rather than a gap —
`PROGRESS.md`'s `E7` says the number goes in the write-up rather than being
discovered by a reader.
