/* src/lib/client.c -- bk_call(): one request, one response, one connection.
 *
 * EINTR is retried everywhere.  SIGPIPE is not ignored here (that is the
 * caller's process-wide decision; httpd and dnsfwd both do it at startup) but
 * every write is guarded by poll() for POLLOUT and a deadline, so a broker
 * that stopped reading times out rather than blocking forever.
 */
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#include "client.h"

#define BK_CONNECT_S_DEFAULT 5
#define BK_IO_S_DEFAULT      15

static int bk_connect_s = BK_CONNECT_S_DEFAULT;
static int bk_io_s = BK_IO_S_DEFAULT;

void bk_set_timeouts(int connect_s, int io_s)
{
	if (connect_s > 0)
		bk_connect_s = connect_s;
	if (io_s > 0)
		bk_io_s = io_s;
}

/* Monotonic milliseconds.  CLOCK_MONOTONIC exists on 2.6.30. */
static long long now_ms(void)
{
	struct timespec ts;

	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;
	return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

static int wait_fd(int fd, short events, long long deadline)
{
	struct pollfd pfd;
	long long left;
	int rc;

	for (;;) {
		left = deadline - now_ms();
		if (left <= 0)
			return -ETIMEDOUT;
		pfd.fd = fd;
		pfd.events = events;
		pfd.revents = 0;
		if (left > 1000)
			left = 1000;
		rc = poll(&pfd, 1, (int)left);
		if (rc < 0) {
			if (errno == EINTR)
				continue;
			return -errno;
		}
		if (rc == 0)
			continue;
		return 0;
	}
}

static int write_all(int fd, const uint8_t *p, size_t n, long long deadline)
{
	size_t off = 0;

	while (off < n) {
		ssize_t w;
		int rc = wait_fd(fd, POLLOUT, deadline);

		if (rc != 0)
			return rc;
		w = write(fd, p + off, n - off);
		if (w < 0) {
			if (errno == EINTR || errno == EAGAIN)
				continue;
			return -errno;
		}
		if (w == 0)
			return -EPIPE;
		off += (size_t)w;
	}
	return 0;
}

int bk_call(const char *sock_path, const struct bk_req *rq, struct bk_resp *rs)
{
	uint8_t wire[PROTO_REQ_MAX];
	uint8_t in[PROTO_RESP_MAX];
	struct proto_req pr;
	struct proto_resp pres;
	struct sockaddr_un sa;
	size_t plen, got = 0, want = PROTO_RESP_HDR;
	int fd, rc, n;
	long long deadline;

	if (sock_path == 0 || rq == 0 || rs == 0)
		return -EINVAL;
	if (rq->body_len > PROTO_REQ_BODY_MAX)
		return -EMSGSIZE;
	if (rq->body_len != 0 && rq->body == 0)
		return -EINVAL;
	plen = strlen(sock_path);
	if (plen == 0 || plen >= sizeof(sa.sun_path))
		return -ENAMETOOLONG;

	memset(&pr, 0, sizeof(pr));
	pr.version = PROTO_VERSION;
	pr.op = rq->op;
	pr.flags = 0;
	memcpy(pr.session, rq->session, PROTO_TOK_LEN);
	memcpy(pr.csrf, rq->csrf, PROTO_TOK_LEN);
	pr.client_ip = rq->client_ip;
	pr.body_len = rq->body_len;
	if (rq->body_len != 0)
		memcpy(pr.body, rq->body, (size_t)rq->body_len);

	n = proto_encode_req(&pr, wire, sizeof(wire));
	if (n < 0)
		return -EINVAL;

	/* SOCK_CLOEXEC is 2.6.27+, so it is available here; the fallback keeps
	 * the file building against older headers. */
#ifdef SOCK_CLOEXEC
	fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
#else
	fd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (fd >= 0)
		(void)fcntl(fd, F_SETFD, FD_CLOEXEC);
#endif
	if (fd < 0)
		return -errno;

	memset(&sa, 0, sizeof(sa));
	sa.sun_family = AF_UNIX;
	memcpy(sa.sun_path, sock_path, plen);

	deadline = now_ms() + (long long)bk_connect_s * 1000;
	for (;;) {
		if (connect(fd, (const struct sockaddr *)&sa, sizeof(sa)) == 0)
			break;
		if (errno == EINTR)
			continue;
		rc = -errno;
		(void)close(fd);
		return rc;
	}

	deadline = now_ms() + (long long)bk_io_s * 1000;
	rc = write_all(fd, wire, (size_t)n, deadline);
	if (rc != 0) {
		(void)close(fd);
		return rc;
	}
	/* Tell the broker no more request bytes are coming; it reads one
	 * request per connection and this makes a truncated request visible to
	 * it as EOF instead of as a stall. */
	(void)shutdown(fd, SHUT_WR);

	while (got < want) {
		ssize_t r;

		rc = wait_fd(fd, POLLIN, deadline);
		if (rc != 0) {
			(void)close(fd);
			return rc;
		}
		r = read(fd, in + got, want - got);
		if (r < 0) {
			if (errno == EINTR || errno == EAGAIN)
				continue;
			rc = -errno;
			(void)close(fd);
			return rc;
		}
		if (r == 0) {
			(void)close(fd);
			return -EPROTO;         /* short response */
		}
		got += (size_t)r;
		if (got == PROTO_RESP_HDR && want == PROTO_RESP_HDR) {
			uint32_t blen = proto_be32(in + PROTO_RS_O_BODYLEN);

			if (blen > PROTO_RESP_BODY_MAX) {
				(void)close(fd);
				return -EPROTO;
			}
			want = (size_t)PROTO_RESP_HDR + (size_t)blen;
		}
	}
	(void)close(fd);

	if (proto_decode_resp(in, got, &pres) < 0)
		return -EPROTO;
	rs->status = pres.status;
	rs->body_len = pres.body_len;
	memset(rs->body, 0, sizeof(rs->body));
	if (pres.body_len != 0)
		memcpy(rs->body, pres.body, (size_t)pres.body_len);
	return 0;
}
