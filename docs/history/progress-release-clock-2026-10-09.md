# `PROGRESS.md` § Release clock's notes, archived verbatim

Moved here verbatim from `PROGRESS.md` at `530dce4c` by `P5e-2` on 2026-10-17, when the section was
cut to its version table and one line: its opening paragraph (lines 213–216) and everything
under the table (lines 229–329). A record: never edited. `tools/docmove.py` proves the move.

## Above the table, as of `530dce4c`

**This table owns ONE thing: which versions have actually shipped.** What a
version *contains* moved to `README.md` § *Which gates make which version* on
2026-09-01 (`P4b-1`); the week estimates are planning material and stay in
`plan/`. The note below records why, because the repair is the finding.

## Under the table, as of `530dce4c`

**Public from v0.1.** Held disclosure items stay out until `docs/disclosure.md`
says otherwise — `plan/` §15 holds the policy.

🟢 **`v0.2` SHIPPED 2026-09-01** — tag `v0.2` at `6cb9bf3`, and the release at
<https://github.com/Jhongwe1/router-customFW/releases/tag/v0.2>.
🔴 **It is this repository's FIRST release.** 量: `gh release list` was empty
before it, so `v0.0` was tagged on 2026-08-25 and never released either —
`CHARTER.md` §110 rule 2 has been unsatisfied since the project's first tag,
which is wider than `REL-0` recorded. 🟢 **2026-09-01, the owner took it: no retrospective `v0.0` release, and the rule
is followed from `v0.3`.** 量 the same day, because the sentence above is a claim
about GitHub and not about this repository: `gh release list` returns **one** row,
`v0.2`, so `v0.0` is tagged and unreleased and nothing else has ever been released.
The reason for not backfilling is that a release note written now would describe a
version by hindsight, which is the same objection that kept `S0` and `R0` out of
`docs/GATE-RESULTS.md`. **`CHARTER.md` §110 rule 2 is therefore unsatisfied for
`v0.0` and `v0.1` by decision rather than by omission**, and satisfied from `v0.3`.

🟢 **`v0.3` SHIPPED 2026-09-11** — tag `v0.3` at `8f42644`, and the release at
<https://github.com/Jhongwe1/router-customFW/releases/tag/v0.3>.

🟢 **`v0.4` SHIPPED 2026-09-17** — tag `v0.4` at `b24abfb`, and the release at
<https://github.com/Jhongwe1/router-customFW/releases/tag/v0.4>.
🔴🔴 **AND THE OWNER HAD TO ASK AGAIN, WHICH MAKES `REL-4`'s GAP A SECOND INSTANCE SIX DAYS AFTER THE FIRST.** The `v0.3` paragraph directly above records that the release *became due without anything here noticing* and that **what found it was the owner asking, not a check**. 🔴 `REL-4` was then closed as ✅ — correctly, because the task *make the v0.3 release* was done — **and the finding inside it was left as a sentence rather than turned into an instrument.** 量 2026-09-17: the tag was pushed at 02:0x and the **release did not exist**; `gh release list` returned `v0.3` and `v0.2` only, and the owner said *我在 github 上沒看到你 release*. Same trigger, same person, six days apart.
🔴 **The closeout audit could not have caught it, and that is the transferable half.** Method 8 enumerates *what this segment produced* and asks *which FILE owns it* — and a GitHub Release is **not a file in this repository**. Every gate was green and every owner file was correct; the missing artefact lived outside the tree entirely. **The method has a blind spot for outward-facing artefacts**, and this is its first measured instance.
⚠️ **What a check would need, written down rather than built.** `README.md` owns version → contents; the gate board owns which gates are `✓`. A release is DUE the moment every gate in a version's row is closed, so the check is a join over two committed tables plus one question `gh release list` answers — which means it cannot be a pure repository check and belongs in CI, where a token exists. **It is not built here**: two instances is a rate, not a target, and building it inside the segment that hit it is fitting an instrument to its own occasion. **The re-open condition is a third instance.**
🟢 Order taken from the precedent again: tag and release first, record second, so no sentence here is written before the thing it describes exists.

🟢 **It is the first release this project has made UNDER that rule rather than in
spite of it**: `v0.0` was tagged and never released, `v0.1` was never tagged, and
`v0.2` was released on the day the rule was written down. 🔴 **And it became due
without anything here noticing.** `README.md` owns version → contents and says `v0.3`
is `R4` + `R5`; `R4` closed 2026-09-02 and `R5` closed 2026-09-11, so it was due the
moment the gate closed — and what found it was the owner asking *I have not seen
a tag release*, not a check. `REL-4` is the record of that gap. ⚠️ **The order was
taken from the precedent rather than chosen**: 量, `v0.2`'s tag points at `6cb9bf3`
and the `SHIPPED` claim landed in `04dc0ef` **three minutes and forty seconds
later** — tag and release first, record second, so no sentence is written before
it is true.

---

### 🟢 `P4b-1`: the second owner is gone, 2026-09-01 — and the column that was NOT flagged was also a copy

**What this table looked like until today**: four columns — `version`,
`Contents`, `Target (optimistic / ×1.8)`, `Shipped` — of which only `Shipped`
was ever this file's own. The other two restated `plan/CHARTER.md` §88, which
is **gitignored**, so house rule 1's usual repair (replace the content with a
pointer) produced a pointer no public reader could follow. `P4b-1` decided the
owner has to be a committed file, and it is `README.md`.

**量 2026-08-31 (twentieth), the `Contents` column, read side by side against
CHARTER §88 — six of six shared rows disagreed:**

| version | `CHARTER.md` §88 | the deleted `Contents` column |
|---|---|---|
| v0.1 | `R0` + `rlxprobe` segment 0 on silicon + **`R1-gate`** | S0 + R0 + **`R1`** + `rlxprobe` + first write-up |
| v0.2 | `R3` (60-second take) + **`P4a`** | **`R2`** + `R3` |
| v0.3 | `R4` + `R5`, **six** drivers + DT binding + `driver-diff` | `R4` + `R5`, **five** drivers |
| v0.4 | **`R1-pub`** + `P1` | **`R6`** |
| v0.5 | **`R6`** + `P2` | **`R7`** |
| v1.0 | `R8` + `R9` + `P3`/`P4b` | `R8` + `R9` + **`P1`–`P4`** |

CHARTER also has `v0.0` and `v0.6` rows; that table had neither, which is what
shifted its tail by one version from `v0.4` down. **It bit twice in one
morning.** Read there, `v0.2` did not need `P4a` and could have been tagged
before that session started; and `v0.1` needed `R1` **whole**, of which
`R1-pub` is `·`, so under that table v0.1 could never be tagged at all —
while `REL-2` says its contents completed on 2026-08-26, which is true under
CHARTER and false under the file `REL-2` lives in.

🔴 **量 2026-09-01 (twenty-second): the `Target` column was a restatement
too, and nothing had ever said so.** The note above singled out `Contents` as
*the* wrong column and left `Target` beside it unflagged. But `×1.8` is
CHARTER's own multiplier, defined in CHARTER, so that column was never this
file's quantity either. Read against §88 by version label:

| version | CHARTER §88 樂觀 / 務實 | the deleted `Target` column |
|---|---|---|
| v0.1 | 2.5 / 4.5 週 | wk 3 / wk 5 — agrees under rounding |
| v0.2 | 4.9 / 8.9 | **wk 7 / wk 12** |
| v0.3 | 9.4 / 16.9 | **wk 12 / wk 21** |
| v0.4 | 12.9 / 23.3 | **wk 17 / wk 30** |
| v0.5 | 18.5 / 33.3 | **wk 23 / wk 41** |
| v1.0 | 28.8 / 51.8 | wk 29 / wk 52 — agrees under rounding |

**Two of six agree and four do not** — and a partly-agreeing copy is worse
than a wholly stale one, because it reads as maintained. ⚠️ The `v0.4`
comparison is by version *label* only: the two tables put different work under
that label, so those two cells were never measuring the same thing.

**Why both columns were deleted rather than reconciled.** The gate board's
`Est.` column analysis below already made this argument and this is the second
instance of it: *an estimate is a planning artefact; this file is the owner of
where I am, which is a fact about work done.* `Shipped` is a fact about work
done and stays. `Target` is an estimate and goes to `plan/`. `Contents` is a
decision about the future, it has to be visible to a public reader, and it goes
to `README.md`. 🔴 **And `CHANGELOG.md`'s `v0.2` section carried the dangling
pointer into the release itself** — its first line read *Contents, against
`plan/CHARTER.md` §88* — which is the defect this gate exists for, shipped.
Repaired in the same commit.
---
