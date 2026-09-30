/* jump.S -- the two instructions that hand the machine to a verified payload,
 * and nothing else.  rlxfw's own code.
 *
 * `.set noreorder`, `.set noat`, `.set nomacro`: every instruction below is one
 * I wrote and every delay slot is filled by hand.  `tools/hazlint` gates the
 * build and this file has no load in it at all.
 */

	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* ---------------------------------------------------------------------------
 * void rlxboot_jump(u32 entry) -- does not return.
 *
 * `jr`, not `jalr`: there is nothing to return to.  The verified payload is
 * entered exactly as the loader's own `J` enters one -- at an address, with no
 * return address worth keeping -- except for one difference, and it is
 * deliberate: a0..a3 ARE ZEROED HERE.
 *
 * `docs/loader-command-semantics.md` s(d): "`J` leaves `a0`-`a3` in a state the
 * target cannot rely on."  A payload booted by rlxboot gets a defined state
 * instead, which costs four instructions and removes a difference between
 * "booted by the loader" and "booted by rlxboot" that would otherwise be
 * undeclared.  $a0 in particular is the register this unit's `do_reserved`
 * dereferences on a fault (`tools/rlxprobe/rlxasm.h`), and 0 + 148 is a kuseg
 * address -- so zeroing it is not safer than SAFE_A0 and this routine is not
 * claiming it is.  What it claims is that the value is KNOWN.
 *
 * $sp is left alone.  The payload establishes its own, as start.S does; a
 * loader that handed over a stack pointer would be making a promise about
 * memory it does not own after the jump.
 *
 * The entry address arrives in $a0 and is moved to $t0 BEFORE $a0 is zeroed,
 * which is the whole of the instruction order here.
 * ------------------------------------------------------------------------- */
	.globl	rlxboot_jump
	.ent	rlxboot_jump
	.type	rlxboot_jump, @function
rlxboot_jump:
	addu	$8, $4, $0		/* t0 = entry, out of a0, FIRST */
	addu	$4, $0, $0		/* a0 = 0 */
	addu	$5, $0, $0		/* a1 = 0 */
	addu	$6, $0, $0		/* a2 = 0 */
	jr	$8
	addu	$7, $0, $0		/* delay slot: a3 = 0, filled by hand */
	.end	rlxboot_jump
