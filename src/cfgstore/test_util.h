/* test_util.h -- the whole test harness: a counter, a macro and a verdict.
 *
 * Deliberately not a framework.  Each test_*.c is its own program with its own
 * main(), the Makefile runs them all and stops on the first non-zero exit, and
 * a failing CHECK prints file, line, group and a message.  Nothing here forks,
 * catches a signal or measures time, so a crash or a sanitizer report is a
 * failure of the run rather than something the harness has to interpret.
 *
 * CHECK's condition is the claim, and the message says what was expected --
 * "FAIL ... rc=-7 want -8" is what a suite is worth at 02:00.
 */
#ifndef RLXFW_TEST_UTIL_H
#define RLXFW_TEST_UTIL_H

#include <stdio.h>
#include <string.h>

static int t_pass;
static int t_fail;
static const char *t_group = "-";

#define T_GROUP(s) (t_group = (s))

#define CHECK(cond, ...)						\
	do {								\
		if (cond) {						\
			t_pass++;					\
		} else {						\
			t_fail++;					\
			printf("FAIL %s:%d [%s] ", __FILE__, __LINE__,	\
			       t_group);				\
			printf(__VA_ARGS__);				\
			putchar('\n');					\
			fflush(stdout);					\
		}							\
	} while (0)

static int t_done(const char *suite)
{
	printf("%-14s %6d passed  %6d failed\n", suite, t_pass, t_fail);
	fflush(stdout);
	return (t_fail == 0) ? 0 : 1;
}

#endif /* RLXFW_TEST_UTIL_H */
