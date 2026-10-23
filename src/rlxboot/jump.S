/* jump.S -- the instructions that hand the machine to a verified payload,
 * and nothing else.  rlxfw's own code.
 *
 * `.set noreorder`, `.set noat`, `.set nomacro`: every instruction below is one
 * I wrote and every delay slot is filled by hand.  `tools/hazlint` gates the
 * build and this file has no load in it at all.
 *
 * Two entries.  `rlxboot_jump` zeroes a0..a3 and is what BOOT=ram uses.
 * `rlxboot_jump_handoff` (BOOT=slots only) leaves the boot handoff in a0..a3
 * instead -- notes/self-update.md § 1.2, `handoff.h` for the four values.
 */

#include "handoff.h"

/* The Makefile passes $(BOOT_DEF) to the assembler as well as to the
 * compiler.  Without it the `#if` below would read an undefined name as 0 and
 * the slots build would lose its handoff entry -- a link failure, but one that
 * names the wrong cause, so the cause is named here instead. */
#ifndef RLXBOOT_SLOTS
#error "RLXBOOT_SLOTS must be 0 (BOOT=ram) or 1 (BOOT=slots); the Makefile's ASFLAGS sets it"
#endif

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

#if RLXBOOT_SLOTS
/* ---------------------------------------------------------------------------
 * void rlxboot_jump_handoff(u32 entry, u32 slot, u32 version, u32 check)
 * -- does not return.  BOOT=slots only (P6r-10, notes/self-update.md § 1.2).
 *
 * o32: a0 = entry, a1 = slot, a2 = version, a3 = check.  a1..a3 are left
 * exactly where the C caller put them; a0 is replaced by the magic.  So the
 * payload -- rtkload, whose entry saves all four (config/host-compat/0011) --
 * is entered with a0..a3 = magic, slot, version, check.
 *
 * The same order as `rlxboot_jump`, and for the same reason: the entry
 * leaves $a0 for $t0 FIRST, then $a0 is overwritten.  Nothing executes
 * between the `jr` and the payload's first instruction but the delay-slot
 * `ori`.  a0 holds a kuseg value at the payload's entry either way -- 0 from
 * `rlxboot_jump`, 0x524C5848 from here -- so the remark above about a fault
 * dereferencing a0 holds for both entries.
 *
 * The four words, assembled by the vendor's toolchain (the Makefile's payload
 * gate reads them back from the linked image): 00804021 3c04524c 01000008
 * 34845848.
 * ------------------------------------------------------------------------- */
	.globl	rlxboot_jump_handoff
	.ent	rlxboot_jump_handoff
	.type	rlxboot_jump_handoff, @function
rlxboot_jump_handoff:
	addu	$8, $4, $0				/* t0 = entry, out of a0, FIRST */
	lui	$4, (RLXB_HANDOFF_MAGIC >> 16)		/* a0 = magic, high half */
	jr	$8
	ori	$4, $4, (RLXB_HANDOFF_MAGIC & 0xFFFF)	/* delay slot: low half */
	.end	rlxboot_jump_handoff
#endif
