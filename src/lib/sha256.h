/* sha256.h -- SHA-256 (FIPS 180-2, restated in RFC 6234 section 6.2) and
 * HMAC-SHA-256 (RFC 2104), for rlxfw's R7 userspace.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT IS
 * ---------------------------------------------------------------------------
 *
 * The one hash this firmware has.  It is used by the login password hash
 * (`src/lib/kdf.c`: PBKDF2 and scrypt are both built on the HMAC below) and
 * by nothing else at the time of writing.  Written from the specification
 * text; no third-party code.  The declarations are pinned by
 * `CONTRACT.md` and must not drift.
 *
 * Every byte that crosses into or out of a `uint32_t` does so through an
 * explicit shift.  There is no cast of a byte pointer to `uint32_t *` and no
 * `memcpy` of a word array, for two independent reasons: the target is
 * big-endian and the host that runs the tests is little-endian, and MIPS-I
 * traps an unaligned `lw` instead of fixing it up.  The input pointer handed
 * to `sha256_update` is therefore allowed to be arbitrarily aligned.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES NOT ESTABLISH
 * ---------------------------------------------------------------------------
 *
 * Passing the RFC vectors says the arithmetic is right.  It says nothing
 * about side channels: this code is not hardened against timing or cache
 * analysis of the message, and SHA-256's own data flow is not secret-index
 * dependent but nothing here proves the compiler kept it that way.  The
 * `wipe`/`memset` calls inside the .c file are hygiene, not a claim about
 * what remains in DRAM: the compiler is permitted to remove a store that
 * nothing reads, and no test in this tree checks that it did not.
 */
#ifndef RLXFW_SHA256_H
#define RLXFW_SHA256_H
#include <stddef.h>
#include <stdint.h>

#define SHA256_DIGEST_LEN 32
#define SHA256_BLOCK_LEN  64

struct sha256_ctx { uint32_t h[8]; uint64_t nbits; uint8_t buf[SHA256_BLOCK_LEN]; size_t buflen; };

void sha256_init(struct sha256_ctx *c);
void sha256_update(struct sha256_ctx *c, const void *p, size_t n);
void sha256_final(struct sha256_ctx *c, uint8_t out[SHA256_DIGEST_LEN]);
int  sha256(const void *p, size_t n, uint8_t out[SHA256_DIGEST_LEN]);   /* PINNED by SPEC-R7 */

struct hmac_sha256_ctx { struct sha256_ctx inner, outer; };
void hmac_sha256_init(struct hmac_sha256_ctx *c, const uint8_t *key, size_t klen);
void hmac_sha256_update(struct hmac_sha256_ctx *c, const void *p, size_t n);
void hmac_sha256_final(struct hmac_sha256_ctx *c, uint8_t out[SHA256_DIGEST_LEN]);
int  hmac_sha256(const uint8_t *key, size_t klen, const void *p, size_t n,
                 uint8_t out[SHA256_DIGEST_LEN]);
#endif
