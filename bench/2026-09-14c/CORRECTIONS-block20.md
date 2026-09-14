# CORRECTIONS — block 20, seating 22, 2026-09-14

Beside `PREDICTIONS-B21-block20.md`, which is frozen and was not touched.
`RUNSHEET.md`'s card-lifecycle rule 1 says corrections go here;
`tools/check-predictions.py:50-54` decides *written first* by the card's mtime,
so editing the card would void the ordering evidence for all 27 cells.

🔴 **§ 0 was written BEFORE power, before any cell ran, and is committed in a
commit that predates every capture in this directory.**
`bench/2026-09-14b/CORRECTIONS-block19.md` § 0.1 holds the measurement of why
that ordering is worth doing and what it does and does not establish; it is not
repeated here, because one piece of state has one owner.

🟢 **Every command on this card is correct as typed. Nothing below changes a
cell.** The findings are predictions, attributions and citations.

---

## 0. The pre-power audit

### 0.1 🔴🔴 Slot 4's two-armed test: four predictions are inverted, and as frozen the card would write a FALSE REFUTATION of `FW-62` into the record

**The cells**: `C4-E2A` (card:303), `C4-S1` (:304), `C4-E2B`/`C4-S2` (:306-307),
the refutation row `R4-5` (:322), and § 3's boot-4 rationale (:136).

**What the card predicts**: `echo 2 > /proc/gpio` leaves `dat` **unchanged at
`0000007C`**, and `C4-S1` then reads bit 6 **flat at 1**, because — quoting the
card's own cited ground — *"`FW-62` says it is not [alive]"*.

**What the vendor source says.** 讀, `rtl_gpio.c` in
`src-vendor/rtl819x-toolchain/linux-2.6.30/drivers/char/`, every link read
rather than taken on report:

| | |
|---|---|
| `:37` | `#define AUTO_CONFIG` — **file scope, unconditional**, so the `#ifdef AUTO_CONFIG` block at `:990` is compiled |
| the shipped image's `.config` | `CONFIG_RTL_8196E=y` (`$FWRE_WORK/rebuild/r3-4/cells/r59/top/linux-2.6.30/.config:7`) |
| the `CONFIG_RTL_8196D \|\| CONFIG_RTL_8196E` branch | `AUTOCFG_LED_PIN 6`, `RESET_BTN_PIN 5` |
| `:365` | `AUTOCFG_LED_DATABASE = PABCD_DAT` |
| `autoconfig_gpio_on()` | `RTL_W32(AUTOCFG_LED_DATABASE, (RTL_R32(AUTOCFG_LED_DATABASE) & (~(1 << AUTOCFG_LED_PIN))))` |
| `autoconfig_gpio_blink()` | **the same line, character for character**, then `AutoCfg_LED_Blink = 1; AutoCfg_LED_Toggle = 1; AutoCfg_LED_Slow_Blink = 0;` |
| `rtl_gpio_init()` | `init_timer(&probe_timer); probe_timer.function = &rtl_gpio_timer; mod_timer(&probe_timer, jiffies + HZ)` — **armed at init, unconditionally** |
| `rtl_gpio_timer()`'s last statement | `mod_timer(&probe_timer, jiffies + HZ);` — **outside** the `#ifdef AUTO_CONFIG`, so it re-arms whatever the button did |
| the toggle block, `:990-1040` | while `AutoCfg_LED_Blink == 1`: set bit 6 if `AutoCfg_LED_Toggle`, else clear it, then flip `AutoCfg_LED_Toggle`. `AutoCfg_LED_Slow_Blink` is 0, so there is no halving |

**So, corrected:**

| cell | card | 讀 |
|---|---|---|
| `C4-E2A` | `dat` unchanged, `0000007C` | **`0000003C`** — bit 6 cleared, by the same line `C4-E1` is predicted from |
| `C4-S1` | bit 6 flat at 1 | **bit 6 alternating, half-period 1.000 s**, first tick **set** (`blink()` leaves `Toggle = 1`) |
| `C4-E2B` | — | **`0000003C`** again; the write does not depend on the timer |
| `C4-S2` | latched at whatever the hold left | **flat, bit 6 = 0** — `C4-E2B`, typed ~40 s earlier, is why, so this arm cannot show a latch |

🔴 **The card predicts one value and `C4-E1` the other FROM THE SAME LINE OF
CODE.** That is the finding, not the individual numbers.

🔴 **And `R4-5` inverts a result into its opposite.** It reads: *"`C4-S1` shows
bit 6 moving with no press | `FW-62`'s once-per-boot timer, from a direction
seating 20 could not reach."* But `FW-62` is about the **reset-button** path —
a press held past ~2 s starting `probe_counter`, and a release consuming it.
The blink here is `AutoCfg_LED_Blink`, a **different path through the same
timer**, started by a `/proc` write and not by a press. A moving bit 6 in
`C4-S1` is `FW-65` 殘留 ②'s **positive** half landing where
`notes/gpio-driver.md:1313-1318` already predicts it, not a refutation of
anything. **As frozen, the two arms have zero discriminating power**, which is
the one property `SPEC.md:630` requires of them (*兩半互為控制*).

🟢 **The card's own escape hatch fires before power** and is what makes this
recordable rather than an argument: card:303 says *"If `dat` moves here … the
two-armed test below is void."* It moves. The test is void as framed and is
replaced above.

⚠️ **A consequence the card does not carry**: `AutoCfg_LED_Blink` is cleared
only by `autoconfig_gpio_on()`/`_off()`, so it stays 1 through `C4-H`.
**Boot 4's hold therefore blinks from tick 1 by the AutoCfg path**, which
removes § 3's discriminator (*"boot 4's hold will not blink"*) and any
steady-lit structure on that boot.

⚠️ **A small race, stated rather than discovered**: `C4-E2A` reads `dat`
immediately after the `echo`, and the timer fires once a second. The immediate
value is `0000003C`; a tick landing between the write and the read gives
`0000007C`. Both are consistent with the corrected model and neither is the
card's prediction.

**Refutation condition for this correction**: `C4-E2A` reads `0000007C` **and**
`C4-S1` is flat over ≥ 10 s. Either one alone is the race above; both together
mean `AUTO_CONFIG` is not in this build after all, and the source reading is
wrong.

### 0.2 🔴 Slot 5 returns n = 2, not n = 3

§ 3 (card:135) and prediction #7 (card:277) promise a third value of the
steady-lit interval from boot 4's hold. `C4-H`'s payload (card:476) is
`sleep 20 < /dev/input/event0 ; cat /proc/load_default ; cat
/proc/rtl819x-gpio` — **one** gpio read, taken after the release. There is no
time series during that hold, so no interval can be extracted; and per 0.1 that
hold blinks from tick 1 anyway. § 8 (card:383) already says the opposite of § 3
— *"`C2-H` (slot 5 has no other cell)"*.

`SPEC.md:629` asks for *一次夠長的按住* — one hold. **Three was the card's own
addition.** Slot 5 returns **two** values and the residual is answered to that
extent.

### 0.3 🔴 `C2-P1`/`C3-P1`'s stated expectation cannot exist: nothing on boots 2 and 3 opens `/dev/input/event0`

Card:447: *"after the hold: the ring carries the press and release in jiffies,
gpio carries the latch."*

`b0_n_press`, `b0_n_release`, `j_first` and `j_last` advance only inside
`rtl819x_keys_poll()`
(`config/rlxfw-src/linux-2.6.30/drivers/input/keyboard/rtl819x-keys.c:313`,
counters at `:354/:356/:367-370`), and polling starts only on an evdev **open**
(`:79`, `:91`). The only cell on this card that opens the node is `C4-H`.
Measured control: `bench/2026-09-10/C2-P.log` reads `n_open 0 / n_poll 0 /
j_first 0 / j_last 0 / b0_n_press 0 / b0_n_release 0`.

🔴 **A fifteen-second hold will report `b0_n_press 0`, which reads as a driver
or a button fault.** It is neither. On boots 2 and 3 the hold's only
observable is `dat` bit 5 sampled in the loop.

**Same root cause kills a claim in § 5.1**: card:206-208 says `n_state_chk`
/`n_state_foreign` give `notes/slots45-draft.md`'s **route ②** for free. Route
② (draft `:148-150`) needs the evdev node open at `interval 10`; no cell opens
it, no cell writes `interval`, and the default is 50 ms
(`rtl819x-keys.c:235`). During `C2-H`, `Δn_state_chk` is `+2` per sample
(`FW-64`) and carries nothing `dat` does not.

### 0.4 🔴 Prediction #5's number was superseded eleven minutes after the freeze

Card:275 predicts *"stays ≥ **152.1 s** | `REG-37`"*. `SPEC.md:330` now carries
**更正：那個區間是 139.251 秒，不是 152.1 秒** — 152.098 was a capture's
`duration_s`, which includes its `--idle 8.0` tail; the observed latch is
**139.251348 s**, so the card's figure is 9.2 % high.

Timeline from git: card frozen `d8e270a` **15:33:16**; the correction landed in
`44cff1c` **15:44:47**; the card was amended at 15:56:47 declaring *"No number
… changed"*. `git grep 152.1` still hits the card at `:275` and
`notes/slots45-draft.md:181`.

⚠️ **No cell observes either figure.** The longest post-release gpio
observation on boots 2/3 is `C2-H`'s ~7.5 s tail; on boot 4, `C4-E2B`
intervenes before `C4-S2`. Predictions **#5 and #6 also have no refutation
row** — `R5-b`…`R5-g` (card:281-288) cover neither. And by the mechanism at
`notes/gpio-driver.md:1203-1207` the latched bit-6 value is the **parity of the
final pressed tick**, so *"fifteen seconds by your own clock"* makes a latched
**0** a coin flip that no row covers.

### 0.5 🟠 Two stale `SPEC.md:NNN` citations, both broken by the commit that edited the card

| card | says it is | is, at HEAD | correct target |
|---|---|---|---|
| `:114` `SPEC.md:329` | *half-period 1 second* | `REG-36` (`0xB8003504`) | **`SPEC.md:330`** |
| `:339` `SPEC.md:669` | loader network buffer pool inference ＋ its § G hazard | `~~CPU-27~~ ✅` (`Status.BEV`) | **`SPEC.md:671`** (`MEM-11`) |

Both were **right at `d8e270a`**; `44cff1c` added three lines and shifted them.
⚠️ For `SPEC.md:671` a line bump is not enough — `MEM-11`'s text was rewritten
in that commit and no longer carries the inference the card describes.

🔴 **Third instance in one calendar day** (block 19's card carries three of its
own) **and nothing in the repository checks this class**: `spec-check` sweeps
`SPEC.md`'s own tables, `cardcheck numbers` reads only `cardnum` rows, and
neither looks at a `FILE:NNN` written in prose. `PROGRESS.md:1707` closed
`CITE-1` in the sixty-sixth segment — the segment that wrote both cards.

### 0.6 🟠 § 5.2's two inputs are both wrong and the errors cancel

Card:231-237. 量: the `/proc/rtl819x-gpio` dump is **574 bytes at rest** — it
reproduces in six committed captures — but 574 is the at-rest **minimum, not a
constant**: `n_get` and `n_state_chk` gain digits at `+2` per sample (`FW-64`),
and `X1-getg` (574) against `X2-getg` (575) differ in exactly
`n_state_chk 9` → `12`. Modelled over `C2-H`'s 150 iterations the mean is
**577.3** and the last is **578** — so the card is **3.3 bytes low**.

Against that, `/proc/uptime` is shorter than the card's ~15. 讀
`fs/proc/uptime.c:23` — `seq_printf(m, "%lu.%02lu %lu.%02lu\n", …)` — so the
wire length is `d1 + d2 + 8` where `d1`/`d2` are the two integer parts' digit
counts: **12 bytes** while both are two digits, 11 if idle drops under 10 s,
13 once uptime passes 99 s. At the ~30 s these cells run at it is **12**, so
the card is **3 bytes high**.

🔴 **The two errors cancel to 0.3 bytes per sample**: 574 ＋ 15 = 589 against
577.3 ＋ 12 = **589.3**. The bands therefore hold — 25 iter 4.035–4.135 s
(card 4.04–4.14), 150 iter 24.21–24.81 (card 24.2–24.8), 100 iter 16.14–16.54
(card 16.1–16.5) — **which is the finding, not a reprieve.** This is the *pair
of wrong numbers whose difference is right* shape in its purest form: neither
figure is a `cardnum` row, both are wrong, the model is right, and nothing in
this repository can see any of it.

⚠️ **The 13-byte figure was in this section's first draft and is wrong.** It
was relayed rather than re-derived; deriving it from the format string is what
produced the 12, and the correction makes the cancellation tighter rather than
looser. Recorded because the class — *a relayed number that reads like a
measurement* — is the one this project keeps finding in its own files.

### 0.7 🟠 `6.4×` and `± 0.164 s` in one sentence come from two different periods

Card:122. `X5-blink`'s measured period is 0.98227 s.
`0.98227 / 0.1634` (the full predicted sample period) = **6.01×**;
`0.98227 / 0.1534` (the **wire term only**, card:232) = **6.40×**, whose
one-sample bracket is **± 0.153**, not ± 0.164. Exactly one of the two numbers
in that sentence is right.

### 0.8 🟠 Three id collisions or silent re-purposings — the `NET-14` class

* **`R4-0`** collides with the existing project id at
  `bench/2026-09-01/PREDICTIONS-B7-block5.md:18` (the build-loop measurement),
  also in `CHANGELOG.md:1192` and `docs/GATE-RESULTS.md:611`.
* **`R4-5`** is re-used for an incompatible condition:
  `notes/slots45-draft.md:191` is *"the LED blinks **after** the hold"*;
  card:322 is *"bit 6 moving with no press"*. Arm B's refutation is dropped.
* **`R5-f`**: draft `:196` = *"the two routes disagree"*; card:287 =
  *"`/proc/uptime` does not advance"*.

### 0.9 🟠 `R4-6` is missing the branch `R5-d` carries

Card:323 attributes `C4-LD → load_default 0` solely to *"the hold was too short
or the operator was still holding"* and prescribes **re-run the boot**. Any
release with `probe_counter ≥ 2` **before** `C4-H` kills the timer permanently
(`rtl_gpio.c:963-975` — two `return;` paths that skip the `:1043`
`mod_timer`), and `REG-37` (`SPEC.md:330`) already carries an unrecorded short
press as an open candidate. `R5-d` (card:285) names exactly that branch for
slot 5; `R4-6` does not.

### 0.10 ⚠️ Smaller, recorded rather than repaired

* **`R4-3` is a single-cause attribution.** Card:320 reads a flat
  `n_state_foreign` as *"the detector cannot see the thing it was built for"*.
  All five helpers write `PABCD_DAT` only on the
  `sys_bonding_type() != BOND_8196ES` arm, which `docs/KNOWN-ISSUES.md:26` says
  *"is not understood by anything here"*. The arm is almost certainly taken
  (`REG-30` reads `0x0000000F`, and `X16`/`X17` measured the PABCD bit-6
  blink), but the card never names the alternative.
* **Freeze-order cross-reference off by one section.** Card:39 says *"§ 10
  carries the midnight rule"*; it is **§ 9** (card:392-402). Separately the
  list is written `1 2 3 4 5 7 6` with no blank line, so Markdown renumbers it
  and a reader sees the amendment as item 6.
* **"fifteen artefacts" outside the fence is 39 files.** `looprun.py:217-223`
  declares four capture prefixes plus `-rescue.json`, and
  `console-capture.py:432-434` writes `.log`/`.timing`/`.meta.json` for each →
  **13 per cell × 3 = 39**. The fence itself is correct; only the count in the
  justification is wrong.
* **`C2-SI`'s target is looser than its owner's.** Card:349 says
  `objsize ∈ [251, 267]`; `SPEC.md:672`, written 16:05 after the freeze, says
  **`{252, 256, 260, 264}`**. Score against the owner.
* **Three paraphrases inside quotation marks** — card:181 against
  `tools/cardcheck.py:26-28`, card:216-218 against `cardcheck.py:34-35`, and
  card:91 attributing `R4-0` to draft § 1 when it is draft § 4 `:189`.
* **The eye is missing.** `SPEC.md:630` and `notes/gpio-driver.md:1318` both
  ask for *"two `echo`s **and an eye**"*. No cell asks the operator to report
  what they saw — and `FW-63` is the finding that the operator's eye carried
  information no counter had. **Ask for it on boot 4.**
* **An undeclared departure.** The card runs slot 5 first and slot 4 second,
  reversing `docs/isa-prior-art.md:356-357`'s stated order without saying so.
  The card's reason (card:134) is better than the schedule's; it is the silence
  that is the defect.

### 0.11 🟢 Prediction #2's provenance is understated, and correcting it sharpens a refutation row

Card:272 gives the source for *"bit 6 then 0 for **5.000 s**"* as **"the
question itself"**. It is **讀**, with zero free parameters: `PROBE_TIME 5`
(`rtl_gpio.c:522`), the LED-on branch `2 <= C <= PROBE_TIME` (`:897`), the
parity branch `C & 1` (`:921-936`), and `mod_timer(&probe_timer, jiffies + HZ)`
(`:1043`) → lit on ticks with `C+1` = 2…6, **five ticks × 1.000 s**, first
alternation level **dark**. This repository had already derived it
(`notes/gpio-driver.md:1201-1221`, 2026-09-10), so it is code-first and not
fitted to `X5-blink`.

⚠️ **And as written `R5-b` (card:283) is an invalid inference**: a measured
interval that is *not* 5.000 s does not resurrect `T = 3.95/3.05/3.90`, a model
refuted structurally at `notes/gpio-driver.md:1236-1247`. With the 讀 mark the
row becomes sharp — a value other than 5.000 s refutes a **source reading**,
which is a much stronger thing to be able to say.

## 0.12 What the audit checked and found correct

| | result |
|---|---|
| `cardcheck.py commands` | rc 0 — `27 command(s): 2 LOADER, 25 SHELL; 18 invocable name(s); 6 declared absence-test(s)` |
| `cardcheck.py numbers` | rc 0 — **36 of 36 re-derived**, including the `T`-vs-`t` symbol types and every reference-log count |
| `check-predictions.py` | **`0 of 27`**, rc 1 — the correct pre-power value |
| `spec-check.py` | rc 0, read from inside a script file |
| **Class 1 — terminators** | clean. **No `--idle N` sits under a silence ≥ N** — seating 20's five-cell trap does not recur. The one `sleep` cell (`C4-H`) has `--seconds 45` and no `--idle`, byte-for-byte the shape of `bench/2026-09-10/X19-short` (45.07 s, `stop --seconds`). Loop cells: gap 0.163 s against `--idle 5`/`8`. All 27 carry a terminator |
| `--until 'val04'` | safe, **measured not argued**: `val04` occurs **0** times in a keys-only dump (`bench/2026-09-10/C12-O3.log`), and seating 20's ten pair reads all match at offset 1054 of 1072 — in the gpio tail |
| reset risk | the three `RB` cells all carry `--esc-after 20 --esc-period 0.002 --until '<RealTek>'`; nothing else on the card can reset the board. A 2–5 s release sends `SIGTERM` to PID 1, inert here (`FW-37`); the carded holds are 15 s and 8 s |
| board state across three boots | sound. Block 19 ends at the loader prompt; `looprun`'s `S4` sends `J BFC00000` and **assumes** that prompt; each `RB` cell hands it back. `looprun` refuses `--iterations 2` for this exact hazard (`looprun.py:1351-1369`), and three separate invocations are what make the evasion safe |
| the `looprun` command line | accepted. `--cell-top`/`--work` refusals are gated on `"S3" not in skip` (`looprun.py:552-565`), so `--skip S2,S3` needs neither — `LOOP-4b`'s defect is worked around; `--recipe-override 692a2801` must be lowercase and is; `--image-sha256` is verified before the port opens |
| the image | **exists**, 1,052,672 bytes, `sha256 c890e0ef…19fcb5` — byte-identical to the string typed in all three cells; `manifest.tsv` reads `recipe_id 692a2801` |
| `--idle 8` on the boot capture | closed by measurement: seventeen seating-20 `*-boot.timing` files, max inter-read gap **4.69–4.73 s**, last byte 10.80–10.88 s, all 1,637 bytes, all `stop=--idle 8.0 with no bytes`. **3.3 s of margin, seventeen times, on this exact image** |
| `R4-0` cannot fire | `create_proc_entry("gpio", 0, NULL)` with both handlers is unconditional for `CONFIG_RTL_8196E`; mode 0 → `S_IFREG\|S_IRUGO` and root has `CAP_DAC_OVERRIDE`; `echo 1` writes 2 bytes against `if (count < 2) return -EFAULT;` |
| `FW-64`'s factor of two | applied, at card:300 and :301 — confirmed against `rtl819x-gpio.c:687`, one `state_check` per `read_proc` |
| the fence | 27 rows, identical to the 27 `--out` cells and in the same order; no cell outside it |
| **midnight** | **unreachable.** Summing the cells' realistic durations gives **≈ 336 s ≈ 5.6 min of console time**; the card's *"~25 minutes"* is conservative by 4.5×. From a 19:00 start there are ~5 h of margin. Only the § 9/§ 10 pointer is wrong |
| instrument traps | no `ping -c`, no `awk`, no `dd`/`md5sum`, no `exec 3>`, no shell field comparison — so the CRLF `"1\r"` class, `FW-46`, `FW-41`/`FW-47` and the scientific-notation trap have no surface here |
| `_check_send` | longest payload **119** characters, against the 128 cliff |

### 0.13 What this audit did NOT check

* **Block 19.** Its own corrections file holds its audit. The one cross-card
  item is there: block 19's off-card round re-reads `0x80A05000`, which this
  block's first Linux boot overwrites, **so that round must finish before
  `C2`'s `looprun`.**
* **The physical path.** 量 17:07, the CP2102 is not in `usbipd`'s *Connected*
  list and `/dev/ttyUSB0` does not exist in WSL. The free board-off 3-second
  pre-flight is still owed before power.
* **Anything needing the device.** Every claim above is desk-side.
* ⚠️ **The tree was dirty during this audit** — `tools/rbcheck.py`,
  `tools/test-rbcheck.py`, `tools/ci-expected.tsv` and
  `.github/workflows/ci.yml`, none of them on tonight's path (`RB-1`). The
  freeze-order's *"gates green on a tree where this card is `git add`ed"* still
  describes the card and no longer describes the whole tree.

---

## 1. What the seating did differently

*(to be written after the cells run)*
