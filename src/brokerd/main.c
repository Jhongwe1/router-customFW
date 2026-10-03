/* src/brokerd/main.c -- the listener.
 *
 * CONCURRENCY: poll() over one listening fd and at most BK_MAXCONN = 8
 * connection slots, in ONE process and ONE thread.  No fork per connection, no
 * threads (MIPS-I has no atomic RMW), no shared memory, so no locks.
 *
 * WHY POLL AND NOT accept-one-at-a-time.  A single slow client is the whole
 * reason.  With a blocking accept/read per connection, a peer that sends 47 of
 * the 48 header bytes and then stops holds the broker shut for the length of
 * the read timeout, every time.  With poll, that peer occupies one of eight
 * slots and is reaped by its own deadline while the other seven are served.
 * The deadline, not the multiplexing, is what bounds the damage: BK_IDLE_S
 * without a byte, or BK_LIFE_S in total, and the slot is closed.
 *
 * WHAT STILL BLOCKS, stated rather than hidden: the KDF and PING run inside
 * bk_dispatch(), synchronously, so one LOGIN stalls the loop for the length of
 * one scrypt and one PING for up to its timeout.  For the KDF that is
 * deliberate -- plan § D8 ruling 3 wants exactly one evaluation in flight and
 * a single process gives it for free -- and `kdf_busy` keeps the invariant
 * true if this ever becomes fork-per-connection.  For PING it is a real
 * latency hole: up to 10 s of no service.  It is not fixed here.
 */
#define _GNU_SOURCE 1     /* struct ucred, SO_PEERCRED, sync() */

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/reboot.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#include "brokerd.h"

#define BK_MAXCONN 8
#define BK_IDLE_S  5        /* no byte for this long -> closed */
#define BK_LIFE_S  15       /* hard cap on a connection, whatever it does */
#define BK_CHUNK   512

struct conn {
	int   fd;
	uid_t uid;
	int   writing;
	int   reboot_after_write;   /* THIS slot armed it; see the note below */
	long  born;
	long  last;
	struct proto_rx rx;
	uint8_t out[PROTO_RESP_MAX];
	size_t outlen;
	size_t outoff;
};

static volatile sig_atomic_t want_stop;

static void on_term(int sig)
{
	(void)sig;
	want_stop = 1;
}

static long mono(void)
{
	struct timespec ts;

	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;
	return (long)ts.tv_sec;
}

static void set_cloexec_nonblock(int fd)
{
	int fl = fcntl(fd, F_GETFD);

	if (fl >= 0)
		(void)fcntl(fd, F_SETFD, fl | FD_CLOEXEC);
	fl = fcntl(fd, F_GETFL);
	if (fl >= 0)
		(void)fcntl(fd, F_SETFL, fl | O_NONBLOCK);
}

static void conn_close(struct conn *c)
{
	if (c->fd >= 0)
		(void)close(c->fd);
	memset(c, 0, sizeof(*c));
	c->fd = -1;
}

/* Put a response into c->out and switch the slot to writing. */
static void conn_reply(struct conn *c, const struct proto_resp *rs)
{
	int n = proto_encode_resp(rs, c->out, sizeof(c->out));

	if (n < 0) {
		struct proto_resp bare;

		memset(&bare, 0, sizeof(bare));
		bare.version = PROTO_VERSION;
		bare.status = ST_IO;
		n = proto_encode_resp(&bare, c->out, sizeof(c->out));
		if (n < 0) {                  /* cannot happen: 12 bytes */
			conn_close(c);
			return;
		}
	}
	c->outlen = (size_t)n;
	c->outoff = 0;
	c->writing = 1;
}

static void conn_reply_status(struct conn *c, uint8_t st)
{
	struct proto_resp rs;

	memset(&rs, 0, sizeof(rs));
	rs.version = PROTO_VERSION;
	rs.status = st;
	conn_reply(c, &rs);
}

static int bind_socket(const char *path, mode_t mode, gid_t gid)
{
	struct sockaddr_un sa;
	size_t plen = strlen(path);
	mode_t old;
	int fd;

	if (plen == 0 || plen >= sizeof(sa.sun_path)) {
		bk_log("brokerd: refused: socket path length %lu", (unsigned long)plen);
		return -1;
	}
	/* A stale socket from a previous run is not evidence of another broker:
	 * an AF_UNIX path is not held by the process.  Unlink it, then bind; a
	 * live broker still holding the path loses the race and its clients get
	 * ECONNREFUSED, which is why init runs exactly one. */
	if (unlink(path) != 0 && errno != ENOENT) {
		bk_log("brokerd: refused: cannot unlink stale socket (errno %d)", errno);
		return -1;
	}
#ifdef SOCK_CLOEXEC
	fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
#else
	fd = socket(AF_UNIX, SOCK_STREAM, 0);
#endif
	if (fd < 0) {
		bk_log("brokerd: refused: socket() errno %d", errno);
		return -1;
	}
	memset(&sa, 0, sizeof(sa));
	sa.sun_family = AF_UNIX;
	memcpy(sa.sun_path, path, plen);

	/* Bind under a tight umask, then widen deliberately, so there is no
	 * window in which the socket is more permissive than intended. */
	old = umask(0177);
	if (bind(fd, (const struct sockaddr *)&sa, sizeof(sa)) != 0) {
		bk_log("brokerd: refused: bind %s errno %d", path, errno);
		(void)umask(old);
		(void)close(fd);
		return -1;
	}
	(void)umask(old);
	if (gid != (gid_t)-1 && chown(path, 0, gid) != 0)
		bk_log("brokerd: warning: chown %s gid %lu errno %d",
		       path, (unsigned long)gid, errno);
	if (chmod(path, mode) != 0) {
		bk_log("brokerd: refused: chmod %s errno %d", path, errno);
		(void)close(fd);
		return -1;
	}
	if (listen(fd, BK_MAXCONN) != 0) {
		bk_log("brokerd: refused: listen errno %d", errno);
		(void)close(fd);
		return -1;
	}
	set_cloexec_nonblock(fd);
	return fd;
}

static void usage(void)
{
	(void)fprintf(stderr,
	  "brokerd [-s SOCK] [-c CFG] [-m MODE] [-g GID]\n"
	  "  -s  unix socket path   (default " BK_SOCK_PATH ")\n"
	  "  -c  config store path  (default " BK_CFG_PATH ")\n"
	  "  -m  socket mode, octal (default 0666; see notes/broker.md)\n"
	  "  -g  socket group gid   (default: leave as root)\n"
	  "There is deliberately no option for the entropy file, the random\n"
	  "source or the ping binary: each would be a runtime bypass.\n");
}

int main(int argc, char **argv)
{
	struct broker bk;
	struct conn conns[BK_MAXCONN];
	struct pollfd pfd[BK_MAXCONN + 1];
	const char *sock_path = BK_SOCK_PATH;
	const char *cfg_path = BK_CFG_PATH;
	mode_t mode = 0666;
	gid_t gid = (gid_t)-1;
	int lfd, i, opt;

	/* SIGPIPE ignored: a peer that vanishes between our read and our write
	 * must give us EPIPE, not kill the only privileged process on the box.
	 * SIGCHLD is left at SIG_DFL on purpose -- SIG_IGN would make PING's
	 * waitpid() fail with ECHILD and lose the exit status. */
	(void)signal(SIGPIPE, SIG_IGN);
	(void)signal(SIGTERM, on_term);
	(void)signal(SIGINT, on_term);

	while ((opt = getopt(argc, argv, "s:c:m:g:h")) != -1) {
		switch (opt) {
		case 's': sock_path = optarg; break;
		case 'c': cfg_path = optarg; break;
		case 'm': mode = (mode_t)strtoul(optarg, 0, 8); break;
		case 'g': gid = (gid_t)strtoul(optarg, 0, 10); break;
		case 'h': usage(); return 0;
		default:  usage(); return 2;
		}
	}

	bk_init(&bk);
	bk.cfg_path = cfg_path;
	/* Fail-closed, per SPEC § 5: defaults, source = 0, and with no
	 * admin.pwhash no login is possible until one is set.  This load only
	 * makes the start-up log say what the store held: bk_dispatch() loads it
	 * again before every request (`FW-184`). */
	(void)bk_cfg_reload(&bk);
	(void)bk_entropy_ready(&bk);
	bk_log("brokerd: entropy_avail=%lu auth_ready=%d",
	       (unsigned long)bk.entropy_last, bk.auth_ready);
	if (!bk.auth_ready)
		bk_log("brokerd: LOGIN and PWSET will answer NOENTROPY until "
		       "entropy_avail reaches %d at least once", BK_ENTROPY_MIN);

	lfd = bind_socket(sock_path, mode, gid);
	if (lfd < 0)
		return 1;
	for (i = 0; i < BK_MAXCONN; i++) {
		memset(&conns[i], 0, sizeof(conns[i]));
		conns[i].fd = -1;
	}
	bk_log("brokerd: listening on %s mode %04o", sock_path, (unsigned)mode);

	while (!want_stop) {
		int nf = 0, rc, timeout = 1000;
		long now = mono();
		int slot_of[BK_MAXCONN + 1];
		int free_slot = 0;

		for (i = 0; i < BK_MAXCONN; i++)
			if (conns[i].fd < 0)
				free_slot = 1;

		/* Only poll the listener while a slot is free; otherwise a flood
		 * spins on an accept we cannot serve. */
		if (free_slot) {
			pfd[nf].fd = lfd;
			pfd[nf].events = POLLIN;
			pfd[nf].revents = 0;
			slot_of[nf] = -1;
			nf++;
		}
		for (i = 0; i < BK_MAXCONN; i++) {
			if (conns[i].fd < 0)
				continue;
			pfd[nf].fd = conns[i].fd;
			pfd[nf].events = conns[i].writing ? POLLOUT : POLLIN;
			pfd[nf].revents = 0;
			slot_of[nf] = i;
			nf++;
		}
		if (nf == 0) {
			/* Every slot busy with nothing pollable: impossible, but
			 * do not spin. */
			timeout = 100;
		}

		rc = poll(pfd, (unsigned)nf, timeout);
		if (rc < 0) {
			if (errno == EINTR)
				continue;
			bk_log("brokerd: poll errno %d", errno);
			break;
		}
		now = mono();

		for (i = 0; i < nf; i++) {
			struct conn *c;

			if (pfd[i].revents == 0)
				continue;
			if (slot_of[i] < 0) {           /* the listener */
				int cfd;
				struct ucred cr;
				socklen_t crl = sizeof(cr);
				int j, k = -1;

				cfd = accept(lfd, 0, 0);
				if (cfd < 0)
					continue;
				for (j = 0; j < BK_MAXCONN; j++)
					if (conns[j].fd < 0) { k = j; break; }
				if (k < 0) {
					(void)close(cfd);
					continue;
				}
				memset(&cr, 0, sizeof(cr));
				if (getsockopt(cfd, SOL_SOCKET, SO_PEERCRED,
				               &cr, &crl) != 0 ||
				    (size_t)crl < sizeof(cr)) {
					/* No credentials, no service.  This is
					 * the whole identity model. */
					bk_log("brokerd: SO_PEERCRED failed, "
					       "connection dropped");
					(void)close(cfd);
					continue;
				}
				set_cloexec_nonblock(cfd);
				c = &conns[k];
				memset(c, 0, sizeof(*c));
				c->fd = cfd;
				c->uid = cr.uid;
				c->born = now;
				c->last = now;
				c->writing = 0;
				proto_rx_init(&c->rx);
				continue;
			}

			c = &conns[slot_of[i]];
			if (c->fd < 0)
				continue;

			if (!c->writing) {
				uint8_t buf[BK_CHUNK];
				ssize_t r = read(c->fd, buf, sizeof(buf));
				size_t used = 0;
				int st;

				if (r < 0) {
					if (errno == EINTR || errno == EAGAIN)
						continue;
					conn_close(c);
					continue;
				}
				if (r == 0) {
					/* EOF before a complete request: the
					 * peer that sent a header and vanished. */
					conn_close(c);
					continue;
				}
				c->last = now;
				st = proto_rx_feed(&c->rx, buf, (size_t)r, &used);
				if (st < 0) {
					conn_reply_status(c, ST_BADREQ);
					continue;
				}
				if (st != PRX_DONE)
					continue;          /* want more */
				if (used != (size_t)r) {
					/* Bytes past one request on a
					 * one-request-per-connection socket. */
					conn_reply_status(c, ST_BADREQ);
					continue;
				}
				{
					struct proto_resp rs;

					if (bk_dispatch(&bk, &c->rx.req, c->uid, &rs) != 0)
						conn_reply_status(c, ST_IO);
					else
						conn_reply(c, &rs);
					/* SPEC § 6: reply FIRST, then reboot.  With
					 * eight slots, a broker-wide flag would let
					 * another connection's completed write fire
					 * the reboot before THIS reply left the
					 * socket, so the arming is moved onto the
					 * slot that asked for it. */
					if (bk.pending_reboot) {
						c->reboot_after_write = 1;
						bk.pending_reboot = 0;
					}
					/* The request held a password or a token;
					 * do not leave it in the slot. */
					memset(&c->rx, 0, sizeof(c->rx));
					memset(&rs, 0, sizeof(rs));
				}
				continue;
			}

			{
				ssize_t w = write(c->fd, c->out + c->outoff,
				                  c->outlen - c->outoff);

				if (w < 0) {
					if (errno == EINTR || errno == EAGAIN)
						continue;
					conn_close(c);
					continue;
				}
				c->last = now;
				c->outoff += (size_t)w;
				if (c->outoff >= c->outlen) {
					int reboot_now = c->reboot_after_write;

					/* One response per connection.  Read the
					 * flag before the close: conn_close wipes
					 * the slot. */
					conn_close(c);
					if (reboot_now) {
						bk_log("brokerd: REBOOT");
						sync();
						(void)sleep(1);
						(void)reboot(RB_AUTOBOOT);
						/* If reboot() returned we are
						 * not privileged; say so and
						 * keep serving. */
						bk_log("brokerd: reboot() failed,"
						       " errno %d", errno);
					}
				}
			}
		}

		/* Deadlines.  Swept every pass, so a peer that never becomes
		 * readable is still reaped. */
		for (i = 0; i < BK_MAXCONN; i++) {
			struct conn *c = &conns[i];

			if (c->fd < 0)
				continue;
			if (now - c->last >= BK_IDLE_S || now - c->born >= BK_LIFE_S)
				conn_close(c);
		}
	}

	for (i = 0; i < BK_MAXCONN; i++)
		if (conns[i].fd >= 0)
			conn_close(&conns[i]);
	(void)close(lfd);
	(void)unlink(sock_path);
	bk_sess_drop_all(&bk);
	bk_log("brokerd: stopped");
	return 0;
}
