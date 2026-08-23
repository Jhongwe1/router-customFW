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
| **Active step** | `DAY-ZERO` item 2a closed 2026-08-23 (`notes/lwl-mystery.md`). `S0a` closed the same day **with a recorded deviation** — C-10. `S0b` waits for the first bench session |
| **Last session** | 2026-08-23, desk only — `S0a`, then `git init`. Seven encrypted archives; restore drill from copy ② after a physical replug, five trees at zero differences; first commit `9c40aa4` pushed to a **private** `Jhongwe1/router-customFW` (`CHARTER.md`: public from v0.1, and this is S0). `LOG.md` |
| **Next after this** | `DAY-ZERO` item 2b (cache model, F49). Item 1 closed inside `S0a`; item 2a closed. Item 3 is half done: `git init`, first commit and a private remote are in; the submodule pin at `4d3ff26`, `fetch-sources.sh` and the `README.md` first screen are not |
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
| C-3 | `burn()` @ `0x80401318` — where does it write, and what is the SPI command interface? | R8 precondition ② |
| C-4 | Does the loader still offer the ESC window when the kernel region is garbage? | R8 precondition ⑤ |
| C-5 | Which instructions does the vendor kernel emulate? (`simulate_llsc`, `math-emu`, …) | R2d |
| C-6 | Cache management model: R3000 (`Status.IsC`) or MIPS32 (`cache` insn)? — F49 | R1d |
| C-7 | Answered at the desk, `notes/lwl-mystery.md`: stage2 0, busybox 0, boa 176 → 144 → 0 across builds from 2015 to 2020. **Residual, and it is the one that decides F34**: does the vendor kernel carry an unaligned-access emulation handler, and what changed in how `boa` was built between 2018-03-30 and 2019-03-15? | R2, then R1a on silicon |
| C-8 | Does a watchdog reset still present the ESC window, or does bootcode take a different path? | R4 |
| C-9 | Hazards beyond loads: stores, `mflo`/`mfhi`, `mfc0`/`mtc0` — F47, upstream open #100 | R1b |
| C-10 | Copy ③ has never been read back. Is what sits on Google Drive what was uploaded? Copies ① and ② were verified byte for byte; ③ was not. | S0 |

---

## Corrections

Every time the plan changes, one line here, and one row in the plan's §0. **A plan
that records where it was wrong is more credible than one that looks right.**

| Date | What changed | Who caught it |
|---|---|---|
| 2026-08-23 | `DAY-ZERO` 2a predicted the split would be bare metal versus userspace: bootcode avoids the unaligned instructions, userspace takes the toolchain default and lets the kernel clean up. Measured: `busybox` is userspace on the same rootfs and has none either. The split is `boa` against everything else, and it closes in 2019. | `tools/opcount.py` over six firmware trees, `notes/lwl-mystery.md` |
| 2026-08-23 | `DAY-ZERO` §現況 states the upstream working tree is clean. It is not: 13 modified tracked files and 2 untracked, none of them pushed. The two untracked files are unsent disclosure material; their names are deliberately not recorded in a public file, for the same reason the backup manifest was split into a K1 and a K2 side. | `git status` / `git log @{u}..`, run while enumerating what `S0a` had to cover |
| 2026-08-23 | `S0a`'s DoD was "逐檔 `sha256sum` 相符". That check covers 6,346 of 7,770 paths and no mode bits at all, and it reports zero differences on a tree with a cleared setgid bit and a repointed symlink. Replaced by a type/mode/uid/gid/size/mtime/digest manifest (`tools/fsmanifest.py`) with one scope control and three negative controls. | `S0a` control N4 |
| 2026-08-23 | `S0a`'s backup scope listed only `$FWRE_WORK`. Outside it were `refs/` (two datasheets that cannot be committed), `plan/` (gitignored, single copy), this repository itself (not yet under git), and `../router`'s uncommitted work. | `S0a`, listing what is irreplaceable rather than what is large |
| 2026-08-23 | `S0a` copy ② named "another physical disk / USB stick" as if one existed. At the start of the session there was one physical disk and no removable media, so `S0a` could not have closed that day without hardware being attached. | `Get-PhysicalDisk`, `Get-Disk`, `Win32_DiskDrive`, agreeing |
| 2026-08-23 | This file carried a line about what a dated commit history signals to a recruiter — a House style violation (`../router/CLAUDE.md`: committed files are written for an engineer, never for a hiring panel). Removed. `CLAUDE.md` now states the rule so it does not recur. | Author, comparing against the upstream repo's conventions |
| 2026-08-22 | Plan v3 → v4: 18 findings. The five structural ones: R1 must run bare metal (the kernel emulates `ll`/`sc` and the FPU); cache model (F49) is an unmeasured precondition for R1/R5/R6; R9 does depend on R6 having a NIC; the single dependency was verified but never backed up; R8's "needs a spare unit" was over-conservative. | Plan review, `plan/REVIEW-2026-08-22.md` |
