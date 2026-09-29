# `PROGRESS.md` § `R6`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 66–177, by `R1y-4` on
2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R6`'s step list — ✅ CLOSED 2026-09-22, in 18 segments (84th–101st)

**Opened 2026-09-17** on the owner's decision, in the same segment `P1` closed
and `v0.4` was tagged. Its one-line definition is the gate board's: **my
Ethernet driver — `ping`, an `iperf3` number, 30 min flood clean.**

🔴 **This step list is being WRITTEN, not found.** 量 2026-09-17: `PROGRESS.md`
has never contained an `R6` step list, and `R6-0` existed only as a forward
reference in planning prose — `cfcensus`'s `L2` has already fired once on a
citation of it, in the eightieth segment, and the finding was recorded as *a
disposition that invented a gate while disposing of rows that name gates which
do not exist*. Everything below is new.

**Est. 41 段** — the plan's 小計 (21 desk / 17 bench / 3 instrument, 累計 154),
which § Gate board establishes is the only estimate carrying `Actual`'s
definition. 🔴 **Three numbers exist for this gate and two of them are stale**:
量 2026-09-17, `plan/router-rebuild-plan.md:1979` says **41**, this board's
`Est.` cell says **37**, and `plan/SESSIONS.md:20` (v4, 2026-08-23) says **35**
— and that same v4 table gives `R5` 22 against an actual of 32. The board cell
is left alone for the reason its own P1 row now records: editing one cell of a
column this board documents as reproducing no rule would also break its stated
sum. **41 is the denominator; 37 and 35 are not used.**
⚠️ Against the band re-derived at `P1-0` and extended by `P1` to eleven points
(min 0.33× / max 1.38× / median ≈ 0.83×), 41 段 predicts a range of **14–57**,
which is wide enough that it is a bound and not a forecast.

🔴 **`R6` has an unanswered PRECONDITION and it is not a risk.** Its own 否證 ②
is cache coherency for the descriptor rings, which is `SPEC.md` `CPU-45` — both
marks read `—`, the value reads *(未定)*, and it is still an open residual.
`R1h` was opened to settle it and closed without a measurement; the 2026-08-29
attempt had cell A come back negative and Group V invalidated by the payload's
own chain. **So `R6-0`'s first deliverable is that cell's redesign, not the
driver's skeleton** — the failure mode the plan names is *intermittent,
load-dependent data corruption*, which is the most expensive kind to debug.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R6-0`** ✅ **關了 2026-09-17（第八十六段）** | desk 1 | **The existing material, derived and dated, before any driver source exists** — every row this repository holds on the Ethernet / switch / PHY axis, each with its mark, the seating it came from, and 🔴 **whether it is LOADER-state or LINUX-state**. Plus this gate's DoD, its refutation conditions, and **the `CPU-45` cell redesign** | The population comes from **two sources that share no code**: `SPEC.md` through `spec-check`'s own parser, and a code-side instrument (`regcensus` over the vendor's Ethernet driver) — because `tccensus` had to declare that a population derived from the record cannot see a fact measured and never written down, and **this axis has a code-side instrument where the toolchain axis had none**. The list is committed **before** any driver source exists, so `git log` can check the ordering. The `CPU-45` redesign starts from the weakness `docs/rlx-cache-and-cp0.md` § ② states about itself | **That it reads as a to-do list rather than a population.** If most of the axis comes back already measured, the honest output is that this gate is smaller than 41 段 and saying so with the count. 🔴🔴 **A hypothesis was pre-registered here and REFUTED the same evening, BEFORE the census exists — recorded so the census cannot later be credited with it.** This cell first read *`docs/mfgtest.md` § 5 claims **every `NET-*` row in this repository is loader-state**; if that holds, `R6-1` carries the entire measured foundation.* 量 2026-09-17, on the survey that sized this gate: **the claim is false.** `NET-27` — *`/proc/rtl865x/port_status` exists in this kernel*, `讀 + 量-on-artefact`, **dated the same day the claim was left standing** — is Linux-state, and so are `NET-23`, `NET-25`, `NET-26`, `NET-04`, part of `NET-01` and half of `NET-13`. **So `R6-0`'s census does not TEST that sentence; it derives the loader / Linux tally over all 27 rows, which nobody has.** ⚠️ And the residual the refutation leaves is narrower and still real: **`MT-PORT`'s own subject — link state on a named port — has no numbered row in EITHER state**, and the nine `MT-PORT` captures seating 25 took are Linux-side Ethernet measurements that no `SPEC.md` row records. **That is a row `R6` can bank for free and a thing the census must not miss**　🔄 **2026-09-22（第一百段）：這一格的標記從 ⚠️ 半 改成 ✅，而改它的是一次稽核而不是新工作。** 量：這一格自 2026-09-17 起寫著「半」，欠的是**程式碼側的普查工具**；`LOG.md:30360`（第八十六段，同一天 18:26）的標題逐字是「`R6-0` 關了」，交付物是 `tools/hdrcensus.py`（18 個控制全過、接上 `ci.yml` 與 `ci-expected.tsv`、`ci-census` 認得它、不宣告 skip）。🔴 **而本檔 §Now 的 Active gate 格早就記了這件事** —— 它寫著「欠的那個以 `tools/hdrcensus.py` 交付」—— **所以同一個檔案的兩個地方對同一個步驟的狀態意見相反，維持了十四段**，而沒有任何檢查器看得到。步驟表是舊的那一個。⚠️ 這一格「最可能錯的地方」欄問的是*普查讀起來像待辦還是像母體*，而那一題**被答了**：546 個位址裡本 repo 只印過 69 個（87.4 % 從沒印過），也就是這條軸**大部分真的沒量過** —— 它讀起來像待辦，因為它就是。 |
| **`R6-1`** ✅ **2026-09-17，第二十六次上機，一次電源循環，三張卡片** | bench 1, **long**, card 🔴 要 | **The cold seating.** At the loader prompt: NIC and switch register reads, the `CPU-45` bare-metal payload, and the vendor-driver contrast on the same power-up | Every register the census marked *undetermined under Linux* is read at least once; `CPU-45`'s cell returns a verdict **or** returns *cannot distinguish its three causes*, which is also a result; the vendor-driver contrast is taken in the **same** power cycle so it is a control and not a second experiment | 🔴 **Cold cells are the expensive kind** — a question asked wrong costs another power cycle, and there is no spare device. This is the seating the census exists to load |
| **`R6-2`** ✅ **關了 2026-09-19（seating 27，第八十七段）** | desk N | **The switch to a dumb state from my code** — all ports one VLAN, no acceleration | The state is proved by a **register read-back**, not by the absence of a complaint | **That a dumb switch looks identical to a switch nobody configured.** The read-back needs a value that differs from reset 🟢 **關了 2026-09-19(seating 27,第八十七段)。** `41 of 41`,開機擷取 **1,759 = 預測 1,759**,`RLXFW-ID0=F681F8E0`。`D2` 成立:`diff` 與擷取兩個儀器都說 **2 of 37**(`SWTCR1`、`VCR0`),而 `dumb` 從不寫的 28 個**動了 0 個**(負控制)。重置的正控制 **11 of 37**,冪等性 **0** 兩種算法,同狀態取樣 **0**,往返 **9 of 9 全部回來**。🔴 **九個寫入有七個對 `S1` 是 no-op** —— `FULL_RST` 已經把那七個留在恰好等於 `dumb` 要寫的值,所以這一列「最可能錯的地方」欄寫的失敗模式**以量測的形式到達了**,而 DoD 仍然成立,因為有兩個會動而且卡片在動詞執行前就指名是哪兩個。`SPEC.md` `NET-43`–`NET-45` |
| **`R6-3`** ✅ **關了 2026-09-19（seating 28，第八十八段）** | desk N | **The CPU port's DMA rx/tx rings, the interrupt, and NAPI** | The checkpoint ladder is walked and **not skipped**: loopback → one-way TX → RX → NAPI. Each rung has an observable before the next is attempted | 🔴 **`OWN`-bit write ordering and big-endian descriptor fields.** The plan's own 否證 ① is *frames go out and none come back*, which is what a wrong field layout looks like from the outside 🟢🟢 **關了 2026-09-19（seating 28，第八十八段）。** 四階全走，每一階在下一階被嘗試之前都有觀測量：第 0 階 🔴 **否證**（`SWINTSET` 在引擎開、遮罩開下仍然不升中斷，**而正控制在同一次開機裡**）、loopback 逐位元組返回、TX 被工作站擷到、RX 解出一個真 ARP、NAPI 的遮罩→排空→還原→**中斷恢復**。`/proc/interrupts` 的三態控制兩額合。`SPEC.md` `NET-48`–`NET-50` |
| **`R6-4`** ⚠️ **半，2026-09-19（seating 28）** | desk N | **A standard `net_device` plus basic `ethtool` ops**, and the PHY through `phylib` | `ping` completes in both directions with my driver bound and the vendor's **not** loaded, and the discriminator is **positive** — a string only my driver produces — rather than the vendor's absence | **That the switch is forwarding and the driver is not.** This board has a switch between the MAC and the jack; a reply can arrive without my RX path having seen it 🟢 **關了 2026-09-19（seating 28），而 `D4` 只部分成立且缺口寫下來。** `rlx0` + 真 NAPI，`ping` 雙向 4 of 4，正向鑑別器是一個任何 Realtek OUI 都裝不下的本地管理 MAC（**不讀 `H601` 是圍堵決定**）。🔴 廠商驅動仍在映像裡；量到的是它**沒有載運這些流量**（非共享 `request_irq(12)` 成功、`CPUICR` 在我寫之前讀 0、環在我配置的位址上）。`SPEC.md` `NET-51`–`NET-54`　🔄 **2026-09-22（第一百段）：這一格的標記從「沒有標記」改成 ⚠️ 半，而那是降級不是升級。** 量，這一格「What it produces」欄指名三樣東西，只有一樣在映像裡：① **`ethtool` ops 沒有實作** —— 整支驅動裡 `ethtool` 出現 **1 次**，是第 118 行一句說沒有的註解，`SET_ETHTOOL_OPS` **0 次**；② **`phylib` 那一半是 0** —— `phylib`／`phy_connect`／`mdiobus`／`mii_bus`／`phy_device` 各 **0 次**，而 `CONFIG_PHYLIB` 在 `config/` 裡一列都沒有；③ DoD 的「廠商的**沒有**載入」在**這顆映像如今的建置**下不成立，因為關掉 loader DMA 引擎的正是廠商的 probe。🔴 **而「架構上做不到」是過強的說法，本段就地否證了它，而寫下那句過強話的是我自己，在同一段裡。** `notes/nic-driver.md:41` 逐字寫的是「**In this image** that probe is the only thing that turns the engine off」—— 那是一個**建置組態**的事實，不是矽片的事實。量 2026-09-22：`nic_do_engine(0)`（`rtl819x-nic.c:2297-2306`）已經逐位元組做同樣兩個寫入，而 `drivers/net/Makefile:276` 的 `CONFIG_RTL_819X_SWCORE` 關得掉整棵廠商樹。**`D4` 因此只部分成立**，而較窤的真話寫在 `notes/nic-driver.md:56-63`。擁有者 2026-09-22 裁定：**先做到再關**，所以 ③ 是這一段的工作而不是一條註記　🔄 **2026-09-22（第一百零一段）：那個裁定是在量測之前做的，而量測把它推翻了 ——這一格以「部分達成＋缺口具名」關掉。** 量（第一百段的卡片 § 0 ②，`readelf` 對一棵完整建好的樹）：`CONFIG_RTL_819X_SWCORE=n` 在 vmlinux 連結留下**十個未定義符號、四個獨立位置**；過了連結，VLAN 表在要消失的那個目錄裡是 `TACI` 協定；而同一個開關刪掉 `/proc/rtl865x/`，那是 `NET-109 殘留` 下一步的儀器。**所以「先做到」不是一步，是一個 gate**，而且它會先拆掉本 gate 自己兩個殘留需要的儀器。先例 `P4b-gate`（2026-09-01，`D2` 未達成而關，理由記下、兩件事留在 gate 底下）。① 與 ② 照擁有者原裁定「記錄＋延後」 |
| **`R6-5`** ✅ **2026-09-22（seating 37），七次上機，兩條 DoD 都成立：`D6` = `NET-76`（seating 32，31.66 分鐘）、`D5` = `NET-102`（seating 37）** | bench 1, card 要 | **The numbers.** `iperf3`, and 30 minutes of flood with continuous traffic — not a 2.4 s loop | An `iperf3` figure exists **with its method and its spread over ≥ 3 runs**; the flood shows zero drops by the driver's own counters **and** zero oops, with the kernel log captured whole rather than grepped | 🔴 **A single number is not a curve.** This project has recorded that shape four times; one `iperf3` run is one sample. 🔄 **2026-09-20, two seatings, step NOT closed.** Seating 29 (segment 90, 01:30–04:16, four power events) and seating 30 (segment 91, same day from 18:35). `D5` and `D6` were not obtained either time and both reasons are measured rather than guessed: on the first, every `iperf3` run died in its control exchange so no bulk TCP was carried; on the second the blocker became **identified** rather than undetermined — `SPEC.md` `NET-61`. **A throughput number taken in that state would measure the defect and not the path**, so `D5` is deliberately not attempted again before a fixed image exists　🔄 **2026-09-21（seating 32，第四次上機，三次電源循環）：`D6` 拿到了，`D5` 沒有，而四個假說被事前寫好的否證條件殺掉。** `NET-71`：引擎停在一個它自己擁有的描述子上而**什麼都不缺**（`USEDDSC` 18／244、高水位 30、run-out 旗標 0、所有埠零壅塞、`STOPTX` 清、零錯誤位元）——描述子池耗盡與流量控制兩個候選直接被讀數否證。`NET-72`：三階恢復二分，門鈴與引擎命令狀態被排除，`arm` 的三個改變裡兩個被量測排除，剩 OWN 清除。`NET-73`：故障需要一條 TCP 連線，五個維度被排除。`NET-74`／`NET-76`：這支驅動的第一個吞吐量數字，20 秒與 31.66 分鐘兩個時間尺度相差 0.4 %。　🔄 **2026-09-21（第九十四～九十六段，seating 33／34／35）：這一格的標題寫「兩次上機」而實際是 **七次**（seating 29、30、31、32、33、34、35），而它的本文停在 seating 32。** 🔴 **本文引的 `NET-73`「故障需要一條 TCP 連線」已經被否證兩次**：`NET-77`（seating 33，四個階梯全不 wedge）打掉寬讀法，`NET-86`（seating 35，對一個**關閉的埠**灌 UDP、板子上零使用者空間行程）打掉窄讀法。🟢 seating 35 的結果:廠商驅動載運 `iperf3` 並存活（`NET-84`），rlxfw 自己載運 203 MBytes（`NET-85`），`NET-77` 三個候選全滅（`NET-86`），最小重現 347 訊框／8.01 s／0.5 Mbit/s（`NET-87`），而廠商的環滿契約救不了它（`NET-88`）。**步驟仍然沒關**，而剩下的問題收斂成一句，擁有者是 `NET-67 殘留`。　🔄 **2026-09-22（seating 37，第九十九段）：`D5` 成立，而步驟還是沒關。** `iperf3` 那一條 DoD 滿足了：**17.03 / 17.76 / 17.09 Mbit/s**，n=3，散布 0.73 Mbit/s（4.2 %），方法寫在 `notes/nic-driver.md` § 16.3，五次 `phfollow 0` 控制臂是 0.04–0.07 Mbit/s。🔴 **而第二條 DoD —— 30 分鐘連續洪水、驅動自己的計數器零丟包、零 oops、kernel log 整份擷取 —— 這一段一次都沒跑**。它之前跑不了是因為驅動載不動持續流量；現在載得動了。~~**這一列不把「拿到 `D5`」寫成「步驟關了」。**~~　🔄 **2026-09-22 02:30（`72ccbc8`）：這三句話過期了，而修正只改了本格的標題、沒有改本文，所以同一格自己反對自己。** `D6` 不是「這一段一次都沒跑」—— 它在 **seating 32** 就跑完了（`SPEC.md` `NET-76`：`ping -f -w 1800 -l 32 -s 1400`、1,899.593 s ＝ 31.66 分鐘、`drop 0/0`、零 oops、log 整份擷取），而 **DoD 是整個 gate 累積的，不是每次上機重新起算**。本格標題已經是 ✅；本文留著並劃掉，因為「我問錯了哪一個問題」比「答案是什麼」值錢 |
| **`R6-6`** ⊘ **不達成，2026-09-22：三個子句裡兩個量出來結構性達不到，較弱的真話取而代之** | desk 2–3 | **Stretch: per-port VLAN** | Two ports on different VLANs cannot `ping` each other while each reaches the CPU port; **positive control**: restoring one VLAN table restores connectivity | **That the VLAN table wrote and the packets ignored it** — which means the address is wrong, or this part's VLAN is a mechanism other than `PVID`. **Stop-loss one segment; this is a stretch, not a pass condition**　🔴 **2026-09-22：三個子句裡兩個結構性達不到，而理由是量的。**「兩個埠不能互 ping」要兩台主機同時在兩個孔上 —— 量，十三次讀數，每一次**恰好一個埠** `LinkUp`，移動網路線測到的是兩個埠在兩個**時刻**。「還原一張 VLAN **表**」獨立地達不到 —— 讀 `rtl819x-switch.c:93-97`，表要走 `TACI`（`SWTACR`／`SWTAA`／`TCR7`），那是一個協定不是暫存器寫入，rlxfw 能還原的是 **PVID 暫存器**。🟢 **取而代之成立的那句較弱的真話**（原文在 `bench/2026-09-21/PREDICTIONS-B35-block33.md:374-377`，在讀數之前寫下）：*在這顆零件上，`0xBB804A08 + (port*2 & ~3)` 的每埠 PVID 欄位決定那個實體埠的入向流量會不會到達 CPU 埠，由雙向 ping 量測、埠身分在每一次換線的兩側都從 `PSRP` 讀出，而把原本的字寫回去可以還原它。* 可讀的那一半已經在 seating 33／34／35／38 讀過四次，**每一次逐位元組相同** |
| **`R6-7`** ✅ **關了 2026-09-22（第一百零一段，桌面，零電源循環）** | desk 1 | **The write-up**, and `docs/GATE-RESULTS.md` gains its **twelfth** entry | The DoD read one row at a time; what the gate did **not** establish written; the operating clause re-run at twelve entries　🟢 **做到了，而 clause 開火了。** 第十二筆在 `docs/GATE-RESULTS.md`：一行版、三條站得住的主張（`D1` 的不一致、`D3` 的階梯推翻自己第一階、`D5`／`D6` 兩個數字各帶著削弱自己的那一句）、九條「沒有建立什麼」。**十二筆的 clause 開火**，指名 `MT-PORT` 不說是哪一支驅動；**事前登記的普查第四次重跑，母體 44 條 D 列（八個 gate）＋ 13 條 = 57**，而**第四個實例出現了**（`D6` 指名「驅動自己的計數器」，`NET-62` 量到那個計數器對這個故障是瞎的）—— enforcer 仍然不寫，因為登記的條件寫的是**「沒有人已經知道的第四個」**而這一個有 id、有日期，而且它是四個裡**第一個機械檢查器抓不到的**。同一天 `FW-109` 是相反的判決：那個家族買得到，四個正控制都有，而它因為**排程**被延後 | — |

### The DoD, split into what can be refuted

* **D1** ✅ **2026-09-17 — ANSWERED, and the answer is NOT COHERENT** (seating 26, block 25: two of four buffers stale in each of two runs, the eviction branch closed by the data). 🔴 **`CPU-45` is answered on this die before any descriptor ring
  depends on it** — whether this D-cache is coherent with memory written by
  something other than the CPU, and which instruction invalidates a clean line.
  **If it cannot be answered, the gate records in those words that the rings
  rest on an unmeasured memory model**, and says what that costs.
* **D2** ✅ **MET 2026-09-19（seating 27）—— `NET-43`–`NET-45`**：兩個儀器都說 **2 of 37**（`SWTCR1`／`VCR0`），`dumb` 從不寫的 28 個動了 **0** 個（負控制），重置的正控制 11 of 37，往返 9 of 9。 the switch reaches a dumb state from my code, proved by a register
  read-back whose value differs from reset.
* **D3** ✅ **MET 2026-09-19（seating 28）—— `NET-48`–`NET-50`**，四階全走而第 0 階**被自己的正控制推翻**。 🔴 **a frame my driver transmitted is seen by the workstation, and a
  frame the workstation transmitted reaches my driver's RX path** — each with
  **two sources**: a counter of mine on the device, and a capture on the host.
* **D4** ⚠️ **MET IN PART 2026-09-22，缺口具名並估價。** 前半成立（seating 28，雙向 4 of 4，正向鑑別器是一個本地管理 MAC）；後半不成立：廠商驅動在映像裡、它每一個硬體初始化都跑，`re865x_open()` 回 `-ENODEV` 而 `/proc/net/dev` 仍列 `eth0`…`eth4`（`NET-106`）。**拿掉它是一個 gate**（十個未定義符號／四個位置／`TACI`／連帶刪掉 `/proc/rtl865x/`），先例 `P4b-gate`。`docs/GATE-RESULTS.md` 2026-09-22 的「沒有建立什麼」第一條。 `ping` completes both directions with my driver bound and the vendor's
  unloaded, with a **positive** discriminator.
* **D5** ✅ **OBTAINED 2026-09-22（seating 37）—— `NET-102`。** 🔴 *（這一列的標題在 2026-09-22 02:30 之前寫著 **NOT OBTAINED after two seatings**，而 `R6-5` 的步驟格在同一天被標成 ✅；兩處相差十四小時以上，維持到第一百段才被一次稽核抓到。）* 🔴 **而它的數字帶一條引用規則**：`notes/nic-driver.md:2038` 逐字寫著「The three-run figure may not be quoted without the fourth.」—— `phfollow 1` 跑了 **四** 次，三次群聚在 **17.03 / 17.76 / 17.09 Mbit/s**（散布 0.73，4.2 %），**第四次 `H3` 在第一個區間之後崩掉**，同一條臂、同一個命令、同一塊板子。**n ＝ 4 而其中一次崩掉，才是這個量測本身。** *（以下為原文，保留：）* an `iperf3` number exists, with the method that produced it and its
  spread over at least three runs. 🔄 **2026-09-20 (seating 29):** every `iperf3` run died in its control exchange, so no bulk TCP was ever carried (`SPEC.md` `NET-59`'s corrected row, `NET-60`). 🔄 **2026-09-20 (seating 30):** the reason is now identified rather than undetermined — `NET-61`, a burst desynchronises the engine's two RX position registers and the driver then delivers frames carrying another frame's length. **A throughput number taken in that state would measure the defect and not the path**, so `D5` is deliberately not attempted again until a fixed image exists.　🔄 **2026-09-21（seating 32）：仍然沒有，而理由第一次是一個可以被否證的機制。**`D5` 指名的是**儀器**（`iperf3`）而不是協定、方向或單位；`iperf3` 一定開一條 TCP 控制連線；而量到的是**一條 TCP 連線是每一次 wedge 都有、每一次不 wedge 都沒有的唯一因子** —— 訊框大小、在途深度、流量總量、方向、批量協定五個維度全部被否定控制排除（`SPEC.md` `NET-73`）。這一段五次 `iperf3` 呼叫五次 wedge，其中一次連控制連線都沒建立起來。⚠️ **而「一條 TCP 連線」與「`iperf3` 這支程式」沒有被分開** —— 用 `socat` 開一條純 TCP 連線就分開了，不花電、不用新映像，是下一段的第一格。🟢 手上**有**一個數字（`NET-74`／`NET-76`：單向 14.88 Mbit/s、合計 29.76 Mbit/s、持續 31.66 分鐘），但它是 `ping` 量的，**過不了`D5` 的儀器條款，而這一列不把它偷渡進去**。　🔄 **2026-09-21（第九十五段，桌面，零電源）：`D5` 仍然沒有，而這一段做的是 `D3` 自己寫下的否證條件** —— *a field-by-field comparison against the vendor's driver, written down, and not a retry* —— **而它從來沒有被執行過**。`docs/nic-vendor-diff.md`：十條軸，其中 `NET-81`（廠商走硬體查表、rlxfw 泛流 `0x3F`）、`NET-82`（廠商跟 `ph_mbuf` 指標走、從不索引 mbuf 環）與 `NET-83`（`ph_flags` 兩個模板值被第二來源確認）是新的。🔴 **一個候選在桌面上被已提交的擷取否證了**（`ph_vlanId = 0`；`VCR0 = 0` 且跨故障不動，而關掉它的是廠商自己的 probe）。🟢 **而最有用的一件是：廠商驅動的同一次開機對照是拿得到的** —— `docs/KNOWN-ISSUES.md` 說的 EBUSY 是量在一格**沒有先 `ifconfig rlx0 down`** 的擷取上，而 seating 28 先 down 過、交接成功。**三個指令，搭任何一次開機，零額外電源。** ⚠️ 這一段**沒有任何東西在矽片上跑過**。
* **D6** ✅ **MET 2026-09-21（seating 32）—— `NET-76`**，三個連言各有讀數，覆蓋率缺口 97.9 % 寫在列裡。🔴 **而 2026-09-22 的普查把它記成那個家族的第四個實例**：這一列指名的是**儀器**（驅動自己的計數器）而不是性質，而 `NET-62` 量到那個儀器對這個故障是瞎的。 🔴 ~~**NEVER ATTEMPTED, and now blocked for a measured reason.**~~ 30 minutes of continuous flood: zero drops by the driver's own
  counters, zero oops, kernel log captured whole. 🔄 **2026-09-20:** `NET-61` means a flood reaches the desynchronised state within its first seconds, so *zero drops by the driver's own counters* would be **true and meaningless** — 量 seating 30, the driver's `n_rx` counted every one of 5,281 frames while 218 datagrams died above it. **The DoD's own instrument is the one this fault is invisible to**, which is `NET-62`.　🟢🟢 **2026-09-21（seating 32）：達成，三個連言全部有讀數。** 量，映像 `s31L`（`CONFIG_PRINTK=y`，第一次在矽上執行），主機 `ping -f -w 1800 -l 32 -s 1400`，**1,899.593 s ＝ 31.66 分鐘**：① **驅動計數器零遺失** —— `nd_stats rx 2450491/3533456154 tx 2450389/3533309070 drop 0/0`，`n_tx_stop 0`、`tx_stopped 0`、四個 `txd` OWN 全清；② **零 oops** —— 主控台 **0 位元組**，而這顆映像有 `printk`（oops 會印，wedge 會每 1.06 s 印一行，兩者都沒出現）；③ **log 完整擷取而不是 grep** —— 一次不中斷的唯讀擷取，`sent: null`，`duration_s 1860.084442`。**雙向 7,066,765,224 位元組 ＝ 7.067 GB，29.761 Mbit/s 合計。** 🔴 **而第三個連言有一個屬於我的缺口，寫在這裡而不是被抹掉**：擷取 1,860.084 s、洪水 1,899.593 s（`ping -w` 是期限，超時量量到是 99.6 s），**最後 39.5 秒沒被擷取 —— 覆蓋率 97.9 %**。緊接著的讀數是乾淨的，但那 39 秒裡的一個 oops 不會被記錄。⚠️ `drop 0/0` 對它上面那一層是瞎的（`NET-62`），所以主機端的 **0.00518 %** 是並列而不是取代。🔴 洪水之後板子**回 ARP 而不回 ICMP echo**，未定，`NET-76` 殘留。`SPEC.md` `NET-76`。

### Refutation conditions, written now

> **否證 `D3`** — if frames go out and none come back, the descriptor field
> layout is wrong for big-endian. The honest output is a **field-by-field
> comparison against the vendor's driver**, written down, and not a retry.

> **否證 `D6`** — if corruption is intermittent and load-dependent, that is
> `D1` not having been answered. The gate goes **back to `D1`** rather than
> adding a workaround, because a workaround for an unmeasured memory model is
> a second unmeasured thing.

> **否證 `D1`** — if the redesigned cell still cannot separate *no
> read-allocate* from *the alias is snooped* from *the line was evicted*, the
> honest output is that this die's coherency is **undetermined** and the driver
> uses uncached mappings throughout — **with the throughput cost measured
> rather than assumed**, because an uncached ring is a different `D5`.

### Stop-loss, written now

* 🔴 **三個連續工作段（每段 ≥ 4 小時）沒 `ping` 通 → 轉 fallback。這一條一字
  不改。** The fallback is still a deliverable: **this board's actual switch and
  MAC initialisation sequence**, plus a polling-only minimal driver. *(The
  manual gives registers; it does not give order.)*
* **More than 41 段** — the plan's 小計 — and the remaining steps are recorded
  as not-done with their reasons, not carried.
* 🔴 **Any step that turns out to need the board leaves `R6-0`**, named, and
  goes to the step that owns a seating. `R6-0` is desk, **zero power cycles, no
  card** — and what it produces is the *card design* for `R6-1`, which is a
  different artefact from a card.
* 🔴 **The stretch `R6-6` gets one segment.** It is not a pass condition and it
  does not borrow from the mainline's budget.

### What this gate must be able to answer, from the plan

讀 `plan/router-rebuild-plan.md:1946` — three questions the plan attaches to
`R6`, recorded here because a gate that produces a working driver and cannot
answer them has produced a working driver and nothing else:

* *`dma_alloc_coherent` 跟 `dma_map_single` 差在哪？*
* *NAPI 為什麼要遮罩中斷？重開中斷的 race 在哪？*
* *`OWN` 位元的寫入順序錯了會怎樣，你怎麼測出來？*

⚠️ The third one is `D3`'s refutation condition wearing a different hat, and
that is deliberate: it is the question whose answer is a **measurement** rather
than an explanation.
