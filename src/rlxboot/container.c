/* src/rlxboot/container.c -- verify an `RLXU` container.  rlxfw's own code.
 *
 * THE ORDER IS THE SECURITY PROPERTY, NOT THE CHECKS.
 *
 * Every loader that has ever been broken had all the right checks in it.  What
 * this unit's own stage 2 does -- `check_image()` at 0x80407D50, and
 * `docs/loader-flash-write.md` s3 is the reading -- is call
 * `flash_read(header.startAddr, offset + 16, header.len)`, which COPIES THE
 * PAYLOAD TO AN ADDRESS TAKEN OUT OF THE HEADER, and only then sums the RAM
 * copy as 16-bit halfwords and requires the sum to be zero.  So a header the
 * checksum will reject has already been allowed to scatter `header.len` bytes
 * over an address of its own choosing, and no bound on `startAddr` appears
 * anywhere in that path.  rlxboot deliberately does not repeat that, and this
 * file is where the "deliberately" lives:
 *
 *   1  magic, format, header_len          -- is this even an RLXU container
 *   2  every field bound, every overlap   -- arithmetic on the header only
 *   3  Ed25519 over header bytes 0..95    -- the header becomes trusted HERE
 *   4  SHA-256 over payload_len bytes     -- the payload becomes trusted HERE
 *   5  version against the counter        -- policy, on a trusted version
 *
 * Nothing before step 4 reads a payload byte.  Nothing in this file copies
 * anything at all -- the copy is `main.c`'s and happens after `rlxu_verify`
 * returns 0.  `r->hashed` and `r->copied` exist so that claim is testable
 * rather than asserted: on every refusal at or before step 3 both are 0, and
 * `test/t_container.c` checks that on every one of the bit-flip sweep's
 * rejections, not on a chosen example.
 *
 * WHY STEP 2 BEFORE STEP 3, when step 3 is what makes the header trustworthy.
 * Because step 2 reads nothing but the 96 header bytes already in hand and
 * writes nothing: it is pure arithmetic over a buffer whose length step 0 has
 * already bounded.  Doing it first means that by the time the signature
 * verifies, every number in the header is already known to be inside its
 * range, so no later step has to re-derive a bound; and it means a malformed
 * container is refused with a field name even when it is unsigned garbage,
 * which is what makes the test suite able to say WHICH field.  The ordering
 * that would matter -- doing anything with the payload, or with an address out
 * of the header, before step 3 -- is the one this file refuses to do.
 *
 * WHY STEP 5 LAST.  The version is an untrusted 32-bit field until step 3, and
 * the anti-rollback decision is the only one an attacker gains anything from
 * flipping.  Checking it before the signature would mean the counter policy
 * ran on a number nobody had authenticated.
 *
 * THE DECLARED FLASH DESTINATION (format 2, 2026-10-04).  `flash_at` at offset
 * 64 and `flash_form` at offset 68 are inside the signed header, and this file
 * makes three separate decisions about them, in this order:
 *
 *   flash_form   the pair must be CONSISTENT: a destination with no form, or
 *                a form with no destination, or a form that is not one of the
 *                three words, is refused before any arithmetic is done with
 *                it.  The form decides how many bytes land, so a form nobody
 *                checked is a length nobody checked.
 *   flash_dst    the DECLARATION is refused if the LANDING RANGE names
 *                something nothing can license -- the boot loader, `H601`, or
 *                past the end of the part.  This refusal does not depend on
 *                any caller-supplied value, so no caller can turn it off; it
 *                fires in the boot path too, where nothing is written at all.
 *   flash_match  the declaration is compared with `e->write_at` and
 *                `e->write_form`, where and as what the CALLER says it is
 *                about to write.  A mismatch in EITHER is refused, and so is
 *                a container that declares nothing -- because "nobody checked
 *                a destination for this container" is exactly what an
 *                undeclared container means.
 *
 * `flash_dst` is deliberately NOT the whole of `tools/flashguard.py`'s table:
 * the rescue slot is licensable, so the format permits a container that
 * declares it and the host build is where the owner's dated licence is
 * demanded.  A fence that could be opened by a licence would not be a fence,
 * and a fence that duplicated the whole policy would drift from it.
 */

#include "container.h"
#include "sha256b.h"
#include "../lib/ed25519.h"

/* Every address in this file is 32 bits because the device's are, and `unsigned
 * long` is 64 bits on the host that runs the tests.  Without this mask the
 * wrap-around case -- `load_addr + payload_len` carrying past 0xFFFFFFFF -- is
 * unreachable on the host, so the branch that catches it would be covered by no
 * test and only the device would ever execute it.  Masking makes the host a
 * faithful model of the target rather than a permissive one. */
#define A32(x) ((x) & 0xFFFFFFFFUL)

/* ------------------------------------------------------------------ helpers */

unsigned long rlxu_be32(const unsigned char *p)
{
	return ((unsigned long)p[0] << 24) | ((unsigned long)p[1] << 16)
	     | ((unsigned long)p[2] << 8)  | (unsigned long)p[3];
}

unsigned int rlxu_be16(const unsigned char *p)
{
	return ((unsigned int)p[0] << 8) | (unsigned int)p[1];
}

/* [a0,a1) against [b0,b1), both non-empty.  Written with no subtraction so a
 * length that would wrap cannot turn an overlap into a miss; the wrap itself is
 * refused separately, above. */
static int overlaps(unsigned long a0, unsigned long a1,
                    unsigned long b0, unsigned long b1)
{
	if (a0 >= a1 || b0 >= b1)
		return 0;
	return (a0 < b1) && (b0 < a1);
}

/* Compare 32 bytes.  Every byte is read whatever the first one says: a digest
 * comparison that returns early is a digest comparison whose timing is a
 * function of the secret it is comparing, and more practically it is the
 * comparison a mutation can weaken without any vector noticing.
 * `test/mutate.sh` weakens exactly this function and the bit-flip sweep goes
 * red, which is what makes the sweep a test of the comparison and not just of
 * SHA-256. */
static int ct_eq32(const unsigned char *a, const unsigned char *b)
{
	unsigned long d = 0;
	int i;

	for (i = 0; i < 32; i++)
		d |= (unsigned long)(a[i] ^ b[i]);
	return d == 0;
}

static const char *const reason_names[RLXU_R__COUNT] = {
	"ok",
	"short",
	"magic",
	"format",
	"header_len",
	"version",
	"payload_len",
	"flags",
	"reserved",
	"load_addr",
	"entry_addr",
	"dst_self",
	"dst_buf",
	"dst_loader",
	"truncated",
	"sig",
	"digest",
	"rollback",
	"flash_dst",
	"flash_match",
	"flash_form"
};

const char *rlxu_reason_name(int reason)
{
	if (reason < 0 || reason >= RLXU_R__COUNT)
		return "bad_reason";
	return reason_names[reason];
}

static void trace(struct rlxu *r, int tag)
{
	if (r->trace_n < (int)sizeof r->trace)
		r->trace[r->trace_n++] = (unsigned char)tag;
}

static int refuse(struct rlxu *r, rlxu_report_fn rep, int stage, int reason)
{
	r->stage = stage;
	r->reason = reason;
	if (rep)
		rep(r, stage, reason);
	return reason;
}

static void passed(struct rlxu *r, rlxu_report_fn rep, int stage)
{
	if (rep)
		rep(r, stage, RLXU_OK);
}

/* ------------------------------------------------------------ the counter */

unsigned long rlxu_counter_from_bitmap(const unsigned char *bm, int *malformed)
{
	unsigned long lead = 0, total = 0;
	int seen_one = 0, bad = 0;
	int i, b;

	for (i = 0; i < RLXU_CTR_BYTES; i++) {
		for (b = 7; b >= 0; b--) {
			int bit = (bm[i] >> b) & 1;
			if (!bit) {
				total++;
				if (!seen_one)
					lead++;
				else
					bad = 1;
			} else {
				seen_one = 1;
			}
		}
	}
	if (malformed)
		*malformed = bad;
	/* A malformed bitmap yields the TOTAL, which is >= the leading run.  A
	 * counter that is too high refuses updates; one that is too low accepts
	 * a rollback.  Of the two ways to be wrong only the second is a
	 * security failure, so the malformed case is resolved upward. */
	return bad ? total : lead;
}

/* ------------------------------------------------------------------ verify */

int rlxu_verify(const unsigned char *c, unsigned long avail,
                const struct rlxu_env *e, struct rlxu *r,
                rlxu_report_fn rep)
{
	unsigned long dst0, dst1, buf1, body;
	int i;

	/* `*r` is fully initialised before anything is read, so a caller that
	 * ignores the return value still cannot read a stale verdict. */
	r->magic = r->version = r->payload_len = 0;
	r->load_addr = r->entry_addr = r->flags = r->recipe_id = 0;
	r->format = r->header_len = 0;
	r->flash_at = r->flash_form = r->flash_len = 0;
	r->digest = 0;
	r->reason = RLXU_OK;
	r->stage = 0;
	r->trace_n = 0;
	r->hashed = 0;
	r->copied = 0;
	for (i = 0; i < (int)sizeof r->trace; i++)
		r->trace[i] = 0;

	/* Step 0.  Not in the spec's numbered list, and it has to come first:
	 * every step below reads inside the first 160 bytes, so the length of
	 * what is readable is the one thing that cannot be checked later.  A
	 * truncated container is a refusal, never a short read. */
	if (avail < RLXU_BODY_OFF)
		return refuse(r, rep, RLXU_T_HDR, RLXU_R_SHORT);

	/* ---- step 1: is this an RLXU container at all ---------------------- */
	trace(r, RLXU_T_HDR);
	r->magic      = rlxu_be32(c + 0);
	r->format     = rlxu_be16(c + 4);
	r->header_len = rlxu_be16(c + 6);
	if (r->magic != RLXU_MAGIC)
		return refuse(r, rep, RLXU_T_HDR, RLXU_R_MAGIC);
	if (r->format != RLXU_FORMAT)
		return refuse(r, rep, RLXU_T_HDR, RLXU_R_FORMAT);
	if (r->header_len != RLXU_HDR_LEN)
		return refuse(r, rep, RLXU_T_HDR, RLXU_R_HDRLEN);
	passed(r, rep, RLXU_T_HDR);

	/* ---- step 2: every field bound, and every overlap ------------------ */
	trace(r, RLXU_T_BOUND);
	r->version     = rlxu_be32(c + 8);
	r->payload_len = rlxu_be32(c + 12);
	r->load_addr   = rlxu_be32(c + 16);
	r->entry_addr  = rlxu_be32(c + 20);
	r->flags       = rlxu_be32(c + 24);
	r->digest      = c + 28;
	r->recipe_id   = rlxu_be32(c + 60);
	r->flash_at    = rlxu_be32(c + RLXU_FLASH_OFF);
	r->flash_form  = rlxu_be32(c + RLXU_FORM_OFF);

	if (r->version < RLXU_VER_MIN || r->version > RLXU_VER_MAX)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_VERSION);
	/* payload_len == 0 is refused by name.  SPEC s2 gives only the upper
	 * bound; a zero-length payload has no address the entry check could
	 * accept, so it would be refused as `entry_addr` -- a refusal that
	 * names the wrong field is a refusal a test cannot trust. */
	if (r->payload_len == 0 || r->payload_len > RLXU_PAYLOAD_MAX)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_PAYLOAD_LEN);
	/* Any unknown bit set -> reject.  In R8a every defined bit is 0, so
	 * this is `flags != 0`; bit 0 is reserved for "payload is LZMA" and
	 * turning it on is a format change, not a flag flip. */
	if (r->flags != 0)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLAGS);
	for (i = 0; i < RLXU_RESV_LEN; i++)
		if (c[RLXU_RESV_OFF + i] != 0)
			return refuse(r, rep, RLXU_T_BOUND, RLXU_R_RESERVED);

	/* The whole container must be present before one payload byte is read.
	 * `body` cannot wrap: payload_len is already <= 3 MiB. */
	body = RLXU_BODY_OFF + r->payload_len;
	if (avail < body)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_TRUNCATED);
	buf1 = A32(e->buf_base + body);
	if (buf1 < e->buf_base || buf1 > e->buf_limit)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_TRUNCATED);

	/* The destination and the form must agree about whether there is one,
	 * and the form fixes how many bytes land.  `flash_len` is derived HERE
	 * and nowhere else, so the length `flash_dst` bounds, the length the
	 * host guard checked and the length a writer would program are one
	 * number. */
	if (r->flash_at == RLXU_FLASH_NONE) {
		if (r->flash_form != RLXU_FORM_NONE)
			return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_FORM);
		r->flash_len = 0;
	} else if (r->flash_form == RLXU_FORM_WHOLE) {
		r->flash_len = body;
	} else if (r->flash_form == RLXU_FORM_PAYLOAD) {
		r->flash_len = r->payload_len;
	} else {
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_FORM);
	}

	/* The DECLARED landing range, against the two ranges that cost the
	 * device and the end of the part.  `flash_at >= RLXU_CHIP_SIZE` is
	 * tested FIRST so that `flash_at + flash_len` cannot wrap: after it,
	 * flash_at < 4 MiB and flash_len <= 3 MiB + 160, so the sum is under
	 * 8 MiB.  `flash_at < RLXU_FLASH_KEEPOUT_END` then covers both ways in,
	 * because a range starting at or above the keepout cannot extend down
	 * into it. */
	if (r->flash_at != RLXU_FLASH_NONE) {
		if (r->flash_at >= RLXU_CHIP_SIZE)
			return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_DST);
		if (A32(r->flash_at + r->flash_len) > RLXU_CHIP_SIZE)
			return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_DST);
		if (r->flash_at < RLXU_FLASH_KEEPOUT_END)
			return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_DST);
	}
	/* And against where -- and as what -- this caller says it is writing.
	 * Equality in BOTH is the whole rule: a container declaring nothing
	 * (RLXU_FLASH_NONE) is refused against every write, which is the point
	 * of making the declaration non-optional in the producer, and a caller
	 * that would strip a prefix the container did not ask it to strip is
	 * refused even when the offset agrees. */
	if (e->write_at != RLXU_FLASH_NONE
	    && (r->flash_at != e->write_at
	        || r->flash_form != e->write_form))
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_FLASH_MATCH);

	dst0 = r->load_addr;
	dst1 = A32(r->load_addr + r->payload_len);

	/* In RAM, no wrap, and word aligned.  The alignment is an addition to
	 * SPEC s2: `entry_addr` is a jump target and an unaligned one is an
	 * AdEL on this core, which would land in the loader's `do_reserved` and
	 * cost a power cycle rather than print a refusal. */
	if (dst1 < dst0)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_LOAD_ADDR);
	if (dst0 < e->ram_base || dst1 > e->ram_end)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_LOAD_ADDR);
	if ((dst0 & 3UL) != 0)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_LOAD_ADDR);
	if (r->entry_addr < dst0 || r->entry_addr >= dst1)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_ENTRY_ADDR);
	if ((r->entry_addr & 3UL) != 0)
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_ENTRY_ADDR);

	/* Three destinations that are inside RAM and still must not be written.
	 * SPEC s2 names the first two; the loader window is an addition, and the
	 * reason is SPEC s4's own sentence that the loader's code and data
	 * "must not be overwritten before the jump".  rlxboot copies and then
	 * jumps, so the copy happens before the jump by construction. */
	if (overlaps(dst0, dst1, e->self_base, e->self_end))
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_DST_SELF);
	if (overlaps(dst0, dst1, e->buf_base, buf1))
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_DST_BUF);
	if (overlaps(dst0, dst1, e->ldr_base, e->ldr_end))
		return refuse(r, rep, RLXU_T_BOUND, RLXU_R_DST_LOADER);
	passed(r, rep, RLXU_T_BOUND);

	/* ---- step 3: the header's own signature ---------------------------- */
	/* Everything above read only the 96 header bytes and the 24 reserved
	 * bytes inside them.  Nothing has been copied and nothing has been
	 * hashed.  From the next line on, the header is trusted. */
	trace(r, RLXU_T_SIG);
	if (rlx_ed25519_verify(c + RLXU_HDR_LEN, c, RLXU_HDR_LEN, e->pk) != 0)
		return refuse(r, rep, RLXU_T_SIG, RLXU_R_SIG);
	passed(r, rep, RLXU_T_SIG);

	/* ---- step 4: the payload against the trusted digest ---------------- */
	trace(r, RLXU_T_DIGEST);
	{
		unsigned char d[SHA256B_DIGEST];

		sha256b(d, c + RLXU_BODY_OFF, r->payload_len);
		r->hashed = r->payload_len;
		if (!ct_eq32(d, r->digest))
			return refuse(r, rep, RLXU_T_DIGEST, RLXU_R_DIGEST);
	}
	passed(r, rep, RLXU_T_DIGEST);

	/* ---- step 5: anti-rollback ----------------------------------------- */
	/* THE BOUNDARY RULE, stated because a boundary nobody wrote down is a
	 * boundary two readers disagree about: `version == counter` IS
	 * ACCEPTED, `version < counter` is refused.
	 *
	 * The counter is the ordinal of the newest version ever installed, and
	 * R8b advances it by clearing one bit per version -- so after installing
	 * version N the counter reads N.  Refusing equality would mean the
	 * device could not re-install the image it is running, which is the
	 * ordinary recovery operation, and it would require the counter to
	 * advance on a boot rather than on an install.  Accepting equality
	 * grants an attacker nothing: version N is already authorised, they
	 * already hold a signed container for it, and replaying it returns the
	 * device to a state it was legitimately in.  What the counter must stop
	 * is N-1 after N, and that is exactly what `<` stops. */
	trace(r, RLXU_T_VER);
	if (r->version < e->counter)
		return refuse(r, rep, RLXU_T_VER, RLXU_R_ROLLBACK);

	r->stage = RLXU_T_VER;
	r->reason = RLXU_OK;
	passed(r, rep, RLXU_T_VER);
	return RLXU_OK;
}
