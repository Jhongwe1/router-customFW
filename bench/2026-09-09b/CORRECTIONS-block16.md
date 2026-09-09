# Corrections — block 16, seating 19, 2026-09-09

**One power cycle against a budget of one.** Six boots (five carded plus one
`--attempt 2` retry), thirteen carded cells, six declared off-card cells.
`check-predictions` **13 of 13**, `capdate` **0 RED / 0 stale** over 28
directories and 953 captures, `flashwin scan` **CLEAN** over 123 files,
`audit-bench-log` **rc 0**, `leakscan` **zero hits from this directory**.

**Zero flash-write commands, zero `FLR`, `n_writes 0` at both ends.**

---

## 0. The headline, and it is a photon

🟢🟢 **`R5-7`'s premise is now 量.** `PABCD` bit 6 drives **the second of the
eight LEDs on this board**, **active low**, and the polarity is measured at
*both* levels rather than derived from one:

| `dat` bit 6 | register | the operator's eye |
|---|---|---|
| `1` (`C1-G0`, `C1-R0`, `C1-L2`, `X2`, `X3`, `X4`) | `0000007C` / `0000005C` | **dark** |
| `0` (`X5` after release, `X6`) | `0000003C` | **steadily lit** |

Before today every LED statement in this repository was a register reading
(`REG-37`), a disassembly (`FW-40`), or a datasheet pin row whose own wording is
*"可能是一支 LED 驅動腳"* (`BRD-06`). **None of them was light.** The negative
control is the operator's: of eight LEDs, **only #2 moved**; #1 and #4 were
reported unchanged across the whole seating.

🔴 **This still does not decide which port letter bit 6 belongs to.** That is a
naming question with no live experiment that does not require writing into a
byte believed unimplemented, which `RTL819X_GPIO_ALLOW_OUT_MASK = 0` forbids.
See § 6.

---

## 1. Cell by cell, against the frozen card

| cell | predicted | measured | |
|---|---|---|---|
| `C1-A` | the loader prompt inside a 150 s ESC window | 82,794 bytes, `<RealTek>` reached, `Reboot Result from Watchdog Timeout` count **0** — a cold power-on, not a bite | 🟢 |
| `looprun C1` | the loop closes | **25.66 s**, 8 assertions, `AUTOBURN 00000000`, **the board printed `f67eed22` and the build computed `f67eed22`** | 🟢 (attempt 2 — § 3.1) |
| `C1-M0` | 32 group rows | 3,013 bytes in **13.390 s**, and **byte-identical to `bench/2026-09-09/C1-M0.log`** | 🟢 |
| `C1-G0` | ten fields | `cnr FFFFFF8B`, `dir FF000040`, `dat 0000007C`, `btn_raw 1`, `btn_pressed 0`, `base 0`, `ngpio 32`, `allow_out_mask 00000000`, `n_writes 0`, `/proc/load_default 0` — **10 of 10** | 🟢 |
| `C1-R0` | three `dat` reads, all identical | `0000007C` ×3, **one distinct value** | 🟢 |
| `C1-L1` | `btn_pressed 1` in all three; not all three agree in bit 6 | `btn_pressed 1` ×3; `5C / 1C / 5C` — **two distinct values** | 🟢 |
| `C1-L2` | `load_default 1`; `dat 0000003C` | `load_default` **1** 🟢; `dat` **`0000007C`** 🔴 | § 2.1 |
| `C1-M1` | byte-identical to `C1-M0` | identical over **32 group digests**; the only differing byte is `map_jiffies` — § 2.2 | 🟢 |
| `C1-B3` `C2-B3` `C3-B3` | max − min ≤ 3.0 ms → systematic; > 10 ms → jitter | **1261.205 / 1226.583 / 1258.797 ms**, max − min **34.622 ms** → **JITTER** | § 4 |
| `C4-K` | `kick_ms 10` | `kick_ms 10`, `unlocked 1`, `state BOOTGUARD`, `hw_ovsel 9`, `n_hw_kick 48` | 🟢 |
| `C4-X17` | 2,612.7 – 2,622.7 ms; change +136.8 to +146.8 ms | **2519.632 ms**, change **+43.709 ms** | 🔴 § 5 |
| `C5-P` | `n_writes 0` | gpio `n_writes 0`, spi `n_writes 0` / `n_state_foreign 0`, `load_default 0` | 🟢 |

---

## 2. The card's two refuted predictions

### 2.1 🔴 `C1-L2`'s `dat`, and the retraction of a retraction

The card predicted `0000003C` and the board read `0000007C`. **In session I
announced that `SPEC.md` `REG-37` was refuted. That announcement was wrong and
is retracted here**, because `X5`/`X6` then measured the opposite:

* `X5-blink`, seven samples in the **1–7 s** after a long release: `0000003C`.
* `X6-decay`, thirty samples over **152.1 s**: `0000003C`, every one.

**`REG-37` is not refuted; it is confirmed and strengthened.** Seating 15 had
twelve samples over twelve seconds; this seating has **37 samples across more
than 152 s**, so the latch now has a stability *lower bound* it never had.

🔴 **What is refuted is a hypothesis of mine**: that bit 6 decays back to 1 with
a time constant of seconds-to-minutes. `X6` says it does not move for at least
152 s. **So `C1-L2`'s `0000007C` is UNEXPLAINED.** The only candidate named —
and it is named as a candidate, not a conclusion — is an unrecorded short press
(`FW-40`'s `< 2 s` branch) between `C1-L1`'s release and `C1-L2`, in the window
where the operator was asked to look at the board. No evidence supports it and
none refutes it. **The experiment that would settle it**: a long release
followed by a deliberate short press, with `dat` sampled across both.

### 2.2 🔴 `C4-X17`'s magnitude — see § 5. The direction was right and the size was not.

---

## 3. What went wrong, and all of it is mine

### 3.1 🔴 The USB GbE had no address, and the runsheet row exists because of it

`looprun C1` attempt 1 stopped at **`S5c`** — *the HOST cannot reach 10.1.1.1* —
with `dev=eth0 src=172.18.136.170`, WSL's NAT vNIC. `RUNSHEET.md` § P3 carries
this verbatim, 量 at seating 16: **`10.1.1.2/24` does not survive a re-attach**.
The adapter was attached at 08:32 and never configured.

🟢 **The instrument did its job and this is the second time it has**: `S5c` is
`looprun` 1.1's ARP-based host-link precondition, added at the forty-fourth
segment precisely so a host fault stops **before** the TFTP rather than being
reported in the board's vocabulary. It cost one `looprun` invocation and no
power cycle. The retry used **`--attempt 2`**, not `--force`, so attempt 1's
`C1-rescue.json` and `C1-ab2` burn-flag reading survive on disk.

### 3.2 🔴🔴 A whole-file `cmp` of two flash maps compares a TIMING field, and seating 18's attribution bracket rests on it

The first comparison of `C1-M0` against `C1-M1` was `cmp` over the whole log. It
reported **differ: char 330, line 16** and I read that as the block's stop
condition. The difference is:

```
< map_jiffies 1280
> map_jiffies 1279
```

**One jiffy of traversal duration.** The 32 group digests, `map_diff_units 0`,
`map_h601_skipped 8192` and `corrupt_at -1` are identical.

🔴 **The reach is larger than this cell.** `PROGRESS.md`'s seventeenth update
closes `FLS-26`'s attribution bracket with *"`cmp` on the two seatings' `C1-M0`
logs: **identical**"*. That comparison used the same method, and **it succeeded
because the two seatings' `map_jiffies` happened to be equal**. A one-jiffy
difference in traversal time would have printed, in the most alarming vocabulary
available, that the flash had changed. **The claim survives — re-checked here,
the two logs still agree on every content-bearing field — but the method must
exclude `map_jiffies` and did not say so.** `SPEC.md` `FLS-26`.

⚠️ **And my first replacement check had a control that could not fire.** The
positive control mutated a digest with a `sed` pattern that matched nothing, so
zero bytes changed and the control correctly reported *CONTROL FAILED*. The
working version changes one character of one digest and is caught. **A control
that mutates nothing and a control that is ignored print the same green**, which
is this repository's own recurring shape.

### 3.3 🔴 I read a killed run's residue and believed it was my command's output

`X1-relax` was interrupted mid-run. It left `.log` and `.timing` and **no
`.meta.json`** — the SIGTERM signature `CLAUDE.md` documents. The re-run refused
to overwrite (`rc 2`), and my shell then `grep`ed the **leftover file** and
printed two samples as though they were the new reading.

🟢 **What stopped it becoming a false finding was the tool's overwrite refusal,
not any check of mine.** The retry used a new `--out` rather than `--force`.

### 3.4 🔴 The operator reported the mechanism in their first sentence and I read past it

After the first hold the operator wrote: **「按住後 一開始第二顆有先亮個 然後是
閃爍」** — *at first #2 came on, then it blinked*. I recorded that as "the LED
blinked".

`X5-blink` then measured exactly that, from the register side: **five
consecutive `0000001C` samples (bit 6 = 0, LED solid) followed by strict
alternation**. Against `FW-40`'s 5 s threshold this reads as a designed
two-phase indication — *solid: keep holding; blinking: the flag is armed* — and
**the eye had it before any register did.** In a project whose stated division
of labour is *you build the instruments, I read the dials*, the dial was read
correctly and the instrument-builder discarded half of it.

---

## 4. 🔴 `OVSEL` 3 is JITTER, and the instrument proves it inside the same captures

Three `bite 3` rungs, one seating, one image:

```
  cell      bite interval      in-capture 50 ms ruler
  C1-B3        1261.205 ms            48.796 ms
  C2-B3        1226.583 ms            47.461 ms
  C3-B3        1258.797 ms            49.328 ms
  ------------------------------------------------
  max - min      34.622 ms             1.867 ms      ratio 18.54x
```

The ruler is `verb_bite`'s own `mdelay(50)`, measured from the last byte of the
interleaved `RLXFW-W-BITE` mark to the first byte of `RLXFW-W-GO`, in the same
capture as the interval it bounds. **Its mean of 48.5 ms sitting *below* 50 ms
is correct and is itself a check**: `prom_putchar` fills a FIFO, so the mark's
last byte reaches the host *after* the delay has started, and the ruler reads
`50 ms − drain` with a drain of ≈ 1.5 ms.

**The card's pre-written table is read as written: `max − min > 10.0 ms` →
jitter.**

### 4.1 What that costs seating 18

* 🔴 **The four-rung least-squares residuals (+3.5 / +32.5 / −71.0 / +35.0 ms)
  lose their evidence.** Three of the four are inside a 34.6 ms jitter.
  ⚠️ **This does not restore the linear model**: `OVSEL` 8's −71.0 ms is still
  twice the jitter. The correct state is **undetermined**, and saying the model
  is now supported would be the same error with the sign flipped.
* 🔴 **The "factor of ninety" control was `n = 2`.** Seating 18 read *with
  `WDTCLR`, two readings of the same word differ by 1.456 ms; without, three
  readings spread 131.7 ms*. With `n = 3` the with-`WDTCLR` spread is
  **34.622 ms**, so the contrast is **3.8×**, not 90×. **The mechanism is
  untouched** — `bite` clears the counter and `biteraw` does not — only the
  size of the control moves, by a factor of about 24.
  This segment's own `19094aa` is titled *Two points always fit, and that is the
  reason they prove nothing*; the trap was walked into again one segment later.

### 4.2 🔴🔴 And the ruler itself is not stable across seatings — which nobody had checked

Seating 18's `C2-B3`, re-measured **with this session's code**, gives
**1341.959 ms** against its own write-up's 1,340.982 ms — so the instruments
agree. Its ruler reads **65.846 ms**.

```
  seating 19   ruler 48.796 / 47.461 / 49.328   (spread 1.867 ms)
  seating 18   ruler 65.846                      (+17.3 ms against this seating)
```

**17.3 ms is 9× this seating's ruler spread.** Seating 17 introduced the
`mdelay(50)` ruler as the instrument's own control and every rung since has
carried one; **no one had ever compared a ruler across seatings.** Until that is
explained, cross-seating differences in bite timing — including this seating's
`bite 3` mean sitting **92.1 ms below** seating 18's single reading — cannot be
attributed to the device.

---

## 5. 🔴 The `kickms` repair works, points the right way, and is four times too small

The carried-forward text said `kickms 5000`. § 5.1 of the card showed that to be
backwards: the bound is `kick_ms × f`, so 5000 multiplies it by twenty, and
`kickms` does not kick at all. The card used **`kickms 10`** (`kick_jiffies()`'s
one-jiffy floor at `HZ = 100`) plus an explicit `kick`, for an analytic bound of
**1,999 counts**.

```
  seating 18, same raw word 0x00020000, kick_ms 250 :  2475.923 ms
  this cell,                            kick_ms  10 :  2519.632 ms   (ruler 48.689 ms, in family)
  change                                            :   +43.709 ms
  card predicted                                    :  +136.8 .. +146.8 ms      REFUTED
```

🟢 **The uniqueness argument is nevertheless STRONGER, by a route that does not
use seating 18's bound at all.** 2519.632 ms at `f_tick = 199,903 Hz` is
**503,682 counts**. `2^18` would need a negative deficit; `2^20` would need a
deficit of 2,726 ms. **Only `2^19` is admissible**, so **`OVSEL[2] = bit 17`
holds by a second and independent measurement.**

🔴 **The residual deficit is ≈ 20,606 counts ≈ 103 ms and `kickms` cannot reach
it.** 推, with the experiment: `verb_bite` writes the stop word, then prints its
mark, then runs `mdelay(50)` — all *before* arming — and if `WDTE = 0xA5` does
not freeze the counter on this die, that window is the floor. **The experiment
that decides it**: two `biteraw` runs of the same word with different mark
lengths, or a `mdelay` the verb takes as a parameter. Both need a driver change.
⚠️ With a 34.6 ms jitter and `n = 1`, the 103 ms is a single reading and the
deficit's own uncertainty is at least the jitter.

⚠️ **The card's § 5.3 outcome table has bands narrower than the jitter measured
twenty minutes later on the same seating** — its *refuted* row reads *within
±3 ms of 2,475.923*. **The card is not edited.** The bands are re-read here
against 34.6 ms, and the experiment survives only because the predicted
*change* is about four times the jitter.

---

## 6. The off-card cells, declared

The card's fence is 13 cells and every one of them has a capture. These six are
**outside it** and are named here rather than left to be discovered:

| cell | why it is not on the card | what it produced |
|---|---|---|
| `X1-relax` | interrupted mid-run | `.log` + `.timing`, no `.meta.json` — § 3.3 |
| `X2-relax` | first retry, 12 samples | released control, `0000007C` ×12 |
| `X3-relax` | 40 s window, operator did not press inside it | **the strongest released control this project has: 40 samples over 44.6 s, one distinct value** |
| `X4-relax` | chasing § 2.1 | **36 held samples, `0000005C` every one — no blink, with `default_flag` already 1** |
| `X5-blink` | the decisive cell, written after the board was already up | 16 released / 1 + 5 solid / alternating / **7 released at `0000003C`** |
| `X6-decay` | testing my own decay hypothesis | 30 samples over 152.1 s, all `0000003C` — **hypothesis refuted** |

### 6.1 🟢 The vendor's blink is gated on `default_flag`, and one reboot is the independent variable

| `default_flag` | held | released |
|---|---|---|
| `0` (`C1-L1`, `X5`) | **blinks** | bit 6 latches at 0, LED lit |
| `1` (`X4`, 36 samples) | **static `0000005C`** | stays 1, LED dark |

Between `X4` and `X5` the only deliberate change was **four watchdog reboots**,
which clear `default_flag` (`C5-P` reads it back as `0`). So the LED indicates
*the factory-reset flag has not been armed* rather than *the button is down* —
and that is `FW-40`'s code path seen from the outside, on a driver written blind
of it.

⚠️ 推 rather than 量 on the mechanism: nothing here read the vendor's gate. What
is 量 is the association across one controlled reboot, `n = 1` in each arm.

---

## 7. 🟢 The button, bracketed — a first for this device

`C1-M0` ran **before** any press and `C1-M1` **after** the ≥ 5 s hold, on the
same boot, with no reboot between them. They agree on all **32 group digests**,
`map_diff_units 0`, `map_h601_skipped 8192`, `corrupt_at -1`.

> **A reset-button hold that crosses the factory-reset threshold, under rlxfw,
> wrote nothing to 4,186,112 of the 4,194,304 bytes.**

⚠️ Unchanged, and stated every time this is quoted: a digest agreeing with the
2026-08-16 dump cannot see two writes that cancel; `H601`'s 8,192 bytes are
skipped by rule; **no `FLR` ran**. *"Not one flash byte is written"* is exactly
as unsayable as it was.

---

## 8. What `R5-7` may now assume, and what it may not

**May**: bit 6 drives a real, visible LED, active low, position #2 of 8.
Its acceptance observable can be a photon and not a register.

**May not**:

* 🔴 **the port letter.** `rtl819x-gpio.c:120-129` already declares it open and
  labels the chip `rtl819x-pabcd` with lines numbered by bit position. `BRD-06`
  hints at `GPIOB[5]`, and a hint is one source.
* 🔴 **that `leds-gpio` can request line 6.** 量 today, `C1-G0`:
  **`known_mask 00000020`** — only bit 5. `.request` refuses every line outside
  it, so `ALLOW_OUT_MASK` is the *second* guard, not the first. **Two masks have
  to change, and the card that changes them owns the risk argument for driving a
  pin the vendor's own timer also drives.**
* 🔴 **that the vendor will leave it alone.** `rtl_gpio_timer` writes bit 6 on
  its own schedule (§ 6.1). Two drivers on one line is `R5-8`'s `EBUSY` problem
  arriving early.

---

## 8a. 🟢 The boot capture, and this is the strongest reproducibility reading this project has

All five boot captures are **1,424 bytes** — the card's control, unchanged from
seating 18's thirteen and seating 17's ten — and `RLXFW-ID0=F67EED22` in every
one.

🟢 **They are also byte-identical to each other: ONE sha256 across five boots.**
Seating 16's ten fell into **two** sha256 values (the whole difference being
`RLXFW-G3` bit 6, the LED's phase); seating 18's thirteen agreed with each other
but differed from seating 17 in `RLXFW-TA6`.

🟢 **And `C2-boot.log` here is byte-identical to `bench/2026-09-09/C2-boot.log`** —
the same image, a different seating, across a full power-down and a cold
power-on. **Eighteen boots of `r57` across two seatings produce one boot
capture.**

⚠️ Why `RLXFW-G3` does not vary here, stated rather than left as luck: `G3` is
sampled at `subsys_initcall`, *before* the vendor's `device_initcall` starts
`rtl_gpio_timer`, so it reports the state the reset left. Every bite in this
seating was taken with the button released and bit 6 at 1, and `boot_dat` reads
`0000003C` in every dump — so the population had one input, not two. **A seating
that bites while the LED is lit would be the test of that sentence, and none
has.**

---

## 9. Carried forward

1. **`C1-L2`'s unexplained `0000007C`** — § 2.1, with the experiment named.
2. **The cross-seating ruler difference, 17.3 ms** — § 4.2. Until it is
   explained, no cross-seating bite comparison is attributable to the device.
3. **`OVSEL` 3's 34.6 ms jitter has no mechanism.** The linear model is
   undetermined, not refuted and not supported.
4. **`biteraw`'s ≈ 103 ms deficit floor** — § 5, needs a driver change.
5. **`cmp` on map logs must exclude `map_jiffies`** — § 3.2, and `SPEC.md`
   `FLS-26` says so now.
6. **`cardcheck` has no category for a shell keyword** — the card's § 2.4 ②.
   `for` is grammar and the declaration is a list of files; this is why seating
   15's `X14`…`X17` loops were off-card, an oddity nobody had explained.
