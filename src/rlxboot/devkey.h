/* src/rlxboot/devkey.h -- the DEVELOPMENT signing key.  NOT A PRODUCTION KEY.
 *
 * SPEC-R8a.md s3 pins the development key pair to a fixed seed so that two
 * agents working without a channel between them derive the same key: the seed
 * is 32 bytes, every byte 0x42.  It is in the tree ON PURPOSE and it is
 * worthless: anyone reading this file can sign a container for this build.
 *
 * R8b NEEDS A REAL KEY AND IT MUST NOT LIVE HERE.  What that means concretely,
 * because "keep the key safe" is not an instruction:
 *   - the private key never enters this repository, tracked or untracked, and
 *     never enters $FWRE_WORK either, which is shared with another checkout;
 *   - the public key is what gets compiled in, and the commit that changes it
 *     is the commit that ends the development key's authority -- there is no
 *     key list and no revocation in this format, so rotation is a rebuild;
 *   - a signing step that can be run by anything that can also write flash has
 *     bought nothing, so the signer and the flasher are not the same operator.
 *
 * THE VALUE BELOW IS DERIVED, NOT TRANSCRIBED FROM A REPORT.  It was produced
 * by `rlx_ed25519_pubkey_from_seed` on this tree's own code, and
 * `test/t_container.c` re-derives it from the seed at run time and refuses if
 * the two differ -- so a typo here is a test failure, not a device that trusts
 * a key nobody holds.  `tools/rlxsign.py` (another agent, another
 * implementation, same segment) derives it independently; a disagreement
 * between the two is a finding about one of the implementations.
 */
#ifndef RLXBOOT_DEVKEY_H
#define RLXBOOT_DEVKEY_H

/* 2152f8d19b791d24453242e15f2eab6cb7cffa7b6a5ed30097960e069881db12 */
#define RLXBOOT_DEVKEY_HEX \
	"2152f8d19b791d24453242e15f2eab6cb7cffa7b6a5ed30097960e069881db12"

static const unsigned char rlxboot_devkey[32] = {
	0x21,0x52,0xf8,0xd1,0x9b,0x79,0x1d,0x24,
	0x45,0x32,0x42,0xe1,0x5f,0x2e,0xab,0x6c,
	0xb7,0xcf,0xfa,0x7b,0x6a,0x5e,0xd3,0x00,
	0x97,0x96,0x0e,0x06,0x98,0x81,0xdb,0x12
};

/* The seed, for the host tests and the fixtures only.  A device build has no
 * use for it, so it is behind a define the payload never sets -- not merely
 * "not referenced": an unreferenced `static const` is a
 * `-Wunused-const-variable` under `-Werror`, and the fix for that must not be
 * to widen the warning set. */
#ifdef RLXBOOT_WANT_SEED
static const unsigned char rlxboot_devseed[32] = {
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,
	0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42
};
#endif /* RLXBOOT_WANT_SEED */

#endif /* RLXBOOT_DEVKEY_H */
