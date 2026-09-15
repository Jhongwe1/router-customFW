/* ucost-cells.S -- the probed words for `R1-pub-4b`, `D-cost`.  HAND WRITTEN.
 *
 * NOT GENERATED, and that is a decision rather than an omission.
 * `tools/isapay.py emit` owns `cells4.S`, whose cells are shaped for ONE
 * execution under a fault handler with eight recorded words; a cost
 * measurement needs the probed word inside a counted loop and NOTHING ELSE
 * inside it.  `cells4.S` may not be modified at all this segment -- it is one
 * of the four files feeding `uprobe`'s `BUILD_ID`, and seating 23's capture
 * printed that digest -- and reusing it would measure its epilogue rather than
 * its probed word.
 *
 * THE ENCODINGS ARE STILL `tools/isa-payload.tsv`'s.  Every `.word` below
 * names the row it must equal and `tools/ucostcheck.py` is what checks it, in
 * BOTH directions, so the exemption list cannot accrete unreported.
 *
 * `.set nomacro` as well as `.set noreorder`: every instruction here is one
 * this file wrote, not one an assembler chose.
 */
	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* Register allocation, identical in every cell:
 *
 *   $4  in: scratch base      $5  in: iteration count
 *   $10 memory operand base   $9  store datum    $2  load destination / seed
 *   $3  the loop counter
 *
 * $3 is never an operand of a probed word, so a probed word that misbehaves
 * cannot destroy the counter.
 *
 * NO LOAD SITS IN A DELAY SLOT, AND NO LOAD IS FOLLOWED BY A READER OF ITS
 * rt.  The probed word's successor is always `addiu $3, $3, -1`, which reads
 * $3 only.  `tools/hazlint` over the LINKED ELF is what says so; this comment
 * is not evidence.  ⚠️ And for the `ll` cell it says LESS than it looks:
 * hazlint's load set is MIPS-I and `ll` is opcode 0x30, so a green gate is
 * not evidence about that one cell.  It is recorded here rather than
 * discovered later.
 *
 * `off` exists for ONE row and it is the row worth the most.  `CPU-15` measured
 * on this die, bare metal, that all four unaligned load/store instructions
 * EXECUTE and compute correctly -- which is what refuted the public record of
 * the Lexra settlement.  `docs/emulation-surface.md` nevertheless lists five
 * unaligned forms among the eight entries on the emulation surface.  Those two
 * readings predict different costs for the same instruction, and the only
 * difference between this cell and its twin is two added to a base register.
 */
	.macro	uc_cell name, wsym, wval, off=0
	.align	4
	.globl	uc_cell_\name
	.ent	uc_cell_\name
	.type	uc_cell_\name, @function
uc_cell_\name:
	addu	$10, $4, $0		/* memory operand base             */
	addiu	$10, $10, \off		/* 0 for every row but lwu2, and
					 * OUTSIDE the loop, so it is
					 * intercept and never slope       */
	lui	$9, 0x5A5A
	ori	$9, $9, 0x0FF2		/* in_b of the `sw` row            */
	lui	$2, 0xDEAD
	ori	$2, $2, 0xBEEF		/* the `seed` column, every row    */
	addu	$3, $5, $0		/* loop counter                    */
	beq	$3, $0, 90f		/* N == 0 runs no body at all      */
	nop				/* DELAY SLOT, filled by hand      */
	.align	4			/* the body is ONE 16-byte I-cache
					 * line.  CPU-25, 量: I-cache 16
					 * KiB, 16-byte lines, 2-way.  Fixing
					 * the alignment removes line
					 * straddle as a difference between a
					 * row and its twin.  The pad is
					 * zeros = nops and executes once,
					 * so it is intercept, not slope.
					 * ⚠️ It does NOT remove index
					 * conflict against the exception
					 * handler's own lines, which no
					 * control here catches. */
1:
	.globl	\wsym
\wsym:
	.word	\wval			/* THE PROBED WORD                 */
	addiu	$3, $3, -1		/* reads $3 only: not the probed
					 * word's rt, so no load-use hazard */
	bne	$3, $0, 1b
	nop				/* DELAY SLOT, filled by hand      */
90:
	jr	$31
	nop				/* DELAY SLOT, filled by hand      */
	.end	uc_cell_\name
	.endm

/* THE TWO ZERO-CONTROL CELLS ARE SEPARATELY ASSEMBLED AT TWO ADDRESSES ON
 * PURPOSE.  `nop_a` minus `nop_b` is simultaneously the zero control and the
 * test of the assumption every other row rests on -- that the loop's own cost
 * cancels between a row and its twin.  A `nop`-against-`lw` comparison cannot
 * do that job: they are different instructions, so a disagreement cannot be
 * told from `lw` genuinely costing more, and a control that cannot fail for
 * exactly one reason is not a control. */
	uc_cell nop_a, uc_w_nop_a, 0x00000000
	uc_cell nop_b, uc_w_nop_b, 0x00000000
	uc_cell sync,  uc_w_sync,  0x0000000F
	uc_cell lw,    uc_w_lw,    0x8D420000
	uc_cell ll,    uc_w_ll,    0xC1420000
	uc_cell sw,    uc_w_sw,    0xAD490000
	uc_cell sc,    uc_w_sc,    0xE1490000
	uc_cell lwu2,  uc_w_lwu2,  0x8D420000, 2
