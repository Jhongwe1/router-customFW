/* uart.S -- the parts where the instruction order is the point.
 *
 * Assembled under `.set noreorder`, `.set noat` and `.set nomacro`, so every
 * instruction in this file is one I wrote.  `nomacro` is not decoration: a
 * macro is an instruction the assembler chose, and this core's load delay slot
 * is architecturally exposed, so "an instruction I did not choose" and "an
 * instruction that reads a register one cycle too early" are the same risk.
 *
 * `tools/hazlint` gates the build.  It is not a lint whose output someone
 * reads; nothing links unless it exits 0.
 */

	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* ---------------------------------------------------------------------------
 * rlx_putc(int c)
 *
 * Copied in structure from this unit's own putchar, read out of stage 2 at
 * 0x80406B60-0x80406BB8:
 *
 *      80406b84:  lbu  v0,0(a1)        <- LSR at 0xB8002014
 *      80406b88:  nop                  <- THE LOAD DELAY SLOT
 *      80406b8c:  andi v0,v0,0x60      <- THRE | TEMT
 *
 * P9-12 copied the addresses and the 6540 spin bound out of that routine and
 * dropped the `nop`.  The device answered by emitting exactly 16 bytes per
 * iteration -- one 16550 FIFO -- 272 times over ten minutes.
 *
 * The loader gives up waiting after 6540 iterations and writes anyway.  That
 * is copied too: a probe that hangs because the far end stopped draining is
 * worse than a probe that drops a character.
 * ------------------------------------------------------------------------- */
	.globl	rlx_putc
	.ent	rlx_putc
	.type	rlx_putc, @function
rlx_putc:
	lui	$9, 0xb800		/* t1 */
	ori	$10, $9, 0x2014		/* t2 = LSR  */
	ori	$9, $9, 0x2000		/* t1 = THR  */
	addiu	$11, $0, 6540		/* t3 = the loader's own bound */
1:
	lbu	$12, 0($10)		/* t4 = LSR */
	nop				/* LOAD DELAY SLOT -- do not remove */
	andi	$12, $12, 0x60		/* THRE | TEMT */
	bne	$12, $0, 2f
	addiu	$11, $11, -1		/* delay slot, filled by hand */
	bne	$11, $0, 1b
	nop				/* delay slot, filled by hand */
2:
	sb	$4, 0($9)		/* a0 -> THR */
	jr	$31
	nop				/* delay slot, filled by hand */
	.end	rlx_putc

/* ---------------------------------------------------------------------------
 * u32 rlx_pc(void)
 *
 * Returns the caller's return address, which is a real address this code is
 * executing from.  `LOADADDR` echoing a number back is the loader repeating
 * what it was told; this is the payload reporting where it is.
 * ------------------------------------------------------------------------- */
	.globl	rlx_pc
	.ent	rlx_pc
	.type	rlx_pc, @function
rlx_pc:
	jr	$31
	addu	$2, $31, $0		/* delay slot: v0 = ra, executed before the jump */
	.end	rlx_pc

/* ---------------------------------------------------------------------------
 * CP0 reads.
 *
 * Two `nop`s after each `mfc0` before the value is used.  MIPS-I specifies a
 * CP0 read hazard; how many slots this core needs is C-9 and is NOT measured.
 * `jr`+delay would have given two slots anyway -- these are written down so
 * that the spacing is a decision and not an accident of the calling sequence.
 * ------------------------------------------------------------------------- */
	.macro	CP0READ name, reg
	.globl	\name
	.ent	\name
	.type	\name, @function
\name:
	mfc0	$2, $\reg
	nop
	nop
	jr	$31
	nop
	.end	\name
	.endm

	CP0READ rlx_mfc0_status,  12
	CP0READ rlx_mfc0_cause,   13
	CP0READ rlx_mfc0_prid,    15
	CP0READ rlx_mfc0_config,  16

/* Config1 is `mfc0 v0, $16, 1`.  The three-operand form is MIPS32 and gas
 * refuses it under -march=mips1, so the word is written out: opcode 0x10,
 * rs = 0 (MF), rt = 2 (v0), rd = 16, sel = 1.
 *
 *      0100 00 00000 00010 10000 00000000 001  =  0x40028001
 *
 * On a core with Config.M == 0 there is no Config1 and bits 2:0 are reserved,
 * so `probe0.c` reads Config first and only calls this when the core says the
 * register is there. */
	.globl	rlx_mfc0_config1
	.ent	rlx_mfc0_config1
	.type	rlx_mfc0_config1, @function
rlx_mfc0_config1:
	.word	0x40028001		/* mfc0 v0, $16, 1 */
	nop
	nop
	jr	$31
	nop
	.end	rlx_mfc0_config1

/* ---------------------------------------------------------------------------
 * rlx_reset(void) -- does not return.
 *
 * Three steps, and the first two exist because of P9-12's actual failure mode.
 *
 *   1. drain: poll LSR bit 6 (TEMT, transmitter empty) with the loader's own
 *      6540 bound.  The shortest watchdog timeout is 164 us undivided or
 *      2.30 ms through CDBR's divisor of 14 (SPEC.md CLK-08); sixteen bytes at
 *      38400 8N1 take 4.2 ms.  Arming without draining would cut the tail off
 *      the report -- the same shape of bug, one layer up.
 *   2. wait: TEMT says the shift register is empty.  It says nothing about the
 *      CP2102's latency timer at the far end (1-16 ms typical, unmeasured
 *      here), so a counted delay follows.
 *   3. arm: the loader's own idiom, copied verbatim from 0x804092E8 --
 *      including what it does NOT do.  It masks no interrupts and it spins on
 *      itself.  WDTCNR = 0 leaves WDTE != 0xA5, which ENABLES the watchdog,
 *      and OVSEL = 0000, the shortest of the ten timeouts.
 *
 * Why a reset at all: one power cycle is the most expensive unit on this
 * project and there is no spare device.  A payload that returns the board to
 * the loader prompt by itself costs nothing physical, which is what makes a
 * second, third and fourth payload affordable in one seating.
 * ------------------------------------------------------------------------- */
	.globl	rlx_reset
	.ent	rlx_reset
	.type	rlx_reset, @function
rlx_reset:
	lui	$8, 0xb800		/* t0 */
	ori	$9, $8, 0x2014		/* t1 = LSR */
	addiu	$10, $0, 6540		/* t2 */
1:
	lbu	$11, 0($9)		/* t3 = LSR */
	nop				/* LOAD DELAY SLOT -- do not remove */
	andi	$11, $11, 0x40		/* TEMT */
	bne	$11, $0, 2f
	addiu	$10, $10, -1		/* delay slot */
	bne	$10, $0, 1b
	nop				/* delay slot */
2:
	lui	$10, 0x0100		/* 16,777,216 iterations */
3:
	addiu	$10, $10, -1
	bne	$10, $0, 3b
	nop				/* delay slot */

	lui	$2, 0xb800
	ori	$2, $2, 0x311c		/* WDTCNR */
	sw	$0, 0($2)
4:
	beq	$0, $0, 4b
	nop				/* delay slot */
	.end	rlx_reset
