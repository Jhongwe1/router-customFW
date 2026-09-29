# `PROGRESS.md` § `R1y`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R1y`'s closing commit on 2026-09-30,
once its rows were closed. A record: never edited. Cite a step by its id;
`tools/docmove.py` proves the move.

## `R1y`'s step list — ✅ CLOSED 2026-09-30, in one segment (117th)

**Gate:** the record's maintainability (§ Gate board, row `R1y`), desk only.
**Opened** 2026-09-30 by the owner (`LOG.md` 第一百一十七段). **Stop-loss: three
segments** (117th–119th), the owner's, who expects one. The owner's relaxation
of 2026-09-27 carries over (no frozen cards, predictions where they are
needed); the flash rules do not relax, and no step touches the board.

**This list is at the end of the file** (`FW-110`), and `R1y-4` moves every
closed list above it into files of their own.

### Scope, as booked and as ruled at opening

The row booked on 2026-09-23 names four enforcers. The owner's rule of
2026-09-26 — no new checker unless it blocks bricking, an `H601` leak or a
misjudged result — came after the booking and decides them:

* **⊘, each this sentence and not a tool:** the `FW-109` enforcer (a quoted
  string beside a `FILE:NNN` must occur at that line); a cite-by-id enforcer;
  a liveness check on `SPEC.md` § 17's owner column (`FW-111` ①); `cfcensus
  check` comparing the blocks it generates (`FW-111` ②). None blocks one of
  the three. What they would have enforced is repaired once instead: § 17 by
  `R1y-6`, the generated block by `cfcensus write` at this gate's close.
* **Kept:** `TOOL-2`'s three defects, repairs to existing instruments —
  `FW-137` a misjudged result, `FW-138` an exemption wider than its reason in
  the `H601` auditor, `FW-139` two comments; the resolver, which reads and does
  not check; the restructure.
* **`SPEC.md`: § 17's owner column only** (the owner, 2026-09-30). No row is
  rewritten and § 19 is not re-sectioned in this gate.

### What the gate starts from

量 at `7c4c694`, by `awk` over the level-2 headings: `PROGRESS.md` is 1,018,554
bytes — § Now with its preamble 5.5 K, the fourteen closed step lists about
430 K, § Session ladder 199 K, § Carried forward 249 K, § Corrections 93 K,
§ Gate board 30 K. `SPEC.md` is 1,410,196 bytes in 821 rows. `FW-110` counted 77
line citations into `PROGRESS.md` at `f557873` — 15 in frozen bench artefacts,
43 in `LOG.md`, 19 in files `citecheck` checks; `R1y-1` recounts them.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R1y-0`** ✅ **2026-09-30** | desk | This list, § Now and the board's row | `C12`, `cfcensus` and `docsize` green on it | A scope that keeps a checker the 2026-09-26 rule excludes |
| **`R1y-1`** ✅ **2026-09-30** | desk | The blast radius, measured by doing the move in a throwaway clone: a full `desk-sweep` of the unmoved and of the moved tree; every line citation into `PROGRESS.md` classed by citing file and by whether its line moves; every parser of this file's structure | Every step red in the moved tree and not in the control named with its cause | A step the sweep did not run read as green; an index heading holding *step list*, which `cfcensus` and `C12` parse as a step list. 🟢 **Done** (`$FWRE_WORK/rebuild/s117/blast/`): the move made at `7c4c694` in a throwaway clone and a full `desk-sweep` of each arm, 114 steps in both. The control's one unexpected red is `test-config-gates` (a clone lacks the gitignored `build/`); the moved arm added six — `spec-check` (C5 on `FW-73` and `FW-75`, and C12 on the index heading this list's brief gave), `citecheck`, `test-citecheck`, `docsize`'s floor, and `cfcensus` with its ratchet, which refused outright. 78 line citations of `PROGRESS.md`: 16 in checked files, 11 of them into moved lines; `docs/GATE-RESULTS.md` holds none, so the risk `R1y-4`'s row names did not exist. The brief's heading pattern matched 12 of the 14 closed lists |
| **`R1y-2`** ✅ **2026-09-30** | desk | `TOOL-2`: `FW-137`, `FW-138` and `FW-139`, each as that row says it is settled | The row's three controls | Repairing `--probe`'s join so that the thirteen joins that already read move. 🟢 **Done**: `FW-137` — the join prints the first host landmark past the window on an `after` line with its distance, and the seven rounds read the `D8` values there while every line the old tool printed is unchanged, 量 by two scripts that share no code; the value sits on the `after` line, not on the `--` line the control's wording assumed. `FW-138` — an `"exact"` scope and its control A3; the widening probes fire and the real lines stay silent, and the same probe on the nine other `"line"` entries moved three to `"exact"` and rewrote six reasons, the CI corpus unchanged. `FW-139` — both comments name `N41`, which alone kills U3's mutant |
| **`R1y-3`** ✅ **2026-09-30** | desk | A resolver for line citations in records: the cited text at the citing line's commit, and where it lives now | A fixture whose lines move to another file, with a mutant that reads `HEAD` killed; one `LOG.md` entry's `PROGRESS.md` citations resolved | A record line edited inside its own segment dates its citation late (`notes/record-integrity.md` § 5.6); short lines match everywhere. 🟢 **Done**: `tools/citeresolve.py`, 1,614 lines of which about 535 are its self-test, with a CI step and a `ci-expected.tsv` row. 21 cases; the `HEAD`-dated mutant is killed by 14 of them and kept in the tool as R14. It dates by whole-file `git blame -C`, because `-L n,n` misdated 79 of `LOG.md`'s 425 citing lines. On `LOG.md`'s 44 citations of `PROGRESS.md`: 15 at one location, 1 ambiguous, 2 refused, and 26 whose rows were rewritten or grew in place (`FW-158`, `notes/record-integrity.md` § 5.7). The DoD's population was empty: the `2026-09-23` entries cite `PROGRESS.md` nowhere, so all 44 were read instead |
| **`R1y-4`** ✅ **2026-09-30** | desk | The move: the fourteen closed step lists to `docs/history/steps-<gate>.md`, § Session ladder and § Corrections to `docs/history/`, § Carried forward's closed and declined rows appended to `docs/history/progress-carried-forward.md`; the parsers `R1y-1` names adapted; every line citation into moved text in a file `citecheck` checks repaired and read against its sentence; `docsize`'s budgets lowered; `CLAUDE.md`'s *until `R1y`* sentence rewritten | `docmove` conserves every block; the moved tree's `desk-sweep` reads as the control's (🔄 2026-09-30: dropped at the owner's request for speed — the suites the move touches, and CI on the pushed head, which runs every declared step); no record's bytes change | `docs/GATE-RESULTS.md` is a record that `citecheck` checks, so its citations into moved lines cannot be repaired by editing. 🟢 **Done** (`b0850eb`, its tree identical to the landing clone's): `PROGRESS.md` 2,961 → 522 lines, 1,011,442 → 95,212 B; the fourteen lists, the ladder, § Corrections and 87 closed or declined rows moved, `docmove` 1,064 of 1,064 at `--min-chars 1`, a dropped after-file its negative control. `cfcensus` and C12 read `docs/history/steps-*.md` as well, so their verdicts on the same population are unchanged and both run with no list in this file, shown on a variant; C5 repointed on `FW-73`, `FW-75`, `MEM-14` and `FLM-10`; 12 checked citations repaired, one of which had named the wrong row since `f3c425d` while `citecheck` read it `STABLE`; 9 stale baseline rows deleted and none added; `docsize` 98,100; no record's bytes changed but the append to `docs/history/progress-carried-forward.md`. The touched suites green, 15 of 15; CI on `b0850eb`, the first run of every declared step on the moved tree, success (run 36628136555) |
| **`R1y-5`** ✅ **2026-09-30** | desk | § Gate board: each closed gate's cells cut to what closing it meant and its evidence, the old cells moved verbatim to `docs/history/` | `docmove` conserves every block; `cfcensus` reads the same gate states | An evidence link lost in the cut. 🟢 **Done** (`504ca55`): 16 rows; `docmove` 886 of 886; `cfcensus` reads the same gate states; no checked citation lands on a board line. Three old cells were no longer true and were not copied — `R1h`'s D side, `P4b-gate`'s `REEL-1` and `IMG-1`, `P2`'s *`R6b` owns*; `S0` and `R0` have no entry and no step list |
| **`R1y-6`** ✅ **2026-09-30** | desk | `SPEC.md` § 17: each open row whose owning gate is closed or absent re-owned by a live gate, or ⊘ with a category and a reason | `spec-check` green; no open row names only a closed gate | A row forced onto a gate that will not measure it, which is the defect being repaired. 🟢 **Done**: 41 rows open at `7c4c694` (70 on 2026-09-23; `R6b` settled 29). Four re-owned — `REG-13`, `REG-14` and `FLS-06`–`FLS-08` to `R8`, `FW-67` to `R9`; 22 ⊘, each with its plan-§ 17 category, a reason and a reopening condition; 8 answered by their own text or their owner file, marked ✅; 3 split into ✅ and ⊘. Id cells carry the least-settled half's mark; `LDR-22`'s and `CPU-45`'s main rows lost their stale leads. Nine rows stay open, each naming a live gate, `LDR-21` and `FW-68` through `C-13` (`R8`) and `VDR-1` (`R9`) — 量 by two parsers that share no code, the main session's firing on `7c4c694` as its control. `spec-check` green before and after |
| **`R1y-7`** ✅ **2026-09-30** | desk | The write-up: `docs/GATE-RESULTS.md` entry 15; `cfcensus write`; `NET-165`'s no-unattended-standby rule into `CLAUDE.md`, restated by the owner on 2026-09-30 | The DoD read one row at a time, with what was not established | Calling the gate closed on a green sweep instead of on the DoD. 🟢 **Done**: entry 15, with the operating clause and its census re-run at fifteen entries; `cfcensus write`; `CLAUDE.md` § At the bench — the loader answers ARP only after `IPCONFIG` (`NET-95`) and is never left at the prompt unattended (`NET-165`); this list moved to `docs/history/steps-R1y.md` in the closing commit, `R1y-4`'s convention |

### The DoD, split into what can be refuted

* **D1** — `PROGRESS.md` holds state only — § Now, § Gate board, § Release
  clock, the open rows of § Carried forward, the census block and the open
  gate's list — and every block moved out is conserved verbatim (`docmove`,
  0 missing), with `docsize`'s budgets at the measured size + 3 %.
* **D2** — every line citation into moved text in a file `citecheck` checks is
  repaired and read against its sentence, and `citecheck` reads 0 `ROT` and 0
  suspended after the commit; no record's bytes change (`git diff` over
  `LOG.md`, `bench/`, `CHANGELOG.md`, `docs/GATE-RESULTS.md` and the existing
  `docs/history/` files shows appends only).
* **D3** — every line citation of `PROGRESS.md` in `LOG.md` resolves to one
  location, to several (listed), or to none, each none explained.
* **D4** — `TOOL-2`'s three controls, as its row writes them.
* **D5** — no open § 17 row names only a closed gate, or none.
* **D6** — the final tree's full `desk-sweep` reads as `R1y-1`'s control, and CI
  is green on the pushed head. 🔄 2026-09-30: the full `desk-sweep` was dropped at the owner's request for speed; CI on the pushed head runs every declared step.

### Refutation conditions, written now

* A block `docmove` reports missing: the move lost text, and it does not land.
* A checker's verdict on a population the move did not change moves —
  `cfcensus`'s open rows, `spec-check`'s findings, `C12`'s ids: the move changed
  meaning, not location.
* The resolver's `HEAD`-reading mutant survives: the tool does not depend on the
  citing commit and resolves nothing.
* A citation in `docs/GATE-RESULTS.md` passes `citecheck` only once its entry is
  edited: the record rule and the checker disagree, and the owner decides. No
  entry is edited to make a check pass.

### Stop-loss, written now

* **Three segments**, the owner's. At the stop-loss the gate closes on what is
  done, and entry 15 lists the rest.
* **No record is edited.** A step that would need to stops and goes to the owner.
* **`R1y-4` lands only on a sweep that reads as the control's.** 🔄 Dropped 2026-09-30 at the owner's request for speed: it landed on the suites it touches, and CI ran the rest.

### What this gate must be able to answer

* *「`PROGRESS.md` 為什麼長到 1 MB？」* → `FW-112`'s chain, and `D1`.
* *「舊紀錄引用的 `PROGRESS.md` 行號，那一行現在在哪裡？」* → the resolver, and
  `D3`.
