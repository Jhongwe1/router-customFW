/*
 * test-spi-install-glue -- rtl819x-spi.c's R8b Gap A block, compiled on the
 * host and run end to end against a simulated SPI NOR part.
 *
 * tools/test-spi-install.sh extracts the block from the DRIVER -- from its
 * banner to its `END OF R8b GAP A` line -- into gapA.inc, and the driver's
 * /proc write handler, rtl819x_spi_write_proc(), into writeproc.inc; this file
 * #includes both after stubbing exactly the kernel surface they use.  So what
 * runs here is the driver's glue, not a re-statement of it: the parse, the arm
 * read through the write TU's getter, the one-arm-one-attempt disarm, the
 * per-operation policy checks, the commit-by-header loop, the read-back, D19's
 * erase-size probe, the /proc block, and since 1.1 the store's regions, the
 * running-slot fence, repeat=, the counter verb `ctr`, its scratch loop
 * `ctrloop`, and the dispatcher that hands a line to them by its prefix.
 *
 * The runner builds this file TWICE: with -DCONFIG_MTD_RTL819X_PROVISION, the
 * provisioning table (rlxboot, rescue and the barrier nameable), and without
 * it, the SHIPPED table, which names nothing below slot A.  The cases that
 * hold in one table only are each other's control.
 *
 * WHAT IS SIMULATED, AND THEREFORE WHAT A GREEN RUN DOES NOT SAY
 *  - the part: SE clears the aligned block of the part's true erase size
 *    holding its address (4 KiB, 32 KiB, 64 KiB, 128 KiB, 2/8 KiB, or a part
 *    whose SE does nothing, or clears only 128 bytes), PP ANDs bytes in (NOR
 *    semantics), a stuck cell, a bit that will not program, a program that
 *    lands and then fails, and failing operations can be injected, and each
 *    SE / PP / RDSR poll costs simulated microseconds.  It says nothing about
 *    THIS part -- that is what D19 and ctrloop exist to measure.
 *  - the write TU: its arm state, its arm guard (the real
 *    rlxfw_spi_wr_chk_arm) and its getter, which can be made to fail while
 *    handing back an arm that WOULD permit, so ignoring its error shows.
 *  - the handoff: rlxfw_boot_handoff() is a stub here, set per case to slot A
 *    or B with a version, or to none (-ENOENT, touching neither).  The real
 *    one, arch/rlx/kernel/rlxfw-boot.c's, is not compiled by this suite.
 *  - the kernel: kmalloc, vmalloc, copy_from_user, the mutex, jiffies on a
 *    simulated microsecond clock (which can be frozen), msleep, the
 *    claim/release bracket, RDSR polls, and a sha256 "crypto API" over
 *    src/lib/sha256.c, an implementation independent of the kernel's
 *    sha256_generic.  The typed digests come from Python's hashlib, a third.
 *  - the verbs OUTSIDE the block that write_proc dispatches to (probe, rdid,
 *    h601, wedge, trywrite, arm, verify, map, corrupt): stubs that record
 *    which was reached; `arm` parses its three numbers and arms the simulated
 *    TU.  The page the rest of read_proc prints before the install block is
 *    not compiled: its length enters as the `used` swept below.
 *
 * Every scenario checks what the chip holds afterwards, not only what the
 * glue reports, and a refusal is checked to have left the chip BYTE-IDENTICAL
 * and the write path disarmed.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <sys/types.h>
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

static char con[1 << 21];
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
static int fail_after_apply;		/* the failing PP lands, THEN fails */
static int claim_depth, unbracketed, claim_fail;
static u32 stuck_addr = 0xFFFFFFFFu;	/* will not ERASE: reads 0x00 */
static u32 stuck_high = 0xFFFFFFFFu;	/* will not PROGRAM: reads 0xFF */
static u32 stuck1_addr = 0xFFFFFFFFu;	/* ONE bit that will not program */
static u8 stuck1_mask;
#define OPLOG	32768
static char op_kind[OPLOG];
static u32 op_addr[OPLOG], op_len[OPLOG], op_cleared[OPLOG];
static u8 op_val[OPLOG];
static u32 min_addr_seen = 0xFFFFFFFFu;	/* the whole run's; never reset */
static unsigned long n_misaligned;	/* the whole run's; never reset */
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

static void log_op(char k, u32 addr, u32 len, u8 val)
{
	if (op_count < OPLOG) {
		op_kind[op_count] = k;
		op_addr[op_count] = addr;
		op_len[op_count] = len;
		op_val[op_count] = val;
		op_cleared[op_count] = 0u;
	}
}

static u32 popcount8(u8 v)
{
	u32 n = 0;

	while (v) {
		n += v & 1u;
		v >>= 1;
	}
	return n;
}

static int rtl819x_spi_se_block(u32 addr)
{
	long idx = op_count;
	u32 g = true_grain;
	u32 lo = g ? addr & ~(g - 1u) : addr;

	log_op('E', addr, g, 0xFFu);
	op_count++;
	if (lo < min_addr_seen)
		min_addr_seen = lo;
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
	u32 i, n = len, cleared = 0;
	u8 before;

	log_op('P', addr, len, len ? buf[0] : 0xFFu);
	op_count++;
	if (addr < min_addr_seen)
		min_addr_seen = addr;
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	if (addr < 0x00010000u)
		forbidden_touch++;
	if ((addr % 256u) + len > 256u)
		page_cross++;
	rtl819x_spi_wip_polls = 100;
	advance(700ul);
	if (idx == fail_at_op && !fail_after_apply) {
		if (!fail_partial)
			return -EIO;
		n = len / 2u;		/* power fails half-way through */
	}
	for (i = 0; i < n; i++) {
		before = chip[addr + i];
		chip[addr + i] &= buf[i];
		if (addr + i == stuck1_addr)
			chip[addr + i] |= (u8)(before & stuck1_mask);
		cleared += popcount8((u8)(before & ~chip[addr + i]));
	}
	if (stuck_high >= addr && stuck_high < addr + n)
		chip[stuck_high] = 0xFFu;
	if (idx < OPLOG)
		op_cleared[idx] = cleared;
	return idx == fail_at_op ? -EIO : 0;
}

static int rtl819x_spi_read_pio(u32 addr, u32 len, u8 *buf)
{
	/* the real one refuses an unaligned address or length (rtl819x-spi.c) */
	if ((addr | len) & 3u) {
		n_misaligned++;
		return -EINVAL;
	}
	if (n_reads++ == read_fail_at)
		return -ETIMEDOUT;
	if (!rtl819x_spi_lock.held)
		unlocked_ops++;
	memcpy(buf, chip + addr, len);
	return 0;
}

/* the driver's n_writes (outside the block), which its note_write moves */
static unsigned long rtl819x_spi_n_writes;

static void rtl819x_spi_note_write(int erase)
{
	rtl819x_spi_n_writes++;
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

/* ------------------------------------------------- the handoff, a stub */

/* rlxfw_boot_handoff()'s contract (include/linux/rlxfw-handoff.h, which the
 * block above included): 0 with *slot and *ver set when the latched handoff
 * was valid, else -ENOENT touching neither. */
static int ho_ret = -ENOENT, ho_calls;
static u32 ho_slot, ho_version;

int rlxfw_boot_handoff(u32 *slot, u32 *ver)
{
	ho_calls++;
	if (ho_ret)
		return ho_ret;
	*slot = ho_slot;
	*ver = ho_version;
	return 0;
}

/* slot 'A' or 'B' with a version, or 0 for none */
static void handoff(u32 slot, u32 ver)
{
	ho_ret = slot ? 0 : -ENOENT;
	ho_slot = slot;
	ho_version = ver;
}

/* --------- the verbs OUTSIDE the block, which the write handler calls */

static int rtl819x_spi_wedged;
static int n_outside;
static char outside_last[16];

static int outside(const char *what)
{
	n_outside++;
	snprintf(outside_last, sizeof(outside_last), "%s", what);
	return 0;
}
static int rtl819x_spi_verb_probe(void) { return outside("probe"); }
static int rtl819x_spi_verb_rdid(void) { return outside("rdid"); }
static int rtl819x_spi_verb_h601(void) { return outside("h601"); }
static int rtl819x_spi_verb_wedge(void) { return outside("wedge"); }
static int rtl819x_spi_verb_trywrite(void) { return outside("trywrite"); }
static int rtl819x_spi_verb_verify(const char *a) { (void)a; return outside("verify"); }
static int rtl819x_spi_verb_map(const char *a) { (void)a; return outside("map"); }
static int rtl819x_spi_verb_corrupt(const char *a) { (void)a; return outside("corrupt"); }

/* The driver's arm verb is above the banner, outside the block; this stand-in
 * takes the same three numbers and arms the simulated TU. */
static int rtl819x_spi_verb_arm(const char *arg)
{
	unsigned long v[3];
	char *end;
	int i;

	outside("arm");
	for (i = 0; i < 3; i++) {
		v[i] = strtoul(arg, &end, 0);
		if (end == arg)
			return -EINVAL;
		arg = end;
	}
	if (*arg)
		return -EINVAL;
	return rtl819x_spi_wr_do_arm((u32)v[0], (u32)v[1], (u32)v[2]);
}

/* ------------------------------ THE DRIVER'S WRITE HANDLER, verbatim */

#define CONFIG_MTD_RTL819X_WRITE 1
#include "writeproc.inc"

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

static void con_reset(void)
{
	ncon = 0;
	con[0] = '\0';
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
	fail_partial = fail_after_apply = 0;
	fail_vmalloc = fail_copy = fail_tfm = getter_fail = 0;
	claim_fail = 0;
	fail_kmalloc_at = -1;
	n_kmalloc = 0;
	stuck_addr = stuck_high = stuck1_addr = 0xFFFFFFFFu;
	stuck1_mask = 0u;
	rtl819x_spi_kat_rc = 0;
	rtl819x_spi_mtd.erasesize = 0x1000u;
	n_msleep = ms_slept = 0;
	n_note_erase = n_note_prog = 0;
	forbidden_touch = page_cross = unlocked_ops = unbracketed = 0;
	claim_depth = 0;
	handoff(0u, 0u);
	ho_calls = 0;
	rtl819x_spi_wr_do_disarm();
	rtl819x_spi_verb_img_reset();
	con_reset();
}

/* forget what the part was asked so far, and take its bytes as the new
 * baseline, inside one world */
static void rebase(void)
{
	memcpy(orig, chip, CHIP_SZ);
	op_count = 0;
	n_reads = 0;
	n_note_erase = n_note_prog = 0;
	con_reset();
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

static void note_ctr(void)
{
	int r = rtl819x_spi_ctr_st.reason;

	if (r >= 0 && r < RLXFW_SPI_INST_R_COUNT)
		seen[r]++;
}

static void note_loop(void)
{
	int r = rtl819x_spi_ctr_st.loop_reason;

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
	char nm[200], tail[32], page[8192];
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
	    count_lines("RLXFW-SI-RC=00000000") == 1 &&
	    count_lines("RLXFW-SI-REP ") == 0);
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

#if RLXFW_SPI_INST_PROVISION
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
#endif

static void scenario_refusals(const struct blob *A, const struct blob *B,
			      const struct blob *R)
{
	char bad[65], page[8192];
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

#if RLXFW_SPI_INST_PROVISION
	rtl819x_spi_wr_do_arm(0x030000u, 0x070000u, 0x040000u);
	rc = install("barrier", A->hex, "");
	refused("install barrier", rc, RLXFW_SPI_INST_R_ERASE_ONLY, -EINVAL);
#endif

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

#if RLXFW_SPI_INST_PROVISION
	world(0x1000u);
	stage(R, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", R->hex, "");
	refused("rlxboot.cs6c typed for rescue", rc,
		RLXFW_SPI_INST_R_HDR_FLASH_AT, -ENOEXEC);

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", A->hex, "");
	refused("a 140 KiB container for the 64 KiB rescue", rc,
		RLXFW_SPI_INST_R_IMG_SIZE, -EFBIG);
#else
	(void)R;
	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(0x3C0000u, 0x3D0000u, 0x010000u);
	rc = install("cfg0", A->hex, "");
	refused("shipped: a 140 KiB container for the 64 KiB cfg0", rc,
		RLXFW_SPI_INST_R_IMG_SIZE, -EFBIG);
#endif

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
	/* each block behind its own check, each with its own flag; 1.2: the
	 * counter's first */
	ckb("/proc with no room for either block prints the two flags only",
	    rtl819x_spi_inst_proc(page, RTL819X_SPI_PROC_BUDGET -
				  RLXFW_SPI_INST_CTR_PROC_MAX + 1) ==
	    (int)strlen("ctr_truncated 1\ninst_truncated 1\n") &&
	    !strcmp(page, "ctr_truncated 1\ninst_truncated 1\n"));
	rc = rtl819x_spi_inst_proc(page, RTL819X_SPI_PROC_BUDGET -
				   RLXFW_SPI_INST_CTR_PROC_MAX);
	ckb("/proc with room for the counter's block only prints it whole, then "
	    "inst_truncated 1",
	    rc > (int)strlen("inst_truncated 1\n") &&
	    !strncmp(page, "ctr_attempts ", 13) &&
	    rc >= (int)strlen("ctr_truncated 0\ninst_truncated 1\n") &&
	    !strcmp(page + rc - strlen("ctr_truncated 0\ninst_truncated 1\n"),
		    "ctr_truncated 0\ninst_truncated 1\n") &&
	    strstr(page, "inst_version") == NULL);
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

#if RLXFW_SPI_INST_PROVISION
static void scenario_cs6c(const struct blob *R, const struct blob *S,
			  const struct blob *LR)
{
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	int rc;

	/* FW-241: mkcr6c 1.0's bytes -- `cr6c`, sum intact -- typed with their
	 * own correct digest for their own region, refused on the magic before
	 * the first flash op. */
	world(0x10000u);
	stage(LR, 4096u);
	rtl819x_spi_wr_do_arm(0x010000u, 0x020000u, 0x010000u);
	rc = install("rlxboot", LR->hex, "");
	refused("FW-241: rlxboot.cr6c (1.0's signature) on rlxboot", rc,
		RLXFW_SPI_INST_R_HDR_MAGIC, -ENOEXEC);

	world(0x10000u);
	stage(R, 1000u);
	rtl819x_spi_wr_do_arm(0x010000u, 0x020000u, 0x010000u);
	rc = install("rlxboot", R->hex, " pace=30000");
	note_reason();
	/* The rescue drill's window (R8b): one 64 KiB block, so exactly two
	 * pauses -- after the erase, after the program phase -- and none after
	 * the header page or in the read-back: 60 s in which a pull leaves
	 * rlxboot without a valid header.  Provisioning table only: the shipped
	 * one names no rlxboot (scenario_shipped_floor is this case's control). */
	ckb("rlxboot.cs6c on rlxboot at a 64 KiB grain, pace=30000 -> OK, "
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
	ckb("rescue.cs6c (a full 64 KiB) on rescue -> OK",
	    rc == 0 && r->cmp_ok == 1 && region_is(0x020000u, 0x010000u, S) &&
	    outside_untouched(0x020000u, 0x010000u));
}
#else
/* The SHIPPED table names nothing below slot A (notes/self-update.md § 2.1).
 * Each provisioning-only region, typed with a valid payload, its own digest
 * and an arm equal to where it used to be, is REGION here -- the control for
 * scenario_cs6c's permitted install, which holds only in the other build. */
static void scenario_shipped_floor(const struct blob *R, const struct blob *S)
{
	int i, low = 0;
	int rc;

	world(0x10000u);
	stage(R, 4096u);
	rtl819x_spi_wr_do_arm(0x010000u, 0x020000u, 0x010000u);
	rc = install("rlxboot", R->hex, "");
	refused("shipped: install rlxboot is not nameable", rc,
		RLXFW_SPI_INST_R_REGION, -EINVAL);
	world(0x1000u);
	stage(S, 4096u);
	rtl819x_spi_wr_do_arm(0x020000u, 0x030000u, 0x010000u);
	rc = install("rescue", S->hex, "");
	refused("shipped: install rescue is not nameable", rc,
		RLXFW_SPI_INST_R_REGION, -EINVAL);
	world(0x1000u);
	rtl819x_spi_wr_do_arm(0x030000u, 0x070000u, 0x040000u);
	rc = rtl819x_spi_verb_inst("erase barrier");
	refused("shipped: erase barrier is not nameable", rc,
		RLXFW_SPI_INST_R_REGION, -EINVAL);
	world(0x10000u);
	rtl819x_spi_wr_do_arm(0x010000u, 0x020000u, 0x010000u);
	rc = rtl819x_spi_verb_inst("erase rlxboot");
	refused("shipped: erase rlxboot is not nameable", rc,
		RLXFW_SPI_INST_R_REGION, -EINVAL);
	for (i = 0; i < RLXFW_SPI_INST_NREGIONS; i++)
		if (rlxfw_spi_inst_regions[i].base < 0x070000u)
			low++;
	ckb("shipped: the table the glue reads has 5 regions, none below "
	    "0x070000", RLXFW_SPI_INST_NREGIONS == 5 && low == 0);
}
#endif

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
	static char page[8192];
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

/* ------------------------------------------- 1.1: errno rows, the store */

/* Every reason has its own errno row: a reason added without one would fall
 * to rtl819x_spi_inst_err()'s -EPROTO, which is also ARM_READ's. */
static void scenario_errno(void)
{
	int i, missing = 0;

	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++)
		if (rtl819x_spi_inst_errno[i] == 0 || rtl819x_spi_inst_err(i) >= 0)
			missing++;
	ckb("every reason has an errno row of its own (none falls to the "
	    "-EPROTO default)", missing == 0);
	ckb("  1.1's rows: HDR_SEQ ENOEXEC, REPEAT_ONLY_SLOT EINVAL, "
	    "RUNNING_SLOT EBUSY, CTR_ABOVE and CTR_BELOW ERANGE, CTR_HANDOFF "
	    "EPERM, CTR_MALFORMED EILSEQ, CTR_CMP EIO",
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_HDR_SEQ) == -ENOEXEC &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_REPEAT_ONLY_SLOT) == -EINVAL &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_RUNNING_SLOT) == -EBUSY &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_CTR_ABOVE) == -ERANGE &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_CTR_HANDOFF) == -EPERM &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_CTR_BELOW) == -ERANGE &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_CTR_MALFORMED) == -EILSEQ &&
	    rtl819x_spi_inst_err(RLXFW_SPI_INST_R_CTR_CMP) == -EIO);
}

#define C0B	0x3C0000u
#define C1B	0x3D0000u
#define CSZ	0x010000u

/* P6r-10: the store's regions through the install path, with slot images
 * src/cfgstore's host build PRODUCED (and two the runner derived from them). */
static void scenario_cfg(const struct blob *C1, const struct blob *C2,
			 const struct blob *C0, const struct blob *CL,
			 const struct blob *R)
{
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	char line[200];
	int rc;

	world(0x1000u);
	stage(C1, 4096u);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	rc = install("cfg0", C1->hex, "");
	note_reason();
	ckb("install cfg0, cfgstore's seq-1 slot image, under cfg0's arm -> OK, "
	    "the region holds it then 0xFF, the header checked",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    r->hdr_checked && r->hdr_ok && region_is(C0B, CSZ, C1) &&
	    outside_untouched(C0B, CSZ) && wr.armed == 0);
	ckb("  16 erases and 16 programs, header last: n_writes +32 (§ 3.3)",
	    r->n_se == 16u && r->n_pp == 16u && r->ops_planned == 32u &&
	    n_note_erase == 16u && n_note_prog == 16u && op_count == 32 &&
	    op_kind[31] == 'P' && op_addr[31] == C0B &&
	    strstr(con, "RLXFW-SI-GO install cfg0 len=4096 pace=0\n") != NULL);

	world(0x1000u);
	stage(C2, 4096u);
	rtl819x_spi_wr_do_arm(C1B, C1B + CSZ, CSZ);
	rc = install("cfg1", C2->hex, "");
	note_reason();
	ckb("install cfg1, the seq-2 slot image, under cfg1's arm -> OK",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    region_is(C1B, CSZ, C2) && outside_untouched(C1B, CSZ));
	/* and erase it again: the deterministic way to make a slot invalid */
	rebase();
	rtl819x_spi_wr_do_arm(C1B, C1B + CSZ, CSZ);
	rc = rtl819x_spi_verb_inst("erase cfg1");
	note_reason();
	ckb("erase cfg1 (holding a record) under cfg1's arm -> OK: 16 erases, "
	    "no program, the region all 0xFF, n_writes +16",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->n_se == 16u &&
	    r->n_pp == 0u && r->cmp_ok == 1 && region_is(C1B, CSZ, NULL) &&
	    outside_untouched(C1B, CSZ) && n_note_erase == 16u &&
	    n_note_prog == 0u && wr.armed == 0);

	world(0x1000u);
	stage(C1, 4096u);
	rtl819x_spi_wr_do_arm(C1B, C1B + CSZ, CSZ);
	rc = install("cfg0", C1->hex, "");
	refused("install cfg0 under cfg1's arm", rc,
		RLXFW_SPI_INST_R_ARM_WINDOW, -EPERM);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("cfg1", C1->hex, "");
	refused("install cfg1 under slotA's arm", rc,
		RLXFW_SPI_INST_R_ARM_WINDOW, -EPERM);
	rtl819x_spi_wr_do_arm(C1B, C1B + CSZ, CSZ);
	rc = rtl819x_spi_verb_inst("erase cfg0");
	refused("erase cfg0 under cfg1's arm", rc, RLXFW_SPI_INST_R_ARM_WINDOW,
		-EPERM);
	rc = rtl819x_spi_verb_inst("erase cfg0");
	refused("erase cfg0 unarmed", rc, RLXFW_SPI_INST_R_UNARMED, -EACCES);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	snprintf(line, sizeof(line), "install cfg0 sha=%s repeat=2", C1->hex);
	rc = rtl819x_spi_verb_inst(line);
	refused("install cfg0 ... repeat=2 (slots only)", rc,
		RLXFW_SPI_INST_R_REPEAT_ONLY_SLOT, -EINVAL);

	/* the wrong kind of payload, each with its own correct digest */
	world(0x1000u);
	stage(R, 4096u);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	rc = install("cfg0", R->hex, "");
	refused("a cs6c image, its own digest, into cfg0", rc,
		RLXFW_SPI_INST_R_HDR_MAGIC, -ENOEXEC);
	world(0x1000u);
	stage(C0, 4096u);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	rc = install("cfg0", C0->hex, "");
	refused("a slot image with seq 0 into cfg0", rc,
		RLXFW_SPI_INST_R_HDR_SEQ, -ENOEXEC);
	world(0x1000u);
	stage(CL, 4096u);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	rc = install("cfg0", CL->hex, "");
	refused("a 4,097-byte slot image into cfg0", rc,
		RLXFW_SPI_INST_R_HDR_LEN, -ENOEXEC);
	world(0x1000u);
	stage(C1, 4096u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", C1->hex, "");
	refused("a store record, its own digest, into slotA", rc,
		RLXFW_SPI_INST_R_HDR_MAGIC, -ENOEXEC);
}

/* --------------------------------------------- 1.1: the running-slot fence */

static void scenario_fence(const struct blob *A, const struct blob *B,
			   const struct blob *C1)
{
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	int rc;

	world(0x1000u);
	stage(A, 4096u);
	handoff('A', 5u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	refused("handoff names A: install slotA", rc,
		RLXFW_SPI_INST_R_RUNNING_SLOT, -EBUSY);
	ckb("  ... refused before its GO line, the latch read",
	    count_lines("RLXFW-SI-GO ") == 0 && ho_calls >= 1 &&
	    count_lines("RLXFW-SI-END RUNNING_SLOT ") == 1);
	rc = install("slotA", A->hex, "");
	refused("handoff names A: install slotA unarmed -- the fence is "
		"checked before the arm", rc, RLXFW_SPI_INST_R_RUNNING_SLOT,
		-EBUSY);

	world(0x1000u);
	stage(A, 4096u);
	handoff('B', 6u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("handoff names B: install slotA -> OK (the update's own case)",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    region_is(0x070000u, 0x120000u, A));

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(0x070000u, 0x190000u, 0x120000u);
	rc = install("slotA", A->hex, "");
	note_reason();
	ckb("no handoff (a RAM boot, the bench): install slotA -> OK",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK &&
	    region_is(0x070000u, 0x120000u, A) && ho_calls >= 1);

	world(0x1000u);
	stage(B, 4096u);
	handoff('B', 6u);
	rtl819x_spi_wr_do_arm(0x190000u, 0x2B0000u, 0x120000u);
	rc = install("slotB", B->hex, "");
	refused("handoff names B: install slotB", rc,
		RLXFW_SPI_INST_R_RUNNING_SLOT, -EBUSY);

	world(0x1000u);
	stage(B, 4096u);
	handoff('A', 5u);
	rtl819x_spi_wr_do_arm(0x190000u, 0x2B0000u, 0x120000u);
	rc = install("slotB", B->hex, "");
	note_reason();
	ckb("handoff names A: install slotB -> OK",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK &&
	    region_is(0x190000u, 0x120000u, B));

	world(0x1000u);
	stage(C1, 4096u);
	handoff('A', 5u);
	rtl819x_spi_wr_do_arm(C0B, C0B + CSZ, CSZ);
	rc = install("cfg0", C1->hex, "");
	note_reason();
	ckb("handoff names A: install cfg0 -> OK (the store is not a slot)",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK &&
	    region_is(C0B, CSZ, C1));

	world(0x1000u);
	handoff('B', 6u);
	rc = probe();
	note_reason();
	ckb("handoff names B: eraseprobe -> OK (the probe block is not fenced)",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK);
}

/* ---------------------------------------------------- 1.1: repeat=<k> */

static void scenario_repeat(const struct blob *A)
{
	const u32 base = 0x070000u, size = 0x120000u;
	const struct rlxfw_spi_inst_res *r = &rtl819x_spi_inst_st.r;
	const long np = (long)((A->n + 255u) / 256u), per = 288 + np;
	char line[200];
	long i, k, j;
	int rc, order = 1;

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, " repeat=3");
	note_reason();
	ckb("repeat=3: install slotA -> OK, the region holds the bytes, "
	    "disarmed",
	    rc == 0 && r->reason == RLXFW_SPI_INST_OK && r->cmp_ok == 1 &&
	    r->committed == 1 && region_is(base, size, A) &&
	    outside_untouched(base, size) && wr.armed == 0);
	ckb("  the part saw the whole plan three times: n_writes = 3 x (288 + "
	    "ceil(len/256))",
	    op_count == 3 * per && n_note_erase == 3ul * 288ul &&
	    n_note_prog == 3ul * (unsigned long)np && r->n_se == 864u &&
	    r->n_pp == 3u * (u32)np && r->ops_done == 3u * (u32)per &&
	    r->ops_planned == 3u * (u32)per && r->cmp_bytes == 3u * size);
	for (k = 0; k < 3; k++)
		for (i = 0; i < per; i++) {
			j = k * per + i;
			if (j >= OPLOG || (i < 288) != (op_kind[j] == 'E'))
				order = 0;
		}
	ckb("  each repetition erases all, then programs, op 0 at the base, "
	    "the header last",
	    order && op_addr[0] == base && op_addr[per] == base &&
	    op_addr[2 * per] == base && op_addr[per - 1] == base &&
	    op_addr[2 * per - 1] == base && op_addr[3 * per - 1] == base);
	ckb("  console: one GO, RLXFW-SI-REP 2/3 and 3/3 between, 54 E, 54 V, "
	    "3 H lines, one END OK",
	    count_lines("RLXFW-SI-GO install slotA ") == 1 &&
	    count_lines("RLXFW-SI-REP ") == 2 &&
	    strstr(con, "\nRLXFW-SI-REP 2/3\n") != NULL &&
	    strstr(con, "\nRLXFW-SI-REP 3/3\n") != NULL &&
	    count_lines("RLXFW-SI E ") == 54 &&
	    count_lines("RLXFW-SI V ") == 54 &&
	    count_lines("RLXFW-SI H ") == 3 &&
	    count_lines("RLXFW-SI-END OK rc=0 cmp=1 ") == 1);

	/* a cut inside the second repetition's erase phase */
	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	fail_at_op = per + 100;
	rc = install("slotA", A->hex, " repeat=2");
	note_reason();
	ckb("repeat=2 cut at op 100 of the second repetition -> ENGINE, the "
	    "first repetition done, the header gone again",
	    rc == -ETIMEDOUT && r->reason == RLXFW_SPI_INST_R_ENGINE &&
	    r->ops_done == (u32)(per + 100) && r->committed == 0 &&
	    chip[base] == 0xFFu && strstr(con, "\nRLXFW-SI-REP 2/2\n") &&
	    count_lines("RLXFW-SI-END ENGINE ") == 1 && wr.armed == 0);

	world(0x1000u);
	stage(A, 4096u);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	snprintf(line, sizeof(line), "install slotA sha=%s repeat=5 pace=100",
		 A->hex);
	rc = rtl819x_spi_verb_inst(line);
	refused("repeat=5 pace=100 (never both)", rc, RLXFW_SPI_INST_R_SYNTAX,
		-EINVAL);
	rtl819x_spi_wr_do_arm(base, base + size, size);
	rc = install("slotA", A->hex, " repeat=9");
	refused("repeat=9", rc, RLXFW_SPI_INST_R_SYNTAX, -EINVAL);
}

/* ---------------------------------------------- 1.1: the counter, `ctr` */

#define ST	0x3F0000u

static u32 bm_value(u32 base, int *mal)
{
	return rlxfw_spi_inst_ctr_decode(chip + base, mal);
}

/* the state block's bitmap with exactly [0, c) zero, as the new baseline */
static void bm_put(u32 c)
{
	u32 b;

	memset(chip + ST, 0xFF, 512u);
	for (b = 0; b < c; b++)
		chip[ST + (b >> 3)] &= (u8)~(0x80u >> (b & 7u));
	memcpy(orig, chip, CHIP_SZ);
}

static int clz8(u8 v)
{
	int n = 0;

	while (n < 8 && !(v & (0x80u >> n)))
		n++;
	return n;
}

/* The logged ops from `from` on: each a ONE-byte page program inside the
 * 512-byte bitmap at lo, and the bit each one's value clears ascending. */
static int ops_pp1_ascending(long from, u32 lo)
{
	long i;
	int b, prev = -1;

	if (op_count > OPLOG)
		return 0;
	for (i = from; i < op_count; i++) {
		if (op_kind[i] != 'P' || op_len[i] != 1u || op_addr[i] < lo ||
		    op_addr[i] >= lo + 512u)
			return 0;
		b = (int)((op_addr[i] - lo) * 8u) + clz8(op_val[i]) - 1;
		if (b <= prev)
			return 0;
		prev = b;
	}
	return 1;
}

/* ... and each of them took exactly one bit from 1 to 0 on the part */
static int ops_each_cleared_one(long from)
{
	long i;

	if (op_count > OPLOG)
		return 0;
	for (i = from; i < op_count; i++)
		if (op_cleared[i] != 1u)
			return 0;
	return 1;
}

/* A counter refusal: its reason and errno, nothing sent, the chip
 * byte-identical, refused +1, no GO line, one END line, disarmed. */
static void ctr_refuses(const char *name, const char *line, int reason,
			int err)
{
	const struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	u32 ref0 = c->refused, at0 = c->attempts;
	char nm[200];
	int rc;

	con_reset();
	rc = rtl819x_spi_verb_inst(line);
	note_ctr();
	snprintf(nm, sizeof(nm), "%s -> %s, rc %d, nothing sent, disarmed",
		 name, rlxfw_spi_inst_reason_name(reason), err);
	ckb(nm, rc == err && c->reason == reason && c->refused == ref0 + 1 &&
	    c->attempts == at0 + 1 && c->pp == 0u && op_count == 0 &&
	    !memcmp(chip, orig, CHIP_SZ) && wr.armed == 0 &&
	    !rtl819x_spi_lock.held && count_lines("RLXFW-SC-GO ") == 0 &&
	    count_lines("RLXFW-SC-END ") == 1);
}

static void scenario_ctr(void)
{
	const struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	u32 at0, inst0, f0, k, v;
	int rc, mal, landed, all = 1;

	/* W3: 0 -> 6, the round's first advance, with an arm for ANOTHER
	 * region typed before it -- which the verb must neither use nor
	 * leave behind */
	world(0x1000u);
	handoff('B', 6u);
	rtl819x_spi_wr_do_arm(0x190000u, 0x2B0000u, 0x120000u);
	at0 = c->attempts;
	rc = rtl819x_spi_verb_inst("ctr 6");
	note_ctr();
	ckb("ctr 6 on an erased counter, handoff B ver 6 -> OK, rc 0: cur 0, "
	    "new 6, read 6, pp 6",
	    rc == 0 && c->reason == RLXFW_SPI_INST_OK && c->ran && c->cur == 0u &&
	    c->newv == 6u && c->read == 6u && c->pp == 6u && !c->malformed &&
	    c->attempts == at0 + 1);
	ckb("  six ONE-byte page programs at 0x3F0000, values 7F 3F 1F 0F 07 "
	    "03, ascending, each clearing one bit; no erase",
	    op_count == 6 && ops_pp1_ascending(0, ST) &&
	    ops_each_cleared_one(0) && op_addr[0] == ST && op_addr[5] == ST &&
	    op_val[0] == 0x7Fu && op_val[1] == 0x3Fu && op_val[2] == 0x1Fu &&
	    op_val[3] == 0x0Fu && op_val[4] == 0x07u && op_val[5] == 0x03u &&
	    n_note_erase == 0ul);
	ckb("  n_writes moved by the bits cleared (6); the bitmap decodes to "
	    "6, well-formed; nothing outside it changed",
	    n_note_prog == 6ul && bm_value(ST, &mal) == 6u && !mal &&
	    outside_untouched(ST, 512u));
	ckb("  no arm used and none left (the slotB arm is gone), the lock "
	    "held throughout and released",
	    wr.armed == 0 && !rtl819x_spi_lock.held && !unlocked_ops &&
	    !lock_errors);
	ckb("  console: RLXFW-SC-GO cur=0 new=6, then RLXFW-SC-END OK cur=0 "
	    "new=6 read=6 pp=6 ms=<t>",
	    strstr(con, "RLXFW-SC-GO cur=0 new=6\n") != NULL &&
	    strstr(con, "RLXFW-SC-END OK cur=0 new=6 read=6 pp=6 ms=") != NULL &&
	    count_lines("RLXFW-SC-") == 2);

	/* SAME sends nothing */
	rebase();
	rc = rtl819x_spi_verb_inst("ctr 6");
	note_ctr();
	ckb("ctr 6 again: SAME -- OK, pp 0, read 6, nothing sent, no GO line",
	    rc == 0 && c->reason == RLXFW_SPI_INST_OK && c->pp == 0u &&
	    c->cur == 6u && c->read == 6u && op_count == 0 &&
	    !memcmp(chip, orig, CHIP_SZ) && count_lines("RLXFW-SC-GO ") == 0 &&
	    strstr(con, "RLXFW-SC-END OK cur=6 new=6 read=6 pp=0 ms=") != NULL);

	/* W7: 6 -> 7 */
	handoff('A', 7u);
	rebase();
	rc = rtl819x_spi_verb_inst("ctr 7");
	note_ctr();
	ckb("ctr 7 on 6, handoff A ver 7 -> OK: one program, value 01 at "
	    "0x3F0000, n_writes +1",
	    rc == 0 && c->reason == RLXFW_SPI_INST_OK && c->pp == 1u &&
	    op_count == 1 && op_kind[0] == 'P' && op_addr[0] == ST &&
	    op_len[0] == 1u && op_val[0] == 0x01u && n_note_prog == 1ul &&
	    bm_value(ST, &mal) == 7u && !mal);

	/* the tie */
	world(0x1000u);
	ctr_refuses("no handoff (a RAM boot): ctr 6", "ctr 6",
		    RLXFW_SPI_INST_R_CTR_HANDOFF, -EPERM);
	ckb("  ... the END line says so: CTR_HANDOFF cur=0 new=6 read=0 pp=0",
	    strstr(con, "RLXFW-SC-END CTR_HANDOFF cur=0 new=6 read=0 pp=0 "
		   "ms=") != NULL && ho_calls >= 1);
	handoff('A', 5u);
	ctr_refuses("handoff ver 5: ctr 6", "ctr 6",
		    RLXFW_SPI_INST_R_CTR_HANDOFF, -EPERM);
	handoff('B', 7u);
	ctr_refuses("handoff ver 7: ctr 6", "ctr 6",
		    RLXFW_SPI_INST_R_CTR_HANDOFF, -EPERM);

	/* the bitmap as read */
	world(0x1000u);
	bm_put(6u);
	handoff('A', 5u);
	ctr_refuses("ctr 5 on a counter at 6", "ctr 5",
		    RLXFW_SPI_INST_R_CTR_BELOW, -ERANGE);
	world(0x1000u);
	bm_put(6u);
	chip[ST + (100u >> 3)] &= (u8)~(0x80u >> (100u & 7u));
	memcpy(orig, chip, CHIP_SZ);
	handoff('A', 7u);
	ctr_refuses("ctr 7 on 6 with a stray zero at bit 100", "ctr 7",
		    RLXFW_SPI_INST_R_CTR_MALFORMED, -EILSEQ);
	ckb("  ... it read malformed, value the total zero count (7)",
	    c->malformed == 1 && c->cur == 7u);
	handoff('A', 101u);
	rc = rtl819x_spi_verb_inst("ctr 101");
	note_ctr();
	ckb("ctr 101 on the same bitmap (every zero below it) -> OK: repaired "
	    "with 94 one-bit programs, well-formed at 101",
	    rc == 0 && c->reason == RLXFW_SPI_INST_OK && c->pp == 94u &&
	    op_count == 94 && ops_pp1_ascending(0, ST) &&
	    ops_each_cleared_one(0) && bm_value(ST, &mal) == 101u && !mal &&
	    outside_untouched(ST, 512u));

	/* the parser's, before the tie and before any read */
	world(0x1000u);
	handoff('A', 4097u);
	ctr_refuses("ctr 4097 with a handoff of 4097", "ctr 4097",
		    RLXFW_SPI_INST_R_CTR_ABOVE, -ERANGE);
	handoff('A', 6u);
	ctr_refuses("ctr 0", "ctr 0", RLXFW_SPI_INST_R_SYNTAX, -EINVAL);
	ctr_refuses("ctr 06", "ctr 06", RLXFW_SPI_INST_R_SYNTAX, -EINVAL);
	ctr_refuses("ctr 6 with a trailing space", "ctr 6 ",
		    RLXFW_SPI_INST_R_SYNTAX, -EINVAL);
	ctr_refuses("ctr with no value", "ctr", RLXFW_SPI_INST_R_SYNTAX,
		    -EINVAL);
	ctr_refuses("ctr 0x10", "ctr 0x10", RLXFW_SPI_INST_R_SYNTAX, -EINVAL);
	ckb("  ... and no read of the bitmap for any of them", n_reads == 0);
	at0 = c->attempts;
	inst0 = rtl819x_spi_inst_st.attempts;
	rc = rtl819x_spi_verb_inst("ctrl 30");
	note_reason();
	ckb("ctrl 30 is not ctr: the install path's SYNTAX, ctr_attempts "
	    "unchanged",
	    rc == -EINVAL && c->attempts == at0 &&
	    rtl819x_spi_inst_st.attempts == inst0 + 1 &&
	    rtl819x_spi_inst_st.r.reason == RLXFW_SPI_INST_R_SYNTAX &&
	    op_count == 0 && wr.armed == 0);

	/* the whole bitmap, the T9 ceiling, only to the booted version */
	world(0x1000u);
	handoff('B', 4096u);
	rc = rtl819x_spi_verb_inst("ctr 4096");
	note_ctr();
	ckb("ctr 4096, handoff ver 4096 -> OK: 4,096 one-byte programs over "
	    "[0x3F0000, 0x3F0200), the bitmap all zero",
	    rc == 0 && c->reason == RLXFW_SPI_INST_OK && c->pp == 4096u &&
	    op_count == 4096 && ops_pp1_ascending(0, ST) &&
	    ops_each_cleared_one(0) && bm_value(ST, &mal) == 4096u && !mal &&
	    n_note_prog == 4096ul && outside_untouched(ST, 512u));

	/* J: a bit that will not program */
	world(0x1000u);
	handoff('A', 6u);
	stuck1_addr = ST;
	stuck1_mask = 0x04u;		/* bit 5 */
	f0 = c->failed;
	rc = rtl819x_spi_verb_inst("ctr 6");
	note_ctr();
	ckb("ctr 6 with bit 5 stuck at 1 -> CTR_CMP, EIO, a FAILURE (after "
	    "the writes), read 5, pp 6, n_writes +6",
	    rc == -EIO && c->reason == RLXFW_SPI_INST_R_CTR_CMP &&
	    c->failed == f0 + 1 && c->read == 5u && c->pp == 6u &&
	    n_note_prog == 6ul && wr.armed == 0 &&
	    strstr(con, "RLXFW-SC-END CTR_CMP cur=0 new=6 read=5 pp=6 ms=") !=
	    NULL);

	/* I: a cut inside op k -- its bit landed or not -- then a retry */
	for (landed = 0; landed <= 1; landed++)
		for (k = 0; k < 6u; k++) {
			world(0x1000u);
			handoff('A', 6u);
			fail_at_op = (long)k;
			fail_after_apply = landed;
			rc = rtl819x_spi_verb_inst("ctr 6");
			note_ctr();
			v = bm_value(ST, &mal);
			if (rc != -EIO || c->reason != RLXFW_SPI_INST_R_ENGINE ||
			    c->pp != k || n_note_prog != (unsigned long)k ||
			    v != k + (u32)landed || mal || v > 6u ||
			    wr.armed != 0 || !outside_untouched(ST, 512u))
				all = 0;
			fail_at_op = -1;
			fail_after_apply = 0;
			rebase();
			rc = rtl819x_spi_verb_inst("ctr 6");
			note_ctr();
			if (rc != 0 || c->pp != 6u - v ||
			    bm_value(ST, &mal) != 6u || mal ||
			    !ops_pp1_ascending(0, ST))
				all = 0;
		}
	ckb("I a cut inside op k of 0 -> 6 (k = 0..5, the bit landed or not): "
	    "ENGINE, the bitmap reads k or k+1, well-formed, from the old to "
	    "the new; ctr 6 again finishes it", all);

	/* the reads, and memory */
	world(0x1000u);
	handoff('A', 6u);
	read_fail_at = 0;
	ctr_refuses("ctr 6, step 4's read fails", "ctr 6",
		    RLXFW_SPI_INST_R_ENGINE, -ETIMEDOUT);
	world(0x1000u);
	handoff('A', 6u);
	read_fail_at = 1;
	f0 = c->failed;
	rc = rtl819x_spi_verb_inst("ctr 6");
	note_ctr();
	ckb("ctr 6, step 7's read-back fails -> ENGINE, a FAILURE after six "
	    "programs",
	    rc == -ETIMEDOUT && c->reason == RLXFW_SPI_INST_R_ENGINE &&
	    c->failed == f0 + 1 && c->pp == 6u && wr.armed == 0);
	world(0x1000u);
	handoff('A', 6u);
	n_kmalloc = 0;
	fail_kmalloc_at = 0;
	ctr_refuses("ctr 6, no memory for the bitmap", "ctr 6",
		    RLXFW_SPI_INST_R_NOMEM, -ENOMEM);
	fail_kmalloc_at = -1;
	ckb("the counter's lock discipline held",
	    !lock_errors && !rtl819x_spi_lock.held && !unlocked_ops);
}

/* ---------------------------------------- 1.1: the scratch loop, ctrloop */

static void loop_refuses(const char *name, const char *line, int reason,
			 int err)
{
	const struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	char nm[200];
	int rc;

	con_reset();
	rc = rtl819x_spi_verb_inst(line);
	note_loop();
	snprintf(nm, sizeof(nm), "%s -> %s, rc %d, nothing sent, disarmed",
		 name, rlxfw_spi_inst_reason_name(reason), err);
	ckb(nm, rc == err && c->loop_reason == reason && c->loop_ops == 0u &&
	    op_count == 0 && !memcmp(chip, orig, CHIP_SZ) && wr.armed == 0 &&
	    !rtl819x_spi_lock.held && count_lines("RLXFW-SL ") == 0);
}

/* A field of the install path's /proc blocks, as read_proc would print them
 * (prefix 0): "<key> <number>\n", or LONG_MIN when the key is not there. */
static long procnum(const char *key)
{
	static char page[8192];
	char pat[64];
	const char *p;

	rtl819x_spi_inst_proc(page, 0);
	snprintf(pat, sizeof(pat), "%s ", key);
	for (p = page; (p = strstr(p, pat)) != NULL; p++)
		if (p == page || p[-1] == '\n')
			return strtol(p + strlen(pat), NULL, 10);
	return LONG_MIN;
}

/* the last console line that starts with pfx, or NULL */
static const char *last_line(const char *pfx)
{
	const char *p = con, *last = NULL;
	size_t l = strlen(pfx);

	while ((p = strstr(p, pfx)) != NULL) {
		if (p == con || p[-1] == '\n')
			last = p;
		p += l;
	}
	return last;
}

/* the number on the last "RLXFW-SL p=<pass> bit=" line, or -1 */
static long last_bit_line(u32 pass)
{
	char pfx[48];
	const char *p = con, *last = NULL;
	size_t l;

	snprintf(pfx, sizeof(pfx), "RLXFW-SL p=%u bit=", pass);
	l = strlen(pfx);
	while ((p = strstr(p, pfx)) != NULL) {
		last = p;
		p += l;
	}
	return last ? strtol(last + l, NULL, 10) : -1;
}

static void scenario_ctrloop(void)
{
	const struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	char want[160];
	long i, last, shows0;
	u32 v;
	int rc, mal, ok, landed;

	world(0x1000u);
	loop_refuses("ctrloop 2 unarmed", "ctrloop 2",
		     RLXFW_SPI_INST_R_UNARMED, -EACCES);
	rtl819x_spi_wr_do_arm(C1B, C1B + CSZ, CSZ);
	loop_refuses("ctrloop 2 under cfg1's arm", "ctrloop 2",
		     RLXFW_SPI_INST_R_ARM_WINDOW, -EPERM);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	getter_fail = 1;
	getter_lie.armed = 1;
	getter_lie.lo = PB;
	getter_lie.hi = PB + PS;
	getter_lie.budget = PS;
	loop_refuses("ctrloop 2, getter error with a permitting copy",
		     "ctrloop 2", RLXFW_SPI_INST_R_ARM_READ, -EPROTO);
	getter_fail = 0;
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	loop_refuses("ctrloop 0", "ctrloop 0", RLXFW_SPI_INST_R_SYNTAX,
		     -EINVAL);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	loop_refuses("ctrloop 65", "ctrloop 65", RLXFW_SPI_INST_R_SYNTAX,
		     -EINVAL);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	loop_refuses("ctrloop 2 with a trailing space", "ctrloop 2 ",
		     RLXFW_SPI_INST_R_SYNTAX, -EINVAL);

	/* two passes, uncut */
	world(0x1000u);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("ctrloop 2");
	note_loop();
	ckb("ctrloop 2 under the probe arm -> OK: 2 passes done, 8,195 ops",
	    rc == 0 && c->loop_reason == RLXFW_SPI_INST_OK && c->loop_ran &&
	    c->loop_passes == 2u && c->loop_done == 2u &&
	    c->loop_ops == 8195u && op_count == 8195);
	ok = op_count <= OPLOG;
	for (i = 0; ok && i < op_count; i++) {
		if ((i % 4097 == 0) != (op_kind[i] == 'E'))
			ok = 0;
		else if (op_kind[i] == 'E' && op_addr[i] != PB)
			ok = 0;
		else if (op_kind[i] == 'P' &&
			 (op_len[i] != 1u || op_addr[i] < PB ||
			  op_addr[i] >= PB + 512u || op_cleared[i] != 1u))
			ok = 0;
	}
	ckb("  per pass one SE at 0x3E0000, then 4,096 one-byte programs "
	    "inside [0x3E0000, 0x3E0200) clearing one bit each; one SE more",
	    ok && op_kind[8194] == 'E');
	ckb("  n_writes = 2 x 4,097 + 1 = 8,195: 3 erases, 8,192 programs",
	    n_note_erase == 3ul && n_note_prog == 8192ul);
	ckb("  the probe block ends erased (eraseprobe finds it clean), "
	    "nothing outside it changed, disarmed",
	    region_is(PB, PS, NULL) && outside_untouched(PB, PS) &&
	    wr.armed == 0 && !rtl819x_spi_lock.held && !unlocked_ops);
	ckb("  console: 2 x 18 + 2 RLXFW-SL lines -- p=0 erase, erased, "
	    "bit=256 .. bit=4096, and the last SE as p=2",
	    count_lines("RLXFW-SL ") == 38 &&
	    count_lines("RLXFW-SL p=0 bit=") == 16 &&
	    strstr(con, "RLXFW-SL p=0 erase\n") != NULL &&
	    strstr(con, "RLXFW-SL p=0 erased ms=") != NULL &&
	    strstr(con, "RLXFW-SL p=0 bit=256 ms=") != NULL &&
	    strstr(con, "RLXFW-SL p=1 bit=4096 ms=") != NULL &&
	    strstr(con, "RLXFW-SL p=2 erase\n") != NULL &&
	    strstr(con, "RLXFW-SL p=2 erased ms=") != NULL &&
	    strstr(con, "RLXFW-SL p=2 bit=") == NULL);

	/* a cut inside pass 1's program of bit 1000, the bit landed or not */
	for (landed = 0; landed <= 1; landed++) {
		world(0x1000u);
		rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
		fail_at_op = 4097 + 1 + 1000;
		fail_after_apply = landed;
		rc = rtl819x_spi_verb_inst("ctrloop 2");
		note_loop();
		v = bm_value(PB, &mal);
		last = last_bit_line(1u);
		snprintf(want, sizeof(want), "ctrloop 2 cut inside pass 1 at bit "
			 "1000 (%s): ENGINE, 1 pass done, the scratch reads %u",
			 landed ? "landed" : "not landed", 1000u + landed);
		ckb(want, rc == -EIO && c->loop_reason == RLXFW_SPI_INST_R_ENGINE &&
		    c->loop_done == 1u && v == 1000u + (u32)landed && !mal &&
		    wr.armed == 0);
		ckb("  ... within the 256 bits after the last bit= line (768): "
		    "the phase a capture would show",
		    last == 768 && (long)v >= last && (long)v <= last + 256);
		rebase();
		shows0 = procnum("ctrscratch_shows");
		rc = rtl819x_spi_verb_inst("ctrloop show");
		snprintf(want, sizeof(want), "ctrscratch value=%u malformed=0 "
			 "erased=0\n", 1000u + landed);
		ckb("  ctrloop show reads it, read-only: no op, the loop's own "
		    "fields untouched, the same line on the console",
		    rc == 0 && strstr(con, want) != NULL && op_count == 0 &&
		    !memcmp(chip, orig, CHIP_SZ) &&
		    c->loop_reason == RLXFW_SPI_INST_R_ENGINE &&
		    c->loop_done == 1u);
		ckb("  ... and /proc records it, which is what a card reads: "
		    "ctrscratch_shows +1, rc 0, value, malformed 0, erased 0",
		    procnum("ctrscratch_shows") == shows0 + 1 &&
		    procnum("ctrscratch_rc") == 0 &&
		    procnum("ctrscratch_value") == 1000 + landed &&
		    procnum("ctrscratch_malformed") == 0 &&
		    procnum("ctrscratch_erased") == 0);
		fail_at_op = -1;
		fail_after_apply = 0;
		rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
		rc = rtl819x_spi_verb_inst("ctrloop 1");
		note_loop();
		ckb("  and a new ctrloop 1 leaves the block clean again",
		    rc == 0 && c->loop_reason == RLXFW_SPI_INST_OK &&
		    region_is(PB, PS, NULL));
	}

	/* the cut lands in a pass's SE */
	world(0x1000u);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	fail_at_op = 4097;
	rc = rtl819x_spi_verb_inst("ctrloop 2");
	note_loop();
	ckb("ctrloop 2 cut in pass 1's SE -> ENGINE; the last RLXFW-SL line is "
	    "`RLXFW-SL p=1 erase`, and the scratch still reads 4096",
	    rc == -ETIMEDOUT && c->loop_reason == RLXFW_SPI_INST_R_ENGINE &&
	    c->loop_done == 1u && bm_value(PB, &mal) == 4096u && !mal &&
	    last_line("RLXFW-SL ") != NULL &&
	    !strncmp(last_line("RLXFW-SL "), "RLXFW-SL p=1 erase\n",
		     strlen("RLXFW-SL p=1 erase\n")));

	/* a part whose SE does nothing: the post-SE read catches it */
	world(0u);
	se_cost_us = 30ul;
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("ctrloop 2");
	note_loop();
	ckb("ctrloop 2 on a part whose SE does nothing -> PROBE_UNCLEAN at "
	    "pass 1's erase check, nothing programmed over it",
	    rc == -EIO && c->loop_reason == RLXFW_SPI_INST_R_PROBE_UNCLEAN &&
	    c->loop_done == 1u && op_count == 4098 && n_note_prog == 4096ul);

	/* a bit that will not program, inside the scratch bitmap */
	world(0x1000u);
	stuck1_addr = PB + 0x10u;
	stuck1_mask = 0x01u;
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("ctrloop 1");
	note_loop();
	ckb("ctrloop 1 with a bit stuck at 1 -> CTR_CMP at the pass's "
	    "read-back, no pass done",
	    rc == -EIO && c->loop_reason == RLXFW_SPI_INST_R_CTR_CMP &&
	    c->loop_done == 0u);

	/* dirt elsewhere in the block: the final whole-block check */
	world(0x1000u);
	chip[PB + 0x8000u] = 0x00u;
	memcpy(orig, chip, CHIP_SZ);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("ctrloop 1");
	note_loop();
	ckb("ctrloop 1 with a programmed byte at +0x8000 -> PROBE_UNCLEAN: "
	    "the loop ran, but eraseprobe would not find the block clean",
	    rc == -EIO && c->loop_reason == RLXFW_SPI_INST_R_PROBE_UNCLEAN &&
	    c->loop_done == 1u && c->loop_ops == 4098u);

	/* show, on states built by hand; no arm */
	world(0x1000u);
	shows0 = procnum("ctrscratch_shows");
	rc = rtl819x_spi_verb_inst("ctrloop show");
	ckb("ctrloop show on an erased block, unarmed: value=0 malformed=0 "
	    "erased=1, no op",
	    rc == 0 && strstr(con, "ctrscratch value=0 malformed=0 erased=1\n")
	    != NULL && op_count == 0 && wr.armed == 0);
	ckb("  ... /proc: ctrscratch_shows +1, rc 0, value 0, erased 1",
	    procnum("ctrscratch_shows") == shows0 + 1 &&
	    procnum("ctrscratch_rc") == 0 && procnum("ctrscratch_value") == 0 &&
	    procnum("ctrscratch_erased") == 1);
	world(0x1000u);
	chip[PB + 0x800u] = 0x00u;
	rc = rtl819x_spi_verb_inst("ctrloop show");
	ckb("ctrloop show with a byte programmed past the bitmap, inside the "
	    "sector: value=0 erased=0",
	    rc == 0 && strstr(con, "ctrscratch value=0 malformed=0 erased=0\n")
	    != NULL);
	world(0x1000u);
	chip[PB] = 0x5Fu;		/* zeros at bits 0 and 2 */
	rc = rtl819x_spi_verb_inst("ctrloop show");
	ckb("ctrloop show on zeros at bits 0 and 2: value=2 malformed=1",
	    rc == 0 && strstr(con, "ctrscratch value=2 malformed=1 erased=0\n")
	    != NULL);
	/* a good reading first, so a failed one has something to clear */
	world(0x1000u);
	chip[PB] = 0x00u;
	rtl819x_spi_verb_inst("ctrloop show");
	shows0 = procnum("ctrscratch_shows");
	ok = procnum("ctrscratch_value") == 8;
	read_fail_at = n_reads;
	con_reset();
	rc = rtl819x_spi_verb_inst("ctrloop show");
	ckb("ctrloop show whose read fails: the primitive's errno, no line",
	    rc == -ETIMEDOUT && strstr(con, "ctrscratch") == NULL);
	ckb("  ... /proc: ctrscratch_shows +1, ctrscratch_rc -110, and the last "
	    "good value (8) cleared, so no reader can take it for this one",
	    ok && procnum("ctrscratch_shows") == shows0 + 1 &&
	    procnum("ctrscratch_rc") == -ETIMEDOUT &&
	    procnum("ctrscratch_value") == 0 &&
	    procnum("ctrscratch_erased") == 0);
	world(0x1000u);
	n_kmalloc = 0;
	fail_kmalloc_at = 0;
	rc = rtl819x_spi_verb_inst("ctrloop show");
	fail_kmalloc_at = -1;
	ckb("ctrloop show with no memory: ENOMEM, and /proc says so",
	    rc == -ENOMEM && procnum("ctrscratch_rc") == -ENOMEM &&
	    procnum("ctrscratch_value") == 0 && op_count == 0);

	world(0x1000u);
	handoff('A', 5u);
	rtl819x_spi_wr_do_arm(PB, PB + PS, PS);
	rc = rtl819x_spi_verb_inst("ctrloop 1");
	note_loop();
	ckb("ctrloop 1 while slot A runs -> OK (the probe block is not fenced)",
	    rc == 0 && c->loop_reason == RLXFW_SPI_INST_OK);
}

/* --------------------------- the /proc page: the blocks at their widest */

static int longest_reason(void)
{
	int i, best = 1;

	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++)
		if (strlen(rlxfw_spi_inst_reason_name(i)) >
		    strlen(rlxfw_spi_inst_reason_name(best)))
			best = i;
	return best;
}

static int longest_region1(void)
{
	int i, best = 0;

	for (i = 0; i < RLXFW_SPI_INST_NREGIONS; i++)
		if (strlen(rlxfw_spi_inst_regions[i].name) >
		    strlen(rlxfw_spi_inst_regions[best].name))
			best = i;
	return best + 1;
}

/* What read_proc prints after the install path's blocks: its self-measuring
 * line, "proc_bytes_before_this_line %d\n", at its widest int.  The runner
 * checks that line is still the driver's last. */
#define PROC_TAIL	((int)sizeof("proc_bytes_before_this_line -2147483648\n") - 1)
/* MEASURED, bench/2026-10-07/X-B3Pc-cat.log (the armed image, R8b): the page
 * read 2,204 bytes, its own last line says so, and 1,304 of them came before
 * the install block; the other two armed captures of those seatings read
 * 1,298.  The rest of read_proc is unchanged since. */
#define MEASURED_PREFIX	1304
/* The widest prefix read_proc's own comments allow before the install path's
 * blocks -- the sum rtl819x_spi_inst_proc()'s comment states: 1,101 (its
 * unguarded fields, measured in its comment) + 340 (the sixteen guarded) +
 * 128 (the four R8b lines) + 714 (rtl819x-spi-write.c's widest) + 15
 * (wr_truncated) + 25 (n_wip_timeout at ten digits).  The runner checks each
 * allowance is still what those comments say. */
#define THEORY_PREFIX	(1101 + 340 + 128 + 714 + 15 + 25)

/* the end of the counter's block on a page that starts with it, or 0 */
static int ctr_block_len(const char *page)
{
	const char *q;

	if (strncmp(page, "ctr_attempts ", 13))
		return 0;
	q = strstr(page, "\nctr_truncated 0\n");
	return q ? (int)(q + 17 - page) : 0;
}

static void scenario_proc_page(void)
{
	static char page[8192];
	struct rlxfw_spi_inst_st s0;
	struct rlxfw_spi_inst_img im0;
	struct rlxfw_spi_inst_probe p0;
	struct rlxfw_spi_inst_ctr_st c0;
	struct rlxfw_spi_inst_st *s = &rtl819x_spi_inst_st;
	struct rlxfw_spi_inst_img *im = &rtl819x_spi_img_st;
	struct rlxfw_spi_inst_probe *pr = &rtl819x_spi_probe_st;
	struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	int used, n, worst = 0, worst_used = 0, over = 0, liars = 0;
	int nctr, ninst;

	/* after a run, the counter's block is on the page, FIRST (1.2) */
	world(0x1000u);
	handoff('A', 6u);
	rtl819x_spi_verb_inst("ctr 6");
	rtl819x_spi_verb_inst("ctrloop show");
	n = rtl819x_spi_inst_proc(page, 0);
	ckb("/proc after ctr 6 and ctrloop show: the counter's block first -- "
	    "ctr_ran 1, OK, cur 0, new 6, read 6, pp 6, the scratch reading -- "
	    "then the install block, inst_truncated 0 last",
	    n > 17 && !strncmp(page, "ctr_attempts ", 13) &&
	    strstr(page, "\nctr_ran 1\n") && strstr(page, "\nctr_reason OK\n") &&
	    strstr(page, "\nctr_cur 0\n") && strstr(page, "\nctr_new 6\n") &&
	    strstr(page, "\nctr_read 6\n") && strstr(page, "\nctr_pp 6\n") &&
	    strstr(page, "\nctrscratch_rc 0\nctrscratch_value 0\n"
		   "ctrscratch_malformed 0\nctrscratch_erased 1\n"
		   "ctr_truncated 0\ninst_version ") != NULL &&
	    !strcmp(page + n - 17, "inst_truncated 0\n"));
	ckb("/proc: no field shows a byte of the bitmap",
	    strstr(page, "bitmap") == NULL && strstr(page, "sha256") == NULL);

	/* the widest state every field's type can print, with the driver's own
	 * tick of 10,000 us: there every ten-digit se_jiffies wraps se_us, and
	 * 0xFFFFFFFF's product, 4294957296, still prints ten digits, so both are
	 * at their widest (the pure suite passes tick 1 and wraps nothing); %d
	 * fields at -2147483648.  Put back afterwards. */
	s0 = *s;
	im0 = *im;
	p0 = *pr;
	c0 = *c;
	s->attempts = s->done = s->refused = s->failed = 0xFFFFFFFFu;
	s->r.ran = INT_MIN;
	s->r.reason = longest_reason();
	s->r.verb = RLXFW_SPI_INST_V_PROBE;		/* the longest verb */
	s->r.region1 = longest_region1();
	s->r.base = s->r.size = s->r.len = s->r.pace_ms = 0xFFFFFFFFu;
	s->r.rc = s->r.policy = s->r.arm_ok = s->r.sha_checked = INT_MIN;
	s->r.sha_ok = s->r.hdr_checked = s->r.hdr_ok = INT_MIN;
	s->r.ops_planned = s->r.ops_done = s->r.n_se = s->r.n_pp = 0xFFFFFFFFu;
	s->r.erased = s->r.programmed = 0xFFFFFFFFu;
	s->r.committed = s->r.cmp_ran = s->r.cmp_ok = INT_MIN;
	s->r.phase = 'V';
	s->r.cmp_bytes = s->r.cmp_diff = 0xFFFFFFFFu;
	s->r.cmp_first = 0x80000000u;		/* %d: -2147483648 */
	s->r.ms = 0xFFFFFFFFu;
	im->len = im->writes = im->resets = 0xFFFFFFFFu;
	im->err = RLXFW_SPI_INST_IMG_POISONED;
	pr->ran = INT_MIN;
	pr->classified = 1;
	pr->se_bytes = INT_MIN;
	pr->m[0] = pr->m[1] = pr->m[2] = 'O';
	pr->se_polls = pr->pp_polls = 0xFFFFFFFFu;
	pr->se_jiffies = pr->pp_jiffies = 0xFFFFFFFFu;
	pr->cal_polls = pr->cal_ticks = pr->clean_step = pr->clean_ops = 0xFFFFFFFFu;
	pr->clean_known = 0;
	c->attempts = c->done = c->refused = c->failed = 0xFFFFFFFFu;
	c->ran = c->malformed = c->loop_ran = INT_MIN;
	c->reason = c->loop_reason = longest_reason();
	c->cur = c->newv = c->read = c->pp = c->ms = 0xFFFFFFFFu;
	c->loop_passes = c->loop_done = c->loop_ops = c->loop_ms = 0xFFFFFFFFu;
	c->scr_shows = c->scr_value = 0xFFFFFFFFu;
	c->scr_rc = c->scr_malformed = c->scr_erased = INT_MIN;

	n = rtl819x_spi_inst_proc(page, 0);
	nctr = ctr_block_len(page);
	ninst = n - nctr;
	ckb("the widest state, nothing before it: the counter's block is exactly "
	    "its measured MAX, the install block within its own (the driver's "
	    "0x20 / 4,096 / 10,000 print narrower than the header's widest)",
	    nctr == RLXFW_SPI_INST_CTR_PROC_MAX && ninst > 0 &&
	    ninst <= RLXFW_SPI_INST_PROC_MAX &&
	    strstr(page, " se_us=4294957296 pp_us=4294957296 ") != NULL &&
	    !strcmp(page + n - 17, "inst_truncated 0\n"));
	for (used = 0; used <= RTL819X_SPI_PROC_BUDGET; used++) {
		n = rtl819x_spi_inst_proc(page, used);
		if (used + n + PROC_TAIL > (int)PAGE_SIZE)
			over++;
		if (used + n > worst) {
			worst = used + n;
			worst_used = used;
		}
		/* each check is honest: a block that printed fits the budget
		 * the check promised it, its own flag line included */
		if (ctr_block_len(page) &&
		    used + ctr_block_len(page) > RTL819X_SPI_PROC_BUDGET)
			liars++;
		if (strstr(page, "inst_version ") &&
		    used + n > RTL819X_SPI_PROC_BUDGET)
			liars++;
	}
	printf("  (counter block at its widest %d bytes, install block %d, both "
	       "with their flags; over every `used` 0..%d the page reaches %d at "
	       "used %d, + %d for the last line, of %lu)\n",
	       nctr, ninst, RTL819X_SPI_PROC_BUDGET, worst, worst_used,
	       PROC_TAIL, PAGE_SIZE);
	ckb("the page stays inside one 4,096-byte page for every prefix up to "
	    "the budget, every field at its widest, the last line included",
	    over == 0 && worst + PROC_TAIL <= (int)PAGE_SIZE);
	ckb("every block that printed fit the budget its check promised: each "
	    "check counts the block's own flag line", liars == 0);
	n = rtl819x_spi_inst_proc(page, THEORY_PREFIX);
	ckb("at the widest prefix read_proc's comments allow (2,323), the "
	    "counter's block prints WHOLE, at its widest, and the page fits",
	    THEORY_PREFIX == 2323 &&
	    ctr_block_len(page) == RLXFW_SPI_INST_CTR_PROC_MAX &&
	    THEORY_PREFIX + n + PROC_TAIL <= (int)PAGE_SIZE);
	ckb("  ... and the install block, which would need 2,323 + 501 + 1,183 = "
	    "4,007, says inst_truncated 1",
	    !strcmp(page + n - 17, "inst_truncated 1\n") &&
	    strstr(page, "inst_version") == NULL);
	n = rtl819x_spi_inst_proc(page, MEASURED_PREFIX);
	ckb("at the prefix measured on the armed image (1,304 bytes), both "
	    "blocks print at their widest",
	    ctr_block_len(page) == RLXFW_SPI_INST_CTR_PROC_MAX &&
	    strstr(page, "inst_version ") != NULL &&
	    !strcmp(page + n - 17, "inst_truncated 0\n") &&
	    MEASURED_PREFIX + n + PROC_TAIL <= (int)PAGE_SIZE);
	*s = s0;
	*im = im0;
	*pr = p0;
	*c = c0;
}

/* ---------------------- /proc/rtl819x-spi-inst, the machine readers' node */

/* fs/proc/generic.c's __proc_file_read on the path the driver's handlers take,
 * *start left NULL (READ, the tree that builds, :37, :67-182): per pass one
 * handler call and at most PROC_BLOCK_SIZE = PAGE_SIZE - 1024 bytes, the
 * handler's length less *ppos, and the loop ends at the first pass that set
 * eof.  -999 if a handler ever took another path. */
typedef int (*readproc_t)(char *, char **, off_t, int, int *, void *);

static long model_read(readproc_t fn, char *ubuf, size_t nbytes, long *ppos,
		       int *calls)
{
	static char kpage[PAGE_SIZE];
	char *start;
	size_t count;
	long n, retval = 0;
	int eof = 0;

	while (nbytes > 0 && !eof) {
		count = nbytes < PAGE_SIZE - 1024 ? nbytes : PAGE_SIZE - 1024;
		start = NULL;
		n = fn(kpage, &start, (off_t)*ppos, (int)count, &eof, NULL);
		(*calls)++;
		if (n == 0)
			break;
		if (n < 0) {
			if (retval == 0)
				retval = n;
			break;
		}
		if (start != NULL)
			return -999;
		if (n > (long)PAGE_SIZE)
			n = (long)PAGE_SIZE;
		n -= *ppos;
		if (n <= 0)
			break;
		if (n > (long)count)
			n = (long)count;
		memcpy(ubuf, kpage + *ppos, (size_t)n);
		*ppos += n;
		nbytes -= (size_t)n;
		ubuf += n;
		retval += n;
	}
	return retval;
}

/* the model's positive control: a handler 3,500 bytes long */
static int long_handler(char *page, char **start, off_t off, int count,
			int *eof, void *data)
{
	(void)start; (void)off; (void)count; (void)data;
	memset(page, 'x', 3500);
	*eof = 1;
	return 3500;
}

static void scenario_node(void)
{
	static char node[8192], mainp[8192], want[8192], ubuf[65536];
	struct rlxfw_spi_inst_st s0;
	struct rlxfw_spi_inst_img im0;
	struct rlxfw_spi_inst_probe p0;
	struct rlxfw_spi_inst_ctr_st c0;
	struct rlxfw_spi_inst_st *s = &rtl819x_spi_inst_st;
	struct rlxfw_spi_inst_img *im = &rtl819x_spi_img_st;
	struct rlxfw_spi_inst_probe *pr = &rtl819x_spi_probe_st;
	struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	unsigned long w0 = rtl819x_spi_n_writes;
	char *start = NULL;
	long ppos, r1, r2;
	int eof = 0, calls, n, nm, nctr, nw;

	/* n_writes on the node moves with the writes */
	world(0x1000u);
	handoff('A', 6u);
	rtl819x_spi_n_writes = 41ul;
	rtl819x_spi_verb_inst("ctr 6");
	n = rtl819x_spi_inst_node_read_proc(node, &start, 0, 3072, &eof, NULL);
	ckb("/proc/rtl819x-spi-inst after ctr 6: `n_writes 47` first (41 + the "
	    "six programs), the install block, the counter's last; eof set",
	    n > 0 && eof == 1 && start == NULL &&
	    !strncmp(node, "n_writes 47\ninst_version ", 25) &&
	    strstr(node, "\nctr_pp 6\n") != NULL &&
	    !strcmp(node + n - 16, "ctr_truncated 0\n"));

	/* the widest state, as scenario_proc_page builds it, and n_writes at
	 * the target's widest unsigned long (this host's is wider) */
	s0 = *s;
	im0 = *im;
	p0 = *pr;
	c0 = *c;
	s->attempts = s->done = s->refused = s->failed = 0xFFFFFFFFu;
	s->r.ran = INT_MIN;
	s->r.reason = longest_reason();
	s->r.verb = RLXFW_SPI_INST_V_PROBE;
	s->r.region1 = longest_region1();
	s->r.base = s->r.size = s->r.len = s->r.pace_ms = 0xFFFFFFFFu;
	s->r.rc = s->r.policy = s->r.arm_ok = s->r.sha_checked = INT_MIN;
	s->r.sha_ok = s->r.hdr_checked = s->r.hdr_ok = INT_MIN;
	s->r.ops_planned = s->r.ops_done = s->r.n_se = s->r.n_pp = 0xFFFFFFFFu;
	s->r.erased = s->r.programmed = 0xFFFFFFFFu;
	s->r.committed = s->r.cmp_ran = s->r.cmp_ok = INT_MIN;
	s->r.phase = 'V';
	s->r.cmp_bytes = s->r.cmp_diff = 0xFFFFFFFFu;
	s->r.cmp_first = 0x80000000u;
	s->r.ms = 0xFFFFFFFFu;
	im->len = im->writes = im->resets = 0xFFFFFFFFu;
	im->err = RLXFW_SPI_INST_IMG_POISONED;
	pr->ran = INT_MIN;
	pr->classified = 1;
	pr->se_bytes = INT_MIN;
	pr->m[0] = pr->m[1] = pr->m[2] = 'O';
	pr->se_polls = pr->pp_polls = pr->se_jiffies = pr->pp_jiffies = 0xFFFFFFFFu;
	pr->cal_polls = pr->cal_ticks = pr->clean_step = pr->clean_ops = 0xFFFFFFFFu;
	pr->clean_known = 0;
	c->attempts = c->done = c->refused = c->failed = 0xFFFFFFFFu;
	c->ran = c->malformed = c->loop_ran = INT_MIN;
	c->reason = c->loop_reason = longest_reason();
	c->cur = c->newv = c->read = c->pp = c->ms = 0xFFFFFFFFu;
	c->loop_passes = c->loop_done = c->loop_ops = c->loop_ms = 0xFFFFFFFFu;
	c->scr_shows = c->scr_value = 0xFFFFFFFFu;
	c->scr_rc = c->scr_malformed = c->scr_erased = INT_MIN;
	rtl819x_spi_n_writes = 4294967295ul;

	eof = 0;
	n = rtl819x_spi_inst_node_read_proc(node, &start, 0, 3072, &eof, NULL);
	nm = rtl819x_spi_inst_proc(mainp, 0);
	nctr = ctr_block_len(mainp);
	nw = snprintf(want, sizeof(want), "n_writes %lu\n", rtl819x_spi_n_writes);
	memcpy(want + nw, mainp + nctr, (size_t)(nm - nctr));	/* install */
	memcpy(want + nw + (nm - nctr), mainp, (size_t)nctr);	/* counter */
	printf("  (/proc/rtl819x-spi-inst at its widest: %d bytes = %d n_writes + "
	       "%d install + %d counter; one read(2) takes %lu; the header's "
	       "bound RLXFW_SPI_INST_NODE_MAX is %d)\n", n, nw, nm - nctr, nctr,
	       PAGE_SIZE - 1024, RLXFW_SPI_INST_NODE_MAX);
	ckb("the node at the widest state is exactly the main page's two blocks, "
	    "install then counter, after its own n_writes line",
	    nctr > 0 && nw == RLXFW_SPI_INST_NODE_NWRITES_MAX &&
	    n == nw + nm && !memcmp(node, want, (size_t)n));
	ckb("  ... and its widest is inside one read: <= NODE_MAX <= 3,072",
	    n <= RLXFW_SPI_INST_NODE_MAX &&
	    RLXFW_SPI_INST_NODE_MAX <= (int)(PAGE_SIZE - 1024) &&
	    n <= (int)(PAGE_SIZE - 1024));

	/* through generic.c's read loop: one read(2) is the whole node */
	ppos = 0;
	calls = 0;
	r1 = model_read(rtl819x_spi_inst_node_read_proc, ubuf, sizeof(ubuf),
			&ppos, &calls);
	r2 = model_read(rtl819x_spi_inst_node_read_proc, ubuf + (r1 > 0 ? r1 : 0),
			sizeof(ubuf) - (size_t)(r1 > 0 ? r1 : 0), &ppos, &calls);
	ckb("one read(2) of the node, through generic.c's loop, returns all of "
	    "it, and the next returns 0 (FW-64: two handler calls)",
	    r1 == n && !memcmp(ubuf, node, (size_t)n) && r2 == 0 && calls == 2);
	ppos = 0;
	calls = 0;
	r1 = model_read(long_handler, ubuf, sizeof(ubuf), &ppos, &calls);
	r2 = model_read(long_handler, ubuf + (r1 > 0 ? r1 : 0),
			sizeof(ubuf) - (size_t)(r1 > 0 ? r1 : 0), &ppos, &calls);
	ckb("control: the same loop splits a 3,500-byte page into 3,072 and 428 "
	    "-- the main page's hazard, which the node is built to avoid",
	    r1 == 3072 && r2 == 428 && calls == 2);
	*s = s0;
	*im = im0;
	*pr = p0;
	*c = c0;
	rtl819x_spi_n_writes = w0;
}

/* ------------------- the write handler: what reaches the install parser */

static int wp(const char *line)
{
	return rtl819x_spi_write_proc(NULL, line, (unsigned long)strlen(line),
				      NULL);
}

static void scenario_dispatch(void)
{
	const struct rlxfw_spi_inst_ctr_st *c = &rtl819x_spi_ctr_st;
	char big[200];
	u32 at0, inst0;
	int rc, mal, n0;

	world(0x1000u);
	handoff('A', 6u);
	at0 = c->attempts;
	rc = wp("ctr 6\n");
	ckb("write_proc: `ctr 6\\n` reaches the counter verb -- the count back, "
	    "ctr_attempts +1, the bitmap at 6",
	    rc == 6 && c->attempts == at0 + 1 &&
	    c->reason == RLXFW_SPI_INST_OK && bm_value(ST, &mal) == 6u);
	rc = wp("arm 0x3e0000 0x3f0000 0x10000\n");
	ckb("write_proc: `arm` reaches the arm verb, which arms the probe",
	    rc == (int)strlen("arm 0x3e0000 0x3f0000 0x10000\n") && wr.armed &&
	    wr.lo == PB && !strcmp(outside_last, "arm"));
	rc = wp("ctrloop 1\n");
	ckb("write_proc: `ctrloop 1` reaches the loop, which runs to OK",
	    rc == 10 && c->loop_reason == RLXFW_SPI_INST_OK &&
	    c->loop_done == 1u && wr.armed == 0);
	con_reset();
	rc = wp("ctrloop show\n");
	ckb("write_proc: `ctrloop show` reaches the read-only show",
	    rc == 13 && strstr(con, "ctrscratch value=0 ") != NULL);
	at0 = c->attempts;
	inst0 = rtl819x_spi_inst_st.attempts;
	rc = wp("ctrl 30\n");
	ckb("write_proc: `ctrl 30` goes to the parser by its prefix, and the "
	    "parser refuses it SYNTAX (not as ctr)",
	    rc == -EINVAL && c->attempts == at0 &&
	    rtl819x_spi_inst_st.attempts == inst0 + 1 &&
	    rtl819x_spi_inst_st.r.reason == RLXFW_SPI_INST_R_SYNTAX);
	rc = wp("ctr6\n");
	ckb("write_proc: `ctr6` likewise -- the install path's SYNTAX",
	    rc == -EINVAL && c->attempts == at0 &&
	    rtl819x_spi_inst_st.attempts == inst0 + 2);
	n0 = n_outside;
	rc = wp("corrupt 5\n");
	ckb("write_proc: `corrupt 5` is not a ctr line: it reaches corrupt",
	    rc == 10 && n_outside == n0 + 1 && !strcmp(outside_last, "corrupt") &&
	    rtl819x_spi_inst_st.attempts == inst0 + 2);
	rc = wp("eraseprobe\n");
	ckb("write_proc: `eraseprobe` still reaches the parser under `erase`",
	    rc == -EACCES && rtl819x_spi_inst_st.r.verb == RLXFW_SPI_INST_V_PROBE &&
	    rtl819x_spi_inst_st.r.reason == RLXFW_SPI_INST_R_UNARMED);
	memset(big, 'x', sizeof(big));
	memcpy(big, "ctr ", 4);
	big[RLXFW_SPI_INST_LINE_MAX] = '\0';
	inst0 = rtl819x_spi_inst_st.attempts;
	at0 = c->attempts;
	rc = wp(big);
	ckb("write_proc: a 128-byte line is refused whole, never cut into a "
	    "shorter verb",
	    rc == -EINVAL && rtl819x_spi_inst_st.attempts == inst0 &&
	    c->attempts == at0);
}

/* The reasons only the glue produces; the pure suite exempts them by name,
 * so this suite must produce every one of them or the exemption is
 * covering for a reason nobody drives. */
static const int glue_only[] = {
	RLXFW_SPI_INST_R_KAT, RLXFW_SPI_INST_R_HASH, RLXFW_SPI_INST_R_SHA,
	RLXFW_SPI_INST_R_NOMEM, RLXFW_SPI_INST_R_ENGINE, RLXFW_SPI_INST_R_CMP,
	RLXFW_SPI_INST_R_ARM_READ
};

/* 1.1's reasons, which pure functions decide and the glue must REACH: each
 * produced here through the driver's own glue, in both tables. */
static const int glue_reaches[] = {
	RLXFW_SPI_INST_R_HDR_SEQ, RLXFW_SPI_INST_R_REPEAT_ONLY_SLOT,
	RLXFW_SPI_INST_R_RUNNING_SLOT, RLXFW_SPI_INST_R_CTR_ABOVE,
	RLXFW_SPI_INST_R_CTR_HANDOFF, RLXFW_SPI_INST_R_CTR_BELOW,
	RLXFW_SPI_INST_R_CTR_MALFORMED, RLXFW_SPI_INST_R_CTR_CMP,
	RLXFW_SPI_INST_R_PROBE_UNCLEAN
};

int main(int argc, char **argv)
{
	struct blob A, B, R, S, LR, C1, C2, C0, CL;
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
	R = load("rlxboot.cs6c");
	S = load("rescue.cs6c");
	LR = load("rlxboot.cr6c");
	C1 = load("cfg-seq1.bin");
	C2 = load("cfg-seq2.bin");
	C0 = load("cfg-seq0.bin");
	CL = load("cfg-4097.bin");
	printf("test-spi-install-glue: the driver's Gap A block on a simulated "
	       "part, %s table (%d regions); slotA.rlxu %u bytes\n",
	       RLXFW_SPI_INST_PROVISION ? "provisioning" : "SHIPPED",
	       RLXFW_SPI_INST_NREGIONS, A.n);

	scenario_ok(&A, 0x1000u, 0u);
	scenario_ok(&A, 0x10000u, 0u);
	scenario_ok(&A, 0x1000u, 7u);
#if RLXFW_SPI_INST_PROVISION
	scenario_barrier(0x1000u);
	scenario_barrier(0x10000u);
#endif
	scenario_refusals(&A, &B, &R);
	scenario_cuts(&A, 0x1000u);
	scenario_cuts(&A, 0x10000u);
	scenario_late(&A);
#if RLXFW_SPI_INST_PROVISION
	scenario_cs6c(&R, &S, &LR);
#else
	scenario_shipped_floor(&R, &S);
#endif
	scenario_probe_size(0x1000u, 45000ul, 16u);
	scenario_probe_size(0x8000u, 150000ul, 2u);
	scenario_probe_size(0x10000u, 300000ul, 1u);
	scenario_probe_cases(&A);
	scenario_errno();
	scenario_cfg(&C1, &C2, &C0, &CL, &R);
	scenario_fence(&A, &B, &C1);
	scenario_repeat(&A);
	scenario_ctr();
	scenario_ctrloop();
	scenario_proc_page();
	scenario_node();
	scenario_dispatch();

	/* the whole run's: the lowest flash address any op reached, and the
	 * reads' alignment */
#if RLXFW_SPI_INST_PROVISION
	ckb("control: in the provisioning build the lowest address any op "
	    "reached is 0x010000, rlxboot's -- the tracker sees low addresses",
	    min_addr_seen == 0x010000u);
#else
	ckb("shipped: across the whole run the lowest address any op reached "
	    "is 0x070000, slot A's base -- nothing below it was named",
	    min_addr_seen == 0x070000u);
#endif
	ckb("every PIO read the glue issued was 4-aligned in address and length",
	    n_misaligned == 0ul);
	for (i = 0; i < (int)(sizeof(glue_only) / sizeof(glue_only[0])); i++)
		if (!seen[glue_only[i]]) {
			printf("  FAIL      glue-only reason %s was never produced\n",
			       rlxfw_spi_inst_reason_name(glue_only[i]));
			nfail++;
		}
	for (i = 0; i < (int)(sizeof(glue_reaches) / sizeof(glue_reaches[0]));
	     i++)
		if (!seen[glue_reaches[i]]) {
			printf("  FAIL      1.1 reason %s never reached through "
			       "the glue\n",
			       rlxfw_spi_inst_reason_name(glue_reaches[i]));
			nfail++;
		}
	printf("reasons produced:");
	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++)
		if (seen[i])
			printf(" %s=%d", rlxfw_spi_inst_reason_name(i), seen[i]);
	printf("\n");
	free(A.p); free(B.p); free(R.p); free(S.p); free(LR.p);
	free(C1.p); free(C2.p); free(C0.p); free(CL.p);
	if (nfail) {
		printf("test-spi-install-glue: %d FAILURE(S) of %d\n", nfail,
		       ncase);
		return 1;
	}
	printf("test-spi-install-glue: all %d case(s) pass\n", ncase);
	return 0;
}
