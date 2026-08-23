/* start.S -- the first instruction the device executes after `J <load addr>`.
 *
 * Nothing here may assume a stack, a $gp, or a zeroed .bss.  The loader jumps;
 * it does not call, so there is no return address worth keeping and no C
 * environment at all until this file makes one.
 *
 * `.set nomacro` throughout: every instruction below is one I wrote.  The
 * two-instruction `lui`/`addiu` pairs are the standard %hi/%lo relocation pair
 * and are written out rather than left to `la`, which is a macro.
 */

	.set	noreorder
	.set	noat
	.set	nomacro

	.section .text.entry, "ax"
	.globl	_start
	.ent	_start
	.type	_start, @function
_start:
	/* Stack.  `_stack_top` is past .bss in the linker script, so the stack
	 * grows down into space this image owns and never into the loader's. */
	lui	$29, %hi(_stack_top)
	addiu	$29, $29, %lo(_stack_top)

	/* Zero .bss.  The loader staged whatever was in RAM before us and none
	 * of it is ours; a C variable that reads as non-zero because the vendor
	 * kernel's image was sitting there is a bug that would look like a
	 * hardware finding. */
	lui	$8, %hi(_bss_start)
	addiu	$8, $8, %lo(_bss_start)
	lui	$9, %hi(_bss_end)
	addiu	$9, $9, %lo(_bss_end)
1:
	beq	$8, $9, 2f
	nop				/* delay slot, filled by hand */
	sw	$0, 0($8)
	beq	$0, $0, 1b
	addiu	$8, $8, 4		/* delay slot: the increment, and it is useful */
2:

	jal	rlxprobe_main
	nop				/* delay slot, filled by hand */

#if RLX_RESET
	/* Hand the board back to the loader without touching the power.  See
	 * uart.S for why this drains the UART first. */
	jal	rlx_reset
	nop				/* delay slot, filled by hand */
#endif

	/* Reached only when RLX_RESET is 0, or if rlx_reset somehow returns --
	 * which would itself be a finding, because it is declared noreturn. */
3:
	beq	$0, $0, 3b
	nop				/* delay slot, filled by hand */
	.end	_start
