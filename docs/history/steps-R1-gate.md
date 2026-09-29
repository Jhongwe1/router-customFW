# `PROGRESS.md` § `R1-gate`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 1637–1783, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R1-gate`'s step list — closed 2026-08-26, kept as written

**Kept in place rather than deleted**, because the column *"where it is most
likely to be wrong"* is only worth anything if it can be read afterwards against
what actually went wrong. **Two of its five rows called it and two did not**:
`R1g-1` predicted in writing that a write-through D-cache would make cells 2 and
3 agree and that this would be *"unnecessary rather than wrong — a result, and it
has to be written as one"*, and that is what happened. `R1g-5`'s row said *"a
write-up is where a gate quietly widens its own claim"*, and the write-up found
two claims already widened. **What no row anticipated** is that the write-up would refute the gate's own reading of `probe1` — the
write-through sentence — and that the refutation would come from a directory
nobody had looked in.

**Written 2026-08-25 on entering the gate, before any of it was done**
(`plan/SESSIONS.md` §0b). `R1-gate` is `R1d` — the cache-management model, on
silicon — and `R1e` — the CP0 census. Budget **8 segments**: 4 desk, 2 bench,
2 instrument (`plan/router-rebuild-plan.md` §12.1). The steps below add to
**8½**, and the half over budget is `R1g-0`, whose question was not visible
until a payload was being designed against it.

**This list, and not `plan/DAY-ZERO.md`, is what "what do I do next at the desk"
means from here.** `DAY-ZERO` owns the instruments that had to exist before any
gate could run; a gate owns its own steps. That boundary is the one item 7
already drew — `hazlint` was `DAY-ZERO`'s, the hazard verdicts it enables are
`R1b`'s — and item 8 had never been cut along it.

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R1g-0`** ✅ **2026-08-25** | desk ½ | **What a fault costs.** A static read of this unit's own exception path: after `Undefined Exception happen.` and `cp0_cause=%X, cp0_epc=%X`, does control reach the `<RealTek>` prompt, spin, or reset? Is `Status.BEV` 0 or 1 while the loader runs? Does the loader re-install its vectors on a warm reset, or once from ROM? | Each of the three answered with an address, or recorded undetermined with the experiment that decides it | It may not be decidable statically — 🔄 *(that clause named the wrong table — `0x8040A5C0` is `BootStateEvent[3][8]`; the real one is `exception_handlers[32]` at `0x8040EB40`, and thirty of its thirty-two entries DO share a tail. The step's risk was still real, and it is left here as written rather than rewritten to look prescient.)* If it is undetermined, **every later step has to assume a fault costs one power cycle**, which is what puts `R1g-1` ahead of `R1g-2` |
| **`R1g-1`** ✅ **2026-08-25** | desk + instr 2 | **`probe1` — the cache-model discriminator, and the qemu harness.** Six cells, each writing a known instruction into RAM, executing it, and reporting which of two constants came back: ① no flush at all ② `CCTL = 0x002` alone (invalidate I) ③ the vendor's `0x200` then `0x002` (flush D, then invalidate I) ④ the `Status.IsC`/`SwC` path `c-r3k.c` uses and this bootcode never does ⑤ a store through KSEG1 with no flush ⑥ `r3k_cache_size()` reproduced, for I-size, D-size and line size (`CPU-25`). Every cell writes its result to a block at `0x80A00000` **before the next cell starts** | Builds under the `hazlint` gate; runs to its own end under `qemu-system-mips`; the result block is recoverable with one `DW 80A00000` after the payload's watchdog reset, so a hang costs the cells after it and not the cells before it | **Cell ① is the negative control and it is the one that can quietly not work.** If the primed line is evicted between priming and the rewrite, ① reports *not stale* for a reason that has nothing to do with the cache model, and every later cell then looks like a pass. Second: `mtc0 $t,$20` is Lexra's, and three of the six command values `notes/cache-model.md` lists have exactly one source — if it faults, `R1g-0`'s answer decides what that costs. Third: a write-through D-cache makes ② and ③ agree, so the vendor's D-then-I sequence would be **unnecessary rather than wrong** — a result, and it has to be written as one |
| **`R1g-2`** ✅ **2026-08-25** | desk + instr 2 | **`probe2` — the exception handler and the CP0 census.** Install handlers at `0x80000080` **and** `0x80000000` through KSEG1, flushed by whichever method `R1g-1` measured (a build knob, not a constant); then read CP0 registers 0–31 across selects 0–7 and record each as *read / trapped / read as zero*. `Count`(9) and `Compare`(11) read twice around a loop of known length — `F50b`, and it decides three things at once | The full table comes out under qemu; **removing the reserved-encoding control makes the payload refuse to emit a table at all**; the handler's installation is self-checking, so *the handler did not take* and *the instruction is absent* are different observations | `Status.BEV` at the prompt is `CPU-27` and it is **blank** — if it is 1 the vectors are in boot ROM and `0x80000080` is the wrong address entirely. 🔴 **And the address itself was wrong in four files until 2026-08-25**: `0x80000180` is MIPS32's; this core is R3000-class, so `0x80000000` is the UTLB refill vector and `0x80000080` is the general one, and a handler at `0x180` would have looked installed and changed nothing. The payload has to read `BEV` and refuse rather than install blind. Second: overwriting `0x80000180` may leave the loader without a handler after the watchdog reset — `R1g-0` question 4. Third: reading a CP0 register that does not exist is architecturally UNDEFINED, not a trap; a core that returns stale bus data would make *read as zero* and *not implemented* indistinguishable, and the census has to say which of the three it can actually tell apart |
| **`R1g-3`** ✅ **2026-08-26** | desk 1 | **The seating sheet.** A new `RUNSHEET.md` section: every cell's expected value and refutation condition written **before** power, the do-not-type list, and the ride-alongs that cost nothing once the board is up — `C-17`'s `J BFC00000` then `DW 81000400 16`, `NET-13`'s four cable moves with the jack in the `--out` filename, and `CLK-08b` on the 2 ms ESC grid | `tools/check-predictions.py` passes on a prediction block written before the first capture, as it did for all 18 blocks of seating 2 | The failure mode has already happened twice and both times it was an expected value derived from the wrong power cycle (`D2c`) or from the very map the cell was supposed to test (`E10d`). **Every expected value has to name the capture it came from** 🔴 **2026-09-16 (`R1z-2`), and this is why the mark above is dated the 26th and not the 25th**: `LOG.md:3169` is headed *`R1g-3` 的完成定義其實沒滿足* — the DoD was found UNMET mid-segment (`bench/2026-08-26/` did not exist and `B4` had no `PREDICTIONS-*.md` at all), and then met by `PREDICTIONS-b4-block0.md` alone: nine cells, four controls, nine correct *no capture* reports. **Blocks 1–3 were deliberately written at the bench** because each was conditional on the previous cell’s reading, and the reason is recorded rather than excused — *替一個跑不了的 cell 寫 block，是讓它為錯的理由失敗* |
| **`R1g-4a`** ✅ | bench 1 | 🔴 **DONE 2026-08-25, and its DoD was met on both halves.** `probe1`'s block came back on the UART **and** from `0x80A00000`, and the two agree **104/104 row words** with a one-word shift as the negative control; cell 1 read against cell 5 on the `ma` column returned `240222b2`/`240222b2` — **the D-cache is write-through**, which is the write-back-vs-write-through measurement the DoD asked for. The known defect carried in knowingly **fired exactly where it was predicted to**: cell 4 is `07` CORRUPT on both victims, `rlx_isc_inv`'s `sb $0` reached DRAM, and rows 0–3 were banked first, so the negative control and the discriminator survived it. `RUNSHEET.md` § Results B4. *(Original text:)* **The first seating, and it stops before `probe2`.** `H0`'s six free reads, `probe1`, read back, then the three ride-alongs. 🔄 **Split from `R1g-4` on 2026-08-25** after `probe1.c`/`probe2.c` were audited — `docs/rlxprobe-audit-2026-08-25.md`. `rlx_reset` hands the prompt back by itself, so ending here spends nothing extra this visit | `probe1`'s result block recovered from the UART **and** from `0x80A00000`, and the two agree; cell 1 read against cell 5 on the `ma` column, which is a `write-back`-vs-`write-through` measurement in its own right | `MEM-15`: this DRAM keeps its **contents** across a short power-off, so a result block from the previous payload can be read as this one's. Every block needs a per-build nonce and a per-cell written flag, and the region must be poisoned on entry — otherwise *cell 5 never ran* and *cell 5 returned 0* are the same bytes. 🆕 **And one known defect is carried in knowingly**: `CELLS[]` runs cell 4 — the only cell with a demonstrated kill — third. Carried because rows 0–3 are banked first and because `rlx_isc_inv` enters with a safe `$a0`, so a fault there **prints**. That is the exact property `rlx_do_break` lacks, and it is the line the split was decided on |
| **`R1g-4b`** ✅ | desk 1 + bench 1 | 🔴 **DONE 2026-08-25b, and its DoD was met on all three legs.** `probe2`'s block came back on the UART **and** from `0x80A01000`, and the two agree on all 40 header words, on the seal and on every spot-checked census row. **The `break` control failed visibly or not at all — and it did not fail**: `install.bad=0`, `break.count=1`, `cause=00000024`, `epc=80500270`. And `p2a`/`p2b` no longer exist as a pair. 🔴 **The one thing the DoD did not ask for and should have**: a repeatability control. The attempt at one booted the vendor kernel, because **the loader re-stages `0x80500000` on a watchdog reset** — a structural fact about every future seating, now recorded. `RUNSHEET.md` § Results B4 `R1g-4b`. *(Original text:)* **`probe2`, after it is fixed.** The must-fix list is `docs/rlxprobe-audit-2026-08-25.md` § Must-fix: `SAFE_A0` on `rlx_do_break`; a vector read-back in `install_handler`; `$v0`/`$8`/`$15` sentinels and the `exc_rec` bracket on `rlx_count_delta`; `V_DIRTY` in `probe1`. ~24 lines, and **the re-validation is the cost, not the lines** — qemu, the 66-case suite, and a mutation per fix, because a suite that cannot tell the patched payload from the shipped one is `hazlint` 1.0's finding 6 | `probe2`'s block recovered on both channels; **the `break` control fails visibly or not at all**; and `p2a`/`p2b` no longer exist as a pair, because `R1g-4a`'s `H1` decided the flush | **This costs one additional planned power cycle and that is the whole price of the split.** What it buys: `H0b` measures `exception_handlers[9]` — the single unverified link in the `SAFE_A0` finding — `H0c` measures what a kuseg fault lands on, `H0a3` measures whether the vector page is coherent uncached, and `H1` collapses two binaries into one. **The fix gets written against measured values instead of read ones** |
| **`R1g-5`** ✅ | desk 1 | 🔴 **DONE 2026-08-26, and its own risk column called it.** `docs/rlx-cache-and-cp0.md` written; `CPU-19` upgraded to **量** — and the upgrade is not the one this row anticipated: what became measured is the **classification** (`Config.M = 0`, the select field ignored, `rfe` balancing the R3000 stack, `Random` inside 0…31 — four routes, no TLB probe), not only the mechanism. `C-6`'s residual restated and **re-homed to `R1h`**, because both of its owning gates closed under it. 🔴 **The row said *"a write-up is where a gate quietly widens its own claim"*, and the write-up found two claims already widened**: *"the D-cache is write-through"* (`probe1`'s two cells both stored to a line the D-cache did not hold, so write-through and write-back-without-write-allocate give the same reading — and both GPL drops' `boards/rtl8196e` say `CONFIG_ARCH_CACHE_WBC=y`), and *"no `cache` instruction in vendor code that executes"* (**37 of them in this unit's own kernel**, D side only, `0x8000CA40`–`0x8000CD4C` — the scan that returned zero had been run on `stage2.bin` alone). Decision ① is **narrowed, not answered**: the instruction side is 量, the flash-read-back side is decision ②'s question. `SPEC.md` `CPU-19`/`CPU-20`–`CPU-24`/`CPU-25`/`CPU-43`–`CPU-45`; `tools/spec-check.py` gained **C8** and a ninth mutation after `CPU-19` turned out to have been outside two checks since the day it was written. *(Original text:)* **The write-up.** `docs/rlx-cache-and-cp0.md`; `SPEC.md` `CPU-04`, `CPU-25`, `CPU-27`, the `CCTL` command rows, `CPU-19` upgraded from *read* to *measured*; `C-6` closes or its residual is restated; and the four downstream decisions this gate exists to unblock are recorded with the reading that decided each | `tools/spec-check.py` clean, and each of the four decisions names a measurement rather than an argument. 🔴 **Met on three of four, and the fourth is recorded as not met**: decision ② names **no** measurement, because there is none — it names the experiment instead, which is this project's own stated form for *uncertain* (`CLAUDE.md`). **The gate closed on that, deliberately, and the discrepancy is written into the closing statement rather than smoothed over** | A write-up is where a gate quietly widens its own claim. `R1d` measures **which flush works on this core**; it does not measure why, and it licenses no statement about the Lexra family |

**The four decisions `R1-gate` exists to unblock**, so that closing it can be
checked against something: ① where `R5b`'s MTD driver has to flush, ② whether
`R6`'s descriptor rings need an uncached window or a flush, ③ whether the
exception handler `R1a` needs can live at `0x80000080`, ④ whether `R5-0`'s SoC
timer driver is a **prerequisite** or a bonus (`F50b` — if `Count`/`Compare` are
absent it is a prerequisite, and `R1c`'s timing method loses its first route).

🔴 **How they came out, 2026-08-26. Three named a measurement; one did not, and
the gate closed anyway — on purpose.** The full statement with its evidence is
`docs/rlx-cache-and-cp0.md`; this is the scoreboard.

| | verdict | what decided it |
|:-:|---|---|
| ① | 🔄 **answered for the instruction side, and narrowed there** | `CCTL 0x002` alone, 量 twice on independent ground (`probe1` cells 2/3/6; `probe2`'s handler install through KSEG1). **An MTD driver also reads flash back**, and a window whose contents changed underneath the D-cache is decision ②'s question — so half of ① travels with ② |
| ② | 🔴 **未答** | Nothing. `R1d` measured the CPU→memory direction **for a write miss only**, and nothing at all in the memory→CPU direction. `R1h` cells A–E decide it |
| ③ | 🔴 **yes** | `Status = 1000fc00`, bit 22 = 0; `break.count = 1`, `cause = 00000024`, `epc = 80500270`, and the handler restored with `restore.mismatch = 0` |
| ④ | 🔴 **prerequisite** | row `0x48` = `00000000` `S_ZERO`, `count.delta = 0` over 100,000 iterations, and `nowrite = 0` over 256 rows is what makes that zero a real zero |

**Why closing with ② open is the right move rather than the lenient one.** What
② is missing is not more analysis of `R1d`'s captures — it is **a payload that
does not exist and a seating that is not scheduled until `R3`**. A gate held open
waiting for a future seating is a backlog item wearing a gate's name; `R1h` gives
② an owner, a payload, a DoD and a stop-loss. **And the price of closing is paid
in ①**: it is recorded as narrowed rather than answered, which is the sentence a
driver author needs and the one a clean-looking gate would have lost.

### Preconditions — checked, and two are not satisfied

| | |
|---|---|
| ✅ | **`R0` closed**, so the transport is proved: `rescue` + `put` + `J`, with `AUTOBURN` measured `00000000` at the burn path's own instruction *during* the transfers |
| ✅ | **`hazlint` 1.1 exists and gates the build** — `probe0.bin` depends on `probe0.gate`, which does not exist unless `hazlint` exited 0 |
| ✅ | **The `rlxprobe` chassis exists** — segment 0, 23/23, and `-march=mips1 -msoft-float` is the measured build line for gcc 12.4.0 (`TC-06`) |
| ✅ | **`qemu-system-mips` 8.2.2 is installed** |
| 🔄 | **What a fault costs — answered statically by `R1g-0`, and three of its inputs are now measured.** `do_reserved` at `0x80400BE8` prints twice and branches to itself with `IEc` 0 and the watchdog unarmed, so **a fault the loader does not handle costs one power cycle**. 2026-08-25 at the bench: `exception_handlers` **is** at `0x8040EB40` with thirty of thirty-two entries `= 80400BE8`, **including index 9** (`H0b`); the general vector at `0x80000080` holds the dispatcher, identically through the cached and uncached windows (`H0a`/`H0a2`/`H0a3`); and the UTLB refill vector holds `5A5AA5A5`, opcode 22 `BLEZL` (`H0c`) — **not `j` and not `jal`**, so `cache.S`'s no-demonstrated-brick-path argument holds by measurement. **`probe2` is still designed for *a fault ends the seating*, and that is now a cost that has been priced rather than assumed.** ⚠️ Not measured: whether the core **fetches** from `0x80000080`. That is `Status.BEV` |
| 🔄 | **`Status.BEV` at the prompt: upgraded from *blank* to *讀, one source*, at the desk on 2026-08-25, and the evidence was already in this repository.** `docs/loader-phy-and-switch.md` §2's interrupt-layer table has carried *"`Status.IM[7:2]` unmasked, **`BEV` cleared** — set at `0x80406694`, called from `0x80408634`, on the boot path, **never re-masked**"* since 2026-08-23, while `SPEC.md` `CPU-27` and this table both said *not established*. **A fact with one owner that never reached the two files that depend on it** — the same defect class as `43ec0e0`. It is *讀* and not *量*: the tick counter advancing at 100.0018 Hz (`REG-25`, 量) proves an interrupt is being **serviced**, but a `BEV=1` machine servicing it through the ROM vector produces the same reading, so the chain does not isolate `BEV`. **No loader command can read CP0**, so the measurement needs a payload — and with `H2` deferred to `R1g-4b`, `CPU-27` stays *讀* through `R1g-4a`. `probe2` reads it itself and refuses to install if it is not 0, which is the refutation condition |

### Carried forward owned by this gate

🔴 **`C-6` → `R1d`, `R1e` — and both of its owning gates closed under it, which by
this list's own rule makes it the second orphan.** **Re-homed to `R1h`,
2026-08-26**, the same day `R1-gate` closed. *(The precedent is `C-16` below. A
list whose rule is "an item with no owning gate is a bug" has to treat "an item
whose gate closed without it" the same way — and this is the first time that rule
was applied on the day rather than noticed a gate later.)*

**Closed on silicon**: the flush recipe for the **instruction** side (`CCTL
0x002` alone), `Status.IsC` not isolating, and CP0 20's read side — it reads `0`
for real, because `nowrite = 0` over 256 rows proves `mfc0` always writes `rt`
(`CPU-39`), so **CP0 20 is a write-only command register that reads back zero**.

🆕 **Closed at the desk on 2026-08-26, and not by the route this row named**:
**four of the seven CCTL commands now have a name from a source that states
it** — `arch/rlx/mm/cache-rlx.c` gives `0x1 DInval`, `0x2 IInval`, `0x100 DWB`,
`0x200 DWB_Inval` — and `0x100` is a command this repository had no row for at
all. This row used to say the residual needed *"R1e or a `devmem`-class read"*.
**`R1e` ran and could not do it**: the census reads CP0 20 and it reads zero, and
**a read side that is always zero cannot name a write side.** The route that
worked was a directory nobody had opened.

🔴 **Still open, itemised, and each with an owner** — all of them `R1h`:
~~`CCTL 0x010`/`0x020`, unnamed in every source~~ 🔴 **CLOSED 2026-08-26 at the desk**: `0x010 = IMEM0FILL`, `0x020 = IMEM0OFF`, four sources, and `probe3` writes `0x020` as the I-MEM discriminator. **Residual is `CPU-24` 殘留** — bits 6/7 and `0x400`/`0x800`, where the sources **contradict each other** rather than being silent. *(as written:)* (`CPU-24`, **and only its
documentary half**: writing an unnamed command to a cache controller is
declined); cache size / line size / associativity (`CPU-25`, which now has a
**prediction to refute** rather than a blank); the **D side of coherence**
(`CPU-45` — this is `R1-gate`'s decision ②); whether the `cache` instruction
retires on this silicon (`CPU-44`); and write-through versus
write-back-without-write-allocate, together with whether `Status.IsC`/`SwC` exist
as bits (`CPU-19` 殘留). *(Original text:)* Answered at the desk as the R3000
model; its residual
is what this gate measures — `CCTL` commands `0x010` and `0x020` have one source
each and no name in any source, and cache size, line size and associativity are
unknown. `CPU-25` and `CPU-27` are the `SPEC.md` blanks that close with it, and
`CPU-04` closes with `R1e`.

🔴 **And one item is orphaned, which is a defect in that list by its own rule.**
`C-16` — *what actually copies flash `0x060010` into RAM at `0x80500000`* — names
`R0` as its owning gate, and **`R0` closed on 2026-08-24 with `C-16` still open**.
A list whose rule is *an item with no owning gate is a bug* has to treat *an item
whose gate closed without it* the same way.

### Refutation condition, verbatim

> **否證** — 任一負控制沒觸發 → 整張表作廢。**這是唯一能讓這張表變垃圾的失敗，
> 所以它是強制的** (`plan/router-rebuild-plan.md` §6-R1 整體驗收)

> **否證** — 兩個來源不一致 → 記「未確定」，並且**在裸機上用一個自我修改的實驗
> 判決**（寫一條指令進 RAM，刷，跳進去，看執行到的是新的還是舊的） (§6-R1d)

For this gate that reads: **if `probe1` cell ① reports that the freshly written
instruction executes with no flush at all, the other five cells decide nothing**,
because a test that passes without the treatment has not tested the treatment.
The gate does not then close with *"any flush works"*; it closes with *cell ① did
not hold* and a redesign.

### Stop-loss, written now

**Written before the work, because a stop-loss written after three segments have
been spent is a stop-loss nobody applies.**

| If | then |
|---|---|
| **Two seatings** pass and `probe1` cell ① still cannot be made to hold | `R1d` is recorded **未定**. `R5b` and `R6` then carry the conservative cost — flush D-then-I through `CCTL` **and** take the `Status.IsC` path — and the gate closes on that, not on a model |
| `Status.BEV` reads 1, or the handler cannot be installed | The census falls back to the registers that can be read without one, the rest is **未定**, and `F50b` resolves against `Count`/`Compare` — i.e. **`R5-0`'s timer driver becomes a prerequisite**, which is a decision and not a gap |
| `mtc0 $t,$20` faults | `CCTL` is recorded as not reachable from a payload in this state, the `Status.IsC` path becomes the only route, and `notes/cache-model.md`'s two-mechanism reading is **half refuted on silicon** — which is worth more than the gate's own answer |
| Three seatings spent with none of the four downstream decisions settled | Stop. `R1-gate` is not blocking `R3` — the v6 ladder already says so — and the honest move is to run `R3` on the vendor's own cache handling and come back |

**And the gate-crossing rule applies on the way out** (§18.3): one entry in
`study/weekly-results.md` — a one-line version, three claims that stand each with
its evidence, and **what this gate did not prove**. Two consecutive entries whose
*did not prove* is the same thing make that thing the next gate.
