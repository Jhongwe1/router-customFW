/*
 * rtl819x-spi-write -- this driver's flash WRITE path: the policy, the
 * counters and the two MTD-shaped entry points.  Declared to kconfig as of
 * R8b item 4 and still OFF in every committed image.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-5, 2026-09-07, forty-first segment (the
 * refusing stubs); rewritten R8b item 4, 2026-10-04, 122nd segment.
 *
 * NOTE: NOT ONE LINE OF IT HAS RUN ANYWHERE.  It is not in any committed
 * image, it has never been on this die, and the only thing exercised at the
 * desk is its refusals, on the host, through tools/test-spi-wrpolicy.sh.
 *
 * CONFIG_MTD_RTL819X_WRITE is declared by config/host-compat/0010 and held at
 * `n` by config/rlxfw-kernel.delta, and `rlxfw-marks verify`'s
 * `absent:rtl819x_spi_write_page` witness on MK5 is the instrument that says
 * this TU is in no image.  In an image built with it, the engine refuses
 * unless ARMED -- `echo 'arm <lo> <hi> <budget>' > /proc/rtl819x-spi`, a
 * window and a byte budget that each accepted operation debits, disarmed at
 * 0 -- and the arm verb refuses a window overlapping the forbidden one.  The
 * register-level primitives, rtl819x_spi_pp_page() and rtl819x_spi_se_block(),
 * are in rtl819x-spi.c inside its claim()/release() bracket; the arithmetic is
 * rtl819x-spi-wrpolicy.h, a header with no #include that the host test runs.
 *
 * NOTE: n_writes IS BLIND TO A VENDOR-SIDE WRITE.  rlxfw's n_writes counts
 * rlxfw's writes, and SPEC.md FLS-26 proved "not one flash byte is written"
 * false for this device.
 *
 * The sequences are the vendor's, read out of spi_common.c in the tree that
 * builds; docs/blind-write-ledger.md § 9.14 records the paths and their
 * depth, and this is NOT a blind write.
 *
 * The driver page: docs/drivers/spi.md.  The four build-time decisions W1-W4,
 * the split between this file and rtl819x-spi.c, what arming is not, the
 * counters, the sequences line by line and what is this file's own: the head
 * it carried until 2026-10-18, verbatim in docs/drivers/spi-write-history.md.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/mtd/mtd.h>
#include <linux/rlxfw-mark.h>

#include "rtl819x-spi-wrpolicy.h"

/* ------------------------------------------------------------------------
 * The engine, which lives in the other TU beside the controller guard.
 *
 * Declared here and not in a header: a header shared by the two would be a
 * third file with an opinion about this interface, and there are exactly two
 * callers and two definitions.  Both are compiled under the same CONFIG_ as
 * this file, so a configuration that has one has the other.
 * ------------------------------------------------------------------------ */

extern int rtl819x_spi_pp_page(u32 addr, u32 len, const u8 *buf);
extern int rtl819x_spi_se_block(u32 addr);
extern void rtl819x_spi_note_write(int erase);

/* ------------------------------------------------------------------------
 * State.
 * ------------------------------------------------------------------------ */

static struct rlxfw_spi_wr_arm rtl819x_spi_wr_arm;

static unsigned long rtl819x_spi_wr_n_prog;
static unsigned long rtl819x_spi_wr_n_erase;
static unsigned long rtl819x_spi_wr_n_bytes;
static unsigned long rtl819x_spi_wr_n_engine_fail;
static unsigned long rtl819x_spi_wr_n_arm_ok;
static unsigned long rtl819x_spi_wr_n_refused[RLXFW_SPI_WR_R_COUNT];

/* The total, kept separately so a reader does not have to add nine numbers to
 * answer "did anything refuse".  The invariant n_refused_total == sum of the
 * array is printed by rtl819x-spi.c rather than asserted here. */
static unsigned long rtl819x_spi_wr_n_refused_total;

/* The errno each reason becomes.  A table and not a switch, so adding a
 * reason without deciding its errno does not compile.
 *
 * NOTE: EOPNOTSUPP IS NOT IN IT, and that is the one externally visible change
 * this file makes to an existing reading.  In an image where this TU is NOT
 * linked, rtl819x-spi.c's stubs still answer -EOPNOTSUPP and
 * config/mfgtest.sh's MT-FLASH-2 is untouched.  In an image where it IS
 * linked, an unarmed write answers -EACCES.  So no card may carry the errno
 * as a typed constant: /proc/rtl819x-spi prints `unarmed_rc` and the card
 * compares against that.  docs/mfgtest.md § MT-FLASH-2 says so.
 */
static const int rtl819x_spi_wr_errno[RLXFW_SPI_WR_R_COUNT] = {
	0,			/* RLXFW_SPI_WR_OK */
	-EPERM,			/* R_FORBIDDEN  -- the loader or H601 */
	-EINVAL,		/* R_RANGE */
	-EACCES,		/* R_UNARMED */
	-EPERM,			/* R_OUTSIDE    -- outside the armed window */
	-ENOSPC,		/* R_BUDGET */
	-EINVAL,		/* R_MISALIGNED */
	-EINVAL,		/* R_BADLEN */
	-EINVAL,		/* R_PAGECROSS */
	-EPROTO,		/* R_GEOM       -- grain != mtd->erasesize */
};

/* ------------------------------------------------------------------------
 * Refusal bookkeeping.  One function, so `git grep rtl819x_spi_wr_refuse` is
 * the complete list of places this driver says no.
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_wr_refuse(int reason)
{
	if (reason <= 0 || reason >= RLXFW_SPI_WR_R_COUNT) {
		/* Unreachable from the policy header, which returns only the
		 * enum.  Kept because a future reason added there without a
		 * row here must fail LOUDLY and not index off the table. */
		rtl819x_spi_wr_n_refused_total++;
		return -EPROTO;
	}
	rtl819x_spi_wr_n_refused[reason]++;
	rtl819x_spi_wr_n_refused_total++;
	return rtl819x_spi_wr_errno[reason];
}

/* ------------------------------------------------------------------------
 * The two entry points rtl819x-spi.c's mtd_info routes to.
 *
 * The names are the two symbols config/rlxfw-marks.tsv's MK5 witnesses.  They
 * keep their names and their EXPORT_SYMBOLs for the reason the R5-5 comment
 * gave and which has not stopped being true: a symbol-absence proof over a
 * `static` function proves nothing, because absent and inlined read the same
 * in System.map, and MEASURED on the shipped image the compiler did inline most of
 * rtl819x-spi.c's own statics right out of it.  Making these two global forces
 * the linker to emit them.  A cleanup that removes an export with no importer
 * would silently turn MK5's witness into a check that cannot fail.
 *
 * Their SIGNATURES changed this segment, from (u32, u32, const u8 *) and
 * (u32) to the MTD shapes.  MK5's witness is a NAME, so the row is unaffected.
 * ------------------------------------------------------------------------ */

int rtl819x_spi_write_page(struct mtd_info *mtd, loff_t to, size_t len,
			   size_t *retlen, const u_char *buf)
{
	int reason, rc;
	u32 addr;

	if (retlen)
		*retlen = 0;

	/* loff_t is signed and 64-bit here; a negative or oversized `to` must
	 * not be truncated into a legal u32.  READ rtl819x-spi.c's mtd_read,
	 * which makes the same check for the same reason. */
	if (to < 0 || to >= (loff_t)RLXFW_SPI_WR_CHIP ||
	    len > (size_t)RLXFW_SPI_WR_CHIP)
		return rtl819x_spi_wr_refuse(RLXFW_SPI_WR_R_RANGE);
	addr = (u32)to;

	reason = rlxfw_spi_wr_chk_prog(&rtl819x_spi_wr_arm, addr, (u32)len);
	if (reason != RLXFW_SPI_WR_OK)
		return rtl819x_spi_wr_refuse(reason);

	rc = rtl819x_spi_pp_page(addr, (u32)len, (const u8 *)buf);
	if (rc) {
		/* NOT a refusal: the policy said yes and the controller said
		 * no.  Counting it as a refusal would make the refusal
		 * counters say a layer held when none did. */
		rtl819x_spi_wr_n_engine_fail++;
		rlxfw_markx("SW-PPFAIL", (unsigned)-rc);
		return rc;
	}

	/* The budget is debited only on success, so a failed engine does not
	 * silently consume the owner's authorisation. */
	rtl819x_spi_wr_arm.budget -= (u32)len;
	if (rtl819x_spi_wr_arm.budget == 0u)
		rtl819x_spi_wr_arm.armed = 0;
	rtl819x_spi_wr_n_prog++;
	rtl819x_spi_wr_n_bytes += len;
	rtl819x_spi_note_write(0);
	if (retlen)
		*retlen = len;
	return 0;
}
EXPORT_SYMBOL(rtl819x_spi_write_page);

int rtl819x_spi_erase_sector(struct mtd_info *mtd, struct erase_info *instr)
{
	u32 grain = RLXFW_SPI_WR_ERASE_GRAIN;
	u32 addr, len, done;
	int reason, rc;

	instr->state = MTD_ERASE_FAILED;

	if (instr->addr >= (u64)RLXFW_SPI_WR_CHIP ||
	    instr->len > (u64)RLXFW_SPI_WR_CHIP)
		return rtl819x_spi_wr_refuse(RLXFW_SPI_WR_R_RANGE);
	addr = (u32)instr->addr;
	len  = (u32)instr->len;

	/* mtd->erasesize is read from the device rather than from a constant
	 * of this file's, so the 未定 guard compares two independently
	 * maintained numbers.  See RLXFW_SPI_WR_ERASE_GRAIN. */
	reason = rlxfw_spi_wr_chk_erase(&rtl819x_spi_wr_arm, addr, len, grain,
					mtd ? (u32)mtd->erasesize : 0u);
	if (reason != RLXFW_SPI_WR_OK)
		return rtl819x_spi_wr_refuse(reason);

	/* The loop is NOT restarted on failure and does not continue past
	 * one: a partially erased range is reported as a failure with the
	 * byte count visible in n_bytes, never as a success. */
	for (done = 0u; done < len; done += grain) {
		rc = rtl819x_spi_se_block(addr + done);
		if (rc) {
			rtl819x_spi_wr_n_engine_fail++;
			rlxfw_markx("SW-SEFAIL", (unsigned)-rc);
			rtl819x_spi_wr_n_bytes += done;
			return rc;
		}
		rtl819x_spi_wr_n_erase++;
		rtl819x_spi_note_write(1);
	}

	rtl819x_spi_wr_arm.budget -= len;
	if (rtl819x_spi_wr_arm.budget == 0u)
		rtl819x_spi_wr_arm.armed = 0;
	rtl819x_spi_wr_n_bytes += len;
	instr->state = MTD_ERASE_DONE;
	/* The callback is invoked only on success, matching the stub this
	 * replaces: READ drivers/mtd/mtdchar.c, which waits on one only when
	 * erase() returned 0, so a refusal must not leave a sleeper. */
	if (instr->callback)
		instr->callback(instr);
	return 0;
}
EXPORT_SYMBOL(rtl819x_spi_erase_sector);

/* ------------------------------------------------------------------------
 * The arm and disarm verbs, dispatched from rtl819x-spi.c's write_proc so
 * that this driver keeps ONE writable /proc entry.  That constraint is the
 * existing driver's and is not relaxed here: a second writable entry would be
 * a second way to reach the controller.
 * ------------------------------------------------------------------------ */

int rtl819x_spi_wr_do_arm(u32 lo, u32 hi, u32 budget)
{
	int reason = rlxfw_spi_wr_chk_arm(lo, hi, budget);

	if (reason != RLXFW_SPI_WR_OK) {
		rlxfw_markx("SW-ARMNO", (unsigned)reason);
		return rtl819x_spi_wr_refuse(reason);
	}
	rtl819x_spi_wr_arm.lo = lo;
	rtl819x_spi_wr_arm.hi = hi;
	rtl819x_spi_wr_arm.budget = budget;
	rtl819x_spi_wr_arm.armed = 1;
	rtl819x_spi_wr_n_arm_ok++;
	rlxfw_markx("SW-ARM", budget);
	return 0;
}
EXPORT_SYMBOL(rtl819x_spi_wr_do_arm);

void rtl819x_spi_wr_do_disarm(void)
{
	rtl819x_spi_wr_arm.armed = 0;
	rtl819x_spi_wr_arm.budget = 0u;
	rtl819x_spi_wr_arm.lo = 0u;
	rtl819x_spi_wr_arm.hi = 0u;
	rlxfw_mark("SW-DISARM");
}
EXPORT_SYMBOL(rtl819x_spi_wr_do_disarm);

/*
 * The arm in force, for rtl819x-spi.c's install path (R8b Gap A, D20).
 *
 * A COPY, never a pointer: the caller can compare against this state and
 * cannot change it, so this file stays the one owner of the arm.  It is read
 * UNDER rtl819x_spi_lock, which lives in rtl819x-spi.c: the install path holds
 * it across this call and its disarm, and every writer of this state holds it
 * too -- the arm and disarm verbs since Gap A, mtd->write and mtd->erase since
 * item 4 -- so the four fields are read as one state, never half an arm.
 *
 * -EINVAL on a NULL destination, and the caller zeroes its copy before the
 * call, so a failed read is an UNARMED copy plus an error: both halves refuse.
 */
int rtl819x_spi_wr_get_arm(struct rlxfw_spi_wr_arm *out)
{
	if (!out)
		return -EINVAL;
	*out = rtl819x_spi_wr_arm;
	return 0;
}
EXPORT_SYMBOL(rtl819x_spi_wr_get_arm);

/* ------------------------------------------------------------------------
 * What /proc prints.  The caller owns the page budget, so this returns the
 * length it wrote and writes nothing without being asked.
 *
 * CAUTION: NO FLASH BYTE, NO DIGEST, NO VALUE.  rtl819x-spi.c's header permits
 * "digests over the complement, an offset, counters and controller registers"
 * plus the JEDEC id.  This adds counters, two addresses that CAME FROM THE
 * TYPED VERB rather than from the flash, and a budget.  An armed window's
 * bounds are the owner's own input echoed back, which is what makes a card
 * able to check that the arm it typed is the arm in force.
 * ------------------------------------------------------------------------ */

int rtl819x_spi_wr_proc(char *p)
{
	int len = 0;
	int i;

	len += sprintf(p + len, "wr_version %s\n", "rtl819x-spi-write 2.0");
	len += sprintf(p + len, "wr_armed %d\n", rtl819x_spi_wr_arm.armed);
	len += sprintf(p + len, "wr_arm_lo %08X\n", rtl819x_spi_wr_arm.lo);
	len += sprintf(p + len, "wr_arm_hi %08X\n", rtl819x_spi_wr_arm.hi);
	len += sprintf(p + len, "wr_budget %u\n", rtl819x_spi_wr_arm.budget);
	len += sprintf(p + len, "wr_n_arm_ok %lu\n", rtl819x_spi_wr_n_arm_ok);
	len += sprintf(p + len, "wr_n_prog %lu\n", rtl819x_spi_wr_n_prog);
	len += sprintf(p + len, "wr_n_erase %lu\n", rtl819x_spi_wr_n_erase);
	len += sprintf(p + len, "wr_n_bytes %lu\n", rtl819x_spi_wr_n_bytes);
	len += sprintf(p + len, "wr_n_engine_fail %lu\n",
		       rtl819x_spi_wr_n_engine_fail);
	len += sprintf(p + len, "wr_n_refused %lu\n",
		       rtl819x_spi_wr_n_refused_total);
	/* One line, nine numbers, in enum order, so adding a reason cannot
	 * silently drop it from the output.  The names are in
	 * rtl819x-spi-wrpolicy.h and a card resolves them from there. */
	len += sprintf(p + len, "wr_refused_by");
	for (i = 1; i < RLXFW_SPI_WR_R_COUNT; i++)
		len += sprintf(p + len, " %lu", rtl819x_spi_wr_n_refused[i]);
	len += sprintf(p + len, "\n");
	len += sprintf(p + len, "wr_reasons %d\n", RLXFW_SPI_WR_R_COUNT - 1);
	/* The geometry, printed so no card carries it as a typed constant and
	 * so the 未定 is visible on the device. */
	len += sprintf(p + len, "wr_grain %08X\n",
		       (unsigned)RLXFW_SPI_WR_ERASE_GRAIN);
	len += sprintf(p + len, "wr_page %u\n", (unsigned)RLXFW_SPI_WR_PAGE);
	len += sprintf(p + len, "wr_never_hi %08X\n",
		       (unsigned)RLXFW_SPI_WR_NEVER_HI);
	return len;
}
EXPORT_SYMBOL(rtl819x_spi_wr_proc);

/* The widest this can emit, for rtl819x-spi.c's page budget.  Derived rather
 * than guessed: 16 fixed lines at under 32 bytes each is 512, and the
 * wr_refused_by line is 13 + 9 * 21 = 202 at ULONG_MAX.  768 is the next
 * round number above 714 and is checked by the caller BEFORE this runs. */
#define RTL819X_SPI_WR_PROC_MAX 768
int rtl819x_spi_wr_proc_max(void) { return RTL819X_SPI_WR_PROC_MAX; }
EXPORT_SYMBOL(rtl819x_spi_wr_proc_max);

/*
 * The initcall.  It installs NOTHING and arms NOTHING: the mtd_info's
 * function pointers are rtl819x-spi.c's to set, and an image that boots armed
 * would be the whole point of the arming thrown away.  All it does is say
 * that this TU is in the image, which is the state MK5's `absent:` witness
 * exists to deny.
 */
static int __init rtl819x_spi_write_init(void)
{
	rlxfw_markx("SW0", (unsigned)RLXFW_SPI_WR_ERASE_GRAIN);
	return 0;
}

late_initcall(rtl819x_spi_write_init);
