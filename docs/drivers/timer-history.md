# `rtl819x-timer.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/clocksource/rtl819x-timer.c`](../../kernel/linux-2.6.30/drivers/clocksource/rtl819x-timer.c)
until 2026-10-18 — lines 1–384 at commit `828b3268` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [timer](timer.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-timer.c` counts the file's lines at `828b3268`.

```c
/*
 * rtl819x-timer -- a Linux clocksource on the RTL8196E's Timer/Counter 1.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-1, 2026-09-03.  It is staged into
 * drivers/clocksource/ by tools/rlxfw-marks.py from kernel/;
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
 * WHAT VERSION 4.0 CHANGED
 * (R5-3b-2, 2026-09-06; the /proc format moved again, so the version did):
 *
 *   1. The handover happens at boot instead of from a /proc write.  It is
 *      a SEQUENCER and not a reimplementation: every hardware step is the
 *      same function the verb calls, in the order the card typed on
 *      2026-09-06.  See "ARMING AT BOOT" at rtl819x_boot_arm_early().
 *   2. Seven boot_* lines in /proc, and ten RLXFW-TA<n> lines on the wire.
 *      The duplication is the point: /proc needs a shell and the wire does
 *      not, and the failure this step can produce is one that never
 *      reaches a shell.
 *   3. Nothing in the arm/ackip/register path changed.  A diff that
 *      touched those would have broken the one property that makes this
 *      step cheap -- that R5-3b-1's three cold boots are evidence about
 *      the code this version runs.
 *
 * WHAT VERSION 4.1 CHANGED, AND THE BOARD IS WHY
 * (2026-09-06, seating 14, between K2 and M1):
 *
 *   1. The late half re-bases the pre-check window instead of inheriting
 *      the one that starts at reqirq.  4.0's window spans the vendor's
 *      NIC initialisation, which 量 costs 11 of 585 interrupts -- 1.88 %
 *      against a 1 % tolerance -- so 4.0 refused its own handover on
 *      both boots it was given, with ce_check_dc/dj identical to the
 *      interrupt on a cold boot and a warm one.
 *   2. TA6 now prints that shortfall instead of the wait. The wait is
 *      ~300 on every boot and says nothing; the shortfall is a
 *      measurement of the vendor's driver that nothing else produces.
 *   3. Three attempts, and boot_ce_tries says how many were used.
 *   4. 🔴 THE TOLERANCE DID NOT MOVE. 1 % refused a state in which the
 *      system clock would have run 1.88 % slow through boot, with
 *      nothing in the kernel able to notice -- which is exactly what
 *      R5-3b-1's `cereload` rows demonstrated. Widening it would have
 *      been fixing the instrument to agree with the experiment.
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
 * WHY ARMING WAS A WRITE TO /proc AND NOT SOMETHING init DOES
 * (true of versions 1.0 to 3.0; 🔄 2026-09-06 version 4.0 arms at boot,
 *  and the block at the end of this section is why that became sayable).
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
 * reading is what makes the boot-time path (R5-3) safe to write; ~~until then
 * this file boots inert and writes nothing~~.
 *
 * 🔄 2026-09-06 (R5-3b-2): THAT LAST CLAUSE EXPIRED, AND THE TWO HAZARDS
 * ARE ANSWERED RATHER THAN ACCEPTED.  The paragraph above is kept because
 * it was the correct decision on the evidence of the day it was written,
 * and because what changed is the evidence and not the reasoning.
 *
 *   (1) is answered by a guard that has run on the silicon.  arm() does
 *       not blind-write TCCNR: it reads the word back and compares
 *       RTL819X_TCCNR_TC0_BITS against what it read before, restores the
 *       old value and returns -EIO if they moved.  量 seating 13, three
 *       cold boots: tccnr 0xF0000000 after arm against 0xC0000000 before,
 *       i.e. exactly the TC1 bits and nothing of TC0's, and the vendor's
 *       own tick kept advancing across the whole seating.
 *
 *   (2) is answered by a reading of the mask rather than by an argument
 *       about it.  量 seating 12 (CFG-2): GIMR is 0x00209100 at
 *       arch_initcall -- TC1's bit 9 CLEAR -- and reaches 0x00209300 only
 *       after request_irq(25), set by bsp_ictl_irq_unmask on this
 *       driver's behalf.  So between S1 and S4 of the sequencer a TC1
 *       timeout raises a bit nothing is listening to, and the vendor's
 *       tick is on bit 8 and on the LOPI serial vector, neither of which
 *       this driver touches.
 *
 * 🔴 AND THE HAZARD THE PARAGRAPH ABOVE NAMED LAST -- "a hang costs the
 * whole power cycle" -- IS NOT ANSWERED.  It is REDUCED, and the
 * difference is worth a line.  It cannot be removed: past
 * clockevents_register_device() this boot has no way back.  What the ten
 * RLXFW-TA<n> marks buy is that the power cycle is not spent on silence.
 * They go out through prom_putchar, which needs no console and no log
 * buffer, so the last line on the wire names the stage that did not
 * return.  A power cycle that produces a bisected failure point is a
 * different transaction from one that produces nothing.
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
```
