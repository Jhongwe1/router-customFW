/* p5support.S -- the two routines probe5 needs that are not table rows.
 *
 * HAND-WRITTEN, unlike `cells5.S` beside it, and separate from it for that
 * reason alone: `cells5.S` is a function of `tools/isa-hazard.tsv` and
 * `hazpay.py emit --check` fails if one byte of it was not generated.  A
 * framework routine living in that file would have to be generated too, and a
 * generator that emits hand-written code is a generator nobody can check.
 * `p4support.S` beside it is the precedent and the first routine below is its
 * body verbatim.
 *
 * 🔴 `rlx_status_write` IS THE ONLY WRITE TO CP0 STATUS IN probe5 AND IT IS
 * COMPILED OUT OF EVERY DEVICE BUILD.  `RLX_CLEAR_BEV` is 1 only under
 * `qemu-run.sh`: qemu's Malta is a 24Kf and comes out of `-kernel` with
 * `Status.BEV` set, which is the one state a payload must not install a handler
 * into.  On the device `probe2` measured `BEV = 0` at the prompt (`CPU-27`, 量
 * `bench/2026-08-25b`), so there is nothing to clear -- and compiling the only
 * writer out is what makes that claim readable from the image instead of from
 * this comment.
 *
 * ⚠️ `rlx_mfc0_epc` IS NEW AND IT IS HERE RATHER THAN IN `uart.S` ON PURPOSE.
 * `uart.S` is linked into probe0 through probe4 as well, and a new routine there
 * would change four images that are not this segment's subject -- `probe4`'s in
 * particular is the one going to the bench beside this one.  probe5 is the only
 * payload that writes CP0 14, so probe5 is the only payload that needs to read
 * it, and a probe5-only file is where a probe5-only need belongs.
 *
 * The `nop` spacing after each CP0 access is copied from `uart.S`'s readers and
 * from `cells.S`'s writer, NOT reasoned about: the CP0 read and write hazards on
 * this core are `C-9`/`CPU-31` and are exactly what `probe5` exists to measure.
 * A support routine that assumed the answer would be assuming the result.
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

/* u32 rlx_mfc0_epc(void) -- CP0 14.
 *
 * Read AFTER the sweep, so `epc_end` in the header says what the last `c0_*`
 * cell's write left behind.  It is not that family's control -- each `c0_*` cell
 * reads EPC back itself, inside the cell, which is the reading that matters --
 * it is the outside-a-cell confirmation that the write was visible at all.  A
 * trap during the sweep overwrites EPC in hardware, so this word is only worth
 * reading beside `trapped`. */
	.globl	rlx_mfc0_epc
	.ent	rlx_mfc0_epc
	.type	rlx_mfc0_epc, @function
rlx_mfc0_epc:
	SAFE_A0
	mfc0	$2, $14
	nop
	nop
	jr	$31
	nop
	.end	rlx_mfc0_epc
