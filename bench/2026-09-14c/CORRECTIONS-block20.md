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

All 27 carded cells ran in the order § 10 types them. `check-predictions`:
**27 of 27 came after the prediction, 0 did not**. `capdate`:
`bench/2026-09-14c`, 78 captures, all 2026-09-14. Three carded Linux boots plus
**four off-card ones** (X5, X6, X7 and one re-boot), every `looprun` closing
with **9 assertions and a 1,637-byte boot capture**, `RLXFW-ID0=692A2801`
printed by the board on all seven.

---

### 1.1 Slot 5 is ANSWERED, and the bracket is 0.010 s

Three holds, fitted over every sample with the button **down**, against the
model 0.11 reads out of `rtl_gpio.c` (dark → N ticks LIT → alternate, first
alternation level dark), with **N left free over 3…8**:

| hold | sampler | pressed samples | admissible `N` | `P` | `N·P` |
|---|---|---|---|---|---|
| `C2-H` | carded, bursty | 100 | **4 and 5** | 4: [1.001,1.006] · 5: [0.965,1.006] | 4: [4.004,4.024] · 5: [4.825,5.030] |
| `C3-H` | carded, bursty | 104 | **5** | [0.991, 1.009] | [4.955, 5.045] |
| `X6-lite-h` | off-card, 43.7 Hz | 562 | **5** | [0.999, 1.001] | [4.995, 5.005] |
| **intersection** | | | **5, uniquely** | **[0.999, 1.001]** | **[4.995, 5.005]** |

> **The steady-lit interval is 5.000 s, bracketed to 0.010 s.** The prior
> (`bench/2026-09-09b/X5-blink`, § 2) is `3.927 < L < 5.894` — **1.97 s wide.
> 197× narrower.** § 2 claimed ±0.164 s; the achieved half-width is **±0.005 s**.

🔴 **`C2-H` ALONE COULD NOT ANSWER IT.** It admits `N = 4` with a 4.0-second
steady interval as well as `N = 5` with a 5.0-second one — two different
answers. 0.2 treats the second hold as being about *repetition*; it is what
makes the first one **interpretable**. `PROBE_TIME 5` goes 讀 → 量.

`R5-e` does not fire: the three `N·P` intervals overlap. `R5-f` does not fire:
**zero** gaps ≤ 0 in any of the ten loop captures. `R5-g` does not fire.

**Prediction #1 was tested for the first time and only by the off-card
sampler.** The carded cells bracket the *press* to one burst gap — 1.12 s on
`C2-H`, 1.11 s on `C3-H` — which is as wide as the whole prediction interval,
so those two holds cannot test it either way. `X6-lite-h` brackets the press to
**0.02 s** and gives `t_on − t_press ∈ [1.245, 1.280] s`, i.e. **φ ∈ [0.245,
0.280] s**, inside the predicted (0, 1].

**#4 holds and is discriminated**: a LIT-first model fits **no** `(t_on, P)`
anywhere in the grid, on any of the three holds.

### 1.2 The carded sampler is not what § 5.2 models, and `C2-R` is what said so

`C2-R` and `C3-R` are **identical in every measured quantity** — 14,795 bytes,
25 samples, board span 3.59 s, and the same six-bucket gap histogram
`{0.01: 18, 0.02: 3, 1.11: 1, 1.12: 2}` on two independent boots. So the
following is deterministic, not a one-off.

🔴 **The samples are not evenly spaced.** Twenty-one of twenty-four intervals
are 10–20 ms and **three are ~1.11 s**. Host duration **4.342 s** and
**4.228 s** against § 5.2's band **[4.04, 4.14]** — outside on both boots.

**Two candidate causes, separated by one reading already in the artefacts**:
the host `.timing` shows `d_host` at **0.172–0.176 s for every sample including
the three the board stalls on**, an implied **3,340–3,415 B/s** throughout. The
wire never stops. So the board blocked on the console write — the tty buffer
filled and `cat` slept. The stalls fall at samples 8, 15, 22, **not** at the
5×5 outer-loop boundaries, and 7 samples × 588 bytes = **4,116 bytes ≈ one
4 KiB tty buffer**.

🔴 **So § 5.2's anti-aliasing argument does not hold.** *"6.12 Hz against a
1.000 s alternation is 6.12 samples per level, and the ratio is not an integer
or a half-integer"* is an argument about an **evenly spaced** sampler. The
effective sampling period for a 1 s square wave is the **burst** period,
~1.115 s, which is the worst available ratio. What rescues the carded holds is
that the bursts **drift** against the square wave, so a fit over every pressed
sample recovers what a run-length reading cannot — the same technique § 2 uses
on `X16`/`X17`, applied to this block's own data.

⚠️ **And a second number falls out, unasked**: sustained console throughput is
**588 bytes / 0.1735 s = 3,389 B/s**, which is **88.3 %** of 38400 8N1's
3,840 B/s, reproduced on two boots. Cause undetermined.

🟢 **The replacement, and it needed no card change**: `busybox grep -e ^dat`
instead of `cat`, so a sample is ~29 bytes instead of ~588. 量 `X-lite`:
**44.144 Hz**, gaps `{0.02: 36, 0.03: 13}`, **no stall**, implied 1,250 B/s —
a third of the line rate, so the buffer never fills. **49× the time
resolution.** `busybox seq` is **absent** on this image (`seq: applet not
found`, 量 — `FW-46` says there is no `--list`, so the only way to ask is to
run it), so the 900-iteration form uses `while [ $n -lt 900 ]`, which § 5.1
records `cardcheck`'s `B9` refusing **for a card** and which is legal in an
off-card `X*` cell.

### 1.3 Slot 4: 0.1's four inverted predictions are all confirmed, and the card would have written a false refutation

| cell | frozen card | 0.1, from the vendor source | measured |
|---|---|---|---|
| `C4-E2A` | `dat` unchanged `0000007C` | **`0000003C`** | **`0000003C`** |
| `C4-S1` | bit 6 **flat at 1** | **alternating, ~1.000 s** | **alternating**, `distinct dat ['0000003C','0000007C']`, 16 runs |
| `C4-E2B` | — | **`0000003C`** | **`0000003C`** |
| `C4-S2` | latched at whatever the hold left | **flat, bit 6 = 0** | **flat**, `distinct dat ['0000003C']`, 100 samples over 16.66 s |

🔴🔴 **`R4-5` reads a moving bit 6 in `C4-S1` as refuting `FW-62`'s
once-per-boot timer.** It is `FW-65` 殘留 ②'s positive half — `AutoCfg_LED_Blink`,
a different path through the same timer, started by a `/proc` write and not by
a press. **As frozen, the seating would have written a false refutation of
`FW-62` into the record.** It did not, because 0.1 was written before power.
The operator's eye confirmed the blink independently.

Card:303's escape hatch — *"If `dat` moves here … the two-armed test below is
void"* — fired, as 0.1 said it would.

### 1.4 The two-sided photon test, and the detector's freeze becomes a reading

`C4-E1` (`echo 1`): `dat 0000003C`, `foreign_seen 1`, `foreign_first 0000003C`,
`n_writes` **still 2** (`R4-4` does not fire), and **36 fields compared against
`C4-P0`, 5 differing**. The operator reported the LED **lit**.
`C4-E0` (`echo 0`): `dat 0000007C`, and the operator reported it **dark**.

> A guard that has only ever been seen refusing is a wall. This one was taken
> down and put back up, on the register **and** on the photon.

🟢 **§ 6's asserted *"`n_state_foreign` stops advancing"* is now measured**:
after `C4-E0` it read **7**, and stayed **7** across six further reads
(`X4-frozen`, `X4-b1`, `X4-b2`, `X4-e0b`, `X4-b3`, `C4-P1`).

### 1.5 `FW-64` gains a second half, and it explains a prediction that looked missed

`C4-E1`'s `n_state_foreign` moved **+1**, not the predicted **+2**.

量, four consecutive readings of two counters: **a printed counter comes from
`read_proc` #1 of the current `cat`, so it carries `read_proc` #2 of the
previous one.**

```
C4-P0      chk 3   foreign 0        C4-E1      chk 5   foreign 1
X4-again   chk 7   foreign 3        X4-again2  chk 9   foreign 5
```

`X4-again` and `X4-again2` were **registered before they ran** — `7 / 3` and
then the step — and both hit. So a steady-state per-`cat` delta is `+2`, and a
delta **spanning a state change is split 1/1 across two cats**. The card's `+2`
is right about the driver and wrong about what the print shows — 0.10's *"right
about the driver and placed under the wrong cell"* in a second form.

🟢 **Two further facts, each with its own control**:
* An `echo` costs **no** extra `state_check`. Registered: `X4-e0b` reads **21**
  if it does and **20** if it does not. It read **20**; `X4-b1`/`b2`/`b3` read
  16 / 18 / 22.
* `state_check` runs **once per `.get`** as well as once per `read_proc`. 量
  across `C4-S1` (100 cats), `X4-lite-blink` (600) and `C4-H`: 1,426 expected
  from reads, **1,827** observed, difference **401** — exactly `n_get`'s
  3 → 404. And `n_get 1` on `X5-P0`, whose payload has **no keys read**, against
  `3` on the three carded `*-P0` cells, measures the other half: **reading
  `/proc/rtl819x-keys` costs two `.get` calls**, which is why 0.10's `C11-P0`
  reads `1/1`.

🔴 **One residual, and it is a real call rather than a counter glitch**:
`n_state_chk` stepped `+3` instead of `+2` once in ten reads around `C4-E0`
and once in ninety-nine during `C4-S2`, and `n_state_foreign` stepped with it
both times — so something calls `state_check` about once per ~100 reads that is
neither a `read_proc` nor a `.get`. It needs the driver source; it is not a
bench question.

### 1.6 The AutoCfg override goes 推 → 量, and the consequence is not cosmetic

On boot 4 the operator reported the blink **not changing** during a hold while
`load_default` still went to 1. That is one human observation. `X7-lite-h` is
the same 43 Hz sampler with `AutoCfg_LED_Blink` armed, and its prediction was
registered in the runner before boot 7 existed: *alternation throughout, no
five-tick steady run, so the `N=5` model FAILS.*

量: **twenty consecutive half-periods, every one 0.96–0.99 s**, with the press
at `t0 = 749.04` making no difference at all —

```
dark 748.69..749.68  0.99   <- t0 - 0.35, the press
LIT  749.70..750.67  0.97   <- where the five-second steady run would begin
dark 750.69..751.67  0.98   <- it turns over anyway
```

`N` over 3…8: **none** admissible. The refutation condition (*the steady run
appears*) did not fire.

> **With `AutoCfg_LED_Blink` set, the reset button's LED indication is
> completely overridden — and `default_flag` is still written.** `C4-LD` read
> `1` on boot 4 and `X7-LD2` read `1` on boot 7. **The factory-default branch
> is reachable with no visual indication whatsoever.**

🟢 A **third, independent** route to the vendor tick period falls out: 19
half-periods over 18.99 s give `P ∈ (0.9984, 1.0005)`, from the AutoCfg path
with **no button involved**, agreeing with the two hold routes. **And the press
sits in the middle of those twenty half-periods without shifting the period**,
so the two paths share one timer and do not disturb it.

### 1.7 `FW-40`'s release semantics, bracketed on two boots

| | `load_default` | `dat` |
|---|---|---|
| `X6-LD`, `X7-LD` | **0** | `0000005C` — bit 5 = 0, **still pressed** |
| `X6-LD2`, `X7-LD2` | **1** | `0000007C` / `0000003C` |

A `0` read during a hold is not a missed press; **the flag is written on
release**. Eight readings over six boots, and `X5-P0` / `X6-P0` read `0` on
clean boots. `C2-LD` / `C3-LD` / `C4-LD` all read `1`.

### 1.8 `REG-37`'s latch is a coin flip, and the coin landed both ways

0.4 names it: the latched bit-6 value is the **parity of the final pressed
tick**, so *"fifteen seconds by your own clock"* makes it a coin flip no row
covers. Three holds with a post-release observation: **LIT, LIT, dark.**
`C2-P1` and `C3-P1` read `dat 0000003C`; `X6-LD2` reads `0000007C`. The
operator's eye agreed with the register on all three.

🟢 On `C2-H` the loop ended while the button was still down, so the instrument
has **no** post-release sample and the operator's report is the only
observation of the latch on that boot. That is `FW-63`'s own finding happening
again.

### 1.9 0.3 is confirmed on both sides

`C2-P1` and `C3-P1` read `b0_n_press 0`, `n_open 0`, `n_poll 0`, `j_first 0`,
`j_last 0` after fifteen-second holds — exactly as 0.3 says, because nothing on
those boots opens evdev. `C4-H` is the one cell that does, and it reads
**`n_open 1`, `n_poll 400`**, with `j_last − j_first = 1995` jiffies =
**19.95 s at 50 ms = 400 polls**. The mechanism is confirmed by a **rate**.

### 1.10 § 6b: both halves, and the negative control is the better half

```
C2-MM0  (before any kernel)              C4-MM1  (after three)
8103FFE0: 7561031D 71153577 F5573FDF  ->  00000080 00000001 FFFFFFFF 00000000
8103FFF0: 5F5711B0 56731757 7517D731  ->  00000000 00000000 81C01120 81FFF000
81040000: 575D1157 777353B7 55771555  ->  000424D2 777353B7 55771555 B3177351
81040010: BD151173 5B737255 5EBD73FF  ->  BD151173 5B737255 5EBD73FF 50531915
```

`C2-MM0` is bias garbage, so `MEM-17` retention did **not** pre-fill `mem_map`
and the test is live. `C4-MM1`'s `_mapcount` at `+0x08` is **`FFFFFFFF`** — the
one field the card predicts. `lru.next` is `81C01120`, **not** its own address,
which is the top page sitting on the buddy allocator's free list.

🟢🟢 **Seven of the eight words past the array are byte-identical between the
two reads.** That was free and it is the stronger half: it says the DRAM there
genuinely retained its pre-Linux content across three kernel boots, so the
change **inside** the array is Linux writing and not a read artefact — and it
says the 32-byte period **stops** at `0x8103FFFF`. `mem_map` is
`0x81000000`–`0x8103FFFF`, **measured**, and the derivation from
`MAX_DMA_ADDRESS` is confirmed on the device.

### 1.11 `C2-SI`: the line exists, four times, and that is weaker than "one"

量 `/proc/slabinfo`: **four** caches have `objperslab 15` — `ip_dst_cache`
(256), `inode_cache` (**264**), `size-256` (256), `size-192` (256). All four
`objsize` values are inside `SPEC.md:672`'s `{252, 256, 260, 264}`.

🔴 The card says *"**one** cache with `objperslab` 15"*. There are four, so the
reading is a **consistency check and not an identification**: the `struct slab`
at `0x81800000` is consistent with at least four candidate caches. The
refutation column (*no such line*) did not fire.

### 1.12 `C2-U`: the first `/proc/uptime` read on this device

**`24.79 18.68`** — **12 bytes** on the wire. 0.6 derives the length from
`seq_printf`'s format string as `d1 + d2 + 8`; with both integer parts at two
digits that is 12, against the card's ~15. **The derivation is confirmed and
the card's figure was 3 bytes high**, which is the half of 0.6's cancellation
that could be checked tonight.

### 1.13 What the seating could NOT settle

* 🔴 **`RLXFW-G3` bit 6 is not determined by anything this repository knows.**
  Five boots on one power cycle: `3C, 7C, 7C, 3C, 7C`, with **no correlation to
  what preceded the boot** — boot 5 followed Linux and read `3C` where boots 3
  and 4 followed Linux and read `7C`. `boot_dir FF000000` means bit 6 is an
  **input** when the driver reads it, so the bit is a pin level. An
  "after bare metal → lit, after Linux → dark" reading was formed mid-seating
  on three points and refuted by the fourth; it is recorded here because it was
  stated twice before it was refuted.
* **`REGIMM-1` was not attempted, and the reason is not time.** It needs a
  payload with an exception handler; every such payload here compiles its row
  table in and is frozen with a sha256 the card pins. Adding a row is a rebuild
  and a new binary with no frozen card — not the *"one payload row, riding an
  existing card, zero incremental bench cost"* the plan assumes. It carries
  forward to a desk segment that can give it a card.

### 1.14 The operator-timing finding, and it is a protocol defect

**Four holds. The two preceded by an explicit *ready* handshake landed inside
their sampling window; the two launched at the end of a long message did not.**

* `C4-H`: the press landed outside the 20-second evdev window. `n_poll 400`
  over `j_last − j_first = 19.95 s` **exonerates the driver by a rate** — a
  160-poll press cannot be missed — and `load_default` going 0 → 1 between
  `C4-H` and `C4-LD` proves the press happened, late. Card:476's *"launch time
  does not matter"* is false when the operator's reaction latency through the
  interface is comparable to the window.
* `X5-lite-h` (first attempt): same shape, 900 samples with `bit 5 = 1`
  throughout.
* 🔴 **And the retry cost a press for a different reason**: re-running the same
  script reused the same `--out` path, and `console-capture.py` **correctly
  refused to overwrite** (`rc=2`) the first attempt's artefacts. The board was
  never sent the payload. That is `looprun` 1.1's attempt-numbering discipline
  arriving in a hand-written runner; the fix is a new output name, not
  `--force`.

⚠️ `R4-6`'s single-cause attribution (*too short, or still holding*) missed
this third variant — **not yet started** — and its prescription, *re-run the
boot*, would have reproduced the failure exactly.

### 1.15 Defects in this seating's own instruments, all mine, all caught

1. 🔴 **A loop parser read decimal counters as hex.** `n_state_chk` printed a
   delta histogram summing to 766 against a first-to-last difference of 298;
   `0x454 − 0x156 = 766`, self-consistent. **It was caught because the sum did
   not match** — the one check the *pair of wrong numbers whose difference is
   right* class cannot survive.
2. 🔴 **The model fitter fitted post-release samples.** `FW-62` says the
   release consumes the timer, so the alternating model stops being the model;
   fitting past it reported *the model is refuted* on `C3-H` when what was
   refuted was the fitter. It failed in the safe direction — it refused rather
   than fitting something.
3. 🔴 **The fitter took `t0` as the press.** That is the card's own definition,
   and with a bursty sampler `t0` lags the press by up to one burst gap. It
   reported `#1 REFUTED` on `C2-H`; the correct verdict is *consistent, and
   untestable by this sampler*.
4. 🔴 **Display code hit the CRLF trap**, `grep -xE '[01]'` against a `1\r`
   line, with `tr -d '\r'` placed after the grep instead of before. Same family
   as `FW-47`; it printed an empty value rather than a wrong one.
5. 🔴 **A no-press capture crashed the N-sweep** on an empty list rather than
   refusing.

### 1.16 The flash, and it is the strongest sentence available

**Zero flash-write commands, zero `FLR`, `n_writes 2` in every gpio dump of
every boot.** The bracket stands at **1,024 of 4,194,304 = 0.0244 %**.

🟢 **An off-card `map 0` was taken** — card § 4 ⑥ states the absence of a map
cell *"so that its absence is not later read as a zero"*, and this fills it.
`bench/2026-09-14c/X7-M0`: **32 entries × 131,072 bytes** of address range,
`map_truncated 0`, `map_lines 32`, `map_rc 0`. ⚠️ **The hashed extent is
`map_hashed` = 4,186,112, not 4,194,304**: `map_h601_skipped 8192` and
`map_h601_hashed 0` — `H601` is excluded by rule and the map says so in its own
header.

Selected by the `sent` field in each capture's own `.meta.json` rather than by
filename, **nine `map 0` captures exist in the record and all nine agree**:

```
2026-09-08T22:38:43  2026-09-08T22:40:45  2026-09-09T03:29:44
2026-09-09T09:09:51  2026-09-09T09:17:20  2026-09-10T19:41:24
2026-09-10T21:03:07  2026-09-10T21:27:22  2026-09-14T22:29:58
```

🟢🟢 **And the comparison has a positive control, which `SPEC.md`'s `FLS-26`
row says the method needed and did not have** — *"那次成立是因為兩場的
`map_jiffies` 剛好相等 … 方法必須排除 `map_jiffies`，而它沒有寫下來"*. Written
down, as a check rather than a caution:

| | |
|---|---|
| distinct **whole-log** digests | **2** — so the comparison **can** see a difference |
| distinct **body** digests (first data line … `map_lines`) | **1** |
| the only header field that differs | **`map_jiffies` 1279 / 1280** — one 10 ms tick |
| the other fourteen header fields | single-valued, `map_diff_units 0` among them |

🟢 A reading nobody asked for falls out: the full map takes **1279–1280 jiffies
= 12.79–12.80 s**, reproducible to one tick over nine runs, five seatings and
six days.

Between the eighth capture and the ninth lie **four days**, **seating 21** (two
bare-metal payloads, two uploads) and **tonight** (two more uploads, seven
Linux boots, four button holds, five `/proc/gpio` writes). ⚠️ What that
establishes is what the map can see: 32 group digests over 4,186,112 bytes
agreeing. It cannot see two writes that cancel, it does not look at `H601` at
all, and **no `FLR` ran**.
