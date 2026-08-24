/* probe2.c -- R1e on silicon: the CP0 census, under a handler of our own.
 *
 * What it settles
 * ---------------
 *   PRId      CPU-04 -- RLX4181 or RLX5281. Four public sources point at the
 *             4181 family and one product string points at 5281; a reading in
 *             the 5281 range would be worth MORE than one in the 4181 range,
 *             because it would refute a Realtek datasheet and two public kernel
 *             trees at once. probe0 reads it without a handler; this reads it
 *             again beside every other register, which is the corroboration.
 *   Config    Config.M == 0 proves outright that this is not a MIPS32 core.
 *   Config1   cache geometry, FPU present, MMU present -- if it exists at all.
 *   Status    CPU-27, BEV at the prompt, and this payload REFUSES TO INSTALL
 *             anything if it is not 0.
 *   Count(9)  F50b. An R3000-class CP0 has no Count/Compare; they arrive with
 *   Compare   R4000. If Count does not move across a counted loop, R5-0's SoC
 *   (11)      timer driver is a PREREQUISITE rather than a bonus, and R1c loses
 *             its first timing route. A zero is a result here, so the loop
 *             count is reported beside it.
 *   the rest  every rd 0..31 across every sel 0..7: read / trapped / read as 0.
 *
 * The three states are not the same claim, and the census says which it can
 * tell apart
 * ------------------------------------------------------------------------
 * Reading a CP0 register that does not exist is architecturally UNDEFINED, not
 * a trap. So this reports what it saw and nothing more:
 *
 *   TRAP    the handler fired, and Cause's ExcCode says which exception
 *   VALUE   it returned something non-zero -- the register answers
 *   ZERO    it returned 0 without trapping. **This does not distinguish
 *           "implemented and zero" from "not implemented and the bus returned
 *           zero", and nothing in this payload can.** Written as its own state
 *           rather than folded into either of the others.
 *
 * Order, because a fault costs one power cycle
 * --------------------------------------------
 * 1. Read Status with no handler installed. If BEV is not 0, refuse, report,
 *    and stop -- 0x80000080 would be the wrong address and the vectors would be
 *    in boot ROM.
 * 2. Save the 256 bytes at 0x80000000 and 0x80000080 into our own .bss.
 * 3. Install the handler at BOTH vectors, through KSEG1, then flush.
 * 4. `break`. It must trap and it must come back. THAT is the positive control,
 *    and it uses an instruction that traps on every MIPS ever built rather than
 *    a reserved encoding -- whether a reserved encoding traps on this core is
 *    R1a's question and cannot be assumed by the thing that would answer it.
 * 5. Only then, the 256 reads.
 * 6. Restore both vectors from the saved copy, flush, and hand the board back.
 *
 * Step 4 is the one that can end the seating, and it ends it visibly: if the
 * handler did not take, the loader's own reporter prints `Undefined Exception
 * happen.` and hangs. The result block is written through KSEG1 and poisoned at
 * entry, so `DW` after the next power-up shows exactly how far it got.
 */

#include "rlxprobe.h"
#include "rlxdefs.h"

#ifndef RLX_NONCE
#define RLX_NONCE	"3ab0e572"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x3ab0e572u
#endif

#define RB_MAGIC	0x524C5832u	/* 'RLX2' */
#define RB_VERSION	0x00020001u
#define RB_POISON	0xDEADC0DEu
#define RB_HDR		24u
#define RB_CELLS	256u
#define RB_CELLW	2u		/* value, state-and-cause */
#define RB_WORDS	(RB_HDR + RB_CELLS * RB_CELLW + 1u)

/* states, in the low byte of the second word of each row */
#define S_ZERO		0x00u
#define S_VALUE		0x01u
#define S_TRAP		0x02u

#define VEC_UTLB	((u32)RLX_VEC_UTLB)
#define VEC_GENERAL	((u32)RLX_VEC_GENERAL)
#define VEC_BYTES	128u

static u32 rb_ks0;
static u32 rb_ks1;

/* The handler's record: [0] count, [1] Cause, [2] EPC, [3] spare. exc.S forms
 * its address with lui/addiu and ORs KSEG1 in, so this must be a real global. */
u32 rlx_exc_rec[4];

/* SAFE_A0's target -- see cache.S. probe2 links cache.S for rlx_cctl and
 * rlx_call2_uncached, so it owes the same symbol. */
u32 rlx_fault_frame[64];

/* Saved vectors, restored before the board is handed back. 64 words = both
 * vectors. */
static u32 saved_vec[VEC_BYTES * 2u / 4u];

static void rb_put(u32 i, u32 v) { *(volatile u32 *)(rb_ks1 + i * 4u) = v; }
static u32  rb_get(u32 i)        { return *(volatile u32 *)(rb_ks1 + i * 4u); }

static u32 rd_unc(u32 addr)          { return *(volatile u32 *)(addr | KSEG1_BIT); }
static void wr_unc(u32 addr, u32 v)  { *(volatile u32 *)(addr | KSEG1_BIT) = v; }

/* rlx_exc_rec is written by the handler THROUGH KSEG1 -- it has to be, because
 * the handler may run at a moment when nothing has flushed anything.  So every
 * access to it from C goes through KSEG1 as well.  Reading the cached alias of a
 * word an uncached writer just changed is the oldest bug on this kind of part,
 * and it would have shown up here as "the handler never fired" on a run where it
 * fired every time. */
static u32 exc_rec(u32 n)            { return rd_unc((u32)&rlx_exc_rec[n]); }
static void exc_rec_set(u32 n, u32 v){ wr_unc((u32)&rlx_exc_rec[n], v); }

static void field(const char *name, u32 v)
{
	rlx_puts("rlxprobe: ");
	rlx_puts(name);
	rlx_putc('=');
	rlx_puthex32(v);
	rlx_puts("\r\n");
}

/* The flush this payload uses to make the I-cache see the handler it just
 * wrote. It is a BUILD KNOB and not a constant, because which sequence works is
 * exactly what probe1 measures and probe2 must not assume its own answer. The
 * default is the vendor bootcode's own sequence -- D-cache first, then
 * invalidate I -- which c-r3k.c's dated comment explains: the two caches can
 * hold the same address. */
static void flush_for_handler(void)
{
#if RLX_FLUSH_ISC
	rlx_call2_uncached((u32)rlx_isc_inv, VEC_UTLB, VEC_BYTES * 2u);
#else
	rlx_call2_uncached((u32)rlx_cctl, CCTL_DFLUSH_819X, 0u);
	rlx_call2_uncached((u32)rlx_cctl, CCTL_IINV, 0u);
#endif
}

static void copy_vec_out(void)
{
	u32 i;

	for (i = 0; i < VEC_BYTES / 4u; i++) {
		saved_vec[i] = rd_unc(VEC_UTLB + i * 4u);
		saved_vec[i + VEC_BYTES / 4u] = rd_unc(VEC_GENERAL + i * 4u);
	}
}

static void copy_vec_back(void)
{
	u32 i;

	for (i = 0; i < VEC_BYTES / 4u; i++) {
		wr_unc(VEC_UTLB + i * 4u, saved_vec[i]);
		wr_unc(VEC_GENERAL + i * 4u, saved_vec[i + VEC_BYTES / 4u]);
	}
	flush_for_handler();
}

extern u32 rlx_exc_entry[];
extern u32 rlx_exc_end[];
extern u32 rlx_cp0_stubs[];

static u32 install_handler(void)
{
	u32 words = (u32)(rlx_exc_end - rlx_exc_entry);
	u32 i;

	if (words * 4u > VEC_BYTES)
		return 0u;		/* the caller reports it and stops */

	for (i = 0; i < words; i++) {
		wr_unc(VEC_UTLB + i * 4u, rlx_exc_entry[i]);
		wr_unc(VEC_GENERAL + i * 4u, rlx_exc_entry[i]);
	}
	flush_for_handler();
	return words;
}

void rlxprobe_main(void)
{
	u32 pc, status, sum, i, words, before, took, delta;
	u32 traps = 0, values = 0, zeros = 0;

	rb_ks0 = (u32)RLX_RESULT_BASE;
	rb_ks1 = rb_ks0 | (u32)KSEG1_BIT;

	/* MEM-15: this DRAM keeps its contents across a short power-off, so the
	 * previous payload's block reads exactly like this one's. Poison first. */
	for (i = 0; i < RB_WORDS; i++)
		rb_put(i, RB_POISON);

	pc = rlx_pc();

#if RLX_CLEAR_BEV
	/* qemu ONLY. Its 24Kf leaves BEV set after `-kernel`, and BEV set is the
	 * one state this payload refuses to install into -- so without this the
	 * harness would validate the refusal and nothing after it. A device build
	 * has RLX_CLEAR_BEV=0 and tools/test-rlxprobe.sh asserts it. */
	rlx_mtc0_status(rlx_mfc0_status() & ~(u32)ST0_BEV);
	rlx_puts("rlxprobe: WARNING RLX_CLEAR_BEV=1 -- this is a qemu build\r\n");
#endif
	status = rlx_mfc0_status();

	rb_put(0u, RB_MAGIC);
	rb_put(1u, RLX_NONCE_W);
	rb_put(2u, RB_VERSION);
	rb_put(3u, pc);
	rb_put(4u, status);
	rb_put(5u, 0u);			/* handler words, filled below */
	rb_put(6u, 0u);			/* break control: exceptions taken */
	rb_put(7u, 0u);			/* break control: Cause */

	rlx_puts("\r\n*** rlxprobe P2 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("status", status);
	field("vec", VEC_GENERAL);

	/* CPU-27. BEV is bit 22 in the R3000 Status layout. If it is set, the
	 * vectors are in boot ROM and 0x80000080 is the wrong address entirely
	 * -- so this refuses rather than installing into RAM nothing reads. */
	if (status & (u32)ST0_BEV) {
		rlx_puts("rlxprobe: BEV=1 -- vectors are NOT at 0x80000080. "
			 "Refusing to install.\r\n");
		rb_put(23u, 0xBE71BAD1u);
		rb_put(RB_HDR + RB_CELLS * RB_CELLW, 0u);
		rlx_puts("rlxprobe: end\r\n");
		return;
	}

	copy_vec_out();
	for (i = 0; i < 8u; i++)		/* the first eight saved words, */
		rb_put(8u + i, saved_vec[i]);	/* so the restore is checkable */

	words = install_handler();
	rb_put(5u, words);
	field("handler_words", words);
	if (words == 0u) {
		rlx_puts("rlxprobe: handler does not fit in 128 bytes\r\n");
		rlx_puts("rlxprobe: end\r\n");
		return;
	}

	/* THE POSITIVE CONTROL. If this does not come back, the loader's own
	 * reporter prints and the board hangs -- which is an observation, not a
	 * silence. */
	exc_rec_set(0u, 0u);
	exc_rec_set(1u, 0u);
	exc_rec_set(2u, 0u);
	rlx_do_break();
	rb_put(6u, exc_rec(0u));
	rb_put(7u, exc_rec(1u));
	field("break.count", exc_rec(0u));
	field("break.cause", exc_rec(1u));
	field("break.epc", exc_rec(2u));
	if (exc_rec(0u) == 0u) {
		/* It returned WITHOUT the handler running. On MIPS-I `break`
		 * traps unconditionally, so this is not a property of the core
		 * -- it is the census's instrument reporting that it is not
		 * installed, and a census run under it would report absences
		 * that are its own. */
		rlx_puts("rlxprobe: break did not trap -- the handler is NOT "
			 "live. Census abandoned.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		return;
	}

	/* The census. 32 registers x 8 selects, each through its own stub. */
	for (i = 0; i < RB_CELLS; i++) {
		u32 v, state;

		before = exc_rec(0u);
		v = rlx_call0((u32)rlx_cp0_stubs + i * 12u);
		took = exc_rec(0u) - before;

		if (took) {
			/* bits 12:8 carry ExcCode, from Cause bits 6:2. */
			state = S_TRAP | ((exc_rec(1u) & 0x7Cu) << 6);
			traps++;
		} else if (v) {
			state = S_VALUE;
			values++;
		} else {
			state = S_ZERO;
			zeros++;
		}
		rb_put(RB_HDR + i * RB_CELLW + 0u, v);
		rb_put(RB_HDR + i * RB_CELLW + 1u, state);

		/* Over the UART, only the rows a reader would look at: every
		 * select-0 register, and anything that answered at a non-zero
		 * select. The block has all 256 either way, and `DW` is what
		 * recovers them. A 256-line report at 38400 is 20 KB and five
		 * seconds of exactly the exposure P9-12 was lost to. */
		if ((i & 7u) == 0u || state != S_ZERO) {
			rlx_puts("rlxprobe: cp0 ");
			rlx_puthex32(i);
			rlx_putc(' ');
			rlx_puthex32(v);
			rlx_putc(' ');
			rlx_puthex32(state);
			rlx_puts("\r\n");
		}
	}

	field("traps", traps);
	field("values", values);
	field("zeros", zeros);

	/* F50b. 100,000 iterations of a two-instruction loop; if Count runs at
	 * anything near the timer base it moves by hundreds of thousands, and if
	 * it is not implemented it does not move at all. The spin count is
	 * reported so that a zero delta cannot be confused with a zero loop. */
	delta = rlx_count_delta(100000u);
	field("count.spins", 100000u);
	field("count.delta", delta);
	rb_put(16u, 100000u);
	rb_put(17u, delta);

	copy_vec_back();

	/* Prove the restore, from memory rather than from intent: read the first
	 * eight words back and compare against what was saved. */
	sum = 0u;
	for (i = 0; i < 8u; i++)
		if (rd_unc(VEC_GENERAL + i * 4u) != saved_vec[i + VEC_BYTES / 4u])
			sum++;
	field("restore.mismatch", sum);

	sum = 0u;
	for (i = 0; i < RB_HDR + RB_CELLS * RB_CELLW; i++)
		sum += rb_get(i);
	rb_put(RB_HDR + RB_CELLS * RB_CELLW, sum);
	field("sum", sum);

	rlx_puts("rlxprobe: end\r\n");
}
