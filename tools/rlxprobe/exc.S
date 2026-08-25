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
#include "rlxasm.h"

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
 * 9, and this returns.
 *
 * IF IT DID NOT TAKE, THE FAILURE WAS DESIGNED TO BE VISIBLE AND WAS MEASURED
 * TO BE SILENCE.  `docs/rlxprobe-audit-2026-08-25.md` Must-fix 1, 量 on the
 * emitted image:
 *
 *      80500f40:  1480fffb   bnez a0,80500f30   # rlx_puts' loop exit test
 *      ...                                      # nothing after this writes $a0
 *      80501364:  0c1400b2   jal  rlx_do_break
 *
 * `rlx_puts` exits on the string's NUL, so it always returns with `$a0 = 0`.
 * Without the guard below, `break` reaches the loader's dispatcher, which reads
 * `exception_handlers[9]` -- MEASURED 2026-08-25, `bench/2026-08-25/H0b.log`, it
 * is `0x80400BE8`, `do_reserved`, exactly as the audit assumed -- which does
 * `move v0,a0` and then `lw a3,148(v0)` at 0x80400C00: a load from 0x00000094,
 * kuseg, through a TLB the loader never initialises.  **The first `prom_printf`
 * is at 0x80400C04.**  Neither line reaches the wire, and the promised
 * `Undefined Exception happen.` is complete silence.
 *
 * SAFE_A0 costs two instructions and turns that back into the two prints and
 * the hang at 0x80400C18 that the rest of this payload is designed around.
 * `cache.S` spends thirty lines establishing this hazard and applies the macro
 * to three routines; until 2026-08-25 the one instruction in the tree guaranteed
 * by design to fault was the one without it, and `tools/test-rlxprobe.sh` S1
 * scoped it out because `break` is not a CP0 instruction.  S1 now reads *every
 * routine that contains an instruction that can fault*, and S2 is the mutation.
 * ------------------------------------------------------------------------- */
	.globl	rlx_do_break
	.ent	rlx_do_break
	.type	rlx_do_break, @function
rlx_do_break:
	SAFE_A0				/* $a0 is a caller-saved register and this
					 * routine takes no argument, so there is
					 * nothing here to preserve */
	break
	jr	$31
	nop				/* delay slot, filled by hand */
	.end	rlx_do_break

/* ---------------------------------------------------------------------------
 * u32 rlx_count_delta(u32 spins, u32 *raw)
 *
 * Read CP0 Count (register 9) twice with a counted loop between, return the
 * difference, and write the two raw readings to raw[0] and raw[1].
 *
 * F50b: an R3000-class CP0 has no Count/Compare -- they arrive with R4000 -- and
 * CPU-19 already records this core as using the R3000 cache model.  A zero here
 * says the register is not implemented or is not running; a non-zero says it is,
 * and its rate over a known loop is its frequency.  Not moved = no
 * implementation is the reading the plan writes down, and the thing it decides
 * is whether R5-0's SoC timer driver is a prerequisite or a bonus.
 *
 * BOTH DESTINATIONS ARE PRIMED, AND WITHOUT THAT THE ROUTINE ANSWERED F50b
 * BACKWARDS.  `docs/rlxprobe-audit-2026-08-25.md` Must-fix 4, 量:
 *
 *      805002d4:  40084800   mfc0  t0,$9      # $8 was not initialised
 *      805002f0:  400f4800   mfc0  t7,$9      # $15 is written by no instruction
 *                                             #     anywhere in the payload
 *
 * If `mfc0` does not write `rt` on this core -- which is one of the three
 * plausible behaviours and is precisely what the census exists to find out --
 * then the old code returned (the loader's leftover $t7) - 0xA0500150, a large
 * residue-arithmetic value, against a runsheet cell expecting 00000000.  **A
 * result that reads as its own refutation.**
 *
 * Priming with ZERO would have been worse than not priming: 0 - 0 = 0, and a
 * zero delta is the answer this cell is hunting, so the instrument's own failure
 * would wear the result's clothes.  The two primes are therefore DIFFERENT and
 * they are the same two families the census uses, so one convention covers both:
 *
 *      before <- 0xC0DE0009        after <- 0xD1CE0009
 *
 * -- 0x0009 being CP0 register 9, so the pair names itself in a hex dump.  If
 * neither `mfc0` writes, the caller sees exactly that pair in raw[0]/raw[1] and
 * a delta of 0x110F0000, which is not a plausible tick count and cannot be
 * mistaken for one.  The caller cross-checks it against census row 0x48, which
 * is the same register through the same instruction on a different path.
 *
 * THE LOOP BODY IS THREE INSTRUCTIONS AND MUST STAY THREE.  `CLK-03`'s first
 * experiment (2026-08-25, Delta = 123.7 ms) measured f/CPI against exactly this
 * shape; adding an instruction inside the loop would silently move a published
 * number.
 * ------------------------------------------------------------------------- */
	.globl	rlx_count_delta
	.ent	rlx_count_delta
	.type	rlx_count_delta, @function
rlx_count_delta:
	/* GPR $9 is deliberately not used: `mfc0 $8, $9` means CP0 register 9,
	 * and a general register 9 in the same six lines is how a reader
	 * checking this against the R3000 manual loses ten minutes. */
	addu	$14, $4, $0		/* t6 = spins, taken out of $a0 BEFORE the
					 * guard below overwrites it */
	SAFE_A0				/* CP0 register 9 may not exist on this
					 * core -- that is what this routine is
					 * asking -- so its `mfc0` is in exactly
					 * the class the guard is for.  The
					 * handler is installed by the time this
					 * runs and the `break` control has proved
					 * it live, but "proved live" is a
					 * property of THIS run and the guard is
					 * two instructions. */
	lui	$8, 0xc0de
	ori	$8, $8, 0x0009		/* t0 = the prime for "before" */
	lui	$15, 0xd1ce
	ori	$15, $15, 0x0009	/* t7 = the prime for "after" */

	mfc0	$8, $9			/* t0 = Count, before */
	nop
	nop
1:
	addiu	$14, $14, -1
	bne	$14, $0, 1b
	nop				/* delay slot, filled by hand */
	mfc0	$15, $9			/* t7 = Count, after */
	nop
	nop
	sw	$8, 0($5)		/* raw[0] = before, whatever it is */
	sw	$15, 4($5)		/* raw[1] = after */
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
