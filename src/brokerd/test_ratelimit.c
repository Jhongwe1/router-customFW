/* src/brokerd/test_ratelimit.c -- the LOGIN bucket: the 5th failure locks, the
 * lock's seconds are on the wire, the doubling, the 3600 s cap, and a POSITIVE
 * CONTROL that a correct password still succeeds once the lock expires.
 *
 * Without that control the whole file proves only that the broker can say no.
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

#define GOOD_PW "correct-horse"
#define BAD_PW  "wrong"
#define IP_A 0x0A010164u
#define IP_B 0x0A010165u

static void fixture(struct broker *bk)
{
	if (bk_test_write_file("/tmp/rlxbk_ent_full", "4096\n") != 0) {
		(void)printf("  FAIL cannot write the entropy fixture\n");
		fails++;
	}
	bk_init(bk);
	bk->entropy_path = "/tmp/rlxbk_ent_full";
	bk->use_fake_clock = 1;
	bk->fake_now = 5000;
	/* `R7-8`: this was "/dev/null" while brokerd linked src/brokerd/stub/cfg_stub.c,
	 * whose cfg_store() returned 0 without touching a file.  The real cfg_store
	 * WRITES a 4,096-byte slot and then READS IT BACK to verify, and a read-back
	 * from /dev/null is 0 bytes, so every SET and PWSET answered ST_IO (6).  A
	 * real file per test binary is what the product does; the file is created by
	 * cfg_store itself (O_RDWR|O_CREAT, 0600). */
	bk->cfg_path = "/tmp/rlxbk-store-test_ratelimit.bin";
	(void)bk_entropy_ready(bk);
	bk_test_set_pw(bk, GOOD_PW);
}

/* One LOGIN as uid 100 from ip, returning the status; *secs gets the LOCKED
 * body when there is one. */
static uint8_t login(struct broker *bk, uint32_t ip, const char *pw, uint32_t *secs)
{
	struct proto_req rq;
	struct proto_resp rs;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_LOGIN;
	rq.client_ip = ip;
	rq.body_len = (uint32_t)strlen(pw);
	memcpy(rq.body, pw, rq.body_len);
	(void)bk_dispatch(bk, &rq, BK_UID_HTTPD, &rs);
	if (secs != 0) {
		*secs = 0;
		if (rs.status == ST_LOCKED && rs.body_len == 4)
			*secs = proto_be32(rs.body);
	}
	return rs.status;
}

static void test_fifth_failure_locks(void)
{
	struct broker bk;
	uint32_t secs = 0;
	int i;

	fixture(&bk);
	/* Four failures are refused but not locked. */
	for (i = 0; i < 4; i++) {
		uint8_t st = login(&bk, IP_A, BAD_PW, &secs);

		CHECK(st == ST_AUTH, "failure %d: status %u (want AUTH)", i + 1,
		      (unsigned)st);
	}
	/* The 5th attempt is itself refused with AUTH, and the lock it sets is
	 * what the 6th sees.  (The counter reaches 5 inside bk_rl_fail, which
	 * runs after the answer is decided.) */
	CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_AUTH, "the 5th failure");
	CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED, "locked after five");
	CHECK(secs == BK_RL_LOCK0, "first lock is %d s, reported %u",
	      BK_RL_LOCK0, (unsigned)secs);

	/* The lock is reported even for the CORRECT password: the bucket is
	 * checked before the KDF, so being right does not get you past it. */
	CHECK(login(&bk, IP_A, GOOD_PW, &secs) == ST_LOCKED,
	      "a correct password is still locked out");
	CHECK(secs == BK_RL_LOCK0, "seconds still reported");

	/* The seconds count down. */
	bk.fake_now += 30;
	CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED, "still locked at 30 s");
	CHECK(secs == BK_RL_LOCK0 - 30, "remaining %u, want %d",
	      (unsigned)secs, BK_RL_LOCK0 - 30);

	/* Another IP is unaffected: the table is per client IP. */
	CHECK(login(&bk, IP_B, BAD_PW, &secs) == ST_AUTH,
	      "a second IP is not locked by the first");
}

static void test_doubling_and_cap(void)
{
	struct broker bk;
	uint32_t secs = 0, expect = BK_RL_LOCK0;
	int round;

	fixture(&bk);
	for (round = 0; round < 8; round++) {
		int i;

		/* Five failures, then read the lock. */
		for (i = 0; i < 5; i++)
			(void)login(&bk, IP_A, BAD_PW, &secs);
		CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED,
		      "round %d locked", round);
		CHECK(secs == expect, "round %d: lock %u s, want %u",
		      round, (unsigned)secs, (unsigned)expect);
		/* Walk past it so the next five can re-lock. */
		bk.fake_now += (long)secs + 1;
		expect = expect * 2;
		if (expect > BK_RL_LOCKCAP)
			expect = BK_RL_LOCKCAP;
	}
	CHECK(expect == BK_RL_LOCKCAP, "the sequence reached the cap");
	/* And it stays at the cap rather than doubling past it. */
	{
		int i;

		for (i = 0; i < 5; i++)
			(void)login(&bk, IP_A, BAD_PW, &secs);
		CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED, "capped lock");
		CHECK(secs == BK_RL_LOCKCAP, "capped at %d s, got %u",
		      BK_RL_LOCKCAP, (unsigned)secs);
	}
}

/* THE POSITIVE CONTROL.  Everything above is a refusal; this is the one that
 * says the door still opens. */
static void test_success_after_lock_expires(void)
{
	struct broker bk;
	struct proto_req rq;
	struct proto_resp rs;
	uint32_t secs = 0;
	int i;

	fixture(&bk);
	/* Prove the correct password works BEFORE the lock, so a later failure
	 * cannot be blamed on the fixture. */
	CHECK(login(&bk, IP_A, GOOD_PW, &secs) == ST_OK,
	      "control: the correct password works to begin with");
	bk_sess_drop_all(&bk);

	for (i = 0; i < 5; i++)
		(void)login(&bk, IP_A, BAD_PW, &secs);
	CHECK(login(&bk, IP_A, GOOD_PW, &secs) == ST_LOCKED, "locked");
	CHECK(secs == BK_RL_LOCK0, "lock seconds");

	bk.fake_now += BK_RL_LOCK0;                /* exactly at the boundary */
	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_LOGIN;
	rq.client_ip = IP_A;
	rq.body_len = (uint32_t)strlen(GOOD_PW);
	memcpy(rq.body, GOOD_PW, rq.body_len);
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_OK, "the lock expires and the door opens: %u",
	      (unsigned)rs.status);
	CHECK(rs.body_len == 2 * PROTO_TOK_LEN + 4,
	      "LOGIN body is session+csrf+ttl = %d bytes, got %lu",
	      2 * PROTO_TOK_LEN + 4, (unsigned long)rs.body_len);
	if (rs.body_len == 2 * PROTO_TOK_LEN + 4) {
		CHECK(proto_be32(rs.body + 2 * PROTO_TOK_LEN) == (uint32_t)BK_SESS_TTL,
		      "the ttl on the wire is %d", BK_SESS_TTL);
		CHECK(bk_sess_find(&bk, rs.body) != 0,
		      "the token in the body is the live session");
	}
	/* A success clears the escalation: the next lock starts at 60 s again. */
	for (i = 0; i < 5; i++)
		(void)login(&bk, IP_A, BAD_PW, &secs);
	CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED, "re-locked");
	CHECK(secs == BK_RL_LOCK0, "a success reset the escalation, got %u",
	      (unsigned)secs);
}

/* A locked bucket must not be evictable by filling the table from other
 * addresses: that would make the lock a formality. */
static void test_lock_survives_table_pressure(void)
{
	struct broker bk;
	uint32_t secs = 0;
	int i;

	fixture(&bk);
	for (i = 0; i < 5; i++)
		(void)login(&bk, IP_A, BAD_PW, &secs);
	CHECK(login(&bk, IP_A, BAD_PW, &secs) == ST_LOCKED, "locked");

	/* 32 other addresses, twice the table. */
	for (i = 0; i < 32; i++) {
		bk.fake_now += 1;
		(void)login(&bk, 0x0B000000u + (uint32_t)i, BAD_PW, &secs);
	}
	CHECK(login(&bk, IP_A, GOOD_PW, &secs) == ST_LOCKED,
	      "the lock survived 32 other addresses");
	CHECK(bk_rl_peek(&bk, IP_A) != 0, "the bucket is still in the table");
}

static void test_root_is_exempt(void)
{
	struct broker bk;
	struct proto_req rq;
	struct proto_resp rs;
	int i;

	fixture(&bk);
	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_LOGIN;
	rq.client_ip = IP_A;                 /* ignored: not uid 100 */
	rq.body_len = (uint32_t)strlen(BAD_PW);
	memcpy(rq.body, BAD_PW, rq.body_len);
	for (i = 0; i < 20; i++) {
		(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
		CHECK(rs.status == ST_AUTH, "root LOGIN %d: %u", i,
		      (unsigned)rs.status);
	}
	CHECK(bk_rl_peek(&bk, IP_A) == 0, "root never touches a bucket");
	CHECK(bk_rl_peek(&bk, 0) == 0, "and not bucket 0 either");
}

int main(void)
{
	(void)printf("test_ratelimit\n");
	test_fifth_failure_locks();
	test_doubling_and_cap();
	test_success_after_lock_expires();
	test_lock_survives_table_pressure();
	test_root_is_exempt();
	(void)printf("test_ratelimit: %d failures\n", fails);
	return fails == 0 ? 0 : 1;
}
