/* src/rlxboot/test/mkfixture.c -- build signed test containers and staged
 * counter bitmaps.  HOST ONLY.  rlxfw's own code.
 *
 * `tools/mkfw2.py` (another agent, another implementation, same segment) is the
 * real container builder and the main session cross-checks the two.  This one
 * exists because rlxboot's own tests must not depend on a tool written
 * elsewhere in the same segment: if the two disagree, one of them is wrong, and
 * that is only findable if they are independent.  It signs with the development
 * key of `SPEC-R8a.md` s3 and nothing else.
 *
 *   mkfixture container OUT PAYLOAD VERSION LOAD ENTRY RECIPE
 *   mkfixture rcnt      OUT CLEARED_BITS
 *   mkfixture flip      OUT IN BYTEOFF BIT
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../container.h"
#include "../sha256b.h"
#include "../devkey.h"
#include "../../lib/ed25519.h"

static unsigned char buf[RLXU_BODY_OFF + RLXU_PAYLOAD_MAX];

static void be32(unsigned char *p, unsigned long v)
{
	p[0] = (unsigned char)(v >> 24); p[1] = (unsigned char)(v >> 16);
	p[2] = (unsigned char)(v >> 8);  p[3] = (unsigned char)v;
}

static void be16(unsigned char *p, unsigned int v)
{
	p[0] = (unsigned char)(v >> 8); p[1] = (unsigned char)v;
}

static int die(const char *m)
{
	fprintf(stderr, "mkfixture: %s\n", m);
	return 2;
}

int main(int argc, char **argv)
{
	unsigned char sk[64], pk[32];

	if (argc < 3)
		return die("usage: mkfixture container|rcnt|flip OUT ...");

	memcpy(sk, rlxboot_devseed, 32);
	rlx_ed25519_pubkey_from_seed(pk, rlxboot_devseed);
	memcpy(sk + 32, pk, 32);
	if (memcmp(pk, rlxboot_devkey, 32) != 0)
		return die("devkey.h does not match the key derived from the seed");

	if (strcmp(argv[1], "container") == 0) {
		FILE *f;
		unsigned long n, ver, load, entry, recipe;
		unsigned char d[32];

		if (argc != 8)
			return die("container OUT PAYLOAD VERSION LOAD ENTRY RECIPE");
		f = fopen(argv[3], "rb");
		if (!f)
			return die("cannot open the payload file");
		n = (unsigned long)fread(buf + RLXU_BODY_OFF, 1, RLXU_PAYLOAD_MAX, f);
		fclose(f);
		if (n == 0)
			return die("the payload file is empty");
		ver    = strtoul(argv[4], 0, 0);
		load   = strtoul(argv[5], 0, 16);
		entry  = strtoul(argv[6], 0, 16);
		recipe = strtoul(argv[7], 0, 16);

		memset(buf, 0, RLXU_BODY_OFF);
		be32(buf + 0, RLXU_MAGIC);
		be16(buf + 4, RLXU_FORMAT);
		be16(buf + 6, RLXU_HDR_LEN);
		be32(buf + 8, ver);
		be32(buf + 12, n);
		be32(buf + 16, load);
		be32(buf + 20, entry);
		be32(buf + 24, 0);
		sha256b(d, buf + RLXU_BODY_OFF, n);
		memcpy(buf + 28, d, 32);
		be32(buf + 60, recipe);
		rlx_ed25519_sign(buf + RLXU_HDR_LEN, buf, RLXU_HDR_LEN, sk);

		f = fopen(argv[2], "wb");
		if (!f)
			return die("cannot write the container");
		fwrite(buf, 1, RLXU_BODY_OFF + n, f);
		fclose(f);
		printf("container %s: payload %lu, version %lu, load %08lX, entry %08lX\n",
		       argv[2], n, ver, load, entry);
		return 0;
	}

	if (strcmp(argv[1], "rcnt") == 0) {
		/* The RAM-staged counter: the magic word "RCNT" big-endian, then a
		 * 512-byte unary bitmap with `cleared` bits cleared MSB-first. */
		FILE *f;
		unsigned long cleared, i;
		unsigned char out[4 + RLXU_CTR_BYTES];

		if (argc != 4)
			return die("rcnt OUT CLEARED_BITS");
		cleared = strtoul(argv[3], 0, 0);
		if (cleared > RLXU_CTR_BITS)
			return die("cleared bits exceed 4096");
		be32(out, RLXU_CTR_RAM_MAGIC);
		for (i = 0; i < RLXU_CTR_BYTES; i++)
			out[4 + i] = 0xFF;
		for (i = 0; i < cleared; i++)
			out[4 + (i >> 3)] &= (unsigned char)~(1u << (7 - (i & 7)));
		f = fopen(argv[2], "wb");
		if (!f)
			return die("cannot write the bitmap");
		fwrite(out, 1, sizeof out, f);
		fclose(f);
		printf("rcnt %s: counter %lu\n", argv[2], cleared);
		return 0;
	}

	if (strcmp(argv[1], "flip") == 0) {
		FILE *f;
		unsigned long n, off, bit;

		if (argc != 6)
			return die("flip OUT IN BYTEOFF BIT");
		f = fopen(argv[3], "rb");
		if (!f)
			return die("cannot open the input container");
		n = (unsigned long)fread(buf, 1, sizeof buf, f);
		fclose(f);
		off = strtoul(argv[4], 0, 0);
		bit = strtoul(argv[5], 0, 0);
		if (off >= n || bit > 7)
			return die("the flip is outside the container");
		buf[off] ^= (unsigned char)(1u << bit);
		f = fopen(argv[2], "wb");
		if (!f)
			return die("cannot write the container");
		fwrite(buf, 1, n, f);
		fclose(f);
		printf("flip %s: byte %lu bit %lu of %s\n", argv[2], off, bit, argv[3]);
		return 0;
	}

	return die("unknown mode");
}
