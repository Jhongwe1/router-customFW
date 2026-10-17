# `PROGRESS.md`'s explanatory notes, archived verbatim

Moved here verbatim from `PROGRESS.md` at `530dce4c` by `P5e-2` on 2026-10-17, when the file was cut
to its state: the paragraphs under § Now's table and the table *The four things this file
tracks* (lines 28–62), § Records moved out of this file (lines 66–97), whose rows
`docs/history/README.md` now indexes, and the debt census's notes (lines 372–392 and 411–416)
with its counts as generated before the closed rows left § Carried forward (lines 395–406). The
§ Now rows stayed. A record: never edited. `tools/docmove.py` proves the move.

## Under § Now's table, as of `530dce4c`

**How to read § Now.** It holds current state only: a few sentences per row,
rewritten each segment rather than appended to. What a row used to say is in
`docs/history/progress-now.md` and in `LOG.md`. A wrong row is corrected by
fixing the row and recording the fix in `LOG.md`; the record of being wrong
belongs in the record, not in the state.

Below § Now, § Records moved out of this file says where the records went; the
rest is state — § Gate board, § Release clock, § Carried forward, the census.

### The four things this file tracks, because they are not the same thing

This line existed to name one of them and was read as naming all four. **Active
step above is a bench session, which is not one of `DAY-ZERO` items 0–8** — that
is not an error, but nothing said so.

| | what it is | where it lives | answers |
|---|---|---|---|
| **Gates** `S0`, `R0`…`R9`, `P1`…`P4` | the fifteen milestones | the board below | *how far is the project* |
| **`DAY-ZERO` items 0–8** | 🔄 **the instruments that had to exist before *any* gate could run** — not "the desk step list for the gate that is active now", which is what this row said until 2026-08-25 and which made it a **second owner** of the state § *Step list* owns. `item 7` had already drawn the line the row missed: `hazlint` is `DAY-ZERO`'s, the hazard verdicts it enables are `R1b`'s | `plan/DAY-ZERO.md` | *what had to exist before the first gate* |
| **§ Step list** 🆕 | the session-sized steps of the gate that is active now, written on entering it (`plan/SESSIONS.md` §0b) | at the end of **this file** | *what do I do next at the desk* |
| **Runsheet sessions** ~~`B1`…`B18`~~ 🔄 **`B1`…`B8`, 2026-09-16 (`R1z-2`)** | what gets typed at the bench. 🔄 **Not "one power cycle each", which is what this row said until 2026-08-24**: `B1` and `B2` share one; `B3` costs **two of its own**, because `G6`'s and `G7`'s jumps each end with a kernel running and the loader gone; and a session outlives a seating — `B1` has now been typed across three power cycles, one directory each | `RUNSHEET.md` | *what do I do next at the device* |
| **`C-n`** | open questions that outlive one session, each owned by a gate | Carried forward, below | *what is still unanswered* |

**Runsheet sessions are not plan items and never were.** They exist because
`DAY-ZERO` items 2c and 4 produced a large number of claims read out of a flash
dump, a datasheet and four vendors' source, and **no number in this repository
has been measured on the device**. A session appears when enough desk claims
have piled up to be worth one power cycle. `B1` and `B2` are the first, and
`B3` is the one that closes the gate that is active.

A `C-n` is *not* extra work appearing from nowhere either: it is the mechanism
for **not** doing work now. When a session turns up a question it cannot close,
the choice is to chase it (and lose the thread) or to write it down with the
gate that owns it. The list is long because the desk work has been productive,
and every row names where it gets settled.

## Records moved out of this file

These records were moved verbatim to `docs/history/`: by `R1y-4` on 2026-09-30
from `PROGRESS.md` at `e274ccb`, and each closed gate's step list since in its
closing commit. A record is never edited; a record's line citation is read with `tools/citeresolve.py`.

| What | File |
|---|---|
| `R6`'s step list | `docs/history/steps-R6.md` |
| `P1`'s step list | `docs/history/steps-P1.md` |
| `R1z`'s step list | `docs/history/steps-R1z.md` |
| `R1-pub + R2c`'s step list | `docs/history/steps-R1-pub-R2c.md` |
| `R5`'s step list | `docs/history/steps-R5.md` |
| `R4`'s step list | `docs/history/steps-R4.md` |
| `P4b-gate`'s step list | `docs/history/steps-P4b-gate.md` |
| `P4a`'s step list | `docs/history/steps-P4a.md` |
| `R3`'s step list | `docs/history/steps-R3.md` |
| `R1h`'s step list | `docs/history/steps-R1h.md` |
| `R2a/b/d`'s step list | `docs/history/steps-R2a-b-d.md` |
| `R1-gate`'s step list | `docs/history/steps-R1-gate.md` |
| `P2`'s step list | `docs/history/steps-P2.md` |
| `R6b`'s step list | `docs/history/steps-R6b.md` |
| `R1y`'s step list | `docs/history/steps-R1y.md` |
| `R8a`'s step list | `docs/history/steps-R8a.md` |
| `R7`'s step list | `docs/history/steps-R7.md` |
| `R9`'s step list | `docs/history/steps-R9.md` |
| `R8b`'s step list | `docs/history/steps-R8b.md` |
| `R6c`'s step list | `docs/history/steps-R6c.md` |
| § Session ladder | `docs/history/progress-ladder.md` |
| § Corrections | `docs/history/progress-corrections.md` |
| § Carried forward's closed and declined rows | `docs/history/progress-carried-forward.md` |
| § Gate board's closed rows as they stood before `R1y-5` | `docs/history/progress-gate-board.md` |

## The debt census's notes and counts, as of `530dce4c`

`R1z-0`'s deliverable, first written 2026-09-16. § Carried forward above is the
owner of *what each debt asks*; this section owns only the join that table
cannot state about itself — **which gate each row named, and whether that gate
still exists**. No question text is reproduced and no line number is cited: a
second copy of a debt is a second owner of it, and `CITE-2` is a row of this
very table about the second of those two mistakes.

**The population is derived, not chosen.** Every row of § Carried forward, every
gate of § Gate board, every `## …step list` header, and every step id through
`spec-check`'s own `progress_step_state`. So a row added to the table after this
block was written cannot be missing from it, and **a row cannot be added to the
census without moving its source, where `git log` sees it** — which a
hand-written list cannot promise. That property is what separated `tccensus`
from the four checkers the seventy-seventh segment found broken.

⚠️ **What it cannot see.** Both populations come from one file. This is the
record auditing itself, and it is blind to a debt this project incurred and
never wrote down — the class the seventy-seventh segment's closeout found by
hand, four owner files that no checker could reach. `U6` keeps that testable:
with a gate in progress an open row must be live-owned, and with none some row
must be open and every open row a standing instruction, or the census refuses.

| what | n | meaning |
|---|---:|---|
| LIVE | 1 | open, and a gate that is still open owns it |
| SEGMENT | 11 | open, deferred to *any segment that touches X* — unscheduled, not orphaned |
| ORPHAN | 0 | 🔴 open, and every gate it names is CLOSED — **nobody will do it** |
| ORPHAN? | 0 | open by its first cell, owner closed, and a ✅ sits in the owning-gate cell or opens the question — probably an `L8` row that is finished and never marked |
| DEAD | 0 | 🔴 names a gate that exists nowhere in this file |
| NONE | 0 | open and names no gate at all |
| CLOSED | 8 | first cell says ✅ |
| DECLINED | 5 | first cell says ⊘ |
| **total** | **25** | rows parsed, reconciled against 27 raw table lines minus 2 header lines |
| `L8` | 0 | closure recorded somewhere this table does not declare — the owning-gate cell, or the head of the question; 0 exempted by name |

Every open row whose owner is not a gate that is still open. `ORPHAN` is the
population `R1z` exists for; `ORPHAN?` was a row *probably* finished and never
marked, and the two were counted apart because folding them would have inflated
the debt by fourteen. 🟢 **`R1z-2` read all fourteen one at a time and every
one of them was.** The bucket is empty, and that is the label's own claim
measured rather than repeated.
