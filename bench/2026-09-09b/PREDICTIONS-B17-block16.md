# Block 16 — `R5-7`'s premise, measured with a human as the instrument; and a carried-forward repair that pointed the wrong way

**Written 2026-09-09, forty-eighth segment, at the desk, before power.**
Seating 19, **one power cycle**, five boots, four of which end in a watchdog
bite. **No new image**: the tree is the image that ran in seating 18.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4** — re-derive `RECIPE_ID` and compare with §1. If it moved, the
   image is stale and is **rebuilt**; the card is not edited to match.
   🟢 量 at 09:00 today, all three sources: `f67eed22`.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read **from a script file**
   and not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident).
   🔴 **And it runs on a tree where this card is already `git add`ed** — see
   §7, which is this card's own procedural change and the reason it exists.
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 13`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. It is `bench/2026-09-09b`, which asserts *the first capture happens
   before 00:00 on 2026-09-10*. This card was written at 09:34 on 2026-09-09,
   so the assertion has 14 hours of slack. `tools/capdate.py` checks it
   afterwards. ⚠️ **The suffix `b` is not decoration**: `bench/2026-09-09`
   already holds seating 18's 78 captures, and two seatings in one directory
   would make `capdate` green while destroying every per-seating count.

---

## 0. What this block is, in one paragraph

`R5-7` is `leds-rtl819x`. Its DoD is a `led_classdev` on **`PABCD` bit 6**.
This repository holds four independent readings of that bit — a register
alternating at 1 Hz (`REG-37`), the vendor's compiled blink code (`FW-40`), a
two-phase split across ten boot captures (`FW-40`, seating 16), and a datasheet
pin row (`BRD-06`) — and **not one of them is light**. `BRD-06`'s own wording is
*"所以在這個設計上它**可能**是一支 LED 驅動腳"*. So *"bit 6 is an LED"* is **推**
on a card that is about to build a driver on it. This block makes it 量, with
the operator's eye as the instrument, at a cost of **one boot and no new
image**. It then brackets that experiment with two flash maps, spends three
boots deciding whether seating 18's `OVSEL` 3 anomaly is systematic or jitter,
and spends one boot on a repair that seating 18 carried forward **pointing in
the wrong direction**.

---

## 1. The image, staged and pinned — unchanged from seating 18

| | |
|---|---|
| cell | `r57` |
| `RECIPE_ID` | **`f67eed22`** — the board must print `RLXFW-ID0=F67EED22` |
| `vmlinux` | 4,049,730 bytes, sha256 `ef7e8b57a46e06595d2516a4bb86611b93bec687a01ef0abb3de16d90dfc2254` |
| staged image | `/home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin` |
| image bytes | **1,043,456** |
| image sha256 | **`efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91`** |

🟢 **Rule 4's three sources all ran at the desk at 09:00 and all say
`f67eed22`**: the by-hand formula over `config/`, the build's own
`manifest.tsv`, and `--dry-run`.

🟢 **Nothing under `config/` was touched this segment before the freeze**, which
is why the boot-capture length prediction is **1,424 bytes** unchanged — the
same number thirteen captures hit in seating 18 and ten in seating 17. **That
makes it a control here rather than a prediction**: an image whose bytes did
not move must print the same length, and if it does not, the variable is the
board or the instrument and not the build.

---

## 2. §A — the LED, and why a register reading is not one

### 2.1 What is already known, with its marks

| | mark | source |
|---|---|---|
| `PABCD_DAT` bit 6 alternates with a 1 s half-period while the button is held; static at 1 when released; **cleared to 0 and latched** after a hold of ≥ 5 s | 量 | `SPEC.md` `REG-37`, seating 15 |
| The vendor's `rtl_gpio_timer` sets/clears bit 6 on `count & 1`, and on release at ≥ 5 s does `& ~0x40` and writes ASCII `'1'` into `default_flag` | 讀 (artefact) | `SPEC.md` `FW-40` |
| Ten boot captures fall into two sha256 values and the whole difference is `RLXFW-G3` bit 6 | 量 | `FW-40`, seating 16 |
| SoC pin 49 is shared between `RESET#`, `LED_PORT3` and `GPIOB[5]` | 讀 | `SPEC.md` `BRD-06` |
| `default_flag`'s only readers in this image are two `/proc` handlers | 讀 (artefact) | `FW-40` |

🔴 **None of these is a photon.** Three are the same register read by three
routes and the fourth is a document. `R5-7` would otherwise write a driver whose
acceptance observable is an inference.

### 2.2 The experiment

One hold of about **10 seconds**, with the operator watching the board, while
`C1-L1` takes three `dat` samples three seconds apart. The hold crosses the
≥ 5 s threshold **on purpose**, so one press produces both halves:

* **the blink** — `dat` bit 6 alternates during the hold;
* **the latch** — bit 6 is cleared on release and stays cleared, and
  `/proc/load_default` moves `0` → `1`.

⚠️ **Safety, stated rather than assumed.** A hold of ≥ 5 s is the vendor's
factory-reset gesture. On **this** image it writes one byte into a kernel
variable whose only readers are two `/proc` handlers (`FW-40`, 讀 artefact) and
seating 15 performed an ~8 s hold with `/proc/load_default` read afterwards, so
the act is 量-safe here. 🔴 **It is not safe on the vendor firmware**, where
that gesture reaches a userspace that writes flash. **This block never boots the
vendor firmware**, and §3's two flash maps are what turn that from an assurance
into a reading.

### 2.3 Predictions, and what refutes each

| cell | prediction | refuted by |
|---|---|---|
| `C1-G0` | `cnr FFFFFF8B`, `dir FF000040`, `btn_raw 1`, `btn_pressed 0`, `n_writes 0`, `allow_out_mask 00000000`, `base 0`, `ngpio 32`; `dat` = **`0000007C`**; `/proc/load_default` = **`0`** | `cnr`/`dir` differing refutes `REG-35`; `n_writes` ≠ 0 **stops the block**; `dat` = `0000003C` means bit 6 is 0 at rest on a never-pressed boot, which `REG-37`'s 27 released samples do not predict — **recorded, not repaired** |
| `C1-R0` | **the negative control, released**: three `dat` reads at 0/3/6 s, **all three identical** | any difference means bit 6 moves with the button released, which `REG-37`'s 27 released samples do not predict, and `C1-L1` then proves nothing |
| `C1-L1` | **the same command with the button held**: **bit 5 = 0 in all three** (low nibble `C`), and **not all three agree in bit 6**. **Operator: exactly one LED on the board changes state about once per second while held.** | any read with bit 5 = 1 means the hold lapsed — the cell is re-run, not reinterpreted. **Bit 6 moving with NO LED changing refutes `BRD-06`'s reading for this board** and `R5-7`'s target moves. Two or more LEDs alternating means bit 6 is not the only thing that timer drives |
| `C1-L2` | `/proc/load_default` = **`1`**; `dat` = **`0000003C`** (bit 6 clear, bit 5 back to 1). **Operator: the LED that was blinking is now dark and stays dark.** | `load_default` = `0` refutes the ≥ 5 s branch of `FW-40`; `dat` bit 6 = 1 refutes the `& ~0x40` on release |

### 2.4 🔴 Two things about the sampling that are stated, not left to be assumed

**① The exact phase pattern is NOT predicted, and that is a property of the
signal.** The vendor's timer toggles bit 6 once per second (`mod_timer(jiffies +
100)` at `HZ = 100`, 讀 `FW-40`), so the period is 2.000 s and *any* fixed sleep
that is a whole number of seconds samples a 1 Hz square wave at a multiple of its
own half-period. `sleep 3` ± the shell's own drift straddles a toggle boundary,
so a prediction of the form `v, ¬v, v` would be a coin flip dressed as
arithmetic. What is robust is the pair: **held → not all three agree; released →
all three agree.** A static bit cannot produce the first and a toggling bit
cannot produce the second, whatever the phase.

**② The first draft used `for i in 1 2 3 …; do busybox grep ^dat …; sleep 1;
done` — seating 15's own proven form — and `cardcheck commands` REFUSED it**:
*`for`: NOT IN IMAGE -- not among the 18 declared invocable names*. 🔴 The
declaration is `config/rlxfw-initramfs.tsv`, a list of **files in the image**,
and `for` is shell **grammar**, not a file. `ASH_BUILTINS` would not have helped
either — that list *reports* rather than passes, by design. **The only way to
make the loop pass is to edit a file under `config/`, which moves `RECIPE_ID`
and makes this image stale** — so the gate that says *your card is unbuildable*
and the gate that says *your command is undeclared* would have had to be
satisfied against each other. The card changed instead of the tool, twenty
minutes before power. ⚠️ **The tool gap is real and is carried forward**:
`cardcheck` has no category for a shell keyword, which is also why seating 15's
`X14`…`X17` loops were **off-card** — an oddity nobody had explained until now.

🟢 **The negative control is in the operator's own report and costs nothing**:
every other LED on the board must be unchanged between `C1-G0` and `C1-L2`. An
experiment in which the intended signal moves is worth much less than one in
which the intended signal moves and the things that must not move are watched at
the same time.

🔴 **What this experiment still cannot decide, said here so it is not read as
decided**: **which port letter bit 6 belongs to.** `rtl819x-gpio.c:120-129`
already declares that open — the chip is labelled `rtl819x-pabcd` and its lines
are numbered 0..31 **by bit position, which is the only thing that has been
measured**. `PROGRESS.md`'s `R5-7` row says the step's first act is to *measure
the port mapping*; that row predates the driver and is superseded by it. There
is no live experiment for a port **letter** that does not require writing a bit
into a byte believed unimplemented, and `RTL819X_GPIO_ALLOW_OUT_MASK` is `0`
precisely to forbid that. It is a desk question with two 讀 sources, and
**putting it in front of a power cycle would spend this project's most expensive
unit on a naming question.**

---

## 3. §A′ — the flash bracket around the button, which nothing here has ever done

`FLS-26`'s ledger stands at **proven identical 4,177,920 B (99.61 %), proven
different 8,192 B (0.195 %), undetermined 8,192 B (0.195 %)**, the last being
exactly `H601`. Seating 18 closed the attribution bracket across two vendor
firmware runs by `cmp`-ing two `C1-M0` logs.

🟢 **This block opens a bracket nobody has opened: around a button press.**
`C1-M0` runs **before** the hold and `C1-M1` **after** it, on the same boot.

* **Prediction**: `C1-M1` is **byte-identical to `C1-M0`**, and both are
  byte-identical to `bench/2026-09-09/C1-M0.log` — 32 group rows, 4,186,112
  bytes covered, `H601` skipped by rule.
* **What that would establish**: a ≥ 5 s hold of the reset button, under rlxfw,
  writes **nothing** to 4,186,112 of the 4,194,304 bytes. That sentence has
  never been sayable about any button press on this device.
* **Refuted by**: any differing group. That would be the most important finding
  of the seating and the block stops there.

⚠️ **What it still cannot see**, in the same words the ledger uses: a digest
agreeing with the 2026-08-16 dump cannot see two writes that cancel, `H601`'s
8,192 bytes are skipped by rule, and **no `FLR` runs in this block**. *"Not one
flash byte is written"* stays exactly as unsayable as it was.

---

## 4. §B — is `OVSEL` 3's +2 % systematic or is it jitter?

Seating 18's four-rung ladder left `OVSEL` 3 **+2.26 % long** against the 0 & 8
pair, and seating 17's rung 3 was long the same way. Two seatings, same sign,
no mechanism. 🔴 **Neither seating can tell a systematic offset from jitter,
because each ran rung 3 exactly once.** The whole repeatability figure this
project owns is **1.456 ms**, and it comes from two readings of one word on two
different boots.

**Three `bite 3` runs in one seating** decide it. `bite` composes with
`WDTCLR = 1` (`rtl819x-wdt.c:1236`), so the counter is cleared and the reading is
the clean one — that is the verb whose repeatability is 1.456 ms, not `biteraw`.

| | |
|---|---|
| seating 18's value | **1,340.982 ms** (`bench/2026-09-09/CORRECTIONS-block15.md:134`) |
| prediction | three readings with **max − min ≤ 3.0 ms**, each within **1,340.982 ± 5 ms** |
| **systematic** | max − min ≤ 3.0 ms → the +2 % is a property of the encoding or the counter and the residual becomes *find the mechanism*. `f_wdt` stays unmeasured |
| **jitter** | max − min > 10 ms → seating 18's ±71 ms residual analysis was reading noise, and the four-rung least-squares conclusion is withdrawn |
| **未定** | between 3.0 and 10.0 ms → recorded as undetermined **with the number of rungs a decision would need**, computed from the observed spread. Not rounded into either verdict |

🔴 **This is written before the readings exist, and the middle row is the
reason.** A two-outcome test with no middle is a test that always concludes.

---

## 5. §C — a carried-forward repair that pointed the wrong way, and the cell that proves it

### 5.1 What was carried forward, and what the code says

`PROGRESS.md` carries seating 18's residual ② as: *赤字上界大於 `2^15` … 修法是
`biteraw` 前先 `kickms 5000`*.

量, reading `rtl819x-wdt.c`:

* the bound is **`kick_ms × f`** — `bench/2026-09-09/CORRECTIONS-block15.md:151`
  states it as `0.250 s × 199,903 Hz = 49,976 counts`, and `kick_ms`'s default
  is **250** (`rtl819x-wdt.c:601`);
* so the bound is **proportional to `kick_ms`**, and `kickms 5000` multiplies it
  by 20, to ≈ **999,515 counts** — *twenty times worse than the number it was
  written to fix*;
* and `kickms` **does not kick**. Its handler sets `kick_ms` and calls
  `mod_timer` (`rtl819x-wdt.c:1403-1410`); the only `WDTCLR` writes are
  `rtl819x_wdt_kick_locked()`, reached by the `kick` verb and by the timer.

🔴 **The repair as written would have made the measurement worse and the card
would have read as though it had been fixed.** It was caught by reading the
handler, not by re-reading the sentence.

### 5.2 The repair that works, and its analytic bound

`kick_jiffies()` has a **one-jiffy floor** (`return j ? j : 1`,
`rtl819x-wdt.c:835-840`), so at `HZ = 100` any `kick_ms` below 10 behaves as 10.

```
kickms 10   ->   bound = 0.010 s x 199,903 Hz = 1,999 counts
```

**1,999 < 2^15 = 32,768**, by a factor of 16.4. That is the whole of residual ②.
`kick` immediately before `biteraw` in the same cell makes the actual deficit far
smaller than the bound, but **the bound is what is quoted**, because the shell's
inter-command latency is not something this card has measured.

⚠️ `hw_ovsel` defaults to **9** (`rtl819x-wdt.c:585`) ≈ 84 s, so a 10 ms kick
period has a 8,400× margin and `BOOTGUARD` cannot bite during the cell.

### 5.3 The cell, and it re-runs seating 18's own word

`C4-X17` sends the **identical** raw word seating 18 sent — `0x00020000`, bit 17,
`OVSEL[2]` — and predicts a **specific signed change** that only the deficit
explains.

| | counts | ms |
|---|---|---|
| seating 18, uncleared | 494,944 | **2,475.923** (量) |
| `2^19`, deficit 0 | 524,288 | 2,622.71 |
| `2^19`, deficit at the bound | 522,289 | 2,612.71 |

| outcome | reading | what it means |
|---|---|---|
| 🟢 **deficit model holds** | **2,612.7 – 2,622.7 ms** | `2^19` is confirmed by a *second and independent route* — a measured interval rather than a uniqueness argument over an admissible set. `CLK-28`'s method gains a positive control |
| 🔴 **refuted** | within ±3 ms of **2,475.923** | the 146.8 ms is not the counter's residue; `kickms`/`kick` change nothing and the deficit model that identified `OVSEL[2]` as bit 17 loses its arithmetic |
| 🔴 **impossible** | **> 2,623 ms** | implies a negative deficit; either `f_tick = 199,903 Hz` is wrong or `WDTCLR` does something other than zero the counter |

🟢 **`C4-K` is the positive control on the repair itself**: it reads
`/proc/rtl819x-wdt` back and requires **`kick_ms 10`**. Without it, a `C4-X17`
that came out at 2,475 ms could not distinguish *the model is wrong* from *the
verb never landed*.

---

## 6. What this block does NOT claim

* **No flash write command, no `FLR`, no `EW`/`EB`/`FLW`/burn.** `n_writes` is
  read on the first boot and on the last, and a non-zero reading stops the block.
* **No new image**, so nothing here bears on `RECIPE_ID`'s pipeline.
* **No `leds-rtl819x` code exists yet.** This block measures the premise; the
  driver is the next segment's work and its `ALLOW_OUT_MASK` decision is not
  taken here.
* **Nothing here decides the port letter** (§2.3).
* **`R5`'s `D2` is untouched.** The tree still holds **zero** `.dts` and zero
  `bindings/*.yaml`, owed by four accepted drivers. That is named in
  `PROGRESS.md`, not fixed here, and this card does not pretend otherwise.

---

## 7. 🔴 The freeze hole this card is the first to close by procedure

Gate 2 is `spec-check`, which sweeps **tracked** `.md` files. A card is
**untracked** until the freezing commit, so *the gate that exists to check the
card cannot see the card*. Seating 18 passed all five gates at 03:11 and a desk
sweep at 04:32 found a `C8c` inside the frozen card; it was excused by name
(`C8C_EXEMPT`) with `T13b` as the load-bearing control, **which is a patch and
not a repair**.

The repair is one line of ordering, and it is used here for the first time:

```
git add bench/2026-09-09b/PREDICTIONS-B17-block16.md   # stage FIRST
bash <a script file>                                    # then run the five gates
git commit                                              # then freeze
```

⚠️ **`git add` does not change the file's mtime**, so `check-predictions`'
mtime evidence — the thing that makes a frozen card's predictions dated — is
untouched by staging. That is the property this ordering relies on, and it is
stated here rather than assumed.

---

## 8. The cells

**Five boots, one power cycle.** Boot 1 carries seven cells because §A and §A′
must share one boot: the flash bracket is only a bracket if nothing reboots
between its two halves.

🔴 **`C1-L1` is the one cell in this repository's history that requires the
operator's hand to be on the board while it runs.** The operator presses and
holds **before** the cell is launched and releases **after** it returns. A row
with bit 5 = 1 means the hold lapsed and the cell is re-run.

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell C1 --out-dir bench/2026-09-09b --skip S2,S3,S4 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
#-- 🔴 FIRST HALF OF THE BUTTON BRACKET, and it must precede every press.  Also re-closes FLS-26's attribution against seating 18's C1-M0 at zero extra cost.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- baseline for the latch: dat, btn_raw, n_writes and load_default BEFORE any press.  n_writes non-zero stops the block.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-G0 --send 'cat /proc/rtl819x-gpio ; cat /proc/load_default' --idle 3 --seconds 20
#-- 🟢 THE NEGATIVE CONTROL, RELEASED.  Same command as C1-L1, differing by one physical act.  All three dat reads must be identical.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-R0 --send 'cat /proc/rtl819x-gpio ; sleep 3 ; cat /proc/rtl819x-gpio ; sleep 3 ; cat /proc/rtl819x-gpio' --idle 4 --seconds 40
#-- 🔴 OPERATOR HOLDS THE BUTTON FOR THE WHOLE OF THIS CELL AND WATCHES THE BOARD.  The eye is the instrument here; the register is the control.  Hold until the cell returns -- it spans >5 s, so the release fires FW-40's third branch and C1-L2 reads the latch.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-L1 --send 'cat /proc/rtl819x-gpio ; sleep 3 ; cat /proc/rtl819x-gpio ; sleep 3 ; cat /proc/rtl819x-gpio' --idle 4 --seconds 40
#-- released.  The latch: bit 6 cleared and staying cleared, and load_default 0 -> 1 from the same press.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-L2 --send 'cat /proc/load_default ; cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- 🔴 SECOND HALF OF THE BUTTON BRACKET.  Byte-identical to C1-M0 is the reading; anything else is the seating's most important result and the block stops.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- rung 1 of 3.  Same verb, same word, same seating -- the only variable left is the die.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C1-B3 --send 'echo bite 3 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 2: rung 2 of 3
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-09b --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C2-B3 --send 'echo bite 3 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 3: rung 3 of 3
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-09b --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C3-B3 --send 'echo bite 3 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 4: the repair, in two cells so the FIRST one is a positive control on the SECOND.  kick_ms must read 10 here or C4-X17 measures nothing.
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-09b --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C4-K --send 'echo unlock > /proc/rtl819x-wdt ; echo kickms 10 > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- seating 18's OWN word, with the deficit cut from <=49,976 counts to <=1,999.  Predicts +136.8 to +146.8 ms against 2,475.923.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C4-X17 --send 'echo kick > /proc/rtl819x-wdt ; echo biteraw 0x00020000 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 5: closeout.  n_writes on the way out, against C1-G0 on the way in.
/usr/bin/python3 tools/looprun.py --mode bench --cell C5 --out-dir bench/2026-09-09b --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09b/C5-P --send 'cat /proc/rtl819x-gpio ; cat /proc/rtl819x-spi ; cat /proc/load_default' --idle 3 --seconds 25
```

### 8.1 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The four files under `bench-only/r57-20260909/` never move again; nothing here
points at `config/rlxfw-src/`, which is a live tree.

```cardnum
img-bytes	1043456	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin
img-sha16	efc2ae0d604f8898	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin
vmlinux-bytes	4049730	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/vmlinux
vmlinux-sha16	ef7e8b57a46e0659	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/vmlinux
map-bytes	377513	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map
map-sha16	670b2dbf0a78f3b5	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map
wdt-verb-bite	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_wdt_verb_bite$
gpio-write-proc	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_gpio_write_proc$
expansion-captures	13	count bench/2026-09-09b/PREDICTIONS-B17-block16.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-09b/C[0-9]+-
expansion-loops	5	count bench/2026-09-09b/PREDICTIONS-B17-block16.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell C[0-9]+ --out-dir
expansion-cold	1	count bench/2026-09-09b/PREDICTIONS-B17-block16.md --out bench/2026-09-09b/C[0-9]+-A --esc 150
expansion-bite3	3	count bench/2026-09-09b/PREDICTIONS-B17-block16.md -{2}send 'echo bite 3 > /proc/rtl819x-wdt'
expansion-map0	2	count bench/2026-09-09b/PREDICTIONS-B17-block16.md ^/usr/bin/python3 .*echo map 0 > /proc/rtl819x-spi
expansion-biteraw	1	count bench/2026-09-09b/PREDICTIONS-B17-block16.md echo biteraw 0x[0-9A-F]{8} > /proc/rtl819x-wdt'
cells-fence	13	count bench/2026-09-09b/PREDICTIONS-B17-block16.md ^bench/2026-09-09b/C[0-9]+-[A-Z0-9]+$
send-over-127	0	count bench/2026-09-09b/PREDICTIONS-B17-block16.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-09b/PREDICTIONS-B17-block16.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
```

---

## 9. The fence

```cells
bench/2026-09-09b/C1-A
bench/2026-09-09b/C1-M0
bench/2026-09-09b/C1-G0
bench/2026-09-09b/C1-R0
bench/2026-09-09b/C1-L1
bench/2026-09-09b/C1-L2
bench/2026-09-09b/C1-M1
bench/2026-09-09b/C1-B3
bench/2026-09-09b/C2-B3
bench/2026-09-09b/C3-B3
bench/2026-09-09b/C4-K
bench/2026-09-09b/C4-X17
bench/2026-09-09b/C5-P
```

**13 cells.** Every capture in this seating is inside the fence; there is no
`PC` outside it, which seating 15's card got wrong and which
`check-predictions` `N8`/`N9` now catch.
