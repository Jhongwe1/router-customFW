Part of [the known-issues index](../KNOWN-ISSUES.md): entry 16 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 A closeout gate run on a dirty tree has its own findings switched off — 2026-09-16

量, by CI run `35102926093` going red on `text/citecheck` where every desk run
that segment was green.

`citecheck`'s oracle digests the cited row's content **at the commit that last
wrote the CITING line**. That is what makes a repaired citation drop off the
baseline. 🔴 **But blame is per LINE, and any edit to that line moves it — not
only a repair.** The eightieth segment appended a re-ownership note to one cell
of `PROGRESS.md`'s `LEDGER-3` row; the row's citation of
`tools/ledgerscan.py:505` had been rotted and on the baseline for weeks; the
blame moved to today, today's `:505` matched itself, and the rot read STABLE.
**Not repaired — laundered.** `C4` caught it because the baseline is swept in
both directions.

🔴 **And the desk could not have caught it**, which is the part worth carrying:
on a dirty tree `citecheck` **suspends every baseline row whose citing file is
modified** — it prints *their baseline rows are suspended* and names the count —
so a closeout run with twenty edited rows is a run with those rows switched off.
量 that segment: 28 of 43 rows suspended at the desk, 0 on CI.

**The rule this gives, and it costs nothing**: the `.md` gates are run once
before the commit and **again after it, on the clean tree, before the push**.
`spec-check`, `ledgerscan` and `flashwin scan` read the tree as it is;
`citecheck` is the one whose *population* changes with the tree's dirtiness.

⚠️ **The residual is not fixed**: rot that becomes rot in the same commit that
edits its row is laundered and never enters the baseline, so no later sweep can
find it. There is no control for that case, and inventing one means giving the
oracle a second reference point that is not the citing line's blame.

---
