/* kdf.c -- PBKDF2-HMAC-SHA-256 (RFC 8018 section 5.2), scrypt with Salsa20/8,
 * BlockMix and ROMix (RFC 7914 sections 3-6), the 56-byte `admin.pwhash` blob
 * (SPEC-R7 section 4.2), and the entropy gate in front of the salt.
 *
 * Written from the RFC text.  No third-party code.
 *
 * ---------------------------------------------------------------------------
 * THE ENDIANNESS TRAP, WHICH IS THE POINT OF THE QEMU RUN
 * ---------------------------------------------------------------------------
 *
 * SHA-256 and PBKDF2's block counter are big-endian; the target is big-endian
 * too, so on this CPU a careless word access in that half of the code happens
 * to give the right answer.  Salsa20 is the opposite: its 16 state words are
 * **little-endian** in the 64-byte block, on every machine.  So the one place
 * a cast or a `memcpy` of a `uint32_t` array would be silently wrong is
 * exactly the place where the host test and the target run disagree: the
 * little-endian host would pass every RFC 7914 vector and the big-endian
 * device would compute a different password hash from the same password.
 *
 * Therefore: `le32dec` and `le32enc` read and write four separate bytes with
 * shifts, they are the only route between `uint8_t` blocks and `uint32_t`
 * state, and `src/httpd/test_kdf.c` is run under `qemu-mips-static` as well
 * as on the host.  A host-only green is not evidence for this file.
 *
 * ---------------------------------------------------------------------------
 * MEMORY
 * ---------------------------------------------------------------------------
 *
 * One `malloc` per `kdf_scrypt_raw` call, of exactly
 * `N*128*r + 2*128*r + p*128*r` bytes (V, the X/Y ping-pong pair, B), which is
 * what `kdf_scrypt_peak` returns.  ROMix is written with two block buffers and
 * not three: `X ^= V[j]` happens in place, after `Integerify(X)` has already
 * been read, and then BlockMix writes into the other buffer and the pointers
 * swap.  No VLA, no recursion, no `alloca`.
 *
 * `kdf_scrypt` refuses any parameter set whose peak exceeds `KDF_PEAK_CAP`
 * before allocating anything, because it is reachable from an unauthenticated
 * HTTP request.  `kdf_scrypt_raw` does not apply that cap -- the RFC 7914
 * vectors need 16 MB and 1 GiB -- so a new caller of the raw function is
 * asserting it controls the parameters.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS FILE DOES NOT ESTABLISH
 * ---------------------------------------------------------------------------
 *
 *  - Nothing here is a measurement of the device.  Timings taken under qemu
 *    are qemu's, and the cost of one evaluation on the RTL8196E is 推 until
 *    it is measured on the silicon.
 *  - `pwhash_verify` is constant-time only in its final comparison.  The
 *    scrypt evaluation itself takes password-dependent time (it walks V at a
 *    password-dependent index) and that is inherent to scrypt, not a defect
 *    here; it leaks to a local attacker with a cache, not to an HTTP client.
 *  - The `wipe`/`memset` of working state is hygiene.  A compiler may delete
 *    a store nothing reads; no test in this tree proves DRAM was cleared.
 *  - `kdf_entropy_avail` reads a number the kernel prints.  Whether that
 *    number means the pool is really unpredictable is the kernel's claim, not
 *    this file's, and on this SoC there is no hardware RNG behind it.
 */
#include "kdf.h"
#include "sha256.h"

#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define SCRYPT_BLOCK 64u                 /* one Salsa20 block, bytes */

/* Clear through a volatile pointer so the store is not obviously dead.  Used
 * for the small secrets; see the header on what this does not claim. */
static void wipe(void *p, size_t n)
{
	volatile uint8_t *q = (volatile uint8_t *)p;

	while (n != 0) {
		*q = 0;
		q++;
		n--;
	}
}

int ct_memeq(const void *a, const void *b, size_t n)
{
	const uint8_t *x = (const uint8_t *)a;
	const uint8_t *y = (const uint8_t *)b;
	uint8_t d = 0;
	size_t i;

	if (n == 0)
		return 1;
	if (x == NULL || y == NULL)
		return 0;
	for (i = 0; i < n; i++)
		d = (uint8_t)(d | (uint8_t)(x[i] ^ y[i]));
	/* d == 0  ->  1, else 0, with no branch on d */
	return (int)((((uint32_t)d - 1u) >> 8) & 1u);
}

/* --------------------------------------------------------------------------
 * PBKDF2-HMAC-SHA-256, RFC 8018 section 5.2
 * -------------------------------------------------------------------------- */

int kdf_pbkdf2_sha256(const uint8_t *pw, size_t pwlen,
                      const uint8_t *salt, size_t saltlen,
                      uint32_t iters, uint8_t *out, size_t outlen)
{
	struct hmac_sha256_ctx base, h;
	uint8_t u[SHA256_DIGEST_LEN], t[SHA256_DIGEST_LEN], ctr[4];
	size_t done, need, nblocks, k;
	uint32_t i, j;

	if (out == NULL || outlen == 0)
		return -KDFE_INVAL;
	if (iters == 0)
		return -KDFE_INVAL;
	if (pw == NULL && pwlen != 0)
		return -KDFE_INVAL;
	if (salt == NULL && saltlen != 0)
		return -KDFE_INVAL;
	/* l = ceil(dkLen / hLen) must fit the 4-byte INT(i) of the spec. */
	nblocks = outlen / SHA256_DIGEST_LEN;
	if (outlen % SHA256_DIGEST_LEN != 0)
		nblocks++;
	if (nblocks > 0xffffffffu)
		return -KDFE_INVAL;

	memset(&h, 0, sizeof h);
	hmac_sha256_init(&base, pw, pwlen);
	done = 0;
	for (i = 1; done < outlen; i++) {
		ctr[0] = (uint8_t)((i >> 24) & 0xffu);
		ctr[1] = (uint8_t)((i >> 16) & 0xffu);
		ctr[2] = (uint8_t)((i >>  8) & 0xffu);
		ctr[3] = (uint8_t)( i        & 0xffu);

		h = base;                        /* U_1 = PRF(P, S || INT(i)) */
		if (saltlen != 0)
			hmac_sha256_update(&h, salt, saltlen);
		hmac_sha256_update(&h, ctr, 4);
		hmac_sha256_final(&h, u);
		memcpy(t, u, SHA256_DIGEST_LEN);

		for (j = 1; j < iters; j++) {     /* U_j = PRF(P, U_{j-1}) */
			h = base;
			hmac_sha256_update(&h, u, SHA256_DIGEST_LEN);
			hmac_sha256_final(&h, u);
			for (k = 0; k < (size_t)SHA256_DIGEST_LEN; k++)
				t[k] = (uint8_t)(t[k] ^ u[k]);
		}

		need = outlen - done;
		if (need > (size_t)SHA256_DIGEST_LEN)
			need = (size_t)SHA256_DIGEST_LEN;
		memcpy(out + done, t, need);
		done += need;
	}

	wipe(&base, sizeof base);
	wipe(&h, sizeof h);
	wipe(u, sizeof u);
	wipe(t, sizeof t);
	return 0;
}

/* --------------------------------------------------------------------------
 * Salsa20/8 core, RFC 7914 section 3.  The block is little-endian.
 * -------------------------------------------------------------------------- */

static uint32_t le32dec(const uint8_t *p)
{
	return  (uint32_t)p[0]
	     | ((uint32_t)p[1] <<  8)
	     | ((uint32_t)p[2] << 16)
	     | ((uint32_t)p[3] << 24);
}

static void le32enc(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)( v        & 0xffu);
	p[1] = (uint8_t)((v >>  8) & 0xffu);
	p[2] = (uint8_t)((v >> 16) & 0xffu);
	p[3] = (uint8_t)((v >> 24) & 0xffu);
}

#define ROTL32(x, n) ((uint32_t)(((uint32_t)(x) << (n)) | ((uint32_t)(x) >> (32 - (n)))))

/* The Salsa20 quarterround, as the four assignments of the specification. */
#define QR(a, b, c, d) do {                      \
		(b) ^= ROTL32((uint32_t)((a) + (d)),  7); \
		(c) ^= ROTL32((uint32_t)((b) + (a)),  9); \
		(d) ^= ROTL32((uint32_t)((c) + (b)), 13); \
		(a) ^= ROTL32((uint32_t)((d) + (c)), 18); \
	} while (0)

/* In place on a 64-byte block: out = in + Salsa20/8(in), all word arithmetic
 * modulo 2^32, every word carried across the byte boundary by shifts. */
static void salsa20_8(uint8_t b[SCRYPT_BLOCK])
{
	uint32_t x[16], j[16];
	int i, round;

	for (i = 0; i < 16; i++) {
		j[i] = le32dec(b + 4 * i);
		x[i] = j[i];
	}
	for (round = 0; round < 4; round++) {     /* 8 rounds = 4 double rounds */
		/* columnround */
		QR(x[0],  x[4],  x[8],  x[12]);
		QR(x[5],  x[9],  x[13], x[1]);
		QR(x[10], x[14], x[2],  x[6]);
		QR(x[15], x[3],  x[7],  x[11]);
		/* rowround */
		QR(x[0],  x[1],  x[2],  x[3]);
		QR(x[5],  x[6],  x[7],  x[4]);
		QR(x[10], x[11], x[8],  x[9]);
		QR(x[15], x[12], x[13], x[14]);
	}
	for (i = 0; i < 16; i++)
		le32enc(b + 4 * i, (uint32_t)(x[i] + j[i]));
}

/* --------------------------------------------------------------------------
 * scryptBlockMix, RFC 7914 section 4.  `in` and `out` are 128*r bytes and
 * must not overlap.  The output shuffle
 *     B' = (Y[0], Y[2], ..., Y[2r-2], Y[1], Y[3], ..., Y[2r-1])
 * is done by writing each Y[i] straight to its final place, so no Y array is
 * allocated: even i goes to out[i/2], odd i to out[r + i/2].
 * -------------------------------------------------------------------------- */
static void blockmix(const uint8_t *in, uint8_t *out, uint32_t r)
{
	uint8_t x[SCRYPT_BLOCK];
	uint32_t i;
	size_t k, dst;

	memcpy(x, in + (size_t)(2u * r - 1u) * SCRYPT_BLOCK, SCRYPT_BLOCK);
	for (i = 0; i < 2u * r; i++) {
		const uint8_t *bi = in + (size_t)i * SCRYPT_BLOCK;
		for (k = 0; k < (size_t)SCRYPT_BLOCK; k++)
			x[k] = (uint8_t)(x[k] ^ bi[k]);
		salsa20_8(x);
		dst = ((i & 1u) == 0u) ? (size_t)(i / 2u)
		                       : (size_t)r + (size_t)(i / 2u);
		memcpy(out + dst * SCRYPT_BLOCK, x, SCRYPT_BLOCK);
	}
	wipe(x, sizeof x);
}

/* Integerify(X) mod N, RFC 7914 section 5: the last 64-byte block of X read as
 * a little-endian integer.  N is a power of two <= 2^31 here, so the low word
 * decides and the modulo is a mask.  The read is byte-wise on purpose. */
static uint32_t integerify_mod(const uint8_t *x, uint32_t r, uint32_t n)
{
	return le32dec(x + (size_t)(2u * r - 1u) * SCRYPT_BLOCK) & (n - 1u);
}

/* scryptROMix, RFC 7914 section 5, in place on `b` (128*r bytes).
 * `v` is N*128*r bytes, `xy` is 2*128*r bytes. */
static void romix(uint8_t *b, uint32_t n, uint32_t r, uint8_t *v, uint8_t *xy)
{
	size_t blk = (size_t)128u * r;
	uint8_t *p = xy;
	uint8_t *q = xy + blk;
	uint8_t *tmp;
	uint32_t i, j;
	size_t k;

	memcpy(p, b, blk);
	for (i = 0; i < n; i++) {                /* V[i] = X; X = BlockMix(X) */
		memcpy(v + (size_t)i * blk, p, blk);
		blockmix(p, q, r);
		tmp = p; p = q; q = tmp;
	}
	for (i = 0; i < n; i++) {                /* X = BlockMix(X xor V[j]) */
		j = integerify_mod(p, r, n);     /* read BEFORE the xor */
		{
			const uint8_t *vj = v + (size_t)j * blk;
			for (k = 0; k < blk; k++)
				p[k] = (uint8_t)(p[k] ^ vj[k]);
		}
		blockmix(p, q, r);
		tmp = p; p = q; q = tmp;
	}
	memcpy(b, p, blk);
}

/* --------------------------------------------------------------------------
 * scrypt, RFC 7914 section 6
 * -------------------------------------------------------------------------- */

/* The footprint of one evaluation, with every multiplication checked.  0 and a
 * non-zero return mean "these parameters cannot be represented here". */
static int peak_bytes(uint32_t n, uint32_t r, uint32_t p, size_t *out)
{
	size_t blk, v, xy, b, total;
	const size_t smax = (size_t)-1;

	if (n < 2u || r == 0u || p == 0u)
		return -1;
	if ((n & (n - 1u)) != 0u)               /* N must be a power of two */
		return -1;
	/* RFC 7914 section 6 bounds N < 2^(128 * r / 8) = 2^(16 * r).  With a
	 * 32-bit N only r = 1 can bind, and the shift for r >= 2 would itself be
	 * undefined, so the guard is written round that way and not as the
	 * arithmetic the RFC prints. */
	if (r < 2u && n >= ((uint32_t)1u << (16u * r)))
		return -1;
	if ((size_t)r > smax / 128u)
		return -1;
	blk = (size_t)128u * (size_t)r;
	if ((size_t)n > smax / blk)
		return -1;
	v = (size_t)n * blk;
	if (blk > smax / 2u)
		return -1;
	xy = 2u * blk;
	if ((size_t)p > smax / blk)
		return -1;
	b = (size_t)p * blk;
	if (v > smax - xy)
		return -1;
	total = v + xy;
	if (total > smax - b)
		return -1;
	total += b;
	*out = total;
	return 0;
}

size_t kdf_scrypt_peak(uint8_t log2n, uint16_t r, uint16_t p)
{
	size_t total = 0;
	uint32_t n;

	if (log2n < 1u || log2n > 31u)
		return 0;
	if (sizeof(size_t) * 8u <= (size_t)log2n)
		return 0;
	n = (uint32_t)1u << log2n;
	if (peak_bytes(n, (uint32_t)r, (uint32_t)p, &total) != 0)
		return 0;
	return total;
}

int kdf_scrypt_raw(const uint8_t *pw, size_t pwlen,
                   const uint8_t *salt, size_t saltlen,
                   uint32_t n, uint32_t r, uint32_t p,
                   uint8_t *out, size_t outlen)
{
	uint8_t *work;
	uint8_t *v;
	uint8_t *xy;
	uint8_t *b;
	size_t need = 0, blk, blen;
	uint32_t i;
	int rc;

	if (out == NULL || outlen == 0)
		return -KDFE_INVAL;
	if (pw == NULL && pwlen != 0)
		return -KDFE_INVAL;
	if (salt == NULL && saltlen != 0)
		return -KDFE_INVAL;
	if (r == 0u || p == 0u)
		return -KDFE_INVAL;
	if (n < 2u || (n & (n - 1u)) != 0u)
		return -KDFE_INVAL;
	/* RFC 7914 section 6: r * p < 2^30, and 2*r must not overflow below. */
	if ((uint64_t)r * (uint64_t)p >= ((uint64_t)1 << 30))
		return -KDFE_INVAL;
	if (peak_bytes(n, r, p, &need) != 0)
		return -KDFE_INVAL;

	work = (uint8_t *)malloc(need);
	if (work == NULL)
		return -KDFE_NOMEM;

	blk  = (size_t)128u * (size_t)r;
	blen = (size_t)p * blk;
	v    = work;
	xy   = work + (size_t)n * blk;
	b    = xy + 2u * blk;

	/* B = PBKDF2(P, S, 1, p * 128 * r) */
	rc = kdf_pbkdf2_sha256(pw, pwlen, salt, saltlen, 1u, b, blen);
	if (rc == 0) {
		for (i = 0; i < p; i++)
			romix(b + (size_t)i * blk, n, r, v, xy);
		/* DK = PBKDF2(P, B, 1, dkLen) */
		rc = kdf_pbkdf2_sha256(pw, pwlen, b, blen, 1u, out, outlen);
	}

	/* The small halves through wipe(); V with memset, because 4 MB of
	 * volatile byte stores is real time on a 200 MHz core and the pages go
	 * back to the kernel on free() anyway (uClibc mmaps a request this
	 * large).  Neither is a claim about what remains in DRAM. */
	wipe(xy, 2u * blk);
	wipe(b, blen);
	memset(v, 0, (size_t)n * blk);
	free(work);
	return rc;
}

int kdf_scrypt(const uint8_t *pw, size_t pwlen, const uint8_t salt[16],
               uint8_t log2n, uint16_t r, uint16_t p, uint8_t out[32])
{
	size_t peak;

	if (salt == NULL || out == NULL)
		return -KDFE_INVAL;
	peak = kdf_scrypt_peak(log2n, r, p);
	if (peak == 0 || peak > (size_t)KDF_PEAK_CAP)
		return -KDFE_INVAL;
	return kdf_scrypt_raw(pw, pwlen, salt, 16u,
	                      (uint32_t)1u << log2n, (uint32_t)r, (uint32_t)p,
	                      out, 32u);
}

/* --------------------------------------------------------------------------
 * The 56-byte admin.pwhash blob, SPEC-R7 section 4.2
 *
 *   [0]     alg = 1 (scrypt)
 *   [1]     log2 N
 *   [2..3]  r, big-endian
 *   [4..5]  p, big-endian
 *   [6..7]  0
 *   [8..23] salt
 *   [24..55] scrypt output, 32 bytes
 * -------------------------------------------------------------------------- */

int pwhash_params(const uint8_t blob[PWHASH_LEN], uint8_t *log2n, uint16_t *r, uint16_t *p)
{
	if (blob == NULL)
		return -KDFE_BADBLOB;
	if (blob[0] != 1u)
		return -KDFE_BADBLOB;
	if (blob[6] != 0u || blob[7] != 0u)
		return -KDFE_BADBLOB;
	if (log2n != NULL)
		*log2n = blob[1];
	if (r != NULL)
		*r = (uint16_t)(((uint16_t)blob[2] << 8) | (uint16_t)blob[3]);
	if (p != NULL)
		*p = (uint16_t)(((uint16_t)blob[4] << 8) | (uint16_t)blob[5]);
	return 0;
}

int pwhash_make(const uint8_t *pw, size_t pwlen, uint8_t log2n, uint16_t r, uint16_t p,
                const uint8_t salt[16], uint8_t out[PWHASH_LEN])
{
	uint8_t key[32];
	int rc;

	if (salt == NULL || out == NULL)
		return -KDFE_INVAL;
	rc = kdf_scrypt(pw, pwlen, salt, log2n, r, p, key);
	if (rc != 0) {
		wipe(key, sizeof key);
		return rc;
	}
	memset(out, 0, PWHASH_LEN);
	out[0] = 1u;
	out[1] = log2n;
	out[2] = (uint8_t)((r >> 8) & 0xffu);
	out[3] = (uint8_t)( r       & 0xffu);
	out[4] = (uint8_t)((p >> 8) & 0xffu);
	out[5] = (uint8_t)( p       & 0xffu);
	out[6] = 0u;
	out[7] = 0u;
	memcpy(out + 8, salt, 16);
	memcpy(out + 24, key, 32);
	wipe(key, sizeof key);
	return 0;
}

int pwhash_verify(const uint8_t blob[PWHASH_LEN], const uint8_t *pw, size_t pwlen)
{
	uint8_t key[32];
	uint8_t log2n = 0;
	uint16_t r = 0, p = 0;
	int rc, eq;

	if (blob == NULL)
		return -KDFE_BADBLOB;
	rc = pwhash_params(blob, &log2n, &r, &p);
	if (rc != 0)
		return rc;
	/* Through kdf_scrypt, so a blob that asks for more than KDF_PEAK_CAP is
	 * refused rather than allocated: the blob comes off a config store that
	 * a future attacker may be able to write. */
	rc = kdf_scrypt(pw, pwlen, blob + 8, log2n, r, p, key);
	if (rc != 0) {
		wipe(key, sizeof key);
		return rc;
	}
	eq = ct_memeq(key, blob + 24, 32);
	wipe(key, sizeof key);
	return eq;
}

/* --------------------------------------------------------------------------
 * Entropy, fail closed
 * -------------------------------------------------------------------------- */

int kdf_entropy_avail(void)
{
	char buf[32];
	int fd;
	ssize_t got;
	long v = 0;
	int any = 0;
	size_t i;

	fd = open("/proc/sys/kernel/random/entropy_avail", O_RDONLY);
	if (fd < 0)
		return -KDFE_IO;
	for (;;) {
		got = read(fd, buf, sizeof buf - 1u);
		if (got < 0 && errno == EINTR)
			continue;
		break;
	}
	(void)close(fd);
	if (got <= 0)
		return -KDFE_IO;
	buf[got] = '\0';

	/* Decimal by hand: no atoi, and the value is bounded before it is used. */
	for (i = 0; i < (size_t)got; i++) {
		char c = buf[i];
		if (c >= '0' && c <= '9') {
			if (v > 1000000L)            /* far past any real reading */
				return -KDFE_IO;
			v = v * 10L + (long)(c - '0');
			any = 1;
		} else if (any != 0) {
			break;                       /* the number ended */
		} else if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
			continue;                    /* leading space */
		} else {
			return -KDFE_IO;             /* not a number at all */
		}
	}
	if (any == 0)
		return -KDFE_IO;
	return (int)v;
}

int pwhash_salt(uint8_t salt[16])
{
	int e, fd;
	size_t done = 0;
	ssize_t got;

	if (salt == NULL)
		return -KDFE_INVAL;
	memset(salt, 0, 16);

	e = kdf_entropy_avail();
	if (e < 0)
		return e;                            /* -KDFE_IO */
	if (e < KDF_ENTROPY_MIN)
		return -KDFE_ENTROPY;

	fd = open("/dev/urandom", O_RDONLY);
	if (fd < 0)
		return -KDFE_IO;
	while (done < 16u) {
		got = read(fd, salt + done, 16u - done);
		if (got < 0) {
			if (errno == EINTR)
				continue;
			(void)close(fd);
			memset(salt, 0, 16);
			return -KDFE_IO;
		}
		if (got == 0) {                      /* EOF on /dev/urandom */
			(void)close(fd);
			memset(salt, 0, 16);
			return -KDFE_IO;
		}
		done += (size_t)got;
	}
	(void)close(fd);
	return 0;
}
