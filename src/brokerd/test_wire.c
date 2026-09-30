/* src/brokerd/test_wire.c -- the real daemon over a real socket.
 *
 * argv[1] is the built brokerd.  This file forks it, waits for the socket, and
 * then drives it with bk_call() and with raw sockets for the abuse cases the
 * unit tests cannot reach: a header then silence, a body_len larger than what
 * is delivered, a request split across writes, garbage, bytes past one request,
 * and eight slow clients at once.
 *
 * The test runs as an ordinary uid, so SO_PEERCRED reports neither 0, 100 nor
 * 101 and every op is answered PERM.  That is itself the assertion: an unknown
 * peer gets nothing, and it is checked on the wire rather than in a unit.
 * Decoder refusals (BADREQ) happen before the uid is consulted, so those cases
 * are unaffected by which uid runs the test.
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
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "brokerd.h"
#include "client.h"

static int fails;
static pid_t child = -1;
static const char *sock = "/tmp/rlxbk_wire.sock";

#define CHECK(cond, ...) do { \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

static void msleep(int ms)
{
	struct timespec ts;

	ts.tv_sec = ms / 1000;
	ts.tv_nsec = (long)(ms % 1000) * 1000000L;
	(void)nanosleep(&ts, 0);
}

static int start_broker(const char *bin)
{
	int i;

	(void)unlink(sock);
	child = fork();
	if (child < 0)
		return -1;
	if (child == 0) {
		char *av[8];
		char *ev[1];

		av[0] = (char *)"brokerd";
		av[1] = (char *)"-s";
		av[2] = (char *)sock;
		av[3] = (char *)"-c";
		av[4] = (char *)"/tmp/rlxbk_wire_cfg.bin";
		av[5] = (char *)"-m";
		av[6] = (char *)"0600";
		av[7] = 0;
		ev[0] = 0;
		(void)execve(bin, av, ev);
		_exit(127);
	}
	for (i = 0; i < 200; i++) {
		struct stat st;

		if (stat(sock, &st) == 0)
			return 0;
		msleep(25);
	}
	return -1;
}

static void stop_broker(void)
{
	int st = 0;

	if (child <= 0)
		return;
	(void)kill(child, SIGTERM);
	for (;;) {
		pid_t w = waitpid(child, &st, 0);

		if (w == child || (w < 0 && errno != EINTR))
			break;
	}
	child = -1;
	(void)unlink(sock);
}

static int raw_connect(void)
{
	struct sockaddr_un sa;
	int fd = socket(AF_UNIX, SOCK_STREAM, 0);

	if (fd < 0)
		return -1;
	memset(&sa, 0, sizeof(sa));
	sa.sun_family = AF_UNIX;
	(void)strncpy(sa.sun_path, sock, sizeof(sa.sun_path) - 1);
	if (connect(fd, (const struct sockaddr *)&sa, sizeof(sa)) != 0) {
		(void)close(fd);
		return -1;
	}
	return fd;
}

/* Read whatever comes, up to cap, until EOF or `secs` elapse. */
static int raw_drain(int fd, uint8_t *buf, size_t cap, int secs)
{
	size_t got = 0;
	time_t end = time(0) + secs;

	while (got < cap) {
		struct pollfd p;
		ssize_t r;
		int rc;

		if (time(0) > end)
			break;
		p.fd = fd; p.events = POLLIN; p.revents = 0;
		rc = poll(&p, 1, 250);
		if (rc < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (rc == 0)
			continue;
		r = read(fd, buf + got, cap - got);
		if (r < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (r == 0)
			break;
		got += (size_t)r;
	}
	return (int)got;
}

static void mk_wire(uint8_t *w, uint8_t op, uint32_t blen, const uint8_t *body)
{
	memset(w, 0, PROTO_REQ_HDR);
	proto_put_be32(w + PROTO_RQ_O_MAGIC, PROTO_REQ_MAGIC);
	w[PROTO_RQ_O_VERSION] = 1;
	w[PROTO_RQ_O_OP] = op;
	proto_put_be32(w + PROTO_RQ_O_BODYLEN, blen);
	if (blen != 0 && body != 0)
		memcpy(w + PROTO_REQ_HDR, body, blen);
}

static void test_happy_path(void)
{
	struct bk_req rq;
	struct bk_resp rs;
	int rc;

	memset(&rq, 0, sizeof(rq));
	rq.op = OP_STATUS;
	rc = bk_call(sock, &rq, &rs);
	CHECK(rc == 0, "bk_call STATUS rc=%d (%s)", rc, strerror(rc < 0 ? -rc : 0));
	if (rc == 0)
		CHECK(rs.status == ST_PERM,
		      "an unknown uid gets PERM, got %u", (unsigned)rs.status);

	/* Every op, over the wire, answered without the daemon dying. */
	{
		static const uint8_t ops[] = { OP_GET, OP_SET, OP_REBOOT, OP_STATUS,
		                               OP_PING, OP_LOGIN, OP_LOGOUT,
		                               OP_PWSET, 0x20, 0x7F };
		size_t i;

		for (i = 0; i < sizeof(ops) / sizeof(ops[0]); i++) {
			memset(&rq, 0, sizeof(rq));
			rq.op = ops[i];
			rc = bk_call(sock, &rq, &rs);
			CHECK(rc == 0, "op %02x rc=%d", ops[i], rc);
			if (rc == 0)
				CHECK(rs.status == ST_PERM || rs.status == ST_NOTSUP,
				      "op %02x status %u", ops[i], (unsigned)rs.status);
		}
	}
}

static void test_header_then_vanish(void)
{
	uint8_t w[PROTO_REQ_HDR];
	int fd;

	/* 47 of 48 header bytes, then close.  Must not hang the broker. */
	mk_wire(w, OP_STATUS, 0, 0);
	fd = raw_connect();
	CHECK(fd >= 0, "connect");
	if (fd < 0)
		return;
	CHECK(write(fd, w, PROTO_REQ_HDR - 1) == PROTO_REQ_HDR - 1, "partial write");
	(void)close(fd);

	/* ... and the broker still answers the next caller. */
	{
		struct bk_req rq;
		struct bk_resp rs;

		memset(&rq, 0, sizeof(rq));
		rq.op = OP_STATUS;
		CHECK(bk_call(sock, &rq, &rs) == 0,
		      "the broker still answers after a vanished peer");
	}
}

static void test_bodylen_bigger_than_delivered(void)
{
	uint8_t w[PROTO_REQ_HDR];
	uint8_t in[64];
	int fd, got;

	/* body_len says 2048, we send none, then just sit there.  The idle
	 * deadline must close it; we must not block forever. */
	mk_wire(w, OP_LOGIN, 2048, 0);
	fd = raw_connect();
	CHECK(fd >= 0, "connect");
	if (fd < 0)
		return;
	CHECK(write(fd, w, PROTO_REQ_HDR) == PROTO_REQ_HDR, "header write");
	got = raw_drain(fd, in, sizeof(in), 12);
	CHECK(got == 0, "no response to an undelivered body, got %d bytes", got);
	(void)close(fd);

	/* body_len over the cap is refused with BADREQ, on the wire. */
	mk_wire(w, OP_LOGIN, 2049, 0);
	fd = raw_connect();
	if (fd < 0)
		return;
	CHECK(write(fd, w, PROTO_REQ_HDR) == PROTO_REQ_HDR, "header write");
	got = raw_drain(fd, in, sizeof(in), 5);
	CHECK(got == PROTO_RESP_HDR, "a 12-byte refusal, got %d", got);
	if (got == PROTO_RESP_HDR) {
		struct proto_resp r;

		CHECK(proto_decode_resp(in, (size_t)got, &r) == PROTO_RESP_HDR,
		      "decodes");
		CHECK(r.status == ST_BADREQ, "status %u want BADREQ",
		      (unsigned)r.status);
	}
	(void)close(fd);
}

static void test_split_reads(void)
{
	uint8_t w[PROTO_REQ_HDR + 8];
	uint8_t body[8];
	uint8_t in[64];
	int fd, i, got;

	memset(body, 0x11, sizeof(body));
	mk_wire(w, OP_GET, 4, body);
	fd = raw_connect();
	CHECK(fd >= 0, "connect");
	if (fd < 0)
		return;
	/* One byte at a time, with a pause, so every read the broker does is a
	 * short read. */
	for (i = 0; i < PROTO_REQ_HDR + 4; i++) {
		CHECK(write(fd, w + i, 1) == 1, "byte %d", i);
		if ((i % 8) == 0)
			msleep(5);
	}
	got = raw_drain(fd, in, sizeof(in), 8);
	CHECK(got == PROTO_RESP_HDR, "a response to a byte-at-a-time request, "
	      "got %d", got);
	(void)close(fd);
}

static void test_garbage_and_trailing(void)
{
	uint8_t junk[256];
	uint8_t w[PROTO_REQ_HDR + 4];
	uint8_t in[64];
	size_t i;
	int fd, got;

	for (i = 0; i < sizeof(junk); i++)
		junk[i] = (uint8_t)(i * 7 + 3);
	fd = raw_connect();
	CHECK(fd >= 0, "connect");
	if (fd < 0)
		return;
	CHECK(write(fd, junk, sizeof(junk)) == (ssize_t)sizeof(junk), "junk write");
	got = raw_drain(fd, in, sizeof(in), 5);
	CHECK(got == PROTO_RESP_HDR, "garbage gets a 12-byte refusal, got %d", got);
	if (got == PROTO_RESP_HDR) {
		struct proto_resp r;

		(void)proto_decode_resp(in, (size_t)got, &r);
		CHECK(r.status == ST_BADREQ, "garbage status %u", (unsigned)r.status);
	}
	(void)close(fd);

	/* One valid request plus one extra byte: one request per connection. */
	mk_wire(w, OP_STATUS, 0, 0);
	w[PROTO_REQ_HDR] = 0x41;
	fd = raw_connect();
	if (fd < 0)
		return;
	CHECK(write(fd, w, PROTO_REQ_HDR + 1) == PROTO_REQ_HDR + 1, "write+1");
	got = raw_drain(fd, in, sizeof(in), 5);
	CHECK(got == PROTO_RESP_HDR, "trailing byte answered, got %d", got);
	if (got == PROTO_RESP_HDR) {
		struct proto_resp r;

		(void)proto_decode_resp(in, (size_t)got, &r);
		CHECK(r.status == ST_BADREQ, "trailing byte status %u want BADREQ",
		      (unsigned)r.status);
	}
	(void)close(fd);
}

/* A slow client must not hold the broker shut.  Fill every slot with peers that
 * send nothing, then prove a normal call still gets served. */
static void test_slow_clients_do_not_block(void)
{
	int fd[16];
	int i, n = 0;
	struct bk_req rq;
	struct bk_resp rs;
	int rc;

	for (i = 0; i < 16; i++) {
		fd[i] = raw_connect();
		if (fd[i] >= 0)
			n++;
	}
	(void)printf("  %d idle peers connected (slots = 8)\n", n);
	/* With all eight slots held by silent peers, this call can only be
	 * served once a deadline frees one.  bk_call's own timeout is 15 s and
	 * the broker's idle deadline is 5 s, so it must come back OK. */
	memset(&rq, 0, sizeof(rq));
	rq.op = OP_STATUS;
	rc = bk_call(sock, &rq, &rs);
	CHECK(rc == 0, "served despite %d idle peers, rc=%d", n, rc);
	for (i = 0; i < 16; i++)
		if (fd[i] >= 0)
			(void)close(fd[i]);
}

/* bk_call at the size limits, against a throwaway echo server.
 *
 * brokerd here runs as an ordinary uid, so every op is PERM and no response
 * carries a body.  That leaves client.c's large-transfer path untested: a
 * 2,048-byte request and a 4,096-byte response, both bigger than a socket
 * buffer's first read, so the loops in bk_call have to iterate.  This server
 * exists only to make them. */
static void test_client_limits(void)
{
	const char *esock = "/tmp/rlxbk_echo.sock";
	struct sockaddr_un sa;
	struct bk_req rq;
	struct bk_resp rs;
	uint8_t body[PROTO_REQ_BODY_MAX];
	pid_t p;
	int lfd, rc, i;

	for (i = 0; i < (int)sizeof(body); i++)
		body[i] = (uint8_t)(i * 31 + 7);

	(void)unlink(esock);
	lfd = socket(AF_UNIX, SOCK_STREAM, 0);
	CHECK(lfd >= 0, "echo socket");
	if (lfd < 0)
		return;
	memset(&sa, 0, sizeof(sa));
	sa.sun_family = AF_UNIX;
	(void)strncpy(sa.sun_path, esock, sizeof(sa.sun_path) - 1);
	CHECK(bind(lfd, (const struct sockaddr *)&sa, sizeof(sa)) == 0, "echo bind");
	CHECK(listen(lfd, 4) == 0, "echo listen");

	p = fork();
	if (p < 0) {
		(void)close(lfd);
		return;
	}
	if (p == 0) {
		uint8_t in[PROTO_REQ_MAX];
		uint8_t out[PROTO_RESP_MAX];
		struct proto_resp r;
		size_t got = 0;
		int cfd = accept(lfd, 0, 0);
		int n;

		if (cfd < 0)
			_exit(1);
		/* Read the whole request, however it is split. */
		while (got < sizeof(in)) {
			ssize_t k = read(cfd, in + got, sizeof(in) - got);

			if (k < 0) {
				if (errno == EINTR)
					continue;
				break;
			}
			if (k == 0)
				break;
			got += (size_t)k;
		}
		memset(&r, 0, sizeof(r));
		r.version = PROTO_VERSION;
		r.status = ST_OK;
		r.body_len = PROTO_RESP_BODY_MAX;
		/* Echo the request body into the first part of the response so the
		 * parent can prove the bytes survived both directions. */
		if (got >= PROTO_REQ_HDR)
			memcpy(r.body, in + PROTO_REQ_HDR,
			       got - PROTO_REQ_HDR > PROTO_RESP_BODY_MAX
			       ? PROTO_RESP_BODY_MAX : got - PROTO_REQ_HDR);
		n = proto_encode_resp(&r, out, sizeof(out));
		if (n > 0) {
			int off = 0;

			/* Deliberately dribble it out, so bk_call's read loop
			 * must go round more than once. */
			while (off < n) {
				int chunk = n - off > 700 ? 700 : n - off;
				ssize_t w = write(cfd, out + off, (size_t)chunk);

				if (w <= 0)
					break;
				off += (int)w;
				msleep(3);
			}
		}
		(void)close(cfd);
		(void)close(lfd);
		_exit(0);
	}
	(void)close(lfd);

	memset(&rq, 0, sizeof(rq));
	rq.op = OP_LOGIN;
	rq.body = body;
	rq.body_len = PROTO_REQ_BODY_MAX;
	rc = bk_call(esock, &rq, &rs);
	CHECK(rc == 0, "bk_call at the size limits rc=%d", rc);
	if (rc == 0) {
		CHECK(rs.status == ST_OK, "echo status %u", (unsigned)rs.status);
		CHECK(rs.body_len == PROTO_RESP_BODY_MAX,
		      "a 4096-byte response arrived whole, got %lu",
		      (unsigned long)rs.body_len);
		CHECK(memcmp(rs.body, body, PROTO_REQ_BODY_MAX) == 0,
		      "the 2048-byte request body survived both directions");
	}
	{
		int st = 0;

		while (waitpid(p, &st, 0) < 0 && errno == EINTR)
			;
	}
	(void)unlink(esock);

	/* An over-long body is refused before a socket is opened. */
	rq.body_len = PROTO_REQ_BODY_MAX + 1;
	CHECK(bk_call(esock, &rq, &rs) == -EMSGSIZE, "bk_call refuses 2049 bytes");
	rq.body_len = 4;
	rq.body = 0;
	CHECK(bk_call(esock, &rq, &rs) == -EINVAL, "bk_call refuses a null body");
}

static void test_socket_mode(void)
{
	struct stat st;

	CHECK(stat(sock, &st) == 0, "stat the socket");
	CHECK((st.st_mode & 07777) == 0600, "mode %04o, want 0600 (-m was passed)",
	      (unsigned)(st.st_mode & 07777));
	CHECK(S_ISSOCK(st.st_mode), "it is a socket");
}

int main(int argc, char **argv)
{
	(void)printf("test_wire\n");
	if (argc < 2) {
		(void)printf("  FAIL no brokerd binary given\n");
		return 1;
	}
	(void)signal(SIGPIPE, SIG_IGN);
	if (start_broker(argv[1]) != 0) {
		(void)printf("  FAIL brokerd did not come up on %s\n", sock);
		stop_broker();
		return 1;
	}
	test_socket_mode();
	test_happy_path();
	test_header_then_vanish();
	test_split_reads();
	test_garbage_and_trailing();
	test_bodylen_bigger_than_delivered();
	test_slow_clients_do_not_block();
	test_client_limits();
	stop_broker();
	(void)printf("test_wire: %d failures\n", fails);
	return fails == 0 ? 0 : 1;
}
