/*
 * rlxfw-entropy -- an entropy source for the RTL8196E, and its credit policy.
 *
 * R7, 2026-09-30.  rlxfw's own file.  It is staged into the kernel tree's
 * drivers/char/ by tools/rlxfw-marks.py from kernel/; it is never
 * edited inside src-vendor/, and the Kbuild line that compiles it is a row of
 * config/rlxfw-marks.tsv (MK13), not a hand edit.
 *
 * THE DEFECT THIS EXISTS FOR.  On the image without it the input pool is
 * empty and stays empty: MEASURED 2026-09-30, entropy_avail 0 at 768 s and at
 * 1,613 s of uptime (bench/2026-09-30/SB-ENT.log, SB-RT1.log).  No handler in
 * that image carries IRQF_SAMPLE_RANDOM, the other two credit paths are never
 * exercised on an unattended boot, and arch/rlx's get_cycles() is
 * `return 0;` -- include/linux/rlxfw-entropy.h records the mechanism.
 *
 * THE SOURCE is the arrival phase of an aperiodic interrupt, rtl819x-nic's
 * IRQ 12, read on TC0CNT (0xB8003108, SPEC.md REG-07).  THIS FILE NEVER
 * WRITES THE BLOCK: it reads TC0CNT every event, and TCCNR, TC0DATA and CDBR
 * once at the probe.  The timer tick and the console are not sources, and the
 * NIC's handler does not carry IRQF_SAMPLE_RANDOM, so no event is credited
 * twice.
 *
 * THE CREDIT POLICY
 *
 *   * Every event mixes 12 bytes into the input pool: the raw TC0CNT phase,
 *     jiffies, and (source << 16 | sequence).  Mixing is unconditional and
 *     free of any claim -- mixing without crediting cannot lower the pool's
 *     quality.
 *
 *   * An event QUALIFIES when the MINIMUM of the first three absolute
 *     differences of the phase series is non-zero -- the shape random.c's
 *     estimator uses on jiffies, applied to the fine counter instead.  A
 *     source whose phase walks at a constant rate never qualifies.
 *
 *   * Credit is ONE BIT PER RLXFW_ENT_PER_BIT (16) QUALIFYING EVENTS, and at
 *     most one bit per jiffy.
 *
 * Why three orders and not one, why 16, why the clamp, what an attacker on
 * the LAN controls, and what this policy does not establish -- that the bits
 * are cryptographically strong: the head this file carried until 2026-10-18,
 * verbatim in docs/drivers/entropy-history.md.  The driver page:
 * docs/drivers/entropy.md; the reasoning and every reading: notes/entropy.md.
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
 * NOTE: THE PAGE BUDGET IS COUNTED, NOT ASSUMED.  read_proc_t sprintfs into one
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
 *   1. TCCNR's TC0En must be set.  MEASURED REG-09: this unit reads 0xC0000000.
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
