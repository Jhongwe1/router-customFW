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
| **Active gate** | `S0` — safety net |
| **Active step** | `DAY-ZERO` item 3 — upstream pinned at `4d3ff26` and verified, `README.md` first screen written, source trees fetched. Items 0, 1, 2a, 2b, 2c closed the same day. `S0a` closed **with a recorded deviation** — C-10. `S0b` waits for the first bench session |
| **Last session** | 2026-08-23, desk only — `S0a`, then `git init`. Seven encrypted archives; restore drill from copy ② after a physical replug, five trees at zero differences; first commit `9c40aa4` pushed to a **private** `Jhongwe1/router-customFW` (`CHARTER.md`: public from v0.1, and this is S0). `LOG.md` |
| **Next after this** | `DAY-ZERO` item 4 — six questions about loader command semantics, three of which upstream has already answered. Then item 6 (build container), item 7 (`hazlint`), item 8 (`rlxprobe`). Item 5 is the only bench item in this section |
| **Blocked on** | nothing at the desk. `S0b` needs the device on the bench |

**Step list for the active gate**: `plan/DAY-ZERO.md` items 0–8.
On entering a gate that has no step list yet, the first session writes one here
before doing any of it (`plan/SESSIONS.md` §0b).

---

## Gate board

Status: `·` not started · `~` in progress · `✓` closed (needs an evidence link)
· `⊘` deliberately not done (needs a reason and a category — plan §17)

| Gate | What closing it means | Est. | Actual | Status | Evidence |
|---|---|---:|---:|:---:|---|
| **S0** | backup restored and verified; three power experiments written up | 1 | — | `~` | `S0a` `LOG.md` 2026-08-23, drill from copy ② not ③ (C-10) · `S0b` not started |
| **R0** | vendor kernel booted from RAM, **0 flash bytes written** | 5 | — | `·` | |
| **R1** | ISA / hazard / CP0 table, **bare metal**, positive + negative controls hold | 16 | — | `·` | |
| **R2** | toolchain equivalence measured; the right GPL drop named; T-modern spike resolved | 8 | — | `·` | |
| **R3** | my kernel boots to a shell **and pings** | 12 | — | `·` | |
| **R4** | edit → result in < 90 s; scripted reset via WDT | 5 | — | `·` | |
| **R5** | five drivers in-tree, each accepted, 10 boots without an oops | 22 | — | `·` | |
| **R6** | my Ethernet driver: `ping`, an `iperf3` number, 30 min flood clean | 35 | — | `·` | |
| **R7** | my userspace; `system()`/`popen()` count = 0 from two independent sources | 32 | — | `·` | |
| **R8** | signed update accepted, one flipped bit rejected, 10 power-cuts survived | 18 | — | `·` | |
| **R9** | three-column differential table, **third column not empty** | 16 | — | `·` | |
| **P1** | `mfgtest` passes on a good unit, and every check has been made to FAIL once | 8 | — | `·` | |
| **P2** | boot-time breakdown + throughput, both firmwares, same script | 6 | — | `·` | |
| **P3** | bring-up report — grows every gate, closed at v1.0 | 5 | — | `·` | |
| **P4** | complete GPL release + a byte-identical rebuild of my own image | 3 | — | `·` | |
| | | **192** | | | |

**Est. is uncalibrated.** The calibration point is the first driver (R5). When it
lands, multiply every remaining row by the measured ratio and say so here.

---

## Release clock

| | Contents | Target (optimistic / ×1.8) | Shipped |
|---|---|---|---|
| **v0.1** | S0 + R0 + R1 + `rlxprobe` + first write-up | wk 3 / wk 5 | — |
| v0.2 | R2 + R3 — kernel boots (video) | wk 7 / wk 12 | — |
| v0.3 | R4 + R5 — five drivers + logic-analyser traces | wk 12 / wk 21 | — |
| v0.4 | R6 — my Ethernet driver | wk 17 / wk 30 | — |
| v0.5 | R7 — my userspace | wk 23 / wk 41 | — |
| v1.0 | R8 + R9 + P1–P4 + demo video | wk 29 / wk 52 | — |

**Public from v0.1.** Held disclosure items stay out until `docs/disclosure.md`
says otherwise — `plan/` §15 holds the policy.

---

## Carried forward

Open questions that outlive a single session. Each one names the gate that will
close it. **An item with no owning gate is a bug in this list.**

| # | Question | Owning gate |
|---|---|---|
| C-1 | Does the loader scan for the `cr6c` tag, or is the kernel offset hard-coded? | R8 (A/B layout) |
| C-2 | Is there anywhere to inject a kernel command line? (upstream `P9-1`) | R4 |
| C-3 | Answered, `docs/loader-flash-write.md`: `burn()` is the image parser and dispatcher, bounds-checked only at the top against chip capacity, **no lower bound**, and `boot` is one of its eight accepted section signatures. SPI controller at `SFCR 0xb8001200` / `SFCR2 0xb8001204` / `SFCSR 0xb8001208` / `SFDR 0xb800120c`, two sources agreeing; `RDID` is `0x9F`. **Residual**: which of `burn()`'s four callees erases and which programs, and the `SFCSR` transaction bit layout, which is single-source. | R5b, R8 |
| C-4 | Answered from vendor source of **a different bootcode generation**: a failed image check skips the ESC wait and goes straight to `goToDownMode()`, the same place ESC reaches. This unit's `stage2` carries the same two destination strings but not the same image-check messages, so the structure is inferred for this unit. **Confirm on the bench, kernel region only.** | R8 precondition ⑤ |
| C-5 | Which instructions does the vendor kernel emulate? (`simulate_llsc`, `math-emu`, …) | R2d |
| C-6 | Answered, `notes/cache-model.md`: **R3000 model**. The vendor kernel reaches `c-r3k.c` through `cpu_has_3k_cache` and uses `Status.IsC`/`SwC`; the bootcode uses a Lexra CP0 register 20 instead and never touches `IsC`. `0x002` invalidates I-cache and `0x200` flushes D-cache, two sources agreeing. **Residual**: CP0 20 commands `0x010` and `0x020` are single-source and unnamed; cache size, line size and associativity unknown. | R1d, R1e |
| C-7 | Answered at the desk, `notes/lwl-mystery.md`: stage2 0, busybox 0, boa 176 → 144 → 0 across builds from 2015 to 2020. **Residual, and it is the one that decides F34**: does the vendor kernel carry an unaligned-access emulation handler, and what changed in how `boa` was built between 2018-03-30 and 2019-03-15? | R2, then R1a on silicon |
| C-8 | Does a watchdog reset still present the ESC window, or does bootcode take a different path? | R4 |
| C-9 | Hazards beyond loads: stores, `mflo`/`mfhi`, `mfc0`/`mtc0` — F47, upstream open #100 | R1b |
| C-10 | Copy ③ has never been read back. Is what sits on Google Drive what was uploaded? Copies ① and ② were verified byte for byte; ③ was not. | S0 |
| C-11 | The pinned baseline `4d3ff26` exists on `origin/w08-writeup` only, not on the upstream default branch. If that branch is deleted, rebased or renamed, the pin becomes unfetchable and R9's differential argument loses its anchor. A tag would fix it permanently. | R9 |

---

## Corrections

Every time the plan changes, one line here, and one row in the plan's §0. **A plan
that records where it was wrong is more credible than one that looks right.**

| Date | What changed | Who caught it |
|---|---|---|
| 2026-08-23 | The commit that records the pinned baseline is `dd85c37`, whose subject is about the datasheet and says nothing about it. `git add <one file>` followed by `git commit` commits the **whole index**, and `.gitmodules` and `upstream` had been staged earlier. Not rewritten: the history is pushed, and a force push to fix an attribution is the wrong risk class for the problem. `git log -- .gitmodules` finds it; this row explains it. | `git show --stat` after the fact |
| 2026-08-23 | `tools/fetch-sources.sh` tested `[ -d upstream/.git ]` before checking the pinned baseline. In a submodule `.git` is a **file** holding `gitdir: ...`, so the test was false and the check — the one that catches the differential baseline having moved — silently never ran. Changed to `-e`; it now fires and passes. | the fetch reporting `skip upstream not present` about a submodule that was demonstrably present |
| 2026-08-23 | `SOURCES.json` sends every GPL drop to `src-vendor/`, which sits on NTFS. The vendor kernel trees carry paths that differ only in case — `xt_CONNMARK.h` against `xt_connmark.h` and 29 more pairs in `wecb-vz-gpl` alone. Measured on `rtl819x-toolchain`: **254 files would have been lost silently**. `src-vendor` is now a symlink into ext4 under `$FWRE_WORK/rebuild/`, which is where `CLAUDE.md` already says binaries belong. | creating `B.h` and `b.h` on `/mnt/c` and getting one file |
| 2026-08-23 | `CLAUDE.md` says DrvFs drops symlinks and permission bits. Measured: symlinks **survive** (`ln -s` works, `readlink` resolves); permission bits do not — everything reads back as `777`, and git responds by setting `core.fileMode=false`, so it cannot see mode changes at all. The rule is right; half its stated reason is not. | a five-line probe on `/mnt/c` |
| 2026-08-23 | `.gitignore` had `src-vendor/` with a trailing slash, which matches directories only. Once `src-vendor` became a symlink, git wanted to commit it. Pattern corrected and `tools/test-gitignore.sh` grew a fourteenth case for exactly this. | `git status` after making the symlink |
| 2026-08-23 | `git submodule add` recorded the upstream default branch's HEAD (`277af488`) in the index, not the pinned `4d3ff26` that was then checked out. Committing at that point would have recorded the wrong baseline — the one thing R9's credibility rests on. `git add upstream` before committing. | `git submodule status` showing a `+` prefix |
| 2026-08-23 | `DAY-ZERO` 2c placed the `WREN` / `PP` / `RDSR` sequence inside `burn()`. It is not there: `burn()` is the image parser and dispatcher, and the SPI command layer is at `0x804055ac`–`0x80405d44`, which it reaches indirectly. The plan was off by one layer. | reading `burn()`, `docs/loader-flash-write.md` |
| 2026-08-23 | `DAY-ZERO` 2b argued the loader must have made the I-cache see freshly written RAM, "otherwise P9-12 would not have succeeded". Measured: from `0x804004a8` the loader jumps to the KSEG1 alias of its own next instruction and runs uncached, so for its own code it did not have to. It does flush D-then-I immediately before jumping to the kernel image, so the conclusion holds — but not for the stated reason. | reading the reset path, `notes/cache-model.md` |
| 2026-08-23 | `DAY-ZERO` 2a predicted the split would be bare metal versus userspace: bootcode avoids the unaligned instructions, userspace takes the toolchain default and lets the kernel clean up. Measured: `busybox` is userspace on the same rootfs and has none either. The split is `boa` against everything else, and it closes in 2019. | `tools/opcount.py` over six firmware trees, `notes/lwl-mystery.md` |
| 2026-08-23 | `DAY-ZERO` §現況 states the upstream working tree is clean. It is not: 13 modified tracked files and 2 untracked, none of them pushed. The two untracked files are unsent disclosure material; their names are deliberately not recorded in a public file, for the same reason the backup manifest was split into a K1 and a K2 side. | `git status` / `git log @{u}..`, run while enumerating what `S0a` had to cover |
| 2026-08-23 | `S0a`'s DoD was "逐檔 `sha256sum` 相符". That check covers 6,346 of 7,770 paths and no mode bits at all, and it reports zero differences on a tree with a cleared setgid bit and a repointed symlink. Replaced by a type/mode/uid/gid/size/mtime/digest manifest (`tools/fsmanifest.py`) with one scope control and three negative controls. | `S0a` control N4 |
| 2026-08-23 | `S0a`'s backup scope listed only `$FWRE_WORK`. Outside it were `refs/` (two datasheets that cannot be committed), `plan/` (gitignored, single copy), this repository itself (not yet under git), and `../router`'s uncommitted work. | `S0a`, listing what is irreplaceable rather than what is large |
| 2026-08-23 | `S0a` copy ② named "another physical disk / USB stick" as if one existed. At the start of the session there was one physical disk and no removable media, so `S0a` could not have closed that day without hardware being attached. | `Get-PhysicalDisk`, `Get-Disk`, `Win32_DiskDrive`, agreeing |
| 2026-08-23 | This file carried a line about what a dated commit history signals to a recruiter — a House style violation (`../router/CLAUDE.md`: committed files are written for an engineer, never for a hiring panel). Removed. `CLAUDE.md` now states the rule so it does not recur. | Author, comparing against the upstream repo's conventions |
| 2026-08-22 | Plan v3 → v4: 18 findings. The five structural ones: R1 must run bare metal (the kernel emulates `ll`/`sc` and the FPU); cache model (F49) is an unmeasured precondition for R1/R5/R6; R9 does depend on R6 having a NIC; the single dependency was verified but never backed up; R8's "needs a spare unit" was over-conservative. | Plan review, `plan/REVIEW-2026-08-22.md` |
