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

/* probe3's victim is TWO words and the GUARD IS FIRST -- the inverse of
 * victims.S's layout, and every probe1 habit about `vaddr + 4` being the guard
 * is wrong for it:
 *
 *      +0:  jr    $31                 <- RLX_VIC_GUARD, must never change
 *      +4:  addiu $2, $0, imm         <- delay slot, and THE PATCHED WORD
 *
 * The reason is resolution: an 8-byte victim can be placed at 8-byte stride, so
 * Group W can see an 8-byte line.  A three-word victim cannot go below 16
 * bytes, and at 16 bytes "the line is 16 B" and "the line is 8 B" are the same
 * reading.  probe3.S holds the assembled template; the arena is a copy of it.
 */
#define RLX_VIC_GUARD		0x03E00008	/* jr $31 */
#define RLX_VIC_WORDS		2

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
#define ST0_CU3			0x80000000	/* coprocessor 3 usable       */

/* THE TWO CONTROL BITS `s-isc` SETS BESIDE `IsC`, AND WHY THEY ARE THESE TWO.
 *
 * Without a control bit, *"bit 16 stuck"* and *"Status has no write mask"* are
 * one reading, and the cell answers nothing.  A control bit has to be one this
 * core cannot plausibly implement, so that a 1 in the read-back means the
 * register is an unmasked 32-bit latch.
 *
 * Bit 6 and bit 24, and the core vendor's own document is the first source:
 *
 *   讀  Lexra LX4189 Data Sheet Rel 1.9 sec 3.4.1, the STATUS figure -- fields
 *       27-23, 21-16 and 7-6 are all shown as `0`, and the prose says *"The 0
 *       fields are ignored on write and are 0 on read."*  Both bits are inside
 *       a `0` field.  ⚠️ AND SO IS BIT 16: on the LX4189 there is no `IsC` at
 *       all, which is what makes `bit 16 reads back clear` a PREDICTION for
 *       `s-isc` rather than a blank.  ⚠️ The LX4189 is NOT this core -- Table 2
 *       lists only CP0 8/12/13/14/15/20, so it has no TLB, and this die has 32
 *       TLB entries (量, CPU-08).  It is a sibling, not this part.
 *   讀  arch/rlx/include/asm/rlxregs.h:97, in the GPL drops this project holds,
 *       carries the comment "bits 6 & 7 are reserved on R[23]000" -- Realtek's
 *       own header for this architecture port.  Bit 24 is in the R3000
 *       figure's other reserved run, 24-23.
 *   讀  MIPS32: bit 6 is `SX`, which enables 64-bit supervisor addressing and
 *       exists only on MIPS64; bit 24 is `MX`, the DSP ASE presence bit, a
 *       MIPS32r2 feature.  `Config.M = 0` is 量 on this die, so it is not a
 *       MIPS32 core and neither field can mean anything here.
 *
 * TWO of them rather than one, because one cannot see a PARTIAL write mask.
 * They sit at opposite ends of the register; if they disagree with each other,
 * the mask is not a single contiguous decode, and no single bit could have
 * shown that. */
#define ST0_CTRL_A		0x00000040	/* bit 6  -- LX4189 `0` field 7-6   */
#define ST0_CTRL_B		0x01000000	/* bit 24 -- LX4189 `0` field 27-23 */

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

/* The names `cache-rlx.c` gives the same bits, added 2026-08-26 for probe3.
 * The three above are probe1's names from before that file was read, and they
 * are kept so probe1's emitted code and its comments still agree.  Same values,
 * one table:
 *
 *      0x001 DInval    0x002 IInval    0x100 DWB    0x200 DWB_Inval
 *
 * `0x100` is the one this repository had never recorded at all.  This unit's
 * kernel issues it at 0x8000CA94/0x8000CAC0; ITS LOADER NEVER DOES, and no
 * source here has ever recorded its effect -- which is what cell `c-F`
 * measures, and what cell `c-C` needs before it is safe to run at all.
 *
 * ⚠️ LX4189 sec 5.2 on the CCTL register: *"When reading this register, the
 * contents of the Reserved bits are undefined.  When writing this register, the
 * contents of the Reserved bits should be preserved."*  The clear/write/clear
 * idiom BOTH implementations on this die use cannot preserve anything, and
 * CPU-39 measured CP0 20 reading zero here, so a read-modify-write degenerates
 * to a plain write on this part.  The two facts agree; neither is a licence to
 * assume the LX4189's map is this core's. */
#define CCTL_DINVAL		0x001
#define CCTL_IINVAL		0x002
#define CCTL_DWB		0x100
#define CCTL_DWBINVAL		0x200

/* --- the SoC timer, as an instrument ------------------------------------ */
/* TC0's count register.  量 REG-07 (one reading, 0x0010B960, mid-count),
 * REG-09 (TCCNR = 0xC0000000, so TC0En = 1 and TC0Mode = 1), CLK-04 (the
 * loader's tick advances at 100.0018 Hz over a 2,080 s baseline, which requires
 * the counter to count).
 *
 * 🔴 THE COUNT FIELD IS BITS 31:4.  量 REG-05: TC0DATA reads 0x0022E0A0 =
 * 142,858 << 4, exactly the compiled-in image value.  A payload that subtracts
 * raw words reports ticks x 16 and a wrap 16x too late.  probe3.S returns raw
 * words and probe3.c does the shift, so the block keeps the readings a later
 * correction could re-derive from.
 *
 * 14,286,057 Hz, 69.9983 ns/LSB, wrapping every 142,858 ticks = 9.9998 ms --
 * and 142,858 IS NOT A POWER OF TWO, so a masked subtraction is wrong.
 * 🔴 NOT 14.9650 MHz: that is CLK-08b's WATCHDOG clock, a different clock on
 * the same die, 4.75 % away, and CLK-08b is the row that refuted f_timer/14. */
#define RLX_TC0CNT		0xB8003108

/* --- the memory-mapped SPI window and the controller's clock register ---
 * Group F, 2026-09-01.  `docs/probe3-cells.md` § 6.8.
 *
 * 🔴 THE TWO WINDOW BASES ARE NOT THE SAME DECODE AND THE PAYLOAD MAY NOT
 * ASSUME THEY ALIAS.  RLX_F_WIN is physical 0x1D000000 and RLX_F_BOOT is
 * 0x1FC00000; the second is where this SoC fetches its reset vector and where
 * the loader's stage 1 executes from (讀, § 19.7.2), and NOTHING in this
 * project has ever compared them.  `f-alias` is that comparison; every other
 * cell in the group reports per window.
 *
 * ⚠️ AND NOTHING HAS READ RLX_F_WIN OUTSIDE LINUX.  SPEC.md's FLS-11 and
 * MAP-12 mark the value 量 and cite the loader printing
 * `offset 0x003f0000<0xbd3f0000>` -- but § 20's lui census found `0xbd00`
 * exactly ONCE in the loader and it is that printf's argument, so what the
 * device emitted is a compile-time constant.  The real measurement is the
 * kernel's, 2026-08-31: 4,194,304 bytes through map->virt = 0xbd000000.  At
 * the loader prompt the window is UNDEMONSTRATED, which is what `f-live` is.
 *
 * RLX_SFCR is 量 REG-13: 0x3FC00000 at the prompt, cold and warm alike, so
 * SPI_CLK_DIV = 001B = DIV 4 -- written by stage 2, which writes this register
 * twice, and NOT by stage 1, which writes it zero times in 4,848 bytes.
 *
 * RLX_F_SPAN_MASK bounds every Group F leg to the same 64 KiB whatever its
 * stride.  It is a mask and not a length because the loop can then apply it in
 * one instruction, and it is 64 KiB because RLX_F_BOOT's decode SIZE is
 * measured nowhere in this project -- a leg that walked a megabyte of it would
 * be reading addresses nothing has shown exist. */
#define RLX_F_WIN		0xBD000000
#define RLX_F_BOOT		0xBFC00000
#define RLX_SFCR		0xB8001200
#define RLX_F_SPAN_MASK		0x0000FFFF

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
