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

## 2. Six rules, each from a measurement

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

**R6. The number is re-derived, never copied.** 量 2026-09-16: a patch script
anchored on ninety characters quoted out of `PROGRESS.md` was REFUSED, because
the file reads `補丁的錪點` and the quotation had silently corrected the typo
to `錨點`. **The danger of a quoted anchor is not that it fails to match — a
failure is cheap — it is that a slightly different one matches the wrong
place.** Address a row by its label; a label is derived from the table and
there is nothing to mistype.

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
`R1z-2`'s.
