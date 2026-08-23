# LOG

工作日誌，一次坐下來一則。**桌面日也寫** —— 桌面日正是下一次上機計畫改變的日子。

每一句話標記來源：**量到的**（在裝置上）、**讀出來的**（從程式碼或 dump 裡）、
**推測的，待量測**。三者混在一起就都不值錢。

---

## 2026-08-23 — `S0a`：3-2-1 加密備份 + 還原演練

桌面日，未接觸裝置。

### 開工前的四個量測，它們改寫了這一步的內容

| 量到的 | 用什麼量的 | 後果 |
|---|---|---|
| 全機只有一顆實體磁碟（NVMe INTEL SSDPEKNW512G8，476.9 GB），無可移除媒體 | `Get-PhysicalDisk`、`Get-Disk`、`Win32_DiskDrive` 三者一致 | `~/fwre-work`（vhdx 31.26 GB）、`router-rebuild/`、`../router` 同在一片矽上。當時的狀態是 1 份、1 種媒體、0 份離線 |
| 以 `key` 掃 `$FWRE_WORK` 得 7,675 路徑 / 197 setuid / 66 unreadable；以 `root` 掃得 **7,776 / 294 / 0** | `tools/fsmanifest.py`，同一棵樹跑兩次 | 非 root 的封裝會靜默漏掉 101 個路徑與 97 個 setuid 位元，其中包含 `qemu-env-2018/var/dropbear/dropbear_rsa_host_key` |
| 762 symlink、12 device node、1 FIFO、294 setuid/setgid；287 個檔案 mode 為 `7355` | `sudo find` / `fsmanifest.py` | 封裝只能是 `tar`（root、`--numeric-owner`）。zip／7z／複製到 DrvFs 都會丟掉這些 |
| `getfacl -R -s` 回報 0 行 | `getfacl` | 沒有非平凡 ACL，manifest 不記錄 ACL 是有根據的省略，不是遺漏 |

`../router` 的工作區有 13 個已修改的追蹤檔與 2 個未追蹤檔，`git log @{u}..` 為空 ——
這些改動不在 `origin` 上，因此在此之前只存在於一顆磁碟上。
兩個未追蹤檔屬於尚未寄出的揭露材料；**檔名不記在這裡**，理由與 manifest 拆成
K1／K2 兩側相同：檔名本身就是揭露資訊。

### 產出

七個封裝，兩把 X25519 金鑰（K1 = 資料，K2 = `disclosure`，刻意分開，
使一次資料還原不等於交出未寄出的漏洞報告）。

| 封裝 | 根 | 密文大小 |
|---|---|---:|
| `core-fwre.tar.zst.age` | `$FWRE_WORK` | 9.6 MiB |
| `core-desk.tar.zst.age` | `…/Desktop` | 8.4 MiB |
| `full-fwre.tar.zst.age` | `$FWRE_WORK`，除 `disclosure/` | 52.6 MiB |
| `router-git.tar.zst.age` | `…/Desktop` | 23.0 MiB |
| `meta-K1` / `meta-K2` | manifest 本身 | 333 KiB / 827 B |
| `disclosure.tar.zst.age` | `$FWRE_WORK/disclosure` | 3.7 KiB |

`tar --numeric-owner --acls --xattrs --sort=name` → `zstd -19 -T0 --long=27` → `age -r`。
manifest 加密後才隨資料移動：`manifest-fwre.tsv` 含 `disclosure/` 的**檔名**，
而檔名本身就是揭露資訊。K1 側與 K2 側因此拆開。

`par2 -r10`（K1 組）與 `-r30`（K2 組）：`age` 的分塊 AEAD 能**偵測**位元腐蝕但不能**修復**，
一份放在抽屜裡一年的副本需要的是後者。備份內另附 `age` 與 `zstd` 的 amd64 `.deb`，
使還原不依賴當時那台機器連得上套件庫。

### 控制

否證條件在執行前寫下。

| 控制 | 預測 | 實測 |
|---|---|---|
| P0 範圍 | 非 root 掃描應少於 root 掃描 | 少 101 路徑、97 setuid（見上表） |
| 基準 | 未竄改的還原比對為 0 行 | 0 |
| N1 密文翻一個位元 | `age` 非零離開 | `exit=1`，`failed to decrypt and authenticate payload chunk`，**且已先寫出 5,046,272 bytes** —— 判準是離開碼，不是有無輸出 |
| N2 清一個 setgid 位元 | 正好 2 行 | 2 |
| N3 改一個 symlink 目標 | 正好 4 行（連結 + 父目錄 mtime） | 4 |
| N4 兩個缺陷都在，用 `find -type f \| sha256sum` 檢查 | —— | **0 行**。它只覆蓋 7,770 個路徑中的 6,346 個，不覆蓋任何 mode 位元 |
| par2 修復 | 應能修回原始雜湊 | 破壞 59,000 bytes → `Repair complete` → sha256 回到 `f6b1e932…` |
| 金鑰抄寫 | 改一個字元應失敗 | `malformed secret key: invalid checksum`。`age-keygen -y` 由私鑰導出公鑰，與 `K1.pub`/`K2.pub` 比對可同時抓出「抄成另一把合法金鑰」與「K1/K2 標籤寫反」 |

N4 是對 DAY-ZERO 所寫 DoD（「逐檔 `sha256sum` 相符」）的直接否證。

### 還原演練

從副本 ②（Transcend ESD310P，exFAT，disk 1）進行，**在實體重新插拔之後**，
所以讀到的是快閃顆粒而非 Windows 檔案快取。演練期間 `/home/key/rlxfw-backup/`
先行改名，使任何一步若退回本地副本會是失敗而非靜默通過；
驗證用的 `fsmanifest.py` 取自 `core-desk.tar.zst.age` 解出來的那一份，不是工作區那一份。

| 對象 | 行數 | 差異 | `unreadable` |
|---|---:|---:|---:|
| `full-fwre` | 7,770 | **0** | 0 |
| `router-rebuild` | 24 | **0** | 0 |
| `router`（含 `.git`） | 2,593 | **0** | 0 |
| `disclosure` | 6 | **0** | 0 |
| `core-fwre`（子集） | 500 | 0 個不在來源中 | 0 |

從 USB 還原出來的 `dumps/flash-n150rt-console-1.bin`：4,194,304 bytes，
`a800059a9b8c414df026a22b8423a5939d0f9bb793109d0f7ce086f6810f37ea`。

### 過程中發現並修掉的一個缺陷

第一次演練時 `router` 差 2 行，只差根目錄 `.` 的 mtime。兩個假說：
tar 在第二次解壓時重建共同父目錄並蓋上當下時間（H1）；或來源在建 manifest 之後被改過（H2）。
判別：來源 `router` 的 mtime 當時仍等於 manifest 記錄的 `1787437631` ⇒ 來源未動 ⇒ H1。
對照組是 `router-rebuild`，它只來自單一封裝、無第二次解壓覆蓋，兩邊完全相符。

修法不是規定解壓順序，而是把 `router/` 這個目錄項本身也放進 `router-git` 封裝
（`tar --no-recursion router --recursion router/.git`），使還原與順序無關 ——
並用兩種順序各驗一次證明它確實無關。

### 沒有做到的

| | 狀態 | 原因 |
|---|---|---|
| 副本 ③ 的還原驗證 | ⊘ | 已上傳 Google Drive，未下載回來比對。作者決定跳過。**「上傳成功」與「上去的東西是對的」是兩個不同的主張**，後者未被檢查。要關掉這一格，下載 `meta-K1.tar.zst.age`（333 KiB）比對 sha256 即可 |
| `S0b` 三個電源實驗 | 未開始 | 需要接觸硬體，本次為桌面日 |

USB 上另有 `rlxfw-backup-2026-08-23/`（作者自行複製），經比對為 K1 側的嚴格子集，
11 個檔案逐位元組相同，缺 K2 組、`disclosure`、`meta-K2` 與離線 `age`/`zstd`。
兩個名稱近似、內容不同的資料夾並存於同一媒體上，是還原時的誤選風險。

### 對 `DAY-ZERO.md` / 計畫 §6-S0 的四則修正

1. §現況第一條寫上游「工作區乾淨」。量到 13 個已修改 + 2 個未追蹤，且未推送。
2. `S0a` 的 DoD「逐檔 `sha256sum` 相符」對 type / mode / uid / gid 是盲的，見 N4。
3. `S0a` 的備份範圍只涵蓋 `$FWRE_WORK`。`refs/`（兩份不可提交的 datasheet）、
   `plan/`（gitignored，單一副本）、repo 本身（當時尚無 git）、
   以及 `../router` 的未提交工作都在範圍之外。
4. `S0a` 的副本 ② 假設有第二種實體媒體存在。開工當時沒有。

### 版本控制（順序與 `DAY-ZERO` 第 3 項不同，理由記在這裡）

`tools/test-gitignore.sh` 排在第一個 commit **之前**，而非計畫所寫的第 3 項結尾。
git 歷史是這個專案裡唯一「做錯了難以收回」的地方，而 `refs/` 底下那份 datasheet
標著 `CONFIDENTIAL: Development Partners Only`。結果 13/13，其中六個是正控制 ——
一份只寫 `*` 的 `.gitignore` 光靠七個負案例就會拿到 7/7。

新增 `.gitattributes`（`* text=auto eol=lf`）。這裡的腳本在 Windows 上編輯、
在 WSL 下對著 `/mnt/c` 上同一份檔案執行，而 Git for Windows 的 `core.autocrlf`
預設為 `true`：沒有這個檔案，clone 回來的腳本帶 CRLF，全部以
`bash
: No such file or directory` 失敗 —— 在它們被寫出來的那台機器上。

第一個 commit `9c40aa4`，十個檔案。推送之前先把 `Jhongwe1/router-customFW`
由 PUBLIC 改為 PRIVATE：`CHARTER.md` 寫的是「v0.1 起 public」，而現在是 S0。
倉庫因此同時成為第四份副本（異地、帶版本歷史），但它不取代 `S0a` ——
它不含 `dumps/`、`refs/`、`plan/`，而那些正是不可再生的部分。

寫進 committed 檔案之前，`LOG.md` 與 `PROGRESS.md` 裡兩個未追蹤檔的檔名先被移除。
那兩個檔名描述的是尚未寄出的揭露內容；把它們寫進一個將會公開的檔案，
與稍早刻意不讓同類檔名以明文上雲端，是同一條理由 —— 原本的寫法前後不一致。

---

## 2026-08-23 — `DAY-ZERO` 2a：`lwl`/`lwr`/`swl`/`swr` 計數

同日，桌面工作，未接觸裝置。完整內容在 `notes/lwl-mystery.md`；這裡只記過程與判讀。

### 工具

`tools/opcount.py`：把檔案當 big-endian 32 位元字、在每個 4-對齊位移做 primary opcode
直方圖。載入位址 4-對齊 ⇒ 每條指令都落在 `≡ 0 (mod 4)` 的位移上 ⇒ 掃描是指令集合的
**超集**：會把資料算成指令，但不可能漏掉指令。**所以每個計數都是上界，而且只有一種
結果是嚴謹的 —— 零。** 這一題要的正好是零。

先試 `objdump -d`，它在這些二進位上**輸出 0 行**：`/bin/boa` 的 section header 被 strip 掉，
而 `-d` 只處理 section。它於是對每個助憶符都回報 0。一個看不見的工具照樣願意報一個數字。

控制在 `tools/test-opcount.sh`，15 個案例：P1 已知計數的 fixture 必須逐項重現；
N1 同一批位元組讀成 little-endian 必須得到不同答案（得 0）；N2 從位移 2 開始掃必須得到
不同答案（得 0）；另有「寫死的機器碼是否仍與組譯器一致」一項。

程式碼區的界線是由**四位元組皆可列印 ASCII 的佔比**這個獨立訊號推出來的，
不是找一個能湊出預期數字的界線。

### 量到的

| 二進位 | 種類 | 程式碼區 | 四條合計 |
|---|---|---|---:|
| `stage2.bin` bootcode | **裸機** | `0x80400000`–`0x8040a000` | **0** |
| `bin/busybox` unit-2018 | userspace | `0x403000`–`0x43c000` | **0** |
| `bin/boa` unit-2018 | userspace | `0x403c00`–`0x462000` | **144** |

`stage2` 的程式碼區內，`cache`、`ll`/`sc`、`sync`、branch-likely、SPECIAL2/3、FPU、
MIPS16 `jalx` **全部為 0**。`busybox` 亦然。兩者都是嚴格的 MIPS-I **減去非對齊載入／
儲存** —— 正好是 Lexra 出貨的那個子集。

`boa` 跨六份韌體：2015、2016 兩份是 176；2018 兩份是 144；2019、2020 兩份是 **0**。
六列的 `lwl` 全部等於 `lwr`、`swl` 全部等於 `swr`。配對是檢查而不是巧合：
編譯器產生非對齊存取時成對發射，六個獨立界定的程式碼區都精確配對，
說明界線是對的、而且這些是指令不是資料。

`stage2` 全檔掃描回報 1 而非 0。三個命中全部在程式碼區之外，逐一裁決都是資料 ——
其中 `ll` @ `0x8040ab14` 那個字是 `c0a80001`，也就是 **`192.168.0.1`**，
它後面四個位元組就是字串 `"
Switch core initialization failed!
"`。

### 判讀與其界限

**讀出來的**：Realtek 自己為這顆 SoC 寫的 bootcode，在 40 KiB 程式碼裡一條都沒用；
廠商的 `busybox` 也沒有。`boa` 用到 2018–2019 之間某一刻，然後停止。

**沒有建立的**：矽片是否實作這四條。這裡沒有任何一個數字量自裝置。
一個避開某條指令的二進位，是關於**編譯它的 toolchain** 的證據，不是關於**執行它的硬體**。

背景（已查證）：MIPS Technologies 對 Lexra 的專利訴訟標的是美國專利 4,814,976，
涵蓋的正是這四條指令；Lexra 的核心實作 MIPS I 唯獨不含它們。專利原屬 Silicon Graphics。
1998 年先有一次**商標**訴訟，和解條件是 Lexra 必須明白聲明其產品不實作非對齊載入／儲存。

### `DAY-ZERO` 2a 的預測錯在哪

它預期分界是「裸機 vs userspace」。量到的分界是「`boa` vs 其他所有東西」，
而且在 2019 年關閉。因此 2a 交給 R2 的後續問題變成一個更窄也更好的問題：
**`boa` 的建置方式有什麼不同，以及 2019 年改了什麼。**

---

## 2026-08-23 — `DAY-ZERO` 2b 與 2c

同日，桌面工作，未接觸裝置。完整內容在 `notes/cache-model.md` 與
`docs/loader-flash-write.md`。

### 2b：快取管理模型（F49）

2a 已經給了半個答案 —— `stage2` 程式碼區沒有任何 `cache` 指令。剩下的從兩處讀出：

**一、loader 從 reset 之後第三段就切成 uncached 執行。** `0x80400498` 取自己下一條
指令的位址、OR 上 `0xA0000000`、跳進 KSEG1 的別名。所以「它怎麼讓 I-cache 看見剛寫進
RAM 的東西」對它自己的程式碼而言不成立 —— 它不需要。

**二、它用一個 CP0 register 20 做快取操作**，慣用法是「清零、寫命令、再清零」，
值有 `0x020`、`0x202`、`0x010`（開機初始化）與 `0x200`、`0x002`（封裝成函式）。
`stage2` 從不設 `Status.IsC` 或 `SwC`。

第二來源是廠商 kernel。`linux-2.6.30/arch/mips/mm/` 只有標準的
`c-r3k.c`／`c-r4k.c`／`c-tx39.c`／`c-octeon.c`，**沒有 Lexra 專屬的快取檔**，
而 `c-r3k.c` 裡有一模一樣的 `mtc0 $0,$20` / `mtc0 $8,$20` / `mtc0 $0,$20` 序列，
並直接命名了值：**`2` = invalidate I-cache、`1` = flush D-cache、`512` = flush D-cache
（819x 變體）**。它同時使用 `ST0_ISC`／`ST0_SWC`。

所以模型是 **R3000 的**，CP0 register 20 是疊在上面的 Lexra 擴充，不是取代。
`0x010` 與 `0x020` 只有一個來源、沒有名字，**記為未定**，沒有猜。

`c-r3k.c` 裡還帶著日期的註解解釋了為什麼要先 D 後 I：

> *Ghhuang (2007/3/9): RD-Center suggest that we need to flush D-cache entries
> which might match to same address as I-cache ... when we flush I-cache.*

而 `stage2` 的 `0x804066e8` 正是先呼叫 `0x804066c0`（`0x200`）再寫 `0x002`。
這一條直接決定 R1d 怎麼把例外處理器裝進去。

### 2c：`burn()` @ `0x80401318`（F45）

`burn()` 不是 flash 寫入原語，是**映像解析器與派工器**。它比對八個四位元組區段簽章
（`boot`、`sqsh`、`w6cp`、`jw6c`、`cwmp`、`ksap`、`ALL1`、`ALL2`），驗 checksum，
印出 `burn Addr =0x%x! srcAddr=0x%x len =0x%x`，然後寫。

**邊界檢查只有上界**：`目的位址 + 長度` 對晶片容量比較，超過就截斷。
**沒有下界，而簽章表裡有 `boot`。** 也就是原廠升級路徑本身可以寫進 loader 區 ——
`CLAUDE.md` 那條「永不寫 `0x000000`–`0x005FFF`」只能由我們自己的工具強制，
**裝置不會幫忙**。

SPI 控制器的暫存器與命令介面拿到了，而且是**兩個來源同意**：GPL drop 的
`bootcode/boot/flash/spi_common.c` 命名了 `SFCR 0xb8001200`、`SFCR2 0xb8001204`、
`SFCSR 0xb8001208`、`SFDR 0xb800120c`；這台自己的 `stage2` 分別引用了它們
2／1／19／14 次。`SFDR2 0xb8001210` 只有 GPL 說，這台**零次引用**，記為
「廠商宣告、此 loader 未用」。命令表含 **`RDID` = `0x9F`**，註解寫著
"outputs JEDEC ID: 1 byte manufacturer ID & 2 byte device ID"。

**JEDEC ID 這一格因此在桌面上就關掉了介面未知的部分** —— 讀它仍然需要在裝置上跑碼，
但要發什麼、往哪個暫存器發，現在是規格而不是未知。

第三段（映像壞掉時 loader 走哪條路）從 GPL 原始碼讀到：`doBooting()` 在
`if (flag)` 為假時直接 `goToDownMode()`，也就是**壞映像不會讓你失去救援路徑，
而是更快到達它**。但那是**另一個 bootcode 世代**的原始碼；這台的 `stage2` 有相同的
`---Escape booting by user` 與 `Jump to image start=0x%x...`，卻**沒有**
`no sys signature` 與 `sys checksum error`。所以結構對這台是推測，
確認要在 bench 上做，而且只對 kernel 區做。

### 這兩項用到的新來源

廠商 kernel 與 WECB bootcode 都沒有 clone，是用 `gh api` 逐檔讀的 ——
`fetch-sources.sh`（`DAY-ZERO` 第 3 項）尚未執行，`src-vendor/` 仍是空的。

---

## 2026-08-23 — `DAY-ZERO` 第 3 項：釘上游、抓來源、寫 README 第一屏

同日，桌面工作，未接觸裝置。

### 釘上游

`git submodule add` 之後 `git submodule status` 前面帶一個 `+`。那不是裝飾：
**index 裡記的是 clone 當下預設分支的 HEAD `277af488`，不是隨後 checkout 的
`4d3ff26`。** 就那樣 commit 下去，記進版本歷史的差分基準會是錯的一個 commit ——
而那是 R9 唯一的錨。`git add upstream` 之後 index 變成
`160000 4d3ff26bfb8a32986d3db532ca25197ef3043fdb`，`+` 消失。

驗證同時翻出一件事：`git branch -r --contains 4d3ff26` 只回報 `origin/w08-writeup`。
**這個 pin 只活在一個分支上。** 分支被刪、被 rebase 或改名，它就抓不回來了。
記為 C-11，修法是在上游打一個 tag。

### `src-vendor/` 不能放在 `/mnt/c`

`SOURCES.json` 把每個 GPL drop 的 `dest` 指到 `src-vendor/`，而 repo 在 NTFS 上。
**廠商的 kernel 樹裡有只差大小寫的同名路徑** —— 光 `wecb-vz-gpl` 就有 30 對以上
（`xt_CONNMARK.h` 對 `xt_connmark.h`、`ipt_ECN.c` 對 `ipt_ecn.c`、
`Documentation/IO-mapping.txt` 對 `io-mapping.txt`…）。

先量再修：在 `/mnt/c` 上 `touch B.h b.h` → **只剩 1 個檔案**；在 ext4 上 → 2 個。
clone 完成後對 `rtl819x-toolchain` 反過來算：
**在大小寫不敏感的檔案系統上會有 254 個檔案安靜消失。**

修法是把 `src-vendor` 做成指向 `$FWRE_WORK/rebuild/src-vendor` 的 symlink ——
那正是 `CLAUDE.md` 已經指定放二進位的地方。checkout 後複驗：
兩個 `xt_*MARK.h` 都在，`git status` 乾淨，`core.fileMode = true`。

順帶量到兩件關於 DrvFs 的事，其中一件修正了 `CLAUDE.md`：

| | `CLAUDE.md` 說 | 量到 |
|---|---|---|
| symlink | 會掉 | **不會。** `ln -s` 成功、`readlink` 解得開 |
| 權限位元 | 會掉 | 會，而且全部變 `777`；git 因此把 `core.fileMode` 設成 `false`，**完全看不見 mode 變化** |

規則本身是對的，它給的理由有一半不對。

### `.gitignore` 的斜線

`src-vendor/` 結尾的斜線只匹配目錄。`src-vendor` 一變成 symlink，git 就想 commit 它。
拿掉斜線，並在 `tools/test-gitignore.sh` 補第 14 個案例 ——
**專門測這件剛剛咬過人的事**。14 passed, 0 failed。

### 抓來源

`tools/fetch-sources.sh` 跑完：兩份 datasheet 雜湊相符，四棵樹 clone 完成並記錄
commit id 到 `src-vendor/CLONED.tsv`。全部落在 ext4，`/mnt/c` 上只有一個 symlink。

### 順手把 2c 的 SPI 暫存器補成三來源

裝了 `poppler-utils` 之後讀 `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` §7.4.5–7.4.9：
`SFCR 0xB800_1200`、`SFCR2 0xB800_1204`、`SFCSR 0xB800_1208`、`SFDR 0xB800_120C`、
`SFDR2 0xB800_1210` —— 與 GPL 原始碼、與這台自己的 loader 三者一致，
**而且這一份是 8196E 自己的 datasheet，前兩者是 8196C／8198 世代。**

datasheet 的 Table 10 給出 `SFCSR` 的完整位元佈局，與 GPL 的位移巨集**逐欄位吻合**
（`SPI_CSB0<<31`、`LEN<<28`、`SPI_RDY<<27`、`IO_WIDTH<<25`、`CHIP_SEL<<24`、
`CMD_BYTE<<16`）。它自己舉的例子就是 `'Read ID' is 0x9F`。
另外註明 **`SFCSR` 與 `SFDR` 不支援 byte access** —— 那是 R5b 會踩、而且踩了不會報錯的地方。
`docs/loader-flash-write.md` 裡我自己標的那個「單一來源」缺口因此關掉。

### `fetch-sources.sh` 裡一個不會觸發的控制

fetch 跑完之後結果裡有一行 `skip upstream not present` —— 而 upstream 明明在，
而且我在啟動它之前就親眼驗過 pin。原因是腳本測 `[ -d "$HERE/upstream/.git" ]`，
而 **submodule 的 `.git` 是一個檔案**（33 bytes，內容 `gitdir: ../.git/modules/upstream`），
不是目錄。

所以那個「差分基準有沒有被移動過」的檢查，在 upstream 是正規 submodule 的情況下
**永遠不會執行**。它不會報錯，只會安靜地跳過，然後結尾照樣印
`all declared sources present and verified`。

改成 `-e` 之後 `--verify` 回報 `upstream pinned at 4d3ff26bfb8a (matches SOURCES.json)`
與 `nothing was skipped`。

**一個不會觸發的控制跟沒有控制的差別只在心理上** —— 這句話今天出現第二次，
第一次是在備份的 DoD 上。

### `README.md` 第一屏

按 `ARTIFACTS.md` §1 的五件事寫，但 Status 一列照現實寫，不照範本寫：
**「Nothing built, nothing flashed, zero bytes written to the device.」**
以及一列 `Not measured`：**這個 repo 到今天為止沒有任何一個數字是在矽片上量到的。**

### 收尾：把 pin 錨死，並修掉 `CLAUDE.md` 裡被量測否證的一句

上游 repo 現在帶一個 annotated tag `rlxfw-baseline` 指向 `4d3ff26`，
遠端驗證 tag object `7c4c0537` 解到該 commit。`SOURCES.json` 的 `pin` 區塊
增加一欄 `tag`。**差分基準不再依賴任何一個分支活著。** C-11 當天開當天關。

順帶量到：`../router` 在本次 session 期間多了一個 commit `f69ef16`（19 個檔案，
涵蓋早上點出的 13 M + 2 ??，工作區現已乾淨）。`4d3ff26` 仍是 HEAD 的祖先 ——
歷史是加在上面而不是改寫，錨點沒事。該 commit 尚未推送。

`CLAUDE.md` 改了兩處，都是今天實測的結果：

1. 「DrvFs drops symlinks and permission bits」→ symlink **不會**掉，權限位元會，
   而且真正致命的是 NTFS 大小寫不敏感會吃掉 **254 個**廠商 kernel 樹的檔案。
   規則不變，理由換成量到的。
2. WSL 派工方式：`-lc` 會剝掉 `$VAR` 並把開頭的 `/` 做 MSYS 轉換
   （`bash /mnt/c/x.sh` 變成 `bash 'C:/Program Files/Git/mnt/c/x.sh'`）。
   改成 `bash -ls` 加 stdin heredoc，body 完全不被動到 —— 本 session 全程如此。

### 下一步

`DAY-ZERO` 第 4 項（loader 命令語意六題，其中三題上游已答）。
第 5 項是這一節唯一要碰硬體的一項。
