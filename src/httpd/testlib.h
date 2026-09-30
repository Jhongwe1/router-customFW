/* src/httpd/testlib.h -- the three lines of harness every test_*.c shares.
 *
 * Output is one line per case so a failure names itself, and the program's exit
 * status is the verdict.  A tool reporting 0 is making a claim, so every test
 * program also counts its cases and REFUSES if it ran fewer than it declared:
 * a suite that silently ran nothing is the failure mode a green tick hides.
 */
#ifndef RLXFW_HTTPD_TESTLIB_H
#define RLXFW_HTTPD_TESTLIB_H

#include <stdio.h>
#include <stdlib.h>

static int t_n;
static int t_bad;

static void t_ok(int cond, const char *name, const char *detail)
{
	t_n++;
	if (cond) {
		(void)printf("ok %d - %s\n", t_n, name);
	} else {
		t_bad++;
		(void)printf("not ok %d - %s%s%s\n", t_n, name,
			     detail != NULL ? ": " : "",
			     detail != NULL ? detail : "");
	}
}

static void t_okf(int cond, const char *name, long got, long want)
{
	char buf[96];

	(void)snprintf(buf, sizeof(buf), "got %ld want %ld", got, want);
	t_ok(cond, name, cond ? NULL : buf);
}

/* `least` is the number of cases this program must have run.  It is a separate
 * claim from "they all passed", and it is the one that catches a loop that never
 * entered its body. */
static int t_done(int least)
{
	(void)printf("# %d/%d passed (declared at least %d)\n",
		     t_n - t_bad, t_n, least);
	if (t_n < least) {
		(void)printf("not ok - REFUSED: only %d cases ran, %d declared\n",
			     t_n, least);
		return 1;
	}
	return t_bad == 0 ? 0 : 1;
}

#endif /* RLXFW_HTTPD_TESTLIB_H */
