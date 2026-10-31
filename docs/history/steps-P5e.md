# `PROGRESS.md` § `P5e`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `P5e`'s closing commit on 2026-10-30, once its
rows were marked. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `P5e`'s step list — ⊘ *Traded away* 2026-10-30, by the owner's decision to end the project, in ten segments (132nd–139th, 147th, 149th)

**Gate:** the repository readable and checkable by a reader with no context (§ Gate
board, row `P5e`). **Opened** 2026-10-09 (132nd segment) by the owner. Desk work runs
under the relaxed process; the flash rules, `H601`, the power handshake and `NET-165`
do not relax, and every outward act — each push, the GitHub topics and About URL, the
video upload, the external report — waits for the owner's yes for that act.

**The five questions.** A reader of the first screen must be able to answer: what this
is, what it runs on, how far it got, what is proven and what is not, and how someone
else checks it.

**Refutation condition, written before any step.** With `entrycheck` green, one reader
from outside the project, given only the repository's URL, cannot answer one of the
five within two minutes: the gate has not passed and reopens, and the question that
failed goes into the entry's *does not establish*.

**Stop-loss.** `P5e-1` past 2 segments: revert it and take the no-move route (a
repository map and directory READMEs). ③ of `P5e-3` past 1 segment for any driver: ⊘
to the next gate. The gate past 26 segments: close the steps that read their DoD and
move the rest out, rather than extend.

### The DoD rows, read by `tools/entrycheck.py`

Records are excluded wherever a row says *non-record* (`bench/`, `LOG.md`,
`CHANGELOG.md`, `docs/history/`, `docs/log/`, `docs/GATE-RESULTS.md`, `RUNSHEET.md`).
The baseline is measured by the tool at the opening and recorded in `LOG.md`.

| row | measure | target |
|---|---|---|
| E1 | `README.md` lines | ≤ 150 |
| E2 | words before `README.md`'s first `## ` heading, by the tool's printed definition | ≤ 200 |
| E3 | ISO dates in `README.md` | ≤ 1 |
| E4 | status emoji in `README.md` | 0 |
| E5 | words in `README.md`'s longest table cell | ≤ 60 |
| E6 | a mermaid diagram or an image before the first `## ` | ≥ 1 |
| E7 | a build section of ≤ 10 lines linking `docs/build.md` | present |
| E8 | `LOG.md` bytes; root `.md` pages GitHub refuses to show | ≤ 1,000,000; none |
| E9 | `RUNSHEET.md` at the root | absent |
| E10 | `CHANGELOG.md` lines; lines in its longest version section | ≤ 300; ≤ 40 |
| E11 | `PROGRESS.md` lines | ≤ 200 |
| E12 | GitHub's primary language | C |
| E13 | GitHub topics | ≥ 8 |
| E14 | a CI job that builds and tests the code: the six programs' suites and `rlxboot`'s hosttest, their summary lines in the log | present, green |
| E15 | `docs/README.md`; every tracked `.md` under `docs/` and `notes/` within two links of it | 100 % |
| E16 | references to the untracked planning directory in non-record files, by the tool's pattern | 0 |
| E17 | line of the first `#include` in each rlxfw driver `.c` (may be ⊘) | ≤ 60 |
| E18 | C and H files with an emoji or a 量／讀／推 mark (may be ⊘) | 0 |
| E19 | non-record files holding a personal path | 0 |
| E20 | `README.md`'s video is not `v0.2`'s replay | true |
| E21 | non-record files using a term from the tool's career-framing pattern | 0 |

### The steps

| Step | | What it produces | DoD (written before the work) | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`P5e-0`** ✅ **2026-10-09** | desk | this list and the board row; the three opening decisions in § Now; `tools/entrycheck.py` (the rows above) with a self-test and a mutation suite, both in CI | the board row reads `~` and names this list; `entrycheck report` on the opening tree reads RED on at least 8 rows, each named; every row's PASS fixture and RED fixture run in CI | a row that cannot fail; a definition (first screen, word, cell) the tool does not print |
| **`P5e-1`** ✅ **2026-10-17** | desk | `config/rlxfw-src/` moved to `kernel/` in one commit: the literal path in state, finding and tool files, the tools that build the path from parts, and `RECIPE_ID`'s inputs extended to `kernel/`; records untouched, since `citeresolve` reads them at their own commit. `citecheck` follows renames, landed before the move | `git grep 'config/rlxfw-src'` reads 0 outside records; `citecheck`'s verdict counts after the move equal those before, the followed renames counted; `RECIPE_ID` moves when one byte under `kernel/` changes; two builds of the moved tree byte-equal, and their `vmlinux` differs from the pre-move build's only in `RECIPE_ID`'s bytes, `System.map` equal (`FW-254`'s method); `rlxfw-marks check` and `verify` read the pre-move count; `modrecord check` rc 0; desk-sweep green except `T13`; CI green | a tool that builds the path from parts finds no file, scans 0 and stays green; a citation that goes blind instead of red — 量 at `fb5a5d17`, 125 of `citecheck`'s 535 live citations point into the moved tree (122 by suffix, 3 by full path) |
| **`P5e-2`** ✅ **2026-10-30** | desk | the large files split, frozen and indexed, every move verbatim and proven by `docmove`: ① `LOG.md` keeps the current month, earlier months move to `docs/log/<YYYY-MM>.md`, entries selected by date; ② `RUNSHEET.md` to `docs/history/`; ③ `CHANGELOG.md` whole to `docs/history/`, and a new one of ≤ 40 lines per version that summarises and links back; ④ `PROGRESS.md` ≤ 200 lines — the board one line per row, its long cells and the `Est.` analysis verbatim to `docs/history/`, `docsize` lowered in the same commit; ⑤ `docs/KNOWN-ISSUES.md` split into the current issues (≤ 150 lines) and `docs/history/known-issues-closed.md`; ⑥ `docs/spec/README.md`, an English entry to `SPEC.md`: its map, how to read a row, the most-cited rows, with `SPEC.md` itself unchanged; ⑦ `docs/reports/README.md`, one row per `docs/GATE-RESULTS.md` entry: one sentence, its claims, what it does not establish; ⑧ `docs/FINDINGS.md` ≤ 60 lines under a `docsize` budget, the rest verbatim to `docs/history/`; ⑨ every checked citation into a moved line re-pointed — 量 at `fb5a5d17`: 12 into `LOG.md`'s August and September, 7 into `RUNSHEET.md`, 3 each into `docs/KNOWN-ISSUES.md` and `docs/FINDINGS.md`, 1 into `PROGRESS.md` | E8, E9, E10 and E11 green; `docmove` rc 0 for every move; after the commit `citecheck` reads 0 failed and 0 suspended; `spec-check`, `cfcensus check` and `docsize` (new budgets) rc 0; `docs/reports/README.md` has one row per entry | a repaired citation that lands on the same token in a different sentence — read each line's prose; `docsize`'s 50 % floor failing the shrinking commit; a new `CHANGELOG.md` that restates releases instead of summarising them |
| **`P5e-3`** ✅ **2026-10-18** | desk | entry pages: ① `docs/README.md` ≤ 80 lines in three layers — start here, reports, reference and record — links only, no state; ② `docs/drivers/<name>.md` for timer, gpio, keys, wdt, spi, nic, switch and entropy, each ≤ 80 lines: what it does, its registers and their sources, what holds on the silicon, known limits, links to the `.c`, `notes/` and `SPEC.md` rows; `kernel/README.md` and `src/README.md` index the code; ③ (may be ⊘) driver file heads slimmed — the first `#include` by line 60, the version history verbatim to `docs/drivers/<name>-history.md`, emoji and 量／讀／推 in C and H rewritten as `MEASURED:`, `READ:` and `INFERRED:`, the line citations into each `.c` re-pointed, one driver per commit; ④ `docs/decisions/`, ten ADRs of ≤ 25 lines; ⑤ `docs/charter.md`, `docs/build.md`, `docs/flash.md` and `docs/method.md`, with every reference to the untracked planning files in a non-record file re-pointed at them; ⑥ `tools/README.md` placing every tool in one of four classes — bench, build, check, census | E15 and E16 green; eight driver pages, each ≤ 80 lines; ten ADRs; `tools/README.md` lists as many tools as `git ls-files tools` holds; ③ if done: E17 and E18 green and `citecheck` 0 failed | `docs/README.md` becoming a second owner of § Now; driver pages restating `notes/` instead of linking it; ③'s citations re-pointed without reading each line's prose |
| **`P5e-4`** ✅ **2026-10-17** | desk | CI and the GitHub page: ① a `build-host` job — the six programs' suites, `rlxboot`'s `hosttest` and `qemutest`, and each `src/fuzz/` harness over its corpus once, `ci-expected.tsv` and the census measured before `ci.yml` changes; ② (optional) a nightly `build-target`: the pinned toolchain cached, an image built with `--recipient`, its sha256 compared with the release manifest; ③ the text checks in their own workflow, so the code badge reports code; ④ two badges; ⑤ eight or more topics and an About URL; ⑥ `.gitattributes`: `tools/** linguist-detectable=false`, `bench/** linguist-generated`; ⑦ a root `Makefile` with `image`, `userspace`, `test` and `docs`; ⑧ no personal path in a non-record file | the closing commit's CI runs `build-host` and its log holds the six-suite summary line and `rlxboot`'s hosttest summary; `ci-census` counts the new suites; E12, E13, E14 and E19 green; a clean clone with only gcc runs `make test` to rc 0, in CI | a suite that finds no test program and reads 0 ran and green; census arithmetic that does not close; `linguist-detectable=false` hiding `tools/` without `tools/README.md` saying so |
| **`P5e-5`** ✅ **2026-10-19** | desk | `README.md` rewritten once, after `P5e-1` to `P5e-4`: a first screen that answers the five questions in ≤ 200 words, with a diagram and three links (the release, `docs/KNOWN-ISSUES.md`, `docs/FINDINGS.md`); below it, what works (layer, what is rlxfw's own, its state on the silicon, evidence), what does not, numbers, build and flash (→ `docs/build.md`), a repository map (→ `docs/README.md`), how it was verified (→ `docs/method.md`), hardware, how it was built (tools, the division of work, what is the author's), licences; `docs/architecture.md` with three mermaid diagrams — boot and trust chain, flash layout, processes and privileges; one bench photo ≤ 500 KB under `media/`; the old README verbatim to `docs/history/` | E1–E7, E20 and E21 green; `docmove` rc 0; `citecheck` 0 failed; the three link targets exist | the tool's first screen differing from what a 1080p screen shows — the tool prints its definition; the README written before the paths settle; *how it was built* written as a defence instead of a record of provenance |
| **`P5e-6`** ⊘ **2026-10-30** | bench 1 · desk 1 | the video, recorded once and cut twice: ① 60 s without narration — power on, `RLXBOOT-KEY`, `SIG ok` and `DIGEST ok`, the kernel, `rlx0` pinging both ways, `httpd` answering; ② 3–5 min — a RAM boot, a boot from a slot through `rlxboot`, an update with one flipped bit refused, ping, `httpd`'s and `dnsfwd`'s privilege drops, and the power cut during an update as a replay of `R8b`'s captures (`bench/2026-10-07/`), captioned as a replay; ③ (may be ⊘) the power cut filmed live, which needs a slot write and the owner's dated yes; ④ the reel's definition committed, so a clean clone regenerates the replayed part with `replay-capture.py reel` | both links in `README.md`, ① on the first screen; the regenerated replay equals the published one by sha256 or by frame, whichever the tool guarantees — measured before this DoD is used; `docs/media.md` names each segment's capture and `RLXFW-ID0`, compared by the tool; terminal text ≥ 18 pt; the upload and the link are the owner's acts. **⊘ *Traded away*, 2026-10-30, by the owner's decision to close the project, which reaches past this list's own ⊘ clause**: both links landed, ① on `README.md`'s first screen and ② below it, and `docs/media.md` names each take's captures and the `RLXFW-ID0` that `bootslot judge` and `looprun` compared; not met: the replay and ④, never recorded, ③, not filmed, and the 18 pt, not measured | an encoder that makes equal sha256 impossible; rewriting flash for a shot while slot A already holds `T` |
| **`P5e-7`** ⊘ **2026-10-30** | desk | the `TCCNR` defect reported to `shibajee/linux-rtl8196e`: four bit-setting functions read a 32-bit register into a `u16` while the control bits sit at 31:28, so they never set them, with no warning under `-Wall` (`docs/driver-diff.md` § 3.5 ①); optionally ② and `TCIR`'s write-one-to-clear bits cleared by a read-modify-write | reconfirmed at the project's current HEAD before sending; only code, the comparison and the fix are sent, nothing that identifies this unit; passes when the report is sent and its outcome recorded — merged, declined, or 30 days without a reply — not when it is accepted; sending is the owner's act. **⊘ *Traded away*, the owner's ruling of 2026-10-30 not to wait**: sent 2026-10-19 as `shibajee/linux-rtl8196e#1`; on 2026-10-30 it is open, with no comment and no review, and its 30 days end on 2026-11-18 | a defect already fixed upstream: clone its HEAD first |
| **`P5e-8`** ✅ **2026-10-30** | desk | the close: a `docs/GATE-RESULTS.md` entry, § Now rewritten, a `LOG.md` entry, `CHANGELOG.md`'s Unreleased section, and this list verbatim to `docs/history/steps-P5e.md` | on the closing commit: desk-sweep green except `T13`, CI green, `entrycheck check` green with its waivers named; the entry's *does not establish* names the reader test's result, whether ③ of `P5e-6` was filmed and ③ of `P5e-3` done, and the three opening decisions | the README's video link still pointing at `v0.2` (E20) |

**Order.** `0 → 1 → 2 → 3 → 4 → 5 → 8`, with `2`, `3` and `4` in parallel once `1` has
landed; `6` and `7` at any time — `6` needs one seating, and `5`'s video link follows it.
**Closes when** every step reads its DoD. May be ⊘, each with a reason and a category:
③ of `P5e-3`, ③ of `P5e-6`, the optional parts of `P5e-7`, and `P5e-1` by its
stop-loss route. Nothing else.
