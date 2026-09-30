/* src/httpd/kdfbench.c -- one scrypt evaluation, timed and weighed.
 *
 * WHY IT IS A SEPARATE PROGRAM.  The anti-DoS budget in notes/httpd.md is an
 * argument about two numbers: the bytes one evaluation allocates and the seconds
 * it occupies the broker.  Both have to be measured on a process that does
 * nothing else, or the figure is the test suite's footprint.  So: one call, and
 * a `noop` mode that does everything except the call, so the difference is the
 * KDF and not the runtime.
 *
 *     kdfbench eval <log2n> <r> <p>     one evaluation
 *     kdfbench noop <log2n> <r> <p>     the same program, no evaluation
 *     kdfbench peak <log2n> <r> <p>     print the arithmetic only, allocate nothing
 *
 * It prints one line of `key=value` pairs so a script can read it, and it prints
 * its own elapsed time from CLOCK_MONOTONIC as well as leaving the outer
 * /usr/bin/time to measure the process -- two clocks, because a single one cannot
 * be checked.
 *
 * WHAT THE NUMBERS DO NOT ESTABLISH.  qemu-mips-static time is NOT the device's
 * time and no scaling of it is: qemu-user translates each guest instruction on a
 * host running at several GHz, while the device is a 400 MHz MIPS-I with no cache
 * hierarchy worth the name.  The two errors are in opposite directions and
 * neither is known, so the device figure stays 推 until the board prints it.
 * The peak RSS is more portable than the time -- the allocation is the same number
 * of bytes on both -- but even that is the allocation, not the resident set the
 * 2.6.30 kernel will actually show.
 */

#include "../lib/kdf.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double elapsed_s(const struct timespec *a, const struct timespec *b)
{
	return (double)(b->tv_sec - a->tv_sec) +
	       (double)(b->tv_nsec - a->tv_nsec) / 1e9;
}

/* VmHWM from /proc/self/status, in kB, or 0 when it cannot be read.  Under
 * qemu-user this is the EMULATOR's high-water mark, which is why the script that
 * calls this takes a difference against `noop` rather than believing one run. */
static unsigned long vmhwm_kb(void)
{
	FILE *f = fopen("/proc/self/status", "r");
	char line[256];
	unsigned long v = 0;

	if (f == NULL)
		return 0;
	while (fgets(line, sizeof(line), f) != NULL) {
		if (strncmp(line, "VmHWM:", 6) == 0) {
			v = strtoul(line + 6, NULL, 10);
			break;
		}
	}
	(void)fclose(f);
	return v;
}

int main(int argc, char **argv)
{
	static const uint8_t pw[16] = "correct horse st";
	static const uint8_t salt[16] = {
		0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
		0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff
	};
	uint8_t out[32];
	struct timespec t0, t1;
	unsigned long log2n, r, p;
	size_t peak;
	int rc = 0;
	int do_eval;

	if (argc != 5) {
		(void)fprintf(stderr,
			      "usage: kdfbench {eval|noop|peak} <log2n> <r> <p>\n");
		return 2;
	}
	log2n = strtoul(argv[2], NULL, 10);
	r = strtoul(argv[3], NULL, 10);
	p = strtoul(argv[4], NULL, 10);
	if (log2n < 1 || log2n > 24 || r < 1 || r > 1024 || p < 1 || p > 16) {
		(void)fprintf(stderr, "kdfbench: parameters out of range\n");
		return 2;
	}
	do_eval = (strcmp(argv[1], "eval") == 0);

	peak = kdf_scrypt_peak((uint8_t)log2n, (uint16_t)r, (uint16_t)p);
	if (strcmp(argv[1], "peak") == 0) {
		(void)printf("mode=peak log2n=%lu r=%lu p=%lu peak_bytes=%lu"
			     " peak_kib=%lu cap_bytes=%u over_cap=%d\n",
			     log2n, r, p, (unsigned long)peak,
			     (unsigned long)(peak / 1024u), KDF_PEAK_CAP,
			     peak > KDF_PEAK_CAP ? 1 : 0);
		return 0;
	}

	(void)clock_gettime(CLOCK_MONOTONIC, &t0);
	if (do_eval)
		rc = kdf_scrypt_raw(pw, sizeof(pw), salt, sizeof(salt),
				    1u << log2n, (uint32_t)r, (uint32_t)p,
				    out, sizeof(out));
	(void)clock_gettime(CLOCK_MONOTONIC, &t1);

	(void)printf("mode=%s log2n=%lu r=%lu p=%lu rc=%d peak_bytes=%lu"
		     " vmhwm_kb=%lu wall_s=%.4f out0=%02x\n",
		     do_eval ? "eval" : "noop", log2n, r, p, rc,
		     (unsigned long)peak, vmhwm_kb(), elapsed_s(&t0, &t1),
		     do_eval ? out[0] : 0);
	return rc == 0 ? 0 : 1;
}
