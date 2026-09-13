/* p4support.S -- the one routine probe4 needs that is not a table row.
 *
 * HAND-WRITTEN, unlike `cells4.S` beside it, and separate from it for that
 * reason alone: `cells4.S` is a function of `tools/isa-payload.tsv` and
 * `isapay.py emit --check` fails if one byte of it was not generated.  A
 * framework routine living in that file would have to be generated too, and a
 * generator that emits hand-written code is a generator nobody can check.
 *
 * 🔴 THIS FILE CONTAINS THE ONLY WRITE TO CP0 STATUS IN probe4, AND IT IS
 * COMPILED OUT OF EVERY DEVICE BUILD.  `RLX_CLEAR_BEV` is 1 only under
 * `qemu-run.sh`: qemu's Malta is a 24Kf and comes out of `-kernel` with
 * `Status.BEV` set, which is the one state a payload must not install a
 * handler into.  On the device `probe2` measured `BEV = 0` at the prompt
 * (`CPU-27`, 量 `bench/2026-08-25b`), so there is nothing to clear -- and
 * compiling the only writer out is what makes that claim readable from the
 * image instead of from this comment.  `probe1` cell 4 is why it matters:
 * `Status.IsC` does not isolate on this core and its byte stores reached DRAM.
 *
 * The body and its nop spacing are copied verbatim from `cells.S`'s
 * `rlx_status_write`.  The CP0 write hazard on this core is `C-9` and is NOT
 * established; these are copied, not reasoned about.
 */
	.set	noreorder
	.set	noat
	.set	nomacro
#include "rlxasm.h"

	.text

#if RLX_CLEAR_BEV
/* void rlx_status_write(u32 v) */
	.globl	rlx_status_write
	.ent	rlx_status_write
	.type	rlx_status_write, @function
rlx_status_write:
	addu	$8, $4, $0		/* a Status word such as 0x1000FC00 is a
					 * kuseg address, which is exactly the
					 * case SAFE_A0 exists for */
	SAFE_A0
	mtc0	$8, $12
	nop
	nop
	nop
	jr	$31
	nop
	.end	rlx_status_write
#endif
