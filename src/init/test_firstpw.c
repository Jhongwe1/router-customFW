/* test_firstpw.c -- the console first-password step (src/init/firstpw.c)
 * against a store in a scratch directory, a console that is a pipe or a pty,
 * and an entropy pool that fills on cue.  notes/self-update.md § 3.8 is what
 * it checks.
 *
 * ---------------------------------------------------------------------------
 * THE INSTRUMENTS, AND WHICH ONE COULD BE LYING
 * ---------------------------------------------------------------------------
 *
 *   store    src/lib/cfg.c's FILE backend: the step is given a regular file's
 *            path.  What is tested is fp_run's choice -- which write, over
 *            what, or none -- and cfg_store and cfg_store_fresh are one body
 *            on both backends (cfg.c store_rec); the flash backend's own
 *            sequence is src/cfgstore's test_flash's, not this file's.
 *   console  a pipe fed before the run (output to a file) for the scripted
 *            cases; a pty for the echo case, where every byte the line
 *            discipline sends back is read from the master and searched for
 *            the password.  Its positive control: with echo on, a canary
 *            typed into the same pty IS found.
 *   pool     the entropy and salt seams: the salt refuses -KDFE_ENTROPY while
 *            the scripted pool is below KDF_ENTROPY_MIN, as pwhash_salt does,
 *            and records the pool at every draw; the clock moves only by what
 *            the step asks to sleep.
 *   echo     tcsetattr is wrapped (--wrap=tcsetattr) so that it can fail, or
 *            answer 0 while leaving ECHO on (POSIX allows a partial change),
 *            which no pty here does by itself: the guard shown refusing.
 *   hash     pwhash_verify (src/lib/kdf.c) on the stored blob -- the
 *            computation brokerd's LOGIN makes with the blob's own parameters
 *            -- and the blob's parameter bytes against brokerd.h's BK_KDF_*.
 */

#define _GNU_SOURCE	/* posix_openpt, grantpt, unlockpt, ptsname */

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#include "firstpw.h"
#include "kdf.h"
#include "schema.h"
#include "brokerd.h"	/* BK_KDF_*, BK_ENTROPY_MIN, BK_PWHASH_LEN */

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

#define PMAX 320
#define OUTMAX 16384

static char g_dir[PMAX], p_store[PMAX], p_out[PMAX], p_dirstore[PMAX];
static char g_out[OUTMAX + 1];

/* ------------------------------------------------------------------------- */
/* tcsetattr, wrapped                                                        */
/* ------------------------------------------------------------------------- */

int __real_tcsetattr(int fd, int act, const struct termios *t);

static int g_tcset_mode;	/* 0 real, 1 fails EIO, 2 "succeeds", ECHO kept */

int __wrap_tcsetattr(int fd, int act, const struct termios *t)
{
	struct termios k;

	if (g_tcset_mode == 1) {
		errno = EIO;
		return -1;
	}
	if (g_tcset_mode == 2) {
		k = *t;
		k.c_lflag |= (tcflag_t)ECHO;
		return __real_tcsetattr(fd, act, &k);
	}
	return __real_tcsetattr(fd, act, t);
}

/* ------------------------------------------------------------------------- */
/* The pool, the clock, the salt                                             */
/* ------------------------------------------------------------------------- */

static long g_now;
static long g_fill_at;		/* the pool reads 0 before, 200 from here on */
static int g_salt_io;		/* the salt fails -KDFE_IO */
static int g_salt_calls, g_draws;
static int g_draw_pool;		/* the pool's reading at the (last) draw */

static int pool(void)
{
	return g_now >= g_fill_at ? 200 : 0;
}

static int f_entropy(void *ctx)
{
	(void)ctx;
	return pool();
}

static int f_salt(void *ctx, uint8_t salt[16])
{
	int i;

	(void)ctx;
	g_salt_calls++;
	if (g_salt_io)
		return -KDFE_IO;
	if (pool() < KDF_ENTROPY_MIN)
		return -KDFE_ENTROPY;	/* pwhash_salt's refusal */
	for (i = 0; i < 16; i++)
		salt[i] = (uint8_t)(0xA0 + i);
	g_draws++;
	g_draw_pool = pool();
	return 0;
}

static void f_sleep(void *ctx, long ms)
{
	(void)ctx;
	g_now += ms;
}

static void pool_reset(void)
{
	g_now = 0;
	g_fill_at = 0;
	g_salt_io = 0;
	g_salt_calls = 0;
	g_draws = 0;
	g_draw_pool = -1;
	g_tcset_mode = 0;
}

/* ------------------------------------------------------------------------- */
/* Files                                                                     */
/* ------------------------------------------------------------------------- */

static long read_file(const char *path, char *buf, size_t cap)
{
	int fd = open(path, O_RDONLY);
	size_t got = 0;

	if (fd < 0)
		return -1;
	for (;;) {
		ssize_t r = read(fd, buf + got, cap - got);

		if (r <= 0)
			break;
		got += (size_t)r;
		if (got == cap)
			break;
	}
	(void)close(fd);
	return (long)got;
}

static void write_file(const char *path, const void *buf, size_t n)
{
	int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	ssize_t w;

	if (fd < 0)
		return;
	w = write(fd, buf, n);
	(void)w;
	(void)close(fd);
}

static int file_absent(const char *path)
{
	struct stat st;

	return stat(path, &st) != 0 && errno == ENOENT;
}

/* ------------------------------------------------------------------------- */
/* Stores                                                                    */
/* ------------------------------------------------------------------------- */

static const uint8_t old_salt[16] = {
	1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
};

/* A valid record at seq 2 in slot 1, sys.hostname "bench" (not the
 * default), and, if asked, a hash of "old-password-1". */
static void store_valid(int with_hash)
{
	struct cfg c;
	uint8_t blob[PWHASH_LEN];

	(void)unlink(p_store);
	CK(cfg_defaults(&c) == 0);
	CK(cfg_set(&c, CFGID_SYS_HOSTNAME, (const uint8_t *)"bench", 5) == 0);
	if (with_hash) {
		CK(pwhash_make((const uint8_t *)"old-password-1", 14, KDF_LOG2N,
			       KDF_R, KDF_P, old_salt, blob) == 0);
		CK(cfg_set(&c, CFGID_ADMIN_PWHASH, blob, PWHASH_LEN) == 0);
	}
	CK(cfg_store(p_store, &c) == 0);	/* seq 1, slot 0 */
	CK(cfg_store(p_store, &c) == 0);	/* seq 2, slot 1 */
	CK(c.seq == 2u && c.source == 2);
}

static void store_corrupt(void)
{
	uint8_t z[CFG_FILE_SIZE];

	memset(z, 0, sizeof z);		/* seq 0 and no magic: two bad slots */
	write_file(p_store, z, sizeof z);
}

/* ------------------------------------------------------------------------- */
/* Running the step on a pipe                                                */
/* ------------------------------------------------------------------------- */

static void env(struct fp_env *e, int in_fd, int out_fd, const char *store)
{
	memset(e, 0, sizeof *e);
	e->in_fd = in_fd;
	e->out_fd = out_fd;
	e->store = store;
	e->entropy = f_entropy;
	e->salt = f_salt;
	e->sleep_ms = f_sleep;
	e->ctx = NULL;
}

static int run_pipe(const char *input, const char *store)
{
	struct fp_env e;
	int p[2], out, rc;
	long n;
	ssize_t w;

	if (pipe(p) != 0)
		return -100;
	w = write(p[1], input, strlen(input));
	(void)w;
	(void)close(p[1]);	/* EOF after the script */
	out = open(p_out, O_RDWR | O_CREAT | O_TRUNC, 0600);
	env(&e, p[0], out, store);
	rc = fp_run(&e);
	(void)close(p[0]);
	(void)close(out);
	n = read_file(p_out, g_out, OUTMAX);
	g_out[n > 0 ? n : 0] = '\0';
	return rc;
}

static int said(const char *s)
{
	return strstr(g_out, s) != NULL;
}

/* The store holds a hash of `pw`, by brokerd's parameters; seq and slot
 * as given (slot 0 = source 1). */
static void ck_hashed(const char *pw, uint32_t seq, int slot)
{
	struct cfg c;
	struct cfg_store_info info;
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;

	CK(cfg_load_info(p_store, &c, &info) == 0);
	CK(info.selected == slot + 1);
	CK(c.seq == seq);
	CK(cfg_get(&c, CFGID_ADMIN_PWHASH, v, &len) == 0);
	CK(len == BK_PWHASH_LEN);
	CK(v[0] == 1u);					/* alg scrypt */
	CK(v[1] == BK_KDF_LOG2N);
	CK(((v[2] << 8) | v[3]) == BK_KDF_R);
	CK(((v[4] << 8) | v[5]) == BK_KDF_P);
	CK(v[6] == 0u && v[7] == 0u);
	CK(pwhash_verify(v, (const uint8_t *)pw, strlen(pw)) == 1);
	CK(pwhash_verify(v, (const uint8_t *)"not-the-password", 16) == 0);
}

static void ck_hostname(const char *want)
{
	struct cfg c;
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;

	CK(cfg_load(p_store, &c) == 0);
	CK(cfg_get(&c, CFGID_SYS_HOSTNAME, v, &len) == 0);
	CK(len == strlen(want) && memcmp(v, want, len) == 0);
}

/* ------------------------------------------------------------------------- */
/* Cases                                                                     */
/* ------------------------------------------------------------------------- */

static void t_offer(void)
{
	struct cfg c;
	uint8_t blob[PWHASH_LEN];

	CK(cfg_defaults(&c) == 0);
	CK(fp_offer(0, &c) == FP_OFFER_YES);
	CK(fp_offer(-CFGE_IO, &c) == FP_OFFER_UNREADABLE);
	CK(fp_offer(0, NULL) == FP_OFFER_UNREADABLE);
	memset(blob, 0x11, sizeof blob);
	blob[0] = 1u;
	CK(cfg_set(&c, CFGID_ADMIN_PWHASH, blob, PWHASH_LEN) == 0);
	CK(fp_offer(0, &c) == FP_OFFER_NO);
	/* a present hash whose alg byte is not 1 still counts as one */
	blob[0] = 0u;
	CK(cfg_set(&c, CFGID_ADMIN_PWHASH, blob, PWHASH_LEN) == 0);
	CK(fp_offer(0, &c) == FP_OFFER_NO);
}

static void t_absent(void)
{
	pool_reset();
	(void)unlink(p_store);
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_SET_FRESH);
	ck_hashed("correct horse", 1u, 0);
	ck_hostname("rlxfw");	/* the default: nothing else was invented */
	CK(said("admin.pwhash set through cfg_store_fresh: the defaults and the "
		"hash written as slot 0 seq 1; the store held no record"));
	CK(g_draws == 1);
	CK(g_draw_pool >= KDF_ENTROPY_MIN);
}

static void t_corrupt(void)
{
	pool_reset();
	store_corrupt();
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_SET_FRESH);
	ck_hashed("correct horse", 1u, 0);
	CK(said("through cfg_store_fresh: the defaults and the hash written as "
		"slot 0 seq 1; the store held bytes but no valid record"));
}

static void t_valid_nohash(void)
{
	pool_reset();
	store_valid(0);
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_SET_STORE);
	ck_hashed("correct horse", 3u, 0);	/* seq 2 + 1, the other slot */
	ck_hostname("bench");			/* the record kept its keys */
	CK(said("admin.pwhash set through cfg_store: the record of slot 1 seq "
		"2, the hash added, written as slot 0 seq 3"));
}

static void t_valid_hash(void)
{
	static char before[CFG_FILE_SIZE], after[CFG_FILE_SIZE];
	struct cfg c;
	long nb, na;

	pool_reset();
	store_valid(1);
	nb = read_file(p_store, before, sizeof before);
	/* PID 1 does not offer the step ... */
	CK(cfg_load(p_store, &c) == 0);
	CK(fp_offer(0, &c) == FP_OFFER_NO);
	/* ... and the step itself, run anyway, writes nothing over the hash */
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_HASHED);
	na = read_file(p_store, after, sizeof after);
	CK(nb == (long)CFG_FILE_SIZE && na == nb);
	CK(memcmp(before, after, sizeof before) == 0);
	ck_hashed("old-password-1", 2u, 1);
	CK(said("a password is already set (slot 1, seq 2); nothing written"));
}

static void t_mismatch(void)
{
	pool_reset();
	(void)unlink(p_store);
	CK(run_pipe("correct horse\ncorrect horsf\n", p_store) == FP_R_EOF);
	CK(file_absent(p_store));
	CK(g_salt_calls == 0);
	CK(said("the two entries differ; nothing written, asking again"));
	CK(said("the console's input ended; nothing written"));

	/* and the same over a valid record: its bytes stay */
	{
		static char before[CFG_FILE_SIZE], after[CFG_FILE_SIZE];

		store_valid(0);
		(void)read_file(p_store, before, sizeof before);
		CK(run_pipe("correct horse\ncorrect horsf\n", p_store) ==
		   FP_R_EOF);
		(void)read_file(p_store, after, sizeof after);
		CK(memcmp(before, after, sizeof before) == 0);
	}
}

static void t_lengths(void)
{
	char in[400], pw64[65], pw65[66];

	memset(pw64, 'q', 64);
	pw64[64] = '\0';
	memset(pw65, 'q', 65);
	pw65[65] = '\0';

	/* 7 is refused and asked again; 8 is taken */
	pool_reset();
	(void)unlink(p_store);
	CK(run_pipe("1234567\n12345678\n12345678\n", p_store) == FP_R_SET_FRESH);
	CK(said("fewer than 8 bytes; nothing written, asking again"));
	ck_hashed("12345678", 1u, 0);

	/* 65 is refused; 64 is taken */
	pool_reset();
	(void)unlink(p_store);
	(void)snprintf(in, sizeof in, "%s\n%s\n%s\n", pw65, pw64, pw64);
	CK(run_pipe(in, p_store) == FP_R_SET_FRESH);
	CK(said("longer than 64 bytes; nothing written, asking again"));
	ck_hashed(pw64, 1u, 0);

	/* trailing CRs are not part of it, as in cfgstore's read_line */
	pool_reset();
	(void)unlink(p_store);
	CK(run_pipe("correct horse\r\ncorrect horse\r\n", p_store) ==
	   FP_R_SET_FRESH);
	ck_hashed("correct horse", 1u, 0);

	/* the console ends at once: nothing written */
	pool_reset();
	(void)unlink(p_store);
	CK(run_pipe("", p_store) == FP_R_EOF);
	CK(file_absent(p_store));
}

static void t_entropy(void)
{
	/* the pool fills at 65 s: 65 refused draws, one taken, the reading on
	 * the console at the 1st, 31st and 61st */
	pool_reset();
	g_fill_at = 65000L;
	(void)unlink(p_store);
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_SET_FRESH);
	CK(g_salt_calls == 66);
	CK(g_draws == 1);
	CK(g_draw_pool >= KDF_ENTROPY_MIN);
	CK(g_now == 65000L);
	{
		const char *p = g_out;
		int n = 0;

		while ((p = strstr(p, "waiting for entropy")) != NULL) {
			n++;
			p++;
		}
		CK(n == 3);
	}
	CK(said("entropy_avail=0, 128 needed"));
	ck_hashed("correct horse", 1u, 0);

	/* the salt's other failure is not waited out: nothing written */
	pool_reset();
	g_salt_io = 1;
	(void)unlink(p_store);
	CK(run_pipe("correct horse\ncorrect horse\n", p_store) == FP_R_KDF);
	CK(file_absent(p_store));
	CK(said("FAILED: no salt (/dev/urandom or entropy_avail unreadable); "
		"nothing written"));
}

static void t_unreadable(void)
{
	/* the store's path is a directory: not a regular file, never written */
	pool_reset();
	CK(mkdir(p_dirstore, 0700) == 0 || errno == EEXIST);
	CK(run_pipe("correct horse\ncorrect horse\n", p_dirstore) == FP_R_IO);
	CK(said("FAILED: the store could not be read"));
	CK(said("nothing written"));
	(void)rmdir(p_dirstore);
}

/* ------------------------------------------------------------------------- */
/* The pty: what the console shows                                           */
/* ------------------------------------------------------------------------- */

static int pty_open(int *master, int *slave)
{
	char *name;

	*master = posix_openpt(O_RDWR | O_NOCTTY);
	if (*master < 0)
		return -1;
	if (grantpt(*master) != 0 || unlockpt(*master) != 0)
		return -1;
	name = ptsname(*master);
	if (name == NULL)
		return -1;
	*slave = open(name, O_RDWR | O_NOCTTY);
	return *slave < 0 ? -1 : 0;
}

/* Read the master into buf (appending) until `want` appears or the timeout
 * passes or the master reports an end.  1 when found. */
static int pty_until(int master, char *buf, size_t cap, size_t *len,
		     const char *want, int timeout_ms)
{
	struct pollfd p;

	for (;;) {
		ssize_t r;

		buf[*len] = '\0';
		if (want != NULL && strstr(buf, want) != NULL)
			return 1;
		p.fd = master;
		p.events = POLLIN;
		p.revents = 0;
		if (poll(&p, 1, timeout_ms) <= 0)
			return 0;
		if (*len + 1 >= cap)
			return 0;
		r = read(master, buf + *len, cap - 1 - *len);
		if (r <= 0)
			return 0;
		*len += (size_t)r;
	}
}

/* waitpid with a deadline.  A step that blocks -- reading a console it should
 * have refused, say -- is killed and reported, not waited for: a hang is not
 * a test result (notes/init.md § 6).  1 when it exited (st set), 0 killed. */
static int wait_bounded(pid_t pid, int ms, int *st)
{
	struct timespec ts;
	int waited = 0;

	ts.tv_sec = 0;
	ts.tv_nsec = 10L * 1000000L;
	for (;;) {
		pid_t r = waitpid(pid, st, WNOHANG);

		if (r == pid)
			return 1;
		if (r < 0)
			return 0;
		if (waited >= ms) {
			(void)kill(pid, SIGKILL);
			(void)waitpid(pid, st, 0);
			return 0;
		}
		(void)nanosleep(&ts, NULL);
		waited += 10;
	}
}

static void t_pty_echo(void)
{
	static char buf[OUTMAX];
	struct termios t;
	struct fp_env e;
	size_t len = 0;
	int master = -1, slave = -1, st = -1, ok, mode;
	pid_t pid;
	ssize_t w;

	if (pty_open(&master, &slave) != 0) {
		printf("FAIL no pty: errno %d\n", errno);
		fails++;
		return;
	}

	/* The control: echo on, a canary typed is seen on the master. */
	CK(tcgetattr(slave, &t) == 0 && (t.c_lflag & (tcflag_t)ECHO) != 0);
	w = write(master, "canary-0451\n", 12);
	(void)w;
	CK(pty_until(master, buf, sizeof buf, &len, "canary-0451", 2000) == 1);
	{
		char sink[64];

		w = read(slave, sink, sizeof sink);	/* consume the line */
		(void)w;
	}

	/* The step on the pty, in a child; the parent types as a person would,
	 * each entry after its prompt. */
	pool_reset();
	(void)unlink(p_store);
	len = 0;
	pid = fork();
	if (pid == 0) {
		(void)close(master);
		env(&e, slave, slave, p_store);
		_exit(fp_run(&e));
	}
	CK(pid > 0);
	ok = pty_until(master, buf, sizeof buf, &len, "new password: ", 5000);
	CK(ok == 1);
	w = write(master, "hunter2-secret\n", 15);
	(void)w;
	ok = pty_until(master, buf, sizeof buf, &len, "the same again: ", 5000);
	CK(ok == 1);
	w = write(master, "hunter2-secret\n", 15);
	(void)w;
	ok = pty_until(master, buf, sizeof buf, &len,
		       "admin.pwhash set through cfg_store_fresh", 30000);
	CK(ok == 1);
	CK(pid > 0 && wait_bounded(pid, 30000, &st) == 1);
	CK(WIFEXITED(st) && WEXITSTATUS(st) == FP_R_SET_FRESH);

	/* THE property: the password is nowhere in what the console showed */
	CK(strstr(buf, "hunter2") == NULL);
	if (strstr(buf, "hunter2") != NULL)
		printf("      the console showed the password:\n%s\n", buf);
	ck_hashed("hunter2-secret", 1u, 0);
	/* and echo is back on afterwards */
	CK(tcgetattr(slave, &t) == 0 && (t.c_lflag & (tcflag_t)ECHO) != 0);

	/* The guard refusing: tcsetattr fails (1), or answers 0 and leaves ECHO
	 * on (2).  No password is read -- a step that went on to read would sit
	 * on the console, so each runs in a child with a deadline -- and
	 * nothing is written. */
	for (mode = 1; mode <= 2; mode++) {
		pool_reset();
		(void)unlink(p_store);
		pid = fork();
		if (pid == 0) {
			(void)close(master);
			g_tcset_mode = mode;
			env(&e, slave, slave, p_store);
			_exit(fp_run(&e));
		}
		CK(pid > 0);
		ok = pid > 0 ? wait_bounded(pid, 5000, &st) : 0;
		if (ok != 1)
			printf("      tcsetattr mode %d: the step was still running "
			       "after 5 s (reading the console?)\n", mode);
		CK(ok == 1);
		CK(ok == 1 && WIFEXITED(st) && WEXITSTATUS(st) == FP_R_TTY);
		CK(file_absent(p_store));
	}
	CK(tcgetattr(slave, &t) == 0 && (t.c_lflag & (tcflag_t)ECHO) != 0);
	g_tcset_mode = 0;
	len = 0;
	(void)pty_until(master, buf, sizeof buf, &len, NULL, 200);
	CK(strstr(buf, "REFUSED: the console's echo could not be turned off")
	   != NULL);

	(void)close(slave);
	(void)close(master);
}

/* ------------------------------------------------------------------------- */
/* Constants and the device's environment                                    */
/* ------------------------------------------------------------------------- */

static void t_constants(void)
{
	struct fp_env e;

	/* the three writers of admin.pwhash agree on what they write */
	CK(KDF_LOG2N == BK_KDF_LOG2N && KDF_R == BK_KDF_R && KDF_P == BK_KDF_P);
	CK(PWHASH_LEN == BK_PWHASH_LEN && PWHASH_LEN == CFG_PWHASH_LEN);
	/* brokerd's gate and pwhash_salt's refusal are the same threshold */
	CK(KDF_ENTROPY_MIN == BK_ENTROPY_MIN);
	CK(FP_PW_MIN == 8 && FP_PW_MAX == 64);

	fp_env_dev(&e, 0, 1, CFG_FLASH_DEV);
	CK(e.in_fd == 0 && e.out_fd == 1);
	CK(e.store != NULL && strcmp(e.store, "/dev/mtd2ro") == 0);
	CK(e.entropy != NULL && e.salt != NULL && e.sleep_ms != NULL);
}

int main(void)
{
	char tmpl[PMAX], *abs;

	(void)signal(SIGPIPE, SIG_IGN);
	(void)snprintf(tmpl, sizeof tmpl, "%s", "./firstpw-XXXXXX");
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
	if (snprintf(p_store, sizeof p_store, "%s/cfg.bin", g_dir) >= PMAX ||
	    snprintf(p_out, sizeof p_out, "%s/console.out", g_dir) >= PMAX ||
	    snprintf(p_dirstore, sizeof p_dirstore, "%s/adir", g_dir) >= PMAX) {
		printf("FAIL the scratch path is too long\n");
		return 1;
	}

	t_constants();
	t_offer();
	t_absent();
	t_corrupt();
	t_valid_nohash();
	t_valid_hash();
	t_mismatch();
	t_lengths();
	t_entropy();
	t_unreadable();
	t_pty_echo();

	(void)unlink(p_store);
	(void)unlink(p_out);
	(void)rmdir(g_dir);
	printf("test_firstpw: %d checks, %d failures\n", checks, fails);
	return fails == 0 ? 0 : 1;
}
