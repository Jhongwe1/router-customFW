/* test_crc32.c -- the known answers, the chaining identity, and a control that
 * proves this suite can fail.
 *
 * The check value 0xCBF43926 for "123456789" is the one every CRC-32/ISO-HDLC
 * implementation is published with, so agreeing with it is agreeing with an
 * external authority rather than with our own encoder -- which is the whole
 * reason to have a known-answer test at all.
 */

#include <stdint.h>
#include <stdlib.h>

#include "crc32.h"
#include "test_util.h"

int main(void)
{
	static const uint8_t nine[] = { '1', '2', '3', '4', '5', '6', '7', '8',
					'9' };
	uint8_t buf[64];
	uint32_t base;
	int i, bit;

	T_GROUP("known answer");
	CHECK(crc32_ieee(0, nine, sizeof nine) == 0xCBF43926u,
	      "\"123456789\" gave 0x%08lX, want 0xCBF43926",
	      (unsigned long)crc32_ieee(0, nine, sizeof nine));
	CHECK(crc32_ieee(0, "", 0) == 0u, "empty gave 0x%08lX, want 0",
	      (unsigned long)crc32_ieee(0, "", 0));
	CHECK(crc32_ieee(0, NULL, 0) == 0u, "NULL/0 must be the empty CRC");

	/* One more published vector, so that a transposition in the first one
	 * cannot be the only thing this test agrees with. */
	T_GROUP("second vector");
	CHECK(crc32_ieee(0, "a", 1) == 0xE8B7BE43u,
	      "\"a\" gave 0x%08lX, want 0xE8B7BE43",
	      (unsigned long)crc32_ieee(0, "a", 1));

	T_GROUP("chaining");
	for (i = 0; i <= (int)sizeof nine; i++) {
		uint32_t c = crc32_ieee(0, nine, (size_t)i);

		c = crc32_ieee(c, nine + i, sizeof nine - (size_t)i);
		CHECK(c == 0xCBF43926u,
		      "split at %d gave 0x%08lX", i, (unsigned long)c);
	}

	/* THE CONTROL.  A CRC that ignored its input would pass every line
	 * above; these lines fail unless it actually reads the bytes, and the
	 * single-bit sweep is the property the record format leans on (every
	 * one-bit change in a slot must change the CRC). */
	T_GROUP("control: it reads the bytes");
	for (i = 0; i < (int)sizeof buf; i++)
		buf[i] = (uint8_t)(i * 7 + 1);
	base = crc32_ieee(0, buf, sizeof buf);
	CHECK(base != 0u, "a 64-byte buffer must not CRC to 0 by accident");
	for (i = 0; i < (int)sizeof buf; i++) {
		for (bit = 0; bit < 8; bit++) {
			uint32_t c;

			buf[i] ^= (uint8_t)(1u << bit);
			c = crc32_ieee(0, buf, sizeof buf);
			buf[i] ^= (uint8_t)(1u << bit);
			CHECK(c != base, "flipping byte %d bit %d did not change"
			      " the CRC", i, bit);
		}
	}

	T_GROUP("length matters");
	CHECK(crc32_ieee(0, nine, 8) != crc32_ieee(0, nine, 9),
	      "8 and 9 bytes of the same buffer must differ");

	return t_done("crc32");
}
