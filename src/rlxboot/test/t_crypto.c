/* src/rlxboot/test/t_crypto.c -- the crypto control.  rlxfw's own code.
 *
 * ONE SOURCE FILE, TWO TARGETS.  This is compiled for the host by gcc-13 and
 * clang-18 and for big-endian MIPS by the 4181 rsdk gcc 3.4.6, and the MIPS
 * build is run under `qemu-mips-static`.  That is the whole point: a verifier
 * that is right little-endian and wrong big-endian passes every host test, and
 * `SPEC-R8a.md` s3 names exactly that defect.  The same vectors, the same
 * source, two byte orders.
 *
 * It is a test, so libc is allowed here.  The payload links none of it.
 *
 *   t_crypto              run every case, print one line each, exit non-zero on
 *                         the first failure count > 0
 *   t_crypto digest N     print `sha256 <hex>` and `sha512 <hex>` of the
 *                         deterministic message of length N, so the shell can
 *                         compare with coreutils -- an independent second
 *                         source for the hashes that no vector table provides
 *   t_crypto stack        measure the verifier's worst-case stack depth
 *   t_crypto devkey       print the public key derived from SPEC s3's seed
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../sha256b.h"
#include "../../lib/sha512.h"
#include "../../lib/ed25519.h"
#include "vectors.h"

static int failures;
static int checks;

static void ok(const char *what, int good)
{
	checks++;
	if (!good) {
		failures++;
		printf("FAIL  %s\n", what);
	} else {
		printf("ok    %s\n", what);
	}
}

static void hex(const unsigned char *p, unsigned long n, char *out)
{
	static const char d[] = "0123456789abcdef";
	unsigned long i;

	for (i = 0; i < n; i++) {
		out[2 * i] = d[p[i] >> 4];
		out[2 * i + 1] = d[p[i] & 15];
	}
	out[2 * n] = 0;
}

/* The deterministic message of length n: a 32-bit LCG, so the host and the
 * MIPS build hash IDENTICAL bytes.  `rand()` would have made the two builds
 * hash different messages and the comparison meaningless. */
static void genmsg(unsigned char *p, unsigned long n)
{
	unsigned long i, s = 0x12345678UL;

	for (i = 0; i < n; i++) {
		s = (s * 1103515245UL + 12345UL) & 0xFFFFFFFFUL;
		p[i] = (unsigned char)((s >> 16) & 0xff);
	}
}

/* ------------------------------------------------------------------- hashes */

static unsigned char big[1000000];

static void test_hashes(void)
{
	unsigned char d[64];
	int i;

	for (i = 0; i < SHA_VECTORS; i++) {
		const struct sha_vec *v = &sha_vectors[i];
		const unsigned char *m = v->msg;
		unsigned long n = v->msglen;
		char nm[96];

		if (n > 4096) {            /* TEST3: a million 'a's, built here */
			memset(big, 'a', n);
			m = big;
		}
		sha256b(d, m, n);
		sprintf(nm, "sha256  %s (%lu bytes)%s", v->name, n,
		        v->rfc256 ? " [RFC 6234]" : "");
		ok(nm, memcmp(d, v->d256, 32) == 0);

		rlx_sha512(d, m, n);
		sprintf(nm, "sha512  %s (%lu bytes)%s", v->name, n,
		        v->rfc512 ? " [RFC 6234]" : "");
		ok(nm, memcmp(d, v->d512, 64) == 0);
	}

	/* The chunked path.  A one-shot-only suite never exercises `buflen`, and
	 * the boot path is one-shot -- so the incremental interface would be
	 * untested code in a signed loader.  Odd chunk sizes on purpose: 64 and
	 * 32 would never leave a partial block behind. */
	{
		struct sha256b c;
		unsigned char one[32], many[32];
		unsigned long n = 100000, off;
		unsigned long step = 37;

		memset(big, 'a', n);
		sha256b(one, big, n);
		sha256b_init(&c);
		for (off = 0; off < n; off += step) {
			unsigned long k = (n - off < step) ? n - off : step;
			sha256b_update(&c, big + off, k);
		}
		sha256b_final(&c, many);
		ok("sha256  chunked at 37 bytes == one-shot", memcmp(one, many, 32) == 0);
	}

	/* The length accumulator's carry.  0x20000000 bytes is 2^32 bits exactly,
	 * so this is the first length at which the high half must be non-zero.
	 * Fed as 8,192 chunks of 65,536 so nothing needs 512 MiB of memory.  The
	 * expected digest is not a vector -- there is none this long -- so what
	 * is checked is that the two halves of the counter hold the right value,
	 * read back out of the context before `final`. */
	{
		struct sha256b c;
		unsigned long k;

		memset(big, 0, 65536);
		sha256b_init(&c);
		for (k = 0; k < 8192; k++)
			sha256b_update(&c, big, 65536);
		ok("sha256  bit counter carried at 2^32 bits",
		   c.nbits_hi == 1UL && c.nbits_lo == 0UL);
		sha256b_update(&c, big, 1);
		ok("sha256  bit counter past the carry",
		   c.nbits_hi == 1UL && c.nbits_lo == 8UL);
	}
}

/* ------------------------------------------------------------------ ed25519 */

static void test_ed25519(void)
{
	unsigned char pk[32], sig[64], tmp[64], m[1100];
	char nm[96];
	int i;

	for (i = 0; i < ED_VECTORS; i++) {
		const struct ed_vec *v = &ed_vectors[i];
		unsigned char sk[64];

		memcpy(sk, v->sk, 32);
		rlx_ed25519_pubkey_from_seed(pk, v->sk);
		sprintf(nm, "ed25519 %s public key from seed", v->name);
		ok(nm, memcmp(pk, v->pk, 32) == 0);

		memcpy(sk + 32, v->pk, 32);
		rlx_ed25519_sign(sig, v->msg, v->msglen, sk);
		sprintf(nm, "ed25519 %s signature", v->name);
		ok(nm, memcmp(sig, v->sig, 64) == 0);

		sprintf(nm, "ed25519 %s verifies", v->name);
		ok(nm, rlx_ed25519_verify(v->sig, v->msg, v->msglen, v->pk) == 0);
	}

	/* THE THREE NEGATIVE CONTROLS, and each is a sweep rather than an
	 * example: SPEC s3 asks for a flipped bit in the signature, the message
	 * and the public key, and "a flipped bit" with no quantifier is how a
	 * suite ends up testing bit 0 of byte 0 three times. */
	{
		const struct ed_vec *v = &ed_vectors[ED_VECTORS - 1];  /* 64-byte msg */
		int bit, bad = 0;

		for (bit = 0; bit < 64 * 8; bit++) {
			memcpy(tmp, v->sig, 64);
			tmp[bit >> 3] ^= (unsigned char)(1u << (bit & 7));
			if (rlx_ed25519_verify(tmp, v->msg, v->msglen, v->pk) == 0)
				bad++;
		}
		ok("ed25519 every one of 512 signature bit flips rejected", bad == 0);

		bad = 0;
		for (bit = 0; bit < (int)v->msglen * 8; bit++) {
			memcpy(m, v->msg, v->msglen);
			m[bit >> 3] ^= (unsigned char)(1u << (bit & 7));
			if (rlx_ed25519_verify(v->sig, m, v->msglen, v->pk) == 0)
				bad++;
		}
		ok("ed25519 every one of 512 message bit flips rejected", bad == 0);

		bad = 0;
		for (bit = 0; bit < 32 * 8; bit++) {
			memcpy(pk, v->pk, 32);
			pk[bit >> 3] ^= (unsigned char)(1u << (bit & 7));
			if (rlx_ed25519_verify(v->sig, v->msg, v->msglen, pk) == 0)
				bad++;
		}
		ok("ed25519 every one of 256 public key bit flips rejected", bad == 0);

		/* The positive control on those three sweeps: restore and it must
		 * verify again.  Without this, a verifier that rejected everything
		 * -- including a stuck `return -1` -- would pass all three. */
		ok("ed25519 unflipped still verifies (sweep positive control)",
		   rlx_ed25519_verify(v->sig, v->msg, v->msglen, v->pk) == 0);
	}

	/* s + L in place of s.  Upstream's `crypto_sign_open` accepts this; the
	 * wrapper's `rlx_s_below_L` refuses it.  A valid signature is needed to
	 * build it, so this is malleability and not forgery -- but a loader for
	 * which two byte strings authorise one container is a loader whose
	 * bit-flip sweep proves less than it looks.  This is the positive
	 * control on that branch: without it, `rlx_s_below_L` could return 1
	 * always and nothing else would notice. */
	{
		const struct ed_vec *v = &ed_vectors[1];
		static const unsigned char L[32] = {
			0xed,0xd3,0xf5,0x5c,0x1a,0x63,0x12,0x58,
			0xd6,0x9c,0xf7,0xa2,0xde,0xf9,0xde,0x14,
			0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x10
		};
		unsigned int carry = 0;
		int k;

		memcpy(tmp, v->sig, 64);
		for (k = 0; k < 32; k++) {
			carry += (unsigned int)tmp[32 + k] + (unsigned int)L[k];
			tmp[32 + k] = (unsigned char)(carry & 0xff);
			carry >>= 8;
		}
		ok("ed25519 s + L refused as non-canonical",
		   rlx_ed25519_verify(tmp, v->msg, v->msglen, v->pk)
		       == RLX_ED25519_ESCALAR);
	}

	/* A message longer than the bound is REFUSED, not truncated. */
	ok("ed25519 msglen > ED25519_MSG_MAX refused",
	   rlx_ed25519_verify(ed_vectors[0].sig, m, ED25519_MSG_MAX + 1,
	                      ed_vectors[0].pk) == RLX_ED25519_ETOOLONG);
}

/* ------------------------------------------------------------- the dev key */

static const unsigned char dev_seed[32] = {
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42
};

static void print_devkey(void)
{
	unsigned char pk[32];
	char h[80];

	rlx_ed25519_pubkey_from_seed(pk, dev_seed);
	hex(pk, 32, h);
	printf("devkey %s\n", h);
}

/* ---------------------------------------------------------------- the stack */

/* Paint a window below the current stack pointer, run one verification, then
 * find the deepest byte that is no longer painted.  The number this prints is
 * what `STACK_SIZE` in the linker script is sized against.
 *
 * It is a MEASUREMENT with a known weakness, stated rather than hidden: it sees
 * only bytes the callee actually wrote, so a frame that is reserved and not
 * written reads as unused.  It is therefore a lower bound on the depth, and the
 * stack the payload reserves is many times it.
 *
 * The pointer goes through a `volatile` global so the compiler cannot track its
 * provenance: with `&probe` used directly, gcc-13 is right that a subscript of
 * -65535 is outside a one-byte object, and `-Werror=array-bounds` refuses it.
 * That diagnostic is correct and the code is deliberate, which is exactly the
 * case for hiding the provenance rather than for widening the warning set.
 *
 * NOT RUN UNDER -fsanitize=address: painting 64 KiB below the frame is a
 * stack-buffer-underflow by construction, and ASan is right about that too.
 * The sanitiser build runs every other case. */
static unsigned char * volatile sp_hook;

static void measure_stack(void)
{
	unsigned char probe;
	unsigned char *sp;
	unsigned long window = 64u * 1024u;
	unsigned long i, deepest = 0;
	const struct ed_vec *v = &ed_vectors[3];        /* the 1023-byte message */

	probe = 0;
	sp_hook = &probe;
	sp = sp_hook;
	for (i = 1024; i < window; i++)
		sp[-(long)i] = 0xA5;
	if (rlx_ed25519_verify(v->sig, v->msg, v->msglen, v->pk) != 0) {
		printf("stack  MEASUREMENT VOID: the verification failed\n");
		failures++;
		return;
	}
	for (i = window - 1; i >= 1024; i--) {
		if (sp[-(long)i] != 0xA5) {
			deepest = i;
			break;
		}
	}
	printf("stack  verifier touched %lu bytes below sp (paint window %lu)\n",
	       deepest, window);
	if (deepest + 2048 >= window) {
		printf("FAIL   the paint window was too small to bound the depth\n");
		failures++;
	}
}

int main(int argc, char **argv)
{
	if (argc > 1 && strcmp(argv[1], "devkey") == 0) {
		print_devkey();
		return 0;
	}
	if (argc > 1 && strcmp(argv[1], "stack") == 0) {
		measure_stack();
		return failures ? 1 : 0;
	}
	if (argc > 2 && strcmp(argv[1], "digest") == 0) {
		unsigned long n = strtoul(argv[2], 0, 10);
		unsigned char d[64];
		char h[160];

		if (n > sizeof big)
			return 2;
		genmsg(big, n);
		/* argv[3], when given, is where the message itself is written, so
		 * the shell can hand THE SAME BYTES to coreutils.  It used to
		 * reproduce `genmsg` in awk instead, and that was wrong in a way
		 * worth recording: awk computes in doubles, `s * 1103515245`
		 * exceeds 2^53, and the LCG silently diverged after the first two
		 * bytes -- 199 of 201 lengths "disagreed with coreutils" when
		 * every digest was in fact correct.  A cross-check must not
		 * reimplement the input; it must be handed it. */
		if (argc > 3) {
			FILE *f = fopen(argv[3], "wb");
			if (!f)
				return 2;
			if (n)
				fwrite(big, 1, n, f);
			fclose(f);
		}
		sha256b(d, big, n);
		hex(d, 32, h);
		printf("sha256 %s\n", h);
		rlx_sha512(d, big, n);
		hex(d, 64, h);
		printf("sha512 %s\n", h);
		return 0;
	}

	test_hashes();
	test_ed25519();
	print_devkey();
	printf("t_crypto %d checks, %d failures\n", checks, failures);
	return failures ? 1 : 0;
}
