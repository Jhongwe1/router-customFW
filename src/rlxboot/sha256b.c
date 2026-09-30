/* src/rlxboot/sha256b.c -- SHA-256, FIPS 180-4.  rlxfw's own code.
 *
 * Written rather than imported, and the reason is the opposite of the reason
 * `src/lib/ed25519.c` is imported.  A hash has no rare-input failure mode of
 * the kind field arithmetic has: every word of the state is a fixed function of
 * the message words, the RFC 6234 vector set exercises the full round schedule,
 * and the only thing the vectors do not cover exhaustively is the length
 * padding -- which is enumerable, so the host test drives every message length
 * 0..200 against a second source.  Ed25519's carry propagation is not
 * enumerable, which is why that one is an import.
 *
 * Constraints: no libc, no malloc, no recursion, `unsigned long` is 32 bits on
 * this target and every intermediate is masked to 32 bits so the same source is
 * correct on a host where it is 64.
 */

#include "sha256b.h"

#define M32(x) ((x) & 0xFFFFFFFFUL)
#define ROR(x,n) (M32(((x) >> (n)) | ((x) << (32 - (n)))))

static const unsigned long K[64] = {
	0x428a2f98UL,0x71374491UL,0xb5c0fbcfUL,0xe9b5dba5UL,
	0x3956c25bUL,0x59f111f1UL,0x923f82a4UL,0xab1c5ed5UL,
	0xd807aa98UL,0x12835b01UL,0x243185beUL,0x550c7dc3UL,
	0x72be5d74UL,0x80deb1feUL,0x9bdc06a7UL,0xc19bf174UL,
	0xe49b69c1UL,0xefbe4786UL,0x0fc19dc6UL,0x240ca1ccUL,
	0x2de92c6fUL,0x4a7484aaUL,0x5cb0a9dcUL,0x76f988daUL,
	0x983e5152UL,0xa831c66dUL,0xb00327c8UL,0xbf597fc7UL,
	0xc6e00bf3UL,0xd5a79147UL,0x06ca6351UL,0x14292967UL,
	0x27b70a85UL,0x2e1b2138UL,0x4d2c6dfcUL,0x53380d13UL,
	0x650a7354UL,0x766a0abbUL,0x81c2c92eUL,0x92722c85UL,
	0xa2bfe8a1UL,0xa81a664bUL,0xc24b8b70UL,0xc76c51a3UL,
	0xd192e819UL,0xd6990624UL,0xf40e3585UL,0x106aa070UL,
	0x19a4c116UL,0x1e376c08UL,0x2748774cUL,0x34b0bcb5UL,
	0x391c0cb3UL,0x4ed8aa4aUL,0x5b9cca4fUL,0x682e6ff3UL,
	0x748f82eeUL,0x78a5636fUL,0x84c87814UL,0x8cc70208UL,
	0x90befffaUL,0xa4506cebUL,0xbef9a3f7UL,0xc67178f2UL
};

static void block(struct sha256b *c, const unsigned char *p)
{
	unsigned long w[64], a, b, cc, d, e, f, g, h, t1, t2;
	int i;

	for (i = 0; i < 16; i++)
		w[i] = ((unsigned long)p[4*i] << 24) | ((unsigned long)p[4*i+1] << 16)
		     | ((unsigned long)p[4*i+2] << 8) | (unsigned long)p[4*i+3];
	for (i = 16; i < 64; i++) {
		unsigned long s0 = ROR(w[i-15],7) ^ ROR(w[i-15],18) ^ M32(w[i-15] >> 3);
		unsigned long s1 = ROR(w[i-2],17) ^ ROR(w[i-2],19) ^ M32(w[i-2] >> 10);
		w[i] = M32(w[i-16] + s0 + w[i-7] + s1);
	}

	a = c->h[0]; b = c->h[1]; cc = c->h[2]; d = c->h[3];
	e = c->h[4]; f = c->h[5]; g = c->h[6]; h = c->h[7];

	for (i = 0; i < 64; i++) {
		t1 = M32(h + (ROR(e,6) ^ ROR(e,11) ^ ROR(e,25))
		           + ((e & f) ^ (~e & g)) + K[i] + w[i]);
		t2 = M32((ROR(a,2) ^ ROR(a,13) ^ ROR(a,22))
		           + ((a & b) ^ (a & cc) ^ (b & cc)));
		h = g; g = f; f = e; e = M32(d + t1);
		d = cc; cc = b; b = a; a = M32(t1 + t2);
	}

	c->h[0] = M32(c->h[0] + a); c->h[1] = M32(c->h[1] + b);
	c->h[2] = M32(c->h[2] + cc); c->h[3] = M32(c->h[3] + d);
	c->h[4] = M32(c->h[4] + e); c->h[5] = M32(c->h[5] + f);
	c->h[6] = M32(c->h[6] + g); c->h[7] = M32(c->h[7] + h);
}

void sha256b_init(struct sha256b *c)
{
	c->h[0] = 0x6a09e667UL; c->h[1] = 0xbb67ae85UL;
	c->h[2] = 0x3c6ef372UL; c->h[3] = 0xa54ff53aUL;
	c->h[4] = 0x510e527fUL; c->h[5] = 0x9b05688cUL;
	c->h[6] = 0x1f83d9abUL; c->h[7] = 0x5be0cd19UL;
	c->nbits_hi = 0;
	c->nbits_lo = 0;
	c->buflen = 0;
}

/* The bit counter is two 32-bit halves and not one 64-bit value, because
 * `long long` on the target means a libgcc call for every add.  3 MiB is
 * 25,165,824 bits, so the high half is only ever exercised by a test -- and it
 * IS exercised: the host suite feeds 2^29 + 8 bytes through `update` in chunks
 * and checks the carry, because a length accumulator that never carries in
 * production is one nothing has ever shown to carry at all. */
static void addbits(struct sha256b *c, unsigned long nbytes)
{
	unsigned long lo = M32(nbytes << 3);
	unsigned long hi = M32(nbytes >> 29);
	unsigned long old = c->nbits_lo;

	c->nbits_lo = M32(old + lo);
	if (c->nbits_lo < old)
		c->nbits_hi = M32(c->nbits_hi + 1);
	c->nbits_hi = M32(c->nbits_hi + hi);
}

void sha256b_update(struct sha256b *c, const unsigned char *p, unsigned long n)
{
	unsigned long i;

	addbits(c, n);

	if (c->buflen) {
		while (n && c->buflen < SHA256B_BLOCK) {
			c->buf[c->buflen++] = *p++;
			n--;
		}
		if (c->buflen < SHA256B_BLOCK)
			return;
		block(c, c->buf);
		c->buflen = 0;
	}
	while (n >= SHA256B_BLOCK) {
		block(c, p);
		p += SHA256B_BLOCK;
		n -= SHA256B_BLOCK;
	}
	for (i = 0; i < n; i++)
		c->buf[c->buflen++] = p[i];
}

void sha256b_final(struct sha256b *c, unsigned char out[SHA256B_DIGEST])
{
	unsigned char pad[SHA256B_BLOCK * 2];
	unsigned long hi = c->nbits_hi, lo = c->nbits_lo;
	unsigned long i, len = c->buflen, total;

	for (i = 0; i < len; i++)
		pad[i] = c->buf[i];
	pad[len++] = 0x80;
	total = (len <= 56) ? 64 : 128;
	while (len < total - 8)
		pad[len++] = 0;
	pad[len++] = (unsigned char)((hi >> 24) & 0xff);
	pad[len++] = (unsigned char)((hi >> 16) & 0xff);
	pad[len++] = (unsigned char)((hi >> 8) & 0xff);
	pad[len++] = (unsigned char)(hi & 0xff);
	pad[len++] = (unsigned char)((lo >> 24) & 0xff);
	pad[len++] = (unsigned char)((lo >> 16) & 0xff);
	pad[len++] = (unsigned char)((lo >> 8) & 0xff);
	pad[len++] = (unsigned char)(lo & 0xff);

	block(c, pad);
	if (total == 128)
		block(c, pad + SHA256B_BLOCK);

	for (i = 0; i < 8; i++) {
		out[4*i]   = (unsigned char)((c->h[i] >> 24) & 0xff);
		out[4*i+1] = (unsigned char)((c->h[i] >> 16) & 0xff);
		out[4*i+2] = (unsigned char)((c->h[i] >> 8) & 0xff);
		out[4*i+3] = (unsigned char)(c->h[i] & 0xff);
	}
}

void sha256b(unsigned char out[SHA256B_DIGEST], const unsigned char *p, unsigned long n)
{
	struct sha256b c;

	sha256b_init(&c);
	sha256b_update(&c, p, n);
	sha256b_final(&c, out);
}
