/* probe4.c -- `R1a`'s instruction sweep.  One row per encoding, three verdicts.
 *
 * `plan/router-rebuild-plan.md:1007` states the question this payload asks:
 *
 *     每一列都帶一個算得出唯一答案的運算元，判讀三分 …
 *     「不 trap 但答錯」是最重要的那一格
 *
 * and `PROGRESS.md:121`'s risk column states the way to lose it:
 *
 *     a payload that compares in-place reports a boolean and throws the value
 *     away
 *
 * SO THIS PAYLOAD DOES NOT COMPARE ANYTHING.  It records, for every row, the
 * exception count, the whole `Cause` word, `EPC`, and the four result words,
 * and `tools/isapay.py verdict` decides at the desk.  The expected constants
 * are not in this image at all -- there is nothing here for a wrong expectation
 * to be silently right against.
 *
 * The cells are generated: `tools/isapay.py emit` turns `tools/isa-payload.tsv`
 * into `cells4.S` and `probe4rows.h`.  The register allocation is identical in
 * every cell, which is the whole reason a generator beats 45 hand-written
 * cells -- the encoding's rs/rt/rd fields and the setup code that fills those
 * registers come out of one place and cannot drift apart.
 *
 * WHAT THIS PAYLOAD INHERITS RATHER THAN REDOES
 *   - the handler at `0x80000080` and `0x80000000`, and the `break` control on
 *     it: `probe2`, `R1e`, 量 `bench/2026-08-25b`;
 *   - `CCTL 0x002` as the sufficient I-side flush: `probe1`, `R1d`, 量
 *     `bench/2026-08-25`;
 *   - `SAFE_A0`: the loader's `do_reserved` reads a `pt_regs *` out of `$a0`.
 *
 * WHAT IT DOES NOT DO
 *   - no flash, no configuration write, no `Status` write on a device build;
 *   - no timing: `R1c`'s cost column needs a ruler this payload does not carry;
 *   - no MIPS16 and no NX row yet -- both need a second execution context and
 *     they are named in `docs/isa-payload.md` § 6 rather than left to be
 *     noticed missing.
 */
#include "rlxprobe.h"
#include "rlxdefs.h"
#include "probe4rows.h"

#ifndef RLX_NONCE
#define RLX_NONCE	"7e41c9d0"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x7e41c9d0u
#endif

#define RB_MAGIC	0x524C5834u	/* 'RLX4' */
#define RB_VERSION	0x00060001u
#define RB_POISON	0xDEADC0DEu

#define RB_HDR		32u
#define O_ROWS		RB_HDR
#define O_SEAL		(O_ROWS + P4_ROWS * P4_ROW_WORDS)
#define RB_WORDS	(O_SEAL + 1u)
#define RB_POISON_W	(RB_WORDS + 8u)

/* The layout adds up, and it adds up at COMPILE time.  C99 has no
 * _Static_assert; a negative array bound is the portable form. */
typedef char p4_layout_adds_up[(RB_WORDS == 33u + 8u * P4_ROWS) ? 1 : -1];

/* And the read-back must show poison.  `DW base n` returns 4*ceil(n/4) words
 * (`LDR-07`), so a block whose length is a multiple of four returns no word
 * past its own seal -- and a payload that wrote past its block writes UPWARD
 * from the seal, so that first word past is exactly where the evidence is.
 * 33 + 8R is 1 mod 4 for every R, which makes this property structural rather
 * than a remainder that happened to fall out.  probe3 carries the same check
 * and got there by arithmetic luck three times. */
typedef char p4_readback_shows_poison[(RB_WORDS % 4u != 0u) ? 1 : -1];

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
#define H_SCRATCH_BAD	20u	/* rows whose inputs did not read back after  */
#define H_TRAPPED	21u	/* rows with n > 0                            */
#define H_RAN		22u	/* rows with n == 0                           */
#define H_RES_MISMATCH	23u	/* vector words not restored                  */
#define H_RES_STILLHDL	24u	/* ... and still holding OUR handler          */
#define H_STATUS_END	25u
#define H_TAG_BASE	26u
#define H_SEAL		O_SEAL

/* --- progress ------------------------------------------------------------- */
#define P_POISON	0x01u
#define P_HEADER	0x02u
#define P_INSTALLED	0x03u
#define P_BREAK		0x04u
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

/* exc.S forms this address with lui/addiu, so it must be a definition here.
 * `rlx_fault_frame` is NOT defined here -- report.c owns it, because every
 * payload links report.c.  Defining it in both is a link error, which is the
 * right failure: two owners of one address. */
u32 rlx_exc_rec[4];

#if RLX_CLEAR_BEV
/* p4support.S, and it exists only on a qemu build -- see that file. */
void rlx_status_write(u32 v);
#endif

static u32 rb_ks0, rb_ks1;
static u32 saved_vec[VEC_WORDS * 2u];
static u32 ins_changed, ins_bad;

/* One scratch block, re-initialised before every row.  It is `P4_SCRATCH_B`
 * bytes and 8-byte aligned because a row's memory operand is two words and
 * `lwl`/`lwr` reach three bytes past the first. */
static u32 scratch[P4_SCRATCH_B / 4u] __attribute__((aligned(8)));

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
		wr_unc(VEC_UTLB + i * 4u, rlx_exc_entry[i]);
		wr_unc(VEC_GENERAL + i * 4u, rlx_exc_entry[i]);
	}
	flush_i();

	for (i = 0; i < words; i++) {
		got = rd_unc(VEC_UTLB + i * 4u);
		if (got != rlx_exc_entry[i])
			ins_bad++;
		if (got != saved_vec[i])
			ins_changed++;
		got = rd_unc(VEC_GENERAL + i * 4u);
		if (got != rlx_exc_entry[i])
			ins_bad++;
		if (got != saved_vec[i + VEC_WORDS])
			ins_changed++;
	}
	return words;
}

/* --- one row -------------------------------------------------------------- */
/* THE TAG IS WRITTEN BEFORE THE CALL, and that ordering is the whole reason a
 * hang is readable.  probe3 states it: a cell that neither retires nor traps
 * refutes the handler and not the instruction, and it can only say so if the
 * block already names the row it died in. */
static void run_row(u32 i)
{
	const struct p4_row *r = &p4_rows[i];
	u32 b = O_ROWS + i * P4_ROW_WORDS;
	u32 n, cause, epc;

	rb_put(b + 0u, P4_TAG_BASE | i);
	rb_put(b + 1u, 0u);
	rb_put(b + 2u, 0u);
	rb_put(b + 3u, 0u);
	rb_put(b + 4u, 0u);
	rb_put(b + 5u, 0u);
	rb_put(b + 6u, 0u);
	rb_put(b + 7u, 0u);
	progress(P_ROWS + i);

	scratch[0] = r->in_a;
	scratch[1] = r->in_b;
	scratch[2] = r->seed;
	scratch[3] = 0u;
	scratch[4] = r->mem0;
	scratch[5] = r->mem1;
	scratch[6] = 0u;
	scratch[7] = 0u;
	scratch[8] = 0u;
	scratch[9] = 0u;

	exc_set(0u, 0u);
	exc_set(1u, 0u);
	exc_set(2u, 0u);

	r->cell((void *)scratch);

	n = exc_rec(0u);
	cause = exc_rec(1u);
	epc = exc_rec(2u);

	rb_put(b + 1u, n);
	rb_put(b + 2u, cause);
	rb_put(b + 3u, epc);
	rb_put(b + 4u, scratch[6]);	/* out_gpr */
	rb_put(b + 5u, scratch[7]);	/* out_m0  */
	rb_put(b + 6u, scratch[8]);	/* out_m1  */
	rb_put(b + 7u, scratch[9]);	/* out_aux */

	/* The inputs must still read back as written.  A row whose probed
	 * instruction destroyed the scratch produced its answer against
	 * operands nobody chose, and without this the reading would look
	 * exactly like an ordinary WRONG. */
	if (scratch[0] != r->in_a || scratch[1] != r->in_b)
		rb_put(H_SCRATCH_BAD, rb_get(H_SCRATCH_BAD) + 1u);

	if (n)
		rb_put(H_TRAPPED, rb_get(H_TRAPPED) + 1u);
	else
		rb_put(H_RAN, rb_get(H_RAN) + 1u);
}

/* Every row, over the UART, one line each.
 *
 * THE SECOND CHANNEL.  On the device the result block is read back with `DW`,
 * and probe2's seating is the precedent for why a second one is worth its
 * seconds: two channels agreeing on all 40 header words is a different claim
 * from one channel being self-consistent.  Here it is also the ONLY channel
 * under qemu, which has no loader to type `DW` into.
 *
 * ~68 bytes a row, 75 rows, about 1.3 s at 38400.  It prints from the result
 * block through KSEG1 rather than from the C variables, so what it prints is
 * what a `DW` would return and not what the payload believes it wrote.
 */
static void dump_rows(void)
{
	u32 i, j, b;

	rlx_puts("rlxprobe: rows begin\r\n");
	for (i = 0; i < P4_ROWS; i++) {
		b = O_ROWS + i * P4_ROW_WORDS;
		rlx_puts("P4 ");
		rlx_puthex32(i);
		rlx_puts(" ");
		rlx_puts(p4_names[i]);
		for (j = 0; j < P4_ROW_WORDS; j++) {
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
	 * this one's.  A run that dies before its first row then shows poison,
	 * which is a different observation from the previous run's data. */
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
	rb_put(H_ROWS, P4_ROWS);
	rb_put(H_ROW_WORDS, P4_ROW_WORDS);
	rb_put(H_LAYOUT_ROWS, O_ROWS);
	rb_put(H_LAYOUT_SEAL, O_SEAL);
	rb_put(H_TAG_BASE, P4_TAG_BASE);
	rb_put(H_SCRATCH_BAD, 0u);
	rb_put(H_TRAPPED, 0u);
	rb_put(H_RAN, 0u);
	progress(P_HEADER);

	rlx_puts("\r\n*** rlxprobe P4 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("flags", flags);
	field("status", status);
	field("rows", P4_ROWS);
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
		rlx_puts("rlxprobe: HANDLER DID NOT INSTALL -- every zero in this "
			 "table would be unattributable.  Refusing the sweep.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		rlx_reset();
	}
	progress(P_INSTALLED);

	/* C1.  `break` traps on every MIPS ever built, which is what makes it a
	 * control on the handler rather than a question about this core.  It
	 * runs BEFORE the sweep: a sweep whose handler was never shown to work
	 * reports absences it cannot attribute. */
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
		rlx_puts("rlxprobe: BREAK DID NOT TRAP -- C1 failed, the sweep "
			 "is void before it starts.  Refusing.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		rlx_reset();
	}

	for (i = 0; i < P4_ROWS; i++)
		run_row(i);

	copy_vec_back();
	for (i = 0; i < VEC_WORDS; i++) {
		if (rd_unc(VEC_UTLB + i * 4u) != saved_vec[i])
			res_mismatch++;
		if (rd_unc(VEC_GENERAL + i * 4u) != saved_vec[i + VEC_WORDS])
			res_mismatch++;
		/* The sharper half: of the words the install actually changed,
		 * how many still hold OUR handler.  A restore that put back a
		 * word which was already equal proves nothing. */
		if (i < words) {
			if (saved_vec[i] != rlx_exc_entry[i] &&
			    rd_unc(VEC_UTLB + i * 4u) == rlx_exc_entry[i])
				res_stillhdl++;
			if (saved_vec[i + VEC_WORDS] != rlx_exc_entry[i] &&
			    rd_unc(VEC_GENERAL + i * 4u) == rlx_exc_entry[i])
				res_stillhdl++;
		}
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
	field("scratch.bad", rb_get(H_SCRATCH_BAD));
	field("restore.mismatch", res_mismatch);
	field("restore.stillhdl", res_stillhdl);
	field("seal", sum);
	field("words", RB_WORDS);
	dump_rows();
	rlx_puts("rlxprobe: end\r\n");
	rlx_reset();
}
