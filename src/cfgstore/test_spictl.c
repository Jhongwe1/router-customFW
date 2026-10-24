/* test_spictl.c -- src/lib/spictl.c against real files: every refusal shown
 * refusing and every path shown permitting (SPEC-S144-U §§ 2 and 5).
 *
 * argv[1] a scratch directory on a filesystem that keeps modes (ext4).
 *
 * ---------------------------------------------------------------------------
 * THE INSTRUMENTS, AND WHICH ONE COULD BE LYING
 * ---------------------------------------------------------------------------
 *
 *   --wrap  src/cfgstore/Makefile links this program with
 *           -Wl,--wrap=open,--wrap=write,--wrap=flock,--wrap=nanosleep, so
 *           every call spictl.o makes to those four symbols comes here first:
 *           each open and each write(2) is recorded with its fd and length,
 *           the next write can be made to fail or to come back short, and
 *           flock can be made to answer ENOSYS -- the kernel without
 *           CONFIG_FILE_LOCKING, which no host here is.  It sees calls, not
 *           syscalls: a write(2) reached another way (writev, a stdio
 *           stream) would not be recorded.
 *   syscw   the kernel's own count of this process's write-family syscalls,
 *           /proc/self/io, read before and after: the second source for
 *           "exactly one write(2) per verb", blind to how the call was made.
 *           Its positive control is two plain writes counted as two.
 *   time    CLOCK_MONOTONIC around the lock, for "times out after about its
 *           timeout": bounds written before the first run, [1.0, 2.0] s for
 *           a 1 s timeout and [0.4, 1.5] s for a lock released at 0.5 s.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "spictl.h"
#include "test_util.h"

#define DIRMAX 400

static char g_dir[DIRMAX];

/* ------------------------------------------------------------------------- */
/* The recorder                                                              */
/* ------------------------------------------------------------------------- */

int __real_open(const char *path, int flags, ...);
ssize_t __real_write(int fd, const void *buf, size_t n);
int __real_flock(int fd, int op);
int __real_nanosleep(const struct timespec *req, struct timespec *rem);

#define REC_MAX 64

struct wrec {
	int fd;
	size_t len;
	char head[160];
};

static struct wrec g_w[REC_MAX];
static int g_nw;
static int g_nopen;
static int g_nsleep;
static int g_nflock;
static int g_wfail_at = -1, g_wfail_errno;	/* the Nth write fails */
static int g_wshort_at = -1;			/* the Nth write is short */
static int g_flock_enosys;

static void rec_reset(void)
{
	g_nw = 0;
	g_nopen = 0;
	g_nsleep = 0;
	g_nflock = 0;
	g_wfail_at = -1;
	g_wfail_errno = 0;
	g_wshort_at = -1;
	g_flock_enosys = 0;
}

int __wrap_open(const char *path, int flags, ...)
{
	int mode = 0;

	if (flags & O_CREAT) {
		va_list ap;

		va_start(ap, flags);
		mode = va_arg(ap, int);
		va_end(ap);
	}
	g_nopen++;
	return __real_open(path, flags, mode);
}

ssize_t __wrap_write(int fd, const void *buf, size_t n)
{
	int k = g_nw;

	if (g_nw < REC_MAX) {
		size_t m = (n < sizeof g_w[0].head - 1) ? n : sizeof g_w[0].head - 1;

		g_w[g_nw].fd = fd;
		g_w[g_nw].len = n;
		memcpy(g_w[g_nw].head, buf, m);
		g_w[g_nw].head[m] = '\0';
		g_nw++;
	}
	if (k == g_wfail_at) {
		errno = g_wfail_errno;
		return -1;
	}
	if (k == g_wshort_at && n > 1)
		return __real_write(fd, buf, n - 1);
	return __real_write(fd, buf, n);
}

int __wrap_flock(int fd, int op)
{
	g_nflock++;
	if (g_flock_enosys) {
		errno = ENOSYS;
		return -1;
	}
	return __real_flock(fd, op);
}

int __wrap_nanosleep(const struct timespec *req, struct timespec *rem)
{
	g_nsleep++;
	return __real_nanosleep(req, rem);
}

/* ------------------------------------------------------------------------- */

static long ms_now(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (long)ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

static void nap_ms(long ms)
{
	struct timespec ts;

	ts.tv_sec = ms / 1000L;
	ts.tv_nsec = (ms % 1000L) * 1000000L;
	(void)__real_nanosleep(&ts, NULL);
}

/* syscw from /proc/self/io, or -1. */
static long syscw(void)
{
	char b[512];
	char *p;
	int fd = __real_open("/proc/self/io", O_RDONLY);
	ssize_t n;

	if (fd < 0)
		return -1;
	n = read(fd, b, sizeof b - 1);
	close(fd);
	if (n <= 0)
		return -1;
	b[n] = '\0';
	p = strstr(b, "syscw: ");
	if (p == NULL)
		return -1;
	return strtol(p + 7, NULL, 10);
}

static void path_in(char *out, size_t cap, const char *name)
{
	(void)snprintf(out, cap, "%s/%s", g_dir, name);
}

static int put_file(const char *path, const void *buf, size_t n)
{
	int fd = __real_open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	ssize_t w;

	if (fd < 0)
		return -1;
	w = n ? __real_write(fd, buf, n) : 0;
	close(fd);
	return (w == (ssize_t)n) ? 0 : -1;
}

static long get_file(const char *path, void *buf, size_t cap)
{
	int fd = __real_open(path, O_RDONLY);
	ssize_t n;

	if (fd < 0)
		return -1;
	n = read(fd, buf, cap);
	close(fd);
	return (long)n;
}

/* ------------------------------------------------------------------------- */
/* The lock                                                                  */
/* ------------------------------------------------------------------------- */

/* A child that tries the lock and reports rc, elapsed ms and sleeps. */
struct lockrep {
	int rc;
	long ms;
	int sleeps;
};

static int child_lock(const struct spictl_paths *p, unsigned t,
		      struct lockrep *out)
{
	int pfd[2];
	pid_t pid;
	int st = 0;
	ssize_t n;

	if (pipe(pfd) != 0)
		return -1;
	pid = fork();
	if (pid < 0)
		return -1;
	if (pid == 0) {
		struct lockrep r;
		long t0;

		close(pfd[0]);
		g_nsleep = 0;
		t0 = ms_now();
		r.rc = spictl_lock(p, t);
		r.ms = ms_now() - t0;
		r.sleeps = g_nsleep;
		n = __real_write(pfd[1], &r, sizeof r);
		if (r.rc >= 0)
			spictl_unlock(r.rc);
		_exit(n == (ssize_t)sizeof r ? 0 : 1);
	}
	close(pfd[1]);
	n = read(pfd[0], out, sizeof *out);
	close(pfd[0]);
	if (waitpid(pid, &st, 0) != pid || n != (ssize_t)sizeof *out)
		return -1;
	return 0;
}

static void t_lock(void)
{
	struct spictl_paths p;
	char lk[DIRMAX + 32], nodir[DIRMAX + 32], ro[DIRMAX + 32];
	struct stat st;
	struct lockrep r;
	int fd, fd2, rc;
	long t0;

	path_in(lk, sizeof lk, "flash.lock");
	memset(&p, 0, sizeof p);
	p.lock = lk;

	T_GROUP("lock: created 0600 whatever the umask");
	remove(lk);
	umask(022);
	fd = spictl_lock(&p, 1);
	CHECK(fd >= 0, "lock on a fresh path: %d", fd);
	CHECK(stat(lk, &st) == 0 && (st.st_mode & 0777) == 0600,
	      "mode 0%o, want 0600", (unsigned)(st.st_mode & 0777));
	spictl_unlock(fd);
	remove(lk);
	umask(0);
	fd = spictl_lock(&p, 1);
	CHECK(fd >= 0 && stat(lk, &st) == 0 && (st.st_mode & 0777) == 0600,
	      "umask 0: mode 0%o, want 0600 (the open's own mode, not 0666)",
	      (unsigned)(st.st_mode & 0777));
	spictl_unlock(fd);
	umask(022);

	T_GROUP("lock: a second holder in another process times out");
	fd = spictl_lock(&p, 1);
	CHECK(fd >= 0, "the first holder: %d", fd);
	CHECK(child_lock(&p, 1, &r) == 0, "the child ran");
	CHECK(r.rc == -ETIMEDOUT, "the child got %d, want -ETIMEDOUT (%d)",
	      r.rc, -ETIMEDOUT);
	CHECK(r.ms >= 1000 && r.ms <= 2000,
	      "it gave up after %ld ms, want [1000, 2000] for a 1 s timeout",
	      r.ms);
	CHECK(r.sleeps == 10, "ten 100 ms steps, counted %d", r.sleeps);
	printf("  timeout 1 s while held: rc %d after %ld ms, %d sleeps\n",
	       r.rc, r.ms, r.sleeps);

	T_GROUP("lock: and gets it once released");
	{
		int pfd[2];
		pid_t pid;
		int wst = 0;
		ssize_t n;

		CHECK(pipe(pfd) == 0, "pipe");
		pid = fork();
		if (pid == 0) {
			struct lockrep c;
			long c0;

			close(pfd[0]);
			c0 = ms_now();
			c.rc = spictl_lock(&p, 3);
			c.ms = ms_now() - c0;
			c.sleeps = 0;
			n = __real_write(pfd[1], &c, sizeof c);
			if (c.rc >= 0)
				spictl_unlock(c.rc);
			_exit(n == (ssize_t)sizeof c ? 0 : 1);
		}
		close(pfd[1]);
		nap_ms(500);
		spictl_unlock(fd);
		n = read(pfd[0], &r, sizeof r);
		close(pfd[0]);
		CHECK(pid > 0 && waitpid(pid, &wst, 0) == pid &&
		      n == (ssize_t)sizeof r, "the child ran");
		CHECK(r.rc >= 0, "after the release the child got %d, want an fd",
		      r.rc);
		CHECK(r.ms >= 400 && r.ms <= 1500,
		      "it got it after %ld ms, want [400, 1500] for a release at"
		      " 500 ms", r.ms);
		printf("  released at 500 ms: the waiter got fd %d after %ld ms\n",
		       r.rc, r.ms);
	}

	T_GROUP("lock: timeout 0 is one attempt");
	fd = spictl_lock(&p, 0);
	CHECK(fd >= 0, "free: %d", fd);
	rec_reset();
	t0 = ms_now();
	fd2 = spictl_lock(&p, 0);
	CHECK(fd2 == -ETIMEDOUT, "held, timeout 0: %d", fd2);
	CHECK(g_nsleep == 0 && ms_now() - t0 < 100,
	      "no sleep for a 0 s timeout: %d sleeps", g_nsleep);
	spictl_unlock(fd);
	fd = spictl_lock(&p, 0);
	CHECK(fd >= 0, "and free again after the release: %d", fd);
	spictl_unlock(fd);

	T_GROUP("lock: ENOSYS (no CONFIG_FILE_LOCKING) is final, and named");
	rec_reset();
	g_flock_enosys = 1;
	t0 = ms_now();
	rc = spictl_lock(&p, 30);
	CHECK(rc == -ENOSYS, "flock ENOSYS: %d, want -ENOSYS", rc);
	CHECK(g_nsleep == 0 && g_nflock == 1 && ms_now() - t0 < 100,
	      "no retry on ENOSYS: %d flock calls, %d sleeps", g_nflock,
	      g_nsleep);
	CHECK(strstr(spictl_lock_why(rc), "ENOSYS") != NULL &&
	      strstr(spictl_lock_why(rc), "CONFIG_FILE_LOCKING") != NULL,
	      "named: \"%s\"", spictl_lock_why(rc));
	CHECK(strstr(spictl_lock_why(-ETIMEDOUT), "ENOSYS") == NULL,
	      "and the timeout is named otherwise: \"%s\"",
	      spictl_lock_why(-ETIMEDOUT));
	g_flock_enosys = 0;
	fd = spictl_lock(&p, 30);
	CHECK(fd >= 0, "the real flock permits: %d", fd);
	spictl_unlock(fd);

	T_GROUP("lock: refusals from the path");
	path_in(nodir, sizeof nodir, "no-such-dir/flash.lock");
	p.lock = nodir;
	rec_reset();
	rc = spictl_lock(&p, 1);
	CHECK(rc == -ENOENT && g_nflock == 0,
	      "a lock in a missing directory: %d, %d flock calls", rc, g_nflock);
	path_in(ro, sizeof ro, "ro-dir");
	(void)mkdir(ro, 0755);
	(void)chmod(ro, 0555);
	{
		char rl[DIRMAX + 64];

		(void)snprintf(rl, sizeof rl, "%s/flash.lock", ro);
		p.lock = rl;
		rc = spictl_lock(&p, 1);
		if (geteuid() != 0)
			CHECK(rc == -EACCES,
			      "a lock /run will not let a non-root caller create:"
			      " %d, want -EACCES", rc);
		else
			printf("#   euid 0: the EACCES case cannot be shown here"
			       " (rc %d); it is NOT counted as a pass\n", rc);
		if (rc >= 0)
			spictl_unlock(rc);
	}
	(void)chmod(ro, 0755);
	p.lock = NULL;
	CHECK(spictl_lock(&p, 1) == -EINVAL, "no path: -EINVAL");
	CHECK(spictl_lock(NULL, 1) == -EINVAL, "no paths at all: -EINVAL");
}

/* ------------------------------------------------------------------------- */
/* Verbs                                                                     */
/* ------------------------------------------------------------------------- */

static void t_verb(void)
{
	struct spictl_paths p;
	char proc[DIRMAX + 32], nodir[DIRMAX + 32], buf[256], line[200];
	long c0, c1, n;
	int rc, i;

	path_in(proc, sizeof proc, "proc-verb");
	memset(&p, 0, sizeof p);
	p.proc = proc;

	T_GROUP("syscw: the kernel's write count sees two writes as two");
	{
		char scratch[DIRMAX + 32];
		int fd;
		ssize_t w1, w2;

		path_in(scratch, sizeof scratch, "syscw-control");
		fd = __real_open(scratch, O_WRONLY | O_CREAT | O_TRUNC, 0600);
		c0 = syscw();
		w1 = __real_write(fd, "a", 1);
		w2 = __real_write(fd, "b", 1);
		c1 = syscw();
		close(fd);
		CHECK(c0 >= 0 && w1 == 1 && w2 == 1 && c1 - c0 == 2,
		      "syscw moved %ld for two writes (reads %ld -> %ld)",
		      c1 - c0, c0, c1);
	}

	T_GROUP("verb: one open, ONE write(2) of the line, bytes exact");
	CHECK(put_file(proc, "", 0) == 0, "stand-in");
	rec_reset();
	c0 = syscw();
	rc = spictl_verb(&p, "img reset");
	c1 = syscw();
	CHECK(rc == 0, "img reset: %d", rc);
	CHECK(g_nw == 1 && g_w[0].len == 9 && strcmp(g_w[0].head, "img reset") == 0,
	      "%d writes; the first %lu bytes \"%s\"", g_nw,
	      (unsigned long)(g_nw ? g_w[0].len : 0), g_nw ? g_w[0].head : "");
	CHECK(c1 - c0 == 1, "syscw moved %ld, want 1", c1 - c0);
	CHECK(g_nopen == 1, "%d opens, want 1", g_nopen);
	n = get_file(proc, buf, sizeof buf);
	CHECK(n == 9 && memcmp(buf, "img reset", 9) == 0,
	      "the stand-in holds %ld bytes; no newline added", n);

	/* the install line's shape, and the longest line the handler takes */
	n = snprintf(line, sizeof line, "install cfg0 sha=");
	for (i = 0; i < 64; i++)
		line[n + i] = "0123456789abcdef"[i % 16];
	line[n + 64] = '\0';
	CHECK(put_file(proc, "", 0) == 0, "stand-in");
	rec_reset();
	rc = spictl_verb(&p, line);
	CHECK(rc == 0 && g_nw == 1 && g_w[0].len == 81,
	      "an install line: rc %d, %d writes of %lu bytes", rc, g_nw,
	      (unsigned long)(g_nw ? g_w[0].len : 0));
	memset(line, 'x', 127);
	line[127] = '\0';
	rec_reset();
	rc = spictl_verb(&p, line);
	CHECK(rc == 0 && g_nw == 1 && g_w[0].len == 127,
	      "127 bytes: rc %d, %d writes", rc, g_nw);

	T_GROUP("verb: the write's own errno comes back");
	p.proc = "/dev/full";
	rec_reset();
	rc = spictl_verb(&p, "disarm");
	CHECK(rc == -ENOSPC && g_nw == 1,
	      "/dev/full: rc %d, want -ENOSPC, after %d writes", rc, g_nw);
	p.proc = proc;
	rec_reset();
	g_wfail_at = 0;
	g_wfail_errno = EBADMSG;
	rc = spictl_verb(&p, "install cfg1 sha=00");
	CHECK(rc == -EBADMSG && g_nw == 1,
	      "a refused verb: rc %d, want -EBADMSG, after %d writes", rc, g_nw);
	rec_reset();
	g_wshort_at = 0;
	rc = spictl_verb(&p, "disarm");
	CHECK(rc == -EIO && g_nw == 1,
	      "a short write is -EIO and is not retried: rc %d, %d writes", rc,
	      g_nw);

	T_GROUP("verb: refusals before any write");
	path_in(nodir, sizeof nodir, "no-such-dir/proc");
	p.proc = nodir;
	rec_reset();
	rc = spictl_verb(&p, "disarm");
	CHECK(rc == -ENOENT && g_nw == 0, "missing: rc %d, %d writes", rc, g_nw);
	p.proc = proc;
	rec_reset();
	rc = spictl_verb(&p, "");
	CHECK(rc == -EINVAL && g_nw == 0 && g_nopen == 0,
	      "an empty line: rc %d, %d opens, %d writes", rc, g_nopen, g_nw);
	CHECK(spictl_verb(&p, NULL) == -EINVAL, "no line: -EINVAL");
	CHECK(spictl_verb(NULL, "disarm") == -EINVAL, "no paths: -EINVAL");
}

/* ------------------------------------------------------------------------- */
/* Staging                                                                   */
/* ------------------------------------------------------------------------- */

static void t_stage(void)
{
	static unsigned char src[10000], back[12000];
	struct spictl_paths p;
	char img[DIRMAX + 32], nodir[DIRMAX + 32];
	long c0, c1, n;
	int rc, i;

	for (i = 0; i < (int)sizeof src; i++)
		src[i] = (unsigned char)(i * 31 + 5);
	path_in(img, sizeof img, "proc-img");
	memset(&p, 0, sizeof p);
	p.img = img;

	T_GROUP("stage: 10,000 bytes as 4,096 + 4,096 + 1,808, in order");
	CHECK(put_file(img, "", 0) == 0, "stand-in");
	rec_reset();
	c0 = syscw();
	rc = spictl_stage(&p, src, sizeof src);
	c1 = syscw();
	CHECK(rc == 0, "stage: %d", rc);
	CHECK(g_nw == 3, "%d writes, want 3", g_nw);
	if (g_nw == 3) {
		CHECK(g_w[0].len == 4096 && g_w[1].len == 4096 &&
		      g_w[2].len == 1808, "sizes %lu %lu %lu",
		      (unsigned long)g_w[0].len, (unsigned long)g_w[1].len,
		      (unsigned long)g_w[2].len);
		CHECK(g_w[0].fd == g_w[1].fd && g_w[1].fd == g_w[2].fd,
		      "one descriptor for the three");
		CHECK(memcmp(g_w[1].head, src + 4096, 64) == 0 &&
		      memcmp(g_w[2].head, src + 8192, 64) == 0,
		      "each write starts where the last ended");
	}
	CHECK(c1 - c0 == 3, "syscw moved %ld, want 3", c1 - c0);
	CHECK(g_nopen == 1, "%d opens, want 1", g_nopen);
	n = get_file(img, back, sizeof back);
	CHECK(n == 10000 && memcmp(back, src, sizeof src) == 0,
	      "the stand-in holds the 10,000 bytes: %ld", n);

	T_GROUP("stage: the chunk boundary");
	CHECK(put_file(img, "", 0) == 0, "stand-in");
	rec_reset();
	rc = spictl_stage(&p, src, 4096);
	CHECK(rc == 0 && g_nw == 1 && g_w[0].len == 4096, "4,096: one write");
	CHECK(put_file(img, "", 0) == 0, "stand-in");
	rec_reset();
	rc = spictl_stage(&p, src, 4097);
	CHECK(rc == 0 && g_nw == 2 && g_w[0].len == 4096 && g_w[1].len == 1,
	      "4,097: 4,096 then 1");

	T_GROUP("stage: a refused append stops the staging");
	CHECK(put_file(img, "", 0) == 0, "stand-in");
	rec_reset();
	g_wfail_at = 1;
	g_wfail_errno = EFBIG;
	rc = spictl_stage(&p, src, sizeof src);
	CHECK(rc == -EFBIG && g_nw == 2,
	      "EFBIG on the second: rc %d after %d writes (no third)", rc, g_nw);
	CHECK(put_file(img, "", 0) == 0, "stand-in");
	rec_reset();
	g_wshort_at = 1;
	rc = spictl_stage(&p, src, sizeof src);
	CHECK(rc == -EIO && g_nw == 2,
	      "a short second append: rc %d after %d writes", rc, g_nw);

	T_GROUP("stage: refusals before any write");
	rec_reset();
	CHECK(spictl_stage(&p, src, 0) == -EINVAL && g_nopen == 0,
	      "nothing to stage: -EINVAL, no open");
	CHECK(spictl_stage(&p, NULL, 4) == -EINVAL, "no buffer: -EINVAL");
	path_in(nodir, sizeof nodir, "no-such-dir/img");
	p.img = nodir;
	rec_reset();
	rc = spictl_stage(&p, src, 16);
	CHECK(rc == -ENOENT && g_nw == 0, "missing: rc %d, %d writes", rc, g_nw);
}

/* ------------------------------------------------------------------------- */
/* Fields                                                                    */
/* ------------------------------------------------------------------------- */

static const char page_a[] =
	"version rtl819x-spi 1.1\n"
	"n_writes 1266\n"
	"n_write_refused 0\n"
	"inst_version rtl819x-spi-install 1.1\n"
	"img_cap 1179648\n"
	"img_len 4096\n"
	"img_writes 1\n"
	"img_resets 3\n"
	"img_err none\n"
	"inst_reason OK\n"
	"inst_rc 0\n"
	"inst_cmp_ran 1\n"
	"inst_cmp_ok 1\n"
	"inst_cmp_bytes 65536\n"
	"inst_cmp_diff 0\n"
	"inst_cmp_first -1\n"
	"eraseprobe se_bytes=-1 se_polls=0 se_us=0 pp_us=0 clean=-1\n"
	"u_max 4294967295\n"
	"u_over 4294967296\n"
	"u_lead 01\n"
	"u_alpha 12a\n"
	"u_empty \n"
	"proc_bytes_before_this_line 470\n";

static void t_field(void)
{
	struct spictl_paths p;
	char proc[DIRMAX + 32], v[64];
	static char big[5200];
	uint32_t u = 0;
	int rc;

	path_in(proc, sizeof proc, "inst-node");
	memset(&p, 0, sizeof p);
	p.state = proc;
	CHECK(put_file(proc, page_a, sizeof page_a - 1) == 0, "page a");

	T_GROUP("field: read from p->state, never from p->proc");
	{
		static const char decoy[] = "img_len 1\nn_writes 7\n";
		char dp[DIRMAX + 32];

		path_in(dp, sizeof dp, "proc-page");
		CHECK(put_file(dp, decoy, sizeof decoy - 1) == 0, "the verbs' page");
		p.proc = dp;
		rc = spictl_field(&p, "img_len", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "4096") == 0,
		      "img_len from the node, not the page's 1: %d \"%s\"", rc, v);
		p.state = NULL;
		CHECK(spictl_field(&p, "img_len", v, sizeof v) == -EINVAL,
		      "no state path: -EINVAL, even with a readable p->proc");
		p.state = proc;
		p.proc = NULL;
		CHECK(spictl_field(&p, "img_len", v, sizeof v) == 0,
		      "and p->proc is not needed to read a field");
	}

	T_GROUP("field: present");
	rc = spictl_field(&p, "img_len", v, sizeof v);
	CHECK(rc == 0 && strcmp(v, "4096") == 0, "img_len: %d \"%s\"", rc, v);
	rc = spictl_field(&p, "img_err", v, sizeof v);
	CHECK(rc == 0 && strcmp(v, "none") == 0, "img_err: %d \"%s\"", rc, v);
	rc = spictl_field(&p, "inst_reason", v, sizeof v);
	CHECK(rc == 0 && strcmp(v, "OK") == 0, "inst_reason: %d \"%s\"", rc, v);
	rc = spictl_field(&p, "eraseprobe", v, sizeof v);
	CHECK(rc == 0 && strncmp(v, "se_bytes=-1 se_polls=0", 22) == 0,
	      "a value with spaces is the rest of the line: \"%s\"", v);
	rec_reset();
	rc = spictl_field(&p, "n_writes", v, sizeof v);
	CHECK(rc == 0 && strcmp(v, "1266") == 0 && g_nopen == 1,
	      "n_writes: %d \"%s\" in %d open", rc, v, g_nopen);

	T_GROUP("field: absent, and a key never matches a longer one");
	CHECK(spictl_field(&p, "nope", v, sizeof v) == -ENOENT, "nope");
	CHECK(spictl_field(&p, "img", v, sizeof v) == -ENOENT,
	      "img is not img_len, img_cap, img_writes or img_err");
	CHECK(spictl_field(&p, "n_write", v, sizeof v) == -ENOENT,
	      "n_write is not n_writes or n_write_refused");
	CHECK(spictl_field(&p, "inst_cmp", v, sizeof v) == -ENOENT,
	      "inst_cmp is none of the four inst_cmp_*");
	CHECK(spictl_field(&p, "img_len4096", v, sizeof v) == -ENOENT,
	      "nor is a key that runs into the value");
	{
		static const char b1[] = "img_len 4096\nimg 7\n";
		static const char b2[] = "img 7\nimg_len 4096\n";

		CHECK(put_file(proc, b1, sizeof b1 - 1) == 0, "page b1");
		rc = spictl_field(&p, "img", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "7") == 0,
		      "img after img_len: %d \"%s\", want \"7\"", rc, v);
		CHECK(put_file(proc, b2, sizeof b2 - 1) == 0, "page b2");
		rc = spictl_field(&p, "img_len", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "4096") == 0,
		      "img_len after img: %d \"%s\"", rc, v);
		rc = spictl_field(&p, "img", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "7") == 0, "img first: \"%s\"", v);
	}

	T_GROUP("field: too long for the caller's buffer");
	CHECK(put_file(proc, page_a, sizeof page_a - 1) == 0, "page a");
	rc = spictl_field(&p, "img_len", v, 4);
	CHECK(rc == -E2BIG, "4 bytes for \"4096\": %d, want -E2BIG", rc);
	CHECK(v[0] == '\0', "and the buffer is left empty");
	rc = spictl_field(&p, "img_len", v, 5);
	CHECK(rc == 0 && strcmp(v, "4096") == 0, "5 bytes fit: %d", rc);

	T_GROUP("field: complete lines only, one read only");
	{
		static const char cut[] = "img_len 4096\ninst_reason OK";
		int k;

		CHECK(put_file(proc, cut, sizeof cut - 1) == 0, "cut page");
		CHECK(spictl_field(&p, "inst_reason", v, sizeof v) == -ENOENT,
		      "a last line without its newline is not a field");
		rc = spictl_field(&p, "img_len", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "4096") == 0, "the line before it is");

		memset(big, 'z', sizeof big);
		for (k = 63; k < (int)sizeof big; k += 64)
			big[k] = '\n';
		memcpy(big, "early 1\n", 8);
		memcpy(big + 4160, "late 1\n", 7);
		CHECK(put_file(proc, big, sizeof big) == 0, "a 5,200-byte page");
		rc = spictl_field(&p, "early", v, sizeof v);
		CHECK(rc == 0 && strcmp(v, "1") == 0, "inside the read: %d", rc);
		CHECK(spictl_field(&p, "late", v, sizeof v) == -ENOENT,
		      "past the one read of %d bytes: absent", SPICTL_PAGE_MAX);
	}

	T_GROUP("field_u32: strict decimal");
	CHECK(put_file(proc, page_a, sizeof page_a - 1) == 0, "page a");
	CHECK(spictl_field_u32(&p, "n_writes", &u) == 0 && u == 1266u,
	      "n_writes %lu", (unsigned long)u);
	CHECK(spictl_field_u32(&p, "inst_cmp_diff", &u) == 0 && u == 0u, "0");
	CHECK(spictl_field_u32(&p, "u_max", &u) == 0 && u == 0xFFFFFFFFu,
	      "4294967295");
	CHECK(spictl_field_u32(&p, "u_over", &u) == -ERANGE, "4294967296");
	CHECK(spictl_field_u32(&p, "inst_cmp_first", &u) == -EINVAL, "-1");
	CHECK(spictl_field_u32(&p, "u_lead", &u) == -EINVAL, "01");
	CHECK(spictl_field_u32(&p, "u_alpha", &u) == -EINVAL, "12a");
	CHECK(spictl_field_u32(&p, "u_empty", &u) == -EINVAL, "empty");
	CHECK(spictl_field_u32(&p, "nope", &u) == -ENOENT, "absent");

	T_GROUP("field: refusals");
	CHECK(spictl_field(&p, "", v, sizeof v) == -EINVAL, "empty key");
	CHECK(spictl_field(&p, "img len", v, sizeof v) == -EINVAL, "a space");
	CHECK(spictl_field(&p, "img_len", NULL, 8) == -EINVAL, "no buffer");
	CHECK(spictl_field(&p, "img_len", v, 0) == -EINVAL, "no room");
	p.state = "/nonexistent/rtl819x-spi-inst";
	CHECK(spictl_field(&p, "img_len", v, sizeof v) == -ENOENT,
	      "a missing node");
	CHECK(strcmp(spictl_dev.state, "/proc/rtl819x-spi-inst") == 0 &&
	      strcmp(spictl_dev.proc, "/proc/rtl819x-spi") == 0,
	      "spictl_dev: verbs to %s, fields from %s", spictl_dev.proc,
	      spictl_dev.state);
}

/* ------------------------------------------------------------------------- */
/* The flash read                                                            */
/* ------------------------------------------------------------------------- */

static void t_flash(void)
{
	static unsigned char chip[0x400000];
	unsigned char buf[4096 + 16];
	struct spictl_paths p;
	char fl[DIRMAX + 32], nofl[DIRMAX + 32];
	int rc, i, k;
	static const struct {
		uint32_t off;
		size_t len;
		const char *what;
	} forbid[] = {
		{ 0x0000FFFCu, 8, "0xFFFC len 8: across the floor" },
		{ 0x00000000u, 4, "0 len 4: the loader's first word" },
		{ 0x00006000u, 4096, "0x6000: H601" },
		{ 0x0000FFFCu, 4, "0xFFFC len 4: ends exactly at the floor" },
		{ 0x00000000u, 0, "0 len 0: an empty range below the floor" },
		{ 0xFFFFFFFCu, 8, "0xFFFFFFFC len 8: wraps to 4" },
		{ 0xFFFFFFFCu, 4, "0xFFFFFFFC len 4: ends at 2^32" },
		{ 0x00010000u, 0xFFFFFFFCu, "0x10000 len 0xFFFFFFFC: wraps" },
	};

	for (i = 0; i < (int)sizeof chip; i++)
		chip[i] = (unsigned char)((i >> 8) ^ (i * 13));
	path_in(fl, sizeof fl, "mtd2ro.bin");
	path_in(nofl, sizeof nofl, "no-such-mtd2ro");
	remove(nofl);
	memset(&p, 0, sizeof p);

	T_GROUP("flash_read: the guard refuses before any open");
	p.flash = nofl;
	for (k = 0; k < (int)(sizeof forbid / sizeof forbid[0]); k++) {
		memset(buf, 0xA5, sizeof buf);
		rec_reset();
		/* The device is absent here, so a guard that let a range
		 * through would answer -ENOENT, never touch buf, and still be
		 * caught; the huge lengths are never read for the same reason. */
		rc = spictl_flash_read(&p, forbid[k].off, buf, forbid[k].len);
		CHECK(rc == -EPERM, "%s: %d, want -EPERM", forbid[k].what, rc);
		CHECK(g_nopen == 0, "%s: %d opens, want 0", forbid[k].what,
		      g_nopen);
		CHECK(buf[0] == 0xA5 && buf[sizeof buf - 1] == 0xA5,
		      "%s: the buffer was touched", forbid[k].what);
	}
	CHECK(put_file(fl, chip, sizeof chip) == 0, "the 4 MiB stand-in");
	p.flash = fl;
	rec_reset();
	memset(buf, 0xA5, sizeof buf);
	rc = spictl_flash_read(&p, 0, buf, 4);
	CHECK(rc == -EPERM && g_nopen == 0 && buf[0] == 0xA5,
	      "0 len 4 with the device present: %d, %d opens", rc, g_nopen);
	p.flash = nofl;

	T_GROUP("flash_read: the guard permits 0x10000 (the open is what fails)");
	rec_reset();
	rc = spictl_flash_read(&p, 0x10000u, buf, 4);
	CHECK(rc == -ENOENT && g_nopen == 1,
	      "0x10000 on a missing device: %d after %d opens, want -ENOENT"
	      " after 1", rc, g_nopen);

	T_GROUP("flash_read: alignment");
	rec_reset();
	CHECK(spictl_flash_read(&p, 0x10002u, buf, 4) == -EINVAL, "off 0x10002");
	CHECK(spictl_flash_read(&p, 0x10000u, buf, 6) == -EINVAL, "len 6");
	CHECK(g_nopen == 0, "no open for a misaligned request: %d", g_nopen);

	T_GROUP("flash_read: permitted reads return the device's bytes");
	p.flash = fl;
	rc = spictl_flash_read(&p, 0x10000u, buf, 4096);
	CHECK(rc == 0 && memcmp(buf, chip + 0x10000, 4096) == 0,
	      "0x10000: %d", rc);
	rc = spictl_flash_read(&p, 0x3C0000u, buf, 4096);
	CHECK(rc == 0 && memcmp(buf, chip + 0x3C0000, 4096) == 0,
	      "0x3C0000: %d", rc);
	rc = spictl_flash_read(&p, 0x3D0000u, buf, 4096);
	CHECK(rc == 0 && memcmp(buf, chip + 0x3D0000, 4096) == 0,
	      "0x3D0000: %d", rc);
	rc = spictl_flash_read(&p, 0x3FFFFCu, buf, 8);
	CHECK(rc == -EIO, "past the end of the device is short: %d, want -EIO",
	      rc);
	CHECK(spictl_flash_read(&p, 0x3C0000u, NULL, 4) == -EINVAL,
	      "no buffer: -EINVAL");
	remove(fl);
}

int main(int argc, char **argv)
{
	if (argc < 2 || strlen(argv[1]) >= DIRMAX) {
		fputs("usage: test_spictl <scratch dir>\n", stderr);
		return 2;
	}
	(void)snprintf(g_dir, sizeof g_dir, "%s/spictl", argv[1]);
	(void)mkdir(g_dir, 0755);
	printf("  scratch: %s\n", g_dir);
	t_lock();
	t_verb();
	t_stage();
	t_field();
	t_flash();
	return t_done("spictl");
}
