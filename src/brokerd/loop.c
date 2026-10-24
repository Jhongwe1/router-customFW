/* src/brokerd/loop.c -- the listener's loop, out of main.c so that a test can
 * drive it: one poll() pass at a time, a socket adopted with the uid its peer
 * credentials named.  main() is argv, the socket and this, in a loop.
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
 * latency hole: up to 10 s of no service.  It is not fixed here.  UPDATE_END
 * (two slot reads and three verifications) and the install after it block the
 * same way; the install ends in a reboot.
 *
 * THE INSTALL RUNS AFTER THE REPLY, ON THE SLOT THAT CARRIED IT
 * (notes/self-update.md § 4.5).  END's OK sets bk->pending_update; the pass
 * that dispatched it moves the flag onto that connection, exactly as REBOOT's
 * flag is moved, and the install runs only when the LAST byte of that reply
 * has been written.  Every other way the slot can end -- a write that fails
 * (the client gave up and closed), the deadline sweep, shutdown -- goes
 * through conn_drop(), which tells update.c the reply was not delivered, and
 * nothing is staged.  What "written" can mean here is the limit of it: the
 * bytes are in the peer's socket buffer, not read; a client that closes after
 * the write returned gets an install it never reported.
 */
#define _GNU_SOURCE 1     /* struct ucred, SO_PEERCRED, sync() */

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
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

static void conn_close(struct bk_conn *c)
{
	if (c->fd >= 0)
		(void)close(c->fd);
	memset(c, 0, sizeof(*c));
	c->fd = -1;
}

/* Every end of a slot that is NOT its reply's last byte leaving: the install a
 * slot carried does not run (update.c logs it and frees the staging). */
static void conn_drop(struct broker *bk, struct bk_conn *c)
{
	if (c->install_after_write) {
		c->install_after_write = 0;
		(void)bk_upd_after_reply(bk, 0);
	}
	conn_close(c);
}

/* Put a response into c->out and switch the slot to writing.  0 when rs itself
 * is what will be written; 1 when it could not be encoded and a bare ST_IO
 * stands in for it; -1 when not even that could be formed (the slot is closed). */
static int conn_reply(struct bk_conn *c, const struct proto_resp *rs)
{
	int n = proto_encode_resp(rs, c->out, sizeof(c->out));
	int ret = 0;

	if (n < 0) {
		struct proto_resp bare;

		memset(&bare, 0, sizeof(bare));
		bare.version = PROTO_VERSION;
		bare.status = ST_IO;
		n = proto_encode_resp(&bare, c->out, sizeof(c->out));
		if (n < 0) {                  /* cannot happen: 12 bytes */
			conn_close(c);
			return -1;
		}
		ret = 1;
	}
	c->outlen = (size_t)n;
	c->outoff = 0;
	c->writing = 1;
	return ret;
}

static void conn_reply_status(struct bk_conn *c, uint8_t st)
{
	struct proto_resp rs;

	memset(&rs, 0, sizeof(rs));
	rs.version = PROTO_VERSION;
	rs.status = st;
	(void)conn_reply(c, &rs);
}

int bk_bind_socket(const char *path, mode_t mode, gid_t gid)
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

void bk_loop_init(struct bk_loop *L)
{
	int i;

	for (i = 0; i < BK_MAXCONN; i++) {
		memset(&L->c[i], 0, sizeof(L->c[i]));
		L->c[i].fd = -1;
	}
}

int bk_loop_adopt(struct bk_loop *L, int fd, uid_t uid)
{
	struct bk_conn *c = 0;
	long now = mono();
	int j;

	for (j = 0; j < BK_MAXCONN; j++)
		if (L->c[j].fd < 0) { c = &L->c[j]; break; }
	if (c == 0) {
		(void)close(fd);
		return -1;
	}
	set_cloexec_nonblock(fd);
	memset(c, 0, sizeof(*c));
	c->fd = fd;
	c->uid = uid;
	c->born = now;
	c->last = now;
	c->writing = 0;
	proto_rx_init(&c->rx);
	return 0;
}

static void conn_read(struct broker *bk, struct bk_conn *c, long now)
{
	uint8_t buf[BK_CHUNK];
	ssize_t r = read(c->fd, buf, sizeof(buf));
	size_t used = 0;
	int st;

	if (r < 0) {
		if (errno == EINTR || errno == EAGAIN)
			return;
		conn_drop(bk, c);
		return;
	}
	if (r == 0) {
		/* EOF before a complete request: the peer that sent a header
		 * and vanished. */
		conn_drop(bk, c);
		return;
	}
	c->last = now;
	st = proto_rx_feed(&c->rx, buf, (size_t)r, &used);
	if (st < 0) {
		conn_reply_status(c, ST_BADREQ);
		return;
	}
	if (st != PRX_DONE)
		return;          /* want more */
	if (used != (size_t)r) {
		/* Bytes past one request on a one-request-per-connection
		 * socket. */
		conn_reply_status(c, ST_BADREQ);
		return;
	}
	{
		struct proto_resp rs;
		int as_is = -1;

		if (bk_dispatch(bk, &c->rx.req, c->uid, &rs) != 0)
			conn_reply_status(c, ST_IO);
		else
			as_is = conn_reply(c, &rs);
		/* SPEC § 6: reply FIRST, then reboot.  With eight slots, a
		 * broker-wide flag would let another connection's completed
		 * write fire the reboot before THIS reply left the socket, so
		 * the arming is moved onto the slot that asked for it. */
		if (bk->pending_reboot) {
			c->reboot_after_write = 1;
			bk->pending_reboot = 0;
		}
		/* The same for END's install, and one more condition: the
		 * bytes about to be written must BE that OK.  A reply that
		 * could not be encoded goes out as a bare ST_IO, and an
		 * install behind an answer that says IO would be an install
		 * nobody was told about. */
		if (bk->pending_update) {
			bk->pending_update = 0;
			if (as_is == 0 && rs.status == ST_OK && c->fd >= 0)
				c->install_after_write = 1;
			else
				(void)bk_upd_after_reply(bk, 0);
		}
		/* The request held a password or a token; do not leave it in
		 * the slot. */
		memset(&c->rx, 0, sizeof(c->rx));
		memset(&rs, 0, sizeof(rs));
	}
}

static void conn_write(struct broker *bk, struct bk_conn *c, long now)
{
	ssize_t w = write(c->fd, c->out + c->outoff, c->outlen - c->outoff);

	if (w < 0) {
		if (errno == EINTR || errno == EAGAIN)
			return;
		/* EPIPE above all: the client closed before the reply could
		 * reach it.  For END's OK that is "not delivered". */
		conn_drop(bk, c);
		return;
	}
	c->last = now;
	c->outoff += (size_t)w;
	if (c->outoff >= c->outlen) {
		int reboot_now = c->reboot_after_write;
		int install_now = c->install_after_write;

		/* One response per connection.  Read the flags before the
		 * close: conn_close wipes the slot. */
		c->install_after_write = 0;
		conn_close(c);
		if (install_now)
			(void)bk_upd_after_reply(bk, 1);
		if (reboot_now) {
			bk_log("brokerd: REBOOT");
			sync();
			(void)sleep(1);
			(void)reboot(RB_AUTOBOOT);
			/* If reboot() returned we are not privileged; say so
			 * and keep serving. */
			bk_log("brokerd: reboot() failed, errno %d", errno);
		}
	}
}

int bk_loop_step(struct broker *bk, struct bk_loop *L, int lfd, int timeout_ms)
{
	struct pollfd pfd[BK_MAXCONN + 1];
	int slot_of[BK_MAXCONN + 1];
	int nf = 0, rc, i, free_slot = 0;
	long now;

	for (i = 0; i < BK_MAXCONN; i++)
		if (L->c[i].fd < 0)
			free_slot = 1;

	/* Only poll the listener while a slot is free; otherwise a flood spins
	 * on an accept we cannot serve. */
	if (lfd >= 0 && free_slot) {
		pfd[nf].fd = lfd;
		pfd[nf].events = POLLIN;
		pfd[nf].revents = 0;
		slot_of[nf] = -1;
		nf++;
	}
	for (i = 0; i < BK_MAXCONN; i++) {
		if (L->c[i].fd < 0)
			continue;
		pfd[nf].fd = L->c[i].fd;
		pfd[nf].events = L->c[i].writing ? POLLOUT : POLLIN;
		pfd[nf].revents = 0;
		slot_of[nf] = i;
		nf++;
	}
	if (nf == 0 && timeout_ms > 100) {
		/* Every slot busy with nothing pollable: impossible, but do not
		 * spin. */
		timeout_ms = 100;
	}

	rc = poll(pfd, (unsigned)nf, timeout_ms);
	if (rc < 0) {
		if (errno == EINTR)
			return 0;
		bk_log("brokerd: poll errno %d", errno);
		return -1;
	}
	now = mono();

	for (i = 0; i < nf; i++) {
		struct bk_conn *c;

		if (pfd[i].revents == 0)
			continue;
		if (slot_of[i] < 0) {           /* the listener */
			struct ucred cr;
			socklen_t crl = sizeof(cr);
			int cfd;

			cfd = accept(lfd, 0, 0);
			if (cfd < 0)
				continue;
			memset(&cr, 0, sizeof(cr));
			if (getsockopt(cfd, SOL_SOCKET, SO_PEERCRED, &cr, &crl) != 0 ||
			    (size_t)crl < sizeof(cr)) {
				/* No credentials, no service.  This is the
				 * whole identity model. */
				bk_log("brokerd: SO_PEERCRED failed, "
				       "connection dropped");
				(void)close(cfd);
				continue;
			}
			(void)bk_loop_adopt(L, cfd, cr.uid);
			continue;
		}

		c = &L->c[slot_of[i]];
		if (c->fd < 0)
			continue;
		if (!c->writing)
			conn_read(bk, c, now);
		else
			conn_write(bk, c, now);
	}

	/* Deadlines.  Swept every pass, so a peer that never becomes readable
	 * is still reaped.  The staging's own two deadlines beside them. */
	for (i = 0; i < BK_MAXCONN; i++) {
		struct bk_conn *c = &L->c[i];

		if (c->fd < 0)
			continue;
		if (now - c->last >= BK_IDLE_S || now - c->born >= BK_LIFE_S)
			conn_drop(bk, c);
	}
	bk_upd_sweep(bk);
	return 0;
}

void bk_loop_close_all(struct broker *bk, struct bk_loop *L)
{
	int i;

	for (i = 0; i < BK_MAXCONN; i++)
		if (L->c[i].fd >= 0)
			conn_drop(bk, &L->c[i]);
}
