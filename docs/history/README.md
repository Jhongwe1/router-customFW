# docs/history/

Text moved verbatim out of this repository's state documents, so that each could be rewritten
to its current state without losing what it said. Every file here except this index is a
record: it is never edited, it names the commit its text was moved from, and
`tools/docmove.py` proves the move against that commit. A line citation in a record is read
with `tools/citeresolve.py`, against the tree of the commit that wrote it. This index is
state: one line per file, kept current. `LOG.md`'s earlier months are not here; they are
under `docs/log/`.

## Closed gates' step lists

Each holds one gate's step list, moved verbatim from the end of `PROGRESS.md`: the first
fourteen by `R1y-4` on 2026-09-30 from `e274ccb`, each later one in its gate's closing commit.
`tools/cfcensus.py` and `spec-check`'s `C12` read them as part of the step map.

| File | The gate, and when it closed | Moved |
|---|---|---|
| [steps-R1-gate.md](steps-R1-gate.md) | `R1-gate`, 2026-08-26 | by `R1y-4`, 2026-09-30 |
| [steps-R2a-b-d.md](steps-R2a-b-d.md) | `R2a/b/d`, 2026-08-28 | by `R1y-4`, 2026-09-30 |
| [steps-R1h.md](steps-R1h.md) | `R1h`, 2026-08-29 | by `R1y-4`, 2026-09-30 |
| [steps-R3.md](steps-R3.md) | `R3`, 2026-08-31 | by `R1y-4`, 2026-09-30 |
| [steps-P4a.md](steps-P4a.md) | `P4a`, 2026-09-01 | by `R1y-4`, 2026-09-30 |
| [steps-P4b-gate.md](steps-P4b-gate.md) | `P4b-gate`, 2026-09-01 | by `R1y-4`, 2026-09-30 |
| [steps-R4.md](steps-R4.md) | `R4`, 2026-09-02 | by `R1y-4`, 2026-09-30 |
| [steps-R5.md](steps-R5.md) | `R5`, 2026-09-11 | by `R1y-4`, 2026-09-30 |
| [steps-R1-pub-R2c.md](steps-R1-pub-R2c.md) | `R1-pub + R2c`, 2026-09-16 | by `R1y-4`, 2026-09-30 |
| [steps-R1z.md](steps-R1z.md) | `R1z`, 2026-09-16 | by `R1y-4`, 2026-09-30 |
| [steps-P1.md](steps-P1.md) | `P1`, 2026-09-17 | by `R1y-4`, 2026-09-30 |
| [steps-R6.md](steps-R6.md) | `R6`, 2026-09-22 | by `R1y-4`, 2026-09-30 |
| [steps-P2.md](steps-P2.md) | `P2`, 2026-09-25 | by `R1y-4`, 2026-09-30 |
| [steps-R6b.md](steps-R6b.md) | `R6b`, 2026-09-28 | by `R1y-4`, 2026-09-30 |
| [steps-R1y.md](steps-R1y.md) | `R1y`, 2026-09-30 | in its closing commit |
| [steps-R8a.md](steps-R8a.md) | `R8a`, 2026-09-30 | in its closing commit |
| [steps-R7.md](steps-R7.md) | `R7`, 2026-09-30 | in its closing commit |
| [steps-R9.md](steps-R9.md) | `R9`, 2026-10-04 | in its closing commit |
| [steps-R8b.md](steps-R8b.md) | `R8b`, 2026-10-08 | in its closing commit |
| [steps-R6c.md](steps-R6c.md) | `R6c`, 2026-10-09 | in its closing commit |

## `PROGRESS.md`'s history

| File | What it holds | Moved |
|---|---|---|
| [progress-now.md](progress-now.md) | § Now's rows as they stood at `f557873`, before § Now became current state only | 2026-09-23 |
| [progress-carried-forward.md](progress-carried-forward.md) | § Carried forward rows before a rewrite: `CI-5`, the rows closed or declined by 2026-09-30, and the earlier text of rows closed in place on 2026-10-05 and 2026-10-08 | from 2026-09-23 |
| [progress-ladder.md](progress-ladder.md) | § Session ladder | by `R1y-4`, 2026-09-30, from `e274ccb` |
| [progress-corrections.md](progress-corrections.md) | § Corrections | by `R1y-4`, 2026-09-30, from `e274ccb` |
| [progress-gate-board.md](progress-gate-board.md) | the closed gates' board rows before `R1y-5` cut them to what closing each means | by `R1y-5`, 2026-09-30, from `e274ccb` |
| [progress-gate-board-2026-10-09.md](progress-gate-board-2026-10-09.md) | § Gate board, every row whole, with the deleted `Est.` column | by `P5e-2`, 2026-10-09, from `530dce4c` |
| [progress-est-analysis-2026-10-09.md](progress-est-analysis-2026-10-09.md) | the analysis of the `Est.` column that recommended deleting it, with its measured ratio | by `P5e-2`, 2026-10-09, from `530dce4c` |
| [progress-release-clock-2026-10-09.md](progress-release-clock-2026-10-09.md) | § Release clock's notes: the first releases, and why the table keeps only the shipped dates | by `P5e-2`, 2026-10-09, from `530dce4c` |
| [progress-carried-forward-2026-10-09.md](progress-carried-forward-2026-10-09.md) | the thirteen closed and declined rows of § Carried forward | by `P5e-2`, 2026-10-09, from `530dce4c` |
| [progress-notes-2026-10-09.md](progress-notes-2026-10-09.md) | the notes under § Now, *The four things this file tracks*, § Records moved out of this file, and the debt census's notes and counts | by `P5e-2`, 2026-10-09, from `530dce4c` |

## `README.md`, `CHANGELOG.md` and the runsheet

| File | What it holds | Moved |
|---|---|---|
| [readme-2026-09-29.md](readme-2026-09-29.md) | `README.md`'s lead, `Status` row and `Not measured` row through `v0.4` | 2026-09-29, at `v0.5`'s release |
| [readme-2026-10-04.md](readme-2026-10-04.md) | the same three places through `v0.5` | 2026-10-04, at `v0.6`'s release |
| [readme-2026-10-05.md](readme-2026-10-05.md) | `README.md`'s control counts and census paragraph, as they stood at `c0349701` | 2026-10-05, when `README-1` and `CI-4` closed |
| [readme-2026-10-09.md](readme-2026-10-09.md) | `README.md`'s lead and `Status` row through `v0.6` | 2026-10-09, at `v1.0`'s release |
| [changelog-through-v1.0.md](changelog-through-v1.0.md) | `CHANGELOG.md` whole, through `v1.0`: the per-segment entries and every release's section | by `P5e-2`, 2026-10-09, with `git mv` |
| [runsheet-2026-09-27.md](runsheet-2026-09-27.md) | `RUNSHEET.md` whole: the bench procedure and the safety rules that outlive a seating; from 2026-09-16 each seating's card under `bench/` owned what was typed | by `P5e-2`, 2026-10-09, with `git mv` |

## Other

| File | What it holds | Moved |
|---|---|---|
| [claude-md-2026-09-23.md](claude-md-2026-09-23.md) | `CLAUDE.md` as it stood before it was rewritten to rules only | 2026-09-23 |
| [known-issues-closed.md](known-issues-closed.md) | `docs/KNOWN-ISSUES.md`'s closed entries and its `v0.5` and `v0.6` sections | by `P5e-2`, 2026-10-09, from `530dce4c` |
| [known-issues-segment-limits.md](known-issues-segment-limits.md) | `docs/KNOWN-ISSUES.md`'s eighteen dated *What … did NOT establish* sections, each one segment's or seating's limits | by `P5e-2`, 2026-10-10, from `530dce4c` |
