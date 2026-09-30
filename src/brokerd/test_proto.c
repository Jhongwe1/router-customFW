/* src/brokerd/test_proto.c -- the codec, and the decoder sweep.
 *
 * THE SWEEP IS THE POINT.  For a valid request per op, every single-byte
 * corruption at every offset of the 48-byte header (48 x 255 cases) and every
 * truncation at every length 0..48+body are fed to the decoder, twice: once as
 * one buffer and once byte at a time through the incremental machine.  Each
 * case must EITHER decode to a request identical to the un-corrupted one (when
 * the corrupted byte does not change meaning: only within the session, csrf and
 * client_ip fields can a change be legal, and then the fields differ, so
 * "identical" is checked field by field against what the bytes now say) OR be
 * refused with a negative PROTO_E_*.  No case may crash, hang or report a
 * consumed length that is not 48 + the body_len the bytes carry.
 *
 * THE MUTATION CONTROL lives in the Makefile target `mutants`, which does not
 * touch proto.c: it sed-copies it with the body_len bound turned into `if (0)`
 * and links this same test against the copy.  The run must FAIL.  A suite that
 * cannot be made to fail is not evidence, and the copy keeps the shipped file
 * free of a switch that could be flipped.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "proto.h"

static int fails;
static long cases;

#define CHECK(cond, ...) do { \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

static const uint8_t ops[] = {
	OP_GET, OP_SET, OP_REBOOT, OP_STATUS, OP_PING,
	OP_LOGIN, OP_LOGOUT, OP_PWSET, OP_UPDATE_BEGIN
};
#define NOPS ((int)(sizeof(ops) / sizeof(ops[0])))

/* A representative body per op, so the sweep exercises a real length. */
static uint32_t body_for(uint8_t op, uint8_t *b, size_t cap)
{
	memset(b, 0, cap);
	switch (op) {
	case OP_GET:    b[0] = 0x00; b[1] = 0x10; b[2] = 0x00; b[3] = 0x30; return 4;
	case OP_SET:    b[0] = 0x00; b[1] = 0x20; b[2] = 0x00; b[3] = 0x01;
	                b[4] = 0x01; return 5;
	case OP_PING:   b[0] = 10; b[1] = 1; b[2] = 1; b[3] = 2; b[4] = 3; return 5;
	case OP_LOGIN:  memcpy(b, "hunter2xx", 9); return 9;
	case OP_PWSET:  b[0] = 4; memcpy(b + 1, "oldp", 4);
	                b[5] = 8; memcpy(b + 6, "newpass1", 8); return 14;
	default:        return 0;
	}
}

static void mk_req(struct proto_req *rq, uint8_t op)
{
	int i;

	memset(rq, 0, sizeof(*rq));
	rq->version = PROTO_VERSION;
	rq->op = op;
	rq->flags = 0;
	for (i = 0; i < PROTO_TOK_LEN; i++) {
		rq->session[i] = (uint8_t)(0xA0 + i);
		rq->csrf[i] = (uint8_t)(0x50 + i);
	}
	rq->client_ip = 0x0A010164u;
	rq->body_len = body_for(op, rq->body, sizeof(rq->body));
}

static int req_eq(const struct proto_req *a, const struct proto_req *b)
{
	if (a->version != b->version || a->op != b->op || a->flags != b->flags)
		return 0;
	if (a->client_ip != b->client_ip || a->body_len != b->body_len)
		return 0;
	if (memcmp(a->session, b->session, PROTO_TOK_LEN) != 0)
		return 0;
	if (memcmp(a->csrf, b->csrf, PROTO_TOK_LEN) != 0)
		return 0;
	if (a->body_len != 0 && memcmp(a->body, b->body, a->body_len) != 0)
		return 0;
	return 1;
}

/* Decode by feeding one byte at a time, so a split-read bug shows up as a
 * disagreement with the one-shot decode. */
static int decode_bytewise(const uint8_t *buf, size_t n, struct proto_req *out,
                           size_t *used_out)
{
	struct proto_rx rx;
	size_t i, total = 0;
	int st = PRX_HDR;

	proto_rx_init(&rx);
	for (i = 0; i < n; i++) {
		size_t used = 0;

		st = proto_rx_feed(&rx, buf + i, 1, &used);
		total += used;
		if (st < 0 || st == PRX_DONE)
			break;
	}
	if (used_out != 0)
		*used_out = total;
	if (st < 0)
		return st;
	if (st != PRX_DONE)
		return PROTO_E_SHORT;
	*out = rx.req;
	return (int)total;
}

/* An INDEPENDENT model of SPEC § 6's header grammar, written from the spec's
 * field order rather than from proto.c.  Returns 0 and fills *exp when the
 * frame must decode, or the exact negative code that must come back.
 *
 * The EXACT code matters, not just "refused": a frame whose body_len is over
 * the cap must say BODYLEN and not SHORT, because SHORT tells a caller to wait
 * for more bytes that will never make the frame legal.  Comparing exact codes
 * is also what lets the sweep catch the removed bound (mutation M1) -- with
 * only a sign comparison, M1 hides behind proto_rx_feed's second bound check
 * and the whole sweep stays green. */
static int expect_from_bytes(const uint8_t *w, size_t n, struct proto_req *exp)
{
	uint32_t blen;

	if (n < PROTO_REQ_HDR)
		return PROTO_E_SHORT;
	if (proto_be32(w + PROTO_RQ_O_MAGIC) != PROTO_REQ_MAGIC)
		return PROTO_E_MAGIC;
	if (w[PROTO_RQ_O_VERSION] != PROTO_VERSION)
		return PROTO_E_VERSION;
	if (proto_be16(w + PROTO_RQ_O_FLAGS) != 0)
		return PROTO_E_FLAGS;
	blen = proto_be32(w + PROTO_RQ_O_BODYLEN);
	if (blen > PROTO_REQ_BODY_MAX)
		return PROTO_E_BODYLEN;
	if (n < (size_t)PROTO_REQ_HDR + (size_t)blen)
		return PROTO_E_SHORT;
	memset(exp, 0, sizeof(*exp));
	exp->version = w[PROTO_RQ_O_VERSION];
	exp->op = w[PROTO_RQ_O_OP];
	exp->flags = 0;
	memcpy(exp->session, w + PROTO_RQ_O_SESSION, PROTO_TOK_LEN);
	memcpy(exp->csrf, w + PROTO_RQ_O_CSRF, PROTO_TOK_LEN);
	exp->client_ip = proto_be32(w + PROTO_RQ_O_CLIENTIP);
	exp->body_len = blen;
	if (blen != 0)
		memcpy(exp->body, w + PROTO_REQ_HDR, blen);
	return 0;
}

/* One case: the buffer w[0..n) must behave exactly as expect_from_bytes says,
 * both one-shot and bytewise. */
static void one_case(const uint8_t *w, size_t n, const char *what)
{
	struct proto_req got, gotb, exp;
	size_t usedb = 0;
	int rc, rcb, want;

	cases++;
	want = expect_from_bytes(w, n, &exp);
	memset(&got, 0, sizeof(got));
	memset(&gotb, 0, sizeof(gotb));
	rc = proto_decode_req(w, n, &got);
	rcb = decode_bytewise(w, n, &gotb, &usedb);

	if (want == 0) {
		CHECK(rc > 0, "%s: should decode, rc=%d n=%lu", what, rc,
		      (unsigned long)n);
		if (rc > 0) {
			CHECK((size_t)rc == (size_t)PROTO_REQ_HDR + exp.body_len,
			      "%s: consumed %d want %lu", what, rc,
			      (unsigned long)(PROTO_REQ_HDR + exp.body_len));
			CHECK(req_eq(&got, &exp), "%s: fields differ", what);
		}
		CHECK(rcb > 0, "%s: bytewise should decode, rc=%d", what, rcb);
		if (rcb > 0)
			CHECK(req_eq(&gotb, &exp), "%s: bytewise fields differ", what);
	} else {
		CHECK(rc == want, "%s: rc=%d want %d", what, rc, want);
		CHECK(rcb == want, "%s: bytewise rc=%d want %d", what, rcb, want);
	}
	/* Whatever happened, the two paths must agree on accept vs refuse. */
	CHECK((rc < 0) == (rcb < 0), "%s: one-shot and bytewise disagree "
	      "(%d vs %d)", what, rc, rcb);
}

static void test_roundtrip(void)
{
	int i;

	for (i = 0; i < NOPS; i++) {
		struct proto_req rq, back;
		uint8_t w[PROTO_REQ_MAX];
		int n, rc;

		mk_req(&rq, ops[i]);
		n = proto_encode_req(&rq, w, sizeof(w));
		CHECK(n == (int)(PROTO_REQ_HDR + rq.body_len),
		      "op %02x encode n=%d", ops[i], n);
		rc = proto_decode_req(w, (size_t)n, &back);
		CHECK(rc == n, "op %02x decode rc=%d want %d", ops[i], rc, n);
		CHECK(req_eq(&rq, &back), "op %02x round trip differs", ops[i]);
		/* The header bytes are where SPEC pins them. */
		CHECK(proto_be32(w) == PROTO_REQ_MAGIC, "magic");
		CHECK(w[4] == 1, "version byte");
		CHECK(w[5] == ops[i], "op byte");
		CHECK(proto_be16(w + 6) == 0, "flags");
		CHECK(proto_be32(w + 40) == rq.client_ip, "client_ip BE");
		CHECK(proto_be32(w + 44) == rq.body_len, "body_len BE");
	}
}

static void test_resp_roundtrip(void)
{
	static const uint8_t sts[] = { ST_OK, ST_BADREQ, ST_PERM, ST_AUTH,
	                               ST_LOCKED, ST_INVAL, ST_IO, ST_NOENT,
	                               ST_BUSY, ST_NOTSUP, ST_NOENTROPY };
	size_t i;

	for (i = 0; i < sizeof(sts) / sizeof(sts[0]); i++) {
		struct proto_resp rs, back;
		uint8_t w[PROTO_RESP_MAX];
		int n, rc;

		memset(&rs, 0, sizeof(rs));
		rs.version = PROTO_VERSION;
		rs.status = sts[i];
		rs.body_len = (uint32_t)(i * 7);
		memset(rs.body, (int)(0x30 + i), rs.body_len);
		n = proto_encode_resp(&rs, w, sizeof(w));
		CHECK(n == (int)(PROTO_RESP_HDR + rs.body_len), "resp encode");
		rc = proto_decode_resp(w, (size_t)n, &back);
		CHECK(rc == n, "resp decode rc=%d", rc);
		CHECK(back.status == rs.status && back.body_len == rs.body_len,
		      "resp fields");
		CHECK(memcmp(back.body, rs.body, rs.body_len) == 0, "resp body");
	}
	/* A response claiming more body than the buffer holds is short, not a
	 * read past the end. */
	{
		uint8_t w[PROTO_RESP_HDR];
		struct proto_resp back;

		memset(w, 0, sizeof(w));
		proto_put_be32(w, PROTO_RESP_MAGIC);
		w[4] = 1;
		proto_put_be32(w + 8, 4096);
		CHECK(proto_decode_resp(w, sizeof(w), &back) == PROTO_E_SHORT,
		      "resp short");
		proto_put_be32(w + 8, 4097);
		CHECK(proto_decode_resp(w, sizeof(w), &back) == PROTO_E_BODYLEN,
		      "resp over-long body_len");
	}
}

static void test_sweep(void)
{
	int i;
	long corrupt = 0, trunc = 0;

	/* NOPS representative frames, plus one MAXIMAL frame (body_len 2048).
	 * The maximal one is what lets a single-byte corruption move body_len
	 * DOWNWARDS below what is delivered -- trailing bytes, which the codec
	 * accepts and the connection layer refuses -- and UPWARDS over the cap
	 * with the body actually present. */
	for (i = 0; i <= NOPS; i++) {
		struct proto_req rq;
		uint8_t base[PROTO_REQ_MAX], w[PROTO_REQ_MAX];
		int n, off, d;
		size_t len;
		uint8_t opname;

		if (i < NOPS) {
			mk_req(&rq, ops[i]);
			opname = ops[i];
		} else {
			mk_req(&rq, OP_LOGIN);
			rq.body_len = PROTO_REQ_BODY_MAX;
			memset(rq.body, 0x5A, PROTO_REQ_BODY_MAX);
			opname = 0xFF;          /* the maximal frame */
		}
		n = proto_encode_req(&rq, base, sizeof(base));
		CHECK(n > 0, "sweep encode");
		if (n <= 0)
			continue;

		/* every single-byte corruption at every header offset */
		for (off = 0; off < PROTO_REQ_HDR; off++) {
			for (d = 1; d < 256; d++) {
				char what[64];

				memcpy(w, base, (size_t)n);
				w[off] = (uint8_t)(base[off] ^ (uint8_t)d);
				(void)snprintf(what, sizeof(what),
				               "op%02x corrupt off=%d xor=%02x",
				               opname, off, d);
				one_case(w, (size_t)n, what);
				corrupt++;
			}
		}
		/* truncation at every length 0..48+body */
		for (len = 0; len <= (size_t)n; len++) {
			char what[64];

			memcpy(w, base, (size_t)n);
			(void)snprintf(what, sizeof(what), "op%02x trunc=%lu",
			               opname, (unsigned long)len);
			one_case(w, len, what);
			trunc++;
		}
	}
	(void)printf("  sweep: %ld corruption cases, %ld truncation cases, "
	             "%ld decoder calls (each run one-shot AND bytewise)\n",
	             corrupt, trunc, cases);
}

/* The body_len bound, on its own, with the exact value SPEC pins. */
static void test_bodylen_bound(void)
{
	uint8_t w[PROTO_REQ_MAX];
	struct proto_req rq, got;
	int n;

	mk_req(&rq, OP_LOGIN);
	n = proto_encode_req(&rq, w, sizeof(w));
	CHECK(n > 0, "bound encode");

	proto_put_be32(w + PROTO_RQ_O_BODYLEN, PROTO_REQ_BODY_MAX);
	CHECK(proto_decode_req(w, (size_t)n, &got) == PROTO_E_SHORT,
	      "2048 is legal but the bytes are not there");
	proto_put_be32(w + PROTO_RQ_O_BODYLEN, PROTO_REQ_BODY_MAX + 1);
	CHECK(proto_decode_req(w, (size_t)n, &got) == PROTO_E_BODYLEN,
	      "2049 must be refused");
	proto_put_be32(w + PROTO_RQ_O_BODYLEN, 0xFFFFFFFFu);
	CHECK(proto_decode_req(w, (size_t)n, &got) == PROTO_E_BODYLEN,
	      "0xFFFFFFFF must be refused");
	/* And the same through the incremental machine, where the mutation
	 * would smash rx.req.body. */
	{
		struct proto_rx rx;
		size_t used = 0;
		uint8_t big[PROTO_REQ_MAX];

		memcpy(big, w, (size_t)n);
		proto_put_be32(big + PROTO_RQ_O_BODYLEN, 0x7FFFFFFFu);
		proto_rx_init(&rx);
		CHECK(proto_rx_feed(&rx, big, sizeof(big), &used) == PROTO_E_BODYLEN,
		      "incremental must refuse 0x7FFFFFFF");
	}
}

static void test_tlv(void)
{
	uint8_t b[64];
	size_t off = 0;
	uint16_t t, l;
	const uint8_t *v;

	CHECK(proto_tlv_put_u32(b, sizeof(b), &off, 0x8001, 0x01020304) == 0, "tlv put");
	CHECK(off == 8, "tlv off=%lu", (unsigned long)off);
	off = 0;
	CHECK(proto_tlv_get(b, 8, &off, &t, &v, &l) == 0, "tlv get");
	CHECK(t == 0x8001 && l == 4 && proto_be32(v) == 0x01020304u, "tlv value");
	/* A length past the end is refused, not read. */
	off = 0;
	proto_put_be16(b + 2, 5);
	CHECK(proto_tlv_get(b, 8, &off, &t, &v, &l) == -1, "tlv over-long");
	/* Capacity is checked against what is left, not against the total. */
	off = 60;
	CHECK(proto_tlv_put_u32(b, sizeof(b), &off, 1, 0) == -1, "tlv no room");
	off = 0;
	CHECK(proto_tlv_get(b, 3, &off, &t, &v, &l) == -1, "tlv header short");
}

static void test_null_and_zero(void)
{
	struct proto_req rq;
	struct proto_rx rx;
	uint8_t b[8];
	size_t used = 99;

	CHECK(proto_decode_req(0, 0, &rq) == PROTO_E_SHORT ||
	      proto_decode_req(0, 0, &rq) < 0, "null buf n=0");
	CHECK(proto_decode_req(b, 0, 0) == PROTO_E_INVAL, "null out");
	proto_rx_init(&rx);
	CHECK(proto_rx_feed(&rx, b, 0, &used) == PRX_HDR, "zero-length feed");
	CHECK(used == 0, "zero-length used");
	CHECK(proto_rx_feed(0, b, 1, &used) == PROTO_E_INVAL, "null rx");
	/* A machine that refused stays refused and consumes nothing more. */
	proto_rx_init(&rx);
	memset(b, 0, sizeof(b));
	CHECK(proto_rx_feed(&rx, b, 8, &used) == PRX_HDR, "8 zero bytes: want more");
	{
		uint8_t z[PROTO_REQ_HDR];

		memset(z, 0, sizeof(z));
		proto_rx_init(&rx);
		CHECK(proto_rx_feed(&rx, z, sizeof(z), &used) == PROTO_E_MAGIC,
		      "48 zero bytes: bad magic");
		CHECK(proto_rx_feed(&rx, z, sizeof(z), &used) == PROTO_E_MAGIC,
		      "stuck in error");
		CHECK(used == 0, "an errored machine consumes nothing");
	}
}

int main(void)
{
	(void)printf("test_proto\n");
	test_roundtrip();
	test_resp_roundtrip();
	test_tlv();
	test_null_and_zero();
	test_bodylen_bound();
	test_sweep();
	(void)printf("test_proto: %ld cases, %d failures\n", cases, fails);
	return fails == 0 ? 0 : 1;
}
