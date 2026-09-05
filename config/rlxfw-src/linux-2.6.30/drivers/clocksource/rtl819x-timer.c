/*
 * rtl819x-timer -- a Linux clocksource on the RTL8196E's Timer/Counter 1.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-1, 2026-09-03.  It is staged into
 * drivers/clocksource/ by tools/rlxfw-marks.py from config/rlxfw-src/;
 * config/rlxfw-marks.tsv carries the one Kbuild line that links it.
 *
 * WRITTEN BLIND, AND THAT WORD HAS A LEDGER -- AND A DATE.
 * docs/blind-write-ledger.md 4.3 is the frozen record of what this
 * repository had read of anyone else's timer ON 2026-09-03, WHEN THE FIRST
 * VERSION OF THIS FILE WAS WRITTEN: one string literal of the vendor's
 * (`"rlx timer"`, arch/rlx/kernel/rlx-cevt.c:139,226, taken for an
 * arch/rlx-vs-arch/mips proof), the weak generic kernel/sched_clock.c:39, and
 * arch/rlx/kernel/rlx-time.c with zero citations.  Neither vendor file was
 * opened to write it.  Every number below comes from SPEC.md -- this die's
 * own readings -- or from the RTL8196E datasheet, which is the specification
 * and not an implementation.
 *
 * 🔴 THE BLIND CLAIM IS BOUNDED BY A DATE AND NOT BY THIS FILE'S CONTENTS.
 * On 2026-09-04, R5-10 opened arch/rlx/bsp/timer.c and arch/rlx/kernel/
 * rlx-time.c IN FULL (ledger 4.2), so the sentence above is history and not
 * a present-tense claim.  What survives unqualified is the ORIGINAL version:
 * its source predates that reading by a day, which git log can check and
 * this comment cannot.  Everything added in version 2.0 -- the derived rate,
 * the interrupt path -- was written AFTER, and docs/driver-diff.md's timer
 * section must say so rather than inherit the word.
 *
 * 🔴 2026-09-06, R5-3b: arch/rlx/kernel/rlx-cevt.c WAS OPENED IN FULL, and
 * everything in version 3.0 was written after it.  Ledger 4.3 carries the
 * row; the depth moves line -> full for that path.  What was taken is
 * stated there and it is not a register sequence -- the vendor's TC0
 * clockevent programs no timer register at all (its set_mode and
 * set_next_event are stubs).  What was taken is the RATING, 100, which is
 * the number this driver has to beat, and the fact that its features word
 * carries CLOCK_EVT_FEAT_PERIODIC alone.  Both are facts about what this
 * driver must coexist with, not about how to drive TC1.
 *
 * WHAT VERSION 2.0 CHANGED, AND WHY EACH WAS FORCED BY A READING
 * (R5-3a, 2026-09-04; the /proc format moved, so RTL819X_TC_VERSION moved):
 *
 *   1. The count rate is DERIVED at init, two independent ways, instead of
 *      being the compiled-in 14,286,057.  量 seating 11: under Linux the
 *      divider is 1000 and not 14, so the compiled figure was 71.43x high
 *      (SPEC.md REG-11, CLK-22).
 *   2. The shift is derived WITH it, because it cannot be a constant once the
 *      rate is not.  量 at the desk: clocksource_hz2mult() returns u32 and
 *      2.6.30 has no clocks_calc_mult_shift(); at 200,000 Hz the old shift of
 *      24 gives an exact mult of 83,886,080,000, which TRUNCATES to
 *      2,281,701,376 -- 136 ns per count against a true 5,000.  Fixing the
 *      reported rate without the shift would have shipped a worse number
 *      than the bug.
 *   3. tc1_ext is advanced by a kernel timer, not by whoever reads /proc.
 *      量 TM-5c: 462 s with no reader left tc1_ext 92,362,366 counts behind
 *      the counter and tc1_ext_trusted still reading 1.
 *   4. tc1_ext_trusted is decided in JIFFIES.  Its old test was on a gap
 *      already reduced mod 2^27, so a gap of one full period plus delta read
 *      as delta -- 量 TM-5b2: a real 140,693,532-count gap reported as
 *      6,475,672 and trusted.
 *   5. The interrupt path exists, in four separately-typed steps.  See
 *      "THE INTERRUPT PATH" below.
 *
 * WHY TIMER/COUNTER 1 AND NOT 0.
 * TC0 is the vendor's system tick and this driver never writes it.  TC0 is
 * also unusable as a clocksource on its own: SPEC.md CLK-17 records that it
 * wraps every 142,858 counts -- 9.9998 ms, and NOT a power of two -- so the
 * `(now - last) & mask` arithmetic every clocksource core uses is wrong for
 * it, and the software alternative (`if (d < 0) d += 142858`) needs a read
 * more often than once per 10 ms.  At CONFIG_HZ=100 nothing in this kernel
 * can guarantee that.
 *
 * TC1 is idle on this unit: 量 SPEC.md REG-06/REG-08/REG-09 -- TC1DATA = 0,
 * TC1CNT = 0, and TCCNR = 0xC0000000, whose TC1En (bit 29) and TC1Mode
 * (bit 28) are both clear.  Programming it with a power-of-two period makes
 * the mask arithmetic exact.  docs/probe3-cells.md 8 already weighed this
 * write once and declined it, recording it as "the upgrade path for R5-0";
 * this is that path taken, with the guards that payload could not afford.
 *
 * WHY ARMING IS A WRITE TO /proc AND NOT SOMETHING init DOES.
 * Enabling TC1 sets bits in TCCNR, which is the same register that holds
 * TC0En.  Two hazards follow and neither is settled by any source this
 * project has:
 *
 *   (1) a read-modify-write of TCCNR could disturb TC0 and stop the system
 *       tick;
 *   (2) TCIR's TC1IP (bit 28) latches on a TC1 timeout, and something has to
 *       stop that reaching the vendor's timer handler.  D Table 14/15 say it
 *       does not have to: the global controller gives the two timers SEPARATE
 *       bits -- GIMR bit 8 TC0_IE / bit 9 TC1_IE, GISR bit 8 TC0_IP / bit 9
 *       TC1_IP -- so a TC1 timeout raises bit 9, which is a different line
 *       from the one the vendor's tick uses.  量 SPEC.md REG-01: GIMR reads
 *       0x00008100 at the loader prompt, i.e. TC0_IE set and TC1_IE CLEAR.
 *
 *       🔴 2026-09-04: hazard (2)'s PRECONDITION was never met, and that is
 *       not the same as the hazard being wrong.  量 seating 11 (TM-5b2): over
 *       703.46 s and a full 2^27 period, TC1IP stayed 0 -- because
 *       rtl819x_tc1_arm() writes TCCNR and TC1DATA and NEVER writes TCIR bit
 *       30, the timer block's own interrupt enable.  Version 1.0 armed a
 *       counter and did not arm an interrupt.  The sentence above is a
 *       prediction this file made and could not test; version 2.0's `armirq`
 *       is what tests it (docs/interrupt-map.md 3.2, notes/timer-driver.md 9).
 *
 *       🟢 2026-09-04, seating 12 (CFG-2): what Linux leaves in GIMR IS now
 *       established, and this paragraph used to say it was not.  量:
 *       gimr_at_init = 0x00209100 -- bits 8, 12, 15 and 21 -- so TC0's ICTL
 *       position (bit 8) and UART0's (bit 12) are unmasked and TC1's (bit 9)
 *       is CLEAR, at arch_initcall, before this driver writes anything.
 *       After request_irq(25) it reads 0x00209300: bit 9 and nothing else,
 *       set by bsp_ictl_irq_unmask on this driver's behalf.  The driver
 *       still never writes GIMR; it READS it, refuses to arm while bit 9 is
 *       set by anyone but itself, and prints both words.
 *
 *       ⚠️ Bit 12 being set is not idle trivia.  讀 arch/rlx/bsp/irq.c:
 *       bsp_ictl_irq_dispatch() is an `else if` chain that dispatches ONE
 *       source per exception and tests BSP_UART0_IP (bit 12) and
 *       BSP_UART1_IP (bit 13) BEFORE BSP_TC1_IP (bit 9).  量 seating 12,
 *       EX-19: the console's 41,824 interrupts arrived as `8: RLX LOPI
 *       serial`, i.e. down the LOPI vector and not through this chain, and
 *       gisr read 0x88000004 with bit 12 clear.  So the starvation the
 *       chain would permit does not happen in this configuration -- which
 *       is a measurement about this board, not a property of the code.
 *
 * A driver that armed at boot would put both hazards in front of the boot,
 * where a hang costs the whole power cycle -- this project's most expensive
 * unit.  Arming from userspace puts them after a shell, where the failure is
 * observed, bounded and reversible, and where GIMR can be READ first.  R5-2's
 * reading is what makes the boot-time path (R5-3) safe to write; until then
 * this file boots inert and writes nothing.
 *
 * WHY RATING 0.
 * 讀 kernel/time/clocksource.c: clocksource_enqueue() inserts sorted by
 * rating and select_clocksource() takes the list head, so the highest rating
 * wins.  clocksource_jiffies has rating 1 and is always registered.  A
 * rating of 1 here would tie with it and rely on enqueue's `>=` to break the
 * tie in jiffies' favour -- true today, and an implementation detail.  0 is
 * strictly lower, so this clocksource cannot become the system time base by
 * accident whether or not arch/rlx registers one of its own.  The rating
 * band documented in include/linux/clocksource.h starts at 1; 0 is outside
 * it deliberately, and this comment is the reason.  R5-3 raises it.
 *
 * 🔄 R5-3b: R5-3 does NOT raise it, and that is a correction rather than a
 * deferral.  The number above is the CLOCKSOURCE's rating and it stays 0.
 * What R5-3b raises is a different field on a different structure -- the
 * CLOCKEVENT's -- because on this part the two cannot be the same timer
 * channel at the same time.  See THE CLOCKEVENT below.
 *
 * WHAT THIS FILE DOES NOT KNOW, ON PURPOSE.
 * Whether arch/rlx registers a clocksource of its own is not looked up here.
 * The experiment does not need it: /sys/devices/system/clocksource/
 * clocksource0/available_clocksource answers it on the silicon, and not
 * knowing is what keeps docs/driver-diff.md's timer rows worth writing.
 *
 * THE CLOCKEVENT, AND WHY IT IS A MODE AND NOT AN ADDITION  (R5-3b)
 * -----------------------------------------------------------------
 * 🔴 TC1 HAS ONE RELOAD REGISTER AND THE TWO JOBS WANT DIFFERENT VALUES.
 *
 *   the clocksource wants a POWER-OF-TWO period, because every clocksource
 *   core computes (now - last) & mask and that is exact only when the
 *   hardware period is mask + 1;
 *
 *   a 100 Hz clockevent wants hz_used / HZ = 200,000 / 100 = 2,000 counts,
 *   which is 2^4 x 125 and not a power of two -- and no power of two at or
 *   above this driver's floor of 2^8 divides it.
 *
 * So one TC1 cannot be both.  `mode cs` and `mode ce` are that fact made
 * typeable; arm() writes a different TC1DATA under each and registers the
 * clocksource under only the first.
 *
 * 🔴 AND THE OBVIOUS ESCAPE IS CLOSED BY A MEASUREMENT THIS PROJECT ALREADY
 * OWNS.  The standard way to keep both is a software-extended clocksource:
 * the tick ISR adds one period to a 64-bit accumulator, and read() returns
 * accumulator + counter.  It has one race -- between the counter wrapping and
 * the ISR running, read() goes BACKWARDS by up to one period -- and the
 * standard fix is to ask the hardware whether a wrap is pending and add a
 * period if it is.  On this part that question cannot be asked: SPEC.md
 * IRQ-09, 量 seating 12 -- the vendor's bsp_timer_ack() is `REG32(BSP_TCIR)
 * |= BSP_TC0IP`, a read-modify-write on a register whose IP bits are
 * write-1-to-clear, called a hundred times a second, so any pending bit in
 * TCIR has a lifetime of at most one 10 ms tick.  A wrap-pending test built
 * on TC1IP would be right most of the time, and a clocksource that is right
 * most of the time hands the timekeeping core a backwards step that its
 * unsigned (now - last) & mask turns into a jump of nearly the whole mask.
 * The escape is therefore REFUTED rather than skipped, and the refutation is
 * a reading of this die and not a preference.
 *
 * WHY PERIODIC AND NOT ONESHOT.
 * 量, on the .config this image is built from: CONFIG_NO_HZ and
 * CONFIG_HIGH_RES_TIMERS are not set and CONFIG_TICK_ONESHOT is absent, so
 * kernel/time/tick-common.c cannot put the tick device into oneshot mode at
 * all.  A oneshot implementation would be a path this configuration can never
 * execute, and an untested path in the one driver that can stop the board
 * booting is worth less than the sentence saying it is absent.
 *
 * THE HANDOVER, AND THE FOUR THINGS READ OUT OF THE CORE THAT DECIDE IT
 * (讀 kernel/time/tick-common.c and kernel/time/clockevents.c, 2.6.30):
 *
 *   1. tick_check_new_device() takes the new device only if
 *      `curdev->rating >= newdev->rating` is FALSE.  The vendor's rlx
 *      clockevent is rating 100 (讀 arch/rlx/kernel/rlx-cevt.c:234), so a
 *      rating of exactly 100 does NOT take over.  It has to be strictly
 *      greater.  That inequality is what makes the negative control below
 *      free.
 *   2. The "prefer one shot capable devices" test only BLOCKS a non-oneshot
 *      newdev when curdev already has oneshot.  It never promotes.  So
 *      advertising ONESHOT would buy nothing even if it were safe.
 *   3. tick_setup_device() sets the OLD device's event_handler to
 *      clockevents_handle_noop.  So after the handover the vendor's TC0
 *      interrupt still fires at 100 Hz, still runs its own ISR -- which still
 *      pets the hardware watchdog (CONFIG_RTL_WTDOG=y) and still runs
 *      bsp_timer_ack() -- and no longer advances jiffies.  Nothing
 *      double-counts, and nothing stops.
 *   4. The order of set_mode calls is SHUTDOWN then PERIODIC, both inside
 *      tick_device_lock with interrupts off: clockevents_exchange_device()
 *      shuts the new device down before tick_setup_periodic() starts it.
 *      This driver's set_mode therefore must not treat SHUTDOWN as "stop the
 *      hardware", because the hardware is what the next call depends on.
 *
 * WHY set_mode TOUCHES NO REGISTER ON THE NORMAL PATH.
 * arm() has already programmed TC1DATA and TCCNR, and `cevt` refuses unless a
 * read-back says so.  set_mode(PERIODIC) therefore VERIFIES and records; it
 * writes only if the verification fails, and counts that as ce_hw_bad.  The
 * asymmetry is deliberate: the failure mode of "an interrupt arrives and does
 * nothing" is a slow clock, and the failure mode of "no interrupt arrives" is
 * a board that has to be power-cycled.
 *
 * 🔴 THE HANDOVER IS ONE-WAY WITHIN A BOOT, AND NOTHING HERE HIDES THAT.
 * The tick core exposes no way to give a device back: tick_cpu_device is a
 * static per-cpu variable and tick_device_lock is a static spinlock, neither
 * exported.  So once either clock_event_device of this driver is registered,
 * `disarm` REFUSES -- stopping TC1 under a registered device would stop the
 * system tick with no way to restart it.  Recovery is a power cycle.
 *
 * WHY THERE ARE TWO clock_event_devices.
 * ce_mode reading CLOCK_EVT_MODE_PERIODIC after `cevt` is the evidence that
 * the handover happened.  On its own that is an argument from source: the
 * field is written only by clockevents_set_mode(), which is called only from
 * the two places above.  The probe device turns it into a measurement.  It is
 * identical in every respect except a rating of 99 -- strictly below the
 * vendor's 100 -- so the core is REQUIRED to decline it, and the same fields
 * read on the same silicon in the same seating come back
 * ce_probe_mode = UNUSED and ce_probe_mode_calls = 0.  Without that arm, a
 * reading of PERIODIC has no negative control.  It costs one /proc write and
 * carries no risk, and its set_mode is the SAME function as the real one, so
 * a surprise selection would leave a running tick rather than a dead board.
 *
 * THE PRE-CHECK, AND WHY IT IS NOT A BENCH-CARD RULE.
 * `cevt` refuses unless this driver has itself watched its interrupt arrive
 * at the rate the kernel's tick needs -- irq_count advancing 1:1 with jiffies,
 * over at least RTL819X_CE_MIN_J jiffies since reqirq, within
 * RTL819X_CE_TOL_PERMILLE.  The window costs nothing: it is whatever time
 * passes between `reqirq` and `cevt`, which a card spends reading /proc
 * anyway.  A stop-if written on a card would be a rule whose correctness
 * depends on the operator reading two numbers correctly at 38400 baud; this
 * repository has ruled that shape out once already (CLAUDE.md, the H601
 * pre-read containment), so the check belongs to the thing that would be
 * destroyed.
 *
 * WHAT THE PRE-CHECK CANNOT DO, written here because a guard whose limits are
 * not written down gets trusted past them:
 *   * it measures TC1 delivery while the VENDOR still drives jiffies.  It
 *     cannot see a failure that only appears once jiffies depends on TC1 --
 *     for instance a handler that deadlocks against a lock tick_periodic
 *     takes.  Nothing at the desk can see that either; it is what the first
 *     cell is for.
 *   * it is a ratio over one window.  A delivery that stops later passes it.
 *
 * THE INTERRUPT PATH, AND WHY IT IS FOUR VERBS AND NOT ONE  (R5-3a)
 * -----------------------------------------------------------------
 * docs/interrupt-map.md 3.1: a TC1 interrupt crosses SEVEN gates in three
 * register files.  This driver owns two of them (TCCNR's TC1En, TCIR's
 * TC1IE); the kernel already owns GIMR bit 9 and Status.
 *
 *   armirq   sets TCIR bit 30 alone.  GIMR bit 9 stays clear, so nothing can
 *            be DELIVERED -- 量 RUNSHEET C5, 2026-08-24: on this die a GIMR
 *            mask stops delivery and NOT latching.  Zero risk by measurement
 *            rather than by argument.
 *   ackip    writes 1 to TCIR bit 28 and reads it back.  This is the only
 *            test this project has of D Table 25's write-1-to-clear claim,
 *            which is single-source.
 *   reqirq   request_irq(25, ...).  The first real delivery.
 *   freeirq  gives it back.
 *
 * and R5-3b adds four more, in the order a card must use them:
 *
 *   mode ce   selects the clockevent period.  Disarmed only.
 *   rating N  the clockevent's rating.  Before registration only.
 *   cevtprobe registers the rating-99 device.  The negative control.
 *   cevt      registers the real one.  THE HANDOVER, and one-way.
 *   cereload  makes the period deliberately wrong, AFTER the handover, so
 *             that the board's own clock can be seen to follow it against
 *             the host's.  Refused before `cevt` by `cevt`'s own -ERANGE.
 *
 * 🔴 reqirq REFUSES unless this driver has ITSELF watched ackip take TC1IP
 * from 1 to 0.  The reason is mechanical, not cautious.  讀 arch/rlx/bsp/irq.c:
 * the ICTL irq_chip's .mask_ack is bsp_ictl_irq_mask -- it MASKS and does not
 * ack the device -- and 讀 kernel/irq/chip.c handle_level_irq(): after the
 * handler returns it unmasks unless IRQ_DISABLED.  So a handler that cannot
 * clear TC1IP re-triggers immediately and the board is gone.  A stop-if on a
 * bench card would be a rule whose correctness depends on the experiment
 * coming out the expected way; this repository has already ruled that shape
 * out once (CLAUDE.md, the H601 pre-read containment).  The precondition is
 * therefore checked by the thing that would be destroyed.
 *
 * 🔴 AND THE HANDLER CARRIES THE SAME GUARD AT RUN TIME.  It clears TC1IP,
 * READS IT BACK, and if the bit is still set calls disable_irq_nosync() --
 * which sets IRQ_DISABLED, which is the flag handle_level_irq() consults
 * before unmasking.  An interrupt storm becomes one line in /proc.
 *
 * WHAT NEITHER GUARD CAN DO, stated here because a guard whose limits are not
 * written down gets trusted past them:
 *   * it cannot save a handler that HANGS -- nothing here has a watchdog;
 *   * it cannot act before the first delivery, so if merely unmasking wedges
 *     the part, the guard never runs;
 *   * ackip proving write-1-to-clear at one instant does not prove it at
 *     every instant. It is n=1 by construction and the /proc file says so.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/clocksource.h>
#include <linux/clockchips.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/jiffies.h>
#include <linux/time.h>
#include <linux/timer.h>
#include <linux/interrupt.h>
#include <linux/delay.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/page.h>
#include <asm/div64.h>
#include <asm/rlxregs.h>
#include <asm/uaccess.h>

/* ------------------------------------------------------------------------
 * The register block.  Base and offsets: D (RTL8196E datasheet) 8.2.1
 * Table 19, and every one of them read on this die -- SPEC.md REG-05..REG-12.
 * Two sources agree on all seven, which is what CLAUDE.md requires before a
 * register value enters code.
 * ------------------------------------------------------------------------ */
#define RTL819X_TC_PHYS		0x18003100	/* 0xB8003100 through KSEG1 */

/* The global interrupt controller, 0x100 below the timer block.  READ ONLY
 * here -- this driver never writes either word.  D 8.1 Table 13; the two
 * values on this die are SPEC.md REG-01 and REG-02. */
#define RTL819X_INTC_PHYS	0x18003000	/* 0xB8003000 */
#define RTL819X_GIMR		0x00		/* REG-01, D Table 14 */
#define RTL819X_GISR		0x04		/* REG-02, D Table 15 */

/*
 * 🆕 R5-3a: the four routing registers, READ ONLY, in the same block.
 *
 * `IRR0`-`IRR3` are eight 4-bit destination-select fields each, written
 * unconditionally by `bsp_irq_init()` on every boot (讀 arch/rlx/bsp/irq.c:
 * 222-225).  SPEC.md: `REG-32`, `REG-03`, `REG-04`, `REG-33`.  THREE OF THE
 * FOUR HAVE NEVER BEEN READ AT ALL, and `IRR1`'s one reading is at the loader
 * prompt (`0x30050004`), which `bsp_irq_init` overwrites -- so under Linux
 * every nibble should differ.
 *
 * 🔴 They are here because there is no other way to read them on this board.
 * 量 2026-09-04, config/rlxfw-initramfs.tsv: this image carries ELEVEN
 * busybox symlinks and `devmem` is not one of them.  A read that needs an
 * applet the image does not have is a read that does not happen.
 */
#define RTL819X_IRR0		0x08		/* REG-32 */
#define RTL819X_IRR1		0x0c		/* REG-03 */
#define RTL819X_IRR2		0x10		/* REG-04 */
#define RTL819X_IRR3		0x14		/* REG-33 */

/* D Table 14/15: the two timers have SEPARATE bits at the global controller,
 * which is what bounds this driver's second hazard.  A TC1 timeout raises
 * GISR bit 9, not the bit 8 the vendor's tick uses, and GIMR bit 9 is the
 * mask for it -- 量 REG-01, clear at the loader prompt. */
#define RTL819X_INTC_TC0	(1u << 8)
#define RTL819X_INTC_TC1	(1u << 9)

/*
 * TC1's Linux IRQ number.  讀 arch/rlx/bsp/bspchip.h:102,
 * `BSP_TC1_IRQ (BSP_IRQ_ICTL_BASE + 9)` with `BSP_IRQ_ICTL_BASE` = 16, so 25.
 * docs/interrupt-map.md 1 and 3.1.
 *
 * 🔴 Written as a literal rather than by including bspchip.h, for the same
 * reason every register address in this file is a literal: that header is the
 * BSP's private one, it is not on a driver's include path, and depending on it
 * would put a vendor header in the include graph of a file whose whole claim
 * is that it did not read one.  The derivation is in the comment; the check
 * that it is still true is BUILD_BUG_ON below and the /proc `irq_num` line.
 *
 * ⚠️ TC0 is IRQ 13 and is NOT on this domain -- it is a LOPI line, masked in
 * ESTATUS through mflxc0.  The two timers in one register block do not share
 * a route, and nothing in this file goes anywhere near TC0's.
 */
#define RTL819X_TC1_IRQ		25

#define RTL819X_TC0DATA		0x00		/* REG-05, D Table 20 */
#define RTL819X_TC1DATA		0x04		/* REG-06, D Table 21 */
#define RTL819X_TC0CNT		0x08		/* REG-07, D Table 22 */
#define RTL819X_TC1CNT		0x0c		/* REG-08, D Table 23 */
#define RTL819X_TCCNR		0x10		/* REG-09, D Table 24 */
#define RTL819X_TCIR		0x14		/* REG-10, D Table 25 */
#define RTL819X_CDBR		0x18		/* REG-11, D Table 26 */
/* 0x1c is WDTCNR (REG-12).  Named here so the next reader can see that it is
 * inside this block and that nothing below touches it. */

/* D Table 20/21/22/23: the count lives in bits 31:4 and bits 3:0 are
 * reserved.  Confirmed on this die: TC0DATA reads 0x0022E0A0 = 142,858 << 4
 * (SPEC.md REG-05). */
#define RTL819X_TC_VALUE_SHIFT	4

/* D Table 24, Timer/Counter Control Register.  Mode is 0 = counter (times
 * out once) and 1 = timer (reloads).  TCCNR reads 0xC0000000 on this unit,
 * i.e. TC0 enabled in timer mode and TC1 off (SPEC.md REG-09). */
#define RTL819X_TCCNR_TC0EN	(1u << 31)
#define RTL819X_TCCNR_TC0MODE	(1u << 30)
#define RTL819X_TCCNR_TC1EN	(1u << 29)
#define RTL819X_TCCNR_TC1MODE	(1u << 28)
#define RTL819X_TCCNR_TC0_BITS	(RTL819X_TCCNR_TC0EN | RTL819X_TCCNR_TC0MODE)
#define RTL819X_TCCNR_TC1_BITS	(RTL819X_TCCNR_TC1EN | RTL819X_TCCNR_TC1MODE)

/* D Table 25, Timer/Counter Interrupt Register.  The two IP bits are
 * write-1-to-clear; writing 0 to one is documented to leave it alone, which
 * is what lets TC1IP be cleared without touching TC0's pending tick.  TCIR
 * reads 0x80000000 on this unit -- TC0IE set, everything else clear
 * (SPEC.md REG-10). */
#define RTL819X_TCIR_TC0IE	(1u << 31)
#define RTL819X_TCIR_TC1IE	(1u << 30)
#define RTL819X_TCIR_TC0IP	(1u << 29)
#define RTL819X_TCIR_TC1IP	(1u << 28)
#define RTL819X_TCIR_IE_BITS	(RTL819X_TCIR_TC0IE | RTL819X_TCIR_TC1IE)

/* ------------------------------------------------------------------------
 * Parameters, each with the reason it is this number.
 * ------------------------------------------------------------------------ */

/*
 * The rate TC0CNT and TC1CNT increment at.  SPEC.md CLK-17, 量: derived from
 * two measured quantities and nothing else -- CLK-04's 100.0018 Hz tick and
 * REG-05's TC0DATA = 142,858.  It needs no divisor semantics and no 200 MHz
 * figure.
 *
 * THAT IT IS ALSO TC1's RATE IS 讀, NOT 量.  D 8.2 says one Clock Division
 * Base Register "defines the base clock for counting" for the block, so both
 * timers and the watchdog divide the same clock.  REFUTED BY: a measured TC1
 * rate outside CLK-17 +- 50 ppm on the silicon, which would be a finding
 * about the SoC rather than about this driver.  R5-2 is that measurement.
 */
#define RTL819X_TC_HZ		14286057

/*
 * 🔴 AND IT IS THE LOADER'S RATE, NOT LINUX'S.  量 seating 11 (TM-1), the
 * first reading of this block under a kernel: CDBR is 0x03E80000 -- divisor
 * 1000 -- where the loader left 0x000E0000, divisor 14; and TC0DATA is
 * 0x00007D00 (reload 2,000) where the loader left 0x0022E0A0 (142,858).
 * arch/rlx/bsp/timer.c is what rewrites both (讀 2026-09-04, R5-10).  So the
 * constant above is 71.43x the rate this driver actually counts at under
 * Linux, and version 1.0 printed it as `hz_assumed` for a whole seating.
 *
 * It is KEPT, as the fallback and as the thing the derivation is checked
 * against, because a derivation with nothing to disagree with is not checked.
 *
 * THE TWO DERIVATIONS, AND WHY BOTH.
 *
 *   hz_tick = (TC0DATA >> 4) * HZ
 *       Needs no clock constant at all: it says "one jiffy is this many
 *       counts", which is exactly what R5-2 measured with residual EXACTLY
 *       ZERO over three intervals, the longest 140,693,532 counts across a
 *       2^27 wrap (SPEC.md REG-05, notes/timer-driver.md 8.2).  This is the
 *       one the clocksource uses.
 *
 *   hz_cdbr = BSP_SYS_CLK_RATE / (CDBR >> 16)
 *       Needs the 200 MHz figure, which is 讀 (arch/rlx/bsp/bspchip.h
 *       BSP_SYS_CLK_RATE) and 量 to 200.0049 MHz +- 7 ppm (SPEC.md CLK-02).
 *
 * They are different quantities that must agree: the first descends from the
 * kernel's own tick, the second from the crystal.  On this part both give
 * 200,000 (量 TM-1: 2000 * 100, and 200000000 / 1000), and hz_agree in /proc
 * is that comparison made by the driver rather than by a reader.  A
 * disagreement is a finding about the SoC's dividers, not about this file.
 */
#define RTL819X_SYS_CLK_HZ	200000000

/* The two derivations may differ by rounding only.  1 part in 4096 is far
 * looser than anything here needs and far tighter than a wrong divisor. */
#define RTL819X_HZ_TOL_SHIFT	12

/*
 * The TC1 period, in counts.  A power of two so that the clocksource core's
 * `(now - cycle_last) & mask` is exact -- which is the whole reason this
 * driver programs a timer instead of reading TC0's 142,858-count wrap.
 *
 * 2^27 is the largest power of two the 28-bit TC1Data[27:0] field can hold.
 * At CLK-17 that is 9.395 s, so a reader sampling faster than every ~9 s can
 * extend the counter without aliasing; the /proc file below reports the
 * largest gap it has seen so that the reader can check that rather than
 * assume it.
 *
 * D Table 20/21 does not say whether the hardware period is TC1Data counts
 * or TC1Data + 1, and this driver does not need to know: the two differ by
 * one count in 134,217,728, i.e. 0.0075 ppm, four orders of magnitude below
 * the +-50 ppm this gate's D4 asks for.  If the period is 2^27 + 1 the value
 * 2^27 appears once per wrap and masks to 0, which costs one count per wrap
 * and never runs the counter backwards.
 */
#define RTL819X_TC1_PERIOD	(1u << 27)
#define RTL819X_TC1_MASK_BITS	27
#define RTL819X_TC1_MASK	(RTL819X_TC1_PERIOD - 1u)

/*
 * 🆕 R5-3a: the period is settable, while disarmed, by `period <bits>`.
 *
 * It is not a convenience.  docs/interrupt-map.md 3.3 cell I2 has to wait at
 * least one TC1 period to see whether TC1IP latches, and at the Linux rate
 * one 2^27 period is 671.07 s (SPEC.md CLK-22).  Two cells at that length is
 * most of a seating, and a seating is this project's most expensive unit.
 * At 2^20 the same wait is 5.24 s.
 *
 * The floor is 8 and not 2: rtl819x_tc1_arm()'s own positive control waits
 * 100 us -- about 20 counts at 200 kHz -- and a period shorter than a few
 * hundred counts would make that control's "did it move" reading ambiguous
 * with a wrap.  The ceiling is the 28-bit TC1Data[27:0] field.
 */
#define RTL819X_TC1_BITS_MIN	8
#define RTL819X_TC1_BITS_MAX	27

/*
 * The shift search.  2.6.30 has NO clocks_calc_mult_shift() -- 讀
 * include/linux/clocksource.h, which carries clocksource_hz2mult() and
 * nothing else -- so this driver does the search itself.
 *
 * 🔴 It cannot be a constant once the rate is derived, and the failure is
 * SILENT.  clocksource_hz2mult returns u32 by a cast, so an oversized value
 * is truncated with no diagnostic.  量 at the desk, 2026-09-04:
 *
 *   hz = 14,286,057, shift 24 -> mult 1,174,376,947            fits
 *   hz =    200,000, shift 24 -> mult 83,886,080,000 -> u32 2,281,701,376
 *
 * The truncated value implies 136.000000 ns per count where the true figure
 * is 5,000 -- a factor of 36.76, wrong in the direction that makes time run
 * fast.  At 200,000 Hz the largest shift meeting both bounds is 19, where the
 * mult is 2,621,440,000 EXACTLY (1e9/200000 = 5000 is an integer, so the
 * search's rounding term contributes nothing at all).
 *
 * TWO bounds, and the second is the one that is easy to forget:
 *   * mult must fit u32, or clocksource_hz2mult truncates it;
 *   * mask * mult must fit s63, because 讀 cyc2ns() is
 *     `((u64)cycles * cs->mult) >> cs->shift` returned as s64.
 * With mask = 2^27-1 and mult <= 2^32-1 the product is at most 2^59, so the
 * second bound cannot bite at this mask -- it is computed anyway, because the
 * mask is settable now and a bound that is only true for one configuration is
 * not a bound.
 *
 * MULT_FLOOR is the other direction: a shift so low that mult is small makes
 * the ns conversion coarse.  2^20 bounds the rounding error at about 1 ppm,
 * four orders below this gate's +-50 ppm.
 */
#define RTL819X_SHIFT_MAX	31
#define RTL819X_MULT_FLOOR	(1u << 20)

/*
 * mult/shift.  clocksource_hz2mult(14286057, shift) fits in u32 up to
 * shift = 25; 26 overflows.  24 is used because NTP adjusts mult at run time
 * by up to about 11 % and shift 24 leaves the most headroom among the shifts
 * whose own rounding error -- 1 part in 2^24 of 69.998 ns, i.e. 0.00085 ppm
 * -- is already four orders of magnitude below the tolerance that matters.
 * At shift 24 the value is 1,174,376,947.
 *
 * Overflow of the core's `cyc * mult`: the largest cycle count is the mask,
 * 2^27 - 1, and (2^27-1) * 1.18e9 = 1.6e17, well inside s64.
 */
#define RTL819X_TC1_SHIFT	24

/* See the header comment.  Deliberately below clocksource_jiffies' 1. */
#define RTL819X_TC1_RATING	0

/*
 * 🆕 R5-3b.  The clockevent's ratings.
 *
 * 讀 arch/rlx/kernel/rlx-cevt.c:234, `cd->rating = 100`, and 讀
 * kernel/time/tick-common.c tick_check_new_device(): the incumbent keeps the
 * tick unless `curdev->rating >= newdev->rating` is false.  So 100 is the
 * number to beat and it must be beaten strictly.
 *
 * 300 rather than 101.  include/linux/clocksource.h documents the band its
 * own ratings live in -- 1 jiffies, 100 "base level", 200 "good", 300
 * "desired", 400 "perfect" -- and include/linux/clockchips.h documents none
 * for clockevents, so the clocksource band is the only convention there is.
 * A hardware timer that reloads from a register the vendor's own tick was
 * derived from is "desired": it is not a placeholder, and it is not better
 * than the hardware allows.  The value is settable at run time by `rating`
 * so that one seating can take both sides of the inequality.
 *
 * 99 for the probe, not 100.  A tie at 100 would already be declined by the
 * `>=` above, but a tie is decided by an operator inequality and 99 is
 * decided by arithmetic.  The probe exists to be a NEGATIVE CONTROL, and a
 * control that depends on reading one comparison operator correctly is the
 * kind this project has already been burned by.
 */
#define RTL819X_CE_RATING_VENDOR	100
#define RTL819X_CE_RATING_DFLT	300
#define RTL819X_CE_RATING_PROBE	99
#define RTL819X_CE_RATING_MIN	1
#define RTL819X_CE_RATING_MAX	1000

/*
 * The pre-check `cevt` refuses without.
 *
 * MIN_J is 300 jiffies = 3 s at CONFIG_HZ=100, which is long enough that the
 * ratio is not dominated by the +-1 jiffy quantisation of its own endpoints:
 * one jiffy in 300 is 3,333 ppm and the tolerance below is 10,000.
 *
 * TOL_PERMILLE is 10, i.e. 1 %.  量 seating 12 (SPEC.md IRQ-08): the measured
 * delivery rate was within 0.0199 % and 0.0994 % of the programmed rate at
 * two periods 16x apart, and 0.0206 % with the NIC up and four pings in
 * flight.  1 % is a hundred times the worst of those, so this refuses on a
 * fault and not on jitter -- which is what a gate before an irreversible step
 * has to do to be worth passing.
 */
#define RTL819X_CE_MIN_J	300
#define RTL819X_CE_TOL_PERMILLE	10

/*
 * 🆕 `cereload <counts>` -- the bounds on a DELIBERATELY WRONG tick period.
 *
 * WHY THE VERB EXISTS.  My clockevent runs at HZ and so does the vendor's, so
 * "line 25 advanced 1:1 with jiffies" and "line 13 advanced 1:1 with jiffies"
 * are the same sentence and neither says whose interrupt is the tick.  The
 * pointer in ce_handler answers it from the build, and ce_mode answers it from
 * the core -- both are readings of kernel state.  This verb answers it from
 * the OUTSIDE: double the period and the board's own clock runs at half the
 * host's, which is a causal demonstration rather than a correlation, and the
 * host's capture timestamps are a reference this driver cannot influence.
 *
 * 500 counts is 400 Hz -- four interrupts per intended tick, and the ISR is a
 * few register accesses.  20,000 is 10 Hz: coarse, but every timeout in the
 * kernel is expressed in jiffies and simply runs slow.  Zero is excluded
 * because a reload of 0 is not a slow clock, it is an undefined one.
 *
 * 🔴 It may only be used while ARMED and in clockevent mode, and `cevt`
 * REFUSES while the live reload differs from the one HZ implies.  So the
 * sequence is fixed by the code: hand the tick over at the right rate, then
 * make it wrong on purpose, then put it back.  A card cannot reorder that.
 */
#define RTL819X_CE_RELOAD_MIN	500
#define RTL819X_CE_RELOAD_MAX	20000

#define RTL819X_MODE_CS		0	/* clocksource: power-of-two period */
#define RTL819X_MODE_CE		1	/* clockevent:  hz_used / HZ period */

#define RTL819X_PROC_NAME	"rtl819x-timer"
#define RTL819X_TC_VERSION	"3.0"

/* ------------------------------------------------------------------------
 * State
 * ------------------------------------------------------------------------ */

static DEFINE_SPINLOCK(rtl819x_tc_lock);

/* Read once at init, before anything of ours has written a register.  These
 * are what the /proc file compares against, so that "we did not disturb TC0"
 * is a comparison and not a claim. */
static u32 rtl819x_tccnr_at_init;
static u32 rtl819x_tcir_at_init;
static u32 rtl819x_cdbr_at_init;
static u32 rtl819x_gimr_at_init;
static u32 rtl819x_tc0data_at_init;

static int rtl819x_tc1_armed;
static int rtl819x_last_verdict;	/* 0, or the -errno of the last refusal */
static u32 rtl819x_tccnr_after_arm;
static u32 rtl819x_tc1_delta_at_arm;	/* the counter's own movement proof */

/* The software extension of the counter.  🔄 R5-3a: advanced by a KERNEL
 * TIMER, not by whoever happens to read /proc.
 *
 * 量 TM-5c, seating 11: 462 s with nobody reading, and tc1_ext sat 92,362,366
 * counts behind tc1_cycles while tc1_ext_trusted still read 1 -- because
 * rtl819x_ext_advance()'s only caller was inside the /proc read.  "The sum of
 * the intervals somebody looked at" is not an extension of a counter. */
static u64 rtl819x_ext_cycles;
static u32 rtl819x_ext_last;
static u32 rtl819x_ext_gap_max;		/* counts -- ALIASES, kept on purpose */
static u32 rtl819x_ext_reads;
static u64 rtl819x_ext_last_j;		/* jiffies at the last advance */
static u64 rtl819x_ext_gap_max_j;	/* jiffies -- CANNOT alias */
static u32 rtl819x_ext_ticks;		/* advances driven by the timer */
static struct timer_list rtl819x_ext_timer;
static unsigned long rtl819x_ext_interval_j;

/* Derived at init from the block's own registers.  See RTL819X_TC_HZ. */
static u32 rtl819x_hz_tick;		/* (TC0DATA >> 4) * HZ */
static u32 rtl819x_hz_cdbr;		/* SYS_CLK / (CDBR >> 16) */
static u32 rtl819x_hz_used;		/* what the clocksource was built on */
static int rtl819x_hz_agree;		/* the two derivations agree */
static u32 rtl819x_shift_used;
static u32 rtl819x_ce_shift;
static u64 rtl819x_period_j;		/* one TC1 period, in jiffies */

/* The period, settable while disarmed. */
static unsigned int rtl819x_period_bits = RTL819X_TC1_MASK_BITS;

/* The interrupt path.  Every one of these is in /proc, because a state
 * machine whose state is not readable at the bench is a state machine that
 * gets driven by memory. */
static int rtl819x_tc1ie_set;		/* WE set TCIR bit 30 */
static int rtl819x_ack_proven;		/* WE watched TC1IP go 1 -> 0 */
static int rtl819x_ackip_before;
static int rtl819x_ackip_after;
static int rtl819x_irq_requested;
static u32 rtl819x_irq_count;
static u32 rtl819x_irq_spurious;
static u32 rtl819x_irq_stuck;		/* the storm guard fired */
static u32 rtl819x_irq_last_tcir;

/* request_irq's cookie.  Its ADDRESS is the identity; the value is never
 * read, and it exists so free_irq has something to match. */
static int rtl819x_irq_cookie;
static u32 rtl819x_irq_preacked;	/* TC1IP already 0 on ISR entry (IRQ-09) */

/* 🆕 R5-3b.  The clockevent. */
static int rtl819x_mode = RTL819X_MODE_CS;
static u32 rtl819x_ce_reload;		/* counts per tick, LIVE */
static u32 rtl819x_ce_reload_hz;	/* counts per tick that HZ implies */
static u32 rtl819x_ce_reload_writes;	/* how many times `cereload` wrote it */
static int rtl819x_ce_reload_exact;	/* hz_used % HZ == 0 */
static int rtl819x_ce_registered;	/* the real device is on the list */
static int rtl819x_ce_probe_registered;
static int rtl819x_ce_live;		/* set_mode(PERIODIC) has run on it */
static u32 rtl819x_ce_mode_calls;
static u32 rtl819x_ce_probe_mode_calls;
static int rtl819x_ce_last_mode = -1;
static int rtl819x_ce_probe_last_mode = -1;
static u32 rtl819x_ce_next_calls;	/* set_next_event -- must stay 0 */
static u32 rtl819x_ce_badmode;		/* set_mode(ONESHOT) -- must stay 0 */
static u32 rtl819x_ce_hw_bad;		/* set_mode(PERIODIC) had to write */
static u64 rtl819x_ce_cycles;		/* reload per delivered interrupt */
static u32 rtl819x_ce_base_irq;		/* irq_count at reqirq */
static u64 rtl819x_ce_base_j;		/* jiffies  at reqirq */
static u32 rtl819x_ce_check_dc;		/* the pre-check's two numbers, kept */
static u32 rtl819x_ce_check_dj;

/* ------------------------------------------------------------------------
 * Register access.
 *
 * __raw_readl/__raw_writel and not readl/writel: readl is defined to convert
 * a little-endian device word to CPU order, and on this big-endian part an
 * on-chip register is already in CPU order.  CONFIG_SWAP_IO_SPACE is not set
 * in this build so the two happen to be identical here, but the raw form is
 * the one that stays correct if it ever is.
 *
 * The address is formed with CKSEG1ADDR, so it is uncached and unmapped and
 * needs no ioremap -- which also means these work from any initcall level.
 * ------------------------------------------------------------------------ */

static inline void __iomem *rtl819x_tc_reg(unsigned int off)
{
	return (void __iomem *)(CKSEG1ADDR(RTL819X_TC_PHYS) + off);
}

static inline u32 rtl819x_tc_rd(unsigned int off)
{
	return __raw_readl(rtl819x_tc_reg(off));
}

static inline void rtl819x_tc_wr(unsigned int off, u32 v)
{
	__raw_writel(v, rtl819x_tc_reg(off));
}

static inline u32 rtl819x_intc_rd(unsigned int off)
{
	return __raw_readl((void __iomem *)(CKSEG1ADDR(RTL819X_INTC_PHYS) + off));
}

/* The live mask.  It is derived from rtl819x_period_bits and not from the
 * RTL819X_TC1_MASK constant, because `period` makes the period settable while
 * disarmed -- and a mask that did not follow it would let the wrap arithmetic
 * be exact for a period the hardware is no longer using, which is the one
 * failure a power-of-two period exists to prevent. */
static inline u32 rtl819x_tc1_mask(void)
{
	return (1u << rtl819x_period_bits) - 1u;
}

static inline u32 rtl819x_tc1_raw(void)
{
	return rtl819x_tc_rd(RTL819X_TC1CNT) >> RTL819X_TC_VALUE_SHIFT;
}

/*
 * 🔄 R5-3b: the mask is applied in clocksource mode ONLY.
 *
 * In clockevent mode the hardware period is hz_used / HZ = 2,000 counts and
 * rtl819x_tc1_mask() describes a power of two that the counter is no longer
 * using -- masking with it would fold a position of 2,000 down to 2,000 &
 * 0x7FF = 1,952 and invent motion that did not happen.  The raw value is
 * already inside [0, reload) so nothing needs folding.
 */
static inline u32 rtl819x_tc1_cycles(void)
{
	u32 v = rtl819x_tc1_raw();

	return (rtl819x_mode == RTL819X_MODE_CE) ? v : (v & rtl819x_tc1_mask());
}

/* One TC1 period in counts, whichever mode is selected. */
static inline u32 rtl819x_tc1_reload(void)
{
	return (rtl819x_mode == RTL819X_MODE_CE)
		? rtl819x_ce_reload : (rtl819x_tc1_mask() + 1u);
}

/*
 * One period in jiffies, and the quarter of it the extension timer runs at.
 *
 * 🆕 R5-3b.  ONE owner, because two had already disagreed: version 2.0
 * computed this inside arm() alone, so `period 8` on a disarmed driver moved
 * mask_bits and left period_jiffies describing the previous period -- 量
 * seating 12 EX-1, mask_bits = 8 beside period_jiffies = 524
 * (notes/timer-driver.md 11.6 6).  It changed no behaviour, because arm()
 * recomputes; what it changed was what /proc SAYS, and a dump that describes a
 * configuration the driver is not in is the same defect class as a spec table
 * that lags its finding.
 *
 * Caller holds rtl819x_tc_lock.
 */
static void rtl819x_derive_period(void)
{
	rtl819x_period_j = (u64)rtl819x_tc1_reload() * HZ;
	do_div(rtl819x_period_j, rtl819x_hz_used ? rtl819x_hz_used : 1);
	/* At least 1 jiffy, so a very short period cannot ask for a zero-delay
	 * timer that re-arms itself forever. */
	rtl819x_ext_interval_j = (unsigned long)(rtl819x_period_j >> 2);
	if (rtl819x_ext_interval_j < 1)
		rtl819x_ext_interval_j = 1;
}

/* ------------------------------------------------------------------------
 * The clocksource
 * ------------------------------------------------------------------------ */

static cycle_t rtl819x_tc1_read(struct clocksource *cs)
{
	return (cycle_t)rtl819x_tc1_cycles();
}

static struct clocksource rtl819x_tc1_clocksource = {
	.name	= "rtl819x-tc1",
	.rating	= RTL819X_TC1_RATING,
	.read	= rtl819x_tc1_read,
	.mask	= CLOCKSOURCE_MASK(RTL819X_TC1_MASK_BITS),
	.shift	= RTL819X_TC1_SHIFT,
	.flags	= CLOCK_SOURCE_IS_CONTINUOUS,
};

/* Advance the software extension.  Caller holds rtl819x_tc_lock.
 *
 * 🔴 TWO gap figures, and keeping both is the point.  `d` is already reduced
 * mod the period, so an interval of one full period plus delta is
 * indistinguishable from delta -- 量 TM-5b2: a real gap of 140,693,532 counts
 * reported as 6,475,672, which is exactly that value mod 2^27, with
 * tc1_ext_trusted still reading 1.  `dj` is in jiffies, which this driver
 * never reduces, so it cannot alias.
 *
 * The old figure is NOT removed.  Printing both is what makes the defect
 * legible to a later reader instead of merely absent: the pair
 * (gap_max = 6,475,672, gap_max_j = 70,346) says "a whole period was lost"
 * on its face, and either number alone does not.
 */
static void rtl819x_ext_advance(u32 now)
{
	u32 d = (now - rtl819x_ext_last) & rtl819x_tc1_mask();
	u64 j = get_jiffies_64();
	u64 dj = j - rtl819x_ext_last_j;

	rtl819x_ext_cycles += d;
	if (d > rtl819x_ext_gap_max)
		rtl819x_ext_gap_max = d;
	if (dj > rtl819x_ext_gap_max_j)
		rtl819x_ext_gap_max_j = dj;
	rtl819x_ext_last = now;
	rtl819x_ext_last_j = j;
	rtl819x_ext_reads++;
}

/*
 * The kernel timer that drives it.  One quarter of a period, so three
 * consecutive misses are needed before the extension can alias -- and the
 * jiffies gap above would report even that.
 *
 * ⚠️ This timer is driven by the vendor's TC0 tick, so it shares TC0's fate:
 * if the system tick dies, so does the extension AND so does `jiffies`, and
 * a stopped `jiffies` makes dj read 0, which looks trustworthy.  That is a
 * real blind spot and it is bounded: a board whose tick has stopped is not
 * running, and tc1_cycles is read directly from the hardware on every /proc
 * read, so the comparison tc1_cycles-vs-tc1_ext still exposes it.
 */
static void rtl819x_ext_tick(unsigned long data)
{
	unsigned long flags;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_tc1_armed) {
		rtl819x_ext_advance(rtl819x_tc1_cycles());
		rtl819x_ext_ticks++;
		mod_timer(&rtl819x_ext_timer, jiffies + rtl819x_ext_interval_j);
	}
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
}

/* ------------------------------------------------------------------------
 * arm / disarm
 * ------------------------------------------------------------------------ */

/*
 * Refusals, and each one is a state this driver must not write into:
 *
 *   -EBUSY   TC1 is already enabled -- by us, or by something else.  D Table
 *            24/25 both carry a note about "Mitigation&Timer1", so the SoC
 *            has a use for TC1 that is not this driver's, and stomping it is
 *            not a risk worth taking to get a clocksource.
 *   -ENODEV  TC0En is clear, i.e. the system tick is not running from this
 *            block.  Then the model this driver is built on does not hold and
 *            it should say so rather than program a timer beside it.
 *   -EPERM   GIMR bit 9 (TC1_IE) is SET, so TC1's pending flag can reach the
 *            CPU.  Nothing in this kernel is this driver's interrupt handler,
 *            and TCIR's TC1IE is not the only gate -- refusing here is the
 *            measurement that says something under Linux unmasked it, which
 *            is a finding about the vendor's setup and not about this file.
 *   -EIO     the read-back says our write disturbed TC0's bits.  The saved
 *            value is put back immediately and the driver stays disarmed.
 *   -ETIME   TC1CNT did not move after being enabled.  A clocksource that
 *            returns a constant makes time stop the moment anything selects
 *            it; refusing to register is the only safe answer.  This is the
 *            positive control CLAUDE.md asks for -- the driver may not report
 *            success without having seen the counter advance.
 */
static int rtl819x_tc1_arm(void)
{
	unsigned long flags;
	u32 cnr, back, before, after;
	int ret = 0;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);

	cnr = rtl819x_tc_rd(RTL819X_TCCNR);
	if (rtl819x_tc1_armed || (cnr & RTL819X_TCCNR_TC1EN)) {
		ret = -EBUSY;
		goto out;
	}
	if (!(cnr & RTL819X_TCCNR_TC0EN)) {
		ret = -ENODEV;
		goto out;
	}
	/* 🆕 R5-3b.  -ERANGE: clockevent mode was asked for on a kernel whose
	 * tick rate does not divide the counter's rate, so no integer reload
	 * gives HZ exactly.  量 on this build it does -- 200,000 / 100 = 2,000
	 * -- and the refusal exists so that a config change makes the driver
	 * say so instead of running the system clock at the wrong rate. */
	if (rtl819x_mode == RTL819X_MODE_CE && !rtl819x_ce_reload_exact) {
		ret = -ERANGE;
		goto out;
	}
	/* 🔄 R5-3a: the refusal now asks WHOSE bit it is.  Version 1.0 read a
	 * set GIMR bit 9 as "something under Linux unmasked it", which was the
	 * only possibility then.  After `reqirq` it is normally OURS -- and a
	 * driver that refused to re-arm because of a mask its own request_irq()
	 * asked the irqchip to set would be reporting its own footprint as a
	 * finding.  Somebody ELSE's bit 9 is still -EPERM. */
	if ((rtl819x_intc_rd(RTL819X_GIMR) & RTL819X_INTC_TC1)
	    && !rtl819x_irq_requested) {
		ret = -EPERM;
		goto out;
	}

	/* The two writes, in this order: the period has to be in place before
	 * the counter is allowed to run, or the first pass is against
	 * whatever TC1DATA held. */
	rtl819x_tc_wr(RTL819X_TC1DATA,
		      rtl819x_tc1_reload() << RTL819X_TC_VALUE_SHIFT);
	rtl819x_tc_wr(RTL819X_TCCNR, cnr | RTL819X_TCCNR_TC1_BITS);

	back = rtl819x_tc_rd(RTL819X_TCCNR);
	rtl819x_tccnr_after_arm = back;
	if ((back & RTL819X_TCCNR_TC0_BITS) != (cnr & RTL819X_TCCNR_TC0_BITS)) {
		rtl819x_tc_wr(RTL819X_TCCNR, cnr);
		ret = -EIO;
		goto out;
	}

	/* Did it actually start?  100 us is about 1,429 counts at CLK-17, so
	 * a moving counter cannot read equal and a stopped one cannot read
	 * different. */
	before = rtl819x_tc1_cycles();
	udelay(100);
	after = rtl819x_tc1_cycles();
	/* 🔄 R5-3b: `& mask` is wrong in clockevent mode for the reason given at
	 * rtl819x_tc1_cycles().  100 us is about 20 counts at 200 kHz against a
	 * 2,000-count period, so a wrap inside the window would need the counter
	 * to run 100x fast; the branch is written for correctness, not because
	 * it is expected to be taken. */
	if (rtl819x_mode == RTL819X_MODE_CE)
		rtl819x_tc1_delta_at_arm = (after >= before)
			? (after - before)
			: (after + rtl819x_ce_reload - before);
	else
		rtl819x_tc1_delta_at_arm = (after - before) & rtl819x_tc1_mask();
	if (rtl819x_tc1_delta_at_arm == 0) {
		rtl819x_tc_wr(RTL819X_TCCNR, cnr);
		ret = -ETIME;
		goto out;
	}

	rtl819x_ext_cycles = 0;
	rtl819x_ext_last = after;
	rtl819x_ext_gap_max = 0;
	rtl819x_ext_reads = 0;
	rtl819x_ext_last_j = get_jiffies_64();
	rtl819x_ext_gap_max_j = 0;
	rtl819x_ext_ticks = 0;
	rtl819x_ce_cycles = 0;
	rtl819x_tc1_armed = 1;

	/* The mask has to match the period that was just loaded, and it is read
	 * by clocksource_register() below. */
	rtl819x_tc1_clocksource.mask = CLOCKSOURCE_MASK(rtl819x_period_bits);

	/* 🆕 R5-3b.  In clockevent mode there is no software extension and no
	 * kernel timer driving one: rtl819x_ext_advance()'s arithmetic is the
	 * masked kind, the period is not a power of two, and the ISR runs once
	 * per period anyway -- so ce_cycles is exact where an extension would be
	 * approximate.  Every tc1_ext_* line in /proc therefore reads 0 in this
	 * mode, and `mode=ce` on the line above it is why. */
	/* 🔄 R5-3b: both derived quantities come from one function, and it is
	 * called here for BOTH modes -- a mode that jumped over it would print
	 * period_jiffies=0, a zero that reads as a measurement of a 0-jiffy
	 * period rather than as an unset variable.  In clockevent mode the value
	 * is 2,000 x 100 / 200,000 = 1, which is the whole point of that mode.
	 * The extension TIMER is what the CE branch skips, and it skips it
	 * after this. */
	rtl819x_derive_period();

	if (rtl819x_mode == RTL819X_MODE_CE)
		goto armed;

	mod_timer(&rtl819x_ext_timer, jiffies + rtl819x_ext_interval_j);

armed:
out:
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* Registration is outside the lock: clocksource_register() takes
	 * clocksource_lock with interrupts disabled and there is no reason to
	 * hold two. */
	if (ret == 0 && rtl819x_mode == RTL819X_MODE_CE) {
		/* Nothing to register: the clocksource's mask arithmetic is not
		 * valid for this period.  See THE CLOCKEVENT in the header. */
		return 0;
	}
	if (ret == 0) {
		ret = clocksource_register(&rtl819x_tc1_clocksource);
		if (ret) {
			/* 🔴 R5-3a, found at the desk and not on the device:
			 * version 1.0 cleared `armed` here and left TC1
			 * COUNTING.  The hardware stayed enabled, `disarm`
			 * then returned -EINVAL because `armed` was 0, and
			 * nothing in the driver could stop it -- an
			 * unreachable state created by the one path that is
			 * supposed to be the safe failure.  It has never been
			 * reached (clocksource_register returned 0 on the
			 * silicon, 量 seating 11), which is why a reading
			 * would not have found it. */
			spin_lock_irqsave(&rtl819x_tc_lock, flags);
			rtl819x_tc1_armed = 0;
			rtl819x_tc_wr(RTL819X_TCCNR,
				      rtl819x_tc_rd(RTL819X_TCCNR)
				      & ~RTL819X_TCCNR_TC1_BITS);
			rtl819x_last_verdict = ret;
			spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
			del_timer_sync(&rtl819x_ext_timer);
		}
	}
	return ret;
}

/* ------------------------------------------------------------------------
 * The interrupt path.  R5-3a; docs/interrupt-map.md 3.3 cells I2-I4.
 * ------------------------------------------------------------------------ */

/*
 * Set or clear TCIR bit 30, preserving TC0's enable and writing ZERO into
 * both IP positions.
 *
 * 🔴 The zeros are the load-bearing part.  Both IP bits are write-1-to-clear
 * (D Table 25), so a read-modify-write that carried a set IP back would clear
 * it -- and if that IP were TC0's, this driver would have eaten the vendor
 * tick's pending flag on its way to setting an unrelated enable.  Masking
 * with IE_BITS is what makes the write touch enables only.
 */
static void rtl819x_tc1ie_write(int on)
{
	u32 ir = rtl819x_tc_rd(RTL819X_TCIR) & RTL819X_TCIR_IE_BITS;

	if (on)
		ir |= RTL819X_TCIR_TC1IE;
	else
		ir &= ~RTL819X_TCIR_TC1IE;
	rtl819x_tc_wr(RTL819X_TCIR, ir);
}

/* I2.  Arm the timer block's own interrupt enable, and nothing else. */
static int rtl819x_tc1_armirq(void)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!rtl819x_tc1_armed)
		ret = -EINVAL;			/* nothing to raise a flag */
	else if (rtl819x_tc1ie_set)
		ret = -EBUSY;
	else if (rtl819x_tc_rd(RTL819X_TCIR) & RTL819X_TCIR_TC1IE)
		ret = -EBUSY;			/* somebody else's enable */
	else {
		rtl819x_tc1ie_write(1);
		rtl819x_tc1ie_set = 1;
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

static int rtl819x_tc1_disarmirq(void)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!rtl819x_tc1ie_set)
		ret = -EINVAL;
	else {
		rtl819x_tc1ie_write(0);
		rtl819x_tc1ie_set = 0;
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

/*
 * I3.  Write 1 to TCIR bit 28 and read it back.
 *
 * This is this project's ONLY test of D Table 25's write-1-to-clear claim,
 * which stands on that one leaked-draft table.  It became testable again only
 * because 3.2 corrected TMR-2's attribution: version 1.0 never set TC1IE, so
 * the bit never latched, and a bit that has never been 1 cannot be shown to
 * clear.  `ack_proven` is set ONLY on a 1 -> 0 transition this function
 * watched itself -- not on a 0 -> 0, which proves nothing and is what a
 * casual implementation would record.
 */
static int rtl819x_tc1_ackip(void)
{
	unsigned long flags;
	u32 before, after;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	before = rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_tc_wr(RTL819X_TCIR,
		      (before & RTL819X_TCIR_IE_BITS) | RTL819X_TCIR_TC1IP);
	after = rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_ackip_before = (before & RTL819X_TCIR_TC1IP) ? 1 : 0;
	rtl819x_ackip_after  = (after  & RTL819X_TCIR_TC1IP) ? 1 : 0;
	if (rtl819x_ackip_before && !rtl819x_ackip_after)
		rtl819x_ack_proven = 1;
	rtl819x_last_verdict = 0;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return 0;
}

/* ------------------------------------------------------------------------
 * The clockevent.  R5-3b; see THE CLOCKEVENT in the header comment.
 * ------------------------------------------------------------------------ */

static void rtl819x_ce_set_mode(enum clock_event_mode mode,
				struct clock_event_device *evt);
static int rtl819x_ce_set_next(unsigned long delta,
			       struct clock_event_device *evt);

/*
 * The real device.  `.rating` is the only field a verb may change and it may
 * change it only before registration; `.cpumask`, `.mult` and `.shift` are
 * filled in at init because cpumask_of() is not a constant expression and the
 * rate is derived rather than compiled in.
 *
 * `.event_handler = clockevents_handle_noop` is not a placeholder.  The ISR
 * calls this field unconditionally once ce_live is set, and there is a real
 * window -- inside clockevents_exchange_device(), between
 * clockevents_shutdown(new) and tick_setup_periodic(new) -- in which the core
 * has not yet installed tick_handle_periodic.  The noop is what makes that
 * window harmless instead of a NULL call.
 */
static struct clock_event_device rtl819x_tc1_cevt = {
	.name		= "rtl819x-tc1",
	.features	= CLOCK_EVT_FEAT_PERIODIC,
	.rating		= RTL819X_CE_RATING_DFLT,
	.irq		= RTL819X_TC1_IRQ,
	.set_mode	= rtl819x_ce_set_mode,
	.set_next_event	= rtl819x_ce_set_next,
	.event_handler	= clockevents_handle_noop,
	.mode		= CLOCK_EVT_MODE_UNUSED,
};

/*
 * The negative control.  Identical except for a rating of 99, which
 * tick_check_new_device()'s `curdev->rating >= newdev->rating` is REQUIRED to
 * decline against the vendor's 100.  It shares set_mode with the real device
 * on purpose: if the core ever did take it, the outcome is a running tick and
 * a raised ce_probe_mode_calls, not a dead board.
 */
static struct clock_event_device rtl819x_tc1_cevt_probe = {
	.name		= "rtl819x-tc1-probe",
	.features	= CLOCK_EVT_FEAT_PERIODIC,
	.rating		= RTL819X_CE_RATING_PROBE,
	.irq		= RTL819X_TC1_IRQ,
	.set_mode	= rtl819x_ce_set_mode,
	.set_next_event	= rtl819x_ce_set_next,
	.event_handler	= clockevents_handle_noop,
	.mode		= CLOCK_EVT_MODE_UNUSED,
};

/*
 * 🔴 NO LOCK HERE, and that is a reading rather than an oversight.
 *
 * 讀 kernel/time/clockevents.c and tick-common.c: every call reaches this
 * function from clockevents_exchange_device() (inside local_irq_save) or from
 * tick_setup_periodic() (inside tick_check_new_device's
 * spin_lock_irqsave(&tick_device_lock))  -- interrupts are off at both.  量
 * on this build: CONFIG_SMP is not set and CONFIG_PREEMPT is not set, so with
 * interrupts off nothing else on this machine can be executing.  Taking
 * rtl819x_tc_lock would additionally nest this driver's lock inside two of
 * the kernel's, which is an ordering nothing here needs.
 *
 * It writes no register on the expected path.  arm() programmed TC1DATA and
 * TCCNR, and rtl819x_tc1_cevt_register() refused unless a read-back agreed --
 * so PERIODIC verifies and records.  A write here means the hardware moved
 * between those two points, which is ce_hw_bad and a finding.
 */
static void rtl819x_ce_set_mode(enum clock_event_mode mode,
				struct clock_event_device *evt)
{
	int probe = (evt == &rtl819x_tc1_cevt_probe);
	u32 want, cnr;

	if (probe) {
		rtl819x_ce_probe_mode_calls++;
		rtl819x_ce_probe_last_mode = (int)mode;
	} else {
		rtl819x_ce_mode_calls++;
		rtl819x_ce_last_mode = (int)mode;
	}

	switch (mode) {
	case CLOCK_EVT_MODE_PERIODIC:
		want = rtl819x_ce_reload << RTL819X_TC_VALUE_SHIFT;
		cnr = rtl819x_tc_rd(RTL819X_TCCNR);
		if (rtl819x_tc_rd(RTL819X_TC1DATA) != want
		    || !(cnr & RTL819X_TCCNR_TC1EN)) {
			rtl819x_ce_hw_bad++;
			rtl819x_tc_wr(RTL819X_TC1DATA, want);
			rtl819x_tc_wr(RTL819X_TCCNR,
				      cnr | RTL819X_TCCNR_TC1_BITS);
		}
		if (!probe)
			rtl819x_ce_live = 1;
		break;

	case CLOCK_EVT_MODE_ONESHOT:
		/* Unreachable: this device does not advertise the feature and
		 * CONFIG_TICK_ONESHOT is absent from this build.  Counted rather
		 * than handled, because the count is the only thing that could
		 * ever tell a later reader the unreachable happened. */
		rtl819x_ce_badmode++;
		break;

	case CLOCK_EVT_MODE_SHUTDOWN:
	case CLOCK_EVT_MODE_UNUSED:
	case CLOCK_EVT_MODE_RESUME:
	default:
		/* 🔴 SHUTDOWN deliberately does NOT stop TC1.
		 * clockevents_exchange_device() calls it on the way IN, one
		 * statement before tick_setup_periodic() turns the same device
		 * on, so a driver that honoured it would switch its own tick
		 * source off inside the handover.  Nothing in this configuration
		 * ever removes a tick device, and the price of ignoring the
		 * request is an interrupt that arrives and runs a noop. */
		break;
	}
}

/*
 * Unreachable in this configuration, and the return value is chosen for what
 * happens if that is ever wrong.
 *
 * 讀 kernel/time/tick-common.c tick_setup_periodic(): a device WITHOUT
 * CLOCK_EVT_FEAT_PERIODIC is driven by `for (;;) { if
 * (!clockevents_program_event(...)) return; next += tick_period; }` -- with
 * interrupts disabled.  A set_next_event that always fails makes that loop
 * spin forever and the board is gone with no console.  Returning 0 makes it
 * return after one pass.  Both outcomes are wrong; one of them can be read
 * afterwards, because ce_next_calls is in /proc and must be 0.
 *
 * The other two callers -- tick_program_event() and the broadcast path -- are
 * behind CONFIG_TICK_ONESHOT and CONFIG_GENERIC_CLOCKEVENTS_BROADCAST, 量
 * both absent from this build's .config.
 */
static int rtl819x_ce_set_next(unsigned long delta,
			       struct clock_event_device *evt)
{
	rtl819x_ce_next_calls++;
	return 0;
}

/*
 * The pre-check.  Caller holds rtl819x_tc_lock.
 *
 * One interrupt per jiffy is what the tick needs, and in clockevent mode the
 * reload IS hz_used / HZ -- so the expected ratio is exactly 1 and no
 * calibration constant enters.  The two raw numbers are kept in /proc so the
 * ratio can be recomputed off the capture instead of trusted.
 */
static int rtl819x_ce_precheck(void)
{
	u64 dj = get_jiffies_64() - rtl819x_ce_base_j;
	u32 dc = rtl819x_irq_count - rtl819x_ce_base_irq;
	u64 diff;

	rtl819x_ce_check_dc = dc;
	rtl819x_ce_check_dj = (dj > 0xFFFFFFFFULL) ? 0xFFFFFFFFu : (u32)dj;

	if (dj < RTL819X_CE_MIN_J)
		return -ETIME;
	diff = ((u64)dc > dj) ? ((u64)dc - dj) : (dj - (u64)dc);
	if (diff * 1000ULL > dj * (u64)RTL819X_CE_TOL_PERMILLE)
		return -ETIME;
	return 0;
}

/*
 * `cevt` / `cevtprobe`.  The refusals, and each one is a state in which
 * handing the system tick to this driver would be a guess:
 *
 *   -EINVAL  not in clockevent mode, or not armed, or TC1IE is not ours, or
 *            no interrupt has been requested.  Each of those is one of I1..I4
 *            not done, and I1..I4 are what make the delivery a measurement.
 *   -EPERM   ackip has not watched TC1IP go 1 -> 0.  The ISR's ability to
 *            clear its own pending bit is what keeps handle_level_irq's
 *            unmask from re-triggering forever, and after the handover that
 *            loop would take the system clock with it.
 *   -EBUSY   already registered.  🔴 This is the only thing standing between
 *            a second `cevt` and a corrupted list: 量 on this build,
 *            CONFIG_BUG is not set, so clockevents_register_device()'s own
 *            BUG_ON(dev->mode != CLOCK_EVT_MODE_UNUSED) compiles to nothing.
 *   -ENODEV  the hardware does not read back what arm() wrote.  Checked here
 *            so that set_mode(PERIODIC) can be a verification.
 *   -ETIME   the delivery pre-check.  See rtl819x_ce_precheck().
 */
static int rtl819x_tc1_cevt_register(int probe)
{
	unsigned long flags;
	struct clock_event_device *cd;
	u32 want;
	int ret = 0;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_mode != RTL819X_MODE_CE)
		ret = -EINVAL;
	else if (!rtl819x_tc1_armed)
		ret = -EINVAL;
	else if (!rtl819x_tc1ie_set)
		ret = -EINVAL;
	else if (!rtl819x_ack_proven)
		ret = -EPERM;
	else if (!rtl819x_irq_requested)
		ret = -EINVAL;
	else if (probe ? rtl819x_ce_probe_registered : rtl819x_ce_registered)
		ret = -EBUSY;
	else if (rtl819x_ce_reload != rtl819x_ce_reload_hz)
		/* 🔴 -ERANGE: `cereload` has already made the period deliberately
		 * wrong.  Handing the tick over at a rate the kernel does not
		 * expect would make every later reading ambiguous between "the
		 * takeover worked and the clock is wrong" and "the takeover did
		 * not work".  The refusal is what keeps those two apart. */
		ret = -ERANGE;
	else {
		want = rtl819x_ce_reload << RTL819X_TC_VALUE_SHIFT;
		if (rtl819x_tc_rd(RTL819X_TC1DATA) != want)
			ret = -ENODEV;
		else if (!(rtl819x_tc_rd(RTL819X_TCCNR) & RTL819X_TCCNR_TC1EN))
			ret = -ENODEV;
		else
			ret = rtl819x_ce_precheck();
	}

	/* 🔴 Marked registered BEFORE the call and inside the same critical
	 * section as the -EBUSY test.  clockevents_register_device() can call
	 * set_mode(PERIODIC) synchronously, which sets ce_live, after which the
	 * next TC1 interrupt is a system tick -- so `disarm`'s refusal has to
	 * already be in force when that happens.  The function returns void and
	 * cannot fail, so there is no path that leaves this flag set over a
	 * registration that did not occur. */
	if (!ret) {
		if (probe)
			rtl819x_ce_probe_registered = 1;
		else
			rtl819x_ce_registered = 1;
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	if (ret)
		return ret;

	/* Outside the lock: the registration path takes clockevents_lock and
	 * tick_device_lock and calls back into set_mode. */
	cd = probe ? &rtl819x_tc1_cevt_probe : &rtl819x_tc1_cevt;
	clockevents_register_device(cd);
	return 0;
}

/*
 * `cereload <counts>`.  See RTL819X_CE_RELOAD_MIN for why this exists.
 *
 * The write is a plain store to TC1DATA under this driver's lock.  D Table 21
 * does not say whether a reload written mid-period takes effect at the next
 * wrap or immediately, and this verb does not need to know: either way the
 * period that follows is the new one, and the cell that uses it measures over
 * seconds.  ⚠️ That ignorance is stated rather than assumed away -- a cell
 * that tried to measure the FIRST period after the write would be measuring
 * something this project has not established.
 */
static int rtl819x_tc1_set_cereload(const char *s)
{
	unsigned long n, flags;
	char *end;
	int ret = 0;

	n = simple_strtoul(s, &end, 10);
	if (end == s || *end != '\0')
		return -EINVAL;
	if (n < RTL819X_CE_RELOAD_MIN || n > RTL819X_CE_RELOAD_MAX)
		return -ERANGE;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_mode != RTL819X_MODE_CE)
		ret = -EINVAL;
	else if (!rtl819x_tc1_armed)
		ret = -EINVAL;
	else {
		rtl819x_ce_reload = (u32)n;
		rtl819x_ce_reload_writes++;
		rtl819x_tc_wr(RTL819X_TC1DATA,
			      rtl819x_ce_reload << RTL819X_TC_VALUE_SHIFT);
		/* period_jiffies follows the reload, so a dump taken after
		 * `cereload 4000` says 2 and not 1 -- and the kernel still
		 * believes 1, which is the whole point of the cell. */
		rtl819x_derive_period();
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

/* `mode cs` / `mode ce`, while disarmed and before any registration. */
static int rtl819x_tc1_set_mode_verb(const char *s)
{
	unsigned long flags;
	int m, ret = 0;

	if (!strcmp(s, "cs"))
		m = RTL819X_MODE_CS;
	else if (!strcmp(s, "ce"))
		m = RTL819X_MODE_CE;
	else
		return -EINVAL;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_tc1_armed)
		ret = -EBUSY;
	else if (rtl819x_ce_registered || rtl819x_ce_probe_registered)
		ret = -EBUSY;
	else {
		rtl819x_mode = m;
		rtl819x_derive_period();
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

/*
 * `rating <n>`, before registration only.
 *
 * It exists so that one seating can take BOTH sides of
 * tick_check_new_device()'s inequality with the same code and the same
 * hardware: a value at or below RTL819X_CE_RATING_VENDOR must not take the
 * tick, and a value above it must.  A rating that could only be set at
 * compile time would make those two readings two different images.
 */
static int rtl819x_tc1_set_rating(const char *s)
{
	unsigned long r, flags;
	char *end;
	int ret = 0;

	r = simple_strtoul(s, &end, 10);
	if (end == s || *end != '\0')
		return -EINVAL;
	if (r < RTL819X_CE_RATING_MIN || r > RTL819X_CE_RATING_MAX)
		return -ERANGE;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_ce_registered)
		ret = -EBUSY;
	else
		rtl819x_tc1_cevt.rating = (int)r;
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

/*
 * The handler.  IRQF_DISABLED, so interrupts are already off and a plain
 * spin_lock is enough.
 *
 * 讀 kernel/irq/chip.c handle_level_irq(): mask_ack_irq() runs first (the
 * ICTL chip's .mask_ack is bsp_ictl_irq_mask, which masks and does not ack),
 * then this runs, then the source is unmasked UNLESS desc->status carries
 * IRQ_DISABLED.  So clearing TC1IP here is what makes the unmask safe, and
 * disable_irq_nosync() -- which sets that flag -- is what happens when the
 * clear does not take.
 */
static irqreturn_t rtl819x_tc1_isr(int irq, void *dev_id)
{
	u32 ir, back;
	int stuck = 0, live;

	spin_lock(&rtl819x_tc_lock);
	ir = rtl819x_tc_rd(RTL819X_TCIR);
	if (!(ir & RTL819X_TCIR_TC1IP)) {
		/* 🆕 R5-3b.  TC1IP clear on entry is counted SEPARATELY from
		 * "not ours", because SPEC.md IRQ-09 gives it a second cause
		 * that has nothing to do with ownership: the vendor's
		 * bsp_timer_ack() erases every pending bit in TCIR a hundred
		 * times a second, and it can erase ours between the latch and
		 * this read.  irq_preacked is that rate, and 量 seating 12 it
		 * was 0 in 119,818 deliveries. */
		rtl819x_irq_preacked++;

		/* 🔴 In clockevent mode this is NOT a reason to return early,
		 * and that is the design constraint IRQ-09 imposes on this
		 * step.  讀 arch/rlx/bsp/irq.c bsp_ictl_irq_dispatch(): line 25
		 * is reached only when GIMR & GISR has BSP_TC1_IP set, so the
		 * dispatcher has ALREADY proved the interrupt is TC1's -- the
		 * TCIR read is a second and weaker witness.  Skipping
		 * event_handler here would drop a system tick to save a check
		 * that the caller already made.
		 *
		 * In clocksource mode the old behaviour is kept exactly, because
		 * cell I1's refutation condition is "anything different from
		 * seating 11" and a control that has moved is not a control. */
		if (rtl819x_mode != RTL819X_MODE_CE) {
			/* Not ours.  讀 kernel/irq/spurious.c
			 * note_interrupt(): after 100,000 interrupts on a line,
			 * more than 99,900 of them unhandled disables it.  A
			 * second net under the one below, and a slow one -- it
			 * is not the guard, it is the backstop. */
			rtl819x_irq_spurious++;
			spin_unlock(&rtl819x_tc_lock);
			return IRQ_NONE;		/* see note_interrupt */
		}
	}
	rtl819x_tc_wr(RTL819X_TCIR,
		      (ir & RTL819X_TCIR_IE_BITS) | RTL819X_TCIR_TC1IP);
	back = rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_irq_last_tcir = back;
	rtl819x_irq_count++;
	if (back & RTL819X_TCIR_TC1IP) {
		rtl819x_irq_stuck++;
		stuck = 1;
	}
	if (rtl819x_mode == RTL819X_MODE_CE) {
		/* Exact, not extended: this handler runs once per reload by
		 * construction, so the accumulator advances by the period
		 * itself and never has to reconstruct a wrap. */
		rtl819x_ce_cycles += rtl819x_ce_reload;
	} else {
		/* Free: the handler runs at least once per period, so it is a
		 * better driver of the extension than the timer, and it costs
		 * two register reads that have already happened. */
		rtl819x_ext_advance(rtl819x_tc1_cycles());
	}
	live = rtl819x_ce_live;
	spin_unlock(&rtl819x_tc_lock);

	/* 🆕 R5-3b.  The tick, outside this driver's lock on purpose.
	 *
	 * event_handler is tick_handle_periodic once the core has taken this
	 * device, and that path takes xtime_lock (write side) and rq->lock.
	 * Holding rtl819x_tc_lock across it would put this driver's lock
	 * OUTSIDE two of the kernel's busiest, for no reason: the ICTL line is
	 * masked by mask_ack_irq until this handler returns, so nothing of ours
	 * can re-enter, and every field the handler could want was read above.
	 *
	 * Before the handover -- and during the SHUTDOWN window inside
	 * clockevents_exchange_device() -- event_handler is
	 * clockevents_handle_noop, which is why calling it unconditionally
	 * while ce_live is safe rather than merely convenient. */
	if (live)
		rtl819x_tc1_cevt.event_handler(&rtl819x_tc1_cevt);

	/* Outside our lock on purpose: disable_irq_nosync takes desc->lock, and
	 * nesting that inside this one creates an ordering that nothing else
	 * here needs.  Between the unlock and this call the source is still
	 * masked by mask_ack_irq, so nothing can arrive.
	 *
	 * 🔴 R5-3b: once the tick is ours this call STOPS THE SYSTEM CLOCK, and
	 * it is kept anyway.  A storm on line 25 with the tick on it is a
	 * livelocked board that also stops the clock, and it stops the vendor's
	 * TC0 handler too -- which is what pets the hardware watchdog
	 * (CONFIG_RTL_WTDOG=y, 讀 arch/rlx/kernel/rlx-cevt.c:159).  A stopped
	 * clock leaves a board that can be read; a livelock leaves one that
	 * resets itself.  Neither is good and the first is better. */
	if (stuck)
		disable_irq_nosync(RTL819X_TC1_IRQ);
	return IRQ_HANDLED;
}

/*
 * I4.  The first real delivery in this project.
 *
 * request_irq() ends in desc->chip->startup(), which for the ICTL chip is the
 * unmask that sets GIMR bit 9 -- so the mask is moved BY ITS OWNER (讀
 * arch/rlx/bsp/irq.c bsp_ictl_irq_unmask, an unlocked read-modify-write that
 * a second writer would race).  This driver never writes GIMR.
 */
static int rtl819x_tc1_reqirq(void)
{
	unsigned long flags;
	int ret;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_irq_requested)
		ret = -EBUSY;
	else if (!rtl819x_tc1_armed)
		ret = -EINVAL;
	else if (!rtl819x_tc1ie_set)
		ret = -EINVAL;			/* I2 first, or nothing fires */
	else if (!rtl819x_ack_proven)
		ret = -EPERM;			/* I3 first.  See the header. */
	else
		ret = 0;
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	if (ret)
		return ret;

	/* Outside the lock: request_irq allocates with GFP_KERNEL. */
	ret = request_irq(RTL819X_TC1_IRQ, rtl819x_tc1_isr, IRQF_DISABLED,
			  RTL819X_PROC_NAME, &rtl819x_irq_cookie);
	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!ret) {
		rtl819x_irq_requested = 1;
		/* 🆕 R5-3b.  The pre-check's window opens here and nowhere else.
		 * `cevt` compares (irq_count, jiffies) against this pair, so the
		 * window is exactly "since delivery began" -- no verb to
		 * remember, no clock for the operator to read, and a window
		 * that cannot be reset to make a failing ratio pass. */
		rtl819x_ce_base_irq = rtl819x_irq_count;
		rtl819x_ce_base_j = get_jiffies_64();
	}
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return ret;
}

static int rtl819x_tc1_freeirq(void)
{
	unsigned long flags;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!rtl819x_irq_requested) {
		rtl819x_last_verdict = -EINVAL;
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		return -EINVAL;
	}
	rtl819x_irq_requested = 0;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* free_irq can sleep, and it must not be called from interrupt context
	 * (讀 kernel/irq/manage.c: __free_irq opens with WARN(in_interrupt())).
	 * This runs from a /proc write, which is process context.
	 *
	 * A depth left behind by the storm guard does NOT survive: __free_irq
	 * sets IRQ_DISABLED and shuts the line down when the last action goes,
	 * and it is the NEXT __setup_irq that puts depth back to 0 -- so the
	 * imbalance is cleared by re-requesting, not by freeing. Said this way
	 * because the first draft of this comment credited free_irq with it. */
	free_irq(RTL819X_TC1_IRQ, &rtl819x_irq_cookie);
	return 0;
}

/*
 * 🔄 R5-3a: disarm unwinds EVERYTHING this driver created, in reverse order.
 *
 * Version 1.0 had two writes to undo and undid both -- 量 seating 11, twice,
 * the second after a 703 s arm.  Version 2.0 can also have requested an IRQ
 * and set TCIR bit 30, and leaving either behind would break the property
 * that reading made a result: `tccnr_at_init`/`tcir_at_init` are in /proc so
 * that "the block is as we found it" is a COMPARISON, and a disarm that left
 * TC1IE set would make that comparison false while reporting success.
 */
static int rtl819x_tc1_disarm(void)
{
	unsigned long flags;
	u32 cnr, ir;
	int had_irq;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!rtl819x_tc1_armed) {
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		return -EINVAL;
	}
	/* 🔴 R5-3b.  -EBUSY once EITHER clock_event_device is registered, and
	 * this refusal is the honest form of "the handover is one-way".
	 *
	 * 讀 kernel/time/clockevents.c: there is no unregister.  A registered
	 * device sits on clockevent_devices for the life of the boot, and if it
	 * is also the tick device its interrupt is the only thing advancing
	 * jiffies.  Stopping TC1 here would stop the system clock with nothing
	 * able to restart it -- and it would do so from a /proc write, i.e.
	 * from a process that then never runs again.
	 *
	 * The probe device is included even though it was never selected: it
	 * points at the same hardware, and a rule that depends on the core
	 * having declined it is a rule that depends on the experiment coming
	 * out the expected way. */
	if (rtl819x_ce_registered || rtl819x_ce_probe_registered) {
		rtl819x_last_verdict = -EBUSY;
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		return -EBUSY;
	}
	rtl819x_tc1_armed = 0;
	had_irq = rtl819x_irq_requested;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* Order: stop delivery, then stop the source, then stop the counter.
	 * The reverse would leave a window where the flag can be raised with
	 * no handler installed -- harmless here because GIMR would already be
	 * masked, and written this way so it stays harmless if that changes. */
	if (had_irq)
		rtl819x_tc1_freeirq();

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_tc1ie_set) {
		rtl819x_tc1ie_write(0);
		rtl819x_tc1ie_set = 0;
	}
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* Outside the lock: del_timer_sync waits for a running callback, and
	 * that callback takes this lock. */
	del_timer_sync(&rtl819x_ext_timer);

	clocksource_unregister(&rtl819x_tc1_clocksource);

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	cnr = rtl819x_tc_rd(RTL819X_TCCNR);
	rtl819x_tc_wr(RTL819X_TCCNR, cnr & ~RTL819X_TCCNR_TC1_BITS);

	/* Clear a TC1IP that may have latched while TC1 ran, and do it with a
	 * value whose TC0IP bit is 0 so the vendor's pending tick is left
	 * alone.  Both IP bits are write-1-to-clear (D Table 25), so a 0 here
	 * is documented to have no effect.  This is the one write in the file
	 * that rests on a single source; it happens only on disarm, and the
	 * before/after TCIR are both in the /proc dump so its effect is
	 * readable rather than assumed. */
	ir = rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_tc_wr(RTL819X_TCIR,
		      (ir & RTL819X_TCIR_IE_BITS) | RTL819X_TCIR_TC1IP);

	rtl819x_last_verdict = 0;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return 0;
}

/* ------------------------------------------------------------------------
 * /proc/rtl819x-timer
 *
 * Machine-readable key=value, one per line, because the reader at the other
 * end is a bench card at 38400 baud and a human transcribing hex is the
 * error source this whole project spends its effort avoiding.
 *
 * Nanoseconds are NOT computed here.  ext_cycles * mult overflows u64 after
 * about ten minutes of counting, and a driver that silently wrapped its own
 * report would be worse than one that reports cycles and says what to
 * multiply by.
 * ------------------------------------------------------------------------ */

static int rtl819x_tc_read_proc(char *page, char **start, off_t off,
				int count, int *eof, void *data)
{
	unsigned long flags;
	struct timespec ts;
	u64 j, ext, gap_j;
	u32 cyc, tc0cnt, tc0data, tc1data, cnr, ir, cdbr, gimr, gisr;
	u32 irr0, irr1, irr2, irr3, status;
	u32 gap, reads, ticks;
	int armed, verdict, len = 0;
	/* 🆕 R5-3b.  Snapshotted with everything else, for the same reason:
	 * a takeover reading and the counter reading that explains it have to
	 * describe one instant. */
	int ce_mode_, ce_reg, ce_preg, ce_live_, ce_lm, ce_plm;
	u32 ce_mc, ce_pmc, ce_nc, ce_bm, ce_hb, preacked, ce_dc, ce_dj, ce_rat;
	u64 ce_cyc;
	unsigned long ce_h;

	/* 🔴 `Status` is read BEFORE the lock, and that is not tidiness.
	 * spin_lock_irqsave() disables interrupts, so a Status read inside it
	 * would report IEc = 0 ALWAYS -- a constant dressed as a measurement.
	 * IM2 and BEV are unaffected by the lock, so only one of the three
	 * bits needed care and all three are taken where all three are true.
	 *
	 * ⚠️ `ST0_IEC` and not `ST0_IE`: 讀 arch/rlx/include/asm/rlxregs.h,
	 * this core has the MIPS-I three-deep interrupt-enable stack
	 * (IEc/IEp/IEo at bits 0/2/4) and no single `ST0_IE`. That agrees with
	 * SOURCES.json's binutils note that every Lexra core is ISA_MIPS1. */
	status = read_c0_status();

	/* One coherent sample: the counter, the tick and the wall clock have
	 * to describe the same instant or the ratio R5-2 computes from them
	 * carries the sampling jitter as if it were a frequency error. */
	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	cyc	= rtl819x_tc1_cycles();
	tc0cnt	= rtl819x_tc_rd(RTL819X_TC0CNT);
	j	= get_jiffies_64();
	getnstimeofday(&ts);
	/* 🔄 R5-3b: not in clockevent mode.  rtl819x_ext_advance() reduces its
	 * gap mod a power-of-two mask that the hardware is not using there. */
	if (rtl819x_tc1_armed && rtl819x_mode != RTL819X_MODE_CE)
		rtl819x_ext_advance(cyc);
	tc0data	= rtl819x_tc_rd(RTL819X_TC0DATA);
	tc1data	= rtl819x_tc_rd(RTL819X_TC1DATA);
	cnr	= rtl819x_tc_rd(RTL819X_TCCNR);
	ir	= rtl819x_tc_rd(RTL819X_TCIR);
	cdbr	= rtl819x_tc_rd(RTL819X_CDBR);
	gimr	= rtl819x_intc_rd(RTL819X_GIMR);
	gisr	= rtl819x_intc_rd(RTL819X_GISR);
	irr0	= rtl819x_intc_rd(RTL819X_IRR0);
	irr1	= rtl819x_intc_rd(RTL819X_IRR1);
	irr2	= rtl819x_intc_rd(RTL819X_IRR2);
	irr3	= rtl819x_intc_rd(RTL819X_IRR3);
	ext	= rtl819x_ext_cycles;
	gap	= rtl819x_ext_gap_max;
	gap_j	= rtl819x_ext_gap_max_j;
	ticks	= rtl819x_ext_ticks;
	reads	= rtl819x_ext_reads;
	armed	= rtl819x_tc1_armed;
	verdict	= rtl819x_last_verdict;
	ce_mode_= rtl819x_mode;
	ce_reg	= rtl819x_ce_registered;
	ce_preg	= rtl819x_ce_probe_registered;
	ce_live_= rtl819x_ce_live;
	ce_lm	= rtl819x_ce_last_mode;
	ce_plm	= rtl819x_ce_probe_last_mode;
	ce_mc	= rtl819x_ce_mode_calls;
	ce_pmc	= rtl819x_ce_probe_mode_calls;
	ce_nc	= rtl819x_ce_next_calls;
	ce_bm	= rtl819x_ce_badmode;
	ce_hb	= rtl819x_ce_hw_bad;
	ce_cyc	= rtl819x_ce_cycles;
	ce_dc	= rtl819x_ce_check_dc;
	ce_dj	= rtl819x_ce_check_dj;
	ce_rat	= (u32)rtl819x_tc1_cevt.rating;
	ce_h	= (unsigned long)rtl819x_tc1_cevt.event_handler;
	preacked = rtl819x_irq_preacked;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	len += scnprintf(page + len, PAGE_SIZE - len, "driver=rtl819x-timer %s\n",
			 RTL819X_TC_VERSION);
	len += scnprintf(page + len, PAGE_SIZE - len, "state=%s\n", armed ? "armed" : "idle");
	len += scnprintf(page + len, PAGE_SIZE - len, "last_verdict=%d\n", verdict);

	/* Declared parameters -- so the card does not re-derive them and get
	 * a different answer from the driver's.
	 *
	 * 🔄 R5-3a: `hz_assumed` is kept AND is no longer what the clocksource
	 * runs on.  It is the compiled-in constant, which seating 11 showed is
	 * the loader's rate and 71.43x the kernel's; `hz_used` is what was
	 * derived at init and built into `mult`.  Both are printed because a
	 * reader comparing this capture with seating 11's needs to see which
	 * number moved and which did not. */
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_assumed=%u\n", RTL819X_TC_HZ);
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_tick=%u\n", rtl819x_hz_tick);
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_cdbr=%u\n", rtl819x_hz_cdbr);
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_agree=%d\n", rtl819x_hz_agree);
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_used=%u\n", rtl819x_hz_used);
	/* 🔄 R5-3b: the HARDWARE period, which in clockevent mode is
	 * hz_used / HZ and not mask + 1. */
	len += scnprintf(page + len, PAGE_SIZE - len, "period_cycles=%u\n",
			 rtl819x_tc1_reload());
	len += scnprintf(page + len, PAGE_SIZE - len, "mask_bits=%u\n", rtl819x_period_bits);
	len += scnprintf(page + len, PAGE_SIZE - len, "shift=%u\n", rtl819x_shift_used);
	len += scnprintf(page + len, PAGE_SIZE - len, "mult=%u\n", rtl819x_tc1_clocksource.mult);
	len += scnprintf(page + len, PAGE_SIZE - len, "rating=%d\n", RTL819X_TC1_RATING);
	len += scnprintf(page + len, PAGE_SIZE - len, "period_jiffies=%llu\n",
			 (unsigned long long)rtl819x_period_j);
	len += scnprintf(page + len, PAGE_SIZE - len, "ext_interval_j=%lu\n",
			 rtl819x_ext_interval_j);
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_kernel=%u\n", (unsigned)HZ);

	/* The sample. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_cycles=%u\n", cyc);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext=%llu\n", (unsigned long long)ext);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_reads=%u\n", reads);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_gap_max=%u\n", gap);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_gap_max_j=%llu\n",
			 (unsigned long long)gap_j);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_ticks=%u\n", ticks);
	/* 🔄 R5-3a: decided in JIFFIES, which this driver never reduces, so it
	 * cannot alias.  The old test was `gap < mask/2` on a gap already
	 * reduced mod the period -- 量 TM-5b2, a real 140,693,532-count gap
	 * read as 6,475,672 and passed.  This is the owner's rule
	 * (Δjiffies × TICK_NSEC against one period in ns) with both sides
	 * divided by TICK_NSEC: the same inequality, no 64-bit multiply, and
	 * period_jiffies is printed above so a reader can redo it. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_trusted=%d\n",
			 (reads > 0 && rtl819x_period_j > 0
			  && gap_j < rtl819x_period_j) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "jiffies=%llu\n", (unsigned long long)j);
	len += scnprintf(page + len, PAGE_SIZE - len, "wall=%ld.%09ld\n",
			 (long)ts.tv_sec, ts.tv_nsec);

	/* The raw block, now. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tc0data=%08X\n", tc0data);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc0cnt=%08X\n", tc0cnt);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1data=%08X\n", tc1data);
	len += scnprintf(page + len, PAGE_SIZE - len, "tccnr=%08X\n", cnr);
	len += scnprintf(page + len, PAGE_SIZE - len, "tcir=%08X\n", ir);
	len += scnprintf(page + len, PAGE_SIZE - len, "cdbr=%08X\n", cdbr);

	/* The global controller, read and never written.  Both words whole, and
	 * then the four bits the hazard is about on their own lines: TC1_IE is
	 * what would let a TC1 timeout reach the CPU, and TC1_IP after at least
	 * one period says whether the flag latches at all. */
	len += scnprintf(page + len, PAGE_SIZE - len, "gimr=%08X\n", gimr);
	len += scnprintf(page + len, PAGE_SIZE - len, "gisr=%08X\n", gisr);
	len += scnprintf(page + len, PAGE_SIZE - len, "gimr_tc0ie=%d\n",
			 (gimr & RTL819X_INTC_TC0) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "gimr_tc1ie=%d\n",
			 (gimr & RTL819X_INTC_TC1) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "gisr_tc0ip=%d\n",
			 (gisr & RTL819X_INTC_TC0) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "gisr_tc1ip=%d\n",
			 (gisr & RTL819X_INTC_TC1) ? 1 : 0);

	/* TCIR bit 28 on its own line: whether a TC1 timeout latches a pending
	 * bit while TC1IE is clear is the undetermined this driver's arming
	 * path is shaped around, and it is answered by reading this after the
	 * period has elapsed at least once. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tcir_tc1ip=%d\n",
			 (ir & RTL819X_TCIR_TC1IP) ? 1 : 0);

	/* 🆕 R5-3a.  TC1IE is the gate seating 11 left clear without knowing
	 * it -- SPEC.md REG-10, docs/interrupt-map.md 3.2 -- so it goes on its
	 * own line beside TC1IP, which is the bit it is supposed to produce.
	 * The two together are the whole of cell I2. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tcir_tc1ie=%d\n",
			 (ir & RTL819X_TCIR_TC1IE) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1ie_ours=%d\n",
			 rtl819x_tc1ie_set);
	len += scnprintf(page + len, PAGE_SIZE - len, "ackip_before=%d\n",
			 rtl819x_ackip_before);
	len += scnprintf(page + len, PAGE_SIZE - len, "ackip_after=%d\n",
			 rtl819x_ackip_after);
	len += scnprintf(page + len, PAGE_SIZE - len, "ack_proven=%d\n",
			 rtl819x_ack_proven);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_num=%d\n",
			 RTL819X_TC1_IRQ);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_requested=%d\n",
			 rtl819x_irq_requested);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_count=%u\n",
			 rtl819x_irq_count);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_spurious=%u\n",
			 rtl819x_irq_spurious);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_stuck=%u\n",
			 rtl819x_irq_stuck);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_last_tcir=%08X\n",
			 rtl819x_irq_last_tcir);

	/* 🆕 R5-3a.  The routing, and the CPU-side gate.  Read only, and free:
	 * the four IRR words are in the block this driver already maps, and
	 * `Status` costs one mfc0.  Three of the four IRRs have never been read
	 * on this die and the fourth only at the loader prompt. */
	len += scnprintf(page + len, PAGE_SIZE - len, "irr0=%08X\n", irr0);
	len += scnprintf(page + len, PAGE_SIZE - len, "irr1=%08X\n", irr1);
	len += scnprintf(page + len, PAGE_SIZE - len, "irr2=%08X\n", irr2);
	len += scnprintf(page + len, PAGE_SIZE - len, "irr3=%08X\n", irr3);
	len += scnprintf(page + len, PAGE_SIZE - len, "irr1_tc0_rs=%u\n",
			 irr1 & 0xFu);
	len += scnprintf(page + len, PAGE_SIZE - len, "irr1_tc1_rs=%u\n",
			 (irr1 >> 4) & 0xFu);
	len += scnprintf(page + len, PAGE_SIZE - len, "status=%08X\n", status);
	len += scnprintf(page + len, PAGE_SIZE - len, "status_im2=%d\n",
			 (status & (1u << 10)) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "status_bev=%d\n",
			 (status & ST0_BEV) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "status_iec=%d\n",
			 (status & ST0_IEC) ? 1 : 0);

	/* The block as it was before this driver wrote anything, so that
	 * "TC0 undisturbed" is a comparison the reader can make. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tc0data_at_init=%08X\n",
			 rtl819x_tc0data_at_init);
	len += scnprintf(page + len, PAGE_SIZE - len, "tccnr_at_init=%08X\n",
			 rtl819x_tccnr_at_init);
	len += scnprintf(page + len, PAGE_SIZE - len, "tcir_at_init=%08X\n",
			 rtl819x_tcir_at_init);
	len += scnprintf(page + len, PAGE_SIZE - len, "cdbr_at_init=%08X\n",
			 rtl819x_cdbr_at_init);
	len += scnprintf(page + len, PAGE_SIZE - len, "gimr_at_init=%08X\n",
			 rtl819x_gimr_at_init);
	len += scnprintf(page + len, PAGE_SIZE - len, "tccnr_after_arm=%08X\n",
			 rtl819x_tccnr_after_arm);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc0_undisturbed=%d\n",
			 ((cnr ^ rtl819x_tccnr_at_init)
			& RTL819X_TCCNR_TC0_BITS) ? 0 : 1);
	len += scnprintf(page + len, PAGE_SIZE - len, "arm_delta_100us=%u\n",
			 rtl819x_tc1_delta_at_arm);

	/* 🆕 R5-3b.  Appended at the end and not interleaved, so a capture from
	 * version 2.0 and one from 3.0 differ by a suffix -- which is what makes
	 * `diff` between two seatings readable. */
	len += scnprintf(page + len, PAGE_SIZE - len, "mode=%s\n",
			 ce_mode_ == RTL819X_MODE_CE ? "ce" : "cs");
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_reload=%u\n",
			 rtl819x_ce_reload);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_reload_hz=%u\n",
			 rtl819x_ce_reload_hz);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_reload_writes=%u\n",
			 rtl819x_ce_reload_writes);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_reload_exact=%d\n",
			 rtl819x_ce_reload_exact);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_rating=%u\n", ce_rat);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_rating_probe=%d\n",
			 RTL819X_CE_RATING_PROBE);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_rating_vendor=%d\n",
			 RTL819X_CE_RATING_VENDOR);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_registered=%d\n", ce_reg);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_probe_registered=%d\n",
			 ce_preg);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_live=%d\n", ce_live_);
	/* The mode enum, as the number the core wrote: 0 UNUSED, 1 SHUTDOWN,
	 * 2 PERIODIC, 3 ONESHOT, 4 RESUME (讀 include/linux/clockchips.h).
	 * -1 means this driver's own initial value and no call yet. */
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_mode=%d\n", ce_lm);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_mode_calls=%u\n", ce_mc);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_probe_mode=%d\n", ce_plm);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_probe_mode_calls=%u\n",
			 ce_pmc);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_next_calls=%u\n", ce_nc);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_badmode=%u\n", ce_bm);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_hw_bad=%u\n", ce_hb);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_cycles=%llu\n",
			 (unsigned long long)ce_cyc);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_check_dc=%u\n", ce_dc);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_check_dj=%u\n", ce_dj);
	/* 🟢 The takeover's second and independent witness.  Before it,
	 * event_handler is clockevents_handle_noop; after
	 * tick_set_periodic_handler() it is tick_handle_periodic.  The address
	 * is printed as well as the flag so it can be resolved against this
	 * build's own System.map -- a check that needs no second reading from
	 * the device and cannot be produced by any other code path. */
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_handler=%08lX\n", ce_h);
	len += scnprintf(page + len, PAGE_SIZE - len, "ce_handler_is_noop=%d\n",
			 (ce_h == (unsigned long)clockevents_handle_noop) ? 1 : 0);
	len += scnprintf(page + len, PAGE_SIZE - len, "irq_preacked=%u\n",
			 preacked);

	*eof = 1;
	if (off >= len)
		return 0;
	*start = page + off;
	len -= off;
	return (len > count) ? count : len;
}

/*
 * `period <bits>`, while disarmed only.
 *
 * simple_strtoul and not sscanf: this runs in a /proc write from a bench
 * card, the input is one small integer, and pulling in the scanf machinery
 * for it would be the larger change.
 *
 * ⚠️ It refuses while armed.  The alternative -- re-loading TC1DATA under a
 * running counter -- would leave the clocksource's mask and the hardware's
 * period disagreeing for the length of one wrap, and `(now - last) & mask` is
 * exact only while they agree.  That is the one property a power-of-two
 * period is chosen for.
 */
static int rtl819x_tc1_set_period(const char *s)
{
	unsigned long bits;
	unsigned long flags;
	char *end;

	bits = simple_strtoul(s, &end, 10);
	if (end == s || *end != '\0')
		return -EINVAL;
	if (bits < RTL819X_TC1_BITS_MIN || bits > RTL819X_TC1_BITS_MAX)
		return -ERANGE;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (rtl819x_tc1_armed) {
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		return -EBUSY;
	}
	rtl819x_period_bits = (unsigned int)bits;
	/* 🆕 R5-3b: and the derived pair follows it immediately, so that a
	 * disarmed dump never shows mask_bits and period_jiffies describing two
	 * different periods. */
	rtl819x_derive_period();
	rtl819x_last_verdict = 0;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
	return 0;
}

static int rtl819x_tc_write_proc(struct file *file, const char __user *buffer,
				 unsigned long count, void *data)
{
	char buf[16];
	unsigned long n = count;
	int ret;

	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "arm"))
		ret = rtl819x_tc1_arm();
	else if (!strcmp(buf, "disarm"))
		ret = rtl819x_tc1_disarm();
	/* 🆕 R5-3a.  ONE VERB PER GATE, and that is the design rather than an
	 * interface preference: docs/interrupt-map.md 3.3 makes I1..I4 four
	 * separate writes and four separate reads so that a wedge costs the
	 * rest of a seating and not the step before it.  Folding `armirq` into
	 * `arm` would have merged I1 and I2, and I1's refutation condition is
	 * "anything different from seating 11" -- which is untestable if the
	 * thing being used as the control has changed. */
	else if (!strcmp(buf, "armirq"))
		ret = rtl819x_tc1_armirq();
	else if (!strcmp(buf, "disarmirq"))
		ret = rtl819x_tc1_disarmirq();
	else if (!strcmp(buf, "ackip"))
		ret = rtl819x_tc1_ackip();
	else if (!strcmp(buf, "reqirq"))
		ret = rtl819x_tc1_reqirq();
	else if (!strcmp(buf, "freeirq"))
		ret = rtl819x_tc1_freeirq();
	else if (!strncmp(buf, "period ", 7))
		ret = rtl819x_tc1_set_period(buf + 7);
	/* 🆕 R5-3b.  `cevtprobe` before `cevt` is not an ordering this code
	 * enforces -- the two are independent registrations -- but it is the
	 * order the card runs them in, because the probe is the negative
	 * control for the reading `cevt` produces. */
	else if (!strcmp(buf, "cevtprobe"))
		ret = rtl819x_tc1_cevt_register(1);
	else if (!strcmp(buf, "cevt"))
		ret = rtl819x_tc1_cevt_register(0);
	else if (!strncmp(buf, "mode ", 5))
		ret = rtl819x_tc1_set_mode_verb(buf + 5);
	else if (!strncmp(buf, "rating ", 7))
		ret = rtl819x_tc1_set_rating(buf + 7);
	else if (!strncmp(buf, "cereload ", 9))
		ret = rtl819x_tc1_set_cereload(buf + 9);
	else
		return -EINVAL;

	/* The errno is the verdict and it is also in the /proc dump, so a
	 * refusal is legible both from the shell's exit status and from a
	 * capture taken afterwards. */
	return ret ? ret : (int)count;
}

/* ------------------------------------------------------------------------
 * init
 *
 * arch_initcall: after core_initcall, where clocksource_jiffies registers,
 * and after start_kernel's time_init(), so the block is in the state the
 * vendor's own timer left it.  procfs exists before any initcall
 * (proc_root_init() runs from vfs_caches_init()), so nothing here needs a
 * later level.
 *
 * Nothing is printed.  CONFIG_PRINTK is not set in this build and printk()
 * compiles to a stub (config/rlxfw-kernel.delta records the measurement), so
 * a message here would be a message nobody receives; the /proc file carries
 * the verdict instead.
 * ------------------------------------------------------------------------ */

/*
 * The shift search.  Largest shift whose mult fits u32, whose mask*mult fits
 * s63, and whose mult is not so small that the ns conversion goes coarse.
 * -> the shift, or 0 if nothing qualifies (which cannot happen for a hz in
 * range and is handled anyway, because "cannot happen" is how a driver ends
 * up registering a clocksource whose mult is 0).
 */
static u32 __init rtl819x_pick_shift(u32 hz, u32 mask, u32 *mult_out)
{
	int shift;

	for (shift = RTL819X_SHIFT_MAX; shift >= 0; shift--) {
		u64 m = ((u64)NSEC_PER_SEC << shift) + hz / 2;
		u64 prod;

		do_div(m, hz);
		if (m > 0xFFFFFFFFULL || m < RTL819X_MULT_FLOOR)
			continue;
		/* m <= 2^32-1 and mask <= 2^28-1, so this product is at most
		 * 2^60 and the check itself cannot overflow the u64 it is
		 * computed in. */
		prod = m * (u64)mask;
		if (prod > 0x7FFFFFFFFFFFFFFFULL)
			continue;
		*mult_out = (u32)m;
		return (u32)shift;
	}
	*mult_out = 0;
	return 0;
}

/*
 * The clockevent's shift search.  Largest shift whose ns->cycles multiplier
 * still fits the unsigned long the core stores it in.  Same shape as
 * rtl819x_pick_shift() above and a different direction: that one converts
 * cycles to nanoseconds, this one nanoseconds to cycles.
 */
static u32 __init rtl819x_ce_pick_shift(u32 hz, u32 *mult_out)
{
	int shift;

	for (shift = RTL819X_SHIFT_MAX; shift >= 0; shift--) {
		u64 m = ((u64)hz << shift) + NSEC_PER_SEC / 2;

		do_div(m, NSEC_PER_SEC);
		if (m > 0xFFFFFFFFULL || m == 0)
			continue;
		*mult_out = (u32)m;
		return (u32)shift;
	}
	*mult_out = 0;
	return 0;
}

static int __init rtl819x_timer_init(void)
{
	struct proc_dir_entry *pde;
	u32 div, mult = 0, lo, hi, ce_mult = 0;

	/* 25 must be a real IRQ number in this configuration.  NR_IRQS is 48 =
	 * 8 CPU + 8 LOPI + 32 ICTL (讀 arch/rlx/include/asm/mach-generic/irq.h),
	 * and if a config change ever shrinks it this stops the build rather
	 * than calling request_irq() on a number the kernel has no desc for. */
	BUILD_BUG_ON(RTL819X_TC1_IRQ >= NR_IRQS);

	rtl819x_tc0data_at_init	= rtl819x_tc_rd(RTL819X_TC0DATA);
	rtl819x_tccnr_at_init	= rtl819x_tc_rd(RTL819X_TCCNR);
	rtl819x_tcir_at_init	= rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_cdbr_at_init	= rtl819x_tc_rd(RTL819X_CDBR);
	rtl819x_gimr_at_init	= rtl819x_intc_rd(RTL819X_GIMR);

	/* The two derivations.  See RTL819X_TC_HZ for why there are two. */
	rtl819x_hz_tick = (rtl819x_tc0data_at_init >> RTL819X_TC_VALUE_SHIFT)
			* (u32)HZ;
	div = rtl819x_cdbr_at_init >> 16;
	rtl819x_hz_cdbr = div ? (RTL819X_SYS_CLK_HZ / div) : 0;

	/* Agreement, to 1 part in 2^12.  Written without division so a zero on
	 * either side cannot trap. */
	lo = rtl819x_hz_tick < rtl819x_hz_cdbr ? rtl819x_hz_tick : rtl819x_hz_cdbr;
	hi = rtl819x_hz_tick < rtl819x_hz_cdbr ? rtl819x_hz_cdbr : rtl819x_hz_tick;
	rtl819x_hz_agree = (lo > 0
			    && (u64)(hi - lo) << RTL819X_HZ_TOL_SHIFT <= (u64)lo);

	/*
	 * hz_tick is what the clocksource is built on, and the reason is a
	 * measurement rather than a preference: R5-2 verified
	 * ΔTC1 = Δjiffies × (TC0DATA >> 4) + Δ(TC0CNT >> 4) with residual
	 * EXACTLY ZERO over three intervals -- so "one jiffy is TC0DATA>>4
	 * counts" is 量 on this die, while hz_cdbr additionally needs the
	 * 200 MHz figure to be right.  hz_cdbr is the cross-check.
	 *
	 * 🔴 If TC0DATA reads 0 -- a block this driver's model does not
	 * describe -- the fallback is the compiled constant, and hz_used says
	 * which was taken.  Falling back SILENTLY to a rate 71.43x wrong is
	 * exactly what version 1.0 did without knowing it.
	 */
	rtl819x_hz_used = rtl819x_hz_tick ? rtl819x_hz_tick : RTL819X_TC_HZ;

	/* mult here and not in arm(): the /proc dump prints it, and a dump
	 * whose mult reads 0 until somebody arms would invite the reader to
	 * think the number is broken rather than unset.  NTP adjusts mult on
	 * the selected clocksource only, and at rating 0 this is never it. */
	/* 🔴 The search runs against the LARGEST mask this driver can be set
	 * to, not the current one.  `period` can shrink the mask later, and a
	 * smaller mask only relaxes the mask*mult bound -- so a shift chosen
	 * at the maximum stays valid for every period, and one chosen at the
	 * current period would not survive being widened again. */
	rtl819x_shift_used = rtl819x_pick_shift(rtl819x_hz_used,
						RTL819X_TC1_MASK, &mult);
	rtl819x_tc1_clocksource.shift = rtl819x_shift_used;
	rtl819x_tc1_clocksource.mult = mult;
	rtl819x_tc1_clocksource.mask = CLOCKSOURCE_MASK(rtl819x_period_bits);

	/* 🆕 R5-3b.  The clockevent's period is the vendor's own reload: 量
	 * REG-05, TC0DATA >> 4 = 2,000, and hz_used is (TC0DATA >> 4) * HZ, so
	 * hz_used / HZ is that same 2,000 by construction.  The division is
	 * checked rather than assumed because a kernel with a different HZ would
	 * make it inexact and the driver would then be running the system clock
	 * at a rate it never states. */
	rtl819x_ce_reload_hz = rtl819x_hz_used / (u32)HZ;
	rtl819x_ce_reload = rtl819x_ce_reload_hz;
	rtl819x_ce_reload_exact = (rtl819x_hz_used % (u32)HZ) == 0
				  && rtl819x_ce_reload_hz > 0;

	/* cpumask_of() is not a constant expression, so it cannot go in the
	 * initialiser.  It matters: tick_check_new_device() starts with
	 * cpumask_test_cpu(cpu, newdev->cpumask) and CONFIG_BUG is not set in
	 * this build, so clockevents_register_device()'s BUG_ON(!dev->cpumask)
	 * would not catch a NULL -- the dereference would. */
	rtl819x_tc1_cevt.cpumask = cpumask_of(0);
	rtl819x_tc1_cevt_probe.cpumask = cpumask_of(0);

	/* ns -> cycles, for fields nothing in this configuration reads.
	 * clockevents_program_event() is the only consumer and it is behind the
	 * oneshot paths this build does not have.  They are filled in anyway,
	 * with this driver's own shift search rather than the vendor's
	 * clockevent_set_clock(): that function is __cpuinit, and with
	 * CONFIG_HOTPLUG_CPU absent its text is discarded after init -- calling
	 * it from anywhere but here would be a jump into freed memory. */
	rtl819x_ce_shift = rtl819x_ce_pick_shift(rtl819x_hz_used, &ce_mult);
	rtl819x_tc1_cevt.shift = rtl819x_ce_shift;
	rtl819x_tc1_cevt.mult = ce_mult;
	rtl819x_tc1_cevt_probe.shift = rtl819x_ce_shift;
	rtl819x_tc1_cevt_probe.mult = ce_mult;
	if (ce_mult) {
		rtl819x_tc1_cevt.max_delta_ns =
			clockevent_delta2ns(1u << RTL819X_TC1_BITS_MAX,
					    &rtl819x_tc1_cevt);
		rtl819x_tc1_cevt.min_delta_ns =
			clockevent_delta2ns(16, &rtl819x_tc1_cevt);
		rtl819x_tc1_cevt_probe.max_delta_ns =
			rtl819x_tc1_cevt.max_delta_ns;
		rtl819x_tc1_cevt_probe.min_delta_ns =
			rtl819x_tc1_cevt.min_delta_ns;
	}

	/* Before procfs exists, so the very first `cat` describes the period the
	 * driver is actually configured for rather than two zeros. */
	rtl819x_derive_period();

	setup_timer(&rtl819x_ext_timer, rtl819x_ext_tick, 0UL);

	pde = create_proc_entry(RTL819X_PROC_NAME, 0644, NULL);
	if (!pde)
		return -ENOMEM;
	pde->read_proc  = rtl819x_tc_read_proc;
	pde->write_proc = rtl819x_tc_write_proc;
	return 0;
}
arch_initcall(rtl819x_timer_init);
