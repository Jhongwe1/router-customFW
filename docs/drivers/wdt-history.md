# `rtl819x-wdt.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c`](../../kernel/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c)
until 2026-10-18 — lines 1–407 at commit `8965e5fa` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [wdt](wdt.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-wdt.c` counts the file's lines at `8965e5fa`.

```c
/*
 * rtl819x-wdt -- a /dev/watchdog for the RTL8196E's WDTCNR.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-6, 2026-09-08, forty-fifth segment.  It is
 * staged into drivers/watchdog/ by tools/rlxfw-marks.py from kernel/;
 * config/rlxfw-marks.tsv `MK6` carries the one Kbuild line that links it, and
 * config/rlxfw-kernel.delta carries the two config lines that make it reachable
 * (CONFIG_WATCHDOG=y, so drivers/Makefile:79 descends here at all) and the one
 * that makes it the ONLY thing touching WDTCNR (CONFIG_RTL_WTDOG=n).
 *
 * WRITTEN BLIND.  docs/blind-write-ledger.md records ZERO cited paths in the
 * `wdt` domain -- PROGRESS.md's D3 refutation clause names gpio, wdt, led and
 * keys as the four drivers with no implementation read.  No third-party
 * RTL8196E watchdog driver has been cloned, opened or read by this project.
 * What WAS read is (a) the Linux watchdog USERSPACE ABI, which is mainline and
 * not an implementation of this SoC:
 *
 *     include/linux/watchdog.h          WDIOC_*, WDIOF_*, struct watchdog_info
 *     include/linux/miscdevice.h        WATCHDOG_MINOR = 130
 *     Documentation/watchdog/watchdog-api.txt   magic close, nowayout
 *
 * and (b) THE VENDOR'S OWN watchdog code in the drop this image is built from,
 * which is not a third-party implementation but the thing this driver replaces.
 * Every line of it is enumerated below, because "I read the code I am
 * displacing" is a fact the ledger has to carry, not one to leave implicit.
 *
 * ========================================================================
 * 1.  THE REGISTER.   SPEC.md MAP-08, REG-12.   WDTCNR = 0xB800311C.
 * ========================================================================
 *
 *   [31:24] WDTE       0xA5 stops the counter; ANY other value runs it.
 *                      讀 x2: rtl865xc_asicregs.h WDSTOP_PATTERN 0xA5 and
 *                      WDTE_OFFSET 24; datasheet D 8.2.9 Table 27.
 *                      量: the power-on reset value of the whole word is
 *                      A5000000 (REG-12), i.e. the part comes up STOPPED.
 *   [23]    WDTCLR     write 1 to clear the counter.  A kick.
 *                      讀 rtl865xc_asicregs.h WDTCLR (1<<23).
 *                      量 (indirectly): the vendor kicks with it 100x/s and
 *                      this board does not reset, which it would in
 *                      ~1,335 ms if the write did nothing.
 *                      🔴 This row read "17.5 ms" until 2026-09-09.  The
 *                      INFERENCE is unchanged and only slower -- 100 kicks a
 *                      second against a 1.33 s deadline still means a dead
 *                      WDTCLR resets the board, just 76x later -- but the
 *                      number was CLK-08b's loader-state constant.  量
 *                      seating 17: OVSEL 3 bites at 1,334.723 ms.
 *   [22:21] OVSEL[1:0] 讀 rtl865xc_asicregs.h OVSEL_16 (1<<21),
 *                      OVSEL_17 (2<<21), OVSEL_18 (3<<21).
 *   [20]    WDTIND     "indicate whether watchdog ever occurs".
 *                      讀 rtl865xc_asicregs.h WDTIND (1<<20) + D Table 27.
 *                      🔴 量 REFUTED AS READABLE -- REG-12 殘留: read on both
 *                      sides of a real watchdog reset in one power cycle
 *                      (Y-wd0/Y-wd1) it is 0 both times, with the negative
 *                      control holding.  Three explanations are not
 *                      separated.  This driver reports it and does not
 *                      believe it; see WDIOC_GETBOOTSTATUS below.
 *   [19]    OVSEL[2]?  🔴 UNDETERMINED.  See section 2.
 *   [18]    OVSEL[3]   量 CLK-08: the loader was driven to write 0x00040000
 *                      and 0x00240000 and the two timeouts came out
 *                      557.583 ms and 1118.133 ms, ratio 2.0053, with an
 *                      ESC-count check (528:262 = 2.0153) that uses no
 *                      timestamp at all.
 *
 *   timeout = 2^(15+OVSEL) / 14,965,000 Hz          量 CLK-08b (+-0.02 MHz)
 *
 *   🔴 That frequency is NOT the timer base clock.  CLK-08b: f_timer/14 =
 *   14.2861 MHz is 4.75 % away and the timer base itself is known to +-7 ppm,
 *   so the gap is ~6800x its own error bar.  The watchdog counts something
 *   else and CLK-08b 殘留 says what it counts is undetermined.  This driver
 *   therefore treats 14.965 MHz as a MEASURED CONSTANT OF THIS DIE and not as
 *   a derived one -- if it is ever re-derived from a clock tree, the constant
 *   below is the single place that changes.
 *
 * ========================================================================
 * 2.  THE HOLE IN THE ENCODING, AND WHY THIS DRIVER REFUSES FOUR SETTINGS.
 * ========================================================================
 *
 * CLK-07 (讀, D Table 27) says OVSEL is 4 bits and selects 2^15..2^24 -- ten
 * settings.  The SDK header only defines four (OVSEL_15..OVSEL_18) and puts
 * them at bit 21.  The two measured points then force a SPLIT field:
 *
 *     OVSEL=8 (2^23)  ->  0x00040000  = bit 18 alone
 *     OVSEL=9 (2^24)  ->  0x00240000  = bit 18 + bit 21
 *
 * The difference between 8 and 9 is OVSEL bit 0, and the difference in the
 * register is bit 21 -- so OVSEL[0] is at bit 21, which agrees with the SDK's
 * OVSEL_16 = (1<<21).  OVSEL[1] is then bit 22 (SDK OVSEL_17 = 2<<21) and
 * OVSEL[3] is bit 18 (both measured points have it set).  That leaves
 * OVSEL[2], which was 0 in every reading this project has ever taken.
 *
 * 🔴 SO OVSEL[2] IS AT BIT 19 OR AT BIT 20, AND NOTHING HERE SEPARATES THEM.
 * Bit 20 is where the SDK header and the datasheet both put WDTIND, which
 * argues for bit 19 -- but REG-12 殘留 records that this die does not read
 * WDTIND back, so the one measurement that could corroborate the header's
 * bit-20 assignment is the one that failed.  推, not 量.
 *
 * The consequence is a hole at OVSEL 4,5,6,7 (2^19..2^22, 35..280 ms).  This
 * driver returns -EOPNOTSUPP for those four rather than guessing, and
 * -EINVAL for out-of-range, so the two failures are distinguishable at the
 * shell.  The six settings it does accept are 0,1,2,3 (讀, and 0 and 3 also
 * 量 -- see section 3) and 8,9 (量, CLK-08).
 *
 * 🟢 The `biteraw` verb is what closes the hole, and it costs two reboots and
 * no power cycle: arm 1<<19 and time the bite, then arm 1<<20 and time it.
 * One hypothesis predicts 35.0 ms and 2.19 ms, the other predicts 2.19 ms and
 * 35.0 ms.  A 16x separation, read off console timestamps.  See section 6.
 *
 * ========================================================================
 * 3.  WHAT THE VENDOR DOES WITH THIS REGISTER, ENUMERATED ON THE ARTEFACT.
 * ========================================================================
 *
 * Read 2026-09-08 off the vmlinux this image's tree produces (cell spi11,
 * 4,047,318 bytes), by resolving every instruction that forms the constant
 * 0xB800311C to its owning symbol in System.map.  NINE references, five
 * owners -- source says what could happen, the artefact says what did:
 *
 *   bsp_timer_init+0xb8      WDTCNR = 0x00600000   ARM.  OVSEL=3, which is
 *                            1,334.723 ms 量 -- this line read 17.5 ms
 *                            until 2026-09-09.
 *   rlx_timer_interrupt+0x60 WDTCNR |= 1<<23       KICK, 100 Hz.
 *   rlx_timer_interrupt+0x4c WDTCNR = 0 ; for(;;)  is_fault reboot path.
 *   bsp_machine_restart+0xb4 WDTCNR = 0 ; for(;;)  REBOOT.
 *   write_watchdog_reboot+0x84  WDTCNR = 0 ; for(;;)   /proc/watchdog_reboot.
 *   rtl8192cd_open+0x680     WDTCNR = 0 ; for(;;)  wlan open failure path.
 *   rtl8192cd_init_hw_PCI x2, rtl8192cd_init_one x1   kicks during wlan init.
 *
 * 🔴 THE FIRST TWO ARE THE WHOLE PROBLEM, AND THE FIRST ONE CORRECTS A
 * COMMITTED ROW.  SPEC.md FW-45 reasoned about kernel-side loop safety from
 * "CLK-08 bounds the watchdog window at about one second".  That is the
 * LOADER's OVSEL=9.  Under Linux the vendor arms OVSEL=3 -- 2^18 ticks --
 * and kicks every 10 ms at HZ=100.
 *
 * 🔴🔴 AND THIS PARAGRAPH THEN GOT ITS OWN NUMBER WRONG BY 76x, IN THE SAME
 * DIRECTION AND FOR THE SAME REASON AS THE ROW IT WAS CORRECTING.  What it
 * said is kept verbatim, because what it got wrong is the useful part:
 *
 *   "17.5 ms -- and kicks every 10 ms at HZ=100.  The margin is 7.5 ms, not
 *    1.1 s, and the system tolerates ZERO lost timer interrupts."
 *
 *   "That makes an old measurement mean more, not less.  rtl819x-spi's 4 MiB
 *    traversal ran 13.3 s on this board across ten boots with that 17.5 ms
 *    deadline live -- so no interrupt-blocked window on that path exceeded
 *    17.5 ms, measured, without anyone setting out to measure it.  It also
 *    bounds IRQ-13's unexplained loss: whatever drops 11 of 585 TC1
 *    interrupts during the vendor NIC's init cannot be producing >17.5 ms
 *    gaps in TC0 delivery, or the board would have reset instead of booting."
 *
 * 量 seating 17: OVSEL 3 is 1,334.723 ms.  So
 *
 *   - the margin over a 10 ms tick is ~1,325 ms, not 7.5 ms, and the system
 *     tolerates about 130 lost timer interrupts rather than zero;
 *   - the free bound on the SPI traversal is 1,310 ms, i.e. SEVENTY-FIVE
 *     TIMES WEAKER, which makes it worth very little;
 *   - the IRQ-13 bound moves the same way for the same reason.
 *
 * The middle one is the one to watch.  "The correction makes an older
 * measurement worth more" is the shape of sentence that gets quoted onward
 * without being re-derived, and it WAS quoted onward -- into
 * docs/FINDINGS.md (docs/history/findings-2026-10-17.md now) and notes/watchdog-driver.md -- before anything
 * re-derived it.
 *
 * ⚠️ THE DECISION IS UNCHANGED, and writing that out is the point.
 * CONFIG_RTL_WTDOG=n is justified by "there is an unconditional 100 Hz kick",
 * which is true at 17.5 ms and true at 1,334.7 ms: a watchdog that cannot
 * bite cannot bite at either deadline.
 *
 * 🔴 AND THE VENDOR'S ARRANGEMENT MAKES A /dev/watchdog IMPOSSIBLE.  A kick
 * in the tick ISR feeds the dog whether or not userspace is alive, so a
 * driver shipped alongside it would expose a watchdog that CANNOT BITE.
 * CLAUDE.md: a tool that cannot fail proves nothing.  Hence:
 *
 *   ------------------------------------------------------------------
 *   CONFIG_RTL_WTDOG=n, AND THE BLAST RADIUS WAS ENUMERATED FIRST.
 *   ------------------------------------------------------------------
 *   REMOVED   bsp_timer_init's arm; rlx_timer_interrupt's 100 Hz kick and
 *             its is_fault reboot; the three wlan kicks (gated on the same
 *             symbol -- CONFIG_RTL865X_WTDOG, the other arm of every
 *             `#if defined(A) || defined(B)`, is absent from autoconf.h);
 *             kernel/panic.c's and kernel/exit.c's is_fault stores.
 *   KEPT      bsp_machine_restart -- boards/rtl8196e/bsp/setup.c:104-118 is
 *             NOT gated, so `busybox reboot -f` still resets the board and
 *             FW-37's 2.407 s economy survives.  /proc/watchdog_reboot --
 *             drivers/char/rtl_gpio.c:2178 is NOT gated either, so a vendor
 *             "bite now" instrument survives as an independent control.
 *   COST      the vendor's "the TC0 interrupt stopped" net is gone.  This
 *             driver's bootguard (section 4) replaces it and catches
 *             strictly more, one layer up.
 *   BONUS     with =y, panic() sets is_fault and the NEXT tick reboots in
 *             <=10 ms + 2.19 ms.  At 38400 8N1 that is ~46 characters, so a
 *             vendor-kernel panic is truncated -- which is why the tree is
 *             full of panic_printk (FW-31).  With =n a panic PRINTS.  推:
 *             the arithmetic is above; refuted by any capture of a vendor
 *             kernel panic longer than ~46 characters.
 *   EVIDENCE  instruction absence.  D4's pattern from R5-5: ship =n, count,
 *             then rebuild =y in a discard tree and watch them come back.
 *
 * 🔴 THAT PREDICTION WAS WRITTEN AS "NINE FALL TO TWO" AND THE BUILD REFUTED
 * IT: nine fell to SIX.  量, cell r56b's vmlinux, the same enumeration:
 * bsp_timer_init's arm and BOTH of rlx_timer_interrupt's references are gone
 * -- the three that mattered -- but FOUR wlan references survived, in
 * rtl8192cd_open, rtl8192cd_init_hw_PCI (x2) and rtl8192cd_init_one.
 *
 * THE CAUSE IS A SPECIFIC READING ERROR AND IT IS WORTH MORE THAN THE
 * PREDICTION WOULD HAVE BEEN.  The wlan sites are NOT gated on
 * CONFIG_RTL_WTDOG.  In the built tree they read
 *
 *     #if defined(CONFIG_RTL_8198) || defined(CONFIG_RTL_819XD) || \
 *         defined(CONFIG_RTL_8196E)
 *             REG32(BSP_WDTCNR) |= 1 << 23;
 *
 * -- gated on WHICH BOARD THIS IS, and CONFIG_RTL_8196E is 1.  The
 * `#if defined(CONFIG_RTL865X_WTDOG) || defined(CONFIG_RTL_WTDOG)` wrappers
 * that the claim came from are in drivers/net/wireless/rtl8192e/, and the
 * directory that BUILDS is rtl8192cd/ -- which had already been measured
 * (built-in.o, 820,910 bytes) before the claim was written.  Two SDK vintages
 * of one driver, gated differently, and the gating was carried across from
 * the copy that is not compiled.
 *
 * WHAT IT COSTS THE DECISION: nothing.  The 100 Hz unconditional kick and the
 * vendor's OVSEL=3 arm are gone, which is what a bitable watchdog needs.
 * (This line said "the 17.5 ms arm" until 2026-09-09.  The arm is 1,334.7 ms
 * 量 and the sentence does not depend on which.)
 * WHAT IT COSTS THE SAFETY NET: a bounded amount, and the bound is measured
 * rather than argued.  All three surviving KICKS are on the wlan bring-up
 * path, and 量 the image's own initcall table puts that path at
 * `__initcall_rtl8192cd_init6` -- device_initcall, level SIX -- while this
 * driver is `__initcall_rtl819x_wdt_init7`, level SEVEN.  A kick that runs
 * before BOOTGUARD arms cannot feed BOOTGUARD.  The fourth reference,
 * rtl8192cd_open+0x680, is `WDTCNR = 0; for(;;)` -- a deliberate BITE on the
 * wlan open failure path, not a feeder.
 * ⚠️ 未定, and it is why `kickms` exists: whether rtl8192cd_init_hw_PCI can be
 * re-entered from a userspace `ifconfig up` AFTER this driver has armed.  §6
 * has the cell that settles it by experiment instead of by reading.
 *
 * ========================================================================
 * 4.  THE TIMEOUT MODEL, AND WHY IT IS TWO LAYERS.
 * ========================================================================
 *
 * The longest hardware timeout on this part is OVSEL=9 = 1.121 s.  No
 * ordinary userspace watchdog daemon pings that fast; the conventional
 * /dev/watchdog contract is tens of seconds.  A driver that reported
 * timeout=1 and refused everything else would be honest and useless.
 *
 * So there are three states, and the file says which is which rather than
 * hiding the second feeder:
 *
 *   STOPPED    WDTE=0xA5.  The counter is not running.  This is the state
 *              the SILICON powers up in (REG-12), and after =n it is also
 *              the state Linux reaches userspace in until this driver runs.
 *   BOOTGUARD  armed at hw_ovsel; a kernel timer kicks it UNCONDITIONALLY
 *              every kick_ms.  This is not a userspace watchdog.  It catches
 *              exactly one thing: the kernel timer wheel stopping.  That is
 *              a superset of what the vendor's ISR kick caught, because the
 *              timer wheel stops if the ISR stops AND if the wheel itself
 *              wedges with interrupts still flowing.
 *   USER       /dev/watchdog is open.  The same kernel timer kicks, but ONLY
 *              while time_before(jiffies, user_deadline).  Userspace sets
 *              the deadline with a write or WDIOC_KEEPALIVE and its length
 *              with WDIOC_SETTIMEOUT.  Stop pinging and the kernel timer
 *              stops kicking and the hardware bites within hw_timeout.
 *
 * 🔴 ONE DELIBERATE DEVIATION FROM THE UPSTREAM CONTRACT, NAMED HERE SO IT
 * IS A DECISION AND NOT A BUG.  watchdog-api.txt says a close without
 * nowayout STOPS the watchdog.  Here it returns to BOOTGUARD instead, because
 * STOPPED would silently delete the boot-time net that CONFIG_RTL_WTDOG=n
 * removed -- a driver that becomes LESS safe when a daemon exits cleanly is
 * the wrong default on a board with one power switch and no spare.  The
 * upstream behaviour is available: `stop` on /proc, or WDIOS_DISABLECARD,
 * both of which really do stop it and are counted separately.  This is a
 * docs/driver-diff.md L2 row: same silicon, opposite decision from the
 * vendor's (unconditional ISR kick) and from upstream's (stop on close).
 *
 * 🔴 NO READ-MODIFY-WRITE ON WDTCNR, EVER, AND THAT IS THIS PROJECT'S OWN
 * SCAR.  The vendor kicks with `REG32(WDTCNR) |= 1<<23`.  SPEC.md IRQ-08 is
 * the measured instance of exactly that shape going wrong one register away:
 * the vendor's tick handler does `REG32(BSP_TCIR) |= BSP_TC0IP` on a register
 * whose IP bits are write-1-to-clear, and it therefore clears every pending
 * bit in TCIR a hundred times a second including one belonging to a driver it
 * has never heard of.  WDTCNR has WDTIND in it, whose semantics on this die
 * are undetermined.  So every write below is a FULL WORD computed from this
 * driver's own shadow, never `readl | bit`.  The cost is that a foreign write
 * is not preserved; that is the point, and n_state_foreign counts it.
 *
 * ========================================================================
 * 5.  WHAT THIS FILE DOES NOT ESTABLISH.
 * ========================================================================
 *
 *  1. WHERE OVSEL[2] IS.  Section 2.  Four of ten settings are refused.
 *  2. WHETHER WDTIND WORKS.  REG-12 殘留 says it reads 0 across a real reset.
 *     WDIOC_GETBOOTSTATUS therefore returns 0 ALWAYS, and that 0 is not
 *     evidence that no watchdog reset happened -- it is evidence the bit does
 *     not read back.  wdtind_at_probe is exported so the claim stays visible
 *     instead of being laundered through an ABI that has no way to say
 *     "unknown".  The residual's own prescription (a payload that reads
 *     0xB800311C as the first thing after reset, before the loader runs) is
 *     NOT satisfied by this driver and cannot be: the loader runs first.
 *  3. WHAT THE WATCHDOG COUNTS.  CLK-08b 殘留.  14.965 MHz has no known
 *     integer relationship to the 200.0049 MHz base.
 *  4. n_state_foreign CANNOT FIRE IN THE SHIPPING IMAGE, and saying so is the
 *     point.  With =n nothing else writes WDTCNR while this driver is
 *     running; with =y the vendor's `|= 1<<23` preserves every other bit, so
 *     a masked read-back comparison would still agree.  The counter is not
 *     decoration: `wedge` is its positive control, and the strong
 *     discriminator between the two builds is wdtcnr_at_probe (section 6),
 *     not this counter.
 *
 * ========================================================================
 * 6.  THE EXPERIMENT THIS FILE IS BUILT TO SUPPORT, AND ITS CONTROLS.
 * ========================================================================
 *
 * D1 says ten boots must include THE THING THE DRIVER DOES.  For a watchdog
 * that is "resets the machine when it is not fed", so the ten boots have to
 * contain a bite.  A bite on this board is cheap and was already routine
 * before this driver existed: bsp_machine_restart IS a deliberate bite at
 * OVSEL=0, so every `busybox reboot -f` this project has ever run was one.
 * It writes no flash, it is self-clearing (CLK-10: WDTCNR reads A5000000
 * after a real reset), and FW-37 measured 2.407 s from command to loader
 * prompt.
 *
 * FIELD, not mark, is what the card gates on -- FW-47: every capture line is
 * CRLF and rlxfw_mark() interleaves with busybox ash's echo.  So:
 *
 *   wdtcnr_at_probe   A5000000 with CONFIG_RTL_WTDOG=n, 00600000 with =y.
 *                     ONE FIELD, TWO VALUES, and it is the whole proof that
 *                     the config line did what section 3 says.  Predicted
 *                     before the build.
 *   state / n_hw_kick BOOTGUARD and a counter that advances at ~1/kick_ms on
 *                     every one of the ten boots.  The driver is doing its
 *                     job continuously, not once.
 *   n_bite            the bite cells.
 *
 * 🟢 AND ONE CELL WHOSE VALUABLE OUTCOME IS THE NEGATIVE ONE -- "AM I THE ONLY
 * FEEDER?"  n_state_foreign cannot see a foreign `|= 1<<23` (§5.4), and after
 * the refutation above there are three surviving wlan kicks whose reachability
 * after late_initcall is 未定.  Reading more source cannot settle that; one
 * cell can:
 *
 *     stop ; kickms 3000 ; ovsel 0 ; bootguard        (hw timeout 163.8 ms)
 *
 * The kernel timer will not come round for 3 s, so if nothing else writes
 * WDTCLR the board MUST reset at ~0.164 s.  If it does NOT, something else is
 * kicking and the enumeration in section 3 is still incomplete.  A watchdog
 * cell in which "the board survived" is the finding.
 *
 * 🔴 THIS RECIPE SAID `ovsel 9` AND `1121 ms` UNTIL 2026-09-09, AND AS
 * WRITTEN IT TESTED NOTHING.  OVSEL 9 is 83.8 s 量, so a 3 s kick period
 * beats the hardware deadline by 28x and the board survives whether or not
 * anything else is feeding -- a cell whose "negative" outcome is guaranteed
 * and which therefore cannot fail.  It was carded that way and run that way;
 * 量 seating 17, the answer came from RE-RUNNING it at OVSEL 0, where the
 * board did reset, with wlan0 down and again with wlan0 up.  FW-51's residual
 * closes on that re-run, not on the carded cell.  The rule this leaves behind
 * is wider than the fix: a starvation cell needs its kick period LONGER than
 * the hardware deadline, and after WDT-1 both numbers come from one
 * derivation, so they cannot drift apart again without the dump saying so.
 *
 * THE LADDER, and it is designed as DIFFERENCES so every constant cancels.
 * A single absolute bite time carries an unknown offset: the UART's last byte
 * is still in the shift register when the counter is armed (260 us at 38400),
 * and the loader takes its own time to first byte (CLK-14: 2.07 ms).  Time
 * FOUR bites at OVSEL 0, 3, 8, 9 -- predicted 2.190 / 17.517 / 560.551 /
 * 1121.101 ms -- and fit gap(OVSEL) = 2^(15+OVSEL)/f + d for f and d.  Three
 * independent differences where CLK-08b had two points and one unknown, and
 * OVSEL 8 and 9 were measured through a COMPLETELY DIFFERENT PATH (the loader
 * being driven at its own prompt) as 557.583 and 1118.133 ms.
 *
 * 🔴 2026-09-08, seating 17.  EVERY PREDICTED NUMBER IN THE PARAGRAPH ABOVE IS
 * WRONG BY 76x, AND THE CLAIM THAT FOLLOWED IT WAS CIRCULAR.  Both are kept
 * here rather than deleted, because what they got wrong is the useful part.
 *
 *   CIRCULAR: the deleted sentence read "If the Linux figures reproduce that
 *   pair's DIFFERENCE, 14.965 MHz is confirmed from inside Linux."  CLK-08b's
 *   14.965 MHz was SOLVED FROM that difference -- (2^24-2^23)/(1118.133 -
 *   557.583) ms -- so predicting it back is an identity, and SPEC.md's own
 *   CLK-08b residual already said re-measuring a timeout only re-measures
 *   14.965.  Two files in this repository disagreed about whether an
 *   experiment could succeed and nobody noticed until a card had to state it.
 *
 *   WRONG BY 76x: 量, two rungs 32x apart, each carrying its own mdelay(50)
 *   ruler in the same capture (floors 0.517 and 0.868 ms) --
 *       OVSEL 3 (0x00E00000)  1,334.723 ms
 *       OVSEL 8 (0x00840000) 41,930.599 ms
 *   gap(8)-gap(3) = 40,595.876 ms over 2^23-2^18 counts gives
 *       f_wdt(Linux) = 200,180 Hz,  d = +25.179 ms
 *   and CLK-17 measured TC0CNT under Linux at 200,005 Hz by a different method
 *   on a different register in a different seating.  Ratio 0.999.
 *
 *   SO 14.965 MHz IS A LOADER-STATE CONSTANT, exactly as CLK-17's 14,286,057 Hz
 *   is: Linux reprograms CDBR and both slow together.  The constant at the top
 *   of this file (RTL819X_WDT_HZ) is therefore RIGHT FOR THE LOADER AND WRONG
 *   FOR THE STATE THIS DRIVER RUNS IN, and every usec in rtl819x_wdt_steps[] is
 *   76x short.  It is NOT changed here: the table is what /proc prints and what
 *   a card predicts, and changing it silently would break the one field a
 *   seating can compare against a frozen card.  R5-6's second bench half
 *   derives it at init the way rtl819x-timer's hz_used is derived (CLK-17's
 *   2026-09-04 fix), and until then hw_timeout_us is documented-wrong.
 *
 *   NEGATIVE CONTROL, in the same cells: OVSEL 0 and 3 are the vendor's own
 *   two values.  🔴 量: OVSEL 3 came out at 1,334.723 ms, not 17.517 -- so the
 *   control FIRED, and what it refuted was SPEC.md FW-45 rather than this
 *   driver.  OVSEL 0 turned out not to be measurable by this method at all:
 *   prom_putchar fills a UART FIFO rather than the wire, so rlxfw_puts returns
 *   with bytes still queued and a 163.7 ms reset lands mid-drain -- the 0x8D
 *   corrupting RLXFW-W-GO in C1-B is that.  The ladder has TWO clean rungs.
 *
 * ========================================================================
 */
```
