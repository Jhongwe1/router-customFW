/*
 * test-spi-wrpolicy -- the flash write path's refusals, on the host.
 *
 * R8b item 4, 2026-10-04.  It #includes the DRIVER's own header, not a copy
 * of its arithmetic:
 *
 *   config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h
 *
 * which has no #include of its own for exactly this reason.  A harness holding
 * its own bounds test would be the shape where a guard and its test agree with
 * each other and both are wrong.
 *
 * 🔴 WHAT A GREEN RUN SAYS, AND IT IS NARROW.  The policy refuses and permits
 * as declared, on x86-64, at this grain.  It says NOTHING about the silicon:
 * no page has been programmed, no block erased, and the kernel TU that calls
 * these functions is in no image.  notes/spi-mtd-driver.md § 12 says so in the
 * same words.
 *
 * ------------------------------------------------------------------------
 * HOW IT AVOIDS BEING A TEST THAT CANNOT FAIL
 * ------------------------------------------------------------------------
 *
 *  1. EVERY REASON MUST FIRE.  The suite asserts that each of the nine refusal
 *     reasons is produced by at least one case.  A reason nobody drives is a
 *     counter whose zero means nothing, and adding a reason to the header
 *     without a case here turns the suite red.
 *  2. BOTH ARMS, ON THE SAME GUARD.  The forbidden window is driven ARMED --
 *     refused while unarmed proves nothing -- and the permitted cases prove
 *     the guard is not simply refusing everything.
 *  3. GRAIN-INDEPENDENT CASES.  Three cases are computed from
 *     RLXFW_SPI_WR_ERASE_GRAIN rather than written as literals, so when item
 *     1's settled value replaces the 未定 placeholder they still assert the
 *     right thing -- in particular that the lowest erasable block is the first
 *     grain-aligned block at or above RLXFW_SPI_WR_NEVER_HI, which is the
 *     brick-margin arithmetic `FW-187` 殘留 is about.
 *  4. A MUTATION MODE.  `--mutate N` inverts case N's expectation and the
 *     suite must then go RED.  tools/test-spi-wrpolicy.sh runs the unmutated
 *     suite FIRST and refuses to trust a mutation run until it is green.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The four names the header needs, and nothing else.  Deliberately NOT
 * <linux/types.h>: if this harness needed kernel headers it could not run at
 * the desk, which is the whole point of it. */
typedef unsigned int u32;
typedef unsigned char u8;

#include "rtl819x-spi-wrpolicy.h"

#define GRAIN  RLXFW_SPI_WR_ERASE_GRAIN
#define PAGE   RLXFW_SPI_WR_PAGE
#define NEVER  RLXFW_SPI_WR_NEVER_HI
#define CHIP   RLXFW_SPI_WR_CHIP

/* The first grain-aligned block at or above the forbidden window.  Computed,
 * not typed: at a 4 KiB grain it is 0x008000 and at 64 KiB it is 0x010000, and
 * the second is the whole reason `FW-187` 殘留 blocks R8b. */
#define FIRST_OK_BLK  (((NEVER + GRAIN - 1u) / GRAIN) * GRAIN)
/* The grain-aligned block below it, which must be refused. */
#define LAST_BAD_BLK  (FIRST_OK_BLK - GRAIN)

enum { OP_PROG, OP_ERASE, OP_ARM };

struct kase {
	const char *name;
	int op;
	int armed;
	u32 alo, ahi, abudget;	/* the arm state, or the arm request */
	u32 addr, len;
	u32 grain, mtd_erasesize;
	int want;
};

static const struct kase cases[] = {
/* ---- the forbidden window, DRIVEN ARMED so the refusal is the guard's and
 * not the arming state's.  The arm window below is itself legal; what is
 * refused is the operation, inside it, reaching below NEVER. ---- */
{ "prog offset 0, armed",            OP_PROG, 1, 0u, CHIP, CHIP,
  0x000000u, 1u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "prog last loader byte, armed",    OP_PROG, 1, 0u, CHIP, CHIP,
  0x005FFFu, 1u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "prog into H601, armed",           OP_PROG, 1, 0u, CHIP, CHIP,
  0x006000u, 1u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "prog last H601 byte, armed",      OP_PROG, 1, 0u, CHIP, CHIP,
  0x007FFFu, 1u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "prog straddling H601's top",      OP_PROG, 1, 0u, CHIP, CHIP,
  0x007F00u, 0x100u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "prog len 0 at offset 0",          OP_PROG, 1, 0u, CHIP, CHIP,
  0x000000u, 0u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },

/* ---- THE PERMITTING ARM.  Without these the suite is a guard that refuses
 * everything, which is also what a broken guard does. ---- */
{ "prog first legal page",           OP_PROG, 1, 0x008000u, 0x009000u, 0x100u,
  0x008000u, 0x100u, 0u, 0u, RLXFW_SPI_WR_OK },
{ "prog one byte, legal",            OP_PROG, 1, 0x020000u, 0x030000u, 0x10u,
  0x020000u, 1u, 0u, 0u, RLXFW_SPI_WR_OK },
{ "prog unaligned inside a page",    OP_PROG, 1, 0x020000u, 0x030000u, 0x40u,
  0x0200C0u, 0x40u, 0u, 0u, RLXFW_SPI_WR_OK },
{ "prog last page of the chip",      OP_PROG, 1, 0x3FFF00u, CHIP, 0x100u,
  0x3FFF00u, 0x100u, 0u, 0u, RLXFW_SPI_WR_OK },

/* ---- arming ---- */
{ "prog unarmed",                    OP_PROG, 0, 0u, 0u, 0u,
  0x020000u, 0x10u, 0u, 0u, RLXFW_SPI_WR_R_UNARMED },
{ "prog above the armed window",     OP_PROG, 1, 0x020000u, 0x030000u, 0x100u,
  0x030000u, 1u, 0u, 0u, RLXFW_SPI_WR_R_OUTSIDE },
{ "prog below the armed window",     OP_PROG, 1, 0x020000u, 0x030000u, 0x100u,
  0x01FFFFu, 1u, 0u, 0u, RLXFW_SPI_WR_R_OUTSIDE },
{ "prog past the armed budget",      OP_PROG, 1, 0x020000u, 0x030000u, 4u,
  0x020000u, 8u, 0u, 0u, RLXFW_SPI_WR_R_BUDGET },
{ "prog exactly the budget",         OP_PROG, 1, 0x020000u, 0x030000u, 8u,
  0x020000u, 8u, 0u, 0u, RLXFW_SPI_WR_OK },

/* ---- page geometry.  The vendor bounds uiLen by nothing at all. ---- */
{ "prog longer than a page",         OP_PROG, 1, 0x020000u, 0x030000u, CHIP,
  0x020000u, PAGE + 1u, 0u, 0u, RLXFW_SPI_WR_R_BADLEN },
{ "prog crossing a page boundary",   OP_PROG, 1, 0x020000u, 0x030000u, CHIP,
  0x0200F0u, 0x20u, 0u, 0u, RLXFW_SPI_WR_R_PAGECROSS },
{ "prog ending exactly on a page",   OP_PROG, 1, 0x020000u, 0x030000u, CHIP,
  0x0200F0u, 0x10u, 0u, 0u, RLXFW_SPI_WR_OK },

/* ---- range ---- */
{ "prog off the end of the chip",    OP_PROG, 1, 0u, CHIP, CHIP,
  0x3FFFFFu, 2u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },
{ "prog at the chip size",           OP_PROG, 1, 0u, CHIP, CHIP,
  CHIP, 1u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },
{ "prog len 0, legal address",       OP_PROG, 1, 0x020000u, 0x030000u, CHIP,
  0x020000u, 0u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },

/* ---- erase: the geometry self-check and the 未定 guard ---- */
{ "erase grain 0",                   OP_ERASE, 1, 0u, CHIP, CHIP,
  0x020000u, 0x1000u, 0u, 0x1000u, RLXFW_SPI_WR_R_GEOM },
{ "erase grain not a power of two",  OP_ERASE, 1, 0u, CHIP, CHIP,
  0x020000u, 0x1800u, 0x1800u, 0x1800u, RLXFW_SPI_WR_R_GEOM },
{ "erase grain below a page",        OP_ERASE, 1, 0u, CHIP, CHIP,
  0x020000u, 0x80u, 0x80u, 0x80u, RLXFW_SPI_WR_R_GEOM },
{ "erase grain != mtd->erasesize",   OP_ERASE, 1, 0u, CHIP, CHIP,
  0x020000u, 0x10000u, 0x10000u, 0x1000u, RLXFW_SPI_WR_R_GEOM },

/* ---- erase: THE 64 KiB HAZARD, which is `FW-187` 殘留 in one case.  An
 * erase at 0x008000 is above the forbidden window, and at a 64 KiB grain it
 * CLEARS FROM ZERO.  A check on addr alone would permit it. ---- */
{ "erase at 0x8000, 64 KiB grain",   OP_ERASE, 1, 0u, CHIP, CHIP,
  0x008000u, 0x10000u, 0x10000u, 0x10000u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "erase at 0x8000, 4 KiB grain",    OP_ERASE, 1, 0x008000u, 0x009000u,
  0x1000u, 0x008000u, 0x1000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_OK },
{ "erase block 0",                   OP_ERASE, 1, 0u, CHIP, CHIP,
  0x000000u, 0x1000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_FORBIDDEN },

/* ---- erase: grain-independent, computed from the header's own constant ---- */
{ "erase the last forbidden block",  OP_ERASE, 1, 0u, CHIP, CHIP,
  LAST_BAD_BLK, GRAIN, GRAIN, GRAIN, RLXFW_SPI_WR_R_FORBIDDEN },
{ "erase the first legal block",     OP_ERASE, 1, FIRST_OK_BLK,
  FIRST_OK_BLK + GRAIN, GRAIN,
  FIRST_OK_BLK, GRAIN, GRAIN, GRAIN, RLXFW_SPI_WR_OK },
{ "erase two legal blocks",          OP_ERASE, 1, FIRST_OK_BLK,
  FIRST_OK_BLK + 2u * GRAIN, 2u * GRAIN,
  FIRST_OK_BLK, 2u * GRAIN, GRAIN, GRAIN, RLXFW_SPI_WR_OK },

/* ---- erase: alignment and length, where the vendor ROUNDS UP ---- */
{ "erase addr not grain-aligned",    OP_ERASE, 1, 0x020000u, 0x030000u, CHIP,
  0x020800u, 0x1000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_MISALIGNED },
{ "erase len below one grain",       OP_ERASE, 1, 0x020000u, 0x030000u, CHIP,
  0x020000u, 0x800u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_BADLEN },
{ "erase len 1.5 grains",            OP_ERASE, 1, 0x020000u, 0x030000u, CHIP,
  0x020000u, 0x1800u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_BADLEN },
{ "erase len 1 byte",                OP_ERASE, 1, 0x020000u, 0x030000u, CHIP,
  0x020000u, 1u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_BADLEN },

/* ---- erase: arming and range ---- */
{ "erase unarmed",                   OP_ERASE, 0, 0u, 0u, 0u,
  0x020000u, 0x1000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_UNARMED },
{ "erase outside the armed window",  OP_ERASE, 1, 0x020000u, 0x021000u,
  0x1000u, 0x021000u, 0x1000u, 0x1000u, 0x1000u,
  RLXFW_SPI_WR_R_OUTSIDE },
{ "erase past the armed budget",     OP_ERASE, 1, 0x020000u, 0x030000u, 0x800u,
  0x020000u, 0x1000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_BUDGET },
{ "erase off the end of the chip",   OP_ERASE, 1, 0u, CHIP, CHIP,
  0x3FF000u, 0x2000u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_RANGE },
{ "erase len 0",                     OP_ERASE, 1, 0u, CHIP, CHIP,
  0x020000u, 0u, 0x1000u, 0x1000u, RLXFW_SPI_WR_R_RANGE },

/* ---- the arm verb's own refusal, which is the SECOND independent place the
 * forbidden rule lives ---- */
{ "arm over the loader",             OP_ARM, 0, 0x000000u, 0x010000u, 0x1000u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "arm over H601 only",              OP_ARM, 0, 0x006000u, 0x008000u, 0x100u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "arm straddling H601's top",       OP_ARM, 0, 0x007FFFu, 0x009000u, 0x100u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_FORBIDDEN },
{ "arm from 0x8000 up",              OP_ARM, 0, 0x008000u, 0x010000u, 0x1000u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_OK },
{ "arm the rescue window",           OP_ARM, 0, 0x020000u, 0x030000u, 0x10000u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_OK },
{ "arm hi == lo",                    OP_ARM, 0, 0x020000u, 0x020000u, 1u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },
{ "arm hi < lo",                     OP_ARM, 0, 0x030000u, 0x020000u, 1u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },
{ "arm past the chip",               OP_ARM, 0, 0x3F0000u, CHIP + 1u, 0x1000u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_RANGE },
{ "arm budget 0",                    OP_ARM, 0, 0x020000u, 0x030000u, 0u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_BUDGET },
{ "arm budget wider than window",    OP_ARM, 0, 0x020000u, 0x021000u, 0x1001u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_R_BUDGET },
{ "arm budget == window",            OP_ARM, 0, 0x020000u, 0x021000u, 0x1000u,
  0u, 0u, 0u, 0u, RLXFW_SPI_WR_OK },
};

#define NCASES ((int)(sizeof(cases) / sizeof(cases[0])))

static const char *const rname[RLXFW_SPI_WR_R_COUNT] = {
	"OK", "FORBIDDEN", "RANGE", "UNARMED", "OUTSIDE", "BUDGET",
	"MISALIGNED", "BADLEN", "PAGECROSS", "GEOM"
};

static int run_one(const struct kase *k)
{
	struct rlxfw_spi_wr_arm a;

	memset(&a, 0, sizeof(a));
	if (k->op == OP_ARM)
		return rlxfw_spi_wr_chk_arm(k->alo, k->ahi, k->abudget);

	a.armed = k->armed;
	a.lo = k->alo;
	a.hi = k->ahi;
	a.budget = k->abudget;
	if (k->op == OP_PROG)
		return rlxfw_spi_wr_chk_prog(&a, k->addr, k->len);
	return rlxfw_spi_wr_chk_erase(&a, k->addr, k->len, k->grain,
				      k->mtd_erasesize);
}

int main(int argc, char **argv)
{
	int mutate = -1;
	int i, got, want, fail = 0, permitted = 0;
	int seen[RLXFW_SPI_WR_R_COUNT];

	if (argc == 3 && !strcmp(argv[1], "--mutate"))
		mutate = atoi(argv[2]);
	else if (argc != 1) {
		fprintf(stderr, "usage: %s [--mutate N]\n", argv[0]);
		return 2;
	}

	memset(seen, 0, sizeof(seen));
	printf("test-spi-wrpolicy: %d case(s); grain %08X, page %u, "
	       "never_hi %08X, first_ok_blk %08X\n",
	       NCASES, (unsigned)GRAIN, (unsigned)PAGE, (unsigned)NEVER,
	       (unsigned)FIRST_OK_BLK);

	/* The empty-range property the second term of overlaps_never() exists
	 * for.  Asserted separately because no table row can express it. */
	if (rlxfw_spi_wr_overlaps_never(0u, 0u) != 0) {
		printf("FAIL  overlaps_never(0,0) must be 0\n");
		fail++;
	}
	if (rlxfw_spi_wr_overlaps_never(0u, 1u) != 1) {
		printf("FAIL  overlaps_never(0,1) must be 1\n");
		fail++;
	}

	for (i = 0; i < NCASES; i++) {
		got = run_one(&cases[i]);
		want = cases[i].want;
		if (i == mutate) {
			/* The mutation: ask for the one answer the policy did
			 * not give, so a suite that cannot fail shows up. */
			want = (want == RLXFW_SPI_WR_OK)
			       ? RLXFW_SPI_WR_R_FORBIDDEN : RLXFW_SPI_WR_OK;
			printf("MUTATED case %d: now expecting %s\n",
			       i, rname[want]);
		}
		if (got < 0 || got >= RLXFW_SPI_WR_R_COUNT) {
			printf("FAIL  %2d  %-32s  reason %d out of range\n",
			       i, cases[i].name, got);
			fail++;
			continue;
		}
		seen[got]++;
		if (cases[i].want == RLXFW_SPI_WR_OK)
			permitted++;
		if (got != want) {
			printf("FAIL  %2d  %-32s  got %s, want %s\n",
			       i, cases[i].name, rname[got], rname[want]);
			fail++;
		}
	}

	/* A reason nobody drives is a counter whose zero means nothing. */
	for (i = 1; i < RLXFW_SPI_WR_R_COUNT; i++) {
		if (!seen[i]) {
			printf("FAIL  reason %s is never produced by any "
			       "case: its counter could not move\n", rname[i]);
			fail++;
		}
	}
	/* And a guard that refuses everything passes every refusal case. */
	if (permitted < 8) {
		printf("FAIL  only %d permitting case(s); a guard is shown "
		       "permitting as well as refusing\n", permitted);
		fail++;
	}

	printf("reasons produced:");
	for (i = 1; i < RLXFW_SPI_WR_R_COUNT; i++)
		printf(" %s=%d", rname[i], seen[i]);
	printf("\npermitted %d of %d\n", permitted, NCASES);

	if (fail) {
		printf("test-spi-wrpolicy: %d FAILURE(S)\n", fail);
		return 1;
	}
	printf("test-spi-wrpolicy: all %d case(s) pass\n", NCASES);
	return 0;
}
