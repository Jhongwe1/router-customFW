# PROGRESS

**The one file that answers "where am I".** House rule 1: one piece of state has
exactly one owner. This is the owner of *current position*. Nothing else may
restate it — other files reference a gate id, they never say which gate is active.

Read this first, every session. Update it before you close, in the same commit as
the work (house rule 6).

---

## Now

| | |
|---|---|
| **Active gate** | **None.** **`R8` closed 2026-10-04 by splitting its row**: it closes on the three clauses `R8a` read from RAM (`docs/GATE-RESULTS.md` entries 16 and 18), and `R8b` — persistence and the ten power cuts — is a row of its own, booked and not open, because its experiment is an interrupted flash write and it waits behind `R9`. `R8a` and `R7` closed 2026-09-30 (entries 16 and 17). Which gate opens next is the owner's decision. |
| **Active step** | None: no gate is open, and `R8` closed with no step list of its own. The owner's relaxation of 2026-09-27, widened on 2026-09-30, continues (2026-10-02) — no frozen cards, no desk-sweep per commit; the flash rules, `H601`, the power handshake and `NET-165` did not relax, and the 119th segment issued no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`. <!-- C12: between gates, no step id --> |
| **Session history** | `LOG.md`, one dated entry per segment. What this table said until 2026-09-23 is archived verbatim in `docs/history/progress-now.md`. |
| **Next after this** | 🔄 **2026-10-04（第一百一十九段）**: `R8` closed by splitting its row; which gate opens next is the owner's. **`R9` is the one that unblocks `R8b`**: its vendor column needs the vendor firmware still bootable from flash, and `R8b`'s first slot write destroys 921,619 of the vendor kernel's 987,155 bytes (`FW-167`). Entry 18's clause run fires on `R7` → `R8` on what entry 17's named, persistence, and adds no instruction. **`FW-184` is fixed** and shown on the device (`docs/KNOWN-ISSUES.md`). Entry 14's clause still names the mechanism of `rlx0`'s transmit fault — its doable part is `M5`, one press and no image. The mainline builds `SWCORE=n` since 8g, so `R9` builds `quiet-swcore`. <!-- C12: between gates, no step id --> |
| **Blocked on** | Nothing. Waiting on the owner, blocking no step: **`R8b` needs `R9` first and a dated yes per flash write**; `CLAUDE.md` § Flash has every press claim rlxfw's `n_writes`, which carries no information (`FW-142`); `MK6`, `MK7` and `MK9`'s witnesses cannot fail, nor `MK10`'s on a standard-`/init` image (`FW-143`); `CLK-42` 殘留 waits for a gate; `FW-172` stays 推, its deciding experiment `CPU-19` ①'s and unscheduled; no CI step runs the host tests under `src/`, so `FW-184`'s regression test runs only at the desk; `r3-4/cells/f184a` (485 MB) is kept for a rebuild without a re-stage until the owner says to delete it; and the main session's rulings in entries 14 to 18 stand unless the owner overrides them. |

**Step list for the active gate**: none is open. The next gate's list goes at
the **end** of this file, where a new list or row moves no line a checked file
cites (`SPEC.md` `FW-110`), and moves verbatim to `docs/history/steps-<gate>.md`
in its closing commit, as `R1y`'s, `R8a`'s and `R7`'s did; `cfcensus` and `C12`
read the lists there as well (`R1y-4`).

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

---

## Records moved out of this file

These records were moved verbatim to `docs/history/`: by `R1y-4` on 2026-09-30
from `PROGRESS.md` at `e274ccb`, and each closed gate's step list since in its
closing commit. A record is never edited; a record's line citation is read with
`tools/citeresolve.py`.

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
| § Session ladder | `docs/history/progress-ladder.md` |
| § Corrections | `docs/history/progress-corrections.md` |
| § Carried forward's closed and declined rows | `docs/history/progress-carried-forward.md` |
| § Gate board's closed rows as they stood before `R1y-5` | `docs/history/progress-gate-board.md` |

---

## Gate board

Status: `·` not started · `~` in progress · `✓` closed (needs an evidence link)
· `⊘` deliberately not done (needs a reason and a category — plan §17)

| Gate | What closing it means | Est. | Actual | Status | Evidence |
|---|---|---:|---:|:---:|---|
| **S0** | backup restored and verified. `S0b`, three power experiments written up, is `⊘`, so the definition is the backup alone. | 1 | 1 | **`✓`** | `S0a`: `LOG.md` 2026-08-23 — copy ② restored with zero diff on 7,770 paths, copy ③ read back 19/19 (`C-10`, `tools/verify-backup-copy.sh`) · `S0b` `⊘`: `notes/power-and-programmer.md` §4 |
| **R0** | vendor kernel booted from RAM, no flash-write command issued, and the loader head and the `cr6c` header unchanged over 512 of 4,194,304 bytes. The criterion is not *"0 flash bytes written"*, which no instrument here can establish. | 5 | **7** | **`✓`** | `RUNSHEET.md` Results — seating 2 part three · `bench/2026-08-24c`–`f`, 81 captures, 18 prediction blocks (`G5`, `G7`, `G8-pre`/`G8a`/`G8b`) |
| **R1-gate** 🆕 | cache-management model settled on silicon, and the CP0 census read — `PRId`, `Config`, `Config1`, `Status.BEV`, `Count`/`Compare`. Three of the four downstream decisions it unlocks have a reading; the fourth, ② — whether `R6`'s descriptor rings need an uncached window — is recorded as not met and moved to `R1h`. | 5 | **9½** | **`✓`** | `docs/GATE-RESULTS.md` entry 1 (2026-08-26) · step list `docs/history/steps-R1-gate.md` · `docs/rlx-cache-and-cp0.md` · `RUNSHEET.md` § Results B4 (`R1g-4a`, `R1g-4b`) |
| **R1h** ✅ | what `R1-gate` closed without, on one payload and one seating: cache geometry measured (`CPU-25`), the D side of coherence (`R1-gate`'s decision ②, `CPU-45`), whether this core retires the `cache` instruction (`CPU-44`), and write-through versus write-back-without-write-allocate (`CPU-19` 殘留). Three came back with readings; the D side closed without a measurement. | **—** —— **deliberately not costed into this column**, whose own analysis below says it is not a quantity. The gate’s budget lives in its step list: **4 segments, 猜, uncalibrated** | **5½** | **`✓`** | `docs/GATE-RESULTS.md` entry 3 (2026-08-29) · step list `docs/history/steps-R1h.md` · `notes/cache-model.md` |
| **R2a/b/d** 🆕 ✓ | which GPL drop this firmware was built from (structural similarity against six real builds), and the two greps for what the vendor kernel emulates. It closed on its stop-loss outcome: `TC-02` stays 推 because the metric measures the toolchain rather than the drop (`TC-18`), the emulation question is answered (`CPU-47`), and no container was needed. | 5 | 5 | `✓` | `docs/GATE-RESULTS.md` entry 2 (2026-08-28) · step list `docs/history/steps-R2a-b-d.md` · `notes/rebuild-vs-shipped.md` · `notes/vendor-toolchains.md` · `SPEC.md` `TC-11`…`TC-20` |
| **R3** 🆕 | my kernel boots to a shell and pings, as five claims: D1 delivered and entered, D2 my kernel entered (not the vendor's), D3 early bring-up, D4 a shell that accepts typing, D5 ping both directions. All five held on one boot. | 12 | **18** | **`✓`** | `docs/GATE-RESULTS.md` entry 4 (2026-08-31) · step list `docs/history/steps-R3.md` · `bench/2026-08-30b`–`d` and `bench/2026-08-31`–`c`, seatings 5–8 · `config/r3-11-reel.tsv`, v0.2's reel |
| **R4** 🆕 | edit → result in < 90 s; scripted reset via WDT. | 5 · **plan 8** | **4** | **`✓`** | `docs/GATE-RESULTS.md` entry 7 (2026-09-02) · step list `docs/history/steps-R4.md` · `notes/dev-loop.md` §7 · `bench/2026-09-01/` (`Y-r02`…`Y-r20`) · `bench/2026-09-02/`, seating 10 |
| **R5** 🆕 | six drivers in-tree, each accepted, 10 boots without an oops, each with a compile-tested DT binding marked *not probed on hardware*; and `docs/driver-diff.md`, written blind, then diffed against the two public RTL8196E trees in two layers scored separately (fact / decision), every disagreement decided on the silicon or recorded undetermined. `D4` was met as a ratio, not a frequency. | 24 | **32** | **`✓`** | `docs/GATE-RESULTS.md` entry 8 (2026-09-11) · step list `docs/history/steps-R5.md` |
| **R1-pub** | instruction / hazard / Lexra-ASE census + the vendor-kernel emulation column + the three-toolchain silicon comparison (`R2c`) — the first independently publishable artefact, `docs/rlx-isa.md`. | 14 | **20** | **`✓`** | `docs/GATE-RESULTS.md` entry 9 (2026-09-16) · step list `docs/history/steps-R1-pub-R2c.md` |
| **R1z** 🆕 | paying the debts this repository's own record names, with the population derived from § Carried forward rather than hand-picked. `tools/cfcensus.py check` went from 29 findings to 0, and it is a gate now. | 3 | **3** | **`✓`** | `docs/GATE-RESULTS.md` entry 10 (2026-09-16) · step list `docs/history/steps-R1z.md` |
| **R6** | my Ethernet driver: `ping`, an `iperf3` number, 30 min flood clean. `D1`–`D3`, `D5` and `D6` met and `D4` met in part; the named stretch, per-port VLAN (`R6-6`), not met. | 37 | **18** | **`✓`** | `docs/GATE-RESULTS.md` entry 12 (2026-09-22) · step list `docs/history/steps-R6.md` · `notes/switch-driver.md` § 8 · `SPEC.md` `NET-43`–`NET-45`, `NET-48`–`NET-54` |
| **R7** ✅ | my userspace, six programs of mine plus busybox rebuilt from the drop's source, running on the silicon — and a pass condition that had to be **re-specified before anything could count**: both sources named on 2026-08-25 read 0 on a static binary by construction (a `PT_DYNAMIC` walk finds no such segment; `system` is *defined*, not undefined, in a static link), and 0 was the passing answer, so the gate's own instrument could not fail. `tools/uspacescan.py` replaces both and refuses rather than reporting 0 when it cannot decide; over the image, 0 forbidden imports from both sources on all six. The baseline was corrected in the same pass, including that the published method could have missed `system` itself | 34 | **1** | **`✓`** | `docs/GATE-RESULTS.md` entry 17 (2026-09-30) · step list `docs/history/steps-R7.md` · `notes/userspace-integration.md` · `notes/entropy.md` · `notes/rootfs-census.md` · `docs/KNOWN-ISSUES.md` (two device-only defects, both since fixed and shown on the device) · `SPEC.md` `FW-160`–`FW-184` |
| **R8** ✅ | signed update accepted, one flipped bit rejected, and a version below the anti-rollback counter rejected — the three clauses `R8a` read on the silicon, from RAM, with no flash-write command issued. 🔄 **Closed 2026-10-04 by splitting the row, which is not a claim of completion**: until then the row also read *10 power-cuts survived*, and that clause, with the persistence it implies, is an interrupted flash write by construction, so it is `R8b`'s own row below, behind `R9` | 18 | **2** | **`✓`** | `docs/GATE-RESULTS.md` entries 16 (2026-09-30) and 18 (2026-10-04) · `R8a`'s and `R8b`'s rows below |
| **R8a** ✅ | the half of `R8` that needs no flash write: a signed container staged in RAM, verified by `rlxboot` — ① a correct signature accepted and the image boots, ② one flipped bit anywhere refused, ③ a version below the anti-rollback counter refused. All three held on the silicon in four rounds. It is not `R8`: it establishes nothing about writing flash, about surviving a power cut, or about key management, and it is not secure boot on a part with no evidence of a key-hash fuse | **—** —— uncosted for `R1h`'s reason: the budget lives in its own step list, and `R8`'s 18 already carries this work | **1** | **`✓`** | `docs/GATE-RESULTS.md` entry 16 (2026-09-30) · step list `docs/history/steps-R8a.md` · `notes/rlxboot.md` · `notes/update-chain.md` · `SPEC.md` `FW-166`–`FW-172` |
| **R9** | three-column differential table, **third column not empty** | 16 | — | `·` | |
| **R8b** | persistence and the ten power cuts: an update written to a flash slot and booted from it through `rlxboot`, and ten physical power pulls during a write, each followed by a boot from the other slot. A row of its own since `R8` closed on 2026-10-04, and **not open**: it waits behind `R9`, whose vendor column needs the vendor firmware still bootable from flash while slot A's first write destroys 921,619 of its kernel's 987,155 bytes (`FW-167`), and behind the owner's dated yes for each flash write | **—** —— uncosted for `R1h`'s reason: `R8`'s 18 already carries this work | — | `·` | its booking and preconditions: `docs/GATE-RESULTS.md` entry 16 § `R8b`; the split: entry 18 |
| **P1** ✅ | `mfgtest` passes on a good unit, and every check has been made to FAIL once | 8 | **4** | **`✓`** | `docs/GATE-RESULTS.md` entry 11 (2026-09-17) · step list `docs/history/steps-P1.md` |
| **P2** ✅ | boot-time breakdown + throughput, both firmwares, same script. `D1`, `D2`, `D4` and `D6`–`D8` met, `D3` under its closing rule, and `D5` for ICMP and the vendor's driver, while rlxfw's own driver's reading is a failure handed to `R6b` (`NET-116`); the stretch, `P2-6`, carried to `P3` as `LA-1`. | 6 | **10** | **`✓`** | `docs/GATE-RESULTS.md` entry 13 (2026-09-25) · step list `docs/history/steps-P2.md` · `SPEC.md` `NET-116`–`NET-121`, `FW-135`–`FW-141` |
| **P3** | bring-up report — grows every gate, closed at v1.0 | 5 | — | `·` | |
| **P4a** ✅ | reproducible build: same tree built twice → same image sha256, with the positive control that changing one source byte changes it. Closed at Level 1, one machine, with Level 2 — a third party rebuilding the published recipe to the same sha256 — not closed, and the control refuted as worded: a comment byte is a source byte and does not change the image. | 1 | **1** | **`✓`** | `docs/GATE-RESULTS.md` entry 5 (2026-09-01) · step list `docs/history/steps-P4a.md` · `notes/reproducible-build.md` §7 · `SPEC.md` `TC-38`/`TC-39` |
| **P4b-gate** 🆕 | the part of `P4b` that blocks tagging, pulled forward: closing it means each of `CHARTER.md` §110's four release obligations has a committed owner, not that all four are done — version → contents (`README.md`), the per-gate ledger (`docs/GATE-RESULTS.md`), the known-issues list (`docs/KNOWN-ISSUES.md`) and the take's home. Tagging is not in this gate. | 2 | **2** | **`✓`** | `docs/GATE-RESULTS.md` entry 6 (2026-09-01) · step list `docs/history/steps-P4b-gate.md` · <https://github.com/Jhongwe1/router-customFW/releases/tag/v0.2> |
| **P4b** | complete GPL release (corresponding source, written offer, per-file modification record) + release process | 2 | — | `·` | |
| **R6b** ✅ | `rlx0`'s TX loss fixed first, then what `R6` left without an owner. The loss was the descriptor lengths, and `rtl819x-nic` 1.6 makes the vendor's convention the default; `rlx0` pings both ways on a `SWCORE=n` image, the mainline's configuration since 8g. | — | **7** | **`✓`** | `docs/GATE-RESULTS.md` entry 14 (2026-09-28) · step list `docs/history/steps-R6b.md` · `docs/nic-vendor-diff.md` § 16 · `SPEC.md` `NET-119`–`NET-169`, `CLK-49`, `FW-142`–`FW-157` |
| **R1y** ✅ | the record's maintainability: `PROGRESS.md` split into state and record — closed step lists, history and closed rows moved verbatim to `docs/history/`, with a resolver for the line citations records keep; `TOOL-2`'s three instrument defects; `SPEC.md` § 17's owner column repaired once. The four enforcers the booking named are ⊘ by the owner's rule of 2026-09-26 | — | **1** | **`✓`** | `docs/GATE-RESULTS.md` entry 15 (2026-09-30) · step list `docs/history/steps-R1y.md` · `notes/record-integrity.md` § 5.7–5.8 · `SPEC.md` `FW-137`–`FW-139`, `FW-158`, `FW-159` |
| | | **200** | | | |

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

🔴 **So the instruction cannot be carried out as written, and that is the
result rather than a failure to produce one.** The 170 planned segments still
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

---

## Release clock

**This table owns ONE thing: which versions have actually shipped.** What a
version *contains* moved to `README.md` § *Which gates make which version* on
2026-09-01 (`P4b-1`); the week estimates are planning material and stay in
`plan/`. The note below records why, because the repair is the finding.

| version | Shipped |
|---|---|
| `v0.0` | tagged 2026-08-25, **never released** |
| **`v0.1`** | — · never tagged; its contents completed 2026-08-26 |
| `v0.2` | 🟢 **2026-09-01** |
| `v0.3` | 🟢 **2026-09-11** |
| `v0.4` | 🟢 **2026-09-17** |
| `v0.5` | 🟢 **2026-09-29** |
| `v0.6` | 🟢 **2026-10-04** |
| `v1.0` | — |

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

---

## Carried forward
Open questions that outlive a single session. Each one names the gate that will close it. **An item with no owning gate is a bug in this list.**

| # | Question | Owning gate |
|---|---|---|
| `LA-1` 🆕 | 🔴 **The plan's interrupt latency measured by logic analyser — *中斷延遲（LA 量）* — has no reading, and nothing stands in for it under that name.** `P2-6` held it as a stretch with one segment, and its first rung never ran: 讀, none of `P2`'s three bench directories names the analyser, and the plan's hardware table lists it as on hand and never connected to anything. `P2`'s stop-loss wrote the failed-rung case, and the unrun rung is treated the same way: recorded as not done, with the on-die counter not offered under the plan's name. What settles it, `P2-6`'s ladder unchanged: rung 1 is the plan's own self-test, the width of one console TX bit at 38400 baud — 26.04 µs, computed before power — read within one sample period; rung 2 is a GPIO toggled on every tick, with edge-to-edge jitter idle and under `iperf3`, at least 10,000 ticks per load condition. 推 rung 2 needs an image whose tick handler toggles a pin. Not established by this row: that the analyser works at all — rung 1 is the test of that | `P3` — the bring-up report, where an interrupt-latency figure is read; assigned at `P2`'s close, 2026-09-25. ⚠️ 讀 the plan budgets `P3` at 5 desk, 0 bench and 0 instrument segments, and both rungs need the board: the seating this takes is not in `P3`'s budget, and whichever gate books it spends it |
| `UP-AUD-1` 🆕 | 🔴 **第七十二段的收工稽核列舉了「這一段做出什麼」再問誰擁有它,找到十四個擁有者檔裡的過期句子,修了七個,這是另外七個。** 它們是同一個發現的七個面:**一個進到映像裡的二進位是這個 repo 沒有過的種類**,而那些檔案描述的是舊的種類。**已修**:`docs/KNOWN-ISSUES.md` 的「No userspace of mine」與 mtime 計數、`docs/GATE-RESULTS.md` 的「open for userspace」現在式、`docs/isa-prior-art.md` 的 `R1C-1-b` 事前登記(**它發火了而既沒有兌現也沒有豁免**)與工具鏈前提、`docs/FINDINGS.md` 的「nothing here had met them」、`notes/kernel-build.md` 的 §9 標頭與「四顆現行映像」。**未修,按代價排序**:① `docs/toolchain-comparison.md` —— `TC-57` 是它自己定義的那種列(三工具鏈、一儀器、一問題)而且是 §2.2 的第三個產出物類別,另外 `:317-318` 的「所有三個 release 在這個軸上行為相同」要加「在**碼產生**上」這個範圍詞(預建的 `libc.a` 對靜態連結而言 release 就是那個旗標),`:380-383` 說 `TC-05` 的 userspace 半還是空白;② `docs/toolchain-prior-art.md` 的 `<!-- tccensus: -->` 區塊要重新產生(50→58 個 `TC-` id、39/59→41/61),而 `:298` 在標記之外,是 `XNUM-1` 的形狀;③ `docs/isa-payload.md` 要一節寫第二條 arm ——`PU` 列形、字 2 是訊號號碼左移 16 再或上 `si_code`,而不是 `Cause`、🔴 **而且它的 §6 有 `C1`/`C2`,user arm 也有 `C1a`/`C1b`/`C2`,同一支儀器的文件裡兩個不同的 `C2`**;④ `docs/isa-prior-art.md` `:729-731` 還寫著用 `objdump -d` 數 `break` 且推測來源是除零的 `break 7`,兩者都被量測取代;`:664` 的 45 與 user arm 跑的 75 不是同一個數;⑤ `notes/kernel-build.md` §9 的分類與分擁有者小表、§3.4 自己還帶著 2,395,932、§18.6 該有 `up2` 的一欄;⑥ `README.md` `:76-79`(31→36、7→12)與 `:392-400` 的工具普查(100→134 檔、48→57 支,而 `elfops.py` 在 README 裡出現 **0** 次)—— 那一段自己寫著「重新導出的計數會抓到中間的每一段」,這是它第六次;⑦ `notes/dev-loop.md` `:29-30` 的「userspace-only iteration 是另一個迴圈」要撤回 —— 在這顆映像上沒有那種迴圈,`uprobe.c` 在 `config/` 底下,改一行就移動 `RECIPE_ID`、付一次完整 `S2`,而 `:177` 的 0.159 s 是那個成本的一小部分;`notes/incremental-build.md` §7.1／§7.5 是同一件事的另一半(`config/` 現在有第二棵源碼樹,而**一個不編進任何 kernel object 的檔案照樣移動 `RECIPE_ID`**);`RUNSHEET.md` `P4`／`P9` 的數字;`config/rlxfw-initramfs.tsv` 的新列是**第一個在乾淨 clone 裡不存在的來源**(`$REPO/build/…` 被 `.gitignore` 忽略)而檔案裡沒有任何命令說怎麼產生它。⚠️ **`bench/README.md` 的索引列要等那次上電之後才加**,`capdate.py` 的 `D4` 在兩個方向上都會紅到它在為止 🔄 **2026-09-15(第七十三段收工)的結算,而第一件要說的是它沒被遵守**:🔴 **③④ 寫著「在下一次上機之前就該做」,而上機發生了而它們沒做。** 記在這裡而不是靜靜順延,因為一個被寫下又被跳過的建議,下一次就不會有人當真。✅ **已補**:`bench/README.md` 的索引列(上電後才加,如上所述)、⑦ 的 `notes/dev-loop.md` 半(新的 §17b,而它寫的是**比原本更強的一件** —— `S3` 從未為 `up2` 跑過,而且每個 cell 目錄裡都有一顆廠商的同名 `nfjrom`,所以「檔案在」不構成證據)、⑥ 的 `README.md` **initramfs 半**(31/7 → **36/12**,用 `mkinitramfs build` 自己的輸出重新導出,`grep` 標籤欄當第二讀者,兩者一致)。🔴 **⑥ 的工具普查半刻意沒修,而理由是一個陷阱**:README 寫 `git ls-files tools/` **100** 檔、**48** 支程式、拆成「**21** described / **27** not」。量 2026-09-15,用它自己寫下的判準: 🔄 **2026-09-15(第七十四段):這個交下去的量測本身也舊了，而舊化它的是同一段自己** —— `tools/emupredict.py` 與 `tools/mustrun.py` 進來，所以 `git ls-files tools/` 是 **136**、帶 `#!` 且排除 `tools/test-*` 的是 **59**。① 做的時候要**重新導出**而不是用這裡的任何一個數字；那八支完全沒出現在 README 的名單也會變。**134 檔、57 支程式** —— 這兩個無歧義。**但 21/27 那個拆分的判準是「described below」,而我用「有沒有在 README 裡出現過」量到 49/8**,加起來也是 57,**也自洽,而且是錯的** —— 換上去就是本專案自己記著的那個最難抓的型態(一對錯的數字只要差對就永遠自洽)。所以留給 ⑥ 一次做完,而**量測先交下去免得重量**:完全沒有在 `README.md` 裡出現過的 8 支是 `citecheck`／`elfops`／`emueq`／`hazpay`／`isapay`／`procgrow`／`tcpay`／`uartrate`,而 57−48=**9**,所以有一支新工具是被提到但未被描述的,那一支是 ⑥ 要自己找出來的。✅ **2026-09-15（第七十四段）又補：③④。** ③ `docs/isa-payload.md` 得到第二條 arm 的一節（新 § 11，141 行：`PU` 列形、字 2 是訊號號碼左移 16 再或上 `si_code` 而不是 `Cause`、讀數、標頭與 `C2-UPR` 範圍控制、這條 arm 沒建立什麼），而兩個 `C2` 的衝突改成**裸機那一個改名 `C5`**：量，凍結卡片裡唯一指名這支儀器 `C2` 的是 seating 23 卡片 § 6.4，而那是**使用者** arm 的；seating 21 卡片把裸機那個叫 `D2`。④ `docs/isa-prior-art.md` 的 `objdump -d` 數 `break` 方法與「來源是除零 `break 7`」推兩半就地劃掉，換成 `tools/elfops.py count` 按 opcode 數與 `TC-58` 的讀數（linked break=2，兩條都在 `__GI_abort`）；45 對 75 兩個方向都導出（payload 側 32 名字相符＋12 按 group = 44，**census 側是 37 of 39**）。🔴 **一個命名的殘留**：`tools/isa-payload.tsv` 的 `special0e` `why` 欄與生成的 `cells4.S` 仍寫 `C2`，**刻意不修** —— 量，四份原始碼的 sha256 是 `a87be346bb83e7f9`，正是 seating 23 擷取印的 `BUILD_ID`；正控制：加一行註解就變成 `4ac4cd1f6c0b61ed`。要在 nonce 本來就會動的那一次一起改。 **未動**:①②⑤、⑥ 的工具普查半、⑦ 的 `notes/incremental-build.md`／`RUNSHEET` `P4`／`P9`／`config/rlxfw-initramfs.tsv` 三件 | ~~`R1-pub-7`~~,而 ~~③④ 在下一次上機之前就該做~~ 🔄 **那個期限已經過了;③ 現在更好做,因為第二條 arm 已經在矽片上跑過,那一節可以用量測而不是預測寫** 🔄 **2026-09-16（第八十段）：十四個面裡十三個落地，而其中**五個是量出「早就付了」**。** 今天付的八項：①a①b（`docs/toolchain-comparison.md`）、②b（`docs/toolchain-prior-art.md` 五個站點，而不是原本以為的三個）、⑤a（`notes/kernel-build.md`，29→37 筆 / 580,632→626,508 位元組）、⑥b（`README.md`，100/48 → **139/62**）、⑦a⑦b⑦c，加上 ⑦d —— **`config/rlxfw-initramfs.tsv` 的兩列是這張表裡第一個在乾淨 clone 裡不存在的來源，而檔案裡沒有命令說怎麼產它** —— 它每一次被順延都是因為 `config/` 下的一行註解會移動 `RECIPE_ID`，而這一段已經移動了它，所以邊際成本是零。🔴 **五個早就付了的，沒有一個是重讀這一列發現的**：③④（`ed7eb7a` 09-15 23:31，而點名它們的規格列晚了十三小時四十三分）、①c 與 ② 的第三個子項（`26f4dfc` 09-16，而那個 commit message 從未提過 `UP-AUD-1`）、②a（`9301f44` 09-16）。⚠️ **還活著的只剩 ⑤c**：`notes/kernel-build.md` §18.6 的 `up2` 欄要一顆建置產物才能填，而這一段一次建置都沒跑。改派，第一次移交；**any desk segment that runs a build** |
| `CENS-1` 🆕 | 🔴 **沒有任何東西把一次擷取接回它填的普查列,而這個缺口已經讓一句安全警告引用了一個板子早就填掉的空白。** 量 2026-09-14(第六十八段):`tools/isacensus.py` 的四個模式都不開 `bench/` 下的任何檔;`isapay verdict` 算得出判決卻不寫回;`isacensus write` 由 **tsv** 重新產生文件區塊,而 tsv 的路線旗標只能手改。後果是 `tools/isa-census.tsv` 從 `2ee0c6d`(2026-09-13)之後就沒有被重新導出,`bench/2026-09-14/C1-P4j.log` 在 **05:57:21** 進了 repo,而 `docs/isa-prior-art.md` § 9 的安全警告在 **16:20:41** 寫下時引用 § 10 ③ 的空白當理由 —— **早 10 小時 23 分、12 個 commit**。這一段把 45 列全部重新導出(路線 ① **3 → 42**),但那是**手做的 join**,下一次一樣會過期。⚠️ 收它要一支「讀擷取 → 提議路線旗標」的工具,而它的正控制是**把一列改成過期並要求被報出來**。 | ~~`R1-pub-7`~~,或任何一段動 `isacensus` 的桌面段 🔄 **2026-09-16（第八十段）：那個具名 gate 劃掉，常設指示留下。** 它在 2026-09-16 走完它自己的步驟而沒有做它，把它留在這一格是讓一列**看起來**有擁有者。這不是改派：常設指示自己就是一個擁有者，而它一直在那裡 |
| `CORR-1` 🆕 | ⚠️ **上電前的更正檔第一次早於它自己的擷取進 git,而那是判例還是一次性,沒有任何東西決定。** 量 2026-09-14:十八份 `CORRECTIONS-block*.md` **零份**在自己目錄第一個 `.log` 之前 commit(十七份同一個 commit、一份更晚),正控制是 33 個 bench 目錄裡有 17 個的 `PREDICTIONS-*` 做到了,所以「BEFORE」是說得出口的判決。這一段的兩份(`f9fffa4`,17:28:45,上機 19:00)做到了。🔴 **但沒有任何檢查器要求它** —— `check-predictions` 讀的是卡片與擷取的 mtime,更正檔完全在它的視野外,而 `RUNSHEET` 的生命週期規則只說「更正寫進新檔」,沒說何時。⚠️ 收它的兩個選項各有代價:① 加一條檢查(要先決定「更正檔必須早於擷取」是不是真的普遍成立 —— 上電後才發現的缺陷本來就不可能早於);② 只把它寫成判例,像 `BRD-README-1` 選 ② 的理由。**這一列不替擁有者做決定。** 🔄 **2026-09-14 晚,收工稽核補一個觀察而不是一個決定**:`RUNSHEET.md` § *Four rules about the card's lifecycle*(`:3798`)對「更正檔什麼時候 commit」**一個字都沒說**,它最接近的一句是 `:3855` —— *"`CORRECTIONS-block14.md`, which is written **after** the seating, is not a card, and therefore had nothing telling anyone to check it."* 而這一段的頭條宣稱(更正檔早於擷取)目前只活在一則 commit 訊息、`LOG.md` 與 `PROGRESS.md:17` 裡,**而那三個地方未來的卡片作者都不會讀**。⚠️ **一條沒有家的規則讀起來像一個缺席而不是一個決定** —— 所以選項 ② 若成立,`RUNSHEET` 仍然要有一句話說「這是判例不是規則」,否則兩個選項在檔案裡長得一模一樣。 | 任何一段動 `check-predictions` 或 `RUNSHEET` 的桌面段 |
| `BRD-2` 🆕 | ⚠️ **`bench/README.md` 的 captures 欄對一個還沒跑的目錄是一個預測,而四個檢查沒有一個看得到。** 量 2026-09-14(收工稽核):`:87`／`:88` 對 `2026-09-14b`／`-14c` 寫 **7** 與 **27**,而磁碟上兩個目錄各只有兩個 `.md`、**零個 `.log`**;`:44` 自己定義那一欄是 *"counts `*.log`"*。`capdate` 的 `D4` 依設計是對**目錄名**的集合比對(`tools/capdate.py:328-330`),`D1`／`D2`／`D3` 只對**持有擷取的**目錄發火,所以一個零擷取的目錄落在四個檢查之外。🟢 **今晚跑完它們就會變成對的**,所以這不是一個錯誤而是一個**沒有守衛的視窗** —— 而收工稽核那句「`bench/README.md` 的索引已經寫著兩份更正檔」比它讀起來窄:索引欄對了,計數欄沒有被任何東西看過。⚠️ 收它是一個 `capdate` 案例(captures 欄非零而目錄沒有 `.log` → 報出來),而它的正控制是這個 repo 要求的那一種:**把一列改成不符,必須被報出來**。 | 任何一段動 `capdate` 的桌面段 |
| `CHLOG-1` 🆕 | 🔴 **`CHANGELOG.md` 的十三則條目全部在 `## Unreleased` 標題之上,所以那個標題不再包含它宣稱包含的東西,而在這一點被說清楚之前「多久寫一則」這個問題沒有答案。** 量 2026-09-09:`grep '^## '` 全檔只有三個標題(`Unreleased` 1313、`v0.2` 1693、`v0.0` 3492),1–1312 行沒有任何 `##`。兩個已提交的檔案說這個檔的角色是**版本內容**不是逐段紀錄(`README.md`「says what each tag contains」、`docs/GATE-RESULTS.md` §「what a released version contains — `CHANGELOG.md` owns that」),而 `LOG.md` 是逐段的擁有者。觀察到的也不是節奏:近三十段 12 段有條目,缺口不落在步驟邊界(41/42/43 全缺,44–47 全有)。**兩種可能的設計沒有一個被寫下來** —— 頭部是「尚未歸檔」而 `## Unreleased` 是「已歸檔未發布」的兩層結構,或者那個標題只是過時該併掉。⚠️ **這一段刻意不寫條目**,因為往一個關係未定義的區域再加第十四則會讓缺陷更大 🔄 **2026-09-13(第六十一段):那個「多久寫一則」現在有一個數字,而它不是缺陷。** 量:逐段條目最新的是**第五十六段**(2026-09-10)。🔄 **2026-09-13(第六十二段):這裡原本還寫著「而 `LOG.md` 在第六十一段,所以第 57–61 段沒有逐段條目」—— 而那是一個**每一段都會過期的數字**，`XNUM-1` 的形狀寫在一個以數字過期為題的列旁邊。改成只留不漂移的那一半:**最新的逐段條目是第五十六段**，差幾段由讀的人自己對 `LOG.md` 算。第六十二段同樣刻意沒寫，理由不變。**🔴 **而第六十一段第一版的寫法是錯的、並且推上去了**:它寫「包含發 `v0.3` 的第五十九段」,而量 `grep '^## '` 有**四**個標題,`## v0.3 — 2026-09-11` 就在 1416 行 —— **發行版在裡面**,不在裡面的是逐段條目。那一段還開了一個 `CHLOG-2`,而這一列早就擁有這個問題 —— **替同一個未決問題開第二個擁有者**,正是這個 repo 一再點名的缺陷;`CHLOG-2` 已撤回,測量折進這一列。⚠️ 而這一列的判斷沒有變:在 `## Unreleased` 的結構被說清楚之前,「多久寫一則」仍然沒有答案,所以「落後五段」是那個未決問題的讀數而不是一個要補的洞。 | `R5-11` 🔄 **2026-09-16（第八十段）：改派 `P4b`，第一次移交。** `CHANGELOG.md` 的 `## Unreleased` 該不該包含逐段條目，是一個**發行流程**的問題，而 `P4b` 的定義就是*完整的 GPL 發行 ＋ 發行流程*。這一列的判斷不變：在結構被說清楚之前，「多久寫一則」沒有答案 |
| `FLW-1` 🆕 | 🔴 **沒有任何東西查得出一份已提交的檔案裡有沒有禁區視窗的「摘要」，而今天正是靠人眼發現的。** 三支掃描器問的是三個不同的問題，沒有一支問這個：`flashwin scan` 找**禁區的位元組**（量 2026-09-07：`--sweep . --exclude upstream` 2,497 個檔、113 個探針、**CLEAN**，而 `LOG.md` 與 `tools/leakscan.py` 兩個帶著完整 64 hex 的檔都在被掃的集合裡 —— **這是 `scan` 正確地回答它自己的問題**，摘要裡一個 dump 的位元組都沒有）；`leakscan` 找**位址會長成的文字形狀**；`audit-bench-log` 找主題關鍵字。⚠️ **而縮寫不是緩解**：`FLS-14` 印的 60 bits 對 2^24 候選集誤判率 2^-36。🔴 **這支儀器今天故意不做**：它第一次跑就會點名 `LOG.md:87`，而那件事的裁決就是今天下的 —— **在同一個小時裡寫一支會替今天的決定背書的檢查器，等於沒有獨立的控制**。🟢 **正控制先寫死**：它**必須**報出 `LOG.md:87` 與 `tools/leakscan.py:137`，並且**不得**報出 `FLS-24` 的補集摘要（那份的前像不含 `H601`）；候選摘要集怎麼列舉是設計問題（每個 `(offset,length)` 是一個大空間），起點是「這個 repo 用過的視窗」加上整片、加上每個對齊區段 | `R9`（或更早，由擁有者決定插隊） |
| `README-1` 🆕 | 🔴 **`README.md` 有三份清單，三份都不完整，而「這是策展還是漏掉」沒有任何地方寫。** 量 2026-09-07（**母體的定義寫在這裡，因為換一個定義就換一個數字**）：`tools/` 頂層的 `.py`／`.sh`，非 `test-*` 的 ~~**36 個裡 27 個在 README、9 個不在**~~ 🔴 **重新導出 2026-09-11(第五十七段):43 個裡 27 個在 README、**16** 個不在。** 用的是本列自己寫下的母體定義,一個字都沒改。**「27」沒有動,而母體從 36 長到 43** —— 七支新工具進來而沒有一支進 README,**其中只有一支(`derivcheck.py`)是今晚加的**。所以這一列的缺口不是「有一支漏掉」,是**這條路徑上沒有任何東西在維護**,而本列自己引的數字從 2026-09-07 起就沒有被重新導出過 —— **一列引了數字而母體會動,那個數字就是一個會過期的宣稱**。不在的十六支:`binsim` `capdate` `capfield` `citime` `derivcheck` `desk-sweep` `dtcheck` `flashmap` `isa-probe` `rbcheck` `rebuild-census` `regcensus` `repdiff` `tc-smoke` `vendor-tripwire` `verify-backup-copy`（`binsim.py`、`citime.py`、`isa-probe.sh`、`rbcheck.py`、`rebuild-census.py`、`repdiff.py`、`tc-smoke.sh`、`vendor-tripwire.sh`、`verify-backup-copy.sh`）；`test-*` 的 **30 個裡 10 個在、20 個不在**；`notes/*.md` **16 個裡 10 個在、6 個不在**。⚠️ **交辦說的是「十個」而我量到 9，差別完全在母體**：把 `tools/rlxprobe/` 底下的組語與 C 原始檔也算成工具會得到 **25**。**兩個都不是錯的，是兩個不同的問題**，所以這一列寫的是定義不是一個數字。🔴 **而這一段刻意一個都沒補**：`notes/flash-digest-scope.md` 是今天新增的，把它加進一份 10/16 的清單，只會把一份策展清單變成一份看起來完整的清單 —— 那正是這一列存在的理由。**先由擁有者說出意圖，再決定補或不補** | `R5-11`（gate 的寫上去） 🔄 **2026-09-16（第八十段）：改派 `P4b`，第一次移交。** 這一列問的是 `README.md` 的三份清單是**策展還是不完整**，而那是發行文件的問題。⚠️ **它裡面有一半今天被付了而且是別人付的**：`CI-4` 量出 README 七個活的控制數裡四個過期，四個都改了 |
| `TCHK-1` 🆕 | ⚠️ **`tools/tcheck.py` recomputes the fields version 2.0 printed, and 3.0 prints twenty-two more that nothing recomputes.** 量 2026-09-06: the new `/proc` keys are `mode`, `ce_reload`, `ce_reload_hz`, `ce_reload_writes`, `ce_rating`, `ce_rating_probe`, `ce_rating_vendor`, `ce_registered`, `ce_probe_registered`, `ce_live`, `ce_mode`, `ce_mode_calls`, `ce_probe_mode`, `ce_probe_mode_calls`, `ce_next_calls`, `ce_badmode`, `ce_hw_bad`, `ce_cycles`, `ce_check_dc`, `ce_check_dj`, `ce_handler`, `ce_handler_is_noop`, `irq_preacked`. 🔴 **Two of them are recomputable and that is what makes this a gap rather than a wish**: `ce_check_dc / ce_check_dj` is a ratio the tool could check against 1 within the driver's own tolerance, and `Δce_cycles / hz_used` against `Δwall` is the whole of `cereload`'s causal test — a number this repository's discipline says a tool must re-derive rather than a reader transcribe. ⚠️ **It is not done now on purpose**: `tcheck` reads captures and there are none, so every case would be written against a fixture rather than against the artefact it exists to read | **the seating that produces block 10's captures** —— `tools/tcheck.py`、`bench/2026-09-06/PREDICTIONS-B11-block10.md` §5.5 |
| `LEDGER-1` 🆕 | ⚠️ **`ledgerscan` 只讀工作樹的 `HEAD`,而歷史掃描是手工跑的一次性量測。** 量 2026-09-02:167 個 commit、`git log --all -p` 的 **24,797,072** 位元組(只看新增行、排除 `upstream/`、排除這支工具自己的夾具):歷史裡 **92** 條路徑、`HEAD` 有 **95** 條,而**只有 2 條在歷史裡不在 `HEAD`** —— `arch/rlx/include/asm/processor.h` 與 `lib/decompress_inflate.c`,**兩條都是 out-of-scope**。🟢 **所以只掃 `HEAD` 在範圍內一條都沒漏**,而那實質收緊了帳本 §0 ① 的下界。🔴 **但一個不能重跑的量測價值有限**:它現在是一段 scratchpad 腳本,不是 `ledgerscan history`。要做成動作需要三件事:① 一個合成控制(一個 commit 加入路徑、下一個 commit 刪掉,`history` 必須找到它,而 `scan` 必須找不到);② 它太慢,不能進每次 CI 的 `--self-test`(24.8 MB 的 diff),所以要獨立動作 + 自己的 skip 列;③ 決定它紅的條件 —— 「歷史有而 HEAD 沒有且 in-scope」應該是紅還是只是報告,而那取決於帳本要不要涵蓋它們;🔴 ④ **而且它需要一個基準 commit 參數,理由是這個量測自我推翻**:把那兩條路徑寫進帳本就把它們放進了 `HEAD`,量到同一個掃描立刻變成 **0**。重新導出必須 checkout 2026-09-02 之前的 commit,所以 `history` 不能只有「現在」這一個模式 | `R9` 🔄 **2026-09-16（第八十段）**，接手自 **`R5` 的準備**：the measurement it wants is a differential over a baseline commit, which is `R9`'s own axis |
| `CI-4` 🆕 | 🔴 **`README.md` 的工具清單有 7 個控制數,而沒有任何東西比對它們;量 2026-09-02,兩個是過期的。** 把 README 每個 `tools/<name>` 段落裡的 `N controls` 對 `tools/ci-expected.tsv`(擁有者,因為 `ci-census` 從執行結果重新導出它),三個數再從這一輪 sweep 的 `.out` 檔逐一重新導出:`rlxfw-marks` 32 ✓、`looprun` 45 ✓、`flrbracket` 50 ✓、`cardcheck` 27 ✓;**`ledgerscan` 57 對 71**(今天自己寫的 —— 寫完之後又加了 14 個控制)、**`replay-capture` 17 對 23**(既有的)。🟢 **既有的那一個才是重點**:這不是一次失誤,是一個沒有檢查器的介面。🔴 **而第一版的掃描報了三個,第三個是假陽性,那正是這個檢查器最難的部分**:`test-cardcheck-mutants` 那一段寫的是「Two survived **the 23 controls that existed when they were written**」——那是 `cardcheck` 當時的控制數,一個**歷史陳述**,不會過期;那一段自己的數是同一行的 `18 mutants`,而它是對的。**所以 `\b(\d+) controls\b` 不夠**,檢查器必須分辨「這支有 N 個控制」與「當時有 N 個控制」,而那不是正則做得到的 —— 設計傾向:**只認段落第一行、緊接在 `tools/<name>` 之後的那一個數**,其餘視為散文並明列為未涵蓋。設計其餘:`ci-census.py` 的一個**獨立動作**(不進 `census()` 主流程,那有 19+ 個控制不該一起動);三個控制 —— 正控制(合成一份不符的 README 必須紅)、負控制(相符的必須綠)、liveness(抓到的數量 > 0,因為一個什麼都抓不到的正則會永遠綠)。⚠️ 跟 `CI-3` 是同一個主題的兩個動作,應該一起做。 🔄 **2026-09-07（第三十九段）：這一列的計數今天動了一個，而同一次量測順帶問出一件這一列沒有問過的事。** 動的是 `tools/spec-check.py` 那一段的「TWELVE checks and forty case lines」→ **THIRTEEN ／ fifty**（`C12`），由 `ci-census` 的規則量出來而不是數的。⚠️ **而順帶量到的是：README 的工具清單不是一份普查。** 量，非 `test-*` 的工具裡有 **十個**不在清單上 —— `binsim.py`、`citime.py`、`rbcheck.py`、`rebuild-census.py`、`repdiff.py`、`isa-probe.sh`、`rlxfw-kbuild.sh`、`tc-smoke.sh`、`vendor-tripwire.sh`、`verify-backup-copy.sh`。🔴 **這一段本來要「補上 `citime`」，量完之後沒有補** —— 因為十個一起缺代表那份清單是**挑選過的**而不是漏掉的，而在不知道它想不想完整之前補一個進去，是把一份策展清單改成一份看起來完整的清單。**未定的是意圖**：沒有任何地方寫著那份清單該不該涵蓋全部，而讀者分不出「策展」與「不完整」。**決定它的實驗**：問擁有者一句話，然後把答案寫進 `README.md` 那一節的開頭；如果答案是「該完整」，那它就跟這一列的計數一樣需要一個檢查器 | **`R5` 的準備** 🔄 **2026-09-16（第八十段）：第一半付了，第二半改派 `P4b`（第一次移交）。** 量 2026-09-16，把 README 每一個 `N controls` 對 `tools/ci-expected.tsv`：**八個站點裡七個是活的計數，四個過期** —— `rlxfw-marks` 32→**58**、`ledgerscan` 71→**84**、`looprun` 55→**66**、`cardcheck` 31→**35**，四個都改了；`tcheck` 14、`flrbracket` 50、`replay-capture` 23 本來就對。🔴 **第八個站點是我自己量測的假陽性**：`README.md:772` 的「23 controls」是一句有日期的歷史陳述（*Two survived the 23 controls that existed when they were written*），不是現在的計數 —— 抽取器抓到它，而**驗歸屬**才排掉它。② 剩下的那一半——*那份清單該不該完整*——是擁有者的一句話，與 `README-1` 同一個問題，所以兩列同時改派 `P4b` |
| `P4A-1` 🆕 | 🔴 **`P4a` closed at Level 1 and Level 2 is one open item, not the open-ended list it looked like.** 讀 2026-09-01: this drop's `scripts/mkcompile_h` has no `KBUILD_BUILD_USER`/`_HOST` and writes `(key@K)` from `whoami`/`hostname` (:65-66), so a third party rebuilding the published recipe gets a different banner and a different sha256 whatever is done about the clock. **Five of the seven candidates were settled rather than carried**: `LINUX_COMPILER` is `"gcc version 3.4.6-1.3.6"` and nothing else (讀); the image holds **0** hits for `/home/key`, `r3-4` or `cells/` (量); the initramfs source mtimes were closed by `host-compat/0002` hunk 2; `LINUX_COMPILE_TIME` reaches no object. 🟢 **2026-09-01 (`R4-0`): `.version` under `--keep` is MEASURED — 2 bytes of 3,968,240, both the `#1`/`#3` digit in `linux_banner` and `init_uts_ns` (`SPEC.md` `TC-42`), so ONE stays unmeasured: kbuild's link order against `readdir`.** *(This read "Two stay unmeasured".)* `notes/reproducible-build.md` §6 | **`P4b`** at v1.0, which is where *corresponding source* lives — and it is the gate whose reader needs Level 2 |
| `NAME-1` 🆕 | ⚠️ **Two directories/files now have names narrower than their contents, and both were left that way DELIBERATELY on 2026-09-01.** `config/host-compat/` holds `0002`, which is about build determinism and not about host compatibility; `tools/test-kbuild-cflags.sh` now also tests the build-stamp guard. 🔴 **The reason for not renaming either is specific, not laziness**: `host-compat` has nine references across six files, and renaming the suite would move BOTH its row in `ci-expected.tsv` and its allowed-skip label in `ci.yml` — an allowed-skip label edited in one place and not the other is exactly what put three commits red on 2026-08-31 (run 33410057391), and this machine is structurally unable to see that class. **A rename belongs in a commit that does nothing else** | ~~**none yet.**~~ Renaming is not a gate's work; it is a session's, and it needs a session that is not also changing what the things do 🔄 **2026-09-16 (第八十段): this becomes a STANDING INSTRUCTION, which is an owner and not a deferral.** *Any desk segment that is not also changing what these things do* — which is this row’s own stated condition, quoted rather than invented. 🔴 **This segment does not qualify and that is measured, not modest**: it renamed `CFG-2`→`CFG-3` and moved `RECIPE_ID`, so a directory rename on top of it would put two unrelated changes in one `RECIPE_ID` move. The table’s rule that a row with no owning gate is a bug is satisfied: a standing instruction is an owner, and `CENS-1` and `REGIMM-1` carry the same shape; **any desk segment that is not also changing what these things do** |
| `CI-2` 🆕 | 🔴 **`spec-check`'s table sweep walks `git ls-files`, so a file that is not yet staged is outside the population it reports on — and the natural order (write, run the gate, commit) guarantees every NEW file is outside it.** 量 2026-09-01: `09e1a23` was pushed with two `C8` defects in `docs/KNOWN-ISSUES.md` after a local gate run that was genuinely green, because the file was untracked when it ran. CI's `text` job caught it (run 33434417629). ⚠️ **This is NOT the class `CI-1` describes**: `CI-1` is a check this machine cannot make, and this is a check it can make and was asked at the wrong moment. The fixes are different. 🟢 **The repair is one line and it is a habit, not a checker**: `git add -A && spec-check && git commit`. Nothing verifies that ordering, which is the same shape as the note above about numbers | ~~**none.**~~ A checker for *were the gates run after staging* would have to run in the commit hook, and this repository has deliberately kept its gates as commands a reader can run rather than as hooks a clone inherits 🔄 **2026-09-16 (第八十段): a STANDING INSTRUCTION, and the row’s own question is answered in the other direction.** It said a checker for *were the gates run after staging* would need a commit hook. 量 2026-09-16: the PROCEDURE landed instead — `CLAUDE.md` now carries *`git add -N` every NEW `.md` file before running that gate*, added the same day by the seventy-eighth segment after CI caught two `C8` defects in a file five local runs had reported clean. 🟢 **And an INSTRUMENT is possible without a hook, which this row assumed it was not**: `spec-check` can report untracked, non-ignored `.md` files as OUTSIDE its population, which is a scope statement rather than a hook. Its strictness fixture is written here so the next segment does not have to derive it: *a tree with an untracked `.md` carrying a `C8` defect — the old version reports clean, the new one reports the file is unswept.* **Owner**; **any desk segment that edits `spec-check`’s population** |
| `IMG-1` 🆕 | 🔴 **The `v0.2` release ships no image, and the three reasons are not the same weight.** ① the GPL corresponding-source obligation, which `P4b` owns at v1.0 and which is not started; ② 量, **four of five `file` entries in `config/rlxfw-initramfs.tsv` are `owner=unit`** — the vendor's busybox, uClibc and libgcc out of this device's dump, so the image is not all mine to publish; ③ `P4a` closes at Level 1, so a published binary could not be checked against the published source anyway. 🟢 **③ is the one that dissolves rather than waits**: `P4A-1`'s Level 2 makes a published binary worth publishing, and until then it is a file people would have to take on trust — which is the thing this repository is built not to ask for. ⚠️ ② does not dissolve: a firmware image with the vendor's userspace in it is somebody else's property whatever `P4a` reaches. `R7` (my userspace) is the gate that changes ②, not `P4a` | **`P4b`** at v1.0 for ①, **`R7`** for ②, **`P4A-1`** for ③ — and the three are independent, which is why the row lists them separately rather than as one blocker |
| `CNT-1` 🔄 | 🔴 **Four numbers this repository states about itself were found wrong in one morning, and no instrument here can see the class.** 量 2026-09-01, all four caught by re-deriving a figure against the artefact it counts: `P4b-3` said `docs/KNOWN-ISSUES.md` had **25** entries when it had 28 (true at `09e1a23`, broken by three later commits the same session); `docs/KNOWN-ISSUES.md` said **17 of 59** CI runs were red when its own population was 18 of 59; `notes/reproducible-build.md` §6 said **five of seven** Level-2 rows were settled when three were, **and its own decomposition left one row in no category at all**; `docs/KNOWN-ISSUES.md` copied that fifth number and then listed four things under it. **The shape is constant and it is why nobody re-checks**: the number carries no weight in the sentence around it. ⚠️ **The next step is a measurement, not a tool** — the population of such numbers in committed files is unknown, and building a checker before counting the population is building an instrument with no evidence it has anything to find, which this project's own rule forbids  🔴 **2026-09-07（第四十一段）：這個類別又一個實例，而它比前四個都難看見 —— 因為那個數字是**儀器算出來的**，不是手打的。** 量：`ci.yml` 里真正的 `run:` 步驟是 **61** 個；`grep -cE '^\s*run:'` 只看到 **59**；`grep -c 'run:'` 讀到 **62**。差別是：① `:358` 是一行**以 `run:` 結尾的註解**；② **`:728` 與 `:733` 用的是行內 `- run:` 形式**，而任何以 `^\s*run:` 定錨的選擇器都看不到它們。 🔴 **而那兩步從 `970f041`（2026-08-25，`apt` 進 `ci.yml` 的同一個 commit）就在了**（`git log -S`），所以**這個專案每一次桌面全套 sweep 都静静地跳過了它們**，而每一句「all N 個 `run:` 步驟」都差了兩個。`shellcheck --severity=error tools/*.sh` **從來沒在這張桌子上跑過**，只在 CI 上跑過。 🟢 **形狀與 `CLAUDE.md` 已經記了兩次的那個同類**（一個選 `run:` **行**的 sweep 看不見 `run:` **區塊**，`verify-backup-copy` 因此掉了兩次），這是第三個變體：**定錨在行首的選擇器看不見行內清單形式**。 ⚠️ **所以 `CNT-1` 要改的不是數字而是它自己的下一步**：這一列寫著「下一步是量測不是工具」，而今天這個實例說的是**就算有工具，工具自己的選擇器也是一個沒人檢查的數字**。治它的不是第二個計數器，是讓儀器**把它數到的總數印出來並且跟一個宣告值比對** —— 這一段的 sweep 現在就這樣做，數不到 61 就印 `WARNING`。  🔴 **同一天第二個實例，而它是這個類別至今最銳利的一個 —— 因為那個「第二個地方」是一張凍結的卡片，而那個數字是**板子自己會印出來檢查的**。** `RECIPE_ID` 是對 **`config/` 底下每一個檔**的 sha256，**連註解都算**。映像建好、staged、數字寫進卡片之後，我在 `config/rlxfw-src/…/rtl819x-spi.c` 改了**一行註解**，recipe 就從 `e0028cc8` 變成 `3b589390`。**沒有任何東西警告** —— `rlxfw-kbuild.sh` 自己的註解知道`config/` 的編輯會移動 `RECIPE_ID`，但它把那件事寫成**重建成本**；沒人寫下來它也會讓一張凍結卡片的身分斷言失效。🟢 **抓到它的是收工稽核重新導一次 recipe，而不是重讀卡片**；修法是**重建**（`r55a` → `r55b`，`RECIPE_ID` `fce0af22`）而不是改卡片上的數。⚠️ **而這一列的「下一步是量測不是工具」現在有了一個很具體的候選**：卡片凍結前重新導一次 `RECIPE_ID` 並跟卡片上的值比對 —— 今天只把它寫進卡片的凍結順序，而**寫在散文裡的規則不是規則**，所以檢查器是 carried-forward。 | ~~**none, and the row says so.**~~ `spec-check` does this one file wide, for `SPEC.md`'s rows against their owner files; whether the idea generalises to prose is the owner's call  🟢 **2026-09-01, later the same day: the class now has a measured backing instead of an intuition, and it came from the CI history.** 量, all eighteen red CI runs read from their own logs: **sixteen of the eighteen** are the same shape — a count or a label about the repository's own contents, kept in a second place, invalidated by a change somewhere else. Seven are `tools/ci-expected.tsv`'s per-suite counts against the suites, four are one hardcoded *N cold, M warm* inside `test-boot-timeline`'s `B2` against the captures under `bench/`, five are that table's allowed-skip labels against what a tool actually prints. 🔴 **So the question is no longer whether the class is real. It is why the machine-readable half has an instrument and the prose half has none** — `ci-census` makes this class fail loudly on a push; in prose the identical mistake sits there silently, which is how four of them reached committed files. ⚠️ **The population of prose counts is still unmeasured** and that is still the next step; what changed is that the class is now this repository's single largest recorded source of CI failure.  🔄 **2026-09-07（第三十九段）：一個第五個實例，而它在 `CLAUDE.md` 裡，被四條獨立的規則量出來，而且這個 repo 自己早就寫下了會抓到它的那條規則。** `CLAUDE.md` 的環境段寫「a full sweep of all **60** `run:` steps（🔄 **61** from the thirty-seventh segment，when `citime self-test` was added）」。量 2026-09-07，`.github/workflows/` 只有一個檔案，而它有 **59** 個 `run:` step —— 四條互相獨立的算法一致：`grep -cE '^[[:space:]]+run:'` **59**、`grep -cE '^ +run:'` **59**、`- name:` 的步驟數 **59**、以及 **GitHub 自己的逐 job step 清單**（`instruments` 16、`lint` 6、`text` 51、`census` 7，各扣掉 5 個框架 step ＝ 11＋2＋44＋2）**59**。🔴 **而它在 `f82c704` 當下就是 59** —— 也就是 `CLAUDE.md` 說「把它從 60 變成 61」的那一個 commit —— 所以這不是後來掉了兩步。⚠️ **差在哪裡未定**：產生 61 的那支 sweep 腳本不在這個 repo 裡（`CLAUDE.md` 記的是它的行為不是它的原始碼），所以無法判定它多算了什麼。**決定它的實驗**：下次跑 sweep 讓它逐一印出它實際叫起來的指令，然後與 `ci.yml` 對名字。🟢 **而這一列最有價值的地方是：`CLAUDE.md` 同一段裡已經寫著會抓到它的那句話** ——「**never read a sweep's own count as coverage**」，而 61 正是一支 sweep 自己報的數。**規則寫下來了，套用到自己身上的那一次沒有做。** `CLAUDE.md` 沒有被這一段改動：它自己的規則是「where this contradicts the repo, the repo wins and this file is wrong」，而改那個檔案是擁有者的事。 🟢 **2026-09-07（第四十二段）：這一列自己指定的實驗跑了，而它把「差在哪裡未定」關掉了。** 這一列寫著「下次跑 sweep 讓它逐一印出它實際叫起來的指令，然後與 `ci.yml` 對名字」。`tools/desk-sweep.py enumerate` 就是那件事，而且那支腳本**現在在這個 repo 裡**（上一版的 ⚠️ 說它不在，所以判不了它多算了什麼）。量：用 PyYAML 讀，`run:` 步驟是 **61** 個 —— **59 個行首形式 ＋ 2 個行內 `- run:`** —— 所以 **61 是對的、59 是選擇器的盲點**，而 `grep -c 'run:'` 的 62 多算的是 `:358` 那行以 `run:` 結尾的註解。那兩步是 `lint` 的：`#1` 是 `sudo apt-get install shellcheck`（在桌面被拒），`#2` 是 `shellcheck --severity=error tools/*.sh`，**量：rc 0，綠，這張桌子上的第一次**。🟢 **而「never read a sweep's own count as coverage」現在有執行器**：`C9` 要求活的 `ci.yml` 解得開且步驟數 ≥ 40，`C10` 要求每一個宣告的名字仍然存在、且安全規則仍然至少命中一步，`C10b` 要求它命中的數目非零。 🔴 **同一天這個類別又來一個實例，而它是被 CI 抓到的不是被重讀抓到的**：`tools/ci-expected.tsv` 說 `test-config-gates` 的 `bench_total` 是 **58**，而 `aca873d`（第四十一段）給那支 suite 加了兩個 case 沒有動這個數字。**兩層盲點疊起來才讓它活下來**：`census` 是桌面跑不了的兩支之一（它要 GitHub 的 artifact 目錄），而在 CI 上它 `needs: [text, instruments]` —— `text` 因為 `C8` 紅掉，所以 `census` 被 **skipped**，紅的那一句從來沒有印出來。**第一次 `text` 綠，`census` 就紅了**，而那是它第一次真的跑。 🔄 **2026-09-16 (第八十段): the row’s OWN next step is paid, and the rest is a standing instruction.** This cell said *the population of prose counts is still unmeasured and that is still the next step*. 量 2026-09-16, with the rule stated first because a different rule gives a different number: over **146** tracked `.md`, a **bold** number immediately followed by one of ten repository nouns gives **33** sites — `files` 15, `controls` 8, `entries` 3, `rows` 2, and one each of `suites`, `steps`, `mutants`, `cases`, `captures`. 🟢 **33 is small enough for a checker**, which is the thing the row wanted to know. ⚠️ The rule is narrow on purpose and its blindness is stated: an unbolded count and any other noun are outside it — but bolding is what does the identifier-exclusion work that `XNUM-1` measured as the first job. **Owner**; **any desk segment that adds a count about this repository to prose** |
| `REEL-1` 🆕 | 🔴 **`R16` asserts on the model and a stopwatch measures the artefact, so the reel has been ~2.5 s over its ceiling with a green gate.** 量 2026-09-01, three end-to-end runs: **62.246 / 62.235 / 62.310 s** against a computed 59.749 s and `plan/ARTIFACTS.md` §2's 60 s. Decomposed: ~0.065-0.14 s fixed per segment plus **1.461 s in `K-J` alone**, whose 2,339 timing records each pay ~0.62 ms of `sleep` granularity — so the gap grows with RECORDS, not with duration. **The sentence was corrected and the reel was not**, because `config/r3-11-reel.tsv`'s own rule forbids fitting the pause column to the ceiling. ⚠️ What is open is whether `R16` should measure wall time (which would make it host-dependent and therefore a bad CI case) or whether the ceiling should move | `P4b` 🔄 **2026-09-16（第八十段）**，接手自 **`P4b-gate`** ④ — it is the take's spec, and the take is what that item owns：it is the release take's spec, and `P4b` is the gate that publishes at v1.0 |
| `PRED-1` 🆕 | 🔴 **`check-predictions` reports three different causes with one sentence, and the third one is not "a seating that stopped".** 量 2026-09-01, the diagnostic line owed since the eighteenth segment: of the **34** cells with no capture, **9** are a seating that never happened (`bench/2026-08-26` holds a prediction block and not one capture), **11** are seatings that stopped part-way, and **14** were VOIDED at the bench and re-run under a new prefix — `X-flr0` became `X2-flr0`, `K-rb` became `K2-rb`. Ten of those fourteen have a replacement block (`block3d`) that is green; four (`K2-rb`, `K2-rbp` and their re-runs) have no prediction block at all, because the fourth power cycle of seating 8 was unplanned. **Nothing links a superseded cell to its replacement**, so the tool cannot separate the three and its one sentence is wrong for the third. ⚠️ The sweep itself is correct and green: 0 out of order over 47 files and 333 cells 🆕 **2026-09-01: the `superseded-by:` line this row proposes now exists, once.** `bench/2026-09-01/CORRECTIONS-block6.md` §1 carries it for `Y0-A` → `Y-A`, in the format named here. ⚠️ **It does not close the row**: the fourteen earlier superseded cells still have none, and **no tool reads the line** — `check-predictions` still cannot separate its three causes. 🔄 **2026-09-03 (twenty-ninth): there is a FOURTH cause and it was found by re-deriving this row's own total.** The sweep now reports **45** cells with no capture; `R5-2`'s card contributes 10, so the baseline is **35** against the 34 recorded here. The one that moved is `bench/2026-09-02/LP-3`, and its seating **completed** — `looprun`'s `S7` writes `LP-boot`, which block 7's own §4 says in advance. **So the fourth cause is: the capture exists, under a name a TOOL chose, while the card's hand-typed column names another.** It is the least alarming of the four and the most misleading, because nothing distinguishes it from a seating that stopped, and it will recur every time `looprun` drives a carded cell. ⚠️ **The count 34 was not wrong when it was written**; it is the class this row exists for arriving in the row itself | ~~**none yet.**~~ A `superseded-by:` line in a corrections file would do it, and it is a format change to blocks that are already frozen — which is the same shape as the `written:` line `check-predictions.py`'s own docstring carries forward 🔄 **2026-09-16 (第八十段): a STANDING INSTRUCTION — *any segment that writes a corrections file*.** That is this row’s own proposal (`a superseded-by: line in a corrections file would do it`) turned into an owner, and it is the right shape because the change is a FORMAT change to blocks that are frozen: it can only be made by the segment that writes the next one, never retroactively; **any segment that writes a corrections file** |
| TC-e ⊘ | ⊘ **放棄 2026-09-30（第一百一十八段，`R7` 關的那一個提交）—— 類別：「真的缺陷，但沒有任何活的 gate 會碰到它」。** 缺陷本身仍然成立：**`tc-smoke` 的 L1 分不出十個壊掉的 binutils 與一個。** `NEED` 列了十個程式而只有 `as` 有控制（`S2`）；`ar ranlib nm objdump size strip` 在工具裡沒有任何別的地方被呼叫，所以把 `NEED` 缩到只剩 `as` 也每一例都過。修法也還是那一個：一個 `deadobjdump` stub 旋鈕加三條斷言的例。🔴 **放棄的理由就寫在它自己原本的擁有者格裡** ——「只有引進新工具銀時才會咬人」，而 `R7` 沒有引進：它用 `R5` 選定的同一把 `rsdk-1.3.6-4181` 建了六支程式與一顆 busybox。而還開着的 gate 那一個都不引進：`R8b` 寫 flash、`R9` 是差分証明、`P3` 是報告、`P4b` 是 GPL 釋出。把它強按到其中任何一個上面，正好是 `R1y-6` 在修的那個缺陷 —— 一列被按在一道不會量它的閘上。🟢 **重新打開的條件，寫死**：第四把工具銀、或一組不同的 binutils、或任何一次改 `tc-smoke` 的 `NEED` 表進入建置的那一天。到那一天之前，這一列報 0 是因為沒有母體，不是因為它被修好了 | ⊘（原本 `R7`，接手自 ~~`R2a`~~） |
| C-1 | Answered, `docs/loader-command-semantics.md` §a: **it scans.** `0x80408084` probes `0x010000`, `0x020000`, `0x030000`, then sweeps `[0x030000, 0x060000]` at a `0x10000` stride skipping those three — six candidates, and this unit's kernel is at `0x060000`, the last one. The accepted candidate is left in the global `0x8040DD3C`. Corroborated by the vendor's `check_image_header()`. **R8's A/B layout needs no loader change: any 64 KiB boundary in that window is a slot, and the lowest good image wins.** **Residual**: two `DW`s at the bench refute or confirm it (§8 rows 1–2). | ~~R8~~ (A/B layout) 🔄 **2026-10-04 (第一百一十九段): re-owned when its gate closed on the half that writes nothing.** A slot layout is a layout of flash, which only the half that writes can test; **`R8b`** (A/B layout) |
| C-3 | Answered, `docs/loader-flash-write.md`: `burn()` is the image parser and dispatcher, bounds-checked only at the top against chip capacity, **no lower bound**, and `boot` is one of its eight accepted section signatures. SPI controller at `SFCR 0xb8001200` / `SFCR2 0xb8001204` / `SFCSR 0xb8001208` / `SFDR 0xb800120c`, two sources agreeing; `RDID` is `0x9F`. `ComSrlCmd_RDID()` at `0x804058bc` spins on `SFCSR` bit 27 and writes `0x9F000000` to `SFDR`, which confirms the bit layout from behaviour rather than documentation. **The JEDEC ID question is answered and it is readable**: neither caller of `ComSrlCmd_RDID()` stores the value, but the SPI probe passes it one level down to the descriptor installer at `0x8040533C`, which writes it to `0x8040FBD4 + 0` — so **`DW 8040FBD4 8` at the prompt reads it, with four precomputed fields in the same output as the control** (`RUNSHEET.md` B2). The same trace found that this unit takes the **unknown-chip fallback** — `chipName: UNKNOWN` — so `burn()`'s only bound, the capacity at descriptor `+12`, is the hard-coded `1 << 22` and is correct for this device **by coincidence**. **Residual**: which of `burn()`'s four callees erases and which programs. | ~~R5b~~, ~~R8~~ 🔄 **2026-09-16 (第八十段): the first owner is struck — 量, it was never a gate.** `LOG.md:29235` records it as a plan-layer gate that deliberately never entered the board, so a row naming it carried an owner that could not act; `R8` is open and was already this row’s second owner, which is why its kind read `LIVE` throughout. ⚠️ **`SPEC.md:734` (`REG-14`) names the same non-gate and no check here can see that** — `cfcensus` reads `PROGRESS.md` alone — so it is corrected in the same commit rather than left to become the next `NET-14` 🔄 **2026-10-04 (第一百一十九段): the second owner is struck too — its gate closed on the half that writes nothing.** Which callee erases and which programs is the first question of the write path, which is plan precondition ④ and moved with the flash half; **`R8b`** |
| C-4 | **Upgraded from inferred to read**, `docs/loader-command-semantics.md` §a: `doBooting()` is at `0x80408690` in **this unit's own code**, and `beqz a0` on a zero image-check result goes straight to `goToDownMode()` with no ESC wait and no message. The check itself is `check_image()` at `0x80407D50` — signature (`cs6c`→1, `cr6c`→2) plus a 16-bit sum over the RAM copy that must be zero. It looked un-locatable because this build **compiles out the `no sys signature` / `sys checksum error` strings while keeping the rootfs ones** — the check is silent, not missing. **Residual, still a bench item**: that a deliberately corrupted image reaches the prompt in practice. Kernel region only. | ~~R8 precondition ⑤~~ 🔄 **2026-10-04 (第一百一十九段): re-owned when its gate closed on the half that writes nothing.** The plan's preconditions moved with the flash half (`docs/GATE-RESULTS.md` entry 16 § `R8b`); **`R8b` precondition ⑤** |
| C-13 | `check_image()` returns "no image" outright when the global `0x8040DBA4` is 1 (the vendor calls it `gCHKKEY_HIT`). Its only writer at `0x804082B4` reads `0xB8002014` bit 24 and compares the top byte of `0xB8002000` — the UART path, so it looks like *a key was pressed*, but the register addresses are not confirmed against the datasheet and the argument is not traced. **A flag that makes the loader declare every image bad is a rescue path and possibly a hazard.** Fifteen minutes at the desk. 🆕 **A measured capture is consistent with it and with nothing else so far**: `upstream/dumps/uart-bootloader.log` reaches `<RealTek>` with **no `---Escape booting by user` line**, and that message sits on `doBooting()`'s non-zero branch (`0x804086D0`) while the silent branch is the `beqz a0` one — i.e. `check_image()` returned 0. Consistent with, not proof of: the ESC-wait at `0x80408320`'s return convention is still untraced, and flipping it would flip the reading. | ~~R8~~ 🔄 **2026-10-04 (第一百一十九段): re-owned when its gate closed on the half that writes nothing.** A flag that makes the loader call every image bad bears on a boot from flash and on the rescue path, which only the half that writes exercises; **`R8b`** |
| `REGIMM-1` 🆕 | 🔴 **`teqi` 家族在每一支儀器之外，而發現它的是一次不相干的安全問題。** 上一段把「21 個未向量 cause」的危害量成空清單，而那個結論的位址是母體 —— 75 條裡沒有任何一條 REGIMM trap。量：零命中。收它需要一列 payload 加一行 `hazlint` 的 `ISA_TRAPS`，而 `SPEC.md` `CPU-60` 是它的家。🔄 **2026-09-15(第七十一段):成本的更正終於傳回擁有者檔了。** 這一列在第六十九段就判定它**不是**「搭現有卡片零增量上機成本」——需要帶例外處理器的 payload,而每一顆這樣的 payload 都把列表編譯進去、被卡片 sha256 釘死 —— 但 `SPEC.md` `CPU-60` 與 `docs/isa-payload.md` §7 兩處**同日寫著相反的話而沒有被改**,直到今晚才就地更正。⚠️ 這是一次「同一天內部翻案沒有傳回擁有者檔」的案例,而抓到它的不是任何閘門,是一次列舉式的稽核 | ~~`R1-pub-4`~~，或任何一段動 `isa-payload.tsv` 的桌面段 🔄 **2026-09-16（第八十段）：那個具名 gate 劃掉，常設指示留下。** 它在 2026-09-16 走完它自己的步驟。⚠️ 而這一列自己第六十九段就判定它**不是**零增量上機成本，所以常設指示是它真正的擁有者而不是一個方便的說法 |
| `VDR-1` 🆕 | 🔴 **進入廠商 userspace 的每一條路都以一次 flash 寫入開場，而這件事之前沒有任何一個檔案說過。** 主控台沒 shell／沒 getty／沒 login（`/etc/inittab` 全注解）、loader 沒有 `init=`／`bootargs` 機制（13 針 0 命中）、`TELNET_ENABLED` = 0；唯一實證的入口 `formSysCmd` 觸發後會把 `SYSCMD_SELECT` 寫進 `0x00C000` 的 `COMPCS`（量 `P10-10`，在兩個禁區之外且 blast radius 有界，但它是寫入）。⚠️ 而還有兩個未量的環節：沒有 `chmod` applet （下載下來是 0644，`execve` 給 `EACCES`），以及 payload 的 stdout 到底落在 UART 還是要轉到 `/var/web` 再用 HTTP 拿。**最便宜的決定性實驗不花 flash 也不花電源**：在 `qemu-mips-static -L squashfs-root` 下演練整條鏈 | `R9` 🔄 **2026-09-16（第八十段）**，接手自 `R1-pub-4`（`docs/isa-prior-art.md` § 9.5）；而寫 flash 這一步永遠是擁有者的明確 yes：its subject is the vendor firmware's own behaviour, which is `R9`'s third column |

---

## The debt census — generated by `tools/cfcensus.py`

🔴 **Generated. Nothing between the `<!-- cfcensus: -->` markers is written by
hand** — `cfcensus write` regenerates them and a hand edit here is overwritten
without warning. Nothing checks that they are current (`FW-111`).

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
hand, four owner files that no checker could reach. `U6` is the control that
keeps that sentence testable: the live file must yield at least one open row
owned by a live gate, or the census refuses to report at all.

<!-- cfcensus:counts begin -->
| what | n | meaning |
|---|---:|---|
| LIVE | 14 | open, and a gate that is still open owns it |
| SEGMENT | 10 | open, deferred to *any segment that touches X* — unscheduled, not orphaned |
| ORPHAN | 0 | 🔴 open, and every gate it names is CLOSED — **nobody will do it** |
| ORPHAN? | 0 | open by its first cell, owner closed, and a ✅ sits in the owning-gate cell or opens the question — probably an `L8` row that is finished and never marked |
| DEAD | 0 | 🔴 names a gate that exists nowhere in this file |
| NONE | 0 | open and names no gate at all |
| CLOSED | 0 | first cell says ✅ |
| DECLINED | 1 | first cell says ⊘ |
| **total** | **25** | rows parsed, reconciled against 27 raw table lines minus 2 header lines |
| `L8` | 0 | closure recorded somewhere this table does not declare — the owning-gate cell, or the head of the question; 0 exempted by name |
<!-- cfcensus:counts end -->

### The rows with no live owner

Every open row whose owner is not a gate that is still open. `ORPHAN` is the
population `R1z` exists for; `ORPHAN?` was a row *probably* finished and never
marked, and the two were counted apart because folding them would have inflated
the debt by fourteen. 🟢 **`R1z-2` read all fourteen one at a time and every
one of them was.** The bucket is empty, and that is the label's own claim
measured rather than repeated.

<!-- cfcensus:debt begin -->
| # | kind | owner named |
|---|---|---|
| `UP-AUD-1` | SEGMENT | — |
| `CENS-1` | SEGMENT | — |
| `CORR-1` | SEGMENT | — |
| `BRD-2` | SEGMENT | — |
| `TCHK-1` | SEGMENT | — |
| `NAME-1` | SEGMENT | — |
| `CI-2` | SEGMENT | — |
| `CNT-1` | SEGMENT | — |
| `PRED-1` | SEGMENT | — |
| `REGIMM-1` | SEGMENT | — |
<!-- cfcensus:debt end -->

---

