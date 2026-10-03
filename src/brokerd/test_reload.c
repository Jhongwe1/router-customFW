/* src/brokerd/test_reload.c -- `FW-184`: a password set with `cfgstore passwd`
 * while brokerd runs must decide the very next request, with no restart.
 *
 * argv[1] is a host build of src/cfgstore, made by this directory's Makefile
 * from the sources the image's is made from, and every password change below
 * goes through it: fork, exec `cfgstore --file STORE passwd`, the password on
 * stdin.  So the write under test is cfgstore's own code path, not this
 * file's idea of it.
 *
 * WHY NOT OVER THE SOCKET.  test_wire.c runs the real daemon, but as an
 * ordinary uid, and SO_PEERCRED makes every op PERM there, so LOGIN cannot be
 * driven that way without root.  A broker here is a struct in this process,
 * "started" with the calls main() made at 5eaeb643 (bk_init, the store path,
 * ONE cfg_load), and every request goes through bk_dispatch(), which is what
 * main()'s loop calls.  NOT covered: main() itself.
 *
 * REFUTATION CONDITIONS, written before the run.  Any one of them is FW-184,
 * or a variant of it, still present:
 *   R1  a broker started before `cfgstore passwd` refuses the new password
 *       (the device's case, 2026-09-30: HTTP 401 for the right password)
 *   R2  after a change, the PREVIOUS password still logs in on a broker that
 *       held it -- a password the operator replaced keeps working
 *   R3  a session opened under the previous password still authorises a
 *       request after the change
 *   R4  with the slot being written cut short, a request is answered from
 *       anything but the last complete record (a mixture, or the older one)
 *   R5  with no valid record in either slot, or an unreadable store, any
 *       password logs in or any session survives -- stale credentials
 *   R6  R5's state is logged other than exactly once over several requests
 * The controls, without which a pass would mean nothing:
 *   C1  a broker started AFTER the write logs in with that password, so R1
 *       cannot be a format mismatch between cfgstore's hash and LOGIN; it is
 *       also the device's own experiment (`kill`, respawn, HTTP 200)
 *   C2  a wrong password is refused by the same broker in the same state
 *   C3  after R5, a repaired store logs in again: fail-closed is a state
 *   C4  the torn-write cases reach BOTH outcomes
 * A control that fails is counted apart from the checks, because it says the
 * fixture is broken rather than the code.
 */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include "brokerd.h"

#define STORE  "/tmp/rlxbk-store-test_reload.bin"
#define NEXT   "/tmp/rlxbk-store-test_reload.next"
#define ASIDE  "/tmp/rlxbk-store-test_reload.aside"
#define ENT    "/tmp/rlxbk_ent_reload"
#define ERRLOG "/tmp/rlxbk-test_reload.stderr"

#define PW1 "first-pass-1"
#define PW2 "second-pass-2"
#define PW3 "third-pass-3"
#define PW4 "fourth-pass-4"
#define BAD "not-the-password"

static int fails, ctl_fails, checks;
static uint32_t next_ip = 0x0A000001u;

#define CHECK(cond, ...) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

#define CONTROL(cond, ...) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		ctl_fails++; \
		(void)printf("  FAIL (CONTROL) %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

/* Run cfgstore on `store`: argv {cfgstore, --file, store, verb[, arg]}, an
 * empty environment, `in` on stdin.  stdout and stderr come back in out[].
 * Returns the exit status, or -1 if it did not exit normally. */
static int cfgstore(const char *bin, const char *store, const char *verb,
                    const char *arg, const char *in, char *out, size_t cap)
{
	int pin[2], pout[2], st = 0;
	size_t got = 0;
	pid_t p;

	out[0] = '\0';
	if (pipe(pin) != 0)
		return -1;
	if (pipe(pout) != 0) {
		(void)close(pin[0]);
		(void)close(pin[1]);
		return -1;
	}
	p = fork();
	if (p < 0)
		return -1;
	if (p == 0) {
		char *av[6];
		char *ev[1];
		int n = 0;

		if (dup2(pin[0], 0) < 0 || dup2(pout[1], 1) < 0 ||
		    dup2(pout[1], 2) < 0)
			_exit(126);
		(void)close(pin[0]);
		(void)close(pin[1]);
		(void)close(pout[0]);
		(void)close(pout[1]);
		av[n++] = (char *)"cfgstore";
		av[n++] = (char *)"--file";
		av[n++] = (char *)store;
		av[n++] = (char *)verb;
		if (arg != 0)
			av[n++] = (char *)arg;
		av[n] = 0;
		ev[0] = 0;
		(void)execve(bin, av, ev);
		_exit(127);
	}
	(void)close(pin[0]);
	(void)close(pout[1]);
	if (in != 0 && write(pin[1], in, strlen(in)) != (ssize_t)strlen(in))
		(void)printf("  note: short write to cfgstore's stdin\n");
	(void)close(pin[1]);
	for (;;) {
		ssize_t r = read(pout[0], out + got, cap - 1 - got);

		if (r < 0 && errno == EINTR)
			continue;
		if (r <= 0)
			break;
		got += (size_t)r;
		if (got + 1 >= cap)
			break;
	}
	out[got] = '\0';
	(void)close(pout[0]);
	while (waitpid(p, &st, 0) < 0)
		if (errno != EINTR)
			return -1;
	return WIFEXITED(st) ? WEXITSTATUS(st) : -1;
}

/* A broker the way main() started one at 5eaeb643: bk_init, the store path,
 * and ONE load at start-up.  The entropy file and the clock are the seams
 * every unit test in this directory sets. */
static void start(struct broker *bk)
{
	bk_init(bk);
	bk->entropy_path = ENT;
	bk->use_fake_clock = 1;
	bk->fake_now = 20000;
	bk->cfg_path = STORE;
	if (cfg_load(STORE, &bk->cfg) != 0)
		(void)cfg_defaults(&bk->cfg);
	(void)bk_entropy_ready(bk);
}

/* LOGIN as httpd, each call from a new client address so that no bucket ever
 * reaches the fifth failure that locks it.  On OK the two tokens are copied
 * out when asked for. */
static uint8_t login(struct broker *bk, const char *pw, uint8_t *tok, uint8_t *csrf)
{
	struct proto_req rq;
	struct proto_resp rs;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_LOGIN;
	rq.client_ip = next_ip++;
	rq.body_len = (uint32_t)strlen(pw);
	memcpy(rq.body, pw, rq.body_len);
	if (bk_dispatch(bk, &rq, BK_UID_HTTPD, &rs) != 0)
		return 0xFF;
	if (rs.status == ST_OK && rs.body_len == 2 * PROTO_TOK_LEN + 4) {
		if (tok != 0)
			memcpy(tok, rs.body, PROTO_TOK_LEN);
		if (csrf != 0)
			memcpy(csrf, rs.body + PROTO_TOK_LEN, PROTO_TOK_LEN);
	}
	return rs.status;
}

/* GET lan.ipaddr as httpd with a session: OK while the session lives. */
static uint8_t get_with(struct broker *bk, const uint8_t *tok, const uint8_t *csrf)
{
	struct proto_req rq;
	struct proto_resp rs;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = OP_GET;
	proto_put_be16(rq.body, CFGID_LAN_IPADDR);
	rq.body_len = 2;
	memcpy(rq.session, tok, PROTO_TOK_LEN);
	memcpy(rq.csrf, csrf, PROTO_TOK_LEN);
	if (bk_dispatch(bk, &rq, BK_UID_HTTPD, &rs) != 0)
		return 0xFF;
	return rs.status;
}

static int rd_file(const char *path, uint8_t *buf, size_t n)
{
	int fd = open(path, O_RDONLY);
	size_t got = 0;

	if (fd < 0)
		return -1;
	while (got < n) {
		ssize_t r = read(fd, buf + got, n - got);

		if (r < 0 && errno == EINTR)
			continue;
		if (r <= 0)
			break;
		got += (size_t)r;
	}
	(void)close(fd);
	return got == n ? 0 : -1;
}

static int wr_file(const char *path, const uint8_t *buf, size_t n)
{
	int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	size_t done = 0;

	if (fd < 0)
		return -1;
	while (done < n) {
		ssize_t w = write(fd, buf + done, n - done);

		if (w < 0 && errno == EINTR)
			continue;
		if (w <= 0)
			break;
		done += (size_t)w;
	}
	return (close(fd) == 0 && done == n) ? 0 : -1;
}

/* stderr into ERRLOG between err_begin() and err_end(), so a test can count
 * what bk_log() said.  err_end() prints what was caught, indented. */
static int saved_err = -1;
static char errtext[8192];

static void err_begin(void)
{
	int fd;

	(void)fflush(stderr);
	saved_err = dup(2);
	fd = open(ERRLOG, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd >= 0) {
		(void)dup2(fd, 2);
		(void)close(fd);
	}
}

static const char *err_end(void)
{
	int fd;
	ssize_t r;
	char *line;

	(void)fflush(stderr);
	if (saved_err >= 0) {
		(void)dup2(saved_err, 2);
		(void)close(saved_err);
		saved_err = -1;
	}
	errtext[0] = '\0';
	fd = open(ERRLOG, O_RDONLY);
	if (fd < 0)
		return errtext;
	r = read(fd, errtext, sizeof(errtext) - 1);
	(void)close(fd);
	errtext[r > 0 ? r : 0] = '\0';
	for (line = errtext; *line != '\0'; ) {
		char *nl = strchr(line, '\n');
		int len = nl ? (int)(nl - line) : (int)strlen(line);

		(void)printf("    log| %.*s\n", len, line);
		line += len + (nl ? 1 : 0);
	}
	return errtext;
}

static int count(const char *hay, const char *needle)
{
	int n = 0;
	size_t l = strlen(needle);

	while ((hay = strstr(hay, needle)) != 0) {
		n++;
		hay += l;
	}
	return n;
}

int main(int argc, char **argv)
{
	static struct broker x, y;
	static uint8_t cur[CFG_FILE_SIZE], nxt[CFG_FILE_SIZE], file[CFG_FILE_SIZE];
	uint8_t tok[PROTO_TOK_LEN], csrf[PROTO_TOK_LEN];
	char out[4096];
	const char *bin, *log;
	int rc, i, n_old = 0, n_new = 0;
	uint32_t ext;
	uint8_t a, b, c, g;

	(void)printf("test_reload\n");
	if (argc < 2) {
		(void)printf("  FAIL no cfgstore binary given\n");
		return 1;
	}
	bin = argv[1];
	/* A cfgstore that exits before reading its stdin must not kill us. */
	(void)signal(SIGPIPE, SIG_IGN);
	if (wr_file(ENT, (const uint8_t *)"4096\n", 5) != 0) {
		(void)printf("  FAIL cannot write %s\n", ENT);
		return 1;
	}
	(void)rmdir(STORE);
	(void)unlink(STORE);
	(void)unlink(NEXT);
	(void)unlink(ASIDE);

	/* ---- the device's case: the first password, set while brokerd runs */
	(void)printf("  -- R1: the first password, set after the broker started\n");
	rc = cfgstore(bin, STORE, "init", "--force", 0, out, sizeof(out));
	CONTROL(rc == 0, "cfgstore init --force rc=%d: %s", rc, out);
	start(&x);
	CONTROL(login(&x, PW1, 0, 0) == ST_AUTH,
	        "before any password is set, LOGIN must be AUTH");
	rc = cfgstore(bin, STORE, "passwd", 0, PW1 "\n", out, sizeof(out));
	CONTROL(rc == 0 && strstr(out, "written: slot 1, seq 2") != 0,
	        "cfgstore passwd rc=%d: %s", rc, out);
	start(&y);
	CONTROL(login(&y, PW1, 0, 0) == ST_OK,
	        "C1: a broker started after the write must accept it");
	a = login(&x, PW1, 0, 0);
	CHECK(a == ST_OK, "R1: the broker that was running refuses the password "
	      "cfgstore just set: status %u, want OK (%u)", a, ST_OK);
	CHECK(login(&x, BAD, 0, 0) == ST_AUTH, "C2: a wrong password must be AUTH");

	/* ---- a change, on a broker that held the previous password */
	(void)printf("  -- R2/R3: a change, on a broker holding the previous one\n");
	a = login(&y, PW1, tok, csrf);
	CONTROL(a == ST_OK, "a session under PW1: %u", a);
	CONTROL(get_with(&y, tok, csrf) == ST_OK,
	        "the session authorises a GET before the change");
	rc = cfgstore(bin, STORE, "passwd", 0, PW2 "\n", out, sizeof(out));
	CONTROL(rc == 0 && strstr(out, "written: slot 0, seq 3") != 0,
	        "cfgstore passwd rc=%d: %s", rc, out);
	g = get_with(&y, tok, csrf);
	CHECK(g == ST_AUTH, "R3: a session opened under the previous password "
	      "still authorises a GET: status %u, want AUTH (%u)", g, ST_AUTH);
	a = login(&y, PW2, 0, 0);
	CHECK(a == ST_OK, "R1: the new password: status %u, want OK", a);
	b = login(&y, PW1, 0, 0);
	CHECK(b == ST_AUTH, "R2: the password that was replaced still logs in: "
	      "status %u, want AUTH (%u)", b, ST_AUTH);

	/* ---- a write caught half-way.  The next record is made by cfgstore
	 * itself, on a copy, and then spliced into the store a prefix at a time:
	 * the slot being written is cut short at L bytes, and the slot holding
	 * the selected record is untouched, exactly as cfg_store leaves them. */
	(void)printf("  -- R4: the slot being written, cut short\n");
	rc = rd_file(STORE, cur, sizeof(cur));
	CONTROL(rc == 0, "read %s", STORE);
	rc = (rc == 0) ? wr_file(NEXT, cur, sizeof(cur)) : -1;
	CONTROL(rc == 0, "copy to %s", NEXT);
	rc = cfgstore(bin, NEXT, "passwd", 0, PW3 "\n", out, sizeof(out));
	CONTROL(rc == 0 && strstr(out, "written: slot 1, seq 4") != 0,
	        "cfgstore passwd on the copy rc=%d: %s", rc, out);
	CONTROL(rd_file(NEXT, nxt, sizeof(nxt)) == 0, "read %s", NEXT);
	ext = CFG_HDR_LEN + proto_be32(nxt + CFG_SLOT_SIZE + 12);
	CONTROL(ext > CFG_HDR_LEN && ext < CFG_SLOT_SIZE, "record extent %lu",
	        (unsigned long)ext);
	{
		const uint32_t lens[] = { 0, CFG_HDR_LEN, ext - 1, ext, CFG_SLOT_SIZE };

		for (i = 0; i < (int)(sizeof(lens) / sizeof(lens[0])); i++) {
			uint32_t L = lens[i];
			int complete;

			memcpy(file, cur, sizeof(file));
			memcpy(file + CFG_SLOT_SIZE, nxt + CFG_SLOT_SIZE, L);
			/* Decided from the bytes, not from L: if the byte after the
			 * cut already equals the new record's, a cut at ext-1 IS
			 * complete, and the loader is right to take it. */
			complete = (memcmp(file + CFG_SLOT_SIZE, nxt + CFG_SLOT_SIZE,
			                   ext) == 0);
			if (wr_file(STORE, file, sizeof(file)) != 0) {
				CONTROL(0, "write %s", STORE);
				continue;
			}
			a = login(&y, PW2, 0, 0);
			b = login(&y, PW3, 0, 0);
			c = login(&y, PW1, 0, 0);
			CHECK(a == (complete ? ST_AUTH : ST_OK) &&
			      b == (complete ? ST_OK : ST_AUTH) && c == ST_AUTH,
			      "R4: L=%lu (%s): PW2 %u PW3 %u PW1 %u", (unsigned long)L,
			      complete ? "complete" : "torn", a, b, c);
			if (a == ST_OK)
				n_old++;
			if (b == ST_OK)
				n_new++;
			(void)printf("     L=%-4lu %-8s PW2 %u  PW3 %u  PW1 %u\n",
			             (unsigned long)L, complete ? "complete" : "torn",
			             a, b, c);
		}
	}
	CONTROL(n_old > 0 && n_new > 0, "C4: the cut reached both outcomes "
	        "(previous record %d times, new record %d times)", n_old, n_new);

	/* ---- no valid record in either slot */
	(void)printf("  -- R5/R6: no valid record in either slot\n");
	CONTROL(wr_file(STORE, nxt, sizeof(nxt)) == 0, "write %s", STORE);
	a = login(&y, PW3, tok, csrf);
	CONTROL(a == ST_OK, "a session under PW3: %u", a);
	memcpy(file, nxt, sizeof(file));
	file[CFG_HDR_LEN + 2] ^= 0x01;                 /* slot 0's payload */
	file[CFG_SLOT_SIZE + CFG_HDR_LEN + 2] ^= 0x01; /* slot 1's payload */
	CONTROL(wr_file(STORE, file, sizeof(file)) == 0, "write %s", STORE);
	err_begin();
	a = login(&y, PW3, 0, 0);
	b = login(&y, PW3, 0, 0);
	g = get_with(&y, tok, csrf);
	c = login(&y, PW2, 0, 0);
	log = err_end();
	CHECK(a == ST_AUTH && b == ST_AUTH, "R5: no valid record, yet the last "
	      "good password is answered %u, %u; want AUTH", a, b);
	CHECK(c == ST_AUTH, "R5: an older password: %u, want AUTH", c);
	CHECK(g == ST_AUTH, "R5: a session survived the store going bad: %u", g);
	i = count(log, "holds no valid record");
	CHECK(i == 1, "R6: 'holds no valid record' logged %d times over four "
	      "requests, want once", i);

	/* ---- repaired, then unreadable */
	(void)printf("  -- C3, then R5/R6 for a store that cannot be read\n");
	rc = cfgstore(bin, STORE, "init", "--force", 0, out, sizeof(out));
	CONTROL(rc == 0, "cfgstore init --force over the bad store rc=%d: %s",
	        rc, out);
	rc = cfgstore(bin, STORE, "passwd", 0, PW4 "\n", out, sizeof(out));
	CONTROL(rc == 0, "cfgstore passwd rc=%d: %s", rc, out);
	err_begin();
	a = login(&y, PW4, tok, csrf);
	log = err_end();
	CHECK(a == ST_OK, "C3: the repaired store must log in again: %u", a);
	i = count(log, "readable again");
	CHECK(i == 1, "the recovery logged %d times, want once", i);
	/* A directory where the file was: open(O_RDONLY) succeeds on it and
	 * read() fails with EISDIR, which is cfg_load_info's I/O path for any
	 * uid -- chmod 000 would not stop a root test run. */
	rc = rename(STORE, ASIDE);
	CONTROL(rc == 0 && mkdir(STORE, 0700) == 0, "a directory at %s", STORE);
	err_begin();
	a = login(&y, PW4, 0, 0);
	b = login(&y, PW4, 0, 0);
	g = get_with(&y, tok, csrf);
	log = err_end();
	CHECK(a == ST_AUTH && b == ST_AUTH, "R5: unreadable store, yet the "
	      "last good password is answered %u, %u; want AUTH", a, b);
	CHECK(g == ST_AUTH, "R5: a session survived an unreadable store: %u", g);
	i = count(log, "unreadable");
	CHECK(i == 1, "R6: 'unreadable' logged %d times over three requests, "
	      "want once", i);
	(void)rmdir(STORE);
	CONTROL(rename(ASIDE, STORE) == 0, "put %s back", STORE);
	CHECK(login(&y, PW4, 0, 0) == ST_OK, "C3: the store back in place");

	(void)unlink(NEXT);
	(void)unlink(ERRLOG);
	(void)printf("test_reload: %d checks, %d failures (%d of them controls)\n",
	             checks, fails, ctl_fails);
	return fails == 0 ? 0 : 1;
}
