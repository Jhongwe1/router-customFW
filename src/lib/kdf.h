/* kdf.h -- PBKDF2-HMAC-SHA-256 (RFC 8018), scrypt (RFC 7914), the 56-byte
 * `admin.pwhash` blob of SPEC-R7 section 4.2, and the entropy gate in front
 * of the salt.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT IS FOR
 * ---------------------------------------------------------------------------
 *
 * One thing: rlxfw's web login password.  brokerd holds the blob, brokerd
 * verifies it, and nothing else in the image calls scrypt.  The parameter set
 * below (`KDF_LOG2N`/`KDF_R`/`KDF_P`) is a memory budget before it is a
 * security choice: a 26 MB machine with no swap, serving a login form that an
 * unauthenticated caller can hit, cannot afford the scrypt parameters a PC
 * would use.  `KDF_PEAK_CAP` is the hard ceiling, checked before the
 * allocation, and `kdf_scrypt` refuses rather than trying.
 *
 * `kdf_scrypt_peak` is the whole footprint of one evaluation, in bytes:
 *
 *     N * 128 * r   the V array of ROMix          (RFC 7914 section 5)
 *   + 2 * 128 * r   the X and Y scratch blocks    (ping-ponged, not 3 copies)
 *   +   p * 128 * r the B blocks of scrypt itself (RFC 7914 section 6)
 *
 * and it is one `malloc`, so the number is exactly what the process asks the
 * allocator for.  There is no other heap use in this file.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES NOT ESTABLISH
 * ---------------------------------------------------------------------------
 *
 * `kdf_scrypt_peak` counts what is *requested*.  It is not RSS: uClibc's
 * allocator adds a header and rounds, and for a request over 128 KiB it calls
 * `mmap`, so the pages arrive on first touch and go back to the kernel on
 * `free`.  ROMix touches every one of them, so RSS follows the request
 * closely in practice -- but the number here is an accounting identity about
 * this source file, not a measurement of the kernel's page count.
 *
 * Nothing here is constant-time except `ct_memeq`.  scrypt's memory access
 * pattern is password-dependent by design (that is what makes it memory-hard)
 * and this implementation makes no attempt to hide it from a local attacker.
 *
 * The time one evaluation takes on the device's own CPU is 推 until measured
 * on the silicon; figures taken under qemu are the emulator's timing and
 * bound nothing.
 */
#ifndef RLXFW_KDF_H
#define RLXFW_KDF_H
#include <stddef.h>
#include <stdint.h>

/* Errors, returned negated, and based at 200 so no -KDFE_* can be mistaken for a
 * -errno.  They were 1..5 when this header was first pinned, and that was a
 * defect the implementer caught: -1..-5 are -EPERM, -ENOENT, -ESRCH, -EINTR and
 * -EIO, so a caller (brokerd) that puts a KDF result and a syscall result in the
 * same int could not tell "the blob is malformed" from "I/O error".  Every use is
 * by name, so moving the base is a header change and nothing else.
 *
 * 200 removes the collisions that matter and does not pretend to remove all of
 * them: MIPS errnos run up to EDQUOT = 1133, so a caller that mixes the two error
 * spaces in one int still has a bug.  brokerd maps these to its own status byte
 * (SPEC-R7 section 6) rather than passing them outward. */
#define KDFE_INVAL    200  /* a parameter is out of range */
#define KDFE_NOMEM    201  /* the working buffer could not be allocated */
#define KDFE_ENTROPY  202  /* the kernel pool is not ready -> NOENTROPY */
#define KDFE_IO       203  /* /dev/urandom or /proc could not be read */
#define KDFE_BADBLOB  204  /* the 56-byte pwhash blob is malformed */

/* Recommended parameters (agent D's anti-DoS budget; notes/httpd.md owns the argument). */
#define KDF_LOG2N  12
#define KDF_R      7
#define KDF_P      1
#define KDF_PEAK_CAP 4194304u   /* the pre-written cap, bytes, plan D8 ruling 1 */

/* PBKDF2-HMAC-SHA-256, RFC 8018 */
int kdf_pbkdf2_sha256(const uint8_t *pw, size_t pwlen,
                      const uint8_t *salt, size_t saltlen,
                      uint32_t iters, uint8_t *out, size_t outlen);

/* scrypt, RFC 7914.  N = 1<<log2n.  PINNED signature. */
int kdf_scrypt(const uint8_t *pw, size_t pwlen, const uint8_t salt[16],
               uint8_t log2n, uint16_t r, uint16_t p, uint8_t out[32]);

/* scrypt with a free-form salt and output length: the RFC 7914 section 12
   vectors need salts that are not 16 bytes and a 64-byte output, so the pinned
   wrapper above cannot express them. */
int kdf_scrypt_raw(const uint8_t *pw, size_t pwlen,
                   const uint8_t *salt, size_t saltlen,
                   uint32_t n, uint32_t r, uint32_t p,
                   uint8_t *out, size_t outlen);

/* bytes scrypt will allocate for these parameters, 0 if they overflow */
size_t kdf_scrypt_peak(uint8_t log2n, uint16_t r, uint16_t p);

/* ---------------------------------------------------------------------------
 * Names carried over from the -ENOSYS stub this file replaces.
 *
 * 讀 2026-09-30, the tree this lands in: another agent's src/lib/kdf.h already
 * declares `kdf_scrypt` behind a `KDF_IMPLEMENTED` feature macro and defines the
 * blob's offsets, and src/cfgstore/main.c reads `if (!KDF_IMPLEMENTED)`.  This
 * file is the real implementation, so the stub is deleted when this patch is
 * applied -- and a delete that breaks two other programs' compiles is not an
 * integration.  The names are therefore kept, with the values the stub gave them,
 * checked against SPEC-R7 section 4.2 rather than copied on trust:
 * alg at [0], log2N at [1], r at [2..3], p at [4..5], zero at [6..7], salt at
 * [8..23], key at [24..55].
 *
 * KDF_IMPLEMENTED is 1 here and it is not a promise about the device: it says
 * the code exists and its RFC vectors pass on a big-endian MIPS-I binary under
 * qemu.  A caller that needs to know whether a password can be SET must read
 * kdf_entropy_avail(), which on this board reads 0 (notes/httpd.md section 5.5).
 * ------------------------------------------------------------------------- */
#define KDF_IMPLEMENTED   1
#define KDF_ALG_SCRYPT    1
#define KDF_PWHASH_LEN   56
#define KDF_SALT_OFF      8
#define KDF_SALT_LEN     16
#define KDF_KEY_OFF      24
#define KDF_KEY_LEN      32

/* the 56-byte admin.pwhash blob of SPEC-R7 section 4.2 */
#define PWHASH_LEN 56
int pwhash_make(const uint8_t *pw, size_t pwlen, uint8_t log2n, uint16_t r, uint16_t p,
                const uint8_t salt[16], uint8_t out[PWHASH_LEN]);
int pwhash_verify(const uint8_t blob[PWHASH_LEN], const uint8_t *pw, size_t pwlen);
                                        /* 1 match, 0 mismatch, <0 -KDFE_* */
int pwhash_params(const uint8_t blob[PWHASH_LEN], uint8_t *log2n, uint16_t *r, uint16_t *p);

/* Entropy, fail closed.  Reads /proc/sys/kernel/random/entropy_avail; >= 128
   once is enough (the caller latches it).  Returns the reading, or -KDFE_IO. */
int  kdf_entropy_avail(void);
#define KDF_ENTROPY_MIN 128
/* 16 salt bytes from /dev/urandom, REFUSING if entropy_avail < KDF_ENTROPY_MIN:
   0, or -KDFE_ENTROPY / -KDFE_IO.  Never returns a weak salt. */
int  pwhash_salt(uint8_t salt[16]);

/* constant-time compare, 1 when equal, 0 otherwise; no early exit */
int ct_memeq(const void *a, const void *b, size_t n);
#endif
