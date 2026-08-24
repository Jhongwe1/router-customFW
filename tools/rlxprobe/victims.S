/* victims.S -- the sixteen functions probe1 rewrites one instruction of.
 *
 * A file of its own, and not part of cache.S, because probe2 links cache.S for
 * `rlx_cctl` and `rlx_call2_uncached` and has no use for 16 KiB of victims.  A
 * payload that carries code it never executes is a payload whose `hazlint`
 * population is 16 KiB of `nop`.
 */

#include "rlxdefs.h"

	.set	noreorder
	.set	noat
	.set	nomacro

/* ---------------------------------------------------------------------------
 * The victims.
 *
 * RLX_VICTIM_SLOTS of them, RLX_VICTIM_STRIDE apart, each three instructions:
 *
 *      addiu  v0, zero, RLX_VICTIM_OLD    <- the word the experiment rewrites
 *      jr     ra
 *      nop
 *
 * A cell uses slots k and k+RLX_VICTIM_PAIR_GAP rather than k and k+1, and the
 * reason is the one thing that can silently ruin cell 1.  If a victim's line
 * were evicted between priming it and calling it again, the second call would
 * refetch from memory and report the NEW constant with no flush having
 * happened -- a pass that means nothing.  Two victims 7 KiB apart can share a
 * cache index only if the cache size divides 7168, and the only power of two
 * that does is 1024.  So agreement between the two members of a pair excludes
 * eviction for every plausible cache size except 1 KiB, and disagreement is
 * itself a measurement rather than a failure.
 *
 * This does NOT exclude eviction by the driver code that runs between the two
 * calls, which is why cell 1 exists and why the gate's refutation condition is
 * written against cell 1 and not against the flush cells.
 *
 * The padding between victims is zero words, which decode as `nop`, so the gate
 * scans 16 KiB of `sll $0,$0,0` and finds no loads in it.  That is not a
 * weakness of the gate: there is nothing there.
 * ------------------------------------------------------------------------- */
	.section .victims, "ax"

	/* No per-victim symbol and no `.macro`: probe1.c reaches a victim as
	 * `rlx_victims + slot * RLX_VICTIM_STRIDE`, and it CHECKS that arithmetic
	 * at run time by reading the word there uncached and requiring it to be
	 * RLX_VICTIM_WORD_OLD before it will use the slot.  A symbol per victim
	 * would have looked like a stronger guarantee while checking nothing --
	 * the linker would place them wherever it liked and the payload would
	 * still compute addresses the other way. */
	.align	10
	.globl	rlx_victims
rlx_victims:
	.rept	RLX_VICTIM_SLOTS
	.align	10
	addiu	$2, $0, RLX_VICTIM_OLD	/* THE PATCHED WORD */
	jr	$31
	nop				/* delay slot, filled by hand */
	.endr
	.align	10
	.globl	rlx_victims_end
rlx_victims_end:
