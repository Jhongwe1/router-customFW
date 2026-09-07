/*
 * rtl819x-spi-write -- the designated home of this driver's flash WRITE
 * path, declared and deliberately not built.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-5, 2026-09-07, forty-first segment.
 * config/rlxfw-marks.tsv declares it as
 *
 *     obj-$(CONFIG_MTD_RTL819X_WRITE) += rtl819x-spi-write.o
 *
 * and CONFIG_MTD_RTL819X_WRITE is not declared to kconfig anywhere.  An
 * undeclared CONFIG_ expands to empty in GNU Make, so this file is not
 * compiled, and no menu, no defconfig and no `oldconfig` can change that.
 * The positive control is a make-level override in a DISCARDED tree,
 * `make CONFIG_MTD_RTL819X_WRITE=y`, because `obj-$(...)` is plain Make and
 * needs no kconfig at all to fire.
 *
 * ------------------------------------------------------------------------
 * WHAT D4 PROVES, AND -- SAID PLAINLY -- WHAT IT DOES NOT
 * ------------------------------------------------------------------------
 *
 * D4 proves that the translation unit which is THIS DRIVER's write path is
 * not in the shipped image, by symbol absence in System.map and `nm
 * vmlinux`, with rlxfw-marks.py's `absent:` witness doing the checking and
 * the control build making that witness go red.
 *
 * 🔴 It does NOT prove that no code in the image can write this flash, and
 * the write-up must not let it read that way.  量 2026-09-07: the VENDOR's
 * write path is in this image and always has been.
 * CONFIG_RTL819X_SPI_FLASH=y, spi_probe.c's spi_chip_setup() installs
 * `mtd->write = mtd_spi_write` and `mtd->erase = mtd_spi_erase`
 * unconditionally, and those reach ComSrlCmd_ComWriteData /
 * PageWrite_111002 / ComSrlCmd_SE -- real page-program and sector-erase
 * sequences on the same four registers.  What keeps them from being reached
 * is the userspace surface: /dev/mtd0ro is odd-minor, which mtdchar refuses
 * to open for writing (FW-26's reasoning, CONFIG_MTD_CHAR), and
 * /dev/mtdblock1 is declared 0400 in config/rlxfw-initramfs.tsv.  Those are
 * access controls on a path that exists, not the absence of a path.
 *
 * So the accurate sentence is: **rlxfw contributes no flash-write code to
 * this image.**  Not: this image cannot write flash.  docs/KNOWN-ISSUES.md
 * carries the narrower one.
 *
 * ------------------------------------------------------------------------
 * WHY THE BODIES REFUSE INSTEAD OF WORKING
 * ------------------------------------------------------------------------
 *
 * Because mainline is zero-write through R9 and a working page-program in
 * this tree would be a loaded gun that one make-level override away from
 * being aimed.  These two functions are the ENTRY POINTS -- the place a
 * write path goes, the signatures the MTD core would call, the counter it
 * would move -- and they return -EPERM.  When R9 arrives, what changes is a
 * body, not a build system, not a Makefile line, and not a decision about
 * where write code lives.
 *
 * ⚠️ THAT MAKES D4's CONTROL A CONTROL OVER STUBS, and the notes say so.
 * A reviewer who reads "the write path is not in the image" should be able
 * to find out in one hop that the write path is also not written yet.  Both
 * sentences are true and only the pair is honest.
 *
 * What a real implementation would be, so the shape is on the record rather
 * than in someone's head -- all 讀, from spi_common.c and this unit's own
 * loader, none of it executed anywhere:
 *
 *   erase a 4 KiB sector   WREN (0x06) -> SE (0x20) with a 3-byte address
 *                          -> poll RDSR (0x05) bit 0 (WIP) until clear
 *   program a 256B page    WREN (0x06) -> PP (0x02), 3-byte address, then
 *                          the data through SFDR in 4-byte phases
 *                          -> poll RDSR bit 0 until clear
 *
 * and every one of those would have to be preceded by the same claim /
 * restore / read-back guard rtl819x-spi.c uses, plus an offset check that
 * refuses CLAUDE.md's two Never regions -- 0x000000-0x005FFF and
 * H601 at 0x006000-0x007FFF -- which is the ONE thing this file would have
 * that the vendor's does not.  量 docs/loader-flash-write.md 1: the vendor's
 * burn() has no lower bound at all and will write offset 0 if an image
 * section asks it to.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/mtd/mtd.h>
#include <linux/rlxfw-mark.h>

/* The counter the entry points move.  It is separate from rtl819x-spi.c's
 * n_writes on purpose: this file is not linked, so a shared symbol would be
 * a reference from the main TU to a TU that is not there. */
static unsigned long rtl819x_spi_write_refused;

/*
 * The two symbols config/rlxfw-marks.tsv names in its `absent:` witness.
 * Their being in System.map is exactly what the control build produces and
 * what makes that row go red.
 *
 * 🔴 THE `EXPORT_SYMBOL`s BELOW ARE LOAD-BEARING AND ARE NOT FOR A
 * CONSUMER.  Nothing imports these.  They are here because a symbol-absence
 * proof over a `static` function proves NOTHING -- absent and inlined read
 * the same -- and 量 on the shipped image, the compiler did inline most of
 * rtl819x-spi.c's own statics right out of System.map.  Making these two
 * global forces the linker to emit them, so the control build shows
 * `801a8a20 T rtl819x_spi_write_page` with a capital T and `verify` can go
 * red on it.  A later cleanup that removes an export with no importer would
 * silently turn D4 into a check that cannot fail.
 */
int rtl819x_spi_write_page(u32 addr, u32 len, const u8 *buf)
{
	(void)addr;
	(void)len;
	(void)buf;
	rtl819x_spi_write_refused++;
	return -EPERM;
}
EXPORT_SYMBOL(rtl819x_spi_write_page);

int rtl819x_spi_erase_sector(u32 addr)
{
	(void)addr;
	rtl819x_spi_write_refused++;
	return -EPERM;
}
EXPORT_SYMBOL(rtl819x_spi_erase_sector);

/*
 * In the control build this initcall is the only thing that runs, and all it
 * does is say so.  It deliberately does NOT install itself on the mtd: the
 * point of the control is that the SYMBOLS appear, and reaching across to
 * another translation unit's mtd_info would give this file a dependency it
 * has no reason to have.
 */
static int __init rtl819x_spi_write_init(void)
{
	rlxfw_markx("SW0", (unsigned)rtl819x_spi_write_refused);
	return 0;
}

late_initcall(rtl819x_spi_write_init);
