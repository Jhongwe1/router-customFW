# `PROGRESS.md` § `R4`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 854–1011, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R4`'s step list — ✅ CLOSED 2026-09-02, in four segments

**Opened 2026-09-01** on the owner's decision, immediately after `P4b-gate`
closed. **Est. — and there are two numbers, which is the `Est.` column defect
again.** The gate board says **5**; the planning material says **3 desk + 2
bench + 3 instrument = 8**. The analysis under the gate board already settled
which one a decision should be made against: `Actual` counts segments consumed
in `LOG.md` including instrument days, and the only estimate with that
definition is the plan's. **So the budget carried here is 8, 猜, uncalibrated**,
and the board's 5 is recorded as the second number rather than reconciled.

### What this gate inherits, with its marks

| | | mark |
|---|---|---|
| `WDTCNR` is at `0xB800311C`, reset value `0xA5000000`, `WDTE[7:0]` = `0xA5` is the **stop** pattern, and `WatchDogIND` bit 20 reads `0` after a power-on reset | `SPEC.md` `REG-12` | 量 |
| `J BFC00000` **is** a reset: it writes `WDTCNR = 0` and then spins with interrupts masked, so only the watchdog can leave that loop | `SPEC.md` `LDR-33`, four sources | 讀 |
| The loader prints `Reboot Result from Watchdog Timeout!` immediately after `ramSize: 32M` where a cold boot prints a single space | `C-8`, three instances | 量 |
| `quietm` reaches a shell prompt in **7.260 s** from `J`; `loudm` in **8.98 s** | `SPEC.md` `FW-32` / `FW-27` | 量 |
| One kernel build cell takes **49 s** | `rep4`, twenty-first segment | 量 |
| The watchdog's wall-clock timeout at its two HIGH settings: **1118.133 ms** (`OVSEL=1001`) and **557.583 ms** (`OVSEL=1000`), ratio 2.0053 | `SPEC.md` `CLK-08`, `bench/2026-08-25/H3c-D4.timing` | 量 |
| The timeout at the **lowest** `OVSEL`, which is what `WDTCNR = 0` selects and therefore what `J BFC00000` fires — **2.184 ms** by halving from the measured point, never observed | derived here; `R4-1` predicts it, `R4-2` measures it | 推 |

### 🔴 Two things the plan says about this gate that this repository's own readings contradict

**① *"`F35` has already proved the loader itself writes the watchdog at
`0xB800311C`"* — 量 says it does not.** `CLK-11`: the loader **never writes
`WDTCNR`**, except two `sw zero` sites each followed by an in-place spin —
`0x804012F8` (the `reboot.......` path) and `0x804092E8`. So *the loader feeds
the dog* is false, and the premise the plan builds §1 on is not the one that
holds.

🟢 **What holds instead is better, and it may make §1 free.** `LDR-33` says
`J BFC00000` already performs exactly the recipe a scripted reset needs — write
`WDTCNR = 0`, then spin where only the watchdog can reach you. **It is an
existing loader command**, so a scripted reset may require no new register write
at all. ⚠️ **That is 讀, not 量**: nothing has issued `J BFC00000` on this
device and watched what comes back. `R4-1` predicts it, `R4-2` runs it.

**② The plan's acceptance for §1 — *"the ESC window still appears after the
reset"* — is the right test, and part of it is already answered in a direction
the plan did not anticipate.** Seating 8's reel segment 7 holds a watchdog reset
followed by the **vendor's** firmware booting whole, because after a reset the
loader re-stages `0x80500000` from flash. So *the ESC window appears* and *the
reset returns me to my image* are two different claims, and only the first is
what §1 needs. **The second is false by construction** and is the reason the
loop has to re-upload, which is what `R4-0` has to cost.

### 🔴 And one thing this gate has to decide before it can be planned: whether NFS root belongs in it at all

The plan's headline is *NFS root development loop*. **讀 2026-09-01,
`config/rlxfw-kernel.delta`: there is no `CONFIG_NFS_FS`, no `CONFIG_ROOT_NFS`
and no `CONFIG_IP_PNP` anywhere in it, and `CONFIG_CMDLINE` is
`"console=ttyS0,38400"` with `root=` deliberately removed** (Decision B — the
first boot mounts an initramfs built from this unit's own userspace).

**So NFS root is not a setting to flip; it is three config additions plus a
dependency on the vendor `rtl819x` driver coming up early enough.** ⚠️ **And it
shortens the wrong loop.** NFS root removes the image upload for a **userspace**
change. A **kernel** change still has to be built and uploaded whatever the root
filesystem is — and `R5`, the gate this one exists to make fast, is six kernel
drivers. **Whether NFS root is on this gate's critical path is a decision, and
`R4-0`'s measurement is what decides it.** Written here so that the decision is
visible if it goes the other way.

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R4-0`** ✅ **2026-09-01** | desk 1 | **The loop that exists, timed end to end**, on the recipe that already boots (`quietm`). Every stage separately: edit, stage + build, image assembly, get to `<RealTek>`, TFTP, `J`, first useful output. **Machine time and human time counted in different columns**, because only one of them is what `< 90 s` is about | Every stage has a number, the numbers sum to the measured total, and the sum is compared against the two numbers already in `SPEC.md` (49 s build, 7.260 s boot) rather than replacing them. **A stage with no number is recorded as unmeasured, not estimated** | **That the build dominates.** 49 s + 7.260 s is already 57 s before the upload, so the machine part may be near the ceiling with nothing removed — in which case `< 90 s` is a statement about the human stages and the DoD needs saying differently |
| **`R4-1`** ✅ **2026-09-01** | desk 1 | **The scripted-reset recipe, written and predicted before power.** What `J BFC00000` should print, what `C-8`'s discriminator should read, what an ESC window should look like afterwards, and what each of those looks like if the reset does *not* happen | A prediction block under `bench/`, frozen and committed before the seating, with `check-predictions` reporting `0 of N` at the desk. **Both directions written**: what a successful reset prints AND what a failed one prints, because a cell that can only come out one way is not a cell | **The ESC window.** If the bootcode takes a different path for a watchdog reset than for a cold one and skips the ESC window, the recipe is unusable *and that is itself a finding* — it changes `D4`'s rescue assumption, which is the sentence the whole zero-write posture leans on |
| **`R4-2`** ✅ **2026-09-01** | bench 1 | **The run**, sharing a seating rather than spending its own power cycle. `J BFC00000`, the discriminator, the ESC window, **N resets in a row**, and the **lowest-`OVSEL`** timeout — the one `WDTCNR = 0` selects, 推 2.184 ms, which no seating has observed | `Reboot Result from Watchdog Timeout!` appears where a cold boot prints a space, the `<RealTek>` prompt is reachable afterwards, and it repeats. **the 2.184 ms prediction is confirmed, refuted, or recorded as below the instrument's resolution** — and the third outcome is a real answer, not a miss: the console channel quantises at ~2 ms, so a reset this fast may be unresolvable from here, which is itself what an automated loop needs to know | **One success is not a loop.** A reset that works once and wedges on the third is worse than one that never works, because the loop will be trusted. The cell has to be N in a row with N written before the seating |
| **`R4-3`** ✅ **2026-09-02** | desk 2 | **The loop as a tool**, with its controls: edit → build → assemble → upload → reset → capture → assert, and a positive control that it can fail. The `--keep` tension is this step's to resolve or to record | The tool runs the whole loop unattended and **reports a number**; a deliberately broken input turns it red. `ci-census`-shaped arithmetic if it grows cases | **`--keep`.** An incremental build is the obvious way to cut the 49 s, and `rlxfw-kbuild.sh --keep` is marked `[TESTING ONLY]` because it breaks `.version` and therefore `P4a`'s `L2-6`. **This gate wants exactly the thing the reproducible-build gate forbade**, and pretending otherwise is how a Level-2 claim quietly dies 🟢 **DONE, in two halves.** 桌面半 2026-09-02(第二十五段):工具落地,26 個控制,斷言由建置算出。上機半 2026-09-02(第二十六段,seating 10):`--mode bench` 第一次對著板子跑完,**報出 34.74 s**,七個斷言全成立。🔴 **而 `--keep` 一個字都沒有打開** —— `R4-0` 已經量出它只買 3–5 %、而且拒絕與 `--marks` 一起跑,所以這一格的張力是靠量測消掉的不是靠讓步。🔴 **通電前一小時的稽核找到三個缺陷**,兩個安全(`S5b` burn flag 回讀、`S6b` staged head 比對,兩個都在板子上發射並通過)、一個是這個 gate 的核心(`S3` 從來沒有接到 `S2` 的樹)。控制 26 → 45 |
| **`R4-4`** ✅ **2026-09-02** | desk 1 | **The write-up**, and `docs/GATE-RESULTS.md` gains its ~~sixth~~ **seventh** entry 🔴 *(the ordinal was wrong when this row was written, and finding out why was part of the step: `P4b-gate` closed 2026-09-01 and the gate that CREATED that ledger did not put itself in it, so there were five entries where `D2`'s own property — one per closed gate — asks for six)* | The DoD read one row at a time, what the gate did not establish written, and the operating clause re-run over ~~six~~ **seven** entries 🟢 **DONE 2026-09-02(第二十六段).** `docs/GATE-RESULTS.md` 收兩筆:`P4b-gate` 的缺筆(按結案日插在 `P4a` 後面,所以 clause 讀到的順序就是它當天本來該讀到的)與 `R4` 的。clause 在**七筆六對**上重跑:仍然只指 `CPU-45`,而且是從同一對指的 —— **兩筆新條目沒有產生新的發射**。🔴 **而七筆讓 clause 自己的射程第一次看得見**:*DoD 指名了一個成品而不是它要的性質* 重複了兩次(`R3` 的 `D3` 指 `MemTotal:`、`P4b-gate` 的 `D2` 指一個 gitignore 掉的路徑),而它們**隔了兩筆**,規則寫的是「相鄰」所以看不到。**記下來,沒有去改規則** —— 因為得不到你已經想好的答案就去改規則,正是這種規則不再是儀器的方式 | 🔴 **2026-09-16 (`R1z-2`): this cell held a bare `✅` and this column is *where it is most likely to be wrong*** — a closure mark in a column that means something else, which is `L6`’s own subject one layer down. The mark is now in cell 1 with the date `🟢 DONE 2026-09-02` in cell 4 already carried. **What is most likely to be wrong here is unchanged and was never written**: the write-up step of a gate cannot be refuted by the gate it writes up |

### The DoD, split into what can be refuted

* **D1** the loop that existed before this gate has a measured end-to-end number,
  broken into stages, with machine time and human time separated.
* **D2** a reset can be triggered **without touching the power**, from a
  committed script, and the `<RealTek>` prompt is reachable afterwards — N times
  in a row, N written before the seating.
* **D3** the loop, from a source edit to an assertion about what the board
  printed, runs unattended and reports a number.
* **D4** that number is **under 90 s**, or the gate closes with the number it
  actually reaches and the reason recorded.

🔴 **`D4` is deliberately written with an escape, and the escape is the honest
half.** `< 90 s` is inherited from the plan and has never been checked against
an arithmetic this repository can already do: 49 s of build plus 7.260 s of boot
is 57 s before the upload is counted. **A DoD that can only be met by a number
nobody has verified is reachable is a DoD that invites its own fudging** — `R3`'s
`D3` named an observable that does not exist, and this is the same failure one
step earlier.

### Refutation condition, written now

> **否證 D2** — the scripted reset is refuted by the **absence** of `C-8`'s
> discriminator: if the console prints a single space where
> `Reboot Result from Watchdog Timeout!` was predicted, the reset did not
> happen and no amount of *the board came back* substitutes for it. 🔴 **And the
> reverse is a separate claim**: the discriminator appearing proves a watchdog
> reset occurred, **not** that the ESC window is reachable. Both are cells.

> **否證 D3** — a loop tool that cannot be made to fail proves nothing. Its
> positive control is a deliberately broken input — a source edit that must
> change the image, an assertion that must not match — and it has to go red.

### Stop-loss, written now

* **Two seatings** and `D2` still has no reset that repeats → the scripted reset
  is recorded 未定, the loop keeps its human stage, and `D1`/`D3`/`D4` are
  re-scoped to the machine stages alone. **This gate blocks nothing**; `R5` gets
  slower, it does not get stopped.
* **If `R4-0` shows the machine stages alone exceed 90 s**, `D4` is renegotiated
  in the open before any work is done to chase it, not after. The number to beat
  is then whatever `R4-0` measured, and the plan's 90 is recorded as an estimate
  that did not survive contact.
* 🔴 **`--keep` may not be turned on to hit a number.** If an incremental build
  is the answer, it arrives with `P4a`'s `L2-6` re-measured and
  `notes/reproducible-build.md` updated in the same commit — or it does not
  arrive. **A faster loop bought by silently dropping a reproducibility claim is
  the worst trade available here.**
* **More than 11 segments** (8 猜 + the same 1.4× this board's only two
  comparable gates ran at) and what is left moves to `R5`'s preparation.

### ✅ Read one at a time on the way out, 2026-09-02

| | verdict |
|---|---|
| **D1** the loop that existed before this gate has a measured end-to-end number, stages separated, machine and human apart | 🟢 **met, `R4-0`.** 50.4–71.1 s machine, against a served turnaround of 1149 s on the seating it read. Four of its nine predictions were refuted and they are all still in `notes/dev-loop.md` §8 |
| **D2** a reset can be triggered without touching the power, from a committed script, and the prompt is reachable afterwards — N times in a row, N written first | 🟢 **met, `R4-2`, 21/21 with N written before the seating**, and three more inside the loop tool on 2026-09-02. `C-8`'s discriminator present every time |
| **D3** the loop, from a source edit to an assertion about what the board printed, runs unattended and reports a number | 🟡 **met in two halves that have never been one command, and this row says so rather than rounding up.** The bench half ran `S4`–`S7` with **no operator gap at all** and reported **34.74 s**; the desk half ran `S2`→`S3`→`S8` and reported **39.14 s**, with `A3` linking a build made at 12:29 to a boot the board produced at 12:15. 🔴 **The seam is `--skip S2,S3`, and until that morning it was not optional** — nothing carried `S2`'s staged tree into `S3`. Fixed, and the one stage still untested in a single command is *upload the image `S3` just assembled* |
| **D4** that number is under 90 s, or the gate closes with the number it reached and the reason recorded | 🟢 **met: 73.88 s, 16.1 s of margin** — 🔴 **and it is a sum of two runs, not a measured total.** ⚠️ It is *larger* than `R4-0`'s 50.4–71.1 s, which is the honest direction: `R4-0` did not count the reset, because then the reset was a hand on a power switch. Making it a stage cost **13.21 s**, and **≈24.4 s of the 34.74 s bench half is terminator budget** rather than board |

**Refutation condition** — *`D2` is refuted by the absence of `C-8`'s
discriminator; `D3` by a loop tool that cannot be made to fail.* 🟢 **Neither
fired, and the second one was tested rather than assumed**: the suite drives the
whole runner in `--mode replay` and a wrong id, a truncated boot and a missing
recipe each turn it red (`M1`/`M2`/`M3`), while `M0` requires it green
unmutated — because a harness that kills everything and a harness that tests
nothing print the same thing. 🔴 **And the discriminator's reverse is still a
separate claim**: it appeared, and that says a watchdog reset occurred, not that
the ESC window is reachable. Both were cells and both were read.

**Stop-loss, checked** — two seatings allowed for `D2`, **one spent**
(2026-09-01) plus a ride-along on 2026-09-02. Eleven segments allowed, **four
used**. 🔴 **`--keep` was not turned on**, and `R4-0` is why: it buys 3–5 % and
refuses to run with `--marks` at all, so the trade `P4a` forbade never had to be
made. The `D4` renegotiation clause never fired.

🔴 **What this gate leaves for `R5`, and both are measured rather than
suspected**: `--iterations > 1` is now **refused** — `S4` is a loader command
and iteration 1 ends with the loader gone — so *a loop that runs once* is what
exists, and `R5` is six drivers; and **70 % of the bench half is terminator
budget**, which is the largest single block of the BENCH half — ⚠️ **not of
the loop**, because the build is 35.96 s and larger, and the build side has
already been examined by `R4-0` and `notes/incremental-build.md`. Cutting it
needs the largest-inter-byte-silence distribution measured out of the
captures this project already holds, not a guess.
