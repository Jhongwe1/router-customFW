/* cells.S -- the primitives R1h's cell table needs and that probe1/probe2 do
 * not already carry.
 *
 * NOT NAMED probe3.S, AND THE REASON IS A BUILD FAILURE RATHER THAN TASTE: the
 * Makefile maps `%.S` and `%.c` onto the same `%.o`, so a `probe3.S` beside a
 * `probe3.c` is one object built twice, linked twice, and a page of `multiple
 * definition of` out of the linker.  Measured on the first build of this file.
 *
 * Assembled under `.set noreorder`, `.set noat` and `.set nomacro`, so every
 * instruction here is one I wrote.  `tools/hazlint` gates the build.
 *
 * SIX THINGS IN THIS FILE ARE LOAD-BEARING AND NONE OF THEM IS OBVIOUS.
 *
 * 1. NOTHING HERE TOUCHES THE STACK.
 *    `docs/probe3-cells.md` § 6.5: `rlx_call2_uncached` spills `$31` onto a
 *    KSEG0 stack, and `CCTL 0x001` (`DInval`) invalidates the whole D-cache
 *    WITHOUT writing back.  Under the write-back branch that spill is a dirty
 *    line, `DInval` discards it, the epilogue's `lw $31,0($29)` then reads
 *    pre-writeback DRAM and `jr $31` goes somewhere nobody chose.  That is the
 *    loader's permanent hang with no handler that can help.
 *
 *    So every routine below is a leaf that keeps its return address in a
 *    REGISTER.  `rlx_w_exec` is the only one that calls anything; it moves
 *    `$31` into `$25` at entry and returns with `jr $25`.  `rlx_cctl2` issues
 *    `DWB` and `DInval` as two consecutive `mtc0`s with no memory reference
 *    between them, and the `DWB` is what makes the caller's already-spilled
 *    `$31` safe to reload afterwards.  `c-F` is the cell that decides whether
 *    `DWB` writes back at all, and probe3.c does not run `c-C` if it says no.
 *
 * 2. THE VICTIM IS TWO WORDS AND THE GUARD IS FIRST.
 *    probe1's victim is three words with the patched word at +0 and the guard
 *    at +4.  This inverts it:
 *
 *        +0:  jr    $31                <- THE GUARD, always 0x03E00008
 *        +4:  addiu $2, $0, IMM        <- delay slot, and THE PATCHED WORD
 *
 *    The reason is resolution: an 8-byte victim can sit at 8-byte stride, so
 *    Group W can see an 8-byte line.  A 3-word victim cannot go below 16 bytes,
 *    and at 16 bytes "the line is 16 B" and "the line is 8 B" are one reading.
 *    EVERY probe1 HABIT ABOUT `vaddr + 4` BEING THE GUARD IS NOW WRONG, and
 *    V_NOTVICTIM/V_CORRUPT are re-derived below rather than copied.
 *
 *    The guard being the control-flow word is strictly better than probe1's: a
 *    victim whose guard is intact cannot jump anywhere except back to `$31`,
 *    and the guard is read UNCACHED BEFORE the call.
 *
 *    ⚠️ The patched word is therefore in a BRANCH DELAY SLOT by construction.
 *    M3'' says no PROBED instruction may sit in one, because the handler adds 4
 *    to EPC unconditionally.  `addiu` is not a probed instruction -- nothing
 *    here is asking whether it faults -- and `Cause` is recorded whole, so a
 *    `BD` that happens anyway is visible.
 *
 * 3. NO GPR $12 OR $13 IS USED ANYWHERE IN THIS FILE.
 *    cache.S's rule, kept because this file writes CP0 register 12 and CP0
 *    register 20.  `mtc0 $10, $12` means CP0 register 12; `addu $12, ...` means
 *    general register 12.  A reader checking this against the R3000 or the
 *    LX4189 Status figure should not have to hold that distinction in their
 *    head.  `$1` IS used, which is what `.set noat` is for, and it is used only
 *    where the register budget is exactly full -- each site says so.
 *
 * 4. AFTER `SAFE_A0`, `$4` IS NEVER WRITTEN AGAIN.
 *    The guard is only a guard while the value is still there.  A routine that
 *    put a loop counter in `$4` after `SAFE_A0` would hand the loader's
 *    `do_reserved` a small integer as a `pt_regs *` -- which is the exact
 *    hazard the macro exists for, reintroduced by the code that installed it.
 *    The first draft of this file did that in `rlx_w_exec`.
 *
 * 5. THE ARENA IS GENERATED AT RUN TIME AND THE GATE STILL COVERS ITS WORDS.
 *    victims.S's argument -- "a payload that built its victim instructions at
 *    run time would be handing the instruction decoder something `hazlint`
 *    never scanned" -- is preserved rather than waived.  The two words are
 *    ASSEMBLED HERE, in `.text`, gated with everything else, and `rlx_w_arm`
 *    COPIES them.  What the gate does not see is the replication, and a
 *    replication introduces no instruction.  The immediate the experiment
 *    rewrites is sixteen bits of an `addiu`, which cannot introduce a hazard.
 *
 * 6. `mfc3` AND `cache` ARE EMITTED AS RAW WORDS.
 *    `-march=mips1` refuses both mnemonics.  Opcode 0x13 is COP3 on MIPS-I --
 *    this unit's own kernel contains four `mtc3` at 0x8000227C..0x800022E8 --
 *    and opcode 0x2F is the MIPS-II `cache`, whose retirement on this core is
 *    the whole of question (c).  Both are written out with their encodings
 *    derived beside them.  They are the only instructions in this payload
 *    outside MIPS-I and `tools/test-rlxprobe.sh` names every one of them.
 */

#include "rlxdefs.h"
#include "rlxasm.h"

	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* ---------------------------------------------------------------------------
 * THE VICTIM TEMPLATE.  Two words, assembled here, copied by rlx_w_arm.
 *
 * It is `.globl` and it is never called at this address: probe3.c reads it as
 * DATA through KSEG1 and rlx_w_arm copies it into the arena.  Executing it here
 * would return RLX_VICTIM_OLD, which is harmless and is not what it is for.
 * ------------------------------------------------------------------------- */
	.align	3
	.globl	rlx_vic_template
rlx_vic_template:
	jr	$31				/* +0 THE GUARD  0x03E00008 */
	addiu	$2, $0, RLX_VICTIM_OLD		/* +4 delay slot, THE PATCHED WORD */
	.globl	rlx_vic_template_end
rlx_vic_template_end:

/* ---------------------------------------------------------------------------
 * CP0 Status.  THREE ROUTINES, AND THEY ARE THE ONLY WRITERS OF CP0 12 IN THIS
 * PAYLOAD -- `tools/test-rlxprobe.sh` counts the `mtc0 $x,$12` in the emitted
 * image and names the routines they are in.
 *
 * probe2 contains none at all, by its own audit requirement.  probe3 must
 * contain some: Group M sets `CU3` because CP3 is unreachable without it (讀,
 * this unit's kernel at 0x8000221C, and LX4189 § 2.4 -- "a Coprocessor Unusable
 * Exception is taken if these instructions are executed ... and the Cu0 bit is
 * 0 in the CP0 STATUS register"), and Group S sets `IsC` because reading that
 * bit is what ⓓ② is.
 *
 * The nop counts are the sources' own.  The CP0 write hazard on this core is
 * C-9 and is NOT established; these are copied, not reasoned about.
 * ------------------------------------------------------------------------- */

/* u32 rlx_status_or(u32 orbits) -- OR bits into Status, return the PREVIOUS
 * value so the caller can restore it exactly.  Group M holds CU3 across a whole
 * cell, so set and restore are separate calls here. */
	.globl	rlx_status_or
	.ent	rlx_status_or
	.type	rlx_status_or, @function
rlx_status_or:
	addu	$8, $4, $0		/* t0 = orbits, taken out of a0 BEFORE
					 * SAFE_A0 overwrites it */
	SAFE_A0
	mfc0	$9, $12
	nop
	nop
	or	$10, $9, $8
	mtc0	$10, $12
	nop
	nop
	nop
	jr	$31
	addu	$2, $9, $0		/* delay slot: return the OLD Status */
	.end	rlx_status_or

/* void rlx_status_write(u32 v) -- restore. */
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

/* u32 rlx_status_poke(u32 orbits, u32 *out_ks1)
 *
 *      out[0] = Status on entry
 *      out[1] = Status read back WITH orbits set
 *      out[2] = Status after the restore
 *
 * Cell `s-isc`.  THERE IS NO LOAD AND NO STORE BETWEEN THE SET AND THE CLEAR,
 * and that is M5 rather than tidiness: probe1 cell 4 measured `07` CORRUPT on
 * both victims, `240222b2 -> 000222b2`, because stores issued while `IsC` was
 * set reached DRAM on this core.  The three results are held in registers
 * across the isolated window and written afterwards.
 *
 * `out_ks1` must be a KSEG1 pointer.  The payload reads it straight back and
 * this project does not read a cached alias of a word it just wrote uncached.
 * ------------------------------------------------------------------------- */
	.globl	rlx_status_poke
	.ent	rlx_status_poke
	.type	rlx_status_poke, @function
rlx_status_poke:
	addu	$8, $4, $0		/* t0 = orbits */
	addu	$9, $5, $0		/* t1 = out, KSEG1 */
	SAFE_A0
	mfc0	$10, $12		/* t2 = entry value */
	nop
	nop
	or	$11, $10, $8
	mtc0	$11, $12		/* --- the isolated window opens --- */
	nop
	nop
	nop
	mfc0	$14, $12		/* t6 = the read-back */
	nop
	nop
	mtc0	$10, $12		/* --- and closes.  No memory reference
					 *     between those two mtc0s.       --- */
	nop
	nop
	nop
	mfc0	$15, $12		/* t7 = after the restore */
	nop
	nop
	sw	$10, 0($9)
	sw	$14, 4($9)
	sw	$15, 8($9)
	jr	$31
	addu	$2, $14, $0		/* delay slot */
	.end	rlx_status_poke

/* ---------------------------------------------------------------------------
 * CP3 read stubs -- cell `m-imem`.
 *
 *      mfc3 rt, rd  =  (0x13 << 26) | (0 << 21) | (rt << 16) | (rd << 11)
 *                   =  0x4C000000 | (rt << 16) | (rd << 11)
 *
 * rt = $2 gives 0x4C020000 | (rd << 11).  Opcode 0x13 is COP3 in MIPS-I; the
 * MIPS-II reallocation of that opcode to COP1X does not apply to a core
 * measured to have Config.M = 0 (量, probe2, `bench/2026-08-25b/H2a.log`).
 *
 * Cross-checked against this unit's own kernel, which writes the same
 * coprocessor: `mtc3 t0,$0` at 0x8000227C is the MT form, rs = 4.
 *
 * Eight stubs, three words each, so probe3.c reaches stub n at
 * `rlx_cp3_stubs + n * 12` -- the same arithmetic exc.S's CP0 stubs use, and
 * `tools/test-rlxprobe.sh` checks it against the emitted image rather than
 * trusting it.  $0/$1 are IMEMBASE/IMEMTOP and $4/$5 are DMEMBASE/DMEMTOP by
 * the third-party `lxregs.h`'s naming; $2/$3/$6/$7 are read because a register
 * that answers where no source names one is worth more than a blank.
 *
 * ⚠️ The LX4189 has NO CP3 registers for this: its IMEM/DMEM base and top are
 * hardwired configuration pins (`CFG_IWBASE[31:10]`, `CFG_IWTOP[17:10]`,
 * § 5.4).  This SoC's core exposes them to software, which the kernel proves by
 * writing them -- so the CP3 numbering has ONE source (the third-party
 * `lxregs.h`) plus this unit's own behaviour, and the core vendor's document
 * does not corroborate it.
 * ------------------------------------------------------------------------- */
	.macro	CP3STUB rd
	.word	0x4C020000 | (\rd << 11)
	jr	$31
	nop
	.endm

	.align	4
	.globl	rlx_cp3_stubs
rlx_cp3_stubs:
	CP3STUB	0
	CP3STUB	1
	CP3STUB	2
	CP3STUB	3
	CP3STUB	4
	CP3STUB	5
	CP3STUB	6
	CP3STUB	7
	.globl	rlx_cp3_stubs_end
rlx_cp3_stubs_end:

/* ---------------------------------------------------------------------------
 * u32 rlx_lw_unc_primed(u32 addr, u32 prime)
 *
 * One uncached load, with the destination primed BEFORE it.  probe2's rule:
 * F50b spent a seating on "reads zero" being indistinguishable from "the
 * destination was never written".
 * ------------------------------------------------------------------------- */
	.globl	rlx_lw_unc_primed
	.ent	rlx_lw_unc_primed
	.type	rlx_lw_unc_primed, @function
rlx_lw_unc_primed:
	addu	$8, $4, $0
	lui	$9, KSEG1_BIT>>16
	or	$8, $8, $9
	addu	$2, $5, $0		/* the prime, before the load */
	SAFE_A0
	lw	$2, 0($8)
	nop				/* LOAD DELAY SLOT -- do not remove */
	jr	$31
	nop
	.end	rlx_lw_unc_primed

/* ---------------------------------------------------------------------------
 * Group T -- the SoC timer as an instrument.
 *
 * `TC0CNT`'s COUNT FIELD IS BITS 31:4, NOT THE WHOLE WORD.  量, REG-05: this
 * unit's `TC0DATA` reads 0x0022E0A0 = 142,858 << 4, exactly the compiled-in
 * image value, so the shift is measured on silicon rather than assumed.  Every
 * routine below returns and stores RAW WORDS and shifts nothing.  probe3.c does
 * the >> 4, because a raw reading survives a verdict function that is later
 * found wrong and a shifted one does not.
 *
 * The counter wraps every 142,858 ticks = 9.9998 ms and THE MODULUS IS NOT A
 * POWER OF TWO, so `after - before` masked to 28 bits is wrong.  Every window
 * in this payload stays under 3 ms and probe3.c carries the one-wrap fixup.
 *
 * BOTH DESTINATIONS ARE PRIMED in every bracket, with the two families probe2
 * established.  Priming with zero would be worse than not priming: 0 - 0 = 0,
 * and a zero delta is one of the answers these cells hunt.
 * ------------------------------------------------------------------------- */

/* u32 rlx_tc_spin(u32 spins, u32 *raw_ks1) -- cell `t-cal`.
 *
 * THE LOOP BODY IS THREE INSTRUCTIONS AND MUST STAY THREE.  CLK-03's first
 * experiment measured f/CPI against exactly this shape; adding an instruction
 * inside the loop would silently move a published number. */
	.globl	rlx_tc_spin
	.ent	rlx_tc_spin
	.type	rlx_tc_spin, @function
rlx_tc_spin:
	addu	$14, $4, $0		/* t6 = spins, out of a0 before SAFE_A0 */
	addu	$15, $5, $0		/* t7 = raw, KSEG1 */
	SAFE_A0
	lui	$9, RLX_TC0CNT>>16
	ori	$9, $9, RLX_TC0CNT&0xffff
	lui	$8, 0xc0de
	ori	$8, $8, 0x7c00		/* prime for "before" */
	lui	$10, 0xd1ce
	ori	$10, $10, 0x7c00	/* prime for "after"  */
	lw	$8, 0($9)
	nop				/* LOAD DELAY SLOT */
1:
	addiu	$14, $14, -1
	bne	$14, $0, 1b
	nop				/* delay slot, filled by hand */
	lw	$10, 0($9)
	nop				/* LOAD DELAY SLOT */
	sw	$8, 0($15)
	sw	$10, 4($15)
	subu	$2, $10, $8
	jr	$31
	nop
	.end	rlx_tc_spin

/* u32 rlx_tc_reads(u32 k, u32 *raw_ks1) -- cell `t-ovh`.
 *
 * K iterations of {one uncached read, three ALU/branch}.  The slope over K is
 * the cost of one ITERATION, not of one read alone, and probe3.c reports it
 * that way.  A slope of exactly 0 cannot occur under tick quantisation and is
 * therefore not a refutation -- the first draft of the cell named it as one,
 * which is a condition that cannot fire. */
	.globl	rlx_tc_reads
	.ent	rlx_tc_reads
	.type	rlx_tc_reads, @function
rlx_tc_reads:
	addu	$14, $4, $0
	addu	$15, $5, $0
	SAFE_A0
	lui	$9, RLX_TC0CNT>>16
	ori	$9, $9, RLX_TC0CNT&0xffff
	lui	$8, 0xc0de
	ori	$8, $8, 0x7b00
	lui	$10, 0xd1ce
	ori	$10, $10, 0x7b00
	lw	$8, 0($9)
	nop				/* LOAD DELAY SLOT */
1:
	lw	$11, 0($9)
	addiu	$14, $14, -1		/* does not read $11 -- see hazlint */
	bne	$14, $0, 1b
	nop				/* delay slot, filled by hand */
	lw	$10, 0($9)
	nop				/* LOAD DELAY SLOT */
	sw	$8, 0($15)
	sw	$10, 4($15)
	subu	$2, $10, $8
	jr	$31
	nop
	.end	rlx_tc_reads

/* u32 rlx_tc_walk(u32 base, u32 passes, u32 *raw_ks1) -- cell `t-hit`.
 *
 * 256 loads at 16-byte stride = a 4 KiB footprint, `passes` times, bracketed.
 * THE ITERATION COUNT CARRIES N AND THE FOOTPRINT DOES NOT: after the caller's
 * discarded warming pass every cached access is a hit, so the KSEG0 leg
 * measures RESIDENCY rather than miss latency.  A single sweep of a working set
 * larger than the cache measures miss latency in both windows and is not a
 * residency instrument at all.
 *
 * `base` is a whole address, so the caller passes the KSEG0 alias for one leg
 * and the KSEG1 alias for the other and nothing else differs. */
	.globl	rlx_tc_walk
	.ent	rlx_tc_walk
	.type	rlx_tc_walk, @function
rlx_tc_walk:
	addu	$14, $4, $0		/* t6 = base */
	addu	$15, $5, $0		/* t7 = passes */
	addu	$24, $6, $0		/* t8 = raw, KSEG1 */
	SAFE_A0
	lui	$9, RLX_TC0CNT>>16
	ori	$9, $9, RLX_TC0CNT&0xffff
	lui	$8, 0xc0de
	ori	$8, $8, 0x7a00
	lui	$10, 0xd1ce
	ori	$10, $10, 0x7a00
	lw	$8, 0($9)
	nop				/* LOAD DELAY SLOT */
2:
	addu	$11, $14, $0		/* p = base */
	addiu	$25, $0, 256		/* 256 loads x 16 B = 4 KiB */
3:
	lw	$3, 0($11)
	addiu	$11, $11, 16		/* does not read $3 */
	addiu	$25, $25, -1
	bne	$25, $0, 3b
	nop				/* delay slot, filled by hand */
	addiu	$15, $15, -1
	bne	$15, $0, 2b
	nop				/* delay slot, filled by hand */
	lw	$10, 0($9)
	nop				/* LOAD DELAY SLOT */
	sw	$8, 0($24)
	sw	$10, 4($24)
	subu	$2, $10, $8
	jr	$31
	nop
	.end	rlx_tc_walk

/* ---------------------------------------------------------------------------
 * Groups W and V -- the two eviction walks.
 *
 * THE CONTROL BLOCK, in words, and every access to it goes through KSEG1:
 *
 *      0  base        arena base for this sweep point, KSEG0
 *      1  stride      bytes between victims / targets
 *      2  count       how many
 *      3  bmp         KSEG1 pointer to the nibble bitmap, or 0 for none
 *      4  n_fresh     out
 *      5  n_other     out -- void-prime, weird, not-a-victim, corrupt
 *      6  weird       out -- the RAW value of the first victim that returned
 *                    neither constant.  A bitmap cannot carry it and it is the
 *                    one thing a nibble genuinely loses.
 *      7  weird_seen  out -- 0 or 1, because a weird value of 0 is possible
 *      8  reserved
 *      9  tmpl        KSEG1 address of rlx_vic_template
 *
 * n_stale is NOT returned: it is count - n_fresh - n_other, exact arithmetic in
 * C rather than a third counter.  WHICH victim went bad is not returned either
 * -- probe3.c reads it out of the bitmap, which is already there.  Both of
 * those are register-budget decisions and both are stated because a reader
 * would otherwise look for the fields.
 *
 * ⚠️ WHAT THE NIBBLE LOSES, STATED RATHER THAN LEFT TO BE NOTICED.  probe1's
 * eight-word row carries `ex` -- the value the victim actually returned -- so a
 * verdict can be re-derived at the desk if the verdict FUNCTION is later found
 * wrong.  A nibble carries the verdict alone.  What is kept instead is word 6:
 * the raw value of the FIRST victim whose return matched neither constant,
 * which is the only case where the nibble and the value disagree about
 * anything.  The sixteen named rows reconstruct `ex` from the nibble and say so
 * in the block; `ma` and `g` in those rows are read back from DRAM, which does
 * not move, and are raw.
 *
 * THE OFFSET-LIST FORMS take a second block: word 0 is the number of offsets
 * and words 1..n are byte offsets from `base`.  The sweeps use the stride form
 * because 2,048 offsets is 8 KiB of table; the pattern cells (`w-line`,
 * `w-back`, `w-back2`, `v-line`) use the list form because their offsets are
 * deliberately irregular.
 * ------------------------------------------------------------------------- */

#define CTL_BASE	0
#define CTL_STRIDE	4
#define CTL_COUNT	8
#define CTL_BMP		12
#define CTL_NFRESH	16
#define CTL_NOTHER	20
#define CTL_WEIRD	24
#define CTL_WEIRDSEEN	28
#define CTL_TMPL	36

/* void rlx_w_arm(u32 ctl_ks1, u32 list_ks1)
 *
 * Write the two-word template into every slot, THROUGH KSEG1.  `list_ks1` is 0
 * for the stride form.  This is the half of the re-arm that rewrites memory;
 * the caller follows it with `CCTL 0x002`, which is M2 and is measured. */
	.globl	rlx_w_arm
	.ent	rlx_w_arm
	.type	rlx_w_arm, @function
rlx_w_arm:
	addu	$24, $4, $0		/* ctl */
	addu	$25, $5, $0		/* list, or 0 */
	SAFE_A0
	lw	$8, CTL_BASE($24)
	lw	$9, CTL_STRIDE($24)
	lw	$11, CTL_COUNT($24)
	lw	$10, CTL_TMPL($24)
	lui	$14, KSEG1_BIT>>16
	or	$8, $8, $14		/* every store goes through KSEG1 */
	lw	$2, 0($10)		/* template word 0 -- the guard */
	lw	$3, 4($10)		/* template word 1 -- addiu OLD */
	beq	$25, $0, .Larm_stride
	nop
	/* --- list form: block base + list[1 + i] --- */
	addiu	$25, $25, 4		/* skip the count word; the caller has
					 * already put it in CTL_COUNT */
	addu	$15, $8, $0		/* t7 = block base, KSEG1 */
.Larm_list:
	lw	$7, 0($25)
	nop				/* LOAD DELAY SLOT */
	addu	$6, $15, $7
	sw	$2, 0($6)
	sw	$3, 4($6)
	addiu	$25, $25, 4
	addiu	$11, $11, -1
	bne	$11, $0, .Larm_list
	nop				/* delay slot, filled by hand */
	jr	$31
	nop
.Larm_stride:
	sw	$2, 0($8)
	sw	$3, 4($8)
	addu	$8, $8, $9
	addiu	$11, $11, -1
	bne	$11, $0, .Larm_stride
	nop				/* delay slot, filled by hand */
	jr	$31
	nop
	.end	rlx_w_arm

/* void rlx_w_patch(u32 ctl_ks1, u32 list_ks1)
 *
 * Store the NEW word into every slot's PATCHED WORD, at +4, through KSEG1.
 * The guard at +0 is never written here, so a guard that has changed by the
 * time `rlx_w_exec` reads it is DRAM corruption and not this routine. */
	.globl	rlx_w_patch
	.ent	rlx_w_patch
	.type	rlx_w_patch, @function
rlx_w_patch:
	addu	$24, $4, $0
	addu	$25, $5, $0
	SAFE_A0
	lw	$8, CTL_BASE($24)
	lw	$9, CTL_STRIDE($24)
	lw	$11, CTL_COUNT($24)
	lui	$14, KSEG1_BIT>>16
	lui	$2, RLX_VICTIM_WORD_NEW>>16
	ori	$2, $2, RLX_VICTIM_WORD_NEW&0xffff
	or	$8, $8, $14
	beq	$25, $0, .Lpat_stride
	nop
	addiu	$25, $25, 4
	addu	$15, $8, $0
.Lpat_list:
	lw	$7, 0($25)
	nop				/* LOAD DELAY SLOT */
	addu	$6, $15, $7
	sw	$2, 4($6)
	addiu	$25, $25, 4
	addiu	$11, $11, -1
	bne	$11, $0, .Lpat_list
	nop
	jr	$31
	nop
.Lpat_stride:
	sw	$2, 4($8)
	addu	$8, $8, $9
	addiu	$11, $11, -1
	bne	$11, $0, .Lpat_stride
	nop
	jr	$31
	nop
	.end	rlx_w_patch

/* u32 rlx_w_exec(u32 ctl_ks1, u32 list_ks1)
 *
 * Execute every victim and classify what it returned.  Returns n_fresh; both
 * counters and the bitmap go in the control block.
 *
 * THE NIBBLE CODING, and it is probe1's verdict numbering so one table reads
 * both payloads:
 *
 *      0  never written    -- the block was poisoned and nothing wrote here
 *      1  V_STALE          executed OLD
 *      2  V_FRESH          executed NEW
 *      4  V_VOIDPRIME      it came back holding the prime, so the victim's own
 *                          instruction never executed
 *      5  V_NOTVICTIM      the guard word was wrong BEFORE the call, so it was
 *                          never called
 *      6  V_WEIRD          executed neither constant and it is not the prime
 *      7  V_CORRUPT        the guard word changed ACROSS the call
 *
 * The guard is read uncached before AND after every call.  That costs two
 * uncached loads per victim and it is what stands between a bad arena write and
 * a jump to an address nobody chose -- the loader's permanent hang, one power
 * cycle, no spare device.
 *
 * REGISTER BUDGET, because it is exactly full and the next edit will hit it:
 *
 *      $24 ctl   $25 saved $31   $11 list ptr   $8 victim addr   $9 stride
 *      $14 bmp   $15 remaining   $10 nibbles held   $5 n_fresh   $6 n_other
 *      $7 the guard constant, loaded once     $1 nibble accumulator
 *      $2 $3 temporaries
 *
 * `$4` is SAFE_A0's and is never written after it.  `$12`/`$13` are not used.
 * `$1` is used because `.set noat` is in force and fourteen registers is what
 * there is.  The guard constant lives in `$7` FOR THE WHOLE ROUTINE precisely
 * so that the check across the call needs only one temporary and `$2` -- the
 * victim's return value -- survives it.
 * ------------------------------------------------------------------------- */
	.globl	rlx_w_exec
	.ent	rlx_w_exec
	.type	rlx_w_exec, @function
rlx_w_exec:
	addu	$24, $4, $0		/* ctl */
	addu	$11, $5, $0		/* list, or 0 -- out of a1 before SAFE_A0 */
	SAFE_A0
	addu	$25, $31, $0		/* OUR return address, in a register */
	lw	$8, CTL_BASE($24)	/* victims execute CACHED, so KSEG0 */
	lw	$9, CTL_STRIDE($24)
	lw	$14, CTL_BMP($24)
	lw	$15, CTL_COUNT($24)
	lui	$7, RLX_VIC_GUARD>>16
	ori	$7, $7, RLX_VIC_GUARD&0xffff
	addu	$5, $0, $0		/* n_fresh */
	addu	$6, $0, $0		/* n_other */
	addu	$10, $0, $0		/* nibbles held in the accumulator */
	addu	$1, $0, $0		/* accumulator */
	beq	$11, $0, .Lwe_loop
	nop
	addiu	$11, $11, 4		/* list form: skip the count word */
.Lwe_loop:
	beq	$11, $0, .Lwe_guard
	nop
	lw	$3, 0($11)		/* list form: offset */
	lw	$2, CTL_BASE($24)
	nop				/* LOAD DELAY SLOT */
	addu	$8, $2, $3
	addiu	$11, $11, 4
.Lwe_guard:
	/* ---- the guard, read UNCACHED, BEFORE anything is called ---- */
	lui	$3, KSEG1_BIT>>16
	or	$3, $8, $3
	lw	$2, 0($3)
	nop				/* LOAD DELAY SLOT */
	bne	$2, $7, .Lwe_notvic
	nop

	/* ---- call it.  The prime goes in the jump's delay slot, which is
	 *      rlx_call0_primed's trick: $v0 carries a value the victim could
	 *      not produce, so "it did not run" says so instead of returning
	 *      whatever the last computation left. ---- */
	jalr	$31, $8
	addiu	$2, $0, -1		/* DELAY SLOT: the prime, 0xFFFFFFFF */

	/* ---- the guard again, ACROSS the call.  $2 must survive, which is
	 *      why the constant is in $7 and not rebuilt here. ---- */
	lui	$3, KSEG1_BIT>>16
	or	$3, $8, $3
	lw	$3, 0($3)
	nop				/* LOAD DELAY SLOT */
	bne	$3, $7, .Lwe_corrupt
	nop

	addiu	$3, $0, RLX_VICTIM_OLD
	beq	$2, $3, .Lwe_stale
	nop
	addiu	$3, $0, RLX_VICTIM_NEW
	beq	$2, $3, .Lwe_fresh
	nop
	addiu	$3, $0, -1
	beq	$2, $3, .Lwe_void	/* it came back holding the prime */
	nop
	/* V_WEIRD -- and this is the ONE case a nibble cannot carry, so the raw
	 * value of the first one is kept in the control block. */
	lw	$3, CTL_WEIRDSEEN($24)
	nop				/* LOAD DELAY SLOT */
	bne	$3, $0, .Lwe_weird
	nop
	sw	$2, CTL_WEIRD($24)
	addiu	$3, $0, 1
	sw	$3, CTL_WEIRDSEEN($24)
.Lwe_weird:
	addiu	$3, $0, 6
	beq	$0, $0, .Lwe_pack
	addiu	$6, $6, 1		/* delay slot: n_other++ */
.Lwe_void:
	addiu	$6, $6, 1
	beq	$0, $0, .Lwe_pack
	addiu	$3, $0, 4		/* delay slot: V_VOIDPRIME */
.Lwe_stale:
	beq	$0, $0, .Lwe_pack
	addiu	$3, $0, 1		/* delay slot: nibble = V_STALE */
.Lwe_fresh:
	addiu	$5, $5, 1
	beq	$0, $0, .Lwe_pack
	addiu	$3, $0, 2		/* delay slot: nibble = V_FRESH */
.Lwe_notvic:
	addiu	$6, $6, 1
	beq	$0, $0, .Lwe_pack
	addiu	$3, $0, 5		/* delay slot: V_NOTVICTIM */
.Lwe_corrupt:
	addiu	$6, $6, 1
	addiu	$3, $0, 7		/* V_CORRUPT */
.Lwe_pack:
	sll	$1, $1, 4
	or	$1, $1, $3
	addiu	$10, $10, 1
	andi	$3, $10, 7
	bne	$3, $0, .Lwe_next
	nop
	beq	$14, $0, .Lwe_next
	nop
	sw	$1, 0($14)
	addiu	$14, $14, 4
	addu	$1, $0, $0
.Lwe_next:
	addiu	$15, $15, -1
	beq	$15, $0, .Lwe_flush
	nop
	bne	$11, $0, .Lwe_loop	/* list form: $8 is recomputed there */
	nop
	beq	$0, $0, .Lwe_loop
	addu	$8, $8, $9		/* delay slot: stride form advances $8 */
.Lwe_flush:
	/* ---- flush a partial nibble word ---- */
	andi	$3, $10, 7
	beq	$3, $0, .Lwe_out
	nop
	beq	$14, $0, .Lwe_out
	nop
	addiu	$2, $0, 8
	subu	$2, $2, $3
	sll	$2, $2, 2
	sllv	$1, $1, $2
	sw	$1, 0($14)
.Lwe_out:
	sw	$5, CTL_NFRESH($24)
	sw	$6, CTL_NOTHER($24)
	jr	$25
	addu	$2, $5, $0		/* delay slot: return n_fresh */
	.end	rlx_w_exec

/* ---------------------------------------------------------------------------
 * Group V -- the D side.  Same control block, but the targets are DATA WORDS
 * and the observation is a cached LOAD, not a call.
 *
 * NO UNCACHED READ OF A TARGET APPEARS ANYWHERE IN THESE ROUTINES, and that is
 * not caution.  LX4189 § 5.2, the core vendor's own document: *"if the affected
 * memory location has an alias in uncacheable (KSEG1) space ... perform an
 * uncached read of the affected memory locations.  If the location is resident
 * in the data cache it will be invalidated."*  An uncached guard read of the
 * kind rlx_w_exec does on the I side would invalidate the very line Group V is
 * measuring.  There is no guard word to read here anyway -- a data target is
 * one word -- so the constraint costs nothing.
 *
 * There is also NO STACK REFERENCE, for a second and independent reason:
 * `_stack_top` sits around 0x8052xxxx and the arena at 0x80A1xxxx.  Those are
 * congruent modulo 8 KiB, so in a direct-mapped 8 KiB D-cache -- the exact
 * geometry this walk exists to test -- a driver's own spills would evict the
 * working set it is measuring.
 * ------------------------------------------------------------------------- */

/* void rlx_v_store(u32 ctl_ks1, u32 word) -- uncached-store `word` into every
 * target.  Used for both the arm (OLD) and the patch (NEW) passes. */
	.globl	rlx_v_store
	.ent	rlx_v_store
	.type	rlx_v_store, @function
rlx_v_store:
	addu	$24, $4, $0
	addu	$2, $5, $0		/* the word */
	SAFE_A0
	lw	$8, CTL_BASE($24)
	lw	$9, CTL_STRIDE($24)
	lw	$11, CTL_COUNT($24)
	lui	$14, KSEG1_BIT>>16
	or	$8, $8, $14
	nop
.Lvs_loop:
	sw	$2, 0($8)
	addu	$8, $8, $9
	addiu	$11, $11, -1
	bne	$11, $0, .Lvs_loop
	nop
	jr	$31
	nop
	.end	rlx_v_store

/* void rlx_v_touch(u32 ctl_ks1, u32 unused) -- cached-load every target.  THIS
 * IS THE ALLOCATE, and it is a separate pass so that the read which measures is
 * never the read which fills. */
	.globl	rlx_v_touch
	.ent	rlx_v_touch
	.type	rlx_v_touch, @function
rlx_v_touch:
	addu	$24, $4, $0
	SAFE_A0
	lw	$8, CTL_BASE($24)	/* KSEG0 -- cached */
	lw	$9, CTL_STRIDE($24)
	lw	$11, CTL_COUNT($24)
	nop				/* LOAD DELAY SLOT */
.Lvt_loop:
	lw	$2, 0($8)
	addu	$8, $8, $9		/* does not read $2 */
	addiu	$11, $11, -1
	bne	$11, $0, .Lvt_loop
	nop
	jr	$31
	nop
	.end	rlx_v_touch

/* u32 rlx_v_read(u32 ctl_ks1, u32 list_ks1) -- cached-load every target and
 * classify it.  Same nibble coding as rlx_w_exec, minus the two guard verdicts,
 * which have no meaning for a data word.
 *
 * Register budget: $24 ctl, $25 accumulator, $11 list, $8 addr, $9 stride,
 * $14 bmp, $15 remaining, $10 nibbles held, $5 n_fresh, $6 n_other,
 * $7 = the OLD word, $1 = the NEW word, $2/$3 temporaries.  `$25` is free here
 * because nothing is called: this routine issues loads and nothing else. */
	.globl	rlx_v_read
	.ent	rlx_v_read
	.type	rlx_v_read, @function
rlx_v_read:
	addu	$24, $4, $0
	addu	$11, $5, $0		/* list, or 0 */
	SAFE_A0
	lw	$8, CTL_BASE($24)
	lw	$9, CTL_STRIDE($24)
	lw	$14, CTL_BMP($24)
	lw	$15, CTL_COUNT($24)
	lui	$7, RLX_VICTIM_WORD_OLD>>16
	ori	$7, $7, RLX_VICTIM_WORD_OLD&0xffff
	lui	$1, RLX_VICTIM_WORD_NEW>>16
	ori	$1, $1, RLX_VICTIM_WORD_NEW&0xffff
	addu	$5, $0, $0
	addu	$6, $0, $0
	addu	$10, $0, $0
	addu	$25, $0, $0
	beq	$11, $0, .Lvr_loop
	nop
	addiu	$11, $11, 4
.Lvr_loop:
	beq	$11, $0, .Lvr_read
	nop
	lw	$3, 0($11)
	lw	$2, CTL_BASE($24)
	nop				/* LOAD DELAY SLOT */
	addu	$8, $2, $3
	addiu	$11, $11, 4
.Lvr_read:
	addiu	$2, $0, -1		/* prime: a faulting load leaves it */
	lw	$2, 0($8)		/* THE MEASUREMENT -- cached */
	nop				/* LOAD DELAY SLOT */
	beq	$2, $7, .Lvr_stale
	nop
	beq	$2, $1, .Lvr_fresh
	nop
	addiu	$3, $0, -1
	beq	$2, $3, .Lvr_void	/* the load did not write its destination */
	nop
	lw	$3, CTL_WEIRDSEEN($24)
	nop				/* LOAD DELAY SLOT */
	bne	$3, $0, .Lvr_weird
	nop
	sw	$2, CTL_WEIRD($24)
	addiu	$3, $0, 1
	sw	$3, CTL_WEIRDSEEN($24)
.Lvr_weird:
	addiu	$3, $0, 6		/* V_WEIRD */
	beq	$0, $0, .Lvr_pack
	addiu	$6, $6, 1
.Lvr_void:
	addiu	$6, $6, 1
	beq	$0, $0, .Lvr_pack
	addiu	$3, $0, 4		/* V_VOIDPRIME */
.Lvr_stale:
	beq	$0, $0, .Lvr_pack
	addiu	$3, $0, 1
.Lvr_fresh:
	addiu	$5, $5, 1
	addiu	$3, $0, 2
.Lvr_pack:
	sll	$25, $25, 4
	or	$25, $25, $3
	addiu	$10, $10, 1
	andi	$3, $10, 7
	bne	$3, $0, .Lvr_next
	nop
	beq	$14, $0, .Lvr_next
	nop
	sw	$25, 0($14)
	addiu	$14, $14, 4
	addu	$25, $0, $0
.Lvr_next:
	addiu	$15, $15, -1
	beq	$15, $0, .Lvr_flush
	nop
	bne	$11, $0, .Lvr_loop
	nop
	beq	$0, $0, .Lvr_loop
	addu	$8, $8, $9
.Lvr_flush:
	andi	$3, $10, 7
	beq	$3, $0, .Lvr_out
	nop
	beq	$14, $0, .Lvr_out
	nop
	addiu	$2, $0, 8
	subu	$2, $2, $3
	sll	$2, $2, 2
	sllv	$25, $25, $2
	sw	$25, 0($14)
.Lvr_out:
	sw	$5, CTL_NFRESH($24)
	sw	$6, CTL_NOTHER($24)
	jr	$31
	addu	$2, $5, $0
	.end	rlx_v_read

/* ---------------------------------------------------------------------------
 * Group C -- coherence.  Four sequences, each one leaf routine, each entered
 * through KSEG1 by rlx_call2_uncached, each with NO STACK REFERENCE AT ALL.
 *
 * THE CONTROL BLOCK, in words, KSEG1 throughout:
 *
 *      0  x_ks0     the target, cached alias
 *      1  x_ks1     the target, uncached alias
 *      2  p0        the first value
 *      3  p1        the second
 *      4  cmd1      CCTL command, or 0 for none
 *      5  cmd2      CCTL command, or 0 for none -- issued back to back with
 *                   cmd1, no memory reference between them
 *      6  drain     an unrelated uncached address for c-E0, or 0
 *      7  drain_n   how many reads of it
 *      8  out l1
 *      9  out l2
 *     10  out l3
 *
 * `cmd1`/`cmd2` are DATA, not code, so one routine covers c-A, c-A0, c-F, c-B
 * and c-C, and the treatment that separates them is a word in a block the
 * result names.  That is deliberate: five near-identical asm routines would be
 * five places for one of them to drift.
 * ------------------------------------------------------------------------- */

#define CC_XKS0		0
#define CC_XKS1		4
#define CC_P0		8
#define CC_P1		12
#define CC_CMD1		16
#define CC_CMD2		20
#define CC_DRAIN	24
#define CC_DRAINN	28
#define CC_L1		32
#define CC_L2		36
#define CC_L3		40

/* void rlx_c_seq(u32 cc_ks1, u32 do_load1)
 *
 *      uncached-store p0
 *      [cached-load  x -> l1]          THE ALLOCATE, skipped for c-A0
 *      uncached-store p1               the stand-in for the engine
 *      [treatment: cmd1, then cmd2]
 *      cached-load   x -> l2           THE MEASUREMENT
 *      uncached-load x -> l3           did the second store land at all
 *
 * The `l3` read is LAST for a reason found in the core vendor's own document.
 * LX4189 § 5.2: an uncached read of a location resident in the data cache
 * INVALIDATES that line.  So the uncached read has to come after `l2`, or it
 * destroys the state `l2` is measuring. */
	.globl	rlx_c_seq
	.ent	rlx_c_seq
	.type	rlx_c_seq, @function
rlx_c_seq:
	addu	$24, $4, $0		/* cc */
	addu	$25, $5, $0		/* do_load1 */
	SAFE_A0
	lw	$8, CC_XKS0($24)
	lw	$9, CC_XKS1($24)
	lw	$10, CC_P0($24)
	lw	$11, CC_P1($24)
	lw	$14, CC_CMD1($24)
	lw	$15, CC_CMD2($24)
	nop				/* LOAD DELAY SLOT */

	sw	$10, 0($9)		/* uncached-store p0 */
	addiu	$2, $0, -1		/* l1 prime */
	beq	$25, $0, .Lcs_nol1
	nop
	lw	$2, 0($8)		/* CACHED LOAD -- THE ALLOCATE */
	nop				/* LOAD DELAY SLOT */
.Lcs_nol1:
	sw	$2, CC_L1($24)
	sw	$11, 0($9)		/* uncached-store p1 */

	beq	$14, $0, .Lcs_meas	/* the treatment */
	nop
	mtc0	$0, $20
	nop
	mtc0	$14, $20
	nop
	nop
	mtc0	$0, $20
	nop
	beq	$15, $0, .Lcs_meas
	nop
	mtc0	$15, $20		/* NO memory reference between the two
					 * commands -- see the head of this file */
	nop
	nop
	mtc0	$0, $20
	nop
.Lcs_meas:
	addiu	$2, $0, -1
	lw	$2, 0($8)		/* CACHED LOAD -- THE MEASUREMENT */
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L2($24)
	addiu	$3, $0, -1
	lw	$3, 0($9)		/* uncached load, and it comes LAST */
	nop				/* LOAD DELAY SLOT */
	sw	$3, CC_L3($24)
	jr	$31
	nop
	.end	rlx_c_seq

/* void rlx_c_seq_e(u32 cc_ks1, u32 unused) -- cells c-E, c-E0 and c-E2.
 *
 *      uncached-store p0
 *      cached-load   x -> l1           the allocate
 *      cached-store  p1                A WRITE HIT on a resident line -- the
 *                                      case no probe1 cell exercised
 *      [drain_n uncached reads of `drain`]      c-E0's write-buffer control
 *      [cmd1]                                   c-E2's CCTL 0x100
 *      uncached-load x -> l3           THE MEASUREMENT
 *
 * EACH OF THE THREE CELLS RUNS THIS WHOLE SEQUENCE, and that is a correction
 * rather than duplication.  The cell table had c-E0 and c-E2 continuing from
 * c-E's state; LX4189 § 5.2 says c-E's own final uncached read invalidates the
 * line, so by the time c-E2 issued its `DWB` there would be no dirty line left
 * and its `P0` reading would have been recorded as *"0x100 does not write
 * back"* -- a refutation of the command produced by the running order.
 *
 * The write buffer c-E0 exists to control for is documented: LX4189 § 5.6,
 * *"Writes that are serviced by the data cache may require extra time to be
 * serviced by the LBC if its write buffer is full"*. */
	.globl	rlx_c_seq_e
	.ent	rlx_c_seq_e
	.type	rlx_c_seq_e, @function
rlx_c_seq_e:
	addu	$24, $4, $0
	SAFE_A0
	lw	$8, CC_XKS0($24)
	lw	$9, CC_XKS1($24)
	lw	$10, CC_P0($24)
	lw	$11, CC_P1($24)
	lw	$14, CC_CMD1($24)
	lw	$15, CC_DRAIN($24)
	lw	$25, CC_DRAINN($24)
	nop				/* LOAD DELAY SLOT */

	sw	$10, 0($9)		/* uncached-store p0 */
	addiu	$2, $0, -1
	lw	$2, 0($8)		/* cached load -- the allocate */
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L1($24)
	sw	$11, 0($8)		/* CACHED STORE -- the write hit */

	beq	$15, $0, .Lce_cmd	/* the drain, c-E0 only */
	nop
	beq	$25, $0, .Lce_cmd
	nop
.Lce_drain:
	lw	$3, 0($15)
	addiu	$25, $25, -1		/* does not read $3 */
	bne	$25, $0, .Lce_drain
	nop
.Lce_cmd:
	beq	$14, $0, .Lce_meas	/* the CCTL, c-E2 only */
	nop
	mtc0	$0, $20
	nop
	mtc0	$14, $20
	nop
	nop
	mtc0	$0, $20
	nop
.Lce_meas:
	addiu	$3, $0, -1
	lw	$3, 0($9)		/* UNCACHED LOAD -- THE MEASUREMENT */
	nop				/* LOAD DELAY SLOT */
	sw	$3, CC_L3($24)
	jr	$31
	nop
	.end	rlx_c_seq_e

/* void rlx_c_seq_g(u32 cc_ks1, u32 unused) -- cell c-G, and it exists because
 * the core vendor's own document makes a claim nothing here had tested.
 *
 * LX4189 § 5.2: *"perform an uncached read of the affected memory locations.
 * If the location is resident in the data cache it will be invalidated."*  ⓑ
 * asks what on this core can invalidate a clean line; that sentence answers it
 * with no CCTL at all, and if it holds here `R6` gets a per-line invalidate
 * primitive for the price of a load.
 *
 *      uncached-store p0
 *      cached-load   x -> l1           the allocate
 *      uncached-store p1
 *      uncached-load x -> l2           THE CLAIMED INVALIDATOR
 *      cached-load   x -> l3           THE MEASUREMENT
 *
 * l3 = p1 -> the uncached read invalidated the line.  l3 = p0 -> it did not,
 * and this core does not do what the LX4189 document says its family does.
 * Readable only where c-A was positive: with no stale line there is nothing to
 * invalidate and both outcomes read the same. */
	.globl	rlx_c_seq_g
	.ent	rlx_c_seq_g
	.type	rlx_c_seq_g, @function
rlx_c_seq_g:
	addu	$24, $4, $0
	SAFE_A0
	lw	$8, CC_XKS0($24)
	lw	$9, CC_XKS1($24)
	lw	$10, CC_P0($24)
	lw	$11, CC_P1($24)
	nop				/* LOAD DELAY SLOT */

	sw	$10, 0($9)
	addiu	$2, $0, -1
	lw	$2, 0($8)		/* cached load -- the allocate */
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L1($24)
	sw	$11, 0($9)		/* uncached-store p1 */
	addiu	$2, $0, -1
	lw	$2, 0($9)		/* UNCACHED READ -- the claimed invalidator */
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L2($24)
	addiu	$3, $0, -1
	lw	$3, 0($8)		/* CACHED LOAD -- THE MEASUREMENT */
	nop				/* LOAD DELAY SLOT */
	sw	$3, CC_L3($24)
	jr	$31
	nop
	.end	rlx_c_seq_g

/* void rlx_c_seq_d(u32 cc_ks1, u32 unused) -- cell c-D.  rlx_c_seq's shape with
 * one MIPS-II `cache 0x11` over the line instead of a CCTL command.  Run only
 * if `x-11` retired: this is the second time the instruction executes, and the
 * first time was the one that decided whether it can. */
	.globl	rlx_c_seq_d
	.ent	rlx_c_seq_d
	.type	rlx_c_seq_d, @function
rlx_c_seq_d:
	addu	$24, $4, $0
	SAFE_A0
	lw	$8, CC_XKS0($24)
	lw	$9, CC_XKS1($24)
	lw	$10, CC_P0($24)
	lw	$11, CC_P1($24)
	nop				/* LOAD DELAY SLOT */

	sw	$10, 0($9)
	addiu	$2, $0, -1
	lw	$2, 0($8)
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L1($24)
	sw	$11, 0($9)
	/* cache 0x11, 0($8):  (0x2F << 26) | (8 << 21) | (0x11 << 16) */
	.word	0xBD110000
	nop
	nop
	addiu	$2, $0, -1
	lw	$2, 0($8)		/* THE MEASUREMENT */
	nop				/* LOAD DELAY SLOT */
	sw	$2, CC_L2($24)
	addiu	$3, $0, -1
	lw	$3, 0($9)
	nop				/* LOAD DELAY SLOT */
	sw	$3, CC_L3($24)
	jr	$31
	nop
	.end	rlx_c_seq_d

/* ---------------------------------------------------------------------------
 * Group X -- the `cache` instruction, and the reserved encoding.
 *
 * THE FIRST `cache` INSTRUCTION THIS PROJECT HAS EVER EXECUTED.  probe3.c
 * writes each cell's row into the result block BEFORE calling one of these,
 * exactly as probe1 does, because 否證 ⓒ says a `cache` that neither retires
 * nor traps -- the payload hangs -- refutes the handler and not the instruction.
 *
 *      cache op, 0(base)  =  (0x2F << 26) | (base << 21) | (op << 16) | offset
 *
 * base is $8, so the constant part is 0xBC000000 | (8 << 21) = 0xBD000000.
 * ------------------------------------------------------------------------- */
	.macro	CACHEOP name, op
	.globl	\name
	.ent	\name
	.type	\name, @function
\name:
	addu	$8, $4, $0		/* the address, out of a0 before SAFE_A0 */
	SAFE_A0
	.word	0xBD000000 | (\op << 16)
	nop
	nop
	jr	$31
	nop
	.end	\name
	.endm

	CACHEOP	rlx_x_cache10, 0x10		/* Hit Invalidate I / Lexra IInval  */
	CACHEOP	rlx_x_cache11, 0x11		/* Hit Invalidate D / Lexra DInval  */
	CACHEOP	rlx_x_cache15, 0x15		/* Hit WB Invalidate D / DWBInval   */
	CACHEOP	rlx_x_cache19, 0x19		/* Hit Writeback D / DWB            */

/* void rlx_x_ri(void) -- SPECIAL with function 0x0E.
 *
 * Unassigned in MIPS-I and still unassigned in MIPS32r2 (0x0A movz, 0x0B movn,
 * 0x0C syscall, 0x0D break, 0x0F sync).  量(qemu): it traps with
 * Cause.ExcCode = 0x0A.  量: zero occurrences in this unit's `stage2.bin`, with
 * the scanner's control being the two `rfe`s the same grep does find.
 *
 * ⚠️ IT MAY RETIRE HERE, AND THAT WOULD BE A FINDING RATHER THAN A FAILURE.
 * The binutils Lexra patch adds more than a hundred proprietary mnemonics to
 * these cores and this project has not downloaded it yet (R2c).  If SPECIAL
 * 0x0E is one of them, this instruction is a Lexra ASE operation and it
 * retires, and the RI path stays unproven -- which `h-brk` already licenses
 * around, because the handler branches on nothing (M3').
 *
 * DO NOT USE `rfe` (0x42000010) AS THE RI CONTROL.  It is RI on qemu and a
 * VALID instruction on this core -- exc.S builds the device return path on it
 * and `stage2.bin` contains two.  It is the INVERSE control.
 * ------------------------------------------------------------------------- */
	.globl	rlx_x_ri
	.ent	rlx_x_ri
	.type	rlx_x_ri, @function
rlx_x_ri:
	SAFE_A0				/* $a0 is caller-saved and this routine
					 * takes no argument */
	.word	0x0000000E
	nop
	nop
	jr	$31
	nop
	.end	rlx_x_ri

/* void rlx_cctl2(u32 cmd1, u32 cmd2)
 *
 * Two CCTL commands back to back inside ONE leaf, with no call, no return and
 * no memory reference between them.  This is `c-C`'s mitigation and § 6.5 of
 * the cell table explains why the version of it that lived outside a single
 * routine would have cost the power cycle: `CCTL 0x001` (`DInval`) invalidates
 * the whole D-cache WITHOUT writing back, so a `$31` spilled to a KSEG0 stack
 * between the two commands is discarded and `jr $31` goes to a wild address.
 *
 * Enter through KSEG1.  `cmd1` is `DWB` and `cmd2` is `DInval`; the caller does
 * not run this at all if `c-F` measured that `DWB` does not write back.
 * ------------------------------------------------------------------------- */
	.globl	rlx_cctl2
	.ent	rlx_cctl2
	.type	rlx_cctl2, @function
rlx_cctl2:
	addu	$8, $4, $0
	addu	$9, $5, $0
	SAFE_A0
	mtc0	$0, $20
	nop
	mtc0	$8, $20
	nop
	nop
	mtc0	$0, $20
	nop
	mtc0	$9, $20
	nop
	nop
	mtc0	$0, $20
	nop
	jr	$31
	nop
	.end	rlx_cctl2
