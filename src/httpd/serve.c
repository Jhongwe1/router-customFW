/* src/httpd/serve.c -- sockets, the privilege drop, and the fork-per-connection
 * loop with the login limiter in the parent.
 *
 * THE ORDER OF THE DROP, and why each step is verified rather than assumed:
 *   bind(:80)        needs uid 0, so it is first and it is the only thing root is
 *                    used for.
 *   chroot(root)     before any credential change, because chroot(2) needs
 *                    CAP_SYS_CHROOT which a uid-100 process does not have.
 *   chdir("/")       NOT optional.  A chroot without it leaves the working
 *                    directory outside the new root, and every relative path the
 *                    process opens still resolves from there: the chroot would be
 *                    decoration.  This is the step the brief's sequence does not
 *                    name and the code must have.
 *   setgroups(0)     also not optional, and also absent from the brief's sequence:
 *                    setgid() does not clear the supplementary group list, so a
 *                    process that was in group 0 keeps group 0 after setgid(100)
 *                    and every group-0 file stays reachable.
 *   setgid(gid)      before setuid, because after setuid the process can no longer
 *                    change its groups.
 *   setuid(uid)      last.
 * Then two refusals must hold: setuid(0) and setgid(0) must both fail with EPERM.
 * A guard is shown permitting as well as refusing, so srv_drop() also proves the
 * chroot is pointing at the web root (a file that only exists there must stat) and
 * that a path outside it does not resolve.
 *
 * THE LIMITER IS IN THE PARENT.  rl.h owns the argument; the mechanism is here: a
 * socketpair per child, one byte out ('L'), five bytes back (verdict plus a
 * big-endian retry-after).  No shared memory, so no atomic read-modify-write is
 * needed -- which matters because this core has none (D7).
 *
 * WHAT THIS FILE DOES NOT ESTABLISH.  It has never run on the device.  Every
 * number in the comments is either a limit this code enforces or a figure marked
 * 推 in notes/httpd.md.
 */

/* _GNU_SOURCE before the first include: uClibc 0.9.30 hides setgroups() behind
 * __USE_BSD and O_NONBLOCK's friends behind __USE_GNU. */
#define _GNU_SOURCE 1

#include "serve.h"

#include "http.h"
#include "rl.h"
#include "routes.h"

#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <netinet/in.h>
#include <signal.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* ------------------------------------------------------------------ plumbing */

static void set_cloexec(int fd)
{
	int fl = fcntl(fd, F_GETFD, 0);

	if (fl >= 0)
		(void)fcntl(fd, F_SETFD, fl | FD_CLOEXEC);
}

static uint32_t now_ms(void)
{
	struct timespec ts;

	if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0)
		return (uint32_t)((uint32_t)ts.tv_sec * 1000u +
				  (uint32_t)(ts.tv_nsec / 1000000L));
	/* A box without a monotonic clock would make every bucket refill from a
	 * wall clock an attacker cannot move; time(NULL) is the fallback and the
	 * millisecond resolution is lost, which only makes the limiter stricter. */
	return (uint32_t)time(NULL) * 1000u;
}

static ssize_t rd(int fd, void *p, size_t n)
{
	ssize_t r;

	do {
		r = read(fd, p, n);
	} while (r < 0 && errno == EINTR);
	return r;
}

static int wr_all(int fd, const void *p, size_t n)
{
	const unsigned char *b = (const unsigned char *)p;
	size_t off = 0;

	while (off < n) {
		ssize_t w = write(fd, b + off, n - off);

		if (w < 0) {
			if (errno == EINTR)
				continue;
			return -1;
		}
		if (w == 0)
			return -1;
		off += (size_t)w;
	}
	return 0;
}

/* ------------------------------------------------------------ listen and drop */

int srv_listen(uint16_t port, int backlog)
{
	struct sockaddr_in sa;
	int fd, one = 1;

	fd = socket(AF_INET, SOCK_STREAM, 0);
	if (fd < 0)
		return -1;
	set_cloexec(fd);
	(void)setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

	memset(&sa, 0, sizeof(sa));
	sa.sin_family = AF_INET;
	sa.sin_port = htons(port);
	sa.sin_addr.s_addr = htonl(INADDR_ANY);

	if (bind(fd, (struct sockaddr *)&sa, sizeof(sa)) != 0) {
		(void)close(fd);
		return -1;
	}
	if (listen(fd, backlog) != 0) {
		(void)close(fd);
		return -1;
	}
	return fd;
}

static void fatal(const char *step)
{
	/* Loud, one line, no request bytes, and it does not return. */
	(void)fprintf(stderr, "httpd: REFUSING TO SERVE: %s failed (errno %d)\n",
		      step, errno);
	(void)fflush(stderr);
	_exit(1);
}

int srv_drop(const char *root, uint32_t uid, uint32_t gid, const char *proof)
{
	struct stat st;
	int ngr;

	if (uid == 0 || gid == 0) {
		(void)fprintf(stderr, "httpd: REFUSING TO SERVE: uid/gid 0 asked for\n");
		_exit(1);
	}
	if (geteuid() != 0) {
		(void)fprintf(stderr,
			      "httpd: REFUSING TO SERVE: not root, cannot chroot\n");
		_exit(1);
	}

	if (chroot(root) != 0)
		fatal("chroot");
	if (chdir("/") != 0)
		fatal("chdir(\"/\") after chroot");

	/* The guard shown permitting: a file that exists only inside the web root
	 * must stat now.  Without this, a chroot to the wrong directory is
	 * indistinguishable from a chroot to the right one. */
	if (proof != NULL && stat(proof, &st) != 0)
		fatal("the chroot does not contain the web root's own file");
	/* and shown refusing: a path that exists on the real root must not. */
	if (stat("/etc/passwd", &st) == 0)
		fatal("/etc/passwd is still visible: the chroot did not take");

	if (setgroups(0, NULL) != 0)
		fatal("setgroups(0)");
	ngr = getgroups(0, NULL);
	if (ngr != 0) {
		errno = 0;
		fatal("the supplementary group list is not empty");
	}
	if (setgid((gid_t)gid) != 0)
		fatal("setgid");
	if (getgid() != (gid_t)gid || getegid() != (gid_t)gid)
		fatal("setgid did not take");
	if (setuid((uid_t)uid) != 0)
		fatal("setuid");
	if (getuid() != (uid_t)uid || geteuid() != (uid_t)uid)
		fatal("setuid did not take");

	/* The two refusals.  If either of these succeeds the process is still
	 * root in a way the checks above did not see, and serving would be worse
	 * than not serving. */
	if (setuid(0) == 0)
		fatal("setuid(0) SUCCEEDED after the drop");
	if (setgid(0) == 0)
		fatal("setgid(0) SUCCEEDED after the drop");

	return 0;
}

/* ------------------------------------------------------- one connection, child */

static volatile sig_atomic_t got_chld;

static void on_chld(int s)
{
	(void)s;
	got_chld = 1;
}

struct kdfchan {
	int fd;
};

static int kdf_grant(void *ctx, uint32_t *retry_s)
{
	struct kdfchan *c = (struct kdfchan *)ctx;
	unsigned char ask = SRV_ASK;
	unsigned char ans[5];
	ssize_t r;

	*retry_s = 1;
	if (c == NULL || c->fd < 0)
		return 0;                       /* no channel: refuse, fail closed */
	if (wr_all(c->fd, &ask, 1) != 0)
		return 0;
	r = rd(c->fd, ans, sizeof(ans));
	if (r != 5)
		return 0;
	*retry_s = ((uint32_t)ans[1] << 24) | ((uint32_t)ans[2] << 16) |
		   ((uint32_t)ans[3] << 8) | (uint32_t)ans[4];
	return ans[0] == SRV_YES;
}

static void kdf_release(void *ctx)
{
	struct kdfchan *c = (struct kdfchan *)ctx;
	unsigned char rel = SRV_REL;

	if (c != NULL && c->fd >= 0)
		(void)wr_all(c->fd, &rel, 1);
}

static void set_rcv_timeout(int fd, int secs)
{
	struct timeval tv;

	tv.tv_sec = secs;
	tv.tv_usec = 0;
	(void)setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
	(void)setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
}

static int send_rsp(int fd, struct http_rsp *rs)
{
	char hdr[1024];
	int hl;

	hl = route_headers(rs, hdr, sizeof(hdr));
	if (hl < 0) {
		struct http_rsp e;

		route_rsp_init(&e);
		route_err(&e, 500, "hdr");
		hl = route_headers(&e, hdr, sizeof(hdr));
		if (hl < 0)
			return -1;
		(void)wr_all(fd, hdr, (size_t)hl);
		(void)wr_all(fd, e.body, e.blen);
		return 500;
	}
	if (wr_all(fd, hdr, (size_t)hl) != 0)
		return -1;

	if (rs->fd >= 0) {
		unsigned char buf[2048];
		uint32_t left = rs->fsize;

		while (left > 0) {
			size_t want = (left < sizeof(buf)) ? left : sizeof(buf);
			ssize_t r = rd(rs->fd, buf, want);

			if (r <= 0)
				break;
			if (wr_all(fd, buf, (size_t)r) != 0)
				break;
			left -= (uint32_t)r;
		}
		(void)close(rs->fd);
		rs->fd = -1;
	} else if (rs->blen > 0) {
		(void)wr_all(fd, rs->body, rs->blen);
	}
	return rs->status;
}

int srv_conn(int fd, const struct route_env *env)
{
	struct http_parser ps;
	struct http_req rq;
	struct http_rsp rs;
	unsigned char buf[2048];
	int done = 0;
	int status;

	http_parse_init(&ps, &rq);
	set_rcv_timeout(fd, HTTP_HDR_TIMEOUT_S);

	for (;;) {
		ssize_t r = rd(fd, buf, sizeof(buf));
		size_t used = 0;
		int rc;

		if (r == 0) {
			if (ps.state == HS_REQLINE && ps.linelen == 0)
				return -1;      /* nothing at all: no answer owed */
			route_rsp_init(&rs);
			route_err(&rs, 400, "short");
			return send_rsp(fd, &rs);
		}
		if (r < 0) {
			if (errno == EAGAIN || errno == EWOULDBLOCK) {
				route_rsp_init(&rs);
				route_err(&rs, 408, "timeout");
				return send_rsp(fd, &rs);
			}
			return -1;
		}

		rc = http_feed(&ps, buf, (size_t)r, &used);
		if (rc < 0) {
			route_rsp_init(&rs);
			route_err(&rs, -rc, "request");
			if (-rc == 405)
				rs.allow_get_post = 1;
			return send_rsp(fd, &rs);
		}
		if (rc == 1) {
			done = 1;
			break;
		}
		/* The body gets its own, longer timeout the moment the headers
		 * are behind us.  Both are per-recv; the child's alarm() is the
		 * bound on the whole connection. */
		if (ps.state == HS_BODY)
			set_rcv_timeout(fd, HTTP_BODY_TIMEOUT_S);
	}

	if (!done)
		return -1;

	(void)route_dispatch(&rq, &rs, env);
	status = send_rsp(fd, &rs);
	/* The password and the body it arrived in leave this process' stack and
	 * heap-free buffers zeroed, so a later core dump or a reused page cannot
	 * carry them.  It is cheap and it is not a substitute for anything. */
	memset(&rq, 0, sizeof(rq));
	memset(&rs, 0, sizeof(rs));
	return status;
}

/* --------------------------------------------------------------- accept loop */

struct kid {
	pid_t pid;
	int fd;
	uint32_t ip;
	uint8_t holds;
};

static struct kid kids[HTTP_CONN_MAX];

/* ------------------------------------------------- the one KDF grant, and why
 * it is not a local of srv_loop() any more.
 *
 * 量 on the device on 2026-09-30 (image r78a): POST /api/login answered
 * `429 {"ok":false,"error":"ratelimit","retry_s":2}` in 0.030 s and never
 * stopped -- 20 s of idle later, and a further 90 s later -- while
 * GET /api/status kept answering 200 from the same httpd.  The buckets in rl.c
 * were not doing it: test_rl.c's sweep shows a 90 s gap refilling a login bucket
 * to its burst from every state it can be in, and the smallest retry_s an empty
 * login bucket can name is 5, not 2.  A constant 2 has exactly one source,
 * SRV_KDF_BUSY_S, and reaching it needs a holder.
 *
 * The holder was `int kdf_inflight` in srv_loop(), kept beside kids[i].holds.
 * reap() clears kids[i].holds when a child exits -- but reap() cannot reach a
 * local of its caller, so a child that exited while holding the grant, and was
 * reaped before the parent read its release byte or its EOF, left kdf_inflight
 * pointing at a slot with no process in it.  Nothing ever cleared it again and
 * every login for the life of the process was refused.  Two copies of one piece
 * of state, and only one of them maintained on every path.
 *
 * There is now one copy: kids[i].holds, in the table reap() already clears.  The
 * three functions below are the only readers and writers, and serve.h declares
 * them so test_serve.c drives these and not a model of them.
 */
static struct rl_bucket kdf_g;
static struct rl_table  kdf_ip;

void srv_kdf_reset(void)
{
	unsigned i;

	rl_init(&kdf_g, RL_KDF_BURST, RL_KDF_RATE_MILLI);
	rl_table_init(&kdf_ip, RL_KDF_IP_BURST, RL_KDF_IP_RATE);
	for (i = 0; i < HTTP_CONN_MAX; i++)
		kids[i].holds = 0;
}

/* The slot holding the grant, or -1.  Eight bytes, scanned once per ask: the
 * cost of not keeping a second copy of the answer. */
static int kdf_holder(void)
{
	unsigned i;

	for (i = 0; i < HTTP_CONN_MAX; i++) {
		if (kids[i].holds != 0)
			return (int)i;
	}
	return -1;
}

void srv_kdf_gone(unsigned slot)
{
	if (slot < HTTP_CONN_MAX)
		kids[slot].holds = 0;
}

int srv_kdf_ask(unsigned slot, uint32_t ip, uint32_t t_ms,
		 uint32_t *retry_s)
{
	*retry_s = 1;
	if (slot >= HTTP_CONN_MAX)
		return 0;
	if (kdf_holder() >= 0) {
		/* plan D8 ruling 3: one evaluation at a time, and the cap is the
		 * whole memory budget.  A second asker is told when, not queued. */
		*retry_s = SRV_KDF_BUSY_S;
		return 0;
	}
	if (!rl_table_take(&kdf_ip, ip, t_ms)) {
		*retry_s = rl_table_retry_s(&kdf_ip, ip);
		return 0;
	}
	if (!rl_take(&kdf_g, t_ms)) {
		/* The per-address token this call just took bought nothing, so it
		 * goes back.  Without the refund one refused attempt is charged to
		 * two buckets, and the per-address bucket -- one token per ten
		 * seconds, the slowest here -- drains faster than the rate rl.h
		 * declares.  Same family as the defect above: a refusal changing
		 * state it did not pay for. */
		rl_table_refund(&kdf_ip, ip);
		*retry_s = rl_retry_s(&kdf_g);
		return 0;
	}
	kids[slot].holds = 1;
	*retry_s = 0;
	return 1;
}

static void reap(void)
{
	for (;;) {
		int st;
		pid_t p = waitpid(-1, &st, WNOHANG);
		unsigned i;

		if (p <= 0)
			break;
		for (i = 0; i < HTTP_CONN_MAX; i++) {
			if (kids[i].pid == p) {
				if (kids[i].fd >= 0)
					(void)close(kids[i].fd);
				kids[i].pid = 0;
				kids[i].fd = -1;
				srv_kdf_gone(i);
				kids[i].ip = 0;
			}
		}
	}
}

/* The parent's "at the cap" answer.  It goes through route_err() and
 * route_headers() like every other response rather than being a hand-written
 * blob, because the hand-written blob it replaced declared `Content-Length: 29`
 * for a 28-byte body -- found by counting the bytes, not by a test: curl reads
 * the status line and the connection closes, so a short body looks like a pass.
 * Now the length comes from the same code that computes every other one, and
 * test_serve.c's "the body is exactly Content-Length bytes" case covers it. */
static void send_503(int fd)
{
	struct http_rsp rs;
	char hdr[512];
	int fl = fcntl(fd, F_GETFL, 0);
	int hl;
	ssize_t w;

	route_rsp_init(&rs);
	rs.retry_after = 1;
	rs.nostore = 1;
	route_err(&rs, 503, "busy");
	hl = route_headers(&rs, hdr, sizeof(hdr));
	if (hl < 0)
		return;

	/* Non-blocking: the parent must never wait on a peer.  One attempt each,
	 * then the connection closes whether they landed or not -- a 503 that did
	 * not fit in the socket buffer is a 503 the peer reads as a reset, which is
	 * a correct answer to "the server is at its connection cap". */
	if (fl >= 0)
		(void)fcntl(fd, F_SETFL, fl | O_NONBLOCK);
	w = write(fd, hdr, (size_t)hl);
	(void)w;
	w = write(fd, rs.body, rs.blen);
	(void)w;
}

int srv_loop(int lfd, const char *sock_path)
{
	struct rl_bucket conn_g;
	struct rl_table conn_ip;
	struct sigaction sa;
	unsigned i;

	for (i = 0; i < HTTP_CONN_MAX; i++) {
		kids[i].pid = 0;
		kids[i].fd = -1;
		kids[i].ip = 0;
		kids[i].holds = 0;
	}

	rl_init(&conn_g, RL_CONN_BURST, RL_CONN_RATE_MILLI);
	rl_table_init(&conn_ip, RL_CONN_IP_BURST, RL_CONN_IP_RATE);
	srv_kdf_reset();

	memset(&sa, 0, sizeof(sa));
	sa.sa_handler = SIG_IGN;
	(void)sigaction(SIGPIPE, &sa, NULL);
	memset(&sa, 0, sizeof(sa));
	sa.sa_handler = on_chld;
	sa.sa_flags = 0;                /* no SA_RESTART: select() must return */
	(void)sigaction(SIGCHLD, &sa, NULL);

	for (;;) {
		fd_set rfds;
		int maxfd = lfd;
		int n;
		unsigned live = 0;

		if (got_chld) {
			got_chld = 0;
			reap();
		}

		FD_ZERO(&rfds);
		for (i = 0; i < HTTP_CONN_MAX; i++) {
			if (kids[i].fd >= 0) {
				FD_SET(kids[i].fd, &rfds);
				if (kids[i].fd > maxfd)
					maxfd = kids[i].fd;
			}
			if (kids[i].pid != 0)
				live++;
		}
		/* Stop accepting at the cap rather than queueing: the answer to
		 * "more than eight at once" is 503, and it is the parent that
		 * gives it so no ninth child is ever forked. */
		if (live < HTTP_CONN_MAX)
			FD_SET(lfd, &rfds);

		n = select(maxfd + 1, &rfds, NULL, NULL, NULL);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			return -1;
		}

		for (i = 0; i < HTTP_CONN_MAX; i++) {
			unsigned char c;
			ssize_t r;

			if (kids[i].fd < 0 || !FD_ISSET(kids[i].fd, &rfds))
				continue;
			r = rd(kids[i].fd, &c, 1);
			if (r <= 0) {
				srv_kdf_gone(i);
				(void)close(kids[i].fd);
				kids[i].fd = -1;
				continue;
			}
			if (c == SRV_REL) {
				srv_kdf_gone(i);
				continue;
			}
			if (c != SRV_ASK)
				continue;
			{
				unsigned char ans[5];
				uint32_t retry = 1;
				int yes = srv_kdf_ask(i, kids[i].ip, now_ms(),
						      &retry);

				ans[0] = (unsigned char)(yes ? SRV_YES : SRV_NO);
				ans[1] = (unsigned char)((retry >> 24) & 0xffu);
				ans[2] = (unsigned char)((retry >> 16) & 0xffu);
				ans[3] = (unsigned char)((retry >> 8) & 0xffu);
				ans[4] = (unsigned char)(retry & 0xffu);
				(void)wr_all(kids[i].fd, ans, sizeof(ans));
			}
		}

		if (!FD_ISSET(lfd, &rfds))
			continue;

		{
			struct sockaddr_in pa;
			socklen_t pl = sizeof(pa);
			int cfd;
			uint32_t ip = 0;
			uint32_t t;
			unsigned slot = HTTP_CONN_MAX;
			unsigned same_ip = 0;
			int sp[2];
			pid_t pid;

			memset(&pa, 0, sizeof(pa));
			cfd = accept(lfd, (struct sockaddr *)&pa, &pl);
			if (cfd < 0)
				continue;
			set_cloexec(cfd);
			if (pl >= (socklen_t)sizeof(pa))
				ip = ntohl(pa.sin_addr.s_addr);
			t = now_ms();

			for (i = 0; i < HTTP_CONN_MAX; i++) {
				if (kids[i].pid == 0 && slot == HTTP_CONN_MAX)
					slot = i;
				if (kids[i].pid != 0 && kids[i].ip == ip)
					same_ip++;
			}
			/* One address may not hold every slot: a peer that opens
			 * connections and sends nothing costs at most SRV_PER_IP
			 * of them, and the rest stay available. */
			if (slot == HTTP_CONN_MAX || same_ip >= SRV_PER_IP ||
			    !rl_table_take(&conn_ip, ip, t) ||
			    !rl_take(&conn_g, t)) {
				send_503(cfd);
				(void)close(cfd);
				continue;
			}
			if (socketpair(AF_UNIX, SOCK_STREAM, 0, sp) != 0) {
				send_503(cfd);
				(void)close(cfd);
				continue;
			}
			set_cloexec(sp[0]);
			set_cloexec(sp[1]);

			pid = fork();
			if (pid < 0) {
				(void)close(sp[0]);
				(void)close(sp[1]);
				send_503(cfd);
				(void)close(cfd);
				continue;
			}
			if (pid == 0) {
				struct route_env env;
				struct kdfchan ch;
				unsigned k;

				/* The child keeps exactly two fds: the peer and
				 * its own end of the channel.  Every other
				 * child's channel is inherited by fork and would
				 * otherwise let one connection answer another
				 * one's grant. */
				(void)close(lfd);
				(void)close(sp[0]);
				for (k = 0; k < HTTP_CONN_MAX; k++) {
					if (kids[k].fd >= 0)
						(void)close(kids[k].fd);
				}
				/* SO_RCVTIMEO is per-recv, so a peer that sends
				 * one byte every four seconds would never time
				 * out.  This is the bound on the whole
				 * connection, and SIGALRM's default action ends
				 * the process. */
				(void)alarm(HTTP_HDR_TIMEOUT_S +
					    HTTP_BODY_TIMEOUT_S + 5);
				memset(&sa, 0, sizeof(sa));
				sa.sa_handler = SIG_DFL;
				(void)sigaction(SIGCHLD, &sa, NULL);

				ch.fd = sp[1];
				memset(&env, 0, sizeof(env));
				env.sock = sock_path;
				env.client_ip = ip;
				env.kdf_grant = kdf_grant;
				env.kdf_release = kdf_release;
				env.ctx = &ch;

				(void)srv_conn(cfd, &env);
				(void)shutdown(cfd, SHUT_WR);
				(void)close(cfd);
				(void)close(sp[1]);
				_exit(0);
			}

			(void)close(sp[1]);
			(void)close(cfd);
			kids[slot].pid = pid;
			kids[slot].fd = sp[0];
			kids[slot].ip = ip;
			srv_kdf_gone(slot);
		}
	}
}
