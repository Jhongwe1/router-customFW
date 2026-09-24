# CORRECTIONS — block 45, seating 40

Every departure from the frozen card `PREDICTIONS-B47-block45.md`, and every
defect found in it. The card itself is **not edited** — `check-predictions`
reads its mtime. No off-card cell ran in this block.

---

## § 1 🔴 The `cells` fence names `looprun`'s single-round artefacts wrongly — found after the press

The fence lists `D1Q-r01-ab2`, `D1Q-r01-2a` and `D1Q-r01-boot`. `looprun` with
`--iterations 1` names a single round's artefacts without the round number: 量
2026-09-25, the directory holds `D1Q-ab2`, `D1Q-2a` and `D1Q-boot` (each with its
`.log`, `.timing` and `.meta.json`), and no `D1Q-r01-*`. The names were copied
from block 44's two-round block (`P2Q-r01-*`) without being read off a one-round
run. The card's own `cardnum` row `cells-fence 78` counts the fence, not the
files, so nothing before power could see it.

**What it costs.** `check-predictions` reads **75 of 78** captures after the
prediction and 3 that "did not" — those three are the fence's wrong names, not
missing captures. `capdate` counts them as not captured and dates the three real
files as off-card captures on the declared date (`off-card in 2026-09-25b: 3
dated`). Every other cell of the fence was captured after the card's commit.

**What is not affected.** The three artefacts are `looprun`'s record of the one
round that took the board to rlxfw's shell (`RESULT: the loop closed, 8
assertion(s) held`); no prediction reads them.
