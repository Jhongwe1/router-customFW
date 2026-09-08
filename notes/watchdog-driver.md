# `rtl819x-wdt` — a `/dev/watchdog` on a dog somebody else was feeding

*(This title read "on a **17.5 ms** dog" until 2026-09-08 evening. 量 on the
silicon that night: the encoding it refers to bites at **1,334.723 ms** under
Linux. The number is gone from the title rather than corrected in it, because a
title is the one place a stale figure gets quoted from without being re-derived
— § 10.)*

**`R5-6`. Desk half 2026-09-08, forty-fifth segment; bench half the same night,
forty-sixth segment, seating 17.** Owner of every finding this step produced;
`SPEC.md` indexes them and does not restate them.

Four segments on one calendar day (43, 44, 45, 46 all 2026-09-08 — 量 at 12:18
and again at 21:50, three sides agreeing both times). The desk half creates no
`bench/` directory; the bench half creates `bench/2026-09-08b`, and
`tools/capdate.py` reports it `OK — 68 capture(s), all 2026-09-08`, so
`RUNSHEET` lifecycle rule 3's prediction came out right.

---

## 1. The finding that decided the step's shape, and it corrects a committed row

🔴 **Under Linux this board runs with a 17.5 ms watchdog, kicked every 10 ms.
Not "about one second".**

讀, the source this image is built from,
`boards/rtl8196e/bsp/timer.c:75-84`:

```c
#if defined(CONFIG_RTL_WTDOG)
#ifdef CONFIG_RTK_VOIP
	{ extern void bsp_enable_watchdog( void ); bsp_enable_watchdog(); }
#else
	REG32(BSP_WDTCNR) = 0x00600000;
#endif
#endif
```

量, the artefact — `bsp_timer_init` at `0x802B9798` in cell `spi11`'s vmlinux,
which is the tree R5-6 builds from:

```
802b9850:	3603311c 	ori	v1,s0,0x311c      # s0 = 0xb8000000
802b9854:	3c020060 	lui	v0,0x60           # 0x00600000
802b9858:	ac620000 	sw	v0,0(v1)          # WDTCNR = 0x00600000
```

A **plain store**, so `WDTE[31:24]` becomes `0x00`, which is not the `0xA5`
stop pattern — the watchdog is *running* — and `OVSEL` is `3`.

    2^18 ÷ 14,965,000 Hz = 17.517 ms          (CLK-08b's measured frequency)

and `arch/rlx/kernel/rlx-cevt.c:159` kicks it from the TC0 tick handler at
`CONFIG_HZ = 100`. **Margin: 7.5 ms. The system tolerates zero lost timer
interrupts.**

### 1.1 What this corrects

`SPEC.md` `FW-45` (written 2026-09-07) reasons about kernel-side loop safety
from *"`CLK-08` bounds the watchdog window at about one second"*. That is the
**loader's** `OVSEL=1001`, driven at the loader prompt in the `D4`/`H3c` cells.
It is not what Linux runs. The row's number is wrong by **64×**.

### 1.2 🟢 The correction makes an old measurement mean more, not less

`FW-45`'s conclusion — that `rtl819x-spi`'s 4 MiB traversal is safe because
`cond_resched()` every 4 KiB lets the vendor's TC0 handler keep feeding — is
**unchanged and now stronger**. Seating 16 ran that traversal three times,
13.3 s each, across ten boots, with a **17.5 ms** deadline live. So:

> 量, without anyone setting out to measure it: **no interrupt-blocked window
> on the whole PIO read path exceeded 17.5 ms**, over ~40 s of in-kernel
> traversal.

### 1.3 🟢 And it bounds `IRQ-13`'s unexplained loss for free

`IRQ-13` (2026-09-06, seating 14) records driver 4.0 refusing its own handover
because over the vendor NIC's initialisation TC1 delivered **574 of 585**
interrupts — 11 short, 1.88 % — and says the mechanism is *not isolated*.

The watchdog constrains it from the other side. Those boots completed. Had any
single TC0 delivery gap exceeded 17.5 ms, the board would have reset instead.
So whatever drops TC1 interrupts there:

* is **not** producing >17.5 ms holes in TC0 delivery, and
* if 11 losses were 11 evenly spread *missed ticks*, each would be a 20 ms gap
  and the board would have bitten — so they are **not** simple missed ticks.

推, and it is a constraint rather than an explanation. It costs nothing: both
inputs were already committed. ⚠️ It assumes TC0 and TC1 share a delivery path
closely enough that a stall in one implies a stall in the other; they are two
sources in one block behind one ICTL line (`docs/interrupt-map.md` § 3.6), which
makes that likely and not proven.

---

## 2. Every `WDTCNR` toucher in the shipping image, enumerated on the artefact

Source says what *could* happen. The artefact says what *did*. Every
instruction that forms the constant `0xB800311C` in cell `spi11`'s vmlinux,
resolved to its owning symbol through that image's own `System.map`:

| address | owner | what it does |
|---|---|---|
| `0x802B9850` | `bsp_timer_init+0xb8` | `WDTCNR = 0x00600000` — **the arm**, OVSEL 3 |
| `0x8000AEE8` | `rlx_timer_interrupt+0x60` | `WDTCNR \|= 1<<23` — **the 100 Hz kick** |
| `0x8000AED4` | `rlx_timer_interrupt+0x4c` | `WDTCNR = 0; for(;;)` — the `is_fault` reboot |
| `0x80006B8C` | `bsp_machine_restart+0xb4` | `WDTCNR = 0; for(;;)` — **how `reboot` works** |
| `0x800E8FB4` | `write_watchdog_reboot+0x84` | `WDTCNR = 0; for(;;)` — `/proc/watchdog_reboot` |
| `0x8011D9A4` | `rtl8192cd_open+0x680` | `WDTCNR = 0; for(;;)` — wlan open failure |
| `0x80143D98` | `rtl8192cd_init_hw_PCI+0x10cc` | kick during wlan init |
| `0x80143E88` | `rtl8192cd_init_hw_PCI+0x11bc` | kick |
| `0x802C9258` | `rtl8192cd_init_one+0x5e0` | kick |

**Nine references, five owners: one arm, four kicks, four deliberate
self-resets.**

### 2.1 🟢 `bsp_machine_restart` is a watchdog bite, and that re-attributes `FW-37`

`boards/rtl8196e/bsp/setup.c:104-118`, 讀, and **not inside any `#if`**:

```c
static void bsp_machine_restart(char *command)
{
    static void (*back_to_prom)(void) = (void (*)(void)) 0xbfc00000;
    REG32(GIMR)=0;
    local_irq_disable();
#ifdef CONFIG_NET
    shutdown_netdev();
#endif
    REG32(BSP_WDTCNR) = 0;      // enable watch dog
    while (1) ;
    back_to_prom();             /* dead code: the dog always gets there first */
}
```

`WDTCNR = 0` is `WDTE = 0x00` (run) and `OVSEL = 0` (2^15 = **2.190 ms**).

So **there is no separate reset controller on this part's software path**: a
reboot *is* a deliberate watchdog bite at the shortest setting. That
re-attributes two existing rows without re-measuring anything:

* `FW-37` — `busybox reboot -f` reaching the loader prompt in **2.407 s** — is
  a watchdog reset, which is why `CLK-13`'s `Reboot Result from Watchdog
  Timeout!` appears on it (`REG-34` recorded exactly that on seating 14 and
  attributed it to "the warm reset").
* `CLK-08`'s bound on the shortest setting, *"the lowest setting bounded above
  at 2.3 ms by `entry`"*, now has a source-side prediction to sit beside:
  **2.190 ms**. It fits.

### 2.2 The consequence for this driver, stated as the reason it exists

A kick in the tick ISR feeds the dog whether or not userspace is alive. A
`/dev/watchdog` shipped beside it would expose a watchdog that **cannot bite** —
CLAUDE.md's *a tool that cannot fail proves nothing*, in driver form. So the
config decision is not tidiness; it is the precondition for `R5-6` existing.

---

## 3. `WDTCNR`'s encoding, and the hole in it

`0xB800311C`, `SPEC.md` `MAP-08` / `REG-12`.

| bits | field | how it is known |
|---|---|---|
| `[31:24]` | `WDTE` — `0xA5` stops, anything else runs | 讀 ×2 (SDK `WDSTOP_PATTERN`, D Table 27); 量 (reset value `A5000000`) |
| `[23]` | `WDTCLR` — write 1 to clear the counter | 讀 (SDK); 量 indirectly (the vendor kicks with it 100×/s and the board does not reset) |
| `[22]` | `OVSEL[1]` | 讀 (SDK `OVSEL_17 = 2<<21`) |
| `[21]` | `OVSEL[0]` | 讀 (SDK `OVSEL_16 = 1<<21`) **and** 量 (the 8→9 difference) |
| `[20]` | `WDTIND` | 讀 (SDK, D); 🔴 量 **refuted as readable** — `REG-12` 殘留 |
| `[19]` | `OVSEL[2]`? | 🔴 **未定** |
| `[18]` | `OVSEL[3]` | 量 (`CLK-08`: both points set it) |

### 3.1 How the split was pinned, and what is left over

`CLK-08` drove the loader to write two values and timed the resulting resets:

```
OVSEL=8 (2^23)  ->  WDTCNR = 0x00040000  ->  557.583 ms
OVSEL=9 (2^24)  ->  WDTCNR = 0x00240000  -> 1118.133 ms
```

The difference between OVSEL 8 and 9 is OVSEL bit 0; the difference in the
register is bit 21. **So `OVSEL[0]` is bit 21** — which independently agrees
with the SDK header's `OVSEL_16 = (1 << 21)`, a source that was written for a
different chip and knows nothing about these two captures. `OVSEL[1]` is then
bit 22 (`OVSEL_17 = 2<<21`), and `OVSEL[3]` is bit 18, set in both.

`OVSEL[2]` was **0 in every reading this project has ever taken**, so its bit
is bit 19 or bit 20 and nothing here separates them. Bit 20 is where both the
SDK header and the datasheet put `WDTIND`, which argues for bit 19 — but
`REG-12` 殘留 records that this die does not read `WDTIND` back at all, so the
one measurement that could corroborate the header's bit-20 assignment is
precisely the one that failed. **推, not 量.**

### 3.2 The table the driver ships, holes included

`t = 2^(15+OVSEL) ÷ 14,965,000 Hz`, `CLK-08b`.

| OVSEL | ticks | µs | encoding | how known |
|---|---|---|---|---|
| 0 | 2^15 | 2,190 | `0x00000000` | 量 (`bsp_machine_restart`, `write_watchdog_reboot`; `CLK-08` ≤2.3 ms) |
| 1 | 2^16 | 4,379 | `0x00200000` | 讀 |
| 2 | 2^17 | 8,759 | `0x00400000` | 讀 |
| 3 | 2^18 | 17,517 | `0x00600000` | 量 (this image's `bsp_timer_init`) |
| 4 | 2^19 | 35,034 | 🔴 未定 | — |
| 5 | 2^20 | 70,069 | 🔴 未定 | — |
| 6 | 2^21 | 140,138 | 🔴 未定 | — |
| 7 | 2^22 | 280,275 | 🔴 未定 | — |
| 8 | 2^23 | 560,551 | `0x00040000` | 量 (`CLK-08`) |
| 9 | 2^24 | 1,121,101 | `0x00240000` | 量 (`CLK-08`) |

🟢 **The table checks itself.** `CLK-08b` solved for a common offset `c` and got
**2.967 ms**. Predicted 560.551 minus measured 557.583 = **2.968 ms**;
predicted 1121.101 minus measured 1118.133 = **2.968 ms**. The same residual at
both points, to a microsecond, from an arithmetic that was done here from
scratch rather than requoted.

The driver returns **`-EOPNOTSUPP`** for OVSEL 4–7 and `-EINVAL` for
out-of-range, so the two failures are distinguishable at the shell, and
`/proc/rtl819x-wdt` prints all ten rows with a `valid` column so the hole is
legible **on the board** rather than only in this file.

### 3.3 🟢 The experiment that closes it, and it costs two reboots

`biteraw 0x00080000` (bit 19) and `biteraw 0x00100000` (bit 20), each timed off
the console.

| hypothesis | bit 19 gives | bit 20 gives |
|---|---|---|
| `OVSEL[2]` is bit 19 | 35.0 ms | 2.19 ms (bit 20 = `WDTIND`, no OVSEL change) |
| `OVSEL[2]` is bit 20 | 2.19 ms | 35.0 ms |

A **16×** separation, and the two hypotheses predict *opposite* orderings, so
neither can be satisfied by an instrument that is simply slow. Two bites,
~2.4 s each, no power cycle.

---

## 4. The decision: `CONFIG_RTL_WTDOG=n`, with the blast radius enumerated first

| | |
|---|---|
| **REMOVED** | `bsp_timer_init`'s arm; `rlx_timer_interrupt`'s 100 Hz kick and its `is_fault` reboot; the three wlan kicks; `kernel/panic.c:101` and `kernel/exit.c:925,947`'s `is_fault` stores |
| **KEPT** | `bsp_machine_restart` (`boards/rtl8196e/bsp/setup.c:114`, not gated) → **`busybox reboot -f` still resets the board**, so `FW-37`'s twelve-boots-per-power-press economy survives. `write_watchdog_reboot` (`drivers/char/rtl_gpio.c:2178`, not gated) → a **vendor** "bite now" instrument survives as an independent control on this driver's own bite |
| **COST** | the vendor's "the TC0 interrupt stopped" net. Replaced by BOOTGUARD, one layer up |
| **BONUS** | a panic now **prints** |

### 4.1 Why the three wlan kicks go with it

They are wrapped in `#if defined(CONFIG_RTL865X_WTDOG) || defined(CONFIG_RTL_WTDOG)`.
量: `CONFIG_RTL865X_WTDOG` is **absent** from this build's
`include/linux/autoconf.h`, which carries `CONFIG_RTL_WTDOG 1` and nothing
resembling the other. So the disjunction has exactly one live arm.

### 4.2 The panic bonus, with the arithmetic

With `=y`, `panic()` sets `is_fault`; the next TC0 tick (≤10 ms away) takes the
`else` branch, disables interrupts, writes `WDTCNR = 0` and spins — a bite
2.19 ms later. Total ≤12.2 ms. At 38400 8N1 one byte is 260.4 µs, so a panic
message is cut at **≈46 characters**.

That is 推 — the arithmetic is sound but nothing here has captured a
vendor-kernel panic — and it explains something already measured: `FW-31`
counts **97 `panic_printk` call sites** in this tree. A kernel that reboots
12 ms into its own panic needs a print path that does not wait for anything.

**Refuted by** any capture of a vendor-kernel panic longer than ~46 characters.

### 4.3 The evidence, written as a prediction

The nine `0xB800311C` references fall to **two** vendor-owned, plus this
driver's own. This is the `D4` pattern R5-5 used on
`CONFIG_MTD_RTL819X_WRITE`: ship `=n`, count the instructions, then rebuild
`=y` in a discard tree and watch them come back.

**Refuted by** any third vendor survivor, or by `busybox reboot -f` no longer
resetting the board.

### 4.4 🔴 It was refuted. Nine fell to **six**, and the cause is mine

量, the same enumeration on cell `r56c`'s vmlinux:

| survivor | predicted? |
|---|---|
| `bsp_machine_restart+0xb4` | ✅ |
| `write_watchdog_reboot+0x84` | ✅ |
| `rtl8192cd_open+0x680` | 🔴 no |
| `rtl8192cd_init_hw_PCI+0x10cc` | 🔴 no |
| `rtl8192cd_init_hw_PCI+0x11bc` | 🔴 no |
| `rtl8192cd_init_one+0x5e0` | 🔴 no |

The three that mattered **did** go: `bsp_timer_init`'s arm and both of
`rlx_timer_interrupt`'s references are absent from the image.

**The cause is a specific reading error and it is worth more than the
prediction would have been.** The wlan sites are not gated on
`CONFIG_RTL_WTDOG` at all. In the tree that builds they read

```c
#if defined(CONFIG_RTL_8198) || defined(CONFIG_RTL_819XD) || defined(CONFIG_RTL_8196E)
	REG32(BSP_WDTCNR) |=  1 << 23;
```

— gated on **which board this is**, and `CONFIG_RTL_8196E` is `1`. The
`#if defined(CONFIG_RTL865X_WTDOG) || defined(CONFIG_RTL_WTDOG)` wrappers the
claim came from are in `drivers/net/wireless/rtl8192e/`, and the directory that
**builds** is `rtl8192cd/` — which had already been measured (`built-in.o`,
820,910 bytes) in the same session, *before* the claim was written. Two SDK
vintages of one driver, gated differently, and the gating was carried across
from the copy that is not compiled.

🔴 **The evidence was in my own earlier output and I read past it.** The
`CONFIG_RTL_WTDOG` grep listed exactly three `rtl8192cd/` files —
`8192cd_osdep.c`, `8192cd_sme.c`, `8192cd_ioctl.c` — and `8192cd_hw.c` was not
among them. The absence *was* the answer. This is `rlxfw-requote-hazard`'s
shape: a partial view requoted instead of re-derived.

### 4.5 What the refutation costs, bounded by measurement rather than argued

**The decision: nothing.** The 100 Hz unconditional kick and the 17.5 ms arm
are gone, which is exactly what a bitable watchdog needs.

**The safety net: a bounded amount.** All three surviving *kicks* are on the
wlan bring-up path, and 量 the image's own initcall table:

```
802d0ad4 t __initcall_rtl8192cd_init6      <- device_initcall,  level 6
802d0b9c t __initcall_rtl819x_wdt_init7    <- late_initcall,    level 7
```

**A kick that runs before `BOOTGUARD` arms cannot feed `BOOTGUARD`.** The
fourth reference, `rtl8192cd_open+0x680`, is `WDTCNR = 0; for(;;)` — a
deliberate **bite** on the wlan open failure path, not a feeder, and it
predates this driver.

⚠️ **未定**: whether `rtl8192cd_init_hw_PCI` can be re-entered from a userspace
`ifconfig up` *after* this driver has armed. Reading more source cannot settle
it — the call graph goes through function pointers and a `vap_idx` loop. One
cell can, and § 6.5 is it.

---

## 5. The timeout model, and why it is two layers

The longest hardware timeout on this part is **1.121 s**. No ordinary
`/dev/watchdog` daemon pings that fast. A driver reporting `timeout=1` and
refusing everything else would be honest and useless.

| state | hardware | who feeds it | what it catches |
|---|---|---|---|
| `STOPPED` | `WDTE=0xA5` | nobody | nothing. The silicon's power-on state (`REG-12`) |
| `BOOTGUARD` | armed at `hw_ovsel` | a kernel timer, unconditionally, every `kick_ms` | the kernel **timer wheel** stopping |
| `USER` | armed at `hw_ovsel` | the same kernel timer, **only** while `time_before(jiffies, deadline)` | userspace stopping |

The difference between the two armed states is one `time_before()` and nothing
else. Two feeding paths would be two places to get wrong.

`BOOTGUARD` catches a **superset** of what the vendor's ISR kick caught: the
timer wheel stops if the ISR stops, and also if the wheel itself wedges with
interrupts still flowing.

### 5.1 🔴 One deliberate deviation from the upstream contract

`Documentation/watchdog/watchdog-api.txt` says a close without `nowayout`
**stops** the watchdog. Here it returns to `BOOTGUARD`.

Stopping would silently delete the boot-time net that `CONFIG_RTL_WTDOG=n`
removed. A driver that becomes *less* safe when a daemon exits cleanly is the
wrong default on a board with one power switch and no spare. The upstream
behaviour is still reachable and is counted separately: `stop` on `/proc`, or
`WDIOS_DISABLECARD`.

This is a `docs/driver-diff.md` **L2** row — same silicon, opposite decision
from the vendor's (unconditional ISR kick) *and* from upstream's (stop on
close), with the reason for each written down.

### 5.2 🔴 No read-modify-write on `WDTCNR`, and that is this project's own scar

The vendor kicks with `REG32(WDTCNR) |= 1<<23`. `SPEC.md` `IRQ-08` is the
**measured** instance of exactly that shape going wrong one register away: the
vendor's tick handler does `REG32(BSP_TCIR) |= BSP_TC0IP` on a register whose
`IP` bits are write-1-to-clear, and therefore clears every pending bit in
`TCIR` a hundred times a second — including one belonging to a driver it has
never heard of. That finding is what bounds every single-sample reading of
`TCIR` this project has ever taken.

`WDTCNR` contains `WDTIND`, whose semantics on this die are undetermined. So
every write in `rtl819x-wdt.c` is a **full word composed from the driver's own
shadow**, and there is deliberately no set-bit helper. The cost is that a
foreign write is not preserved. That is the point, and `n_state_foreign`
counts it.

---

## 6. The experiment, and its refutation conditions written first

`D1` says ten boots must include **the thing the driver does**. For a watchdog
that is *resets the machine when it is not fed*, so the ten boots must contain
a bite.

### 6.1 A bite on this board is cheap, and was already routine

* `bsp_machine_restart` **is** a bite (§ 2.1), so every `busybox reboot -f`
  this project has run was one — dozens.
* It is self-clearing: `CLK-10`, `WDTCNR` reads `A5000000` after a real reset.
* It writes no flash.
* `FW-37`: 2.407 s from command to loader prompt.
* No boot loop is possible: the loader boots from **flash**, which holds the
  vendor firmware; this image lives in RAM at `0x80500000` and is re-entered by
  hand.

### 6.2 The field that proves the config decision

**`wdtcnr_at_probe`**, latched in `late_initcall` before the driver writes
anything:

| build | value | meaning |
|---|---|---|
| `CONFIG_RTL_WTDOG=n` (shipping) | `A5000000` | nobody armed it |
| `CONFIG_RTL_WTDOG=y` (control) | `00600000` | `bsp_timer_init` armed it at OVSEL 3 |

One field, two values, and it is the whole proof. A card gates on a **field**,
never on a mark — `FW-47`: every capture line is CRLF and `rlxfw_mark()`
interleaves with busybox ash's echo.

### 6.3 The ladder is DIFFERENCES, and that is the design

A single absolute bite time carries an unknown offset: the UART's last byte is
still in the shift register when the counter is armed (260 µs at 38400), and
the loader takes its own time to first byte (`CLK-14`: 2.07 ms).

Time four bites at OVSEL 0, 3, 8, 9 — predicted **2.190 / 17.517 / 560.551 /
1121.101 ms** — and fit `gap(OVSEL) = 2^(15+OVSEL)/f + d` for `f` and `d`.
**Three independent differences where `CLK-08b` had two points and one
unknown**, and OVSEL 8 and 9 were measured through a completely different path
(the loader, driven at its own prompt). If the Linux figures reproduce that
pair's *difference*, 14.965 MHz is confirmed from inside Linux against a number
derived at the loader. If they do not, one of the two paths is wrong and the
disagreement is the finding.

🟢 **The negative control is in the same cells.** OVSEL 0 and 3 are the
vendor's own two values. 17.517 ms must come out of a driver of mine at the
number `bsp_timer_init` programmed, and 2.190 ms must match what
`bsp_machine_restart` has been doing for every reboot in this project's
history. A ladder whose two known rungs disagreed with the two the board has
been living on would refute the driver, not the clock.

### 6.4 The ordering constraint `PROGRESS.md` carried, and what it becomes

The carried-forward note says the `map` cell must run **before** the wdt is
armed, because `map 0` is a ~13 s in-kernel loop and the watchdog is the most
likely thing to reboot the board mid-way.

With `CONFIG_RTL_WTDOG=n` the reason changes and the constraint stays. During
`map 0` the vendor's dog no longer exists; the only dog is mine, and
`BOOTGUARD` arms it at boot. So the card writes `stop` before `map 0`.

🟢 **And then it runs `map 0` a second time with `BOOTGUARD` live**, which turns
the hazard into a measurement: does the map path yield to the timer wheel often
enough to be fed at 250 ms intervals under a 1.121 s deadline? Safe-first, then
armed, and the second run is a result rather than a risk.

### 6.5 🟢 "Am I the only feeder?" — a cell whose valuable outcome is negative

§ 4.4 leaves three surviving wlan kicks whose reachability after
`late_initcall` is 未定, and § 7.4 says `n_state_foreign` cannot see a foreign
`|= 1<<23`. So the question is not answerable by reading. It is answerable by
one cell:

```
stop ; kickms 3000 ; ovsel 9 ; bootguard        # hw timeout 1121 ms
```

The kernel timer will not come round for 3,000 ms. If nothing else writes
`WDTCLR`, the board **must** reset at ≈1.121 s.

| outcome | means |
|---|---|
| resets at ≈1.121 s | this driver is the only feeder; § 4.4's enumeration is complete |
| survives 3 s | 🔴 **something else is kicking** and the enumeration is not complete |

**A watchdog cell in which "the board survived" is the finding.** It costs one
reboot. `kickms` exists only for this, and it is deliberately *not* clamped
against `hw_timeout_us`: a value that guarantees a bite is exactly what the
cell asks for, and a driver that refused it would be refusing the measurement.

⚠️ Run it with the wlan interface **up**, or it tests nothing — the whole point
is the state in which a wlan kick could plausibly run.

---

## 7. What this step does not establish

1. **Where `OVSEL[2]` is.** § 3.1. Four of ten settings are refused.
2. **Whether `WDTIND` works.** `WDIOC_GETBOOTSTATUS` returns 0 *always*, and
   that 0 is not evidence that no watchdog reset happened — it is evidence the
   bit does not read back (`REG-12` 殘留). `WDIOF_CARDRESET` is deliberately
   **absent** from `.options`: a driver must not advertise a capability it
   cannot honour. `wdtind_at_probe` is exported so the claim stays visible
   rather than being laundered through an ABI with no way to say *unknown*.
   ⚠️ The residual's own prescription — a payload that reads `0xB800311C` as
   the first thing after reset — **cannot** be satisfied by a Linux driver,
   because the loader runs first. It stays on `probe3`.
3. **What the watchdog counts.** `CLK-08b` 殘留: 14.965 MHz has no known
   integer relationship to the 200.0049 MHz base.
4. **`n_state_foreign` cannot fire in the shipping image**, and saying so is
   the point. With `=n` nothing else writes `WDTCNR` while the driver runs;
   with `=y` the vendor's `|= 1<<23` preserves every other bit, so a masked
   read-back would still agree. Its positive control is the `wedge` verb.
   The strong discriminator between builds is `wdtcnr_at_probe` (§ 6.2).
5. **Nothing on the silicon.** Not one line of this driver has executed. The
   whole of §§ 1–6 is desk work on committed captures, vendor source and a
   built vmlinux.

---

## 8. 🔴 A correction found on the way, older than this segment

**`CONFIG_GPIO_SYSFS` has been an undeclared config difference in three
consecutive images.**

量, running the gate that `config/rlxfw-kernel.delta` describes against images
that had already shipped:

```
kconfig-delta check --built spi11.config-built
  UNDECLARED (1) -- the build's .config differs here and nothing says why:
     CONFIG_GPIO_SYSFS                            - -> n
  RESULT: REFUSED
```

and the `oldconfig` logs:

| cell | `(NEW)` lines | which |
|---|---|---|
| `r53b2` (before `R5-4`) | 0 | — |
| `r54b` (`R5-4`, seating 13's image) | 1 | `GPIO_SYSFS [N/y/?]` |
| `r55b` (seating 16's image) | 1 | `GPIO_SYSFS [N/y/?]` |
| `spi11` | 1 | `GPIO_SYSFS [N/y/?]` |

It entered with `CONFIG_GPIOLIB=y` on 2026-09-06 (`drivers/gpio/Kconfig:51`,
`depends on SYSFS && EXPERIMENTAL`, 量 both `y` here) and has been undeclared
in every image since, **including the one seating 16 ran**.

⚠️ **The three images are not wrong.** The value taken was `n`, which is what
the row now declares, so no shipped behaviour changes and no measurement is
retracted. What was wrong is that the value was decided by **how stdin happened
to be connected** — `--oldconfig yes` answers `y` to a `[N/y/?]` — which is
exactly the class of accident the delta file exists to close. The file's own
header asserted the opposite (*"`(NEW)` is 0 again and no answer — empty, n, y
or EOF — can change the result"*) and had been wrong for two days.

🔴 **Why nothing caught it**: `kconfig-delta check` is not run by
`rlxfw-kbuild.sh` and has to be typed. That is the same shape as `LOG.md`'s
note that `rlxfw-marks verify` is never run automatically either — **two gates
that exist, work, and are not on any path**. Carried forward as `CFG-2`.

### 8.1 The prediction this segment's own build has to satisfy

Because `CONFIG_WATCHDOG=y` opens a menu, the same accident is available one
directory over. So it was enumerated rather than assumed: parsing
`drivers/watchdog/Kconfig` with `if`/`endif` nesting tracked and every
`depends on` evaluated against this build's `.config`, exactly **two** entries
carry a prompt with all conditions met — `WATCHDOG_NOWAYOUT` and
`SOFT_WATCHDOG`. `CONFIG_PCI=n` and `CONFIG_USB_SUPPORT=n` keep the PCI and USB
sections closed; every MIPS entry depends on another platform.

Both are pinned. **`(NEW)` = 0.** Refuted by any `(NEW)` line in the build log.

### 8.2 🔴 And `SOFT_WATCHDOG=n` is load-bearing, not housekeeping

`softdog` registers the **same** miscdevice minor this driver does —
`WATCHDOG_MINOR = 130`, 讀 `include/linux/miscdevice.h:15`. With both built in,
whichever registers second takes `-EBUSY` from `misc_register` and the image
ships a `/dev/watchdog` whose identity depends on link order.
`rtl819x-wdt` reports `misc_rc` in `/proc` precisely so such a collision would
be a field rather than a mystery — but not having it is better than detecting
it.

---

## 9. `MK6` is the first Kbuild row whose absence is silent

`MK2`/`MK3`/`MK4` all link against a framework symbol (`clocksource_register`,
`gpiochip_add`, `mtd_device_register`), so dropping the config line that makes
the framework reachable is an undefined reference and the build stops.

A watchdog driver is not reached that way. `drivers/Makefile:79` is
`obj-$(CONFIG_WATCHDOG) += watchdog/` — the whole **directory** is conditional.
Without `CONFIG_WATCHDOG=y` the file is never compiled, `MK6`'s line is never
read, and the build is green with no driver in it.

`MK6`'s witness is therefore a **string against the built image**:
`str:rtl819x-wdt`, which `rlxfw-marks.py verify` reads out of the artefact.
CLAUDE.md's own note says only `verify` can catch a mark that compiled and is
not in the image; here what it catches is a whole translation unit that was
never compiled at all.

---

## 10. Seating 17 — what the silicon said, and the three things it refuted

**2026-09-08 evening, forty-sixth segment. Three power cycles, ten boots, nine
watchdog resets. Zero flash-write commands, zero `FLR`, `n_writes 0`.**
The card is `bench/2026-09-08b/PREDICTIONS-B15-block14.md` (frozen, 42 cells);
the seating's own record is `CORRECTIONS-block14.md` beside it.

### 10.1 The driver works, and the predictions that mattered were exact

Ten boot captures, **every one 1,424 bytes**, a figure derived at the desk from
the mark shapes (seating 16's measured 1,318 + `S8`'s 10 + `W0`…`W5`'s 96) with
106 of those bytes never previously measured. `RLXFW-ID0=B417A3E7`.

**`wdtcnr_at_probe A5000000`** is the whole proof that § 4's
`CONFIG_RTL_WTDOG=n` did what the blast-radius enumeration said — one field,
two possible values, written down before the build. `registered 1`,
`misc_rc 0`, `state_name BOOTGUARD`, `n_arm 1`.

`TA5` read **`FFFF8D38`** against a prediction of `FFFF8D37 ± 2`: the 106 new
bytes cost 27.6 ms of UART time at 38400, which is 2.76 jiffies, and the tick
counted 4.

🟢 **`W4` is a reading nobody planned.** The driver writes `0x00A40000` (arm
*and* `WDTCLR`) and the register reads back **`0x00240000`**, so **`WDTCLR` does
not read back on this die.** `WDTCNR_VOLATILE_MASK` was right to ignore it, and
now that is measured rather than assumed.

All ten `ovselN` rows came out exactly as tabled, **including
`ovsel3 enc 00600000`** — a driver written blind, decoding a split field the
vendor never documented, computing the vendor's own constant.

### 10.2 🔴 The step's own headline number was wrong by 76×

§ 1 of this file is titled *"the finding that decided the step's shape"* and it
is the 17,517 µs figure. **It is a loader-state figure and this driver does not
run at the loader.**

Two rungs 32× apart, each carrying its own `mdelay(50)` ruler in the same
capture:

| rung | encoding | silence after `RLXFW-W-GO` | ruler | floor |
|---|---|---|---|---|
| `bite 3` | `00E00000` | **1,334.723 ms** | 50.517 ms | **0.517 ms** |
| `bite 8` | `00840000` | **41,930.599 ms** | 49.132 ms | **0.868 ms** |

`gap(8) − gap(3) = 40,595.876 ms` over `2^23 − 2^18 = 8,126,464` counts gives
**`f = 200,180 Hz`** with `d = +25.179 ms`. `CLK-17` measured `TC0CNT` under
Linux at **200,005 Hz** — different register, different method, different
seating. **Ratio 0.999.**

So `CLK-08b`'s 14.965 MHz is a loader-state constant exactly as `CLK-17`'s
14,286,057 Hz is, and `CLK-08b`'s open residual — *what does the watchdog
count* — is answered: **it counts what the timer block counts.**

⚠️ **`RTL819X_WDT_HZ` and the whole `usec` column of `rtl819x_wdt_steps[]` are
therefore documented-wrong by 76× and are NOT changed yet.** The table is what
`/proc` prints and what a card predicts against; changing it silently would
break the one field a seating compares with a frozen card. Deriving it at init
— the way `rtl819x-timer`'s `hz_used` is derived, `CLK-17`'s 2026-09-04 fix —
is `R5-6`'s second bench half.

🟢 **The direction of the error is the safe one.** `kick_ms 250` against
`OVSEL` 9 was believed to be a 4.48× margin; it is **335×** (83.8 s).

### 10.3 🟢 § 6's "am I the only feeder" cell, and the answer

🔴 **The cell as written in § 6 and on the card was VOID**, and the seating's own
third cell is what showed it: `kickms 3000` against `OVSEL` 9 is 3 s against
**83.8 s**, so the kernel timer kicks 28 times before the hardware could bite.

Re-run at `OVSEL` 0 (163.7 ms) against the same 3 s timer, both halves:

* `R2-SO3`, `wlan0` **down** → board reset;
* `R2-SO6`, after `ifconfig wlan0 up` (antenna attached) → board reset.

**So nothing else on this board writes `WDTCLR` after `late_initcall`, including
with the vendor's wlan driver brought up from userspace.** § 4.4's 未定 —
whether `rtl8192cd_init_hw_PCI` can be re-entered from an `ifconfig up` after
this driver has armed — is closed by experiment, which is what `kickms` exists
for.

### 10.4 🔴 § 3's hole: both candidate bits refuted

`biteraw` was built to close `OVSEL[2]`'s bit-19-or-bit-20 question with a 16×
separation. Both words are `OVSEL` 0 in every known bit plus the candidate, so
the two predictions were **163.7 ms** (bit does nothing) and **2,619 ms** (bit
is `OVSEL[2]`).

| cell | word | ruler | silence |
|---|---|---|---|
| `R2-RAW19` | `00080000` | 50.370 ms | **68.647 ms** |
| `R2-RAW20` | `00100000` | 50.719 ms | **12.336 ms** |

**Neither.** And both are *shorter* than `OVSEL` 0, by factors 2.4 and 13.3 —
an `OVSEL` bit can only lengthen a timeout. **Neither bit 19 nor bit 20 is
`OVSEL[2]`**, the hole stays open, and the prescription is now a sweep rather
than a guess: `biteraw` one bit at a time over bits 16…23, eight cells, eight
boots, each window three times the value `f = 200,180 Hz` predicts
(`SPEC.md` `FW-53` 殘留).

### 10.5 🟢 Two controls that fired, and one instrument found for free

**`n_state_foreign`'s positive control fired**: `R2-WG` ran `wedge` without
resetting the board and `R2-F` reads `n_wedge 1`, `n_state_foreign 1`,
`shadow_agrees 1`. § 5.4 says that counter cannot fire in the shipping image;
this is the only way it is ever seen to move, and it has moved.

**Three refusals, three errnos**, routed through `cat` so `strerror` prints
instead of `FW-41`'s truncated ash echo: `EPERM` (locked), `EOPNOTSUPP` (the
`OVSEL[2]` hole), `EINVAL` (out of range), with `n_reject` 1→2→3 and `hw_ovsel`
unmoved at 9 throughout. That is § 3's *"distinguishable at the shell"* claim,
tested.

🟢 **And the loader prints its own reset cause.** `Reboot Result from Watchdog
Timeout!` appears after every watchdog reset and is **absent** after every cold
power-on. Both directions have been on disk since 2026-08-24 and nothing had
read them. This seating: three cold power-ons, 0 lines; nine bites, 1 line each.
It uses no timestamp, and it is what separates *"the board reset"* from *"the
board reset because of a watchdog timeout"* for § 10.4's two cells.

### 10.6 🔴 What it cost, and both extra power cycles were one mistake

**A cell whose payload can reset the board, given no `--esc-after`.**

* `C1-WG`: the board took a watchdog reset while ash was still echoing the
  command, at `; c` — before the write happened. The cell had no `--esc-after`
  because this file's own § 5 says the wedge *"cannot start a countdown"*.
  `R2-WG` re-ran it and it did not bite. **One observation, unexplained, not
  reproduced.**
* `C3-B`: rung 8's window was 20 s and the answer was 41.9 s — **the same root
  cause as § 10.2**, since every window on the card came from the constant the
  card's own third cell refuted.

Both times the loader autobooted from flash and the **vendor firmware ran**, for
roughly two and four minutes. Seating 8 has the precedent and its bracket was
unchanged; this is unplanned exposure and is recorded as such.

🟢 **The guard added after the second one stopped it becoming a third**: after
every bite, prove the loader was caught *before* handing the board to
`looprun`. It fired on `C3-B` and again on `R2-WG`.

🔴 **`OVSEL` 0 is not measurable by this method at all.** `prom_putchar` fills a
UART FIFO rather than the wire, so `rlxfw_puts` returns with bytes still queued
and a 163.7 ms reset lands mid-drain — the `0x8D` corrupting `RLXFW-W-GO` in
`C1-B` is that. § 6's ladder has **two clean rungs, not four**.

### 10.7 🟢 What the SPI driver did while the watchdog was armed

Constraint ① of the card: `map 0` disarmed, then re-armed and run again.

| | Δjiffies | Δ`n_hw_kick` | predicted |
|---|---|---|---|
| at rest | 343 | **14** | 13.72 |
| across the **armed** 4 MiB traversal | 12,143 | **485** | 485.7 |

`map_jiffies` 1,280 both times; the 32 digest lines byte-identical between the
two runs. **The timer wheel ran at its programmed rate through a 12.8 s
kernel-mode SPI traversal under a live deadline** — far stronger than *the board
survived*, and the at-rest row is the control that says what the rate is.

⚠️ `jiffies` wrapped through zero inside that measurement
(4,294,955,745 → 592, Linux's `INITIAL_JIFFIES = −300·HZ`).
