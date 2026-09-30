/* src/fuzz/fuzz_http.c -- one file in, the HTTP request parser over it.
 *
 * Plain main(argc, argv): the harness reads one file and returns, so it works
 * under afl-clang-fast's persistent-free mode, under a gcov build, and from a
 * shell with a single input.  That matters because the coverage figure and the
 * fuzzing run have to be over the SAME code path; a harness that only exists in
 * one of the two is a coverage number about nothing.
 *
 * WHAT IS FUZZED.  http_feed() and http_decode_path(), which together are
 * everything an unauthenticated peer can reach before a route is chosen.  The
 * input is fed in CHUNKS of a size taken from the input's own first byte, so the
 * incremental state machine is exercised at every boundary rather than always
 * being handed one big buffer -- a parser can be correct on whole buffers and
 * wrong across a split, and the split is the interesting half.
 *
 * WHAT IS NOT FUZZED HERE.  The routes, the broker codec and the config store.
 * Nothing in this file talks to a socket and nothing allocates.
 */

#include "http.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define IN_MAX (1 << 16)

int main(int argc, char **argv)
{
	static unsigned char in[IN_MAX];
	struct http_parser ps;
	struct http_req rq;
	FILE *f;
	size_t n, off;
	size_t chunk;
	char decoded[HTTP_PATH_MAX];

	if (argc < 2)
		return 0;
	f = fopen(argv[1], "rb");
	if (f == NULL)
		return 0;
	n = fread(in, 1, sizeof(in), f);
	(void)fclose(f);
	if (n == 0)
		return 0;

	/* The first byte picks the chunk size, 1..64.  Everything from that byte
	 * on is the request, so a one-byte input is still a legal (empty) one. */
	chunk = (size_t)(in[0] & 0x3f) + 1;

	http_parse_init(&ps, &rq);
	off = 1;
	while (off < n) {
		size_t take = (n - off < chunk) ? (n - off) : chunk;
		size_t used = 0;
		int rc = http_feed(&ps, in + off, take, &used);

		if (rc != 0)
			break;
		if (used == 0)
			break;                 /* no progress: stop, do not spin */
		off += used;
	}

	/* And the decoder on its own, over the same bytes as a request target, so
	 * a target that no request line would ever carry is still reached. */
	{
		size_t tl = (n - 1 < 1024) ? n - 1 : 1024;
		int dl = 0;

		if (tl > 0)
			dl = http_decode_path((const char *)in + 1, tl, decoded,
					      sizeof(decoded));
		/* http_mime() is called with an attacker-controlled name in
		 * routes.c, so it belongs in the fuzzer's reach.  量 2026-09-30:
		 * the first version of this harness called neither it nor
		 * http_reason() nor http_parse_all(), and those three functions
		 * were 35 of the 63 unreached lines in http.c -- the reason the
		 * pre-registered 85 % line threshold was missed at 84.96 %.  The
		 * answer was to connect the harness, not to lower the number. */
		if (dl > 0) {
			const char *t = http_mime(decoded);

			if (t != NULL && t[0] == '\0')
				abort();       /* a table entry with no type */
		}
	}

	/* The one-shot entry the route layer and the tests use. */
	{
		struct http_req r2;
		int rc2 = http_parse_all(in + 1, n - 1, &r2);

		if (rc2 == 1 && r2.pathlen != strlen(r2.path))
			abort();
		/* Every status this program can answer with must have a reason
		 * phrase; `http_reason` returning its default for a status the
		 * parser produced would put "Error" on the wire. */
		if (rc2 < 0) {
			const char *why = http_reason(-rc2);

			if (why == NULL || why[0] == '\0')
				abort();
			if (strcmp(why, "Error") == 0)
				abort();      /* a status with no phrase */
		}
	}

	/* Read something out of the result so no compiler can decide the parse was
	 * dead code. */
	if (rq.pathlen > sizeof(rq.path))
		abort();                       /* an invariant, not a check */
	if (rq.body_len > HTTP_BODY_MAX)
		abort();
	return 0;
}
