/* sha256.c -- SHA-256 and HMAC-SHA-256, written from FIPS 180-2 / RFC 6234
 * section 6.2 and RFC 2104.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES
 * ---------------------------------------------------------------------------
 *
 * One 64-byte compression function, a streaming context around it, and the
 * two-pass HMAC construction of RFC 2104 (K' = K padded or hashed to 64
 * bytes; H((K' ^ 0x5c..) || H((K' ^ 0x36..) || text))).  The HMAC context
 * holds the two inner/outer states *after* the pads have been absorbed, so a
 * caller that needs many MACs under one key -- PBKDF2 does, 160,000 of them
 * for the c=80000 vector -- copies the struct instead of re-keying.  That is
 * the only reason `struct hmac_sha256_ctx` is shaped the way CONTRACT.md
 * pins it.
 *
 * ---------------------------------------------------------------------------
 * THE ENDIANNESS RULE, AND WHY IT IS NOT DECORATION
 * ---------------------------------------------------------------------------
 *
 * SHA-256 is big-endian internally, so on this target a word load would
 * happen to work.  It is still done with shifts, everywhere, because the
 * host that runs `test_kdf` is little-endian and the same object file has to
 * produce the same digest on both.  A `memcpy` into a `uint32_t` array would
 * pass on one machine and fail on the other; worse, MIPS-I raises an address
 * error on an unaligned `lw`, and `sha256_update` is handed arbitrary
 * pointers (the middle of a scrypt block, for one).  `be32dec` reads four
 * separate bytes, so alignment never comes up.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES NOT ESTABLISH
 * ---------------------------------------------------------------------------
 *
 * The RFC vectors in `src/httpd/test_kdf.c` establish that this file
 * computes SHA-256 and HMAC-SHA-256 for those inputs on the two hosts and
 * under qemu-mips.  They do not establish: behaviour past 2^61 bytes of
 * input (`nbits` would wrap and no test reaches it), constant-time
 * execution, or that the `memset` of a context on `sha256_final` actually
 * clears DRAM -- a compiler may delete a store whose value is never read.
 */
#include "sha256.h"
#include <string.h>

#define ROTR32(x, n) ((uint32_t)(((uint32_t)(x) >> (n)) | ((uint32_t)(x) << (32 - (n)))))
#define SHR32(x, n)  ((uint32_t)((uint32_t)(x) >> (n)))

/* RFC 6234 section 5.1: the six logical functions. */
#define CH(x, y, z)  (((x) & (y)) ^ ((uint32_t)~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define BSIG0(x) (ROTR32(x,  2) ^ ROTR32(x, 13) ^ ROTR32(x, 22))
#define BSIG1(x) (ROTR32(x,  6) ^ ROTR32(x, 11) ^ ROTR32(x, 25))
#define SSIG0(x) (ROTR32(x,  7) ^ ROTR32(x, 18) ^ SHR32(x,  3))
#define SSIG1(x) (ROTR32(x, 17) ^ ROTR32(x, 19) ^ SHR32(x, 10))

/* RFC 6234 section 5.1: the first 32 bits of the fractional parts of the cube
 * roots of the first 64 primes. */
static const uint32_t K256[64] = {
	0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u,
	0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
	0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
	0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
	0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
	0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
	0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
	0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
	0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
	0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
	0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u,
	0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
	0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u,
	0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
	0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
	0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u
};

/* RFC 6234 section 6.1: the fractional parts of the square roots of the first
 * eight primes. */
static const uint32_t H256_0[8] = {
	0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
	0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u
};

static uint32_t be32dec(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
	     | ((uint32_t)p[2] <<  8) |  (uint32_t)p[3];
}

static void be32enc(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)((v >> 24) & 0xffu);
	p[1] = (uint8_t)((v >> 16) & 0xffu);
	p[2] = (uint8_t)((v >>  8) & 0xffu);
	p[3] = (uint8_t)( v        & 0xffu);
}

static void be64enc(uint8_t *p, uint64_t v)
{
	be32enc(p,     (uint32_t)((v >> 32) & 0xffffffffu));
	be32enc(p + 4, (uint32_t)( v        & 0xffffffffu));
}

/* One compression, RFC 6234 section 6.2.  `blk` may be unaligned. */
static void sha256_block(uint32_t h[8], const uint8_t *blk)
{
	uint32_t w[64];
	uint32_t a, b, c, d, e, f, g, hh, t1, t2;
	int t;

	for (t = 0; t < 16; t++)
		w[t] = be32dec(blk + 4 * t);
	for (t = 16; t < 64; t++)
		w[t] = SSIG1(w[t - 2]) + w[t - 7] + SSIG0(w[t - 15]) + w[t - 16];

	a = h[0]; b = h[1]; c = h[2]; d = h[3];
	e = h[4]; f = h[5]; g = h[6]; hh = h[7];

	for (t = 0; t < 64; t++) {
		t1 = hh + BSIG1(e) + CH(e, f, g) + K256[t] + w[t];
		t2 = BSIG0(a) + MAJ(a, b, c);
		hh = g; g = f; f = e;
		e = d + t1;
		d = c; c = b; b = a;
		a = t1 + t2;
	}

	h[0] += a; h[1] += b; h[2] += c; h[3] += d;
	h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
}

void sha256_init(struct sha256_ctx *c)
{
	int i;

	if (c == NULL)
		return;
	for (i = 0; i < 8; i++)
		c->h[i] = H256_0[i];
	c->nbits = 0;
	c->buflen = 0;
	memset(c->buf, 0, sizeof c->buf);
}

void sha256_update(struct sha256_ctx *c, const void *p, size_t n)
{
	const uint8_t *in = (const uint8_t *)p;
	size_t take;

	if (c == NULL || n == 0)
		return;
	if (in == NULL)
		return;
	c->nbits += (uint64_t)n * 8u;

	if (c->buflen != 0) {
		take = (size_t)SHA256_BLOCK_LEN - c->buflen;
		if (take > n)
			take = n;
		memcpy(c->buf + c->buflen, in, take);
		c->buflen += take;
		in += take;
		n -= take;
		if (c->buflen == (size_t)SHA256_BLOCK_LEN) {
			sha256_block(c->h, c->buf);
			c->buflen = 0;
		}
	}
	while (n >= (size_t)SHA256_BLOCK_LEN) {
		sha256_block(c->h, in);
		in += SHA256_BLOCK_LEN;
		n -= (size_t)SHA256_BLOCK_LEN;
	}
	if (n != 0) {
		memcpy(c->buf, in, n);
		c->buflen = n;
	}
}

/* The context is wiped: call sha256_init to reuse it.  A second
 * sha256_final on the same context returns the digest of the empty string,
 * not the previous digest. */
void sha256_final(struct sha256_ctx *c, uint8_t out[SHA256_DIGEST_LEN])
{
	uint8_t pad[SHA256_BLOCK_LEN];
	uint64_t nbits;
	size_t padlen;
	int i;

	if (c == NULL || out == NULL)
		return;
	nbits = c->nbits;                       /* the updates below change it */
	memset(pad, 0, sizeof pad);
	pad[0] = 0x80u;
	/* 0x80 then zeros until the buffer is 56 mod 64; the widest case is
	 * buflen == 56, which needs 64 bytes, exactly sizeof pad. */
	padlen = (c->buflen < 56u) ? (56u - c->buflen) : (120u - c->buflen);
	sha256_update(c, pad, padlen);
	be64enc(pad, nbits);
	sha256_update(c, pad, 8);

	for (i = 0; i < 8; i++)
		be32enc(out + 4 * i, c->h[i]);
	memset(c, 0, sizeof *c);
	memset(pad, 0, sizeof pad);
}

int sha256(const void *p, size_t n, uint8_t out[SHA256_DIGEST_LEN])
{
	struct sha256_ctx c;

	if (out == NULL)
		return -1;
	if (p == NULL && n != 0)
		return -1;
	sha256_init(&c);
	sha256_update(&c, p, n);
	sha256_final(&c, out);
	return 0;
}

/* --------------------------------------------------------------------------
 * HMAC-SHA-256, RFC 2104
 * -------------------------------------------------------------------------- */

void hmac_sha256_init(struct hmac_sha256_ctx *c, const uint8_t *key, size_t klen)
{
	uint8_t k[SHA256_BLOCK_LEN];
	uint8_t kh[SHA256_DIGEST_LEN];
	uint8_t pad[SHA256_BLOCK_LEN];
	size_t i;

	if (c == NULL)
		return;
	if (key == NULL && klen != 0)
		klen = 0;                       /* fail closed: MAC under a zero key */

	memset(k, 0, sizeof k);
	if (klen > (size_t)SHA256_BLOCK_LEN) {
		(void)sha256(key, klen, kh);
		memcpy(k, kh, SHA256_DIGEST_LEN);
		memset(kh, 0, sizeof kh);
	} else if (klen != 0) {
		memcpy(k, key, klen);
	}

	for (i = 0; i < (size_t)SHA256_BLOCK_LEN; i++)
		pad[i] = (uint8_t)(k[i] ^ 0x36u);
	sha256_init(&c->inner);
	sha256_update(&c->inner, pad, SHA256_BLOCK_LEN);

	for (i = 0; i < (size_t)SHA256_BLOCK_LEN; i++)
		pad[i] = (uint8_t)(k[i] ^ 0x5cu);
	sha256_init(&c->outer);
	sha256_update(&c->outer, pad, SHA256_BLOCK_LEN);

	memset(k, 0, sizeof k);
	memset(pad, 0, sizeof pad);
}

void hmac_sha256_update(struct hmac_sha256_ctx *c, const void *p, size_t n)
{
	if (c == NULL)
		return;
	sha256_update(&c->inner, p, n);
}

void hmac_sha256_final(struct hmac_sha256_ctx *c, uint8_t out[SHA256_DIGEST_LEN])
{
	uint8_t d[SHA256_DIGEST_LEN];

	if (c == NULL || out == NULL)
		return;
	sha256_final(&c->inner, d);
	sha256_update(&c->outer, d, SHA256_DIGEST_LEN);
	sha256_final(&c->outer, out);
	memset(d, 0, sizeof d);
}

int hmac_sha256(const uint8_t *key, size_t klen, const void *p, size_t n,
                uint8_t out[SHA256_DIGEST_LEN])
{
	struct hmac_sha256_ctx c;

	if (out == NULL)
		return -1;
	if (key == NULL && klen != 0)
		return -1;
	if (p == NULL && n != 0)
		return -1;
	hmac_sha256_init(&c, key, klen);
	hmac_sha256_update(&c, p, n);
	hmac_sha256_final(&c, out);
	memset(&c, 0, sizeof c);
	return 0;
}
