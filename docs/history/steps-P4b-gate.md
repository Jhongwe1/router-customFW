# `PROGRESS.md` § `P4b-gate`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 1015–1101, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `P4b-gate`'s step list — ✅ CLOSED 2026-09-01, in two desk segments

✅ **CLOSED 2026-09-01**, two segments against an estimate of **2** — the
first gate on this board to land on its own number, and with n=1 that is worth
nothing except saying so. Opened the same day on the owner's decision against
`REL-0`. 🔴 **Closing it means all four have a committed owner, not that
all four are finished** — `REEL-1` is still open under `P4b-4` and `IMG-1`
under nothing, and both are named rather than folded in.

🔴 **Tagging is not a step here.** A tag is outward-facing and effectively
irreversible. The owner's ruling, 2026-09-01: **it waits for their word, and it
waits for the 60-second take to be shot.**

| step | | done |
|---|---|---|
| `P4b-1` ✅ **2026-09-01** | **version → contents gets ONE committed owner.** 量 2026-09-01: `plan/CHARTER.md` §88 and this file's Release clock disagree on **six of six** shared rows, and CHARTER is gitignored, so the authoritative copy is invisible to a public reader. The decision is *which committed file owns it*; the mechanical part (this table's `Contents` column becomes a pointer, or goes) follows. ⚠️ The same analysis already exists one section down for the gate board's `Est.` column, and it recommended deletion over reconciliation  🟡 **PARTLY, 2026-09-01.** `CHANGELOG.md`'s `v0.2` section and `docs/KNOWN-ISSUES.md` now state, in committed files, what the RELEASED versions contain — so `D1` is met for v0.2. ⚠️ **The map of FUTURE versions still has two owners**, and the Release clock below is still the stale one. The decision the step names has not been made 🟢 **DONE 2026-09-01, twenty-second segment. The owner is `README.md` § *Which gates make which version*.** Three places stopped restating it in the same commit: this file's Release clock dropped `Contents` **and** `Target` and keeps only `Shipped`; `plan/CHARTER.md`'s table dropped its 內容 column and keeps only 累計段 and the two week estimates; `CHANGELOG.md`'s `v0.2` section stopped opening with *Contents, against `plan/CHARTER.md` §88*, which was a pointer into a gitignored file **shipped inside a public release**. 🔴 **And the repair found a second restated column nobody had flagged**: `Target` carries CHARTER's own `×1.8` multiplier, so it was never this file's quantity either — 量, it agreed with §88 on two of six rows (v0.1 and v1.0, under rounding) and disagreed on four. The note in the Release clock has the row-by-row reading. ⚠️ **The deletion is the same call the `Est.` column analysis recommends one section down**, and this is its second instance: an estimate is a planning artefact, a shipped date is a fact about work done | ✅ |
| `P4b-2` ✅ **2026-09-01** | **`study/weekly-results.md` becomes readable from the public repository, and the owed entries are written.** 量: `.gitignore:17` is `study/` and `git ls-files study/` returns nothing. Two halves: a decision (an ignore exception for one file, or move it out of `study/`), then the entries — `R2a/b/d` 2026-08-28, `R1h` 2026-08-29, `R3` 2026-08-31, `P4a` 2026-09-01. 🟢 **Every one of them has its 「這個 gate 沒有證明什麼」 already written**: `notes/kernel-build.md` §21.7 for `R3`, `notes/reproducible-build.md` §7 for `P4a`. 🔴 **And the rule's own operating clause needs `n ≥ 2` to run at all** — *two consecutive entries whose 「沒有證明什麼」 is the same thing means that thing is the next gate* — which is exactly the decision the owner had to make by hand this morning  🔴 **OPEN, and half of it was RULED ON rather than done.** Owner 2026-09-01: `study/` stays gitignored for now. The four owed entries are still owed. **`D2` is therefore not met and this gate is not closed** 🟢 **DONE 2026-09-01, twenty-second segment, and the two halves stopped being in conflict once the artefact left the directory.** `docs/GATE-RESULTS.md` — committed, English, **five** entries (`R1-gate`, `R2a/b/d`, `R1h`, `R3`, `P4a`). `study/` stays gitignored as the owner ruled; `study/weekly-results.md` is now a redirect. 🔴 **This row's own claim that all four owed entries already had their 「沒證明什麼」 written was FALSE, and it named only two files.** 量 2026-09-01: `notes/kernel-build.md` §21.7 and `notes/reproducible-build.md` §7 exist; **`R2a/b/d` and `R1h` have no such section anywhere**. What they have is four `## What could still be wrong` sections and a scattered set of residuals — *doubt about a claim already made* is not *a list of what was never established*, and those two entries had to be derived rather than copied. ⚠️ `S0` and `R0` are deliberately not backfilled; the reason is at the head of the new file and it is that a hindsight-written entry contaminates the operating clause. 🟢 **The clause RAN, for the first time, and named `CPU-45`** — see the new carried-forward row | ✅ |
| `P4b-3` ✅ **2026-09-01** | **`CHANGELOG.md` gets a `v0.1` and a `v0.2` section, and a known-issues list exists.** 量 2026-09-01: the file has exactly two `## ` headings, `Unreleased` and `v0.0 — 2026-08-25`, so everything since v0.0 is one block; and 量, no committed file holds a known-issues list — after this row was written the phrase occurs once in the repository, here, which is a description of the gap and not the list. CHARTER §110 rule 2 asks for both  🟢 **DONE 2026-09-01.** `CHANGELOG.md` has a `## v0.2 — 2026-09-01` section carved out of `Unreleased`, and `docs/KNOWN-ISSUES.md` is the known-issues list §110 rule 2 asks for — a list whose entries each name what is not established and which gate changes it, 🟢 **and the release itself now exists** (https://github.com/Jhongwe1/router-customFW/releases/tag/v0.2), which is the other half of rule 2 and had never been done for ANY version, each naming what is not established and which gate changes it. 🔴 **This row carried a count of that file three times and it was wrong twice more after the ten-minute one.** It read *26 entries in six sections*, was corrected to *25 entries across 7 sections (21 table rows and 4 bullets)* — true at `09e1a23` — and then **three later commits in the same session added rows** and nothing said so: 量 per commit, 25 → 25 → 26 → 27 → **28**. 🟢 **2026-09-01: the count is DELETED rather than corrected a third time.** The step is *a known-issues list exists*; how many rows it has carries no weight in that sentence, which is exactly why nobody ever re-derived it. The number now lives only in the file it describes. ⚠️ **No `v0.1` section**: the owner ruled that tag not urgent, so the release spans `v0.0` → `v0.2` and the CHANGELOG says so rather than inventing a boundary | ✅ |
| `P4b-4` ✅ **2026-09-01** | **non-text artefacts get a declared home.** Video is not committed here (`CLAUDE.md`: one is someone else's property, the others identify one physical device — video is neither, but it is also not text and this repository has no convention for it). Where the take lives, how `README.md` links it, and whether the raw footage from 2026-08-30 is kept at all. ⚠️ `REEL-1` sits under this step: the take's own spec says 60 s and the artefact measures 62.2 s  🟢 **DONE 2026-09-01.** The take's home is YouTube, named in `README.md`'s first screen and in the CHANGELOG's v0.2 section — with the sentence that says it is a replay, which is the part that makes the link honest. ⚠️ `REEL-1` (62.2 s against a 60 s spec) is unchanged and stays open under this step | ✅ |

### The DoD, split into what can be refuted

* **D1** a public reader, with only this repository, can find what `v0.2`
  contains without reading `plan/`.
* **D2** ✅ **met 2026-09-01, by an artefact whose PATH this row got wrong.**
  The row asked for `study/weekly-results.md` in `git ls-files`; what is in
  `git ls-files` is `docs/GATE-RESULTS.md`, five entries, one per closed gate.
  🔴 **The DoD named a file rather than a property**, and the property it
  wanted — *a public reader can read one entry per gate* — was unreachable at
  the path it named, because `study/` is gitignored and the owner ruled it stays
  that way. Recorded as a defect in the DoD's wording, the way `R3`'s `D3` was,
  rather than repaired silently.
* **D3** `CHANGELOG.md` has a section per released version, each with known
  issues.
* **D4** the take has a home named in a committed file.

### Refutation condition, written now

**This gate is not closed by four ticks.** It is closed when a reader who has
never seen `plan/` can answer *what is in v0.2* and *what has this project not
proved* from committed files alone. 🔴 **If closing it requires writing anything
into a committed file that reads like a hiring pitch, the gate has failed and
the four items go back to `P4b` at v1.0** — `plan/ARTIFACTS.md` §0's own
boundary paragraph is the standard, and it is the one rule in this project that
a release-engineering gate is most likely to break.

### Stop-loss, written now

* **More than 3 segments** and the remaining items move to `P4b`. This gate was
  pulled forward because four things had no owner, not because release
  engineering is due.
* **If `P4b-1`'s decision cannot be made in one segment**, the Release clock's
  `Contents` column is DELETED rather than reconciled — the same call the `Est.`
  column analysis already recommends, and a table with no wrong answer beats a
  table with two.
* 🔴 **No step here may be closed by editing `plan/`.** That directory is
  gitignored; a fix that lands only there has changed nothing a reader can see,
  which is the defect this gate exists for.

### ✅ Read one at a time on the way out, 2026-09-01

| | verdict |
|---|---|
| **D1** a public reader can find what `v0.2` contains without reading `plan/` | 🟢 **met.** `CHANGELOG.md`'s `v0.2` section says what it contains and no longer attributes it to a gitignored file; `README.md` § *Which gates make which version* says which gates define every version, released or not; `docs/KNOWN-ISSUES.md` says what it does not establish |
| **D2** one entry per closed gate, in `git ls-files` | 🟢 **met, and the row's own path was wrong** — see above. `docs/GATE-RESULTS.md`, five entries |
| **D3** `CHANGELOG.md` has a section per released version, each with known issues | 🟢 **met for the versions that exist.** `v0.0` and `v0.2` have sections; there is no `v0.1` section because there is no `v0.1` tag, and the release says it spans `v0.0` → `v0.2` rather than inventing a boundary. ⚠️ So *per released version* is satisfied, and *per version* is not — the difference is `REL-2` and it stays open |
| **D4** the take has a home named in a committed file | 🟢 **met.** `README.md`'s first screen and `CHANGELOG.md`'s `v0.2` section, each carrying the sentence that says it is a replay |

**Refutation condition** — *closed only when a reader who has never seen
`plan/` can answer what is in v0.2 and what this project has not proved, from
committed files alone.* 🟢 **Both halves have a committed owner now**, and the
second one has two: `docs/KNOWN-ISSUES.md` per release and
`docs/GATE-RESULTS.md` per gate. 🔴 **The other half of that condition —
*if closing it requires writing anything into a committed file that reads like a
hiring pitch, the gate has failed* — is the one a reader should check rather
than take.** What was written is five `did not establish` lists, a count of red
CI runs, and a table saying which of this file's own columns were copies. The
standard is `plan/ARTIFACTS.md` §0 and the gate does not get to grade itself
against it.

**Stop-loss** — three bullets, none reached. Two segments against a cap of
three. ⚠️ **The second bullet turned out not to be load-bearing**: it said
*if `P4b-1`'s decision cannot be made in one segment, delete the `Contents`
column rather than reconcile it.* The decision WAS made, and its outcome was to
delete that column anyway — and `Target` with it. A stop-loss whose fallback
is what the decision produces is not a stop-loss, it is a prediction; it is
recorded that way rather than counted as a line that held.
