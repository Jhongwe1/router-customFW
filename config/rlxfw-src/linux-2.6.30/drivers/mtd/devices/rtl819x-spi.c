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
 * 🔄 R8b ITEM 4, 2026-10-04 (122nd segment).  ALL THREE LAYERS WERE RE-DECIDED
 * AND THE SHAPE CHANGED, SO THE PARAGRAPHS ABOVE DESCRIBE THE MAINLINE AND NOT
 * THE WHOLE RULE.  The four decisions are W1-W4 in rtl819x-spi-write.c's
 * header; what they do to the three layers here:
 *
 *  L1  CONFIG_MTD_RTL819X_WRITE is now DECLARED to kconfig -- `bool`,
 *      `default n`, config/host-compat/0010 -- so "no menu, no defconfig and
 *      no oldconfig can turn it on" is NO LONGER TRUE and must not be quoted.
 *      What replaces it is weaker and reviewable: the symbol is `n` in
 *      config/rlxfw-kernel.delta, so the TU is in no committed image, and
 *      kconfig-delta check is the instrument that says so about the .config
 *      the compiler actually saw.  MK5's `absent:` witness still covers the
 *      artefact.  A make-command-line override is no longer the only route,
 *      and that is the point: an override leaves no trace in .config.
 *  L2  The stubs still refuse in a mainline image, with -EOPNOTSUPP and the
 *      same counter, and MT-FLASH-2 is untouched.  They now also take
 *      rtl819x_spi_lock and ROUTE to the write TU when it is linked, where an
 *      unarmed request refuses with -EACCES.  So no card may carry the errno
 *      as a typed constant: `unarmed_rc` is printed below for that.
 *  L3  UNCHANGED, and that is W4's decision rather than an omission.  See the
 *      mtd_info below.
 *
 * ⚠️ AND THE HONEST SENTENCE ABOUT ALL OF IT: not one line of the write path
 * has run anywhere.  It is not in any committed image and has never been on
 * this die.  What was exercised at the desk is the POLICY's refusals, on the
 * host, through tools/test-spi-wrpolicy.sh -- which says nothing about the
 * silicon.
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
/* jiffies and HZ arrive through <linux/sched.h> in this tree, but 1.1 reads
 * both directly and an indirect include is a dependency nobody declared. */
#include <linux/jiffies.h>
#include <linux/param.h>
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

#define RTL819X_SPI_VERSION	"rtl819x-spi 1.2"

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

/* JEDEC Read ID.  `MT-FLASH-1`.  讀 from this unit's own loader, whose
 * ComSrlCmd_RDID at 0x804058BC issues exactly this opcode; D's own example
 * names 0x9F for this part.  Two sources, REG-14's rule satisfied. */
#define RTL819X_SPI_CMD_RDID	0x9Fu
/* The 24-bit answer this part gives.  FLS-04, and REG-21's flash descriptor
 * at 0x8040FBD4 holds the same three bytes two ways (001C7016 / 1C701600).
 * It identifies the PART, not this UNIT -- see the alphabet note above. */
#define RTL819X_SPI_RDID_EXPECT	0x001C7016u
/* The loader reads FOUR bytes and takes the top three: 量 from the fresh
 * disassembly, both callers at 0x80405050 and 0x8040505C pass a1 = 4, and
 * 0x80405064 is `srl s1,v0,0x8`.  This driver reuses that width rather than
 * asking for three, because a 4-byte phase is the one shape this controller
 * has been measured to serve 4,115 times. */
#define RTL819X_SPI_RDID_LEN	4

#define RTL819X_SPI_SIZE	0x00400000u	/* FLS-14 */
#define RTL819X_SPI_ERASESIZE	0x00001000u	/* sector, from the loader's
						 * fallback descriptor */
/* 🔴 THAT NUMBER IS 未定 AS A FACT ABOUT THIS PART, and this is the only place
 * in this file that says so.  SPEC.md `FW-187` 殘留 / `FW-191` 殘留: it is what
 * /proc/mtd reports (量 2026-10-04) and what the vendor's UNKNOWN fallback
 * assumes, which are two readings of SOFTWARE and no reading of the chip.  The
 * write path's own granularity is RLXFW_SPI_WR_ERASE_GRAIN in
 * rtl819x-spi-wrpolicy.h -- ONE line, which is where item 1's settled value is
 * substituted -- and rlxfw_spi_wr_chk_erase() refuses EVERY erase while the
 * two disagree, so changing one and forgetting the other is loud. */

/* H601 -- this unit's MAC and radio calibration.  CLAUDE.md's second Never
 * row.  Exactly two 4 KiB chunks, which is why the skip below has no
 * partial-chunk arithmetic. */
#define RTL819X_SPI_H601_LO	0x00006000u
#define RTL819X_SPI_H601_HI	0x00008000u
#define RTL819X_SPI_H601_SIZE	(RTL819X_SPI_H601_HI - RTL819X_SPI_H601_LO)

/* The `h601` verb's structure constants.  讀, from the vendor's own source;
 * every one is a layout fact of this SoC family, not a fact about this unit.
 *
 *   HDR   sizeof(PARAM_HEADER_T) -- signature[4] + len, __attribute__((packed)),
 *         apmib.h:2291-2295 and SIGNATURE_LEN 4 at :1648.  Corroborated three
 *         ways: apmib.c:326 declares `char hw_setting_start[6]`, apmib.c:329
 *         and flash.c:2050 both read exactly 6, and apmib.c:537 starts the
 *         body at OFFSET+sizeof(hsHeader).
 *   NIC0  offset of nic0Addr INSIDE the body.  HW_SETTING_T begins
 *         `unsigned char boardVer;` then `nic0Addr[6]` -- mibdef.h:13-15, and
 *         the struct is __PACK__ with every member a char, so no ABI can
 *         insert padding and the answer is 1 on any compiler.
 */
#define RTL819X_SPI_H601_HDR	6u
#define RTL819X_SPI_H601_NIC0	1u

/* The clamp.  🔴 NEITHER BOUND IS THE VENDOR'S -- see the verb's comment.
 * MIN is the smallest body this parser actually touches: boardVer(1) +
 * nic0Addr(6) + nic1Addr(6) + the checksum byte(1).  It is deliberately NOT
 * sizeof(HW_SETTING_T)+1 = 1166: that number is 推, computed from the drop's
 * headers and never compiled, and 980 of its bytes are a 5 GHz channel table
 * on a 2.4 GHz-only board -- so gating on it would refuse a good unit if this
 * drop is not the drop this unit shipped with.  `hw_len` is printed instead,
 * so a surprise is diagnosable without the gate having an opinion.
 * MAX keeps header+body inside the window that was read. */
#define RTL819X_SPI_H601_LEN_MIN	14u
#define RTL819X_SPI_H601_LEN_MAX	(RTL819X_SPI_H601_SIZE - \
					 RTL819X_SPI_H601_HDR)

#define RTL819X_SPI_CHUNK	4096u
#define RTL819X_SPI_COMPLEMENT	4186112u	/* FLS-24 */

/* ------------------------------------------------------------------------
 * THE MAP, AND WHY IT IS TWO LEVELS OF 32 RATHER THAN ONE LIST OF 1,024
 * ------------------------------------------------------------------------
 *
 * FLS-26, 量 2026-09-08: verify() found the first difference between this
 * flash and the 2026-08-16 dump at [0x9000,0xA000) and could find nothing
 * past it, because a PREFIX digest stops at the first difference.  4,153,344
 * bytes -- 99.02 % -- are undetermined.
 *
 * The obvious fix is a per-4-KiB digest list.  It does not fit, and the
 * reason is a hard limit rather than a preference: rtl819x_spi_read_proc is
 * a 2.6.30 read_proc_t, which sprintf()s into ONE page (PAGE_SIZE = 4096)
 * and sets *eof.  1,024 lines of ~76 characters is 78 KiB.  There is no
 * bounds check in that interface; a driver that overran it would corrupt
 * whatever follows the page, on a board with no spare.
 *
 * 32 x 32 = 1024 exactly.  So:
 *
 *   map 0        32 digests, one per 128 KiB group  -> which group differs
 *   map 1 <g>    32 digests, one per 4 KiB chunk of group g -> which sector
 *
 * Two commands answer the whole 4 MiB when one group differs, three when
 * two do, and EVERY one of them can be written into a card in advance
 * because the desk computes all 32 group digests and all 32 chunk digests
 * of any group it likes from the dump before the board is powered.  The
 * alternative -- verify with an offset, bisecting -- cannot be carded,
 * because each rung's address depends on the previous rung's answer.  That
 * is exactly why seating 16's nineteen BIS rungs were off-card.
 *
 * Output is bounded by construction (32 lines) and by RTL819X_SPI_MAP_BUDGET
 * at run time, and map_truncated says which.  A tool that can silently drop
 * the tail of its own answer is a tool whose zero means nothing.
 * ------------------------------------------------------------------------ */
#define RTL819X_SPI_MAP_N	32u	/* entries per level, both levels */
#define RTL819X_SPI_MAP_GROUP	(RTL819X_SPI_SIZE / RTL819X_SPI_MAP_N)
						/* 131072 = 128 KiB */
/* Every byte the map's own read_proc may write.  PAGE_SIZE is 4096; this
 * leaves 512 bytes of headroom against a line format that grows.  Checked
 * before every sprintf, not after. */
#define RTL819X_SPI_MAP_BUDGET	3584

/* The same ceiling for the FIRST /proc file, which had none until the rdid
 * and h601 fields arrived.  RESERVE is what the guarded block plus the
 * self-measuring line can emit at their widest -- 340 + 40 = 380, rounded
 * up.  Both numbers are derived in the comment at the guard itself. */
#define RTL819X_SPI_PROC_BUDGET		3584
#define RTL819X_SPI_PROC_RESERVE	512

/* 🔴 The bound the vendor's driver does not have.  A read of SFCSR is an
 * uncached KSEG1 load; FW-34 Group F measured an uncached word through the
 * flash window at 2.075 us, which is the slowest access on this bus, so
 * 200,000 spins is under 0.42 s even at that rate -- inside the watchdog
 * window CLK-08 bounds at 557 ms for the shorter of its two settings.  A
 * real phase completes in under a microsecond at any divider, so this is a
 * ceiling and not a delay. */
#define RTL819X_SPI_RDY_SPINS	200000u

#define RTL819X_SPI_PROC_NAME	"rtl819x-spi"
#define RTL819X_SPI_MAP_PROC_NAME "rtl819x-spi-map"
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

/* R8b item 4.  ATTEMPTS, which n_write_refused is not: once the write TU can
 * say yes, "how many times was mtd->write called" and "how many of those were
 * refused" stop being the same question, and a single counter answering both
 * would be a counter that cannot show a permitted write. */
static unsigned long rtl819x_spi_n_mtd_write_calls;
static unsigned long rtl819x_spi_n_mtd_erase_calls;

#ifdef CONFIG_MTD_RTL819X_WRITE
/* The write TU, then the install path's /proc block, defined at the end of
 * this file under the same CONFIG_ (R8b Gap A -- below every cited line). */
extern int rtl819x_spi_write_page(struct mtd_info *mtd, loff_t to, size_t len,
				  size_t *retlen, const u_char *buf);
extern int rtl819x_spi_erase_sector(struct mtd_info *mtd,
				    struct erase_info *instr);
extern int rtl819x_spi_wr_do_arm(u32 lo, u32 hi, u32 budget);
extern void rtl819x_spi_wr_do_disarm(void);
extern int rtl819x_spi_wr_proc(char *p);
extern int rtl819x_spi_wr_proc_max(void);
static int rtl819x_spi_inst_proc(char *page, int used);

/* What an UNARMED write answers in this build.  -EACCES, from the write TU's
 * errno table.  It is printed as `unarmed_rc` so a card compares against the
 * image's own number instead of a typed one -- the same rule as identifying a
 * booted image by RLXFW-ID0 rather than by a typed digest. */
#define RTL819X_SPI_UNARMED_RC	(-EACCES)
#else
/* No write TU: the stubs below are the whole answer and it is the one every
 * committed image has given since 2026-09-07. */
#define RTL819X_SPI_UNARMED_RC	(-EOPNOTSUPP)
#endif

/* `rdid` results.  n_rdid is SEPARATE from n_pio_bytes deliberately: that
 * counter means *bytes of the flash ARRAY read*, and RDID reads none -- it
 * reads the chip's identity register.  Folding the two would make a counter
 * this project quotes mean two things. */
static unsigned long rtl819x_spi_n_rdid;
static int  rtl819x_spi_rdid_ran;
static int  rtl819x_spi_rdid_rc = -EAGAIN;
static u32  rtl819x_spi_rdid_id;

/* `h601` results.  VERDICTS ONLY -- see the H601 paragraph in the header.
 * Every field below is either a boolean, a structure size identical on every
 * unit of this model, or a count. */
static int  rtl819x_spi_h601_ran;
static int  rtl819x_spi_h601_rc = -EAGAIN;
static int  rtl819x_spi_h601_sig_ok;
static int  rtl819x_spi_h601_ver;
static u32  rtl819x_spi_h601_len;
static int  rtl819x_spi_h601_len_sane;
static int  rtl819x_spi_h601_sum_ok;
static int  rtl819x_spi_h601_mac_not_zero;
static int  rtl819x_spi_h601_mac_not_ff;
static int  rtl819x_spi_h601_mac_group_bit;
/* 🔴 THERE IS NO mac_local_bit AND THAT IS DELIBERATE.  The first draft had
 * one.  docs/mfgtest.md §4 declares exactly four MAC booleans and states
 * that they leak four bits per run; a fifth would widen a containment
 * decision this file does not own, so it was removed rather than argued
 * for.  If a local-bit verdict is ever wanted, it is a change to §4 first. */

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

/* 1.1: the window verify() actually covered.  Before this there was only a
 * limit, so `cmp_bytes` and the scope were the same number and a windowed
 * run had no way to say where it had been. */
static u32  rtl819x_spi_v_start;
static u32  rtl819x_spi_v_len;

/* 🔴 1.1: the traversal timed IN THE KERNEL, against the tick this project
 * owns (R5-3b-2 registered the rating-300 clock_event_device, so jiffies is
 * driven by rtl819x-timer).  FW-48 stands as a bounded question because a
 * .timing row cannot separate *data arrived* from *the tool began waiting*
 * -- CORRECTIONS-block13 § 5 names this exact experiment as the way out:
 * "the driver can timestamp its own traversal against the 100 Hz clockevent
 * and take serial timing out of the path entirely".  hz is printed beside
 * it so the desk needs no compiled-in constant of its own. */
static unsigned long rtl819x_spi_v_jiffies;
static unsigned long rtl819x_spi_map_jiffies;

/* map() results. */
static int  rtl819x_spi_map_ran;
static int  rtl819x_spi_map_rc;
static int  rtl819x_spi_map_level = -1;
static u32  rtl819x_spi_map_group;
static u32  rtl819x_spi_map_unit;	/* bytes each entry covers */
static u32  rtl819x_spi_map_hashed;	/* bytes that reached a digest */
static u32  rtl819x_spi_map_h601_skipped;
static u32  rtl819x_spi_map_h601_hashed;  /* MUST be 0, same guard as verify */
static u32  rtl819x_spi_map_diff_units;	  /* entries where PIO != MMIO */
static int  rtl819x_spi_map_truncated;
static u8   rtl819x_spi_map_d[RTL819X_SPI_MAP_N][32];
static u32  rtl819x_spi_map_off[RTL819X_SPI_MAP_N];
static u32  rtl819x_spi_map_bytes[RTL819X_SPI_MAP_N];
static u8   rtl819x_spi_map_equal[RTL819X_SPI_MAP_N];

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

#ifdef CONFIG_MTD_RTL819X_WRITE
/* ------------------------------------------------------------------------
 * W3.  The two register-level write primitives.
 *
 * THEY LIVE HERE AND NOT IN THE WRITE TU, and the reason is the claim/release
 * pair above: it is the only thing in this project that saves SFCR/SFCR2/
 * SFCSR, restores them, reads them back and latches `wedged` when the restore
 * did not take -- and does NOT restore SFDR, because writing SFDR issues a
 * command.  A second copy of that guard in another file would be a second
 * owner of the one invariant that makes this driver survivable beside the
 * vendor's.  So the policy is over there and the registers are here.
 *
 * THE ORDER IS THE VENDOR'S, 讀 from spi_common.c in the tree that builds, and
 * docs/blind-write-ledger.md § 9.14 records every path.  What is NOT the
 * vendor's: both spins below are BOUNDED.  spiFlashReady() (:728-742) is
 * `while (1)` on the WIP bit with no ceiling and no counter, so a part that
 * never clears WIP reboots this router through the watchdog; here it returns
 * -ETIMEDOUT and counts.
 *
 * ⚠️ A VENDOR ODDITY THAT IS NOT COPIED.  SeqCmd_Order (:786-792) calls
 * `SFCSR_CS_L(ucChip, ucIOWidth, IOWIDTH_SINGLE)` -- the io-width in the
 * LENGTH argument and the length in the io-width argument, i.e. the two are
 * swapped.  It is inert only because DATA_LENTH1 and IOWIDTH_SINGLE are both
 * 0x00.  rtl819x_spi_cmd1() below passes a length of 0 on purpose rather than
 * reproducing the swap, so a future reader is not left deciding whether the
 * swap mattered.
 * ------------------------------------------------------------------------ */

#define RTL819X_SPI_CMD_WREN	0x06u	/* spi_common.c:129 */
#define RTL819X_SPI_CMD_PP	0x02u	/* spi_common.c, SPICMD_PP */
#define RTL819X_SPI_CMD_SE	0x20u	/* spi_common.c:138 */
#define RTL819X_SPI_CMD_RDSR	0x05u	/* spi_common.c:132 */
#define RTL819X_SPI_SR_WIP	0x01u	/* bit SPI_STATUS_WIP, :165 */

/* The WIP ceiling.  Each spin is a full RDSR transaction, so this is NOT
 * comparable with RTL819X_SPI_RDY_SPINS, which counts register reads.  推, and
 * labelled as a guess: a 4 KiB sector erase on this part family is tens of
 * milliseconds and a page program hundreds of microseconds, but this part's
 * datasheet is not on hand (`FW-191`: the draft here is the SoC's).  At the
 * ~2 us FW-34 Group F measured for an uncached access, 200,000 RDSR round
 * trips is far past either.  It is a ceiling and not a delay, and
 * n_wip_timeout is what says it was reached. */
#define RTL819X_SPI_WIP_SPINS	200000u

static unsigned long rtl819x_spi_n_wip_timeout, rtl819x_spi_wip_polls;

/* One opcode byte, CS down and up around it.  The vendor's SeqCmd_Order. */
static int rtl819x_spi_cmd1(u32 cmd)
{
	int rc = rtl819x_spi_cs_low(0);

	if (rc)
		return rc;
	rtl819x_spi_wr(RTL819X_SFDR, cmd << 24);
	rtl819x_spi_cs_high();
	return 0;
}

/* Poll RDSR bit 0 until WIP clears.  The vendor's spiFlashReady(), bounded.
 * The shift is SeqCmd_Read's: with a 1-byte read phase the answer is in the
 * TOP byte of SFDR (`ui >> ((4 - ucRDLen) * 8)`). */
static int rtl819x_spi_wait_wip(void)
{
	unsigned int i;

	for (i = 0; i < RTL819X_SPI_WIP_SPINS; i++) {
		u32 v = (u32)(rtl819x_spi_wip_polls = i + 1u);	/* D19 count */
		int rc = rtl819x_spi_cs_low(0);

		if (rc)
			return rc;
		rtl819x_spi_wr(RTL819X_SFDR,
			       (u32)RTL819X_SPI_CMD_RDSR << 24);
		rc = rtl819x_spi_cs_low(0);
		if (rc) {
			rtl819x_spi_cs_high();
			return rc;
		}
		v = rtl819x_spi_rd(RTL819X_SFDR) >> 24;
		rtl819x_spi_cs_high();
		if (!(v & RTL819X_SPI_SR_WIP))
			return 0;
		/* Preemptible: an erase is milliseconds and the TC0 interrupt that
		 * pets the watchdog has to run.  Same reason the lock above is a
		 * mutex and not a spinlock. */
		cond_resched();
	}
	rtl819x_spi_n_wip_timeout++;
	return -ETIMEDOUT;
}

/* n_writes, incremented from one place so the counter CLAUDE.md § Flash quotes
 * has one owner.  🔴 IT IS BLIND TO A VENDOR-SIDE WRITE: spi_probe.c:101-103
 * installs mtd_spi_write / mtd_spi_erase on the vendor's partitions
 * unconditionally and nothing here counts those.  The breakdown into programs
 * and erases is the write TU's wr_n_prog / wr_n_erase. */
void rtl819x_spi_note_write(int erase)
{
	rtl819x_spi_n_writes++;
}

/*
 * Page Program.  The vendor's ComSrlCmd_ComWrite with SPICMD_PP, ISFAST_NO,
 * IOWIDTH_SINGLE, DUMMYCOUNT_0 (PageWrite_111002, :1070-1074), inside this
 * driver's claim/release bracket.  The caller has already checked that
 * [addr, addr+len) is inside one page and outside the forbidden window.
 *
 * The bytes are assembled into the word EXPLICITLY, big end first, instead of
 * memcpy'ing a u32 the way the vendor does (:974-976) -- that is correct only
 * because this core is big-endian, and a driver whose correctness depends on
 * the host's endianness is a driver that breaks silently when it moves.
 */
int rtl819x_spi_pp_page(u32 addr, u32 len, const u8 *buf)
{
	struct rtl819x_spi_state s;
	int rc, rc2;
	u32 i, k, tail, v;

	rc = rtl819x_spi_claim(&s);
	if (rc)
		return rc;
	rtl819x_spi_n_xfer++;

	rc = rtl819x_spi_cmd1(RTL819X_SPI_CMD_WREN);
	if (rc)
		goto out;

	/* command, then three address bytes, no dummy, then a 4-byte phase */
	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, (u32)RTL819X_SPI_CMD_PP << 24);
	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, addr << 8);
	rtl819x_spi_wr(RTL819X_SFDR, addr << 16);
	rtl819x_spi_wr(RTL819X_SFDR, addr << 24);
	rc = rtl819x_spi_cs_low(3);
	if (rc)
		goto out;

	for (i = 0; i + 4u <= len; i += 4u) {
		v = ((u32)buf[i] << 24) | ((u32)buf[i + 1] << 16) |
		    ((u32)buf[i + 2] << 8) | (u32)buf[i + 3];
		rtl819x_spi_wr(RTL819X_SFDR, v);
	}
	tail = len - i;
	if (tail) {
		/* A short final phase, LEN = tail-1, the bytes in the TOP of the
		 * word -- which is what the vendor's memcpy of `tail` bytes into a
		 * u32 produces on this core, written out instead of inherited. */
		v = 0u;
		for (k = 0u; k < tail; k++)
			v |= (u32)buf[i + k] << (24 - 8u * k);
		rc = rtl819x_spi_cs_low(tail - 1u);
		if (rc)
			goto out;
		rtl819x_spi_wr(RTL819X_SFDR, v);
	}
	rtl819x_spi_cs_high();
	rc = rtl819x_spi_wait_wip();
out:
	rc2 = rtl819x_spi_release(&s);
	return rc ? rc : rc2;
}

/*
 * Sector/block erase.  The vendor's ComSrlCmd_SE (:819-825) -> SeqCmd_Order
 * WREN, SeqCmd_Write(SPICMD_SE, addr, 3), spiFlashReady.  SeqCmd_Write's
 * shift is `uiValue << ((4 - ucValueLen) * 8)` = addr << 8 for a 3-byte
 * value, and its phase length is ucValueLen-1 = 2.
 *
 * WHICH granularity this clears is 未定 -- see RLXFW_SPI_WR_ERASE_GRAIN -- and
 * the opcode is SE 0x20, which is what the vendor's UNKNOWN fallback selects
 * for this unrecognised part.  This function erases ONE block and the caller
 * loops, so a wrong grain shows up as a refused request rather than as eight
 * blocks cleared where one was asked for.
 */
int rtl819x_spi_se_block(u32 addr)
{
	struct rtl819x_spi_state s;
	int rc, rc2;

	rc = rtl819x_spi_claim(&s);
	if (rc)
		return rc;
	rtl819x_spi_n_xfer++;

	rc = rtl819x_spi_cmd1(RTL819X_SPI_CMD_WREN);
	if (rc)
		goto out;
	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, (u32)RTL819X_SPI_CMD_SE << 24);
	rc = rtl819x_spi_cs_low(2);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, addr << 8);
	rtl819x_spi_cs_high();
	rc = rtl819x_spi_wait_wip();
out:
	rc2 = rtl819x_spi_release(&s);
	return rc ? rc : rc2;
}
#endif	/* CONFIG_MTD_RTL819X_WRITE */

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

/* 1.1: a WINDOW, not a limit.
 *
 * `verify <n>` still means [0, n) -- every reading seating 16 took keeps its
 * meaning -- and `verify <n> <off>` means [off, off+n).  Both ends are
 * rounded DOWN to a chunk and an unaligned or out-of-range window is refused
 * rather than clamped: a clamp would silently hash a different scope from
 * the one the desk computed its expectation over, and comparing two digests
 * taken over different byte counts is the mistake the SCOPE? guard already
 * exists to prevent (notes/flash-digest-scope.md § 8.2).
 */
static int rtl819x_spi_verify(u32 start, u32 len)
{
	struct rtl819x_spi_hash h;
	u8 *a = NULL, *b = NULL;
	u32 off, i, limit;
	unsigned long t0;
	int rc = 0;

	/* Set before any `goto out` can be taken: the out: path reads it, and
	 * an uninitialised t0 there would print a duration for a run that
	 * never started -- a number that looks like a measurement. */
	t0 = jiffies;
	if (rtl819x_spi_kat_rc)
		return -EPERM;		/* a digest engine that has not passed
					 * its own vectors does not get used */
	if (!len || len > RTL819X_SPI_SIZE)
		len = RTL819X_SPI_SIZE;
	if (start & (RTL819X_SPI_CHUNK - 1u))
		return -EINVAL;
	len &= ~(RTL819X_SPI_CHUNK - 1u);
	if (!len || start >= RTL819X_SPI_SIZE)
		return -EINVAL;
	if (start + len > RTL819X_SPI_SIZE)
		return -ERANGE;		/* not clamped -- see the note above */
	limit = start + len;

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
	rtl819x_spi_v_start = start;
	rtl819x_spi_v_len = len;
	rtl819x_spi_v_jiffies = 0;

	for (off = start; off < limit; off += RTL819X_SPI_CHUNK) {
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
	/* Taken here rather than at the successful exit, so a run that bailed
	 * still says how long it had been going.  jiffies is unsigned and
	 * wraps; the subtraction is correct across the wrap and the interval
	 * measured so far is 13.4 s against a 2^32 tick wrap at 100 Hz. */
	rtl819x_spi_v_jiffies = jiffies - t0;
	rtl819x_spi_v_ran = 1;
	rtl819x_spi_v_rc = rc;
	return rc;
}

/* ------------------------------------------------------------------------
 * map() -- 32 digests, one level at a time.  See the MAP note by the
 * constants for why 32 x 32 and not 1,024.
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_map(int level, u32 group)
{
	struct rtl819x_spi_hash h;
	u8 *a = NULL, *b = NULL;
	u32 unit, base, e, off, i;
	unsigned long t0;
	int rc = 0;

	t0 = jiffies;			/* see verify(), same reason */
	if (rtl819x_spi_kat_rc)
		return -EPERM;
	if (level == 0) {
		unit = RTL819X_SPI_MAP_GROUP;
		base = 0;
		group = 0;
	} else if (level == 1) {
		if (group >= RTL819X_SPI_MAP_N)
			return -EINVAL;
		unit = RTL819X_SPI_MAP_GROUP / RTL819X_SPI_MAP_N;
		base = group * RTL819X_SPI_MAP_GROUP;
	} else {
		return -EINVAL;
	}

	memset(&h, 0, sizeof(h));
	h.tfm = crypto_alloc_shash("sha256", 0, 0);
	if (IS_ERR(h.tfm)) {
		rc = PTR_ERR(h.tfm);
		h.tfm = NULL;
		goto out;
	}
	a = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	b = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	if (!a || !b) {
		rc = -ENOMEM;
		goto out;
	}

	rtl819x_spi_map_level = level;
	rtl819x_spi_map_group = group;
	rtl819x_spi_map_unit = unit;
	rtl819x_spi_map_hashed = 0;
	rtl819x_spi_map_h601_skipped = 0;
	rtl819x_spi_map_h601_hashed = 0;
	rtl819x_spi_map_diff_units = 0;
	rtl819x_spi_map_truncated = 0;
	memset(rtl819x_spi_map_d, 0, sizeof(rtl819x_spi_map_d));

	for (e = 0; e < RTL819X_SPI_MAP_N; e++) {
		rtl819x_spi_map_off[e] = base + e * unit;
		rtl819x_spi_map_bytes[e] = 0;
		rtl819x_spi_map_equal[e] = 1;

		h.d1 = rtl819x_spi_desc(h.tfm);
		if (!h.d1) {
			rc = -ENOMEM;
			goto out;
		}
		for (off = rtl819x_spi_map_off[e];
		     off < rtl819x_spi_map_off[e] + unit;
		     off += RTL819X_SPI_CHUNK) {
			int in_h601 = (off >= RTL819X_SPI_H601_LO &&
				       off < RTL819X_SPI_H601_HI);

			rc = rtl819x_spi_read_pio(off, RTL819X_SPI_CHUNK, a);
			if (rc)
				goto out;
			rtl819x_spi_read_mmio(off, RTL819X_SPI_CHUNK, b);

			/* The same negative control verify() uses, so one
			 * verb moves both instruments and neither can be a
			 * digest that cannot fail. */
			if (rtl819x_spi_corrupt_at >= (long)off &&
			    rtl819x_spi_corrupt_at <
			    (long)(off + RTL819X_SPI_CHUNK))
				a[rtl819x_spi_corrupt_at - off] ^= 0xFFu;

			/* D3, per entry.  A verdict reveals no content, so it
			 * covers H601 exactly as verify()'s does. */
			for (i = 0; i < RTL819X_SPI_CHUNK; i++) {
				if (a[i] != b[i]) {
					rtl819x_spi_map_equal[e] = 0;
					break;
				}
			}

			if (in_h601) {
				rtl819x_spi_map_h601_skipped +=
					RTL819X_SPI_CHUNK;
				continue;
			}
			rc = crypto_shash_update(h.d1, a, RTL819X_SPI_CHUNK);
			if (rc)
				goto out;
			rtl819x_spi_map_bytes[e] += RTL819X_SPI_CHUNK;
			rtl819x_spi_map_hashed += RTL819X_SPI_CHUNK;
			/* The same belt-and-braces assertion verify() carries:
			 * it can only fire if CHUNK or H601's bounds stop
			 * being chunk-aligned, and then it fires instead of
			 * a digest of this unit's MAC being printed. */
			if (off + RTL819X_SPI_CHUNK > RTL819X_SPI_H601_LO &&
			    off < RTL819X_SPI_H601_HI)
				rtl819x_spi_map_h601_hashed +=
					RTL819X_SPI_CHUNK;

			/* Per CHUNK, matching verify().  It was per ENTRY in
			 * the first draft, which at level 0 is once per
			 * 128 KiB -- about 0.41 s by FW-48's slope, against
			 * verify()'s ~13 ms.  The watchdog is petted from the
			 * vendor's TC0 interrupt and does not depend on this,
			 * so nothing measured says 0.41 s is unsafe; it is a
			 * scheduling latency an order of magnitude worse than
			 * the function next door for no reason. */
			cond_resched();
		}
		rc = crypto_shash_final(h.d1, rtl819x_spi_map_d[e]);
		kfree(h.d1);
		h.d1 = NULL;
		if (rc)
			goto out;
		if (!rtl819x_spi_map_equal[e])
			rtl819x_spi_map_diff_units++;
	}
out:
	kfree(a);
	kfree(b);
	kfree(h.d1);
	if (h.tfm && !IS_ERR(h.tfm))
		crypto_free_shash(h.tfm);
	rtl819x_spi_map_jiffies = jiffies - t0;
	rtl819x_spi_map_ran = 1;
	rtl819x_spi_map_rc = rc;
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
 * on this kernel -- mtdchar.c:457 calls mtd->erase with no NULL check.  In a
 * mainline image they hold no write code and reference nothing in the write
 * TU; they are the errno that a NULL would have been if the MTD core had
 * checked.
 *
 * 🔄 R8b item 4.  TWO THINGS CHANGED AND BOTH ARE VISIBLE FROM OUTSIDE.
 *
 *  1. THEY TAKE THE LOCK.  In a CONFIG_MTD_RTL819X_WRITE image they issue a
 *     transaction, so they have to.  🔴 AND THAT IS WHY `trywrite` BELOW NO
 *     LONGER HOLDS IT: rtl819x_spi_lock is not recursive, so the old shape --
 *     verb takes the lock, then calls through the pointers -- would have
 *     DEADLOCKED on the first boot of the first write image, inside the one
 *     verb whose job is to show the refusal works.  量 is impossible here (no
 *     committed image links the TU), so this is a defect only reading finds,
 *     and it is recorded rather than quietly fixed.
 *  2. THE ATTEMPT AND THE REFUSAL ARE COUNTED SEPARATELY.  n_write_refused
 *     still moves by exactly one per refused call, so config/mfgtest.sh's
 *     MT-FLASH-2 (+2 across a trywrite) reads the same in BOTH builds: in a
 *     mainline image both pointers refuse, and in a write image offset 0 is
 *     inside the forbidden window so both refuse there too.  What changes is
 *     the errno, which is why it is printed rather than typed into a card.
 */
static int rtl819x_spi_mtd_write(struct mtd_info *mtd, loff_t to, size_t len,
				 size_t *retlen, const u_char *buf)
{
	int rc;

	mutex_lock(&rtl819x_spi_lock);
	rtl819x_spi_n_mtd_write_calls++;
#ifdef CONFIG_MTD_RTL819X_WRITE
	rc = rtl819x_spi_write_page(mtd, to, len, retlen, buf);
#else
	(void)mtd; (void)to; (void)buf;
	*retlen = 0;
	rc = -EOPNOTSUPP;
#endif
	if (rc)
		rtl819x_spi_n_write_refused++;
	mutex_unlock(&rtl819x_spi_lock);
	return rc;
}

static int rtl819x_spi_mtd_erase(struct mtd_info *mtd, struct erase_info *instr)
{
	int rc;

	mutex_lock(&rtl819x_spi_lock);
	rtl819x_spi_n_mtd_erase_calls++;
#ifdef CONFIG_MTD_RTL819X_WRITE
	rc = rtl819x_spi_erase_sector(mtd, instr);
#else
	(void)mtd;
	/* No callback is invoked: mtdchar only waits on one when erase()
	 * returned 0, so refusing here does not leave a sleeper. */
	instr->state = MTD_ERASE_FAILED;
	rc = -EOPNOTSUPP;
#endif
	if (rc)
		rtl819x_spi_n_write_refused++;
	mutex_unlock(&rtl819x_spi_lock);
	return rc;
}

static struct mtd_info rtl819x_spi_mtd = {
	.type		= MTD_NORFLASH,
	/* MTD_CAP_ROM is 0: MTD_WRITEABLE is NOT set, which is layer L3.
	 * mtdchar's mtd_open refuses an open for writing with -EACCES at :94,
	 * separately from the odd-minor rule at :73, and mtdblock.c:421 reads
	 * the same flag to mark the block device read-only.
	 *
	 * 🔄 R8b item 4's W4 RE-DECIDED THIS AND KEPT IT, WHICH IS A DECISION
	 * AND NOT AN OMISSION.  量 from the tree that builds: MTD_CAP_ROM is 0
	 * and MTD_WRITEABLE is 0x400 (include/mtd/mtd-abi.h:35, :29), and the
	 * vendor's own spi_chip_setup sets MTD_CAP_NORFLASH =
	 * MTD_WRITEABLE|MTD_BIT_WRITEABLE on ITS partitions (spi_probe.c:94).
	 * What MTD_CAP_NORFLASH here would buy is NOTHING REACHABLE:
	 * tools/mkinitramfs.py refuses to declare an even char minor over this
	 * device, so mtdchar's :73 odd-minor rule refuses the open whatever
	 * this flag says, and there is no `dd` and no mtd_debug in this image
	 * (config/image-commands.tsv).  What it would cost is the one static
	 * layer that cannot be armed away.  So the write path is reachable ONLY
	 * through this file's own verbs, and mtdchar and mtdblock stay outside
	 * the trust boundary entirely.
	 *
	 * ⚠️ THE OTHER ALTERNATIVE REJECTED: flipping the flag at run time
	 * inside the arm verb.  mtd_open reads it ONCE, at open(), and
	 * mtdblock.c:421 caches it into dev->readonly at add time -- so a
	 * descriptor opened while armed would stay writable after the disarm,
	 * and whether the refusal held would depend on WHEN the open happened.
	 * A guard whose answer depends on timing is not a guard.
	 *
	 * 🔴 L3 STILL HAS NEVER BEEN OBSERVED FIRING, here or anywhere in this
	 * project, and W4 does not change that: observing :94 needs an even
	 * char minor over THIS device, which mkinitramfs refuses -- correctly,
	 * since it can check the odd-minor rule from a declaration and cannot
	 * check mtd->flags.  So L3 is 讀 and stays 讀. */
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

	/* 1.1.  v_start/v_len say WHICH window the digests above are over --
	 * before this, `cmp_bytes` was both the scope and the length and a
	 * windowed run had no way to say where it had been.  v_jiffies is the
	 * traversal timed in the kernel against this project's own tick, with
	 * hz beside it so nothing downstream carries a constant. */
	len += sprintf(page + len, "v_start %u\n", rtl819x_spi_v_start);
	len += sprintf(page + len, "v_len %u\n", rtl819x_spi_v_len);
	len += sprintf(page + len, "v_jiffies %lu\n", rtl819x_spi_v_jiffies);
	len += sprintf(page + len, "hz %u\n", (unsigned)HZ);
	len += sprintf(page + len, "map_ran %d\n", rtl819x_spi_map_ran);
	len += sprintf(page + len, "map_rc %d\n", rtl819x_spi_map_rc);
	len += sprintf(page + len, "map_level %d\n", rtl819x_spi_map_level);
	len += sprintf(page + len, "map_group %u\n", rtl819x_spi_map_group);
	len += sprintf(page + len, "map_jiffies %lu\n",
		       rtl819x_spi_map_jiffies);

	/* ---------------------------------------------------------------
	 * 🔴 THE BUDGET, AND IT ARRIVES WITH THE FIRST FIELDS THAT NEEDED IT.
	 *
	 * This handler is a 2.6.30 read_proc_t: it sprintf()s into ONE page
	 * and there is no bounds check in that interface.  The header has
	 * said so since 1.1 -- "a driver that overran it would corrupt
	 * whatever follows the page, on a board with no spare" -- and then
	 * guarded only the SECOND file, because that is the one whose output
	 * grows with a loop.  This file's output grows when someone adds a
	 * field, which is slower and just as unbounded.
	 *
	 * 量, before the fields below were written: the worst case this
	 * handler could already produce is 1,101 bytes -- every %lu at ten
	 * digits, every %d at -2147483648, and the printed-digest branch
	 * taken, which is the widest of its three.  The SIXTEEN fields below
	 * add at most 340, and the self-measuring line after the guard adds
	 * at most 40, so RESERVE is 380 rounded up to 512.  (That arithmetic
	 * was got wrong once while writing this -- "fourteen fields, 317
	 * bytes" -- and re-derived by script rather than patched, because a
	 * reserve and a field count that are both wrong by the same amount
	 * stay self-consistent forever.)  So the guard is not load-bearing today and
	 * is written now because the moment to add one is while the headroom
	 * is still three kilobytes, not when a reader is chasing a corrupted
	 * page on a board with no spare.
	 *
	 * It guards what FOLLOWS it and nothing above, which is stated
	 * rather than left to be discovered: retro-fitting a check to 48
	 * existing sprintf()s would be a large edit to code that is 量 to
	 * fit, and a large edit to working code is its own risk. */
	if (len + RTL819X_SPI_PROC_RESERVE <= RTL819X_SPI_PROC_BUDGET) {
		/* `MT-ID`, and putting it here turns a host-side check into a
		 * device-side one.  RLXFW_SRC_ID is the build's own digest
		 * over config/, delivered to every C object as KCPPFLAGS, and
		 * until now its only reader was init/main.c printing the
		 * RLXFW-ID0 boot mark.  A capture and a /proc read are then
		 * two independent routes to one number, which is the shape
		 * this project prefers over one route asserted twice.
		 *
		 * The #else is not defensive padding: `--id-scope main` is a
		 * real, declared build mode under which this define does not
		 * reach this file, and a check must be able to see that it is
		 * looking at such a build rather than read a missing line as
		 * a mismatch. */
#ifdef RLXFW_SRC_ID
		len += sprintf(page + len, "recipe_id %08X\n",
			       (unsigned)RLXFW_SRC_ID);
#else
		len += sprintf(page + len, "recipe_id absent\n");
#endif
		len += sprintf(page + len, "n_rdid %lu\n", rtl819x_spi_n_rdid);
		len += sprintf(page + len, "rdid_ran %d\n",
			       rtl819x_spi_rdid_ran);
		len += sprintf(page + len, "rdid_rc %d\n",
			       rtl819x_spi_rdid_rc);
		len += sprintf(page + len, "rdid_id %06X\n",
			       rtl819x_spi_rdid_id);
		/* The comparand is compiled in, so the board is not told what
		 * to expect by whoever typed the verb.  MT-FLASH-1's own
		 * injection is on the SCRIPT's comparator, which is class S
		 * and is declared as such in docs/mfgtest.md §2. */
		len += sprintf(page + len, "rdid_expect %06X\n",
			       RTL819X_SPI_RDID_EXPECT);
		len += sprintf(page + len, "rdid_match %d\n",
			       rtl819x_spi_rdid_ran && !rtl819x_spi_rdid_rc &&
			       rtl819x_spi_rdid_id == RTL819X_SPI_RDID_EXPECT);

		len += sprintf(page + len, "h601_ran %d\n",
			       rtl819x_spi_h601_ran);
		len += sprintf(page + len, "h601_rc %d\n",
			       rtl819x_spi_h601_rc);
		len += sprintf(page + len, "hw_sig_ok %d\n",
			       rtl819x_spi_h601_sig_ok);
		len += sprintf(page + len, "hw_ver %d\n",
			       rtl819x_spi_h601_ver);
		/* A structure size, identical on every unit of this model.
		 * docs/mfgtest.md §4 rules on it explicitly. */
		len += sprintf(page + len, "hw_len %u\n",
			       rtl819x_spi_h601_len);
		len += sprintf(page + len, "hw_len_sane %d\n",
			       rtl819x_spi_h601_len_sane);
		len += sprintf(page + len, "hw_sum_ok %d\n",
			       rtl819x_spi_h601_sum_ok);
		len += sprintf(page + len, "mac_not_zero %d\n",
			       rtl819x_spi_h601_mac_not_zero);
		len += sprintf(page + len, "mac_not_ff %d\n",
			       rtl819x_spi_h601_mac_not_ff);
		len += sprintf(page + len, "mac_group_bit %d\n",
			       rtl819x_spi_h601_mac_group_bit);

		/* R8b item 4.  FOUR LINES THAT EVERY IMAGE PRINTS, so a card can
		 * tell a mainline image from a write image and can read this
		 * image's own refusal errno instead of carrying one.  `wr_linked`
		 * is the discriminator; `unarmed_rc` is what MT-FLASH-2 and any
		 * trywrite gate compare against.  They are inside the budget's
		 * guarded block, so RESERVE covers them: four lines at under 32
		 * bytes is 128 against 512 - 380 = 132 of slack, which is 量 by
		 * proc_bytes_before_this_line and not by this arithmetic. */
#ifdef CONFIG_MTD_RTL819X_WRITE
		len += sprintf(page + len, "wr_linked 1\n");
#else
		len += sprintf(page + len, "wr_linked 0\n");
#endif
		len += sprintf(page + len, "unarmed_rc %d\n",
			       RTL819X_SPI_UNARMED_RC);
		len += sprintf(page + len, "n_mtd_write_calls %lu\n",
			       rtl819x_spi_n_mtd_write_calls);
		len += sprintf(page + len, "n_mtd_erase_calls %lu\n",
			       rtl819x_spi_n_mtd_erase_calls);
	} else {
		len += sprintf(page + len, "proc_truncated 1\n");
	}
#ifdef CONFIG_MTD_RTL819X_WRITE
	/* The write TU's own fields, behind a SECOND budget check with the TU's
	 * own declared maximum.  A separate `if` and not folded into the one
	 * above on purpose: that block is 量 to fit and this one is in no image
	 * yet, so a reader can see which of the two ran out of room.  Its
	 * wr_truncated, like the install block's inst_truncated, prints either
	 * way: a short answer must never be ambiguous ("no room"/"nothing"). */
	if (len + rtl819x_spi_wr_proc_max() <= RTL819X_SPI_PROC_BUDGET) {
		len += rtl819x_spi_wr_proc(page + len);
		len += sprintf(page + len, "wr_truncated 0\n");
	} else {
		len += sprintf(page + len, "wr_truncated 1\n");
	}
	len += sprintf(page + len, "n_wip_timeout %lu\n",
		       rtl819x_spi_n_wip_timeout);
	len += rtl819x_spi_inst_proc(page + len, len);	/* R8b Gap A */
#endif
	/* Self-measuring, so the headroom is a reading a card can assert on
	 * rather than an arithmetic nobody re-runs.  It reports the length
	 * BEFORE its own line, which is why it is last and why it says so. */
	len += sprintf(page + len, "proc_bytes_before_this_line %d\n", len);

	*eof = 1;
	return len;
}

/* ------------------------------------------------------------------------
 * The map's own /proc file.
 *
 * 🔴 A SECOND file rather than more lines in the first one, and that is a
 * decision with a measured reason.  Every card in this project predicts the
 * BYTE COUNT of its captures -- seating 16's ten boot captures were 1,318
 * bytes against a prediction of 1,318 -- and every one of the seating's
 * thirty-two cells reads /proc/rtl819x-spi.  Appending 2.5 KiB to that file
 * would move all of them.  The map goes somewhere else, and the existing
 * dump keeps its shape except for the nine fields above, which are declared.
 *
 * The budget is checked BEFORE each sprintf and map_truncated is printed
 * either way, so a reader is never left to infer from a short answer whether
 * the map ran out of room or the flash ran out of differences.
 * ------------------------------------------------------------------------ */

static int rtl819x_spi_map_read_proc(char *page, char **start, off_t off,
				     int count, int *eof, void *data)
{
	char hx[66];
	int len = 0;
	u32 e;

	len += sprintf(page + len, "version %s\n", RTL819X_SPI_VERSION);
	len += sprintf(page + len, "map_ran %d\n", rtl819x_spi_map_ran);
	len += sprintf(page + len, "map_rc %d\n", rtl819x_spi_map_rc);
	len += sprintf(page + len, "map_level %d\n", rtl819x_spi_map_level);
	len += sprintf(page + len, "map_group %u\n", rtl819x_spi_map_group);
	len += sprintf(page + len, "map_unit %u\n", rtl819x_spi_map_unit);
	len += sprintf(page + len, "map_entries %u\n", RTL819X_SPI_MAP_N);
	len += sprintf(page + len, "map_hashed %u\n", rtl819x_spi_map_hashed);
	len += sprintf(page + len, "map_h601_skipped %u\n",
		       rtl819x_spi_map_h601_skipped);
	/* THE GUARD, same one verify() carries: the digests below print only
	 * because this is 0, and it is 0 because the arithmetic came out that
	 * way rather than because the skip was believed to be right. */
	len += sprintf(page + len, "map_h601_hashed %u\n",
		       rtl819x_spi_map_h601_hashed);
	len += sprintf(page + len, "map_diff_units %u\n",
		       rtl819x_spi_map_diff_units);
	len += sprintf(page + len, "map_jiffies %lu\n",
		       rtl819x_spi_map_jiffies);
	len += sprintf(page + len, "hz %u\n", (unsigned)HZ);
	len += sprintf(page + len, "corrupt_at %ld\n", rtl819x_spi_corrupt_at);

	if (!rtl819x_spi_map_ran || rtl819x_spi_map_rc) {
		len += sprintf(page + len, "map_truncated 0\n");
		len += sprintf(page + len, "# no map has completed\n");
		*eof = 1;
		return len;
	}
	if (rtl819x_spi_map_h601_hashed) {
		len += sprintf(page + len, "map_truncated 0\n");
		len += sprintf(page + len,
			       "# WITHHELD map_h601_hashed=%u\n",
			       rtl819x_spi_map_h601_hashed);
		*eof = 1;
		return len;
	}

	/* One line per entry: offset, PIO==MMIO, bytes hashed, digest.  Every
	 * digest line is EXACTLY 80 characters (6+1+1+1+6+1+64) and a SKIPPED
	 * line is 23, both fixed width, which is what lets a desk-side reader
	 * diff two captures line for line.
	 *
	 * 80 is the terminal width and that is safe here, measured rather than
	 * assumed: FW-49 (量 2026-09-08, over 762 committed captures) found
	 * that only the ECHO of a typed line is wrapped -- by busybox ash's
	 * line editor, 33 times, always with len(sent) >= 80 -- while OUTPUT
	 * is not, an 88-character /proc/version line arriving whole in five
	 * captures from five seatings.  Nothing between this sprintf and the
	 * capture file counts columns. */
	for (e = 0; e < RTL819X_SPI_MAP_N; e++) {
		/* 81 = the 80-character digest line plus its newline; 96
		 * leaves slack for a format that grows.  The first draft
		 * wrote 80 and was off by exactly the newline. */
		if (len + 96 > RTL819X_SPI_MAP_BUDGET) {
			rtl819x_spi_map_truncated = 1;
			break;
		}
		if (!rtl819x_spi_map_bytes[e]) {
			len += sprintf(page + len, "%06X %d %6u SKIPPED\n",
				       rtl819x_spi_map_off[e],
				       rtl819x_spi_map_equal[e],
				       rtl819x_spi_map_bytes[e]);
			continue;
		}
		rtl819x_spi_hex(hx, rtl819x_spi_map_d[e]);
		len += sprintf(page + len, "%06X %d %6u %s\n",
			       rtl819x_spi_map_off[e],
			       rtl819x_spi_map_equal[e],
			       rtl819x_spi_map_bytes[e], hx);
	}
	len += sprintf(page + len, "map_truncated %d\n",
		       rtl819x_spi_map_truncated);
	len += sprintf(page + len, "map_lines %u\n", e);

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

/*
 * `rdid` -- JEDEC Read ID, opcode 0x9F.  `MT-FLASH-1`.
 *
 * ------------------------------------------------------------------------
 * WHY THIS ISSUES NO SFCR WRITE, AND WHY THAT IS A READING AND NOT A HOPE
 * ------------------------------------------------------------------------
 *
 * `docs/mfgtest.md` §7 opened this as an undetermined question, on the
 * ground that "this driver never writes SFCR" while the loader's
 * ComSrlCmd_RDID does.  Both halves of that sentence were wrong, and the
 * second one was wrong in a way that hid the answer.
 *
 *  1. 🔴 THIS DRIVER HAS NEVER HAD SUCH A CONTRACT.  It writes SFCR on
 *     every transaction, at rtl819x_spi_release().  The only "never writes
 *     it" in this file is about SFCSR's CMD_BYTE field.  The true invariant
 *     is narrower and stronger: SFCR is only ever written back with the
 *     value claim() read microseconds earlier, never with a value of this
 *     driver's own choosing -- and release()'s read-back is what enforces
 *     it rather than asserts it.  This verb keeps that invariant exactly.
 *
 *  2. 🔴 THE LOADER'S SFCR WRITE IS NOT PART OF THE TRANSACTION.  讀, from
 *     a fresh disassembly of the FULL routine -- the excerpt quoted in
 *     `docs/loader-flash-write.md` begins at 0x8040591C, which is 96 bytes
 *     and 24 instructions into a routine that starts at 0x804058BC, and
 *     the SFCR write lives in the part not shown.  The order is:
 *
 *         804058E4  spin on SFCSR RDY
 *         80405900  sw   0xFFC00000 -> SFCR     <-- divider, BEFORE any CS
 *         80405904  jal  0x804057AC             <-- CS_L/CS_H twice: an idle
 *         80405914  jal  SFCSR_CS_L(chip, 0, 0) <-- the transaction starts
 *         80405944  sw   0x9F000000 -> SFDR     <-- the opcode
 *         80405954  jal  SFCSR_CS_L(chip, n-1, 0)
 *         8040595C  lw   SFDR                   <-- the answer
 *         80405968  jal  SFCSR_CS_H(chip, 0, 0)
 *
 *     CS is asserted at 0x80405914, sixteen instructions AFTER the SFCR
 *     write.  So the SFCR write is bus setup performed at probe time, when
 *     the divider is unknown -- not a step the opcode needs.
 *
 *  3. AND UNDER LINUX THE DIVIDER IS ALREADY THAT VALUE.  量, seating 16:
 *     boot_sfcr reads FFC00000, which is the exact word ComSrlCmd_RDID
 *     writes, because spi_regist calls it twice at device_initcall and it
 *     is the only function in the whole image that writes that register.
 *     So the loader's SFCR write would be idempotent here.  Skipping it
 *     runs this opcode at precisely the divider the vendor's own RDID runs
 *     it at, and n_state_foreign is the standing instrument that says so:
 *     it counts transactions beginning with an SFCR this driver did not
 *     expect, and it read 0 across 4,115 of them.
 *
 * REFUTATION CONDITIONS, written before the verb ran anywhere:
 *   - rdid_id != 1C7016 -> either this sequence is wrong or FLS-04 is.
 *     Discriminator: the loader reads the same value on every boot into the
 *     descriptor REG-21 measured as 001C7016 at 0x8040FBD4.
 *   - n_state_foreign moves on this transaction -> §3 above is refuted and
 *     the divider was not what registration latched.
 *   - n_state_bad moves, or wedged latches -> the restore did not take.
 *   - n_writes moves -> this is no longer a read-only act.  It cannot: no
 *     code path in this translation unit increments it.
 *
 * WHAT IT EMITS, AND WHY THAT IS A WIDENING THIS FILE HAS TO DECLARE.  The
 * header's permitted alphabet is "digests over the complement, an offset,
 * counters and controller registers".  A JEDEC id is none of those, so it
 * is a new class and is named here rather than left for a reviewer to
 * infer.  It is admissible because it identifies the PART and not this
 * UNIT -- every N150RT of this revision answers 1C7016 -- and because the
 * value is already committed in this repository twice, at SPEC.md FLS-04
 * and in REG-21's descriptor.  It is not a byte of the flash array: RDID
 * is answered by the chip's identity register and reads no array address.
 */
static int rtl819x_spi_verb_rdid(void)
{
	struct rtl819x_spi_state s;
	int rc, rc2;
	u32 v = 0;

	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_claim(&s);
	if (rc) {
		mutex_unlock(&rtl819x_spi_lock);
		rtl819x_spi_rdid_ran = 1;
		rtl819x_spi_rdid_rc = rc;
		rtl819x_spi_rdid_id = 0;
		/* The mark is emitted on EVERY path, including this one.  A
		 * verb that prints a mark when it succeeds and nothing when
		 * it is refused teaches a card to read silence as a failure
		 * mode it cannot distinguish from a mark that was lost. */
		rlxfw_markx("S-RDID", 0);
		return rc;
	}
	rtl819x_spi_n_rdid++;

	/* One byte out.  The opcode is taken from the TOP byte of the word
	 * when LEN selects one byte -- the same reason read_pio shifts its
	 * address left rather than masking it. */
	rc = rtl819x_spi_cs_low(0);
	if (rc)
		goto out;
	rtl819x_spi_wr(RTL819X_SFDR, (u32)RTL819X_SPI_CMD_RDID << 24);

	/* Four bytes back, which is what the loader asks for: both of its
	 * callers pass 4 and then take the top three with `srl v0,8`. */
	rc = rtl819x_spi_cs_low(RTL819X_SPI_RDID_LEN - 1);
	if (rc)
		goto out;
	v = rtl819x_spi_rd(RTL819X_SFDR);
out:
	rc2 = rtl819x_spi_release(&s);
	mutex_unlock(&rtl819x_spi_lock);
	rc = rc ? rc : rc2;

	rtl819x_spi_rdid_ran = 1;
	rtl819x_spi_rdid_rc = rc;
	/* The fourth byte is whatever the part clocks out after the three
	 * identity bytes.  It is undefined by JEDEC for this opcode, nothing
	 * here depends on it, and it is discarded rather than printed. */
	rtl819x_spi_rdid_id = rc ? 0 : (v >> 8);
	rlxfw_markx("S-RDID", rtl819x_spi_rdid_id);
	return rc;
}

/*
 * `h601` -- the hardware-settings block, read as a STRUCTURE and reported as
 * VERDICTS.  `MT-MAC` and `MT-RFCAL`.
 *
 * ------------------------------------------------------------------------
 * WHY THIS IS NOT A SECOND INSTRUMENT MEASURING WHAT `map 1 0` MEASURES
 * ------------------------------------------------------------------------
 *
 * `map 1 0` already emits a per-4-KiB line for offsets 006000 and 007000 --
 * an offset, a PIO-vs-MMIO equality boolean, and the word SKIPPED.  So
 * "are those pages readable and self-consistent" is answered.  This verb
 * answers a question that one cannot: whether the bytes PARSE.  A page can
 * be read identically by two paths and still hold a block whose checksum
 * does not close, which is the failure a factory test exists to catch.
 * If this verb only reported equality it would be a zero that means
 * nothing, and it would not be written.
 *
 * ------------------------------------------------------------------------
 * THE STRUCTURE, 讀 FROM THE VENDOR'S OWN SOURCE, AND THE FOUR PLACES THE
 * DESIGN DOCUMENT WAS WRONG OR SILENT
 * ------------------------------------------------------------------------
 *
 *   +0x0000  4  signature -- 'H' '6' then the version as two ASCII digits
 *   +0x0004  2  len       -- body bytes INCLUDING the trailing checksum
 *   +0x0006  .  body      -- boardVer(1), nic0Addr[6], nic1Addr[6], ...
 *   +0x0006+len-1  1      -- the checksum byte
 *
 *  1. 🔴 `len` IS BIG-ENDIAN AND §4 DOES NOT SAY SO.  The device stores it
 *     in native order and this part is big-endian; the proof is the x86
 *     HOST builder, which swaps on the way in -- `cvcfg.c:635`,
 *     `Header.len = WORD_SWAP(Header.len);//important!`, and again at :1794,
 *     :1829, :1883.  Read the other way round, 0x048E becomes 0x8E04, a
 *     length that runs off the end of the window.  This reads it byte by
 *     byte so the order is written down rather than inherited.
 *
 *  2. 🔴 THE VENDOR BOUNDS `len` FROM BELOW ONLY.  `apmib.c:469` refuses
 *     `len < sizeof(HW_SETTING_T)+1` and compares it against nothing else;
 *     `HW_SETTING_SECTOR_LEN` appears only on the COMPRESSED path
 *     (`apmib.c:369`, `:1626`).  So a corrupt length makes the vendor read
 *     straight through this window and into DEFAULT_SETTING at 0x8000.
 *     The clamp below is this driver's, not the vendor's, and it is what
 *     keeps every access inside the 8 KiB that was read.
 *
 *  3. 🔴 THE CHECKSUM FORMULA IS AT `apmib.h:1833`, NOT `apmib.c:547`.
 *     §4 cites the call site.  The arithmetic §4 states is right:
 *     CHECKSUM sums bytes into an `unsigned char` and returns `~sum + 1`,
 *     so CHECKSUM_OK's invariant is that the sum over all `len` body bytes,
 *     the checksum byte included, is zero.  The 6-byte header is NOT
 *     covered -- `apmib.c:537` reads the body from OFFSET+sizeof(header)
 *     and `:547` checksums that same buffer, and `/bin/flash`'s own
 *     `flash.c:2946-2951` does the identical thing independently.
 *
 *  4. ⚠️ "H6" IS NOT THE ONLY TAG THE VENDOR ACCEPTS.  `apmib.c:338` also
 *     takes "Hf" and "Hu", and anything else means a COMPRESSED block with
 *     a different layout, not a corrupt one.  So `hw_sig_ok 0` here means
 *     *not the uncompressed H6 form*.  It is a stricter test than the
 *     vendor's and the direction is the safe one, but it is not the same
 *     test and saying so is the difference between a verdict and a guess.
 *
 * ------------------------------------------------------------------------
 * CONTAINMENT
 * ------------------------------------------------------------------------
 *
 * The bytes enter DRAM, which `verify` and `map` already do and the header
 * already says.  What may not happen is that any of them, or any digest of
 * them, reaches the console -- CLAUDE.md's second Never row is explicit
 * that not even a sha256 of this window may enter the repository.  So this
 * verb prints: three booleans about the header, a version, a structure size
 * identical on every unit of this model, and four booleans about the MAC.
 * docs/mfgtest.md §4 declares exactly that set and states its cost as four
 * bits per run.  Nothing here prints a byte, a digest, or an index into
 * the body.
 */
static int rtl819x_spi_verb_h601(void)
{
	u8 *buf;
	int rc;
	u32 len, i;
	u8 sum = 0;
	const u8 *body, *mac;

	/* 🔴 EVERY VERDICT IS CLEARED FIRST, and that is not tidiness.  These
	 * are file statics, and the two MAC booleans are OR-accumulated in a
	 * loop that only ever writes 1.  Without this, a second run against a
	 * blanked block would inherit the first run's `mac_not_zero 1` and
	 * report a good MAC that is not there -- a stale pass, which is the
	 * one direction a factory test may never fail in.  The early `goto
	 * out` paths make it worse: they leave every field at whatever the
	 * previous run left. */
	rtl819x_spi_h601_sig_ok = 0;
	rtl819x_spi_h601_ver = -1;
	rtl819x_spi_h601_len = 0;
	rtl819x_spi_h601_len_sane = 0;
	rtl819x_spi_h601_sum_ok = 0;
	rtl819x_spi_h601_mac_not_zero = 0;
	rtl819x_spi_h601_mac_not_ff = 0;
	rtl819x_spi_h601_mac_group_bit = 0;

	buf = kmalloc(RTL819X_SPI_H601_SIZE, GFP_KERNEL);
	if (!buf) {
		rtl819x_spi_h601_ran = 1;
		rtl819x_spi_h601_rc = -ENOMEM;
		rlxfw_markx("S-H601", (unsigned)-ENOMEM);
		return -ENOMEM;
	}

	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_read_pio(RTL819X_SPI_H601_LO,
				  RTL819X_SPI_CHUNK, buf);
	if (!rc)
		rc = rtl819x_spi_read_pio(RTL819X_SPI_H601_LO +
					  RTL819X_SPI_CHUNK,
					  RTL819X_SPI_CHUNK,
					  buf + RTL819X_SPI_CHUNK);
	mutex_unlock(&rtl819x_spi_lock);

	rtl819x_spi_h601_ran = 1;
	rtl819x_spi_h601_rc = rc;
	if (rc)
		goto out;

	rtl819x_spi_h601_sig_ok = (buf[0] == 'H' && buf[1] == '6');

	/* Two ASCII decimal digits.  -1 where they are not digits, which is
	 * what the vendor's sscanf failure leaves too. */
	if (buf[2] >= '0' && buf[2] <= '9' && buf[3] >= '0' && buf[3] <= '9')
		rtl819x_spi_h601_ver = (buf[2] - '0') * 10 + (buf[3] - '0');
	else
		rtl819x_spi_h601_ver = -1;

	len = ((u32)buf[4] << 8) | buf[5];		/* big-endian, see 1 */
	rtl819x_spi_h601_len = len;
	rtl819x_spi_h601_len_sane =
		(len >= RTL819X_SPI_H601_LEN_MIN &&
		 len <= RTL819X_SPI_H601_LEN_MAX);

	/* Every read below is inside the 8 KiB already in `buf`, and it is
	 * the clamp above that makes that true rather than the layout. */
	if (!rtl819x_spi_h601_len_sane)
		goto out;

	body = buf + RTL819X_SPI_H601_HDR;
	for (i = 0; i < len; i++)
		sum += body[i];
	rtl819x_spi_h601_sum_ok = (sum == 0);

	mac = body + RTL819X_SPI_H601_NIC0;
	for (i = 0; i < 6; i++) {
		if (mac[i] != 0x00u)
			rtl819x_spi_h601_mac_not_zero = 1;
		if (mac[i] != 0xFFu)
			rtl819x_spi_h601_mac_not_ff = 1;
	}
	/* Bit 0 of the first octet.  Clear on any unicast address, so a set
	 * bit here says the block does not hold a usable station MAC. */
	rtl819x_spi_h601_mac_group_bit = mac[0] & 1u;
out:
	/* 🔴 The buffer held this unit's MAC.  Zero it before freeing: the
	 * page goes back to the allocator, and MEM-17 measured this DRAM
	 * keeping a previous power cycle's contents. */
	memset(buf, 0, RTL819X_SPI_H601_SIZE);
	kfree(buf);
	rlxfw_markx("S-H601", (unsigned)rtl819x_spi_h601_rc);
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

	/* 🔴 NO mutex AROUND THIS SINCE R8b ITEM 4, and that is why the
	 * restructuring was not cosmetic.  mtd->write and mtd->erase now take
	 * rtl819x_spi_lock themselves -- they must, because in a write image
	 * they issue a transaction -- and this mutex is not recursive, so the
	 * old shape would have deadlocked here on the first boot of the first
	 * write image.  Nothing else can issue a verb concurrently: ONE
	 * writable /proc entry takes verbs (an armed build's second one,
	 * rtl819x-spi-img, only appends to RAM under rtl819x_spi_lock) and the
	 * shell that writes it is serial, so reading the counters outside the
	 * lock is not a race on this board.  Said rather than left implicit,
	 * because it IS an assumption. */
	r0 = rtl819x_spi_n_write_refused;
	w0 = rtl819x_spi_n_writes;

	rcw = rtl819x_spi_mtd.write(&rtl819x_spi_mtd, 0, 1, &rl, &b);

	memset(&ei, 0, sizeof(ei));
	ei.mtd = &rtl819x_spi_mtd;
	ei.addr = 0;
	ei.len = RTL819X_SPI_ERASESIZE;
	rce = rtl819x_spi_mtd.erase(&rtl819x_spi_mtd, &ei);

	/* 🔴 THE EXPECTED ERRNO IS NOT unarmed_rc IN A WRITE IMAGE, and getting
	 * that wrong would have made this verb FAIL ON A CORRECT REFUSAL.  Both
	 * calls are at offset 0, which is inside the forbidden window, so the
	 * write TU refuses them FORBIDDEN (-EPERM) and never reaches the arming
	 * test -- which is exactly the ordering rtl819x-spi-wrpolicy.h is built
	 * around and the reason the forbidden check runs first.  So in a write
	 * image both answers are -EPERM and in a mainline image both are
	 * -EOPNOTSUPP; the conjunct asks that they AGREE with each other and
	 * with this build's own constant, never for a value typed elsewhere. */
	ok = (rcw == rce) &&
#ifdef CONFIG_MTD_RTL819X_WRITE
	     (rcw == -EPERM) &&
#else
	     (rcw == RTL819X_SPI_UNARMED_RC) &&
#endif
	     (rl == 0) &&
	     (ei.state == MTD_ERASE_FAILED) &&
	     (rtl819x_spi_n_write_refused == r0 + 2) &&
	     (rtl819x_spi_n_writes == w0) && (rtl819x_spi_n_writes == 0);

	rlxfw_markx("S-TRYW", (unsigned)ok);
	return ok ? 0 : -EPROTO;
}

#ifdef CONFIG_MTD_RTL819X_WRITE
/*
 * `arm <lo> <hi> <budget>`.  THREE numbers, all three REQUIRED, and parsed
 * with an end pointer like every other verb in this file -- simple_strtoul
 * with a NULL end returns 0 for a malformed field, and 0 is a legal address.
 *
 * 🔴 NO DEFAULTS.  An omitted field is -EINVAL and not a zero: `arm 20000`
 * must not arm [0x20000, 0) with budget 0, and it must not arm the whole chip
 * either.  The owner types all three or nothing is armed.
 *
 * 🔴 AND THE VERB IS NOT THE AUTHORISATION.  CLAUDE.md's dated `owner-yes` per
 * exact payload is; this is the mechanism that makes an UNDECLARED write
 * impossible rather than merely discouraged.  rlxfw_spi_wr_chk_arm() refuses a
 * window overlapping the loader or H601 here, and every use refuses it again,
 * so the forbidden rule lives in two independent places.
 */
static int rtl819x_spi_verb_arm(const char *arg)
{
	unsigned long v[3];
	char *end;
	const char *p = arg;
	int i;

	for (i = 0; i < 3; i++) {
		while (*p == ' ' || *p == '\t')
			p++;
		v[i] = simple_strtoul(p, &end, 0);
		if (end == p)
			return -EINVAL;
		p = end;
	}
	while (*p == ' ' || *p == '\t')
		p++;
	/* Trailing rubbish is refused rather than ignored: `arm 20000 30000 1000 0`
	 * is somebody's fourth idea about this interface and must not be read as
	 * the first three. */
	if (*p)
		return -EINVAL;
	return rtl819x_spi_wr_do_arm((u32)v[0], (u32)v[1], (u32)v[2]);
}

/* ========================================================================
 * R8b GAP A -- THE INSTALL PATH.  2026-10-05, 124th segment.
 * ========================================================================
 *
 * A payload is staged in RAM through /proc/rtl819x-spi-img (D12), then ONE
 * verb writes it to ONE region of a compiled-in table, commit-by-header:
 *
 *   cat <payload> > /proc/rtl819x-spi-img
 *   echo 'arm 0x70000 0x190000 0x120000' > /proc/rtl819x-spi
 *   echo 'install slotA sha=<64 hex>' > /proc/rtl819x-spi
 *
 * Every decision is in rtl819x-spi-install.h, which has no #include and is
 * compiled unchanged by tools/test-spi-install.c on the host; what is here
 * executes those decisions against the registers.  THE #includes BELOW ARE
 * MID-FILE ON PURPOSE: tracked documents cite this file by line (430, 1120,
 * 1216, 1919 and 2298 when this was written), and FW-110's rule is that an
 * insertion above a cited line moves it.  So the whole path sits below the
 * last cited line, and its two touch points above it -- one prototype, one
 * call in read_proc -- were made line-neutral.
 *
 * HOW A WRITE IS AUTHORISED (D6, D7) -- AND THE ARM IS SINGLE-USE.
 *  - The region comes from the table; no verb takes an address.
 *  - The arm in force -- a copy from the write TU's getter, taken under
 *    rtl819x_spi_lock (D20) -- must be exactly that region, with a budget
 *    of at least its size.  The copy is zeroed first, so a failed read is
 *    both an error (ARM_READ) and an unarmed copy.
 *  - The sha256 of the staged bytes, computed by the same
 *    crypto/sha256_generic.c that verify() uses and gated on the same boot
 *    KAT, must equal the typed digest.  The staged digest is never printed,
 *    so the device cannot be where a card copies the digest from.
 *  - The payload's own declaration must name this region: a container's
 *    signed flash_at and flash_form (WHOL); a cr6c's burnAddr, plus
 *    check_image()'s zero 16-bit sum.
 *  - 🔴 EVERY install/erase verb, whatever its outcome, a refusal included,
 *    ends DISARMED.  One arm, one attempt: a retry re-types both statements.
 *
 * WHY THE WRITES DO NOT GO THROUGH rtl819x_spi_write_page/_erase_sector.
 * Their budget is debited per operation and the arm verb caps it at hi-lo,
 * so an install -- erase S bytes, then program up to S more -- would spend
 * the whole budget in its erase phase.  Changing that is the write TU's
 * decision, not this path's.  So each operation here is checked by the SAME
 * policy functions (rtl819x-spi-wrpolicy.h: the forbidden window first, then
 * range, geometry and window) against a per-phase arm that is exactly the
 * region with a budget of its size, and is executed by the same two register
 * primitives above.  The forbidden-window rule thus runs on every operation,
 * beneath a region table that already keeps every address >= 0x010000.
 *
 * D11, FROM THE CODE.  Every erase is rtl819x_spi_se_block(): WREN, SE opcode
 * 0x20 (RTL819X_SPI_CMD_SE) with a 3-byte address, then the bounded WIP poll.
 * The step is RLXFW_SPI_WR_ERASE_GRAIN, 0x1000, which the policy's GEOM
 * conjunct refuses unless it equals rtl819x_spi_mtd.erasesize.  At either
 * candidate size the cleared range is exactly the region (argued at
 * rlxfw_spi_inst_op(), computed by the host test); at 65,536 each block is
 * erased sixteen times, which costs time and not correctness.
 *
 * D19, THE READING OF IT.  `eraseprobe`, under an arm equal to the probe
 * block (0x3E0000, 64 KiB), refuses unless the block reads erased, writes
 * three marker pages, issues ONE SE at the block base, and reads which
 * markers it cleared -- the verdict table is at rlxfw_spi_inst_probe_size().
 * It records that SE's and one page program's RDSR poll counts and ticks,
 * and the polls one tick holds when the part is idle (a read-only calibration
 * inside the usual claim/release), because the only clocksource here is
 * jiffies and a poll count is the finest reading this path can take.  It then
 * re-erases the block with the step its own verdict proves, and verifies.
 *
 * WHAT THIS DOES NOT ESTABLISH.  That any of it works on this die: no line
 * below has run anywhere.  That RTL819X_SPI_WIP_SPINS (推) outlasts an erase
 * of this part: if it does not, the install stops with ENGINE, n_wip_timeout
 * moves, and the region is left erased and invalid -- the safe failure, but
 * a failure.  That a container's signature is valid: D7's optional in-kernel
 * Ed25519 is NOT done, because src/rlxboot's verifier reaches this tree only
 * through a build-time staging step this path does not own.  rlxboot checks
 * the signature at boot, and that is the security boundary.
 */
#include <linux/vmalloc.h>
#include <linux/delay.h>
#include "rtl819x-spi-wrpolicy.h"
#include "rtl819x-spi-install.h"

/* D20.  The write TU's arm, copied out under rtl819x_spi_lock. */
extern int rtl819x_spi_wr_get_arm(struct rlxfw_spi_wr_arm *out);

#define RTL819X_SPI_IMG_PROC_NAME	"rtl819x-spi-img"

static u8 *rtl819x_spi_img;			/* vmalloc'd on the first append */
static struct rlxfw_spi_inst_img rtl819x_spi_img_st;
static struct rlxfw_spi_inst_st rtl819x_spi_inst_st;
static struct rlxfw_spi_inst_probe rtl819x_spi_probe_st;

/* Reason -> errno.  ENGINE is overridden by the primitive's own errno. */
static const int rtl819x_spi_inst_errno[RLXFW_SPI_INST_R_COUNT] = {
	0,		/* OK */
	-EINVAL,	/* SYNTAX */
	-EINVAL,	/* REGION */
	-EINVAL,	/* ERASE_ONLY */
	-EINVAL,	/* NOT_ERASABLE */
	-EPROTO,	/* ARM_READ */
	-EACCES,	/* UNARMED -- the write TU's own unarmed errno */
	-EPERM,		/* ARM_WINDOW */
	-ENOSPC,	/* ARM_BUDGET */
	-EIO,		/* IMG_BAD */
	-ENODATA,	/* IMG_EMPTY */
	-EFBIG,		/* IMG_SIZE */
	-EPERM,		/* KAT */
	-EIO,		/* HASH */
	-EBADMSG,	/* SHA */
	-ENOEXEC,	/* HDR_MAGIC */
	-ENOEXEC,	/* HDR_FORMAT */
	-ENOEXEC,	/* HDR_FLASH_AT */
	-ENOEXEC,	/* HDR_FORM */
	-ENOEXEC,	/* HDR_LEN */
	-ENOEXEC,	/* HDR_SUM */
	-EPERM,		/* POLICY */
	-ENOMEM,	/* NOMEM */
	-EIO,		/* ENGINE */
	-EIO,		/* CMP */
	-EINVAL,	/* PROBE_ONLY */
	-ENOTEMPTY,	/* PROBE_DIRTY -- refused, nothing written */
	-EIO,		/* PROBE_MARK */
	-EIO,		/* PROBE_ANOMALY -- measured, inconclusive */
	-EIO,		/* PROBE_UNCLEAN */
};

static int rtl819x_spi_inst_err(int reason)
{
	int e;

	if (reason == RLXFW_SPI_INST_OK)
		return 0;
	if (reason < 0 || reason >= RLXFW_SPI_INST_R_COUNT)
		return -EPROTO;
	e = rtl819x_spi_inst_errno[reason];
	return e ? e : -EPROTO;	/* a reason with no row never reads as 0 */
}

static void rtl819x_spi_inst_say_step(int ph, u32 blk, unsigned long t0)
{
	char b[RLXFW_SPI_INST_SAY_MAX];

	rlxfw_spi_inst_fmt_step(b, ph, blk, jiffies_to_msecs(jiffies - t0),
				rtl819x_spi_inst_st.r.pace_ms);
	rlxfw_puts(b);
}

/* ------------------------------------------------------------------------
 * D19: the erase-size probe.  Called with rtl819x_spi_lock held.
 * ------------------------------------------------------------------------ */

/* Read [base, base+size) and say whether every byte is 0xFF. */
static int rtl819x_spi_probe_read_ff(u32 base, u32 size, u8 *buf, int *all_ff)
{
	u32 off;
	int rc;

	*all_ff = 1;
	for (off = 0; off < size; off += RTL819X_SPI_CHUNK) {
		rc = rtl819x_spi_read_pio(base + off, RTL819X_SPI_CHUNK, buf);
		if (rc)
			return rc;
		if (rlxfw_spi_inst_probe_chk_erased(buf, RTL819X_SPI_CHUNK))
			*all_ff = 0;
		cond_resched();
	}
	return 0;
}

/* The idle RDSR polls that fit in RLXFW_SPI_INST_PROBE_CAL_TICKS ticks, from
 * a tick edge, inside the driver's own claim/release bracket.  READ-ONLY:
 * RDSR changes nothing on the part.  Both loops are bounded by
 * RTL819X_SPI_WIP_SPINS, so a stopped tick ends them with cal_ticks short of
 * its target instead of hanging -- the reading then says so itself. */
static int rtl819x_spi_probe_cal(struct rlxfw_spi_inst_probe *p)
{
	struct rtl819x_spi_state s;
	unsigned long j0;
	u32 n;
	int rc = 0, rc2;

	rc2 = rtl819x_spi_claim(&s);
	if (rc2)
		return rc2;
	j0 = jiffies;
	for (n = 0; jiffies == j0 && n < RTL819X_SPI_WIP_SPINS; n++) {
		rc = rtl819x_spi_wait_wip();
		if (rc)
			goto out;
	}
	j0 = jiffies;
	for (n = 0; jiffies - j0 < RLXFW_SPI_INST_PROBE_CAL_TICKS &&
		    n < RTL819X_SPI_WIP_SPINS; n++) {
		rc = rtl819x_spi_wait_wip();
		if (rc)
			goto out;
		cond_resched();
	}
	p->cal_polls = n;
	p->cal_ticks = (u32)(jiffies - j0);
out:
	rc2 = rtl819x_spi_release(&s);
	return rc ? rc : rc2;
}

/*
 * `eraseprobe`, steps (a)-(f) of D19.  Returns a reason; *wrote says whether
 * any program or erase was sent (a refusal sends none), *err the primitive's
 * errno when the reason is ENGINE.  Every write is checked by the same
 * policy functions the install path uses, against an arm equal to the block.
 */
static int rtl819x_spi_probe(const struct rlxfw_spi_inst_region *rg,
			     unsigned long t0, int *wrote, int *err)
{
	struct rlxfw_spi_inst_probe *p = &rtl819x_spi_probe_st;
	struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	struct rlxfw_spi_wr_arm arm_p, arm_e, arm_c;
	char say[RLXFW_SPI_INST_SAY_MAX];
	u8 mark[RLXFW_SPI_WR_PAGE];
	u8 *buf;
	unsigned long j0;
	u32 a, off;
	int k, ff, rc = 0, verified = 0, why = RLXFW_SPI_INST_OK;

	*wrote = 0;
	buf = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	if (!buf)
		return RLXFW_SPI_INST_R_NOMEM;

	/* (a) the block reads erased, or nothing is written at all */
	r->phase = 'R';
	rc = rtl819x_spi_probe_read_ff(rg->base, rg->size, buf, &ff);
	if (rc) {
		why = RLXFW_SPI_INST_R_ENGINE;
		goto out;
	}
	p->clean_known = 1;
	p->clean = ff;
	verified = 1;
	if (!ff) {
		why = RLXFW_SPI_INST_R_PROBE_DIRTY;
		goto out;
	}
	rc = rtl819x_spi_probe_cal(p);
	if (rc) {
		why = RLXFW_SPI_INST_R_ENGINE;
		goto out;
	}
	arm_p.armed = 1;
	arm_p.lo = rg->base;
	arm_p.hi = rg->base + rg->size;
	arm_p.budget = rg->size;
	arm_e = arm_p;
	arm_c = arm_p;
	rlxfw_spi_inst_fmt_go(say, r);
	rlxfw_puts(say);

	/* (b) a marker page at +0x0000, +0x1000, +0x8000, each read back */
	r->phase = 'M';
	verified = 0;
	rlxfw_spi_inst_probe_mark(mark);
	for (k = 0; k < RLXFW_SPI_INST_PROBE_NMARK; k++) {
		a = rg->base + rlxfw_spi_inst_probe_off[k];
		r->policy = rlxfw_spi_wr_chk_prog(&arm_p, a, RLXFW_SPI_WR_PAGE);
		if (r->policy) {
			why = RLXFW_SPI_INST_R_POLICY;
			goto out;
		}
		j0 = jiffies;
		rc = rtl819x_spi_pp_page(a, RLXFW_SPI_WR_PAGE, mark);
		if (k == 0) {
			p->pp_polls = (u32)rtl819x_spi_wip_polls;
			p->pp_jiffies = (u32)(jiffies - j0);
		}
		*wrote = 1;
		if (rc) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto out;
		}
		rtl819x_spi_note_write(0);
		arm_p.budget -= RLXFW_SPI_WR_PAGE;
		r->n_pp++;
		r->programmed += RLXFW_SPI_WR_PAGE;
		rc = rtl819x_spi_read_pio(a, RLXFW_SPI_WR_PAGE, buf);
		if (rc) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto out;
		}
		why = rlxfw_spi_inst_probe_chk_mark(buf);
		if (why)
			goto out;
	}

	/* (c) exactly ONE SE, at the block base, timed in polls and ticks */
	r->phase = 'E';
	r->policy = rlxfw_spi_wr_chk_erase(&arm_e, rg->base,
					   RLXFW_SPI_WR_ERASE_GRAIN,
					   RLXFW_SPI_WR_ERASE_GRAIN,
					   (u32)rtl819x_spi_mtd.erasesize);
	if (r->policy) {
		why = RLXFW_SPI_INST_R_POLICY;
		goto out;
	}
	j0 = jiffies;
	rc = rtl819x_spi_se_block(rg->base);
	p->se_polls = (u32)rtl819x_spi_wip_polls;
	p->se_jiffies = (u32)(jiffies - j0);
	p->se_issued = 1;
	if (rc) {
		why = RLXFW_SPI_INST_R_ENGINE;
		goto out;
	}
	rtl819x_spi_note_write(1);
	r->n_se++;

	/* (d) which of the three that one erase cleared */
	for (k = 0; k < RLXFW_SPI_INST_PROBE_NMARK; k++) {
		rc = rtl819x_spi_read_pio(rg->base + rlxfw_spi_inst_probe_off[k],
					  RLXFW_SPI_WR_PAGE, buf);
		if (rc) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto out;
		}
		p->m[k] = rlxfw_spi_inst_probe_state(buf);
	}
	p->se_bytes = rlxfw_spi_inst_probe_size(p->m[0], p->m[1], p->m[2]);
	p->classified = 1;
	rlxfw_spi_inst_fmt_probe(say, p);
	rlxfw_puts(say);

	/* (e) re-erase with the step the verdict proves, then verify */
	r->phase = 'C';
	p->clean_step = rlxfw_spi_inst_probe_clean_step(p->se_bytes);
	for (off = 0; p->clean_step && off < rg->size; off += p->clean_step) {
		r->policy = rlxfw_spi_wr_chk_erase(&arm_c, rg->base + off,
						   RLXFW_SPI_WR_ERASE_GRAIN,
						   RLXFW_SPI_WR_ERASE_GRAIN,
					(u32)rtl819x_spi_mtd.erasesize);
		if (r->policy) {
			why = RLXFW_SPI_INST_R_POLICY;
			goto out;
		}
		rc = rtl819x_spi_se_block(rg->base + off);
		if (rc) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto out;
		}
		rtl819x_spi_note_write(1);
		arm_c.budget -= RLXFW_SPI_WR_ERASE_GRAIN;
		p->clean_ops++;
		r->n_se++;
		cond_resched();
	}
	rtl819x_spi_inst_say_step('E', 0u, t0);
	r->phase = 'V';
	rc = rtl819x_spi_probe_read_ff(rg->base, rg->size, buf, &ff);
	if (rc) {
		why = RLXFW_SPI_INST_R_ENGINE;
		goto out;
	}
	p->clean = ff;
	verified = 1;
	rtl819x_spi_inst_say_step('V', 0u, t0);

	/* (f) the verdict: unclean outranks an inconclusive size */
	why = rlxfw_spi_inst_probe_verdict(p->se_bytes, p->clean);
	if (!why)
		r->phase = 'D';
out:
	/* A stop after a write and before the final read leaves the block in a
	 * state nobody read: clean is then unknown, never a stale 1. */
	if (!verified)
		p->clean_known = 0;
	kfree(buf);
	*err = rc;
	return why;
}

/* sha256 over the staged bytes, chunked so the scheduler runs between. */
static int rtl819x_spi_inst_sha(const u8 *p, u32 n, u8 *out)
{
	struct crypto_shash *tfm;
	struct shash_desc *d;
	u32 off, c;
	int rc = 0;

	tfm = crypto_alloc_shash("sha256", 0, 0);
	if (IS_ERR(tfm))
		return PTR_ERR(tfm);
	d = rtl819x_spi_desc(tfm);
	if (!d) {
		crypto_free_shash(tfm);
		return -ENOMEM;
	}
	for (off = 0; off < n && !rc; off += c) {
		c = n - off;
		if (c > RTL819X_SPI_CHUNK)
			c = RTL819X_SPI_CHUNK;
		rc = crypto_shash_update(d, p + off, c);
		cond_resched();
	}
	if (!rc)
		rc = crypto_shash_final(d, out);
	kfree(d);
	crypto_free_shash(tfm);
	return rc;
}

/*
 * One attempt.  Called with rtl819x_spi_lock held.  Everything before the
 * RLXFW-SI-GO line is a REFUSAL -- nothing has been sent to the chip --
 * and everything after it is a FAILURE, because a write may have happened.
 */
static int rtl819x_spi_inst_run(const char *line)
{
	struct rlxfw_spi_inst_st *s = &rtl819x_spi_inst_st;
	struct rlxfw_spi_inst_res *r = &s->r;
	const struct rlxfw_spi_inst_region *rg;
	struct rlxfw_spi_inst_req rq;
	struct rlxfw_spi_wr_arm arm, arm_e, arm_p;
	struct rlxfw_spi_inst_plan pl;
	struct rlxfw_spi_inst_opd op;
	char say[RLXFW_SPI_INST_SAY_MAX];
	unsigned long t0 = jiffies;
	u8 got[32];
	u8 *chunk = NULL;
	u32 i, nops, off;
	int why, rc = 0, wrote = 0;

	rlxfw_spi_inst_begin(s);
	why = rlxfw_spi_inst_parse(line, &rq);
	r->verb = rq.verb;
	r->region1 = rq.region + 1;
	r->pace_ms = rq.pace_ms;
	if (rq.verb == RLXFW_SPI_INST_V_PROBE)
		rlxfw_spi_inst_probe_begin(&rtl819x_spi_probe_st);
	if (why)
		goto refuse;
	rg = &rlxfw_spi_inst_regions[rq.region];
	r->base = rg->base;
	r->size = rg->size;

	/* D6: the two typed statements agree, or nothing happens.  D20: the
	 * copy is zeroed first, so even a getter that failed without saying
	 * so would hand back an UNARMED arm. */
	arm.armed = 0;
	arm.lo = arm.hi = arm.budget = 0u;
	if (rtl819x_spi_wr_get_arm(&arm))
		why = RLXFW_SPI_INST_R_ARM_READ;
	else
		why = rlxfw_spi_inst_chk_arm(&arm, rg);
	if (why)
		goto refuse;
	r->arm_ok = 1;

	if (rq.verb == RLXFW_SPI_INST_V_PROBE) {
		why = rtl819x_spi_probe(rg, t0, &wrote, &rc);
		if (why == RLXFW_SPI_INST_OK) {
			s->done++;
			goto out;
		}
		if (wrote)
			goto fail;
		goto refuse;
	}

	if (rq.verb == RLXFW_SPI_INST_V_INSTALL) {
		why = rlxfw_spi_inst_chk_img(&rtl819x_spi_img_st, rg);
		if (!why && !rtl819x_spi_img)
			why = RLXFW_SPI_INST_R_IMG_EMPTY;
		if (why)
			goto refuse;
		r->len = rtl819x_spi_img_st.len;
		/* D7: the owner's yes is for THESE bytes. */
		if (rtl819x_spi_kat_rc) {
			why = RLXFW_SPI_INST_R_KAT;
			goto refuse;
		}
		rc = rtl819x_spi_inst_sha(rtl819x_spi_img, r->len, got);
		if (rc) {
			why = RLXFW_SPI_INST_R_HASH;
			goto refuse;
		}
		r->sha_checked = 1;
		r->sha_ok = rlxfw_spi_inst_digest_eq(got, rq.sha);
		if (!r->sha_ok) {
			why = RLXFW_SPI_INST_R_SHA;
			goto refuse;
		}
		why = rlxfw_spi_inst_chk_payload(rtl819x_spi_img, r->len, rg);
		r->hdr_checked = 1;
		r->hdr_ok = !why;
		if (why)
			goto refuse;
	}

	why = rlxfw_spi_inst_plan_init(&pl, rg, r->len,
				       RLXFW_SPI_WR_ERASE_GRAIN);
	if (why)
		goto refuse;
	nops = rlxfw_spi_inst_nops(&pl);
	r->ops_planned = nops;
	chunk = kmalloc(RTL819X_SPI_CHUNK, GFP_KERNEL);
	if (!chunk) {
		why = RLXFW_SPI_INST_R_NOMEM;
		goto refuse;
	}
	arm_e.armed = 1;
	arm_e.lo = rg->base;
	arm_e.hi = rg->base + rg->size;
	arm_e.budget = rg->size;
	arm_p = arm_e;

	rlxfw_spi_inst_fmt_go(say, r);
	rlxfw_puts(say);
	/* D5: erase all (first block first), program pages 1.., page 0 last. */
	for (i = 0; i < nops; i++) {
		if (rlxfw_spi_inst_op(&pl, i, &op) == RLXFW_SPI_INST_OP_ERASE) {
			r->phase = 'E';
			r->policy = rlxfw_spi_wr_chk_erase(&arm_e, op.addr,
					op.len, RLXFW_SPI_WR_ERASE_GRAIN,
					(u32)rtl819x_spi_mtd.erasesize);
			if (r->policy) {
				why = RLXFW_SPI_INST_R_POLICY;
				goto fail;
			}
			rc = rtl819x_spi_se_block(op.addr);
			if (rc) {
				why = RLXFW_SPI_INST_R_ENGINE;
				goto fail;
			}
			rtl819x_spi_note_write(1);
			arm_e.budget -= op.len;
			r->n_se++;
			r->erased += op.len;
		} else if (op.kind == RLXFW_SPI_INST_OP_PROG) {
			r->phase = op.commit ? 'H' : 'P';
			r->policy = rlxfw_spi_wr_chk_prog(&arm_p, op.addr,
							  op.len);
			if (r->policy) {
				why = RLXFW_SPI_INST_R_POLICY;
				goto fail;
			}
			rc = rtl819x_spi_pp_page(op.addr, op.len,
						 rtl819x_spi_img + op.off);
			if (rc) {
				why = RLXFW_SPI_INST_R_ENGINE;
				goto fail;
			}
			rtl819x_spi_note_write(0);
			arm_p.budget -= op.len;
			r->n_pp++;
			r->programmed += op.len;
			r->committed = op.commit;
		} else {
			why = RLXFW_SPI_INST_R_POLICY;	/* plan ended early */
			goto fail;
		}
		r->ops_done++;
		if (op.blk_end) {
			rtl819x_spi_inst_say_step(r->phase, op.blk, t0);
			/* D10: the pause a human pull lands in */
			if (r->pace_ms && !op.commit)
				msleep(r->pace_ms);
		}
		cond_resched();
	}

	/* D5's read-back over the WHOLE region: staged bytes, then 0xFF. */
	r->phase = 'V';
	r->cmp_ran = 1;
	for (off = 0; off < rg->size; off += RTL819X_SPI_CHUNK) {
		rc = rtl819x_spi_read_pio(rg->base + off, RTL819X_SPI_CHUNK,
					  chunk);
		if (rc) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto fail;
		}
		rlxfw_spi_inst_cmp(chunk, off, RTL819X_SPI_CHUNK,
				   rtl819x_spi_img, r->len, &r->cmp_diff,
				   &r->cmp_first);
		r->cmp_bytes += RTL819X_SPI_CHUNK;
		if ((off + RTL819X_SPI_CHUNK) % RLXFW_SPI_INST_BLOCK == 0u)
			rtl819x_spi_inst_say_step('V',
					off / RLXFW_SPI_INST_BLOCK, t0);
		cond_resched();
	}
	if (r->cmp_diff) {
		why = RLXFW_SPI_INST_R_CMP;
		goto fail;
	}
	r->cmp_ok = 1;
	r->phase = 'D';
	s->done++;
	why = RLXFW_SPI_INST_OK;
	goto out;
refuse:
	s->refused++;
	goto out;
fail:
	s->failed++;
out:
	kfree(chunk);
	r->reason = why;
	r->rc = (why == RLXFW_SPI_INST_R_ENGINE && rc) ? rc :
		rtl819x_spi_inst_err(why);
	r->ms = jiffies_to_msecs(jiffies - t0);
	rlxfw_spi_inst_fmt_end(say, r);
	rlxfw_puts(say);
	return r->rc;
}

/* `install ...` and `erase ...`.  The whole line goes to the parser, so a
 * malformed one is still an attempt -- and still disarms. */
static int rtl819x_spi_verb_inst(const char *line)
{
	int rc;

	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_inst_run(line);
	/* ONE ARM, ONE ATTEMPT: refused, failed or done, the write path
	 * leaves this verb disarmed. */
	rtl819x_spi_wr_do_disarm();
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_markx("SI-RC", (unsigned)rc);
	return rc;
}

/* `img reset`: forget the staged bytes and any latched error. */
static int rtl819x_spi_verb_img_reset(void)
{
	mutex_lock(&rtl819x_spi_lock);
	vfree(rtl819x_spi_img);			/* NULL is a no-op */
	rtl819x_spi_img = NULL;
	rlxfw_spi_inst_img_reset(&rtl819x_spi_img_st);
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_mark("SI-IMGRESET");
	return 0;
}

/* /proc/rtl819x-spi-img.  Appends; refuses an overflow WHOLE with EFBIG and
 * poisons the buffer (EIO on every later append) until `img reset`.  Under
 * rtl819x_spi_lock, so an append cannot land in the middle of an install. */
static int rtl819x_spi_img_write_proc(struct file *file,
				      const char __user *buffer,
				      unsigned long count, void *data)
{
	struct rlxfw_spi_inst_img *im = &rtl819x_spi_img_st;
	int rc;

	mutex_lock(&rtl819x_spi_lock);
	switch (rlxfw_spi_inst_img_admit(im, count)) {
	case RLXFW_SPI_INST_IMG_OK:
		break;
	case RLXFW_SPI_INST_IMG_OVERFLOW:
		rc = -EFBIG;
		goto out;
	default:
		rc = -EIO;
		goto out;
	}
	if (!count) {
		rc = 0;
		goto out;
	}
	if (!rtl819x_spi_img) {
		rtl819x_spi_img = vmalloc(RLXFW_SPI_INST_IMG_CAP);
		if (!rtl819x_spi_img) {
			im->err = RLXFW_SPI_INST_IMG_NOMEM;
			rc = -ENOMEM;
			goto out;
		}
	}
	if (copy_from_user(rtl819x_spi_img + im->len, buffer, count)) {
		im->err = RLXFW_SPI_INST_IMG_FAULT;
		rc = -EFAULT;
		goto out;
	}
	im->len += (u32)count;
	im->writes++;
	rc = (int)count;
out:
	mutex_unlock(&rtl819x_spi_lock);
	return rc;
}

/* The /proc block, behind its own budget check like the write TU's. */
static int rtl819x_spi_inst_proc(char *page, int used)
{
	int len = 0;

	if (used + RLXFW_SPI_INST_PROC_MAX <= RTL819X_SPI_PROC_BUDGET) {
		len += rlxfw_spi_inst_emit(page, &rtl819x_spi_inst_st,
					   &rtl819x_spi_img_st,
					   &rtl819x_spi_probe_st,
					   RTL819X_SPI_CMD_SE,
					   RLXFW_SPI_WR_ERASE_GRAIN,
					   jiffies_to_usecs(1));
		len += sprintf(page + len, "inst_truncated 0\n");
	} else {
		len += sprintf(page + len, "inst_truncated 1\n");
	}
	return len;
}
/* END OF R8b GAP A.  tools/test-spi-install.sh compiles the lines from the
 * banner above to this one on the host, against a simulated chip. */
#endif

/* `<n>` or `<n> <off>`.  Two numbers, parsed with an END POINTER rather than
 * by splitting on a space, because simple_strtoul with a NULL end silently
 * returns 0 for a malformed second field and 0 is a legal offset. */
static int rtl819x_spi_verb_verify(const char *arg)
{
	unsigned long len = 0, start = 0;
	char *end;
	int rc;

	if (*arg) {
		len = simple_strtoul(arg, &end, 0);
		while (*end == ' ' || *end == '\t')
			end++;
		if (*end) {
			char *end2;
			start = simple_strtoul(end, &end2, 0);
			if (end2 == end)
				return -EINVAL;
		}
	}
	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_verify((u32)start, (u32)len);
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_markx("S-VRC", (unsigned)rc);
	rlxfw_markx("S-VDIFF", (unsigned)rtl819x_spi_v_diff_bytes);
	rlxfw_markx("S-VD1", (unsigned)rtl819x_spi_v_d1_match);
	return rc;
}

/* `map <level>` or `map <level> <group>`. */
static int rtl819x_spi_verb_map(const char *arg)
{
	unsigned long level, group = 0;
	char *end;
	int rc;

	level = simple_strtoul(arg, &end, 0);
	if (end == arg)
		return -EINVAL;
	while (*end == ' ' || *end == '\t')
		end++;
	if (*end) {
		char *end2;
		group = simple_strtoul(end, &end2, 0);
		if (end2 == end)
			return -EINVAL;
	}
	mutex_lock(&rtl819x_spi_lock);
	rc = rtl819x_spi_map((int)level, (u32)group);
	mutex_unlock(&rtl819x_spi_lock);
	rlxfw_markx("S-MRC", (unsigned)rc);
	rlxfw_markx("S-MDIFF", (unsigned)rtl819x_spi_map_diff_units);
	rlxfw_markx("S-MH601", (unsigned)rtl819x_spi_map_h601_hashed);
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
#ifdef CONFIG_MTD_RTL819X_WRITE
	/* R8b Gap A: `install` carries 64 hex digits, so a line outgrows 31
	 * bytes -- and an over-long line is REFUSED rather than cut, because a
	 * cut install line must never parse as a shorter, different one. */
	char buf[RLXFW_SPI_INST_LINE_MAX];
#else
	char buf[32];
#endif
	unsigned long n = count;
	int ret;

#ifdef CONFIG_MTD_RTL819X_WRITE
	if (n >= sizeof(buf))
		return -EINVAL;
#endif
	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "probe"))
		ret = rtl819x_spi_verb_probe();
	else if (!strcmp(buf, "rdid"))
		ret = rtl819x_spi_verb_rdid();
	else if (!strcmp(buf, "h601"))
		ret = rtl819x_spi_verb_h601();
	else if (!strcmp(buf, "wedge"))
		ret = rtl819x_spi_verb_wedge();
	else if (!strcmp(buf, "unwedge")) {
		rtl819x_spi_wedged = 0;
		ret = 0;
	} else if (!strcmp(buf, "trywrite"))
		ret = rtl819x_spi_verb_trywrite();
#ifdef CONFIG_MTD_RTL819X_WRITE
	/* arm and disarm take the lock since Gap A, so neither can land inside
	 * an install, which holds it from its arm check to its disarm. */
	else if (!strncmp(buf, "arm ", 4)) {
		mutex_lock(&rtl819x_spi_lock);
		ret = rtl819x_spi_verb_arm(buf + 4);
		mutex_unlock(&rtl819x_spi_lock);
	} else if (!strcmp(buf, "disarm")) {
		mutex_lock(&rtl819x_spi_lock);
		rtl819x_spi_wr_do_disarm();
		mutex_unlock(&rtl819x_spi_lock);
		ret = 0;
	} else if (!strncmp(buf, "install", 7) || !strncmp(buf, "erase", 5))
		ret = rtl819x_spi_verb_inst(buf);
	else if (!strcmp(buf, "img reset"))
		ret = rtl819x_spi_verb_img_reset();
#endif
	else if (!strcmp(buf, "verify"))
		ret = rtl819x_spi_verb_verify("");
	else if (!strncmp(buf, "verify ", 7))
		ret = rtl819x_spi_verb_verify(buf + 7);
	else if (!strncmp(buf, "corrupt ", 8))
		ret = rtl819x_spi_verb_corrupt(buf + 8);
	else if (!strncmp(buf, "map ", 4))
		ret = rtl819x_spi_verb_map(buf + 4);
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

	/* 0444: every verb stays on the first file.  A second writable entry
	 * would be a second way to reach the controller, and this driver's
	 * whole L2 argument is that nothing issues a transaction except
	 * through one of the verbs. */
	pde = create_proc_entry(RTL819X_SPI_MAP_PROC_NAME, 0444, NULL);
	if (!pde) {
		rlxfw_mark("S8-NOMAP");
		return 0;
	}
	pde->read_proc = rtl819x_spi_map_read_proc;
	rlxfw_mark("S8");

#ifdef CONFIG_MTD_RTL819X_WRITE
	/* R8b Gap A, D12.  A SECOND WRITABLE ENTRY, which the 0444 paragraph
	 * above argues against -- and its argument does not reach this one:
	 * it issues no transaction.  It appends bytes to a RAM buffer under
	 * rtl819x_spi_lock and does nothing else; every flash operation is
	 * still one verb on the first file.  0200 and no read_proc, so a read
	 * returns end-of-file. */
	pde = create_proc_entry(RTL819X_SPI_IMG_PROC_NAME, 0200, NULL);
	if (!pde) {
		rlxfw_mark("S9-NOIMG");
		return 0;
	}
	pde->write_proc = rtl819x_spi_img_write_proc;
	rlxfw_mark("S9");
#endif
	return 0;
}

late_initcall(rtl819x_spi_init);
