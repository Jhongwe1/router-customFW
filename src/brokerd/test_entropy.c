/* src/brokerd/test_entropy.c -- the fail-closed entropy gate, driven from both
 * sides through the injectable /proc path.
 *
 * The first fixture is not invented: "0\n" is what
 * /proc/sys/kernel/random/entropy_avail printed on this device on 2026-09-30 at
 * 768.26 s of uptime (bench/2026-09-30/SB-ENT.log) and again at 1613.27 s
 * (SB-RT1.log).  So the NOENTROPY half of this file is the board's behaviour
 * today, not a hypothetical, and the "after" half is what a kernel with an
 * entropy source would give.
 */
#include <stdio.h>
#include <string.h>

#include "brokerd.h"
#include "test_help.h"

static int fails;

#define CHECK(cond, ...) do { \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

#define ENT_PATH "/tmp/rlxbk_entropy_drive"
#define PW "correct-horse"

static void fixture(struct broker *bk, const char *contents)
{
	if (bk_test_write_file(ENT_PATH, contents) != 0) {
		(void)printf("  FAIL cannot write %s\n", ENT_PATH);
		fails++;
	}
	bk_init(bk);
	bk->entropy_path = ENT_PATH;
	bk->use_fake_clock = 1;
	bk->fake_now = 100;
	/* `R7-8`: this was "/dev/null" while brokerd linked src/brokerd/stub/cfg_stub.c,
	 * whose cfg_store() returned 0 without touching a file.  The real cfg_store
	 * WRITES a 4,096-byte slot and then READS IT BACK to verify, and a read-back
	 * from /dev/null is 0 bytes, so every SET and PWSET answered ST_IO (6).  A
	 * real file per test binary is what the product does; the file is created by
	 * cfg_store itself (O_RDWR|O_CREAT, 0600). */
	bk->cfg_path = "/tmp/rlxbk-store-test_entropy.bin";
	bk_test_set_pw(bk, PW);
}

static uint8_t call(struct broker *bk, uint8_t op, uid_t uid,
                    struct proto_resp *rs)
{
	struct proto_req rq;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = op;
	if (op == OP_LOGIN) {
		rq.body_len = (uint32_t)strlen(PW);
		memcpy(rq.body, PW, rq.body_len);
	} else if (op == OP_PWSET) {
		rq.body[0] = (uint8_t)strlen(PW);
		memcpy(rq.body + 1, PW, strlen(PW));
		rq.body[1 + strlen(PW)] = 8;
		memcpy(rq.body + 2 + strlen(PW), "newpass1", 8);
		rq.body_len = (uint32_t)(2 + strlen(PW) + 8);
	}
	(void)bk_dispatch(bk, &rq, uid, rs);
	return rs->status;
}

static int status_tlv(const struct proto_resp *rs, uint16_t type,
                      uint32_t *v32, uint8_t *v8)
{
	size_t off = 0;
	uint16_t t, l;
	const uint8_t *val;

	while (proto_tlv_get(rs->body, rs->body_len, &off, &t, &val, &l) == 0) {
		if (t != type)
			continue;
		if (l == 4 && v32 != 0)
			*v32 = proto_be32(val);
		if (l == 1 && v8 != 0)
			*v8 = val[0];
		return 1;
	}
	return 0;
}

/* The board as it is today. */
static void test_zero_refuses(void)
{
	struct broker bk;
	struct proto_resp rs;

	fixture(&bk, "0\n");
	CHECK(bk_entropy_ready(&bk) == 0, "entropy_avail 0 is not ready");
	CHECK(bk.auth_ready == 0, "auth_ready stays 0");
	CHECK(call(&bk, OP_LOGIN, BK_UID_HTTPD, &rs) == ST_NOENTROPY,
	      "httpd LOGIN with a correct password: %u (want NOENTROPY)",
	      (unsigned)rs.status);
	CHECK(call(&bk, OP_LOGIN, BK_UID_ROOT, &rs) == ST_NOENTROPY,
	      "root LOGIN too: %u", (unsigned)rs.status);
	CHECK(call(&bk, OP_PWSET, BK_UID_ROOT, &rs) == ST_NOENTROPY,
	      "root PWSET: %u", (unsigned)rs.status);
	CHECK(bk_sess_count(&bk) == 0, "no session was issued");
	/* A NOENTROPY LOGIN does not consume a rate-limit attempt: a board that
	 * cannot log anyone in must not also lock them out. */
	CHECK(bk_rl_peek(&bk, 0) == 0, "no bucket was touched");

	/* Everything that is not LOGIN/PWSET still works. */
	CHECK(call(&bk, OP_STATUS, BK_UID_ROOT, &rs) == ST_OK, "STATUS works");
	{
		uint32_t e = 0xFFFFFFFFu;
		uint8_t r = 0xFF;

		CHECK(status_tlv(&rs, BKS_ENTROPY, &e, 0), "STATUS has 0x8007");
		CHECK(e == 0, "STATUS reports entropy_avail = %lu, want 0",
		      (unsigned long)e);
		CHECK(status_tlv(&rs, BKS_AUTHRDY, 0, &r), "STATUS has 0x8008");
		CHECK(r == 0, "STATUS reports auth_ready = %u, want 0", (unsigned)r);
	}
	{
		struct proto_req rq;

		memset(&rq, 0, sizeof(rq));
		rq.version = PROTO_VERSION;
		rq.op = OP_GET;
		proto_put_be16(rq.body, CFGID_LAN_IPADDR);
		rq.body_len = 2;
		(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
		CHECK(rs.status == ST_OK, "root GET works with no entropy");
	}
}

static void test_boundary(void)
{
	struct broker bk;
	struct proto_resp rs;

	fixture(&bk, "127\n");
	CHECK(bk_entropy_ready(&bk) == 0, "127 is below the %d threshold",
	      BK_ENTROPY_MIN);
	CHECK(call(&bk, OP_LOGIN, BK_UID_ROOT, &rs) == ST_NOENTROPY, "127: refused");

	fixture(&bk, "128\n");
	CHECK(bk_entropy_ready(&bk) == 1, "128 is ready");
	CHECK(call(&bk, OP_LOGIN, BK_UID_ROOT, &rs) == ST_OK,
	      "128: LOGIN succeeds, got %u", (unsigned)rs.status);
	CHECK(rs.body_len == 2 * PROTO_TOK_LEN + 4, "a session was issued");
	CHECK(bk_sess_count(&bk) == 1, "one session");
}

/* "Seen at least once since boot" -- so a pool that drains again does not take
 * the ability to log in away. */
static void test_sticky(void)
{
	struct broker bk;
	struct proto_resp rs;

	fixture(&bk, "4096\n");
	CHECK(bk_entropy_ready(&bk) == 1, "ready");
	CHECK(bk_test_write_file(ENT_PATH, "0\n") == 0, "drain the pool");
	CHECK(bk_entropy_ready(&bk) == 1, "still ready: the flag is sticky");
	CHECK(call(&bk, OP_LOGIN, BK_UID_ROOT, &rs) == ST_OK,
	      "LOGIN after the pool drained: %u", (unsigned)rs.status);
	{
		uint8_t r = 0;

		(void)call(&bk, OP_STATUS, BK_UID_ROOT, &rs);
		CHECK(status_tlv(&rs, BKS_AUTHRDY, 0, &r) && r == 1,
		      "auth_ready stays 1");
	}
}

/* An unreadable /proc is not permission. */
static void test_unreadable_fails_closed(void)
{
	struct broker bk;
	struct proto_resp rs;

	fixture(&bk, "4096\n");
	bk_init(&bk);
	bk.entropy_path = "/tmp/rlxbk_entropy_does_not_exist";
	bk.use_fake_clock = 1;
	bk.cfg_path = "/tmp/rlxbk-store-test_entropy.bin";
	bk_test_set_pw(&bk, PW);
	CHECK(bk_entropy_ready(&bk) == 0, "a missing file is not ready");
	CHECK(call(&bk, OP_LOGIN, BK_UID_ROOT, &rs) == ST_NOENTROPY,
	      "missing file: %u", (unsigned)rs.status);

	/* Garbage in the file is read as 0, not as "large". */
	bk_init(&bk);
	bk.entropy_path = ENT_PATH;
	bk.use_fake_clock = 1;
	bk.cfg_path = "/tmp/rlxbk-store-test_entropy.bin";
	bk_test_set_pw(&bk, PW);
	CHECK(bk_test_write_file(ENT_PATH, "nonsense\n") == 0, "write garbage");
	CHECK(bk_entropy_ready(&bk) == 0, "garbage is not ready");
	CHECK(bk_test_write_file(ENT_PATH, "-4096\n") == 0, "write a negative");
	CHECK(bk_entropy_ready(&bk) == 0, "a leading '-' is not a number here");
	CHECK(bk_test_write_file(ENT_PATH, "99999999999999999999\n") == 0, "overflow");
	CHECK(bk_entropy_ready(&bk) == 1, "a saturating value is still >= 128");
}

int main(void)
{
	(void)printf("test_entropy\n");
	test_zero_refuses();
	test_boundary();
	test_sticky();
	test_unreadable_fails_closed();
	(void)printf("test_entropy: %d failures\n", fails);
	if (fails == 0)
		(void)printf("  NOTE: on the r6b8i image as measured 2026-09-30 the\n"
		             "  first fixture IS the board: entropy_avail = 0, so LOGIN\n"
		             "  and PWSET answer NOENTROPY and no session can be issued.\n");
	return fails == 0 ? 0 : 1;
}
