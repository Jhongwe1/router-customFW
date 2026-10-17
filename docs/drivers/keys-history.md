# `rtl819x-keys.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/input/keyboard/rtl819x-keys.c`](../../kernel/linux-2.6.30/drivers/input/keyboard/rtl819x-keys.c)
until 2026-10-18 — lines 1–171 at commit `32933d60` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [keys](keys.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-keys.c` counts the file's lines at `32933d60`.

```c
/*
 * rtl819x-keys -- the board's buttons, polled, as a real input device.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-8, 2026-09-10, fifty-fourth segment.  It is
 * staged into drivers/input/keyboard/ by tools/rlxfw-marks.py from
 * kernel/; config/rlxfw-marks.tsv row MK8 carries the one Kbuild
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
```
