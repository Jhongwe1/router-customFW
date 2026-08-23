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

### 追加：找到這台自己的 loader 發 RDID 的位置

回答一個追問時多查到的，屬於 2c。`ComSrlCmd_RDID()` 在 `0x804058bc`，被呼叫兩次：
它輪詢 `SFCSR` 的 bit 27，然後把 `0x9F000000` 寫進 `SFDR`，再從 `SFDR` 讀回。

**這是 `SFCSR` 位元佈局的第四個來源，而且種類不同。** 前三個（GPL 巨集、
datasheet 的表、位址引用次數）都是**文件或靜態引用**；這一個是這台機器自己的程式
**在行為上依賴那個語意** —— 它就是在等 bit 27。文件可能寫錯型號，
一段從 2018 年開機到現在的程式不會等錯位元。

同時確認命令是寫進 `SFDR` 而不是 `SFCSR` 的 `CMD_BYTE` 欄位，
與 datasheet 註明 `CMD_BYTE` "Only Used in MMIO Mode" 一致。

**值仍然未知。** `v0` 是回傳暫存器，除非兩個呼叫者之一把它存進記憶體，
否則沒有固定位址可讀。**那還沒追**，值得十分鐘 —— 若有存，
下次上機用 loader 的 `EB` 就能讀出 JEDEC ID，不必寫任何新程式碼、零風險。

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

---

## 2026-08-23 — `DAY-ZERO` 第 4 項：loader 命令語意六題

桌面日，未接觸裝置。產出 `docs/loader-command-semantics.md`。

### 開工前先對狀態，而狀態表有一格是壞的

計畫說「五題裡三題上游已經答了」。逐題回查上游的實際證據，發現第 (d) 題
（有沒有地方塞 kernel command line）標成「上游 `P9-1`，仍開著」是**過期的**：
`P9-1` 在 `RUNBOOK` §8.12.10 已判 refuted，三個靜態來源，
而且 8/17 的 bench 動態半也一致。

**兩個 session 差點繞著一個已經有答案的問題轉。** 這件事的形狀值得記住：
**計畫的狀態欄是一份快取，而快取會過期。** 開工前花十分鐘回查來源，比事後發現便宜。

同一輪對狀態也發現第 (f) 題問窄了 —— 它問「17 條裡**哪一條**能寫任意記憶體」，
而答案是四條，其中兩條的量級遠大於 `EB`/`EW`。

### 儀器，以及四個會擋人的控制

不抄上游的表。理由寫在文件 §0：上游自己記錄過「手抄一張表 = 一個沒有儀器的宣稱」，
在第二個 repo 重演一次，等於一份狀態兩個 owner。改成**在這裡重跑儀器**。

| 控制 | 排除什麼 | 結果 |
|---|---|---|
| 重抽的 `stage2.bin` 必須雜湊到 `f88869d1…` | 讀到跟上游不同的物件 | 相符 |
| `docs/loader-flash-write.md` 引的 `ComSrlCmd_RDID()` 序列必須在新反組譯裡逐指令重現 | `--adjust-vma`、endianness、架構旗標任一錯 | 在 `0x8040591c`–`0x80405970` 重現 |
| `loader-unpack.py` 找不到 17 條指令就拒絕出報告 | 一個其實是掃描壞掉的「不存在」結論 | `documented_commands_missing: []` |
| `-m mips:3000` 對 MIPS-I 以外的東西印 `.word` | 用 MIPS32 解碼器安靜地吞掉答案 | **印了兩個 `.word`，而它們是這一天最重要的發現** |

第四條原本只是保守設定。它變成了 §9。

### (a) loader 是掃的，不是硬編碼的 —— C-1 關閉

先寫反證條件：*若硬編碼，到 header 解析為止產生 `0x060000` 的立即數恰有一處，
外圍無迴圈。* 正控制：同一次搜尋必須找得到已知存在的 32 項 SPI chip table 掃描迴圈。

**讀出來的**：`0x80408084` 先固定試 `0x010000`／`0x020000`／`0x030000`，
再從 `0x030000` 以 `0x10000` 為步長掃到 `0x060000`，跳過已試的三個。
候選集恰好六個，而**這台的 kernel 在 `0x060000`，是最後一個**。
廠商 `check_image_header()` 逐行對得上，連「跳過已試的三個」那三個比較都在。

**對 R8 的後果比預期好**：A/B 佈局不需要教 loader 任何事。
`0x010000`–`0x060000` 的任何 64 KiB 邊界都是一個 slot，而且低位址優先 ——
那正是 A/B 想要的行為，免費拿到。

### (a) 的副產品：C-4 從「推測」升成「讀出來的」

追 header 解析點就會經過 image check。`check_image()` 在 `0x80407D50`：
簽章（`cs6c`→1、`cr6c`→2）加上一個必須為零的 16-bit 半字和。
`doBooting()` 在 `0x80408690`，`beqz a0` 在檢查失敗時**直接跳到 `goToDownMode()`**，
沒有 ESC 等待、沒有訊息。

`docs/loader-flash-write.md` §3 原本寫「這台的 binary 裡找不到 image check，
結構是從另一個 bootcode 世代推論的」。**那句話錯在把「字串不存在」讀成「檢查不存在」。**
這個 build 把 `no sys signature` / `sys checksum error` 編掉了，
卻留著 `rootfs checksum error` —— 檢查是靜默的，不是缺席的。

順帶解掉上游 `T-09`：上游觀察到 RAM `0x80500000` 有一份 flash `0x060010` 的複本，
而那個 session 沒有人放它進去，因此推論 loader 在 ESC 視窗之前就搬了。
**現在那個推論有指令**：`0x80407E44` 的 `jal 0x80404f38`，
發生在**檢查**當中 —— 這一代把 checksum 算在 RAM 複本上，廠商那一代算在 flash 上。

### (f) 四條寫入路徑，不是一條

**讀出來的**，逐指令：

| 路徑 | 粒度 | 邊界檢查 | 確認 | 回顯 | 單次量級 |
|---|---|---|---|---|---|
| `EB` | 1 byte | **無** | 無 | **靜默** | ≤ 19 bytes |
| `EW` | 4 bytes | **無** | 無 | **靜默** | ≤ 76 bytes |
| `FLR <dst_RAM> …` | flash→RAM | **dst 無** | `(Y)es , (N)o` | 成功/失敗一行 | 整個 flash 區段 |
| `LOADADDR` + TFTP 上傳 | 網路→RAM | **無** | 無 | 大小一行 | MB 級 |

`EW` 那個 `sw` 的 base register 一路追回 `strtoul(argv[0])`，沿途沒有遮罩、沒有比較。

四件會在 bench 上咬人的事，help 字串一件都沒說：
**未對齊位址被安靜地往上進位**（`EW B800311E` 寫到 `0xB8003120`）；
**`EW`/`EB` 完全不回顯**，寫對和寫錯長得一樣，只能用 `DW` 讀回來確認；
**`EB` 不進位、那個構不到的 `sh` 版本往下進位** —— 三個函式三種政策；
**空參數的 `EB`/`EW` 會 `strtoul(NULL)`**，代價一次電源循環。

還有一個讀回來的坑：**`DB`/`DW` 的長度是十進位的**，而 loader 裡其他每一個數字都是十六進位。

### `EH` 在 image 裡，而且構不到

`0x804096F4` 是一個完整的 halfword 寫入器。三個搜尋都是 0（直接 `jal`、
整字面值、`lui`+`addiu`/`ori` 組合），而三個都有正控制
（同樣的搜尋在 `strtoul` 上得 32 個 `jal`，在 `EB`/`EW` 上找到它們的命令表列）。

廠商源碼解釋得一乾二淨：`EH` 的**表格列**被 `#ifdef REMOVED_UNUSED` 包掉了，
`CmdWriteHword` 這個**函式**沒有，而 link 沒開 `--gc-sections`。

後果不只是趣聞：**沒有 16-bit 寫入**，而 datasheet 說 `SFCSR`/`SFDR` 不支援 byte access ——
所以 SPI 控制器只能用 `EW` 戳，`EB` 完全構不到它。

### R4 的重置：`J BFC00000`，而且它本來就是一條指令

**讀出來的**：`J BFC00000` 走特例，寫 `WDTCNR = 0`（`0xB800311C`）然後死迴圈，
而中斷在兩條指令之前就已經全遮蔽，所以只有 watchdog 能離開那個迴圈。

`0xB800311C` 有**四個來源**，而其中一個是行為性的：
8196E 自己的 datasheet §8.2.9 Table 27、廠商 Linux header、
廠商 bootcode 的 `monitor.c`（連註解都一樣）、
以及**這台自己的 loader 在第二個地方用同一個 idiom** ——
`0x8040130C`，就在印完 `reboot.......` 之後，那是燒完 flash 的重開路徑。

**最有用的一格是 `WatchDogIND`（bit 20）**：`1` = 發生過 watchdog reset、
`0` = 上電或 pin reset。C-8 問「watchdog reset 之後 ESC 視窗還在不在」，
而這個位元讓「到底是不是 watchdog 重的」不必用推論回答。

**沒有建立的是時間**。`CDBR = 0x000E0000`（除數 14），但它除的 bus clock
這個 repo 沒有任何一處量過，所以 2^15 是一個計數而不是一段時間。
**在 R1 量到時脈之前，runbook 裡不准出現秒數。**

### (d) 重構：問題換成 rlxfw 的版本

在這裡重跑 13 根針的掃描（0 命中，17 條指令正控制）。答案是「沒有」。

但計畫給 (d) 的理由是「有的話 R4 的 `root=/dev/nfs` 就不必改 kernel 內建 cmdline」。
**廠商 kernel 的 cmdline 在 LZMA 酬載裡，所以 `FLR` 之後戳 RAM 戳到的是壓縮位元組 ——
限制從來不是 loader 的寫入原語，是 image 佈局。而 image 佈局是 rlxfw 自己的。**

推薦：**自己的 image 裡放一塊未壓縮、固定位址的 cmdline buffer，`J` 之前用 `EW` 改。**
零 flash 寫入，一行命令一次改動。(d) 和 (f) 在這裡接起來，
而那是整份文件唯一原創的工程判斷。

### §9：`-m mips:3000` 印的那兩個 `.word`

`0x80407E20` 是 `movz s3,v1,v0`，`0x80407ED8` 是 `movn s3,zero,s4` ——
「是不是 `cr6c`」和「checksum 是不是零」的結果。**兩條都是 MIPS-IV，不是 MIPS-I。**

第一次全域掃描報了 `cache`、`ll`、`clz`、`teq`、`tge` 和一個 `lwr`。
**全部是假陽性** —— 解碼器在讀字串表：`'pload, F'` 解成 `clo`，
`0xc0a80001`（`192.168.0.1`）解成 `ll`。

修法不是更好的解碼器，是**讓工具把它的證據印在結論旁邊**：
每個命中後面附十六進位與 ASCII，讓讀的人可以推翻它。重跑之後：

- `0x80400000`–`0x8040A000`（程式碼）：**只有 `movz` × 12、`movn` × 6，其他全是 0。**
  `tools/opcount.py` 在同一範圍對它的 21 個欄位全部回報 0 —— 包含 `ll`、`sc`、
  `cache`、`lwl`/`lwr`/`swl`/`swr`。
- `0x8040A000` 以上：28 個命中，每一個都看得出是文字或表格資料。

**第二列就是控制項。** 兩個都回報 0 的解碼器什麼都沒證明；這兩個都會叫，
而且它們的假陽性在旁邊那一欄看得見。

順帶用第二支工具重現了 2a 的結論（`stage2` 的 `lwl`/`lwr`/`swl`/`swr` = 0），
連 `0x8040D760` 那個資料區命中的判讀都一樣。

### 而 `movz` 這一格有第三條腿，它是在裝置上量到的

**讀出來的**：loader 自己帶著例外回報器 —— `Undefined Exception happen.`、
`cp0_cause=%X, cp0_epc=%X`、`NOT HANDLE TRAP IN JUMP DELAY SLOT`，
在 `0x8040A4E0`–`0x8040A5B0`，底下 `0x8040A5C0` 是 16 項的 dispatch table。

**量到的**：`check_image()` 必然跑在 loader banner 與 `Jump to image start=` 之間。
**18 份 console 擷取、其中 4 份涵蓋整個視窗，兩個字串一個都沒有。**
8/18 那次冷開機在這個視窗裡花了 4.89 秒，只印了 banner 和 jump。

（這是一個不存在宣稱，所以有控制：同樣的 grep 在同樣 18 個檔裡找得到
`Booting`、`chipName`、`Jump to image start`、`RealTek`，最後一個在 14 個檔裡。）

所以「這顆核心實作了 `movz`/`movn`」的替代解釋，是「有東西**靜默地**模擬它們，
而旁邊那個會印字的例外回報器沒有印」。**那是比較弱的解釋，但它沒有被排除，
所以不准寫成定論。** 記為 C-12，由 R1a 的裸機 RI handler 一條指令解掉。

它同時給 R1d 一件本來會在現場才發現的事：**原廠 loader 已經裝了自己的例外處理**，
所以 R1d 的「把 handler 寫進 `0x80000180` 再讓 I-cache 看見」是在**取代**東西，
不是在填空。

### 還開著的、以及刻意沒做的

新開 C-12（`movz`/`movn`，R1a）與 C-13（`0x8040DBA4` 這個讓 loader
把每個 image 都判成壞的全域旗標，R8，值十五分鐘）。

文件 §8 只寫「bench 要確認什麼、什麼結果會推翻它」，**不寫操作步驟** ——
步驟屬於之後的 runsheet，而「一條命令被手抄進一個不擁有它的檔案」
正是上游 `A2.7` 一次錯四個地方的共同原因。

九列預測裡第 8 列是值得為它排一次上電的那一列：
**watchdog reset 之後 `WDTCNR` bit 20 應該讀到 1，上電之後應該讀到 0。**
兩者相同的話，這個位元在這顆上不具鑑別力，C-8 得換一個可觀察量。

### 下一步

`DAY-ZERO` 第 6 項（建容器）、第 7 項（`hazlint`）、第 8 項（`rlxprobe`）。
第 5 項是這一節唯一要碰硬體的。

---

## 2026-08-23（同日，第二段）— 第 5 項的桌面準備，以及第 7 項的控制升級

桌面日，未接觸裝置。起因是一個問題：**「不先做第 5 項（唯一的硬體項）嗎？」**

### 這個問題的答案是對的，而理由比計畫寫的多一條

三條，第三條計畫沒寫：

① **`S0` 是現行 gate，而第 5 項是唯一擋著它的東西。** 第 6/7/8 項是 R1／R2 的前置。
先做它們，等於讓現行 gate 開著去做下一個 gate 的輸入 —— gate board 上 `S0` 會一直是 `~`。

② **E5 成功的話會多一條不依賴 loader 的救援路徑。** 今天這個沒有備機的專案，
整個救援故事是「loader 的 TFTP 救援還答得動」。**一條路徑，而且它跑在最可能壞掉的那個東西上。**
多一條 in-system 讀取路徑，會改變 R8 以及之後每一次 flash 寫入的風險輪廓。
那值遠超過它的四十分鐘。

③ **它幾乎不花電源循環。** E0／E1／E2 不通電或用板子自己的變壓器，E3 是免費的。

### 但照計畫上機會浪費半場，原因是一個沒人確認過的假設

**讀出來的**（datasheet §6）：`RESET#` 是 **pin 49，與 `LED_PORT3`／`GPIOB[5]` 共用**。
所以那支腳在這個設計上**可能根本是 LED 驅動**，不是 reset 輸入。

而計畫的實驗 2 和 3 都以「把 SoC 按在 reset」開頭。**兩個裡有兩個跑不了。**

桌面查到三件事，都指向那顆按鈕是 `RESET#`，但**三個「不存在」不是一條線**：

| 找到什麼 | 怎麼找的 |
|---|---|
| 板上電源孔旁邊有一顆按鈕 | 上游 `notes/hardware-inspection.md` §7 |
| **rootfs 全部執行檔 0 命中** reset button / restore default / gpio button | `strings` 掃 `bin`、`sbin`、`usr/bin`、`usr/sbin` |
| **廠商 kernel 0 命中**，而 **13 個 `gpio`／`GPIO` 字串在** | `strings` 掃 LZMA 解出來的 3,374,772 bytes。**那 13 個字串就是控制項** —— 掃描看得見 GPIO 程式碼，只是沒有按鈕的 |
| 這台的 loader 只輪詢 UART | 第 4 項的 `loader.json`，`interrupt_wiring.console_input` |

**所以順序改成 `E3 → E0 → E1 → E2 →（E4 → E5）`，因為 E3 免費而且擋著另外兩個**：
console 接著、按下去，印出 stage-1 的 `Booting...` 就是 `RESET#`。記為 C-14。

### 第二個問題：計畫的實驗 2 只測得到一半

**讀出來的**，而且它一直在已有的數字裡：`WP#` = 1.79 V、`HOLD#` = 1.79 V、`VCC` = 1.70 V。
`WP#`／`HOLD#` 在這顆 part 上是接到電源軌的，所以**板上的 3.3 V 網路本身就在 1.79 V**，
而 flash 的 `VCC` 腳比它低 90 mV。

**那 1.5 V 掉在「注入點到板子」之間，不在板子裡面。** 一句話把剩下的假說切成兩個：

- **H1 電流預算** —— 板子吃的比源頭給得起的多，源頭垮掉。預測：**壓降出現在源頭**。
- **H2 串聯電阻** —— 夾具接觸與排線是幾歐姆，板子的一般耗電就在上面掉了 1.5 V。
  預測：**壓降出現在線路上**，穩壓輸出還是 3.3 V。

**計畫的實驗 2 只測 H1。** H2 為真時它會被讀成「H1 被否證」，而 H2 從頭到尾沒被測過。
改成一次 **IR-drop walk**：沿五個節點量一遍，最大的那一階就是答案。
**同一支電表、同樣五分鐘，但它給的是位置而不是是非題。**

### 一個計畫沒有、但少了它會誤判的實驗

**E0：夾具到底有沒有接觸。** 板子用自己的變壓器跑著、**CH341A 拔離 USB**，
量夾具 pin 8 那條線的另一端。約 3.3 V = 接觸沒問題；量不到 = 夾子根本沒咬上。

**接觸不良和板子吃電，從晶片端看起來一模一樣。** 沒有這一條，
後面每一個實驗都可能為了一個與 SoC 無關的理由失敗。

### datasheet 給的兩件事，一件降低風險、一件升高

**降低**：power-on strap 腳是 `MA[10:8]`（44、52、53）與 `RAS#`／`CAS#`（51）—— DRAM 那些。
**`SF_*` 不是 strap 腳**，strap 在電源過 0.7 V 之後 300 ms latch。
所以外部 master 在開機時掛在 SPI 匯流排上，**不會改到 SoC 的 strap 設定**。E5 少一個危險。

**升高**：`SF_CS0#`（pin 45）與 `SF_SCK`（pin 48）是 SoC 的**輸出**，
而手冊**沒有說** `RESET#` 拉低時它們會 tri-state。若沒有，燒錄器就是在對推挽輸出對幹。
**中止條件因此寫進 `notes/power-and-programmer.md`，而且明講：
E0–E4 就足以關掉 S0b，E5 可以留給一次帶邏輯分析儀的場次去「看」而不是「假設」。**

（另外 datasheet §1 說這顆「只需要 3.3 V 外部供電，內建 SWR/LDO 把 3.3 V 轉 1.0 V 當 core」。
所以從 flash 的 `VCC` 腳注入，是拿一個夾子的接點去餵 SoC core、SDRAM、五埠交換器和 WLAN。
計畫原本那個假說現在有 datasheet 撐著，不再只是直覺。）

### 第 7 項的控制升級 —— 今天那個錯誤的用處

`hazlint` 原本的正控制是「對 stage 2 必須**零報**」。
**一個期望答案是零的控制，分不出「檢查正確」和「檢查沒在看」。**

第 4 項那次假陽性意外給了它更好的 fixture：**同一份 stage 2，期望答案不是零。**

| 區域 | 期望 |
|---|---|
| `0x80400000`–`0x8040A000` | **恰好 18 筆：`movz` × 12、`movn` × 6**，位址逐一列在 `docs/loader-command-semantics.md` §9。其餘每格 0 |
| `0x8040A000` 以上 | **28 筆必須被判成資料** |

**一份 fixture 同時測兩個方向**：報不足漏掉那 18 筆，報過頭把字串表算進來。
它擋住的實際風險有兩個：`-march=mips1` 編出來的東西若出現 `movz`/`movn`，
就是 toolchain 沒遵守旗標；而廠商的 rsdk **確實**發了這兩條（loader 就是證據），
所以 R2 的 toolchain 等價性必須知道原廠當年瞄準的等級高於 MIPS-I。

**預設值不動**：C-12 解掉之前 `-march=mips1` 仍然是安全側。改的是控制清單 ——
從「證明沒有東西」升級成「證明數得對」。

### 產出與下一步

`notes/power-and-programmer.md`：Part 1（假說、六個實驗、預測、中止條件）**寫完，上機之前寫的**；
Part 2 是空的表格，等 bench。計畫的第 5、7 項改寫，`PROGRESS.md` 三條 Correction、C-14。

下一步是**上機**，而且 `S0b` 一關，`S0` 就關。

---

## 2026-08-23（同日，第三段）— `S0b` 判 `⊘`，C-3 關掉，B1 runsheet

桌面日，未接觸裝置。

### `S0b` 不做，而代價比看起來小

**決定**：`⊘`，分類「卡在儀器上」（`plan/` §17 第 5 項）外加一個明說的風險決定。

兩個理由，順序有意義：
① **唯一沒試過的變體做不到** —— 業界標準的 in-system 讀法是「板子自己供電、
燒錄器 `VCC` 不接」，而這副 SOIC-8 夾具的另一端是**焊死的**，`VCC` 線開不了。
（用膠帶絕緣夾子的 pin 8 接點可以在機械上開它 —— 但那不碰理由②，而②才是決定性的。）
② **剩下的風險落在唯一一台裝置上** —— `SF_CS0#`（pin 45）與 `SF_SCK`（pin 48）
是 SoC 的**輸出**，datasheet 沒說 `RESET#` 拉低時它們會 tri-state。
那是輸出對輸出，小心解決不了，只有量測能解決，而那要邏輯分析儀。

**一台機器、沒有備機。一條可能弄壞裝置的救援路徑不是救援路徑。**

**而這一節存在的目的，桌面上已經拿到了。** 它的目的是「把『量到 1.7 V 就放棄』
換成一個解釋」。解釋在已有的數字裡：`WP#` = `HOLD#` = 1.79 V 對 `VCC` = 1.70 V，
而那兩支在這顆 part 上接電源軌 —— **所以板上的 3.3 V 網路本身就在 1.79 V，
那 1.5 V 掉在注入點到板子之間，不在板子裡面。** 加上 datasheet §1
「只需要 3.3 V 外部供電，內建 SWR/LDO 轉 1.0 V 當 core」，
從 flash 的 `VCC` 腳注入就是拿一個夾子的接點去餵 SoC core、SDRAM、五埠交換器和 WLAN。

**沒拿到的是 H1（電流預算）對 H2（串聯電阻）的分離** —— 而它現在記為「未定」，
不是被猜掉。`plan/` §17 第 5 項（dump 的獨立第二儀器）維持開著，
而它缺什麼現在講得很精確：一副 `VCC` 線開得了的夾具，
**以及**一次「看到」`SF_CS0#`／`SF_SCK` 在 reset 下確實浮空的量測，而不是假設。

**S0 因此不能今天關** —— C-10（雲端副本 ③ 從沒讀回來驗過）還開著，
而那是十分鐘的桌面工作，不是上機工作。gate 的定義也跟著縮小了，並且寫在 gate board 上。

### C-3 的殘留：我上一輪答應要做、沒做，補做之後結論相反

`docs/loader-flash-write.md` 寫「`v0` 是回傳暫存器，除非兩個 caller 之一存起來，
否則沒有固定位址可讀 —— **那還沒追**」。追了：

**兩個 caller 都沒存**（第一次呼叫的結果整個丟掉，那是喚醒/沖匯流排的 dummy read；
第二次的結果 `srl 8` 進 `s1`）。**但值在下一層被存了。**

`s1` 被交給 `0x8040533C`，而它把一筆 72 bytes 的描述子寫進 `0x8040FBD4 + chip*72`：

```
80405390   sw   a1,0(s0)     ; +0  = JEDEC ID
80405398   sb   v0,4(s0)     ; +4  = manufacturer
804053bc   sw   s1,12(s0)    ; +12 = capacity = 1 << address_bits
804053c0   sw   s3,16(s0)    ; +16 = block size
804053dc   sw   s2,24(s0)    ; +24 = sector size
```

**所以 `DW 8040FBD4 8` 在 `<RealTek>` 提示字元下就讀得到 JEDEC ID**，
零新程式碼、零風險 —— 而且**同一行輸出裡有四個可預先算出來的欄位當控制**
（`+12 = 00400000`、`+16 = 00010000`、`+20 = 00000040`、`+24 = 00001000`）。
四個對了，第五個才可信。

**那句話錯在哪**：它對 caller 的判斷是對的，對結論是錯的。
**一次在第一個看起來合理的邊界就停下來的追蹤。**

### 同一次追蹤翻出一件 R8 的事

這台走的是**未知晶片的 fallback**（所以 banner 印 `chipName: UNKNOWN`），
而 fallback 硬寫 `li a2,22` → `1 << 22` = 4,194,304 進描述子 `+12`。

而 `docs/loader-flash-write.md` §1 早就讀出 `burn()` 唯一的邊界檢查就是
`lw a3,12(s0)` —— 那個 `+12`。

**所以這台的 loader 唯一的邊界檢查是一個「未辨識晶片」的預設常數，
而它對，是因為 2014 年的合理預設剛好是 4 MiB。loader 從來不知道它的 flash 多大，它是用猜的。**
R8 不能靠那個 bound；`flashguard` 得自己擋 `CLAUDE.md` 的下限。

### 🔴 `AUTOBURN` 預設是 1

預先算 bench 期望值時順手讀到的：`0x8040D4A0` 在 image 裡的初始值是 **`0x00000001`**。

**所以 loader 開機時 auto-burn 是開著的。** 一次沒先送 `AUTOBURN 0` 的 TFTP 上傳完成，
就會被寫進 flash。**之前所有寫法都把送 `AUTOBURN 0` 當成保險；它是必要條件**，
而 R0 的「零 flash 寫入」整個靠它。

這是一個「為了當控制項而算的期望值，結果自己變成發現」的例子。

### 順帶：一個與上游對不上的八個位元組

上游 `RUNBOOK` §8.12.10 把自解壓 stub 放在 flash **`0x060030`**（`3c 10 80 5f`）。
這裡量到那個字在 **`0x060028`**，早八個位元組（另外兩處在 `0x060250`、`0x060EF8`）。
記下來而不去改上游 —— 它可能是在描述 stub 區段從哪裡開始而不是那個字的位址，
而且它支撐的結論（cmdline 在壓縮酬載裡）兩種讀法都不受影響。

### `RUNSHEET.md`，這個 repo 的第一份

問題是「我們的東西都是 dump 看出來的，要不要實際測一下」。要，而且現在就有一場
**零風險、零新程式碼、零 flash 寫入、一次電源循環**的可以做。

B1 有 17 格，每一格都帶著**上機前算出來的期望值**：

- **B1 是全域控制**：`DW 8040DBC0 1` 必須回 `8040B070 00000000 80409A9C 8040B074`。
  對了，載入基底、表位址、16 bytes stride、欄位順序、以及「RAM 裡就是 dump 裡那份」全部一起對。
  **不對就停，這張表後面每一個位址都不可信。**
- **B5 是一個很尖的預測**：`gCHKKEY_CNT` 應該正好是 **16** ——
  `ceil(987138 / 65536)`，一次 64 KiB 一格，而且只有 kernel image 走到 checksum 迴圈。
  兩個初始值在 image 裡都是 0，所以這個數是乾淨的。
- **B8／B9 用三種方式測同一件事**（`DW` 的長度是十進位）。
  `DW 8040DBC0 A` **什麼都不印**是其中最漂亮的一個：`strtoul("A",_,10)` = 0，長度 0，直接返回。
- **C3 測 `EW` 的靜默向上進位** —— R4 的 cmdline 方案整個站在「`EW` 寫到你叫它寫的地方」上。
- **D2 是值得為它排一次上電的那一格**：watchdog reset 之後 `WatchDogIND` 應該讀到 1，
  上電之後讀到 0。相同的話這個位元不具鑑別力，C-8 得換觀察量。

「不准打」清單裡多了一條，而且是今天才知道要防的：**任何 TFTP 上傳** ——
因為 `AUTOBURN` 預設是 1。

### 下一步

上機跑 B1。另外 **C-10 是十分鐘的桌面工作，而它是 `S0` 剩下的唯一一件事**。

### 補：上機那天的實務，以及 B2 的位置

查了上游 `console-dump.py` 的實際介面，發現一件必須寫進 runsheet 的事：
**`cmd` 子命令有一份 `FORBIDDEN` 清單，會主動拒絕 `EB`、`EW`、`AUTOBURN`、
`LOADADDR`、`FLW`、`J`**，並且回一句「這支工具只讀。真的要寫，自己打進 picocom，
在你決定了之後」。

**那是對的設計，而繞過一個刻意的拒絕比小心地手打更糟。** 所以 B1 的分工是：
A/B 段走工具（`DW`、`DB` 不在清單上），C/D 段關掉工具、開 picocom 手打。
一個序列埠一次只能一個程式，而 read-then-write 的順序本來就對得上這個切換。

順帶把上游那個「`--at-prompt` 忘了加，工具會報三個都不是真因的原因」的坑
寫進 runsheet 的驅動說明。

**B2（PHY）建好位置但沒寫內容**：`PHYR`/`MDIOR` 兩個 handler 沒追過，
而它們正好是六個「不檢查 argc 就 deref `argv`」裡的兩個，
且四個 handler 在線性讀法下被分類錯過。**這份檔案的規矩是「每一格帶著上機前算出的期望值」**，
所以未追過的命令不進 runsheet。B2 要開始之前需要三樣東西，列在檔案裡。

---

## 2026-08-23（同日，第四段）— B2：PHY 與交換器，以及「零風險」那句話是錯的

桌面，沒碰路由器。目標是把 `PHYR`／`MDIOR` 追出來，讓 B2 有資格跟 B1 同一次上電。
產物：`docs/loader-phy-and-switch.md`、`RUNSHEET.md` 的 B2 段與改過的 B1 框架。

### MDIO 介面：三個來源，而且最強的那個是這顆 part 自己的 datasheet

`phy_read` 在 `0x80402F80`、`phy_write` 在 `0x80402FF8`。

`MDCIOCR = 0xBB804004`（bit31 讀/寫、PHYADD 28:24、REGADD 20:16、WRDATA 15:0）、
`MDCIOSR = 0xBB804008`（bit31 忙碌、RDATA 15:0）——**A（這台自己的 code）、
B（廠商 bootcode 標頭）、D（RTL8196E datasheet Table 57/58/59）逐個欄位對上**。
再加一個：廠商 **kernel** 的 `rtl8651_getAsicEthernetPHYReg()` 跟 loader
一句對一條指令。SPI 那次拿到兩個來源，這次是三個。

順手撈到一件事：那句 `delay(10)` 在 B 裡是有條件的 ——
`if (REG32(REVR) == RTL8196C_REVISION_A) mdelay(10); //wei add, for 8196C revision A.`
**A 沒有那個版本判斷，無條件延遲 10 ms。** `MDIOR` 掃 32 次的成本就是這裡來的。

### 🔴 「PHY read」會寫兩個暫存器，而它的延遲有四層前提

`phy_read()` 寫 `MDCIOCR`，並且 **`GIMR |= 1<<8`（`TCIE`）而且不還原**。
追下去才知道為什麼非寫不可：

```
timer ISR 0x80408EE0  ->  (*(uint32*)0x8040DCE8)++      ← 唯一的寫入者
tick()    0x80408F10  ->  return *0x8040DCE8
delay(ms) 0x80407CF0  ->  忙等 tick 前進 ms/10
```

`0x8040DCE8` 只有 ISR 會寫。所以 `delay()` 要回得來，需要四層同時成立：
`Status.IM[7:2]` 沒被遮（`0x80406694`）、`Status.IE=1`（`0x8040865C`、
`0x80408494`）、`TCCNR`/`TCIR` 有裝（`timer_init`）、以及 `GIMR` bit 8。

**而第四層是 `doBooting()` 自己清掉的** —— `GIMR = 0` 寫在
`0x804086E4` 和 `0x80408700`，它的兩條路都寫。所以 loader 自己的網路初始化
是在 `GIMR = 0` 之後跑的，`phy_read` 那一行不是順手，是不寫就會卡死。

**B2 的第一格因此是一道閘**：`DW 8040DCE8 1` 隔十秒讀兩次。
不前進就一個 PHY 命令都不准送 —— 板子會卡在延遲裡，不是卡在 MDIO 輪詢裡。
這是今天最值得的一格，因為在此之前第一次 `PHYR` 是在賭一次電源循環。

### 這道閘順便把 C-8 缺的那個數字生出來了

`timer_init` 的參數是 `0x8040DBA0` 的編譯期常數，image 裡是 **`0x0BEBC200`
= 200,000,000**。配上 `CDBR` 除數 14 與 `TC0DATA = 142858`：

```
200e6 / 14 / 142858 = 100.0 Hz          （推論，待量測）
```

而 `delay(10)` 正好是一個 tick = 10 ms，跟 B 的 `mdelay(10)` 對得起來。

C-8 現在寫的是「wall-clock 沒建立，因為 `CDBR` 除的那個匯流排時脈沒量過」。
**兩個 `DW` 加一支碼錶就量到了。** 若 tick 是 100 Hz，200 MHz 就是矽片上量到的
而不是編譯進去的信仰；若不是，那更值錢。

### 四條命令、三種參數慣例，而 help 字串有一條是錯的

| | argc 檢查 | argv[0] | argv[1] | argv[2] | 做什麼 |
|---|---|---|---|---|---|
| `MDIOR` | 有（`bgtz`） | **暫存器，十進位** | — | — | **掃 phyid 0…31** |
| `MDIOW` | 有（`slti 3`） | phyid，十六 | **暫存器，十進位** | data，十六 | 單發寫 |
| `PHYR` | **沒有** | phyid，十六 | 暫存器，**十六** | — | 單發讀 |
| `PHYW` | **沒有** | phyid，十六 | 暫存器，**十六** | data，十六 | 寫完再讀回 |

三件會產出「錯得很像對」的事：

**一、`MDIOR` 的 help 說 `MDIOR <phyid> <reg>`，但它只吃一個參數，而那個參數是
暫存器編號，十進位，PHY 位址是它自己掃的。** `MDIOR 0 2` 會被接受，把 `2` 丟掉，
掃暫存器 **0**。32 行輸出裡沒有一行會告訴你。format string 是第二個證人：
`Reg=%02d` 印十進位，旁邊兩個欄位印十六進位。

**二、兩條 `MDIO*` 用十進位、兩條 `PHY*` 用十六進位解析暫存器。**
0–9 一致，10 以上分歧，而 MII 的 vendor 空間從 16 開始。

**三、`PHYR`／`PHYW` 完全不看 argc。** B 的 `CmdPHYregR` 也不看 —— 同一列命令表、
同一句 help、同兩句 format string（連 `regID` 旁邊逗號的位置都一樣，這就是
image 裡兩句 `Find PHY Chip!` 怎麼分辨的：`0x8040B5B8` 是 `PHYR` 的、
`0x8040B5EC` 是 `PHYW` 讀回的那句）。

**而 `MDIOR`／`MDIOW` 在廠商樹裡是別的東西** —— 唯一一處在 `test_slvpcie.c`，
是 PCIe slave port 的暫存器讀寫，只是撞名。拿 B 去推 A 會得到一個很有自信的錯答案。
所以 `MDIOR`／`MDIOW`／`PORT1` 三條都是單一來源，用到它們的格子上要寫明。

### 🔴 `PORT1` 是工廠測試的 PHY 寫入迴圈，不吃參數，而工具擋不住它

第 17 條命令，從沒追過，就在 PHY 那四條旁邊。help 說 `PORT1: port 1 patch for FT2`。
`0x8040A294` 是三行 wrapper，真正的東西在 `0x8040A0A0`：

```
17 個字的表從 0x8040B84C 複製到堆疊        ; 5400 5440 54C0 5480 5580 ...
0x8040B890 的四個位元組 = 00 02 03 04       ; 目標 PHY 位址
外圈 17 次 × 中圈 4 次：
    phy_write(4, 31, 1) ; phy_write(4, 20, 0xB20|(1<<phy)) ; phy_read(4, 20)
    phy_write(phy, 31, 1)
    內圈：phy_write(phy, 19, table[i])      ; printf("... gray_code=%x")
    phy_write(phy, 31, 0)
```

**約六百次 PHY 暫存器寫入，用 31 號做 page select，沒有中止路徑。**
loader 自己把那張表叫做 `gray_code`。

而 `console-dump.py` 的 `FORBIDDEN = ("FLW","EB","EW","AUTOBURN","LOADADDR","J ")`
**沒有「暫存器寫入」這個概念** —— `PHYW`、`MDIOW`、`PORT1` 三條都過得去。
那支會拒絕 `EW`、附一句「這支工具只讀」的工具，會一聲不吭地送出 `PORT1`。

不去改它：`upstream/` 釘死在 `4d3ff26`，那個釘就是 R9 差分證明的全部可信度。
**改的是 runsheet 的「不准打」清單**，跟當初處理 `--at-prompt` 那個坑同一個做法。

### 我本來要用的第二儀器，查完不成立

原本想用 B 的 `PHY_BASE = SWCORE_BASE + 0x2000`（每個 port 的 MII 0–5
記憶體映射影子，`PORT0_PHY_IDENTIFIER_1 = 0xBB802008`）當作**不經 MDIO** 的
獨立第二路徑去讀 PHY ID。

兩個理由不行：**D 的 §11 在這顆 part 上沒有這個 block**（Table 57 那個
`0xBB80_4000` 區只有 `04` 和 `08` 兩格）；而且**把 image 裡 48 個 `lui …,0xbb80`
全部解到後面的 `ori`／位移之後，13 個位址全在 `0xBB804xxx`，一個都不在
`0xBB802xxx`**。單一來源，而且來源是別的世代。

換上來的東西更好而且有兩個來源：**`PCRP1`–`PCRP4`（`0xBB804108`–`0xBB804114`）
的 bit 30:26 是 `ExtPHYID`，datasheet Table 64 說 port0~4 預設就是 0x0~4，
而 loader 只設定 `PCRP0`、沒有迴圈碰其他四個**，所以它們還是 reset 預設值。
`DW BB804100 8` 一行，不經 MDIO 讀出交換器自己認定的 port↔PHY 位址對應。

### PHY ID 算不出來，而這件事本身要寫進格子裡

B2 的 stub 說「PHY ID 是矽片固定的，顯然可以先算出來」。找過了，**算不出來**：
D 完全沒有 PHY 的 MII 暫存器表；B 裡唯一的 PHY-ID 常數是 `0x001CC912`，
它自己的註解說那是「8212 two giga port」，外接千兆的東西；B 的工廠測試副程式
是把期望值當參數傳進去而不是寫死；而**上游所有 console capture 裡沒有一次
`Find PHY Chip!`** —— 因為那兩句只由 `PHYR` 和 `PHYW` 印，而這台從沒打過。

所以 E4 那格帶的是結構性期望：不能是 `0000` 也不能是 `ffff`；
**0、2、3、4 四個位址必須讀到同一個值**（`PORT1` 用同一張表 patch 這四個，
那是 A 自己說它們是同一個 macro）；而**位址 1 是那個被跳過的**，
一樣 → `PORT1` 跳過的理由跟 port 有關；不一樣或不回應 → 跟 PHY 有關。

那一格的判定欄要寫「這是量測，不是確認」。

### 一件 datasheet 說「保留」而板子自己反駁的事

loader 在 `0x8040371C` 和 `0x80403904` 做 `PITCR |= 1`。
D 的 Table 63：`Port0_TypeCfg[1:0]`，`00: UTP (10/100M embedded PHY)`、
**`01: Reserved`**。

而 `upstream/dumps/uart-bootloader.log`（**量到的**）在 `---Ethernet init Okay!`
上面那行是：

```
P0phymode=01, embedded phy
```

**這顆晶片自己的 boot loader 給了一個 datasheet 說「保留」的值一個名字。**
那份 datasheet 是草稿（`Rev. D1.1`，有浮水印）。記下來，不去解釋。

### 順帶：同一份 capture 跟 C-13 對得上

那份 capture 走到 `<RealTek>` 而**沒有印 `---Escape booting by user`**。
那句話在 `doBooting()` 的非零分支（`0x804086D0`），沉默的是 `beqz a0` 那條 ——
也就是 `check_image()` 回 0。而 C-13 說的就是 `gCHKKEY_HIT` 會讓
`check_image()` 直接宣告「沒有 image」。

**相符，不是證明**：`0x80408320` 那個 ESC 等待的回傳約定還沒追，翻過來讀法就翻。
寫進 C-13 的格子裡，標著這句話。

### 上機的執行順序

`B1 §A` → `B1 §B` → `B2 §E`（走工具，`PHYR`/`MDIOR` 不在拒絕清單上）→
關工具開 picocom → `B1 §C` → `B1 §D` → **`B2 §F`**。

`§F` 只有兩格，而第一格 `PHYR 5 2` 是**整場唯一可能結束這次上電的一格** ——
`MDCIOSR` 那個等待沒有 timeout、沒有次數上限，datasheet 說 `ExtPHYID` 只配到
port 4，所以位址 5 應該不回應。回得來，`MDIOR` 才准掃。放在最後，
是因為到那時候前面全部已經抓完了。

### 今天改掉的說法

- 「PHY 那一場零風險零程式碼」—— 零程式碼對，零風險錯。
- 「用廠商的 `rtl865xc_asicregs.h` PHY block 當第二來源」—— 那個 block 在這顆上不存在。
- 「PHY ID 可以先算出來」—— 算不出來，而且四個來源都查過了。
- `PORT1` 不在「不准打」清單裡，而工具會送它。
- `MDIOR` 的 help 是錯的，廠商樹裡的 `MDIOR` 是另一個東西。

### 下一步

上機跑 B1 + B2，一次上電。另外 **C-10 是十分鐘的桌面工作，而它是 `S0` 剩下的
唯一一件事**。

---

## 2026-08-23（同日，第五段）— C-10：儀器做好了，而備份自己的清單只蓋到 19 個檔裡的 7 個

桌面，沒碰路由器。C-10 是 `S0` 剩下的唯一一件事。

### C-10 問的是什麼

`S0a` 做了三份副本，讀回來驗過兩份。**「上傳回報成功」跟「上面躺的東西是對的」
是兩個不同的主張**，而第二個從沒被檢查過。那就是 C-10。

### 先量到的：那份 ciphertext 清單蓋不到一半的檔案

`CIPHERTEXT-SHA256.txt` 列了七個 `.age` 封裝。備份集裡有 **19 個檔案**。
沒被蓋到的 12 個：

```
CIPHERTEXT-SHA256.txt              K1-set.par2            K1-set.vol000+200.par2
K1.pub                             K2-set.par2            K2-set.vol000+339.par2
K2.pub                             RESTORE.md
tools-for-restore/{DEBS-SHA256.txt,README.txt,age_*.deb,zstd_*.deb}
```

**兩組 par2 復原卷都在裡面，而它們是整份備份裡唯一能「修」的東西。**
`age` 對每 64 KiB 做一次認證，所以它**偵測**得到位元腐蝕；`S0a` 自己就寫過
它不能**修復**，par2 才能。結果會修的那個沒人在驗。

**`K1.pub`／`K2.pub` 也在裡面。** 它們的用途是：`age-keygen -y` 從私鑰導出公鑰，
跟 `.pub` 比對，同時抓出「抄成另一把合法金鑰」與「K1/K2 標籤寫反」。
一個壞掉的 `K1.pub` 會讓那個比對不符，然後你會去懷疑私鑰 —— 在最不該懷疑錯的時候。

### 做出來的儀器

`tools/verify-backup-copy.sh`，兩個模式：

```
verify-backup-copy.sh <參考副本> <待驗副本>
verify-backup-copy.sh --self-test <參考副本>
```

它雜湊全部 19 個檔，並且**分開報 `DIFFERS` / `MISSING` / `EXTRA`** ——
因為「這份副本沒壞」跟「這份副本是完整的」是兩個主張，而只有第一個在被問。

**自我測試四格，其中三格是「這支工具會不會失敗」：**

| | 造的缺陷 | 期望 | 實測 |
|---|---|---|---|
| C0 | 沒動 | 0 | 0 |
| C1 | 翻一個位元組 | 1 | 1 |
| C2 | 刪一個檔 | 1 | 1 |
| C3 | 多一個檔 | 1 | 1 |

C0 單獨看什麼都不證明，這就是 C1–C3 存在的理由。
（C1 用 `x` 蓋掉第一個位元組；若那個位元組本來就是 `x`，C1 會報 0 而**當場失敗**，
所以這一格保護得了自己。）

### 副本 ① 是乾淨的，所以拿它當基準是有根據的

`sha256sum -c CIPHERTEXT-SHA256.txt` → **7/7 OK**。
比對副本 ③ 之前先確認基準沒漂，否則比出來的東西沒有意義。

### 一個名字差一個字的資料夾

`C:\Users\Key20\rlxfw-backup-2026-08-23` **不是副本 ③**：

```
11 個檔逐位元組相同，8 個 MISSING
（K2-set.par2、K2-set.vol000+339.par2、disclosure.tar.zst.age、meta-K2.tar.zst.age、
  tools-for-restore/ 四個）
```

也就是 K1 側的嚴格子集 —— 跟 `S0a` 記在 USB 上那個同名資料夾同一個東西。
`S0a` 已經把「兩個名稱近似、內容不同的資料夾並存」記為還原時的誤選風險；
**現在它在兩個媒體上各有一份。**

順帶：這次比對跑在 `/mnt/c` 上，而 `CLAUDE.md` 說二進位不放 `/mnt/c`。
那條規則的理由是 DrvFs 丟權限位元、NTFS 大小寫不敏感 ——
**這裡只雜湊檔案內容、沒有 symlink、沒有大小寫相近的路徑，所以不適用。**
規則有理由，理由不成立時要說出來，而不是繞過去。

### 為什麼 C-10 今天關不掉

**沒有 Drive 客戶端**：`rclone`／`gdrive` 都沒裝，沒有掛載的 `G:`，
沒有 Google Drive 桌面版（`%LOCALAPPDATA%\Google\DriveFS` 不存在）。

而且**就算裝了 `rclone`，`rclone check` 的預設路徑也回答不了 C-10**：
Google 回的是它**在上傳當下記下**的摘要，那正好是「上傳有沒有正確到達」——
C-10 問的是另一個主張。要答 C-10 只能 `--download`，也就是真的讀回來。
**這件事本身就是 C-10 的重點。**

所以剩下的是一個作者才能做的下載動作。做完之後一行指令就有答案，
而且那一行同時回答「有沒有壞」與「是不是完整的」。

### 下一步

作者把 Google Drive 上那份下載到本機，跑
`bash tools/verify-backup-copy.sh /home/key/rlxfw-backup/2026-08-23 <下載的目錄>`。
`MISSING` 那幾行會直接說出上去的是完整 19 檔還是 11 檔的 K1 子集，
而那兩種結果對 `S0` 的意思不一樣。

---

## 2026-08-23（同日，第六段）— C-10 關掉，`S0` 跟著關掉；以及上機前的四項檢查

### C-10：副本 ③ 讀回來了

作者從 Google Drive 下載到 `C:\Users\Key20\Desktop\rlxfw-backup`。19 個檔全在。

| 檢查 | 結果 |
|---|---|
| `verify-backup-copy.sh` 對副本 ① | **19/19 逐位元組相同，0 MISSING、0 EXTRA** |
| 下載的樹自己的 `sha256sum -c CIPHERTEXT-SHA256.txt` | 7/7 OK（獨立第二次） |
| 正控制：把下載樹的 `K1.pub` 翻一個位元組 | **恰好一筆 `DIFFERS K1.pub`** |

第三列是重點：**乾淨的結果來自一支在同一份資料上證明過會失敗的檢查。**

**我上一段的懷疑是錯的。** 我看到 `C:\Users\Key20\rlxfw-backup-2026-08-23`
是 11 檔的 K1 子集，推測上雲端的可能也是同一份。不是 —— 完整 19 檔都上去了。
那是一個從資料夾名字做的推論，而它現在被量測推翻。

### `S0` 因此關掉

`S0a` 的 DoD 是「從副本 ③ 還原到空目錄，逐檔相符」。實際做到的是：
**還原演練從副本 ②**（解密、解壓、manifest 比對，7,770 路徑零差異），
**而副本 ③ 現在證明與該樹逐位元組相同**。
所以「讀到位元組之後」的每一步都是決定性的；沒被測到的是「從 Drive 讀回來」
這條路徑本身，而下載就是在測它。這個論證寫進 gate board 的 evidence 欄，
不是打個勾了事。

`S0` → `✓`，`Actual = 1`。現行 gate 改為 `R0`。**這是第一個關掉的 gate。**

### 上機前的四項檢查，兩項本來會在通電之後才炸

USB 透過 `usbipd` 掛進 WSL。`1-1`（CP2102）與 `3-4`（Realtek USB GbE）都已 `Shared`。

**一、WSL 不會自己活著。** 第一次 `usbipd attach` 回
`There is no WSL 2 distribution running`。這個 repo 的 `CLAUDE.md` 已經記過
「distro 在工具呼叫之間會重啟」；解法是先開一個長命的 WSL 程序把它撐住。

**二、`/dev/ttyUSB0` 起來了。** `cp210x converter now attached to ttyUSB0`，
`key` 在 `dialout` 群組裡，用工具自己的 `Console` 類別開了又關，乾淨。
板子關著時讀到 0 bytes —— 那是通電後「有東西進來」的基線。

**三、🔴 `r8152` 不在 WSL 核心裡。**
`modprobe: FATAL: Module r8152 not found in /lib/modules/6.6.87.2-microsoft-standard-WSL2`。
Realtek RTL8153（`0bda:8153`）要的就是它；`cdc_ether`/`cdc_ncm` 在，但那顆預設不走 CDC。
**所以把網卡 attach 進 WSL，很可能兩邊都看不到它** —— 而 B2 的 `E10`/`E11`
需要的只是「對端有 link」。網卡留在 Windows 側就滿足了，而且保證有 link。
B1／B2 全程不碰網路（runsheet 明文禁止任何 TFTP 上傳，因為 `AUTOBURN` 預設是 1）。
**網卡不 attach。** 它是 R0 才需要的東西，那時再解 r8152。

**四、我自己搞錯一次，值得記。** 我看到 login shell 的 `python3` 是
`/home/key/.venvs/thermal/bin/python3` 而它沒有 `pyserial`，就判定
runsheet 寫的 `python3 upstream/tools/console-dump.py …` 會在通電後炸掉。
**錯了**：那支工具根本不用 `pyserial`，它用 `termios` + `os.open`，只靠標準函式庫，
而且它自己的註解第 213 行就寫著這件事。用那個 venv 的 python3 實際建構它的
`Console` 物件、開埠、關埠，全部正常。

**從原始碼讀出來的結論要用執行來收尾。** 我讀了 `--help` 回 0 就假設是延遲 import，
那是一個聽起來合理的錯誤解釋；直接跑那條路徑才是判準。

---

## 2026-08-23（同日，第七段）— 第一次矽片量測

上機。一次上電，零 flash 寫入。`B1` 的 A/B 段 + `B2` 的 `E1`–`E12` + 一格現場加的
`E2b` + `C5`（`E5` 改寫成寫入版）。`§C1`–`C4`、`§D`、`E11`、`§F` 沒跑，留下一次上電。

原始 log 在 `$FWRE_WORK/rebuild/bench-2026-08-23/`，逐格判定在 `RUNSHEET.md`
兩張 Results 表。這裡只寫「量到什麼改變了什麼」。

### 三個數字

**一、時脈。** `0x8040DCE8` 從 `0x473A` 走到 `0x5F52`，6,168 counts，
量到的經過時間 61.842 秒（讀數兩側各打時間戳）→ **99.74 Hz，對 100.0 Hz 的預測差 0.26%**。

現場加了一格 `E2b` 讀 `TC0DATA`，得 `0x0022E0A0` = 142,858 << 4，跟 image 算的一樣。
配上 `B7` 讀到的 `CDBR = 0x000E0000` —— **四個項有三個在矽片上讀到**：

```
base = 99.74 × 14 × 142,858 = 199.48 MHz     對編譯進去的 0x0BEBC200 = 200,000,000
```

所以 200 MHz 是**推導**出來的不是巧合。順帶把除數欄位的語意也定了：
除數若是 15，base 會是 213.7 MHz，沒有人做那種時脈。

**沒有一起解決的、而且不准當成解決了的**：watchdog 數不數同一個被 `CDBR` 除過的時脈。
數的話 `OVSEL=0000` 是 2.29 ms，不數的話是 164 µs。**要 `D1` 的實測延遲來選，而 `D1` 沒跑。**

**二、JEDEC ID = `0x1C7016`。** 同一行輸出裡四個預先算好的欄位
（`+12/+16/+20/+24`）全部吻合，所以描述子布局對、ID 可信。`C-3` 的主問題關掉。

**三、PHY ID = `0x001CC880`，位址 0、1、2、3、4 全部一樣**，包含 `PORT1` 跳過的位址 1。
**所以那個跳過是關於 port，不是關於 PHY** —— R6 一支驅動涵蓋五個。
`ExtPHYID` 在 `PCRP0`–`PCRP4` 讀到 0,1,2,3,4，完全如預測。

### 一格失敗，揭穿兩格「通過」

`B5` 預測 `gCHKKEY_HIT`=0、counter=16，讀到 **1 和 0**。
從通電前就送 ESC 會設起那個旗標，`check_image()` 頭兩條指令就讀它然後返回，
checksum 迴圈根本沒跑。**預測是為「沒被打斷的開機」算的，而那不是這張表產生的開機。**

因為它失敗才回頭看隔壁，而**隔壁兩格比它更糟**：

- **`B3`**：值 `05060000` 對，但 `0x8040DD3C` 是在**每次呼叫 `check_image()` 之前**
  寫的（`0x804080C0`），裝的是**正在試的**候選。旗標讓每次檢查都失敗 → 掃到最後 →
  最後一個候選是 `0x060000`，**而這台的 kernel 也剛好在那裡。兩種機制同一個答案，
  這格分不出來。**
- **`B4`**：四個字精確吻合，但它宣稱的機制不可能 —— `check_image()` 在複製之前就返回了。
  RAM 裡的東西是誰放的不知道。**開成 `C-16`。**

**一個吻合的數字掩護一個錯的機制**，而要靠一格失敗才把兩格挖出來。
這一段是今天最值得寫下來的東西。

### 我自己死掉的兩個主張

**一、`GIMR` bit 8 在提示字元下已經是 1**（`0x00008100`），不是我寫的 0。
`doBooting()` 的 `GIMR = 0` 是真的，但它不是提示字元之前最後一次寫。
結論還活著（tick 有在走），但 **`E5` 在跑之前就作廢** —— 被預測會翻轉的位元已經在終態。

**二、「datasheet 說保留而 loader 給了它名字」撤回。**
`PITCR` 讀到 `0x00000000`，`PCRP0` 的 `EnForceMode` 是 0 ——
**那整段被 strap 擋住的分支在這塊板上沒跑**，所以 `P0phymode=01` 不是那個欄位。
`PITCR = 0` 就是「UTP (10/100M embedded PHY)」，跟開機那行說的一樣。
**datasheet 沒錯，矛盾是我造的** —— 把印出來的值接到一個欄位上，
卻沒檢查寫那個欄位的程式碼有沒有執行。

### `E5` 改寫成寫入版，過了，而且多帶兩個發現

`E5` 當讀取是死的，改成 `C5`：清掉 `GIMR` bit 8 → 送一發 `PHYR` → 讀回來。

上機前先做了一次呼叫圖走訪，確認命令迴圈 `0x80409144` 走不到
`tick()`／`delay()`／ESC 等待 —— 而同一支走訪器從 `PHYR` 出發正確找到
`PHYR → phy_read → delay → tick`，**所以那個「找不到」是一支證明會響的儀器給的**。

```
GIMR = 00008100   GISR = 88000004
EW B8003000 8000  （靜默）
GIMR = 00008000   GISR = 88000104      ← 清掉了，而且主控台還回話
PHYR 0 2          UID=0x0000001c
GIMR = 00008100   GISR = 88000004      ← 自己回來了
```

**中間那行回得出來**就證明主控台不需要 timer，走訪的結論從論證變成量測。

**而 `GISR` 我沒預測**：`88000004` → `88000104` → `88000004`。
bit 8 是 `TCIP`，timer 中斷 **pending**。遮住時中斷取不走所以**卡在 pending**，
`PHYR` 重新開啟之後 ISR 跑了、ack 了、pending 清掉。
**遮罩、閂鎖、遞送、確認四件事在五行裡全部看得到。**

順帶把 `C1` 和 `C2` 各關掉一半：`EW` 是靜默的（在硬體暫存器上，不是 scratch RAM），
而且**寫在你叫它寫的位址**。R4 的 cmdline 方案整個站在後面那句上。

### 🔴 我違反了 runsheet 的規矩 4，而且它當場付了代價

規矩 4：**命令從這份檔案或工具打，絕不手抄重述。**
我把 `C5` 的序列重述成一張聊天表格。表格欄位複製時會帶前導空白，
而 `0x80407248` 的 tokeniser 是**先存 `argv[i]` 再測分隔字元**的，
所以一個前導空白會把 `argv[0]` NUL 成空字串，dispatcher 對不到任何一條 →
`Unknown command !`。

上游早就記過這個坑。**今天是它第一次在裝置上響，而觸發它的正是那條規矩禁止的重述。**

操作者把它讀成「CP2102 掉了」。**正好相反** —— `Unknown command !` 是板子自己印的字串，
它出現就同時證明了 TX、RX 和命令迴圈三個都活著。掉線是沉默，不是錯誤訊息。

### 還有一件事：原始 log 不在 git 裡

Results 表裡每一個讀數都是我從 log 手抄的，而這個 repo 有一條規矩就是
「手抄是一個背後沒有儀器的主張」。四份 log 一共 5.8 KB，
查過沒有 MAC、沒有序號、沒有任何識別這台實體裝置的東西。
**建議 commit 進 `bench/2026-08-23/`**，讓每一格都有可以覆核的原件。等作者決定。

### 下一次上電要做的

`§C1`–`C4`（`EW`/`EB` 寫 scratch RAM，`C3` 的靜默向上進位是尖的那格）、
`§D`（`J BFC00000`、`WatchDogIND`、按鈕，順便掐 `J` 到重置的秒數給 `C-8`）、
`E11`（換網路孔）、`§F`（`PHYR 5 2` → `MDIOR 2`）。
`§D3` 和 `E11` 要人的手。

---

## 2026-08-24 —— `SPEC.md`：把散在十幾份檔案裡的數字收成一張表

桌面日，未接觸裝置。沒有新的量測，**一個新的觀察**（見下）。

### 為什麼寫它

到今天為止，「這台機器是什麼」這件事散在至少十四份檔案裡：五顆 IC 在
`upstream/notes/hardware-inspection.md`、flash 佈局在 `flash-layout.md`、
主控台參數在 `uart-pinout.md`、暫存器讀數在 `RUNSHEET.md` 的兩張 Results 表、
SPI 與 PHY 的語意在 `docs/` 的三份、快取模型在 `notes/cache-model.md`、
禁寫區與預算在 gitignored 的 `plan/` 裡。要做一個設計決定就得先把它們翻一遍，
而**翻的過程本身就是出錯的地方** —— 這個 repo 已經有一次是把一份筆記裡
為了排版而截掉 ASCII 欄的 `DB` 引文，當成規格拿去寫解析器。

### 三個決定

| 決定 | 選了什麼 | 理由 |
|---|---|---|
| 範圍 | 硬體 + 原廠韌體 + 設計標的（禁寫區、A/B 預算、RAM 預算） | 設計時三段會一起看。只放硬體的話，`TGT-01`/`TGT-02` 那兩條絕對禁令就不在同一張紙上 |
| 標記法 | **數值來源與語意來源分兩欄** | 這個 repo 被「值對、名字錯」咬過兩次（`B3`、`B4`）。單一標記寫不出「`0x187F0038` 是量到的，而它叫什麼是推的」這句話 |
| 防漂移 | 每列一個穩定 ID + 擁有者檔案連結，SPEC 明說自己不擁有任何結論 | 房規第一條。這是**索引**，擁有者檔案永遠贏 |

### 建表過程撈出來的四件事

**一、`E9` 的 transcript 裡有兩個字從來沒被判讀過。**
`DW BB804100 8` 印八個字，而 `E9` 那格只判了前六個（`PITCR` 加 `PCRP0`–`PCRP4`）。
第七、八個是 `0xBB804118` = `00000000` 與 `0xBB80411C` = `187F0038`，
後者 bit 30:26 讀出來是 **6**。照 `PCRP` 每埠 4 位元組的間距，那就是埠 5 與埠 6 ——
**但間距是推的，手上沒有任何來源明寫這兩個位址。** 已補進 `RUNSHEET.md` 的 `E9` 判讀欄，
`SPEC.md` 的 `NET-10` 指回那裡。

同樣的事在 `E10` 也有一份：`0xBB804140` 與 `0x4144` 都讀 `0x7A`，
D 只名到 `PSRP6`，第二個沒有來源。

> **這是「一次上機讀回來的東西，比那格問的問題多」的第二個實例。**
> `C5` 那次是 `GISR` 自己跑出來的，這次是兩個沒人看的字。
> 值得記的不是這兩個數，是**判讀欄的長度是照預測寫的，不是照輸出寫的**。

**二、flash 的 sector / page / block 大小不是這顆的規格。**
`4096 / 256 / 0x10000` 是 loader 在**認不出晶片**時裝上去的 fallback 描述子裡的字面值
（`docs/loader-flash-write.md` §2、`upstream/notes/loader-chip-table.md` §4 都已經說過），
但它們在對話裡一直被當成「這顆 flash 的規格」在用。表上現在把數值標「量」、
語意標「推」，並在 `FLS-06`–`FLS-08` 寫明它們的第二來源是 EN25QH32B 的 datasheet，
**而那份我沒有**。

**三、`CLK-03` 是一格空白，而我原本以為它有答案。**
量到 199.48 MHz、banner 印 400 MHz，÷2 看起來理所當然 ——
**但那是一個讀法，不是一次量測**，而且沒有任何來源說 CPU 時脈與匯流排時脈是這個關係。
留白，附上實驗。

**四、`RF-01`（RTL8188ER）到今天仍然只有一個來源。**
封裝絲印。驅動印的是版本號不是料號。表上把「×1」寫在來源欄，
就是為了讓這種列不能靠排版混過去。

### 順手改的兩處房規

`CLAUDE.md` 加了 `SPEC.md` 那一列，並把語言規則從「英文，工作日誌除外」
改成「英文，工作日誌與 `SPEC.md` 除外」——
**規矩檔和 repo 不一致時是規矩檔錯**，所以改的是規矩檔。
收工那條也加了一句：**一個 session 若產生、改變或否證了一個數字，
`SPEC.md` 在同一個 commit 裡改**。落後的規格表比沒有規格表更糟，因為它看起來是現行的。

### 新規矩第一次生效，就在同一天

同一天 `RUNSHEET.md` 多了 `C6`、`C7`、`D1b`、`D2`、`D2b`（不是這個 session 做的），
其中 `D2` 的桌面查證**推翻了 `B7` 的判讀**：loader 對 `WDTCNR` 只有兩個寫入點，
兩個都是 `sw zero` 後緊接自跳迴圈，所以 `A5000000` 是**硬體 reset 預設值**，
不是 loader 寫上去的。那份查證帶了正控制（同一個方法要找得到 `B7` 在裝置上量過的
`CDBR = 0x000E0000` 寫入點），所以它是一次會失敗的檢查。

`SPEC.md` 因此改了三列（`REG-12`、`CLK-08`、`CLK-10`），新增四列
（`MEM-10` 暖重置後 SDRAM 存不存活、`LDR-06b` 一行載得下 18 個字、
`LDR-06c` 輸入行緩衝長度未量、`LDR-23b` `AUTOBURN 0` 的語法與生效與否都未證）。

**表寫完的同一天就被改了一列，這件事本身是證據**：一張不跟著改的規格表，
壽命大概就是這麼長。

### 這份表最可能怎麼壞掉，先寫在這裡

**它是每個數字的第二份副本。** 現在唯一的防線是「每列帶擁有者連結」加上收工規矩，
**兩個都靠人**。真正的防線是一支 `tools/spec-check.py`：
逐列驗有沒有標記、宣稱兩個來源就真的列了兩個、數值字串仍然出現在擁有者檔案裡，
並帶一個正控制（故意寫錯一列，它必須抓到）。**沒寫，而它應該寫。**
在寫出來之前，這張表的正確性是一句承諾而不是一次檢查 ——
這正是這個 repo 對別人的工具會說的那句話。

### `tools/spec-check.py` —— 上一節說「應該寫」的那支，寫了

七項檢查（C1 id 唯一、C2 標記合法、C3 留白與 §17 的雙向不變量、C4 擁有者檔案存在、
C5 字面值仍在擁有者檔案裡、C6 §18 的去識別化、C7 有值就要有來源），
**八個突變**，每個突變必須產生一個檔案原本沒有的 finding，而且必須由**指名的那一項檢查**抓到。

**第一次跑就抓到 28 件。** 分類之後，沒有一件是誤報：

| 類 | 件數 | 是什麼 |
|---|---:|---|
| C3 `V` 是 `—` 卻擺著一個真的值 | 11 | 手冊上的值（EJTAG、GPIO、PCIe、手冊宣稱的 ISA）被標成「什麼來源都沒有」。**標記表缺一個類別** —— 讀自文件既不是量到的、也不是讀出這台自己的碼。補了第四個標記 `文` |
| C3 留白卻不在 §17 | 2 | `REG-04`、`REG-14` |
| C4 擁有者不存在 | 1 | `FW-16` 寫了 `compcs-decode.md`，那是 upstream 內部的相對路徑，從 repo 根目錄解不開 |
| C5 值不在擁有者檔案裡 | 10 | 大多是**擁有者指錯**：讀數住在 `RUNSHEET.md`，我卻指向擁有語意的 `docs/`。另一件是 `MAP-01`：**KSEG0 = `0x80000000` 這句話，這個 repo 裡沒有任何檔案擁有它** |
| C1 | 1 | id 欄的 🆕 裝飾 —— 這是工具的錯，不是檔案的 |

### 工具自己的四個弱點，也是它自己找出來的

① id 欄可以帶 🆕；② `SOURCES.json` 寫 `0xB800_1000` 而反組譯寫 `0xB8001000`；
③ 年份（`2018`）當字面值會讓每一列都「被自己的日期確認」；
④ `00000000` 出現在每一份 hex dump 裡，拿它當字面值等於什麼都沒比。
全部修掉，而修法都寫在 `matches()` 與 `literals()` 的 docstring 裡。

### 兩個假控制，而它們是這次最值得記的

**`M3` 測的是我自己剛降級掉的那個方向。** C3 原本要求「§17 列到的 ⇔ 值是留白」雙向相等，
但 `RF-01`、`CPU-17` 這些列**值成立而殘留問題還開著**，§17 本來就該列它們。
把反向改成資訊性之後，`M3`（填掉一個留白但不從 §17 拿掉）就沒有東西會響 ——
**一個測試在它要測的性質被改掉之後仍然「存在」，那是最糟的一種綠燈。**
`M3` 改成測 `I2`（真的值配 `V = —`），`M4` 保留測 `I1`。

**`M4` 刪錯了行。** 它刪掉定義列而不是 §17 那列，於是 blank 跟著消失，
檢查當然不響 —— 報出來是 `NOT CAUGHT`，而那正是控制該有的行為。
改成只在 `## 17.` 之後動手。

**還有一個沒被觸發但會發生的漏洞**：如果檔案**本來就有**同類的 finding，
突變會空過。控制現在先算一次 baseline，突變必須產生一個**原本沒有的** finding 才算數。

### 順手修掉兩句已經不真的話

`CLAUDE.md` 開頭寫「today the repo is at S0」，而 `PROGRESS.md` 說 active gate 是 `R0`。
不是把 S0 改成 R0 —— **是整句不再複述 gate**，因為一個 gate id 被複製到第二個地方就會在那裡過期，
而房規第一條就是為了這個。

`refs/README.md` 寫「The tool that enforces this is `tools/regmap-check.py`」。
**那支工具不存在。** 改成說實話：兩來源那條規矩今天靠讀，機械檢查的是更弱的性質，
而且明寫「**沒有任何東西在檢查兩個來源互相同意**」。

### `CLK-08` 被改寫了，而改寫是對的

同一天 `SPEC.md` 的 `CLK-08` 被改寫（不是這個 session）：我原本寫「十檔全部低於儀器解析度」，
那是**把最短那一檔的結論套到全部十檔**。最長的 `OVSEL=1001`（2²⁴）是 84.1 ms 或 1.177 s，
兩個都在解析度之上而且差 14×。同時新增了 `CLK-11`（loader 從沒寫過 `WDTCNR`）。

### `tools/` 的權限位元：一個看起來像美觀問題的東西

`git ls-files -s tools/` 是分裂的：最早的三支是 `100755`，之後加的七支是 `100644`。
**十支全部都有 shebang，十支全部都是程式**，所以那個分裂不是任何人的決定 ——
是 `/mnt/c` 上 `core.fileMode=false`，git 記下 `git add` 當下拿到的 mode，
從此再也看不見它。

決定：**統一成 755，而且加一個守門的檢查。** 三個理由，第三個才是決定性的：

1. **755 是原意，644 是侵蝕。** 反方案（全部 644）要自洽的話得把十支的 shebang 都拿掉，
   而一個檔案自己寫著 `#!/usr/bin/env python3` 卻不可執行，是它自己跟自己矛盾。
2. 今天沒有代價（文件一律 `python3`／`bash` 呼叫），但 `DAY-ZERO` 第 6 項建 container
   之後就有：`Permission denied` 是一個要花半小時才會想到「是權限位元」的除錯。
3. 🔴 **這個退化是必然的。** 十支裡七支已經這樣退化過，而機制只要 repo 還在 `/mnt/c`
   就永遠存在。**只改不守，幾支新工具之後就長回來，而且沒有人會注意到** ——
   這正是「一條沒有儀器的規矩只是一個承諾」那句話，套在我自己身上。

`tools/test-file-modes.sh`：**讀 index，不讀工作目錄**，因為工作目錄正是 DrvFs 說謊的地方。
雙向檢查（有 shebang 必須 755、沒有 shebang 不准 755），
控制是一個 `core.fileMode=false` 的合成 repo，裡面各放一個方向的違規與各一個正確檔案，
掃描必須**恰好**報出那兩個。單向檢查會讓「每個檔案都 755」的 repo 過關。

第一次跑：控制立，真實 repo 報出正好那七支，而且**沒有任何非程式檔被誤標成 755**。
修完 11 支全部 `100755`。收工流程多一行，兩秒。

### 下一次上電要做的（不變）

`§C1`–`C4`、`§D`、`E11`、`§F`。`§D3` 和 `E11` 要人的手。
桌面側多兩條：`python3 tools/spec-check.py` 與 `bash tools/test-file-modes.sh`，
`CLAUDE.md` 已經寫上。

---

## 2026-08-24（第一段）— 修一張正要上機的 sheet，而「量不到」的那個數字換個檔位就量得到

桌面日。沒有通電。做的是：把 `RUNSHEET.md` 裡已經寫好、正要上機的那幾格
修對，補四格它缺的，寫一支計時器具，並把 R0 寫成 session `B3`。

### 先修 `PROGRESS.md` 自己

`§Now` 從首矽之前就沒有再動過。它寫「B1 和 B2……**both written and waiting
for the bench**」和「Last session：**desk only**」，而同一個檔案往下四十行的
Corrections 表寫著「First silicon. Section A and B of B1 and E1–E12 of B2 ran」。

查了三個 commit 對它的 diff：`b316f38` +6、`766e315` +2、`af290f1` +1，
**全部是往 Carried-forward 和 Corrections 兩張表新增列，`Now` 表格一格都沒動。**
`CLAUDE.md` 的「Before you stop: update `PROGRESS.md` § Now」在那三次都沒做。

**一個宣稱自己是「我在哪」唯一擁有者的檔案，和它自己的證據表矛盾。**

### 碼錶量不到那個數字 —— 而要修的是實驗，不是儀器

`§D1` 原本要求「掐 `J BFC00000` 到重置的秒數」，說那是 `C-8` 缺的那一格。
拿這個 repo 自己的數字算了一遍：

`J BFC00000` 寫 `WDTCNR = 0`，所以 `OVSEL[3:0]` = `0000`，也就是十檔裡**最短**的
2¹⁵ 個基底時脈 tick。基底是 `E2` 在裝置上量到的 199.48 MHz。

| | `OVSEL`=`0000`（`J` 選中的） | `OVSEL`=`1001`（最長） |
|---|---:|---:|
| 未除頻 | **164 µs** | 84.1 ms |
| 經 `CDBR` ÷14 | **2.30 ms** | 1.177 s |

人手碼錶的反應誤差約 ±200 ms，CP2102 的 latency timer（典型 1–16 ms，這台沒量過）
是另一層地板。**所以碼錶上出現的那個數字幾乎全部是重置之後的開機時間**，
把它記進 `C-8` 就是一次量測戴著另一次的名字。

但接下來這一步才是重點。`SPEC.md` 的 `CLK-08`（今天由另一個 session 寫的）
把這個結論寫成「**十個檔位全部低於儀器解析度**」。**那是把最短那檔的結論
套到了全部十檔上。** 1.177 秒不是任何儀器量不到的東西；84 毫秒也在 16 毫秒的
地板之上。兩者相差 14×，而那個 14 正好就是要判別的那個除數。

於是有了 `D4`：**手動 `EW B800311C 240000` 把 `OVSEL` 武裝到 `1001`，然後
`D4 − D1`。** `D1` 是它的控制 —— `D1` 的區間是開機時間加上一個 ≈0 的逾時，
所以相減之後開機時間對消，剩下的就是逾時本身。讀到 1.17 s 就是它數除頻後的
時脈，讀到 84 ms 就是未除頻的，**讀到其他任何一個 2 的冪次，就是 `OVSEL`
欄位的打包方式跟 datasheet Table 27 被讀出來的不一樣** —— 那個錯誤會現形成
一個錯的冪次，而不是一個錯的結論。

`240000` 的來歷：`OVSEL[1:0]` 在 bit 22:21，`OVSEL[3:2]` 在 bit 18:17，
`1001` 拆成 `1<<21 | 1<<18`。`WDTE` = `0x00` ≠ `0xA5`，所以看門狗啟動。
比 `D1` 多出來的風險是零：兩者都以一次看門狗重置收尾，而那正是兩者的目的。

### 掃 `WDTCNR` 的寫入者，結果比預期強

`D2` 原本只寫「bit 20 = 1」。想把它升級成整個字，需要先確認 loader 不會自己
去清那個 write-1-to-clear 的位元。掃出來的結果推翻了我自己的前提：

**loader 從來沒有寫過 `WDTCNR`，除了兩處，而兩處都是 `sw zero` 之後原地死迴圈**
—— `0x804012F8`（`reboot.......`，字串在 `0x8040A79C` 已核對）和 `0x804092E8`
（`J BFC00000` 的特例，`lui v0,0xbfc0` / `bne` 落在它前面）。兩處後面都是
`j` 到自己，delay slot 是 `nop`，**所以它們之後不會再執行任何東西。**

搜尋覆蓋，三種互補的方法：`0x311c` 立即值（2 筆，就是這兩處）；
`TC_BASE 0x3100` 加位移 28（唯一一個 `ori …,0x3100` 在 `0x80408F38`，
後面接的是造常數不是 store）；所有 base 不是 `sp` 的 `sw …,28(reg)`
（3 筆，分別落在 `0xBB804D00` 家族、SPI descriptor `0x8040FBD4`、`0xB8B20000`）。

第三種是補上來的：第一次我 `head -20` 就停了，而那 20 筆剛好全是 `28(sp)`，
**「追蹤停在第一個看似合理的邊界」這個這個 repo 已經記錄過一次的失敗模式，
今天又發生了一次**，只是這次在同一段裡就抓回來了。

**正控制打中了**：同一個方法找得到 `0x80408F34` 的 `CDBR = 0x000E0000`，
而那個值 `B7` 在裝置上量到過。找不到它的搜尋什麼都不能證明。

兩個後果。①**`B7` 量到的 `A5000000` 是硬體重置預設值**，不是 loader 停錶寫的
—— `B7` 的判讀語氣暗示了後者，改掉。②**`D2` 的路徑上沒有任何軟體**，它直接
讀硬體，所以它的兩個結果都乾淨：`A5100000` 代表 `WatchDogIND` 撐過了它自己
回報的那次重置；`A5000000` 代表撐不過，`C-8` 的鑑別器就死了。

而既然它可能死，就補了 `D2b`：**`DW 81000000 1` 讀 `C1` 在同一次上機稍早寫進去
的 `DEADBEEF CAFEBABE`。** SDRAM 內容撐得過暖重置、撐不過斷電，所以一個還在
那裡的 scratch word 不用讀任何狀態位元就說得出「這是暖的」。它自己的否證是
`D3`（按鈕冷開機之後同一個讀數必須變掉）。**兩個互相獨立的觀測，而這次上機
會告訴你哪一個有效。**

### `AUTOBURN 0` 從來沒有被證明過，而 R0 整個壓在它身上

`B6` 在裝置上量到 `AUTOBURN` = 1。它在整份 image 裡只被讀一次，`0x80401B9C`，
在上傳完成路徑上。**但沒有人打過 `AUTOBURN 0` 再把 `0x8040D4A0` 讀回來。**

翻上游 `console-dump.py` 的 `rescue` 才看到為什麼這不是形式主義：它**依序試
四種寫法** —— `AUTOBURN: 0`、`AUTOBURN 0`、`AUTOBURN=0`、`AUTOBURN:0` ——
因為 help 印的是 `AUTOBURN: 0/1` 而那不是語法，而且註解寫著「這是這顆 loader
的文件第三次跟它自己的 parser 不一致」。**打錯語法拿到的是 `Unknown command !`，
而在一個沒有回讀的流程裡，那看起來就像成功。**

新的 `C6`：送 `AUTOBURN 0`（走 `rescue`，它只吐得出 `0`），然後 `DW 8040D4A0 1`
期望 `00000000`。echo 是 loader 說它以為的事，回讀是燒錄路徑真正去看的那一格。
兩個來源。

順帶一件只有把 R0 排進同一次上機才會浮出來的事：**`D1`、`D3`、`D4` 各重置一次，
而重置把 `AUTOBURN` 打回 1。** 所以它要送兩次 —— `C6` 證明機制，`B3` 的 `G2`
在最後一次重置之後當實際的閘。兩件不同的事，兩格。

### `tools/console-capture.py`（+ 七個案例的自我測試）

唯讀開埠、每個 chunk 打時戳、`--send` 只送一行、然後轉唯讀。輸出**兩個檔**：
`.log` 是逐位元組的原件，`.timing` 是 `<offset> <秒>`。

**為什麼是兩個檔**：2026-08-23 抓到兩樣東西在改 bench 逐字紀錄
（`.gitattributes` 的 `text=auto`，和我自己習慣性的 `sed 's/\r$//'`）。
**把時戳交錯進 log 就是第三樣在改它的東西，而且這次是產生它的儀器自己。**

自我測試七個案例，五個是必須會失敗的控制。**第一次跑的時候有三個真的失敗了**，
而那三個各自是真的：
- `N4` 拿到的是 pyserial 的 traceback 而不是拒絕 —— **whitespace 檢查寫在
  開埠之後**。一個先碰了裝置才決定拒絕的工具，已經碰過那個它要拒絕的裝置了。
  檢查移到參數解析。
- `P1`/`P2` 在 29 個 byte 就截斷 —— `--idle 0.8` 短於被量的那個 1.50 秒靜默。
  **這不是 bug，這正是 `D1` 的形狀**（`D1` 量的東西*就是*一段靜默）。
  升級成第七個案例 `N5`，並在 docstring 裡寫明 `D1` 要用 `--seconds` 不能用
  `--idle`。
- 我用 Windows 的 python 寫檔，整份 shell script 變成 CRLF，在 WSL 下解析失敗。
  **正好是 `.gitattributes` 那條規則存在的理由，這次從反方向咬到我。**

### 環境，三件實測

| | |
|---|---|
| **`python3` 不是 `/usr/bin/python3`** | 這台的 `python3` 解析到 `~/.venvs/thermal/bin/python3`，**它沒有 `serial` 模組**；apt 的 `python3-serial` 裝在 `/usr/bin/python3` 底下。所以 `RUNSHEET.md` 白紙黑字寫的 `python3 upstream/tools/console-dump.py …` **在一個乾淨的登入 shell 裡會 `ModuleNotFoundError`**，跑不跑得起來取決於看不見的 shell 狀態。sheet 現在全部寫死 `/usr/bin/python3`，而且開電前的 `P0` 就在檢查它 |
| **distro 裡沒有 docker 也沒有 podman** | `/mnt/c/…/docker` 那個是 Docker Desktop 的 shim，`could not be found in this WSL 2 distro`。DAY-ZERO 第 6 項擋住 |
| **qemu 沒裝** | 而第 8 項的 DoD 一字不差寫著「qemu 下跑得出完整六段表格」。今天裝了，`qemu-system-mips` 8.2.2 |

順帶量到的兩件工具鏈事實：`mips-linux-gnu-gcc-12` (12.4.0) 的
`-march=mips1` 在測試樣本上**確實尊重 load delay slot**（`jr ra` 填在 slot 裡，
使用點在 slot+1），而且 **`movz`/`movn` 是 0 筆；同一段 C 用 `-march=mips32` 編
就出現 1 筆**。後面那條給了第 7 項的第四個檢查一個乾淨的判準：
`.o` 裡出現 `movz`/`movn` 就是旗標沒被遵守的陽性訊號。（一個樣本不是證明，
而那正是 `hazlint` 要拿去掃全體的理由。）

### image header 的欄位順序，我記錯了

要替 R0 算期望值，先把 flash `0x060000` 的 16 個 byte 拆開：

```
63 72 36 63 | 80 50 00 00 | 00 06 00 00 | 00 0f 10 02
   'cr6c'      startAddr      flashOff        len
```

**是 sig / startAddr / flashOffset / len**，不是我原先以為的
sig / len / startAddr / checksum。兩個 R0 需要的數字本來會從錯的字裡讀出來。
對得上的是 `B3` 在裝置上量到的 word 4 = `80500000`。

payload = dump `[0x060010, +0x0F1002)`，**987,138 bytes**，
`sha256 396561a0…45a03e90`，落在 `0x80500000`–`0x805F1002`。切出來放在
`$FWRE_WORK/rebuild/r0-vendor-kernel.bin`。

### session `B3` —— R0，八格

機制本身在**這台實體裝置上**已經做過一次：上游 `P9-12`，2026-08-21，
`J 80500000` 跳進一份裝置沒看過的 156-byte image，零 flash bytes。
新的是酬載：987,138 bytes 而不是 156，而且有真正的進入點。

設計上有兩件事值得寫下來：

**① `G1` 可能讓 R0 的一半免費。** `B4` 量到 `0x80500000` 已經有 flash `0x060010`
的前 16 個 byte（`C-16` 記著沒人解釋得了那是誰搬的）。如果 `G1` 讀到的中段和
尾端也對得上 dump，**那 964 KiB 整份已經在 RAM 裡，`J 80500000` 不用網路就
開得起來** —— 那是 `G6`，而它變成網路路徑要對照的**參考開機**。

**② `G6` 是 `G7` 的正控制，而那是整個設計。** `G7` 問的不是「有沒有 kernel
開起來」，是「網路路徑送到的是不是同一份 bytes」。有了二十分鐘前在同一塊板子上
產生的參考輸出，一個差異就是被抓到的傳輸錯誤。**沒有 `G6`，一次成功的開機
只證明了「某一份 image」開起來了。**

還有兩個控制互補：`G4` 上傳到 `0x81000000`（不是 `0x80500000`，因為那裡可能
本來就有正確的 bytes，於是「上傳到了」和「本來就在」是同一個讀數），
`get` 回來 `cmp`；但 `put` 和 `get` 共用 `0x8040D3A8`，**所以往返證不了載入
位址對不對**，那由 `G5` 的三點下毒＋回讀來補。

進站前先把上游 `P9-12` 的第四種結果寫進 sheet：它進站前寫了三格判讀表
（橫幅重複／只有跳轉行／什麼都沒有），**而實際發生的是第四格**——橫幅出現、
每一輪在同一個字元被切斷。

### 兩個 session 同時在改這個 repo

做到一半發現 `SPEC.md`（55 KB）、`CLAUDE.md`、`PROGRESS.md` 在我這一段工作期間
被動過，而那不是我。對方在寫一份「這個專案握有的每一個數字」的索引表，
並且往 `CLAUDE.md` 加了一條房規：**產生、改變或否證了一個數字，`SPEC.md`
要在同一個 commit 裡改。**

它在讀我的 `RUNSHEET` 改動並整合（`CLK-08`、`CLK-10`、`MEM-10` 三列都是），
所以不是衝突而是協作。但**兩個 agent 同時寫同一個檔案是會互相覆蓋的**，
今天沒撞到是運氣。記在這裡，讓下一次不要靠運氣。

### 下一步

`hazlint`（DAY-ZERO 第 7 項），範圍照上游 `P9-12` 的驗屍報告重寫：
掃**二進位**裡「load 之後緊接著讀被載入暫存器」，正控制報 stage2 的
**1,474 / 646 / 0**（掃了幾個 load、幾個後面接 `nop`、幾個違規 ——
沒在看的工具會報 0 個 load，不是 0 個違規），負控制用上游那個真的在這顆
矽片上壞掉過的 156-byte payload。

---

## 2026-08-24（第二段）— `hazlint`：驗收條件三個全中，而寫它的過程翻掉三件寫在計畫裡的事

桌面日，未接觸裝置。`DAY-ZERO` 第 7 項關閉。

### 三個驗收條件

| | 期望 | 實得 |
|---|---|---|
| 正控制 | `stage2.bin` → `1474 / 646 / 0` | `1474 / 646 / 0`（43.83%），exit 0 |
| 負控制 | 上游壞掉的 `P9-12` payload → 至少 1 筆違規並指出 offset | **2 筆**，offset `0x1c` 與 `0x2c`，exit 1 |
| 母體計數被拿掉 | 整支拒絕輸出 | 三種拿法（期望值改錯、fixture 構不到、操作者明說豁免）**一律 exit 2** |

`tools/hazlint` 八個內建控制，`tools/test-hazlint.sh` 42 個案例、0 skip，
其中九個**把工具本身改壞再要求它自己叫**。

### 定義是逆推出來的，而逆推的過程本身是一個結果

上游記的是「1,474 個**有目的暫存器的** load」。照字面掃全檔得 1,475，差一筆。
差的那一筆是 `0x8040AB14` 的 `c0a80001`，解成 `ll` —— 而那是 `192.168.0.1`，
`docs/loader-command-semantics.md` §9 早就把它點名成資料。

所以「load」的定義敲成 **MIPS-I 寫進通用暫存器的 load（`lb lbu lh lhu lw lwl lwr`），
且 `rt != $zero`**。`ll` 是 MIPS-II，這顆是 MIPS-I 系，它**因為 ISA 的理由**落在
定義外，不是為了讓數字對而被減掉。同樣落在外面的 `0x8040D760` 那個 `lwr` 的
`rt` 是 `$zero`，寫不進任何地方，也就沒有 load-use hazard 可言。
**兩個排除各自都有第二來源說它是資料。**

拿掉 `rt != $zero` 這條規則，母體會跳到 **1,665** —— 那 191 筆全是字串表裡
`lb zero,…` 之類的東西。`test-hazlint.sh` `M3` 就是這條，它證明母體控制真的
在保護一個東西。

### 🔴 一、負控制的檔案，計畫指錯了，而指錯的方向剛好讓控制不會叫

`plan/DAY-ZERO.md` 寫「上游那份壞掉的 **156-byte** payload」。

- `w08-ramboot-v1-truncating.bin` = **148 B** = **壞的那份**
- `w08-ramboot.bin` = **156 B** = **修好的那份**

148 + 8 = 156，那八個 byte 就是補上去的兩個 `nop`（在 `0x20` 與 `0x34`，
上游 `BENCH-LOG.md` `T-90` 自己寫的位置）。上游 `PROGRESS.md` 那句
"a 156-byte image" 講的是**複驗**那一次，不是失敗那一次。

**照字面拿 156-byte 那份當負控制，`hazlint` 會回報 0 筆違規 ——
而一個永遠不會叫的負控制，看起來跟一個通過的負控制完全一樣。**
這正是這個專案反覆在抓的那個病，只是這次它藏在一句「156」裡。

兩份都留下，而且變強了：148 那份是負控制，156 那份升級成**差分正控制**，
同一支程式、只差兩個 `nop`（外加四個因此位移的分支偏移，工具會逐字驗這件事），
2 筆違規 → 0 筆。

**順帶**：驗屍文只點名 `andi t2,t2,0x60` 那一筆。**壞的 payload 裡有兩筆** ——
`0x1c` 的 `lbu a0,0(s1)` 後面接 `beqz a0`，同一種錯，沒被寫下來。修法把兩個
都補了，文字只記了一個。**修對了但沒記全，下一份 payload 會踩另一個。**

### 🔴 二、`rlxprobe` 的建置行，在這台機器上不會編譯

```
cc1: error: ‘-march=mips1’ requires ‘-mfp32’
```

`mips-linux-gnu-gcc-12` (12.4.0, Ubuntu 24.04)。`-march=r3000` 同病。
第 6 項與第 8 項記的 `-march=mips1 -mabi=32 -nostdlib -ffreestanding -fno-pic`
**照抄就是一個編譯錯誤**。加 `-msoft-float` 就過，而且對一顆沒有 FPU 的核心，
那比 `-mfp32` 誠實。

**而發現它的方式值得記**：`E2` 那個案例原本寫成「`-march=mips1` 編出來的
`movz`/`movn` 應該是 0」，第一次跑就過了 —— 因為 `.o` 根本沒產生，
`grep -c` 對一個空輸出回報 0。**一個 0，來自一個沒有跑起來的編譯，
跟來自一個跑起來的編譯長得一模一樣。** 案例現在先確認 `.o` 存在才相信它的計數。
這是同一天之內，同一個病的第三個實例。

加上旗標之後，計畫記的那筆量測重現了：`mips1` → 0 筆 `movz`/`movn`，
`mips32` → 1 筆，兩個 `.o` 的 load-use 違規都是 0。

### 🔴 三、第四個檢查的 rodata 那一半：`28 筆` 拿不回來

同一段 `[0x8040A000, 0x8040DD10)`，三支解碼器三個答案：

| 判準 | 命中 |
|---|---:|
| `hazlint --isa --loose`（只看 opcode/funct） | **445** |
| `hazlint --isa`（嚴格：編碼固定為零的欄位必須真的是零） | **236** |
| `objdump -m mips:3000` 的 `.word` | **829** |

沒有一支是 28，而且從 §9 記下來的東西也拼不出 28：那一列點名 `0x0000004b` 是
`movn`（**寬鬆**判準才接受，嚴格判準看 `sa=1` 就拒），又點名 `'pload, F'` 是
`clo`（`SPECIAL2`）。**當時用的觀察名單夠窄才會得到 28，而那份名單沒有被寫下來。**

**28 撤掉當控制、留著當紀錄。** 換上去的不是另一個數字，是那一列本來想測的
**性質**，寫成會失敗的形式：寬鬆判準必須在 `0x8040AB14` 找到 `ll`，
必須抓到六筆 `0x20` 間距的 `0x0000004b`；嚴格判準必須把那六筆拒掉；
而且**每一次執行都把兩個判準的數字並排印出來**。

> **一個沒有指名判準的計數不是量測。** 這跟上游 runbook §8.12.46 那張手抄表是
> 同一種錯：一組正確的值配一句沒說清楚它從哪來的話，讀起來跟兩個都對一樣。

程式區那一半**完全重現**，而且升到三個來源：18 筆、`movz`×12、`movn`×6，
十八個位址一個不差，寬鬆與嚴格判準都一樣。`objdump -m mips:3000` 也在這十八個
位址各印一個 `.word` —— **外加四個**，`0x80400C40`/`0x44`/`0x68`/`0x7C`，
`rs = 3` 的 `COP0` 字，既不是 `mfc0` 也不是 `mtc0`，手上沒有任何來源給它名字
（多半就是 `notes/cache-model.md` 講的那顆 Lexra CP0）。記下來，是因為
**一個把它們印出來的解碼器和一個不印的解碼器，都被叫做「18」**。

### 兩個沒人要的發現，來自 `--survey`

| 形狀 | 數量 | 頭幾個位址 |
|---|---:|---|
| `mult`/`div` 後面緊接 `mfhi`/`mflo` | **16** | `0x80403C14`、`0x80404248`、`0x804042A0` |
| `mtc0` 後面緊接 `mfc0` | **3** | `0x80400408`、`0x8040041C`、`0x80400660` |
| load 坐在任何分支／跳躍的 delay slot 裡 | **0** | — |

第一個 `mtc0` 那筆是 `mtc0 zero,c0_status` 之後**下一個字**就 `mfc0 t1,c0_status`
—— 同一顆暫存器，中間什麼都沒有。原廠編譯器在這十九處**一個 `nop` 都沒補**。
這與「`HI`/`LO` 與 CP0 有互鎖、只有 load delay slot 外露」相容，
**也與「十九個潛伏的 bug」相容。數得出來不等於判得出來** —— `C-9` 開著，
R1b 的實驗是裸機上 `mult`→`mflo` 與 `mtc0`→`mfc0` 各補 0/1/2 個 `nop`。

第三列則是主檢查能用線性掃描的**前提**：一個 load 都不在 delay slot 裡，
所以「下一個字」和「下一個被執行的指令」在這份檔案裡處處相同。
（工具還是把 delay slot 的情形實作了，包含條件分支的兩條腿都檢查、
`jr`/`jalr` 判 `unresolved` 而不是硬拿下一個字 —— 因為 `rlxprobe` 是手寫組語。）

### 還沒做的那一半

**第二層。** `P9-12` 的結論是「第一層讓今天過關，第二層讓明天的 payload 不會
再這樣過關」。今天交的是第一層。第二層是 `rlxprobe` 的建置把 `hazlint` 當
**gate**（exit != 0 就停），而那是第 8 項**開工的第一件事，不是最後一件**。
exit code 已經按 gate 設計好：0 乾淨、1 有違規、2 拒絕認證、3 用法錯。

### 下一步

`DAY-ZERO` 第 8 項 `rlxprobe`，裸機六段，`R1d` 擋著其他所有段。

---

## 2026-08-24（第三段）— seating 2 上機第一段：六格全中，而三個計畫外的發現都是量測系統自己壞掉

**一次電源循環，零 flash 位元組，約二十分鐘。** `bench/2026-08-24/`。

### 這一場怎麼跑的，以及為什麼不是照 sheet 寫的跑

sheet 說 `§A` 用 `console-dump.py catch`、`§C` 用 picocom 手打。**兩個都換掉了。**

`console-dump.py catch` 只印 banner 那一行，把開機前到 prompt 之間的串流丟掉 ——
`bench/README.md` 早就把 `A2` 記成「被它自己的儀器判定不可能滿足」。
`tools/console-capture.py` 的 `--esc N` 是**在擷取迴圈裡面**送 ESC 的，所以它一邊送一邊逐位元組收。
**`A2` 因此不是換一格，是換一支儀器。**

picocom 換成同一支工具，**每格一個 byte-exact + 時間戳的檔**，不用手抄。
它沒有 `console-dump.py` 那張 `FORBIDDEN` 清單 —— 那張清單屬於一支被釘在 `4d3ff26` 唯讀的工具，
而 `D1` 本來就用 `console-capture.py` 送 `J BFC00000`。

### 六格

| 格 | 讀到 | 判定 |
|---|---|---|
| `§A` | banner 與 2026-08-17/18 逐行相同，`chipName: UNKNOWN`、`ramSize: 32M`、`400MHz`、`P0phymode=01` | ✅ **`A2` 關閉**，1,306 bytes。**沒有 `---Escape booting by user`**，與 `C-13` 一致 |
| `A0` 🆕 | 第一次 `Unknown command !`；第二次 `8040DBC0: 8040B070 00000000 80409A9C 8040B074` | ✅ 三件事：**重開 port 不重置板子**（`BRD-09` 推測→量測）、prompt 活著、`B1` 在第二次上電重現 |
| `C1` | 只有回音 | ✅ `EW` 靜默，多值形式 |
| `C2` | `81000000: DEADBEEF CAFEBABE …` | ✅ 依序落位。R4 的 cmdline buffer 計畫從推測變量測 |
| `C3` | `81000100: 00000400 **11111111** …` | 🔴 ✅ **`EW` 對未對齊位址靜默地往上進位**（`…102` → `…104`） |
| `C4` | `81000200: 41 42 43 00  ABC.` | ✅ **`EB` 位址照字面**。同一顆 loader，兩個寫入原語**相反**的位址處理 |
| `C6` | `AUTOBURN: 0` → `Unknown command !`；`AUTOBURN 0` → `AutoBurning=0`；`8040D4A0: 00000000` | 🔴 ✅ **關閉，兩個獨立來源。R0 與一次 flash 寫入之間唯一的那道門，證明會動** |

### 🔴 一、行緩衝區 128 bytes，而它在 `C7` 跑之前把 `C7` 改掉了

`§A` 的 ESC 串流打在 prompt 上，loader **每收滿剛好 128 個 ESC 就回一次 `Unknown command !`，七次都是同一個數字**。
每秒約 50 個 ESC，時序假象不會七次落在同一個數。

讀出來的第二來源：命令迴圈 `0x80409190` 的 `memset(buf,0,128)`、`0x804091A0` 的 `readline(buf,128,1)`。

**而 `readline`（`0x8040708C`）三個出口只有 CR 那條寫 NUL**（`0x804070FC`，在延遲槽裡）；
LF 那條與長度到底那條（`0x80407194`，`count < 128`）都不寫。
呼叫端的 `memset` 只救得了**短於** 128 的行 —— 那才留得下零。

> **剛好 128 個字元的行是唯一一個「文字佔滿全部、又沒人寫終止符」的長度**，
> 斷詞器（`0x80407248`）於是掃過 `sp+143`，進到 8 bytes 堆疊空隙，再進到存起來的 `s0`（`sp+152`）。

`C7` 原本送 **18 個值 = 173 個字元**。`EW 81000400 ` + 12 個完整值 + 第 13 個的 8 個 hex **剛好是 128** ——
**原本那一格會被切在正好那個位置，而命令是 `EW`。** 改成 12 個值 / 119 字元，
並且加一條「**任何命令列都不得剛好 128 個字元**」。

而 `C7` 本來要問的問題順帶答完了：**一行載 12 個字 / 48 bytes**，
1 KiB 的裸機探針要 **22 行不是 15 行**，R1 的無網路路徑貴了 47%。

### 🔴 二、`A0` 第一次失敗，而失敗那次比成功那次有用

`Unknown command !` 的成因是 `§A` 的擷取被 `--seconds` 切在半途，**12 個 ESC 還留在行緩衝區**，
這一格的命令接在它們後面。

**而 `SPEC.md` `LDR-16` 早就寫著這件事**：「排隊的 ESC 會毒到下一條命令；先送一個裸 CR」。
上游量過，這裡也記著。

> **規則在表裡，不在程序裡，所以它被重新發現而不是被遵守。**
> 這不是新發現，是一個**已知事實沒有被搬進會被照著做的那份文件**。
> 規則現在寫進 `RUNSHEET.md` seating 2 的執行程序。

（我在當下把它講成了新發現，那是錯的，`LDR-16` 已經記了兩個來源。更正記在這裡。）

### 🔴 三、`§D` 今天不做，而攔住它的是儀器不是時間

`D1` 送 `J BFC00000` → 看門狗重置 → 重開機；`D2`/`D2b` 必須讀**那次暖重置之後的 loader prompt**。
所以同一次擷取要「送命令 → 錄重開機 → 在重開機的 ESC 視窗裡送 ESC」。

**`console-capture.py` 的 `--esc` 迴圈在 `capture()` 裡位於 `ser.write(line)` 之上**，做不到。
硬跑 `D1` 會直接開進廠商 kernel，救回來要一次電源循環，
**而那正好毀掉 `D2b` 要驗的暖重置條件**。

**這是第三格輸在一支做不到那件事的儀器上（`A2`、`E5`），也是第一格在跑之前就被攔下來的。**
修法是 `--esc-after`，在桌面上做、補上控制項；在板子旁邊臨時改量測工具、不重跑它的控制，這個專案不做。

### 這一場的形狀

**四個計畫外的發現，三個是「量測系統的行為」而不是「晶片的行為」。**
今天真正在測的是儀器與程序本身，而它壞了三次、三次都被抓到，其中一次在造成損害之前。

零 flash 位元組。RAM 只碰 `0x81000000`/`0x81000100`/`0x81000200` 三個 scratch 位址。

### 下一場從哪裡開始

`C7`（改寫版）→ `E11`（要動網路線）→ `§F`（`F1` 是會終結整場的風險格）→ `§D`（等 `--esc-after`）→ **`B3`（R0，關現行 gate）**。
`§D` 之前要重跑 `C1` 把 `D2b` 的彈藥裝回去 —— 關機會丟掉那個字。

---

## 2026-08-24（第四段）— 三支工具，而最難看的發現是我跟操作者說過「這個控制項是關鍵」的那一個

桌面，上機之後。

### `hazlint` 1.0 的對抗性審查：24 個宣稱，17 個成立

四個獨立視角（解碼器、盲點、控制項、數字），每一個宣稱交給另一個 agent、任務是**推翻它**。

**🔴 第一名，而它打到我自己講過的話。**

我跟操作者說過：「**母體控制才是讓 0 有意義的東西**」。

`K4` 用 `raw_words()` 自己組字，而使用者給的每一個檔案走 `elf_ranges()` + `words_from()`。
**母體控制驗證的是一條被掃描的檔案永遠不會走的程式路徑。**
下面那一整組 span 缺陷，它一個都抓不到 —— 它每次都印出漂亮的 `1474 / 646 / 0`，
而那條路上根本沒有它們。**一個看起來在守東西、實際上沒有的控制項**，
正是這支工具被寫出來要抓的那一類錯。現在 `K4` 走 `raw_span()`，和 `--raw` 同一條路。

**第二名，而它是個雙重失效。**

`lwl`/`lwr` 配對豁免用 `continue` 跳過整個後繼指令，而不是只跳過 `rt` 的合併，
所以它連後繼指令的 **base 暫存器**一起豁免掉了：
`lwl t0,0(t1)` 接 `lwr t0,3(t0)` 拿剛載入的 `t0` 當位址，是真 hazard，exit 0。

而且 —— `reads()` 對 `lwl`/`lwr` 只回 `{rs}`，**從來沒把合併讀進來**，
所以那個豁免要壓抑的東西根本不可能出現。窮舉 63,488 種編碼，它壓抑了 1,984 個，
**每一個都是真陽性**。兩半一起修：`reads()` 補上 `rt`，豁免補上 `rs_of(w2) != rt`。

**其餘十五條，分四組：**

| 組 | 內容 |
|---|---|
| span（6） | `.o` 的每個 section `sh_addr` 都是 0 → 位址碰撞、分支目標解析到別的 section；攤平的 word 列表讓**上一個 span 的最後一個字變成下一個 span 第一個字的前導指令**；超出 EOF 的 span 被安靜縮短；未重定位的 `j`/`jal` 解析到位址 0 而不是回報 unresolved |
| 覆蓋（2） | `sh_offset` 超過 EOF 的可執行 section **從掃描和報告裡一起消失**；只掃 `PF_X`，而一個很小的可執行段就能滿足 `loads > 0` 那道保險 |
| 解碼器（3） | 四個 REGIMM branch-likely、三個協同處理器分支**根本沒被認出是分支**；`reads()` 的 `lwl`/`lwr` |
| 控制項（4） | 上面每一條**都沒有任何控制項擋得住** —— 打過補丁的工具和出貨的工具，對舊的 K1–K6 完全無法區分 |

### 修法不是逐條打補丁

根因是 `scan()` 拿到攤平的 word 列表。現在它拿 **`Span` 的列表**，而且：

- 「上一個字」「下一個字」**只在同一個 span 內成立**；
- `sh_addr == 0` 的 section 用合成位址（`0xFF000000` 起），**報告明說位址是合成的**，
  而任何從它算出來的**絕對**目標一律 `unresolved`（PC 相對位移不受影響，因為整段一起搬）；
- `sh_offset`/`sh_size` 超出 EOF → **報錯，不是安靜縮短**；
- 報告列出**每一個沒被掃到的 alloc 段**，每次執行都印。

**`1474 / 646 / 0` 全程沒有變。**

### 一個設計判斷：`unresolved` 和 `note` 是兩種宣稱

改完之後 `.o` 的第一個字如果是 load，`head_unknown` 會叫，於是**每一個第一條指令是 load 的 `.o` 都會 exit 1**。

想清楚之後，那是兩件不同的事：

- **`unresolved`** ＝ 後繼指令**不知道是哪一個**。沒檢查到的後繼就是沒檢查到的 load → exit 1。
- **`note`** ＝ 後繼指令**知道也檢查了**，不能排除的是**還有第二個**（連結器可能在這個 span 前面擺一個分支）。

**這不是把不方便的結果降級** —— 兩者宣稱的東西不一樣。而它的代價要明講：
**gate 要指著連結後的映像，不是 `.o`**。`rlxprobe` 的 Makefile 本來就是。

### 控制項：42 → 56

每一條修法配一個會失敗的變異：`M7`（豁免吞掉 base）、`M8`（忘掉 REGIMM branch-likely）、
`M9`（忘掉 `lwl`/`lwr` 的合併讀），三個都必須讓 `--self-test` 拒絕輸出。
外加 `U1`（最後一個字是 load → exit 1，第 14 條說這個契約零覆蓋）與
`U2`（真的組出兩個可執行 section 的 `.o`，不得跨接縫誤報，接縫要被講出來，位址要標成合成的）。

`M9` 第一版沒有隔離出它要測的東西 —— 它用的案例靠 base 暫存器就會叫，
把 `rt` 拿掉照樣是違規。換成 `lw t0` 接 `lwr t0,3(t2)`：base 無關，
**唯一讓它成為 hazard 的理由就是 `lwr` 讀 `rt` 來合併**。

### 另外兩支

**`tools/rlxprobe/` 第 0 段**（23 個案例）。`probe0.bin` 相依於 `probe0.gate`，
而 `probe0.gate` 不存在除非 `hazlint` exit 0；`G3` 把 `HAZLINT` 指到不存在的路徑，
要求建置**壞掉**而不是繼續。putchar 照 loader 自己的抄，**含那個 `nop`**，`A1` 守著它。
量到的：264 個 word **0 條非 MIPS-I 指令**（兩種判準），`--survey` 三種未定 hazard 形狀**全 0**。

**`console-capture.py --esc-after`**（7 → 10）。`--esc` 在 `--send` 之前跑，
`D1` 要的是相反的順序。`P3` 驗它在命令之後真的寫出 ESC 且期間到達的回覆仍然進 log，
`N6` 驗 `--esc-after 0` 時**一個 ESC 都不寫** —— 否則 `P3` 在一支無條件送 ESC 的工具上照樣會過。
**`§D` 解鎖了。**

### 下一步

`RUNSHEET.md` seating 2 第二段：`C7`（改寫版）→ `E11` → `§F` → `§D` → **`B3`（關現行 gate）**。
`§D` 之前先重跑 `C1`。
