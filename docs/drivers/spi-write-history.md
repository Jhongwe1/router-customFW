# `rtl819x-spi-write.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-write.c`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-write.c)
until 2026-10-18 — lines 1–154 at commit `d067e692` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [spi](spi.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-spi-write.c` counts the file's lines at `d067e692`.

```c
/*
 * rtl819x-spi-write -- this driver's flash WRITE path: the policy, the
 * counters and the two MTD-shaped entry points.  Declared to kconfig as of
 * R8b item 4 and still OFF in every committed image.
 *
 * THIS FILE IS NOT REALTEK'S.  R5-5, 2026-09-07, forty-first segment (the
 * refusing stubs); rewritten R8b item 4, 2026-10-04, 122nd segment.
 *
 * ------------------------------------------------------------------------
 * WHAT CHANGED, AND THE ONE SENTENCE THAT HAS NOT
 * ------------------------------------------------------------------------
 *
 * Until this segment this file held two bodies returning -EPERM and a comment
 * saying what a real implementation would be.  It now holds the real one.
 * 🔴 WHAT HAS NOT CHANGED: **not one line of it has run anywhere.**  It is not
 * in any committed image, it has never been on this die, and the only thing
 * exercised at the desk is its refusals, on the host, through
 * tools/test-spi-wrpolicy.sh.  Every paragraph below that reads like a
 * statement about the silicon is 讀 or 推 and is marked.
 *
 * ------------------------------------------------------------------------
 * THE FOUR BUILD-TIME DECISIONS R8b ITEM 4 ASKED FOR, AND WHERE EACH LIVES
 * ------------------------------------------------------------------------
 *
 *  W1  CONFIG_MTD_RTL819X_WRITE is DECLARED to kconfig, `bool`, `default n`,
 *      by config/host-compat/0010.  Before this segment it was declared
 *      nowhere, which made `obj-$(CONFIG_MTD_RTL819X_WRITE)` expand to empty
 *      in GNU Make and left a make-command-line override in a discarded tree
 *      as the only way to build this file.  An override leaves no trace in
 *      .config, so tools/kconfig-delta.py could not see it -- the opposite of
 *      what this project wants of a decision this size.  Declaring it makes
 *      the switch a reviewed line in config/rlxfw-kernel.delta.
 *  W2  That line's VALUE is `n`, and it is `n` on the mainline.  CLAUDE.md:
 *      *a write needs my explicit yes* -- which is not conditional on R9, and
 *      the conditional half of that rule (*mainline is zero-write through R9*)
 *      stopped biting the moment R9 closed, so it is deliberately NOT quoted
 *      here as the reason.  A compiled write path is not a write, but it is
 *      one `echo` away from one.  The BINDING reason is the one in
 *      config/rlxfw-marks.tsv's MK5 block: 讀 tools/rlxfw-marks.py, a
 *      conditional Kbuild row must carry an `absent:` witness, so an image
 *      built at `y` makes MK5 go red and it cannot be re-witnessed without
 *      either retiring D4's build-time layer or relaxing that pairing rule --
 *      a choice about a containment check, and therefore the owner's.
 *      So this TU is still not compiled into anything, and `rlxfw-marks
 *      verify`'s `absent:rtl819x_spi_write_page` witness on MK5 is still the
 *      instrument that says so.  Flipping it to `y` is one field of one row,
 *      and notes/spi-mtd-driver.md § 12.2 names what goes red when it does.
 *  W3  The page-program and sector-erase sequences are implemented, in
 *      rtl819x-spi.c beside the controller guard that already owns SFCR/
 *      SFCR2/SFCSR, and reached from here.  See THE SPLIT below.
 *  W4  mtd->flags stays MTD_CAP_ROM.  The write path is reachable only
 *      through this driver's own /proc verb, never through mtdchar or
 *      mtdblock.  rtl819x-spi.c's mtd_info comment carries the reason.
 *
 * ------------------------------------------------------------------------
 * THE SPLIT: POLICY HERE, REGISTERS THERE, AND WHY NOT THE OTHER WAY ROUND
 * ------------------------------------------------------------------------
 *
 * rtl819x-spi.c's claim()/release() pair is the only thing in this project
 * that saves SFCR/SFCR2/SFCSR, restores them, reads them back and latches
 * `wedged` when the restore did not take -- and SFDR is deliberately NOT
 * restored, because writing it ISSUES a command.  A second copy of that guard
 * in this file would be a second owner of the one invariant that keeps this
 * driver survivable beside the vendor's.  So:
 *
 *   here       the forbidden-window test, the arming state, the alignment and
 *              page geometry, the per-reason counters, the MTD signatures
 *   there      rtl819x_spi_pp_page() and rtl819x_spi_se_block(), two
 *              register-level primitives inside the existing claim/release
 *              bracket, compiled only under the same CONFIG_
 *
 * and the arithmetic in rtl819x-spi-wrpolicy.h is in a header with no
 * #include so the host test runs the same code the board would.
 *
 * ------------------------------------------------------------------------
 * ARMING, AND WHY A COMPILE-TIME SWITCH IS NOT ENOUGH
 * ------------------------------------------------------------------------
 *
 * W2 keeps the code out of the image.  But the image R8b's seating needs has
 * W2 flipped, and in THAT image a compile-time switch protects nothing: every
 * boot would carry a live page-program reachable from /proc.  So the engine
 * refuses unless ARMED, and an arm is:
 *
 *   echo 'arm <lo> <hi> <budget>' > /proc/rtl819x-spi
 *
 * with a window, a byte budget that each accepted operation debits, and
 * automatic disarm when the budget reaches 0.  The arm verb refuses a window
 * overlapping the forbidden one, which makes the forbidden refusal exist in
 * two independent places rather than one.
 *
 * 🔴 WHAT ARMING IS NOT.  It is not a security boundary -- root can type the
 * verb, and this board's only user is root.  It is a containment rule for the
 * failure this project actually has: a stray write, a wrong card cell, a
 * payload whose destination nobody declared.  CLAUDE.md's dated `owner-yes`
 * per payload is the authorisation; this is the mechanism that makes an
 * undeclared write impossible rather than merely discouraged.
 *
 * ------------------------------------------------------------------------
 * THE COUNTERS, AND WHAT EACH ZERO WOULD AND WOULD NOT MEAN
 * ------------------------------------------------------------------------
 *
 *   n_prog, n_erase     operations the engine ACCEPTED and ran.  Both feed
 *                       rtl819x-spi.c's n_writes, which is the number
 *                       CLAUDE.md § Flash quotes.
 *   n_refused[reason]   one counter per refusal reason.  A zero in any of
 *                       them is a claim, and the host test is what makes the
 *                       claim falsifiable at the desk: it drives every
 *                       reason to fire at least once.
 *   n_engine_fail       the engine returned an error after the policy had
 *                       passed -- a bounded RDY spin that timed out, a
 *                       restore that did not take, a WIP that never cleared.
 *                       This is the only counter that can move without any
 *                       decision of this file's being wrong.
 *
 * 🔴 n_writes IS BLIND TO A VENDOR-SIDE WRITE, and this file must not be read
 * as saying otherwise.  量 2026-09-07 and unchanged: CONFIG_RTL819X_SPI_FLASH=y,
 * spi_probe.c:101-103 installs mtd->write = mtd_spi_write and mtd->erase =
 * mtd_spi_erase on the vendor's partitions UNCONDITIONALLY, and those reach
 * PageWrite_111002 / ComSrlCmd_SE -- real page-program and sector-erase on the
 * same four registers.  Nothing here counts them.  What keeps them out of
 * reach is the userspace surface: /dev/mtd0ro is an odd minor, which mtdchar
 * refuses to open for writing, and /dev/mtdblock1 is 0400 in
 * config/rlxfw-initramfs.tsv.  Those are access controls on a path that
 * exists.  So the accurate sentence stays: **rlxfw's n_writes counts rlxfw's
 * writes**, and SPEC.md FLS-26 already proved "not one flash byte is written"
 * false for this device.
 *
 * ------------------------------------------------------------------------
 * THE SEQUENCES, 讀, AND WHOSE THEY ARE
 * ------------------------------------------------------------------------
 *
 * Both are the vendor's order, read out of
 * src-vendor/rtl819x-toolchain/linux-2.6.30/drivers/mtd/chips/rtl819x/
 * spi_common.c in the tree that builds.  docs/blind-write-ledger.md § 9.14
 * records the paths and their depth; this is NOT a blind write and its diff is
 * not called one.
 *
 *   erase a block    SeqCmd_Order(WREN 0x06)                       :821
 *                    SeqCmd_Write(SE 0x20, addr, 3 bytes)          :822
 *                    spiFlashReady() -- poll RDSR 0x05 bit 0 (WIP) :728-742
 *   program a page   SeqCmd_Order(WREN 0x06)                       :969
 *                    ComSrlCmd_InputCommand(PP 0x02, addr, dummy 0):971
 *                    the data in 4-byte SFDR phases                :973-979
 *                    a short tail phase with LEN = i-1             :982-988
 *                    spiFlashReady()                               :990
 *
 * 🟢 WHAT IS THIS FILE's OWN, and what docs/driver-diff.md scores: the
 * forbidden window (the vendor has none -- spi_cmd.c:46-53 is `#if 0`); the
 * refusal of a non-grain-multiple erase length where the vendor ROUNDS IT UP
 * (spi_cmd.c:71-78); the BOUNDED WIP poll, where the vendor's spiFlashReady()
 * is `while (1)` with no ceiling and no counter, so a part that never clears
 * WIP reboots the router through the watchdog; the arming state; and the
 * per-reason counters.
 */
```
