/* src/rlxboot/klib.c -- memcpy, memset, memcmp.  rlxfw's own code.
 *
 * There is no libc in this image and there will not be one.  `-fno-builtin`
 * stops gcc turning a structure assignment or a loop into a `memcpy` call, but
 * it does not promise never to emit one, so these are defined with the C names
 * as well as the `rlx_` ones -- a call the compiler emits then links to code in
 * this tree rather than failing at link time, which is the good outcome.
 *
 * Byte at a time, deliberately.  A word-at-a-time copy needs an alignment case
 * analysis, and on this core an unaligned `lw` is an AdEL rather than a slow
 * path (`SPEC.md` `CPU-75`).  3 MiB byte-wise is a few tens of milliseconds and
 * the correctness is on one page.
 *
 * NO OVERLAP HANDLING, and that is a decision: `rlxu_verify` refuses any
 * container whose destination overlaps the container itself, so `rlx_memcpy`'s
 * only caller cannot hand it overlapping ranges.  A `memmove` here would be
 * code covering a case the verifier has already refused, and the check that
 * matters is the verifier's.
 */

#include "rlxboot.h"

void *rlx_memcpy(void *d, const void *s, unsigned long n)
{
	unsigned char *p = (unsigned char *)d;
	const unsigned char *q = (const unsigned char *)s;

	while (n--)
		*p++ = *q++;
	return d;
}

void *rlx_memset(void *d, int c, unsigned long n)
{
	unsigned char *p = (unsigned char *)d;

	while (n--)
		*p++ = (unsigned char)c;
	return d;
}

int rlx_memcmp(const void *a, const void *b, unsigned long n)
{
	const unsigned char *p = (const unsigned char *)a;
	const unsigned char *q = (const unsigned char *)b;

	while (n--) {
		if (*p != *q)
			return (int)*p - (int)*q;
		p++;
		q++;
	}
	return 0;
}

/* The C names, for anything the compiler emits on its own.  They are separate
 * definitions rather than aliases so that `nm` on the payload shows exactly
 * which symbols exist. */
void *memcpy(void *d, const void *s, unsigned long n);
void *memset(void *d, int c, unsigned long n);
int memcmp(const void *a, const void *b, unsigned long n);

void *memcpy(void *d, const void *s, unsigned long n)
{
	return rlx_memcpy(d, s, n);
}

void *memset(void *d, int c, unsigned long n)
{
	return rlx_memset(d, c, n);
}

int memcmp(const void *a, const void *b, unsigned long n)
{
	return rlx_memcmp(a, b, n);
}
