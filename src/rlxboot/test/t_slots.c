/* src/rlxboot/test/t_slots.c -- the slot choice, R8b spec D4.  rlxfw's own code.
 *
 * Drives `slots.c` and `container.c` -- the translation units the device runs --
 * against a 4 MiB array standing in for the part and two host arrays standing
 * in for the RAM buffers.  The device numbers (0x070000, 0x81000000, ...) are
 * the device's; only the pointers are the host's.
 *
 * THE RULE THIS FILE FOLLOWS is `t_container.c`'s: every container is built
 * and SIGNED here, so a slot that is refused is refused for the reason the case
 * names and not because nothing in it was ever valid.  Every case asserts the
 * decision, both verdicts by name, and the console lines an operator would read
 * -- exact lines, not substrings, because a parser on the bench will match
 * exact lines.
 *
 * WHAT IT CANNOT SEE: `main.c`'s halt and jump (the qemu payload run does those),
 * the flash window itself, the cache, and any timing.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../rlxboot.h"
#include "../container.h"
#include "../slots.h"
#include "../sha256b.h"
#include "../devkey.h"
#include "../../lib/ed25519.h"

#define CHIP    0x400000UL
#define GUARDW  16                       /* guard words each side of a buffer */
#define GUARD   0x5A5AA5A5u
#define STALE   0xC3C3C3C3u              /* what a buffer holds before a run  */
#define SLOTW   (RLXB_SLOT_SIZE / 4)

static unsigned int flash_w[CHIP / 4];
static unsigned int bufa_w[GUARDW + SLOTW + GUARDW];
static unsigned int bufb_w[GUARDW + SLOTW + GUARDW];
#define FLASH ((unsigned char *)flash_w)

static unsigned char sk[64];
static int failures, checks;
static struct rlxu_env env;
static struct rlxb_slot A, B;

/* ------------------------------------------------------------- the console */

static char con[1 << 16];
static unsigned long con_n;

static void cap(int c)
{
	if (con_n < sizeof con - 1) {
		con[con_n++] = (char)c;
		con[con_n] = 0;
	}
}

static const struct rlxb_io io = { cap };

/* The 0-based number of the first whole line equal to `want` (CR stripped),
 * or -1. */
static int line_no(const char *want)
{
	const char *p = con;
	size_t n = strlen(want);
	int k = 0;

	while (*p) {
		const char *e = strchr(p, '\n');
		size_t len = e ? (size_t)(e - p) : strlen(p);

		if (len && p[len - 1] == '\r')
			len--;
		if (len == n && memcmp(p, want, n) == 0)
			return k;
		if (!e)
			break;
		p = e + 1;
		k++;
	}
	return -1;
}

static int has_line(const char *want)
{
	return line_no(want) >= 0;
}

/* 1 if any line begins with `pre`. */
static int has_prefix(const char *pre)
{
	const char *p = con;
	size_t n = strlen(pre);

	while (*p) {
		const char *e = strchr(p, '\n');

		if (strncmp(p, pre, n) == 0)
			return 1;
		if (!e)
			break;
		p = e + 1;
	}
	return 0;
}

/* ------------------------------------------------------------ the plumbing */

static void ok(const char *what, int good)
{
	checks++;
	if (!good) {
		failures++;
		printf("FAIL  %s\n", what);
		printf("      console was:\n%s", con);
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

static void slot_init(struct rlxb_slot *s, char name, unsigned long off,
                      unsigned long bufaddr, unsigned int *bufw)
{
	memset(s, 0, sizeof *s);
	s->name      = name;
	s->flash_off = off;
	s->size      = RLXB_SLOT_SIZE;
	s->buf_addr  = bufaddr;
	s->src       = flash_w + off / 4;
	s->buf       = bufw + GUARDW;
	s->reason    = -1;
}

/* A fresh part (every byte 0xFF, as erased NOR reads), two buffers holding a
 * stale pattern inside their guards, the device's memory map, and an empty
 * console.  The base env's buffer window is ZERO and its flash comparison is
 * NONE on purpose: `slots.c` must replace all four, and if it forgot one, every
 * container would be refused and every accepting case below would go red. */
static void reset(unsigned long counter)
{
	unsigned long i;

	memset(flash_w, 0xFF, sizeof flash_w);
	for (i = 0; i < GUARDW + SLOTW + GUARDW; i++) {
		int g = (i < GUARDW || i >= GUARDW + SLOTW);
		bufa_w[i] = g ? GUARD : STALE;
		bufb_w[i] = g ? GUARD : STALE;
	}
	slot_init(&A, 'A', RLXB_SLOT_A_FLASH, RLXB_SLOT_A_BUF, bufa_w);
	slot_init(&B, 'B', RLXB_SLOT_B_FLASH, RLXB_SLOT_B_BUF, bufb_w);

	env.ram_base   = RLXB_RAM_BASE;
	env.ram_end    = RLXB_RAM_END;
	env.self_base  = RLXB_SELF;
	env.self_end   = RLXB_SELF + 0x10000UL;
	env.buf_base   = 0;
	env.buf_limit  = 0;
	env.ldr_base   = RLXB_LDR_BASE;
	env.ldr_end    = RLXB_LDR_END;
	env.counter    = counter;
	env.write_at   = RLXU_FLASH_NONE;
	env.write_form = RLXU_FORM_NONE;
	env.pk         = rlxboot_devkey;

	con_n = 0;
	con[0] = 0;
}

static int guards_intact(void)
{
	unsigned long i;

	for (i = 0; i < GUARDW; i++)
		if (bufa_w[i] != GUARD || bufb_w[i] != GUARD
		    || bufa_w[GUARDW + SLOTW + i] != GUARD
		    || bufb_w[GUARDW + SLOTW + i] != GUARD)
			return 0;
	return 1;
}

/* Build and sign a container of `n` payload bytes at `dst`, declaring
 * `flash_at` in `form`.  `seed` makes two containers' payloads differ.
 * Returns the container's length. */
static unsigned long mk(unsigned char *dst, unsigned long ver, unsigned long n,
                        unsigned int seed, unsigned long flash_at,
                        unsigned long form)
{
	unsigned char d[32];
	unsigned long i;

	for (i = 0; i < n; i++)
		dst[RLXU_BODY_OFF + i] = (unsigned char)(i * 131UL + seed * 29UL + 1UL);
	memset(dst, 0, RLXU_BODY_OFF);
	be32(dst + 0, RLXU_MAGIC);
	be16(dst + 4, RLXU_FORMAT);
	be16(dst + 6, RLXU_HDR_LEN);
	be32(dst + 8, ver);
	be32(dst + 12, n);
	be32(dst + 16, 0x80500000UL);
	be32(dst + 20, 0x80500000UL);
	be32(dst + 24, 0);
	sha256b(d, dst + RLXU_BODY_OFF, n);
	memcpy(dst + 28, d, 32);
	be32(dst + 60, 0xAABBCCDDUL);
	be32(dst + RLXU_FLASH_OFF, flash_at);
	be32(dst + RLXU_FORM_OFF, form);
	rlx_ed25519_sign(dst + RLXU_HDR_LEN, dst, RLXU_HDR_LEN, sk);
	return RLXU_BODY_OFF + n;
}

/* A container signed for the slot it is placed in -- what D13's P, Q and R are. */
static unsigned long put(struct rlxb_slot *s, unsigned long ver, unsigned long n,
                         unsigned int seed)
{
	return mk(FLASH + s->flash_off, ver, n, seed, s->flash_off,
	          RLXU_FORM_WHOLE);
}

static struct rlxb_slot *run(void)
{
	return rlxb_select(&A, &B, &env, 0, &io);
}

/* The READ line, dots included: one per 64 KiB the copy crosses. */
static void read_line(char *out, const struct rlxb_slot *s, unsigned long n)
{
	unsigned long k, dots = n / RLXB_TICK_BYTES;
	int m = sprintf(out, "RLXBOOT-READ %c flash=%08lx buf=%08lx n=%lu",
	                s->name, s->flash_off, s->buf_addr, n);

	if (dots) {
		out[m++] = ' ';
		for (k = 0; k < dots; k++)
			out[m++] = '.';
	}
	out[m] = 0;
}

/* sha256 of the bytes the boot would copy, against the verified digest. */
static int boot_bytes_match_digest(const struct rlxb_slot *w)
{
	unsigned char d[32];

	sha256b(d, rlxb_boot_body(w), w->r.payload_len);
	return memcmp(d, w->r.digest, 32) == 0;
}

/* ------------------------------------------------------- the D4 cases */

static void test_a_only(void)
{
	struct rlxb_slot *w;
	char l[256];
	unsigned long n;

	reset(0);
	n = put(&A, 1, 100000, 1);
	w = run();
	ok("A only: A boots", w == &A);
	ok("A only: A ok, B refused magic (erased)",
	   A.reason == RLXU_OK && B.reason == RLXU_R_MAGIC);
	read_line(l, &A, n);
	ok("A only: READ A names the slot, the buffer, n and one dot per 64 KiB",
	   has_line(l));
	read_line(l, &B, RLXU_BODY_OFF);
	ok("A only: READ B is the 160-byte prefix and no more", has_line(l));
	ok("A only: VERDICT A ok ver=1, VERDICT B bad=magic, SLOT A",
	   has_line("RLXBOOT-VERDICT A ok ver=1")
	   && has_line("RLXBOOT-VERDICT B bad=magic")
	   && has_line("RLXBOOT-SLOT A") && !has_prefix("RLXBOOT-HALT"));
	ok("A only: the lines come in the order A read, A verdict, B read, "
	   "B verdict, choice",
	   line_no("RLXBOOT-VERDICT A ok ver=1") < line_no(l)
	   && line_no(l) < line_no("RLXBOOT-VERDICT B bad=magic")
	   && line_no("RLXBOOT-VERDICT B bad=magic") < line_no("RLXBOOT-SLOT A"));
	ok("A only: buffers' guards intact", guards_intact());
}

static void test_b_only(void)
{
	struct rlxb_slot *w;

	reset(0);
	put(&B, 1, 70000, 2);
	w = run();
	ok("B only: B boots", w == &B);
	ok("B only: A refused magic, B ok",
	   A.reason == RLXU_R_MAGIC && B.reason == RLXU_OK);
	ok("B only: SLOT B, no HALT",
	   has_line("RLXBOOT-VERDICT A bad=magic")
	   && has_line("RLXBOOT-VERDICT B ok ver=1")
	   && has_line("RLXBOOT-SLOT B") && !has_prefix("RLXBOOT-HALT"));
}

static void test_a_higher(void)
{
	struct rlxb_slot *w;

	reset(0);
	put(&A, 3, 50000, 1);
	put(&B, 2, 60000, 2);
	w = run();
	ok("both valid, A higher (3 > 2): A boots", w == &A);
	ok("both valid, A higher: both verdicts ok, SLOT A",
	   has_line("RLXBOOT-VERDICT A ok ver=3")
	   && has_line("RLXBOOT-VERDICT B ok ver=2")
	   && has_line("RLXBOOT-SLOT A"));
}

static void test_b_higher(void)
{
	struct rlxb_slot *w;

	reset(0);
	put(&A, 2, 50000, 1);
	put(&B, 3, 60000, 2);
	w = run();
	ok("both valid, B higher (3 > 2): B boots", w == &B);
	ok("both valid, B higher: both verdicts ok, SLOT B",
	   has_line("RLXBOOT-VERDICT A ok ver=2")
	   && has_line("RLXBOOT-VERDICT B ok ver=3")
	   && has_line("RLXBOOT-SLOT B"));
	reset(0);
	put(&A, 1, 4000, 1);
	put(&B, RLXU_VER_MAX, 4000, 2);
	w = run();
	ok("both valid, B at the highest legal version against A at 1: B",
	   w == &B && has_line("RLXBOOT-VERDICT B ok ver=4294967294"));
}

static void test_tie(void)
{
	struct rlxb_slot *w;

	reset(0);
	put(&A, 2, 50000, 1);
	put(&B, 2, 60000, 2);
	w = run();
	ok("tie (2 = 2): A boots", w == &A);
	ok("tie: both verdicts ok ver=2, SLOT A",
	   has_line("RLXBOOT-VERDICT A ok ver=2")
	   && has_line("RLXBOOT-VERDICT B ok ver=2")
	   && has_line("RLXBOOT-SLOT A"));
	ok("tie: the bytes the boot copies are A's, not B's",
	   w && boot_bytes_match_digest(w) && w->r.payload_len == 50000);
}

static void test_neither(void)
{
	struct rlxb_slot *w;
	unsigned long n;

	reset(0);
	n = put(&B, 4, 60000, 2);
	FLASH[B.flash_off + n - 1] ^= 0x01;      /* the last payload byte */
	w = run();
	ok("neither: nothing boots", w == 0);
	ok("neither: A refused magic, B refused digest",
	   A.reason == RLXU_R_MAGIC && B.reason == RLXU_R_DIGEST);
	ok("neither: both verdicts and the HALT line with both reasons, no SLOT",
	   has_line("RLXBOOT-VERDICT A bad=magic")
	   && has_line("RLXBOOT-VERDICT B bad=digest")
	   && has_line("RLXBOOT-HALT A=magic B=digest")
	   && !has_prefix("RLXBOOT-SLOT"));
	ok("neither: the HALT line comes after both verdicts",
	   line_no("RLXBOOT-HALT A=magic B=digest")
	   > line_no("RLXBOOT-VERDICT B bad=digest")
	   && line_no("RLXBOOT-VERDICT B bad=digest")
	   > line_no("RLXBOOT-VERDICT A bad=magic"));

	reset(0);
	w = run();
	ok("both erased: nothing boots, HALT A=magic B=magic",
	   w == 0 && has_line("RLXBOOT-HALT A=magic B=magic"));
}

/* D5 programs a slot's first page LAST, so a cut anywhere inside the write
 * leaves the header page erased while the body may be partly there. */
static void test_torn_header(void)
{
	struct rlxb_slot *w;
	char l[256];

	reset(0);
	put(&A, 5, 200000, 1);
	memset(FLASH + A.flash_off, 0xFF, 256);
	put(&B, 1, 60000, 2);
	w = run();
	ok("torn header in A (first page 0xFF), B valid at a LOWER version: B",
	   w == &B);
	ok("torn header: A refused magic after reading the 160-byte prefix only",
	   A.reason == RLXU_R_MAGIC && A.copied == RLXU_BODY_OFF);
	read_line(l, &A, RLXU_BODY_OFF);
	ok("torn header: READ A says n=160 and has no dots", has_line(l));
	ok("torn header: VERDICT A bad=magic, SLOT B",
	   has_line("RLXBOOT-VERDICT A bad=magic") && has_line("RLXBOOT-SLOT B"));

	reset(0);
	put(&A, 5, 200000, 1);
	memset(FLASH + A.flash_off, 0xFF, 256);
	w = run();
	ok("torn header in A, B erased: HALT A=magic B=magic",
	   w == 0 && has_line("RLXBOOT-HALT A=magic B=magic"));
}

static void test_torn_body(void)
{
	struct rlxb_slot *w;
	unsigned long n;

	reset(0);
	put(&A, 1, 60000, 1);
	n = put(&B, 5, 300000, 2);
	memset(FLASH + B.flash_off + n - 4096, 0xFF, 4096);   /* last 4 KiB erased */
	w = run();
	ok("torn body in B (header intact, last 4 KiB 0xFF), A valid lower: A",
	   w == &A);
	ok("torn body: B refused digest -- its higher version did not count",
	   B.reason == RLXU_R_DIGEST && B.copied == ((n + 3UL) & ~3UL));
	ok("torn body: VERDICT B bad=digest, SLOT A",
	   has_line("RLXBOOT-VERDICT B bad=digest") && has_line("RLXBOOT-SLOT A"));
}

/* "VERIFY THE BYTES YOU BOOT."  Four separate claims, each its own check. */
static void test_winner_bytes(void)
{
	struct rlxb_slot *w;
	unsigned long na, nb;
	const unsigned char *body;
	unsigned char save[RLXU_BODY_OFF];

	reset(0);
	na = put(&A, 1, 90000, 1);
	nb = put(&B, 2, 120000, 2);
	w = run();
	ok("winner bytes: B (version 2) wins", w == &B);
	if (w != &B)
		return;
	body = rlxb_boot_body(w);
	ok("winner bytes: the verdict's digest pointer is INSIDE B's buffer -- "
	   "the copy was verified, not the flash",
	   w->r.digest == (const unsigned char *)B.buf + 28);
	ok("winner bytes: the boot copies from B's buffer + 160, not from flash",
	   body == (const unsigned char *)B.buf + RLXU_BODY_OFF
	   && !(body >= FLASH && body < FLASH + CHIP));
	ok("winner bytes: B's buffer holds slot B's bytes",
	   memcmp(B.buf, FLASH + B.flash_off, nb) == 0);
	ok("winner bytes: the bytes the boot copies hash to the verified digest",
	   boot_bytes_match_digest(w));
	/* Flash changes after the verdict.  What the boot copies must not. */
	memset(FLASH + B.flash_off, 0x00, nb);
	ok("winner bytes: still the verified bytes after slot B's flash changed",
	   boot_bytes_match_digest(w));
	/* B's copy ran after A's verdict; A's buffer must still be A's. */
	ok("winner bytes: B's copy did not touch A's buffer",
	   memcmp(A.buf, FLASH + A.flash_off, na) == 0
	   && A.buf[(na + 3UL) / 4UL] == STALE);
	ok("winner bytes: nothing written past either copy, guards intact",
	   B.buf[(nb + 3UL) / 4UL] == STALE && guards_intact());

	/* And the same with A winning, so neither buffer is special. */
	reset(0);
	na = put(&A, 9, 90000, 3);
	put(&B, 2, 120000, 4);
	w = run();
	memcpy(save, FLASH + A.flash_off, sizeof save);
	memset(FLASH + A.flash_off, 0xFF, na);
	ok("winner bytes: A wins, and its boot bytes survive A's flash being erased",
	   w == &A && w->r.digest == (const unsigned char *)A.buf + 28
	   && boot_bytes_match_digest(w)
	   && memcmp(A.buf, save, sizeof save) == 0);
}

/* An unverified header's version is an unauthenticated field and must not win. */
static void test_unverified_version(void)
{
	struct rlxb_slot *w;

	reset(0);
	put(&A, 1, 40000, 1);
	put(&B, 9, 40000, 2);
	FLASH[B.flash_off + RLXU_HDR_LEN + 7] ^= 0x20;    /* the signature */
	w = run();
	ok("B claims version 9 with a broken signature, A is 1: A boots",
	   w == &A && B.reason == RLXU_R_SIG
	   && has_line("RLXBOOT-VERDICT B bad=sig") && has_line("RLXBOOT-SLOT A"));

	reset(0);
	put(&A, 1, 40000, 1);
	put(&B, 1, 40000, 2);
	be32(FLASH + B.flash_off + 8, 9);                  /* version, unsigned */
	w = run();
	ok("B's version raised to 9 after signing: refused sig, A boots",
	   w == &A && B.reason == RLXU_R_SIG);
}

static void test_rollback(void)
{
	struct rlxb_slot *w;

	reset(5);
	put(&A, 4, 40000, 1);
	put(&B, 6, 40000, 2);
	w = run();
	ok("counter 5: A (4) refused rollback, B (6) boots",
	   w == &B && A.reason == RLXU_R_ROLLBACK
	   && has_line("RLXBOOT-VERDICT A bad=rollback"));

	reset(5);
	put(&A, 5, 40000, 1);
	put(&B, 4, 40000, 2);
	w = run();
	ok("counter 5: A (5, equal) accepted, B (4) refused: A",
	   w == &A && B.reason == RLXU_R_ROLLBACK);

	reset(7);
	put(&A, 4, 40000, 1);
	put(&B, 6, 40000, 2);
	w = run();
	ok("counter 7: both below it: HALT A=rollback B=rollback",
	   w == 0 && has_line("RLXBOOT-HALT A=rollback B=rollback"));
}

/* DECISION: the signed destination must name the slot it was read from. */
static void test_wrong_slot(void)
{
	struct rlxb_slot *w;

	reset(0);
	mk(FLASH + A.flash_off, 3, 40000, 1, RLXB_SLOT_B_FLASH, RLXU_FORM_WHOLE);
	w = run();
	ok("a container signed for slot B found in slot A: refused flash_match",
	   w == 0 && A.reason == RLXU_R_FLASH_MATCH
	   && has_line("RLXBOOT-HALT A=flash_match B=magic"));

	reset(0);
	mk(FLASH + A.flash_off, 3, 40000, 1, RLXU_FLASH_NONE, RLXU_FORM_NONE);
	w = run();
	ok("an undeclared container (flash_at none) in slot A: refused flash_match",
	   w == 0 && A.reason == RLXU_R_FLASH_MATCH);

	reset(0);
	mk(FLASH + A.flash_off, 3, 40000, 1, RLXB_SLOT_A_FLASH, RLXU_FORM_PAYLOAD);
	w = run();
	ok("slot A's base but form PAYL: refused flash_match",
	   w == 0 && A.reason == RLXU_R_FLASH_MATCH);

	reset(0);
	mk(FLASH + A.flash_off, 3, 40000, 1, RLXB_SLOT_A_FLASH, RLXU_FORM_WHOLE);
	mk(FLASH + B.flash_off, 2, 40000, 2, RLXB_SLOT_A_FLASH, RLXU_FORM_WHOLE);
	w = run();
	ok("positive control: A's own declaration boots; the same declaration "
	   "found in B is refused", w == &A && B.reason == RLXU_R_FLASH_MATCH);
}

/* MEM-17: DRAM survives a power cycle.  A valid container left in a buffer by
 * an earlier boot must not be what this boot verifies. */
static void test_stale_ram(void)
{
	struct rlxb_slot *w;

	reset(0);
	mk((unsigned char *)A.buf, 9, 40000, 1, RLXB_SLOT_A_FLASH, RLXU_FORM_WHOLE);
	mk((unsigned char *)B.buf, 9, 40000, 2, RLXB_SLOT_B_FLASH, RLXU_FORM_WHOLE);
	w = run();
	ok("stale valid containers in both buffers, both slots erased: HALT",
	   w == 0 && has_line("RLXBOOT-HALT A=magic B=magic"));
}

/* D21: in BOOT=slots the counter comes from the flash bitmap ONLY.  This suite
 * links `flashread.c` built BOOT=slots; `t_container` links it built BOOT=ram
 * and shows R8a's RAM-first order still holds there. */
static void bits(unsigned char *bm, unsigned long cleared)
{
	unsigned long i;

	memset(bm, 0xFF, RLXU_CTR_BYTES);
	for (i = 0; i < cleared && i < RLXU_CTR_BITS; i++)
		bm[i >> 3] &= (unsigned char)~(1u << (7 - (i & 7)));
}

static void test_ctr_flash_only(void)
{
	static unsigned int ram[1 + RLXU_CTR_BYTES / 4];
	unsigned char flash[RLXU_CTR_BYTES], out[RLXU_CTR_BYTES];
	struct rlxb_slot *w;
	int mal = 0, src;

	ram[0] = RLXU_CTR_RAM_MAGIC;                 /* valid-looking: RCNT, 9 */
	bits((unsigned char *)(ram + 1), 9);
	bits(flash, 0);
	src = rlxb_counter_read(out, ram, flash);
	ok("BOOT=slots ignores a valid-looking RCNT block (9): flash decides, 0",
	   src == 0 && rlxu_counter_from_bitmap(out, &mal) == 0 && mal == 0);

	bits((unsigned char *)(ram + 1), RLXU_CTR_BITS);   /* planted: 4096 */
	src = rlxb_counter_read(out, ram, flash);
	ok("BOOT=slots ignores a planted RCNT reading 4096, which would refuse "
	   "every slot", src == 0 && rlxu_counter_from_bitmap(out, &mal) == 0);

	bits(flash, 8);
	bits((unsigned char *)(ram + 1), 0);              /* RAM says 0 */
	src = rlxb_counter_read(out, ram, flash);
	ok("BOOT=slots honours the flash bitmap (8) over an RCNT saying 0",
	   src == 0 && rlxu_counter_from_bitmap(out, &mal) == 8);

	/* The consequence for the choice.  RAM says 9, flash says 0: slot A at
	 * version 7 boots.  Were the RAM block honoured, A would be refused
	 * rollback and the board would halt. */
	reset(0);
	bits((unsigned char *)(ram + 1), 9);
	bits(flash, 0);
	rlxb_counter_read(out, ram, flash);
	env.counter = rlxu_counter_from_bitmap(out, &mal);
	put(&A, 7, 30000, 1);
	w = run();
	ok("RAM says 9, flash says 0: slot A at version 7 boots",
	   w == &A && A.reason == RLXU_OK && env.counter == 0);
}

static void test_bounds(void)
{
	struct rlxb_slot *w;
	char l[256];
	unsigned long n;

	reset(0);
	n = put(&A, 1, RLXB_SLOT_SIZE - RLXU_BODY_OFF, 1);
	w = run();
	read_line(l, &A, RLXB_SLOT_SIZE);
	ok("a container that fills slot A exactly: accepted, 18 dots",
	   w == &A && n == RLXB_SLOT_SIZE && A.copied == RLXB_SLOT_SIZE
	   && has_line(l));

	reset(0);
	put(&A, 1, 1000, 1);
	be32(FLASH + A.flash_off + 12, RLXB_SLOT_SIZE - RLXU_BODY_OFF + 1);
	w = run();
	ok("payload_len one byte past the slot: 160 bytes read, refused truncated",
	   w == 0 && A.copied == RLXU_BODY_OFF && A.reason == RLXU_R_TRUNCATED);

	reset(0);
	put(&A, 1, 1000, 1);
	be32(FLASH + A.flash_off + 12, RLXU_PAYLOAD_MAX + 1);
	w = run();
	ok("payload_len past 3 MiB: 160 bytes read, refused payload_len",
	   w == 0 && A.copied == RLXU_BODY_OFF && A.reason == RLXU_R_PAYLOAD_LEN);

	reset(0);
	n = put(&A, 1, 1001, 1);
	w = run();
	ok("an odd length is copied to the next word and no further",
	   w == &A && A.copied == ((n + 3UL) & ~3UL)
	   && A.buf[A.copied / 4] == STALE && guards_intact());
}

/* The stage callbacks: A's five, then B's five. */
static int rec_stage[16], rec_n;

static void recorder(const struct rlxu *r, int stage, int reason)
{
	(void)r;
	(void)reason;
	if (rec_n < 16)
		rec_stage[rec_n++] = stage;
}

static void test_stage_order(void)
{
	static const int want[10] = {
		RLXU_T_HDR, RLXU_T_BOUND, RLXU_T_SIG, RLXU_T_DIGEST, RLXU_T_VER,
		RLXU_T_HDR, RLXU_T_BOUND, RLXU_T_SIG, RLXU_T_DIGEST, RLXU_T_VER
	};
	int i, good;

	reset(0);
	put(&A, 1, 30000, 1);
	put(&B, 2, 30000, 2);
	rec_n = 0;
	rlxb_select(&A, &B, &env, recorder, &io);
	good = (rec_n == 10);
	for (i = 0; good && i < 10; i++)
		good = (rec_stage[i] == want[i]);
	ok("the stage callback fires for A's five stages, then B's five", good);
}

/* `rlxb_choose` alone, as a table: (A ok?, A ver, B ok?, B ver) -> winner. */
static void test_choose_table(void)
{
	static const struct {
		int oka; unsigned long va; int okb; unsigned long vb; char want;
	} t[] = {
		{ 1, 1, 1, 1, 'A' }, { 1, 2, 1, 1, 'A' }, { 1, 1, 1, 2, 'B' },
		{ 1, 7, 0, 9, 'A' }, { 0, 9, 1, 7, 'B' }, { 0, 1, 0, 1, 0 },
		{ 1, RLXU_VER_MAX, 1, RLXU_VER_MAX, 'A' },
		{ 1, 1, 1, RLXU_VER_MAX, 'B' },
	};
	unsigned long i;
	int bad = 0;

	for (i = 0; i < sizeof t / sizeof t[0]; i++) {
		struct rlxb_slot *w;
		char got;

		reset(0);
		A.reason = t[i].oka ? RLXU_OK : RLXU_R_SIG;
		A.r.version = t[i].va;
		B.reason = t[i].okb ? RLXU_OK : RLXU_R_DIGEST;
		B.r.version = t[i].vb;
		w = rlxb_choose(&A, &B);
		got = w ? w->name : 0;
		if (got != t[i].want) {
			printf("      row %lu: got %c want %c\n", i,
			       got ? got : '-', t[i].want ? t[i].want : '-');
			bad++;
		}
	}
	reset(0);
	ok("rlxb_choose: eight rows of the D4 table", bad == 0);
}

/* `t_slots show`: the console of three cases, as an operator would read it --
 * for a reader checking the line formats, not for a verdict. */
static int show(void)
{
	unsigned long n;

	printf("--- both valid, B higher (a mainline-sized B)\n");
	reset(0);
	put(&A, 1, 100000, 1);
	put(&B, 2, 1114112, 2);
	run();
	fputs(con, stdout);
	printf("--- A torn header, B torn body: halt\n");
	reset(0);
	put(&A, 3, 200000, 1);
	memset(FLASH + A.flash_off, 0xFF, 256);
	n = put(&B, 4, 300000, 2);
	memset(FLASH + B.flash_off + n - 4096, 0xFF, 4096);
	run();
	fputs(con, stdout);
	printf("--- a container signed for slot B, found in slot A\n");
	reset(0);
	mk(FLASH + A.flash_off, 3, 40000, 1, RLXB_SLOT_B_FLASH, RLXU_FORM_WHOLE);
	run();
	fputs(con, stdout);
	return 0;
}

int main(int argc, char **argv)
{
	unsigned char pk[32];

	memcpy(sk, rlxboot_devseed, 32);
	rlx_ed25519_pubkey_from_seed(pk, rlxboot_devseed);
	memcpy(sk + 32, pk, 32);
	if (argc > 1 && strcmp(argv[1], "show") == 0)
		return show();
	ok("devkey.h matches the key derived from the 0x42 seed",
	   memcmp(pk, rlxboot_devkey, 32) == 0);

	test_a_only();
	test_b_only();
	test_a_higher();
	test_b_higher();
	test_tie();
	test_neither();
	test_torn_header();
	test_torn_body();
	test_winner_bytes();
	test_unverified_version();
	test_rollback();
	test_wrong_slot();
	test_stale_ram();
	test_ctr_flash_only();
	test_bounds();
	test_stage_order();
	test_choose_table();

	printf("t_slots %d checks, %d failures\n", checks, failures);
	return failures ? 1 : 0;
}
