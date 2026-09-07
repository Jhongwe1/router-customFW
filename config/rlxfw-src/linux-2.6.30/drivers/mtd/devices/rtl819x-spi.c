/*
 * rtl819x-spi -- a READ-ONLY MTD device on the RTL8196E's SPI flash
 * controller, driven by PROGRAMMED I/O through SFCSR/SFDR.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-5, 2026-09-07, forty-first segment.  It is
 * staged into drivers/mtd/devices/ by tools/rlxfw-marks.py from
 * config/rlxfw-src/; config/rlxfw-marks.tsv carries the two Kbuild lines --
 * the one that links this file, and the CONDITIONAL one that declares the
 * write translation unit and deliberately does not build it.
 *
 * ------------------------------------------------------------------------
 * WHAT IS DIFFERENT ABOUT THIS DRIVER, AND IT IS NOT A GOOD THING
 * ------------------------------------------------------------------------
 *
 * Every other driver in this gate had the peripheral to itself.  This one
 * does not.  量 2026-09-07, on the baseline config and on the r54 vmlinux:
 *
 *   CONFIG_RTL819X_SPI_FLASH=y, so drivers/mtd/chips/rtl819x/ IS in this
 *   image, and it drives the SAME four registers.  Its mtd->read is
 *   mtd_spi_read -> do_spi_read -> spi_flash_info[chip].pfRead ->
 *   SpiRead_11110B -> ComSrlCmd_ComRead, which is PROGRAMMED I/O, not the
 *   memory-mapped window.  Its mtd->write and mtd->erase exist.  There is
 *   no lock anywhere on that path.
 *
 * 🔴 THAT CORRECTS A ROW OF OUR OWN.  SPEC.md FW-34 states the chain as
 * `mtd_read -> part_read -> rtl819x_flash` and spends its whole exclusion
 * argument on rtl8196_map_copy_from's 1024-byte short read.  The conclusion
 * (a truncated read is excluded) survives and gets STRONGER; the mechanism
 * named is wrong.  The map's copy_from is not merely bypassed by a macro --
 * it is never installed and never called.  量, one scan of the r54 vmlinux
 * with the counters printed side by side:
 *
 *     jal -> rtl8196_map_copy_from   0        <- the claim
 *     jal -> ComSrlCmd_ComRead       1        <- the control
 *     jal -> SFCSR_CS_L             17        <- the control
 *     .data words == 801a482c        0        (its address is never stored)
 *     .data words == bd000000        2        (so the scan CAN see .data)
 *
 * ⚠️ AND A TRAP THAT SCAN WALKED INTO, kept because the next census will
 * meet it too: `jal -> mtd_spi_read` and `jal -> SpiRead_11110B` are BOTH 0,
 * and both functions are live.  They are reached through function pointers
 * (`jalr v0` on chip_info->read; `jalr v1` on +0x3C of spi_flash_info +
 * chip*72).  A `jal` census cannot see an indirect call, so a 0 from one is
 * not "dead code".  FW-39's technique is unaffected -- it counts `sw` to an
 * ADDRESS, which is a different question.
 *
 * ------------------------------------------------------------------------
 * SO THE COEXISTENCE RULE IS A MEASUREMENT, NOT AN ASSUMPTION
 * ------------------------------------------------------------------------
 *
 * Three things make sharing the controller survivable, and the fourth is
 * what this driver adds:
 *
 *  1. Nothing here happens on its own.  Registration reads three registers
 *     and stops.  Every transaction is the direct consequence of a write to
 *     /proc, the same shape rtl819x-timer and rtl819x-gpio use.
 *  2. The vendor's own entry points re-establish the controller on every
 *     call -- SFCSR_CS_L spins for RDY and then writes SFCSR whole, and
 *     ComSrlCmd_RDID rewrites SFCR.  讀, from its disassembly.  So a vendor
 *     transaction after one of mine does not inherit my state.
 *  3. Mine restores what it found: SFCR, SFCR2, SFCSR, then reads them back.
 *  4. 🔴 AND THE READ-BACK IS THE POINT.  "Nothing else touched the
 *     controller" is otherwise an assumption, and this project does not
 *     accept those.  n_state_foreign counts transactions that BEGAN with
 *     SFCR/SFCR2 different from the values latched at registration;
 *     n_state_bad counts restores that did not take.  A zero in either is a
 *     reading, because the `wedge` verb is the positive control that makes
 *     them able to move.
 *
 * 🔴 SFDR IS NEVER RESTORED, AND THAT IS THE SUBTLE ONE.  It is the command
 * port: writing it ISSUES an SPI command.  A generic "save and restore all
 * four registers" loop -- which is what one writes without thinking -- would
 * end every transaction by clocking whatever byte happened to be in the save
 * slot out to the flash chip.  Three registers are saved.  Four would be a
 * bug that looks like tidiness.
 *
 * ------------------------------------------------------------------------
 * THE REGISTERS, AND WHERE EACH NUMBER CAME FROM
 * ------------------------------------------------------------------------
 *
 *   SPEC.md REG-13   SFCR 0xB8001200, SFCR2 ...04, SFCSR ...08, SFDR ...0C,
 *                    SFDR2 ...10.  量 on this board 2026-08-25b, and three
 *                    independent sources agree on the map: this unit's own
 *                    loader (A), the vendor bootcode header (B), and the
 *                    RTL8196E datasheet (D).
 *   SPEC.md REG-14   SFCSR bit 27 is SPI_RDY, 0 busy and 1 ready.  讀+, and
 *                    the strongest form of it: this unit's own
 *                    ComSrlCmd_RDID at 0x804058BC spins on exactly that bit
 *                    before touching SFDR.  Code that has booted this board
 *                    since 2018 depends on the semantics.
 *   SPEC.md LDR-42   The loader's FLR reads flash through SFDR programmed
 *                    I/O and NOT through the window; it supplies Fast Read
 *                    0x0B, and its data loop does not touch SFCSR between
 *                    words, so the pacing is the controller's.
 *   SPEC.md FLS-11   The memory-mapped window is 0xBD000000, KSEG1,
 *   SPEC.md MAP-12   uncached.
 *   SPEC.md FLS-14   The flash is 4,194,304 bytes and two committed copies
 *                    of a dump of it are byte-identical over all of it.
 *
 * SFCSR's fields, from D table 10, every one matching B's shift macros:
 *
 *   31 SPI_CSB0   chip select 0.  0 ACTIVE, 1 not active.  Reset 1.
 *   30 SPI_CSB1   chip select 1, same encoding.  Reset 1.
 *   29:28 LEN     bytes in this phase minus one: 00=1 .. 11=4.  Reset 11.
 *   27 SPI_RDY    read-only.  0 busy, 1 ready.
 *   26:25 IO_WIDTH  00 serial, 01 dual.
 *   24 CHIP_SEL   0 = CS0#.
 *   23:16 CMD_BYTE  D marks this "Only Used in MMIO Mode", and the serial
 *                   path puts the command in SFDR instead -- which is what
 *                   the loader's RDID does.  This driver never writes it.
 *
 * ------------------------------------------------------------------------
 * WHAT WAS READ TO WRITE THIS, AND THE HONEST VERDICT ON IT
 * ------------------------------------------------------------------------
 *
 * docs/blind-write-ledger.md 4.5 already says it, before this file existed:
 * 🔴 **R5-5 cannot be claimed as blind against the vendor.**  Eleven paths,
 * three of them decision-layer.  This segment added more -- spi_flash.c,
 * spi_probe.c's mtd_info, ComSrlCmd_ComRead, ComSrlCmd_InputCommand,
 * SFCSR_CS_L, spi_regist, setFSCR -- and they are in the ledger with their
 * depth.  The transaction ORDER below is the vendor's, because it is the
 * order that is known to work on this die, and pretending otherwise would be
 * a worse driver told as a better story.
 *
 * 🟢 What IS this file's own, and what docs/driver-diff.md will score:
 *
 *   - EVERY SPIN IS BOUNDED.  The vendor's SFCSR_CS_L, SFCSR_CS_H,
 *     spiFlashReady and ComSrlCmd_RDID all spin on a hardware bit with an
 *     unconditional back-branch and no counter (`j 801a29ac`, 讀 from the
 *     artefact).  量: this board arms a watchdog -- bsp_timer_init writes
 *     WDTCNR = 0x00600000 and rlx_timer_interrupt does WDTCNR |= 1<<23 on
 *     every TC0 interrupt -- and CLK-08 puts its window at roughly a second.
 *     So on the vendor's driver a controller that never raises RDY reboots
 *     the router.  Here it returns -ETIMEDOUT and counts.
 *   - The byte order is written out explicitly instead of memcpy'ing a u32,
 *     so the result does not depend on the host's endianness.  The vendor's
 *     `memcpy(puc, &ui, 4)` is correct only because this core is big-endian.
 *   - The save/restore/read-back guard above.
 *   - The three-layer write refusal below.
 *
 * ------------------------------------------------------------------------
 * THREE LAYERS REFUSE A WRITE -- AND THE FIRST DRAFT OF THIS PARAGRAPH WAS
 * WRONG ABOUT ONE OF THEM, WHICH IS WHY THE CODE BELOW LOOKS AS IT DOES
 * ------------------------------------------------------------------------
 *
 *  L1  The write path is a SEPARATE TRANSLATION UNIT that is not compiled.
 *      config/rlxfw-marks.tsv declares it as
 *      `obj-$(CONFIG_MTD_RTL819X_WRITE) += rtl819x-spi-write.o`, and that
 *      CONFIG_ is not declared to kconfig at all -- an undeclared CONFIG_
 *      expands to empty in GNU Make, so no menu, no defconfig and no
 *      `oldconfig` can turn it on.  Proved by symbol absence in System.map
 *      and `nm vmlinux`, and rlxfw-marks.py's `absent:` witness is what
 *      checks it.  Positive control: `make CONFIG_MTD_RTL819X_WRITE=y` in a
 *      DISCARDED tree makes the symbols appear and makes that row go red.
 *  L2  mtd->write and mtd->erase are STUBS THAT REFUSE with -EOPNOTSUPP and
 *      count the attempt.
 *  L3  mtd->flags is MTD_CAP_ROM, which is 0 -- MTD_WRITEABLE is not set --
 *      so mtdchar's mtd_open refuses an open for writing with -EACCES
 *      before L2 is ever consulted.
 *
 * 🔴 L2 WAS ORIGINALLY "leave the pointers NULL, the core returns
 * -EOPNOTSUPP".  That is FALSE on this kernel, and checking it rather than
 * asserting it is the only reason this file does not ship a latent oops.
 * 讀 drivers/mtd/mtdchar.c in this drop:
 *
 *      case MEMERASE:                                         :419
 *          if (!(file->f_mode & FMODE_WRITE)) return -EPERM;   :423
 *          ...
 *          ret = mtd->erase(mtd, erase);                       :457
 *
 * There is no NULL check.  A NULL .erase is a null-pointer call, not a
 * refusal.  So the three layers were NOT independent: L3 was the only thing
 * standing between a NULL pointer and a dereference, and "defence in depth"
 * would have described a single point of failure.
 *
 * 🟢 With stubs they ARE independent, and each fails differently: L1 is a
 * link-time absence, L2 an errno from this file, L3 an errno from the MTD
 * core at open().  L3's own basis is measured too -- mtd_open at :94,
 * `if ((file->f_mode & FMODE_WRITE) && !(mtd->flags & MTD_WRITEABLE))
 * return -EACCES`, which is SEPARATE from the odd-minor rule at :73.  That
 * matters: the vendor's /dev/mtd0 is an even minor and CAN be opened for
 * writing; this device cannot be, on either minor.  mtdblock.c:421 reads the
 * same flag and marks /dev/mtdblockN read-only.
 *
 * ⚠️ AND L3 HAS NEVER BEEN OBSERVED FIRING, HERE OR ANYWHERE IN THIS PROJECT.
 * :94 is skipped on every vendor partition, because the vendor's map sets
 * MTD_CAP_NORFLASH and MTD_WRITEABLE with it.  Observing it needs an EVEN char
 * minor over THIS device, and tools/mkinitramfs.py refuses to declare one --
 * correctly, since it can check the odd-minor rule from a declaration and
 * cannot check mtd->flags.  So L3 is 讀 and stays 讀; the `trywrite` verb
 * observes L2, the layer behind it, on the die.
 *
 *  and a counter, n_writes, which counts writes to the FLASH CHIP and is 0.
 *  It is not a fourth layer; it is the instrument that says the other three
 *  held.  Register writes to the controller are counted separately in
 *  n_reg_writes, which is NOT zero and must not be confused with it: this
 *  driver writes SFCSR and SFDR on every read, because that is what issuing
 *  a read command IS on this controller.
 *
 * ------------------------------------------------------------------------
 * THE EXPERIMENT: D1 AND D3 IN ONE TRAVERSAL
 * ------------------------------------------------------------------------
 *
 * PROGRESS.md's R5-5 row freezes four rows.  D1 and D3 are both done by
 * rtl819x_spi_verify(), one pass, two 4 KiB buffers:
 *
 *   D1  sha256 over H601's COMPLEMENT -- [0x000000,0x006000) united with
 *       [0x008000,0x400000), 4,186,112 bytes = 99.8047 % -- computed in this
 *       kernel by crypto/sha256_generic.c, and compared against a constant
 *       re-derived from FLS-14's dump.  The rootfs is not touched and the
 *       name `mtd_debug` does not appear, which is what the rewritten DoD
 *       was for.
 *   D2  The 8,192 bytes left out are a RULE, not a failure.  flashwin
 *       refuses to print a digest of any window overlapping H601 (量,
 *       FLS-24), and that refusal was not overturned.  Their verification
 *       stays in the FLR bracket, which compares without printing.
 *   D3  The SAME bytes read again through 0xBD000000 and compared IN THE
 *       KERNEL, printing only `equal` or the first differing offset.  A
 *       verdict is not a digest, so D3 spans the FULL 4,194,304 bytes --
 *       H601 included -- because an offset reveals no content.  The digest
 *       does not, because a digest would.
 *
 * 🔴 THE CITATION IN THE FROZEN DoD WAS THE WRONG HALF OF THE RIGHT ROW, and
 * this is the finding that most changes what D3 means.  D3 cited FW-34 as
 * having measured the 0xBD000000 path over all 4,194,304 bytes.  It did not:
 * that reading is `busybox wc -lc < /dev/mtd0ro`, which goes through
 * mtd_spi_read -- the PIO path -- as the census above shows.  Nothing in
 * this project has ever read the window past probe3's 1,024 words.
 *
 * 🟢 The right half of the same row is FW-34's Group F: 1,024 uncached loads
 * through 0xBD000000 at stride 4 and at stride 1,024 took the SAME 30,354
 * ticks, R = 1.0000, so the window serves a single-word read as its own
 * transaction and does NOT buffer.  That is what makes D3 two paths rather
 * than one path read twice -- an independence at the CONTROLLER, not merely
 * in the source.  Without it, `equal` would be compatible with a controller
 * returning the same buffered data twice.
 *
 * 🟢 AND D3 IS ALSO THE CONTROL ON D1's OWN PATH.  The MMIO read of a chunk
 * happens after the PIO read of the same chunk.  If a transaction of mine
 * left the controller unusable, the window read that follows would differ.
 *
 * 🟢 THE NEGATIVE CONTROL IS ONE VERB AND IT MOVES BOTH HALVES.  `corrupt
 * <off>` flips a byte in the PIO buffer AFTER the read and BEFORE the hash.
 * D1 must then give a different digest and D3 must report exactly that
 * offset.  Without it, `equal` and `match` are what a tool that cannot fail
 * also prints.
 *
 * ------------------------------------------------------------------------
 * THE H601 GUARD IS A PROPERTY OF THE COMPUTED VALUE
 * ------------------------------------------------------------------------
 *
 * The traversal counts h601_hashed: bytes inside [0x006000,0x008000) that
 * reached either digest.  /proc prints the digests ONLY when that count is
 * 0.  So the digest is printable because the arithmetic came out H601-free,
 * not because the author believed the skip was right.  H601 = exactly two
 * 4 KiB chunks, aligned, so the skip needs no partial-chunk arithmetic --
 * chunk 6 and chunk 7 and nothing else.
 *
 * ⚠️ H601's bytes DO enter DRAM: D3 compares them.  That is the same thing
 * the FLR bracket does and it is not a capture.  What keeps it safe is that
 * this driver has NO verb and NO /proc field that emits a flash byte -- not
 * a hexdump, not a sample, not a first-differing-VALUE.  Only digests over
 * the complement, an offset, counters and controller registers.  Adding a
 * hexdump verb here would defeat every paragraph above.
 *
 * ------------------------------------------------------------------------
 * WHAT THIS FILE DOES NOT ESTABLISH
 * ------------------------------------------------------------------------
 *
 *  1. THAT THE FLASH CONTENT MATCHES THE DUMP.  D1 says the complement
 *     hashes to what the 2026-08-16 dump hashes to.  It says nothing about
 *     H601, by construction, and the 0.0244 % flash bracket does not move.
 *  2. ANY WRITE OR ERASE BEHAVIOUR.  L1 means that code is not here.  The
 *     write TU compiles in the control build and has never run anywhere.
 *  3. THAT MY TRANSACTION IS OPTIMAL.  It is the vendor's order at the
 *     vendor's Fast Read with one dummy byte.  Faster shapes exist in
 *     spi_common.c (dual IO, 0x3B/0xBB) and none of them has been measured
 *     on this die, so none is used.
 *  4. THE SPI CLOCK.  量 from the r54 artefact, ComSrlCmd_RDID writes
 *     SFCR = 0xFFC00000, SPI_CLK_DIV = 7 -> divisor 16, and spi_regist
 *     calls it twice at device_initcall -- where REG-13 read 0x3FC00000,
 *     divisor 4, at the LOADER prompt.  That is 讀, from code; S1 below is
 *     the reading that would make it 量.  This driver does not set the
 *     divider and does not depend on its value.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/mutex.h>
#include <linux/sched.h>
#include <linux/proc_fs.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/err.h>
#include <linux/mtd/mtd.h>
#include <crypto/hash.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

#define RTL819X_SPI_VERSION	"rtl819x-spi 1.0"

/* CKSEG1ADDR of these gives 0xB80012xx and 0xBD000000.  __raw_readl and not
 * readl: an on-chip register on this big-endian part is already in CPU
 * order.  Same reasoning as rtl819x-timer.c and rtl819x-gpio.c. */
#define RTL819X_SPI_PHYS	0x18001200	/* REG-13 */
#define RTL819X_SPI_WIN_PHYS	0x1D000000	/* FLS-11, MAP-12 */

#define RTL819X_SFCR		0x00
#define RTL819X_SFCR2		0x04
#define RTL819X_SFCSR		0x08
#define RTL819X_SFDR		0x0C
/* SFDR2 at +0x10 is present on this part per D and referenced ZERO times by
 * this unit's loader (REG-13).  It is not read here: LDR-07 has never let
 * anything read it, so this driver would be its first reader and a first
 * reader of an unknown register belongs in a typed act, not in a probe. */

#define SFCSR_CSB0		0x80000000u
#define SFCSR_CSB1		0x40000000u
#define SFCSR_CSB_MASK		(SFCSR_CSB0 | SFCSR_CSB1)
#define SFCSR_LEN_SHIFT		28
#define SFCSR_RDY		0x08000000u	/* REG-14 */
#define SFCSR_IOW_SHIFT		25
#define SFCSR_IOW_SINGLE	0u

#define RTL819X_SPI_CMD_FASTREAD 0x0Bu		/* LDR-42, and SFCR2's top
						 * byte read as 0x0B on this
						 * board -- REG-13 */
#define RTL819X_SPI_FASTREAD_DUMMY 1		/* DUMMYCOUNT_1 */

#define RTL819X_SPI_SIZE	0x00400000u	/* FLS-14 */
#define RTL819X_SPI_ERASESIZE	0x00001000u	/* sector, from the loader's
						 * fallback descriptor */

/* H601 -- this unit's MAC and radio calibration.  CLAUDE.md's second Never
 * row.  Exactly two 4 KiB chunks, which is why the skip below has no
 * partial-chunk arithmetic. */
#define RTL819X_SPI_H601_LO	0x00006000u
#define RTL819X_SPI_H601_HI	0x00008000u

#define RTL819X_SPI_CHUNK	4096u
#define RTL819X_SPI_COMPLEMENT	4186112u	/* FLS-24 */

/* 🔴 The bound the vendor's driver does not have.  A read of SFCSR is an
 * uncached KSEG1 load; FW-34 Group F measured an uncached word through the
 * flash window at 2.075 us, which is the slowest access on this bus, so
 * 200,000 spins is under 0.42 s even at that rate -- inside the watchdog
 * window CLK-08 bounds at 557 ms for the shorter of its two settings.  A
 * real phase completes in under a microsecond at any divider, so this is a
 * ceiling and not a delay. */
#define RTL819X_SPI_RDY_SPINS	200000u

#define RTL819X_SPI_PROC_NAME	"rtl819x-spi"
#define RTL819X_SPI_MTD_NAME	"rtl819x-spi-pio"

/* FLS-24, re-derived 2026-09-07 from flash-n150rt-console-2.bin by two
 * independent routes (dd+sha256sum, and python byte slices) which agreed
 * digit for digit, with two negative controls: the whole-file digest differs,
 * and flipping one byte moves it.  Elided form a9916fd8...4ce3cba, which is
 * what SPEC.md prints.  Typed by nobody -- emitted as this initialiser by the
 * derivation script and pasted whole. */
static const u8 rtl819x_spi_expect_d1[32] = {
	0xA9, 0x91, 0x6F, 0xD8, 0x6A, 0xDB, 0x49, 0xFF,
	0x0A, 0x4F, 0x53, 0xD4, 0x9B, 0xC3, 0x77, 0xCA,
	0x5C, 0x54, 0x32, 0x1D, 0xCF, 0xF0, 0x2B, 0xDB,
	0x55, 0xE7, 0xB4, 0xAB, 0x64, 0xCE, 0x3C, 0xBA,
};

/* ------------------------------------------------------------------------
 * Register access.
 * ------------------------------------------------------------------------ */

static inline void __iomem *rtl819x_spi_reg(unsigned int off)
{
	return (void __iomem *)(CKSEG1ADDR(RTL819X_SPI_PHYS) + off);
}

static inline u32 rtl819x_spi_rd(unsigned int off)
{
	return __raw_readl(rtl819x_spi_reg(off));
}

static unsigned long rtl819x_spi_n_reg_writes;

/* The ONLY write helper, so `git grep rtl819x_spi_wr` is an auditable list.
 * Unlike rtl819x-gpio's, this one is REACHED: issuing a read on this
 * controller is a sequence of register writes.  n_reg_writes is therefore
 * not the number this driver keeps at zero -- n_writes is. */
static inline void rtl819x_spi_wr(unsigned int off, u32 v)
{
	rtl819x_spi_n_reg_writes++;
	__raw_writel(v, rtl819x_spi_reg(off));
}

/* ------------------------------------------------------------------------
 * State.
 * ------------------------------------------------------------------------ */

static DEFINE_MUTEX(rtl819x_spi_lock);	/* a mutex and NOT a spinlock: a full
					 * traversal is seconds of work and it
					 * must be preemptible, or the TC0
					 * interrupt that pets the watchdog
					 * cannot run */

static u32 rtl819x_spi_boot_sfcr;	/* latched at late_initcall */
static u32 rtl819x_spi_boot_sfcr2;
static u32 rtl819x_spi_boot_sfcsr;

static int rtl819x_spi_kat_rc = -EAGAIN;	/* FIPS 180-2 known answers */
static int rtl819x_spi_add_rc = -EAGAIN;
static int rtl819x_spi_added;
static int rtl819x_spi_wedged;		/* a restore did not take; refuse */

static unsigned long rtl819x_spi_n_xfer;	/* PIO transactions issued */
static unsigned long rtl819x_spi_n_pio_bytes;
static unsigned long rtl819x_spi_n_mmio_bytes;
static unsigned long rtl819x_spi_n_rdy_timeout;
static unsigned long rtl819x_spi_n_state_foreign;
static unsigned long rtl819x_spi_n_state_bad;
static unsigned long rtl819x_spi_n_mtd_read;

/* THE NUMBER THIS DRIVER EXISTS TO KEEP AT ZERO: writes to the FLASH CHIP.
 * Not register writes -- see n_reg_writes. */
static unsigned long rtl819x_spi_n_writes;

/* L2 firing.  Separate from n_writes because a REFUSED write is evidence the
 * layer works, and a write is evidence it did not. */
static unsigned long rtl819x_spi_n_write_refused;

/* verify() results, all -1 / 0 until it has run once */
static int  rtl819x_spi_v_ran;
static int  rtl819x_spi_v_rc;
static u32  rtl819x_spi_v_cmp_bytes;
static long rtl819x_spi_v_first_diff = -1;
static u32  rtl819x_spi_v_diff_bytes;
static u32  rtl819x_spi_v_digest_bytes;
static u32  rtl819x_spi_v_h601_skipped;
static u32  rtl819x_spi_v_h601_hashed;	/* MUST be 0 for a digest to print */
static u8   rtl819x_spi_v_d1[32];
static u8   rtl819x_spi_v_dmmio[32];
static int  rtl819x_spi_v_d1_match;
static long rtl819x_spi_corrupt_at = -1;	/* negative control */

/* ------------------------------------------------------------------------
 * The transaction.
 * ------------------------------------------------------------------------ */

struct rtl819x_spi_state {
	u32 sfcr, sfcr2, sfcsr;
};

static int rtl819x_spi_wait_ready(void)
{
	unsigned int i;

	for (i = 0; i < RTL819X_SPI_RDY_SPINS; i++) {
		if (rtl819x_spi_rd(RTL819X_SFCSR) & SFCSR_RDY)
			return 0;
		cpu_relax();
	}
	rtl819x_spi_n_rdy_timeout++;
	return -ETIMEDOUT;
}

/* CS low with a phase length.  `len` is bytes-1 in the LEN field, matching
 * the vendor's SFCSR_CS_L(chip, len, iowidth): chip 0 gives CSB = 1, i.e.
 * CSB1 set and CSB0 clear, and CSB0 clear is CS0 ASSERTED. */
static int rtl819x_spi_cs_low(unsigned int len)
{
	int rc = rtl819x_spi_wait_ready();

	if (rc)
		return rc;
	rtl819x_spi_wr(RTL819X_SFCSR,
		       SFCSR_CSB1 |
		       ((u32)len << SFCSR_LEN_SHIFT) |
		       (SFCSR_IOW_SINGLE << SFCSR_IOW_SHIFT) |
		       SFCSR_RDY);
	return 0;
}

/* CS high.  Called on EVERY exit path including the error ones, because a
 * transaction abandoned with CS asserted leaves the flash chip mid-command
 * and the memory-mapped window unusable. */
static void rtl819x_spi_cs_high(void)
{
	/* Deliberately NOT bounded by a return: if RDY never comes we still
	 * have to raise CS, and the spin is already bounded. */
	(void)rtl819x_spi_wait_ready();
	rtl819x_spi_wr(RTL819X_SFCSR,
		       SFCSR_CSB0 | SFCSR_CSB1 |
		       (SFCSR_IOW_SINGLE << SFCSR_IOW_SHIFT) |
		       SFCSR_RDY);
}

static int rtl819x_spi_claim(struct rtl819x_spi_state *s)
{
	if (rtl819x_spi_wedged)
		return -EIO;
	s->sfcr  = rtl819x_spi_rd(RTL819X_SFCR);
	s->sfcr2 = rtl819x_spi_rd(RTL819X_SFCR2);
	s->sfcsr = rtl819x_spi_rd(RTL819X_SFCSR);

	/* The collision detector.  Not a failure: another owner changing the
	 * divider does not make my read wrong, it makes it slower or faster.
	 * It is recorded because "nothing else touched the controller" is
	 * otherwise an assumption. */
	if (s->sfcr != rtl819x_spi_boot_sfcr ||
	    s->sfcr2 != rtl819x_spi_boot_sfcr2)
		rtl819x_spi_n_state_foreign++;
	return 0;
}

/*
 * 🔴 THE POSITIVE CONTROL FOR THE GUARD BELOW, AND WHERE IT HAD TO GO.
 *
 * The first version of `wedge` corrupted the SAVED value and let release()
 * write it: `s.sfcr = ~real`.  That does not test anything -- release()
 * writes X and then compares the read-back against the SAME X, so it would
 * have agreed -- and it would have put 0xC03FFFFF into the live SFCR, moving
 * this board's SPI clock divider and TCS to values nothing has measured.  A
 * control that writes an unmeasured value to a live flash controller on a
 * one-device project is worse than no control.
 *
 * So the flag corrupts the READ-BACK used in the comparison and nothing
 * else.  No wrong value ever reaches the silicon; what is falsified is the
 * check, which is the only thing a control should falsify.
 */
static int rtl819x_spi_force_mismatch;

static int rtl819x_spi_release(const struct rtl819x_spi_state *s)
{
	u32 a, b, c;

	rtl819x_spi_cs_high();
	rtl819x_spi_wr(RTL819X_SFCR,  s->sfcr);
	rtl819x_spi_wr(RTL819X_SFCR2, s->sfcr2);
	rtl819x_spi_wr(RTL819X_SFCSR, s->sfcsr);
	/* SFDR is not restored.  See the header: it is the command port. */

	a = rtl819x_spi_rd(RTL819X_SFCR);
	b = rtl819x_spi_rd(RTL819X_SFCR2);
	c = rtl819x_spi_rd(RTL819X_SFCSR);

	if (rtl819x_spi_force_mismatch)
		a = ~a;			/* comparison only; see above */

	/* SFCSR is compared with RDY masked out, because RDY is read-only and
	 * may legitimately differ from what was written back.  What must hold
	 * is that BOTH chip selects are inactive. */
	if (a != s->sfcr || b != s->sfcr2 ||
	    (c & SFCSR_CSB_MASK) != SFCSR_CSB_MASK) {
		rtl819x_spi_n_state_bad++;
		rtl819x_spi_wedged = 1;
		return -EIO;
	}
	return 0;
}

/*
 * One Fast Read.  `addr` and `len` are 4-aligned; the caller guarantees it.
 *
 * The order is the vendor's ComSrlCmd_InputCommand with ISFAST_NO,
 * IOWIDTH_SINGLE, DUMMYCOUNT_1 -- command byte, three address bytes, one
 * dummy byte, then a 4-byte phase and the data.  Each SFDR write is taken
 * from the TOP byte of the word when LEN selects one byte, which is why the
 * address is shifted left rather than masked.
 */
static int rtl819x_spi_read_pio(u32 addr, u32 len, u8 *buf)
{
	struct rtl819x_spi_state s;
	int rc, rc2;
	u32 i;

	if (addr > RTL819X_SPI_SIZE || len > RTL819X_SPI_SIZE - addr)
		return -EINVAL;
	if ((addr | len) & 3u)
		return -EINVAL;

	rc = rtl819x_spi_claim(&s);
	if (rc)
		return rc;
	rtl819x_spi_n_xfer++;

	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, (u32)RTL819X_SPI_CMD_FASTREAD << 24);

	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, addr << 8);
	rtl819x_spi_wr(RTL819X_SFDR, addr << 16);
	rtl819x_spi_wr(RTL819X_SFDR, addr << 24);
	for (i = 0; i < RTL819X_SPI_FASTREAD_DUMMY; i++)
		rtl819x_spi_wr(RTL819X_SFDR, 0);

	rc = rtl819x_spi_cs_low(3);
	if (rc)
		goto out;

	/* The data loop does not touch SFCSR -- LDR-42 read exactly that in
	 * the loader's own engine, and the vendor's Linux loop is the same
	 * shape.  The pacing is on the controller's side. */
	for (i = 0; i < len; i += 4) {
		u32 v = rtl819x_spi_rd(RTL819X_SFDR);

		buf[i + 0] = (u8)(v >> 24);
		buf[i + 1] = (u8)(v >> 16);
		buf[i + 2] = (u8)(v >> 8);
		buf[i + 3] = (u8)v;
	}
	rtl819x_spi_n_pio_bytes += len;
out:
	rc2 = rtl819x_spi_release(&s);
	return rc ? rc : rc2;
}

/*
 * The same bytes through the memory-mapped window.  Word loads, not memcpy:
 * FW-34's Group F measured the window with 32-bit loads, and memcpy's access
 * sizes are unspecified -- using a size nothing has measured would put an
 * untested variable inside the control.
 */
static void rtl819x_spi_read_mmio(u32 addr, u32 len, u8 *buf)
{
	const volatile u32 __iomem *p =
		(const volatile u32 __iomem *)(CKSEG1ADDR(RTL819X_SPI_WIN_PHYS)
					       + addr);
	u32 i;

	for (i = 0; i < len; i += 4) {
		u32 v = __raw_readl((void __iomem *)(p + (i >> 2)));

		buf[i + 0] = (u8)(v >> 24);
		buf[i + 1] = (u8)(v >> 16);
		buf[i + 2] = (u8)(v >> 8);
		buf[i + 3] = (u8)v;
	}
	rtl819x_spi_n_mmio_bytes += len;
}

/* ------------------------------------------------------------------------
 * sha256, and the known-answer test that makes it an instrument.
 *
 * CONFIG_CRYPTO_MANAGER is not set on this board, so the crypto core runs NO
 * self-test on registration -- 讀 crypto/algapi.c crypto_wait_for_test(): with
 * no notifier to consume it, crypto_probing_notify returns NOTIFY_DONE and
 * crypto_alg_tested() is called directly, which completes the larval WITHOUT
 * testing anything.  That is also why crypto_alloc_shash works here at all,
 * and the refutation condition is written down: if it returns an error, or if
 * boot stalls in crypto_wait_for_test, the reading is wrong.
 *
 * So the KAT is not belt and braces.  It is the only thing standing between
 * a digest and a number nobody checked.  Three vectors: the empty string, the
 * FIPS 180-2 one-block vector, and its 56-byte multi-block vector -- 56
 * crosses the 55-byte padding boundary, which is where a hand-written or
 * miscompiled implementation fails while passing the other two.
 * ------------------------------------------------------------------------ */

static const char rtl819x_spi_kat1[] = "abc";
static const char rtl819x_spi_kat2[] =
	"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";

static const u8 rtl819x_spi_kat0_want[32] = {	/* "" */
	0xE3, 0xB0, 0xC4, 0x42, 0x98, 0xFC, 0x1C, 0x14,
	0x9A, 0xFB, 0xF4, 0xC8, 0x99, 0x6F, 0xB9, 0x24,
	0x27, 0xAE, 0x41, 0xE4, 0x64, 0x9B, 0x93, 0x4C,
	0xA4, 0x95, 0x99, 0x1B, 0x78, 0x52, 0xB8, 0x55,
};
static const u8 rtl819x_spi_kat1_want[32] = {	/* "abc" */
	0xBA, 0x78, 0x16, 0xBF, 0x8F, 0x01, 0xCF, 0xEA,
	0x41, 0x41, 0x40, 0xDE, 0x5D, 0xAE, 0x22, 0x23,
	0xB0, 0x03, 0x61, 0xA3, 0x96, 0x17, 0x7A, 0x9C,
	0xB4, 0x10, 0xFF, 0x61, 0xF2, 0x00, 0x15, 0xAD,
};
static const u8 rtl819x_spi_kat2_want[32] = {	/* the 56-byte vector */
	0x24, 0x8D, 0x6A, 0x61, 0xD2, 0x06, 0x38, 0xB8,
	0xE5, 0xC0, 0x26, 0x93, 0x0C, 0x3E, 0x60, 0x39,
	0xA3, 0x3C, 0xE4, 0x59, 0x64, 0xFF, 0x21, 0x67,
	0xF6, 0xEC, 0xED, 0xD4, 0x19, 0xDB, 0x06, 0xC1,
};

struct rtl819x_spi_hash {
	struct crypto_shash *tfm;
	struct shash_desc *d1;		/* the complement */
	struct shash_desc *d2;		/* the same bytes via the window */
};

static struct shash_desc *rtl819x_spi_desc(struct crypto_shash *tfm)
{
	struct shash_desc *d = kmalloc(sizeof(*d) + crypto_shash_descsize(tfm),
				       GFP_KERNEL);

	if (!d)
		return NULL;
	d->tfm = tfm;
	d->flags = 0;
	if (crypto_shash_init(d)) {
		kfree(d);
		return NULL;
	}
	return d;
}

static int rtl819x_spi_kat_one(struct crypto_shash *tfm, const void *msg,
			       unsigned int len, const u8 *want)
{
	struct shash_desc *d = rtl819x_spi_desc(tfm);
	u8 got[32];
	int rc;

	if (!d)
		return -ENOMEM;
	rc = crypto_shash_update(d, msg, len);
	if (!rc)
		rc = crypto_shash_final(d, got);
	kfree(d);
	if (rc)
		return rc;
	return memcmp(got, want, 32) ? -EILSEQ : 0;
}

static int rtl819x_spi_kat(void)
{
	struct crypto_shash *tfm = crypto_alloc_shash("sha256", 0, 0);
	int rc;

	if (IS_ERR(tfm))
		return PTR_ERR(tfm);
	rc = rtl819x_spi_kat_one(tfm, "", 0, rtl819x_spi_kat0_want);
	if (!rc)
		rc = rtl819x_spi_kat_one(tfm, rtl819x_spi_kat1,
					 sizeof(rtl819x_spi_kat1) - 1,
					 rtl819x_spi_kat1_want);
	if (!rc)
		rc = rtl819x_spi_kat_one(tfm, rtl819x_spi_kat2,
					 sizeof(rtl819x_spi_kat2) - 1,
					 rtl819x_spi_kat2_want);
	crypto_free_shash(tfm);
	return rc;
}

/* ------------------------------------------------------------------------
 * D1 and D3, one traversal.
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_verify(u32 limit)
{
	struct rtl819x_spi_hash h;
	u8 *a = NULL, *b = NULL;
	u32 off, i;
	int rc = 0;

	if (rtl819x_spi_kat_rc)
		return -EPERM;		/* a digest engine that has not passed
					 * its own vectors does not get used */
	if (!limit || limit > RTL819X_SPI_SIZE)
		limit = RTL819X_SPI_SIZE;
	limit &= ~(RTL819X_SPI_CHUNK - 1u);
	if (!limit)
		return -EINVAL;

	memset(&h, 0, sizeof(h));
	h.tfm = crypto_alloc_shash("sha256", 0, 0);
	if (IS_ERR(h.tfm)) {
		rc = PTR_ERR(h.tfm);
		h.tfm = NULL;
		goto out;
	}
	h.d1 = rtl819x_spi_desc(h.tfm);
	h.d2 = rtl819x_spi_desc(h.tfm);
	a = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	b = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	if (!h.d1 || !h.d2 || !a || !b) {
		rc = -ENOMEM;
		goto out;
	}

	rtl819x_spi_v_cmp_bytes = 0;
	rtl819x_spi_v_first_diff = -1;
	rtl819x_spi_v_diff_bytes = 0;
	rtl819x_spi_v_digest_bytes = 0;
	rtl819x_spi_v_h601_skipped = 0;
	rtl819x_spi_v_h601_hashed = 0;
	rtl819x_spi_v_d1_match = 0;

	for (off = 0; off < limit; off += RTL819X_SPI_CHUNK) {
		int in_h601 = (off >= RTL819X_SPI_H601_LO &&
			       off < RTL819X_SPI_H601_HI);

		rc = rtl819x_spi_read_pio(off, RTL819X_SPI_CHUNK, a);
		if (rc)
			goto out;
		rtl819x_spi_read_mmio(off, RTL819X_SPI_CHUNK, b);

		/* The negative control, applied AFTER the read and BEFORE
		 * both the comparison and the hash, so one verb moves D1 and
		 * D3 together. */
		if (rtl819x_spi_corrupt_at >= (long)off &&
		    rtl819x_spi_corrupt_at < (long)(off + RTL819X_SPI_CHUNK))
			a[rtl819x_spi_corrupt_at - off] ^= 0xFFu;

		/* D3: a verdict over every byte, H601 included.  Only the
		 * offset is ever printed. */
		for (i = 0; i < RTL819X_SPI_CHUNK; i++) {
			if (a[i] != b[i]) {
				rtl819x_spi_v_diff_bytes++;
				if (rtl819x_spi_v_first_diff < 0)
					rtl819x_spi_v_first_diff =
						(long)(off + i);
			}
		}
		rtl819x_spi_v_cmp_bytes += RTL819X_SPI_CHUNK;

		/* D1/D2: the digest sees the complement and nothing else. */
		if (in_h601) {
			rtl819x_spi_v_h601_skipped += RTL819X_SPI_CHUNK;
		} else {
			rc = crypto_shash_update(h.d1, a, RTL819X_SPI_CHUNK);
			if (!rc)
				rc = crypto_shash_update(h.d2, b,
							 RTL819X_SPI_CHUNK);
			if (rc)
				goto out;
			rtl819x_spi_v_digest_bytes += RTL819X_SPI_CHUNK;
			if (off + RTL819X_SPI_CHUNK > RTL819X_SPI_H601_LO &&
			    off < RTL819X_SPI_H601_HI)
				rtl819x_spi_v_h601_hashed += RTL819X_SPI_CHUNK;
		}

		/* Seconds of work with the watchdog petted from the vendor's
		 * TC0 handler.  Without this the loop is the thing that stops
		 * it running. */
		cond_resched();
	}

	rc = crypto_shash_final(h.d1, rtl819x_spi_v_d1);
	if (!rc)
		rc = crypto_shash_final(h.d2, rtl819x_spi_v_dmmio);
	if (rc)
		goto out;
	/* NOTE: crypto_shash_final() finalises the digest; it does NOT free
	 * the desc.  An earlier draft set these to NULL here "because final()
	 * consumed them", which leaked both allocations on every verify.  The
	 * out: path below is the only owner. */

	rtl819x_spi_v_d1_match =
		(rtl819x_spi_v_digest_bytes == RTL819X_SPI_COMPLEMENT &&
		 rtl819x_spi_v_h601_hashed == 0 &&
		 !memcmp(rtl819x_spi_v_d1, rtl819x_spi_expect_d1, 32));
out:
	kfree(a);
	kfree(b);
	kfree(h.d1);
	kfree(h.d2);
	if (h.tfm && !IS_ERR(h.tfm))
		crypto_free_shash(h.tfm);
	rtl819x_spi_v_ran = 1;
	rtl819x_spi_v_rc = rc;
	return rc;
}

/* ------------------------------------------------------------------------
 * MTD.
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_mtd_read(struct mtd_info *mtd, loff_t from, size_t len,
				size_t *retlen, u_char *buf)
{
	u32 addr = (u32)from;
	u32 done = 0;
	int rc = 0;

	*retlen = 0;
	if (from < 0 || from >= (loff_t)RTL819X_SPI_SIZE)
		return -EINVAL;
	if (len > RTL819X_SPI_SIZE - addr)
		return -EINVAL;
	/* This driver's transaction is word-shaped and it does not pretend
	 * otherwise.  A short read that REPORTS the short length is honest;
	 * FW-34's whole exclusion argument exists because the vendor's map
	 * function returns void and cannot. */
	if ((addr | (u32)len) & 3u)
		return -EINVAL;

	mutex_lock(&rtl819x_spi_lock);
	while (done < len) {
		u32 n = len - done;

		if (n > RTL819X_SPI_CHUNK)
			n = RTL819X_SPI_CHUNK;
		rc = rtl819x_spi_read_pio(addr + done, n, buf + done);
		if (rc)
			break;
		done += n;
		cond_resched();
	}
	rtl819x_spi_n_mtd_read++;
	mutex_unlock(&rtl819x_spi_lock);
	*retlen = done;
	return rc;
}

/*
 * Layer L2.  These exist BECAUSE leaving the pointers NULL is not a refusal
 * on this kernel -- mtdchar.c:457 calls mtd->erase with no NULL check.  They
 * hold no write code and reference nothing in the write TU; they are the
 * errno that a NULL would have been if the MTD core had checked.
 */
static int rtl819x_spi_mtd_write(struct mtd_info *mtd, loff_t to, size_t len,
				 size_t *retlen, const u_char *buf)
{
	(void)mtd; (void)to; (void)buf;
	*retlen = 0;
	rtl819x_spi_n_write_refused++;
	return -EOPNOTSUPP;
}

static int rtl819x_spi_mtd_erase(struct mtd_info *mtd, struct erase_info *instr)
{
	(void)mtd;
	rtl819x_spi_n_write_refused++;
	/* No callback is invoked: mtdchar only waits on one when erase()
	 * returned 0, so refusing here does not leave a sleeper. */
	instr->state = MTD_ERASE_FAILED;
	return -EOPNOTSUPP;
}

static struct mtd_info rtl819x_spi_mtd = {
	.type		= MTD_NORFLASH,
	/* MTD_CAP_ROM is 0: MTD_WRITEABLE is NOT set, which is layer L3.
	 * mtdchar's mtd_open refuses an open for writing with -EACCES at :94,
	 * separately from the odd-minor rule at :73, and mtdblock.c:421 reads
	 * the same flag to mark the block device read-only. */
	.flags		= MTD_CAP_ROM,
	.size		= RTL819X_SPI_SIZE,
	.erasesize	= RTL819X_SPI_ERASESIZE,
	.writesize	= 1,
	.name		= RTL819X_SPI_MTD_NAME,
	.owner		= THIS_MODULE,
	.read		= rtl819x_spi_mtd_read,
	.write		= rtl819x_spi_mtd_write,	/* L2, refuses */
	.erase		= rtl819x_spi_mtd_erase,	/* L2, refuses */
};

/* ------------------------------------------------------------------------
 * /proc/rtl819x-spi
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_hex(char *p, const u8 *d)
{
	static const char x[] = "0123456789abcdef";
	int i;

	for (i = 0; i < 32; i++) {
		p[i * 2]     = x[d[i] >> 4];
		p[i * 2 + 1] = x[d[i] & 15];
	}
	p[64] = '\0';
	return 64;
}

static int rtl819x_spi_read_proc(char *page, char **start, off_t off,
				 int count, int *eof, void *data)
{
	u32 sfcr  = rtl819x_spi_rd(RTL819X_SFCR);
	u32 sfcr2 = rtl819x_spi_rd(RTL819X_SFCR2);
	u32 sfcsr = rtl819x_spi_rd(RTL819X_SFCSR);
	char hx[66];
	int len = 0;

	len += sprintf(page + len, "version %s\n", RTL819X_SPI_VERSION);
	len += sprintf(page + len, "added %d\n", rtl819x_spi_added);
	len += sprintf(page + len, "add_rc %d\n", rtl819x_spi_add_rc);
	len += sprintf(page + len, "mtd_index %d\n",
		       rtl819x_spi_added ? rtl819x_spi_mtd.index : -1);
	len += sprintf(page + len, "kat_rc %d\n", rtl819x_spi_kat_rc);
	len += sprintf(page + len, "wedged %d\n", rtl819x_spi_wedged);

	/* live */
	len += sprintf(page + len, "sfcr %08X\n", sfcr);
	len += sprintf(page + len, "sfcr2 %08X\n", sfcr2);
	len += sprintf(page + len, "sfcsr %08X\n", sfcsr);
	/* latched at late_initcall, before this driver issued anything */
	len += sprintf(page + len, "boot_sfcr %08X\n", rtl819x_spi_boot_sfcr);
	len += sprintf(page + len, "boot_sfcr2 %08X\n", rtl819x_spi_boot_sfcr2);
	len += sprintf(page + len, "boot_sfcsr %08X\n", rtl819x_spi_boot_sfcsr);

	/* The two competing readings of SFCR, as 1/0 rather than prose.
	 * REG-13 measured 3FC00000 at the LOADER prompt; the r54 artefact
	 * says ComSrlCmd_RDID writes FFC00000 at device_initcall.  Exactly
	 * one of these should be 1, and which one is the finding. */
	len += sprintf(page + len, "sfcr_as_loader %d\n", sfcr == 0x3FC00000u);
	len += sprintf(page + len, "sfcr_as_kernel %d\n", sfcr == 0xFFC00000u);
	len += sprintf(page + len, "cs_idle %d\n",
		       (sfcsr & SFCSR_CSB_MASK) == SFCSR_CSB_MASK);

	/* counters.  n_reg_writes is NOT n_writes; see the header. */
	len += sprintf(page + len, "n_xfer %lu\n", rtl819x_spi_n_xfer);
	len += sprintf(page + len, "n_reg_writes %lu\n",
		       rtl819x_spi_n_reg_writes);
	len += sprintf(page + len, "n_pio_bytes %lu\n",
		       rtl819x_spi_n_pio_bytes);
	len += sprintf(page + len, "n_mmio_bytes %lu\n",
		       rtl819x_spi_n_mmio_bytes);
	len += sprintf(page + len, "n_mtd_read %lu\n", rtl819x_spi_n_mtd_read);
	len += sprintf(page + len, "n_rdy_timeout %lu\n",
		       rtl819x_spi_n_rdy_timeout);
	len += sprintf(page + len, "n_state_foreign %lu\n",
		       rtl819x_spi_n_state_foreign);
	len += sprintf(page + len, "n_state_bad %lu\n",
		       rtl819x_spi_n_state_bad);

	/* THE NUMBER THIS DRIVER EXISTS TO KEEP AT ZERO. */
	len += sprintf(page + len, "n_writes %lu\n", rtl819x_spi_n_writes);
	/* L2 firing.  Non-zero is the layer WORKING. */
	len += sprintf(page + len, "n_write_refused %lu\n",
		       rtl819x_spi_n_write_refused);

	/* verify() */
	len += sprintf(page + len, "v_ran %d\n", rtl819x_spi_v_ran);
	len += sprintf(page + len, "v_rc %d\n", rtl819x_spi_v_rc);
	len += sprintf(page + len, "cmp_bytes %u\n", rtl819x_spi_v_cmp_bytes);
	len += sprintf(page + len, "cmp_equal %d\n",
		       rtl819x_spi_v_ran && rtl819x_spi_v_first_diff < 0);
	len += sprintf(page + len, "cmp_first_diff %ld\n",
		       rtl819x_spi_v_first_diff);
	len += sprintf(page + len, "cmp_diff_bytes %u\n",
		       rtl819x_spi_v_diff_bytes);
	len += sprintf(page + len, "digest_bytes %u\n",
		       rtl819x_spi_v_digest_bytes);
	len += sprintf(page + len, "complement_expected %u\n",
		       (unsigned)RTL819X_SPI_COMPLEMENT);
	len += sprintf(page + len, "h601_skipped %u\n",
		       rtl819x_spi_v_h601_skipped);

	/* THE GUARD.  The digests below print only because this is 0, and it
	 * is 0 because the arithmetic came out that way -- not because the
	 * skip was believed to be right. */
	len += sprintf(page + len, "h601_hashed %u\n", rtl819x_spi_v_h601_hashed);
	len += sprintf(page + len, "corrupt_at %ld\n", rtl819x_spi_corrupt_at);

	if (!rtl819x_spi_v_ran) {
		len += sprintf(page + len, "d1_sha256 (not run)\n");
		len += sprintf(page + len, "dmmio_sha256 (not run)\n");
	} else if (rtl819x_spi_v_h601_hashed) {
		len += sprintf(page + len,
			       "d1_sha256 WITHHELD h601_hashed=%u\n",
			       rtl819x_spi_v_h601_hashed);
		len += sprintf(page + len,
			       "dmmio_sha256 WITHHELD h601_hashed=%u\n",
			       rtl819x_spi_v_h601_hashed);
	} else {
		rtl819x_spi_hex(hx, rtl819x_spi_v_d1);
		len += sprintf(page + len, "d1_sha256 %s\n", hx);
		rtl819x_spi_hex(hx, rtl819x_spi_v_dmmio);
		len += sprintf(page + len, "dmmio_sha256 %s\n", hx);
	}
	len += sprintf(page + len, "d1_match %d\n", rtl819x_spi_v_d1_match);
	len += sprintf(page + len, "d1_d3_agree %d\n",
		       rtl819x_spi_v_ran && !rtl819x_spi_v_h601_hashed &&
		       !memcmp(rtl819x_spi_v_d1, rtl819x_spi_v_dmmio, 32));

	*eof = 1;
	return len;
}

/* ------------------------------------------------------------------------
 * Verbs.  Nothing in this driver issues a transaction except through one of
 * these, and each is one typed act -- the same shape R5-3a used to take the
 * interrupt path four gates at a time.
 * ------------------------------------------------------------------------ */

/* `probe` is the smallest possible act: one 4-byte Fast Read at offset 0,
 * which is what the vendor's own spi_regist does at the end of its probe.
 * It exists so the first transaction of a seating is 4 bytes and not 4 MiB. */
static int rtl819x_spi_verb_probe(void)
{
	u8 buf[4];
	int rc;

	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_read_pio(0, 4, buf);
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_markx("S-PROBE", (unsigned)rc);
	/* The four bytes are NOT printed.  Offset 0 is the loader region, and
	 * this driver emits no flash byte anywhere -- see the header. */
	return rc;
}

/* `wedge` is the POSITIVE CONTROL for the restore guard: without it,
 * n_state_bad = 0 and n_state_foreign = 0 are what a guard that CANNOT fire
 * also prints, and this project does not accept those.
 *
 * It runs one real 4-byte transaction with rtl819x_spi_force_mismatch set,
 * which makes release()'s read-back comparison fail.  The transaction must
 * come back -EIO, n_state_bad must move, and `wedged` must latch so that the
 * NEXT transaction is refused before it starts -- all three are checked
 * here, because "it returned an error" is weaker than "and then it stayed
 * refused".
 *
 * NOTHING WRONG IS WRITTEN TO THE CONTROLLER.  See the note above
 * rtl819x_spi_force_mismatch for the version of this that would have. */
static int rtl819x_spi_verb_wedge(void)
{
	unsigned long bad0;
	u8 buf[4];
	int rc, rc2, ok;

	mutex_lock(&rtl819x_spi_lock);
	bad0 = rtl819x_spi_n_state_bad;

	rtl819x_spi_force_mismatch = 1;
	rc = rtl819x_spi_read_pio(0, 4, buf);
	rtl819x_spi_force_mismatch = 0;

	/* The second half of the control: the latch has to hold. */
	rc2 = rtl819x_spi_read_pio(0, 4, buf);

	ok = (rc == -EIO) &&
	     (rtl819x_spi_n_state_bad == bad0 + 1) &&
	     (rtl819x_spi_wedged == 1) &&
	     (rc2 == -EIO);

	rtl819x_spi_wedged = 0;		/* the control cleans up after itself */
	mutex_unlock(&rtl819x_spi_lock);

	rlxfw_markx("S-WEDGE", (unsigned)ok);
	return ok ? 0 : -EPROTO;	/* the control PASSES when the guard
					 * refused, twice, for the right
					 * reason */
}

/* `trywrite` reaches layer L2 ON THE SILICON, which is the closest this image
 * can get to observing a write refusal by this driver.
 *
 * 🔴 WHY NOT L3, WHICH IS THE ONE THAT HAS NEVER FIRED ANYWHERE.  mtdchar's
 * :94 refusal -- `!(mtd->flags & MTD_WRITEABLE)` -- needs an EVEN char minor,
 * and tools/mkinitramfs.py refuses to declare one: it can check the odd-minor
 * rule from the declaration and cannot check mtd->flags, which is a run-time
 * property of this driver.  That refusal was accepted rather than argued with.
 * So :94 stays 讀, and this verb observes the layer immediately behind it.
 *
 * It calls through the mtd_info's own function pointers rather than the
 * functions directly, so what is exercised is the path the MTD core takes.
 * Safe by construction and checked by the assertion: the stubs contain no
 * transaction at all, and n_writes -- the flash-write counter -- must still
 * read 0 afterwards. */
static int rtl819x_spi_verb_trywrite(void)
{
	struct erase_info ei;
	unsigned long r0, w0;
	size_t rl = 0;
	u8 b = 0;
	int rcw, rce, ok;

	mutex_lock(&rtl819x_spi_lock);
	r0 = rtl819x_spi_n_write_refused;
	w0 = rtl819x_spi_n_writes;

	rcw = rtl819x_spi_mtd.write(&rtl819x_spi_mtd, 0, 1, &rl, &b);

	memset(&ei, 0, sizeof(ei));
	ei.mtd = &rtl819x_spi_mtd;
	ei.addr = 0;
	ei.len = RTL819X_SPI_ERASESIZE;
	rce = rtl819x_spi_mtd.erase(&rtl819x_spi_mtd, &ei);

	ok = (rcw == -EOPNOTSUPP) && (rce == -EOPNOTSUPP) && (rl == 0) &&
	     (ei.state == MTD_ERASE_FAILED) &&
	     (rtl819x_spi_n_write_refused == r0 + 2) &&
	     (rtl819x_spi_n_writes == w0) && (rtl819x_spi_n_writes == 0);
	mutex_unlock(&rtl819x_spi_lock);

	rlxfw_markx("S-TRYW", (unsigned)ok);
	return ok ? 0 : -EPROTO;
}

static int rtl819x_spi_verb_verify(const char *arg)
{
	unsigned long limit = 0;
	int rc;

	if (*arg)
		limit = simple_strtoul(arg, NULL, 0);
	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_verify((u32)limit);
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_markx("S-VRC", (unsigned)rc);
	rlxfw_markx("S-VDIFF", (unsigned)rtl819x_spi_v_diff_bytes);
	rlxfw_markx("S-VD1", (unsigned)rtl819x_spi_v_d1_match);
	return rc;
}

static int rtl819x_spi_verb_corrupt(const char *arg)
{
	if (!strcmp(arg, "off")) {
		rtl819x_spi_corrupt_at = -1;
		return 0;
	}
	rtl819x_spi_corrupt_at = (long)simple_strtoul(arg, NULL, 0);
	if (rtl819x_spi_corrupt_at < 0 ||
	    rtl819x_spi_corrupt_at >= (long)RTL819X_SPI_SIZE) {
		rtl819x_spi_corrupt_at = -1;
		return -EINVAL;
	}
	return 0;
}

static int rtl819x_spi_write_proc(struct file *file, const char __user *buffer,
				  unsigned long count, void *data)
{
	char buf[32];
	unsigned long n = count;
	int ret;

	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "probe"))
		ret = rtl819x_spi_verb_probe();
	else if (!strcmp(buf, "wedge"))
		ret = rtl819x_spi_verb_wedge();
	else if (!strcmp(buf, "unwedge")) {
		rtl819x_spi_wedged = 0;
		ret = 0;
	} else if (!strcmp(buf, "trywrite"))
		ret = rtl819x_spi_verb_trywrite();
	else if (!strcmp(buf, "verify"))
		ret = rtl819x_spi_verb_verify("");
	else if (!strncmp(buf, "verify ", 7))
		ret = rtl819x_spi_verb_verify(buf + 7);
	else if (!strncmp(buf, "corrupt ", 8))
		ret = rtl819x_spi_verb_corrupt(buf + 8);
	else
		return -EINVAL;

	return ret ? ret : (int)count;
}

/* ------------------------------------------------------------------------
 * Registration.
 *
 * late_initcall, and the level is a decision rather than a habit:
 *
 *  - the vendor's map driver is module_init, i.e. device_initcall, and it
 *    registers TWO partitions (量 from the baseline: CONFIG_ROOTFS_SQUASH
 *    with no dual image selects the two-entry rtl8196_parts1[] --
 *    "boot+cfg+linux" 0x130000 and "root fs" 0x2D0000, which re-derives
 *    FW-34's 1,245,184 and 2,949,120 exactly).  Registering BEFORE it would
 *    make this device mtd0 and move /dev/mtd0ro and /dev/mtdblock1 onto
 *    something else -- FW-30 declares both nodes.  So: after.  The
 *    PREDICTION, written before the board is powered, is mtd_index 2.
 *  - sha256_generic is a device_initcall too, so the crypto algorithm this
 *    driver's KAT asks for is registered by the time we run.
 *  - and the vendor's probe has finished touching the controller, so
 *    boot_sfcr/boot_sfcr2 latch the state Linux settles at rather than a
 *    state halfway through somebody else's transaction.
 * ------------------------------------------------------------------------ */

static int __init rtl819x_spi_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("S0");

	/* Latched before this driver issues anything, so a later reader can
	 * tell "the controller as Linux left it" from "as I left it". */
	rtl819x_spi_boot_sfcr  = rtl819x_spi_rd(RTL819X_SFCR);
	rtl819x_spi_boot_sfcr2 = rtl819x_spi_rd(RTL819X_SFCR2);
	rtl819x_spi_boot_sfcsr = rtl819x_spi_rd(RTL819X_SFCSR);

	/* S1 IS THE PREDICTION.  讀 from the r54 artefact says FFC00000
	 * (ComSrlCmd_RDID, SPI_CLK_DIV 7, divisor 16); REG-13 measured
	 * 3FC00000 at the loader prompt (divisor 4).  This mark is what makes
	 * the first of those 量 -- or refutes it. */
	rlxfw_markx("S1", rtl819x_spi_boot_sfcr);
	rlxfw_markx("S2", rtl819x_spi_boot_sfcr2);
	rlxfw_markx("S3", rtl819x_spi_boot_sfcsr);

	rtl819x_spi_kat_rc = rtl819x_spi_kat();
	rlxfw_markx("S4", (unsigned)rtl819x_spi_kat_rc);

	rtl819x_spi_add_rc = add_mtd_device(&rtl819x_spi_mtd);
	/* add_mtd_device returns 1 on failure in 2.6.30 -- 讀
	 * drivers/mtd/mtdcore.c, it returns 0 on success and 1 when no slot
	 * is free -- so this is not the usual errno convention and is not
	 * written as one. */
	rtl819x_spi_added = (rtl819x_spi_add_rc == 0);
	rlxfw_markx("S5", (unsigned)rtl819x_spi_add_rc);
	rlxfw_markx("S6", rtl819x_spi_added ?
		    (unsigned)rtl819x_spi_mtd.index : 0xFFFFFFFFu);

	pde = create_proc_entry(RTL819X_SPI_PROC_NAME, 0644, NULL);
	if (!pde) {
		/* Same call as rtl819x-gpio's: losing /proc costs the verbs,
		 * not the device, and tearing down a registered mtd because
		 * its debug interface failed is the worse of the two. */
		rlxfw_mark("S7-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_spi_read_proc;
	pde->write_proc = rtl819x_spi_write_proc;
	rlxfw_mark("S7");

	return 0;
}

late_initcall(rtl819x_spi_init);
