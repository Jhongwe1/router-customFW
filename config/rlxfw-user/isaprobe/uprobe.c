/* uprobe.c -- `R1c`'s column-② instrument, and this project's first compiled
 * userspace program.
 *
 * WHAT IT IS.  `probe4` runs 75 instruction encodings BARE METAL, under this
 * project's own exception handler, at `Status = 0x1000FC00`.  This runs THE
 * SAME 75 ENCODINGS as an ordinary Linux process, under rlxfw's own kernel,
 * and records the same eight words per row.  `docs/emulation-surface.md`
 * calls the two readings column ① and column ②; the rows where they differ
 * are the kernel's emulation surface.
 *
 * WHY IT LINKS `cells4.S` RATHER THAN RE-DECLARING THE POPULATION.  Because
 * then the two columns are not two tables that agree -- they are one table,
 * one generator (`tools/isapay.py emit` from `tools/isa-payload.tsv`), and
 * literally the same `.word` bytes, executed twice at two privilege levels.
 * A second population here would be a second owner of the thing the whole
 * comparison rests on.  `tools/isa-payload.tsv`'s own header says it: "THIS
 * IS THE OWNER ... nothing else may declare a probed encoding."
 *
 * ---------------------------------------------------------------------------
 * THE ABI HAZARD THIS FILE IS WRITTEN AGAINST, 量 2026-09-15
 * ---------------------------------------------------------------------------
 *
 * The signal frame this program is handed is written by `arch/rlx`, and the
 * `struct sigcontext` in `arch/rlx/include/asm/sigcontext.h` is a TRUNCATED
 * one: `{ sc_regmask, sc_status, sc_pc, sc_regs[32], sc_mdhi, sc_mdlo }`,
 * sizeof 288.  The toolchain's own `<bits/sigcontext.h>` carries the STOCK
 * MIPS struct -- the same prefix, then `sc_fpregs[32]`, `sc_ownedfp`,
 * `sc_fpc_csr`, `sc_fpc_eir`, `sc_used_math`, `sc_dsp`, `sc_mdhi`, `sc_mdlo`,
 * `sc_hi1`..`sc_lo3` -- sizeof 592.  Both were read on 2026-09-15; the kernel
 * one in all three GPL drops (byte-identical), the libc one in
 * `rsdk-1.3.6-4181-EB-2.6.30-0.9.30/include/bits/sigcontext.h`.
 *
 * The two AGREE on everything this file reads:
 *
 *     uc_mcontext        at uc + 24     (both; `stack_t` is {sp,size,flags}
 *                                        in both, and the 8-alignment pad
 *                                        before sigcontext is in both)
 *     sc_pc              at uc + 32     -- 64-bit slot, BIG ENDIAN, so the
 *                                        meaningful 32-bit word is at uc + 36
 *     sc_regs[i]         at uc + 40 + 8*i, meaningful word at + 4
 *
 * They DISAGREE from `sc_fpregs` onward, and the disagreement is not
 * cosmetic.  The kernel writes `uc_sigmask` at uc + 312 and allocates the
 * whole `rt_sigframe` 480 bytes; the libc header puts `uc_sigmask` at
 * uc + 616 and makes `sizeof(ucontext_t)` 744.  **Assigning to
 * `uc->uc_sigmask` through the libc header writes 128 bytes starting 136
 * bytes past the end of the frame the kernel allocated.**  Nothing in this
 * file touches a ucontext field below `sc_regs`, and the offsets it does use
 * are asserted against the libc header at COMPILE time (below), so a
 * toolchain whose header stops agreeing fails the build instead of producing
 * a measurement.
 *
 * ---------------------------------------------------------------------------
 * WHY THE HANDLER ADVANCES `sc_pc` INSTEAD OF ONLY `siglongjmp`-ing
 * ---------------------------------------------------------------------------
 *
 * 讀 `arch/rlx/kernel/traps.c`, 2026-09-15.  In `do_ri` the EPC is advanced
 * by `compute_return_epc()` and then put back -- `regs->cp0_epc = old_epc;`
 * carrying the source's own comment "Undo skip-over" -- immediately before
 * `force_sig`.  In `do_cpu` the `cpid == 0` arm does the same, and the
 * `cpid != 0` arm never calls `compute_return_epc` at all, so its EPC was
 * never advanced either.
 *
 * 🔴 **So in all three signal-delivering paths `sc_pc` names the FAULTING
 * INSTRUCTION, and `+4` is uniformly correct.**  That is a measured result
 * and not the obvious one: a plausible reading of `do_cpu` is that its
 * `cpid != 0` arm leaves the EPC advanced, which would make `+4` skip an
 * extra instruction.  It does not, because the advance is inside the
 * `cpid == 0` block.
 *
 * Advancing rather than jumping matters for one reason: `siglongjmp` unwinds,
 * so the cell never reaches its own epilogue and the recorded output words
 * are whatever they were before the fault.  Advancing lets the cell finish
 * and write `out_gpr`/`out_m0`/`out_m1`/`out_aux`, which is what makes the
 * three-way verdict (traps / ran-and-right / ran-and-WRONG) available in this
 * arm as well as in `probe4`'s.  `tools/isa-payload.tsv`'s `ll` row is the
 * example that decides it: `ll` and `lwc0` are the same encoding, and only
 * the VALUE separates them.
 *
 * `siglongjmp` is kept as an ESCAPE HATCH, not as the mechanism.  A probed
 * word that transfers control -- `tools/isa-payload.tsv`'s `jr` row, or any
 * encoding that happens to decode as a jump -- can land somewhere unmapped,
 * where `+4` is unmapped too, and the process takes a signal per word
 * forever.  That is a hang, not a reading.  After `UP_MAX_SIG` signals in one
 * row the handler jumps out and the row is recorded as ESCAPED.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS PROGRAM DOES NOT DO
 * ---------------------------------------------------------------------------
 *
 * It does not adjudicate.  Exactly like `probe4`, it records `n`, the signal,
 * the faulting PC and four result words, and the verdict is computed at the
 * desk by `tools/isapay.py verdict`.  A payload that decides right-vs-wrong
 * in place reports a boolean and throws the value away.
 *
 * It does not check that the PC it reports is the probed word's address --
 * that check exists, it is control C2, and it lives at the desk because the
 * desk can resolve `rlx_p4_<name>_w` out of THIS BINARY's symbol table.
 * Compiling 75 more addresses in would be a second copy of an address the
 * ELF already carries.
 *
 * It says nothing about cost.  `docs/emulation-surface.md` § 0 "does not
 * claim ②": every how-much-does-emulation-cost question is `4b`.
 */

#include <signal.h>
#include <sys/ucontext.h>	/* for `ucontext_t` and `struct sigcontext` --
				 * <signal.h> alone does not guarantee either,
				 * and `bits/sigcontext.h` refuses to be
				 * included any other way */
#include <setjmp.h>
#include <string.h>
#include <unistd.h>
#include <stddef.h>

#include "probe4rows.h"		/* GENERATED, tools/rlxprobe/, by isapay.py */

#ifndef UPROBE_BUILD_ID
#define UPROBE_BUILD_ID "0000000000000000"
#endif

typedef unsigned int u32;

/* ---------------------------------------------------------------------------
 * The kernel's frame offsets, and the compile-time proof that the libc header
 * agrees with them where we rely on it.
 * ------------------------------------------------------------------------- */

#define UC_MCONTEXT	24u			/* &uc->uc_mcontext - uc     */
#define SC_PC		8u			/* sigcontext.sc_pc          */
#define SC_REGS		16u			/* sigcontext.sc_regs[0]     */
#define BE_LO		4u			/* low word of a BE u64 slot */

#define UC_PC_LO	(UC_MCONTEXT + SC_PC + BE_LO)		/* 36 */

/* A build-time refusal, not a comment.  If a toolchain's <signal.h> ever
 * stops agreeing with `arch/rlx` on these three, the array size goes negative
 * and the compiler stops -- which is the only moment at which the
 * disagreement is cheap. */
typedef char up_assert_mcontext[(offsetof(ucontext_t, uc_mcontext) == UC_MCONTEXT) ? 1 : -1];
typedef char up_assert_scpc[(offsetof(struct sigcontext, sc_pc) == SC_PC) ? 1 : -1];
typedef char up_assert_scregs[(offsetof(struct sigcontext, sc_regs) == SC_REGS) ? 1 : -1];
typedef char up_assert_be[(sizeof(long long) == 8) ? 1 : -1];

/* ---------------------------------------------------------------------------
 * `SAFE_A0` in cells4.S references this.  Bare metal it is the guard against
 * the loader's `do_reserved` dereferencing the faulting code's `$a0`
 * (`tools/rlxprobe/rlxasm.h`).  Under Linux nothing reads `$a0` on the
 * exception path, so it is inert here -- but the cells are linked VERBATIM
 * and a verbatim link means taking their externs too.  Defining it is
 * cheaper and more honest than forking the generator for one macro.
 * ------------------------------------------------------------------------- */
u32 rlx_fault_frame[64];

/* ---------------------------------------------------------------------------
 * Output.  write(2) only -- no stdio.
 *
 * Not a size decision.  stdio buffers, and a buffer that is flushed by exit
 * rather than by the row that filled it puts the rows in the capture at a
 * time that is not the time they were measured.  Every other instrument in
 * this project writes a row when the row happens.
 * ------------------------------------------------------------------------- */

static void up_write(const char *s, unsigned n)
{
	unsigned done = 0u;
	while (done < n) {
		int k = (int)write(1, s + done, n - done);
		if (k <= 0)
			return;			/* a closed console is not a finding */
		done += (unsigned)k;
	}
}

static void up_puts(const char *s)
{
	unsigned n = 0u;
	while (s[n] != '\0')
		n++;
	up_write(s, n);
}

static void up_puthex32(u32 v)
{
	static const char hx[] = "0123456789abcdef";
	char b[8];
	int i;
	for (i = 7; i >= 0; i--) {
		b[i] = hx[v & 0xfu];
		v >>= 4;
	}
	up_write(b, 8u);
}

static void up_field(const char *k, u32 v)
{
	up_puts("rlxuprobe: ");
	up_puts(k);
	up_puts("=");
	up_puthex32(v);
	up_puts("\r\n");
}

/* ---------------------------------------------------------------------------
 * The handler
 * ------------------------------------------------------------------------- */

#define UP_MAX_SIG	8u		/* per row, before the escape hatch */

#define UP_MODE_PC	0		/* advance sc_pc past the faulting word */
#define UP_MODE_JMP	1		/* siglongjmp out (control C1a only)    */

static volatile sig_atomic_t	up_mode;
static volatile sig_atomic_t	up_armed;
static volatile u32		up_n;
static volatile u32		up_sig;
static volatile u32		up_code;
static volatile u32		up_pc;
static sigjmp_buf		up_esc;

static void up_handler(int sig, siginfo_t *si, void *ucv)
{
	unsigned char *uc = (unsigned char *)ucv;
	volatile u32 *pcp = (volatile u32 *)(void *)(uc + UC_PC_LO);

	up_n++;

	/* The FIRST signal is the row's reading.  A second one is either the
	 * escape hatch's business or, for a row whose word decodes as a
	 * transfer of control, noise -- and `up_n` carries it either way. */
	if (up_n == 1u) {
		up_sig  = (u32)sig;
		up_code = (si != 0) ? (u32)si->si_code : 0u;
		up_pc   = *pcp;
	}

	if (up_mode == UP_MODE_JMP) {
		if (up_armed)
			siglongjmp(up_esc, 1);
		_exit(96);			/* unreachable by construction */
	}

	if (up_n > UP_MAX_SIG) {
		if (up_armed)
			siglongjmp(up_esc, 2);
		_exit(97);
	}

	*pcp = *pcp + 4u;
}

static int up_install(void)
{
	static const int sigs[] = { SIGILL, SIGBUS, SIGSEGV, SIGFPE, SIGTRAP };
	struct sigaction sa;
	unsigned i;

	for (i = 0u; i < sizeof(sigs) / sizeof(sigs[0]); i++) {
		memset(&sa, 0, sizeof sa);
		sa.sa_sigaction = up_handler;
		sa.sa_flags = SA_SIGINFO;
		sigemptyset(&sa.sa_mask);
		if (sigaction(sigs[i], &sa, (struct sigaction *)0) != 0)
			return (int)(i + 1u);	/* which one failed */
	}
	return 0;
}

/* ---------------------------------------------------------------------------
 * One row
 * ------------------------------------------------------------------------- */

#define UP_SCRATCH_WORDS	(P4_SCRATCH_B / 4u)

static u32 up_scratch[UP_SCRATCH_WORDS];

/* `probe4.c`'s layout, reproduced because `cells4.S` encodes it in every
 * cell's offsets: 0 in_a, 1 in_b, 2 seed(-> $2), 3 -, 4 mem0, 5 mem1,
 * 6 out_gpr, 7 out_m0, 8 out_m1, 9 out_aux. */
#define UP_O_OUT_GPR	6u
#define UP_O_OUT_M0	7u
#define UP_O_OUT_M1	8u
#define UP_O_OUT_AUX	9u

static u32 up_scratch_bad;

/* The row index lives at file scope and is `volatile` because it is read AFTER
 * a `siglongjmp` that may have come from the escape hatch.
 *
 * 🔴 This is not defensive style; gcc refused the build over it and the
 * refusal was right.  C says an automatic object that is not `volatile` and
 * was modified between `sigsetjmp` and `siglongjmp` has an INDETERMINATE
 * value afterwards.  A clobbered index here would not crash: it would print a
 * correct-looking row under the wrong name, with the wrong tag, and
 * `isapay.py verdict_row` would score it NOT-RUN or, worse, score it against
 * another row's expectation.  The escape hatch is exactly the path where it
 * would happen, and exactly the path that is hard to reach on purpose.
 */
static volatile u32 up_row_idx;

static void up_emit_row(u32 i, const char *name, const u32 w[8])
{
	unsigned j;
	up_puts("PU ");
	up_puthex32(i);
	up_puts(" ");
	up_puts(name);
	for (j = 0u; j < 8u; j++) {
		up_puts(" ");
		up_puthex32(w[j]);
	}
	up_puts("\r\n");
}

static void up_run_row(u32 i)
{
	const struct p4_row *r = &p4_rows[i];
	u32 w[8];
	unsigned j;
	int jv;

	up_row_idx = i;

	for (j = 0u; j < UP_SCRATCH_WORDS; j++)
		up_scratch[j] = 0u;
	up_scratch[0] = r->in_a;
	up_scratch[1] = r->in_b;
	up_scratch[2] = r->seed;
	up_scratch[4] = r->mem0;
	up_scratch[5] = r->mem1;

	up_n = 0u;
	up_sig = 0u;
	up_code = 0u;
	up_pc = 0u;
	up_mode = UP_MODE_PC;

	jv = sigsetjmp(up_esc, 1);
	if (jv == 0) {
		up_armed = 1;
		r->cell((void *)up_scratch);
	}
	up_armed = 0;

	/* word 0 is the tag, written by the HARNESS and not by the cell, so a
	 * row that never ran is distinguishable from a row that ran and read
	 * zero -- `isapay.py verdict_row` returns NOT-RUN on a tag mismatch. */
	w[0] = P4_TAG_BASE | up_row_idx;
	w[1] = up_n;
	w[2] = (up_sig << 16) | (up_code & 0xffffu);
	w[3] = up_pc;
	w[4] = up_scratch[UP_O_OUT_GPR];
	w[5] = up_scratch[UP_O_OUT_M0];
	w[6] = up_scratch[UP_O_OUT_M1];
	w[7] = up_scratch[UP_O_OUT_AUX];

	/* 🔴 There is deliberately NO escaped-flag bit in `w[1]`.
	 *
	 * The first draft set bit 31 of `n`.  `tools/isapay.py`'s `verdict_row`
	 * decides TRAPS with `if n:` -- a truthiness test on the raw word -- so
	 * an escaped row that never trapped would have read TRAPS, and the two
	 * arms' word 1 would have meant two different things.
	 *
	 * The flag was redundant anyway: the handler jumps out at
	 * `up_n > UP_MAX_SIG`, so `n` never exceeds `UP_MAX_SIG + 1` and
	 * `n == UP_MAX_SIG + 1` IS the escape.  `max_sig` is printed in the
	 * header so the desk derives the threshold from the capture instead of
	 * hard-coding it.  The count stays a count.
	 */
	(void)jv;

	if (up_scratch[0] != p4_rows[up_row_idx].in_a ||
	    up_scratch[1] != p4_rows[up_row_idx].in_b)
		up_scratch_bad++;

	(void)r;
	up_emit_row(up_row_idx, p4_names[up_row_idx], w);
}

/* ---------------------------------------------------------------------------
 * Controls
 * ------------------------------------------------------------------------- */

/* C1a.  A handler that did not install reports "no signal" for every row, and
 * "no signal" is exactly the reading that means THE SILICON IMPLEMENTS IT.
 * `docs/emulation-surface.md` § 7.3 names that backwards reading as the trap
 * for `ll`/`sc`; this is the same trap one level down, at the instrument.
 *
 * `raise` is used rather than an illegal encoding because it exercises the
 * signal path with NOTHING borrowed from the thing under test.  It must run
 * in JMP mode: `raise`'s own PC is inside libc, and advancing it by 4 would
 * skip an instruction of `raise`. */
static u32 up_c1a(void)
{
	int jv;
	up_n = 0u;
	up_mode = UP_MODE_JMP;
	jv = sigsetjmp(up_esc, 1);
	if (jv == 0) {
		up_armed = 1;
		raise(SIGILL);
	}
	up_armed = 0;
	up_mode = UP_MODE_PC;
	return (jv != 0 && up_n >= 1u) ? 1u : 0u;
}

/* C1b.  An actual reserved encoding must reach the handler.  The row is
 * `special0e` (`0x0000000E`), 量 ExcCode 0x0A on this die 2026-08-29, and it
 * is run here as a control BEFORE the sweep as well as being row N of it.
 * Running it twice is free: the cell has no state. */
static u32 up_find(const char *want)
{
	u32 i;
	for (i = 0u; i < P4_ROWS; i++) {
		if (strcmp(p4_names[i], want) == 0)
			return i;
	}
	return P4_ROWS;				/* not found */
}

static u32 up_c1b(void)
{
	unsigned j;
	u32 found = up_find("special0e");

	if (found == P4_ROWS)
		return 0xffffffffu;		/* the row is gone: a finding */

	/* file-scope and volatile for the same reason `up_run_row` uses it */
	up_row_idx = found;

	for (j = 0u; j < UP_SCRATCH_WORDS; j++)
		up_scratch[j] = 0u;
	up_scratch[2] = p4_rows[up_row_idx].seed;
	up_n = 0u;
	up_mode = UP_MODE_PC;
	up_armed = 1;
	if (sigsetjmp(up_esc, 1) == 0)
		p4_rows[up_row_idx].cell((void *)up_scratch);
	up_armed = 0;
	return up_n;
}

/* ---------------------------------------------------------------------------
 * main
 * ------------------------------------------------------------------------- */

/* Decimal, six lines, rather than `atoi`.  Not a size argument: `atoi` on a
 * string that is not a number is undefined, and the one place this program
 * takes input is a line an operator typed at a bench. */
static u32 up_dec(const char *s, u32 dflt)
{
	u32 v = 0u;
	unsigned k = 0u;
	if (s == 0 || s[0] == '\0')
		return dflt;
	for (k = 0u; s[k] != '\0'; k++) {
		if (s[k] < '0' || s[k] > '9')
			return dflt;
		v = v * 10u + (u32)(s[k] - '0');
	}
	return v;
}

/* usage: uprobe [NONCE [FIRST [LAST]]]
 *
 * The range exists so that one row that hangs the board does not cost the
 * other 74.  On this project a power cycle is the most expensive unit there
 * is; two extra arguments are not.  With no range it runs all of them, which
 * is what a healthy seating does in one command. */
int main(int argc, char **argv)
{
	u32 i, c1a, c1b, first, last;
	int rc;

	up_puts("\r\n*** rlxuprobe PU ");
	up_puts(UPROBE_BUILD_ID);
	up_puts(" ");
	up_puts((argc > 1 && argv[1] != 0) ? argv[1] : "-");
	up_puts(" ***\r\n");

	first = (argc > 2) ? up_dec(argv[2], 0u) : 0u;
	last  = (argc > 3) ? up_dec(argv[3], P4_ROWS - 1u) : P4_ROWS - 1u;
	if (last >= P4_ROWS)
		last = P4_ROWS - 1u;
	if (first > last)
		first = last;

	up_field("rows", P4_ROWS);
	up_field("first", first);
	up_field("last", last);
	up_field("scratch_b", P4_SCRATCH_B);
	up_field("uc_pc_lo", UC_PC_LO);
	up_field("max_sig", UP_MAX_SIG);
	up_field("scratch_at", (u32)(unsigned long)&up_scratch[0]);

	rc = up_install();
	up_field("install_rc", (u32)rc);
	if (rc != 0) {
		/* Refuse.  A sweep with no handler produces 75 rows of
		 * "no signal", which reads as a die that implements
		 * everything.  Better to print nothing. */
		up_puts("rlxuprobe: REFUSED install\r\n");
		up_puts("rlxuprobe: end\r\n");
		return 2;
	}

	c1a = up_c1a();
	up_field("c1a_raise", c1a);
	c1b = up_c1b();
	up_field("c1b_special0e_n", c1b);
	if (c1a == 0u || c1b == 0u || c1b == 0xffffffffu) {
		up_puts("rlxuprobe: REFUSED control\r\n");
		up_puts("rlxuprobe: end\r\n");
		return 3;
	}

	/* The escape hatch bounds a SIGNAL STORM; this bounds a HANG.  A probed
	 * word that decodes as a backward branch, or a `jr` to an address that
	 * happens to be mapped, loops with no signal at all and no counter
	 * moves.  On this project that costs a power cycle, which is the most
	 * expensive unit there is.  `SIGALRM`'s default action terminates, and
	 * because every row is `write(2)`-ed as it happens with no buffering,
	 * the console already holds every row up to the hang -- a capture with
	 * rows and no `rlxuprobe: end` is a readable outcome rather than a lost
	 * seating.
	 *
	 * 30 s against a measured need of ~1.9 s: 7,087 bytes at 38400 8N1 is
	 * 1.85 s of wire time, and the qemu run's compute was far below that.
	 */
	alarm(30u);

	up_puts("rlxuprobe: rows begin\r\n");
	for (i = first; i <= last; i++)
		up_run_row(i);
	up_puts("rlxuprobe: rows end\r\n");
	alarm(0u);

	up_field("scratch_bad", up_scratch_bad);
	up_puts("rlxuprobe: end\r\n");
	return 0;
}
