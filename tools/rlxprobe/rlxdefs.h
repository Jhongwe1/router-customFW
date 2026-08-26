/* rlxdefs.h -- constants shared between the C and the assembly of rlxprobe.
 *
 * NOTHING BUT #define IN THIS FILE.  It is included from `.S` sources, which go
 * through the C preprocessor and then straight into the assembler: a
 * declaration, a typedef or a comment-free C statement in here becomes
 * assembler input and fails in a way that reads like a toolchain fault.
 * `rlxprobe.h` holds the declarations and is not safe to include from `.S`.
 */
#ifndef RLXDEFS_H
#define RLXDEFS_H

/* --- the patched instruction --------------------------------------------- */

/* Each victim's first word is `addiu $2, $0, imm` -- opcode 0x09, rs = 0,
 * rt = 2 -- so the whole word is 0x2402_iiii and the experiment rewrites the
 * low sixteen bits.  Both immediates are positive, so `addiu`'s sign extension
 * returns them unchanged and the value in $2 is the immediate itself.
 *
 * The two differ in nine bits.  A pair differing in one bit would make a single
 * flipped bit in DRAM indistinguishable from the result the cell is looking
 * for, and MEM-16 measured that this DRAM's uninitialised bias is 89.5%
 * reproducible rather than random -- so bit-level accidents are a live category
 * here, not a theoretical one. */
#define RLX_VICTIM_OLD		0x11A1
#define RLX_VICTIM_NEW		0x22B2
#define RLX_VICTIM_WORD_OLD	0x240211A1
#define RLX_VICTIM_WORD_NEW	0x240222B2

/* 1 KiB apart, sixteen of them.  cache.S explains why a cell uses slots k and
 * k+7 and not k and k+1. */
#define RLX_VICTIM_STRIDE	0x400
#define RLX_VICTIM_SLOTS	16
#define RLX_VICTIM_PAIR_GAP	7

/* --- CP0 Status, R3000 layout -------------------------------------------- */
/* These are the R3000 positions, which is the model CPU-19 records for this
 * core -- NOT the MIPS32 positions.  On a MIPS32 core bit 16 is Config-defined
 * and bit 17 is not IsC at all, so a payload built against the wrong model
 * would set two bits nobody meant to set. */
#define ST0_IEC			0x00000001	/* interrupt enable, current  */
#define ST0_ISC			0x00010000	/* isolate cache              */
#define ST0_SWC			0x00020000	/* swap caches                */
#define ST0_CM			0x00080000	/* cache miss                 */
#define ST0_BEV			0x00400000	/* boot exception vectors     */

/* --- CP0 register 20, Lexra's, called CCTL by inference ------------------- */
/* `notes/cache-model.md` holds the provenance of every one of these.
 * 2026-08-26: the two that used to have no name anywhere have one now, and they
 * turned out not to be cache commands at all -- see the block below. */
#define CCTL_DFLUSH_819X	0x200		/* two sources, agree          */
#define CCTL_IINV		0x002		/* two sources, agree          */
#define CCTL_DFLUSH_865XB	0x001		/* one source                  */
/* 2026-08-26: NAMED, and they were never cache commands.  0x010 fills the
 * 16 KiB local instruction scratchpad from CP3 $0/$1 and stalls the core while
 * it does; 0x020 clears that scratchpad's valid bit so IMEM-region fetches fall
 * through to the I-cache.  Two independent sources: the Lexra LX4189 datasheet
 * sec 5.2, and arch/rlx/include/asm/rlxregs.h:632-633 in the GPL drops this
 * project holds.  notes/cache-model.md owns the table.
 *
 * probe1 and probe2 write NEITHER.  probe3 writes 0x020 as the I-MEM
 * discriminator -- the scratchpad is the same size as the predicted I-cache, so
 * nothing else separates them -- and still does not write 0x010. */
#define CCTL_IMEM0FILL		0x010		/* named 2026-08-26; not written here  */
#define CCTL_IMEM0OFF		0x020		/* named 2026-08-26; probe3 writes this */

/* --- the 16550 --------------------------------------------------------- */
/* THE DEVICE'S ADDRESSES ARE THE DEFAULT AND THE ONLY ONES THAT MATTER.
 * They are knobs for exactly one reason: qemu-system-mips has no 16550 at
 * 0xB8002000, and a harness that cannot print cannot check a harness.
 *
 * On this part the UART registers are FOUR bytes apart with the value in the
 * top byte -- stage 1 writes 0x03000000 to LCR at 0xB800200C, and putchar polls
 * 0xB8002014 for LSR -- so LSR is THR + 0x14, not THR + 5.  qemu's Malta board
 * carries an ordinary ISA 16550 at 0xB80003F8 with one-byte spacing, so there
 * LSR is THR + 5.  Both are expressed as whole addresses rather than as a base
 * plus an offset, because the offset is the part that differs.
 *
 * `tools/rlxprobe/qemu-run.sh` is the only thing that ever overrides them, and
 * what it validates is control flow, never an answer -- qemu interlocks the
 * load delay slot and this core does not. */
#ifndef RLX_UART_THR
#define RLX_UART_THR		0xB8002000
#endif
#ifndef RLX_UART_LSR
#define RLX_UART_LSR		0xB8002014
#endif

/* --- the exception vectors --------------------------------------------- */
/* THE DEVICE'S ADDRESSES ARE THE DEFAULT AND THEY ARE THE R3000 ONES.
 *
 *      0x80000000 .. 0x8000007F   UTLB refill
 *      0x80000080 .. 0x800000FF   general exception
 *
 * Three sources agree and none says 0x80000180 -- see notes/cache-model.md.
 * 0x80000180 is the MIPS32 address and it had reached seven committed sites in
 * this repository until 2026-08-25.
 *
 * They are knobs for one reason, and it is the same reason as the UART: qemu
 * has no MIPS-I core.  qemu-system-mips's Malta board is a 24Kf, a MIPS32 part,
 * whose general vector with BEV=0 IS 0x80000180.  So `qemu-run.sh` overrides
 * this pair, and what it then exercises is the handler install, the `break`
 * control, the 256 stubs and the restore -- the structure, never an answer.
 *
 * NOTHING BUT qemu-run.sh MAY SET THESE.  `tools/test-rlxprobe.sh` asserts that
 * a default build carries the R3000 pair, because a payload silently built for
 * qemu's vector would install a handler into RAM the device never reads and
 * then fault into the loader's permanent hang. */
#ifndef RLX_VEC_UTLB
#define RLX_VEC_UTLB		0x80000000
#endif
#ifndef RLX_VEC_GENERAL
#define RLX_VEC_GENERAL		0x80000080
#endif

/* qemu only, and it is off by default.  qemu's 24Kf comes out of `-kernel` with
 * Status.BEV set, which is the one state probe2 refuses to install into -- so
 * without this the harness validates the refusal and nothing after it. */
#ifndef RLX_CLEAR_BEV
#define RLX_CLEAR_BEV		0
#endif

/* --- address windows ------------------------------------------------------ */
#define KSEG_MASK		0xE0000000
#define KSEG0_BASE		0x80000000
#define KSEG1_BIT		0x20000000

#endif /* RLXDEFS_H */
