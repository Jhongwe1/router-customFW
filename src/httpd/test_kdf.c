/* test_kdf.c -- the RFC vectors for src/lib/sha256.c and src/lib/kdf.c, and
 * the pwhash blob round trip.  Host test; also run under qemu-mips-static.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT CHECKS
 * ---------------------------------------------------------------------------
 *
 * SHA-256 (FIPS 180-2 / RFC 6234 section 8.5), HMAC-SHA-256 (RFC 4231 cases
 * 1-7), PBKDF2-HMAC-SHA-256 (RFC 7914 section 11, plus the RFC 6070 shape at
 * SHA-256), scrypt (RFC 7914 section 12, all four), then the 56-byte
 * `admin.pwhash` blob of SPEC-R7 section 4.2 and the memory cap
 * `KDF_PEAK_CAP` in both directions -- a refusal AND an acceptance.
 *
 * ---------------------------------------------------------------------------
 * WHY IT IS RUN TWICE, ON TWO ENDIANNESSES
 * ---------------------------------------------------------------------------
 *
 * scrypt's Salsa20 state is little-endian inside a big-endian target.  A byte
 * order mistake in that one place passes every vector on an x86 host and fails
 * on the device, so a green run here is evidence only for the machine it ran
 * on.  The target run is `qemu-mips-static ./test_kdf` on a static
 * big-endian ELF from the rsdk gcc 3.4.6.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES NOT ESTABLISH
 * ---------------------------------------------------------------------------
 *
 *  - Not timing.  It measures nothing; the cost of one evaluation on the
 *    RTL8196E is 推 until measured on the silicon, and a figure taken under
 *    qemu is the emulator's.
 *  - Not the absence of side channels, and not that any `wipe` cleared DRAM.
 *  - `ok` on the 1 GiB RFC 7914 vector without `--big` means SKIPPED, which
 *    is why the totals line says so.  A suite that counted it as a pass and
 *    said nothing would be lying by arithmetic.
 *  - A pass says these inputs produce these outputs.  It says nothing about
 *    inputs no vector covers -- in particular no vector here has a salt
 *    longer than 16 bytes through the pinned `kdf_scrypt` wrapper, because
 *    that wrapper cannot express one.
 */
/* src/httpd/Makefile compiles this with -I$(LIB) on the host and -I./lib on the
 * staged target tree, so the plain form is the one that works in both; a
 * "../lib/..." path would break under the target staging, which flattens the
 * layout. */
#include "kdf.h"
#include "sha256.h"

#include <stdio.h>
#include <string.h>

static int ntest = 0;
static int npass = 0;
static int nskip = 0;

static void puthex(const uint8_t *b, size_t n)
{
	size_t i;

	for (i = 0; i < n; i++)
		printf("%02x", (unsigned int)b[i]);
}

static void checkb(const char *name, const uint8_t *got, const uint8_t *want, size_t n)
{
	ntest++;
	if (memcmp(got, want, n) == 0) {
		npass++;
		printf("ok %d - %s\n", ntest, name);
		return;
	}
	printf("not ok %d - %s: got ", ntest, name);
	puthex(got, n);
	printf(" want ");
	puthex(want, n);
	printf("\n");
}

static void checki(const char *name, long got, long want)
{
	ntest++;
	if (got == want) {
		npass++;
		printf("ok %d - %s\n", ntest, name);
		return;
	}
	printf("not ok %d - %s: got %ld want %ld\n", ntest, name, got, want);
}

static int hexval(int c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

/* Bounded: refuses an odd digit count, a non-hex character, or more than
 * `outmax` bytes.  Every expected value in this file goes through it, so it is
 * self-tested below before anything trusts it. */
static int unhex(const char *s, uint8_t *out, size_t outmax, size_t *outlen)
{
	size_t n = 0;
	int hi, lo;

	if (s == NULL || out == NULL)
		return -1;
	while (s[0] != '\0') {
		if (s[1] == '\0')
			return -1;
		hi = hexval((unsigned char)s[0]);
		lo = hexval((unsigned char)s[1]);
		if (hi < 0 || lo < 0)
			return -1;
		if (n >= outmax)
			return -1;
		out[n] = (uint8_t)(((unsigned int)hi << 4) | (unsigned int)lo);
		n++;
		s += 2;
	}
	if (outlen != NULL)
		*outlen = n;
	return 0;
}

#define EXPMAX 64

static void check_hex(const char *name, const uint8_t *got, const char *wanthex, size_t n)
{
	uint8_t want[EXPMAX];
	size_t wl = 0;

	if (unhex(wanthex, want, sizeof want, &wl) != 0 || wl != n) {
		ntest++;
		printf("not ok %d - %s: this test's own expected value is malformed\n",
		       ntest, name);
		return;
	}
	checkb(name, got, want, n);
}

/* A non-zero return is a failure of the case, not a reason to skip it. */
static void check_out(const char *name, int rc, const uint8_t *got,
                      const char *wanthex, size_t n)
{
	if (rc != 0) {
		ntest++;
		printf("not ok %d - %s: the call returned %d\n", ntest, name, rc);
		return;
	}
	check_hex(name, got, wanthex, n);
}

/* --------------------------------------------------------------------------
 * The instrument's own control: if `unhex` is broken every vector below is
 * meaningless, so it is checked first, in both directions.
 * -------------------------------------------------------------------------- */
static void t_unhex(void)
{
	uint8_t b[4];
	size_t n = 0;
	int bad = 0;

	memset(b, 0xff, sizeof b);
	if (unhex("00ff10AB", b, sizeof b, &n) != 0)
		bad++;
	if (n != 4)
		bad++;
	if (b[0] != 0x00u || b[1] != 0xffu || b[2] != 0x10u || b[3] != 0xabu)
		bad++;
	if (unhex("abc", b, sizeof b, &n) == 0)          /* odd length */
		bad++;
	if (unhex("00gg", b, sizeof b, &n) == 0)         /* not hex */
		bad++;
	if (unhex("0011223344", b, sizeof b, &n) == 0)   /* over the bound */
		bad++;
	if (unhex("", b, sizeof b, &n) != 0 || n != 0)   /* empty is 0 bytes */
		bad++;
	checki("unhex-self-test", (long)bad, 0L);
}

/* --------------------------------------------------------------------------
 * SHA-256, FIPS 180-2 / RFC 6234 section 8.5
 * -------------------------------------------------------------------------- */
static void t_sha256(void)
{
	static const char s56[] =
		"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
	uint8_t d[SHA256_DIGEST_LEN];
	uint8_t chunk[1000];
	struct sha256_ctx c;
	int i;

	(void)sha256("abc", 3, d);
	check_hex("sha256-abc", d,
		"ba7816bf8f01cfea414140de5dae2223"
		"b00361a396177a9cb410ff61f20015ad", 32);

	(void)sha256(s56, strlen(s56), d);
	check_hex("sha256-56byte", d,
		"248d6a61d20638b8e5c026930c3e6039"
		"a33ce45964ff2167f6ecedd419db06c1", 32);

	/* One million 'a', fed in 1,000 chunks of 1,000 -- not a multiple of the
	 * 64-byte block, so the streaming buffer is exercised at every phase. */
	memset(chunk, 'a', sizeof chunk);
	sha256_init(&c);
	for (i = 0; i < 1000; i++)
		sha256_update(&c, chunk, sizeof chunk);
	sha256_final(&c, d);
	check_hex("sha256-million-a", d,
		"cdc76e5c9914fb9281a1c7e284d73e67"
		"f1809a48a497200e046d39ccc7112cd0", 32);

	(void)sha256("", 0, d);
	check_hex("sha256-empty", d,
		"e3b0c44298fc1c149afbf4c8996fb924"
		"27ae41e4649b934ca495991b7852b855", 32);
}

/* --------------------------------------------------------------------------
 * HMAC-SHA-256, RFC 4231 test cases 1-7
 * -------------------------------------------------------------------------- */
static void t_hmac(void)
{
	static const char m7[] =
		"This is a test using a larger than block-size key and a larger "
		"than block-size data. The key needs to be hashed before being "
		"used by the HMAC algorithm.";
	uint8_t key[131], data[50], d[SHA256_DIGEST_LEN];
	size_t i;

	for (i = 0; i < 20; i++)
		key[i] = 0x0bu;
	(void)hmac_sha256(key, 20, "Hi There", strlen("Hi There"), d);
	check_hex("hmac-rfc4231-1", d,
		"b0344c61d8db38535ca8afceaf0bf12b"
		"881dc200c9833da726e9376c2e32cff7", 32);

	(void)hmac_sha256((const uint8_t *)"Jefe", 4,
		"what do ya want for nothing?", strlen("what do ya want for nothing?"), d);
	check_hex("hmac-rfc4231-2", d,
		"5bdcc146bf60754e6a042426089575c7"
		"5a003f089d2739839dec58b964ec3843", 32);

	for (i = 0; i < 20; i++)
		key[i] = 0xaau;
	for (i = 0; i < 50; i++)
		data[i] = 0xddu;
	(void)hmac_sha256(key, 20, data, 50, d);
	check_hex("hmac-rfc4231-3", d,
		"773ea91e36800e46854db8ebd09181a7"
		"2959098b3ef8c122d9635514ced565fe", 32);

	for (i = 0; i < 25; i++)                 /* 0x01 02 .. 19 */
		key[i] = (uint8_t)(i + 1u);
	for (i = 0; i < 50; i++)
		data[i] = 0xcdu;
	(void)hmac_sha256(key, 25, data, 50, d);
	check_hex("hmac-rfc4231-4", d,
		"82558a389a443c0ea4cc819899f2083a"
		"85f0faa3e578f8077a2e3ff46729665b", 32);

	/* Case 5: RFC 4231 publishes only the 128-bit truncation. */
	for (i = 0; i < 20; i++)
		key[i] = 0x0cu;
	(void)hmac_sha256(key, 20, "Test With Truncation",
		strlen("Test With Truncation"), d);
	check_hex("hmac-rfc4231-5-128", d, "a3b6167473100ee06e0c796c2955552b", 16);

	/* Cases 6 and 7: a 131-byte key, longer than the 64-byte block, so K is
	 * hashed first (RFC 2104). */
	for (i = 0; i < 131; i++)
		key[i] = 0xaau;
	(void)hmac_sha256(key, 131,
		"Test Using Larger Than Block-Size Key - Hash Key First",
		strlen("Test Using Larger Than Block-Size Key - Hash Key First"), d);
	check_hex("hmac-rfc4231-6", d,
		"60e431591ee0b67f0d8a26aacbf5b77f"
		"8e0bc6213728c5140546040f0ee37f54", 32);

	(void)hmac_sha256(key, 131, m7, strlen(m7), d);
	check_hex("hmac-rfc4231-7", d,
		"9b09ffa71b942fcb27635fbcd5b0e944"
		"bfdc63644f0713938a7f51535c3a35e2", 32);
}

/* --------------------------------------------------------------------------
 * PBKDF2-HMAC-SHA-256
 * -------------------------------------------------------------------------- */
static void t_pbkdf2(void)
{
	uint8_t dk[64];
	int rc;

	/* RFC 7914 section 11 */
	rc = kdf_pbkdf2_sha256((const uint8_t *)"passwd", 6,
		(const uint8_t *)"salt", 4, 1u, dk, 64);
	check_out("pbkdf2-rfc7914-passwd-salt-c1", rc, dk,
		"55ac046e56e3089fec1691c22544b605"
		"f94185216dde0465e68b9d57c20dacbc"
		"49ca9cccf179b645991664b39d77ef31"
		"7c71b845b1e30bd509112041d3a19783", 64);

	rc = kdf_pbkdf2_sha256((const uint8_t *)"Password", 8,
		(const uint8_t *)"NaCl", 4, 80000u, dk, 64);
	check_out("pbkdf2-rfc7914-Password-NaCl-c80000", rc, dk,
		"4ddcd8f60b98be21830cee5ef22701f9"
		"641a4418d04c0414aeff08876b34ab56"
		"a1d425a1225833549adb841b51c9b317"
		"6a272bdebba1d078478f62b397f33c8d", 64);

	/* The RFC 6070 shape at SHA-256: "password"/"salt", dkLen 32. */
	rc = kdf_pbkdf2_sha256((const uint8_t *)"password", 8,
		(const uint8_t *)"salt", 4, 1u, dk, 32);
	check_out("pbkdf2-password-salt-c1-dk32", rc, dk,
		"120fb6cffcf8b32c43e7225256c4f837"
		"a86548c92ccc35480805987cb70be17b", 32);

	rc = kdf_pbkdf2_sha256((const uint8_t *)"password", 8,
		(const uint8_t *)"salt", 4, 2u, dk, 32);
	check_out("pbkdf2-password-salt-c2-dk32", rc, dk,
		"ae4d0c95af6b46d32d0adff928f06dd0"
		"2a303f8ef3c251dfd6e2d85a95474c43", 32);

	rc = kdf_pbkdf2_sha256((const uint8_t *)"password", 8,
		(const uint8_t *)"salt", 4, 4096u, dk, 32);
	check_out("pbkdf2-password-salt-c4096-dk32", rc, dk,
		"c5e478d59288c841aa530db6845c4c8d"
		"962893a001ce4e11a4963873aa98134a", 32);
}

/* --------------------------------------------------------------------------
 * scrypt, RFC 7914 section 12.  All four; the fourth wants 1 GiB.
 * -------------------------------------------------------------------------- */
static void t_scrypt(int big)
{
	uint8_t dk[64];
	int rc;

	rc = kdf_scrypt_raw((const uint8_t *)"", 0, (const uint8_t *)"", 0,
		16u, 1u, 1u, dk, 64);
	check_out("rfc7914-p1", rc, dk,
		"77d6576238657b203b19ca42c18a0497"
		"f16b4844e3074ae8dfdffa3fede21442"
		"fcd0069ded0948f8326a753a0fc81f17"
		"e8d3e0fb2e0d3628cf35e20c38d18906", 64);

	rc = kdf_scrypt_raw((const uint8_t *)"password", 8,
		(const uint8_t *)"NaCl", 4, 1024u, 8u, 16u, dk, 64);
	check_out("rfc7914-p2", rc, dk,
		"fdbabe1c9d3472007856e7190d01e9fe"
		"7c6ad7cbc8237830e77376634b373162"
		"2eaf30d92e22a3886ff109279d9830da"
		"c727afb94a83ee6d8360cbdfa2cc0640", 64);

	rc = kdf_scrypt_raw((const uint8_t *)"pleaseletmein", 13,
		(const uint8_t *)"SodiumChloride", 14, 16384u, 8u, 1u, dk, 64);
	check_out("rfc7914-p3", rc, dk,
		"7023bdcb3afd7348461c06cd81fd38eb"
		"fda8fbba904f8e3ea9b543f6545da1f2"
		"d5432955613f0fcf62d49705242a9af9"
		"e61e85dc0d651e40dfcf017b45575887", 64);

	if (big == 0) {
		ntest++;
		npass++;
		nskip++;
		printf("ok %d - rfc7914-p4 skipped (1 GiB, opt-in --big)\n", ntest);
		return;
	}
	rc = kdf_scrypt_raw((const uint8_t *)"pleaseletmein", 13,
		(const uint8_t *)"SodiumChloride", 14, 1048576u, 8u, 1u, dk, 64);
	check_out("rfc7914-p4", rc, dk,
		"2101cb9b6a511aaeaddbbe09cf70f881"
		"ec568d574a2ffd4dabe5ee9820adaa47"
		"8e56fd8f4ba5d09ffa1c6d927c40f4c3"
		"37304049e8a952fbcbf45c6fa77a41a4", 64);
}

/* --------------------------------------------------------------------------
 * The 56-byte admin.pwhash blob, SPEC-R7 section 4.2
 * -------------------------------------------------------------------------- */
static void t_pwhash(void)
{
	static const char pw[] = "correct horse battery staple";
	uint8_t salt[16], blob[PWHASH_LEN], bad[PWHASH_LEN];
	uint8_t log2n = 0;
	uint16_t r = 0, p = 0;
	size_t i;
	int rc, bd;

	for (i = 0; i < 16; i++)
		salt[i] = (uint8_t)(0x40u + i);

	rc = pwhash_make((const uint8_t *)pw, strlen(pw),
		KDF_LOG2N, KDF_R, KDF_P, salt, blob);
	if (rc != 0) {
		ntest++;
		printf("not ok %d - pwhash-make: rc=%d\n", ntest, rc);
		return;                          /* the rest cannot be judged */
	}

	/* The header bytes, field by field, against section 4.2. */
	bd = 0;
	if (blob[0] != 1u)                       bd++;   /* alg = 1, scrypt */
	if (blob[1] != (uint8_t)KDF_LOG2N)       bd++;
	if (blob[2] != 0u || blob[3] != KDF_R)   bd++;   /* r, big-endian */
	if (blob[4] != 0u || blob[5] != KDF_P)   bd++;   /* p, big-endian */
	if (blob[6] != 0u || blob[7] != 0u)      bd++;   /* reserved */
	if (memcmp(blob + 8, salt, 16) != 0)     bd++;   /* salt at [8..23] */
	checki("pwhash-blob-layout", (long)bd, 0L);

	bd = 0;
	if (pwhash_params(blob, &log2n, &r, &p) != 0)    bd++;
	if (log2n != (uint8_t)KDF_LOG2N)                 bd++;
	if (r != (uint16_t)KDF_R)                        bd++;
	if (p != (uint16_t)KDF_P)                        bd++;
	checki("pwhash-params", (long)bd, 0L);

	checki("pwhash-roundtrip",
		(long)pwhash_verify(blob, (const uint8_t *)pw, strlen(pw)), 1L);

	memcpy(bad, blob, PWHASH_LEN);
	bad[24] = (uint8_t)(bad[24] ^ 0x01u);    /* one bit of the stored key */
	checki("pwhash-flip-key",
		(long)pwhash_verify(bad, (const uint8_t *)pw, strlen(pw)), 0L);

	memcpy(bad, blob, PWHASH_LEN);
	bad[8] = (uint8_t)(bad[8] ^ 0x01u);      /* one bit of the salt */
	checki("pwhash-flip-salt",
		(long)pwhash_verify(bad, (const uint8_t *)pw, strlen(pw)), 0L);

	memcpy(bad, blob, PWHASH_LEN);
	bad[0] = 2u;                             /* an algorithm that is not 1 */
	checki("pwhash-bad-alg",
		(long)pwhash_verify(bad, (const uint8_t *)pw, strlen(pw)),
		(long)-KDFE_BADBLOB);

	memcpy(bad, blob, PWHASH_LEN);
	bad[6] = 1u;                             /* reserved must read zero */
	checki("pwhash-bad-reserved",
		(long)pwhash_verify(bad, (const uint8_t *)pw, strlen(pw)),
		(long)-KDFE_BADBLOB);
}

static void t_ct_memeq(void)
{
	uint8_t a[17], b[17];
	size_t n, i;
	int bad = 0;

	for (n = 0; n <= 16u; n++) {
		for (i = 0; i < sizeof a; i++) {
			a[i] = (uint8_t)(i * 7u + 1u);
			b[i] = a[i];
		}
		if (ct_memeq(a, b, n) != 1)
			bad++;
		if ((memcmp(a, b, n) == 0) != (ct_memeq(a, b, n) == 1))
			bad++;
		for (i = 0; i < n; i++) {
			b[i] = (uint8_t)(b[i] ^ 0x80u);
			if (ct_memeq(a, b, n) != 0)
				bad++;
			if ((memcmp(a, b, n) == 0) != (ct_memeq(a, b, n) == 1))
				bad++;
			b[i] = (uint8_t)(b[i] ^ 0x80u);
		}
	}
	checki("ct_memeq-sweep", (long)bad, 0L);
}

/* --------------------------------------------------------------------------
 * The memory accounting and the cap, shown refusing AND permitting
 * -------------------------------------------------------------------------- */
static void t_peak_and_cap(void)
{
	uint8_t salt[16], out[32], out2[32];
	size_t i;
	int rc, bd;

	/* V + XY + B = N*128*r + 2*128*r + p*128*r */
	checki("peak-12-7-1", (long)kdf_scrypt_peak(12, 7, 1),
		4096L * 896L + 2L * 896L + 1L * 896L);
	checki("peak-12-8-1", (long)kdf_scrypt_peak(12, 8, 1),
		4096L * 1024L + 2L * 1024L + 1L * 1024L);
	checki("peak-11-8-1", (long)kdf_scrypt_peak(11, 8, 1),
		2048L * 1024L + 2L * 1024L + 1L * 1024L);

	bd = 0;
	if (kdf_scrypt_peak(0, 8, 1) != 0)   bd++;   /* N = 1 */
	if (kdf_scrypt_peak(12, 0, 1) != 0)  bd++;   /* r = 0 */
	if (kdf_scrypt_peak(12, 8, 0) != 0)  bd++;   /* p = 0 */
	if (kdf_scrypt_peak(32, 1, 1) != 0)  bd++;   /* past the log2n bound */
	if (kdf_scrypt_peak(255, 8, 1) != 0) bd++;
	/* RFC 7914 section 6: N < 2^(16*r), so r = 1 admits N up to 32768 and
	 * refuses 65536.  Shown in both directions. */
	if (kdf_scrypt_peak(16, 1, 1) != 0)  bd++;
	if (kdf_scrypt_peak(15, 1, 1) == 0)  bd++;
	if (kdf_scrypt_peak(16, 2, 1) == 0)  bd++;   /* r = 2 lifts the bound */
	checki("peak-refuses-bad-params", (long)bd, 0L);

	/* The size_t overflow guard.  With the pinned argument types it is
	 * reachable only where size_t is 32 bits -- which is the target, and not
	 * the host that runs the sanitizers.  So the expectation is the
	 * machine's, and the case says which machine it is asserting about
	 * instead of quietly passing on one of them. */
	bd = 0;
	if (sizeof(size_t) == 4u) {
		if (kdf_scrypt_peak(31, 65535, 1) != 0)
			bd++;                    /* 2^31 * 8,388,480 > 2^32 */
	} else {
		if (kdf_scrypt_peak(31, 65535, 1) == 0)
			bd++;                    /* representable in 64 bits */
	}
	checki("peak-overflow-guard-32bit-only", (long)bd, 0L);

	for (i = 0; i < 16; i++)
		salt[i] = (uint8_t)i;

	/* (12,8,1) needs 4,197,376 bytes: 3,072 over KDF_PEAK_CAP. */
	rc = kdf_scrypt((const uint8_t *)"x", 1, salt, 12, 8, 1, out);
	checki("scrypt-cap-refuses-12-8-1", (long)rc, (long)-KDFE_INVAL);

	rc = kdf_scrypt((const uint8_t *)"x", 1, salt, KDF_LOG2N, KDF_R, KDF_P, out);
	checki("scrypt-cap-accepts-recommended", (long)rc, 0L);

	/* The pinned wrapper is kdf_scrypt_raw with saltlen 16, N = 1<<log2n and
	 * dkLen 32, and nothing else. */
	rc = kdf_scrypt_raw((const uint8_t *)"x", 1, salt, 16,
		(uint32_t)1u << KDF_LOG2N, KDF_R, KDF_P, out2, 32);
	if (rc != 0) {
		ntest++;
		printf("not ok %d - scrypt-wrapper-matches-raw: raw rc=%d\n", ntest, rc);
	} else {
		checkb("scrypt-wrapper-matches-raw", out, out2, 32);
	}
}

int main(int argc, char **argv)
{
	int big = 0;

	if (argc > 2) {
		fprintf(stderr, "usage: test_kdf [--big]\n");
		return 2;
	}
	if (argc == 2) {
		if (strcmp(argv[1], "--big") == 0) {
			big = 1;
		} else {
			fprintf(stderr, "usage: test_kdf [--big]\n");
			return 2;
		}
	}

	t_unhex();
	t_sha256();
	t_hmac();
	t_pbkdf2();
	t_scrypt(big);
	t_pwhash();
	t_ct_memeq();
	t_peak_and_cap();

	if (nskip > 0)
		printf("# %d/%d passed (%d skipped)\n", npass, ntest, nskip);
	else
		printf("# %d/%d passed\n", npass, ntest);
	return (npass == ntest) ? 0 : 1;
}
