/* exc.S -- a bare-metal exception handler for this core, and the 256 stubs the
 * CP0 census reads through.
 *
 * Assembled under `.set noreorder`, `.set noat`, `.set nomacro`.  `hazlint`
 * gates the build.
 *
 * THE VECTOR IS 0x80000080, AND THAT IS THE WHOLE REASON THIS FILE EXISTS
 * ----------------------------------------------------------------------
 * Four documents in this repository said 0x80000180 until 2026-08-25.  That is
 * the MIPS32 general exception vector.  This is a Lexra RLX with an R3000-class
 * CP0 and the layout is
 *
 *      0x80000000 .. 0x8000007F   UTLB refill vector
 *      0x80000080 .. 0x800000FF   general exception vector
 *
 * read three ways that agree and none that does not: this unit's own `trap_init`
 * at 0x8040D07C builds `lui v0,0x8000` / `ori t0,v0,0x80`; the vendor bootcode's
 * own comment says *"vector base is 80000000, offset 0x80"*; and
 * `linux-2.6.30/arch/rlx/kernel/traps.c:691` is `#define RLX_TRAP_VEC_BASE
 * 0x80000080`.  Corroborated by the loader leaving an exception with `rfe`
 * (0x42000010, two sites) while the `eret` encoding 0x42000018 occurs zero times
 * in the same file -- and that zero has its control, because the same grep finds
 * both `rfe`s.  `notes/cache-model.md` carries it in full.
 *
 * WHY A HANDLER IS WORTH INSTALLING AT ALL
 * ----------------------------------------
 * Without one, a fault reaches the loader's `do_reserved` at 0x80400BE8, which
 * prints twice and executes `j 0x80400C18` -- a branch to itself, with
 * interrupts already off and the watchdog not armed.  It hangs forever, and one
 * hang costs one power cycle.  A CP0 census that must survive several hundred
 * reads of registers nobody has ever read on this part cannot be run under that.
 *
 * WHAT THIS HANDLER DELIBERATELY DOES NOT DO
 * ------------------------------------------
 *   * It never touches $sp.  $sp at the moment of a fault is whatever the
 *     faulting code had, and `do_reserved`'s own `sw ra,16(sp)` is a reminder
 *     of what assuming otherwise looks like.
 *   * It uses only $k0 and $k1, which is what they are for.
 *   * It writes its record through KSEG1, so nothing it records is sitting in a
 *     write-back D-cache if the run ends badly.
 *   * It adds 4 to EPC unconditionally.  THAT IS WRONG IN A BRANCH DELAY SLOT,
 *     where EPC points at the branch and Cause.BD is set -- so no probed
 *     instruction is ever placed in one, and Cause is recorded whole so that
 *     BD is visible if it ever happens anyway.
 */

#include "rlxdefs.h"

	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* ---------------------------------------------------------------------------
 * The handler.
 *
 * Assembled here and COPIED to 0x80000080 (and to 0x80000000), so nothing in it
 * may depend on the address it was linked at.  Every address it forms is
 * absolute -- `lui`/`addiu` -- and its only control transfer is `jr`, so the
 * copy runs correctly wherever it lands.  The bytes between rlx_exc_entry and
 * rlx_exc_end are what gets copied; the build asserts that span is <= 128.
 * ------------------------------------------------------------------------- */
	.globl	rlx_exc_entry
	.ent	rlx_exc_entry
	.type	rlx_exc_entry, @function
rlx_exc_entry:
	lui	$26, %hi(rlx_exc_rec)
	addiu	$26, $26, %lo(rlx_exc_rec)
	lui	$27, KSEG1_BIT>>16
	or	$26, $26, $27		/* k0 = &rlx_exc_rec, uncached */

	mfc0	$27, $13		/* Cause */
	nop
	nop
	sw	$27, 4($26)

	mfc0	$27, $14		/* EPC */
	nop
	nop
	sw	$27, 8($26)

	lw	$27, 0($26)		/* the count of exceptions taken */
	nop				/* LOAD DELAY SLOT -- do not remove */
	addiu	$27, $27, 1
	sw	$27, 0($26)

	mfc0	$26, $14		/* EPC again, into the register we jump on */
	nop
	nop
	addiu	$26, $26, 4		/* skip the faulting instruction */
#if RLX_RET_ERET
	/* qemu ONLY, and the fork is here rather than hidden because it is the
	 * one place where this file stops describing the device.  `rfe` is
	 * MIPS-I; MIPS32 removed it and put `eret` in its place, so on qemu's
	 * 24Kf the R3000 return below is itself a Reserved Instruction and the
	 * handler faults inside itself.  Measured 2026-08-25: probe2 stopped
	 * dead at the `break` control under qemu with the R3000 return.
	 *
	 * A device build has RLX_RET_ERET=0 and `tools/test-rlxprobe.sh`
	 * asserts that the emitted image contains 0x42000010 (`rfe`) and does
	 * NOT contain 0x42000018 (`eret`). */
	mtc0	$26, $14		/* EPC = EPC + 4 */
	nop
	nop
	.word	0x42000018		/* eret -- MIPS32, not this core */
	nop
#else
	jr	$26
	rfe				/* delay slot: R3000 pops the KU/IE stack */
#endif
	.globl	rlx_exc_end
rlx_exc_end:
	.end	rlx_exc_entry

/* ---------------------------------------------------------------------------
 * void rlx_do_break(void)
 *
 * THE POSITIVE CONTROL ON THE HANDLER, and it has to be an instruction that
 * traps on every MIPS ever built -- not a reserved encoding.  Whether a reserved
 * encoding traps on THIS core is R1a's question and is exactly what a census
 * running under an unproven handler could not answer.  `break` is MIPS-I and its
 * ExcCode is 9 (Bp) by definition.
 *
 * If the handler took, `rlx_exc_rec[0]` increments, Cause's ExcCode field reads
 * 9, and this returns.  If it did not, the loader's reporter prints
 * `Undefined Exception happen.` and the board hangs -- which is an unambiguous
 * observation and not a silent wrong answer.
 * ------------------------------------------------------------------------- */
	.globl	rlx_do_break
	.ent	rlx_do_break
	.type	rlx_do_break, @function
rlx_do_break:
	break
	jr	$31
	nop				/* delay slot, filled by hand */
	.end	rlx_do_break

/* ---------------------------------------------------------------------------
 * u32 rlx_count_delta(u32 spins)
 *
 * Read CP0 Count (register 9) twice with a counted loop between, and return the
 * difference.  F50b: an R3000-class CP0 has no Count/Compare -- they arrive with
 * R4000 -- and CPU-19 already records this core as using the R3000 cache model.
 * A zero here says the register is not implemented or is not running; a non-zero
 * says it is, and its rate over a known loop is its frequency.
 *
 * Not moved = no implementation is the reading the plan writes down, and the
 * thing it decides is whether R5-0's SoC timer driver is a prerequisite or a
 * bonus.  Zero is therefore a RESULT here, which is why the loop count is
 * returned beside it: a zero delta with a zero loop count would be an
 * instrument failure wearing a result's clothes.
 * ------------------------------------------------------------------------- */
	.globl	rlx_count_delta
	.ent	rlx_count_delta
	.type	rlx_count_delta, @function
rlx_count_delta:
	/* GPR $9 is deliberately not used: `mfc0 $8, $9` means CP0 register 9,
	 * and a general register 9 in the same six lines is how a reader
	 * checking this against the R3000 manual loses ten minutes. */
	mfc0	$8, $9			/* t0 = Count, before */
	nop
	nop
	addu	$14, $4, $0		/* t6 = spins */
1:
	addiu	$14, $14, -1
	bne	$14, $0, 1b
	nop				/* delay slot, filled by hand */
	mfc0	$15, $9			/* t7 = Count, after */
	nop
	nop
	subu	$2, $15, $8
	jr	$31
	nop
	.end	rlx_count_delta

/* ---------------------------------------------------------------------------
 * The CP0 read stubs: 32 registers x 8 select values = 256 of them.
 *
 *      mfc0 v0, $rd, sel   =   0x40020000 | (rd << 11) | sel
 *
 * emitted as a raw word, because the three-operand form is MIPS32 and gas
 * refuses it under -march=mips1.  Verified against the one this repository
 * already had: rd = 16, sel = 1 gives 0x40020000 | 0x8000 | 1 = 0x40028001,
 * which is the word `probe0`'s Config1 reader has carried since it was written.
 *
 * Every stub is three words and they are contiguous, so probe2.c reaches stub n
 * as `rlx_cp0_stubs + n * 12`.  `tools/test-rlxprobe.sh` checks that arithmetic
 * against the emitted image rather than trusting it.
 *
 * The select field does not exist on an R3000-class CP0 -- bits 2:0 are
 * reserved.  Reading all eight is how this finds out whether this core decodes
 * them, ignores them, or faults on them, and those are three different answers.
 * ------------------------------------------------------------------------- */
	.macro	CP0STUB rd, sel
	.word	0x40020000 | (\rd << 11) | \sel
	jr	$31
	nop
	.endm

	.macro	CP0ROW rd
	CP0STUB	\rd, 0
	CP0STUB	\rd, 1
	CP0STUB	\rd, 2
	CP0STUB	\rd, 3
	CP0STUB	\rd, 4
	CP0STUB	\rd, 5
	CP0STUB	\rd, 6
	CP0STUB	\rd, 7
	.endm

	.align	4
	.globl	rlx_cp0_stubs
rlx_cp0_stubs:
	CP0ROW	0
	CP0ROW	1
	CP0ROW	2
	CP0ROW	3
	CP0ROW	4
	CP0ROW	5
	CP0ROW	6
	CP0ROW	7
	CP0ROW	8
	CP0ROW	9
	CP0ROW	10
	CP0ROW	11
	CP0ROW	12
	CP0ROW	13
	CP0ROW	14
	CP0ROW	15
	CP0ROW	16
	CP0ROW	17
	CP0ROW	18
	CP0ROW	19
	CP0ROW	20
	CP0ROW	21
	CP0ROW	22
	CP0ROW	23
	CP0ROW	24
	CP0ROW	25
	CP0ROW	26
	CP0ROW	27
	CP0ROW	28
	CP0ROW	29
	CP0ROW	30
	CP0ROW	31
	.globl	rlx_cp0_stubs_end
rlx_cp0_stubs_end:
