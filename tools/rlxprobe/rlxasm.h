/* rlxasm.h -- assembler macros shared between cache.S and exc.S.
 *
 * ASSEMBLER ONLY.  This file is #included from `.S` sources, which go through
 * the C preprocessor and then straight into the assembler.  It must never be
 * included from C: a `.macro` directive reaching the compiler fails in a way
 * that reads like a toolchain fault.  `rlxdefs.h` holds the constants both
 * languages share; `rlxprobe.h` holds the C declarations; this holds the
 * assembler's own.
 *
 * It exists because SAFE_A0 lived in cache.S and `exc.S` needed it -- and the
 * reason it needed it is the whole of `docs/rlxprobe-audit-2026-08-25.md`
 * Must-fix 1: the one instruction in the tree that is guaranteed by design to
 * fault, `break` in `rlx_do_break`, was the one instruction without the guard.
 * Duplicating two instructions into a second file would have left two copies of
 * a decision that has to be one.
 */
#ifndef RLXASM_H
#define RLXASM_H

/* ---------------------------------------------------------------------------
 * SAFE_A0 -- put a readable, word-aligned KSEG0 address in $a0 before executing
 * anything that could fault.
 *
 * WHY, and this is not defensive programming, it is a measured hazard.
 *
 * This unit's loader handles a reserved exception with `do_reserved` at
 * 0x80400BE8, registered as the RAW vector target with no SAVE_ALL wrapper.  So
 * it runs on the faulting code's own `sp` and its own `a0`, and its third
 * instruction is
 *
 *      80400c00:  8c470094   lw   a3,148(v0)      # v0 = the faulting a0
 *
 * -- it dereferences whatever the faulting code happened to have in $a0,
 * treating it as a `pt_regs *` that nobody built.
 *
 * `rlx_cctl(0x002)` passes 0x002 in $a0.  0x002 + 148 = 0x96, which is kuseg,
 * and kuseg is TLB-mapped on this core.  The loader never executes a single TLB
 * instruction, so the TLB is in whatever state reset left it; a miss there goes
 * to the UTLB refill vector at 0x80000000.
 *
 * MEASURED 2026-08-25, `bench/2026-08-25/H0c.log`: word 0 of that vector holds
 * 0x5A5AA5A5, whose opcode field is 0b010110 = 22 = BLEZL -- not `j` (2) and not
 * `jal` (3).  So the escalation this macro was once argued from ("it could
 * branch into the loader's flash-write path at 0x804099AC") stays refuted BY
 * MEASUREMENT rather than by reading stage 1's source: a J-format instruction is
 * the only shape that could reach loader code from there, and this is not one.
 *
 * There is no demonstrated brick path.  SAFE_A0 stays because it costs TWO
 * INSTRUCTIONS and removes an undetermined case, not because a disaster was
 * shown.
 *
 * With a safe $a0 the same fault takes the ordinary branch: two prints and a
 * hang at 0x80400C18.  A hang costs one power cycle, which is expensive and
 * bounded.  And it is recognisable: `rlx_fault_frame` is zeroed by start.S, so
 * the loader prints `ra=0` and the operator knows the guard was in place.
 *
 * `rlx_fault_frame` is declared by whichever payload links this -- 64 words,
 * checked by `tools/test-rlxprobe.sh` V2 to be inside .bss and at least 148+4
 * bytes long, because 148 is the offset `do_reserved` reads.
 * ------------------------------------------------------------------------- */
	.macro	SAFE_A0
	lui	$4, %hi(rlx_fault_frame)
	addiu	$4, $4, %lo(rlx_fault_frame)
	.endm

#endif /* RLXASM_H */
