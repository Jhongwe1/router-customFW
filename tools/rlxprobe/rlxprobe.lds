/* rlxprobe.lds
 *
 * LOAD_ADDR and STACK_SIZE come in on the link line with --defsym, so the same
 * script builds a payload for any address the loader's `LOADADDR` will accept.
 *
 * Two PT_LOADs, and the split is not cosmetic.  `tools/hazlint` takes its scan
 * range from the EXECUTABLE program headers.  If .rodata shared a segment with
 * .text, every banner string in this file would be handed to the instruction
 * decoder as code -- which is exactly the false-positive class
 * `docs/loader-command-semantics.md` §9 spent a session adjudicating.  Keeping
 * rodata out of the executable segment means the gate scans code and only
 * code, and it means the ELF is honest about what is meant to be executed.
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

	/* `_start` must be the first byte of the raw image: the loader's `J`
	 * goes to the load address, not to an entry symbol. KEEP() because
	 * nothing references it and --gc-sections would be within its rights. */
	.text : {
		KEEP(*(.text.entry))
		*(.text .text.* .gnu.linkonce.t.*)

		/* The victims, when a payload has any.  Two things are
		 * deliberate and neither is obvious.
		 *
		 * The section is called `.victims` and not `.text.victims`,
		 * because `*(.text .text.*)` above would have swallowed that
		 * name and scattered sixteen 1 KiB-aligned functions through
		 * the payload's own code.
		 *
		 * There is no ALIGN() here.  The alignment comes from `.align
		 * 10` inside the input section, so the linker aligns it and a
		 * payload with NO victims gets no padding at all -- which is
		 * what keeps probe0's image the size it was.  A script-side
		 * ALIGN would have padded every payload to 1 KiB and, worse,
		 * a `_victims_start = .` written before it would have recorded
		 * the address BEFORE the padding.  `rlx_victims` is the symbol
		 * to use: it sits after cache.S's own `.align`. */
		KEEP(*(.victims))
		. = ALIGN(4);
	} :text

	/* ALIGN(16), not ALIGN(4).  `.data` and `.bss` come out of the
	 * compiler with 16-byte alignment, so a `.rodata` that ends on a
	 * 4-byte boundary leaves a hole between the two -- and `objcopy -O
	 * binary` does not emit a hole that belongs to no section.  The raw
	 * image is then shorter than the linked one and the Makefile's size
	 * assertion fires, correctly, on four bytes of nothing.  Ending
	 * aligned to the same boundary the next section wants removes the
	 * hole rather than teaching the check to ignore it. */
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
		. = ALIGN(4);
	} :data
	_bss_end = .;
	_end = .;

	/* The stack lives above .bss, inside space this image owns. Putting it
	 * anywhere in 0x8040xxxx would be putting it in the loader's. */
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
