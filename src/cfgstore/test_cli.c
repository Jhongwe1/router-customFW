/* test_cli.c -- the CLI's contract: its exit codes, its all-or-nothing SET, and
 * the two things it must never print.
 *
 * It runs the real binary.  fork + execv with a fixed argv array, never
 * system() and never popen() -- the same rule the product is held to, because a
 * test that shells out is a test that would have to be exempted from the R7
 * census.  stdout and stderr go to a scratch file and are read back, so a case
 * can assert on what was printed as well as on the status.
 *
 * argv[1] the cfgstore binary, argv[2] a scratch directory.
 */

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include "test_util.h"

#define PATH_MAX_ 512
#define OUT_MAX   65536

static char g_bin[PATH_MAX_];
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

int main(int argc, char **argv)
{
	int rc;

	if (argc < 3) {
		fputs("usage: test_cli <cfgstore binary> <scratch dir>\n", stderr);
		return 2;
	}
	snprintf(g_bin, sizeof g_bin, "%s", argv[1]);
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

	/* 🔴 `R7-8` REWROTE THIS GROUP.  It asserted that `passwd` refuses with
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
