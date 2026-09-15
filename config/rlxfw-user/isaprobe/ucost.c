/* ucost.c -- `R1-pub-4b`'s instrument (`D-cost`), and the second compiled
 * userspace program in this project.
 *
 * DRAFT, segment 75.  Nothing here has been compiled, and nothing here has
 * run.  Every number in the comments is marked.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT IS, AND WHAT `4a` LEFT FOR IT
 * ---------------------------------------------------------------------------
 *
 * `R1-pub-4a` established the emulation SURFACE: which instructions this
 * kernel traps and emulates instead of executing.  Its instrument reads *did a
 * signal arrive*, and `docs/emulation-surface.md` § 4 states its own blind
 * spot in its own words:
 *
 *     "`ll` and `sc` are emulated in user mode and the test **cannot see
 *      it**: they already retire on the die, so both columns read *no signal*
 *      and the difference is invisible to the instrument."
 *
 * 🔴 THAT SENTENCE IS THE REASON THIS FILE IS NOT ONLY A COST MEASUREMENT.
 * An exception round trip and a native load differ by roughly three orders of
 * magnitude.  A clock therefore SEES what a signal counter cannot, and this
 * program is the first instrument in the project that can decide whether
 * `ll` and `sc` are emulated at all under Linux on this die -- a question
 * `4a` declared unanswerable with its own instrument and answered from the
 * vendor's source instead (讀, `traps.c:589-636`, `do_cpu` carrying
 * `simulate_llsc`).
 *
 * Both outcomes are pre-registered, and they are told apart by ONE number:
 *
 *   `slope(ll) - slope(lw)`  >=  ~1 count/iteration   -> emulated.  `4a`'s
 *       mechanism column becomes 量 by a second and independent route.
 *   `slope(ll) - slope(lw)`  <=  the `nop_a`-vs-`nop_b` spread  -> NOT
 *       emulated in any sense this clock can see, and § 4's "emulated in user
 *       mode" is refuted as a statement about the executing machine.
 *
 * ---------------------------------------------------------------------------
 * THE MEASUREMENT IS A SLOPE, NEVER A POINT
 * ---------------------------------------------------------------------------
 *
 * `SPEC.md` `FW-48`, 量 2026-09-08: an interval instrument's INTERCEPT is
 * contaminated and its SLOPE survives.  Here the intercept absorbs the cell
 * prologue, the two `/proc` reads, two syscall round trips and the handler's
 * own ~1.6 KiB of `scnprintf`; none of that scales with N.  So every row is
 * run at four iteration counts and what is reported is four (N, snapshot)
 * pairs.  THE BOARD DOES NO FITTING.  It does not even subtract a twin.
 *
 * ---------------------------------------------------------------------------
 * THE RULER, AND THE ONE PLACE THE BRIEF'S DESIGN IS WRONG
 * ---------------------------------------------------------------------------
 *
 * `docs/isa-prior-art.md` § 9 ③ chose `jiffies` for the wraps and `TC0CNT`
 * for the sub-tick residue.  🔴 THAT COMPOSITION IS ONLY EXACT WHILE
 * `jiffies` COUNTS TC0 WRAPS, AND UNDER `R5-3b-2` IT DOES NOT -- the system
 * tick is TC1, this project's own clockevent.  Mixing TC1's wrap count with
 * TC0's phase is a clock with a deterministic sawtooth of one whole tick.
 *
 * 量, segment 75, from twelve committed captures in `bench/2026-09-06b/`
 * (`mode=ce` in all twelve, `j` spanning 65,499 jiffies = 655 s):
 *
 *     phi = ((tc0cnt >> 4) - tc1_cycles) mod 2000  =  716 or 717, all twelve
 *
 * So the two counters are phase-LOCKED to +-1 count over 655 s (they divide
 * one CDBR base, 讀 D 8.2) and the offset is a constant 716 counts = 3.58 ms.
 * A constant cancels in a difference -- EXCEPT across the wrap, where the
 * brief's composite steps by exactly -2000 counts while the true clock does
 * not.  P(an interval straddles exactly one such step) = 2 * (1284/2000) *
 * (716/2000) = 0.46.  推: ~46 % of intervals carry an error of exactly
 * 10.0 ms.  On an emulated row at N = 262,144 that is ~1 %; on a native row
 * it is larger than the whole reading.
 *
 * 🟢 THE FIX IS FREE AND IT IS NOT A NEW READING.  `tc1_cycles` is in the
 * SAME 1.6 KiB snapshot, and `jiffies` + `tc1_cycles` are the wrap count and
 * the phase of ONE counter.  This file therefore parses BOTH phases and emits
 * BOTH composites for every rung, and selects neither: the desk computes the
 * one the capture's own `mode`/`ce_live` fields license, and their
 * disagreement is visible rather than absorbed.  Two rulers that must agree
 * is this project's own rule for a register value, applied to a clock.
 *
 * ⚠️ If `ce_live` reads 0 the tick is the vendor's TC0 and the polarity
 * reverses: then `comp_tc0` is the exact one and `comp_tc1` is the sawtooth.
 * Which is why neither is chosen here.
 *
 * ---------------------------------------------------------------------------
 * ONE `open` / ONE `read` / ONE `close`
 * ---------------------------------------------------------------------------
 *
 * `SPEC.md` `FW-64`, 量 2026-09-10: one `cat` is TWO `read_proc` invocations
 * on this kernel, and two of this project's counting identities were written
 * as though it were one.  A single `read(fd, buf, 4096)` of a handler whose
 * output fits in one page is ONE invocation: 讀 `rtl819x-timer.c:2271-2276`,
 * the handler sets `*eof = 1` and returns `min(len, count)`, so the second
 * invocation only happens if something asks for the bytes past `len`.  This
 * program never does.
 *
 * 量: `bench/2026-09-06b/M9-P.log` -- 101 fields, 1,612 bytes from `driver=`
 * to the end.  39.4 % of one page.  🔴 It is still CHECKED rather than
 * assumed: a read returning exactly the buffer size is a refusal, because
 * that is indistinguishable from truncation, and a truncated snapshot loses
 * the FIELDS AT THE END FIRST -- `jiffies` sits at byte ~700 of 1,612 and
 * would survive, which is precisely why silent truncation here would be
 * invisible rather than loud.
 *
 * ---------------------------------------------------------------------------
 * HOUSE RULES THIS FILE IS WRITTEN AGAINST
 * ---------------------------------------------------------------------------
 *
 *   - `write(2)` only.  No stdio.  A buffer flushed at exit puts a row in the
 *     capture at a time that is not the time it was measured, and a row that
 *     is on the wire when it happens survives an `alarm` kill.
 *   - NO DIVISION BY A RUNTIME VALUE anywhere.  gcc emits `break 7` for the
 *     divide-by-zero check and the build gate counts `break` BY OPCODE
 *     (`config/rlxfw-user/isaprobe/Makefile`, G1/G1b).  There is no `/` and
 *     no `%` in this file at all; every reduction is a shift or a multiply.
 *   - The probed encodings are `.word`s in `ucost-cells.S` and are never
 *     mnemonics.  Each is exported as a symbol and PRINTED BY THE BOARD, so
 *     the capture names the byte that executed rather than a C-side copy of
 *     it.  `tools/isa-payload.tsv` remains the owner of every encoding.
 *   - `alarm()` as the deadlock escape, exactly as `uprobe` has it.
 */

#include <unistd.h>
#include <fcntl.h>

#ifndef UCOST_BUILD_ID
#define UCOST_BUILD_ID "0000000000000000"
#endif

typedef unsigned int u32;

/* ---------------------------------------------------------------------------
 * The cells.  `ucost-cells.S`, hand-written, one 16-byte I-cache line per
 * loop body.
 *
 * Signature: void cell(void *base, unsigned n).  $4 = base for the probed
 * word's memory operand, $5 = iteration count.
 *
 * The `_w` symbols sit ON the probed word inside the loop, so reading one
 * from C reads the assembled text.  `probe4`'s `rlx_p4_<name>_w` is the same
 * device one privilege level down, and its gate G3 is the same idea.
 * ------------------------------------------------------------------------- */

extern void uc_cell_nop_a(void *, unsigned);
extern void uc_cell_nop_b(void *, unsigned);
extern void uc_cell_sync (void *, unsigned);
extern void uc_cell_lw   (void *, unsigned);
extern void uc_cell_ll   (void *, unsigned);
extern void uc_cell_sw   (void *, unsigned);
extern void uc_cell_sc   (void *, unsigned);
extern void uc_cell_lwu2 (void *, unsigned);

extern const u32 uc_w_nop_a;
extern const u32 uc_w_nop_b;
extern const u32 uc_w_sync;
extern const u32 uc_w_lw;
extern const u32 uc_w_ll;
extern const u32 uc_w_sw;
extern const u32 uc_w_sc;
extern const u32 uc_w_lwu2;

/* ---------------------------------------------------------------------------
 * Output.  write(2) only.
 * ------------------------------------------------------------------------- */

static void uc_write(const char *s, unsigned n)
{
	unsigned done = 0u;
	while (done < n) {
		int k = (int)write(1, s + done, n - done);
		if (k <= 0)
			return;			/* a closed console is not a finding */
		done += (unsigned)k;
	}
}

static void uc_puts(const char *s)
{
	unsigned n = 0u;
	while (s[n] != '\0')
		n++;
	uc_write(s, n);
}

static void uc_puthex32(u32 v)
{
	static const char hx[] = "0123456789abcdef";
	char b[8];
	int i;
	for (i = 7; i >= 0; i--) {
		b[i] = hx[v & 0xfu];
		v >>= 4;
	}
	uc_write(b, 8u);
}

static void uc_field(const char *k, u32 v)
{
	uc_puts("rlxucost: ");
	uc_puts(k);
	uc_puts("=");
	uc_puthex32(v);
	uc_puts("\r\n");
}

/* ---------------------------------------------------------------------------
 * The ruler
 * ------------------------------------------------------------------------- */

#define UC_PROC		"/proc/rtl819x-timer"
#define UC_BUF		4096u		/* one page: the handler's own bound */
#define UC_SHIFT	4u		/* RTL819X_TC_VALUE_SHIFT, 讀 :485.
					 * `tc0cnt` and `tc0data` are printed
					 * RAW (:2100-2101) where the TC1 path
					 * shifts (:943).  A reader that forgets
					 * this is wrong by 16x. */

static char uc_buf[UC_BUF];

struct uc_snap {
	u32 j;			/* `jiffies=`, decimal, taken mod 2^32 */
	u32 c0raw;		/* `tc0cnt=`, hex, RAW -- shift at use     */
	u32 c1;			/* `tc1_cycles=`, decimal, already shifted */
	u32 irq;		/* `irq_count=`, decimal                  */
	u32 nbytes;		/* what the single read() returned        */
};

/* WHY `irq_count` IS IN THE PER-RUNG SNAPSHOT.  量 seating 14: `Djiffies`,
 * `Dirq_count` and `Dce_cycles / 2000` were all 26,373 over 263.73 s and all
 * 65,476 over 654.76 s, residual 0 in both.  So `Dirq_count == Djiffies` is a
 * measured identity on this image, and a rung where it fails is a rung during
 * which the tick was lost -- which makes the ruler UNDER-read by exactly the
 * lost ticks and would otherwise be invisible.  `IRQ-13` is the measurement
 * that says this is not hypothetical: 11 interrupts in 585 went missing
 * across the vendor NIC's initialisation, 1.88 %.  One extra parsed field
 * turns every rung into a self-checking one. */

/* Parse witnesses: three fields whose values are known before power, so a
 * parser that returns garbage is visible in the header rather than in the
 * slope.  量 `bench/2026-09-06b/M9-P.log`: tc0data=00007D00 (>>4 = 2000),
 * hz_used=200000, hz_kernel=100.  A tool reporting 0 is making a claim. */
static u32 uc_reload;		/* tc0data >> 4, expected 2,000 */
static u32 uc_hz_used;		/* expected 200,000            */
static u32 uc_hz_kernel;	/* expected 100                */
static u32 uc_ce_live;		/* 1 => jiffies is TC1's       */
static u32 uc_mode_ce;		/* `mode=ce`                   */
static u32 uc_reads_ok;
static u32 uc_reads_bad;

/* Find "\n<key>" and return a pointer just past the '='.  0 if absent.
 * `n` is the live length, so a shorter read cannot be walked past. */
static const char *uc_find(const char *buf, unsigned n, const char *key)
{
	unsigned i, k;
	for (i = 0u; i + 1u < n; i++) {
		if (buf[i] != '\n')
			continue;
		for (k = 0u; key[k] != '\0'; k++) {
			if (i + 1u + k >= n || buf[i + 1u + k] != key[k])
				break;
		}
		if (key[k] == '\0' && i + 1u + k < n && buf[i + 1u + k] == '=')
			return buf + i + 2u + k;
	}
	return (const char *)0;
}

/* Decimal.  Accumulated in u32, so `jiffies=%llu` is taken MOD 2^32 on
 * purpose: unsigned wraparound is defined in C, a difference of two such
 * values is exact while the interval is under 2^32 jiffies, and this kernel
 * starts `jiffies` five minutes below 2^32 precisely so the wrap gets
 * exercised.  量 `bench/2026-09-06b/M9-P.log`: jiffies=4294939055. */
static u32 uc_dec_at(const char *p, u32 *out)
{
	u32 v = 0u;
	unsigned k = 0u;
	if (p == 0 || p[0] < '0' || p[0] > '9')
		return 0u;
	while (p[k] >= '0' && p[k] <= '9') {
		v = v * 10u + (u32)(p[k] - '0');
		k++;
	}
	*out = v;
	return 1u;
}

static u32 uc_hex_at(const char *p, u32 *out)
{
	u32 v = 0u;
	unsigned k = 0u;
	if (p == 0)
		return 0u;
	while (k < 8u) {
		char c = p[k];
		u32 d;
		if (c >= '0' && c <= '9')
			d = (u32)(c - '0');
		else if (c >= 'A' && c <= 'F')
			d = (u32)(c - 'A') + 10u;
		else if (c >= 'a' && c <= 'f')
			d = (u32)(c - 'a') + 10u;
		else
			break;
		v = (v << 4) | d;
		k++;
	}
	if (k == 0u)
		return 0u;
	*out = v;
	return 1u;
}

#define UC_SNAP_OK		0u
#define UC_SNAP_EOPEN		1u
#define UC_SNAP_EREAD		2u
#define UC_SNAP_ETRUNC		3u	/* read filled the page: may be short */
#define UC_SNAP_EFIELD		4u

/* ONE open, ONE read, ONE close.  See the header: this is exactly one
 * `read_proc` invocation, and `FW-64` is why that sentence is written down. */
static u32 uc_snap(struct uc_snap *s)
{
	int fd;
	int n;
	const char *p;

	s->j = 0u;
	s->c0raw = 0u;
	s->c1 = 0u;
	s->irq = 0u;
	s->nbytes = 0u;

	fd = open(UC_PROC, O_RDONLY);
	if (fd < 0) {
		uc_reads_bad++;
		return UC_SNAP_EOPEN;
	}
	n = (int)read(fd, uc_buf, UC_BUF);
	close(fd);

	if (n <= 0) {
		uc_reads_bad++;
		return UC_SNAP_EREAD;
	}
	if ((unsigned)n >= UC_BUF) {
		/* Indistinguishable from truncation, and a truncated snapshot
		 * drops the LAST fields, which are not the ones read here --
		 * so this would be silent.  Refuse instead. */
		uc_reads_bad++;
		return UC_SNAP_ETRUNC;
	}
	s->nbytes = (u32)n;

	p = uc_find(uc_buf, (unsigned)n, "jiffies");
	if (p == 0 || uc_dec_at(p, &s->j) == 0u)
		goto bad;
	p = uc_find(uc_buf, (unsigned)n, "tc0cnt");
	if (p == 0 || uc_hex_at(p, &s->c0raw) == 0u)
		goto bad;
	p = uc_find(uc_buf, (unsigned)n, "tc1_cycles");
	if (p == 0 || uc_dec_at(p, &s->c1) == 0u)
		goto bad;
	p = uc_find(uc_buf, (unsigned)n, "irq_count");
	if (p == 0 || uc_dec_at(p, &s->irq) == 0u)
		goto bad;

	uc_reads_ok++;
	return UC_SNAP_OK;
bad:
	uc_reads_bad++;
	return UC_SNAP_EFIELD;
}

/* The slow-moving fields, read once at start-up.  Separate from uc_snap()
 * because a per-rung snapshot must do the least possible work between the
 * handler's spinlock and the loop. */
static u32 uc_snap_static(void)
{
	int fd;
	int n;
	const char *p;
	u32 v;

	fd = open(UC_PROC, O_RDONLY);
	if (fd < 0)
		return UC_SNAP_EOPEN;
	n = (int)read(fd, uc_buf, UC_BUF);
	close(fd);
	if (n <= 0)
		return UC_SNAP_EREAD;
	if ((unsigned)n >= UC_BUF)
		return UC_SNAP_ETRUNC;

	p = uc_find(uc_buf, (unsigned)n, "tc0data");
	if (p == 0 || uc_hex_at(p, &v) == 0u)
		return UC_SNAP_EFIELD;
	uc_reload = v >> UC_SHIFT;

	p = uc_find(uc_buf, (unsigned)n, "hz_used");
	if (p == 0 || uc_dec_at(p, &uc_hz_used) == 0u)
		return UC_SNAP_EFIELD;
	p = uc_find(uc_buf, (unsigned)n, "hz_kernel");
	if (p == 0 || uc_dec_at(p, &uc_hz_kernel) == 0u)
		return UC_SNAP_EFIELD;
	p = uc_find(uc_buf, (unsigned)n, "ce_live");
	if (p == 0 || uc_dec_at(p, &uc_ce_live) == 0u)
		return UC_SNAP_EFIELD;

	p = uc_find(uc_buf, (unsigned)n, "mode");
	uc_mode_ce = (p != 0 && p[0] == 'c' && p[1] == 'e') ? 1u : 0u;

	return UC_SNAP_OK;
}

/* The two composites.  A multiply and a shift; no division anywhere, and the
 * multiplier is the RELOAD READ OFF THE BOARD rather than a compiled 2,000 --
 * `CLAUDE.md`'s eighth update is the precedent: a card that hardcoded the
 * loader's constant would have refuted its own headline by 71.4x with the
 * hardware innocent. */
static u32 uc_comp_tc0(const struct uc_snap *s)
{
	return s->j * uc_reload + (s->c0raw >> UC_SHIFT);
}

static u32 uc_comp_tc1(const struct uc_snap *s)
{
	return s->j * uc_reload + s->c1;
}

/* ---------------------------------------------------------------------------
 * The population
 *
 * Seven cells, three measured rows, and the twins.  Each measured row's twin
 * has the SAME memory shape, so the cell prologue, the loop overhead and the
 * data cache behaviour are identical and only the probed word differs.
 *
 *   row  cell     class  what it is
 *   ---  -------  -----  ------------------------------------------------
 *    0   nop_a      N    zero control A, and `sync`'s twin
 *    1   nop_b      N    zero control B -- a SECOND cell at a SECOND
 *                        address, because `x - x` is a tool that cannot fail
 *    2   sync       E    MEASURED.  量 2026-09-15: `RAN`, no signal, so
 *                        `do_ri` -> `simulate_sync`.  The one row `4a` could
 *                        see (`docs/emulation-surface.md` § 4)
 *    3   lw         N    twin for `ll`: same load, same $2, same base
 *    4   ll         E    MEASURED.  Invisible to `4a` by its own statement
 *    5   sw         N    twin for `sc`: same store, same $9, same base
 *    6   sc         E    MEASURED.  量 2026-09-15: the die stored bare metal
 *                        and did not store under Linux, and cost is what
 *                        separates "the kernel emulated and refused" from
 *                        "the die executed and failed"
 *    7   lwu2       E    MEASURED, and it is the row two of this repository's
 *                        own documents disagree about.  The SAME `lw` word as
 *                        row 3, at a base two bytes higher.  Its twin is row 3
 *                        and the twin is the best in this table: same
 *                        encoding, same registers, same cache line -- the only
 *                        difference is an odd address.
 *
 * 🔴🔴 ROW 7 IS A DECIDING CELL AND BOTH PREDICTIONS ARE WRITTEN DOWN HERE.
 * `SPEC.md` CPU-15, 量 on this die at the loader prompt: all four unaligned
 * load/store instructions EXECUTE and compute the right answer -- the reading
 * that refuted the public record of the Lexra settlement.  If the hardware
 * does them, the kernel's unaligned handler never fires and row 7 costs what
 * row 3 costs: **slope difference at the zero control**.
 * `docs/emulation-surface.md` nevertheless lists five unaligned forms among
 * the eight entries on the emulation surface.  If that is what the executing
 * machine does, row 7 costs an exception round trip -- the most expensive
 * emulation on this kernel and the only one ordinary programs hit.
 * **Those are different numbers and this cell reads one of them.**  Neither
 * document is edited to agree with the other before the board answers.
 *
 * ⚠️ The census `isa-payload.tsv` EXCLUDES the unaligned forms by rule
 * (`docs/isa-prior-art.md` § 0), which is why `4a` could not reach this and
 * why row 7 needs no new tsv row: it reuses row 3's word.
 *
 * ⚠️ `nop_a` is both the zero control's A leg and `sync`'s twin.  That is
 * deliberate and it is stated rather than hidden: the zero control is
 * `nop_a - nop_b` and NOT `nop_a - nop_a`, so it can fail.
 *
 * ⚠️ `sc` writes its own `rt` ($9) on a core that implements it, so
 * iterations 2..N store a different value from iteration 1 while the `sw`
 * twin stores the seed every time.  The instruction STREAM is identical; only
 * the stored datum differs, and a store's cost does not depend on its datum
 * on any machine this project has measured.  推.  The experiment that settles
 * it adds one `ori $9, $0, 1` to BOTH loops, which changes both intercepts
 * and neither slope difference.
 * ------------------------------------------------------------------------- */

#define UC_CLS_N	0u	/* native / control */
#define UC_CLS_E	1u	/* emulation candidate */

struct uc_rowdef {
	void (*cell)(void *, unsigned);
	const u32 *word;
	const char *name;
	u32 cls;
};

static const struct uc_rowdef uc_rows[] = {
	{ uc_cell_nop_a, &uc_w_nop_a, "nop_a", UC_CLS_N },
	{ uc_cell_nop_b, &uc_w_nop_b, "nop_b", UC_CLS_N },
	{ uc_cell_sync,  &uc_w_sync,  "sync",  UC_CLS_E },
	{ uc_cell_lw,    &uc_w_lw,    "lw",    UC_CLS_N },
	{ uc_cell_ll,    &uc_w_ll,    "ll",    UC_CLS_E },
	{ uc_cell_sw,    &uc_w_sw,    "sw",    UC_CLS_N },
	{ uc_cell_sc,    &uc_w_sc,    "sc",    UC_CLS_E },
	{ uc_cell_lwu2,  &uc_w_lwu2,  "lwu2",  UC_CLS_E }
};

#define UC_ROWS		(sizeof(uc_rows) / sizeof(uc_rows[0]))
#define UC_RUNGS	4u

/* THE LADDERS.  Two, because one cannot serve both classes -- the two costs
 * are expected to differ by ~1,000x and a ladder sized for one is either at
 * the quantisation floor or over the time budget for the other.
 *
 * The floor: 1 count = 1/200,005 s = 4.99988 us (推 for the absolute rate --
 * LOG.md:15231 says the 2,000-counts-per-jiffy ratio is 量 and the absolute
 * 200,005 Hz is still 推; the driver's own derived `hz_used` is 200,000).
 * Every rung is sized so the SMALLEST reads >= ~40 counts, i.e. >= ~200 us.
 *
 * 推, from CLK-01's 400 MHz (量) and a four-instruction body at ~4-6 cycles:
 * a native iteration is ~10-15 ns.
 *
 *   class N   16,384 -> ~41 counts     1,048,576 -> ~2,621 counts (13.1 ms)
 *   class E    4,096 -> ~10 counts native / ~4,096 counts if emulated at 5 us
 *             262,144 -> ~655 counts native / 262,144 counts (1.31 s) at 5 us
 *
 * Class E's bottom rung is sized for the NATIVE hypothesis, because if `ll`
 * turns out not to be emulated the row still has to produce a usable slope --
 * a ladder that only works if the answer is the expected one is not an
 * experiment.
 *
 * Both ladders are x4 geometric so the linearity check has the same shape on
 * both, and so the budget guard below can predict the next rung by a multiply.
 */
static const u32 uc_ladder_n[UC_RUNGS] = {   16384u,  65536u, 262144u, 1048576u };
static const u32 uc_ladder_e[UC_RUNGS] = {    4096u,  16384u,  65536u,  262144u };

/* Per-row wall budget, in composite counts.  1,600,000 counts ~ 8.0 s.
 * Seven rows -> ~56 s worst case, against the alarm below.
 *
 * The guard runs BEFORE a rung and predicts it as 4x the previous one, which
 * the x4 ladder makes exact for a linear row.  A prediction the board makes
 * and the desk can check beats a fixed cap that is either too tight or
 * useless -- and a skipped rung is REPORTED, so a two-rung row is visibly a
 * two-rung row rather than a three-rung row with a quiet hole. */
#define UC_BUDGET	1600000u

/* 180 s.  The worst case above is ~56 s; a `sync` at 100 us/iteration would
 * hit the budget guard rather than the alarm.  The alarm exists for the case
 * the budget cannot see: a probed word that does not return at all.  Every
 * row is on the wire when it happens, so an alarm kill leaves a capture with
 * rows and no `end` -- a readable outcome rather than a lost seating. */
#define UC_ALARM	180u

static u32 uc_scratch[8];	/* the memory operand.  8 words = 32 B, and
				 * word 0 is the only one any probed encoding
				 * here touches (all four use 0($10)). */

/* ---------------------------------------------------------------------------
 * One rung
 * ------------------------------------------------------------------------- */

static u32 uc_rung(u32 row, u32 rung, u32 n, u32 *elapsed)
{
	struct uc_snap a, b;
	u32 ra, rb;

	*elapsed = 0u;

	ra = uc_snap(&a);
	if (ra != UC_SNAP_OK)
		return ra;

	uc_rows[row].cell((void *)uc_scratch, n);

	rb = uc_snap(&b);
	if (rb != UC_SNAP_OK)
		return rb;

	/* THE BOARD EMITS RAW SNAPSHOTS.  The two composites are printed as a
	 * convenience and are recomputable from the six raw fields beside
	 * them, so a disagreement between the board's arithmetic and the
	 * desk's is visible.  No fitting, no subtraction of a twin, no
	 * division. */
	uc_puts("UC ");
	uc_puthex32(row);
	uc_puts(" ");
	uc_puts(uc_rows[row].name);
	uc_puts(" ");
	uc_puthex32(uc_rows[row].cls);
	uc_puts(" ");
	uc_puthex32(rung);
	uc_puts(" ");
	uc_puthex32(n);
	uc_puts(" ");
	uc_puthex32(a.j);       uc_puts(" ");
	uc_puthex32(a.c0raw);   uc_puts(" ");
	uc_puthex32(a.c1);      uc_puts(" ");
	uc_puthex32(a.irq);     uc_puts(" ");
	uc_puthex32(b.j);       uc_puts(" ");
	uc_puthex32(b.c0raw);   uc_puts(" ");
	uc_puthex32(b.c1);      uc_puts(" ");
	uc_puthex32(b.irq);     uc_puts(" ");
	uc_puthex32(uc_comp_tc0(&b) - uc_comp_tc0(&a)); uc_puts(" ");
	uc_puthex32(uc_comp_tc1(&b) - uc_comp_tc1(&a)); uc_puts(" ");
	uc_puthex32(b.j - a.j);                         uc_puts(" ");
	uc_puthex32(b.irq - a.irq);                     uc_puts(" ");
	uc_puthex32(a.nbytes);
	uc_puts("\r\n");

	/* The budget follows whichever ruler the tick licenses.  This is the
	 * ONE place the program chooses, and it chooses only for its own
	 * guard -- never for what it reports. */
	*elapsed = uc_ce_live ? (uc_comp_tc1(&b) - uc_comp_tc1(&a))
			      : (uc_comp_tc0(&b) - uc_comp_tc0(&a));
	return UC_SNAP_OK;
}

static void uc_run_row(u32 row)
{
	const u32 *ladder = (uc_rows[row].cls == UC_CLS_E) ? uc_ladder_e
							  : uc_ladder_n;
	u32 rung, spent = 0u, last = 0u, done = 0u, rc = UC_SNAP_OK;

	for (rung = 0u; rung < UC_RUNGS; rung++) {
		if (rung > 0u) {
			u32 predict = last << 2;	/* x4 ladder */
			if (spent + predict > UC_BUDGET)
				break;
		}
		rc = uc_rung(row, rung, ladder[rung], &last);
		if (rc != UC_SNAP_OK)
			break;
		spent += last;
		done++;
	}

	uc_puts("UCEND ");
	uc_puthex32(row);
	uc_puts(" ");
	uc_puts(uc_rows[row].name);
	uc_puts(" rungs=");
	uc_puthex32(done);
	uc_puts(" spent=");
	uc_puthex32(spent);
	uc_puts(" rc=");
	uc_puthex32(rc);
	uc_puts("\r\n");
}

/* ---------------------------------------------------------------------------
 * Controls
 *
 * C0  TWO READS BACK TO BACK, NOTHING BETWEEN.  Bounds the intercept: the
 *     reported number IS the per-read cost, so the desk can say how much of
 *     each rung's reading is instrument.  It must be small and non-negative.
 *
 * C1  THE CLOCK MUST MOVE.  A parser that returned 0 for every field would
 *     report every cost as zero, and zero cost reads as "nothing is
 *     emulated" -- which is `docs/emulation-surface.md` § 7.3's backwards
 *     reading, one level down at the instrument.  `CLAUDE.md`: a tool
 *     reporting 0 is making a claim.  A REFUSAL, not a warning.
 *
 * C2  THE THREE PARSE WITNESSES, printed in the header: `reload` must read
 *     0x7D0 (2,000), `hz_used` 200,000 and `hz_kernel` 100.  量
 *     `bench/2026-09-06b/M9-P.log`.  The program refuses only on `reload`
 *     == 0 (which would make the composite degenerate) and PRINTS the other
 *     two, because a board whose `hz_used` is not 200,000 is a finding about
 *     the board and not a reason to stop.
 * ------------------------------------------------------------------------- */

static u32 uc_c0(void)
{
	struct uc_snap a, b;
	if (uc_snap(&a) != UC_SNAP_OK)
		return 0xffffffffu;
	if (uc_snap(&b) != UC_SNAP_OK)
		return 0xffffffffu;
	return uc_ce_live ? (uc_comp_tc1(&b) - uc_comp_tc1(&a))
			  : (uc_comp_tc0(&b) - uc_comp_tc0(&a));
}

static u32 uc_c1(void)
{
	struct uc_snap a, b;
	if (uc_snap(&a) != UC_SNAP_OK)
		return 0xffffffffu;
	uc_cell_nop_a((void *)uc_scratch, uc_ladder_n[UC_RUNGS - 1u]);
	if (uc_snap(&b) != UC_SNAP_OK)
		return 0xffffffffu;
	return uc_ce_live ? (uc_comp_tc1(&b) - uc_comp_tc1(&a))
			  : (uc_comp_tc0(&b) - uc_comp_tc0(&a));
}

/* ---------------------------------------------------------------------------
 * main
 * ------------------------------------------------------------------------- */

/* Decimal, by hand rather than `atoi`: `atoi` on a string that is not a
 * number is undefined, and the one place this program takes input is a line
 * an operator typed at a bench.  `uprobe`'s `up_dec`, same reason. */
static u32 uc_arg(const char *s, u32 dflt)
{
	u32 v = 0u;
	unsigned k;
	if (s == 0 || s[0] == '\0')
		return dflt;
	for (k = 0u; s[k] != '\0'; k++) {
		if (s[k] < '0' || s[k] > '9')
			return dflt;
		v = v * 10u + (u32)(s[k] - '0');
	}
	return v;
}

/* usage: ucost [NONCE [ROWFIRST [ROWLAST]]]
 *
 * The range exists for the same reason `uprobe`'s does: one row that hangs
 * the board must not cost the other six, and on this project a power cycle is
 * the most expensive unit there is. */
int main(int argc, char **argv)
{
	u32 i, first, last, c0, c1;
	u32 rc;

	uc_puts("\r\n*** rlxucost UC ");
	uc_puts(UCOST_BUILD_ID);
	uc_puts(" ");
	uc_puts((argc > 1 && argv[1] != 0) ? argv[1] : "-");
	uc_puts(" ***\r\n");

	first = (argc > 2) ? uc_arg(argv[2], 0u) : 0u;
	last  = (argc > 3) ? uc_arg(argv[3], (u32)UC_ROWS - 1u)
			   : (u32)UC_ROWS - 1u;
	if (last >= (u32)UC_ROWS)
		last = (u32)UC_ROWS - 1u;
	if (first > last)
		first = last;

	uc_field("rows",   (u32)UC_ROWS);
	uc_field("rungs",  UC_RUNGS);
	uc_field("first",  first);
	uc_field("last",   last);
	uc_field("budget", UC_BUDGET);
	uc_field("alarm",  UC_ALARM);
	uc_field("shift",  UC_SHIFT);

	/* The encodings, read out of the assembled text.  A `.word` that
	 * drifted from `tools/isa-payload.tsv` is visible in the capture and
	 * not only in a build gate nobody re-ran. */
	uc_field("w_nop_a", uc_w_nop_a);
	uc_field("w_nop_b", uc_w_nop_b);
	uc_field("w_sync",  uc_w_sync);
	uc_field("w_lw",    uc_w_lw);
	uc_field("w_ll",    uc_w_ll);
	uc_field("w_sw",    uc_w_sw);
	uc_field("w_sc",    uc_w_sc);

	uc_field("lad_n0", uc_ladder_n[0]);
	uc_field("lad_n3", uc_ladder_n[UC_RUNGS - 1u]);
	uc_field("lad_e0", uc_ladder_e[0]);
	uc_field("lad_e3", uc_ladder_e[UC_RUNGS - 1u]);

	rc = uc_snap_static();
	uc_field("static_rc", rc);
	if (rc != UC_SNAP_OK) {
		uc_puts("rlxucost: REFUSED ruler\r\n");
		uc_puts("rlxucost: end\r\n");
		return 2;
	}

	/* C2, the parse witnesses. */
	uc_field("reload",    uc_reload);	/* expect 000007d0 = 2,000   */
	uc_field("hz_used",   uc_hz_used);	/* expect 00030d40 = 200,000 */
	uc_field("hz_kernel", uc_hz_kernel);	/* expect 00000064 = 100     */
	uc_field("ce_live",   uc_ce_live);
	uc_field("mode_ce",   uc_mode_ce);
	if (uc_reload == 0u) {
		uc_puts("rlxucost: REFUSED reload\r\n");
		uc_puts("rlxucost: end\r\n");
		return 3;
	}

	/* C0 and C1. */
	c0 = uc_c0();
	uc_field("c0_readpair", c0);
	c1 = uc_c1();
	uc_field("c1_clockmoves", c1);
	if (c1 == 0u || c1 == 0xffffffffu) {
		/* Zero here means the clock did not move over ~1 M native
		 * iterations, which cannot be true and therefore means the
		 * ruler is not being read.  Every cost below would be 0. */
		uc_puts("rlxucost: REFUSED control\r\n");
		uc_puts("rlxucost: end\r\n");
		return 4;
	}

	alarm(UC_ALARM);

	uc_puts("rlxucost: rows begin\r\n");
	for (i = first; i <= last; i++)
		uc_run_row(i);
	uc_puts("rlxucost: rows end\r\n");
	alarm(0u);

	uc_field("reads_ok",  uc_reads_ok);
	uc_field("reads_bad", uc_reads_bad);
	uc_field("scratch0",  uc_scratch[0]);
	uc_puts("rlxucost: end\r\n");
	return 0;
}
