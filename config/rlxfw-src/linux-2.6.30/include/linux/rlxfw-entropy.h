/*
 * rlxfw-entropy -- the interface between rlxfw's drivers and rlxfw's own
 * entropy accounting.   R7.
 *
 * This header is rlxfw's own file.  It is staged into the kernel tree's
 * include/linux/ by tools/rlxfw-marks.py from config/rlxfw-src/; it is never
 * edited inside src-vendor/.
 *
 * WHY THIS EXISTS AT ALL.  量 2026-09-30 on image r6b8i (recipe 3685a3a4),
 * over the console: /proc/sys/kernel/random/entropy_avail reads 0 at 768 s of
 * uptime and 0 again at 1613 s, with poolsize 4096
 * (bench/2026-09-30/SB-ENT.log, bench/2026-09-30/SB-RT1.log).  讀 the reason,
 * in the tree that builds (src-vendor/rtl819x-toolchain/linux-2.6.30):
 *
 *   1. drivers/char/random.c:689 add_interrupt_randomness() is the only
 *      credit path an interrupt can reach, and kernel/irq/handle.c calls it
 *      only for a handler registered with IRQF_SAMPLE_RANDOM.  No driver in
 *      this image registers that flag.
 *   2. 🔴 THE OTHER TWO CREDIT PATHS EXIST AND ARE MERELY IDLE -- the first
 *      draft of this header said they were absent, and that was wrong.
 *      add_input_randomness() is reached from drivers/input/input.c:308, and
 *      drivers/input/keyboard/rtl819x-keys.c registers a polled input device
 *      that calls input_report_key(): a RESET BUTTON PRESS credits the pool.
 *      add_disk_randomness() is gated on disk->random, which
 *      block/genhd.c:1157 sets unconditionally in alloc_disk_node() with no
 *      rotational test, so an mtdblock request completion would credit it
 *      too (drivers/mtd/mtd_blkdevs.c:122 -> end_request); the image is quiet
 *      only because nothing issues mtdblock I/O.  A third path, the
 *      RNDADDTOENTCNT ioctl (random.c:1122-1127), credits with NO DATA for
 *      CAP_SYS_ADMIN.  Any experiment on this file must exclude all three.
 *   3. 🔴 AND THE FLAG WOULD NOT HAVE BEEN ENOUGH.  add_timer_randomness()
 *      (random.c:614) mixes `get_cycles()` and estimates the credit from
 *      jiffies deltas alone -- and arch/rlx/include/asm/timex.h defines
 *      get_cycles() as `return 0;`.  So on this core the pool would receive a
 *      constant in its high-resolution field, and the credit would come from
 *      100 Hz jiffies, whose first/second/third-order minimum is 0 for almost
 *      every pair of packets.  Setting IRQF_SAMPLE_RANDOM would produce a
 *      number, not entropy.
 *
 * So rlxfw supplies its own sample and its own credit policy, and the policy
 * lives in reviewed rlxfw code (drivers/char/rlxfw-entropy.c) rather than in
 * an estimator this board defeats.  The one vendor change is a narrow input
 * function in random.c, config/host-compat/0009.
 */
#ifndef _LINUX_RLXFW_ENTROPY_H
#define _LINUX_RLXFW_ENTROPY_H

/* Event sources.  One slot per rlxfw driver that can observe a genuinely
 * aperiodic event.  A periodic source must NEVER be given a slot: see
 * drivers/char/rlxfw-entropy.c, "WHAT IS NOT A SOURCE HERE". */
#define RLXFW_ENT_SRC_NIC	0	/* rtl819x-nic, IRQ 12, one per ISR */
#define RLXFW_ENT_SRC_NSRC	1

/*
 * Record one aperiodic event.  Safe from hard-IRQ context with interrupts
 * already off (which is where rtl819x-nic's IRQF_DISABLED handler runs) and
 * from process context.  Costs one uncached register read, three words of
 * pool mixing, and no allocation.  It never sleeps and never prints.
 *
 * `src` is one of RLXFW_ENT_SRC_*; a value outside the range is counted and
 * dropped rather than trusted.
 */
void rlxfw_entropy_event(unsigned int src);

/*
 * The vendor-side input, defined by config/host-compat/0009 in
 * drivers/char/random.c.  It mixes `nbytes` from `buf` into the input pool
 * and credits `credit_bits` bits -- and it makes no estimate of its own, on
 * purpose: the estimate is the caller's, so that the one number that matters
 * for security is in a file rlxfw reviews.  `credit_bits` <= 0 mixes without
 * crediting.  Declared here and not in include/linux/random.h so that no
 * vendor header has to change.
 */
void rlxfw_random_add(const void *buf, unsigned int nbytes, int credit_bits);

#endif /* _LINUX_RLXFW_ENTROPY_H */
