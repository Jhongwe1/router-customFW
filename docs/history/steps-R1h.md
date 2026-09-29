# `PROGRESS.md` § `R1h`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 1463–1566, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R1h`'s step list — ✅ CLOSED 2026-08-29, on the tail of `R3`'s first seating

✅ **Closed 2026-08-29.** `R1h-3` ran on power cycle 1 of seating 5 and `R1h-4`
landed in the same commit. **ⓐ has a measurement** (16 KiB / 16 B / 2-way, with
both of 否證 ⓐ's controls firing in both directions), **ⓒ closes positive**
(four `cache` ops retire while `x ri` traps in the same run under the same
handler), **ⓑ is 未定 after one of the two seatings the stop-loss allows**
(`c-A` negative, and the payload's own interlock voided Group V rather than
reporting the voided cells as passes), and **ⓓ's second half has a reading**
(none of the three bits sticks, and the refutation condition did *not* fire, so
the reading carries information). No flash-write command was issued; the
flash-byte count is **unmeasured**, because no `FLR` bracket was run.
🔴 **The gate stayed open
across `R2` and the whole of `R3`'s desk work, which the re-cut of 2026-08-26
said was deliberate rather than stalled — and it was: what it was waiting for
was a power cycle it was always going to share.**

**Written 2026-08-26 on entering the gate, before any of it was done.** `R1h`
exists because `R1-gate` closed with three residuals and **an item with no owning
gate is a bug in this file's own list** — the same rule that caught `C-16` being
orphaned by `R0`. Budget **猜, uncalibrated: 4 segments** — 2 desk, 1 instrument,
1 bench, and **the bench segment is shared with `R3`'s seating rather than being
its own power cycle.**

🔴 **RE-CUT 2026-08-26, after the desk half was written.** The seating is at the
**tail of `R3`**, so `R1h`'s desk half and `R1h`'s bench half are separated by
the whole of `R2` and `R3` — and three of the five steps were written assuming
they were adjacent. **`R1h`'s desk work ends at `R1h-1`. `R1h-2`, `R1h-3` and
`R1h-4` move to `R3`'s seating preparation** and are marked ⏸ below.

**Why `R1h-2` could not stay where it was**: it produces *"the seating sheet
section, written into `RUNSHEET.md` **beside `R3`'s**"*, and `R3`'s section will
not exist for ~12 segments; its DoD (`check-predictions.py` passing on a block
written before the first capture) is a **bench-time** artefact and cannot be met
at the desk at all. A step whose DoD cannot be reached is not a step.

⚠️ **So `R1h` stays OPEN across `R2` and `R3`, and that is deliberate rather than
stalled.** Written down because the next reader of this file — including me in a
few months — will otherwise read a long-open gate as a stuck one. The gate still
owns ⓐ ⓑ ⓒ ⓓ; what moved is when its bench half is spent.

🔴 **And the ordering INSIDE that seating does not move, whatever the scheduling
does.** `probe3` runs **first**, before `R3`'s kernel. `R3`'s DoD is *my kernel
boots to a shell and pings* — and in that state the loader is gone, the DRAM is
gone, there is no `<RealTek>` prompt to type `J` into and no `DW` to recover the
result block. **"At the tail of `R3`" is when the seating happens, not the order
within it.**

**What `R1h` exists to settle**, so that closing it can be checked against
something:

| | question | `SPEC.md` |
|:-:|---|---|
| ⓐ | cache size, line size, associativity — **measured**, not read out of a build constant | `CPU-25` |
| ⓑ | does the D-cache allocate on read, and does anything on this core invalidate a clean line — **`R1-gate`'s decision ②** | `CPU-45` |
| ⓒ | does this core retire the MIPS-II `cache` instruction | `CPU-44` |
| ⓓ | write-through or write-back-without-write-allocate; and are `Status.IsC`/`SwC` implemented as bits | `CPU-19` 殘留 |

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| ~~**`R1h-0`**~~ ✅ | desk 1 | **DONE 2026-08-26 — `docs/probe3-cells.md`.** 🔴 **And writing it refuted two of the things this gate was standing on**: the walk's *mechanism* is I-side while the *prediction written for it* is D-side (so `probe3` carries two walks, the D-side one armed at run time by cell A); and **this part has a 16 KiB instruction scratchpad that is exactly the size of the predicted I-cache**, found by naming `CCTL 0x010`/`0x020` — `IMEM0FILL`/`IMEM0OFF`, four sources, one of them this unit's own kernel. `CPU-24` closes; `CPU-46` is new. *(as written on entering:)* **`probe3`'s cell table, with every expected value and refutation condition written before the cell.** The eviction walk for ⓐ; cells A–E for ⓑ and ⓓ; one `cache 0x11` and one `cache 0x10` for ⓒ | Every cell names what outcome would refute it, and **every expected value names the capture or the artefact it came from** — the failure that has already happened twice (`D2c`, `E10d`) | **Cell A's negative is uninterpretable on its own.** *Fresh* is consistent with no read-allocate, with the KSEG1 alias being snooped, and with the line having been evicted. It is interpretable only beside cell E, and only with `probe1`'s two-victims-far-apart trick against eviction |
| ~~**`R1h-1`**~~ ✅ | desk + instr 2 | **DONE 2026-08-27.** 🔴 **And the one thing it closed on was a label that turned out to be defended by a wrong reason.** `hazlint --isa` read primary opcode `0x13` as `COP1X (MIPS-IV)`; on this MIPS-I core it is COP3. The handoff's justification — *0x13 is COP1X from MIPS-II onward* — is wrong in both halves (量, binutils 2.42: `mfc3` assembles at `mips1` **and** `mips2`, is refused at `mips3`; `lwxc1` waits for `mips4`. 讀, MIPS IV Rev 3.2 A 8.3.4: COP3 is MIPS I and II, MIPS III removed it, MIPS IV reused the opcode). 🔴 **And the same paragraph stopped the fix from going where it was aimed**: COP3 is *optional and implementation-specific* at MIPS I, so ISA membership is not evidence the silicon executes it — and whether it does is `m-imem`/否證 M, still open. **Nothing came off the watch list.** `probe3` still reports 13 `--isa` hits; the eight are now `mfc3` at level `MIPS-I COP3`, each printed with its address and its decode. Three sites fixed (`isa_hit`, `reads`, `control_flow`), **and not one violation count on any artefact in this tree moved** — 量: `stage2.bin` 1474/646/0, probe0–3 all zero, before and after. So the deliverable is the controls: `hazlint` 10 → 12 (`K6d`, `K9`, and `K6c`'s two counts pinned instead of merely unequal), `test-hazlint.sh` 56 → **96**, `test-rlxprobe.sh` 195 → **202**, `M10`–`M14`. Three defects fell out sideways: the identical bad row in `tools/opcount.py`, a `ck` in `test-hazlint.sh` reading `[ -n "$STAGE2" ]`'s exit status instead of hazlint's (**could not fail here, could not pass on a runner**), and `cells.S` claiming `-march=mips1` refuses `mfc3` when 量 says it refuses only `cache` — comment corrected, payload untouched, rebuilt sha256 `1a0725c0…` identical. 🔴 **And then the whole change was put to five adversarial readers with every finding sent to a separate refuter — 11 of 25 survived, and four of them changed the substance**: the headline *no violation count moved* is false — the decompressed kernel goes **172 → 171（🔄 **2026-08-28：171 是錯的，正確是 168，走掉的是四個點位不是一個** —— 見本檔 Corrections 與 `tools/hazlint` 1.3 的版本註。⚠️ 而 172 與 168 都是 1.3 之前的**全檔**掃描，在 1.3 之下這個檔案要 `--allow-mips16` 才重現得出來）**, a false positive at `0x802BC490` where the old operand model read a sub-opcode selector as `$t7`; the strict delta's explanation carried the new rule's rejection count where the old one belonged (**69 of 97**, not 44); `notes/cache-model.md` claimed no word of the 97 has its low 11 bits zero and **nine do**, one of them a well-formed `bc3f` that is `K9`'s own fixture; and the identical mislabel was alive at **`0x33`/`0x3B`**, where `reads()` treated `swc3`'s coprocessor register as a general one — 量, that made the shipped tool **refuse a build** for a hazard that is not there. Three of the new controls were themselves too weak to catch a mutant and were strengthened. *(as recorded while in progress:)* Built: `cells.S` + `probe3.c`, through the `hazlint` gate (804 loads, 0 violations), running end to end under qemu (`qemu/2026-08-26/probe3.txt`, the first qemu capture this repository has committed). The three preconditions are all closed — build system, the three 未定 qemu columns, the capture. 🔴 **And the core vendor's datasheet, fetched the same day, refuted four things in the cell table** (`docs/probe3-cells.md` § 1.4): `c-E0`/`c-E2` would have refuted `CCTL 0x100` by an artefact of the running order, cell `c-G` is new, `w-line`'s void gate was at `+192` where 128 bytes is a legal line, and associativity stopped being sourceless. ✅ **The suite is done too**: 106 → **195 cases, 0 failed**, twelve mutations — six that need no emulator and six that run under qemu — plus a coverage table that **names the cells nothing covers and why**, because on this harness most cache readings are identical mutated and unmutated and a mutation whose predicted effect equals the baseline cannot fail. **Still open, and it is one thing**: `hazlint --isa` labels opcode `0x13` `COP1X (MIPS-IV)` where on a MIPS-I core it is **COP3**; fixing it moves `test-hazlint.sh`'s K6a/K6b/K6c control numbers, which have to be re-measured rather than re-guessed. *(as written on entering:)* **`probe3` itself**, under the `hazlint` gate, plus its qemu harness and one mutation per cell. 🔴 **Plus one deliverable the re-cut adds: a written rebuild-on-the-day procedure.** The binary will sit in the tree across `R2` and `R3` before it is seated, and this project has been bitten by exactly that — 量: `make P=probe2 payload RESULT_BASE=0x80A01000` printed `Nothing to be done` while the `probe2.bin` in the tree was a `0x80A00000` build. Empty the build directory, rebuild, record the `sha256`, and `rb=80a02000` is the stale-build check. **In the file, not in anyone's memory** | Runs to its own end under `qemu-system-mips`; **the mutation for each cell produces the failure that cell exists to detect**; the result block is recoverable with one `DW` after the payload's own watchdog reset | 🔴 **qemu will disagree with the device again, and that is the expected case.** `probe1`'s cell 1 came back FRESH on qemu and STALE on silicon. **A qemu run that looks like the device is the run to distrust**, and every cell needs its expected-under-qemu value written down separately from its expected-on-device value |
| ✅ **`R1h-2`** | desk ½, **at `R3`'s seating prep** | 🔄 **Closed 2026-08-29 with `R3-7`, which is the same step.** `RUNSHEET` §B5's card, its **eleven** corrections (§B5-c1…c12, and `c12` is the list of what the frozen block says that is now known to be wrong), and `bench/2026-08-30b/PREDICTIONS-B5-block1.md` — twelve cells, frozen, `0 of 12` at the desk because control `N2` fires on every capture that is still in the future. ⚠️ **`R1h-3`'s own block is NOT written**, and that is deliberate: `probe3` is power cycle 1 and its cells are `R1h-3`'s to predict. *(as written on entering:)* **The seating sheet section, written into `RUNSHEET.md` beside `R3`'s** — including **two separate uploads**, because the loader re-stages `0x80500000` on a watchdog reset and one power cycle cannot run two payloads without re-uploading | `tools/check-predictions.py` passes on a block written before the first capture | **The order.** `R3` is the expensive one and `probe3` is the cheap one; if `R3` boots and takes the board away, `probe3` has to have run first — or the seating buys one thing |
| ✅ **`R1h-3`**| bench 1, **the tail of `R3`** — 🔄 **desk half done 2026-08-29** | **The run**, on `R3`'s power cycle, **and `probe3` goes first within it**. 🔄 **The desk half was not in this row when it was written and it turned out to be half a segment of its own**: `bench/2026-08-30/PREDICTIONS-B5-block0.md`, thirteen cells, frozen, `0 of 13`, **and its §0 is the card** because `RUNSHEET` §B5's card excludes power cycle 1 in its own sentence. `P7` is spent — `probe3` rebuilt 2026-08-29, sha256 byte-identical to `R1h-1`'s. **What remains is the seating**  ✅ **收掉 2026-08-29 晚上。** ⓐ 有量測（16 KiB / 16 B / 2-way，兩個控制在兩個方向都成立）、ⓒ 正向收（四條 `cache` 全 retire，而 `x ri` 在同一次 run 陷入）、ⓑ 記為未定（`c-A` 否定，Group V 被 payload 自己的連鎖 void，停損允許第二次上機）、ⓓ 後半有讀數（三個位元都沒留住，而否證條件沒觸發）。🔄 **沒有發出任何 flash 寫入命令 —— 而位元組數未量，這次上機一個 `FLR` 都沒跑。** *（這一句原本寫「零 flash 位元組」，而 2026-08-30 的掃描第一遍漏掉了它 —— 同一個檔案在同一天把同一次上機的同一句話改對了兩次，就是沒改這一列。）* DoD 的「兩個通道一致」現在是算術：`tools/rbcheck.py` 三路全部 `C93E60B5`，三個 margin 字都是 `DEADC0DE`，十個控制成立。🔴 **而這一列預言的失敗模式今天沒有發生，另一種發生了**：它寫「桌面那半的失敗模式是引用沒動過的來源、抄沒重量的控制」，今天兩者都沒犯 —— 犯的是**照著一張沒有人真的跑過的卡片**，而那是在通電前讀 `argparse` 抓到的，不是在板邊| ⓐ ⓑ ⓒ each get a reading or an explicit 未定 with the reason; **zero flash bytes**; the result block agrees on both channels — 🔄 **and that last clause is now mechanical rather than an eyeball**: the UART's `sum=`, the seal word, and a re-sum of the recovered block **minus `0x10`** (for `progress(P_SEALED)`'s re-stamp) must all agree, a procedure demonstrated on `probe2`'s committed `H2g`/`H2a` with its negative control firing before it was written down | **A fault ends the seating and takes `R3` with it.** `probe3` runs before `R3`, and every cell writes its result before the next cell starts. 🔄 **And the desk half's own failure mode showed up twice**: a value predicted from a previous payload's reading without checking whether the source file had moved since (`install.changed`), and a control quoted from a frozen block without re-measuring it (`A-catch`'s missing negative). Both were caught by the adversarial pass, neither by re-reading the draft |
| ✅ **`R1h-4`**| desk ½, **after that seating** | **The write-up.** `CPU-25`, `CPU-44`, `CPU-45` and `CPU-19` 殘留 land; `C-6`'s remaining half closes or is restated again; `R1-gate`'s decision ② gets its answer in `docs/rlx-cache-and-cp0.md`  ✅ **收掉 2026-08-29，與上機同一個 commit。** `CPU-25`（大小/line/關聯度，量）、`CPU-44`（retire，正向）、`CPU-45`（未定，第一次上機）、`CPU-19` 殘留（② 收、① 跟著 `CPU-45` 走）全部落地，`docs/rlx-cache-and-cp0.md` § ② 給出的是**下一個實驗**而不是一段論證。`tools/spec-check.py` 九個控制先成立然後全綠。🔴 **而這一列預言的陷阱正是今天踩到的東西 —— 只是踩在別人腳上**：kernel 印的 `icache: 16kB/16B, dcache: 8kB/16B` 每一個數字都是 `bspcpu.h` 的 `#define`，是「穿著量測外衣的建置常數」的教科書例子。**走訪的數字與 kernel 的數字是兩個宣稱，而這份寫上去在它們一致的時候也這樣說了** —— 同一行還帶著 `dcache: 8kB`，而那個**完全沒有量測**| `tools/spec-check.py` clean; **decision ② names a measurement or names the next experiment**, and does not name an argument | The same trap `R1g-5` walked into: a geometry number that is a build constant wearing a measurement's clothes. **The walk's number and the kernel's number are two different claims** and the write-up says so even when they agree |

### Refutation condition, written now

> **否證 ⓐ** — the eviction walk's own negative control is a victim set smaller
> than any plausible cache: **every victim must come back STALE**. If a victim
> reports FRESH at a working-set size no cache could evict from, the walk is
> measuring something that is not capacity eviction and **the size number is
> void, not approximate**.

> **否證 ⓑ** — 🔴 **NARROWED 2026-08-26: cell E is cell A's positive control in
> only ONE of its two branches, and the form below is too strong.**
> `docs/probe3-cells.md` § 6.5 and `docs/rlx-cache-and-cp0.md` § ② own the full
> statement. If E shows a **held** store, the line was resident, read-allocate is
> real, and A's *fresh* can only mean the alias is snooped — eviction being
> excluded by the far-apart pair. **If E shows write-through, it says nothing
> about residency**: ⓓ is answered in passing and A's *fresh* stays a two-way
> disjunction whose survivors no observation through the alias can separate.
> 🔴 **And the dependency runs both ways**: E assumes its own middle load
> allocated, which is what A measures — so a negative A voids E too.
> *(Kept as written:)*
> **cell E is the positive control for cell A.** If E cannot produce
> a dirty line — that is, if a store to a line the CPU has just loaded is
> immediately visible uncached — then this core is write-through after all, cell
> A's *fresh* has one fewer explanation, and **ⓓ is answered in passing.** If E
> *does* produce one, then A's *fresh* would mean the alias is snooped, and that
> is a result about the alias rather than about the cache.

> **否證 ⓒ** — a `cache` instruction that neither retires nor traps (the payload
> hangs) refutes the handler, not the instruction. `probe3` writes its cell
> result **before** issuing the instruction, exactly as `probe1` does.

### Stop-loss, written now

| If | then |
|---|---|
| **Two seatings** and cell A still cannot be made to hold | `CPU-45` is recorded **未定**, and **`R6` carries the conservative cost**: rings *and* payload buffers in the uncached window, which is what the vendor's own driver does for the rings. The throughput number in `R6`'s DoD is then measured against that, and is not compared with anything |
| `cache 0x11` traps | **That is an answer, not a failure.** `CPU-44` closes negative, the D-invalidate candidates reduce to `CCTL 0x001`/`0x200`, and **this unit's own kernel becomes a puzzle worth its own row** — it contains 37 instructions its own silicon will not execute |
| The eviction walk returns a size that is not a power of two | Record **未定** rather than the number. A non-power-of-two is the walk measuring something else, and rounding it to the nearest plausible value is how a build constant gets laundered into a measurement |
| `R3` and `probe3` cannot both fit one seating | **`probe3` goes first.** It is the cheap one, and `R3` booting a kernel is what ends a seating |
