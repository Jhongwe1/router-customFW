/* rlxboot.lds -- rlxboot's link map.
 *
 * Modelled on `tools/rlxprobe/rlxprobe.lds`, and the one structural thing that
 * is copied rather than simplified is the TWO PT_LOADs: `tools/hazlint` takes
 * its scan range from the EXECUTABLE program headers, so a `.rodata` sharing a
 * segment with `.text` hands every banner string and every SHA-256 constant to
 * the instruction decoder as code.  This payload has 640 bytes of K[64] and
 * 640 of K[80] in `.rodata`; misplacing them would produce a page of
 * false-positive hazards in a table of hash constants.
 *
 * LOAD_ADDR and STACK_SIZE arrive on the link line with --defsym.  The default
 * in the Makefile is 0x81800000, which is SPEC-R8a.md s4's pinned address for
 * rlxboot -- NOT rlxprobe's 0x80500000, which is where the payload rlxboot
 * boots is staged.
 *
 * `_rlxboot_start` and `_stack_top` are what `main.c` derives its own
 * self-range from, so the destination check refuses a container that would land
 * on rlxboot's code, its .bss or its stack.  They are symbols and not constants
 * on purpose: a payload that grew would otherwise keep a stale bound.
 */

OUTPUT_ARCH(mips)
ENTRY(_start)

PHDRS
{
	text PT_LOAD FLAGS(5);		/* R E */
	data PT_LOAD FLAGS(6);		/* RW  */
}

SECTIONS
{
	. = LOAD_ADDR;
	_rlxboot_start = .;

	/* `_start` must be the first byte of the raw image: the loader's `J`
	 * goes to the load address, not to an entry symbol.  KEEP() because
	 * nothing references it. */
	.text : {
		KEEP(*(.text.entry))
		*(.text .text.* .gnu.linkonce.t.*)
		. = ALIGN(4);
	} :text

	/* ALIGN(16) at the end of each, for rlxprobe.lds's reason: `.data` and
	 * `.bss` come out of the compiler 16-byte aligned, and `objcopy -O
	 * binary` does not emit a hole belonging to no section -- so a
	 * `.rodata` ending on a 4-byte boundary makes the raw image shorter
	 * than the linked one and the Makefile's size assertion fires on four
	 * bytes of nothing. */
	.rodata : {
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		. = ALIGN(16);
	} :data

	.data : {
		*(.data .data.* .gnu.linkonce.d.*)
		. = ALIGN(16);
	} :data

	. = ALIGN(4);
	_bss_start = .;
	.bss (NOLOAD) : {
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		*(.sbss .sbss.*)
		*(.scommon)
		. = ALIGN(4);
	} :data
	_bss_end = .;
	_end = .;

	/* The stack, inside space this image owns.  32 KiB: the deepest the
	 * verifier was MEASURED to touch is reported by
	 * `src/rlxboot/test/t_crypto.c stack`, and the reserve is several times
	 * it.  The measurement is a lower bound -- it sees bytes that were
	 * written, not frames that were merely reserved -- which is the reason
	 * for the margin rather than for a tighter number. */
	. = ALIGN(16);
	. = . + STACK_SIZE;
	_stack_top = .;

	/DISCARD/ : {
		*(.comment)
		*(.note*)
		*(.pdr)
		*(.reginfo)
		*(.MIPS.abiflags)
		*(.gnu.attributes)
		*(.eh_frame)
		*(.mdebug*)
	}
}
