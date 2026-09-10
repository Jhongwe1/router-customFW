/*
 * rlxfw-devices -- the board's platform devices.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-7, 2026-09-10, fifty-third segment; R5-8
 * added the button on 2026-09-10, fifty-fourth segment.  It is staged into
 * arch/rlx/kernel/ by tools/rlxfw-marks.py from config/rlxfw-src/;
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
 * 🔴 R5-8 IS THE SAME ARGUMENT REACHING THE OPPOSITE CONCLUSION, WHICH IS
 * WHY BOTH DEVICES BELONG IN ONE FILE.  The button's upstream consumer is
 * gpio_keys, and 量 it cannot drive this board: it calls gpio_to_irq() at
 * six sites and rtl819x-gpio has no .to_irq, so upstream's driver requests
 * the line, configures it, asks for an irq, gets -ENXIO and fails its probe.
 * So the button is driven by rtl819x-keys, a driver of mine -- and the
 * platform data it consumes is still upstream's struct gpio_keys_button,
 * unmodified, so what changed between the LED and the button is the DRIVER
 * and not the board's description of itself.  Two devices, one board file,
 * one vocabulary.
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
#include <linux/input.h>
#include <linux/gpio_keys.h>

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

/* 🔴 AND THESE FOUR ARE R5-8's, AND THEY ARE HERE RATHER THAN IN THE DRIVER
 * FOR A MEASURED REASON.
 *
 * drivers/input/keyboard/rtl819x-keys.c carries an #error on CONFIG_INPUT
 * too, and THAT ONE CANNOT FIRE.  量 drivers/Makefile:71 --
 * `obj-$(CONFIG_INPUT) += input/` -- so with INPUT unset the directory is
 * never descended into, the driver is never compiled, its #error is never
 * preprocessed, and the build is GREEN with no keys driver in the image.
 * The same holds one level down for CONFIG_INPUT_KEYBOARD, which is what
 * `obj-$(CONFIG_INPUT_KEYBOARD) += keyboard/` in drivers/input/Makefile
 * gates.  A guard inside the thing being guarded is not a guard.
 *
 * 量 arch/rlx/Makefile:117 -- `core-y += arch/rlx/kernel/ arch/rlx/mm/`,
 * unconditional -- so THIS file is compiled on every build of this
 * architecture whatever the .config says.  The same four lines placed here
 * are a hard build failure.  That is the difference between the LEDS block
 * above (whose symbols gate a directory that drivers/Makefile:94 also gates,
 * so the same argument applies to it) and a witness read after the fact.
 *
 * CONFIG_INPUT_EVDEV is the fourth and it is NOT a build dependency: the
 * driver compiles, links and registers without it.  It is here because
 * without it the device never polls.  讀 drivers/input/input-polldev.c: the
 * poll work is queued only by input_open_polled_device(), which is
 * input_dev->open, which the input core calls when a HANDLER opens the
 * device.  量, the handlers in this drop that would connect to a key-only
 * device and can open one: evdev (drivers/input/evdev.c:190, on the first
 * userspace open of /dev/input/eventN), evbug (drivers/input/evbug.c:63, at
 * connect) and the VT keyboard handler (drivers/char/keyboard.c, needs
 * CONFIG_VT, which this image does not have).  mousedev and joydev do not
 * match a device with only EV_KEY; apm-power needs APM_EMULATION and
 * rfkill-input needs rfkill, and neither is in this image.  ⚠️ That list is
 * an enumeration of THIS drop and would have to be retaken on another.
 *
 * With none of the three the image ships a keys driver that registers, opens
 * a /proc file, and reports every counter as 0 for ever -- and with
 * CONFIG_PRINTK=n there is not one message about it.  That is the silent
 * mode this whole block exists for, so the condition is written as the
 * disjunction rather than as CONFIG_INPUT_EVDEV alone. */
#if !defined(CONFIG_INPUT)
#error "rlxfw-devices.c needs CONFIG_INPUT=y -- drivers/Makefile:71 gates the whole directory on it"
#endif
#if !defined(CONFIG_INPUT_KEYBOARD)
#error "rlxfw-devices.c needs CONFIG_INPUT_KEYBOARD=y -- it is what descends into drivers/input/keyboard/, where rtl819x-keys.c is staged"
#endif
#if !defined(CONFIG_INPUT_POLLDEV)
#error "rlxfw-devices.c needs CONFIG_INPUT_POLLDEV=y -- rtl819x-keys links against input_register_polled_device"
#endif
#if !defined(CONFIG_INPUT_EVDEV) && !defined(CONFIG_INPUT_EVBUG) && !defined(CONFIG_VT)
#error "rlxfw-devices.c needs an input handler that can OPEN a device -- without one input-polldev never queues a poll and rtl819x-keys reads 0 for ever"
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

/* ------------------------------------------------------------------------
 * R5-8: the reset button.
 * ------------------------------------------------------------------------ */

/* 量 BRD-05, and it has been read from both sides.  PABCD bit 5 is the reset
 * button, ACTIVE LOW -- the pin reads 1 at rest and 0 while it is held.  The
 * number is a BIT POSITION for the same reason RLXFW_LED2_GPIO is: which of
 * PABCD's four ports it belongs to has never been measured on this die. */
#define RLXFW_RESET_GPIO	5

/* 讀 include/linux/input.h:511, `#define KEY_RESTART 0x198`.  It is the code
 * every GPIO reset button in mainline reports and it is in THIS drop --
 * checked, because KEY_WPS_BUTTON, the other candidate, is NOT: it arrives in
 * 2.6.32 and a board file naming it would not compile here.
 *
 * ⚠️ THE CODE IS A LABEL AND NOTHING IN THIS IMAGE ACTS ON IT.  There is no
 * keymap, no VT and no userspace daemon; the value's whole job is to be the
 * number that appears in /dev/input/event0 and in /proc/rtl819x-keys, so that
 * a reader can tell this button's event from another button's.  What the
 * board DOES on a long press is still the vendor's rtl_gpio_timer writing
 * default_flag (量 FW-40), and this driver changes none of that. */
static struct gpio_keys_button rlxfw_board_keys[] = {
	{
		.code			= KEY_RESTART,
		.gpio			= RLXFW_RESET_GPIO,
		/* 量 BRD-05.  Applied ONCE, in the driver's poll, for the
		 * reason the LED's active_low is applied once: rtl819x-gpio's
		 * .get deals in RAW pin levels so a polarity lives in exactly
		 * one place. */
		.active_low		= 1,
		.desc			= "reset",
		.type			= EV_KEY,
		/* 0.  There is no wakeup path on this SoC and rtl819x-keys
		 * REFUSES a non-zero value here rather than ignoring it, so
		 * this field is load-bearing in the negative direction. */
		.wakeup			= 0,
		/* Milliseconds.  The driver turns it into a count of
		 * consecutive equal polls -- ceil(100 / poll_ms), so 2 at the
		 * compiled-in 50 ms -- and prints the count as b0_need, so
		 * the conversion is checkable rather than assumed.
		 * 🔴 100 ms is a GUESS.  Nothing has measured this button's
		 * bounce; the driver's event ring is what will measure it,
		 * and b0_n_bounce is the counter that says whether the guess
		 * was doing any work at all. */
		.debounce_interval	= 100,
	},
};

static struct gpio_keys_platform_data rlxfw_board_keys_pdata = {
	.buttons	= rlxfw_board_keys,
	.nbuttons	= (int)ARRAY_SIZE(rlxfw_board_keys),
	/* 0.  EV_REP would make the input core synthesise repeats from a held
	 * key, which on a polled device would be a second source of events
	 * with no pin transition behind them -- and `n_report` beside
	 * `n_press` is precisely the reading that would stop meaning
	 * anything. */
	.rep		= 0,
};

/* 🔴 THE NAME IS THE EXPERIMENT.  This is upstream's
 * `struct gpio_keys_platform_data`, unmodified, describing this board's
 * button in upstream's own vocabulary -- so the only thing that decides
 * which driver gets it is this string.  `gpio-keys` would hand it to
 * drivers/input/keyboard/gpio_keys.c, which on this SoC requests the line,
 * sets it to input, calls gpio_to_irq(), gets -ENXIO out of rtl819x-gpio's
 * .to_irq being NULL, frees the line and fails its probe (讀 gpio_keys.c
 * :119-142).  `rtl819x-keys` hands it to a driver that makes the same call,
 * records the same answer as mark K4, and then polls.  One board
 * description, two drivers, and the one that cannot work fails for a reason
 * that belongs to the silicon.
 *
 * ⚠️ gpio_keys is NOT in this image and that is a decision with a cost.  Two
 * consumers of one line would make the order of the two probes matter, and
 * that order rests on device_initcall link order -- exactly what this file's
 * arch_initcall comment says it will not rest on.  So the comparison lives
 * in a control BUILD (量, cells k8c1/k8c2) and in mark K4, not on the bus. */
static struct platform_device rlxfw_board_keys_dev = {
	.name	= "rtl819x-keys",
	.id	= -1,
	.dev	= {
		.platform_data = &rlxfw_board_keys_pdata,
	},
};

/* Only the ARRAY OF POINTERS is __initdata.  The gpio_led and
 * gpio_keys_button arrays and the platform data that point at them are NOT:
 * leds-gpio and rtl819x-keys read them at probe, rtl819x-keys keeps a
 * pointer into pdata->buttons for the life of the driver, the driver core
 * may reach platform_data again afterwards, and free_initmem() runs after
 * do_initcalls(). */
static struct platform_device *rlxfw_board_devices[] __initdata = {
	&rlxfw_board_leds_dev,
	&rlxfw_board_keys_dev,
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
