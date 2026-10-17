# `rtl819x-gpio.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/gpio/rtl819x-gpio.c`](../../kernel/linux-2.6.30/drivers/gpio/rtl819x-gpio.c)
until 2026-10-18 — lines 1–183 at commit `df00a168` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [gpio](gpio.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-gpio.c` counts the file's lines at `df00a168`.

```c
/*
 * rtl819x-gpio -- a gpiolib gpio_chip on the RTL8196E's PABCD port.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-4, 2026-09-06, thirty-seventh segment.  It
 * is staged into drivers/gpio/ by tools/rlxfw-marks.py from kernel/;
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
```
