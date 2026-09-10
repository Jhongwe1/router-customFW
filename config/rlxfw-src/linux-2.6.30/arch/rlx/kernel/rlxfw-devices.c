/*
 * rlxfw-devices -- the board's platform devices.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-7, 2026-09-10, fifty-third segment.  It is
 * staged into arch/rlx/kernel/ by tools/rlxfw-marks.py from config/rlxfw-src/;
 * config/rlxfw-marks.tsv carries the one Kbuild line that links it.
 *
 * ------------------------------------------------------------------------
 * WHY THIS FILE EXISTS AT ALL, WHICH IS A DECISION AND NOT A CONVENTION
 * ------------------------------------------------------------------------
 *
 * R5-7 drives an LED through UPSTREAM leds-gpio rather than through a driver
 * of mine.  notes/gpio-driver.md 9 gives the reason and it is evidential:
 * an UNMODIFIED upstream consumer binding to my gpio_chip is evidence a
 * driver I wrote myself cannot produce.  leds-gpio's platform binding needs a
 * platform_device carrying gpio_led_platform_data, and somebody has to
 * register it.  That somebody is a BOARD file, which is what this is.
 *
 * Three homes were on the table and notes/gpio-driver.md 9.1 picks this one
 * on three measurements rather than on taste:
 *
 *   A  arch/rlx/kernel/          <- here
 *   B  inside rtl819x-gpio.c     a GPIO CONTROLLER instantiating its own
 *                                CONSUMERS is a layering inversion, and it
 *                                would make the LED's existence a property
 *                                of the chip driver rather than of the board
 *   C  drivers/leds/...          the path would lie: this registers a
 *                                platform device and is not an LED driver
 *
 * 🔴 AND NOT arch/rlx/bsp/, WHICH IS WHERE A BOARD FILE BELONGS.  量
 * 2026-09-10, every subdirectory of arch/rlx: `bsp` is the ONLY symlink --
 * docs/interrupt-map.md 6.1 resolved it as -> ../../../target/bsp ->
 * boards/rtl8196e/bsp -- so staging a file "into arch/rlx/bsp/" writes into
 * the vendor's shared board tree, and tools/rlxfw-marks.py refuses any path
 * under src-vendor/ by construction.  boot, configs, fw, include, kernel,
 * lib, mm, oprofile and pci are all real directories.
 *
 * 🟢 arch/rlx/Makefile:117 is `core-y += arch/rlx/kernel/ arch/rlx/mm/`,
 * unconditional, so a file dropped here is linked into the core with no new
 * Kconfig symbol and no `select`.  And `obj-y += NAME.o` is one of exactly
 * four forms rlxfw-marks.py will insert, so this needs no host-compat patch.
 *
 * ------------------------------------------------------------------------
 * -Werror
 * ------------------------------------------------------------------------
 *
 * arch/rlx/kernel/Makefile ends with `EXTRA_CFLAGS += -Werror`.  Every other
 * file of mine has been built under the kernel's default flags; this is the
 * first that must be warning-clean or the build stops.
 * notes/modern-kernel-port.md 9.1's C0a/C0b controls exist because kbuild
 * exits 0 and prints nothing for a file it declines to build -- here the
 * failure mode is the opposite and louder, which is the easier one to have.
 *
 * ------------------------------------------------------------------------
 * INITCALL LEVEL: arch_initcall (3)
 * ------------------------------------------------------------------------
 *
 * A platform DEVICE must exist before the platform DRIVER registers, and
 * leds-gpio's gpio_led_init is module_init -- device_initcall, level 6 --
 * in a built-in build.  Level 3 is before every level-6 entry regardless of
 * link order, so this is the one ordering in R5-7 that does NOT rest on a
 * Makefile's line numbers.  It is also before rtl819x-gpio's own
 * subsys_initcall (4), which is harmless: registering a platform device
 * touches no GPIO and asks gpiolib nothing.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/platform_device.h>
#include <linux/leds.h>

#include <linux/rlxfw-mark.h>

/* 🔴 THESE TWO #errors ARE LOAD-BEARING AND THEY CLOSE A KNOWN HOLE.
 *
 * config/rlxfw-kernel.delta declares CONFIG_NEW_LEDS, CONFIG_LEDS_CLASS,
 * CONFIG_LEDS_GPIO and CONFIG_LEDS_GPIO_PLATFORM -- but `kconfig-delta check`
 * is never invoked by tools/rlxfw-kbuild.sh (CFG-2, and it is the same shape
 * as `rlxfw-marks verify` never being run automatically).  So the delta and
 * the built .config can drift with nothing noticing.  A build that drifted
 * here would produce an image in which this file registers a platform device
 * that no driver ever binds to: the LED simply never works, /sys/class/leds
 * is empty, and NOTHING SAYS SO -- with CONFIG_PRINTK=n there is not even a
 * message.  That is the silent mode MK6's row in config/rlxfw-marks.tsv was
 * written to avoid, one layer up.
 *
 * CONFIG_LEDS_GPIO_PLATFORM is the one that is easy to miss, and it is not
 * optional decoration: 讀 drivers/leds/leds-gpio.c, the whole of
 * gpio_led_probe AND the platform_driver that carries it sit inside
 * `#ifdef CONFIG_LEDS_GPIO_PLATFORM`.  Without it leds-gpio builds, links,
 * and registers no platform driver at all.
 *
 * =y and not =m: this runs at arch_initcall and there is no module loader in
 * this image's userspace to bring a module in afterwards. */
#if !defined(CONFIG_LEDS_GPIO)
#error "rlxfw-devices.c needs CONFIG_LEDS_GPIO=y -- see config/rlxfw-kernel.delta"
#endif
#if !defined(CONFIG_LEDS_GPIO_PLATFORM)
#error "rlxfw-devices.c needs CONFIG_LEDS_GPIO_PLATFORM=y -- leds-gpio's whole platform path is #ifdef'd on it"
#endif

/* 量 BRD-13, 2026-09-09 (seating 19): PABCD bit 6 drives the SECOND of the
 * board's eight LEDs, ACTIVE LOW, polarity read at both levels with the other
 * seven LEDs as the negative control.
 *
 * The number is a BIT POSITION, not a port-letter offset.  Which of PABCD's
 * four ports bit 6 belongs to has never been measured on this die, so
 * rtl819x-gpio labels its chip `rtl819x-pabcd` and numbers its lines 0..31 by
 * bit; this consumer uses the same numbering because it is the only one that
 * has been measured.  dt/rtl8196e.dtsi says the same thing in the same
 * words. */
#define RLXFW_LED2_GPIO		6

/* The name is the one dt/rtl8196e-totolink-n150rt.dts already carries for
 * this LED, character for character, so the device tree that cannot be used
 * on 2.6.30 and the platform data that can describe the same object under one
 * name.  It becomes /sys/class/leds/n150rt:green:led2/. */
static struct gpio_led rlxfw_board_leds[] = {
	{
		.name			= "n150rt:green:led2",
		.default_trigger	= NULL,
		.gpio			= RLXFW_LED2_GPIO,
		/* 量 BRD-13.  Applied ONCE, here.  rtl819x-gpio's .get and
		 * .set deal in RAW pin levels precisely so that a polarity
		 * lives in exactly one place -- inverting in both would apply
		 * it twice and the LED would be right by accident. */
		.active_low		= 1,
		.retain_state_suspended	= 0,
	},
};

static struct gpio_led_platform_data rlxfw_board_led_pdata = {
	.num_leds	= (int)ARRAY_SIZE(rlxfw_board_leds),
	.leds		= rlxfw_board_leds,
	/* NULL, so leds-gpio leaves cdev.blink_set unset and the LED has no
	 * hardware blink.  The vendor's rtl_gpio_timer blinks this same bit
	 * from a kernel timer (量 FW-40); offering a second blink mechanism
	 * on one pin would make "which one is blinking it" a question the
	 * capture cannot answer. */
	.gpio_blink_set	= NULL,
};

/* id -1: there is one of these, so the device is `leds-gpio` and not
 * `leds-gpio.0`.  leds-gpio matches on driver.name, so either binds; -1 is
 * what makes the name in /sys/bus/platform/devices readable. */
static struct platform_device rlxfw_board_leds_dev = {
	.name	= "leds-gpio",
	.id	= -1,
	.dev	= {
		.platform_data = &rlxfw_board_led_pdata,
	},
};

/* Only the ARRAY OF POINTERS is __initdata.  The gpio_led array and the
 * platform data it points at are NOT: leds-gpio reads them at probe and the
 * driver core may reach platform_data again afterwards, and free_initmem()
 * runs after do_initcalls(). */
static struct platform_device *rlxfw_board_devices[] __initdata = {
	&rlxfw_board_leds_dev,
};

static int __init rlxfw_devices_init(void)
{
	int rc;

	/* PD0 before, PD1 with the return code after.  Two marks and not one
	 * because they separate two causes that would otherwise share a
	 * capture: PD0 with no PD1 is this initcall having been entered and
	 * not returned, which is a different failure from a non-zero rc.
	 * That is the rule config/rlxfw-marks.tsv states for adding a mark --
	 * it must separate two causes, not only say "we got further". */
	rlxfw_mark("PD0");
	rc = platform_add_devices(rlxfw_board_devices,
				  (int)ARRAY_SIZE(rlxfw_board_devices));
	rlxfw_markx("PD1", (unsigned int)rc);

	/* Returned rather than swallowed.  With CONFIG_PRINTK=n an initcall's
	 * failure is invisible to the kernel's own reporting, which is why
	 * PD1 carries the value onto the wire instead. */
	return rc;
}

arch_initcall(rlxfw_devices_init);
