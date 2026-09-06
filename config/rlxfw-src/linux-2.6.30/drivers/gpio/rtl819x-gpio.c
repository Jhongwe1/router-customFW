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
 * THIS DRIVER WRITES NOTHING TO THE SILICON, AND THAT IS THE IMPLEMENTATION
 * RATHER THAN AN ABUNDANCE OF CAUTION.
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
 *     outside RTL819X_GPIO_KNOWN_MASK, so the chip's usable width is one.
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

#define RTL819X_GPIO_VERSION	"rtl819x-gpio 1.0"

#define RTL819X_GPIO_PHYS	0x18003500	/* 0xB8003500 through KSEG1 */

#define RTL819X_PABCD_CNR	0x00		/* MAP-09, REG-26 */
#define RTL819X_PABCD_UNK04	0x04		/* unnamed; see `probe04` */
#define RTL819X_PABCD_DIR	0x08		/* MAP-09, REG-27 */
#define RTL819X_PABCD_DAT	0x0C		/* MAP-09, REG-28 */

#define RTL819X_GPIO_NGPIO	32
#define RTL819X_GPIO_BUTTON	5		/* BRD-05 */

/* The one line this die is known to carry as a GPIO.  REG-26: bit 5 is the
 * only cleared bit of CNR, and the loader is what cleared it. */
#define RTL819X_GPIO_KNOWN_MASK	(1u << RTL819X_GPIO_BUTTON)

/* Zero, and the long comment at the top of this file is the reason.  This is
 * the single place that changes if a line ever acquires a measured safe
 * output state. */
#define RTL819X_GPIO_ALLOW_OUT_MASK	0u

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
static int  rtl819x_gpio_unlocked = -1;	/* line unlocked for output, or -1 */

static u32  rtl819x_gpio_boot_cnr;	/* latched at subsys_initcall */
static u32  rtl819x_gpio_boot_dir;
static u32  rtl819x_gpio_boot_dat;

static unsigned long rtl819x_gpio_n_get;	/* .get calls */
static unsigned long rtl819x_gpio_n_req_ok;	/* .request accepted */
static unsigned long rtl819x_gpio_n_req_no;	/* .request refused */
static unsigned long rtl819x_gpio_n_dirin_ok;
static unsigned long rtl819x_gpio_n_dirin_no;
static unsigned long rtl819x_gpio_n_dirout_no;	/* .direction_output refused */
static unsigned long rtl819x_gpio_n_set_no;	/* .set refused (counted, void) */
static unsigned long rtl819x_gpio_n_writes;	/* actual register writes.  0. */

/* The unnamed word at +0x04 is not read at boot.  A read is normally free,
 * but a read-to-clear status register is a write in effect and nothing here
 * knows what +0x04 is.  `probe04` makes reading it a typed act. */
static int  rtl819x_gpio_probed04;
static u32  rtl819x_gpio_val04;

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
	u32 dat;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_n_get++;

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
	u32 dir;

	if (off >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (!((1u << off) & RTL819X_GPIO_ALLOW_OUT_MASK) ||
	    rtl819x_gpio_unlocked != (int)off) {
		rtl819x_gpio_n_dirout_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return -EPERM;
	}

	/* Unreachable while RTL819X_GPIO_ALLOW_OUT_MASK is 0.  It is written
	 * out rather than left as a `return -EPERM;` so that the day a line
	 * acquires a measured safe output state, the change is one constant
	 * and not a new code path written under time pressure at a bench. */
	dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	rtl819x_gpio_wr(RTL819X_PABCD_DAT,
			value ? (rtl819x_gpio_rd(RTL819X_PABCD_DAT) | (1u << off))
			      : (rtl819x_gpio_rd(RTL819X_PABCD_DAT) & ~(1u << off)));
	rtl819x_gpio_wr(RTL819X_PABCD_DIR, dir | (1u << off));
	rtl819x_gpio_n_writes += 2;
	spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
	return 0;
}

/* .set returns void, so this cannot report a refusal to its caller.  It
 * counts instead, and the count is in /proc.  See the limitation note in the
 * file header for why omitting this op is not an option. */
static void rtl819x_gpio_set(struct gpio_chip *chip, unsigned off, int value)
{
	unsigned long flags;
	u32 dat;

	if (off >= RTL819X_GPIO_NGPIO)
		return;

	spin_lock_irqsave(&rtl819x_gpio_lock, flags);
	if (!((1u << off) & RTL819X_GPIO_ALLOW_OUT_MASK) ||
	    rtl819x_gpio_unlocked != (int)off) {
		rtl819x_gpio_n_set_no++;
		spin_unlock_irqrestore(&rtl819x_gpio_lock, flags);
		return;
	}

	dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	rtl819x_gpio_wr(RTL819X_PABCD_DAT,
			value ? (dat | (1u << off)) : (dat & ~(1u << off)));
	rtl819x_gpio_n_writes++;
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
	u32 cnr = rtl819x_gpio_rd(RTL819X_PABCD_CNR);
	u32 dir = rtl819x_gpio_rd(RTL819X_PABCD_DIR);
	u32 dat = rtl819x_gpio_rd(RTL819X_PABCD_DAT);
	int len = 0;

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
	len += sprintf(page + len, "unlocked %d\n", rtl819x_gpio_unlocked);

	len += sprintf(page + len, "n_get %lu\n", rtl819x_gpio_n_get);
	len += sprintf(page + len, "n_req_ok %lu\n", rtl819x_gpio_n_req_ok);
	len += sprintf(page + len, "n_req_no %lu\n", rtl819x_gpio_n_req_no);
	len += sprintf(page + len, "n_dirin_ok %lu\n", rtl819x_gpio_n_dirin_ok);
	len += sprintf(page + len, "n_dirin_no %lu\n", rtl819x_gpio_n_dirin_no);
	len += sprintf(page + len, "n_dirout_no %lu\n", rtl819x_gpio_n_dirout_no);
	len += sprintf(page + len, "n_set_no %lu\n", rtl819x_gpio_n_set_no);

	/* THE NUMBER THIS DRIVER EXISTS TO KEEP AT ZERO. */
	len += sprintf(page + len, "n_writes %lu\n", rtl819x_gpio_n_writes);

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

static int rtl819x_gpio_verb_unlock(const char *arg)
{
	unsigned long line;
	char *end;

	line = simple_strtoul(arg, &end, 0);
	if (end == arg || line >= RTL819X_GPIO_NGPIO)
		return -EINVAL;

	/* -EPERM for every line while the mask is 0, and the /proc dump
	 * carries allow_out_mask so the refusal is legible without this
	 * source. */
	if (!((1u << line) & RTL819X_GPIO_ALLOW_OUT_MASK))
		return -EPERM;

	rtl819x_gpio_unlocked = (int)line;
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
		ret = rtl819x_gpio_verb_unlock(buf + 7);
	else if (!strcmp(buf, "lock")) {
		rtl819x_gpio_unlocked = -1;
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
