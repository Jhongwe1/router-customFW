# `rlxfw-entropy.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c`](../../kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c)
until 2026-10-18 — lines 1–233 at commit `8b073d37` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [entropy](entropy.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rlxfw-entropy.c` counts the file's lines at `8b073d37`.

```c
/*
 * rlxfw-entropy -- an entropy source for the RTL8196E, and its credit policy.
 *
 * R7, 2026-09-30.  rlxfw's own file.  It is staged into the kernel tree's
 * drivers/char/ by tools/rlxfw-marks.py from kernel/; it is never
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
```
