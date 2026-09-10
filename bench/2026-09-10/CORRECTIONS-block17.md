# Corrections — block 17, seating 20, 2026-09-10

**§ 0 was written BEFORE power and before any cell ran.** The frozen card
(`PREDICTIONS-B18-block17.md`, mtime `17:45:05 +0800`) may not be edited —
`check-predictions` reads its mtime and the tool's own docstring says fixing
even a typo has to make the check fail — so a defect found after the freeze
lands here, and it lands here *before* it is executed rather than after,
because "the operator remembers" is not a mechanism.

---

## 0. The pre-power audit

### 0.1 🔴 Five cells stop eleven to twenty-one seconds before their own output

**量, three independent ways.**

`tools/console-capture.py:786` —

```python
if args.idle and now - last_byte_at >= args.idle:
    stop_reason = f"--idle {args.idle} with no bytes"
    break
```

with `last_byte_at = t0` at `:509` and reassigned only when bytes arrive
(`:567`). So `--idle N` is *N seconds since the last byte on the wire*, and a
payload that is deliberately silent for longer than `N` ends the capture in the
middle of its own silence.

Five cells on the card send a payload whose first act is a silence longer than
their `--idle`:

| cell | payload's longest silence | `--idle` | capture stops at | output arrives at |
|---|---|---|---|---|
| `C12-B10` | `sleep 15` | 4 | **≈ 4.0 s** | ≈ 15.2 s |
| `C12-B50` | `sleep 15` | 4 | **≈ 4.0 s** | ≈ 15.2 s |
| `C12-B200` | `sleep 15` | 4 | **≈ 4.0 s** | ≈ 15.2 s |
| `C13-H50` | `sleep 25` | 4 | **≈ 4.0 s** | ≈ 25.4 s |
| `C13-H10` | `sleep 25` | 4 | **≈ 4.0 s** | ≈ 25.4 s |

Arrival time is `len(send)/3840 + sleep + out_bytes/3840` at 38400 8N1, with
`out_bytes` taken from committed captures of the same commands, not estimated.

**The corpus is the second source and it is 7 of 7.** Over all 953 committed
captures that carry a `stop_reason`, 473 used `--idle`; **seven** of those
carry a `sleep N` in `--send`, and in **every one of the seven** `--idle`
exceeds the sleep — the widest gap in the record is `sleep 5` under `--idle 8`.
`bench/2026-09-09b/C1-R0` is the closest analogue on the card's own shape
(`cat ; sleep 3 ; cat ; sleep 3 ; cat`, `--idle 4`) and it ran **10.134 s**,
which is what the model above predicts to within the read granularity. **No
capture in this project has ever run `--idle` under a longer sleep**, so the
five cells are outside the behaviour the corpus establishes, not a variation of
it.

**The third source is a checker with positive controls**, which is the only
kind this project accepts: five synthetic cells, one per rule, **5 of 5 fired**,
including a probe with exactly this shape.

🔴 **What makes it worth writing down is that it would not have looked like a
failure.** The command line's own echo comes back in ~14 ms, so each of the
five would have produced a capture of roughly **54 bytes** with the clean
`stop_reason` `--idle 4.0 with no bytes` — and `check-predictions` scores a
cell on whether a capture exists and postdates the card, not on its content.
**The seating would have reported `55 of 55` with the entire press ladder and
both long holds empty.** The operator's three presses would have been real, the
ring would have recorded them, and nothing would have read the ring.

🔴 **And it does not stop at the five.** The port closes while the board is
still inside `sleep`; the shell is not reading stdin, so the *next* cell's
command line goes into the tty's canonical buffer and is executed after the
sleep returns — with that cell's `cat` output landing in the *following* cell's
capture. `C12-A50`'s `echo clear` would then wipe the ring at an undefined
point relative to the presses, and the rung attribution the ladder exists for
would be gone.

### 0.2 The correction, which is the removal of one flag and no change to any number

`--seconds` alone satisfies the terminator rule (`console-capture.py`'s guard
requires *either* `--seconds` or `--idle`, and refuses before the port is
opened). The card's own `--seconds` values were chosen as the worst case for
the physical act, so keeping them exactly means the operator's window is
precisely what the card's comment above each cell says.

| cell | as frozen | as run |
|---|---|---|
| `C12-B10` | `--idle 4 --seconds 40` | `--seconds 40` |
| `C12-B50` | `--idle 4 --seconds 40` | `--seconds 40` |
| `C12-B200` | `--idle 4 --seconds 40` | `--seconds 40` |
| `C13-H50` | `--idle 4 --seconds 55` | `--seconds 55` |
| `C13-H10` | `--idle 4 --seconds 55` | `--seconds 55` |

Rejected alternatives, so the choice is on the record rather than in someone's
head:

* **`--idle 18` / `--idle 28`** — ends the cell sooner (≈ 33 s and ≈ 53 s) but
  introduces two numbers the card does not contain, for a saving of seven
  seconds and two seconds respectively.
* **`--until` on a field of the final `cat`** — would end each cell ~24 s
  earlier *and* record whether the output arrived at all, which is the better
  instrument. **Rejected because there is no safe pattern**: 讀
  `rtl819x-keys.c`'s `read_proc`, the last thing it prints is the `ev` ring
  loop, whose length is exactly what the ladder is measuring. `--until` on
  `b0_n_report` would fire before the ring and the drain that follows a match
  is **50 ms = 192 bytes at 38400**, against a full ring of 32 lines ≈ 800
  bytes. It would truncate the instrument. (This is why `--until 'val04'` *is*
  safe on the pair cells and `--until 'map_lines'` *is* safe on the map cells:
  in both drivers that field is the last `sprintf` in the function — 讀
  `rtl819x-gpio.c:100` and `rtl819x-spi.c:80` — and seating 19's `C1-M0`
  measured `until_offset 2997` against `bytes 3013`, so 16 bytes came back
  after the match.)

The cost is **230 s of dead air** across the five cells (3 × 40 + 2 × 55, minus
the ~86 s of real payload), against a seating whose measured budget is ~16 min
of instrument time in a window of over four hours. It is not a trade worth
optimising.

### 0.3 The two AMBERs, dismissed with the reason

`C11-L3` (`--send` is 104 characters) and `C11-L5` (90) are over `FW-49`'s
80-character threshold, so `busybox ash`'s line editor will wrap the **echo**
and the capture will carry `\r\r\n`. Both are under the loader's 128-byte
readline cliff, and `FW-49` measured that **output is never wrapped** — an
88-character `/proc/version` line arrived whole in five captures — so no field
either cell reads can be broken by it. Recorded because a `\r\r\n` in a capture
has two sources and only one of them is a wrap.

### 0.4 What the audit checked and found clean

| | |
|---|---|
| `--until` matching its own `--send` echo | 0 of 55 (`arm_until()` is called after the write, so the echo is inside the search window) |
| `--send` ≥ 128 characters | 0 of 55 |
| a payload that can reset the board with no `--esc-after` | 0 of 55 — every `busybox reboot -f` carries `--esc-after 20` |
| `--seconds` too small for its own payload | 0 of 55 |
| fence against commands | 55 = 55, exact |
| every boot ends in a `-RB` cell | 13 of 13 |

### 0.5 The gates and the artefact, re-run at 19:2x before power

| | |
|---|---|
| `cardcheck commands` | 54 commands, 54 SHELL, 18 invocable names — **rc 0** |
| `cardcheck numbers` | **28 of 28 re-derived** |
| `check-predictions` | **0 of 55**, which is what an unrun card must read |
| staged image | four files, all four sha256 and all three sizes byte-for-byte the card's `§1`, mode `-r--r--r--` |
| `rlxfw-marks verify` on the frozen `vmlinux` | 12 marks, 8 witnesses, **0 not a discriminator**; `MK5 absent: rtl819x_spi_write_page` **0**, `MK7 str: n150rt:green:led2` **1**, `MK8 str: rtl819x-keys/input0` **1** |
| `D4` on the frozen `System.map` | `rtl819x_spi_write_page` **0**, and the vendor's `mtd_spi_write` / `mtd_spi_erase` **1** each — the honest form of that claim |
| `looprun --mode plan` | rc 0 for `--skip S2,S3,S4` and for `--skip S2,S3`. ⚠️ **Three of looprun's refusals are gated on `mode in ("desk","bench")`**, so `plan` proved the recipe-override and image checks and **not** the artefact-clash check; `bench/2026-09-10/` holds no capture, so there is nothing to clash with |
| host link (`S5c`'s `P-a`) | `ip -4 route get 10.1.1.1` prints a `dev <if>` **and a `src 10.1.1.2`**, which is the whole of what `P-a` reads. The address does not survive a usbipd re-attach and the adapter was re-attached at 19:15 — `RUNSHEET` `P3` has bitten on this twice. *(The interface name is written `<if>` deliberately: it encodes the host adapter's MAC, `leakscan` classifies it `HOST`, and this row does not need it — eight committed files already carry one and this one need not be the ninth.)* |
| free pre-flight, board off | 3.070 s, **0 bytes**, port opened — which removes the adapter and the port from the tool's own three causes and leaves the board |

### 0.6 The deadline this card set itself

`bench/2026-09-10` asserts that every capture **starts** before `00:00` on
2026-09-11, and `started_wallclock` is local time with an offset
(`2026-09-10T19:17:17+0800`, from the pre-flight's own metadata), so the
deadline is local midnight. Measured at open: **2026-09-10 19:14:5x +08:00** on
all three of Git Bash, WSL and Windows, epoch `1789038891` / `1789038896` /
`1789038899`. 量, the same instant: `Get-Date -UFormat %s` read
`1789067699` — **28,800 ahead, exactly UTC+8**, which is `CLAUDE.md`'s
PowerShell trap ⑥ reproduced rather than quoted.

Budget, derived from the two most recent seatings rather than estimated:
**looprun median 39.5 s** over 17 invocations (min 38.5, max 40.1);
`--until` cells that matched ended at a **median 1 %** of their cap. Estimate
for this card **≈ 16 min** of instrument time, worst case **≈ 46 min**, plus
the operator's own time in three episodes. § 10's drop order is not expected to
be needed.

*(量 afterwards, on this seating's own artefacts: `looprun` rz→boot **38.95 s**
median over the 16 invocations that ran an `S4`, min 38.89, max 39.95 — the
prediction was 1.4 % high. Instrument time is not separable from the operator's
here, because seven cells waited on a hand. The drop order was not used and no
cell was dropped.)*

---

## 1. The headline, in one paragraph

**One power cycle against a budget of one. Seventeen boots, 169 captures, 55
carded cells and 29 declared off-card ones, `check-predictions` 55 of 55,
`capdate` 0 RED over 29 directories and 1,121 captures, `flashwin scan` CLEAN
over 3,964 files, `xcheck sweep` 0 disagreements over 1,125 artefacts.**
🟢 **`R5-7` and `R5-8` both met their DoD**: an unmodified upstream `leds-gpio`
bound to a `gpio_chip` of mine produced **light** from a sysfs write, with the
operator's own negative control; and a polled input device of mine turned a
press of the board's reset button into `input_report_key()` calls, with the
three-state open control coming out **(0, 0) → (1, 60) → (2, 120) → (2, 120)**
— sixty polls per three-second open, twice, and **flat** when the sleep carried
no open. 🔴 **The largest result was on no card**: the vendor's
`rtl_gpio_timer` acts **once per boot**, and nine button episodes across four
boots say so with two independent observables. **Zero flash-write commands,
zero `FLR`, `n_writes 4` and every one of the four accounted for.**

---

## 2. The frozen card, cell by cell

### 2.1 `D1` — the boot capture

**Seventeen boot captures, every one 1,637 bytes, against a prediction of
1,637.** The card's own ladder named 1,493 / 1,551 / 1,580 as the three ways it
could have stopped short; none of them happened, and **213 of those bytes had
never been on this die**.

By value, every mark the card names: `K2 = 00000000`, `K3 = 00000001`,
**`K4 = FFFFFFFA`** (`-ENXIO`, the same errno the `/proc` file prints as `-6`
from a second call site), `K5 = K7 = 00000000`, `K6 = 00000000`,
`RLXFW-ID0=692A2801` — the id the build computed, compared by `looprun`'s `A3`
and typed by nobody.

🟢 **The seventeen fall into exactly two sha256 values, 14 and 3, and the whole
difference is ONE LINE**: `RLXFW-G3=0000007C` against `RLXFW-G3=0000003C`, which
is bit 6 — the LED the vendor's `rtl_gpio_timer` leaves wherever its last
episode left it. Every other byte of every boot is identical. **Two new drivers
were added to this image and its initialisation is still deterministic to the
byte.**

### 2.2 § 3.1's ordering prediction, which quotes no address

讀 `drivers/Makefile`: `gpio/` at :8, `input/` at :71, `leds/` at :94, and
`rtl819x-keys` and `leds-gpio` are both `device_initcall`, so link order
decides. 量, the byte offsets inside `C1-boot.log`:

| mark | offset |
|---|---|
| `G0` … `G6` | 448 … 553 |
| `K0` … `K8` | **987 … 1121** |
| `G7`, `G8` | **1131, 1150** |

**Every `K` precedes `G7`/`G8`**, and `G0`…`G6` precede everything because the
`gpio_chip` is a `subsys_initcall` (4) and the other two are `device_initcall`
(6). Nothing was asked of the kernel about itself; the reading is an ordering
in one file.

### 2.3 § 3.2 / § 3.3 — **62 of 66 fields hit**

The four misses are § 3, and two of them are the same mistake.

🟢 The hits include every one that carries a decision: `cnr FFFFFF8B`,
`dir FF000040`, `dat 0000007C`, `known_mask 00000060`, **`allow_out_mask
00000040`** (the card said `00000000` here means the mask change did not reach
the artefact and the block stops — it reached it), `out_effective 00000040`,
`n_req_ok 2`, `n_dirin_ok 1`, `n_dirout_ok 1`, `n_set_ok 0`, `n_writes 2`,
`state_last 0000007C`, `n_state_foreign 0`, `b0_code 408`, `b0_need 2`,
`irq_probe`/`irq_live`/`enxio` all `-6`, `poll_ms 50` / `poll_jiffies 5` /
`hz 100`, `n_open 0` / `n_poll 0`.

🟢 **Ten at-rest pair reads, ten boots, 68 fields each, and the only fields
that ever differ are `j_now` — which is free-running — and `boot_dat`'s bit 6**,
which is § 2.1's one line seen from the `/proc` side.

### 2.4 § 2.1's decision ①, and the half that could have refuted it

`FW-61` predicted that `tryout 5` would reach **this driver's** guard rather
than being turned away earlier by gpiolib, because `gpio_ensure_requested()`
tests `test_and_set_bit(...) == 0` and `test_and_set_bit` returns the **old**
value, so a line already held by `rtl819x-keys` skips the whole compatibility
path and returns 0.

量, and all three legs hold:

| cell | measured |
|---|---|
| `C1-T5` | **`RLXFW-G-TRYRC=FFFFFFFF`** = `-EPERM`, from the guard, with `TRYCNR`/`TRYDIR`/`TRYDAT` XORs all `00000000` |
| `C1-T12` | **`FFFFFFED`** = `-ENODEV`, and `n_req_no` +1 with `n_dirout_no` unmoved — refused at `.request`, `.direction_output` never reached |
| `C1-CL` | `cat: write error: Device or resource busy` — gpiolib arbitrating between my chip and a **real** consumer, where on `r58` the same `EBUSY` was an artefact of the `tryout` above it |

🔴 **`n_req_ok` reads `2` in both `C1-P` and `C1-P2`.** The card wrote that a
move to 3 refutes the reading of `test_and_set_bit` and takes the whole
subsection with it. It did not move.

### 2.5 § 5.1 — the guard's two-sided test, and the eye

Three operator readings and six register readings, in order:

| cell | operator | `dat` | `out_locked` | `out_effective` | `n_set_ok` | `n_set_no` | `n_writes` |
|---|---|---|---|---|---|---|---|
| `C11-L1` | **LED #2 lights, #1 and #4 unchanged** | `0000003C` | `00000000` | `00000040` | 1 | 0 | **3** |
| `C11-L3`/`L4` | **still lit**, `brightness` reads back `0` | `0000003C` | `00000040` | `00000000` | 1 | **1** | **3** |
| `C11-L5`/`L6` | **dark** | `0000007C` | `00000000` | `00000040` | **2** | 1 | **4** |

🟢 **Every field the card predicted, including the one that matters most:
`n_writes` does not move at `C11-L4`.** The refusal happens *before* the write,
not after it, so `out_locked` is a gate and not a log.

🟢 **`RC7`**: `ls /sys/class/leds` prints `n150rt:green:led2` and nothing else.
The 1,637-byte capture could not have settled that and the directory listing
does.

### 2.6 § 6 — the press ladder, and four integer-exact poll counts

| cell | interval | `b0_need` | `n_poll` | `j_last − j_first` | `n_edge` | `n_press` | `n_bounce` | press durations |
|---|---|---|---|---|---|---|---|---|
| `C12-B10` | 10 ms | **10** | 1498 | 1497 = 1497 × 1 | 6 | **3** | 0 | 0.78 0.90 0.21 s |
| `C12-B50` | 50 ms | **2** | 301 | 1500 = 300 × 5 | 4 | **2** | 0 | 0.55 0.55 s |
| `C12-B200` | 200 ms | **1** | 75 | 1480 = 74 × 20 | **6** | **2** | 0 | 1.00 0.20 0.80 s |
| `X8-b50l` (off-card) | 50 ms | 2 | 297 | 1480 = 296 × 5 | 6 | **3** | 0 | 1.25 0.60 0.95 s |

🟢 **`j_last − j_first` is exactly `(n_poll − 1) × poll_jiffies` on all four
rungs**, with no remainder, at three different intervals. The poll loop runs at
the period the driver programmed and drops nothing.

🟢🟢 **`C12-B200` is the sharpest cell of the ladder and it needed the ring
rather than a counter.** Six edges — all three physical presses are in the log —
and `b0_n_press` **2**. The press the debouncer declined is the **0.20 s** one,
which is exactly one poll period at `b0_need = 1`. **The instrument recorded a
physical act and the debouncer refused it, and only the ring can tell those two
apart.**

🔴 **The card's `b0_n_press = 3` at every rung is refuted, and the two failures
have different causes.** At 200 ms it is the debouncer, above. At 50 ms
(`C12-B50`) only four edges arrived, i.e. one press left no trace at all — and
the operator's own count was *"should have been three, but I am not sure about
the 0.5 s"*. **`X8-b50l` is the off-card control that separates the sampler
from the operator**: three deliberate 0.6–1.25 s presses at the same 50 ms give
**3 of 3**, so 50 ms sampling does not lose a press that is comfortably above
threshold. What the ring cannot do is give the duration of a press it never
saw, and that limit is stated rather than argued around.

⚠️ **`b0_need × interval` is 100 ms at both the 10 ms and the 50 ms rung** —
10 × 10 and 2 × 50 — so the two rungs share a *threshold* and differ in
*resolution*. The card's monotonicity prediction (`n_edge` non-increasing down
the ladder) reads 6 → 4 → 6, which is not monotone; but the card's stated
refutation was *`n_edge` at 200 ms exceeding `n_edge` at 10 ms*, and 6 does not
exceed 6. **The dip is a missing press at rung 2, not extra edges at rung 3**,
and edges-per-press is 2 at every rung.

### 2.7 § 6's three-state control

| | `n_open` | `n_poll` |
|---|---|---|
| before any open (`C12-O`, first read) | **0** | **0** |
| after one 3 s open (`C12-O`, second read) | **1** | **60** |
| after a second 3 s open (`C12-O2`) | **2** | **120** |
| after a 3 s sleep with **no** open (`C12-O3`) | **2** | **120** |

**20 Hz × 3 s = 60, twice, and zero without an open.** `j_last − j_first` on
the first open is **295 = 59 × 5**, i.e. sixty polls five jiffies apart. The
polling is *caused* by the open: it starts and restarts with them, twice, and
does not run without one.

### 2.8 § 8 — the flash bracket

`C1-M0`, `C13-M1` and the off-card `X29-M2` are **byte-identical to each other
and to `bench/2026-09-09/C1-M0.log`**, sha256
`b3d3d7d081310c0d30d6fa02f4362181ed83345d3dbd859907b072f2c9e63fc9`. **Four maps
of group 0's 32 units, two seatings, one digest**, with every press of this
seating — carded and off-card — inside the last two.

⚠️ Unchanged: this is *the map agrees with itself and with the 2026-08-16
dump*. It cannot see two writes that cancel, it does not read `H601`, and no
`FLR` ran. `FLS-26`'s ledger does not move.

---

## 3. The three predictions this card got wrong

### 3.1 🔴 `cnr_as_spec` / `dir_as_spec` — the card would have stopped a healthy block

§ 3.2 predicts `1` / `1` and says **`RC3` fires on either being 0**. Both read
**0**.

**It is a desk error, and the corpus says so before the device does.** 讀
`rtl819x-gpio.c:258`: `RTL819X_GPIO_CNR_EXPECT = 0xFFFFFFDF` and
`DIR_EXPECT = 0xFF000000` — those are `REG-26`/`REG-27`, the **loader-state**
readings of 2026-08-24. Under Linux the live values are `FFFFFF8B` / `FF000040`
(`REG-35`, 量 seating 15). 量 over every committed capture that prints the
field — **29 files from two earlier seatings, 35 occurrences, every one `0`** —
and the same files read `cnr FFFFFF8B` / `dir FF000040`. This seating adds 46
more files and twelve at-rest reads, all `0`.

🟢 **The board prints both numbers in the same capture and that is what makes
this a desk error rather than a question**: `C1-P` carries `cnr FFFFFF8B`
beside `boot_cnr FFFFFFDF` and `dir FF000040` beside `boot_dir FF000000`. The
`EXPECT` constants are the `boot_*` values. Nothing needs re-measuring.

🔴 **So the card's `RC3` as written would have fired on every seating this
project has ever run, including the one that established `REG-35`.**
`notes/gpio-driver.md`'s own `RC3` row is the correct one — its substantive
halves are the *live* values, and both hold. The block did not stop.

⚠️ **`cardcheck numbers` passed 28 of 28 and could not have caught this**: the
`1 / 1` is prose in a table, not a `cardnum` row. A predicted value that no
`cardnum` row can re-derive is a value nothing checks until the board contradicts
it.

### 3.2 🔴 `n_get` and `n_state_chk` — the table is right about the driver and wrong about the cell

§ 3.2 predicts `n_get 1` and `n_state_chk 1` on the first read of a boot; the
carded pair cells read **3**. § 3's own preamble says the opposite of its table
— *"the two `/proc` files are read keys first, then gpio, always, so that the
gpio counters include the keys read's own `gpio_get_value`"* — so the card
contradicts itself fifteen lines apart.

🟢 **And the table's numbers are measured true, on the one cell of this seating
that has no keys read in front of it.** `C11-P0` is
`ls /sys/class/leds ; cat /proc/rtl819x-gpio` and it reads **`n_get 1`,
`n_state_chk 1`** — the card's values exactly — where all eleven pair reads read
3 and 3. **The prediction is not wrong about the driver; it is placed under a
cell it does not describe.** That is a narrower and more useful defect than
*"the card got the counters wrong"*, and it was found by re-reading the corpus
after the operator asked whether the four misses needed re-measuring.

🟢 **Three off-card cells decomposed it into single variables and found
something § 4 did not have.** `X1`/`X2`/`X4`/`X5`/`X6` are the *same* command —
`cat /proc/rtl819x-gpio` — five times with nothing else touching the port:

| | `n_get` | `n_state_chk` | Δ |
|---|---|---|---|
| `X4` | 7 | 18 | — |
| `X5` | 7 | 20 | **+2** |
| `X6` | 7 | 22 | **+2** |

and `X2 → X3` (which adds one keys read in front) moves `n_get` by **+2**.

🔴 **So one `cat` is TWO `read_proc` invocations**, on both files — 2.6.30's
`proc_file_read` calls the handler again after `*eof`, and the second call is
what the card's Identity 1 and Identity 2 do not carry. **Both identities have a
factor of two on their `/proc` terms.** Correcting them is desk work and the
data to do it is in this directory.

⚠️ **One outlier is left standing rather than smoothed away**: `X1 → X2` is
**+3**, where every later pair is +2. This data does not explain it.

### 3.3 🔴 § 7's ratio, and the control that could not have worked as carded

§ 7 predicts `n_state_foreign / n_state_chk → 0.5` over an integer number of
2 s periods, with `C13-H10` — the same act at five times the poll rate — as the
control that the ratio *must not move*.

`C13-H50` gives **240 / 505 = 0.4752**. `C13-H10` gives **2503 / 2503 =
1.0000**.

🔴 **The control is void, and the card contains the reason it is void.** § 2.2
cites `REG-37` — bit 6 stays latched low for at least 152.1 s after a long press
— to order the LED episode *before* the holds. **The same fact makes the second
hold's starting state contaminated**, because `C13-A10` does not touch the LED
and nothing between the two holds re-establishes the driver's reference. Every
one of `C13-H10`'s 2,503 checks was foreign because bit 6 was already low when
it started, not because the poll rate changed. **The card applied `REG-37` to
one ordering decision and not to the other.**

🟢 **And `REG-37`'s own sentence is now narrower.** It says the latch *"is not
recovered by re-running"*. 量, `X10-dark`: one `echo 0 > …/brightness` takes
`dat` from `0000003C` to **`0000007C`**, and `X11-hold` reads it again with
nothing written and finds it still high with `n_state_foreign` frozen. **True of
re-pressing; false of writing.** `R5-7`'s LED path recovers it in one write, so
the ordering constraint is *"worthless unless something re-establishes the
reference"*, and this image has something that does.

🟢 **With the reference re-established the control ran for real** (`X12`/`X13`,
off-card) and it did not measure what § 7 wanted either — see § 4.

---

## 4. 🔴🟢 The result that was on no card: the vendor's timer acts once per boot

Nine button episodes over four boots, two poll rates, and two independent
observables.

| boot | ep | cell | interval | Δ`chk` | Δ`foreign` | ratio | longest contact | operator's eye |
|---|---|---|---|---|---|---|---|---|
| 13 | 1 | `C13-H50` | 50 ms | 505 | **240** | **0.4752** | 18.35 s | — |
| 13 | 2 | `C13-H10` | 10 ms | 2503 | 2503 | 1.0000 | (never released) | 一直亮 |
| 13 | 3 | `X13-h10` | 10 ms | 2507 | **0** | 0.0000 | 13.38 s | 暗 |
| 14 | 1 | `X15-h1` | 50 ms | 505 | **240** | **0.4752** | 20.95 s | **鮮亮一下,後來一直閃** |
| 14 | 2 | `X17-h2` | **50 ms** | 505 | **0** | 0.0000 | 21.45 s | **沒亮** |
| 15 | 1 | `X19-short` | 50 ms | 405 | 314 | 0.7753 | 4.30 s | 恆亮了 |
| 15 | 2 | `X21-long` | 50 ms | 505 | **0** | 0.0000 | 6.85 s | — |
| 17 | 1 | `X26-short3` | 50 ms | 305 | **0** | 0.0000 | **0.45 s** | 沒反應 |
| 17 | 2 | `X28-long` | 50 ms | 505 | **268** | **0.5307** | 17.90 s | 亮 → 過一陣開始閃 → 放開還亮 |

**The rule that fits all nine with no exception**: `rtl_gpio_timer` acts on the
**first press of a boot that is held past about two seconds**, and never again
on that boot. A press that never reaches that branch neither starts it nor
consumes it.

Three confounds were broken, each by an experiment rather than by argument:

1. **poll rate.** Boot 14's two holds are both at 50 ms — one blinks, one does
   not. The `interval` is not the variable.
2. **`default_flag`.** `H_B` was *the blink stops once the ≥5 s branch writes
   `'1'`*. Boot 15's second hold made a **6.85 s** contact with
   `/proc/load_default` reading **`0`** before it and **`0`** after. The flag
   never moved and the blink was still gone.
3. **"any press consumes it".** `H_A` was that. Boot 17's first episode is a
   **0.45 s** press with `foreign 0` and `load_default 0`, and the **17.90 s**
   hold after it on the same boot blinks (**0.5307**) and takes
   `/proc/load_default` to **`1`**.

🟢 **`/proc/load_default` is the second observable and it agrees five times
out of five**, including the two that matter: a 6.85 s contact leaving it at
`0` (timer dead) and a 17.90 s hold after a short press taking it to `1` (timer
alive). **The LED branch and the factory-default branch live and die together**,
which is what `FW-40` says about them — they are the same timer.

⚠️ **The consequence is large and is stated as 推**: on this board the reset
button's `>= 5 s` factory-default branch can be reached **once per power-up**,
by the first press that exceeds about two seconds. This seating measured the
behaviour; the mechanism is a disassembly question and `FW-40`'s own reading is
where it goes.

### 4.1 And the duty cycle is not 0.5 — there is a steady phase first

The operator's third reading — *"lit first, then after a while it starts
blinking, and after release it stays lit"* — is what explains why every blinking
hold measures 57–61 % low rather than 50 %. Solving `T + (hold − T)/2 =
low_time` on the three holds that blinked:

| cell | hold | low fraction | **T** |
|---|---|---|---|
| `C13-H50` | 18.35 s | 0.608 | **3.95 s** |
| `X15-h1` | 20.95 s | 0.573 | **3.05 s** |
| `X28-long` | 17.90 s | 0.609 | **3.90 s** |

**A steady-lit phase of about 3–4 s, then the alternation.** `X19-short`'s
4.30 s hold is the fourth point: it went low 1.75 s in and never alternated,
which is the same phase seen from inside it, and the operator called it
*"恆亮了"*.

### 4.2 The eye as an instrument: ten readings, ten agreements, and one thing only it could give

| the operator said | the register said |
|---|---|
| lit, and #1/#4 unchanged | `dat 0000003C`, `n_set_ok 1` |
| still lit | `dat` still `0000003C`, `n_writes` unmoved |
| dark | `dat 0000007C`, `n_set_ok 2` |
| 一直亮著 | ratio **1.0000** |
| 恆亮了 | ratio 0.7753, bit 6 low from 1.75 s into a 4.30 s hold |
| 暗 / 沒亮 / 都沒亮 | ratio **0.0000**, three times |
| 0.5 秒 LED 沒反應 | `n_state_foreign 0`, `load_default 0` |
| 鮮亮一下,後來一直閃 | ratio **0.4752** |
| **亮 → 過一陣開始閃 → 放開還亮** | ratio 0.5307, `dat` ends `0000003C` |

🟢 **The last row is the one the counters could not have produced.** A ratio of
0.61 is equally consistent with *"low for 61 % of the samples, spread evenly"*
and with *"steadily low for the first 3.9 s, then alternating"* — the driver
counts samples and does not timestamp their values. **The operator's sentence
is what chose between them**, and § 4.1's `T` exists because of it.

⚠️ The eye is not a second source for the register in these rows; the two
answer the same question by different routes and agreed ten times out of ten,
which is what makes the tenth reading worth acting on.

---

## 5. The off-card cells, declared

Twenty-nine captures in this directory are outside the card's fence. They are
listed here because a seating whose off-card work is not declared is a seating
whose `55 of 55` means less than it looks.

| cells | why |
|---|---|
| `X1`,`X2`,`X4`,`X5`,`X6`,`X3` | § 3.2's decomposition — the same `/proc` read repeated to isolate one variable |
| `X7`,`X8` | the press-ladder control: 50 ms with deliberately long presses |
| `X9`,`X10`,`X11` | whether the driver can retake bit 6 from `REG-37`'s latch |
| `X12`,`X13` | § 7's control, re-run with a clean reference |
| `X14`,`X15`,`X16`,`X17` | boot 14 — the blink reproduced, then the poll-rate confound broken |
| `X18`,`X19`,`X20`,`X21` | boot 15 — the `default_flag` confound broken |
| `X22`,`X25`,`X26`,`X27`,`X28` | boots 16 and 17 — the short-press confound broken |
| `X29` | the second flash bracket, closing over every off-card press |

Boot 16 (`X22`) was **abandoned and re-run as boot 17** (`X25`) because the
button may have been touched between arming and the window, and the
experiment's precondition is *the first button activity of this boot is the
three short presses*. **A precondition that cannot be shown to hold is not a
precondition**; the reboot cost 45 s and removed the ambiguity.

---

## 6. What this seating does not claim

1. **Which port of `PABCD` bit 5 and bit 6 belong to.** Unchanged.
2. **That a press reached userspace.** `b0_n_report` counts
   `input_report_key()` calls and nothing in this image decodes
   `/dev/input/event0` (`FW-46`).
3. **Why the vendor's timer runs once.** § 4 is a behaviour with nine
   observations; the mechanism is `FW-40`'s disassembly and it has not been
   re-read.
4. **That `n_state_foreign > 0` identifies the vendor's timer.** It identifies
   *a writer that is not this driver*.
5. **Anything about bounce.** `b0_n_bounce` read **0** in every carded rung, so
   the correct statement is *bounce is below 10 ms or falls between polls*.
   `X21-long` read **1** and it is the seating's only non-zero, on a hold whose
   ring shows sixteen edges — contact chatter, not a clean press.

---

## 7. Defects in my own conduct, with what caught each

1. 🔴 **The five `--idle` cells** — § 0. Caught before power by a checker with
   five positive controls, and confirmed by 7 of 7 in the corpus.
2. 🔴 **A guard of mine produced a false RED and it cost the first power
   window.** A pre-flight check for the `--baud` default grepped the two lines
   after `add_argument("--baud"` for the literal `38400`; the default is the
   named constant `DEFAULT_BAUD`. **The refusal fired before the port was
   opened and before the operator pressed power, so it cost nothing but a
   round trip** — which is the shape a guard should fail in. The corrected form
   checks both halves: that `DEFAULT_BAUD` is 38400 and that the flag defaults
   to it.
3. 🔴 **MSYS path translation bit three times**, on `wsl -d … -- /usr/bin/python3
   /mnt/c/…` and on `wsl -d … -- bash /mnt/c/…`. `CLAUDE.md` records it; the
   heredoc form is the only one that does not. It cost three round trips and no
   bench time.
4. 🔴 **A `--send` of 131 characters was refused by `_check_send`** before the
   port was opened — the loader's 128-byte readline cliff. My cell, not the
   card's; split into two.
5. ⚠️ **`console-capture.py`'s `resolution_note` still says the USB-serial
   latency floor is *"1–16 ms typical, unmeasured on this host"*.** `CLAUDE.md`
   § sixteenth update measured it (floors 0.517 and 0.868 ms). It is a
   correction that did not propagate into a tool's own output, which is exactly
   `XNUM-1`'s shape one instance further out. **Not changed during a seating**;
   carried forward.
6. 🔴 **`check-predictions`' own control `N7` produced ONE spurious RED at the
   closeout, and it does not reproduce.** 量: the closeout run at 22:05 —
   immediately after `git add -A` staged 531 paths — reported
   `FAIL N7 … files=2 regressions=2` against an expected 1, and the tool
   correctly **refused to report on the file at all** rather than passing a
   verdict from a broken instrument. **Five consecutive re-runs are green.**
   ⚠️ **The obvious cause is excluded**: `N7`'s fixtures are built under
   `tempfile.TemporaryDirectory()`, which on this host is WSL's `/tmp` — ext4,
   nanosecond mtime — and the fixture separates its two prediction files with
   `time.sleep(0.02)`, so a granularity collision is not available as an
   explanation. **Cause undetermined**, and it is written down rather than
   widened away: a control that can fail spuriously trains a reader to ignore
   a red, which is the failure this project's whole control discipline exists
   to prevent. The verdict it refused to give was obtained on the re-run and is
   **`55 of 55`**, with the card's mtime still `17:45:05.180107600 +0800`.
