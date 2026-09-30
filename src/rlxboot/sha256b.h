/* src/rlxboot/sha256b.h -- SHA-256 for the boot path.  rlxfw's own code.
 *
 * WHY THERE ARE TWO SHA-256 IMPLEMENTATIONS IN THIS TREE, and it is not an
 * oversight.  `src/lib/sha256.c` is userspace's, written by another hand in the
 * same segment.  This one is the boot loader's: `src/rlxboot/` links nothing
 * outside itself and `src/lib/` by design, and a boot loader that shares a
 * translation unit with userspace is a boot loader whose trust boundary moved.
 *
 * The two are a CROSS-CHECK, not a duplication: both are driven against the
 * RFC 6234 vectors, independently written, and if they disagree on one vector
 * one of them is wrong and that is a finding.  `SPEC-R8a.md` s4 asks for exactly
 * this.  The main session may unify them later; until then the names are
 * prefixed `sha256b_` so both can be linked into one binary without collision.
 *
 * The `b` is for "boot", not for a version.
 */
#ifndef RLXBOOT_SHA256B_H
#define RLXBOOT_SHA256B_H

#define SHA256B_DIGEST 32
#define SHA256B_BLOCK  64

struct sha256b {
	unsigned long h[8];        /* the eight chaining words          */
	unsigned long nbits_hi;    /* message length in bits, high half  */
	unsigned long nbits_lo;    /* message length in bits, low half   */
	unsigned long buflen;      /* bytes held in buf, 0..63           */
	unsigned char buf[SHA256B_BLOCK];
};

void sha256b_init(struct sha256b *c);
void sha256b_update(struct sha256b *c, const unsigned char *p, unsigned long n);
void sha256b_final(struct sha256b *c, unsigned char out[SHA256B_DIGEST]);

/* One-shot.  The payload digest is taken over up to 3 MiB in one contiguous
 * staged buffer, so the boot path only ever needs this form; the incremental
 * form exists because the RFC 6234 vectors include a 1,000,000-byte message
 * that the host test feeds in chunks, and testing the chunked path is the only
 * way to know the length accumulator carries. */
void sha256b(unsigned char out[SHA256B_DIGEST], const unsigned char *p, unsigned long n);

#endif /* RLXBOOT_SHA256B_H */
