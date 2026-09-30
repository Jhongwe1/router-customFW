/* src/lib/ed25519.h -- Ed25519 verification (RFC 8032), freestanding.
 *
 * The arithmetic in `ed25519.c` is IMPORTED (TweetNaCl 20140427, public
 * domain).  This header, and the three `rlx_` entry points it declares, are
 * rlxfw's.  `src/rlxboot/test/mk-import.sh` names every retained upstream line
 * range and `check-import.sh` proves the retained text is unaltered.
 *
 * Constraints this interface exists to enforce:
 *   - no malloc, no VLA: the message length is bounded by ED25519_MSG_MAX and a
 *     longer message is REFUSED, never truncated;
 *   - no recursion anywhere below these calls;
 *   - verification only in the device image.  ED25519_KEYGEN and ED25519_SIGN
 *     are defined for host tests and fixtures and NEVER for the rlxboot
 *     payload, so `nm` on the payload shows no signer.
 */
#ifndef RLX_ED25519_H
#define RLX_ED25519_H

/* 1024 and not 96.  The rlxboot payload only ever verifies a 96-byte header,
 * but the RFC 8032 s7.1 vector set includes a 1023-byte message, and the whole
 * value of running that set on the target is that the target runs the SAME
 * code.  A bound of 96 would have made the target's vector run a different
 * program from the device's. */
#ifndef ED25519_MSG_MAX
#define ED25519_MSG_MAX 1024
#endif

#define RLX_ED25519_EBADSIG   (-1)   /* the equation did not hold          */
#define RLX_ED25519_EPUBKEY   (-2)   /* A is not a point on the curve      */
#define RLX_ED25519_ESCALAR   (-3)   /* s >= L: not a canonical signature  */
#define RLX_ED25519_ETOOLONG  (-4)   /* msglen > ED25519_MSG_MAX           */

/* 0 on success, one of the negatives above on failure.  Never partially
 * succeeds and writes nothing the caller can mistake for a verdict. */
int rlx_ed25519_verify(const unsigned char *sig, const unsigned char *msg,
                       unsigned long msglen, const unsigned char *pk);

#ifdef ED25519_KEYGEN
int rlx_ed25519_pubkey_from_seed(unsigned char pk[32], const unsigned char seed[32]);
#endif

#ifdef ED25519_SIGN
int rlx_ed25519_sign(unsigned char sig[64], const unsigned char *msg,
                     unsigned long msglen, const unsigned char sk[64]);
#endif

#endif /* RLX_ED25519_H */
