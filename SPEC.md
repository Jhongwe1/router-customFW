# SPEC —— 這個專案握有的每一個數字

**這是一份數值索引，不是任何結論的擁有者。** 每一列帶一個穩定 id、數值、
兩個證據標記、背後有幾個獨立來源，以及**擁有這個發現的檔案**的連結。
語意、推導過程與否證條件都留在擁有者檔案裡；這張表存在的目的，
是讓一個設計決定不必先去把它們翻出來。

房規第一條 —— 一份狀態只有一個擁有者 —— 在這裡沒有被暫停。
**若這份檔案與擁有者檔案不一致，擁有者檔案贏，而這一列是過期的。**
數值變了就在同一個 commit 裡改這裡；一列若說不出擁有者，那列本身就是 bug。

**範圍：一台實體裝置。** TOTOLINK N150RT，硬體 V2.0，二手購入，從未部署。
凡是屬於「這個型號」而非「這台」的值都會註明。凡是只屬於這台的
—— MAC、序號、射頻校正、WPS PIN —— **完全不在這裡**，理由見 §18。

---

## 0. 怎麼讀一列

兩個標記，因為這個專案已經被「數值對、名字錯」咬過兩次
（`RUNSHEET.md` 的 `B3`、`B4`）。

| 欄 | 標的是什麼 |
|---|---|
| **V** | **數值**的來源 —— 這個數字是怎麼來的 |
| **N** | **名稱與語意**的來源 —— 誰說這個欄位叫這個名字、是這個意思 |

| 標記 | 意思 |
|:---:|---|
| **量** | **在這台裝置上量到的** —— 一次讀數，並指名是哪一份 capture。封裝絲印記為「量」而來源記 `P`：油墨是對這台的觀察，不是對它行為的觀察 |
| **讀** | **從程式碼或 dump 讀出來的** —— 靜態，對指名的那份 artefact 為真 |
| **推** | **推測的，待量測** |
| **文** | **讀自文件的** —— datasheet 或廠商標頭說的，既不是這台的量測、也不是它自己的碼。單獨一個 `文` 永遠不夠讓一個值進到程式碼裡 |
| **—** | **尚未確立。** 這一格是刻意留白的，§17 會說什麼能填它 |

> **`V` 是 `—` 的列，值欄一定要帶一個明說的記號**：`留白`／`未定`／`未讀`（開著的問題，§17 欠它一個實驗），或 `§18`／`選定`（根本不是一個待量的值）。**沒有來源標記卻擺著一個值，讀起來就像已經確立。**`tools/spec-check.py` 的 C3 檢查這一條。

來源，而它們的可信度並不相等：

| | 是什麼 |
|:---:|---|
| **A** | 這台自己的 flash dump 與從中切出來的 binary —— `stage2.bin`、rootfs。對「**這台**做了什麼」是決定性的 |
| **B** | 廠商 GPL 原始碼 —— bootcode、Linux 2.6.30、`apmib`。**是不同世代的 SDK。** 它解釋一個常數為什麼是這個值，永遠不能代替 A |
| **C** | `upstream/`，pin 在 `4d3ff26` —— 它在**同一台實體裝置**上取得的量測與報告 |
| **D** | `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` —— Draft Rev D1.1，2013-07-17，`-VE1/2/3` 內嵌 DRAM 版。**這台不是那顆**；周邊暫存器地圖共用是一個假設。標 `CONFIDENTIAL`，引用、不提交 |
| **E** | 廠商 Linux 標頭檔 —— 暫存器名稱與位元欄位 |
| **P** | 這台的封裝絲印或照片 |
| **S** | 本 repo 自己的 bench 逐字紀錄 —— `bench/<日期>/*.log` |
| **X** | 第三方公開規格。列出來是為了被否證，永遠不當證據 |

**兩個獨立來源，否則就是未定。** 來源欄只有一項的列，就是還沒達到
`CLAUDE.md` 那條門檻的列 —— 而把這件事寫在表上，正是這一欄存在的理由。

### 這張表怎麼被檢查

`python3 tools/spec-check.py`。七項檢查：

| | 檢查什麼 |
|:---:|---|
| C1 | 每一列都有格式正確且唯一的 id |
| C2 | `V` 與 `N` 欄帶合法標記 |
| C3 | 值標了 `留白`／`未定`／`未讀` ⇒ §17 一定列著它。`V` 是 `—` ⇒ 值一定帶一個明說的記號 |
| C4 | 擁有者欄指到的檔案真的存在 |
| C5 | 這一列的字面值（十六進位字、`0x` 形式、帶千分位的數）**仍然出現在它的擁有者檔案裡** |
| C6 | §18 那條規則：把 `tools/audit-bench-log.py` 的樣式跑一遍，每個命中都必須在一張帶理由的白名單上 |
| C7 | 帶著值的列至少寫出一個來源 |

**八個突變，每一個都必須產生一個這個檔案原本沒有的 finding**，而且必須由指名的那一項檢查、用指名的那句話抓到 —— 被別的檢查抓到是一個假的控制，而重現一個本來就有的 finding 不算數。**控制在每次執行時都跑**（跟 `audit-bench-log.py` 同一個理由），任何一個沒立，工具就拒絕對檔案發表意見。

**它抓不到的，寫在這裡免得乾淨的結果被讀成比它更多的東西**：C5 比對的是字面值不是意思，所以散文被改寫而數字沒動會過，數字正確但擁有者檔案本身錯了也會過；它完全不知道一個值對不對 —— 那只有 bench 知道。`plan/` 是 gitignored 的，在 clone 裡驗不了。**沒有任何東西在檢查「兩個來源互相同意」**，那條房規靠讀。

---

## 1. 身分

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `IDN-01` | 產品 | TOTOLINK N150RT | 量 | — | P、C | `upstream/notes/hardware-inspection.md` |
| `IDN-02` | 硬體版本 | `V2.0` | 量 | — | P（機殼標籤） | `upstream/notes/anatomy-n150rt.md` |
| `IDN-03` | 序號 | *(屬於這台 —— §18)* | — | — | — | — |
| `IDN-04` | 板上絲印 | `0422C`，在 SDRAM 旁 | 量 | — | P | `upstream/notes/hardware-inspection.md` §7.1 |
| `IDN-05` | PCB 廠標／防燃等級 | `JL-2` · UL `94V-0` | 量 | — | P | 同上 |
| `IDN-06` | PCB 日期標 | `18.15` —— 2018 年第 15 週 | 量 | 推 | P | 同上 §6 |
| `IDN-07` | 組裝時間下界 | **不早於 2018-09** | 推 | — | 五個彼此一致的日期碼 | 同上 §6 |
| `IDN-08` | 組裝方式 | 單面貼裝；背面是裸銅、焊點與兩張標籤 | 量 | — | P | 同上 §7.1 |

## 2. 矽片 —— SoC 與 CPU 核心

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `CPU-01` | SoC | **Realtek RTL8196E** | 量 | 量 | **×3** —— P、開機 banner（C、S）、開機碼自己對 ID 的比較（A） | `upstream/notes/uart-findings.md` §2 |
| `CPU-02` | SoC 封裝絲印 | `RTL8196E · I510VG1 · GF23 TAIWAN` | 量 | — | P | `upstream/notes/hardware-inspection.md` |
| `CPU-03` | 晶片 ID 比較常數 | `0x8196E000`，比對的是 reset 時對 `0xB8000000` 的一次讀取 | 讀 | 讀 | A | `upstream/notes/uart-findings.md` §2 |
| `CPU-04` | **CPU 核心** | *(未定 —— RLX4181 或 RLX5281)* | — | — | D 說 `RLX4181`；通行說法是 `RLX5281`；**裝置兩個都不說** | `refs/README.md`、gate R1 |
| `CPU-05` | `/proc/cpuinfo` `system type` | `RTL819xD` —— 第三種不同的叫法，除了矽片 ID 的 `8196E` 與網卡驅動的 `8196C` | 量 | — | C | `upstream/test-ledger.md` `P5-5` |
| `CPU-06` | `/proc/cpuinfo` `cpu model` | `52481` —— 一個十進位數字，**不是核心名稱** | 量 | — | C | 同上 |
| `CPU-07` | BogoMIPS | `398.95` | 量 | — | C | 同上 |
| `CPU-08` | TLB entries | `32` | 量 | 量 | C | 同上 |
| `CPU-09` | MIPS16 | `mips16 implemented : yes`（kernel 自己的說法） | 量 | — | C、D | 同上 |
| `CPU-10` | 硬體 watchpoint | `no` | 量 | — | C | 同上 |
| `CPU-11` | 時脈 | **400 MHz** | 量 | — | 開機 banner（C、S）、D | `bench/2026-08-23/A-catch.log` |
| `CPU-12` | 位元組序 | **big-endian** | 讀 | 讀 | A —— 每一支 ELF 都是 `ELFDATA2MSB` | `upstream/notes/anatomy-n150rt.md` |
| `CPU-13` | 手冊宣稱的 ISA | `Supports MIPS-1 ISA, MIPS16 ISA` | 文 | 讀 | **只有 D** | `SOURCES.json` `ds-rtl8196e-vex` |
| `CPU-14` | **load delay slot** | **架構外露 —— 沒有 interlock** | 量 | 讀 | **×2** —— C 對 `stage2` 的指令普查（1,474 個 load、646 個後面接 `nop`、後面接「讀取剛載入暫存器」的 0 個），以及矽片上一次單一變數實驗。**2026-08-24 在本 repo 用 `tools/hazlint` 獨立重算，三個數字全中**，負控制是上游那份真的在這台上失敗過的 payload | `tools/hazlint` |
| `CPU-15` | 矽片有沒有 `lwl`/`lwr`/`swl`/`swr` | *(未定)* | — | — | 裸機 RI 處理器下執行一條 `lwl` 就結案 | `notes/lwl-mystery.md`、gate R1a |
| `CPU-16` | ……這台的 binary 裡有幾個 | `stage2` **0** · `busybox` **0** · `boa` **144** | 讀 | 讀 | A、`tools/opcount.py`，控制在 `tools/test-opcount.sh` | `notes/lwl-mystery.md` |
| `CPU-17` | `movz` / `movn` | **loader 程式區裡 18 個**，其中兩個在 `check_image()` 裡，每次開機都會跑；18 份 capture 裡沒有任何例外訊息 | 讀（數量）· 量（那個「沒有」） | 讀 | A、C | `docs/loader-command-semantics.md` §9、`C-12` |
| `CPU-18` | loader 程式區裡的 `ll` `sc` `cache` `pref` `sync`、branch-likely、SPECIAL2/3、FPU、`jalx` | **全部為零** | 讀 | 讀 | A，**三支**解碼器（第三支是 `tools/hazlint --isa`，寬鬆與嚴格兩種判準都得 18），每一支都在 rodata 裡示範過會誤報，那就是控制 | 同上 |
| `CPU-29` | `mult`/`div` 後面緊接 `mfhi`/`mflo` 的位址數 | **16 個**，最早在 `0x80403C14` | 讀 | 讀 | A，`tools/hazlint --survey` | `docs/loader-command-semantics.md` §9 |
| `CPU-30` | `mtc0` 後面緊接 `mfc0` 的位址數 | **3 個** —— `0x80400408`、`0x8040041C`、`0x80400660`，第一個是同一顆 `Status` 寫完立刻讀 | 讀 | 讀 | A，同上 | 同上 |
| `CPU-31` | 非 load 的 hazard 規則（`HI`/`LO`、CP0） | *(未定)* —— `CPU-29`／`CPU-30` 說原廠編譯器**沒有**在中間補 `nop`，這與「有互鎖」相容，也與「有互鎖但這兩處是 bug」相容。數得出來不等於判得出來 | 讀（計數）· — （規則） | — | A | `C-9`、gate R1b |
| `CPU-19` | 快取管理模型 | **R3000 式** —— `Status.IsC`/`SwC`，外加一顆 Lexra 的 CP0 20 號暫存器 | 讀 | 推（`CCTL` 這個名字） | A + B | `notes/cache-model.md` |
| `CPU-20` | CP0 r20 —— invalidate I-cache | `0x002` | 讀 | 讀 | **×2** —— A `0x804066e8`、B `c-r3k.c` | 同上 |
| `CPU-21` | CP0 r20 —— flush D-cache（819x 路徑） | `0x200` | 讀 | 讀 | **×2** —— A `0x804066c0`、B | 同上 |
| `CPU-22` | CP0 r20 —— flush D-cache（865xB 路徑） | `0x001` | 讀 | 讀 | **×1 —— 只有 B** | 同上 |
| `CPU-23` | CP0 r20 —— `0x202` | 兩件事一次寫 | 讀 | 推 | A `0x804004f8`；意思是從 `0x200 \| 0x002` 推出來的 | 同上 |
| `CPU-24` | CP0 r20 —— `0x010`、`0x020` | *(未定)* —— 開機初始化時發出，任何來源都沒有名字 | 讀 | — | **只有 A** | 同上 |
| `CPU-25` | 快取大小／line 大小／關聯度 | *(留白)* | — | — | `c-r3k.c` 的 `r3k_cache_size()` 本身就是一個現成的裸機量測 | gate R1d |
| `CPU-26` | loader 自己的例外處理 | 有 —— `Undefined Exception happen.`、`cp0_cause=%X, cp0_epc=%X`，`0x8040A5C0` 有 16 筆分派表指向 `0x80400DA0`–`0x80401BDC` | 讀 | 讀 | A | `docs/loader-command-semantics.md` §9 |
| `CPU-27` | `<RealTek>` 提示字元時的 `Status.BEV` | *(留白)* —— 沒追過 | — | — | — | gate R1d |
| `CPU-28` | 對建置旗標的後果 | 用 `-march=mips1`。**`-march=mips32` 會安靜地編錯** —— 不 fault、不警告 | 推 | — | 由 `CPU-14` 推出 | `plan/` §3.4、`CLAUDE.md` |

## 3. 記憶體 —— SDRAM

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `MEM-01` | 型號 | **Winbond W9825G6KH-6** —— 256 Mbit，16M × 16 | 量 | 讀 | P；`-6` 解碼為 6 ns / 166 MHz 速度等級 | `upstream/notes/hardware-inspection.md` §3 |
| `MEM-02` | 絲印／日期碼 | `Winbond · W9825G6KH-6 · 1837H · 6824506000` —— 2018 年第 37 週，全板最新的一顆 | 量 | 推 | P | 同上 §6 |
| `MEM-03` | 匯流排寬度 | **16 bit** | 量 | 讀 | 開機 banner 的 `[16bit]`，且這顆本身是 ×16 | `upstream/notes/uart-findings.md` §2 |
| `MEM-04` | 實裝容量 | **32 MiB** | 量 | 量 | **×2** —— P，以及 loader 的 `ramSize: 32M` | 同上 |
| `MEM-05` | loader 偵測到的 | `32M` | 量 | — | C、S | `bench/2026-08-23/A-catch.log` |
| `MEM-06` | Linux 實際拿到的 | **26,052 kB**（25.4 MiB） | 量 | — | C —— 在運行中的裝置上讀 `/proc/meminfo` | `upstream/test-ledger.md` `P5-5` |
| `MEM-07` | 記憶體控制器 | `MCR`，`0xB8001000` | 讀 | 讀 | D §7.4.1 | `SOURCES.json` |
| `MEM-08` | SDRAM timing 設定 | *(留白)* —— loader 設的，從沒讀出來過 | — | — | — | gate R5 |
| `MEM-09` | 上電 strapping 腳 | 是 DRAM 那幾支 —— `MA[10:8]` 在 44/52/53，`RAS#`/`CAS#` 在 51。**不是 `SF_*` 那幾支** | 讀 | 讀 | D §6.1 | `notes/power-and-programmer.md` §3 |
| `MEM-10` | 暖重置後 SDRAM 內容是否存活 | *(留白)* —— 若存活，它就是 `C-8` 不依賴 `WatchDogIND` 的第二個鑑別器：暖重置後 scratch 字還在、冷開機後不在 | — | — | `D2b` 讀 `0x81000000` 是不是還等於 `C1` 寫的 `DEADBEEF CAFEBABE`，再用 `D3` 的冷開機當否證 | `RUNSHEET.md` `D2b`、`C-8` |

## 4. Flash

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `FLS-01` | 型號 | **Eon（cFeon）EN25QH32B**，SOP-8，板上編號 `U19` | 量 | 讀 | P | `upstream/notes/hardware-inspection.md` §1 |
| `FLS-02` | 絲印／日期碼 | `cFeon · QH32B-104HIP · X703811 · 1750HKB` —— 2017 年第 50 週 | 量 | 推 | P | 同上 |
| `FLS-03` | 容量 | **4 MiB / 32 Mbit** | 量 | 量 | **×3** —— P、JEDEC 容量位元組、`0x350000` 讀回全 `FF` | 同上、`upstream/notes/flash-layout.md` |
| `FLS-04` | **JEDEC ID** | **`0x1C7016`** —— 廠商碼 `0x1C`（Eon），容量位元組 `0x16` = 2²² | 量 | 讀 | S `B2`，2026-08-23，**同一次輸出裡帶四個事前算好的控制** | `RUNSHEET.md` `B2`、`docs/loader-flash-write.md` |
| `FLS-05` | 封裝本體寬度 | **150 mil** | 量 | — | **×1** —— 一把尺，對照前一天凍結的預測。**沒有留下 artefact**，沒人能覆核 | `upstream/notes/hardware-inspection.md` §1 |
| `FLS-06` | sector 大小 | `0x1000`（4 KiB） | 量 | 推 | 值在裝置上的描述子 `+24` 讀到 —— 但它來自 loader 的**未知晶片 fallback**，不是來自這顆 flash | `docs/loader-flash-write.md` §2 |
| `FLS-07` | page 大小 | `0x100`（256 B） | 讀 | 推 | A —— fallback 的字面值 | 同上 |
| `FLS-08` | block 大小 | `0x10000`（64 KiB） | 量 | 推 | 描述子 `+16`；同樣是 fallback | 同上 |
| `FLS-09` | loader 認定的容量 | `0x00400000` = `1 << 22` | 量 | 讀 | 描述子 `+12`；**這是給不認得的晶片用的寫死預設值**。對這台正確純屬巧合 | 同上 |
| `FLS-10` | loader 的晶片表 | 32 筆，`0x20` 間距，在 `stage2` 的 `0x0d764`。**沒有一筆對得上 `1c7016`** → banner 印 `chipName: UNKNOWN` | 讀 | 讀 | A、C | `upstream/notes/loader-chip-table.md` |
| `FLS-11` | 記憶體映射視窗 | **`0xBD000000`**（KSEG1，非快取） | 量 | 讀 | loader 執行 `FLW` 時自己印出 `offset 0x003f0000<0xbd3f0000>` | `upstream/notes/uart-pinout.md` §4 |
| `FLS-12` | loader 用的第二個映射 | `0xB8000000 + 偏移`，`check_image()` 用 `lhu`/`sh` 成對搬 | 讀 | 讀 | A | `docs/loader-command-semantics.md` §a |
| `FLS-13` | 實際的抹除粒度 | `FLW` **整組命令裡沒有 erase**，而且寫 `FF` 真的能讓它回到 `FF`，所以它一定自己在抹 —— 指向 4 KiB sector 的 read-modify-erase-program 循環 | 量（行為） | 推 | C | `upstream/notes/uart-pinout.md` §4 |
| `FLS-14` | 完整 dump | 4,194,304 bytes，`sha256 a800059a…10f37ea`，用 `FLR`+`DB` 花 105 分鐘讀完，**0 次區塊重讀** | 量 | — | C | `upstream/notes/dump-vs-official.md` §1 |
| `FLS-15` | flash 的第二支儀器 | *(留白)* —— 從來沒有燒錄器讀過這顆 | — | — | — | `notes/power-and-programmer.md` §4，`⊘` |
| `FLS-16` | 夾具供電下的 `VCC` | **1.70 V**，穩定，三種供電組態都一樣 | 量 | — | C `T-85` | `notes/power-and-programmer.md` §1 |
| `FLS-17` | 同一次的 `WP#` / `HOLD#` | **1.79 V** —— 比 `VCC` **高** 90 mV，所以整片板的 3.3 V 網路本身就在 1.79 V | 量 | 讀 | C `T-85` + 這顆的腳位功能 | 同上 §2 |
| `FLS-18` | SPI 命令集 | `WREN 06` `WRDI 04` **`RDID 9F`** `RDSR 05` `WRSR 01` `READ 03` `FASTREAD 0B` `SE 20` `BE D8` `CE 60` `PP 02` `DP B9` `RDP AB` | 讀 | 讀 | B，而 `RDID` 的值 D 自己的範例也再說一次 | `docs/loader-flash-write.md` §2 |

## 5. 乙太網路 —— 交換器、PHY、埠

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `NET-01` | 交換器 | 5 埠 10/100，整合在 SoC 裡 | 量 | 讀 | 開機 log 的五個介面、板上三顆網路變壓器、D | `upstream/notes/hardware-inspection.md` §7.1 |
| `NET-02` | 網路變壓器 | `U&T UTH20T02M` ×2（各兩埠）+ `UTH16T01M` ×1；日期碼 `1818` | 量 | — | P | 同上 |
| `NET-03` | 網路孔 | **4 × LAN（橘）+ 1 × WAN（黃）** | 量 | — | P | 同上 |
| `NET-04` | 埠 ↔ 介面 ↔ VLAN | `eth1` 埠 0 vid **8**（WAN，別名 `peth0`）· `eth4` 埠 1 · `eth3` 埠 2 · `eth2` 埠 3 · `eth0` 埠 4，後四者都是 vid **9** | 量 | 讀 | C —— 廠商 kernel 自己的開機行、member port 位元遮罩 | `upstream/dumps/uart-boot.log` |
| `NET-05` | 會回應 MDIO 的 PHY 位址 | **0、1、2、3、4** | 量 | 量 | S `E4`、`E7`、`E8` —— 這台裝置有史以來第一批 MDIO 交易 | `RUNSHEET.md` `E4`–`E8` |
| `NET-06` | PHY 識別碼 | **`0x001CC880`**（MII reg 2 = `0x001C`，reg 3 = `0xC880`），**五個位址完全相同** | 量 | 讀 | S。**沒有任何來源預測得出這個值** —— 它是一次量測，不是一次確認 | `docs/loader-phy-and-switch.md` §6 |
| `NET-07` | 位址 1 | 回同一個識別碼 → loader 的 `PORT1` 跳過位址 1 是**關於埠**，不是關於 PHY。一支驅動涵蓋五個 | 量 | 推 | S `E8` | `RUNSHEET.md` `E8` |
| `NET-08` | 位址 5–31 | *(留白)* —— `F1`/`F2` 未跑，而 `F1` 正是那格會終結一次上機的 | — | — | — | `RUNSHEET.md` §F |
| `NET-09` | `ExtPHYID` 對應表 | `PCRP0`–`PCRP4` 的 bit 30:26 讀到 **0、1、2、3、4** | 量 | 讀 | S `E9` + D Table 64 | `docs/loader-phy-and-switch.md` §7 |
| `NET-10` | `0xBB804118` / `0xBB80411C` | `0x00000000` / `0x187F0038` —— 後者 bit 30:26 = **6**。照 `PCRP` 每埠 4 位元組的間距推下去，這兩個就是 `PCRP5` 與 `PCRP6` | 量 | 推 | S `E9`。**間距是推的；手上沒有任何來源明寫這兩個位址**。`E9` 的判讀只涵蓋到第 6 個字，這兩個字是同一份 transcript 裡沒被寫下來的部分 | `RUNSHEET.md` `E9` |
| `NET-11` | `PSRP` 位元配置 | 8 `LinkDownEventFlag`（閂鎖，讀取即清）· 7 NWayEnable · 6 RxPause · 5 TxPause · **4 LinkUp** · 3 Duplex · 1:0 速度（`01` = 100M） | 讀 | 讀 | B 給 7:0 的內容；D Table 65 確認 bit 8 與該欄位 | `docs/loader-phy-and-switch.md` §7 |
| `NET-12` | 連線狀態，量到的 | `PSRP0`–`PSRP4` = `10E0 10E0` **`1099`** `10E0 10E0` —— **恰好一埠 up**，100M 全雙工 | 量 | 讀 | S `E10`，並由對端 Windows 回報 `Up, 100 Mbps` 在裝置外佐證 | `RUNSHEET.md` `E10` |
| `NET-13` | 哪一個 RJ45 是哪一個埠號 | *(留白)* —— `E11` 要拔插網路線 | — | — | — | `RUNSHEET.md` `E11` |
| `NET-14` | 讀到的 MII 暫存器 | `BMSR` 有連線 `0x78ED` / 無連線 `0x78C9` · `BMCR` `0x1100` · `ANLPAR` `0xC1E1` | 量 | 讀 | S `E12`，名稱來自 MII 標準 | `RUNSHEET.md` `E12` |
| `NET-15` | MDIO 控制器 | `MDCIOCR` `0xBB804004` —— bit 31 `COMMAND`、`PHYADD[4:0]` 28:24、`REGADD[4:0]` 20:16、`WRDATA[15:0]` 15:0 · `MDCIOSR` `0xBB804008` —— bit 31 `STATUS`、`RDATA[15:0]` | 讀 | 讀 | **×3** —— A、B（`asicregs.h` 與 `rtl8651_getAsicEthernetPHYReg()`）、**D Table 57–59** | `docs/loader-phy-and-switch.md` §1 |
| `NET-16` | 一次 MDIO 讀取**不是**唯讀 | `phy_read()` 會寫 `MDCIOCR`，**而且會設 `GIMR` bit 8**，且從不還原 | 讀 | 讀 | A，並在裝置上以因果方式確認 | 同上 §2、`RUNSHEET.md` `C5` |
| `NET-17` | MDIO 等待沒有 timeout | `0x80402FD8` 的 `bltz v1`，沒有 timeout、沒有迴圈上限。一個永不回應的位址會終結整次上機 | 讀 | 讀 | A | 同上 §1 |
| `NET-18` | MDIO 的 erratum 延遲 | **每一次**讀取都 `delay(10)`，而且沒有版本判斷 —— B 把同一個延遲關在 `RTL8196C_REVISION_A` 之後 | 讀 | 讀 | A + B | 同上 §1 |
| `NET-19` | `PITCR` `0xBB804100` | 讀到 **`0x00000000`** = `UTP (10/100M embedded PHY)`。會把 bit 0 設起來的那段 strap 分支，**在這片板上沒有跑** | 量 | 讀 | S `E9` + D Table 63 | 同上 §7 |
| `NET-20` | `PCRP0` | `0x007F0039` —— `EnForceMode` 是 0，所以 loader 的 force-mode 設定同樣沒跑 | 量 | 讀 | S `E9` + D Table 64 | 同上 §7 |
| `NET-21` | loader 碰過的交換器暫存器 | 48 個 `lui …,0xbb80` 站點收斂成 13 個相異位址，**全部落在 `0xBB804xxx`**：`4000 MACCR` · `4004 MDCIOCR` · `4008 MDCIOSR` · `4100 PITCR` · `4104 PCRP0` · `414C P0GMIICR` · **`4234` 無名** · `4418 SWTCR0` · `4428 FFCR` · `4A08 PVCR0` · `4D00 SWTACR` · `4D08 SWTAA` · `4D3C TCR7` | 讀 | 混合 —— 4 個有 D + B，8 個只有 B，**1 個兩者皆無** | A | 同上 §7、`C-15` |
| `NET-22` | `0xBB802xxx`（B 的 MII 記憶體映射影子） | **這顆不能用** —— D 沒有這個區塊，而且 loader 那 48 個站點沒有一個落在裡面 | 讀 | 讀 | A + D | `docs/loader-phy-and-switch.md` §7 |
| `NET-23` | 網卡驅動怎麼稱呼這顆 | `chip name: 8196C, chip revid: 0` —— **錯的，而且它自己在兩行前就自我否定**：它宣告自己正在探測 RTL8186 | 量 | — | C | `upstream/notes/uart-findings.md` §2 |

## 6. 無線電

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `RF-01` | 型號 | **Realtek RTL8188ER** —— 1T1R 802.11n，2.4 GHz，獨立一顆 | 量 | 讀 | **×1 —— 只有 P。** 驅動 banner 印的是版本，不是料號 | `upstream/notes/hardware-inspection.md` §4 |
| `RF-02` | 絲印 | `RTL8188ER · I210QP1 · GF08` | 量 | — | P | 同上 |
| `RF-03` | 驅動 banner | `Realtek WLAN driver - version 1.6 (2013-02-21)`、`Adaptivity function - version 7.1` | 量 | — | C | `upstream/dumps/uart-boot.log` |
| `RF-04` | 它怎麼接到 SoC | *(留白)* —— 從沒追過 | — | — | — | gate R10d |
| `RF-05` | 天線 | 絲印上有 `ANT1` 與 `ANT2`；**只裝一支**，一條線走到板子右緣 | 量 | 推 | P | `upstream/notes/hardware-inspection.md` §7.3 |
| `RF-06` | 校正資料 | 在 flash `0x006000` 的 `H601` 裡。**回復原廠設定不會還原它** —— 永久禁寫 | 讀 | 讀 | A、C | `plan/` D4、`CLAUDE.md` |
| `RF-07` | WPS | 開機時就活著 —— `WiFi Simple Config v2.18-wps1.0` | 量 | — | C | `upstream/notes/uart-findings.md` §3 |

## 7. 板子 —— 電源、連接器、排針

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `BRD-01` | 穩壓器 | `LSC · LSP5526 · 181525`，8 腳，旁邊有 `D3`。**未識別**；降壓只是從位置推的。輸出腳從沒量過 | 量（油墨） | 推 | **×1** | `upstream/notes/hardware-inspection.md` §5 |
| `BRD-02` | 外部供電 | **只有一條 3.3 V**；核心 1.0 V 由內建 SWR 或 LDO 產生 | 讀 | 讀 | D §1 | `notes/power-and-programmer.md` §2 |
| `BRD-03` | 電源輸入 | 板子左上角的圓形插孔，旁邊有一顆按鈕 | 量 | — | P | `upstream/notes/hardware-inspection.md` §7.1 |
| `BRD-04` | `J2` | 緊鄰插孔的 2 腳排針；機殼開關的辮子線插在這裡。**「串在 DC 迴路上」是從照片來的佈局推論**，用通斷檔就能定案 | 量 | 推 | P | 同上 §7.4 |
| `BRD-05` | 那顆按鈕 | *(留白)* —— `RESET#` 還是 GPIO，未定。三個「沒有」指向 `RESET#`，而三個沒有不等於一條線 | — | — | — | `C-14`、`RUNSHEET.md` `D3` |
| `BRD-06` | `RESET#` | SoC 第 49 腳，**與 `LED_PORT3` 和 `GPIOB[5]` 共用** —— 所以在這個設計上它可能是一支 LED 驅動腳 | 讀 | 讀 | D §6、§6.1 | `notes/power-and-programmer.md` §3 |
| `BRD-07` | `SF_CS0#` / `SF_SCK` | 第 45 與 48 腳，是 SoC 的**輸出**。D 沒有任何一句說它們在 `RESET#` 拉低時會 tri-state | 讀 | 讀 | D | 同上 §3 |
| `BRD-08` | UART 排針 | 4 腳 2.54 mm，**出廠就焊好**，絲印寫 `UART`，在板子下緣 LED 排旁邊。**整個 W02 沒有任何一處需要焊接** | 量 | 量 | P + 逐腳掃描 | `upstream/notes/uart-pinout.md` |
| `BRD-09` | UART 腳位 | 第 1 腳 **`VCC 3.3 V`** · 2 **`TX`**（板 → 你）· 3 **`RX`** · 4 **`GND`** | 量 | 量 | 每腳兩個來源；`RX` 是在 ESC 打進去中斷了開機之後才從論證變成量測 | 同上 §1、§5 |
| `BRD-10` | 主控台參數 | **38400 8N1**，邏輯準位 **3.3 V** | 量 | 量 | 最窄脈衝 26 µs 對 38400 的 26.042 µs（差 0.16%），再用同一份 capture 裡的 52 µs 脈衝自我檢查，最後由解碼成可讀 ASCII 確認 | 同上 §2 |
| `BRD-11` | EJTAG | D 說是 5 訊號 P1149.1。**板上沒有定位過**，也沒有轉接器 | 文 | 讀 | D §1 | `upstream/docs/lab-inventory.md` §3 |
| `BRD-12` | 未貼裝的焊墊 | `U6` 周圍是空的。未調查 | 量 | — | P | `upstream/notes/hardware-inspection.md` §7.1 |

## 8. 位址地圖

除非另外標記，每一列都是「讀」；固定住多數位址的是 loader 自己的用法。

| id | 範圍／位址 | 是什麼 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `MAP-01` | `0x80000000` | KSEG0 —— 快取的 RAM | 文 | 文 | MIPS 架構。**這個 repo 裡沒有任何檔案擁有這一列** —— `spec-check.py` 的 C5 就是這樣找出來的 | — |
| `MAP-02` | `0xA0000000` | KSEG1 —— 非快取別名。**loader 自己跑在這裡**：它在 `0x804004a8` 跳到自己下一條指令的 KSEG1 別名 | 讀 | 讀 | A | `notes/cache-model.md` |
| `MAP-03` | `0xB8000000` | SoC 周邊暫存器空間 | 讀 | 讀 | A + D | `plan/` F7 |
| `MAP-04` | `0xB8001000` | 記憶體控制器（`MCR`） | 讀 | 讀 | D §7.4.1 | `SOURCES.json` |
| `MAP-05` | `0xB8001200` | SPI flash 控制器 | 讀 | 讀 | **×3** —— A、B、D §7.4.5–7.4.9 | `docs/loader-flash-write.md` §2 |
| `MAP-06` | `0xB8002000` | UART（DLAB 切換在 `0xB8002100`/`2000`） | 讀 | 讀 | D §9.3、A | `SOURCES.json` |
| `MAP-07` | `0xB8003000` | 中斷控制器 | 讀 | 讀 | D §8.1、A、S | 見 §10 |
| `MAP-08` | `0xB8003100` | 計時器／看門狗 | 讀 | 讀 | D §8.2、E、A、S | 見 §10 |
| `MAP-09` | `0xB8003500` | GPIO —— `PABCD_CNR 3500`、`PABCD_DIR 3508`、`PABCD_DAT 350C` | 文 | 讀 | D §8.3。**本專案從未碰過** | `SOURCES.json` |
| `MAP-10` | `0xB8B01000` | PCIe host 模式。**不是網路 MAC** | 文 | 讀 | D §10.3 | `SOURCES.json` |
| `MAP-11` | `0xBB804000` | 交換器核心 | 讀 | 讀 | A + D §11.1 | `docs/loader-phy-and-switch.md` §7 |
| `MAP-12` | `0xBD000000` | SPI flash 的記憶體映射，KSEG1 | 量 | 讀 | loader 自己在 `FLW` 那行印的 | `upstream/notes/uart-pinout.md` §4 |
| `MAP-13` | `0xBFC00000` | reset 向量 —— `J BFC00000` 就是重置命令 | 讀 | 讀 | A | `docs/loader-command-semantics.md` §f |
| `MAP-14` | `0x80400000`–`0x8040DD10` | loader 自己的映像與 `.data`；`.bss` 從 `0x8040DD10` 起，堆疊在其下 | 讀 | 讀 | A；載入基底是從指標序列還原出來的，不是假設的 | `upstream/notes/loader-chip-table.md` §1 |
| `MAP-15` | `0x80500000` | 這台的 kernel 映像被搬去的位置 —— 就是它自己容器標頭裡的 `startAddr` | 量 | 讀 | S `B3`/`B4` + A | `RUNSHEET.md` `B3` |
| `MAP-16` | `0x81000000` | *(選定)* bench 用的 scratch —— 進 SDRAM 16 MiB，遠離 loader 與已就位的 kernel | — | — | 這是選的，不是裝置性質 | `RUNSHEET.md` §C |

## 9. 在這台裝置上讀過或寫過的暫存器

**只有真的有讀數的列才標「量」。** 值欄是這台在 `<RealTek>` 提示字元下回的東西，
未特別註明者皆為 2026-08-23。

| id | 位址 | 名稱 | 讀數 | V | N | 來源 | 擁有者 |
|---|---|---|---|:-:|:-:|---|---|
| `REG-01` | `0xB8003000` | `GIMR` | `0x00008100` —— 在提示字元下 **bit 8 `TCIE` 與 bit 15 `SWIE` 就已經是 1** | 量 | 讀 | S `E3`、D、B | `docs/loader-phy-and-switch.md` §2 |
| `REG-02` | `0xB8003004` | `GISR` | `0x88000004`；看到 bit 8 `TCIP` 在被遮住時閂鎖、遞送之後清掉 | 量 | 讀 | S `C5` | `RUNSHEET.md` `C5` |
| `REG-03` | `0xB800300C` | `IRR1` | `0x30050004` —— loader 寫的是 `0x00050004`；bit 28 的 `SWIRS` = 3 | 量 | 讀 | S `E3` + A | 同上 |
| `REG-04` | `0xB8003010` | `IRR2` | *(未讀)* | — | 讀 | D | — |
| `REG-05` | `0xB8003100` | `TC0DATA` | `0x0022E0A0` = 142,858 << 4 —— **所以計數欄位是 bit 31:4** | 量 | 量 | S `E2b` + A 的編譯進去的值 | `docs/loader-phy-and-switch.md` §2 |
| `REG-06` | `0xB8003104` | `TC1DATA` | `0x00000000` | 量 | 讀 | S `E2b` + `SOURCES.json` 的位移表 | `RUNSHEET.md` `E2b`、`SOURCES.json` |
| `REG-07` | `0xB8003108` | `TC0CNT` | `0x0010B960` | 量 | 讀 | S `E2b` + `SOURCES.json` 的位移表 | `RUNSHEET.md` `E2b`、`SOURCES.json` |
| `REG-08` | `0xB800310C` | `TC1CNT` | `0x00000000` | 量 | 讀 | S `E2b` + `SOURCES.json` 的位移表 | `RUNSHEET.md` `E2b`、`SOURCES.json` |
| `REG-09` | `0xB8003110` | `TCCNR` | `0xC0000000` —— 與 `timer_init` 寫的完全一樣 | 量 | 讀 | S `B7` + A | `RUNSHEET.md` `B7` |
| `REG-10` | `0xB8003114` | `TCIR` | `0x80000000` | 量 | 讀 | S `B7` + A | 同上 |
| `REG-11` | `0xB8003118` | `CDBR` | `0x000E0000` —— 除頻欄位 **14** | 量 | 讀 | S `B7` + A + D | 同上 |
| `REG-12` | `0xB800311C` | `WDTCNR` | `0xA5000000` —— `WDTE[7:0]` = `0xA5`，**停止**樣式；**上電重置後 `WatchDogIND` bit 20 = `0`**。🔴 **這是硬體 reset 預設值，不是 loader 寫的**：2026-08-24 桌面查證，loader 對 `WDTCNR` 只有兩個寫入點（`0x804012F8`、`0x804092E8`），兩個都是 `sw zero` 後緊接自跳迴圈，之後沒有任何指令執行。`B7` 原本的判讀暗示相反，已更正 | 量 | 讀 | **×4** —— S `B7`、D §8.2.9 Table 27、E、B | `RUNSHEET.md` `D2`、`docs/loader-command-semantics.md` §f |
| `REG-13` | `0xB8001200`–`0x1210` | `SFCR` `SFCR2` `SFCSR` `SFDR` `SFDR2` | *(未讀 —— 從沒在裝置上讀過)* | — | 讀 | **×3** —— A（`SFCSR` 19 處參照、`SFDR` 14 處）、B、D | `docs/loader-flash-write.md` §2 |
| `REG-14` | `0xB8001208` bit 27 | `SPI_RDY` | *(未讀)* —— 但**這台自己的 `ComSrlCmd_RDID()` 就是在等這個位元**，那是程式碼倚賴語意，比一份文件宣稱語意更硬 | — | 讀+ | A + D table 10 | 同上 |
| `REG-15` | `0xBB804100` | `PITCR` | `0x00000000` | 量 | 讀 | S `E9` + D Table 63 | `docs/loader-phy-and-switch.md` §7 |
| `REG-16` | `0xBB804104`–`0x4114` | `PCRP0`–`PCRP4` | `007F0039` `047F0039` `087F0039` `0C7F0039` `107F0039` | 量 | 讀 | S `E9` + D Table 64 | 同上 |
| `REG-17` | `0xBB804128`–`0x4138` | `PSRP0`–`PSRP4` | `10E0` `10E0` **`1099`** `10E0` `10E0` | 量 | 讀 | S `E10` + D Table 62 + B | 同上 |
| `REG-18` | `0xBB80413C` | B 稱 `PSRP5`；**D 的 Table 62 跳過 `0x3C`** | `0x000000E2` | 量 | — | S `E10`；兩份文件不一致，而 D 是這顆 | `RUNSHEET.md` `E10`、`docs/loader-phy-and-switch.md` §7 |
| `REG-19` | `0xBB804140` | D 稱 `PSRP6` | `0x0000007A` | 量 | 讀 | S `E10` + D Table 62 | `RUNSHEET.md` `E10` |
| `REG-19b` | `0xBB804144` | 依 `PSRP` 間距是下一埠；**沒有來源明寫** | `0x0000007A` | 量 | 推 | S `E10` | `RUNSHEET.md` `E10` |
| `REG-20` | `0x8040DBC0` | loader 命令表的 `?` 那一列 | `8040B070 00000000 80409A9C 8040B074` —— 名稱指標、`argc`、handler、說明指標，16 位元組間距 | 量 | 讀 | S `B1` —— 這是整份 runsheet 其他位址的全域控制 | `RUNSHEET.md` `B1` |
| `REG-21` | `0x8040FBD4` | flash 晶片描述子 | `001C7016 1C701600 16000000 00400000 / 00010000 00000040 00001000 00000400` | 量 | 讀 | S `B2` + A | `docs/loader-flash-write.md` §2 |
| `REG-22` | `0x8040DBA4` | `gCHKKEY_HIT` | 從上電前就串流 ESC 時是 **`1`** —— 於是 `check_image()` 短路，checksum 迴圈從沒跑過 | 量 | 讀 | S `B5` + A + B | `C-13`、`C-16` |
| `REG-23` | `0x8040D4A0` | `AUTOBURN` | **上電後 `1`** —— 提示字元下自動燒錄是**開著的**；🔄 **`AUTOBURN 0` 之後量到 `0`**（`C6`），而**每一次重置都會把它打回 `1`** | 量 | 讀 | S `B6`、`C6` + A 的初始值 | `RUNSHEET.md` `B6`、`C6` |
| `REG-24` | `0x8040DD3C` | 正在測試的候選偏移，偏置 `0x05000000` | `0x05060000` —— **值對了而判讀被否證**：它存的是**正在試**的候選，不是被接受的那個 | 量 | 讀（已更正） | S `B3` + A | `RUNSHEET.md` `B3` |
| `REG-25` | `0x8040DCE8` | 計時器 tick 計數 | 61.842 秒內 `0x0000473A` → `0x00005F52` | 量 | 讀 | S `E1`/`E2` + A | `docs/loader-phy-and-switch.md` §2 |

## 10. 時脈、計時器、看門狗、中斷

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `CLK-01` | CPU 時脈 | **400 MHz** | 量 | — | banner、D | `bench/2026-08-23/A-catch.log` |
| `CLK-02` | 計時器基底時脈 | **量到 199.48 MHz**，對照編譯進去的 `0x0BEBC200` = 200,000,000 —— 差 **0.26%** | 量 | 讀 | 由三個在矽片上讀到的項推導：tick、`CDBR`、`TC0DATA` | `docs/loader-phy-and-switch.md` §2 |
| `CLK-03` | 它與 `CLK-01` 的關係 | *(留白)* —— ÷2 是最明顯的讀法，而它沒有被量過 | — | — | — | gate R1 |
| `CLK-04` | 計時器 tick | **99.74 Hz**，對照上機前預測的 100.0 Hz | 量 | 讀 | S `E2`，61.842 秒內 6,168 個計數 | 同上 |
| `CLK-05` | `delay(10)` | 一個 tick = **10 ms**，與 B 的 `mdelay(10)` 相符 | 讀 | 讀 | A + B | 同上 |
| `CLK-06` | 除頻欄位的語意 | `CDBR` 的 14 就是除數本身 —— 若是 15，基底會變成 213.7 MHz，那不是任何人會做的時脈 | 量 | 推 | 推導 | 同上 |
| `CLK-07` | 看門狗逾時選擇 | `OVSEL[3:0]` = `0000` = 2¹⁵ 個基底時脈 tick —— 十個檔位裡最短的 | 讀 | 讀 | D Table 27 | `docs/loader-command-semantics.md` §f |
| `CLK-08` | 看門狗的實際牆鐘時間 | *(留白 —— 但 `D4` 這次上機就填得到)* —— 以 `CLK-02` 量到的 199.48 MHz 算，`J BFC00000` 選中的 `OVSEL`=`0000` 是 2¹⁵ tick = **164 µs**（未除頻）或 **2.30 ms**（經 `CDBR` ÷14），兩者都遠低於任何儀器的解析度，CP2102 的 latency timer（典型 1–16 ms，這裡沒量過）還是另一層地板。**但十檔裡最長的 `OVSEL`=`1001`（2²⁴）是 84.1 ms 或 1.177 s —— 兩個都在解析度之上，而且相差 14×。** 原本這一列寫「十檔全部量不到」，那是把最短那檔的結論套到了全部十檔上 | — | 讀 | `D` Table 27 的欄位編碼 × `CLK-02` | `C-8`、`RUNSHEET.md` `D4` |
| `CLK-09` | 上電後的 `WatchDogIND` | **`0`** | 量 | 讀 | S `B7` + D | `RUNSHEET.md` `B7` |
| `CLK-10` | 看門狗重置後的 `WatchDogIND` | *(留白)* —— `D2` 預測整個字讀 **`A5100000`**。若讀回 `A5000000`，這個位元撐不過它自己回報的那次重置，**`C-8` 就失去這個鑑別器**，改用 `MEM-10` | — | 讀 | — | `C-8`、`RUNSHEET.md` `D2` |
| `CLK-11` 🆕 | 誰寫過 `WDTCNR` | **loader 從來沒寫過它，除了兩處 `sw zero` 之後原地死迴圈** —— `0x804012F8`（`reboot.......` 那條路）與 `0x804092E8`（`J BFC00000`）。所以 `B7` 量到的 `A5000000` 是**硬體重置預設值**，不是 loader 寫進去的，而 `D2` 的路徑上沒有任何軟體，它直接讀硬體 | 讀 | 讀 | A，三種搜法互補：`0x311c` 立即值（2 筆）、`TC_BASE 0x3100`＋位移 28（0 筆）、非 `sp` 的 `sw …,28(reg)`（3 筆，全落在別的周邊）。**正控制：同一個方法找得到 `0x80408F34` 的 `CDBR = 0x000E0000`，而那個值 `B7` 在裝置上量到過** | `RUNSHEET.md` `D2` |
| `IRQ-01` | IRQ 15 | `eth0` —— loader 的 TFTP 是中斷驅動的，handler 在 `0x804023B0` | 讀 | 讀 | C，靜態 + 暫存器讀回 | `plan/` F40 |
| `IRQ-02` | IRQ 8 | `timer` | 讀 | 讀 | C | 同上 |
| `IRQ-03` | IRQ 27 | `SPEED` | 讀 | — | C | 同上 |
| `IRQ-04` | 一個計時器中斷需要的四層 | `Status.IM[7:2]` 未遮罩且 `BEV` 清掉 · `Status.IE` = 1 · `TCCNR`/`TCIR` 已武裝 · `GIMR` bit 8 | 讀 | 讀 | A。**第 4 層原本寫的值是錯的，是量測改正了它** —— 見 `REG-01` | `docs/loader-phy-and-switch.md` §2 |

## 11. 開機載入器

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `LDR-01` | Banner | `---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)` —— 2026-08-17、-18、-23 三次逐位元組相同 | 量 | — | C、S | `bench/2026-08-23/A-catch.log` |
| `LDR-02` | 第二階段 | `stage2.bin`，56,592 bytes，`sha256 f88869d1…c9c1b4ee`，載入基底 **`0x80400000`** | 讀 | 讀 | A；基底是從 `0x20` 間距的指標序列還原的，而還原器在 0 個或 2 個候選時都拒絕回答 | `upstream/notes/loader-chip-table.md` §1 |
| `LDR-03` | 命令集 | `?` 印出 **17 條** —— `HELP` 自己反而回 `Unknown command !` | 量 | 量 | S，且靜態還原的表與裝置逐行相同 | `bench/2026-08-23/A-catch.log` |
| `LDR-04` | 命令表 | 在 `0x8040DBC0`，16 位元組間距，`{name*, argc, handler, help*}` | 量 | 讀 | S `B1`、`B9` + A | `RUNSHEET.md` `B1` |
| `LDR-05` | 大小寫 | **不敏感** —— dispatcher 先跑 `strupr` | 讀 | 讀 | C | `plan/` F37 |
| `LDR-06` | 斷詞器 | 20 個槽，**只用空白**當分隔，每行把所有槽清零，而且**先存 `argv[i]` 再測分隔字元** —— 所以**一個前導空白會讓 `argv[0]` 變成空字串** | 讀 | 讀 | A `0x80407248`，並在 2026-08-23 於裝置上實際引爆 | `docs/loader-command-semantics.md` §f |
| `LDR-06b` | 一行能載多少 | 🔄 **2026-08-24 更正，被 `LDR-06c` 推翻。** 斷詞器的 20 個槽不是綁束條件，**行緩衝的 128 bytes 才是**：`EW <addr> ` 佔 12 字元，每個值 9 字元，所以 `11 + 9n < 128` → **一行 12 個字 = 48 bytes，119 個字元**。1 KiB 的裸機探針要 **22 行，不是 15 行**。原本那句只算了槽數 | 量 | 讀 | S `A-catch` + A（斷詞器與行讀取器兩處） | `RUNSHEET.md` `C7`、`docs/loader-command-semantics.md` §f |
| `LDR-06c` | loader 的輸入行緩衝長度 | **128 bytes** | 量 | 讀 | **×2** —— S：`A-catch` 裡剛好 128 個 ESC 後回 `Unknown command !`，**同一個數字七次**；A：命令迴圈 `0x80409190` 的 `memset(buf,0,128)` 與 `0x804091A0` 的 `readline(buf,128,1)` | `docs/loader-command-semantics.md` §f |
| `LDR-06d` 🆕 | 🔴 **剛好 128 個字元的行沒有終止符** | `readline`（`0x8040708C`）三個出口只有 CR 那條寫 NUL（`0x804070FC`）；LF 那條與長度到底那條（`0x80407194`，`count < 128`）都不寫。呼叫端的 `memset` 只救得了**短於** 128 的行，因為那才留得下零。**所以斷詞器（`0x80407248`）會掃過 `sp+143`，進到 8 bytes 堆疊空隙，再進到存起來的 `s0`（`sp+152`）**。堆疊框 184 bytes，緩衝在 `sp+16` | 讀 | 讀 | A | 同上 |
| `LDR-07` | `DB` / `DW` 的進位陷阱 | 位址十六進位，**長度十進位**。`DW` 數的是「字」，一行四個，而且在 bit 31 為 0 時會把位址強制推進 KSEG0 | 量 | 讀 | S `B8`（`A` 沒有任何輸出）、`B9`（`10` 印三行）+ A | `RUNSHEET.md` `B8`、`B9` |
| `LDR-08` | `EW` | 4 位元組寫入，**不做邊界檢查**，**完全靜默**，接受多個值並依序寫成連續的字，未對齊的位址會**向上**進位 | 量 | 讀 | 🔄 **2026-08-24 全部升成量測**：S `C1`（靜默、多值）、`C2`（依序落位）、**`C3`（`EW 81000102` 把值放到 `0x81000104`）** + A | `docs/loader-command-semantics.md` §f |
| `LDR-09` | `EB` | 1 位元組寫入，不檢查邊界，靜默，**完全不進位** —— **與 `LDR-08` 相反，而那個不對稱才是要記住的東西** | 量 | 讀 | 🔄 S `C4`（`EB 81000200 41 42 43` → 逐位元組落在 `…200/201/202`）+ A | 同上 |
| `LDR-10` | `EH` | **程式碼在 `0x804096F4`，但到不了** —— 它的表列在 B 裡被 `#ifdef REMOVED_UNUSED` 關掉，三種搜法都回 0，而同樣的搜法對照組分別回 32 與 2 | 讀 | 讀 | A + B | 同上 |
| `LDR-11` | 能寫任意記憶體的路徑 | **四條** —— `EB`、`EW`、`FLR` 的第一個參數（整個 flash 區段）、以及 `LOADADDR` 之後的 TFTP 寫入（MB 級） | 讀 | 讀 | A | 同上 |
| `LDR-12` | 六個 handler 未測 `argc` 就取用 `argv[0]` | `EB` `EW` `LOADADDR` `FLR` `PHYR` `PHYW` —— 其中任何一條不帶參數就打，代價是一次電源循環 | 讀 | 讀 | A、`loader-unpack.py --commands` | 同上、`RUNSHEET.md` 的禁打清單 |
| `LDR-13` | `PHYR`/`PHYW` 對 `MDIOR`/`MDIOW` | **四條命令三種參數慣例**，而且 `MDIOR` 的說明字串連自己的參數個數都寫錯：它只讀 `argv[0]`，用**十進位**解析，當成*暫存器*，然後自己掃 PHY 位址 | 讀 | 讀 | A。`MDIOR`/`MDIOW`/`PORT1` **只有 A 一個來源** —— B 裡的 `MDIOR` 是一條同名的 PCIe slave port 命令 | `docs/loader-phy-and-switch.md` §3 |
| `LDR-14` | `PORT1` | 一支**產測程式** —— 不讀 `argv`、不讀 `argc`，把一張 Gray code 表打進位址 `{0,2,3,4}` 的 PHY vendor 暫存器 19：**光是 payload 就 612 次寫入，外加周邊 272 次**，而且無法中止 | 讀 | 讀 | A；B 只佐證了 page select 的慣用寫法 | 同上 §4 |
| `LDR-15` | ESC 視窗 | **約 4.886 秒**，從 banner 到 `Jump to image start`，而且它在上電當下就開 —— ESC 必須在那之前就已經在串流 | 量 | — | C，2026-08-18 | `RUNSHEET.md` `A1` |
| `LDR-16` | 中斷手法的副作用 | 排隊的 ESC 會毒到**下一條**命令，讓它回 `Unknown command !`。先送一個裸 CR 讀到提示字元再說。🔄 **2026-08-24 第三次重現（`A0`），而重現它花掉了一格** —— 這條規則在這張表裡，卻**不在 `RUNSHEET.md` 的執行程序裡**，所以它被重新發現而不是被遵守。已寫進 seating 2 的程序 | 量 | 讀 | C、S（三次） | `upstream/notes/uart-pinout.md` §4、`RUNSHEET.md` seating 2 |
| `LDR-17` | 映像定位 | **它會掃。** 先固定試 `0x010000`/`0x020000`/`0x030000`，再以 `0x10000` 為步長掃 `[0x030000, 0x060000]` 並跳過那三個 —— 共六個候選。rootfs 則是 `0x0E0000`/`0x0F0000`/`0x130000` 再 `0x100000`/`0x110000`/`0x120000` | 讀 | 讀 | A + B 的 `check_image_header()` | `docs/loader-command-semantics.md` §a、`C-1` |
| `LDR-18` | `check_image()` | 在 `0x80407D50`：簽章 `cs6c` → 1、`cr6c` → 2，然後對 RAM 副本做 16 位元半字加總，必須為零。只有 `2` 能滿足呼叫端 | 讀 | 讀 | A + B | 同上 |
| `LDR-19` | 這個檢查是靜默的 | 這個 build **把 `no sys signature` / `sys checksum error` 編掉了**，卻留著 rootfs 的那兩句。當初把「字串不在」讀成了「檢查不在」 | 讀 | 讀 | A | 同上 |
| `LDR-20` | `doBooting()` | 在 `0x80408690`。**壞映像直接進救援提示字元 —— 不等 ESC，也不印任何訊息** | 讀 | 讀 | A，與 B 逐分支相符 | 同上、`C-4` |
| `LDR-21` | `gCHKKEY_HIT` | 在 `0x8040DBA4`。為 `1` 時 `check_image()` 直接回「沒有映像」。它唯一的寫入者讀 `0xB8002014` bit 24 與 `0xB8002000` 的最高位元組 —— 那是 UART 路徑，**但沒有對照 D 確認過** | 量（值） | 推（機制） | S `B5` + A + B | `C-13` |
| `LDR-22` | 是誰在任何 `FLR` 之前就填了 `0x80500000` | *(留白)* —— 提示字元下 RAM 就已經是 flash `0x060010` 的內容，而 `check_image()` **不可能**是填它的那個 | 量（那些位元組） | — | S `B4` | `C-16` |
| `LDR-23` | `AUTOBURN` | 初始值 `1`，全映像**只有一條指令**讀它（`0x80401B9C`），在上傳完成的路徑上。**上傳完成而事前沒打 `AUTOBURN 0`，就會被燒進 flash** | 量 | 讀 | S `B6` + A + C | `RUNSHEET.md` `B6` |
| `LDR-23b` | 關掉它的語法，以及它到底有沒有生效 | **`AUTOBURN 0`（空白，不是冒號）。有效。** 🔄 2026-08-24：`AUTOBURN: 0` → `Unknown command !`；`AUTOBURN 0` → `AutoBurning=0`；回讀 `0x8040D4A0` = `00000000`（`B6` 當時是 `00000001`）。**說明字串自己印的形式不是語法，在裝置上證實了**；`IPCONFIG:` 對 `IPCONFIG ` 是同型態的第二例 | 量 | 讀 | **×2** —— S `C6` 的回音（loader 說它以為的事）+ S `C6` 回讀 `0x8040D4A0`（`0x80401B9C` 那條指令實際會看的字） | `RUNSHEET.md` `C6`、`bench/2026-08-24/C6-rescue.json` |
| `LDR-24` | `LOADADDR` | 一個十六進位參數，**不檢查邊界、不確認**；全域在 `0x8040D3A8`，初始值 `0x80500000` | 讀 | 讀 | A | `docs/loader-command-semantics.md` §b |
| `LDR-25` | TFTP | 是**伺服器**不是客戶端；編譯進去的 IP 是 **`192.168.1.6`**，不必打 `IPCONFIG` 就會回應 | 讀 | 讀 | C，指令級 + 線上的 DATA opcode | `plan/` F42 |
| `LDR-26` | 兩個會繞過一切的檔名 | **`nfjrom` 與 `boot.img`** 會把載入位址強制成 `0x80000000`，並在傳輸結束當下直接執行 | 讀 | 讀 | C | `plan/` F44 |
| `LDR-27` | `burn()` | 在 `0x80401318` —— 它是映像解析器與分派器。接受八種區段簽章：`boot` `sqsh` `w6cp` `jw6c` `cwmp` `ksap` `ALL1` `ALL2` | 讀 | 讀 | A | `docs/loader-flash-write.md` §1 |
| `LDR-28` | `burn()` 的邊界 | **只有上界** —— 晶片描述子裡的容量，而且寫太長是被*截斷*而不是被拒絕。**下界根本不存在**，而 `boot` 是它接受的簽章之一 | 讀 | 讀 | A | 同上 |
| `LDR-29` | `0xDEADC0DE` | 緊接在 4 KiB 對齊映像之後的標記；loader 找到它就把燒錄長度加 4。**是誰寫下這個標記並未確立** | 讀 | 讀 | A | 同上 |
| `LDR-30` | `FLW` | 四個參數；會印出記憶體映射位址；只用一個 `.` 回應；確認提示是 `(Y)es, (N)o->` —— 而 `FLR` 的是 `(Y)es , (N)o ? -->` | 量 | 讀 | C（2026-08-17 實際執行過）+ A + B | `upstream/notes/uart-pinout.md` §4 |
| `LDR-31` | `FLR` | `FLR <dst_RAM> <src_flash> <len>`，三個都是十六進位，**三個都不檢查邊界**；它同時會寫 TFTP 長度全域 `0x8040DD28` | 讀 | 讀 | A | `docs/loader-command-semantics.md` §f |
| `LDR-32` | `DB` 的吞吐 | 81 個字元載 16 個位元組 —— **5.06 倍膨脹**，38400 下上限約 759 B/s，**實測 723 B/s**；讀完 4 MiB 約 95 分鐘 | 量 | 讀 | C | `upstream/notes/uart-pinout.md` §4.1 |
| `LDR-33` | `J BFC00000` | 就是重置 —— 它寫 `WDTCNR = 0` 然後在中斷全遮的狀態下空轉，所以只有看門狗能離開那個迴圈 | 讀 | 讀 | **×4** —— A（兩處）、B（帶廠商自己的註解）、D、E | `docs/loader-command-semantics.md` §f |
| `LDR-34` | 任何地方都沒有 kernel 命令列 | 13 個命令列形狀的關鍵字，**0 命中**，而同一次執行找齊了全部 17 條命令當控制。沒有環境變數機制、沒有儲存、也沒有對應命令 | 讀 | 讀 | C，並在本 repo 重跑一次 | 同上 §d、`C-2` |
| `LDR-35` | 從主控台碰不到的東西 | 沒有 16 位元寫入、沒有記憶體填值、除了 `MDIOW`/`PHYW` 外沒有暫存器命令、**沒有任何讀寫 CP0 的辦法** | 讀 | 讀 | A + B | 同上 §f |

## 12. 這台實際在跑的韌體

**不是本專案分析過的那兩份映像中的任何一份。** 是第三個 build，
而這台自己的 flash 之外，任何地方都沒有它的副本。

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `FW-01` | 版本字串 | **`TOTOLINK-CX-N150RT-V2.1.6-B20171121.1002`** —— `/etc/version`，41 bytes | 讀 | 讀 | A，並由 `boa` 編譯進去的 `Model No. N150RT (Firmware V2.1.6)` 佐證 | `upstream/notes/dump-vs-official.md` |
| `FW-02` | 二進位檔的建置日期 | **2018-01-10**，四個元件一致到分鐘 | 量 | 讀 | C | `upstream/notes/uart-findings.md` §1 |
| `FW-03` | Kernel | `Linux version 2.6.30.9 (admin@office.hopeiot) (gcc 4.4.5-1.5.5p2) #1526 Wed Jan 10 14:50:54 CST 2018` | 量 | — | C，從運行中的裝置讀出 | `upstream/test-ledger.md` `P5-5`、`upstream/PROGRESS.md` |
| `FW-04` | Kernel 命令列 | 編譯進去的是 `console=ttyS0,38400 root=/dev/mtdblock1`，**沒有 `init=`**；`Kernel command line` 這個字串不存在，所以開機 log 永遠印不出命令列 | 讀 | 讀 | C | `docs/loader-command-semantics.md` §d |
| `FW-05` | init／shell | BusyBox `v1.13.4 (2018-01-10 14:56:45 CST)`。**主控台上沒有 getty、沒有 shell** —— 打 `\r` 會回顯只是因為 tty 層在回顯 | 量 | 讀 | C | `upstream/notes/uart-pinout.md` §3 |
| `FW-06` | Web 伺服器 | `Boa/0.94.14rc21`，建於 `Jan 10 2018 at 14:57:54`，**485,012 bytes**，`sha256 19fe29d7…`，`pid=350, port 80`，以 **root** 執行 | 量（banner）· 讀（大小、雜湊） | 讀 | C、A | `upstream/notes/dump-vs-official.md` |
| `FW-07` | 開機起來的其他 daemon | `WiFi Simple Config v2.18-wps1.0` · `MiniIGD v1.09.1` · `IEEE 802.11f (IAPP) … (v1.8)` · `Realtek FastPath v1.03` · `sysconf init gw all` · `wan_disconnect: StartDnsSpoof` | 量 | — | C | `upstream/notes/uart-findings.md` §3 |
| `FW-08` | 根檔案系統 | **SquashFS 4.0，LZMA**，128 KiB 區塊，**567 inode**，20 fragment，`bytes_used` 1,876,033 | 讀 | 讀 | A | `upstream/notes/flash-layout.md` §3 |
| `FW-09` | libc | **uClibc 0.9.30.3** | 讀 | 讀 | A —— 這個 build 上映射的是 `/lib/libuClibc-0.9.30.3.so` | `upstream/notes/mips-ret2libc.md` |
| `FW-10` | 開機時的網路緩衝參數 | `SKB_BUF_SIZE=2408`、`MAX_SKB_NUM=256`、`NUM_RX_PKTHDR_DESC=428`、`eth_skb_free_num=694` | 量 | — | C | `upstream/dumps/uart-boot.log` |
| `FW-11` | MTD | `/dev/mtdblock0` 是整顆（`apmib` 讀的就是它）；`/dev/mtdblock1` 是 rootfs | 讀 | 讀 | A + C | `upstream/notes/firmware-upgrade-path.md` |
| `FW-12` | 映像容器 | `IMG_HEADER_T`，**16 位元組，big-endian**：`signature[4]`、`startAddr`、`burnAddr`、`len`。`w6cg` 與 `cr6c` 連標頭一起寫進 flash；rootfs **沒有**標頭 | 讀 | 讀 | A + C，並以三個 build 的區段接續驗證 | `upstream/notes/anatomy-n150rt.md` |
| `FW-13` | 升級路徑到底檢查什麼 | 一個 4 位元組 tag、一個**無金鑰**加總、一個型號字串。就這樣 | 讀 | 讀 | C，`UpgradeByData` 指令級讀完 | `upstream/notes/firmware-upgrade-path.md` |
| `FW-14` | 型號相容 tag | `TOTOLINK-N150RT-V2.1.0` —— 這是硬體／產品標籤，**不是韌體版本**；兩份廠商映像雖然標成 2.1.2 與 3.4.0，裡面都是這個字串 | 讀 | 讀 | C | `upstream/notes/anatomy-n150rt.md` |
| `FW-15` | 設定檔格式 | `COMPCS` 目前設定 · `COMPDS` 預設設定 · `COMPHS` 硬體設定 —— 是 `apmib` 表的**壓縮**（不是加密）TLV 序列化 | 讀 | 讀 | A + B | `upstream/notes/mib-and-config-dat.md` |
| `FW-16` | 出廠的 shell 帳號 | `/etc/passwd.org` 裡的 `root:123456`、`onlime_r:12345`（uid 0）；這台的 `TELNET_ENABLED = 0` | 讀 | 讀 | C。屬於型號層級，且已載於 CVE 紀錄 | `upstream/notes/credentials.md`、`upstream/notes/compcs-decode.md` |
| `FW-17` | 預設 SSID 命名 | `TOTOLINK N150RT` 加上 MAC 末六碼（在沒改過的機器上） | 讀 | 讀 | C | `upstream/notes/compcs-decode.md` |
| `FW-18` | 利用緩解機制 | **一個都沒有** —— 沒有 canary、沒有 RELRO、沒有 PIE、沒有 FORTIFY，而且每一支帶 `PT_GNU_STACK` 的 ELF 都標成 `RWE` | 讀 | 讀 | C，逐一數過每支 ELF | `upstream/notes/anatomy-n150rt.md` |
| `FW-19` | 手上另外兩份可比對的 build | V2.1.2（2015-08-25）與 V3.4.0（2020-10-30）—— **這台一份都沒跑過** | 讀 | 讀 | C | `upstream/notes/dump-vs-official.md` §3 |

## 13. flash 內容，從這台讀出來的

| id | 偏移 | 內容 | 長度 | V | N | 來源 | 擁有者 |
|---|---|---|---|:-:|:-:|---|---|
| `FLM-01` | `0x000000` | 開機載入器，MIPS 程式碼 —— `0b f0 00 04` = `j`，接著就是晶片 ID 比較 | — | 量 | 讀 | C | `upstream/notes/flash-layout.md` |
| `FLM-02` | `0x006000` | **`H601`** —— 硬體設定：MAC 位址與射頻校正 | — | 讀 | 讀 | A | 同上 §6 |
| `FLM-03` | `0x008000` | `COMPDS` —— 出廠預設 | `0x1D39`（7,481） | 讀 | 讀 | A | 同上 |
| `FLM-04` | `0x00A000` | 寫入的零 —— 是配置過的，不是抹除狀態 | — | 讀 | 推 | A | 同上 |
| `FLM-05` | `0x00C000` | **`COMPCS`** —— 現行設定；`config.dat` 就是它 | `0x1D36`（7,478） | 讀 | 讀 | A | 同上 |
| `FLM-06` | `0x00E000` | 寫入的零 | — | 讀 | 推 | A | 同上 |
| `FLM-07` | `0x010000` | **`w6cg`** 標頭 + bzip2 網頁資源 | `0x043A14`（277,012） | 讀 | 讀 | A | 同上 |
| `FLM-08` | `0x053A24`–`0x05FFFF` | 填充 —— 單一重複值 | 50,652 | 讀 | 讀 | A，是量出來的不是假設的 | `upstream/notes/dump-vs-official.md` §2 |
| `FLM-09` | `0x060000` | **`cr6c`** 標頭 + kernel；`startAddr = 0x80500000` | `0x0F1002`（987,138） | 讀 | 讀 | A，且 loader 自己印的 `Jump to image start` 與之相符 | `upstream/notes/flash-layout.md` |
| `FLM-10` | `0x060028` | kernel 的自解壓 stub —— `3c 10 80 5f` = `lui s0,0x805f` | — | 讀 | 推 | A。**上游 RUNBOOK 把這個字放在 `0x060030`；在這裡量到的是 `0x060028`** | `PROGRESS.md` Corrections |
| `FLM-11` | `0x151012`–`0x17FFFF` | 填充 —— 單一重複值 | 192,494 | 讀 | 讀 | A | `upstream/notes/dump-vs-official.md` §2 |
| `FLM-12` | `0x180000` | **SquashFS 4.0 / LZMA**，沒有容器標頭 —— 它必須正好落在分割區邊界上 | 使用 1,876,033 | 讀 | 讀 | A | `upstream/notes/flash-layout.md` §2 |
| `FLM-13` | `0x34A041` | 映像結束 —— **3.29 MiB**。公開規格說的 2 MB 不可能成立 | — | 讀 | — | A，且 W01 早在硬體到手三週前就從廠商容器推出「≥ 4 MB」 | 同上 §1 |
| `FLM-14` | `0x350000`–`0x3FFFFF` | **抹除狀態**，全 `FF`，整條尾巴 | — | 量 | 讀 | C，完整 dump | `upstream/notes/dump-vs-official.md` §2 |
| `FLM-15` | SquashFS superblock 的 `mkfs_time` | `0x80AD1C00` —— 位元組反轉後是 1,879,424，對照 `bytes_used` 的 1,876,033。**那個欄位裝的是位元組反轉的大小，不是時間戳**；三個 build 都是如此 | — | 讀 | 讀 | A + C（三個 build） | `upstream/notes/flash-layout.md` §4 |

## 14. 工具鏈與 libc

| id | 項目 | 值 | V | N | 來源 | 擁有者 |
|---|---|---|:-:|:-:|---|---|
| `TC-01` | 建置這份原廠韌體的東西 | `gcc 4.4.5-1.5.5p2`、uClibc `0.9.30.3`、Linux `2.6.30.9` | 量 | — | C，kernel 自己的 banner | `upstream/test-ledger.md` `P5-5` |
| `TC-02` | 候選的 GPL drop | `rtl819x-toolchain` 的 `toolchain/rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714` —— **banner 每一欄都對得上。在 R2a 量到之前它是假說** | 推 | — | `SOURCES.json` | gate R2 |
| `TC-03` | 那份 drop 的但書 | 它的目標板是 ALFA AIP-W512，不是 TOTOLINK 這片。DDR timing、PHY 設定、GPIO 腳位都可能不同，**而弄錯不一定會當機** | 推 | 推 | `SOURCES.json` | gate R2 |
| `TC-04` | `boa` 觀察到的 ELF flags | 到 2018-03-30 為止是 `0x1007` … pic … mips1；2019-03-15 起是 `0x1005` … mips1 | 讀 | 讀 | A + C，橫跨六個 build | `notes/lwl-mystery.md` |
| `TC-05` | rlxfw 自己要用什麼建 | *(留白)* —— T-vendor 對 T-modern 是 gate R2 的決定。`-march=mips1`、big-endian、o32、soft-float 已定案，libc 未定 | — | — | — | `plan/` §5、gate R2 |
| `TC-06` | 🔴 `mips-linux-gnu-gcc-12` (12.4.0) 下 `-march=mips1` 的實際條件 | **單獨給 `-march=mips1` 會被拒絕**：`cc1: error: '-march=mips1' requires '-mfp32'`。`-msoft-float` 也滿足它，而且對一顆沒有 FPU 的核心那才是誠實的旗標。`-march=r3000` 同病 | 量 | 讀 | 2026-08-24 在本機量到；`plan/DAY-ZERO.md` 第 6、8 項記的建置行少了這個旗標，照抄不會編譯 | `tools/test-hazlint.sh` `E2` |
| `TC-07` | 同一段 C 在兩個 `-march` 下的 `movz`/`movn` | `-march=mips1 -msoft-float` **0 個**；`-march=mips32 -msoft-float` **1 個**。兩個 `.o` 的 load-use 違規都是 0 | 量 | 讀 | 同上，而且「`.o` 真的產生了」本身是一個控制 —— 沒編出來的 0 跟編出來的 0 長得一樣 | 同上 |

## 15. rlxfw 的設計標的

**這些是決定，不是量測。** 放在這裡是因為設計時會跟硬體數字一起看，
而且其中兩條是絕對的。

| id | 項目 | 值 | 擁有者 |
|---|---|---|---|
| `TGT-01` | `0x000000`–`0x005FFF` | **永久禁寫。** 變磚不可回復，而且沒有備機 | `CLAUDE.md`、`plan/` D4 |
| `TGT-02` | `0x006000`–`0x007FFF`（`H601`） | **永久禁寫。** 這台的 MAC 與射頻校正，回復原廠設定不會還原 | `CLAUDE.md`、`plan/` D4 |
| `TGT-03` | `0x008000`–`0x00FFFF`（`COMPDS`/`COMPCS`） | 有經過驗證的備份才准寫 | `plan/` D4 |
| `TGT-04` | `0x010000`–`0x3FFFFF` | kernel 與 rootfs —— **R8 起**可寫，前提是先做過一次救援演練 | `plan/` D4 |
| `TGT-05` | 零 flash 寫入 | **主線在 R9 之前一個 flash 位元組都不寫。** 要寫必須拿到明確的同意 | `CLAUDE.md` |
| `TGT-06` | 為什麼寫 kernel 區是可回復的 | loader 佔 `0x000000`–`0x005FFF` 且永遠不被寫；它在提供 ESC 視窗**之前**就把映像搬進 RAM；檢查失敗會直接進提示字元。所以不論 `0x010000` 之後變成什麼樣，救援路徑都還在 | `plan/` D4、`docs/loader-command-semantics.md` §a |
| `TGT-07` | 預計的 A/B 佈局 | `0x010000` `rlxboot` 64 KiB（預算 ≤ 32 KiB）· `0x020000` slot A 1,920 KiB · `0x200000` slot B 1,920 KiB · `0x3E0000` state 128 KiB | `plan/` §9 |
| `TGT-08` | 每個 slot 的預算 | kernel（LZMA）≤ 900 KiB、rootfs ≤ 950 KiB、餘裕 70 KiB。原廠 kernel 是 987 KiB | `plan/` §9 |
| `TGT-09` | RAM 預算 | 以 `MEM-06` 的 26,052 kB 為底：kernel ≤ 8 MiB、userspace ≤ 6 MiB、更新緩衝 1.92 MiB、DMA ring + RX 池 ~600 KiB、餘裕 ≥ 8 MiB | `plan/` §9 |
| `TGT-10` | `0x010000`–`0x060000` 之間任一個 64 KiB 邊界 | 都是**原廠 loader 自己就找得到**的 slot，而且它偏好最低的那個 —— 所以 A/B 方案不需要改 loader | `docs/loader-command-semantics.md` §a |

## 16. 公開規格，以及它錯在哪

列出來是為了讓它被否證，而不是被半記半忘。來源 **X**：
TechInfoDepot 的 TOTOLINK N150RT 條目。

| id | 公開規格說 | 實際量到 | 是怎麼抓到的 |
|---|---|---|---|
| `PUB-01` | SoC **RTL8196C** | **RTL8196E**（`CPU-01`） | 晶片絲印，然後是開機碼自己對 ID 的比較 |
| `PUB-02` | Flash **2 MB** | **4 MiB**（`FLS-03`） | **廠商自己的韌體塞不進去** —— 在硬體到手三週前，就從容器的 burn 位址推出來了 |
| `PUB-03` | RAM **16 MB** | **實裝 32 MiB**（`MEM-04`） | 封裝絲印，然後是 `ramSize: 32M` |

**這三條原本都寫在本專案自己的計畫書裡，是從規格表抄來的，不是從板子上讀來的。**
其中最可查證地錯的那一條，光靠韌體就被證明不可能 —— 而那時裝置還沒到桌上。

## 17. 留白清單 —— 各由什麼來填

上面每一格留白都在這裡出現一次，並附上能填它的實驗。
**一格留白如果沒有出路，那格本身就是這張表的 bug。**

| id | 缺什麼 | 什麼能定案 | owning gate |
|---|---|---|---|
| `CPU-04` | 核心是 RLX4181 還是 RLX5281 | 裸機探針讀 `PRId` 與 `Config.M`。`/proc/cpuinfo` 試過了，它印的是一個十進位數字 | R1 |
| `CPU-15` | 矽片到底有沒有 `lwl`/`lwr`/`swl`/`swr` | 裸機 Reserved Instruction 處理器下的一條 `lwl` | R1a |
| `CPU-17` | `movz`/`movn` 是矽片實作還是被靜默模擬 | 同一個處理器，一條指令 | R1a / `C-12` |
| `CPU-24` | CP0 r20 的 `0x010` 與 `0x020` | 單一來源且無名；需要一次裸機讀取 | R1e |
| `CPU-31` | `HI`/`LO` 與 CP0 的 hazard 規則 | 裸機上一組 `mult`→`mflo`、`mtc0`→`mfc0`，中間補 0/1/2 個 `nop`，看讀值何時開始正確。`CPU-29`／`CPU-30` 已經指出原廠一個都沒補 | R1b |
| `CPU-25` | 快取大小、line 大小、關聯度 | 在裸機上重現 `r3k_cache_size()` | R1d |
| `CPU-27` | 提示字元下的 `Status.BEV` | 去追，或由 payload 讀出來 | R1d |
| `MEM-08` | SDRAM timing | 讀 loader 對記憶體控制器的寫入 | R5 |
| `REG-04` | `IRR2` 從沒被讀過 | 一次 `DW B8003010 1`，零風險，順手 | R6 |
| `REG-13` | SPI 控制器的五個暫存器從沒在裝置上讀過 | 位址有三個來源，讀數一個都沒有。**寫 flash 之前必須先讀**，因為 B 給的是命令**序列**而序列只有一個來源 | R5b |
| `REG-14` | `SFCSR` bit 27 `SPI_RDY` 的實際行為 | 這台自己的 `ComSrlCmd_RDID()` 就在等它，但沒人看過它翻 | R5b |
| `FLS-15` | flash 的第二支儀器 | 一組 `VCC` 線可以斷開的夾具，**外加**觀察到 `SF_CS0#`/`SF_SCK` 在 reset 時是浮接的 | `⊘` —— `notes/power-and-programmer.md` §5 |
| `FLS-06`–`FLS-08` | 這顆真正的 sector／page／block 大小 | EN25QH32B 的 datasheet，或 `RDID` 之後的後續命令。今天這三個值是 loader 的 fallback 預設 | R5b |
| `NET-08` | PHY 位址 5–31 | `PHYR 5 2`，然後 `MDIOR 2` —— **而 `PHYR 5 2` 正是那格會終結一次上機的** | `RUNSHEET.md` §F |
| `NET-13` | 哪個 RJ45 是哪個埠號 | 換一個網路孔，看那個位元跟不跟著跑 | `RUNSHEET.md` `E11` |
| `NET-10` | `0xBB804118`/`0x411C` 是什麼 | 值已量到；照 `PCRP` 間距推是埠 5 與埠 6，而**間距是推的**，沒有來源明寫 | R6 / `C-15` |
| `RF-01` | 無線電型號的第二來源 | 驅動印的是版本，不是料號 | R10d |
| `RF-04` | 無線電怎麼接到 SoC | 從沒追過 | R10d |
| `BRD-01` | `LSP5526` 是什麼 | 量它的輸出腳對地 —— 三十秒的事，而且它是板上唯一與分析無關的一顆 | — |
| `BRD-05` | 按鈕是 `RESET#` 還是 GPIO | 接著主控台按下去，看 stage 1 有沒有跑 | `C-14`、`RUNSHEET.md` `D3` |
| `CLK-03` | 199.48 MHz 與 400 MHz 的關係 | 未量；÷2 是一種讀法，不是一次量測 | R1 |
| `CLK-08` | 看門狗的牆鐘逾時 | **`D4`，同一次上機就填得到。** 最短那檔量不到（164 µs／2.30 ms），最長那檔量得到（84.1 ms／1.177 s，相差 14×）—— **要修的是實驗，不是儀器。** `EW B800311C 240000` 武裝 `OVSEL`=`1001`，`D1` 當控制（它的區間是開機時間加上一個 ≈0 的逾時），`D4 − D1` 就是逾時本身，開機時間對消 | `C-8` |
| `CLK-10` | `WatchDogIND` 到底有沒有鑑別力 | `D2` 讀整個字，預測 `A5100000`；讀回 `A5000000` 就是沒有 | `C-8` |
| `MEM-10` | 暖重置後 SDRAM 內容存不存活 | `D2b` 讀回 `C1` 寫的 scratch 字，`D3` 的冷開機當否證 | `C-8` |
| `LDR-22` | 是誰在任何 `FLR` 之前填了 `0x80500000` | 值是量到的，而它被宣稱的機制已被否證 | `C-16` |
| `LDR-21` | `gCHKKEY_HIT` 的寫入者 | 桌面十五分鐘，對照 D | `C-13` |
| `TC-02` | 那份 GPL drop 是不是就是這一份 | 建出來比對 | R2a |
| `TC-05` | rlxfw 自己的工具鏈 | T-modern 的 timeboxed spike | R2 |

## 18. 刻意不放在這裡的東西

**任何識別「這一台」而非「這個型號」的東西。** 這條規則在檔案被加進來之前
就適用，不是推上去之後才補。

| | 為什麼 |
|---|---|
| MAC 位址 | 在 flash `0x006000` 的 `H601` 裡，也印在 PCB 背面的條碼標籤上。兩者已被確認逐位元組相同 |
| 序號 | 在正面的 QR 與數字標籤上 —— QR 會被自動解碼，而且大幅縮圖之後仍然可解 |
| WPS PIN | 經由 `HW_WLAN0_WSC_PIN` 可達，而且開機 log 有可能印出來 |
| 射頻校正 | `H601` 的其餘部分 |
| flash dump 本身 | 它既是廠商韌體，又同時裝著上面全部。`SOURCES.json` 記錄怎麼取得公開輸入；dump 不是其中之一 |
| 兩份 datasheet | `refs/README.md` —— 引用、記錄雜湊，永不轉載 |

`tools/audit-bench-log.py` 會對任何要進 `bench/` 的檔案掃描以上這些形態，
而且**每一條樣式都先跑過一份合成的正控制**，除非全部命中，否則它拒絕回報乾淨。
