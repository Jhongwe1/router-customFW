/* src/brokerd/test_authz.c -- the authorisation matrix, driven by the table.
 *
 * The matrix is walked, not listed: for every row of ops.c's rules[] x every
 * peer uid in {0, 100, 101, 1000} x session {absent, valid, stale} x csrf
 * {correct, wrong}, the expected status is DERIVED FROM THE ROW and compared
 * with what bk_dispatch() answers.  A row added to the table without a rule
 * therefore fails here rather than opening a door quietly.
 *
 * The named negatives SPEC-R7 cares about are asserted separately at the end,
 * in the words of the brief, so a change to the derivation cannot silently
 * weaken them: uid 100 without a session cannot GET; uid 101 cannot SET and
 * cannot read a third key; a wrong CSRF cannot SET.
 */
#include <stdio.h>
#include <string.h>

#include "brokerd.h"
#include "test_help.h"

#define TEST_PW "adminpw1"

static int fails;
static long cells;

#define CHECK(cond, ...) do { \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

/* A broker whose entropy file says 4096 and whose random source is real, so
 * LOGIN/PWSET are not short-circuited by the entropy gate in this file.
 * ping_bin is /bin/echo and the timeout 2 s: op_ping must still fork, execve a
 * real binary, read a pipe and reap a child, but the matrix does not pay 10 s
 * a cell for it.  The argv it builds is the production one either way. */
static void fixture(struct broker *bk, const char *entropy_file)
{
	bk_init(bk);
	bk->entropy_path = entropy_file;
	bk->use_fake_clock = 1;
	bk->fake_now = 10000;
	/* `R7-8`: this was "/dev/null" while brokerd linked src/brokerd/stub/cfg_stub.c,
	 * whose cfg_store() returned 0 without touching a file.  The real cfg_store
	 * WRITES a 4,096-byte slot and then READS IT BACK to verify, and a read-back
	 * from /dev/null is 0 bytes, so every SET and PWSET answered ST_IO (6).  A
	 * real file per test binary is what the product does; the file is created by
	 * cfg_store itself (O_RDWR|O_CREAT, 0600). */
	bk->cfg_path = "/tmp/rlxbk-store-test_authz.bin";
	bk->ping_bin = "/bin/echo";
	bk->ping_timeout_s = 2;
	(void)bk_entropy_ready(bk);
	bk_test_set_pw(bk, TEST_PW);
}

static void write_file(const char *path, const char *text)
{
	if (bk_test_write_file(path, text) != 0) {
		(void)printf("  FAIL cannot write %s\n", path);
		fails++;
	}
}

static void mk(struct proto_req *rq, uint8_t op)
{
	memset(rq, 0, sizeof(*rq));
	rq->version = PROTO_VERSION;
	rq->op = op;
	switch (op) {
	case OP_GET:
		proto_put_be16(rq->body, CFGID_LAN_IPADDR);
		rq->body_len = 2;
		break;
	case OP_SET:
		proto_put_be16(rq->body, 0x0020);      /* dhcpd.enable, rw */
		proto_put_be16(rq->body + 2, 1);
		rq->body[4] = 1;
		rq->body_len = 5;
		break;
	case OP_PING:
		rq->body[0] = 127; rq->body[1] = 0; rq->body[2] = 0;
		rq->body[3] = 1;   rq->body[4] = 1;
		rq->body_len = 5;
		break;
	case OP_LOGIN:
		memcpy(rq->body, "whatever", 8);
		rq->body_len = 8;
		break;
	case OP_PWSET:
		rq->body[0] = 0;
		rq->body[1] = 8;
		memcpy(rq->body + 2, "newpass1", 8);
		rq->body_len = 10;
		break;
	default:
		rq->body_len = 0;
		break;
	}
}

/* What the table says the answer must be, for the cases the table decides.
 * Returns 1 and sets *want when the row alone settles it; 0 when the answer
 * depends on the op's own body or state (then only "not PERM/AUTH" is checked). */
static int expect(const struct bk_op_rule *r, uid_t uid, int sess, int csrf_ok,
                  uint8_t *want)
{
	if (!r->supported) { *want = ST_NOTSUP; return 1; }
	if (uid != BK_UID_ROOT && uid != BK_UID_HTTPD && uid != BK_UID_DNSFWD) {
		*want = ST_PERM; return 1;
	}
	if (uid == BK_UID_HTTPD && !r->allow_100) { *want = ST_PERM; return 1; }
	if (uid == BK_UID_DNSFWD && !r->allow_101) { *want = ST_PERM; return 1; }
	/* need_session is uid 100's requirement ONLY.  uid 101 cannot obtain a
	 * session, so reading this flag for it would refuse the one op SPEC § 6
	 * grants it -- which is the bug this line used to hide. */
	if (uid == BK_UID_HTTPD && r->need_session) {
		if (sess != 1) { *want = ST_AUTH; return 1; }   /* absent or stale */
		if (r->need_csrf && !csrf_ok) { *want = ST_PERM; return 1; }
	}
	return 0;
}

static void walk(void)
{
	static const uid_t uids[] = { 0, 100, 101, 1000 };
	struct broker bk;
	int oi, ui, si, ci;

	write_file("/tmp/rlxbk_ent_full", "4096\n");

	for (oi = 0; oi < bk_op_count(); oi++) {
		const struct bk_op_rule *r = bk_op_at(oi);

		for (ui = 0; ui < 4; ui++) {
			for (si = 0; si < 3; si++) {      /* 0 none 1 valid 2 stale */
				for (ci = 0; ci < 2; ci++) {
					struct proto_req rq;
					struct proto_resp rs;
					struct bk_sess *s;
					uint8_t want = 0;
					int decided;

					fixture(&bk, "/tmp/rlxbk_ent_full");
					mk(&rq, r->op);
					if (si != 0) {
						s = bk_sess_new(&bk);
						if (s == 0) {
							(void)printf("  FAIL no session (urandom?)\n");
							fails++;
							continue;
						}
						memcpy(rq.session, s->tok, PROTO_TOK_LEN);
						memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
						if (si == 2)
							bk.fake_now += BK_SESS_TTL;
					}
					if (ci == 1)
						rq.csrf[0] = (uint8_t)(rq.csrf[0] ^ 0xFF);
					cells++;
					CHECK(bk_dispatch(&bk, &rq, uids[ui], &rs) == 0,
					      "%s uid=%lu: dispatch failed",
					      r->name, (unsigned long)uids[ui]);
					decided = expect(r, uids[ui], si, ci == 0, &want);
					if (!decided) {
						/* The table let it through, so the
						 * answer is the op's.  With the
						 * fixture's known password, LOGIN
						 * and PWSET are a wrong secret and
						 * must be AUTH; every other op must
						 * succeed. */
						want = (r->op == OP_LOGIN ||
						        r->op == OP_PWSET)
						     ? ST_AUTH : ST_OK;
					}
					CHECK(rs.status == want,
					      "%s uid=%lu sess=%d csrf_ok=%d: "
					      "status %u want %u (%s)",
					      r->name, (unsigned long)uids[ui],
					      si, ci == 0,
					      (unsigned)rs.status, (unsigned)want,
					      decided ? "table" : "op");
					bk_sess_drop_all(&bk);
				}
			}
		}
	}
	(void)printf("  matrix: %ld cells over %d ops x 4 uids x 3 session "
	             "states x 2 csrf states\n", cells, bk_op_count());
}

/* The named negatives, spelled out. */
static void named_negatives(void)
{
	struct broker bk;
	struct proto_req rq;
	struct proto_resp rs;
	struct bk_sess *s;

	write_file("/tmp/rlxbk_ent_full", "4096\n");

	/* uid 100 without a session cannot GET */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_GET);
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_AUTH, "httpd GET with no session: %u", (unsigned)rs.status);

	/* ... and can with one */
	s = bk_sess_new(&bk);
	CHECK(s != 0, "session");
	if (s != 0) {
		memcpy(rq.session, s->tok, PROTO_TOK_LEN);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
		(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
		CHECK(rs.status == ST_OK, "httpd GET with a session: %u",
		      (unsigned)rs.status);
		CHECK(rs.body_len == 8, "one TLV of a 4-byte IPV4 = 8 bytes, got %lu",
		      (unsigned long)rs.body_len);
	}

	/* root GETs without any session */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_GET);
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_OK, "root GET without a session: %u", (unsigned)rs.status);

	/* uid 101 reads its two keys */
	mk(&rq, OP_GET);
	proto_put_be16(rq.body, CFGID_DNS_UPSTREAM);
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_OK, "dnsfwd GET dns.upstream: %u", (unsigned)rs.status);
	proto_put_be16(rq.body, CFGID_LAN_IPADDR);
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_OK, "dnsfwd GET lan.ipaddr: %u", (unsigned)rs.status);

	/* uid 101 cannot read a third key */
	proto_put_be16(rq.body, 0x0023);            /* dhcpd.lease */
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_PERM, "dnsfwd GET a third key: %u", (unsigned)rs.status);

	/* ... nor sneak it in beside an allowed one */
	proto_put_be16(rq.body, CFGID_LAN_IPADDR);
	proto_put_be16(rq.body + 2, 0x0023);
	rq.body_len = 4;
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_PERM, "dnsfwd GET allowed+third: %u", (unsigned)rs.status);

	/* uid 101 cannot SET */
	mk(&rq, OP_SET);
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_PERM, "dnsfwd SET: %u", (unsigned)rs.status);

	/* nobody but root reads admin.pwhash */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	s = bk_sess_new(&bk);
	mk(&rq, OP_GET);
	proto_put_be16(rq.body, CFGID_ADMIN_PWHASH);
	if (s != 0) {
		memcpy(rq.session, s->tok, PROTO_TOK_LEN);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
	}
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_PERM, "httpd GET admin.pwhash: %u", (unsigned)rs.status);

	/* a wrong CSRF cannot SET, and the right one can */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	s = bk_sess_new(&bk);
	CHECK(s != 0, "session");
	if (s != 0) {
		mk(&rq, OP_SET);
		memcpy(rq.session, s->tok, PROTO_TOK_LEN);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
		rq.csrf[15] = (uint8_t)(rq.csrf[15] ^ 0x01);
		(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
		CHECK(rs.status == ST_PERM, "httpd SET with a wrong CSRF: %u",
		      (unsigned)rs.status);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
		(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
		CHECK(rs.status == ST_OK, "httpd SET with the right CSRF: %u",
		      (unsigned)rs.status);
	}

	/* httpd may not SET a read-only key even with a good session+csrf */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	s = bk_sess_new(&bk);
	if (s != 0) {
		memset(&rq, 0, sizeof(rq));
		rq.version = PROTO_VERSION;
		rq.op = OP_SET;
		proto_put_be16(rq.body, 0x0060);       /* http.port, web = r */
		proto_put_be16(rq.body + 2, 2);
		rq.body[4] = 0x1F; rq.body[5] = 0x90;
		rq.body_len = 6;
		memcpy(rq.session, s->tok, PROTO_TOK_LEN);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
		(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
		CHECK(rs.status == ST_PERM, "httpd SET a web=r key: %u",
		      (unsigned)rs.status);
		/* root may */
		(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
		CHECK(rs.status == ST_OK, "root SET a web=r key: %u",
		      (unsigned)rs.status);
	}

	/* SET refuses non-ascending TLVs (duplicates are impossible) */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_SET;
	proto_put_be16(rq.body, 0x0020);
	proto_put_be16(rq.body + 2, 1);
	rq.body[4] = 1;
	proto_put_be16(rq.body + 5, 0x0020);       /* same id again */
	proto_put_be16(rq.body + 7, 1);
	rq.body[9] = 0;
	rq.body_len = 10;
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_INVAL, "SET duplicate id: %u", (unsigned)rs.status);
	CHECK(rs.body_len == 2 && proto_be16(rs.body) == 0x0020,
	      "INVAL carries the key id");

	/* UPDATE_* are NOTSUP for everyone, root included */
	{
		uint8_t o;

		for (o = 0x20; o <= 0x22; o++) {
			mk(&rq, o);
			(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
			CHECK(rs.status == ST_NOTSUP, "op %02x root: %u",
			      o, (unsigned)rs.status);
		}
	}
	/* an op that is not in the table at all */
	mk(&rq, 0x7F);
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_NOTSUP, "op 7f: %u", (unsigned)rs.status);

	/* client_ip is honoured only from uid 100.  Drive it through the rate
	 * limiter: a uid-101-claimed ip must not create a bucket for it. */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_LOGIN);
	rq.client_ip = 0x0A0100FEu;
	(void)bk_dispatch(&bk, &rq, BK_UID_DNSFWD, &rs);
	CHECK(rs.status == ST_PERM, "dnsfwd LOGIN: %u", (unsigned)rs.status);
	CHECK(bk_rl_peek(&bk, 0x0A0100FEu) == 0,
	      "a uid-101 client_ip must not reach the bucket table");
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(bk_rl_peek(&bk, 0x0A0100FEu) != 0,
	      "a uid-100 client_ip must reach the bucket table");

	/* STATUS: the reduced set without a session, the full set with one */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_STATUS);
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_OK, "httpd STATUS no session: %u", (unsigned)rs.status);
	{
		size_t off = 0;
		int n = 0, saw_ent = 0, saw_up = 0, saw_rdy = 0, saw_ver = 0;
		uint16_t t, l;
		const uint8_t *v;

		while (proto_tlv_get(rs.body, rs.body_len, &off, &t, &v, &l) == 0) {
			n++;
			if (t == BKS_ENTROPY) saw_ent = 1;
			if (t == BKS_UPTIME)  saw_up = 1;
			if (t == BKS_AUTHRDY) saw_rdy = 1;
			if (t == BKS_VERSION) saw_ver = 1;
		}
		CHECK(n == 3, "STATUS without a session: %d TLVs, want 3", n);
		CHECK(saw_up && saw_ver && saw_rdy, "the three public rows");
		CHECK(!saw_ent, "entropy_avail must not be in the public set");
	}
	s = bk_sess_new(&bk);
	if (s != 0) {
		memcpy(rq.session, s->tok, PROTO_TOK_LEN);
		memcpy(rq.csrf, s->csrf, PROTO_TOK_LEN);
		(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
		{
			size_t off = 0;
			int n = 0, saw_ent = 0;
			uint16_t t, l;
			const uint8_t *v;

			while (proto_tlv_get(rs.body, rs.body_len, &off, &t, &v, &l) == 0) {
				n++;
				if (t == BKS_ENTROPY) saw_ent = 1;
			}
			CHECK(n == 8, "STATUS with a session: %d TLVs, want 8", n);
			CHECK(saw_ent, "entropy_avail present with a session");
		}
	}
	/* root sees the full set with no session at all */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_STATUS);
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	{
		size_t off = 0;
		int n = 0;
		uint16_t t, l;
		const uint8_t *v;

		while (proto_tlv_get(rs.body, rs.body_len, &off, &t, &v, &l) == 0)
			n++;
		CHECK(n == 8, "root STATUS: %d TLVs, want 8", n);
	}

	/* REBOOT: the flag is set, and only after the table let it through */
	fixture(&bk, "/tmp/rlxbk_ent_full");
	mk(&rq, OP_REBOOT);
	(void)bk_dispatch(&bk, &rq, BK_UID_HTTPD, &rs);
	CHECK(rs.status == ST_AUTH, "httpd REBOOT with no session: %u",
	      (unsigned)rs.status);
	CHECK(bk.pending_reboot == 0, "a refused REBOOT must not arm the reboot");
	(void)bk_dispatch(&bk, &rq, BK_UID_ROOT, &rs);
	CHECK(rs.status == ST_OK && bk.pending_reboot == 1, "root REBOOT arms it");
}

int main(void)
{
	(void)printf("test_authz\n");
	walk();
	named_negatives();
	(void)printf("test_authz: %ld cells, %d failures\n", cells, fails);
	return fails == 0 ? 0 : 1;
}
