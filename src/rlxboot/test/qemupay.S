/* qemupay.S -- a small payload for rlxboot to boot.  TEST FIXTURE ONLY.
 *
 * It exists so that the qemu end-to-end run can tell "rlxboot jumped" from
 * "rlxboot printed RLXBOOT-BOOT and then hung", which are the same capture
 * without it.  It prints two lines and spins:
 *
 *   RLXPAY-OK
 *   RLXPAY-REGS a0=<8 hex> a1=<8 hex> a2=<8 hex> a3=<8 hex>
 *
 * The second line is a0..a3 AS THEY WERE AT ENTRY -- copied to s0..s3 by the
 * first four instructions, before anything else runs -- so the run reads what
 * rlxboot handed over (P6r-10, notes/self-update.md § 1.2): the handoff
 * after a slot boot, zeros after `rlxboot_jump`.  What it reads is the
 * emulator's registers; qemu says nothing about the silicon.
 *
 * `.set noreorder`, `.set noat`, `.set nomacro`; every delay slot filled by
 * hand.  It is a fixture and not part of the payload, so it is not linked into
 * `rlxboot.bin` -- but it is assembled by the same compiler under the same
 * rules, because a fixture that broke the rules would be the one place a
 * hand-encoded instruction got into this tree.
 *
 * Linked at whatever LOAD_ADDR the fixture container names (0x80500000), and
 * position-independent in the only sense that matters here: it forms the UART
 * address with lui/ori, its strings with lui/addiu of an absolute address and
 * calls with `jal`, so it must be linked at the address it is loaded to.
 *
 * Registers: s0..s3 a0..a3 at entry; t1 THR, t2 LSR, t3 the string, t4 the
 * byte, t5 the spin bound, t6 LSR's value, t7 the word printed, t8 its digit
 * count; ra for the two calls.  No stack.
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
	addu	$16, $4, $0			/* s0 = a0 at entry, FIRST */
	addu	$17, $5, $0			/* s1 = a1 */
	addu	$18, $6, $0			/* s2 = a2 */
	addu	$19, $7, $0			/* s3 = a3 */
	lui	$9, RLX_UART_THR>>16
	ori	$9, $9, RLX_UART_THR&0xffff	/* t1 = THR */
	lui	$10, RLX_UART_LSR>>16
	ori	$10, $10, RLX_UART_LSR&0xffff	/* t2 = LSR */
	lui	$11, %hi(msg)
	jal	puts				/* RLXPAY-OK */
	addiu	$11, $11, %lo(msg)		/* delay slot: t3 = the string */
	lui	$11, %hi(m_a0)
	jal	puts				/* RLXPAY-REGS a0= */
	addiu	$11, $11, %lo(m_a0)		/* delay slot */
	jal	puthex
	addu	$15, $16, $0			/* delay slot: t7 = a0 at entry */
	lui	$11, %hi(m_a1)
	jal	puts				/*  a1= */
	addiu	$11, $11, %lo(m_a1)		/* delay slot */
	jal	puthex
	addu	$15, $17, $0			/* delay slot: t7 = a1 at entry */
	lui	$11, %hi(m_a2)
	jal	puts				/*  a2= */
	addiu	$11, $11, %lo(m_a2)		/* delay slot */
	jal	puthex
	addu	$15, $18, $0			/* delay slot: t7 = a2 at entry */
	lui	$11, %hi(m_a3)
	jal	puts				/*  a3= */
	addiu	$11, $11, %lo(m_a3)		/* delay slot */
	jal	puthex
	addu	$15, $19, $0			/* delay slot: t7 = a3 at entry */
	lui	$11, %hi(m_nl)
	jal	puts				/* CR LF */
	addiu	$11, $11, %lo(m_nl)		/* delay slot */
4:
	beq	$0, $0, 4b
	nop					/* delay slot */
	.end	_start

/* puts: t3 = a NUL-terminated string.  Each byte waits for THRE | TEMT,
 * bounded by the loader's own 6540 polls, then goes to THR.  Clobbers t3..t6. */
	.ent	puts
puts:
1:
	lbu	$12, 0($11)			/* t4 = *p */
	nop					/* LOAD DELAY SLOT */
	beq	$12, $0, 9f
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
9:
	jr	$31
	nop					/* delay slot */
	.end	puts

/* puthex: t7 = a word; prints it as eight lower-case hex digits, most
 * significant first.  Clobbers t4..t8. */
	.ent	puthex
puthex:
	addiu	$24, $0, 8			/* t8 = digits left */
5:
	srl	$12, $15, 28			/* t4 = the top nibble */
	sltiu	$13, $12, 10			/* t5 = 1 when it is 0..9 */
	bne	$13, $0, 6f
	addiu	$12, $12, 0x30			/* delay slot, both paths: '0' + n */
	addiu	$12, $12, 0x27			/* 10..15: 'a' - '0' - 10 more */
6:
	addiu	$13, $0, 6540			/* t5 = the loader's own bound */
7:
	lbu	$14, 0($10)			/* t6 = LSR */
	nop					/* LOAD DELAY SLOT */
	andi	$14, $14, 0x60			/* THRE | TEMT */
	bne	$14, $0, 8f
	addiu	$13, $13, -1			/* delay slot */
	bne	$13, $0, 7b
	nop					/* delay slot */
8:
	sb	$12, 0($9)
	sll	$15, $15, 4			/* the next nibble to the top */
	addiu	$24, $24, -1
	bne	$24, $0, 5b
	nop					/* delay slot */
	jr	$31
	nop					/* delay slot */
	.end	puthex

	/* `.section .rodata`, not `.rodata`: this assembler has no `.rodata`
	 * pseudo-op ("unknown pseudo-op", measured).  The linker script puts
	 * .rodata in the non-executable segment, which is what keeps these
	 * strings out of hazlint's instruction decoder. */
	.section .rodata, "a"
msg:
	.asciz	"RLXPAY-OK\r\n"
m_a0:
	.asciz	"RLXPAY-REGS a0="
m_a1:
	.asciz	" a1="
m_a2:
	.asciz	" a2="
m_a3:
	.asciz	" a3="
m_nl:
	.asciz	"\r\n"
