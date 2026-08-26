/* probe3.c -- R1h on silicon: the cache geometry, the coherence model, and
 * whether this core retires the MIPS-II `cache` instruction.
 *
 * `docs/probe3-cells.md` is the cell table and it owns every expected value and
 * every refutation condition.  THIS FILE OWNS NONE OF THEM.  What it owns is
 * the running order, the self-gating, and the encoding -- and where a comment
 * here states an expectation it is quoting that file, not deciding anything.
 *
 * WHAT R1h EXISTS TO SETTLE
 * -------------------------
 *   (a) cache size, line size, associativity -- MEASURED, not read out of a
 *       build constant.  Two walks: Group W on the I side, where the mechanism
 *       is measured (probe1 cells 1/5, `01` STALE on all four victims), and
 *       Group V on the D side, where the prediction lives.
 *   (b) does the D-cache allocate on read, and does anything on this core
 *       invalidate a clean line.  Group C.
 *   (c) does this core retire the MIPS-II `cache` instruction.  Group X.
 *   (d) write-through or write-back-without-write-allocate, and is `Status.IsC`
 *       implemented as a bit.  Cells `c-E`/`c-E0`/`c-E2` and `s-isc`.
 *
 * THE THREE THINGS THIS PAYLOAD GATES ON ITSELF, BECAUSE A CELL THAT PASSES
 * FOR THE WRONG REASON IS WORSE THAN ONE THAT DOES NOT RUN
 * ------------------------------------------------------------------------
 *   `h-brk`  If the handler does not take, Groups M and X do not run: a `cache`
 *            trap would then reach the loader's `do_reserved` at 0x80400BE8,
 *            which prints twice and executes `j 0x80400C18` -- a branch to
 *            itself -- and hangs forever.  One power cycle, no spare device.
 *   `c-A`    If there is no stale line, EVERY Group V cell returns FRESH at
 *            every size, which is indistinguishable from *there is no
 *            D-cache*; and `c-B`/`c-C`/`c-D`/`c-F` all return `l2 = P1`
 *            whether their treatment works or not.  So those are written into
 *            the block as `void`, with the reason, and no verdict is reported.
 *   `c-F`    `CCTL 0x001` (`DInval`) invalidates the whole D-cache WITHOUT
 *            writing back, including this payload's own spilled `$31`.  `c-C`
 *            runs only if `c-F` measured that `CCTL 0x100` (`DWB`) writes back
 *            first.  cells.S's `rlx_cctl2` issues the pair inside one leaf.
 *
 * WHAT qemu SAYS ABOUT ALL OF IT, WHICH IS THE OPPOSITE OF THE DEVICE
 * ------------------------------------------------------------------
 * TCG invalidates a translation block when a store lands on code it has already
 * translated, keyed on the PHYSICAL address, so both the KSEG0 and the KSEG1
 * window behave like a machine with a coherent I-cache: EVERY W CELL IS FRESH
 * AT EVERY N AND EVERY S, so there is no boundary to find.  TCG models no
 * D-cache, so A = A' = B = C = D = E = G.  qemu does not decode the `cache` op
 * field at all -- all 32 values retire -- so it answers (c) in neither
 * direction and its agreement would mean nothing.
 *
 * 🔴 A qemu RUN THAT PRODUCES A BOUNDARY, A STALE LINE, OR A TRAP ON A `cache`
 * OP MEANS THE HARNESS IS BROKEN, NOT THAT qemu FOUND SOMETHING.  And 否證 (a)'s
 * negative control -- every victim STALE at 1 KiB -- is GUARANTEED TO FAIL under
 * qemu.  `tools/test-rlxprobe.sh` must not assert it there.
 *
 * MEM-15 IS WHY THE BLOCK IS POISONED FIRST.  This DRAM keeps its contents
 * across a short power-off, so a block left by the previous payload reads
 * exactly like this one's.  The arena is initialised for the same reason: a
 * leftover arena reads exactly like a live one.
 */

#include "rlxprobe.h"
#include "rlxdefs.h"

#ifndef RLX_NONCE
#define RLX_NONCE	"7e41c9d0"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x7e41c9d0u
#endif

/* --- the result block ----------------------------------------------------- */
/*
 *      words        what
 *      0    .. 63   header, fixed layout
 *      64   .. 255  cell results, fixed layout
 *      256  .. 383  sixteen named rows of eight words
 *      384  .. 639  the retained nibble bitmap, 2,048 victims
 *      640          the seal
 *
 * 641 words.  `DW 80A02000 641` is 15 + 2 + 47 x 161 + 9 = 7,593 bytes and
 * 1.98 s at 3840 B/s (LDR-07, fitted over 91 captures by tools/reply-size.py).
 * That is 79 % of the largest `DW` this loader has ever executed -- 820 words /
 * 9,661 bytes, 量 H2g -- and it is three digits, so it does not depend on the
 * untested question of whether the loader accepts a four-digit decimal length.
 * Cell `P3` tests that separately and nothing here rests on the answer.
 *
 * THE BITMAP HOLDS ONE SWEEP POINT.  Summed over the cell table the victim
 * INSTANCES are well over twelve thousand, and the block is reused between
 * points.  Which point survives to the read-back is a decision, it is
 * `H_BMP_POINT`, and `H_BMP_COUNT` is that point's own victim count -- so the
 * desk can compare the count the payload thought it wrote against the length it
 * actually read.
 */
#define RB_MAGIC	0x524C5833u	/* 'RLX3' */
#define RB_VERSION	0x00050001u
#define RB_POISON	0xDEADC0DEu

#define RB_HDR		64u
#define RB_RES		192u
#define RB_ROWS		16u
#define RB_ROWW		8u
#define RB_BMPW		256u

#define O_RES		RB_HDR
#define O_ROWS		(O_RES + RB_RES)
#define O_BMP		(O_ROWS + RB_ROWS * RB_ROWW)
#define O_SEAL		(O_BMP + RB_BMPW)
#define RB_WORDS	(O_SEAL + 1u)		/* 641 -- mirrored in the Makefile */
#define RB_POISON_W	(RB_WORDS + 8u)		/* a margin, so a run that wrote
						 * PAST its own block shows data
						 * where poison was predicted */

/* The Makefile carries RB_WORDS_probe3 as a second copy of this arithmetic, and
 * tools/test-rlxprobe.sh recomputes both and fails if they drift.  This is the
 * compile-time half of the same check: a layout that does not add up does not
 * build.  (C99 has no _Static_assert; a negative array bound is the portable
 * form and it has been the portable form for thirty years.) */
typedef char rb_layout_adds_up[(RB_WORDS == 641u) ? 1 : -1];

#define UNC(a)		((volatile u32 *)((a) | KSEG1_BIT))

/* --- header words --------------------------------------------------------- */
/* Named rather than numbered at the point of use, because a block layout that
 * exists only as literals inside rb_put() calls is a layout the runsheet cell
 * has to be diffed against by eye. */
#define H_MAGIC		0u
#define H_NONCE		1u
#define H_PROGRESS	2u
#define H_PC		3u
#define H_VERSION	4u
#define H_FLAGS		5u
#define H_RB		6u
#define H_STATUS	7u
#define H_VEC		8u
#define H_HWORDS	9u
#define H_INS_CHANGED	10u
#define H_INS_BAD	11u
#define H_INS_FIRSTBAD	12u
#define H_BRK_COUNT	13u
#define H_BRK_CAUSE	14u
#define H_BRK_EPC	15u
#define H_ARENA		16u
#define H_ARENA_END	17u
#define H_ARENA_MOVED	18u
#define H_TMPL		19u
#define H_TMPL_W0	20u	/* the guard word AS ASSEMBLED, read back through */
#define H_TMPL_W1	21u	/* KSEG1 -- so the arena's contents are checkable */
#define H_BMP_POINT	22u
#define H_BMP_COUNT	23u
#define H_RES_MISMATCH	24u
#define H_RES_STILLHDL	25u
#define H_STATUS_END	26u
#define H_G_HBRK	27u	/* the three gates, as the payload read them */
#define H_G_CA		28u
#define H_G_CF		29u
#define H_G_X11		30u
#define H_ROWS_USED	31u
#define H_SAVED0	32u	/* 32..39: the general vector's first eight words */
#define H_LAYOUT_RES	40u	/* the four offsets, so the desk can parse the   */
#define H_LAYOUT_ROWS	41u	/* block from the block rather than from this   */
#define H_LAYOUT_BMP	42u	/* file                                          */
#define H_LAYOUT_SEAL	43u
#define H_CELLS_RUN	44u
#define H_CELLS_VOID	45u
#define H_UART_ROWS	46u
#define H_SEAL_KIND	47u	/* 1 = the sum excludes H_PROGRESS's final value */
/* 🔴 A WORD OF ITS OWN, AND THE FIRST DRAFT PUT IT IN `H_FLAGS`, WHERE IT WAS
 * INVISIBLE.  `FLAGS_W` starts at 0x50000000 -- 'P' -- so bits 28 and 30 are
 * already set in every build, and a *running in KSEG0* flag at 0x40000000 could
 * never be read as anything but set.  量 on the first qemu run: `flags=50070002`
 * with the bit indistinguishable from the marker, and the *NOT IN KSEG0* warning
 * -- the one that says every cache cell is void -- could not have fired.
 * `FLAGS_W` is the BUILD stamp and `make show` prints the same expression; a
 * run-time bit does not belong in it. */
#define H_KSEG0		48u
#define H_G_TIMER	49u
#define H_T_SEP_A	50u	/* the SEPARATED pair, which is the one 否證 T   */
#define H_T_SEP_B	51u	/* is written against                            */

/* Progress, written after each stage completes, so a block recovered by `DW`
 * after a hang says where the run stopped without any inference from what is
 * missing.  Poison here means it did not reach the header at all. */
#define P_HEADER	0x10u
#define P_HANDLER	0x20u
#define P_TIMER		0x30u
#define P_WALK_I	0x40u
#define P_IMEM_OFF	0x50u
#define P_SCRATCH	0x60u
#define P_COHERE	0x70u
#define P_WALK_D	0x80u
#define P_CACHEOP	0x90u
#define P_ISC		0xA0u
#define P_RESTORED	0xB0u
#define P_SEALED	0xC0u

/* --- the cell-results area, fixed layout --------------------------------- */
/* Offsets from O_RES.  Group by group, in the order § 7 runs them. */

/* Group M -- 22 words */
#define R_M_CU3_BEFORE	0u
#define R_M_CU3_SET	1u
#define R_M_CU3_REST	2u
#define R_M_STATUS	3u
#define R_M_CP3		4u	/* 4..19: eight registers x (prime1, prime2) */
#define R_M_TRAPS	20u	/* bit n = CP3 register n trapped            */
#define R_M_CAUSE	21u

/* Group T -- 18 words */
#define R_T_LIVE_A	22u
#define R_T_LIVE_B	23u	/* back to back                              */
#define R_T_LIVE_C	24u
#define R_T_LIVE_D	25u	/* separated by a calibrated loop            */
#define R_T_OVH1	26u
#define R_T_OVH100	27u
#define R_T_OVH1K	28u
#define R_T_OVH4K	29u
#define R_T_CAL_HI	30u
#define R_T_CAL_LO	31u
#define R_T_HIT_WARM	32u
#define R_T_HIT_KS0	33u
#define R_T_HIT_KS1	34u
#define R_T_TC1CNT	35u
#define R_T_TCCNR	36u
#define R_T_TCIR	37u
#define R_T_RAW0	38u
#define R_T_RAW1	39u

/* Group W -- 44 words */
#define R_W_LINE	40u	/* 40..42: bits lo, bits hi, n_other          */
#define R_W_LINE0	43u	/* 43..45 */
#define R_W_BACK	46u	/* 46..48 */
#define R_W_BACK2	49u	/* 49..51 */
#define R_W_SIZE	52u	/* 52..65: 7 points x (n_fresh, n_other)      */
#define R_W_IMEM	66u	/* 66..79: 7 points x (n_fresh, n_other)      */
#define R_W_ARMFRESH	80u	/* summed over every arming execution; MUST be 0 */
#define R_W_ASSOC	81u	/* 81..83: (T,M) packed, K, the cap that bit  */

/* Group V -- 24 words */
#define R_V_LINE	84u	/* 84..86 */
#define R_V_SIZE	87u	/* 87..98: 6 points x (n_fresh, n_other)      */
#define R_V_ARMFRESH	99u
#define R_V_ASSOC	100u	/* 100..102 */
#define R_V_DMEM_BASE	103u
#define R_V_DMEM_TOP	104u
#define R_V_ARENA	105u
#define R_V_SPARE	106u	/* 106..107 */

/* Group C -- 60 words, twelve cells of five:
 *      l1  the allocate's reading      l2  THE MEASUREMENT
 *      l3  the uncached read-back      l2b member b's measurement
 *      vd  the verdict, and member b's verdict in bits 15:8 */
#define R_C		108u
#define R_C_STRIDE	5u
#define C_A0		0u
#define C_A		1u
#define C_A2		2u	/* the second separation */
#define C_E		3u
#define C_E0		4u
#define C_E2		5u
#define C_F		6u
#define C_B		7u
#define C_C		8u
#define C_D		9u
#define C_G		10u
#define C_SPARE		11u
#define C_CELLS		12u

/* Group X -- 20 words */
#define R_X		168u	/* 168..182: five cells x (exc, cause, epc)   */
#define R_X_STRIDE	3u
#define X_RI		0u
#define X_11		1u
#define X_10		2u
#define X_15		3u
#define X_19		4u
#define X_CELLS		5u
#define R_X_SCRATCH	183u	/* 183..185: the word and its two neighbours,
				 * XORed before against after                 */
#define R_X_FUNC	186u	/* 186..187: x-10's functional leg           */

/* Group S -- 4 words */
#define R_S_BEFORE	188u
#define R_S_SET		189u
#define R_S_REST	190u
#define R_S_VERDICT	191u

typedef char res_area_is_full[(R_S_VERDICT + 1u == RB_RES) ? 1 : -1];

/* --- verdict nibbles, shared with cells.S -------------------------------- */
#define V_NEVER		0x0u
#define V_STALE		0x1u
#define V_FRESH		0x2u
#define V_VOIDPRIME	0x4u
#define V_NOTVICTIM	0x5u
#define V_WEIRD		0x6u
#define V_CORRUPT	0x7u

/* --- Group C verdicts ----------------------------------------------------- */
#define CV_UNRUN	0x00u
#define CV_P0		0x01u	/* the measurement read the FIRST value  */
#define CV_P1		0x02u	/* ... the second                        */
#define CV_OTHER	0x03u
#define CV_VOID_NOSTALE	0x10u	/* c-A was negative: nothing to invalidate */
#define CV_VOID_NORESID	0x11u	/* residency not established               */
#define CV_VOID_GATE	0x12u	/* an upstream gate refused it             */
#define CV_VOID_SETUP	0x13u	/* a store did not land; the cell never ran */

/* --- the address map ------------------------------------------------------ */
/* 🔴 ONLY ONE SPAN OF DRAM ON THIS DEVICE HAS POSITIVE EVIDENCE OF BEING FREE
 * at the loader prompt: 0x80A00000-0x80AF1002 held a 987,138-byte image across
 * a complete TFTP upload AND download, byte-identical, with the loader's own
 * network stack live throughout (量 `G4`, 2026-08-24d).  Everywhere else the
 * case is *"nothing has read it"*, and MEM-14 is this device's own
 * counterexample: 0x81000000 was exactly that kind of address until three
 * captures showed the boot path writes it on every boot.
 *
 * probe1's block is at 0x80A00000 (160 words) and probe2's at 0x80A01000 (817).
 * Both hold measurements recovered from DRAM after their seatings.  probe3's is
 * at 0x80A02000 and the arena starts a whole 64 KiB above it. */
#define ARENA		0x80A10000u
#define ARENA_END	0x80A90000u

/*      offset       size     what
 *      0x00000      1 KiB    w-line's block
 *      0x08000      1 KiB    w-line0's block, deliberately distant, and
 *                            +0x400 of it is x-10's functional leg
 *      0x10000      1 KiB    w-back
 *      0x18000      1 KiB    w-back2
 *      0x20000     64 KiB    the I-side sweep
 *      0x30000     64 KiB    the D-side sweep
 *      0x40000     32 KiB    Group C's targets, and Group X's scratch word
 *      0x48000    224 KiB    both associativity sweeps
 *
 * The 512 KiB is inside the proven span and it is fully accounted for above;
 * nothing in this payload writes outside it except its own result block. */
#define A_PAT_LINE	(ARENA + 0x00000u)
#define A_PAT_LINE0	(ARENA + 0x08000u)
#define A_PAT_BACK	(ARENA + 0x10000u)
#define A_PAT_BACK2	(ARENA + 0x18000u)
#define A_WSIZE		(ARENA + 0x20000u)
#define A_VSIZE		(ARENA + 0x30000u)
#define A_COH		(ARENA + 0x40000u)
#define A_XSCRATCH	(ARENA + 0x47000u)
#define A_ASSOC		(ARENA + 0x48000u)
#define A_ASSOC_SPAN	0x38000u

/* Group C's two targets are FAR APART and the separation is deliberately not a
 * power of two.  *Far apart* defeats LINE SHARING; it does not defeat SET
 * CONFLICT, which happens at multiples of (cache size / ways) -- and both of
 * those are exactly what Group V is there to measure, with associativity 留白.
 * So `c-A` runs at TWO separations and an eviction artefact shows up as a
 * disagreement between them rather than as a negative result that would void
 * Group C and Group V together. */
#define COH_SEP1	0x1400u		/*  5 KiB */
#define COH_SEP2	0x2C00u		/* 11 KiB */

/* --- the sweep points ----------------------------------------------------- */
#define W_POINTS	7u
#define V_POINTS	6u
#define W_STRIDE	32u	/* I side: a victim is 8 bytes, so 32 is four of
				 * them and it is under any plausible line   */
#define V_STRIDE_DEFAULT 16u	/* D side: the predicted line, re-derived from
				 * v-line's MEASURED value before the sweep  */
static const u32 W_KIB[W_POINTS] = { 1u, 2u, 4u, 8u, 16u, 32u, 64u };
static const u32 V_KIB[V_POINTS] = { 1u, 2u, 4u, 8u, 16u, 32u };

/* --- the pattern-cell offset lists --------------------------------------- */
/* Word 0 is the count; words 1.. are byte offsets from the block base.  The
 * FIRST entry is V0 -- the one that is executed before the patch -- and it is
 * the must-fire: V0 was demonstrably fetched, so at any line size >= 4 B it
 * MUST read STALE.  Without that, *all FRESH* is indistinguishable from an
 * 8-byte line, a patch that missed, and a dead re-arm.
 *
 * 🔴 THE PROBES RUN OUT TO +320 AND THE VOID GATE IS AT +256, BECAUSE 128 IS A
 * LEGAL LINE SIZE ON THIS FAMILY.  LX4189 § 5.1: *"configurable for a 16, 32,
 * 64, or 128-byte cache line size"*, and § 5.6: *"the cache obtains a cache line
 * (4, 8, 16, or 32 words)"*.  The cell table's first draft stopped at +192 and
 * called a STALE run reaching it *"past any plausible line"* -- which would have
 * recorded a real 128-byte line as a void measurement. */
static const u32 L_LINE[]  = { 13u, 0u, 8u, 16u, 24u, 32u, 48u, 64u, 96u,
			       128u, 160u, 192u, 256u, 320u };
static const u32 L_BACK[]  = { 12u, 136u, 0u, 64u, 104u, 112u, 120u, 128u,
			       144u, 152u, 168u, 192u, 256u };
static const u32 L_BACK2[] = {  9u, 152u, 128u, 136u, 144u, 160u, 168u, 176u,
			       184u, 192u };
static const u32 L_VLINE[] = { 13u, 0u, 4u, 8u, 12u, 16u, 20u, 24u, 32u, 48u,
			       64u, 96u, 128u, 192u };
static const u32 L_V0ONLY[] = { 1u, 0u };
static const u32 L_V0BACK[] = { 1u, 136u };
static const u32 L_V0BACK2[] = { 1u, 152u };

/* --- state ---------------------------------------------------------------- */
static u32 rb_ks0;
static u32 rb_ks1;

static u32 wctl[16];		/* cells.S's walk control block   */
static u32 cctl_blk[16];	/* cells.S's coherence block */
static u32 poke_out[4];		/* rlx_status_poke's three words   */
static u32 tc_raw[2];
static u32 saved_vec[64];
static u32 cells_run, cells_void, rows_used;
static u32 g_hbrk, g_ca, g_cf, g_x11, g_timer;
static u32 arena_moved;
static u32 v_stride;
static u32 arm_fresh_i, arm_fresh_d;

u32 rlx_exc_rec[4];		/* exc.S forms this address with lui/addiu */

static u32 ins_changed, ins_bad, ins_firstbad;

extern u32 rlx_exc_entry[];
extern u32 rlx_exc_end[];
extern u32 rlx_vic_template[];
extern u32 rlx_cp3_stubs[];

/* cells.S */
u32  rlx_status_or(u32 orbits);
void rlx_status_write(u32 v);
u32  rlx_status_poke(u32 orbits, u32 *out_ks1);
u32  rlx_lw_unc_primed(u32 addr, u32 prime);
u32  rlx_tc_spin(u32 spins, u32 *raw_ks1);
u32  rlx_tc_reads(u32 k, u32 *raw_ks1);
u32  rlx_tc_walk(u32 base, u32 passes, u32 *raw_ks1);
void rlx_w_arm(u32 ctl_ks1, u32 list_ks1);
void rlx_w_patch(u32 ctl_ks1, u32 list_ks1);
u32  rlx_w_exec(u32 ctl_ks1, u32 list_ks1);
void rlx_v_store(u32 ctl_ks1, u32 word);
void rlx_v_touch(u32 ctl_ks1, u32 unused);
u32  rlx_v_read(u32 ctl_ks1, u32 list_ks1);
void rlx_c_seq(u32 cc_ks1, u32 do_load1);
void rlx_c_seq_e(u32 cc_ks1, u32 unused);
void rlx_c_seq_g(u32 cc_ks1, u32 unused);
void rlx_c_seq_d(u32 cc_ks1, u32 unused);
void rlx_x_cache10(u32 addr);
void rlx_x_cache11(u32 addr);
void rlx_x_cache15(u32 addr);
void rlx_x_cache19(u32 addr);
void rlx_x_ri(void);
void rlx_cctl2(u32 cmd1, u32 cmd2);

/* The build stamp.  A build that cannot say what it is cannot be checked from a
 * capture.  0x50 is 'P', so a zero word is distinguishable from a build with
 * every knob off.  `make show` prints this number from the same expression
 * rather than from a second copy of it. */
#define FLUSH_CMD	CCTL_IINVAL
#define FLAGS_W		(0x50000000u | ((u32)FLUSH_CMD & 0xFFFFu) \
			 | ((u32)RLX_RESET     << 16) \
			 | ((u32)RLX_CLEAR_BEV << 17) \
			 | ((u32)RLX_RET_ERET  << 18) \
			 | ((u32)RLX_ISC       << 19) \
			 | ((u32)RLX_GEOM      << 20))

#define VEC_UTLB	((u32)RLX_VEC_UTLB)
#define VEC_GENERAL	((u32)RLX_VEC_GENERAL)
#define VEC_WORDS	32u

/* --- block access --------------------------------------------------------- */
static void rb_put(u32 i, u32 v) { *(volatile u32 *)(rb_ks1 + i * 4u) = v; }
static u32  rb_get(u32 i)        { return *(volatile u32 *)(rb_ks1 + i * 4u); }
static void res_put(u32 i, u32 v){ rb_put(O_RES + i, v); }

static u32 rd_unc(u32 a)         { return *(volatile u32 *)(a | KSEG1_BIT); }
static void wr_unc(u32 a, u32 v) { *(volatile u32 *)(a | KSEG1_BIT) = v; }

static u32 exc_rec(u32 n)        { return rd_unc((u32)&rlx_exc_rec[n]); }
static void exc_set(u32 n, u32 v){ wr_unc((u32)&rlx_exc_rec[n], v); }

static void progress(u32 p)      { rb_put(H_PROGRESS, p); }

static void field(const char *name, u32 v)
{
	rlx_puts("rlxprobe: ");
	rlx_puts(name);
	rlx_putc('=');
	rlx_puthex32(v);
	rlx_puts("\r\n");
}

static void pair(const char *name, u32 v)
{
	rlx_putc(' ');
	rlx_puts(name);
	rlx_putc('=');
	rlx_puthex32(v);
}

/* --- the sixteen named rows ---------------------------------------------- */
/*
 * ⚠️ `ex` IN THESE ROWS IS RECONSTRUCTED FROM THE VERDICT NIBBLE, AND SAYING SO
 * IS THE POINT.  probe1's eight-word row carries the value the victim actually
 * returned, so a verdict can be re-derived at the desk if the verdict FUNCTION
 * is later found wrong -- and probe1's own history is exactly that (the audit
 * found `rlx_call0` never wrote `$2`, and every trapped row's `v` was carrying a
 * loop counter).  A nibble cannot carry `ex`, and the walk has no register left
 * to keep it in.
 *
 * What is kept instead: `mb`, `ma` and `g` here are UNCACHED READS OF DRAM taken
 * now, and DRAM does not move -- those three are raw.  And the raw value of the
 * first victim in each pass whose return matched neither constant is kept in the
 * walk's own control block, which is the only case where the nibble and the
 * value disagree about anything.
 */
static void rb_row(u32 tag, u32 vaddr, u32 primed, u32 executed,
		   u32 mem_before, u32 mem_after, u32 guard, u32 verdict)
{
	u32 b;

	if (rows_used >= RB_ROWS)
		return;
	b = O_ROWS + rows_used * RB_ROWW;
	rb_put(b + 0u, tag);
	rb_put(b + 1u, vaddr);
	rb_put(b + 2u, primed);
	rb_put(b + 3u, executed);
	rb_put(b + 4u, mem_before);
	rb_put(b + 5u, mem_after);
	rb_put(b + 6u, guard);
	rb_put(b + 7u, verdict);

	rlx_puts("rlxprobe:");
	pair("t", tag);
	pair("v", vaddr);
	pair("pr", primed);
	pair("ex", executed);
	pair("mb", mem_before);
	pair("ma", mem_after);
	pair("g", guard);
	pair("vd", verdict);
	rlx_puts("\r\n");

	rows_used++;
	rb_put(H_ROWS_USED, rows_used);
}

/* Reconstruct `ex` from the nibble and read the three raw memory words back. */
static u32 nib_ex(u32 nibble)
{
	if (nibble == V_STALE)
		return (u32)RLX_VICTIM_OLD;
	if (nibble == V_FRESH)
		return (u32)RLX_VICTIM_NEW;
	if (nibble == V_VOIDPRIME)
		return 0xFFFFFFFFu;
	return 0u;		/* not reconstructible; the nibble is the datum */
}

static void row_victim(u32 tag, u32 vaddr, u32 nibble)
{
	rb_row(tag, vaddr, 0xFFFFFFFFu, nib_ex(nibble),
	       (u32)RLX_VICTIM_WORD_OLD, rd_unc(vaddr + 4u), rd_unc(vaddr),
	       nibble);
}

static void row_target(u32 tag, u32 addr, u32 nibble)
{
	rb_row(tag, addr, 0xFFFFFFFFu, nib_ex(nibble),
	       (u32)RLX_VICTIM_WORD_OLD, rd_unc(addr), 0u, nibble);
}

/* --- the bitmap ----------------------------------------------------------- */
static u32 bmp_nib(u32 k)
{
	u32 w = rb_get(O_BMP + (k >> 3));

	return (w >> ((7u - (k & 7u)) * 4u)) & 0xFu;
}

static void bmp_clear(void)
{
	u32 i;

	for (i = 0; i < RB_BMPW; i++)
		rb_put(O_BMP + i, 0u);
}

/* The index of the first victim whose nibble is neither STALE nor FRESH, or
 * 0xFFFFFFFF.  The walk has no register to keep this in; the bitmap is already
 * there, so it is read out here instead of measured twice. */
static u32 bmp_first_bad(u32 count)
{
	u32 k, n;

	for (k = 0; k < count && k < RB_BMPW * 8u; k++) {
		n = bmp_nib(k);
		if (n != V_STALE && n != V_FRESH)
			return k;
	}
	return 0xFFFFFFFFu;
}

/* Pack up to eight nibbles of a pattern cell into one word, big end first, so a
 * reader sees the probes in the order the list names them. */
static u32 bmp_pack(u32 from, u32 n)
{
	u32 i, w = 0;

	for (i = 0; i < 8u; i++)
		w = (w << 4) | ((i < n) ? bmp_nib(from + i) : 0u);
	return w;
}

/* --- the walk driver ------------------------------------------------------ */
static void wctl_set(u32 base, u32 stride, u32 count, u32 want_bmp)
{
	wr_unc((u32)&wctl[0], base);
	wr_unc((u32)&wctl[1], stride);
	wr_unc((u32)&wctl[2], count);
	wr_unc((u32)&wctl[3], want_bmp ? ((rb_ks1) + O_BMP * 4u) : 0u);
	wr_unc((u32)&wctl[4], 0u);
	wr_unc((u32)&wctl[5], 0u);
	wr_unc((u32)&wctl[6], 0u);
	wr_unc((u32)&wctl[7], 0u);
	wr_unc((u32)&wctl[9], (u32)rlx_vic_template | (u32)KSEG1_BIT);
}

static u32 wctl_get(u32 i) { return rd_unc((u32)&wctl[i]); }
#define WCTL_KS1	((u32)&wctl[0] | (u32)KSEG1_BIT)
#define CBLK_KS1	((u32)&cctl_blk[0] | (u32)KSEG1_BIT)

static void flush_i(void)
{
	rlx_call2_uncached((u32)rlx_cctl, (u32)FLUSH_CMD, 0u);
}

/* One I-side measurement point.  Returns n_fresh from the final execution and
 * leaves n_other in the control block.
 *
 * THE RE-ARM IS `CCTL 0x002` PLUS A REWRITE OF THE ARENA TO OLD, AND ITS
 * DETECTOR IS FREE.  Neither `w-line0` nor the 1 KiB control can detect a broken
 * re-arm: `w-line0` never fetched anything, so a failed invalidate leaves
 * nothing behind, and a stale line left in place reads STALE, which is the 1 KiB
 * control's own expected value.  The detector is THE ARMING EXECUTION'S OWN
 * READING -- after the rewrite to OLD, every victim's first execution MUST
 * return OLD, and a victim returning NEW there proves the invalidate did not
 * take.  It is summed into `arm_fresh_i` across every point in the payload. */
static u32 w_point(u32 base, u32 stride, u32 count, u32 want_bmp,
		   const u32 *list, u32 exec_v0_only)
{
	u32 lks1 = list ? ((u32)list | (u32)KSEG1_BIT) : 0u;
	u32 n;

	wctl_set(base, stride, count, 0u);
	rlx_call2_uncached((u32)rlx_w_arm, WCTL_KS1, lks1);
	flush_i();

	/* the arming execution, and its own reading is the re-arm detector */
	if (exec_v0_only) {
		/* the pattern cells fetch V0 alone: the probes must NOT be in
		 * the I-cache before the patch, or every one of them reads
		 * STALE for a reason that has nothing to do with the line. */
		const u32 *one = (list == L_LINE)  ? L_V0ONLY :
				 (list == L_BACK)  ? L_V0BACK :
				 (list == L_BACK2) ? L_V0BACK2 : L_V0ONLY;
		wctl_set(base, stride, 1u, 0u);
		arm_fresh_i += rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1,
						  (u32)one | (u32)KSEG1_BIT);
	} else {
		wctl_set(base, stride, count, 0u);
		arm_fresh_i += rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1,
						  lks1);
	}

	wctl_set(base, stride, count, 0u);
	rlx_call2_uncached((u32)rlx_w_patch, WCTL_KS1, lks1);

	wctl_set(base, stride, count, want_bmp);
	n = rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1, lks1);
	return n;
}

/* `w-line0` is the negative control: V0 is never executed, so nothing was
 * fetched and nothing can be stale.  Any STALE means the patch is not landing or
 * the arena is contaminated, and `w-line` is void. */
static u32 w_point_nofetch(u32 base, u32 count, const u32 *list)
{
	u32 lks1 = (u32)list | (u32)KSEG1_BIT;

	wctl_set(base, 0u, count, 0u);
	rlx_call2_uncached((u32)rlx_w_arm, WCTL_KS1, lks1);
	flush_i();
	wctl_set(base, 0u, count, 0u);
	rlx_call2_uncached((u32)rlx_w_patch, WCTL_KS1, lks1);
	wctl_set(base, 0u, count, 1u);
	return rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1, lks1);
}

/* One D-side measurement point.  The observation channel -- *an uncached write
 * is invisible to a resident clean line* -- IS `c-A`'s positive reading, which
 * is why Group V does not run at all unless `c-A` was positive. */
static u32 v_point(u32 base, u32 stride, u32 count, u32 want_bmp,
		   const u32 *list)
{
	u32 lks1 = list ? ((u32)list | (u32)KSEG1_BIT) : 0u;
	u32 n;

	wctl_set(base, stride, count, 0u);
	rlx_call2_uncached((u32)rlx_v_store, WCTL_KS1,
			   (u32)RLX_VICTIM_WORD_OLD);
	rlx_call2_uncached((u32)rlx_v_touch, WCTL_KS1, 0u);
	arm_fresh_d += rlx_call2_uncached((u32)rlx_v_read, WCTL_KS1, lks1);

	wctl_set(base, stride, count, 0u);
	rlx_call2_uncached((u32)rlx_v_store, WCTL_KS1,
			   (u32)RLX_VICTIM_WORD_NEW);
	wctl_set(base, stride, count, want_bmp);
	n = rlx_call2_uncached((u32)rlx_v_read, WCTL_KS1, lks1);
	return n;
}

/* --- Group C -------------------------------------------------------------- */
static void cc_set(u32 x, u32 p0, u32 p1, u32 cmd1, u32 cmd2,
		   u32 drain, u32 drain_n)
{
	wr_unc((u32)&cctl_blk[0], x);
	wr_unc((u32)&cctl_blk[1], x | (u32)KSEG1_BIT);
	wr_unc((u32)&cctl_blk[2], p0);
	wr_unc((u32)&cctl_blk[3], p1);
	wr_unc((u32)&cctl_blk[4], cmd1);
	wr_unc((u32)&cctl_blk[5], cmd2);
	wr_unc((u32)&cctl_blk[6], drain);
	wr_unc((u32)&cctl_blk[7], drain_n);
	wr_unc((u32)&cctl_blk[8], 0u);
	wr_unc((u32)&cctl_blk[9], 0u);
	wr_unc((u32)&cctl_blk[10], 0u);
}

static u32 cc_get(u32 i) { return rd_unc((u32)&cctl_blk[i]); }

/* The two values.  They differ in many bits and neither is a plausible bias
 * word: MEM-16 measured this DRAM's uninitialised bias as 89.5 % reproducible
 * against a measured null of 55.98 %, so bit-level accidents are a live category
 * here rather than a theoretical one. */
#define C_VAL0		0xA5A50001u
#define C_VAL1		0x5A5A0002u

/* The four sequence shapes cells.S carries. */
#define K_SEQ		0u	/* c-A0, c-A, c-F, c-B, c-C */
#define K_G		1u	/* c-G  -- does an uncached READ invalidate */
#define K_D		2u	/* c-D  -- `cache 0x11` as the treatment    */
#define K_E		3u	/* c-E, c-E0, c-E2 -- the write HIT         */

static u32 cv_of(u32 v)
{
	if (v == C_VAL0)
		return CV_P0;
	if (v == C_VAL1)
		return CV_P1;
	return CV_OTHER;
}

/* Run one coherence cell on ONE target and return its verdict.
 *
 * WHICH WORD IS THE MEASUREMENT DEPENDS ON THE SHAPE, and getting that wrong
 * would be a cell that reports the setup check as its answer:
 *
 *      K_SEQ / K_D   l1 the allocate, l2 THE MEASUREMENT, l3 the setup check
 *      K_G           l1 the allocate, l2 the claimed invalidator's own read,
 *                    l3 THE MEASUREMENT
 *      K_E           l1 the allocate, l3 THE MEASUREMENT, l2 unused
 */
static u32 c_one(u32 kind, u32 x, u32 cmd1, u32 cmd2, u32 do_load1,
		 u32 drain, u32 drain_n, u32 *l1, u32 *l2, u32 *l3)
{
	cc_set(x, C_VAL0, C_VAL1, cmd1, cmd2, drain, drain_n);
	switch (kind) {
	case K_G:
		rlx_call2_uncached((u32)rlx_c_seq_g, CBLK_KS1, 0u);
		break;
	case K_D:
		rlx_call2_uncached((u32)rlx_c_seq_d, CBLK_KS1, 0u);
		break;
	case K_E:
		rlx_call2_uncached((u32)rlx_c_seq_e, CBLK_KS1, 0u);
		break;
	default:
		rlx_call2_uncached((u32)rlx_c_seq, CBLK_KS1, do_load1);
		break;
	}
	*l1 = cc_get(8u);
	*l2 = cc_get(9u);
	*l3 = cc_get(10u);

	/* THE SETUP CHECK THAT VOIDS THE CELL BEFORE ITS VERDICT IS READ.
	 * `l1 != first value` means the first store did not land -- so nothing
	 * downstream of it means anything.  For K_SEQ and K_D the final uncached
	 * load must also read the second value, or the second store did not
	 * land either. */
	if (do_load1 && cv_of(*l1) != CV_P0)
		return CV_VOID_SETUP;
	if ((kind == K_SEQ || kind == K_D) && cv_of(*l3) != CV_P1)
		return CV_VOID_SETUP;
	if (kind == K_G || kind == K_E)
		return cv_of(*l3);
	return cv_of(*l2);
}

static void c_cell(u32 slot, const char *name, u32 kind, u32 xa, u32 xb,
		   u32 cmd1, u32 cmd2, u32 do_load1, u32 drain, u32 drain_n)
{
	u32 l1, l2, l3, va, vb, l1b, l2b, l3b;
	u32 base = R_C + slot * R_C_STRIDE;

	va = c_one(kind, xa, cmd1, cmd2, do_load1, drain, drain_n,
		   &l1, &l2, &l3);
	vb = c_one(kind, xb, cmd1, cmd2, do_load1, drain, drain_n,
		   &l1b, &l2b, &l3b);

	/* Member b is recorded as its MEASUREMENT and its verdict, not in full.
	 * The pair exists to cross-check eviction -- probe1's two-victims-far-
	 * apart trick -- and what carries that is a DISAGREEMENT between the two
	 * verdicts.  Member a is recorded in full, which is where the raw words
	 * a later correction would need actually are. */
	res_put(base + 0u, l1);
	res_put(base + 1u, l2);
	res_put(base + 2u, l3);
	res_put(base + 3u, (kind == K_G || kind == K_E) ? l3b : l2b);
	res_put(base + 4u, va | (vb << 8));
	cells_run++;
	if (va != vb)
		rlx_puts("rlxprobe: c PAIR DISAGREES -- an eviction artefact, "
			 "not a coherence reading\r\n");

	rlx_puts("rlxprobe: c ");
	rlx_puts(name);
	pair("l1", l1);
	pair("l2", l2);
	pair("l3", l3);
	pair("mb", (kind == K_G || kind == K_E) ? l3b : l2b);
	pair("vd", va | (vb << 8));
	rlx_puts("\r\n");
	(void)l1b;
}

static void c_void(u32 slot, const char *name, u32 why)
{
	u32 base = R_C + slot * R_C_STRIDE;

	res_put(base + 0u, 0u);
	res_put(base + 1u, 0u);
	res_put(base + 2u, 0u);
	res_put(base + 3u, 0u);
	res_put(base + 4u, why);
	cells_void++;

	rlx_puts("rlxprobe: c ");
	rlx_puts(name);
	rlx_puts(" VOID ");
	rlx_puthex32(why);
	rlx_puts("\r\n");
}

/* --- Group X -------------------------------------------------------------- */
/* 否證 ⓒ, and the payload obeys it literally: a `cache` instruction that neither
 * retires nor traps -- the payload hangs -- refutes the handler, not the
 * instruction.  SO THE ROW IS WRITTEN TO THE BLOCK BEFORE THE INSTRUCTION IS
 * ISSUED, exactly as probe1 does. */
static u32 x_scratch;

static u32 x_cell(u32 slot, const char *name, void (*fn)(u32), u32 addr)
{
	u32 base = R_X + slot * R_X_STRIDE;
	u32 before, after, b0, b1, b2, a0, a1, a2;

	/* the row FIRST, so a hang leaves a block that says which cell it was in */
	res_put(base + 0u, 0xFFFFFFFFu);	/* "issued, no result yet" */
	res_put(base + 1u, 0u);
	res_put(base + 2u, 0u);
	rlx_puts("rlxprobe: x ");
	rlx_puts(name);
	rlx_puts(" ISSUING\r\n");

	b0 = rd_unc(x_scratch - 4u);
	b1 = rd_unc(x_scratch);
	b2 = rd_unc(x_scratch + 4u);
	before = exc_rec(0u);
	if (fn)
		fn(addr);
	else
		rlx_x_ri();
	after = exc_rec(0u);
	a0 = rd_unc(x_scratch - 4u);
	a1 = rd_unc(x_scratch);
	a2 = rd_unc(x_scratch + 4u);

	res_put(base + 0u, after - before);
	res_put(base + 1u, (after != before) ? exc_rec(1u) : 0u);
	res_put(base + 2u, (after != before) ? exc_rec(2u) : 0u);
	cells_run++;

	rlx_puts("rlxprobe: x ");
	rlx_puts(name);
	pair("n", after - before);
	pair("cause", (after != before) ? exc_rec(1u) : 0u);
	pair("epc", (after != before) ? exc_rec(2u) : 0u);
	pair("dw", (b0 ^ a0) | (b1 ^ a1) | (b2 ^ a2));
	rlx_puts("\r\n");

	/* THE SCRATCH WORD OR A NEIGHBOUR CHANGING is a finding in its own
	 * right: it means 0x2F decodes as something else on this core. */
	return ((b0 ^ a0) | (b1 ^ a1) | (b2 ^ a2)) ? 2u :
	       ((after != before) ? 1u : 0u);	/* 0 retired, 1 trapped, 2 wrote */
}

/* --- the timer ------------------------------------------------------------ */
/* TC0CNT's count field is bits 31:4 (量 REG-05), the wrap is 142,858 ticks and
 * 142,858 IS NOT A POWER OF TWO, so a masked subtraction is wrong.  Valid for
 * one wrap only; every window in this payload stays under 3 ms of a 9.9998 ms
 * wrap. */
#define TC_WRAP		142858u

static u32 tc_prime_bad(u32 raw)
{
	return ((raw & 0xFFFF0000u) == 0xC0DE0000u) ||
	       ((raw & 0xFFFF0000u) == 0xD1CE0000u);
}

static u32 tc_ticks(u32 before, u32 after)
{
	u32 a, b;

	if (tc_prime_bad(before) || tc_prime_bad(after))
		return 0xFFFFFFFFu;	/* the load did not write its destination */
	a = after >> 4;
	b = before >> 4;
	return (a >= b) ? (a - b) : (a + TC_WRAP - b);
}

static u32 tc_bracket(u32 (*fn)(u32, u32 *), u32 arg)
{
	u32 raw = (u32)&tc_raw[0] | (u32)KSEG1_BIT;

	(void)fn(arg, (u32 *)raw);
	return tc_ticks(rd_unc((u32)&tc_raw[0]), rd_unc((u32)&tc_raw[1]));
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
	ins_firstbad = 0xFFFFFFFFu;

	if (words * 4u > VEC_WORDS * 4u)
		return 0u;

	for (i = 0; i < words; i++) {
		wr_unc(VEC_UTLB + i * 4u, rlx_exc_entry[i]);
		wr_unc(VEC_GENERAL + i * 4u, rlx_exc_entry[i]);
	}
	flush_i();

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

/* --- main ----------------------------------------------------------------- */
void rlxprobe_main(void)
{
	u32 pc, flags, status, i, j, words, sum;
	u32 nf, no, first_bad;
	u32 boundary, bnd_count, cap = 0u;
	u32 c_size, t, m, k;
	u32 imem_base = 0u, imem_top = 0u, dmem_base = 0u, dmem_top = 0u;
	u32 m_traps = 0u;
	u32 v_arena;
	u32 w_imem_differs = 0u;

	rb_ks0 = (u32)RLX_RESULT_BASE;
	rb_ks1 = rb_ks0 | (u32)KSEG1_BIT;

	/* FIRST, before the banner and before any measurement.  MEM-15: this
	 * DRAM keeps its CONTENTS across a short power-off, so a block left by
	 * the previous payload reads exactly like this one's.  A run that dies
	 * before its first cell then shows a poisoned block, which is a
	 * different observation from the previous run's data. */
	for (i = 0; i < RB_POISON_W; i++)
		rb_put(i, RB_POISON);

	pc = rlx_pc();

#if RLX_CLEAR_BEV
	/* qemu ONLY.  Its 24Kf leaves BEV set after `-kernel`, and BEV set is
	 * the one state this payload refuses to install into.  A device build
	 * has RLX_CLEAR_BEV=0 and tools/test-rlxprobe.sh asserts it. */
	rlx_status_write(rlx_mfc0_status() & ~(u32)ST0_BEV);
	rlx_puts("rlxprobe: WARNING RLX_CLEAR_BEV=1 -- this is a qemu build\r\n");
#endif
	status = rlx_mfc0_status();

	/* Running from KSEG1 would make every cache cell vacuous, and it is one
	 * mistyped `J A0500000` away.  The payload says which window it is in
	 * rather than assuming the operator typed what the sheet says -- in a
	 * word of its own, see H_KSEG0. */
	flags = FLAGS_W;
	rb_put(H_KSEG0, ((pc & KSEG_MASK) == (u32)KSEG0_BASE) ? 1u : 0u);

	rb_put(H_MAGIC, RB_MAGIC);
	rb_put(H_NONCE, RLX_NONCE_W);
	rb_put(H_VERSION, RB_VERSION);
	rb_put(H_PC, pc);
	rb_put(H_FLAGS, flags);
	rb_put(H_RB, rb_ks0);
	rb_put(H_STATUS, status);
	rb_put(H_VEC, VEC_GENERAL);
	rb_put(H_ARENA, ARENA);
	rb_put(H_ARENA_END, ARENA_END);
	rb_put(H_TMPL, (u32)rlx_vic_template);
	rb_put(H_TMPL_W0, rd_unc((u32)&rlx_vic_template[0]));
	rb_put(H_TMPL_W1, rd_unc((u32)&rlx_vic_template[1]));
	rb_put(H_LAYOUT_RES, O_RES);
	rb_put(H_LAYOUT_ROWS, O_ROWS);
	rb_put(H_LAYOUT_BMP, O_BMP);
	rb_put(H_LAYOUT_SEAL, O_SEAL);
	rb_put(H_SEAL_KIND, 1u);
	progress(P_HEADER);

	rlx_puts("\r\n*** rlxprobe P3 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("flags", flags);
	field("status", status);
	field("arena", ARENA);
	field("tmpl", rd_unc((u32)&rlx_vic_template[0]));
	field("kseg0", rb_get(H_KSEG0));
	if (rb_get(H_KSEG0) == 0u)
		rlx_puts("rlxprobe: NOT IN KSEG0 -- every cache cell is void\r\n");

	/* THE TEMPLATE'S OWN CONTROL.  Every victim in the arena is a copy of
	 * these two words; if the guard is not `jr $31` the walk would be
	 * jumping into whatever it wrote, and there would be nothing to notice
	 * it with.  This is a build-time constant read back from the emitted
	 * image at run time, which is the only version of the check that can
	 * fail. */
	if (rd_unc((u32)&rlx_vic_template[0]) != (u32)RLX_VIC_GUARD ||
	    rd_unc((u32)&rlx_vic_template[1]) != (u32)RLX_VICTIM_WORD_OLD) {
		rlx_puts("rlxprobe: the victim template is not what this file "
			 "assembled. Refusing to build an arena.\r\n");
		rlx_puts("rlxprobe: end\r\n");
		return;
	}

	/* --- 0. BEV, and the refusal ------------------------------------- */
	/* CPU-27.  BEV is bit 22 in the R3000 Status layout, and it is 量 0 at
	 * the prompt on this unit.  If it is set the vectors are in boot ROM and
	 * 0x80000080 is the wrong address entirely. */
	if (status & (u32)ST0_BEV) {
		rlx_puts("rlxprobe: BEV=1 -- vectors are NOT at 0x80000080. "
			 "Refusing to install.\r\n");
		rlx_puts("rlxprobe: end\r\n");
		return;
	}

	/* --- 1. Group H, and it is the gate ------------------------------ */
	/* IT MOVED TO THE FRONT FOR A REASON.  It used to be stage 4, which left
	 * the `CCTL 0x020` write -- the first command this project issues that
	 * its own loader does not issue after reset -- running with NO HANDLER
	 * INSTALLED, where any fault reaches the loader's permanent hang.  It
	 * costs nothing new: it is probe2's, measured end to end. */
	copy_vec_out();
	for (i = 0; i < 8u; i++)
		rb_put(H_SAVED0 + i, saved_vec[i + VEC_WORDS]);

	words = install_handler();
	rb_put(H_HWORDS, words);
	rb_put(H_INS_CHANGED, ins_changed);
	rb_put(H_INS_BAD, ins_bad);
	rb_put(H_INS_FIRSTBAD, ins_firstbad);
	field("handler_words", words);
	field("install.changed", ins_changed);
	field("install.bad", ins_bad);
	if (words == 0u || ins_bad != 0u) {
		field("install.firstbad", ins_firstbad);
		rlx_puts("rlxprobe: the handler is NOT at the vector. "
			 "Refusing to break.\r\n");
		copy_vec_back();
		rlx_puts("rlxprobe: end\r\n");
		return;
	}
	if (ins_changed == 0u)
		rlx_puts("rlxprobe: WARNING install.changed=0 -- the vector "
			 "already held these words, so the read-back is "
			 "vacuous\r\n");

	exc_set(0u, 0u);
	exc_set(1u, 0u);
	exc_set(2u, 0u);
	rlx_do_break();
	rb_put(H_BRK_COUNT, exc_rec(0u));
	rb_put(H_BRK_CAUSE, exc_rec(1u));
	rb_put(H_BRK_EPC, exc_rec(2u));
	field("break.count", exc_rec(0u));
	field("break.cause", exc_rec(1u));
	field("break.epc", exc_rec(2u));
	g_hbrk = (exc_rec(0u) != 0u);
	rb_put(H_G_HBRK, g_hbrk);
	if (!g_hbrk)
		rlx_puts("rlxprobe: break did not trap and the handler bytes "
			 "ARE at the vector -- Groups M and X will NOT run\r\n");
	progress(P_HANDLER);

	/* --- 2. Group T -- the cheapest thing in the payload -------------- */
	/* Four loads from an address the loader itself reads (REG-07).  Placed
	 * first because if it works, everything after it COULD carry timing. */
	res_put(R_T_LIVE_A, rlx_lw_unc_primed(RLX_TC0CNT, 0xC0DE7D00u));
	res_put(R_T_LIVE_B, rlx_lw_unc_primed(RLX_TC0CNT, 0xD1CE7D00u));
	res_put(R_T_TC1CNT, rlx_lw_unc_primed(RLX_TC0CNT + 4u, 0xC0DE7D01u));
	res_put(R_T_TCCNR,  rlx_lw_unc_primed(RLX_TC0CNT + 8u, 0xC0DE7D02u));
	res_put(R_T_TCIR,   rlx_lw_unc_primed(RLX_TC0CNT + 12u, 0xC0DE7D03u));

	/* ⚠️ EQUAL ON A BACK-TO-BACK PAIR IS NOT A REFUTATION AND DOES NOT VOID
	 * THE GROUP.  One tick is 69.9983 ns and `t-ovh` is what says whether an
	 * uncached register read costs more than that; back to back the two
	 * reads may be closer than the LSB, and *equal* would then be the
	 * reading of a perfectly live counter.  The separated pair is the one
	 * that decides. */
	res_put(R_T_CAL_HI, tc_bracket(rlx_tc_spin, 140800u));
	res_put(R_T_LIVE_C, rd_unc((u32)&tc_raw[0]));
	res_put(R_T_LIVE_D, rd_unc((u32)&tc_raw[1]));
	res_put(R_T_CAL_LO, tc_bracket(rlx_tc_spin, 70400u));
	res_put(R_T_RAW0, rd_unc((u32)&tc_raw[0]));
	res_put(R_T_RAW1, rd_unc((u32)&tc_raw[1]));

	res_put(R_T_OVH1,   tc_bracket(rlx_tc_reads, 1u));
	res_put(R_T_OVH100, tc_bracket(rlx_tc_reads, 100u));
	res_put(R_T_OVH1K,  tc_bracket(rlx_tc_reads, 1000u));
	res_put(R_T_OVH4K,  tc_bracket(rlx_tc_reads, 4000u));

	/* `t-hit`: a 4 KiB working set -- half the predicted D-cache --
	 * traversed 32 times at 16 B stride, once through KSEG0 and once
	 * through KSEG1, WITH ONE WARMING PASS DISCARDED.  The iteration count
	 * carries N and the footprint does not: after the warming pass every
	 * cached access is a hit, so the KSEG0 leg measures RESIDENCY rather
	 * than miss latency.  It is the only instrument in this payload that
	 * observes residency WITHOUT going through the alias, which makes it the
	 * only route that could split `c-A`'s remaining two-way disjunction. */
	{
		u32 raw = (u32)&tc_raw[0] | (u32)KSEG1_BIT;

		(void)rlx_tc_walk(A_VSIZE, 1u, (u32 *)raw);
		res_put(R_T_HIT_WARM,
			tc_ticks(rd_unc((u32)&tc_raw[0]),
				 rd_unc((u32)&tc_raw[1])));
		(void)rlx_tc_walk(A_VSIZE, 32u, (u32 *)raw);
		res_put(R_T_HIT_KS0,
			tc_ticks(rd_unc((u32)&tc_raw[0]),
				 rd_unc((u32)&tc_raw[1])));
		(void)rlx_tc_walk(A_VSIZE | (u32)KSEG1_BIT, 32u, (u32 *)raw);
		res_put(R_T_HIT_KS1,
			tc_ticks(rd_unc((u32)&tc_raw[0]),
				 rd_unc((u32)&tc_raw[1])));
	}
	field("t.live", rb_get(O_RES + R_T_LIVE_A));
	field("t.live2", rb_get(O_RES + R_T_LIVE_B));
	field("t.sep.a", rb_get(O_RES + R_T_LIVE_C));
	field("t.sep.b", rb_get(O_RES + R_T_LIVE_D));
	field("t.tccnr", rb_get(O_RES + R_T_TCCNR));
	field("t.cal.hi", rb_get(O_RES + R_T_CAL_HI));
	field("t.cal.lo", rb_get(O_RES + R_T_CAL_LO));
	field("t.ovh.1", rb_get(O_RES + R_T_OVH1));
	field("t.ovh.4k", rb_get(O_RES + R_T_OVH4K));
	field("t.hit.warm", rb_get(O_RES + R_T_HIT_WARM));
	field("t.hit.ks0", rb_get(O_RES + R_T_HIT_KS0));
	field("t.hit.ks1", rb_get(O_RES + R_T_HIT_KS1));

	/* 否證 T, EVALUATED BY THE PAYLOAD RATHER THAN LEFT TO THE DESK.
	 *
	 * ⚠️ The refutation is written against the SEPARATED pair, not the
	 * back-to-back one.  One tick is 69.9983 ns; back to back the two reads
	 * may be closer than the LSB, and *equal* would then be the reading of a
	 * perfectly live counter.  `t-ovh` is what says which of those it is.
	 *
	 * 🔴 AND `0xFFFFFFFF` IS ITS OWN STATE.  量(qemu) this run: Malta has no
	 * timer at 0xB8003108 and an unmapped uncached read there returns all
	 * ones, twice, with the destination demonstrably written -- the value is
	 * not either prime.  *Nothing is there* and *the register is frozen* are
	 * different claims about a machine, and one of them is true of qemu and
	 * neither is expected of the device (REG-07, REG-09, CLK-04). */
	{
		u32 a = rb_get(O_RES + R_T_LIVE_C);
		u32 b = rb_get(O_RES + R_T_LIVE_D);

		if (a == 0xFFFFFFFFu && b == 0xFFFFFFFFu) {
			g_timer = 0u;
			rlx_puts("rlxprobe: Group T VOID -- TC0CNT reads all "
				 "ones twice: there is no timer at that "
				 "address on this machine\r\n");
		} else if (tc_prime_bad(a) || tc_prime_bad(b)) {
			g_timer = 0u;
			rlx_puts("rlxprobe: Group T VOID -- the uncached load "
				 "did not write its destination\r\n");
		} else if (a == b) {
			g_timer = 0u;
			rlx_puts("rlxprobe: Group T VOID -- TC0CNT is frozen "
				 "across a calibrated loop, so it is not a "
				 "live mirror of the counter\r\n");
		} else {
			g_timer = 1u;
		}
		rb_put(H_G_TIMER, g_timer);
		rb_put(H_T_SEP_A, a);
		rb_put(H_T_SEP_B, b);
		field("g.timer", g_timer);
	}
	progress(P_TIMER);

	/* --- 3. Group W -- the I-side walk ------------------------------- */
	/* Nothing here is new: uncached stores, cached fetches, `CCTL 0x002`.
	 * EVERY INSTRUCTION IN THIS STAGE HAS ALREADY EXECUTED ON THIS SILICON. */

	/* w-line0 FIRST: it is the negative control, and if it fails `w-line`
	 * was never worth running. */
	bmp_clear();
	nf = w_point_nofetch(A_PAT_LINE0, L_LINE[0], L_LINE);
	res_put(R_W_LINE0 + 0u, bmp_pack(0u, 8u));
	res_put(R_W_LINE0 + 1u, bmp_pack(8u, L_LINE[0] - 8u));
	res_put(R_W_LINE0 + 2u, wctl_get(5u));
	field("w.line0.fresh", nf);
	field("w.line0.bits", rb_get(O_RES + R_W_LINE0));

	bmp_clear();
	nf = w_point(A_PAT_LINE, 0u, L_LINE[0], 1u, L_LINE, 1u);
	res_put(R_W_LINE + 0u, bmp_pack(0u, 8u));
	res_put(R_W_LINE + 1u, bmp_pack(8u, L_LINE[0] - 8u));
	res_put(R_W_LINE + 2u, wctl_get(5u));
	field("w.line.fresh", nf);
	field("w.line.bits", rb_get(O_RES + R_W_LINE));
	field("w.line.bits2", rb_get(O_RES + R_W_LINE + 1u));
	/* V0 is the must-fire.  It was demonstrably fetched, so at any line size
	 * >= 4 B it MUST read STALE; if it does not, the block is void and *all
	 * FRESH* is indistinguishable from an 8-byte line, a patch that missed,
	 * and a dead re-arm. */
	row_victim(0x574C0000u, A_PAT_LINE + L_LINE[1], bmp_nib(0u));
	for (i = 1; i < L_LINE[0]; i++)
		if (bmp_nib(i) == V_FRESH) {
			row_victim(0x574C0001u | (i << 8),
				   A_PAT_LINE + L_LINE[1u + i], bmp_nib(i));
			break;
		}

	bmp_clear();
	nf = w_point(A_PAT_BACK, 0u, L_BACK[0], 1u, L_BACK, 1u);
	res_put(R_W_BACK + 0u, bmp_pack(0u, 8u));
	res_put(R_W_BACK + 1u, bmp_pack(8u, L_BACK[0] - 8u));
	res_put(R_W_BACK + 2u, wctl_get(5u));
	field("w.back.bits", rb_get(O_RES + R_W_BACK));
	field("w.back.bits2", rb_get(O_RES + R_W_BACK + 1u));
	/* STALE extending BACKWARDS is the signature of a line fill;
	 * forward-only is prefetch, and this is the only cell that separates
	 * them.  ⚠️ It alone cannot separate L = 32 from L = 16 plus one
	 * next-line prefetch -- `w-back2` is what does. */
	row_victim(0x57424000u, A_PAT_BACK + 128u, bmp_nib(6u));

	bmp_clear();
	nf = w_point(A_PAT_BACK2, 0u, L_BACK2[0], 1u, L_BACK2, 1u);
	res_put(R_W_BACK2 + 0u, bmp_pack(0u, 8u));
	res_put(R_W_BACK2 + 1u, bmp_pack(8u, L_BACK2[0] - 8u));
	res_put(R_W_BACK2 + 2u, wctl_get(5u));
	field("w.back2.bits", rb_get(O_RES + R_W_BACK2));
	field("w.back2.bits2", rb_get(O_RES + R_W_BACK2 + 1u));
	row_victim(0x57423200u, A_PAT_BACK2 + 128u, bmp_nib(1u));

	/* w-size.  ASCENDING IN W, so a FRESH victim at a large point cannot
	 * contaminate a smaller one. */
	boundary = 0xFFFFFFFFu;
	for (i = 0; i < W_POINTS; i++) {
		u32 count = (W_KIB[i] * 1024u) / W_STRIDE;

		nf = w_point(A_WSIZE, W_STRIDE, count, 0u, (const u32 *)0, 0u);
		no = wctl_get(5u);
		res_put(R_W_SIZE + i * 2u + 0u, nf);
		res_put(R_W_SIZE + i * 2u + 1u, no);
		rlx_puts("rlxprobe: w.size ");
		rlx_puthex32(W_KIB[i]);
		pair("n", count);
		pair("fresh", nf);
		pair("other", no);
		rlx_puts("\r\n");
		if (nf != 0u && boundary == 0xFFFFFFFFu)
			boundary = i;
	}
	res_put(R_W_ARMFRESH, arm_fresh_i);
	field("w.arm.fresh", arm_fresh_i);

	/* THE RETAINED BITMAP.  One sweep point survives to the read-back and it
	 * is a decision: the BOUNDARY point, because its PATTERN is what carries
	 * associativity and aliasing, and the largest point otherwise.  It is a
	 * SECOND RUN of that point -- the sweep above ran with no bitmap -- and
	 * both runs' counts are in the block, so a disagreement between them is
	 * itself visible rather than silently resolved. */
	{
		u32 pt = (boundary != 0xFFFFFFFFu) ? boundary : (W_POINTS - 1u);

		bnd_count = (W_KIB[pt] * 1024u) / W_STRIDE;
		if (bnd_count > RB_BMPW * 8u)
			bnd_count = RB_BMPW * 8u;
		bmp_clear();
		nf = w_point(A_WSIZE, W_STRIDE, bnd_count, 1u,
			     (const u32 *)0, 0u);
		rb_put(H_BMP_POINT, 0x57000000u | W_KIB[pt]);
		rb_put(H_BMP_COUNT, bnd_count);
		field("bmp.point", 0x57000000u | W_KIB[pt]);
		field("bmp.count", bnd_count);
		field("bmp.rerun.fresh", nf);
		first_bad = bmp_first_bad(bnd_count);
		field("bmp.firstbad", first_bad);

		/* 否證 ⓐ and its positive control, as the payload checks them:
		 * every victim STALE at the smallest working set, MOST victims
		 * FRESH at the largest.  Rows for both, whatever they say. */
		row_victim(0x57530001u, A_WSIZE, bmp_nib(0u));
		if (boundary != 0xFFFFFFFFu)
			for (k = 0; k < bnd_count; k++)
				if (bmp_nib(k) == V_FRESH) {
					row_victim(0x57530002u | (k << 8),
						   A_WSIZE + k * W_STRIDE,
						   bmp_nib(k));
					break;
				}
	}

	/* w-assoc.  PARAMETERS CHOSEN AT RUN TIME from w-size's answer, and the
	 * two controls are free: M = 1 at every T MUST read all-STALE (one
	 * victim cannot self-evict), and the largest M at the smallest T MUST
	 * show FRESH.  Neither firing means (T, M) is a number with nothing
	 * behind it.
	 *
	 * ⚠️ THE CAP IS REPORTED.  With T = C and C large, twelve victims do not
	 * fit in the 256 KiB the assoc arena has; the payload records how many M
	 * it could reach, because a silent truncation reads as coverage. */
	c_size = (boundary != 0xFFFFFFFFu) ? (W_KIB[boundary] * 1024u) : 0u;
	res_put(R_W_ASSOC + 0u, c_size);
	if (c_size >= 1024u) {
		u32 best_t = 0u, best_m = 0u;

		cap = 0u;
		for (j = 0; j < 4u; j++) {
			t = c_size >> (3u - j);		/* C/8, C/4, C/2, C */
			if (t < 64u)
				continue;
			for (m = 1u; m <= 12u; m++) {
				if (m * t > A_ASSOC_SPAN) {
					cap++;
					break;
				}
				bmp_clear();
				nf = w_point(A_ASSOC, t, m, 0u,
					     (const u32 *)0, 0u);
				if (m == 1u && nf != 0u) {
					/* one victim cannot self-evict */
					best_t = 0u;
					best_m = 0xFFu;
					j = 4u;
					break;
				}
				if (nf != 0u) {
					if (best_t == 0u || m < best_m) {
						best_t = t;
						best_m = m;
					}
					break;
				}
			}
		}
		res_put(R_W_ASSOC + 1u, (best_t & 0xFFFFFF00u) | (best_m & 0xFFu));
		res_put(R_W_ASSOC + 2u, cap);
		field("w.assoc.tm", rb_get(O_RES + R_W_ASSOC + 1u));
		field("w.assoc.capped", cap);
		rb_row(0x57415353u, best_t, best_m,
		       (best_m > 1u && best_m != 0xFFu) ? (best_m - 1u) : 0u,
		       c_size, cap, 0u, (best_m == 0xFFu) ? 0xBADu : 0u);
	} else {
		res_put(R_W_ASSOC + 1u, 0u);
		res_put(R_W_ASSOC + 2u, 0xFFFFFFFFu);
		rlx_puts("rlxprobe: w.assoc NOT RUN -- w-size is void\r\n");
		cells_void++;
	}
	progress(P_WALK_I);

	/* --- 4. w-imem --------------------------------------------------- */
	/* 🔴 THE FIRST `CCTL` COMMAND THIS PROJECT HAS WRITTEN THAT ITS OWN
	 * LOADER DOES NOT ISSUE AFTER RESET.  `0x020` is `IMEM0OFF`, named by
	 * four sources, two of which are independent: the Lexra LX4189 datasheet
	 * § 5.2 and `arch/rlx/include/asm/rlxregs.h:632-633`.  It clears one
	 * valid bit; the payload ends in `rlx_reset` and the loader re-runs its
	 * whole reset sequence, so the restore is the reboot.  `0x010`
	 * (`IMEM0FILL`) stays out: it stalls the core through a full 16 KiB
	 * line-read burst from a BASE/TOP pair this payload did not program.
	 *
	 * ⚠️ CP0 20 IS WRITE-ONLY AND READS ZERO (M4, `CPU-39`), so NO CELL IN
	 * THIS PAYLOAD CAN CONFIRM A `CCTL` COMMAND WAS ACCEPTED.  *Identical to
	 * w-size* is also the no-op reading.  It is a pass only where `m-imem`
	 * returned a window and the arena is provably outside it, and the
	 * write-up says 未定 everywhere else. */
	rlx_call2_uncached((u32)rlx_cctl, (u32)CCTL_IMEM0OFF, 0u);
	for (i = 0; i < W_POINTS; i++) {
		u32 count = (W_KIB[i] * 1024u) / W_STRIDE;

		nf = w_point(A_WSIZE, W_STRIDE, count, 0u, (const u32 *)0, 0u);
		no = wctl_get(5u);
		res_put(R_W_IMEM + i * 2u + 0u, nf);
		res_put(R_W_IMEM + i * 2u + 1u, no);
		if (nf != rb_get(O_RES + R_W_SIZE + i * 2u))
			w_imem_differs++;
		rlx_puts("rlxprobe: w.imem ");
		rlx_puthex32(W_KIB[i]);
		pair("fresh", nf);
		pair("other", no);
		rlx_puts("\r\n");
	}
	field("w.imem.differs", w_imem_differs);
	/* 🔴 *IDENTICAL* IS ALSO THE NO-OP READING, and the payload says so
	 * rather than letting a pass be inferred.  CP0 20 is write-only and
	 * reads zero (M4, CPU-39), so nothing here can confirm the `CCTL 0x020`
	 * was decoded at all: *the arena was never in the IMEM window* and *the
	 * command did nothing* give the same numbers.  It is a pass only where
	 * `m-imem` returned a window and the arena is provably outside it. */
	if (w_imem_differs == 0u)
		rlx_puts("rlxprobe: w-imem IDENTICAL -- and that is also the "
			 "no-op reading. UNDETERMINED unless m-imem returned "
			 "a window.\r\n");
	else
		rlx_puts("rlxprobe: w-imem DIFFERS -- the unqualified walk was "
			 "measuring the scratchpad. That is a result, not a "
			 "failure.\r\n");
	progress(P_IMEM_OFF);

	/* --- 5. Group M -- where the scratchpads are --------------------- */
	/* A TRAP HERE IS AN EXPECTED OUTCOME, NOT A FAILURE.  There is no
	 * prediction for the device and that IS the finding: the loader contains
	 * ZERO COP3 instructions, so at the prompt IMEMBASE/IMEMTOP hold
	 * whatever reset left, and nothing in any source says what that is.  The
	 * kernel's values are NOT a prediction for this cell -- they are what a
	 * different codebase chose after the loader had already handed over. */
	if (g_hbrk) {
		u32 s0, s1;

		s0 = rlx_status_or((u32)ST0_CU3);
		s1 = rlx_mfc0_status();
		res_put(R_M_CU3_BEFORE, s0);
		res_put(R_M_CU3_SET, s1);
		rlx_status_write(s0);
		res_put(R_M_CU3_REST, rlx_mfc0_status());
		field("m.cu3.before", s0);
		field("m.cu3.set", s1);

		/* SET CU3 AGAIN AND HOLD IT ACROSS THE WHOLE CELL.  `mfc3` with
		 * CU3 clear traps BY CONSTRUCTION, and that would be recorded as
		 * *CP3 unreachable* when it was an artefact of the running
		 * order. */
		s0 = rlx_status_or((u32)ST0_CU3);
		res_put(R_M_STATUS, rlx_mfc0_status());
		for (i = 0; i < 8u; i++) {
			u32 stub = (u32)rlx_cp3_stubs + i * 12u;
			u32 b, v1, v2;

			b = exc_rec(0u);
			v1 = rlx_call0_primed(stub, 0xC0DE0300u | i);
			if (exc_rec(0u) != b) {
				m_traps |= (1u << i);
				res_put(R_M_CAUSE, exc_rec(1u));
			}
			b = exc_rec(0u);
			v2 = rlx_call0_primed(stub, 0xD1CE0300u | i);
			if (exc_rec(0u) != b) {
				m_traps |= (1u << i);
				res_put(R_M_CAUSE, exc_rec(1u));
			}
			res_put(R_M_CP3 + i * 2u + 0u, v1);
			res_put(R_M_CP3 + i * 2u + 1u, v2);
			rlx_puts("rlxprobe: m.cp3 ");
			rlx_puthex32(i);
			pair("v1", v1);
			pair("v2", v2);
			pair("trap", (m_traps >> i) & 1u);
			rlx_puts("\r\n");
			/* THE TWO-PRIME READ IS probe2's RULE, NOT CAUTION.
			 * F50b spent a seating on *reads zero* being
			 * indistinguishable from *the destination was never
			 * written*, and priming is what separated them. */
			if (!((m_traps >> i) & 1u) &&
			    v1 != (0xC0DE0300u | i) && v2 != (0xD1CE0300u | i) &&
			    v1 == v2) {
				if (i == 0u)
					imem_base = v1;
				else if (i == 1u)
					imem_top = v1;
				else if (i == 4u)
					dmem_base = v1;
				else if (i == 5u)
					dmem_top = v1;
			}
		}
		res_put(R_M_TRAPS, m_traps);
		rlx_status_write(s0);
		field("m.traps", m_traps);
		field("m.cause", rb_get(O_RES + R_M_CAUSE));
		field("m.imembase", imem_base);
		field("m.imemtop", imem_top);
		field("m.dmembase", dmem_base);
		field("m.dmemtop", dmem_top);
		/* 🔴 *CP3 UNREACHABLE* AND *CU3 IS NOT SETTABLE* ARE DIFFERENT
		 * CLAIMS, and the Status read-back beside the results is what
		 * separates them at the desk.  量(qemu) this run: `m.cu3.set`
		 * came back with bit 31 CLEAR and all eight stubs trapped, so on
		 * that machine the two are confounded and the qemu leg cannot
		 * decide either.  What it DOES buy is real: sixteen non-`Bp`
		 * exceptions delivered to this handler and returned from, before
		 * the device ever sees one. */
		if (m_traps != 0u &&
		    (rb_get(O_RES + R_M_CU3_SET) & (u32)ST0_CU3) == 0u)
			rlx_puts("rlxprobe: m-imem trapped with CU3 NOT set -- "
				 "*CP3 unreachable* is not separable from "
				 "*CU3 is not implemented as a bit* here\r\n");
		cells_run += 2u;
	} else {
		res_put(R_M_TRAPS, 0xFFFFFFFFu);
		rlx_puts("rlxprobe: Group M NOT RUN -- h-brk did not gate\r\n");
		cells_void += 2u;
	}
	res_put(R_V_DMEM_BASE, dmem_base);
	res_put(R_V_DMEM_TOP, dmem_top);
	progress(P_SCRATCH);

	/* --- 6. Group C -- coherence ------------------------------------- */
	/* `c-A0` runs FIRST because it is the negative control: if it fails,
	 * `c-A` was never worth running and the seating learns that in two loads
	 * instead of after a whole group. */
	{
		u32 xa = A_COH, xb = A_COH + COH_SEP1;
		u32 xc = A_COH + 0x4000u, xd = A_COH + 0x4000u + COH_SEP2;
		u32 va;

		c_cell(C_A0, "A0", K_SEQ, xa, xb, 0u, 0u, 0u, 0u, 0u);
		if ((rb_get(O_RES + R_C + C_A0 * R_C_STRIDE + 4u) & 0xFFu)
		    != CV_P1) {
			/* `c-A0` returning P0 means something else is stale and
			 * EVERY CELL IN THIS GROUP IS VOID. */
			rlx_puts("rlxprobe: c-A0 did not read P1 -- Group C and "
				 "Group V are VOID\r\n");
			g_ca = 0u;
			for (i = C_A; i < C_CELLS; i++)
				c_void(i, "gated", CV_VOID_GATE);
		} else {
			c_cell(C_A, "A", K_SEQ, xa, xb, 0u, 0u, 1u, 0u, 0u);
			c_cell(C_A2, "A2", K_SEQ, xc, xd, 0u, 0u, 1u, 0u, 0u);
			va = rb_get(O_RES + R_C + C_A * R_C_STRIDE + 4u) & 0xFFu;
			g_ca = (va == CV_P0);

			/* ⓓ①.  EACH OF THE THREE E CELLS RUNS ITS OWN WHOLE
			 * SEQUENCE.  LX4189 § 5.2 says `c-E`'s final uncached
			 * read invalidates the line, so a `c-E2` that continued
			 * from `c-E`'s state would find no dirty line left and
			 * record *0x100 does not write back* -- a refutation of
			 * the command produced by the running order.
			 *
			 * `c-E0` is the write-buffer control and it runs BEFORE
			 * `c-E2`: after a `DWB` and a second load the buffer has
			 * drained under both hypotheses, so `c-E2` alone is a
			 * cell that cannot fail.  Its drain is 64 uncached reads
			 * of `TC0CNT`, an address this payload already reads and
			 * whose line is nowhere near the target. */
			c_cell(C_E, "E", K_E, xa, xb, 0u, 0u, 1u, 0u, 0u);
			c_cell(C_E0, "E0", K_E, xa, xb, 0u, 0u, 1u,
			       (u32)RLX_TC0CNT | (u32)KSEG1_BIT, 64u);
			c_cell(C_E2, "E2", K_E, xa, xb, (u32)CCTL_DWB, 0u, 1u,
			       0u, 0u);

			if (g_ca) {
				c_cell(C_F, "F", K_SEQ, xa, xb,
				       (u32)CCTL_DWB, 0u, 1u, 0u, 0u);
				g_cf = ((rb_get(O_RES + R_C + C_F *
						R_C_STRIDE + 4u) & 0xFFu)
					== CV_P0);
				c_cell(C_B, "B", K_SEQ, xa, xb,
				       (u32)CCTL_DWBINVAL, 0u, 1u, 0u, 0u);
				/* 🔴 `CCTL 0x001` INVALIDATES THE WHOLE D-CACHE
				 * WITHOUT WRITING BACK, INCLUDING THIS
				 * PAYLOAD'S OWN SPILLED `$31`.  It runs only
				 * behind a `DWB` in the same leaf, and only if
				 * `c-F` measured that the `DWB` writes back.
				 * ⚠️ `c-F` IS NOT THAT MITIGATION: `c-B` runs
				 * between them, so every frame pushed after
				 * `c-F` is dirty again by the time `c-C` fires.
				 * The mitigation is the two `mtc0`s inside one
				 * leaf, which is what cmd1 + cmd2 means here. */
				if (g_cf)
					c_cell(C_C, "C", K_SEQ, xa, xb,
					       (u32)CCTL_DWB,
					       (u32)CCTL_DINVAL, 1u, 0u, 0u);
				else
					c_void(C_C, "C", CV_VOID_GATE);
				c_cell(C_G, "G", K_G, xa, xb, 0u, 0u, 1u,
				       0u, 0u);
			} else {
				/* 🔴 WITH NO STALE LINE TO INVALIDATE, EVERY
				 * TREATMENT RETURNS THE SECOND VALUE WHETHER IT
				 * WORKS OR NOT.  These are void, not passes. */
				c_void(C_F, "F", CV_VOID_NOSTALE);
				c_void(C_B, "B", CV_VOID_NOSTALE);
				c_void(C_C, "C", CV_VOID_NOSTALE);
				c_void(C_G, "G", CV_VOID_NOSTALE);
			}
		}
		rb_put(H_G_CA, g_ca);
		rb_put(H_G_CF, g_cf);
		field("g.ca", g_ca);
		field("g.cf", g_cf);
	}
	progress(P_COHERE);

	/* --- 7. Group V -- the D-side walk, ARMED BY c-A ----------------- */
	/* Its observation channel -- *an uncached write is invisible to a
	 * resident clean line* -- IS `c-A`'s positive reading.  If `c-A` is
	 * negative, every V cell returns FRESH at every size, which is
	 * indistinguishable from *there is no D-cache*. */
	v_arena = A_VSIZE;
	if (dmem_base != 0u && dmem_top != 0u &&
	    !((v_arena + 0x10000u) < dmem_base || v_arena > dmem_top)) {
		v_arena = A_ASSOC;	/* placement, not a treatment */
		arena_moved = 1u;
	}
	rb_put(H_ARENA_MOVED, arena_moved);
	res_put(R_V_ARENA, v_arena);
	v_stride = V_STRIDE_DEFAULT;

	if (g_ca) {
		bmp_clear();
		nf = v_point(v_arena, 0u, L_VLINE[0], 1u, L_VLINE);
		res_put(R_V_LINE + 0u, bmp_pack(0u, 8u));
		res_put(R_V_LINE + 1u, bmp_pack(8u, L_VLINE[0] - 8u));
		res_put(R_V_LINE + 2u, wctl_get(5u));
		field("v.line.bits", rb_get(O_RES + R_V_LINE));
		field("v.line.bits2", rb_get(O_RES + R_V_LINE + 1u));
		/* `+0` was demonstrably loaded, so it MUST read STALE -- the
		 * must-fire, licensed by `c-A` having been positive. */
		row_target(0x564C0000u, v_arena, bmp_nib(0u));

		/* ONE TARGET PER LINE, AND THE LINE IS RE-DERIVED FROM
		 * `v-line`'s MEASURED value rather than from the prediction. */
		{
			u32 run = 0u;

			for (i = 1u; i < L_VLINE[0]; i++) {
				if (bmp_nib(i) != V_STALE)
					break;
				run = L_VLINE[1u + i];
			}
			if (run >= 4u && run <= 128u) {
				v_stride = 4u;
				while (v_stride <= run)
					v_stride <<= 1;
			}
		}
		field("v.stride", v_stride);

		boundary = 0xFFFFFFFFu;
		for (i = 0; i < V_POINTS; i++) {
			u32 count = (V_KIB[i] * 1024u) / v_stride;

			nf = v_point(v_arena, v_stride, count, 0u,
				     (const u32 *)0);
			no = wctl_get(5u);
			res_put(R_V_SIZE + i * 2u + 0u, nf);
			res_put(R_V_SIZE + i * 2u + 1u, no);
			rlx_puts("rlxprobe: v.size ");
			rlx_puthex32(V_KIB[i]);
			pair("n", count);
			pair("fresh", nf);
			pair("other", no);
			rlx_puts("\r\n");
			if (nf != 0u && boundary == 0xFFFFFFFFu)
				boundary = i;
		}
		res_put(R_V_ARMFRESH, arm_fresh_d);
		field("v.arm.fresh", arm_fresh_d);

		c_size = (boundary != 0xFFFFFFFFu) ?
			 (V_KIB[boundary] * 1024u) : 0u;
		res_put(R_V_ASSOC + 0u, c_size);
		if (c_size >= 1024u) {
			u32 best_t = 0u, best_m = 0u;

			cap = 0u;
			for (j = 0; j < 4u; j++) {
				t = c_size >> (3u - j);
				if (t < 16u)
					continue;
				for (m = 1u; m <= 12u; m++) {
					if (m * t > A_ASSOC_SPAN) {
						cap++;
						break;
					}
					nf = v_point(A_ASSOC, t, m, 0u,
						     (const u32 *)0);
					if (m == 1u && nf != 0u) {
						best_t = 0u;
						best_m = 0xFFu;
						j = 4u;
						break;
					}
					if (nf != 0u) {
						if (best_t == 0u || m < best_m) {
							best_t = t;
							best_m = m;
						}
						break;
					}
				}
			}
			res_put(R_V_ASSOC + 1u,
				(best_t & 0xFFFFFF00u) | (best_m & 0xFFu));
			res_put(R_V_ASSOC + 2u, cap);
			field("v.assoc.tm", rb_get(O_RES + R_V_ASSOC + 1u));
		} else {
			res_put(R_V_ASSOC + 1u, 0u);
			res_put(R_V_ASSOC + 2u, 0xFFFFFFFFu);
		}
		cells_run += 3u;
	} else {
		for (i = 0; i < V_POINTS; i++) {
			res_put(R_V_SIZE + i * 2u + 0u, 0xFFFFFFFFu);
			res_put(R_V_SIZE + i * 2u + 1u, 0xFFFFFFFFu);
		}
		res_put(R_V_LINE + 2u, 0xFFFFFFFFu);
		rlx_puts("rlxprobe: Group V VOID -- c-A negative, so every V "
			 "cell would read FRESH at every size and that is "
			 "indistinguishable from having no D-cache\r\n");
		cells_void += 3u;
	}
	progress(P_WALK_D);

	/* --- 8. Group X -- the first `cache` instruction ----------------- */
	x_scratch = A_XSCRATCH;
	wr_unc(x_scratch - 4u, 0x33330001u);
	wr_unc(x_scratch, 0x33330002u);
	wr_unc(x_scratch + 4u, 0x33330003u);

	if (g_hbrk) {
		u32 r;

		/* `x-ri` first: 留白 on the device, and the honesty is the
		 * point.  No Lexra ISA document exists in this repository, so no
		 * encoding can be SHOWN reserved on this core.  It retiring is a
		 * finding, and `h-brk` alone already licenses `x-11` because the
		 * handler branches on nothing (M3'). */
		(void)x_cell(X_RI, "ri", (void (*)(u32))0, 0u);

		r = x_cell(X_11, "c11", rlx_x_cache11, x_scratch);
		g_x11 = (r == 0u);
		rb_put(H_G_X11, g_x11);

		r = x_cell(X_10, "c10", rlx_x_cache10, x_scratch);
		/* `x-10`'s FUNCTIONAL LEG, and it re-establishes its own
		 * baseline here.  Without the untreated twin, *the victim went
		 * FRESH* names six intervening stages of `CCTL` as readily as it
		 * names `cache 0x10`. */
		if (r == 0u) {
			u32 base = A_PAT_LINE0 + 0x400u;

			wctl_set(base, 64u, 2u, 0u);
			rlx_call2_uncached((u32)rlx_w_arm, WCTL_KS1, 0u);
			flush_i();
			wctl_set(base, 64u, 2u, 0u);
			(void)rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1, 0u);
			wctl_set(base, 64u, 2u, 0u);
			rlx_call2_uncached((u32)rlx_w_patch, WCTL_KS1, 0u);
			rlx_x_cache10(base);		/* ONE of the two */
			bmp_clear();
			wctl_set(base, 64u, 2u, 1u);
			(void)rlx_call2_uncached((u32)rlx_w_exec, WCTL_KS1, 0u);
			res_put(R_X_FUNC + 0u, bmp_nib(0u));
			res_put(R_X_FUNC + 1u, bmp_nib(1u));
			field("x.c10.treated", bmp_nib(0u));
			field("x.c10.twin", bmp_nib(1u));
			row_victim(0x58313000u, base, bmp_nib(0u));
			/* 🔴 THE UNTREATED TWIN MUST STILL READ STALE. */
		} else {
			res_put(R_X_FUNC + 0u, 0xFFFFFFFFu);
			res_put(R_X_FUNC + 1u, 0xFFFFFFFFu);
		}

		/* `c-D` -- conditional on `x-11` retiring.  ⚠️ Gating on `x-11`
		 * answers ⓒ for ONE op and reports it for a family: qemu does
		 * not decode the op field at all, so *uniform decoding* is
		 * precisely the assumption not to make. */
		if (g_x11 && g_ca)
			c_cell(C_D, "D", K_D, A_COH, A_COH + COH_SEP1,
			       0u, 0u, 1u, 0u, 0u);
		else
			c_void(C_D, "D", g_x11 ? CV_VOID_NOSTALE
					       : CV_VOID_GATE);

		if (g_x11) {
			(void)x_cell(X_15, "c15", rlx_x_cache15, x_scratch);
			(void)x_cell(X_19, "c19", rlx_x_cache19, x_scratch);
		} else {
			res_put(R_X + X_15 * R_X_STRIDE, 0xFFFFFFFFu);
			res_put(R_X + X_19 * R_X_STRIDE, 0xFFFFFFFFu);
			cells_void += 2u;
		}
	} else {
		for (i = 0; i < X_CELLS; i++)
			res_put(R_X + i * R_X_STRIDE, 0xFFFFFFFFu);
		c_void(C_D, "D", CV_VOID_GATE);
		cells_void += X_CELLS;
	}
	res_put(R_X_SCRATCH + 0u, rd_unc(x_scratch - 4u));
	res_put(R_X_SCRATCH + 1u, rd_unc(x_scratch));
	res_put(R_X_SCRATCH + 2u, rd_unc(x_scratch + 4u));
	progress(P_CACHEOP);

	/* --- 9. Group S -- is Status.IsC implemented as a bit ------------ */
	/* LAST, because it has the least source support of anything here and it
	 * writes a `Status` bit this core is already MEASURED to mishandle:
	 * probe1 cell 4 read `07` CORRUPT on both victims, and the stores issued
	 * while `IsC` was set reached DRAM.  `rlx_status_poke` therefore has NO
	 * MEMORY REFERENCE between the set and the clear.
	 *
	 * 🔴 THE CONTROL BITS ARE 6 AND 24 AND THEY ARE WHAT MAKE THIS A CELL.
	 * Without them, *bit 16 stuck* and *Status has no write mask* are one
	 * reading.  LX4189 § 3.4.1's STATUS figure shows 27-23, 21-16 and 7-6 as
	 * `0` fields and says *"The 0 fields are ignored on write and are 0 on
	 * read"* -- which puts both control bits AND bit 16 itself inside a
	 * `0` field, so the LX4189 PREDICTS bit 16 clear.  TWO control bits
	 * rather than one, at opposite ends of the register, because one cannot
	 * see a PARTIAL write mask. */
	{
		u32 poke = (u32)&poke_out[0] | (u32)KSEG1_BIT;
		u32 sb, ss, sr, vd;

		(void)rlx_status_poke((u32)ST0_ISC | (u32)ST0_CTRL_A |
				      (u32)ST0_CTRL_B, (u32 *)poke);
		sb = rd_unc((u32)&poke_out[0]);
		ss = rd_unc((u32)&poke_out[1]);
		sr = rd_unc((u32)&poke_out[2]);
		res_put(R_S_BEFORE, sb);
		res_put(R_S_SET, ss);
		res_put(R_S_REST, sr);

		vd = ((ss & (u32)ST0_ISC) ? 1u : 0u)
		   | ((ss & (u32)ST0_CTRL_A) ? 2u : 0u)
		   | ((ss & (u32)ST0_CTRL_B) ? 4u : 0u)
		   | ((sr == sb) ? 0u : 0x100u);
		res_put(R_S_VERDICT, vd);
		field("s.before", sb);
		field("s.set", ss);
		field("s.restored", sr);
		field("s.vd", vd);
		if (sr != sb)
			rlx_puts("rlxprobe: s-isc did NOT restore Status -- "
				 "everything after it is suspect\r\n");
		cells_run++;
	}
	progress(P_ISC);

	/* --- 10. restore, seal, hand the board back ---------------------- */
	copy_vec_back();

	sum = 0u;
	for (i = 0; i < VEC_WORDS; i++) {
		if (rd_unc(VEC_UTLB + i * 4u) != saved_vec[i])
			sum++;
		if (rd_unc(VEC_GENERAL + i * 4u) != saved_vec[i + VEC_WORDS])
			sum++;
	}
	rb_put(H_RES_MISMATCH, sum);
	field("restore.mismatch", sum);

	/* `restore.stillhandler` is the leg a check whose failure mode is *the
	 * value is unchanged* needs: of the words the install actually CHANGED,
	 * how many still equal OUR handler.  The `saved != entry` guard is not
	 * tidiness -- ten of this handler's words are `nop`, and under qemu the
	 * vector page starts as zeros, so counting every position where the
	 * restored word equals a handler word returned 20 on a perfect restore. */
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

	status = rlx_mfc0_status();
	rb_put(H_STATUS_END, status);
	field("status_end", status);
	rb_put(H_CELLS_RUN, cells_run);
	rb_put(H_CELLS_VOID, cells_void);
	rb_put(H_UART_ROWS, rows_used);
	field("cells.run", cells_run);
	field("cells.void", cells_void);

	/* THE SEAL COVERS THE BLOCK AS IT WAS BEFORE P_SEALED WAS STAMPED, and
	 * anyone re-summing it afterwards has to know that.  The sum runs over
	 * words 0 .. O_SEAL-1, which INCLUDES H_PROGRESS at word 2, and
	 * `progress(P_SEALED)` then writes word 2 again -- so a straight re-sum
	 * of the recovered block is high by exactly P_SEALED - P_RESTORED = 0x10
	 * on every complete run.  量 on probe2, `bench/2026-08-25b/H2g.log`:
	 * naive re-sum 0xEC84409D against a stored 0xEC84408D.
	 *
	 * NOT REORDERED.  Sealing first and stamping progress afterwards is what
	 * makes `progress` monotone all the way to the end; a block whose seal is
	 * written but whose progress says P_RESTORED is a run that died between
	 * the two, and that is a state worth being able to see.  `H_SEAL_KIND`
	 * is 1 so the desk does not have to know this from a comment. */
	sum = 0u;
	for (i = 0; i < O_SEAL; i++)
		sum += rb_get(i);
	rb_put(O_SEAL, sum);
	progress(P_SEALED);
	field("sum", sum);
	field("rb.words", RB_WORDS);

	rlx_puts("rlxprobe: end\r\n");
}
