/*
 * rlxfw-entropy -- an entropy source for the RTL8196E, and its credit policy.
 *
 * R7, 2026-09-30.  rlxfw's own file.  It is staged into the kernel tree's
 * drivers/char/ by tools/rlxfw-marks.py from config/rlxfw-src/; it is never
 * edited inside src-vendor/, and the Kbuild line that compiles it is a row of
 * config/rlxfw-marks.tsv (MK13), not a hand edit.
 *
 * THE DEFECT THIS EXISTS FOR.  量 2026-09-30, image r6b8i (recipe 3685a3a4),
 * over the console (bench/2026-09-30/SB-ENT.log, SB-RT1.log):
 *
 *     entropy_avail 0        poolsize 4096      uptime 768.26
 *     entropy_avail 0        poolsize 4096      uptime 1613.27
 *
 * 🔴 AND THE CONTROL ARM IS MEASURED, NOT ASSUMED.  量 2026-09-30, same
 * image, uptime 3289-3437 s (bench/2026-09-30/ENT-B1, ENT-B2, ENT-C1..C6):
 * with a pre-registered refutation -- if entropy_avail rose above 0 on the
 * unmodified image while a burst of aperiodic interrupts demonstrably landed,
 * the premise here would be false -- 400 ICMP echoes round-tripped 400/400
 * and IRQ 12 advanced 279 -> 294 -> 1063 while IRQ 8 advanced 1048 -> 9320.
 * entropy_avail read 0 before, 0 after each burst and 0 after a further 30 s
 * idle.  ~770 NIC interrupts and ~7,700 serial interrupts, and not one bit
 * credited.  The refutation did not fire and its positive control passed
 * (round 1 is the control that went red for a reason worth keeping: the host
 * pinged 10.1.1.1 while rlx0 carries 10.1.1.3/8, so 300 frames arrived only
 * as broadcast ARP and IRQ 12 moved 15 -- no entropy figure from that round
 * means anything).
 *
 * The pool is empty and stays empty.  include/linux/rlxfw-entropy.h records
 * the three-part mechanism 讀 out of the tree that builds; the short form is
 * that no handler carries IRQF_SAMPLE_RANDOM (量: 36 driver call sites in the
 * drop do, and zero of them is compiled into this image), that the other two
 * credit paths are never exercised on an unattended boot, and that arch/rlx's
 * get_cycles() is `return 0;` so the kernel's own estimator would have had
 * nothing sub-jiffy to measure even with the flag.
 *
 * 🔴 "THERE IS NO INPUT DEVICE AND NO DISK" WAS THE FIRST DRAFT OF THAT
 * SENTENCE AND BOTH HALVES WERE WRONG.
 * drivers/input/keyboard/rtl819x-keys.c registers a POLLED input device and
 * calls input_report_key(), which reaches add_input_randomness() through
 * drivers/input/input.c:308 -- so a RESET BUTTON PRESS is a live credit path,
 * human-timed and rare.  And add_disk_randomness()'s gate is not a rotating
 * disk: block/genhd.c:1157 calls rand_initialize_disk() unconditionally inside
 * alloc_disk_node(), with no rotational test in this tree, so any mtdblock
 * request completion samples (drivers/mtd/mtd_blkdevs.c:122 -> end_request ->
 * block/blk-core.c:2011).  The image is quiet only because nothing issues
 * mtdblock I/O; /dev/mtdN through mtdchar does not use the block layer.  Both
 * matter to any experiment on this file: a button press or a mount credits the
 * pool for a reason that is not this driver.  A third path is the
 * RNDADDTOENTCNT ioctl (random.c:1122-1127), which credits with no data at all
 * for CAP_SYS_ADMIN -- so "entropy_avail >= 128" is a claim about root's
 * restraint as well as about the hardware.
 *
 * ------------------------------------------------------------------------
 * WHAT IS NOT A SOURCE HERE, AND WHY
 * ------------------------------------------------------------------------
 *
 * 🔴 THE TIMER TICK IS NOT A SOURCE.  IRQ 13 (TC0, 讀 76,827 in
 * /proc/interrupts at 768 s) and IRQ 25 (TC1, 76,799) are periodic by
 * construction: their arrival phase against TC0CNT is the same number every
 * tick, up to the drift between two dividers of one base clock.  Sampling a
 * clock with itself measures nothing.  Crediting it would raise
 * entropy_avail on a schedule -- which is worse than 0, because 0 is
 * honest and a scheduled number looks like a measurement.  Rejected.
 *
 * 🔴 THE CONSOLE (IRQ 8) IS NOT WIRED UP, AND THAT IS A CHOICE.  Its arrival
 * times are genuinely aperiodic -- they are the operator's keystrokes -- but
 * (a) reaching them needs a patch to the vendor's shared 8250 IRQ chain, and
 * (b) an unattended boot produces none, so it cannot be the source that makes
 * a login possible.  It would add risk to the one path that must work and
 * bits to the one case that does not need them.  Rejected for R7; the hook is
 * one call and RLXFW_ENT_SRC_NSRC is what it would grow.
 *
 * 🔴 IRQF_SAMPLE_RANDOM ON THE NIC IS NOT USED EITHER, deliberately.  It
 * would route the same interrupt through add_timer_randomness(), which on
 * this board mixes a constant get_cycles() and credits from the min of the
 * first three jiffies deltas -- ~0 bits for packets arriving faster than
 * 100 Hz -- and it would credit ON TOP of this file's credit for the same
 * event.  Two estimators on one event is over-crediting, which is the one
 * error in this file that is a security defect rather than a slow boot.
 *
 * ------------------------------------------------------------------------
 * WHAT IS THE SOURCE
 * ------------------------------------------------------------------------
 *
 * The arrival phase of an aperiodic interrupt, read on TC0CNT.
 *
 * TC0 is the vendor's clockevent, still running on IRQ 13 (讀 76,827 in the
 * capture) although since CLK-27 `jiffies` follows rlxfw's TC1 clockevent on
 * IRQ 25 instead.  🔴 THIS FILE NEVER WRITES THE BLOCK.  It reads four words
 * -- TC0CNT every event, and TCCNR, TC0DATA and CDBR once at the probe -- and
 * writes none of them, so it cannot disturb either tick.  The register is
 * 0xB8003108, `TC0CNT`, SPEC.md REG-07: D (RTL8196E datasheet) 8.2.1 Table 19
 * gives the block base and Table 22 the layout (count in bits 31:4, 3:0
 * reserved), and the same offsets are read on this die --
 * drivers/clocksource/rtl819x-timer.c:418,474 is rlxfw's second reading of
 * both.  🔴 THIS FILE INTRODUCES NO NEW REGISTER VALUE: base, offset and
 * shift are the three that rlxfw's timer driver already carries on two
 * sources, restated here rather than shared so that the entropy source does
 * not depend on an optional driver being configured in.
 *
 * 量 SPEC.md REG-07: two reads of 0xB8003108 seconds apart gave 114,003 and
 * 16,989 ticks -- the counter is live.  D Table 22 says it counts up from 0
 * and reloads at TC0DATA.
 *
 * 🔴 THE RATE IS NOT USED BY ANY DECISION IN THIS FILE, and that is on
 * purpose -- which is as well, because the rate is 推 and not 量.  Under the
 * loader TC0 runs at 14,286,057 Hz with TC0DATA = 142,858 (SPEC.md CLK-17,
 * whose VALUE mark is 推: it is CLK-04's tick times REG-05, not a frequency
 * anyone measured); under Linux arch/rlx/bsp/timer.c reprograms CDBR from
 * divisor 14 to 1000 and TC0DATA from 142,858 to 2,000 (量 seating 11, TM-1),
 * so the live rate is ~200 kHz -- also 推 -- and the period is ~10 ms == one
 * jiffy at CONFIG_HZ=100.  What IS 量 is the ratio: 2,000 counts per jiffy,
 * residual exactly 0 over 140,693,532 counts (CLK-23).  CLAUDE.md forbids
 * predicting a
 * Linux-state value from a loader constant, so no rate is compiled in: the
 * policy below asks only whether the counter MOVED between two events, and
 * /proc/rlxfw-entropy prints TC0DATA and CDBR raw so a reader derives the
 * rate rather than trusting a number in this comment.
 *
 * 🔴 A FINER CLOCK WAS ALREADY LOOKED FOR AND IS NOT THERE.  The first draft
 * of this comment called it 未定 and asked for a bare-metal read of CP0
 * register 9; that read exists.  量 SPEC.md CPU-42, 2026-08-25b, bare metal:
 * rd 9 `Count` reads 00000000 before and after a 100,000-iteration loop,
 * delta 0, traps 0, with `nowrite` 0 on all 256 rows so the zero is a real
 * zero, and CP0 rd 1 `Random` moving as the positive control.  rd 11
 * `Compare` also reads 0.  Two more 讀 readings agree that the port has no
 * counter: arch/rlx/include/asm/cpu-features.h:84 is
 * `#define cpu_has_counter 0`, and arch/rlx/kernel/cpu-probe.c:30 never sets
 * MIPS_CPU_COUNTER.  arch/rlx/include/asm/timex.h's `return 0;` is the third.
 *
 * ⚠️ 殘留, and it is narrower than "未定": a Count that exists but is
 * clock-gated reads and behaves exactly like one that is absent
 * (docs/rlx-cache-and-cp0.md).  The experiment that separates them is one
 * `mtc0` to rd 9 followed by one `mfc0`, and it has never been run -- CPU-56
 * measured that `mtc0` to rd 14 does not write, so it is not a formality.
 * Either way this file cannot use it today, and the coarse clock can only make
 * the credit policy MORE conservative than it claims.
 *
 * ------------------------------------------------------------------------
 * THE CREDIT POLICY, AND THE ARITHMETIC THAT JUSTIFIES IT
 * ------------------------------------------------------------------------
 *
 *   * Every event mixes 12 bytes into the input pool: the raw TC0CNT phase,
 *     jiffies, and (source << 16 | sequence).  Mixing is unconditional and
 *     free of any claim -- mixing without crediting cannot lower the pool's
 *     quality.
 *
 *   * An event QUALIFIES when the MINIMUM of the first three absolute
 *     differences of the phase series is non-zero.  That is the shape
 *     random.c:637-660 uses on jiffies, applied to the fine counter instead,
 *     and the reason it is three orders and not one is a defect this file
 *     was written with and then had to fix:
 *
 *     🔴 `phase != last_phase` IS A TEST THAT CANNOT FAIL ON A REGULAR
 *     SOURCE.  A host sending one packet every 7.1 ms against a ~10 ms
 *     counter period walks the phase by a CONSTANT ~1,420 counts every time.
 *     The phase differs on every event, so a first-order test qualifies all
 *     of them and credits a stream with no jitter in it at all.  The first
 *     difference of a constant-rate walk is constant, so the SECOND
 *     difference is 0 and the event does not qualify; going to the third
 *     order costs nothing and refuses a constant-acceleration walk too.
 *
 *     This is also the whole liveness test.  If the register were
 *     mis-addressed, frozen, or the block powered down, every phase would be
 *     equal, d1 would be 0, and NOTHING would ever be credited.  The failure
 *     mode is a pool that stays at 0 -- which is the state today, and which
 *     R7's login treats as fail-closed.  A broken source cannot manufacture
 *     bits here; it can only fail to produce them.
 *
 *   * Credit is ONE BIT PER RLXFW_ENT_PER_BIT (16) QUALIFYING EVENTS, and at
 *     most one bit per jiffy.
 *
 * WHY 16, stated as the derating it is rather than as a measurement.  The
 * observable is an 11-bit phase (0..1999 counts at ~5 us).  A floor that
 * assumes an attacker who sends every packet and controls its arrival to
 * within ONE count -- far better than any measurement of this board -- still
 * leaves the bus, DRAM refresh and cache state to move the phase, which is
 * exactly what "qualifies" tests.  Take the pessimistic floor at 1 bit per
 * qualifying event and this policy claims 1/16 of it: a 16x derating of a
 * floor that is itself pessimistic.  The kernel's own estimator (random.c's
 * fls(min-delta) >> 1, up to 11 bits per event) is between 1x and 176x more
 * generous on the same data.
 *
 * 🔴 WHAT AN ATTACKER CONTROLS, WITH THE RATIO MEASURED.  量 2026-09-30 on
 * the unmodified image, two bursts from the host (bench/2026-09-30/ENT-C1..C6,
 * $FWRE_WORK/rebuild/s118/bench/entctl2-ping.txt): 300 broadcast frames moved
 * IRQ 12 by only 15, and 400 ICMP echoes round-tripping both ways moved it by
 * 769.  So the interrupt count is NOT the packet count -- the driver's
 * batching puts it anywhere between ~1/20 and ~2 interrupts per frame -- and
 * an attacker who can put frames on the LAN chooses how many events this file
 * sees, over a range of more than an order of magnitude.  The policy is
 * therefore written so that the EVENT COUNT buys as little as possible and
 * the WALL CLOCK is the binding constraint, which is what the clamp below
 * does.  What the attacker cannot choose is the phase: the same burst showed
 * rtt min/avg/max/mdev 1.056/10.619/100.703/14.940 ms -- milliseconds of
 * arrival spread against a 5 us counter tick -- and the part of that spread
 * contributed by the board's own bus, DRAM refresh and cache state is not
 * reachable from the wire at all.
 *
 * WHY THE ONE-BIT-PER-JIFFY CLAMP.  It bounds what a flood can buy: at
 * CONFIG_HZ=100 the pool cannot gain more than 100 bits/s from this source
 * however many packets arrive, so R7's 128-bit threshold needs >= 1.28 s of
 * wall clock AND >= 2,048 qualifying events, whichever is slower.  Without
 * the clamp, a 100 kpps flood would credit 6,250 bits/s and the 4,096-bit
 * pool would fill in 0.65 s, which is a number pretending to be a
 * measurement.
 *
 * ⚠️ WHAT THIS POLICY DOES NOT ESTABLISH, and no value of entropy_avail can:
 * that the bits are cryptographically strong.  entropy_avail is an accounting
 * variable this file writes to; it is not a measurement of the source's
 * min-entropy.  Establishing that needs the raw samples off the board and an
 * SP 800-90B style estimate over them, which R7 does not do.  The
 * `dist` histogram in /proc/rlxfw-entropy exists so that measurement has
 * something to start from: it is the fls() of the absolute phase difference
 * per event, and a source whose every event lands in bucket 0 or 1 is one
 * whose 16x derating is not enough.
 *
 * ------------------------------------------------------------------------
 * COST AND CONTEXT
 * ------------------------------------------------------------------------
 *
 * rlxfw_entropy_event() runs in rtl819x-nic's IRQF_DISABLED handler, once per
 * interrupt and NOT once per packet -- NAPI coalesces, so the rate is bounded
 * by the poll cycle and not by the wire.  It costs one uncached read, three
 * words of pool mixing and no allocation.  It never sleeps, never prints, and
 * never calls into the network stack.
 *
 * The one vendor change is config/host-compat/0009, which adds
 * rlxfw_random_add() to drivers/char/random.c -- mix_pool_bytes() and
 * credit_entropy_bits() are static there and there is no other way in.  That
 * function makes no estimate: the estimate is here, where it is reviewed.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/jiffies.h>
#include <linux/spinlock.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <linux/bitops.h>
#include <linux/rlxfw-entropy.h>
#include <asm/io.h>
#include <asm/addrspace.h>

#define RLXFW_ENT_VERSION	"rlxfw-entropy 1.0"
#define RLXFW_ENT_PROC_NAME	"rlxfw-entropy"

/* The Timer/Counter block.  SPEC.md REG-05..REG-11; D 8.2.1 Table 19 for the
 * base, Tables 20/22/24/26 for the four words read below.  Nothing here is
 * ever written. */
#define RLXFW_ENT_TC_PHYS	0x18003100	/* 0xB8003100 through KSEG1 */
#define RLXFW_ENT_TC0DATA	0x00		/* REG-05, D Table 20 */
#define RLXFW_ENT_TC0CNT	0x08		/* REG-07, D Table 22 */
#define RLXFW_ENT_TCCNR		0x10		/* REG-09, D Table 24 */
#define RLXFW_ENT_CDBR		0x18		/* REG-11, D Table 26 */
#define RLXFW_ENT_VALUE_SHIFT	4		/* count in 31:4, 3:0 reserved */
#define RLXFW_ENT_TCCNR_TC0EN	(1u << 31)

/* The derating.  See "THE CREDIT POLICY" above.  One bit is credited per this
 * many qualifying events, and never more than one bit per jiffy. */
#define RLXFW_ENT_PER_BIT	16

/* Buckets for the fls() of |phase difference|.  fls() of a 28-bit field is at
 * most 28; 32 buckets covers every value it can return. */
#define RLXFW_ENT_NBUCKET	32

static DEFINE_SPINLOCK(rlxfw_ent_lock);

/* Set once, at init, only if the probe below succeeds.  Until then nothing is
 * credited -- read-only, so a failed probe leaves the pool exactly as this
 * file found it. */
static int rlxfw_ent_alive;

/* What the probe read, kept so /proc can show the reader the same four words
 * the decision was taken on. */
static u32 rlxfw_ent_tc0data;
static u32 rlxfw_ent_cdbr;
static u32 rlxfw_ent_tccnr;
static unsigned int rlxfw_ent_probe_reads;	/* reads the liveness test used */

/* Counters.  Updated under rlxfw_ent_lock; unsigned long, so a reader must
 * not assume they never wrap. */
static unsigned long rlxfw_ent_n_event[RLXFW_ENT_SRC_NSRC];
static unsigned long rlxfw_ent_n_badsrc;	/* src outside the range */
static unsigned long rlxfw_ent_n_early;		/* before the probe finished */
static unsigned long rlxfw_ent_n_qual;		/* min|d1,d2,d3| non-zero */
static unsigned long rlxfw_ent_n_repeat;	/* regular to third order */
static unsigned long rlxfw_ent_n_clamped;	/* credit withheld by the clamp */
static unsigned long rlxfw_ent_bits;		/* bits this file has credited */
static unsigned long rlxfw_ent_dist[RLXFW_ENT_NBUCKET];

static unsigned int rlxfw_ent_acc;		/* qualifying events since credit */
static u32 rlxfw_ent_last_phase;
static long rlxfw_ent_last_d1;
static long rlxfw_ent_last_d2;
static unsigned int rlxfw_ent_nseen;		/* capped at 3: the warm-up */
static unsigned long rlxfw_ent_last_credit_j;
static u32 rlxfw_ent_seq;

static inline u32 rlxfw_ent_rd(unsigned int off)
{
	/* CKSEG1: uncached and unmapped, so no ioremap and usable from any
	 * initcall level and from interrupt context.  __raw_readl and not
	 * readl: an on-chip register on this big-endian part is already in CPU
	 * order (the reason drivers/clocksource/rtl819x-timer.c gives). */
	return __raw_readl((void __iomem *)(CKSEG1ADDR(RLXFW_ENT_TC_PHYS) + off));
}

static inline u32 rlxfw_ent_phase(void)
{
	return rlxfw_ent_rd(RLXFW_ENT_TC0CNT) >> RLXFW_ENT_VALUE_SHIFT;
}

/*
 * The event hook.  Called from rtl819x-nic's ISR with interrupts already off.
 *
 * Ordering inside: read the clock FIRST, before taking the lock, so that the
 * sample is the arrival phase and not the phase after an uncontended
 * spin_lock_irqsave -- which on this UP kernel is a constant number of
 * instructions and would subtract exactly the jitter being measured.
 */
void rlxfw_entropy_event(unsigned int src)
{
	u32 phase = rlxfw_ent_phase();
	unsigned long flags;
	int credit = 0;
	struct {
		u32 phase;
		u32 jiffies;
		u32 tag;
	} sample;

	spin_lock_irqsave(&rlxfw_ent_lock, flags);

	if (src < RLXFW_ENT_SRC_NSRC)
		rlxfw_ent_n_event[src]++;
	else
		rlxfw_ent_n_badsrc++;

	sample.phase = phase;
	sample.jiffies = (u32)jiffies;
	sample.tag = (src << 16) | (rlxfw_ent_seq++ & 0xffffu);

	if (!rlxfw_ent_alive) {
		/* The probe has not passed.  Mix anyway -- mixing makes no
		 * claim -- but credit nothing, ever. */
		rlxfw_ent_n_early++;
		spin_unlock_irqrestore(&rlxfw_ent_lock, flags);
		rlxfw_random_add(&sample, sizeof(sample), 0);
		return;
	}

	if (rlxfw_ent_nseen < 3) {
		/* Three events are needed before a third-order difference
		 * exists.  They are mixed, and credited nothing. */
		rlxfw_ent_nseen++;
	} else {
		long d1 = (long)phase - (long)rlxfw_ent_last_phase;
		long d2 = d1 - rlxfw_ent_last_d1;
		long d3 = d2 - rlxfw_ent_last_d2;
		long m;
		int b;

		rlxfw_ent_last_d1 = d1;
		rlxfw_ent_last_d2 = d2;

		if (d1 < 0)
			d1 = -d1;
		if (d2 < 0)
			d2 = -d2;
		if (d3 < 0)
			d3 = -d3;
		m = d1;
		if (m > d2)
			m = d2;
		if (m > d3)
			m = d3;

		/* fls() of the widest value reachable here is 30; bucket 0 is
		 * the m == 0 case, which is exactly a phase series regular to
		 * third order and credits nothing. */
		b = fls((unsigned int)m);
		if (b >= RLXFW_ENT_NBUCKET)
			b = RLXFW_ENT_NBUCKET - 1;
		rlxfw_ent_dist[b]++;

		if (m == 0) {
			rlxfw_ent_n_repeat++;
		} else {
			rlxfw_ent_n_qual++;
			if (++rlxfw_ent_acc >= RLXFW_ENT_PER_BIT) {
				if (jiffies != rlxfw_ent_last_credit_j) {
					rlxfw_ent_acc = 0;
					rlxfw_ent_last_credit_j = jiffies;
					rlxfw_ent_bits++;
					credit = 1;
				} else {
					/* Hold the accumulator at the
					 * threshold: the next qualifying event
					 * in a later jiffy credits, and no
					 * number of events inside one jiffy
					 * can bank bits. */
					rlxfw_ent_acc = RLXFW_ENT_PER_BIT;
					rlxfw_ent_n_clamped++;
				}
			}
		}
	}

	rlxfw_ent_last_phase = phase;
	spin_unlock_irqrestore(&rlxfw_ent_lock, flags);

	/* Outside this file's lock: random.c takes its own. */
	rlxfw_random_add(&sample, sizeof(sample), credit);
}

#ifdef CONFIG_PROC_FS
/*
 * 🔴 THE PAGE BUDGET IS COUNTED, NOT ASSUMED.  read_proc_t sprintfs into one
 * 4,096-byte page (CLAUDE.md).  Fixed lines: 11, none above 72 characters,
 * so <= 792.  The histogram is at most RLXFW_ENT_NBUCKET = 32 lines of the
 * form "dist  NN  <20-digit>\n", <= 32 characters, so <= 1,024.  Worst case
 * 1,816 bytes, and empty buckets are skipped.
 */
static int rlxfw_ent_read_proc(char *page, char **start, off_t off,
			       int count, int *eof, void *data)
{
	unsigned long ev[RLXFW_ENT_SRC_NSRC];
	unsigned long dist[RLXFW_ENT_NBUCKET];
	unsigned long qual, repeat, bits, badsrc, early, clamped;
	unsigned int acc, nseen;
	unsigned long flags;
	int alive, i, len = 0;

	spin_lock_irqsave(&rlxfw_ent_lock, flags);
	alive = rlxfw_ent_alive;
	nseen = rlxfw_ent_nseen;
	for (i = 0; i < RLXFW_ENT_SRC_NSRC; i++)
		ev[i] = rlxfw_ent_n_event[i];
	memcpy(dist, rlxfw_ent_dist, sizeof(dist));
	qual = rlxfw_ent_n_qual;
	repeat = rlxfw_ent_n_repeat;
	bits = rlxfw_ent_bits;
	badsrc = rlxfw_ent_n_badsrc;
	early = rlxfw_ent_n_early;
	clamped = rlxfw_ent_n_clamped;
	acc = rlxfw_ent_acc;
	spin_unlock_irqrestore(&rlxfw_ent_lock, flags);

	len += sprintf(page + len, "%s\n", RLXFW_ENT_VERSION);
	/* The probe's own readings, raw, so the rate is the reader's to
	 * derive and no rate is claimed here. */
	len += sprintf(page + len,
		       "alive %d probe_reads %u tc0data %08X cdbr %08X tccnr %08X\n",
		       alive, rlxfw_ent_probe_reads, rlxfw_ent_tc0data,
		       rlxfw_ent_cdbr, rlxfw_ent_tccnr);
	len += sprintf(page + len, "per_bit %d hz %d\n",
		       RLXFW_ENT_PER_BIT, HZ);
	len += sprintf(page + len, "ev_nic %lu\n", ev[RLXFW_ENT_SRC_NIC]);
	len += sprintf(page + len, "qualifying %lu\n", qual);
	len += sprintf(page + len, "repeat %lu\n", repeat);
	len += sprintf(page + len, "acc %u nseen %u\n", acc, nseen);
	len += sprintf(page + len, "bits %lu\n", bits);
	len += sprintf(page + len, "clamped %lu\n", clamped);
	len += sprintf(page + len, "early %lu badsrc %lu\n", early, badsrc);
	for (i = 0; i < RLXFW_ENT_NBUCKET; i++)
		if (dist[i])
			len += sprintf(page + len, "dist %2d %lu\n",
				       i, dist[i]);

	*eof = 1;
	return len;
}
#endif /* CONFIG_PROC_FS */

/*
 * The probe, and it is a positive control on the register address rather than
 * a formality.  Three readings have to agree with what SPEC.md says this
 * block is, and the counter has to be seen to move:
 *
 *   1. TCCNR's TC0En must be set.  量 REG-09: this unit reads 0xC0000000.
 *      With TC0 disabled the tick would not be running and TC0CNT would be
 *      meaningless.
 *   2. TC0DATA's low nibble must be zero and its count field non-zero.
 *      D Table 20 reserves bits 3:0; a wrong address is far more likely to
 *      read something with bits set there than not.
 *   3. TC0CNT must CHANGE within a bounded number of reads.  This is the
 *      reading that cannot be faked by a plausible-looking constant.
 *
 * Any one failing leaves rlxfw_ent_alive at 0, which means this file credits
 * nothing for the rest of the boot and /proc says so.  It does not print --
 * CONFIG_PRINTK is n in the mainline variant -- and it does not fail the
 * initcall: an entropy source that is not there must not stop the boot.
 *
 * The bound on 3 is reads, not time: the loop needs no calibrated delay and
 * cannot hang.  At ~200 kHz under Linux the counter advances once per ~1,000
 * CPU cycles, so an uncached read loop sees a change within a few hundred
 * iterations; 65,536 is a ceiling, not an expectation, and probe_reads
 * reports what was actually used so the expectation is falsifiable.
 */
static int __init rlxfw_entropy_init(void)
{
	u32 first, now;
	unsigned int i;

#ifdef CONFIG_PROC_FS
	struct proc_dir_entry *pde;
#endif

	rlxfw_ent_tccnr = rlxfw_ent_rd(RLXFW_ENT_TCCNR);
	rlxfw_ent_tc0data = rlxfw_ent_rd(RLXFW_ENT_TC0DATA);
	rlxfw_ent_cdbr = rlxfw_ent_rd(RLXFW_ENT_CDBR);

	if ((rlxfw_ent_tccnr & RLXFW_ENT_TCCNR_TC0EN) &&
	    (rlxfw_ent_tc0data & ((1u << RLXFW_ENT_VALUE_SHIFT) - 1u)) == 0 &&
	    (rlxfw_ent_tc0data >> RLXFW_ENT_VALUE_SHIFT) != 0) {
		first = rlxfw_ent_phase();
		for (i = 1; i <= 65536u; i++) {
			now = rlxfw_ent_phase();
			if (now != first)
				break;
		}
		rlxfw_ent_probe_reads = i;
		if (i <= 65536u) {
			rlxfw_ent_last_phase = now;
			rlxfw_ent_last_credit_j = jiffies;
			rlxfw_ent_alive = 1;
		}
	}

#ifdef CONFIG_PROC_FS
	pde = create_proc_entry(RLXFW_ENT_PROC_NAME, 0444, NULL);
	if (pde)
		pde->read_proc = rlxfw_ent_read_proc;
#endif
	return 0;
}

/* device_initcall (6), so the node and the probe are both in place before
 * rtl819x-nic's late_initcall (7) can register IRQ 12 and call in. */
device_initcall(rlxfw_entropy_init);
