# Known issues

**What this repository does not establish, at `v0.2`.**
`plan/CHARTER.md` §110 rule 2 asks for a known-issues list beside every release.
This is that list, and it is written to the same standard as everything else
here: each entry names what is *not* true, what was measured instead, and which
gate changes it. Nothing below is a plan; the plan is `PROGRESS.md`'s gate board.

Marked the same way as the rest of the repository: **量** measured on the device
· **讀** read out of code, a dump or a document · **推** inferred, pending a
measurement.

---

## The firmware does not exist

| | |
|---|---|
| 🔴 **There is no driver of mine.** | `R3`'s D5 — a `ping` with four replies, confirmed on the host's own capture in both directions — went out through the **vendor's** `rtl819x` driver, in the vendor's own configuration. A kernel of mine boots and reaches userspace; every peripheral it touches is Realtek's code. **`R6` is the gate that changes this sentence, and `R3` must not be read as having changed it.** |
| 🔴 **No userspace of mine.** | The initramfs is built from **this unit's own extracted rootfs** — busybox, uClibc, and the symlinks around them are the vendor's binaries, declared one row at a time in `config/rlxfw-initramfs.tsv` with an owner per row. That is deliberate (`R3`'s Decision B: if the shell does not come up, the shell is not the new thing) and it means nothing in userspace is mine. `R7`. |
| ⚠️ **Nothing has been written to flash, and that is a weaker sentence than it sounds.** | See the next section. |

---

## The flash claim, and why it is not "zero bytes written"

| | |
|---|---|
| 🔴 **"No flash-write command was issued" is not "not one flash byte is written".** | `RUNSHEET` `G8b` forbids the second without a full re-dump hashed against `FLS-14`, and no seating has run one. What exists is a bracket: four 256-byte windows read back before and after, over two power cycles. |
| 量 **The bracket reaches 1,024 of 4,194,304 bytes — 0.0244 %.** | All byte-identical to the 2026-08-16 reference dump. It **cannot** see a write outside those four windows, and it cannot see two writes that cancel. |
| 量 **`H601` — this unit's MAC and radio calibration, the region a wrong write cannot be undone in — is covered to 512 of 8,192 bytes: 6.3 %.** | The other 93.7 % is unchecked. This region is why the project is zero-write through `R9`. |
| 🟢 **The bracket does have a negative control.** | Every destination is read **before** its `FLR`; on the round that established this, all eight pre-reads differed from the expectation, so *the `FLR` wrote* is measured rather than assumed. One earlier round was **voided** by that control when DRAM retained a previous cycle's contents across a power cycle. |

---

## The reproducible build closes at one machine

| | |
|---|---|
| 🔴 **`P4a` is closed at Level 1: same machine, same tree, built twice. A third party rebuilding the published recipe will NOT get the same sha256.** | 讀 2026-09-01: this drop's `scripts/mkcompile_h` has no `KBUILD_BUILD_USER` and no `KBUILD_BUILD_HOST` (those arrived in mainline after 2.6.30). It writes `LINUX_COMPILE_BY` from `` `whoami` `` and `LINUX_COMPILE_HOST` from `` `hostname` ``, so the banner carries this workstation's identity and the image carries the banner. |
| ⚠️ **Five other candidates for the same problem were measured or read away, and are listed so the residual is one item rather than a worry.** | `LINUX_COMPILER` is `"gcc version 3.4.6-1.3.6"` and carries no build path (讀); the image holds **0** hits for `/home/key`, `r3-4` or `cells/` (量); the initramfs entries' mtimes are declared, all 31 of them; `LINUX_COMPILE_TIME` reaches no object in the tree. Two stay unmeasured: `.version` under `--keep`, and kbuild's link order against `readdir`. `notes/reproducible-build.md` §6. |
| 🔴 **`P4a`'s own definition of done is wrong as written, and the gate closed with it recorded rather than repaired.** | The gate board says *"with the positive control that changing one source byte changes it"*. 量: one byte of a string literal changes the sha256; one byte inside a **comment** in the same file leaves it byte-identical. The wording needs *that reaches the image*. The second outcome was predicted before it was run, because a control that can only come out one way is not a control. |
| ⚠️ **Every sha256 recorded for a build belongs to a recipe id and has to be quoted with one.** | `RLXFW_SRC_ID` is a sha256 over `config/` **as bytes**, comments included, so a typo fix in a declaration produces a different image. That is the design — the image's identity tracks the declaration exactly — and the cost is that two images are not comparable across a documentation-only commit. |

---

## Gates that closed with a defect recorded

| | |
|---|---|
| 🔴 **`R3`'s D3 had no observable.** | The written criterion for *early bring-up completes* was the string `MemTotal:`, which **this kernel never prints in any configuration** — it is a `/proc/meminfo` field, not a boot message. The row passed on a substitute (the eleven boot marks, which are discriminators checked in the image before the seating). A DoD whose observable does not exist is a defect in the DoD and is recorded as one. |
| ⚠️ **`R3-2`'s `TC-d` half stayed half-done for one step.** | It is carried as a debt in the running-order note rather than counted as a pass. |
| ⚠️ **`R1h`'s decision ② is still `R1-gate`'s.** | It was answered on the D side by a bare-metal payload, and not by the gate that owned it. |

---

## The artefacts

| | |
|---|---|
| ⚠️ **The 60-second take is a REPLAY, not a live recording.** | It is seven committed serial captures replayed at true wire speed by `tools/replay-capture.py reel config/r3-11-reel.tsv`. `plan/ARTIFACTS.md` §2's v0.2 row describes a live power-up. The replay is reproducible by anyone who clones this repository, which a recording is not — but it is not a recording of the board, and the video says so. |
| ⚠️ **The take is PUBLIC where the project's own plan asked for unlisted.** | `plan/ARTIFACTS.md` §2 specifies an unlisted link. The owner ruled otherwise on 2026-09-01, so it is a departure from the plan rather than an oversight. 🟢 **The containment check is the same either way and it was run before the recording**: `flashwin scan` reports CLEAN on all seven segments against this unit's reference dump, and a MAC-shaped sweep returns 0 — so nothing in the frames identifies the device beyond what this repository already publishes. |
| 🔴 **It measures 62.2 s against a 60 s spec, and the gate that checks the length cannot see it.** | 量 2026-09-01, three runs: **62.246 / 62.235 / 62.310 s** (range 0.075 s) against a computed 59.749 s. `replay-capture`'s `R16` asserts on capture-plus-pause; a stopwatch measures the replay, and the difference is ~0.065–0.14 s of fixed cost per segment plus **1.461 s in one 33 s segment** whose 2,339 timing records each pay ~0.62 ms of `sleep` granularity. **The pause column was not trimmed to fit** — that is what `config/r3-11-reel.tsv`'s own rule forbids. Open: whether `R16` should measure wall time (which would make it host-dependent, and therefore a bad CI case) or whether the ceiling should move. |
| ⚠️ **`study/weekly-results.md` is not in the public repository.** | 量: `.gitignore:17` is `study/`, and `git ls-files study/` returns nothing. `CHARTER.md` §110 rule 3 asks for one entry per closed gate in that file, and four are owed (`R2a/b/d`, `R1h`, `R3`, `P4a`). **Owner's ruling 2026-09-01: leaving it ignored is acceptable for now.** `P4b-gate` ③ owns the decision. |

---

## The repository's own record

| | |
|---|---|
| 🔴 **17 of this repository's 59 CI runs are red, and until 2026-09-01 nobody had counted them.** | 量 2026-09-01, `gh run list --limit 200`: **59 runs — 41 success, 17 failure, 1 in flight.** The failures span 2026-08-28 to 2026-09-01. ⚠️ **Every previous statement in this repository about its own CI history was made from the last few rows of `gh run list` and was wrong**: the twentieth session wrote *three red commits, one cause*, and the twenty-first corrected it to *four* and then to *five*, each time from a window rather than from the history. 🔴 **Four of the seventeen are diagnosed in this repository** — three share an allowed-skip label edited in the table and not in the tool (`95895e1`, `5b66938`, `3a10e0c`), one is a blank line inside a markdown table row (`2266324`) — plus `2026e8e` (a case that skips on a runner and runs here) and `09e1a23` (two one-cell rows in a two-column table, pushed after a green local gate because `spec-check` sweeps *tracked* files and the file was untracked). **The other eleven have never been looked at**, and saying so is the point of this row. |
| 🔴 **Three CI failures now share one shape: a case that RUNS on the author's machine prints no skip line, so its label is never compared against the expected-skip table.** | The variable is different every time — `$FWRE_WORK` twice, the **timezone** once — so a rule about any one of them does not close the class. Two partial answers are in place: a case with no branch cannot print an undeclared skip, and a runner can be simulated locally with an empty `$FWRE_WORK`. Neither is complete. `PROGRESS.md` `CI-1`. |
| 🔴 **Version → contents has two owners and they disagree on six of six shared rows.** | `plan/CHARTER.md` §88 is authoritative and is **gitignored**, so a public reader cannot follow a pointer to it; `PROGRESS.md`'s Release clock restates it and is stale. This file and `CHANGELOG.md` now own the contents of the versions that have actually been released; the map of *future* versions still has the defect. `P4b-gate` ① owns it. |
| 🔴 **`v0.2` is this repository's first published release, and `v0.0` was tagged and never released.** | 量 2026-09-01: `gh release list` returned nothing before `v0.2` was created. `CHARTER.md` §110 rule 2 — *a release per version, with a CHANGELOG and known issues* — has therefore been unsatisfied since the project's first tag on 2026-08-25, which is wider than the carried-forward row that named the gap. Whether to publish a retrospective `v0.0` release is open. |
| ⚠️ **`v0.1` was never tagged.** | Its contents (`R0`, `rlxprobe` executing on the silicon, `R1-gate`) completed 2026-08-26. Owner's ruling 2026-09-01: not urgent. This release therefore spans `v0.0` → `v0.2`. |

---

## What has never been measured at all

* **Whether a DMA write is visible to a cached CPU read.** Nothing has been
  measured in that direction, and it is the one driver decision the cache gate
  closed without.
* **Whether this silicon retires the `cache` instruction.** This unit's own
  vendor kernel contains 37 of them, D side only; none has been executed by
  anything of this project's.
* **The pipeline hazards**, which need a controlled loop and a timing harness.
* **`RLXFW-ID0`, the build-identity string added on 2026-09-01, has never been
  read off the board.** It is checked in the image — present once in mine,
  absent from the vendor's — and its behaviour on the wire is 推 until a
  seating prints it.
