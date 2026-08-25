/* probe1.c -- R1d on silicon: which cache-management sequence makes this core
 * see an instruction that was just written into RAM.
 *
 * What is settled and what is not
 * -------------------------------
 * `notes/cache-model.md` answered the desk half of R1d from two sources and it
 * ends on this sentence: "Both of those are single-source for the exact bit
 * values.  Before either goes into rlxprobe, confirm on silicon."  That is what
 * this payload is.  It decides nothing about the Lexra family; it decides what
 * this die does.
 *
 * Six cells, and the first one is the one that matters
 * ----------------------------------------------------
 * Each cell primes a victim function (so its instructions are in the I-cache),
 * rewrites one immediate field of it in RAM, applies one candidate treatment,
 * calls it again, and reads the word back uncached.
 *
 *   1  store cached,   NO treatment      the NEGATIVE CONTROL
 *   5  store uncached, NO treatment      does bypassing the D-cache change it
 *   4  store cached,   Status.IsC/SwC    the mechanism c-r3k.c uses and this
 *                                        unit's own bootcode never does
 *   2  store cached,   CCTL 0x002        invalidate I, alone
 *   3  store cached,   CCTL 0x200,0x002  the vendor bootcode's own sequence
 *   6  store uncached, CCTL 0x002        the recipe notes/cache-model.md
 *                                        recommends for R1d, measured rather
 *                                        than assumed, because probe2 uses it
 *
 * THE CELLS RUN IN THAT ORDER, WHICH IS INCREASING RISK, and every cell's
 * result is in the result block before the next one starts.  Cells 1 and 5
 * execute no instruction this payload has not already executed.  Cell 4 writes
 * CP0 Status, which is MIPS-I.  Cells 2, 3 and 6 write CP0 register 20, which
 * is Lexra's and has never been touched from anything but the vendor's own
 * code -- so if a fault ends the run, everything before that point survives.
 *
 * Cell 1 decides whether the other five mean anything.  If a freshly written
 * instruction executes with no treatment at all, then either this core has no
 * I-cache, or the line was evicted between the two calls, or the caches are
 * coherent -- and under any of the three, a cell that "passed" passed without
 * being tested.  `PROGRESS.md`'s R1-gate refutation condition is written
 * against exactly that outcome.
 *
 * Two channels, because one of them has failed before
 * ---------------------------------------------------
 * Every result goes to the UART and to a block at RLX_RESULT_BASE, written
 * through KSEG1 so no part of it is sitting in a write-back D-cache when the
 * watchdog fires.  MEM-10 measured a two-word canary at 0x80A00000 surviving
 * three warm resets byte for byte, so after this payload hands the board back
 * to the loader, `DW 80A00000` recovers the run.  Upstream's P9-12 lost its
 * nonce to a 16-byte FIFO; a payload with one output channel is that failure
 * waiting for a second chance.
 *
 * What a fault costs, and what this payload does about it
 * -------------------------------------------------------
 * READ, 2026-08-25, from this unit's own stage 2: a fault the loader does not
 * handle reaches `do_reserved` at 0x80400BE8, which prints twice and then
 * executes `j 0x80400C18` -- a branch to itself, with interrupts already
 * disabled by the exception entry and the watchdog not armed.  IT HANGS
 * FOREVER.  A fault costs one power cycle, and there is no spare device.
 *
 * So the payload is ordered by risk and writes every result before taking the
 * next one, and cache.S's SAFE_A0 keeps $a0 out of kuseg at every instruction
 * that could fault -- because `do_reserved` dereferences the faulting code's
 * own $a0 and `rlx_cctl(0x002)` would otherwise hand it the integer 2.  What
 * that would actually do is UNDETERMINED, not catastrophic: the sharper claim
 * ("it could branch into the loader's flash-write path") was checked and
 * withdrawn the same day.  The guard costs two instructions.
 *
 * The prior on the risky instructions is better than it looks.  `mtc0 $t,$20`
 * -- what cells 2, 3 and 6 use -- is executed by this unit's own loader on
 * every power-on, at 0x804004DC, 0x804004F8, 0x80400514, 0x804066C0 and
 * 0x804066E8, and the board boots.  The one instruction here that no vendor
 * code has ever executed is the READ side, `mfc0 $2,$20`, and it runs last.
 *
 * What this payload should do under qemu, which is the opposite of the device
 * ------------------------------------------------------------------------
 * qemu's TCG invalidates a translation block when a store lands on code it has
 * already translated, so qemu behaves like a machine with a coherent I-cache.
 * MEASURED 2026-08-25: cells 1 and 5 -- the two with no treatment at all -- come
 * back FRESH under qemu, which is exactly the answer that would make the whole
 * experiment vacuous on the device.  A qemu run where cell 1 came back STALE
 * would mean the harness is broken, not that qemu found something.
 *
 * That is not a defect in qemu and it is not a reason to distrust the harness.
 * It is the reason the harness can only ever check control flow: an emulator
 * kinder than the device certifies exactly the bugs the device rejects, which
 * is how upstream's P9-12 was certified by its own simulator before it failed
 * on this silicon.
 *
 * And MEM-15 is why the block is poisoned before anything else happens: this
 * DRAM keeps its CONTENTS across a short power-off, so a block left by the
 * previous payload reads exactly like this one's.  The first thing this file
 * does is overwrite the region with a value no measurement can produce.  A
 * run that dies before its first cell then shows a poisoned block, which is a
 * different observation from the previous run's data.
 */

#include "rlxprobe.h"
#include "rlxdefs.h"

/* Checked against the four artefacts before it was written down -- the 4 MiB
 * dump, the decompressed stage 2, and the R0 kernel payload: zero occurrences.
 * The control for that check is `RealTek`, which occurs 3 times in decompressed
 * stage 2 and ZERO times in the dump, because the dump stores stage 2
 * LZMA-compressed -- so the strong leg is the decompressed image, not the
 * dump. */
#ifndef RLX_NONCE
#define RLX_NONCE	"9d34f1c7"
#endif
#ifndef RLX_NONCE_W
#define RLX_NONCE_W	0x9d34f1c7u
#endif

/* --- result block --------------------------------------------------------- */

#define RB_MAGIC	0x524C5831u	/* 'RLX1' */
#define RB_VERSION	0x00010001u
#define RB_POISON	0xDEADC0DEu
#define RB_HDR		8u
#define RB_ROWW		8u
#define RB_ROWS		16u		/* 12 cell rows + 4 extras */
#define RB_WORDS	(RB_HDR + RB_ROWS * RB_ROWW + 1u)
#define RB_POISON_W	160u		/* poisoned span, >= RB_WORDS */

#define UNC(a)		((volatile u32 *)((a) | KSEG1_BIT))

/* verdicts */
#define V_STALE		0x01u	/* executed OLD, memory holds NEW   */
#define V_FRESH		0x02u	/* executed NEW                      */
#define V_NOSTORE	0x03u	/* executed OLD, memory holds OLD    */
#define V_VOIDPRIME	0x04u	/* the prime call did not return OLD */
#define V_NOTVICTIM	0x05u	/* the word there was not a victim   */
#define V_WEIRD		0x06u	/* executed neither constant         */
#define V_CORRUPT	0x07u	/* the treatment DESTROYED the victim */

/* treatments */
#define T_NONE		0u
#define T_CCTL_I	1u
#define T_CCTL_DI	2u
#define T_ISC		3u

struct cellspec {
	u32 id;			/* the cell number as the write-up names it */
	u32 store_uncached;	/* store the patch through KSEG1 */
	u32 treat;
	u32 slot;		/* first victim slot; the pair is slot + gap */
};

/* Run order is risk order, not numeric order. */
static const struct cellspec CELLS[6] = {
	{ 1u, 0u, T_NONE,    0u },
	{ 5u, 1u, T_NONE,    1u },
	{ 4u, 0u, T_ISC,     2u },
	{ 2u, 0u, T_CCTL_I,  3u },
	{ 3u, 0u, T_CCTL_DI, 4u },
	{ 6u, 1u, T_CCTL_I,  5u },
};

/* Two names for one block, and keeping them separate is the point.
 *
 * `rb_ks0` is what goes in the report and what the operator types after `DW`.
 * `rb_ks1` is what every store actually goes through, and it is the KSEG1
 * alias: a result block sitting in a write-back D-cache when the watchdog fires
 * is a block `DW` will not see.  Folding the two into one variable and ORing at
 * each use would work and would leave nothing in the emitted code for
 * `tools/test-rlxprobe.sh` to check, which is why they are separate. */
static u32 rb_ks0;
static u32 rb_ks1;
static u32 rb_seq;		/* rows fully written */

/* The safe $a0 that SAFE_A0 points at was defined here until 2026-08-25.  It is
 * in report.c now: uart.S's CP0 readers gained the guard, and probe0 links
 * uart.S without linking this file.  The hazard is in rlxasm.h. */

static void rb_put(u32 word_index, u32 v)
{
	*(volatile u32 *)(rb_ks1 + word_index * 4u) = v;
}

static u32 rb_get(u32 word_index)
{
	return *(volatile u32 *)(rb_ks1 + word_index * 4u);
}

static void rb_poison(void)
{
	u32 i;

	for (i = 0; i < RB_POISON_W; i++)
		rb_put(i, RB_POISON);
}

/* The checksum is written last and covers everything before it, so a block that
 * was truncated by a fault is distinguishable from one that was completed.  A
 * sum is enough: nothing here is adversarial, the only failure being detected
 * is "it stopped". */
static void rb_seal(void)
{
	u32 i, sum = 0;

	for (i = 0; i < RB_HDR + RB_ROWS * RB_ROWW; i++)
		sum += rb_get(i);
	rb_put(RB_HDR + RB_ROWS * RB_ROWW, sum);
}

static void rb_row(u32 row, u32 tag, u32 vaddr, u32 primed, u32 executed,
		   u32 mem_before, u32 mem_after, u32 guard, u32 verdict)
{
	u32 b = RB_HDR + row * RB_ROWW;

	rb_put(b + 0u, tag);
	rb_put(b + 1u, vaddr);
	rb_put(b + 2u, primed);
	rb_put(b + 3u, executed);
	rb_put(b + 4u, mem_before);
	rb_put(b + 5u, mem_after);
	rb_put(b + 6u, guard);
	rb_put(b + 7u, verdict);

	rb_seq = row + 1u;
	rb_put(4u, rb_seq);		/* header word 4: how far it got */
}

/* --- reporting ------------------------------------------------------------ */

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

/* --- one victim ----------------------------------------------------------- */

static void run_victim(u32 row, const struct cellspec *c, u32 member, u32 vaddr)
{
	u32 tag, primed, executed, mem_before, mem_after, written, verdict, guard;

	tag = 0x43000000u | (c->id << 16) | member;	/* 'C' cc mm */
	primed = 0u;
	executed = 0u;
	written = 0u;
	mem_after = 0u;

	/* Control before treatment: is the word at this address really the
	 * victim this file assembled?  If the 1 KiB stride assumption is wrong,
	 * or the payload was linked somewhere unexpected, this is where it
	 * shows -- and it shows as a named verdict rather than as a cell that
	 * reports a number. */
	mem_before = *UNC(vaddr);
	if (mem_before != RLX_VICTIM_WORD_OLD) {
		rb_row(row, tag, vaddr, 0u, 0u, mem_before, 0u,
		       *UNC(vaddr + 4u), V_NOTVICTIM);
		return;
	}

	/* Prime: fetch the victim into the I-cache and confirm it runs. */
	/* 0xFFFFFFFF is the prime: see cache.S.  It is not the victim's OLD or
	 * NEW constant and it is not a plausible `addiu $2,$0,imm` result, so a
	 * prime call that returned WITHOUT executing the victim now says so in
	 * $v0 instead of returning whatever the previous computation left --
	 * which is what V_VOIDPRIME is for.  Free: the slot held a `nop`. */
	primed = rlx_call0_primed(vaddr, 0xFFFFFFFFu);
	if (primed != (u32)RLX_VICTIM_OLD) {
		rb_row(row, tag, vaddr, primed, 0u, mem_before, mem_before,
		       *UNC(vaddr + 4u), V_VOIDPRIME);
		return;
	}

	written = RLX_VICTIM_WORD_NEW;
	if (c->store_uncached)
		*UNC(vaddr) = written;
	else
		*(volatile u32 *)vaddr = written;

	switch (c->treat) {
	case T_CCTL_I:
		rlx_call2_uncached((u32)rlx_cctl, CCTL_IINV, 0u);
		break;
	case T_CCTL_DI:
		/* D first, then I.  c-r3k.c carries the vendor's dated reason:
		 * "we need to flush D-cache entries which might match to same
		 * address as I-cache ... when we flush I-cache." */
		rlx_call2_uncached((u32)rlx_cctl, CCTL_DFLUSH_819X, 0u);
		rlx_call2_uncached((u32)rlx_cctl, CCTL_IINV, 0u);
		break;
	case T_ISC:
		/* 16 bytes: the victim is three instructions and is 1 KiB
		 * aligned, so 16 bytes starting at it covers its line for any
		 * line size from 4 to 1024. */
		rlx_call2_uncached((u32)rlx_isc_inv, vaddr, 16u);
		break;
	case T_NONE:
	default:
		break;
	}

	/* THE GUARD, and qemu is what made it necessary.
	 *
	 * `rlx_isc_inv` byte-stores zeros across the victim.  With the caches
	 * isolated that writes cache tags, which is the whole idiom c-r3k.c
	 * uses.  ON A CORE THAT DOES NOT IMPLEMENT Status.IsC IT WRITES REAL
	 * MEMORY -- and zeroing byte 0 of the victim's second word turns
	 * 0x03E00008 (`jr ra`) into 0x00E00008, which is `jr $7`.  The payload
	 * then jumps to whatever is in $t3.  Measured under qemu-system-mips on
	 * 2026-08-25: probe1 stopped dead after cell 5, silently, with no guest
	 * exception logged.
	 *
	 * This core's own bootcode NEVER uses IsC -- only the vendor's kernel
	 * source does -- so whether it isolates here is exactly as unestablished
	 * as it is on qemu.  So the victim's tail is read back before it is
	 * called, and a treatment that destroyed it is a named verdict rather
	 * than a jump into the weeds.
	 *
	 * It is not defensive noise: V_CORRUPT is a RESULT.  It says the
	 * treatment wrote memory where it was supposed to write cache tags. */
	guard = *UNC(vaddr + 4u);
	if (guard != 0x03E00008u) {
		rb_row(row, tag, vaddr, primed, 0u, mem_before, *UNC(vaddr),
		       guard, V_CORRUPT);
		return;
	}

	executed = rlx_call0_primed(vaddr, 0xFFFFFFFFu);
	mem_after = *UNC(vaddr);

	if (executed == (u32)RLX_VICTIM_NEW)
		verdict = V_FRESH;
	else if (executed != (u32)RLX_VICTIM_OLD)
		verdict = V_WEIRD;
	else if (mem_after == written)
		verdict = V_STALE;
	else
		verdict = V_NOSTORE;

	rb_row(row, tag, vaddr, primed, executed, mem_before, mem_after,
	       guard, verdict);
}

static void report_row(u32 row)
{
	u32 b = RB_HDR + row * RB_ROWW;

	rlx_puts("rlxprobe:");
	pair("t", rb_get(b + 0u));
	pair("v", rb_get(b + 1u));
	pair("pr", rb_get(b + 2u));
	pair("ex", rb_get(b + 3u));
	pair("mb", rb_get(b + 4u));
	pair("ma", rb_get(b + 5u));
	pair("g", rb_get(b + 6u));
	pair("vd", rb_get(b + 7u));
	rlx_puts("\r\n");
}

/* --- main ----------------------------------------------------------------- */

extern u32 rlx_victims[];

void rlxprobe_main(void)
{
	u32 pc, flags, victims, i, m, row;

	rb_ks0 = (u32)RLX_RESULT_BASE;
	rb_ks1 = rb_ks0 | (u32)KSEG1_BIT;

	/* FIRST, before the banner and before any measurement: overwrite the
	 * region, because MEM-15 says the previous run's block is still there
	 * and reads exactly like this one's. */
	rb_poison();

	pc = rlx_pc();
	victims = (u32)&rlx_victims[0];

	/* Running from KSEG1 would make every cache cell vacuous, and it is one
	 * mistyped `J A0500000` away.  The payload says which window it is in
	 * rather than assuming the operator typed what the sheet says. */
	flags = 0u;
	if ((pc & KSEG_MASK) == (u32)KSEG0_BASE)
		flags |= 0x1u;
#if RLX_GEOM
	flags |= 0x2u;
#endif

	rb_put(0u, RB_MAGIC);
	rb_put(1u, RLX_NONCE_W);
	rb_put(2u, RB_VERSION);
	rb_put(3u, pc);
	rb_put(4u, 0u);
	rb_put(5u, RB_ROWS);
	rb_put(6u, flags);
	rb_put(7u, victims);

	rlx_puts("\r\n*** rlxprobe P1 " RLX_NONCE " ***\r\n");
	field("pc", pc);
	field("rb", rb_ks0);
	field("vic", victims);
	field("flags", flags);
	if (!(flags & 0x1u))
		rlx_puts("rlxprobe: NOT IN KSEG0 -- every cache cell is void\r\n");

	row = 0u;
	for (i = 0u; i < 6u; i++) {
		for (m = 0u; m < 2u; m++) {
			u32 slot = CELLS[i].slot + m * (u32)RLX_VICTIM_PAIR_GAP;
			u32 vaddr = victims + slot * (u32)RLX_VICTIM_STRIDE;

			run_victim(row, &CELLS[i], m, vaddr);
			report_row(row);
			row++;
		}
	}

	/* Extras, after every cell is already in the block. */

	/* CP0 register 20's read side.  Both sources only ever write it; this is
	 * the first read anyone has taken, and it is placed here because a fault
	 * costs only itself. */
	rb_row(row, 0x58435430u /* 'XCT0' */, 0u, 0u, rlx_mfc0_cctl(), 0u, 0u,
	       0u, 0u);
	report_row(row);
	row++;

#if RLX_GEOM
	/* ARMED.  See cache.S: while isolated, a core that does not implement
	 * IsC writes real memory over [RLX_GEOM_BASE, +1 MiB].  The runsheet
	 * reads that window before and after this runs. */
	rb_row(row, 0x58474D49u /* 'XGMI' */, (u32)RLX_GEOM_BASE, 0u,
	       rlx_r3k_size((u32)RLX_GEOM_BASE, ST0_ISC | ST0_SWC), 0u, 0u, 0u, 0u);
	report_row(row);
	row++;
	rb_row(row, 0x58474D44u /* 'XGMD' */, (u32)RLX_GEOM_BASE, 0u,
	       rlx_r3k_size((u32)RLX_GEOM_BASE, ST0_ISC), 0u, 0u, 0u, 0u);
	report_row(row);
	row++;
#endif

	rb_seal();
	field("seq", rb_seq);
	field("sum", rb_get(RB_HDR + RB_ROWS * RB_ROWW));

	/* An explicit end marker.  Without one, "the report stopped after the
	 * last row" and "the report ended after the last row" are the same
	 * observation, and P9-12 is why that distinction is not left to
	 * inference. */
	rlx_puts("rlxprobe: end\r\n");
}
