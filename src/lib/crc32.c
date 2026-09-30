/* crc32.c -- see crc32.h for the convention and the known answers. */

#include "crc32.h"

uint32_t crc32_ieee(uint32_t crc, const void *p, size_t n)
{
	const uint8_t *b = (const uint8_t *)p;
	uint32_t c = crc ^ 0xFFFFFFFFu;
	size_t i;
	int k;

	for (i = 0; i < n; i++) {
		c ^= (uint32_t)b[i];
		for (k = 0; k < 8; k++) {
			/* Branch-free reflected step.  The mask is built from
			 * unsigned arithmetic only: negating a signed 1 to get
			 * 0xFFFFFFFF is the idiomatic form and is also the one
			 * that makes -fsanitize=undefined complain on a
			 * platform where int is not 32 bits. */
			c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
		}
	}
	return c ^ 0xFFFFFFFFu;
}
