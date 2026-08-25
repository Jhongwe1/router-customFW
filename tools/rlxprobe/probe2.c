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
 *             count is reported beside it -- and so is the raw pair, and so is
 *             census row 0x48, which reads the same register a second way.
 *   the rest  every rd 0..31 across every sel 0..7: read / trapped / read as 0
 *             / destination not written / changed between two reads.
 *
 * WHAT CHANGED ON 2026-08-25, AND WHAT EACH ONE COST TO FIND
 * ---------------------------------------------------------
 * `docs/rlxprobe-audit-2026-08-25.md` read this file for the first time and its
 * Must-fix list is `R1g-4b`. Four entries were written against readings; the
 * seating on 2026-08-25 turned every one of their premises into a measurement,
 * and added a fifth entry out of its own result. All five are below, marked
 * where they land.
 *
 *   1  `rlx_do_break` had no SAFE_A0, so the designed visible failure was
 *      silence. `exception_handlers[9] == 0x80400BE8` is now MEASURED (H0b) --
 *      the refutation condition did not fire. Fixed in exc.S.
 *   2  `install_handler` never read the vector back, so "the stores did not
 *      land" and "the core does not fetch there" were one hang. Fixed here:
 *      44 uncached reads, and a positive control on the comparison.
 *   3  p2a and p2b were two indistinguishable binaries. H1 settled the flush,
 *      so there is one binary and the recipe is stamped into a header word and
 *      into the banner.
 *   4  every CP0 read assumed `mfc0` writes `rt`, which is what the census
 *      exists to test. Fixed by priming the destination -- see the census.
 *   5  NEW, out of the seating's own result: `Status.IsC` does not isolate on
 *      this core and its byte stores reached DRAM. **This payload does not
 *      touch Status.** `rlx_isc_inv` is not linked and `rlx_mtc0_status` is not
 *      built, so a device image contains no `mtc0` to CP0 register 12 at all --
 *      an assertion about the emitted words rather than about this comment.
 *
 * The three states were two claims and are now six, and the census says which
 * of them it can tell apart
 * ------------------------------------------------------------------------
 * Reading a CP0 register that does not exist is architecturally UNDEFINED, not
 * a trap. So this reports what it saw and nothing more:
 *
 *   TRAP     the handler fired, and Cause's ExcCode says which exception.
 *   VALUE    both reads returned the same non-zero value -- the register
 *            answers, and it answered the same twice.
 *   ZERO     both reads returned 0 without trapping. **This does not
 *            distinguish "implemented and zero" from "not implemented and the
 *            bus returned zero", and nothing in this payload can.**
 *   NOWRITE  both reads returned THEIR OWN PRIME. `mfc0` retired without
 *            writing its destination register. This is the state the audit's
 *            Must-fix 4 is about and until 2026-08-25 nothing here could see
 *            it: a trapped row reported whatever $v0 held on entry, which was
 *            the running `zeros` counter -- a steadily increasing small integer
 *            that reads like a family of related registers answering.
 *   MOVES    the two reads disagree and neither is a prime. The register
 *            changed between them. **rd 9 is Count, so this state is a second,
 *            independent route to F50b that does not depend on
 *            `rlx_count_delta`'s arithmetic at all.** It is also what a
 *            read-to-clear register looks like, and this payload cannot tell
 *            those two apart -- the rate over a known loop is what does.
 *   MIXED    one read returned its prime and the other did not. Unexplained,
 *            and reported as its own state rather than folded into one that has
 *            an explanation.
 *
 * The two primes are 0xC0DE0000|n and 0xD1CE0000|n, where n is the row -- so a
 * not-written row names itself in a hex dump, and a register that genuinely
 * reads 0xC0DE00nn for its own n would have to do it twice with two different
 * top halves. Both raw words are in the result block whatever the state, so a
 * PARTIAL write -- a core that writes some bits of rt and not others -- is
 * visible even though no state names it.
 *
 * Order, because a fault costs one power cycle
 * --------------------------------------------
 * 1. Read Status with no handler installed. If BEV is not 0, refuse, report,
 *    and stop -- 0x80000080 would be the wrong address and the vectors would be
 *    in boot ROM.
 * 2. Save the 256 bytes at 0x80000000 and 0x80000080 into our own .bss.
 * 3. Install the handler at BOTH vectors, through KSEG1, then flush, THEN READ
 *    ALL 44 WORDS BACK and refuse if any of them is wrong.
 * 4. `break`. It must trap and it must come back. THAT is the positive control,
 *    and it uses an instruction that traps on every MIPS ever built rather than
 *    a reserved encoding -- whether a reserved encoding traps on this core is
 *    R1a's question and cannot be assumed by the thing that would answer it.
 * 5. Only then, the 512 reads.
 * 6. Restore both vectors from the saved copy, flush, check both directions,
 *    and hand the board back.
 *
 * Steps 3 and 4 now decompose a failure that used to be one hang. If the
 * read-back fails, the stores did not land. If the read-back passes and `break`
 * does not come back, the bytes are there and the core did not fetch them --
 * which is the flush, and the flush is `CCTL 0x002` alone because that is what
 * probe1 measured. **So probe2 is a second, independent test of R1d's decision
 * 1, on a different address range and through a different store path**, and it
 * costs nothing to have.
 *
 * MEM-15 is why the block is poisoned before anything else happens: this DRAM
 * keeps its CONTENTS across a short power-off, so a block left by the previous
 * payload reads exactly like this one's.
 */

#include "rlxprobe.h"
#include "rlxdefs.h"

#ifndef RLX_NONCE
#define RLX_NONCE	"3ab0e572"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x3ab0e572u
#endif

/* --- result block --------------------------------------------------------- */

#define RB_MAGIC	0x524C5832u	/* 'RLX2' */
#define RB_VERSION	0x00030001u	/* 2 -> 3: three words per row */
#define RB_POISON	0xDEADC0DEu
#define RB_HDR		40u
#define RB_CELLS	256u
#define RB_CELLW	3u		/* value(prime 1), value(prime 2), state */
#define RB_WORDS	(RB_HDR + RB_CELLS * RB_CELLW + 1u)
#define RB_POISON_W	(RB_WORDS + 8u)	/* a margin, so a run that wrote PAST its
					 * own block shows data where poison was
					 * predicted */

/* Header words. Named rather than numbered at the point of use, because a block
 * layout that exists only as literals inside rb_put() calls is a layout the
 * runsheet cell has to be diffed against by eye. */
#define H_MAGIC		0u
#define H_NONCE		1u
#define H_PROGRESS	2u	/* how far the run got -- see P_* below */
#define H_PC		3u
#define H_VERSION	4u
#define H_FLAGS		5u	/* the build stamp, see FLAGS_W */
#define H_STATUS	6u	/* Status, read before anything is installed */
#define H_VEC		7u
#define H_HWORDS	8u
#define H_INS_CHANGED	9u
#define H_INS_BAD	10u
#define H_INS_FIRSTBAD	11u
#define H_BRK_COUNT	12u
#define H_BRK_CAUSE	13u
#define H_BRK_EPC	14u
#define H_ROWS_DONE	15u
#define H_TRAPS		16u
#define H_VALUES	17u
#define H_ZEROS		18u
#define H_NOWRITE	19u
#define H_MOVES		20u
#define H_MIXED		21u
#define H_CNT_SPINS	22u
#define H_CNT_BEFORE	23u
#define H_CNT_AFTER	24u
#define H_CNT_DELTA	25u
#define H_CNT_TRAPS	26u
#define H_CNT_ROW48	27u
#define H_RES_MISMATCH	28u
#define H_RES_STILLHDL	29u
#define H_STATUS_END	30u
#define H_ROWS_PRINTED	31u
#define H_SAVED0	32u	/* the first eight words of the GENERAL vector */

/* Progress. Written after each stage completes, so a block recovered by `DW`
 * after a hang says where the run stopped, without any inference from what is
 * missing. Poison here means it did not reach the header at all. */
#define P_HEADER	0x10u
#define P_STATUS	0x20u
#define P_SAVED		0x30u
#define P_INSTALLED	0x40u
#define P_BREAK		0x50u
#define P_CENSUS	0x60u
#define P_COUNT		0x70u
#define P_RESTORED	0x80u
#define P_SEALED	0x90u

/* States, in the low byte of the third word of each row. Bits 12:8 carry
 * ExcCode (Cause 6:2) when something trapped; bits 16 and 17 say WHICH pass
 * trapped, because "it traps every time" and "it trapped once" are different
 * claims about a core. */
#define S_ZERO		0x00u
#define S_VALUE		0x01u
#define S_TRAP		0x02u
#define S_NOWRITE	0x03u
#define S_MOVES		0x04u
#define S_MIXED		0x05u
#define S_TRAP1		0x00010000u
#define S_TRAP2		0x00020000u

/* The two primes. See the header comment. `n` is the row, so a not-written row
 * carries its own index and two rows cannot be confused with each other. */
#define PRIME1(n)	(0xC0DE0000u | (n))
#define PRIME2(n)	(0xD1CE0000u | (n))

/* The census row that reads CP0 register 9 select 0 -- Count. rd * 8 + sel. */
#define ROW_COUNT	(9u * 8u + 0u)

/* The flush this payload uses to make the I-cache see the handler it just
 * wrote. IT IS A CONSTANT AND NOT A KNOB, and that is the whole of Must-fix 3.
 *
 * It used to be `RLX_FLUSH_ISC`, and the two builds it produced -- p2a and p2b
 * -- were indistinguishable on both channels: not in a header word, not in a
 * `field()`, not in the banner, not in `make show`, same `rb=`, and the two
 * command lines differed by four characters. The fix is not a `field()`. The fix
 * is that probe1 MEASURED which flush works, so there is one binary.
 *
 * `CCTL 0x002` alone, because that is what was measured: cells 2, 3 and 6 all
 * came back FRESH, a cached store to a line the D-cache does not hold reaches
 * memory unaided (cell 1 against cell 5 on the `ma` column, both 240222b2), and
 * the vendor's D-then-I is therefore unnecessary rather than wrong here.
 * (This comment read "the D-cache is write-through" until 2026-08-26. Both of
 * those cells store to a line the cache does not hold, so that is one reading of
 * the measurement and not the only one -- notes/cache-model.md.) This payload's stores go through KSEG1 anyway,
 * so there is no dirty D-line for a D-flush to write out even in principle.
 *
 * The `Status.IsC` path is not an option any more, at any setting: probe1 cell
 * 4 measured its byte stores reaching DRAM. `rlx_isc_inv` is not linked into
 * this payload. */
#define FLUSH_CMD	CCTL_IINV

/* The build stamp. A build that cannot say what it is cannot be checked from a
 * capture -- which is the half of Must-fix 3 that survives having one binary.
 * 0x50 is 'P', so a zero word is distinguishable from a build with every knob
 * off. A device build reads 0x50010002, and `make show` prints that number from
 * this same expression rather than from a second copy of it. */
#define FLAGS_W		(0x50000000u | ((u32)FLUSH_CMD & 0xFFFFu) \
			 | ((u32)RLX_RESET     << 16) \
			 | ((u32)RLX_CLEAR_BEV << 17) \
			 | ((u32)RLX_RET_ERET  << 18) \
			 | ((u32)RLX_ISC       << 19) \
			 | ((u32)RLX_GEOM      << 20))

/* How many census rows go to the UART. The block carries all 256 either way and
 * `DW` is what recovers them; this bounds the report.
 *
 * The predicate is not a cap on its own -- it prints every select-0 row, and a
 * select != 0 row ONLY when it differs from its own register's select-0 row. If
 * this core ignores the select field, which is what an R3000-class CP0 does,
 * that is exactly 32 lines and `rows.printed` says so. If it decodes select,
 * every row that answered differently prints. The cap is the backstop, and when
 * it bites it reports how many it dropped, because a silent cap reads as
 * coverage. */
#define RB_UART_ROWS	96u

#define VEC_UTLB	((u32)RLX_VEC_UTLB)
#define VEC_GENERAL	((u32)RLX_VEC_GENERAL)
#define VEC_BYTES	128u
#define VEC_WORDS	(VEC_BYTES / 4u)

static u32 rb_ks0;
static u32 rb_ks1;

/* The handler's record: [0] count, [1] Cause, [2] EPC, [3] spare. exc.S forms
 * its address with lui/addiu and ORs KSEG1 in, so this must be a real global. */
u32 rlx_exc_rec[4];

/* SAFE_A0's target used to be defined here and in probe1.c. It moved to
 * report.c on 2026-08-25, when uart.S's CP0 readers gained the guard and probe0
 * -- which links uart.S and neither of the two payloads -- needed it too. */

/* Saved vectors, restored before the board is handed back. 64 words = both
 * vectors: [0 .. 31] UTLB, [32 .. 63] general. */
static u32 saved_vec[VEC_WORDS * 2u];

/* rlx_count_delta writes its two raw readings here, and the payload reads them
 * back through KSEG1 for the same reason the exception record is uncached. */
static u32 count_raw[2];

/* Filled by install_handler(), read by the caller. Three numbers rather than one
 * return value, because "it does not fit", "the bytes are not there" and "the
 * comparison could not have failed" are three different reasons to stop. */
static u32 ins_changed;
static u32 ins_bad;
static u32 ins_firstbad;

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

static void progress(u32 p) { rb_put(H_PROGRESS, p); }

static void field(const char *name, u32 v)
{
	rlx_puts("rlxprobe: ");
	rlx_puts(name);
	rlx_putc('=');
	rlx_puthex32(v);
	rlx_puts("\r\n");
}

static void flush_for_handler(void)
{
	rlx_call2_uncached((u32)rlx_cctl, FLUSH_CMD, 0u);
}

static void copy_vec_out(void)
{
	u32 i;

	for (i = 0; i < VEC_WORDS; i++) {
		saved_vec[i] = rd_unc(VEC_UTLB + i * 4u);
		saved_vec[i + VEC_WORDS] = rd_unc(VEC_GENERAL + i * 4u);
	}
}

static void copy_vec_back(void)
{
	u32 i;

	for (i = 0; i < VEC_WORDS; i++) {
		wr_unc(VEC_UTLB + i * 4u, saved_vec[i]);
		wr_unc(VEC_GENERAL + i * 4u, saved_vec[i + VEC_WORDS]);
	}
	flush_for_handler();
}

extern u32 rlx_exc_entry[];
extern u32 rlx_exc_end[];
extern u32 rlx_cp0_stubs[];

/* Install the handler at both vectors and PROVE THE BYTES ARE THERE.
 *
 * Must-fix 2, and it is the entry that converts one class of power cycle into a
 * printed refusal. Twenty-two words went to 0x80000000 and 0x80000080 through
 * KSEG1 and the next thing that touched the vector was `break` -- so "the stores
 * did not land" and "the core does not fetch there" were the same hang.
 *
 * Nothing in this project had ever WRITTEN physical 0 through KSEG1 before this
 * payload does it 44 times as its first act. What it had done, on 2026-08-25, is
 * READ that page both ways: `H0a3` is `DW A0000080 32` word for word identical
 * to `DW 80000080 32`, so an uncached read of that page is a valid reading of
 * what is in DRAM there. That is what makes the read-back below a check rather
 * than a second guess.
 *
 * `ins_changed` is the positive control on the comparison. The read-back
 * compares 44 words against the array that wrote them, so on its own it can only
 * fail if a store did not land -- but it would also PASS if the loop had written
 * nothing and the vector happened to hold the handler already. Counting how many
 * of the 44 differ from the saved copy is free and makes the check able to fail
 * in the other direction too. A run where ins_changed is 0 has a check that
 * proves nothing, and it says so on the wire. */
static u32 install_handler(void)
{
	u32 words = (u32)(rlx_exc_end - rlx_exc_entry);
	u32 i, got;

	ins_changed = 0u;
	ins_bad = 0u;
	ins_firstbad = 0xFFFFFFFFu;

	if (words * 4u > VEC_BYTES)
		return 0u;		/* the caller reports it and stops */

	for (i = 0; i < words; i++) {
		wr_unc(VEC_UTLB + i * 4u, rlx_exc_entry[i]);
		wr_unc(VEC_GENERAL + i * 4u, rlx_exc_entry[i]);
	}
	flush_for_handler();

	for (i = 0; i < words; i++) {
		got = rd_unc(VEC_UTLB + i * 4u);
		if (got != rlx_exc_entry[i]) {
			ins_bad++;
			if (ins_firstbad == 0xFFFFFFFFu)
				ins_firstbad = i;
		}
		if (got != saved_vec[i])
			ins_changed++;

		got = rd_unc(VEC_GENERAL + i * 4u);
		if (got != rlx_exc_entry[i]) {
			ins_bad++;
			if (ins_firstbad == 0xFFFFFFFFu)
				ins_firstbad = i + words;
		}
		if (got != saved_vec[i + VEC_WORDS])
			ins_changed++;
	}
	return words;
}

/* One census row: two calls, two primes, one verdict. */
static u32 census_row(u32 i, u32 *v1out, u32 *v2out)
{
	u32 v1, v2, before, state, cause = 0u;
	u32 t1 = 0u, t2 = 0u;
	u32 stub = (u32)rlx_cp0_stubs + i * 12u;

	before = exc_rec(0u);
	v1 = rlx_call0_primed(stub, PRIME1(i));
	if (exc_rec(0u) != before) {
		t1 = S_TRAP1;
		cause = exc_rec(1u);
	}

	before = exc_rec(0u);
	v2 = rlx_call0_primed(stub, PRIME2(i));
	if (exc_rec(0u) != before) {
		t2 = S_TRAP2;
		cause = exc_rec(1u);
	}

	*v1out = v1;
	*v2out = v2;

	if (t1 || t2)
		/* bits 12:8 carry ExcCode, from Cause bits 6:2. */
		state = S_TRAP | ((cause & 0x7Cu) << 6) | t1 | t2;
	else if (v1 == PRIME1(i) && v2 == PRIME2(i))
		state = S_NOWRITE;
	else if (v1 == PRIME1(i) || v2 == PRIME2(i))
		state = S_MIXED;
	else if (v1 != v2)
		state = S_MOVES;
	else if (v1 == 0u)
		state = S_ZERO;
	else
		state = S_VALUE;

	return state;
}

void rlxprobe_main(void)
{
	u32 pc, status, sum, i, words, delta;
	u32 traps = 0, values = 0, zeros = 0, nowrite = 0, moves = 0, mixed = 0;
	u32 printed = 0, suppressed = 0;
	u32 base_v1 = 0, base_v2 = 0, base_state = 0;
	u32 row48 = 0xFFFFFFFFu;
	u32 cnt_before, cnt_after, cnt_traps;

	rb_ks0 = (u32)RLX_RESULT_BASE;
	rb_ks1 = rb_ks0 | (u32)KSEG1_BIT;

	/* MEM-15: this DRAM keeps its contents across a short power-off, so the
	 * previous payload's block reads exactly like this one's. Poison first. */
	for (i = 0; i < RB_POISON_W; i++)
		rb_put(i, RB_POISON);

	pc = rlx_pc();

#if RLX_CLEAR_BEV
	/* qemu ONLY. Its 24Kf leaves BEV set after `-kernel`, and BEV set is the
	 * one state this payload refuses to install into -- so without this the
	 * harness would validate the refusal and nothing after it. A device build
	 * has RLX_CLEAR_BEV=0 and tools/test-rlxprobe.sh asserts it.
	 *
	 * THIS IS THE ONLY WRITE TO CP0 Status ANYWHERE IN THIS PAYLOAD, and it
	 * is compiled out of a device build together with the routine that
	 * performs it -- see cache.S. */
	rlx_mtc0_status(rlx_mfc0_status() & ~(u32)ST0_BEV);
	rlx_puts("rlxprobe: WARNING RLX_CLEAR_BEV=1 -- this is a qemu build\r\n");
#endif
	status = rlx_mfc0_status();

	rb_put(H_MAGIC, RB_MAGIC);
	rb_put(H_NONCE, RLX_NONCE_W);
	rb_put(H_VERSION, RB_VERSION);
	rb_put(H_PC, pc);
	rb_put(H_FLAGS, FLAGS_W);
	rb_put(H_STATUS, status);
	rb_put(H_VEC, VEC_GENERAL);
	progress(P_HEADER);

	rlx_puts("\r\n*** rlxprobe P2 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("flags", FLAGS_W);
	field("status", status);
	field("vec", VEC_GENERAL);

	/* CPU-27. BEV is bit 22 in the R3000 Status layout. If it is set, the
	 * vectors are in boot ROM and 0x80000080 is the wrong address entirely
	 * -- so this refuses rather than installing into RAM nothing reads. */
	if (status & (u32)ST0_BEV) {
		rlx_puts("rlxprobe: BEV=1 -- vectors are NOT at 0x80000080. "
			 "Refusing to install.\r\n");
		rlx_puts("rlxprobe: end\r\n");
		return;
	}
	progress(P_STATUS);

	copy_vec_out();
	/* The first eight words of the GENERAL vector, so that a block recovered
	 * from DRAM after a power cycle can be told apart from this run's. Eight
	 * of the general vector and not of the UTLB one, because the general
	 * vector is the one every other number in this block is about. */
	for (i = 0; i < 8u; i++)
		rb_put(H_SAVED0 + i, saved_vec[i + VEC_WORDS]);
	progress(P_SAVED);

	words = install_handler();
	rb_put(H_HWORDS, words);
	rb_put(H_INS_CHANGED, ins_changed);
	rb_put(H_INS_BAD, ins_bad);
	rb_put(H_INS_FIRSTBAD, ins_firstbad);
	field("handler_words", words);
	field("install.changed", ins_changed);
	field("install.bad", ins_bad);
	if (words == 0u) {
		rlx_puts("rlxprobe: handler does not fit in 128 bytes\r\n");
		rlx_puts("rlxprobe: end\r\n");
		return;
	}
	if (ins_bad != 0u) {
		/* Must-fix 2's whole point: this is the branch that used to be
		 * a hang. The bytes are not at the vector, so the core would
		 * fetch whatever is, and `break` would go to the loader. */
		field("install.firstbad", ins_firstbad);
		rlx_puts("rlxprobe: the handler is NOT at the vector -- the "
			 "uncached stores did not land. Refusing to break.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		return;
	}
	if (ins_changed == 0u) {
		/* The read-back passed, and it could not have failed. Not a
		 * reason to stop -- the handler bytes ARE there -- but the
		 * check proved nothing, and a run must not read as if it did. */
		rlx_puts("rlxprobe: WARNING install.changed=0 -- the vector "
			 "already held these words, so the read-back is "
			 "vacuous\r\n");
	}
	progress(P_INSTALLED);

	/* THE POSITIVE CONTROL. If this does not come back, the loader's own
	 * reporter prints and the board hangs -- which is an observation, not a
	 * silence, and it is an observation only because `rlx_do_break` now
	 * carries SAFE_A0. Until 2026-08-25 it did not, and this branch was
	 * measured to produce nothing at all on the wire. */
	exc_rec_set(0u, 0u);
	exc_rec_set(1u, 0u);
	exc_rec_set(2u, 0u);
	rlx_do_break();
	rb_put(H_BRK_COUNT, exc_rec(0u));
	rb_put(H_BRK_CAUSE, exc_rec(1u));
	rb_put(H_BRK_EPC, exc_rec(2u));
	field("break.count", exc_rec(0u));
	field("break.cause", exc_rec(1u));
	field("break.epc", exc_rec(2u));
	if (exc_rec(0u) == 0u) {
		/* It returned WITHOUT the handler running. On MIPS-I `break`
		 * traps unconditionally, so this is not a property of the core
		 * -- it is the census's instrument reporting that it is not
		 * installed, and a census run under it would report absences
		 * that are its own.
		 *
		 * The read-back above already passed, so the bytes ARE at the
		 * vector. That leaves the flush: the core is still fetching the
		 * old line. `CCTL 0x002` alone is what probe1 measured to be
		 * sufficient, and this is the branch that would refute it. */
		rlx_puts("rlxprobe: break did not trap, and the handler bytes "
			 "ARE at the vector -- so the I-cache did not see "
			 "them. Census abandoned.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		return;
	}
	progress(P_BREAK);

	/* The census. 32 registers x 8 selects, each through its own stub, each
	 * read twice with a different prime. */
	for (i = 0; i < RB_CELLS; i++) {
		u32 v1, v2, state, differs, show;

		state = census_row(i, &v1, &v2);

		switch (state & 0xFFu) {
		case S_TRAP:	traps++;   break;
		case S_VALUE:	values++;  break;
		case S_ZERO:	zeros++;   break;
		case S_NOWRITE:	nowrite++; break;
		case S_MOVES:	moves++;   break;
		default:	mixed++;   break;
		}

		rb_put(RB_HDR + i * RB_CELLW + 0u, v1);
		rb_put(RB_HDR + i * RB_CELLW + 1u, v2);
		rb_put(RB_HDR + i * RB_CELLW + 2u, state);
		rb_put(H_ROWS_DONE, i + 1u);

		if (i == ROW_COUNT)
			row48 = state;

		/* Over the UART: every select-0 row, and any select != 0 row
		 * that DIFFERS from its own register's select-0 row. On a core
		 * that ignores the select field -- which is what an R3000-class
		 * CP0 does -- that is 32 lines, and `rows.printed` says so
		 * without anyone having to count them. On a core that decodes
		 * it, every row that answered differently prints. A 256-line
		 * report at 38400 is 13 KB and three and a half seconds of
		 * exactly the exposure P9-12 was lost to. */
		if ((i & 7u) == 0u) {
			base_v1 = v1;
			base_v2 = v2;
			base_state = state;
			differs = 1u;
		} else {
			differs = (v1 != base_v1 || v2 != base_v2 ||
				   state != base_state);
		}
		show = differs && printed < RB_UART_ROWS;
		if (differs && !show)
			suppressed++;
		if (show) {
			rlx_puts("rlxprobe: cp0 ");
			rlx_puthex32(i);
			rlx_putc(' ');
			rlx_puthex32(v1);
			rlx_putc(' ');
			rlx_puthex32(v2);
			rlx_putc(' ');
			rlx_puthex32(state);
			rlx_puts("\r\n");
			printed++;
		}
	}
	rb_put(H_TRAPS, traps);
	rb_put(H_VALUES, values);
	rb_put(H_ZEROS, zeros);
	rb_put(H_NOWRITE, nowrite);
	rb_put(H_MOVES, moves);
	rb_put(H_MIXED, mixed);
	rb_put(H_ROWS_PRINTED, printed);
	progress(P_CENSUS);

	field("traps", traps);
	field("values", values);
	field("zeros", zeros);
	field("nowrite", nowrite);
	field("moves", moves);
	field("mixed", mixed);
	field("rows.printed", printed);
	field("rows.suppressed", suppressed);

	/* F50b. 100,000 iterations of a three-instruction loop; if Count runs at
	 * anything near the timer base it moves by hundreds of thousands, and if
	 * it is not implemented it does not move at all.
	 *
	 * FOUR THINGS ARE REPORTED BESIDE THE DELTA AND EACH ONE CLOSES A WAY
	 * THIS CELL COULD LIE.
	 *   spins   a zero delta with a zero loop count is an instrument failure
	 *           wearing a result's clothes.
	 *   before  the two raw readings. Both destinations are primed, so a
	 *   after   core whose `mfc0` does not write `rt` returns
	 *           C0DE0009 / D1CE0009 here and the delta is visibly nonsense
	 *           rather than a plausible small number.
	 *   traps   the call is bracketed the way the census brackets its stubs.
	 *           A trapped `mfc0` leaves the destination alone, so a trap
	 *           produces the same residue arithmetic, and nothing here
	 *           connected the two until now.
	 *   row48   rd 9, sel 0 -- the same register through the same
	 *           instruction on a different path. If it is S_TRAP or
	 *           S_NOWRITE, this delta is residue arithmetic and F50b is
	 *           answered by the row, not by the delta. The audit's Must-fix
	 *           4 ends on exactly that cross-check and nothing in the
	 *           payload made it. */
	cnt_traps = exc_rec(0u);
	delta = rlx_count_delta(100000u, (u32 *)((u32)&count_raw[0] | KSEG1_BIT));
	cnt_traps = exc_rec(0u) - cnt_traps;
	cnt_before = rd_unc((u32)&count_raw[0]);
	cnt_after  = rd_unc((u32)&count_raw[1]);

	rb_put(H_CNT_SPINS, 100000u);
	rb_put(H_CNT_BEFORE, cnt_before);
	rb_put(H_CNT_AFTER, cnt_after);
	rb_put(H_CNT_DELTA, delta);
	rb_put(H_CNT_TRAPS, cnt_traps);
	rb_put(H_CNT_ROW48, row48);
	progress(P_COUNT);

	field("count.spins", 100000u);
	field("count.before", cnt_before);
	field("count.after", cnt_after);
	field("count.delta", delta);
	field("count.traps", cnt_traps);
	field("count.row48", row48);
	if (cnt_traps != 0u || (row48 & 0xFFu) == S_TRAP ||
	    (row48 & 0xFFu) == S_NOWRITE)
		rlx_puts("rlxprobe: count.delta is NOT a tick count -- "
			 "mfc0 $9 did not deliver a value on this core\r\n");

	copy_vec_back();

	/* Prove the restore, from memory rather than from intent, IN BOTH
	 * DIRECTIONS and over BOTH vectors.
	 *
	 * The old check read eight words of the GENERAL vector and compared them
	 * against the array that had just written them, while the block's saved
	 * words were the UTLB vector's -- so it covered 8 of 64 words, checked
	 * one vector against the block and the other against itself, and the
	 * only proposition it could refute was "the uncached store landed".
	 *
	 * `restore.mismatch` is that proposition, now over all 64 words. It
	 * still cannot tell you whether `saved_vec` itself is right -- nothing
	 * in this payload can, and `H2h` cannot either, because the watchdog
	 * reset re-runs `trap_init` before the next command is typed.
	 *
	 * `restore.stillhandler` is the leg that was missing: of the words the
	 * install actually CHANGED, how many still equal OUR handler. If the
	 * restore worked it is 0, and a check whose failure mode is "the value
	 * is unchanged" needs a companion whose failure mode is "the value is
	 * still mine".
	 *
	 * The `saved != entry` guard is not tidiness, it is the difference
	 * between a control and a coincidence. Ten of this handler's words are
	 * `nop`, and under qemu the vector page starts as zeros -- so counting
	 * every position where the restored word equals a handler word returned
	 * 20 on a run whose restore was perfect. Measured 2026-08-25, on the
	 * first qemu run of this code. Only positions the install demonstrably
	 * changed can say anything about whether the restore undid it. */
	sum = 0u;
	for (i = 0; i < VEC_WORDS; i++) {
		if (rd_unc(VEC_UTLB + i * 4u) != saved_vec[i])
			sum++;
		if (rd_unc(VEC_GENERAL + i * 4u) != saved_vec[i + VEC_WORDS])
			sum++;
	}
	rb_put(H_RES_MISMATCH, sum);
	field("restore.mismatch", sum);

	sum = 0u;
	for (i = 0; i < words; i++) {
		if (saved_vec[i] != rlx_exc_entry[i] &&
		    rd_unc(VEC_UTLB + i * 4u) == rlx_exc_entry[i])
			sum++;
		if (saved_vec[i + VEC_WORDS] != rlx_exc_entry[i] &&
		    rd_unc(VEC_GENERAL + i * 4u) == rlx_exc_entry[i])
			sum++;
	}
	rb_put(H_RES_STILLHDL, sum);
	field("restore.stillhandler", sum);
	progress(P_RESTORED);

	/* Status again, free, and it is not decoration: this payload writes
	 * Status nowhere, so a Status that moved across the run is a fact about
	 * the core or about the handler and not about this code. */
	status = rlx_mfc0_status();
	rb_put(H_STATUS_END, status);
	field("status_end", status);

	/* THE SEAL COVERS THE BLOCK AS IT WAS BEFORE P_SEALED WAS STAMPED, and
	 * anyone re-summing it afterwards has to know that.
	 *
	 * The sum runs over words 0 .. RB_HDR+RB_CELLS*RB_CELLW-1, which
	 * INCLUDES H_PROGRESS at word 2.  `progress(P_SEALED)` then writes word
	 * 2 again.  So a straight re-sum of the recovered block is high by
	 * exactly P_SEALED - P_RESTORED = 0x90 - 0x80 = 0x10, on every complete
	 * run, and the block reads as corrupt to anyone who does not subtract
	 * it.
	 *
	 * 量 2026-08-25, `bench/2026-08-25b/H2g.log`: naive re-sum 0xEC84409D
	 * against a stored 0xEC84408D.  Re-summing with word 2 forced to
	 * P_RESTORED gives 0xEC84408D, exact.
	 *
	 * Not reordered.  Sealing first and stamping progress afterwards is what
	 * makes `progress` monotone all the way to the end -- a block whose seal
	 * is written but whose progress says P_RESTORED is a run that died
	 * between the two, and that is a state worth being able to see.  The fix
	 * is this comment and the arithmetic in the runsheet, not a swap that
	 * would make P_SEALED mean less. */
	sum = 0u;
	for (i = 0; i < RB_HDR + RB_CELLS * RB_CELLW; i++)
		sum += rb_get(i);
	rb_put(RB_HDR + RB_CELLS * RB_CELLW, sum);
	progress(P_SEALED);
	field("sum", sum);

	rlx_puts("rlxprobe: end\r\n");
}
