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

### 下一步

`DAY-ZERO` 第 2b 項（快取模型，F49）。2a 已經先給了它兩個資料點：
`stage2` 程式碼區沒有任何 `cache` 指令，而 `mtc0`/`mfc0` 有 82 處，
其中 57 次是 `c0_status`、13 次是 CP0 reg 20。

第 1 項已於建立 manifest 時關閉；第 3 項其餘部分（submodule 釘 `4d3ff26`、
`fetch-sources.sh`、`README.md` 第一屏）仍開著。
