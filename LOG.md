# LOG

工作日誌，一次坐下來一則。**桌面日也寫** —— 桌面日正是下一次上機計畫改變的日子。

每一句話標記來源：**量到的**（在裝置上）、**讀出來的**（從程式碼或 dump 裡）、
**推測的，待量測**。三者混在一起就都不值錢。

**排序:由舊到新,一律 append。** 規則的擁有者是 `CLAUDE.md` 的收工那一節(*append a dated entry to `LOG.md`*),這裡只是指過去,不複製它。

🔄 **2026-09-02(第二十六段)把檔案改回服從那條規則。** 第二十四與二十五段當時寫在檔案最前面,而那從來不是一個決定 —— 沒有任何檔案寫過「新的在前」,只是第二十四段那樣做了、第二十五段跟著做。選「新的在前」等於回頭改 `CLAUDE.md` 去配合一次沒人決定過的漂移,所以改的是檔案。**這一次搬動只動那兩則(413 行);反過來做要倒轉 58 個條目、`git blame` 全毀。** 而拖延不是免費的:同樣這件事在第二十五段是 88 行,今天是 413。

---

**2026-10-09 起本檔只留當月的條目。** 更早的月份逐字搬到 `docs/log/<YYYY-MM>.md`，一個月一個檔，依條目標題的日期挑選；每個月第一次收工時把上個月的條目搬過去（`CLAUDE.md` § Closeout）。

## 2026-11-02 — 第一百五十段（04:2x 開場，桌面；零次電源動作，零次 flash 寫入，零次 `FLW`／`EW`／`EB`／非零 `AUTOBURN`／`FLR`）：擁有者問專案值不值得再做、能不能全自動收尾，然後把這一段的決定交給我；決定不重開 gate；`FW-235` 的三個檔還原到 pin，桌面唯一的非預期紅 `T13` 轉綠（`FW-277`）；十月的 36 則逐字搬進 `docs/log/2026-10.md`

**開場（04:2x，`/clear` 之後，擁有者）。** 兩個問題：「現在這個專案適合再做下去嗎 我手邊目前有機子」、「還是說不要按照之前的繁瑣規則 你自動把剩下做一做 我盡量讓你自動搞定 讓我忙其他事情」。回答之前先讀 repo：`PROGRESS.md` § Now 寫 closed、兩個 gate 的步驟表在 `docs/history/`；本地 `main` 比 `origin/main`（`60758038`）多一個 commit `c4f29814`（第一百四十九段之二的紀錄，還沒推，等 push 的 yes）；`gh issue view`（04:25:12，Windows 的鐘）：`shibajee/linux-rtl8196e#1` OPEN、0 則留言、最後更新 2026-10-18T17:59:46Z，跟 11-01 讀到的一樣；C: 剩 14.16 GB。回答：專案已經關了，剩下的分四類 —— 要外人的（`P5e` 的外部讀者測試、`P5e-7` 的回覆）、要擁有者在場的（`P6r-17` 的量測、`LA-1`）、桌面可全自動但關閉紀錄寫明對外無差的（`P6r-15`、`P6r-21`、`FW-235` 的三個檔、十月 LOG 搬家、vhdx 壓縮）、新功能（WAN／NAT、新核心、WiFi）；不建議為第三類重開 gate；最有價值且不花擁有者時間的一件是請一個外人跑 `REPRODUCE.md` 第 0 層；留給擁有者三個決定（推不推 `c4f29814`、要不要找外人、機子要不要用）。擁有者回：「本session都按照你的決定即可 用你最頂的工程思維」。

**這一句怎麼讀。** 交給我的是決定，不是對外動作的 yes（2026-10-09 的規則，第一百四十九段的交接也寫「每一個對外動作要那一個動作自己的 yes」），所以 push 留到收工問。電源與 flash 不動：這一段沒有任何事需要板子。`wsl --shutdown` 之後壓縮 vhdx：量 `ps`，WSL 裡正跑著擁有者另一個專案（`mctp-spdm-pqc`）的 `verify_repo.sh`、`pcapcount.py` 等程序，shutdown 會殺掉它們 —— 不做。

**決定與理由。** 不重開 gate，做兩件桌面的事。① `FW-235` 的三個檔還原：它的否證條件 2026-10-05 就寫好（「`--check` 回 0 或 `git status` 回空，就推翻這一列」），代價是一條 `git checkout`，收益是 tripwire 預設樹組上每一個包 tripwire 的建置不再在命令跑之前拒絕、desk-sweep 最後一個非預期紅（`T13`，`P5e-8` 的 DoD 事先排除的那一步）消失。它一直寫「恢復是擁有者的」，理由是那棵樹跟 `../router` 共用；所以先量 `../router`：它追蹤的 `.md`／`.sh`／`.py`／`.json` 沒有一個檔寫到 `users/miniigd` 或 `rtl819x-toolchain`（grep 0 個檔；它提到 `miniigd` 的 10 個檔都在講裝置上的 UPnP daemon），所以沒有它記錄過的決定會被撤銷。擁有者這一句把這一段的決定交給我，由我決定、記在這裡。② 十月的 LOG 搬 `docs/log/`：`CLAUDE.md` § Closeout 要在一個月的第一次收工搬上個月；第一百四十九段之二沒搬的理由（「不會有在十一月開場的一段」）在這一段開場的那一刻失效。不做的：`P6r-15`、`P6r-21`（關閉時的理由照舊；`bench/` 搬出樹會動 census、capdate 等讀 `bench/` 的套件，而收益對外是零）；上機（`P6r-17`、`LA-1` 要擁有者在場按電源、接線）；完整 desk-sweep（沒改任何工具或程式碼，放寬流程下只跑 CI 會跑的文件檢查）。

**還原（04:44:58）。** 量 `$FWRE_WORK/rebuild/s150/restore.sh`，由路徑執行，先驗 `HEAD` ＝ `5c9be5d943318fdb4d048ae22078129594eb5a10`、`git status --porcelain=v1 --ignored=matching` 恰 3 行且正是那三條 ` D`，任一不符就拒絕：`git checkout -- users/miniigd/miniigd_1.3.6-5281 users/miniigd/miniigd_4181 users/miniigd/miniigd_5281` rc 0；之後 porcelain 0 行；三個檔的 `git hash-object` 各等於 index 的 blob（`310ee1ff…`、`8bf25a92…`、`506aa6a6…`），mode 755，113,493／117,333／104,319 位元組，mtime 2026-11-02 04:44:58。`s150/tripwire-run.sh`：`tools/vendor-tripwire.sh --check` 從 `s150/scratch/` 跑 exit 0、`VENDOR-TRIPWIRE: CLEAN  6 tree(s) watched, 0 lines`；`bash tools/test-vendor-tripwire.sh` 從 repo 根目錄（`ci.yml` 的寫法）04:45:19–04:45:29：`RESULT: 30 passed, 0 failed, 1 skip line(s)`，主體 `ggbruno-openwrt`，`T13` 兩個 case ok（exit 0、6 棵樹），skip 的是 `T10`（要 `--live`）；對照 2026-10-31 sweep 的 `28 passed, 2 failed`，差的正是 `T13` 那兩個；套件跑完再 `--check` 一次 exit 0，六棵樹的 porcelain 各 0 行。成因仍然沒找到；三個檔的 mtime 現在是今天的。`SPEC.md` `FW-277`。

**搬 LOG。** `s150/edit.py`（每個錨點先驗恰好出現一次，全部驗過才寫，`.tmp` 之後 `os.replace`）：`LOG.md` 1,725 行 → 15 行（只剩檔頭）；`docs/log/2026-10.md` 1,719 行＝ 9 行檔頭（仿 `2026-09.md` 的）＋ 原第 16–1725 行逐字；36 則，標題日期 2026-10-02 到 2026-10-30；`docs/log/README.md` 加一列。`tools/docmove.py check --before HEAD:LOG.md --after LOG.md docs/log/2026-10.md`：CONSERVED —— 636 個 before-blocks、571 受檢、571 保留、0 遺失、65 short、0 allow。

**改了什麼。** `SPEC.md`：`FW-235` 的量測格尾加 🔄 指向 `FW-277`（同一行），`FW-277` 新列在 § 19 尾（第 1209 行，檔尾之後沒有被引用的行）。`notes/kernel-build.md`：髒樹那一節「Restoring it is the owner's」之後加一段（4,813 → 4,828 行；對它的三處行號引用 701–702、702、2516 都在插入點之上）。`docs/sbom.md` 第 100 行尾加一句、`REPRODUCE.md` 第 139 行的現在式改成過去式並指向 `FW-277`（兩檔行數不變）。`PROGRESS.md` § Now 第 19、20 列改寫：日期標成 2026-11-02（第一百五十段）、「Blocked on」拿掉「the owner's to restore」、`P6r-13` 的主題記為關閉後做掉（151 行不變；47,411 → 47,452 位元組，預算 48,900）。`notes/self-update.md` 第 84、832 行：`LOG.md:945`、`:971`、`LOG.md:1045` 改指 `docs/log/2026-10.md:939`、`:965`、`:1039` —— 搬動後舊號碼過了 `LOG.md` 的檔尾（citecheck C5 抓到），新舊行用 `cmp` 逐位元組相同（偏移 6 ＝ 9 行新檔頭 − 15 行舊檔頭），只改檔名與數字。

**檢查（第一輪，`s150/docchecks.sh`，04:50:28–04:56:13，寫這一則與修那兩處引用之前）。** `spec-check`、`docsize`（PROGRESS 47,452 of 48,900）、`cfcensus` 三個、`entrycheck report --offline`（E8w、E12、E13、E14w 照舊 UNMEASURED）、`modrecord check`、`ledgerscan` 兩個、`test-file-modes`（5 passed）、`flashwin`（8 個改動檔 CLEAN、113 個探針）、`digestscan scan`（0 findings、16 exempt）都 rc 0。兩個紅：`citecheck` C3／C5，就是上面那兩處引用；`git diff --check` 一行，`LOG.md:15` 的檔尾空行 —— 這一則接上去就沒了。第二輪在最後的樹上跑，結果寫在 commit 訊息，commit 之後的 `citecheck`（0 suspended）也是。

**做錯的事。** ① Git Bash 的 `grep -c '\\'` 想數腳本裡的反斜線，回「Trailing backslash」，什麼都沒數到；改用 WSL 的 `grep -nF 'x1b'` 逐行看。② 讀第一輪輸出時把 `citecheck.py.out` 寫成 `citecheck.out`，`sed` 找不到檔，多跑一次。③ 搬 LOG 之前沒有先掃活的檔（`notes/`、`docs/`）對 `LOG.md:N` 的引用 —— 第一百四十九段刪目錄前沒查文字引用是同一類錯，這次是 citecheck 第一輪才抓到兩處；搬之前該先 `git grep`。

**沒做、接下來。** push：`c4f29814` 與這一段的 commit 都還沒推，要擁有者對 push 的 yes；推上去之後兩輪 CI 的結論不會再有一則記。`wsl --shutdown` 後壓縮 vhdx（C: 14.16 GB）：WSL 正在跑擁有者另一個專案，沒做。`shibajee/linux-rtl8196e#1` 留在對方那裡。`P6r-15`、`P6r-21` 照關閉時的理由不做。第一百四十七到一百四十九段沒寫的 study 檔不補。
