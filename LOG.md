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

---

## 2026-08-24（第五段）— seating 2 上機第二段：基準時脈 200.0049 MHz ±7 ppm，而 `0x81000000` 從來不是 scratch

**一次電源循環（`A-catch` 03:32:42 開，`CONT3` 04:53:45 落在同一次開機上），
零 flash 位元組，33 個擷取。** `bench/2026-08-24b/`，30 格加三個 flush，
每格一個 byte-exact + 時間戳的檔，全程沒有一行是手抄的。
`§F`（`F1`、`F2`）、`§D`（`D1`、`D1b`、`D2`、`D2b`、`D4`）與 `B3` 沒跑到。

### 這一場中途換了駕駛，而換掉的東西是一條 house rule 的執行者

前半場是操作者逐格轉述，後半場 console 直接交給我開。
**`RUNSHEET.md` house rule 2（「期望值寫在後面的格子只能舉例，不能否證」）
在前半場是免費被強制執行的** —— 期望值寫在一則已經送出去的訊息裡，改不掉。
直接開始之後，它一個執行者都沒有：寫在讀數後面的預測，跟寫在前面的長得一模一樣。

`bench/2026-08-24b/PREDICTIONS-block{1,2,3,3b}.md` 加 `tools/check-predictions.py`
是補回來的那個執行者。判準是 `mtime(預測檔) < mtime(它點名的每一個擷取)`，
四個控制、其中三個必須失敗（`P1` 先預測後擷取要過、`N1` 反過來要被抓、
`N2` 點名了卻沒有擷取要被抓、`N3` 空的 `cells` 區塊要拒絕出報告而不是回報乾淨），
任一個不照做就拒絕對檔案下判斷。四個 block 全部通過，邊際 **+8.2 s … +650.4 s**。

**它證不到的東西寫在它自己的 docstring 裡**：mtime 不是密碼學時戳，`touch -d` 改得掉。
它對一個合作的稽核者證明順序，對一個願意偽造的人證明不了任何事。
代價也要講：**一個 block 跑完之後就不准再動那個預測檔**，改一個錯字都會讓檢查失敗 ——
而那正是正確行為。

### 🔴 一、基準時脈重新量到 ±7 ppm，而 seating 1 那 0.26 % 是碼錶不是板子

**量到的**，四次 `DW 8040DCE8 1`（word 1 = tick 計數器），間隔取自 `.log` 的 mtime：

| 格 | tick | mtime |
|---|---:|---|
| `E1b` | 252,061 | 04:14:52.116 |
| `E2b` | 277,390 | 04:19:05.387 |
| `CONT2` | 428,675 | 04:44:18.209 |
| `CONT3` | 485,370 | 04:53:45.148 |

| 配對 | 秒 | f (Hz) | base (MHz) | ppm |
|---|---:|---:|---:|---:|
| `E1b`→`E2b` | 253.270 | 100.0078 | 200.0168 | +84.1 |
| `E1b`→`CONT2` | 1766.093 | 100.0027 | 200.0066 | +32.9 |
| `E1b`→`CONT3` | 2333.032 | 100.0025 | 200.0062 | +30.8 |
| **`E2b`→`CONT2`** | 1512.822 | **100.0018** | **200.0049** | **+24.3** |
| **`E2b`→`CONT3`** | 2079.762 | **100.0018** | **200.0049** | **+24.3** |
| **`CONT2`→`CONT3`** | 566.940 | **100.0018** | **200.0049** | **+24.4** |

**三條長基線在五位有效數字上一致，而殘差只有一個名字**：
`E1b` 的 mtime 相對它那次 tick 取樣偏了約 **15 ms**，那是 CP2102 latency timer 的尺度
（1–16 ms），它在短基線上佔主導 —— 253 秒那條讀成 +84 ppm 就是這麼來的。

> **Timer base clock = 200.0049 MHz，±0.0015 MHz（2080 秒基線上 ±7 ppm）。**
> 編進 loader 的 `0x0BEBC200` = 200,000,000 **只差 +24 ppm**，在一般晶振的公差裡面。

base = `f × CDBR(14) × TC0DATA(142,858)`，後兩項都是 seating 1 在裝置上量到的
（`B7`、`E2b`）。三項裡三項量到，這是推導不是猜。

🔴 **`CLK-02` 的 199.48 MHz 與 `CLK-04` 的 99.74 Hz 就此被取代，而它們留在原處。**
seating 1 那次是**手計時 61.842 秒**；人讀碼錶約 ±0.15 s，**那就是 ±0.25 %** ——
跟當時被寫成板子性質的那個偏差同一個量級。**那 0.26 % 是儀器。**

三件順手拿到的：

- 🆕 **量到的：tick 計數器開機時從 ~0 起算。** 零點 **03:32:51.54**（由 `CONT3` 與
  `f = 100.0018` 外推）。第一個 UART byte 在 03:32:50.13，所以
  **`timer_init` 落在開機後 1.41 s** —— banner（+0.585 s）之後、乙太／PHY init（+2.246 s）之前。
  兩條互不相干的推導（單點除以經過時間、差分）一致。
- 🆕 **tick 計數器是一個帶預測值的「同一次開機嗎」證人**，一次讀 71 bytes，
  而且**完全不依賴 DRAM 保留**（`D2b` 依賴）。第八節那次 console 斷線就是它結掉的。
- `§F` 要的 timer gate 在這次開機上重新建立（`E1b`/`E2b`）：**不前進就一個 PHY 命令都不准送**，
  否則板子會卡在 `delay()` 裡而不是卡在 MDIO 輪詢裡。

### 🔴 二、`0x81000000` 不是 scratch —— 一張 32-byte 週期的活描述子表

**量到的**，`C7-pre`（`DW 81000400 28`，354 bytes，七行，stride `0x10`），
**寫任何東西進去之前**讀的：

```
81000400:	00000400	00000001	FFFFFFFF	00000000
81000410:	00000000	00000000	81000418	81000418
81000420:	00000400	00000001	FFFFFFFF	00000000
…
```

一個**完整的 32-byte 週期**，而最後八個 byte 是一條**就地初始化的空環狀串列**：
`0x81000418` 那個字是 `0x81000418`，`0x8100041C` 也是 —— `next = prev = &next`，
`INIT_LIST_HEAD` 的形狀。

**兩個理由說它不是雜訊**：未初始化的 DRAM 生不出**自己的位址**；
而且它生出來的位址跟 `DW` 印出來的位址一致，所以位址解碼也是對的。**有東西寫了它。**
*推測的*：1 KiB 緩衝描述子陣列加一條 free list，多半是 loader 的網路緩衝池
（開機印 `---Ethernet init Okay!`，`0x400` 是合理的封包緩衝大小）。否證路徑是讀那段初始化程式，桌面工作。

**它反過來讓 part one 三格變硬**：`C2` 在 `+0x08`/`+0x0C` 的 `FFFFFFFF 00000000`、
`C3b` 在 `0x81000100`（`0x20` 對齊）的 `00000400`，都是**這張表沒被動過的那一份**，
不是「沒預測到的 SDRAM」。尤其 **`C3`「`EW` 把未對齊位址往上進位」變得更難反駁** ——
`0x81000104` 的既有值現在已知是 `00000001`，所以 `11111111` 出現在那裡、
而 `0x81000100` 還讀到 `00000400`，證明那次寫入**沒有**落在 `…100`。
`C4b` 尾巴那個 `00` 是 `00000400` 的第四個 byte，`EB` 沒碰到。三格一個圖樣，全部相容。

🔴 **同時它否證 `RUNSHEET.md` `§C` 的前提。** 那句話說 `0x81000000` 是 scratch，
理由是「遠高於 loader 的映像、遠高於暫存的 kernel」—— **一個排除了兩個已知物、
而完全沒有排除 loader 在執行期配置的任何東西的論證。**
part one 寫在一個活結構上而沒有壞掉，**那是運氣，不是設計。**

`C7-pre2`（`DW 81800000 8`）給第二個：`+0x08` = `0x58`、`+0x0C` = `0x81800058`
= **base + `+0x08` 的值**，一個長度加一個指向 base+長度的指標；`0x81C09988` 指到 **28.04 MiB**。
所以 `0x81000000`–`0x81C09988` 至少有兩個互相指來指去的活結構。**這不是填充圖樣。**

**因此 `§G` 換位址，而換法是探測不是論證。** `G4-addr-probe`（`DW 80A00000 8`）
讀到 `55617135 0077BF55 …`：**沒有指標形狀的字、沒有自我參照、沒有週期**，
來源未定（未初始化 DRAM 或記憶體測試填充），而**兩種來源都沒有東西指進去**。
`0x80A00000`–`0x80AF1002` 在暫存 kernel 尾端（`0x805F1002`）之上、16 MiB 那些結構之下。
新格 `G0` 的否證條件寫在它自己那一行：**頭、中、尾三讀，任何一個指標形狀的字就換位址** ——
八個字是一個 32-byte 視窗，它替 964 KiB 講不了話。
（`G4` 照原樣上傳會**用一次 TFTP 傳輸蓋掉那次 TFTP 傳輸自己的緩衝**，*推測的*，
而那種東西壞起來的樣子叫「板子故障」。）

### 🔴 三、`C7`：懸崖在 128、一行載十二個字，而 sheet 給的讀回長度會製造一個假截斷

**讀出來的 + 量到的**：`DW <addr> N` 印 **`4 × ceil(N/4)` 個字，不是 `N` 個** ——
`i` 從 0 每次加 4、只要 `i < N` 就整行印四個。`docs/loader-command-semantics.md:555`
早就寫著「數的是字，四個一行」，`B9` 也量過 `DW 8040DBC0 10` → **三行**。

🔴 **而 `RUNSHEET.md` `C7` 要的是 `DW 81000400 3` 去讀回十二個寫進去的值。
那只印一行四個。** `C7` 的失敗模式是**截斷**，所以四個字的讀回
**看起來就跟「在第四個值上被截斷」一模一樣 —— 這一格要抓的失敗模式，被這一格自己製造出來。**
在桌面改成 `28`（`C7-pre`）、`16`（`C7a-rb`）、`16`（`C7b-rb`）之後才打字。
**進位是往上的，所以長度給太小不會自己叫。**

| | 行 | 字元 | 量到的 |
|---|---|---:|---|
| `C7a` | `EW 81000400` + 12 個值 | **119** | 130-byte log，只有回音、無 `Unknown command !`；十二個**依序**落位；`0x81000430` 的四字溢出控制未變 |
| `C7b` | `EW 81000440` + 11 個值，以前導零補齊 | **127** | 138-byte log；十一個全落位；第 12 個字（`0x8100046C`）仍是 `00000000` |

- 🔴 **懸崖在 128，127 是安全的。** 兩行都完整回來。這是 `_check_send` 現在用 `>=` 守的邊界。
- 🔴 **`EW` 寫的正好是 `argc − 1` 個字，不是「至少」。** 兩個溢出控制都與前狀態逐位元組相同。
- 🔴 **`C7b` 的溢出控制是從模型預測出來的，而那個位址從來沒被讀過。**
  `C7-pre` 停在 `0x8100046F`；32-byte 週期預測 `0x81000470` =
  `00000000 00000000 81000478 81000478`，回來的就是這個。
  那張週期表因此從「七行裡看到的圖樣」升成「做過樣本外預測而沒有被否證的模型」。
- 🔴 **這一格自己的問題在矽片上答完：一行命令載十二個 32-bit 字 = 48 bytes。**
  所以 1 KiB 的裸機探針要 `ceil(1024/48)` = **22 行不是 sheet 假設的 15 行 —— R1 的無網路路徑貴 47 %。**
- 🆕 **量到的：loader 的十六進位解析是 `strtoul` 式的，不是定寬。**
  `00C7B00001`（十個字元）讀回來是 **`C7B00001`**：前導零忽略、不截成八位、不溢位。
  **這個 repo 沒有任何一份來源預測過它**；補零之所以被選成 `C7b` 的補齊法，
  正是因為答錯的話落地的是一個**已知位址上的錯值**，而不是一個**不知道在哪的錯位址**。

🆕 **量到的：`DW <addr> 1` 的回覆在這顆 loader 上是一個 71 bytes 的結構常數**，而通式是

```
bytes = len(command) + 2      （回音與它的 \n\r）
      + 47 × 行數             （9 個 "AAAAAAAA:" + 4 × (tab + 8 hex) + 2）
      + 9                     （"<RealTek>"）
```

`A0` 71 ✓ · `C7-pre` 354 ✓ · `C7a-rb` 213 ✓ · `E10b` 118 ✓ · `C7a` 130 ✓ · `C7b` 138 ✓，
**每一個都在格子跑之前算好，每一個都精確。一個回覆完不完整，從此是一次減法。**

### 🔴 四、`C-14` 用一個會動的位元關掉，而 `§D` 因此被改寫

**量到的**，`B7a`（放開）與 `B7c`（按住，包在 `--esc-after 20 --seconds 35` 裡，
所以這一格**沒有**預期到的那條分支 —— 重置 —— 若真的發生，也救得回來）：

```
released  B8003500:	FFFFFFDF	00000000	FF000000	0000003C
held      B8003500:	FFFFFFDF	00000000	FF000000	0000001C
XOR                                                  00000020   → 只有 bit 5
```

> **`C-14` 答完：那顆按鈕是 `PABCD` bit 5 上的一支 GPIO，低態有效。它不是 `RESET#`。**

- w1 `PABCD_CNR` = `FFFFFFDF`：🔴 **bit 5 是整個 32 位元字裡唯一被清掉的位元。**
  反組譯的宣稱（`0x804083AC`，從 main `0x80406778` 無條件呼叫，清 `0xB8003500`
  與 `0xB8003508` 的 bit 5）由一個「正好只有那個位元是 0」的字在矽片上確認。
- w3 `PABCD_DIR` bit 5 = 0 → 輸入；w4 `PABCD_DAT` bit 5 = 1 → 放開，低態有效帶上拉。
- `CNR`／`DIR` 按下前後不變 ⇒ 讀到的是**腳位狀態**而不是一次重新設定。
  `B7c.log` 裡**沒有 `Booting...`、沒有 banner** —— 按住期間板子沒有重置。
- **量到的**（`B7b`，`DW B8000000 1`）：`0xB800000C & 0xF` = **`0xF`，不是 13**。
  `0x80408DE4` 只在那個 nibble 是 13 時才從 `[0x8040DD4C]+0x44` 取按鈕狀態；
  它不是，所以 loader 讀的是真 GPIO，**`B7a`/`B7c` 讀的就是 loader 讀的那支腳。**

**與操作者的回報對得起來**：按住十秒會回復原廠設定，那是**廠商 kernel 在跑的時候**，
也就是軟體在替一支 GPIO 計時；而硬體 `RESET#` 承載不了「按住多久」這個語意。
在 loader 提示字元下沒有東西在替它計時。兩個觀察講的是同一支腳。

🔴 **這同時否證 `notes/power-and-programmer.md` §3 的「這台的 loader 只輪詢 UART」** ——
loader 自己的 init 把這支腳設成 GPIO 輸入，`0x80408DE4` 讀它。
那一句是三個「不存在」推出來的，而**其中一個根本不是不存在**。

**對 `§D` 的後果**：

| | 原本寫的 | 現在 |
|---|---|---|
| `D3` | 按按鈕，預期一次完整的 stage-1 冷開機 | **不會發生，而且問題在這一格被花掉之前就答完了。** 退役，不刪除 |
| 🔴 `D2b` | scratch 字撐過 `D1` 的暖重置；**否證條件是「按鈕（冷開機）之後同一個讀值必須變」** | **按鈕給不出冷開機，這個否證條件沒有了。** 移到 `§G` 那次本來就要付的電源循環（`D2b-cold`），讀 `DW 81000000 1` 與後面那個 canary，零額外成本 |

而且 **`D2b` 現在有三個結果不是兩個**：`0x81000000` 在第二節那張表裡面，
所以一次「重跑了表的初始化程式」的暖重置會回 `00000400 00000001 FFFFFFFF 00000000` ——
**既不是 `DEADBEEF CAFEBABE` 也不是垃圾**，而兩列版的格子會把它記成「重置清掉了 DRAM」。
新格 `D2c`（canary `EW 80A00000 5EA72D2B A5A5A5A5`，值刻意跟 part one 不同，
好讓「這一次的寫入到達了」可證）才讓中間那一列可判。

### 🔴 五、`NET-13` 關掉，五個點全部量到，而那張圖不是線性的

| 從 WAN 側數的插孔 | port |
|---|---|
| 1 = **WAN** | `PSRP0` |
| 2 | `PSRP2` |
| 3 | `PSRP3` |
| 4 | `PSRP4` |
| 5 | **`PSRP1`** |

**量到的**，一次一條線、`E11a`–`E11e`，每次 `DW BB804128 8`，
每次**恰好一個 port 的 bit 4 被設起來，而且每次都是不同的那一個**。

🔴 **實體順序是 `0, 2, 3, 4, 1`。** 一支從插孔位置取 port index 的驅動程式
**恰好錯在一個插孔上**，而那正是 `PORT1` 跳過的那個 port。
`E12` 那條規則（「`n` 取自 `E9` 的 `ExtPHYID`，不是取自 port 編號」）現在有了具體案例，
只是它的形狀是**絲印位置對 port index**，不是 `ExtPHYID` 對 port index。

**`NET-07` 的解釋因此換掉。** `E8` 已經確立 `PORT1` 跳過 PHY address 1
是**關於 port 而不是關於 PHY**；理由**不是**「port 1 沒有插孔」。
剩下的候選來自 help 字串本身，`PORT1: port 1 patch for FT2` ——
一個**為了** port 1 而套在其他四個 port 上的 patch，好讓 port 1 在 FT2 裡被單獨測。
*推測的*；否證路徑是讀那段程式寫了什麼，由 `docs/loader-phy-and-switch.md` §4 擁有。

同一段還量到三件：

- 🆕 **`PSRP` bit 6/5 是協商出來的流量控制。** 跨兩次電源循環、兩種對端的配對比較：
  seating 1 對 PC NIC，`ANLPAR` = `0xC1E1`，bits 6,5 **清**；今天對 RTL8153 USB GbE，
  `ANLPAR` = **`0xCDE1`**，bits 6,5 **設**。**`0xCDE1 XOR 0xC1E1 = 0x0C00`** ——
  兩個 `ANLPAR` 只差 bit 11（`ASM_DIR`）與 bit 10（`PAUSE`），
  而兩個 `PSRP` 只差 bit 6 與 bit 5，**別的什麼都沒差**。
  斷線狀態下每個 port 的 6,5 都是設起來的，所以預設是「開啟」，不宣告 PAUSE 的對端把它清掉。
  `NET-11` 早就從來源 B 給了 6 = RxPause、5 = TxPause；**這是頭一次讓其中任何一個按要求動。**
- 🆕 **兩個背後沒有插孔的 `PSRP` 字，在五次拔插下不動。** 第 7、8 個字今天八次讀
  **全部是 `0000007A`**（bit 4 LinkUp、bit 3 全雙工、速度位元 `10`），第 6 個字全程 `000000E2`。
  五次實體移動改了 `PSRP0`–`PSRP4` 而完全沒碰到這三個 ⇒ 它們不由任何實體插孔驅動。
  *推測的*：交換器的內部／CPU 側 port。這是一個**有五次獨立機會被否證**的假說。
- `E10b`（**任何插孔都沒有線**）：`PSRP0`–`PSRP4` 全部 `000010E0`，bit 4 全清，五個一模一樣。
  **這是 `E10` 從來沒能取到的那個零** —— seating 1 有線插著，`PSRP2` 讀 `0x1099`，
  所以 `E10` 寫的那個期望「沒插線時每個字 bit 4 = 0」**從來沒有被真的量過**。
  「一個後來會變成 1 的 0，比一個孤零零的 1 值錢」是 `E10` 自己的話，而這是那個零。

`E9b`（`DW BB804100 8`）與 seating 1 的 `E9` **逐位元組相同**，
而這次開機期間線插過**四個不同的插孔** ⇒ `PCRP` 確認與連線狀態無關，
`F2` 的掃描因此有了**同一次開機內**的比較基準。
`E12c`/`E12d`：連線 `BMSR` `0x78ED`、未連線 `0x78C9`，**XOR = `0x24`** ——
bit 5（Autoneg Complete）與 bit 2（Link Status），別的都沒動，
在**不同的實體 port 上**重現 seating 1 那一對。
🆕 `E12e`（`PHYR 0 5`，未連線的 port）：`ANLPAR` = **`0x0001`**，只剩 802.3 selector ——
跟幾秒前 `E12b` 的值不同，所以這個暫存器是**每 port 一份**（共用會讓 `E12b` 整格作廢），
而未連線的 port 讀到的是**被清掉**而不是殘留。沒有來源預測過，seating 1 沒讀過。

**這四次 PHY 讀同時是 `F1` 的正控制**：MDIO 控制器在幾秒前對 address 0 與 1、
四個暫存器完成了交易，所以 `PHYR 5 2` 若卡住，可以歸因到 address 5 本身，
而不是控制器、匯流排或命令。

### 🔴 六、三個我自己的結論被撤回，而三次都是一個事先寫下了結果的格子殺的

| 結論 | 被誰殺的 | 值多少 |
|---|---|---|
| 「`PSRP` bit 8 是黏著的，`DW` 不清它」（來自 `E11a2`） | **`E11c2`** —— 專門為了分開兩個模型而造的格子：`PSRP0` 在 `E11c` 已經斷線、它的插孔是**空的**，不可能有新的 down 事件，而一次讀就把 bit 8 從 1 帶到 0 | 真答案（read-to-clear）是 `D` Table 65 與 `NET-11` **本來就帶著**的那一個 |
| 「`PSRP1` 沒有插孔，這就是 `PORT1` 跳過 address 1 的原因」 | **`E11e`**，它的否證條件事先點名了這個結果 | 插孔數是**回報**來的不是量到的；`NET-07` 的解釋因此仍然開著 |
| 「`CONT` 的沉默是行緩衝區裡的殘留」 | **`flush-cont`**，它回了一個裸提示字元 | 導出第八節那條真正的規則，而那條比殘留規則寬 |

`E11a2` 那個讀值也有了解釋，而且**不是儀器缺陷**：一條還在穩定中的連線上的**第二次
autoneg 鎖存**，是真事件。read-to-clear 在 `E11e` 第三次被確認（`PSRP3` 的 bit 8
在兩次讀之間沒有任何插拔事件的情況下 1 → 0）。
**`RUNSHEET.md` `E11` 的機制講對了一半**：bit 8 確實是斷線旗標、確實是 read-to-clear，
但那一格的程序（「再讀一次，bit 8 就是 0」）在 port 上還掛著一條正在穩定的連線時
**不是可靠的鑑別器**。撐起這一格的是跟著網路線跑的 bit 4。

### 🔴 七、一個方法錯誤，寫出來而不是安靜地改掉

`PREDICTIONS-block3.md` 給 `CONT` 的容差是 **±5 counts**，
而它是把一個從 **253 秒**基線得到的速率當成精確值往前傳播算出來的。
那個速率帶著約 50 ppm 的不確定度，在 4,287 秒上是 ±215 ms ≈ **±21 counts**。
（`CONT` 沒有回資料，`PREDICTIONS-block3b.md` 把同一個公式與同一個 ±5 原樣重述給 `CONT2`，
所以真正對上這個門檻的讀值是 `CONT2` 的。）
實測差了 **9.1 counts** —— **在誠實的容差裡面、在寫下來的那個容差外面。**

這一格照樣有鑑別力（板子重置那條分支會差約 400,000 counts），
但**門檻與它自己所依據的不確定度不一致**。
這跟第一節那件事是同一根線：**短基線上的儀器誤差被讀成了被測物的性質。**

### 八、量測系統：console 轉接器在一段純空閒中離開了主機的 USB 匯流排

**量到的**。WSL uptime `10679.98 s` = **04:33:57**，`dmesg` 記下
`vhci_hcd: connection closed` → `release socket` → `usb 1-1: USB disconnect` →
`cp210x ttyUSB0 ... disconnected`。Windows 的 `usbipd list` 把 `1-1` 整個移出
*Connected*，`Get-PnpDevice -PresentOnly` 找不到 `VID_10C4` ——
**所以它離開的是主機匯流排，不只是 usbip 附掛**。**WSL 沒有重啟**
（uptime 從 01:36:01 起全程連續）。

**替板子與操作者洗清的時間軸**：前一個擷取 `E9b` 落在 **04:26:33.51**，
掉線在那之後 **7 分 24 秒的純空閒**，按鈕是再之後才按的。
**根因未定。** 候選（一個都沒被判掉）：usbip socket 暫態、USB selective suspend
沒能喚醒、接頭鬆動。**若在長空閒中再犯，先測 selective suspend。**

**工具的順序讓沒有東西被送出一半**：`_check_send` 在 `serial.Serial()` 之前驗，
open 失敗，命令根本沒離開主機。那個順序就是 `N4` 在測的東西。

🆕 **量到的：重新列舉之後送出去的第一個東西是一個丟掉的。**
`CONT`（`DW 8040DCE8 1`）回來 **24 bytes**：回音、`\n\r`、`<RealTek>` ——
**一行資料都沒有**，正是 `B8` 在長度參數解析成零時的形狀。
最順的解釋是行緩衝區殘留，而它**被否證**：下一格 `flush-cont`（`--send ''`）
回了一個 **11 bytes 的裸提示字元、沒有 `Unknown command !`**，緩衝區是空的。
之後送出的同一條命令 `CONT2` 正常。

> **重新列舉之後的第一條命令會被回音但不會被執行，特徵是「回音 + 提示字元 + 沒有輸出」。**
> *推測的*：板子的 UART 在重新列舉期間看到 break 或框架錯誤，`readline` 丟掉緩衝，
> 剩下的 CR 產生一個空行提示。**機制沒有建立，行為有。**

**因此那條 flush 規則被重述，而它兩個方向都錯：**

- **太窄**：它不涵蓋 USB 重新列舉 —— 那根本不是一次擷取。現在涵蓋了。
- **太寬**：真正的觸發條件是**「任何一次擷取，寫進 port 的最後一個 byte 不是 CR」**，
  也就是任何跑過 `--esc` 或 `--esc-after` 的擷取。**量到的**：part one 的
  `C1 → C2 → C3a → C3b → C4a → C4b → C6-readback` **全部**被 `--seconds` 切斷、
  **一個都沒 flush**，而且每一個都是對的。ESC 迴圈結束在一個牆鐘期限上、不寫終止符；
  `--send` 的擷取結束在工具自己寫的那個 CR 上。

另外兩件關於儀器的：

- **量到的：USB GbE 轉接器的連線狀態只有 `ethtool` 看得見。** `0bda:8153` 綁到
  **`r8153_ecm`**（CDC-ECM）而不是原生 `r8152`：`/sys/class/net/<if>/carrier`
  **永遠讀 `1`**、`operstate` **永遠讀 `unknown`**，插不插線都一樣。
  **一個永遠說 1 的工具不可能失敗。** `E11a`/`E11b` 的板外佐證用的是
  `ethtool <if> | grep 'Link detected'`。同一支驅動的 `Speed`/`Duplex` **不可信**
  （`Speed: Unknown!`、`Duplex: Half`，而當時是 100M 全雙工連上的）。
- 🆕 **量到的：`.log` 的 mtime 就是最後一個 byte 落地的時刻，準到次毫秒。** 三個方式：
  `E1b` 的 mtime 比 `started_wallclock` 晚 **117 ms**，正是 71 bytes 在 38400 上的往返；
  `A-catch` 晚 **25.2 s**，對上它 `.timing` 裡 `24.997` 的最後一個 ESC；
  `flush.log` 的 `.timing` 顯示 31 bytes 以 **3–4 bytes/ms** 到達，那是 38400 的線速
  （31 × 10 / 38400 = 8.07 ms）—— 一個被排空的緩衝會在一次 read 裡全到。
  **兩個用途今天都用到了**：`.timing` 能分辨「板子現在在講話」與「我在讀一個過期的緩衝」；
  而同一條命令的兩次擷取，從執行到最後一個 byte 的固定偏移相同，**在差分裡會抵消** ——
  第一節那個時脈量測靠的就是這件事。

### 九、`§A`：ESC 帳目是一個分割，而開機時間軸給了 `D1b` 一個它本來沒有的下界

**量到的**（`A-catch`，1066 bytes，`--esc 25 --seconds 40`，第 8.129 s 上電）：

- ESC 收攏之後，開機文字與 part one 的 `A-catch.log` **逐位元組相同**，
  含 `Booting...` 後面那個 `\x00`、`chipName: UNKNOWN`、`ramSize: 32M`。第三次電源循環同一串。
- `---Escape booting by user` **再次缺席**，與 `C-13`（ESC 已設 `gCHKKEY_HIT`）一致。
- 🔴 **128 bytes 的分割是精確的。** loader 回音了 **730** 個 ESC，分成
  `[128, 128, 128, 128, 128, 90]`，**730 = 5 × 128 + 90**，而那 90 的餘數**沒被消耗** ——
  下一格 `flush` 吃掉它，回**正好一個** `Unknown command !`。part one 是 `7 × 128 + 12`。
  **兩次獨立電源循環、十二次未終止的填滿，關係是一個分割，不是數字 128 剛好出現兩次。**
- 🆕 **ESC 速率是 50.2/s，而瓶頸是主機不是線**：730 bytes 花 14.55 s，
  在 38400 上那些 byte 只要 0.19 s，天花板是工具的 `ser.write(ESC); drain(0.02)` 迴圈。
  **對 `D1`/`D4` 的後果**：`--esc-after 20` 會沖出 ≈1000 bytes ≈ 7 次填滿加一個餘數 ——
  由 `B7c` 精確證實（985 bytes，`7 × 128 + 89`，七個 `Unknown command !`）。
  **所以 `flush-d1` 不是條件式的**：餘數是 `N mod 128` 而 `N` 事先不可知。
- 🆕 **ESC 視窗的消費者不回音，命令迴圈才回音。** 上電（8.129 s）到提示字元（10.444 s）
  之間送出約 115 個 ESC，log 裡**一個都沒有**；提示字元之後的每一個都有。
  `gCHKKEY_HIT` 那條路徑與 `readline` 是不同的程式，log 的 ESC 數只反映後者。
- 🆕 **開機時間軸**（取自 `.timing`）：第一個 UART byte → banner **0.585 s**；
  banner → `P0phymode` **1.661 s**；→ `---Ethernet init Okay!` **0.063 s**；→ 提示字元 **0.006 s**。
  **第一個 byte → 提示字元 = 2.315 s，其中 72 % 是乙太／PHY init。**
  **這給 `D1b` 一個它本來沒有的下界**：`D1` 量的是 `Jump to address=` → banner，
  而那段區間**包含**這 0.585 s。**`D1` 低於 0.585 s，就代表暖開機跳過了冷開機會做的事。**
  `D1b` 原本寫的是「大約一秒，不預測數值」。

`A0` 這次（第三次電源循環）回來的 71 bytes 與 part one 的
`A0b-reopen-control.log` **逐位元組相同**：同一個載入基底、同一個表位址、
同樣 16-byte stride、同樣的欄位順序。

### 十、工具

- **`tools/console-capture.py`**：`_check_send()` 多兩條拒絕。**`len(value) >= 128` 拒絕**，
  推導整段寫在訊息裡（裝置：正好 128 個 ESC → `Unknown command !`；程式：
  `0x80409190`/`0x804091A0` 的 `memset(buf,0,128)` + `readline(buf,128,1)`，
  而 `readline` 只在 CR 那條路徑寫 NUL，長度到底那條 `0x80407194` 不寫，
  於是**填滿緩衝區的那一行沒有終止符**，斷詞器 `0x80407248` 掃過 `sp+143` 進到存起來的暫存器）。
  **是 `>=` 不是 `==`**，因為更長的會被切成 128。第二條：**非 ASCII 拒絕**，
  因為 `capture()` 的 `.encode("ascii")` 發生在**開 port 之後** —— `N4` 存在就是為了擋這個順序缺陷。
- **`tools/test-console-capture.sh` 10 → 13 案例**：`N7` 一行 128 字元的 `--send` 必須被拒
  （輸入就是 **`RUNSHEET.md` `C7` 差點送出去的那一行**）、`P4` 一行 127 字元必須被**接受**
  （輸入就是後來在 bench 上真的打出去的 `C7b`）、`N8` 非 ASCII 必須在碰 port 之前被拒。
  **`P4` 是讓 `N7` 不會在一支「凡是長的都拒」的工具上照樣通過的那一格。**
  三個變異各自隔離一個案例：門檻 128→100 **只**掛 `P4`；刪掉長度守衛 **只**掛 `N7`；
  刪掉 ASCII 檢查 **只**掛 `N8`。
- **`tools/check-predictions.py` 新增**，四個控制、三個必須失敗，見本則開頭。

### 下一步

`§F`（`F1` 是會終結整場的風險格）→ `§D`（`D0a`/`D0b` 兩個裝彈的寫入排在 `§F`**之後**，
因為 `F1` 可能付掉一次電源循環，而 DRAM 跟著走）→ **`B3`（R0，關現行 gate）**。
`§G` 要付**兩次自己的電源循環**，`G0` 這個位址探測必須排在 `D0b` 之前 ——
`D0b` 寫的正是 `G0` 要讀成未動過的那個位址。

## 2026-08-24（第六段）— seating 2 上機第三段：`R0` 關掉，而 `C-17` 從開題那天就問錯了寫入者

**五次電源循環（`bench/2026-08-24c` / `d` / `e` / `f`），81 個擷取，
18 個事前預測區塊中 **17 個**通過 `check-predictions.py`（`block12` 因 `24e` 漏抓窗口有 9 格從未跑，於 `24f`/`block13` 重跑並 10/10 通過），**存在的 81 個擷取全部晚於其預測檔**，**81 個擷取裡沒有下過任何一個寫 flash 的指令**。**
`§F`、arm、`§D`、`§G` 全部跑完，`R0` 在 `G7` 關掉。
其中**兩次拔電是漏抓 ESC 窗口的代價**，成因不同，兩次都記在下面。

### 開工前：`console-capture.py` 1.2，以及它自己的對抗式審查

`PROGRESS.md` 的「Next after this」點名的桌面項目是：讓兩個 ESC 迴圈之後
工具自己補一個終止 CR，把 `flush-` 格從「規則」變成「儀器的性質」。
寫完是 40 行工具 + 120 行測試，套件 13 → 18。

**然後把它丟進 `hazlint` 那次用過的同一套對抗式審查**：五個 lens，
每一條 finding 交給另一支專門去反駁它的 agent。**32 條聲稱，10 條活下來**，
而且每一條都是**跑出來的**不是讀出來的。其中四條會在今天花掉一格：

1. **沒有任何案例涵蓋「`--esc` 但沒有 `--send`」** —— 那正是 `A-catch` 的形狀，
   今天的第一格。一個把終止動作 gate 在 `args.send is not None` 底下的變異體
   拿到 18/18。→ `P8`/`N11`。
2. 🔴 **ESC 迴圈中途 Ctrl-C 會完全跳過終止動作。** 在 pty 上量到：
   `D1` 形狀的中斷留下 245 個 ESC、殘留 **117**，而
   `117 + len('DW B8003110 1') = 130 ≥ 128` —— 那是緩衝區懸崖不是可回復的
   `Unknown command !`；而 metadata 記的是 `"cr": {}`，這份檔案自己定義為
   「那個迴圈沒跑」。**一份 1.1 的擷取戴著 1.2 的版本號。** → 修掉 + `P10`。
3. **settle 完全沒有防護**：`budget = 0.0`、把 settle 迴圈整段刪掉、
   把 `PROMPT` 改成永遠不匹配的字串 —— 三個變異體都拿到 18/18。
   → `P9`/`N12`/`N13`，而且是這套件裡唯一會去讀 `.meta.json` 的案例。
4. **`N10` 的斷言是 `!= "CR"`**，所以一個**根本沒跑起來**的變異體會被記成
   「變異被殺掉」。→ 改成 `== "NONE"` 且 ESC > 0。

**完備性批評者又補了五個缺口**，其中一個今天派上用場：
`--seconds` 會把 settle 預算夾到 0，而那時 `prompt_seen: false` 會跟
「等滿了而板子沒回話」共用同一個值。→ `N14`，預算為 0 時記 `null` 不記 `false`。
**這個欄位在幾小時後救了一次判讀**：`24e` 漏抓窗口時，
`prompt_seen: false` 配跑滿的 3 秒 settle 就是那個簽章。

套件最後 **13 → 25**（24 格、25 個結果，`P3` 檢查兩件事），**14** 個是必須失敗的控制項（`N1`–`N14`）。
`RUNSHEET.md` 的 `P2` 那一列同步改成 `25 passed` ——
**那一列已經過期兩次**（`6c6c3b5` 把套件從 7 帶到 10 而它還寫著 7）。

**而審查給的最好的一個建議是我原本弄反的**：不要刪掉 `flush-d1`/`flush-d3`。
1.2 之下它們的期望值**反過來** —— 裸 prompt 11 bytes 是通過，
`Unknown command !` + prompt 31 bytes 是失敗 —— 於是它們從雜事變成
**唯一能證明「loader 拿那個 CR 做了什麼」的量測**。套件只能證明工具寫了什麼。
今天三次獨立實例（`flush-d1`、`flush-d3`、`flush-d4c`）**全部 11 bytes**。

### 🔴 一、`R0` 關掉，而證據鏈的每一環都有它自己的反證條件

| 環 | 讀數 |
|---|---|
| `G1a/b/c` | 頭／中／尾三點對上 payload 檔 → loader 已 staged 整份 964 KiB，`G6` 可跑 |
| `G6` | 從 RAM 開機，對 `uart-boot.log` 自 `decompressing kernel:` 起 **62 行比對、62 行相同、0 行不同**，而且是**逐位元組**的 1687/1687 |
| `G2-rb` | `8040D4A0` = `00000000` —— 守衛讀在燒錄路徑自己的那一個指令 `0x80401B9C` 上 |
| `G4` | 987,138 bytes 上傳／讀回／`cmp` 逐位元組相同，sha256 相符 |
| `G5` | 三點毒化 → **驗證毒化落地** → 重新指向 `0x80500000` → 再上傳 → 三點都變回 dump 自己的位元組 |
| `G8a` | `AUTOBURN` 仍 `00000000`；flash 兩區對**開機前**基準線逐位元組相同 |
| `G7` | **`G7.log` 與 `G6.log` 整檔逐位元組相同**（1789 bytes，sha256 同為 `2f921f75…`），而且網路送進去的 kernel 開到 userspace、ping 2/2 3.6 ms |
| `G8b` | flash 兩區對 `G8a` **和** `G8-pre` 都逐位元組相同 |

**`G5` 是 `G4` 結構上做不到的那一件事。** `put` 和 `get` 都服務
`[0x8040D3A8]`，所以往返證明不了落點；而 `G1` 已經證明**正確的位元組本來就在
那裡**，所以不先毒化就重讀，一個封包都沒到也會過。

**`G8b-ab` = `00000001` 是這一場最漂亮的一格。**「每次重置都把 `AUTOBURN`
打回 1」一直是從映像初始值加 `B6` 推出來的**論證**，而 `G8a` 必須排在拔電之前
就是靠它。這一格把論證變成**這次拔電上的量測**。

**`R0` 有資格說什麼、沒資格說什麼，寫在會被引用的地方**：三個 flash 區塊
一共碰到 **4,194,304 bytes 裡的 512 bytes**。那句話是
「loader 頭部與 `cr6c` 標頭未變」，**不是**「零 flash 位元組」。

### 🔴 二、`C-17` 答了，而它的前提從第一天就是錯的

`C-17` 記著 `0x81000400` 那張表**推**為「loader 的網路緩衝區池」，
論證是「未初始化 DRAM 生不出自己的位址，所以有東西寫了它」。
**後半成立，前半收回。**

| 條件 | `0x81000400` |
|---|---|
| **16 小時**斷電之後（`X1`，今早） | 高熵偏壓雜訊 |
| **幾秒**斷電、緊接在 kernel 跑過之後（`X1-24d`、`X1-24f`） | 整張 32 位元組週期表原封不動回來 |
| 連線建立之後（`X1c`） | 與對照格逐位元組相同 —— 不是連線蓋的 |
| `IPCONFIG` 之後（`X1-post`） | 與對照格逐位元組相同 —— 不是 `IPCONFIG` 蓋的 |

**正控制把推論整個拿掉**：`0x80A00000` 在拔電之後讀回**我自己上一次拔電
用 `FLR` 寫進去的 16 個字，逐位元組不變**（`G0-head-24d` 對 `G8pre-rd0`）。
寫入者不是推出來的，是我下的指令。

**所以這是 DRAM 短時間斷電保留內容，不是 loader 的資料結構。**
`+0x18` 那個自指的 `list_head` 正是 `INIT_LIST_HEAD` 留下的形狀。
`0x400` 不是封包緩衝區大小。

**它變成什麼**：`MEM-15`，一條 DRAM 性質。**對往後每一個 canary 的後果**：
「它撐過了一次拔電」在這塊板上什麼都不代表，除非同時說明斷了多久。
今早 `X1`/`X2` 跨 16 小時、23 個特徵字零殘留 —— 那才是讓 `D2b`/`D2c` 站得住的東西。

### 三、`0x81000000` word 1 每次開機都被寫成 `00000144`，而我先前把訊號讀成雜訊

寫 `DEADBEEF` → 重置 → `00000144`。再寫 `F00DFACE` → 重置 → **又是 `00000144`**。
冷開機直接讀也是 `00000144`。word 2 兩次都活著，所以不是衰減。

**而它先前就在資料裡，我讀成了雜訊。** 1 KiB 週期性檢查裡：

| 偏移 | `0x81000000` | `0x81000400` | 差異位元 |
|---|---|---|---|
| `+00` | `00000144` | `57890336` | **13 / 32** |
| `+04` | `7BB04BB7` | `73F64BB7` | 4 / 32 |
| `+08` | `34361357` | `34361357` | **0 / 32** |
| `+0c` | `AB2563FB` | `BB0563F3` | 3 / 32 |

word 1 是唯一的離群值，超出其他三個三倍以上。我當成雜訊；
它其實正是「有東西寫了這個字、打斷了到處都成立的週期性」的訊號。

`0x144` = 324，意義不明。**stage 2 的 900 個 `lui` 裡 `lui …,0x8100` 是 0 個**，
所以位址是執行期算出來的、或寫它的東西在 stage 1。

### 🔴 四、`C-8` 關掉了，關在一個比它等的暫存器更好的東西上

loader 在開機文字裡印 **`Reboot Result from Watchdog Timeout!`**，
位置在 `ramSize: 32M` 之後；冷開機那一行是**一個空格**。三次量到。

**它讀的是硬體位元不是軟體旗標**，而這一點是 `D4`/`D4c` 免費給的：
看門狗是用 `EW` 從 prompt 武裝的，loader 之後一條指令都沒執行，那行仍然出現。
如果它是 `J BFC00000` 路徑上設的 RAM 旗標，就不會 —— 而 DRAM 確實撐得過暖重置。

**`WatchDogIND` 本身不能用**：`D2` 與 `D2d` 都讀 `A5000000`，bit 20 是清的，
`D2` 預測的 `A5100000` 被否證。*推*：loader 讀完就清（write-1-to-clear），
這跟它印了那行話一致。

**第二個鑑別器也成立**，但位址必須換：`0x80A00000` 的 canary 撐過**三次**
暖重置逐位元組不變；`0x81000000` 不能用，見上一節。

### 五、`CLK-08` 填上了，而 2.5 % 的殘差是被定性的不是被掃掉的

兩個 `OVSEL` 點，用 ESC 回音心跳量（loader 逐個回音，板子一死回音就停，
20 ms 解析度）：

| `OVSEL` | 算出來 | 量到 | 短少 |
|---|---:|---:|---:|
| `1001`（2²⁴） | 1174.4 ms | **1145 ms** | 29.4 ms |
| `1000`（2²³） | 587.2 ms | **572 ms** | 15.2 ms |

分頻／未分頻沒有疑義 —— 未分頻的候選是 83.9 ms，差 14 倍。
🔴 ~~**而殘差的形狀說明了它是什麼**：短少量比值 1.93、兩比值吻合 0.09 %，
所以是尺度因子不是儀器延遲，看門狗快 1.0257 倍。~~
**這一段當晚被反駁稽核整段推翻，見 §十二 ②** —— 發表的 1145 / 572 ms
對不上這裡宣告的觀測方法，而且一個固定延遲對兩點吻合得跟尺度因子一樣好。
**免費補上的那一個確認留著，因為它不靠任何時間戳**：兩格的 ESC 回音個數是
**56 對 28 = 恰好 2.000**，這單獨就確認了 `OVSEL` 的分裂欄位解碼。

~~**另外三次獨立重置給了 R4 要的數字**：重置 → console 第一個 byte = 340 / 348 / 345 ms，吻合到 2.4 %。~~
🔴 **這一段當晚就被反駁稽核推翻 —— 三個真數字貼錯了名字，見 §十二 ③。**

### 六、`§F` 跑了，沒有卡住，而它預期的發現是反的

`F1`（`PHYR 5 2`）回來了，87 bytes，正是預測的大小，`UID=0x00000000`。
`F2`（`MDIOR 2`）掃完 32 個位址：**0–4 回 `0x001c`，5–31 回 `0x0000`**，
1042 bytes 的大小逐位元組算得出來。

**`docs/loader-phy-and-switch.md` §6 的事前預測 32 點命中**，
分界正好落在 datasheet 說的地方；而內建反證（32 行全同 = 匯流排在回音）
**有真的機會觸發卻沒觸發** —— 兩個相異值，不是一個。

**這一格預期的發現是「`MDIOR` 絕對不能在這顆上跑」。相反才是真的：**
控制器在 32 個位址上都會完成，`MDIOR` 現在是這裡最便宜的全位址掃描，
一個指令取代 32 個。這對 R6 是一支儀器。

**兩個小修正，都是反組譯讀出來的主張被矽片改掉**：
① `F1` 的風險論證說不存在的位址會回 `0xFFFF`「因為匯流排被拉高」——
實際回 `0x0000`。**承重的那一半（交易會完成）成立，機制細節那一半被否證**，
而那正是驅動程式用來偵測 PHY 不存在的判準。
② §3 的格式字串表寫 `Reg=%02d`，矽片印 `Reg=2`，所以是 `%d`。

### 🔴 七、`NET-13` 被操作者推翻，而量測站在他那邊

`NET-13` 記著實體孔序是 `0, 2, 3, 4, 1`，並由此導出
「照絲印位置取 port index 的驅動會在剛好一個孔上出錯」。**兩句都收回。**

錯在哪：五筆 `PSRP` **讀數**是量的，但**貼在每筆讀數上的孔別是事後指派的**，
而寫入時假設了「五次換孔依實體位置依序走過」。今天兩個實測點
（`E10c`：換孔前線在孔 1 → `PSRP1`；`E10d`：移到孔 2 → `PSRP2`，
而且同一次擷取同時帶著離開的 bit 8 latch 與抵達的 bit 4）符合線性圖、
不符合 `0,2,3,4,1`。

**同一個原因造成的第二次失誤** —— 第一次是「`PSRP1` 沒有孔」，
死在孔數是回報的而不是量的。**流程修正：跟著換孔的 `PSRP` 讀數，
孔的身分要寫進 `--out` 檔名**，讓標籤躺在檔案系統裡而不是誰的記憶裡。

### 🔴 八、一個被指定為「唯一可信」的儀器，其實不會回報 link

規則寫著「網卡 link 狀態只能看 ethtool」。今天 `ethtool` 說
`Link detected: no`，同一時間**板子**說 `PSRP1` bit 4 是 set、
而且帶著 `E12b` 建立的 `0xF9` 流量控制簽章（= 對端是 RTL8153）。

主機介面是 **administratively down** —— `<BROADCAST,MULTICAST>`、沒有 `UP`、
`qdisc noop`。`ethtool` 的 `Link detected` 反映的是 netdev 不是線路。
`ip link set up` 之後立刻變 `yes`。
**而 `/sys/.../carrier` 也不是「永遠 1」**：介面 down 時它回 `Invalid argument`。

**修正後的規則**：`ethtool` 只有在 `ip link set up` **之後**可信；
板子的 `PSRP` 是那個獨立的第二來源。
**沒抓到的話 `§G` 的 `put` 會在一個 admin-down 的介面上失敗，而且看起來像板子的錯。**

抓到它的是 `E10c` —— 一個唯一任務是重現 `E10b` 全埠 down 的對照格。

### 九、ARP，雙向確認，而它是 R4 的一條需求

`G4-put` 花 **10.46 s**、**3 次重傳**；`G5-put` 花 **1.52 s**、**0 次**。
3 × TFTP 逾時 3.0 s = 9.0 s，對上實測差 8.935 s。

**loader 的 MAC 是從它被給的 IP 合成的**（neighbour entry 讀到
`56:0a:01:01:01:e8`），vendor kernel 用真的那一個。
前一次 kernel 留下的 stale entry 讓第一次傳輸吃三次重傳；
而 `G7` 之後一個 stale 的 **loader** entry 直接讓 ping 失敗，
清掉之後立刻 2/2 —— **兩個方向都確認**。
R4 的無人看管 `bench-ci` 必須在每一次 loader↔kernel 轉換時 flush neighbour entry。

**而這一條也是「不要把模糊的讀數寫成結論」的一個實例**：
`G7` 之後 ping 失敗，我沒有寫「kernel 沒起來」，先去分辨了。

### 十、今天加進 sheet 的三種格子，都是同一個形狀的洞

- **`G8-pre`** —— `§G` 在它第一次開 kernel 之前沒有 flash 基準線，
  `G8a`/`G8b` 是拿另一天的 dump 比。加上去之後兩者變成同一場的 `cmp`。
- **`D0-rb1`/`D0-rb2`** —— `D0a`/`D0b` 的期望值都是「靜默」，
  而靜默的 `EW` 跟被拒絕的 `EW` 分不出來。
- **`G5-pv1/2/3`** —— 沒有它，「`5A5A5A5A` 被蓋掉了」跟「毒化根本沒落地」
  分不出來，而 `G1` 已經證明正確的位元組本來就在那裡。**那一格會在
  一個封包都沒到的情況下通過。**

三個都是**在寫該區塊的 predictions 時**發現的 —— 逼自己回答
「如果什麼都沒發生，這一格會讀成什麼」，洞就自己現形。

### 十一、兩次拔電的代價，而只有一次是人的問題

① 我叫操作者**先插回去**再跟我說，那把 ESC 串放到窗口之後。**我的錯**，
   修法是 capture 先起。
② 修好之後窗口還是漏了：ESC 跑滿 45 秒，**開機文字在 t=64.2 s 才出現**。
   **那是程序的缺陷不是操作者的** —— 多串一秒 ESC 是免費的，
   漏掉窗口要賠一次拔電，而 45 秒是照實驗室尺度訂的。
   **常規改成 `--esc 180 --seconds 200`。**

`bench/2026-08-24e/A-catch` 留著不刪：它是這個專案第一份
「從儀器這一側看漏掉 ESC 窗口長什麼樣」的紀錄，
而 `cr.prompt_seen: false` 配跑滿的 settle 就是那個簽章 ——
**那個欄位存在，正是因為 1.2 審查的完備性批評者堅持
「沒去看」和「看了沒看到」不能共用一個值。** 寫下它的幾小時後它就被用上了。

### 免費撿到的

- **開機文字跨三次完整擷取到的拔電逐位元組相同**（`24c`/`24d`/`24f`，各 181 bytes）；`A0` 同樣三次。🔴 *（原本寫「五次」，見 §十二。）*
- **vendor kernel 的 console 有 getty**，把控制字元回音成字面的兩字元
  `^[`（canonical 模式 + `ECHOCTL`）。**這是不送任何東西就能從轉錄分辨
  「現在是 kernel 還是 loader」的方法** —— loader 回的是真正的 `0x1b`。
- **上電偏壓 89.5 % 跨 16 小時可重現**（256 bits 只差 27 bits，一個字只差 1 bit），
  而且有 **1 KiB 週期**。後果：未初始化 DRAM 在這塊板上不是熵源，
  而且一個沒寫過的值跨開機看起來會是穩定的。
- `G1c` 的全零尾巴**因為今天的偏壓量測而變成一個強得多的測試**：
  這裡的未初始化 DRAM 是高熵雜訊，所以十六個零位元組只可能是被寫進去的。

### 🔴 十二、寫完之後把每一條主張丟去反駁，21 條裡 9 條被打破

寫完 `LOG` / `PROGRESS` / `SPEC` / `RUNSHEET` 之後，把當天的 21 條頭條主張
各交給一支獨立 agent，指令是**去推翻它**，而且**不准採用文稿裡的任何數字**，
必須自己從 `bench/` 的原始檔重算。結果：**12 條守住，9 條被打破。**
這一節是那 9 條，因為房規說「被推翻的紀錄留在原地」，
而且**被打破的那幾條，多半正是這個專案自己命名過的失效模式**。

**① 🔴「零 flash 位元組」被我寫了四次，而每一次都在摘要位置。**
`RUNSHEET:601`、`PROGRESS` § Now、**`R0` 那一列的判準欄（也就是我剛標成 `✓` 的那一格）**、
以及本篇的標題行。四個地方都在該檔案的摘要句，而界限句在 60 行以外的正文裡 ——
`R0` 那一格甚至在同一個儲存格裡先宣告判準、再自己否認它。
**這是 `G8b` 那一列從一開始就寫著要避免的事，我在別處寫了四次。**
改成「81 個擷取裡沒有下過任何一個寫 flash 的指令；loader 頭部與 `cr6c` 標頭
對同場基準線逐位元組相同 —— 4,194,304 bytes 裡重讀了 512 bytes，0.012 %」。

**② 🔴 看門狗那個「尺度因子」結論不成立，而它錯在我宣稱自己排除掉的那個形狀。**
我發表的 1145 / 572 ms 對不上我自己宣告的觀測方法：ESC 回音心跳給的是
**1122.55 / 549.64 ms**，兩者都被高估了**同樣的 22.4 ms** —— 一個常數。
稽核算出：單一固定延遲 `L ∈ 24.5–37.6 ms` 對兩點的吻合程度與尺度因子完全相同；
而 `RUNSHEET` `D4` **自己設計的估計式**（`D4 − D1`）給的短少量比值是 **1.495**，
比起比例假說的 2.00 更靠近固定假說的 1.00。
`1.0257 倍`、`1.93`、`0.09 %`、`14.653/14.665 MHz` 全部刪除。
連「固定延遲會給出 0.975 與 0.952」都是算錯的 —— `L` = 29.4 ms 給的是 0.9750 與 **0.9499**。
**而稽核也指出決定它的實驗不是第三個 `OVSEL` 點**（在 20 ms 格點下一樣分不出來），
**是把心跳做細**：`drain(0.02)` → `drain(0.002)`。
**免費補上一個完全不靠時間戳的確認**：兩格的 ESC 回音個數是 **56 對 28 = 恰好 2.000**，
這單獨就確認了 `OVSEL` 的分裂欄位解碼。

**③ 🔴「重置 → console 第一個 byte = 340 / 348 / 345 ms」是三個真數字貼錯名字。**
348 和 345 是 loader 印完 `Booting...` 之後、印 `chipName:` 之前的靜默 ——
**它開始的時候 console 已經在說話了**；340 是那個 `0xFF` 到 `Booting` 的間隔。
真正的重置 → 第一個 byte 在 `D1` 上是 **2.07 ms**。
**而它寫上去的當下就跟同一份文稿裡的 `D1b` 矛盾**：0.592 s 減掉 `Booting`→橫幅的
0.583 s 只剩約 9 ms。**這正是 `D1b` 那一格存在的理由 —— 一個量測戴著另一個量的名字 ——
而我在同一天、同一份文稿裡犯了它。** 真正被量到的東西改記為 `CLK-15`（n=9，344.7–356.9 ms）。

**④ 🔴 `NET-13` 我改錯了方向：它該回到未定，不是換一個結論。**
`E10d` 在舊圖和線性圖下**預測相同**（孔 2 → `PSRP2`），
而且 `PREDICTIONS-block0b.md`（早於該擷取 7 分 08 秒）正是**用舊圖**推出它的期望值並命中 ——
**一個不會失敗的對照**。還有一個更省的解釋沒被排除：`E11e` 把線留在點亮 `PSRP1` 的孔，
16 小時沒人動它，那樣 `E10c` 反而是舊圖的確認。
**所以我把一個沒有證據的結論換成了另一個沒有證據的結論，那比原來更糟。**
站得住的只有：五個 RJ45 對埠 {0,1,2,3,4} 是雙射，
因此**孔以 1..5 編號時「孔 N = 埠 N」不可能成立，寫這句話前必須先講清楚編號基底**。

**⑤ 🔴 `C-17` 裡 `IPCONFIG` 的否證用錯了理由，而錯法我 40 分鐘後才在 `G5` 上認出來。**
我寫「`X1-post` 與 `X1-24d` 相同，所以 `IPCONFIG` 不蓋它」——
但那個對照**本來就帶著結構**，重讀不可能失敗，**一個不會失敗的對照**。
正確理由有兩個，都成立：`24c` 全場 46 個擷取裡沒有下過 `IPCONFIG`，
而 `X1-24d` 在 `24d` 的 `IPCONFIG` 之前就讀到結構了。
**連線建立（`X1c`）的否證是有效的** —— 它的對照 `X1b` 不含結構，蓋出來會看得見。
**而且「哪一次執行寫的」仍然未定**：`0x81000400` 在 21:28:23–22:10:35 之間沒被讀過，
那個窗口裡有三次暖重置**和** `G6` 的 kernel 開機。決定它的格子：`J BFC00000` 之後立刻 `DW 81000400 16`。

**⑥ 63 行其實是 62 行**，而多出來的那一行正好是**唯一不同的那一行**
（`---Jump to address=80500000` 對 autoboot 的 `Jump to image start=...`）。
成因：Python `str.splitlines()` 在 `init started:` 前面那個裸 CR 上斷行，憑空生出一行。
而 `G7` 對 `G6` **整檔逐位元組相同**，用行數講反而低估了它。

**⑦「開機文字跨五次拔電相同」實際只有三次**完整擷取到 181 bytes；
`24e` 短了 63 bytes、整份檔案裡沒有 `<RealTek>` —— 而那件事就寫在同一篇的四段之前。

**⑧ `check-predictions` 是 17/18 不是 18/18。** `block12` 失敗，**而且它應該失敗**：
十格裡有九格在 `24e` 漏抓窗口時從未跑，後來在 `24f`/`block13` 重跑並 10/10 通過。
**不要去改 `block12`** —— 工具的 docstring 說得很清楚，改一個字就會重寫 mtime 並破壞檢查，
而這個失敗現在是「有一個 block 被計畫了然後丟失」的持久紀錄。
但摘要句必須寫 17/18 並說明原因，否則就是 `N2` 這個控制在程式裡通過、在散文裡被繞過。
**存在的 81 個擷取全部晚於其預測檔**（最小邊際 +7.7 s），這一半是真的。

**⑨ 控制項是 14 個不是 13 個**（`N1`–`N14`）。

**這一輪自己也給了三個補強**，不是只有壞消息：
`MEM-16` 的虛無假設不是 50 % —— 在這塊板上量出來是 **55.98 %**，所以 89.5 % 要對照 56 %；
`D2` 那一列寫的 `B8003110` 是傾印行的基底，真正的 `WDTCNR` 是**第 4 個字、`0xB800311C`**；
`G8pre-*` 那幾份 `.log` 裡的位址是 **RAM 目的地**不是 flash 偏移。

**要記下來的那一條**：今天有三個獨立的地方，我在同一天內
**發現了「對照組不會失敗」這個缺陷（`D0-rb`、`G5-pv`），
然後在另外兩個地方自己犯了它（`X1-post`、`E10d`）。**
認得出一個失效模式，跟不會犯它，是兩件事。

---

## 2026-08-25（桌面）— 把計畫拿去跟外面對一次，而十一條裡有四條是外面來的

**工時：桌面 ≈4 h / bench 0 / 儀器 0。**（v5 §12.1 承諾要記工時，這是第一則。）

零上電、零 flash、零暫存器。產出：`plan/REVIEW-2026-08-25.md` 十一條裁決、
計畫升到 v6、`notes/rootfs-census.md`、`SPEC.md` `FW-20`–`FW-22` 三列與
`CPU-04`／`TGT-07`／`TGT-08` 三列改寫、`SOURCES.json` 補一棵樹與四筆引用。

**前兩輪審查（8-22 的 18 條、8-24 的 21 條）幾乎全部是內部一致性**：
計畫自己前後矛盾、控制不可能觸發、單位算錯。
**這一輪有四條來自 repo 之外**，而那件事本身有資訊量 ——
它跟 v5 §0 最後那段是同一個形狀的觀察：
錯誤從「關於裝置」換到「關於量測系統」，現在換到「關於外界」。
**內部檢查再嚴也抓不到第三群，因為外界的事實跟內部一致性完全無關。**

### 🔴 一、一條從第一版繼承下來、兩輪審查都沒有重新推導過的 gate 依賴

梯子從 v1 就寫 `R0 → R1 → R2 → R3`，而**兩輪審查檢查了它裡面的每一件事，
從來沒有問過那個箭頭是不是真的**。逐成分追 `R3`：

| `R3` 的成分 | 需要 `R1` 嗎 |
|---|---|
| 我的 defconfig，建在 T-vendor 上 | **不需要** —— T-vendor 編出了現在正跑在這顆矽片上的韌體，那是存在性證明。`-march=mips32` 安靜算錯是**另一條 toolchain 候選**的風險 |
| GPL drop 的網卡驅動（受控變因） | 不需要 |
| 快取層 `c-r3k.c` | **不需要** —— 廠商 kernel 已經走這條路開起來過 |
| codegen 的安全網 | **已經存在而且與 `R1` 無關**：`hazlint` 掃每一顆要進裝置的 `.o` |

真正擋著東西的只有 `R1d`（快取模型）與 `R1e`（CP0 普查），
它們擋的是 `R5b` 的 MTD 快取處理、`R6` 的 DMA 一致性、
handler 能裝在哪、以及 timer 驅動是前置還是加分。
`R1a`／`R1b`／`R1c`／`R1f` 擋不住任何東西 —— 它們是交付物。

**所以 `R1` 拆成 `R1-gate` 與 `R1-pub`，`R3` 的累計從 61 段降到約 41 段，
而總工作量一段都沒有少。** 移動的是**什麼時候知道會不會失敗**：
拆之前，`R1-pub` 的十六段會花在一台**還沒證明能執行我的 kernel 的機器上**。

**這條的否證條件寫在裁決 1 裡**：若 `R3` 在沒有 `R1d` 的情況下開不起來、
而且失敗原因指向快取，那就是「廠商 kernel 走 `c-r3k.c` 成功」
不足以移轉到「我的 config 也會成功」，這條裁決作廢。
—— 但 `R1-gate` 本來就含 `R1d`，所以即使那樣，損失也只有 `R1-pub` 的位置。

### 🔴 二、第四次把「我沒搜到」寫成「不存在」，而這次那棵樹裡有一台 TOTOLINK 板子的 device tree

公開有**兩棵** RTL8196E 的 Linux 樹。一棵在 `SOURCES.json` 裡只是一條論壇連結，
而**受它影響的那個 gate（`R5`）通篇沒有提到它**；另一棵完全不在。

| | |
|---|---|
| `ggbruno/openwrt` | Linux **4.14.187**。作者原話：*"All the SoC drivers are implemented and tested (gpio, pci, irq, timers, etc), for the three SoCs"*，開機 log 裡 SPI/MTD 也在動。**沒做完的是 network 與 wireless**，交換器驅動要重寫 |
| `shibajee/linux-rtl8196e` | `arch/mips/boot/dts/realtek/rtl8196e.dtsi` 與 **`rtl8196e_totolink_n100re.dts`**、`CPU_RLX4181` 進 `cpu_type_enum`、`-march=rlx4181`、沿用 R3000 路徑、`wait` 支援、`rdhwr` 模擬、defconfig |

**`R5` 的六顆裡有三顆、加上 v5 才刻意延後的 irqchip、加上 DT binding，全部已經在那裡。**

**修法不是砍 `R5`。** 加一份 `docs/driver-diff.md`：
**先盲寫**（看了再寫就沒有兩份獨立實作），**再逐暫存器 diff，
不一致的地方回到矽片上判決** —— 誰對不由誰資深決定，由這台機器決定。

> **宣稱「沒有人做過」一次搜尋就倒；跟做過的人對答案，才是真的沒有人做過的事。**

順帶把兩份 Lexra toolchain patch 逐項查過，**計畫寫的全對**：
六顆核心的名字與遮罩、`TUNE_RLX` → `TUNE_MIPS3000`、
Lexra 目標關掉 `lwl/lwr/swl/swr` 的產生、條件搬移綁在 `INSN_RLXB`
（所以「18 個 `movz`/`movn` ⇒ 排除基線 `LX4180`」成立）。
**兩個要記下來的細節**：① 關掉 `lwl` 的是 gcc patch，**binutils patch 不關**，
組譯器仍然收得下那四條；② 那個旗標是 `-mno-bdsl`，它禁止的是
**load 進 branch delay slot**，**不是 load-use delay** —— 兩件事，不要混寫。

### 🔴 三、一個驗收條件跟它自己選的工具打架，而要證明它的那個檢查不可能失敗

`R7` 要求 rootfs 的 `system`/`popen` 引用數 = 0，
而 `R7f` 點名 `dnsmasq` 與 `udhcpd`。**沒有人量過廠商的數字是多少** ——
而一個「0」的目標，在不知道它是對著什麼歸零之前，是沒有意義的。

量了（55 個 ELF，正控制 `malloc`/`strcpy`/`socket` 兩邊都看得到，
負控制不存在的符號名兩邊都 0）：

| | |
|---|---:|
| 引用 `system` 或 `popen` 的 ELF | **31 / 55** |
| 帶 `#!` 的檔案 | **75** |
| `.sh` | **36** |
| 指向 busybox 的 symlink | **50** |

**`busybox` 兩個都不引用**（它用 `execv`/`execve`/`execvp`/`vfork`/`fork`/`daemon`），
所以出貨 busybox 不會殺掉這個宣稱。**但 `dnsmasq` 引用 `popen`、
`udhcpd` 引用 `system`**，而且這顆 busybox **沒有編進任何 `udhcp*` applet**。
代價是自己寫兩支小程式（`dnsfwd` ~200 行、`ifupd` ~150 行），
而它們順便變成兩個有界 parser 的 fuzz target。`iptables` 乾淨，
所以 `execve` + argv 陣列那條路可以走。

🔴 **而更糟的是那個檢查本身。** 這些 binary **沒有 section header** ——
`readelf --dyn-syms` 對全部 55 個都回傳空的，**一支建在它上面的檢查器
會在每一個檔案上報 0 個發現，而 0 正好是通過。**
這是 `hazlint` 的 `K4` 那個形狀的第三個實例，只是這次它還沒被寫出來就被抓到。
兩個獨立來源現在具名，而且必須不同種：
出貨產物走 `PT_DYNAMIC`/`DT_SYMTAB`，建置產物在 strip 之前跑 `nm --undefined-only`。

**方法自己的界限也記下來**：`.dynstr` 掃描對「沒有」可靠，
對「有」是上界（可能是訊息字串）。而且它有一個**觀察到的**假陰性 ——
`printf` 在兩邊都數到 0，因為那個名字只出現在 `fprintf`/`snprintf` 裡面，
而比對是整行的。**31 是上界，寫在 `notes/rootfs-census.md` 裡。**

### 四、一個從來沒有被算過記憶體的 KDF

設定儲存指定 scrypt，「參數由效能量測決定」。
scrypt 的全部價值是記憶體硬度：`N=16384,r=8` 要 **16 MiB**，
而 `MEM-06` 說這顆 kernel 只拿到 **26,052 kB**。
**一個未認證的 POST 就吃掉 60% 的可用 RAM**，而這台沒有 cgroup。
判準改成 anti-DoS 預算（先寫上限再量），rate limiter 明確排在 KDF 之前，
KDF 只在特權行程裡一次一個，fallback 具名為 PBKDF2-HMAC-SHA256。
**驗收帶正控制：把 rate limiter 拿掉，同一個測試必須讓機器失去回應。**

### 五、`CPU-04` 的票數變了，而值那一欄一格都沒動

指向 `RLX4181` 的現在有四票：那份洩漏的 datasheet、
**一份公開（可再散布、可以放進公開 README）的 `RTL8196E-CG` datasheet**、
以及上面那兩棵樹。指向 `RLX5281` 的最強證據是 **`rsdk-1.5.5-5281-EB-…` 這個目錄名**
—— 那是一個 toolchain 套件的名字，不是矽片的宣稱。

**規矩不變**（`PRId` 之前一律寫「Lexra 系核心，未定」），
**但預測要收窄，而且要在上機前寫進 `bench/PREDICTIONS-*`**：
🔴 **如果 `PRId` 落在 5281 段，那比落在 4181 段更值錢** ——
它會同時否證一份 Realtek 自己的公開 datasheet 與兩棵公開的 kernel 樹。
一個先寫下來、方向明確的預測，比一個「未定」有資訊量得多。

### 六、幾件小的，但其中兩件現在就該做

- **`git tag` 是空的。** 十三支帶控制的儀器、每支有測試腳本、33 個 commit，
  而**沒有任何東西自動跑它們**，也還沒有發過一次 release。
  CI 從「R2 才建」提前到現在，約一段桌面工作 ——
  README 說「每支都有正負控制」是一句無法查證的話，一個綠色的 CI 不是。
- **「Buildroot 不支援 mips1」少了半句**：upstream 移除了它是對的，
  但一個維護中的 fork 把 mips1/2/3/4 加回去了。**同一個形狀的第五次，規模小。**
- **`SPEC.md` 的 `TGT-07`/`TGT-08` 落後計畫兩版**，還帶著沒有 rescue slot 的舊佈局。已改。
- 🔴 **`PROGRESS.md` 的 `Est.` 欄有第二個擁有者**：它總計 198，
  計畫的細帳總計 252，而**沒有任何地方說一個排程問題該對哪一個問**。
  房規第 1 條就是為了防這件事。記在那張表底下，沒有偷偷挑一個。

### 這一則自己最可能錯在哪

① **那兩棵樹的完成度是我從 README、目錄清單與論壇貼文讀來的，
不是 clone 下來讀程式碼讀出來的。** 「全部實作並測過」是作者自己的說法，
而在這裡作者的說法算一票。**下一件桌面工作就是它的驗證**：
讀 `rtl8196e.dtsi` 的 `compatible` 與暫存器位址，跟 `SPEC.md` §9 對答案。
② **31 / 55 是上界**，理由在上面。
③ **`R1-gate ≈8 段`／`R2a/b/d ≈6 段` 是從總數切出來的，是猜的**，標為猜的 ——
但裁決 1 的結論不依賴那個切法，它依賴「`R3` 不需要 `R1`」，而那是逐項查證的。

---

## 2026-08-25（桌面，第二段）— `R1-gate` 開了，兩支 payload 寫完，而例外向量的位址我錯了三天

桌面日，未接觸裝置。零 flash 位元組，零電源循環。

### 這一天最重要的一件事，而它不是我計畫要做的

**一般例外向量在這顆核心上是 `0x80000080`，不是 `0x80000180`。**

`0x80000180` 是 MIPS32 的位址。這顆是 Lexra RLX，R3000 級的 CP0，佈局是
`0x80000000` UTLB refill、`0x80000080` general。三個獨立來源一致，**零個說 `0x180`**：

- 這台自己的 `trap_init @ 0x8040D07C` 建 `lui v0,0x8000` / `ori t0,v0,0x80`，
  從 `0x8040054C` 複製 128 bytes，然後 `jal 0x80406728`（flush_cache）；
- 廠商 bootcode 自己的註解：`bootcode/boot/init/irq.c:228`
  —— *"remember here we set BEV=0, and vector base is 80000000, offset 0x80"*，
  下一行就是 `memcpy((void *)(KSEG0 + 0x80), &exception_matrix, 0x80);`
- 廠商給這個核心家族的 Linux：`linux-2.6.30/arch/rlx/kernel/traps.c:691`，
  `#define RLX_TRAP_VEC_BASE 0x80000080`。

**旁證帶正控制**：這個 loader 用 `rfe`（`0x42000010`）離開例外，兩處；
`eret` 的編碼 `0x42000018` 在同一份反組譯裡 **0 次** ——
而那個 0 是有控制的，同一個 grep 找得到那兩個 `rfe`。`rfe` 是 R3000，`eret` 是 MIPS32。

**代價**：照 `0x80000180` 寫的 handler 會落在沒有人讀的 RAM 裡。payload 看起來裝好了，
第一次 fault 照樣走到 loader 的永久 hang，**花掉一次電源循環，什麼都沒學到。**
七個 committed 位置寫著這個錯的位址。

🔴 **而我第一版的更正清單把 `SPEC.md` `CPU-27` 也算進去，那是錯的** —— `CPU-27` 是留白，
它根本沒有帶任何位址。**一次更正可以無中生有出一個它正在更正的錯誤。**

### 一次 fault 值多少：一次電源循環，沒有例外

`do_reserved @ 0x80400BE8` 印兩行然後 `80400c18: 08100306 j 0x80400c18` —— **跳到自己**。
`0x08100306` 的 `imm << 2 = 0x400C18`，`(PC+4)[31:28] = 8`，目標就是這條指令自己的位址。
例外進入已經把 KU/IE 堆疊推過，`IEc = 0`，中斷打不斷它；看門狗沒上膛
（`b800311c` 的原始四位元組搜尋在 stage 1／1.5／2 裡除了兩個刻意重開機以外都沒有，
而那個 0 的控制是同一個搜尋在 stage 1.5 的暫存器表裡找得到 `b8001050` 與 `b8001008`）。

**兩條字串都不以 `\n` 結尾**（NUL 在 `0xA52B` 與 `0xA547`），
所以線上出現的是一行沒有終止的文字，然後永遠安靜。
一個以換行為單位 flush 的擷取工具會顯示成「板子安靜了，什麼都沒說」。

順帶：`SPEC.md` `CPU-26` **認錯了表**。`0x8040A5C0` 不是例外分派表，
它是 `BootStateEvent[3][8]`，TFTP／ARP 開機狀態機。
辨識帶一個普通指標表過不了的控制：廠商原始碼在 row 1 與 row 2 之間有兩處刻意的不對稱
（`setTFTP_RRQ` ↔ `errorTFTP`），而 binary 24 格全部重現。

### qemu 賺回它的位置兩次，而第一次是它抓到我寫的一個會自毀的 cell

`probe1` 的 cell 4 重現 `c-r3k.c` 的 `r3k_flush_icache_range`：
設 `Status.IsC | SwC`，然後在範圍上 byte-store 零 —— 在快取被隔離時那寫的是 tag。

**qemu 的 24Kf 不隔離**，所以那些位元組寫進了真記憶體：
受測函式第二個字 `03e00008`（`jr ra`）的 byte 0 被清成 `00e00008` = **`jr $7`**。
payload 跳到 `$t3` 裡的東西，然後停死，**guest error log 裡一行都沒有**。

**這台自己的 bootcode 從來沒用過 `IsC`，只有廠商 kernel 的原始碼用** ——
所以這件事在裝置上跟在 qemu 上一樣未確立。現在的作法是：
treatment 之後、呼叫之前先把受測函式的尾巴讀回來，
`V_CORRUPT` 成為一個第一級的判讀，意思是**「這個 treatment 寫到記憶體，而它本來應該寫 tag」**。
那不是防禦性程式碼，那是一個結果。

第二次：`probe2` 的 256 個 stub 普查、`break` 正控制、向量還原，
全部在 qemu 上跑完一遍 —— **在它們花掉一次電源循環之前**。
代價是三個常數：UART 位址、向量位址、以及 `eret` 換掉 `rfe`
（`rfe` 是 MIPS-I，MIPS32 拿掉了它，所以 R3000 的返回在 24Kf 上自己就是一條保留指令）。
每一個都在 `make show` 裡會印出 `*** NOT A DEVICE BUILD ***`，
而 `tools/test-rlxprobe.sh` 有一對案例在守那條警告本身。

### `CLK-15` 關掉，而 `SPEC.md` §17 為它寫的實驗指錯了 binary

§17 說「靜態讀 `0x80400000`–`0x80400440` 的開機路徑就能定案」。
**`Booting...` 不是 stage 2 印的** —— 這個字串在 `stage2.bin` 裡出現 0 次。
它由 **stage 1** 在 `0xBFC003A4–0xBFC003D0` 用一個沒有 THRE 輪詢的 byte 迴圈
直接寫 `0xB8002000`。所以那 350 ms **跨了一個 stage 邊界**，那個範圍永遠讀不到它。

主導項是 stage 1 在 `0xBFC001D0–0xBFC001EC` 的複製迴圈：
flash `0x0004F0–0x0056AB`，20,924 bytes，5,231 圈，一次一個字，
**迴圈的八條指令與它的來源字每一個都是從 memory-mapped SPI NOR 來的未快取讀**。

**解壓縮是用量測排除的，不是用論證**：同一組 LZMA 參數解 976,877 → 3,374,772 bytes
的 kernel 花 1.0132 / 1.0233 s（`bench/2026-08-24c/G6.timing`、`24d/G7.timing`），
依輸出位元組換算 17.1 ms、依輸入位元組換算 18.1 ms —— 兩個獨立換算一致，約 5 %。
而這一列原本猜的「DRAM init／校準」：DRAM read-window 訓練掃描 ≤32 圈，微秒等級。

**兩個沒藏的鬆端**：`Booting...` 後面那個 NUL 不是那個迴圈寫的（它在 NUL 上 `beqz` 退出），
來源未定；3.5 % 的開機間散布對固定時脈的指令執行來說太大，未解釋。

### `C-16` 關掉，而錯的是我的否證

carried-forward 那一列寫著 `check_image()`「在**前兩條指令**就讀 `gCHKKEY_HIT` 然後返回，
所以它不可能是填 RAM 的那個」。**它是在第十七條指令讀的**，前面有九個暫存器保存。
而 `0x80407E44` 就在它裡面，就是把 flash `0x060010` 搬進 `0x80500000` 的那個呼叫,
目的位址是**從 flash 標頭讀出來的** —— 整個 stage 2 裡沒有任何一個 `lui X,0x8050`。

區塊計數器就在文件說的 `0x8040DBA8`；它讀到 0 是因為後面的 rootfs 掃描
在 `0x80407FF4` 把它設成正好 0，然後才去輪詢 ESC。
**這順便解釋了一件沒人解釋過的事**：`---Escape booting by user` 在每一份 ESC 串流擷取裡都不存在，
因為 `doBooting` 收到 `a0 = 0`，走了安靜的 rescue 路徑。

### `DAY-ZERO` 與 `PROGRESS.md` 兩邊都在擁有「我下一步在桌上做什麼」

房規第 1 條。分界線第 7 項自己已經畫過了：`hazlint` 是 `DAY-ZERO` 的（**儀器**），
它保護的 hazard 判決是 `R1b` 的（**讀數**）。第 8 項從來沒照這條線切，
所以它的 DoD 就是 `R1` 的 DoD，而 `DAY-ZERO` 要等 `R5` 在跑才可能關。
第 6 項（容器）擋的是 `R2`／`R3`，從來沒擋過 `R1`。

**這個重整自帶一個檢查，而檢查當天就跑了**：被重新指派的東西必須當天出現在
新擁有者的清單裡，一個字都不能少。容器整段連同 2026-08-24 量到的阻塞事實
與三條未決路線進了 `plan/router-rebuild-plan.md` §6-R2 的前置；
`R1d`／`R1e` 的 payload 進了 `PROGRESS.md` 的 § Step list 成為 `R1g-1`／`R1g-2`；
`R1a`／`R1b` 交給 `R1-pub`；`R1c`／`R1f` 離開 item 8 回到它們自己的 gate。

### `v0.0` 的 CI，以及它第一次被指向真實輸入就抓到東西

一個綠色的徽章是一句「0 個失敗」，而**一個安靜縮水一半的套件也是 0 個失敗**。
量到的：`tools/test-hazlint.sh` 在乾淨 runner 上印 **8 條 skip 行，代表 25 個案例**；
`test-rlxprobe.sh` 印 **1 條，代表全部**；`test-opcount.sh` 的 skip 什麼計數都沒加，
它自己的結尾寫著「14 passed, 0 failed」而且是綠的。

`tools/ci-census.py` 檢的是算術：`ok + FAIL + Σ covers == 這個套件的 bench 總數`。
它第一次被指向真實擷取就讀到 **20 + 23 = 43 對 45** —— `test-rlxprobe.sh` 的 `A2`
有兩個案例躲在 `if [ -s … ]` 裡，**既沒有 FAIL 也沒有 skip 行就消失了**。
任何以 skip **行數**為單位的檢查都看不到它。

**88 個案例在 runner 上跑，118 個不跑，而 118 個每一個都印在 build 頁面上。**
不裝 `gcc-mips-linux-gnu` 是刻意的：裝了之後 `test-rlxprobe` 會**建得起來**，
然後 `hazlint` 因為沒有 `stage2.bin` 這個母體控制而拒絕報告 —— **而那個拒絕是對的**。

### 這一則自己最可能錯在哪

① **`0x80000080` 是讀出來的，不是量出來的。** 三個來源一致、`eret`/`rfe` 的旁證帶正控制，
但沒有一個是在這台上跑出來的。`RUNSHEET.md` § Session B4 的 `H0a`（`DW 80000080 32`）
是把它變成 **量** 的那一格，唯讀、零風險、零成本，而且它排在整場 session 的第一個。
**如果那 32 個字不是 `notes/cache-model.md` 列的那些，`probe2` 就不准跑。**

② **「hang 是永久的」也是讀出來的。** 看門狗沒上膛是靜態掃描的結論，
而反駁稽核指出我拿來當旁證的「提示字元撐過十八次 session」是**誤引**：
那個「十八」是十八份 console 擷取，出處在講另一件事，而 `bench/` 裡最長的一份擷取是 180.079 s。
零成本的驗證方式：**如果哪天真的 fault 了，先等 60 秒再碰電源。**

③ **`probe1` 的 cell 1 可能因為驅動程式碼把受測行踢出快取而假陽性。** 這無法在桌上排除。
緩解是一格用兩個相距 7 KiB 的受測函式（7 KiB 只有 1 KiB 的快取大小整除得了），
而真正的處置是寫在 gate 的否證條件裡：cell 1 若讀到 FRESH，另外五格什麼都沒證明。

④ **`probe2` 的 `ZERO` 狀態同時是兩件事**：*有實作而且是零* 與 *沒實作而匯流排回零*。
payload 裡沒有任何東西能分開它們，所以它被寫成它自己的一個狀態，而不是折進另外兩個。

⑤ **CI 的「118 個沒跑」是這個 repo 現在最大的一塊未覆蓋面，而它有出路**：
給 `hazlint` 第二個 runner 滿足得了的母體控制。條件寫在 `PROGRESS.md` 的
「Next after this」④，而且它自帶否證：那個合成 fixture 必須在同形狀的語料上
重現 K4 自己的數字，否則它不是母體控制，它是一個單元測試。
## 2026-08-25（桌面，第三段）— B4 這張表在上機前被審了一次，而它有三格各自就能花掉那一次電源循環

桌面日，未接觸裝置。零 flash 位元組，零電源循環。**上機延到 2026-08-26。**

這一段沒有新的裝置知識。它做的是一件更難寫進履歷的事：**把一張已經寫好、已經
說「每個期望值都寫在前面」的表，當成別人寫的東西來讀一遍。** 結果是七個編輯、
三個新工具檢查、和兩個「照紙上做就會發生」的失敗。

### 一、`H1a` 會把 payload 上傳到它自己的結果區

`H1a` 那一格寫的是「`rescue` + `put`，**exactly as `§G` 的 `G2`/`G4` do it**」。
翻回去看 `G2`：`--load-addr 0x80A00000`。`G4`：`--expect-load 80A00000`。
**那是 `probe1` 的 `RESULT_BASE`。** 走 `0x80500000` 的是 `G5`，不是 G2/G4。

照字面做的話：image 落在 `0x80A00000`，`J 80500000` 跳進 loader 已經 staged 好的
vendor kernel（`G1` 量過 964 KiB 早就在那裡）—— **loader 沒了、Linux 吃掉 32 MiB
DRAM，`H1c`/`H2g` 的 RAM 通道跟著一起沒**。

**而工具結構上抓不到它**：`--expect-load` 是拿 transcript 跟自己比對，
`put` 跟 `get` 又都服務同一個全域 `[0x8040D3A8]`——`G4` 那一格自己就寫了這句話。

`H1a` 和 `H2a` 是全 B4 唯一兩格**完全沒有字面命令**的格子，而 B4 的開場白引用的
正是 rule 4：*命令從這裡打或從工具打，絕不手抄*。一個檔案可以在同一頁上引用一條
規則並且違反它。

### 二、`make` 不會因為旋鈕變了就重建，而 `make show` 會替它圓謊

```
$ make -C tools/rlxprobe P=probe2 payload RESULT_BASE=0x80A01000
make: Nothing to be done for 'payload'.
```

而這棵樹裡的 `build/probe2/probe2.bin`（6640 bytes, `bda8bb96…`）是
`RESULT_BASE=0x80A00000` 的建置——`lui *,0x80a0` ×1、`lui *,0xa0a0` ×2，
`0x80a1`/`0xa0a1` 各 0。**量**。

所以 `H2` 會上傳一顆把 537 個字 poison 到 `0x80A00000` 的 probe2，蓋掉 `probe1`
的整個結果區，而 `H2g` 讀 `0x80A01000` 讀到垃圾——**UART 那一側看起來完全正常**。
一個 build system 製造出來的雙通道不一致，要在現場、板子通電的狀態下 debug。

**根因**：沒有任何一個 object 依賴任何帶 `-D` 的東西。每個旋鈕都只透過 `-D` 進
編譯器。**`tools/test-rlxprobe.sh` 62 格從來看不到它，因為每一格都建在全新的
`BUILD=` 目錄裡**——一個測試套件可以用一個好習慣把它要測的 bug 藏起來。

修的是根因不是症狀：加一個 parse-time 的 flags stamp，每個 object 依賴它。
然後補 `R3`–`R6` 四格，並且**驗證它們會失敗**：
拿掉 `.flags` 依賴 → `R3`/`R4` 兩格紅（「knob change rebuilds」expected no got yes）；
把 `RB_WORDS_probe1` 改成 88 → `R5` 紅、`R6` 不動。**兩個變異各自只打到該打的格。**

### 三、B4 沒有寫任何一行 capture 指令，而它有三個 reset 邊界

122 行的 `§ Session B4` 裡：`console-capture` **0** 次、`--esc` **0** 次、
`--esc-after` **0** 次、`--seconds` **0** 次、flush 格 **0** 個、`A0` **0** 個。

而 `H1b`、`H2a`、`H3a` 的命令每一個都會讓板子重開。`rlx_reset` 是
TEMT drain → 16,777,216 次三指令迴圈 → `sw $0,0(WDTCNR)`，**報告印完不到一秒**
就 reset；ESC 窗約 4.9 s。**沒有人的手能在那之間起一個 capture。**

`D1` 那一格早就有正確的形狀（`--send 'J BFC00000' --esc-after 20 --seconds 45`），
而兩次歷史損失有兩次是 ESC 窗。修法早就有了，**只是住在 150 行以外**。

### 四、`H0a` 的期望值指向一個沒有那個值的檔案

`H0a` 寫「the 32 words **`notes/cache-model.md` lists**」。那個檔案**一個十六進位
字都沒列**。全 repo grep 那 11 個字，只有 `RUNSHEET.md:626` 一行；另外 21 個字
**沒有任何檔案預測過**。而 `PROGRESS.md` 和 `LOG.md` 把同一個死指標各抄了一次。

這正是三天前那條寫給自己的話又發生一次：**一次更正可以無中生有出一個它正在更正
的錯誤。** 差別是這次它落在「決定 `probe2` 准不准跑」的那一格上，而三分之二
的讀數沒有通過／不通過的標準。

補法不是把 11 個字再抄一遍。是：

- 從 `stage2.bin` 偏移 `0x54C` 讀出全部 32 個字，**11 個字零不符**，記進 owner
  檔（`notes/cache-model.md`），連解碼一起；
- 加一格 `H0a2` = `DW 8040054C 32` —— 讀那份拷貝的**來源**，必須跟 `H0a` 32 個字
  全等。**一個不需要任何預測值的雙讀恆等式**，而且自帶正控制：`DW` 壞掉或位址被
  改寫，兩次讀不會一致。它覆蓋的正是那 21 個沒人預測過的字。

順帶知道了 word 12–31 是什麼：`trap_init` 複製 128 bytes，派送碼只佔 44，
所以 **word 13（`401A6000` = `mfc0 k0,c0_status`）是 loader IRQ handler 的第一條
指令**被順手拖進來的死拷貝（`0x80400580 - 0x8040054C = 0x34`）。
一個把「前 11 個是 live code」讀成「其餘應該是 0」的操作者，會為了非零的 word 13
放棄整個 `H2` 半場。

**還有一個免費的東西**：這 11 個字自己就是一次 hazard 讀數。`mfc0` 後面兩個
`nop`、`lw` 後面一個 `nop`——那是廠商對這顆核心 hazard 深度的信念，寫在
**已安裝、會被執行**的那份拷貝裡，不是寫在 SDK header 裡。`hazlint` 的規則因此
多了一個來自執行路徑的旁證。

### 五、同一個缺陷類別的第二個實例，落在 stop-loss 那一格

`H2b` 寫「Traced through ten writes to Status, the value at the prompt should be
`1000FC01`」。全 repo grep `1000FC01`：**一個 hit，就是那一行**。
而 `SPEC.md` `CPU-27` 是**留白**，`docs/loader-command-semantics.md` §9 明講
`Status.BEV` 在 prompt 時**沒被追過**。

一份 committed 的 runsheet 宣稱做過一個十處的追蹤，而兩個 owner 檔案說它沒發生。
撤掉，改成「未預測，只有 bit 22 承重」。

### 六、兩個宣稱比它們量的多的儀器

- **`H2f` 的 `restore.mismatch`**：probe2 對**兩個** vector 各寫 22 字、各存還原
  32 字；檢查讀回**64 個裡的 8 個**，而且**完全沒讀 UTLB vector**——那正是
  `notes/cache-model.md` 記載 loader 從沒填過、`H0c` 說 faulting kuseg load 會去
  的那一個。而且它只走 `field()`，**沒有 `rb_put`**：在一支「一個輸出通道就是
  P9-12 等著再發生一次」的 payload 裡，唯獨這一格只有一個通道。
  補 `H2h`：reset 之後重讀 `DW 80000080 32` + `DW 80000000 8` 跟 `H0a`/`H0c` 比對
  ——零風險，而且基準本來就在取。
- **`H2f` 的停機指令是錯的**：`RESET ?= 1`，`start.S` 在 `main` 一 return 就
  `jal rlx_reset`，loader 根本沒機會在 reset 之前拿回控制權，`trap_init` 早就重跑
  過了。照紙上寫的，操作者會為了一個不存在的理由放棄三格 ride-along。
- **`DW 80A00000 88`**：block 是 `8 + 16×8 + 1 = 137` 字。88 字 = header + 10 行，
  少掉 cell 6 兩格、`XCT0` 那格、和 word 136 的 **seal**——而 seal 正是「跑完
  vs 截斷」的判別字。`Makefile` 的 `show` 印的也是同一個死的 88，**而且對
  probe2 也印 88，它的 block 是 537**。

### 七、要推之前先看了一眼 CI 的數字

`.github/workflows/ci.yml` 三個地方寫 `test-rlxprobe` 的 bench 總數是 `45`，
一個地方預測 `NOT RUN IN THIS JOB: 101 case(s)`。**量**：今天是 **66** 和 **122**，
而 122 是拿 `tools/ci-census.py` 跑一次模擬 runner 印出來的，不是算出來的。

那個 header 從 45 格長到 62 再長到 66，中間沒有人重新量過。而 `v0.0` 的 tag 就在
那個 commit 上，**那是外部讀者唯一會打開的一個 commit**。
這個 repo 的整個論點是「一個沒人能否證的 badge 不是證據」——那就不能推一個
第一次 build 就會打自己臉的 workflow 檔。

### 八、`R1g-3` 的完成定義其實沒滿足

`R1g-3` 的 DoD 是「`check-predictions.py` 在第一個 capture 之前寫好的 block 上
通過，像 seating 2 的 18 個 block 那樣」。`bench/2026-08-26/` 不存在，B4 的
`PREDICTIONS-*.md` 一份都沒有，而 B4 除了 `H3b` 之外沒有指定任何 capture prefix。
**表寫完了不等於 DoD 滿足了。**

`bench/2026-08-26/PREDICTIONS-b4-block0.md` 寫掉，九格 `A-catch`/`A0`/`H0a`/
`H0a2`/`H0a3`/`H0b`/`H0c`/`H0d-a`/`H0d-b`，四個控制項全過，九格都正確回報
「no capture」。blocks 1–3 在現場寫，因為每一個都以前一個的讀數為條件——
**替一個跑不了的 cell 寫 block，是讓它為錯的理由失敗。**

### 這一段沒有做的事

- **沒有量任何裝置上的東西。** 上面每一個數字不是讀出來的、就是在這台工作站上
  跑出來的。
- **沒有動 `probe1.c` / `probe2.c` 一個字。** 兩支 payload 的邏輯沒有被審——
  審的是它們周圍的東西：runsheet、Makefile、CI 的數字。qemu 說控制流對，
  而 qemu 對 load delay slot 是有互鎖的。
- `CPU-25` 這一場還是量不到（`GEOM=0`）。那是個選擇：`GEOM=1` 在 `IsC` 沒實作時
  會寫 1 MiB 真記憶體，而這張表沒有那個視窗的前後讀。現在至少寫下來了。
- 三個新加的格（`H0a2`/`H0a3`/`H0d`）**沒有一個在裝置上跑過**。它們是零風險的
  `DW`，但零風險不等於已驗證。

### 收尾

`spec-check.py` 10/10、`test-file-modes.sh`、`test-rlxprobe.sh` **66/66**、
`test-hazlint.sh` 56/56、`ci-census --self-test` 12/12。
`SPEC.md` `CPU-33` 補上那 32 個字的來處。

### 這一段之後又動了四個地方，而它們都不在 `B4` 裡

審完 B4 之後還剩四件，四件都做了。排序的依據是「它會不會讓下一個人（包括明天的我）
拿著錯的東西行動」，不是大小。

**一、廢掉的 `0x8040A5C0` 還在兩個地方讀起來像是現在式。**
`docs/loader-command-semantics.md:956` 寫「above a 16-entry dispatch table at
`0x8040A5C0`」，而**同一份文件的 §10 已經推翻了它**；`PROGRESS.md` 的 `R1g-0`
也還寫著「那張表有 16 格而且不必共用 tail」。grep 的人會先碰到錯的那一個。
兩處都標上推翻，**`R1g-0` 那句保留原文不改寫** —— 把一個寫錯的風險評估改成看起來
很準的樣子，是另一種不誠實。

**二、`CLAUDE.md` 的 usbipd 句子跟它自己的 log 矛盾。**
§ Environment 寫附著「drops when the distro goes idle」。`LOG.md:2287` 量到的是相反：
**WSL uptime 全程連續**，離開的是 **CP2102**，在**純空閒 7 分 24 秒**之後掉出
Windows USB 匯流排，根因**未定**。差別不是措辭：若信了原本那句，明天在台上會拿
`wsl -- sleep 36000` 當作修法，**而它修不到這個故障**。重寫，並且把「keep-alive 是
給 attach 用的、不是這個的修法」寫進去。

**三、決定 push 會不會漏東西的那道 guard，在 push 發生的那台機器上跑不完。**
`tools/test-gitignore.sh` 在 Git Bash 上 `exit 1`：MSYS 建不了 symlink，`ln -s` 失敗，
`set -o errexit` 在印出 `RESULT` 之前就中止。在 WSL 是 15/15。
改成跟其他套件一樣的 skip 行（`tools/ci-expected.tsv` 帶 label），並且**兩種形狀都拿
`ci-census` 驗過**：Linux 15/15 総數還是 122，MSYS 14+1 skip 也綠。順手修掉 header 的
「13 cases」→ 15 和 `.gitignore` 註解的「case 14」→ 15。

**四、`CPU-25` 的事前預測，而它是四件裡唯一我本來可能不做的。**
第二棵 RTL8196E 樹的 `rtl8196e.dtsi` 帶 I 16 KiB／D 8 KiB／line 16／16 和
`compatible = "lexra,rlx4181"`。**我自己抓了一次來看**，而不是拿 agent 回報的數字寫進
一個帶 provenance 標記的表——把沒驗證過的第三方數字標成「讀」，比不記還糟。

記下去的同時把它的弱點一起記：同一份檔的 `soc` 寫 `ranges = <0 0xB8000000 0x1000>`
（4 KiB 窗）却把 `interrupt-controller@B8003000` 給 `reg = <0x0 0x100>`，
`serial@B8002000` 跟 `serial@B8002100` 帶**同一個** `reg`，而且 `dtc` 在
`clocks = <&cpu_clk/2>` 直接拒絕解析。**所以它只能當 driver 形狀的先前技術和這五個
整數用，不能當任何位址的來源。** `tlb-entries = 32` **不記**：`CPU-08` 已經是
量／量，把第三方的猜測放在一個量測旁邊，正是兩來源規則要防的事。

而這個預測**下一場不會被測到**：`B4` 是 `GEOM=0`。寫在這裡的意義就是這句話——
一個寫在量測前面的數字是否證條件，寫在後面的同一個數字是描述。

---

## 2026-08-25（桌面，第四段）— 兩支 payload 第一次被讀，而 `H2` 從這場退出來

第三段審的是**圍著** payload 的東西——runsheet、`Makefile`、CI 數字。這一段讀的是
裡面。理由只有一條不對稱：**`qemu-system-mips` 對 load delay slot 有互鎖、實作
MIPS32 的 CP0 語意、而且 I-cache 是相干的。它的簽核正好是這顆核心會拒絕的那一類**
——upstream 的 `P9-12` 就是被自己的模擬器簽核之後、隔天在這片矽上倒掉的。

六個獨立 lens，每個發現再送給一個「工作是駁倒它」的讀者。

### 先記工具自己壞掉的地方，因為它決定了這份東西能主張多少

**47 個發現產出、21 個送進駁倒階段（10 個被駁倒）、26 個一個駁倒者都沒見到**——
驗證階段撞上 session limit 死掉，而**它死在最重要的兩個 lens 上：ISA/hazard 六個
全滅，fault-cost 前六個全滅**。

所以這份稽核的三分之二是**主張不是發現**，這句話要寫在前面而不是註腳裡。會改變
上機決定的那幾條我自己動手對著 emitted binary 重驗過，那些標 *量*；其餘標 `[1-src]`
留在 `docs/rlxprobe-audit-2026-08-25.md` 裡。

### 一、`probe2` 設計成「看得見的失敗」，而它量到是完全的靜默

`probe2.c` 和 `H2c` 都承諾：handler 沒裝上去會印 `Undefined Exception happen.`，
**「an unambiguous observation」**。反組譯 `build/p2a/probe2/probe2.elf`：

```
80500f40:  1480fffb   bnez  a0,80500f30      # rlx_puts 的迴圈出口
80500f48:  8fbf0014   lw    ra,20(sp)        # 之後沒有任何指令寫 $a0
80501328:  24441884   addiu a0,v0,6276       # 最後一個寫 $a0 的（jal 的延遲槽）
80501364:  0c1400b2   jal   805002c8 <rlx_do_break>
805002c8:  0000000d   break                  # 沒有 SAFE_A0
```

`rlx_puts` 在字串的 NUL 上退出迴圈，所以**它永遠帶著 `$a0 = 0` 返回**。失敗分支上
`do_reserved` 做 `move v0,a0`（v0 = 0）然後 `lw a3,148(v0)`——從 `0x00000094` 載入，
kuseg，TLB-mapped，而 loader 一條 TLB 指令都沒執行過。**那條 `lw` 在 `0x80400C00`，
第一個 `prom_printf` 在 `0x80400C04`。兩行都印不出來。**

`cache.S` 花三十行把這個危害立起來，並且對三個常式套了 macro。**全樹唯一一條設計
上保證會 fault 的指令，是唯一一條沒套的**，而 `test-rlxprobe.sh` 的 `S1` 寫成「every
**CP0 instruction** that could fault」，把 `break` 劃出去了。

### 二、`install_handler` 寫進去之後沒有人讀回來

44 個字透過 KSEG1 進向量頁，flush，`return words`，**下一個碰到向量的是 `break`**。
「store 沒落地」和「flush 把它吃掉」塌成同一個靜默。而 `FLUSH_ISC=1` 那條路的 flush
是跨**兩個**向量的 64 個 `sb $0`——`cache.S:184-186` 自己寫了這個危險，還加了一句
「never at a range it does not own」，而 `probe2` 指的正是一段它不擁有的範圍。

### 三、每一個 CP0 讀取都假設 `mfc0` 會寫 rt，而那正是這場 census 要測的

```
80500218 <rlx_call0>:      80500224: nop      ← 延遲槽是空的，$v0 從沒被寫過
805002d4 <rlx_count_delta>: 805002d4: mfc0 t0,$9   ← $8 沒初始化
                            805002f0: mfc0 t7,$9   ← $15 全 payload 沒有指令寫過
```

handler 走 `EPC+4` 且不碰目的暫存器，所以 **trap 分支上**：census 的 `v` 欄位帶的是
迴圈裡的 `zeros` 計數器（一個穩定遞增的小整數，看起來像一族暫存器在回答），
`count.delta` 是 `$t7 − 0xA0500150`。而 `H2e` 事先寫的期望值是 `00000000`，所以一個
大的 residue 數會被讀成**它的否證**，把 `F50b` 答反、把 `R5-0` 的計時器驅動降級。

**弱腿跟強腿要分開講**：「`mfc0` 退休但不寫 rt」是三種可能行為裡最不可能的一種。
**但 trap 那條腿不需要這個假設**——trap 時目的暫存器確定沒被寫，而 `probe2` 對
trapped row 照樣記 `v`。

### 四、我自己那條最大的發現被駁倒了，而駁倒它的是這個 repo 自己

我追出「prompt 下計時器中斷是活的、每 10 ms 一次、走 `0x80000080` 派送，而 `probe2`
正要覆蓋它」——四層全部立得住，三層是量的（`REG-01` `GIMR=0x00008100`、
`REG-09`/`REG-10`、`REG-25` 2,080 秒基線）。然後去找能駁倒它的東西，找到了：
**`docs/loader-command-semantics.md:1054`——`J <addr>` 進 payload 前清 `IE` 和
`GIMR0`**，每一條路徑，不只 `J BFC00000` 那個特例。upstream 為此有
`mkramboot.py --irq-restore`。

**不成立，但兩個殘留是真的**：`probe2` 手上有 Status 那個字、檢查了 bit 22、忽略
bit 0；而 `uart.S` §`rlx_reset` 說 loader 那個 idiom「masks no interrupts」，跟同一個
位址在 `loader-command-semantics.md:782` 的紀錄**相反**。兩者有一個是錯的。

### 五、決定：`H2` 退出這場，`R1g-4` 拆成 `4a`/`4b`

不是「修還是不修」，是**要不要跑最後那一格**。47 個發現不是均勻分佈的：`H0` 根本
不跑 payload，`H1` 上的那一個（`CELLS[]` 把 cell 4 排第三）**失敗會印**，而 `H2` 上
的失敗量到是靜默。

**代價：多一顆計畫內的電源循環。** 這句話寫在這裡而不是被稀釋掉。

**買到的不只是安全**：`H0b` 量 `exception_handlers[9]`——那是第一條發現底下**唯一
沒被驗證過的一環**；`H0c` 量 kuseg fault 實際會落到什麼上；`H0a3` 量向量頁未快取
視圖一不一致；而 **`H1` 讓 `p2a`/`p2b` 塌成一顆 binary**，把「兩個 image、差四個
字元、兩個通道都分不出來」整個消掉，而不是拿一個 `field()` 糊上去。**修法會對著量
到的值寫，而不是對著讀到的值。**

這個計畫自己檢查自己這一點，是它比「今晚趕著改 24 行」好的地方——而不是相反。

### 六、順手：兩個一直在那裡、只是沒走到該去的檔案的東西

**`CPU-27` 不是空白，是單一來源。** `docs/loader-phy-and-switch.md` §2 的中斷四層表
從 2026-08-23 起就寫著 `BEV` cleared、設在 `0x80406694`、never re-masked，而 `SPEC.md`
和 gate 前提條件兩邊都寫「沒追過」。**一個事實只有一個擁有者，而它從來沒走到兩個
依賴它的檔案**——跟 `43ec0e0` 同一個缺陷類。它是 *讀* 不是 *量*：tick 前進只證明中
斷**有被服務**，`BEV=1` 走 ROM 向量會給一模一樣的讀數。

**sheet 用 loader 的大寫十六進位寫，payload 印小寫。** `report.c:18` 是
`"0123456789abcdef"`，所以 `rb=80A00000` 和 `pc=` 的 `A05` 是**正確執行時永遠不會出現
的字串**——而 `rb=` 正是 stale-build 檢查。

### 七、`--esc-after 60`：數字不改，而推導的殘差才是值錢的東西

算出來的預算是 **6.02 s**，其中 `LDR-15` 的 ESC 視窗 4.886 s 佔 **81 %**，而要拿來
校準的報告長度（1,543 bytes / 0.4018 s）佔 **6.7 %**。**校準它等於校準整張表裡最小的
那一項**，而第二大項（`rlx_reset` 的延遲迴圈）踩在一個從沒量過的 CPU 時脈上——
`CLK-01` 的 400 MHz 是**開機 banner 印出來的字串**。

殘差是免費的量測：`Δ = t(重置後第一個 byte) − t(報告最後一個 byte) = 延遲迴圈 +
[4.5, 4.6] ms`，預測 **130.4 ms**（400 MHz × 3 cycles）對 **256.2 ms**（200 MHz），而
`CLK-15` 用同一個 `.timing` 機制在 350 ms 上拿到 3.5 % 全距。**它量的是 `f/CPI` 不是
`f`**，所以 256 ms 否證的是「400 MHz **且** 3 cycles」這個組合——那仍然是結果，而
`CLK-03` 到今天為止沒有被指派任何實驗。

## 2026-08-25（上機）— `R1g-4a`：負控制成立，而 `Status.IsC` 在這顆上是壞的那一條

一次電源循環，`bench/2026-08-25/`，**26 份擷取、10 個預測區塊、26/26 都寫在自己的擷取
之前**（最小邊際 +7.9 s），**零 flash 位元組**。送出去的每一道命令從擷取自己的
metadata 逐一列出，不是從 log 猜的：**22 個 `DW` 讀、兩個 `J`、兩個 `EW`，而兩個 `EW`
都是 `B800311C`（看門狗暫存器）**。一支掃 `FLW`／`AUTOBURN 1`／`EB`／落在 flash 範圍的
`EW` 的掃描器對 26 份全部回 0，而它對一行植入的 `FLW` 會觸發。

`R1d` 關了。`R1e` 沒有，而那是決定不是缺口。

### 一、通電前抓到三件事，其中兩件本來會安靜地毀掉一格

**① 日期對不上。** 預測檔寫在 `bench/2026-08-26/`，實際上機是 08-25。舊檔**沒動也
沒刪**（mtime 06:09 才是真正的預先登錄時間戳），開 `bench/2026-08-25/` 與新的 block 0，
兩檔 `diff` 六個 hunk，**其中恰好一個落在預測裡**，而那一個在檔案裡當著讀者的面改掉，
理由寫在旁邊。「只改了路徑」這句話本身會是假的，所以沒有寫。

**② 🔴 `console-capture.py` 在樹上是 `1.3`，而七個 committed 位置還寫 1.2。**
`4f5331e` 在 02:41 把 `TOOL_VERSION` 改掉，預測檔 06:09 才寫，**改完之後還預測了舊版本
號**。這會讓 `A-catch` 的 metadata 預測失敗在儀器的版本字串上 —— 該是訊號的欄位變成
雜訊。改了 `RUNSHEET.md` 兩處與新 block；封存的 08-26 檔不動。

**③ 🔴 `H3b` 那一列寫 `DW B8003250 8`，而那個位址在整個 repo 裡只出現在那一列。**
其他每一處 —— `SPEC.md` 三列、`docs/loader-phy-and-switch.md` §7、`bench/README.md`、
`docs/loader-command-semantics.md`、**這份 sheet 自己的 `E10` 那一列**、以及 08-24 的八份
擷取 —— 都是 `0xBB804128`。**而且它不會報錯**：`0xB8003250` 落在 SoC 暫存器視窗，`DW`
會回八個看起來很正常的字，四次換線會量到四份別的東西。

三件都是同一個缺陷類：**一個事實被手抄到第二個地方，然後在那裡走樣**。

### 二、`H0`：把一份文件變成量測

`H0a` 的 32 個字與 06:09 事先登錄的清單**逐字相同**。`H0a2`（`DW 8040054C 32`）與它
**全 32 個字相同**，所以 `trap_init` 的 128 byte 複製完整落地 —— 包含這個 repo 在今天
以前沒有任何人預測過的第 11–31 個字。`H0a3`（`DW A0000080 32`）也相同，而且印出來的第一個
位址是 `A0000080`，**所以讀到的不是陳舊的 D-cache line**。

`H0b`：`[0]=80400580`、`[23]=804007C0`、**其餘三十筆 `80400BE8`**。🔴 其中
**`exception_handlers[9] == 0x80400BE8`** 正是稽核 § Must-fix 1 底下唯一還沒被驗證的承重
連結 —— `rlx_do_break` 少了 `SAFE_A0` 維持滿級嚴重度，`H2` 延後是對的。

`H0c` word 0 = `5A5AA5A5`，opcode `010110` = 22 = `BLEZL`，**不是 `j`(2) 也不是
`jal`(3)** —— `cache.S` 的免磚論證由「論證」變成「量測」。**這一格是准許 `probe1` 跑的
那一格。**

🆕 `H0a2` 順手帶回一件關於 `LDR-07` 的新事實：**`DW` 不會把起始位址向下對齊**。這是
本專案第一次餵它非 16-byte 對齊的位址，block 0 事先把它寫成待決問題，答案是不會。

### 三、`probe1`：三件事同時被判掉

十三列全到，`seq=0000000d`，UART 報告 **1543 bytes**（事前算的
`32 + 144 + 13×104 + 15`，一個位元組不差），`H1c` **1671 bytes / 140 words**，兩條通道
**104/104 逐字一致**（附一個位移一個字的負控制）。

**① 負控制成立，而且與 qemu 相反。** cell 1（不施加處置、cached store）兩個相距
7 KiB 的 victim 都是 `01` STALE：執行舊常數，而記憶體已經是新的。qemu 在同一格回
FRESH（TCG 會作廢 translation block），而 §H1 在上機前就寫下：**長得像 qemu 那一次的
裝置執行，才是否證這個實驗的那一次。**

**② D-cache 是 write-through。** cell 1 與 cell 5 的 `ma` 都是 `240222b2`，兩格只差
cached／uncached store 一個變數。**這取消了一個污染**：稽核 §5 說在 write-back 情況下
cell 2 對 cell 3 量到的會是 D-flush 而不是 I-invalidate，而那句錯話會一路走進 `R5b` 的
MTD 驅動當成 flush 配方。**讓它可判的是稽核寫進 sheet 的那張表，不是它寫進 binary 的
verdict。**

**③ `CCTL 0x002` 單獨就夠。** cell 2、3、6 六個 victim 全 FRESH。加上 ②，廠商 bootcode
的 `0x200` 然後 `0x002` 是**多餘而不是錯** —— 而這句措辭是 `R1g-1` 在 payload 還沒寫之前
就登錄好的。**四個下游決策的第一個答了。**

**④ 🔴 `Status.IsC` 不隔離，隔離期間的 store 進 DRAM。** cell 4 兩個 victim 都是
`07` CORRUPT：`240222b2 → 000222b2`、guard `03e00008 → 00e00008`，**每個字的最高位元組
被清零、stride 4**，正是 `rlx_isc_inv` 那條 `sb $0, 0($4)` 走過的樣子。qemu 前一天找到
同一個失效，而它產生的 `V_CORRUPT` guard 是 payload 沒有跳進荒野的原因。`CPU-35` 關閉；
`GEOM=0` 回頭被證成。⚠️ **量到的是行為不是位元** —— `Status` 那兩個位元有沒有被實作要
讀回 `Status`，那是 `probe2`。

`PROGRESS.md` 的 stop-loss 預期的是相反的情況（「`mtc0 $t,$20` 出錯 → `IsC` 變成唯一
路徑」）。**現實是 `CCTL` 能用，`IsC` 是壞的那一條。**

### 四、兩個免費的量測，都不在計畫裡

**`CLK-03` 第一個實驗約束。** `--esc-after` 把報告與重置後開機放進同一份擷取，所以
`Δ = 123.7 ms` 只要讀檔就有。三個事前登錄的候選：**130.4 ms（400 MHz 且 3 cycles）存活**
（低 5.1 %，在本儀器已證實的散布內），172.3 ms 否證（1.39 倍），256.2 ms 否證（2.07 倍）。
`f/CPI = 1.408 × 10⁸`。⚠️ 它量的是 `f/CPI` 不是 `f`，所以存活的是**組合**。

**`CLK-08b` 關閉，而且答案是比例不是固定。** `H3c` 把心跳從 20.35 ms 換成 2.118 ms，
量到 1118.133 / 557.583 ms（比值 2.0053；ESC 回音 528:262 = 2.0153，完全不用時間戳）。
**固定延遲模型無解** —— `L+c` 由 `D4` 得 56.243、由 `D4c` 得 29.605。比例模型有唯一解
`c = 2.967 ms`、`f_wdt = 14.9650 MHz`。🔴 **`c` 有硬的物理下界**：它跨越 loader 的提示
字元，而提示字元必須先被送出去，兩份擷取裡都是 10 bytes = 2.604 ms。看起來漂亮的
**15.000 MHz** 需要 `c` = 0.32 與 1.64 ms 兩個矛盾值，**兩個都小於提示字元自己的傳輸
時間 —— 排除**。被否證的是 `f_timer/14 = 14.2861 MHz`，差 4.75 %，而計時器基頻本身量到
±7 ppm。**14.965 MHz 與 200.0049 MHz 之間的整數關係未定**，四個候選沒有一個在 1 % 內。

### 五、`NET-13` 關掉了，而關掉它的圖不是原本設計的那一張

原本的實驗是「換孔時把孔別寫進檔名」，而**孔別**指的是**位置**（從 WAN 端數起），
操作者看到的是**絲印**（WAN／LAN1–4）。兩者只有在機殼按升序印刷時才能換算，而那個順序
這個 repo 從來沒有記錄過 —— **這個歧義沒有被說出來，而它正是 `NET-13` 兩次翻車的同一
個東西**。檔名改成 `pos<N>-<絲印>` 兩者都帶。

四個量到的點，每一點的標籤都由操作者在它自己的擷取**之前**口頭指定：
**WAN→0、LAN1→1、LAN2→2、LAN3→3**，LAN4→4 由雙射消去（操作者放棄第五次移線，此格
標 **推**）。五次讀取每次都恰好一埠 bit 4 起來。🔴 **`LAN1 → port 1`** 是重點：port 1
正是 `PORT1` 的 patch 清單跳過的那一埠，而它背後是哪個孔在今天以前從沒在標籤先寫好的
情況下被指名過。**位置圖仍然未定，而它現在缺的是看一眼機殼，不是一次暫存器讀取。**

🆕 **兩個沒人列過的 `PSRP` 發現，第一個會走進驅動**：① **速度與雙工欄位不受
`LinkUp` 把關** —— 拔掉的埠仍然報告 100M 全雙工（`…E9`），而對照在**單一擷取內部**：
四個協商過的埠是 `E9`，唯一沒協商過的 `PSRP4` 是 `E0`。② **bit 8 的讀取即清，第一次在
link 往「下」掉的事件上量到**，而且孔是空的 —— 先前三次全是往上收斂，那種情況下兩個
模型不可分辨。兩件事之後各自又通過兩次獨立測試：後面兩格各**事先推導**了五個埠字裡的
三個，六個推導字全中。

### 六、`C-17` 關閉，而強的形式是這個電源循環自己提供的

`DW 81000400 16` 兩次都是偏壓垃圾、沒有任何字等於自己的位址，兩次跨**不同的重置
路徑**（看門狗、ROM 向量），而且**逐位元組相同**。弱的讀法是「長時間斷電也預測垃圾」；
**強的讀法是：loader 在這個電源循環上做完了 `IPCONFIG` 和一次 19,792 bytes 的 TFTP
傳輸，而暖重置保留 DRAM —— 如果那裡是 loader 的網路描述子池，那次傳輸會把它建起來。**
它沒有。所以 `C7-pre` 量到的結構是廠商核心寫的，`§G` 把上傳位址移開是對的。

同一個比較順手是一次保留度量測：**16 個字的 DRAM 上電偏壓撐過一次 ROM 向量重置**，
比 canary 強，因為 canary 是有人選的值。

### 七、開機捕捉的第 0 個位元組不是雜訊，它是時戳

block 0 預測 `A-catch` 前 181 bytes 與 `24c` 逐位元組相同。**量到：byte 0 不同
（今天 `0x00`、`24c` `0xFF`），byte 1–180 全同。** 那個位元組是收發器對一條還沒被驅動
的線的第一次取樣，`0x00` 與 `0xFF` 是同一條線的兩個靜止極性 —— 裝置印出來的字元兩次
會一樣，這兩次不一樣。

**而它是時戳**：兩次冷上電裡，下一個位元組在 **0.349 / 0.340 s 之後**；今天兩次暖重置
是 0.001 / 0.010 s，而且沒有那個 artifact byte。🔴 **所以 `Booting...` 前後各有一個
≈345 ms 的靜默，相鄰而等長，而 `CLK-15` 只擁有後面那一個。** `SPEC.md` `CLK-14` 記著
「冷上電量不到」，也記著一組 340/348/345 ms 曾經被貼錯名字、於 2026-08-25 改判給
`CLK-15`。**兩個等長且相鄰的區間，正是一個數字被歸給錯的那一段的方式** —— 改判送對了
哪一個，現在是一個桌面問題，九份擷取都在磁碟上。今天不判。

### 八、我自己錯了四次，四次都留著

① 🔴 **block 1 的六個 member-1 victim 位址各高了一個 slot（`0x400`）。** 裝置是對的，
十二列 `mb=240211a1` 表示 payload 每格都找到了它的 victim。**檔案不改** —— 它已經跑過，
改它 mtime 就會往後跳，`check-predictions` 會正確地失敗。② block 3 預測 214 bytes、量到
213：`DW 81000400 16` 是 14 個字元不是 15。③ 第一版的字級比較器兩邊都回 0 個字然後報告
`IDENTICAL` —— 一個不可能失敗的比較；重做時加了正控制（字數必須 32）與負控制
（`H0a` 對 `H0b` 必須不同）。④ `24d`/`24e` 的 `^[` 我先讀成檔案庫完整性缺陷（**錯**），
再讀成廠商核心的 `ECHOCTL` 回音（**對，但 2026-08-24 就已經寫在 `RUNSHEET.md` 和這份
`LOG.md` 裡了**）。不是發現，是一份這次沒讀的檔案。

**兩個算術錯都出在現場寫的區塊，沒有一個出在桌上寫的 block 0。**
`check-predictions.py` 驗的是**順序**不是**算術**。回覆長度公式今天 15 中 15，而唯一沒中
的一次是人把命令字元數算錯 —— **它該變成工具，在下一次上機之前。**

### 九、免費的正控制

**主控台行緩衝區 128 bytes**：`A-catch` 回音 `6968 = 128 × 54 + 56`，54 條連續滿行、
零例外（原本 n=7），而最後 56 bytes 的殘餘由 `terminate_esc_line` 自己的 CR 沖掉 ——
**這是它在真矽片上而不是在 pty 上的正控制**。**`LDR-07` 的回覆長度公式** 15 中 15。
**`CLK-13`** 四次新的暖開機，其中 `H3c` 那兩次**有分辨力**。**`CLK-15`** n=9 → 11。
**`NET-10` 的三個不變字**加五次讀取、共 13 次，而關鍵是**這五次在另一個電源循環上**：
先前八次全在同一次開機裡，所以「跨換孔不變」與「跨開機不變」在今天以前是同一組讀數。
🔴 **而 `CLK-16` 的「約 0.32 ms 固定額外開銷」在真實序列埠上被否證**：要求 20 ms 實得
+0.29 ms、要求 2 ms 實得 +0.118 ms —— 不是固定加項，也不是固定乘項。舊的三點都在 pty
上，所以兩組不衝突，**衝突的是「固定常數」這個模型**。

### 十、收工時多抓到一個，而它是 `-text` 那條規則的同一類

`tools/audit-bench-log.py` 在 `bytes` 這個標籤底下印的不是位元組數。它用
`io.open(p, encoding='utf-8')` 讀檔，**Python 的 universal newlines 把每個 `\r\n` 併成
一個 `\n`**，所以印出來的是「位元組數減去 CRLF 對數」。今天五個檔一個不差：
`8855−58=8797`、`5356−49=5307`、`1371−11=1360`、`10790−71=10719`，而 `H1c` 沒有 CRLF
所以 `1671−0=1671` —— **那個沒有差的檔案正是為什麼這件事一直沒被看見**。

🔴 **這正是 `.gitattributes` 的 `bench/** -text` 存在的理由那一類缺陷**：loader 自己的
PHY 格式字串以 `\r\n` 結尾，這些轉錄是逐位元組的，而那條規則套在 git 上、沒有套在跟
它們住在同一個目錄的工具上。**掃描本身從來沒受影響**（八個樣式都是 ASCII，解碼後仍在，
而它的正控制每次都全數觸發），壞的只有那個數字 —— 但那是一個會被引用的數字。

修法是一個關鍵字：`newline=''`，加上直接用 `os.path.getsize` 印真正的位元組數，並且在
兩者不相等時（也就是真的有非 ASCII 位元組時）把字元數標出來。五個檔現在都與 `wc -c`
相同。⚠️ **這個修正還沒有自己的控制** —— 要一個帶已知 CRLF 數的 fixture 才能讓套件分辨
修好的與出廠的版本，而那正是 `hazlint` 1.0 的 finding 6。記在這裡而不是假裝它有。

---

## 2026-08-25（桌面，第五段）— `R1g-4b` 的桌面段：五項修法進 `probe2`，而重點從頭到尾是那套能不能分辨修好的與出廠的

**桌面日，沒上機，沒碰電源。** 產出是三件：`probe2` 的五項必修、兩支新工具、
以及一個原本開著的桌面問題被關掉。

### 一、五項必修都進去了，而其中三項比清單要求的更遠

`docs/rlxprobe-audit-2026-08-25.md` § Must-fix 的四項，加上 `R1g-4a` 自己的結果補的第五項。

**① `rlx_do_break` 沒有 `SAFE_A0`。** 兩條指令。macro 從 `cache.S` 搬到新的
`tools/rlxprobe/rlxasm.h`，因為 `exc.S` 也要用它 —— 把兩條指令複製到第二個檔案，
就是把一個決定變成兩份。**而那一條的原文是「把 `S1` 擴到每一條可能 fault 的指令」，
照做之後它抓出 `uart.S` 裡另外四個沒有 guard 的 `mfc0`。** 那四個裡有三個讀的暫存器
（15、16、16-select-1）在這顆核心上根本沒被確立過，其中 16-select-1 是**故意**拿 MIPS32
的編碼餵 MIPS-I 的部件。所以四個也加了 guard，`rlx_fault_frame` 因此搬到 `report.c`
（`probe0` 連結 `uart.S`，但不連結兩支 payload 的任何一支）。

🔴 **然後 `S1` 這種「清單式」的檢查本身被換掉了。** 一份清單的好壞取決於最後一個
往裡面加東西的人，而 Must-fix 1 之所以存在，正是因為 `break` 沒被加進去。`S3` 改成
讀**發出來的映像**：找出每一個含有可能 fault 指令的 routine，問它進去之前 `$a0`
有沒有被弄安全；既不 guarded 也不在豁免表上的就是失敗。豁免只有兩筆，而每一筆
都是論證不是壓制 —— `rlx_exc_entry`（它就是 handler，它自己 fault 沒有東西接得住）
與 `rlx_cp0_stubs`（經由 `rlx_call0_primed` 進入，`$a0` 已經是 stub 自己的位址，
guard 要建立的性質本來就成立）。`S4` 是它的 mutation。

**② `install_handler` 從不回讀。** 44 次未快取回讀，`install.bad` / `install.firstbad`
進報告也進區塊，命中就**拒絕 `break`**。加上 `install.changed` 當那個比較的正控制 ——
拿寫進去的陣列去比回讀的值，這個檢查在「迴圈根本沒寫」的情況下也會通過，
而數一數 44 個字裡有幾個跟原本存下來的不同是免費的。

**③ `p2a`／`p2b` 兩顆分不出來。** 不是加 `field()`：**`RLX_FLUSH_ISC` 直接不存在了。**
`ISC` 改成在 `Makefile` 裡逐 payload 設定並且加 `override`，所以
`make P=probe2 ISC=1` 也改不動它（`C5` 就是這一格）。build stamp 還是加了 —— `flags`
同時是 header word、`field()` 與 `make show` 的一行 —— 因為一顆說不出自己是什麼的
映像沒辦法從擷取上檢查。

**④ 每一次 CP0 讀都假設 `mfc0` 會寫 `rt`。** 見下一節。

**⑤ `probe2` 一個字都不准碰 `Status.IsC`。** `rlx_isc_inv` 不再被連結，
`rlx_mtc0_status` 只在 `RLX_CLEAR_BEV`（qemu 專用）下才編譯 —— 所以
**一顆裝置版 `probe2` 的映像裡沒有任何一條寫 CP0 register 12 的 `mtc0`**。
`C1` 從反組譯讀這件事，`C2` 證明這個檢查會失敗。這比「程式碼裡沒有呼叫」強：
前者是關於發出來的字的斷言，後者是關於註解的。

### 二、④ 沒有照抄，而多出來的那一趟是今天最值得的東西

稽核建議 `rlx_call0` 的 delay slot 填 `addiu $2,$0,-1`。做了，但常數換成**每一列唯一**
的 prime，而且**普查跑兩趟，兩趟用不同的 prime 家族**：`0xC0DE00nn` 與 `0xD1CE00nn`。

- 兩趟都拿回自己的 prime → **目的暫存器沒被寫**，確定，不是高信心。
- 兩趟不同且都不是 prime → **這個暫存器在兩次讀之間變了**。

第二條是關鍵：**rd 9 就是 `Count`，所以它給了 `F50b` 第二條獨立路線，
完全不經過 `rlx_count_delta` 的算術。** 而 qemu 的 24Kf 自己的 `Count` 是在跑的，
所以它的 row `0x48` 回來就是 `S_MOVES` —— **這個機制的正控制，免費拿到的。**

`rlx_count_delta` 兩個目的暫存器都預先填了，而且填**不同的值**：兩個都填零的話
`0 − 0 = 0`，而零正是這一格在獵的答案 —— 儀器自己的失敗會穿上結果的衣服。
再加上例外計數括起來，以及 payload 自己去比對 census row `0x48`：稽核那一條的最後
一句就是這個對照，而原本沒有任何東西把兩者連起來。

代價：結果區塊 537 → 809 字，`DW 80A01000 809` = 9,567 bytes / 2.49 s
（數字出自今天新做的 `tools/reply-size.py`）。

### 三、四個 mutation，一個必修配一個，而其中一個存在是因為 qemu 到不了那個狀態

`tools/test-rlxprobe.sh` 66 → **106 格，0 失敗**。

- **M1**：一個 census stub 發 `nop` 而不是 `mfc0` → 那一列必須是 `S_NOWRITE`。
  🔴 **qemu 自己永遠產不出這個狀態**，它的 `mfc0` 一定寫 `rt`；沒有這個 mutation，
  ④ 的整個 prime 機制就是沒有任何東西測過就上機。
- **M2**：install 的儲存改寫到別處 → `install.bad != 0`、印出拒絕、**`break.count`
  一次都沒出現**、而且仍然走到 end marker。那條分支從前是一個掛死。
- **M3**：拿掉最後的 `copy_vec_back()` → 兩條 restore 腿都響。
- **M5**：把存下來的向量換成 handler 自己 → install 什麼都沒改，回讀不可能失敗，
  payload 必須**自己說出這個檢查是空的**。沒有 M5 的話，那個「這個檢查本來就不會
  失敗」的控制自己是沒被檢查的。

🔴 **而修好的 payload 第一次跑 qemu 就抓到我自己的一個缺陷。**
`restore.stillhandler` 在一次完美的 restore 上讀到 20：handler 有十個 `nop`，
qemu 的向量頁又是全零，所以那個「負控制」在數巧合。改成只數 install 真的改過的位置。
**這就是為什麼 harness 要跑在上機之前而不是之後。**

### 四、`tools/reply-size.py` —— 公式變工具，母體從手數的 15 變成 121

`LDR-07` 的 `len(cmd) + 2 + 47 × lines + 9`。昨天 15 中 15，唯一沒中的是人把
`DW 81000400 16` 數成 15 個字元（是 14）。

**每個指令族的常數是從擷取擬合出來的**，不是從 loader 原始碼讀的、也不是在終端機上
數的：`DW` 47×⌈N/4⌉（n=91）、`EW`／`EB` 無輸出（n=11）、`Y` 23（n=6）、`PHYR` 68（n=5）、
`FLR` 79 **而且不回 `<RealTek>`**（n=6）。**`DB`／`J`／`MDIOR` 明確不建模**，各自寫下
樣本數與理由 —— 把沒看的東西算進「0 個不明」，就是本專案一直在抓的那種掃描。

對 `bench/` 全部跑：**121 中、0 個不明**。原本兩個「不中」現在各有名字：`CONT` 的 24
bytes 是 `ECHO-ONLY`（`C-19` 的簽名），`A0-reopen-control` 的 44 bytes 是
`UNKNOWN-COMMAND`。

🔴 **十二個控制項在我自己的工具上先抓到三個錯**，其中一個是 `FLR` 的 body 我多算了 2
（它的擬合殘差已經含了 echo tail，而它根本不回 prompt）。**獨立確認**：工具對
`DW 80A00000 137` 算出 1671，正是 `H1c` 量到的位元組數，兩條路互不相干。

### 五、`tools/boot-timeline.py` —— 兩個相鄰的 ≈345 ms 分開了，而 `CLK-15` 有一句話是錯的

**先把錨點定死。** 這段靜默從哪一個位元組起算有四個講得通的選法，彼此差到 1.7 ms。
拿 `CLK-15` 自己那九份擷取試：**只有「`Booting...\r\n` 之後那個 NUL → `chipName` 的
第一個位元組」重現得出 0.3447 .. 0.3569**，正對上那一列公佈的 344.7–356.9 ms；
另外三個都重現不出來。所以那就是它一直在量的東西 —— 而它從來沒寫下來。

**然後冷暖分群，而分群的依據刻意不是 artifact byte。** 用 artifact byte 分，
「artifact 只出現在冷開機」就變成定義上的真理。用的是 `C-8`：loader 自己在
`ramSize: 32M` 之後印 `Reboot Result from Watchdog Timeout!` 還是一個空格 ——
一個硬體位元，路徑上沒有我們的軟體。

| | |
|---|---|
| 冷上電 | 348.0–356.9 ms，n=7，全距 2.5 % |
| 暖重置 | 338.2–347.6 ms，n=7，全距 2.7 % |
| 合併 | 338.2–356.9 ms，全距 5.4 % |

🔴 **兩群不重疊，而 `CLK-15` 寫的是「冷暖重置皆同」。**
決定性的比較是**同一個電源循環之內**，因為那樣就沒有日期、溫度與板子：
`2026-08-24c` 冷 352.1 對同循環三次暖重置最大 347.6（**+4.5 ms**）、
`2026-08-25` 冷 355.7 對同循環四次暖重置最大 341.1（**+14.5 ms**）。兩個獨立循環，
方向一致。**那一列記的 3.5 % 未解釋散布，有一部分是兩群被當成一群。**

機制未定。候選是 SPI NOR 控制器的除頻在冷上電與 watchdog／ROM 重置之後不同、
或 SPI NOR 自己的上電喚醒。**決定它的實驗是兩個 `DW`**：冷開機後與暖重置後各讀一次
`SFCR`／`SFCR2`／`SFCSR`／`SFDR` 並比對。零風險，順手，寫進 `SPEC.md` §17 了。

**而原本的桌面問題答了**：2026-08-25 早上把 340/348/345 三個數字整批改判給 `CLK-15`，
**送對了兩個、送錯了一個**。340 = `bench/2026-08-24c/A-catch` 的 artifact byte 間隔
= 0.3404 s，那是 `CLK-14` 的量；348 與 345 是 `D1` 的 0.3476 與 `D4` 的 0.3447，
屬於 `CLK-15`。而 `CLK-15` 公佈的下界 344.7 就是 `D4` 那一筆，**所以那個區間本身從來
沒有被汙染過** —— 被貼錯的是「三個數字是同一件事」這句話。

🆕 順手把 `CLK-14` 的暖重置母體從 n=3 加到 n=6，新的三筆跑在 2.115 ms 的心跳格點上，
是遠比 20 ms 格點緊的上界。**而 `H1b` 被排除，排除它才是重點**：它送的是
`J 80500000`，開機文字之前那個最大間隔 0.1237 s 是 `probe1` 自己的延遲迴圈 ——
那是 `CLK-03` 的量，把它放進 `CLK-14` 就是再犯一次同樣的錯。`B3` 是這條規則的控制。

### 六、`est` 198 對 252：兩個都不是「準的那一個」

兩張表逐列重算過：計畫 §12.1 的每一列都等於它自己的桌面+bench+儀器，累計欄一致，
總計 252；`PROGRESS.md` gate board 的十七列相加確實是 198。**所以算術從來不是問題。**

計畫的儀器欄合計 44，所以 252 − 44 = **208** 才是它的「桌面+bench」。而 198 不是 208：
十七列裡有十列跟計畫的桌面+bench 完全相同，**七列不同，而且方向不一致**
（`R5` 少 4、`R1-pub` 少 2、`R7` 反而多 1），淨差 −10。

🔴 **所以 198 不是總量、不是桌面+bench、也不是任何一個一致的子集，沒有規則生得出它。**
它也不是舊版的複本 —— 舊版的複本指得出是哪一版。它是逐列長出來的第三個數字。

**該拿哪一個做決定？計畫的。** 因為旁邊那一欄是 `Actual`，而 `Actual` 數的是
`LOG.md` 裡一個 gate 關到下一個 gate 之間消耗掉的工作段，**那裡面包含儀器日**。
定義相同的估計只有計畫的小計。對兩個已關的 gate：`S0` 實際 1 對計畫 3、
`R0` 實際 7 對計畫 11 —— **消耗 8 對計畫 14，0.57×，n=2**，而值得留下來的是這個比值
不是任一個總數。

**而 house rule 1 的缺陷比「兩個擁有者」更尖。** 估計是規劃的產物；這個檔案是
「我在哪裡」的擁有者，那是關於**已完成工作**的事實。`Actual`／`Status`／`Evidence`
屬於這裡，**`Est.` 不屬於**。建議的修法是把那一欄刪掉而不是對帳，只在表下留一行
記那個量到的比值 —— 比值本身是關於已完成工作的事實。**今天沒做**，因為從 gate board
刪一欄是一個決定，而這一段是那個決定該根據的分析。

### 七、順手驗到的一件 `P4a`

`RUNSHEET.md` 裡我寫「`fbac7d60…` 是 `R1d` 量測所在的那顆」—— 那句話必須可驗證，
不然它跟一個沒有出處的數字沒兩樣。`git archive 2db12bb` 到乾淨目錄、同一版 gcc 12.4.0
重建：**`fbac7d60…`，逐位元組相同。** 🆕 **這順便是 `P4a`（可重現建置）的第一個資料點，
早了四個 gate 而且是意外拿到的**：這棵樹跨 checkout 已經是可重現的。

### 八、收工清單

`tools/test-rlxprobe.sh` 106/0；`tools/test-reply-size.sh` 12/0；
`tools/test-boot-timeline.sh` 12/0；`python3 tools/spec-check.py` 八個控制全過；
`bash tools/test-file-modes.sh` 3/0（四支新工具都 `100755`）；
`ci-census` 在模擬的 text job 上全綠。`ci-expected.tsv` 的 `test-rlxprobe` 66 → 106，
加了兩列新的套件；`ci.yml` 的「NOT RUN IN THIS JOB」122 → 162，
而「裝了 gcc 會怎樣」重量過：`test-rlxprobe` 從 29/37 變成 **56 ok / 50 FAIL**。

## 2026-08-25（上機，第二次）— `R1g-4b`：`R1e` 關了，而最貴的一課是第二次 `J` 開的是原廠韌體

**一次電源循環，23 份擷取，四個 prediction block，零個 flash 位元組。**
`bench/2026-08-25b/`。這是 CP0 census 在這顆矽片上跑起來的那一場。

### 零、插電前攔下來的兩件，各自都能花掉這次電源循環

**① `§H2a` 的 `--image` 指著 `build/p2a/probe2/probe2.bin`。** 那個檔**存在**，
6,656 bytes、`8a15b501…` —— 已撤回的 p2a。它會乾淨地上傳、乾淨地跑起來，跑的是
`break` 失敗完全靜默、census 被汙染、`FLUSH_ISC` 還在的那一版。而 `build/probe2/`
今晚之前根本不存在。同一個缺陷類是 `G2`/`G4` 帶 `--load-addr 0x80A00000`，
上一場才更正過；**它活過了「兩支 binary 併成一支」那次重寫，因為沒有人拿工具指過那個字串。**

**② hang 復原指令 `DW 80A00000 137` 是 `probe1` 的。** 今晚的區塊在 `0x80A01000`、
817 個字。而 `MEM-15` 讓這條更糟：`probe1` 昨天的區塊 —— magic `524C5831`、
nonce `9D34F1C7`、13 列資料、有效封印 —— 可能還在 `0x80A00000`，**會看起來像一次
完成的執行**。改成 `DW 80A01000 817`。

還有一件不花電源但會發表錯誤數字的：**`0xBE71BAD1` 在任何 payload 原始碼裡都不存在**，
而三個檔案（`RUNSHEET.md` ×2、`SPEC.md` `CPU-27`）把它當成 `BEV=1` 的拒絕簽章。
量：`grep -rin be71bad1 tools/` 零命中，同一支 grep 找 `DEADC0DE` 有命中 ——
**搜尋是會失敗的**。真正的簽章是 `progress=00000010` 加 `status` bit 22，兩個獨立訊號。

### 一、`R1e` 關了，而每一格都有它自己的控制

`status = status_end = 1000FC00`，**bit 22 = 0** —— `CPU-27` 從「讀，單一來源」
變成量。而讓它是量而不是又一次讀的，是 `break` 陷進我們裝在 `0x80000080` 的 handler
**並且回來了**：`break.count=1`、`cause=00000024`（ExcCode 9）、`epc=80500270`，
那是 emitted image 裡 `break` 的確切位址。「核心從那裡取指」是直接證據不是推論。

🔴 **被撤回的 `1000FC01` 是對的。** 量到的字跟它只差 bit 0 `IEc`，而 `IEc=0`
正是「`J` 清掉 `IE`」對 payload 的預測。當初撤回是因為它只有一個出處，不是因為它錯 ——
**這兩件事不一樣，而寫下差別比宣布誰贏了重要。**

`PRId = 0000CD01`，事前寫進 `PREDICTIONS-b4-block1.md` 的預測原封命中。
⚠️ **值是量，名字不是。** 這個 repo 裡沒有任何來源把 `0xCD01` 對到 `RLX4181`
而不是 `RLX5281`；那個 `52481` 是同一個數字換個底。**所以 `RLX5281` 仍然不能寫 ——
而 `RLX4181` 也不能。** 缺的是一份來源，不是一次量測。

**`F50b` 答了，而答案是貴的那一邊**：`Count` 沒有實作（rd 9 讀 0、`S_ZERO`、
`count.delta = 0`）。**`R5-0` 的 SoC timer 驅動是前提不是加分，`R1c` 失去第一條計時路線。**

而讓那個 0 是真的 0 的，是 **`nowrite = 0`，256 列全部** —— `mfc0` 在這顆核心上
一定寫 `rt`。稽核 Must-fix 4 問的就是這件事，**答案是用一支為了偵測它而造的儀器排除的，
不是用假設排除的**。這是今晚最像工程的一格。

### 二、`Random` 是這份 census 本來不會有的正控制

row `0x08` 是 `mfc0 v0, c0_random`。八列回十六個不同值，index 欄位落在 **5…29，
全在 0…31 之內** —— 而 `CPU-08` 的 32 個 TLB entry 是量到的。傳統 64 entry 的 R3000
會在 8…63 之間繞。**這條佐證路線裡沒有任何 TLB 探測。**

為什麼它比別的列重要：`F50b` 是靠「`Count` 不動」決定的。**沒有一個在這顆矽片上
會動的暫存器，那個讀數就不可否證** —— 一個壞掉的雙讀機制會給出一模一樣的答案。
qemu 的 `0x48 = S_MOVES` 是 qemu 的控制。這一格是這顆的，而且免費。

順帶：`moves = 8` 而那八列全是 rd 1 的八個 select，`rows.suppressed = 0`，
`rows.printed = 39` —— **這顆 CP0 忽略 select 欄位**。而看得懂 39 的前提是插電前
把表上的 `0x20` 改成 `32 + 7 × moves`：**會變動的暫存器不可能等於自己稍早那一列**，
所以在完全忽略 select 的核心上它也會印滿八個。

### 三、CP0 20 終於分開了

`probe1` 的 `XCT0` 讀到 `00000000`，但分不開「有實作而且讀 0」與「目的沒被寫」。
今晚 row `0xa0` 一樣是 0，而 `nowrite = 0` 把它分開了：**它真的讀 0**。
寫側早就是量（cells 2/3/6 證明 `mtc0 $t,$20` 有效果）。
**合起來：CP0 20 是唯寫的命令暫存器、讀回 0。** 這句話直接進 `R5b` 的 MTD 驅動。

`Config` 讀 0 → `Config.M = 0`，**不是 MIPS32 核心**，直接證明。**而且沒有 `Config1`，
所以 `CPU-25` 不可能從 CP0 出來** —— 我事前提的那條免費路線被量測關掉了，
這比它成立更值得寫下來。

### 四、`CPU-25` 現在是「路被量掉了」而不是「還沒試」

`GEOM=1` 沒跑，理由不是謹慎是量測：`rlx_r3k_size` 的演算法**靠隔離**。
它先在 base 寫 marker 再讀回 —— **不隔離的核心也會過，因為 store 與 load 都進 DRAM，
守門為了錯的理由通過** —— 再把 `base+k*4` 逐一清零、在 base 寫 −1、往上找第一個非零。
核心不隔離時那些字剛被清成 0 且保持 0，迴圈走到天花板，**回傳 `0`，而 `0` 正是它自己
「核心不回答」的值**。`CPU-35` 昨天已經量到這顆不隔離。**所以這個實驗昨天就被否證了。**

順帶更正一個到處都在的措辭：`GEOM=1` **不是**「寫 1 MiB 真記憶體」。
loop 2 每圈一個 `sw`、14 圈，加 base 兩次，每次呼叫約 16 個字。**1 MiB 是外框不是體積。**

還活著的只有一條：**不需要隔離的 eviction walk**，用 `H1` cell 1 已經證明的機制
（寫進指令流的 store 看不到）。桌面工作，`probe3`。

### 五、兩條通道，而每一個控制都打出來了

40 個表頭字逐字命中，含 word 32–39 = `H0a` 前八字（六分鐘前 loader 用另一條命令讀的）。
封印 `EC84408D` 兩邊一致。毒區 809–816 八個 `DEADC0DE`，817–819 **不是** —— 兩側控制。
`H2i-below` 與 `H0d-a` 相同 → `probe2` 沒寫到自己區塊以下。

🔴 **而這一場避開的假警報是量到的不是論證的。** `H2h-utlb` 跟**今晚**的 `H0c` 逐位元組
相同；跟 **08-25** 的 `H0c` 就是不同。UTLB 向量是 DRAM 上電偏壓，loader 從不寫它，
而這塊 DRAM 的偏壓跨電源循環會動 4–27 個位元（共 256，含正負控制）。
拿上一場的擷取當基準，一次**完美的 restore** 會讀成 **「`probe2` 毀了實體 0」** ——
那正是唯一會讓 gate 停下來的結果。

### 六、封印不能用直接重加來驗證，而這件事現在寫下來了

重加 0–807 得 `EC84409D`，儲存的是 `EC84408D`，**高剛好 `0x10`**。
`probe2.c` 先算總和、寫進 word 808、**然後**才 `progress(P_SEALED)` ——
所以算的時候 word 2 還是 `P_RESTORED`(`0x80`) 不是 `P_SEALED`(`0x90`)。
把 word 2 換回 `0x80` 重加得 `EC84408D`，精確。

**沒有調換順序。** 先封印再蓋 progress，才能讓 `progress` 一路單調到底 ——
一個封印寫好但 progress 停在 `P_RESTORED` 的區塊，是死在那兩步之間的執行，
**那個狀態值得看得見**。修的是註解與這一段，不是順序。

### 七、`CLK-15 冷暖差`：SPI 除頻被排除

`DW B8001200 4`，這個視窗在這台裝置上的第一次讀數。
`SFCR`/`SFCR2`/`SFCSR` 冷暖**逐位元組相同**，只有 `SFDR` 由 `FFFF0002` 變 `FFFF0000`。
**除頻不變，所以它不是那 4.5–14.5 ms 的機制**，下一個候選是 NOR 自己的上電喚醒。

🔴 **而 `SFDR` 會動，正是讓「相同」有意義的那件事。** 否則「四個字一樣」同時相容於
「除頻不變」與「這個視窗根本不反映開機組態」，這一格分不開。
**這個控制是意外撿到的 —— 我為這一格設計的正控制（`SFDR` 裡有 JEDEC ID `1C 70 16`）
沒有打出來。**

`SFCSR = D8050000` 解碼：兩個 chip select 都不啟用、`SPI_RDY`=1、`LEN`=`01`（2 bytes，
**不是重置值 `11`**）、`CMD_BYTE`=`0x05`（`RDSR`）。`SFCR2` 最高位元組 `0x0B`（`Fast Read`）。
**loader 不是把控制器留在重置狀態，是留在輪詢狀態。**

### 八、我錯了五件，五件都留著

1. **`A-catch` 位元組 1–181** —— 今晚有**兩個** artifact byte（`00 fc`），
   開機文字從 byte 2 開始。裝置那 181 個位元組跨三次冷上電逐字相同、負控制也成立；
   **不可預測的是儀器那一段**，而 `0xFC` 不是靜止取樣，是 framing error。
2. **`SFCSR & 0xF8000000 == 0xF8000000`** —— 量到 `D8050000`。
3. **`SFDR` 含 `1C 70 16`** —— 量到 `FFFF0002`。這一格的正控制沒打出來。
4. **事前寫下並命中**：payload 的判決行不涵蓋 `S_ZERO`，今晚量到確實沒觸發（無害）。
5. 🔴 **最貴的一件：第二次 `J 80500000` 開的是原廠韌體。**

第五件值得單獨寫。跑完一次之後我想拿 census 的重現性控制，於是再送一次 `J 80500000`。
它印 `decompressing kernel:`，把原廠韌體開到 userspace。
**原因是 loader 在每次開機 —— 包含 watchdog 重置 —— 都會把 flash `0x060010` 的核心
重新搬進 `0x80500000`。** 我在 block 3 寫的「the payload is unchanged in DRAM at
`0x80500000`」是假設不是量測，**而這個 repo 裡本來就有推翻它的事實**：`§G1` 存在的
理由就是問這件事，`§H1a` 的警告字面上就是這句。**那條更正是我今晚親手寫進 sheet 的，
然後從另一邊走進同一個陷阱。**

代價：一次電源循環。已經拿到的東西一個都沒少。
而它量到的是 **`C-16` 的複製者在暖重置上也會跑** —— 所以**同一次開機不重新上傳
就不可能把 payload 跑第二次**，這件事之前沒有任何檔案寫過。

**這裡有一條規律，第三次出現了**：`G2`/`G4` 的 `--load-addr`、今晚的 `p2a` 路徑、
現在這一個。三次都是**假設一個位址的內容**，三次都有一份既存的檔案講反話。
下一支 payload 的 sheet 應該有一格叫「跳進去之前先讀那個位址的前八個字」。

### 九、三個工具缺陷，都是把工具指向今晚的擷取才掉出來的

**`reply-size.py check` 遇到讀不了的 `.meta.json` 會 crash。**
`UNREADABLE` 分支存在、有計數、還算進 misses，**但永遠印不出來** ——
它把錯誤訊息存進印表機用 `%+d` 格式化的那一欄。**存在為了回報壞擷取的那個分支，
是唯一一個會把工具弄掛的分支。** 跟 `hazlint` 1.0 的 K4、`test-gitignore.sh` 的 exit 1
同一個缺陷類：一個不會觸發的控制。12 案例 → **21**，含一個把兩半都改回去、
要求 traceback 回來的 mutation。順手：`UNREADABLE` 不再算進 `modelled`，
那一直在灌水本專案引用的母體數字。

**`boot-timeline.py` 的 artifact 錨點寫死成 byte 0 → byte 1。**
今晚兩個 artifact byte，它量的是**兩個 artifact byte 之間**，回報 **4.2 ms**，
而另外兩次冷開機是 340.4 與 349.0 —— 池化散布 **149.1 %**，而且沒有一行說為什麼。
改成 byte 0 → 裝置自己的 `\r\nBooting`。⚠️ **把舊守門拿掉之後每一份暖擷取都壞了**：
`\r\nBooting` 在 `--esc-after` 擷取裡是在 payload 報告**之後**才出現，
於是 `H2a` 的 2,909 位元組報告整個變成「prefix」，artifact 讀 63.7 s。
所以現在是兩個守門：byte 0 是靜止取樣，**且** prefix ≤ 8 bytes。
池化散布 149.1 % → **2.5 %**。12 → **15** 案例。

**`exc.S:201` 的註解寫 `0x110F0000`，正確是 `0x10F00000`**（兩位數對調）。
註解不影響二進位，**但那是讀者拿來對讀數的數字** —— 一次正確的 not-written 執行
會被任何相信它的人判成不符。裝置今晚回的是 `S_ZERO` 不是 `S_NOWRITE`，
所以那條分支沒被走到，這次沒付代價。

### 十、順手落下來的三個數字

`booting` 冷 n=8 / 暖 n=8 **仍然不重疊**，而同循環冷暖對多了第三個：**+6.0 ms**
（348.8 對 342.8），落在既有的 +4.5 與 +14.5 之間。

冷開機在 **2.32 ms** 的 ESC 格點上是 **348.8 ms**，**落在** `CLK-15` 公佈的
348.0–356.9 之內 —— 細格點沒把數字拉走。**這是一個回了陰性的偏差檢查，
不是散布的量測，n=1 量不出散布。** 而 `--esc-period` 這條路的機制本來就不成立：
`drain()` 用 `select()` 在位元組抵達當下打時戳。真正要查的是 `.timing` 的
一次 `read()` 一個時戳，那是桌面工作。

`MEM-15` 收緊：`probe1` 那個 137 字、有 magic 有封印的區塊**沒有**撐過約 3.9 小時斷電。
區間從「幾秒有／16 小時無」變成「幾秒有／3.9 小時無」，而且載體是選定值不是 canary。

## 2026-08-26（桌面）— `R1g-5`：`R1-gate` 結案，而寫作把 gate 自己倚賴的兩個說法否證掉

桌面一整天，不通電，零 flash 位元組。要做的是 `R1-gate` 的最後一步：寫
`docs/rlx-cache-and-cp0.md`，四個下游決定各配上決定它的那個讀數，`CPU-19` 從
讀升成量，`C-6` 關閉或殘留重述。**四件都做了，而做的過程翻掉兩個這個 gate 一直
站在上面的說法**，還有一個從 `CPU-19` 寫下來那天就存在的儀器漏洞。

### 一、先講結論：gate 打勾了，而代價付在決定①上

`R1-gate` 的 DoD 是「四個下游決定各指名一次量測」。今天三個指名了，②沒有。
我還是把它打勾了，理由三條，按分量排：

**第一，缺的不是分析，是一支不存在的 payload。** ② 要的東西再看一百遍 `R1d` 的
擷取也不會出現 —— 要的是 `probe3` 跟一次上機。一個為了等未來某次上機而不關的
gate，實際上已經是 backlog 項目而不是 gate。把它歸進新開的 `R1h`，它才有主人、
有 payload、有 DoD、有 stop-loss。**這比讓 `R1-gate` 開著更負責，不是更寬鬆。**

**第二，「未答＋判決它的實驗」本來就是這個專案自己寫的合格答案**（`CLAUDE.md`：
不確定是有效答案，後面接判決它的實驗）。stop-loss 也早就寫了：決定沒定案時，
誠實的動作是往下交。

**第三，代價付在①。** 決定①「`R5b` 的 MTD 驅動在哪裡刷」量到的是**指令側**。
MTD 驅動還要把 flash 讀回來，而那是「視窗內容在 D-cache 背後被換掉」——
跟②同一個方向，`R1d` 一個字都沒量。所以①結成「指令側已答；資料側跟著②走」。
**一個 gate 可以帶著誠實收窄的結論結案；不能帶著沒被說出來的漏洞結案。**

### 二、「D-cache 是 write-through」是把量測讀寬了，而且有第二來源講反話

這是今天最重要的一件，而它是被「決定②要寫成未答」這個要求逼出來的：
我要寫清楚 ② 為什麼未答，就得先寫清楚 `R1d` 到底涵蓋了什麼。

`probe1` cell 1（cached store）與 cell 5（uncached store）的 `ma` 都是
`240222b2`，而 `ma` 是 uncached 讀回 —— 所以 cached store 確實不必刷就到了記憶體。
**但兩格的 store 都打在 D-cache 沒有持有的 line 上**（victim 那些字是被
**執行**過，不是被 **load** 過）。一個 write miss 之下，**write-through** 與
**write-back 但不做 write-allocate** 會給出同一個讀數。

`notes/cache-model.md` 從第一天就寫了選言：「write-through（或不做
write-allocate）」。**而下游每一次轉述都掉了括號裡那半句** —— `SPEC.md`
`CPU-19`、`RUNSHEET.md` § Results B4、`PROGRESS.md` § Now、還有 `PROGRESS.md`
自己的 `R1g-5` 那一列。**一個承重的替代選項不該擺在括號裡，那正是它會被丟掉的原因。**

然後我去翻廠商自己怎麼設定這顆：兩份 GPL drop 的
`boards/rtl8196e/config.linux-2.6.30.*` 五個板型全部寫
**`CONFIG_ARCH_CACHE_WBC=y`** —— write-back。⚠️ **兩份 drop 同源，這是一票不是兩票。**
但它是一票投在我這裡記成「已定案」的那個問題上。

**為什麼這件事對 ring 是致命而對 `probe1` 不是**：descriptor ring 的樣式是
「load 狀態字 → store ownership 位元」，**那是一次 write hit**。
write-back 不做 write-allocate 的話，那個 store 就髒在 D-cache 裡，DMA 引擎
看不到 —— 而 `probe1` 的六格會讀到跟它們讀到的一模一樣的東西。
所以 **CPU→裝置那一半，對 `R6` 真正會用的樣式也沒有涵蓋。** ②在兩個方向上都未答。

判決它的是 `R1h` 的 cell E：先 load 再 store 同一個位址，然後 uncached 讀回。

### 三、我們自己寫的否證條件成立了，而當初那次掃描只掃了 loader

`notes/cache-model.md` 有一句寫得很好的否證條件：

> 「這顆用 R3000 快取模型、不用 MIPS32 的 `cache` 指令」這個主張，
> **由在任何會執行的廠商程式碼裡找到一條 `cache`（主 opcode `0x2F`）來否證。**

當初回 0 的那次掃描掃的是 `stage2.bin` —— 一台 4 MiB 裝置裡的 56,592 bytes。
今天把它指向這台自己的 kernel（從自己的 flash dump 切出來、解壓）：

**37 條 `cache` 指令，全部是 D 側。** `0x8000CA40`–`0x8000CD4C` 一段，
op 欄只有 `0x11`（`DInval`）／`0x15`（`DWBInval`）／`0x19`（`DWB`），
base 只有 `v0`／`a0`，offset 只有 `0x00`…`0x70` 八個、stride `0x10` ——
**八條蓋 128 bytes，那就是 16 byte line 的假設，而這個讀法只需要二進位。**
全檔另外命中 15 條，位址全部 ≥ `0x802BA660`、op 欄十種、offset 是任意 16 位元值。
**code 與 data 被三個彼此獨立的性質完全分開**，不是靠我挑位址挑出來的。

**兩個控制，都會失敗而都沒失敗：**

**① VMA base 不是假設的。** 取 file offset = VMA − `0x80000000`，
`jal` 的目標落在合理 prologue 上的比例是 **18,068／31,145 = 58.0 %**；
把整個 image 位移 +1／+2／+7／−3 個字，同一個判準給 **1.7 %／3.0 %／2.9 %／0.2 %**。
判準很粗，所以結果是那個對比，不是 58 % 這個數字。

**② 掃描器有正控制。** 同一支不改，跑 `stage2.bin`：五個已知的 CCTL 位址全部重現
（`0x020` @ `0x804004DC`、`0x202` @ `0x804004F8`、`0x010` @ `0x80400514`、
`0x200` @ `0x804066CC`、`0x002` @ `0x80406704`），而 `cache` 只命中**一條** ——
`0x8040D264`，op 欄 0，就是 `notes/lwl-mystery.md` 早就判過的那個 data 偽陽性。
**它找得到該找的，而且還是找得到那個不是程式碼的。**

⚠️ **這不代表這是 MIPS32 核心**，`Config.M = 0` 是量到的。它改的是句子：
**loader 只用 CCTL；這台的 kernel 用 CCTL 做整顆快取的操作、用 `cache` 做範圍操作，而且只有 D 側。**
I 側（op `0x10`）全檔零條，I 側一律走 `CCTL 0x002`。

⚠️ **而「在二進位裡」不等於「會執行」**，這一格要的是後者。那些常式從
`_dma_cache_wback_inv` 進來，乙太網路路徑每個封包呼叫一次，而這台在轉封包 ——
**那是論證，不是讀數。** 判決它的是一條 `cache 0x11` 放進 payload 跑跑看，
而 `R1g-4b` 已經量到 handler 能接，所以一次 trap 換來的是一行印出來的判決，
不是一次電源循環。

### 四、CCTL 有名字了，而當初的結論是查錯目錄

`notes/cache-model.md` 寫過「`arch/mips/mm/` 裡只有原版的 `c-r3k.c`、`c-r4k.c`、
`c-tx39.c`、`c-octeon.c` —— **沒有 Lexra 專屬的 cache 檔**」。
**這兩棵樹有兩個 arch 目錄，而這顆 SoC 走的是 `arch/rlx/`。**
`arch/rlx/mm/cache-rlx.c`，"RLX specific mmu/cache code"，Realtek，Tony Wu，2008-12-07。

而且**這個 repo 早就在別處引用過那個目錄** —— `SPEC.md` `CPU-33` 的三個來源之一
就是 `arch/rlx/kernel/traps.c`。**所以事實在檔案裡，只是那次搜尋沒去。**
跟 `43ec0e0` 同一個缺陷類，只是這次連查都沒查。

它的標頭註解直接給出編碼：

```
 *  CCTL OP                      *  CACHE OP
 *   0x1   = DInval              *   0x10 = IInval
 *   0x2   = IInval              *   0x11 = DInval
 *   0x100 = DWB                 *   0x15 = DWBInval
 *   0x200 = DWB_Inval           *   0x19 = DWB
 *                               *   0x1b = DWB_IInval
```

**四個命令從「用法推出來的意思」變成「有來源明寫的名字」**，而 **`0x100`（`DWB`）
這個 repo 之前一列都沒有** —— 這台的 kernel 在 `0x8000CA94`／`0x8000CAC0` 發它。
⚠️ **`cache-rlx.c` 跟 `c-r3k.c` 是兩個檔不是兩個獨立來源**：同一批 drop、同一個
Realtek SDK 祖先。變的是「本來任何來源都沒有名字」現在有了，不是多一票。

**`0x010`／`0x020` 還是無名。** 🔴 **同一天的第二段就推翻了這一句 —— 見本檔 2026-08-26（桌面，第二段）：它們是 `IMEM0FILL`／`IMEM0OFF`，而命名檔就在已經在手的 GPL drop 裡。這一段留著不改，因為它是當時狀態的紀錄。** 但證據變了形狀：**這台上有兩個獨立實作**
（loader `0x804004DC`／`0x80400514`，kernel `0x80002240`／`0x800022A8`）
都在 reset 時發它們，都夾著 `0x202`。那是關於它們的**位置**，不是關於意思。

**而能命名它們的那條路我主動放棄了，這是決定不是缺口**：從 payload 把一個沒有
名字的命令寫進快取控制器，在一台裝置的預算下換不到任何下游決定需要的東西 ——
`R5b` 要的是 `0x002`，②要的是 D 側作廢，而候選（`0x001`、`0x200`、`cache 0x11/0x15`）
全部有名字。**剩下的是一份會講話的文件。**
順帶：這一格原本寫「`R1e` 或一次 `devmem` 級的讀取就能定案」。
**`R1e` 跑了而且做不到** —— census 讀 CP0 20 讀到 0，而
**一個永遠讀 0 的讀側說不出寫側的意思。**

### 五、`SPEC.md` `CPU-19` 從寫下來那天起就沒被 `spec-check.py` 檢查過

今天要改的就是這一列，改之前先看它現在長什麼樣，然後發現：
`` `Status.IsC|SwC` `` 裡那個 `|` 沒跳脫，於是**七欄的表裡這一列有八格**。

**每一項檢查都是「按索引拿格子」**，所以斷點之後每一欄位移一格，
而它們不會報錯 —— 它們讀到另一格然後通過：C2 把值欄當標記欄（裡面剛好有「——」，
`—` 是合法標記）而通過；C4／C5 把**來源欄**當擁有者欄，裡面沒有可辨識的路徑，
於是把這一列算進「owner 是 gate 而不是檔案，跳過」。
**摘要把它印成「跳過」，而不是「壞掉」。**

跟 `hazlint` 1.0 的 finding 6、`reply-size.py` 的 `UNREADABLE`、
`test-gitignore.sh` 的 exit 1 同一類：**一個不會觸發的控制**。

補了 **C8 —— 每一列的格數要等於它自己表頭的欄數**，以及第九個突變。
**M9 不是我發明的**：它就是把那個 `|` 還原回去。八個突變變九個，全部成立。

順手把 `SPEC.md` §17 五列 3 格對 4 格的參差補齊。**然後把同一支掃描器指向所有
committed 的 markdown**，又掉出兩個：`PROGRESS.md` 那列引用 kernel image header
的 `cr6c \| 80500000 \| ...`（從寫下來就把 Corrections 表撐成六欄），
以及 `RUNSHEET.md` `P3` 那列（四欄的表裡五格）。兩個都修了。
**一支新工具的第一次執行找出三個既有缺陷，這是它值得寫的理由。**

### 六、`CPU-25` 第一次有一個切自這台的來源，而三個數字的強度不一樣

同一份解壓出來的 kernel 裡：
`0x8000CAAC`、`0x8000CBE0`、`0x8000CCD4` 三處 `sltiu $3,$3,0x4000`，
`0x8000CA18` 一處 `sltiu $2,$5,0x2001` —— 那是「範圍太大就整顆刷」的門檻，
而在 `cache-rlx.c` 裡它們是 `cpu_dcache_size` 與 `cpu_dcache_size × 2`。
**所以這個 build 宣告 D-cache `0x2000` = 8 KiB。**

**三個數字的強度必須分開講，不能混在一起引用：**

| | 強度 |
|---|---|
| **D line 16 B** | **最強** —— 只靠二進位就讀得到：八條 op 蓋 128 bytes 就是 line 大小的假設，跟來源說什麼無關 |
| **D 8 KiB** | 弱一階 —— 要靠 `cache-rlx.c` 才解得開 `0x4000` 那個常數 |
| **I-cache 大小** | **這條路完全讀不到** —— I 側這個 build 沒有 per-line op，沒有門檻常數可讀。它還是留白，而且是一票（第三方 dtsi）都沒有第二個 |

而它們全都是「build 相信的東西」，不是矽片。**寫在 walk 之前所以是否證條件；
寫在之後就只是描述。**

### 七、`R1h` 開了，因為孤兒項是這張表自己的規矩要抓的東西

`C-6` 的兩個擁有 gate（`R1d`、`R1e`）都在它底下關掉了。
`PROGRESS.md` 的規矩是「一個沒有擁有 gate 的項目就是這張表的 bug」，
而 `C-16` 已經示範過「一個 gate 關了但它沒關」要同樣處理。
**這次是當天就套用，不是幾個 gate 之後才發現。**

`R1h` 一支 payload（`probe3`）一次上機，而**那次上機跟 `R3` 共用**，
四件事一起買：`CPU-25` 幾何、`CPU-45` 一致性（就是決定②）、`CPU-44` `cache` 會不會
retire、`CPU-19` 殘留。步驟表、否證條件、stop-loss 都在進 gate 的今天寫好了。

⚠️ **排程上有一條硬約束**：`R1g-4b` 量到 **loader 在 watchdog 重置時也會把
`0x80500000` 重新搬一次**，所以一次開機不重新上傳就跑不了第二支 payload。
`R3` 跟 `probe3` 各自要有自己的上傳步驟，而且 **`probe3` 先跑** ——
`R3` 把 kernel 開起來就是一次 seating 的結束。

### 八、今天的帳

零電源循環、零 flash 位元組。動到的檔案：`docs/rlx-cache-and-cp0.md`（新）、
`notes/cache-model.md`、`SPEC.md`（`CPU-19`、`CPU-20`–`CPU-24`、`CPU-25`、
新增 `CPU-43`–`CPU-45`、§0 的檢查表、§17）、`PROGRESS.md`、`RUNSHEET.md`、
`tools/spec-check.py`（C8＋M9）、`CHANGELOG.md`、`docs/FINDINGS.md`、`README.md`。
`python3 tools/spec-check.py` 九個控制全成立、零 finding；`bash tools/test-file-modes.sh` 3 passed。

**改 `probe2.c` 的註解時順手量了一件事**：那條註解寫「D-cache 是 write-through」，跟 `exc.S` 那個 `0x110F0000`／`0x10F00000` 同一類 —— **讀者拿來對讀數的數字**。改完重建，`probe2.bin` 出來 9,392 bytes、sha256 `78beb72f77f601…`，**與 `RUNSHEET.md` 記的、真的在矽片上跑過的那一支逐位元組相同**。所以「改註解不會重新雜湊二進位」這句話今天是量到的不是假設的，而且順帶證明這棵樹現在還重現得出那支 payload。

**還有一件今天沒做而該記下來的**：`bench/` 底下兩份 `PREDICTIONS-*.md` 也寫著「D-cache is write-through」（`2026-08-25/block1` 的四路表、`2026-08-25b/block0`）。**它們不改** —— 那是上機前寫下的東西，事後修改它就等於毀掉「事前」這個性質本身。`block1` 那張表其實還帶著括號裡的選言，是**結果**那一段把它丟掉的，這件事本身就說明問題不在預測而在轉述。

**今天最該記住的一句**：這一天的三個發現 —— write-through 讀寬了、否證條件成立、
CCTL 的名字 —— **全部來自「把已經有的儀器指向還沒指過的那份 artefact」**，
沒有一個需要新資料、新硬體或一次通電。**`stage2.bin` 是 56,592 bytes，這台是 4 MiB，
而這個 gate 關於快取的每一句話都是在那 56 KB 上做出來的。**

---

## 2026-08-26（桌面，第二段）— `R1h-0`：`probe3` 的格子表，而寫格子表否證了這張表本來要站的兩塊地板

桌面，不通電，零 flash 位元組，零電源循環。產出 `docs/probe3-cells.md`：十一節，
每一格的期望值與否證條件寫在格子之前，每個期望值指名它是從哪一份 capture 或哪一份
artefact 來的，**「qemu 上預期」與「裝置上預期」分成兩欄**，理由是 `probe1` cell 1
在兩邊是相反的（qemu `02` FRESH、矽片 `01` STALE），而那正是它成立的理由。

**開場的四個決定都問過並照著做**：格子表落在新開的 `docs/probe3-cells.md`（`R1h-2`
之後再從它抄出 runsheet 段落）；兩支 walk 都做而 D 側由 payload 自己閘控；ⓓ② 進
payload 但**只寫 `IsC` 不寫 `SwC`**；花一格讀 SoC 的自由跑計時器。中途又問了三件，
三件都改了原本的計畫：`0x020` 放行當控制組、加一格讀 CP3、`RLX4181` 的禁令不動。

### 一、預測與機制講的是不同的快取

`PROGRESS.md` 把 ⓐ 寫成「用 `probe1` cell 1 證明的機制去掃 N 和 S」，而那個機制
（寫進指令流的 store 看不到）量的是 **I 側**；而現成那個「要被否證的預測」——
D-cache 8 KiB、line 16 B，切自這台自己的 kernel —— 是 **D 側**。
**照原樣做的那支 walk，永遠否證不了為它寫的那個預測。**

修法不是改預測，是帶兩支 walk。D 側那支唯一可用的觀測管道就是 KSEG0/KSEG1 別名，
也就是 cell A 正在測的那個東西 —— 所以它是 A 的下游，而且**由 payload 在執行期閘控**：
A 沒量到 stale line，D walk 每一格都會回 fresh，而那與「沒有 D-cache」讀起來一樣。

### 二、這顆上有一塊 16 KiB 的指令 scratchpad，而它和預測中的 I-cache 一樣大

這個 repo 從來沒有任何一列記過它。找到它的路是去問 `CCTL 0x010`／`0x020` 是什麼。

**它們有名字了，而且它們根本不是快取命令。** `0x010 = IMEM0FILL`、
`0x020 = IMEM0OFF`。四個來源，其中兩個彼此獨立：

1. **`arch/rlx/include/asm/rlxregs.h:630-638`**，就在**已經在手的三份 GPL drop** 裡。
   ⚠️ 三份逐位元組相同（md5 `623d85d7…`），和 `cache-rlx.c` 同一個 SDK 祖先 ——
   **一票不是三票**。
2. **Lexra LX4189 Data Sheet Rel 1.9 §5.2**，位元圖加語意散文。核心廠商的文件，
   與 1 獨立。
3. **`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` §1／§2／方塊圖**：「16Kbyte I-MEM,
   8Kbyte D-MEM」—— 而 **`SOURCES.json:195` 從索引寫下來那天就逐字引著這句**。
4. 🔴 **這台自己的 kernel `0x80002210`–`0x80002300`** —— 行為。

第 4 個是把名字變成解釋的那一個：設 `CU3` → `CCTL 0x020` → `CCTL 0x202` →
把 `0x002B8000`＋`0x3FFF`（**16 KiB**）寫進 `CP3 $0`／`$1` → 發 `CCTL 0x010` →
再把 `0x002C0000`＋`0x1FFF`（**8 KiB**）寫進 `$4`／`$5`。
**兩個尺寸與資料表的 I-MEM／D-MEM 逐一吻合，CCTL 是 clear-then-set，
而 `CU3` 就設在第一條 `mtc3` 前面。名字與行為互相解釋。**

**又是 `arch/rlx/` 那個失誤。** `notes/cache-model.md` 寫過「還開著的路是一份會講的
文件」—— 而那份 Realtek 的命名檔就在樹裡，和它已經在讀的 `cache-rlx.c` 同一棵。
**事實在專案裡，搜尋去了別的地方。** 這是第二次了，值得當成一條規則寫下來：
**在說「沒有來源」之前，先 grep 一次自己手上的東西。**

**而後果是第一級的**：LX4189 說「IMEM 無效時，IMEM 區域的可快取 fetch 才由 I-cache
服務」—— 反過來讀就是**有效時不由 I-cache 服務**。而 **I-MEM 16 KiB，預測的 I-cache
也是 16 KiB**，所以任何「大小」量測都分不開這兩個結構。三格新的格子處理它：讀 CP3、
發 `CCTL 0x020` 再跑一次同一支 walk、以及把它寫成整張表的成立條件。

⚠️ 一個回頭看的安慰，而且只是安慰：`probe1` cell 2（`CCTL 0x002`）兩個 victim 都
`02` FRESH，而 IInval 應該不碰 IMEM，所以 `probe1` 的 victim 大概不在 IMEM 窗口裡。
**推，關於 `probe1` 的位址，不轉移到 `probe3` 的任何一個位址。**

### 三、順手量到的：這台的 loader 一條 COP3 都沒有

掃 `stage2.bin` 的 primary opcode `0x13`：97 個命中，**全部是資料** —— 全部 ≥
`0x8040A5B8`（`CPU-26` 早就把那裡定為資料區的起點），而且全部是 ASCII（`"LOT\n"`、
`"NIC_"`、`"MX25"`）。**所以 loader 是對著 reset 預設的 BASE/TOP 發那兩個命令。**

⚠️ 那個零的控制比這個專案平常的弱，而說出來就是重點：同一支掃描器在 kernel 裡找得到
四條乾淨的 `mtc3`，**但那是另一個檔案**。`stage2.bin` 裡沒有已知的 COP3 可以讓它重現。
**零是零；儀器是在別的地方示範的。**

### 四、`CPU-25` 的來源盤點錯了，而且是往「來源更多」的方向錯

這一列從 2026-08-25 起寫「I-cache 大小：一票，第三方」。**`refs/` 那份資料表第一頁
就寫了 I 16 KiB／D 8 KiB，三個地方，而 `SOURCES.json:195` 早就引著。**
所以：**大小 讀×3；line 大小 讀×2（而且資料表不給）；
🔴 真正「任何來源都沒有」的那一格是關聯度。**

🔴 **而寫完之後自己抓到一個把這件事寫太強的地方，寫在這裡是因為它差一點就出貨了。**
`SOURCES.json` 對 `ds-rtl8196e-vex` 的 caveat 早就寫著：那是 **`-VE1/2/3` 版本，DRAM 是
MCM 內嵌的，而這台是外接 SDRAM（`MEM-01`，量），所以這台不是那顆零件**；`CPU-02` 量到
的封裝絲印也完全沒有版本後綴。撐得住的說法是：**同樣兩句話也出現在公開的
`RTL8196E-CG` 資料表**，所以這是**兩份 Realtek 文件、講同一個家族的兩個版本**，而
**這台屬於這個家族是量的**（`CPU-01`，×3）。兩份比一份強，仍然不是對這顆晶粒的讀數 ——
而這正是 ⓐ 還是一個 gate 的理由。⚠️ 但 `CPU-46` 的 I-MEM／D-MEM 有一條腿不受影響：
**這台自己的 kernel 把 `+0x3FFF`／`+0x1FFF` 寫進那四個 CP3 暫存器，那是切自這台的。**

### 五、`§②` 的「cell E 讓 cell A 可判讀」太強

E 只在 **write-back** 那個分支裡是 A 的正控制：E 若量到 store 被扣住，line 就是常駐的，
read-allocate 為真，A 的 *fresh* 只能是「別名被 snoop」。**E 若量到 write-through，
它對常駐與否一句話都沒說**，A 的 *fresh* 仍是二選一 —— 而「不 read-allocate」與
「別名被 snoop」**只有真的 bus master 分得開**。對 `R6` 它們等價，前提是真的 DMA 寫
從快取那一側看起來像 uncached CPU store，**而那個前提要等 `R6` 用真引擎重測**。
Group C 因此從五格長到七格（多了 A′、F、E2），而且 **A 為負時 B／C／D／F 不可否證，
記 void 不記 pass**。

`c-F`（`CCTL 0x100` `DWB`）同時是兩件事：這個 repo 從來沒量過的一個命令的效果，
以及 `c-C`（`CCTL 0x001` 整顆 D-cache 不寫回作廢）的安全前置 —— **安全措施本身就是
一次量測**，這是今天最喜歡的一個安排。

### 六、儀器與預算

**`TC0CNT`（`0xB8003108`）** 進來當一個新儀器，而它的極限先寫下來：70 ns／LSB、
9.9998 ms 回繞、**模數 142,858 不是 2 的冪**（遮 28 bit 是錯的）。
**單次存取永遠量不到，只能 loop-of-N。** 速率 **14.286057 MHz** —— 新開 `CLK-17`，
因為**一個 payload 實際要除的數字不可以只活在一條算式裡**。
🔴 **不是 `CLK-08b` 的 14.9650 MHz**，那是看門狗的時脈，差 4.75 %。
而 `CLK-02` 的名字對不上它自己引的資料表（D 的 “Base clock” 是除頻器的**輸出**），
也改了 —— 這是會讓下一個人反乘 14 倍的那種缺陷。

**qemu 那一欄是量出來的，不是猜的**（8.2.2、Malta、`PRId 00019300`、`Config 80008482`）：
`cache` 的 op 欄 **32 個值全部 retire** —— qemu 根本不解碼 op 欄，所以它對 ⓒ 兩個方向
都答不了，而且**它的答案會長得像確認**；KSEG0 與 KSEG1 的 SMC **都是 FRESH**；
alias 的 A 與 E 都回「相干」。🔴 **`否證 ⓐ` 的負控制在 qemu 上保證失敗**，
harness 不可以在那裡斷言它。順手也量到「看起來像保留」的編碼多半會 retire
（`0x78000000`、`0x00000005`、`0x70000000`、`0x7C000000` 全部 retire），
真的會吃 RI 的是 `0x0000000E`、`0x68000000`、`0x60000000`、`0xEC000000`。
而 **`rfe` 是反向控制** —— 它在 qemu 上吃 RI，在這顆上必須 retire。

**預算**：`--esc-after 60` 之下整份報告的牆是 **208,834 bytes**，`probe1` 那種每
victim 一列在 **2,006 個 victim** 撞牆，而且撞牆的樣子是**原廠核心開機**，讀起來像
payload 當掉。`DW` 有史以來最大是 **820 字／9,661 bytes**。編碼定為 **RAM 裡一個
victim 四位元的 nibble bitmap ＋ UART 摘要 ＋ 16 列具名全欄**：2,177 B 與 5,149 B，
**兩個數字都在這台已經做過的事情底下**。
🔴 **一位元的 bitmap 被否決，理由是它會殺掉一個已經發生過的發現**：`probe1` 有七種
verdict，而 cell 4 兩個 victim 都是 `07` CORRUPT —— 一位元的表會把它們記成一種快取
結果，`Status.IsC` 那個發現就不存在了。

### 七、犯的錯

**在 `SPEC.md` 裡犯了 `C8` 存在的理由本身。** 四個 §17 的列被我加成五欄，
還有一列在程式碼跨距裡寫了沒跳脫的 `` `Status |= CU3` `` —— 就是 `CPU-19` 從寫下來
那天起帶著的那個缺陷，昨天才補的 C8。**工具當場抓到，而且是先報「控制沒成立、
拒絕對這個檔做報告」**，不是報一個乾淨的結果。八個控制成立、一個沒成立的那一行，
比任何一條 finding 都有用。

### 收工

`python3 tools/spec-check.py` 九個控制全成立、零 finding；
`bash tools/test-file-modes.sh` 通過。動到的檔案：`docs/probe3-cells.md`（新）、
`notes/cache-model.md`、`docs/rlx-cache-and-cp0.md`、`SPEC.md`（`CPU-04`、`CPU-24`、
新增 `CPU-24` 殘留、`CPU-25`、`CPU-43`、`CPU-44`、`CPU-45`、新增 `CPU-46`、
`CPU-19` 殘留、`CLK-02`、新增 `CLK-17`、`REG-07`）、`PROGRESS.md`、`SOURCES.json`。

**今天最該記住的一句**：三個發現裡有兩個 —— `CCTL` 的名字、`CPU-25` 的來源 ——
**都是本來就在這個 repo 裡的東西**，一個在 `src-vendor/` 的樹裡，一個在
`SOURCES.json` 自己的第 195 行。昨天那一課是「把已經有的儀器指向還沒指過的
artefact」，今天這一課更難堪一點：**先看一遍自己已經寫下來的東西**。

### 附記（同一天，寫完之後）— 這張表被四支對抗性讀者掃過，而它們抓到會花掉那次電源循環的東西

寫完之後把 `docs/probe3-cells.md` 交給四個獨立的鏡頭去**否證**（物理、來源、控制組、
擁有權），每一條發現再送給一個專門殺它的裁決者。結果不好看，而那正是做這件事的理由 ——
**六個 blocker，其中至少兩個會直接花掉那一次與 `R3` 共用的電源循環**：

1. 🔴 **`c-C` 的 `CCTL 0x001` 會把 `$31` 的溢出位置丟掉。** `rlx_call2_uncached` 把
   `$31` 推到 **KSEG0** 的堆疊（`cache.S:363-365`）；write-back 分支下那條 line 是髒的；
   `DInval` 不寫回就作廢它；epilogue 的 `lw $31,0($29)` 讀到寫回前的 DRAM，`jr $31`
   跳進荒野 —— loader 的永久掛起，而且沒有 handler 救得了。**我原本寫的緩解（`c-F` 先跑）
   根本不成立**，因為 `c-B` 夾在中間，`c-F` 之後推的每一個 frame 又髒了。改成
   `DWB` 與 `DInval` 是同一個 leaf routine 裡連續兩條 `mtc0`，`$31` 全程在暫存器裡。
2. 🔴 **`m-imem` 會因為錯的理由 trap。** `m-cu3` 用完立刻還原 `Status`，而下一格
   `m-imem` 需要 `CU3` —— 我自己寫的 否證 M 是「若 `mfc3` 在 `CU3` 已設的情況下 trap」，
   照字面實作出來，Group M 的頭條發現會是排序的產物。
3. 🔴 **三個 line 大小的格子都沒有一個「必須成立」的讀數。** 唯一確定被 fetch 的位址
   （`V0` 自己）被排除在 patch 之外，所以沒有任何一格**必須**回 STALE —— 而 all FRESH
   同時是「line ≤ 8 B」「patch 沒落地」「re-arm 死了」三種東西的讀數。修法是把 `V0`
   自己的字也 patch 進去當 must-fire。
4. 🔴 **`w-back` 分不開 `L = 32` 與 `L = 16` 加一次 next-line prefetch** —— `+136` 在
   `[128,160)` 的**下半**，兩個假設 stale 同一段。加 `w-back2`，`V0` 放 `+152`（上半），
   兩個假設的 stale 集合就不相交了。
5. 🔴 **`c-E` 有 write buffer 的混淆**：write-through 加一個 posted write，uncached load
   可能超車讀到舊值 —— 看起來就是 write-back。而 `c-E2` 在 `DWB` 之後才讀，兩個假設下
   buffer 都已排空，所以**它是一支不會失敗的工具**。加 `c-E0`。
6. 🔴 **`c-E` 也依賴 `c-A`，而我把依賴寫成單向的**：`c-E` 的第二步假設它 allocate 了，
   而那正是 `c-A` 在量的。沒有 read-allocate 時那個 cached store 是 write **miss**，
   write-through 與 write-back-no-write-allocate 給同一個讀數 —— **正是 ⓓ① 存在要分開的
   那一對**。
7. 🔴 **`TC0CNT` 的計數欄位是 bits 31:4**（`REG-05` 量到 `TC0DATA = 142,858 << 4`），
   我整組計時都當成整個字在減。**差 16 倍，而且不會有任何東西發現。**
8. 🔴 **handler 原本排在第 4 站**，所以第 1–3 站（包含那次 `CCTL 0x020`）是在**沒有
   handler** 的情況下跑的 —— 而它的成本欄寫著「nothing，`probe2` 的，已量」。移到第 1 站。

另外還有一批：`t-hit` 原本掃 128 KiB、每格都是 compulsory miss，*相等*本來就是正確
矽片的預期讀數；`w-imem` 的「兩次相同」同時是 no-op 的讀數（CP0 20 唯寫讀 0，
**這支 payload 沒有任何一格能確認一條 `CCTL` 被接受**）；re-arm 的偵測器方向寫反了；
`P3` 的位元組數自己的算式對不上（23,527 不是 23,547）。

**這一節留在這裡，因為這個專案的規矩是被寫錯的紀錄要留著。** 而更該記住的是：
上面沒有任何一條需要新資料或一次通電 —— 它們全部是**把已經寫下來的東西讀第二遍**。
今天已經因為同樣的理由學過一次了。

## 2026-08-26（桌面，第三段）— 排程定案：上機併到 `R3` 尾部，所以 `R1h` 的桌面段到 `R1h-1` 為止

**桌面，不通電，零 flash 位元組。** 這一段沒有量到任何東西，記在這裡是因為
`CLAUDE.md` 的規矩：**桌面日也要寫，而桌面日正是下一次上機的計畫改變的那一天。**

**決定**：`probe3` 的上機與 `R3` 併在同一次，時間點是 **`R3` 的尾部**。
於是 `R1h` 的桌面段做到 **`R1h-1`** 為止，接著轉 **`R2a/b/d`**，
而 `R1h-2`／`-3`／`-4` 掛到 `R3` 那次上機的準備裡。

### 這不是翻掉計畫，是照計畫自己寫的那句話翻

`PROGRESS.md` § Now 從 `R1h` 開起來那天就寫著：

> ⚠️ **梯子上的下一格其實是 `R2a/b/d`**，它是桌面工作而且擋不住任何東西 ——
> 把 `R1h` 排在前面是一個**排程**決定……**這一條可以翻**

相依性上是乾淨的，三條都查過：`R3` 走的是原廠 kernel 已經開得起來的那層快取，
不需要 ⓐⓑⓒⓓ；`R5b` 需要的決定①（`CCTL 0x002`）2026-08-25 已經答了；
ⓑ 是 `R6` 的事。**沒有任何一格因為這個排法而變得更晚才能用。**

### 🔴 而排程一改，`R1h-2` 的定義就失效了 —— 這是今天真正做的事

`R1h-2` 產出的是「**寫進 `RUNSHEET.md`，擺在 `R3` 的旁邊**」，而 `R3` 的段落
還有 ~12 個 segment 才會存在；它的 DoD 是「`check-predictions.py` 在第一份
capture 之前寫好的 block 上通過」，那是**上機時才產生的東西**。
**一個 DoD 到不了的步驟不是步驟。** 所以 `R1h-2`／`-3`／`-4` 標 ⏸ 移出桌面段。

### 三件跟著寫進去的事

1. **`R1h` 會跨 `R2` 與 `R3` 保持開著，而那是刻意的不是卡住。** 寫下來，
   因為幾個月後的讀者（包含我）會把一個長期開著的 gate 讀成停住的。
2. 🔴 **`R1h-1` 多一個交付物：上機當天的重建程序。** payload 會在樹裡躺過兩個
   gate 才上機，而這個專案已經被這件事咬過 —— 量：`make P=probe2 payload
   RESULT_BASE=0x80A01000` 印 `Nothing to be done`，而樹裡那顆是 `0x80A00000`
   的建置。清空 build 目錄、重建、記 `sha256`、`rb=80a02000` 是檢查，
   **寫進檔案不是記在腦子裡**。`docs/probe3-cells.md` §10b。
3. 🔴 **container 那個 blocker 收窄了，而收窄是讓下一步開得了的原因。**
   它擋的是 **`R2c`**（三工具鏈比較），不是 `R2a/b/d` —— 後者是結構比對加兩個
   grep，5 個 segment，材料已經在磁碟上（`vmlinux-rederived.bin`，hash 錨定）。
   **`R1h-1` 之後那一步不會一開始就撞牆。**

### 一件講了三次的事，第三次寫進檔案

**那次上機裡 `probe3` 仍然先跑。** `R3` 的 DoD 是「kernel 開到 shell 並且
ping 得通」，而那個狀態下 loader 沒了、DRAM 沒了，沒有 `<RealTek>` 可以打 `J`、
也沒有 `DW` 撈得回結果區塊。**「`R3` 尾部」講的是哪一次上機，不是那一次裡面的
順序。** gate 開起來時的 stop-loss 就是這樣寫的，排程改不動它。

`PROGRESS.md`（§ Now、`R1h` 步驟表重切、§ Blocked on 收窄）、
`docs/probe3-cells.md` §10b（新）。


---

## 2026-08-26（桌面＋儀器，第四段）— `R1h-1`：`probe3` 建成並在 qemu 上跑到底，而核心廠商的資料表否證了格子表四件事

**桌面，不通電，零 flash 位元組，零電源循環。** `R1h` 的桌面段。

### 動手前先做完的三件事，順序就是被指定的那個順序

**③ 建置系統，而 `RESULT_BASE` 那一半刻意沒照原話做。**
四個位置照做：`ISC_probe3 := 0`、`PAYLOADS += probe3`、`SRC_probe3`、
`RB_WORDS_probe3`。但 `docs/probe3-cells.md` §10 原本寫的是
「**`probe3` 必須明確給 `0x80A02000`**」—— 那是一句給人看的指示，
而人會累。**改成兩個機制**：

1. **per-payload 預設**（`RESULT_BASE_probe3 := 0x80A02000`，命令列仍然贏），
   所以光打 `make P=probe3 payload` 就是對的；
2. **parse-time 拒絕** —— `RESULT_BASE` 指到別的 payload 的區塊就 `$(error)`。
   量 2026-08-26：`0x80A00000` 與 `0x80A01000` 兩個方向都會擋下來，
   而且**帶大小寫折疊**，因為 `0x80a00000` 是同一個位址，
   一個只認一種拼法的守門是下一個人會不小心繞過去的守門。

保護的是**測量**：`0x80A00000` 是 `probe1` 六格 `R1d` 的區塊，
`0x80A01000` 是 `probe2` 的 256 列 CP0 census，兩份都是從 DRAM 撈回來的。
**建錯 base 的 payload 不會失敗** —— 它會跑完、蓋掉別人的量測、
然後印出一份自己格式完全正確的區塊。

**① 三個未定的 qemu 欄，全部量掉。** 量(qemu) 2026-08-26,
`qemu/2026-08-26/probe3.txt`：

| 格子 | qemu 上量到 | 而它不只是填空 |
|---|---|---|
| `m-cu3` | `before = 00000000`、`set = 00000000` —— **bit 31 不會黏** | 同一次跑證明 `Status` 寫得進去（`CLEAR_BEV` 就是走同一條 routine 清掉 `BEV` 的）。**qemu 是一台「有寫入遮罩」的機器**，那正是 `s-isc` 需要的正控制 |
| `s-isc` | `set = 00000000` —— bit 16、bit 6、bit 24 三顆全部讀回為 0 | 同上 |
| Group T | `TC0CNT` 每次讀回 **`FFFFFFFF`**，每個 bracket 都是 0 | 🔴 **那不是「凍住」。** 值不等於任一個 prime，所以 load 確實寫了目的暫存器 —— Malta 那個位址**什麼都沒有**。**否證 T 因此多了第三種狀態**，而寫格子表的時候那一種不存在 |

**② 這個 repo 第一份被 commit 的 qemu capture。**
`qemu-run.sh` 從第一天就寫進 `mktemp -d`，所以「qemu 上預期」那一欄
一直只有散文加一條 CI 斷言撐著。現在：`qemu/` 是 `bench/` 的**平行目錄**，
自己的 README 寫明「這不是這台裝置的量測」；預設輸出改到
`tools/rlxprobe/build/qemu/`（gitignore 但活得過那次跑）；
`tools/audit-bench-log.py` 掃過那兩個檔（8/8 pattern 在合成控制上發射，0 命中）。
**`bench/` 保持只放矽片，而一個幾個月後掃 `bench/` 找讀數的人，
不必從檔名去推哪一份是模擬器。**

### 🔴 然後是今天真正的發現：LX4189 資料表被抓下來，而它否證了格子表四件事

`SOURCES.json` 的 `ds-lexra-lx4189` 條目原本結尾是
*「NOT DOWNLOADED INTO refs/: cited only. If it is ever fetched it moves to
documents WITH a sha256.」* —— 抓下來了（sha256 `6afb1415…`，
**PDF 不進 repo**，`CLAUDE.md` 禁止）。

⚠️ **而但書比原本記的更硬**：Table 2 列出 LX4189 全部的 CP0 暫存器是
8／12／13／14／15／20，**沒有 TLB**。這顆有 32 個 entry（`CPU-08` 量，
`probe2` census 的 `Random` 讀 5…29 佐證）。
**它是同廠的另一顆，而且是可證明地不是這顆。** 下面每一條都是「讀，關於一顆相關的核心」。

| | 文件說什麼 | 改掉什麼 |
|:-:|---|---|
| ① | §5.2：*"perform an uncached read … If the location is resident in the data cache it will be invalidated"*、*"a write to a KSEG1 address has no affect on the contents of the data cache"* | 🔴 **`c-E0`／`c-E2` 是壞的，而且會誤打誤撞否證掉 `CCTL 0x100`。** `c-E` 最後一步就是 uncached load，照 ① 它會把那條 line 作廢 —— 接在後面的 `c-E2` 發 `DWB` 時髒 line 已經不在，讀回 `P0` 會被記成「`0x100` 不寫回」。**那是執行順序製造出來的否證。** 三個 E 格子改成各跑各的完整序列。同一句話也給了 `c-A` 第一個期望值：**`l2 = P0`** |
| ② | 同上 | 🆕 **新格子 `c-G`。** ⓑ 問「這顆上有什麼能作廢一條乾淨的 line」，核心廠商的答案是 **uncached read**，不用任何 `CCTL`。五個 load、零條新指令；成立的話 `R6` 拿到一個一個 load 的 per-line 作廢原語 |
| ③ | §5.1／§5.6：line 可組態成 16／32／64／128 位元組（4／8／16／32 words） | 🔴 **`w-line` 的 void 門檻在錯的地方。** 原本探到 `+192` 就宣告「超出任何合理的 line」—— **128 位元組在這個家族是合法的**，那個門檻會把一條真的 128 位元組 line 記成 void。探針延伸到 `+320`，門檻移到 `+256` |
| ④ | §5.1 Table 18：`ICACHE` 是 *"Direct mapped or two-way set associative"*，`DCACHE` 只有 *"Direct mapped"* | 🔴 **關聯度不再是「任何來源都沒有，哪裡都沒有」。** I 側搜尋空間 **{1, 2}**，D 側預測 **direct-mapped**。`w-assoc`／`v-assoc` 從盲掃變成有預測可否證：**量到 K = 4 就否證這條血緣** |

**兩個不是更正的東西。**
🔴 **LX4189 的 `PRID` 是 `0x0000c401`**（Table 2）。這台讀 `0x0000CD01`。
那是這個專案手上**第一個** Lexra `PRId` 資料點 —— 它只說 `0xCD01` 不是 LX4189，
**一個點不是一張指派表，`CLAUDE.md` 的禁令一動也不動**。
以及 §3.4.2：*"Other exceptions, BEV = 0 → 0x8000_0080"*，
**第四個**互相獨立的 vector 來源，來自核心廠商。

### `s-isc` 的控制位元：定案，而來源就是那張 `STATUS` 圖

LX4189 §3.4.1 把 **27-23、21-16、7-6 全列為「0」欄位**，
散文寫 *"The 0 fields are ignored on write and are 0 on read"*。

**取 bit 6 與 bit 24，兩顆。** bit 6 在 LX4189 的「0」欄位 7-6 裡、
R3000 保留（`arch/rlx/include/asm/rlxregs.h:97` 的註解逐字寫
*"bits 6 & 7 are reserved on R[23]000"*，**Realtek 自己這個架構移植的標頭**）、
MIPS32 的 `SX` 是 MIPS64 專用；bit 24 在「0」欄位 27-23 裡、R3000 保留、
MIPS32 的 `MX` 是 DSP ASE 的存在位元。
**兩顆而不是一顆，因為一顆看不到「部分遮罩」** —— 它們在暫存器兩端，
遮罩不是一段連續解碼時，兩顆會互相不一致，而那是單一位元永遠產不出的讀數。

⚠️ **也要照實說**：嚴格講**沒有任何一顆位元「在兩張圖裡都沒畫」**。
bit 6／24 在 MIPS32 的圖上是有畫的，只是畫的是 64 位元與 ASE 欄位。
誠實的說法是「R3000 圖裡保留、MIPS32 圖裡是 64 位元／ASE 欄位、
核心廠商自己的圖裡是寫入被忽略的 0 欄位」，**寫作要照這句寫，不可以簡化成前一句**。

🔴 **而同一張圖把 bit 16 自己也放在「0」欄位裡** —— 在那顆 Lexra 上
`IsC`／`SwC` 根本不存在。所以裝置端的期望值也不再是留白：**bit 16 讀回為 0**。

### payload 本身，以及它自己咬到的三件事

`cells.S`（新，約 900 行）＋ `probe3.c`（新，約 1,300 行）。
過 `hazlint` gate，**804 個 load、0 violation**，在 qemu 上從 banner 跑到
`rlxprobe: end`，**5,866 位元組／125 行**。

1. 🔴 **asm 檔不能叫 `probe3.S`。** Makefile 把 `%.S` 與 `%.c` 對到同一個 `%.o`，
   所以 `probe3.S` 擺在 `probe3.c` 旁邊＝同一顆 object 被建兩次、連兩次、
   `ld` 吐一整頁 `multiple definition of`。改名 `cells.S`。**第一次建置就量到。**
2. 🔴 **第一版把 nibble 累加器放在 `$4`，那會在迴圈中途毀掉 `SAFE_A0` 的守門值。**
   `SAFE_A0` 只有在值還在的時候才是守門；把迴圈計數器放進 `$4` 就是
   把 loader 的 `do_reserved` 交給一個小整數當 `pt_regs *` ——
   **正是這個巨集存在的理由，被安裝它的程式碼重新引入。**
   規則寫進檔頭：**`SAFE_A0` 之後 `$4` 不再被寫。**
3. 🔴 **`flags` 裡的「跑在 KSEG0」位元被自己的建置標記蓋掉。**
   `FLAGS_W` 從 `0x50000000`（`'P'`）起跳，所以 bit 28 與 bit 30 每個建置都是 1，
   而 `0x40000000` 的 KSEG0 旗標永遠讀成 set。
   量：第一次 qemu 跑印 `flags=50070002`，
   **那條「NOT IN KSEG0 —— 每一格快取格子都作廢」的警告根本發不出來。**
   移到自己的標頭字 `H_KSEG0`。`FLAGS_W` 是**建置**標記，`make show` 印同一條算式，
   一個執行期位元不該住在裡面。

### 三個自我閘門，全部在 qemu 上照設計的方向發射

`h-brk`（handler 沒裝起來 → Group M 與 X 不跑）、
`c-A`（沒有 stale line → Group V 與 `c-B`/`c-C`/`c-D`/`c-F`/`c-G` **記 void 不記 pass**）、
`c-F`（`DWB` 不寫回 → `c-C` 不跑，而那是安全互鎖不是資料互鎖）。
量(qemu)：`g.ca=0`、`g.cf=0`，四個 C 格子印 `VOID 00000010`，
Group V 印出它為什麼不跑。**閘門在 qemu 上是可斷言的，而快取讀數不是。**

以及一個免費的檢查：**`w.arm.fresh=0`** ——
「重新武裝之後每個 victim 的第一次執行都必須回 OLD」這條偵測器
在 qemu 上也成立，所以「拆掉 `CCTL 0x002` 重新武裝」那個 mutation
**在 qemu 上是斷言得了的**。§6.2 說它免費，這次證明了。

### 動到的檔

`tools/rlxprobe/cells.S`（新）、`tools/rlxprobe/probe3.c`（新）、
`tools/rlxprobe/rlxdefs.h`、`tools/rlxprobe/Makefile`、`tools/rlxprobe/qemu-run.sh`、
`qemu/README.md`（新）、`qemu/2026-08-26/`（新）、
`docs/probe3-cells.md`、`SOURCES.json`、
`SPEC.md` `CPU-04`／`CPU-19` 殘留／`CPU-24` 殘留／`CPU-25`／`CPU-43`／`CPU-44`／
`CPU-45`／`CPU-46`／`CLK-17`。

### 收尾：suite 106 → 195,而 mutation 的數量不是照格子數的

**一個檢查機制一個 mutation,不是一格一個。** `docs/probe3-cells.md` §10 原本寫
「one mutation per cell」,而格子有大約四十個。真正的問題寫在同一份檔的 §6.2 裡:
**在這個 harness 上,大多數快取讀數變不變都一樣** —— W 群每一格在 qemu 上都是 FRESH、
C 群每一格讀同一個值、每一條 `cache` 都 retire。
**一個預測效果等於基線的 mutation 是不會失敗的 mutation**,四十個裡有一半是那種。

所以是**十二個 mutation ＋ 一張覆蓋表**,而覆蓋表最重要的一欄是
**「沒有任何 mutation 蓋得到的格子,與理由」** —— `w-line` 的 `V0`-only 武裝、
`w-back`/`w-back2` 的方向判別、兩支 sweep 的邊界與兩個 assoc、
**re-arm 的 `CCTL 0x002` 那一半**（TCG 在 store 當下就作廢 translation block,
所以拿掉 invalidate 讀數一模一樣 —— `QM2` 改成動「重寫」那一半,
證明的是偵測器**發得出來**,不是 invalidate 是必要的）、
三個 E 格子的寫入政策分支、`c-G`、`m-imem` 的雙 prime、`x-10` 的功能腿。
**那些格子在裝置上各自有自己的 must-fire 控制**,寫在它們自己的格子裡。
分工是:**qemu 檢查發射器,裝置檢查主張**,而那張表就是不讓兩者被搞混的地方。

六個 mutation **不需要模擬器**（`SM1`–`SM6`），這是在沒有 qemu 的機器上還活著的那一半,
也是**能斷言 qemu 的仁慈所遮蔽的東西**的那一半 —— `SM5`（`s-isc` 的控制位元）
就是一個**在 qemu 上完全沒有腿**的檢查:三顆位元設不設都讀回 0。

### 四個自己咬到的錯,其中一個是我今天自己種的

1. 🔴 **`make P=probe0` 被我自己加的區塊碰撞守門擋掉了。** probe0 **不寫結果區塊**
   （它的原始碼裡根本沒有 `RESULT_BASE`）,但它繼承和 probe1 同一個預設位址,
   而只排除 `$(P)` 的檢查看到 probe0 坐在 probe1 的區塊上就拒絕編譯。
   **一個會擋下不可能碰撞的 payload 的守門不是更嚴,是壞的。** suite 裡 probe0 的
   每一個案例同時紅掉才看見。
2. 🔴 **guardscan 的迴圈加了 probe3 卻沒有先建它**,掃描報 `SCANNED=0`,
   而那是**一個不會失敗的檢查** —— 正是這個迴圈存在的理由。
3. 🔴 **W2「cells.S 不碰堆疊」第一版用 awk 追「現在在哪個 routine 裡」,
   結果在一個一次都沒碰堆疊的檔案上報了 298 次**:名字不在清單裡的 C 函式
   全部算成 cells.S。改成從 `nm` 拿範圍 —— 一個 object 的 `.text` 是連續的,
   cells.S 的第一個符號是 victim template、最後一個是 `rlx_cctl2`,兩個邊界位址**就是**那個檔。
4. 🔴 **十七個斷言用 `$` 錨在行尾,而 capture 的每一行都以 `\r` 結尾。**
   `report.c` 每行輸出 `\r\n`,所以 `grep '...=00000000$'` 永遠不match。
   這個檔裡原有的 probe2 斷言全部沒有錨尾,現在知道為什麼了。
   **順帶：`.gitattributes` 也因此多了 `qemu/** -text`** —— 第一次 `git add` 就警告
   `CRLF will be replaced by LF`,那會從一份 125 行的 capture 裡拿掉 125 個位元組,
   而旁邊的 `.build` 檔記著它的 sha256。`bench/` 在 2026-08-23 學過同一課。

### 數字

`tools/test-rlxprobe.sh` **195 passed, 0 failed**（106 → 195）。
`ci-expected.tsv` 同步:bench total 195,`$FWRE_WORK` 清空時 **100 ok / 95 FAIL**（今天量的,
上一個數字是 2026-08-25 的 56/50）。九支 suite 全綠,`ci-census` 的算術收得起來。

### 還開著的一件事,寫清楚給下一段

🔴 **`hazlint --isa` 把 opcode `0x13` 標成 `COP1X (MIPS-IV)`。**
`0x13` 從 MIPS-II 起才是 COP1X,**在 MIPS-I 上它是 COP3** —— 而這顆是 MIPS-I
（`Config.M = 0`,量）,這台自己的 kernel 有四條 `mtc3`,`probe3` 的映像有八條 `mfc3`。
**標籤錯了,gate 沒錯**（gate 是 load-delay 檢查,那個是對的)。
修它會動到 `test-hazlint.sh` K6a/K6b/K6c 三個控制的期望數字 ——
它們數的是 `stage2.bin` 資料區的 loose/strict 命中,而 `0x13` 的分類一改那些數字就會變。
**那要重新量,不是重新猜。**
