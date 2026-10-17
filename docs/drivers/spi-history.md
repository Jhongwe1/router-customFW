# `rtl819x-spi.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c)
until 2026-10-18 — lines 1–313 at commit `6a964e85` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [spi](spi.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-spi.c` counts the file's lines at `6a964e85`.

```c
/*
 * rtl819x-spi -- a READ-ONLY MTD device on the RTL8196E's SPI flash
 * controller, driven by PROGRAMMED I/O through SFCSR/SFDR.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-5, 2026-09-07, forty-first segment.  It is
 * staged into drivers/mtd/devices/ by tools/rlxfw-marks.py from
 * kernel/; config/rlxfw-marks.tsv carries the two Kbuild lines --
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
```
