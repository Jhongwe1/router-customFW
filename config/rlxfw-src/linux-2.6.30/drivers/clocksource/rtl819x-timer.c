/*
 * rtl819x-timer -- a Linux clocksource on the RTL8196E's Timer/Counter 1.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-1, 2026-09-03.  It is staged into
 * drivers/clocksource/ by tools/rlxfw-marks.py from config/rlxfw-src/;
 * config/rlxfw-marks.tsv carries the one Kbuild line that links it.
 *
 * WRITTEN BLIND, AND THAT WORD HAS A LEDGER.
 * docs/blind-write-ledger.md 4.3 is the frozen record of what this
 * repository had read of anyone else's timer before this file existed:
 * one string literal of the vendor's (`"rlx timer"`, arch/rlx/kernel/
 * rlx-cevt.c:139,226, taken for an arch/rlx-vs-arch/mips proof), the weak
 * generic kernel/sched_clock.c:39, and arch/rlx/kernel/rlx-time.c with zero
 * citations.  Neither vendor file was opened to write this one.  Every
 * number below comes from SPEC.md -- this die's own readings -- or from the
 * RTL8196E datasheet, which is the specification and not an implementation.
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
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/clocksource.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/jiffies.h>
#include <linux/time.h>
#include <linux/delay.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/page.h>
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

/* D Table 14/15: the two timers have SEPARATE bits at the global controller,
 * which is what bounds this driver's second hazard.  A TC1 timeout raises
 * GISR bit 9, not the bit 8 the vendor's tick uses, and GIMR bit 9 is the
 * mask for it -- 量 REG-01, clear at the loader prompt. */
#define RTL819X_INTC_TC0	(1u << 8)
#define RTL819X_INTC_TC1	(1u << 9)

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
#define RTL819X_TC_VERSION	"1.0"

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

/* The software extension of the 27-bit counter, advanced on every /proc read
 * and on arm.  It is only valid across reads spaced closer than the period,
 * which is why the largest observed gap is reported beside it. */
static u64 rtl819x_ext_cycles;
static u32 rtl819x_ext_last;
static u32 rtl819x_ext_gap_max;
static u32 rtl819x_ext_reads;

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

static inline u32 rtl819x_tc1_cycles(void)
{
	return (rtl819x_tc_rd(RTL819X_TC1CNT) >> RTL819X_TC_VALUE_SHIFT)
		& RTL819X_TC1_MASK;
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

/* Advance the software extension.  Caller holds rtl819x_tc_lock. */
static void rtl819x_ext_advance(u32 now)
{
	u32 d = (now - rtl819x_ext_last) & RTL819X_TC1_MASK;

	rtl819x_ext_cycles += d;
	if (d > rtl819x_ext_gap_max)
		rtl819x_ext_gap_max = d;
	rtl819x_ext_last = now;
	rtl819x_ext_reads++;
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
	if (rtl819x_intc_rd(RTL819X_GIMR) & RTL819X_INTC_TC1) {
		ret = -EPERM;
		goto out;
	}

	/* The two writes, in this order: the period has to be in place before
	 * the counter is allowed to run, or the first pass is against
	 * whatever TC1DATA held. */
	rtl819x_tc_wr(RTL819X_TC1DATA,
		      RTL819X_TC1_PERIOD << RTL819X_TC_VALUE_SHIFT);
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
	rtl819x_tc1_delta_at_arm = (after - before) & RTL819X_TC1_MASK;
	if (rtl819x_tc1_delta_at_arm == 0) {
		rtl819x_tc_wr(RTL819X_TCCNR, cnr);
		ret = -ETIME;
		goto out;
	}

	rtl819x_ext_cycles = 0;
	rtl819x_ext_last = after;
	rtl819x_ext_gap_max = 0;
	rtl819x_ext_reads = 0;
	rtl819x_tc1_armed = 1;

out:
	rtl819x_last_verdict = ret;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	/* Registration is outside the lock: clocksource_register() takes
	 * clocksource_lock with interrupts disabled and there is no reason to
	 * hold two. */
	if (ret == 0) {
		ret = clocksource_register(&rtl819x_tc1_clocksource);
		if (ret) {
			spin_lock_irqsave(&rtl819x_tc_lock, flags);
			rtl819x_tc1_armed = 0;
			rtl819x_last_verdict = ret;
			spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		}
	}
	return ret;
}

static int rtl819x_tc1_disarm(void)
{
	unsigned long flags;
	u32 cnr, ir;

	spin_lock_irqsave(&rtl819x_tc_lock, flags);
	if (!rtl819x_tc1_armed) {
		spin_unlock_irqrestore(&rtl819x_tc_lock, flags);
		return -EINVAL;
	}
	rtl819x_tc1_armed = 0;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

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
	u64 j, ext;
	u32 cyc, tc0cnt, tc0data, tc1data, cnr, ir, cdbr, gimr, gisr;
	u32 gap, reads;
	int armed, verdict, len = 0;

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
	ext	= rtl819x_ext_cycles;
	gap	= rtl819x_ext_gap_max;
	reads	= rtl819x_ext_reads;
	armed	= rtl819x_tc1_armed;
	verdict	= rtl819x_last_verdict;
	spin_unlock_irqrestore(&rtl819x_tc_lock, flags);

	len += scnprintf(page + len, PAGE_SIZE - len, "driver=rtl819x-timer %s\n",
			 RTL819X_TC_VERSION);
	len += scnprintf(page + len, PAGE_SIZE - len, "state=%s\n", armed ? "armed" : "idle");
	len += scnprintf(page + len, PAGE_SIZE - len, "last_verdict=%d\n", verdict);

	/* Declared parameters -- so the card does not re-derive them and get
	 * a different answer from the driver's. */
	len += scnprintf(page + len, PAGE_SIZE - len, "hz_assumed=%u\n", RTL819X_TC_HZ);
	len += scnprintf(page + len, PAGE_SIZE - len, "period_cycles=%u\n", RTL819X_TC1_PERIOD);
	len += scnprintf(page + len, PAGE_SIZE - len, "mask_bits=%u\n", RTL819X_TC1_MASK_BITS);
	len += scnprintf(page + len, PAGE_SIZE - len, "shift=%u\n", RTL819X_TC1_SHIFT);
	len += scnprintf(page + len, PAGE_SIZE - len, "mult=%u\n", rtl819x_tc1_clocksource.mult);
	len += scnprintf(page + len, PAGE_SIZE - len, "rating=%d\n", RTL819X_TC1_RATING);

	/* The sample. */
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_cycles=%u\n", cyc);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext=%llu\n", (unsigned long long)ext);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_reads=%u\n", reads);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_gap_max=%u\n", gap);
	len += scnprintf(page + len, PAGE_SIZE - len, "tc1_ext_trusted=%d\n",
			 (reads > 0 && gap < (RTL819X_TC1_MASK >> 1)) ? 1 : 0);
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

static int __init rtl819x_timer_init(void)
{
	struct proc_dir_entry *pde;

	/* mult here and not in arm(): the /proc dump prints it, and a dump
	 * whose mult reads 0 until somebody arms would invite the reader to
	 * think the number is broken rather than unset.  NTP adjusts mult on
	 * the selected clocksource only, and at rating 0 this is never it. */
	rtl819x_tc1_clocksource.mult =
		clocksource_hz2mult(RTL819X_TC_HZ, RTL819X_TC1_SHIFT);

	rtl819x_tc0data_at_init	= rtl819x_tc_rd(RTL819X_TC0DATA);
	rtl819x_tccnr_at_init	= rtl819x_tc_rd(RTL819X_TCCNR);
	rtl819x_tcir_at_init	= rtl819x_tc_rd(RTL819X_TCIR);
	rtl819x_cdbr_at_init	= rtl819x_tc_rd(RTL819X_CDBR);
	rtl819x_gimr_at_init	= rtl819x_intc_rd(RTL819X_GIMR);

	pde = create_proc_entry(RTL819X_PROC_NAME, 0644, NULL);
	if (!pde)
		return -ENOMEM;
	pde->read_proc  = rtl819x_tc_read_proc;
	pde->write_proc = rtl819x_tc_write_proc;
	return 0;
}
arch_initcall(rtl819x_timer_init);
