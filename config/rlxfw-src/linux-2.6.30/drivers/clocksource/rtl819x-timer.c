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
 *       ⚠️ What is NOT established is what Linux leaves in GIMR.  This driver
 *       never writes it; it READS it, refuses to arm while bit 9 is set, and
 *       prints both words, so the mask is a measurement taken before the
 *       write rather than an assumption carried into it.
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
 * WHAT THIS FILE DOES NOT KNOW, ON PURPOSE.
 * Whether arch/rlx registers a clocksource of its own is not looked up here.
 * The experiment does not need it: /sys/devices/system/clocksource/
 * clocksource0/available_clocksource answers it on the silicon, and not
 * knowing is what keeps docs/driver-diff.md's timer rows worth writing.
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

#define RTL819X_PROC_NAME	"rtl819x-timer"
#define RTL819X_TC_VERSION	"2.0"

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

static inline u32 rtl819x_tc1_cycles(void)
{
	return (rtl819x_tc_rd(RTL819X_TC1CNT) >> RTL819X_TC_VALUE_SHIFT)
		& rtl819x_tc1_mask();
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
		      (rtl819x_tc1_mask() + 1u) << RTL819X_TC_VALUE_SHIFT);
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
	rtl819x_tc1_armed = 1;

	/* The mask has to match the period that was just loaded, and it is read
	 * by clocksource_register() below. */
	rtl819x_tc1_clocksource.mask = CLOCKSOURCE_MASK(rtl819x_period_bits);

	/* One period in jiffies, and the quarter of it the extension timer
	 * runs at.  Both are computed here rather than at init because the
	 * period is settable and hz is derived: a constant would be right for
	 * one configuration.  At least 1 jiffy, so a very short period cannot
	 * ask for a zero-delay timer that re-arms itself forever. */
	rtl819x_period_j = (u64)(rtl819x_tc1_mask() + 1u) * HZ;
	do_div(rtl819x_period_j, rtl819x_hz_used ? rtl819x_hz_used : 1);
	rtl819x_ext_interval_j = (unsigned long)(rtl819x_period_j >> 2);
	if (rtl819x_ext_interval_j < 1)
		rtl819x_ext_interval_j = 1;
	mod_timer(&rtl819x_ext_timer, jiffies + rtl819x_ext_interval_j);

out:
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* Registration is outside the lock: clocksource_register() takes
	 * clocksource_lock with interrupts disabled and there is no reason to
	 * hold two. */
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
	int stuck = 0;

	spin_lock(&rtl819x_tc_lock);
	ir = rtl819x_tc_rd(RTL819X_TCIR);
	if (!(ir & RTL819X_TCIR_TC1IP)) {
		/* Not ours.  讀 kernel/irq/spurious.c note_interrupt(): after
		 * 100,000 interrupts on a line, more than 99,900 of them
		 * unhandled disables it.  A second net under the one below,
		 * and a slow one -- it is not the guard, it is the backstop. */
		rtl819x_irq_spurious++;
		spin_unlock(&rtl819x_tc_lock);
		return IRQ_NONE;			/* see note_interrupt */
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
	/* Free: the handler runs at least once per period, so it is a better
	 * driver of the extension than the timer, and it costs two register
	 * reads that have already happened. */
	rtl819x_ext_advance(rtl819x_tc1_cycles());
	spin_unlock(&rtl819x_tc_lock);

	/* Outside our lock on purpose: disable_irq_nosync takes desc->lock, and
	 * nesting that inside this one creates an ordering that nothing else
	 * here needs.  Between the unlock and this call the source is still
	 * masked by mask_ack_irq, so nothing can arrive. */
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
	if (!ret)
		rtl819x_irq_requested = 1;
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
	if (rtl819x_tc1_armed)
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
	len += scnprintf(page + len, PAGE_SIZE - len, "period_cycles=%u\n",
			 rtl819x_tc1_mask() + 1u);
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

static int __init rtl819x_timer_init(void)
{
	struct proc_dir_entry *pde;
	u32 div, mult = 0, lo, hi;

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

	setup_timer(&rtl819x_ext_timer, rtl819x_ext_tick, 0UL);

	pde = create_proc_entry(RTL819X_PROC_NAME, 0644, NULL);
	if (!pde)
		return -ENOMEM;
	pde->read_proc  = rtl819x_tc_read_proc;
	pde->write_proc = rtl819x_tc_write_proc;
	return 0;
}
arch_initcall(rtl819x_timer_init);
