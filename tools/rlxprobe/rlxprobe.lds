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
		. = ALIGN(4);
	} :text

	.rodata : {
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		. = ALIGN(4);
	} :data

	.data : {
		*(.data .data.* .gnu.linkonce.d.*)
		. = ALIGN(4);
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
