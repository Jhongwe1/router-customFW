# Block 20 — the Linux half of the same power cycle, and a shape that has never been timed

**Written 2026-09-14, sixty-seventh segment, at the desk, before power.**
Seating 22, **the same one power cycle as block 19**, **three Linux boots**,
**twenty-seven captured cells**. `FW-65` 殘留 (slot 4) and `FW-63` 殘留
(slot 5) of `docs/isa-prior-art.md` § 7's schedule, which `PROGRESS.md`'s
`BLKC-1` has owned since this morning — plus three riders that cost nothing
because a Linux boot is what they needed and this block has three (§ 6b).

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4.** The image is not built tonight — it is seating 20's, already
   staged and already run seventeen times. The analogue of a rebuild is § 1's
   `sha256` plus `looprun`'s own `--image-sha256`, which is the check
   `RLXFW-ID0` cannot make: 量, `tools/looprun.py --help`, *"`RLXFW-ID0` is a
   digest over `config/` only, so it cannot tell two images built from one
   frozen `config/` apart; this can."*
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read **from a script file**
   and not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident), on a tree
   where this card is already `git add`ed.
3. `cardcheck commands` — every command invocable. 🔴 **This card is the first
   in this project's history whose `cardcheck commands` CANNOT see the command
   that matters**, and § 4 ⑤ is where that is declared rather than worked
   around.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 27`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. `bench/2026-09-14c` is the third directory of this calendar day;
   `bench/2026-09-14` is seating 21's and closed, `bench/2026-09-14b` is this
   seating's bare-metal half. § 10 carries the midnight rule.

---

## 0. What this block is, in one paragraph

Block 19 ends at the loader prompt with the board on its **first and only**
power cycle. This block takes that prompt and spends it on three Linux boots of
an image that already exists, to answer two residuals that have been waiting
since 2026-09-10. Slot 5 asks whether the vendor's steady-lit interval is a
**constant 5.000 s** — a question a *count* cannot answer and only a *time
series* can. Slot 4 asks what the vendor's own user-writable `/proc/gpio` does
on silicon, and its `echo 1` is the first non-synthetic positive control
`rtl819x-gpio`'s foreign-write detector has ever been given. **Neither needs a
build, and neither needs a power cycle of its own.**

---

## 1. The image, pinned

Not built tonight. Seating 20's, staged 2026-09-10 and unchanged since.

| | |
|---|---|
| steps | `FW-65` 殘留 (slot 4) ＋ `FW-63` 殘留 (slot 5) |
| image | `/home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin` |
| bytes | **1,052,672** |
| sha256 | `c890e0efeb6881ec…` (16 hex, `cardnum` `r59-sha16`) |
| `RECIPE_ID` / `RLXFW-ID0` | `692a2801` / **`692A2801`** |
| load address | `0x80500000` |
| boot capture | **1,637** bytes, seventeen times over on seating 20 |
| driver | `rtl819x-gpio` 1.1, `leds-gpio`, `rtl819x-keys`, `rtl819x-spi` 1.1, `rtl819x-wdt`, `rtl819x-timer` 4.1 |

🔴 **`looprun` can drive this one and could not drive block 19's.** A kernel is
not a self-resetting payload, so `S7`'s capture needs no `--esc-after`; and
`--skip S2,S3` with an explicit `--image` satisfies the `--image` guard
`LOOP-4b` records rather than tripping it, because the file already exists.
That is the *opposite* of `SEAM-1`'s answer for a bare-metal payload, and the
two are on one seating so the contrast is on one card.

---

## 2. Four things this block needs that the desk settled today, with zero power

Each was a stated blocker in `notes/slots45-draft.md` § 1 or in `BLKC-1`. Each
is now 量 on an artefact, not 推.

| # | the blocker, as written | what was measured, and where |
|---|---|---|
| ① | *"`/proc/uptime` has never been read on this device"* — unconditional in the source, but **讀** | 量 on the artefact that will boot: `r59-20260910/System.map` holds `uptime_proc_show`, `uptime_proc_open`, `uptime_proc_fops`, `proc_uptime_init` **and `__initcall_proc_uptime_init6`** — it is in the initcall table, so it is registered at boot. Positive control `meminfo` present; negative control empty. ⚠️ **This does not prove `proc_create` succeeded at run time**, only that nothing else can stop it; `C2-U` is the cell that reads it |
| ② | *"no `--send` in this project's history has ever contained a shell loop"*, 量 as **0 of all committed `sent` fields** | 🔴 **REFUTED. There are TEN**, on silicon, in `bench/2026-09-06c` and `bench/2026-09-09b`: `X14-fast`, `X15-slow`, `X16-heldfast`, `X17-heldslow`, `X23-after`, `X2-relax`, `X3-relax`, `X4-relax`, `X5-blink`, `X6-decay`. All are `for i in <literal list>; do busybox grep …; done`, four of them nested two deep. 量 2026-09-14, 1,097 captures carrying a `sent` field. **The draft's sweep was wrong and this card does not inherit it, and the ten are the form this card ADOPTS** after `B9` refused the other one (§ 5.1) |
| ③ | whether this unit's busybox **ash** has the loop constructs at all — 推 | 量 under `qemu-mips-static` against this unit's own `squashfs-root`, wrapped per `CLAUDE.md`: `while`+`[`+arith **rc 0**, `until` rc 0, `for-in` rc 0, `cat` two files rc 0, `busybox grep -e ^dat` rc 0, `sleep` fractional rc 0 (0.121 s against a 0.045 s floor). Version **BusyBox v1.13.4 (2018-01-10)**. 🔴 **My own negative control did NOT fire**: `[[ 1 -eq 1 ]]` printed rather than failing, so this ash HAS `[[ ]]`; the harness is still shown able to fail by two other controls (`rc 127` for an absent applet, `rc 1` for an absent file) |
| ④ | `R4-0`: *"if `/proc/gpio` does not exist, slot 4 is **void**"* | 量 on the same `System.map`: **`800e9194 t write_proc`** — the exact address `FW-65` names — beside `default_read_proc`, `default_write_proc`, `rf_switch_read_proc`; `autoconfig_gpio_init`/`_off`/`_on`/`_blink`/`_slow_blink` all five present; `rtl_gpio_timer` present; `default_flag` at `802ae838`. The entry name `gpio` and the vendor's own `Invalid gpio parameter! Failed!` are strings in `vmlinux`. **`R4-0` cannot fire tonight** |

🔴 **And ② changes what slot 5 is for.** `X16-heldfast` and `X17-heldslow` were
taken 3 s apart **during one hold** and nobody has ever read them:

```
bench/2026-09-06c/X16-heldfast   dat 0000001C ×15   pressed, LIT, span 0.166 s
bench/2026-09-06c/X17-heldslow   5C 1C 5C 1C 5C 1C 5C 1C 5C 1C 5C 1C   pressed, alternating, starting DARK
bench/2026-09-06c/X14-fast       dat 0000007C ×15   the not-held control, flat
```

⚠️ **Cited with the directory, because a bare `X17` is ambiguous**: `bench/2026-09-10/CORRECTIONS-block17.md` has its own `X14`…`X17`.

`X17` hits `FW-63`'s predictions #3 (1.000 s alternation) and #4 (**the first
level is HIGH**) word for word, and both were taken **inside one continuous
hold on boot 3, with the vendor timer alive** (量, cell-order reconstruction).
🔴 **But sampling a square wave at its own period is ALIASING, and the
exclusion is much weaker than it looks.** Solving the phase-admissibility
condition over the **measured** arrival times rather than the nominal
`sleep 1`: `X17` admits **294** half-period bands, every one at
`Ts / odd` with `Ts = 1.032680 s`; `X16` excludes only half-periods in
**(6.2 ms, 166 ms)**. Intersected, the two leave **exactly three**:
**1.04 ± 0.10 s, 0.345 s, 0.207 s** — so **neither 1/3 s nor 1/5 s is
excluded**, and `SPEC.md:329`'s *half-period 1 second* is carried by `FW-40`'s
`mod_timer(jiffies + 100)` (讀), not by `X17`.

🔴 **And the steady-lit interval already has a bracket that this block has to
beat.** `bench/2026-09-09b/X5-blink` caught a press mid-capture: a lit run with
a dark sample on each side gives `t(22)−t(18) = 3.926748` and
`t(23)−t(17) = 5.893622`, i.e. **3.927 s < L < 5.894 s**. 5.000 is inside — and
so are 4.0, 4.5 and 5.5. **That is the prior, and it is a 1.97 s window.**
This block's sampler is **6.4× faster**, so its bracket is **± 0.164 s**.

---

## 3. The order, and it is forced by `FW-62` rather than chosen

`FW-62`, 量 seating 20, nine button episodes over four boots with zero
exceptions: the vendor's `rtl_gpio_timer` **acts once per boot**, started by
the first press held past about two seconds, and never again on that boot.

| boot | what it is for | why it is in this position |
|---|---|---|
| **2** | slot 5, clean hold ① | **No `/proc/gpio` write happens before it.** `echo 1` lights the LED (bit 6 → 0), and `FW-63`'s prediction ① is *the first `1→0` transition at `t0+φ+1`* — a prediction that cannot be observed if the LED is already lit. Contaminating this boot would void the sharpest cell on the card |
| **3** | slot 5, clean hold ② | *Constant* is a claim about repetition. Two is the minimum that can disagree; three is what `FW-63` 殘留 actually asks for, and boot 4's hold is the third |
| **4** | slot 4, and hold ③ | The `echo` bracket goes **last** because `autoconfig_gpio_blink` may itself start the timer. If it does, boot 4's hold will not blink — and boots 2 and 3 are then the control that says so. **A risk that would have been a hazard on boot 2 is a discriminator on boot 4** |

Between boots: `busybox reboot -f`, **2.407 s** (`FW-37`), which is a watchdog
bite and not a power cycle. `reboot` is an applet and **not** one of this
image's eleven declared symlinks (`config/rlxfw-initramfs.tsv`: `sh ash cat
echo ls mount ps ifconfig ping mkdir sleep`), which is why it is typed
`busybox reboot -f` — and why `grep` is typed `busybox grep`.

---

## 4. The guards

**① Nothing on this card can reset the board except the `RB` cells.** Seating
17 spent two of its three power cycles on cells whose payload could reset the
board with no `--esc-after`; every `RB` cell here carries
`--esc-after 20 --esc-period 0.002 --until '<RealTek>'`.

**② No `--idle N` sits under a `sleep >= N`.** `cardcheck`'s `A22` refuses it,
and seating 20's card would have produced ~54 bytes from five cells with a
clean `stop_reason` while `check-predictions` scored `55 of 55`. The one cell
here carrying a `sleep` (`C4-H`, `sleep 20 < /dev/input/event0`) has
**`--seconds` and no `--idle`**.

**③ A loop that outruns its capture contaminates the NEXT cell.** This is new
and it is the one failure mode the existing rules do not cover. Every loop cell
carries `--idle` well above its own inter-sample gap and `--seconds` at ≥ 4×
the predicted duration. 🔴 **Recovery, written before it is needed**: if any
loop cell's `stop_reason` is `--seconds … elapsed` rather than `--idle`, the
loop was still running — take an off-card drain capture with **no send flag at
all** and a 30-second terminator, named `X*`, before continuing, and record it.

**④ No payload contains a `'`, a `"`, a backtick OR a `$`.** The first draft
contained six `$`, `cardcheck`'s `B9` refused the whole corpus over them, and
§ 5.1 records the redesign rather than an exemption. The longest payload here
is **119** characters against `_check_send`'s 128-byte cliff — 量 on every
candidate before one was chosen, not counted by eye.

**⑤ 🔴 `cardcheck commands` cannot see the command this card exists to run, and
that is declared rather than worked around.** `argv0s()` has no notion of shell
keywords, so after each `;` it takes the next word as an `argv[0]`: `for`, `do`
and `done` are reported *NOT IN IMAGE*. They are ash keywords, not applet
names, and they are declared in this card's
```` ```cardabsent ```` fence. **Worse, and this is the part that matters:
because `expect_cmd` is false after `do`, the `busybox grep` INSIDE the loop
body is never classified at all** — the one command each loop cell actually
runs is the one command `cardcheck` cannot see. `tools/cardcheck.py:27` already
says *"THE TOKENISER IS NOT A SHELL, and the gap is stated rather than left to
be found"*; this is that sentence arriving. **Those five `busybox grep`
invocations were checked by hand against the applet list measured in § 2 ③.**

**⑥ Zero flash-write commands and zero `FLR`.** No cell types `EW`, `EB`,
`FLW`, `FLR` or a burn verb; no cell writes `/dev/mtd*`; the only `mtd` devices
this image declares are `mtd0ro`, `mtd1ro`, `mtd2ro`. The bracket stays at
**1,024 of 4,194,304 = 0.0244 %** and `FLS-26`'s ledger does not move. ⚠️ **No
`map` cell is on this card**, so unlike seating 20 there is no flash-side
observation at all — stated so that its absence is not later read as a zero.

---

## 5. Slot 5 (`FW-63` 殘留), predicted before the press

### 5.1 The instrument, and the form it is written in is not a preference

```
for a in 1 2 3 4 5 6 7 8 9 0 a b c d e;do for b in 1 2 3 4 5 6 7 8 9 0;do cat /proc/uptime /proc/rtl819x-gpio;done;done
```

**150 iterations, 119 characters, zero `$`, zero quotes, one `cat` per
sample.** Each iteration emits the board's own clock at **10 ms** resolution
(`"%lu.%02lu %lu.%02lu\n"`, 讀) followed by all 37 gpio fields — so every
sample carries `dat` (**bit 5 the button and bit 6 the LED in one word**, no
bridging) *and* `n_state_chk` / `n_state_foreign`, which is
`notes/slots45-draft.md`'s route ② for free.

🔴 **The `$`-free form was forced by a control, and the control was right.**
The first draft of this card used `while [ $n -lt 1200 ]`. `cardcheck`'s `B9`
— *"no committed card needs shell quoting or substitution"* — went **red
across the whole corpus**, and because `cardcheck` runs its controls before it
reports, it then refused to check the **frozen block 19 card** as well. Its
comment says exactly why it exists: *"`argv0s()` is not a shell… That is the
right simplification only while no card needs them, and this is what says so.
**The day a card does, this case goes red BEFORE the card is taken to the
bench**"*. ⚠️ The seven committed `sent` fields carrying `$` are all `X*`
**off-card** cells, which `B9` never sweeps — so no card had ever tried it.
**The redesign is the answer, not an exemption**, and the `for i in <literal
list>` form it uses is the one that has already run on this die ten times.

🔴 **`j_now` is NOT a field of `/proc/rtl819x-gpio`.** 量: it is
`rtl819x-keys.c:467`. The gpio read handler ends at `val04` and contains **no
`jiffies` anywhere** — which is exactly `notes/slots45-draft.md`'s *"nothing in
this image timestamps a bit-6 transition"*. `/proc/uptime` in the same `cat` is
the answer to that, and this is the first time it is read on this device.

### 5.2 The rate is PREDICTED, because the loop is wire-bound

A sample is one `/proc/rtl819x-gpio` (**574 bytes on the wire**, 量) plus one
`/proc/uptime` (~15), so the wire term is **589 × 10 / 38400 = 0.1534 s**. The
board term is **量 and not assumed**: the two no-`sleep` captures give
**11.65 and 11.87 ms per iteration** for a 14-byte output, of which
`14 × 10 / 38400 = 3.65 ms` is wire — leaving **8.0–8.2 ms** of fork plus
`read_proc`. This loop forks once instead of once and formats more, so the
board term is taken as **8–12 ms**:

| cell | shape | iterations | predicted duration | band | rate |
|---|---|---:|---:|---:|---:|
| `C2-R`, `C3-R` | 5 × 5 | **25** | **4.09 s** | 4.04–4.14 | 6.12 Hz |
| `C2-H`, `C3-H` | 15 × 10 | **150** | **24.5 s** | 24.2–24.8 | 6.12 Hz |
| `C4-S1`, `C4-S2` | 10 × 10 | **100** | **16.3 s** | 16.1–16.5 | 6.12 Hz |

🔴 **Read the duration from the `.timing` file, NEVER from
`duration_s − idle`.** 量: the idle check runs in the outer loop behind a
`select` capped at 50 ms (`tools/console-capture.py:556`), so
`duration − idle` over-reads the last byte's arrival by **66.9 and 81.8 ms**
on the two captures that can be checked. On a 166 ms experiment that is a 50 %
error, and it is how the first draft of § 2 above came to say *0.29 s* where
the span is **0.166 s**. `FW-35`'s rule applies to the read: a byte's arrival
is the **last** `.timing` row with `offset <= b`.

**`C2-R` is a prediction check, not a decision point.** Within the band, the
model holds and nothing downstream changes; outside it, `R5-g` fires.

**6.12 Hz against a 1.000 s alternation is 6.12 samples per level**, and the
ratio is not an integer or a half-integer, so this sampler cannot alias the way
`X17-heldslow` does. 🟢 **It is also its own no-`sleep` burst**, which closes
the hole every 1 Hz capture in the corpus has: 量, each of them admits a band
at `Th ≈ Ts/2 ≈ 0.49 s`, so **a ~1 s blink reads as a flat line at 1 Hz**.
Nothing on this card samples at 1 Hz.

### 5.3 The predictions, and `t0` is defined by the data

`t0` = the first sample whose `dat` has **bit 5 = 0**. All times are read off
the `/proc/uptime` line immediately preceding that sample.

| # | prediction | source |
|---|---|---|
| 1 | the first bit-6 `1→0` at **`t0 + φ + 1`**, `φ ∈ (0,1]` → **1.0–2.0 s** after `t0` | `FW-63`, the code shape |
| 2 | bit 6 then **0 for 5.000 s** | the question itself |
| 3 | then alternation at **1.000 s** per level | `FW-63` #3, and `X17` agrees at 1 Hz |
| 4 | the first level of that alternation is **HIGH (dark)** | `FW-63` #4, and `X17` agrees |
| 5 | after release bit 6 is latched **0** and stays ≥ 152.1 s | `REG-37` |
| 6 | `/proc/load_default` reads **`1`** after a hold ≥ 5 s | `FW-40` |
| 7 | three holds give three values of the steady interval agreeing to within one sample period | this is the residual's actual question |

**Refutation, written first**

| id | if this happens | what it refutes |
|---|---|---|
| `R5-b` | the steady interval is **not 5.000 s** ± one sample period | the *constant 5.000 s* reading, and `FW-63`'s struck-through `T = 3.95 / 3.05 / 3.90` comes back |
| `R5-c` | the alternation is not 1.000 s, or it starts **LOW** | the counter-parity reading and `FW-40`'s 1 s `mod_timer`. ⚠️ This would also contradict `X17`, which is the stronger outcome |
| `R5-d` | bit 6 never goes low in a ≥ 15 s hold | **VOID, not a refutation** — the timer was already consumed on that boot. Abandon that boot and `reboot -f`; precedent is seating 20's boot 16 → 17 |
| `R5-e` | the three holds disagree by more than one sample period | **the answer is "not a constant"**, and that is a result, not a failure |
| `R5-f` | `/proc/uptime` does not advance between consecutive samples | the 10 ms resolution is not real; fall back to the host `.timing` under `FW-35`'s rule and say so |
| `R5-g` | the loop's samples are spaced more than 500 ms apart | the instrument cannot resolve a 1.000 s alternation at all and slot 5 is **not measurable tonight** — a legal recorded outcome |

---

## 6. Slot 4 (`FW-65` 殘留), predicted before the write

`FW-65` 讀 the vendor's one-byte dispatch: `E`(69) → `autoconfig_gpio_init`,
`0`(48) → `_off`, `1`(49) → `_on`, `2`(50) → `_blink`, `3`(51) →
`_slow_blink`. Bit 6 = 1 is dark, bit 6 = 0 is lit (`BRD-13`).

| cell | what is written | expected | source |
|---|---|---|---|
| `C4-P0` | nothing | `dat 0000007C`, `n_writes 2`, `n_state_foreign 0`, `foreign_seen 0`, `allow_out_mask 00000040`, and `n_get`/`n_state_chk` **3 / 3** | 量 `bench/2026-09-10/C2-P.log` for the 3/3 — **not** `C11-P0`'s 1/1, because that cell had no keys read in front of it and `FW-64` makes one `cat` two `read_proc` invocations |
| `C4-E1` | `echo 1 > /proc/gpio` | `dat` **`0000003C`** (`DAT &= ~0x40`), `foreign_seen` **1**, `foreign_first` **`0000003C`**, `n_state_foreign` **+2**, `n_writes` **still 2** | `FW-65`, `rtl819x-gpio.c:399-413` |
| `C4-E0` | `echo 0 > /proc/gpio` | `dat` back to **`0000007C`**, and `n_state_foreign` **stops advancing** | the detector compares live `DAT` against `state_last` on bit 6 only and **no read updates the reference**, so restoring bit 6 makes the samples agree again |
| `C4-E2A` | `echo 2 > /proc/gpio` | `dat` unchanged at **`0000007C`**; `AutoCfg_LED_Blink` set | `FW-65` ②. ⚠️ **If `dat` moves here, `autoconfig_gpio_blink` writes `DAT` directly and the two-armed test below is void** |
| `C4-S1` | a 100-sample loop, no press | bit 6 **flat at 1** | the blink block runs only while the timer is alive, and `FW-62` says it is not |
| `C4-H` | a hold ≥ 5 s | `/proc/load_default` → **`1`**, and the LED blinks during the hold | `FW-40` |
| `C4-E2B` | `echo 2 > /proc/gpio` again | `dat` unchanged | the timer is consumed |
| `C4-S2` | a 100-sample loop, after release | bit 6 **flat**, latched at whatever the hold left | `REG-37`, `FW-62` |

🔴 **The load-bearing one is `C4-E1`, and it is load-bearing for a reason that
has nothing to do with the vendor.** `rtl819x-gpio`'s `n_state_foreign` was
built to detect a write by something other than this driver, and it has never
been pointed at one — every zero it has printed is a zero with no positive
control behind it. **One `echo` gives it the first.**

**Refutation, written first**

| id | if this happens | what it refutes |
|---|---|---|
| `R4-0` | `/proc/gpio` does not exist | 🟢 **cannot fire** — § 2 ④ closed it at the desk |
| `R4-3` | `n_state_foreign` does **not** move on `C4-E1` | **the detector cannot see the thing it was built for.** This is the one that matters; every previous zero becomes unattributable |
| `R4-4` | `n_writes` moves | *this driver* wrote, which it must not — the vendor path does not go through it |
| `R4-5` | `C4-S1` shows bit 6 moving with no press | `FW-62`'s once-per-boot timer, from a direction seating 20 could not reach |
| `R4-6` | `C4-H` gives `load_default 0` or `b0_n_release 0` | the hold was too short or the operator was still holding when the window closed — **re-run the boot**, precedent `C13-H10` |

---

## 6b. Three riders, because a Linux boot is the whole thing they were waiting for

量 2026-09-14, at the desk, from the vendor's own GPL source in `src-vendor/`:
`0x81000400` is the Linux kernel's **`mem_map[]`** — one 32-byte `struct page`
per 4 KiB frame — written by `memmap_init_zone()`
(`mm/page_alloc.c:2626-2676`) in four steps whose order is visible in the
bytes: `flags 00000400` is `PG_reserved` (bit 10), `_count 1`,
`_mapcount FFFFFFFF` = −1, and a `lru` `list_head` at `+0x18` holding its own
address, which is what `INIT_LIST_HEAD` leaves. `0x81800000` is a SLAB
**on-slab `struct slab`** whose `s_mem = base + colouroff` is `mm/slab.c:2632`.
Neither is a loader structure, and 🔴 **`SPEC.md:669`'s surviving *loader
network buffer pool* inference — and the `§G` hazard it carries — was already
refuted on the device on 2026-08-25**: `bench/2026-08-25/H3a-early` and
`H3a-rb` read bias garbage there on a power cycle that had brought up
`IPCONFIG` and completed a 19,792-byte TFTP transfer.

Two things stayed open, and each needs exactly one command **on a Linux boot**.

| cell | what it decides | expected | refutation |
|---|---|---|---|
| `C2-MM0` | `DW 8103FFE0 16` at the **loader** prompt, before any kernel has run this power cycle | **bias garbage** — no `struct page` shape, no word equal to its own address | 🔴 **If it is already page-shaped, that is `MEM-17` DRAM retention from a previous session and the two-sided test is VOID for this seating.** Record it; do not improvise a substitute. The precedent is seating 6's cycle 4 |
| `C4-MM1` | the same read at the loader prompt after the last `reboot -f`. 16 words spans `0x8103FFE0`–`0x8104001C`: **the last `struct page` and the first four words past the array** | 32 MiB ÷ 4 KiB = 8,192 frames × 32 B = `0x40000`, so `mem_map` is `0x81000000`–`0x8103FFFF` and **`0x8103FFE0` is entry 8191**. The field this block predicts is `_mapcount` at `+0x08` = **`FFFFFFFF`**, which `reset_page_mapcount()` writes once and only a userspace mapping changes; `flags` and `_count` are **not** predicted, because `free_all_bootmem()` clears `PG_reserved` on every page it hands to the buddy allocator and the top page is free. Past the array, at `0x81040000`, the 32-byte period must **stop** | if `0x8103FFE0` is not page-shaped while `0x81000400` is, `mem_map`'s base is not `0x81000000` and the derivation from `MAX_DMA_ADDRESS` (`arch/rlx/include/asm/dma.h:87` → phys `0x01000000`) is wrong. ⚠️ Every base ≡ 0 (mod 32) that keeps the known pfns inside the kernel image fits the six readings taken so far; **this cell is what makes the base a measurement rather than a derivation** |
| `C2-SI` | `cat /proc/slabinfo` on boot 2 | one cache with **`objperslab` 15** and `objsize` in **[251, 267]** — forced, not fitted, from `inuse=15`, `free=BUFCTL_END`, `bufctl[0]` at `+0x1C` and `ALIGN(88, align)` with `align ≤ 8` | no such line → the `struct slab` reading is wrong, or this image's cache population differs from the one the bytes came from (they were read under the **vendor** firmware, and this is rlxfw) |

🟢 `/proc/slabinfo` exists in this image: 量 on `r59-20260910/System.map` —
`slabinfo_open`, `slabinfo_write`, `slabinfo_op`, `slab_proc_init`, two
`s_show`; the string `slabinfo` is in `vmlinux`, positive control `meminfo`
present, negative control empty.

⚠️ **The third row's own weakness, stated**: the `struct slab` bytes were read
from the **vendor** firmware's memory in 2026-08-24, and `C2-SI` reads
**rlxfw's** slab population. A cache present in one and absent in the other is
an expected difference, not a refutation — which is why the refutation column
says *"or"*.

---

## 7. What this block does NOT claim

* **Nothing about the loader.** Three watchdog resets and one power cycle; the
  loader region is not read, written or digested.
* **Nothing about flash.** § 4 ⑥.
* **Nothing about `CPU-45`, `R1f` or `R2c`** — those are block 19's, on the
  same power cycle, finished before this block starts.
* **Nothing about the vendor firmware.** It does not run tonight.
* 🔴 **Nothing about WHY the vendor timer behaves as it does.** `FW-62` is 量
  and its mechanism is unread; this block measures the same behaviour with a
  clock attached and does not open the disassembly.
* ⚠️ **The three holds are by one operator on one evening.** If they agree,
  that is three measurements of one hand, not three of the mechanism.

---

## 8. The order the cells may be dropped in, if the window closes

Nothing above this line may be dropped: **`C2-R`** (without the rate, every
later `N` is a guess), **`C2-H`** (slot 5 has no other cell), **`C4-E1`** (the
detector's only positive control), **`C4-P0`** (its baseline).

Then, in order: ① `C3-*` — the second clean hold, which costs the *constant*
claim its repetition but not its existence; ② `C4-S2`; ③ `C4-E2B`; ④ `C3-R`,
whose only job is to say the rate did not move between boots.

---

## 9. The drop order, because the directory name is a deadline

`bench/2026-09-14c` is a **prediction that this seating does not cross
midnight**. `tools/capdate.py` is what checks it afterwards, and
`bench/2026-08-30` / `-30b` — 37 captures taken entirely on 08-29, in
directories git shows were created before those captures existed — are why the
rule exists. The window opens ~19:00 and the seating is ~25 minutes of console
time, so the prediction has about five hours of margin. 🔴 **If the first
capture's `started_wallclock` lands on 2026-09-15, the directory is wrong and
`capdate` will say so; do not rename it** — declare it, the way
`bench/2026-08-30` is declared.

---

## 10. The cells

🔴 **Every capture carries a terminator.** `console-capture.py` refuses without
one and has since 2026-08-30.

🔴 **`--until 'val04'` is safe on a gpio cell and is NOT safe on a keys cell.**
`val04` is the last `sprintf` before `*eof` in the gpio handler (量 today,
`rtl819x-gpio.c:767`), and seating 19 measured 16 bytes arriving after the
match. The keys handler prints its 32-slot ring **last**, so a match there
drains only 50 ms of an ~800-byte tail — which is why every cell that reads
keys reads gpio **after** it.

🔴 **No cell's iteration count is a decision.** § 5.2 predicts every loop's
duration from the wire, and `C2-R` is the check on that prediction rather than
an input to a later cell. **Nothing on this card has to be edited at the
bench**, which is what the first draft's rate table would have required.

🔴 **`looprun` writes five artefacts per cell** (`<cell>-rz`, `-2a`, `-ab2`,
`-boot`, `-rescue.json`) and they are **not in § 11's fence**, the same way
block 19's rescue and upload are not in its. Stated here rather than left to be
noticed, because seating 15's card had a capture outside its fence and
`32 of 32` then did not mean *the whole seating was checked*.

```
#-- 🔴 THE NEGATIVE CONTROL FOR SECTION 6b, AND IT MUST BE TYPED BEFORE THE FIRST BOOT.
#-- The board is at the loader prompt, left there by block 19's C1-P6rb, and no kernel has run
#-- on this power cycle.  Page-shaped here means MEM-17 retention and 6b is void -- say so.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-MM0 --send 'DW 8103FFE0 16' --idle 3 --seconds 20
#-- BOOT 2.
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-14c --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
#-- the at-rest baseline.  keys first, gpio second, so val04 is the last thing on the wire.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-P0 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- the cache with objperslab 15.  One command, and MEM-12's last residual closes or does not.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-SI --send 'cat /proc/slabinfo' --idle 4 --seconds 45
#-- 🔴 THE FIRST READ OF /proc/uptime ON THIS DEVICE.  Two numbers, 10 ms resolution.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-U --send 'cat /proc/uptime' --idle 3 --seconds 12
#-- 🔴 THE DECISION POINT.  Read its duration, then pick N from section 5.2.  DO NOT TOUCH THE BUTTON.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-R --send 'for a in 1 2 3 4 5;do for b in 1 2 3 4 5;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 5 --seconds 90
#-- 🔴 SLOT 5, CLEAN HOLD ONE.  OPERATOR: start the command, wait about two seconds, then PRESS AND HOLD
#-- THE RESET BUTTON FOR FIFTEEN SECONDS BY YOUR OWN CLOCK, then release.  Launch time does not matter.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-H --send 'for a in 1 2 3 4 5 6 7 8 9 0 a b c d e;do for b in 1 2 3 4 5 6 7 8 9 0;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 8 --seconds 180
#-- after the hold: the ring carries the press and release in jiffies, gpio carries the latch.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-P1 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- FW-40's second, independent observable.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-LD --send 'cat /proc/load_default' --idle 3 --seconds 15
#-- back to the loader in 2.407 s.  This is a watchdog bite, not a power cycle.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C2-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- BOOT 3.  A fresh vendor timer, and the second of the three holds the word CONSTANT needs.
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-14c --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-P0 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- the rate again, as the control that says it did not move between boots.  DO NOT TOUCH THE BUTTON.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-R --send 'for a in 1 2 3 4 5;do for b in 1 2 3 4 5;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 5 --seconds 90
#-- 🔴 SLOT 5, CLEAN HOLD TWO.  Same instruction as C2-H: wait two seconds, hold fifteen, release.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-H --send 'for a in 1 2 3 4 5 6 7 8 9 0 a b c d e;do for b in 1 2 3 4 5 6 7 8 9 0;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 8 --seconds 180
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-P1 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-LD --send 'cat /proc/load_default' --idle 3 --seconds 15
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C3-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- BOOT 4.  Slot 4, and the third hold.  This is the boot that may be contaminated, deliberately.
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-14c --skip S2,S3 --recipe-override 692a2801 --image /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin --image-sha256 c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-P0 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- 🔴 THE FOREIGN DETECTOR'S FIRST NON-SYNTHETIC POSITIVE CONTROL.  Expect dat 0000003C.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-E1 --send 'echo 1 > /proc/gpio ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- the other side of the same test: restore bit 6 and the detector must stop counting.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-E0 --send 'echo 0 > /proc/gpio ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- arm A: the blink flag set BEFORE any press on this boot.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-E2A --send 'echo 2 > /proc/gpio ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- does anything blink with the flag set and the timer not yet started?  DO NOT TOUCH THE BUTTON.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-S1 --send 'for a in 1 2 3 4 5 6 7 8 9 0;do for b in 1 2 3 4 5 6 7 8 9 0;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 5 --seconds 90
#-- 🔴 HOLD THREE, and slot 4's hold.  OPERATOR: press and hold for EIGHT seconds, then release.
#-- The redirect opens evdev, which is what starts the polling; the window is 20 s and launch time does not matter.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-H --send 'sleep 20 < /dev/input/event0 ; cat /proc/load_default ; cat /proc/rtl819x-gpio' --seconds 45
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-P1 --send 'cat /proc/rtl819x-keys ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-LD --send 'cat /proc/load_default' --idle 3 --seconds 15
#-- arm B: the same write, after the timer is consumed.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-E2B --send 'echo 2 > /proc/gpio ; cat /proc/rtl819x-gpio' --until 'val04' --seconds 30
#-- and arm B's observable.  DO NOT TOUCH THE BUTTON.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-S2 --send 'for a in 1 2 3 4 5 6 7 8 9 0;do for b in 1 2 3 4 5 6 7 8 9 0;do cat /proc/uptime /proc/rtl819x-gpio;done;done' --idle 5 --seconds 90
#-- and back to the loader, so the seating ends where block 19 found it.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
#-- 🔴 THE POSITIVE HALF OF SECTION 6b.  Same read, same address, after three kernels have run.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14c/C4-MM1 --send 'DW 8103FFE0 16' --idle 3 --seconds 20
```

```cardabsent
# ash keywords, not applet names.  See section 4 ⑤.
for
do
done
```

### 10.1 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a frozen artefact or this card itself** — lifecycle rule 2.
The image was frozen on 2026-09-10 and has run seventeen times since; the four
`System.map` rows are read from the map that shipped beside it.

```cardnum
r59-bytes	1052672	size /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin
r59-sha16	c890e0efeb6881ec	sha256-16 /home/key/fwre-work/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin
sm-writeproc	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^800e9194 t write_proc$
sm-autocfg	5	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} T autoconfig_gpio_
sm-gpiotimer	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} t rtl_gpio_timer$
sm-defaultflag	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} d default_flag$
sm-uptimeshow	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map ^[0-9a-f]{8} t uptime_proc_show$
sm-uptimeinit	1	count /home/key/fwre-work/rebuild/bench-only/r59-20260910/System.map __initcall_proc_uptime_init6$
ref-dat	1	count bench/2026-09-10/C11-P0.log ^dat 0000007C
ref-nwrites	1	count bench/2026-09-10/C11-P0.log ^n_writes 2
ref-chk1	1	count bench/2026-09-10/C11-P0.log ^n_state_chk 1
ref-foreign0	1	count bench/2026-09-10/C11-P0.log ^n_state_foreign 0
ref-allow	1	count bench/2026-09-10/C11-P0.log ^allow_out_mask 00000040
ref-chk3	1	count bench/2026-09-10/C2-P.log ^n_state_chk 3
ref-get3	1	count bench/2026-09-10/C2-P.log ^n_get 3
boot-bytes	1637	size bench/2026-09-10/C2-boot.log
x17-dark	6	count bench/2026-09-06c/X17-heldslow.log ^dat 0000005C
x17-lit	6	count bench/2026-09-06c/X17-heldslow.log ^dat 0000001C
x16-lit	15	count bench/2026-09-06c/X16-heldfast.log ^dat 0000001C
x14-rest	15	count bench/2026-09-06c/X14-fast.log ^dat 0000007C
expansion-captures	27	count bench/2026-09-14c/PREDICTIONS-B21-block20.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-14c/C[234]-
expansion-dw	2	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'DW 8103FFE0 16'
expansion-slabinfo	1	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'cat /proc/slabinfo'
expansion-loops	6	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'for a in 1 2 3 4 5
expansion-holds	2	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'for a in 1 2 3 4 5 6 7 8 9 0 a b c d e;
expansion-rb	3	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'busybox reboot -f'
expansion-looprun	3	count bench/2026-09-14c/PREDICTIONS-B21-block20.md ^/usr/bin/python3 tools/looprun[.]py -{2}mode bench
expansion-gpiowrite	4	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send 'echo [0-9] > /proc/gpio
cells-fence	27	count bench/2026-09-14c/PREDICTIONS-B21-block20.md ^bench/2026-09-14c/C[234]-[A-Za-z0-9]+$
send-over-127	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
idle-under-sleep	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send '[^']*sleep [0-9]+[^']*' -{2}idle
no-flr	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send '[^']*(EW |EB |FLW )
no-mtd-write	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md -{2}send '[^']*> /dev/mtd
no-autoexec	0	count bench/2026-09-14c/PREDICTIONS-B21-block20.md ^/usr/bin/python3 .*(allow-autoexec|nfjrom|boot[.]img)
```

⚠️ **`-{2}send` is written where `--send` would be**, and it is load-bearing:
`cardcheck commands` finds cells with `--send\s+'([^']*)'`, so a guard row
spelling the flag out would be read as a cell typing `[^`. The character
classes make each `count` self-immune, because a `count` expression searches
the whole file.

---

## 11. The fence

```cells
bench/2026-09-14c/C2-MM0
bench/2026-09-14c/C2-P0
bench/2026-09-14c/C2-SI
bench/2026-09-14c/C2-U
bench/2026-09-14c/C2-R
bench/2026-09-14c/C2-H
bench/2026-09-14c/C2-P1
bench/2026-09-14c/C2-LD
bench/2026-09-14c/C2-RB
bench/2026-09-14c/C3-P0
bench/2026-09-14c/C3-R
bench/2026-09-14c/C3-H
bench/2026-09-14c/C3-P1
bench/2026-09-14c/C3-LD
bench/2026-09-14c/C3-RB
bench/2026-09-14c/C4-P0
bench/2026-09-14c/C4-E1
bench/2026-09-14c/C4-E0
bench/2026-09-14c/C4-E2A
bench/2026-09-14c/C4-S1
bench/2026-09-14c/C4-H
bench/2026-09-14c/C4-P1
bench/2026-09-14c/C4-LD
bench/2026-09-14c/C4-E2B
bench/2026-09-14c/C4-S2
bench/2026-09-14c/C4-RB
bench/2026-09-14c/C4-MM1
```

**27 cells**, in the order they are typed. The three `looprun` invocations and
the fifteen artefacts they write are the only artefacts of this block outside
the fence, and § 10 says why.
