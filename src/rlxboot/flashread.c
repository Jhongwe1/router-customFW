/* src/rlxboot/flashread.c -- the anti-rollback counter's sources.
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
 * D21 (2026-10-05): A FLASH-RESIDENT IMAGE HAS ONE SOURCE, THE FLASH BITMAP.
 * R8a's bench needed the RAM-staged bitmap at 0x81700000 to drive a rollback
 * case without a flash write.  A resident image does not, and there it is a
 * liability: `MEM-17`, DRAM survives a power cycle, so a stale or planted
 * "RCNT" block would set the floor -- lower than flash's, letting a rollback
 * through, or higher, refusing both slots.  So in BOOT=slots the RAM source
 * is NOT COMPILED: `rlxb_counter_read` never reads its `ram` argument and the
 * device wrapper never forms the address.  The Makefile's payload gate reads
 * the disassembly and refuses a slots image that forms 0x81700000 at all, with
 * the RAM image as the control that the census can see it.  BOOT=ram keeps
 * R8a's order and R8a's accesses: the magic as one word through KSEG0, the
 * bitmap as bytes, flash only when the magic does not read "RCNT".
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
 * the control: the control is the RAM source, and test (3) is driven from RAM
 * -- in BOOT=ram, the only build that still has one.
 */

#include "rlxboot.h"
#include "container.h"

#ifndef RLXBOOT_SLOTS
#error "RLXBOOT_SLOTS must be 0 (BOOT=ram) or 1 (BOOT=slots); the Makefile sets it"
#endif

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

/* The two sources as pointers, so the host suites drive this same code:
 * `t_container` links it built BOOT=ram, `t_slots` built BOOT=slots. */
int rlxb_counter_read(unsigned char *out, const volatile unsigned int *ram,
                      const volatile unsigned char *flash)
{
	unsigned long i;

#if RLXBOOT_SLOTS /* D21: no RAM source */
	(void)ram;
#else
	/* The RAM source first, because it is the one a card can stage and
	 * therefore the one test (3) runs on.  Read through KSEG0, the same way
	 * the loader's TFTP wrote it: the D side is write-back, so a KSEG1 read
	 * of a line the loader left dirty would see stale DRAM.  (Write-allocate
	 * is absent on this core, so a store to a line that was not resident goes
	 * straight to memory and both reads would agree -- but "both agree" is an
	 * argument about a cache nobody has measured writing back here, and the
	 * cached read is correct either way.) */
	if (ram[0] == RLXU_CTR_RAM_MAGIC) {
		const volatile unsigned char *src =
			(const volatile unsigned char *)(ram + 1);

		for (i = 0; i < RLXU_CTR_BYTES; i++)
			out[i] = src[i];
		return 1;
	}
#endif

	/* The flash window.  KSEG1 by construction: RLXB_FLASH_WIN is 0xBD......
	 * `volatile`, and byte loads, because a compiler that decided this loop
	 * was a `memcpy` from constant memory would be within its rights and the
	 * result would not be a device reading. */
	for (i = 0; i < RLXU_CTR_BYTES; i++)
		out[i] = flash[i];
	return 0;
}

int rlxboot_read_counter_bitmap(unsigned char *out)
{
	return rlxb_counter_read(out,
#if RLXBOOT_SLOTS /* D21: no RAM address is formed in this image */
	                         0,
#else
	                         (const volatile unsigned int *)RLXB_CTR_RAM,
#endif
	                         (const volatile unsigned char *)
	                         (RLXB_FLASH_WIN + RLXB_CTR_FLASH));
}
