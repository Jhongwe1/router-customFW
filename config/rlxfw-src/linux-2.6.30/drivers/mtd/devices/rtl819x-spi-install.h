/*
 * rtl819x-spi-install -- every decision R8b's install path makes, as pure
 * functions over u8/u32, in a header with NO #include of its own.
 *
 * THIS FILE IS NOT REALTEK'S.  R8b Gap A, 2026-10-05, 124th segment.  It is
 * included by rtl819x-spi.c ONLY under CONFIG_MTD_RTL819X_WRITE, and by
 * tools/test-spi-install.c on the host, after rtl819x-spi-wrpolicy.h in both.
 * The includer supplies u8/u16/u32 and a declaration of sprintf.
 *
 * WHY A HEADER, and the same reason as rtl819x-spi-wrpolicy.h's: what the
 * desk can exercise is the decisions, and a decision the host test cannot
 * reach is a decision nobody checked.  So the region table, the verb parser,
 * the arm agreement, the payload header checks, the staging admission, the
 * write ORDER and the read-back comparison all live here, and rtl819x-spi.c's
 * glue only executes what these functions return.  What is NOT here: a
 * register, a lock, an allocation, a digest engine.  A green host test says
 * the decisions are right on the host; it says nothing about the silicon.
 *
 * The spec this implements is R8b's D1, D2, D5, D6, D7, D9, D10, D11, D12.
 */

#ifndef RTL819X_SPI_INSTALL_H
#define RTL819X_SPI_INSTALL_H

#ifndef RTL819X_SPI_WRPOLICY_H
#error "include rtl819x-spi-wrpolicy.h before rtl819x-spi-install.h"
#endif

#define RLXFW_SPI_INST_VERSION	"rtl819x-spi-install 1.0"

/* ------------------------------------------------------------------------
 * The region table.  D1 and D6.
 *
 * D1's layout, notes/update-chain.md § 6, unchanged.  NO VERB TAKES AN
 * ADDRESS: a region is named, and these constants are the only flash
 * addresses the install path can reach.  0x000000-0x00FFFF is never nameable,
 * which is asserted below at compile time rather than argued.
 * ------------------------------------------------------------------------ */

/* One loader step.  Every region starts on one and is a whole number of them,
 * which is what makes the erased range equal the region at BOTH candidate
 * erase sizes (D11 -- see rlxfw_spi_inst_op). */
#define RLXFW_SPI_INST_BLOCK	0x00010000u
/* D1: the first nameable byte.  The 64 KiB block below it holds the loader,
 * H601, COMPDS and COMPCS together, so at a 64 KiB erase grain ANY address
 * under this would clear the loader. */
#define RLXFW_SPI_INST_FLOOR	0x00010000u
/* The state block (anti-rollback bitmap, A/B selector).  D3: R8b writes no
 * state, so no region may reach it. */
#define RLXFW_SPI_INST_STATE	0x003F0000u

#define RLXFW_SPI_INST_RLXBOOT_BASE	0x00010000u
#define RLXFW_SPI_INST_RLXBOOT_SIZE	0x00010000u	/*    65,536 */
#define RLXFW_SPI_INST_RESCUE_BASE	0x00020000u
#define RLXFW_SPI_INST_RESCUE_SIZE	0x00010000u	/*    65,536 */
#define RLXFW_SPI_INST_BARRIER_BASE	0x00030000u
#define RLXFW_SPI_INST_BARRIER_SIZE	0x00040000u	/*   262,144 */
#define RLXFW_SPI_INST_SLOTA_BASE	0x00070000u
#define RLXFW_SPI_INST_SLOTA_SIZE	0x00120000u	/* 1,179,648 */
#define RLXFW_SPI_INST_SLOTB_BASE	0x00190000u
#define RLXFW_SPI_INST_SLOTB_SIZE	0x00120000u	/* 1,179,648 */
/* D19: the erase-size probe's own block -- the LAST 64 KiB of the free area
 * (notes/update-chain.md § 6), inside the tail the 2026-08-16 dump read as
 * erased (0x34C000-0x3FFFFF), and ending exactly where the state block
 * begins.  A SE there clears the state block only if the part's erase size
 * is above 64 KiB, which no candidate is (FW-187: 4,096 or 65,536). */
#define RLXFW_SPI_INST_PROBE_BASE	0x003E0000u
#define RLXFW_SPI_INST_PROBE_SIZE	0x00010000u	/*    65,536 */

/* D12: the staging buffer's capacity is the largest region.  The host test
 * recomputes the maximum over the table and compares. */
#define RLXFW_SPI_INST_IMG_CAP		RLXFW_SPI_INST_SLOTA_SIZE

/* Compile-time, so a table edit that breaks D1 does not build. */
#define RLXFW_SPI_INST_ASSERT(name, cond) \
	typedef char rlxfw_spi_inst_assert_##name[(cond) ? 1 : -1]

#define RLXFW_SPI_INST_ALIGNED(b, s) \
	((((b) | (s)) & (RLXFW_SPI_INST_BLOCK - 1u)) == 0u && (s) != 0u)

RLXFW_SPI_INST_ASSERT(floor, RLXFW_SPI_INST_RLXBOOT_BASE >= RLXFW_SPI_INST_FLOOR);
RLXFW_SPI_INST_ASSERT(floor_above_never,
		      RLXFW_SPI_INST_FLOOR >= RLXFW_SPI_WR_NEVER_HI);
RLXFW_SPI_INST_ASSERT(a_rlxboot, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_RLXBOOT_BASE, RLXFW_SPI_INST_RLXBOOT_SIZE));
RLXFW_SPI_INST_ASSERT(a_rescue, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_RESCUE_BASE, RLXFW_SPI_INST_RESCUE_SIZE));
RLXFW_SPI_INST_ASSERT(a_barrier, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_BARRIER_BASE, RLXFW_SPI_INST_BARRIER_SIZE));
RLXFW_SPI_INST_ASSERT(a_slota, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_SLOTA_BASE, RLXFW_SPI_INST_SLOTA_SIZE));
RLXFW_SPI_INST_ASSERT(a_slotb, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_SLOTB_BASE, RLXFW_SPI_INST_SLOTB_SIZE));
/* ascending and disjoint, and the last one ends below the state block */
RLXFW_SPI_INST_ASSERT(o1, RLXFW_SPI_INST_RLXBOOT_BASE +
		      RLXFW_SPI_INST_RLXBOOT_SIZE <= RLXFW_SPI_INST_RESCUE_BASE);
RLXFW_SPI_INST_ASSERT(o2, RLXFW_SPI_INST_RESCUE_BASE +
		      RLXFW_SPI_INST_RESCUE_SIZE <= RLXFW_SPI_INST_BARRIER_BASE);
RLXFW_SPI_INST_ASSERT(o3, RLXFW_SPI_INST_BARRIER_BASE +
		      RLXFW_SPI_INST_BARRIER_SIZE <= RLXFW_SPI_INST_SLOTA_BASE);
RLXFW_SPI_INST_ASSERT(o4, RLXFW_SPI_INST_SLOTA_BASE +
		      RLXFW_SPI_INST_SLOTA_SIZE <= RLXFW_SPI_INST_SLOTB_BASE);
RLXFW_SPI_INST_ASSERT(a_probe, RLXFW_SPI_INST_ALIGNED(
		      RLXFW_SPI_INST_PROBE_BASE, RLXFW_SPI_INST_PROBE_SIZE));
RLXFW_SPI_INST_ASSERT(o5, RLXFW_SPI_INST_SLOTB_BASE +
		      RLXFW_SPI_INST_SLOTB_SIZE <= RLXFW_SPI_INST_PROBE_BASE);
RLXFW_SPI_INST_ASSERT(o5b, RLXFW_SPI_INST_PROBE_BASE +
		      RLXFW_SPI_INST_PROBE_SIZE <= RLXFW_SPI_INST_STATE);
RLXFW_SPI_INST_ASSERT(o6, RLXFW_SPI_INST_STATE <= RLXFW_SPI_WR_CHIP);
RLXFW_SPI_INST_ASSERT(cap, RLXFW_SPI_INST_IMG_CAP >= RLXFW_SPI_INST_SLOTB_SIZE &&
		      RLXFW_SPI_INST_IMG_CAP >= RLXFW_SPI_INST_BARRIER_SIZE);

/* What a region holds, which decides what the installer checks in it. */
enum {
	RLXFW_SPI_INST_K_CR6C = 1,	/* a cr6c image the stock loader boots */
	RLXFW_SPI_INST_K_ERASE,		/* erase only -- D2's barrier */
	RLXFW_SPI_INST_K_RLXU,		/* a signed format-2 RLXU container */
	RLXFW_SPI_INST_K_PROBE		/* `eraseprobe` only -- D19 */
};

struct rlxfw_spi_inst_region {
	const char *name;
	u32 base;
	u32 size;
	int kind;
};

static const struct rlxfw_spi_inst_region rlxfw_spi_inst_regions[] = {
	{ "rlxboot", RLXFW_SPI_INST_RLXBOOT_BASE, RLXFW_SPI_INST_RLXBOOT_SIZE,
	  RLXFW_SPI_INST_K_CR6C },
	{ "rescue",  RLXFW_SPI_INST_RESCUE_BASE,  RLXFW_SPI_INST_RESCUE_SIZE,
	  RLXFW_SPI_INST_K_CR6C },
	{ "barrier", RLXFW_SPI_INST_BARRIER_BASE, RLXFW_SPI_INST_BARRIER_SIZE,
	  RLXFW_SPI_INST_K_ERASE },
	{ "slotA",   RLXFW_SPI_INST_SLOTA_BASE,   RLXFW_SPI_INST_SLOTA_SIZE,
	  RLXFW_SPI_INST_K_RLXU },
	{ "slotB",   RLXFW_SPI_INST_SLOTB_BASE,   RLXFW_SPI_INST_SLOTB_SIZE,
	  RLXFW_SPI_INST_K_RLXU },
	{ "probe",   RLXFW_SPI_INST_PROBE_BASE,   RLXFW_SPI_INST_PROBE_SIZE,
	  RLXFW_SPI_INST_K_PROBE },
};
#define RLXFW_SPI_INST_NREGIONS	6
RLXFW_SPI_INST_ASSERT(nregions, sizeof(rlxfw_spi_inst_regions) /
		      sizeof(rlxfw_spi_inst_regions[0]) ==
		      RLXFW_SPI_INST_NREGIONS);

/* ------------------------------------------------------------------------
 * The reasons.  One per refusal, because one errno for twenty refusals is a
 * counter that cannot say which check held.  /proc prints the NAME.
 * ------------------------------------------------------------------------ */
enum {
	RLXFW_SPI_INST_OK = 0,
	RLXFW_SPI_INST_R_SYNTAX,	/* the verb line does not parse */
	RLXFW_SPI_INST_R_REGION,	/* no region of that name */
	RLXFW_SPI_INST_R_ERASE_ONLY,	/* `install` on the barrier */
	RLXFW_SPI_INST_R_NOT_ERASABLE,	/* `erase` on anything but the barrier */
	RLXFW_SPI_INST_R_ARM_READ,	/* the write TU's getter returned an error */
	RLXFW_SPI_INST_R_UNARMED,	/* no arm in force */
	RLXFW_SPI_INST_R_ARM_WINDOW,	/* the arm is not exactly this region */
	RLXFW_SPI_INST_R_ARM_BUDGET,	/* the arm's budget is below its size */
	RLXFW_SPI_INST_R_IMG_BAD,	/* the staging buffer is poisoned */
	RLXFW_SPI_INST_R_IMG_EMPTY,	/* nothing staged */
	RLXFW_SPI_INST_R_IMG_SIZE,	/* more staged than the region holds */
	RLXFW_SPI_INST_R_KAT,		/* sha256 failed its boot-time vectors */
	RLXFW_SPI_INST_R_HASH,		/* the digest engine returned an error */
	RLXFW_SPI_INST_R_SHA,		/* staged bytes != the typed digest */
	RLXFW_SPI_INST_R_HDR_MAGIC,	/* not the magic this region holds */
	RLXFW_SPI_INST_R_HDR_FORMAT,	/* RLXU: not format 2 / header 96 */
	RLXFW_SPI_INST_R_HDR_FLASH_AT,	/* declared destination != region base */
	RLXFW_SPI_INST_R_HDR_FORM,	/* RLXU: flash_form is not WHOL */
	RLXFW_SPI_INST_R_HDR_LEN,	/* declared length != staged length */
	RLXFW_SPI_INST_R_HDR_SUM,	/* cr6c: the 16-bit sum is not zero */
	RLXFW_SPI_INST_R_POLICY,	/* the write policy refused a planned op */
	RLXFW_SPI_INST_R_NOMEM,		/* an allocation failed */
	RLXFW_SPI_INST_R_ENGINE,	/* a primitive failed after the first op */
	RLXFW_SPI_INST_R_CMP,		/* the read-back differs */
	RLXFW_SPI_INST_R_PROBE_ONLY,	/* install/erase named the probe block */
	RLXFW_SPI_INST_R_PROBE_DIRTY,	/* eraseprobe: the block is not erased */
	RLXFW_SPI_INST_R_PROBE_MARK,	/* a marker page did not read back */
	RLXFW_SPI_INST_R_PROBE_ANOMALY,	/* no candidate size fits the markers */
	RLXFW_SPI_INST_R_PROBE_UNCLEAN,	/* the block could not be re-erased */
	RLXFW_SPI_INST_R_COUNT		/* the array size; not a reason */
};

static const char *const rlxfw_spi_inst_rname[RLXFW_SPI_INST_R_COUNT] = {
	"OK", "SYNTAX", "REGION", "ERASE_ONLY", "NOT_ERASABLE", "ARM_READ",
	"UNARMED", "ARM_WINDOW", "ARM_BUDGET", "IMG_BAD", "IMG_EMPTY",
	"IMG_SIZE", "KAT", "HASH", "SHA", "HDR_MAGIC", "HDR_FORMAT",
	"HDR_FLASH_AT", "HDR_FORM", "HDR_LEN", "HDR_SUM", "POLICY", "NOMEM",
	"ENGINE", "CMP", "PROBE_ONLY", "PROBE_DIRTY", "PROBE_MARK",
	"PROBE_ANOMALY", "PROBE_UNCLEAN"
};

static inline const char *rlxfw_spi_inst_reason_name(int r)
{
	if (r < 0 || r >= RLXFW_SPI_INST_R_COUNT || !rlxfw_spi_inst_rname[r])
		return "?";
	return rlxfw_spi_inst_rname[r];
}

/* ------------------------------------------------------------------------
 * Small helpers.  Written out rather than taken from a library, so the host
 * and the kernel run the same code byte for byte.
 * ------------------------------------------------------------------------ */

static inline u32 rlxfw_spi_inst_be32(const u8 *p)
{
	return ((u32)p[0] << 24) | ((u32)p[1] << 16) | ((u32)p[2] << 8) |
	       (u32)p[3];
}

static inline u32 rlxfw_spi_inst_be16(const u8 *p)
{
	return ((u32)p[0] << 8) | (u32)p[1];
}

/* The token at s: up to a space or the end. */
static inline u32 rlxfw_spi_inst_toklen(const char *s)
{
	u32 n = 0;

	while (s[n] != '\0' && s[n] != ' ')
		n++;
	return n;
}

/* s[0..n) equals the literal, exactly. */
static inline int rlxfw_spi_inst_tokeq(const char *s, u32 n, const char *lit)
{
	u32 i;

	for (i = 0; i < n; i++)
		if (lit[i] != s[i])	/* also stops at lit's NUL */
			return 0;
	return lit[n] == '\0';
}

/* s starts with the literal; returns its length or 0. */
static inline u32 rlxfw_spi_inst_prefix(const char *s, u32 n, const char *lit)
{
	u32 i;

	for (i = 0; lit[i] != '\0'; i++)
		if (i >= n || lit[i] != s[i])
			return 0;
	return i;
}

static inline int rlxfw_spi_inst_hexval(char c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

/* Decimal, 1..10 digits, no sign, no overflow past u32.  -> 0 or -1. */
static inline int rlxfw_spi_inst_dec(const char *s, u32 n, u32 *out)
{
	u32 i, v = 0, d;

	if (n == 0 || n > 10)
		return -1;
	for (i = 0; i < n; i++) {
		if (s[i] < '0' || s[i] > '9')
			return -1;
		d = (u32)(s[i] - '0');
		if (v > (0xFFFFFFFFu - d) / 10u)
			return -1;
		v = v * 10u + d;
	}
	*out = v;
	return 0;
}

/* ------------------------------------------------------------------------
 * The verbs.  D6, D7, D10.
 *
 *   install <region> sha=<64 hex>[ pace=<ms>]
 *   erase <region>[ pace=<ms>]
 *   eraseprobe                     (D19: the probe block is implied)
 *
 * Single spaces, nothing trailing, region names case-sensitive.  Strict on
 * purpose: a malformed line is a refusal, never a guess.  `pace` is 1..10000
 * ms, slept after each 64 KiB block of the erase and program phases (D10); 0
 * is refused, so "paced" is never ambiguous.  The longest line any cell
 * types is `install rlxboot sha=<64> pace=10000`, 95 bytes; the dispatcher's
 * buffer is RLXFW_SPI_INST_LINE_MAX.  The probe block answers to
 * `eraseprobe` and nothing else, and `eraseprobe` takes no argument at all,
 * so no typing can aim the probe's single raw erase anywhere but there.
 * ------------------------------------------------------------------------ */
#define RLXFW_SPI_INST_LINE_MAX		128
#define RLXFW_SPI_INST_PACE_MAX		10000u

enum {
	RLXFW_SPI_INST_V_NONE = 0,
	RLXFW_SPI_INST_V_INSTALL,
	RLXFW_SPI_INST_V_ERASE,
	RLXFW_SPI_INST_V_PROBE
};

struct rlxfw_spi_inst_req {
	int verb;
	int region;		/* index into the table, -1 if none */
	u8 sha[32];		/* the typed digest; install only */
	u32 pace_ms;		/* 0 = unpaced */
};

static inline int rlxfw_spi_inst_parse(const char *s,
				       struct rlxfw_spi_inst_req *rq)
{
	const struct rlxfw_spi_inst_region *rg;
	u32 n, i, v;
	int k, hi, lo;

	rq->verb = RLXFW_SPI_INST_V_NONE;
	rq->region = -1;
	rq->pace_ms = 0u;
	for (i = 0; i < 32u; i++)
		rq->sha[i] = 0u;

	n = rlxfw_spi_inst_toklen(s);
	if (rlxfw_spi_inst_tokeq(s, n, "eraseprobe")) {
		rq->verb = RLXFW_SPI_INST_V_PROBE;
		if (s[n] != '\0')
			return RLXFW_SPI_INST_R_SYNTAX;
		for (k = 0; k < RLXFW_SPI_INST_NREGIONS; k++)
			if (rlxfw_spi_inst_regions[k].kind ==
			    RLXFW_SPI_INST_K_PROBE)
				rq->region = k;
		return rq->region < 0 ? RLXFW_SPI_INST_R_REGION :
					RLXFW_SPI_INST_OK;
	}
	if (rlxfw_spi_inst_tokeq(s, n, "install"))
		rq->verb = RLXFW_SPI_INST_V_INSTALL;
	else if (rlxfw_spi_inst_tokeq(s, n, "erase"))
		rq->verb = RLXFW_SPI_INST_V_ERASE;
	else
		return RLXFW_SPI_INST_R_SYNTAX;
	s += n;
	if (*s != ' ')
		return RLXFW_SPI_INST_R_SYNTAX;
	s++;

	n = rlxfw_spi_inst_toklen(s);
	if (n == 0)
		return RLXFW_SPI_INST_R_SYNTAX;
	for (k = 0; k < RLXFW_SPI_INST_NREGIONS; k++)
		if (rlxfw_spi_inst_tokeq(s, n, rlxfw_spi_inst_regions[k].name))
			break;
	if (k == RLXFW_SPI_INST_NREGIONS)
		return RLXFW_SPI_INST_R_REGION;
	rq->region = k;
	rg = &rlxfw_spi_inst_regions[k];
	if (rg->kind == RLXFW_SPI_INST_K_PROBE)
		return RLXFW_SPI_INST_R_PROBE_ONLY;
	if (rq->verb == RLXFW_SPI_INST_V_INSTALL &&
	    rg->kind == RLXFW_SPI_INST_K_ERASE)
		return RLXFW_SPI_INST_R_ERASE_ONLY;
	if (rq->verb == RLXFW_SPI_INST_V_ERASE &&
	    rg->kind != RLXFW_SPI_INST_K_ERASE)
		return RLXFW_SPI_INST_R_NOT_ERASABLE;
	s += n;

	if (rq->verb == RLXFW_SPI_INST_V_INSTALL) {
		if (*s != ' ')
			return RLXFW_SPI_INST_R_SYNTAX;
		s++;
		n = rlxfw_spi_inst_toklen(s);
		if (n != 4u + 64u || rlxfw_spi_inst_prefix(s, n, "sha=") != 4u)
			return RLXFW_SPI_INST_R_SYNTAX;
		for (i = 0; i < 32u; i++) {
			hi = rlxfw_spi_inst_hexval(s[4u + 2u * i]);
			lo = rlxfw_spi_inst_hexval(s[5u + 2u * i]);
			if (hi < 0 || lo < 0)
				return RLXFW_SPI_INST_R_SYNTAX;
			rq->sha[i] = (u8)((hi << 4) | lo);
		}
		s += n;
	}

	if (*s == ' ') {
		s++;
		n = rlxfw_spi_inst_toklen(s);
		if (rlxfw_spi_inst_prefix(s, n, "pace=") != 5u || n > 10u ||
		    s[5] == '0' ||
		    rlxfw_spi_inst_dec(s + 5, n - 5u, &v) != 0 ||
		    v == 0u || v > RLXFW_SPI_INST_PACE_MAX)
			return RLXFW_SPI_INST_R_SYNTAX;
		rq->pace_ms = v;
		s += n;
	}
	if (*s != '\0')
		return RLXFW_SPI_INST_R_SYNTAX;
	return RLXFW_SPI_INST_OK;
}

/* ------------------------------------------------------------------------
 * The arm.  D6: "two typed statements have to agree".
 *
 * The arm in force is the write TU's (rtl819x-spi-write.c), static there and
 * read through that TU's getter, rtl819x_spi_wr_get_arm() (D20): a COPY, taken
 * under rtl819x_spi_lock, so this path can compare against the arm and cannot
 * change it.  The getter replaced a parse of the TU's /proc printout -- one
 * owner of the value either way, but a getter cannot drift with a format.
 * Fail-closed on both halves: the caller zeroes its copy before the call (a
 * zeroed arm is UNARMED here), and a getter error is ARM_READ whatever the
 * copy holds.
 * ------------------------------------------------------------------------ */

/* The typed arm must name EXACTLY this region with a budget that covers it.
 * The arm verb itself already refuses budget > hi - lo, so in practice the
 * budget equals the size; ">=" is D6's wording and is what is checked. */
static inline int rlxfw_spi_inst_chk_arm(const struct rlxfw_spi_wr_arm *a,
					 const struct rlxfw_spi_inst_region *rg)
{
	if (!a->armed)
		return RLXFW_SPI_INST_R_UNARMED;
	if (a->lo != rg->base || a->hi != rg->base + rg->size)
		return RLXFW_SPI_INST_R_ARM_WINDOW;
	if (a->budget < rg->size)
		return RLXFW_SPI_INST_R_ARM_BUDGET;
	return RLXFW_SPI_INST_OK;
}

/* ------------------------------------------------------------------------
 * The staging buffer.  D12.
 *
 * Appends only.  An append that would pass the capacity is refused WHOLE and
 * POISONS the buffer: what is staged is then a prefix of something, and an
 * install of a prefix must not be one typo away.  Poisoned stays poisoned
 * until `img reset`.
 * ------------------------------------------------------------------------ */
enum {
	RLXFW_SPI_INST_IMG_OK = 0,
	RLXFW_SPI_INST_IMG_OVERFLOW,	/* an append passed the capacity */
	RLXFW_SPI_INST_IMG_FAULT,	/* copy_from_user failed mid-append */
	RLXFW_SPI_INST_IMG_NOMEM,	/* the buffer could not be allocated */
	RLXFW_SPI_INST_IMG_POISONED,	/* refused: an earlier error stands */
	RLXFW_SPI_INST_IMG_COUNT
};

static const char *const rlxfw_spi_inst_iname[RLXFW_SPI_INST_IMG_COUNT] = {
	"none", "OVERFLOW", "FAULT", "NOMEM", "POISONED"
};

struct rlxfw_spi_inst_img {
	u32 len;		/* bytes staged */
	u32 writes;		/* appends accepted */
	u32 resets;		/* `img reset`s */
	int err;		/* RLXFW_SPI_INST_IMG_*, latched */
};

static inline int rlxfw_spi_inst_img_admit(struct rlxfw_spi_inst_img *im,
					   unsigned long count)
{
	if (im->err != RLXFW_SPI_INST_IMG_OK)
		return RLXFW_SPI_INST_IMG_POISONED;
	if (count > (unsigned long)(RLXFW_SPI_INST_IMG_CAP - im->len)) {
		im->err = RLXFW_SPI_INST_IMG_OVERFLOW;
		return RLXFW_SPI_INST_IMG_OVERFLOW;
	}
	return RLXFW_SPI_INST_IMG_OK;
}

static inline void rlxfw_spi_inst_img_reset(struct rlxfw_spi_inst_img *im)
{
	im->len = 0u;
	im->writes = 0u;
	im->err = RLXFW_SPI_INST_IMG_OK;
	im->resets++;
}

static inline int rlxfw_spi_inst_chk_img(const struct rlxfw_spi_inst_img *im,
					 const struct rlxfw_spi_inst_region *rg)
{
	if (im->err != RLXFW_SPI_INST_IMG_OK)
		return RLXFW_SPI_INST_R_IMG_BAD;
	if (im->len == 0u)
		return RLXFW_SPI_INST_R_IMG_EMPTY;
	if (im->len > rg->size)
		return RLXFW_SPI_INST_R_IMG_SIZE;
	return RLXFW_SPI_INST_OK;
}

static inline int rlxfw_spi_inst_digest_eq(const u8 *a, const u8 *b)
{
	u32 i;
	u8 d = 0u;

	for (i = 0; i < 32u; i++)
		d |= (u8)(a[i] ^ b[i]);
	return d == 0u;
}

/* ------------------------------------------------------------------------
 * The payload's own declaration of where it goes.  D7.
 *
 * RLXU, format 2 -- the offsets are src/rlxboot/container.h's, restated here
 * because that header is not in the kernel tree, and the host test includes
 * BOTH and fails on any difference, so the restatement cannot drift silently.
 * The signature is NOT checked here (D7's optional half, declined: see
 * rtl819x-spi.c's Gap A block); what is checked is the signed flash_at, the
 * signed flash_form, and that the container is exactly 160 + payload_len.
 * ------------------------------------------------------------------------ */
#define RLXFW_SPI_INST_RLXU_MAGIC	0x524C5855u	/* "RLXU" */
#define RLXFW_SPI_INST_RLXU_FORMAT	2u
#define RLXFW_SPI_INST_RLXU_HDR_LEN	96u
#define RLXFW_SPI_INST_RLXU_BODY_OFF	160u
#define RLXFW_SPI_INST_RLXU_PLEN_OFF	12u
#define RLXFW_SPI_INST_RLXU_FLASH_OFF	64u
#define RLXFW_SPI_INST_RLXU_FORM_OFF	68u
#define RLXFW_SPI_INST_RLXU_FORM_WHOLE	0x57484F4Cu	/* "WHOL" */
#define RLXFW_SPI_INST_RLXU_PAYLOAD_MAX	0x00300000u

static inline int rlxfw_spi_inst_chk_rlxu(const u8 *img, u32 len, u32 base)
{
	u32 plen;

	if (len < 4u || rlxfw_spi_inst_be32(img) != RLXFW_SPI_INST_RLXU_MAGIC)
		return RLXFW_SPI_INST_R_HDR_MAGIC;
	if (len < RLXFW_SPI_INST_RLXU_BODY_OFF)
		return RLXFW_SPI_INST_R_HDR_LEN;
	if (rlxfw_spi_inst_be16(img + 4) != RLXFW_SPI_INST_RLXU_FORMAT ||
	    rlxfw_spi_inst_be16(img + 6) != RLXFW_SPI_INST_RLXU_HDR_LEN)
		return RLXFW_SPI_INST_R_HDR_FORMAT;
	if (rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_RLXU_FLASH_OFF) != base)
		return RLXFW_SPI_INST_R_HDR_FLASH_AT;
	/* The installer lands the WHOLE staged container, so the signed form
	 * must say so: a PAYL container here would be landed in a form its
	 * own signature disagrees with (container.h's FORMAT 2 paragraph). */
	if (rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_RLXU_FORM_OFF) !=
	    RLXFW_SPI_INST_RLXU_FORM_WHOLE)
		return RLXFW_SPI_INST_R_HDR_FORM;
	plen = rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_RLXU_PLEN_OFF);
	if (plen == 0u || plen > RLXFW_SPI_INST_RLXU_PAYLOAD_MAX ||
	    plen != len - RLXFW_SPI_INST_RLXU_BODY_OFF)
		return RLXFW_SPI_INST_R_HDR_LEN;
	return RLXFW_SPI_INST_OK;
}

/* cr6c, IMG_HEADER_T: signature[4], startAddr, burnAddr, len (FW-12), and
 * tools/mkcr6c.py writes the destination into burnAddr.  The acceptance rule
 * is check_image()'s: signature `cr6c` and a zero 16-bit big-endian sum over
 * the `len` payload bytes (tools/rtkimage.py sum16, C-4).  An odd `len` is
 * refused, as mkcr6c refuses an odd binary. */
#define RLXFW_SPI_INST_CR6C_MAGIC	0x63723663u	/* "cr6c" */
#define RLXFW_SPI_INST_CR6C_HDR_LEN	16u
#define RLXFW_SPI_INST_CR6C_BURN_OFF	8u
#define RLXFW_SPI_INST_CR6C_LEN_OFF	12u

static inline int rlxfw_spi_inst_chk_cr6c(const u8 *img, u32 len, u32 base)
{
	u32 blen, i, sum = 0u;

	if (len < 4u || rlxfw_spi_inst_be32(img) != RLXFW_SPI_INST_CR6C_MAGIC)
		return RLXFW_SPI_INST_R_HDR_MAGIC;
	if (len < RLXFW_SPI_INST_CR6C_HDR_LEN)
		return RLXFW_SPI_INST_R_HDR_LEN;
	if (rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_CR6C_BURN_OFF) != base)
		return RLXFW_SPI_INST_R_HDR_FLASH_AT;
	blen = rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_CR6C_LEN_OFF);
	if (blen != len - RLXFW_SPI_INST_CR6C_HDR_LEN || (blen & 1u) != 0u)
		return RLXFW_SPI_INST_R_HDR_LEN;
	for (i = RLXFW_SPI_INST_CR6C_HDR_LEN; i < len; i += 2u)
		sum += rlxfw_spi_inst_be16(img + i);
	if ((sum & 0xFFFFu) != 0u)
		return RLXFW_SPI_INST_R_HDR_SUM;
	return RLXFW_SPI_INST_OK;
}

static inline int rlxfw_spi_inst_chk_payload(const u8 *img, u32 len,
				const struct rlxfw_spi_inst_region *rg)
{
	if (rg->kind == RLXFW_SPI_INST_K_RLXU)
		return rlxfw_spi_inst_chk_rlxu(img, len, rg->base);
	if (rg->kind == RLXFW_SPI_INST_K_CR6C)
		return rlxfw_spi_inst_chk_cr6c(img, len, rg->base);
	if (rg->kind == RLXFW_SPI_INST_K_PROBE)
		return RLXFW_SPI_INST_R_PROBE_ONLY;
	return RLXFW_SPI_INST_R_ERASE_ONLY;	/* the barrier takes no payload */
}

/* ------------------------------------------------------------------------
 * The write ORDER.  D5 and D11, as a function from an index to an operation,
 * so the kernel loop and the host test walk the SAME sequence.
 *
 *   ops [0, ne)        erase, ascending from the region base -- so the block
 *                      holding the region's FIRST byte goes first and the old
 *                      header is gone before anything else is touched
 *   ops [ne, ne+np-1)  program pages 1 .. np-1, ascending
 *   op  ne+np-1        program page 0 -- the header -- LAST
 *
 * Every erase precedes every program.  That is not only D5's order: at a
 * 64 KiB grain an erase issued after a program into the same block would
 * clear it again, so it is also what keeps the sequence right under BOTH of
 * D11's candidate erase sizes.
 *
 * D11.  The erase step is `grain`, which rtl819x-spi.c passes as
 * RLXFW_SPI_WR_ERASE_GRAIN (0x1000) and the policy requires to equal the
 * mtd erasesize.  Every op is one SE (0x20) at base + i*grain.  If SE clears
 * 4,096 bytes, the ops clear [base, base+size) exactly, one sector each.  If
 * it clears 65,536, each op clears the block holding its address; since base
 * and size are multiples of 65,536 (asserted above), every such block lies
 * inside the region and every block of the region holds an op -- so the
 * cleared range is again exactly [base, base+size), with each block cleared
 * sixteen times.  The host test computes both unions from this function.
 * ------------------------------------------------------------------------ */
enum {
	RLXFW_SPI_INST_OP_END = 0,
	RLXFW_SPI_INST_OP_ERASE,
	RLXFW_SPI_INST_OP_PROG
};

struct rlxfw_spi_inst_plan {
	u32 base, size;		/* the region */
	u32 len;		/* staged bytes; 0 = erase only */
	u32 grain;		/* the erase step */
	u32 ne, np;		/* erase ops, program ops */
};

struct rlxfw_spi_inst_opd {
	int kind;
	u32 addr, len;		/* flash address and byte count */
	u32 off;		/* offset in the region == in the staged bytes */
	u32 blk;		/* 64 KiB block index within the region */
	int blk_end;		/* the last op of its phase in this block */
	int commit;		/* the header page, programmed last */
};

static inline int rlxfw_spi_inst_plan_init(struct rlxfw_spi_inst_plan *pl,
				const struct rlxfw_spi_inst_region *rg,
				u32 len, u32 grain)
{
	/* A refused plan is an EMPTY plan -- zero operations -- never one
	 * left holding whatever the caller's stack held. */
	pl->base = pl->size = pl->len = pl->grain = pl->ne = pl->np = 0u;
	if (grain == 0u || (grain & (grain - 1u)) != 0u ||
	    grain < RLXFW_SPI_WR_PAGE || grain > RLXFW_SPI_INST_BLOCK)
		return RLXFW_SPI_INST_R_POLICY;
	if (len > rg->size)
		return RLXFW_SPI_INST_R_IMG_SIZE;
	pl->base = rg->base;
	pl->size = rg->size;
	pl->len = len;
	pl->grain = grain;
	pl->ne = rg->size / grain;
	pl->np = (len + RLXFW_SPI_WR_PAGE - 1u) / RLXFW_SPI_WR_PAGE;
	return RLXFW_SPI_INST_OK;
}

static inline u32 rlxfw_spi_inst_nops(const struct rlxfw_spi_inst_plan *pl)
{
	return pl->ne + pl->np;
}

static inline int rlxfw_spi_inst_op(const struct rlxfw_spi_inst_plan *pl,
				    u32 i, struct rlxfw_spi_inst_opd *op)
{
	u32 j, k;

	op->kind = RLXFW_SPI_INST_OP_END;
	op->addr = op->len = op->off = op->blk = 0u;
	op->blk_end = op->commit = 0;
	if (i < pl->ne) {
		op->kind = RLXFW_SPI_INST_OP_ERASE;
		op->off = i * pl->grain;
		op->addr = pl->base + op->off;
		op->len = pl->grain;
		op->blk = op->off / RLXFW_SPI_INST_BLOCK;
		op->blk_end = ((op->off + pl->grain) %
			       RLXFW_SPI_INST_BLOCK) == 0u;
		return op->kind;
	}
	j = i - pl->ne;
	if (j >= pl->np)
		return RLXFW_SPI_INST_OP_END;
	k = (j + 1u < pl->np) ? j + 1u : 0u;	/* 1 .. np-1, then 0 */
	op->kind = RLXFW_SPI_INST_OP_PROG;
	op->off = k * RLXFW_SPI_WR_PAGE;
	op->addr = pl->base + op->off;
	op->len = pl->len - op->off;
	if (op->len > RLXFW_SPI_WR_PAGE)
		op->len = RLXFW_SPI_WR_PAGE;
	op->blk = op->off / RLXFW_SPI_INST_BLOCK;
	op->commit = (k == 0u);
	op->blk_end = op->commit || (k + 1u == pl->np) ||
		      (((k + 1u) * RLXFW_SPI_WR_PAGE) % RLXFW_SPI_INST_BLOCK)
		      == 0u;
	return op->kind;
}

/* The read-back.  D5: the staged bytes, then 0xFF to the end of the region.
 * Only an OFFSET leaves this function, never a byte. */
static inline void rlxfw_spi_inst_cmp(const u8 *got, u32 off, u32 n,
				      const u8 *img, u32 len,
				      u32 *ndiff, u32 *first)
{
	u32 i;
	u8 want;

	for (i = 0; i < n; i++) {
		want = (off + i < len) ? img[off + i] : 0xFFu;
		if (got[i] != want) {
			if (*ndiff == 0u)
				*first = off + i;
			(*ndiff)++;
		}
	}
}

/* ------------------------------------------------------------------------
 * The erase-size probe.  D19 -- the reading FW-227 counts as zero.
 *
 * Under an arm equal to the probe block, and only if the block first reads
 * entirely erased, a marker page goes to +0x0000, +0x1000 and +0x8000, ONE SE
 * (0x20) is issued at +0x0000, and the three are read back.  Which of them
 * that single erase cleared is the verdict:
 *
 *     +0x0000  +0x1000  +0x8000   se_bytes   what it bounds, for an aligned
 *                                            erase of S bytes at +0x0000
 *     erased   intact   intact      4096     256 <= S <= 4,096
 *     erased   erased   intact     32768     4,352 <= S <= 32,768
 *     erased   erased   erased     65536     S >= 33,024
 *     intact   intact   intact         0     the opcode cleared nothing
 *     anything else                   -1     no candidate fits: ANOMALY
 *
 * ⚠️ THREE SAMPLE POINTS BOUND THE SIZE; THEY DO NOT MEASURE IT.  The verdict
 * separates FW-187's two candidates (4,096 and 65,536) and the common third
 * (32,768); it would read an 8 KiB or 16 KiB part as 32768 and a 2 KiB part as
 * 4096, and it cannot see past the block, so "65536" means at least 33,024.
 *
 * Clean-up uses the step the verdict proves: the size itself.  An anomaly is
 * cleaned at 4,096, the step that is right under every candidate; a part
 * whose SE cleared nothing cannot be cleaned by this opcode, so nothing else is
 * tried -- no other opcode is in this driver -- and the block is reported
 * unclean.  The marker byte is 'A'..'Z', never 0xFF and never 0x00, so a
 * marker page can be neither mistaken for erased nor for a stuck-low page.
 * ------------------------------------------------------------------------ */
#define RLXFW_SPI_INST_PROBE_NMARK	3
static const u32 rlxfw_spi_inst_probe_off[RLXFW_SPI_INST_PROBE_NMARK] = {
	0x0000u, 0x1000u, 0x8000u
};
/* How long the read-only RDSR calibration runs, in ticks. */
#define RLXFW_SPI_INST_PROBE_CAL_TICKS	10u

static inline u8 rlxfw_spi_inst_probe_byte(u32 i)
{
	return (u8)(0x41u + i % 26u);
}

static inline void rlxfw_spi_inst_probe_mark(u8 *page)
{
	u32 i;

	for (i = 0; i < RLXFW_SPI_WR_PAGE; i++)
		page[i] = rlxfw_spi_inst_probe_byte(i);
}

/* (a) the block must read erased before the probe writes anything */
static inline int rlxfw_spi_inst_probe_chk_erased(const u8 *p, u32 n)
{
	u32 i;

	for (i = 0; i < n; i++)
		if (p[i] != 0xFFu)
			return RLXFW_SPI_INST_R_PROBE_DIRTY;
	return RLXFW_SPI_INST_OK;
}

/* (b) a marker page must read back as written */
static inline int rlxfw_spi_inst_probe_chk_mark(const u8 *p)
{
	u32 i;

	for (i = 0; i < RLXFW_SPI_WR_PAGE; i++)
		if (p[i] != rlxfw_spi_inst_probe_byte(i))
			return RLXFW_SPI_INST_R_PROBE_MARK;
	return RLXFW_SPI_INST_OK;
}

/* (d) one marker page after the SE: 'E' erased, 'I' intact, 'O' other */
static inline int rlxfw_spi_inst_probe_state(const u8 *p)
{
	u32 i;
	int erased = 1, intact = 1;

	for (i = 0; i < RLXFW_SPI_WR_PAGE; i++) {
		if (p[i] != 0xFFu)
			erased = 0;
		if (p[i] != rlxfw_spi_inst_probe_byte(i))
			intact = 0;
	}
	return erased ? 'E' : intact ? 'I' : 'O';
}

static inline int rlxfw_spi_inst_probe_size(int m0, int m1, int m8)
{
	if (m0 == 'E' && m1 == 'I' && m8 == 'I')
		return 4096;
	if (m0 == 'E' && m1 == 'E' && m8 == 'I')
		return 32768;
	if (m0 == 'E' && m1 == 'E' && m8 == 'E')
		return 65536;
	if (m0 == 'I' && m1 == 'I' && m8 == 'I')
		return 0;
	return -1;
}

/* (e) the clean-up step the verdict proves; 0 = this opcode cannot clean */
static inline u32 rlxfw_spi_inst_probe_clean_step(int se_bytes)
{
	if (se_bytes == 4096 || se_bytes == 32768 || se_bytes == 65536)
		return (u32)se_bytes;
	if (se_bytes < 0)
		return 0x1000u;
	return 0u;
}

/* The verb's own answer: an unclean block outranks an inconclusive size. */
static inline int rlxfw_spi_inst_probe_verdict(int se_bytes, int clean)
{
	if (clean != 1)
		return RLXFW_SPI_INST_R_PROBE_UNCLEAN;
	if (se_bytes < 0)
		return RLXFW_SPI_INST_R_PROBE_ANOMALY;
	return RLXFW_SPI_INST_OK;
}

/* Zero-initialised means "never run", field by field. */
struct rlxfw_spi_inst_probe {
	int ran;			/* an eraseprobe was attempted */
	int se_issued;			/* the one SE was sent */
	int classified, se_bytes;
	int m[RLXFW_SPI_INST_PROBE_NMARK];	/* 'E' 'I' 'O', 0 unread */
	u32 se_polls, se_jiffies;	/* that SE's RDSR polls and ticks */
	u32 pp_polls, pp_jiffies;	/* the first marker program's */
	u32 cal_polls, cal_ticks;	/* idle RDSR polls in cal_ticks ticks */
	int clean_known, clean;
	u32 clean_step, clean_ops;
};

/* Every eraseprobe attempt starts from nothing, so no field can carry an
 * earlier probe's reading into this one's verdict. */
static inline void rlxfw_spi_inst_probe_begin(struct rlxfw_spi_inst_probe *p)
{
	static const struct rlxfw_spi_inst_probe zero;

	*p = zero;
	p->ran = 1;
}

/* ------------------------------------------------------------------------
 * The results.  Zero-initialised means "nothing has run", field by field,
 * so the kernel's static needs no init call: region is index+1, the two
 * verdicts have a separate `checked`, and cmp_first is printed as -1 while
 * cmp_diff is 0.
 * ------------------------------------------------------------------------ */
struct rlxfw_spi_inst_res {
	int ran, verb, region1;		/* region1: index + 1, 0 = none */
	u32 base, size, len, pace_ms;
	int reason, rc, policy;		/* policy: the wrpolicy reason */
	int arm_ok, sha_checked, sha_ok, hdr_checked, hdr_ok;
	u32 ops_planned, ops_done, n_se, n_pp, erased, programmed;
	int committed, phase;		/* phase: 0 or 'E' 'P' 'H' 'V' 'D' */
	int cmp_ran, cmp_ok;
	u32 cmp_bytes, cmp_diff, cmp_first;
	u32 ms;
};

struct rlxfw_spi_inst_st {
	u32 attempts, done, refused, failed;
	struct rlxfw_spi_inst_res r;
};

static inline void rlxfw_spi_inst_begin(struct rlxfw_spi_inst_st *s)
{
	static const struct rlxfw_spi_inst_res zero;

	s->r = zero;
	s->r.ran = 1;
	s->attempts++;
}

/* The /proc block.  Every line is a counter, a verdict, a name, an offset
 * or an owner-typed number echoed back -- no flash byte, no digest.  The
 * staged image's digest is deliberately NOT printed: the device must not be
 * a place the typed digest can be copied from (D7). */
#define RLXFW_SPI_INST_PROC_MAX		1152

/* A boolean field prints as 0 or 1 whatever the int holds, which is also what
 * bounds this block's widest output (the host test measures it). */
#define RLXFW_SPI_INST_B(x)	((x) != 0)

static inline const char *rlxfw_spi_inst_verb_name(int v)
{
	return v == RLXFW_SPI_INST_V_INSTALL ? "install" :
	       v == RLXFW_SPI_INST_V_ERASE ? "erase" :
	       v == RLXFW_SPI_INST_V_PROBE ? "eraseprobe" : "-";
}

static inline const char *rlxfw_spi_inst_region_name(int region1)
{
	return (region1 > 0 && region1 <= RLXFW_SPI_INST_NREGIONS) ?
	       rlxfw_spi_inst_regions[region1 - 1].name : "-";
}

static inline int rlxfw_spi_inst_emit(char *p,
				      const struct rlxfw_spi_inst_st *s,
				      const struct rlxfw_spi_inst_img *im,
				      const struct rlxfw_spi_inst_probe *pr,
				      u32 erase_opcode, u32 erase_step,
				      u32 tick_us)
{
	const struct rlxfw_spi_inst_res *r = &s->r;
	const char *vn, *rn, *in;
	int k, len = 0;
	char m[RLXFW_SPI_INST_PROBE_NMARK];

	vn = rlxfw_spi_inst_verb_name(r->verb);
	rn = rlxfw_spi_inst_region_name(r->region1);
	for (k = 0; k < RLXFW_SPI_INST_PROBE_NMARK; k++)
		m[k] = (pr->m[k] == 'E' || pr->m[k] == 'I' || pr->m[k] == 'O') ?
		       (char)pr->m[k] : '-';
	in = (im->err >= 0 && im->err < RLXFW_SPI_INST_IMG_COUNT) ?
	     rlxfw_spi_inst_iname[im->err] : "?";

	len += sprintf(p + len, "inst_version %s\n", RLXFW_SPI_INST_VERSION);
	len += sprintf(p + len, "img_cap %u\n", (unsigned)RLXFW_SPI_INST_IMG_CAP);
	len += sprintf(p + len, "img_len %u\n", (unsigned)im->len);
	len += sprintf(p + len, "img_writes %u\n", (unsigned)im->writes);
	len += sprintf(p + len, "img_resets %u\n", (unsigned)im->resets);
	len += sprintf(p + len, "img_err %s\n", in);
	len += sprintf(p + len, "inst_attempts %u\n", (unsigned)s->attempts);
	len += sprintf(p + len, "inst_done %u\n", (unsigned)s->done);
	len += sprintf(p + len, "inst_refused %u\n", (unsigned)s->refused);
	len += sprintf(p + len, "inst_failed %u\n", (unsigned)s->failed);
	len += sprintf(p + len, "inst_ran %d\n", RLXFW_SPI_INST_B(r->ran));
	len += sprintf(p + len, "inst_verb %s\n", vn);
	len += sprintf(p + len, "inst_region %s\n", rn);
	len += sprintf(p + len, "inst_base %06X\n", (unsigned)r->base);
	len += sprintf(p + len, "inst_size %u\n", (unsigned)r->size);
	len += sprintf(p + len, "inst_len %u\n", (unsigned)r->len);
	/* D10: a paced run says so in every result. */
	len += sprintf(p + len, "inst_paced %d\n", r->pace_ms != 0u);
	len += sprintf(p + len, "inst_pace_ms %u\n", (unsigned)r->pace_ms);
	len += sprintf(p + len, "inst_reason %s\n",
		       rlxfw_spi_inst_reason_name(r->reason));
	len += sprintf(p + len, "inst_rc %d\n", r->rc);
	len += sprintf(p + len, "inst_policy %d\n", r->policy);
	len += sprintf(p + len, "inst_arm_ok %d\n", RLXFW_SPI_INST_B(r->arm_ok));
	len += sprintf(p + len, "inst_sha_checked %d\n",
		       RLXFW_SPI_INST_B(r->sha_checked));
	len += sprintf(p + len, "inst_sha_ok %d\n", RLXFW_SPI_INST_B(r->sha_ok));
	len += sprintf(p + len, "inst_hdr_checked %d\n",
		       RLXFW_SPI_INST_B(r->hdr_checked));
	len += sprintf(p + len, "inst_hdr_ok %d\n", RLXFW_SPI_INST_B(r->hdr_ok));
	/* D11, printed so no card carries it as a typed constant */
	len += sprintf(p + len, "inst_erase_op %02X\n", (unsigned)erase_opcode);
	len += sprintf(p + len, "inst_erase_step %u\n", (unsigned)erase_step);
	len += sprintf(p + len, "inst_ops %u\n", (unsigned)r->ops_done);
	len += sprintf(p + len, "inst_ops_planned %u\n",
		       (unsigned)r->ops_planned);
	len += sprintf(p + len, "inst_n_se %u\n", (unsigned)r->n_se);
	len += sprintf(p + len, "inst_n_pp %u\n", (unsigned)r->n_pp);
	len += sprintf(p + len, "inst_erased %u\n", (unsigned)r->erased);
	len += sprintf(p + len, "inst_programmed %u\n", (unsigned)r->programmed);
	len += sprintf(p + len, "inst_committed %d\n",
		       RLXFW_SPI_INST_B(r->committed));
	len += sprintf(p + len, "inst_phase %c\n",
		       r->phase > 32 && r->phase < 127 ? (char)r->phase : '-');
	len += sprintf(p + len, "inst_cmp_ran %d\n", RLXFW_SPI_INST_B(r->cmp_ran));
	len += sprintf(p + len, "inst_cmp_ok %d\n", RLXFW_SPI_INST_B(r->cmp_ok));
	len += sprintf(p + len, "inst_cmp_bytes %u\n", (unsigned)r->cmp_bytes);
	len += sprintf(p + len, "inst_cmp_diff %u\n", (unsigned)r->cmp_diff);
	len += sprintf(p + len, "inst_cmp_first %d\n",
		       r->cmp_diff ? (int)r->cmp_first : -1);
	len += sprintf(p + len, "inst_ms %u\n", (unsigned)r->ms);
	/* D19.  The first line is the verdict, in the format a card reads:
	 * se_bytes -1 until a size is classified, clean -1 until the block
	 * has been read.  se_us and pp_us are TICK-resolution: the only
	 * clocksource on this board is jiffies (bench/2026-09-03 TM-2a/2b),
	 * so the fine readings are the RDSR poll counts, and cal_polls /
	 * cal_ticks is what converts them. */
	len += sprintf(p + len, "eraseprobe se_bytes=%d se_polls=%u se_us=%u "
		       "pp_us=%u clean=%d\n",
		       pr->classified ? pr->se_bytes : -1,
		       (unsigned)pr->se_polls,
		       (unsigned)(pr->se_jiffies * tick_us),
		       (unsigned)(pr->pp_jiffies * tick_us),
		       pr->clean_known ? RLXFW_SPI_INST_B(pr->clean) : -1);
	len += sprintf(p + len, "eraseprobe_detail ran=%d m0000=%c m1000=%c "
		       "m8000=%c se_jiffies=%u pp_polls=%u pp_jiffies=%u "
		       "cal_polls=%u cal_ticks=%u clean_step=%u clean_ops=%u\n",
		       RLXFW_SPI_INST_B(pr->ran), m[0], m[1], m[2],
		       (unsigned)pr->se_jiffies, (unsigned)pr->pp_polls,
		       (unsigned)pr->pp_jiffies, (unsigned)pr->cal_polls,
		       (unsigned)pr->cal_ticks, (unsigned)pr->clean_step,
		       (unsigned)pr->clean_ops);
	return len;
}

/* Console lines.  D10: per 64 KiB block, the block index and ms since the
 * attempt began; a paced run says so on every line.  `ph` is E (erase), P
 * (program), H (the header page, last), V (read-back). */
#define RLXFW_SPI_INST_SAY_MAX		96

static inline int rlxfw_spi_inst_fmt_step(char *b, int ph, u32 blk, u32 ms,
					  u32 pace)
{
	if (pace)
		return sprintf(b, "RLXFW-SI %c %02u %u paced=%u\n", (char)ph,
			       (unsigned)blk, (unsigned)ms, (unsigned)pace);
	return sprintf(b, "RLXFW-SI %c %02u %u\n", (char)ph, (unsigned)blk,
		       (unsigned)ms);
}

static inline int rlxfw_spi_inst_fmt_go(char *b,
					const struct rlxfw_spi_inst_res *r)
{
	return sprintf(b, "RLXFW-SI-GO %s %s len=%u pace=%u\n",
		       rlxfw_spi_inst_verb_name(r->verb),
		       rlxfw_spi_inst_region_name(r->region1),
		       (unsigned)r->len, (unsigned)r->pace_ms);
}

/* D19's console line, printed once the single SE's effect has been read. */
static inline int rlxfw_spi_inst_fmt_probe(char *b,
				const struct rlxfw_spi_inst_probe *pr)
{
	return sprintf(b, "RLXFW-SI-PROBE se_bytes=%d m=%c%c%c polls=%u "
		       "ticks=%u\n", pr->classified ? pr->se_bytes : -1,
		       pr->m[0] ? (char)pr->m[0] : '-',
		       pr->m[1] ? (char)pr->m[1] : '-',
		       pr->m[2] ? (char)pr->m[2] : '-',
		       (unsigned)pr->se_polls, (unsigned)pr->se_jiffies);
}

static inline int rlxfw_spi_inst_fmt_end(char *b,
					 const struct rlxfw_spi_inst_res *r)
{
	return sprintf(b, "RLXFW-SI-END %s rc=%d cmp=%d ms=%u pace=%u\n",
		       rlxfw_spi_inst_reason_name(r->reason), r->rc, r->cmp_ok,
		       (unsigned)r->ms, (unsigned)r->pace_ms);
}

#endif /* RTL819X_SPI_INSTALL_H */
