/*
 * test-spi-install-glue -- rtl819x-spi.c's R8b Gap A block, compiled on the
 * host and run end to end against a simulated SPI NOR part.
 *
 * tools/test-spi-install.sh extracts the block from the DRIVER -- from its
 * banner to its `END OF R8b GAP A` line -- into gapA.inc, and this file
 * #includes it after stubbing exactly the kernel surface the block uses.  So
 * what runs here is the driver's glue, not a re-statement of it: the parse,
 * the arm read through the write TU's getter, the one-arm-one-attempt disarm,
 * the per-operation policy checks, the commit-by-header loop, the read-back,
 * D19's erase-size probe and the /proc block.
 *
 * WHAT IS SIMULATED, AND THEREFORE WHAT A GREEN RUN DOES NOT SAY
 *  - the part: SE clears the aligned block of the part's true erase size
 *    holding its address (4 KiB, 32 KiB, 64 KiB, 128 KiB, 2/8 KiB, or a part
 *    whose SE does nothing, or clears only 128 bytes), PP ANDs bytes in (NOR
 *    semantics), a stuck cell and failing operations can be injected, and
 *    each SE / PP / RDSR poll costs simulated microseconds.  It says nothing
 *    about THIS part -- that is what D19 exists to measure.
 *  - the write TU: its arm state, its arm guard (the real
 *    rlxfw_spi_wr_chk_arm) and its getter, which can be made to fail while
 *    handing back an arm that WOULD permit, so ignoring its error shows.
 *  - the kernel: kmalloc, vmalloc, copy_from_user, the mutex, jiffies on a
 *    simulated microsecond clock (which can be frozen), msleep, the
 *    claim/release bracket, RDSR polls, and a sha256 "crypto API" over
 *    src/lib/sha256.c, an implementation independent of the kernel's
 *    sha256_generic.  The typed digests come from Python's hashlib, a third.
 *
 * Every scenario checks what the chip holds afterwards, not only what the
 * glue reports, and a refusal is checked to have left the chip BYTE-IDENTICAL
 * and the write path disarmed.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "sha256.h"

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

/* ------------------------------------------------- the kernel, stubbed */

#define __user
#define GFP_KERNEL 0
#define PAGE_SIZE 4096UL
struct file;

static int fail_kmalloc_at = -1, n_kmalloc;
static void *kmalloc(size_t n, int f)
{
	(void)f;
	if (n_kmalloc++ == fail_kmalloc_at)
		return NULL;
	return malloc(n);
}
static void kfree(const void *p) { free((void *)p); }

static int fail_vmalloc;
static void *vmalloc(unsigned long n) { return fail_vmalloc ? NULL : malloc(n); }
static void vfree(const void *p) { free((void *)p); }

static int fail_copy;
static unsigned long copy_from_user(void *d, const void *s, unsigned long n)
{
	if (fail_copy)
		return n;
	memcpy(d, s, n);
	return 0;
}

struct mutex { int held; };
static struct mutex rtl819x_spi_lock;
static int lock_errors;
static void mutex_lock(struct mutex *m)
{
	if (m->held)
		lock_errors++;		/* the kernel would deadlock here */
	m->held = 1;
}
static void mutex_unlock(struct mutex *m)
{
	if (!m->held)
		lock_errors++;
	m->held = 0;
}

/* Time: a simulated microsecond clock, and jiffies derived from it at HZ 100
 * unless frozen -- a stopped tick is a case the probe must survive. */
static unsigned long fake_us, jiffies;
static int freeze_time;
static void advance(unsigned long us)
{
	fake_us += us;
	if (!freeze_time)
		jiffies = fake_us / 10000ul;
}
static unsigned int jiffies_to_msecs(const unsigned long j)
{
	return (unsigned int)(j * 10ul);
}
static unsigned int jiffies_to_usecs(const unsigned long j)
{
	return (unsigned int)(j * 10000ul);
}
static unsigned long n_msleep, ms_slept;
static void msleep(unsigned int ms)
{
	n_msleep++;
	ms_slept += ms;
	advance(ms * 1000ul);
}
static void cond_resched(void) { }

struct crypto_shash { int unused; };
struct shash_desc {
	struct crypto_shash *tfm;
	u32 flags;
	struct sha256_ctx c;
};
static struct crypto_shash the_tfm;
static int fail_tfm;
#define IS_ERR(p)	((unsigned long)(p) >= (unsigned long)-4095)
#define PTR_ERR(p)	((long)(p))
static struct crypto_shash *crypto_alloc_shash(const char *n, u32 t, u32 m)
{
	(void)n; (void)t; (void)m;
	if (fail_tfm)
		return (struct crypto_shash *)(long)-ENOENT;
	return &the_tfm;
}
static void crypto_free_shash(struct crypto_shash *t) { (void)t; }
static struct shash_desc *rtl819x_spi_desc(struct crypto_shash *tfm)
{
	struct shash_desc *d = kmalloc(sizeof(*d), GFP_KERNEL);

	if (!d)
		return NULL;
	d->tfm = tfm;
	d->flags = 0;
	sha256_init(&d->c);
	return d;
}
static int crypto_shash_update(struct shash_desc *d, const u8 *p,
			       unsigned int n)
{
	sha256_update(&d->c, p, n);
	return 0;
}
static int crypto_shash_final(struct shash_desc *d, u8 *out)
{
	sha256_final(&d->c, out);
	return 0;
}
static int rtl819x_spi_kat_rc;

static char con[1 << 20];
static size_t ncon;
static void rlxfw_puts(const char *s)
{
	size_t n = strlen(s);

	if (ncon + n + 1 < sizeof(con)) {
		memcpy(con + ncon, s, n);
		ncon += n;
		con[ncon] = '\0';
	}
}
static void rlxfw_puts_hex(const char *s, unsigned int v)
{
	char b[96];

	snprintf(b, sizeof(b), "%s%08X\n", s, v);
	rlxfw_puts(b);
}
#define rlxfw_mark(tag)		rlxfw_puts("RLXFW-" tag "\n")
#define rlxfw_markx(tag, v)	rlxfw_puts_hex("RLXFW-" tag "=", \
					       (unsigned int)(v))

/* --------------------------------------------- the part, simulated */

#define CHIP_SZ	0x00400000u
#define RTL819X_SPI_CHUNK	4096u
#define RTL819X_SPI_PROC_BUDGET	3584
#define RTL819X_SPI_CMD_SE	0x20u
#define RTL819X_SPI_WIP_SPINS	200000u
#define POLL_US			7ul	/* one simulated RDSR poll */

static u8 chip[CHIP_SZ], orig[CHIP_SZ];
static u32 true_grain = 0x1000u;	/* 0: an SE that does nothing */
static unsigned long se_cost_us = 45000ul, n_se_done;
static int partial_first_se, partial_all_se;
static long op_count, fail_at_op = -1, n_reads, read_fail_at = -1;
static int fail_partial, forbidden_touch, page_cross, unlocked_ops;
static int claim_depth, unbracketed, claim_fail;
static u32 stuck_addr = 0xFFFFFFFFu;	/* will not ERASE: reads 0x00 */
static u32 stuck_high = 0xFFFFFFFFu;	/* will not PROGRAM: reads 0xFF */
static char op_kind[8192];
static u32 op_addr[8192];
static unsigned long n_note_erase, n_note_prog;
static unsigned long rtl819x_spi_wip_polls;

static struct { u32 erasesize; } rtl819x_spi_mtd = { 0x1000u };

struct rtl819x_spi_state { u32 sfcr, sfcr2, sfcsr; };
static int rtl819x_spi_claim(struct rtl819x_spi_state *s)
{
	(void)s;
	if (claim_fail)
		return -EIO;
	claim_depth++;
	return 0;
}
static int rtl819x_spi_release(const struct rtl819x_spi_state *s)
{
	(void)s;
	claim_depth--;
	return 0;
}
/* one RDSR poll on an idle part: WIP clear at once */
static int rtl819x_spi_wait_wip(void)
{
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	if (claim_depth <= 0)
		unbracketed++;
	rtl819x_spi_wip_polls = 1;
	advance(POLL_US);
	return 0;
}

static void log_op(char k, u32 addr)
{
	if (op_count < (long)sizeof(op_kind)) {
		op_kind[op_count] = k;
		op_addr[op_count] = addr;
	}
}

static int rtl819x_spi_se_block(u32 addr)
{
	long idx = op_count;
	u32 g = true_grain;
	u32 lo = g ? addr & ~(g - 1u) : addr;

	log_op('E', addr);
	op_count++;
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	if (lo < 0x00010000u)
		forbidden_touch++;
	if (idx == fail_at_op) {
		rtl819x_spi_wip_polls = RTL819X_SPI_WIP_SPINS;	/* the ceiling */
		advance(RTL819X_SPI_WIP_SPINS * POLL_US);
		return -ETIMEDOUT;
	}
	rtl819x_spi_wip_polls = se_cost_us / POLL_US;
	advance(se_cost_us);
	if (!g)
		return 0;			/* the opcode did nothing */
	if (partial_all_se || (partial_first_se && n_se_done == 0))
		memset(chip + lo, 0xFF, 128);	/* a part that half-erases */
	else
		memset(chip + lo, 0xFF, g);
	n_se_done++;
	if (stuck_addr >= lo && stuck_addr < lo + g)
		chip[stuck_addr] = 0x00u;	/* a cell that will not erase */
	return 0;
}

static int rtl819x_spi_pp_page(u32 addr, u32 len, const u8 *buf)
{
	long idx = op_count;
	u32 i, n = len;

	log_op('P', addr);
	op_count++;
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	if (addr < 0x00010000u)
		forbidden_touch++;
	if ((addr % 256u) + len > 256u)
		page_cross++;
	rtl819x_spi_wip_polls = 100;
	advance(700ul);
	if (idx == fail_at_op) {
		if (!fail_partial)
			return -EIO;
		n = len / 2u;		/* power fails half-way through */
	}
	for (i = 0; i < n; i++)
		chip[addr + i] &= buf[i];
	if (stuck_high >= addr && stuck_high < addr + n)
		chip[stuck_high] = 0xFFu;
	return idx == fail_at_op ? -EIO : 0;
}

static int rtl819x_spi_read_pio(u32 addr, u32 len, u8 *buf)
{
	if (n_reads++ == read_fail_at)
		return -ETIMEDOUT;
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	memcpy(buf, chip + addr, len);
	return 0;
}

static void rtl819x_spi_note_write(int erase)
{
	if (erase)
		n_note_erase++;
	else
		n_note_prog++;
}

/* ----------------------------------- the write TU, simulated */

#include "rtl819x-spi-wrpolicy.h"

static struct rlxfw_spi_wr_arm wr, getter_lie;
static unsigned long wr_n_disarm;
static int getter_fail;

static int rtl819x_spi_wr_do_arm(u32 lo, u32 hi, u32 budget)
{
	if (rlxfw_spi_wr_chk_arm(lo, hi, budget) != RLXFW_SPI_WR_OK)
		return -EINVAL;
	wr.lo = lo;
	wr.hi = hi;
	wr.budget = budget;
	wr.armed = 1;
	return 0;
}

static void rtl819x_spi_wr_do_disarm(void)
{
	wr.armed = 0;
	wr.lo = wr.hi = wr.budget = 0u;
	wr_n_disarm++;
}

/* D20's getter.  When made to fail it ALSO hands back an arm that would
 * permit (getter_lie), so a caller that ignored the error would write. */
static int rtl819x_spi_wr_get_arm(struct rlxfw_spi_wr_arm *out)
{
	if (getter_fail) {
		*out = getter_lie;
		return -EIO;
	}
	*out = wr;
	return 0;
}

/* ------------------------------------- THE DRIVER'S BLOCK, verbatim */

#include "gapA.inc"

/* ------------------------------------------------------------ cases */

static int ncase, nfail, mutate = -1;
static int seen[RLXFW_SPI_INST_R_COUNT];

static void ckb(const char *name, int holds)
{
	int idx = ncase++;
	int want = 1;

	if (idx == mutate) {
		want = 0;
		printf("MUTATED case %d: now expecting the property to FAIL\n",
		       idx);
	}
	if ((holds != 0) != want) {
		printf("  FAIL %4d %s\n", idx, name);
		nfail++;
	} else {
		printf("  ok   %4d %s\n", idx, name);
	}
}

struct blob {
	u8 *p;
	u32 n;
	char hex[65];
};

static const char *fixdir;

static struct blob load(const char *name)
{
	struct blob b;
	char path[1024], line[256];
	FILE *f;
	long sz;
	size_t nl = strlen(name);

	memset(&b, 0, sizeof(b));
	snprintf(path, sizeof(path), "%s/%s", fixdir, name);
	f = fopen(path, "rb");
	if (!f) {
		fprintf(stderr, "glue: no fixture %s\n", path);
		exit(3);
	}
	fseek(f, 0, SEEK_END);
	sz = ftell(f);
	fseek(f, 0, SEEK_SET);
	b.p = malloc((size_t)sz);
	if (!b.p || fread(b.p, 1, (size_t)sz, f) != (size_t)sz)
		exit(3);
	fclose(f);
	b.n = (u32)sz;
	/* the digest the OWNER would type: hashlib's, from the runner */
	snprintf(path, sizeof(path), "%s/digests", fixdir);
	f = fopen(path, "r");
	if (!f)
		exit(3);
	while (fgets(line, sizeof(line), f))
		if (!strncmp(line, name, nl) && line[nl] == ' ' &&
		    strlen(line + nl + 1) >= 64u) {
			memcpy(b.hex, line + nl + 1, 64);
			b.hex[64] = '\0';
		}
	fclose(f);
	if (strlen(b.hex) != 64u) {
		fprintf(stderr, "glue: no digest for %s\n", name);
		exit(3);
	}
	return b;
}

static void world(u32 grain)
{
	u32 i;

	for (i = 0; i < CHIP_SZ; i++)
		chip[i] = (u8)(i * 131u + 7u);	/* whatever was there before */
	/* the probe block and the state block read erased, as the 2026-08-16
	 * dump read 0x34C000-0x3FFFFF */
	memset(chip + 0x3E0000u, 0xFF, 0x20000u);
	memcpy(orig, chip, CHIP_SZ);
	true_grain = grain;
	se_cost_us = 45000ul;
	partial_first_se = partial_all_se = 0;
	n_se_done = 0;
	fake_us = jiffies = 0;
	freeze_time = 0;
	op_count = n_reads = 0;
	fail_at_op = read_fail_at = -1;
	fail_partial = fail_vmalloc = fail_copy = fail_tfm = getter_fail = 0;
	claim_fail = 0;
	fail_kmalloc_at = -1;
	n_kmalloc = 0;
	stuck_addr = stuck_high = 0xFFFFFFFFu;
	rtl819x_spi_kat_rc = 0;
	rtl819x_spi_mtd.erasesize = 0x1000u;
	n_msleep = ms_slept = 0;
	n_note_erase = n_note_prog = 0;
	forbidden_touch = page_cross = unlocked_ops = unbracketed = 0;
	claim_depth = 0;
	rtl819x_spi_wr_do_disarm();
	rtl819x_spi_verb_img_reset();
	ncon = 0;
	con[0] = '\0';
}

static int stage(const struct blob *b, u32 step)
{
	u32 off, n;
	int rc = 0;

	for (off = 0; off < b->n; off += n) {
		n = b->n - off < step ? b->n - off : step;
		rc = rtl819x_spi_img_write_proc(NULL, (const char *)b->p + off,
						n, NULL);
		if (rc != (int)n)
			return rc;
	}
	return rc;
}

static int install(const char *region, const char *hex, const char *tail)
{
	char line[200];

	snprintf(line, sizeof(line), "install %s sha=%s%s", region, hex, tail);
	return rtl819x_spi_verb_inst(line);
}

static int region_is(u32 base, u32 size, const struct blob *b)
{
	u32 i;

	if (b && memcmp(chip + base, b->p, b->n))
		return 0;
	for (i = b ? b->n : 0u; i < size; i++)
		if (chip[base + i] != 0xFFu)
			return 0;
	return 1;
}

static int outside_untouched(u32 base, u32 size)
{
	return !memcmp(chip, orig, base) &&
	       !memcmp(chip + base + size, orig + base + size,
		       CHIP_SZ - base - size);
}

static int count_lines(const char *pfx)
{
	const char *p = con;
	int n = 0;
	size_t l = strlen(pfx);

	while ((p = strstr(p, pfx)) != NULL) {
		if (p == con || p[-1] == '\n')
			n++;
		p += l;
	}
	return n;
}

static void note_reason(void)
{
	int r = rtl819x_spi_inst_st.r.reason;

	if (r >= 0 && r < RLXFW_SPI_INST_R_COUNT)
		seen[r]++;
}

/* A refusal: the reason, the errno, the chip byte-identical, no op issued,
 * and the write path disarmed afterwards. */
static void refused(const char *name, int rc, int reason, int err)
{
	char nm[200];
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;

	note_reason();
	snprintf(nm, sizeof(nm), "%s -> %s, rc %d, chip untouched, disarmed",
		 name, rlxfw_spi_inst_reason_name(reason), err);
	ckb(nm, rc == err && r->reason == reason && r->rc == err &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ) && wr.armed == 0 &&
	    !rtl819x_spi_lock.held);
}

static void scenario_ok(const struct blob *A, u32 grain, u32 pace)
{
	const u32 base = 0x070000u, size = 0x120000u;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	u32 np = (A->n + 255u) / 256u;
	long i, firstP = -1, lastE = -1;
	unsigned long dis0, att0, done0;
	char nm[200], tail[32], page[4096];
	int rc, plines, n;

	world(grain);
	snprintf(nm, sizeof(nm), "grain %u: staged in 4 KiB appends", grain);
	ckb(nm, stage(A, 4096u) == (int)(A->n % 4096u ? A->n % 4096u : 4096u)
	    && rtl819x_spi_img_st.len == A->n);
	ckb("arm slotA through the (simulated) write TU",
	    rtl819x_spi_wr_do_arm(base, base + size, size) == 0 && wr.armed);
	dis0 = wr_n_disarm;
	att0 = rtl819x_spi_inst_st.attempts;
	done0 = rtl819x_spi_inst_st.done;
	tail[0] = '\0';
	if (pace)
		snprintf(tail, sizeof(tail), " pace=%u", pace);
	rc = install("slotA", A->hex, tail);
	note_reason();
	snprintf(nm, sizeof(nm), "grain %u pace %u: install slotA -> OK, rc 0",
		 grain, pace);
	ckb(nm, rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    r->committed == 1 && r->phase == 'D' &&
	    rtl819x_spi_inst_st.done == done0 + 1 &&
	    rtl819x_spi_inst_st.attempts == att0 + 1);
	ckb("  the region holds the staged bytes, then 0xFF",
	    region_is(base, size, A));
	ckb("  not one byte outside the region changed",
	    outside_untouched(base, size));
	ckb("  288 erases, one program per staged page, all accounted",
	    r->n_se == 288u && r->n_pp == np && r->erased == size &&
	    r->programmed == A->n && r->ops_done == r->ops_planned &&
	    n_note_erase >= 288u);
	for (i = 0; i < op_count && i < (long)sizeof(op_kind); i++) {
		if (op_kind[i] == 'E')
			lastE = i;
		else if (firstP < 0)
			firstP = i;
	}
	ckb("  D5: every erase before every program, op 0 at the base",
	    firstP > lastE && op_kind[0] == 'E' && op_addr[0] == base);
	ckb("  D5: the last operation programs page 0 (the header)",
	    op_kind[op_count - 1] == 'P' && op_addr[op_count - 1] == base);
	ckb("  nothing below 0x010000, no page crossed, lock held throughout",
	    !forbidden_touch && !page_cross && !unlocked_ops && !lock_errors &&
	    !rtl819x_spi_lock.held);
	ckb("  ONE ARM, ONE ATTEMPT: disarmed afterwards",
	    wr.armed == 0 && wr_n_disarm == dis0 + 1);
	plines = count_lines("RLXFW-SI P ");
	ckb("  D10: 18 E lines, 18 V lines, one H line, P lines, GO and END",
	    count_lines("RLXFW-SI E ") == 18 &&
	    count_lines("RLXFW-SI V ") == 18 &&
	    count_lines("RLXFW-SI H ") == 1 && plines >= 1 &&
	    count_lines("RLXFW-SI-GO install slotA ") == 1 &&
	    count_lines("RLXFW-SI-END OK rc=0 cmp=1 ") == 1 &&
	    count_lines("RLXFW-SI-RC=00000000") == 1);
	if (pace) {
		snprintf(nm, sizeof(nm), "  D10: slept %u ms after each E and P "
			 "block, never after the header", pace);
		ckb(nm, n_msleep == (unsigned long)(18 + plines) &&
		    ms_slept == (unsigned long)pace * (18ul + plines));
		snprintf(tail, sizeof(tail), " paced=%u\n", pace);
		ckb("  D10: every step line and the result say paced",
		    count_lines("RLXFW-SI ") == 18 + plines + 1 + 18 &&
		    strstr(con, tail) != NULL &&
		    strstr(con, " paced=") != NULL);
	} else {
		ckb("  unpaced: no sleep, no line says paced",
		    n_msleep == 0 && strstr(con, "paced") == NULL);
	}
	n = rtl819x_spi_inst_proc(page, 0);
	ckb("  /proc: reason OK, cmp_ok 1, the pace declared, not truncated",
	    n > 0 && strstr(page, "inst_reason OK\n") &&
	    strstr(page, "inst_cmp_ok 1\n") &&
	    strstr(page, pace ? "inst_paced 1\n" : "inst_paced 0\n") &&
	    strstr(page, "inst_truncated 0\n") &&
	    strstr(page, "inst_region slotA\n") &&
	    strstr(page, "inst_erase_op 20\n"));
	ckb("  a second install on the spent arm is refused (UNARMED)",
	    install("slotA", A->hex, "") == -EACCES &&
	    rtl819x_spi_inst_st.r.reason == RLXFW_SPI_INST_R_UNARMED &&
	    region_is(base, size, A));
}

static void scenario_barrier(u32 grain)
{
	const u32 base = 0x030000u, size = 0x040000u;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	char nm[160];
	int rc;

	world(grain);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = rtl819x_spi_verb_inst("erase barrier");
	note_reason();
	snprintf(nm, sizeof(nm), "grain %u: erase barrier -> OK, 64 erases, "
		 "no program, all 0xFF", grain);
	ckb(nm, rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->n_se == 64u &&
	    r->n_pp == 0u && r->cmp_ok == 1 && region_is(base, size, NULL) &&
	    outside_untouched(base, size) && wr.armed == 0 &&
	    count_lines("RLXFW-SI E ") == 4 && count_lines("RLXFW-SI V ") == 4);
}

static void scenario_refusals(const struct blob *A, const struct blob *B,
			      const struct blob *R)
{
	char bad[65], page[4096];
	int rc;

	world(0x1000u);
	stage(A, 4096u);
	rc = install("slotA", A->hex, "");
	refused("not armed", rc, RLXFW_SPI_INST_R_UNARMED, -EACCES);

	rtl819x_spi_wr_do_arm(0x190000u, 0x2B0000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	refused("armed for slotB, install slotA", rc,
		RLXFW_SPI_INST_R_ARM_WINDOW, -EPERM);

	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x100000u);
	rc = install("slotA", A->hex, "");
	refused("armed slotA with a short budget", rc,
		RLXFW_SPI_INST_R_ARM_BUDGET, -ENOSPC);

	memcpy(bad, A->hex, sizeof(bad));
	bad[63] = bad[63] == '0' ? '1' : '0';
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", bad, "");
	refused("one digest digit wrong", rc, RLXFW_SPI_INST_R_SHA, -EBADMSG);
	ckb("  ... sha_checked 1, sha_ok 0",
	    rtl819x_spi_inst_st.r.sha_checked == 1 &&
	    rtl819x_spi_inst_st.r.sha_ok == 0);

	world(0x1000u);
	stage(B, 4096u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", B->hex, "");
	refused("slotB's container, its own digest, typed for slotA", rc,
		RLXFW_SPI_INST_R_HDR_FLASH_AT, -ENOEXEC);

	world(0x1000u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	refused("nothing staged", rc, RLXFW_SPI_INST_R_IMG_EMPTY, -ENODATA);

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_kat_rc = -EILSEQ;
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	refused("sha256 failed its boot KAT", rc, RLXFW_SPI_INST_R_KAT, -EPERM);
	rtl819x_spi_kat_rc = 0;

	fail_tfm = 1;
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	refused("the digest engine cannot be allocated", rc,
		RLXFW_SPI_INST_R_HASH, -EIO);
	fail_tfm = 0;

	rtl819x_spi_wr_do_arm(0x030000u, 0x070000u, 0x040000u);
	rc = install("barrier", A->hex, "");
	refused("install barrier", rc, RLXFW_SPI_INST_R_ERASE_ONLY, -EINVAL);

	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = rtl819x_spi_verb_inst("erase slotA");
	refused("erase slotA", rc, RLXFW_SPI_INST_R_NOT_ERASABLE, -EINVAL);

	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = rtl819x_spi_verb_inst("install slotA");
	refused("install slotA with no digest (a typo still disarms)", rc,
		RLXFW_SPI_INST_R_SYNTAX, -EINVAL);

	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = rtl819x_spi_verb_inst("installx");
	refused("installx", rc, RLXFW_SPI_INST_R_SYNTAX, -EINVAL);

	/* D20: the getter fails AND hands back an arm that would permit */
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	getter_fail = 1;
	getter_lie.armed = 1;
	getter_lie.lo = 0x070000u;
	getter_lie.hi = 0x190000u;
	getter_lie.budget = 0x120000u;
	rc = install("slotA", A->hex, "");
	refused("D20 getter error with a permitting copy", rc,
		RLXFW_SPI_INST_R_ARM_READ, -EPROTO);
	getter_fail = 0;

	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	n_kmalloc = 0;
	fail_kmalloc_at = 0;
	rc = install("slotA", A->hex, "");
	refused("no memory for the digest", rc, RLXFW_SPI_INST_R_HASH, -EIO);
	fail_kmalloc_at = -1;

	world(0x1000u);
	stage(R, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", R->hex, "");
	refused("rlxboot.cr6c typed for rescue", rc,
		RLXFW_SPI_INST_R_HDR_FLASH_AT, -ENOEXEC);

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", A->hex, "");
	refused("a 140 KiB container for the 64 KiB rescue", rc,
		RLXFW_SPI_INST_R_IMG_SIZE, -EFBIG);

	/* staging: overflow poisons, reset clears */
	world(0x1000u);
	{
		static u8 big[0x120000];
		struct blob X;

		X.p = big;
		X.n = sizeof(big);
		ckb("staging: exactly the capacity is accepted",
		    stage(&X, 65536u) == 65536 &&
		    rtl819x_spi_img_st.len == 0x120000u);
		ckb("staging: one byte more -> EFBIG, and the buffer poisons",
		    rtl819x_spi_img_write_proc(NULL, "x", 1, NULL) == -EFBIG &&
		    rtl819x_spi_img_st.err == RLXFW_SPI_INST_IMG_OVERFLOW);
		ckb("staging: poisoned -> EIO on the next append",
		    rtl819x_spi_img_write_proc(NULL, "x", 1, NULL) == -EIO);
		rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
		rc = install("slotA", A->hex, "");
		refused("install from a poisoned buffer", rc,
			RLXFW_SPI_INST_R_IMG_BAD, -EIO);
		rtl819x_spi_verb_img_reset();
		ckb("img reset: empty, clean, appends accepted again",
		    rtl819x_spi_img_st.len == 0u &&
		    rtl819x_spi_img_st.err == 0 &&
		    rtl819x_spi_img_write_proc(NULL, "x", 1, NULL) == 1);
		ckb("a 0-byte append is accepted and stages nothing",
		    rtl819x_spi_img_write_proc(NULL, "x", 0, NULL) == 0 &&
		    rtl819x_spi_img_st.len == 1u);
		rtl819x_spi_verb_img_reset();
		fail_vmalloc = 1;
		ckb("no memory for the buffer -> ENOMEM, poisoned",
		    rtl819x_spi_img_write_proc(NULL, "x", 1, NULL) == -ENOMEM &&
		    rtl819x_spi_img_st.err == RLXFW_SPI_INST_IMG_NOMEM);
		fail_vmalloc = 0;
		rtl819x_spi_verb_img_reset();
		fail_copy = 1;
		ckb("a faulting user buffer -> EFAULT, poisoned",
		    rtl819x_spi_img_write_proc(NULL, "x", 1, NULL) == -EFAULT &&
		    rtl819x_spi_img_st.err == RLXFW_SPI_INST_IMG_FAULT);
		fail_copy = 0;
		rtl819x_spi_verb_img_reset();
	}
	ckb("/proc near the page budget prints inst_truncated 1 only",
	    rtl819x_spi_inst_proc(page, RTL819X_SPI_PROC_BUDGET -
				  RLXFW_SPI_INST_PROC_MAX + 1) ==
	    (int)strlen("inst_truncated 1\n") &&
	    !strcmp(page, "inst_truncated 1\n"));
	ckb("lock discipline held across every refusal",
	    !lock_errors && !rtl819x_spi_lock.held);
}

/* A power cut, simulated as the engine failing at op k: the glue must stop,
 * report ENGINE with the primitive's own errno, disarm -- and the slot must
 * be one rlxboot refuses: the new header absent, the old one erased. */
static void scenario_cuts(const struct blob *A, u32 grain)
{
	const u32 base = 0x070000u, size = 0x120000u;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	u32 np = (A->n + 255u) / 256u, nops = 288u + np;
	long ks[9];
	char nm[200];
	int i, rc, partial;

	ks[0] = 0; ks[1] = 1; ks[2] = 287; ks[3] = 288; ks[4] = 289;
	ks[5] = 288 + (long)np / 2; ks[6] = (long)nops - 2;
	ks[7] = (long)nops - 1; ks[8] = (long)nops - 1;
	for (i = 0; i < 9; i++) {
		partial = (i == 8);
		world(grain);
		stage(A, 4096u);
		rtl819x_spi_wr_do_arm(base, base + size, size);
		fail_at_op = ks[i];
		fail_partial = partial;
		rc = install("slotA", A->hex, "");
		note_reason();
		snprintf(nm, sizeof(nm), "grain %u: engine stops at op %ld%s -> "
			 "ENGINE, the primitive's errno, disarmed", grain, ks[i],
			 partial ? " (header half-programmed)" : "");
		ckb(nm, r->reason == RLXFW_SPI_INST_R_ENGINE &&
		    rc == (ks[i] < 288 ? -ETIMEDOUT : -EIO) &&
		    r->ops_done == (u32)ks[i] && wr.armed == 0 &&
		    rtl819x_spi_inst_st.failed >= 1u &&
		    count_lines("RLXFW-SI-END ENGINE ") == 1);
		ckb("  the new header is NOT in place (rlxboot refuses the slot)",
		    memcmp(chip + base, A->p, 256) != 0 && r->committed == 0);
		/* (a half-programmed header carries the new magic and not the
		 * rest of the header -- the line above is its property) */
		if (ks[i] >= 1 && !partial)
			ckb("  the old header is gone: the magic reads erased",
			    chip[base] == 0xFFu && chip[base + 1] == 0xFFu &&
			    chip[base + 2] == 0xFFu && chip[base + 3] == 0xFFu);
		ckb("  nothing outside the region changed",
		    outside_untouched(base, size));
	}
}

static void scenario_late(const struct blob *A)
{
	const u32 base = 0x070000u, size = 0x120000u;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	u32 at = 5000u;
	int rc;

	/* a cell inside the staged bytes that will not erase -- at a byte the
	 * payload needs to be non-zero, or the fault would be invisible */
	while (A->p[at] == 0x00u)
		at++;
	world(0x1000u);
	stage(A, 4096u);
	stuck_addr = base + at;
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("a stuck cell in the payload -> CMP, EIO, first diff at its offset",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_CMP &&
	    r->cmp_diff == 1u && r->cmp_first == at && r->cmp_ok == 0 &&
	    r->committed == 1 && wr.armed == 0);

	/* ... and one in the 0xFF tail */
	world(0x1000u);
	stage(A, 4096u);
	stuck_addr = base + A->n + 10u;
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("a stuck cell in the tail -> CMP, first diff at len + 10",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_CMP &&
	    r->cmp_diff == 1u && r->cmp_first == A->n + 10u);

	/* the read-back itself fails, after a complete write */
	world(0x1000u);
	stage(A, 4096u);
	read_fail_at = 3;
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("the read-back fails -> ENGINE even though the write completed",
	    rc == -ETIMEDOUT && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    r->committed == 1 && r->cmp_ok == 0);

	/* the policy, consulted per operation, refuses the first op */
	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_mtd.erasesize = 0x10000u;
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("erasesize != grain: the policy refuses op 0 (GEOM), no SE issued",
	    rc == -EPERM && r->reason == RLXFW_SPI_INST_R_POLICY &&
	    r->policy == RLXFW_SPI_WR_R_GEOM && op_count == 0 &&
	    !memcmp(chip, orig, CHIP_SZ) && wr.armed == 0);
	rtl819x_spi_mtd.erasesize = 0x1000u;

	/* no memory for the read-back buffer, after a good digest */
	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	n_kmalloc = 0;
	fail_kmalloc_at = 1;		/* 0: the digest's desc, 1: the chunk */
	rc = install("slotA", A->hex, "");
	refused("no memory for the read-back buffer", rc,
		RLXFW_SPI_INST_R_NOMEM, -ENOMEM);
	fail_kmalloc_at = -1;
}

static void scenario_cr6c(const struct blob *R, const struct blob *S)
{
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	int rc;

	world(0x10000u);
	stage(R, 1000u);
	rtl819x_spi_wr_do_arm(0x010000u, 0x020000u, 0x010000u);
	rc = install("rlxboot", R->hex, " pace=30000");
	note_reason();
	/* The rescue drill's window (R8b): one 64 KiB block, so exactly two
	 * pauses -- after the erase, after the program phase -- and none after
	 * the header page or in the read-back: 60 s in which a pull leaves
	 * rlxboot without a valid header. */
	ckb("rlxboot.cr6c on rlxboot at a 64 KiB grain, pace=30000 -> OK, "
	    "two pauses, 60 s",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    region_is(0x010000u, 0x010000u, R) &&
	    outside_untouched(0x010000u, 0x010000u) &&
	    n_msleep == 2ul && ms_slept == 60000ul);

	world(0x1000u);
	stage(S, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", S->hex, "");
	note_reason();
	ckb("rescue.cr6c (a full 64 KiB) on rescue -> OK",
	    rc == 0 && r->cmp_ok == 1 && region_is(0x020000u, 0x010000u, S) &&
	    outside_untouched(0x020000u, 0x010000u));
}

/* ---------------------------------------------------- D19, the probe */

#define PB	0x3E0000u
#define PS	0x010000u

static int probe(void)
{
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	return rtl819x_spi_verb_inst("eraseprobe");
}

/* The /proc verdict line, by its own printout. */
static int verdict_line(const char *want_prefix)
{
	static char page[4096];
	char *l;

	rtl819x_spi_inst_proc(page, 0);
	l = strstr(page, "\neraseprobe se_bytes=");
	return l && !strncmp(l + 1, want_prefix, strlen(want_prefix));
}

static void scenario_probe_size(u32 g, unsigned long cost, u32 want_ops)
{
	const struct rlxfw_spi_inst_probe *p = &rtl819x_spi_probe_st;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	char nm[200], want[96];
	int rc;

	world(g);
	se_cost_us = cost;
	rc = probe();
	note_reason();
	snprintf(nm, sizeof(nm), "D19 a %u-byte part: eraseprobe -> OK, "
		 "se_bytes=%u, clean, %u clean-up SE(s)", g, g, want_ops);
	ckb(nm, rc == 0 && r->reason == RLXFW_SPI_INST_OK &&
	    p->classified && p->se_bytes == (int)g && p->clean_known &&
	    p->clean == 1 && p->clean_step == g && p->clean_ops == want_ops);
	ckb("  three markers programmed, ONE probe SE, the block 0xFF again, "
	    "nothing outside it changed",
	    r->n_pp == 3u && op_kind[3] == 'E' && op_addr[3] == PB &&
	    region_is(PB, PS, NULL) && outside_untouched(PB, PS));
	snprintf(nm, sizeof(nm), "  that SE's polls (%lu) and ticks recorded; "
		 "one program's polls; disarmed", cost / POLL_US);
	ckb(nm, p->se_issued && p->se_polls == cost / POLL_US &&
	    p->se_jiffies >= cost / 10000ul &&
	    p->se_jiffies <= cost / 10000ul + 1ul && p->pp_polls == 100u &&
	    wr.armed == 0 && !lock_errors && !rtl819x_spi_lock.held);
	ckb("  calibration: 10 ticks of idle RDSR polls, inside claim/release",
	    p->cal_ticks == 10u && p->cal_polls >= 14280u &&
	    p->cal_polls <= 14290u && !unbracketed && claim_depth == 0);
	snprintf(want, sizeof(want), "eraseprobe se_bytes=%u se_polls=%lu ", g,
		 cost / POLL_US);
	ckb("  /proc: the verdict line in its own format, clean=1",
	    verdict_line(want) && strstr(con, "RLXFW-SI-GO eraseprobe probe ") &&
	    count_lines("RLXFW-SI-PROBE se_bytes=") == 1 &&
	    count_lines("RLXFW-SI-END OK ") == 1);
}

static void scenario_probe_cases(const struct blob *A)
{
	const struct rlxfw_spi_inst_probe *p = &rtl819x_spi_probe_st;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	char line[200];
	int rc;

	/* a part whose SE does nothing: measured, and the block stays dirty */
	world(0u);
	se_cost_us = 30ul;
	rc = probe();
	note_reason();
	ckb("D19 a no-op part: se_bytes=0, markers intact, no clean-up tried, "
	    "UNCLEAN, EIO",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_PROBE_UNCLEAN &&
	    p->classified && p->se_bytes == 0 && p->m[0] == 'I' &&
	    p->m[1] == 'I' && p->m[2] == 'I' && p->clean_step == 0u &&
	    p->clean_ops == 0u && p->clean_known && p->clean == 0 &&
	    rtl819x_spi_inst_st.failed >= 1u && wr.armed == 0 &&
	    verdict_line("eraseprobe se_bytes=0 ") &&
	    strstr(con, "RLXFW-SI-PROBE se_bytes=0 m=III ") != NULL);
	/* ... and a second probe now refuses, without a stale reading */
	op_count = 0;
	memcpy(orig, chip, CHIP_SZ);
	rc = probe();
	note_reason();
	ckb("  a second eraseprobe on the dirty block: PROBE_DIRTY, ENOTEMPTY, "
	    "nothing written, se_bytes back to -1",
	    rc == -ENOTEMPTY && r->reason == RLXFW_SPI_INST_R_PROBE_DIRTY &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ) && !p->classified &&
	    p->clean_known && p->clean == 0 &&
	    verdict_line("eraseprobe se_bytes=-1 se_polls=0 se_us=0 pp_us=0 "
			 "clean=0"));

	/* (a): a block with one programmed bit is refused before any write */
	world(0x1000u);
	chip[PB + 0x7777u] = 0xFEu;
	memcpy(orig, chip, CHIP_SZ);
	rc = probe();
	note_reason();
	ckb("D19 (a) one bit programmed in the block: PROBE_DIRTY, nothing "
	    "written, refused, disarmed",
	    rc == -ENOTEMPTY && r->reason == RLXFW_SPI_INST_R_PROBE_DIRTY &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ) && wr.armed == 0 &&
	    rtl819x_spi_inst_st.refused >= 1u);

	/* a part whose FIRST SE half-erases, later ones are whole: an anomaly
	 * that the 4 KiB clean-up repairs */
	world(0x1000u);
	partial_first_se = 1;
	rc = probe();
	note_reason();
	ckb("D19 an anomalous first SE: se_bytes=-1, cleaned at 4096, "
	    "PROBE_ANOMALY, clean=1",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_PROBE_ANOMALY &&
	    p->classified && p->se_bytes == -1 && p->m[0] == 'O' &&
	    p->clean_step == 0x1000u && p->clean_ops == 16u && p->clean == 1 &&
	    region_is(PB, PS, NULL) && outside_untouched(PB, PS));

	/* every SE half-erases: anomaly, and the clean-up cannot repair it */
	world(0x1000u);
	partial_all_se = 1;
	rc = probe();
	note_reason();
	ckb("D19 every SE half-erases: anomaly AND unclean -> PROBE_UNCLEAN "
	    "outranks, clean=0",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_PROBE_UNCLEAN &&
	    p->se_bytes == -1 && p->clean_known && p->clean == 0 &&
	    verdict_line("eraseprobe se_bytes=-1 ") && outside_untouched(PB, PS));

	/* (a) catches a stuck-LOW cell before anything is written ... */
	world(0x1000u);
	chip[PB + 0x1005u] = 0x00u;
	memcpy(orig, chip, CHIP_SZ);
	rc = probe();
	note_reason();
	ckb("D19 (a) a stuck-low cell reads as not erased: PROBE_DIRTY, "
	    "nothing written",
	    rc == -ENOTEMPTY && r->reason == RLXFW_SPI_INST_R_PROBE_DIRTY &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ));
	/* ... and (b) catches a stuck-HIGH one, which reads erased at (a) and
	 * will not take the marker: it stops before the SE */
	world(0x1000u);
	stuck_high = PB + 0x1000u + 5u;
	rc = probe();
	note_reason();
	ckb("D19 (b) a marker that does not read back: PROBE_MARK, EIO, after "
	    "a write, no SE issued, clean unknown",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_PROBE_MARK &&
	    r->n_pp == 2u && !p->se_issued && !p->clean_known &&
	    rtl819x_spi_inst_st.failed >= 1u && wr.armed == 0 &&
	    verdict_line("eraseprobe se_bytes=-1 se_polls=0 se_us=0 pp_us=0 "
			 "clean=-1"));
	world(0x1000u);
	fail_at_op = 1;			/* the second marker's program */
	fail_partial = 1;		/* ... lands half a page */
	rc = probe();
	note_reason();
	ckb("D19 (b) a marker programs half a page: ENGINE after a write, no "
	    "SE issued, clean unknown (-1)",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    !p->se_issued && !p->clean_known &&
	    rtl819x_spi_inst_st.failed >= 1u && wr.armed == 0 &&
	    verdict_line("eraseprobe se_bytes=-1 se_polls=0 se_us=0 pp_us=0 "
			 "clean=-1") && outside_untouched(PB, PS));
	world(0x1000u);
	read_fail_at = 16 + 1;		/* reads 0-15 are (a), 16 marker 0's */
	rc = probe();
	note_reason();
	ckb("D19 (b) a marker read-back that cannot be read: ENGINE, clean -1",
	    rc == -ETIMEDOUT && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    !p->se_issued && !p->clean_known);

	/* (c): the one SE times out at the WIP ceiling */
	world(0x1000u);
	fail_at_op = 3;			/* 3 markers, then the SE */
	rc = probe();
	note_reason();
	ckb("D19 (c) the SE outlasts the WIP ceiling: ENGINE, ETIMEDOUT, "
	    "se_polls=200000 recorded",
	    rc == -ETIMEDOUT && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    p->se_issued && p->se_polls == RTL819X_SPI_WIP_SPINS &&
	    !p->classified && !p->clean_known);

	/* a stopped tick: the calibration is bounded and says so */
	world(0x1000u);
	freeze_time = 1;
	rc = probe();
	note_reason();
	ckb("D19 a stopped tick: no hang, cal_ticks 0 and cal_polls at the "
	    "bound, the probe still completes",
	    rc == 0 && p->cal_ticks == 0u &&
	    p->cal_polls == RTL819X_SPI_WIP_SPINS && p->se_bytes == 4096 &&
	    p->clean == 1);

	/* refusals that write nothing */
	world(0x1000u);
	rtl819x_spi_wr_do_arm(0x190000u, 0x2B0000u, 0x120000u);
	rc = rtl819x_spi_verb_inst("eraseprobe");
	refused("eraseprobe armed for slotB", rc, RLXFW_SPI_INST_R_ARM_WINDOW,
		-EPERM);
	rc = rtl819x_spi_verb_inst("eraseprobe");
	refused("eraseprobe unarmed", rc, RLXFW_SPI_INST_R_UNARMED, -EACCES);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	getter_fail = 1;
	getter_lie.armed = 1;
	getter_lie.lo = PB;
	getter_lie.hi = PB + PS;
	getter_lie.budget = PS;
	rc = rtl819x_spi_verb_inst("eraseprobe");
	refused("eraseprobe, getter error with a permitting copy", rc,
		RLXFW_SPI_INST_R_ARM_READ, -EPROTO);
	getter_fail = 0;
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("erase probe");
	refused("erase probe", rc, RLXFW_SPI_INST_R_PROBE_ONLY, -EINVAL);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	snprintf(line, sizeof(line), "install probe sha=%s", A->hex);
	rc = rtl819x_spi_verb_inst(line);
	refused("install probe", rc, RLXFW_SPI_INST_R_PROBE_ONLY, -EINVAL);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("eraseprobe 0x3e0000");
	refused("eraseprobe with an address", rc, RLXFW_SPI_INST_R_SYNTAX,
		-EINVAL);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	claim_fail = 1;
	rc = rtl819x_spi_verb_inst("eraseprobe");
	note_reason();
	ckb("D19 the calibration cannot claim the controller: ENGINE before "
	    "any write, refused, chip untouched",
	    rc == -EIO && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ));
	claim_fail = 0;

	/* the stated bounds, shown on the driver's code.  A 128 KiB part is no
	 * candidate (FW-187), and on one the probe's SE reaches the state
	 * block: a programmed bit there is shown erased, so the hazard is a
	 * reading of this test and not only a sentence. */
	world(0x20000u);
	se_cost_us = 600000ul;
	chip[0x3F0000u] = 0x7Fu;		/* one anti-rollback bit */
	memcpy(orig, chip, CHIP_SZ);
	rc = probe();
	note_reason();
	ckb("bound: a 128 KiB part reads 65536 -- and its SE erased the state "
	    "block's programmed bit at 0x3F0000",
	    rc == 0 && p->se_bytes == 65536 && orig[0x3F0000u] == 0x7Fu &&
	    chip[0x3F0000u] == 0xFFu && memcmp(chip, orig, 0x3E0000u) == 0);
	world(0x2000u);
	rc = probe();
	note_reason();
	ckb("bound: an 8 KiB part reads 32768 and cleans", rc == 0 &&
	    p->se_bytes == 32768 && p->clean == 1);
}

/* The reasons only the glue produces; the pure suite exempts them by name,
 * so this suite must produce every one of them or the exemption is
 * covering for a reason nobody drives. */
static const int glue_only[] = {
	RLXFW_SPI_INST_R_KAT, RLXFW_SPI_INST_R_HASH, RLXFW_SPI_INST_R_SHA,
	RLXFW_SPI_INST_R_NOMEM, RLXFW_SPI_INST_R_ENGINE, RLXFW_SPI_INST_R_CMP,
	RLXFW_SPI_INST_R_ARM_READ
};

int main(int argc, char **argv)
{
	struct blob A, B, R, S;
	int i;

	for (i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "--mutate") && i + 1 < argc)
			mutate = atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fixtures") && i + 1 < argc)
			fixdir = argv[++i];
		else {
			fprintf(stderr, "usage: %s --fixtures DIR [--mutate N]\n",
				argv[0]);
			return 2;
		}
	}
	if (!fixdir) {
		fprintf(stderr, "glue: --fixtures DIR is required\n");
		return 3;
	}
	A = load("slotA.rlxu");
	B = load("slotB.rlxu");
	R = load("rlxboot.cr6c");
	S = load("rescue.cr6c");
	printf("test-spi-install-glue: the driver's Gap A block on a simulated "
	       "part; slotA.rlxu %u bytes\n", A.n);

	scenario_ok(&A, 0x1000u, 0u);
	scenario_ok(&A, 0x10000u, 0u);
	scenario_ok(&A, 0x1000u, 7u);
	scenario_barrier(0x1000u);
	scenario_barrier(0x10000u);
	scenario_refusals(&A, &B, &R);
	scenario_cuts(&A, 0x1000u);
	scenario_cuts(&A, 0x10000u);
	scenario_late(&A);
	scenario_cr6c(&R, &S);
	scenario_probe_size(0x1000u, 45000ul, 16u);
	scenario_probe_size(0x8000u, 150000ul, 2u);
	scenario_probe_size(0x10000u, 300000ul, 1u);
	scenario_probe_cases(&A);

	for (i = 0; i < (int)(sizeof(glue_only) / sizeof(glue_only[0])); i++)
		if (!seen[glue_only[i]]) {
			printf("  FAIL      glue-only reason %s was never produced\n",
			       rlxfw_spi_inst_reason_name(glue_only[i]));
			nfail++;
		}
	printf("reasons produced:");
	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++)
		if (seen[i])
			printf(" %s=%d", rlxfw_spi_inst_reason_name(i), seen[i]);
	printf("\n");
	free(A.p); free(B.p); free(R.p); free(S.p);
	if (nfail) {
		printf("test-spi-install-glue: %d FAILURE(S) of %d\n", nfail,
		       ncase);
		return 1;
	}
	printf("test-spi-install-glue: all %d case(s) pass\n", ncase);
	return 0;
}
