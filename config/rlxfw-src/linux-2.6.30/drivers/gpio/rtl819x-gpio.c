/*
 * rtl819x-gpio -- a gpiolib gpio_chip on the RTL8196E's PABCD port.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-4, 2026-09-06, thirty-seventh segment.  It
 * is staged into drivers/gpio/ by tools/rlxfw-marks.py from config/rlxfw-src/;
 * config/rlxfw-marks.tsv carries the one Kbuild line that links it, and
 * config/host-compat/0005 is what makes CONFIG_GPIOLIB reachable on this arch
 * at all.
 *
 * WRITTEN BLIND, AND THIS IS THE CLEANEST INSTANCE IN THE GATE.
 * docs/blind-write-ledger.md 4.1 records ZERO cited paths in the `gpio`
 * domain: no third-party RTL8196E GPIO driver has been cloned, opened or
 * read by this project, and `ggbruno/openwrt` -- the port whose author
 * claims gpio works -- is not even fetched (SOURCES.json, "fetch": "later").
 * What WAS read to write this file is the gpiolib FRAMEWORK, which is
 * mainline Linux and not an implementation of this SoC:
 *
 *     include/asm-generic/gpio.h        struct gpio_chip, gpiochip_add()
 *     drivers/gpio/gpiolib.c            which ops the framework dispatches to
 *     drivers/gpio/Kconfig              the GPIOLIB dependency (see 0005)
 *     arch/rlx/include/asm/mach-generic/gpio.h   the arch's two branches
 *
 * All four are in ledger 4.9 with their depth.  Reading the framework is
 * unavoidable -- a gpio_chip cannot be written without knowing what a
 * gpio_chip is -- and it says nothing about which register drives which pin
 * on this die, which is the layer docs/driver-diff.md compares.
 *
 * EVERY REGISTER FACT BELOW IS THIS DIE'S OWN READING.
 *
 *   SPEC.md MAP-09   0xB8003500 is the GPIO block: PABCD_CNR at +0x00,
 *                    PABCD_DIR at +0x08, PABCD_DAT at +0x0C.  文 (the
 *                    datasheet) and 量 (read on this board, 2026-08-24).
 *   SPEC.md REG-26   PABCD_CNR = 0xFFFFFFDF.  量.  Bit 5 is the ONLY cleared
 *                    bit in the whole 32-bit word.  Disassembly of this
 *                    unit's own loader puts the write at 0x804083AC, called
 *                    unconditionally from main() at 0x80406778, and what it
 *                    clears is bit 5 of 0xB8003500 and of 0xB8003508.
 *   SPEC.md REG-27   PABCD_DIR = 0xFF000000.  量.  Bit 5 = 0, an INPUT, and
 *                    byte-identical with the button held and released.
 *   SPEC.md REG-28   PABCD_DAT: 0x0000003C released, 0x0000001C held.  量.
 *                    XOR = 0x00000020 -- bit 5 alone -- so the button is
 *                    ACTIVE LOW.
 *   SPEC.md BRD-05   That button is a GPIO and NOT RESET#.  It has a pull-up.
 *
 * ------------------------------------------------------------------------
 * 🔴 1.1, R5-7, 2026-09-10: THIS DRIVER NOW WRITES TWO WORDS, ON ONE BIT.
 *
 * The banner below said "THIS DRIVER WRITES NOTHING TO THE SILICON, AND THAT
 * IS THE IMPLEMENTATION RATHER THAN AN ABUNDANCE OF CAUTION."  It is kept
 * because everything under it is still true of bit 5 and of the other thirty
 * lines, and because a claim that stopped being true is worth more in place
 * than deleted.  What changed is one bit and it is written down in one
 * constant: RTL819X_GPIO_ALLOW_OUT_MASK is (1u << 6).
 *
 * The argument is notes/gpio-driver.md -- three hazards answered one at a
 * time for bit 6 only (§ 3), eight refutation conditions written before the
 * change (§ 8), a runtime contention detector because the vendor's
 * rtl_gpio_timer writes the same bit and nothing can arbitrate (§ 6), and
 * § 5, which states in its own words the hole the argument does NOT close:
 * seven functions in this image materialise PABCD_DAT and have not been read.
 *
 * 🟢 The two writes are predicted to change nothing: DIR already reads
 * FF000040 (bit 6 already an output) and DAT already reads 0000007C (bit 6
 * already high, the LED already dark), both put there by the vendor's own
 * firmware and measured on this die.  G7/G8 are in the boot capture so that
 * is a reading rather than an assumption.
 * ------------------------------------------------------------------------
 *
 * ------------------------------------------------------------------------
 * THIS DRIVER WRITES NOTHING TO THE SILICON, AND THAT IS THE IMPLEMENTATION
 * RATHER THAN AN ABUNDANCE OF CAUTION.       [1.0.  See the 1.1 note above.]
 * ------------------------------------------------------------------------
 *
 * The loader already cleared bit 5 of CNR and of DIR before Linux started
 * (REG-26).  So the pin is already a GPIO, already an input, and reading the
 * button needs no register write at all.  A driver that needs no writes
 * should issue none; there is no separate safety argument to make.
 *
 * What the guard is for is everything else, and here the numbers are the
 * argument:
 *
 *   CNR = 0xFFFFFFDF means 31 of 32 pins are on PERIPHERAL functions.  This
 *   project has not established which peripherals.  The UART this board is
 *   read through is a candidate, and so is the SPI controller that reaches
 *   the flash.  Clearing the wrong CNR bit takes a pin away from whatever
 *   owns it, and on a one-device-no-spare project the failure mode of
 *   "the console stopped" is indistinguishable from "the kernel hung".
 *
 *   DIR = 0xFF000000 means bits 24..31 are already OUTPUTS, driven by
 *   something this project has not identified.  A masked write whose mask is
 *   wrong reaches them.
 *
 *   And bit 5 -- the one line that IS a GPIO -- is the worst output of all.
 *   It has a pull-up and a button to ground.  Driving it high while the
 *   button is held shorts the pad driver through the switch.
 *
 * So RTL819X_GPIO_ALLOW_OUT_MASK is 0.  Not "0 for now" -- 0 because no line
 * on this die has a measured safe output state, and the constant is the one
 * place that changes when one does.  The output path is written, complete,
 * and refuses; the `tryout` verb exists to demonstrate the refusal ON THE
 * SILICON with a before/after register comparison, because a guard that has
 * never been observed refusing is a guard nobody has tested.
 *
 * 🟢 1.1: A LINE DID ACQUIRE ONE, AND THE SENTENCE ABOVE IS WHY THE CHANGE IS
 * ONE CONSTANT.  BRD-13 (量 2026-09-09, seating 19) is that measurement for
 * bit 6: it drives the second of the board's eight LEDs, active low, polarity
 * read at BOTH levels with the other seven LEDs as the negative control.
 * Bit 5's paragraph above is untouched and bit 5 is still refused -- which is
 * `RC4`, the refutation condition that makes the other seven mean anything:
 * `tryout 5` must still come back -EPERM in the SAME boot in which bit 6
 * works.  The `tryout` verb therefore did not become obsolete when the mask
 * opened; it became the control.
 *
 * 🔴 A LIMITATION OF 2.6.30's gpiolib THAT SHAPES THIS FILE.
 * struct gpio_chip's .set returns void (include/asm-generic/gpio.h:92-93 in
 * this drop), so a refusal inside .set cannot reach the caller as an errno.
 * The guard therefore lives at .request and .direction_output, which do
 * return int, and .set is a counted no-op.  讀 drivers/gpio/gpiolib.c:967 --
 * gpio_direction_output() fails early unless BOTH .set and .direction_output
 * are present, so omitting .set to make writing impossible is not available:
 * it would also disable the direction call, and __gpio_set_value() at :1065
 * dispatches through chip->set with no NULL check, which would be an oops
 * rather than a refusal.  All four ops are therefore present and the policy
 * is in the bodies.
 *
 * ------------------------------------------------------------------------
 * THE EXPERIMENT THIS FILE IS BUILT TO SUPPORT, AND ITS CONTROLS
 * ------------------------------------------------------------------------
 *
 * R5's DoD asks for ten boots without an oops per driver, and PROGRESS.md
 * already records that the count has water in it: ten boots of one image
 * prove one image booted ten times.  For this driver the ten boots have to
 * contain the thing the driver does, so they are split into two populations
 * that differ by one physical act:
 *
 *   boots with the button RELEASED   G3 = 0000003C, G5 = 1
 *   boots with the button HELD       G3 = 0000001C, G5 = 0
 *
 * G3 and G5 are printed at subsys_initcall, before any shell exists, so the
 * reading needs no userspace and no typing.
 *
 * 🟢 THE NEGATIVE CONTROL IS IN THE SAME MARKS.  G1 (CNR) and G2 (DIR) must
 * be IDENTICAL on every boot of both populations, because pressing a button
 * cannot change a pin's function or direction.  An experiment in which the
 * intended signal moves is worth much less than one in which the intended
 * signal moves and two things that must not move are watched at the same
 * time.  If G1 or G2 tracks the button, the register map in SPEC.md is
 * wrong and the reading that says bit 5 is an input is unsupported.
 *
 * ------------------------------------------------------------------------
 * WHAT THIS FILE DOES NOT ESTABLISH
 * ------------------------------------------------------------------------
 *
 *  1. WHICH PORT LETTER BIT 5 IS.  PABCD packs four ports into one word and
 *     this project has never established the byte order.  BRD-06 records
 *     that RESET# is SoC pin 49, shared with LED_PORT3 and GPIOB[5] -- which
 *     hints at B, and a hint is not a reading.  It matters for the .dts node
 *     and the binding that R5's DoD asks for, and it is R5-4's open question
 *     rather than something this file quietly decides.  The chip is
 *     therefore labelled by its REGISTER name, `rtl819x-pabcd`, and the
 *     lines are numbered 0..31 by bit position, which is the only thing
 *     that has been measured.
 *
 *  2. THAT ANY OTHER BIT IS A GPIO.  ngpio is 32 because the register is 32
 *     bits wide, not because 32 pins exist.  .request refuses every line
 *     outside RTL819X_GPIO_KNOWN_MASK, so the chip's usable width is TWO in
 *     1.1 -- bit 5 (BRD-05, a button) and bit 6 (BRD-13, an LED) -- and it
 *     was one in 1.0.  Thirty of the thirty-two are still refused, and the
 *     two that are not are the two this project has driven or watched with
 *     its own eyes on this board.
 *
 *  3. AN INTERRUPT.  .to_irq is NULL.  No GPIO interrupt has been measured
 *     on this die, and docs/interrupt-map.md has no row for one.
 *     🔴 It is ALSO not safe to add one here without a Kconfig check:
 *     arch/rlx/include/asm/mach-generic/gpio.h:16 declares gpio_to_irq()
 *     OUTSIDE the CONFIG_GPIOLIB guard and arch/rlx defines it nowhere.
 *     量: the only caller in the built set is gpiolib.c:1155, inside
 *     `#ifdef CONFIG_DEBUG_FS` at :1133, and this image has
 *     `# CONFIG_DEBUG_FS is not set` -- so it is compiled out and the link
 *     succeeds.  Turning CONFIG_DEBUG_FS on breaks the link.  That is a
 *     property of the arch header being incomplete against mainline MIPS's,
 *     which aliases gpio_to_irq to __gpio_to_irq under GPIOLIB.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/gpio.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/module.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

/* ------------------------------------------------------------------------
 * Constants.  Every one of these has a SPEC.md id above.
 * ------------------------------------------------------------------------ */

#define RTL819X_GPIO_VERSION	"rtl819x-gpio 1.1"

#define RTL819X_GPIO_PHYS	0x18003500	/* 0xB8003500 through KSEG1 */

#define RTL819X_PABCD_CNR	0x00		/* MAP-09, REG-26 */
#define RTL819X_PABCD_UNK04	0x04		/* unnamed; see `probe04` */
#define RTL819X_PABCD_DIR	0x08		/* MAP-09, REG-27 */
#define RTL819X_PABCD_DAT	0x0C		/* MAP-09, REG-28 */

#define RTL819X_GPIO_NGPIO	32
#define RTL819X_GPIO_BUTTON	5		/* BRD-05 */
#define RTL819X_GPIO_LED2	6		/* BRD-13 */

/* The lines this die is known to carry as GPIOs.
 *
 * bit 5  REG-26: the only cleared bit of CNR, and the loader is what cleared
 *        it.  A button, active low, BRD-05.
 * bit 6  BRD-13, 量 2026-09-09 (seating 19): drives the SECOND of the eight
 *        LEDs on the board, ACTIVE LOW, polarity measured at both levels with
 *        the other seven LEDs as the negative control.  🔴 It is NOT a
 *        cleared bit of CNR -- the live CNR is FFFFFF8B (量 C1-G0), and bit 6
 *        is clear there because the VENDOR's rtl_gpio_init cleared it, not the
 *        loader.  notes/gpio-driver.md § 3.1 is the whole argument and § 3.4
 *        is the ordering it rests on; .direction_output below turns that
 *        ordering into a runtime check rather than leaving it an assumption. */
#define RTL819X_GPIO_KNOWN_MASK	((1u << RTL819X_GPIO_BUTTON) | \
				 (1u << RTL819X_GPIO_LED2))

/* 🔴 THIS WAS 0 UNTIL 2026-09-10 AND THE OLD COMMENT IS KEPT BELOW.
 *
 * It is bit 6 and nothing else.  notes/gpio-driver.md § 3 answers the three
 * hazards for that one bit and § 8 writes eight refutation conditions before
 * the change; the short form is that every level either writer can produce on
 * bit 6 has already been produced on this die BY THE VENDOR'S OWN FIRMWARE,
 * measured (REG-37, twelve strictly alternating samples; BRD-13, both levels
 * seen by eye), and that DIR already reads FF000040 -- bit 6 is already an
 * output, put there by the vendor.
 *
 * Bit 5 stays out, and that is the load-bearing half: it has a pull-up and a
 * button to ground, so driving it high while the button is held shorts the pad
 * driver through the switch.  `tryout 5` must still be refused in the same
 * boot in which bit 6 works -- notes/gpio-driver.md § 8 `RC4`.
 *
 * (Original: "Zero, and the long comment at the top of this file is the
 * reason.  This is the single place that changes if a line ever acquires a
 * measured safe output state."  A line did.) */
#define RTL819X_GPIO_ALLOW_OUT_MASK	(1u << RTL819X_GPIO_LED2)

/* The bit the foreign-write detector watches.  Bit 6 only: bit 5 is a button
 * and legitimately moves under the operator's finger, so watching it would
 * measure the operator.  notes/gpio-driver.md § 6.1. */
#define RTL819X_GPIO_WATCH_MASK		(1u << RTL819X_GPIO_LED2)

/* The values REG-27 and REG-26 recorded on 2026-08-24.  They are used only to
 * report agreement or disagreement -- nothing is written to make them true. */
#define RTL819X_GPIO_CNR_EXPECT	0xFFFFFFDFu
#define RTL819X_GPIO_DIR_EXPECT	0xFF000000u

#define RTL819X_GPIO_PROC_NAME	"rtl819x-gpio"

/* ------------------------------------------------------------------------
 * Register access.  Same reasoning as rtl819x-timer.c: __raw_readl and not
 * readl, because readl converts a little-endian device word to CPU order and
 * an on-chip register on this big-endian part is already in CPU order.
 * CKSEG1ADDR, so the mapping is uncached, unmapped, and needs no ioremap --
 * which is also what lets this run from subsys_initcall.
 * ------------------------------------------------------------------------ */

static inline void __iomem *rtl819x_gpio_reg(unsigned int off)
{
	return (void __iomem *)(CKSEG1ADDR(RTL819X_GPIO_PHYS) + off);
}

static inline u32 rtl819x_gpio_rd(unsigned int off)
{
	return __raw_readl(rtl819x_gpio_reg(off));
}

/* Deliberately the ONLY write helper in this file, and every call site is
 * inside a refusal that has already returned.  It exists so that
 * `git grep rtl819x_gpio_wr` returns an auditable list, which is what
 * docs/blind-write-ledger.md counts. */
static inline void rtl819x_gpio_wr(unsigned int off, u32 v)
{
	__raw_writel(v, rtl819x_gpio_reg(off));
}

/* ------------------------------------------------------------------------
 * State.  All of it is counters and policy; none of it mirrors hardware,
 * because a mirror is a second source that can disagree with the register
 * and there is no reason to have one for three words that are one load away.
 * ------------------------------------------------------------------------ */

static DEFINE_SPINLOCK(rtl819x_gpio_lock);

static int  rtl819x_gpio_added;		/* gpiochip_add() returned 0 */
static int  rtl819x_gpio_add_rc = -EAGAIN;

/* 🔴 REPLACES `rtl819x_gpio_unlocked`, AND THE REPLACEMENT IS A WEAKENING.
 *
 * The old interlock was opt-in: output was impossible until somebody typed
 * `unlock N`.  leds-gpio cannot type anything, so an opt-in interlock means
 * either the LED never works or the interlock is open from boot -- and an
 * interlock that must be open for the driver's only consumer to bind is not an
 * interlock.  notes/gpio-driver.md § 7 ② states this as a weakening rather
 * than dressing it as a refactor.
 *
 * What replaces it can only NARROW: the effective mask is
 * ALLOW_OUT_MASK & ~out_locked, so no runtime act can grant output on a line
 * the compiled mask does not carry.  `unlock` refuses any such line outright.
 *
 * 🟢 The compensation is that the guard becomes two-sided and testable on the
 * die in one boot: `lock 6` then a sysfs brightness write must leave DAT
 * unmoved, `unlock 6` then the same write must move it.  Until 1.1 the guard
 * had only ever been observed refusing, which is a wall and not a guard.
 *
 * The name is inverted deliberately: `unlocked` defaulting to "everything
 * unlocked" would be a name that lies. */
static u32  rtl819x_gpio_out_locked;	/* lines forbidden at run time. 0. */

static u32  rtl819x_gpio_boot_cnr;	/* latched at subsys_initcall */
static u32  rtl819x_gpio_boot_dir;
static u32  rtl819x_gpio_boot_dat;

static unsigned long rtl819x_gpio_n_get;	/* .get calls */
static unsigned long rtl819x_gpio_n_req_ok;	/* .request accepted */
static unsigned long rtl819x_gpio_n_req_no;	/* .request refused */
static unsigned long rtl819x_gpio_n_dirin_ok;
static unsigned long rtl819x_gpio_n_dirin_no;
static unsigned long rtl819x_gpio_n_dirout_ok;	/* .direction_output permitted */
static unsigned long rtl819x_gpio_n_dirout_no;	/* .direction_output refused */
static unsigned long rtl819x_gpio_n_set_ok;	/* .set permitted */
static unsigned long rtl819x_gpio_n_set_no;	/* .set refused (counted, void) */

/* 🔴 NO LONGER ZERO ON THIS IMAGE, and that is the whole of R5-7.  1.0's
 * comment here read "actual register writes.  0." -- see notes/gpio-driver.md
 * § 7, which predicts exactly 2 after probe (one DAT, one DIR, from the single
 * .direction_output leds-gpio issues) and predicts that BOTH write a value the
 * register already holds. */
static unsigned long rtl819x_gpio_n_writes;

/* ------------------------------------------------------------------------
 * The foreign-write detector.  notes/gpio-driver.md § 6.
 *
 * Two writers, no arbiter: gpio_request arbitrates between gpiolib consumers,
 * and the vendor's rtl_gpio_timer does not go through gpiolib, so nothing can
 * mediate.  § 6 bounds the CONSEQUENCE (every level either writer can produce
 * on bit 6 has already been produced on this die by the vendor, so the worst
 * outcome of losing the race is that a light is wrong) and this is the
 * instrument that says whether the race happens at all.
 *
 * Same shape as rtl819x-spi's n_state_foreign, which read 0 across 4,115
 * transfers: remember the value last written to DAT, and on every subsequent
 * access compare the live register's WATCH_MASK bits against it.
 *
 * 🔴 ITS STATED LIMIT, which is why the positive control is what it is: it
 * SAMPLES.  A write undone before the next sample is invisible.  The control
 * therefore holds the button for ~10 s against a 1 Hz writer (FW-40) rather
 * than looking for a single event -- notes/gpio-driver.md § 6.2.  A counted
 * zero is a claim, and this one is only worth reading beside a boot in which
 * the same counter was made to move.
 * ------------------------------------------------------------------------ */
static int  rtl819x_gpio_state_known;	/* have we ever written DAT? */
static u32  rtl819x_gpio_state_last;	/* the whole word we last wrote */
static unsigned long rtl819x_gpio_n_state_chk;	/* comparisons made */
static unsigned long rtl819x_gpio_n_state_foreign;	/* of those, diverged */
static int  rtl819x_gpio_foreign_seen;	/* first divergence latched */
static u32  rtl819x_gpio_foreign_first;	/* the live DAT at that moment */

/* G7/G8 are emitted OUTSIDE the lock from values sampled inside it.  See
 * rtl819x_gpio_direction_output() for why that is not a convenience. */
static int  rtl819x_gpio_first_out_done;
static u32  rtl819x_gpio_first_out_before;
static u32  rtl819x_gpio_first_out_after;

/* The unnamed word at +0x04 is not read at boot.  A read is normally free,
 * but a read-to-clear status register is a write in effect and nothing here
 * knows what +0x04 is.  `probe04` makes reading it a typed act. */
static int  rtl819x_gpio_probed04;
static u32  rtl819x_gpio_val04;

/* ------------------------------------------------------------------------
 * Policy and detector helpers.  Both are called with the lock held.
 * ------------------------------------------------------------------------ */

/* The effective output permission: the compiled mask, narrowed by whatever
 * the runtime mask has taken away.  There is deliberately no path that can
 * widen it -- see the comment on rtl819x_gpio_out_locked. */
static inline u32 rtl819x_gpio_out_mask(void)
{
	return (u32)RTL819X_GPIO_ALLOW_OUT_MASK & ~rtl819x_gpio_out_locked;
}

/* Compare the live DAT against the value this driver last wrote, on the
 * watched bits only.  Called with the lock held, ALWAYS BEFORE a write of our
 * own -- otherwise the driver would be counting itself. */
static void rtl819x_gpio_state_check(u32 dat)
{
	if (!rtl819x_gpio_state_known)
		return;
	rtl819x_gpio_n_state_chk++;
	if (((dat ^ rtl819x_gpio_state_last) & RTL819X_GPIO_WATCH_MASK) == 0)
		return;
	rtl819x_gpio_n_state_foreign++;
	if (!rtl819x_gpio_foreign_seen) {
		rtl819x_gpio_foreign_seen = 1;
		rtl819x_gpio_foreign_first = dat;
	}
}

/* Record what we just put in DAT.  The WHOLE word is kept, not just the
 * watched bits, so that /proc can show a reader the value rather than a
 * fragment of one. */
static void rtl819x_gpio_state_note(u32 dat)
{
	rtl819x_gpio_state_last = dat;
	rtl819x_gpio_state_known = 1;
}

/* ------------------------------------------------------------------------
 * gpio_chip operations.
 * ------------------------------------------------------------------------ */

/* Refuse any line this die has not been measured to carry.  This is the
 * framework's own entry point (gpiolib.c:804 dispatches gpio_request here),
 * so a consumer such as gpio_keys asking for a line that is on a peripheral
 * function gets -ENODEV from the driver rather than a plausible reading of a
 * pin that is doing something else. */
static int rtl819x_gpio_request(struct gpio_chip *chip, unsigned off)
{
	unsigned long flags;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (!((1u << off) & RTL819X_GPIO_KNOWN_MASK)) {
		rtl819x_gpio_n_req_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -ENODEV;
	}
	rtl819x_gpio_n_req_ok++;
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
	return 0;
}

static void rtl819x_gpio_free(struct gpio_chip *chip, unsigned off)
{
	/* Nothing is allocated, so nothing is released.  The hook is present
	 * because gpiolib.c:846 calls it when it exists and its absence would
	 * make the request/free pair asymmetric in the dump. */
}

static int rtl819x_gpio_get(struct gpio_chip *chip, unsigned off)
{
	unsigned long flags;
	u32 dat;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	/* 1.1 takes the lock here, which 1.0 did not: the counter is no longer
	 * the only shared state a .get touches -- the detector's comparison is
	 * one too, and it has to see the same word the count is for. */
	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_n_get++;
	rtl819x_gpio_state_check(dat);
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);

	/* The RAW pin level, not the logical one.  REG-28 makes the button
	 * active low, and inverting here would put the polarity in two places
	 * -- this driver and the consumer's DT flag -- which is how a polarity
	 * ends up applied twice. */
	return (dat >> off) & 1u;
}

/* Verify rather than write.  REG-27 says DIR bit 5 is already 0, put there by
 * the loader before Linux ran, so the correct implementation of "make this an
 * input" on this die is to check that it already is. */
static int rtl819x_gpio_direction_input(struct gpio_chip *chip, unsigned off)
{
	u32 dir, cnr;
	unsigned long flags;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	if (!((1u << off) & RTL819X_GPIO_KNOWN_MASK)) {
		spin_lock_irqsave(&rtl819x_gpio_lock, flags);
		rtl819x_gpio_n_dirin_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -ENODEV;
	}

	cnr = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);

	/* -EIO and not -EPERM: this is the hardware disagreeing with a
	 * recorded measurement, which is a different event from the policy
	 * refusing, and the two must not arrive as the same errno. */
	if (cnr & (1u << off)) {
		spin_lock_irqsave(&rtl819x_gpio_lock, flags);
		rtl819x_gpio_n_dirin_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -EIO;		/* pin is on a peripheral function */
	}
	if (dir & (1u << off)) {
		spin_lock_irqsave(&rtl819x_gpio_lock, flags);
		rtl819x_gpio_n_dirin_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -EIO;		/* already an output; not our doing */
	}

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	rtl819x_gpio_n_dirin_ok++;
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
	return 0;
}

static int rtl819x_gpio_direction_output(struct gpio_chip *chip, unsigned off,
					 int value)
{
	unsigned long flags;
	u32 dir, dat, newdat;
	int first = 0;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (!((1u << off) & rtl819x_gpio_out_mask())) {
		rtl819x_gpio_n_dirout_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -EPERM;
	}

	/* § 3.4's ORDERING ASSUMPTION, TURNED INTO A RUNTIME CHECK.
	 *
	 * The argument for opening bit 6 rests on the vendor's rtl_gpio_init
	 * having already cleared CNR bit 6 -- i.e. on this driver's
	 * subsys_initcall (4) running after that.  notes/gpio-driver.md § 3.4
	 * measures the ordering and then declines to rely on it: if CNR bit 6
	 * is SET when we get here, the pin is on a peripheral function and
	 * driving it would take that pin away from whatever owns it.
	 *
	 * -EIO and not -EPERM, for .direction_input's reason: the hardware
	 * disagreeing with a recorded measurement is a different event from
	 * the policy refusing, and the two must not arrive as one errno.
	 *
	 * This driver still never writes CNR. */
	if (rtl819x_gpio_rd(RTL819X_PABCD_CNR) & (1u << off)) {
		rtl819x_gpio_n_dirout_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -EIO;
	}

	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);

	/* Before our own write, never after: a detector that ran afterwards
	 * would be comparing the register against what we just put in it. */
	rtl819x_gpio_state_check(dat);

	newdat = value ? (dat | (1u << off)) : (dat & ~(1u << off));

	/* DAT before DIR.  The level is established while the pin is still an
	 * input, so enabling the driver cannot glitch it through the old
	 * level.  On this die both writes are predicted to be no-ops --
	 * notes/gpio-driver.md § 7 -- and G7/G8 below are what say whether
	 * they were. */
	rtl819x_gpio_wr(RTL819X_PABCD_DAT, newdat);
	rtl819x_gpio_wr(RTL819X_PABCD_DIR, dir | (1u << off));
	rtl819x_gpio_n_writes += 2;
	rtl819x_gpio_state_note(newdat);
	rtl819x_gpio_n_dirout_ok++;

	if (!rtl819x_gpio_first_out_done) {
		rtl819x_gpio_first_out_done = 1;
		rtl819x_gpio_first_out_before = dat;
		rtl819x_gpio_first_out_after =
			rtl819x_gpio_rd(RTL819X_PABCD_DAT);
		first = 1;
	}
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);

	/* 🔴 THE MARKS ARE EMITTED HERE AND NOT INSIDE THE LOCK, and that is a
	 * decision rather than a tidy-up.  rlxfw_markx reaches the wire through
	 * prom_putchar, which busy-waits on the UART FIFO: eleven bytes at
	 * 38400 8N1 is ~2.9 ms, and inside spin_lock_irqsave that is 2.9 ms
	 * with interrupts off.  The VALUES are the ones sampled inside the
	 * lock, so the reading is unchanged; only the wait moved out.
	 *
	 * G7 is DAT immediately before the first permitted .direction_output
	 * and G8 immediately after.  Predicted equal, and equal to 0000007C --
	 * unless the board booted into the post-long-press state REG-37 caught
	 * (0000003C, bit 6 low, the LED lit), in which case G7 says so instead
	 * of it being assumed. */
	if (first) {
		rlxfw_markx("G7", rtl819x_gpio_first_out_before);
		rlxfw_markx("G8", rtl819x_gpio_first_out_after);
	}
	return 0;
}

/* .set returns void, so this cannot report a refusal to its caller.  It
 * counts instead, and the count is in /proc.  See the limitation note in the
 * file header for why omitting this op is not an option. */
static void rtl819x_gpio_set(struct gpio_chip *chip, unsigned off, int value)
{
	unsigned long flags;
	u32 dat, newdat;

	if (off >= RTL819X_GPIO_NGPIO)
		return;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (!((1u << off) & rtl819x_gpio_out_mask())) {
		rtl819x_gpio_n_set_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return;
	}

	/* No CNR check here, deliberately, and the asymmetry with
	 * .direction_output is the point: gpiolib will not reach this op
	 * without a direction_output having succeeded first (a consumer that
	 * has not set a direction has nothing to set a value on), so the CNR
	 * reading has already been taken on this line in this boot.  Repeating
	 * it would cost an uncached read on the sysfs write path -- the one
	 * path a human drives at speed -- to re-answer a question whose answer
	 * cannot change without a CNR write, and this driver never writes CNR.
	 * ⚠️ That reasoning is about THIS driver: if CNR ever becomes writable
	 * from anywhere, this comment is the thing that stops being true. */
	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_state_check(dat);
	newdat = value ? (dat | (1u << off)) : (dat & ~(1u << off));
	rtl819x_gpio_wr(RTL819X_PABCD_DAT, newdat);
	rtl819x_gpio_n_writes++;
	rtl819x_gpio_state_note(newdat);
	rtl819x_gpio_n_set_ok++;
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
}

static struct gpio_chip rtl819x_gpio_chip = {
	/* Named for the REGISTER and not for a port letter, because which of
	 * A/B/C/D bit 5 belongs to has never been measured here.  See "WHAT
	 * THIS FILE DOES NOT ESTABLISH" 1. */
	.label			= "rtl819x-pabcd",
	.owner			= THIS_MODULE,
	.request		= rtl819x_gpio_request,
	.free			= rtl819x_gpio_free,
	.direction_input	= rtl819x_gpio_direction_input,
	.get			= rtl819x_gpio_get,
	.direction_output	= rtl819x_gpio_direction_output,
	.set			= rtl819x_gpio_set,
	.to_irq			= NULL,		/* see NOT ESTABLISHED 3 */
	.base			= 0,
	.ngpio			= RTL819X_GPIO_NGPIO,
	.can_sleep		= 0,
};

/* ------------------------------------------------------------------------
 * /proc/rtl819x-gpio
 * ------------------------------------------------------------------------ */

static int rtl819x_gpio_read_proc(char *page, char **start, off_t off,
				  int count, int *eof, void *data)
{
	unsigned long flags;
	unsigned long n_chk, n_foreign;
	u32 cnr, dir, dat, locked, s_last, f_first;
	int s_known, f_seen;
	int len = 0;

	/* 🔴 READING THIS FILE IS AN OBSERVATION, NOT A REPORT OF ONE.  The
	 * detector samples (notes/gpio-driver.md § 6.1), so `cat` IS a sample
	 * -- § 6.2's positive control is the button held for ~10 s while this
	 * file is read in a loop.  Everything is taken under the lock so the
	 * three live words, the comparison they feed and the counters printed
	 * from them are one snapshot rather than several. */
	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	cnr = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_state_check(dat);
	locked	  = rtl819x_gpio_out_locked;
	s_known	  = rtl819x_gpio_state_known;
	s_last	  = rtl819x_gpio_state_last;
	n_chk	  = rtl819x_gpio_n_state_chk;
	n_foreign = rtl819x_gpio_n_state_foreign;
	f_seen	  = rtl819x_gpio_foreign_seen;
	f_first	  = rtl819x_gpio_foreign_first;
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);

	len += sprintf(page + len, "version %s\n", RTL819X_GPIO_VERSION);
	len += sprintf(page + len, "added %d\n", rtl819x_gpio_added);
	len += sprintf(page + len, "add_rc %d\n", rtl819x_gpio_add_rc);
	len += sprintf(page + len, "base %d\n", rtl819x_gpio_chip.base);
	len += sprintf(page + len, "ngpio %u\n",
		       (unsigned)rtl819x_gpio_chip.ngpio);

	/* live */
	len += sprintf(page + len, "cnr %08X\n", cnr);
	len += sprintf(page + len, "dir %08X\n", dir);
	len += sprintf(page + len, "dat %08X\n", dat);

	/* latched at subsys_initcall, so a later reader can see whether the
	 * port moved between boot and now without having captured the boot */
	len += sprintf(page + len, "boot_cnr %08X\n", rtl819x_gpio_boot_cnr);
	len += sprintf(page + len, "boot_dir %08X\n", rtl819x_gpio_boot_dir);
	len += sprintf(page + len, "boot_dat %08X\n", rtl819x_gpio_boot_dat);

	/* agreement with the 2026-08-24 readings, as 1/0 rather than prose */
	len += sprintf(page + len, "cnr_as_spec %d\n",
		       cnr == RTL819X_GPIO_CNR_EXPECT);
	len += sprintf(page + len, "dir_as_spec %d\n",
		       dir == RTL819X_GPIO_DIR_EXPECT);

	/* the button, both ways round.  raw is the pin, level is REG-28's
	 * active-low reading applied once, here, for a human. */
	len += sprintf(page + len, "btn_raw %d\n",
		       (int)((dat >> RTL819X_GPIO_BUTTON) & 1u));
	len += sprintf(page + len, "btn_pressed %d\n",
		       (int)(((dat >> RTL819X_GPIO_BUTTON) & 1u) ? 0 : 1));

	len += sprintf(page + len, "known_mask %08X\n",
		       (u32)RTL819X_GPIO_KNOWN_MASK);
	len += sprintf(page + len, "allow_out_mask %08X\n",
		       (u32)RTL819X_GPIO_ALLOW_OUT_MASK);
	/* Three fields and not one, because the runtime mask and the compiled
	 * one answer different questions and a reader must not have to AND
	 * them in their head. */
	len += sprintf(page + len, "out_locked %08X\n", locked);
	len += sprintf(page + len, "out_effective %08X\n",
		       (u32)RTL819X_GPIO_ALLOW_OUT_MASK & ~locked);

	len += sprintf(page + len, "n_get %lu\n", rtl819x_gpio_n_get);
	len += sprintf(page + len, "n_req_ok %lu\n", rtl819x_gpio_n_req_ok);
	len += sprintf(page + len, "n_req_no %lu\n", rtl819x_gpio_n_req_no);
	len += sprintf(page + len, "n_dirin_ok %lu\n", rtl819x_gpio_n_dirin_ok);
	len += sprintf(page + len, "n_dirin_no %lu\n", rtl819x_gpio_n_dirin_no);
	len += sprintf(page + len, "n_dirout_ok %lu\n", rtl819x_gpio_n_dirout_ok);
	len += sprintf(page + len, "n_dirout_no %lu\n", rtl819x_gpio_n_dirout_no);
	len += sprintf(page + len, "n_set_ok %lu\n", rtl819x_gpio_n_set_ok);
	len += sprintf(page + len, "n_set_no %lu\n", rtl819x_gpio_n_set_no);

	/* 🔴 1.0's comment here was "THE NUMBER THIS DRIVER EXISTS TO KEEP AT
	 * ZERO."  It is not zero on this image and the change is R5-7 itself.
	 * notes/gpio-driver.md § 7 predicts exactly 2 after probe, both of
	 * them writing a value the register already held. */
	len += sprintf(page + len, "n_writes %lu\n", rtl819x_gpio_n_writes);

	/* The foreign-write detector.  n_state_chk is what makes the zero
	 * readable: a zero divergence count beside a zero comparison count is
	 * an instrument that never ran, and those two are not the same
	 * reading. */
	len += sprintf(page + len, "state_known %d\n", s_known);
	len += sprintf(page + len, "state_last %08X\n", s_last);
	len += sprintf(page + len, "n_state_chk %lu\n", n_chk);
	len += sprintf(page + len, "n_state_foreign %lu\n", n_foreign);
	len += sprintf(page + len, "foreign_seen %d\n", f_seen);
	len += sprintf(page + len, "foreign_first %08X\n", f_first);

	len += sprintf(page + len, "probed04 %d\n", rtl819x_gpio_probed04);
	len += sprintf(page + len, "val04 %08X\n", rtl819x_gpio_val04);

	*eof = 1;
	return len;
}

/* `claim` / `release` go through gpiolib rather than calling this driver's
 * own ops, so what they exercise is the path a real consumer takes. */
static int rtl819x_gpio_verb_claim(void)
{
	return gpio_request(rtl819x_gpio_chip.base + RTL819X_GPIO_BUTTON,
			    "rtl819x-gpio button");
}

static int rtl819x_gpio_verb_release(void)
{
	gpio_free(rtl819x_gpio_chip.base + RTL819X_GPIO_BUTTON);
	return 0;
}

/* THE GUARD'S POSITIVE CONTROL, and the reason it is a verb.
 *
 * RTL819X_GPIO_ALLOW_OUT_MASK is 0, so the output path can never run on this
 * image -- which means nothing would ever observe it refusing.  A guard that
 * has only been reasoned about is not a guard that has been tested.  This
 * verb calls gpio_direction_output() through gpiolib on a named line,
 * snapshots the three registers before and after, and reports both the errno
 * and whether any of the three moved.  Expected: -EPERM (or -EINVAL from the
 * framework), and all three words byte-identical. */
static int rtl819x_gpio_verb_tryout(const char *arg)
{
	unsigned long line;
	u32 a[3], b[3];
	int rc;
	char *end;

	line = simple_strtoul(arg, &end, 0);
	if (end == arg || line >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	a[0] = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	a[1] = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	a[2] = rtl819x_gpio_rd(RTL819X_PABCD_DAT);

	rc = gpio_direction_output(rtl819x_gpio_chip.base + line, 0);

	b[0] = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	b[1] = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	b[2] = rtl819x_gpio_rd(RTL819X_PABCD_DAT);

	/* On the wire, so the reading survives without a shell and lands in
	 * the same capture as the boot marks. */
	rlxfw_markx("G-TRYRC", (unsigned)rc);
	rlxfw_markx("G-TRYCNR", a[0] ^ b[0]);
	rlxfw_markx("G-TRYDIR", a[1] ^ b[1]);
	rlxfw_markx("G-TRYDAT", a[2] ^ b[2]);

	/* A refusal is the expected outcome, so it is not an error of the
	 * verb.  The verb succeeded in asking. */
	return 0;
}

/* Reading the unnamed word at +0x04 is a typed act because a read-to-clear
 * status register is a write in effect, and nothing here knows what +0x04
 * is.  It is never read at boot. */
static int rtl819x_gpio_verb_probe04(void)
{
	rtl819x_gpio_val04 = rtl819x_gpio_rd(RTL819X_PABCD_UNK04);
	rtl819x_gpio_probed04 = 1;
	rlxfw_markx("G-UNK04", rtl819x_gpio_val04);
	return 0;
}

/* `lock N` takes a line out of the runtime mask; `unlock N` puts it back.
 *
 * Neither can grant output on a line RTL819X_GPIO_ALLOW_OUT_MASK does not
 * carry: `unlock` refuses such a line with -EPERM rather than silently doing
 * nothing, so a card that types `unlock 5` gets a reading either way.  `lock`
 * accepts any valid line, because taking away a permission that does not exist
 * is harmless and refusing it would make the two verbs asymmetric for no
 * measurable reason.
 *
 * 🟢 THESE TWO ARE THE GUARD'S TWO-SIDED TEST, which 1.0 could not run.  With
 * the compiled mask at 0 the only observable outcome was a refusal, and a
 * guard that has only ever been seen refusing is a wall.  In one boot:
 * `lock 6` then a sysfs brightness write must leave DAT unmoved, `unlock 6`
 * then the same write must move it.  notes/gpio-driver.md § 7 ②. */
static int rtl819x_gpio_verb_lock(const char *arg, int set)
{
	unsigned long line;
	unsigned long flags;
	char *end;

	line = simple_strtoul(arg, &end, 0);
	if (end == arg || line >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	if (!set && !((1u << line) & RTL819X_GPIO_ALLOW_OUT_MASK))
		return -EPERM;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (set)
		rtl819x_gpio_out_locked |= (1u << line);
	else
		rtl819x_gpio_out_locked &= ~(1u << line);
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
	return 0;
}

static int rtl819x_gpio_write_proc(struct file *file, const char __user *buffer,
				   unsigned long count, void *data)
{
	char buf[24];
	unsigned long n = count;
	int ret;

	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "claim"))
		ret = rtl819x_gpio_verb_claim();
	else if (!strcmp(buf, "release"))
		ret = rtl819x_gpio_verb_release();
	else if (!strncmp(buf, "tryout ", 7))
		ret = rtl819x_gpio_verb_tryout(buf + 7);
	else if (!strncmp(buf, "unlock ", 7))
		ret = rtl819x_gpio_verb_lock(buf + 7, 0);
	else if (!strncmp(buf, "lock ", 5))
		ret = rtl819x_gpio_verb_lock(buf + 5, 1);
	else if (!strcmp(buf, "lock")) {
		/* Bare `lock` keeps 1.0's meaning -- NOTHING may output -- so
		 * the spelling a card already knows still does what it said.
		 * ~0 and not ALLOW_OUT_MASK, because the field should read as
		 * "everything", which is what was typed. */
		unsigned long f;

		spin_lock_irqsave(&rtl819x_gpio_lock, f);
		rtl819x_gpio_out_locked = ~0u;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, f);
		ret = 0;
	} else if (!strcmp(buf, "probe04"))
		ret = rtl819x_gpio_verb_probe04();
	else if (!strcmp(buf, "sample")) {
		/* One .get through gpiolib, so n_get moves and a reader can
		 * tell a live read from a cached dump. */
		ret = gpio_get_value(rtl819x_gpio_chip.base +
				     RTL819X_GPIO_BUTTON);
		rlxfw_markx("G-SAMPLE", (unsigned)ret);
		ret = 0;
	} else
		return -EINVAL;

	return ret ? ret : (int)count;
}

/* ------------------------------------------------------------------------
 * Registration.
 *
 * subsys_initcall, for one reason and not by convention: a gpio_chip has to
 * exist before any consumer asks for a line, and R5-7 (leds-gpio) and R5-8
 * (gpio-keys) are both device_initcall-class consumers.  Nothing here needs
 * ioremap or an allocator, so there is no lower bound of its own.
 * ------------------------------------------------------------------------ */

static int __init rtl819x_gpio_init(void)
{
	struct proc_dir_entry *pde;
	u32 cnr, dir, dat;

	rlxfw_mark("G0");

	/* Latched before anything is registered, so the boot reading is of
	 * the port as the loader left it and not as this driver found it
	 * after gpiolib touched anything. */
	cnr = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_boot_cnr = cnr;
	rtl819x_gpio_boot_dir = dir;
	rtl819x_gpio_boot_dat = dat;

	/* G1 and G2 are the NEGATIVE control of the button experiment: they
	 * must be identical on every boot of both populations.  G3 is the
	 * signal.  G5 is the same bit as a level, printed separately so a
	 * reader does not have to do the shift. */
	rlxfw_markx("G1", cnr);
	rlxfw_markx("G2", dir);
	rlxfw_markx("G3", dat);

	rtl819x_gpio_add_rc = gpiochip_add(&rtl819x_gpio_chip);
	rtl819x_gpio_added = (rtl819x_gpio_add_rc == 0);
	rlxfw_markx("G4", (unsigned)rtl819x_gpio_add_rc);

	rlxfw_markx("G5", (dat >> RTL819X_GPIO_BUTTON) & 1u);

	if (rtl819x_gpio_add_rc)
		return rtl819x_gpio_add_rc;

	pde = create_proc_entry(RTL819X_GPIO_PROC_NAME, 0644, NULL);
	if (!pde) {
		/* The chip stays registered.  Losing /proc costs the verbs,
		 * not the gpiochip, and tearing down a working controller
		 * because its debug interface failed would be the worse of
		 * the two outcomes. */
		rlxfw_mark("G6-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_gpio_read_proc;
	pde->write_proc = rtl819x_gpio_write_proc;
	rlxfw_mark("G6");

	return 0;
}

subsys_initcall(rtl819x_gpio_init);
