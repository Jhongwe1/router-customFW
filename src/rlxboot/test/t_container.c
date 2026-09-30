/* src/rlxboot/test/t_container.c -- the container control.  rlxfw's own code.
 *
 * Drives `container.c` -- the same translation unit the device runs -- on the
 * host and, cross-compiled, on big-endian MIPS under `qemu-mips-static`.
 *
 * THE RULE THIS FILE FOLLOWS.  Every bound is violated with a container that is
 * otherwise VALID AND CORRECTLY SIGNED: the header is mutated and then signed
 * again.  A test that mutated a field without re-signing would be refused for
 * the field, pass, and prove nothing -- because it would also be refused if the
 * field check did not exist, by the signature.  Signing after the mutation is
 * what makes each case a test of the bound and not of Ed25519.
 *
 * Every case asserts the reason BY NAME, so a refusal for the wrong reason is a
 * failure and not a pass.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../container.h"
#include "../sha256b.h"
#include "../devkey.h"
#include "../../lib/ed25519.h"

#define PAY 1024
#define CAP (RLXU_BODY_OFF + PAY)

static unsigned char C[CAP + 64];
static unsigned char sk[64];
static int failures, checks;

static struct rlxu_env env;

/* The memory map of SPEC-R8a.md s4, as the device sees it.  The self range is
 * rlxboot's link address plus a generous image+stack extent; `main.c` derives
 * the real one from linker symbols and this table is what the host suite uses.
 */
static void setenv_default(unsigned long counter)
{
	env.ram_base  = 0x80000000UL;
	env.ram_end   = 0x82000000UL;
	env.self_base = 0x81800000UL;
	env.self_end  = 0x81810000UL;
	env.buf_base  = 0x81000000UL;
	env.buf_limit = 0x81700000UL;
	env.ldr_base  = 0x80400000UL;
	env.ldr_end   = 0x80420000UL;
	env.counter   = counter;
	env.pk        = rlxboot_devkey;
}

static void ok(const char *what, int good)
{
	checks++;
	if (!good) {
		failures++;
		printf("FAIL  %s\n", what);
	} else {
		printf("ok    %s\n", what);
	}
}

static void be32(unsigned char *p, unsigned long v)
{
	p[0] = (unsigned char)(v >> 24); p[1] = (unsigned char)(v >> 16);
	p[2] = (unsigned char)(v >> 8);  p[3] = (unsigned char)v;
}

static void be16(unsigned char *p, unsigned int v)
{
	p[0] = (unsigned char)(v >> 8); p[1] = (unsigned char)v;
}

struct hdrspec {
	unsigned long magic, version, payload_len, load, entry, flags, recipe;
	unsigned int format, header_len;
};

static void spec_default(struct hdrspec *s)
{
	s->magic = RLXU_MAGIC;
	s->format = RLXU_FORMAT;
	s->header_len = RLXU_HDR_LEN;
	s->version = 7;
	s->payload_len = PAY;
	s->load = 0x80500000UL;
	s->entry = 0x80500000UL;
	s->flags = 0;
	s->recipe = 0xAABBCCDDUL;
}

/* Build a container from a spec: fill the payload, digest it, write the header,
 * then sign the 96 header bytes.  `resv_nonzero` plants a non-zero byte in the
 * reserved field; -1 leaves it zero. */
static void build(const struct hdrspec *s, int resv_nonzero)
{
	unsigned char d[32];
	unsigned long i;

	for (i = 0; i < PAY; i++)
		C[RLXU_BODY_OFF + i] = (unsigned char)(i * 7 + 3);
	memset(C, 0, RLXU_BODY_OFF);

	be32(C + 0, s->magic);
	be16(C + 4, s->format);
	be16(C + 6, s->header_len);
	be32(C + 8, s->version);
	be32(C + 12, s->payload_len);
	be32(C + 16, s->load);
	be32(C + 20, s->entry);
	be32(C + 24, s->flags);
	sha256b(d, C + RLXU_BODY_OFF, s->payload_len <= PAY ? s->payload_len : PAY);
	memcpy(C + 28, d, 32);
	be32(C + 60, s->recipe);
	if (resv_nonzero >= 0)
		C[64 + resv_nonzero] = 0x01;

	rlx_ed25519_sign(C + RLXU_HDR_LEN, C, RLXU_HDR_LEN, sk);
}

static int run(unsigned long avail, struct rlxu *r)
{
	return rlxu_verify(C, avail, &env, r, 0);
}

static void expect(const char *what, unsigned long avail, int reason)
{
	struct rlxu r;
	char nm[160];
	int got = run(avail, &r);

	sprintf(nm, "%s -> %s", what, rlxu_reason_name(reason));
	if (got != reason) {
		checks++; failures++;
		printf("FAIL  %s (got %s)\n", nm, rlxu_reason_name(got));
		return;
	}
	/* The claim that nothing is hashed before the signature verifies, checked
	 * on EVERY case rather than on one. */
	if (reason != RLXU_OK && r.stage <= RLXU_T_SIG && (r.hashed || r.copied)) {
		checks++; failures++;
		printf("FAIL  %s: refused at stage %d but hashed=%lu copied=%lu\n",
		       nm, r.stage, r.hashed, r.copied);
		return;
	}
	ok(nm, 1);
}

/* ------------------------------------------------------- the field bounds */

static void test_fields(void)
{
	struct hdrspec s;

	setenv_default(1);

	spec_default(&s); build(&s, -1);
	expect("a valid container", CAP, RLXU_OK);

	spec_default(&s); s.magic = 0x524C5856UL; build(&s, -1);
	expect("magic RLXV", CAP, RLXU_R_MAGIC);
	spec_default(&s); s.format = 2; build(&s, -1);
	expect("format 2", CAP, RLXU_R_FORMAT);
	spec_default(&s); s.format = 0; build(&s, -1);
	expect("format 0", CAP, RLXU_R_FORMAT);
	spec_default(&s); s.header_len = 95; build(&s, -1);
	expect("header_len 95", CAP, RLXU_R_HDRLEN);
	spec_default(&s); s.header_len = 97; build(&s, -1);
	expect("header_len 97", CAP, RLXU_R_HDRLEN);

	spec_default(&s); s.version = 0; build(&s, -1);
	expect("version 0", CAP, RLXU_R_VERSION);
	spec_default(&s); s.version = 0xFFFFFFFFUL; build(&s, -1);
	expect("version 0xFFFFFFFF", CAP, RLXU_R_VERSION);
	spec_default(&s); s.version = 1; build(&s, -1);
	expect("version 1 (the lowest legal)", CAP, RLXU_OK);
	spec_default(&s); s.version = 0xFFFFFFFEUL; build(&s, -1);
	expect("version 0xFFFFFFFE (the highest legal)", CAP, RLXU_OK);

	spec_default(&s); s.payload_len = 0; build(&s, -1);
	expect("payload_len 0", CAP, RLXU_R_PAYLOAD_LEN);
	spec_default(&s); s.payload_len = RLXU_PAYLOAD_MAX + 1; build(&s, -1);
	expect("payload_len 3 MiB + 1", CAP, RLXU_R_PAYLOAD_LEN);
	spec_default(&s); s.payload_len = 0xFFFFFFFFUL; build(&s, -1);
	expect("payload_len 0xFFFFFFFF", CAP, RLXU_R_PAYLOAD_LEN);

	spec_default(&s); s.flags = 1; build(&s, -1);
	expect("flags bit 0 (the reserved LZMA bit)", CAP, RLXU_R_FLAGS);
	spec_default(&s); s.flags = 0x80000000UL; build(&s, -1);
	expect("flags bit 31", CAP, RLXU_R_FLAGS);

	spec_default(&s); build(&s, 0);
	expect("reserved byte 0 non-zero", CAP, RLXU_R_RESERVED);
	spec_default(&s); build(&s, 31);
	expect("reserved byte 31 non-zero", CAP, RLXU_R_RESERVED);

	/* load_addr.  Each case keeps entry_addr inside the payload so the
	 * refusal cannot be the entry check wearing load_addr's name. */
	spec_default(&s); s.load = 0x7FFFF000UL; s.entry = 0x7FFFF000UL; build(&s, -1);
	expect("load_addr below RAM", CAP, RLXU_R_LOAD_ADDR);
	spec_default(&s); s.load = 0x82000000UL; s.entry = 0x82000000UL; build(&s, -1);
	expect("load_addr at the top of RAM", CAP, RLXU_R_LOAD_ADDR);
	spec_default(&s); s.load = 0x81FFFF00UL; s.entry = 0x81FFFF00UL; build(&s, -1);
	expect("load_addr + payload_len past RAM", CAP, RLXU_R_LOAD_ADDR);
	spec_default(&s); s.load = 0xFFFFFF00UL; s.entry = 0xFFFFFF00UL; build(&s, -1);
	expect("load_addr + payload_len wraps", CAP, RLXU_R_LOAD_ADDR);
	spec_default(&s); s.load = 0x80500002UL; s.entry = 0x80500002UL; build(&s, -1);
	expect("load_addr unaligned", CAP, RLXU_R_LOAD_ADDR);

	spec_default(&s); s.entry = 0x804FFFFCUL; build(&s, -1);
	expect("entry_addr below the payload", CAP, RLXU_R_ENTRY_ADDR);
	spec_default(&s); s.entry = 0x80500000UL + PAY; build(&s, -1);
	expect("entry_addr one past the payload", CAP, RLXU_R_ENTRY_ADDR);
	spec_default(&s); s.entry = 0x80500000UL + PAY - 4; build(&s, -1);
	expect("entry_addr at the last word of the payload", CAP, RLXU_OK);
	spec_default(&s); s.entry = 0x80500001UL; build(&s, -1);
	expect("entry_addr unaligned", CAP, RLXU_R_ENTRY_ADDR);

	/* The three destinations inside RAM that must not be written. */
	spec_default(&s); s.load = 0x8180FF00UL; s.entry = 0x8180FF00UL; build(&s, -1);
	expect("destination overlaps rlxboot itself", CAP, RLXU_R_DST_SELF);
	spec_default(&s); s.load = 0x817FFF00UL; s.entry = 0x817FFF00UL; build(&s, -1);
	expect("destination ends inside rlxboot", CAP, RLXU_R_DST_SELF);
	spec_default(&s); s.load = 0x81000080UL; s.entry = 0x81000080UL; build(&s, -1);
	expect("destination overlaps the container", CAP, RLXU_R_DST_BUF);
	spec_default(&s); s.load = 0x80410000UL; s.entry = 0x80410000UL; build(&s, -1);
	expect("destination overlaps the stage-2 loader", CAP, RLXU_R_DST_LOADER);
	/* The positive control on those three: one word below the loader window
	 * and one word above rlxboot's end are both PERMITTED.  A guard is shown
	 * permitting as well as refusing. */
	spec_default(&s); s.load = 0x803FFC00UL; s.entry = 0x803FFC00UL; build(&s, -1);
	expect("destination ending exactly at the loader base", CAP, RLXU_OK);
	spec_default(&s); s.load = 0x81810000UL; s.entry = 0x81810000UL; build(&s, -1);
	expect("destination starting exactly at rlxboot's end", CAP, RLXU_OK);
	spec_default(&s); s.load = 0x80FFFC00UL; s.entry = 0x80FFFC00UL; build(&s, -1);
	expect("destination ending exactly at the container base", CAP, RLXU_OK);

	/* A signature that is not the header's. */
	spec_default(&s); build(&s, -1);
	C[RLXU_HDR_LEN + 10] ^= 0x40;
	expect("a corrupted signature", CAP, RLXU_R_SIG);
	spec_default(&s); build(&s, -1);
	C[28] ^= 0x01;               /* the digest field: inside the signed range */
	expect("a flipped digest bit (signature covers it)", CAP, RLXU_R_SIG);
	spec_default(&s); build(&s, -1);
	C[RLXU_BODY_OFF + 500] ^= 0x08;
	expect("a flipped payload bit", CAP, RLXU_R_DIGEST);
}

/* ------------------------------------------------------ truncation, 0..CAP */

static void test_truncation(void)
{
	struct hdrspec s;
	unsigned long n;
	int bad = 0, first_ok = 0;

	setenv_default(1);
	spec_default(&s);
	build(&s, -1);

	for (n = 0; n < CAP; n++) {
		struct rlxu r;
		if (rlxu_verify(C, n, &env, &r, 0) == RLXU_OK)
			bad++;
		if (r.hashed && r.stage <= RLXU_T_SIG)
			bad++;
	}
	{
		struct rlxu r;
		first_ok = (rlxu_verify(C, CAP, &env, &r, 0) == RLXU_OK);
	}
	printf("      truncation sweep: %lu lengths 0..%d refused, %d accepted at %d\n",
	       (unsigned long)CAP, CAP - 1, first_ok, CAP);
	ok("every truncation 0..160+payload-1 refused", bad == 0);
	ok("the untruncated length accepted (truncation positive control)", first_ok);

	/* More bytes available than the container needs is not a truncation. */
	{
		struct rlxu r;
		ok("extra bytes past the container accepted",
		   rlxu_verify(C, CAP + 64, &env, &r, 0) == RLXU_OK);
	}
	/* A container that does not fit the staging window is a truncation even
	 * when `avail` says otherwise -- the window, not the caller, bounds it. */
	{
		struct rlxu r;
		env.buf_limit = env.buf_base + CAP - 1;
		ok("container past the staging window refused",
		   rlxu_verify(C, CAP, &env, &r, 0) == RLXU_R_TRUNCATED);
		env.buf_limit = 0x81700000UL;
	}
}

/* ------------------------------------------------------ the bit-flip sweep */

static void test_bitflips(void)
{
	struct hdrspec s;
	unsigned long bit;
	unsigned long n_hdr = 0, n_sig = 0, n_pay = 0;
	unsigned long by_stage[8];
	unsigned long accepted = 0, leaked = 0;
	int i;

	for (i = 0; i < 8; i++)
		by_stage[i] = 0;

	setenv_default(1);
	spec_default(&s);
	build(&s, -1);

	/* Pass condition (2) of SPEC-R8a s0 is "one flipped bit anywhere is
	 * rejected", and "anywhere" is a loop.  Three regions, every bit of each:
	 * 96 header bytes, 64 signature bytes, and the whole 1,024-byte payload.
	 */
	for (bit = 0; bit < RLXU_HDR_LEN * 8; bit++) {
		struct rlxu r;
		C[bit >> 3] ^= (unsigned char)(1u << (bit & 7));
		if (rlxu_verify(C, CAP, &env, &r, 0) == RLXU_OK)
			accepted++;
		else if (r.stage <= RLXU_T_SIG && (r.hashed || r.copied))
			leaked++;
		if (r.stage < 8) by_stage[r.stage]++;
		C[bit >> 3] ^= (unsigned char)(1u << (bit & 7));
		n_hdr++;
	}
	for (bit = 0; bit < RLXU_SIG_LEN * 8; bit++) {
		struct rlxu r;
		unsigned long o = RLXU_HDR_LEN * 8 + bit;
		C[o >> 3] ^= (unsigned char)(1u << (o & 7));
		if (rlxu_verify(C, CAP, &env, &r, 0) == RLXU_OK)
			accepted++;
		else if (r.stage <= RLXU_T_SIG && (r.hashed || r.copied))
			leaked++;
		if (r.stage < 8) by_stage[r.stage]++;
		C[o >> 3] ^= (unsigned char)(1u << (o & 7));
		n_sig++;
	}
	for (bit = 0; bit < PAY * 8; bit++) {
		struct rlxu r;
		unsigned long o = RLXU_BODY_OFF * 8 + bit;
		C[o >> 3] ^= (unsigned char)(1u << (o & 7));
		if (rlxu_verify(C, CAP, &env, &r, 0) == RLXU_OK)
			accepted++;
		if (r.stage < 8) by_stage[r.stage]++;
		C[o >> 3] ^= (unsigned char)(1u << (o & 7));
		n_pay++;
	}

	printf("      bit-flip sweep: %lu header + %lu signature + %lu payload"
	       " = %lu flips\n", n_hdr, n_sig, n_pay, n_hdr + n_sig + n_pay);
	printf("      refused at stage hdr=%lu bound=%lu sig=%lu digest=%lu ver=%lu\n",
	       by_stage[RLXU_T_HDR], by_stage[RLXU_T_BOUND], by_stage[RLXU_T_SIG],
	       by_stage[RLXU_T_DIGEST], by_stage[RLXU_T_VER]);
	ok("every single-bit flip in header, signature and payload refused",
	   accepted == 0);
	ok("no refusal at or before the signature had hashed a payload byte",
	   leaked == 0);
	/* The positive control: after the sweep has flipped and restored every
	 * bit, the container must still verify.  Without it a sweep over a
	 * container that was broken from the start would read as a clean pass. */
	{
		struct rlxu r;
		ok("the container still verifies after the sweep (positive control)",
		   rlxu_verify(C, CAP, &env, &r, 0) == RLXU_OK);
	}
	/* And the sweep must have exercised more than one refusal stage, or it
	 * is one test repeated 9,472 times. */
	ok("the sweep reached at least three different refusal stages",
	   (by_stage[RLXU_T_HDR] > 0) + (by_stage[RLXU_T_BOUND] > 0)
	   + (by_stage[RLXU_T_SIG] > 0) + (by_stage[RLXU_T_DIGEST] > 0) >= 3);
}

/* -------------------------------------------------------- the order of it */

static int rep_stage[8], rep_reason[8], rep_n;

static void recorder(const struct rlxu *r, int stage, int reason)
{
	(void)r;
	if (rep_n < 8) {
		rep_stage[rep_n] = stage;
		rep_reason[rep_n] = reason;
		rep_n++;
	}
}

static void test_order(void)
{
	struct hdrspec s;
	struct rlxu r;

	setenv_default(1);

	/* THE ONE TEST THAT CAN SEE A REORDERED VERIFICATION.  Reordering steps
	 * 3 and 4 changes no accept/reject verdict, so no functional case catches
	 * it.  What changes is the sequence of stages that ran and whether a
	 * payload byte was hashed before the signature verified. */
	spec_default(&s); build(&s, -1);
	rlxu_verify(C, CAP, &env, &r, 0);
	ok("accepted container traced hdr,bound,sig,digest,ver",
	   r.trace_n == 5 && r.trace[0] == RLXU_T_HDR && r.trace[1] == RLXU_T_BOUND
	   && r.trace[2] == RLXU_T_SIG && r.trace[3] == RLXU_T_DIGEST
	   && r.trace[4] == RLXU_T_VER);
	ok("accepted container hashed exactly payload_len bytes",
	   r.hashed == PAY);
	ok("rlxu_verify copies nothing, ever", r.copied == 0);

	C[RLXU_HDR_LEN + 3] ^= 0x10;
	rlxu_verify(C, CAP, &env, &r, 0);
	ok("bad signature traced hdr,bound,sig and stopped",
	   r.trace_n == 3 && r.trace[2] == RLXU_T_SIG);
	ok("bad signature hashed ZERO payload bytes", r.hashed == 0);

	spec_default(&s); s.load = 0x8180FF00UL; s.entry = 0x8180FF00UL; build(&s, -1);
	rlxu_verify(C, CAP, &env, &r, 0);
	ok("an overlapping destination never reaches the signature",
	   r.trace_n == 2 && r.trace[1] == RLXU_T_BOUND && r.hashed == 0);

	/* The report callback is what the device prints from, so it is in the
	 * trust path and must not be untested code.  It must fire once per stage
	 * entered, in the same order as the trace, and with the same reasons. */
	rep_n = 0;
	spec_default(&s); build(&s, -1);
	rlxu_verify(C, CAP, &env, &r, recorder);
	ok("the report callback fired five times, in stage order",
	   rep_n == 5 && rep_stage[0] == RLXU_T_HDR && rep_stage[1] == RLXU_T_BOUND
	   && rep_stage[2] == RLXU_T_SIG && rep_stage[3] == RLXU_T_DIGEST
	   && rep_stage[4] == RLXU_T_VER
	   && rep_reason[0] == RLXU_OK && rep_reason[4] == RLXU_OK);

	rep_n = 0;
	spec_default(&s); s.version = 0; build(&s, -1);
	rlxu_verify(C, CAP, &env, &r, recorder);
	ok("the callback stops at the failing stage and names it",
	   rep_n == 2 && rep_stage[1] == RLXU_T_BOUND
	   && rep_reason[1] == RLXU_R_VERSION);
}

/* ----------------------------------------------------------- the counter */

static void bitmap_with(unsigned char *bm, unsigned long cleared)
{
	unsigned long i;

	for (i = 0; i < RLXU_CTR_BYTES; i++)
		bm[i] = 0xFF;
	for (i = 0; i < cleared && i < RLXU_CTR_BITS; i++)
		bm[i >> 3] &= (unsigned char)~(1u << (7 - (i & 7)));
}

static void test_counter(void)
{
	unsigned char bm[RLXU_CTR_BYTES];
	static const unsigned long cases[] = { 0, 1, 7, 8, 9, 4095 };
	unsigned long i;
	int mal;
	char nm[96];

	for (i = 0; i < sizeof cases / sizeof cases[0]; i++) {
		unsigned long got;
		bitmap_with(bm, cases[i]);
		got = rlxu_counter_from_bitmap(bm, &mal);
		sprintf(nm, "counter bitmap with %lu bits cleared reads %lu",
		        cases[i], cases[i]);
		ok(nm, got == cases[i] && mal == 0);
	}
	/* The shape of the first byte at each of those, so a reader can check the
	 * bit order rather than trust it: MSB first. */
	bitmap_with(bm, 1);
	ok("one bit cleared leaves 0x7F in byte 0 (MSB first)", bm[0] == 0x7F);
	bitmap_with(bm, 8);
	ok("eight bits cleared leave 0x00,0xFF", bm[0] == 0x00 && bm[1] == 0xFF);
	bitmap_with(bm, 9);
	ok("nine bits cleared leave 0x00,0x7F", bm[0] == 0x00 && bm[1] == 0x7F);

	memset(bm, 0xFF, sizeof bm);
	ok("an all-0xFF (factory erased) bitmap reads 0",
	   rlxu_counter_from_bitmap(bm, &mal) == 0 && mal == 0);
	memset(bm, 0x00, sizeof bm);
	ok("an all-zero bitmap reads 4096",
	   rlxu_counter_from_bitmap(bm, &mal) == RLXU_CTR_BITS && mal == 0);

	/* Malformed: a zero bit after the first one bit.  The value returned is
	 * the TOTAL zero count, which is above the leading run, so a malformed
	 * bitmap can only refuse an update and never accept a rollback. */
	bitmap_with(bm, 4);
	bm[10] = 0x00;
	{
		unsigned long got = rlxu_counter_from_bitmap(bm, &mal);
		ok("a malformed bitmap is flagged and resolves upward",
		   mal == 1 && got == 12);
	}
}

static void test_rollback(void)
{
	struct hdrspec s;

	/* THE BOUNDARY, spelled out in the test as well as in container.c:
	 * below is refused, EQUAL IS ACCEPTED, above is accepted. */
	setenv_default(5);
	spec_default(&s); s.version = 4; build(&s, -1);
	expect("version 4 against counter 5", CAP, RLXU_R_ROLLBACK);
	spec_default(&s); s.version = 5; build(&s, -1);
	expect("version 5 against counter 5 (EQUAL IS ACCEPTED)", CAP, RLXU_OK);
	spec_default(&s); s.version = 6; build(&s, -1);
	expect("version 6 against counter 5", CAP, RLXU_OK);

	setenv_default(0);
	spec_default(&s); s.version = 1; build(&s, -1);
	expect("version 1 against an erased counter 0", CAP, RLXU_OK);

	setenv_default(RLXU_CTR_BITS);
	spec_default(&s); s.version = 4095; build(&s, -1);
	expect("version 4095 against an exhausted counter 4096", CAP, RLXU_R_ROLLBACK);
	spec_default(&s); s.version = 4096; build(&s, -1);
	expect("version 4096 against an exhausted counter 4096", CAP, RLXU_OK);
	setenv_default(1);
}

int main(void)
{
	unsigned char pk[32];

	memcpy(sk, rlxboot_devseed, 32);
	rlx_ed25519_pubkey_from_seed(pk, rlxboot_devseed);
	memcpy(sk + 32, pk, 32);

	/* devkey.h is a transcription of a derived value, so it is checked
	 * against a fresh derivation before anything else runs. */
	ok("devkey.h matches the key derived from the 0x42 seed",
	   memcmp(pk, rlxboot_devkey, 32) == 0);

	test_fields();
	test_truncation();
	test_bitflips();
	test_order();
	test_counter();
	test_rollback();

	printf("t_container %d checks, %d failures\n", checks, failures);
	return failures ? 1 : 0;
}
