/*
 * rlxfw's boot marks.   R3-6.
 *
 * THIS FILE IS NOT REALTEK'S.  It is staged into arch/rlx/kernel/ by
 * tools/rlxfw-marks.py; config/rlxfw-marks.tsv declares it and the eleven
 * call sites, one row each, with a reason per row.
 *
 * WHY THIS EXISTS AT ALL.
 * 讀 the built .config: `# CONFIG_PRINTK is not set`.  include/linux/kernel.h
 * then makes printk() `static inline int __cold printk(...) { return 0; }`, so
 * every call site compiles to nothing and its format string is dropped from
 * the image.  量 on the R3 vmlinux: printk is three 20-byte
 * `move v0,zero / jr ra` stubs.  And this unit's own boot capture agrees --
 * bench/2026-08-24c/G6.log goes from `start address: 0x80003440` straight to
 * `Realtek WLAN driver - version 1.6` with nothing in between.  So between
 * kernel entry and userspace this board prints NOTHING, and R3's D3 -- "early
 * bring-up completes" -- had no observable at all.
 *
 * WHY NOT early_printk(), WHICH LOOKS AVAILABLE.
 * CONFIG_EARLY_PRINTK=y is set, which is a trap.  量 on the R3 vmlinux,
 * early_printk is a WEAK 16-byte stub at 0x80013bec:
 *
 *      sw a1,4(sp) / sw a2,8(sp) / jr ra / sw a3,12(sp)
 *
 * kernel/printk_log.c:42 defines it `__attribute__((weak))` with an empty
 * body and nothing under arch/rlx overrides it.  It writes the varargs
 * register-save area and returns.  It prints nothing.
 *
 * WHY NOT panic_printk, WHICH IS REAL.
 * It is (44 bytes, 0x80015140, jal vprintk) and CONFIG_PANIC_PRINTK=y.  But it
 * goes through vprintk into the log buffer and reaches the wire only once a
 * console is registered -- init/main.c:629 console_init(), and before that
 * arch/rlx/kernel/setup.c:546 setup_early_printk().  Six of the eleven marks
 * below are EARLIER than both.  A mark that is buffered until a console comes
 * up cannot report a hang that stops the console from coming up, which is the
 * failure this ladder exists to locate.
 *
 * SO: prom_putchar.  arch/rlx/kernel/early_printk.c:24, GLOBAL, 100 bytes at
 * 0x8000b080 in .text (not __init, so it is resident), polling UART0_LSR at
 * 0xB8002014 and writing UART0_THR at 0xB8002000 -- KSEG1, uncached, no
 * subsystem, no buffer, no console.  Its busy loop is bounded at 30,000
 * iterations by Realtek's own code, so it cannot hang.  It works from the
 * first C instruction of the kernel.
 *
 * WHAT IT ASSUMES, AND HOW THAT IS REFUTED.
 * 推: that the UART divisor the loader left behind is still 38400 8N1 when
 * these run.  The loader prints `decompressing kernel:` at 38400 through the
 * same UART0 and prom_putchar never touches the divisor, so it inherits
 * whatever is set.  REFUTED BY: garbage bytes where a mark should be.  B5 is
 * placed immediately after bsp_serial_init() precisely so that "the vendor's
 * own serial init changed the divisor" is one readable line rather than a
 * silent boot.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/rlxfw-mark.h>

/*
 * The dependency is asserted HERE and nowhere else, on purpose.
 * CONFIG_EARLY_PRINTK=y comes from the vendor's own board template (line 141),
 * so it is not a difference and `config/rlxfw-kernel.delta` has no rule for it
 * -- that file declares only what rlxfw changes.  A dependency that is real
 * but is not a delta has to fail where it is used, or it is not checked at all.
 */
#ifndef CONFIG_EARLY_PRINTK
#error "rlxfw_mark needs prom_putchar, which arch/rlx/kernel/Makefile builds \
only under CONFIG_EARLY_PRINTK. That symbol is =y in the vendor board template \
and rlxfw does not change it; if it ever goes away this build must STOP rather \
than fall back to a printk() that is a stub in this configuration."
#endif

extern int prom_putchar(char c);

/*
 * A mark is one line, and it is written whole before the next one starts.
 * No newline-first: a capture truncated mid-mark must show a partial mark and
 * not a clean previous line, because "the last thing I saw was B6" and "B6
 * completed" are different claims.
 *
 * The whole string arrives as ONE literal from the macro in
 * <linux/rlxfw-mark.h>; see that file for why, and for the measurement that
 * made it necessary.
 */
void rlxfw_puts(const char *s)
{
	while (*s) {
		if (*s == '\n')
			prom_putchar('\r');
		prom_putchar(*s);
		s++;
	}
}

/*
 * The same, then a 32-bit value the vendor image cannot fake because it is
 * read out of this die at run time rather than compiled in.  Used by B2
 * (PRId) and B7 (bsp_swcore_init's return value, which is otherwise consumed
 * by an unconditional bsp_machine_halt() -- a bare while(1)).
 *
 * Hex is emitted by hand.  It cannot call any printf: printk is a stub in this
 * configuration, and vsnprintf would pull in the whole formatting path, which
 * at B0 has not been initialised.
 */
void rlxfw_puts_hex(const char *s, unsigned int v)
{
	static const char hex[] = "0123456789ABCDEF";
	int i;

	rlxfw_puts(s);
	for (i = 28; i >= 0; i -= 4)
		prom_putchar(hex[(v >> i) & 0xF]);
	rlxfw_puts("\n");
}
