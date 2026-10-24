/* src/brokerd/test_e2e.c -- POST /api/firmware end to end on the host: httpd's
 * real request path (srv_conn, route_stream_gate, upload.c) and the real
 * broker client (src/lib/client.c) talking to a real brokerd loop (loop.c,
 * ops.c, update.c) over an AF_UNIX socket, so the two implementations of the
 * update wire format (src/lib/proto.h) are checked against each other and
 * not only against the stand-ins each side's own suite uses.
 *
 *   test_e2e <fixture dir> <scratch dir>
 *
 * Three processes.  The test forks a brokerd child that runs bk_loop_step()
 * over a listening socket, with simkern's rtl819x-spi behind it; for each
 * case it forks a writer that sends the HTTP request -- head, then the body in
 * uneven segments -- into one end of a socketpair, and runs srv_conn() on the
 * other end itself, which makes one bk_call() per broker op exactly as httpd's
 * connection child does.
 *
 * THE ONE STAND-IN, stated: the brokerd child accepts each connection itself
 * and adopts it with uid 100, which is what SO_PEERCRED names for httpd on the
 * device (it runs as uid 100); this test is one uid and cannot be two.  The
 * session httpd presents is one the child's broker issued before the fork.
 *
 * Asserted per case: the HTTP status and the JSON body exactly; brokerd's
 * STATUS line for it; and from simkern's event log (written by the brokerd
 * child) that a refusal made no verb, no staging write and no lock, and that
 * the accepted upload made the whole install sequence and one reboot request.
 * The install runs after the 200 has left, so every check of the child's side
 * waits for barrier() first.
 *
 * WHAT IT DOES NOT ESTABLISH.  TCP, the real fork-per-connection child of
 * srv_loop() and its alarm(2), SO_PEERCRED's uid, the device's kernel: none of
 * them is in this picture.
 */
#define _GNU_SOURCE 1

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include "brokerd.h"
#include "client.h"
#include "sha256.h"
#include "simkern.h"
#include "../httpd/http.h"
#include "../httpd/routes.h"
#include "../httpd/serve.h"
#include "../httpd/upload.h"
#include "../rlxboot/rlxboot.h"
#include "../rlxboot/container.h"

static int fails, nchecks;

#define CHECK(cond, ...) do { \
	nchecks++; \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

static const char *fixdir, *rundir;
static char sock_path[600], boot_file[600], store_file[600], reboot_file[600],
            log_file[600];
static pid_t bkpid = -1;
static uint8_t tok[PROTO_TOK_LEN], csrf[PROTO_TOK_LEN];

struct blob {
	uint8_t *p;
	size_t   n;
};

static struct blob fx_a5, fx_b6, fx_b7, fx_b6big, fx_b6key;

static void load(struct blob *b, const char *name)
{
	char path[700];
	struct stat st;
	FILE *f;

	(void)snprintf(path, sizeof(path), "%s/%s.rlxu", fixdir, name);
	if (stat(path, &st) != 0 || st.st_size <= 0) {
		(void)printf("  FAIL fixture %s is missing: run src/brokerd/mkfix.sh\n", path);
		exit(2);
	}
	b->n = (size_t)st.st_size;
	b->p = malloc(b->n + 8);
	f = fopen(path, "rb");
	if (b->p == 0 || f == 0 || fread(b->p, 1, b->n, f) != b->n) {
		(void)printf("  FAIL fixture %s unreadable\n", path);
		exit(2);
	}
	(void)fclose(f);
}

static void put_text(const char *path, const char *text)
{
	FILE *f = fopen(path, "w");

	if (f == 0 || fputs(text, f) < 0 || fclose(f) != 0) {
		(void)printf("  FAIL cannot write %s\n", path);
		exit(2);
	}
}

/* The part, as test_update's layout(): simkern's low-64-KiB pattern, 0xFF,
 * the two slots, the counter.  Written whole, by path: the brokerd child
 * opens /dev/mtd2ro (simkern's file) again for every read. */
static void layout(const struct blob *a, const struct blob *b, unsigned ctr,
                   const char *boot)
{
	static uint8_t chip[SIMK_CHIP];
	unsigned i;
	FILE *f;

	memset(chip, 0xFF, sizeof(chip));
	for (i = 0; i < 0x10000u; i++)
		chip[i] = (uint8_t)((i * 7u + 1u) & 0x7Fu);
	if (a != 0)
		memcpy(chip + RLXB_SLOT_A_FLASH, a->p, a->n);
	if (b != 0)
		memcpy(chip + RLXB_SLOT_B_FLASH, b->p, b->n);
	for (i = 0; i < ctr; i++)
		chip[RLXB_CTR_FLASH + i / 8] =
			(uint8_t)(chip[RLXB_CTR_FLASH + i / 8] & ~(0x80u >> (i % 8)));
	f = fopen(simk_flash_file(), "wb");
	if (f == 0 || fwrite(chip, 1, sizeof(chip), f) != sizeof(chip) ||
	    fclose(f) != 0) {
		(void)printf("  FAIL cannot lay out %s\n", simk_flash_file());
		exit(2);
	}
	put_text(boot_file, boot);
	put_text(log_file, "");          /* the child appends; start empty */
}

/* ------------------------------------------------------ the brokerd child */

static int e2e_reboot(void)
{
	FILE *f = fopen(reboot_file, "a");

	if (f != 0) {
		(void)fputs("reboot\n", f);
		(void)fclose(f);
	}
	return -EPERM;
}

static void broker_child(struct broker *bk, int lfd, pid_t parent)
{
	struct bk_loop L;

	bk_loop_init(&L);
	for (;;) {
		struct pollfd p;

		if (getppid() != parent)
			_exit(0);
		p.fd = lfd;
		p.events = POLLIN;
		p.revents = 0;
		if (poll(&p, 1, 0) > 0) {
			int c = accept(lfd, 0, 0);

			if (c >= 0)
				(void)bk_loop_adopt(&L, c, BK_UID_HTTPD);
		}
		(void)bk_loop_step(bk, &L, -1, 5);
	}
}

static int start_broker(void)
{
	static struct broker bk;
	struct bk_sess *s;
	pid_t parent = getpid();
	int lfd;

	bk_init(&bk);
	bk.cfg_path = store_file;
	bk.boot_path = boot_file;
	bk.upd_reboot = e2e_reboot;
	s = bk_sess_new(&bk);
	if (s == 0)
		return -1;
	memcpy(tok, s->tok, PROTO_TOK_LEN);
	memcpy(csrf, s->csrf, PROTO_TOK_LEN);
	lfd = bk_bind_socket(sock_path, 0600, (gid_t)-1);
	if (lfd < 0)
		return -1;
	(void)fflush(stdout);
	(void)fflush(stderr);
	bkpid = fork();
	if (bkpid < 0)
		return -1;
	if (bkpid == 0) {
		broker_child(&bk, lfd, parent);
		_exit(0);
	}
	(void)close(lfd);
	return 0;
}

/* ------------------------------------------------------- the httpd side */

static unsigned armed = 20;

/* alarm(2) as route_env.alarm_fn: what was armed comes back, `secs` is armed. */
static unsigned e2e_alarm(unsigned secs)
{
	unsigned prev = armed;

	armed = secs;
	return prev;
}

static int grant(void *ctx, uint32_t *retry_s)
{
	(void)ctx;
	*retry_s = 0;
	return 1;
}

static int wr_all(int fd, const uint8_t *p, size_t n)
{
	while (n > 0) {
		ssize_t w = write(fd, p, n);

		if (w < 0 && errno == EINTR)
			continue;
		if (w <= 0)
			return -1;
		p += w;
		n -= (size_t)w;
	}
	return 0;
}

static void hex16(const uint8_t *p, char *out)
{
	static const char hx[] = "0123456789abcdef";
	int i;

	for (i = 0; i < 16; i++) {
		out[2 * i] = hx[p[i] >> 4];
		out[2 * i + 1] = hx[p[i] & 15];
	}
	out[32] = '\0';
}

/* One upload through srv_conn().  `clen` is the declared Content-Length; the
 * body is img[0..n).  Returns srv_conn()'s status; the answer is in out. */
static int exchange(const char *clen, const uint8_t *img, size_t n, char *out,
                    size_t cap)
{
	static const size_t seg[] = { 1, 7, 2043, 2045, 4096, 65536 };
	struct route_env env;
	char head[700], ts[33], tc[33];
	size_t got = 0;
	pid_t w;
	int sv[2], st;

	hex16(tok, ts);
	hex16(csrf, tc);
	(void)snprintf(head, sizeof(head),
	               "POST /api/firmware HTTP/1.1\r\n"
	               "Host: 10.1.1.1\r\n"
	               "Cookie: rlxs=%s; rlxc=%s;\r\n"
	               "X-RLX-CSRF: %s\r\n"
	               "Content-Type: application/octet-stream\r\n"
	               "Content-Length: %s\r\n\r\n", ts, tc, tc, clen);
	memset(&env, 0, sizeof(env));
	env.sock = sock_path;
	env.client_ip = 0x0a010164u;
	env.kdf_grant = grant;
	env.alarm_fn = e2e_alarm;
	armed = 20;
	out[0] = '\0';
	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
		return -999;
	(void)fflush(stdout);
	w = fork();
	if (w == 0) {
		size_t i = 0;
		unsigned s = 0;

		(void)signal(SIGPIPE, SIG_IGN);
		(void)close(sv[0]);
		if (wr_all(sv[1], (const uint8_t *)head, strlen(head)) != 0)
			_exit(0);
		while (i < n) {
			size_t k = seg[s++ % (sizeof(seg) / sizeof(seg[0]))];

			if (k > n - i)
				k = n - i;
			if (wr_all(sv[1], img + i, k) != 0)
				_exit(0);       /* the answer came first */
			i += k;
		}
		_exit(0);
	}
	if (w < 0) {
		(void)close(sv[0]);
		(void)close(sv[1]);
		return -998;
	}
	st = srv_conn(sv[0], &env);
	(void)shutdown(sv[0], SHUT_WR);
	for (;;) {
		ssize_t r = read(sv[1], out + got, cap - 1 - got);

		if (r <= 0)
			break;
		got += (size_t)r;
		if (got + 1 >= cap)
			break;
	}
	out[got] = '\0';
	(void)close(sv[0]);
	(void)close(sv[1]);
	(void)waitpid(w, NULL, 0);
	return st;
}

/* STATUS through the real client, with the session: the BARRIER.  The child
 * serves one connection to its end -- END's reply, then the install behind
 * it, then the reboot request -- before it accepts the next, so once this
 * answers, whatever the previous upload set off has finished.  Without it the
 * first run of this file read the log while the install was still writing it.
 * Returns BKS_UPDATE_LAST's text, "" when STATUS carried none. */
static const char *barrier(void)
{
	static char last[BKS_UPDATE_LAST_MAX + 1];
	static struct bk_resp br;
	struct bk_req q;
	size_t off = 0;
	uint16_t t, l;
	const uint8_t *v;

	memset(&q, 0, sizeof(q));
	q.op = OP_STATUS;
	memcpy(q.session, tok, PROTO_TOK_LEN);
	memcpy(q.csrf, csrf, PROTO_TOK_LEN);
	q.client_ip = 0x0a010164u;
	(void)snprintf(last, sizeof(last), "(no answer)");
	if (bk_call(sock_path, &q, &br) != 0 || br.status != ST_OK)
		return last;
	last[0] = '\0';
	while (proto_tlv_get(br.body, br.body_len, &off, &t, &v, &l) == 0)
		if (t == BKS_UPDATE_LAST && l <= BKS_UPDATE_LAST_MAX) {
			memcpy(last, v, l);
			last[l] = '\0';
		}
	return last;
}

static int code_of(const char *out)
{
	if (strncmp(out, "HTTP/1.1 ", 9) != 0)
		return -1;
	return (int)strtol(out + 9, NULL, 10);
}

static const char *body_of(const char *out)
{
	const char *b = strstr(out, "\r\n\r\n");

	return b != 0 ? b + 4 : "";
}

/* simkern's log, as the brokerd child wrote it: verbs, staging writes, locks. */
static int log_writes(char *first, size_t cap)
{
	char line[256];
	FILE *f = fopen(log_file, "r");
	int n = 0;

	if (first != 0 && cap > 0)
		first[0] = '\0';
	if (f == 0)
		return -1;
	while (fgets(line, sizeof(line), f) != 0) {
		if (line[0] == 'v' || line[0] == 'i' || line[0] == 'L' ||
		    line[0] == 'U') {
			if (n == 0 && first != 0)
				(void)snprintf(first, cap, "%s", line);
			n++;
		}
	}
	(void)fclose(f);
	return n;
}

static int reboots(void)
{
	char line[64];
	FILE *f = fopen(reboot_file, "r");
	int n = 0;

	if (f == 0)
		return 0;
	while (fgets(line, sizeof(line), f) != 0)
		n++;
	(void)fclose(f);
	return n;
}

/* The accepted upload's install, line by line in simkern's log. */
static int log_is_install(const uint8_t *img, size_t n)
{
	static const char hx[] = "0123456789abcdef";
	char line[256], want[200], hex[65];
	uint8_t md[SHA256_DIGEST_LEN];
	size_t staged = 0;
	int step = 0, i;
	FILE *f = fopen(log_file, "r");

	if (f == 0)
		return 0;
	(void)sha256(img, n, md);
	for (i = 0; i < 32; i++) {
		hex[2 * i] = hx[md[i] >> 4];
		hex[2 * i + 1] = hx[md[i] & 15];
	}
	hex[64] = '\0';
	while (fgets(line, sizeof(line), f) != 0) {
		line[strcspn(line, "\n")] = '\0';
		if (line[0] == 's')
			continue;
		switch (step) {
		case 0: if (strcmp(line, "L") != 0) goto bad; step++; break;
		case 1: if (strcmp(line, "v disarm") != 0) goto bad; step++; break;
		case 2: if (strcmp(line, "v img reset") != 0) goto bad; step++; break;
		case 3: {
			size_t k = n - staged > 4096 ? 4096 : n - staged;

			(void)snprintf(want, sizeof(want), "i %lu", (unsigned long)k);
			if (strcmp(line, want) != 0) goto bad;
			staged += k;
			if (staged == n)
				step++;
			break;
		}
		case 4:
			(void)snprintf(want, sizeof(want), "v arm 0x190000 0x2b0000 0x120000");
			if (strcmp(line, want) != 0) goto bad;
			step++;
			break;
		case 5:
			(void)snprintf(want, sizeof(want), "v install slotB sha=%s", hex);
			if (strcmp(line, want) != 0) goto bad;
			step++;
			break;
		case 6: if (strcmp(line, "v img reset") != 0) goto bad; step++; break;
		case 7: if (strcmp(line, "U") != 0) goto bad; step++; break;
		default: goto bad;
		}
	}
	(void)fclose(f);
	return step == 8;
bad:
	(void)printf("    log line '%s' at step %d\n", line, step);
	(void)fclose(f);
	return 0;
}

static uint8_t flipbuf[RLXB_SLOT_SIZE + 8];

static const uint8_t *flip(const struct blob *b, size_t byte, int bit)
{
	memcpy(flipbuf, b->p, b->n);
	flipbuf[byte] = (uint8_t)(flipbuf[byte] ^ (1u << bit));
	return flipbuf;
}

static void refused(const char *name, const struct blob *a, const struct blob *b,
                    unsigned ctr, const char *boot, const uint8_t *img, size_t n,
                    int want_code, const char *why)
{
	static char out[16384];
	char want[160], clen[24], first[256];
	int st, w;

	layout(a, b, ctr, boot);
	(void)snprintf(clen, sizeof(clen), "%lu", (unsigned long)n);
	st = exchange(clen, img, n, out, sizeof(out));
	(void)snprintf(want, sizeof(want),
	               "{\"ok\":false,\"error\":\"update\",\"reason\":\"%s\"}", why);
	CHECK(st == want_code && code_of(out) == want_code &&
	      strcmp(body_of(out), want) == 0,
	      "%s: %d '%s', want %d %s", name, code_of(out), body_of(out),
	      want_code, want);
	CHECK(strcmp(barrier(), why) == 0, "%s: brokerd's STATUS says '%s'", name,
	      barrier());
	w = log_writes(first, sizeof(first));
	CHECK(w == 0, "%s: brokerd wrote %d events, first '%s'", name, w, first);
	CHECK(reboots() == 0, "%s: a reboot was asked for", name);
}

int main(int argc, char **argv)
{
	static char out[16384];
	char clen[24];
	int st;

	if (argc != 3) {
		(void)fprintf(stderr, "usage: test_e2e <fixture dir> <scratch dir>\n");
		return 2;
	}
	fixdir = argv[1];
	rundir = argv[2];
	(void)setvbuf(stdout, NULL, _IOLBF, 0);
	(void)signal(SIGPIPE, SIG_IGN);
	if (mkdir(rundir, 0700) != 0 && errno != EEXIST) {
		(void)printf("  FAIL mkdir %s\n", rundir);
		return 2;
	}
	/* /tmp, as test_wire's socket: an AF_UNIX path holds at most 107 bytes
	 * and an O= under a CI checkout can come close to that; the pid keeps
	 * two runs (gcc, clang, sanitized) from sharing it. */
	(void)snprintf(sock_path, sizeof(sock_path), "/tmp/rlxbk-e2e-%ld.sock",
	               (long)getpid());
	(void)snprintf(boot_file, sizeof(boot_file), "%s/rlxfw-boot", rundir);
	(void)snprintf(store_file, sizeof(store_file), "%s/cfg-store.bin", rundir);
	(void)snprintf(reboot_file, sizeof(reboot_file), "%s/reboots", rundir);
	(void)snprintf(log_file, sizeof(log_file), "%s/writes.log", rundir);
	(void)unlink(store_file);
	(void)unlink(reboot_file);
	load(&fx_a5, "a5");
	load(&fx_b6, "b6");
	load(&fx_b7, "b7");
	load(&fx_b6big, "b6big");
	load(&fx_b6key, "b6key");
	if (simk_init(rundir) != 0) {
		(void)printf("  FAIL simk_init\n");
		return 2;
	}
	if (start_broker() != 0) {
		(void)printf("  FAIL cannot start the brokerd child\n");
		return 2;
	}
	(void)printf("test_e2e: brokerd child %ld on %s\n", (long)bkpid, sock_path);

	/* X01: accepted.  A5 runs, the counter is 5, B6 of FW-246's length. */
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	(void)snprintf(clen, sizeof(clen), "%lu", (unsigned long)fx_b6big.n);
	st = exchange(clen, fx_b6big.p, fx_b6big.n, out, sizeof(out));
	CHECK(st == 200 && strcmp(body_of(out),
	                          "{\"ok\":true,\"slot\":\"B\",\"version\":6}") == 0,
	      "X01 the accepted upload: %d '%s'", st, body_of(out));
	CHECK(strcmp(barrier(), "ok B 6") == 0, "X01 brokerd's STATUS says '%s'",
	      barrier());
	CHECK(log_is_install(fx_b6big.p, fx_b6big.n),
	      "X01 the install sequence in simkern's log");
	CHECK(reboots() == 1, "X01 one reboot asked for, got %d", reboots());
	{
		static uint8_t chip[SIMK_CHIP];
		FILE *f = fopen(simk_flash_file(), "rb");
		int ok = f != 0 && fread(chip, 1, sizeof(chip), f) == sizeof(chip);
		size_t i;

		if (f != 0)
			(void)fclose(f);
		ok = ok && memcmp(chip + RLXB_SLOT_B_FLASH, fx_b6big.p, fx_b6big.n) == 0 &&
		     memcmp(chip + RLXB_SLOT_A_FLASH, fx_a5.p, fx_a5.n) == 0;
		for (i = fx_b6big.n; ok && i < RLXB_SLOT_SIZE; i++)
			if (chip[RLXB_SLOT_B_FLASH + i] != 0xFF)
				ok = 0;
		CHECK(ok, "X01 slot B holds the container, slot A untouched");
	}
	(void)unlink(reboot_file);

	/* one refusal per row of notes/self-update.md § 4.6 */
	refused("X02 a payload bit flipped", &fx_a5, 0, 5, "slot A ver 5\n",
	        flip(&fx_b6, 1000, 3), fx_b6.n, 400, "digest");
	refused("X03 bit 0 of header byte 28", &fx_a5, 0, 5, "slot A ver 5\n",
	        flip(&fx_b6, 28, 0), fx_b6.n, 400, "sig");
	refused("X04 signed for the running slot", &fx_a5, &fx_b6, 6,
	        "slot B ver 6\n", fx_b7.p, fx_b7.n, 400, "flash_match");
	refused("X05 a key the build does not trust", &fx_a5, 0, 5, "slot A ver 5\n",
	        fx_b6key.p, fx_b6key.n, 400, "sig");
	refused("X06 booted from RAM: the handoff is none", &fx_a5, 0, 5, "none\n",
	        fx_b6.p, fx_b6.n, 400, "handoff");
	refused("X07 below the counter", &fx_a5, &fx_b6, 6, "slot B ver 6\n",
	        fx_a5.p, fx_a5.n, 400, "rollback");
	/* a body larger than a slot: httpd's 413 at the header line, before BEGIN */
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	st = exchange("1179649", fx_b6.p, fx_b6.n, out, sizeof(out));
	CHECK(st == 413 && code_of(out) == 413, "X08 Content-Length 1,179,649: %d", st);
	/* no update op reached brokerd: its last word is still X07's */
	CHECK(strcmp(barrier(), "rollback") == 0,
	      "X08 brokerd's STATUS moved: '%s'", barrier());
	CHECK(log_writes(0, 0) == 0 && reboots() == 0, "X08 and brokerd wrote nothing");

	if (bkpid > 0) {
		(void)kill(bkpid, SIGKILL);
		(void)waitpid(bkpid, NULL, 0);
	}
	(void)unlink(sock_path);
	free(fx_a5.p); free(fx_b6.p); free(fx_b7.p); free(fx_b6big.p); free(fx_b6key.p);
	(void)printf("test_e2e: %d checks, %d failures\n", nchecks, fails);
	return fails == 0 ? 0 : 1;
}
