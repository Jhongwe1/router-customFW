# `PROGRESS.md` § `P1`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 181–355, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `P1`'s step list — ✅ CLOSED 2026-09-17, in 4 segments (81st–84th)

**Opened 2026-09-16** on the owner's decision, in the same segment `R1z` closed.
Its one-line definition is the gate board's: **`mfgtest` passes on a good unit,
and every check has been made to FAIL once.** The second half is the gate; the
first half is a demonstration. 讀 `plan/router-rebuild-plan.md` for the plan's
own check list, which this gate does **not** adopt unaltered — see ① below.

**Est. 11 段**, the plan's 小計, which `PROGRESS.md` § Gate board establishes is
the only estimate carrying `Actual`'s definition. ⚠️ Calibrated as a **band, not
a ratio**. 🔄 **Re-derived at `P1-0` from TEN points, not copied**, by a script
whose positive control is that the nine points § Gate board publishes reproduce
that line's own six figures exactly — they do. 🔴 **The tenth point is ONE gate,
not two**: `R1-pub + R2c` at 20/20 = 1.00× is a point; **`R1z` is not**, because
its own gate board row says it 沒有計畫數字可以校準 — the plan does not contain
that gate — so `3/3` compares a number to itself, excluded for the same reason
`P4b-gate` already is. 量: **min / max / spread do NOT move** (0.33× / 1.38× /
4.15× — the tenth lands inside), **mean 0.844× → 0.859×**, **median 0.833× →
0.917×**. So the band's integer edges hold and its centre moves: **4–15 段,
median ≈ 10**. ⚠️ A structure in that data was tested and is **not** used — the
plan's estimate looks better for bigger gates (Spearman ρ = −0.643 between plan
size and |ratio − 1|, permutation p = 0.049 against a pre-written 0.10, null
median |ρ| 0.238 at n = 10) — because size and recency are collinear here
(ρ = +0.486, measured) and n = 10 cannot separate *the estimator improved with
practice* from *big gates average out*. 🔴 **And that test's first control could
not fail**: one shuffle, scored *did it do worse than the real column*, which
passes on 95.1 % of draws by construction at p = 0.05. It is the null
distribution now. `docs/mfgtest.md` §6.

### What this gate inherits, with its marks

| | | mark |
|---|---|---|
| Six drivers of mine run on this die, each with a `/proc` surface and one `SPEC.md` id that proves it: timer `CLK-27`, GPIO `BRD-13`, SPI/MTD `FLS-26`/`FLS-27`, watchdog `FW-52`, ports `NET-12` | `SPEC.md`, `docs/GATE-RESULTS.md` | 量 |
| 🔄 **2026-09-16 (`P1-0`): this row said *the LED and the button have no `SPEC.md` id at all*, and 量 that is FALSE in the safe direction.** `BRD-05` (the button — `PABCD` bit 5, active-low with a pull-up, not `RESET#`, 量 2026-08-24) and `BRD-13` (the LED — #2 of eight on the board, active-low, 量 2026-09-09, the first time light entered this repository's evidence chain) both exist and are both 量, alongside `REG-28`, `REG-30`, `FW-40`, `FW-62`, `FW-63`, `FW-65`. **What is actually missing is narrower**: `rtl819x-keys` — the *driver* — has no id, and `BRD-13` is the *lamp's* row rather than the gpio driver's. So a check can cite which lamp and what polarity, and has nothing numbered to cite for the code that lit it | `SPEC.md` `BRD-05`/`BRD-13`, `docs/mfgtest.md` §5 | 量 |
| 🔴 Every `NET-*` reading is **loader-state, not Linux** | `SPEC.md` § NET | 讀 |
| 🔴 `open("/dev/watchdog")` itself arms the hardware, so a check that merely opens it has already changed the machine | `SPEC.md` `FW-52`, `notes/watchdog-driver.md` | 量 |
| 🔄 **2026-09-16 (`P1-0`): READ, and this row was wrong three ways.** 量: **`UDPserver` is NOT on this unit's flash** (`ls` → no such file; `grep -rl UDPserver` over the whole rootfs, binaries included, → nothing — the daemon ships only in the `3.4.0` images and `UDPserver.c` is from the GPL drop); there are **THIRTEEN** poke scripts, not twelve (`idd1` is byte-for-byte the same command as `id1`, a vendor copy-paste, and a census that counts twelve is silently dropping it); and **`mp.sh` is dead code here** — `etc/init.d/rcS` does not mention it. 🟢 What it tests and what it does **not** is now recorded, and the second half is the load-bearing one: no LED, no button, no flash integrity, no MAC *verification*. `SPEC.md` `FW-84`/`FW-85`, `docs/mfgtest.md` §0. *(Original row: the vendor has a manufacturing test on this unit's own flash — `bin/mp.sh`, twelve register-poke scripts, `users/mp-daemon/UDPserver.c` on UDP:9034 — and this repository has never recorded it — 量 2026-09-16, `git grep -in 'mp\.sh\|UDPserver\|9034'` returns nothing | this unit's extracted rootfs, the GPL drop | 量 |
| 🔄 **2026-09-16 (`P1-0`): REFUTED twice over.** It is **not the only** candidate — the live implementation is `apmib.c:547` — and it is **not a correct** one: its constants are `"hs"`/version 3, from a different SoC generation, where this board's are `"H6"`/**1**, which is where the name `H601` comes from. `SPEC.md` `FLS-28` now carries the structure (no byte of the window was read). *(Original row: `UDPserver.c`'s `PARAM_HEADER_T` with its commented-out `CHECKSUM()` is the **only** candidate specification for an `H601` checksum check — 量: there is **no committed parse of `H601`'s layout or checksum anywhere in this repository** | the GPL drop | 讀 |
| The mutation suites are the failure-injection precedent and their shape is exact: `str.replace(old, new, 1)` into a source copy, an anchor that must occur exactly once or the row is a SURVIVOR, and **kill is not `rc != 0` — it is *the check the row NAMES went red*** | `tools/test-*-mutants.py` | 讀 |

### 🔴 Three things this gate has to settle before a check is written

**① THE PLAN'S OWN CHECK LIST VIOLATES THIS PROJECT'S ZERO-FLASH-WRITE RULE, AND
NOTHING IN THE REPOSITORY HAS ADJUDICATED IT.** 讀 `plan/router-rebuild-plan.md`:
one line of `P1`'s check list is *`SPI NOR JEDEC ID` + 抹一個備用 sector 寫回讀
比對* — erase a spare sector, write it back, compare. `CLAUDE.md`'s Never table
says **mainline is zero-write through `R9`, and a write needs the owner's
explicit yes**; `P1` sits at cumulative segment 113 and `R8` at 224. 量
2026-09-16: `git grep '抹一個備用 sector'` gives two hits, the plan and a
2026-08-22 review, **and no adjudication anywhere**. **This is the owner's
decision and not an engineering one, and `P1-0` may not start until it is
made.** 🟢 A zero-write substitute is already built and is not a compromise
invented to dodge the question: `rtl819x-spi`'s `trywrite` verb calls
`mtd->write()` and `mtd->erase()` **through the pointers**, gets `-EOPNOTSUPP`
from both because `.flags = MTD_CAP_ROM`, and asserts `n_writes == 0` — so *the
write path is reachable and refuses* is a measurable check that writes nothing.

🟢 **ANSWERED 2026-09-16, and the answer is NO WRITE.** The owner was asked
and delegated the decision. 🔴 **A delegation is not an explicit yes to a
write**, and the Never table's own wording is what settles it: the permission it
demands was not given, so it does not exist. The line **splits**, because its two
halves are not the same kind of thing — **JEDEC ID is a read and stays** (as a
comparison against `FLS-04`'s registered `1C7016`, 量 2026-08-23, not as a
discovery), **erase-and-write-back is struck** and replaced by `trywrite`.
🔴 **And the plan holds a SECOND violation nothing here had noticed**: its DoD
names *清 MAC* as an example injection, 量 **one hit in the whole repository**
— the plan's own line — and no adjudication. Clearing the MAC writes `H601`,
which the Never table forbids touching at all. **Struck**, and its injection is
simulated at the boundary, which is what ③ below already prescribes.
⚠️ **What is given up is stated rather than argued away**: this unit's flash
writability is untested by this gate. `docs/mfgtest.md` §1 ①.

**② THE PLAN'S ENTRY METHOD DOES NOT EXIST ON THIS BOARD.** The plan offers
*hold the reset button, or add `mfg=1` to the kernel cmdline*. 讀
`docs/loader-command-semantics.md`: thirteen cmdline-shaped needles, **zero
hits**, against a scan demonstrated in the same run to find all seventeen loader
commands — *there is no environment mechanism, no storage for one, and no
command that sets one*. Three costed options are already tabled there. The
reset-strap route is better measured (`FW-40`, `FW-62`: the vendor's timer fires
**once per power-up**) but 讀 `FW-46`: the button's events have **no consumer in
this image** and `.to_irq` is NULL. **`P1-0` picks one and writes down what it
costs.**

🟢 **ANSWERED 2026-09-16, and none of the three options is needed, because
the question was the wrong one.** 讀, from the vendor's own build system:
**manufacturing mode on this SoC is a different image, chosen at build time** —
`MODEL_RTL8196E_MP` is a Kconfig **`choice` member** mutually exclusive with the
GW models, its entire `rcS` is 21 lines ending `mp.sh` + `UDPserver &`, and
`Makefile:188` skips `root.bin`, the web pages and `mkbin` entirely to ship a
bare **`MP_NFJROM`**. 🟢 **An `nfjrom` is a RAM-loaded image and it is exactly
what this project already ships** — `loudm` is the `rtkload` pipeline's own
`nfjrom` renamed. **So `mfgtest` is its own image, TFTP to RAM, entered with
`J`: there is no mode, no strap and no cmdline, because the image is the mode.**
Cost: one extra build-matrix entry, a different `RECIPE_ID` (so the boot-capture
byte count is **re-derived, not copied**), and the output must record **which NIC
driver ran**. Zero flash writes, zero new loader mechanisms.
🔴 **A fourth, uncosted mechanism was found and is rejected by measurement**:
`gCHKKEY_HIT` is a real console-key-at-power-on strap the loader already
implements (`REG-22`, 量 set) — and it is set by streaming ESC from before
power-on, which is what **every rlxfw seating already does** to catch the loader
prompt, so it would read 1 on every boot this project makes. *A mode signal that
is 1 in the workflow that would use it is not a mode signal.*
⚠️ **And the `FW-46` citation in this paragraph is wrong**: that row is about
`dd`/`md5sum`/`--list`, not about input events. The claim survives with a real
source — see the inherited-context table above and `SPEC.md` `FW-83`.
`docs/mfgtest.md` §1 ②.

**③ EVERY FAILURE-INJECTION PRECEDENT IN THIS REPOSITORY MUTATES SOFTWARE, AND
THIS GATE'S INJECTIONS ARE PHYSICAL ON A ONE-OF-A-KIND DEVICE.** The mutation
suites edit a copy of a source file; nothing is risked. *Every check has been
made to FAIL once* means provoking a real failure on the only unit this project
has. **So the design needs a column the precedent does not have: reversibility,
stated per injection before any of them runs** — and an injection that cannot be
shown reversible is either simulated at the boundary the check reads, or it is
recorded as not-done with the reason.

🟢 **DESIGNED 2026-09-16.** The owner authorised three classes and declined
the fourth: **P** physical, operator-performed, zero-risk (unplug, press, power
down); **R** register, through **my own** `/proc` verbs, where reversibility is
*a reboot restores the initial state* and that is 量 (seventeen byte-identical
boots, seating 20); **V** vendor driver or vendor state; and **not T** — anything
needing a tool, a short or an external source, so a row that would need one is
recorded **unfalsifiable-on-this-hardware**. 🆕 A fifth word the precedent does
not have: **S**, *simulated at the boundary the check reads*, for a check whose
physical failure cannot be produced without an irreversible act. 🔴 **`S` is
weaker than the rest and the table says so per row** — it proves the check's
decision logic, not that the check is wired to the peripheral — and four of the
eleven live rows are `S`. 🆕 A sixth verdict, **`NO-TAKE`**: the hardware
analogue of `INVALID-MUTANT`, *the injection did not happen*. The precedent is
unanimous that collapsing verdicts is how these harnesses go wrong.
`docs/mfgtest.md` §1 ③ and §3.

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`P1-0`** ✅ | desk 1 | **`mfgtest`'s own DoD, and the failure-injection design for every check.** One table: check id, what it reads, the peripheral and its `SPEC.md` id, the pass criterion, **how it is made to fail**, and **whether that injection is reversible on this unit**. Plus the three decisions above, each answered or explicitly the owner's | Every row has all six columns filled or is struck with a reason. ① is answered in writing by the owner. The 段 band is re-derived from ten points and not copied | 🟢 **CLOSED 2026-09-16, one desk segment against the one budgeted.** `docs/mfgtest.md`: eleven live rows with all six columns plus reversibility, one struck (`MT-DDR`, no owned surface, with the reason), the three decisions answered, and the band re-derived from ten points. 🔴 **And this cell's own prediction was REFUTED in the safe direction** — it said the LED and the button have no `SPEC.md` id; `BRD-05` and `BRD-13` are both 量, and what is actually missing is the *driver* id |
| **`P1-1`** ✅ | desk 2 | **The checks, as a tool that runs on the device.** One binary or script per the `P1-0` table, reading only surfaces this project owns | Each check prints one two-space `ok`/`FAIL` line; the tool refuses if it cannot identify the unit | **`FW-46`**: this image's busybox has no `dd`, no `md5sum`, no `--list`, so nothing on the device can digest a byte 🟢 **CLOSED 2026-09-17, one desk segment against the two budgeted.** `config/mfgtest.sh` -- nine checks, one two-space `ok`/`FAIL` line each, a `REFUSING` precondition that exits 2 rather than 1, and a DECLARED population so a phase that runs fewer checks than it declares is caught. Two new driver verbs (`rdid`, `h601`), a page budget for the first `/proc` file, and a `recipe_id` field that turns `MT-ID` into a device-side check. Built: `p11a`, ~~`RECIPE_ID` `c433013b`~~ **`b1818b92`** — 🔴 corrected in place 2026-09-17: the build log, the `-DRLXFW_SRC_ID` on the compiler line, the manifest and a recompute of `config/` all say `b1818b92`; `c433013b` was the build *before* `config/mfgtest.sh` existed and this row was never updated after the rebuild. The next card was about to predict `MT-ID` against it. Zero warnings on the driver, 12 marks verified. 🔴 **The blocking question was framed on a contract that does not exist** and the `C-3` excerpt it rested on was a partial view of its own routine -- see § Now. 🔴 **`CARD-4` closed, and NOT by widening the list**: 量, landing on `ASH_BUILTINS` still produced an issue that failed the card, so a wider guess would have changed the wording and not the verdict. Three outcomes now, 35 -> 39 cases, 22 -> 24 mutants, and **zero verdict changes on the committed corpus -- which is the correct outcome, because it means the widening papers over nothing** |
| **`P1-2`** ✅ | desk 2 | **The injection harness**, following the mutation-suite contract: every row NAMES the check it must turn red, and a row that turns a different one red is `WRONG-CASE`, not a pass | A `DECLARED` population constant; a `REFUSING` baseline case; `equivalent` rows must survive with a written proof | **That `rc != 0` is read as a kill.** The precedent says it is not, and this is the rule most likely to be simplified away 🟢 **CLOSED 2026-09-17, in the same segment.** `tools/mfginject.py`: 29 rows, **24 of 24 killed, 0 alive**, the must-survive row survived as proved, and five class-R/P rows stand down for `P1-4` as ONE skip line covering 5. Four controls plus a REFUSING B0 baseline. 🔴 **`C1` caught a real defect on its first run**: the timer driver emits `name=value` where every other driver here emits `name value`, so the script could not read a single field of `/proc/rtl819x-timer` -- **and the fixture had been written in the same wrong format as the parser, so the two agreed with each other and both disagreed with the die**. `C3` is `C2`'s negative half, because a command scanner that has stopped finding anything prints the same zero as one finding nothing wrong. Census reconciles: `ran 28/33, failed 0, not run 5` |
| **`P1-3`** ✅ | bench 1 | **The run on a good unit**, from a card frozen before power | Every check passes, and the boot capture's byte count is predicted before the seating | **`OPS-1`** — 量: a ready-handshake landed 2/2 and a `GO` at the end of a message landed 0/2, which is directly load-bearing for the LED and button checks 🟢 **CLOSED 2026-09-17, seating 25, one bench segment against the one budgeted.** **11 of 11 on a good unit** — nine automatic in `C1-AUTO2`, `MT-LED` with the operator reading LED #2 of eight lit and #1/#4 unchanged, `MT-BUTTON` with `n_open 1->2 n_poll 400->2200 b0_n_press 0->1`. Boot capture **1,637** bytes against 1,637 derived before power. 🔴 **Four of the eleven could not have gone green on a good unit** and are in `docs/mfgtest.md` § 9; the fourth was caught **by the good unit itself**, `C1-AUTO` returning `8 of 9` with a healthy tick |
| **`P1-4`** ✅ | bench 1–2 | **Every check made to FAIL once**, each injection reversed and the reversal verified before the next | Each check's red is observed and its `WRONG-CASE` control does not fire; the unit is byte-identical on the `FLR` bracket afterwards | 🔴 **This is the step that can brick the device.** An injection whose reversal is 推 rather than 量 does not run 🟢 **CLOSED 2026-09-17, same seating, and it cost no reset.** Five physical injections, **five real kills**, each specific and each with its revert measured before the next: `M25` `lock 6` (lamp stays lit through a `brightness←0`, `n_writes` unmoved), `M26` no press (`n_open` and `n_poll` MOVE, `b0_n_press` flat), `M27` `corrupt` (`diff_units=1`, only `MT-FLASH-3` red), `M28` `cereload` (`reload=20000 want=2000`), `M29` `stop` (`state=STOPPED`). 🔴 **Two of the five were `NO-TAKE`s against the implementation** and were re-specified before power — `M26` because nothing opened the input node, `M29` because `kickms` moves neither field `mt_wdt` reads |
| **`P1-5`** ✅ | desk ½ | **The write-up**, and `docs/GATE-RESULTS.md` gains its **eleventh** entry | The DoD read one row at a time; what the gate did **not** establish written; the operating clause re-run at eleven entries | 🟢 **CLOSED 2026-09-17, one desk half-segment against the half budgeted.** `docs/GATE-RESULTS.md`'s eleventh entry: `D1`–`D4` read one row at a time, three claims, eleven residual bullets, and the clause re-run over eleven entries — the new pair does **not** fire, because the one item `R1z` and `P1` share (`RECIPE_ID` moved / the next card must re-derive `RLXFW-ID0`) was **closed** by `P1` rather than carried. 🔴 **Three findings came out of the write-up itself**: § 2's table over-declares on three rows and only one had been caught (`FW-93`), the published map digest does not re-derive without `tr -d '\r'` (`FW-92`), and the class-`S` count is five where two files said four. 🔴 **And the tenth entry was handed a pre-registered decision and did not make it** — 量 by `git show 126f659`; it is made here, one entry late |

### The DoD, split into what can be refuted

* **D1** every check in the `P1-0` table reads a surface this project owns, with
  its `SPEC.md` id, or is struck with the reason it cannot.
* **D2** 🔴 **every check has been made to fail once, and the failure was the one
  the injection named** — a red that is not the named check's is `WRONG-CASE`
  and the row is not paid.
* **D3** 🔴 **zero flash-write commands unless ① is answered yes in writing**,
  and the `FLR` bracket is byte-identical across the gate.
* **D4** the injection design states reversibility per row **before** any
  injection runs, and every reversal is verified by measurement.

### Refutation condition, written now

> **否證 `D2`** — if a check cannot be made to fail without risking the unit, the
> honest output is that the check is **unfalsifiable on this hardware** and it
> leaves the tool. A check nobody can break is a check that proves nothing, and
> carrying it would make `mfgtest`'s green a claim about the tool rather than
> about the board.

> **否證 `D1`** — if the checks that survive ① and ② cover fewer peripherals than
> the six drivers this project already has on silicon, the gate is **smaller
> than the plan** and the honest output is to say so with the count.

### Stop-loss, written now

* **More than 15 段** — the top of the calibrated band — and the remaining checks
  are recorded as not-done with their reasons, not carried.
* 🔴 **More than 3 power cycles for `P1-4`** and the remaining injections are
  recorded as unfalsifiable-on-this-hardware rather than retried. One device, no
  spare.
* 🔴 **Any injection whose reversal is 推 rather than 量 does not run at all**,
  and this is a stop before the fact rather than a budget.
