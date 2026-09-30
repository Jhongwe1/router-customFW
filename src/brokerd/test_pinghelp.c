/* src/brokerd/test_pinghelp.c -- a stand-in for this image's busybox `ping`.
 *
 * It ignores every argument -- 讀 config/image-commands.tsv, this image's
 * `ping` ignores -c, so nothing the broker puts in argv stops it either -- and
 * then never exits.  Two builds, because the two ways a PING can end are
 * different mechanisms and each needs its own case:
 *
 *   default          8 KiB, four times the 2048-byte cap, then sleep.  The
 *                    TRUNCATION path: the broker stops reading at 2048 and does
 *                    not wait for the deadline.
 *   -DPINGHELP_SLOW  64 bytes, then sleep.  The DEADLINE path: the output never
 *                    fills the buffer and the child never exits, so only the
 *                    wall-clock timeout can end the op.
 */
#include <stdio.h>
#include <unistd.h>

#ifdef PINGHELP_SLOW
#define CHUNKS 2
#else
#define CHUNKS 256
#endif

int main(int argc, char **argv)
{
	int i;

	(void)argc;
	(void)argv;
	for (i = 0; i < CHUNKS; i++)
		(void)fwrite("0123456789abcdefghijklmnopqrstuv", 1, 32, stdout);
	(void)fflush(stdout);
	for (;;)
		(void)sleep(3600);
	return 0;
}
