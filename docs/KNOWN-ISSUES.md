# Known issues

**What this repository does not establish.**
`plan/CHARTER.md` §110 rule 2 asks for a known-issues list beside every release.
This is that list, and it is written to the same standard as everything else
here: each entry names what is *not* true, what was measured instead, and which
gate changes it. Nothing below is a plan; the plan is `PROGRESS.md`'s gate board.

⚠️ **This file on `main` is the CURRENT list, not `v0.4`'s.** A release's list is
the copy at that release's tag, which is frozen; this one keeps moving. Anything
that has since been closed is at the bottom rather than deleted, so the two can
be read against each other. 🔄 **`v0.2` → `v0.3` on 2026-09-11.** 🔄 **`v0.3` → `v0.4` on 2026-09-17.**

Marked the same way as the rest of the repository: **量** measured on the device
· **讀** read out of code, a dump or a document · **推** inferred, pending a
measurement.

---

## The firmware does not exist

| | |
|---|---|
| 🔄 **Nothing of mine has driven a peripheral — and as of 2026-09-03 21:20 that is no longer true, so this row now says what IS still true instead.** 🟢 **`rtl819x-timer` executed on the silicon**: it programmed `TC1DATA` and `TCCNR` (`tccnr` `C0000000` → `F0000000`, exactly bits 29/28), registered a `clocksource` the kernel listed as `rtl819x-tc1`, was read fourteen times, and unwound both writes on disarm — twice, the second after a 703-second arm. **So a peripheral register block on this SoC has now been driven by code of mine.** 🔴 **What is still true, and is the narrower claim this row keeps**: nothing of mine has driven a peripheral that the system *depends on*. The timer ran at **rating 0** precisely so the kernel would not switch to it — 量, `TM-4b` read `jiffies` while `TM-4a` listed both — and `GIMR` bit 9 was read and never written, so **no interrupt of mine was ever delivered**. `R5-3` is the step that changes the first of those and `R6` the second; **`R5-2` must not be read as having changed either.** 🔴 **2026-09-04, seating 12: the sentence in bold above expired at 14:07, and the clause before it did not.** 量: `irq_count` **119,818**, `irq_spurious` 0, `irq_stuck` 0, a `/proc/interrupts` line `25: … ICTL rtl819x-timer` that `EX-0` measured absent beforehand and `EX-19` measured absent again afterwards, and a delivery rate matching `hz_used / period_cycles / hz_kernel` to **0.02 %** at two periods 16× apart (`SPEC.md` `IRQ-08`). **`GIMR` bit 9 is still never written by this driver** — `request_irq` asks the irqchip and `bsp_ictl_irq_unmask` does it, 量 `00209100` → `00209300` and back down on `free_irq`, three times each. **What survives is the narrower claim this row exists to keep**: nothing of mine drives a peripheral the system *depends on*. `rating` read **0** in all eighteen dumps and the time base was `jiffies` throughout, deliberately — that is `R5-3b` ⚠️ **(split on 2026-09-06 into `R5-3b-1`, the `/proc`-driven handover, and `R5-3b-2`, arming at boot)**, and `R5-3a` must not be read as having changed it. 🔄 **2026-09-06: BOTH halves of `R5-3b` closed, so the bold sentence above expired again — first at 03:11 and then at 14:48 — and this row did not follow for two segments.** 🟢 **The system tick is this driver's, and from boot**: a `clock_event_device` at rating 300, the tick core exchanging the devices on eleven independent boots (`ce_mode=2`, `ce_handler` `80036D50` → `80036FC4`), and *before userspace* proved by an ORDERING rather than a field — `RLXFW-TA8` precedes `RLXFW-B10` in the same capture, on all eleven — ~~at byte 887 and 925~~ 🔄 **量 2026-09-11 (`R5-11`): that pair reproduces under neither convention — raw (925, 965), CR-stripped (885, 923), identical on all eleven captures. The ORDERING holds under both; only the two offsets were wrong, and their *difference* of 38 is right, which is why eight files carried them. `SPEC.md` `CLK-27`.** 🔴 **So the narrower claim has to move again, and what survives is narrower still: the CLOCKSOURCE half is untouched.** `rating` read **0** in every dump of both seatings and the system's time *source* is still `jiffies`; only the *tick* is mine. ⚠️ And the interrupt-loss mechanism `IRQ-13` works around is **not isolated** — the driver moves its pre-check window rather than explaining why the vendor's NIC initialisation costs 11 of 585 interrupts. 🟢 **Found by the thirty-seventh segment's closeout enumeration, not by the segments that made it stale** — which is the case for asking every owner file what moved rather than asking which ones look relevant. 🔴 **2026-09-06, seating 13: that narrower claim expired at 03:11.** `R5-3b-1` registered a `clock_event_device` at rating 300, the tick core exchanged the devices **three times on three independent cold boots** — `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4` — and from that instant `jiffies` advanced because of an interrupt this repository's own source produced. 🟢 **And it is not asserted, it is caused**: `cereload` changes TC1's reload and the kernel's clock follows, six rows over five reloads, ratios `1.0000 / 2.0000 / 1.0000 / 4.0000 / 1.0000 / 10.0000`; at 20000 the shell answered a `cat` after a `sleep 5` that took **50 real seconds**. `P3-7` then shows the two interrupt lines at different rates for the first time — the vendor's 3,009 against my 301 over 30.10 real seconds, with `Δjiffies` = **301**. **So the system now depends on a peripheral driven by code of mine.** ⚠️ **What is still true and is narrower again**: the dependence is created by a `/proc` write **after userspace exists**, never at boot — every one of the three boots came up on the vendor's tick and was handed over by hand. And the **clocksource** side is untouched: `rating` read 0 in every dump of this seating too, and `available_clocksource` was never asked to change. Arming at boot is `R5-3b-2`; **`R5-3b-1` must not be read as having done it**. 🔴 **2026-09-06, seating 14: that sentence expired at 14:48, and it is the last of this row's five successive narrowings.** `R5-3b-2` arms the timer from inside the kernel: `arch_initcall` does `arm`/`ackip`/`reqirq`, `late_initcall` takes the pre-check window and registers the rating-300 `clock_event_device`. **Ten boots** (`M1`…`M10`, all warm resets driven by `busybox reboot -f`) **plus an eleventh from a cold power-on whose every field is byte-identical**, image `ea6ee537`, driver 4.1 — `boot_done=1`, `ce_live=1`, `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4`, the rating-99 negative control registered and never called, `irq_spurious`/`irq_stuck`/`ce_hw_bad`/`ce_badmode` all 0, zero lost ticks over 263.73 s three ways with residual 0. 🟢 **And *before userspace* is proved by an ordering rather than by a field**: `RLXFW-TA8` (the instant the registration returned) precedes `RLXFW-B10` (`init_post()`, immediately before the branch into `/sbin/init`) in the same capture, on all ten — ~~byte 887 against 925 on `M1`~~ 🔄 **量 2026-09-11 (`R5-11`): that pair reproduces under neither convention — raw (925, 965), CR-stripped (885, 923), identical on all eleven captures. The ORDERING holds under both; only the two offsets were wrong, and their *difference* of 38 is right, which is why eight files carried them. `SPEC.md` `CLK-27`.** 🔴 **The first version of it refused its own handover, twice, and that refusal is the seating's most useful reading**: 4.0's pre-check window spanned the vendor's NIC initialisation, over which TC1 delivers **574 of 585** interrupts — 1.88 % against a 1 % tolerance — while the steady state loses **1 in 14,385**. The tolerance was not widened; the window was moved. `SPEC.md` `IRQ-13`. ⚠️ **What is still true and is narrower again**: the **clocksource** half is untouched — `rating` read 0 in all ten dumps and the system's time SOURCE is still `jiffies`; only the *tick* is this driver's. And nine of the ten boots are warm resets driven by `busybox reboot -f` from the host (`FW-37`); one power-on started the seating. **`R6` is still the gate that makes a peripheral of mine carry the network.** *(This row read "There is no driver of mine" until 2026-09-03, and that sentence stopped being exact at `R5-1`: `config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c` exists, compiles, and is linked into the image — 量, `rtl819x-tc1` present once in `vmlinux`, absent from every image built before it. **It has not executed.** It also writes no register at boot and registers nothing until a shell asks it to, so even on the board it is inert until `R5-2`.)* 🔄 **The two sentences inside that parenthesis are kept verbatim and both expired on 2026-09-03**: it executed, and it stopped being inert the moment `TM-3` wrote `arm`. **The half that survived is the one that was doing the work** — *writes no register at boot, registers nothing until a shell asks it to* — 量, `TM-1` read `state=idle`, `tccnr` at its init value and `available_clocksource` naming only `jiffies`, on a board that had been running my kernel for 30 s. 🔴 **2026-09-03: and it has a known defect, found at the desk before it ever ran.** Its `tc1_ext_trusted` flag reports **1** on sampling gaps longer than one counter period, because the masked difference aliases back into the trusted band — 量, a 60 s gap loses six whole wraps and the flag still says trusted (`SPEC.md` `CLK-22`, `PROGRESS.md` `TMR-1`). **Nothing reads that field yet**: `R5-2`'s card quotes `tc1_cycles` and unwraps outside the kernel, and predicts the false `1` so the defect is confirmed on silicon rather than only on paper. The fix is `R5-3`'s, because `config/` is the source of `RECIPE_ID` and touching it invalidates the staged image. 🔄 **2026-09-03, seating 11: confirmed on silicon — mechanism exactly right, threshold wrong by 71.43× — and a SECOND defect found that the desk analysis did not identify.** The aliasing did not happen at 60 s (under Linux `CDBR` divides by 1000, so one period is **671.07 s**, not 9.395016 s); it happened at **703 s**, where the true gap of 140,693,532 counts was accumulated by `tc1_ext` as **6,475,804** — exactly that value mod 2²⁷ — with `trusted` still **1**. 🔄 **2026-09-04 (`R5-3a`): this clause used to name `tc1_ext_gap_max` **6,475,672** as the aliased value and that was wrong by 132.** 量, recomputed from `TM-5b-arm`/`TM-5b2` by program: `140,693,532 mod 2²⁷` is **6,475,804**, which is both the wrapped TC1 delta `(6,477,665 − 1,861) & MASK` and `Δtc1_ext`; `gap_max` reads 6,475,672 because `tc1_ext_reads` goes 1 → 3 across that arm, so it is the **largest single** inter-read gap of two, not the span (the other is 132). **The mechanism is unchanged and the alias is exact** — what was lost is precisely one period, 134,217,728 counts. The clause had been copied into nine committed files. 🔴 The second defect: 讀 `rtl819x-timer.c:476-477`, the **only** call site of `rtl819x_ext_advance()` is inside `rtl819x_tc_read_proc` and guarded by `armed`, so **`tc1_ext` is a sum over the intervals somebody happened to read `/proc` in, not an extension of the counter** — 量, `TM-5c`, 462 s with no reader: `tc1_cycles=98,840,142` against `tc1_ext=6,477,776`, `trusted` **1**. ~~Both fixes are `R5-3`'s.~~ 🟢 **2026-09-04 (`R5-3a`): both are written.** `tc1_ext_trusted` is decided in **jiffies** now (`Δjiffies < period_jiffies`, which is the owner's `Δjiffies × TICK_NSEC` rule with both sides divided by `TICK_NSEC`), and `tc1_ext` is advanced by a `timer_list` at a quarter of a period plus by the interrupt handler. 🔴 **This row does not close**: nothing of version 2.0 has executed, and the cell that closes it is `TI-3` on `bench/2026-09-04/PREDICTIONS-B10-block9.md` 🟢 **— and it ran. Version 2.0 executed; both fixes are confirmed on silicon.** `tc1_ext_trusted` is decided in jiffies and reports **0** at period 8, correctly: `gap_max_j = 1` against `period_jiffies = 0`, so a 255-count mask sampled every 10 ms cannot be trusted and the driver says so — the defect that used to report `1` on an aliased gap now reports 0 on an aliased configuration. At period 12 and 20 it reports **1** with `gap_max_j = 1` under a `period_jiffies` of 2 and 524. And `tc1_ext` is advanced with **nobody reading `/proc`**: `TI-3` slept 8 s and returned `tc1_ext_ticks = 66`, `tc1_ext` within 0.018 % of `Δjiffies × hz_used` over 87 s. *(This clause is kept rather than deleted: it named the cell that would close it, and the cell is what closed it.)*. ⚠️ `R5-3` was split on the same day into `R5-3a` (the interrupt path) and `R5-3b` (clockevent and the rating); these fixes ride the `R5-3a` image. 🔴 **2026-09-08, seating 17: a SIXTH narrowing is due, and this time the dependence is of a kind none of the five above describes.** `rtl819x-wdt`'s `BOOTGUARD` arms the hardware watchdog at `late_initcall` and feeds it from a kernel timer, so **from that instant the board reboots unless code of mine keeps running.** That is not "the system uses my peripheral"; it is "the system does not survive my peripheral stopping", which is a strictly stronger dependence than the tick — the tick could in principle be handed back, and this cannot without a `stop`. 量: nine bites this seating, every one confirmed by the loader's own `Reboot Result from Watchdog Timeout!`, and `R2-SO3`/`R2-SO6` show the board resetting on schedule when the feed is deliberately starved **with the vendor's wlan driver up**, so nothing else is feeding it. ⚠️ **What is still true and is narrower again**: the **clocksource** half remains untouched (`rating` 0 in every dump of this seating too), and the watchdog carries no *data* — the network still runs entirely on Realtek's code, so `R6` is unchanged as the gate that moves this row's second column. ⚠️ And the dependence is **opt-out by design**: `bootguard=0` as a module parameter, or `stop` on `/proc`, returns the board to a state where nothing of mine can reset it — which is why this is recorded as a narrowing and not as `R6` arriving early. 🔄 **2026-09-09, seating 18: the dependence now has a USERSPACE arm, and one clause of this row went unmeasured for the first time.** 🟢 `C5-UB` held `/dev/watchdog` open with `sleep 400 > /dev/watchdog` and the board reset **143.563 s** later, against 60 s of `soft_timeout` plus the derived `OVSEL` 9 period — **−0.22 %**. So the documented Linux watchdog contract runs end to end on this part: an `open()` moves the driver to `WDT_USER`, the soft deadline stops the kick, and the hardware resets the board. 🟢 **And the evidence is a CONSEQUENCE, not a field**: `BOOTGUARD` is fed every 250 ms and can never bite, so a reset at that moment is the state change itself. The `state` field was never read while the device was held. 🔴 **What this row asserts and this seating did NOT measure**: *`rating` reads 0 in every dump*. No cell on seating 18's card dumps the timer's `/proc` at all — the card's own § 6 makes the claim and nothing tests it, which is the second claim-without-a-cell that seating found in its own card. What IS measured is `/proc/interrupts` at `OFF-IRQ`: `25: 2412 ICTL rtl819x-timer` against the vendor's `13: 2444`, so the clockevent is live and driving the tick — but that is the TICK half, and the clocksource half is **carried forward from seating 17 rather than re-measured**. `bench/2026-09-09/CORRECTIONS-block15.md` § 1.6 names the same shape for `n_writes`. | `R3`'s D5 — a `ping` with four replies, confirmed on the host's own capture in both directions — went out through the **vendor's** `rtl819x` driver, in the vendor's own configuration. A kernel of mine boots and reaches userspace; every peripheral it touches is Realtek's code. **`R6` is the gate that changes this sentence, and `R3` must not be read as having changed it.** |
| 🆕 **2026-09-06, seating 15 (`R5-4`): a second driver of mine ran on the die, and it establishes LESS than the timer did — deliberately.** | 🟢 `rtl819x-gpio` registered a `gpio_chip` at `subsys_initcall` on **ten boots**, `gpiochip_add()` returning 0 every time, ten boot captures **byte-identical** at 1,184 bytes, and `n_writes` **0** in every dump of the seating. 🟢 Its guard refused on the silicon at two layers with two errnos — `-EPERM` from `.direction_output` and `-ENODEV` from `.request` — with all three register XORs `00000000`. 🔴 **What it does NOT establish, and none of it is a surprise because the card said all five before the board was powered**: which port letter bit 5 belongs to (so the `.dts` node and the binding `R5`'s DoD asks for still cannot be written); whether bits 2, 4 and 6 are usable (the vendor treats them as GPIO, this driver refuses them on purpose); **any output at all** — `RTL819X_GPIO_ALLOW_OUT_MASK` is `0` and no cell changed it; and any GPIO interrupt — `.to_irq` is `NULL`. ⚠️ **The line it would use is already written down and was not touched**: `GPIO_ABCD` is bit 16 of the global controller (`docs/interrupt-map.md`), so what is missing is the work, not the address. ⚠️ **Nothing depends on this chip.** No consumer is bound to it; `R5-7` (leds-gpio) and `R5-8` (gpio-keys) are the steps that would change that, and `R5-4` must not be read as having done it. 🟢 **2026-09-10: still true, and this row is the THIRD owner file that had `R5-7`'s driver right.** 🔄 **2026-09-16 (`P1-0`): this said `config/rlxfw-kernel.delta:82` and this row both say `leds-gpio`, and 量 that was FALSE WHEN IT WAS WRITTEN.** That row calls it `LEDS_GPIO` — the Kconfig symbol, appearing incidentally inside a `CONFIG_GENERIC_GPIO` row — and `notes/gpio-driver.md:622` says exactly that while this file did not. 量: the string `leds-gpio` did not appear **anywhere** in that file until `710119f` at **08:30:57**, which is **5 h 28 min after** `d64ee2f` committed this sentence at **03:02:37** on the same day. 🔴 **`citecheck`'s baseline had it recorded as ordinary rot** — content that moved — and that is what hid the fact that it never pointed at what the prose claimed. It surfaced only because an unrelated edit to this line in the segment's own commit moved its blame, `C4` fired on the now-stale baseline row, and chasing THAT found this. **The laundering incident produced a better finding than the thing it hid.** `config/rlxfw-kernel.delta:174-177` and this row both say `leds-gpio`; `PROGRESS.md`, `docs/bringup.md` and `notes/device-tree.md` said `leds-rtl819x` — **six sites in three files**, 量 by a repo-wide grep at closeout after the write-up had already claimed there were two — and all six were amended. ~~⚠️ **`ALLOW_OUT_MASK` is still `0` on `main` and on every artefact that has ever run** — `R5-7`'s risk argument (`notes/gpio-driver.md`) decides to open it for bit 6 and no line of that change is written yet, so **nothing in this paragraph has moved**.~~ 🔄 **2026-09-10 (fifty-third segment): the first half expired and the second did not, and the difference is the whole of what this row is for.** `rtl819x-gpio` **1.1** is on `main` with `ALLOW_OUT_MASK = (1u << 6)` and `KNOWN_MASK = 0x60`, built as image `r58` (`RECIPE_ID` `083b1cb8`) — 量, `direction_output` goes **112 → 552 bytes** and gains **two** `lui …,0xb800` where `r57` had none, so the write path is in the artefact and not only in the source. ~~⚠️ **But `0` is still true of every artefact that has ever RUN**: `r58` has not been on the silicon, no seating has taken place, and `n_writes` has never been read as anything but 0 on this device. ⚠️ **And *nothing depends on this chip* is still true too** — the `platform_device` that would bind `leds-gpio` is in the same image and has never probed, so the sentence four clauses above stands unchanged until a seating moves it.~~ 🔄 **2026-09-10, seating 20: BOTH of those expired, and what replaces them is narrower in a way worth stating precisely.** 量, image `r59` (`RECIPE_ID` `692a2801`), seventeen boots: `allow_out_mask` reads **`00000040`** in every dump, `n_writes` reads **2** at rest and **4** at the end of the LED boot, and every one of the four is accounted for (two from `leds-gpio`'s `gpio_direction_output(6, 1)` at probe, two from `.set`). **So `ALLOW_OUT_MASK` is `1u << 6` on an artefact that has run, and this chip has written a register on this die.** 🟢 **And two consumers are bound**: upstream's `leds-gpio` holds line 6 and `rtl819x-keys` holds line 5, both through `gpio_request` — `n_req_ok` reads **2** at rest on every boot, and the guard was exercised in *both* directions (`C11-L1` lights it, `lock 6` refuses the next write with `n_writes` unmoved, `unlock 6` lets it through). 🔴 **What is still true and is now the narrower claim this row keeps**: *nothing the system needs* depends on this chip. The LED is an indicator that no code reads back; the button is polled by a device whose events nothing in this image consumes 🔄 **2026-09-16 (`P1-0`): this cited `FW-46`, which is the row about `dd`/`md5sum`/`--list` being absent and says nothing about input events — a 推 claim wearing a 量 row's id, and it violates that row's own ⚠️ that a card may not guess whether an applet exists. The claim is right and now has a source: 量 `FW-83`, the image's whole invocable vocabulary is 50 applets and 40 ash builtins and none of them decodes an input event, and 量 `config/rlxfw-initramfs.tsv` declares seven files**); and `.to_irq` is still `NULL`, so no interrupt path passes through it. **A consumer being bound and the system depending on it are two different sentences, and only the first one moved.** 🔴 **The clocksource half of the row above is still untouched** — `rating` read 0 again and the system's time SOURCE is still `jiffies`. 🔴 **The clocksource half of the row above is still untouched** — `rating` read 0 again and the system's time SOURCE is still `jiffies`. |
| 🆕 **The vendor's factory-reset path is now READ and partly measured, and that narrows a safety question rather than closing it.** | 🟢 量/讀 2026-09-06: in **Linux**, holding the reset button runs `rtl_gpio_timer` once a second; a 2–4 s hold sends SIGTERM to PID 1 (which this image's PID 1 ignores — `FW-37`) and a **≥ 5 s hold writes ASCII `'1'` into `default_flag`**, which in this image has exactly two readers and both are `/proc` handlers. Confirmed on the die: `/proc/load_default` read `0`, then `1` after a timed hold. **So the kernel does not write flash on this path; the vendor's userspace would, and this image has none.** `SPEC.md` `FW-40`. 🔴 **This says nothing about the LOADER**, which is where `R5-4`'s card drew its line and where a factory reset would actually be a flash write. That question is open and untouched. 🔴 **And no `FLR` bracket ran this seating**, so the flash claim did not move: still 1,024 of 4,194,304 bytes, 0.0244 %. ⚠️ Seven of the nine functions that touch `PABCD_DAT` — `autoconfig_gpio_init`, `autoconfig_gpio_off`, `autoconfig_gpio_on`, `autoconfig_gpio_blink`, `autoconfig_gpio_slow_blink`, `read_proc` and `rf_switch_read_proc` — were **seen and not read** (🔴 *this said TWO, from a count taken over five of eleven resolved addresses*), and `sys_bonding_type()`, the gate on the whole button path in *both* the loader and this kernel, is not understood by anything here. 🟢 **2026-09-10 (`R5-7`'s desk half): that count was re-derived by tool and THIS FILE WAS THE HALF THAT WAS RIGHT.** `tools/regcensus.py` on `r57`, attributing every materialisation to a `System.map` symbol without disassembling any of them: **9 symbols, and the seven named above are exactly the unread ones.** `docs/blind-write-ledger.md` § 4.9 said *"three of them were actually read"* and named `rtl_gpio_init` as the third — but `rtl_gpio_init` is not one of the nine (it materialises the block base and `PABCD_DIR`, never `PABCD_DAT`, which is what `REG-35`'s own reading of it says). **Two files disagreed and this one had it.** 🔴 **And `R5-7` has decided to leave the seven unread**, on the ledger § 6 principle that the reading is available later and the blindness is not — the trade, its number, and the runtime instrument that replaces it are in `notes/gpio-driver.md` § 5–§ 6. |
| 🆕 **2026-09-10 (`R5-12`): all four drivers compile against the current longterm kernel, and NONE of them has ever been built into a 6.18 kernel, let alone run on one.** | 量: `rtl819x-timer` / `-gpio` / `-spi` / `-wdt` each reach `rc 0`, 0 errors and 0 warnings against **6.18.50**, producing 37,300 / 11,512 / 27,572 / 22,696-byte `elf32-tradbigmips` objects. **What that is:** four `.o` files. **What it is not:** a kernel, a boot, or a device. There is no 6.18 kernel on this part and there will not be one inside `R5` — the part boots the vendor's 2.6.30 and everything measured on the silicon was measured there. 🔴 **Nor is compiling upstream acceptance**, which is what `D1` actually asks for: three of the four would be rejected on sight — the watchdog is a hand-rolled `miscdevice` where a modern driver registers a `watchdog_device`, the gpio chip has no `of_node`/`fwnode` and is not a `platform_driver` bound through the `dt/` bindings this project already wrote, and every one of them carries a `/proc` file that upstream would want in debugfs or nowhere. ⚠️ **And the port's own cost figure is a floor**, by two measured mechanisms — see `notes/modern-kernel-port.md` § 9.4. | 
| 🔴 **No userspace of mine.** | The initramfs is built from **this unit's own extracted rootfs** — busybox, uClibc, and the symlinks around them are the vendor's binaries, declared one row at a time in `config/rlxfw-initramfs.tsv` with an owner per row. That is deliberate (`R3`'s Decision B: if the shell does not come up, the shell is not the new thing) and it means nothing in userspace is mine. `R7`. 🔄 **2026-09-15: two clauses of this row are now FALSE and the headline survives only in a narrower form.** The declaration carries a second `rlxfw` `file` row — `/bin/uprobe`, built from `config/rlxfw-user/isaprobe/uprobe.c`, not carved from the dump — so the image is no longer built *only* from this unit's rootfs, and something in userspace IS mine. **What survives is: nothing of mine has RUN in userspace ON THE DIE.** uprobe has executed only under `qemu-mips-static`; the image that carries it has never booted; and `/init` does not exec it, so `R3`'s Decision B — if the shell does not come up, the shell is not the new thing — is untouched. `notes/userspace-probe.md`. |
| ⚠️ **Nothing has been written to flash, and that is a weaker sentence than it sounds.** | See the next section. |

---

## 🔴 Every per-`-march` claim here is about ONE toolchain, and until 2026-09-13 none of them said which

| | |
|---|---|
| 🆕 **The vendor assembler's per-core ISA table is not *the* vendor assembler's.** 量 2026-09-13 (`R1-pub-0b`), four `isa-probe.sh` runs under the vendor tripwire: the two `rsdk-1.3.6` releases agree in **160 of 160** cells, and `rsdk-1.5.5` does not. Its `as` (binutils 2.19.92) answers `Error: Bad value (lx4180) for -march` for two of the six spellings — taking the numeric `4180`/`5280` for the same cores — and over the six columns the two generations share it differs in **2 of 120**, both `jalx` at `mips1` and `mips2`. `notes/vendor-kernel-isa.md` § 6's committed matrix reproduces exactly, and it is `rsdk-1.3.6-4181`'s: `isa-probe.sh` picks the OLDEST release, because its search is a plain glob, and its docstring said *newest* until this segment. **So `TC-13`, `CPU-12`, `CPU-44` and every other row that quotes an assembler column are rows about a named release**, and the rows now name it. `SPEC.md` `TC-48`, `docs/toolchain-prior-art.md` § 9 | 量 2026-09-13 |
| **What changes it** | reading stock `opcodes/mips-opc.c` for binutils 2.16.94 and 2.19.92 side by side, which attributes the `jalx` difference; and `R1-pub-6`, which builds the three-column table these readings are the first column of |
| ⚠️ **The `jalx` difference is UNATTRIBUTED.** Nothing here separates a Lexra-patch change from an upstream binutils change between 2.16.94 and 2.19.92. Reading stock `opcodes/mips-opc.c` for both versions is the experiment that would, and it has not been done. 🔄 **2026-09-13 (`R1-pub-6`): two of the three candidate explanations are measured OUT and the named experiment is the one that is left.** ① 量: the public Lexra binutils-2.24 patch contains **zero** `jalx` lines — not added, not removed, not even as context — against **917** added lines across **14** files, with `movz` as the positive control (present, on an opcode-table line, gaining `RLXB`) and a nonsense mnemonic as the negative. **So the public patch did not do it.** ② 讀, upstream: the binutils change to `jalx`'s opcode membership is Catherine Moore's, **May 2010**, `I16` → `I1` — *after* 2.19.92.20091006 and in the **permissive** direction, so it cannot explain a 2.16.94 that accepts and a 2.19.92 that rejects. **What is left is Realtek's own patch to those two binutils versions, and neither is on this disk.** **Neither generation's answer is evidence about the die** — every cell in that table is a statement about an opcode table, which § 6 says in its own words | ⚠️ 推 |
| ⚠️ **`R2c`'s most relevant column cannot be filled by any toolchain on this disk.** `rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225` is the release whose generation built this unit's firmware and whose `-march` this board needs. All three GPL drops' `users/Makefile` name it; none ships it. `SPEC.md` `TC-20`, `TC-01` | 量 — grep over three drops |

## The flash claim, and why it is not "zero bytes written"

| | |
|---|---|
| 🟢 **2026-09-01: the bracket now also says a scripted reset writes nothing to those windows, and that is a sentence `R4`'s unattended loop leans on.** | Seating 9 ran the four windows after one cold boot and **twenty watchdog resets**, with four RAM destinations no `FLR` in this project had ever used — so `MEM-17`'s retention path could not pre-fill them with the answer, which is what voided seating 8's cycle 6. Fourteen comparisons, all as predicted: four read-backs equal to the reference, four pre-reads differing, two positive controls. 🔴 **The percentage did not move: still 0.0244 %, still 6.3 % of `H601`, still no full re-dump.** |
| 🟢 **2026-09-09 (seating 19): the bracket was used on an ACTION for the first time, and the action is the one this repository has most reason to fear.** | `C1-M0` ran before any press and `C1-M1` after a reset-button hold that crossed the vendor's factory-reset threshold — `/proc/load_default` moved `0` → `1` from that same press — **same boot, no reboot between them**, identical over all 32 group digests. **A hold that arms the factory-reset flag, under rlxfw, wrote nothing to 4,186,112 of the 4,194,304 bytes.** ⚠️ It says nothing about the vendor firmware, where that gesture reaches a userspace that does write flash; this seating never booted it. 🔴 And the comparison method itself had to be narrowed to say this at all — `notes/flash-digest-scope.md` § 10 |
| 🔴 **"No flash-write command was issued" is not "not one flash byte is written".** | `RUNSHEET` `G8b` forbids the second without a full re-dump hashed against `FLS-14`, and no seating has run one. What exists is a bracket: four 256-byte windows read back before and after, over two power cycles. |
| 量 **The bracket reaches 1,024 of 4,194,304 bytes — 0.0244 %.** | All byte-identical to the 2026-08-16 reference dump. It **cannot** see a write outside those four windows, and it cannot see two writes that cancel. |
| 量 **`H601` — this unit's MAC and radio calibration, the region a wrong write cannot be undone in — is covered to 512 of 8,192 bytes: 6.3 %.** | The other 93.7 % is unchecked **by this project's `FLR` bracket**, and the qualifier is the whole sentence. 🔄 **2026-09-07 (fortieth segment): without it this row says of the DEVICE what is only true of the BRACKET** — `SPEC.md` `FLS-25` compared the full 8,192 bytes against the reference dump six times over 2026-08-17..19 and found **zero** differing bytes. ⚠️ **That does not move the 6.3 %**: those six re-reads are one instrument, they are upstream-era artefacts predating rlxfw's first power-up, and none of them is an `FLR` bracket read at a seating. 🔴 **`CLAUDE.md` already made exactly this correction for exactly this region on 2026-08-30** (*true of rlxfw's own bracket, false about the device*) and this sibling row never received it. This region is why the project is zero-write through `R9`. |
| 🟢 **The bracket does have a negative control.** | Every destination is read **before** its `FLR`; on the round that established this, all eight pre-reads differed from the expectation, so *the `FLR` wrote* is measured rather than assumed. One earlier round was **voided** by that control when DRAM retained a previous cycle's contents across a power cycle. |
| 🔴 **2026-09-08 (seating 16): the sentence above is now known to be FALSE for the DEVICE, and that is worse than unmeasured.** | `SPEC.md` `FLS-26`. `rtl819x-spi` digested `H601`'s complement on the silicon — `digest_bytes 4186112`, `h601_hashed 0`, over a traversal of all **4194304** bytes — and got `a1673578…100d49eb` where `FLS-24` says `a9916fd8…4ce3cba`. **The constant is not the thing that is wrong**: the same range recomputed at the desk from **both** dump files by an independent implementation gives `a9916fd8…` exactly. So flash content has moved since 2026-08-16. 🔴 **Attribution is not established and this seating could not narrow it** — it was not tonight (loader straight to my image on all ten boots, no vendor firmware, `n_writes 0` in every dump, no `FLW`/`EW`/`EB`/burn issued), and the vendor firmware *has* run on this part since the dump, but that is a hypothesis with a mechanism, not a measurement. 🔄 2026-09-26: the `n_writes 0` clause carries no information — no committed `rtl819x-spi` increments the counter (`FW-142`, `notes/spi-mtd-driver.md` § 11.6). |
| 🟢 **And the one region that matters most is now proven intact over all of it, not sampled.** | `verify 32768` covers exactly `[0, 0x6000)` — the whole loader region, **24,576** bytes — and it is byte-identical to the 2026-08-16 dump. Every `FLR` bracket in this project combined had sampled **256** of those. The first difference is `[0x9000, 0xA000)`: **4096** bytes, exactly one erase sector, above `H601` in `mtd0`'s `"boot+cfg+linux"`. |
| 🔄 **2026-09-08 (forty-fourth segment): the driver's limit is lifted and the coverage figures are unchanged, which is the point.** | `rtl819x-spi` 1.1 adds `verify <n> <off>` and a two-level `map` (32 x 32 = 1024), and `tools/flashmap.py` computes the expectation from the dump so every line can be carded before power. **It has read nothing**: the scope decision is that these verbs ride on `R5-6`'s image. So the row below stands in every digit. |
| 🔴 **Coverage is still the binding limit, and it is now limited by the DRIVER rather than by the bracket.** | Proven identical **28,672** bytes (0.684 %); proven different **4096** (0.098 %); **undetermined 4,153,344 (99.02 %)**; never hashed by rule 8,192 (0.195 %). Prefix digests find the *first* difference and nothing past it, and `verify` takes a limit with **no offset** (`rtl819x-spi.c:845`). ~~Whether anything above `0xA000` also moved cannot be settled by this image.~~ 🟢🟢 **SETTLED, and the whole row's arithmetic is superseded — 2026-09-08 (seating 17) and 2026-09-09 (seating 18).** The way out was not `verify` but `rtl819x-spi` 1.1's two-level `map`: `map 0` says 31 of 32 groups are byte-identical to the 2026-08-16 dump, and `map 1 0` splits the remaining group into 32 units of 4,096 — **30 same, 2 DIFFER**. So **proven identical 28,672 → 4,177,920 B (99.61 %)**, **proven different 4,096 → 8,192 B (0.195 %)**, **undetermined 4,153,344 → 8,192 B (0.195 %) — and that is exactly `H601`**, never hashed by rule rather than for want of an instrument, so the old *never hashed by rule 8,192* column and the *undetermined* column are now the same 8,192 bytes. 🔴 The differing region GREW: the second unit is `[0xD000,0xE000)` and nothing had ever seen it, because a prefix digest finds the first difference and nothing past it — so the *one erase sector* in the row above was never checked, only never contradicted. `notes/flash-digest-scope.md` § 10 owns the arithmetic. |

---

## The reproducible build closes at one machine

| | |
|---|---|
| 🔴 **`P4a` is closed at Level 1: same machine, same tree, built twice. A third party rebuilding the published recipe will NOT get the same sha256.** | 讀 2026-09-01: this drop's `scripts/mkcompile_h` has no `KBUILD_BUILD_USER` and no `KBUILD_BUILD_HOST` (those arrived in mainline after 2.6.30). It writes `LINUX_COMPILE_BY` from `` `whoami` `` and `LINUX_COMPILE_HOST` from `` `hostname` ``, so the banner carries this workstation's identity and the image carries the banner. |
| ⚠️ **The other six candidates for the same problem split three ways, and are listed so the residual is one item rather than a worry.** | **Three were measured or read away**: `LINUX_COMPILER` is `"gcc version 3.4.6-1.3.6"` and carries no build path (讀); the image holds **0** hits for `/home/key`, `r3-4` or `cells/` (量); the initramfs entries' mtimes are declared, ~~all 31 of them~~ 🔄 **all 36 of them, 量 2026-09-15**. **One is untestable on this host**: `locale -a` returns `C`, `C.utf8` and `POSIX` and nothing else, so no run-time case here can distinguish a driver that pins `LC_ALL` from one that does not — the driver pins it and the assertion is on the source text, which is weaker and says so. 🔄 **2026-09-01, later the same day: ONE stays unmeasured** — kbuild's link order against `readdir`. `.version` under `--keep` was measured by `R4-0`: a fresh cell links once and reads `1`, the same tree after two `--keep` builds reads `3`, and the two images differ in **2 bytes of 3,968,240** — the `#1` against `#3` in `linux_banner` and `init_uts_ns`, and nowhere else (`SPEC.md` `TC-42`, `notes/dev-loop.md` §5.1). 🔄 **2026-09-02: two bytes is the cost of a DIGIT, not of the counter, and this row published it as a bound.** 量, a ladder of consecutive links from one tree: `#7→#8`, `#8→#9` and `#10→#11` each differ in **2** bytes; **`#9→#10` differs in 56**, adding a `.symtab` byte, because the decimal rendering widens and shifts `UTS_VERSION` in both of its copies. The CLAIM is unchanged — `--keep` does break byte-identity — and the SENTENCE was wrong from the tenth link on. `notes/incremental-build.md` §5.5. *(This read "Two stay unmeasured", and it was the third number in this row to need re-deriving rather than re-reading.)* 🔄 **2026-09-01: this row said *five … were measured or read away* and then listed four things, one of which (`LINUX_COMPILE_TIME`) is not one of the seven, while the `LC_ALL` row was named nowhere.** It was copied from `notes/reproducible-build.md` §6, whose own summary was wrong the same way; both were corrected by re-deriving the count off the table rather than by any checker. `notes/reproducible-build.md` §6. |
| 🔴 **`P4a`'s own definition of done is wrong as written, and the gate closed with it recorded rather than repaired.** | The gate board says *"with the positive control that changing one source byte changes it"*. 量: one byte of a string literal changes the sha256; one byte inside a **comment** in the same file leaves it byte-identical. The wording needs *that reaches the image*. The second outcome was predicted before it was run, because a control that can only come out one way is not a control. |
| ⚠️ **Every sha256 recorded for a build belongs to a recipe id and has to be quoted with one.** | `RLXFW_SRC_ID` is a sha256 over `config/` **as bytes**, comments included, so a typo fix in a declaration produces a different image. That is the design — the image's identity tracks the declaration exactly — and the cost is that two images are not comparable across a documentation-only commit. |

---

## Gates that closed with a defect recorded

| | |
|---|---|
| 🔴 **`R3`'s D3 had no observable.** | The written criterion for *early bring-up completes* was the string `MemTotal:`, which **this kernel never prints in any configuration** — it is a `/proc/meminfo` field, not a boot message. The row passed on a substitute (the eleven boot marks, which are discriminators checked in the image before the seating). A DoD whose observable does not exist is a defect in the DoD and is recorded as one. |
| ⚠️ **`R3-2`'s `TC-d` half stayed half-done for one step.** | It is carried as a debt in the running-order note rather than counted as a pass. |
| ⚠️ **`R1h`'s decision ② is still `R1-gate`'s.** | It was answered on the D side by a bare-metal payload, and not by the gate that owned it. |
| 🔴 **`R5`'s `D4` named an artefact that cannot carry the property, and it is the THIRD time.** | The row asked that *the timer is the system time base and `/proc/timer_list` agrees with `CLK-02` to ± 50 ppm*. `/proc/timer_list` **exists in this kernel** — 讀, `kernel/time/Makefile` carries `obj-y += … timer_list.o` and `timer_list.c` calls `proc_create("timer_list", …)` — and it was never read: `R5-2` used the driver's own `/proc`, which carries both counters inside one `spin_lock_irqsave`, and recorded why in place. **Nor is it a frequency**: `wall`, `jiffies` and TC1 all descend from one divider, so what is 量 is the ratio `TC1 : tick = 2000 : 1` and the absolute 200.005 kHz stays 推. With `R3`'s `D3` (`MemTotal:`) and `P4b-gate`'s `D2` (`study/weekly-results.md`) that is three of eight gates — and they sit at entries 4, 6 and 8, so `docs/GATE-RESULTS.md`'s operating clause, which reads *consecutive*, still cannot see the pattern. 🔴 **A census of all 17 gate-level DoD rows was run at `R5-11` with its refutation condition written first — *a fourth instance nobody already knows about buys an enforcer; only the known three means an instrument fitted to three points should not exist* — and it returned the three. No enforcer was written.** |
| 🔴 **`R1-pub-3`'s control clause is not met, and the instrument that should have said so could not be asked.** | *Every hazard test's own control fires* reads **21 of 24**: three `cp0` rows' per-row `ctl` control did not fire. Those rows are `VOID` and `D3` permits that, but the clause says *every*. `hazpay`'s `check_controls` inspected **2 of 26** declared controls and the probe's own `aux.zero` header field was blind to the same three rows for an unrelated reason — it tests *equal to zero* and the wrong value was `0x80500270`. Both were fixed in the segment that closed the gate; **the clause is still not met, it is merely measurable now.** `SPEC.md` `FW-76`, `docs/isa-hazard.md` § 6 |
| 🔴🔴 **`R1-pub`'s `D-cost` `E5` is a conjunction and every adjudication of it quoted one conjunct.** | `Δirq_count == Δjiffies` on every rung fails **5 of 64**, all five one-sided, and counting both conjuncts as the sentence is written takes boot 1 to **31.2 %** against that clause's own ¼ void threshold. 🟢 The four costs do not move and the reason is structural: the ruler is `comp_tc1`, `Δirq` is not in it, and both of its terms are snapshotted inside one lock — readable with no reference to the outcome. 🔴 The clause put two properties under one threshold and only one bears on what the threshold protects. `SPEC.md` `FW-75` |
| ⚠️ **`R1-pub`'s `R2c` half fired a stop-loss whose remedy is impossible, and got no decision.** | The plan caps `R2c` at 2 段; charged three defensible ways it spent 1, 2, or 3–4. The prescribed remedy — drop the third toolchain and ship two columns — cannot be applied, because all three columns are already on silicon. Nothing in this repository counts the segments, and the gate closed with the count recorded three ways rather than with the flattering one taken |
---

## The artefacts

| | |
|---|---|
| ⚠️ **The 60-second take is a REPLAY, not a live recording.** | It is seven committed serial captures replayed at true wire speed by `tools/replay-capture.py reel config/r3-11-reel.tsv`. `plan/ARTIFACTS.md` §2's v0.2 row describes a live power-up. The replay is reproducible by anyone who clones this repository, which a recording is not — but it is not a recording of the board, and the video says so. |
| 🔴 **The `v0.2` release ships no image, and that is deliberate.** | 量: the release has **0 assets**. Three reasons, each checkable rather than a preference. **① GPL.** The kernel is a derivative of Realtek's GPL source, so distributing the binary carries the corresponding-source obligation — and `P4b` (corresponding source, a written offer, a per-file modification record) is on the gate board at **v1.0** and is not started. Publishing the binary now would create an obligation this project cannot currently meet. **② It is not all mine to publish.** 量 `config/rlxfw-initramfs.tsv`: ~~**four of the five `file` entries are `owner=unit`**~~ 🔄 **量 2026-09-15: four of SIX, and TWO are mine** — this count was exactly right until the seventy-second segment added `/bin/uprobe`. The conclusion is unchanged and holds on four of six: — `/bin/busybox`, `/lib/libuClibc-0.9.30.3.so`, `/lib/ld-uClibc-0.9.30.3.so` and `/lib/libgcc_s.so.1`, all carved out of this device's own flash dump. Only `/init` is mine. Shipping the image ships the vendor's userspace. **③ It would not help anyone check anything.** `P4a` closes at Level 1, so a third party rebuilding the published recipe does not get this hash — a published binary could not be verified against the published source, which is the only reason to publish one. Level 2 is what would change that. ⚠️ What IS published is what can be checked: the seven captures the take is made of, every declaration the build reads, and the tools with their controls. |
| ⚠️ **The take is PUBLIC where the project's own plan asked for unlisted.** | `plan/ARTIFACTS.md` §2 specifies an unlisted link. The owner ruled otherwise on 2026-09-01, so it is a departure from the plan rather than an oversight. 🟢 **The containment check is the same either way and it was run before the recording**: `flashwin scan` reports CLEAN on all seven segments against this unit's reference dump, and a MAC-shaped sweep returns 0 — so nothing in the frames identifies the device beyond what this repository already publishes. |
| 🔴 **It measures 62.2 s against a 60 s spec, and the gate that checks the length cannot see it.** | 量 2026-09-01, three runs: **62.246 / 62.235 / 62.310 s** (range 0.075 s) against a computed 59.749 s. `replay-capture`'s `R16` asserts on capture-plus-pause; a stopwatch measures the replay, and the difference is ~0.065–0.14 s of fixed cost per segment plus **1.461 s in one 33 s segment** whose 2,339 timing records each pay ~0.62 ms of `sleep` granularity. **The pause column was not trimmed to fit** — that is what `config/r3-11-reel.tsv`'s own rule forbids. Open: whether `R16` should measure wall time (which would make it host-dependent, and therefore a bad CI case) or whether the ceiling should move. |

---

## The repository's own record

| | |
|---|---|
| 🔄 **TWENTY CI runs in this repository's history are red. All twenty have a diagnosis, and sixteen of them are one class.** | 量 2026-09-01, `gh run list --limit 300` returns **65** rows — fewer than the limit, so this is the population and not a window — **47 success, 18 failure**, spanning 2026-08-28 to 2026-08-31. Every one of the eighteen was read from its own `--log-failed` on 2026-09-01 and lands in exactly one of four classes, with no remainder. **① The census table and what it describes drift apart — 7 runs.** `tools/ci-expected.tsv` holds a per-suite case count; a suite grows and the table does not follow, so `ci-census` reports `CENSUS-MISMATCH` (`17a02dd` kconfig-delta 24/22 and mkinitramfs 23/19, `33d3482` rbcheck 16/10, `50eebce`/`4a9ce38`/`8d26e52` test-rbcheck 31/29, `195ae3d` test-rlxprobe 0/206) or, once, the reverse — `0353d40`, a suite in the table that was never added to the workflow, so it produced no output at all. **② A hardcoded population inside a case — 4 runs.** `test-boot-timeline`'s `B2` asserts a literal *N cold, M warm* against the captures under `bench/`, so a seating turns it red (`3b3bb87` *eight cold, eight warm*; `af8360d`/`b9a1bf2`/`19926fc` *ten cold, nine warm*). **③ A case that runs on the author's machine and skips on the runner, so its label is never compared — 5 runs** (`d658f03`, `95895e1`/`5b66938`/`3a10e0c`, `2026e8e`); `PROGRESS.md` `CI-1` owns it. **④ A markdown structural defect `spec-check` catches, pushed past a green local gate — 2 runs** (`2266324` a row not closed with a pipe; `09e1a23` two one-cell rows in a two-column table); `CI-2` owns it. 🔴 **Sixteen of the eighteen — classes ①, ② and ③ — are one shape: a count or a label about the repository's own contents, kept in a second place, invalidated by a change somewhere else.** That is the same class as the row below, and the only difference is that here an instrument exists, so it fails loudly on a push instead of silently forever. ⚠️ **The count of undiagnosed runs this row carried before today was ELEVEN, and eleven was right — reached by two errors of opposite sign that cancel exactly.** It read *17 of 59* and *four of the seventeen are diagnosed*, then named six. 量: (a) the population was 18, not 17 — the run recorded as *1 in flight* was `09e1a23`'s and it concluded **red**, so the number was already wrong about its own stated population rather than merely overtaken; (b) `09e1a23` was counted as diagnosed while excluded from that denominator; and (c) `d658f03` was in the denominator and diagnosed in `CI-1`, and was not counted. 18 − 7 = 11. **A correction that changed eleven to twelve was drafted and withdrawn**: it fixed (a) and (b) and missed (c). **A count is a window in time as well as in rows**, and a run still in flight belongs to neither column. 🔴 **The denominator is deliberately not in this row's headline, and the reason is that it moved while this row was being written.** 量: 65 rows when the class above was measured; **66** twenty minutes later, because the commit carrying this row pushed and went green. A denominator that changes on every push cannot live in a live sentence — it can only live in a dated one, which is what the 量 above is. The numerator is the load-bearing half: eighteen is the thing three previous statements here undercounted. 🔄 **2026-09-06 (thirty-seventh segment): eighteen → TWENTY, and the headline sentence was present tense while the 量 beside it was dated — so the row aged for five days without anything noticing.** 量 today, same command: `gh run list --limit 300` returns **110** rows, **89 success, 20 failure, 1 still running**. The two new ones, both read from their own `--log-failed`, so the *all have a diagnosis* clause stays true rather than being quietly dropped: **① `33849822488`** (2026-09-04, `bd9fecd`) — `CENSUS-MISMATCH: test-tcheck ran 10/9`, a suite that grew by one case while `tools/ci-expected.tsv` did not follow, which is class ① above and takes it from 7 runs to 8. **② `34027603554`** (2026-09-06, `47dfb2a`) — `test-file-modes`, `tools/citime.py` recorded `100644`. It had already been repaired that segment with `git update-index --chmod=+x`, and splitting the work into four commits meant a `git reset`, which discarded that with the rest of the index; the following `git add` re-captured the old mode under `core.fileMode=false`. 🔴 **That is a FIFTH class and it is new here**: not a declaration that drifted, but a repair undone by an unrelated git operation, with the desk's green `test-file-modes` taken BEFORE the reset and therefore saying nothing about the tree that was pushed. ⚠️ **And the denominator moved for the reason this row already gives**: the commit carrying this correction pushes, and pushes make runs. The 110 is dated, like the 65. |
| 🔴 **FIVE CI failures share one shape, across three variables: a case that RUNS on the author's machine prints no skip line, so its label is never compared against the expected-skip table.** | The variable is different every time — `$FWRE_WORK` twice, the **timezone** once — so a rule about any one of them does not close the class. Two partial answers are in place: a case with no branch cannot print an undeclared skip, and a runner can be simulated locally with an empty `$FWRE_WORK`. Neither is complete. `PROGRESS.md` `CI-1`.  🔄 **2026-09-01: three → five, by reading every red run's log rather than the ones this repository happened to have written about.** The three variables are unchanged — `$FWRE_WORK` twice and the timezone once — but the `flashwin` variable accounts for **three** runs (`95895e1`, `5b66938`, `3a10e0c`, all `UNEXPECTED-SKIP "this unit's flash dump"`), not one. ⚠️ **Every one of the five was DETECTED by the census arithmetic**, not by the label check — each carries a `CENSUS-MISMATCH` and a `NOT-RUN-TOTAL MISMATCH` beside the `UNEXPECTED-SKIP`. The thing that catches this class is the sum that has to close, which is the property the workflow header says it is there for. |
| 🔴 **`v0.2` is this repository's first published release, and `v0.0` was tagged and never released.** | 量 2026-09-01: `gh release list` returned nothing before `v0.2` was created. `CHARTER.md` §110 rule 2 — *a release per version, with a CHANGELOG and known issues* — has therefore been unsatisfied since the project's first tag on 2026-08-25, which is wider than the carried-forward row that named the gap. Whether to publish a retrospective `v0.0` release is open. |
| ⚠️ **`v0.1` was never tagged.** | Its contents (`R0`, `rlxprobe` executing on the silicon, `R1-gate`) completed 2026-08-26. Owner's ruling 2026-09-01: not urgent. This release therefore spans `v0.0` → `v0.2`. |
| 🔴 **Four numbers this repository states about ITSELF were wrong on one morning, and nothing here can see the class.** | 量 2026-09-01, all four found by re-deriving a figure against the thing it counts, none by a checker: `PROGRESS.md`'s `P4b-3` said this file had **25 entries** when it had 28 — true when written, broken by three later commits in the same session; this file's CI row said **17 of 59** when its own population was 18 of 59; `notes/reproducible-build.md` §6 said **five of seven** Level-2 rows were settled when three were, and this file copied it. **The shape is constant**: a count about the repository's own contents, load-bearing for nothing in the sentence around it, so nobody re-checks it, and no tool here reads a natural-language number against the artefact it describes. `spec-check` checks `SPEC.md`'s rows against their owner files, which is the same idea one file wide. **Whether the class is worth an instrument has not been measured** — the population of such numbers in committed files is unknown, and measuring it is the first step, not building one.  🟢 **2026-09-01, later the same day: the class now has a measured backing instead of an intuition, and it came from the CI history.** 量, all eighteen red CI runs read from their own logs: **sixteen of the eighteen** are the same shape — a count or a label about the repository's own contents, kept in a second place, invalidated by a change somewhere else. Seven are `tools/ci-expected.tsv`'s per-suite counts against the suites, four are one hardcoded *N cold, M warm* inside `test-boot-timeline`'s `B2` against the captures under `bench/`, five are that table's allowed-skip labels against what a tool actually prints. 🔴 **So the question is no longer whether the class is real. It is why the machine-readable half has an instrument and the prose half has none** — `ci-census` makes this class fail loudly on a push; in prose the identical mistake sits there silently, which is how four of them reached committed files. ⚠️ **The population of prose counts is still unmeasured** and that is still the next step; what changed is that the class is now this repository's single largest recorded source of CI failure. 🔄 **2026-09-14 (sixty-eighth segment): FIVE more instances in one segment, and one of them was repaired a way this repository had not tried before.** 量, all five found while editing for other reasons and none by a checker: `tools/rbcheck.py`'s module docstring said *thirty-one* on a day the column said forty (and had earlier said *ten* when it said sixteen); `run_controls`'s own docstring said *sixteen* when there were forty; `.github/workflows/ci.yml`'s comment beside that suite said *ten controls* and *six of the ten*; `SPEC.md` `CPU-58` said a frozen card misfiled it in *two* places when it is six; and `docs/FINDINGS.md` § stated the ISA census at *3 of 45* after the board had moved it to 42. 🟢 **The repair for the first three was NOT to correct the number.** It was to delete it and name the owner — `tools/ci-expected.tsv` holds the count and `ci-census` compares it against what actually ran — so the prose can no longer go stale because it no longer states the fact. **That is strictly stronger than a correction and it costs nothing**, and it is available to every prose count whose machine-readable owner already exists. ⚠️ It is NOT available where no owner exists, which is most of them, and that is the half the unmeasured population is about. 🔴 **A sixth instance the same segment is a different shape and has no such repair**: `SPEC.md` `CPU-14` cited `docs/isa-hazard.md` § 7.1, a section that does not exist — the warm-cache caveat is § 7's first numbered item. A stale *citation* has no owner table to defer to, and `spec-check`'s `C11` checks payload-source references rather than `FILE § N` written in prose. |
| 🔴 **A gate can be green while the thing it guards is under-declared, and one was.** | 量 2026-09-03: `ledgerscan check` reported *ok* over 32 in-scope paths while `docs/blind-write-ledger.md` declared `kernel/time/jiffies.c` at depth `name` and `ledgerscan scan` read it as `line` — `notes/timer-driver.md:273` cites `:37`. **`check` compares SETS OF PATHS and never looks at the depth column**, and the depth is what separates *saw the interface* from *read the code*, which is the distinction the whole ledger exists to make. The row is corrected; **the checker is not**, and `PROGRESS.md` `LEDGER-2` owns it. ⚠️ The obvious repair is wrong: `scan`'s depth is the maximum observed anywhere in the repository and the ledger's is *what this row says it took*, so a mismatch must be **reported**, not **decided**. |
| ⚠️ **The gate ledger's own operating clause fired on its first run and named a different next gate than the plan.** | `docs/GATE-RESULTS.md`'s rule — two consecutive entries whose *what it did not establish* is the same thing make that thing the next gate — could not run until there were two entries. With five, one consecutive pair shares an item: `R1h` and `R3` both carry `CPU-45` (whether a cached read sees a write the CPU did not make). The plan's next gate is `R4`. **Two caveats are recorded with it**: four of the five entries were written in one sitting after all five gates had closed, so the *selection* of residuals had hindsight even though their contents are dated records; and `CPU-45` already has an owning gate with a second seating allowed, so the clause is reordering a queue rather than finding an orphan. |

---

## 🔴 The image contains a flash-write path, and it is not mine

**量 2026-09-07 (`R5-5`, `FW-44`).** `CONFIG_RTL819X_SPI_FLASH=y`, and
`spi_probe.c`'s `spi_chip_setup()` installs `mtd->write = mtd_spi_write` and
`mtd->erase = mtd_spi_erase` unconditionally. Those reach
`ComSrlCmd_ComWriteData`, `PageWrite_111002` and `ComSrlCmd_SE` — real page
program and sector erase sequences on the SPI controller. They have been in
every image this project has ever built and in the vendor's shipped one.

What keeps them from being reached is the userspace surface, not their absence:
`/dev/mtd0ro` is an odd minor and `mtdchar`'s `mtd_open` refuses it for writing
(`:73`), and `/dev/mtdblock1` is declared `0400` in
`config/rlxfw-initramfs.tsv`. **Those are access controls on a path that
exists.**

🔴 **2026-09-14 (sixty-ninth segment): that access control exists on MY side and
NOT on the vendor's, and the difference is measured.** 讀 `unsquashfs -ll` on
this unit's own shipped image — not on the extracted tree, where `unsquashfs`
without root reports `created 0 devices` and every node reads as absent, which
is a false zero this finding nearly took: `/dev/mtd0`–`/dev/mtd4` ship
`crw-rw-rw-` and **`/dev/mtdblock0`–`3` ship `brw-rw-rw-`, mode 0666**.
`/dev/mtdblock0` covers the **loader and `H601`** — the two windows this
project's own rules call unrecoverable — and `/bin/flash` (87,664 B) sits in the
same `PATH`. 讀 the board config: `# CONFIG_MTD_CHAR is not set`, so the `mtd*`
char nodes are dead (`ENODEV`), but `CONFIG_MTD_BLOCK=y`, so **`mtdblock*` is
live**. ⚠️ **This narrows the section's own sentence rather than contradicting
it**: *the userspace surface is what keeps them unreached* is true of every
image rlxfw builds and **false of the vendor's**, where nothing is in the way
except the absence of a shell. `SPEC.md` `FW-68`; the route that would reach it,
and its own flash-write cost, is `PROGRESS.md`'s `VDR-1`.

🟢 So the sentence `R5-5`'s `D4` earns is **rlxfw contributes no
flash-write code to this image**. It is *not* *this image cannot write flash*,
and no write-up may use the first to imply the second. `rtl819x-spi`'s own
device is stricter than the vendor's partitions — `MTD_CAP_ROM` means
`mtd_open` refuses it at `:94` on **either** minor, where `/dev/mtd0` is an even
minor and passes `:73` — but that is a statement about `mtd2`, not about the
image.

⚠️ And `D4`'s positive control is a control **over stubs**: the write TU's two
entry points return `-EPERM` and contain no SPI transaction, deliberately,
because mainline is zero-write through `R9`.

## What has never been measured at all

🔄 **2026-09-02 (`R5-0`), two rows leave this section and one arrives.**
*Leaving*: the incremental cost of a real edit on a reused tree — **592 `CC` /
32.58 s**, against 3 `CC` for the same edit with `RECIPE_ID` held (`SPEC.md`
`TC-45`); and whether confining `-DRLXFW_SRC_ID` moves the product — it does
not, two fresh stages give a byte-identical `vmlinux` (`TC-46`).
*Arriving*: ✅ ~~🔴 **whether the public RTL8196E ports derive from the vendor's `arch/rlx`.**~~ 🟢 **ANSWERED 2026-09-11 (`R5-9`): they do not, with one file's exception.** The derivation check ran with its ordering constraint intact — pre-registration in `git log` eighty-five seconds before the clone — and read `shibajee` INDEPENDENT on every domain it implements and `ggbruno` DERIVED on `prom.c` alone, four `BSP_` UART macros in the early console path. ⚠️ **It does NOT clear `R5-5`.** That step's independence was already spent on the vendor side by `docs/blind-write-ledger.md` § 4.5, which is a different question from this one and is not touched. `docs/driver-diff.md` § 2.

* 🔴 **Whether an unaligned ACCESS costs an exception on bare metal.**
  `CPU-15` measured the four unaligned *instructions* — `lwl`, `lwr`, `swl`,
  `swr` — executing at the loader prompt, and `CPU-75` measured an unaligned
  *address* costing **915 ns** in Linux user mode. Two states of one machine and
  neither refutes the other. The deciding experiment is timing the same `lwu2`
  at the loader prompt; it needs a payload and a seating.
* 🔴 **Four of the eight instructions on the emulation surface are unpriced**
  — the unaligned `lh`, `lhu`, `sh` and `sw`. `4b` priced `sync`, `lwu2`, `ll`
  and `sc`; `E7` required the number to be in the write-up rather than
  discovered by a reader, and it is (`docs/emulation-surface.md`). The rows are
  still unpriced.
* 🔴 **Two counters read at one instant, through this driver's own `/proc`.**
  Neither `R5` nor `R1-pub` established it — which is what the operating clause
  fires on at nine entries. 讀 `drivers/clocksource/rtl819x-timer.c`:
  `j = get_jiffies_64()` is inside the lock held 1998–2042 and `irq_count` is
  read live at 2147, 105 lines after the unlock. 🟢 Three lines would settle the
  pairing; what it needs after that is a measurement that the five one-sided
  differences go away, and 🔴 **if they do not, the mechanism is something other
  than sampling skew and that is the larger finding** — the gap is symmetric in
  sign and does not predict five same-sign differences in sixty-four rungs.
* ⚠️ **Whether `docs/rlx-isa.md` is readable by someone who did not build it.**
  Every claim in it is *checkable* from a clone — § 9 is that table, and one row
  of it was a promise the page could not keep until the day the gate closed.
  **Checkable and readable-by-an-outsider are different properties and only the
  first is established.** That is a different deliverable and it has no DoD yet.

* ✅ ~~**Whether an interrupt of mine can be delivered at all.**~~
  🟢 **ANSWERED 2026-09-04, seating 12: yes, 119,818 times.** Every one
  of § 3.1's seven gates is now 量, `Status.IM2`/`IEc`/`BEV` included
  (`status = 10000401`) and all four routing registers read in **both**
  states — the loader's `00000000 30050004 00000000 00000000` and
  Linux's `22222222 C222FA2D 2EB29F22 22222022`. `SPEC.md` `IRQ-08`,
  `IRQ-10`, `bench/2026-09-04/CORRECTIONS-block9.md`.
  🔴 **What replaces it is narrower and was not on this list**: a
  pending bit in `TCIR` has a lifetime of at most one 10 ms tick,
  because the vendor's own ack is a read-modify-write on a
  write-1-to-clear register (`SPEC.md` `IRQ-09`). That does not stop
  delivery and it does bound every single-sample reading of that
  register ever taken here.
* ✅ ~~**Whether a DMA write is visible to a cached CPU read.** Nothing has been
  measured in that direction, and it is the one driver decision the cache gate
  closed without.~~ 🟢🟢 **ANSWERED 2026-09-17 (seating 26), and the answer is
  that it is NOT visible: this D-cache holds stale lines after a real bus master
  overwrites the underlying DRAM.** The engine is the switch's CPU-port RX DMA,
  already running at the loader prompt; the treatment is eight broadcast frames;
  two of four buffers read `V1 == V0` with `V2` different, in each of two runs.
  The reading is airtight rather than suggestive because a miss would have
  fetched `V2`, so the line *was* resident — **there is no *it was evicted*
  escape**, which is what every previous attempt lacked.
  `docs/rlx-cache-and-cp0.md` § ⓑ-4.
  🔴 **What is still open, and it is not small**:
  * the D-cache's **write policy** (`CPU-19` 殘留 ①) has **zero** measurements,
    and § ② says why that is decisive for a ring — a ring is a *write hit on a
    resident line*;
  * D-side **line size** and **associativity** have never been measured; the
    量 16-byte / 2-way figures are the **I**-cache, and `v-line`/`v-assoc` have
    never run;
  * **why two of the four buffers read the new value is undetermined** — the
    split is structural, the same two both runs, and the geometry that would
    explain it is the unmeasured one above;
  * the **throughput cost of uncached rings** is unmeasured and is a different
    number (`R6-1` `D5`).
* ✅ ~~**Whether this silicon retires the `cache` instruction.** This unit's own
  vendor kernel contains 37 of them, D side only; none has been executed by
  anything of this project's.~~
  🟢 **ANSWERED 2026-08-29, seating 7, and this bullet had carried the refuted
  sentence for fourteen days.** 量 `bench/2026-08-30/QJ.log`: `probe3`'s Group X
  issued four op values — `0x10` `IInval`, `0x11` `DInval`, `0x15` `DWBInval`,
  `0x19` `DWB` — and every one returned `n=00000000`, with `x ri`'s
  `cause=00000028` (ExcCode 10) in the **same capture on the same boot** as the
  control that makes *no trap* a reading rather than a dead handler. `SPEC.md`
  `CPU-44`, `docs/probe3-cells.md` § Group X.
  🔴 **What survives is narrower and is already written there**: `CPU-44` closes
  on *retires*, not on *invalidates* — `x c10`'s untreated twin moved too, so the
  six intervening `CCTL` stages explain the treated victim as readily as
  `cache 0x10` does.
  ⚠️ **Found by `R1-pub-0`'s census (2026-09-12), not by any gate.** Five checks
  were green over this file the whole time: none of them compares a sentence
  about the future to a capture that has already answered it.
  `docs/isa-prior-art.md` § 3.
* **The pipeline hazards**, which need a controlled loop and a timing harness.
* **What an incremental build of a REAL edit costs on this tree.** 量 2026-09-02
  fixed the reason there was no incremental build at all — a bare `#` truncating
  every `.cmd` file, so kbuild's command comparison could never match — and a
  no-op `make` went from 599 objects and 28.0–32.1 s to 2 and 6.9–10.3 s. But
  **every number taken that day is a no-op or a `touch`**, and touching a file is
  not editing it. A real `R5` iteration changes a driver's `.c` and possibly a
  header it includes; how many objects that costs, and how many seconds, has no
  reading. 🔴 It also cannot be taken with today's recipe: measuring it needs a
  reused tree, and `rlxfw-marks.py` refuses to re-apply to one. `PROGRESS.md`
  `INC-1`.
* **How long the watchdog takes to fire at its SHORTEST setting.**
  ⚠️ **This bullet replaces one added and withdrawn on the same day, and the
  withdrawn one was false.** It read *`CLK-08` has been an empty cell since
  2026-08-24*. 量: `CLK-08` was measured — **1118.133 ms** at `OVSEL=1001` and
  **557.583 ms** at `OVSEL=1000`, `bench/2026-08-25/H3c-D4.timing`. The false
  claim came from `SPEC.md` §17's residual row for the same id, whose prose still
  said *empty*; a search for `WDT`/`watchdog` in ASCII matched that row and not
  the measured one, which records the fact in Chinese. **What is genuinely
  unmeasured is narrower**: both measured points are high `OVSEL` settings, while
  `J BFC00000` writes `WDTCNR = 0` — the **lowest** setting, ~~推 2.184 ms by
  halving, never observed. `R4` predicts it and then measures it.~~
  🔴 **2026-09-08 (`R5-6`): the halving is not merely imprecise, it is
  STRUCTURALLY INVALID at this end, and the owning gate was stale too — `R4`
  closed on 2026-09-02.** 2.184 ms is `1118.133 ÷ 2⁹`. But `CLK-08b` solved
  the two measured points for a common offset and got **`c` = 2.967 ms**:
  what was measured is `2^(15+OVSEL)/f − c`, not `2^(15+OVSEL)/f`. Halving a
  quantity that carries a constant offset scales the offset with it, and at
  `OVSEL` 0 the offset is **larger than the number being predicted** — the
  halved prediction of the *measured interval* is negative. The correct
  prediction comes from the model and not from the ladder:
  **2^15 ÷ 14,965,000 = 2,190 µs** (`CLK-28`).
  🟢 **And it has gained two independent supports without a seating.**
  `bsp_machine_restart` (`boards/rtl8196e/bsp/setup.c:114`, not inside any
  `#if`) writes `WDTCNR = 0` and spins, so **every `busybox reboot -f` this
  project has ever run was a bite at exactly this setting** — dozens of them,
  and `FW-37` timed one end to end at 2.407 s. `CLK-08`'s own upper bound of
  **≤2.3 ms** from `entry` sits 0.11 ms above the prediction. ~~**`R5-6`
  measures it directly**: the `bite 0` rung of the OVSEL ladder, one reboot,
  no power cycle.~~
  🔴 **2026-09-08 (seating 17): that rung RAN and this bullet stays open, with
  BOTH of its halves now wrong for different reasons.**
  ① **The prediction is a loader-state figure.** `2,190 µs` = `2^15 ÷
  14,965,000`, and 量 that divisor is `CLK-08b`'s **loader** constant: under
  Linux the watchdog counts at **200,180 Hz**, so `OVSEL` 0 is **163.7 ms**,
  not 2.19 ms. Everything above this line that divides by 14,965,000 is
  describing the loader. The `≤2.3 ms` bound from `entry` is a **loader**
  measurement and still stands *for the loader*; it is not a bound on the
  Linux figure and this bullet had been reading it as one.
  ② 🔴 **The method does not work at this end, and that is a fact about the
  instrument rather than about the setting.** `rlxfw_puts` returns when the
  bytes are in the UART **FIFO**, not on the wire, so the arm happens with up
  to 16 characters still queued; at 163.7 ms the reset lands mid-drain and
  corrupts the marker the interval is measured from — 量, the `0x8D` after
  `RLXFW-W-GO` in `bench/2026-09-08b/C1-B.log`, and a "gap" of 1.095 ms that
  no non-negative offset can reconcile with the rung above it. **The ladder has
  two clean rungs, not four**, and neither is this one.
  🟢 **What it would take**: a marker whose last byte is known to be on the
  wire before the arm — either a drain loop reading the UART's own TX-empty
  status, or a rung timed from the PREVIOUS rung's arm rather than from a
  print. Neither exists yet. `SPEC.md` `FW-50`/`CLK-08b`,
  `notes/watchdog-driver.md` § 2.1 and § 10.6.
* ~~**`RLXFW-ID0`, the build-identity string added on 2026-09-01, has never
  been read off the board.**~~ 🟢 **CLOSED 2026-09-02, seating 10.** The board
  printed `RLXFW-ID0=B1434383` and `looprun`'s `A3` compared it against the id
  the build had just computed: *board printed b1434383, build computed
  b1434383*. **Nobody typed that value at any point** — it is a sha256 over
  `config/`, compiled in, printed by the kernel, and read back by the tool.
  It was checked twice on the day: once inside the bench run, and once by a
  desk run whose build started at 12:29 asserting over the capture the board
  produced at 12:15. `bench/2026-09-02/LP-boot.log`, `docs/GATE-RESULTS.md`
  `R4` claim 1.
* 🔴 **`R4`'s loop has never run `S2` to `S7` in one invocation, so its 73.88 s
  is a sum of two runs.** The bench half skipped the build; the desk half
  skipped the board. The one stage untested in a single command is *upload
  the image the loop just assembled*, ~~and it needs a power cycle~~. `SEAM-1`.
  🔴🔴 **2026-09-14: and it CANNOT be run at all, which is narrower and worse
  than needing a power cycle.** The `--image` pre-flight is above the stage loop
  and requires the file to exist; `S3` is what creates it. Two arms refused with
  **zero files created**; the control (`--skip S2,S3` with an existing image)
  passed the same guard and reached `S4`. So the never-run is **structural**, not
  a scheduling accident, and it cost no power cycle to establish.
  `notes/dev-loop.md` § 10.6.
* 🔴 **`looprun --iterations` above 1 is refused, because the loop cannot
  repeat.** `S4` is a loader command and iteration 1 ends with the loader
  gone. A loop that runs once is what exists; `R5` is six drivers. `LOOP-3`.
* 🆕 **`gpio_to_irq()` on this die.** 2026-09-10 (`R5-8`).
  `config/host-compat/0006` aliases it to gpiolib's `__gpio_to_irq`, which
  returns `-ENXIO` when `chip->to_irq` is `NULL`, and `rtl819x-gpio.c:658` is
  `.to_irq = NULL` — but **that chain is READ, not measured on the silicon**.
  🔄 **2026-09-11 (`R5-9`): still not measured, and it is now an unmeasured thing rather than an unknown one.** `ggbruno/openwrt`'s
  `arch/mips/realtek/gpio.c` implements a full `irq_chip` on this SoC's GPIO with a chained parent handler, and `shibajee`'s SoC header names the three
  registers it would need — `GPABCDISR`, `GPABIMR`, `GPCDIMR` — which this repository had never named. `docs/driver-diff.md` § 3.2 and
  § 3.4.5. ⚠️ Neither is 量 on this die and neither third-party image has been run here, so this row does not move: what changed is that
  *nobody has shown it works on this part* is no longer one of the reasons.
  `rtl819x-keys` prints the live value as `RLXFW-K4` on every boot and the
  prediction is `FFFFFFFA`; ~~nothing has booted it~~ 🔄 **量 2026-09-10,
  seating 20: `RLXFW-K4 = FFFFFFFA` on all seventeen boot captures, and
  `/proc/rtl819x-keys` prints `irq_probe -6`, `irq_live -6`, `enxio -6` —
  the same errno from a latched call site, a live one, and the constant
  itself. The read chain is now measured on the silicon.** The same sentence covers
  the `-EINVAL` this patch gives `irq_to_gpio()`, and that half is WEAKER
  still: 量, three files in this drop call it and this board builds none of
  them, so no image this project ships can demonstrate it either way.
* 🆕 **This button's bounce.** 2026-09-10 (`R5-8`). The
  `debounce_interval = 100` in `arch/rlx/kernel/rlxfw-devices.c` is a guess
  and the file says so. The instrument for it is `rtl819x-keys`' 32-slot
  jiffies ring and its `b0_n_bounce` counter, and the ring's resolution is
  bounded at 10 ms by `HZ=100` — which is also the floor of the poll
  interval, because `input-polldev` converts it with `msecs_to_jiffies()`.
  **A polled button cannot see bounce finer than its own poll interval**;
  that is a property of polling and not a defect of the timestamp.
* 🆕 **Whether `rtl819x-keys` polls at all on the die.** 2026-09-10.
  `input-polldev` queues no work until a HANDLER opens the input device
  (讀 `drivers/input/input-polldev.c`), and in this image the only handler
  that can is `evdev`, whose `input_open_device()` is inside `evdev_open()`
  (`drivers/input/evdev.c:190`) — i.e. it needs a userspace open of
  `/dev/input/event0`. Nothing has performed one. `n_open`/`n_poll` are the
  three-state reading that will say so.
* 🆕 **`SPEC.md` `FW-55`'s `111,540 個 load` is not reproducible.**
  2026-09-10. The same `tools/hazlint-objs.py` on `r59` — a SUPERSET of
  `r58`'s population — reports 3,096 loads over 70 leaf objects, and a
  superset cannot be smaller. `--also drivers`, the only wider run, REFUSES
  on `Q7b`. The row does not record which directories were swept, and the
  tool prints its population on every run precisely because a sweep's own
  population is a claim. The number stays in place with the correction beside
  it.


---

## 🔴 The device cannot check the driver's own arithmetic, and a mark it prints can be invisible to a `grep`

*Both measured 2026-09-08, seating 16. They are here rather than in a bench card
because they are properties of the image and of the console, and every future
card inherits them.*

| | |
|---|---|
| 🔴 **`FW-46` — this image's busybox has no `dd`, no `md5sum`, and no `--list`, so nothing on the device can digest a byte.** | 量, four cells, all `applet not found`: `busybox dd if=/dev/mtd2ro bs=4096 skip=8\|9\|10 count=1 \| busybox md5sum` three times, and `busybox --list` once. **`busybox wc` does work** — `C1-SZ` used it to read back `4194304` — so this is a small configuration, not a broken busybox, and "the applets are all missing" is refuted by a control in the same seating. 🔴 **The consequence is not inconvenience, it is a missing second source**: `rtl819x-spi`'s internal sha256 has **no independent on-device check** on this image, so all three of `FLS-26`'s controls on it are desk comparisons against the dump. ⚠️ And a card may not *guess* an applet exists: `RUNSHEET` §B5 records eleven busybox symlinks and "everything else is `busybox <name>`", which says how to **call** an applet and not whether it is **there**. Three cells were spent finding that out. |
| 🔴 **`FW-47` — the kernel's `rlxfw_mark()` output and busybox ash's echo of the typed line interleave character by character, so a mark the board printed can be absent from a `grep`.** | 量, `C1-TW`. The board printed `RLXFW-S-TRYW=00000001`; the capture's first line reads `… ; cat /proc/rtlR8L19XxF-sWp-iS-` with `TRYW=00000001` on the next. `RLXFW-S-` and the echo's remaining `819x-spi` are woven together one character at a time — both strings are present and neither is readable. 🔴 **Same family as `FW-41`** (*a mark the board printed can be absent from a `grep`*), different mechanism: `FW-41` is ash dropping the last character of a refused write's payload; this is concurrent output interleaving. 🟢 **The fix was already in the card's §4.3a and was not drawn out of it**: marks come from `write_proc` and fields from `read_proc`, so the mark is emitted *during* the echo and collides with it while the fields are emitted *after* and arrive clean. **Gate on fields, never on marks.** It cost one false stop, and the fields `n_write_refused 2` / `n_writes 0` in that very capture said the driver was right. 🔄 2026-09-26: of the two, `n_writes 0` carries no information — no committed `rtl819x-spi` increments it (`FW-142`). |
| 🔴 **Every console capture line is CRLF, so a field read with `awk` is `"1\r"` and compares unequal to `"1"` — while printing as `1`.** | 量 with `od -c`: `1 \r \n`. Three gates in one seating reported STOP or VOID on cells that had **passed**, each while printing the correct value beside the wrong verdict, because a carriage return is invisible in display. **The diagnostic and the test disagreed and the diagnostic looked right.** Any helper that reads a field out of a capture must strip it, and must self-test against captures whose answers are already known before it is trusted. |

---

## 🔴 A carriage return is invisible, and so is the tool you would use to see it

Every console capture line ends `\r\n`. `awk`'s `$2` is therefore `"1\r"` and
`[ "1\r" = "1" ]` is false. On 2026-09-08 that produced **three gates
reporting STOP or VOID on cells that had passed, each while printing the
correct value beside the wrong verdict**.

⚠️ 量 2026-09-08, while building the replacement: `cat -A` **under Git Bash
does not show the `^M` either**, because that shell translates the file on the
way in. The tool you would reach for to make a CR visible hides it. `od -c`,
or read the bytes in Python.

`tools/capfield.py` is the shared reader, and it refuses more than it answers:
a name that looks like a **mark** is refused with the reason rather than
returning empty (an empty answer reads to a caller as a failed assertion); a
field that occurs more than once is refused rather than picked (`X14-fast`'s
`dat` occurs 15 times); and `num`/`sub` **require** `--base`, because
`n_writes 0` is decimal and `sfcr FFC00000` is hexadecimal in the same dump
and `FW-35` is in this repository because `awk` read `8001e714` as scientific
notation. Its self-test runs against committed captures whose answers are
known and every other mode refuses to answer if it fails.

🆕 **2026-09-15, and this one says a line number can be undefined.** Building
`CITE-2`'s checker turned up a second consequence of a lone `\r`, on the
instrument side rather than the shell side. Python's
`subprocess(..., text=True)` applies universal-newline translation, so a bare
`\r` **becomes a line break** — `bench/2026-08-23/B.log` is 39 lines of bytes
and **59** read that way, while the same file read with `newline=""` is 39.
The first working version of `citecheck` had one side each way and reported
**76 rotted citations where there are 57**; the nineteen artefacts were all
`bench/` logs and all displaced by a *negative* amount, which is what gave it
away. Both sides now read bytes and split on `\n` only.

🔴 **What survives the fix is a stated limit, not a repair.** 量 2026-09-15:
**7 cited files hold a bare `\r`**, and in those files *line N* is not a
well-defined thing — an editor, `sed -n` and a universal-newline reader do not
agree on which line that is. `citecheck` prints the count on every run rather
than resolving it, because there is nothing to resolve: the ambiguity is in
the file.

🔴🔴 **A FOURTH consumer, 2026-09-17, and this one is not a
gate — it is a published number.** `docs/mfgtest.md` § 9.8,
`bench/2026-09-17/CORRECTIONS-block23.md` and `LOG.md` all quote
**`ae87ac03269985d6`** as the digest over the 32 lines of `MT-FLASH-3`'s flash
map, and it is the number carrying *4,186,112 bytes are unchanged across eight
days*. 量: `sed -n '19,50p' X8-M0.log \| sha256sum` returns
**`70484defc9714ecc…`**. The published value comes back only after
`tr -d '\r'`, **and none of the three files says so.** Negative control: 31 of
the 32 lines give a third value.

⚠️ **The direction matters.** The first three instances failed
loudly — a gate said STOP on a cell that had passed. This one fails
quietly and in the wrong direction: a reader re-deriving the digest from the
committed capture gets a different answer and concludes **the flash moved**.
The normalisation is now written down in `docs/mfgtest.md` § 9.8 and
`SPEC.md` `FW-92`; **nothing enforces it**, and no other published digest in
this repository has been checked the same way.

## 🔴 `\r\r\n` has two sources and only one of them is a wrap

量 2026-09-08 over all 762 committed captures (`FW-49`). busybox ash's line
editor wraps the **echo** of a typed line at the terminal width: 33 captures,
one wrap each, all with `len(sent)` in 80..121. The other 33 occurrences sit
**after** the echo and are the loader's ordinary `\r` + `\r\n` on a 10-character
command. **A scan that counts `\r\r\n` sees 66 and conflates two mechanisms
whose counts happen to be equal.**

Output is not wrapped -- an 88-character `/proc/version` line arrives whole in
five captures, and two loader commands of 119 and 127 characters do not wrap.
🔴 The consequence is a band: `console-capture.py` refuses a `--send` only at
**128** characters, so **79..127 is accepted and wrapped**, and in that band
both "the first newline ends the command" and "grep for the whole command"
fail.

🔄 **2026-09-16 (`R1z-2`), and the number this row was proudest of is no longer
the bracket.** The 2026-09-08 sweep read 762 committed captures; the corpus is
now **1,273**, of which 1,232 carry a `sent` and **1,194** classify (38
are `FW-47`'s echo-interleaving family). The band that was EMPTY on 2026-09-08 --
71..79 characters, the emptiness that made the threshold 推 rather than 量 --
now holds **40 captures and not one of them wraps**: fourteen at 71, four at
72, one at 75, one at 77, and **twenty at 78**, the last being six distinct
commands across two seatings (`bench/2026-09-10`, `bench/2026-09-14c`). The
shortest wrapped command is still **80** (`bench/2026-09-06b/K1-N`), and the
only two unwrapped captures above 80 are the loader's 119- and 127-character
`EW`s -- this row's own negative control firing a second time. The whole
classified corpus, by length: `<= 70` **1,091** captures and **0** wraps; the
band **40** and **0**; `>= 80` **63**, of which **61** wrap. 🔄 2026-09-26: the loader's two are no longer the only unwrapped sends above 80 — five shell sends of 2026-09-21 are too (below).

🔴🔴 **FOUR SWEEPS OF ONE CORPUS IN ONE HOUR. ONE WAS RIGHT, AND THE THREE
WRONG ONES DISAGREE WITH EACH OTHER.** This row's threshold was measured four
times on 2026-09-16, by four readers working separately from the same 1,273
committed captures.

* A throwaway script reading each log with `io.open(p, encoding='utf-8')` —
  universal newlines — saw **zero** wraps at every length, because the
  translation turns `\r\r\n` into `\n\n`. It reported an empty corpus.
* 🔴 **Two independent readers counted `\r\r\n` ANYWHERE IN THE LOG, both got
  20 of 20 at length 78, and both concluded the threshold was pinned there.**
  One of the two wrote down, in the same report, the objection that breaks it:
  *"`FW-49` says `\r\r\n` has two sources and I did not localise the bytes to
  the echo."* It published the conclusion anyway.
* `capfield wrapcensus`, using `echo_end` on a byte-read log, says **0 of 20**.

量, on `bench/2026-09-10/C11-L1`: `sent` is 78 characters and `echo_end` is
**78** — exactly, so nothing was inserted — and the single `\r\r\n` sits at
offset 78, *immediately after* the echo:
`…brightness ; cat /proc/rtl819x-gpio\r\r\nversion rtl819x-gpi`. Across all
twenty at that length: **0 inside the echo, 20 anywhere in the log.** The
contrast case is `bench/2026-09-03/TM-6` — `sent` 97, `echo_end` **100**, the
three extra characters being the wrap itself, splitting a command mid-token:
`…sleep 30 ; cat \r\r\n/proc/rtl819x-timer`.

🔴 **That is the conflation THIS ROW ALREADY NAMES**, reproduced one layer
down by two readers who had both read it: *a scan that counts `\r\r\n` sees 66
and conflates two mechanisms whose counts happen to be equal*. It is
attractive precisely because **20 equals 20** — the corpus returns the same
number under the wrong method, so the wrong method returns a plausible answer
and no arithmetic complains. One reader said nothing wraps and two said
everything at 78 does; the committed tool, which reads bytes and asks WHERE
the `\r\r\n` sits, is right, and it is right because `echo_end` was written
and tested for this exact question before any of the four sweeps ran.

🔴 **Two sweeps, two classified counts, and the committed tool is the one
that is right.** The first draft of this measurement walked the echo by
SKIPPING any character that did not match `sent`, so it could assemble the
command out of a much longer body and classified **1,218**;
`capfield.echo_end` steps over CR and LF only and returns nothing on a
mismatch, so it classifies **1,194** and declines 38. The band agrees in
both (40, none wrapped) and the difference is entirely at `>= 80`, where
the loose matcher added three captures it should have declined. 🟢 The
sweep now lives in `capfield wrapcensus`, beside `echo_end`, so the wrap
rule has one definition rather than two that can drift; its `K10` is the
positive control (>= 33 wraps above 80, the number this row records),
`K11` the negative (zero below 70) and `K12` the reconciliation, and it
prints the one length inside the bracket that has no capture: **79**.

So the bracket narrows from `70 < T <= 80` to **`78 < T <= 80`**: eight of its
ten values closed with data committed on 2026-09-10 and 2026-09-14 that nothing
had read. 🔴 **It is still not pinned.** The corpus holds **zero** captures at
exactly 79, so `T` is 79 or 80, and the 推 mechanism value -- 78 usable columns
beside a two-column `# ` prompt -- predicts **79**. One 79-character command at
a shell decides it, on any seating, and it costs no power cycle of its own. 🔄 **Pinned 2026-09-25 by block 46: `T` = 79** (below, *What block 46 did NOT establish*).

🔴 **Two independent triage routes reported the band's 40 captures correctly
and both concluded the experiment was already on disk.** Neither classified
whether those captures WRAP. They do not, which is why the threshold moved and
did not pin. The count was right and the conclusion was wrong in both, from the
same missing step.

🔴 **And the first instrument written to measure it returned ZERO wraps at
every length**, including the 33 this row records above 80.
`io.open(path, encoding='utf-8')` is universal-newlines: it turns the `\r\r\n`
being searched for into `\n\n`. The instrument destroyed its own subject and
reported an empty corpus. What caught it was this row's own 33 used as a
positive control; with `newline=''` the same sweep sees **64 of 66**.

## 🔴 A one-word correction that cannot be made without invalidating evidence

量 2026-09-16 (`R1z-3`). `tools/isa-payload.tsv`'s `special0e` row carries
`C2` in its `why` column where the answer is `C5`. The correction is one token
and it has been carried in this project's record seven times.

It is not a carry. The handover rule this project applies — *a row handed over
more than twice must be `⊘` or done now* — has *a change of owner* as its
subject, and across all seven the owner, the reason and the expiry were
identical. Counting them counts segments elapsed.

🔴 **The block is measured.** That column's text goes verbatim into
`cells4.S` and `BUILD_ID` is a digest over that file, so the edit moves
`a87be346bb83e7f9` → `43ddceb652831584` — and three committed bench captures
plus two frozen cards cite the former. Making the correction today would
invalidate evidence in order to satisfy bookkeeping, which is the wrong
direction: this project repairs the record to match the measurement and not
the other way round.

So it is a **rider on the next rebuild**, and its expiry is observable with no
new tool: the first committed capture that prints a `BUILD_ID` other than
`a87be346bb83e7f9`. 🔴 **No checker enforces that, and the absence is named
rather than assumed** — a new instrument is outside `R1z`'s scope, and a check
that would be red from today until the next rebuild is the shape this
repository already refuses, because a permanently red gate trains a reader to
stop reading reds.

## 🔴 Two bench directories are named for a day none of their captures happened on

量 2026-09-08 by `tools/capdate.py` on its first sweep. `bench/2026-08-30` and
`bench/2026-08-30b` hold 13 and 24 captures, all taken on **2026-08-29**
(22:59:15-23:13:02 and 23:16:42-23:26:29), and `git log --diff-filter=A` shows
both directories were created before those captures existed. The name was a
prediction that the seating would cross midnight; it did not. This is
`RUNSHEET` lifecycle rule 3's own failure, seven days before that rule was
written.

They are **not renamed**: 40 and 84 references across 23 and 17 files,
including two frozen cards and three tools. They are declared by name in
`capdate.KNOWN_MISNAMED`, and the list is swept in both directions so an entry
that stops applying fails rather than sitting there.

## 🔴 The check that asks whether a committed file holds forbidden flash bytes cannot run in CI, and has been invoked wrong

`tools/flashwin.py scan` is the only instrument that asks, **by the bytes**,
whether a file this repository has already committed contains content from
`H601` or the loader region. It needs `--dump` — the 4 MiB reference dump —
and that dump may never be committed, because it identifies one physical
device.

**So the check is desk-only by construction.** 量 2026-09-15 on
`.github/workflows/ci.yml`: CI runs `flashwin --self-test` and
`tools/test-flashwin-mutants.py` and **no step runs `scan`**. Those two say
the tool works; neither says anything about what is in the tree.

🔴 **And a desk-only check has nobody to notice that it did not run.** 量
2026-09-15: a `co-flashwin-scan.out` dated **2026-09-10** sits in
`$FWRE_WORK/rebuild/` and its entire content is
`flashwin.py scan: error: the following arguments are required: --dump`. 推:
that closeout's cell did not run and the error was not read. The same
invocation was made again on 2026-09-15 and caught the same way — by reading
the output instead of the exit line.

🟢 Run correctly on 2026-09-15 it reads **CLEAN over 4,441 files with 113
distinct 16-byte probes**. That is the reading; the issue is that nothing
makes it happen.

⚠️ What would close this is not a CI step — it cannot be one. It is a closeout
script that names `--dump` explicitly and fails loudly without it, and the
place that owns the closeout list is `CLAUDE.md`, which is the owner's file.

🔴 **2026-09-15, seating 23's closeout: a THIRD occurrence, and the half that
was missing is now the half that worked.** The closeout ran `scan` without
`--dump` for the third time — 2026-09-10, 2026-09-15 (seventy-second segment),
and again here. **What changed is that the closeout was a script that captured
each gate's output and printed `RED <name> (rc=2)` with the first lines of it**,
so the failure was read in the same minute rather than sitting in a `.out` file
for five days. Re-run correctly it reads **CLEAN over 4,467 files with 113
distinct 16-byte probes**, against `$FWRE_WORK/dumps/flash-n150rt-console-2.bin`
— the dump `notes/flash-digest-scope.md` names.

⚠️ **The remaining half is still open and it is the one this row asked for**:
the script had to be told `--dump` by a human after it went red, so a fourth
occurrence is available to anyone who writes the closeout from memory again.
🔴 **And a second failure mode was found the same way**: the same closeout
invoked `tools/xcheck.py check`, which does not exist — the mode is `sweep` —
and that produced a second `RED` that was also a misuse and not a finding.
**Two of the eight gates went red for reasons that had nothing to do with the
tree**, which is the shape that trains a reader to skim reds. Run correctly,
`xcheck sweep` reads 1,242 artefacts, 3 identities, 0 disagreements.

## 🔴 What the seventy-eighth segment did NOT establish — 2026-09-16

**Three instruments landed and a gate closed two of its five steps. This
section is what none of that settled.**

🔴 **The debt census is the record auditing itself, and it is blind by
construction.** Both of `cfcensus`'s populations come from one file. It cannot
see a debt this project incurred and never wrote down — which is the class the
seventy-seventh segment's closeout found **by hand**, four owner files that no
checker could reach. `U6` keeps that from being a sentence nobody tests (the
live file must yield at least one open row owned by a live gate, or the census
refuses), but a control that the tool is still reading is not a control that
the tool is reading enough.

🔴 **The 44 orphans are not 44 things still to do.** An adversarial review and
three independent triage passes agree that the classification has false
positives in at least four shapes, all measured: a row whose closure is written
`🟢 CLOSED` rather than `✅` is missed entirely (`REL-1`, whose owner cell
carries a URL to the artefact); a row naming a gate id **and** a standing
segment owner is reported as an orphan because the gate test runs first
(`TCPAY-1`, `CENS-1`, `C12-1`, `REGIMM-1`, `CAPD-1`); nine of the eleven
`L2` rows name work that exists under another name (`R2a` is `R2a/b/d`, `R1a`
and `R1b` were folded into `R1-pub`); and a row closed in `PROGRESS.md` §
Corrections rather than in its own cell is invisible (`C-16`). **The number is
an upper bound with a known direction, and it is published as one.**

🔴 **And one sentence of mine was committed and is wrong.** `tools/cfcensus.py`'s
docstring says a hand adjudication run the same afternoon was wrong about
`REL-1`. It was not: `REL-1`'s owner cell ends `🟢 **CLOSED 2026-09-01: the
take EXISTS.**` with the link. On that row the hand was right and the
instrument is wrong. The correction is in place and the claim is not repeated.

⚠️ **`R1z-2` is half done.** The `SPEC.md` § 19 scope defect and its six
findings are paid; **the 58 row dispositions are not**, deliberately — applying
them against a classification with four known false-positive shapes would bake
the defect into the table. The census is fixed first.

⚠️ **`C12`'s block selection is correct and was inert.** 量 2026-09-16: the
live `Next after this` row carried **zero** `🔄` markers, so `c12_blocks`
returned a single block covering the whole row, and the date-based selection
four controls were built for in the forty-fifth segment was doing nothing on
the live file. The code is right and the data had drifted. **Nothing here
measures inertness**, and `spec-check`'s own comment still said 28 dated blocks,
measured 2026-09-08.

🔴 **A citation format this repository prefers is indistinguishable from the one
it is replacing.** 量: the largest `SPEC.md:NNN`-shaped match in the repository
is that file's name followed by a colon and **110225**, in `tools/toolchain-census.tsv`'s `cite` column — whose
format is `FILE:TOKEN`, a **search token**, and whose token here is the tail of
the release name `rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225`. That is the good
format, the one `CITE-2` wants. It is simply unreadable as such by any scanner
when the token is all digits, and that is a hazard for the migration rather
than a defect in the row.

🟢 **And the scanner proved the sentence above while the sentence was being written.** The first draft of this section spelled that token out as a literal, and `citecheck`'s `M1` immediately reported *`docs/KNOWN-ISSUES.md` cites `SPEC.md`:110225 — SPEC.md has 804 lines*. A paragraph explaining that a scanner cannot tell the two formats apart was itself unreadable by the scanner, so it is written apart here — which is the workaround, not a fix.


⚠️ **The legend cannot gain the row it needs.** `算` is a sixth provenance mark
and it is declared in `tools/spec-check.py` rather than in `SPEC.md`'s legend,
because 量 the legend ends at `SPEC.md:34` and every one of the 28 distinct
`SPEC.md:NNN` citations in this repository points at line 696 or below, fifteen
of them inside three FROZEN bench artefacts. One inserted line moves all of
them. `C2b` is the control that forces the declaration out once `CITE-2` is
paid; until then two files disagree on purpose.

---


## 🔴 A closeout gate run on a dirty tree has its own findings switched off — 2026-09-16

量, by CI run `35102926093` going red on `text/citecheck` where every desk run
that segment was green.

`citecheck`'s oracle digests the cited row's content **at the commit that last
wrote the CITING line**. That is what makes a repaired citation drop off the
baseline. 🔴 **But blame is per LINE, and any edit to that line moves it — not
only a repair.** The eightieth segment appended a re-ownership note to one cell
of `PROGRESS.md`'s `LEDGER-3` row; the row's citation of
`tools/ledgerscan.py:505` had been rotted and on the baseline for weeks; the
blame moved to today, today's `:505` matched itself, and the rot read STABLE.
**Not repaired — laundered.** `C4` caught it because the baseline is swept in
both directions.

🔴 **And the desk could not have caught it**, which is the part worth carrying:
on a dirty tree `citecheck` **suspends every baseline row whose citing file is
modified** — it prints *their baseline rows are suspended* and names the count —
so a closeout run with twenty edited rows is a run with those rows switched off.
量 that segment: 28 of 43 rows suspended at the desk, 0 on CI.

**The rule this gives, and it costs nothing**: the `.md` gates are run once
before the commit and **again after it, on the clean tree, before the push**.
`spec-check`, `ledgerscan` and `flashwin scan` read the tree as it is;
`citecheck` is the one whose *population* changes with the tree's dirtiness.

⚠️ **The residual is not fixed**: rot that becomes rot in the same commit that
edits its row is laundered and never enters the baseline, so no later sweep can
find it. There is no control for that case, and inventing one means giving the
oracle a second reference point that is not the citing line's blame.

---


## 🔴 What `R1z` did NOT pay — 2026-09-16 (eightieth segment)

`R1z` took `cfcensus check` from 29 findings to 0 and the ratchet to a gate.
**Three things it did not do, each with what would settle it.**

| | |
|---|---|
| 🔴 **The debt census cannot see a debt that has already been PAID.** Its population is § Carried forward and that table is a claim, not a measurement. 量 2026-09-16: of the rows disposed of in one segment, **five had been paid while the record still carried them as owing** — one of them 13 h 43 m before the step row that named it, and one repaired at 03:50:57 and carried as stale by three consecutive closeouts. `cfcensus`'s own ⚠️ says it is blind to a debt never written down; this is that blindness with the sign flipped and it is **not** fixed | **What would settle it**: an instrument whose population is the ARTEFACT rather than the table — for each open row, the file it names, asked whether the sentence it complains about is still there. That is `tccensus`'s shape applied to prose, and its false-positive rate is unmeasured |
| 🔴 **`UP-AUD-1` ⑤c is unpaid and needs a build.** `notes/kernel-build.md` § 18.6's `up2` column takes a figure from a build artefact, and this gate ran no build. Re-owned to *any desk segment that runs a build*, first handover counted | **What would settle it**: one build, then the column |
| 🔴 **`CI-5` is `⊘`, not paid.** 量: `BIG3` has no consumer — no gate's DoD names it and no checker reads it — so carrying it further would be carrying an instrument nobody asked for | **Re-open condition**, on the row: the next CI run whose `BIG3` leaves the current band's upper bound, or the first gate DoD to cite it |

⚠️ **And one cost this gate incurred rather than removed**: `RECIPE_ID` moved
(an id rename inside `config/rlxfw-src/`, and the initramfs table's new build
commands). 量: no card was frozen against the old value — every `bench/`
directory already holds its captures — but **the next card must re-derive
`RLXFW-ID0` rather than copy it.**

---


## 🔴 What `P1` did NOT establish — 2026-09-17 (eighty-fourth segment)

`P1` shipped a production test that runs on this board: eleven checks, **11 of
11 on a good unit**, and **five of them turned red by physical injection** with
every revert measured. **Six things it did not establish**, each with what
would settle it.

| | |
|---|---|
| 🔴🔴 **The design table over-declares on three of its eleven rows, and only one had ever been caught.** 讀 2026-09-17, every § 2 pass criterion read against the `chk` call that implements it: `MT-TICK` named an input the script never reads (found at seating 25, struck), **`MT-PORT` declares *the output names the vendor driver* and prints the port**, **`MT-MAC` declares *body checksum 0* and puts that condition in `MT-RFCAL` alone** — so a unit with a valid header and a broken body checksum scores `MT-MAC` **ok**. All three claim a conjunct the script does not test. 🔄 2026-09-26 (`R6b-6`): `MT-PORT`'s is now tested (`mfgtest` 1.1; `SPEC.md` `FW-93`); `MT-MAC`'s is not | **What would settle it**: an instrument whose population is the table and whose subject is the script. This sweep is eleven hand comparisons and **will not see a twelfth row added tomorrow.** Three in eleven is a rate, not a target, and a checker fitted to three points should not exist — the same argument this repository already applied to the `D`-row census |
| 🔴 **`MT-PORT`'s missing conjunct is the one `R6` needs.** The plan's own ordering note says the port item runs against the **vendor's** driver until `R6` lands, so the output must record which driver served it or the historical numbers stop meaning anything the moment mine does. **Every `MT-PORT` line this project has captured is unlabelled** | **What would settle it**: one line in `mt_port`. It is `R6-0` work and not a tidy-up, because changing `config/mfgtest.sh` moves `RECIPE_ID`, and `MT-ID` compares against `RECIPE_ID`. 🔄 **2026-09-26 (`R6b-6`): done at the desk, not yet on silicon** — `mfgtest` 1.1 prints `Port3 LinkUp by rtl819x-switch 1.2; vendor tree present`, read from rlxfw's `/proc/rtl819x-switch` 1.2 rather than the vendor's `port_status`, so the label outlives `R6b-8`; in the `r6b6q` image (recipe `acf8ed3d`). `docs/mfgtest.md` § 2, `SPEC.md` `FW-93` |
| 🔴 **Five of the eleven live rows are class `S` — simulated at the boundary — and two files said four.** 量 2026-09-17 by two independent routes: `S` 5, `R` 4, `P` 2. `git log -S` puts the sentence and the `MT-ID` row in the **same commit**, so it was wrong the day it was written, in the section whose whole job is to understate nothing | **What would settle it**: nothing in this repository counts a table column. Corrected in place with the original quoted; the class of defect is open |
| 🔴 **No capture holds an operator's answer.** 量: five captures contain the string `OPERATOR`, once each, and every one is the **prompt**. The register half of each pairing is captured and closes exactly — `n_set_ok` 1→2, refused, →3, refused, 4→5 with `n_set_no 2` counting the two refusals; `n_poll` +400 / +1800 / +400 against 20 / 90 / 20 s at 20 Hz. **But `MT-LED` and `MT-BUTTON` are two checks whose verdict a machine cannot reconstruct from `bench/` alone** | **What would settle it**: the operator's reading typed into the capture as a `--send`, so the human answer and the register land in one file with one timestamp. That is a card-format change, the same shape `CAPD-1` already owes |
| 🔴 **Flash writability is untested, DDR is untested, and four of the vendor's eight factory-test areas are out of reach.** The flash substitute tests that the write path **refuses**, which is a different claim. `MT-DDR` is struck with its reason: no owned surface, no `devmem`, and `MEM-17` measured DRAM retaining a previous power cycle's contents, so a naive walking-1s can pass on stale data. TX power, RX sensitivity, PSD and thermal need instruments this project does not have | **What would settle it**: for DDR, a kernel verb over a `__get_free_pages` region — costed by nobody. For the other four, hardware. Recorded as a gap **against the plan**, not against the prior art: 讀, the vendor does not test DDR either |
| 🔴 **`D3`'s second conjunct was paid by an instrument it does not name, and the one it names never ran.** `D3` says *the `FLR` bracket is byte-identical across the gate*; 量, **zero `FLR` ran in `P1`**. What paid it is `MT-FLASH-3`'s 32-group map over 4,186,112 bytes, line-identical to two seatings eight days earlier — about four thousand times the bracket's 1,024 bytes | ⚠️ **Wider and less independent, and both halves are the finding.** The bracket reads flash under the *loader*, with Linux down and my driver unloaded; the map is computed by the same driver whose writes it is used to rule out, and `n_writes 0` comes from that driver too (🔄 2026-09-26: and it cannot move — no committed `rtl819x-spi` increments it, `FW-142`). **What would settle it**: one `FLR` bracket on `R6`'s first seating, which costs nothing — it rides the opening cold boot |

---

## 🔴 What `R6-2`'s desk half did NOT establish — 2026-09-17 (eighty-sixth segment)

A switch driver of mine is in the image, it writes nothing at boot, and the
DoD a frozen card called unsatisfiable is now a measurement that can be taken.
~~**None of it has run on the silicon.**~~ 🔄 **2026-09-19, seating 27: it
ran, and `R6-2` closed.** Every row below is kept and annotated rather than
deleted; what seating 27 did *not* establish has its own section further down.
Seven things the desk half did not
establish, each with what would settle it.

| | |
|---|---|
| 🔄 **CLOSED 2026-09-19.** ~~🔴🔴 **Not one instruction of `rtl819x-switch.c` has executed.**~~ 量: `41 of 41` carded cells, boot capture **1,759 bytes against a prediction of 1,759**, `RLXFW-ID0=F681F8E0` printed by the board. The original row read: The driver compiles, links, and its witness string is in the artefact three times against zero in the vendor's — but `rlxfw-marks verify` proves a translation unit is in an image and says nothing about whether any code path was reached. Every claim about `MSCR`, `VCR0`, `SWTCR1`, `FULL_RST` and the dumb configuration is 讀 | **What would settle it**: one power cycle. The boot marks `SW0`–`SW6` land in the boot capture with no verb typed, so the first reading is free once the board is on |
| 🔴🔴 **THIS ROW WAS WRONG BY A FACTOR OF FOUR, and seating 27's pre-power audit caught it.** 量 2026-09-19: `SWTCR1` = `00000200` and `PVCR1`/`2`/`3` = `00080008` were already in `bench/2026-09-17b` and in `SPEC.md`. It was **two of nine** — `MSCR` and `VCR0` — and after that seating's loader reads it is **zero of nine**. 推 the mechanism: `hdrcensus` searches committed files for an 8-hex token, and a `DW <base> 4` window labels only its base, so the other three words are invisible to it. The original row read: ~~**Eight of the nine registers the `dumb` verb writes have no reading on this die in ANY state.**~~ `R6-1` read `SWTCR0` and `PVCR0`; `MSCR`, `VCR0`, `SWTCR1` and `PVCR1`–`PVCR4` have never been read. So the driver's own `snap` of them at `subsys_initcall` is the first measurement, and **a write is being aimed at a register whose current value is unknown** | **What would settle it**: the `subsys_initcall` latch, which happens on every boot. It is ordered before any verb precisely so the reading exists before a write can disturb it |
| 🔴 **That a switch register reads back at all is assumed.** This part has one measured counter-example — `WDTCLR` was written `00A40000` and read `00240000` (`SPEC.md` `FW-52`) — and the vendor's own `_rtl8651_readAsicEntry` reads a switch TABLE entry **twice into two buffers and retries up to ten times** if the two disagree. ⚠️ That is the indirect table path, not the direct register path this driver uses, and **nothing here has established that the direct path is free of the same problem** | **What would settle it**: the `restore` round trip, and `snap`/`diff` taken twice on an unchanged state. Both are on the driver and neither has run |
| 🔴 **That `MSCR`, `VCR0` and `SWTCR1` are decoded by this part at all.** The header names them; this die is already known to name a register it does not populate — `PCRP5` at `0xBB804118` reads `00000000` where every neighbour reads `xx7F00xx`, and `SPEC.md` `NET-10` records the datasheet siding with the silicon against the header | **What would settle it**: reading them. A register that decodes returns a value; one that does not returns zero or garbage, and the neighbours are the control |
| 🔴 **`FULL_RST` is not proven to be a reset in the sense `D2` means.** It is documented *"Reset all tables & queues"*, the vendor asserts it, and `rtl8651_clearRegister()` says what Realtek thinks blank looks like — but that function **has no caller anywhere in the tree** (量), so it is an opinion and not a reading. Whether `FULL_RST` alone reaches the same state as the vendor's `FULL_RST` + 650 ms clock-gate recipe is **unmeasured by any source in this repository** | 🔴 **`resetcmp` IS NOT A VERB, and this row is where a frozen card's cell 8 came from.** 量 2026-09-19: the token appears exactly twice in the whole repository — a comment at `rtl819x-switch.c:375` and this row. Typing it returns `-EINVAL`. ~~**What would settle it**: the `resetcmp` verb, which runs both and diffs the dumps.~~ **What settled it**: `reset full` → `snap` → `reset vendor` → `snap` → `diff`, composed out of the verbs that do exist — and composing it exposed a confound the missing verb hid, because `reset vendor` asserts `FULL_RST` too. 量: the clock gate moves **0** of the nine `dumb` registers and 1 of 37 overall, and that one is a read-to-clear link latch moving because the gate worked. 🔴 **And the refutation is written first**: if no census register satisfies `S1 ≠ S0'`, the reset did nothing and the whole block is void rather than passed |
| 🟢 **CLOSED 2026-09-19 — it became positive on the FIRST seating after all, because the prior value was taken at the loader prompt twenty minutes before the card was frozen.** `CVIDR` reads `81964000` from the loader's `DW BB804200` (four times, across a power cycle) and from the driver's `__raw_readl()` at `subsys_initcall`. Two code paths sharing nothing, on a register nobody writes. The original row read: ~~**`CVIDR` is a read-path control that cannot be positive yet.**~~ Its value on this die is **未定** — nothing has read `0xBB804200`. On the first seating it can only fail (a wrong value proves the read path is broken); it becomes a positive control from the second seating onward, when there is a prior value to agree with | **What would settle it**: reading it once. Stated here rather than left for a reader to discover that a named control was doing half a job |
| 🔴 **`R6-2`, `R6-3` and `R6-4` are marked `desk N` and none of their DoDs can be met at a desk.** 量 `PROGRESS.md:105-111`: only `R6-1` (closed) and `R6-5` carry a seating. But `R6-2`'s DoD is a register read-back, `R6-3`'s is a ladder with an observable per rung, and `R6-4`'s is `ping` in both directions — all three are silicon. **The desk/bench column and the DoD column disagree for three consecutive rows** | 推, and it is a reading of the table rather than a fact about it: `desk N` means *this step consumes no power cycle of its own* and the proofs accumulate to `R6-5`'s seating, which the gate's own stop-loss anticipates (*any step that turns out to need the board … goes to the step that owns a seating*). **What would settle it**: the owner saying which reading is intended. 🔴 **The cost of the 推 being right is that a wrong register write or a wrong descriptor layout is discovered at the most expensive possible moment**, which is why the ordering of cells within that one card matters more than usual |

---

---

## 🔴 What seating 27 did NOT establish — 2026-09-19 (eighty-seventh segment)

`R6-2` closed. Nine things it did not close, each with what would settle it.

| | |
|---|---|
| 🔴🔴 **`R6-3`'s rung zero does not work as designed.** `SWINTSET` — `CPUICR` bit 20 — leaves no trace when written with the engine off (`CPUICR` `0`) and the mask closed (`CPUIIMR` `0`), and raises no `CPUIISR` bit. An off-card control proves the write path reaches the register: the mbuf-size field written through the same `echo write` **stuck**, confirmed twice. So `NET-38 殘留` ① — which `CPUIISR` bit is the software interrupt — is **not** answered | 推, three candidates: it needs `TXCMD`/`RXCMD` set, or `CPUIIMR` open, or bit 20 is not `SWINTSET` on this part. **What would settle it**: the same four cells with the engine on, which is one `ifconfig` away and was deliberately not done on a card that had already written its predictions. 🔄 **2026-09-26 (`R6b-5`): that cell ran the next day** — `bench/2026-09-19b/C13-swint`, engine on, mask `000007FE`, and no bit latched either (`SPEC.md` `NET-50`): the first candidate is closed, the second only for that mask — `CPUIIMR` fully open was never tried. `NET-38 殘留` ①② are ⊘, and ③ waits on `R6b-2`'s mechanism (`SPEC.md` § 17) |
| 🔴 **Which port index the CPU traffic appears on is now a FOUR-way disagreement, not a three-way one.** `asicCounter` shows `<Port: 5>` transmitting 6 unicast — exactly the count port 3 received — with RX zero, while `PCRP5` reads `00000000` in loader, `S0'` and Linux states and the vendor source calls port 5 the unpopulated MII port | **What would settle it**: an `asicCounter` bracket around traffic on a *different* physical port. One cable move, no power cycle, and it separates *port 5 is the CPU path* from *the counter block's indices are offset* |
| 🔴 **`PSRP6_RW` differs from `PSRP6` by exactly bit 2, and no source names that bit.** `0000007E` against `0000007A` | `SPEC.md` `NET-41 殘留` owns it. The decisive experiment is a **write**, needs an explicit yes, and `LDR-44` says `EW` is in the loader's unchecked-argument family. 🔄 **2026-09-26 (`R6b-5`): `NET-41 殘留` waits on `R6b-2`, ⊘ unless its mechanism names the CPU port's MAC-side state** — nothing this project boots touches the word; the reason and the reopening conditions are in `SPEC.md` § 17, and the readings in `docs/loader-phy-and-switch.md`'s `PSRP6_RW` section |
| 🔴 **`FULL_RST` is still not proven to be a power-on reset.** What `D2` supports is *differs from the state this part's own documented full reset leaves it in* — stronger than *differs from loader state*, weaker than *differs from the power-on default* | Unchanged from the desk half. Nothing short of a cold power-on with the driver latching before anything else would move it, and the driver's `subsys_initcall` latch is already the closest available |
| 🔴 **Seven of `dumb`'s nine writes are no-ops against `S1`**, so `D2` rests on `VCR0` and `SWTCR1` alone. The card predicted which two, from loader-state readings, before the verb ran — but a dumb configuration that differs from a reset switch in two registers is a thinner result than the gate's one-line goal implies | **What would settle it**: nothing measurable. It is a property of Realtek's reset, not of this driver, and it is recorded so that a reader does not mistake *two* for *nine* |
| 🔴 **The network does not come back after `restore 0`**, and nothing in this project restores the *vendor's* working configuration. `restore 0` writes `S0'`, which predates it | **What would settle it**: a fourth slot latched after the vendor NIC driver's `device_initcall`. The driver has four slots and slot 0 is taken by `S0'`; a `snap 1` at a shell before any verb is the existing workaround and it is a procedure, not a guard |
| 🔴 **`TEACR` and `ALECR`'s semantics are undetermined.** Their values are now known in three states (`00000000` at the loader and at `S0'`, `00000002` and `000505F2` live) and no source in this repository says what the bits are | **What would settle it**: the draft datasheet, or the vendor driver's writers. Neither has been read for these two |
| 🔴 **The free loader cells that would close `LDR-45`'s 推 have not been run**: `DW 80000000`, `DW 80410094`, `DW B800311C`. All three are read-only and cost nothing | **What would settle it**: three commands at any future loader prompt. `DW B800311C` reading a top byte ≠ `A5` refutes *the loader never arms the watchdog* |
| ⚠️ **`docs/loader-command-semantics.md` § 10's own free cell, `DW 80000080 32`, has still never been run** — seating 27 measured the same thing the expensive way, by accident | One command at a loader prompt |

---

## 🔴 What seating 28 did NOT establish — 2026-09-19 (eighty-eighth segment)

`R6-3` and `R6-4` both closed. Ten things they did not close, each with what
would settle it.

| | |
|---|---|
| 🔴🔴 **CI IS RED AND IT WAS RED WHEN THIS SEGMENT WAS PUSHED.** 🔄 **And the first version of this row gave the WRONG DIAGNOSIS for the one failure that actually blocks CI** — it said *"at least four are the same root cause: a hardcoded corpus count"*. That was written from a local `desk-sweep` summary and not from the failure text | **量, from `gh run view 35425822141 --log-failed`, and CI's list is SHORTER than the sweep's because the `text` job ABORTS at its first failure and everything after it is SKIPPED, not passed.** Two real failures, and they have nothing in common: 🟢 **2026-09-20 (eighty-ninth segment): all six adjudicated, five fixed, and the number was wrong in BOTH directions.** The sweep's *eight* and CI's *two* were never the same claim, and this row said so correctly — but the reason they could not be compared was STRUCTURAL and nobody had named it: the `text` job aborted at its first failing step and skipped the ~45 after it. That is fixed at the cause (`aecf346`): `if: !cancelled()` on every step below `capture dir` in both jobs, with `steps.prep.outcome == 'success'` supplying the ordering GitHub has no per-step `needs` for. NOT `continue-on-error: true`, which marks the step green and takes the run green with it — this repository's own `EXIT CODE: 0` incident bought deliberately; NOT `always()`, which also runs on a human cancellation. **Pre-registered before the push and confirmed by the run**: run `35453791429`'s `text` job ran **6m28s instead of aborting at 23s** and reported **SIX** failing steps where it had reported one — `test-boot-timeline`, `bootbytes`, `test-config-gates`, `audit-bench-log`, `citecheck`, `test-citecheck` — with `test-reply-size` green. **Desk-sweep's list and CI's list are now the same claim**, which is what this row was really asking for. |
| 🔴 **`text/test-reply-size` — and it is MINE.** `reply-size.py` does not crash on a count; it raises `ValueError: DW needs an address and a length` in `_dw_body` — line 97 of `tools/reply-size.py` **as that file stood at `fe900a1`** | **Cause: this seating typed `DW <addr>` with NO length**, three times — the free loader cells `DW 80000000`, `DW 80410094`, `DW B800311C`. The model assumes `DW` always carries two arguments. **The fix has its own measurement already in `bench/2026-09-19b`**: a bare `DW <addr>` reply is **69 bytes** (`X2`/`X3`/`X4`, all three) and `DW <addr> 4` is **71** (`X5`/`X6`) — the loader defaults to one line of four words, so the body is identical and the two extra bytes are the echo of ` 4`. 否證: if a fourth bare-`DW` capture anywhere in the corpus is not 69 bytes, the default is not a constant. ✅ **2026-09-20: fixed, and the FIRST fix was incomplete in a way worth keeping.** `b7eaf70` taught the default to `_dw_body` and left `predict`'s `int(argv[2], 10)` — the same parse, written a second time to build the derivation string — untouched, so `--self-test` stayed **green** while `check bench` died with `IndexError` and CI went red again on the commit that said it was fixed. Ten controls passed and not one called a bare `DW`: every one goes through the helper and the crash was in the caller. **A CONTROL THAT EXERCISES A HELPER DOES NOT EXERCISE ITS CALLER** — `hazlint` 1.0's `K4` and this tool's own `S5` with the roles swapped. Repaired in `6d2cd43`: one `_dw_words()` both callers ask; `C9`/`C9b`/`C9c` going through `predict` on purpose; `C10`–`C10c` pinning that a malformed command raises, with a parseable one as the negative control; and a `cmd_check` that reports an unparseable command as an `UNPARSEABLE` ROW instead of raising, because **a sweep that dies on row 1 has said nothing about rows 2..N** and three captures took 516 down. Suite 21 → 29 cases. 量, re-derived over the whole corpus: three bare-`DW` captures at 69, fifty-eight `DW <addr> 4` at 71, command lengths 11 and 13, so the difference is exactly `len(" 4")` and the bodies are identical. ⚠️ **This row used to carry that line number as a `path:NNN` citation, and it is deliberately GONE rather than re-pointed** — 🔴 and the commit that wrote this sentence to say so **added a second copy of the citation instead of removing the first**, because a sentence about a citation is a citation. 量: two occurrences on one line, `citecheck` `C1` 323 → 325, the same `M3` printed twice. Both are named by revision now, which is what a line number alone could never do: the message it quoted (`"DW needs an address and a length"`) 量 exists nowhere in the tree now, so *replace only the digits* cannot be satisfied and re-pointing would have cited a line whose text says something else. |
| 🔴 **`instruments/dtcheck` — and it is NOT mine.** 量, two runs, the version is printed by the step itself: the GREEN run `35387305159` (2026-09-18 19:59) ran `dt-validate (2026.6)` and reported `ok C1`; the RED run `35425822141` (2026-09-19 06:27) ran `dt-validate (**2026.9**)` and reported `FAIL C1`. **Same `.dts`, same `dt/`, no commit touched either** | 讀 the `dtschema` step of `.github/workflows/ci.yml` at the red run's commit `ca1b16d`: `/tmp/dtvenv/bin/pip install -q dtschema` — **unpinned**. So a green run here is not reproducible: the dependency moved between two pushes seventeen hours apart. ⚠️ **The failure text is worth keeping rather than pinning past**: 2026.9 rejects `linux,code`, `debounce-interval` and `default-state` as `bytes` where it wants an integer, which is a statement about how the DTB encodes them and may be a real defect that 2026.6 could not see. **Pinning the version and never looking would convert a finding into silence** — and this file's own `dtcheck` entry already records that all three dt tools print real failures and exit 0. 🔄 **2026-09-20: the pin was right, the reason written beside it is WRONG, and the true cause is more useful.** ① *"rejects three properties as bytes where it wants an integer"* cannot be right: `default-state` wants a **string** (`leds/common.yaml`, an enum), and it produces the **identical** message. 量 the message is `is not of type 'object', 'integer', 'array', 'boolean', 'null'` and it comes from `dt-core.yaml`'s generic JSON-primitive list — **one message, three properties, two different expected DT types, so the complaint is upstream of every binding's type expectation.** As written it aimed the next reader at the `.dts`, which is the one place the defect is not. ② 讀 `dt/*.dts:76/78/105`: `linux,code = <0x198>`, `debounce-interval = <60>`, `default-state = "off"` — all canonical, and the bytes `dt-validate` quotes back are the correct encodings of correct source. **Nothing in `dt/` should change.** ③ **The real cause is CORPUS COVERAGE, not the container.** `dtcheck` validates a compiled `.dtb` (讀 `tools/dtcheck.py:265-278`), but *"a .dtb loses type information so everything is bytes"* is refuted: 量 only **three** properties fail while `label`, `gpios`, `compatible`, `reg` and `#gpio-cells` — including `label` two lines above `linux,code` in the same node — validate fine. The discriminator is that `property_get_type()` returns `[]` for exactly the three. `dt/bindings/` has no `input` or `leds` directory, and `dt/unmatched-allow.tsv` already declares `gpio-keys` and `gpio-leds` as kernel bindings outside the corpus. 2026.6 GUESSED a type for an untyped property; 2026.9 hands the raw bytes to the validator. 量, with a negative control in the same command: supply minimal `gpio-keys`/`gpio-leds` schemas and pristine 2026.9 reports **0** of the three; same `.dtb` without them, **3**. 🟢 **So 2026.9 is not a regression to pin past — it is a stricter instrument reporting a scope limit that was always there**, and `C2`'s blind spot is now named: `C2` enumerates unmatched COMPATIBLES and cannot see that an unmatched node's PROPERTIES go untyped and unvalidated with it. 🔴 **And a second, pre-existing defect came out of it**: `dtcheck --extra-schema` does not work. 量, same `.dtb`, same schemas, only the packaging changed — one `-s` gives **4** unmatched, two `-s` give **11**, because a second `-s` makes this project's own six bindings stop matching. **Version-independent**, equally broken under the pinned 2026.6, never caught because CI never passes the flag — and it is the escape hatch **five of `unmatched-allow.tsv`'s seven rows name as the reason they are allowed.** |
| ⚠️ **The other six the local sweep listed are UNADJUDICATED**, because CI never reached them | `text/test-boot-timeline`, `text/bootbytes` (`K2`), `text/test-config-gates`, `text/audit-bench-log`, `text/citecheck`, `text/test-citecheck`. The corpus-count story is still the likely one for several — `test-boot-timeline`'s `B2` would be red for the **fifth** time — and the durable fix carried forward since the eighty-seventh segment is unchanged: **assert the property, report the count**. ⚠️ But `bootbytes` `K2` is a different shape and must not be lumped in: `{307: 1, 309: 1, 710: 105}`, a constant it asserts is one value is now three. **Adjudicate each from the CI log, not from the sweep summary — that is the mistake this row was written to record**. 🔄 **2026-09-20: adjudicated, and this row is wrong twice.** ① *"the corpus-count story is still the likely one for several"* — 量, it is **three rotting literals in two suites**, and they are the only assertions in the `text` job that are red because the corpus grew: `test-boot-timeline.sh` B2 (`41/171/0`) and B3 (`79`), and `test-config-gates.sh` `G4c` (`8`). ⚠️ **`G4c` is not even the capture corpus** — it counts `str:`/`sym:` rows in `config/rlxfw-marks.tsv`, which went 8 → 9 because seating 28 added `MK10` for `rtl819x-nic`. A *driver* moved it, not 148 captures. Everything else with a literal in it is legitimately fixed: tool-control counts, frozen fixtures, and measured loader replies. All three are now properties, with what each no longer catches written beside it. ② *"`bootbytes` `K2` is a different shape and must not be lumped in"* — **half right, and the half that is wrong is the interesting one.** The SHAPE is different (a selection, not a count) but the TRIGGER is identical: 量 `bench/**/*boot*.log` also matches `*reboot*.log` — **"boot" is a substring of "reboot"** — and seating 28 produced the first such files this repository has ever held. Two `busybox reboot -f` captures that stop at the loader prompt and never enter Linux were read as a third and fourth value of the boot constant; their remainders (307, 309) differ by the two bytes of one echoed `^[`. ⚠️ **The commit that went red is not the commit that made the defect reachable**: `edb7122` put the first `*reboot*.log` into the glob's match set and nothing failed, because it carries no `RLXFW-` and the content filter dropped it; `72bfecd` added the two that carry marks. ③ **`audit-bench-log` was not a count either**, and its five hits are seating 28's first `ifconfig` on a net_device of ours — `rtl819x-nic`'s own MAC and the broadcast of the already-allowlisted bench network in the second spelling busybox prints. Both allowlisted with reasons and scope limits. 🔴 **The MAC was ALREADY on `spec-check.py`'s `REDACTION_ALLOWLIST` with a full reason and was not on this one, and nothing in this repository compares the two** — while the entry one line above it records a divergence (`192.168.1.6`) that IS a stated decision. **A decision and an oversight are indistinguishable by reading either file.** |
| 🔴 **Why the switch's ingress path wedged is unidentified, and the flood is not proven to have caused it.** What is measured is its LOCATION (below both drivers — the vendor's own driver also sent 2 and received 0) and its REMEDY (a cold power-on). It happened **once** | `SPEC.md` `NET-54 殘留`. First: does it reproduce at all, from a known-healthy cold boot? Second: the reading set was too thin — all eight `PSRP<n>`, `MACCR`, `FFCR`, `SWTCR0`, and above all `/proc/rtl865x/asicCounter`, which would say whether frames reached the SWITCH. Without it, *the switch got them and would not forward to the CPU port* and *the port never saw them* are still one hypothesis. 🔄 **2026-09-26 (`R6b-5`): two phrases in this row are corrected, and the row is re-owned to `R6b-3` beside `NET-124` 殘留** — block 46 showed the same shape with the cable untouched (`NET-124`). `eth4`'s counters are port 3's MIB counters, not a count the vendor driver keeps (`notes/nic-driver.md` § 6.4, item 5's note), so the vendor's driver was not a separate control, and the reading this row asked for was in fact taken: port 3 counted no frame in, errored or not — for that boot, *the port never saw them*. The mechanism and the cause are still open; `SPEC.md` § 17 `NET-54` 殘留 says what `R6b-3` reads when the shape recurs |
| 🔴 **The run-out fix is an untested guard.** It is compiled into `r6nic3` and 量 shows the path it adds was never exercised: `seen_iisr` carries no run-out bit in either image, and loss is 0.0536 % with it against 0.0531 % without | It is kept because a descriptor run-out raising no interrupt is a real hazard. To test it you must first be able to STARVE the ring on healthy hardware, which four concurrent 1400-byte floods did not do |
| 🔴 **`netif_wake_queue` is never called, and the defect is real and unreached.** `nic_xmit` stops the queue on a busy descriptor and nothing restarts it | `n_xmit_busy` read **0** in every flood on both images, so four TX descriptors were never exhausted at `pipe 2`–`pipe 4`. A load with a real window — an `iperf3` stream, `R6-5` — should reach it. 否證: if `n_xmit_busy` moves while the interface keeps working, this analysis is wrong |
| 🔴 **Throughput is unmeasured.** Every number this seating produced is ping-bound: each flood waits for a reply, so 1.88 MB/s each way is a floor on the path and not a rate | `R6-5`. And its method must be written down with it — this project has recorded four times that a single number is not a curve |
| 🔴 **`R6-4`'s `D4` is only partially met.** The vendor's driver is still in the image. What is measured is that it is not carrying the traffic: non-shared `request_irq(12)` succeeded, `CPUICR` read `00000000` until my driver wrote it, and the rings in use are at addresses my driver printed | Removing it is not free and the reason is measured: 讀 `rtl_nic.c:6214-6215`, the vendor's **probe** is the only thing in this image that disarms the DMA engine the loader leaves running at `0xA040FC70` — memory Linux hands out. Remove the driver and something else must do that first |
| 🔴 **No card was frozen for this seating.** Predictions were written into each runner script before it ran, but `check-predictions` cannot score it and there is no mtime evidence | An exchange of auditability for iteration speed. It bought six boots and three images on one power cycle. Whether to repeat it is a decision for `R6-5`, whose seating has a fixed budget |
| ⚠️ **`ph_queueId`'s layout is still inherited from a declaration nothing has ever executed.** 量: one grep hit in the whole vendor Ethernet tree — its own declaration — against `ph_mbuf` 50, `m_data` 28, `ph_len` 11 | The minimal ladder does not touch it, which is why `R6-3` closed without it. `R6-5`'s larger frames may |
| ⚠️ **Whether TX rings 2 and 3 interrupt at all is undetermined.** `CPUIIMR`/`CPUIISR` define two TX rings' worth of bits and this part has four | No source in any drop resolves it. This driver uses ring 0 only |
| ⚠️ **`CPUIISR` bits 12 and 13 fire on every transmit and the header names neither.** `last_iisr` read `00003206` and `0000320E` throughout | Two unnamed bits in a register this whole gate turns on. A sweep of `CPUICR` states against `CPUIISR` would bound them |

---

## 🔴 What the eighty-ninth segment did NOT establish — 2026-09-20 (desk, zero power cycles)

Six red CI suites went green and `R6-5` was prepared. Eleven things that did
not close, each with what would settle it.

| | |
|---|---|
| 🔴🔴 **NOTHING OF `R6-4a` HAS RUN ON THE SILICON.** The TX-queue wake, the `ndo_tx_timeout` handler, the five `/proc` fields and the `txstall` verb are all 讀 and 推. What IS measured is that they **compile**: image `r6nic5`, `RECIPE_ID ffe4b5cf`, `vmlinux` 4,212,358 bytes, `rtl819x-nic.o` 28,104 bytes | `R6-5`'s seating, and `notes/nic-driver.md` § 7.7 carries the refutation condition. ⚠️ The strongest single reading to take is `n_tx_timeout > 0` — it would mean the interrupt-driven wake missed and only the 5 s watchdog saved it, i.e. the design is wrong **even though the link survived** |
| 🔴 **The `txstall` control has a refutation condition and it has not been run.** If `txstall off` does not restore transmit, clearing `TXCMD` mid-flight wedges the engine, the control is VOID, and the seating falls back to the flood alone | One cell, two-sided, before any load. And it needs **two** `ping` runs, not one: 量 this image's `ping` always sends four packets and the ring holds four, so one ping fills it exactly and never reaches the fifth frame — the control would be void while looking like it ran |
| 🔴 **`iperf3` is built and has never touched the device, and it is not in an image.** 量: `iperf 3.1.3`, **252,644 bytes** static, **zero source edits**, `hazlint` 0 load-use violations in 12,639 loads, and a MIPS-BE client and server completed TCP, UDP and JSON runs against each other under `qemu-mips-static` | Adding it to `config/rlxfw-initramfs.tsv` is a `config/` change, so it moves `RECIPE_ID` and needs a rebuild. That is `R6-5`'s first desk act. ⚠️ `TCP_INFO` is the one thing qemu **cannot** verify — it returns `optlen 4` where a native build returns 104 — so a nonsense `Retr` column is the signature to watch for on the die |
| 🔴 **`-fno-if-conversion` cannot reach a statically linked vendor `libc.a`, and that generalises.** 量, two builds as a control: flagged and flagless both carry the **same 114** conditional moves (65 `movz`, 49 `movn`), and every one is in uClibc/libm — `iperf`'s own 16 objects emit **zero** | `config/rlxfw-cflags`'s safety net (`TC-25`) is a compile-time flag and `libc.a` was compiled by Realtek years ago. It applies to **any** future static userspace tool, not just this one. `hazlint` reports 0 load-use violations, which is the check that matters; the 114 rest on `docs/isa-prior-art.md`'s prior art, not on the flag |
| 🔴 **pktgen is compiled in and has never been driven.** 量: `CONFIG_NET_PKTGEN=y` at the built `.config:512`, `pktgen.o` 49,012 bytes, and the prediction written before the build — `(NEW)` stays 0 — **held** | It bypasses the qdisc, so a number it produces is a **TX-path rate and not TCP goodput** and may not be quoted as one. What it is for is `R6-4a`: 讀 `pktgen.c`, it checks `netif_queue_stopped()` and retries on `NETDEV_TX_BUSY`, so it hammers exactly the stop/wake path |
| 🔴 **Two allowlists overlap and nothing compares them.** `02:52:4C:58:46:57` was on `spec-check.py`'s `REDACTION_ALLOWLIST` with a full reason and NOT on `audit-bench-log.py`'s, and the entry one line above it in that file records a divergence (`192.168.1.6`) that **is** a stated decision | **A decision and an oversight are indistinguishable by reading either file.** What would settle it: a cross-check that enumerates both lists and requires every difference to be DECLARED rather than merely true. Not built — it needs a declared-divergence table that does not exist, and inventing one at the end of a long segment is how a guard gets written badly　🔄 **2026-09-21 (seating 35): it fired a THIRD time, and this time the file's own text said the entry was already there.** 量, CI run `35603465351` went red at `audit-bench-log`: **4 hits over 2 files**, all `02:52:4c:58:46:57` in `tcpdump`'s lower-case spelling, from the first ARP REPLY this project has captured off the board. `audit-bench-log.py` carried the UPPER-case spelling only, while `spec-check.py` carried both — and the `fc:19:28:61:84:c9` entry written one segment earlier states in prose that this address *carries two entries*. **The case pair was made in one file and the sentence describing it was written in the other.** Fixed by adding the entry; the cross-check this row asks for still does not exist, and it would now have three instances to be built from |
| 🔴 **`dtcheck --extra-schema` does not work and the pin is still in place.** 量, same `.dtb`, same schemas, only the packaging changed: one `-s` gives **4** unmatched, two give **11**, because a second `-s` makes this project's own six bindings stop matching. **Version-independent** — equally broken under the pinned 2026.6 | It is the escape hatch **five of `dt/unmatched-allow.tsv`'s seven rows name as their reason**. The fix is to merge the schema dirs into one corpus dir, and it needs a positive control or the merge cannot fail: a schema in the "extra" dir that the corpus does NOT contain, whose compatible must become MATCHED |
| 🔴 **`C2`'s blind spot is named and not closed.** It enumerates unmatched COMPATIBLES and cannot see that an unmatched node's PROPERTIES go untyped and unvalidated with it | 量, with a negative control in the same command: supply minimal `gpio-keys`/`gpio-leds` schemas and pristine dtschema 2026.9 reports **0** of the three complaints; without them, **3**. Vendoring those two kernel bindings into `dt/bindings/` would lift the pin BY MEASUREMENT and delete two `unmatched-allow.tsv` rows — which is a scope decision about what this repository claims to describe, not a CI repair |
| ⚠️ **What the three corpus-count replacements no longer catch, and it is real.** `B2` no longer sees a capture flipping cold↔warm while both stay above their floors. `B3` no longer sees one capture ceasing to qualify while another starts. `G4c` no longer NOTIFIES on a new mark row | The first is partly recovered by the named witnesses beside it (`A-catch` cold, `H2a` warm), not fully. The second's real detector was the per-directory isolation checks, which are **comments, not cases** — the honest form is a case over a NAMED directory, not a total. The third is a deliberate trade: one red CI per new driver trains a reader to ignore reds |
| ⚠️ **`bootbytes`' glob is still wrong in the other direction.** 量: five `RLXFW-B10`-carrying `.log` files are not named `*boot*.log`, four harmless at const 710 and one — `bench/2026-08-30b/L3.log`, 6,459 bytes — at const **6,320**, a verbose-printk image | Widening the glob naively **re-reds `K2`** on that last one, measured. Whether a verbose-printk image is the same population is a question for `SPEC.md`'s owner. The population's outer edge is therefore still a naming convention, and saying so is the scope limit |
| ⚠️ **`CLAUDE.md` states "replace only the digits" without the range caveat, and I did not edit it.** 量: `…ci.yml:755` occurs exactly once on its line — as a range's START — so a correct-looking digit replacement produced `837-773`, and `git apply --check` was GREEN on it | It is recorded here and in `0fbb2f0`'s message. `CLAUDE.md` is the operating-rules file and editing it is the owner's call, not a closeout action. The generator now matches the whole citation including the `-NNN` tail, requires exactly one occurrence, re-derives both endpoints and asserts `start < end` |

---

## 🔴 What `R6-5`'s seating did NOT establish — 2026-09-20 (ninetieth segment, seating 29)

`D5` and `D6` are both open. Seven things did not close, each with what would
settle it.

| | what would settle it |
|---|---|
| 🔴🔴 **No throughput number exists.** Every `iperf3` run on the die either failed its control exchange (`SPEC.md` `NET-60`) or hung the board (`NET-59`). `D5` asks for a number with its spread over three runs and there is not one | The next seating, with **3.1.3 on both ends** — 量 that a `qemu-mips-static` server binds the real interface and a same-version client completes against it |
| 🔴🔴 **A real TCP load hangs the whole board and the mechanism is undetermined.** Two reproductions; console silent for 100 s at 0 bytes; `reboot -f` ineffective (7,489 bytes captured, all of it ESC, no loader prompt); and **not a panic**, because `traps.c:52` is `#define printk panic_printk` and nothing printed | A **bounded** transfer — `-n 64K`, then bisect upward — with a liveness probe between every step and `n_irq` read after each. 推: an interrupt storm, because the CPU is alive and making no progress |
| 🔴 **`D6` was never attempted.** The 30-minute flood did not start | Gated on the two rows above |
| 🔴 **`-l 8K`'s survival is uninterpretable.** It did not hang, but its control connection broke before any data moved, so it is not evidence that a small blksize is safe | Re-run it once the control exchange works |
| 🔴 **`NET-54`'s re-attribution is 推, not 量.** A marginal cable produced exactly `NET-54`'s shape — interface deaf, below both drivers, recovered by an action that involves handling the board. That is a hypothesis about a past reading, not a measurement of it | `NET-54` reproducing with the cable demonstrably untouched. 🔄 2026-09-26: `NET-54`'s own `eth4` counters are port 3's MIB and read no frame in, which is `NET-56`'s counter signature (`notes/nic-driver.md` § 6.4) — still a reading of the past boot, not a cause. 🔄 2026-09-26: this row's refutation condition was met by block 46 (`NET-124`): the same shape with the cable untouched — 量 the host's link read `LOWER_UP` with `transns` 4 unchanged at all 76 host reads after A1-00 (no carrier transition), and 讀 the card's only physical actions were the power press and power-off. `SPEC.md` § 17 `NET-54` 殘留 is re-owned to `R6b-3` |
| 🔴 **The vendor-driver contrast could not be taken.** `ifconfig eth4 up` returned `SIOCSIFFLAGS: Device or resource busy` because my driver holds a non-shared `request_irq(12)` — 量 `bench/2026-09-20/X9` | An image in which my driver is not bound, or a shared IRQ. Until then *below both drivers* cannot be re-measured on this arrangement　🔄 **2026-09-21 (seating 35): TAKEN, and this row's reason is refuted on the device.** 量 `bench/2026-09-21e/V2-DOWN`/`V3-ETH4`: with `ifconfig rlx0 down` FIRST, line 12 leaves `/proc/interrupts` and `ifconfig eth4 10.1.1.4 up` takes it back as `12: 12 RLX LOPI eth4`, `UP BROADCAST RUNNING`. The vendor's driver then carried a full `iperf3` run — 31.3 MBytes at 25.4 Mbit/s, `Retr 0` — and survived it. `SPEC.md` `NET-84`, `docs/nic-vendor-diff.md` § 11. |
| ⚠️ **Whether the three defects in `notes/nic-driver.md` § 8 interact is unknown.** `NET-57` (no watchdog), `NET-58` (a re-open leaves the engine loose) and `NET-59` (the hang) were each measured alone | `NET-59` first; the other two have identified causes and it does not |

⚠️ **A closeout audit was launched and its report was never read.** The segment
ended while an adversarial *what did this produce, and who owns it* pass was still
running, so its findings are not in this list. That is a hole of a known shape: the
audit's whole job is to find what the write-up failed to record, and nobody read the
answer. **The next segment re-runs it before anything else touches these files.**

⚠️ **And one process failure of mine, recorded because it cost the most.**
Block 29 lost **fourteen carded cells** by typing them into a shell that was
already dead — nothing checked between cells, so each `--send` went into a hung
console and produced a 39-byte capture that `check-predictions` scores exactly
like a real one, since it reads existence and mtime and never content. The fix
is a two-line liveness probe between steps, and it paid for itself on its first
run: the next failure cost **one** cell instead of fourteen. **A card's cells
are one-shot, and a gate between them is not optional.**

## 🔴 What `R6-5`'s third seating did NOT establish — 2026-09-21 (ninety-second segment, seating 31)

Image `s31b`, `RECIPE_ID f179cf21`, four cold power-ons, 29 of 29 carded cells
spent.

| | |
|---|---|
| 🔴🔴 **No throughput number exists, and the reason changed for the third time.** Seating 29 blamed the iperf3 control exchange (`NET-60`); seating 30 blamed the ring desync (`NET-61`); **both are now excluded.** `NET-60` is closed — 量 `V1`, `Reverse mode, remote host 10.1.1.2 is sending`, so 3.1.3 at both ends negotiates a bulk transfer 3.16 could not. `NET-61` is excluded — `n_dsync 0` through all three wedges with the detector's positive control proven in the same boot. What stops `D5` is `NET-67` 🔄 **2026-09-21 (ninety-fifth segment): that sentence is stale and is corrected rather than deleted.** `SPEC.md` `NET-78` measures the current failure as the opposite of `NET-67` on **every** reading — `tx_stopped 0`, `n_tx_stop 0`, `n_xmit_busy 0`, `n_tx_full 0`, all four `txd` CPU-owned, `n_tx` advancing 5 → 37 — on two independent cold boots. **The blocker has now been named four times (`NET-59` → `NET-61` → `NET-67` → `NET-78`) and each name was refuted by the next seating's measurements; this file carried the third one for two seatings.**: sustained TCP fills all four TX descriptors and the queue never wakes | Next: read the ENGINE side. `tpdcr0_pos` across a wedge and `/proc/rtl865x/asicCounter`'s CPU-port `Snd` — neither was read, and neither costs power |
| 🔴 **`D6` was never attempted, and this seating established it is unmeetable on any image this project has run.** 讀 `config/rlxfw-kernel.delta:138`, `set@loud CONFIG_PRINTK n y`: with `PRINTK=n` an oops prints nothing and there is no kernel log, so *zero oops* and *kernel log captured whole* are both unobservable | `s31L` was built `--variant loud` for it and **never uploaded**. 🔴 And `RECIPE_ID` cannot tell the two images apart (`FW-99`) — the discriminator must be the assembled image's sha256 🔄 **2026-09-21 (seating 32): the second half of that sentence expired at 03:19.** `s31L` — the loud image this row names as built and never uploaded — was uploaded, booted and ran the flood. **`D6` is met.** See this file's seating-32 section and `SPEC.md` `NET-76`. The first half stands: it *was* never attempted before then. |
| 🔴 **Why the switch engine stops retiring TX descriptors is unanswered.** The fault is fully characterised on the driver's side and completely unexamined on the engine's side | `NET-67` 殘留 |
| 🔴 **Whether the fault needs TCP at all is untested.** Every wedge this seating was TCP; a long ping flood is RX-plus-TX with no TCP and is the discriminator | Not run 🔄 **2026-09-21 (seating 32): run, with three negative controls, and the answer is that a TCP connection IS required** — a flood ping at in-flight depth 34 moved 27,017 frames each way without wedging, and so did the same flood with 3,110 concurrent 18-byte pings. `SPEC.md` `NET-73`. ⚠️ What is still not separated is "a TCP connection" from "`iperf3` the program". |
| 🔴 **The recovery is partial and decays, and the three readings were not separated.** `arm` alone moved every counter but left ping at 0/4; one `ifconfig down/up` reached 2/4; a second returned to 0/4 | `NET-68` 殘留 |
| ⚠️ **`R6-6` was not attempted**, deliberately. Two of its three DoD clauses were established unreachable before power: two ports need two simultaneous endpoints, and rlxfw cannot write the VLAN **table** at all (讀 `rtl819x-switch.c:88-92` — the table is the indirect TACI path, so what a restore restores is the PVID register, not the object the DoD names) | Carried to the next segment with `R6-7` |
| ⚠️ **`n_rx` rose by more than the fragment count on several ladder rungs** (e.g. +14 for a 9-fragment datagram). 推 background ARP and stragglers; not chased | — |

### 🔴 `NET-64`'s owner passage, which did not exist until now

`SPEC.md` has named `docs/KNOWN-ISSUES.md` as `NET-64`'s owner since
2026-09-20 and this file contained **zero** occurrences of the string — the
same defect class commit `4ce031e` fixed for `NET-65`/`FW-97`/`FW-98` and did
not find here.

**`NET-64` asked what made the board silent for 112 minutes with a watchdog
armed at ~84 s that never bit.** Its own row recorded the contradiction: if it
bit, the loader should have echoed the ESC stream and did not; if it did not
bit, the CPU was running. Both branches cost the "hard hang" reading.

🟢 **Seating 31 answers the branch.** 量, twice: during the fault the tty
echoes the exact bytes sent (`X5-ECHO2`, 24 bytes, precisely
`echo RLXFW-ECHO-PROBE2\r\n`) while a read-only window with `sent: null`
returns **0 bytes over 30 s**. Echo is done by the kernel's line discipline, so
**the kernel was running** — `NET-64`'s H4/H6 branch, and the "hard hang"
headline is refuted rather than merely unsupported. 🔄 **2026-09-26 (`R6b-5`): that sentence merges the two states the next paragraph keeps apart.** Seating 31's echo refutes a hang in seating 31's wedges; `NET-64`'s seating-30 silence had no echo at all, so what costs its "hard hang" is its own branch — an armed watchdog that never bit — not this echo.

⚠️ **What is still not established** is whether seating 30's 112-minute silence
is the *same* fault as seating 31's wedges. Seating 30's console gave **0 bytes
with no echo at all**; seating 31's echoes. Those are different observables, and
this file does not merge them. 🔄 **2026-09-26 (`R6b-5`, desk): corrected, and this passage owns the correction — `NET-64`'s arm did NOT run with the engine on.** 讀 `bench/2026-09-20b/PREDICTIONS-B34-block32.md`: every arm cell, `A1`–`A7`, sends `engine off ; arm ; engine on`; 量 `A1.log` prints `N-ENGOFF`, then `N-ARM=A15B8000`, then `N-ENGON`; 讀 1.1's `nic_do_arm()` returns `-EBUSY` while `nic_engine_on` (present since `edb7122`), and marks `N-ARM` only after a successful arm. What differed from every later arm is the arm's body: 1.1's did not reset the indices (`N1`: `rp=1 rm=1` against `rx_idx 2`), and `1ab93d0` made it reset both and refill the RX ring. That this was the precondition is 推, n = 1, and the silence came after a six-frame burst; old-body arms with the indices skewed did not all silence the console. Since `1ab93d0`, the committed captures (block 46 excluded) hold 78 `RLXFW-N-ARMR` marks in 77 captures from 2026-09-21 to 2026-09-25b, and the console printed after every one of them in the same capture (量 2026-09-26); `recover` also fired where no capture caught its marks (`n_recov_fire`, 25 on `NET-104`'s night). **Not established**: what the silence was — the 21:57 detach reading excludes an adapter drop, not a USB/IP data-path stall while attached, because no round trip through `COM3` was taken while the board was still in the state. `SPEC.md` § 17 `NET-64` 殘留 is ⊘, with its reopening conditions; the driver's own comments that repeat the old reason (`rtl819x-nic.c`, *THREE THINGS IT MAY NOT BE* and *ORDER IS LOAD-BEARING*) are corrected with driver 1.5 (`R6b-2`).

## 🔴 What `R6-5`'s fourth seating did NOT establish — 2026-09-21 (ninety-third segment, seating 32)

Images `s31b` (quiet) and `s31L` (loud, first execution on this silicon),
`RECIPE_ID f179cf21` for both. Three power cycles; the second and third were
**recoveries**, not experiments. Card
`bench/2026-09-21b/PREDICTIONS-B36-block34.md`, results
`bench/2026-09-21b/RESULTS-block34.md`.

| | what would settle it |
|---|---|
| 🔴🔴 **Why the engine stops is still unanswered, but the question is now precise.** Five hypotheses went in and four came out refuted **by direct measurement, against refutation conditions written before power**: the ASIC descriptor pool is not exhausted (`USEDDSC` 18 of a live `S_DSC_RUNOUT` of 244, high-water 30, `DSCRUNOUT` and `SharedBufFCON_Flag` 0 throughout), no port's output queue is congested (`PCSR0`/`PCSR1` both `00000000`, CPU port included), the doorbell is not it (`txstall off` does not recover), and the engine's command state is not it (`engine off ; engine on` does not recover). `STOPTX` is clear and `seen_iisr` carries no error bit. **The engine sits on a descriptor it owns, at its own position pointer, short of nothing, and will not consume it** | The one surviving hypothesis is the ring state, and `arm` changes three things at once. Two are excluded by measurement — repositioning (rung 2 did it alone and failed) and the index reset (software-only) — leaving the OWN-clear. 🔴 **Isolating it needs a build**: no verb on this image clears one descriptor without the others. `NET-71`, `NET-72` |
| 🔴🔴 **`D5` NOT OBTAINED, and for the first time the reason is a mechanism.** `PROGRESS.md`'s `D5` names `iperf3` and nothing else; `iperf3` always opens a TCP control socket; and a TCP connection is the one factor present in every wedge and absent from every non-wedge. Five `iperf3` invocations this seating, five wedges, one of them with the host-side server log **empty** — the control connection never completed | ⚠️ **"A TCP connection" and "`iperf3`" are not separated.** A raw TCP connection with no `iperf3` — `socat` from the host to any listening port — separates them. **The first cell of the next seating, and it costs no power and no image.** `NET-73` |
| 🟢🟢 **`D6` IS MET** — 31.66 minutes, `drop 0/0`, zero console bytes on a `PRINTK=y` image, one unbroken read-only capture; **7.067 GB both ways at 29.761 Mbit/s aggregate**. 🔴 **What did NOT close with it**: the capture ran 1,860.084 s and the flood 1,899.593 s, so **the last 39.5 s are uncaptured — 97.9 % coverage, not whole**. `ping -w` overshoots its deadline while waiting for outstanding replies, measured here at **99.6 s** | One number: the capture's `--seconds` must exceed the flood's `-w` by more than the overshoot. `SPEC.md` `NET-76` |
| 🔴 **After the flood the board answers ARP and not ICMP echo, and it is not `NET-67`.** 量: ARP `REACHABLE`, `n_tx_stop 0`, `tx_stopped 0`, all four `txd` OWN clear, and `nd_stats` advancing in **both** directions across four ping attempts (`rx +6`, `tx +3`). So the TX path works | `/proc/net/snmp`'s `Icmp:` pair, `cat` whole — ⚠️ this image's `busybox grep` has no `/bin/` symlink (`FW-96`), so it cannot be filtered on the board. Host-side `tcpdump` on the bench network is the third route. `NET-76` 殘留 |
| 🔴 **The vendor-driver contrast still could not be taken**, for the same reason as seating 29: `ifconfig eth4 up` returns `SIOCSIFFLAGS: Device or resource busy` because this driver holds a non-shared `request_irq(12)`. **So "the vendor's driver survives what kills mine" remains 推 in this repository 🔄 **2026-09-21 (the ninety-fifth segment, desk): this row's REASON does not hold, and the contrast is available.** 量, the capture the `Device or resource busy` reading comes from — `bench/2026-09-20/X9-eth4.log` — sends `ifconfig eth4 10.1.1.4 up` with **`rlx0` still up**, which `bench/2026-09-20/X11-eth4off.log` confirms in the same seating (`rlx0 … UP BROADCAST RUNNING`). 量 `notes/nic-driver.md:518-519`, seating 28: with `ifconfig rlx0 down` FIRST, the handover **worked** — `12: 2 RLX LOPI eth4`, `UP BROADCAST RUNNING`. 讀 `rtl819x-nic.c:1699-1712`: `nic_ndo_stop()` calls `free_irq(NIC_IRQ, …)`. 讀 `rtl_nic.c:4192-4210`: the vendor's first open calls `rtl865x_init_hw()`, a full hardware re-init including every descriptor base. **`notes/nic-driver.md:986-988` states the narrow version correctly — *cannot be re-measured while `rlx0` is bound* — and `:1428-1430` dropped the qualifier, turning a conditional failure into a property of the driver.** 推 that the handover survives a load; the cell that decides it is three commands and rides an existing boot. `docs/nic-vendor-diff.md` § 8 ④.** | An image in which this driver is not bound, or a shared IRQ　🔄 **2026-09-21 (seating 35): it was taken, on the boot this row's own desk correction predicted it would ride.** Three commands, no extra power. 量 `NET-84`: the handover works, the vendor survives `iperf3`, and the two drivers do not share rings — rlxfw's `/proc` read the engine's bases at `A15B2C00`/`A15B0000`/`A1FCA400` while its own device was down. **So *the vendor's driver survives what kills mine* is 量 in this repository now.** |
| 🔴 **Why the shell stops executing while the kernel and the tty stay alive.** 量, a three-state reading: kernel printing every 1.06 s, tty echoing a 101-character line in full, and `echo RLXFW-PROBE-E` — an ash **builtin**, no `fork`, no `/proc` — returning one line instead of two | 推: `printk` reaches the wire through polled `prom_putchar` while a userspace write needs the UART **TX interrupt**. **Reading `/proc/interrupts`' serial line across the transition settles it; not read.** `NET-75` |
| 🔴 **It is why `busybox reboot -f` cannot recover this fault** — the shell never executes it. 量 twice now: seating 31 captured 7,489 bytes, all ESC; this seating **7,883 bytes, all ESC**. **Two of this seating's three power cycles were spent on that** | The same `/proc/interrupts` reading, plus a kernel-side escape that does not need the shell (the watchdog driver's `/proc` has one, and it also needs the shell) |
| ⚠️ **`seen_iisr` bits 12 and 13 are set in health and in fault and are unnamed** in this driver's bit table | Not chased. `rtl865xc_asicregs.h`'s `CPUIISR` field list　🔄 **2026-09-21 (seating 35): two MORE bits appeared, and which one appears is a discriminator between the fault states.** 量: `0002320E` in `W1`, `Y1` and `Y4` (bit 17), `0001320E` in `W2` (bit 16), and plain `0000320E` in `Y5` and `Y6` — the two lowest-rate wedges set neither. So bits 16 and 17 are load-dependent rather than fault-dependent, and the minimal reproducer sets no new bit at all. Still unnamed, same place to look |
| ⚠️ **Seating 31's `n_rx` anomaly is still unexplained.** The loopback hypothesis that would have explained it is refuted at the desk: `portlist 0x3F` is bits 0–5 and the CPU port is 6 in the `PORTID` namespace and 7 in the TX-descriptor mask namespace, so `0x3F` excludes it under both | Not chased |

⚠️ **And two process failures of this segment, recorded because one of them
nearly became a measurement.** An overwrite refusal was sent to `/dev/null` and
the stale files that the tool had declined to replace were then read as the new
reading — five of nine rows wrong, internally consistent. And a **byte count
was read as a boot**, where the uptime stamps inside the same capture showed the
board had never lost power; `looprun` stopped at `S5` and uploaded nothing.
🟢 Both were caught by something other than the person who made them — the
second by the tool's own abort gate. `RESULTS-block34.md` § 1, § 9.

## 🔴 What the ninety-fifth segment did NOT establish — 2026-09-21 (desk, zero power cycles)

The vendor comparison `D3`'s refutation condition asked for,
`docs/nic-vendor-diff.md`. Everything in it is 讀 of a source file or 量 of a
capture already committed; **nothing was run on the silicon.**

| what is not established | what would settle it |
|---|---|
| 🔴🔴 **`NET-78` is not identified.** Four candidates now exist with sources; none has been measured | § 8 of that file names the reading for each. ① needs the switch's per-port MIB counters across the fault; ③ needs a build; ④ rides an existing boot |
| 🔴 **The whole comparison is single-sourced.** `SOURCES.json:115-118` declares `utessel-edimax` as *"A SECOND independent implementation of the rtl819x network driver … incl. `rtl_nic.c`"*, `needed_by: R6`; 量, it has never been cloned and is cited nowhere, as are `openwrt-rtk` and `vankel-rtl819x-sdk`. **This project's rule that a register reading needs two sources has never been applied to the NIC axis** | Clone the two trees and re-read `rtl_nic.c`'s TX decision against them. Desk, zero power |
| ⚠️ **`rtl_isWanDev(cp)` is not resolved for `eth4`**, and § 2's first row assumes it is a LAN device. If it is the WAN device the vendor uses direct mode with `cp->portmask` = `0x8` — which changes that row but not its point, because `0x8` is one port against rlxfw's six | 讀 the vendor's netif registration; desk |
| ⚠️ **The `NET-82` change is proposed, not costed on hardware.** Following `ph_mbuf` removes `NET-61`'s fault class and simultaneously turns `NET-70`'s `n_dsync` detector from a fault indicator into a normal reading | A build plus a boot, with the counter kept and its meaning re-stated first |
| ⚠️ **Nothing here touched `A3`/`A4`** — the TX pkthdr words 2/3/4 are still absent from the `/proc` dump, and `-DRTL_DEBUG_NIC_SKB_BUFFER` is still not in the board template. Both change `RECIPE_ID` | One image |

🟢 **What it did establish is a reference**: the vendor's TX mode decision
(`NET-81`), the vendor's RX index discipline (`NET-82`), and a two-source
confirmation of the one descriptor field this driver said it could not derive
(`NET-83`). 🔴 **And one candidate was refuted at the desk on captures that
were already in the repository** (`SPEC.md` `NET-78` 殘留, `docs/nic-vendor-diff.md` § 9).

## 🔴 What seating 35 and the loader read did NOT establish — 2026-09-21 (ninety-sixth and ninety-seventh segments)

| | |
|---|---|
| 🔴🔴 **Why the engine stops retiring a TX descriptor.** Untouched, and it is now the **only** question on this line: `NET-88`'s single-variable A/B ran the vendor's own ring-full contract and got `n_tx_recovered` **0** over 1,548 OWN-bit reads, so no TX-side driver strategy masks it | The engine side. `NET-72` left one candidate — `arm`'s OWN-clear — and isolating it needs a build, because no verb on this image clears one descriptor without the others. `NET-67 殘留` |
| 🔴🔴 **The rate story does not close, and the contradiction is in this seating's own data.** `W2` took **1,023 inbound frame/s** (66-byte ACKs, 0.54 Mbit/s) for 72.91 s and did not wedge; `Y5` took **43 frame/s** (1,400-byte UDP, 0.50 Mbit/s) for 8.01 s and did. **So it is not the frame rate.** What is left is byte rate or mbuf occupancy, 推 on two points against one | `bench/2026-09-21e/y5-rateladder.py` with its steps going **down** from 0.5 Mbit/s at a fixed frame size. ⚠️ It lives under `bench/` because it was written for one seating; **if the next seating re-uses it, it belongs in `tools/`** |
| 🟢 **CLOSED 2026-09-21 (seating 36) — permanence is measured to 600 s.** Four readings at +16/+46/+120/+600 s, four OWN bits unmoved, `n_tx` 17 throughout, each paired with a ping, and `n_rx`/`n_irq` advancing exactly +6 per interval as the internal control. `SPEC.md` `NET-99`. *(was: **Permanence over SECONDS is not measured for the `tx_mode 1` arm.** The 1,548 reads are twelve occasions of a 128-iteration tight loop with interrupts off, so they bound recovery on a **microsecond** scale. The board stayed unreachable afterwards — but **no ping was taken after that run**, so for that arm permanence is an inference standing where a reading was claimed)* | Four `/proc` reads at +5, +30, +120 and +600 s after the wedge, each with a ping. It is the first cell of the next seating and it decides which of the two candidate fixes gets built |
| 🔴 **`D5` NOT MET, and `W2`'s number may not be quoted as it.** `D5` names an `iperf3` figure *with its method and its spread over at least three runs*; `NET-85` is **one** run whose control connection stalled at about 10 s, so its 203 MBytes / 23.3 Mbit/s is the average of a transfer that was never terminated properly | Three runs after the fix, on the same ladder that reproduces the fault |
| 🟢 **CLOSED 2026-09-21 (seating 36) — it ran, and the answer is *survives*.** The loader took 31,475 frames up to 8 Mbit/s with ARP answering throughout, and its own receive counter moved +5,544 against 5,534 sent, so the frames reached the engine. `SPEC.md` `NET-96`/`NET-97`. 🔴 **And the row's own premise was wrong**: the loader does not answer ARP at its prompt until `IPCONFIG` has been typed (`NET-95`). *(was: **The loader-prompt experiment has not run, and both of its outcomes change the framing.** 量 `NET-93`/`NET-94`: the loader drives the same four TX descriptors, the same `TXFD` doorbell and the same `0x3F` flood constant, and answers ARP at its prompt on every seating)* | Blast UDP at the board **at the loader prompt** and ask whether it still answers ARP. Survives → the fault is in rlxfw's software; stops → it is below both implementations and `R6-5`'s whole framing, including whether `D5` is reachable on this hardware, has to be rewritten |
| ⚠️ **`seen_iisr` bits 12 and 13 are still unnamed.** Bits 16 and 17 were named this segment (`NET-92`, both run-outs, both excluded); 12 and 13 are set in health and in fault alike and were not chased | `rtl865xc_asicregs.h`'s `CPUIISR` field list, the same read that named 16 and 17 |
| ⚠️ **`R6-6` is unchanged and two of its three DoD clauses are still unreachable before power** — one cable gives one `LinkUp` (thirteen readings), and rlxfw cannot write the VLAN table at all (讀 `rtl819x-switch.c:88-92`, the table is behind the TACI indirect path). The seating read `VCR0`/`VCR1`/`PVCR0`–`PVCR4` again and they agree with seating 33 | `R6-7` writes the weaker true statement into `docs/GATE-RESULTS.md`, with the measurement behind it |
| ⚠️ **Nine of the card's 52 cells did not run**, and `check-predictions` records **43 of 52** rather than being repaired | `bench/2026-09-21e/CORRECTIONS-block38.md` § 1, one reason per cell |

## 🔴 What seating 36 did NOT establish — 2026-09-21 (ninety-eighth segment)

| | |
|---|---|
| 🔴🔴 **Why the engine stops retiring a TX descriptor.** Still untouched, and it is still the only question on this line. This seating removed the engine itself as the difference (`NET-98`: the loader survives 16× the dose on the same power-up) and produced a repair that works (`NET-101`), but a repair is not a mechanism | The run-out mask of § 12.4 is the strongest remaining candidate and 讀 `rtl819x-nic.c:1475-1478` says it **cannot be tested without an image** — the NAPI-complete path ORs those bits back in on every completion. `NET-67 殘留` |
| 🔴 **The recovery has never run from inside the driver.** `engine off` → `arm` → `engine on` was typed at a shell, three `/proc` writes, three times on one evening. There is no detector, and the thing that would call it does not exist | `P2`'s image: a stall detector plus `nic_do_engine(0)`/`nic_do_arm()`/`nic_do_engine(1)`. **Not** `watchdog_timeo` (`NET-55`/`NET-57`, dead code here), **not** `ndo_stop`/`ndo_open` (`X16` re-broke a recovered interface, `NET-58`), **not** `arm` with the engine running (`NET-64` 🔄 2026-09-26: withdrawn as the reason — `NET-64`'s arm ran after `engine off`; `nic_do_arm()`'s `-EBUSY` is what orders it) |
| ⚠️ **The ladder stopped at 8 Mbit/s and nobody knows where the loader breaks.** `Y1` took rlxfw down at 8.6 Mbit/s, so the loader has been tested just past that and no further. *Survives 16×* is a bound, not a ceiling | More rungs, on a seating that has a reason to want them. Cheap: no image, no boot |
| ⚠️ **Bytes 1 and 6 of the loader's synthesised MAC are unexplained.** 量 bytes 2–5 are the `IPCONFIG` address; `0x56` and `0xe8` are constant on every seating that recorded them, which is equally consistent with a constant and with something unit-specific. The `spec-check` `C6` entry added tonight says so rather than claiming the whole value is understood | One seating that sets a different `IPCONFIG` address and re-reads `ip neigh`. Zero power, one command |
| ⚠️ **`R6-6` is unchanged**, and its two unreachable DoD clauses are unreachable for the third seating running. The readable half was read again and all seven values are byte-identical to seatings 33, 34 and 35 | `R6-7` writes the weaker true statement. Unchanged from seating 35's row |
| 🔴 **Three cells of mine were defective and the card did not catch any of them.** Part B's `B1-PING` targets an interface **no card cell brings up** (the bring-up ran as declared off-card cells); the `X17` recovery cell was **133 characters** against `--send`'s 127-character limit and never ran; and the refutation condition written for it — *`n_arm_flush` must MOVE or `arm` did not reach the ring* — is **not a valid discriminator**, because it reads 0 both when `arm` never runs and when `arm` runs and works | `cardcheck` sees neither: it checks commands against the image's applet list and numbers against artefacts, not payload length and not whether an interface has an `up` cell in front of its `ping` |


## 🔴 69 citations into `rtl819x-nic.c` rotted in one segment, and they are DECLARED rather than repaired — 2026-09-22

量 2026-09-22, `tools/citecheck.py` on a clean tree immediately after the
hundredth segment's commit, so `0 suspended` and the verdict is real:
**`C3` 69 rotted citations not on the baseline, `C7` 9 new citations onto a
now-blank line**, against `STABLE 310`.

🔴 **The cause is not the `SPEC.md` rows this segment added** — that was my
first reading and it is wrong. `rtl819x-nic.c` went **2,912 → 3,108 lines**
(ethtool ops, the idle ring, `nic_ph_last_cls`, four new dump fields, the
`txrings` verb, two corrected head-comment items), so **every**
`rtl819x-nic.c:NNNN` citation anywhere in the repository moved. The six lines
inserted into `SPEC.md` shift citations into `SPEC.md` itself and are the
smaller half.

⚠️ **Why it is not repaired tonight.** `CLAUDE.md` records that an automatic
citation repairer *"will eventually edit a number a human sentence on the SAME
LINE forbids editing"* — `SPEC.md` already carries one such number, marked
**這一處不准改號碼** because it quotes what a frozen card said. Neither
`citecheck` nor a repairer can tell a live pointer from a historical
quotation; only the prose can. Sixty-nine of those at the end of a long
session is exactly the shape that produces a wrong edit.

🔴 **What this costs right now, stated rather than discovered later**: the
hundredth segment's commits are **not pushed**, because CI runs `citecheck`
and would go red. `citime`'s ledger will therefore show them missing until the
repair lands.

🟢 **The repair is mechanical and the tool hands over the new line numbers**,
but the rule stands: replace only the digits, check the exact old token is on
the exact old line first, re-derive each new number **by reading it back**
rather than copying it from the checker's message, and read the prose on every
line before touching it. The 9 `C7` cases are the ones to do first: a citation
onto a blank line is already meaningless.

## 🔴 What seating 38 did NOT establish — 2026-09-22 (hundredth segment)

| | |
|---|---|
| 🔴🔴 **The driver still needs a verb to work — a DIFFERENT verb.** | `phfollow` is the compiled default now and it demonstrably took: `A4-BASE` reads `ph_follow 1` and `B3-N` reads `n_ph_used 136` over `n_ph_chk 179`. But `recov_mode` reads **0** at boot, and seating 37's 17 Mbit/s was measured with `recover 1` armed by hand. On this image's own defaults the first `NET-67` wedge is terminal: `B2-IPERF`, with no verb typed on that boot, gave **0.39 Mbit/s for 10.66 s then zero**, 502 KBytes, receiver 0.00 Bytes, and `B3-N` read `n_tx_stop 1`, `tx_stopped 1`, `txd0`–`txd3` = `A15B81D1`/`81E9`/`8201`/`821B` with bit 0 set on all four. *Next:* `recover` compiled on by default, which is one initialiser — and the reason it was not done tonight is that nobody had noticed it was a verb. `SPEC.md` `NET-107` 🔄 **2026-09-22 (101st segment, desk): the initialiser is located so the next segment does not have to find it again, and it is TWO edits rather than one.** `rtl819x-nic.c:775` is `static int nic_recov_mode;` — the declaration with no initialiser — and `rtl819x-nic.c:744-746` is a three-line comment headed **DEFAULT OFF** whose stated reason is that one boot can then produce the broken arm and the repaired arm with nothing else changed. **That reason survives the flip**: `recover 0` typed once gives the same A/B, at the cost of one command. ⚠️ Not done here, and the reason is scope rather than doubt: it changes `RECIPE_ID`, which is a digest over `config/`, so a `config/` that has moved with no image built is a trap for the next card. It rides the next image. 🟢 **2026-09-23 (`P2-2`): done, both edits** -- `rtl819x-nic 1.4`, `:744-746` now headed DEFAULT ON and `:775` initialised to 1, in recipe `a2c56bc8` (`p2q`, `p2l`). A boot prints `RLXFW-N7=00000011`, `ph_follow << 4 \| recov_mode`, so a capture says which defaults it booted with. Not yet read on silicon; `P2-3` is its first boot. |
| 🔴 **The card's own discriminator for that cell was wrong.** | It said a figure in the 0.04–0.07 Mbit/s band would mean the compiled default had not taken. The measured overall figure **was** 0.06 Mbit/s **and** the default had taken. A throughput band cannot separate *the fix is not in* from *the fix is in and something else stopped the traffic*; only a counter on the fix's own branch can, and `n_ph_used` is that counter. |
| 🔴🔴 **`NET-67` is not the three zeroed TX ring bases.** | The strongest structural difference between this driver and the two implementations that do not wedge, killed by a single-variable A/B on one boot: arm 1 gave `Δn_tx_stop` +1 with first miss at **t = 1.138 s**, arm 4 — `tpdcr1/2/3` all reading `A15BE290` = `idle_ring` — gave `Δn_tx_stop` +1 with first miss at **t = 1.124 s**. Same dose, same descriptor state, 1.2 % apart. Eight candidates dead, none replaced. `SPEC.md` `NET-108` |
| 🔴 **The engine-side reading was taken and it does not close.** | `Rcv 0 bytes` on the CPU port's ingress beside `CRCAlignErr` growing +7 for +7 transmitted frames, while port 3's egress also grows +7. The obvious reading — frames leaving with a bad FCS, dropped by the host NIC in hardware — is **refuted** by the host's own `RX errors: crc`, which is 0 before and 0 after. `SPEC.md` `NET-109 殘留` |
| ⚠️ **Every `asicCounter` reading this seating took was AFTER the fault.** | There is no healthy baseline to difference against, so *the fault caused this* and *it has always read this way* are not separated. That is the first thing the residual asks for and it costs no power. 🔄 **2026-09-23 (`P2-2`): "no healthy baseline" overstated it.** Committed healthy readings exist and were not cited: 量 `bench/2026-09-20/D12-AC0`, after a recovery with ping answering, reads the CPU port's `Rcv 0 bytes` with `CRCAlignErr 21` = the driver's `n_tx 21`, and port 3 `Snd 1914 bytes`; `2026-09-20b/X2-asic` (`NET-65`, 217 = 217) and `2026-09-21e/V1-ACNT` read the same way. So *CPU ingress `Rcv 0` while `CRCAlignErr` tracks TX* is the healthy state and not the fault's signature. What is still missing is a fresh boot's same-instant pair of driver dump and `asicCounter`: card A's `P1-N0` → `P1-AC0`. |
| ⚠️ **The ethtool ops were never exercised.** | Declared before power on the card: `config/image-commands.tsv` has no `ethtool` applet and the unit's rootfs has no binary, so `get_drvinfo` / `get_link` / `get_ringparam` are in the image and inert. They are verified statically only. *Next:* a small static MIPS `linkprobe`, the way `/bin/iperf3` already reaches the board. 🔄 **2026-09-26 (`R6b-6`): the caller exists and is in the `r6b6q` image** — `/bin/linkprobe`, desk-proven (`tools/linkprobecheck.py` 37/37, build gates G1–G7), `SPEC.md` `FW-144`; `rtl819x-switch` 1.2 keeps the bit-8 latch `get_link` used to erase (`NET-127`). **Still never executed on silicon**: that is `R6b-6`'s card |
| 🔴 **Two defects were in the frozen card and a third was in my prediction.** | `C2-OFF` sent `recover 0` **and `engine off`** — with the engine off the dose that follows measures nothing; corrected at the bench and declared. The card wrote `NB blast --host/--frames/--size/--rate` when `netblast blast` takes `--target/--src/--dev/--rates/--step-s`; `cardcheck commands` checks that command *names* are invocable, not that their *arguments* are, so it could not catch it. And the boot-capture prediction of 7,717 was **refuted at 7,705** — see the row below. |
| 🔴 **The boot-byte prediction was made on a field the project's own tool normalises because it varies.** | Both captures are 187 lines with identical timestamp bytes (1,728 each); the whole 12-byte difference is the vendor wlan driver printing `tmpReg[0xe]` where `s99c` printed `tmpReg[0x2e]` — **exactly 12 occurrences, 1 byte each, no residual**. `bootbytes`' `K7` control already documents this as the varwidth field. The lesson is not *predict more carefully*; it is *ask the tool to predict rather than copying a previous measurement*. |
| ⚠️ **`D4` is still not met as written.** | The vendor driver is in the image and every hardware initialisation it performs still runs. What is measured is one rung: its `open` refuses. `SPEC.md` `NET-106` 🔄 **2026-09-23 (`P2-2`)**: recipe `a2c56bc8` sets `CONFIG_RLXFW_VENDOR_ETH_OPEN=y` -- `config/host-compat/0007`'s own switch, back at its Kconfig default -- so `re865x_open` is whole again, because `P2`'s `D5` measures the vendor's driver on this kernel through `eth4`. The refusal stays one delta row away, and `s100L` is still the image that measured it. |

## 🔴 What seating 37 did NOT establish — 2026-09-22 (ninety-ninth segment)

| | |
|---|---|
| 🔴🔴 **Why the engine stops retiring a TX descriptor.** Still untouched, and this seating killed its two strongest candidates without replacing either: the run-out mask is not it (`NET-105` ①, the loader's own `0x000007F8` in force with two sources agreeing, and the queue still stopped twice), and the RX pairing is not it (`NET-105` ②, `Y5`'s dose reproduces the stall with `phfollow 1`). It happened **26 times** tonight, including during runs that carried 17 Mbit/s | The engine side, which no seating has yet read: `tpdcr0_pos` across a wedge, and `/proc/rtl865x/asicCounter`'s CPU-port `Snd`. Both were named as the next step after seating 31 and neither has been done. `NET-67 殘留` |
| 🔴 **Why the pkthdr↔mbuf pairing decouples at high frame rate.** 量 is a correlation on two points — 1,094 frames at 43 frame/s with zero divergence, ~141,000 at ~1,500 frame/s with essentially total divergence — on one board on one evening. The mechanism is unread, and the `seen_iisr` run-out bits latching at the same transition is suggestive and not evidence | ① the disassembly of whatever the engine does to `ph_mbuf`; ② a frame-rate bisection at fixed frame size, which turns *between 43 and 1,500* into a number. `NET-103 殘留` 🔄 **2026-09-26 (`R6b-5`): re-owned to `R6b-3`, by its own ④** — `NET-61` 殘留's burst half reopened on block 46's arm C the same day, so the two are read from the same run. It had been set aside because ① cannot succeed (the engine is silicon, and D has no descriptor chapter), and ② names the wrong variable — average rate does not decide it (`bench/2026-09-22b` `C4-DOSE`/`C8-DOSE`, `SPEC.md` `NET-103` 🔄). `SPEC.md` § 17 `NET-103` 殘留 says what was traded and why ④ reopened it |
| 🔴 **`phfollow 1` is not the default and no image has been built with it as the default.** Everything in `NET-102` was measured with a `/proc` switch typed at a shell on one boot. A driver whose correct behaviour requires a verb is not a driver that works | One image with `NIC_RXBUF_PHMBUF` compiled as the default, and a boot that carries the 17 Mbit/s figure with no verb typed |
| ⚠️ **`D5`'s **four** runs come from one evening, one board, one direction — and one of the four collapsed.** 🔄 **2026-09-22（第一百段）：這一列原本寫 `D5`'s **three** runs，而 `notes/nic-driver.md:2038` 逐字禁止那個框法** —— *The three-run figure may not be quoted without the fourth*。**n ＝ 4，其中 `H3` 在第一個區間之後崩掉**；三次群聚是 17.03 / 17.76 / 17.09。⚠️ 而這個錯誤出現在**誠信帳本自己**裡面。 Host→board only; the board was the server in every run that produced a number. The reverse direction was measured only in the `phfollow 0` arms, where it produced nothing | Three runs in each direction on a later seating, with `phfollow` compiled in |
| ⚠️ **One `phfollow 1` run in four collapsed** (`H3`, 6.22 Mbit/s for one interval then zero) and nothing explains it. It is in the table rather than dropped | More runs. At four samples a one-in-four failure rate has a confidence interval that includes almost everything |
| ⚠️ **`R6-6`'s write half did not run.** It was the one high-risk cell the owner authorised, scheduled last, and it was **skipped by decision, not by accident**: two of `R6-6`'s three DoD clauses were already measured unreachable before power (one cable gives one `LinkUp`; rlxfw cannot write the VLAN table, 讀 `rtl819x-switch.c:88-92`), and the vendor `/proc` write path it would have used is already proven by `NET-100`'s three-source read-back. So a success would not have closed anything and a hang would have cost a power press on a board with no spare | `R6-7` writes the weaker true statement. The readable half now agrees across **five** seatings (33/34/35/36/37), all 37 registers byte-identical |
| 🔴 **A fourth line-ending trap, and it is the one this repository had not recorded.** The Bash tool's bare `python` is **Windows** Python, and `open(p, "w")` there defaults to `newline=None`, which translates every `\n` to `\r\n`. 量: one such edit to `PROGRESS.md` converted the whole file -- 2,434 CR bytes where `HEAD` had **0** -- and `git diff --stat` still showed only the 3 intended lines, because git had already normalised it. The warning `CRLF will be replaced by LF the next time Git touches it` was the only signal. `CLAUDE.md` records cp950 and the 3.10/3.12 split for Windows Python and **not this**; WSL's `/usr/bin/python3` has none of the three | Write every file edit through WSL's `/usr/bin/python3`, which is already this project's rule for anything touching `spec-check`. The check is one command: `tr -cd '\r' < f \| wc -c` |
| 🔴 **Four defects were mine and three are repeats of things already in the record.** ① The card put `iperf3` in the **foreground** on the board, which hangs its only shell — seating 31 recorded that exact fix (`&`) and I did not apply it. ② I read *0 bytes on a passive capture* as *the board is hung*, when an idle shell at a prompt reads the same; `CLAUDE.md` states the discriminator (*a command that comes back*) for the USB link and I applied it to the adapter and not to the board. It cost ~8 minutes and no power. ③ Piping a runner into `head` killed it with SIGPIPE at cell 6 of 8. ④ I wrote that `NET-82` was *refuted for this die* on evidence that covered one load | ①–③ are `FW-108`. ④ is corrected in place in `notes/nic-driver.md` § 16.2 and in this file's own record: the refutation was true of the UDP ladder and false of the load that matters |
| ⚠️ **`check-predictions` will not be `39 of 39`.** Parts F and G sit outside the `cells` fence by design, and the card says so in its own § before the fence — so a green on this card is a statement about A–E and not about the seating | The closeout reports F, G and the `X*`/`H*`/`J*` cells as declared off-card work |

## 🟢 `cardcheck` refuses a flash-write command on a card — closed 2026-09-23 (`P2-2`)

*(was, 2026-09-23, one hundred and second segment: no tool refused one;
`classify_command` returned `('LOADER', [])` for `FLW 0 0 0` and for
`EW 8040D4A0 1`, so nothing but a reader stood between a card and a flash
write.)*

量 at the desk, 2026-09-23: `FLW`, `EW` and `EB` in any case, and every
`AUTOBURN` but the exact string `AUTOBURN 0`, each draw one `FLASH WRITE` issue
(`A29`, `A30`); `DW`, `J`, `AUTOBURN 0` and `LOADADDR` are untouched (`A21`). The
one way through is the owner's dated yes on the card itself: an `owner-yes`
fence of `YYYY-MM-DD<TAB><payload>` rows, matched byte for byte and not after
whitespace normalisation, because the loader's tokeniser splits on single
spaces (`A31`, `A33`). A malformed row, a second row for one payload and a row
that permits nothing each fail in their own right (`A32`, `A34`). No
`cardabsent` line and no `--expect-absent` reaches a loader issue (`A35`);
before this change `--expect-absent FLR` took `FLR`'s H601 containment issue
from 1 bad to 0. The two frozen cards' three `EW B800311C …` rows are excused
by (card, exact payload) (`A36`), and `B12` sweeps that list both ways. All 85
cards keep their exit status against `HEAD`'s `cardcheck` run in `HEAD`'s own
tree; only those two print a note per excused row. The mutation suite's new
`W0` requires every kill to turn the case its row names red, and it found two
kills counted since 2026-08-31 that were not kills: `M1` never compiled and
`M11` died of an `AttributeError`. `SPEC.md` `FW-113`.

What this does not establish: that a yes came from the owner (presence and
exactness only). Anything written other than as a single-quoted
`--send '...'`: of 15 flash-verb payloads the committed captures record as
sent, 3 are in such a `--send`, and `bench/2026-08-24c/PREDICTIONS-block3c.md`
cell `D4c` (`EW B800311C 40000`, in a table cell) still passes. Anything about an
upload: the `AUTOBURN` read-back before a `put` is still enforced only by
`looprun`'s `S5b`.

## 🔴 A frozen card declares a day none of its captures happened on — 2026-09-23 (desk)

量 2026-09-23 by `tools/capdate.py`'s card checks (`D5`–`D10`, `CAPD-1`) on
their first sweep. `bench/2026-09-21/PREDICTIONS-B35-block33.md` says
**declared date 2026-09-21**, and all 22 of its dated fenced captures started on
**2026-09-20**, 23:16:54–23:27:08, as did 24 of the 37 dated captures in its
directory that no card fences (23:28:26–23:59:55; the other 13 ran 00:00:15–00:07:47
on 2026-09-21). The card was committed at 2026-09-20 23:16:35; the seating crossed
midnight at `W2-START`, 33 minutes after its last dated carded capture. The
directory check could only report the directory as spanning two days (`D2`);
the card check is what names it. This is the two misnamed directories' failure
(the section headed *Two bench directories are named for a day none of their
captures happened on*), one level down: a date written before power is a
prediction, and this one was wrong by one evening.

The card is **not edited**: a frozen card is never repaired, and `git grep` at
`5972a2a` finds 11 references to it in 9 other files, one of them another frozen
card (`bench/2026-09-21b/PREDICTIONS-B36-block34.md`). It is declared by name in
`capdate.KNOWN_CARD_DATE`, for `D7` and `D8` only, and that list is swept in both
directions like `KNOWN_MISNAMED`.

What this does not establish: which day the seating's owner meant. It says only
that the card's claim and the host clock disagree. The check runs after the
captures exist; before power, a declared date can only be compared with the
directory name, which is the same prediction written twice. `P2`'s seatings plan
not to cross midnight, and split the directory and the card if they do.

## 🔴 What the one hundred and fourth segment did NOT establish — 2026-09-23 (desk, zero power cycles)

`P2-2`: two images, four closed debts, and card A frozen for seating A. **Nothing
was run on the silicon**; every reading below is a desk measurement, a build, or
a prediction the seating will score.

| what is not established | what would settle it |
|---|---|
| 🔴 **That either image boots.** `p2q` and `p2l` passed both declaration gates and the tripwire, their chain is checked by card A's own rows, and a rebuild reproduced them byte for byte — and none of that is a boot | `P2-3`'s first `looprun` round |
| 🔴 **That `/init`'s bring-up leaves `S7`'s terminator intact on a loud boot.** Every committed bring-up was typed by hand on a quiet image; the argument that nothing prints after `exec /bin/sh` is 讀 (no `printk` in either driver, every mark in process context, `CONFIG_IPV6` unset) | The first `P1L-rNN-boot` |
| ⚠️ **`recover` as a compiled default.** `NET-107`'s repair has only ever been armed by hand; `RLXFW-N7=00000011` will say the default took, and only a trial's `n_recov_fire` will say it works unprompted | `P1-TR*`, `P1-UR*` |
| ⚠️ **That the builds between `R3-2` (2026-08-29) and 2026-09-23 wrote nothing into a vendor tree** (`FW-122`). The trees are git-clean today; a write undone since, or a touch that moved only an mtime, is invisible to any check made now | Nothing can, for the past; every build since is watched |
| ⚠️ **That `D2`'s same-mode design removes the confound it was built for.** The vendor is now started by `J 80500000` from a caught prompt, so both columns stream ESC; whether listen-vs-ESC matters at all is what `M1`/`M2` measure, n = 1 each | `P2-3`'s `Z9-D2`, then seating B |
| ⚠️ **`D8` below one second.** With the host's entry flushed before each boot, network up is a bracket one ARP retransmit wide (1.00–1.09 s), and the channel offset is predicted to fail the one-byte criterion on console quantisation alone (~1 ms). Narrower needs a host setting or an `arping` loop, and that is the owner's choice | Seating B, if the owner wants it narrower |
| ✅ **The vendor's per-daemon readiness beyond `boa`** — read 2026-09-25 (111th segment): seating B's card probed 80, 52869 and 52881 every 0.2 s, the list `V1-NMAP` gave; the first success on 52881 came at J+17.08–17.42 s and on 52869 at J+31.27–32.50 s in 9 of 9 vendor boots, 推 `wscd`'s and `miniigd`'s (`NET-118`, `notes/boot-time.md` § 8.8). *(Was: `miniigd`'s port is configured, not compiled in, so card A probed TCP 80 only.)* | Which daemon owns each port on this unit, beyond timing and a related SDK drop: nothing planned |

🟢 **What it did establish**: the build path now refuses an image whose
declaration was never checked (`FW-121`), assembles every image under the
tripwire (`FW-122`), and records the initramfs by content (`FW-123`); a card now
cannot type a flash-writing verb without the owner's dated yes (`FW-113`), cannot
declare a date its captures contradict without `capdate` saying so (`FW-120`), and
cannot carry a host probe record `capdate` cannot date (`hostprobe` 1.2).

## 🔴 rlxfw's NIC driver loses frames it reports as sent, and `recover` cannot see it — 2026-09-23 (seating 39)

量, `P2-3`'s press 1 on `p2q` (`rtl819x-nic 1.4`): of the twelve `iperf3` trials on
`rlx0`, six never completed their end-of-test exchange and three could not
connect (`No route to host`); on the same hardware and kernel the vendor driver
completed all twelve (`notes/nic-driver.md` § 19, `NET-111`, `NET-114`). The
switch's own counters say why: no receive loss the counters can resolve (346,724 =
346,724; 🔄 111th segment: "every frame that entered port 3 reached the driver" until
seating B's same comparison read +2 frames and +134 B across a handover, so the method
bounds a receive loss and cannot show it zero, `notes/nic-driver.md` § 20.4), and at
least 182 frames the driver handed to the engine never
left port 3 (`NET-112`) — the iperf3 server's results, retransmitted and never
acknowledged, and the answers to the host's ARP. `recover` arms only when four TX
descriptors are engine-owned and a fifth frame is offered, so a loss in which the
engine clears OWN never triggers it (`NET-113`).

**What depends on it**: any use of `rlx0` that ends a transfer with a small reply —
a TCP session's close, a request/response, ARP after heavy traffic — can hang
until something else fills the TX ring. A throughput figure from `rlx0` is valid
only while data flows, and `P2`'s rlxfw receive figure has n = 1: `TR1`'s 16.953
Mbit/s, read in seating B from the board's own server log, the host having no
`receiver` line (`NET-116`; 🔄 111th segment: "n = 0 (no `receiver` line exists)"
until then). **What settles the mechanism**: § 19.5's experiments E0–E5, zero
flash, one power press. 🔄 111th segment: block 45, `R6b`'s first bench block, ran
E1–E6 and E10 and placed the loss in frames of lengths the engine was not given
(`NET-119`); the mechanism is `R6b`'s, its eight candidates all 推
(`notes/nic-driver.md` § 21).

## 🔴 What seating 39 did NOT establish — 2026-09-23 (the one hundred and fifth segment)

Card A ran whole: twelve presses, 223 of 223 cells, three map brackets identical to
the prediction, `D2` held (`CLK-34`). Four of the 104th segment's open items above
are answered: both images boot (7,948 B loud, 2,117 B quiet, as predicted);
`S7`'s terminator held on every loud boot; `recover` fired unprompted seven times
(and cannot see the loss that mattered, `NET-113`); and the same-mode design gave a
mode control inside ±10 ms both cold and warm.

| what is not established | what would settle it |
|---|---|
| ✅ **Whose clock carries `CLK-32`'s factor, for seatings A and B** — settled 2026-09-25 (111th segment): the host's. Seating B, stamped on `CLOCK_MONOTONIC_RAW` with `timesyncd` stopped, put the loader's `booting` at 0.356060 s warm (n 13) and 0.355865 s cold (n 12), inside the registered ±0.5 % of 0.35625 s (`CLK-43`). How seating A's came about: 🔄 2026-09-23 (106th segment): inside seating A it is the host — four independent references put its `CLOCK_MONOTONIC` 1.4 % slow at 15:52 and 3.1 % by 18:10, and corrected for it the loader does not drift (`CLK-35`); the host's tick is being slewed while `timesyncd` steps realtime (`CLK-38`) — 🔄 107th segment: by WSL's own `chronyd`, which steers the guest to Windows' clock while `timesyncd` pulls it to NTP; stopping `timesyncd` ended the slew. 🔄 108th segment: `timesyncd` slews as well as steps — through the kernel PLL while its offset is small, a third rate term that ran `CLOCK_MONOTONIC` up to 2.8 % fast (`CLK-39`) — and steps only above about 0.4 s. For earlier seatings it stays 推: the pre-registered retro test failed its own control and did not test it (`CLK-32`) | For earlier seatings: nothing planned |
| ✅ **`D2` corrected for that clock** — settled 2026-09-23 (106th segment): warm +0.19 ms, cold +0.15 ms, `D2` holds raw and corrected (`CLK-34`, `notes/boot-time.md` § 7.1) | — |
| 🔴 **Why `rlx0`'s frames are lost below the DMA engine** (`NET-112`). 🔄 2026-09-25 (111th segment): block 45 ran E1 and E2 and placed it — the engine hands the switch frames of lengths it was not given, 678 `JabberErr` at the CPU port in E2, while 60- and 1,514-B replies went through clean (`NET-119`, `notes/nic-driver.md` § 21.2). *(Was: where below the DMA engine, and why.)* 🔄 2026-09-26 (112th segment): block 46, one length per bracket, was a failed reproduction by the gate's own clause, and `D1` — the stage — is recorded undetermined (`NET-123`, `notes/nic-driver.md` § 22) 🔄 2026-09-26 (`R6b-2`): `rtl819x-nic` 1.5 carries `txlen`, `txoff`, `txrb`, `sweep` and `swclear` (a wire sweep over more than one length is refused at every `txlen` but `vendor`); at its defaults every function it hooks performs 1.4's stores in 1.4's order and every other driver function is instruction-for-instruction 1.4's (`storeseq`, `NET-125`), so every image that types no 1.5 verb carries the fault unchanged. Nothing has run on the silicon. 🔄 2026-09-26 (block 47, `R6b-3`'s first card): 1.5 ran on the silicon. At `txlen vendor` E2 read 220 of 220 twice and the wire sweep read `JabberErr` 0 over 1,455 lengths, while 1.4's lengths on the same boot answered 145 of 1,327 and jabbered at the 19 predicted lengths — `D2`'s first boot of two (`NET-128`, `NET-129`, `notes/nic-driver.md` § 25). The default is still 1.4's, so every image that types no 1.5 verb still carries the fault. | `R6b-3`'s card 2: `D2`'s second boot and `D1`'s per-length stack arm; the mechanism stays 推, `M1`-cover8 the one rule left standing (`NET-129`) *(was: the eight candidates of `notes/nic-driver.md` § 21.6, all 推; next `R6b-2`'s image A/B)* |
| ⚠️ **rlxfw's receive throughput, beyond n = 1.** 🔄 2026-09-25 (111th segment): the server's own report was read — seating B's `TR1` logged 16.953 Mbit/s received over 30.01 s on `rlx0` (`NET-116`), one trial; the host still has no `receiver` line, and the UDP trials lost 86.6–87.8 % above the driver (`NET-117`). *(Was: no `rlx0` board-receive trial produced a `receiver` line.)* | A driver that completes the exchange; more trials scored on the server's own report (`R6b`'s regression) |
| ✅ **`D7`, § 3.7's segments, and the vendor's `J` → `boa` miss** — second-sourced 2026-09-23 (106th segment): a parser sharing no code with the tool agrees to the microsecond; four statements of the first computation corrected (`CLK-37`, `notes/boot-time.md` § 7.6) | — |
| ✅ **The vendor's `D8`, `D4` readiness beyond `V1`, and `P3-TCPD`'s check of the `D8` reconstruction** — computed 2026-09-23 (106th segment) for all nine vendor boots; the reconstruction holds on the one frame-checked boot, with four stated limits (`notes/boot-time.md` §§ 7.3, 7.5, 7.7) | Two inferences it left are seating B's tests (§ 7.7) |
| ⚠️ **Anything from `P1-UR3` on `rlx0`, cleanly**: the host re-attach bounced port 3's link first (`bench/2026-09-23/CORRECTIONS-block42.md` § 5.1) | Seating B |
| ✅ **`D3`** — settled 2026-09-25 (111th segment): on a second calendar day 134 of the 140 numbers the frozen list called stable reproduced within ±10 % on both columns, and none of the six misses is a row of the segmented table or `D7`'s Δ (`CLK-48`, `docs/boot-time-table.md` § 10); the six are carried as `D3-MISS` | — |

## 🟢 `cardcheck` refuses a HOST cell its own tool rejects — closed 2026-09-24 (`P2-4`, `FW-124`)

*(was, 2026-09-23, one hundred and fifth segment: nothing checked a frozen card's
`HOST` cells; twice a card carried one whose own tool rejected its arguments,
found only at the bench — block 41's `netblast` options and card B44's `Z9-D2`.)*

量 at the desk, 2026-09-24 (108th segment): `cardcheck commands` now reads every
`HOST <prefix> :: <cmd>` line of a card, inside a fence or not, with the grammar
of `tools/cardrun.py` — the runner that executes cards and the grammar's one
owner (`FW-132`) — and puts each project-tool command to that tool's own
`build_parser()` and `refuse_args()` in-process, so the reason printed is the
tool's own. Over the 86 committed cards it refuses exactly the twelve cells the
107th segment's research predicted before any code existed; they are excused by
(card, cell, a fragment of the refusal) in `FROZEN_HOST_CELLS`, swept both ways
by `B13`. Every card keeps its `commands` and `numbers` exit status against the
tool at `0dfb2dd`. `SPEC.md` `FW-124`.

What this does not establish: anything about a system command's arguments
(177 in the corpus are counted and named, never checked); anything a tool checks
only after `refuse_args` — routes, interfaces, the iputils floor, image digests,
records that already exist; what a cell means (a correctly spelled `--rates 43`
in Mbit/s passes); that each tool's `refuse_args` is complete.

## 🔴 What block 46 did NOT establish, and what it pinned — 2026-09-25 (`R6b-1`, the one hundred and twelfth segment)

Block 46 (`bench/2026-09-25c/`, one press on `p2q`) put each of E2's eleven lengths in its
own bracket over four arms. Its record is `notes/nic-driver.md` § 22.

**The stage (`D1`) is undetermined.** 量 The reproduction control failed: arm A1 read FAULT
at the controls A1-03 and A1-07 (60 B) and A1-13 (1,514 B), each after a bad length with no
re-arm. By the gate's own clause `R6b-1` is a failed reproduction and none of its other arms
localizes anything (`NET-123`). **What depends on it**: every statement of *where* the
length fault sits stays 推 until `R6b-2`'s image A/B; the fix cannot be aimed from this block.

**The host stopped reaching the board mid-block** (`NET-124`). 量 From A2-03 through the last
bracket, port 3 received nothing — its receive counters identical in 56 of 56 reads — while
the host adapter counted 175 frames sent in A2-03…A2-19 and 45 in D, with its link up and the
board still reaching the host in B. So A2-04…A2-19 and all of arm D tested nothing. Which
element failed is 推: the host adapter's transmit path under usbip is the leading candidate,
and the board side is not excluded, because port 3's link state was not read. **What depends
on it**: any host-stimulus reading on this bench, until a card checks host → board liveness
before every arm and keeps the host's kernel log from before the press (`SPEC.md` § 17,
`NET-124` 殘留). The same shape in the same direction was `NET-54` (2026-09-19); `R6b-3` owns its § 17 row beside this one.

**`FW-49`'s wrap threshold is pinned: `T` = 79** (量). The four 79-character sends,
`C-08-L1511a`, `C-09-L1512a`, `C-10-L1513a` and `C-11-L1514a`, each fold: their echo carries
`\r\r\n` after the 78th character and the 79th follows on the next line, and each command
acted (two looped frames each). The three 78-character sends (`C-05`…`C-07`) and the four
77-character sends do not fold. A 78-character send ends its echo with `\r\r\n` rather than
`\r\n` — all 23 of the corpus's 78-character sends do (19 of 2026-09-10, 1 of 2026-09-14c, block 46's 3): 推 the 80-column wrap landing just after
the last character, so a `\r\r\n` right after an echo is not only the loader's. Second source,
`capfield wrapcensus` at `873a471`: 2,844 `.meta.json`, 2,712 with a `sent`, 2,485 classified;
79 characters 4 wrapped and 0 not, 78 characters 0 and 23; "the threshold `T` is in (78, 79]
… `T` is pinned". Its exceptions also correct this file's 2026-09-16 paragraph: besides the
loader's 119- and 127-character `EW`s, five shell sends of 2026-09-21 do not fold —
`X17-SW5` (80), `X17-UP5` (96), `H6-REC`, `H7-REC2` and `X6-REC` (103); 推 `FW-47`'s
echo-interleaving family, not read further. Not established: the mechanism, which stays 推
(78 usable columns beside the two-column `# ` prompt; busybox's line editor was not read).

**`n_writes 0` carries no information** (讀, `FW-142`): no committed `rtl819x-spi` increments
the counter, so the flash claim of every seating rests on the commands issued and the map
bracket, never on it (`notes/spi-mtd-driver.md` § 11.6).

## Closed since `v0.2` was tagged

**Kept rather than deleted, so this file can be read against the copy at the `v0.2` tag.**

| | |
|---|---|
| 🟢 **CLOSED 2026-09-01 — the per-gate ledger is public.** *(was: `study/weekly-results.md` is not in the public repository)* | 量: `.gitignore:17` is `study/`, and `git ls-files study/` returns nothing. `CHARTER.md` §110 rule 3 asks for one entry per closed gate in that file, and four are owed (`R2a/b/d`, `R1h`, `R3`, `P4a`). **Owner's ruling 2026-09-01: leaving it ignored is acceptable for now.** `P4b-gate` ③ owns the decision. 🟢 **2026-09-01, `P4b-2`:** the file moved to `docs/GATE-RESULTS.md` — committed, English, one entry per closed gate, and its name now says what its unit is. `study/` stays gitignored; the owner's ruling about the directory and the requirement on this artefact turned out not to be in conflict once the artefact stopped living in that directory. Five entries: `R1-gate`, `R2a/b/d`, `R1h`, `R3`, `P4a`. `S0` and `R0` are deliberately not backfilled, with the reason at the top of that file. |
| 🟢 **CLOSED 2026-09-01 — version → contents has one committed owner.** *(was: two owners disagreeing on six of six shared rows)* | `plan/CHARTER.md` §88 is authoritative and is **gitignored**, so a public reader cannot follow a pointer to it; `PROGRESS.md`'s Release clock restates it and is stale. This file and `CHANGELOG.md` now own the contents of the versions that have actually been released; the map of *future* versions still has the defect. `P4b-gate` ① owns it. 🟢 **2026-09-01, `P4b-1`:** `README.md` § *Which gates make which version* is the owner. `PROGRESS.md`'s Release clock dropped both restated columns and keeps only `Shipped`; the planning material's table dropped its contents column and keeps only its estimates; and `CHANGELOG.md`'s `v0.2` section stopped pointing at a gitignored file. 🔴 **The repair also found that the `Target` column beside `Contents` was a restatement too** — it carries the planning material's own ×1.8 multiplier — and it agreed on only two of six rows while never having been flagged. |