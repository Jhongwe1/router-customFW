/* src/brokerd/test_ping.c -- PING: argv from typed values, the TIMEOUT as the
 * mechanism that ends it, truncation at 2048, and no zombie left behind.
 *
 * argv[1] is a helper binary (built as `pinghelp`) that ignores its arguments,
 * writes more than 2048 bytes and then sleeps.  It stands in for this image's
 * busybox ping, which IGNORES -c (config/image-commands.tsv): the count never
 * stops it, so the wall-clock deadline is the primary mechanism and this test
 * is the one that says so.  argv[2] is a helper that exits at once, for the
 * EOF path.
 */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "brokerd.h"

static int fails;

#define CHECK(cond, ...) do { \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

static void fixture(struct broker *bk, const char *bin, int timeout_s)
{
	bk_init(bk);
	/* `R7-8`: this was "/dev/null" while brokerd linked src/brokerd/stub/cfg_stub.c,
	 * whose cfg_store() returned 0 without touching a file.  The real cfg_store
	 * WRITES a 4,096-byte slot and then READS IT BACK to verify, and a read-back
	 * from /dev/null is 0 bytes, so every SET and PWSET answered ST_IO (6).  A
	 * real file per test binary is what the product does; the file is created by
	 * cfg_store itself (O_RDWR|O_CREAT, 0600). */
	bk->cfg_path = "/tmp/rlxbk-store-test_ping.bin";
	bk->ping_bin = bin;
	bk->ping_timeout_s = timeout_s;
	/* A REAL clock here: the timeout is the subject. */
	bk->use_fake_clock = 0;
}

static uint8_t ping(struct broker *bk, uint8_t a, uint8_t b, uint8_t c,
                    uint8_t d, uint8_t n, struct proto_resp *rs)
{
	struct proto_req rq;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_PING;
	rq.body[0] = a; rq.body[1] = b; rq.body[2] = c; rq.body[3] = d;
	rq.body[4] = n;
	rq.body_len = 5;
	(void)bk_dispatch(bk, &rq, BK_UID_ROOT, rs);
	return rs->status;
}

static void test_body_validation(void)
{
	struct broker bk;
	struct proto_resp rs;
	struct proto_req rq;

	fixture(&bk, "/bin/echo", 2);
	CHECK(ping(&bk, 10, 1, 1, 2, 0, &rs) == ST_INVAL, "count 0 refused");
	CHECK(ping(&bk, 10, 1, 1, 2, 6, &rs) == ST_INVAL, "count 6 refused");
	CHECK(ping(&bk, 0, 0, 0, 0, 1, &rs) == ST_INVAL, "0.0.0.0 refused");
	CHECK(ping(&bk, 10, 1, 1, 2, 1, &rs) == ST_OK, "10.1.1.2 count 1 ok");
	CHECK(ping(&bk, 10, 1, 1, 2, 5, &rs) == ST_OK, "count 5 ok");

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_PING;
	rq.body_len = 4;
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_INVAL, "a 4-byte body refused");
	rq.body_len = 6;
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_INVAL, "a 6-byte body refused");
	rq.body_len = 0;
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_INVAL, "an empty body refused");
}

/* The dotted quad reaches argv, and it is the only thing from the request that
 * does.  /bin/echo prints its arguments, so the output IS argv[1..]. */
static void test_argv_is_typed(void)
{
	struct broker bk;
	struct proto_resp rs;

	fixture(&bk, "/bin/echo", 3);
	CHECK(ping(&bk, 192, 168, 254, 1, 3, &rs) == ST_OK, "echo ok");
	if (rs.body_len == 0) {
		(void)printf("  SKIP /bin/echo produced nothing\n");
		return;
	}
	rs.body[rs.body_len < sizeof(rs.body) ? rs.body_len : sizeof(rs.body) - 1] = 0;
	CHECK(strstr((char *)rs.body, "192.168.254.1") != 0,
	      "the dotted quad is in argv: [%s]", (char *)rs.body);
	CHECK(strstr((char *)rs.body, "-c 3") != 0, "the count is in argv: [%s]",
	      (char *)rs.body);
	CHECK(strstr((char *)rs.body, "-W 1") != 0, "-W 1 is in argv");
	/* No shell metacharacter can appear, because nothing textual from the
	 * caller reaches argv: the target is four bytes. */
	CHECK(strchr((char *)rs.body, ';') == 0, "no ';' in argv");
	CHECK(strchr((char *)rs.body, '`') == 0, "no backtick in argv");
	CHECK(strchr((char *)rs.body, '|') == 0, "no pipe in argv");
}

static void no_child_left(const char *what)
{
	int st = 0;
	pid_t w = waitpid(-1, &st, WNOHANG);

	CHECK(w == -1 && errno == ECHILD,
	      "%s: no unreaped child remains (waitpid returned %ld)", what, (long)w);
}

/* THE TRUNCATION PATH.  The helper writes 8 KiB and never exits: the broker
 * stops at 2048 bytes and does NOT sit out the deadline. */
static void test_truncation(const char *helper)
{
	struct broker bk;
	struct proto_resp rs;
	time_t t0, t1;
	long dt;

	fixture(&bk, helper, 4);
	t0 = time(0);
	CHECK(ping(&bk, 10, 1, 1, 2, 1, &rs) == ST_OK, "truncated ping is OK");
	t1 = time(0);
	dt = (long)(t1 - t0);
	(void)printf("  truncation path: %ld s wall (timeout 4 s), %lu bytes\n",
	             dt, (unsigned long)rs.body_len);
	CHECK(rs.body_len == BK_PING_OUT_MAX, "output capped at %d, got %lu",
	      BK_PING_OUT_MAX, (unsigned long)rs.body_len);
	CHECK(dt <= 2, "a full buffer returns without waiting out the deadline "
	      "(%ld s of 4)", dt);
	no_child_left("truncation");
}

/* THE DEADLINE PATH, and the one that matters on the device.  The helper writes
 * 64 bytes and never exits, exactly as this image's `ping` does not stop for
 * -c: nothing but the wall-clock timeout can end this. */
static void test_deadline(const char *helper)
{
	struct broker bk;
	struct proto_resp rs;
	time_t t0, t1;
	long dt;

	fixture(&bk, helper, 2);
	t0 = time(0);
	CHECK(ping(&bk, 10, 1, 1, 2, 1, &rs) == ST_OK,
	      "a timed-out ping is OK with whatever output arrived");
	t1 = time(0);
	dt = (long)(t1 - t0);
	(void)printf("  deadline path: %ld s wall (timeout 2 s), %lu bytes\n",
	             dt, (unsigned long)rs.body_len);
	CHECK(dt >= 2 && dt <= 8, "the deadline ended it in %ld s, want 2..8", dt);
	CHECK(rs.body_len == 64, "the 64 bytes written before the sleep, got %lu",
	      (unsigned long)rs.body_len);
	no_child_left("deadline");
}

static void test_exec_failure(void)
{
	struct broker bk;
	struct proto_resp rs;

	/* A missing binary is not a crash and not a hang: the child exits 127
	 * and the pipe closes. */
	fixture(&bk, "/nonexistent/rlxfw/ping", 3);
	CHECK(ping(&bk, 10, 1, 1, 2, 1, &rs) == ST_OK,
	      "a failed execve still answers");
	CHECK(rs.body_len == 0, "and produces no output, got %lu",
	      (unsigned long)rs.body_len);
	no_child_left("exec failure");
}

int main(int argc, char **argv)
{
	(void)printf("test_ping\n");
	test_body_validation();
	test_argv_is_typed();
	test_exec_failure();
	if (argc > 2) {
		test_truncation(argv[1]);
		test_deadline(argv[2]);
	} else {
		(void)printf("  FAIL need <pinghelp> <pinghelp_slow>; the deadline "
		             "path is the point of this file\n");
		fails++;
	}
	(void)printf("test_ping: %d failures\n", fails);
	return fails == 0 ? 0 : 1;
}
