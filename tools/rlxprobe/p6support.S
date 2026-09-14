/* p6support.S -- the one routine probe6 needs that is not a table row.
 *
 * HAND-WRITTEN, and separate from `cells6.S` for the reason `p5support.S` gives
 * beside it: `cells6.S` is a function of `tools/isa-toolchain.tsv` and
 * `tcpay.py emit --check` fails if one byte of it was not generated, so a
 * framework routine living there would have to be generated too -- and a
 * generator that emits hand-written code is a generator nobody can check.
 *
 * 🔴 `rlx_status_write` IS COMPILED OUT OF EVERY DEVICE BUILD.  `RLX_CLEAR_BEV`
 * is 1 only under `qemu-run.sh`: qemu's Malta is a 24Kf and comes out of
 * `-kernel` with `Status.BEV` set, which is the one state a payload must not
 * install a handler into.  On the device `probe2` measured `BEV = 0` at the
 * prompt (`CPU-27`, 量 `bench/2026-08-25b`), so there is nothing to clear --
 * and compiling the only writer out is what makes that claim readable from the
 * image instead of from this comment.
 *
 * probe6 has no counterpart to `p5support.S`'s `rlx_mfc0_epc`: it writes no CP0
 * register at all on a device build, so there is none to read back.
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
