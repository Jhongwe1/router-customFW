/* report.c -- the two output helpers every payload needs.
 *
 * They lived in probe0.c until probe1 existed, at which point "shared by one
 * caller" stopped being true.  Nothing here talks to hardware directly: rlx_putc
 * is in uart.S, where the instruction order is the point.
 */

#include "rlxprobe.h"

void rlx_puts(const char *s)
{
	while (*s)
		rlx_putc(*s++);
}

void rlx_puthex32(u32 v)
{
	static const char digits[] = "0123456789abcdef";
	int i;

	for (i = 28; i >= 0; i -= 4)
		rlx_putc(digits[(v >> i) & 0xf]);
}

/* SAFE_A0's target -- see rlxasm.h.
 *
 * It lives HERE, in the one file every payload links, and not in probe1.c and
 * probe2.c, which is where it used to be defined twice. `uart.S`'s four CP0
 * readers and `rlx_mfc0_config1` carry SAFE_A0 as of 2026-08-25, and probe0
 * links uart.S -- so a symbol owned by two of the three payloads would have
 * been a link error the moment the guard became universal.
 *
 * 64 words: the loader's `do_reserved` dereferences the faulting code's own
 * $a0 and reads offset 148 of it, so the region has to be at least 152 bytes
 * and word aligned. `tools/test-rlxprobe.sh` V2 checks both, in every payload,
 * against the emitted image rather than against this comment. start.S zeroes
 * .bss, so a fault under the guard prints `ra=0` and the operator knows the
 * guard was in place.
 */
u32 rlx_fault_frame[64];
