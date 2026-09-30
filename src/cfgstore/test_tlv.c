/* test_tlv.c -- the bounded reader, written against the reader rather than
 * against the record: this is where the length check itself is the subject.
 *
 * ---------------------------------------------------------------------------
 * THE MUTATION CONTROL LIVES HERE
 * ---------------------------------------------------------------------------
 *
 * `exhaustive length` below is the case that must fail if tlv_next's bounds
 * check is weakened or removed.  It is exhaustive over the two numbers the
 * check compares: for every buffer length 4..40 and every declared value
 * length 0..64 (plus 0xFFFF), it asserts
 *
 *     accepted  <=>  declared_len <= buffer_len - 4
 *
 * and, when accepted, that value+len lands inside the buffer.  Both directions
 * are asserted: a reader that refused everything would pass a one-directional
 * test and break every record.
 *
 * The buffers are malloc'd at the exact size, so address sanitizer sees a read
 * past the end as a heap overflow rather than as a harmless walk into padding.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "test_util.h"
#include "tlv.h"

static void put_hdr(uint8_t *p, uint16_t type, uint16_t len)
{
	tlv_put_be16(p, type);
	tlv_put_be16(p + 2, len);
}

int main(void)
{
	struct tlv_reader r;
	struct tlv_writer w;
	uint16_t type, len;
	const uint8_t *val;
	uint8_t buf[64];
	int rc, i;

	T_GROUP("be accessors");
	{
		uint8_t b[4];

		tlv_put_be32(b, 0x01020304u);
		CHECK(b[0] == 1 && b[1] == 2 && b[2] == 3 && b[3] == 4,
		      "be32 put is not big-endian: %02x%02x%02x%02x",
		      b[0], b[1], b[2], b[3]);
		CHECK(tlv_get_be32(b) == 0x01020304u, "be32 round trip");
		tlv_put_be16(b, 0xABCDu);
		CHECK(b[0] == 0xAB && b[1] == 0xCD, "be16 put is not big-endian");
		CHECK(tlv_get_be16(b) == 0xABCDu, "be16 round trip");
	}

	T_GROUP("empty and partial headers");
	tlv_reader_init(&r, buf, 0);
	CHECK(tlv_next(&r, &type, &len, &val) == 1, "0 bytes must be a clean end");
	for (i = 1; i < 4; i++) {
		tlv_reader_init(&r, buf, (size_t)i);
		CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_TRUNC,
		      "%d byte(s) must be TRUNC, not a clean end", i);
	}

	T_GROUP("exact fit and one short");
	put_hdr(buf, 0x0010, 4);
	memset(buf + 4, 0xAA, 4);
	tlv_reader_init(&r, buf, 8);
	rc = tlv_next(&r, &type, &len, &val);
	CHECK(rc == 0 && type == 0x0010 && len == 4 && val == buf + 4,
	      "exact fit rc=%d type=%u len=%u", rc, type, len);
	CHECK(tlv_next(&r, &type, &len, &val) == 1, "then a clean end");
	tlv_reader_init(&r, buf, 7);
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_TRUNC,
	      "one byte short must be TRUNC");

	T_GROUP("hostile length");
	put_hdr(buf, 0x0001, 0xFFFF);
	tlv_reader_init(&r, buf, 4);
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_TRUNC,
	      "len 65535 with 0 value bytes must be TRUNC");
	tlv_reader_init(&r, buf, sizeof buf);
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_TRUNC,
	      "len 65535 with 60 value bytes must be TRUNC");

	T_GROUP("ascending ids");
	put_hdr(buf, 0x0002, 0);
	put_hdr(buf + 4, 0x0001, 0);
	tlv_reader_init(&r, buf, 8);
	CHECK(tlv_next(&r, &type, &len, &val) == 0, "first of a descending pair");
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_ORDER,
	      "descending id must be ORDER");
	put_hdr(buf, 0x0002, 0);
	put_hdr(buf + 4, 0x0002, 0);
	tlv_reader_init(&r, buf, 8);
	CHECK(tlv_next(&r, &type, &len, &val) == 0, "first of an equal pair");
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_ORDER,
	      "a duplicate id must be ORDER, so duplicates cannot exist");
	put_hdr(buf, 0x0000, 0);
	put_hdr(buf + 4, 0x0001, 0);
	tlv_reader_init(&r, buf, 8);
	CHECK(tlv_next(&r, &type, &len, &val) == 0, "id 0 is a legal first id");
	CHECK(tlv_next(&r, &type, &len, &val) == 0, "0 then 1 is ascending");

	T_GROUP("trailing garbage");
	put_hdr(buf, 0x0010, 2);
	tlv_reader_init(&r, buf, 4 + 2 + 3);	/* one TLV then 3 loose bytes */
	CHECK(tlv_next(&r, &type, &len, &val) == 0, "the complete TLV");
	CHECK(tlv_next(&r, &type, &len, &val) == -TLVE_TRUNC,
	      "3 trailing bytes must be TRUNC, never a clean end");

	T_GROUP("exhaustive length");
	{
		int blen;
		long accepted = 0, refused = 0;

		for (blen = 4; blen <= 40; blen++) {
			int vlen;

			for (vlen = 0; vlen <= 64; vlen++) {
				uint8_t *p = malloc((size_t)blen);
				int want_ok;

				CHECK(p != NULL, "malloc %d", blen);
				if (p == NULL)
					continue;
				memset(p, 0x5A, (size_t)blen);
				put_hdr(p, 0x0100, (uint16_t)vlen);
				tlv_reader_init(&r, p, (size_t)blen);
				rc = tlv_next(&r, &type, &len, &val);
				want_ok = (vlen <= blen - 4);
				if (want_ok) {
					accepted++;
					CHECK(rc == 0, "blen=%d vlen=%d: rc=%d,"
					      " want accept", blen, vlen, rc);
					if (rc == 0) {
						CHECK(len == (uint16_t)vlen,
						      "len %u != %d", len, vlen);
						CHECK(val >= p &&
						      val + len <= p + blen,
						      "blen=%d vlen=%d: value"
						      " escapes the buffer",
						      blen, vlen);
					}
				} else {
					refused++;
					CHECK(rc == -TLVE_TRUNC,
					      "blen=%d vlen=%d: rc=%d, want"
					      " TRUNC", blen, vlen, rc);
				}
				free(p);
			}
			/* and the 16-bit maximum, which no buffer can satisfy */
			{
				uint8_t *p = malloc((size_t)blen);

				if (p != NULL) {
					memset(p, 0, (size_t)blen);
					put_hdr(p, 0x0100, 0xFFFF);
					tlv_reader_init(&r, p, (size_t)blen);
					refused++;
					CHECK(tlv_next(&r, &type, &len, &val) ==
					      -TLVE_TRUNC,
					      "blen=%d vlen=65535 must be TRUNC",
					      blen);
					free(p);
				}
			}
		}
		printf("  exhaustive length: %ld accepted, %ld refused\n",
		       accepted, refused);
		CHECK(accepted > 0 && refused > 0,
		      "the sweep must exercise BOTH answers: %ld/%ld",
		      accepted, refused);
	}

	T_GROUP("writer");
	tlv_writer_init(&w, buf, sizeof buf);
	CHECK(tlv_write(&w, 0x0010, (const uint8_t *)"abcd", 4) == 0, "write 1");
	CHECK(tlv_write(&w, 0x0010, (const uint8_t *)"abcd", 4) == -TLVE_ORDER,
	      "a duplicate id must be refused by the writer too");
	CHECK(tlv_write(&w, 0x0009, (const uint8_t *)"abcd", 4) == -TLVE_ORDER,
	      "a descending id must be refused");
	CHECK(tlv_write(&w, 0x0011, NULL, 4) == -TLVE_ARG,
	      "NULL value with len 4 must be refused");
	CHECK(tlv_write(&w, 0x0011, NULL, 0) == 0, "NULL value with len 0 is ok");
	CHECK(tlv_writer_len(&w) == 12, "12 bytes written, got %lu",
	      (unsigned long)tlv_writer_len(&w));

	T_GROUP("writer space");
	{
		uint8_t small[8];

		tlv_writer_init(&w, small, sizeof small);
		CHECK(tlv_write(&w, 1, (const uint8_t *)"abcd", 4) == 0,
		      "4+4 fits exactly");
		CHECK(tlv_write(&w, 2, (const uint8_t *)"", 0) == -TLVE_SPACE,
		      "a 4-byte header must not fit in 0 bytes");
		tlv_writer_init(&w, small, sizeof small);
		CHECK(tlv_write(&w, 1, (const uint8_t *)"abcde", 5) ==
		      -TLVE_SPACE, "4+5 must not fit in 8");
		CHECK(tlv_writer_len(&w) == 0,
		      "a refused write must write nothing");
		tlv_writer_init(&w, small, 3);
		CHECK(tlv_write(&w, 1, NULL, 0) == -TLVE_SPACE,
		      "a header must not fit in 3 bytes");
	}

	T_GROUP("writer then reader");
	{
		static const uint8_t v1[3] = { 1, 2, 3 };
		static const uint8_t v2[1] = { 9 };
		size_t n;

		tlv_writer_init(&w, buf, sizeof buf);
		CHECK(tlv_write(&w, 0x0001, v1, 3) == 0, "w1");
		CHECK(tlv_write(&w, 0x0070, v2, 1) == 0, "w2");
		n = tlv_writer_len(&w);
		tlv_reader_init(&r, buf, n);
		CHECK(tlv_next(&r, &type, &len, &val) == 0 && type == 0x0001 &&
		      len == 3 && memcmp(val, v1, 3) == 0, "r1");
		CHECK(tlv_next(&r, &type, &len, &val) == 0 && type == 0x0070 &&
		      len == 1 && val[0] == 9, "r2");
		CHECK(tlv_next(&r, &type, &len, &val) == 1, "clean end");
	}

	T_GROUP("NULL arguments");
	tlv_reader_init(&r, NULL, 4096);
	CHECK(tlv_next(&r, &type, &len, &val) == 1,
	      "a NULL buffer must read as length 0, not as 4096 bytes");
	CHECK(tlv_next(&r, NULL, &len, &val) == -TLVE_ARG, "NULL type out");
	tlv_writer_init(&w, NULL, 4096);
	CHECK(tlv_write(&w, 1, (const uint8_t *)"x", 1) == -TLVE_SPACE,
	      "a NULL destination must have no room");

	return t_done("tlv");
}
