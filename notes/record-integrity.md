# The record's own instruments

Five committed tools check this repository's *record* rather than its device:
`spec-check`, `citecheck`, `ledgerscan`, `check-predictions` and, from
2026-09-16, `cfcensus`. Until this file they had no owner between them — each
one's reasoning lived in its own docstring, so the thing they share, which is
**how a checker of prose goes green while checking nothing**, was written down
five times in five places and nowhere as a subject.

This file owns that subject. It does not restate what any tool does; `--help`
and the docstrings own that. It owns the measured failure modes and the rules
that came out of them.

---

## 1. The failure mode, stated once

A checker of code fails loudly: the build breaks. A checker of *prose* fails
**silently and green**, because its population is a thing it computed and an
empty population is indistinguishable from a clean one.

量 2026-09-16, the seventy-seventh segment's closeout, five checkers in one
afternoon:

| | what it believed | what it was doing |
|---|---|---|
| `spec-check` `C12` | the row saying what comes next points at open work | reading nine steps of two CLOSED gates as open |
| the hazard suite's control check | every declared per-row control fires | looking at 2 of 26 declarations |
| `D-cost`'s `E5` | the ruler's identity holds on every rung | scoring one of its two conjuncts |
| a coverage sweep | 2 of 26 | the same defect one layer down |
| `tccensus` | **nothing — it printed `REFUSING`** | saying out loud that it could not check |

**The one that behaved differently is the one whose population came from
another instrument rather than from a hand-written list.** That sentence is
the reason `cfcensus` exists and it is the rule this file keeps.

---

## 2. Seven rules, each from a measurement

**R1. A population comes from an instrument, not from a list.** A hand list
cannot notice a row added after the list was written. 量 2026-09-16:
`tccensus`'s population is *every `TC-` id `SPEC.md` holds*, so three rows
added that evening turned it red the same hour; the four hand-listed checkers
beside it saw nothing.

**R2. A checker that cannot fail is a paragraph.** Every sweep needs a
positive control, and the control needs its own negative half. 量: `C8`'s
`T1` asserts the clean fixture produces **no** finding, which is what makes
`T2`–`T6` mean anything — a checker that fires on everything passes every
mutation.

**R3. A refusal is a result.** `tccensus` printing *REFUSING -- the unmutated
pair is already red, so no control below means anything* is worth more than a
green run, because on a red tree every control "succeeds" and that success
carries no information. `cfcensus` refuses on: a missing file, a section
holding two tables where one was assumed, a row that does not close with `|`,
a row with fewer fields than its header, a gate board row whose field count
differs from its header, and `spec-check` failing to import.

**R4. A count reconciles or it is a refusal.** `cfcensus` counts the raw
table lines and the parsed rows and refuses if they differ, because a parser
that silently drops three rows reports a *smaller* number and nothing about
the smallness says it is wrong.

**R5. A ratchet is per check, never a total.** § 4.

**R5b. A gate that sweeps TRACKED files cannot see a file you are adding.**
量 2026-09-16, and it cost a red CI run: `spec-check` walks `git ls-files`, so
`notes/record-integrity.md` — this file — was invisible to every local run of
the gate while it was untracked, and its two `C8` defects were reported by CI
on the commit that added it. `CLAUDE.md` already carries this for bench cards
(*a card is untracked until the freezing commit, so the gate that exists to
check the card cannot see the card*); **it is not a fact about cards, it is a
fact about every new `.md` file**. 🟢 The fix is one command and it is
measured: `git add -N <path>` puts the file in `git ls-files` (0 → 1 on a
probe) without staging its content, so the gate sees it before the commit.

⚠️ **And this rule already existed, one subject too narrow, with the same measurement.** `RUNSHEET.md`'s card-lifecycle rule 1 carries it dated 2026-09-10, with a two-armed control — the same file untracked reports 0 findings at `rc 0` and `git add`ed reports 1 at `rc 1`. **I re-derived a measurement this repository already held**, which is the failure `cfcensus` exists to make visible, committed by the segment that built it. What is new is the subject: the rule was written about bench cards and is true of every new file a sweep is meant to cover.

**R6. The number is re-derived, never copied.** 量 2026-09-16: a patch script
anchored on ninety characters quoted out of `PROGRESS.md` was REFUSED, because
the file reads `補丁的錪點` and the quotation had silently corrected the typo
to `錨點`. **The danger of a quoted anchor is not that it fails to match — a
failure is cheap — it is that a slightly different one matches the wrong
place.** Address a row by its label; a label is derived from the table and
there is nothing to mistype.

**R7. A mechanical repair checks the SHAPE of what it repairs, not only that it is unique.** 量 2026-09-17 (eighty-fourth segment): opening `R6` inserted **118 lines** into `PROGRESS.md`, and `citecheck` reported **six** committed citations rotted across **three** files — that is the measured cost of a line citation, and it is not small. The repair script applied exactly what the tool reported and asserted each old citation occurred **once on its own line**. 🔴 **It did not ask whether the citation was a single line or a RANGE.** one row held a **range**, and only its start moved — giving a citation that counts backwards:

```
before   SPEC.md:803  ->  PROGRESS.md:462-465
after    SPEC.md:803  ->  PROGRESS.md:580-465      <- counts backwards
correct  SPEC.md:803  ->  PROGRESS.md:580-583      <- both ends +118
```

🔴 **The examples above are FENCED, and that is not cosmetic.** Written as prose they are real citations to this tool, and the first draft of this rule was itself reported by `citecheck` as *counts backwards* — **the rule about broken citations, flagged as a broken citation.** Fencing is the tool's own filter class 6, so the example is excluded by the instrument rather than by weakening it. `citecheck`'s `M2` caught it on the next run. ⚠️ **The uniqueness check passed and was the wrong question**: uniqueness says *I found the right one*, and what was needed was *I know what kind of thing this is*. A repair is an edit, and an edit written from a tool's report inherits only what the report happened to print.

---

## 3. `C12`, anatomised — 量 2026-09-16, `R1z-1`

`spec-check`'s `C12` asserts that `PROGRESS.md` § Now's `Next after this` row
points at work that is not finished. It is the row `CLAUDE.md` tells every
session to read first.

**Before, on the live file: 54 step ids known, 40 closed, 14 treated as OPEN —
and four of those fourteen were really open.** Ten of fourteen wrong, on a
check whose entire subject is *is this step finished*.

| hole | mechanism | cost |
|---|---|---|
| ① | `NO-STEP-ID` was printed and was never a finding, so *deliberately empty* and *forgotten* had one output — and `T23`, which demands at least one step id on the live file, turned the second into `REFUSING to report on the file`, rc 2, the whole tool. **The file could not sit between gates without taking the checker down.** | `R1z` was opened the hour `R1-pub` closed, by a control rather than by a preference |
| ② | closure was read from a per-step `✅` only, and `R4`'s five step rows and `R1-gate`'s four carry none under headers dated `CLOSED 2026-09-02` and `closed 2026-08-26` | nine steps read as open work for two weeks |
| ③ | a step id inside struck-through text or a `*( … )*` correction is *described*, not pointed at, and `C12` counted both | the seventy-seventh segment struck a false sentence holding a closed id and `C12` counted it; a draft of the seventy-eighth named nine closed steps **while describing hole ②** and made `C12` green on ids nobody intended to point at |
| ④ | the row guard required the line to start with a pipe, two asterisks and a backtick, so `R1h-0`…`R1h-4` — whose first cells are `~~**`R1h-0`**~~ ✅` and `✅ **`R1h-2`**` — were **absent** from the map rather than misclassified | worse than misclassification: an absent id is dropped from `C12`'s own id set without a word |
| ⑤ | the id class was `R` plus a digit, so `P4b-1`…`P4b-4`, `P4a-1`…`P4a-5` and `R2a/b/d-0`…`R2a/b/d-4` were invisible | fourteen ids in three CLOSED sections; and it is why the debt gate had to be called `R1z` and not `P5` |
| ⑥ | a carried-forward row whose first cell reads ``**`cr6c` for `R9`** 🆕`` lives inside `R3`'s step-list section, and the guard accepted it | `R9` was returned as an OPEN STEP, so a `Next after this` row that merely **mentioned** that gate satisfied `C12` |

**After: 72 step ids known, 68 closed, 4 open — `R1z-1`, `R1z-2`, `R1z-3`,
`R1z-4`, and all four are real.**

🟢 **Every change was shown to make the checker stricter before it landed**,
which is `R1z`'s `D2`. Nine new cases `P23`–`P31`; **eight fail on the
implementation of the previous commit and one, `P24`, does not** — `P24` is
the negative half of hole ②, and it cannot fail on the old version because
the rule only ever *adds* closure. Both implementations were loaded into one
process and run over the same fixtures and the same live file, so the
before/after is a reading and not a claim.

⚠️ **One thing this did not fix.** `c12_blocks` selects the newest dated block
and 量 2026-09-16 the live row carried **zero** `🔄` markers, so it returned a
single block covering the whole row — the date selection four controls were
built for in the forty-fifth segment was, on the live file, a no-op. The code
is right and the data had drifted; `spec-check`'s own comment still said 28
dated blocks, measured 2026-09-08. **A rule can be correct and inert, and
nothing here measures inertness.**

---

## 4. The ratchet, and why a total is not one

A debt this gate cannot pay in one segment still has to be prevented from
growing. The shape is a baseline the finding count is compared against, red in
**both** directions: above it a debt grew, below it a debt was paid and nobody
wrote it down.

🔴 **The first version compared a total, and it was fooled within the hour by
its own segment.** 量: `R1z-1` made `spec-check` stop returning the phantom
`R9` (`L7` 1 → 0) and, in the same edit, made the `P` series visible so a
fifth unmarked step family appeared (`L6` 2 → 3). **The total stayed at 85 and
the ratchet went green**, on a run in which two different things moved.

That is this repository's own recorded trap — *a pair of wrong numbers is
self-consistent as long as the difference is right* — reproduced inside the
instrument written to prevent it. The baseline is a dict per check now, and
`U13` is the control: it moves two entries by equal and opposite amounts and
requires red.

⚠️ Why a plain gate was rejected. `cfcensus check` is red on every run until
`R1z` closes, and a step that is always red teaches a reader to stop reading
reds — this repository's own objection to a local sweep that ends in two
expected failures every time. Leaving `check` out of CI is the other failure,
recorded as `CI-3`: *nothing notices a tool with a `--self-test` that is never
in CI*.

---

🔄 **2026-09-16, `R1z-2`: a per-check COUNT is still not enough, and the
adversarial pass said so before the per-check count existed** — *a mutant that
moves two rows in opposite directions WITHIN `L1` is still invisible*. So the
ratchet now carries a second dict: `BASELINE_SIG`, a sha256 over each check's
sorted row ids, first eight hex. The count says HOW MANY the instrument
reported; the digest says WHICH ROWS.

🟢 **It fired on its first real event and showed something a count could not.**
Reverting the `Answered` widening left `L1` at 45, `L8` at 19 and `L11` at 1 —
every count matching the moved baseline while three different row sets moved
underneath them. And `L8`'s digest came back `e9fe5859`, byte-for-byte the
value it carried before the widening: the revert restored the same nineteen
rows, not merely the same nineteen.

🔴 **A hand baseline does not inherit the live digests**, and that went red on
the same run: `U12=` passes `baseline={'L1': 1}` for a two-row fixture and was
comparing it against `PROGRESS.md`'s rows. A caller that supplies counts and
not ids is testing counts. `U12sig` and `U12sig-` are the pair that keep the
layer from being a line of code nothing exercises — the same fixture, its own
freshly computed digest passing and a wrong one red.

---

## 6. The five classification fixes, and the two that this file's own rules
## refuted

量 2026-09-16, `R1z-2`. Each rule is read off the data, and each REPRODUCES the
rows that were already right before it fixes the ones that were not — that
symmetry is what separates a derived rule from a chosen one.

* **A no-owner declaration at the owner cell's head beats a gate id anywhere in
  it.** Ten cells begin `**none…`; ten of ten are genuine; five were being
  classified by a gate id scraped from the same cell's prose. `擁有者` is
  deliberately excluded — four cells begin with it and in all four it
  introduces a real owner, one of them `XNUM-1`.
* **A standing-instruction owner is one of the cell's CLAUSES, not a substring
  of it.** Eight clause-head hits: the three already classified `SEGMENT`, plus
  five. The naive reordering would have mislabelled `GPIO-1` (offset 76 of a
  669-character cell) and `UP-AUD-1` (inside `~~ ~~`).
* **Ten of the eleven `L2` rows name work that has a home under another name**,
  so `GATE_RENAME` is declared with a committed source per entry.
* **An unresolved token is reported on any row**, not only on one that resolved
  nothing — four rows were dropping six tokens against `GATE_SHAPE`'s own
  comment.
* **`L11`** reads a closure recorded in § Corrections rather than in the row.

🔴 **Two of this file's own rules then refuted two of those changes within the
hour.** `Answered` is not a closure (four of four end in an open residual; the
character carries the verdict and the word does not). And `L11`'s first form —
the id within sixty characters of a closure verb — caught a sentence about what
closing would COST; the discriminator is structural, the closure must BE the
entry's `**bold**` headline, and it is 2 of 2 with no counterexample either
way.

⚠️ **And the hint label had been lying about where it looked.** `L8` reported a
`CLOSED` at character 1,143 as *the head of the question*, because that branch
ORed a position-free word search onto two position tests. The classification
was right and only the sentence was wrong; there are two labels now.

---

## 5. What none of these instruments can see

⚠️ **Both of `cfcensus`'s populations come from one file.** It is the record
auditing itself and it is blind to a debt this project incurred and never
wrote down. That class is real and was found by hand: the seventy-seventh
segment's closeout enumerated what the segment had produced and asked who
owned each thing, and found four owner files with nothing in them — and
**none of the eight gates could see any of the four**, because `spec-check`'s
`C5` follows a *literal value* into its owner file and those rows had no
literal to follow.

`U6` is what keeps that from being a sentence nobody tests: the live file must
yield at least one open row owned by a live gate, or the census refuses. A
debt census that finds everything closed has stopped reading.

🔴 **And `SPEC.md` § 19 is outside `spec-check`'s row-level window.** 量
2026-09-16: `tools/spec-check.py` selects `1 <= section <= 16`, § 17 gets its
own handling, and § 19 — the staging section every row measured since
2026-09-14 lands in — is reached by `C1`, `C2`, `C4`, `C5` and `C7` **not at
all**. The section exists for a good reason (inserting rows higher up moved
nine frozen bench-card line references), and the cost was never stated. It is
`R1z-2`'s. 🟢 **Paid the same day**: the window is `every numbered section except the two that are not definition tables`, both exclusions asserted, and 483 rows in 17 tables are checked where 450 in 16 were. Six defects fell out of it in the hour.

### 5.1 A citation written `file:A,B,C` is checked at `A` and nowhere else — 量 2026-09-21

🔴 `citecheck` is the instrument this repository trusts to say a line-number
citation still points at what it pointed at. It has a blind spot that is one
regex wide.

量, asking the tool itself rather than reading its source and inferring:

```
>>> import citecheck
>>> citecheck.CITE_RX.findall("rtl819x-nic.c:323,891,895,898-900,908")
[('rtl819x-nic.c', '292', '')]
```

**One element.** `CITE_RX` (`tools/citecheck.py:276`) matches `file:N` and stops
at the comma; every line number after the first is not a citation as far as this
tool is concerned.

🔴 **How it surfaced, and the detail worth keeping.** `SPEC.md` `NET-61`
cited `rtl819x-nic.c:323,751,758,768,1232,1239`. 量, read back one at a time:
`751` is `return 0;`, `758` is `nic_isr`'s signature, `768` is a blank line,
`1232` is a comment about `FW-45`'s watchdog and `1239` is `{`. **Five of six had
rotted.** The same run of `citecheck` reported `0 new rot`, `8 passed, 0 failed`
— because the only number it could see was `292`, and `292` is the one that had
not moved. **The checker looked at exactly the number that was still right.**

量, the population, so this is a finding and not an anecdote: `git grep` over
tracked `.md` finds **11** citations in the comma form, carrying **32** line
numbers, of which **21 are invisible to `citecheck`**. Examples:
`include/linux/jiffies.h:43,54,58`, `net/core/dev.c:2954,3185`,
`rtl819x-nic.c:908,912-914,1383-1499`.

⚠️ **This is a scope gap, not a broken tool**, and the distinction is the
same one § 5 makes about every other instrument here: everything `CITE_RX` can
see, `citecheck` checked, and its `T26` control (an uncommitted citing line is
suspended rather than assumed stable) is unaffected. What it cannot see, it has
never claimed to see — **and that claim was never written down, which is why
five rotted citations sat under a green verdict.**

🔴 **Not fixed here, deliberately.** Widening `CITE_RX` changes the
population every one of this tool's cases is scored against, and this
repository's own rule is that a checker's population may not move without a
positive control that the new rows are really checked. That control does not
exist yet. `SPEC.md` `FW-105`; the fix is the next segment's.

### 5.1a The repair that followed it changed exactly the number the checker could see — 量 2026-09-22

`5b01d73` re-derived `NET-61`'s source column one segment later and changed
**one** number: `292` → `323`, which is the only one `CITE_RX` can see. The
four behind the comma — `891`, `895`, `898-900`, `908` — were left. 量
2026-09-22, reading the cited file **as it stood at that very commit**:
`891`/`895`/`898-900` were inside `nic_wr()` and `908` inside `nic_dw()`, the
register accessors, **not** the harvest path the row's own prose names. So
they were not rot; they were wrong when they were committed, and they had been
wrong since the segment that wrote them.

**The mechanism this section describes produced a second instance inside the
row that documents it**, and nothing reported it either time. `SPEC.md`
`NET-61`'s source column now reads
`347, 1398, 1401, 1402-1403, 1411, 1344-1386`, every one of them read back out
of today's file; the 2026-09-21 prose keeps `891…908` because that
sentence is dated.

🔴 **And `FW-105`'s own source column had been half-repaired the same way.**
It lists the five numbers measured rotted on 2026-09-21 — those numbers are the
finding's *data*, not pointers into today's file — and `5b01d73` re-pointed
`751` → `1003`, because `751` happened to be spelled with a full path and was
therefore the one number `CITE_RX` could see. `:758`, `:768`, `:1232`, `:1239`
stayed. The row's prose still read `751`. Put back, and marked
**這一處不准改號碼** the way `SPEC.md:823` already is.

### 5.1b Declaring a quotation launders it, and the baseline is a floor rather than a census — 量 2026-09-22

The oracle digests the cited row at the commit that last wrote the **citing**
line. Writing the note that says *this citation is a quotation, leave it*
edits that line, so its blame becomes today, so the citation is `STABLE` by
construction and never reaches `C3` or the baseline at all.

量 2026-09-22, over this segment's own repair: four citations were classified
as historical quotations. Three of them sit on `SPEC.md:950` — the `FW-105`
row, which this segment annotated — and after the commit all three read
`STABLE`. Only the fourth, § 5.1's own line above, was left untouched and is
the one row this repair adds to `tools/citecheck-baseline.tsv`.

**So the baseline is a floor on the declared quotations, not a census of
them.** That is the laundering hole `citecheck`'s own header states, reached
from the other side: there it hides rot that was already rot, here it hides a
deliberate declaration — and the second one is worse, because a declaration
that leaves no trace in the tool is indistinguishable from never having made
it. ⚠️ No fix is proposed here. A `QUOTED` column in the baseline would be
one, and it needs the same positive control § 5.1's own 🔴 asks for.

## 5.2 🔴 A citation can be wrong the day it is written, and `citecheck` reports it `STABLE` — five instances, 量 2026-09-22

§ 5.1 is about numbers the tool **cannot see**. This is about numbers it
**does** see, checks, and passes — because the check it runs is *has the row
at line N moved*, and a citation that never pointed at what its sentence
claims has nothing to move.

`citecheck`'s own *WHAT IT DOES NOT DO* says it first: *"It cannot tell
whether a citation was CORRECT when it was written. It compares the cited row
then with the cited row now; a citation that named the wrong line from the
start is STABLE here."* That was written as a limit. Closing `R6` walked into
five instances of it in one desk pass.

| # | citing | says | actually | state |
|---|---|---|---|---|
| ① | `PROGRESS.md:128` | `notes/nic-driver.md:2042` **逐字** *The three-run figure may not be quoted without the fourth* | that sentence is at **`:2038`** in every commit since it was written; `:2042` is the parenthetical about the first normalisation | repaired |
| ② | `docs/KNOWN-ISSUES.md:1057` | the same, 逐字 | the same | repaired |
| ③ | `bench/README.md:101` | the same, 逐字 | the same | repaired |
| ④ | `bench/2026-09-21/PREDICTIONS-B35-block33.md:369` | `rtl819x-switch.c:88-92` — the VLAN table is reached through `TACI` | that is at **`:93-97`**; `:88-92` says the driver writes nothing at boot | **frozen card, not repaired** |
| ⑤ | `SPEC.md` `NET-61` | `rtl819x-nic.c:891,895,898-900,908` are the harvest path | they were in `nic_wr()` and `nic_dw()` at the commit that published them (§ 5.1a) | repaired |

🔴 **①–③ are one sentence written into three files in one segment, and all
three use the word 逐字 — *verbatim*.** A quotation is a claim a checker can
test. **The rule they were quoting is the rule against quoting a figure
without its fourth run**, so the record's own guard against a bad quotation
arrived as a bad quotation.

🟢 **This family has an enforcer that can be bought, and `SPEC.md` `FW-109`
says why it differs from the one at `docs/GATE-RESULTS.md`'s twelve-entry
census.** ①–④ all **quote the cited text on the citing line**. The rule is
therefore checkable without semantics: *if a line carries both a quoted string
and a `FILE:NNN`, that string must occur at or near line `NNN` of that file*.
`M4` already does a narrower version of it — a `(token)` tail — over 28
citations; this widens the population to quoted strings. The four rows above
are its positive controls, and ④ is the one that proves the check has to run
over `bench/` too.

🔴 **It is not written here**, and the reason is this file's own rule twice
over: moving a checker's population needs a positive control *and* a segment
to write it in, and this segment closed a gate. What it has is the target, the
controls and the population — which is more than § 5.1's residual has had
since 2026-09-21.

⚠️ **What the enforcer would still not catch is ⑤**, and that is the useful
boundary: `SPEC.md` `NET-61` quotes nothing. It says *`891` is the pkthdr ring
read*, in prose, and only a reader who opens the file can tell that line 891
was a register write. **A citation is checkable exactly when it quotes; the
rest is reading.**

🟢 **And `M3` caught a sixth one in this very segment, before it was
committed, which is the boundary from the other side.** The session brief
handed me line **373** of `bench/2026-09-21/PREDICTIONS-B35-block33.md` for `R6-6`'s weaker
statement; I wrote it into `PROGRESS.md` and `citecheck` `C7` reported *that
line is blank* on the next run. The statement is at
`bench/2026-09-21/PREDICTIONS-B35-block33.md:374-377`. ⚠️ **And the number is
written apart from the filename above on purpose** — a sentence about a bad
citation that spells the bad citation IS one to the scanner, which
`docs/KNOWN-ISSUES.md` already records one instance of.
**`M3` sees the subset of this family that lands on a BLANK line**, which is
why five of the six above went unreported and this one did not — and it is the
cheapest reason to run `citecheck` on a dirty tree even though its baseline
rows are suspended there.

🔴 **And one that had been committed for two days, and was seen only because an
insertion moved it — 量 2026-09-23.** `docs/KNOWN-ISSUES.md`'s
`instruments/dtcheck` row cited `.github/workflows/ci.yml` at line 1163 for
`/tmp/dtvenv/bin/pip install -q dtschema`. That command was at line 1153 in
`ca1b16d`, the commit the red run it describes ran, and at line 1302 in
`23a1463`, the commit that wrote the citation; line 1163 was an unrelated
comment in both. `citecheck` called it `STABLE` for two days, because the cited
line had not changed since the citing line was written. The commit that rewrote
`CLAUDE.md` inserted 18 lines above it, and it went `ROT` — the first time any
check saw it. It now cites the step by name. **An insertion is also a
detector**: it moves a wrong citation exactly as it moves a right one, and the
content oracle then sees the move.

## 5.3 An insertion breaks the citations no checker reads — 量 2026-09-23

`citecheck` skips `bench/`, `LOG.md` and `CHANGELOG.md` (`SRCREF_EXEMPT`,
`tools/spec-check.py:561-574`). That is right, since they are records, and it
means their line-number citations are neither checked nor repairable: an
insertion above a cited line moves them with no instrument noticing.

Measured on a full clone of `f557873`: every `FILE:NNN` into `PROGRESS.md`,
classified by `citecheck`'s content oracle (replicated, and identical to
`oracle()` on all 468 scanned citations) and by **row identity** — the row's
label (step id, `D`-id, carried-forward id, § Now label) at the citing commit
against the label at that line now.

| citing files | citations | content oracle | row identity |
|---|---:|---|---|
| frozen bench artefacts | 15 | 14 `CHANGED`, 1 `STABLE` | 10 on their row, 5 moved |
| `LOG.md` | 43 | 26 `CHANGED`, 12 `ROT`, 1 multi, 4 `STABLE` | 12 on their row, 28 moved, 3 other |
| scanned by `citecheck` | 19 | 10 `STABLE`, 8 `CHANGED`, 1 `ROT` | 14 on their row, 5 moved |

**`CHANGED` is not "already broken".** Ten of the fourteen frozen `CHANGED`
citations still land on the row they name, because the row grew in place; an
insertion above them is what breaks them.

| insertion at | working citations broken | of which not repairable |
|---|---:|---:|
| line 66, above § Gate board | 23 | 13 (8 frozen cards, 5 `LOG.md`) |
| line 1787 | 7 | 3 |
| below line 2340 | 0 | 0 |

Controls: 120 lines inserted into a throwaway clone and committed. At line 66
the committed `citecheck` reported exactly the 9 new `ROT` predicted and the row
test flipped exactly 23; at the end of the file both read unchanged.

The constraint was already known for `SPEC.md`, whose § 19 exists because of it,
and was never applied here: `R1z`, `P1` and `R6` were each inserted at the top,
and 5 of the 15 frozen citations had moved before this was measured. `CITE-2`'s
answer — *maintainable by an instrument* — holds for the population `citecheck`
scans; it never held for the one it exempts.

**Rule:** new step lists go at the end of `PROGRESS.md`, and new text cites rows
by id. The enforcer, and a resolver that reads a frozen line citation against
the file as it was at the card's commit, belong to `R1y`.

## 5.4 Owner columns nothing checks — 量 2026-09-23

* `SPEC.md` § 17's `owning gate` column, resolved against § Gate board (eight
  fixtures, all classified correctly): 70 open rows; **51 name only closed
  gates** (23 of them `R6`), 14 name no gate, 4 a live gate, 1 unresolved.
  `spec-check` checks that an open value appears in § 17, not that its owner
  is alive, and `cfcensus` reads only `PROGRESS.md`.
* `PROGRESS.md`'s generated census block read `ORPHAN 0 / LIVE 35` from
  2026-09-16 while the live census was `ORPHAN 17 / LIVE 14`. The section said
  *`cfcensus check` runs in CI*; CI runs `--self-test` and `ratchet`
  (the `cfcensus` and `cfcensus ratchet` steps), and `check` does not read the blocks.
* `cfcensus` treats only `✓` as closed (`tools/cfcensus.py:831-832`), so a gate
  that has not started counts as a live owner. That is right for a booked gate
  and would be wrong for one marked `⊘`; none is today.

All three belong to `R1y`.

## 5.5 The state documents grew because the record of being wrong was kept inside them — 量 2026-09-23

Measured from git history (`git cat-file blob <rev>:<file>`; a line is a `\n`):

| file | first commit, 2026-08-23 | end of 2026-09-16 (`76791c4`) | `f557873`, 2026-09-23 |
|---|---:|---:|---:|
| `CLAUDE.md` | 81 lines, 5,969 bytes | 1,342 lines, 119,933 bytes | 1,450 lines, 127,686 bytes |
| `PROGRESS.md` | 105 lines, 7,550 bytes | 2,308 lines, 951,723 bytes | 2,434 lines, 1,025,800 bytes |

Where the bytes were at `f557873`. In `CLAUDE.md`, 45.8 % of them were one
opening blockquote of 774 lines — 16 "*N*th update" seating narratives, under a
first sentence saying the file held only what is true today — and 35.3 % its
Environment section, mostly incident accounts. In `PROGRESS.md` the current
position, § Now, was 8.4 %, and its three largest cells were 31,464, 29,147 and
12,332 bytes. Twelve closed step lists were 34.6 %, a "session ladder kept
verbatim" 19.4 %, and the carried-forward table 24.8 %, with 68 of its 109 rows
closed or declined (57 and 11, by `cfcensus`'s own parser). Struck-through text
was 0.74 % and 0.52 %: the accretion was narrative added beside old text, not
strikethrough.

**The mechanism is a chain, and each link feeds the next.** ① "Negative results
stay in place" — right for records — was applied to state documents, whose job is
to say what is true now, so every correction arrived as a paragraph beside the
thing it corrected. ② Frozen cards cite these files by line number, so no line
could be added: over the 39 commits from `021753e` (2026-09-17) to `f557873`,
`PROGRESS.md` held at 2,434 lines while its bytes grew by 65,906, pushed into
existing cells. ③ Each session starts without the whole file in mind, and
appending is locally safe where rewriting is not. ④ The checkers came to parse
the accreted form (`C12`'s union of same-date blocks, `cfcensus`'s hints inside
cells), so cleaning it risked a red CI. ⑤ Nothing measured size.

**What changed, 2026-09-23.** Documents are three kinds — state (rewritten, never
appended, with a size budget in `tools/docsize.py`), record (append-only, never
edited, where the record of being wrong now lives), finding (current value and
source) — and new text cites rows by id. `CLAUDE.md` was rewritten to rules only,
its former text moved verbatim to `docs/history/claude-md-2026-09-23.md`, and
`tools/docmove.py` checks in CI that every block of it is still there. § Now was
rewritten the same way (`docs/history/progress-now.md`). The rest of the
restructure — closed step lists, the ladder, closed rows, `SPEC.md` — is `R1y`'s.

## 5.6 A re-dated line certifies its own rot — 量 2026-09-23

`citecheck` dates a citation by the last commit that touched the citing line,
and compares the cited line then with the cited line now. **Any edit to the
citing line re-dates every citation on it**, including a citation that had
already rotted: from that commit on, the oracle compares the moved line with
itself and reports `STABLE`. § 5.2 is a citation wrong when written; this is a
citation right when written, rotted, and then hidden by an unrelated edit.

Found this segment by listing every citation on every line the segment edited
and reading each against its prose before committing — the edits being digit
repairs that would themselves have re-dated those lines:

* `PROGRESS.md`'s `SEAM-1` row cited `tools/rlxfw-kbuild.sh` lines 203–204 for
  how `RECIPE_ID` is computed. They held it on 2026-09-04 (`9dab609`); three
  hours later `73646a1` moved it to 210, then `b36a1dd` to 262. On 2026-09-14
  `5955b36` edited the same row for another reason, and `citecheck` has called
  the citation `STABLE` since. It now cites 262–263. The `RECIPE-1` row carried
  the same 203–204 and is repaired with it.
* The `RECIPE-1` row also cites the driver at `357,388-389` for the two `cp`
  lines that keep `<cell>.config-installed` and the initramfs spec. In the file
  that citation was written against (`8daa33b`) the second pair was at
  387–388, and the commit that wrote it (`73646a1`) moved all three by nine:
  it was wrong at the commit that landed it, and `citecheck` has only ever read
  its `357` (§ 5.1). It now cites `456,486-487`.
* `PROGRESS.md`'s `CI-4` row cites the sentence *Two survived the 23
  controls* at `README.md` line 764. It was at
  772 on the day the row was written (`126f659`, 2026-09-16) and on every
  commit since — the § 5.2 kind, seen because this segment's `README` edits
  would have moved line 764.

**The remedy used here is a reading, not a tool:** after a commit's edits and
before the commit, every citation on every edited line is listed with its
target's current text and read against its sentence. A tool could do the
dating half — find each citation's first commit with `git log -S` and compare
from there instead of from the line's last edit — but it would still need the
reading, because a citation can be wrong at its first commit too.

What this does not establish: how many rotted citations are hidden this way
today. Only lines this segment edited were read.
