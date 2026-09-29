# `PROGRESS.md` § `R1-pub + R2c`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 452–680, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R1-pub + R2c`'s step list — ✅ CLOSED 2026-09-16, in 20 segments (58th–77th)

**Opened 2026-09-11** on the owner's decision, in the same segment `R5` closed.
**Est. 20 段** — the plan's 小計 (12 desk + 4 bench + 4 instrument). ⚠️ **The
gate board's column says 14**, which is the two-owner defect the paragraphs
under that board describe; the calibration there is against the plan's, so this
row is too. 🟢 **Calibrated for the first time**: nine closed gates run at
**0.33×–1.38×** of the plan, median **0.833×**, so the band here is **7–28
段** with a median of **17**. That is a band and not an estimate, and it is
written down that way because a single number here would be the fourth thing
this project has learned not to publish about this column. 🟢 **量 2026-09-16,
on closing: 20 段** — the 58th, in which `R5` closed and this gate opened,
through the 77th. **1.00× the plan's 20**, 1.43× the gate board's 14, inside the
band and above its median of 17. ⚠️ **The band did not predict it; it contained
it**, which is all a band claims.

### What this gate inherits, with its marks

| | | mark |
|---|---|---|
| The load delay slot is **architecturally exposed** on this core, measured on the device rather than assumed | `SPEC.md` `CPU-*`, `F46` | 量 |
| `PRId` = `0x0000CD01`, so the core is **`RLX4181` revision 1** and `RLX5281` is positively excluded | `CLAUDE.md` Never-table, `notes/vendor-kernel-isa.md` §5 | 量 ＋ 讀 |
| CP0 `Count`(9) and `Compare`(11) are **not implemented on this die** — which is why `R1c`'s timing method cannot be CP0 `Count` and has to be the SoC timer | `SPEC.md` `CPU-42` | 量 |
| The vendor kernel **emulates `ll`/`sc`** and treats `sync` as a no-op, and has **no FPU emulator at all** — `arch/rlx` has no `math-emu` and `do_cpu` gives `SIGILL` for any coprocessor but 0 | `SPEC.md` `CPU-47`, `R2d` | 讀 |
| `mflxc0`/`mtlxc0` assemble at `rlx4181`/`rlx4281`/`rlx5181`/`lx5280`/`rlx5281` and are **rejected** at `lx4180` and at `mips32`; as built they are `0x40620000`/`0x40e20000`, **not** `mfc3` | `docs/interrupt-map.md` § 1.1 | 量 |
| **CP3 is reachable on this part** where the emulator says every `mfc3` traps | seating 8, `probe3` | 量 |
| I-cache **16 KiB, 16-byte lines, 2-way**, measured by experiment and confirmed a second way by the shape of the eviction walk's victims | `SPEC.md` `CPU-25`, seating 8 | 量 |
| A bare-metal payload runs on this part and returns a report over the console — `probe1`, `probe2`, `probe3`, three generations | `tools/rlxprobe/` | 量 |
| The SoC timer is a driver of mine now, so **`R1c`'s ruler exists** where `R1` was originally written assuming CP0 `Count` | `R5`, `SPEC.md` `CLK-27` | 量 |

### 🔴 Three things this gate has to settle before a payload is written

**① The gate's whole claim is *this is not in public data*, and that has to be
established the way `R5-0` established the blind-write premise — by enumerating
what is already here, dated, before anything new is measured.** `probe1`,
`probe2` and `probe3` have run; some `R1a`/`R1b` rows are already closed and
some hazard rows are already answered. **A census that re-measures what
`SPEC.md` already holds and presents the total as new work is the résumé
failure this project keeps naming.** `R1-pub-0` writes that list.

**② `R1-pub` needs BARE METAL, and bare metal now competes with a board that
boots my firmware.** Every seating from 11 to 20 has been Linux. A bare-metal
payload means `J` to a `rlxprobe` image and no kernel, so the two cannot share
a boot — they can share a *seating*, and that is a scheduling decision that has
to be made in writing rather than discovered at the bench. 🟢 Two things ride
these seatings and both are already named: **`CPU-45`**, which the operating
clause has pointed at since five entries, and **the loop's `S2` → `S7` seam**,
which it named for the first time at eight and which `notes/dev-loop.md` § 10.6
measured as needing **no additional power cycle**.

**③ The negative control is not optional here and the plan says so in the
strongest terms it uses anywhere**: *a reserved opcode must trap, and every
hazard test must be shown able to produce the wrong answer; any negative
control that does not fire voids the whole table.* That is the same rule as
`CLAUDE.md`'s *a tool reporting 0 is making a claim*, applied to a census whose
entire output is a column of zeros and ones. **It is written into the step
table as a step, not as a habit.**

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R1-pub-0`** ✅ **2026-09-12** | desk 1 | **What is already measured, dated, before anything new is.** Every `R1a` instruction row and every `R1b` hazard row this repository already holds, with its `SPEC.md` id, the seating it came from and its mark; plus the scheduling decision for ② and the timing method for `R1c` now that `CLK-27` exists | The list is committed **before** any payload source exists, so its ordering is checkable by `git log` the way `docs/blind-write-ledger.md` § 1 is. ② and ③ each get a decision, not a deferral | **That it reads as an excuse rather than a boundary** — if most rows come back already-measured, the honest output is that this gate is smaller than 20 段 and saying so |
| **`R1-pub-0b`** ✅ **2026-09-13** | desk 1 | **`R2c`'s prior art, the same shape as `R1-pub-0`'s.** Every toolchain row this repository already holds — `SPEC.md` § 14's `TC-15`, `TC-19`, `TC-22`, `TC-23` and the rest — with its mark, the artefact it was read on, and whether it is a statement about a toolchain or about the die. The population derived from an instrument, not chosen | The list is committed **before** `R1-pub-6` starts, and it says out loud whether `R2c` is smaller than the plan's 2 段 | **That there is no instrument to derive the population from.** `R1-pub-0` had `hazlint` and `isa-probe.sh`; the toolchain axis may have nothing equivalent, and if so the population is declared and the declaration is the deliverable |
| **`R1-pub-1`** ✅ **2026-09-13** | desk 2 ✅ + instr 1 ✅ | **`R1a`'s payload.** One row per instruction, each carrying an operand whose correct answer is a single computable constant, and a **three-way** verdict: traps / does not trap and right / **does not trap and WRONG** | It builds, `hazlint` is clean over it, and every row's expected constant is derived at the desk and printed beside the reading rather than compared in the payload | **The third cell.** *Does not trap but computes the wrong answer* is the row that matters and the easiest to lose, because a payload that compares in-place reports a boolean and throws the value away |
| **`R1-pub-2`** ✅ **2026-09-13** | desk 1 of 2 ✅ —— 🔴 **預算格，不是進度格**：`LOG.md:25432` 寫「用掉 1 段，預算 2 段」，而第七十六段收工把它讀成了「兩段做完一段」，在 § Now 發明了一個不存在的步驟 | **`R1b`'s payload.** Behavioural hazard tests: each computes a value that differs under interlock and without, never a signal test | Each test is shown, at the desk, to be *able* to produce the wrong answer — the positive control ③ demands — and *not measurable* is a legal recorded outcome | **A hazard test that the compiler has already fixed.** `-O` may insert the very `nop` the test exists to detect; the payload has to be read as built, not as written |
| **`R1-pub-3`** ✅ **2026-09-16** | bench **2 of 2** ✅ | **The run.** Both payloads on one seating, sharing it with `CPU-45` and with the loop seam 🟢 **2026-09-16(seating 24):第二次也是最後一次,停損用完而沒有超支。** slot 2 兩個定義**一顆 payload 都滿足**:Group L 在 stage 2b 給出膝點與判別(`CPU-69`),Group C 在 stage 6 第四次讀負、五格 void —— **而 `CPU-45` 由 A–B–A 從時間側答掉**(`CPU-70`)。`check-predictions` **11 of 11**,三次 `uc1` 開機各 9 個斷言,`probe3` 跑兩次。🔴 卡片 § 5.5 的停止條件開火而葉子兩條路都驗證,見 `CPU-72` 與 `bench/2026-09-16/CORRECTIONS-block22.md` § 2 | Every row returns a verdict or an explicit *not measurable*; the reserved-opcode control fires; every hazard test's own control fires 🔴 **2026-09-16（第七十七段）：前兩條成立，第三條不成立 —— 逐列控制 21 of 24**。三個 `cp0` 列的 `ctl` 沒開火，那三列 VOID、`D3` 允許，而條款寫的是 *every*；而**該說出這件事的儀器只看 26 個宣告控制裡的 2 個**，所以這個問題從來沒被問過。兩邊都在這一段修了，**條款仍然不成立 —— 只是現在量得到**。`SPEC.md` `FW-76` | **That it needs a second seating** — three payloads and two riders on one power cycle is the most this project has ever asked of one |
| **`R1-pub-4`** ✅ **2026-09-16** | desk 2 + bench ½ | **`R1c`.** The same table as a Linux userspace program under the **vendor** kernel (SIGILL handler ＋ `setjmp`), and the two-column diff that is the emulation surface 🟢 **2026-09-16(第七十六段,seating 24):`4b` 跑完了,而 `E1`／`E2`／`E3`／`E5`／`E6`／`E7` 全過。** 四列定價,兩列是數字兩列是界:`sync` **988.6 / 989.5 ns**、`lwu2` **915.6 / 915.4 ns**(兩者跨獨立開機重現到 0.1 %)、`ll` 原生 +2 週期、`sc` 正負號翻轉所以是零。**`E3` 超額達成** —— 四列四 twin 都在兩次開機上,每次開機自己的 rescue／upload／`J`。🔴 **兩個條款本身有缺陷**:`E5` 差一(13/64 個 rung「失敗」而每一個都恰好差 1,允許之後 0/64),`E4` 的門檻坐在雜訊裡(boot 1 失敗 `sw`、boot 2 失敗 `ll`)。`SPEC.md` `FW-73`。🔴 **`docs/rlx-isa.md` § 8.2 否證**,`CPU-74`。擁有者:`docs/emulation-surface.md` | Both columns exist for every row, and each difference is named as an emulation-surface entry with its cost measured against the SoC timer 🔄 **2026-09-14（第六十九段）：`R1C-1` 裁決完成，這一步分成兩半而步號不增**：**4a** = D-diff（45 列、不需要時鐘），**4b** = D-cost（約 4 列）。兩半都跑在 rlxfw 自己的映像上（`O1`），尺是 § 9 的 ③。本欄「跟 **vendor** kernel」這個措辭被**取代**而不是刪掉 —— 取代成一句量過的話，逐字在 `docs/isa-prior-art.md` § 9.3。🆕 **2026-09-15(第七十一段):`4a` 的擁有者檔開了 —— `docs/emulation-surface.md`**,帶結構、母體與四個被下掉的決定(45 列不縮成 39、`jalx` 一格明寫 EXCLUDED、五個未對齊指令的母體缺口單獨宣告、不去占 `R1-pub-7` 的 `docs/rlx-isa.md`)。🔴 **而同一次量到兩件事**:六個 `r1b` 危害列在 trap/no-trap 的詞彙裡**沒有格子可填**,而 `45` 這個數字一直被引用而沒有人注意到;以及模擬面上八個指令裡**只有三個有母體列**(`ll`／`sc`／`sync` 有,`lh`／`lhu`／`lw`／`sh`／`sw` 五個都沒有,而且依 `docs/isa-prior-art.md` §0 的收錄規則**不能有**)—— 那是 `R1-pub-0` 的母體缺陷,在這裡宣告而不在這裡修  🔄 **2026-09-15(第七十二段):`4a` 的欄②不再缺儀器。** `config/rlxfw-user/isaprobe/uprobe.c` 連 `tools/rlxprobe/cells4.S` **逐位元組**,所以兩欄是同一批 `.word` 在兩個特權層級,而不是兩張碰巧一致的表;`tools/isapay.py verdict --arm user --elf` 是桌面那一半,含 C2 —— 每個 trap 列的出錯 PC 必須等於該列自己的 `_w` 符號位址 ——正負兩個方向都在 qemu 擷取上驗過。工具鏈用 `TC-05` 既有的判準量出來(`TC-57`),映像 `up1` 建好且 `uprobe` 在裡面,三個獨立證據。~~**仍然沒有任何一列在矽片上跑過。**~~ 🟢 **2026-09-15(第七十三段,seating 23,一次電源循環):`4a` 的量測半收了 —— 75 個 payload 列全部跑過,總結 `RAN 12, RIGHT 16, TRAPS 46, WRONG 1`,與凍結卡片 `9874012` §6.3 逐字相同。`sync` 讀 `RAN`,所以模擬面在這顆上可見;`ll`/`sc` 不可見;`cache`×4 與 `mflxc0` 是特權假象。`SPEC.md` `CPU-64`。** ✅ **2026-09-15(第七十四段,桌面):`4a` 的寫上去收了。** `docs/emulation-surface.md` 385 → 483 行:欄②表頭從 `predicted` 改成 `量 from user mode, C2-UP.log`,**39 個格子一個位元組都沒動**(md5 相同);摘要那一行換成逐列導出(37 個有 payload 列的 census 列裡 34 列一致,`sync` 是唯一模擬面列);補上欄②的觀測界線(儀器讀訊號不讀 `Cause`)與收尾的「還沒建立什麼」一節。🔴 **而寫的時候拓到 §4 自己的缺陷**:seating 那次編輯把否證條件**刪掉**而不是劃掉,同一節卻寫著「原樣留在上面」,`SPEC.md` `CPU-64` 與 `docs/rlx-isa.md` 也都照抄了 —— **三個檔案都斷言它,沒有一個對過頁面**;已按 `cbd1d0d` 原文還原,而五支 `.md` 閘門在它是假的三個 commit 期間全部是綠的。⚠️ **`4b`(`D-cost`)整個沒開。** `notes/userspace-probe.md`| **The ruler.** `CPU-42` killed CP0 `Count`; `CLK-27` replaced it, and a userspace program reading my clockevent through `gettimeofday` is a longer chain than it looks |
| **`R1-pub-5`** ✅ **2026-09-14** | desk 1 + bench ½ ✅ | **`R1f`.** A C fragment correct under interlock and wrong without, built at every candidate `-march` and run on the device | At least two `-march` values run, and the predicted disagreement is observed **or the prediction is refuted in place** | **That the prediction is already this repository's rule.** `CLAUDE.md` bans `mips32` on exactly this ground; a run that confirms a rule already followed is worth less than one that finds the rule's edge |
| **`R1-pub-6`** ✅ **2026-09-16** | desk 2 + bench 1 —— 🟢 **矽片列 2026-09-14 做完** | **`R2c`.** Three toolchains, the same silicon measurements, three columns | Each toolchain builds the same source and the three columns are compared row by row; the choice, if one is made, is made **by the table**. 🔄 **2026-09-13（第六十二段）：DoD 補回計畫要求的那一列，而它在兩個下游檔案裡都不見了。** `plan/router-rebuild-plan.md:1141` 寫的是「三欄 × 三列的表，其中「load delay 的處理」那一列**三條都必須上矽片**（`R1f` 的程式碼各編一次）」，同一份檔案 §389 的表把那一列標成**唯一會安靜殺死專案的一格**。這一格的 DoD 原本只寫桌面比對，`docs/toolchain-prior-art.md` §6 更進一步寫成「an assembly step」—— **兩份都沒有駁回那個要求，只是沒有讀到它**，所以工作量欄的 `bench 1` 一直是這個 repo 裡唯一還記得它的東西，而它旁邊已經沒有任何 DoD 句子解釋它為什麼在那裡。🟢 **而它比看起來便宜**：`R1-pub-5`（`R1f`，bench ½）與這一列是同一個實驗的兩個寬度——一條工具鏈 × ≥ 2 個 `-march`，對 三條工具鏈 × 同一段碼——所以一支把（toolchain, `-march`）當參數的 payload 產生器可以讓兩個 bench 半**共用一次上電**，而不是各花一次。🟢 **2026-09-13：桌面半收了** —— `docs/toolchain-comparison.md`，五節表加五個新讀數加一節「兩欄以上沒有格子的列」；矽片那一列仍是一欄 | **Two segments is the plan's cap and this repository has never held one.** The stop-loss below is written for it |
| **`R1-pub-7`** ✅ **2026-09-16** | desk 2 | **The write-up**: `docs/rlx-isa.md`, and `docs/GATE-RESULTS.md` gains its **ninth** entry | The DoD read one row at a time, what the gate did not establish written, the operating clause re-run over nine entries | — |

### The DoD, split into what can be refuted

* **D1** every instruction row has one of **three** verdicts, and *does not
  trap and computes the wrong answer* is a cell that has either been observed
  or is recorded as never observed over a stated population.
* **D2** 🔴 **the negative controls fire.** A reserved opcode traps; every
  hazard test is shown able to produce the wrong answer. **Any one that does
  not fire voids the table**, and the table is not published without them.
* **D2b** 🔄 **2026-09-13 (sixty-third segment): the POSITIVE control,
  and it was missing from this list for two segments.** `plan:1074`'s pass
  condition has two halves -- 「**正控制成立**（MIPS-I 組全過）；**負控制成立**
  ...」 -- and `D2` above restates the second half word for word and the first
  not at all. 🔴 **The mechanism is in this section's own heading.** It is
  titled *split into what can be refuted*, and `plan:1075`'s 否證 covers only
  the NEGATIVE half (*任一負控制沒觸發 → 整張表作廢*), so a restatement
  organised around refutability drops a requirement with no refutation
  attached. 🔴 **And the row that pointed the next session at a population
  made it worse**: the census `R1-pub-0` built EXCLUDES the baseline group by
  rule and says so in its own § 0 -- *an instruction this core obviously has,
  and that the loader executes thousands of times per boot, gets no row* --
  which is exactly `add` `lw` `sw` `mult` `beq` `jr`. Two sources that would
  have carried the requirement, both silent. **The rule: `probe4`'s baseline
  group must read RIGHT, or the gate has not passed** -- weaker than 作廢,
  which is what the plan says and this row does not inflate.
  `tools/isapay.py`'s `check_controls` enforces both halves and
  `docs/isa-payload.md` § 6 is the owner.
* **D3** every hazard row reads *exposed* / *not exposed* / *not measurable*,
  with the third a legitimate result carrying the reason it could not be
  measured.
* **D4** the two-column table — bare metal against ~~the vendor kernel~~ 🔄 **the
  kernel, which `R1C-1` (2026-09-14) makes rlxfw's own** — exists for every row, and
  each difference is an entry in the emulation surface ~~with a measured cost~~ 🔄 **(`4b` owns the cost; 🔴 the correction landed on `:124` and not here for a day)**.
* **D5** `R1f` runs at ≥ 2 `-march` values on the device, and the disagreement
  is observed or the prediction is refuted in place.

#### 🆕 `D-cost` — `R1-pub-4b`'s own DoD, 2026-09-16, and it did not have one

🔴 **`D4` above had *"with a measured cost"* struck through and reassigned to
`4b` on 2026-09-14, and no replacement was ever written anywhere.** The only
written acceptance criterion `4b` had was a *prediction* in
`docs/rlx-isa.md` § 8.2 — which is a different kind of sentence. Written now,
before the card's seating, in clauses that can fail:

* **`E1` it is a slope, never a point.** Every quoted cost comes from ≥ 3
  iteration counts. A row with fewer is reported **not measured**, with the
  reason, and no number is quoted for it.
* **`E2` the zero control is smaller than the smallest thing reported.**
  `|slope(nop_a) − slope(nop_b)|` is printed and the smallest quoted cost must
  be **≥ 10×** it. 🔴 **If not, the whole table is void** — not partially
  valid. Two separately assembled `nop` cells at two addresses, so `x − x` is
  not what is being measured and the control can actually fail.
* **`E3` two boots.** At least one measured row and its twin are read on two
  independent boots. `docs/emulation-surface.md` states that every column-②
  cell rests on one capture on one boot; a step that repeats that has not
  noticed it.
* **`E4` linearity is checked and can fail.** Largest residual under
  `max(2 counts, 1 % of the largest Δ)`. Outside it the row is **non-linear**,
  its residuals are reported, and its slope is **not** quoted as a cost.
* **`E5` the ruler's own identity holds on every rung.** `Δirq_count ==
  Δjiffies`, and the two composites agree or differ by exactly one reload.
  More than ¼ of rungs failing voids the seating and the finding is about the
  **ruler** rather than the rows.
  🔴🔴 **2026-09-16 (第七十七段): this clause is a CONJUNCTION and every
  adjudication of it quoted one conjunct.** 量: `SPEC.md` `FW-73`,
  `bench/2026-09-16/CORRECTIONS-block22.md`, `LOG.md` and `:124` all quote only
  *the two composites agree or differ by exactly one reload*. The first conjunct
  — `Δirq_count == Δjiffies` — fails **5 of 64** rungs (`nop_a` r2, `lw` r3,
  `sw` r3, `lwu2` r0 on boot 1; `sw` r0 on boot 2), **every one of them
  `Δirq = Δjiffies + 1`, the same sign five times out of five.** Counted with
  both conjuncts, as the sentence is written: boot 1 is **10 / 32 = 31.2 %**,
  boot 2 is 7 / 32 = 21.9 %, the seating is 17 / 64 = 26.6 % — **boot 1 and the
  seating both cross this clause's own ¼ void threshold.** ⚠️ **而第二個合取項自己的數字也要在這裡,因為這個區塊是它的擁有者**:`FW-73` 量到兩次開機合計 **13 / 64** 個 rung 在第二個合取項上「失敗」,而**每一個都恰好差 1** —— 四個差 ±1、三個差 ±**1,999**,而 **1,999 = 一個 reload 減 1**。*(2026-09-16 第七十八段補:`spec-check` 的 `C5` 追不到這個字面,因為 `SPEC.md` § 19 整節在它的列級視窗之外;視窗拉開之後它第一次開火。)*
  🟢 **The four costs do not move, and the reason is structural rather than a
  rescue.** The ruler is `comp_tc1 = Δjiffies × 2000 + Δtc1`; `Δirq` is not in
  it, and both of its terms are snapshotted inside one `spin_lock_irqsave` —
  `drivers/clocksource/rtl819x-timer.c`, `j = get_jiffies_64()` at line 2001
  inside the lock held 1998–2042. **That separation is readable in `ucost.c` and
  in the driver with no reference to the outcome**, which is what licenses it as
  a reading rather than as something written afterwards to keep a table.
  🔴 **The defect is this clause's: it put two properties under one threshold and
  only one of them bears on what the threshold protects.** A void condition hung
  on a quantity the void is not about will void a correct table.
  ⚠️ **The mechanism is identified and NOT shown to be sufficient**: `irq_count`
  is read live at line 2147, 105 lines after the unlock, and that gap is
  symmetric in sign — it does not predict five one-sided differences in
  sixty-four rungs. Recorded as an open question, not as a cause.
  🟢 **And it is the thing the operating clause fires on at nine entries**, with
  `R5`'s `D4`: *two counters read atomically*, which neither gate established.
  `SPEC.md` `FW-75`, `docs/GATE-RESULTS.md`'s ninth entry and its clause section.
  ⚠️ **The clause text above is not edited.** It is a pre-registration; a
  document written before its own measurement is the rarest thing here.
* **`E6` the `ll`/`sc` question is answered in a direction chosen before the
  capture is read.** Either their slopes exceed their twins' by ≥ 10× the zero
  control — and `docs/rlx-isa.md` § 8.2's *"exactly one row"* is **refuted** —
  or they do not, and *"emulated in user mode"* is refuted as a statement about
  the executing machine while § 8.2 is **confirmed**. **Both are results.**
* **`E7` the surface's own gap is stated in the same document.** The surface is
  **8** instructions and `4b` prices **4**. The number goes in the write-up
  rather than being discovered by a reader.

> **否證 `D-cost`** — if the zero control is not at least 10× smaller than the
> smallest cost the table reports, the table is **void, not partially valid**.
> There is then no way to tell a measured cost from the instrument's own noise.

> **Second 否證, and it NARROWS rather than voids** — if a native twin's slope
> and `nop`'s differ by more than the zero control's spread, *loop overhead
> cancels* is **not** thereby refuted: they are different instructions and may
> genuinely cost differently, and this instrument cannot separate those two.
> What **is** refuted is the right to quote any absolute per-instruction cost;
> the table retreats to *differences against a named twin*, which is what it
> should have said in the first place.

**Stop-loss**: two power cycles. If `sync` — the one row `4a` already measured
as emulated — has no slope after two seatings, the **ruler** is the problem and
not the rows, and the step re-scopes in the open to measure the ruler rather
than absorbing more seatings.

### Refutation condition, written now

> **否證 `D2`** — if the reserved-opcode control does not trap, the payload's
> exception path is not working and **every zero in the table is
> unattributable**. The table is void, not partially valid, and the gate says
> so rather than publishing the rows that happen to look sensible.

> **否證 `D1`** — if `R1-pub-0` finds that the rows this repository already
> holds cover most of the census, the gate is **re-scoped in the open before a
> payload is written**, not padded out to 20 段. What makes this publishable is
> that it is not in public data; what makes it worth doing is that it is not in
> *this* data either.

> **否證 `D4`** — if the emulation-surface diff comes back empty, that is a
> finding about the vendor kernel and it is published as one. An empty diff
> after `CPU-47` already measured `ll`/`sc` emulation would instead mean the
> instrument is wrong, and the two are told apart by `ll`/`sc` themselves being
> in the table as its positive control.

### Stop-loss, written now

* **More than 28 段** — the top of the calibrated band — and the remaining
  sections move to `R10a` with the count recorded.
* 🔴 **`R2c` is capped at 2 段 by the plan and this repository has never held
  a cap.** If it runs over, the third toolchain is dropped and the table ships
  with two columns and the omission named.
  🔴 **2026-09-16, on closing: the cap cannot be scored, and nothing here counts
  it.** Charged three defensible ways — `R1-pub-6`'s own two segments (62nd desk,
  70th bench) makes the write-up the third and the cap **exceeded**; the desk
  side alone makes it the second and the cap **exactly spent**; adding the 61st
  (`R1-pub-0b`, `R2c`'s prior art) and the 66th (the shared payload generator)
  makes it **3–4**. 🔴 **And the prescribed remedy is inapplicable**: all three
  columns are already on silicon, so *drop the third toolchain* cannot be done.
  A fired stop-loss whose remedy is impossible needs a decision; it did not get
  one, and `docs/GATE-RESULTS.md`'s ninth entry records that rather than
  choosing the flattering count.
* 🔴 **No more than two seatings for `R1-pub-3`.** `R1h`'s stop-loss used the
  same shape and its decision ② is still 未定 after it fired, which is the
  precedent for how a fired stop-loss is recorded.
* **If `R1-pub-0` shows the blind premise is spent**, this gate is re-scoped
  before `R1-pub-1` starts rather than after `R1-pub-3` has spent a power
  cycle.
