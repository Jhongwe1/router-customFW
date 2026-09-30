/* crc32.h -- CRC-32 as SPEC-R7 § 5 pins it: IEEE 802.3 / zlib, reflected,
 * polynomial 0xEDB88320, init and xorout 0xFFFFFFFF.
 *
 * ---------------------------------------------------------------------------
 * WHAT THE CONVENTION MEANS, SO A CALLER CANNOT GET IT WRONG
 * ---------------------------------------------------------------------------
 *
 * `crc32_ieee(0, p, n)` is the whole-buffer CRC.  The init/xorout pair is
 * inside the function, so 0 is the seed for a fresh CRC and the return value
 * of one call is the seed of the next:
 *
 *     crc32_ieee(crc32_ieee(0, a, na), b, nb) == crc32_ieee(0, ab, na + nb)
 *
 * The known answers this is tested against (test_crc32.c):
 *     ""            -> 0x00000000
 *     "123456789"   -> 0xCBF43926   (the standard IEEE check value)
 *
 * There is no table.  A 256-entry table is 1 KiB of a 4 MiB flash budget for
 * a function that runs over at most 4 KiB at a time; the bitwise form is
 * ~32 Ki iterations per slot, which on a 400 MHz core is under a millisecond
 * and is not on any path that matters.  Nothing here depends on an
 * initialisation step having run, which is the other reason to have no table.
 */
#ifndef RLXFW_CRC32_H
#define RLXFW_CRC32_H

#include <stddef.h>
#include <stdint.h>

/* n == 0 returns `crc` unchanged; `p` is then not read and may be NULL. */
uint32_t crc32_ieee(uint32_t crc, const void *p, size_t n);

#endif /* RLXFW_CRC32_H */
