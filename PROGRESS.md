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
| **Active step** | `DAY-ZERO` item 4 — closed, `docs/loader-command-semantics.md`. Items 0, 1, 2a, 2b, 2c, 3 closed the same day. `S0a` closed **with a recorded deviation** — C-10. `S0b` waits for the first bench session |
| **Last session** | 2026-08-23, desk only — item 4. The loader **scans** six 64 KiB offsets for the kernel (C-1 closed); the image check is located in this unit's own code and is silent on failure (C-4's structural half closed); `EB`/`EW`/`FLR`/TFTP are four unbounded RAM-write paths and `J BFC00000` is a stock watchdog reset, so R4's `bench-ci` needs no new primitive; `movz`/`movn` execute on this unit's boot path. `LOG.md` |
| **Next after this** | `DAY-ZERO` item 6 (build container), item 7 (`hazlint`), item 8 (`rlxprobe`). Item 5 is the only bench item in this section |
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
| C-1 | Answered, `docs/loader-command-semantics.md` §a: **it scans.** `0x80408084` probes `0x010000`, `0x020000`, `0x030000`, then sweeps `[0x030000, 0x060000]` at a `0x10000` stride skipping those three — six candidates, and this unit's kernel is at `0x060000`, the last one. The accepted candidate is left in the global `0x8040DD3C`. Corroborated by the vendor's `check_image_header()`. **R8's A/B layout needs no loader change: any 64 KiB boundary in that window is a slot, and the lowest good image wins.** **Residual**: two `DW`s at the bench refute or confirm it (§8 rows 1–2). | R8 (A/B layout) |
| C-2 | Answered, `docs/loader-command-semantics.md` §d: **no.** Upstream's `P9-1` was refuted with three static sources and the dynamic half agreed; the 13-needle scan was re-run in this repo — 0 hits, with all 17 commands found as the control. The plan's row saying it was still open was stale. **The rlxfw answer is different from the vendor answer**: since `EB`/`EW` write any address unbounded, R4 puts an **uncompressed cmdline buffer at a fixed address in its own image** and patches it from the console before `J`. Zero flash writes. **Residual, and it is R4's first payload's job**: confirm the buffer survives load-to-entry untouched. | R4 |
| C-3 | Answered, `docs/loader-flash-write.md`: `burn()` is the image parser and dispatcher, bounds-checked only at the top against chip capacity, **no lower bound**, and `boot` is one of its eight accepted section signatures. SPI controller at `SFCR 0xb8001200` / `SFCR2 0xb8001204` / `SFCSR 0xb8001208` / `SFDR 0xb800120c`, two sources agreeing; `RDID` is `0x9F`. `ComSrlCmd_RDID()` at `0x804058bc` spins on `SFCSR` bit 27 and writes `0x9F000000` to `SFDR`, which confirms the bit layout from behaviour rather than documentation. **Residual**: which of `burn()`'s four callees erases and which programs; and whether either caller of `ComSrlCmd_RDID()` stores the result to memory — if one does, `EB` reads the JEDEC ID at the next bench session with no new code. | R5b, R8 |
| C-4 | **Upgraded from inferred to read**, `docs/loader-command-semantics.md` §a: `doBooting()` is at `0x80408690` in **this unit's own code**, and `beqz a0` on a zero image-check result goes straight to `goToDownMode()` with no ESC wait and no message. The check itself is `check_image()` at `0x80407D50` — signature (`cs6c`→1, `cr6c`→2) plus a 16-bit sum over the RAM copy that must be zero. It looked un-locatable because this build **compiles out the `no sys signature` / `sys checksum error` strings while keeping the rootfs ones** — the check is silent, not missing. **Residual, still a bench item**: that a deliberately corrupted image reaches the prompt in practice. Kernel region only. | R8 precondition ⑤ |
| C-5 | Which instructions does the vendor kernel emulate? (`simulate_llsc`, `math-emu`, …) | R2d |
| C-6 | Answered, `notes/cache-model.md`: **R3000 model**. The vendor kernel reaches `c-r3k.c` through `cpu_has_3k_cache` and uses `Status.IsC`/`SwC`; the bootcode uses a Lexra CP0 register 20 instead and never touches `IsC`. `0x002` invalidates I-cache and `0x200` flushes D-cache, two sources agreeing. **Residual**: CP0 20 commands `0x010` and `0x020` are single-source and unnamed; cache size, line size and associativity unknown. | R1d, R1e |
| C-7 | Answered at the desk, `notes/lwl-mystery.md`: stage2 0, busybox 0, boa 176 → 144 → 0 across builds from 2015 to 2020. **Residual, and it is the one that decides F34**: does the vendor kernel carry an unaligned-access emulation handler, and what changed in how `boa` was built between 2018-03-30 and 2019-03-15? | R2, then R1a on silicon |
| C-8 | Still open, but the experiment is now specified — `docs/loader-command-semantics.md` §f. **`J BFC00000` is the reset**: it writes `WDTCNR = 0` (`0xB800311C`, four sources including this loader's own second use of the idiom after `reboot.......`) and spins with interrupts masked. `WDTE[7:0] ≠ 0xA5` runs the watchdog, `OVSEL[3:0] = 0000` is the shortest of ten timeouts. **The discriminator is `WatchDogIND`, bit 20 of the same register: `1` after a watchdog reset, `0` after power-on or pin reset** — so "did the watchdog fire" is answerable without inference. Wall-clock delay is **not** established: `CDBR = 0x000E0000` (divisor 14) but the bus clock it divides is unmeasured. | R4 |
| C-9 | Hazards beyond loads: stores, `mflo`/`mfhi`, `mfc0`/`mtc0` — F47, upstream open #100 | R1b |
| C-10 | Copy ③ has never been read back. Is what sits on Google Drive what was uploaded? Copies ① and ② were verified byte for byte; ③ was not. | S0 |
| C-12 | **Does this core implement `movz`/`movn`, or is something emulating them silently?** `docs/loader-command-semantics.md` §9: 18 conditional moves in the loader's code region and **nothing else outside MIPS-I** (two decoders, both with demonstrated false positives in rodata as the control). Two of them are in `check_image()`, which runs on every boot. The loader carries an exception reporter (`Undefined Exception happen.`, `cp0_cause=%X`) and **18 console captures — 4 covering the whole window — contain neither string**. Bears on the `-march` decision and on RLX4181-vs-RLX5281. **Settled by one instruction under R1a's bare-metal RI handler.** Also hands R1d a fact: the stock loader already installed exception handling, so R1's handler replaces rather than fills. | R1a |
| C-13 | `check_image()` returns "no image" outright when the global `0x8040DBA4` is 1 (the vendor calls it `gCHKKEY_HIT`). Its only writer at `0x804082B4` reads `0xB8002014` bit 24 and compares the top byte of `0xB8002000` — the UART path, so it looks like *a key was pressed*, but the register addresses are not confirmed against the datasheet and the argument is not traced. **A flag that makes the loader declare every image bad is a rescue path and possibly a hazard.** Fifteen minutes at the desk. | R8 |

---

## Corrections

Every time the plan changes, one line here, and one row in the plan's §0. **A plan
that records where it was wrong is more credible than one that looks right.**

| Date | What changed | Who caught it |
|---|---|---|
| 2026-08-23 | My first sweep for non-MIPS-I opcodes reported `cache`, `ll`, `clz`, `teq`, `tge` and an `lwr` — **all false positives.** The decoder had no way to tell code from data and was reading the string table: `'pload, F'` decodes as `clo`, `0xc0a80001` (`192.168.0.1`) as `ll`. Re-run with the hex bytes printed beside every hit and a stated code/rodata boundary, the code region holds **only** `movz` and `movn`. The fix was not a better decoder — it was making the tool print the evidence that lets a reader overrule it. | printing the bytes next to the mnemonics instead of the mnemonics alone |
| 2026-08-23 | `docs/loader-flash-write.md` §3 said the loader's image check *"exists but has not been located in A"* and that the `if (flag) … else goToDownMode()` structure was **inferred for this unit**. Both are now read out of this unit's own code — `check_image()` at `0x80407D50`, `doBooting()` at `0x80408690`. The reason it read as un-locatable is that this build compiles out the two `sys signature` / `sys checksum` strings while keeping the rootfs ones, and an absent string had been read as an absent check. | `DAY-ZERO` 4a, following the `cr6c` immediate rather than the diagnostic strings |
| 2026-08-23 | `DAY-ZERO` item 4 row (d) says *"upstream `P9-1`, still open"*. **It was closed and refuted before this repo existed** — three static sources plus a bench confirmation on 2026-08-17. Two sessions were planned around a question that had an answer. The row also asked the wrong question for rlxfw: "can the loader pass a cmdline" is the vendor's question; rlxfw builds the image, so the operative question is where R4 puts a patchable buffer. | reading upstream's `RUNBOOK` §8.12.10 before starting the work, rather than trusting the plan's status column |
| 2026-08-23 | `DAY-ZERO` item 4 row (f) asks *"which of the 17 commands can write an arbitrary memory address"* — singular. There are **four**: `EB`, `EW`, `FLR` (whose first argument is an unbounded RAM destination taking whole flash regions) and a TFTP write after `LOADADDR` (megabytes). The narrow question would have produced a correct answer about `EB`/`EW` and missed the two that move real volume, which are the ones R0 and R4 will actually use. | reading `FLR`'s handler while looking for something else |
| 2026-08-23 | C-11 closed the day it opened: the upstream repository now carries an annotated tag `rlxfw-baseline` on `4d3ff26`, so the differential baseline is reachable without any branch. `SOURCES.json` records the tag beside the commit. Also measured while doing it: `../router` gained a commit on top of `4d3ff26` during this session, and the pinned commit is still an ancestor, so the anchor held. | verifying the pin after tagging |
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
