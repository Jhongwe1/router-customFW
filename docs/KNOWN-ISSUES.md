# Known issues

**What this repository does not establish.**
The project's charter asks for a known-issues list beside every release. This is
that list, and it is written to the same standard as everything else here: each
entry names what is *not* true, what was measured instead, and which gate changes
it. Nothing below is a plan; the plan is `PROGRESS.md`'s gate board.

⚠️ **This file on `main` is the CURRENT list, not `v0.2`'s.** A release's list is
the copy at that release's tag, which is frozen; this one keeps moving. Anything
that has since been closed is at the bottom rather than deleted, so the two can
be read against each other.

Marked the same way as the rest of the repository: **量** measured on the device
· **讀** read out of code, a dump or a document · **推** inferred, pending a
measurement.

---

## The firmware does not exist

| | |
|---|---|
| 🔄 **Nothing of mine has driven a peripheral — and as of 2026-09-03 21:20 that is no longer true, so this row now says what IS still true instead.** 🟢 **`rtl819x-timer` executed on the silicon**: it programmed `TC1DATA` and `TCCNR` (`tccnr` `C0000000` → `F0000000`, exactly bits 29/28), registered a `clocksource` the kernel listed as `rtl819x-tc1`, was read fourteen times, and unwound both writes on disarm — twice, the second after a 703-second arm. **So a peripheral register block on this SoC has now been driven by code of mine.** 🔴 **What is still true, and is the narrower claim this row keeps**: nothing of mine has driven a peripheral that the system *depends on*. The timer ran at **rating 0** precisely so the kernel would not switch to it — 量, `TM-4b` read `jiffies` while `TM-4a` listed both — and `GIMR` bit 9 was read and never written, so **no interrupt of mine was ever delivered**. `R5-3` is the step that changes the first of those and `R6` the second; **`R5-2` must not be read as having changed either.** 🔴 **2026-09-04, seating 12: the sentence in bold above expired at 14:07, and the clause before it did not.** 量: `irq_count` **119,818**, `irq_spurious` 0, `irq_stuck` 0, a `/proc/interrupts` line `25: … ICTL rtl819x-timer` that `EX-0` measured absent beforehand and `EX-19` measured absent again afterwards, and a delivery rate matching `hz_used / period_cycles / hz_kernel` to **0.02 %** at two periods 16× apart (`SPEC.md` `IRQ-08`). **`GIMR` bit 9 is still never written by this driver** — `request_irq` asks the irqchip and `bsp_ictl_irq_unmask` does it, 量 `00209100` → `00209300` and back down on `free_irq`, three times each. **What survives is the narrower claim this row exists to keep**: nothing of mine drives a peripheral the system *depends on*. `rating` read **0** in all eighteen dumps and the time base was `jiffies` throughout, deliberately — that is `R5-3b` ⚠️ **(split on 2026-09-06 into `R5-3b-1`, the `/proc`-driven handover, and `R5-3b-2`, arming at boot)**, and `R5-3a` must not be read as having changed it. 🔄 **2026-09-06: BOTH halves of `R5-3b` closed, so the bold sentence above expired again — first at 03:11 and then at 14:48 — and this row did not follow for two segments.** 🟢 **The system tick is this driver's, and from boot**: a `clock_event_device` at rating 300, the tick core exchanging the devices on eleven independent boots (`ce_mode=2`, `ce_handler` `80036D50` → `80036FC4`), and *before userspace* proved by an ORDERING rather than a field — `RLXFW-TA8` at byte 887 precedes `RLXFW-B10` at 925 in the same capture, on all eleven. 🔴 **So the narrower claim has to move again, and what survives is narrower still: the CLOCKSOURCE half is untouched.** `rating` read **0** in every dump of both seatings and the system's time *source* is still `jiffies`; only the *tick* is mine. ⚠️ And the interrupt-loss mechanism `IRQ-13` works around is **not isolated** — the driver moves its pre-check window rather than explaining why the vendor's NIC initialisation costs 11 of 585 interrupts. 🟢 **Found by the thirty-seventh segment's closeout enumeration, not by the segments that made it stale** — which is the case for asking every owner file what moved rather than asking which ones look relevant. 🔴 **2026-09-06, seating 13: that narrower claim expired at 03:11.** `R5-3b-1` registered a `clock_event_device` at rating 300, the tick core exchanged the devices **three times on three independent cold boots** — `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4` — and from that instant `jiffies` advanced because of an interrupt this repository's own source produced. 🟢 **And it is not asserted, it is caused**: `cereload` changes TC1's reload and the kernel's clock follows, six rows over five reloads, ratios `1.0000 / 2.0000 / 1.0000 / 4.0000 / 1.0000 / 10.0000`; at 20000 the shell answered a `cat` after a `sleep 5` that took **50 real seconds**. `P3-7` then shows the two interrupt lines at different rates for the first time — the vendor's 3,009 against my 301 over 30.10 real seconds, with `Δjiffies` = **301**. **So the system now depends on a peripheral driven by code of mine.** ⚠️ **What is still true and is narrower again**: the dependence is created by a `/proc` write **after userspace exists**, never at boot — every one of the three boots came up on the vendor's tick and was handed over by hand. And the **clocksource** side is untouched: `rating` read 0 in every dump of this seating too, and `available_clocksource` was never asked to change. Arming at boot is `R5-3b-2`; **`R5-3b-1` must not be read as having done it**. 🔴 **2026-09-06, seating 14: that sentence expired at 14:48, and it is the last of this row's five successive narrowings.** `R5-3b-2` arms the timer from inside the kernel: `arch_initcall` does `arm`/`ackip`/`reqirq`, `late_initcall` takes the pre-check window and registers the rating-300 `clock_event_device`. **Ten boots** (`M1`…`M10`, all warm resets driven by `busybox reboot -f`) **plus an eleventh from a cold power-on whose every field is byte-identical**, image `ea6ee537`, driver 4.1 — `boot_done=1`, `ce_live=1`, `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4`, the rating-99 negative control registered and never called, `irq_spurious`/`irq_stuck`/`ce_hw_bad`/`ce_badmode` all 0, zero lost ticks over 263.73 s three ways with residual 0. 🟢 **And *before userspace* is proved by an ordering rather than by a field**: `RLXFW-TA8` (the instant the registration returned) precedes `RLXFW-B10` (`init_post()`, immediately before the branch into `/sbin/init`) in the same capture, on all ten — byte 887 against 925 on `M1`. 🔴 **The first version of it refused its own handover, twice, and that refusal is the seating's most useful reading**: 4.0's pre-check window spanned the vendor's NIC initialisation, over which TC1 delivers **574 of 585** interrupts — 1.88 % against a 1 % tolerance — while the steady state loses **1 in 14,385**. The tolerance was not widened; the window was moved. `SPEC.md` `IRQ-13`. ⚠️ **What is still true and is narrower again**: the **clocksource** half is untouched — `rating` read 0 in all ten dumps and the system's time SOURCE is still `jiffies`; only the *tick* is this driver's. And nine of the ten boots are warm resets driven by `busybox reboot -f` from the host (`FW-37`); one power-on started the seating. **`R6` is still the gate that makes a peripheral of mine carry the network.** *(This row read "There is no driver of mine" until 2026-09-03, and that sentence stopped being exact at `R5-1`: `config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c` exists, compiles, and is linked into the image — 量, `rtl819x-tc1` present once in `vmlinux`, absent from every image built before it. **It has not executed.** It also writes no register at boot and registers nothing until a shell asks it to, so even on the board it is inert until `R5-2`.)* 🔄 **The two sentences inside that parenthesis are kept verbatim and both expired on 2026-09-03**: it executed, and it stopped being inert the moment `TM-3` wrote `arm`. **The half that survived is the one that was doing the work** — *writes no register at boot, registers nothing until a shell asks it to* — 量, `TM-1` read `state=idle`, `tccnr` at its init value and `available_clocksource` naming only `jiffies`, on a board that had been running my kernel for 30 s. 🔴 **2026-09-03: and it has a known defect, found at the desk before it ever ran.** Its `tc1_ext_trusted` flag reports **1** on sampling gaps longer than one counter period, because the masked difference aliases back into the trusted band — 量, a 60 s gap loses six whole wraps and the flag still says trusted (`SPEC.md` `CLK-22`, `PROGRESS.md` `TMR-1`). **Nothing reads that field yet**: `R5-2`'s card quotes `tc1_cycles` and unwraps outside the kernel, and predicts the false `1` so the defect is confirmed on silicon rather than only on paper. The fix is `R5-3`'s, because `config/` is the source of `RECIPE_ID` and touching it invalidates the staged image. 🔄 **2026-09-03, seating 11: confirmed on silicon — mechanism exactly right, threshold wrong by 71.43× — and a SECOND defect found that the desk analysis did not identify.** The aliasing did not happen at 60 s (under Linux `CDBR` divides by 1000, so one period is **671.07 s**, not 9.395016 s); it happened at **703 s**, where the true gap of 140,693,532 counts was accumulated by `tc1_ext` as **6,475,804** — exactly that value mod 2²⁷ — with `trusted` still **1**. 🔄 **2026-09-04 (`R5-3a`): this clause used to name `tc1_ext_gap_max` **6,475,672** as the aliased value and that was wrong by 132.** 量, recomputed from `TM-5b-arm`/`TM-5b2` by program: `140,693,532 mod 2²⁷` is **6,475,804**, which is both the wrapped TC1 delta `(6,477,665 − 1,861) & MASK` and `Δtc1_ext`; `gap_max` reads 6,475,672 because `tc1_ext_reads` goes 1 → 3 across that arm, so it is the **largest single** inter-read gap of two, not the span (the other is 132). **The mechanism is unchanged and the alias is exact** — what was lost is precisely one period, 134,217,728 counts. The clause had been copied into nine committed files. 🔴 The second defect: 讀 `rtl819x-timer.c:476-477`, the **only** call site of `rtl819x_ext_advance()` is inside `rtl819x_tc_read_proc` and guarded by `armed`, so **`tc1_ext` is a sum over the intervals somebody happened to read `/proc` in, not an extension of the counter** — 量, `TM-5c`, 462 s with no reader: `tc1_cycles=98,840,142` against `tc1_ext=6,477,776`, `trusted` **1**. ~~Both fixes are `R5-3`'s.~~ 🟢 **2026-09-04 (`R5-3a`): both are written.** `tc1_ext_trusted` is decided in **jiffies** now (`Δjiffies < period_jiffies`, which is the owner's `Δjiffies × TICK_NSEC` rule with both sides divided by `TICK_NSEC`), and `tc1_ext` is advanced by a `timer_list` at a quarter of a period plus by the interrupt handler. 🔴 **This row does not close**: nothing of version 2.0 has executed, and the cell that closes it is `TI-3` on `bench/2026-09-04/PREDICTIONS-B10-block9.md` 🟢 **— and it ran. Version 2.0 executed; both fixes are confirmed on silicon.** `tc1_ext_trusted` is decided in jiffies and reports **0** at period 8, correctly: `gap_max_j = 1` against `period_jiffies = 0`, so a 255-count mask sampled every 10 ms cannot be trusted and the driver says so — the defect that used to report `1` on an aliased gap now reports 0 on an aliased configuration. At period 12 and 20 it reports **1** with `gap_max_j = 1` under a `period_jiffies` of 2 and 524. And `tc1_ext` is advanced with **nobody reading `/proc`**: `TI-3` slept 8 s and returned `tc1_ext_ticks = 66`, `tc1_ext` within 0.018 % of `Δjiffies × hz_used` over 87 s. *(This clause is kept rather than deleted: it named the cell that would close it, and the cell is what closed it.)*. ⚠️ `R5-3` was split on the same day into `R5-3a` (the interrupt path) and `R5-3b` (clockevent and the rating); these fixes ride the `R5-3a` image. 🔴 **2026-09-08, seating 17: a SIXTH narrowing is due, and this time the dependence is of a kind none of the five above describes.** `rtl819x-wdt`'s `BOOTGUARD` arms the hardware watchdog at `late_initcall` and feeds it from a kernel timer, so **from that instant the board reboots unless code of mine keeps running.** That is not "the system uses my peripheral"; it is "the system does not survive my peripheral stopping", which is a strictly stronger dependence than the tick — the tick could in principle be handed back, and this cannot without a `stop`. 量: nine bites this seating, every one confirmed by the loader's own `Reboot Result from Watchdog Timeout!`, and `R2-SO3`/`R2-SO6` show the board resetting on schedule when the feed is deliberately starved **with the vendor's wlan driver up**, so nothing else is feeding it. ⚠️ **What is still true and is narrower again**: the **clocksource** half remains untouched (`rating` 0 in every dump of this seating too), and the watchdog carries no *data* — the network still runs entirely on Realtek's code, so `R6` is unchanged as the gate that moves this row's second column. ⚠️ And the dependence is **opt-out by design**: `bootguard=0` as a module parameter, or `stop` on `/proc`, returns the board to a state where nothing of mine can reset it — which is why this is recorded as a narrowing and not as `R6` arriving early. | `R3`'s D5 — a `ping` with four replies, confirmed on the host's own capture in both directions — went out through the **vendor's** `rtl819x` driver, in the vendor's own configuration. A kernel of mine boots and reaches userspace; every peripheral it touches is Realtek's code. **`R6` is the gate that changes this sentence, and `R3` must not be read as having changed it.** |
| 🆕 **2026-09-06, seating 15 (`R5-4`): a second driver of mine ran on the die, and it establishes LESS than the timer did — deliberately.** | 🟢 `rtl819x-gpio` registered a `gpio_chip` at `subsys_initcall` on **ten boots**, `gpiochip_add()` returning 0 every time, ten boot captures **byte-identical** at 1,184 bytes, and `n_writes` **0** in every dump of the seating. 🟢 Its guard refused on the silicon at two layers with two errnos — `-EPERM` from `.direction_output` and `-ENODEV` from `.request` — with all three register XORs `00000000`. 🔴 **What it does NOT establish, and none of it is a surprise because the card said all five before the board was powered**: which port letter bit 5 belongs to (so the `.dts` node and the binding `R5`'s DoD asks for still cannot be written); whether bits 2, 4 and 6 are usable (the vendor treats them as GPIO, this driver refuses them on purpose); **any output at all** — `RTL819X_GPIO_ALLOW_OUT_MASK` is `0` and no cell changed it; and any GPIO interrupt — `.to_irq` is `NULL`. ⚠️ **The line it would use is already written down and was not touched**: `GPIO_ABCD` is bit 16 of the global controller (`docs/interrupt-map.md`), so what is missing is the work, not the address. ⚠️ **Nothing depends on this chip.** No consumer is bound to it; `R5-7` (leds-gpio) and `R5-8` (gpio-keys) are the steps that would change that, and `R5-4` must not be read as having done it. 🔴 **The clocksource half of the row above is still untouched** — `rating` read 0 again and the system's time SOURCE is still `jiffies`. |
| 🆕 **The vendor's factory-reset path is now READ and partly measured, and that narrows a safety question rather than closing it.** | 🟢 量/讀 2026-09-06: in **Linux**, holding the reset button runs `rtl_gpio_timer` once a second; a 2–4 s hold sends SIGTERM to PID 1 (which this image's PID 1 ignores — `FW-37`) and a **≥ 5 s hold writes ASCII `'1'` into `default_flag`**, which in this image has exactly two readers and both are `/proc` handlers. Confirmed on the die: `/proc/load_default` read `0`, then `1` after a timed hold. **So the kernel does not write flash on this path; the vendor's userspace would, and this image has none.** `SPEC.md` `FW-40`. 🔴 **This says nothing about the LOADER**, which is where `R5-4`'s card drew its line and where a factory reset would actually be a flash write. That question is open and untouched. 🔴 **And no `FLR` bracket ran this seating**, so the flash claim did not move: still 1,024 of 4,194,304 bytes, 0.0244 %. ⚠️ Seven of the nine functions that touch `PABCD_DAT` — `autoconfig_gpio_init`, `autoconfig_gpio_off`, `autoconfig_gpio_on`, `autoconfig_gpio_blink`, `autoconfig_gpio_slow_blink`, `read_proc` and `rf_switch_read_proc` — were **seen and not read** (🔴 *this said TWO, from a count taken over five of eleven resolved addresses*), and `sys_bonding_type()`, the gate on the whole button path in *both* the loader and this kernel, is not understood by anything here. |
| 🔴 **No userspace of mine.** | The initramfs is built from **this unit's own extracted rootfs** — busybox, uClibc, and the symlinks around them are the vendor's binaries, declared one row at a time in `config/rlxfw-initramfs.tsv` with an owner per row. That is deliberate (`R3`'s Decision B: if the shell does not come up, the shell is not the new thing) and it means nothing in userspace is mine. `R7`. |
| ⚠️ **Nothing has been written to flash, and that is a weaker sentence than it sounds.** | See the next section. |

---

## The flash claim, and why it is not "zero bytes written"

| | |
|---|---|
| 🟢 **2026-09-01: the bracket now also says a scripted reset writes nothing to those windows, and that is a sentence `R4`'s unattended loop leans on.** | Seating 9 ran the four windows after one cold boot and **twenty watchdog resets**, with four RAM destinations no `FLR` in this project had ever used — so `MEM-17`'s retention path could not pre-fill them with the answer, which is what voided seating 8's cycle 6. Fourteen comparisons, all as predicted: four read-backs equal to the reference, four pre-reads differing, two positive controls. 🔴 **The percentage did not move: still 0.0244 %, still 6.3 % of `H601`, still no full re-dump.** |
| 🔴 **"No flash-write command was issued" is not "not one flash byte is written".** | `RUNSHEET` `G8b` forbids the second without a full re-dump hashed against `FLS-14`, and no seating has run one. What exists is a bracket: four 256-byte windows read back before and after, over two power cycles. |
| 量 **The bracket reaches 1,024 of 4,194,304 bytes — 0.0244 %.** | All byte-identical to the 2026-08-16 reference dump. It **cannot** see a write outside those four windows, and it cannot see two writes that cancel. |
| 量 **`H601` — this unit's MAC and radio calibration, the region a wrong write cannot be undone in — is covered to 512 of 8,192 bytes: 6.3 %.** | The other 93.7 % is unchecked **by this project's `FLR` bracket**, and the qualifier is the whole sentence. 🔄 **2026-09-07 (fortieth segment): without it this row says of the DEVICE what is only true of the BRACKET** — `SPEC.md` `FLS-25` compared the full 8,192 bytes against the reference dump six times over 2026-08-17..19 and found **zero** differing bytes. ⚠️ **That does not move the 6.3 %**: those six re-reads are one instrument, they are upstream-era artefacts predating rlxfw's first power-up, and none of them is an `FLR` bracket read at a seating. 🔴 **`CLAUDE.md` already made exactly this correction for exactly this region on 2026-08-30** (*true of rlxfw's own bracket, false about the device*) and this sibling row never received it. This region is why the project is zero-write through `R9`. |
| 🟢 **The bracket does have a negative control.** | Every destination is read **before** its `FLR`; on the round that established this, all eight pre-reads differed from the expectation, so *the `FLR` wrote* is measured rather than assumed. One earlier round was **voided** by that control when DRAM retained a previous cycle's contents across a power cycle. |
| 🔴 **2026-09-08 (seating 16): the sentence above is now known to be FALSE for the DEVICE, and that is worse than unmeasured.** | `SPEC.md` `FLS-26`. `rtl819x-spi` digested `H601`'s complement on the silicon — `digest_bytes 4186112`, `h601_hashed 0`, over a traversal of all **4194304** bytes — and got `a1673578…100d49eb` where `FLS-24` says `a9916fd8…4ce3cba`. **The constant is not the thing that is wrong**: the same range recomputed at the desk from **both** dump files by an independent implementation gives `a9916fd8…` exactly. So flash content has moved since 2026-08-16. 🔴 **Attribution is not established and this seating could not narrow it** — it was not tonight (loader straight to my image on all ten boots, no vendor firmware, `n_writes 0` in every dump, no `FLW`/`EW`/`EB`/burn issued), and the vendor firmware *has* run on this part since the dump, but that is a hypothesis with a mechanism, not a measurement. |
| 🟢 **And the one region that matters most is now proven intact over all of it, not sampled.** | `verify 32768` covers exactly `[0, 0x6000)` — the whole loader region, **24,576** bytes — and it is byte-identical to the 2026-08-16 dump. Every `FLR` bracket in this project combined had sampled **256** of those. The first difference is `[0x9000, 0xA000)`: **4096** bytes, exactly one erase sector, above `H601` in `mtd0`'s `"boot+cfg+linux"`. |
| 🔄 **2026-09-08 (forty-fourth segment): the driver's limit is lifted and the coverage figures are unchanged, which is the point.** | `rtl819x-spi` 1.1 adds `verify <n> <off>` and a two-level `map` (32 x 32 = 1024), and `tools/flashmap.py` computes the expectation from the dump so every line can be carded before power. **It has read nothing**: the scope decision is that these verbs ride on `R5-6`'s image. So the row below stands in every digit. |
| 🔴 **Coverage is still the binding limit, and it is now limited by the DRIVER rather than by the bracket.** | Proven identical **28,672** bytes (0.684 %); proven different **4096** (0.098 %); **undetermined 4,153,344 (99.02 %)**; never hashed by rule 8,192 (0.195 %). Prefix digests find the *first* difference and nothing past it, and `verify` takes a limit with **no offset** (`rtl819x-spi.c:765`). Whether anything above `0xA000` also moved cannot be settled by this image. `FLS-26` in `SPEC.md` §17 owns the way out. |

---

## The reproducible build closes at one machine

| | |
|---|---|
| 🔴 **`P4a` is closed at Level 1: same machine, same tree, built twice. A third party rebuilding the published recipe will NOT get the same sha256.** | 讀 2026-09-01: this drop's `scripts/mkcompile_h` has no `KBUILD_BUILD_USER` and no `KBUILD_BUILD_HOST` (those arrived in mainline after 2.6.30). It writes `LINUX_COMPILE_BY` from `` `whoami` `` and `LINUX_COMPILE_HOST` from `` `hostname` ``, so the banner carries this workstation's identity and the image carries the banner. |
| ⚠️ **The other six candidates for the same problem split three ways, and are listed so the residual is one item rather than a worry.** | **Three were measured or read away**: `LINUX_COMPILER` is `"gcc version 3.4.6-1.3.6"` and carries no build path (讀); the image holds **0** hits for `/home/key`, `r3-4` or `cells/` (量); the initramfs entries' mtimes are declared, all 31 of them. **One is untestable on this host**: `locale -a` returns `C`, `C.utf8` and `POSIX` and nothing else, so no run-time case here can distinguish a driver that pins `LC_ALL` from one that does not — the driver pins it and the assertion is on the source text, which is weaker and says so. 🔄 **2026-09-01, later the same day: ONE stays unmeasured** — kbuild's link order against `readdir`. `.version` under `--keep` was measured by `R4-0`: a fresh cell links once and reads `1`, the same tree after two `--keep` builds reads `3`, and the two images differ in **2 bytes of 3,968,240** — the `#1` against `#3` in `linux_banner` and `init_uts_ns`, and nowhere else (`SPEC.md` `TC-42`, `notes/dev-loop.md` §5.1). 🔄 **2026-09-02: two bytes is the cost of a DIGIT, not of the counter, and this row published it as a bound.** 量, a ladder of consecutive links from one tree: `#7→#8`, `#8→#9` and `#10→#11` each differ in **2** bytes; **`#9→#10` differs in 56**, adding a `.symtab` byte, because the decimal rendering widens and shifts `UTS_VERSION` in both of its copies. The CLAIM is unchanged — `--keep` does break byte-identity — and the SENTENCE was wrong from the tenth link on. `notes/incremental-build.md` §5.5. *(This read "Two stay unmeasured", and it was the third number in this row to need re-deriving rather than re-reading.)* 🔄 **2026-09-01: this row said *five … were measured or read away* and then listed four things, one of which (`LINUX_COMPILE_TIME`) is not one of the seven, while the `LC_ALL` row was named nowhere.** It was copied from `notes/reproducible-build.md` §6, whose own summary was wrong the same way; both were corrected by re-deriving the count off the table rather than by any checker. `notes/reproducible-build.md` §6. |
| 🔴 **`P4a`'s own definition of done is wrong as written, and the gate closed with it recorded rather than repaired.** | The gate board says *"with the positive control that changing one source byte changes it"*. 量: one byte of a string literal changes the sha256; one byte inside a **comment** in the same file leaves it byte-identical. The wording needs *that reaches the image*. The second outcome was predicted before it was run, because a control that can only come out one way is not a control. |
| ⚠️ **Every sha256 recorded for a build belongs to a recipe id and has to be quoted with one.** | `RLXFW_SRC_ID` is a sha256 over `config/` **as bytes**, comments included, so a typo fix in a declaration produces a different image. That is the design — the image's identity tracks the declaration exactly — and the cost is that two images are not comparable across a documentation-only commit. |

---

## Gates that closed with a defect recorded

| | |
|---|---|
| 🔴 **`R3`'s D3 had no observable.** | The written criterion for *early bring-up completes* was the string `MemTotal:`, which **this kernel never prints in any configuration** — it is a `/proc/meminfo` field, not a boot message. The row passed on a substitute (the eleven boot marks, which are discriminators checked in the image before the seating). A DoD whose observable does not exist is a defect in the DoD and is recorded as one. |
| ⚠️ **`R3-2`'s `TC-d` half stayed half-done for one step.** | It is carried as a debt in the running-order note rather than counted as a pass. |
| ⚠️ **`R1h`'s decision ② is still `R1-gate`'s.** | It was answered on the D side by a bare-metal payload, and not by the gate that owned it. |

---

## The artefacts

| | |
|---|---|
| ⚠️ **The 60-second take is a REPLAY, not a live recording.** | It is seven committed serial captures replayed at true wire speed by `tools/replay-capture.py reel config/r3-11-reel.tsv`. `plan/ARTIFACTS.md` §2's v0.2 row describes a live power-up. The replay is reproducible by anyone who clones this repository, which a recording is not — but it is not a recording of the board, and the video says so. |
| 🔴 **The `v0.2` release ships no image, and that is deliberate.** | 量: the release has **0 assets**. Three reasons, each checkable rather than a preference. **① GPL.** The kernel is a derivative of Realtek's GPL source, so distributing the binary carries the corresponding-source obligation — and `P4b` (corresponding source, a written offer, a per-file modification record) is on the gate board at **v1.0** and is not started. Publishing the binary now would create an obligation this project cannot currently meet. **② It is not all mine to publish.** 量 `config/rlxfw-initramfs.tsv`: **four of the five `file` entries are `owner=unit`** — `/bin/busybox`, `/lib/libuClibc-0.9.30.3.so`, `/lib/ld-uClibc-0.9.30.3.so` and `/lib/libgcc_s.so.1`, all carved out of this device's own flash dump. Only `/init` is mine. Shipping the image ships the vendor's userspace. **③ It would not help anyone check anything.** `P4a` closes at Level 1, so a third party rebuilding the published recipe does not get this hash — a published binary could not be verified against the published source, which is the only reason to publish one. Level 2 is what would change that. ⚠️ What IS published is what can be checked: the seven captures the take is made of, every declaration the build reads, and the tools with their controls. |
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
| 🔴 **Four numbers this repository states about ITSELF were wrong on one morning, and nothing here can see the class.** | 量 2026-09-01, all four found by re-deriving a figure against the thing it counts, none by a checker: `PROGRESS.md`'s `P4b-3` said this file had **25 entries** when it had 28 — true when written, broken by three later commits in the same session; this file's CI row said **17 of 59** when its own population was 18 of 59; `notes/reproducible-build.md` §6 said **five of seven** Level-2 rows were settled when three were, and this file copied it. **The shape is constant**: a count about the repository's own contents, load-bearing for nothing in the sentence around it, so nobody re-checks it, and no tool here reads a natural-language number against the artefact it describes. `spec-check` checks `SPEC.md`'s rows against their owner files, which is the same idea one file wide. **Whether the class is worth an instrument has not been measured** — the population of such numbers in committed files is unknown, and measuring it is the first step, not building one.  🟢 **2026-09-01, later the same day: the class now has a measured backing instead of an intuition, and it came from the CI history.** 量, all eighteen red CI runs read from their own logs: **sixteen of the eighteen** are the same shape — a count or a label about the repository's own contents, kept in a second place, invalidated by a change somewhere else. Seven are `tools/ci-expected.tsv`'s per-suite counts against the suites, four are one hardcoded *N cold, M warm* inside `test-boot-timeline`'s `B2` against the captures under `bench/`, five are that table's allowed-skip labels against what a tool actually prints. 🔴 **So the question is no longer whether the class is real. It is why the machine-readable half has an instrument and the prose half has none** — `ci-census` makes this class fail loudly on a push; in prose the identical mistake sits there silently, which is how four of them reached committed files. ⚠️ **The population of prose counts is still unmeasured** and that is still the next step; what changed is that the class is now this repository's single largest recorded source of CI failure. |
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
*Arriving*: 🔴 **whether the public RTL8196E ports derive from the vendor's
`arch/rlx`.** `docs/blind-write-ledger.md` § 6 — it decides whether reading the
vendor's MTD map cost `R5-5`'s independence, it cannot be settled before
cloning, and cloning is the act the ledger dates. `R5-9` carries it as an
ordering constraint: the derivation check runs **before** any register map is
read.

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
* **Whether a DMA write is visible to a cached CPU read.** Nothing has been
  measured in that direction, and it is the one driver decision the cache gate
  closed without.
* **Whether this silicon retires the `cache` instruction.** This unit's own
  vendor kernel contains 37 of them, D side only; none has been executed by
  anything of this project's.
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
  the image the loop just assembled*, and it needs a power cycle. `SEAM-1`.
* 🔴 **`looprun --iterations` above 1 is refused, because the loop cannot
  repeat.** `S4` is a loader command and iteration 1 ends with the loader
  gone. A loop that runs once is what exists; `R5` is six drivers. `LOOP-3`.


---

## 🔴 The device cannot check the driver's own arithmetic, and a mark it prints can be invisible to a `grep`

*Both measured 2026-09-08, seating 16. They are here rather than in a bench card
because they are properties of the image and of the console, and every future
card inherits them.*

| | |
|---|---|
| 🔴 **`FW-46` — this image's busybox has no `dd`, no `md5sum`, and no `--list`, so nothing on the device can digest a byte.** | 量, four cells, all `applet not found`: `busybox dd if=/dev/mtd2ro bs=4096 skip=8\|9\|10 count=1 \| busybox md5sum` three times, and `busybox --list` once. **`busybox wc` does work** — `C1-SZ` used it to read back `4194304` — so this is a small configuration, not a broken busybox, and "the applets are all missing" is refuted by a control in the same seating. 🔴 **The consequence is not inconvenience, it is a missing second source**: `rtl819x-spi`'s internal sha256 has **no independent on-device check** on this image, so all three of `FLS-26`'s controls on it are desk comparisons against the dump. ⚠️ And a card may not *guess* an applet exists: `RUNSHEET` §B5 records eleven busybox symlinks and "everything else is `busybox <name>`", which says how to **call** an applet and not whether it is **there**. Three cells were spent finding that out. |
| 🔴 **`FW-47` — the kernel's `rlxfw_mark()` output and busybox ash's echo of the typed line interleave character by character, so a mark the board printed can be absent from a `grep`.** | 量, `C1-TW`. The board printed `RLXFW-S-TRYW=00000001`; the capture's first line reads `… ; cat /proc/rtlR8L19XxF-sWp-iS-` with `TRYW=00000001` on the next. `RLXFW-S-` and the echo's remaining `819x-spi` are woven together one character at a time — both strings are present and neither is readable. 🔴 **Same family as `FW-41`** (*a mark the board printed can be absent from a `grep`*), different mechanism: `FW-41` is ash dropping the last character of a refused write's payload; this is concurrent output interleaving. 🟢 **The fix was already in the card's §4.3a and was not drawn out of it**: marks come from `write_proc` and fields from `read_proc`, so the mark is emitted *during* the echo and collides with it while the fields are emitted *after* and arrive clean. **Gate on fields, never on marks.** It cost one false stop, and the fields `n_write_refused 2` / `n_writes 0` in that very capture said the driver was right. |
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

## Closed since `v0.2` was tagged

**Kept rather than deleted, so this file can be read against the copy at the `v0.2` tag.**

| | |
|---|---|
| 🟢 **CLOSED 2026-09-01 — the per-gate ledger is public.** *(was: `study/weekly-results.md` is not in the public repository)* | 量: `.gitignore:17` is `study/`, and `git ls-files study/` returns nothing. `CHARTER.md` §110 rule 3 asks for one entry per closed gate in that file, and four are owed (`R2a/b/d`, `R1h`, `R3`, `P4a`). **Owner's ruling 2026-09-01: leaving it ignored is acceptable for now.** `P4b-gate` ③ owns the decision. 🟢 **2026-09-01, `P4b-2`:** the file moved to `docs/GATE-RESULTS.md` — committed, English, one entry per closed gate, and its name now says what its unit is. `study/` stays gitignored; the owner's ruling about the directory and the requirement on this artefact turned out not to be in conflict once the artefact stopped living in that directory. Five entries: `R1-gate`, `R2a/b/d`, `R1h`, `R3`, `P4a`. `S0` and `R0` are deliberately not backfilled, with the reason at the top of that file. |
| 🟢 **CLOSED 2026-09-01 — version → contents has one committed owner.** *(was: two owners disagreeing on six of six shared rows)* | `plan/CHARTER.md` §88 is authoritative and is **gitignored**, so a public reader cannot follow a pointer to it; `PROGRESS.md`'s Release clock restates it and is stale. This file and `CHANGELOG.md` now own the contents of the versions that have actually been released; the map of *future* versions still has the defect. `P4b-gate` ① owns it. 🟢 **2026-09-01, `P4b-1`:** `README.md` § *Which gates make which version* is the owner. `PROGRESS.md`'s Release clock dropped both restated columns and keeps only `Shipped`; the planning material's table dropped its contents column and keeps only its estimates; and `CHANGELOG.md`'s `v0.2` section stopped pointing at a gitignored file. 🔴 **The repair also found that the `Target` column beside `Contents` was a restatement too** — it carries the planning material's own ×1.8 multiplier — and it agreed on only two of six rows while never having been flagged. |