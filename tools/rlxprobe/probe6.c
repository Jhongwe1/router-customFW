/* probe6.c -- `R1f` and `R2c`'s silicon row.  One row per COMPILER.
 *
 * The question, from `plan/router-rebuild-plan.md:1063-1068` (`R1f`):
 *
 *     一段 C，在有 interlock 的假設下是對的、沒有 interlock 就是錯的，
 *     每個候選 -march 各編一次、都上矽片；錯誤，且沒有任何警告或 fault
 *
 * and from `:1140-1141` (`R2c`): the load-delay row of the three-toolchain
 * table must reach silicon in all three columns, not only at the desk.
 *
 * WHAT IS DIFFERENT FROM probe4 AND probe5, AND IT IS ONE THING
 *
 *   The thing under test is not in this repository.  `probe4`'s rows are
 *   encodings this project wrote; `probe5`'s are sequences this project wrote;
 *   every row here is somebody else's compiler applied to one unchanged C file
 *   (`frag.c`).  Three consequences:
 *
 *   ① THE FRAMEWORK IS NOT BUILT BY THE THING UNDER TEST.  Everything in this
 *      image except the ten `frag-*.o` is the host cross-compiler at
 *      `-march=mips1` -- the configuration every payload that has ever run on
 *      this die was built with.  An instrument built out of its own subject
 *      cannot separate *the fragment computed the wrong value* from *the
 *      reporting path computed the wrong value*.
 *   ② THE PAYLOAD CANNOT COMPARE.  Two of the three readings a row can produce
 *      are constants this payload writes, so an in-image comparison would be
 *      the image agreeing with itself.  `tools/tcpay.py verdict` decides at the
 *      desk, exactly as `isapay` and `hazpay` do.
 *   ③ THE BUILD IS PART OF THE READING.  `tools/isa-toolchain.tsv`'s `pad`
 *      column is a prediction about what a compiler will emit, and
 *      `tcpay verify` checks it word by word against the linked image before
 *      the board is powered.  A toolchain that changed its mind fails the build
 *      instead of producing a row that cannot mean anything.
 *
 * HOW ONE ROW WORKS
 *
 *   The destination word holds `P6_DST_INIT` and the source word holds
 *   `P6_SRC_VAL`.  The row's thunk puts `P6_SENTINEL` in `$v0` in the
 *   instruction immediately before the fragment's load, and calls it.  Then:
 *
 *     the store wrote P6_SRC_VAL   the consumer saw the loaded value    LOCK
 *     the store wrote P6_SENTINEL  the consumer saw $v0's prior value   OPEN
 *     the destination is unchanged the store never happened             VOID
 *
 *   Every row is run TWICE: once with the I-cache invalidated immediately
 *   before the call, and once straight after.  `docs/isa-hazard.md` § 7.1
 *   records that every `probe5` rung ran on a warm cache and that nothing had
 *   measured the cold case; here it is free, and a row whose two runs disagree
 *   is its own verdict (`SPLIT`) rather than an average.
 *
 * WHAT IT DOES NOT DO
 *   - no flash, no configuration write, no CP0 write of any kind on a device
 *     build.  `probe5`'s `mtc0 $11, $14` has no counterpart here;
 *   - no timing.  Every reading is a VALUE;
 *   - it does not control the D-cache state of the two words.  They are
 *     adjacent in one static array, written immediately before each call, so
 *     both are warm in D by construction -- said here rather than left to be
 *     found, because the I-side is controlled and the D-side is not.
 */
#include "rlxprobe.h"
#include "rlxdefs.h"
#include "probe6rows.h"

#ifndef RLX_NONCE
#define RLX_NONCE	"6c3a91f4"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x6c3a91f4u
#endif

#define RB_MAGIC	0x524C5836u	/* 'RLX6' */
#define RB_VERSION	0x00080001u
#define RB_POISON	0xDEADC0DEu

#define RB_HDR		32u
#define O_ROWS		RB_HDR
#define O_SEAL		(O_ROWS + P6_ROWS * P6_ROW_WORDS)
#define RB_WORDS	(O_SEAL + 1u)
#define RB_POISON_W	(RB_WORDS + 8u)

/* The layout adds up at COMPILE time.  C99 has no _Static_assert; a negative
 * array bound is the portable form. */
typedef char p6_layout_adds_up[(RB_WORDS == 33u + 8u * P6_ROWS) ? 1 : -1];

/* And the read-back must show poison.  `DW base n` returns 4*ceil(n/4) words
 * (`LDR-07`), so a block whose length is a multiple of four returns no word past
 * its own seal -- and a payload that wrote past its block writes UPWARD from the
 * seal, which is exactly where the evidence would be.  33 + 8R is 1 mod 4 for
 * every R, so this holds for any row count at this width; the assertion is here
 * rather than in a comment because the width is a constant somebody may
 * change.  `tools/tcpay.py`'s `rb_words()` carries the same guard. */
typedef char p6_readback_shows_poison[(RB_WORDS % 4u != 0u) ? 1 : -1];

#define UNC(a)		((volatile u32 *)((a) | KSEG1_BIT))

/* --- header words --------------------------------------------------------- */
#define H_MAGIC		0u
#define H_NONCE		1u
#define H_PROGRESS	2u
#define H_PC		3u
#define H_VERSION	4u
#define H_FLAGS		5u
#define H_RB		6u
#define H_STATUS	7u
#define H_VEC		8u
#define H_KSEG0		9u
#define H_ROWS		10u
#define H_ROW_WORDS	11u
#define H_LAYOUT_ROWS	12u
#define H_LAYOUT_SEAL	13u
#define H_HWORDS	14u	/* the handler's length, in words             */
#define H_INS_CHANGED	15u	/* vector words the install actually changed  */
#define H_INS_BAD	16u	/* words that did not read back               */
#define H_BRK_COUNT	17u	/* C1 -- `break`.  Must be 1                  */
#define H_BRK_CAUSE	18u
#define H_BRK_EPC	19u
#define H_CELL_BAD	20u	/* rows whose two words did not read back     */
#define H_TRAPPED	21u	/* rows with n > 0                            */
#define H_RAN		22u	/* rows with n == 0                           */
#define H_RES_MISMATCH	23u	/* vector words not restored                  */
#define H_RES_STILLHDL	24u	/* ... and still holding OUR handler          */
#define H_STATUS_END	25u
#define H_TAG_BASE	26u
/* probe6's own five. */
#define H_ADDR_D	27u	/* the destination word's address             */
#define H_ADDR_S	28u	/* the source word's address                  */
#define H_SPLIT		29u	/* rows whose cold and warm runs disagree     */
#define H_SENTINEL	30u	/* the constant THIS BUILD primed into $v0    */
#define H_SRC_VAL	31u	/* the constant THIS BUILD put in the source  */
#define H_SEAL		O_SEAL

/* --- progress ------------------------------------------------------------- */
#define P_POISON	0x01u
#define P_HEADER	0x02u
#define P_INSTALLED	0x03u
#define P_BREAK		0x04u
#define P_CELLS		0x05u
#define P_ROWS		0x10u	/* + row index */
#define P_RESTORED	0xF0u
#define P_SEALED	0xF1u

#define VEC_UTLB	((u32)RLX_VEC_UTLB)
#define VEC_GENERAL	((u32)RLX_VEC_GENERAL)
#define VEC_WORDS	32u

#define FLAGS_W		((u32)0x50000000u | 0x0002u \
			 | ((u32)RLX_RESET << 16) | ((u32)RLX_CLEAR_BEV << 17) \
			 | ((u32)RLX_RET_ERET << 18) | ((u32)RLX_ISC << 19) \
			 | ((u32)RLX_GEOM << 20))

/* exc.S forms this address with lui/addiu, so it must be a definition here. */
u32 rlx_exc_rec[4];

#if RLX_CLEAR_BEV
/* p6support.S, and it exists only on a qemu build. */
void rlx_status_write(u32 v);
#endif

static u32 rb_ks0, rb_ks1;
static u32 saved_vec[VEC_WORDS * 2u];
static u32 ins_changed, ins_bad;

/* THE TWO WORDS.  Adjacent and 8-byte aligned, so a row's load and store touch
 * one D-cache line whatever this die's line size turns out to be -- `CPU-25`
 * measured 16 bytes on the I-side and the D-side geometry is still a build
 * constant (`docs/probe3-cells.md`, Group V is VOID).  Adjacency is therefore
 * an assumption about ONE line only in so far as the line is >= 8 bytes, and
 * nothing in this payload depends on it: both words are written immediately
 * before every call, so both are warm however they are laid out. */
static u32 cell[2] __attribute__((aligned(8)));
#define C_DST	0u
#define C_SRC	1u

static void rb_put(u32 i, u32 v) { *(volatile u32 *)(rb_ks1 + i * 4u) = v; }
static u32  rb_get(u32 i)        { return *(volatile u32 *)(rb_ks1 + i * 4u); }
static u32  rd_unc(u32 a)        { return *UNC(a); }
static void wr_unc(u32 a, u32 v) { *UNC(a) = v; }
static void progress(u32 p)      { rb_put(H_PROGRESS, p); }

static u32  exc_rec(u32 n)        { return rd_unc((u32)&rlx_exc_rec[n]); }
static void exc_set(u32 n, u32 v) { wr_unc((u32)&rlx_exc_rec[n], v); }

static void flush_i(void)
{
	rlx_call2_uncached((u32)rlx_cctl, (u32)CCTL_IINVAL, 0u);
}

static void field(const char *k, u32 v)
{
	rlx_puts("rlxprobe: ");
	rlx_puts(k);
	rlx_puts("=");
	rlx_puthex32(v);
	rlx_puts("\r\n");
}

/* --- the handler ---------------------------------------------------------- */
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
	flush_i();
}

static u32 install_handler(void)
{
	u32 words = (u32)(rlx_exc_end - rlx_exc_entry);
	u32 i, got;

	ins_changed = 0u;
	ins_bad = 0u;
	if (words * 4u > VEC_WORDS * 4u)
		return 0u;

	for (i = 0; i < words; i++) {
		u32 w = rlx_exc_entry[i];

		if (rd_unc(VEC_GENERAL + i * 4u) != w)
			ins_changed++;
		wr_unc(VEC_GENERAL + i * 4u, w);
		wr_unc(VEC_UTLB + i * 4u, w);
	}
	flush_i();
	for (i = 0; i < words; i++) {
		got = rd_unc(VEC_GENERAL + i * 4u);
		if (got != rlx_exc_entry[i])
			ins_bad++;
		got = rd_unc(VEC_UTLB + i * 4u);
		if (got != rlx_exc_entry[i])
			ins_bad++;
	}
	return words;
}

/* --- one row -------------------------------------------------------------- */
/*
 * `probe5`'s comment applies here too: no row is given a chance to leave its
 * own eight words unwritten, because the tag goes in FIRST.  A row that hangs
 * leaves poison in the seven after a valid tag, and the progress word already
 * names the row it died in.
 */
static void run_row(u32 i)
{
	u32 b = O_ROWS + i * P6_ROW_WORDS;
	u32 n, cause, epc, pre, cold, warm, aux;

	rb_put(b + 0u, P6_TAG_BASE | i);
	rb_put(b + 1u, 0u);
	rb_put(b + 2u, 0u);
	rb_put(b + 3u, 0u);
	rb_put(b + 4u, 0u);
	rb_put(b + 5u, 0u);
	rb_put(b + 6u, 0u);
	rb_put(b + 7u, 0u);
	progress(P_ROWS + i);

	exc_set(0u, 0u);
	exc_set(1u, 0u);
	exc_set(2u, 0u);

	/* THE COLD RUN.  The I-cache is invalidated with the fragment's own
	 * words in it, so its first instruction fetch after this is a miss.
	 * `rlx_call2_uncached` runs `rlx_cctl` from KSEG1 so the invalidate does
	 * not have to survive invalidating the code doing it. */
	cell[C_DST] = P6_DST_INIT;
	cell[C_SRC] = P6_SRC_VAL;
	pre = cell[C_DST];
	flush_i();
	p6_thunks[i](&cell[C_DST], &cell[C_SRC], P6_SENTINEL);
	cold = cell[C_DST];

	/* THE WARM RUN.  Same call, nothing invalidated in between. */
	cell[C_DST] = P6_DST_INIT;
	cell[C_SRC] = P6_SRC_VAL;
	p6_thunks[i](&cell[C_DST], &cell[C_SRC], P6_SENTINEL);
	warm = cell[C_DST];

	/* The source word, read back AFTER both calls.  This is the row's
	 * control: `the store wrote the loaded value` and `the load had nothing
	 * to load` would otherwise arrive as the same reading, because a source
	 * word that had been clobbered to the sentinel would make every row read
	 * OPEN and look like a spectacular finding. */
	aux = cell[C_SRC];

	n = exc_rec(0u);
	cause = exc_rec(1u);
	epc = exc_rec(2u);

	rb_put(b + 1u, n);
	rb_put(b + 2u, cause);
	rb_put(b + 3u, epc);
	rb_put(b + 4u, cold);
	rb_put(b + 5u, warm);
	rb_put(b + 6u, aux);
	rb_put(b + 7u, pre);

	if (pre != P6_DST_INIT || aux != P6_SRC_VAL)
		rb_put(H_CELL_BAD, rb_get(H_CELL_BAD) + 1u);
	if (cold != warm)
		rb_put(H_SPLIT, rb_get(H_SPLIT) + 1u);
	if (n) rb_put(H_TRAPPED, rb_get(H_TRAPPED) + 1u);
	else   rb_put(H_RAN,     rb_get(H_RAN)     + 1u);
}

/* Every row, over the UART, one line each.  It prints from the result block
 * through KSEG1 rather than from the C variables, so what it prints is what a
 * `DW` would return and not what the payload believes it wrote. */
static void dump_rows(void)
{
	u32 i, j, b;

	rlx_puts("rlxprobe: rows begin\r\n");
	for (i = 0; i < P6_ROWS; i++) {
		b = O_ROWS + i * P6_ROW_WORDS;
		rlx_puts("P6 ");
		rlx_puthex32(i);
		rlx_puts(" ");
		rlx_puts(p6_names[i]);
		for (j = 0; j < P6_ROW_WORDS; j++) {
			rlx_puts(" ");
			rlx_puthex32(rb_get(b + j));
		}
		rlx_puts("\r\n");
	}
	rlx_puts("rlxprobe: rows end\r\n");
}

/* --- main ----------------------------------------------------------------- */
void rlxprobe_main(void)
{
	u32 pc, flags, status, i, words, sum;
	u32 res_mismatch = 0u, res_stillhdl = 0u;

	rb_ks0 = (u32)RLX_RESULT_BASE;
	rb_ks1 = rb_ks0 | (u32)KSEG1_BIT;

	/* FIRST.  `MEM-17`: this DRAM keeps its contents across a short
	 * power-off, so a block left by a previous payload reads exactly like
	 * this one's. */
	for (i = 0; i < RB_POISON_W; i++)
		rb_put(i, RB_POISON);
	progress(P_POISON);

	pc = rlx_pc();
#if RLX_CLEAR_BEV
	rlx_status_write(rlx_mfc0_status() & ~(u32)ST0_BEV);
	rlx_puts("rlxprobe: WARNING RLX_CLEAR_BEV=1 -- this is a qemu build\r\n");
#endif
	status = rlx_mfc0_status();
	flags = FLAGS_W;

	rb_put(H_MAGIC, RB_MAGIC);
	rb_put(H_NONCE, RLX_NONCE_W);
	rb_put(H_VERSION, RB_VERSION);
	rb_put(H_PC, pc);
	rb_put(H_FLAGS, flags);
	rb_put(H_RB, rb_ks0);
	rb_put(H_STATUS, status);
	rb_put(H_VEC, VEC_GENERAL);
	rb_put(H_KSEG0, ((pc & KSEG_MASK) == (u32)KSEG0_BASE) ? 1u : 0u);
	rb_put(H_ROWS, P6_ROWS);
	rb_put(H_ROW_WORDS, P6_ROW_WORDS);
	rb_put(H_LAYOUT_ROWS, O_ROWS);
	rb_put(H_LAYOUT_SEAL, O_SEAL);
	rb_put(H_TAG_BASE, P6_TAG_BASE);
	rb_put(H_ADDR_D, (u32)&cell[C_DST]);
	rb_put(H_ADDR_S, (u32)&cell[C_SRC]);
	rb_put(H_SENTINEL, P6_SENTINEL);
	rb_put(H_SRC_VAL, P6_SRC_VAL);
	rb_put(H_CELL_BAD, 0u);
	rb_put(H_SPLIT, 0u);
	rb_put(H_TRAPPED, 0u);
	rb_put(H_RAN, 0u);
	progress(P_HEADER);

	rlx_puts("\r\n*** rlxprobe P6 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("flags", flags);
	field("status", status);
	field("rows", P6_ROWS);
	field("kseg0", rb_get(H_KSEG0));
	if (rb_get(H_KSEG0) == 0u)
		rlx_puts("rlxprobe: NOT IN KSEG0 -- the I-side flush is void\r\n");

	copy_vec_out();
	words = install_handler();
	rb_put(H_HWORDS, words);
	rb_put(H_INS_CHANGED, ins_changed);
	rb_put(H_INS_BAD, ins_bad);
	field("install.words", words);
	field("install.changed", ins_changed);
	field("install.bad", ins_bad);
	if (words == 0u || ins_bad != 0u) {
		rlx_puts("rlxprobe: HANDLER DID NOT INSTALL -- a trap in any row "
			 "would hang instead of being counted.  Refusing.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		rlx_reset();
	}
	progress(P_INSTALLED);

	/* C1.  `break` traps on every MIPS ever built, which is what makes it a
	 * control on the handler rather than a question about this core.  No row
	 * of this table is expected to trap -- `lw` and `sw` are MIPS-I -- so
	 * this control is what makes `n == 0` on every row mean *nothing
	 * trapped* rather than *nothing was counted*. */
	exc_set(0u, 0u);
	exc_set(1u, 0u);
	exc_set(2u, 0u);
	rlx_do_break();
	rb_put(H_BRK_COUNT, exc_rec(0u));
	rb_put(H_BRK_CAUSE, exc_rec(1u));
	rb_put(H_BRK_EPC, exc_rec(2u));
	field("break.count", exc_rec(0u));
	field("break.cause", exc_rec(1u));
	progress(P_BREAK);
	if (exc_rec(0u) == 0u) {
		rlx_puts("rlxprobe: BREAK DID NOT TRAP -- every n=0 below would "
			 "be unattributable.  Refusing the sweep.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		rlx_reset();
	}

	/* C2, and it is probe6's own.  The two words have to be writable and
	 * readable BEFORE any row runs: if they are not, every row reads VOID
	 * and the table looks like a finding about ten compilers. */
	cell[C_DST] = P6_DST_INIT;
	cell[C_SRC] = P6_SRC_VAL;
	field("addr.d", (u32)&cell[C_DST]);
	field("addr.s", (u32)&cell[C_SRC]);
	field("cell.d", cell[C_DST]);
	field("cell.s", cell[C_SRC]);
	if (cell[C_DST] != P6_DST_INIT || cell[C_SRC] != P6_SRC_VAL) {
		rlx_puts("rlxprobe: THE TWO WORDS DID NOT READ BACK -- no row "
			 "can mean anything.  Refusing.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		rlx_reset();
	}
	progress(P_CELLS);

	for (i = 0; i < P6_ROWS; i++)
		run_row(i);

	copy_vec_back();
	for (i = 0; i < VEC_WORDS; i++) {
		if (rd_unc(VEC_GENERAL + i * 4u) != saved_vec[i + VEC_WORDS])
			res_mismatch++;
		if (i < (u32)(rlx_exc_end - rlx_exc_entry) &&
		    rd_unc(VEC_GENERAL + i * 4u) == rlx_exc_entry[i])
			res_stillhdl++;
	}
	rb_put(H_RES_MISMATCH, res_mismatch);
	rb_put(H_RES_STILLHDL, res_stillhdl);
	rb_put(H_STATUS_END, rlx_mfc0_status());
	progress(P_RESTORED);

	sum = 0u;
	for (i = 0; i < O_SEAL; i++)
		sum += rb_get(i);
	rb_put(H_SEAL, sum);
	progress(P_SEALED);

	field("trapped", rb_get(H_TRAPPED));
	field("ran", rb_get(H_RAN));
	field("cell.bad", rb_get(H_CELL_BAD));
	field("split", rb_get(H_SPLIT));
	field("restore.mismatch", res_mismatch);
	field("restore.stillhdl", res_stillhdl);
	field("seal", sum);
	field("words", RB_WORDS);
	dump_rows();
	rlx_puts("rlxprobe: end\r\n");
	rlx_reset();
}
