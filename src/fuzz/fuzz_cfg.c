/* fuzz_cfg.c -- drives cfg_parse_record from one file.  A plain
 * main(argc, argv), so `afl-fuzz -- ./fuzz_cfg @@` and `./fuzz_cfg somefile`
 * are the same program.
 *
 * ---------------------------------------------------------------------------
 * WHY IT PARSES EVERY INPUT TWICE, AND WHAT THAT COSTS
 * ---------------------------------------------------------------------------
 *
 * The record carries two CRC-32 fields and cfg_parse_record checks the header's
 * before it reads any header field (see cfg.c).  That makes the format
 * FUZZ-HOSTILE: essentially every mutation of a valid seed fails the header CRC
 * and returns after nine instructions, so a naive harness explores the first
 * two branches of the function and nothing else.  Measured: it is not a
 * throughput problem, it is a reachability problem -- the TLV walk, which is the
 * code this project actually wrote and the code CVE-2024-21778's shape lives in,
 * is unreachable.
 *
 * So each input is parsed twice:
 *
 *   pass 1  as-is.          Exercises the CRC, magic, format and seq refusals.
 *   pass 2  CRCs repaired.  The header CRC is recomputed over bytes 0..19, and
 *           the payload CRC over the payload the header claims -- but ONLY when
 *           that payload is inside the file, so the "payload length past the
 *           bytes we hold" refusal stays reachable.  This pass is where the TLV
 *           walk, the schema checks and the cross-field rules get fuzzed.
 *
 * WHAT THIS MEANS FOR THE RESULT, stated because it is a real limitation: pass 2
 * makes the CRC gate vacuous, so NOTHING the fuzzer reports is evidence about
 * the CRCs.  The CRCs are covered instead by the exhaustive sweeps in
 * test_cfg.c -- every single-bit flip and every single-byte change inside a
 * record's extent -- which is a better instrument for that property than random
 * mutation could be.
 *
 * ---------------------------------------------------------------------------
 * THE BUFFER IS EXACTLY THE INPUT'S SIZE, AND THAT IS THE POINT
 * ---------------------------------------------------------------------------
 *
 * The bytes are copied into a malloc of exactly n (or 1 byte when n is 0)
 * before parsing.  A static 8 KiB array would absorb an off-by-one read
 * silently: the byte past a 131-byte record would still be inside the array,
 * and the fuzzer would find nothing to report.  With an exact-size heap buffer
 * and AFL_USE_ASAN=1, one byte past the record is a heap-buffer-overflow and
 * the run stops.  Build it any other way and a planted off-by-one goes
 * undetected -- which is exactly the thing the planted-defect run checks.
 *
 * ---------------------------------------------------------------------------
 * THE ORACLE
 * ---------------------------------------------------------------------------
 *
 * A crash or a sanitizer report is a finding.  So is a broken round trip: any
 * record cfg_parse_record ACCEPTS must re-encode and re-parse to the same
 * configuration, because the encoder and the decoder disagreeing means one of
 * them accepts something the other cannot represent.  abort() is used so that
 * the fuzzer counts it.
 *
 * FUZZ_CFG_PRINT=1 prints the return code of each pass, for tallying which
 * refusals a corpus actually reaches.  It changes nothing else.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cfg.h"
#include "crc32.h"
#include "tlv.h"

#define FUZZ_MAX (2 * CFG_SLOT_SIZE)	/* a whole two-slot store, at most */

static int g_print;

static int same(const struct cfg *a, const struct cfg *b)
{
	int i;

	if (a->seq != b->seq)
		return 0;
	for (i = 0; i < CFG_NKEYS; i++) {
		if (a->present[i] != b->present[i])
			return 0;
		if (!a->present[i])
			continue;
		if (a->len[i] != b->len[i])
			return 0;
		if (memcmp(a->val[i], b->val[i], (size_t)a->len[i]) != 0)
			return 0;
	}
	return 1;
}

static void one(const uint8_t *data, size_t n, int repair)
{
	uint8_t *m = (uint8_t *)malloc(n ? n : 1);
	struct cfg c;
	int rc;

	if (m == NULL)
		return;
	if (n != 0)
		memcpy(m, data, n);

	if (repair && n >= (size_t)CFG_HDR_LEN) {
		uint32_t paylen = tlv_get_be32(m + 12);

		if ((size_t)paylen <= n - (size_t)CFG_HDR_LEN)
			tlv_put_be32(m + 16,
				     crc32_ieee(0, m + CFG_HDR_LEN,
						(size_t)paylen));
		tlv_put_be32(m + 20, crc32_ieee(0, m, 20));
	}

	rc = cfg_parse_record(m, n, &c);
	if (g_print)
		printf("pass%d rc=%d key=0x%04X\n", repair ? 2 : 1, rc,
		       (unsigned)cfg_last_key());

	if (rc == 0) {
		uint8_t img[CFG_SLOT_SIZE];
		struct cfg d;
		int used;

		/* An accepted record must round-trip.  c.seq is in
		 * [1, 0xFFFFFFFE] because cfg_parse_record checked it. */
		used = cfg_slot_image(&c, c.seq, img, sizeof img);
		if (used <= 0) {
			fprintf(stderr, "ORACLE: accepted a record that will not"
				" re-encode (%d)\n", used);
			abort();
		}
		if (cfg_parse_record(img, sizeof img, &d) != 0) {
			fprintf(stderr, "ORACLE: re-encoded record does not"
				" parse\n");
			abort();
		}
		if (!same(&c, &d)) {
			fprintf(stderr, "ORACLE: round trip changed the"
				" configuration\n");
			abort();
		}
		if (cfg_validate(&c) != 0) {
			fprintf(stderr, "ORACLE: an accepted record fails the"
				" cross-field rules\n");
			abort();
		}
	}
	free(m);
}

int main(int argc, char **argv)
{
	static uint8_t buf[FUZZ_MAX];
	FILE *f;
	size_t n;

	if (argc < 2) {
		fputs("usage: fuzz_cfg <file>\n", stderr);
		return 1;
	}
	g_print = (getenv("FUZZ_CFG_PRINT") != NULL);

	f = fopen(argv[1], "rb");
	if (f == NULL)
		return 1;
	n = fread(buf, 1, sizeof buf, f);
	fclose(f);

	one(buf, n, 0);
	one(buf, n, 1);
	return 0;
}
