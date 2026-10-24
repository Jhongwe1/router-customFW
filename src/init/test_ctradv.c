/* test_ctradv.c -- the counter advance (src/init/ctradv.c) against scratch
 * files standing in for spictl's five paths and /proc/rlxfw-boot, a simulated
 * `ctr` verb, two broker stand-ins and a clock that moves only when the code
 * under test sleeps.  notes/self-update.md § 5 is what it checks.
 *
 * ---------------------------------------------------------------------------
 * THE INSTRUMENTS, AND WHICH ONE COULD BE LYING
 * ---------------------------------------------------------------------------
 *
 *   --wrap  src/init/Makefile links this with -Wl,--wrap= open, close, write,
 *           flock and nanosleep (each as --wrap=<name>).  open and close keep track of which
 *           descriptors are the verbs' file; a write(2) on one of them is the
 *           simulated kernel and is recorded; flock records the lock taken
 *           and released and can answer ENOSYS; nanosleep sleeps nothing and
 *           counts what was asked (spictl_lock's 100 ms steps).  It sees
 *           calls, not syscalls: a write made another way (writev, a stdio
 *           stream) would not be recorded.
 *   events  ONE ordered list: 'L' the lock taken, 'U' released, 'v' a verb.
 *           Each verb also records whether a second descriptor could take the
 *           lock at that moment (it must not: "under the lock" is checked on
 *           the lock itself, not only on the order of the events).
 *   sim     the decisions are the install header's, compiled here unchanged:
 *           rlxfw_spi_inst_parse reads the line, ctr_tie, ctr_check,
 *           ctr_next, ctr_value and ctr_verify decide, and emit and
 *           emit_ctr print the node.  What rtl819x_spi_ctr_run adds around
 *           them -- the order, the four counters, the errno per reason -- is
 *           written again here, NOT shared with the glue, so a difference
 *           between the two is possible and is this test's first limit.
 *   broker  a function the environment calls (scripted answers, for the
 *           60 s), and a real AF_UNIX server answering one frame (for
 *           ctr_broker_status's own bk_call through src/lib/client.c).
 *   clock   the environment's: it moves by what the code asks to sleep and
 *           by a probe cost a case sets, never by itself.  The one real-time
 *           bound is the silent server's, written before the first run:
 *           [1.8, 3.5] s for CTR_BK_IO_S = 2.
 */

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "ctradv.h"
#include "client.h"
#include "brokerd.h"	/* BK_SOCK_PATH; cfg.h's CFG_FLASH_LOCK_S comes with it */

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

#include "rtl819x-spi-wrpolicy.h"
#include "rtl819x-spi-install.h"

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

#define CKS(a, b) do { \
	checks++; \
	if (strcmp((a), (b)) != 0) { \
		fails++; \
		printf("FAIL %s:%d  \"%s\" != \"%s\"\n", __FILE__, __LINE__, \
		       (a), (b)); \
	} \
} while (0)

/* a begins with the literal p */
#define CKP(a, p) do { \
	checks++; \
	if (strncmp((a), (p), strlen(p)) != 0) { \
		fails++; \
		printf("FAIL %s:%d  \"%s\" does not begin \"%s\"\n", __FILE__, \
		       __LINE__, (a), (p)); \
	} \
} while (0)

/* ------------------------------------------------------------------------- */
/* Paths                                                                     */
/* ------------------------------------------------------------------------- */

#define PMAX 320

static char g_dir[PMAX];
static char p_proc[PMAX], p_img[PMAX], p_lock[PMAX], p_flash[PMAX];
static char p_state[PMAX], p_boot[PMAX], p_sock[PMAX];
static struct spictl_paths g_sp;

static void mkpath(char *dst, const char *leaf)
{
	int n = snprintf(dst, PMAX, "%s/%s", g_dir, leaf);

	if (n < 0 || n >= PMAX) {
		printf("FAIL the scratch path is too long\n");
		exit(1);
	}
}

/* ------------------------------------------------------------------------- */
/* The recorder                                                              */
/* ------------------------------------------------------------------------- */

int __real_open(const char *path, int flags, ...);
int __real_close(int fd);
ssize_t __real_write(int fd, const void *buf, size_t n);
int __real_flock(int fd, int op);
int __real_nanosleep(const struct timespec *req, struct timespec *rem);

#define FDMAX 1024
#define EVMAX 64

struct ev {
	char kind;		/* 'L', 'U', 'v' */
	char text[64];
	int locked;		/* 'v': a second descriptor could NOT take the lock */
};

static unsigned char g_isproc[FDMAX];
static struct ev g_ev[EVMAX];
static int g_nev;
static int g_flock_enosys;
static unsigned long g_asked_ms;	/* what nanosleep was asked for */
static int sim_verb(const char *line, size_t n);

static void ev_add(char kind, const char *text, int locked)
{
	struct ev *e;

	if (g_nev >= EVMAX)
		return;
	e = &g_ev[g_nev++];
	memset(e, 0, sizeof *e);
	e->kind = kind;
	if (text != NULL)
		(void)snprintf(e->text, sizeof e->text, "%s", text);
	e->locked = locked;
}

static int ev_count(char kind)
{
	int i, n = 0;

	for (i = 0; i < g_nev; i++)
		if (g_ev[i].kind == kind)
			n++;
	return n;
}

int __wrap_open(const char *path, int flags, ...)
{
	int mode = 0, fd;

	if (flags & O_CREAT) {
		va_list ap;

		va_start(ap, flags);
		mode = va_arg(ap, int);
		va_end(ap);
	}
	fd = __real_open(path, flags, mode);
	if (fd >= 0 && fd < FDMAX)
		g_isproc[fd] = (strcmp(path, p_proc) == 0) ? 1 : 0;
	return fd;
}

int __wrap_close(int fd)
{
	if (fd >= 0 && fd < FDMAX)
		g_isproc[fd] = 0;
	return __real_close(fd);
}

/* Can a second descriptor take the lock right now?  1 = no (held). */
static int lock_is_held(void)
{
	int fd = __real_open(p_lock, O_RDWR | O_CREAT, 0600), held;

	if (fd < 0)
		return 0;
	held = (__real_flock(fd, LOCK_EX | LOCK_NB) != 0);
	if (!held)
		(void)__real_flock(fd, LOCK_UN);
	(void)__real_close(fd);
	return held;
}

ssize_t __wrap_write(int fd, const void *buf, size_t n)
{
	if (fd >= 0 && fd < FDMAX && g_isproc[fd]) {
		char line[128];
		size_t m = n < sizeof line - 1 ? n : sizeof line - 1;
		int rc;

		memcpy(line, buf, m);
		line[m] = '\0';
		ev_add('v', line, lock_is_held());
		rc = sim_verb(line, n);
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

	if (g_flock_enosys) {
		errno = ENOSYS;
		return -1;
	}
	rc = __real_flock(fd, op);
	if (rc == 0 && (op & LOCK_UN))
		ev_add('U', NULL, 0);
	else if (rc == 0 && (op & LOCK_EX))
		ev_add('L', NULL, 0);
	return rc;
}

int __wrap_nanosleep(const struct timespec *req, struct timespec *rem)
{
	(void)rem;
	g_asked_ms += (unsigned long)req->tv_sec * 1000ul +
		      (unsigned long)(req->tv_nsec / 1000000L);
	return 0;
}

/* ------------------------------------------------------------------------- */
/* The simulated kernel: rtl819x_spi_ctr_run, written again                  */
/* ------------------------------------------------------------------------- */

enum { SIM_NORMAL = 0, SIM_NOWRITE, SIM_STRAY, SIM_INTERLEAVE, SIM_GONE };

static struct {
	u8 flash[RLXFW_SPI_INST_CTR_BYTES];	/* the bitmap on the chip */
	int ho_ok;			/* rlxfw_boot_handoff()'s answer */
	u32 ho_ver;
	struct rlxfw_spi_inst_ctr_st c;
	unsigned long nwrites;
	int mode;
} g_sim;

/* rtl819x-spi.c's rtl819x_spi_inst_errno, the rows `ctr` reaches. */
static int sim_errno(int why)
{
	switch (why) {
	case RLXFW_SPI_INST_OK:			return 0;
	case RLXFW_SPI_INST_R_SYNTAX:		return EINVAL;
	case RLXFW_SPI_INST_R_POLICY:		return EPERM;
	case RLXFW_SPI_INST_R_NOMEM:		return ENOMEM;
	case RLXFW_SPI_INST_R_ENGINE:		return EIO;
	case RLXFW_SPI_INST_R_CTR_ABOVE:	return ERANGE;
	case RLXFW_SPI_INST_R_CTR_HANDOFF:	return EPERM;
	case RLXFW_SPI_INST_R_CTR_BELOW:	return ERANGE;
	case RLXFW_SPI_INST_R_CTR_MALFORMED:	return EILSEQ;
	case RLXFW_SPI_INST_R_CTR_CMP:		return EIO;
	default:				return EPROTO;
	}
}

/* /proc/rtl819x-spi-inst as rtl819x_spi_inst_node_read_proc prints it. */
static void sim_node(void)
{
	static const struct rlxfw_spi_inst_st st0;
	static const struct rlxfw_spi_inst_img im0;
	static const struct rlxfw_spi_inst_probe pr0;
	char page[4096];
	int len = 0, fd;
	ssize_t w;

	len += sprintf(page + len, "n_writes %lu\n", g_sim.nwrites);
	len += rlxfw_spi_inst_emit(page + len, &st0, &im0, &pr0, 0x20u,
				   RLXFW_SPI_WR_ERASE_GRAIN, 10000u);
	len += rlxfw_spi_inst_emit_ctr(page + len, &g_sim.c);
	if (len > 3072) {
		printf("FAIL the simulated node is %d bytes, over one read\n", len);
		fails++;
	}
	fd = __real_open(p_state, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0)
		return;
	w = __real_write(fd, page, (size_t)len);
	(void)w;
	(void)__real_close(fd);
}

static int sim_ctr_run(const char *line)
{
	struct rlxfw_spi_inst_ctr_st *c = &g_sim.c;
	struct rlxfw_spi_inst_req rq;
	u8 bm[RLXFW_SPI_INST_CTR_BYTES], rb[RLXFW_SPI_INST_CTR_BYTES];
	u32 nops, b;
	int why, mal = 0;

	why = rlxfw_spi_inst_parse(line, &rq);
	c->attempts++;
	c->ran = 1;
	c->malformed = 0;
	c->cur = c->read = c->pp = 0u;
	c->newv = rq.ctr_n;
	if (why)
		goto refuse;
	why = rlxfw_spi_inst_ctr_tie(rq.ctr_n, g_sim.ho_ok, g_sim.ho_ver);
	if (why)
		goto refuse;
	memcpy(bm, g_sim.flash, sizeof bm);
	why = rlxfw_spi_inst_ctr_check(bm, rq.ctr_n, &c->cur, &mal, &nops);
	c->malformed = mal;
	if (why)
		goto refuse;
	if (nops == 0u) {
		c->read = c->cur;
		c->done++;
		goto out;
	}
	for (b = rlxfw_spi_inst_ctr_next(bm, rq.ctr_n, 0u); b < rq.ctr_n;
	     b = rlxfw_spi_inst_ctr_next(bm, rq.ctr_n, b + 1u)) {
		u32 a = rlxfw_spi_inst_ctr_addr(RLXFW_SPI_INST_STATE, b);

		/* JEDEC PP: bits go from 1 to 0 only */
		g_sim.flash[a - RLXFW_SPI_INST_STATE] &= rlxfw_spi_inst_ctr_value(b);
		g_sim.nwrites++;
		c->pp++;
	}
	if (g_sim.mode == SIM_STRAY)	/* a program that cleared one bit more */
		g_sim.flash[rq.ctr_n >> 3] &= (u8)~(0x80u >> (rq.ctr_n & 7u));
	memcpy(rb, g_sim.flash, sizeof rb);
	c->read = rlxfw_spi_inst_ctr_decode(rb, &mal);
	why = rlxfw_spi_inst_ctr_verify(rb, rq.ctr_n);
	if (why)
		goto fail;
	c->done++;
	goto out;
refuse:
	c->refused++;
	goto out;
fail:
	c->failed++;
out:
	c->reason = why;
	return why ? -sim_errno(why) : 0;
}

/* write_proc: the line, `ctr` dispatched by prefix to the install parser. */
static int sim_verb(const char *line, size_t n)
{
	int rc;

	if (n == 0 || n > RLXFW_SPI_INST_LINE_MAX - 1)
		return -EINVAL;
	if (g_sim.mode == SIM_NOWRITE)
		return -EINVAL;	/* no CONFIG_MTD_RTL819X_WRITE: no ctr at all */
	if (strncmp(line, "ctr", 3) != 0)
		return -EINVAL;
	if (g_sim.mode == SIM_INTERLEAVE)	/* a lock-ignoring writer's verb */
		(void)sim_ctr_run(line);
	rc = sim_ctr_run(line);
	sim_node();
	if (g_sim.mode == SIM_GONE)
		(void)unlink(p_state);
	return rc;
}

static void sim_value(u32 n)
{
	u32 b;

	memset(g_sim.flash, 0xFF, sizeof g_sim.flash);
	for (b = 0; b < n; b++)
		g_sim.flash[b >> 3] &= (u8)~(0x80u >> (b & 7u));
}

static u32 sim_decode(int *mal)
{
	return rlxfw_spi_inst_ctr_decode(g_sim.flash, mal);
}

/* ------------------------------------------------------------------------- */
/* The environment                                                           */
/* ------------------------------------------------------------------------- */

static long g_now;
static long g_probe_cost;	/* clock per broker_up call */
static int g_clock_frozen;	/* sleep does not move the clock */
static int g_up_after;		/* answers from this call on; 0 = never */
static int g_up_calls;
static long g_slept;
static char g_said[8][CTR_LINE_MAX];
static int g_nsaid;

static int f_up(void *ctx)
{
	(void)ctx;
	g_up_calls++;
	g_now += g_probe_cost;
	return (g_up_after > 0 && g_up_calls >= g_up_after) ? 1 : 0;
}

static long f_now(void *ctx)
{
	(void)ctx;
	return g_now;
}

static void f_sleep(void *ctx, long ms)
{
	(void)ctx;
	g_slept += ms;
	if (!g_clock_frozen)
		g_now += ms;
}

static void f_say(void *ctx, const char *s)
{
	(void)ctx;
	if (g_nsaid < 8)
		(void)snprintf(g_said[g_nsaid], CTR_LINE_MAX, "%s", s);
	g_nsaid++;
}

static void put_file(const char *path, const char *text)
{
	int fd = __real_open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	ssize_t w;

	if (fd < 0)
		return;
	w = __real_write(fd, text, strlen(text));
	(void)w;
	(void)__real_close(fd);
}

/* A fresh case: an erased bitmap, a valid handoff for `ver`, a broker that
 * answers at once, the node as the kernel would print it before any `ctr`. */
static void setup(const char *boot, u32 ver)
{
	memset(&g_sim, 0, sizeof g_sim);
	sim_value(0);
	g_sim.ho_ok = 1;
	g_sim.ho_ver = ver;
	g_sim.mode = SIM_NORMAL;
	sim_node();
	if (boot != NULL)
		put_file(p_boot, boot);
	else
		(void)unlink(p_boot);
	g_nev = 0;
	g_flock_enosys = 0;
	g_asked_ms = 0;
	g_now = 0;
	g_probe_cost = 0;
	g_clock_frozen = 0;
	g_up_after = 1;
	g_up_calls = 0;
	g_slept = 0;
	g_nsaid = 0;
	memset(g_said, 0, sizeof g_said);
}

static void env(struct ctr_env *e)
{
	memset(e, 0, sizeof *e);
	e->sp = &g_sp;
	e->boot_path = p_boot;
	e->broker_up = f_up;
	e->now_ms = f_now;
	e->sleep_ms = f_sleep;
	e->say = f_say;
	e->ctx = NULL;
	e->lock_s = CTR_LOCK_S;
}

static int run(void)
{
	struct ctr_env e;

	env(&e);
	return ctr_advance(&e);
}

/* Every outcome: exactly one console line, and it is a `rlxfw: ctr ` line. */
static void ck_one_line(void)
{
	CK(g_nsaid == 1);
	CK(strncmp(g_said[0], "rlxfw: ctr ", 11) == 0);
}

/* Exactly lock, ONE verb `want` (written while the lock was held), unlock. */
static void ck_one_verb_locked(const char *want)
{
	CK(g_nev == 3);
	CK(g_nev == 3 && g_ev[0].kind == 'L');
	CK(g_nev == 3 && g_ev[1].kind == 'v');
	CK(g_nev == 3 && g_ev[2].kind == 'U');
	CK(ev_count('v') == 1);
	CK(g_nev >= 2 && strcmp(g_ev[1].text, want) == 0);
	CK(g_nev >= 2 && g_ev[1].locked == 1);
}

static void ck_nothing(void)
{
	CK(ev_count('v') == 0);
	CK(ev_count('L') == 0);
	CK(ev_count('U') == 0);
}

/* ------------------------------------------------------------------------- */
/* Cases                                                                     */
/* ------------------------------------------------------------------------- */

static void t_parse(void)
{
	static const struct {
		const char *text;
		int want;
		char slot;
		uint32_t ver;
	} v[] = {
		{ "none\n", CTR_BOOT_NONE, 0, 0 },
		{ "slot A ver 1\n", CTR_BOOT_SLOT, 'A', 1u },
		{ "slot B ver 6\n", CTR_BOOT_SLOT, 'B', 6u },
		{ "slot B ver 4096\n", CTR_BOOT_SLOT, 'B', 4096u },
		{ "slot B ver 4294967294\n", CTR_BOOT_SLOT, 'B', 4294967294u },
		{ "slot B ver 4294967295\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 4294967296\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 12345678901\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 0\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 06\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot C ver 6\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot b ver 6\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 6", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 6 \n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B  ver 6\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver -6\n", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 6\nx", CTR_BOOT_BAD, 0, 0 },
		{ "slot B ver 6\n\n", CTR_BOOT_BAD, 0, 0 },
		{ "none", CTR_BOOT_BAD, 0, 0 },
		{ "none\n\n", CTR_BOOT_BAD, 0, 0 },
		{ "None\n", CTR_BOOT_BAD, 0, 0 },
		{ "", CTR_BOOT_BAD, 0, 0 },
	};
	size_t i;

	for (i = 0; i < sizeof v / sizeof v[0]; i++) {
		char slot = '?';
		uint32_t ver = 777u;
		int r = ctr_parse_boot(v[i].text, strlen(v[i].text), &slot, &ver);

		if (r != v[i].want)
			printf("      parse case %u: \"%s\" -> %d\n", (unsigned)i,
			       v[i].text, r);
		CK(r == v[i].want);
		if (v[i].want == CTR_BOOT_SLOT) {
			CK(slot == v[i].slot);
			CK(ver == v[i].ver);
		} else {
			CK(slot == '?');	/* nothing set unless SLOT */
			CK(ver == 777u);
		}
	}
	{
		char slot = '?';
		uint32_t ver = 0;

		CK(ctr_parse_boot(NULL, 5, &slot, &ver) == CTR_BOOT_BAD);
		CK(ctr_parse_boot("none\n", 5, NULL, &ver) == CTR_BOOT_BAD);
	}
}

static void mkchild(struct sv_child *c, const char *name)
{
	memset(c, 0, sizeof *c);
	(void)snprintf(c->name, sizeof c->name, "%s", name);
	c->path = "/x";
}

static void t_fork_due(void)
{
	struct sv_set s;

	memset(&s, 0, sizeof s);
	mkchild(&s.c[0], "brokerd");
	mkchild(&s.c[1], "httpd");
	s.n = 2;
	sv_arm(&s.c[0], 0);
	sv_arm(&s.c[1], 0);

	/* armed but not yet started: not yet */
	CK(ctr_fork_due(&s, 1) == 0);
	/* `lan up` not printed: never, whatever brokerd does */
	CK(ctr_fork_due(&s, 0) == CTR_FORK_NOLAN);
	sv_on_start(&s.c[0], 41, 5);
	CK(ctr_fork_due(&s, 0) == CTR_FORK_NOLAN);
	/* started once: now */
	CK(ctr_fork_due(&s, 1) == 1);
	/* and still once it has exited and waits for its restart */
	CK(sv_on_exit(&s.c[0], 0, 20000) == SV_WAIT);
	CK(ctr_fork_due(&s, 1) == 1);

	/* never started and never will: SV_ABSENT, SV_OFF, no row */
	s.c[0].state = SV_ABSENT;
	s.c[0].starts = 0;
	CK(ctr_fork_due(&s, 1) == CTR_FORK_NOBROKER);
	s.c[0].state = SV_OFF;
	CK(ctr_fork_due(&s, 1) == CTR_FORK_NOBROKER);
	s.c[0].state = SV_GIVENUP;	/* a SIGHUP can re-arm it: wait */
	CK(ctr_fork_due(&s, 1) == 0);
	(void)snprintf(s.c[0].name, sizeof s.c[0].name, "brokerdx");
	CK(ctr_fork_due(&s, 1) == CTR_FORK_NOBROKER);
	CK(ctr_fork_due(NULL, 1) == CTR_FORK_NOBROKER);

	CK(strncmp(ctr_fork_why(CTR_FORK_NOLAN), "rlxfw: ctr not advanced: ",
		   25) == 0);
	CK(strncmp(ctr_fork_why(CTR_FORK_NOBROKER),
		   "rlxfw: ctr not advanced: ", 25) == 0);
}

static void t_none(void)
{
	setup("none\n", 6u);
	CK(run() == CTR_R_NOHANDOFF);
	ck_nothing();
	ck_one_line();
	CKS(g_said[0], "rlxfw: ctr not advanced: no handoff (not started by "
		       "rlxboot)");
	CK(g_sim.c.attempts == 0u);
	CK(g_sim.nwrites == 0ul);
	CK(g_up_calls == 1);	/* "up" was decided first */
}

static void t_ok(void)
{
	int mal = 1;

	setup("slot B ver 6\n", 6u);
	CK(run() == CTR_R_OK);
	ck_one_verb_locked("ctr 6");
	ck_one_line();
	CKS(g_said[0], "rlxfw: ctr 0 -> 6 OK pp=6");
	CK(sim_decode(&mal) == 6u && mal == 0);
	CK(g_sim.nwrites == 6ul);
	CK(g_sim.c.attempts == 1u && g_sim.c.done == 1u);

	/* 6 -> 7: one program */
	setup("slot A ver 7\n", 7u);
	sim_value(6);
	sim_node();
	CK(run() == CTR_R_OK);
	ck_one_verb_locked("ctr 7");
	CKS(g_said[0], "rlxfw: ctr 6 -> 7 OK pp=1");
	CK(sim_decode(&mal) == 7u && mal == 0);
	CK(g_sim.nwrites == 1ul);
}

static void t_same(void)
{
	int mal = 1;

	setup("slot B ver 6\n", 6u);
	sim_value(6);
	sim_node();
	CK(run() == CTR_R_SAME);
	ck_one_verb_locked("ctr 6");
	ck_one_line();
	CKS(g_said[0], "rlxfw: ctr 6 -> 6 SAME pp=0");
	CK(g_sim.nwrites == 0ul);
	CK(sim_decode(&mal) == 6u && mal == 0);
}

static void t_refused(void)
{
	char want[CTR_LINE_MAX];
	u8 before[RLXFW_SPI_INST_CTR_BYTES];

	/* below: the bitmap reads 7, the handoff is 6 */
	setup("slot B ver 6\n", 6u);
	sim_value(7);
	sim_node();
	memcpy(before, g_sim.flash, sizeof before);
	CK(run() == CTR_R_REFUSED);
	ck_one_verb_locked("ctr 6");
	ck_one_line();
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: CTR_BELOW "
		       "ver=6 cur=7 new=6 errno=%d", ERANGE);
	CKS(g_said[0], want);
	CK(g_sim.nwrites == 0ul);
	CK(memcmp(before, g_sim.flash, sizeof before) == 0);

	/* the tie: /proc/rlxfw-boot says 6, the kernel's latch says none */
	setup("slot B ver 6\n", 6u);
	g_sim.ho_ok = 0;
	CK(run() == CTR_R_REFUSED);
	ck_one_verb_locked("ctr 6");
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: "
		       "CTR_HANDOFF ver=6 cur=0 new=6 errno=%d", EPERM);
	CKS(g_said[0], want);
	CK(g_sim.nwrites == 0ul);

	/* malformed: a zero at bit 10, above the value asked */
	setup("slot B ver 6\n", 6u);
	g_sim.flash[1] &= (u8)~(0x80u >> 2);
	sim_node();
	memcpy(before, g_sim.flash, sizeof before);
	CK(run() == CTR_R_REFUSED);
	ck_one_verb_locked("ctr 6");
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: "
		       "CTR_MALFORMED ver=6 cur=1 new=6 errno=%d", EILSEQ);
	CKS(g_said[0], want);
	CK(memcmp(before, g_sim.flash, sizeof before) == 0);

	/* five digits: the kernel's parser takes four */
	setup("slot B ver 70000\n", 70000u);
	CK(run() == CTR_R_REFUSED);
	ck_one_verb_locked("ctr 70000");
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: SYNTAX "
		       "ver=70000 cur=0 new=0 errno=%d", EINVAL);
	CKS(g_said[0], want);

	/* above the bitmap */
	setup("slot B ver 5000\n", 5000u);
	CK(run() == CTR_R_REFUSED);
	ck_one_verb_locked("ctr 5000");
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: CTR_ABOVE "
		       "ver=5000 cur=0 new=0 errno=%d", ERANGE);
	CKS(g_said[0], want);
	CK(g_sim.nwrites == 0ul);
}

static void t_failed(void)
{
	char want[CTR_LINE_MAX];

	setup("slot B ver 6\n", 6u);
	g_sim.mode = SIM_STRAY;
	CK(run() == CTR_R_FAILED);
	ck_one_verb_locked("ctr 6");	/* and no retry */
	ck_one_line();
	(void)snprintf(want, sizeof want, "rlxfw: ctr FAILED: CTR_CMP ver=6 "
		       "cur=0 new=6 read=7 pp=6 errno=%d", EIO);
	CKS(g_said[0], want);
	CK(g_sim.c.failed == 1u);
}

static void t_up(void)
{
	/* never: 121 tries, 60,000 ms, nothing at all written */
	setup("slot B ver 6\n", 6u);
	g_up_after = 0;
	CK(run() == CTR_R_NOBROKER);
	ck_nothing();
	ck_one_line();
	CKS(g_said[0], "rlxfw: ctr not advanced: brokerd did not answer STATUS "
		       "in 60 s");
	CK(g_up_calls == 1 + (int)(CTR_UP_BUDGET_MS / CTR_UP_STEP_MS));
	CK(g_up_calls == 121);
	CK(g_slept == CTR_UP_BUDGET_MS);
	CK(g_now == 60000L);
	CK(g_sim.c.attempts == 0u);

	/* the fifth try answers: 2,000 ms, then the advance */
	setup("slot B ver 6\n", 6u);
	g_up_after = 5;
	CK(run() == CTR_R_OK);
	CK(g_up_calls == 5);
	CK(g_slept == 2000L);
	ck_one_verb_locked("ctr 6");

	/* a clock that never moves: the try count still ends it */
	setup("slot B ver 6\n", 6u);
	g_up_after = 0;
	g_clock_frozen = 1;
	CK(run() == CTR_R_NOBROKER);
	CK(g_up_calls == 121);
	ck_nothing();

	/* each try costs 2 s of clock: the clock ends it, at 25 tries (each
	 * cycle 2,500 ms; 2,000 + 24 x 2,500 = 62,000 >= 60,000) */
	setup("slot B ver 6\n", 6u);
	g_up_after = 0;
	g_probe_cost = 2000L;
	CK(run() == CTR_R_NOBROKER);
	CK(g_up_calls == 25);
	CK(g_now == 62000L);
	ck_nothing();
}

static void t_lock(void)
{
	int other;

	/* held by another writer: 300 tries of 100 ms, then no verb */
	setup("slot B ver 6\n", 6u);
	other = __real_open(p_lock, O_RDWR | O_CREAT, 0600);
	CK(other >= 0);
	CK(other >= 0 && __real_flock(other, LOCK_EX | LOCK_NB) == 0);
	CK(run() == CTR_R_LOCK);
	CK(ev_count('v') == 0);
	CK(g_asked_ms == (unsigned long)CTR_LOCK_S * 1000ul);
	ck_one_line();
	CKS(g_said[0], "rlxfw: ctr not advanced: flock: held by another writer "
		       "past the timeout");
	CK(g_sim.c.attempts == 0u);
	/* released: the same setup is permitted */
	if (other >= 0) {
		(void)__real_flock(other, LOCK_UN);
		(void)__real_close(other);
	}
	setup("slot B ver 6\n", 6u);
	CK(run() == CTR_R_OK);
	ck_one_verb_locked("ctr 6");

	/* no CONFIG_FILE_LOCKING: refused at once, no retry, no verb */
	setup("slot B ver 6\n", 6u);
	g_flock_enosys = 1;
	CK(run() == CTR_R_LOCK);
	CK(ev_count('v') == 0);
	CK(g_asked_ms == 0ul);
	CKS(g_said[0], "rlxfw: ctr not advanced: flock: ENOSYS, the kernel has "
		       "no CONFIG_FILE_LOCKING");
	g_flock_enosys = 0;
}

static void t_unreadable(void)
{
	char want[CTR_LINE_MAX];

	/* no handoff node */
	setup(NULL, 6u);
	CK(run() == CTR_R_BOOTREAD);
	ck_nothing();
	ck_one_line();
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: "
		       "/proc/rlxfw-boot unreadable (errno=%d)", ENOENT);
	CKS(g_said[0], want);

	/* a node that is neither form */
	setup("slot B ver 06\n", 6u);
	CK(run() == CTR_R_BOOTREAD);
	ck_nothing();
	CKS(g_said[0], "rlxfw: ctr not advanced: /proc/rlxfw-boot is neither "
		       "`none` nor `slot X ver N`");

	/* no counter node before the verb: the lock is taken and released,
	 * and no verb is written */
	setup("slot B ver 6\n", 6u);
	(void)unlink(p_state);
	CK(run() == CTR_R_STATE);
	CK(ev_count('v') == 0);
	CK(ev_count('L') == 1 && ev_count('U') == 1);
	ck_one_line();
	CKP(g_said[0], "rlxfw: ctr not advanced: /proc/rtl819x-spi-inst "
		       "unreadable before the verb");

	/* the node gone after the verb: the verdict is not guessed */
	setup("slot B ver 6\n", 6u);
	g_sim.mode = SIM_GONE;
	CK(run() == CTR_R_UNKNOWN);
	ck_one_verb_locked("ctr 6");
	CKP(g_said[0], "rlxfw: ctr verdict unknown: /proc/rtl819x-spi-inst "
		       "unreadable after the verb");
}

static void t_attribution(void)
{
	char want[CTR_LINE_MAX];

	/* a kernel without the write path: the verb never reaches `ctr` */
	setup("slot B ver 6\n", 6u);
	g_sim.mode = SIM_NOWRITE;
	CK(run() == CTR_R_UNRAN);
	ck_one_verb_locked("ctr 6");
	ck_one_line();
	(void)snprintf(want, sizeof want, "rlxfw: ctr not advanced: the verb did "
		       "not reach the counter (ctr_attempts unchanged; write "
		       "%d)", -EINVAL);
	CKS(g_said[0], want);
	CK(g_sim.nwrites == 0ul);

	/* a lock-ignoring writer's `ctr` lands with ours: two attempts, so
	 * the fields are not attributed to this verb */
	setup("slot B ver 6\n", 6u);
	g_sim.mode = SIM_INTERLEAVE;
	CK(run() == CTR_R_UNKNOWN);
	ck_one_verb_locked("ctr 6");
	CKP(g_said[0], "rlxfw: ctr verdict unknown: ctr_attempts +2 ");
}

/* ------------------------------------------------------------------------- */
/* The production probe against a real socket                                */
/* ------------------------------------------------------------------------- */

static long real_ms(void)
{
	struct timespec ts;

	(void)clock_gettime(CLOCK_MONOTONIC, &ts);
	return (long)ts.tv_sec * 1000L + (long)(ts.tv_nsec / 1000000L);
}

/* One frame: read the request, check it is a bare STATUS, answer `status`
 * (or answer nothing when status < 0).  Exit 0 when the request was right. */
static void serve_one(int lfd, int status)
{
	uint8_t in[PROTO_REQ_MAX], out[PROTO_RESP_MAX];
	struct proto_req rq;
	struct proto_resp rs;
	size_t got = 0;
	int c, n, ok;

	c = accept(lfd, NULL, NULL);
	if (c < 0)
		_exit(2);
	for (;;) {
		ssize_t r = read(c, in + got, sizeof in - got);

		if (r <= 0)
			break;
		got += (size_t)r;
	}
	ok = proto_decode_req(in, got, &rq) == PROTO_REQ_HDR &&
	     rq.op == OP_STATUS && rq.body_len == 0u;
	if (status < 0) {
		(void)pause();
		_exit(ok ? 0 : 3);
	}
	memset(&rs, 0, sizeof rs);
	rs.version = PROTO_VERSION;
	rs.status = (uint8_t)status;
	rs.body_len = 0u;
	n = proto_encode_resp(&rs, out, sizeof out);
	if (n > 0 && __real_write(c, out, (size_t)n) != n)
		_exit(4);
	(void)__real_close(c);
	_exit(ok ? 0 : 3);
}

static pid_t server(int status)
{
	struct sockaddr_un sa;
	int lfd;
	pid_t pid;

	(void)unlink(p_sock);
	lfd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (lfd < 0)
		return -1;
	memset(&sa, 0, sizeof sa);
	sa.sun_family = AF_UNIX;
	if (snprintf(sa.sun_path, sizeof sa.sun_path, "%s", p_sock) >=
	    (int)sizeof sa.sun_path) {
		(void)__real_close(lfd);
		return -1;
	}
	if (bind(lfd, (struct sockaddr *)&sa, sizeof sa) != 0 ||
	    listen(lfd, 1) != 0) {
		(void)__real_close(lfd);
		return -1;
	}
	pid = fork();
	if (pid == 0)
		serve_one(lfd, status);
	(void)__real_close(lfd);
	return pid;
}

/* waitpid with a deadline, so a server that never got its connection cannot
 * hang the suite: killed and reported instead.  1 exited, 0 killed. */
static int wait_bounded(pid_t pid, int ms, int *st)
{
	long t0 = real_ms();

	for (;;) {
		pid_t r = waitpid(pid, st, WNOHANG);

		if (r == pid)
			return 1;
		if (r < 0)
			return 0;
		if (real_ms() - t0 >= ms) {
			(void)kill(pid, SIGKILL);
			(void)waitpid(pid, st, 0);
			return 0;
		}
		(void)poll(NULL, 0, 10);
	}
}

static void t_broker_real(void)
{
	pid_t pid;
	int st = -1;
	long t0, dt;

	/* relative to the working directory, so a long $O cannot push it past
	 * sun_path (bk_call refuses that with ENAMETOOLONG) */
	CK(strlen(p_sock) < sizeof(((struct sockaddr_un *)0)->sun_path));

	/* no socket at all: not up, and at once */
	(void)unlink(p_sock);
	t0 = real_ms();
	CK(ctr_broker_status(p_sock) == 0);
	CK(real_ms() - t0 < 1000L);

	/* a broker answering ST_OK to a bare STATUS: up */
	pid = server(ST_OK);
	CK(pid > 0);
	CK(ctr_broker_status(p_sock) == 1);
	CK(pid > 0 && wait_bounded(pid, 5000, &st) == 1);
	CK(WIFEXITED(st) && WEXITSTATUS(st) == 0);	/* it was a bare STATUS */

	/* answering, but not OK: not up */
	pid = server(ST_PERM);
	CK(pid > 0);
	CK(ctr_broker_status(p_sock) == 0);
	CK(pid > 0 && wait_bounded(pid, 5000, &st) == 1);
	CK(WIFEXITED(st) && WEXITSTATUS(st) == 0);

	/* accepting and silent: not up, after CTR_BK_IO_S and not the client's
	 * default 15 s.  Bounds written before the first run: [1.8, 3.5] s. */
	pid = server(-1);
	CK(pid > 0);
	t0 = real_ms();
	CK(ctr_broker_status(p_sock) == 0);
	dt = real_ms() - t0;
	printf("      silent broker: not up after %ld ms\n", dt);
	CK(dt >= 1800L && dt <= 3500L);
	if (pid > 0) {
		(void)kill(pid, SIGKILL);
		(void)waitpid(pid, &st, 0);
	}
	(void)unlink(p_sock);
}

/* The device's environment names the device's paths and constants. */
static void t_env_dev(void)
{
	struct ctr_env e;

	ctr_env_dev(&e);
	CK(e.sp == &spictl_dev);
	CK(e.boot_path != NULL && strcmp(e.boot_path, "/proc/rlxfw-boot") == 0);
	CK(e.lock_s == CTR_LOCK_S);
	CK(e.broker_up != NULL && e.now_ms != NULL && e.sleep_ms != NULL &&
	   e.say != NULL);
	CK(strcmp(spictl_dev.state, "/proc/rtl819x-spi-inst") == 0);
	CK(strcmp(spictl_dev.proc, "/proc/rtl819x-spi") == 0);
	CK(strcmp(spictl_dev.lock, "/run/rlxfw-flash.lock") == 0);
	/* the two owners of two strings and one number */
	CK(strcmp(CTR_BROKER_SOCK, BK_SOCK_PATH) == 0);
	CK(CTR_LOCK_S == CFG_FLASH_LOCK_S);
	CK(CTR_UP_STEP_MS == 500L && CTR_UP_BUDGET_MS == 60000L);
}

int main(void)
{
	char tmpl[PMAX], *abs;

	(void)signal(SIGPIPE, SIG_IGN);
	(void)snprintf(tmpl, sizeof tmpl, "%s", "./ctradv-XXXXXX");
	if (mkdtemp(tmpl) == NULL) {
		printf("FAIL mkdtemp: errno %d\n", errno);
		return 1;
	}
	abs = realpath(tmpl, NULL);
	if (abs == NULL || strlen(abs) + 16 >= sizeof g_dir) {
		printf("FAIL realpath: errno %d\n", errno);
		free(abs);
		return 1;
	}
	if (snprintf(g_dir, sizeof g_dir, "%s", abs) >= (int)sizeof g_dir) {
		free(abs);
		return 1;
	}
	free(abs);
	mkpath(p_proc, "proc");
	mkpath(p_img, "img");
	mkpath(p_lock, "lock");
	mkpath(p_flash, "flash");
	mkpath(p_state, "state");
	mkpath(p_boot, "boot");
	if (snprintf(p_sock, sizeof p_sock, "%s/sock", tmpl) >= (int)sizeof p_sock)
		return 1;
	put_file(p_proc, "");
	g_sp.proc = p_proc;
	g_sp.img = p_img;
	g_sp.lock = p_lock;
	g_sp.flash = p_flash;
	g_sp.state = p_state;

	t_parse();
	t_fork_due();
	t_none();
	t_ok();
	t_same();
	t_refused();
	t_failed();
	t_up();
	t_lock();
	t_unreadable();
	t_attribution();
	t_broker_real();
	t_env_dev();

	(void)unlink(p_proc);
	(void)unlink(p_state);
	(void)unlink(p_boot);
	(void)unlink(p_lock);
	(void)rmdir(g_dir);
	printf("test_ctradv: %d checks, %d failures\n", checks, fails);
	return fails == 0 ? 0 : 1;
}
