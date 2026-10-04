/*
 * rtl819x-spi-wrpolicy -- every refusal the flash WRITE path makes, as pure
 * arithmetic over u32, in a header with NO #include of its own.
 *
 * THIS FILE IS NOT REALTEK'S.  R8b item 4, 2026-10-04, 122nd segment.
 *
 * ------------------------------------------------------------------------
 * WHY A HEADER AND NOT A .c
 * ------------------------------------------------------------------------
 *
 * Because the one thing about this write path that CAN be exercised at the
 * desk is its refusals, and a decision that cannot be exercised is a decision
 * nobody checked.  With no #include, this file compiles unchanged
 *
 *   - into the kernel TU rtl819x-spi-write.c, after <linux/types.h>, and
 *   - into tools/test-spi-wrpolicy.c on the host, after four typedefs,
 *
 * so the arithmetic the board would run is the arithmetic the host test runs.
 * The alternative -- a second copy of the bounds test in the harness -- is the
 * shape where a guard and its test agree with each other and both are wrong.
 *
 * ⚠️ WHAT THIS FILE DELIBERATELY DOES NOT HOLD: a register, an opcode, a
 * delay, a lock, or anything that touches the controller.  Those live in
 * rtl819x-spi.c beside the save/restore/read-back guard that already owns the
 * controller, because two owners of that guard would be worse than one
 * indirection.  So a green host test says the POLICY is right on the host.  It
 * says nothing whatever about the silicon -- see § 5 of
 * notes/spi-mtd-driver.md.
 *
 * ------------------------------------------------------------------------
 * THE ORDER OF THE CHECKS IS THE DESIGN, NOT A STYLE
 * ------------------------------------------------------------------------
 *
 * The forbidden-window test runs FIRST and reads nothing but the request.  It
 * does not consult the arming state, the budget, the alignment or the
 * geometry, so there is no sequence of other decisions that can reach past it.
 * CLAUDE.md: *a containment rule that holds only if the experiment comes out
 * as expected is not a containment rule.*  The host test drives the armed
 * case against a forbidden address on purpose, because "refused while
 * unarmed" would be a pass that proves nothing.
 *
 * Everything after it is ordered cheapest-first with one rule: a check whose
 * arithmetic could overflow runs AFTER the range check that makes it safe.
 */

#ifndef RTL819X_SPI_WRPOLICY_H
#define RTL819X_SPI_WRPOLICY_H

/* ------------------------------------------------------------------------
 * The geometry.
 * ------------------------------------------------------------------------ */

/* FLS-14, 量: the part is 4,194,304 bytes and two committed dumps of it are
 * byte-identical over all of it. */
#define RLXFW_SPI_WR_CHIP	0x00400000u

/*
 * 🔴 THE ERASE GRANULARITY, AND IT IS 未定.  THIS IS THE ONE LINE.
 *
 * SPEC.md `FW-187` 殘留 and `FW-191` 殘留: whether this part's erase opcode
 * clears 4,096 or 65,536 bytes is NOT settled, and the difference is a
 * brick precondition rather than a detail.  At 4 KiB there are eight erase
 * blocks of margin between H601 and 0x010000; at 64 KiB there is ONE block,
 * and that block holds the loader, H601, COMPDS and COMPCS together.
 *
 * The two readings on hand, neither of them a measurement of this part:
 *
 *   讀  /proc/mtd reports `erasesize 00001000` on all three partitions
 *       (量 2026-10-04, bench/2026-10-04/PRE-MTD, `FW-187`) -- but that is
 *       rtl819x-spi.c's own RTL819X_SPI_ERASESIZE and the vendor map's
 *       partition constants, i.e. software, not something the chip said.
 *   讀  the vendor's UNKNOWN fallback.  `FW-191` measured the part as
 *       1C7016, and 量 2026-10-04 at the desk: 0x1C7016 appears NOWHERE in
 *       the GPL drop that builds -- the Eon entries are 1c3115, 1c3116,
 *       1c3015, 1c3016 -- so spi_regist() takes its UNKNOWN branch
 *       (spi_common.c:574) and calls set_flash_info(..., SIZE_064K,
 *       SIZE_004K, SIZE_256B, "UNKNOWN", ComSrlCmd_SE, ...).  So the code
 *       that has driven this board since 2018 erases with SE, opcode 0x20,
 *       and calls the sector 4,096 bytes -- while recording a 64 KiB
 *       block_size it never uses.  That is the fallback's constant applied
 *       because the part was not recognised; it is not a reading of the part.
 *
 * The decisive 量 is an actual erase, which is a flash write, which belongs
 * to R8b under the owner's dated yes for that exact payload.  Until then this
 * value is a PLACEHOLDER, and the guard against it being the wrong one is
 * rlxfw_spi_wr_chk_erase()'s mtd_erasesize conjunct below: a tree where this
 * line and rtl819x-spi.c's RTL819X_SPI_ERASESIZE disagree refuses EVERY
 * erase instead of clearing eight times what was asked.
 *
 * TO SUBSTITUTE ITEM 1's SETTLED VALUE: edit the next line and nothing else,
 * then make RTL819X_SPI_ERASESIZE in rtl819x-spi.c equal to it in the same
 * commit.  The mismatch refusal is what makes forgetting the second edit
 * loud rather than silent.
 */
#define RLXFW_SPI_WR_ERASE_GRAIN	0x00001000u	/* 未定 FW-187/FW-191 */

/*
 * The page-program length bound.  讀, from the vendor's own write path in the
 * tree that builds: ComSrlCmd_ComWriteSector (spi_common.c:1003-1007) issues
 * pfPageWrite exactly page_cnt times with page_size bytes each, advancing the
 * address by page_size, and set_flash_info (:605-606) sets page_size from the
 * table's SIZE_256B and page_cnt = sector_size / page_size.  Every entry in
 * that table and the UNKNOWN fallback pass SIZE_256B.  So the vendor NEVER
 * issues a PP longer than 256 bytes, on any part it knows and on this one.
 *
 * ⚠️ 推, and the direction is the safe one: that a PP crossing a page
 * boundary WRAPS to the start of the page rather than continuing is JEDEC's
 * definition of the opcode and this part's datasheet is not on hand (`FW-191`:
 * the draft datasheet here is the SoC's, not the flash's).  So the bound is
 * enforced conservatively -- a request that crosses is refused, never split
 * silently -- and being wrong about the wrap costs a refused write.  The
 * vendor's ComSrlCmd_ComWrite (spi_common.c:964) bounds uiLen by nothing at
 * all; this is the one place where rlxfw is stricter rather than merely
 * different.
 */
#define RLXFW_SPI_WR_PAGE	0x100u

/*
 * CLAUDE.md's two Never rows, as one half-open window: the loader at
 * 0x000000-0x005FFF (a brick is unrecoverable and there is no spare) and H601
 * at 0x006000-0x007FFF (this unit's MAC and radio calibration, which no reset
 * restores).  They are adjacent, so one window is the whole rule.
 *
 * 🔴 THIS IS THE ONE THING THIS DRIVER HAS THAT THE VENDOR'S DOES NOT, and
 * the vendor's absence of it is 讀 rather than asserted: spi_cmd.c's
 * mtd_spi_erase() has its `skip 1st block erase` guard inside `#if 0`
 * (:46-53), so instr->addr = 0 is accepted and sector 0 is erased; and
 * docs/loader-flash-write.md 1 已 量 that the loader's burn() has no lower
 * bound either.
 */
#define RLXFW_SPI_WR_NEVER_LO	0x00000000u
#define RLXFW_SPI_WR_NEVER_HI	0x00008000u

/* ------------------------------------------------------------------------
 * The reasons.  One per refusal, because a single errno for nine different
 * refusals is a counter that cannot say which layer held.
 * ------------------------------------------------------------------------ */

enum {
	RLXFW_SPI_WR_OK = 0,
	RLXFW_SPI_WR_R_FORBIDDEN,	/* touches the loader or H601 */
	RLXFW_SPI_WR_R_RANGE,		/* off the end of the chip, or len 0 */
	RLXFW_SPI_WR_R_UNARMED,		/* no arm in force */
	RLXFW_SPI_WR_R_OUTSIDE,		/* outside the armed window */
	RLXFW_SPI_WR_R_BUDGET,		/* the arm's byte budget is spent */
	RLXFW_SPI_WR_R_MISALIGNED,	/* erase addr not grain-aligned */
	RLXFW_SPI_WR_R_BADLEN,		/* erase len not a grain multiple, or
					 * a program longer than a page */
	RLXFW_SPI_WR_R_PAGECROSS,	/* a program spanning two pages */
	RLXFW_SPI_WR_R_GEOM,		/* grain != mtd->erasesize */
	RLXFW_SPI_WR_R_COUNT		/* the array size; not a reason */
};

/* ------------------------------------------------------------------------
 * The arming state.  A plain struct so the host test can build one.
 * ------------------------------------------------------------------------ */

struct rlxfw_spi_wr_arm {
	int armed;		/* 0 = nothing may be written, at all */
	u32 lo;			/* the permitted window, half-open [lo, hi) */
	u32 hi;
	u32 budget;		/* bytes still permitted; 0 disarms */
};

/* ------------------------------------------------------------------------
 * The checks.
 * ------------------------------------------------------------------------ */

/* Does the half-open [lo, hi) touch the forbidden window?
 *
 * Both terms are written out although RLXFW_SPI_WR_NEVER_LO is 0 and the
 * second therefore reduces to `hi != 0`.  It is not dead: it is what makes an
 * EMPTY range not overlap, and it is what keeps this function right if the
 * window ever stops starting at zero.  The host test drives lo == hi == 0 for
 * exactly that reason. */
static inline int rlxfw_spi_wr_overlaps_never(u32 lo, u32 hi)
{
	return (lo < RLXFW_SPI_WR_NEVER_HI) && (hi > RLXFW_SPI_WR_NEVER_LO);
}

/* [addr, addr+len) wholly inside the chip, and non-empty.
 * Written as a subtraction rather than `addr + len <= CHIP` so it cannot
 * overflow; every caller runs this before any other arithmetic on len. */
static inline int rlxfw_spi_wr_in_chip(u32 addr, u32 len)
{
	if (len == 0u)
		return 0;
	if (addr >= RLXFW_SPI_WR_CHIP)
		return 0;
	return len <= RLXFW_SPI_WR_CHIP - addr;
}

/* The arm, checked against the range the operation will actually touch.
 * Called only after the forbidden and range tests have passed. */
static inline int rlxfw_spi_wr_chk_arm_state(const struct rlxfw_spi_wr_arm *a,
				      u32 lo, u32 hi)
{
	if (!a->armed)
		return RLXFW_SPI_WR_R_UNARMED;
	if (lo < a->lo || hi > a->hi)
		return RLXFW_SPI_WR_R_OUTSIDE;
	if (a->budget < hi - lo)
		return RLXFW_SPI_WR_R_BUDGET;
	return RLXFW_SPI_WR_OK;
}

/*
 * A page program of `len` bytes at `addr`.
 *
 * Order: forbidden, range, page geometry, then the arm.  The geometry comes
 * before the arm so that a malformed request reports the malformation rather
 * than UNARMED -- a card that reads UNARMED for a request that is also
 * oversized would believe the length was accepted.
 */
static inline int rlxfw_spi_wr_chk_prog(const struct rlxfw_spi_wr_arm *a,
				 u32 addr, u32 len)
{
	if (!rlxfw_spi_wr_in_chip(addr, len)) {
		/* The forbidden test still runs, on the clamped range, so a
		 * nonsense length at offset 0 is reported as FORBIDDEN and not
		 * as a mere range error.  Said plainly: the stronger refusal
		 * wins whenever both apply. */
		if (addr < RLXFW_SPI_WR_NEVER_HI)
			return RLXFW_SPI_WR_R_FORBIDDEN;
		return RLXFW_SPI_WR_R_RANGE;
	}
	if (rlxfw_spi_wr_overlaps_never(addr, addr + len))
		return RLXFW_SPI_WR_R_FORBIDDEN;
	if (len > RLXFW_SPI_WR_PAGE)
		return RLXFW_SPI_WR_R_BADLEN;
	if ((addr & (RLXFW_SPI_WR_PAGE - 1u)) + len > RLXFW_SPI_WR_PAGE)
		return RLXFW_SPI_WR_R_PAGECROSS;
	return rlxfw_spi_wr_chk_arm_state(a, addr, addr + len);
}

/*
 * An erase of `len` bytes at `addr`, at granularity `grain`, on a device
 * reporting `mtd_erasesize`.
 *
 * 🔴 IT REFUSES A NON-MULTIPLE LENGTH RATHER THAN WIDENING TO THE CONTAINING
 * BLOCK, and that is the deliberate difference from the code on this board.
 * 讀 spi_cmd.c mtd_spi_erase() in the tree that builds: its len-alignment
 * check is commented out (:57-60), and then :71-78 round len UP --
 * `len = len - (len & (mtd->erasesize-1)) + mtd->erasesize;` followed by
 * `if (len < mtd->erasesize) len = mtd->erasesize;`.  So asking the vendor's
 * driver to erase one byte erases a whole sector, silently, and returns 0.
 * Here that is -EINVAL and a counter.
 *
 * The forbidden test is applied to the range the erase would CLEAR, which is
 * the grain-aligned block containing addr onwards -- not to addr.  At a
 * 64 KiB grain an erase at 0x008000 would clear from 0x000000, so a check on
 * addr alone would permit the loader's destruction while reading as a guard.
 */
static inline int rlxfw_spi_wr_chk_erase(const struct rlxfw_spi_wr_arm *a,
				  u32 addr, u32 len, u32 grain,
				  u32 mtd_erasesize)
{
	u32 blk_lo, blk_hi;

	/* The geometry self-check, before anything derived from grain.  A
	 * grain that is not a power of two at least a page wide makes every
	 * mask below meaningless, so it is tested rather than assumed. */
	if (grain == 0u || (grain & (grain - 1u)) != 0u ||
	    grain < RLXFW_SPI_WR_PAGE || grain > RLXFW_SPI_WR_CHIP)
		return RLXFW_SPI_WR_R_GEOM;
	/* 未定's guard.  See RLXFW_SPI_WR_ERASE_GRAIN. */
	if (grain != mtd_erasesize)
		return RLXFW_SPI_WR_R_GEOM;

	blk_lo = addr & ~(grain - 1u);
	if (!rlxfw_spi_wr_in_chip(blk_lo, len)) {
		if (blk_lo < RLXFW_SPI_WR_NEVER_HI)
			return RLXFW_SPI_WR_R_FORBIDDEN;
		return RLXFW_SPI_WR_R_RANGE;
	}
	blk_hi = blk_lo + len;
	if (rlxfw_spi_wr_overlaps_never(blk_lo, blk_hi))
		return RLXFW_SPI_WR_R_FORBIDDEN;

	if (addr != blk_lo)
		return RLXFW_SPI_WR_R_MISALIGNED;
	if ((len & (grain - 1u)) != 0u)
		return RLXFW_SPI_WR_R_BADLEN;

	return rlxfw_spi_wr_chk_arm_state(a, blk_lo, blk_hi);
}

/*
 * The arm verb's own refusal.  Arming a window that overlaps the forbidden
 * one is refused HERE as well as at every use, so the forbidden refusal is
 * not the only thing standing between a typo and the loader.  Two independent
 * places, and the host test fires both.
 */
static inline int rlxfw_spi_wr_chk_arm(u32 lo, u32 hi, u32 budget)
{
	if (hi <= lo)
		return RLXFW_SPI_WR_R_RANGE;
	if (hi > RLXFW_SPI_WR_CHIP)
		return RLXFW_SPI_WR_R_RANGE;
	if (budget == 0u || budget > hi - lo)
		return RLXFW_SPI_WR_R_BUDGET;
	if (rlxfw_spi_wr_overlaps_never(lo, hi))
		return RLXFW_SPI_WR_R_FORBIDDEN;
	return RLXFW_SPI_WR_OK;
}

#endif /* RTL819X_SPI_WRPOLICY_H */
