/* src/fuzz/fuzz_dns.c -- one file in, both of dnsfwd's parsers driven.
 *
 * Plain `main(argc, argv)` so the same binary works under afl++ (persistent
 * mode off, `@@` file input), under a coverage build, and by hand.
 *
 * THE BUFFER IS HEAP-ALLOCATED AT EXACTLY THE INPUT LENGTH, and that is not a
 * detail.  A fixed 2 KiB stack array would absorb a one-byte overread: the
 * byte past the datagram would still be inside a valid object and no sanitizer
 * would say a word.  Sized exactly, ASan puts a redzone immediately after the
 * last byte, so a bound that is off by one is a reported error rather than a
 * silent read.  The planted defect this harness is checked against
 * (`make fuzz` builds `fuzz_dns_bug`) is exactly that: the label-length bound
 * `pos + 1 + c > n` changed to `> n + 1`.
 *
 * Both directions are driven on every input, because a query parser and a
 * reply parser share the name decoder and differ only in their header rules --
 * one input therefore reaches both, and a reply-only path cannot hide.
 */

#include "dns.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CAP (DNS_MSG_MAX + 64)   /* enough to reach the over-512 refusal */

/* Consume every field so that no compiler can decide the parse was dead. */
static unsigned long sink;

static void eat_name(const uint8_t *msg, size_t n, size_t off)
{
	uint8_t nm[DNS_NAME_MAX], nl = 0;
	size_t  next = 0;

	if (dns_decode_name(msg, n, off, nm, sizeof nm, &nl, &next) == 0) {
		sink += nl;
		sink += next;
		sink += (unsigned long)dns_name_eq(nm, nl, nm, nl);
	}
}

int main(int argc, char **argv)
{
	uint8_t *buf;
	uint8_t  tmp[CAP];
	size_t   n = 0;
	FILE    *f;

	if (argc < 2) {
		(void)fprintf(stderr, "usage: fuzz_dns FILE\n");
		return 2;
	}
	f = fopen(argv[1], "rb");
	if (f == 0) return 2;
	n = fread(tmp, 1, sizeof tmp, f);
	(void)fclose(f);

	/* Exactly n bytes.  malloc(0) may return NULL, which is fine: the parsers
	 * must not dereference a zero-length buffer. */
	buf = (uint8_t *)malloc(n == 0 ? 1 : n);
	if (buf == 0) return 2;
	memcpy(buf, tmp, n);

	{
		struct dns_query q;
		struct dns_reply r;
		int              rc;

		rc = dns_parse_query(buf, n, &q);
		sink += (unsigned long)(-rc);
		if (rc == 0) {
			sink += q.h.id + q.q.qtype + q.q.qclass + q.q.nlen;
			sink += (unsigned long)dns_name_eq(q.q.name, q.q.nlen,
			                                  q.q.name, q.q.nlen);
			/* Re-encode: the encoder is on the path a real forwarder takes. */
			{
				uint8_t out[DNS_MSG_MAX];
				int     k = dns_encode_query(&q.q, q.h.id, 1, out, sizeof out);

				sink += (unsigned long)k;
				k = dns_encode_error(q.h.id, &q.q, DNS_RCODE_FORMERR,
				                     out, sizeof out);
				sink += (unsigned long)k;
			}
		}

		rc = dns_parse_reply(buf, n, &r);
		sink += (unsigned long)(-rc);
		if (rc == 0) {
			unsigned i;

			sink += r.h.id + r.n_an + r.n_walked + r.q.nlen;
			for (i = 0; i < r.n_an; i++) {
				sink += r.an[i].type + r.an[i].rdlen + r.an[i].ttl;
				/* A CNAME's target is a name inside rdata: decoding it is
				 * what a forwarder that looked at answers would do, and it
				 * drives the decoder from an attacker-chosen offset. */
				if (r.an[i].type == DNS_TYPE_CNAME)
					eat_name(buf, n, r.an[i].rdoff);
			}
		}

		/* The name decoder on its own, at the question offset and at an
		 * offset the input itself picks -- so the fuzzer can steer where the
		 * decode starts, not only what it reads. */
		if (n >= DNS_HDR_LEN + 1) {
			eat_name(buf, n, DNS_HDR_LEN);
			eat_name(buf, n, (size_t)buf[0] % n);
		}
	}

	free(buf);
	/* Exit 0 always: a refusal is the correct behaviour, not a finding.  The
	 * findings are crashes, and the sanitizers report those. */
	return sink == 0x5A5A5A5Au ? 1 : 0;
}
