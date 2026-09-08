# Block 14 — `R5-6`: a `/dev/watchdog` of mine, and the first bite this project has attributed

**Written 2026-09-08, forty-sixth segment, at the desk, before power.** Seating
17, one power cycle, ten boots, nine of which end in a watchdog bite.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4** — re-derive `RECIPE_ID` and compare with §1. If it moved, the
   image is stale and is **rebuilt**; the card is not edited to match.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read from a script file and
   not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident).
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — `0 of 42`, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. It is `bench/2026-09-08b`, which asserts *the first capture happens
   before 00:00 on 2026-09-09*. If the freeze slips past 23:50 the directory is
   renamed to `2026-09-09` and §5's fence re-derived **before** the freezing
   commit. `tools/capdate.py` `D1` is what checks this afterwards, and `D2` will
   report the midnight split this seating is expected to make.

---

## 0. What this block is, in one paragraph

`rtl819x-wdt` 1.0 is a real 2.6.30 `/dev/watchdog` — miscdevice at
`WATCHDOG_MINOR` 130, `WDIOC_*`, magic close, `nowayout` — driving `WDTCNR` at
`0xB800311C`, with three states (`STOPPED` / `BOOTGUARD` / `USER`) and two
timeout layers. `CONFIG_RTL_WTDOG=n` removed the vendor's 17.5 ms arm and its
100 Hz unconditional kick from the tick ISR, **which is this step's precondition
and not its tidy-up**: a watchdog shipped beside a kick that runs whether or not
userspace is alive is a guard that cannot fail. This block is the first time any
of it runs on the silicon.

---

## 1. The image, staged and pinned

| | |
|---|---|
| cell | `r56c` |
| `RECIPE_ID` | **`b417a3e7`** — the board must print `RLXFW-ID0=B417A3E7` |
| `vmlinux` | 4,049,497 bytes, sha256 `df5c917f9aee5b60fbecb04ed7bd83845a0ca62a314b5740448d0af34d5f283e` |
| staged image | `$FWRE_WORK/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin` |
| image bytes | **1,043,456** |
| image sha256 | **`6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545`** |
| marks | 21 declared, `MK6` the new one (`drivers/watchdog/Makefile`) |
| host-compat patches | 5 |

🔴 **The `.bin` did not exist when this segment opened, and that is a defect
this project has had before.** `r56c`'s manifest says `target vmlinux`; the
build produced an ELF and no uploadable image, and `bench-only/` stopped at
`r55-20260907`. Seating 8's card told the operator to upload an image that was
never staged. It was found here **before** power by looking for the file rather
than for the cell directory. `S3` was then run by hand with the same argv
`looprun` uses, and §4.1's `--skip S2,S3` is what makes that legitimate.

🟢 **Rule 4 has three sources and two of them ran at the desk**: the by-hand
formula over `config/` gives `b417a3e7`, the build's own `manifest` says
`recipe_id b417a3e7`, and this card is the third. All three agree, so no rebuild
was needed.

---

## 2. What is being claimed, and what would refute it

| # | claim | refuted by |
|---|---|---|
| `A` | A `/dev/watchdog` of mine is registered on this part and drives `WDTCNR` | `misc_rc` ≠ 0, or `registered 0`, in any `-P` dump |
| `B` | `CONFIG_RTL_WTDOG=n` did what §3 of the driver header says | `wdtcnr_at_probe` ≠ `A5000000` — in particular `00600000`, which is the vendor's arm still happening |
| `C` | `BOOTGUARD` feeds the hardware continuously, not once | `Δn_hw_kick / Δjiffies` ≠ 1/25 in `C1-P`→`C1-K` |
| `D` | It bites, and the bite is the reset | any `-B` cell whose capture holds no loader banner |
| `E` | The bite time follows `2^(15+ovsel)/f + d` over four rungs | a fit whose residual exceeds the instrument floor measured in the same captures (§4.3a) |
| `F` | Nothing else on this board feeds `WDTCNR` after `late_initcall` | `C5-S3` or `C6-S3` **surviving** past ~1.2 s — and that survival is the finding, not a failure |
| `G` | `OVSEL[2]` is at bit 19 or bit 20, and one of them is right | both `C8-B` and `C9-B` giving the same interval, or neither biting |
| `H` | The SPI read path does not starve the timer wheel | `C1-M1` resetting the board, or `Δn_hw_kick` over the armed map falling well below `map_jiffies/25` |

---

## 3. Predictions written before power

### 3.1 The boot capture — **1,424 bytes**, and the ORDER is the stronger half

量: all ten of seating 16's boot captures were **exactly 1,318 bytes**, and all
ten printed `RLXFW-TA0=FFFF8AE5` and `RLXFW-TA5=FFFF8D34`. Seven new marks are
added and every one of them is printed **before** `TA5`:

| mark | shape | bytes |
|---|---|---|
| `RLXFW-S8` | bare (`rtl819x-spi` 1.1) | 10 |
| `RLXFW-W0` | bare | 10 |
| `RLXFW-W1=A5000000` | `markx` | 19 |
| `RLXFW-W2=00000000` | `markx` | 19 |
| `RLXFW-W3=00000000` | `markx` | 19 |
| `RLXFW-W4=00240000` | `markx` | 19 |
| `RLXFW-W5` | bare | 10 |

**1,318 + 106 = 1,424.** Of those 106 bytes, **106 are predicted and none has
ever been measured.**

⚠️ Two marks share a prefix with a failure variant and only one of each pair can
print: `W5` with `W5-NOPROC`, and `S8` with `S8-NOMAP`. A `grep` for `RLXFW-W5`
matches both.

🟢 **A second, quantitative prediction falls out for free.** The 106 new bytes
are all transmitted before `TA5`, at 38400 8N1 = 3,840 B/s = **27.6 ms =
2.76 jiffies**. So `TA5` must read **`FFFF8D37` ± 2**, and a `TA5` unchanged at
`FFFF8D34` would mean the new marks are not on the path this arithmetic assumes.

### 3.2 🔴 The driver header's own refutation clause FIRES, and the conclusion does not follow

The wdt header says, of its `late_initcall` choice:

> *the ordering between TA8 and W0 in the boot capture is therefore an
> observable, not an assumption, and **if W0 ever precedes TA8 the bootguard is
> arming against a tick that does not yet exist and this initcall level is
> wrong**.*

量, on this image's own `System.map`, the level-7 initcall table in link order:

```
802d0b98  __initcall_rtl819x_spi_init7        <- S0..S8
802d0b9c  __initcall_rtl819x_wdt_init7        <- W0..W5
802d0ba0  __initcall_rtl819x_boot_arm_late7   <- TA5..TA9
```

**`W0` precedes `TA8`. The clause fires.** It was written expecting the
opposite, and the artefact says otherwise before the board is powered.

🟢 **The safety conclusion survives, and the premise is what is wrong.** The
clause equates *"TA8 has not happened"* with *"there is no tick"*, and those are
different things. The tick exists from `time_init()`; `TA8` is only where **my**
clockevent takes over from the vendor's. 量, in seating 16's own committed
captures, ten times: `TA5 − TA0 = 0xFFFF8D34 − 0xFFFF8AE5 = 591 jiffies` of tick
between `arch_initcall` and `late_initcall`. The timer wheel `BOOTGUARD` depends
on has been running for 5.9 seconds by the time `W0` prints.

🟢 **And the ordering buys something nobody designed.** Because `W0…W5` run
*before* `TA5…TA9`, the bootguard is armed at `OVSEL` 9 and being kicked every
250 ms **during** `R5-3b-2`'s clockevent handover. `clockevents_exchange_device()`
runs with a 1.121 s watchdog underneath it. If that handover ever wedged the
tick, this board would reset instead of hanging silently — **`R5-6` is a
watchdog on `R5-3b`, by link order, and neither driver knows it.**

🔴 **What is NOT established**: that `late_initcall` is the *best* level, only
that it is not the broken one the clause describes.

🔴 **The clause is NOT corrected in the same commit as this card, and rule 4 is
why.** The header lives in `config/rlxfw-src/`, and `RECIPE_ID` is a sha256 over
**every file under `config/`** — comments included. Editing a comment would move
it off `b417a3e7`, make §1 false, and make the board's own `RLXFW-ID0` check
fail against an image the tree can no longer produce. **The correction is
carried forward to the closeout, after the captures are on disk.** This is the
first time rule 4 has been observed to forbid a documentation fix rather than a
code one.

### 3.3 `/proc/rtl819x-wdt` at `C1-P`

Every scalar, in the driver's own print order. **The card gates on FIELDS, never
on marks** — `FW-47`: every capture line is CRLF and `rlxfw_mark()` interleaves
with busybox ash's echo.

| field | expect | why |
|---|---|---|
| `version` | `rtl819x-wdt 1.0` | |
| `state` / `state_name` | `1` / `BOOTGUARD` | `bootguard=1` armed at `late_initcall` |
| `registered` / `misc_rc` | `1` / `0` | claim `A`; a `-16` here is `SOFT_WATCHDOG` colliding on minor 130, which is why it is pinned `n` |
| **`wdtcnr_at_probe`** | **`A5000000`** | 🔴 **claim `B`, the headline.** `00600000` means the vendor still arms |
| `probe_is_reset` | `1` | |
| `probe_is_vendor_armed` | `0` | |
| `wdtind_at_probe` | `0` | `A5000000 & (1<<20) = 0`; see §6 |
| `wdtcnr_live` | **`00240000`** or `00A40000` | 🟢 a free reading: whether `WDTCLR` reads back on this die. Nothing here has ever measured that — it is masked out of the shadow comparison precisely because it is undetermined |
| `wdtcnr_shadow` | `00240000` | `compose(1, 9, 0)` = `OVSEL_B3 \| OVSEL_B0` |
| `shadow_agrees` | `1` | masked comparison, so it holds under either `wdtcnr_live` |
| `hw_ovsel` / `armed_ovsel` | `9` / `9` | module default |
| `hw_timeout_us` | `1121101` | table row 9 |
| `wdt_hz` | `14965000` | `CLK-08b` |
| `kick_ms` | `250` | 4.48× margin |
| `soft_timeout` | `60` | |
| `bootguard` / `nowayout` | `1` / `0` | |
| `unlocked` / `open` / `expect_close` | `0` / `0` / `0` | |
| `jiffies` | ~`FFFF8D40`+ as decimal | free-running |
| `deadline` | `0` | never entered `USER` |
| `n_hw_kick` | ≥ 1 and advancing | one from the arm, then 4/s |
| `n_user_ping` … `n_unclean_close` | `0` | except `n_arm` = `1` |
| `n_state_foreign` | **`0`** | §6: it *cannot* fire here, and `C1-WG` is why that zero is not decoration |

Then ten `ovselN enc %08X usec %u valid %d` rows, every one of which is a
prediction from the driver's own table:

```
ovsel0 enc 00000000 usec 2190 valid 1
ovsel1 enc 00200000 usec 4379 valid 1
ovsel2 enc 00400000 usec 8759 valid 1
ovsel3 enc 00600000 usec 17517 valid 1
ovsel4 enc 00000000 usec 35034 valid 0
ovsel5 enc 00000000 usec 70069 valid 0
ovsel6 enc 00000000 usec 140138 valid 0
ovsel7 enc 00000000 usec 280275 valid 0
ovsel8 enc 00040000 usec 560551 valid 1
ovsel9 enc 00240000 usec 1121101 valid 1
```

🟢 **`ovsel3 enc 00600000` is the row to read twice.** That is byte-for-byte the
word 量 at `bsp_timer_init+0xb8` on the artefact — the vendor's own arm. A
driver of mine, written blind, computes the vendor's constant from a split-field
decode the vendor never documented.

### 3.4 The 32 `map 0` lines — every one predicted from the dump

`tools/flashmap.py --dump $FWRE_WORK/dumps/flash-n150rt-console-2.bin predict
--level 0` (its own twelve controls pass first). The board must print these, in
this order, on **both** `C1-M0` and `C1-M1`:

```
000000 1 122880 8494cc8666b5c6f673123a43ce18e52cf3cfc242af881a29a46a3f7b8ed4484a
020000 1 131072 632bf336dc8bb1facfedec872a28ab3ace712131b2941c772059a4290e68e761
040000 1 131072 f69f0b3d64904dff91c63375110d45862c117492999114c09b6872a6233a71a3
060000 1 131072 1850b0416d3a6248d1f7fc477e409ad8cbef3d6e12b179941ce549a198709315
080000 1 131072 4efcd613df7261cfe2c85844467fa3099855132c2cf43ec5e91e3d84f8364f69
0A0000 1 131072 2809be96244841d5dc374e4626e6eaee94b3ea12aa46b26f8384fe86eea6fc3f
0C0000 1 131072 48cc303098a46284a96b2accb3d616ab2af6da3ec74dd5545a212b11b1542175
0E0000 1 131072 95671e429e8d0153b0611676a18c2dd9061f46b33f696d66e532894b4e441f54
100000 1 131072 d1cf9142ce69e29e0f92e080f0e548e9e14bd955ba178a96c659f924804dee17
120000 1 131072 a5db8c4d3b79ace0e44a8e466966bf084d5667b7af52a3ef37aa0f120da41398
140000 1 131072 4fcf3508721256ab8fdd53be03b9bf5af0ebfc629cd992089f2e194f6e1cf4e5
160000 1 131072 fa43239bcee7b97ca62f007cc68487560a39e19f74f3dde7486db3f98df8e471
180000 1 131072 73835d3068ba95e0fa405d913508a239214937f0df0a7b152a6e210f0653fac7
1A0000 1 131072 e2418060f3e24ed10190407d945353d6aa12604a660a8ce7c9a9c2d62428ec0f
1C0000 1 131072 8cae1f52490ed7cde71923ff02c08979830e267922e634749e1043c7b67fe927
1E0000 1 131072 af409d8e211e8cbf15e0d6eac2c31802dba69b9e042a0d5571d13213ed1f7595
200000 1 131072 a79966d9d73a61b907f65715f950b325ff31aa7a2d75049fc82084c80956351a
220000 1 131072 5103beb12c6c1f304a5383f53ce994d7b4ebcc8f1674d17a9557827d21bd2ac0
240000 1 131072 a4b182356df0d4a2e22ffc6716531eb3e53ee91ec46496f18e6fdd008b1736db
260000 1 131072 11974511e341ce05eb7a0c9b3ad3af174d74147f5b40e253c8f0eb97aa08614c
280000 1 131072 a450030f8c318db4ca2401d99435049ba27ce54e889e4d4991b0150831d41afe
2A0000 1 131072 413598d270bd30fd78ca1622ec4203ee007b2685bb969ba28b0ea620da36e05c
2C0000 1 131072 f1cabc84c0c95ba3af68e336fc942981bd91202e21efb0b73358ad40758fd52b
2E0000 1 131072 bf624c11eb9f75b15f2e21e9f86e1fd31f0b20338b53ad401ddb94e9f1bed536
300000 1 131072 b305d71c6d9776c0ce91f8d90fe924130fe481e6e36d0aad483ec815a41097b8
320000 1 131072 bfd415326c7063ffbda5e4294c85afd029c5699a65adea6c74604e7ee11f0769
340000 1 131072 32c35b3b9f044739977cb5ff123afc883f5be592c508f28067a0042a5ed68369
360000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
380000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3A0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3C0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3E0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
```

🟢 **The block has two internal shapes that do not depend on any digest value**,
so a reader can check it without trusting `flashmap`:

* group 0 hashes **122,880** bytes and not 131,072 — `H601`'s 8,192 are skipped,
  and that skip is the same guard `verify` uses (`map_h601_hashed` must be `0`);
* the **last five groups share one digest**, because the reference dump has a
  737,280-byte all-`0xFF` run from `0x34C000` and `0x360000`–`0x400000` lies
  wholly inside it. Five identical trailing digests and a different one at
  `340000` is what an `0xFF` run must produce. **Five different digests there
  would refute the instrument, not the flash.**

Fields to gate on: `map_ran 1`, `map_rc 0`, `map_level 0`, `map_unit 131072`,
`map_entries 32`, `map_hashed 4186112`, `map_h601_skipped 8192`,
**`map_h601_hashed 0`**, `map_diff_units 0`, `map_truncated 0`, `map_lines 32`.

🔴 **This is `rtl819x-spi` 1.1's first execution on silicon** — `FLS-26`'s
99.02 % undetermined is untouched by a level-0 map, which digests the whole
complement in 32 pieces and so can only say *which 128 KiB group* moved. Closing
99.02 % needs level-1 maps, and they are not on this card.

---

## 4. The cells

### 4.1 The invocations and the conventions

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-08b/`.

`LOOP` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir
bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image
/home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin
--image-sha256
6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545`

🔴 **`--skip S2,S3` is necessary, not a convenience** — `S3` assembles from the
tree `S2` stages and nothing carries that path when `S2` is skipped, which is
also what makes `--recipe-override` required rather than decorative.
🔴 **`--skip S4` is chosen, and the reason is different from block 13's**: there,
every reset was a `Cn-A` cell; **here every reset is a BITE**. Nine of the ten
boots are entered through a watchdog reset caused by the driver under test, so
**this card contains no warm-reset cell at all** — `expansion-reboot-f` in §4.5
requires zero occurrences of the vendor-reset command, and that row is the
arithmetic form of this paragraph.

⚠️ **This paragraph deliberately does not spell that command out.** `cardnum`
counts the literal across the whole file, so naming it here would make its own
check read `1` — block 13 hit the same shape when an *illustration* of a flag
became a command `cardcheck` then tried to look up.

🔴 `ping` ignores `-c` on this image (`NET-26`); no cell asks for a count.
🔴 **Every capture carries a terminator** — `console-capture.py` refuses one
that does not.
🔴 **No cell may contain a `'`.** Every command is typed inside a single-quoted
`--send`, and a shell cannot nest single quotes. 量: §4.4 was generated from one
list by a script that refuses a payload containing `'` or reaching 128 bytes —
**41 payloads, longest 103 bytes, zero quotes**, and the fence is compared
against the expansion in both directions by the same script.

### 4.2 The rule

| capture | typed | expect | 🔴 stop if |
|---|---|---|---|
| **`C1-A`** cold | `CAP OUT C1-A --esc 150 --esc-period 0.002 --seconds 165` | operator presses power inside the window; loader banner, then `<RealTek>` | no `<RealTek>` → the window was missed and the board is running the **vendor** firmware. Power-cycle and repeat |
| **`Cn-*`** | `LOOP --cell Cn` | the board prints `RLXFW-ID0=B417A3E7` and a **1,424-byte** boot capture | the burn-flag read-back is anything but `00000000` → **nothing is uploaded**, not skippable |
| **`Cn-P`** | `CAP OUT Cn-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20` | §3.3's field table | `registered 0` or `misc_rc` ≠ 0 → **stop the block**; `wdtcnr_at_probe 00600000` → `CONFIG_RTL_WTDOG=n` did not take, stop |
| **`Cn-B`** bite | `CAP OUT Cn-B --send 'echo bite <k> > /proc/rtl819x-wdt' --esc-after 10..12 --esc-period 0.002 --seconds 20` | `RLXFW-W-BITE=…`, ~50 ms, `RLXFW-W-GO`, silence, then the loader | no loader banner within the window → the bite did not happen; §4.6 |

### 4.3 Boot 1's ladder, smallest act first

`C1-P` → `C1-K` (the at-rest kick rate) → `C1-MS` (**disarm**) → `C1-M0`
(map, unarmed) → `C1-MA` (re-arm) → `C1-M1` (**the same map, armed**) → `C1-MK`
(the kick count across it) → three refusals → `unlock` → `wedge` →
`/dev/watchdog` magic close → **`bite 0`**.

**Constraint ① is a measurement and not an avoidance.** The map must run
disarmed first because a ~14 s kernel-mode traversal under a 1.121 s deadline is
exactly the thing that could reboot the board mid-cell. Running it **again**,
armed, converts that hazard into a reading:

| | from | predicted |
|---|---|---|
| at-rest kick rate | `C1-P`→`C1-K` | `Δn_hw_kick / Δjiffies` = **1/25** |
| kick rate under a 4 MiB traversal | `C1-MA`→`C1-MK` | **the same 1/25**, with `Δn_hw_kick ≈ map_jiffies / 25` |
| `map_jiffies` | `C1-M0` and `C1-M1` | **1,300 ± 300**, and the two must agree |

🟢 **"The board survived" is the weak version of this and the card does not
settle for it.** Surviving only bounds the worst timer-wheel stall at < 1.121 s.
The *ratio* says the wheel ran at the rate it was programmed for, throughout —
and `C1-K` is the control that says what that rate is when nothing else is
happening. A survived-but-starved traversal shows up as `Δn_hw_kick` well below
`map_jiffies/25`, and nothing else on this card would notice it.

### 4.3a 🔴 How a bite is timed — and the instrument's floor is MEASURED, not assumed

`console-capture.py` says of its own `.timing`: *"the floor is the USB-serial
latency timer (**1–16 ms typical, unmeasured on this host**)"*. The four rungs
are 2,190 / 17,517 / 560,551 / 1,121,101 µs, so **two of them are at or below a
floor nobody has ever measured**, and a card that quoted `gap(3) − gap(0)` as a
number without saying so would be quoting noise.

🟢 **The driver already prints a ruler and nobody had noticed.** `verb_bite`
does `markx("W-BITE", word)` → `mdelay(50)` with interrupts **on** →
`local_irq_disable()` → `puts("RLXFW-W-GO")` → arm → `for(;;)`. So every bite
capture contains a **known 50 ms interval**, on the same instrument, in the same
file, immediately before the interval being measured. Its deviation from 50 ms
**is** the floor, per capture.

🟢 **And the ESC stream is a metronome.** `--esc-after` streams at
`--esc-period 0.002`; 量 on seating 16's `C2-A`, the board echoes it at ≈425
bytes/s. During the 50 ms drain the tty is echoing, so `.timing` rows are dense
there; at `local_irq_disable()` the echo **stops**, and the bite interval is a
clean silence bracketed by a running metronome on the left and the loader's
first byte on the right.

**How to read a rung**, and `FW-35` is why the second sentence is here:

1. find the byte offset of the last byte of `RLXFW-W-GO\r\n` by string search —
   *not* by "the next byte after `W-BITE`", because echoed ESC lands in between;
2. a byte's arrival time is the **last** `.timing` row with `offset <= b`, never
   the first with `offset >= b`;
3. `gap = t(loader's first byte) − t(last byte of W-GO)`.

`gap(ovsel) = 2^(15+ovsel)/f + d`. Four rungs, two unknowns, **two degrees of
freedom**, and the residual is the result.

🔴 **The `9 − 8` difference is CIRCULAR and this card says so before it is
measured.** `CLK-08b`'s `f = 14.9650 MHz` was solved from exactly that
difference: `(2^24 − 2^23) / (1118.133 − 557.583) ms = 14,965,000 Hz`. So
predicting 560,550 µs back out of a table built from `f` is an identity.
`SPEC.md`'s own `CLK-08b` 殘留 already says it — *"這一格不能靠再量一次逾時解決
（那只會再量到 14.965）"* — and the driver header says the opposite (*"14.965 MHz
is confirmed from inside Linux"*). **The header is wrong.** Two files in this
repository disagreed about whether an experiment could succeed, and nothing
noticed until a card had to state the prediction. The header's correction is
carried forward to the closeout for the same rule-4 reason as §3.2's.

🟢 **What is NOT circular, and it is the ladder's real content:**

* **`gap(8) − gap(3)` = 543,034 µs.** `OVSEL` 3 has *never* been timed — at the
  loader or anywhere else — and 543 ms is two orders of magnitude above any
  plausible floor. This tests the power-of-two structure of the split field
  across a **32×** span with a single `f`.
* **`gap(3) − gap(0)` = 15,327 µs**, reported as a number only if the 50 ms
  ruler shows a floor small enough; otherwise as a bound. Stated now so it is a
  scope limit and not a disappointment.
* 🔴 **Whether the watchdog's clock is the same under Linux as at the loader
  prompt.** This is a live question with a measured precedent: `CLK-17` records
  `TC0CNT` incrementing at 14,286,057 Hz at the loader and **200,005 Hz under
  Linux — 71.43× — because Linux reprograms `CDBR`.** A clock this project
  measured at the loader has already been shown to change. If `gap(9) − gap(8)`
  under Linux is **not** 560,550 µs, the watchdog's counting clock differs
  between loader and Linux, and *that* is the finding.
* **Negative controls, in the same batch**: `OVSEL` 0 must reproduce what
  `bsp_machine_restart` has been doing for every `reboot -f` in this project's
  history, and `OVSEL` 3 must reproduce `bsp_timer_init`'s 17.5 ms.

### 4.3b 🟢 A second instrument for every bite, already on disk, costing nothing

量 2026-09-08 at the desk, over the whole `bench/` corpus: after a warm reset the
loader prints

```
Booting...
Reboot Result from Watchdog Timeout!
chipName: UNKNOWN
```

and after a **cold power-on** it prints `Booting...` straight to `chipName:` with
**no reset-cause line at all**. Both directions are on disk — eight cold captures
(`A-catch.log` ×9 back to 2026-08-24, `C1-A`, `V-A`, `Z-A`, `W-A`, `X-A`, `K-A`)
and eight warm (`C2-A`…`C9-A`).

**So the loader reports its own reset cause, it discriminates perfectly, and it
uses no timestamp.** Every `-B` cell must show that line. It is an independent
confirmation of `FW-45`'s claim that `bsp_machine_restart` *is* a bite, and for
`C8-B`/`C9-B` it separates "the board reset" from "the board reset **because of a
watchdog timeout**" — which is the discrimination those two cells need most.

⚠️ **Where the loader gets it is undetermined and this card does not guess.** A
plain-ASCII search of the 4 MiB dump for that string returns nothing — but so
does the positive control (`RealTek`, `ramSize`, `chipName`, `Ethernet init` are
all absent; only `Booting` is present, at offset 990). **The search is
uninformative, and the failed control is what says so.** The banner almost
certainly lives in stage 2, and `$FWRE_WORK/stage2.bin` is where to look. Desk
work, carried forward — see §6.

### 4.3c The trap cells, and why the valuable outcome is the negative one

`C5` and `C6` run `stop ; kickms 3000 ; ovsel 9 ; bootguard`. The kernel timer
will not come round for 3 s and the hardware deadline is 1.121 s, so **if nothing
else writes `WDTCLR` the board must reset at ~1.121 s.** If it survives, someone
else is feeding, and §3 of the driver header's enumeration is incomplete.

🔴 **The sequence is split at its own decision points**, which is seating 11's
lesson: `C5-S1` types the three verbs, `C5-S2` **reads back** `state 0`,
`kick_ms 3000`, `hw_ovsel 9`, and only then does `C5-S3` arm. A silently refused
`ovsel 9` would otherwise make the trap a different experiment with nothing
saying so.

🔴 **`C5` is the control and `C6` is the experiment**, and the card needs both.
With `wlan0` down, none of the three surviving vendor kicks
(`rtl8192cd_init_hw_PCI` ×2, `rtl8192cd_init_one`) is on any live path, so `C5`
tests the trap itself; `C6` brings `wlan0` up first and re-runs it.
量 (fifteenth update): those three are `__initcall_rtl8192cd_init6`, level 6,
against this driver's level 7 — so a kick at *boot* cannot feed a guard that does
not exist yet. **What is 未定 is re-entry from a userspace `ifconfig up`**, and
reading more source cannot settle it. Antenna attached, 量 by the operator.

### 4.4 The expansion — one line per cell, and it is what gets typed

§4.2 is the rule and §4.3 the ladder; this is both applied. 量, generated from
one list by a script rather than typed, and checked in both directions against
§5's fence: **42 cells, 41 `--send` payloads, longest 103 bytes, 0 containing a
`'`, 0 at or over 128.**

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell C1 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- boot 1 only: the ladder, smallest act first.  Every cell that changes state ends with a `cat` (4.3a).
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-K --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- constraint (1): the map runs DISARMED first.  C1-MS is what makes that a checked fact and not an intention.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-MS --send 'echo stop > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- 4 MiB PIO + 4 MiB window + 64 sha256: ~13-16 s of SILENCE, so --seconds ALONE.  --idle 3 would end the capture inside it.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --seconds 120
#-- re-arm, then the SAME traversal again -- constraint (1)'s measurement, with C1-K as its at-rest control
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-MA --send 'echo bootguard > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --seconds 120
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-MK --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- three refusals, three errnos, one driver.  Routed through `cat` so strerror prints (seating 15's trick) instead of FW-41's truncated ash echo.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-EP --send 'echo wedge | cat > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-RJ --send 'echo ovsel 5 | cat > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-RI --send 'echo ovsel 11 | cat > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-U --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- n_state_foreign's positive control -- section 5.4 says it cannot fire in the shipping image, so this is the only way it is ever seen to move
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-WG --send 'echo wedge > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- /dev/watchdog, MAGIC close: state must come back 1 BOOTGUARD, not 0 STOPPED (header section 4's deliberate deviation)
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-DV --send 'echo V > /dev/watchdog ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- RUNG 0.  This cell RESETS the board -- the bite IS the reset, so no Cn-A cell is needed for boots 2..10.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C1-B --send 'echo bite 0 > /proc/rtl819x-wdt' --esc-after 10 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C2-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- RUNG 3 -- the vendor's own value, 0x00600000, which bsp_timer_init programmed on every boot before this image
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C2-B --send 'echo bite 3 > /proc/rtl819x-wdt' --esc-after 10 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C3-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- RUNG 8
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C3-B --send 'echo bite 8 > /proc/rtl819x-wdt' --esc-after 10 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C4-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- RUNG 9
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C4-B --send 'echo bite 9 > /proc/rtl819x-wdt' --esc-after 12 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C5 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- AM I THE ONLY FEEDER -- wlan DOWN.  This is the CONTROL: with no wlan up, the board MUST reset.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C5-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C5-S1 --send 'echo stop > /proc/rtl819x-wdt ; echo kickms 3000 > /proc/rtl819x-wdt ; echo ovsel 9 > /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- the trap is CHECKED before it is armed -- state 0, kick_ms 3000, hw_ovsel 9.  Seating 11's lesson: split at the card's own decision points.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C5-S2 --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C5-S3 --send 'echo bootguard > /proc/rtl819x-wdt' --esc-after 12 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C6 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- the same trap with wlan UP -- constraint (2).  The three surviving vendor kicks are all on rtl8192cd's bring-up path.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C6-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C6-WU --send 'ifconfig wlan0 up ; ifconfig wlan0' --idle 5 --seconds 40
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C6-S1 --send 'echo stop > /proc/rtl819x-wdt ; echo kickms 3000 > /proc/rtl819x-wdt ; echo ovsel 9 > /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C6-S2 --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C6-S3 --send 'echo bootguard > /proc/rtl819x-wdt' --esc-after 12 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C7 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- /dev/watchdog USER state, the real one: an UNCLEAN close leaves the deadline running and the hardware bites 60 s later
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C7-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C7-W --send 'echo x > /dev/watchdog ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C7-D --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- NO cat here: the ESC stream is echoed by the tty and would interleave with a dump (FW-47's family).  `sleep` keeps ash off the prompt; the ~28 KB of echoed ESC is EXPECTED and is not a defect.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C7-B --send 'sleep 70' --esc-after 70 --esc-period 0.002 --seconds 85
/usr/bin/python3 tools/looprun.py --mode bench --cell C8 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- constraint (4): OVSEL[2] at bit 19 or bit 20.  Two hypotheses, 16x apart, opposite order.  These two cells are LAST because their failure mode is a hang, not a reset.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C8-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C8-U --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C8-B --send 'echo biteraw 0x00080000 > /proc/rtl819x-wdt' --esc-after 12 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C9 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C9-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C9-U --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C9-B --send 'echo biteraw 0x00100000 > /proc/rtl819x-wdt' --esc-after 12 --esc-period 0.002 --seconds 20
/usr/bin/python3 tools/looprun.py --mode bench --cell C10 --out-dir bench/2026-09-08b --skip S2,S3,S4 --recipe-override b417a3e7 --image /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin --image-sha256 6c6f7722d89a4d564afac2fa7fe0d2c936f6d8de7abeeedb8afd3f54cf776545
#-- the tenth boot carries no bite: nine of ten already did, and this one is the clean final reading
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C10-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-08b/C10-F --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

### 4.5 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The four files under `bench-only/r56-20260908/` never move again; nothing here
points at `config/rlxfw-src/`, which is a live tree and would go red on the next
edit for a reason having nothing to do with this seating.

🟢 **Four of these rows are §3.2's ordering finding turned into arithmetic**, and
three more are the `CONFIG_RTL_WTDOG=n` blast radius turned into symbol counts:
`n-is-fault 0` is `kernel/panic.c`'s and `kernel/exit.c`'s stores gone,
`n-softdog 0` is the `WATCHDOG_MINOR` collision that cannot happen, and
`kept-machine-restart` / `kept-watchdog-reboot` are the two survivors the delta
predicted, present.

```cardnum
img-bytes	1043456	size /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin
img-sha16	6c6f7722d89a4d56	sha256-16 /home/key/fwre-work/rebuild/bench-only/r56-20260908/rlxfw-r56-20260908.bin
vmlinux-bytes	4049497	size /home/key/fwre-work/rebuild/bench-only/r56-20260908/vmlinux
vmlinux-sha16	df5c917f9aee5b60	sha256-16 /home/key/fwre-work/rebuild/bench-only/r56-20260908/vmlinux
map-bytes	377310	size /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map
map-sha16	d2470f26fca1eace	sha256-16 /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map
ord-spi-late	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^802d0b98 t __initcall_rtl819x_spi_init7$
ord-wdt-late	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^802d0b9c t __initcall_rtl819x_wdt_init7$
ord-timer-late	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^802d0ba0 t __initcall_rtl819x_boot_arm_late7$
wdt-misc-register	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] misc_register$
wdt-verb-bite	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_wdt_verb_bite$
wdt-steps-table	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_wdt_steps$
wdt-ioctl	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_wdt_ioctl$
n-softdog	0	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] softdog[a-z_]*$
n-is-fault	0	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] is_fault$
kept-machine-restart	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] bsp_machine_restart$
kept-watchdog-reboot	1	count /home/key/fwre-work/rebuild/bench-only/r56-20260908/System.map ^[0-9a-f]{8} [A-Za-z] write_watchdog_reboot$
expansion-captures	42	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-08b/C[0-9]+-
expansion-loops	10	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell C[0-9]+ --out-dir
expansion-cold	1	count bench/2026-09-08b/PREDICTIONS-B15-block14.md --out bench/2026-09-08b/C[0-9]+-A --esc 150
expansion-reboot-f	0	count bench/2026-09-08b/PREDICTIONS-B15-block14.md busybox reboot -[f]
expansion-bite	4	count bench/2026-09-08b/PREDICTIONS-B15-block14.md -{2}send 'echo bite [0-9]+ > /proc/rtl819x-wdt'
expansion-biteraw	2	count bench/2026-09-08b/PREDICTIONS-B15-block14.md -{2}send 'echo biteraw 0x[0-9A-F]{8} > /proc/rtl819x-wdt'
expansion-trap	2	count bench/2026-09-08b/PREDICTIONS-B15-block14.md -{2}send 'echo bootguard > /proc/rtl819x-wdt' -{2}esc-after
expansion-silent	2	count bench/2026-09-08b/PREDICTIONS-B15-block14.md -{2}send '[^']*' --seconds [0-9]+$
cells-fence	42	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^bench/2026-09-08b/C[0-9]+-[A-Z0-9]+$
send-over-127	0	count bench/2026-09-08b/PREDICTIONS-B15-block14.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
ovsel-rows	10	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^ovsel[0-9] enc [0-9A-F]{8} usec [0-9]+ valid [01]$
map-rows	32	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^[0-9A-F]{6} 1 1[0-9]{5} [0-9a-f]{64}$
map-blank-groups	5	count bench/2026-09-08b/PREDICTIONS-B15-block14.md ^3[68ACE]0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260$
```

🔴 **`expansion-reboot-f`'s regex is written `-[f]` and that is not a typo — it
is the fix for a defect this card hit at gate 4.** A `cardnum` `count` row
searches the **whole file**, and its own declaration line is in that file. A
regex that is a **pure literal therefore matches itself**, and the row reads one
higher than the truth: as first written this row said `0`, `cardcheck` said `1`,
and the single occurrence was the row itself. Bracketing the final character
turns the regex into one that still matches the vendor-reset command but no
longer matches its own declaration, so the row is excluded by construction.

🔴 **And it took TWO tries, which is the more useful half.** The first fix
bracketed the character and the row still read `1` — because the *paragraph
written to explain the fix* spelled the command out again. A row that counts a
literal is broken by any prose that quotes it, **including the prose documenting
that it is broken by prose**. That is why this paragraph describes the string
instead of showing it.

量: every other `count` row here
already contains a class or a quantifier (`[0-9]+`, `-{2}`, `3[68ACE]`) and so
was self-avoiding by accident — **which is how block 13's `expansion-warm` row
passed without anyone knowing this was a rule.**

⚠️ **`cardcheck commands` reads 43 and this card has 42 cells; the difference is
not a defect.** The expansion holds **41** — every cell but the cold `C1-A`,
which sends nothing — and §4.2's rule table holds **2** more. Said here because
a reader comparing 43 with 42 would otherwise have to rediscover it.

| number | value | re-derived from |
|---|---|---|
| `RECIPE_ID` | `b417a3e7` | `find config -type f -print0 \| LC_ALL=C sort -z \| xargs -0 sha256sum \| sha256sum \| cut -c1-8`, **and** `r56c.manifest` |
| image bytes / sha256 | 1,043,456 / `6c6f7722…` | `stat -c %s` and `sha256sum` on the staged `.bin` |
| `vmlinux` bytes / sha256 | 4,049,497 / `df5c917f…` | `r56c.manifest`, and the staged tree's own `vmlinux` |
| boot capture | 1,424 | 1,318 量 (ten of seating 16's) + 106 derived from the mark shapes |
| `TA5` | `FFFF8D37` ± 2 | `FFFF8D34` 量 ×10, plus 106 B ÷ 3,840 B/s |
| `TA5 − TA0` | 591 jiffies | `0xFFFF8D34 − 0xFFFF8AE5`, seating 16 |
| the ten `ovselN` rows | as printed in §3.3 | `rtl819x_wdt_steps[]` in the driver |
| the 32 map digests | as printed in §3.4 | `tools/flashmap.py predict --level 0` |
| `map_hashed` | 4,186,112 | 4,194,304 − 8,192 (`H601`) |
| four rung timeouts | 2,190 / 17,517 / 560,551 / 1,121,101 µs | `2^(15+ovsel) / 14,965,000`, `CLK-08b` |
| `9−8` = `8−3` cross-check | 560,550 / 543,034 µs | differences of the four above |
| loader pair | 557,583 / 1,118,133 ms | `SPEC.md` `CLK-08`, `bench/2026-08-25/H3c-D4*` |
| ESC echo rate | ≈425 B/s | `bench/2026-09-08/C2-A.log`, 3,503 B over `--esc-after 8` |
| cells / payloads | 42 / 41, longest 103 B | the generator's own `L1`–`L4` checks |

### 4.6 🔴 The one failure mode that costs a power cycle, and where it is put

`biteraw` writes a word with `WDTE = 0x00` and a bit whose meaning is undetermined.
If that word does **not** start a countdown, the board is left in
`for(;;)` with interrupts disabled and only a power cycle recovers it.

**That is why `C8` and `C9` are ninth and tenth and not third and fourth.** By
the time they run, every other reading on this card is on disk. If `C8-B` or
`C9-B` produces no loader banner within its window:

* the board is hung; **exactly one power cycle is authorised** to recover it;
* `C10` then runs on that cold boot and is **marked in the corrections file as
  cold**, because a warm-boot count that silently includes a cold one is the
  thing `test-boot-timeline`'s `B2` exists to catch;
* the surviving `biteraw` cell is **not** retried on this seating.

---

## 5. The fence

```cells
bench/2026-09-08b/C1-A
bench/2026-09-08b/C1-P
bench/2026-09-08b/C1-K
bench/2026-09-08b/C1-MS
bench/2026-09-08b/C1-M0
bench/2026-09-08b/C1-MA
bench/2026-09-08b/C1-M1
bench/2026-09-08b/C1-MK
bench/2026-09-08b/C1-EP
bench/2026-09-08b/C1-RJ
bench/2026-09-08b/C1-RI
bench/2026-09-08b/C1-U
bench/2026-09-08b/C1-WG
bench/2026-09-08b/C1-DV
bench/2026-09-08b/C1-B
bench/2026-09-08b/C2-P
bench/2026-09-08b/C2-B
bench/2026-09-08b/C3-P
bench/2026-09-08b/C3-B
bench/2026-09-08b/C4-P
bench/2026-09-08b/C4-B
bench/2026-09-08b/C5-P
bench/2026-09-08b/C5-S1
bench/2026-09-08b/C5-S2
bench/2026-09-08b/C5-S3
bench/2026-09-08b/C6-P
bench/2026-09-08b/C6-WU
bench/2026-09-08b/C6-S1
bench/2026-09-08b/C6-S2
bench/2026-09-08b/C6-S3
bench/2026-09-08b/C7-P
bench/2026-09-08b/C7-W
bench/2026-09-08b/C7-D
bench/2026-09-08b/C7-B
bench/2026-09-08b/C8-P
bench/2026-09-08b/C8-U
bench/2026-09-08b/C8-B
bench/2026-09-08b/C9-P
bench/2026-09-08b/C9-U
bench/2026-09-08b/C9-B
bench/2026-09-08b/C10-P
bench/2026-09-08b/C10-F
```

**42 cells.** Boot 1 carries fifteen because the ladder can be stopped at any
rung there; boots 2–10 carry two to five each, and nine of the ten are **entered
through a bite** rather than through a `reboot`.

---

## 6. What this block cannot establish, written now

1. 🔴 **`FLS-26`'s 99.02 %.** A level-0 map digests the whole complement in 32
   pieces of 128 KiB. It can say *which group* moved and nothing finer. The
   level-1 maps that would localise it are not on this card, and `verify`'s new
   `<offset>` argument is not exercised either. **`rtl819x-spi` 1.1 runs here for
   the first time; it does not advance the flash question.**
2. 🔴 **The bracket does not move.** Zero flash-write commands, zero `FLR`, so
   `1,024 of 4,194,304 = 0.0244 %` is unchanged, and *"not one flash byte is
   written"* stays exactly as unsayable as it was. `n_writes` is read once, at
   `C10-F`, and it is a claim about **this driver's counter**, not about the
   device.
3. 🔴 **`WDTIND` / `REG-12` 殘留 is not closed and this card does not pretend to
   try.** `WDIOC_GETBOOTSTATUS` returns 0 always and that 0 is *not* evidence
   that no watchdog reset happened. 🆕 **But §4.3b adds a candidate explanation
   better than the three on record**: the loader prints `Reboot Result from
   Watchdog Timeout!` after a watchdog reset and prints nothing there after a
   power-on, so **something** is read after reset and consumed before Linux runs.
   If that something is `WDTIND`, the bit latches fine and the driver reads 0
   because **the loader already cleared it** — which is a different claim from
   *"the bit does not read back"*. The experiment is a desk one: find the string
   in `$FWRE_WORK/stage2.bin` and disassemble around it. Carried forward.
4. 🔴 **`CLK-08b` 殘留 — what the watchdog counts — is untouched**, and §4.3a
   explains why measuring a timeout again cannot touch it.
5. ⚠️ **`OVSEL[2]` may come out undetermined.** `C8`/`C9` separate bit 19 from
   bit 20 only if exactly one of them bites at ~35 ms. Both biting at 2.19 ms
   would mean neither bit is `OVSEL[2]`, and the hole stays open with one more
   fact in it.
6. ⚠️ **`D2` — a `.dts` or a binding — is untouched.** The whole tree still has
   0 `.dts` and 0 `.yaml`, for this driver and for the four before it.
7. ⚠️ **`n_state_foreign 0` is a claim about a counter that cannot fire here.**
   With `CONFIG_RTL_WTDOG=n` nothing else writes the register, and the vendor's
   `|= 1<<23` would have preserved every other bit anyway. `C1-WG` is the only
   reason that zero is worth printing.

---

## 7. 🔒 FROZEN

**This paragraph is the last edit to this file.** Every capture under
`bench/2026-09-08b/` is written after it. `tools/check-predictions.py` proves
that by mtime; `tools/capdate.py` proves the directory name against the
captures' own committed `started_wallclock`.

The five gates ran before the commit that froze this card, in the order §0
gives, and `spec-check` ran **first** so that a `C8`-shaped syntax defect could
never force an edit to a frozen card.
