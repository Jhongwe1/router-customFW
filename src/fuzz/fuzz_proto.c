/* src/fuzz/fuzz_proto.c -- AFL++ harness for brokerd's request decoder.
 *
 * Reads ONE file named on the command line and drives proto_decode_req over
 * those bytes, then drives the same bytes through the incremental machine in
 * three different chunkings.  The four runs must agree on accept-vs-refuse and,
 * when they accept, on every decoded field.  A disagreement is an abort(), so
 * the fuzzer counts it as a crash: that turns "the decoder mishandles a split
 * read" -- the bug class a one-shot harness cannot see -- into a finding.
 *
 * It is a plain main(argc, argv), so the same binary runs under afl-fuzz, under
 * a coverage build, and by hand on a corpus file.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "proto.h"

#define MAXIN (PROTO_REQ_MAX + 4096)

static void die(const char *why)
{
	(void)fprintf(stderr, "fuzz_proto: DISAGREEMENT: %s\n", why);
	abort();
}

/* Feed buf in chunks of `step` (0 = all at once). */
static int drive(const uint8_t *buf, size_t n, size_t step,
                 struct proto_req *out, size_t *used_out)
{
	struct proto_rx rx;
	size_t off = 0, total = 0;
	int st = PRX_HDR;

	proto_rx_init(&rx);
	if (step == 0)
		step = n ? n : 1;
	while (off < n) {
		size_t take = n - off;
		size_t used = 0;

		if (take > step)
			take = step;
		st = proto_rx_feed(&rx, buf + off, take, &used);
		total += used;
		off += take;
		if (st < 0 || st == PRX_DONE)
			break;
	}
	if (n == 0) {
		size_t used = 0;

		st = proto_rx_feed(&rx, buf, 0, &used);
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

static int same(const struct proto_req *a, const struct proto_req *b)
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

int main(int argc, char **argv)
{
	static uint8_t buf[MAXIN];
	struct proto_req r0, r1, r2, r3;
	size_t n = 0, u1 = 0, u2 = 0, u3 = 0;
	int c0, c1, c2, c3;
	FILE *f;

	if (argc < 2) {
		(void)fprintf(stderr, "usage: fuzz_proto FILE\n");
		return 2;
	}
	f = fopen(argv[1], "rb");
	if (f == 0)
		return 2;
	n = fread(buf, 1, sizeof(buf), f);
	(void)fclose(f);

	memset(&r0, 0, sizeof(r0));
	memset(&r1, 0, sizeof(r1));
	memset(&r2, 0, sizeof(r2));
	memset(&r3, 0, sizeof(r3));

	c0 = proto_decode_req(buf, n, &r0);
	c1 = drive(buf, n, 0, &r1, &u1);        /* one shot through the machine */
	c2 = drive(buf, n, 1, &r2, &u2);        /* one byte at a time */
	c3 = drive(buf, n, 7, &r3, &u3);        /* an awkward chunk size */

	if ((c0 < 0) != (c1 < 0))
		die("one-shot decode vs one-shot machine");
	if ((c0 < 0) != (c2 < 0))
		die("one-shot decode vs bytewise");
	if ((c0 < 0) != (c3 < 0))
		die("one-shot decode vs 7-byte chunks");
	if (c0 < 0) {
		/* All four refused.  The error code must be the same too: a
		 * decoder that refuses for different reasons depending on how the
		 * bytes arrived has state it should not have. */
		if (c0 != c1 || c0 != c2 || c0 != c3)
			die("different refusal reasons for the same bytes");
		return 0;
	}
	if (!same(&r0, &r1) || !same(&r0, &r2) || !same(&r0, &r3))
		die("decoded fields differ between chunkings");
	if ((size_t)c0 != u1 || (size_t)c0 != u2 || (size_t)c0 != u3)
		die("consumed byte counts differ between chunkings");
	if ((size_t)c0 != (size_t)PROTO_REQ_HDR + r0.body_len)
		die("consumed is not 48 + body_len");
	if (r0.body_len > PROTO_REQ_BODY_MAX)
		die("an accepted body_len is over the cap");
	return 0;
}
