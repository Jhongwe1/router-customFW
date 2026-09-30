/* test_dns.c -- dnsfwd's parser battery, anti-spoof tests and policy tests.
 *
 * Runs on the host, opens no socket (the bench owns this machine's
 * interfaces): every syscall dnsfwd would make goes through `struct dns_io`,
 * and this file supplies a fake one with a fake clock and a counting random
 * source.
 *
 * TIME-BOUNDED ON PURPOSE.  `alarm()` is armed around every compression-
 * pointer case, because the defect those cases exist to catch is an infinite
 * loop, and a test that hangs reports nothing.  Compiled with
 * -DDNSFWD_MUT_NO_PTR_GUARD the self-pointer case must hit that alarm;
 * compiled with -DDNSFWD_MUT_NO_QMATCH the "different question" anti-spoof
 * case must go red.  The Makefile's `test` target runs the unmutated suite
 * first and refuses to interpret the mutants unless it passed.
 */

#include "dns.h"

#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* ------------------------------------------------------------------------ */
/* Harness                                                                  */
/* ------------------------------------------------------------------------ */

static unsigned g_checks, g_fail;
static const char *g_case = "?";

static void ck(int cond, int line, const char *fmt, ...)
{
	va_list ap;

	g_checks++;
	if (cond) return;
	g_fail++;
	(void)fprintf(stderr, "FAIL %s:%d [%s] ", "test_dns.c", line, g_case);
	va_start(ap, fmt);
	(void)vfprintf(stderr, fmt, ap);
	va_end(ap);
	(void)fputc('\n', stderr);
}

#define CK(c, ...) ck((c) ? 1 : 0, __LINE__, __VA_ARGS__)

/* Async-signal-safe: write(2) only, no stdio.  `(void)` does not suppress
 * warn_unused_result on write(), so the result is taken into a variable. */
static void on_alarm(int s)
{
	static const char m[] =
		"FAIL: TIMED OUT (a decoder did not terminate) in case ";
	ssize_t w;

	(void)s;
	w = write(2, m, sizeof m - 1);
	w = write(2, g_case, strlen(g_case));
	w = write(2, "\n", 1);
	(void)w;
	_exit(3);
}

/* Hex vectors, written out so the bytes in the test ARE the bytes asserted. */
static size_t hx(uint8_t *out, size_t cap, const char *hex)
{
	size_t n = 0;
	int    hi = -1;

	for (; *hex; hex++) {
		int v;

		if (*hex == ' ' || *hex == '\n' || *hex == '\t') continue;
		if      (*hex >= '0' && *hex <= '9') v = *hex - '0';
		else if (*hex >= 'a' && *hex <= 'f') v = *hex - 'a' + 10;
		else if (*hex >= 'A' && *hex <= 'F') v = *hex - 'A' + 10;
		else { (void)fprintf(stderr, "bad hex '%c'\n", *hex); _exit(4); }
		if (hi < 0) hi = v;
		else {
			if (n >= cap) { (void)fprintf(stderr, "hex overflow\n"); _exit(4); }
			out[n++] = (uint8_t)((hi << 4) | v);
			hi = -1;
		}
	}
	if (hi >= 0) { (void)fprintf(stderr, "odd hex digits\n"); _exit(4); }
	return n;
}

#define QNAME "03 777777 07 6578616d706c65 03 636f6d 00"

/* www.example.com A IN, id 0x1234, RD=1 */
#define V_Q_A    "1234 0100 0001 0000 0000 0000 " QNAME " 0001 0001"
/* the same, AAAA */
#define V_Q_AAAA "1234 0100 0001 0000 0000 0000 " QNAME " 001c 0001"
/* NOERROR, one A: 93.184.216.34, name compressed to offset 12 */
#define V_R_A    "1234 8180 0001 0001 0000 0000 " QNAME " 0001 0001 " \
                 "c00c 0001 0001 0000012c 0004 5db8d822"
/* NOERROR, one AAAA: 2606:2800:220:1:248:1893:25c8:1946 */
#define V_R_AAAA "1234 8180 0001 0001 0000 0000 " QNAME " 001c 0001 " \
                 "c00c 001c 0001 0000012c 0010 " \
                 "26062800 02200001 02481893 25c81946"
/* NXDOMAIN with an SOA in AUTHORITY; every name in it compressed */
#define V_R_NX   "1234 8183 0001 0000 0001 0000 " QNAME " 0001 0001 " \
                 "c010 0006 0001 00000e10 0021 " \
                 "03 6e7331 c010 04 686f7374 c010 " \
                 "00000001 00000e10 00000258 00093a80 0000012c"
/* CNAME chain: www.example.com CNAME cdn.example.com, cdn.example.com A.
 * RR2's name is a pointer to offset 0x2D, which is the `03 c d n` inside
 * RR1's rdata, which itself ends in a pointer to offset 0x10 -- a two-hop
 * compressed name, and the battery's positive control. */
#define V_R_CN   "1234 8180 0001 0002 0000 0000 " QNAME " 0001 0001 " \
                 "c00c 0005 0001 0000012c 0006 03 63646e c010 " \
                 "c02d 0001 0001 0000012c 0004 5db8d823"

/* ------------------------------------------------------------------------ */
/* 1. Scalars: the code must not depend on the host's byte order            */
/* ------------------------------------------------------------------------ */

static void t_endian(void)
{
	uint8_t b[4];

	g_case = "endian";
	CK(dns_get16((const uint8_t *)"\x12\x34") == 0x1234, "get16");
	CK(dns_get16((const uint8_t *)"\x00\xFF") == 0x00FF, "get16 low");
	CK(dns_get16((const uint8_t *)"\xFF\x00") == 0xFF00, "get16 high");
	CK(dns_get32((const uint8_t *)"\xDE\xAD\xBE\xEF") == 0xDEADBEEFu, "get32");
	dns_put16(b, 0xABCD);
	CK(b[0] == 0xAB && b[1] == 0xCD, "put16 %02X %02X", b[0], b[1]);
	dns_put32(b, 0x01020304u);
	CK(b[0] == 1 && b[1] == 2 && b[2] == 3 && b[3] == 4, "put32");
	/* Round trip through an odd address: MIPS-I faults on an unaligned
	 * halfword load, so this must go through the shift path. */
	{
		uint8_t pad[8];

		dns_put16(pad + 1, 0x7788);
		CK(dns_get16(pad + 1) == 0x7788, "unaligned round trip");
	}
}

/* ------------------------------------------------------------------------ */
/* 2. Known answer: encode and decode byte for byte                         */
/* ------------------------------------------------------------------------ */

static void t_known(void)
{
	uint8_t          v[600], enc[DNS_MSG_MAX];
	struct dns_query q;
	struct dns_reply r;
	size_t           n;
	int              rc;
	static const uint8_t wire_name[17] = {
		3,'w','w','w',7,'e','x','a','m','p','l','e',3,'c','o','m',0
	};

	g_case = "known/query-A";
	n = hx(v, sizeof v, V_Q_A);
	CK(n == 33, "query length %lu", (unsigned long)n);
	rc = dns_parse_query(v, n, &q);
	CK(rc == 0, "parse rc %d %s", rc, dns_strerr(rc));
	CK(q.h.id == 0x1234, "id %04X", q.h.id);
	CK(q.h.flags == 0x0100, "flags %04X", q.h.flags);
	CK(q.q.nlen == 17, "nlen %u", q.q.nlen);
	CK(memcmp(q.q.name, wire_name, 17) == 0, "decoded name bytes");
	CK(q.q.qtype == DNS_TYPE_A && q.q.qclass == DNS_CLASS_IN, "qtype/qclass");
	/* Re-encoding must reproduce the input byte for byte. */
	rc = dns_encode_query(&q.q, 0x1234, 1, enc, sizeof enc);
	CK(rc == (int)n, "encode len %d", rc);
	CK(rc > 0 && memcmp(enc, v, n) == 0, "encode is byte-identical");

	g_case = "known/query-AAAA";
	n = hx(v, sizeof v, V_Q_AAAA);
	rc = dns_parse_query(v, n, &q);
	CK(rc == 0 && q.q.qtype == DNS_TYPE_AAAA, "rc %d qtype %u", rc, q.q.qtype);

	g_case = "known/reply-A";
	n = hx(v, sizeof v, V_R_A);
	CK(n == 49, "reply length %lu", (unsigned long)n);
	rc = dns_parse_reply(v, n, &r);
	CK(rc == 0, "parse rc %d %s", rc, dns_strerr(rc));
	CK(r.h.id == 0x1234 && (r.h.flags & DNS_F_RCMASK) == DNS_RCODE_NOERROR,
	   "id/rcode");
	CK(r.n_an == 1 && r.n_walked == 1, "an %u walked %u", r.n_an, r.n_walked);
	CK(r.an[0].type == DNS_TYPE_A && r.an[0].rdlen == 4, "rr type/rdlen");
	CK(r.an[0].ttl == 300, "ttl %lu", (unsigned long)r.an[0].ttl);
	/* POSITIVE CONTROL for compression: the RR's name is `c0 0c` and must
	 * decode to the question's name. */
	CK(r.an[0].nlen == 17 && memcmp(r.an[0].name, wire_name, 17) == 0,
	   "compressed RR name decoded");
	CK(r.an[0].rdoff == 45, "rdoff %u", r.an[0].rdoff);
	CK(v[r.an[0].rdoff] == 0x5D && v[r.an[0].rdoff + 3] == 0x22, "rdata");

	g_case = "known/reply-AAAA";
	n = hx(v, sizeof v, V_R_AAAA);
	rc = dns_parse_reply(v, n, &r);
	CK(rc == 0, "rc %d %s", rc, dns_strerr(rc));
	CK(r.n_an == 1 && r.an[0].type == DNS_TYPE_AAAA && r.an[0].rdlen == 16,
	   "AAAA rr");
	CK(v[r.an[0].rdoff] == 0x26 && v[r.an[0].rdoff + 15] == 0x46, "AAAA rdata");

	g_case = "known/reply-NXDOMAIN";
	n = hx(v, sizeof v, V_R_NX);
	CK(n == 78, "nx length %lu", (unsigned long)n);
	rc = dns_parse_reply(v, n, &r);
	CK(rc == 0, "rc %d %s", rc, dns_strerr(rc));
	CK((r.h.flags & DNS_F_RCMASK) == DNS_RCODE_NXDOMAIN, "rcode %u",
	   r.h.flags & DNS_F_RCMASK);
	CK(r.n_an == 0 && r.n_walked == 1, "an %u walked %u (the SOA)",
	   r.n_an, r.n_walked);

	g_case = "known/reply-CNAME-chain";
	n = hx(v, sizeof v, V_R_CN);
	CK(n == 67, "cname length %lu", (unsigned long)n);
	rc = dns_parse_reply(v, n, &r);
	CK(rc == 0, "rc %d %s", rc, dns_strerr(rc));
	CK(r.n_an == 2, "an %u", r.n_an);
	CK(r.an[0].type == DNS_TYPE_CNAME && r.an[0].rdlen == 6, "rr1 CNAME");
	CK(r.an[1].type == DNS_TYPE_A && r.an[1].rdlen == 4, "rr2 A");
	{
		static const uint8_t cdn[17] = {
			3,'c','d','n',7,'e','x','a','m','p','l','e',3,'c','o','m',0
		};
		uint8_t nm[DNS_NAME_MAX], nl = 0;
		size_t  next = 0;

		/* RR2's name: two hops, 51 -> 45 -> 16.  The control that the guards
		 * refuse loops without refusing legitimate compression. */
		CK(r.an[1].nlen == 17 && memcmp(r.an[1].name, cdn, 17) == 0,
		   "rr2 two-hop compressed name (nlen %u)", r.an[1].nlen);
		/* And the CNAME target inside RR1's rdata decodes the same way. */
		rc = dns_decode_name(v, n, r.an[0].rdoff, nm, sizeof nm, &nl, &next);
		CK(rc == 0 && nl == 17 && memcmp(nm, cdn, 17) == 0,
		   "cname target rc %d nl %u", rc, nl);
	}
}

/* ------------------------------------------------------------------------ */
/* 3. The compression-pointer battery                                       */
/* ------------------------------------------------------------------------ */

struct ptr_case {
	const char *name;
	int         want;          /* 0 = must decode, else the DNSE_* expected */
};

static void ptr_run(const char *name, const uint8_t *msg, size_t n, size_t pos,
                    int want_err, unsigned *refused)
{
	uint8_t nm[DNS_NAME_MAX], nl = 0;
	size_t  next = 0;
	int     rc;

	g_case = name;
	/* Five seconds is generous for a bounded decoder and short enough that a
	 * hang is reported rather than waited out. */
	(void)alarm(5);
	rc = dns_decode_name(msg, n, pos, nm, sizeof nm, &nl, &next);
	(void)alarm(0);
	if (want_err == 0) {
		CK(rc == 0, "expected a decode, got %d %s", rc, dns_strerr(rc));
	} else {
		CK(rc < 0, "expected a refusal, got 0");
		if (rc < 0) (*refused)++;
		/* The specific code is asserted where it identifies which guard
		 * fired; a different refusal is still a refusal, so the message
		 * names both. */
		CK(rc == -want_err, "refused with %s, expected %s",
		   dns_strerr(rc), dns_strerr(want_err));
	}
}

static void t_ptr_battery(unsigned *cases, unsigned *refused)
{
	uint8_t b[600];
	size_t  i;

	/* (1) a pointer to itself.  THE classic infinite loop.  Ordered first so
	 * that the mutant's failure is this case and is reportable. */
	memset(b, 0, sizeof b);
	b[12] = 0xC0; b[13] = 0x0C;
	ptr_run("ptr/self", b, 64, 12, DNSE_PTR, refused); (*cases)++;

	/* (2) a forward pointer. */
	memset(b, 0, sizeof b);
	b[12] = 0xC0; b[13] = 0x20;
	ptr_run("ptr/forward", b, 64, 12, DNSE_PTR, refused); (*cases)++;

	/* (3) a two-pointer cycle: 20 -> 12 -> 20.  One hop of any 2-cycle must
	 * be forwards, so guard 1 alone already refuses this one. */
	memset(b, 0, sizeof b);
	b[20] = 0xC0; b[21] = 0x0C;
	b[12] = 0xC0; b[13] = 0x14;
	ptr_run("ptr/cycle2", b, 64, 20, DNSE_PTR, refused); (*cases)++;

	/* (4) the cycle the strictly-backwards rule PERMITS, and the reason
	 * guard 2 exists.  Entry 40 -> 20; labels from 20 reach a pointer at 30
	 * whose target 25 is below 30; labels from 25 reach the pointer at 40
	 * again.  Every target is below its own pointer's offset, so guard 1
	 * passes all three, and the walk revisits 20 for ever.  Guard 2 (targets
	 * must strictly decrease) is what refuses it. */
	memset(b, 0, sizeof b);
	b[20] = 0x01; b[21] = 'B';
	b[22] = 0x07;
	b[23] = 'a';  b[24] = 'b';
	b[25] = 0x01; b[26] = 'A';
	b[27] = 0x0C;
	b[28] = 'c';  b[29] = 'd';
	b[30] = 0xC0; b[31] = 0x19;            /* -> 25 */
	for (i = 32; i < 40; i++) b[i] = 'e';
	b[40] = 0xC0; b[41] = 0x14;            /* -> 20 */
	ptr_run("ptr/cycle3-backwards-legal", b, 64, 40, DNSE_PTR, refused);
	(*cases)++;

	/* (5) a chain of 200 strictly decreasing pointers: every one legal under
	 * guards 1 and 2, refused by the jump cap. */
	memset(b, 0, sizeof b);
	b[20] = 0x00;                          /* the root, if it were reached */
	for (i = 22; i <= 420; i += 2) {
		size_t t = i - 2;
		b[i]     = (uint8_t)(0xC0 | ((t >> 8) & 0x3F));
		b[i + 1] = (uint8_t)(t & 0xFF);
	}
	ptr_run("ptr/chain200", b, 512, 420, DNSE_JUMPS, refused); (*cases)++;

	/* (6) a pointer whose target is past the packet end.  Backwards implies
	 * below the end, so guard 1 is what refuses it. */
	memset(b, 0, sizeof b);
	b[12] = 0xC0; b[13] = 0xFF;
	ptr_run("ptr/past-end", b, 64, 12, DNSE_PTR, refused); (*cases)++;

	/* (6b) a pointer byte that IS the last byte: the two-byte read is short. */
	memset(b, 0, sizeof b);
	b[12] = 0xC0;
	ptr_run("ptr/truncated", b, 13, 12, DNSE_SHORT, refused); (*cases)++;

	/* (7) a 63-byte label followed by more than 255 bytes of name. */
	memset(b, 0, sizeof b);
	{
		size_t o = 12;
		int    k;

		for (k = 0; k < 5; k++) {
			b[o] = 63;
			memset(b + o + 1, 'x', 63);
			o += 64;
		}
		b[o] = 0;
		ptr_run("name/over255", b, o + 1, 12, DNSE_NAME, refused); (*cases)++;
	}

	/* (7b) the exact boundary, both sides.  63+63+63+61 labels plus the root
	 * is 255 bytes and must decode; one byte more must not. */
	{
		size_t o;
		int    k;

		memset(b, 0, sizeof b);
		o = 12;
		for (k = 0; k < 3; k++) { b[o] = 63; memset(b + o + 1, 'x', 63); o += 64; }
		b[o] = 61; memset(b + o + 1, 'y', 61); o += 62;
		b[o] = 0;
		ptr_run("name/exactly255", b, o + 1, 12, 0, refused); (*cases)++;

		memset(b, 0, sizeof b);
		o = 12;
		for (k = 0; k < 3; k++) { b[o] = 63; memset(b + o + 1, 'x', 63); o += 64; }
		b[o] = 62; memset(b + o + 1, 'y', 62); o += 63;
		b[o] = 0;
		ptr_run("name/256", b, o + 1, 12, DNSE_NAME, refused); (*cases)++;
	}

	/* (8) the two reserved top-bit patterns. */
	memset(b, 0, sizeof b);
	b[12] = 0x40;
	ptr_run("label/topbits-40", b, 64, 12, DNSE_LABEL, refused); (*cases)++;
	memset(b, 0, sizeof b);
	b[12] = 0x80;
	ptr_run("label/topbits-80", b, 64, 12, DNSE_LABEL, refused); (*cases)++;

	/* (9) a label whose length runs off the end. */
	memset(b, 0, sizeof b);
	b[12] = 20;
	ptr_run("label/off-end", b, 20, 12, DNSE_SHORT, refused); (*cases)++;

	/* (10) POSITIVE CONTROLS: a legal single-hop pointer, and the root. */
	memset(b, 0, sizeof b);
	b[12] = 3; b[13] = 'w'; b[14] = 'w'; b[15] = 'w'; b[16] = 0;
	b[20] = 0xC0; b[21] = 0x0C;
	ptr_run("ptr/legal-1hop", b, 64, 20, 0, refused); (*cases)++;
	{
		uint8_t nm[DNS_NAME_MAX], nl = 0;
		size_t  next = 0;
		int     rc;

		g_case = "ptr/legal-1hop-value";
		rc = dns_decode_name(b, 64, 20, nm, sizeof nm, &nl, &next);
		CK(rc == 0 && nl == 5 && nm[0] == 3 && nm[4] == 0, "nl %u rc %d",
		   nl, rc);
		CK(next == 22, "next %lu (a pointer is two bytes wherever it points)",
		   (unsigned long)next);
	}
	memset(b, 0, sizeof b);
	b[12] = 0;
	ptr_run("name/root", b, 64, 12, 0, refused); (*cases)++;
}

/* ------------------------------------------------------------------------ */
/* 4. Truncation and single-byte corruption sweep                           */
/* ------------------------------------------------------------------------ */

struct sweep_counts {
	unsigned trunc_cases, trunc_refused, trunc_accepted;
	unsigned corr_cases, corr_refused, corr_accepted;
};

static void inv_query(const struct dns_query *q, size_t n)
{
	CK(q->q.nlen <= DNS_NAME_MAX, "nlen %u out of bounds", q->q.nlen);
	CK(q->h.qd == 1, "accepted a query with qd %u", q->h.qd);
	(void)n;
}

static void inv_reply(const struct dns_reply *r, size_t n)
{
	unsigned i;

	CK(r->q.nlen <= DNS_NAME_MAX, "qname nlen %u", r->q.nlen);
	CK(r->n_an <= DNS_RR_KEEP, "n_an %u", r->n_an);
	CK(r->n_walked <= DNS_RR_WALK_MAX, "n_walked %u", r->n_walked);
	for (i = 0; i < r->n_an; i++) {
		CK(r->an[i].nlen <= DNS_NAME_MAX, "rr nlen %u", r->an[i].nlen);
		CK((size_t)r->an[i].rdoff + r->an[i].rdlen <= n,
		   "rr rdata %u+%u past %lu", r->an[i].rdoff, r->an[i].rdlen,
		   (unsigned long)n);
	}
}

static void sweep_one(const char *what, const char *hex,
                      struct sweep_counts *c)
{
	uint8_t          orig[600], v[600];
	struct dns_query q;
	struct dns_reply r;
	size_t           n, t;
	unsigned         k;
	static const uint8_t mut[5] = { 0x01, 0x80, 0xFF, 0x00, 0xC0 };

	n = hx(orig, sizeof orig, hex);
	g_case = what;

	/* Truncation at EVERY length below n.  A valid message stops being one at
	 * every prefix, because the parsers require the last byte consumed to be
	 * the last byte received. */
	for (t = 0; t < n; t++) {
		int rq, rr;

		memcpy(v, orig, t);
		(void)alarm(5);
		rq = dns_parse_query(v, t, &q);
		rr = dns_parse_reply(v, t, &r);
		(void)alarm(0);
		c->trunc_cases += 2;
		if (rq == 0) { c->trunc_accepted++; inv_query(&q, t); }
		else           c->trunc_refused++;
		if (rr == 0) { c->trunc_accepted++; inv_reply(&r, t); }
		else           c->trunc_refused++;
	}

	/* Single-byte corruption at EVERY offset (not a sample: n is at most 78
	 * and the whole sweep costs milliseconds), five values each.  The
	 * assertion is that nothing crashes -- address and UB sanitizers are the
	 * detector -- and that an accepted result still satisfies every bound. */
	for (t = 0; t < n; t++) {
		for (k = 0; k < 5; k++) {
			int rq, rr;

			memcpy(v, orig, n);
			v[t] = (uint8_t)(k < 3 ? (v[t] ^ mut[k]) : mut[k]);
			(void)alarm(5);
			rq = dns_parse_query(v, n, &q);
			rr = dns_parse_reply(v, n, &r);
			(void)alarm(0);
			c->corr_cases += 2;
			if (rq == 0) { c->corr_accepted++; inv_query(&q, n); }
			else           c->corr_refused++;
			if (rr == 0) { c->corr_accepted++; inv_reply(&r, n); }
			else           c->corr_refused++;
		}
	}
}

/* ------------------------------------------------------------------------ */
/* 5. The forwarder, over a fake I/O layer                                  */
/* ------------------------------------------------------------------------ */

#define FAKE_SENT_MAX 512

struct fake {
	uint32_t now;
	uint16_t next;
	int      rand_fail;
	int      send_fail;
	int      n_sent;
	struct {
		int      which;
		size_t   n;
		uint32_t addr;
		uint16_t port;
		uint8_t  buf[DNS_MSG_MAX];
	} sent[FAKE_SENT_MAX];
};

static int f_send(void *c, int which, const uint8_t *buf, size_t n,
                  uint32_t addr, uint16_t port)
{
	struct fake *f = (struct fake *)c;

	if (f->send_fail) return -1;
	if (f->n_sent < FAKE_SENT_MAX) {
		f->sent[f->n_sent].which = which;
		f->sent[f->n_sent].n     = n > DNS_MSG_MAX ? DNS_MSG_MAX : n;
		f->sent[f->n_sent].addr  = addr;
		f->sent[f->n_sent].port  = port;
		memcpy(f->sent[f->n_sent].buf, buf, f->sent[f->n_sent].n);
	}
	f->n_sent++;
	return (int)n;
}

static int f_rand16(void *c, uint16_t *out)
{
	struct fake *f = (struct fake *)c;

	if (f->rand_fail) return -5;
	*out = ++f->next;
	return 0;
}

static uint32_t f_now(void *c) { return ((struct fake *)c)->now; }
static void     f_log(void *c, const char *m) { (void)c; (void)m; }

#define IP(a, b, cc, d) (((uint32_t)(a) << 24) | ((uint32_t)(b) << 16) | \
                         ((uint32_t)(cc) << 8) | (uint32_t)(d))

static void fake_init(struct fake *f, struct dns_io *io, struct dnsfwd *d)
{
	memset(f, 0, sizeof *f);
	f->now     = 1000;
	io->send    = f_send;
	io->rand16  = f_rand16;
	io->now_ms  = f_now;
	io->logline = f_log;
	io->ctx     = f;
	dnsfwd_init(d, io);
	/* 10.1.1.1/24, upstream 10.1.1.2 -- SPEC-R7 s 4's defaults. */
	dnsfwd_config(d, IP(10,1,1,1), 0xFFFFFF00u, IP(10,1,1,2));
}

/* Build a reply for a question, with a chosen ID: the upstream's answer. */
static size_t mk_reply(uint8_t *out, uint16_t id, const struct dns_question *q,
                       uint32_t a)
{
	size_t o = 0;

	dns_put16(out + 0, id);
	dns_put16(out + 2, (uint16_t)(DNS_F_QR | DNS_F_RD | DNS_F_RA));
	dns_put16(out + 4, 1);
	dns_put16(out + 6, 1);
	dns_put16(out + 8, 0);
	dns_put16(out + 10, 0);
	o = DNS_HDR_LEN;
	memcpy(out + o, q->name, q->nlen); o += q->nlen;
	dns_put16(out + o, q->qtype);  o += 2;
	dns_put16(out + o, q->qclass); o += 2;
	out[o++] = 0xC0; out[o++] = 0x0C;
	dns_put16(out + o, DNS_TYPE_A); o += 2;
	dns_put16(out + o, DNS_CLASS_IN); o += 2;
	dns_put32(out + o, 300); o += 4;
	dns_put16(out + o, 4); o += 2;
	dns_put32(out + o, a); o += 4;
	return o;
}

static void t_onlan(void)
{
	uint8_t       v[600];
	struct fake   f;
	struct dns_io io;
	struct dnsfwd d;
	size_t        n;

	g_case = "lan/pure";
	CK(dns_on_lan(IP(10,1,1,50), IP(10,1,1,1), 0xFFFFFF00u) == 1, "in subnet");
	CK(dns_on_lan(IP(10,1,2,50), IP(10,1,1,1), 0xFFFFFF00u) == 0, "other /24");
	CK(dns_on_lan(IP(10,1,1,0),  IP(10,1,1,1), 0xFFFFFF00u) == 0, "network");
	CK(dns_on_lan(IP(10,1,1,255),IP(10,1,1,1), 0xFFFFFF00u) == 0, "broadcast");
	CK(dns_on_lan(0,             IP(10,1,1,1), 0xFFFFFF00u) == 0, "0.0.0.0");
	CK(dns_on_lan(IP(8,8,8,8),   IP(10,1,1,1), 0xFFFFFF00u) == 0, "off-LAN");
	CK(dns_on_lan(IP(10,1,1,1),  IP(10,1,1,1), 0xFFFFFF00u) == 1, "ourselves");

	n = hx(v, sizeof v, V_Q_A);

	g_case = "lan/off-source-dropped";
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(203,0,113,9), 33000);
	CK(f.n_sent == 0, "an off-LAN query produced %d datagram(s); an open "
	   "forwarder is an amplifier and must answer nothing", f.n_sent);
	CK(d.st.d_offlan == 1, "d_offlan %u", d.st.d_offlan);

	g_case = "lan/source-port-0-dropped";
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 0);
	CK(f.n_sent == 0, "a query from port 0 produced %d datagram(s)", f.n_sent);

	g_case = "lan/on-source-forwarded";       /* POSITIVE CONTROL */
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1, "n_sent %d", f.n_sent);
	CK(f.n_sent == 1 && f.sent[0].which == DNS_SOCK_UPSTREAM, "went upstream");
	CK(f.n_sent == 1 && f.sent[0].addr == IP(10,1,1,2) && f.sent[0].port == 53,
	   "upstream addr/port");
	CK(f.n_sent == 1 && dns_get16(f.sent[0].buf) != 0x1234,
	   "the outbound ID is fresh, not the client's");
	CK(d.st.q_fwd == 1, "q_fwd %u", d.st.q_fwd);
}

static void t_refusals(void)
{
	uint8_t       v[600];
	struct fake   f;
	struct dns_io io;
	struct dnsfwd d;
	size_t        n;

	/* RD = 0: an iterative query.  dnsfwd forwards, it does not iterate. */
	g_case = "refuse/rd0";
	n = hx(v, sizeof v, "1234 0000 0001 0000 0000 0000 " QNAME " 0001 0001");
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1 && f.sent[0].which == DNS_SOCK_CLIENT, "answered client");
	CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
	   == DNS_RCODE_REFUSED, "REFUSED");
	CK(d.st.q_fwd == 0, "nothing was forwarded");

	/* An OPT record: no EDNS0 in R7, answered FORMERR. */
	g_case = "refuse/edns0";
	n = hx(v, sizeof v, "1234 0100 0001 0000 0000 0001 " QNAME " 0001 0001 "
	                    "00 0029 1000 00000000 0000");
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
	   == DNS_RCODE_FORMERR, "FORMERR for EDNS0");

	/* QDCOUNT != 1. */
	g_case = "refuse/qdcount2";
	n = hx(v, sizeof v, "1234 0100 0002 0000 0000 0000 " QNAME " 0001 0001");
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
	   == DNS_RCODE_FORMERR, "FORMERR");
	CK(f.n_sent == 1 && dns_get16(f.sent[0].buf + 4) == 0,
	   "a header-level refusal echoes no question");

	/* A non-QUERY opcode. */
	g_case = "refuse/opcode";
	n = hx(v, sizeof v, "1234 0900 0001 0000 0000 0000 " QNAME " 0001 0001");
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
	   == DNS_RCODE_NOTIMP, "NOTIMP");

	/* A class we do not serve. */
	g_case = "refuse/class-CH";
	n = hx(v, sizeof v, "1234 0100 0001 0000 0000 0000 " QNAME " 0001 0003");
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
	   == DNS_RCODE_NOTIMP, "NOTIMP for class CHAOS");

	/* A response arriving on :53 gets no answer at all: replying would be a
	 * reflection between two DNS servers. */
	g_case = "refuse/response-on-53";
	n = hx(v, sizeof v, V_R_A);
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	CK(f.n_sent == 0, "a response on :53 produced %d datagram(s)", f.n_sent);

	/* Over 512 bytes. */
	g_case = "refuse/over512";
	{
		uint8_t big[600];
		struct dns_query q;

		memset(big, 0, sizeof big);
		CK(dns_parse_query(big, 513, &q) == -DNSE_LONG, "513 bytes");
	}
}

static void t_antispoof(void)
{
	uint8_t          v[600], rep[DNS_MSG_MAX];
	struct fake      f;
	struct dns_io    io;
	struct dnsfwd    d;
	struct dns_query q;
	size_t           n, rn;
	uint16_t         uid;

	n = hx(v, sizeof v, V_Q_A);
	CK(dns_parse_query(v, n, &q) == 0, "vector parses");

	/* Right ID, wrong SOURCE ADDRESS. */
	g_case = "spoof/wrong-src-addr";
	fake_init(&f, &io, &d);
	(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	uid = dns_get16(f.sent[0].buf);
	rn  = mk_reply(rep, uid, &q.q, IP(6,6,6,6));
	f.n_sent = 0;
	(void)dnsfwd_on_upstream(&d, rep, rn, IP(203,0,113,9), 53);
	CK(f.n_sent == 0, "relayed %d datagram(s) from the wrong address",
	   f.n_sent);
	CK(d.st.d_spoof == 1, "d_spoof %u", d.st.d_spoof);

	/* Right ID, right address, wrong SOURCE PORT. */
	g_case = "spoof/wrong-src-port";
	f.n_sent = 0;
	(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 5353);
	CK(f.n_sent == 0, "relayed %d from the wrong port", f.n_sent);

	/* Right ID, right address and port, DIFFERENT QUESTION.  This is the case
	 * that -DDNSFWD_MUT_NO_QMATCH must turn red. */
	g_case = "spoof/different-question";
	{
		struct dns_question other = q.q;

		other.name[1] = 'X';               /* Xww.example.com */
		rn = mk_reply(rep, uid, &other, IP(6,6,6,6));
		f.n_sent = 0;
		(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
		CK(f.n_sent == 0, "relayed %d datagram(s) for a question we never "
		   "asked -- the Kaminsky question check is not working", f.n_sent);
	}

	/* Right ID, right address and port, WRONG QTYPE. */
	g_case = "spoof/different-qtype";
	{
		struct dns_question other = q.q;

		other.qtype = DNS_TYPE_AAAA;
		rn = mk_reply(rep, uid, &other, IP(6,6,6,6));
		f.n_sent = 0;
		(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
		CK(f.n_sent == 0, "relayed %d for the wrong qtype", f.n_sent);
	}

	/* WRONG ID, everything else right. */
	g_case = "spoof/wrong-id";
	rn = mk_reply(rep, (uint16_t)(uid ^ 0x5A5A), &q.q, IP(6,6,6,6));
	f.n_sent = 0;
	(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
	CK(f.n_sent == 0, "relayed %d with the wrong ID", f.n_sent);

	/* POSITIVE CONTROL: everything matches. */
	g_case = "spoof/positive-control";
	rn = mk_reply(rep, uid, &q.q, IP(93,184,216,34));
	f.n_sent = 0;
	(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
	CK(f.n_sent == 1, "the matching reply was relayed %d time(s)", f.n_sent);
	CK(f.n_sent == 1 && f.sent[0].which == DNS_SOCK_CLIENT, "to the client");
	CK(f.n_sent == 1 && f.sent[0].addr == IP(10,1,1,50) &&
	   f.sent[0].port == 33000, "to the right client address and port");
	CK(f.n_sent == 1 && dns_get16(f.sent[0].buf) == 0x1234,
	   "the client's own ID was restored (%04X)",
	   f.n_sent == 1 ? dns_get16(f.sent[0].buf) : 0);
	CK(f.n_sent == 1 && f.sent[0].n == rn &&
	   memcmp(f.sent[0].buf + 2, rep + 2, rn - 2) == 0,
	   "every byte but the ID relayed unchanged");
	/* The entry is gone, so a second copy of the same reply is not relayed
	 * twice (a birthday-attack amplifier if it were). */
	f.n_sent = 0;
	(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
	CK(f.n_sent == 0, "the same reply was accepted twice");
}

static void t_table(void)
{
	uint8_t       v[600];
	struct fake   f;
	struct dns_io io;
	struct dnsfwd d;
	int           i;

	g_case = "table/exhaustion";
	fake_init(&f, &io, &d);
	/* 64 distinct questions.  The clock advances 100 ms per query so that the
	 * 20 q/s bucket, not the table, is never what refuses. */
	for (i = 0; i < DNS_INFLIGHT_MAX; i++) {
		size_t n = hx(v, sizeof v,
		              "1234 0100 0001 0000 0000 0000 " QNAME " 0001 0001");
		v[13] = (uint8_t)('a' + (i % 26));
		v[14] = (uint8_t)('a' + (i / 26));
		f.now += 100;
		(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
	}
	CK(f.n_sent == DNS_INFLIGHT_MAX, "forwarded %d of %d", f.n_sent,
	   DNS_INFLIGHT_MAX);
	CK(d.tbl.n_used == DNS_INFLIGHT_MAX, "n_used %u", d.tbl.n_used);
	{
		size_t n = hx(v, sizeof v,
		              "1234 0100 0001 0000 0000 0000 " QNAME " 0001 0001");
		v[13] = 'z'; v[14] = 'z';
		f.now += 100;
		f.n_sent = 0;
		(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
		CK(f.n_sent == 0, "a full table sent %d datagram(s); it must drop the "
		   "new query, not grow and not answer", f.n_sent);
		CK(d.st.d_full == 1, "d_full %u", d.st.d_full);
		CK(d.tbl.n_used == DNS_INFLIGHT_MAX, "the table grew to %u",
		   d.tbl.n_used);
	}

	g_case = "table/timeout";
	f.n_sent = 0;
	f.now += DNS_TIMEOUT_MS - 1;      /* the newest entry is not yet due */
	{
		int k = dnsfwd_tick(&d);

		CK(k > 0, "nothing expired after %d ms", DNS_TIMEOUT_MS);
		f.now += DNS_TIMEOUT_MS;
		k += dnsfwd_tick(&d);
		CK(k == DNS_INFLIGHT_MAX, "expired %d of %d", k, DNS_INFLIGHT_MAX);
		CK(d.tbl.n_used == 0, "n_used %u after expiry", d.tbl.n_used);
		CK(f.n_sent == DNS_INFLIGHT_MAX, "sent %d SERVFAILs", f.n_sent);
		CK(f.n_sent > 0 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
		   == DNS_RCODE_SERVFAIL, "the timeout answer is SERVFAIL");
		CK(f.n_sent > 0 && dns_get16(f.sent[0].buf) == 0x1234,
		   "the SERVFAIL carries the client's ID");
	}

	/* A reply for an entry that already timed out must not be relayed. */
	g_case = "table/late-reply";
	{
		struct dns_query q;
		uint8_t          rep[DNS_MSG_MAX];
		size_t           n, rn;

		n = hx(v, sizeof v, V_Q_A);
		(void)dns_parse_query(v, n, &q);
		fake_init(&f, &io, &d);
		(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
		rn = mk_reply(rep, dns_get16(f.sent[0].buf), &q.q, IP(1,2,3,4));
		f.now += DNS_TIMEOUT_MS;
		(void)dnsfwd_tick(&d);
		f.n_sent = 0;
		(void)dnsfwd_on_upstream(&d, rep, rn, IP(10,1,1,2), 53);
		CK(f.n_sent == 0, "a reply after the timeout was relayed %d time(s)",
		   f.n_sent);
	}

	/* The random source failing is not a reason to guess an ID. */
	g_case = "table/no-entropy";
	{
		size_t n = hx(v, sizeof v, V_Q_A);

		fake_init(&f, &io, &d);
		f.rand_fail = 1;
		(void)dnsfwd_on_client(&d, v, n, IP(10,1,1,50), 33000);
		CK(d.st.q_fwd == 0, "forwarded with no random ID");
		CK(f.n_sent == 1 && (dns_get16(f.sent[0].buf + 2) & DNS_F_RCMASK)
		   == DNS_RCODE_SERVFAIL, "SERVFAIL when /dev/urandom fails");
	}
}

static void t_rate(void)
{
	struct dns_rate r;
	int             i, allowed = 0;

	g_case = "rate/burst";
	dns_rate_init(&r);
	for (i = 0; i < 100; i++)
		if (dns_rate_allow(&r, IP(10,1,1,50), 5000)) allowed++;
	CK(allowed == DNS_RATE_CAP_M / DNS_RATE_COST_M,
	   "burst allowed %d, cap is %d", allowed,
	   DNS_RATE_CAP_M / DNS_RATE_COST_M);

	g_case = "rate/refill";
	allowed = 0;
	for (i = 0; i < 100; i++)
		if (dns_rate_allow(&r, IP(10,1,1,50), 6000)) allowed++;
	CK(allowed == 20, "one second refilled %d, expected 20", allowed);

	g_case = "rate/per-address";
	CK(dns_rate_allow(&r, IP(10,1,1,51), 6000) == 1,
	   "a second address was refused by the first address's bucket");

	g_case = "rate/positive-control";
	dns_rate_init(&r);
	CK(dns_rate_allow(&r, IP(10,1,1,50), 0) == 1, "a fresh bucket refused");
}

/* ------------------------------------------------------------------------ */
/* main                                                                     */
/* ------------------------------------------------------------------------ */

int main(void)
{
	struct sweep_counts sc;
	unsigned            pcases = 0, prefused = 0;

	(void)signal(SIGALRM, on_alarm);
	memset(&sc, 0, sizeof sc);

	t_endian();
	t_known();
	t_ptr_battery(&pcases, &prefused);
	sweep_one("sweep/query-A",  V_Q_A,  &sc);
	sweep_one("sweep/reply-A",  V_R_A,  &sc);
	sweep_one("sweep/reply-NX", V_R_NX, &sc);
	sweep_one("sweep/reply-CN", V_R_CN, &sc);
	t_onlan();
	t_refusals();
	t_antispoof();
	t_table();
	t_rate();

	(void)printf("pointer battery   %u cases, %u refusals\n",
	             pcases, prefused);
	(void)printf("truncation sweep  %u cases: %u refused, %u accepted\n",
	             sc.trunc_cases, sc.trunc_refused, sc.trunc_accepted);
	(void)printf("corruption sweep  %u cases: %u refused, %u accepted\n",
	             sc.corr_cases, sc.corr_refused, sc.corr_accepted);
	(void)printf("%u checks, %u failures\n", g_checks, g_fail);
	return g_fail == 0 ? 0 : 1;
}
