# `PROGRESS.md`'s analysis of the gate board's `Est.` column, archived verbatim

Moved here verbatim from `PROGRESS.md` at `530dce4c`, lines 135–207, by `P5e-2` on 2026-10-09, in the
commit that deleted the column, which is the repair its last paragraph recommends. The
column's values are in `docs/history/progress-gate-board-2026-10-09.md`. A record: never edited. `tools/docmove.py`
proves the move.

## Under § Gate board, as of `530dce4c`

🔄 **198 → 200 on 2026-09-01**, and the ORDER matters: the number was written as 198+2 and then CHECKED by summing the column, which is backwards and is recorded that way. The sum is **200 over 18 rows**, with `R1h` deliberately uncosted (its budget lives in its own step list) and, since 2026-09-30, `R8a` too — it is a split of `R8`'s work, not work added to it, so costing it would double-count the 18 beside `R8`. The paragraphs below say why this column is not a quantity; that is a reason to delete it, not a reason to let its arithmetic drift.

🟢 **Est. is CALIBRATED now — 2026-09-11, `R5-11` — and what came out is a band, not a ratio.** This note said *the calibration point is the first driver
(R5); when it lands, multiply every remaining row by the measured ratio and say so here.* `R5` landed. 量, against the **plan's 小計**, which the paragraphs below establish is the only estimate carrying `Actual`'s definition:

| gate | actual | plan 小計 | ratio |
|---|---:|---:|---:|
| `S0` | 1 | 3 | 0.33× |
| `R0` | 7 | 11 | 0.64× |
| `R1-gate` | 9 | 8 | 1.12× |
| `R1h` | 5 | 4 | 1.25× |
| `R2a/b/d` | 5 | 6 | 0.83× |
| `R3` | 18 | 13 | 1.38× |
| `P4a` | 1 | 2 | 0.50× |
| `R4` | 4 | 8 | 0.50× |
| `R5` | **32** | **31** | **1.03×** |

**n = 9 · min 0.33× · max 1.38× · spread 4.15× · mean 0.844× · median 0.833×.**

🔴 **So the instruction cannot be carried out as written, and that is the result rather than a failure to produce one.** The 170 planned segments still
ahead come to **142** at the median, **57** at the minimum and **235** at the
maximum. A single multiplier is not in this data, and publishing one would give
this column a third owner of a quantity it has already had two of.
🔴 **The prior carried into `R5` is refuted.** Pooled, `S0` 1/3 plus `R0` 7/11
is 8/14 = **0.571×**, n = 2 — it predicts **17.7** segments for `R5` against an
actual of **32**, low by **1.81×**. ⚠️ `P4b-gate` is not among the nine: it was
split out of `P4b` on 2026-09-01 and has no row in the plan, so it has no
denominator with the right definition.
⚠️ **What this does not say.** `Actual` counts segments between one gate
closing and the next, so it includes instrument days and desk days spent on
other things; nine gates is nine points from one person on one project, and the
spread is wide enough that the mean and the median are not usefully different
from each other. The recommendation two paragraphs down — delete the `Est.`
column and keep one line for the measured ratio — is unchanged by this, and is
still not done, because deleting a column is a decision.

🔴 **This column had a second owner, and reconciling the two on 2026-08-25
produced a worse answer than "they disagree": neither of them is a quantity.**

The planning material carries a finer accounting — desk, bench and instrument
time as three columns — and totals **252**. This column totals **198**. Both add
up correctly against themselves: every row of the plan's table equals its own
desk+bench+instrument, its cumulative column is consistent, and the seventeen
rows here sum to 198. **So the arithmetic was never the problem.**

**What the difference is not.** The plan's instrument column totals 44, so
252 − 44 = **208** is its desk+bench. This column is 198, not 208. Ten of its
seventeen rows agree with the plan's desk+bench exactly; **seven disagree, and
not all in the same direction** — `R5` is 4 low, `R1-pub` 2 low, `R7` is 1
**high**. Net −10.

🔴 **So 198 is not the total, not desk+bench, and not any consistent subset of
the plan. No rule reproduces it.** It is not a stale copy either: a stale copy
names a revision you can point at. It is a third number that accreted row by row.

**Which one a decision should be made against, and why it is the plan's.** The
column beside this one is `Actual`, and `Actual` counts segments consumed in
`LOG.md` between one gate closing and the next — **which includes instrument
days**. The only estimate with the same definition is the plan's 小計. Against
the two closed gates: `S0` actual 1 against plan 3, `R0` actual 7 against plan
11 — **8 consumed against 14 planned, 0.57×, n=2**, and that ratio is the thing
worth carrying rather than either total. Against this column (1 and 5) the same
two gates read 1.0× and 1.4×, which looks better and means less: it is a number
compared against a number with no definition.

**The house-rule-1 defect is sharper than two owners.** An estimate is a planning
artefact; this file is the owner of *where I am*, which is a fact about work
done. `Actual`, `Status` and `Evidence` belong here. **`Est.` does not**, and the
recommended repair is to delete the column rather than reconcile it, keeping one
line under the board for the measured ratio — which IS a fact about work done and
which is what "multiply every remaining row by the measured ratio" needs. **Not
done today**, because deleting a column from the gate board is a decision and
this entry is the analysis it should be made from.
