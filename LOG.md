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
