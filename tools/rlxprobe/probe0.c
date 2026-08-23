/* probe0.c -- segment 0 of rlxprobe: the chain, and four CP0 registers.
 *
 * What this segment is for
 * ------------------------
 * Every later segment of R1 needs the same five things to work before any of
 * its answers mean anything: the toolchain emits code this core will run, the
 * linker puts the entry at offset 0, the loader's `LOADADDR`/TFTP/`J` path
 * delivers it, the UART routine talks, and the board comes back afterwards.
 * **This segment tests exactly those five and nothing else**, so that when
 * R1a's instruction sweep reports an absence, "the payload did not run" is
 * already excluded.
 *
 * Four registers come free while it is there, and three of them are blanks in
 * SPEC.md:
 *
 *   PRId    CPU-04 -- RLX4181 or RLX5281. One register, one answer, and the
 *           project has been writing "undetermined" in every document since
 *           the beginning because /proc/cpuinfo printed a decimal number.
 *   Config  Config.M == 0 proves this is not a MIPS32 core outright. It also
 *           says whether Config1 -- cache geometry, FPU present, MMU present
 *           -- exists at all, which is CPU-25's whole route.
 *   Status  CPU-27 -- is BEV 0 at the prompt? R1d plans to install a handler
 *           at 0x80000180, and that address is only right if BEV is 0. If it
 *           is 1 the vectors are at 0xBFC00200 in boot ROM and R1d's first
 *           step changes.
 *   Cause   read for its own sake, and as the thing an exception would have
 *           written. The loader's own exception reporter is still installed
 *           while this runs (CPU-26), so a fault here prints rather than
 *           vanishes -- that reporter is this segment's safety net.
 *
 * What it deliberately does NOT do
 * --------------------------------
 *   * It executes no instruction outside MIPS-I except one `mfc0` with a
 *     select field, and that one only after Config says the register exists.
 *   * It installs no exception handler. It runs under the loader's, which is
 *     already there -- so if something faults, `Undefined Exception happen.`
 *     and `cp0_cause=%X, cp0_epc=%X` come out of the loader, not out of a
 *     vacuum. Installing a handler is R1d and needs the cache model first.
 *   * It writes no flash, no configuration and no register except WDTCNR at
 *     the very end, and that one is the documented reset.
 *   * It measures no hazard and no timing. Both need a handler and a
 *     controlled loop, and a number produced without them would be a number.
 */

#include "rlxprobe.h"

/* Checked before it was written down, against the 4 MiB dump (twice), the
 * decompressed stage 2, and the R0 kernel payload: zero occurrences in all
 * four. The control for that check is `RealTek`, which occurs 3 times in
 * decompressed stage 2 and -- this is the part worth knowing -- ZERO times in
 * the 4 MiB dump, because the dump stores stage 2 LZMA-compressed. So the
 * strong leg of "this string cannot have come from the device" is the
 * decompressed image, not the dump. */
#define NONCE "5c1b7ea0"

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

/* One field per line, fixed shape, so `console-lint.py` reads it and a human
 * does not have to. A report a person has to parse by eye is a report that
 * gets misread once. */
static void field(const char *name, u32 v)
{
	rlx_puts("rlxprobe: ");
	rlx_puts(name);
	rlx_putc('=');
	rlx_puthex32(v);
	rlx_puts("\r\n");
}

void rlxprobe_main(void)
{
	u32 pc, status, cause, prid, config;

	/* Read everything before printing anything. The UART routine spins on
	 * the line-status register up to 6540 times per character; doing that
	 * between two CP0 reads would put tens of thousands of cycles inside a
	 * window that is supposed to be a snapshot. Cause in particular is
	 * volatile. */
	pc     = rlx_pc();
	status = rlx_mfc0_status();
	cause  = rlx_mfc0_cause();
	prid   = rlx_mfc0_prid();
	config = rlx_mfc0_config();

	/* Short first, and a leading CRLF: P9-12's banner was cut at the same
	 * character every iteration, so the first thing out is the thing worth
	 * having if only sixteen bytes survive. */
	rlx_puts("\r\n*** rlxprobe P0 " NONCE " ***\r\n");

	field("pc",     pc);
	field("status", status);
	field("cause",  cause);
	field("prid",   prid);
	field("config", config);

	if (config & 0x80000000u) {
		field("config1", rlx_mfc0_config1());
	} else {
		rlx_puts("rlxprobe: config1=absent, Config.M is 0\r\n");
	}

	/* An explicit end marker. Without one, "the report stopped after
	 * `prid`" and "the report ended after `prid`" are the same observation,
	 * and P9-12 is the reason that distinction is not left to inference. */
	rlx_puts("rlxprobe: end\r\n");
}
