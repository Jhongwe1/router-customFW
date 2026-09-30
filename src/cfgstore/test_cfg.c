/* test_cfg.c -- the record, the two-slot store, and the two sweeps that are the
 * A/B design's actual claim.
 *
 * ---------------------------------------------------------------------------
 * THE TORN-WRITE SWEEP, AND WHY ITS CLAIM IS NOT THE OBVIOUS ONE
 * ---------------------------------------------------------------------------
 *
 * The assignment asked for: "for a store holding record N, for EVERY truncation
 * length 0..4096 of the new slot image, cfg_load must still select record N".
 * That is not satisfiable, and the reason is a property of the format rather
 * than a bug.  A full record is 131 bytes; the other 3,965 bytes of the slot
 * are 0xFF fill that the parser never examines.  So a "torn" write that got as
 * far as byte 131 has in fact written the WHOLE record, and selecting it is
 * correct.
 *
 * The invariant that is both true and worth having is stronger:
 *
 *     For every truncation length L in 0..4096, and for both possible previous
 *     contents of the target slot (erased, and an older record), the loaded
 *     configuration is byte-identical to record N or to record N+1 -- never a
 *     mixture, never a partial record, never a value that was in neither.
 *     And "N+1 was selected" implies L >= the record's extent.
 *
 * That is what is asserted below, with the counts of each outcome printed.  The
 * L == 4096 case is the positive control: without it, a sweep that always
 * answered "N" could be passing because slot 1 is never selectable at all.
 *
 * ---------------------------------------------------------------------------
 * WHAT THE BIT-FLIP SWEEP MEASURES
 * ---------------------------------------------------------------------------
 *
 * Every single-bit flip inside the record's extent is REJECTED, not merely
 * "rejected or still self-consistent": the header CRC covers bytes 0..19 (which
 * include the payload CRC field) and the payload CRC covers the payload, and a
 * CRC-32 detects every single-bit and every single-byte error by construction.
 * Flips in the fill region are accepted and must leave every value unchanged --
 * that direction is asserted too, because "everything is rejected" would also
 * be passed by a parser that rejects everything.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cfg.h"
#include "crc32.h"
#include "schema.h"
#include "test_util.h"
#include "tlv.h"

#define SCRATCH_MAX 512

static char g_file[SCRATCH_MAX];

static void base_cfg(struct cfg *c)
{
	int i;

	cfg_defaults(c);
	for (i = 0; i < CFG_NKEYS; i++) {
		const uint8_t *dv;
		uint16_t dl;

		if (schema_default(cfg_keys[i].id, &dv, &dl) == 0)
			cfg_set(c, cfg_keys[i].id, dv, dl);
	}
}

static int cfg_same(const struct cfg *a, const struct cfg *b)
{
	int i;

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

static int write_file(const char *path, const uint8_t *buf, size_t n)
{
	FILE *f = fopen(path, "wb");
	size_t w;

	if (f == NULL)
		return -1;
	w = fwrite(buf, 1, n, f);
	if (fclose(f) != 0)
		return -1;
	return (w == n) ? 0 : -1;
}

static long file_size(const char *path)
{
	FILE *f = fopen(path, "rb");
	long n;

	if (f == NULL)
		return -1;
	if (fseek(f, 0, SEEK_END) != 0) {
		fclose(f);
		return -1;
	}
	n = ftell(f);
	fclose(f);
	return n;
}

/* ------------------------------------------------------------------------- */

static void t_encode_decode(void)
{
	struct cfg a, b;
	uint8_t rec[CFG_SLOT_SIZE];
	int used, rc;

	T_GROUP("encode/decode");
	base_cfg(&a);
	used = cfg_encode_record(&a, 7, rec, sizeof rec);
	CHECK(used > 0, "encode: %s", cfg_strerror(used));
	if (used <= 0)
		return;
	printf("  full default record: %d bytes (%d header + %d payload)\n",
	       used, CFG_HDR_LEN, used - CFG_HDR_LEN);

	/* The largest record the schema can produce, measured rather than
	 * counted by hand: every variable-length key at its maximum length and
	 * admin.pwhash present.  notes/config-store.md quotes this number. */
	{
		struct cfg m;
		uint8_t big[CFG_SLOT_SIZE];
		uint8_t v[CFG_VAL_MAX];
		int j, mx;

		base_cfg(&m);
		memset(v, 'a', sizeof v);
		CHECK(cfg_set(&m, CFG_ID_HOSTNAME, v, CFG_HOSTNAME_MAX) == 0,
		      "a 32-byte hostname");
		memset(v, 0x5A, sizeof v);
		v[0] = 1;
		CHECK(cfg_set(&m, CFG_ID_PWHASH, v, CFG_PWHASH_LEN) == 0,
		      "a 56-byte pwhash");
		for (j = 0; j < CFG_NKEYS; j++)
			CHECK(m.present[j] == 1, "%s must be present in the"
			      " maximal record", cfg_keys[j].name);
		mx = cfg_encode_record(&m, CFG_SEQ_MAX, big, sizeof big);
		CHECK(mx > 0, "maximal encode: %s", cfg_strerror(mx));
		printf("  maximal record: %d bytes (%d payload), %d%% of a"
		       " %d-byte slot\n", mx, mx - CFG_HDR_LEN,
		       (mx * 100) / CFG_SLOT_SIZE, CFG_SLOT_SIZE);
		CHECK(mx < CFG_SLOT_SIZE,
		      "the maximal record must fit a slot: %d of %d", mx,
		      CFG_SLOT_SIZE);
		CHECK(cfg_parse_record(big, (size_t)mx, &b) == 0,
		      "and it must parse");
	}

	/* The header, field by field, read back as bytes -- not through the
	 * encoder's own accessors on a struct it also wrote. */
	CHECK(rec[0] == 0x52 && rec[1] == 0x4C && rec[2] == 0x58 &&
	      rec[3] == 0x43, "magic is not the ASCII bytes RLXC");
	CHECK(rec[4] == 0 && rec[5] == 1, "format must be 0x0001 big-endian");
	CHECK(rec[6] == 0 && rec[7] == 24, "header length must be 0x0018");
	CHECK(rec[8] == 0 && rec[9] == 0 && rec[10] == 0 && rec[11] == 7,
	      "seq 7 must be 00 00 00 07 big-endian");
	CHECK(tlv_get_be32(rec + 12) == (uint32_t)(used - CFG_HDR_LEN),
	      "payload length field");
	CHECK(tlv_get_be32(rec + 16) ==
	      crc32_ieee(0, rec + CFG_HDR_LEN, (size_t)used - CFG_HDR_LEN),
	      "payload CRC field");
	CHECK(tlv_get_be32(rec + 20) == crc32_ieee(0, rec, 20),
	      "header CRC field");

	/* The payload's first TLV must be the lowest id, encoded big-endian. */
	CHECK(tlv_get_be16(rec + CFG_HDR_LEN) == CFG_ID_HOSTNAME,
	      "the first TLV must be id 0x0001, got 0x%04X",
	      (unsigned)tlv_get_be16(rec + CFG_HDR_LEN));

	rc = cfg_parse_record(rec, (size_t)used, &b);
	CHECK(rc == 0, "parse: %s", cfg_strerror(rc));
	CHECK(b.seq == 7, "seq survived: %lu", (unsigned long)b.seq);
	CHECK(cfg_same(&a, &b), "round trip changed a value");

	/* Parsing the whole 4096-byte slot must give the same answer: the fill
	 * is past the record's extent and must not be examined. */
	{
		uint8_t img[CFG_SLOT_SIZE];
		struct cfg d;

		CHECK(cfg_slot_image(&a, 7, img, sizeof img) == used,
		      "slot image length");
		CHECK(memcmp(img, rec, (size_t)used) == 0,
		      "the slot image must start with the record");
		CHECK(img[used] == 0xFF && img[CFG_SLOT_SIZE - 1] == 0xFF,
		      "the slot image must be 0xFF past the record");
		CHECK(cfg_parse_record(img, sizeof img, &d) == 0,
		      "parsing a whole slot");
		CHECK(cfg_same(&a, &d) && d.seq == 7, "same answer as the extent");
	}

	/* An empty payload is a valid record, and every key then defaults. */
	{
		struct cfg e, f;
		int n;

		cfg_defaults(&e);
		n = cfg_encode_record(&e, 1, rec, sizeof rec);
		CHECK(n == CFG_HDR_LEN, "an all-absent cfg is a bare header: %d",
		      n);
		CHECK(cfg_parse_record(rec, (size_t)n, &f) == 0,
		      "a bare header parses");
		CHECK(cfg_same(&e, &f), "and yields an all-absent cfg");
	}

	T_GROUP("encode refusals");
	CHECK(cfg_encode_record(&a, 0, rec, sizeof rec) == -CFGE_SEQ,
	      "seq 0 must be refused on encode");
	CHECK(cfg_encode_record(&a, 0xFFFFFFFFu, rec, sizeof rec) == -CFGE_SEQ,
	      "seq 0xFFFFFFFF must be refused on encode");
	CHECK(cfg_encode_record(&a, 1, rec, 23) == -CFGE_SPACE,
	      "23 bytes cannot hold a header");
	CHECK(cfg_encode_record(&a, 1, rec, CFG_HDR_LEN) == -CFGE_SPACE,
	      "a header with no room for the payload must be refused");
}

/* ------------------------------------------------------------------------- */

static void t_header_refusals(void)
{
	struct cfg a, out;
	uint8_t rec[CFG_SLOT_SIZE];
	int used, i;

	T_GROUP("header refusals");
	base_cfg(&a);
	used = cfg_encode_record(&a, 9, rec, sizeof rec);
	if (used <= 0)
		return;

	/* short buffers */
	for (i = 0; i < CFG_HDR_LEN; i++) {
		CHECK(cfg_parse_record(rec, (size_t)i, &out) == -CFGE_SHORT,
		      "%d bytes must be -CFGE_SHORT", i);
	}

#define MUT(stmt, wantrc, what)						\
	do {								\
		uint8_t m[CFG_SLOT_SIZE];				\
		int rc_;						\
									\
		memcpy(m, rec, (size_t)used);				\
		stmt;							\
		/* repair the header CRC so the mutation itself is what	\
		 * is being tested, not the CRC that covers it */	\
		tlv_put_be32(m + 20, crc32_ieee(0, m, 20));		\
		rc_ = cfg_parse_record(m, (size_t)used, &out);		\
		CHECK(rc_ == (wantrc), "%s: rc=%d (%s), want %d (%s)",	\
		      what, rc_, cfg_strerror(rc_), (wantrc),		\
		      cfg_strerror(wantrc));				\
	} while (0)

	MUT(m[0] = 'X', -CFGE_MAGIC, "wrong magic");
	MUT(tlv_put_be16(m + 4, 2), -CFGE_FORMAT, "format 2");
	MUT(tlv_put_be16(m + 4, 0), -CFGE_FORMAT, "format 0");
	MUT(tlv_put_be16(m + 6, 20), -CFGE_FORMAT, "header length 20");
	MUT(tlv_put_be16(m + 6, 28), -CFGE_FORMAT, "header length 28");
	MUT(tlv_put_be32(m + 8, 0), -CFGE_SEQ, "seq 0");
	MUT(tlv_put_be32(m + 8, 0xFFFFFFFFu), -CFGE_SEQ, "seq 0xFFFFFFFF");
	MUT(tlv_put_be32(m + 12, CFG_SLOT_SIZE - CFG_HDR_LEN + 1), -CFGE_LEN,
	    "payload length one past the slot");
	MUT(tlv_put_be32(m + 12, 0xFFFFFFFFu), -CFGE_LEN,
	    "payload length 0xFFFFFFFF");
	MUT(tlv_put_be32(m + 12, (uint32_t)(used - CFG_HDR_LEN + 1)),
	    -CFGE_SHORT, "payload length one past the bytes we hold");
	MUT(tlv_put_be32(m + 16, 0), -CFGE_CRC, "zeroed payload CRC");
	MUT(m[CFG_HDR_LEN] ^= 0x01, -CFGE_CRC, "a flipped payload bit");

#undef MUT

	/* and the header CRC itself, with no repair */
	{
		uint8_t m[CFG_SLOT_SIZE];

		memcpy(m, rec, (size_t)used);
		m[20] ^= 0x01;
		CHECK(cfg_parse_record(m, (size_t)used, &out) == -CFGE_CRC,
		      "a flipped header CRC bit must be -CFGE_CRC");
		memcpy(m, rec, (size_t)used);
		m[8] ^= 0x01;	/* seq changed, header CRC not repaired */
		CHECK(cfg_parse_record(m, (size_t)used, &out) == -CFGE_CRC,
		      "a changed seq without a repaired CRC is a CRC failure");
	}

	T_GROUP("an erased or zeroed slot is never valid");
	{
		uint8_t img[CFG_SLOT_SIZE];

		memset(img, 0xFF, sizeof img);
		CHECK(cfg_parse_record(img, sizeof img, &out) == -CFGE_CRC,
		      "an erased slot must be refused");
		memset(img, 0x00, sizeof img);
		CHECK(cfg_parse_record(img, sizeof img, &out) == -CFGE_CRC,
		      "a zeroed slot must be refused");
		/* and with a VALID header CRC over all-zero bytes, seq 0 still
		 * refuses it -- the belt to the CRC's braces */
		memset(img, 0x00, sizeof img);
		tlv_put_be32(img + 0, CFG_MAGIC);
		tlv_put_be16(img + 4, 1);
		tlv_put_be16(img + 6, 24);
		tlv_put_be32(img + 16, crc32_ieee(0, img + 24, 0));
		tlv_put_be32(img + 20, crc32_ieee(0, img, 20));
		CHECK(cfg_parse_record(img, sizeof img, &out) == -CFGE_SEQ,
		      "a well-formed record with seq 0 must be -CFGE_SEQ");
	}
}

/* ------------------------------------------------------------------------- */
/* Payload refusals, on exact-size heap buffers so that a weakened length check
 * is a heap overflow that address sanitizer reports as well as a wrong answer. */

static void payload_case(uint16_t seq, const uint8_t *pay, size_t paylen,
			 int wantrc, uint16_t wantkey, const char *what)
{
	uint8_t *buf = malloc((size_t)CFG_HDR_LEN + paylen);
	struct cfg out;
	int rc;

	if (buf == NULL) {
		CHECK(0, "malloc");
		return;
	}
	tlv_put_be32(buf + 0, CFG_MAGIC);
	tlv_put_be16(buf + 4, (uint16_t)CFG_FORMAT);
	tlv_put_be16(buf + 6, (uint16_t)CFG_HDR_LEN);
	tlv_put_be32(buf + 8, seq);
	tlv_put_be32(buf + 12, (uint32_t)paylen);
	if (paylen != 0)
		memcpy(buf + CFG_HDR_LEN, pay, paylen);
	tlv_put_be32(buf + 16, crc32_ieee(0, buf + CFG_HDR_LEN, paylen));
	tlv_put_be32(buf + 20, crc32_ieee(0, buf, 20));

	rc = cfg_parse_record(buf, (size_t)CFG_HDR_LEN + paylen, &out);
	CHECK(rc == wantrc, "%s: rc=%d (%s), want %d (%s)", what, rc,
	      cfg_strerror(rc), wantrc, cfg_strerror(wantrc));
	if (wantkey != 0 && rc == wantrc)
		CHECK(cfg_last_key() == wantkey, "%s: blamed 0x%04X, want 0x%04X",
		      what, (unsigned)cfg_last_key(), (unsigned)wantkey);
	free(buf);
}

static void t_payload_refusals(void)
{
	T_GROUP("payload refusals");

	/* unknown id */
	{
		static const uint8_t p[] = { 0x02, 0x99, 0x00, 0x01, 0x00 };

		payload_case(3, p, sizeof p, -CFGE_UNKNOWN, 0x0299, "unknown id");
	}
	/* wrong length for the type: dhcpd.enable (BOOL) with 2 bytes */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x02, 0x01, 0x00 };

		payload_case(3, p, sizeof p, -CFGE_TYPE, CFG_ID_DHCPD_EN,
			     "BOOL with 2 bytes");
	}
	/* out-of-bounds value: dhcpd.enable = 2 */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x01, 0x02 };

		payload_case(3, p, sizeof p, -CFGE_RANGE, CFG_ID_DHCPD_EN,
			     "BOOL = 2");
	}
	/* out-of-bounds value: http.port = 0 */
	{
		static const uint8_t p[] = { 0x00, 0x60, 0x00, 0x02, 0x00, 0x00 };

		payload_case(3, p, sizeof p, -CFGE_RANGE, CFG_ID_HTTP_PORT,
			     "http.port = 0");
	}
	/* a length past the payload */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x08, 0x01 };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0,
			     "a TLV length past the payload");
	}
	/* a length past the payload, at the 16-bit maximum */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0xFF, 0xFF, 0x01 };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0, "TLV length 65535");
	}
	/* A length past the payload on a VARIABLE-length type.  Measured while
	 * running the mutation control: with the TLV bound removed, the two
	 * cases above are still caught -- by the TYPE's length check, since
	 * BOOL is one byte and 8 is not.  A hostname is 1..32 bytes, so 8 is a
	 * legal length and only the TLV reader's bound stands between the
	 * parser and a read past the payload.  This case is therefore a heap
	 * overflow under that mutation, and the sanitizer says so. */
	{
		static const uint8_t p[] = { 0x00, 0x01, 0x00, 0x08, 'a', 'b' };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0,
			     "a hostname claiming 8 bytes of a 2-byte tail");
	}
	/* Exactly ONE byte too many, on a variable-length type.  The case above
	 * is the missing-check shape; this is the OFF-BY-ONE shape, and the two
	 * are caught by different mutants: `> avail - 4 + 1` still refuses a
	 * length six bytes too long and accepts this one.  Both are here because
	 * a suite that only has the first would call an off-by-one clean at the
	 * record layer. */
	{
		static const uint8_t p[] = { 0x00, 0x01, 0x00, 0x03, 'a', 'b' };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0,
			     "a hostname claiming 3 bytes of a 2-byte tail");
	}
	/* trailing bytes: one complete TLV then three loose bytes */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x01, 0x01,
					     0xAA, 0xBB, 0xCC };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0, "trailing bytes");
	}
	/* a partial header at the end */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x01, 0x01, 0x00 };

		payload_case(3, p, sizeof p, -CFGE_TLV, 0, "one trailing byte");
	}
	/* duplicate ids */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x01, 0x01,
					     0x00, 0x20, 0x00, 0x01, 0x00 };

		payload_case(3, p, sizeof p, -CFGE_ORDER, 0, "duplicate id");
	}
	/* descending ids */
	{
		static const uint8_t p[] = { 0x00, 0x50, 0x00, 0x01, 0x01,
					     0x00, 0x20, 0x00, 0x01, 0x01 };

		payload_case(3, p, sizeof p, -CFGE_ORDER, 0, "descending ids");
	}
	/* ascending is accepted -- the control on the two above */
	{
		static const uint8_t p[] = { 0x00, 0x20, 0x00, 0x01, 0x01,
					     0x00, 0x50, 0x00, 0x01, 0x01 };

		payload_case(3, p, sizeof p, 0, 0, "ascending ids");
	}
	/* a cross-field violation carried in a record: pool outside the LAN */
	{
		static const uint8_t p[] = {
			0x00, 0x10, 0x00, 0x04, 10, 1, 1, 1,	  /* lan.ipaddr */
			0x00, 0x11, 0x00, 0x04, 255, 255, 255, 0, /* lan.netmask */
			0x00, 0x21, 0x00, 0x04, 10, 9, 9, 100,	  /* dhcpd.start */
			0x00, 0x22, 0x00, 0x04, 10, 9, 9, 199	  /* dhcpd.end */
		};

		payload_case(3, p, sizeof p, -CFGE_CROSS, CFG_ID_DHCPD_START,
			     "a record whose pool is off-subnet");
	}
	/* a STR carrying a NUL */
	{
		static const uint8_t p[] = { 0x00, 0x01, 0x00, 0x03,
					     'a', 0x00, 'b' };

		payload_case(3, p, sizeof p, -CFGE_RANGE, CFG_ID_HOSTNAME,
			     "a hostname with an embedded NUL");
	}
	/* a BYTES of the wrong length */
	{
		static uint8_t p[4 + 55];

		tlv_put_be16(p, CFG_ID_PWHASH);
		tlv_put_be16(p + 2, 55);
		memset(p + 4, 0xA5, 55);
		payload_case(3, p, sizeof p, -CFGE_TYPE, CFG_ID_PWHASH,
			     "a 55-byte pwhash");
	}
	/* a value longer than CFG_VAL_MAX, which must never reach struct cfg */
	{
		static uint8_t p[4 + 200];

		tlv_put_be16(p, CFG_ID_HOSTNAME);
		tlv_put_be16(p + 2, 200);
		memset(p + 4, 'a', 200);
		payload_case(3, p, sizeof p, -CFGE_TYPE, CFG_ID_HOSTNAME,
			     "a 200-byte hostname");
	}
}

/* ------------------------------------------------------------------------- */

static void t_bitflip(void)
{
	struct cfg a, ref, out;
	uint8_t img[CFG_SLOT_SIZE];
	int used, i, bit;
	long rejected = 0, accepted_same = 0, accepted_diff = 0;

	T_GROUP("bit-flip sweep");
	base_cfg(&a);
	used = cfg_slot_image(&a, 12345, img, sizeof img);
	if (used <= 0) {
		CHECK(0, "slot image: %s", cfg_strerror(used));
		return;
	}
	CHECK(cfg_parse_record(img, sizeof img, &ref) == 0,
	      "the unmutated image must parse -- the control for this sweep");

	/* Inside the record's extent: every flip must be rejected.  Done on an
	 * exact-size heap copy so that a parser that walked past the record
	 * would be caught by the sanitizer as well as by the verdict. */
	for (i = 0; i < used; i++) {
		for (bit = 0; bit < 8; bit++) {
			uint8_t *m = malloc((size_t)used);
			int rc;

			if (m == NULL) {
				CHECK(0, "malloc");
				return;
			}
			memcpy(m, img, (size_t)used);
			m[i] ^= (uint8_t)(1u << bit);
			rc = cfg_parse_record(m, (size_t)used, &out);
			if (rc != 0) {
				rejected++;
			} else if (cfg_same(&ref, &out) && out.seq == ref.seq) {
				accepted_same++;
			} else {
				accepted_diff++;
				CHECK(0, "byte %d bit %d was ACCEPTED with"
				      " changed values", i, bit);
			}
			free(m);
		}
	}
	printf("  extent %d bytes: %ld flips rejected, %ld accepted unchanged,"
	       " %ld accepted CHANGED\n", used, rejected, accepted_same,
	       accepted_diff);
	CHECK(rejected == (long)used * 8,
	      "every flip in the extent must be rejected: %ld of %ld", rejected,
	      (long)used * 8);
	CHECK(accepted_diff == 0, "a flip changed a value silently");

	/* Outside the extent: the fill is not part of the record, so a flip
	 * there must be accepted AND must change nothing.  This is the other
	 * direction, without which "everything was rejected" proves nothing. */
	{
		long fill_ok = 0, fill_bad = 0;
		int off;

		for (off = used; off < used + 64 && off < CFG_SLOT_SIZE; off++) {
			for (bit = 0; bit < 8; bit++) {
				uint8_t m[CFG_SLOT_SIZE];
				int rc;

				memcpy(m, img, sizeof m);
				m[off] ^= (uint8_t)(1u << bit);
				rc = cfg_parse_record(m, sizeof m, &out);
				if (rc == 0 && cfg_same(&ref, &out) &&
				    out.seq == ref.seq)
					fill_ok++;
				else
					fill_bad++;
			}
		}
		printf("  fill region: %ld flips accepted unchanged, %ld not\n",
		       fill_ok, fill_bad);
		CHECK(fill_bad == 0, "a flip in the 0xFF fill changed the"
		      " parse: %ld cases", fill_bad);
		CHECK(fill_ok == 512, "the fill sweep must have run 512 cases,"
		      " ran %ld", fill_ok);
	}

	/* Every single-BYTE change in the extent, all 255 wrong values. */
	{
		long n = 0, bad = 0;
		int v;

		for (i = 0; i < used; i++) {
			uint8_t orig = img[i];

			for (v = 0; v < 256; v++) {
				uint8_t m[CFG_SLOT_SIZE];

				if ((uint8_t)v == orig)
					continue;
				memcpy(m, img, sizeof m);
				m[i] = (uint8_t)v;
				n++;
				if (cfg_parse_record(m, sizeof m, &out) == 0) {
					bad++;
					if (bad <= 4)
						CHECK(0, "byte %d := 0x%02X was"
						      " accepted", i, v);
				}
			}
		}
		printf("  single-byte sweep: %ld cases, %ld accepted\n", n, bad);
		CHECK(n == (long)used * 255, "the sweep must be exhaustive over"
		      " the extent: %ld of %ld", n, (long)used * 255);
		CHECK(bad == 0, "%ld single-byte corruptions were accepted", bad);
	}
}

/* ------------------------------------------------------------------------- */

static void t_torn(void)
{
	struct cfg old, new_, ref_old, ref_new, got;
	struct cfg_store_info info;
	uint8_t file[CFG_FILE_SIZE];
	uint8_t img_old[CFG_SLOT_SIZE], img_new[CFG_SLOT_SIZE];
	uint8_t img_older[CFG_SLOT_SIZE];
	int used_old, used_new, used_older, bg, rc;
	long sel_old = 0, sel_new = 0, sel_none = 0, early_new = 0, mixed = 0;
	long stale_intact = 0;
	int L, stale_max = -1;
	static const uint8_t h_old[] = { 'o', 'l', 'd' };
	static const uint8_t h_new[] = { 'n', 'e', 'w', 'e', 'r' };
	static const uint8_t h_older[] = { 'a', 'n', 'c', 'i', 'e', 'n', 't' };

	T_GROUP("torn write, exhaustive");

	base_cfg(&old);
	cfg_set(&old, CFG_ID_HOSTNAME, h_old, (uint16_t)sizeof h_old);
	base_cfg(&new_);
	cfg_set(&new_, CFG_ID_HOSTNAME, h_new, (uint16_t)sizeof h_new);

	used_old = cfg_slot_image(&old, 100, img_old, sizeof img_old);
	used_new = cfg_slot_image(&new_, 101, img_new, sizeof img_new);
	CHECK(used_old > 0 && used_new > 0, "images");
	if (used_old <= 0 || used_new <= 0)
		return;
	CHECK(cfg_parse_record(img_old, sizeof img_old, &ref_old) == 0, "ref old");
	CHECK(cfg_parse_record(img_new, sizeof img_new, &ref_new) == 0, "ref new");

	{
		struct cfg older;

		base_cfg(&older);
		cfg_set(&older, CFG_ID_HOSTNAME, h_older, (uint16_t)sizeof h_older);
		used_older = cfg_slot_image(&older, 99, img_older,
					    sizeof img_older);
		CHECK(used_older > 0, "older image");
	}

	/* bg 0: the target slot was erased (0xFF).   bg 1: it held record 99. */
	for (bg = 0; bg < 2; bg++) {
		for (L = 0; L <= CFG_SLOT_SIZE; L++) {
			memcpy(file, img_old, CFG_SLOT_SIZE);
			if (bg == 0)
				memset(file + CFG_SLOT_SIZE, 0xFF, CFG_SLOT_SIZE);
			else
				memcpy(file + CFG_SLOT_SIZE, img_older,
				       CFG_SLOT_SIZE);
			if (L > 0)
				memcpy(file + CFG_SLOT_SIZE, img_new, (size_t)L);

			if (write_file(g_file, file, sizeof file) != 0) {
				CHECK(0, "write %s", g_file);
				return;
			}
			rc = cfg_load_info(g_file, &got, &info);
			if (rc != 0) {
				CHECK(0, "bg=%d L=%d: load rc=%d", bg, L, rc);
				continue;
			}

			/* How often a prefix leaves the TARGET slot still
			 * holding the whole older record.  Counted rather than
			 * derived: notes/config-store.md quotes this number,
			 * and the reasoning behind it (the two records share
			 * their leading header bytes) is the kind that is
			 * self-consistent while being off by one. */
			if (bg == 1 && info.rc[1] == 0 && info.seq[1] == 99) {
				stale_intact++;
				if (L > stale_max)
					stale_max = L;
			}

			/* The invariant: whatever came back is one of the two
			 * complete records, byte for byte. */
			if (got.seq == 100 && cfg_same(&got, &ref_old)) {
				sel_old++;
				CHECK(info.selected == 1, "bg=%d L=%d: record"
				      " 100 must come from slot 0", bg, L);
			} else if (got.seq == 101 && cfg_same(&got, &ref_new)) {
				sel_new++;
				CHECK(L >= used_new, "bg=%d L=%d: record 101"
				      " selected although only %d of %d bytes"
				      " landed", bg, L, L, used_new);
				if (L < used_new)
					early_new++;
			} else if (got.source == 0) {
				sel_none++;
				CHECK(0, "bg=%d L=%d: fell back to defaults"
				      " although slot 0 holds record 100", bg, L);
			} else {
				mixed++;
				CHECK(0, "bg=%d L=%d: loaded a record that is"
				      " neither 100 nor 101 (seq %lu, slot %d)",
				      bg, L, (unsigned long)got.seq, got.source);
			}
		}
	}

	printf("  torn-write sweep: %ld cases over 2 backgrounds x %d lengths\n",
	       sel_old + sel_new + sel_none + mixed, CFG_SLOT_SIZE + 1);
	printf("    record N (seq 100) selected : %ld\n", sel_old);
	printf("    record N+1 (seq 101), complete and >= %d bytes : %ld\n",
	       used_new, sel_new);
	printf("    a mixture, a partial record or a fallback : %ld\n",
	       sel_none + mixed);
	printf("    background (b): prefix left the OLD record (seq 99) intact"
	       " in %ld cases, longest L = %d\n", stale_intact, stale_max);
	CHECK(stale_intact > 0,
	      "a prefix short enough to leave the older record intact must"
	      " occur, or that half of the sweep tests nothing");
	CHECK(sel_none + mixed == 0, "every case must load a complete record");
	CHECK(early_new == 0, "record N+1 was selected before it was complete");
	/* Positive controls: the sweep reached BOTH outcomes, so it is not
	 * passing because slot 1 can never be selected (which would make the
	 * whole sweep vacuous) nor because it is always selected. */
	CHECK(sel_old > 0, "the sweep never selected record N");
	CHECK(sel_new > 0, "the sweep never selected record N+1: slot 1 may be"
	      " unselectable, which would make every other case vacuous");
	/* And the exact boundary: N+1 wins from its own length onwards. */
	CHECK(sel_new == 2 * (CFG_SLOT_SIZE + 1 - used_new),
	      "N+1 should win for L in [%d, %d] on both backgrounds: %ld",
	      used_new, CFG_SLOT_SIZE, sel_new);
}

/* ------------------------------------------------------------------------- */

static void t_store(void)
{
	struct cfg a, b;
	struct cfg_store_info info;
	uint8_t file[CFG_FILE_SIZE];
	uint8_t before[CFG_SLOT_SIZE];
	FILE *f;
	int rc, i;
	static const uint8_t h[] = { 'x', 'y' };

	T_GROUP("store: fresh file");
	remove(g_file);
	base_cfg(&a);
	rc = cfg_store(g_file, &a);
	CHECK(rc == 0, "first store: %s", cfg_strerror(rc));
	CHECK(a.seq == 1, "the first record must be seq 1, got %lu",
	      (unsigned long)a.seq);
	CHECK(a.source == 1, "the first record goes to slot 0, got %d", a.source);
	CHECK(file_size(g_file) == (long)CFG_FILE_SIZE,
	      "the store must be %d bytes, is %ld", CFG_FILE_SIZE,
	      file_size(g_file));

	rc = cfg_load_info(g_file, &b, &info);
	CHECK(rc == 0 && info.selected == 1, "load back: rc=%d selected=%d", rc,
	      info.selected);
	CHECK(b.seq == 1 && cfg_same(&a, &b), "the record survived the file");

	T_GROUP("store: alternation and seq");
	for (i = 2; i <= 9; i++) {
		int want_slot = ((i - 1) % 2 == 0) ? 1 : 2;

		/* Read the slot we expect NOT to be written, before the write. */
		f = fopen(g_file, "rb");
		CHECK(f != NULL, "open for pre-read");
		if (f == NULL)
			return;
		if (fseek(f, (long)(want_slot == 1 ? CFG_SLOT_SIZE : 0),
			  SEEK_SET) != 0)
			CHECK(0, "seek");
		CHECK(fread(before, 1, sizeof before, f) == sizeof before,
		      "pre-read");
		fclose(f);

		rc = cfg_store(g_file, &b);
		CHECK(rc == 0, "store %d: %s", i, cfg_strerror(rc));
		CHECK(b.seq == (uint32_t)i, "seq must be %d, is %lu", i,
		      (unsigned long)b.seq);
		CHECK(b.source == want_slot, "store %d must go to slot %d, went"
		      " to %d", i, want_slot - 1, b.source - 1);

		/* The other slot must be byte-identical to before the write. */
		f = fopen(g_file, "rb");
		if (f == NULL) {
			CHECK(0, "reopen");
			return;
		}
		if (fseek(f, (long)(want_slot == 1 ? CFG_SLOT_SIZE : 0),
			  SEEK_SET) != 0)
			CHECK(0, "seek");
		CHECK(fread(file, 1, sizeof before, f) == sizeof before,
		      "post-read");
		fclose(f);
		CHECK(memcmp(before, file, sizeof before) == 0,
		      "store %d touched the other slot", i);
	}

	T_GROUP("store: the value changes");
	cfg_set(&b, CFG_ID_HOSTNAME, h, (uint16_t)sizeof h);
	rc = cfg_store(g_file, &b);
	CHECK(rc == 0, "store a changed hostname: %s", cfg_strerror(rc));
	{
		struct cfg c;
		uint8_t v[CFG_VAL_MAX];
		uint16_t len = 0;

		CHECK(cfg_load(g_file, &c) == 0, "reload");
		CHECK(cfg_get(&c, CFG_ID_HOSTNAME, v, &len) == 0, "get hostname");
		CHECK(len == 2 && v[0] == 'x' && v[1] == 'y',
		      "the new hostname must come back, got %u bytes", len);
	}

	T_GROUP("store: an invalid cfg is refused, and nothing is written");
	{
		struct cfg bad;
		uint8_t ip[4];
		long before_size = file_size(g_file);
		uint8_t snap[CFG_FILE_SIZE];
		size_t got;

		f = fopen(g_file, "rb");
		got = (f != NULL) ? fread(snap, 1, sizeof snap, f) : 0;
		if (f != NULL)
			fclose(f);
		CHECK(got == sizeof snap, "snapshot");

		base_cfg(&bad);
		ip[0] = 10; ip[1] = 1; ip[2] = 1; ip[3] = 150;
		CHECK(cfg_set(&bad, CFG_ID_LAN_IP, ip, 4) == 0,
		      "the field rules allow 10.1.1.150");
		rc = cfg_store(g_file, &bad);
		CHECK(rc == -CFGE_CROSS, "store must refuse it: %s",
		      cfg_strerror(rc));
		CHECK(file_size(g_file) == before_size, "the file changed size");
		f = fopen(g_file, "rb");
		if (f != NULL) {
			CHECK(fread(file, 1, sizeof file, f) == sizeof file,
			      "re-read");
			fclose(f);
			CHECK(memcmp(snap, file, sizeof file) == 0,
			      "a refused store wrote bytes");
		}
	}

	T_GROUP("fail-closed: both slots invalid");
	{
		struct cfg c;
		uint8_t v[CFG_VAL_MAX];
		uint16_t len = 0;

		memset(file, 0xFF, sizeof file);
		CHECK(write_file(g_file, file, sizeof file) == 0, "erased store");
		CHECK(cfg_load_info(g_file, &c, &info) == 0, "load an erased store");
		CHECK(info.selected == 0, "selected must be 0, is %d",
		      info.selected);
		CHECK(c.source == 0, "source must be 0, is %d", c.source);
		CHECK(c.seq == 0, "seq must be 0, is %lu", (unsigned long)c.seq);
		CHECK(info.file_bytes == (size_t)CFG_FILE_SIZE,
		      "and the caller can still see the file is there: %lu",
		      (unsigned long)info.file_bytes);
		CHECK(cfg_get(&c, CFG_ID_PWHASH, v, &len) == -CFGE_NOENT,
		      "no admin.pwhash, so no login is possible");
		CHECK(cfg_get(&c, CFG_ID_LAN_IP, v, &len) == 0 && len == 4 &&
		      v[0] == 10 && v[1] == 1 && v[2] == 1 && v[3] == 1,
		      "and every other key is its default");

		/* random bytes, not just 0xFF */
		for (i = 0; i < (int)sizeof file; i++)
			file[i] = (uint8_t)((i * 131 + 7) & 0xFF);
		CHECK(write_file(g_file, file, sizeof file) == 0, "noise store");
		CHECK(cfg_load_info(g_file, &c, &info) == 0, "load noise");
		CHECK(info.selected == 0, "noise must not be selected");
		CHECK(c.source == 0, "noise -> defaults");

		/* after both slots are invalid, a store goes to slot 0 */
		base_cfg(&a);
		CHECK(cfg_store(g_file, &a) == 0, "store over a broken store");
		CHECK(a.source == 1 && a.seq == 1,
		      "both invalid -> slot 0, seq 1: slot=%d seq=%lu",
		      a.source - 1, (unsigned long)a.seq);
	}

	T_GROUP("absent store");
	{
		struct cfg c;
		char missing[SCRATCH_MAX + 32];

		snprintf(missing, sizeof missing, "%s.nope", g_file);
		remove(missing);
		CHECK(cfg_load_info(missing, &c, &info) == 0,
		      "an absent store must not be an error");
		CHECK(info.selected == 0 && c.source == 0, "defaults");
		CHECK(info.file_bytes == 0,
		      "and 0 bytes, which is how a caller tells absent from"
		      " corrupt");
	}

	T_GROUP("short store");
	{
		struct cfg c;

		/* only slot 0, and it is valid */
		base_cfg(&a);
		CHECK(cfg_slot_image(&a, 42, file, CFG_SLOT_SIZE) > 0, "image");
		CHECK(write_file(g_file, file, CFG_SLOT_SIZE) == 0, "half store");
		CHECK(cfg_load_info(g_file, &c, &info) == 0, "load a half store");
		CHECK(info.selected == 1 && c.seq == 42,
		      "slot 0 must still be read: selected=%d seq=%lu",
		      info.selected, (unsigned long)c.seq);
		CHECK(cfg_store(g_file, &c) == 0, "store extends the file");
		CHECK(file_size(g_file) == (long)CFG_FILE_SIZE,
		      "and the file is now %d bytes: %ld", CFG_FILE_SIZE,
		      file_size(g_file));
		CHECK(c.seq == 43 && c.source == 2,
		      "the new record goes to slot 1 with seq 43: seq=%lu slot=%d",
		      (unsigned long)c.seq, c.source - 1);
	}

	T_GROUP("seq exhaustion");
	{
		struct cfg c;

		base_cfg(&a);
		CHECK(cfg_slot_image(&a, CFG_SEQ_MAX, file, CFG_SLOT_SIZE) > 0,
		      "image at the last usable seq");
		memset(file + CFG_SLOT_SIZE, 0xFF, CFG_SLOT_SIZE);
		CHECK(write_file(g_file, file, CFG_FILE_SIZE) == 0, "write");
		CHECK(cfg_load(g_file, &c) == 0, "load");
		CHECK(c.seq == CFG_SEQ_MAX, "seq is the maximum");
		CHECK(cfg_store(g_file, &c) == -CFGE_SEQ,
		      "a store past the last usable seq must refuse, not wrap");
	}

	remove(g_file);
}

/* ------------------------------------------------------------------------- */

int main(int argc, char **argv)
{
	const char *dir = (argc > 1) ? argv[1] : ".";
	int rc;

	rc = schema_self_check();
	if (rc != 0) {
		printf("FAIL schema_self_check: %s\n", cfg_strerror(rc));
		return 1;
	}
	snprintf(g_file, sizeof g_file, "%s/test_cfg_store.bin", dir);
	printf("  scratch store: %s\n", g_file);

	t_encode_decode();
	t_header_refusals();
	t_payload_refusals();
	t_bitflip();
	t_torn();
	t_store();

	return t_done("cfg");
}
