/* src/rlxboot/flashread.c -- the anti-rollback counter's two sources.
 * rlxfw's own code.
 *
 * READ ONLY, AND THAT IS A CLAIM A READER CAN CHECK FROM THE BINARY.
 *
 * On this part the memory-mapped window at 0xBD000000 cannot program or erase
 * anything: `docs/loader-flash-write.md` records that on this controller a
 * command is issued by WRITING `SFDR`, so a store into the window is not a
 * transaction, and every program and erase in the vendor's own code goes
 * through the controller registers at 0xB8001200.. .  So "rlxboot has no write
 * path" reduces to "rlxboot never addresses 0xB80012xx", which is a property of
 * the emitted instruction stream and not of this comment.
 * `src/rlxboot/test/flashsafe.sh` reads the disassembly of the linked payload,
 * refuses if any `lui`/`ori` pair or any load or store displacement forms an
 * address in [0xB8001200, 0xB8001300), and has a negative control that plants
 * such a store and must be caught.  It also prints the `lui` census so the
 * reader sees what addresses the image does form.
 *
 * ⚠️ WHAT THIS FILE DOES NOT ESTABLISH.  That the window is live at the loader
 * prompt is 量 (`SPEC.md` `FLS-11`, probe3 Group F, 1,024 uncached loads, R =
 * 1.0000 at two strides with three refutation controls) -- but that reading was
 * at 0xBD000000 and this one is at 0xBD3F0000, 4,128,768 bytes further in, and
 * nothing in this project has read THAT address through THIS window at the
 * prompt.  The decode size of the window is measured nowhere
 * (`tools/rlxprobe/rlxdefs.h` bounds every Group F leg to 64 KiB for exactly
 * that reason).  So the flash source is 推 until a seating reads it, and the
 * instrument that settles it is the card cell that prints
 * `RLXBOOT-CTRSRC flash` with `RLXBOOT-VER ctr=0`: an erased region reads 0,
 * and a window that is not decoded reads 0xFFFFFFFF-ish garbage -- which ALSO
 * gives ctr=0, because 0xFF bytes are what an erased region looks like.  THE
 * TWO ARE NOT DISTINGUISHABLE BY THE COUNTER, which is why the counter is not
 * the control: the control is the RAM source, and test (3) is driven from RAM.
 */

#include "rlxboot.h"
#include "container.h"

/* The counter's own window must not touch the two regions a mistake in it
 * could not be undone.  A compile-time refusal, because a run-time one would be
 * code that has to be reached to matter.  gcc 3.4.6 has no `_Static_assert`, so
 * this is the negative-array-size idiom. */
typedef char rlxboot_ctr_not_in_loader[
	(RLXB_CTR_FLASH >= 0x006000UL && RLXB_CTR_FLASH < 0x008000UL) ? -1 : 1];
typedef char rlxboot_ctr_not_in_h601[
	(RLXB_CTR_FLASH < 0x006000UL) ? -1 : 1];
typedef char rlxboot_ctr_fits[
	(RLXB_CTR_FLASH + RLXU_CTR_BYTES <= 0x400000UL) ? 1 : -1];

int rlxboot_read_counter_bitmap(unsigned char *out)
{
	volatile const unsigned long *ram = (volatile const unsigned long *)RLXB_CTR_RAM;
	volatile const unsigned char *src;
	unsigned long i;

	/* The RAM source first, because it is the one a card can stage and
	 * therefore the one test (3) runs on.  Read through KSEG0, the same way
	 * the loader's TFTP wrote it: the D side is write-back, so a KSEG1 read
	 * of a line the loader left dirty would see stale DRAM.  (Write-allocate
	 * is absent on this core, so a store to a line that was not resident goes
	 * straight to memory and both reads would agree -- but "both agree" is an
	 * argument about a cache nobody has measured writing back here, and the
	 * cached read is correct either way.) */
	if (ram[0] == RLXU_CTR_RAM_MAGIC) {
		src = (volatile const unsigned char *)(RLXB_CTR_RAM + 4);
		for (i = 0; i < RLXU_CTR_BYTES; i++)
			out[i] = src[i];
		return 1;
	}

	/* The flash window.  KSEG1 by construction: RLXB_FLASH_WIN is 0xBD......
	 * `volatile`, and byte loads, because a compiler that decided this loop
	 * was a `memcpy` from constant memory would be within its rights and the
	 * result would not be a device reading. */
	src = (volatile const unsigned char *)(RLXB_FLASH_WIN + RLXB_CTR_FLASH);
	for (i = 0; i < RLXU_CTR_BYTES; i++)
		out[i] = src[i];
	return 0;
}
