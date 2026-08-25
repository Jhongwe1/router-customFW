/* cache.S -- the cache-management primitives R1d has to decide between, and the
 * victim functions it decides them on.
 *
 * Assembled under `.set noreorder`, `.set noat` and `.set nomacro`, so every
 * instruction here is one I wrote.  `tools/hazlint` gates the build.
 *
 * Three things in this file are load-bearing and none of them is obvious.
 *
 * 1. THE FLUSH ROUTINES ARE MEANT TO BE ENTERED THROUGH THEIR KSEG1 ALIAS.
 *    Invalidating the I-cache while executing out of it, or swapping the two
 *    caches while instructions are being fetched from one of them, is the
 *    classic way to fetch garbage.  This unit's own loader does not take that
 *    risk: at 0x804004a8 it takes the address of its own next instruction, ORs
 *    in 0xA0000000 and jumps, and from there it runs uncached
 *    (`notes/cache-model.md`).  `rlx_call2_uncached()` is how a caller does the
 *    same to these routines.  Calling one at its KSEG0 address is not a compile
 *    error and is not checked at run time -- it is the caller's decision, and
 *    probe1.c makes it one way.
 *
 * 2. THE VICTIMS ARE REAL ASSEMBLED CODE, PATCHED IN ONE IMMEDIATE FIELD.
 *    A payload that built its victim instructions at run time would be handing
 *    the instruction decoder something `hazlint` never scanned, which is
 *    exactly the blind spot `hazlint` exists to remove -- upstream's P9-12 came
 *    out of an encoder in `mkramboot.py`, not out of an assembler.  So each
 *    victim is assembled here, gated with everything else, and the experiment
 *    rewrites sixteen bits of one `addiu` immediate.  Sixteen bits of an
 *    immediate cannot introduce a hazard, so the gate's guarantee survives the
 *    patch.
 *
 * 3. NO GPR $12 OR $13 IS USED ANYWHERE IN THIS FILE.  `mtc0 $10, $12` means
 *    CP0 register 12; `addu $12, ...` means general register 12.  Both are
 *    legal, they are different namespaces, and a reader checking this file
 *    against c-r3k.c should not have to hold that distinction in their head.
 */

#include "rlxdefs.h"
#include "rlxasm.h"

	.set	noreorder
	.set	noat
	.set	nomacro

	.text

/* SAFE_A0 lives in `rlxasm.h` now, because `exc.S` needs it too -- see
 * docs/rlxprobe-audit-2026-08-25.md Must-fix 1.  The rationale moved with the
 * macro rather than being summarised in two places. */


/* ---------------------------------------------------------------------------
 * void rlx_cctl(u32 cmd)
 *
 * Write one command to CP0 register 20, using the clear / write / clear idiom
 * that BOTH sources use -- this unit's bootcode at 0x804066c0 and 0x804066e8,
 * and the vendor's linux-2.6.30 c-r3k.c.  `notes/cache-model.md` holds the
 * provenance of every command value; the two this payload writes are the two
 * with two sources agreeing.
 *
 * CP0 register 20 has no meaning in MIPS-I or MIPS32.  Lexra documents a
 * register named CCTL "used to control the instruction and data memories".
 * Calling it CCTL is INFERENCE from that documentation plus the observed
 * behaviour -- neither source states it.
 *
 * The nop counts are the sources' own.  The CP0 write hazard on this core is
 * C-9 and is NOT established; these are copied, not reasoned about.
 * ------------------------------------------------------------------------- */
	.globl	rlx_cctl
	.ent	rlx_cctl
	.type	rlx_cctl, @function
rlx_cctl:
	addu	$8, $4, $0		/* t0 = the command, out of a0 */
	SAFE_A0				/* before the first instruction that could fault */
	mtc0	$0, $20			/* clear */
	nop
	mtc0	$8, $20			/* the command */
	nop
	nop
	mtc0	$0, $20			/* clear */
	nop
	jr	$31
	nop				/* delay slot, filled by hand */
	.end	rlx_cctl

/* ---------------------------------------------------------------------------
 * u32 rlx_mfc0_cctl(void)
 *
 * Read CP0 register 20.  NOBODY HAS EVER READ THIS REGISTER on this part --
 * both sources only ever write it -- so whatever comes back is the first datum
 * anyone has on its read side, and it may be anything, including a fault.
 *
 * probe1 calls this LAST, after every cache cell is already in the result
 * block, so a fault here costs the reading and not the experiment.
 * ------------------------------------------------------------------------- */
	.globl	rlx_mfc0_cctl
	.ent	rlx_mfc0_cctl
	.type	rlx_mfc0_cctl, @function
rlx_mfc0_cctl:
	SAFE_A0				/* this is the ONE instruction here that no
					 * vendor code has ever executed, so it is
					 * the likeliest fault in the payload */
	mfc0	$2, $20
	nop
	nop
	jr	$31
	nop
	.end	rlx_mfc0_cctl

/* ---------------------------------------------------------------------------
 * void rlx_mtc0_status(u32 v) -- the write side uart.S had no reason to have.
 *
 * BUILT ONLY WHEN RLX_CLEAR_BEV IS SET, WHICH IS qemu ONLY, and that is the
 * point rather than a tidy-up.  `probe1` cell 4 measured on 2026-08-25 that
 * `Status.IsC` does NOT isolate on this core: `rlx_isc_inv`'s `sb $0` byte
 * stores reached DRAM and corrupted both victims (`bench/2026-08-25/H1b.log`,
 * `07` CORRUPT, top byte of each word at stride 4).  `probe2` must therefore not
 * touch Status at all -- and "must not" is only a claim until something can
 * check it.  Compiling this routine out of a device build turns it into an
 * assertion about the emitted image: **a device probe2 contains no `mtc0` to
 * CP0 register 12**, which `tools/test-rlxprobe.sh` C1 reads out of the
 * disassembly and C2 shows it can fail.
 * ------------------------------------------------------------------------- */
#if RLX_CLEAR_BEV
	.globl	rlx_mtc0_status
	.ent	rlx_mtc0_status
	.type	rlx_mtc0_status, @function
rlx_mtc0_status:
	addu	$8, $4, $0		/* t0 = the value; a Status word such as
					 * 0x1000FC00 is a kuseg address, which is
					 * exactly the case SAFE_A0 exists for */
	SAFE_A0
	mtc0	$8, $12
	nop
	nop
	nop				/* CP0 write hazard is C-9, unestablished */
	jr	$31
	nop
	.end	rlx_mtc0_status
#endif /* RLX_CLEAR_BEV */

/* ---------------------------------------------------------------------------
 * void rlx_isc_inv(u32 base, u32 len)
 *
 * The OTHER mechanism: the one linux-2.6.30's c-r3k.c uses and this unit's
 * bootcode never does.  `r3k_flush_icache_range()` sets Status.IsC | Status.SwC,
 * clears Status.IEc, byte-stores over the range -- which with the caches
 * isolated and swapped writes cache tags rather than memory -- and restores
 * Status.
 *
 * Two deliberate deviations from c-r3k.c, both because a number it relies on is
 * not established here:
 *
 *   * c-r3k.c strides 0x080 because it knows its line size.  THIS CORE'S LINE
 *     SIZE IS UNKNOWN -- CPU-25 is blank -- so this strides 4, which hits every
 *     line whatever the line size is, at the cost of being slower.  A stride
 *     larger than the line size would skip lines, and the cell would then
 *     report a failed flush that was really a skipped line.
 *   * ENTER THIS THROUGH KSEG1.  With SwC set, data references go to the
 *     I-cache; what instruction fetch does meanwhile is exactly the thing this
 *     core has no documentation for.  Fetching uncached removes the question.
 *
 * DANGER -- AND IT IS NO LONGER A HYPOTHETICAL.  MEASURED 2026-08-25,
 * `bench/2026-08-25/H1b.log` cell 4: **this core does not isolate.**  The
 * `sb $0` stores below reached DRAM and rewrote the top byte of every fourth
 * byte across the range -- `240222b2` -> `000222b2` on the victim and
 * `03e00008` -> `00e00008` on the guard, on BOTH victims, 7 KiB apart.  qemu
 * had found the same failure one day earlier and `probe1`'s `V_CORRUPT` guard
 * is what turned it into a printed verdict instead of a jump into the weeds.
 *
 * So the old wording -- *"if this core does not implement IsC"* -- is settled,
 * and what it settles is that **nothing may point this at a range it does not
 * own.**  probe1 points it only at the victim it is about to overwrite anyway.
 * probe2 pointed it at the exception vector page, which is a range it does not
 * own, and that is why probe2 no longer links this routine at all: `RLX_ISC` is
 * 1 for probe1 and 0 for everything else, set per payload in the Makefile with
 * `override` so it cannot be turned on from a command line.
 * ------------------------------------------------------------------------- */
#if RLX_ISC
	.globl	rlx_isc_inv
	.ent	rlx_isc_inv
	.type	rlx_isc_inv, @function
rlx_isc_inv:
	/* No SAFE_A0 here, and that is a decision rather than an omission: a0 is
	 * already a word-aligned KSEG0 address -- the victim -- and a0 + 148 is
	 * inside the victims region, so `lw a3,148(a0)` in do_reserved reads a
	 * real word.  Adding SAFE_A0 would break the routine, which needs a0. */
	mfc0	$8, $12			/* t0 = Status, saved */
	nop
	nop
	lui	$9, (ST0_ISC|ST0_SWC)>>16
	or	$10, $8, $9		/* t2 = Status | ISC | SWC */
	addiu	$11, $0, -2		/* t3 = ~ST0_IEC = 0xFFFFFFFE */
	and	$10, $10, $11
	addu	$14, $4, $5		/* t6 = end, computed BEFORE isolation */
	mtc0	$10, $12		/* isolate */
	nop
	nop
	nop
1:
	sb	$0, 0($4)		/* the only memory reference while isolated */
	addiu	$4, $4, 4
	bne	$4, $14, 1b
	nop				/* delay slot, filled by hand */

	mtc0	$8, $12			/* restore */
	nop
	nop
	nop
	jr	$31
	nop
	.end	rlx_isc_inv
#endif /* RLX_ISC */

/* ---------------------------------------------------------------------------
 * u32 rlx_r3k_size(u32 base, u32 ca_flags)
 *
 * c-r3k.c's `r3k_cache_size()`, reproduced.  Returns the cache size in BYTES,
 * or 0 when the core does not answer.  `ca_flags` is ST0_ISC for the D-cache
 * and ST0_ISC|ST0_SWC for the I-cache -- c-r3k.c's own convention.
 *
 *   1. isolate; write a marker at base; read it back.  If it does not come back,
 *      or Status.CM is set, the core is not answering: return 0.
 *   2. zero one word at base + k words, k = 32, 64, ... 0x40000.
 *   3. write -1 at base.
 *   4. walk k upward until base + k words reads back non-zero.  That k is where
 *      the cache wrapped onto itself, so k words is the size.
 *
 * Deviation from c-r3k.c: it starts the walk at 128 words and this starts at
 * 32, so a cache smaller than 512 bytes is still reachable.  Starting lower
 * cannot produce a false size -- it can only find a smaller true one.
 *
 * ARMED ONLY WITH RLX_GEOM=1, and it is off by default.  While isolated, a core
 * that does not implement IsC writes real memory over [base, base + 1 MiB].
 * probe1 points this at a scratch window it names in its own report and that
 * the runsheet reads before and after, and it runs after every other result is
 * already in the block, so losing it costs nothing already earned.
 * ------------------------------------------------------------------------- */
#if RLX_GEOM
	.globl	rlx_r3k_size
	.ent	rlx_r3k_size
	.type	rlx_r3k_size, @function
rlx_r3k_size:
	mfc0	$8, $12			/* t0 = Status, saved */
	nop
	nop
	or	$10, $8, $5		/* t2 = Status | ca_flags */
	addiu	$11, $0, -2		/* ~ST0_IEC */
	and	$10, $10, $11
	mtc0	$10, $12
	nop
	nop
	nop

	lui	$9, 0xa5a5
	ori	$9, $9, 0xa5a5		/* t1 = 0xa5a5a5a5 */
	sw	$9, 0($4)
	lw	$14, 0($4)
	nop				/* LOAD DELAY SLOT -- do not remove */
	mfc0	$15, $12		/* t7 = Status, read for CM */
	nop
	nop

	bne	$14, $9, 8f		/* the marker did not come back -> 0 */
	nop
	lui	$24, ST0_CM>>16
	and	$24, $15, $24
	bne	$24, $0, 8f		/* cache miss -> 0 */
	nop

	addiu	$14, $0, 32		/* t6 = k, in words */
	lui	$15, 0x0004		/* t7 = 0x40000 words, the ceiling */
2:
	sll	$24, $14, 2
	addu	$24, $4, $24
	sw	$0, 0($24)
	sll	$14, $14, 1
	sltu	$25, $15, $14
	beq	$25, $0, 2b
	nop

	addiu	$25, $0, -1
	sw	$25, 0($4)		/* base = -1 */

	addiu	$14, $0, 32
3:
	sll	$24, $14, 2
	addu	$24, $4, $24
	lw	$24, 0($24)
	nop				/* LOAD DELAY SLOT -- do not remove */
	bne	$24, $0, 4f		/* wrapped here: k words is the size */
	nop
	sll	$14, $14, 1
	sltu	$25, $15, $14
	beq	$25, $0, 3b
	nop
	addiu	$14, $0, 0		/* never wrapped -> 0 */
4:
	sll	$2, $14, 2		/* words -> bytes */
	beq	$0, $0, 9f
	nop
8:
	addiu	$2, $0, 0
9:
	mtc0	$8, $12			/* restore */
	nop
	nop
	nop
	jr	$31
	nop
	.end	rlx_r3k_size
#endif /* RLX_GEOM */

/* ---------------------------------------------------------------------------
 * u32 rlx_call0_primed(u32 fn, u32 prime)
 * u32 rlx_call2_uncached(u32 fn, u32 arg0, u32 arg1)
 *
 * Call an address.  The second ORs KSEG1 in first, which is what makes the
 * flush routines above run with instruction fetch bypassing the caches.
 *
 * The first takes a PRIME because "the callee returned nothing" and "the callee
 * returned this value" are two different observations and $v0 cannot tell them
 * apart on its own.  See the delay slot below.
 * ------------------------------------------------------------------------- */
	.globl	rlx_call0_primed
	.ent	rlx_call0_primed
	.type	rlx_call0_primed, @function
rlx_call0_primed:
	addiu	$29, $29, -8
	sw	$31, 0($29)
	jalr	$31, $4
	addu	$2, $5, $0		/* DELAY SLOT, AND IT IS THE FIX.
					 *
					 * $v0 is loaded with the caller's prime
					 * BEFORE the callee runs, so a callee
					 * that never writes $v0 returns the
					 * prime rather than whatever the last
					 * unrelated computation left there.
					 *
					 * docs/rlxprobe-audit-2026-08-25.md
					 * Must-fix 4: every CP0 read in probe2
					 * assumes `mfc0` writes `rt`, and that
					 * assumption is what the census exists
					 * to test.  On a trap the destination
					 * is certainly not written -- the
					 * handler advances EPC by 4 and touches
					 * no GPR -- so without a prime a trapped
					 * census row reported whatever $2 held
					 * on entry, which was the running
					 * `zeros` counter: a steadily increasing
					 * small integer that reads like a family
					 * of related registers answering.
					 *
					 * It costs zero instructions: this slot
					 * held a `nop`. */
	lw	$31, 0($29)
	addiu	$29, $29, 8		/* does not read $31 -- see hazlint */
	jr	$31
	nop
	.end	rlx_call0_primed

	.globl	rlx_call2_uncached
	.ent	rlx_call2_uncached
	.type	rlx_call2_uncached, @function
rlx_call2_uncached:
	addiu	$29, $29, -8
	sw	$31, 0($29)
	lui	$8, KSEG1_BIT>>16	/* t0 = 0x20000000, KSEG0 -> KSEG1 */
	or	$8, $4, $8
	addu	$4, $5, $0		/* shuffle down: a0 = arg0 */
	addu	$5, $6, $0		/*               a1 = arg1 */
	jalr	$31, $8
	nop				/* delay slot, filled by hand */
	lw	$31, 0($29)
	addiu	$29, $29, 8
	jr	$31
	nop
	.end	rlx_call2_uncached
