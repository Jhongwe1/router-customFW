# Block 17 — two drivers of mine on one register, and the second one's poll is the first one's sampler

**Written 2026-09-10, fifty-fifth segment, at the desk, before power.**
Seating 20, **one power cycle**, **thirteen boots**, three of which the
operator's hand is on the board for. **New image `r59`**, which carries both
`R5-7` and `R5-8`.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4** — re-derive `RECIPE_ID` and compare with §1. If it moved, the
   image is stale and is **rebuilt**; the card is not edited to match.
   🟢 量 at 17:35 today, all three sources: `692a2801` — the by-hand formula
   over `config/`, the build's own `manifest.tsv`, and `--dry-run`.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read **from a script file**
   and not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident), and on a
   tree where this card is already `git add`ed (seating 19's §7).
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 55`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. It is `bench/2026-09-10`, which asserts *every capture in this seating
   starts before 00:00 on 2026-09-11*. This card was written from 17:20 on
   2026-09-10, so the assertion has under seven hours of slack and it is the
   tightest this project has ever run. 🔴 **§10 is the drop order that keeps
   the assertion true**, and it is on the card rather than in someone's head.
   `tools/capdate.py` checks it afterwards.

---

## 0. What this block is, in one paragraph

`R5-7` puts an unmodified upstream `leds-gpio` on `PABCD` bit 6 through a
`gpio_chip` of mine. `R5-8` puts a polled input device of mine on `PABCD` bit 5
through the same chip. Both desk halves are done and **neither has run on the
silicon**: 量 `notes/gpio-driver.md` § 11, **213 of the boot capture's predicted
1,637 bytes have never been on this die**. This block runs both, on one image,
in one power cycle — and the reason they share a seating is not economy. It is
that **`rtl819x-keys`' 20 Hz poll of line 5 is what samples `rtl819x-gpio`'s
foreign-write detector on bit 6**, so the two drivers measure each other, and
neither image alone can produce the readings in §4 and §7.

---

## 1. The image, staged and pinned

| | |
|---|---|
| cell | `r59` |
| `RECIPE_ID` | **`692a2801`** — the board must print `RLXFW-ID0=692A2801` |
| `vmlinux` | 4,095,382 bytes, sha256 `fe12f9ea0d78803f64b0c9b3968ec68786cbb92f314bf5baaa26513d7cf80591` |
| staged image | `/home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin` |
| image bytes | **1,052,672** |
| image sha256 | **`c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5`** |

🟢 **The four files under `bench-only/r59-20260910/` never move again** —
lifecycle rule 2. Nothing on this card points at `config/rlxfw-src/`, which is
a live tree.

🟢 **`rtkimage build` ran under `tools/vendor-tripwire.sh` and it reported
`CLEAN, 4 tree(s) watched`.** The pipeline executes the vendor's own `rtkload`
Makefile, `lzma` and `cvimg`, and `CLAUDE.md` records what happened the last
time a vendor binary was run without one.

---

## 2. §A — the two decisions this card was told to fix

`PROGRESS.md` carried both forward with the owner declining to settle them at
the desk. Both are settled here, and the first one is settled by a **reading**
rather than by a preference.

### 2.1 Decision ① — ONE image carrying both drivers, not two images

The objection to one image is real and specific: `rtl819x-keys` takes
`gpio_request(5)` at probe, and `RC4`'s instrument is `tryout 5`, which must
return `-EPERM` **from this driver's own guard**. If gpiolib refused earlier,
`RC4` would read as fired with the guard never reached — and that is not
hypothetical, it is what seating 15 measured with the roles reversed
(`bench/2026-09-06c/CORRECTIONS-block12.md` § 2).

讀, and it settles it:

* `gpiolib.c:77-96`, `gpio_ensure_requested()` — the condition is
  `WARN(test_and_set_bit(FLAG_REQUESTED, ...) == 0, ...)`. `test_and_set_bit`
  returns the **old** value, so on a line that is **already requested** the
  test is `WARN(1 == 0)`, the whole block is skipped, no auto-request happens,
  no `WARN` fires, and the function returns **0**.
* `gpiolib.c:955-1000`, `gpio_direction_output()` — with `status == 0` the
  `if (status)` branch that would call `chip->request` is not taken, and
  `chip->direction_output` is called directly.

**So on `r59`, `tryout 5` reaches `rtl819x_gpio_direction_output`, hits
`!((1u << 5) & out_mask())`, and returns `-EPERM`.** `RC4` is intact, and it is
intact *because* a real consumer holds the line.

🟢 **Two things become POSITIVE results that were artefacts on the other
image**:

| | on `r58` (keys absent) | on `r59` (keys holds line 5) |
|---|---|---|
| `tryout 5` | auto-requests line 5, `n_req_ok` +1, leaves the line held under the label `[auto]` | reaches the guard, `n_req_ok` **unmoved** |
| `claim` (= `gpio_request(5)`) | `-EBUSY`, **caused by the `tryout` above it** — seating 15's artefact | `-EBUSY`, caused by `rtl819x-keys` owning the line — gpiolib arbitrating between my chip and a real consumer |

🔴 **`n_req_ok` unmoved across `tryout 5` is the falsifiable half of that
reading**, and `C1-P`/`C1-P2` are what measure it. If it moves to 3, my reading
of `test_and_set_bit`'s return value is wrong and everything in this subsection
goes with it.

### 2.2 Decision ② — three operator episodes, on three separate boots, in this order

The order is forced, not chosen:

1. **LED first.** `REG-37` measured `dat` latched at `0000003C` — bit 6 low,
   the LED lit — for at least 152.1 s after a long press. A long press
   therefore leaves bit 6 in a state that contaminates every subsequent LED
   reading, **and re-running does not recover it**. Any LED cell after a hold
   is worthless.
2. **Short presses second.** They need `state_last` to be whatever it is; they
   do not disturb it.
3. **The long hold last.** It is the only act that crosses `FW-40`'s `>= 5 s`
   branch, and §7 explains why that is safe on this image.

The three do **not** share a boot, because each one's re-run needs a known
starting state and only a boot gives one cheaply — `busybox reboot -f` returns
the board to the loader in 2.407 s (`FW-37`).

🟢 **What does share a boot is the `interval` ladder**, because `interval N` is
a runtime verb: three sampling resolutions of the same button on one boot,
which is §6.

---

## 3. §B — the at-rest dump, predicted field by field before power

Every field below is derived from source read at the desk. The two `/proc`
files are read **keys first, then gpio**, always, so that the gpio counters
include the keys read's own `gpio_get_value` — that convention is what makes §4
arithmetic rather than an estimate.

### 3.1 The initcall order, which is a prediction and not a convention

讀 `drivers/Makefile`: `gpio/` at :8, `mtd/` at :53, `input/` at :71,
`watchdog/` at :79, `leds/` at :94. `rtl819x-keys` and `leds-gpio` are **both**
`device_initcall`, so link order decides, and `input/` precedes `leds/`.

🔴 **So `RLXFW-K0` … `RLXFW-K8` all precede `RLXFW-G7`/`RLXFW-G8` in every boot
capture** — no address quoted, nothing asked of the kernel about itself, the
same shape as seating 14's `TA8`-before-`B10`. **Refuted by** any capture in
which a `G7` line arrives before a `K` line.

🔴 **And it has a consequence nobody would predict from the byte count**: at
the moment `rtl819x-keys` probes, `leds-gpio` has not run, so
`rtl819x_gpio_state_known` is still **0** and the probe's own
`gpio_get_value(5)` calls `state_check` and returns before incrementing
anything. **`n_state_chk` is therefore 0 through the whole boot**, and the
first `/proc/rtl819x-gpio` read is the first comparison the detector ever
makes.

### 3.2 `/proc/rtl819x-gpio`, first read of a boot

| field | prediction | where it comes from |
|---|---|---|
| `version` | `1.1` | |
| `added` / `add_rc` | `1` / `0` | `G4=00000000` from `gpiochip_add()` |
| `base` / `ngpio` | `0` / `32` | |
| `cnr` / `dir` | `FFFFFF8B` / `FF000040` | `REG-35`, 量 seating 15 |
| `dat` | `0000007C` | `REG-37`'s resting value. **`0000003C` is the stated alternative** — if the board booted out of a post-long-press latch, `G7` says so |
| `cnr_as_spec` / `dir_as_spec` | `1` / `1` | `RC3` fires on either being 0 |
| `btn_raw` / `btn_pressed` | `1` / `0` | `BRD-05` active low, nobody holding the button |
| `known_mask` | `00000060` | bits 5 and 6 |
| `allow_out_mask` | `00000040` | bit 6 — **`00000000` here means the mask change did not reach the artefact and the block stops** |
| `out_locked` / `out_effective` | `00000000` / `00000040` | |
| `n_req_ok` / `n_req_no` | **`2`** / `0` | keys' `gpio_request(5)` + `leds-gpio`'s `gpio_request(6)` |
| `n_dirin_ok` / `n_dirin_no` | **`1`** / `0` | keys' `gpio_direction_input(5)` |
| `n_dirout_ok` / `n_dirout_no` | **`1`** / `0` | `leds-gpio`'s `gpio_direction_output(6, 1)` |
| `n_set_ok` / `n_set_no` | **`0`** / `0` | 讀 `led-class.c`: `led_classdev_register` calls `led_update_brightness`, a no-op without `brightness_get`, which `leds-gpio` does not set |
| `n_get` | **`1`** | keys' probe seeds `raw_prev` with one `gpio_get_value(5)`. **`CONFIG_GPIO_SYSFS` is `n` (量, the built `.config`), so nothing exports a line to sysfs and nothing else reads one** |
| `n_writes` | **`2`** | one `DAT`, one `DIR`, from one `.direction_output`. `RC2` fires on anything else |
| `state_known` / `state_last` | `1` / `0000007C` | `active_low = 1`, so the written value is `dat \| 0x40` and `dat` already has bit 6 set — the write is a no-op |
| `n_state_chk` | **`1`** | § 3.1: the read's own comparison is the first one counted |
| `n_state_foreign` / `foreign_seen` | **`0`** / `0` | `RC5` |
| `probed04` / `val04` | `0` / `00000000` | not read at boot, by design |

### 3.3 `/proc/rtl819x-keys`, first read of a boot

| field | prediction | where it comes from |
|---|---|---|
| `version` | `1.0` | |
| `bound` / `reg_rc` / `probe_rc` | `1` / `0` / `0` | `K6` and `K7` both `00000000` |
| `nbuttons` / `max_buttons` / `log_slots` | `1` / `4` / `32` | |
| `irq_probe` / `irq_live` / `enxio` | **`-6`** / **`-6`** / `-6` | `-ENXIO`. The same value the mark `K4` prints as `FFFFFFFA`, **in two representations, from two call sites, one latched at probe and one taken live** |
| `evdev_built` / `evbug_built` | `1` / `0` | |
| `poll_ms` / `poll_jiffies` / `hz` | `50` / `5` / `100` | `msecs_to_jiffies(50)` at `HZ = 100` |
| `n_open` / `n_poll` | **`0`** / **`0`** | nothing has opened `/dev/input/event0` yet — state one of three |
| `j_first` / `j_last` | `0` / `0` | |
| `n_ev` / `n_ev_drop` | `0` / `0` | |
| `boot_raw` | **`1`** | `K3` |
| `b0_gpio` / `b0_code` | `5` / **`408`** | `KEY_RESTART` is `0x198` at `include/linux/input.h:511` |
| `b0_active_low` / `b0_debounce_ms` | `1` / `100` | |
| `b0_need` | **`2`** | `ceil(100 / 50)`, printed so the conversion is checkable rather than assumed |
| `b0_raw` / `b0_state` | `1` / `0` | |
| `b0_n_edge` … `b0_n_report` | all `0` | |
| `ev` lines | **none** | `n_ev` is 0 |

### 3.4 The boot capture

**1,637 bytes**, on all thirteen. The ladder, written before the build
(`LOG.md`, fifty-fourth segment § 7) and re-stated here because a card must
carry what it will be checked against:

| bytes | where it stopped |
|---|---|
| **1,493** | `rtl819x-keys.o` never reached the image; `MK8`'s witness would also be red |
| **1,551** | the driver registered and **probe was never called** — `K7` reads `00000001`, a sentinel a real probe cannot produce |
| **1,580** | probe was entered and `gpio_request` failed; `K2` carries the errno |
| **1,637** | probe ran to the end |

Then by **value**: `K2 = 00000000`, `K3 = 00000001`, **`K4 = FFFFFFFA`**,
`K5 = K7 = 00000000`, `K6 = 00000000`.

⚠️ **1,637 is a prediction and not a measurement.** 1,424 is the measured
floor — thirteen captures in seating 18 and ten in seating 17 — and
**213 bytes of the 1,637 have never been on this die**.

---

## 4. §C — the two counter identities, and why they need one image

Two drivers, four counters, and an arithmetic relation between them with a
residual that is predicted before power.

讀, the four call sites of `rtl819x_gpio_state_check()`: `.get` (:470),
`.direction_output` (:565), `.set` (:637) and `read_proc` (:687) — and in the
two op cases the refusal paths return **before** the check, so only the `_ok`
counters contribute. 讀 `rtl819x_gpio_request` and `rtl819x_gpio_direction_input`:
neither calls it.

讀 `rtl819x_keys_poll`: one `gpio_get_value(k->b->gpio)` per button per poll,
through gpiolib, which is `chip->get`. 讀 `rtl819x_keys_read_proc`: one more per
button. 讀 `rtl819x_keys_flush`: one more per button per open.

**Identity 1** — over any interval between two gpio reads:

    Δn_get = Δn_poll + (keys /proc reads) + (keys `sample` verbs) + Δn_open

**Identity 2** — over the same interval:

    Δn_state_chk = Δn_get + (gpio /proc reads) + Δn_dirout_ok + Δn_set_ok

🔴 **The residual is 0 or 1, and the 1 is not slop — it is a second
measurement.** The two `cat`s in a pair cell are not simultaneous, so a poll
can land between the keys read and the gpio read. Over `N` pair cells the count
of residual-1 cases estimates the shell's `cat`-to-`cat` gap as
`(residual-1 count / N) × poll_ms`, and the `.timing` file estimates the same
gap independently. **Two sources for a quantity nobody set out to measure.**

🟢 **`C10-X` removes the slop instead of estimating it.** It reads
`keys ; gpio ; keys`, so the poll count at the instant of the gpio read is
**bracketed on both sides** by two readings of `n_poll` and Identity 1 becomes
a two-sided inequality with no free term.

⚠️ **On `r58` neither identity exists**: with no keys driver nothing calls
`.get` between `/proc` reads, `Δn_poll` has no owner, and `n_state_chk` moves
only when a human types `cat`.

---

## 5. §D — the LED, and a refusal that is visible as light

`BRD-13` is already 量 (seating 19): `PABCD` bit 6 drives **LED #2 of eight**,
**active low**, with the polarity measured at both levels and with LEDs #1 and
#4 as the operator's own negative control. **This block does not re-establish
that.** What it establishes is narrower and is `R5-7`'s actual DoD: **a
`led_classdev` of upstream's, bound to a `gpio_chip` of mine, produces that
same light from a sysfs write.**

讀 `leds-gpio.c`, so the polarity is applied exactly once and in a place this
card can name:

* `create_gpio_led`: `gpio_direction_output(gpio, active_low)` = `(6, 1)` →
  bit 6 **high** → **dark**. This is the `n_writes = 2` of § 3.2.
* `gpio_led_set`: `value != LED_OFF → level = 1`, then
  `if (active_low) level = !level` → `gpio_set_value(6, 0)` → bit 6 **low** →
  **lit**.

### 5.1 The guard's two-sided test, which `R5-4` could not run

`notes/gpio-driver.md` § 7 ② asks for it and `ALLOW_OUT_MASK = 0` made it
impossible until 2026-09-10: **a guard that has only ever been seen refusing is
a wall.** `lock 6` takes bit 6 out of the runtime mask; `unlock 6` puts it back;
neither can grant a line the compiled mask does not carry.

🔴 **The reading is not a counter, it is that the light does not go out.**

| cell | act | the operator sees | `/proc` |
|---|---|---|---|
| `C11-L1` | `brightness` ← 1 | **LED #2 lights** | `dat` bit 6 → 0, `n_set_ok` 1, `n_writes` **3** |
| `C11-L2` | `lock 6` | nothing | `out_locked` `00000040`, `out_effective` `00000000` |
| `C11-L3` | `brightness` ← 0 | **LED #2 STAYS LIT** | `brightness` reads back **0** |
| `C11-L4` | read `/proc` | — | `dat` bit 6 still **0**, `n_set_no` **1**, `n_writes` still **3** |
| `C11-L5` | `unlock 6`, `brightness` ← 0 | **LED #2 goes dark** | |
| `C11-L6` | read `/proc` | — | `dat` bit 6 → 1, `n_set_ok` **2**, `n_writes` **4** |

🟢 **`C11-L3` is the best single reading on this card**: the LED class device
reports brightness 0 while the pin is still driving the light. **Linux's model
of the world and the pin disagree, on purpose, and the disagreement is what the
guard is.**

🔴 **Refutation, stated as three separate ways this fails**: the LED does not
light at `C11-L1` (`RC8`, and `R5-7`'s DoD is not met); the LED goes dark at
`C11-L3` (the runtime mask does not narrow, and `out_locked` is decoration);
`n_writes` moves at `C11-L4` (the refusal happens after the write rather than
before it, and `.set`'s ordering is wrong).

### 5.2 What `C11-P0` adds and what it cannot

`ls /sys/class/leds` must list **`n150rt:green:led2`**, which is `RC7` — 讀
`create_gpio_led`, `gpio_direction_output` is called **before**
`led_classdev_register`, so the 1,637-byte capture is consistent with the class
device having failed to register and with `CONFIG_PRINTK=n` saying nothing.
**The byte count cannot settle it and the directory listing can.**

⚠️ `CONFIG_LEDS_TRIGGERS` is `n` (量, the built `.config`), so that directory
holds `brightness`, `max_brightness`, `device`, `subsystem` and `uevent` and
**no `trigger`**. A `trigger` file appearing is a config difference nothing
declared.

---

## 6. §E — the press ladder, and what a polled button cannot see

`debounce_interval = 100` ms is a **guess** and the board file says so. Nothing
in this project has measured this button's bounce. The instrument is the
32-slot jiffies ring, and its resolution is the poll interval, which is a
property of polling and not of the timestamp.

**So the experiment is a resolution ladder**: the same physical act, sampled
three ways, in one boot, with `interval N` as the only variable.

| cell | `interval` | `b0_need` | polls per second | what an edge in the ring resolves to |
|---|---|---|---|---|
| `C12-B10` | 10 ms | **10** | 100 | 10 ms — the floor, one tick at `HZ = 100` |
| `C12-B50` | 50 ms | **2** | 20 | 50 ms — the compiled-in value |
| `C12-B200` | 200 ms | **1** | 5 | 200 ms |

Three short presses per rung, inside a 15 s window with the device open.

**Predictions**:

* `b0_n_press` = `b0_n_release` = `b0_n_report` = **3** at every rung. A rung
  that reads fewer has a press the debounce swallowed; at `interval 200`,
  `b0_need = 1`, so a press shorter than one poll period can be missed entirely
  and **that is the rung most likely to under-count**.
* `b0_n_edge` ≥ 6 at every rung, and **monotonically non-increasing down the
  ladder**: a slower sampler cannot see more transitions than a faster one.
  🔴 **Refuted by** `n_edge` at 200 ms exceeding `n_edge` at 10 ms, which would
  mean the extra edges are the instrument's and not the button's.
* `b0_n_bounce` — **no prediction, and that is the point.** If it is non-zero
  at 10 ms and zero at 50 ms, the bounce is between 10 and 50 ms and
  `debounce_interval = 100` is doing real work with 2x margin. If it is **0 at
  all three**, the correct statement is *bounce is below 10 ms or falls between
  polls* — **not** *this button does not bounce* — and 100 ms is then over
  ten times what the measurement can justify.
* `n_ev_drop` — `0` is wanted. Non-zero means more than 32 edges arrived and
  the ring holds only the last 32; the count itself then becomes the bounce
  reading and the ladder is re-run one press per cell.

🟢 **`C12-O`/`C12-O2`/`C12-O3` are the three-state control, and the third state
costs a `sleep` with no open**: `(n_open, n_poll)` reads `(0, 0)` → `(1, rising)`
→ `(2, rising again)` → `(2, FLAT)`. **The second open is what makes it
causation rather than coincidence** — the polling stops and restarts with the
opens, twice.

⚠️ **`sleep N < /dev/input/event0` and not `cat … &`.** The open is what
`evdev_open` needs; the data is not wanted (`FW-46`: nothing in this image
decodes a `struct input_event`, and ESC is among its bytes). A backgrounded
`cat` would need `kill` to close, `kill` is not among this image's eleven
declared busybox symlinks, and `cardcheck`'s `ASH_BUILTINS` list refuses a card
that rests on a builtin — the same refusal seating 18's first draft got for
`exec 3>`.

---

## 7. §F — the long hold, and the vendor's duty cycle measured from the other side

`FW-40`, 量: the vendor's `rtl_gpio_timer` re-arms at `jiffies + 100` — one
second at `HZ = 100` — and blinks bit 6 on the hold counter's **parity**. So
while the button is held, bit 6 is a square wave: **1 s high, 1 s low, 50 %
duty**.

`rtl819x-gpio`'s detector compares the live `DAT` bit 6 against the last value
**this** driver wrote. `C13-D` sets that value to *dark* first, so the
comparison has a known reference. Every `.get` is a sample, and
`rtl819x-keys` supplies 20 of them a second.

**The prediction is a ratio with no units**:

    n_state_foreign / n_state_chk  ->  0.5

over an integer number of 2 s periods. 20 Hz against 0.5 Hz is 40x
oversampling, so aliasing is not available as an explanation.

🔴 **`notes/gpio-driver.md` § 6.2 predicts `about one per second` and that is
wrong on this image, by a factor of ten.** It was written for a detector
sampled by a human typing `cat`. With `rtl819x-keys` in the same image the
sampler is the poll loop: over a 15 s hold at `interval 50`, `n_state_chk`
grows by ~300 and `n_state_foreign` by **~150**. That note is corrected in the
same commit as this card.

🟢 **`C13-H10` is the control that makes the ratio a property of the vendor and
not of my sampler**: at `interval 10` the poll rate is 5x higher, so
`n_state_chk` grows ~5x, and **the ratio must not move**. A ratio that tracks
the poll rate is measuring the sampler.

### 7.1 The `>= 5 s` branch, and why it is safe on this image

`FW-40`, 量 out of this image's own compiled code: on release, a hold of 2–4 s
sends `SIGTERM` to PID 1, and a hold of **>= 5 s writes ASCII `'1'` into
`default_flag`**.

* The `SIGTERM` is ignored: this image's PID 1 is a four-line shell script
  (`FW-37`, which is the same reason `busybox reboot` without `-f` does not
  reset this board).
* `default_flag`'s **only readers in this image are two `/proc` handlers**
  (量, seating 15). Nothing acts on it. Seating 19 crossed this branch on
  `r57` and measured `/proc/load_default` going `0` → `1` with the flash
  bracket around it coming back byte-identical.
* `r59` adds no reader of `default_flag`. 讀, the diff against `r57` is
  `rtl819x-gpio` 1.1, `rlxfw-devices.c`, `rtl819x-keys` and the `leds-gpio`
  and INPUT config families.

**So the hold is not a flash-adjacent act on this image**, and `C13-P1` reads
`/proc/load_default` back as **`1`** to say the branch was reached at all.

### 7.2 What the ring records that no counter does

The hold cell's window is **25 s** and the operator presses a couple of seconds
in and releases a few seconds before it closes. **The instrument records its own
timing** — that is the whole reason the ring carries `jiffies` — so nothing
here depends on a conversation turn lining up with a physical act, which is the
rule this project learned the hard way.

From the ring: `(j_release − j_press) / HZ` is the hold in seconds, and it must
be consistent with `/proc/load_default` reading 1 (`>= 5 s`) and with the
`n_state_foreign` count (`~10 per second of hold` at `interval 50`).
**Three quantities, one physical act, no operator stopwatch.**

---

## 8. §G — the flash bracket

`C1-M0` and `C13-M1` are `rtl819x-spi` 1.1's `map 0`, one before every press of
this seating and one after all of them.

* **Byte-identical is the reading.** Anything else is this seating's most
  important result and the block stops.
* It also closes `FLS-26`'s attribution one segment further: seating 19's
  `C1-M0`/`C1-M1` and this seating's pair are four maps of group 0 with a
  vendor-firmware-free interval between them.
* ⚠️ It does **not** move the 99.61 % / 0.195 % / 0.195 % ledger, and no `FLR`
  runs. **Zero flash-write commands.** `H601` is not read.

---

## 9. What this block does NOT claim

1. **Which port of `PABCD` line 5 and line 6 belong to.** `rtl819x-gpio.c:120`
   lists it as the first thing the file does not establish, and nothing here
   changes that.
2. **That a press reached userspace.** `b0_n_report` counts
   `input_report_key()` calls. Whether the input core propagated one is the
   core's business — it drops a repeat of a state it already holds — so
   `n_report` is an **upper bound** on what a reader of `/dev/input/event0`
   would see. Nothing in this image can decode that node (`FW-46`).
3. **That the vendor's reset path is out of the way.** It is not. Both drivers
   read the same pin; `rtl819x-keys` takes gpiolib's request and the vendor
   path does not use gpiolib, so there is **no arbitration** — only the
   observation that both are readers and neither writes `DAT` bit 5.
4. **Anything about bounce below 10 ms.** §6 states the floor rather than
   leaving it to be discovered.
5. **That `n_state_foreign > 0` identifies the vendor's timer.** It identifies
   *a writer that is not this driver*. `FW-40` is what names it, and that is a
   disassembly reading, not this seating's.

---

## 10. 🔴 The drop order, because the directory name is a deadline

`bench/2026-09-10` asserts that every capture **starts** before 00:00. If the
clock is against you, drop from the bottom of this list, and **each line says
what is lost** so the decision is not made by whoever is most tired:

| drop | what is lost | what survives |
|---|---|---|
| 1. boots 6–9 (`C6`…`C9`) | the D1 population falls from 13 to 9 boots | the boot capture is byte-identical or it is not; nine is enough to say so, and seatings 17 and 18 used ten |
| 2. `C12-A200`/`C12-B200` | the third rung of the resolution ladder | two rungs still bracket the bounce |
| 3. `C13-A10`/`C13-H10` | the duty-cycle **control** | 🔴 the ratio then has no control and **must not be quoted as a result** — write it down as 推 |
| 4. `C10-X` | the exact two-sided bracket on Identity 1 | the ±1 form in §4, which is still a residual |
| 5. `C1-T12` | the `-ENODEV` half of the two-layer refusal | `tryout 5`'s `-EPERM` alone |

🔴 **Nothing above this line may be dropped**: `C1-M0`/`C13-M1` (the flash
bracket has no value as a half), `C11-L1`…`C11-L6` (`R5-7`'s DoD), `C12-O`…
`C12-O3` (without the three-state, every keys counter is unattributable), and
`C13-H50` (`RC6`, without which `RC5`'s zero is worthless).

---

## 11. The cells

**Thirteen boots, one power cycle.** Boots 2–9 are identical and are written
out in full rather than abbreviated, because a card is executed and not read.

🔴 **Every boot ends with `busybox reboot -f`**, which returns the board to the
loader in 2.407 s (`FW-37`) so the next `looprun`'s `S4` has a loader prompt to
type `J BFC00000` at. `reboot` is an applet and not one of this image's eleven
declared symlinks, which is why it is typed as `busybox reboot -f`.

🔴 **No cell on this card can reset the board except the `RB` cells**, which is
deliberate: seating 17 spent two of its three power cycles on cells whose
payload could reset the board with no `--esc-after` on them.

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell C1 --out-dir bench/2026-09-10 --skip S2,S3,S4 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
#-- 🔴 FIRST HALF OF THE FLASH BRACKET, and it must precede every press of this seating.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- the at-rest pair.  KEYS FIRST, GPIO SECOND, always -- 4 depends on it.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- gpiolib arbitrating between my chip and a real consumer.  Through cat, whose error path prints strerror: EBUSY.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-CL --send 'echo claim | cat > /proc/rtl819x-gpio' --idle 3 --seconds 15
#-- RC4.  G-TRYRC must be FFFFFFFF (-EPERM, from MY guard) and the three XORs 00000000.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-T5 --send 'echo tryout 5 > /proc/rtl819x-gpio' --idle 3 --seconds 15
#-- the other refusal, one layer up: line 12 is outside KNOWN_MASK, so .request says -ENODEV and .direction_output is never reached.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-T12 --send 'echo tryout 12 > /proc/rtl819x-gpio' --idle 3 --seconds 15
#-- 2.1's falsifiable half: n_req_ok must still be 2 here.  3 means tryout auto-requested and my reading of gpio_ensure_requested is wrong.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-P2 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C1-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 2
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C2-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C2-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 3
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C3-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C3-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 4
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C4-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C4-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 5
/usr/bin/python3 tools/looprun.py --mode bench --cell C5 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C5-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C5-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 6.  10's drop list starts here.
/usr/bin/python3 tools/looprun.py --mode bench --cell C6 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C6-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C6-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 7
/usr/bin/python3 tools/looprun.py --mode bench --cell C7 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C7-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C7-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 8
/usr/bin/python3 tools/looprun.py --mode bench --cell C8 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C8-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C8-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 9
/usr/bin/python3 tools/looprun.py --mode bench --cell C9 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C9-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C9-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 10: the tenth D1 sample, and the exact bracket on 4's Identity 1.
/usr/bin/python3 tools/looprun.py --mode bench --cell C10 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C10-P --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- keys, gpio, keys: n_poll at the instant of the gpio read is bracketed on both sides and Identity 1 loses its free term.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C10-X --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio ; cat /proc/rtl819x-keys' --idle 3 --seconds 40
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C10-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 11: 🔴 OPERATOR EPISODE 1 OF 3 -- THE EYE.  LED #2 of eight (BRD-13).  Nothing is pressed on this boot.
/usr/bin/python3 tools/looprun.py --mode bench --cell C11 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
#-- RC7: the class device has to EXIST, and the boot capture cannot say so.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-P0 --send 'ls /sys/class/leds ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- 🔴 LOOK AT THE BOARD.  LED #2 must LIGHT.  This is R5-7's DoD and the eye is the instrument.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L1 --send 'echo 1 > /sys/class/leds/n150rt:green:led2/brightness ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- arm the runtime mask.  Nothing visible happens here.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L2 --send 'echo lock 6 > /proc/rtl819x-gpio' --idle 3 --seconds 15
#-- 🔴 LOOK AT THE BOARD.  LED #2 must STAY LIT while brightness reads back 0.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L3 --send 'echo 0 > /sys/class/leds/n150rt:green:led2/brightness ; cat /sys/class/leds/n150rt:green:led2/brightness' --idle 3 --seconds 20
#-- the register side of the same refusal: dat bit 6 still 0, n_set_no 1, n_writes still 3.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L4 --send 'cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- 🔴 LOOK AT THE BOARD.  LED #2 must GO DARK.  Same write, one verb different.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L5 --send 'echo unlock 6 > /proc/rtl819x-gpio ; echo 0 > /sys/class/leds/n150rt:green:led2/brightness' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-L6 --send 'cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C11-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 12: 🔴 OPERATOR EPISODE 2 OF 3 -- NINE SHORT PRESSES.  Under one second each, well clear of FW-40's 2 s branch.
/usr/bin/python3 tools/looprun.py --mode bench --cell C12 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
#-- three-state, part 1: (0,0) then the first open.  DO NOT PRESS ANYTHING IN THIS CELL.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-O --send 'cat /proc/rtl819x-keys ; sleep 3 < /dev/input/event0 ; cat /proc/rtl819x-keys' --idle 4 --seconds 30
#-- part 2: a SECOND open.  n_poll resumes, which is what makes the open the cause.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-O2 --send 'sleep 3 < /dev/input/event0 ; cat /proc/rtl819x-keys' --idle 4 --seconds 30
#-- part 3: a sleep with NO open.  n_poll must be FLAT -- the third state.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-O3 --send 'sleep 3 ; cat /proc/rtl819x-keys' --idle 4 --seconds 30
#-- rung 1 of 3: 10 ms, the floor.  b0_need must read 10.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-A10 --send 'echo interval 10 > /proc/rtl819x-keys ; echo clear > /proc/rtl819x-keys' --idle 3 --seconds 15
#-- 🔴 THREE SHORT PRESSES INSIDE THIS WINDOW.  The ring records their timing; nothing here depends on when the cell was launched.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-B10 --send 'sleep 15 < /dev/input/event0 ; cat /proc/rtl819x-keys' --idle 4 --seconds 40
#-- rung 2 of 3: 50 ms, the compiled-in value.  b0_need must read 2.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-A50 --send 'echo interval 50 > /proc/rtl819x-keys ; echo clear > /proc/rtl819x-keys' --idle 3 --seconds 15
#-- 🔴 THREE SHORT PRESSES INSIDE THIS WINDOW.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-B50 --send 'sleep 15 < /dev/input/event0 ; cat /proc/rtl819x-keys' --idle 4 --seconds 40
#-- rung 3 of 3: 200 ms.  b0_need must read 1, and this is the rung most likely to MISS a press.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-A200 --send 'echo interval 200 > /proc/rtl819x-keys ; echo clear > /proc/rtl819x-keys' --idle 3 --seconds 15
#-- 🔴 THREE SHORT PRESSES INSIDE THIS WINDOW.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-B200 --send 'sleep 15 < /dev/input/event0 ; cat /proc/rtl819x-keys' --idle 4 --seconds 40
#-- nine presses and the detector must still read 0: bit 5 is not watched, and this is what says so.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-Z --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C12-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- boot 13: 🔴 OPERATOR EPISODE 3 OF 3 -- TWO LONG HOLDS.  This is the boot that crosses FW-40's 5 s branch; 7.1 is why that is safe here.
/usr/bin/python3 tools/looprun.py --mode bench --cell C13 --out-dir bench/2026-09-10 --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-P0 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- give the detector a KNOWN reference before the vendor starts moving the bit.  Dark.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-D --send 'echo 0 > /sys/class/leds/n150rt:green:led2/brightness ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-A50 --send 'echo interval 50 > /proc/rtl819x-keys ; echo clear > /proc/rtl819x-keys' --idle 3 --seconds 15
#-- 🔴 PRESS AND HOLD ABOUT 15 SECONDS INSIDE THIS WINDOW, then release and let the cell finish.  Watch LED #2: it should blink at 1 Hz while held.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-H50 --send 'sleep 25 < /dev/input/event0 ; cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --idle 4 --seconds 55
#-- the control: five times the poll rate, same physical act, and the RATIO must not move.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-A10 --send 'echo interval 10 > /proc/rtl819x-keys ; echo clear > /proc/rtl819x-keys' --idle 3 --seconds 15
#-- 🔴 PRESS AND HOLD ABOUT 15 SECONDS INSIDE THIS WINDOW, then release and let the cell finish.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-H10 --send 'sleep 25 < /dev/input/event0 ; cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --idle 4 --seconds 55
#-- 🔴 SECOND HALF OF THE FLASH BRACKET.  Byte-identical to C1-M0 is the reading; anything else is this seating's most important result.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- closeout: n_writes on the way out against C1-P on the way in, and load_default saying the 5 s branch was reached.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-P1 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio ; cat /proc/load_default' --idle 4 --seconds 40
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-10/C13-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
```

### 11.1 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The four files under `bench-only/r59-20260910/` never move again.

```cardnum
img-bytes	1052672	size /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin
img-sha16	c890e0efeb6881ec	sha256-16 /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin
vmlinux-bytes	4095382	size /home/key/fwre-work/rebuild/bench-only/r59-20260910/vmlinux
vmlinux-sha16	fe12f9ea0d78803f	sha256-16 /home/key/fwre-work/rebuild/bench-only/r59-20260910/vmlinux
map-bytes	384617	size /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map
map-sha16	5217513de5179e55	sha256-16 /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map
keys-probe	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_keys_probe$
keys-read-proc	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_keys_read_proc$
gpio-read-proc	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_gpio_read_proc$
leds-gpio-probe	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} [A-Za-z] gpio_led_probe$
spi-map-read-proc	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_spi_map_read_proc$
gpio-keys-absent	0	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map gpio_keys_probe$
expansion-captures	55	count bench/2026-09-10/PREDICTIONS-B18-block17.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-10/C[0-9]+-
expansion-loops	13	count bench/2026-09-10/PREDICTIONS-B18-block17.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell C[0-9]+ --out-dir
expansion-cold	1	count bench/2026-09-10/PREDICTIONS-B18-block17.md --out bench/2026-09-10/C[0-9]+-A --esc 150
expansion-reboot	13	count bench/2026-09-10/PREDICTIONS-B18-block17.md -{2}send 'busybox reboot -f'
expansion-map0	2	count bench/2026-09-10/PREDICTIONS-B18-block17.md ^/usr/bin/python3 .*echo map 0 > /proc/rtl819x-spi
expansion-pair	13	count bench/2026-09-10/PREDICTIONS-B18-block17.md -{2}send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio'
expansion-open	7	count bench/2026-09-10/PREDICTIONS-B18-block17.md sleep [0-9]+ < /dev/input/event0
expansion-interval	5	count bench/2026-09-10/PREDICTIONS-B18-block17.md echo interval [0-9]+ > /proc/rtl819x-keys
expansion-tryout	2	count bench/2026-09-10/PREDICTIONS-B18-block17.md echo tryout [0-9]+ > /proc/rtl819x-gpio'
expansion-lock	2	count bench/2026-09-10/PREDICTIONS-B18-block17.md echo (un)?lock 6 > /proc/rtl819x-gpio
expansion-brightness	4	count bench/2026-09-10/PREDICTIONS-B18-block17.md echo [01] > /sys/class/leds/n150rt:green:led2/brightness
cells-fence	55	count bench/2026-09-10/PREDICTIONS-B18-block17.md ^bench/2026-09-10/C[0-9]+-[A-Z0-9]+$
send-over-127	0	count bench/2026-09-10/PREDICTIONS-B18-block17.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-10/PREDICTIONS-B18-block17.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
no-flr	0	count bench/2026-09-10/PREDICTIONS-B18-block17.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-10/PREDICTIONS-B18-block17.md -{2}send '[^']*(EW |EB |FLW )
```

---

## 12. The fence

```cells
bench/2026-09-10/C1-A
bench/2026-09-10/C1-M0
bench/2026-09-10/C1-P
bench/2026-09-10/C1-CL
bench/2026-09-10/C1-T5
bench/2026-09-10/C1-T12
bench/2026-09-10/C1-P2
bench/2026-09-10/C1-RB
bench/2026-09-10/C2-P
bench/2026-09-10/C2-RB
bench/2026-09-10/C3-P
bench/2026-09-10/C3-RB
bench/2026-09-10/C4-P
bench/2026-09-10/C4-RB
bench/2026-09-10/C5-P
bench/2026-09-10/C5-RB
bench/2026-09-10/C6-P
bench/2026-09-10/C6-RB
bench/2026-09-10/C7-P
bench/2026-09-10/C7-RB
bench/2026-09-10/C8-P
bench/2026-09-10/C8-RB
bench/2026-09-10/C9-P
bench/2026-09-10/C9-RB
bench/2026-09-10/C10-P
bench/2026-09-10/C10-X
bench/2026-09-10/C10-RB
bench/2026-09-10/C11-P0
bench/2026-09-10/C11-L1
bench/2026-09-10/C11-L2
bench/2026-09-10/C11-L3
bench/2026-09-10/C11-L4
bench/2026-09-10/C11-L5
bench/2026-09-10/C11-L6
bench/2026-09-10/C11-RB
bench/2026-09-10/C12-O
bench/2026-09-10/C12-O2
bench/2026-09-10/C12-O3
bench/2026-09-10/C12-A10
bench/2026-09-10/C12-B10
bench/2026-09-10/C12-A50
bench/2026-09-10/C12-B50
bench/2026-09-10/C12-A200
bench/2026-09-10/C12-B200
bench/2026-09-10/C12-Z
bench/2026-09-10/C12-RB
bench/2026-09-10/C13-P0
bench/2026-09-10/C13-D
bench/2026-09-10/C13-A50
bench/2026-09-10/C13-H50
bench/2026-09-10/C13-A10
bench/2026-09-10/C13-H10
bench/2026-09-10/C13-M1
bench/2026-09-10/C13-P1
bench/2026-09-10/C13-RB
```

**55 cells.** Every capture in this seating is inside the fence; there is no
`PC` or `X` outside it, which seating 15's card got wrong and which
`check-predictions` `N8`/`N9` now catch.
