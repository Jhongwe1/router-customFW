/* src/lib/sha512.h -- SHA-512, as used by Ed25519 (RFC 8032).
 *
 * The implementation in `sha512.c` is IMPORTED (TweetNaCl 20140427, public
 * domain); this header is rlxfw's.  `crypto_hash` is upstream's name and is
 * declared here because `src/lib/ed25519.c` calls it; `rlx_sha512` is the name
 * the rest of this tree uses.
 *
 * One-shot only.  There is no incremental interface because nothing in the
 * boot path needs one: Ed25519 hashes a single contiguous 64 + msglen buffer.
 */
#ifndef RLX_SHA512_H
#define RLX_SHA512_H

/* upstream's signature, byte for byte: n is a length in bytes, out is 64 bytes */
int crypto_hash(unsigned char *out, const unsigned char *m, unsigned long long n);

void rlx_sha512(unsigned char out[64], const unsigned char *m, unsigned long n);

#endif /* RLX_SHA512_H */
