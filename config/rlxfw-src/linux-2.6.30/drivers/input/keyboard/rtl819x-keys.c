/*
 * rtl819x-keys -- the board's buttons, polled, as a real input device.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-8, 2026-09-10, fifty-fourth segment.  It is
 * staged into drivers/input/keyboard/ by tools/rlxfw-marks.py from
 * config/rlxfw-src/; config/rlxfw-marks.tsv row MK8 carries the one Kbuild
 * line that links it.
 *
 * Version 1.0.
 *
 * ------------------------------------------------------------------------
 * WHY THIS DRIVER EXISTS WHEN gpio_keys ALREADY DOES THIS JOB
 * ------------------------------------------------------------------------
 *
 * R5-7 drove an LED through UPSTREAM leds-gpio precisely because an
 * unmodified upstream consumer binding to my gpio_chip is evidence a driver
 * of my own cannot produce.  The same reasoning applied here says: use
 * gpio_keys.  It cannot be used, and the reason is a property of this SoC
 * rather than of this tree's tidiness.
 *
 * 量 2026-09-10, over the staged baseline drop:
 *
 *   * drivers/input/keyboard/gpio_keys.c calls gpio_to_irq() at :62, :134,
 *     :175, :199, :222 and :240.  Six source sites; :62 is a BUG_ON inside
 *     the ISR.  It is an interrupt-driven driver from the ground up and has
 *     no polled path.
 *
 *   * gpio-keys-polled, which upstream added later for exactly this case, is
 *     NOT in this drop.  drivers/input/keyboard/ holds gpio_keys.c and no
 *     polled variant.
 *
 *   * arch/rlx declared gpio_to_irq() and defined it nowhere, so
 *     CONFIG_KEYBOARD_GPIO=y was a LINK failure.  config/host-compat/0006
 *     fixes that -- and the fix does not make gpio_keys usable, it moves the
 *     failure from link time to probe time with the chip's own errno in it.
 *     量, cells k8c1/k8c2, one variable (the patch present or absent):
 *     without it `undefined reference to gpio_to_irq' at four relocation
 *     sites including .text.gpio_keys_isr+0x1c; with it, rc 0.
 *
 * So this driver polls, and the negative control is not an argument in a
 * write-up: mark K4 below is THIS DRIVER making the call gpio_keys makes,
 * on the same line, in the same boot, and printing what comes back.
 *
 * ------------------------------------------------------------------------
 * WHAT IT REUSES, AND WHY THAT IS THE POINT
 * ------------------------------------------------------------------------
 *
 * Two upstream pieces are used unmodified, and neither is a convenience:
 *
 *   struct gpio_keys_platform_data   include/linux/gpio_keys.h
 *
 *     The BOARD describes its buttons in upstream's vocabulary -- code,
 *     gpio, active_low, desc, type, wakeup, debounce_interval -- so the
 *     description in arch/rlx/kernel/rlxfw-devices.c is a description an
 *     unmodified upstream driver would accept.  Inventing a private struct
 *     would have made "gpio_keys cannot drive this board" a statement about
 *     my data layout instead of about the silicon.
 *
 *   struct input_polled_dev          drivers/input/input-polldev.c
 *
 *     The polling skeleton, its workqueue and its open/close gating are
 *     upstream's.  This file supplies a poll() and nothing else about
 *     timing.  CONFIG_INPUT_POLLDEV's own help text says the symbol exists
 *     for out-of-tree drivers because in-tree ones select it; this one is
 *     staged rather than Kconfig'd, so config/rlxfw-kernel.delta declares it
 *     with a reason instead.
 *
 * 🔴 WHAT IS DELIBERATELY NOT REUSED: gpio_keys_button.wakeup.  This driver
 * refuses a non-zero wakeup at probe rather than ignoring it.  A field that
 * is accepted and silently dropped is worse than one that is rejected,
 * because the board file would then be describing behaviour that does not
 * exist and nothing would say so.
 *
 * ------------------------------------------------------------------------
 * 🔴 THE ONE THING THAT WOULD HAVE COST A POWER CYCLE
 * ------------------------------------------------------------------------
 *
 * 讀 drivers/input/input-polldev.c: the poll work is queued by
 * input_open_polled_device(), which the input core calls through
 * input_dev->open -- that is, when a HANDLER opens the device.  Nothing
 * queues it at registration.  量, which handler opens what:
 *
 *   drivers/input/evdev.c:190    input_open_device() is inside evdev_open(),
 *                                gated on `!evdev->open++`.  It runs when
 *                                USERSPACE opens /dev/input/eventN.
 *   drivers/input/evbug.c:63     input_open_device() is inside evbug_connect().
 *                                It runs at registration, always.
 *   drivers/char/keyboard.c      the same shape as evbug, and needs CONFIG_VT,
 *                                which this image does not have.
 *
 * So with no handler that opens, poll() is NEVER CALLED: the device
 * registers, /proc appears, every counter reads 0 for ever, and with
 * CONFIG_PRINTK=n nothing says why.
 *
 * The image therefore carries CONFIG_INPUT_EVDEV=y and the initramfs carries
 * /dev/input/event0, and something in userspace has to open it.  evbug was
 * REJECTED, not overlooked: it opens every device it connects to, which
 * would make the polling unconditional and destroy the three-state reading
 * this gives instead --
 *
 *     n_open 0, n_poll 0     nothing has opened the device
 *     n_open 1, n_poll > 0   it is open and the workqueue is running
 *     n_open 1, n_poll flat  it was opened and closed
 *
 * -- which is the same shape as R5-3a's line 25 appearing in
 * /proc/interrupts only between request_irq and free_irq, and it is the
 * strongest evidence available that the polling is caused by the open
 * rather than merely coincident with it.
 *
 * ------------------------------------------------------------------------
 * TIMESTAMPS, AND WHY THEY ARE jiffies
 * ------------------------------------------------------------------------
 *
 * The bench protocol for a button is a TIMED PHYSICAL ACTION -- press, hold,
 * release -- and it cannot be timed by conversation turns.  The instrument
 * has to record its own timing, so every raw edge goes into a ring with the
 * jiffies count at which it was seen and /proc prints the ring.
 *
 * jiffies is not a compromise here, it is the ceiling: 量, this image's
 * system CLOCKSOURCE is still `jiffies` (R5-3b registered a clockevent at
 * rating 300 and left the clocksource at rating 0, deliberately), so
 * getnstimeofday() has 1/HZ granularity too and buys nothing.  HZ is 100, so
 * the ring resolves 10 ms -- and the poll interval is never below one tick
 * anyway, because input-polldev converts it with msecs_to_jiffies().  A
 * polled button cannot see bounce finer than its own poll interval, and that
 * is a property of polling, not of the timestamp.
 *
 * ------------------------------------------------------------------------
 * THE /proc PAGE IS ONE PAGE, AND THAT IS A HARD LIMIT
 * ------------------------------------------------------------------------
 *
 * read_proc_t sprintf()s into a single 4,096-byte page with no bounds check
 * -- the same limit that forced rtl819x-spi 1.1's map to be two-level.  The
 * arithmetic here, written down rather than hoped:
 *
 *     fixed fields          ~34 lines x <= 30 B  =   1020 B
 *     per button            8 lines x <= 34 B x RTL819X_KEYS_MAX (4) = 1088 B
 *     event ring            RTL819X_KEYS_LOG (32) x <= 28 B         =  896 B
 *                                                            total ~ 3004 B
 *
 * Both counts are compile-time caps and both are refused at probe if the
 * board asks for more, so the bound holds for every board file this driver
 * will ever see.
 *
 * ------------------------------------------------------------------------
 * WHAT THIS DRIVER DOES NOT ESTABLISH
 * ------------------------------------------------------------------------
 *
 *  1. THAT THE BOARD HAS A GPIO INTERRUPT.  It establishes the opposite and
 *     prints it: K4 is gpio_to_irq()'s return value, read from the chip
 *     through gpiolib, on every boot.
 *
 *  2. WHICH PORT OF PABCD LINE 5 IS.  rtl819x-gpio numbers its lines 0..31
 *     by bit position because that is the only thing measured on this die;
 *     this consumer uses the same numbering for the same reason.
 *
 *  3. THAT A PRESS REACHED USERSPACE.  It counts input_report_key() calls
 *     (n_report).  Whether the input core propagated one is the core's
 *     business: it drops a repeat of a state it already holds, so
 *     n_report is an upper bound on the events a reader of
 *     /dev/input/event0 will see, and the two numbers are not the same
 *     measurement.
 *
 *  4. THAT THE VENDOR'S OWN RESET PATH IS OUT OF THE WAY.  It is not.  量
 *     FW-40: rtl_gpio_timer polls this same button from a kernel timer once
 *     a second and writes default_flag at >= 5 s.  This driver COEXISTS
 *     with it and reads the same pin; it takes gpiolib's request, which the
 *     vendor path does not use, so there is no gpiolib contention -- and
 *     there is no arbitration either.  Both are readers here; nothing in
 *     this file writes DAT.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/slab.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/jiffies.h>
#include <linux/spinlock.h>
#include <linux/platform_device.h>
#include <linux/proc_fs.h>
#include <linux/gpio.h>
#include <linux/gpio_keys.h>
#include <linux/input.h>
#include <linux/input-polldev.h>
#include <linux/module.h>

#include <linux/rlxfw-mark.h>
#include <asm/uaccess.h>

/* 🔴 WHICH OF THESE THREE CAN ACTUALLY FIRE, stated rather than left to be
 * discovered.
 *
 * CONFIG_INPUT: it CANNOT.  drivers/Makefile:71 is
 * `obj-$(CONFIG_INPUT) += input/`, so with INPUT unset this directory is
 * never descended into, this file is never compiled, and a build that has
 * quietly lost the driver is GREEN.  What covers that is MK8's `str:` witness
 * in config/rlxfw-marks.tsv, which `rlxfw-marks verify` reads out of the
 * BUILT vmlinux.  The #error is kept anyway because it costs nothing and it
 * is the correct statement of the dependency; it is simply not the guard.
 *
 * CONFIG_INPUT_POLLDEV: it CAN.  With INPUT and INPUT_KEYBOARD set, this file
 * compiles and input-polldev.o is not linked, so the failure is at link on
 * input_register_polled_device.  The #error moves that earlier and names it.
 *
 * CONFIG_GPIOLIB: it CAN, the same way -- gpio_request and friends are
 * declared by arch/rlx's header and defined only by gpiolib.c. */
#if !defined(CONFIG_INPUT)
#error "rtl819x-keys.c needs CONFIG_INPUT=y -- see config/rlxfw-kernel.delta"
#endif
#if !defined(CONFIG_INPUT_POLLDEV)
#error "rtl819x-keys.c needs CONFIG_INPUT_POLLDEV=y -- input_register_polled_device lives there"
#endif
#if !defined(CONFIG_GPIOLIB)
#error "rtl819x-keys.c needs CONFIG_GPIOLIB=y -- gpio_request is gpiolib's"
#endif

#define RTL819X_KEYS_VERSION	"1.0"
#define RTL819X_KEYS_PROC_NAME	"rtl819x-keys"
#define RTL819X_KEYS_DRV_NAME	"rtl819x-keys"

/* Compile-time caps.  Both are refused at probe rather than clamped: a board
 * file that asks for five buttons and gets four is describing a board that
 * does not exist, and the /proc page arithmetic above rests on both. */
#define RTL819X_KEYS_MAX	4
#define RTL819X_KEYS_LOG	32

/* 50 ms.  Not from platform data: struct gpio_keys_platform_data has no
 * poll-interval field, because upstream's consumer of it is interrupt
 * driven.  Extending upstream's struct was rejected -- see the header -- so
 * the interval is this driver's own and is writable through /proc, which is
 * what makes the rate a CAUSAL experiment rather than a declaration:
 * `interval 500` must divide Delta n_poll / Delta jiffies by ten, the same
 * shape as R5-3b-1's cereload ladder. */
#define RTL819X_KEYS_POLL_MS	50

/* Sentinel for "probe was never called".  A positive value: a probe that
 * runs returns 0 or a negative errno, so 1 can never be a real answer and a
 * reader does not have to know an errno to see it. */
#define RTL819X_KEYS_NOPROBE	1

/* ------------------------------------------------------------------------
 * State.  One instance; this is a board driver for a soldered-down button.
 * ------------------------------------------------------------------------ */

struct rtl819x_keys_btn {
	const struct gpio_keys_button	*b;
	int		raw_prev;	/* last raw pin level seen by poll */
	int		state;		/* debounced logical state, 1 = pressed */
	unsigned int	stable;		/* consecutive polls at raw_prev */
	unsigned int	need;		/* polls required to accept a change */
	unsigned long	n_press;
	unsigned long	n_release;
	unsigned long	n_report;
	unsigned long	n_edge;		/* raw level differed from raw_prev */
	unsigned long	n_bounce;	/* an edge that went back before `need` */
};

struct rtl819x_keys_ev {
	unsigned long	j;		/* jiffies at the poll that saw it */
	unsigned char	btn;
	unsigned char	raw;
};

static DEFINE_SPINLOCK(rtl819x_keys_lock);

static struct input_polled_dev	*rtl819x_keys_poll_dev;
static struct rtl819x_keys_btn	 rtl819x_keys_btn[RTL819X_KEYS_MAX];
static int			 rtl819x_keys_nbtn;
static const struct gpio_keys_platform_data *rtl819x_keys_pdata;

static unsigned int	rtl819x_keys_poll_ms = RTL819X_KEYS_POLL_MS;

static int		rtl819x_keys_probe_rc = RTL819X_KEYS_NOPROBE;
static int		rtl819x_keys_reg_rc = -EAGAIN;
static int		rtl819x_keys_bound;
static int		rtl819x_keys_irq_probe = RTL819X_KEYS_NOPROBE;
static int		rtl819x_keys_boot_raw = -1;

static unsigned long	rtl819x_keys_n_open;	/* flush() calls = opens */
static unsigned long	rtl819x_keys_n_poll;
static unsigned long	rtl819x_keys_j_first;	/* jiffies at the first poll */
static unsigned long	rtl819x_keys_j_last;	/* jiffies at the last poll */

/* The ring.  n_ev is the total ever recorded, so a reader can tell a ring
 * that wrapped from one that is merely full -- and n_ev_drop is what makes
 * the ring's completeness a number rather than an assumption. */
static struct rtl819x_keys_ev rtl819x_keys_log[RTL819X_KEYS_LOG];
static unsigned int	rtl819x_keys_log_head;
static unsigned long	rtl819x_keys_n_ev;
static unsigned long	rtl819x_keys_n_ev_drop;

/* ------------------------------------------------------------------------
 * The poll.
 * ------------------------------------------------------------------------ */

/* Caller holds the lock. */
static void rtl819x_keys_log_edge(int idx, int raw)
{
	struct rtl819x_keys_ev *e = &rtl819x_keys_log[rtl819x_keys_log_head];

	if (rtl819x_keys_n_ev >= RTL819X_KEYS_LOG)
		rtl819x_keys_n_ev_drop++;

	e->j   = jiffies;
	e->btn = (unsigned char)idx;
	e->raw = (unsigned char)(raw ? 1 : 0);

	rtl819x_keys_log_head = (rtl819x_keys_log_head + 1) % RTL819X_KEYS_LOG;
	rtl819x_keys_n_ev++;
}

static void rtl819x_keys_poll(struct input_polled_dev *dev)
{
	struct input_dev *input = dev->input;
	unsigned long flags;
	int i;
	/* What to report, decided under the lock and reported outside it.
	 * input_event() takes the input core's own spinlock and walks the
	 * handler list; nesting that inside this driver's lock would put a
	 * foreign lock order inside a poll that runs a hundred times a
	 * second for no gain. */
	int rep_code[RTL819X_KEYS_MAX];
	int rep_val[RTL819X_KEYS_MAX];
	int nrep = 0;

	/* The raw reads go through gpiolib, not through this driver's idea of
	 * the register, so what is exercised is the path a real consumer
	 * takes -- the same reason rtl819x-gpio's own claim/release verbs go
	 * through gpio_request(). */
	for (i = 0; i < rtl819x_keys_nbtn; i++) {
		struct rtl819x_keys_btn *k = &rtl819x_keys_btn[i];
		int raw = gpio_get_value(k->b->gpio) ? 1 : 0;
		int pressed;

		spin_lock_irqsave(&rtl819x_keys_lock, flags);

		if (raw != k->raw_prev) {
			k->n_edge++;
			if (k->stable < k->need && k->raw_prev != k->state)
				k->n_bounce++;
			rtl819x_keys_log_edge(i, raw);
			k->raw_prev = raw;
			k->stable = 0;
		} else if (k->stable < k->need) {
			k->stable++;
		}

		pressed = k->b->active_low ? !raw : raw;

		if (k->stable >= k->need && pressed != k->state) {
			k->state = pressed;
			if (pressed)
				k->n_press++;
			else
				k->n_release++;
			k->n_report++;
			rep_code[nrep] = k->b->code;
			rep_val[nrep] = pressed;
			nrep++;
		}

		spin_unlock_irqrestore(&rtl819x_keys_lock, flags);
	}

	spin_lock_irqsave(&rtl819x_keys_lock, flags);
	if (!rtl819x_keys_n_poll)
		rtl819x_keys_j_first = jiffies;
	rtl819x_keys_j_last = jiffies;
	rtl819x_keys_n_poll++;
	/* Read back every poll rather than only at probe: `interval N` may
	 * have changed it, and input-polldev re-reads dev->poll_interval on
	 * each requeue, so this is the value that is actually in force. */
	dev->poll_interval = rtl819x_keys_poll_ms;
	spin_unlock_irqrestore(&rtl819x_keys_lock, flags);

	for (i = 0; i < nrep; i++) {
		input_report_key(input, rep_code[i], rep_val[i]);
		input_sync(input);
	}
}

/* Called by input-polldev on open, before the first poll is queued.
 *
 * raw_prev is seeded from the live pin so the first poll does not read as an
 * edge.  state is deliberately NOT seeded: it stays `released`, so a button
 * already held when the device is opened reports a PRESS after the debounce
 * window instead of being silently absorbed.  Which of the two happened is
 * readable either way -- open_raw records the pin at this instant. */
static void rtl819x_keys_flush(struct input_polled_dev *dev)
{
	unsigned long flags;
	int i;
	int raw[RTL819X_KEYS_MAX];

	for (i = 0; i < rtl819x_keys_nbtn; i++)
		raw[i] = gpio_get_value(rtl819x_keys_btn[i].b->gpio) ? 1 : 0;

	spin_lock_irqsave(&rtl819x_keys_lock, flags);
	for (i = 0; i < rtl819x_keys_nbtn; i++) {
		rtl819x_keys_btn[i].raw_prev = raw[i];
		rtl819x_keys_btn[i].stable = 0;
	}
	rtl819x_keys_n_open++;
	spin_unlock_irqrestore(&rtl819x_keys_lock, flags);
}

/* ------------------------------------------------------------------------
 * /proc/rtl819x-keys
 * ------------------------------------------------------------------------ */

static int rtl819x_keys_read_proc(char *page, char **start, off_t off,
				  int count, int *eof, void *data)
{
	unsigned long flags;
	int len = 0;
	int i;
	int live_irq;
	int raw_now[RTL819X_KEYS_MAX];

	/* Live, every read.  This is the negative control and it is worth
	 * more read now than latched at probe: if it ever stops being -ENXIO
	 * the chip has grown a .to_irq and that is the finding. */
	live_irq = rtl819x_keys_nbtn ?
		gpio_to_irq(rtl819x_keys_btn[0].b->gpio) : -ENODEV;
	for (i = 0; i < rtl819x_keys_nbtn; i++)
		raw_now[i] = gpio_get_value(rtl819x_keys_btn[i].b->gpio) ? 1 : 0;

	len += sprintf(page + len, "version %s\n", RTL819X_KEYS_VERSION);
	len += sprintf(page + len, "bound %d\n", rtl819x_keys_bound);
	len += sprintf(page + len, "reg_rc %d\n", rtl819x_keys_reg_rc);
	len += sprintf(page + len, "probe_rc %d\n", rtl819x_keys_probe_rc);
	len += sprintf(page + len, "nbuttons %d\n", rtl819x_keys_nbtn);
	len += sprintf(page + len, "max_buttons %d\n", RTL819X_KEYS_MAX);
	len += sprintf(page + len, "log_slots %d\n", RTL819X_KEYS_LOG);

	/* THE NEGATIVE CONTROL, both times it was taken.  irq_probe is what
	 * gpio_keys would have seen at its own probe; irq_live is the same
	 * question asked now. */
	len += sprintf(page + len, "irq_probe %d\n", rtl819x_keys_irq_probe);
	len += sprintf(page + len, "irq_live %d\n", live_irq);
	len += sprintf(page + len, "enxio %d\n", -ENXIO);

	/* Whether a handler that can open the device is even in this image.
	 * n_open 0 with evdev_built 0 is a different situation from n_open 0
	 * with evdev_built 1, and a reader must not have to guess which. */
#ifdef CONFIG_INPUT_EVDEV
	len += sprintf(page + len, "evdev_built 1\n");
#else
	len += sprintf(page + len, "evdev_built 0\n");
#endif
#ifdef CONFIG_INPUT_EVBUG
	len += sprintf(page + len, "evbug_built 1\n");
#else
	len += sprintf(page + len, "evbug_built 0\n");
#endif

	spin_lock_irqsave(&rtl819x_keys_lock, flags);
	len += sprintf(page + len, "poll_ms %u\n", rtl819x_keys_poll_ms);
	len += sprintf(page + len, "poll_jiffies %u\n",
		       (unsigned)msecs_to_jiffies(rtl819x_keys_poll_ms));
	len += sprintf(page + len, "hz %d\n", HZ);
	len += sprintf(page + len, "n_open %lu\n", rtl819x_keys_n_open);
	len += sprintf(page + len, "n_poll %lu\n", rtl819x_keys_n_poll);
	len += sprintf(page + len, "j_first %lu\n", rtl819x_keys_j_first);
	len += sprintf(page + len, "j_last %lu\n", rtl819x_keys_j_last);
	len += sprintf(page + len, "j_now %lu\n", jiffies);
	len += sprintf(page + len, "n_ev %lu\n", rtl819x_keys_n_ev);
	len += sprintf(page + len, "n_ev_drop %lu\n", rtl819x_keys_n_ev_drop);
	len += sprintf(page + len, "boot_raw %d\n", rtl819x_keys_boot_raw);

	for (i = 0; i < rtl819x_keys_nbtn; i++) {
		const struct rtl819x_keys_btn *k = &rtl819x_keys_btn[i];

		len += sprintf(page + len, "b%d_gpio %d\n", i, k->b->gpio);
		len += sprintf(page + len, "b%d_code %d\n", i, k->b->code);
		len += sprintf(page + len, "b%d_active_low %d\n",
			       i, k->b->active_low);
		len += sprintf(page + len, "b%d_debounce_ms %d\n",
			       i, k->b->debounce_interval);
		len += sprintf(page + len, "b%d_need %u\n", i, k->need);
		len += sprintf(page + len, "b%d_raw %d\n", i, raw_now[i]);
		len += sprintf(page + len, "b%d_state %d\n", i, k->state);
		len += sprintf(page + len, "b%d_n_edge %lu\n", i, k->n_edge);
		len += sprintf(page + len, "b%d_n_bounce %lu\n", i, k->n_bounce);
		len += sprintf(page + len, "b%d_n_press %lu\n", i, k->n_press);
		len += sprintf(page + len, "b%d_n_release %lu\n",
			       i, k->n_release);
		len += sprintf(page + len, "b%d_n_report %lu\n", i, k->n_report);
	}

	/* Oldest first, so the ring reads as a timeline.  When it has not
	 * wrapped the first n_ev slots are the whole history; when it has,
	 * n_ev_drop above says how much is missing. */
	{
		unsigned long n = rtl819x_keys_n_ev;
		unsigned int slots = (n < RTL819X_KEYS_LOG) ?
			(unsigned int)n : RTL819X_KEYS_LOG;
		unsigned int base = (rtl819x_keys_log_head + RTL819X_KEYS_LOG
				     - slots) % RTL819X_KEYS_LOG;
		unsigned int s;

		for (s = 0; s < slots; s++) {
			const struct rtl819x_keys_ev *e =
				&rtl819x_keys_log[(base + s) % RTL819X_KEYS_LOG];

			len += sprintf(page + len, "ev %u %lu %u %u\n",
				       s, e->j, (unsigned)e->btn,
				       (unsigned)e->raw);
		}
	}
	spin_unlock_irqrestore(&rtl819x_keys_lock, flags);

	*eof = 1;
	return len;
}

/* `interval N` -- N milliseconds, 10..60000.
 *
 * The floor is one tick at HZ=100 and is not a preference: input-polldev
 * converts with msecs_to_jiffies() and requeues, so anything below a tick
 * asks the workqueue for a delay of zero and the poll becomes a busy loop on
 * a keventd thread.  The ceiling is arbitrary and stated as such -- it exists
 * so a typo cannot silently stop the polling for a day. */
static int rtl819x_keys_verb_interval(const char *arg)
{
	unsigned long v;
	char *end;
	unsigned long flags;

	v = simple_strtoul(arg, &end, 0);
	if (end == arg)
		return -EINVAL;
	if (v < 10 || v > 60000)
		return -ERANGE;

	spin_lock_irqsave(&rtl819x_keys_lock, flags);
	rtl819x_keys_poll_ms = (unsigned int)v;
	/* The stable counters are in units of polls, so a changed interval
	 * changes what `need` means.  Recomputed here rather than left to
	 * drift, and the /proc field b<i>_need is how a card checks it. */
	{
		int i;

		for (i = 0; i < rtl819x_keys_nbtn; i++) {
			int d = rtl819x_keys_btn[i].b->debounce_interval;
			unsigned int need = (d > 0) ?
				((unsigned int)d + (unsigned int)v - 1) /
				(unsigned int)v : 1;

			rtl819x_keys_btn[i].need = need ? need : 1;
			rtl819x_keys_btn[i].stable = 0;
		}
	}
	spin_unlock_irqrestore(&rtl819x_keys_lock, flags);
	return 0;
}

/* Zero every counter and the ring, so a bench cell can bracket one press
 * without subtracting.  poll_ms, the debounced states and the raw history
 * are NOT reset: clearing the state would make the next poll report an edge
 * that the button did not make. */
static int rtl819x_keys_verb_clear(void)
{
	unsigned long flags;
	int i;

	spin_lock_irqsave(&rtl819x_keys_lock, flags);
	rtl819x_keys_n_poll = 0;
	rtl819x_keys_j_first = 0;
	rtl819x_keys_j_last = 0;
	rtl819x_keys_n_ev = 0;
	rtl819x_keys_n_ev_drop = 0;
	rtl819x_keys_log_head = 0;
	memset(rtl819x_keys_log, 0, sizeof(rtl819x_keys_log));
	for (i = 0; i < rtl819x_keys_nbtn; i++) {
		rtl819x_keys_btn[i].n_press = 0;
		rtl819x_keys_btn[i].n_release = 0;
		rtl819x_keys_btn[i].n_report = 0;
		rtl819x_keys_btn[i].n_edge = 0;
		rtl819x_keys_btn[i].n_bounce = 0;
	}
	spin_unlock_irqrestore(&rtl819x_keys_lock, flags);
	return 0;
}

/* One read through gpiolib and onto the wire, so a capture can hold a pin
 * level taken at a moment the operator chose.  The same verb name and the
 * same reason as rtl819x-gpio's `sample`. */
static int rtl819x_keys_verb_sample(void)
{
	int raw;

	if (!rtl819x_keys_nbtn)
		return -ENODEV;
	raw = gpio_get_value(rtl819x_keys_btn[0].b->gpio);
	rlxfw_markx("K-SAMPLE", (unsigned)raw);
	return 0;
}

/* gpio_to_irq() again, onto the wire.  It is in /proc already; this puts it
 * in the CAPTURE at a moment a card can name, which is what makes it
 * quotable beside a mark rather than beside a shell transcript. */
static int rtl819x_keys_verb_irq(void)
{
	int irq;

	if (!rtl819x_keys_nbtn)
		return -ENODEV;
	irq = gpio_to_irq(rtl819x_keys_btn[0].b->gpio);
	rlxfw_markx("K-IRQ", (unsigned)irq);
	return 0;
}

static int rtl819x_keys_write_proc(struct file *file, const char __user *buffer,
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

	if (!strncmp(buf, "interval ", 9))
		ret = rtl819x_keys_verb_interval(buf + 9);
	else if (!strcmp(buf, "clear"))
		ret = rtl819x_keys_verb_clear();
	else if (!strcmp(buf, "sample"))
		ret = rtl819x_keys_verb_sample();
	else if (!strcmp(buf, "irq"))
		ret = rtl819x_keys_verb_irq();
	else
		return -EINVAL;

	return ret ? ret : (int)count;
}

/* ------------------------------------------------------------------------
 * probe / remove
 * ------------------------------------------------------------------------ */

static int __devinit rtl819x_keys_probe(struct platform_device *pdev)
{
	const struct gpio_keys_platform_data *pdata = pdev->dev.platform_data;
	struct input_polled_dev *pd;
	struct input_dev *input;
	int i, rc;
	int got = 0;

	/* K1 before anything, K7 after registration returns.  Two marks and
	 * not one for the reason rlxfw-devices.c states for PD0/PD1: K1 with
	 * no K2 is a probe that was entered and did not come back, which is a
	 * different failure from one that returned an errno. */
	rlxfw_mark("K1");

	if (!pdata || pdata->nbuttons < 1 ||
	    pdata->nbuttons > RTL819X_KEYS_MAX) {
		rc = -EINVAL;
		goto out;
	}
	rtl819x_keys_pdata = pdata;

	for (i = 0; i < pdata->nbuttons; i++) {
		const struct gpio_keys_button *b = &pdata->buttons[i];

		/* Refused, not ignored -- see the header.  There is no wakeup
		 * path on this SoC and accepting the field would make the
		 * board file describe behaviour that does not exist. */
		if (b->wakeup) {
			rc = -EOPNOTSUPP;
			goto free_gpios;
		}
		/* EV_KEY only.  EV_SW is a real thing in gpio_keys and this
		 * driver has never been given one; refusing is the honest
		 * answer to a type it has not been tested against. */
		if (b->type && b->type != EV_KEY) {
			rc = -EOPNOTSUPP;
			goto free_gpios;
		}

		rc = gpio_request(b->gpio, b->desc ? b->desc : "rtl819x-keys");
		/* K2 carries the FIRST request's result.  -EBUSY here is the
		 * one contention this driver can actually meet: another
		 * gpiolib consumer holding the same line.  The vendor's
		 * rtl_gpio_timer is not one -- it touches the register
		 * directly and takes no gpiolib request (量 FW-40, REG-37). */
		if (i == 0)
			rlxfw_markx("K2", (unsigned)rc);
		if (rc)
			goto free_gpios;
		got = i + 1;

		rc = gpio_direction_input(b->gpio);
		if (rc)
			goto free_gpios;

		rtl819x_keys_btn[i].b = b;
		rtl819x_keys_btn[i].raw_prev = gpio_get_value(b->gpio) ? 1 : 0;
		rtl819x_keys_btn[i].state = 0;
		rtl819x_keys_btn[i].stable = 0;
		rtl819x_keys_btn[i].need = (b->debounce_interval > 0) ?
			(((unsigned int)b->debounce_interval +
			  rtl819x_keys_poll_ms - 1) / rtl819x_keys_poll_ms) : 1;
		if (!rtl819x_keys_btn[i].need)
			rtl819x_keys_btn[i].need = 1;
	}
	rtl819x_keys_nbtn = pdata->nbuttons;

	/* K3: the pin as probe found it.  On this board it must be 1 on every
	 * boot -- BRD-05 is active low and nobody is holding the reset button
	 * during a TFTP boot -- so it is a negative control that costs one
	 * mark and fires if the polarity reading or the line number is
	 * wrong. */
	rtl819x_keys_boot_raw = rtl819x_keys_btn[0].raw_prev;
	rlxfw_markx("K3", (unsigned)rtl819x_keys_boot_raw);

	/* K4: THE NEGATIVE CONTROL FOR THE WHOLE STEP.  This is the call
	 * gpio_keys makes at its own :134, on the same line, through the same
	 * gpiolib, in the same boot -- and it is the reason gpio_keys cannot
	 * drive this board.  Predicted -ENXIO = -6 = FFFFFFFA, produced by
	 * gpiolib.c:1102 from rtl819x-gpio's .to_irq being NULL.  It is
	 * recorded and NOT acted on: this driver does not want an interrupt
	 * and must not fail because there is none. */
	rtl819x_keys_irq_probe = gpio_to_irq(rtl819x_keys_btn[0].b->gpio);
	rlxfw_markx("K4", (unsigned)rtl819x_keys_irq_probe);

	pd = input_allocate_polled_device();
	if (!pd) {
		rc = -ENOMEM;
		goto free_gpios;
	}

	pd->private = NULL;		/* input-polldev owns input's drvdata */
	pd->poll = rtl819x_keys_poll;
	pd->flush = rtl819x_keys_flush;
	pd->poll_interval = rtl819x_keys_poll_ms;

	input = pd->input;
	input->name = "rtl819x-keys";
	/* 🔴 THIS STRING IS MK8's WITNESS AND ITS FIRST SPELLING WAS
	 * `rtl819x-pabcd/input0`, WHICH WOULD HAVE BROKEN MK3.
	 *
	 * 讀 tools/rlxfw-marks.py:516-523 and :621-624: a `str:` witness is
	 * `_count(image, needle) >= 1`, a byte substring search over the whole
	 * vmlinux.  MK3's witness is `str:rtl819x-pabcd` -- rtl819x-gpio's chip
	 * label -- so a literal of MINE containing those bytes would satisfy
	 * MK3 with rtl819x-gpio.o absent from the image.  One new string in one
	 * new file, and an existing row stops being able to fail.
	 *
	 * `rtl819x-keys/input0` contains no existing witness and no existing
	 * literal contains it: arch/rlx/kernel/rlxfw-devices.c carries
	 * `"rtl819x-keys"` as the platform_device name, and that is a PREFIX of
	 * this, so it cannot satisfy MK8 on its own. */
	input->phys = "rtl819x-keys/input0";
	input->dev.parent = &pdev->dev;
	input->id.bustype = BUS_HOST;
	input->id.vendor  = 0x0000;
	input->id.product = 0x0001;
	input->id.version = 0x0100;

	if (pdata->rep)
		__set_bit(EV_REP, input->evbit);

	for (i = 0; i < rtl819x_keys_nbtn; i++)
		input_set_capability(input, EV_KEY,
				     rtl819x_keys_btn[i].b->code);

	rc = input_register_polled_device(pd);
	rlxfw_markx("K5", (unsigned)rc);
	if (rc) {
		input_free_polled_device(pd);
		goto free_gpios;
	}

	rtl819x_keys_poll_dev = pd;
	platform_set_drvdata(pdev, pd);
	rtl819x_keys_bound = 1;
	rc = 0;
	goto out;

free_gpios:
	while (--got >= 0)
		gpio_free(pdata->buttons[got].gpio);
	rtl819x_keys_nbtn = 0;
out:
	rtl819x_keys_probe_rc = rc;
	return rc;
}

static int __devexit rtl819x_keys_remove(struct platform_device *pdev)
{
	struct input_polled_dev *pd = platform_get_drvdata(pdev);
	int i;

	/* Unwound in the reverse order it was built, and the GPIOs are
	 * released.  R5-3's timer driver unwound both of its register writes
	 * on disarm for the same reason: a driver that cannot be taken back
	 * out has not been shown to have taken anything. */
	if (pd) {
		input_unregister_polled_device(pd);
		input_free_polled_device(pd);
	}
	for (i = rtl819x_keys_nbtn - 1; i >= 0; i--)
		gpio_free(rtl819x_keys_btn[i].b->gpio);

	rtl819x_keys_nbtn = 0;
	rtl819x_keys_bound = 0;
	rtl819x_keys_poll_dev = NULL;
	platform_set_drvdata(pdev, NULL);
	return 0;
}

static struct platform_driver rtl819x_keys_driver = {
	.probe	= rtl819x_keys_probe,
	.remove	= __devexit_p(rtl819x_keys_remove),
	.driver	= {
		.name	= RTL819X_KEYS_DRV_NAME,
		.owner	= THIS_MODULE,
	},
};

/* ------------------------------------------------------------------------
 * Registration.
 *
 * device_initcall (6), which is what module_init() becomes in a built-in
 * build, and it is the level UPSTREAM leds-gpio uses.  That is deliberate:
 * R5-7 and R5-8 differ in the driver, not in when it runs, so an ordering
 * question that comes up on one of them comes up on both.
 *
 * The platform DEVICE is registered by arch/rlx/kernel/rlxfw-devices.c at
 * arch_initcall (3), and 3 is before 6 whatever the link order, so this
 * driver's probe runs against a device that already exists.  That is the one
 * ordering here that does not rest on a Makefile's line numbers.
 *
 * platform_driver_register() and NOT platform_driver_probe(): the second
 * returns -ENODEV when nothing matched, which would make "the board file did
 * not register the device" and "probe failed" the same return value.  K7
 * separates them instead, with a sentinel that a real probe can never
 * produce.
 * ------------------------------------------------------------------------ */

static int __init rtl819x_keys_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("K0");

	rtl819x_keys_reg_rc = platform_driver_register(&rtl819x_keys_driver);

	/* K6 is the registration, K7 is what probe did.  probe runs
	 * SYNCHRONOUSLY inside platform_driver_register() when a matching
	 * device is already on the bus, so by this line K1..K5 have already
	 * been printed if it ran at all -- which makes the ORDER inside one
	 * capture the evidence, not a field.  K7 = 00000001 is the sentinel:
	 * probe was never called. */
	rlxfw_markx("K6", (unsigned)rtl819x_keys_reg_rc);
	rlxfw_markx("K7", (unsigned)rtl819x_keys_probe_rc);

	pde = create_proc_entry(RTL819X_KEYS_PROC_NAME, 0644, NULL);
	if (!pde) {
		/* The driver stays registered.  Losing /proc costs the verbs
		 * and the counters, not the input device -- the same choice
		 * rtl819x-gpio's G6-NOPROC makes and for the same reason. */
		rlxfw_mark("K8-NOPROC");
		return rtl819x_keys_reg_rc;
	}
	pde->read_proc  = rtl819x_keys_read_proc;
	pde->write_proc = rtl819x_keys_write_proc;
	rlxfw_mark("K8");

	return rtl819x_keys_reg_rc;
}

device_initcall(rtl819x_keys_init);
