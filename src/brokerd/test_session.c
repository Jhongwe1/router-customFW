/* src/brokerd/test_session.c -- session lifecycle, LRU, the TTL boundary, and
 * what the constant-time compare can and cannot be tested for.
 */
#include <stdio.h>
#include <string.h>

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

static void fixture(struct broker *bk)
{
	bk_init(bk);
	bk->use_fake_clock = 1;
	bk->fake_now = 1000;
	/* `R7-8`: this was "/dev/null" while brokerd linked src/brokerd/stub/cfg_stub.c,
	 * whose cfg_store() returned 0 without touching a file.  The real cfg_store
	 * WRITES a 4,096-byte slot and then READS IT BACK to verify, and a read-back
	 * from /dev/null is 0 bytes, so every SET and PWSET answered ST_IO (6).  A
	 * real file per test binary is what the product does; the file is created by
	 * cfg_store itself (O_RDWR|O_CREAT, 0600). */
	bk->cfg_path = "/tmp/rlxbk-store-test_session.bin";
}

static void test_new_and_find(void)
{
	struct broker bk;
	struct bk_sess *a, *b;
	uint8_t tok[PROTO_TOK_LEN];

	fixture(&bk);
	a = bk_sess_new(&bk);
	CHECK(a != 0, "a session");
	if (a == 0)
		return;
	memcpy(tok, a->tok, PROTO_TOK_LEN);
	CHECK(bk_sess_count(&bk) == 1, "one session");
	CHECK(bk_sess_find(&bk, tok) == a, "find by token");

	/* The token and the CSRF token are different 16-byte values, and
	 * neither is all zeroes. */
	CHECK(memcmp(a->tok, a->csrf, PROTO_TOK_LEN) != 0, "tok != csrf");
	{
		uint8_t z[PROTO_TOK_LEN];

		memset(z, 0, sizeof(z));
		CHECK(memcmp(a->tok, z, PROTO_TOK_LEN) != 0, "tok not zeroes");
		CHECK(memcmp(a->csrf, z, PROTO_TOK_LEN) != 0, "csrf not zeroes");
		CHECK(bk_sess_find(&bk, z) == 0, "an all-zero token finds nothing");
	}
	/* A second session gets different bytes.  16 random bytes colliding is
	 * not a test failure that can be distinguished from a broken RNG, so
	 * this is the cheap smoke test and nothing more. */
	b = bk_sess_new(&bk);
	CHECK(b != 0 && b != a, "a second session");
	if (b != 0)
		CHECK(memcmp(a->tok, b->tok, PROTO_TOK_LEN) != 0, "distinct tokens");

	/* One wrong byte anywhere must miss. */
	{
		int i;

		for (i = 0; i < PROTO_TOK_LEN; i++) {
			uint8_t t2[PROTO_TOK_LEN];

			memcpy(t2, tok, sizeof(t2));
			t2[i] = (uint8_t)(t2[i] ^ 0x01);
			CHECK(bk_sess_find(&bk, t2) == 0,
			      "token with byte %d flipped must miss", i);
		}
	}
}

static void test_ttl_boundary(void)
{
	struct broker bk;
	struct bk_sess *s;
	uint8_t tok[PROTO_TOK_LEN];

	fixture(&bk);
	s = bk_sess_new(&bk);
	CHECK(s != 0, "session");
	if (s == 0)
		return;
	memcpy(tok, s->tok, PROTO_TOK_LEN);

	bk.fake_now += BK_SESS_TTL - 1;                 /* 899 s idle */
	CHECK(bk_sess_find(&bk, tok) != 0, "alive at TTL-1 (%d s)", BK_SESS_TTL - 1);
	bk.fake_now += 1;                                /* 900 s idle */
	CHECK(bk_sess_find(&bk, tok) == 0, "expired at TTL (%d s)", BK_SESS_TTL);
	CHECK(bk_sess_count(&bk) == 0, "the expired slot is freed");

	/* Use restarts the clock, so 899 + 899 is still alive. */
	fixture(&bk);
	s = bk_sess_new(&bk);
	if (s == 0)
		return;
	memcpy(tok, s->tok, PROTO_TOK_LEN);
	bk.fake_now += BK_SESS_TTL - 1;
	s = bk_sess_find(&bk, tok);
	CHECK(s != 0, "alive");
	if (s != 0)
		s->last = bk_now(&bk);                  /* what dispatch does */
	bk.fake_now += BK_SESS_TTL - 1;
	CHECK(bk_sess_find(&bk, tok) != 0, "use restarted the idle clock");
}

static void test_lru(void)
{
	struct broker bk;
	uint8_t tok[BK_NSESS + 1][PROTO_TOK_LEN];
	int i;

	fixture(&bk);
	for (i = 0; i < BK_NSESS; i++) {
		struct bk_sess *s = bk_sess_new(&bk);

		CHECK(s != 0, "session %d", i);
		if (s == 0)
			return;
		memcpy(tok[i], s->tok, PROTO_TOK_LEN);
		bk.fake_now += 1;                        /* distinct ->last */
	}
	CHECK(bk_sess_count(&bk) == BK_NSESS, "%d sessions", BK_NSESS);

	/* Touch 0 so it is no longer the least recently used; 1 becomes it. */
	{
		struct bk_sess *s = bk_sess_find(&bk, tok[0]);

		CHECK(s != 0, "session 0 alive");
		if (s != 0)
			s->last = bk_now(&bk);
	}
	/* The 5th evicts exactly one, and it is session 1. */
	{
		struct bk_sess *s = bk_sess_new(&bk);

		CHECK(s != 0, "the 5th session");
		if (s == 0)
			return;
		memcpy(tok[BK_NSESS], s->tok, PROTO_TOK_LEN);
	}
	CHECK(bk_sess_count(&bk) == BK_NSESS, "still %d after eviction", BK_NSESS);
	CHECK(bk_sess_find(&bk, tok[1]) == 0, "session 1 was the LRU victim");
	CHECK(bk_sess_find(&bk, tok[0]) != 0, "session 0 survived (it was touched)");
	CHECK(bk_sess_find(&bk, tok[2]) != 0, "session 2 survived");
	CHECK(bk_sess_find(&bk, tok[3]) != 0, "session 3 survived");
	CHECK(bk_sess_find(&bk, tok[BK_NSESS]) != 0, "the 5th is present");

	/* A stale token after eviction is a miss, not a match on the reused
	 * slot: the slot was wiped, so its old bytes are gone. */
	CHECK(bk_sess_find(&bk, tok[1]) == 0, "the evicted token stays stale");
}

static void test_logout_and_drop(void)
{
	struct broker bk;
	struct proto_req rq;
	struct proto_resp rs;
	struct bk_sess *s;
	uint8_t tok[PROTO_TOK_LEN];

	fixture(&bk);
	s = bk_sess_new(&bk);
	CHECK(s != 0, "session");
	if (s == 0)
		return;
	memcpy(tok, s->tok, PROTO_TOK_LEN);

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_LOGOUT;
	memcpy(rq.session, s->tok, PROTO_TOK_LEN);
	memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_OK, "LOGOUT: %u", (unsigned)rs.status);
	CHECK(bk_sess_find(&bk, tok) == 0, "the token is invalid after LOGOUT");
	CHECK(bk_sess_count(&bk) == 0, "the slot is free");

	/* A second LOGOUT with the same (now dead) token is AUTH for httpd. */
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_AUTH, "LOGOUT twice: %u", (unsigned)rs.status);
	/* ... and OK for root, which needs no session. */
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_OK, "root LOGOUT is idempotent: %u", (unsigned)rs.status);
}

/* What bk_ct_eq is testable for: correctness.  Its TIMING is not observable in
 * a unit test -- see the report's mutation section. */
static void test_ct_eq(void)
{
	uint8_t a[16], b[16];
	int i;

	for (i = 0; i < 16; i++) {
		a[i] = (uint8_t)i;
		b[i] = (uint8_t)i;
	}
	CHECK(bk_ct_eq(a, b, 16) == 1, "equal");
	for (i = 0; i < 16; i++) {
		b[i] = (uint8_t)(b[i] ^ 0x80);
		CHECK(bk_ct_eq(a, b, 16) == 0, "differ at byte %d", i);
		b[i] = (uint8_t)(b[i] ^ 0x80);
	}
	CHECK(bk_ct_eq(a, b, 0) == 1, "zero length is equal");
	CHECK(bk_ct_eq(0, b, 16) == 0, "a null side is never equal");
	CHECK(bk_ct_eq(a, 0, 16) == 0, "a null side is never equal");
}

int main(void)
{
	(void)printf("test_session\n");
	test_new_and_find();
	test_ttl_boundary();
	test_lru();
	test_logout_and_drop();
	test_ct_eq();
	(void)printf("test_session: %d failures\n", fails);
	return fails == 0 ? 0 : 1;
}
