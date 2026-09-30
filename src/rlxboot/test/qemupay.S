/* qemupay.S -- a two-line payload for rlxboot to boot.  TEST FIXTURE ONLY.
 *
 * It exists so that the qemu end-to-end run can tell "rlxboot jumped" from
 * "rlxboot printed RLXBOOT-BOOT and then hung", which are the same capture
 * without it.  It prints one line and spins.
 *
 * `.set noreorder`, `.set noat`, `.set nomacro`; every delay slot filled by
 * hand.  It is a fixture and not part of the payload, so it is not linked into
 * `rlxboot.bin` -- but it is assembled by the same compiler under the same
 * rules, because a fixture that broke the rules would be the one place a
 * hand-encoded instruction got into this tree.
 *
 * Linked at whatever LOAD_ADDR the fixture container names (0x80500000), and
 * position-independent in the only sense that matters here: it forms the UART
 * address with lui/ori and its string with lui/ori of an absolute address, so
 * it must be linked at the address it is loaded to.
 */

/* rlxdefs.h for RLX_UART_THR / RLX_UART_LSR.  It guards both with `#ifndef`, so
 * a -D on the command line still wins -- which is how the qemu build moves them
 * to Malta's 0xB80003F8 while a device build gets 0xB8002000 with no flag at
 * all.  Needs -I tools/rlxprobe. */
#include "rlxdefs.h"

	.set	noreorder
	.set	noat
	.set	nomacro

	.section .text.entry, "ax"
	.globl	_start
	.ent	_start
_start:
	lui	$9, RLX_UART_THR>>16
	ori	$9, $9, RLX_UART_THR&0xffff	/* t1 = THR */
	lui	$10, RLX_UART_LSR>>16
	ori	$10, $10, RLX_UART_LSR&0xffff	/* t2 = LSR */
	lui	$11, %hi(msg)
	addiu	$11, $11, %lo(msg)		/* t3 = the string */
1:
	lbu	$12, 0($11)			/* t4 = *p */
	nop					/* LOAD DELAY SLOT */
	beq	$12, $0, 4f
	nop					/* delay slot, filled by hand */
	addiu	$13, $0, 6540			/* t5 = the loader's own bound */
2:
	lbu	$14, 0($10)			/* t6 = LSR */
	nop					/* LOAD DELAY SLOT */
	andi	$14, $14, 0x60			/* THRE | TEMT */
	bne	$14, $0, 3f
	addiu	$13, $13, -1			/* delay slot */
	bne	$13, $0, 2b
	nop					/* delay slot */
3:
	sb	$12, 0($9)
	beq	$0, $0, 1b
	addiu	$11, $11, 1			/* delay slot: advance p */
4:
	beq	$0, $0, 4b
	nop					/* delay slot */
	.end	_start

	/* `.section .rodata`, not `.rodata`: this assembler has no `.rodata`
	 * pseudo-op ("unknown pseudo-op", measured).  The linker script puts
	 * .rodata in the non-executable segment, which is what keeps this
	 * string out of hazlint's instruction decoder. */
	.section .rodata, "a"
msg:
	.asciz	"RLXPAY-OK\r\n"
