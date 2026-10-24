/* test_cli.c -- the CLI's contract: its exit codes, its all-or-nothing SET, and
 * the two things it must never print.
 *
 * It runs the real binary.  fork + execv with a fixed argv array, never
 * system() and never popen() -- the same rule the product is held to, because a
 * test that shells out is a test that would have to be exempted from the R7
 * census.  stdout and stderr go to a scratch file and are read back, so a case
 * can assert on what was printed as well as on the status.
 *
 * argv[1] the cfgstore binary, argv[2] a scratch directory, argv[3]
 * cfgstore-tty (main.c with tcsetattr wrapped by ttyfault.c).
 */

#define _GNU_SOURCE	/* posix_openpt, grantpt, unlockpt, ptsname */

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#include "test_util.h"

#define PATH_MAX_ 512
#define OUT_MAX   65536

static char g_bin[PATH_MAX_];
static char g_ttybin[PATH_MAX_];
static char g_store[PATH_MAX_];
static char g_out[PATH_MAX_];
static char g_in[PATH_MAX_];
static char g_buf[OUT_MAX];

/* Runs the binary with the NULL-terminated argv (argv[0] is replaced by the
 * real path), feeds `stdin_text` if not NULL, and returns the exit status or
 * -1.  The captured output is left in g_buf, NUL-terminated. */
static int run(char **argv, const char *stdin_text)
{
	pid_t pid;
	int status = -1, fd;
	ssize_t n;

	g_buf[0] = '\0';
	argv[0] = g_bin;

	if (stdin_text != NULL) {
		FILE *f = fopen(g_in, "wb");

		if (f == NULL)
			return -1;
		fputs(stdin_text, f);
		fclose(f);
	}

	pid = fork();
	if (pid < 0)
		return -1;
	if (pid == 0) {
		int o = open(g_out, O_WRONLY | O_CREAT | O_TRUNC, 0600);
		int i = (stdin_text != NULL) ? open(g_in, O_RDONLY)
					     : open("/dev/null", O_RDONLY);

		if (o < 0 || i < 0)
			_exit(126);
		if (dup2(o, 1) < 0 || dup2(o, 2) < 0 || dup2(i, 0) < 0)
			_exit(126);
		execv(g_bin, argv);
		_exit(127);
	}
	if (waitpid(pid, &status, 0) != pid)
		return -1;

	fd = open(g_out, O_RDONLY);
	if (fd >= 0) {
		n = read(fd, g_buf, sizeof g_buf - 1);
		g_buf[(n > 0) ? (size_t)n : 0] = '\0';
		close(fd);
	}
	if (!WIFEXITED(status))
		return -1;
	return WEXITSTATUS(status);
}

static int has(const char *needle)
{
	return strstr(g_buf, needle) != NULL;
}

static void show_out(void)
{
	printf("      --- output ---\n%s      --------------\n", g_buf);
}

#define A0(v)			 { NULL, (char *)"--file", g_store, (char *)v, NULL }
#define A1(v, a)		 { NULL, (char *)"--file", g_store, (char *)v, (char *)a, NULL }
#define A2(v, a, b)		 { NULL, (char *)"--file", g_store, (char *)v, (char *)a, (char *)b, NULL }

/* ------------------------------------------------------------------------- */
/* The pty: what the console shows (notes/self-update.md § 6.4).  The child's  */
/* stdin, stdout and stderr are the slave, so every byte the line discipline  */
/* echoes and every byte the program prints is read from the master.          */
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

/* Read the master into buf (appending) until `want` appears, the timeout
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

/* waitpid with a deadline: a child still reading the console after a refusal
 * is killed and reported, not waited for.  1 when it exited (st set). */
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

/* bin on the pty, CFGSTORE_TTYFAULT set to fault (or unset). */
static pid_t spawn_tty(const char *bin, char **argv, int master, int slave,
		       const char *fault)
{
	pid_t pid = fork();

	if (pid != 0)
		return pid;
	(void)close(master);
	if (fault != NULL)
		(void)setenv("CFGSTORE_TTYFAULT", fault, 1);
	else
		(void)unsetenv("CFGSTORE_TTYFAULT");
	if (dup2(slave, 0) < 0 || dup2(slave, 1) < 0 || dup2(slave, 2) < 0)
		_exit(126);
	argv[0] = (char *)bin;
	execv(bin, argv);
	_exit(127);
}

static size_t read_file(const char *path, char *buf, size_t cap)
{
	FILE *f = fopen(path, "rb");
	size_t n;

	if (f == NULL)
		return 0;
	n = fread(buf, 1, cap, f);
	fclose(f);
	return n;
}

static int echo_is_on(int fd)
{
	struct termios t;

	return tcgetattr(fd, &t) == 0 && (t.c_lflag & (tcflag_t)ECHO) != 0;
}

static void t_passwd_tty(void)
{
	static char buf[OUT_MAX], before[3 * 4096], after[3 * 4096];
	static const char *const fault[2] = { "fail", "keep" };
	char *a[] = A0("passwd");
	const char *bin[2];
	size_t len = 0, nb, na;
	int master = -1, slave = -1, st = -1, ok, k;
	pid_t pid;
	ssize_t w;

	T_GROUP("passwd on a tty: echo off, read back");
	if (pty_open(&master, &slave) != 0) {
		CHECK(0, "a pty: errno %d", errno);
		return;
	}

	/* The control: with echo on, a canary typed is seen on the master. */
	CHECK(echo_is_on(slave), "the pty starts with echo on");
	w = write(master, "canary-0451\n", 12);
	(void)w;
	CHECK(pty_until(master, buf, sizeof buf, &len, "canary-0451", 2000) == 1,
	      "the control: a canary typed with echo on is seen on the master");
	{
		char sink[64];

		w = read(slave, sink, sizeof sink);	/* consume the line */
		(void)w;
	}

	/* Permitting, on the real binary and on cfgstore-tty with no fault:
	 * the prompt, the password typed after it, and the password nowhere in
	 * what the console showed.  The read comes before the entropy draw, so
	 * the property holds whichever way the pool answers (0 or 3). */
	bin[0] = g_bin;
	bin[1] = g_ttybin;
	for (k = 0; k < 2; k++) {
		len = 0;
		pid = spawn_tty(bin[k], a, master, slave, NULL);
		CHECK(pid > 0, "fork: errno %d", errno);
		ok = pid > 0 ? pty_until(master, buf, sizeof buf, &len,
					 "new password: ", 5000) : 0;
		CHECK(ok == 1, "%s: the prompt", bin[k]);
		w = write(master, "hunter2-secret\n", 15);
		(void)w;
		ok = pid > 0 ? wait_bounded(pid, 30000, &st) : 0;
		(void)pty_until(master, buf, sizeof buf, &len, NULL, 200);
		CHECK(ok == 1 && WIFEXITED(st) &&
		      (WEXITSTATUS(st) == 0 || WEXITSTATUS(st) == 3),
		      "%s: passwd on a tty exits 0 or 3, got %d", bin[k],
		      (ok == 1 && WIFEXITED(st)) ? WEXITSTATUS(st) : -1);
		CHECK(strstr(buf, "admin.pwhash set") != NULL ||
		      strstr(buf, "entropy_avail") != NULL,
		      "%s: and it read the line and went on", bin[k]);
		CHECK(strstr(buf, "hunter2") == NULL,
		      "%s: the password is nowhere in what the console showed",
		      bin[k]);
		if (strstr(buf, "hunter2") != NULL)
			printf("      the console showed:\n%s\n", buf);
		CHECK(echo_is_on(slave), "%s: echo is back on afterwards", bin[k]);
	}

	/* Refusing: tcsetattr fails, or answers 0 and leaves echo on.  No
	 * password is read -- a child that went on to read would sit on the
	 * console until the deadline -- and the store's bytes do not move. */
	for (k = 0; k < 2; k++) {
		nb = read_file(g_store, before, sizeof before);
		len = 0;
		pid = spawn_tty(g_ttybin, a, master, slave, fault[k]);
		CHECK(pid > 0, "fork: errno %d", errno);
		ok = pid > 0 ? wait_bounded(pid, 5000, &st) : 0;
		CHECK(ok == 1, "%s: the step exited within 5 s (not reading)",
		      fault[k]);
		CHECK(ok == 1 && WIFEXITED(st) && WEXITSTATUS(st) == 3,
		      "%s: refused with 3, got %d", fault[k],
		      (ok == 1 && WIFEXITED(st)) ? WEXITSTATUS(st) : -1);
		(void)pty_until(master, buf, sizeof buf, &len, NULL, 200);
		CHECK(strstr(buf, "the tty's echo could not be turned off") !=
		      NULL, "%s: and said why", fault[k]);
		CHECK(strstr(buf, "new password: ") == NULL,
		      "%s: and asked for nothing", fault[k]);
		na = read_file(g_store, after, sizeof after);
		CHECK(nb > 0 && na == nb && memcmp(before, after, nb) == 0,
		      "%s: the store's bytes are unchanged", fault[k]);
		CHECK(echo_is_on(slave), "%s: echo is on afterwards", fault[k]);
	}

	(void)close(slave);
	(void)close(master);
}

int main(int argc, char **argv)
{
	int rc;

	if (argc < 4) {
		fputs("usage: test_cli <cfgstore binary> <scratch dir>"
		      " <cfgstore-tty binary>\n", stderr);
		return 2;
	}
	(void)signal(SIGPIPE, SIG_IGN);
	snprintf(g_bin, sizeof g_bin, "%s", argv[1]);
	snprintf(g_ttybin, sizeof g_ttybin, "%s", argv[3]);
	snprintf(g_store, sizeof g_store, "%s/test_cli_store.bin", argv[2]);
	snprintf(g_out, sizeof g_out, "%s/test_cli_out.txt", argv[2]);
	snprintf(g_in, sizeof g_in, "%s/test_cli_in.txt", argv[2]);
	remove(g_store);

	T_GROUP("usage");
	{
		char *a[] = { NULL, NULL };
		char *b[] = { NULL, (char *)"badverb", NULL };

		rc = run(a, NULL);
		CHECK(rc == 1, "no arguments must exit 1, got %d", rc);
		rc = run(b, NULL);
		CHECK(rc == 1, "an unknown verb must exit 1, got %d", rc);
		CHECK(has("no such command"), "and say so");
	}

	T_GROUP("get on an absent store");
	{
		char *a[] = A0("get");

		rc = run(a, NULL);
		CHECK(rc == 0, "an absent store reads as defaults, exit 0, got %d",
		      rc);
		CHECK(has("lan.ipaddr=10.1.1.1"), "the default LAN address");
		CHECK(has("admin.pwhash=unset"),
		      "and admin.pwhash reported as unset");
		if (!has("admin.pwhash=unset"))
			show_out();
	}

	T_GROUP("init --force");
	{
		char *a[] = A1("init", "--force");
		char *b[] = A0("init");

		rc = run(b, NULL);
		CHECK(rc == 1, "init without --force must exit 1, got %d", rc);
		rc = run(a, NULL);
		CHECK(rc == 0, "init --force: %d", rc);
		CHECK(has("slot 0") && has("seq 1"), "it must say where it wrote");
		if (rc != 0)
			show_out();
	}

	T_GROUP("get prints values, never the hash");
	{
		char *a[] = A0("get");
		char *b[] = A1("get", "sys.hostname");
		char *c[] = A1("get", "nosuchkey");

		rc = run(a, NULL);
		CHECK(rc == 0, "get: %d", rc);
		CHECK(has("sys.hostname=rlxfw"), "hostname");
		CHECK(has("dhcpd.lease=86400"), "lease");
		CHECK(has("http.port=80"), "port");
		CHECK(has("wan.netmask=0.0.0.0"), "wan netmask");
		CHECK(has("admin.pwhash=unset"), "pwhash as a word");
		rc = run(b, NULL);
		CHECK(rc == 0 && has("sys.hostname=rlxfw"), "get by name: %d", rc);
		CHECK(strchr(g_buf, '\n') == g_buf + strlen("sys.hostname=rlxfw"),
		      "get by name must print exactly one line");
		rc = run(c, NULL);
		CHECK(rc == 2, "an unknown key name must exit 2, got %d", rc);
		CHECK(has("nosuchkey"), "and name it");
	}

	T_GROUP("set: invalid values exit 2 and name the key");
	{
		char *a[] = A1("set", "http.port=0");
		char *b[] = A1("set", "lan.ipaddr=10.1.1.150");
		char *c[] = A1("set", "sys.hostname=-bad");
		char *d[] = A1("set", "noequals");
		char *e[] = A1("set", "nosuch=1");
		char *f[] = A1("set", "admin.pwhash=00");

		rc = run(a, NULL);
		CHECK(rc == 2, "http.port=0 must exit 2, got %d", rc);
		CHECK(has("http.port"), "and name http.port");
		rc = run(b, NULL);
		CHECK(rc == 2, "a cross-field violation must exit 2, got %d", rc);
		CHECK(has("lan.ipaddr"), "and name lan.ipaddr");
		rc = run(c, NULL);
		CHECK(rc == 2, "a bad hostname must exit 2, got %d", rc);
		rc = run(d, NULL);
		CHECK(rc == 1, "an argument without = is usage, exit 1, got %d",
		      rc);
		rc = run(e, NULL);
		CHECK(rc == 2, "an unknown key must exit 2, got %d", rc);
		rc = run(f, NULL);
		CHECK(rc == 2, "admin.pwhash is not settable by `set', got %d",
		      rc);
		CHECK(has("passwd"), "and it must point at `passwd'");
	}

	T_GROUP("set: all-or-nothing");
	{
		char *ok[] = A2("set", "sys.hostname=box", "dhcpd.lease=300");
		char *bad[] = A2("set", "sys.hostname=later", "dhcpd.lease=1");
		char *get[] = A0("get");

		rc = run(ok, NULL);
		CHECK(rc == 0, "two valid assignments: %d", rc);
		rc = run(get, NULL);
		CHECK(has("sys.hostname=box") && has("dhcpd.lease=300"),
		      "both landed");

		rc = run(bad, NULL);
		CHECK(rc == 2, "one bad assignment must exit 2, got %d", rc);
		CHECK(has("dhcpd.lease"), "and name the offending key");
		rc = run(get, NULL);
		CHECK(has("sys.hostname=box"),
		      "the good assignment in the same command must NOT have"
		      " landed");
		CHECK(!has("sys.hostname=later"), "nothing was written");
	}

	T_GROUP("unset");
	{
		char *a[] = A1("unset", "sys.hostname");
		char *b[] = A1("unset", "nosuch");
		char *get[] = A0("get");

		rc = run(a, NULL);
		CHECK(rc == 0, "unset: %d", rc);
		rc = run(get, NULL);
		CHECK(has("sys.hostname=rlxfw"),
		      "an unset key reads as its default again");
		rc = run(b, NULL);
		CHECK(rc == 2, "unset of an unknown key must exit 2, got %d", rc);
	}

	T_GROUP("show and dump");
	{
		char *a[] = A0("show");
		char *b[] = A1("dump", "--hex");
		char *c[] = A0("dump");

		rc = run(a, NULL);
		CHECK(rc == 0, "show: %d", rc);
		CHECK(has("NAME") && has("VALUE") && has("SOURCE") &&
		      has("SEQ"), "show must print a header row");
		CHECK(has("<unset>") || has("<set>"),
		      "and admin.pwhash as a word, never as bytes");
		CHECK(has("slot0"), "and which slot the record came from");
		rc = run(b, NULL);
		CHECK(rc == 0, "dump --hex: %d", rc);
		CHECK(has("slot 0") && has("slot 1"), "both slots");
		CHECK(has("524c5843"), "and the magic in the hex");
		rc = run(c, NULL);
		CHECK(rc == 1, "dump without --hex must exit 1, got %d", rc);
	}

	T_GROUP("a corrupt store: 4 for get, 0 for dump");
	{
		char *g[] = A0("get");
		char *s[] = A1("set", "sys.hostname=zz");
		char *d[] = A1("dump", "--hex");
		char *i[] = A1("init", "--force");
		FILE *f = fopen(g_store, "r+b");
		int k;

		CHECK(f != NULL, "reopen the store to corrupt it");
		if (f != NULL) {
			/* Break both slots: one byte inside each record. */
			for (k = 0; k < 2; k++) {
				if (fseek(f, (long)k * 4096 + 9, SEEK_SET) == 0)
					fputc(0xA5, f);
			}
			fclose(f);
		}
		rc = run(g, NULL);
		CHECK(rc == 4, "get on a corrupt store must exit 4, got %d", rc);
		CHECK(has("no valid record"), "and say what is wrong");
		rc = run(s, NULL);
		CHECK(rc == 4, "set on a corrupt store must exit 4, got %d", rc);
		rc = run(d, NULL);
		CHECK(rc == 0, "dump on a corrupt store must still work, got %d",
		      rc);
		CHECK(has("header not believable") || has("verdict"),
		      "and print a verdict per slot");
		rc = run(i, NULL);
		CHECK(rc == 0, "init --force must repair it, got %d", rc);
		rc = run(g, NULL);
		CHECK(rc == 0, "and then get works again, got %d", rc);
	}

	/* NOTE: `R7-8` REWROTE THIS GROUP.  It asserted that `passwd` refuses with
	 * EX_IO and the words REFUSED/ENOSYS, which was right while src/lib/kdf.h
	 * was a declaration returning -ENOSYS.  The real scrypt landed in the same
	 * segment, KDF_IMPLEMENTED is 1, and cmd_passwd now derives and stores a
	 * 56-byte blob -- so the old assertions were asserting the absence of a
	 * feature that exists, and they were the only three FAILs in the tree.
	 *
	 * The refusal path is kept as the ENTROPY branch, which is a refusal THIS
	 * HOST MAY OR MAY NOT TAKE: pwhash_salt() reads
	 * /proc/sys/kernel/random/entropy_avail and refuses below 128.  Both
	 * outcomes are checked and which one ran is printed, because a case that
	 * silently accepts either outcome is a case that tests nothing. */
	T_GROUP("passwd derives and stores, or refuses on entropy");
	{
		char *a[] = A0("passwd");
		char *b[] = A1("passwd", "hunter2");
		char *s2[] = A1("passwd", "one");
		char *g[] = A0("get");
		char *d[] = A1("dump", "--hex");
		int set_ok;

		rc = run(a, "hunter2hunter2\n");
		set_ok = (rc == 0);
		CHECK(rc == 0 || rc == 3,
		      "passwd must either succeed (0) or refuse on entropy (3), got"
		      " %d", rc);
		if (rc == 0) {
			(void)printf("#   passwd SUCCEEDED: the pool was ready\n");
			CHECK(has("admin.pwhash set"), "and say so");
			CHECK(has("scrypt log2N=12 r=7 p=1"),
			      "and name the parameters it used");
			CHECK(has("written: slot"), "and name the slot it wrote");
		} else {
			(void)printf("#   passwd REFUSED: the pool was not ready\n");
			CHECK(has("REFUSED"), "and say REFUSED");
			CHECK(has("entropy_avail"), "and print the reading");
			CHECK(has("Nothing was written"),
			      "and say nothing was written");
		}
		if (rc != 0 && rc != 3)
			show_out();

		rc = run(b, NULL);
		CHECK(rc == 1, "a password in argv must be refused, got %d", rc);
		CHECK(has("never from argv"), "and say why");

		rc = run(s2, NULL);
		CHECK(rc == 1, "and so must a short one in argv, got %d", rc);

		rc = run(a, "short\n");
		CHECK(rc == 2, "a password under 8 bytes must exit 2, got %d", rc);
		CHECK(has("8..64"), "and name the range");

		rc = run(g, NULL);
		CHECK(rc == 0, "get still works after passwd, got %d", rc);
		CHECK(set_ok ? !has("admin.pwhash=unset")
			     : has("admin.pwhash=unset"),
		      "admin.pwhash's presence matches whether passwd succeeded");
		rc = run(d, NULL);
		CHECK(rc == 0, "dump still works, got %d", rc);
	}

	t_passwd_tty();

	T_GROUP("an unwritable store is 3, not 0");
	{
		char save[PATH_MAX_];
		char *a[] = A1("set", "sys.hostname=zz");

		snprintf(save, sizeof save, "%s", g_store);
		snprintf(g_store, sizeof g_store,
			 "/proc/rlxfw-no-such-dir/cfg.bin");
		rc = run(a, NULL);
		CHECK(rc == 3, "a store that cannot be opened must exit 3, got"
		      " %d", rc);
		snprintf(g_store, sizeof g_store, "%s", save);
	}

	remove(g_store);
	remove(g_out);
	remove(g_in);
	return t_done("cli");
}
