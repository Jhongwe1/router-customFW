/*
 * rtl819x-wdt -- a /dev/watchdog for the RTL8196E's WDTCNR.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-6, 2026-09-08, forty-fifth segment.  It is
 * staged into drivers/watchdog/ by tools/rlxfw-marks.py from config/rlxfw-src/;
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
 *                      this board does not reset, which it would in 17.5 ms
 *                      if the write did nothing.
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
 *   bsp_timer_init+0xb8      WDTCNR = 0x00600000   ARM.  OVSEL=3 = 17.5 ms.
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
 * LOADER's OVSEL=9.  Under Linux the vendor arms OVSEL=3 -- 2^18 ticks,
 * 17.5 ms -- and kicks every 10 ms at HZ=100.  The margin is 7.5 ms, not
 * 1.1 s, and the system tolerates ZERO lost timer interrupts.
 *
 * 🟢 That makes an old measurement mean more, not less.  rtl819x-spi's 4 MiB
 * traversal ran 13.3 s on this board across ten boots with that 17.5 ms
 * deadline live (FW-45, seating 16) -- so no interrupt-blocked window on that
 * path exceeded 17.5 ms, measured, without anyone setting out to measure it.
 * It also bounds IRQ-13's unexplained loss: whatever drops 11 of 585 TC1
 * interrupts during the vendor NIC's init cannot be producing >17.5 ms gaps
 * in TC0 delivery, or the board would have reset instead of booting.
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
 * 17.5 ms arm are gone, which is what a bitable watchdog needs.
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
 *     stop ; kickms 3000 ; ovsel 9 ; bootguard        (hw timeout 1121 ms)
 *
 * The kernel timer will not come round for 3 s, so if nothing else writes
 * WDTCLR the board MUST reset at ~1.121 s.  If it does NOT, something else is
 * kicking and the enumeration in section 3 is still incomplete.  A watchdog
 * cell in which "the board survived" is the finding.
 *
 * THE LADDER, and it is designed as DIFFERENCES so every constant cancels.
 * A single absolute bite time carries an unknown offset: the UART's last byte
 * is still in the shift register when the counter is armed (260 us at 38400),
 * and the loader takes its own time to first byte (CLK-14: 2.07 ms).  Time
 * FOUR bites at OVSEL 0, 3, 8, 9 -- predicted 2.190 / 17.517 / 560.551 /
 * 1121.101 ms -- and fit gap(OVSEL) = 2^(15+OVSEL)/f + d for f and d.  Three
 * independent differences where CLK-08b had two points and one unknown, and
 * OVSEL 8 and 9 were measured through a COMPLETELY DIFFERENT PATH (the loader
 * being driven at its own prompt) as 557.583 and 1118.133 ms.  If the Linux
 * figures reproduce that pair's DIFFERENCE, 14.965 MHz is confirmed from
 * inside Linux against a number derived at the loader.  If they do not, one
 * of the two paths is wrong and the disagreement is the finding.
 *
 *   NEGATIVE CONTROL, in the same cells: OVSEL 0 and 3 are the vendor's own
 *   two values.  17.517 ms must come out of a driver of mine at the same
 *   number the vendor's bsp_timer_init programmed, and 2.190 ms must match
 *   what bsp_machine_restart has been doing for every reboot in this
 *   project's history.  A ladder whose two known rungs disagreed with the
 *   two the board has been living on would refute the driver, not the clock.
 *
 * ========================================================================
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/watchdog.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/timer.h>
#include <linux/jiffies.h>
#include <linux/delay.h>
#include <linux/string.h>
#include <linux/bitops.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

#define RTL819X_WDT_VERSION	"rtl819x-wdt 1.0"

/* ------------------------------------------------------------------------
 * Constants.  Every one has a SPEC.md id in the header above.
 * ------------------------------------------------------------------------ */

#define RTL819X_WDT_PHYS	0x1800311C	/* 0xB800311C through KSEG1 */

#define WDTE_SHIFT		24		/* 讀 WDTE_OFFSET */
#define WDTE_STOP		0xA5u		/* 讀 WDSTOP_PATTERN; 量 reset */
#define WDTE_RUN		0x00u		/* 量 bsp_timer_init writes 0 */
#define WDTCLR			(1u << 23)	/* 讀 WDTCLR */
#define WDTIND			(1u << 20)	/* 讀; 量 REFUTED as readable */

/* The OVSEL split field.  See header section 2 for how each bit was pinned. */
#define OVSEL_B0		(1u << 21)	/* 量 (8 vs 9) + 讀 OVSEL_16 */
#define OVSEL_B1		(1u << 22)	/* 讀 OVSEL_17 = 2<<21 */
#define OVSEL_B3		(1u << 18)	/* 量 (both CLK-08 points) */

/* Everything this driver may ever put in WDTCNR.  A write outside this mask
 * is a bug, and rtl819x_wdt_compose() is the only place a word is built. */
#define WDTCNR_KNOWN_MASK	(0xFFu << WDTE_SHIFT | WDTCLR | \
				 OVSEL_B0 | OVSEL_B1 | OVSEL_B3)

/* Bits masked out of the shadow comparison: WDTCLR is a strobe that is not
 * expected to read back, WDTIND is a status bit whose behaviour on this die
 * is undetermined (REG-12 殘留). */
#define WDTCNR_VOLATILE_MASK	(WDTCLR | WDTIND)

#define RTL819X_WDT_NOVSEL	10		/* 讀 CLK-07: 2^15 .. 2^24 */

/* 量 CLK-08b: the watchdog's own counting frequency on this die.  Not derived
 * from the timer base -- see header section 1. */
#define RTL819X_WDT_HZ		14965000u

#define RTL819X_WDT_PROC_NAME	"rtl819x-wdt"

/* The value REG-12 recorded for a part that has not been armed, and the value
 * this image's bsp_timer_init writes when CONFIG_RTL_WTDOG=y.  Reported as
 * equal/not-equal so the card reads a field, not a hex string it must
 * interpret. */
#define WDTCNR_RESET_VALUE	0xA5000000u
#define WDTCNR_VENDOR_ARMED	0x00600000u

/* ------------------------------------------------------------------------
 * The OVSEL table.  usec is 2^(15+ovsel) / RTL819X_WDT_HZ, rounded, computed
 * at the desk and written out rather than divided at run time -- there is no
 * 64-bit divide in this path and the numbers are part of the record.
 *
 * `enc` is the register encoding; `valid` is 0 for the four settings whose
 * encoding depends on where OVSEL[2] is (header section 2).  They are listed
 * with enc 0 rather than omitted, so /proc prints ten rows and the hole is
 * visible on the board instead of only in this comment.
 * ------------------------------------------------------------------------ */
struct rtl819x_wdt_step {
	u32	enc;
	u32	usec;
	u8	valid;
};

static const struct rtl819x_wdt_step rtl819x_wdt_steps[RTL819X_WDT_NOVSEL] = {
	/* 0 */ { 0,                                  2190u, 1 },
	/* 1 */ { OVSEL_B0,                           4379u, 1 },
	/* 2 */ { OVSEL_B1,                           8759u, 1 },
	/* 3 */ { OVSEL_B1 | OVSEL_B0,               17517u, 1 },
	/* 4 */ { 0,                                 35034u, 0 },
	/* 5 */ { 0,                                 70069u, 0 },
	/* 6 */ { 0,                                140138u, 0 },
	/* 7 */ { 0,                                280275u, 0 },
	/* 8 */ { OVSEL_B3,                         560551u, 1 },
	/* 9 */ { OVSEL_B3 | OVSEL_B0,             1121101u, 1 },
};

/* ------------------------------------------------------------------------
 * Module parameters.
 * ------------------------------------------------------------------------ */

static int hw_ovsel = 9;
module_param(hw_ovsel, int, 0);
MODULE_PARM_DESC(hw_ovsel, "hardware OVSEL (0-3,8,9; 4-7 refused, see file)");

/* 250 ms against a 1121 ms hardware deadline is 4.48x margin, which is four
 * whole kicks.  It is expressed in ms and converted with msecs_to_jiffies so
 * a reader does not have to know HZ. */
static int kick_ms = 250;
module_param(kick_ms, int, 0);
MODULE_PARM_DESC(kick_ms, "kernel-timer kick period in ms");

static int soft_timeout = 60;
module_param(soft_timeout, int, 0);
MODULE_PARM_DESC(soft_timeout, "userspace deadline in seconds (WDIOC_SETTIMEOUT)");

static int bootguard = 1;
module_param(bootguard, int, 0);
MODULE_PARM_DESC(bootguard, "arm the hardware at late_initcall and kick it from a kernel timer");

static int nowayout = 0;
module_param(nowayout, int, 0);
MODULE_PARM_DESC(nowayout, "once /dev/watchdog is opened it cannot be released to BOOTGUARD");

/* ------------------------------------------------------------------------
 * State.
 * ------------------------------------------------------------------------ */

enum rtl819x_wdt_state {
	WDT_STOPPED	= 0,
	WDT_BOOTGUARD	= 1,
	WDT_USER	= 2,
	WDT_BITE	= 3,	/* transient: the kick path must not run */
};

static const char * const rtl819x_wdt_state_name[] = {
	"STOPPED", "BOOTGUARD", "USER", "BITE"
};

static DEFINE_SPINLOCK(rtl819x_wdt_lock);
static struct timer_list rtl819x_wdt_timer;

static int  rtl819x_wdt_state = WDT_STOPPED;
static int  rtl819x_wdt_ovsel;			/* the armed OVSEL */
static u32  rtl819x_wdt_shadow = WDTCNR_RESET_VALUE;
static unsigned long rtl819x_wdt_deadline;	/* jiffies; USER state only */

static u32  rtl819x_wdt_probe_val;		/* WDTCNR before anything */
static int  rtl819x_wdt_misc_rc = -EAGAIN;
static int  rtl819x_wdt_registered;

static unsigned long rtl819x_wdt_n_hw_kick;	/* WDTCLR writes */
static unsigned long rtl819x_wdt_n_user_ping;	/* write()/KEEPALIVE */
static unsigned long rtl819x_wdt_n_arm;
static unsigned long rtl819x_wdt_n_stop;
static unsigned long rtl819x_wdt_n_settimeout;
static unsigned long rtl819x_wdt_n_state_foreign;
static unsigned long rtl819x_wdt_n_missed;	/* timer ran, deadline expired */
static unsigned long rtl819x_wdt_n_bite;
static unsigned long rtl819x_wdt_n_wedge;
static unsigned long rtl819x_wdt_n_reject;	/* verbs/ioctls refused */
static unsigned long rtl819x_wdt_n_unclean_close;	/* closed without 'V' */

static unsigned long rtl819x_wdt_open_flag;	/* bit 0, via test_and_set_bit */
static int  rtl819x_wdt_expect_close;
static int  rtl819x_wdt_unlocked;		/* raw/biteraw permitted */

/* ------------------------------------------------------------------------
 * Register access.  Same reasoning as rtl819x-gpio.c and rtl819x-timer.c:
 * __raw_readl, not readl -- readl byte-swaps a little-endian device word and
 * an on-chip register on this big-endian part is already in CPU order.
 * CKSEG1ADDR, so the mapping is uncached and unmapped and needs no ioremap,
 * which is also what lets this run before any allocator matters.
 * ------------------------------------------------------------------------ */

static inline void __iomem *rtl819x_wdt_reg(void)
{
	return (void __iomem *)CKSEG1ADDR(RTL819X_WDT_PHYS);
}

static inline u32 rtl819x_wdt_rd(void)
{
	return __raw_readl(rtl819x_wdt_reg());
}

/* THE ONLY WRITE HELPER IN THIS FILE, so `git grep rtl819x_wdt_wr` is the
 * auditable list docs/blind-write-ledger.md counts.  It takes a full word;
 * there is deliberately no `set bit` helper, because that is the shape
 * IRQ-08 measured going wrong (header section 4). */
static inline void rtl819x_wdt_wr(u32 v)
{
	__raw_writel(v, rtl819x_wdt_reg());
}

/* Build a full WDTCNR from intent.  The only place a word is composed. */
static u32 rtl819x_wdt_compose(int running, int ovsel, int kick)
{
	u32 v = (running ? WDTE_RUN : WDTE_STOP) << WDTE_SHIFT;

	if (ovsel >= 0 && ovsel < RTL819X_WDT_NOVSEL)
		v |= rtl819x_wdt_steps[ovsel].enc;
	if (kick)
		v |= WDTCLR;

	/* WDTIND is never set by this driver: writing a status bit whose
	 * semantics are undetermined is how a reading gets destroyed. */
	return v & WDTCNR_KNOWN_MASK;
}

/* Compare the live register against the shadow, ignoring the strobe and the
 * status bit.  Called on every kick, so a foreign FULL-WORD write is caught
 * within one kick_ms.  Header section 5.4 says why this cannot fire in the
 * shipping image and what its positive control is. */
static void rtl819x_wdt_check_foreign_locked(void)
{
	u32 live = rtl819x_wdt_rd();

	if ((live & ~WDTCNR_VOLATILE_MASK) !=
	    (rtl819x_wdt_shadow & ~WDTCNR_VOLATILE_MASK))
		rtl819x_wdt_n_state_foreign++;
}

/* ------------------------------------------------------------------------
 * Arm / stop / kick.  All three take the lock from their callers.
 * ------------------------------------------------------------------------ */

static void rtl819x_wdt_arm_locked(int ovsel)
{
	rtl819x_wdt_shadow = rtl819x_wdt_compose(1, ovsel, 0);
	rtl819x_wdt_ovsel  = ovsel;
	/* Arm and clear in one word: the counter's state before arming is not
	 * this driver's to assume, and WDTCLR in the same store means the
	 * first deadline is a full period rather than whatever was left. */
	rtl819x_wdt_wr(rtl819x_wdt_shadow | WDTCLR);
	rtl819x_wdt_n_arm++;
	rtl819x_wdt_n_hw_kick++;
}

static void rtl819x_wdt_stop_locked(void)
{
	rtl819x_wdt_shadow = rtl819x_wdt_compose(0, rtl819x_wdt_ovsel, 0);
	rtl819x_wdt_wr(rtl819x_wdt_shadow);
	rtl819x_wdt_n_stop++;
}

static void rtl819x_wdt_kick_locked(void)
{
	rtl819x_wdt_check_foreign_locked();
	rtl819x_wdt_wr(rtl819x_wdt_shadow | WDTCLR);
	rtl819x_wdt_n_hw_kick++;
}

/* ------------------------------------------------------------------------
 * The kernel timer.  This is the only thing that keeps the hardware fed, in
 * BOTH armed states; the difference between BOOTGUARD and USER is one
 * time_before() and nothing else, which is deliberate -- two feeding paths
 * would be two places to get wrong.
 * ------------------------------------------------------------------------ */

/* One jiffy floor.  msecs_to_jiffies(kick_ms) is 0 for kick_ms < 1000/HZ =
 * 10 ms here, and mod_timer(jiffies + 0) re-fires on the same tick, which
 * livelocks softirq context -- a watchdog driver that hangs the machine it
 * exists to rescue.  The floor is not a clamp on the PARAMETER, because a
 * caller who asked for 5 ms should see what they get in /proc rather than a
 * silently rewritten value. */
static inline unsigned long rtl819x_wdt_kick_jiffies(void)
{
	unsigned long j = msecs_to_jiffies(kick_ms > 0 ? kick_ms : 0);

	return j ? j : 1;
}

static void rtl819x_wdt_tick(unsigned long unused)
{
	unsigned long flags;
	int rearm = 1;

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);

	switch (rtl819x_wdt_state) {
	case WDT_BOOTGUARD:
		rtl819x_wdt_kick_locked();
		break;
	case WDT_USER:
		if (time_before(jiffies, rtl819x_wdt_deadline)) {
			rtl819x_wdt_kick_locked();
		} else {
			/* Deliberately NOT a kick.  The hardware bites in at
			 * most hw_timeout from the last one.  Counted so a
			 * reader can tell "the deadline expired" from "the
			 * timer never ran". */
			rtl819x_wdt_n_missed++;
		}
		break;
	case WDT_STOPPED:
	case WDT_BITE:
	default:
		rearm = 0;
		break;
	}

	if (rearm)
		mod_timer(&rtl819x_wdt_timer,
			  jiffies + rtl819x_wdt_kick_jiffies());

	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
}

/* ------------------------------------------------------------------------
 * State transitions.
 * ------------------------------------------------------------------------ */

static int rtl819x_wdt_ovsel_ok(int ovsel)
{
	if (ovsel < 0 || ovsel >= RTL819X_WDT_NOVSEL)
		return -EINVAL;
	if (!rtl819x_wdt_steps[ovsel].valid)
		return -EOPNOTSUPP;	/* the OVSEL[2] hole; header section 2 */
	return 0;
}

static int rtl819x_wdt_enter(int state, int ovsel)
{
	unsigned long flags;
	int rc;

	if (state == WDT_BOOTGUARD || state == WDT_USER) {
		rc = rtl819x_wdt_ovsel_ok(ovsel);
		if (rc)
			return rc;
	}

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);
	rtl819x_wdt_state = state;

	if (state == WDT_STOPPED) {
		rtl819x_wdt_stop_locked();
		spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
		del_timer_sync(&rtl819x_wdt_timer);
		return 0;
	}

	if (state == WDT_USER)
		rtl819x_wdt_deadline = jiffies + soft_timeout * HZ;

	rtl819x_wdt_arm_locked(ovsel);
	/* A kick period that rounds to zero jiffies makes mod_timer re-fire
	 * immediately and the box livelocks in softirq -- a watchdog driver
	 * that hangs the machine it is supposed to rescue.  One jiffy floor. */
	mod_timer(&rtl819x_wdt_timer,
		  jiffies + rtl819x_wdt_kick_jiffies());
	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
	return 0;
}

static void rtl819x_wdt_ping(void)
{
	unsigned long flags;

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);
	rtl819x_wdt_deadline = jiffies + soft_timeout * HZ;
	rtl819x_wdt_n_user_ping++;
	/* The ping refreshes the DEADLINE; the kernel timer does the kicking.
	 * A ping that also kicked would make the hardware period depend on
	 * how often userspace happens to call, which is the coupling this
	 * two-layer design exists to remove. */
	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
}

/* ------------------------------------------------------------------------
 * /dev/watchdog
 * ------------------------------------------------------------------------ */

static const struct watchdog_info rtl819x_wdt_ident = {
	.options	= WDIOF_SETTIMEOUT | WDIOF_KEEPALIVEPING |
			  WDIOF_MAGICCLOSE,
	.firmware_version = 1,
	.identity	= "rtl819x-wdt",
};

static int rtl819x_wdt_open(struct inode *inode, struct file *file)
{
	int rc;

	if (test_and_set_bit(0, &rtl819x_wdt_open_flag))
		return -EBUSY;

	rtl819x_wdt_expect_close = 0;

	/* If hw_ovsel landed in the OVSEL[2] hole the arm REFUSES, and an
	 * open that succeeded anyway would hand userspace a file descriptor
	 * for a watchdog that is not running -- the exact shape of a guard
	 * that cannot fail.  Fail the open instead, and give the bit back. */
	rc = rtl819x_wdt_enter(WDT_USER, hw_ovsel);
	if (rc) {
		clear_bit(0, &rtl819x_wdt_open_flag);
		rtl819x_wdt_n_reject++;
		return rc;
	}

	return nonseekable_open(inode, file);
}

static int rtl819x_wdt_release(struct inode *inode, struct file *file)
{
	if (rtl819x_wdt_expect_close && !nowayout) {
		/* Back to BOOTGUARD, not STOPPED.  Header section 4 names this
		 * as a deliberate deviation and says why. */
		rtl819x_wdt_enter(WDT_BOOTGUARD, hw_ovsel);
	} else {
		/* No magic close: the deadline keeps running and the hardware
		 * bites.  That is the contract, not a rejection -- it gets its
		 * own counter so a card can tell an unclean close from a
		 * refused ioctl. */
		rtl819x_wdt_n_unclean_close++;
	}

	rtl819x_wdt_expect_close = 0;
	clear_bit(0, &rtl819x_wdt_open_flag);
	return 0;
}

static ssize_t rtl819x_wdt_write(struct file *file, const char __user *data,
				 size_t len, loff_t *ppos)
{
	size_t i;

	if (!len)
		return 0;

	if (!nowayout) {
		rtl819x_wdt_expect_close = 0;
		for (i = 0; i < len; i++) {
			char c;
			if (get_user(c, data + i))
				return -EFAULT;
			if (c == 'V')
				rtl819x_wdt_expect_close = 1;
		}
	}

	rtl819x_wdt_ping();
	return len;
}

static long rtl819x_wdt_ioctl(struct file *file, unsigned int cmd,
			      unsigned long arg)
{
	void __user *argp = (void __user *)arg;
	int __user *p = argp;
	int v, rc;

	switch (cmd) {
	case WDIOC_GETSUPPORT:
		return copy_to_user(argp, &rtl819x_wdt_ident,
				    sizeof(rtl819x_wdt_ident)) ? -EFAULT : 0;

	case WDIOC_GETSTATUS:
		return put_user(0, p);

	case WDIOC_GETBOOTSTATUS:
		/* ALWAYS 0, and header section 5.2 says that 0 is not evidence
		 * that no watchdog reset happened.  WDIOF_CARDRESET is
		 * deliberately absent from .options for the same reason: this
		 * driver does not claim a capability it cannot honour. */
		return put_user(0, p);

	case WDIOC_KEEPALIVE:
		rtl819x_wdt_ping();
		return 0;

	case WDIOC_SETTIMEOUT:
		if (get_user(v, p))
			return -EFAULT;
		if (v < 1 || v > 3600) {
			rtl819x_wdt_n_reject++;
			return -EINVAL;
		}
		soft_timeout = v;
		rtl819x_wdt_n_settimeout++;
		rtl819x_wdt_ping();
		return put_user(soft_timeout, p);

	case WDIOC_GETTIMEOUT:
		return put_user(soft_timeout, p);

	case WDIOC_GETTIMELEFT:
		v = (int)((long)(rtl819x_wdt_deadline - jiffies) / HZ);
		if (v < 0)
			v = 0;
		return put_user(v, p);

	case WDIOC_SETOPTIONS:
		if (get_user(v, p))
			return -EFAULT;
		rc = -EINVAL;
		if (v & WDIOS_DISABLECARD) {
			/* The real stop, and the one path where userspace can
			 * remove the bootguard.  Counted as n_stop. */
			rtl819x_wdt_enter(WDT_STOPPED, rtl819x_wdt_ovsel);
			rc = 0;
		}
		if (v & WDIOS_ENABLECARD) {
			rc = rtl819x_wdt_enter(WDT_USER, hw_ovsel);
		}
		if (rc)
			rtl819x_wdt_n_reject++;
		return rc;

	default:
		rtl819x_wdt_n_reject++;
		return -ENOTTY;
	}
}

static const struct file_operations rtl819x_wdt_fops = {
	.owner		= THIS_MODULE,
	.llseek		= no_llseek,
	.write		= rtl819x_wdt_write,
	.unlocked_ioctl	= rtl819x_wdt_ioctl,
	.open		= rtl819x_wdt_open,
	.release	= rtl819x_wdt_release,
};

static struct miscdevice rtl819x_wdt_miscdev = {
	.minor	= WATCHDOG_MINOR,	/* 130; 讀 include/linux/miscdevice.h */
	.name	= "watchdog",
	.fops	= &rtl819x_wdt_fops,
};

/* ------------------------------------------------------------------------
 * /proc/rtl819x-wdt
 *
 * Fields only.  FW-47: every capture line is CRLF and a mark interleaves with
 * busybox ash's echo, so a bench card gates on a FIELD and never on a mark.
 *
 * 🔴 THE PAGE BUDGET IS COUNTED, NOT ASSUMED.  read_proc_t sprintfs into ONE
 * 4,096-byte page with no bounds check -- R5-5 hit exactly this and it is why
 * rtl819x-spi's map is two levels of 32 rather than one of 1,024.  Worst case
 * here, every field at its widest (32-bit %lu = 10 digits, %d = 11 with the
 * sign, usec = 10): 478 bytes of scalar fields + 207 of counters + 440 for
 * the ten OVSEL rows at 44 bytes each = 1,125 bytes, 27.5 % of the page.  The
 * headroom is 2,971 bytes, so this dump can roughly triple before the shape
 * has to change; the OVSEL block is fixed at ten rows by the hardware and is
 * the only part that could grow without a code change, and it cannot.
 * ------------------------------------------------------------------------ */

static int rtl819x_wdt_read_proc(char *page, char **start, off_t off,
				 int count, int *eof, void *data)
{
	u32 live = rtl819x_wdt_rd();
	int len = 0;
	int i;

	len += sprintf(page + len, "version %s\n", RTL819X_WDT_VERSION);
	len += sprintf(page + len, "state %d\n", rtl819x_wdt_state);
	len += sprintf(page + len, "state_name %s\n",
		       rtl819x_wdt_state_name[rtl819x_wdt_state & 3]);
	len += sprintf(page + len, "registered %d\n", rtl819x_wdt_registered);
	len += sprintf(page + len, "misc_rc %d\n", rtl819x_wdt_misc_rc);

	/* THE FIELD THAT PROVES CONFIG_RTL_WTDOG=n.  Header section 6. */
	len += sprintf(page + len, "wdtcnr_at_probe %08X\n",
		       rtl819x_wdt_probe_val);
	len += sprintf(page + len, "probe_is_reset %d\n",
		       rtl819x_wdt_probe_val == WDTCNR_RESET_VALUE);
	len += sprintf(page + len, "probe_is_vendor_armed %d\n",
		       rtl819x_wdt_probe_val == WDTCNR_VENDOR_ARMED);
	len += sprintf(page + len, "wdtind_at_probe %d\n",
		       (int)((rtl819x_wdt_probe_val & WDTIND) ? 1 : 0));

	len += sprintf(page + len, "wdtcnr_live %08X\n", live);
	len += sprintf(page + len, "wdtcnr_shadow %08X\n", rtl819x_wdt_shadow);
	len += sprintf(page + len, "shadow_agrees %d\n",
		       (live & ~WDTCNR_VOLATILE_MASK) ==
		       (rtl819x_wdt_shadow & ~WDTCNR_VOLATILE_MASK));

	len += sprintf(page + len, "hw_ovsel %d\n", hw_ovsel);
	len += sprintf(page + len, "armed_ovsel %d\n", rtl819x_wdt_ovsel);
	/* RTL819X_WDT_NOVSEL is 10, which is NOT a power of two -- an `& (N-1)`
	 * here would index 9 as 9 and 10 as 0 and look like it worked. */
	len += sprintf(page + len, "hw_timeout_us %u\n",
		       (rtl819x_wdt_ovsel >= 0 &&
			rtl819x_wdt_ovsel < RTL819X_WDT_NOVSEL)
		       ? rtl819x_wdt_steps[rtl819x_wdt_ovsel].usec : 0u);
	len += sprintf(page + len, "wdt_hz %u\n", (u32)RTL819X_WDT_HZ);
	len += sprintf(page + len, "kick_ms %d\n", kick_ms);
	len += sprintf(page + len, "soft_timeout %d\n", soft_timeout);
	len += sprintf(page + len, "bootguard %d\n", bootguard);
	len += sprintf(page + len, "nowayout %d\n", nowayout);
	len += sprintf(page + len, "unlocked %d\n", rtl819x_wdt_unlocked);
	len += sprintf(page + len, "open %d\n",
		       (int)(rtl819x_wdt_open_flag & 1));
	len += sprintf(page + len, "expect_close %d\n",
		       rtl819x_wdt_expect_close);
	len += sprintf(page + len, "jiffies %lu\n", jiffies);
	len += sprintf(page + len, "deadline %lu\n", rtl819x_wdt_deadline);

	len += sprintf(page + len, "n_hw_kick %lu\n", rtl819x_wdt_n_hw_kick);
	len += sprintf(page + len, "n_user_ping %lu\n", rtl819x_wdt_n_user_ping);
	len += sprintf(page + len, "n_arm %lu\n", rtl819x_wdt_n_arm);
	len += sprintf(page + len, "n_stop %lu\n", rtl819x_wdt_n_stop);
	len += sprintf(page + len, "n_settimeout %lu\n",
		       rtl819x_wdt_n_settimeout);
	len += sprintf(page + len, "n_missed %lu\n", rtl819x_wdt_n_missed);
	len += sprintf(page + len, "n_state_foreign %lu\n",
		       rtl819x_wdt_n_state_foreign);
	len += sprintf(page + len, "n_bite %lu\n", rtl819x_wdt_n_bite);
	len += sprintf(page + len, "n_wedge %lu\n", rtl819x_wdt_n_wedge);
	len += sprintf(page + len, "n_reject %lu\n", rtl819x_wdt_n_reject);
	len += sprintf(page + len, "n_unclean_close %lu\n",
		       rtl819x_wdt_n_unclean_close);

	/* Ten rows, one per OVSEL, so the hole at 4..7 is legible ON THE BOARD
	 * and a card can predict every one of them from this file before the
	 * board is powered.  `enc` is what would be written; `valid 0` means
	 * this driver refuses it. */
	for (i = 0; i < RTL819X_WDT_NOVSEL; i++)
		len += sprintf(page + len, "ovsel%d enc %08X usec %u valid %d\n",
			       i, rtl819x_wdt_steps[i].enc,
			       rtl819x_wdt_steps[i].usec,
			       rtl819x_wdt_steps[i].valid);

	*eof = 1;
	return len;
}

/* ------------------------------------------------------------------------
 * Verbs.
 * ------------------------------------------------------------------------ */

/* THE POSITIVE CONTROL FOR D1, and the reason it is a verb rather than a
 * failure mode: a watchdog that has never been observed biting is a watchdog
 * nobody has tested.
 *
 * The sequence is shaped by what the console can measure.  The mark goes out
 * first and mdelay(50) runs with interrupts STILL ON, so busybox ash's echo
 * (FW-41) and the UART both drain and the line before the bite is quiet.
 * Only then are interrupts disabled -- which is what stops the kernel timer
 * from kicking -- and only then is the counter armed.  So the gap the capture
 * measures runs from the last byte of RLXFW-W-GO to the loader's first byte,
 * and it is hw_timeout plus a constant that cancels between two rungs. */
static int rtl819x_wdt_verb_bite(int ovsel, u32 raw, int use_raw)
{
	unsigned long flags;
	u32 word;

	if (!use_raw) {
		int rc = rtl819x_wdt_ovsel_ok(ovsel);
		if (rc)
			return rc;
		word = rtl819x_wdt_compose(1, ovsel, 1);
	} else {
		if (!rtl819x_wdt_unlocked)
			return -EPERM;
		/* A raw word may set any OVSEL bit, including the two this
		 * driver cannot decode -- that is what biteraw is FOR -- but
		 * WDTE is still checked, because a WDTE that is neither 0x00
		 * nor 0xA5 is a typo and not an experiment. */
		if (((raw >> WDTE_SHIFT) & 0xFFu) != WDTE_RUN)
			return -EINVAL;
		word = raw;
	}

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);
	rtl819x_wdt_state = WDT_BITE;
	rtl819x_wdt_n_bite++;
	/* 🔴 DISARM FIRST, and this is not tidiness.  The 50 ms drain below
	 * runs with interrupts on but with the kick path already refusing
	 * (state == WDT_BITE), so a dog left armed from BOOTGUARD would be
	 * counting down through it -- and at hw_ovsel 0 (2.190 ms) or 3
	 * (17.517 ms) it would bite DURING the drain, before the rung being
	 * timed was ever programmed.  The gap would come out ~50 ms for every
	 * rung and the ladder would read as a flat line that looked like a
	 * result.  Stopping here makes the measured interval start at the
	 * arm below and nowhere else. */
	rtl819x_wdt_shadow = rtl819x_wdt_compose(0, rtl819x_wdt_ovsel, 0);
	rtl819x_wdt_wr(rtl819x_wdt_shadow);
	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);

	rlxfw_markx("W-BITE", word);
	mdelay(50);			/* interrupts on: drain the console */

	local_irq_disable();		/* the kernel timer cannot run now */
	rlxfw_puts("RLXFW-W-GO\n");	/* the last byte before the bite */
	rtl819x_wdt_shadow = word & ~WDTCLR;
	rtl819x_wdt_wr(word);
	for (;;)
		;			/* the hardware ends this function */

	return 0;			/* not reached; the compiler wants it */
}

/* THE POSITIVE CONTROL FOR n_state_foreign.  It writes WDTCNR behind the
 * shadow's back, which is exactly what a second owner of this register would
 * look like, so the counter is observed firing at least once instead of being
 * a zero nobody has ever seen move.  Same shape as rtl819x-spi's `wedge`. */
static int rtl819x_wdt_verb_wedge(void)
{
	unsigned long flags;

	if (!rtl819x_wdt_unlocked)
		return -EPERM;

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);
	/* Stop pattern with a different OVSEL from the shadow's.  Stopped, so
	 * this cannot start a countdown; different, so the masked comparison
	 * must notice. */
	rtl819x_wdt_wr(rtl819x_wdt_compose(0, 9, 0) ^ OVSEL_B1);
	rtl819x_wdt_n_wedge++;
	rtl819x_wdt_check_foreign_locked();
	/* Put the register back the way the shadow says it should be, so the
	 * wedge costs one counted disagreement and no state. */
	rtl819x_wdt_wr(rtl819x_wdt_shadow);
	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
	return 0;
}

static int rtl819x_wdt_verb_raw(u32 raw)
{
	unsigned long flags;
	u32 e;

	if (!rtl819x_wdt_unlocked)
		return -EPERM;

	e = (raw >> WDTE_SHIFT) & 0xFFu;
	if (e != WDTE_RUN && e != WDTE_STOP)
		return -EINVAL;

	spin_lock_irqsave(&rtl819x_wdt_lock, flags);
	rtl819x_wdt_shadow = raw & ~WDTCLR;
	rtl819x_wdt_wr(raw);
	spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
	rlxfw_markx("W-RAW", raw);
	return 0;
}

static int rtl819x_wdt_parse_int(const char *arg, long *out)
{
	char *end;
	unsigned long v = simple_strtoul(arg, &end, 0);

	if (end == arg)
		return -EINVAL;
	*out = (long)v;
	return 0;
}

static int rtl819x_wdt_write_proc(struct file *file, const char __user *buffer,
				  unsigned long count, void *data)
{
	char buf[32];
	unsigned long n = count;
	long v;
	int ret;

	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "stop"))
		ret = rtl819x_wdt_enter(WDT_STOPPED, rtl819x_wdt_ovsel);
	else if (!strcmp(buf, "bootguard"))
		ret = rtl819x_wdt_enter(WDT_BOOTGUARD, hw_ovsel);
	else if (!strcmp(buf, "kick")) {
		unsigned long flags;
		spin_lock_irqsave(&rtl819x_wdt_lock, flags);
		if (rtl819x_wdt_state == WDT_BOOTGUARD ||
		    rtl819x_wdt_state == WDT_USER)
			rtl819x_wdt_kick_locked();
		else
			rtl819x_wdt_n_reject++;
		spin_unlock_irqrestore(&rtl819x_wdt_lock, flags);
		ret = 0;
	} else if (!strncmp(buf, "ovsel ", 6)) {
		ret = rtl819x_wdt_parse_int(buf + 6, &v);
		if (!ret) {
			ret = rtl819x_wdt_ovsel_ok((int)v);
			if (!ret) {
				hw_ovsel = (int)v;
				if (rtl819x_wdt_state == WDT_BOOTGUARD ||
				    rtl819x_wdt_state == WDT_USER)
					ret = rtl819x_wdt_enter(
						rtl819x_wdt_state, (int)v);
			}
		}
	} else if (!strncmp(buf, "kickms ", 7)) {
		/* Exists for ONE experiment: setting the kernel-timer period
		 * LONGER than the hardware timeout turns BOOTGUARD into a
		 * detector for a second feeder.  See the file header, § "am I
		 * the only feeder".  Deliberately not clamped against
		 * hw_timeout -- a value that guarantees a bite is exactly what
		 * the cell asks for, and a driver that refused it would be
		 * refusing the measurement. */
		ret = rtl819x_wdt_parse_int(buf + 7, &v);
		if (!ret) {
			if (v < 1 || v > 60000)
				ret = -EINVAL;
			else {
				unsigned long flags;
				kick_ms = (int)v;
				spin_lock_irqsave(&rtl819x_wdt_lock, flags);
				if (rtl819x_wdt_state == WDT_BOOTGUARD ||
				    rtl819x_wdt_state == WDT_USER)
					mod_timer(&rtl819x_wdt_timer,
						  jiffies +
						  rtl819x_wdt_kick_jiffies());
				spin_unlock_irqrestore(&rtl819x_wdt_lock,
						       flags);
				rlxfw_markx("W-KICKMS", (unsigned)v);
			}
		}
	} else if (!strncmp(buf, "bite ", 5)) {
		ret = rtl819x_wdt_parse_int(buf + 5, &v);
		if (!ret)
			ret = rtl819x_wdt_verb_bite((int)v, 0, 0);
	} else if (!strncmp(buf, "biteraw ", 8)) {
		ret = rtl819x_wdt_parse_int(buf + 8, &v);
		if (!ret)
			ret = rtl819x_wdt_verb_bite(-1, (u32)v, 1);
	} else if (!strncmp(buf, "raw ", 4)) {
		ret = rtl819x_wdt_parse_int(buf + 4, &v);
		if (!ret)
			ret = rtl819x_wdt_verb_raw((u32)v);
	} else if (!strcmp(buf, "wedge"))
		ret = rtl819x_wdt_verb_wedge();
	else if (!strcmp(buf, "unlock")) {
		rtl819x_wdt_unlocked = 1;
		ret = 0;
	} else if (!strcmp(buf, "lock")) {
		rtl819x_wdt_unlocked = 0;
		ret = 0;
	} else {
		rtl819x_wdt_n_reject++;
		return -EINVAL;
	}

	if (ret)
		rtl819x_wdt_n_reject++;

	return ret ? ret : (int)count;
}

/* ------------------------------------------------------------------------
 * Registration.
 *
 * late_initcall, for one reason and not by convention: BOOTGUARD arms the
 * hardware and then depends on the kernel timer wheel to feed it, so it must
 * not run before the timer wheel and the tick are up.  R5-3b-2 puts this
 * driver's own clockevent in at late_initcall too and prints RLXFW-TA8 when
 * clockevents_register_device() returns; the ordering between TA8 and W0 in
 * the boot capture is therefore an observable, not an assumption, and if W0
 * ever precedes TA8 the bootguard is arming against a tick that does not yet
 * exist and this initcall level is wrong.
 * ------------------------------------------------------------------------ */

static int __init rtl819x_wdt_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("W0");

	/* Latched BEFORE anything is written, so the value is WDTCNR as the
	 * boot left it.  A5000000 = nobody armed it (CONFIG_RTL_WTDOG=n, the
	 * shipping case).  00600000 = bsp_timer_init armed it at OVSEL=3
	 * (CONFIG_RTL_WTDOG=y, the positive-control build). */
	rtl819x_wdt_probe_val = rtl819x_wdt_rd();
	rtl819x_wdt_shadow = rtl819x_wdt_probe_val;
	rlxfw_markx("W1", rtl819x_wdt_probe_val);

	setup_timer(&rtl819x_wdt_timer, rtl819x_wdt_tick, 0);

	rtl819x_wdt_misc_rc = misc_register(&rtl819x_wdt_miscdev);
	rtl819x_wdt_registered = (rtl819x_wdt_misc_rc == 0);
	rlxfw_markx("W2", (unsigned)rtl819x_wdt_misc_rc);

	if (bootguard) {
		int rc = rtl819x_wdt_enter(WDT_BOOTGUARD, hw_ovsel);
		/* W3 is the return code and not a bare mark: a bootguard that
		 * refused because hw_ovsel landed in the OVSEL[2] hole is a
		 * different boot from one that armed, and the two must not
		 * look the same in a capture. */
		rlxfw_markx("W3", (unsigned)rc);
	} else {
		rlxfw_markx("W3", 0xFFFFFFFFu);
	}

	/* Read back through the same path a /proc reader would use, so the
	 * capture carries proof the arm reached the silicon without needing a
	 * shell. */
	rlxfw_markx("W4", rtl819x_wdt_rd());

	pde = create_proc_entry(RTL819X_WDT_PROC_NAME, 0644, NULL);
	if (!pde) {
		/* /dev/watchdog stays registered.  Losing /proc costs the
		 * verbs, not the watchdog, and tearing down a working guard
		 * because its debug interface failed is the worse outcome. */
		rlxfw_mark("W5-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_wdt_read_proc;
	pde->write_proc = rtl819x_wdt_write_proc;
	rlxfw_mark("W5");

	return 0;
}

late_initcall(rtl819x_wdt_init);

MODULE_AUTHOR("rlxfw");
MODULE_DESCRIPTION("RTL8196E watchdog (WDTCNR)");
MODULE_LICENSE("GPL");
MODULE_ALIAS_MISCDEV(WATCHDOG_MINOR);
