/*
 * rtl819x-timer -- a Linux clocksource on the RTL8196E's Timer/Counter 1.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-1, 2026-09-03.  It is staged into
 * drivers/clocksource/ by tools/rlxfw-marks.py from kernel/;
 * config/rlxfw-marks.tsv carries the one Kbuild line that links it.
 *
 * NOT A BLIND WRITE.  docs/blind-write-ledger.md 4.3 records what had been
 * read of anyone else's timer when version 1.0 was written, on 2026-09-03;
 * the vendor's timer files were opened in full on 2026-09-04 and 2026-09-06
 * (ledger 4.2 and 4.3), and everything from version 2.0 on was written after.
 *
 * It drives TC1.  TC0, the vendor's tick, keeps running, and arm() checks
 * that TC0's bits in the shared TCCNR did not move.  The count rate and the
 * shift are derived at init and never compiled in: under Linux the divider is
 * 1000 and not 14 (MEASURED seating 11, SPEC.md REG-11, CLK-22).  Since 4.0
 * the tick is handed over at boot by a sequencer of the same steps the verbs
 * take, and RLXFW-TA<n> marks each stage on the wire.
 *
 * WHY RATING 0.  The CLOCKSOURCE's rating is 0, strictly below
 * clocksource_jiffies' 1, so it cannot become the system time base by
 * accident.  The clockevent's rating is a different field on a different
 * structure: see THE CLOCKEVENT.
 *
 * THE CLOCKEVENT.  TC1 HAS ONE RELOAD REGISTER AND THE TWO JOBS WANT
 * DIFFERENT VALUES: the clocksource wants a power-of-two period, and a
 * 100 Hz clockevent wants 2,000 counts.  So `mode cs` and `mode ce` choose
 * one, and arm() writes a different TC1DATA under each.  A software-extended
 * clocksource is refuted on this die rather than skipped: the vendor's tick
 * ack is a read-modify-write on write-1-to-clear bits, so a pending TC1IP
 * lives at most one tick (SPEC.md IRQ-09).
 *
 * THE INTERRUPT PATH.  `reqirq` refuses unless this driver has ITSELF watched
 * `ackip` take TC1IP from 1 to 0 (I3): the ICTL chip masks without acking and
 * handle_level_irq() unmasks after the handler, so a handler that cannot
 * clear TC1IP re-triggers at once.  The handler clears TC1IP, reads it back,
 * and on a bit still set calls disable_irq_nosync(), so a storm becomes one
 * line in /proc.
 *
 * The driver page: docs/drivers/timer.md; the reasoning and every reading:
 * notes/timer-driver.md.  Each version's changes and the reading that forced
 * them, why TC1 and not TC0, the hazards of arming and how they were
 * answered, the handover, the pre-check and what neither guard can do: the
 * head this file carried until 2026-10-18, verbatim in
 * docs/drivers/timer-history.md.
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
/* R5-3b-2.  rlxfw_markx() goes straight to prom_putchar: no console, no
 * log buffer, no lock.  It is the only way this configuration can report
 * a boot-time step, because CONFIG_PRINTK is not set and printk() is a
 * 20-byte stub (arch/rlx/kernel/rlxfw_mark.c carries that measurement).
 * A boot-arm that wedges must leave a line on the wire saying where. */
#include <linux/rlxfw-mark.h>
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
 * NEW: R5-3a: the four routing registers, READ ONLY, in the same block.
 *
 * `IRR0`-`IRR3` are eight 4-bit destination-select fields each, written
 * unconditionally by `bsp_irq_init()` on every boot (READ arch/rlx/bsp/irq.c:
 * 222-225).  SPEC.md: `REG-32`, `REG-03`, `REG-04`, `REG-33`.  THREE OF THE
 * FOUR HAVE NEVER BEEN READ AT ALL, and `IRR1`'s one reading is at the loader
 * prompt (`0x30050004`), which `bsp_irq_init` overwrites -- so under Linux
 * every nibble should differ.
 *
 * NOTE: They are here because there is no other way to read them on this board.
 * MEASURED 2026-09-04, config/rlxfw-initramfs.tsv: this image carries ELEVEN
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
 * mask for it -- MEASURED REG-01, clear at the loader prompt. */
#define RTL819X_INTC_TC0	(1u << 8)
#define RTL819X_INTC_TC1	(1u << 9)

/*
 * TC1's Linux IRQ number.  READ arch/rlx/bsp/bspchip.h:102,
 * `BSP_TC1_IRQ (BSP_IRQ_ICTL_BASE + 9)` with `BSP_IRQ_ICTL_BASE` = 16, so 25.
 * docs/interrupt-map.md 1 and 3.1.
 *
 * NOTE: Written as a literal rather than by including bspchip.h, for the same
 * reason every register address in this file is a literal: that header is the
 * BSP's private one, it is not on a driver's include path, and depending on it
 * would put a vendor header in the include graph of a file whose whole claim
 * is that it did not read one.  The derivation is in the comment; the check
 * that it is still true is BUILD_BUG_ON below and the /proc `irq_num` line.
 *
 * CAUTION: TC0 is IRQ 13 and is NOT on this domain -- it is a LOPI line, masked in
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
 * The rate TC0CNT and TC1CNT increment at.  SPEC.md CLK-17, MEASURED: derived from
 * two measured quantities and nothing else -- CLK-04's 100.0018 Hz tick and
 * REG-05's TC0DATA = 142,858.  It needs no divisor semantics and no 200 MHz
 * figure.
 *
 * THAT IT IS ALSO TC1's RATE IS READ, NOT MEASURED.  D 8.2 says one Clock Division
 * Base Register "defines the base clock for counting" for the block, so both
 * timers and the watchdog divide the same clock.  REFUTED BY: a measured TC1
 * rate outside CLK-17 +- 50 ppm on the silicon, which would be a finding
 * about the SoC rather than about this driver.  R5-2 is that measurement.
 */
#define RTL819X_TC_HZ		14286057

/*
 * NOTE: AND IT IS THE LOADER'S RATE, NOT LINUX'S.  MEASURED seating 11 (TM-1), the
 * first reading of this block under a kernel: CDBR is 0x03E80000 -- divisor
 * 1000 -- where the loader left 0x000E0000, divisor 14; and TC0DATA is
 * 0x00007D00 (reload 2,000) where the loader left 0x0022E0A0 (142,858).
 * arch/rlx/bsp/timer.c is what rewrites both (READ 2026-09-04, R5-10).  So the
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
 *       Needs the 200 MHz figure, which is READ (arch/rlx/bsp/bspchip.h
 *       BSP_SYS_CLK_RATE) and MEASURED to 200.0049 MHz +- 7 ppm (SPEC.md CLK-02).
 *
 * They are different quantities that must agree: the first descends from the
 * kernel's own tick, the second from the crystal.  On this part both give
 * 200,000 (MEASURED TM-1: 2000 * 100, and 200000000 / 1000), and hz_agree in /proc
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
 * NEW: R5-3a: the period is settable, while disarmed, by `period <bits>`.
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
 * The shift search.  2.6.30 has NO clocks_calc_mult_shift() -- READ
 * include/linux/clocksource.h, which carries clocksource_hz2mult() and
 * nothing else -- so this driver does the search itself.
 *
 * NOTE: It cannot be a constant once the rate is derived, and the failure is
 * SILENT.  clocksource_hz2mult returns u32 by a cast, so an oversized value
 * is truncated with no diagnostic.  MEASURED at the desk, 2026-09-04:
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
 *   * mask * mult must fit s63, because READ cyc2ns() is
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
 * NEW: R5-3b.  The clockevent's ratings.
 *
 * READ arch/rlx/kernel/rlx-cevt.c:234, `cd->rating = 100`, and READ
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
 * TOL_PERMILLE is 10, i.e. 1 %.  MEASURED seating 12 (SPEC.md IRQ-08): the measured
 * delivery rate was within 0.0199 % and 0.0994 % of the programmed rate at
 * two periods 16x apart, and 0.0206 % with the NIC up and four pings in
 * flight.  1 % is a hundred times the worst of those, so this refuses on a
 * fault and not on jitter -- which is what a gate before an irreversible step
 * has to do to be worth passing.
 */
#define RTL819X_CE_MIN_J	300
#define RTL819X_CE_TOL_PERMILLE	10

/*
 * R5-3b-2, arming at boot.
 *
 * RTL819X_BOOT_ACK_TRIES / _US: the ackip retry, and the two numbers come
 * from a measurement rather than from taste.  IRQ-09 (MEASURED seating 12): the
 * vendor's tick handler does REG32(BSP_TCIR) |= BSP_TC0IP a hundred times
 * a second, and every IP bit in that register is write-1-to-clear, so a
 * TC1IP belonging to this driver survives at most one 10 ms tick.  At an
 * 8-bit period TC1 wraps every 256/200,000 s = 1.28 ms, so the bit is back
 * within 1.28 ms of any clear -- MEASURED seating 12 put the duty cycle at
 * 87.20 %.  Sampling every 500 us for 64 tries covers 32 ms, which is more
 * than three of the vendor's own tick periods.
 *
 * NOTE: The loop exists because ONE ackip is a coin toss and a coin toss in a
 * boot path is a driver that arms on some boots and not others -- which is
 * indistinguishable, from a capture, from hardware that is intermittent.
 *
 * RTL819X_BOOT_WAIT_MAX_J: a ceiling on the pre-check wait, so a jiffies
 * counter that has stopped cannot hang the boot in a loop that is waiting
 * for it to advance.  The wait is expected to be SHORT or zero: the early
 * half runs at arch_initcall and the late half at late_initcall, and the
 * drivers in between are what the 300 jiffies are spent on.
 */
#define RTL819X_BOOT_ACK_TRIES	64
#define RTL819X_BOOT_ACK_US	500
#define RTL819X_BOOT_WAIT_MAX_J	(RTL819X_CE_MIN_J + 200)

/*
 * 4.1, and this constant exists because of a measurement rather than a
 * worry.  MEASURED seating 14, K1 (cold boot) and K2 (warm boot, byte-identical
 * fields): ce_check_dj = 585, ce_check_dc = 574.  Over the span from
 * reqirq at arch_initcall to the pre-check at late_initcall -- which is
 * exactly the vendor's NIC driver initialisation -- TC1 delivered 574 of
 * the 585 interrupts a 100 Hz source owes.  ELEVEN SHORT, 1.88 %, against
 * a 1 % tolerance, and the handover was refused with -ETIME on both boots.
 *
 * OK: The same boot at the shell, K1-P -> K1-Q over 14,385 jiffies:
 * Djiffies 14,385 against Dirq_count 14,384 -- ONE short, 0.0070 % -- and
 * the tick was still the vendor's there, so those two numbers are
 * independent sources and not one identity written twice.
 *
 * So: the loss is confined to the driver-init phase, and the window the
 * pre-check judges on has to be taken in the state the tick will run in.
 * The late half re-bases and waits there.  Three attempts, because a
 * window that lands on a level-7 initcall doing something long should
 * cost 3 s and not the boot.
 */
#define RTL819X_BOOT_CE_TRIES	3

/* The stages, as printed by RLXFW-TA<n> and read back from /proc.  They
 * are numbered rather than named because the mark is the primary reader
 * and it has eight hex digits, not a string. */
#define RTL819X_BOOT_S_NONE	0	/* the sequencer never ran */
#define RTL819X_BOOT_S_ARM8	1	/* period 8, arm, armirq   -- I1, I2 */
#define RTL819X_BOOT_S_ACK	2	/* the ackip retry          -- I3     */
#define RTL819X_BOOT_S_ARMCE	3	/* disarm, mode ce, arm, armirq     */
#define RTL819X_BOOT_S_REQ	4	/* reqirq                   -- I4     */
#define RTL819X_BOOT_S_WAIT	6	/* the rest of the pre-check window  */
#define RTL819X_BOOT_S_PROBE	7	/* cevtprobe, the negative control   */
#define RTL819X_BOOT_S_CEVT	8	/* cevt -- THE HANDOVER              */
#define RTL819X_BOOT_S_DONE	9

/*
 * NEW: `cereload <counts>` -- the bounds on a DELIBERATELY WRONG tick period.
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
 * NOTE: It may only be used while ARMED and in clockevent mode, and `cevt`
 * REFUSES while the live reload differs from the one HZ implies.  So the
 * sequence is fixed by the code: hand the tick over at the right rate, then
 * make it wrong on purpose, then put it back.  A card cannot reorder that.
 */
#define RTL819X_CE_RELOAD_MIN	500
#define RTL819X_CE_RELOAD_MAX	20000

#define RTL819X_MODE_CS		0	/* clocksource: power-of-two period */
#define RTL819X_MODE_CE		1	/* clockevent:  hz_used / HZ period */

#define RTL819X_PROC_NAME	"rtl819x-timer"
#define RTL819X_TC_VERSION	"4.1"

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

/* The software extension of the counter.  UPDATE: R5-3a: advanced by a KERNEL
 * TIMER, not by whoever happens to read /proc.
 *
 * MEASURED TM-5c, seating 11: 462 s with nobody reading, and tc1_ext sat 92,362,366
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

/* NEW: R5-3b.  The clockevent. */
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

/* R5-3b-2.  What the boot sequencer did, for the shell to read after the
 * fact.  Every one of these is also on the wire as an RLXFW-TA<n> line;
 * the duplication is deliberate, because the wire is the only reader that
 * still works when the boot does not reach a shell. */
static int rtl819x_boot_stage;		/* the last stage ENTERED */
static int rtl819x_boot_rc;		/* that stage's return, 0 while ok */
static int rtl819x_boot_done;		/* the handover completed at boot */
static u32 rtl819x_boot_ack_tries;	/* ackip calls until 1 -> 0 was seen */
static u32 rtl819x_boot_wait_j;		/* jiffies spent waiting at S6 */
static u32 rtl819x_boot_j_early;	/* jiffies at arch_initcall */
static u32 rtl819x_boot_j_late;		/* jiffies at late_initcall */
/* 4.1.  The driver-init phase, kept as a reading instead of being the
 * reason the handover fails.  Every boot now reports how many TC1
 * interrupts the vendor's own initialisation costs. */
static u32 rtl819x_boot_pre_dj;		/* jiffies  reqirq -> late_initcall */
static u32 rtl819x_boot_pre_dc;		/* TC1 IRQs over the same span */
static u32 rtl819x_boot_ce_tries;	/* re-based windows the pre-check took */
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
 * UPDATE: R5-3b: the mask is applied in clocksource mode ONLY.
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
 * NEW: R5-3b.  ONE owner, because two had already disagreed: version 2.0
 * computed this inside arm() alone, so `period 8` on a disarmed driver moved
 * mask_bits and left period_jiffies describing the previous period -- MEASURED
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
 * NOTE: TWO gap figures, and keeping both is the point.  `d` is already reduced
 * mod the period, so an interval of one full period plus delta is
 * indistinguishable from delta -- MEASURED TM-5b2: a real gap of 140,693,532 counts
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
 * CAUTION: This timer is driven by the vendor's TC0 tick, so it shares TC0's fate:
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
	/* NEW: R5-3b.  -ERANGE: clockevent mode was asked for on a kernel whose
	 * tick rate does not divide the counter's rate, so no integer reload
	 * gives HZ exactly.  MEASURED on this build it does -- 200,000 / 100 = 2,000
	 * -- and the refusal exists so that a config change makes the driver
	 * say so instead of running the system clock at the wrong rate. */
	if (rtl819x_mode == RTL819X_MODE_CE && !rtl819x_ce_reload_exact) {
		ret = -ERANGE;
		goto out;
	}
	/* UPDATE: R5-3a: the refusal now asks WHOSE bit it is.  Version 1.0 read a
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
	/* UPDATE: R5-3b: `& mask` is wrong in clockevent mode for the reason given at
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

	/* NEW: R5-3b.  In clockevent mode there is no software extension and no
	 * kernel timer driving one: rtl819x_ext_advance()'s arithmetic is the
	 * masked kind, the period is not a power of two, and the ISR runs once
	 * per period anyway -- so ce_cycles is exact where an extension would be
	 * approximate.  Every tc1_ext_* line in /proc therefore reads 0 in this
	 * mode, and `mode=ce` on the line above it is why. */
	/* UPDATE: R5-3b: both derived quantities come from one function, and it is
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
			/* NOTE: R5-3a, found at the desk and not on the device:
			 * version 1.0 cleared `armed` here and left TC1
			 * COUNTING.  The hardware stayed enabled, `disarm`
			 * then returned -EINVAL because `armed` was 0, and
			 * nothing in the driver could stop it -- an
			 * unreachable state created by the one path that is
			 * supposed to be the safe failure.  It has never been
			 * reached (clocksource_register returned 0 on the
			 * silicon, MEASURED seating 11), which is why a reading
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
 * NOTE: The zeros are the load-bearing part.  Both IP bits are write-1-to-clear
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
 * NOTE: NO LOCK HERE, and that is a reading rather than an oversight.
 *
 * READ kernel/time/clockevents.c and tick-common.c: every call reaches this
 * function from clockevents_exchange_device() (inside local_irq_save) or from
 * tick_setup_periodic() (inside tick_check_new_device's
 * spin_lock_irqsave(&tick_device_lock))  -- interrupts are off at both.  MEASURED
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
		/* NOTE: SHUTDOWN deliberately does NOT stop TC1.
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
 * READ kernel/time/tick-common.c tick_setup_periodic(): a device WITHOUT
 * CLOCK_EVT_FEAT_PERIODIC is driven by `for (;;) { if
 * (!clockevents_program_event(...)) return; next += tick_period; }` -- with
 * interrupts disabled.  A set_next_event that always fails makes that loop
 * spin forever and the board is gone with no console.  Returning 0 makes it
 * return after one pass.  Both outcomes are wrong; one of them can be read
 * afterwards, because ce_next_calls is in /proc and must be 0.
 *
 * The other two callers -- tick_program_event() and the broadcast path -- are
 * behind CONFIG_TICK_ONESHOT and CONFIG_GENERIC_CLOCKEVENTS_BROADCAST, MEASURED
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
 *   -EBUSY   already registered.  NOTE: This is the only thing standing between
 *            a second `cevt` and a corrupted list: MEASURED on this build,
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
		/* NOTE: -ERANGE: `cereload` has already made the period deliberately
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

	/* NOTE: Marked registered BEFORE the call and inside the same critical
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
 * seconds.  CAUTION: That ignorance is stated rather than assumed away -- a cell
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
 * READ kernel/irq/chip.c handle_level_irq(): mask_ack_irq() runs first (the
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
		/* NEW: R5-3b.  TC1IP clear on entry is counted SEPARATELY from
		 * "not ours", because SPEC.md IRQ-09 gives it a second cause
		 * that has nothing to do with ownership: the vendor's
		 * bsp_timer_ack() erases every pending bit in TCIR a hundred
		 * times a second, and it can erase ours between the latch and
		 * this read.  irq_preacked is that rate, and MEASURED seating 12 it
		 * was 0 in 119,818 deliveries. */
		rtl819x_irq_preacked++;

		/* NOTE: In clockevent mode this is NOT a reason to return early,
		 * and that is the design constraint IRQ-09 imposes on this
		 * step.  READ arch/rlx/bsp/irq.c bsp_ictl_irq_dispatch(): line 25
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
			/* Not ours.  READ kernel/irq/spurious.c
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

	/* NEW: R5-3b.  The tick, outside this driver's lock on purpose.
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
	 * NOTE: R5-3b: once the tick is ours this call STOPS THE SYSTEM CLOCK, and
	 * it is kept anyway.  A storm on line 25 with the tick on it is a
	 * livelocked board that also stops the clock, and it stops the vendor's
	 * TC0 handler too -- which is what pets the hardware watchdog
	 * (CONFIG_RTL_WTDOG=y, READ arch/rlx/kernel/rlx-cevt.c:159).  A stopped
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
 * unmask that sets GIMR bit 9 -- so the mask is moved BY ITS OWNER (READ
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
		/* NEW: R5-3b.  The pre-check's window opens here and nowhere else.
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
	 * (READ kernel/irq/manage.c: __free_irq opens with WARN(in_interrupt())).
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
 * UPDATE: R5-3a: disarm unwinds EVERYTHING this driver created, in reverse order.
 *
 * Version 1.0 had two writes to undo and undid both -- MEASURED seating 11, twice,
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
	/* NOTE: R5-3b.  -EBUSY once EITHER clock_event_device is registered, and
	 * this refusal is the honest form of "the handover is one-way".
	 *
	 * READ kernel/time/clockevents.c: there is no unregister.  A registered
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
	/* NEW: R5-3b.  Snapshotted with everything else, for the same reason:
	 * a takeover reading and the counter reading that explains it have to
	 * describe one instant. */
	int ce_mode_, ce_reg, ce_preg, ce_live_, ce_lm, ce_plm;
	u32 ce_mc, ce_pmc, ce_nc, ce_bm, ce_hb, preacked, ce_dc, ce_dj, ce_rat;
	u64 ce_cyc;
	unsigned long ce_h;

	/* NOTE: `Status` is read BEFORE the lock, and that is not tidiness.
	 * spin_lock_irqsave() disables interrupts, so a Status read inside it
	 * would report IEc = 0 ALWAYS -- a constant dressed as a measurement.
	 * IM2 and BEV are unaffected by the lock, so only one of the three
	 * bits needed care and all three are taken where all three are true.
	 *
	 * CAUTION: `ST0_IEC` and not `ST0_IE`: READ arch/rlx/include/asm/rlxregs.h,
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
	/* UPDATE: R5-3b: not in clockevent mode.  rtl819x_ext_advance() reduces its
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
	 * UPDATE: R5-3a: `hz_assumed` is kept AND is no longer what the clocksource
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
	/* UPDATE: R5-3b: the HARDWARE period, which in clockevent mode is
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
	/* UPDATE: R5-3a: decided in JIFFIES, which this driver never reduces, so it
	 * cannot alias.  The old test was `gap < mask/2` on a gap already
	 * reduced mod the period -- MEASURED TM-5b2, a real 140,693,532-count gap
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

	/* NEW: R5-3a.  TC1IE is the gate seating 11 left clear without knowing
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

	/* NEW: R5-3a.  The routing, and the CPU-side gate.  Read only, and free:
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

	/* NEW: R5-3b.  Appended at the end and not interleaved, so a capture from
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
	 * 2 PERIODIC, 3 ONESHOT, 4 RESUME (READ include/linux/clockchips.h).
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
	/* OK: The takeover's second and independent witness.  Before it,
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

	/* R5-3b-2.  What the boot sequencer did.  These are read outside the
	 * lock on purpose: they are written once each, by initcalls, before
	 * any process can open this file, so there is nothing to serialise
	 * against and taking the lock would suggest otherwise. */
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_stage=%d\n",
			 rtl819x_boot_stage);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_rc=%d\n",
			 rtl819x_boot_rc);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_done=%d\n",
			 rtl819x_boot_done);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_ack_tries=%u\n",
			 rtl819x_boot_ack_tries);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_wait_j=%u\n",
			 rtl819x_boot_wait_j);
	/* 4.1.  The driver-init phase, as its own reading. */
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_pre_dj=%u\n",
			 rtl819x_boot_pre_dj);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_pre_dc=%u\n",
			 rtl819x_boot_pre_dc);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_ce_tries=%u\n",
			 rtl819x_boot_ce_tries);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_j_early=%u\n",
			 rtl819x_boot_j_early);
	len += scnprintf(page + len, PAGE_SIZE - len, "boot_j_late=%u\n",
			 rtl819x_boot_j_late);

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
 * CAUTION: It refuses while armed.  The alternative -- re-loading TC1DATA under a
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
	/* NEW: R5-3b: and the derived pair follows it immediately, so that a
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
	/* NEW: R5-3a.  ONE VERB PER GATE, and that is the design rather than an
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
	/* NEW: R5-3b.  `cevtprobe` before `cevt` is not an ordering this code
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
 * R5-3b-2: arming at boot.
 *
 * WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT.
 * It is a sequencer.  Every hardware step below is the same function the
 * /proc verb calls, in the same order the card ran by hand on 2026-09-06
 * (bench/2026-09-06, cells P2-1a..P2-5 and P3-1a..P3-5, three independent
 * cold boots).  Nothing here re-implements arm(), ackip() or the
 * registration, because then R5-3b-1's evidence would not carry: a second
 * implementation of a step is a second thing to be wrong about, and this step
 * is supposed to change WHEN the handover happens and nothing else.
 *
 * THE ONLY NEW LOGIC IS THREE THINGS:
 *   1. the ackip retry (see RTL819X_BOOT_ACK_TRIES for the measurement);
 *   2. the wait for the pre-check window, which by hand was `sleep 8`;
 *   3. the unwind, which by hand was the operator not typing the next line.
 *
 * WHY IT IS SPLIT ACROSS TWO INITCALL LEVELS.
 * rtl819x_ce_precheck() needs RTL819X_CE_MIN_J = 300 jiffies = 3 s of
 * delivered interrupts before it will let the tick be handed over.  Spending
 * that as a busy wait inside one initcall would add 3 s to every boot for
 * nothing.  Split, the window is spent on the drivers that run between
 * arch_initcall and late_initcall, and the late half waits only for whatever
 * is LEFT.  RLXFW-TA6 prints that remainder, so how long this board takes
 * between the two levels becomes a reading rather than an assumption.
 *
 * WHY late_initcall AND NOT A WORKQUEUE.
 * READ init/main.c: do_initcalls() runs every level to completion inside
 * kernel_init, and only then does init_post() exec /sbin/init.  So a
 * late_initcall is the last place that is still guaranteed to be BEFORE
 * userspace -- which is what this step's DoD says.  A workqueue would race
 * the first process.
 *
 * NOTE: WHY THERE IS NO RUNTIME SWITCH, WHICH WAS CONSIDERED AND REJECTED.
 * A magic word left in DRAM by the loader would have let one image both arm
 * and not arm.  MEM-17 refutes it: MEASURED 2026-08-31, this board's DRAM retains a
 * previous power cycle's contents, so a stale word would arm a boot that
 * asked not to be armed -- and a switch that can be set by the previous
 * experiment is not a switch.  The recovery path is cheaper anyway: nothing
 * of this is in flash, the image is TFTP'd to RAM on every cycle, so a wedged
 * boot costs exactly one power cycle and the previous image is the fallback.
 *
 * NOTE: WHAT A FAILURE COSTS, BY STAGE.
 * S1..S7 are soft: the sequencer unwinds with disarm(), the vendor keeps the
 * tick, the board boots, and /proc plus the marks say which stage and which
 * errno.  S8 is the only hard one -- past clockevents_register_device() the
 * tick is this driver's and a broken ISR stops jiffies with nothing able to
 * restart it.  That is the same one-way door rtl819x_tc1_disarm() documents,
 * arrived at from a different direction.
 * ------------------------------------------------------------------------ */

static int __init rtl819x_boot_arm_early(void)
{
	int rc, i;

	rtl819x_boot_j_early = (u32)get_jiffies_64();
	rlxfw_markx("TA0", rtl819x_boot_j_early);

	/* S1 -- I1 and I2 at an 8-bit period.  The period is not a preference:
	 * it is the one seating 13 proved ackip against, and RTL819X_BOOT_ACK_*
	 * carries why a short period is what makes the proof possible at all. */
	rtl819x_boot_stage = RTL819X_BOOT_S_ARM8;
	rc = rtl819x_tc1_set_period("8");
	if (!rc)
		rc = rtl819x_tc1_arm();
	if (!rc)
		rc = rtl819x_tc1_armirq();
	rlxfw_markx("TA1", (u32)rc);
	if (rc)
		goto fail;

	/* S2 -- I3.  ack_proven is what rtl819x_tc1_cevt_register() refuses on
	 * with -EPERM, and it is set only on a 1 -> 0 this driver watched. */
	rtl819x_boot_stage = RTL819X_BOOT_S_ACK;
	for (i = 0; i < RTL819X_BOOT_ACK_TRIES && !rtl819x_ack_proven; i++) {
		udelay(RTL819X_BOOT_ACK_US);
		rtl819x_tc1_ackip();
	}
	rtl819x_boot_ack_tries = (u32)i;
	/* 0xFFFFFFFF and not the try count, on failure: a count that reached the
	 * ceiling and a count that succeeded on the last try print the same
	 * number, and those are opposite outcomes. */
	rlxfw_markx("TA2", rtl819x_ack_proven ? (u32)i : 0xFFFFFFFFu);
	if (!rtl819x_ack_proven) {
		rc = -EPERM;
		goto fail;
	}

	/* S3 -- back to the clockevent period.  disarm() first because
	 * set_mode_verb() refuses while armed, and set_period()/mode changes
	 * under a running counter are what that refusal exists to prevent. */
	rtl819x_boot_stage = RTL819X_BOOT_S_ARMCE;
	rc = rtl819x_tc1_disarm();
	if (!rc)
		rc = rtl819x_tc1_set_mode_verb("ce");
	if (!rc)
		rc = rtl819x_tc1_arm();
	if (!rc)
		rc = rtl819x_tc1_armirq();
	rlxfw_markx("TA3", (u32)rc);
	if (rc)
		goto fail;

	/* S4 -- I4.  This is also where ce_base_j / ce_base_irq are taken, so
	 * the pre-check window starts counting from here. */
	rtl819x_boot_stage = RTL819X_BOOT_S_REQ;
	rc = rtl819x_tc1_reqirq();
	rlxfw_markx("TA4", (u32)rc);
	if (rc)
		goto fail;

	rtl819x_boot_rc = 0;
	return 0;

fail:
	rtl819x_boot_rc = rc;
	/* Leave the block as it was found.  disarm() clears TC1IE, frees the
	 * IRQ if one was requested, stops TC1 and clears a latched TC1IP; its
	 * own return is discarded because there is nothing further to do with
	 * it and rtl819x_boot_rc already holds the failure that matters. */
	rtl819x_tc1_disarm();
	return 0;
}

/*
 * The late half.  Returns 0 always: an initcall that returns non-zero prints
 * nothing in this configuration and changes nothing, so the return value is
 * not a channel.  The marks and /proc are.
 */
static int __init rtl819x_boot_arm_late(void)
{
	unsigned long flags;
	u64 j0;
	int rc, i;

	rtl819x_boot_j_late = (u32)get_jiffies_64();
	rlxfw_markx("TA5", rtl819x_boot_j_late);

	if (rtl819x_boot_stage != RTL819X_BOOT_S_REQ || rtl819x_boot_rc) {
		/* The early half did not finish.  TA1..TA4 say which stage and
		 * with what errno; this line says the late half saw that and
		 * declined, rather than that it never ran. */
		rlxfw_markx("TA6", 0xFFFFFFFFu);
		return 0;
	}

	/*
	 * S6.  UPDATE: 4.1: the window is taken HERE, and the old one is kept as a
	 * reading.  See RTL819X_BOOT_CE_TRIES for the two measurements that
	 * forced this; in one line, the span this function used to judge on is
	 * the vendor's NIC initialisation and it costs 11 of 585 interrupts,
	 * while the steady state costs 1 of 14,385.
	 *
	 * TA6 is the SHORTFALL over the driver-init phase and no longer the
	 * wait, because the wait is now ~300 on every boot and says nothing,
	 * while the shortfall is a different number every board could give.
	 * The wait and the attempt count are in /proc, and a hang inside the
	 * loop is still located by TA6 printing and TA7 not.
	 */
	rtl819x_boot_stage = RTL819X_BOOT_S_WAIT;
	rtl819x_boot_pre_dj = (u32)(get_jiffies_64() - rtl819x_ce_base_j);
	rtl819x_boot_pre_dc = rtl819x_irq_count - rtl819x_ce_base_irq;
	rlxfw_markx("TA6", rtl819x_boot_pre_dj - rtl819x_boot_pre_dc);

	j0 = get_jiffies_64();
	for (i = 0; i < RTL819X_BOOT_CE_TRIES; i++) {
		u64 w0;

		rtl819x_boot_ce_tries = (u32)(i + 1);

		/* Re-base under the lock: rtl819x_irq_count is the ISR's and the
		 * two fields have to be taken as one pair, or the first window
		 * starts with a count that is already one interrupt stale. */
		spin_lock_irqsave(&rtl819x_tc_lock, flags);
		rtl819x_ce_base_j = get_jiffies_64();
		rtl819x_ce_base_irq = rtl819x_irq_count;
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

		/* The ceiling is not decoration: this loop's exit condition is
		 * jiffies advancing, and if the thing that advances jiffies has
		 * stopped, an uncapped loop here would hang the boot in the one
		 * place with no way to say so. */
		w0 = get_jiffies_64();
		while (get_jiffies_64() - rtl819x_ce_base_j < RTL819X_CE_MIN_J) {
			if (get_jiffies_64() - w0 > RTL819X_BOOT_WAIT_MAX_J)
				break;
			msleep(20);
		}

		/* NOTE: The verdict is NOT marked here, and that is deliberate.
		 * rtl819x_tc1_cevt_register() runs this same pre-check under its
		 * own lock, so a failure surfaces as TA7's errno -- one mark,
		 * one meaning.  A mark here would print -ETIME twice for one
		 * refusal and read as two. */
		if (rtl819x_ce_precheck() == 0)
			break;
	}
	rtl819x_boot_wait_j = (u32)(get_jiffies_64() - j0);

	/* S7 -- the negative control, and it is not optional.  A rating of 300
	 * winning means nothing unless a rating of 99 on the same hardware,
	 * through the same registration call, on the same boot, loses.  MEASURED
	 * seating 13: ce_probe_registered=1 with ce_probe_mode_calls=0, three
	 * times.  If that stops being true this line is where it shows. */
	rtl819x_boot_stage = RTL819X_BOOT_S_PROBE;
	rc = rtl819x_tc1_cevt_register(1);
	rlxfw_markx("TA7", (u32)rc);
	if (rc) {
		rtl819x_boot_rc = rc;
		return 0;
	}

	/* S8 -- the handover.  Past the call inside this, the system tick is
	 * TC1's interrupt.  There is no way back in this boot: clockevents.c
	 * has no unregister and tick_cpu_device is static per-cpu. */
	rtl819x_boot_stage = RTL819X_BOOT_S_CEVT;
	rc = rtl819x_tc1_cevt_register(0);
	rlxfw_markx("TA8", (u32)rc);
	if (rc) {
		rtl819x_boot_rc = rc;
		return 0;
	}

	rtl819x_boot_stage = RTL819X_BOOT_S_DONE;
	rtl819x_boot_done = 1;
	/* The last mark is not "done": it is the two flags the tick core owns,
	 * read back.  bit1 = ce_registered (this driver set it), bit0 = ce_live
	 * (only tick_setup_periodic -> set_mode(PERIODIC) sets it).  A 2 here
	 * means the registration returned and the core never called back, which
	 * is exactly the failure a bare "done" would hide. */
	rlxfw_markx("TA9", ((u32)rtl819x_ce_registered << 1)
			   | (u32)(rtl819x_ce_live ? 1 : 0));
	return 0;
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
	 * 8 CPU + 8 LOPI + 32 ICTL (READ arch/rlx/include/asm/mach-generic/irq.h),
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
	 * counts" is MEASURED on this die, while hz_cdbr additionally needs the
	 * 200 MHz figure to be right.  hz_cdbr is the cross-check.
	 *
	 * NOTE: If TC0DATA reads 0 -- a block this driver's model does not
	 * describe -- the fallback is the compiled constant, and hz_used says
	 * which was taken.  Falling back SILENTLY to a rate 71.43x wrong is
	 * exactly what version 1.0 did without knowing it.
	 */
	rtl819x_hz_used = rtl819x_hz_tick ? rtl819x_hz_tick : RTL819X_TC_HZ;

	/* mult here and not in arm(): the /proc dump prints it, and a dump
	 * whose mult reads 0 until somebody arms would invite the reader to
	 * think the number is broken rather than unset.  NTP adjusts mult on
	 * the selected clocksource only, and at rating 0 this is never it. */
	/* NOTE: The search runs against the LARGEST mask this driver can be set
	 * to, not the current one.  `period` can shrink the mask later, and a
	 * smaller mask only relaxes the mask*mult bound -- so a shift chosen
	 * at the maximum stays valid for every period, and one chosen at the
	 * current period would not survive being widened again. */
	rtl819x_shift_used = rtl819x_pick_shift(rtl819x_hz_used,
						RTL819X_TC1_MASK, &mult);
	rtl819x_tc1_clocksource.shift = rtl819x_shift_used;
	rtl819x_tc1_clocksource.mult = mult;
	rtl819x_tc1_clocksource.mask = CLOCKSOURCE_MASK(rtl819x_period_bits);

	/* NEW: R5-3b.  The clockevent's period is the vendor's own reload: MEASURED
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

	/* NOTE: AFTER the /proc entry and not before it.  If arming fails, the
	 * only thing that can say why is this file, and a sequencer that ran
	 * before its own reporting channel existed would have to be debugged
	 * from the marks alone.  A create_proc_entry() that failed returns
	 * above without arming at all, which is the right order for the same
	 * reason. */
	rtl819x_boot_arm_early();
	return 0;
}
arch_initcall(rtl819x_timer_init);

/* The late half is its own initcall rather than a call from the early one:
 * the 300-jiffy pre-check window is supposed to be spent on the drivers in
 * between, and a call would spend it as a busy wait instead. */
late_initcall(rtl819x_boot_arm_late);
