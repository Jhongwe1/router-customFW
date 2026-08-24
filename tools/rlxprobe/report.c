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
