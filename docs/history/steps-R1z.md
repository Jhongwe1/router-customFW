# `PROGRESS.md` § `R1z`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 357–448, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R1z`'s step list — ✅ CLOSED 2026-09-16, in three segments (78th–80th)

**Opened 2026-09-16** on the owner's decision, in the same segment `R1-pub + R2c`
closed. 🔴 **The plan does not contain this gate.** `plan/router-rebuild-plan.md`
runs `R0`–`R10` and `P1`–`P4`, and none of them owns *the debts this
repository's own record names*. The precedent for a gate the plan does not
contain as such is `P4b-gate`, carved out on 2026-09-01 because `CHARTER.md`
§ 110's release obligations were owned by no gate; the shape here is the same
and the reason is stated rather than assumed.

🟢 **Its population is DERIVED, not chosen.** Every row of § Carried forward
whose owning gate is now closed, plus every debt the seventy-seventh segment's
`LOG.md` entry records. **That is the one thing `tccensus` did today that the
four checkers this segment found broken did not do** — a hand-picked list cannot
notice what was added to the record after the list was written.

**Est. 3 段.** ⚠️ That is an estimate and not a band: nine closed gates
calibrate at 0.33×–1.38× of the plan's number, and this gate **has no plan
number to calibrate against**, so the band cannot be computed. The stop-loss
below is what bounds it instead.

### What this gate inherits, with its marks

| | | mark |
|---|---|---|
| `§ Carried forward` is the owner of this project's debts, and a row with no owning gate is **that table's own bug** — which is why `R1h` was opened | `PROGRESS.md` § Carried forward | 讀 |
| `spec-check`'s `C12` has a recorded blind spot since before this gate, and the seventy-seventh segment measured **three more** | `C12-1`, `LOG.md` § 7b | 量 |
| A checker whose population comes from another instrument catches what a hand list cannot — 量 2026-09-16, `tccensus` caught three `SPEC.md` rows a hand list would have missed | `LOG.md` § 7c | 量 |
| `XNUM-1` carries a **pre-registered rule about its own third handover**, and `R1-pub-7` closed without doing it | `PROGRESS.md` § Carried forward | 讀 |

### 🔴 Two things this gate has to settle before a line of any checker changes

**① A checker this gate edits is a checker this project is currently working
around, and that order has already gone wrong once today.** The seventy-seventh
segment wrote *a checker I am working around should not be edited by me in the
same hour* — and then, while describing `C12`'s hole in the very row `C12`
reads, made `C12` go **green for the wrong reason**. **So every change here has
to be shown to make the checker STRICTER**, with a fixture the old version
passes and the new one catches. A change that only makes a checker quieter is
the failure this gate exists to prevent, committed by the gate itself.

**② `XNUM-1`'s rule fires on entry and must be APPLIED rather than quoted.**
Its own text: *this is the second handover, and a second handover is a signal —
if `R1-pub-7` hands it on again, the right action is to admit it will not be
done and record it as `⊘`, not to give it a third owner.* `R1-pub-7` closed on
2026-09-16 without doing it. **Putting it in this gate is doing it, not handing
it on — and the test of that sentence is whether it is done when this gate
closes.** If it is not, it is `⊘` and this row is why.

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R1z-0`** ✅ **2026-09-16** | desk 1 | **The population, derived and dated, before any fix.** Every `§ Carried forward` row whose owning gate is closed, every debt the seventy-seventh segment recorded, each with its owner and whether it is desk-only | The list is committed **before** any fix lands, so `git log` can check that nothing was added to it to match what got done — the `R1-pub-0` shape | **That it reads as a to-do list rather than a population.** If most rows turn out already closed, the honest output is that this gate is smaller than 3 段 and saying so |
| **`R1z-1`** ✅ **2026-09-16** | desk 1 | **`C12` sees what it claims to check.** Four measured holes: it reads nine steps of two CLOSED gates as open (`R4-0`…`R4-4`, `R1g-0`…`R1g-3` carry no per-step ✅); it matches only ids beginning `R` ＋ a digit, so a `P`-series step is invisible; it cannot tell a correction naming a closed step from a pointer at one; and `C12-1`'s decoration-before-the-id blind spot | **Each change carries a fixture the OLD version passes and the new one catches**, and the count of steps it treats as open is printed before and after. A change that catches nothing new is reverted | **That a fix makes it quieter.** The first three holes each make it too permissive; a fix that also loosens something is the thing ① forbids |
| **`R1z-2`** ✅ **2026-09-16** | desk 2 | **The record's own citations and owners.** `XNUM-1` (apply its rule), `RUN-1`, `UP-AUD-1` ~~③④~~ 🔴 **這兩個面是這一步的規格寫下來的**十三小時四十三分之前**就付掉的** —— 量：`ed7eb7a` 2026-09-15 23:31 付掉 ③④，而這一列由 `4dff849` 2026-09-16 13:14 寫下。**它不是漂移，是出生就過期**，而同一個形狀在 `docs/isa-prior-art.md` § 7 上連續發生三段。活的是 ①a①b②b⑤⑥b⑦a⑦b⑦c 八項，加上要建置的 ⑤c 與要搭 `RECIPE_ID` 車的 ⑦d, `docs/isa-prior-art.md` § 7's stale schedule table, and ~~`TC-57` naming an owner file that does not mention it~~ 🔴 **這一項被量測推翻，不是被付掉。** 量 2026-09-16：`TC-57` 的擁有者 `notes/userspace-probe.md` §1 確實 0 次出現「`TC-57`」這個字串，但它裝著整張證據表，而 `spec-check` 的 `C5`（值對擁有者檔重查，323 列）**通過**。全表掃描：364 個擁有者可寫的列裡，**137（37.6 %）的擁有者檔提到自己的 id，227 個不提**，而 `SPEC.md` 自己的開頭要求的是「語意、推導過程與否證條件都留在擁有者檔案裡」（引句而不引行號，理由就是同一個 commit 裡 `CITE-2` 的裁決：行號引用會腐爛，而這一個在一小時內就被 `citecheck` 拓到了） —— **沒有一個字要求 id 字串**。一支執行它的檢查器第一天就會燃 227 次。⚠️ 而追它的時候碰到隴壁一個真的：同一張三列 `libc.a` 表同時在 `notes/userspace-probe.md` §1 與 `docs/toolchain-comparison.md` §3.3，而後者是前者的讀者（它開頭就引 `TC-57`） | Every row ends ✅ done, `⊘` with a reason, or re-owned **with the handover counted**. No row leaves in the state it arrived in | **That a row is re-owned rather than done.** `XNUM-1` is the test case and it is already at two handovers 🔴 **2026-09-16：這一步被標成 `✅` 又被撤回，而撤回的理由就是它自己的 DoD。** 五十八列被處置、`XNUM-1` 照它自己的規則 `⊘`、`TCPAY-1` 付了 —— 但這一步點名的五項裡還有四項沒動：`RUN-1` 與 `UP-AUD-1` 仍然 `OPEN` 且擁有者欄逐字未變（**也就是「No row leaves in the state it arrived in」逐字不成立**），`docs/isa-prior-art.md` § 7 的過期時程表與 `TC-57` 指名一個沒有提到它的擁有者檔都沒被碰。量：這一段從未提交過 `docs/isa-prior-art.md`，而 `TC-57` 在 `docs/toolchain-comparison.md` 裡 4 處。🟢 **抱歉不是重點；重點是一個步驟的 `✅` 只能來自它自己的 DoD，而不是來自那一段做了很多事。**這個撤回是使用者問「下一段是不是 R1z-4」的時候才被抱到的 |
| **`R1z-3`** ✅ **2026-09-16** | desk 1 | **The instruments' debts.** `TCPAY-1`, `hazpay`'s `H28` passing for an accidental reason (its `mkout` zips `live`, not `noctl`, and the two coincide only because the `ctl` rows are last), and `special0e`'s `why` column `C2` → `C5` — whose expiry is *the first rebuild after `4a`'s re-run lands*, and the re-run has landed | Each carries a case that fails before the fix. `special0e` moves **only** in a rebuild, because its text feeds `cells4.S` and `BUILD_ID`, which two seatings' captures printed | **`special0e`.** It has been carried six times, each time for a correct reason. A seventh carry needs the reason restated, not repeated 🔄 **2026-09-16, and the ruling is that it is not a CARRY.** The handover rule's subject is *a change of owner*, and seven times the owner, the reason and the expiry have been identical; counting them counts segments elapsed. It is **blocked**, and the block is measured rather than asserted: that string goes verbatim into `cells4.S` and `BUILD_ID` covers that file, so changing it moves `a87be346bb83e7f9` → `43ddceb652831584` while three bench captures and two frozen cards cite the former. Doing it now would invalidate evidence to satisfy bookkeeping. It is a **rider on the next rebuild**, and its expiry is observable without a new tool: the first committed capture that prints a `BUILD_ID` other than `a87be346bb83e7f9`. 🔴 **No checker is built for it**, and that is a named absence rather than an oversight — a new instrument is outside this gate's scope, and a check that would be red until the next rebuild trains a reader to stop reading reds |
| **`R1z-4`** ✅ **2026-09-16** | desk ½ | **The write-up**, and `docs/KNOWN-ISSUES.md` gains what was NOT paid | The DoD read one row at a time; every unpaid row is `⊘` with a reason in `§ Carried forward`, not silently carried | — |

### The DoD, split into what can be refuted

* **D1** the population is derived from `§ Carried forward` and from the
  seventy-seventh segment's record, and is committed **before** any fix — so a
  row cannot be added to it to match work that was already done.
* **D2** 🔴 **every checker change is shown to make it STRICTER**, with a fixture
  the old version passes and the new one catches, and with the count of things
  it accepts printed before and after. **A change that catches nothing new is
  reverted**, and the finding is that the checker was right.
* **D3** every row this gate touches ends ✅, `⊘` with a reason, or re-owned with
  the handover counted. `XNUM-1`'s third-handover rule is **applied**.
* **D4** zero power cycles. Nothing here needs the board, and a step that turns
  out to need it leaves this gate rather than pulling a seating into it.

### Refutation condition, written now

> **否證 `D2`** — if a change to a checker lets through anything the old version
> caught, the change is **reverted** and the reading is that the checker was
> right and the row that provoked it was wrong. This is the direction the
> seventy-seventh segment got wrong by accident and it is written first here.

> **否證 `D1`** — if the derived population comes back mostly closed, this gate
> is **smaller than 3 段** and the honest output is to say so and close early,
> not to find work to fill it.

### Stop-loss, written now

* **More than 3 段** and every remaining row is recorded `⊘` with a reason
  rather than carried a further time. 🔴 **This gate exists because carrying is
  what went wrong**, so its own overrun may not be paid for by carrying.
* 🔴 **Any step that turns out to need the board leaves this gate**, named, and
  goes to the gate that owns the seating. A debt gate that spends a power cycle
  has become something else.
* **If `R1z-0` shows the population is under five live rows**, the gate closes
  in one segment with the count recorded.
