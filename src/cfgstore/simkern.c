/* simkern.c -- see simkern.h.  TEST-ONLY: linked into test_flash and
 * cfgstore-sim under $O/host, never into a target object list (the target
 * build compiles $(RLXLIB_NAMES) and main.c, and src/cfgstore/Makefile's T1
 * gate counts exactly those objects).
 *
 * The decisions are the kernel's, not this file's: the verb parser, the arm
 * agreement, the staging admission, the payload check, the plan of erases and
 * programs and the read-back comparison are the pure functions of
 * rtl819x-spi-install.h and rtl819x-spi-wrpolicy.h, compiled here unchanged as
 * tools/test-spi-install.c compiles them.  What this file adds is what
 * rtl819x-spi.c's glue adds around them -- the order (rtl819x_spi_inst_run),
 * the digest, the disarm after every attempt, the errno per reason -- written
 * again from that glue and NOT shared with it, so a difference between the two
 * is possible and is this simulation's first limit.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "sha256.h"
#include "simkern.h"

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

#include "rtl819x-spi-wrpolicy.h"
#include "rtl819x-spi-install.h"

/* The four device paths spictl_dev names, as strings: the product's own. */
#define DEV_PROC	"/proc/rtl819x-spi"
#define DEV_IMG		"/proc/rtl819x-spi-img"
#define DEV_LOCK	"/run/rlxfw-flash.lock"
#define DEV_FLASH	"/dev/mtd2ro"
#define DEV_STATE	"/proc/rtl819x-spi-inst"

/* Other spellings of the image's flash nodes: on the device each is a
 * character device, so here each opens /dev/zero, and an lseek on it is an
 * event ('c'), which is how a case shows the file backend never read it. */
static const char *const sk_other_nodes[] = {
	"/dev/mtd0ro", "/dev/mtd1ro", "//dev/mtd2ro", "/dev/./mtd2ro"
};

int __real_open(const char *path, int flags, ...);
int __real_close(int fd);
ssize_t __real_write(int fd, const void *buf, size_t n);
int __real_flock(int fd, int op);
int __real_nanosleep(const struct timespec *req, struct timespec *rem);
off_t __real_lseek(int fd, off_t off, int whence);

/* ------------------------------------------------------------------------- */

#define SK_PATH		512
#define SK_FDMAX	1024
#define SK_EVMAX	512

enum { FD_NONE = 0, FD_VERB, FD_IMG, FD_LOCK, FD_FLASH, FD_CHAR };

static int sk_on;
static char sk_dirp[SK_PATH], sk_page[SK_PATH], sk_lock[SK_PATH];
static char sk_node[SK_PATH];
static char sk_flash[SK_PATH], sk_log[SK_PATH], sk_staged[SK_PATH];
static unsigned char sk_fd[SK_FDMAX];

static struct simk_ev sk_ev[SK_EVMAX];
static int sk_nev, sk_evlost;
static unsigned long sk_slept;

/* the simulated driver */
static struct rlxfw_spi_wr_arm sk_arm;
static struct rlxfw_spi_inst_img sk_im;
static struct rlxfw_spi_inst_st sk_st;
static struct rlxfw_spi_inst_probe sk_pr;
static unsigned char *sk_img;
static unsigned long sk_nwrites, sk_refused;
static int sk_fault;
static int sk_holder = -1;

/* rtl819x-spi.c's rtl819x_spi_inst_errno, the rows this simulation reaches. */
static int sk_errno(int why)
{
	switch (why) {
	case RLXFW_SPI_INST_OK:			return 0;
	case RLXFW_SPI_INST_R_SYNTAX:
	case RLXFW_SPI_INST_R_REGION:
	case RLXFW_SPI_INST_R_ERASE_ONLY:
	case RLXFW_SPI_INST_R_NOT_ERASABLE:	return EINVAL;
	case RLXFW_SPI_INST_R_UNARMED:		return EACCES;
	case RLXFW_SPI_INST_R_ARM_WINDOW:	return EPERM;
	case RLXFW_SPI_INST_R_ARM_BUDGET:	return ENOSPC;
	case RLXFW_SPI_INST_R_IMG_BAD:		return EIO;
	case RLXFW_SPI_INST_R_IMG_EMPTY:	return ENODATA;
	case RLXFW_SPI_INST_R_IMG_SIZE:		return EFBIG;
	case RLXFW_SPI_INST_R_SHA:		return EBADMSG;
	case RLXFW_SPI_INST_R_HDR_MAGIC:
	case RLXFW_SPI_INST_R_HDR_FORMAT:
	case RLXFW_SPI_INST_R_HDR_FLASH_AT:
	case RLXFW_SPI_INST_R_HDR_FORM:
	case RLXFW_SPI_INST_R_HDR_LEN:
	case RLXFW_SPI_INST_R_HDR_SUM:
	case RLXFW_SPI_INST_R_HDR_SEQ:		return ENOEXEC;
	case RLXFW_SPI_INST_R_POLICY:		return EPERM;
	case RLXFW_SPI_INST_R_NOMEM:		return ENOMEM;
	case RLXFW_SPI_INST_R_ENGINE:
	case RLXFW_SPI_INST_R_CMP:		return EIO;
	default:				return EPROTO;
	}
}

/* ------------------------------------------------------------------------- */
/* Events                                                                    */
/* ------------------------------------------------------------------------- */

static void sk_event(char kind, const char *text, size_t len, int err,
		     uint32_t off)
{
	struct simk_ev *e;
	char line[200];
	int n, fd;

	if (sk_nev < SK_EVMAX) {
		e = &sk_ev[sk_nev++];
		memset(e, 0, sizeof *e);
		e->kind = kind;
		if (text != NULL)
			(void)snprintf(e->text, sizeof e->text, "%s", text);
		e->len = len;
		e->err = err;
		e->off = off;
	} else {
		sk_evlost++;
	}
	switch (kind) {
	case 'v':
		n = snprintf(line, sizeof line, "v %s", text);
		break;
	case 'i':
		n = snprintf(line, sizeof line, "i %lu", (unsigned long)len);
		break;
	case 's':
	case 'c':
		n = snprintf(line, sizeof line, "%c 0x%lx", kind,
			     (unsigned long)off);
		break;
	default:
		n = snprintf(line, sizeof line, "%c", kind);
		break;
	}
	if (n < 0 || (size_t)n >= sizeof line - 16)
		return;
	if (err != 0)
		n += snprintf(line + n, sizeof line - (size_t)n, " !%d", err);
	line[n++] = '\n';
	fd = __real_open(sk_log, O_WRONLY | O_CREAT | O_APPEND, 0600);
	if (fd >= 0) {
		ssize_t w = __real_write(fd, line, (size_t)n);

		(void)w;
		(void)__real_close(fd);
	}
}

void simk_reset(void)
{
	sk_nev = 0;
	sk_evlost = 0;
	sk_slept = 0;
}

int simk_nev(void)
{
	return sk_evlost ? -1 : sk_nev;
}

const struct simk_ev *simk_ev(int i)
{
	return (i >= 0 && i < sk_nev) ? &sk_ev[i] : NULL;
}

unsigned long simk_slept_ms(void)
{
	return sk_slept;
}

unsigned long simk_nwrites(void)
{
	return sk_nwrites;
}

void simk_fault(int f)
{
	sk_fault = (f > SIMK_NONE && f < SIMK_NFAULT) ? f : SIMK_NONE;
}

const char *simk_flash_file(void)
{
	return sk_flash;
}

const char *simk_dir(void)
{
	return sk_dirp;
}

const char *simk_staged_file(void)
{
	return sk_staged;
}

/* ------------------------------------------------------------------------- */
/* Setup                                                                     */
/* ------------------------------------------------------------------------- */

static void sk_model_reset(void)
{
	memset(&sk_arm, 0, sizeof sk_arm);
	memset(&sk_im, 0, sizeof sk_im);
	memset(&sk_st, 0, sizeof sk_st);
	memset(&sk_pr, 0, sizeof sk_pr);
	free(sk_img);
	sk_img = NULL;
	/* Not 0: a reader that assumed a zero baseline instead of reading the
	 * counter before the install would be wrong here. */
	sk_nwrites = 1234;
	sk_refused = 0;
	sk_fault = SIMK_NONE;
	memset(sk_fd, 0, sizeof sk_fd);
	simk_reset();
}

int simk_attach(const char *dir)
{
	if (dir == NULL || strlen(dir) + 16 >= SK_PATH)
		return -1;
	(void)snprintf(sk_dirp, sizeof sk_dirp, "%s", dir);
	(void)snprintf(sk_page, sizeof sk_page, "%s/proc.page", dir);
	(void)snprintf(sk_node, sizeof sk_node, "%s/inst.node", dir);
	(void)snprintf(sk_lock, sizeof sk_lock, "%s/flash.lock", dir);
	(void)snprintf(sk_flash, sizeof sk_flash, "%s/mtd2ro.bin", dir);
	(void)snprintf(sk_log, sizeof sk_log, "%s/writes.log", dir);
	(void)snprintf(sk_staged, sizeof sk_staged, "%s/staged.bin", dir);
	sk_model_reset();
	sk_on = 1;
	return 0;
}

int simk_init(const char *dir)
{
	unsigned char *chip;
	ssize_t w;
	size_t i;
	int fd;

	if (simk_attach(dir) != 0)
		return -1;
	chip = malloc(SIMK_CHIP);
	if (chip == NULL)
		return -1;
	memset(chip, 0xFF, SIMK_CHIP);
	for (i = 0; i < 0x10000u; i++)
		chip[i] = (unsigned char)((i * 7u + 1u) & 0x7Fu);	/* never 0xFF */
	fd = __real_open(sk_flash, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0) {
		free(chip);
		return -1;
	}
	w = __real_write(fd, chip, SIMK_CHIP);
	(void)__real_close(fd);
	free(chip);
	if (w != (ssize_t)SIMK_CHIP)
		return -1;
	fd = __real_open(sk_log, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd >= 0)
		(void)__real_close(fd);
	return 0;
}

/* A child that inherited RLXFW_SIMKERN_DIR attaches at its first wrapped
 * call; without it nothing is mapped and every call passes through. */
static void sk_ready(void)
{
	const char *d;

	if (sk_on)
		return;
	d = getenv("RLXFW_SIMKERN_DIR");
	if (d != NULL && d[0] != '\0')
		(void)simk_attach(d);
}

int simk_hold_lock(int on)
{
	if (on) {
		if (sk_holder >= 0)
			return 0;
		sk_holder = __real_open(sk_lock, O_RDWR | O_CREAT, 0600);
		if (sk_holder < 0)
			return -1;
		if (__real_flock(sk_holder, LOCK_EX | LOCK_NB) != 0) {
			(void)__real_close(sk_holder);
			sk_holder = -1;
			return -1;
		}
		return 0;
	}
	if (sk_holder >= 0) {
		(void)__real_flock(sk_holder, LOCK_UN);
		(void)__real_close(sk_holder);
		sk_holder = -1;
	}
	return 0;
}

/* ------------------------------------------------------------------------- */
/* The driver: rtl819x-spi.c's write_proc, verb by verb                      */
/* ------------------------------------------------------------------------- */

static int sk_flash_rw(int wr, uint32_t addr, void *buf, size_t n)
{
	int fd = __real_open(sk_flash, wr ? O_WRONLY : O_RDONLY);
	ssize_t r;

	if (fd < 0)
		return -1;
	r = wr ? pwrite(fd, buf, n, (off_t)addr) : pread(fd, buf, n, (off_t)addr);
	(void)__real_close(fd);
	return (r == (ssize_t)n) ? 0 : -1;
}

/* `arm <lo> <hi> <budget>`: three numbers, base 0, nothing trailing. */
static int sk_verb_arm(const char *arg)
{
	unsigned long v[3];
	const char *q = arg;
	char *end;
	int i;

	if (sk_fault == SIMK_ARM_EPERM)
		return -EPERM;
	for (i = 0; i < 3; i++) {
		while (*q == ' ' || *q == '\t')
			q++;
		if (*q == '-' || *q == '+')
			return -EINVAL;
		v[i] = strtoul(q, &end, 0);
		if (end == q)
			return -EINVAL;
		q = end;
	}
	while (*q == ' ' || *q == '\t')
		q++;
	if (*q != '\0')
		return -EINVAL;
	if (rlxfw_spi_wr_chk_arm((u32)v[0], (u32)v[1], (u32)v[2]) !=
	    RLXFW_SPI_WR_OK) {
		sk_refused++;
		return -EPERM;
	}
	sk_arm.lo = (u32)v[0];
	sk_arm.hi = (u32)v[1];
	sk_arm.budget = (u32)v[2];
	sk_arm.armed = 1;
	return 0;
}

static void sk_disarm(void)
{
	memset(&sk_arm, 0, sizeof sk_arm);
}

/* rtl819x_spi_inst_run for `install` and `erase`; the probe and the counter
 * are not simulated and refuse SYNTAX. */
static int sk_verb_inst(const char *line)
{
	struct rlxfw_spi_inst_res *r = &sk_st.r;
	const struct rlxfw_spi_inst_region *rg;
	struct rlxfw_spi_inst_req rq;
	struct rlxfw_spi_inst_plan pl;
	struct rlxfw_spi_inst_opd op;
	unsigned char got[SHA256_DIGEST_LEN], chunk[0x1000];
	u32 i, nops, off;
	int why;

	rlxfw_spi_inst_begin(&sk_st);
	why = rlxfw_spi_inst_parse(line, &rq);
	r->verb = rq.verb;
	r->region1 = rq.region + 1;
	r->pace_ms = rq.pace_ms;
	if (why)
		goto refuse;
	if (rq.verb != RLXFW_SPI_INST_V_INSTALL &&
	    rq.verb != RLXFW_SPI_INST_V_ERASE) {
		why = RLXFW_SPI_INST_R_SYNTAX;
		goto refuse;
	}
	rg = &rlxfw_spi_inst_regions[rq.region];
	r->base = rg->base;
	r->size = rg->size;
	why = rlxfw_spi_inst_chk_arm(&sk_arm, rg);
	if (why)
		goto refuse;
	r->arm_ok = 1;

	if (rq.verb == RLXFW_SPI_INST_V_INSTALL) {
		why = rlxfw_spi_inst_chk_img(&sk_im, rg);
		if (!why && sk_img == NULL)
			why = RLXFW_SPI_INST_R_IMG_EMPTY;
		if (why)
			goto refuse;
		r->len = sk_im.len;
		(void)sha256(sk_img, r->len, got);
		{
			int fd = __real_open(sk_staged,
					     O_WRONLY | O_CREAT | O_TRUNC, 0600);

			if (fd >= 0) {
				ssize_t w = __real_write(fd, sk_img, r->len);

				(void)w;
				(void)__real_close(fd);
			}
		}
		if (sk_fault == SIMK_INST_SHA)
			got[0] ^= 0x01u;
		r->sha_checked = 1;
		r->sha_ok = rlxfw_spi_inst_digest_eq(got, rq.sha);
		if (!r->sha_ok) {
			why = RLXFW_SPI_INST_R_SHA;
			goto refuse;
		}
		why = rlxfw_spi_inst_chk_payload(sk_img, r->len, rg);
		r->hdr_checked = 1;
		r->hdr_ok = !why;
		if (why)
			goto refuse;
	}

	why = rlxfw_spi_inst_plan_init(&pl, rg, r->len,
				       RLXFW_SPI_WR_ERASE_GRAIN);
	if (why)
		goto refuse;
	nops = rlxfw_spi_inst_nops(&pl);
	r->ops_planned = nops;
	for (i = 0; i < nops; i++) {
		if (rlxfw_spi_inst_op(&pl, i, &op) == RLXFW_SPI_INST_OP_ERASE) {
			r->phase = 'E';
			if (op.len > sizeof chunk) {
				why = RLXFW_SPI_INST_R_POLICY;
				goto fail;
			}
			memset(chunk, 0xFF, op.len);
			if (sk_flash_rw(1, op.addr, chunk, op.len) != 0) {
				why = RLXFW_SPI_INST_R_ENGINE;
				goto fail;
			}
			sk_nwrites++;
			r->n_se++;
			r->erased += op.len;
		} else if (op.kind == RLXFW_SPI_INST_OP_PROG) {
			r->phase = op.commit ? 'H' : 'P';
			if (sk_flash_rw(1, op.addr, sk_img + op.off,
					op.len) != 0) {
				why = RLXFW_SPI_INST_R_ENGINE;
				goto fail;
			}
			sk_nwrites++;
			r->n_pp++;
			r->programmed += op.len;
			r->committed = op.commit;
		} else {
			why = RLXFW_SPI_INST_R_POLICY;
			goto fail;
		}
		r->ops_done++;
	}
	if (sk_fault == SIMK_NW_MINUS1)
		sk_nwrites--;
	if (sk_fault == SIMK_NW_PLUS1)
		sk_nwrites++;

	r->phase = 'V';
	r->cmp_ran = 1;
	for (off = 0; off < rg->size; off += (u32)sizeof chunk) {
		if (sk_flash_rw(0, rg->base + off, chunk, sizeof chunk) != 0) {
			why = RLXFW_SPI_INST_R_ENGINE;
			goto fail;
		}
		rlxfw_spi_inst_cmp(chunk, off, (u32)sizeof chunk, sk_img,
				   r->len, &r->cmp_diff, &r->cmp_first);
		r->cmp_bytes += (u32)sizeof chunk;
	}
	if (r->cmp_diff) {
		why = RLXFW_SPI_INST_R_CMP;
		goto fail;
	}
	r->cmp_ok = 1;
	r->phase = 'D';
	sk_st.done++;
	why = RLXFW_SPI_INST_OK;
	goto out;
refuse:
	sk_st.refused++;
	goto out;
fail:
	sk_st.failed++;
out:
	r->reason = why;
	r->rc = -sk_errno(why);
	sk_disarm();		/* ONE ARM, ONE ATTEMPT */
	return r->rc;
}

static int sk_verb(const char *buf, size_t count)
{
	char b[RLXFW_SPI_INST_LINE_MAX];
	size_t n = count;

	if (n >= sizeof b)
		return -EINVAL;
	memcpy(b, buf, n);
	b[n] = '\0';
	while (n > 0 && (b[n - 1] == '\n' || b[n - 1] == '\r'))
		b[--n] = '\0';
	if (strncmp(b, "arm ", 4) == 0)
		return sk_verb_arm(b + 4);
	if (strcmp(b, "disarm") == 0) {
		if (sk_fault == SIMK_DISARM_EIO)
			return -EIO;
		sk_disarm();
		return 0;
	}
	if (strncmp(b, "install", 7) == 0 || strncmp(b, "erase", 5) == 0)
		return sk_verb_inst(b);
	if (strcmp(b, "img reset") == 0) {
		free(sk_img);
		sk_img = NULL;
		rlxfw_spi_inst_img_reset(&sk_im);
		return 0;
	}
	return -EINVAL;
}

static int sk_stage(const void *buf, size_t count)
{
	switch (rlxfw_spi_inst_img_admit(&sk_im, (unsigned long)count)) {
	case RLXFW_SPI_INST_IMG_OK:
		break;
	case RLXFW_SPI_INST_IMG_OVERFLOW:
		return -EFBIG;
	default:
		return -EIO;
	}
	if (sk_fault == SIMK_STAGE_EFBIG) {
		sk_im.err = RLXFW_SPI_INST_IMG_OVERFLOW;
		return -EFBIG;
	}
	if (count == 0)
		return 0;
	if (sk_img == NULL) {
		sk_img = malloc(RLXFW_SPI_INST_IMG_CAP);
		if (sk_img == NULL) {
			sk_im.err = RLXFW_SPI_INST_IMG_NOMEM;
			return -ENOMEM;
		}
	}
	memcpy(sk_img + sk_im.len, buf, count);
	sk_im.len += (u32)count;
	sk_im.writes++;
	return (int)count;
}

/* /proc/rtl819x-spi-inst, the node every field is read from (SPEC-S144-U § 2,
 * the 21:4x ruling): n_writes, the install block, the counter's block -- the
 * install header's own two emit functions -- with a fault applied to what is
 * PRINTED only, never to the state.  The kernel asserts at compile time that
 * the node fits one read; this refuses to serve one that does not. */
#define SK_NODE_MAX	3072

static int sk_node_text(char *p)
{
	static const struct rlxfw_spi_inst_ctr_st ctr0;
	struct rlxfw_spi_inst_st st = sk_st;
	struct rlxfw_spi_inst_img im = sk_im;
	int len = 0;

	if (sk_fault == SIMK_IMGLEN_SHORT && im.len > 0)
		im.len--;
	if (sk_fault == SIMK_IMGERR)
		im.err = RLXFW_SPI_INST_IMG_POISONED;
	if (sk_fault == SIMK_INST_REASON && st.r.ran &&
	    st.r.reason == RLXFW_SPI_INST_OK)
		st.r.reason = RLXFW_SPI_INST_R_CMP;
	if (sk_fault == SIMK_CMP_DIFF && st.r.cmp_ran)
		st.r.cmp_diff = 1;
	if (sk_fault == SIMK_CMP_OK0 && st.r.cmp_ran)
		st.r.cmp_ok = 0;

	len += sprintf(p + len, "n_writes %lu\n", sk_nwrites);
	len += rlxfw_spi_inst_emit(p + len, &st, &im, &sk_pr, 0x20u,
				   RLXFW_SPI_WR_ERASE_GRAIN, 10000u);
	len += rlxfw_spi_inst_emit_ctr(p + len, &ctr0);
	return len;
}

/* /proc/rtl819x-spi, the verbs' page.  On the device it prints these fields
 * and many more, past one read; here it prints none, so a reader that took a
 * field from it instead of the node finds nothing and the case goes red. */
static const char sk_proc_text[] =
	"version rtl819x-spi (simulated; fields are in /proc/rtl819x-spi-inst)\n";

static int sk_serve(const char *file, const char *text, int n)
{
	ssize_t w;
	int fd;

	if (n < 0 || n > SK_NODE_MAX * 2) {
		errno = EFBIG;
		return -1;
	}
	fd = __real_open(file, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0)
		return -1;
	w = __real_write(fd, text, (size_t)n);
	(void)__real_close(fd);
	if (w != (ssize_t)n) {
		errno = EIO;
		return -1;
	}
	return __real_open(file, O_RDONLY);
}

static int sk_open_node(void)
{
	static char text[8192];
	int n = sk_node_text(text);

	if (n > SK_NODE_MAX) {		/* the kernel's assert, as a refusal */
		errno = EFBIG;
		return -1;
	}
	return sk_serve(sk_node, text, n);
}

/* ------------------------------------------------------------------------- */
/* The wrappers                                                              */
/* ------------------------------------------------------------------------- */

static int sk_mark(int fd, int kind)
{
	if (fd >= 0 && fd < SK_FDMAX)
		sk_fd[fd] = (unsigned char)kind;
	else if (fd >= SK_FDMAX) {
		(void)__real_close(fd);
		errno = EMFILE;
		return -1;
	}
	return fd;
}

static int sk_kind(int fd)
{
	return (sk_on && fd >= 0 && fd < SK_FDMAX) ? sk_fd[fd] : FD_NONE;
}

int __wrap_open(const char *path, int flags, ...)
{
	int mode = 0, acc = flags & O_ACCMODE;

	if (flags & O_CREAT) {
		va_list ap;

		va_start(ap, flags);
		mode = va_arg(ap, int);
		va_end(ap);
	}
	sk_ready();
	if (!sk_on || path == NULL)
		return __real_open(path, flags, mode);
	if (strcmp(path, DEV_PROC) == 0) {
		if (acc == O_RDONLY)
			return sk_serve(sk_page, sk_proc_text,
					(int)sizeof sk_proc_text - 1);
		return sk_mark(__real_open("/dev/null", O_WRONLY), FD_VERB);
	}
	if (strcmp(path, DEV_STATE) == 0) {
		if (acc != O_RDONLY) {		/* 0444: read-only */
			errno = EACCES;
			return -1;
		}
		return sk_open_node();
	}
	{
		size_t k;

		for (k = 0; k < sizeof sk_other_nodes / sizeof sk_other_nodes[0];
		     k++) {
			if (strcmp(path, sk_other_nodes[k]) != 0)
				continue;
			if (acc != O_RDONLY) {	/* 0400 and an odd minor */
				errno = EACCES;
				return -1;
			}
			return sk_mark(__real_open("/dev/zero", O_RDONLY), FD_CHAR);
		}
	}
	if (strcmp(path, DEV_IMG) == 0) {
		if (acc == O_RDONLY) {		/* 0200: no read_proc */
			errno = EACCES;
			return -1;
		}
		return sk_mark(__real_open("/dev/null", O_WRONLY), FD_IMG);
	}
	if (strcmp(path, DEV_LOCK) == 0)
		return sk_mark(__real_open(sk_lock, flags, mode), FD_LOCK);
	if (strcmp(path, DEV_FLASH) == 0) {
		if (acc != O_RDONLY) {		/* 0400 and an odd minor */
			errno = EACCES;
			return -1;
		}
		return sk_mark(__real_open(sk_flash, O_RDONLY), FD_FLASH);
	}
	return __real_open(path, flags, mode);
}

int __wrap_close(int fd)
{
	if (fd >= 0 && fd < SK_FDMAX)
		sk_fd[fd] = FD_NONE;
	return __real_close(fd);
}

ssize_t __wrap_write(int fd, const void *buf, size_t n)
{
	char text[RLXFW_SPI_INST_LINE_MAX + 8];
	int k = sk_kind(fd), rc;

	if (k == FD_VERB) {
		size_t m = (n < sizeof text - 1) ? n : sizeof text - 1;

		memcpy(text, buf, m);
		text[m] = '\0';
		rc = sk_verb((const char *)buf, n);
		sk_event('v', text, n, rc < 0 ? -rc : 0, 0);
		if (rc < 0) {
			errno = -rc;
			return -1;
		}
		return (ssize_t)n;
	}
	if (k == FD_IMG) {
		rc = sk_stage(buf, n);
		sk_event('i', NULL, n, rc < 0 ? -rc : 0, 0);
		if (rc < 0) {
			errno = -rc;
			return -1;
		}
		return (ssize_t)n;
	}
	return __real_write(fd, buf, n);
}

int __wrap_flock(int fd, int op)
{
	int rc;

	if (sk_kind(fd) == FD_LOCK && sk_fault == SIMK_LOCK_ENOSYS) {
		errno = ENOSYS;
		return -1;
	}
	rc = __real_flock(fd, op);
	if (rc == 0 && sk_kind(fd) == FD_LOCK)
		sk_event((op & LOCK_UN) ? 'U' : 'L', NULL, 0, 0, 0);
	return rc;
}

int __wrap_nanosleep(const struct timespec *req, struct timespec *rem)
{
	if (req != NULL)
		sk_slept += (unsigned long)req->tv_sec * 1000ul +
			    (unsigned long)(req->tv_nsec / 1000000L);
	if (rem != NULL) {
		rem->tv_sec = 0;
		rem->tv_nsec = 0;
	}
	return 0;
}

off_t __wrap_lseek(int fd, off_t off, int whence)
{
	if (sk_kind(fd) == FD_FLASH)
		sk_event('s', NULL, 0, 0, (uint32_t)off);
	if (sk_kind(fd) == FD_CHAR)
		sk_event('c', NULL, 0, 0, (uint32_t)off);
	return __real_lseek(fd, off, whence);
}
