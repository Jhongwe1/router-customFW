/* src/httpd/test_serve.c -- srv_conn() over a socketpair: the whole read-parse-
 * answer path, without a listening socket, a fork or a root process.
 *
 * WHY THERE IS NO --no-chroot FLAG TO TEST WITH.  A binary that can be told to
 * skip its privilege drop is a binary that will one day be started that way, so
 * main() has no such switch.  The connection handler is a separate function
 * instead, and this file calls it directly.  What that means is that srv_drop()
 * itself is NOT covered by a host test -- it needs to be root to run at all -- and
 * the report says so rather than implying otherwise.
 *
 * The cases here are the ones the parser tests cannot reach: a peer that sends
 * nothing, a peer that closes mid-request, a request that arrives in two writes,
 * and the exact bytes of the response head.
 *
 * And the streaming upload, POST /api/firmware (upload.h), end to end through
 * srv_conn(): the head and the first body bytes in one write, the rest from a
 * forked writer in uneven segments, the three update ops answered by the
 * stand-in in test_upd.h.  Its own controls -- that it refuses each defect it is
 * there to catch -- are the S-cases, run before anything relies on it.
 */

#include "http.h"
#include "rl.h"
#include "routes.h"
#include "serve.h"
#include "testlib.h"
#include "upload.h"

#include "client.h"
#include "test_upd.h"
#include "../rlxboot/rlxboot.h"

#include <signal.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* HTTP_UPLOAD_MAX is one slot, restated in http.h (which says why).  This is
 * what keeps the two equal: a tree where they differ does not compile here, and
 * so `make test` fails before a case runs. */
typedef char http_upload_max_is_rlxb_slot_size
	[(HTTP_UPLOAD_MAX == RLXB_SLOT_SIZE) ? 1 : -1];

/* The broker is not reachable from a test.  The cases before the upload's are
 * static content or a deliberate 503; the three update ops are answered by the
 * stand-in, which speaks their wire format. */
int bk_call(const char *sock_path, const struct bk_req *rq, struct bk_resp *rs)
{
	(void)sock_path;
	if (rq->op == OP_UPDATE_BEGIN || rq->op == OP_UPDATE_DATA ||
	    rq->op == OP_UPDATE_END)
		return upd_call(rq, rs);
	return -111;
}

static int grant(void *ctx, uint32_t *retry_s)
{
	(void)ctx;
	*retry_s = 0;
	return 1;
}

/* Run one exchange.  `parts` is a NULL-terminated list of writes, so a request
 * can be delivered in pieces.  Returns the number of bytes read back. */
static size_t exchange(const char **parts, char *out, size_t cap, int *status)
{
	int sv[2];
	struct route_env env;
	size_t got = 0;
	unsigned i;

	memset(&env, 0, sizeof(env));
	env.sock = "/nonexistent/broker.sock";
	env.client_ip = 0x0a010164u;
	env.kdf_grant = grant;
	env.alarm_fn = upd_alarm;

	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
		return 0;
	for (i = 0; parts != NULL && parts[i] != NULL; i++) {
		size_t l = strlen(parts[i]);

		if (write(sv[1], parts[i], l) != (ssize_t)l)
			break;
	}
	(void)shutdown(sv[1], SHUT_WR);

	*status = srv_conn(sv[0], &env);
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
	return got;
}

/* ------------------------------------------ the streaming upload's harness */

#define U_SESS "0123456789abcdef0123456789abcdef"
#define U_CSRF "fedcba9876543210fedcba9876543210"
#define U_OTHR "00000000000000000000000000000001"
#define U_IP   0x0a010164u

static int u_wr(int fd, const uint8_t *p, size_t n)
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

/* A request head for the upload route, blank line included.  `clen` is text so a
 * case can name a value past every bound; NULL leaves the header out. */
static void u_head(char *h, size_t cap, const char *path, const char *sess,
		   const char *hdr, const char *ck, const char *clen)
{
	size_t n = 0;

	n += (size_t)snprintf(h + n, cap - n, "POST %s HTTP/1.1\r\n"
			      "Host: 10.1.1.1\r\n", path);
	if (sess != NULL || ck != NULL) {
		n += (size_t)snprintf(h + n, cap - n, "Cookie:");
		if (sess != NULL)
			n += (size_t)snprintf(h + n, cap - n, " rlxs=%s;", sess);
		if (ck != NULL)
			n += (size_t)snprintf(h + n, cap - n, " rlxc=%s;", ck);
		n += (size_t)snprintf(h + n, cap - n, "\r\n");
	}
	if (hdr != NULL)
		n += (size_t)snprintf(h + n, cap - n, "X-RLX-CSRF: %s\r\n", hdr);
	n += (size_t)snprintf(h + n, cap - n,
			      "Content-Type: application/octet-stream\r\n");
	if (clen != NULL)
		n += (size_t)snprintf(h + n, cap - n, "Content-Length: %s\r\n",
				      clen);
	(void)snprintf(h + n, cap - n, "\r\n");
}

/* One upload over a socketpair, through srv_conn().  The head and the first
 * `first` body bytes go in ONE write before srv_conn() starts, so they are in
 * its first read and the bytes past the blank line reach upload_run() as `pre`;
 * a forked writer sends the rest of the `nbody` bytes of upd_byte(i) in segments
 * of uneven sizes, as a peer's arrive.  `eof`: the writer half-closes after its
 * bytes, a peer that gave up.  Without it the connection stays open, as a client
 * waiting for its answer keeps it, so a reader wanting more than the body would
 * wait -- and the case would see a 408, not a pass.  Returns srv_conn()'s
 * status, with the answer's bytes in `out`. */
static int u_exchange(const char *head, uint32_t nbody, uint32_t first, int eof,
		      char *out, size_t cap)
{
	static uint8_t w[8192];
	static const size_t seg[] = { 1, 7, 2043, 2045, 4096, 65536 };
	struct route_env env;
	size_t hl = strlen(head);
	size_t got = 0;
	pid_t pid = -1;
	int sv[2];
	int st;
	uint32_t k;

	memset(&env, 0, sizeof(env));
	env.sock = "/nonexistent/broker.sock";
	env.client_ip = U_IP;
	env.kdf_grant = grant;
	env.alarm_fn = upd_alarm;
	out[0] = '\0';
	if (first > nbody)
		first = nbody;
	if (hl + first > sizeof(w))
		return -998;
	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
		return -999;
	memcpy(w, head, hl);
	for (k = 0; k < first; k++)
		w[hl + k] = upd_byte(k);
	if (u_wr(sv[1], w, hl + first) != 0) {
		(void)close(sv[0]);
		(void)close(sv[1]);
		return -997;
	}
	if (first < nbody || eof) {
		(void)fflush(stdout);
		pid = fork();
		if (pid == 0) {
			static uint8_t b[65536];
			uint32_t i = first;
			unsigned s = 0;

			(void)signal(SIGPIPE, SIG_IGN);
			(void)close(sv[0]);
			while (i < nbody) {
				size_t n = seg[s++ % (sizeof(seg) / sizeof(seg[0]))];
				size_t j;

				if (n > nbody - i)
					n = nbody - i;
				for (j = 0; j < n; j++)
					b[j] = upd_byte(i + (uint32_t)j);
				if (u_wr(sv[1], b, n) != 0)
					_exit(0);   /* the answer came first */
				i += (uint32_t)n;
			}
			if (eof)
				(void)shutdown(sv[1], SHUT_WR);
			_exit(0);
		}
		if (pid < 0) {
			(void)close(sv[0]);
			(void)close(sv[1]);
			return -996;
		}
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
	/* A writer still blocked on a full socket gets EPIPE here and exits. */
	(void)close(sv[0]);
	(void)close(sv[1]);
	if (pid > 0)
		(void)waitpid(pid, NULL, 0);
	return st;
}

/* The answer's body, exactly, and its status line's code. */
static int u_body_is(const char *out, const char *want)
{
	const char *b = strstr(out, "\r\n\r\n");

	return b != NULL && strcmp(b + 4, want) == 0;
}

static int u_code(const char *out)
{
	if (strncmp(out, "HTTP/1.1 ", 9) != 0)
		return -1;
	return (int)strtol(out + 9, NULL, 10);
}

/* The stand-in, called directly: its own refusals, each with a permitting twin. */
static int s_call(uint8_t op, const uint8_t *body, uint32_t blen,
		  struct bk_resp *rs)
{
	struct bk_req q;

	memset(&q, 0, sizeof(q));
	q.op = op;
	q.client_ip = U_IP;
	q.body = body;
	q.body_len = blen;
	memset(rs, 0, sizeof(*rs));
	return upd_call(&q, rs);
}

static int s_reason(const struct bk_resp *rs, const char *why)
{
	size_t off = 0;
	uint16_t t, l;
	const uint8_t *v;

	while (proto_tlv_get(rs->body, rs->body_len, &off, &t, &v, &l) == 0) {
		if (t == UPD_T_REASON)
			return l == strlen(why) && memcmp(v, why, l) == 0;
	}
	return 0;
}

static uint32_t s_u32(const struct bk_resp *rs, uint16_t type)
{
	size_t off = 0;
	uint16_t t, l;
	const uint8_t *v;

	while (proto_tlv_get(rs->body, rs->body_len, &off, &t, &v, &l) == 0) {
		if (t == type && l == 4)
			return proto_be32(v);
		if (t == type && l == 1)
			return v[0];
	}
	return 0xffffffffu;
}

static void standin_cases(void)
{
	static uint8_t big[PROTO_REQ_BODY_MAX + 1];
	struct bk_resp rs;
	uint8_t b[16];

	memset(b, 0, sizeof(b));

	/* S01, refusing: a DATA at the wrong offset, and the staging stays
	 * poisoned for a right one after it and for END. */
	upd_reset();
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	t_okf(rs.status == ST_OK && s_u32(&rs, UPD_T_DEST) == 'B',
	      "S01 control: the stand-in's BEGIN answers OK with UPD_T_DEST",
	      rs.status, ST_OK);
	proto_put_be32(b, 1);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "sequence"),
	     "S01 it refuses a DATA at the wrong offset, INVAL sequence", NULL);
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 10, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "sequence"),
	     "S01 and stays poisoned for a right one after it", NULL);
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_END, b, 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "sequence"),
	     "S01 and for END", NULL);

	/* S02, permitting: the same staging, done right. */
	upd_reset();
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 10, &rs);
	t_ok(rs.status == ST_OK && s_u32(&rs, UPD_T_RECEIVED) == 10,
	     "S02 control: a right DATA is OK with UPD_T_RECEIVED 10", NULL);
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_END, b, 4, &rs);
	t_ok(rs.status == ST_OK && s_u32(&rs, UPD_T_DEST) == 'B' &&
	     s_u32(&rs, UPD_T_VERSION) == 7,
	     "S02 control: and END is OK with UPD_T_DEST and UPD_T_VERSION", NULL);

	/* S03: a piece past the declared total. */
	upd_reset();
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 11, &rs);
	t_ok(rs.status == ST_INVAL && upd.past_total == 1,
	     "S03 it refuses a piece past BEGIN's total", NULL);

	/* S04: END over an incomplete staging, and END with another total. */
	upd_reset();
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 4, &rs);
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_END, b, 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "incomplete"),
	     "S04 it refuses END before every byte arrived, incomplete", NULL);
	upd_reset();
	proto_put_be32(b, 4);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 4, &rs);
	proto_put_be32(b, 5);
	(void)s_call(OP_UPDATE_END, b, 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "incomplete"),
	     "S04 and END naming another total", NULL);

	/* S05: a DATA with no BEGIN before it. */
	upd_reset();
	proto_put_be32(b, 0);
	(void)s_call(OP_UPDATE_DATA, b, 4 + 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "sequence"),
	     "S05 it refuses a DATA before BEGIN", NULL);

	/* S06: a body bk_call() itself would not send. */
	upd_reset();
	t_okf(s_call(OP_UPDATE_DATA, big, PROTO_REQ_BODY_MAX + 1, &rs) ==
	      -EMSGSIZE, "S06 a 2,049-byte body is -EMSGSIZE, as bk_call()",
	      0, -EMSGSIZE);
	t_okf(s_call(OP_UPDATE_BEGIN, b, 3, &rs) == 0 && rs.status == ST_INVAL,
	      "S06 and a BEGIN of three bytes is refused", rs.status, ST_INVAL);

	/* S07: the tokens and the address, refusing and permitting. */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	proto_put_be32(b, 10);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	t_okf(rs.status == ST_AUTH, "S07 it refuses a call without the session",
	      rs.status, ST_AUTH);
	{
		struct bk_req q;

		memset(&q, 0, sizeof(q));
		q.op = OP_UPDATE_BEGIN;
		q.client_ip = U_IP;
		q.body = b;
		q.body_len = 4;
		memcpy(q.session, upd.sess, 16);
		(void)upd_call(&q, &rs);
		t_okf(rs.status == ST_PERM,
		      "S07 and one with the session and a wrong CSRF token",
		      rs.status, ST_PERM);
		memcpy(q.csrf, upd.csrf, 16);
		upd.refused = 0;
		(void)upd_call(&q, &rs);
		t_okf(rs.status == ST_OK, "S07 control: and permits both right",
		      rs.status, ST_OK);
	}

	/* S08: a total over a slot, as brokerd's too_big. */
	upd_reset();
	proto_put_be32(b, HTTP_UPLOAD_MAX + 1u);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	t_ok(rs.status == ST_INVAL && s_reason(&rs, "too_big"),
	     "S08 it refuses a total over one slot, too_big", NULL);
	upd_reset();
	proto_put_be32(b, HTTP_UPLOAD_MAX);
	(void)s_call(OP_UPDATE_BEGIN, b, 4, &rs);
	t_okf(rs.status == ST_OK, "S08 control: and permits exactly one slot",
	      rs.status, ST_OK);
}

/* One accepted upload of n bytes, and everything the stand-in saw of it. */
static void u_accept(uint32_t n, uint32_t first, const char *name)
{
	static char want[UPD_LOG_MAX + 1];
	char head[1024], out[4096], nm[160], cl[16];
	uint32_t k = (n + UPD_DATA_MAX - 1) / UPD_DATA_MAX;
	int st;

	(void)snprintf(cl, sizeof(cl), "%lu", (unsigned long)n);
	u_head(head, sizeof(head), HTTP_UPLOAD_PATH, U_SESS, U_CSRF, U_CSRF, cl);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_exchange(head, n, first, 0, out, sizeof(out));
	upd_want_log(want, sizeof(want), n);

	(void)snprintf(nm, sizeof(nm), "U %s: 200 on the wire", name);
	t_okf(st == 200 && u_code(out) == 200, nm, st, 200);
	(void)snprintf(nm, sizeof(nm), "U %s: the body is END's verdict", name);
	t_ok(u_body_is(out, "{\"ok\":true,\"slot\":\"B\",\"version\":7}"), nm,
	     out);
	(void)snprintf(nm, sizeof(nm), "U %s: one BEGIN, total %lu", name,
		       (unsigned long)n);
	t_okf(upd.nbegin == 1 && upd.total == n, nm, (long)upd.total, (long)n);
	(void)snprintf(nm, sizeof(nm), "U %s: ceil(n/2044) = %lu DATA", name,
		       (unsigned long)k);
	t_okf(upd.ndata == (int)k, nm, upd.ndata, (long)k);
	(void)snprintf(nm, sizeof(nm),
		       "U %s: every offset exact, no piece past the total", name);
	t_ok(upd.bad_offset == 0 && upd.past_total == 0 && upd.bad_frame == 0 &&
	     upd.oversize == 0, nm, NULL);
	(void)snprintf(nm, sizeof(nm),
		       "U %s: every piece full but the last, which is %lu", name,
		       (unsigned long)(n - UPD_DATA_MAX * (k - 1)));
	t_okf(upd.short_mid == 0 &&
	      upd.last_len == n - UPD_DATA_MAX * (k - 1), nm,
	      (long)upd.last_len, (long)(n - UPD_DATA_MAX * (k - 1)));
	(void)snprintf(nm, sizeof(nm),
		       "U %s: the bytes forwarded are the bytes sent, in order",
		       name);
	t_ok(upd.received == n && upd.hash == upd_hash_of(n), nm, NULL);
	(void)snprintf(nm, sizeof(nm), "U %s: one END, total %lu", name,
		       (unsigned long)n);
	t_okf(upd.nend == 1 && upd.end_total == n, nm, (long)upd.end_total,
	      (long)n);
	(void)snprintf(nm, sizeof(nm),
		       "U %s: the order B A D.. a A T E, exactly", name);
	t_ok(strcmp(upd.log, want) == 0, nm, upd.log);
	(void)snprintf(nm, sizeof(nm),
		       "U %s: END's timeouts 5 and 60, set once", name);
	t_ok(upd.ntimeouts == 1 && upd.to_connect == UPLOAD_END_CONNECT_S &&
	     upd.to_io == UPLOAD_END_IO_S, nm, NULL);
	(void)snprintf(nm, sizeof(nm),
		       "U %s: the first alarm armed is HTTP_UPLOAD_ALARM_S", name);
	t_okf(upd.alarm_first == HTTP_UPLOAD_ALARM_S, nm, (long)upd.alarm_first,
	      HTTP_UPLOAD_ALARM_S);
	(void)snprintf(nm, sizeof(nm), "U %s: no refusal, no call after one",
		       name);
	t_ok(upd.refused == 0 && upd.after_refusal == 0, nm, NULL);
}

/* An upload the stand-in is told to refuse, or one cut short.  Returns the
 * status srv_conn() sent; the answer is in `out`. */
static int u_run(const char *clen, uint32_t nbody, uint32_t first, int eof,
		 char *out, size_t cap)
{
	char head[1024];

	u_head(head, sizeof(head), HTTP_UPLOAD_PATH, U_SESS, U_CSRF, U_CSRF,
	       clen);
	return u_exchange(head, nbody, first, eof, out, cap);
}

static void upload_cases(void)
{
	char head[1024], out[4096];
	int st;

	t_okf(HTTP_UPLOAD_MAX == RLXB_SLOT_SIZE,
	      "U00 HTTP_UPLOAD_MAX is rlxboot's slot, 1,179,648",
	      (long)HTTP_UPLOAD_MAX, (long)RLXB_SLOT_SIZE);

	/* --- the gate: refused before any broker call, each with its twin ---- */
	upd_reset();
	u_head(head, sizeof(head), HTTP_UPLOAD_PATH, NULL, U_CSRF, U_CSRF, "5000");
	st = u_exchange(head, 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 401, "U01 no session is 401 on the wire", st, 401);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"nosession\"}"),
	     "U01 with route_dispatch's own body", out);
	t_okf(upd.calls == 0, "U01 and no broker call", upd.calls, 0);

	upd_reset();
	u_head(head, sizeof(head), HTTP_UPLOAD_PATH, U_SESS, U_OTHR, U_CSRF,
	       "5000");
	st = u_exchange(head, 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 403, "U02 a CSRF header that is not the cookie is 403", st,
	      403);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"csrf\"}"),
	     "U02 with route_dispatch's own body", out);
	t_okf(upd.calls == 0, "U02 and no broker call", upd.calls, 0);
	upd_reset();
	u_head(head, sizeof(head), HTTP_UPLOAD_PATH, U_SESS, NULL, U_CSRF, "5000");
	st = u_exchange(head, 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 403 && upd.calls == 0,
	      "U02 no CSRF header is 403, and no broker call", st, 403);

	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("0", 0, 0, 0, out, sizeof(out));
	t_okf(st == 400, "U03 Content-Length 0 is 400", st, 400);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"nobody\"}"),
	     "U03 nobody, as every API POST without a body", out);
	t_okf(upd.calls == 0, "U03 and no broker call", upd.calls, 0);

	/* --- the bound: refused whole at the header line ---------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("1179649", 2000, 2000, 0, out, sizeof(out));
	t_okf(st == 413, "U04 Content-Length 1,179,649 is 413", st, 413);
	t_okf(upd.calls == 0, "U04 and no broker call, with body bytes offered",
	      upd.calls, 0);
	upd_reset();
	(void)snprintf(head, sizeof(head), "POST %s HTTP/1.1\r\nHost: x\r\n"
		       "Content-Length: 1179649\r\n", HTTP_UPLOAD_PATH);
	st = u_exchange(head, 0, 0, 1, out, sizeof(out));
	t_okf(st == 413, "U04 refused AT the header line: no blank line was sent",
	      st, 413);
	upd_reset();
	(void)snprintf(head, sizeof(head), "POST %s HTTP/1.1\r\nHost: x\r\n"
		       "Content-Length: 1179648\r\n", HTTP_UPLOAD_PATH);
	st = u_exchange(head, 0, 0, 1, out, sizeof(out));
	t_okf(st == 400 && u_body_is(out, "{\"ok\":false,\"error\":\"short\"}"),
	      "U04 control: 1,179,648 passes that line and waits for the rest",
	      st, 400);
	t_okf(upd.calls == 0, "U04 and neither made a broker call", upd.calls, 0);
	u_accept(HTTP_UPLOAD_MAX, 1500, "1,179,648 (one slot)");

	/* --- a stream of n bytes ---------------------------------------------- */
	u_accept(1, 1, "n=1");
	u_accept(2044, 2044, "n=2,044");
	u_accept(2045, 0, "n=2,045");
	u_accept(1110176, 1500, "n=1,110,176");
	u_accept(100, 100, "n=100, all of it read with the head");

	/* Bytes past Content-Length, in the same write, are not the body. */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("10", 30, 30, 0, out, sizeof(out));
	t_okf(st == 200 && upd.ndata == 1, "U05 Content-Length 10 with 30 sent: "
	      "one DATA", upd.ndata, 1);
	t_ok(upd.received == 10 && upd.hash == upd_hash_of(10),
	     "U05 carrying the first ten bytes and nothing past them", NULL);

	/* The decoded path is the one that streams, as the table matches it. */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	u_head(head, sizeof(head), "/api/%66irmware", U_SESS, U_CSRF, U_CSRF,
	       "3000");
	st = u_exchange(head, 3000, 1500, 0, out, sizeof(out));
	t_okf(st == 200 && upd.nend == 1,
	      "U06 /api/%66irmware is the same route, streamed", st, 200);

	/* --- an early EOF: no END, and the answer ------------------------------ */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("5000", 3000, 1500, 1, out, sizeof(out));
	t_okf(st == 400, "U07 a peer that closes after 3,000 of 5,000 is 400", st,
	      400);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"short\"}"),
	     "U07 short, srv_conn()'s answer to any request cut short", out);
	t_okf(upd.nend == 0, "U07 and no END", upd.nend, 0);
	t_ok(strcmp(upd.log, "BAD") == 0 && upd.received == UPD_DATA_MAX,
	     "U07 the one full piece went, the partial one did not", upd.log);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("5000", 5000, 1500, 1, out, sizeof(out));
	t_okf(st == 200 && upd.nend == 1,
	      "U07 control: the same peer sending all 5,000 then closing gets END",
	      st, 200);

	/* --- BEGIN refused: no body byte forwarded ----------------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.begin_st = ST_INVAL;
	upd.begin_why = "handoff";
	st = u_run("5000", 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 400, "U08 BEGIN refused INVAL handoff is 400", st, 400);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"update\","
		       "\"reason\":\"handoff\"}"),
	     "U08 with the reason, in the update form", out);
	t_ok(upd.ndata == 0 && upd.nend == 0 && strcmp(upd.log, "B") == 0,
	     "U08 and not one DATA, no END, no alarm: the log is B", upd.log);
	t_okf(upd.alarm_first == 0, "U08 the child's alarm is not re-armed",
	      (long)upd.alarm_first, 0);
	t_okf(upd.ntimeouts == 0, "U08 nor the broker's timeouts touched",
	      upd.ntimeouts, 0);
	{
		static const struct {
			uint8_t st;
			const char *why;
			int code;
			const char *body;
			const char *name;
		} m[] = {
			{ ST_BUSY, "busy", 503,
			  "{\"ok\":false,\"error\":\"update\",\"reason\":\"busy\"}",
			  "U09 BEGIN BUSY is 503, as every route maps BUSY" },
			{ ST_IO, "flash", 500,
			  "{\"ok\":false,\"error\":\"update\",\"reason\":\"flash\"}",
			  "U09 BEGIN IO is 500" },
			{ ST_NOTSUP, NULL, 501,
			  "{\"ok\":false,\"error\":\"notsup\"}",
			  "U09 BEGIN NOTSUP without a reason (brokerd today) is 501" },
			{ ST_INVAL, "Digest", 400,
			  "{\"ok\":false,\"error\":\"inval\",\"key\":0}",
			  "U09 a reason outside [a-z0-9_] is not rendered" },
			{ ST_INVAL, "a23456789012345678901234567890123", 400,
			  "{\"ok\":false,\"error\":\"inval\",\"key\":0}",
			  "U09 nor one of 33 bytes" },
			{ ST_INVAL, "a2345678901234567890123456789012", 400,
			  "{\"ok\":false,\"error\":\"update\",\"reason\":"
			  "\"a2345678901234567890123456789012\"}",
			  "U09 control: one of 32 bytes is" }
		};
		unsigned i;

		for (i = 0; i < sizeof(m) / sizeof(m[0]); i++) {
			upd_reset();
			upd_expect(U_SESS, U_CSRF, U_IP);
			upd.begin_st = m[i].st;
			upd.begin_why = m[i].why;
			st = u_run("5000", 5000, 1500, 0, out, sizeof(out));
			t_ok(st == m[i].code && u_body_is(out, m[i].body) &&
			     upd.ndata == 0, m[i].name, out);
		}
	}
	/* brokerd's own gate, which carries no reason */
	upd_reset();
	upd_expect(U_OTHR, U_CSRF, U_IP);
	st = u_run("5000", 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 401 && u_body_is(out, "{\"ok\":false,\"error\":\"auth\"}") &&
	      upd.ndata == 0,
	      "U10 brokerd refusing the session at BEGIN is 401 auth, no DATA",
	      st, 401);
	upd_reset();
	upd_expect(U_SESS, U_OTHR, U_IP);
	st = u_run("5000", 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 403 && u_body_is(out, "{\"ok\":false,\"error\":\"perm\"}") &&
	      upd.ndata == 0,
	      "U10 and the CSRF token at BEGIN is 403 perm, no DATA", st, 403);
	upd_reset();
	upd.fail = 1;
	st = u_run("5000", 5000, 1500, 0, out, sizeof(out));
	t_okf(st == 503 && u_body_is(out, "{\"ok\":false,\"error\":\"broker\"}") &&
	      upd.ndata == 0,
	      "U11 a broker that cannot be reached is 503, no DATA", st, 503);

	/* --- a refusal at DATA k: no DATA after it, no END --------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.data_k = 3;
	upd.data_st = ST_INVAL;
	upd.data_why = "sequence";
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_okf(st == 400, "U12 DATA 3 of 5 refused INVAL is 400", st, 400);
	t_ok(u_body_is(out, "{\"ok\":false,\"error\":\"update\","
		       "\"reason\":\"sequence\"}"), "U12 with its reason", out);
	t_ok(strcmp(upd.log, "BADDD") == 0 && upd.after_refusal == 0,
	     "U12 no DATA after the third, no END: the log is BADDD", upd.log);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.data_k = 1;
	upd.data_st = ST_IO;
	upd.data_why = "nomem";
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 500 && strcmp(upd.log, "BAD") == 0 &&
	     u_body_is(out, "{\"ok\":false,\"error\":\"update\","
		       "\"reason\":\"nomem\"}"),
	     "U12 DATA 1 refused IO is 500, and the stream stops there", upd.log);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 200 && strcmp(upd.log, "BADDDDDaATE") == 0,
	     "U12 control: unrefused, all five and END", upd.log);

	/* --- brokerd's count disagreeing -------------------------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.recv_skew = 1;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 500 && u_body_is(out, "{\"ok\":false,\"error\":\"broker\"}") &&
	     strcmp(upd.log, "BAD") == 0,
	     "U13 a RECEIVED one past the bytes sent is 500, no END", upd.log);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.no_received = 1;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 500 && strcmp(upd.log, "BAD") == 0,
	     "U13 and a DATA OK without RECEIVED", upd.log);

	/* --- END: the verdict as JSON ----------------------------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.dest = 'A';
	upd.version = 7;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 200 && u_body_is(out, "{\"ok\":true,\"slot\":\"A\","
					 "\"version\":7}"),
	     "U14 END OK is {\"ok\":true,\"slot\":\"A\",\"version\":7}", out);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.end_st = ST_INVAL;
	upd.end_why = "digest";
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 400 && u_body_is(out, "{\"ok\":false,\"error\":\"update\","
					 "\"reason\":\"digest\"}"),
	     "U14 END refused INVAL digest is 400 with the reason", out);
	t_ok(strcmp(upd.log, "BADDDDDaATE") == 0,
	     "U14 after every piece, and nothing after END", upd.log);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.end_st = ST_INVAL;
	upd.end_why = "rollback";
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 400 && u_body_is(out, "{\"ok\":false,\"error\":\"update\","
					 "\"reason\":\"rollback\"}"),
	     "U14 and rollback likewise", out);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.no_version = 1;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 500 && u_body_is(out, "{\"ok\":false,\"error\":\"broker\"}"),
	     "U15 an END OK without UPD_T_VERSION is 500", out);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.dest = 'C';
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 500 && u_body_is(out, "{\"ok\":false,\"error\":\"broker\"}"),
	     "U15 and one naming slot C", out);

	/* --- END only with its deadline inside the alarm ----------------------- */
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.alarm_elapsed = HTTP_UPLOAD_ALARM_S - UPLOAD_END_NEED_S + 1;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 408 && u_body_is(out, "{\"ok\":false,\"error\":\"timeout\"}"),
	     "U16 69 s left of the alarm: 408, END not sent", out);
	t_ok(strcmp(upd.log, "BADDDDDaA") == 0 && upd.ntimeouts == 0,
	     "U16 the alarm read and put back, no timeouts set, no END", upd.log);
	t_okf(upd.alarm_left == UPLOAD_END_NEED_S - 1,
	      "U16 and the alarm left as it was found", (long)upd.alarm_left,
	      UPLOAD_END_NEED_S - 1);
	upd_reset();
	upd_expect(U_SESS, U_CSRF, U_IP);
	upd.alarm_elapsed = HTTP_UPLOAD_ALARM_S - UPLOAD_END_NEED_S;
	st = u_run("10000", 10000, 1500, 0, out, sizeof(out));
	t_ok(st == 200 && upd.nend == 1,
	     "U16 control: 70 s left, END is sent", upd.log);

	/* --- what the parser keeps unchanged for this route -------------------- */
	upd_reset();
	(void)snprintf(head, sizeof(head), "POST %s HTTP/1.1\r\nHost: x\r\n"
		       "Transfer-Encoding: chunked\r\n\r\n", HTTP_UPLOAD_PATH);
	st = u_exchange(head, 0, 0, 0, out, sizeof(out));
	t_okf(st == 501 && upd.calls == 0,
	      "U17 Transfer-Encoding on the upload route is still 501, no call",
	      st, 501);
	upd_reset();
	(void)snprintf(head, sizeof(head), "GET %s HTTP/1.1\r\nHost: x\r\n\r\n",
		       HTTP_UPLOAD_PATH);
	st = u_exchange(head, 0, 0, 0, out, sizeof(out));
	t_okf(st == 405 && upd.calls == 0, "U17 GET on it is 405, no call", st,
	      405);
	upd_reset();
	(void)snprintf(head, sizeof(head), "POST %s HTTP/1.1\r\nHost: x\r\n\r\n",
		       HTTP_UPLOAD_PATH);
	st = u_exchange(head, 0, 0, 0, out, sizeof(out));
	t_okf(st == 411 && upd.calls == 0,
	      "U17 and POST without Content-Length is 411, no call", st, 411);
	/* the bound is this route's alone */
	upd_reset();
	(void)snprintf(head, sizeof(head), "POST /api/login HTTP/1.1\r\nHost: x\r\n"
		       "Content-Length: 4097\r\n\r\n");
	st = u_exchange(head, 0, 0, 0, out, sizeof(out));
	t_okf(st == 413, "U18 any other POST over 4,096 is 413 as before", st,
	      413);

	/* --- upload_run() itself: a read that times out, and one that fails ---- */
	{
		static const char tmo[] = "{\"ok\":false,\"error\":\"timeout\"}";
		struct timeval tv;
		struct route_env env;
		struct http_req q;
		struct http_rsp rs;
		uint8_t b[3000];
		int sv[2];
		uint32_t i;

		memset(&env, 0, sizeof(env));
		env.sock = "/nonexistent/broker.sock";
		env.client_ip = U_IP;
		env.alarm_fn = upd_alarm;
		u_head(head, sizeof(head), HTTP_UPLOAD_PATH, U_SESS, U_CSRF, U_CSRF,
		       "5000");
		t_okf(http_parse_all((const uint8_t *)head, strlen(head), &q) ==
		      HTTP_FEED_STREAM, "U19 the head parses as the upload route",
		      0, HTTP_FEED_STREAM);
		/* srv_conn() gives the body HTTP_BODY_TIMEOUT_S per read; the
		 * socket gets one second here, so the suite does not wait ten. */
		if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) == 0) {
			tv.tv_sec = 1;
			tv.tv_usec = 0;
			(void)setsockopt(sv[0], SOL_SOCKET, SO_RCVTIMEO, &tv,
					 sizeof(tv));
			for (i = 0; i < sizeof(b); i++)
				b[i] = upd_byte(i);
			(void)u_wr(sv[1], b, sizeof(b));
			upd_reset();
			upd_expect(U_SESS, U_CSRF, U_IP);
			st = upload_run(sv[0], &q, NULL, 0, &env, &rs);
			t_ok(st == 408 && rs.blen == strlen(tmo) &&
			     memcmp(rs.body, tmo, rs.blen) == 0,
			     "U19 3,000 of 5,000 and then silence: 408 timeout", rs.body);
			t_ok(upd.nend == 0 && strcmp(upd.log, "BAD") == 0,
			     "U19 the full piece went, END did not", upd.log);
			(void)close(sv[0]);
			(void)close(sv[1]);
		}
		/* A read that fails outright -- here a descriptor already closed --
		 * is a peer that is gone: nothing to answer, -1, and no DATA. */
		if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) == 0) {
			(void)close(sv[0]);
			(void)close(sv[1]);
			upd_reset();
			upd_expect(U_SESS, U_CSRF, U_IP);
			st = upload_run(sv[0], &q, NULL, 0, &env, &rs);
			t_okf(st == -1 && upd.nend == 0 && strcmp(upd.log, "BA") == 0,
			      "U20 a read that fails is no answer at all, and no DATA",
			      st, -1);
		}
	}
}

int main(void)
{
	char out[8192];
	int st;
	size_t n;

	/* A writer the answer outran is told by EPIPE, not killed by SIGPIPE; and
	 * a case that hangs is ended by this, the one real alarm in the program
	 * (upload.c's go to the stand-in through route_env.alarm_fn). */
	(void)signal(SIGPIPE, SIG_IGN);
	(void)alarm(600);

	/* A well-formed GET for a file that is not there: 404, and the head has
	 * every header SPEC-R7 requires.  The point is the wire bytes, not the
	 * struct. */
	{
		const char *p[] = { "GET /static/none.css HTTP/1.1\r\n"
				    "Host: 10.1.1.1\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 404, "404 on the wire", st, 404);
		t_ok(n > 100, "a response was written", NULL);
		t_ok(strncmp(out, "HTTP/1.1 404 Not Found\r\n", 24) == 0,
		     "the status line", out);
		t_ok(strstr(out, "\r\nX-Frame-Options: DENY\r\n") != NULL,
		     "X-Frame-Options", NULL);
		t_ok(strstr(out,
			    "\r\nContent-Security-Policy: default-src 'self'\r\n")
		     != NULL, "Content-Security-Policy", NULL);
		t_ok(strstr(out, "\r\nX-Content-Type-Options: nosniff\r\n") != NULL,
		     "X-Content-Type-Options", NULL);
		t_ok(strstr(out, "\r\nConnection: close\r\n") != NULL,
		     "Connection: close", NULL);
		t_ok(strstr(out, "\r\nContent-Length: ") != NULL, "Content-Length",
		     NULL);
		t_ok(strstr(out, "\r\n\r\n") != NULL, "the blank line", NULL);
		/* the body length on the wire equals the Content-Length */
		{
			const char *b = strstr(out, "\r\n\r\n");
			unsigned long cl = 0;
			const char *c = strstr(out, "Content-Length: ");

			if (c != NULL)
				cl = strtoul(c + 16, NULL, 10);
			t_okf(b != NULL && strlen(b + 4) == cl,
			      "the body is exactly Content-Length bytes",
			      b != NULL ? (long)strlen(b + 4) : -1, (long)cl);
		}
		t_ok(strstr(out, "none.css") == NULL,
		     "the requested name is not echoed anywhere in the answer",
		     NULL);
	}

	/* A peer that sends nothing and closes: no answer is owed, and nothing
	 * hangs.  This is the case a server that blocks on a first read gets
	 * wedged by. */
	{
		const char *p[] = { NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == -1, "a silent peer gets no response", st, -1);
		t_okf(n == 0, "and no bytes are written", (long)n, 0);
	}

	/* A peer that closes mid-request: one answer, and it is a refusal. */
	{
		const char *p[] = { "GET /api/sta", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a truncated request is 400", st, 400);
		t_ok(strncmp(out, "HTTP/1.1 400 Bad Request\r\n", 26) == 0,
		     "with the right status line", out);
	}

	/* A request delivered in five writes still parses as one request. */
	{
		const char *p[] = { "POST /api/lo", "gin HTTP/1.1\r\nHost: x\r\n",
				    "Content-Type: application/json\r\n",
				    "Content-Length: 23\r\n\r\n",
				    "{\"password\":\"abcdefgh\"}", NULL };

		n = exchange(p, out, sizeof(out), &st);
		/* The broker is unreachable in this test, so a correctly parsed
		 * login must come back 503 -- which is itself the evidence that
		 * the five writes were reassembled into one request. */
		t_okf(st == 503, "a request split across five writes reaches the"
		      " broker call", st, 503);
		t_ok(strstr(out, "\"broker\"") != NULL,
		     "and the answer names the unreachable broker", out);
	}
	{
		/* The same request with Content-Length one byte too high: the
		 * parser must still be waiting when the peer closes, so it is 400
		 * and not 503.  Without this case the one above would pass even if
		 * the length check did nothing. */
		const char *p[] = { "POST /api/login HTTP/1.1\r\nHost: x\r\n"
				    "Content-Type: application/json\r\n"
				    "Content-Length: 24\r\n\r\n"
				    "{\"password\":\"abcdefgh\"}", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a body one byte shorter than announced is 400",
		      st, 400);
	}

	/* chunked is 501 on the wire, not an ignored header. */
	{
		const char *p[] = { "POST /api/login HTTP/1.1\r\nHost: x\r\n"
				    "Transfer-Encoding: chunked\r\n\r\n"
				    "4\r\nabcd\r\n0\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 501, "chunked is 501", st, 501);
		t_ok(strncmp(out, "HTTP/1.1 501 Not Implemented\r\n", 30) == 0,
		     "with the right status line", out);
	}

	/* An over-long request line is refused with 414 and the answer is small:
	 * a refusal must not be proportional to the input. */
	{
		static char big[4096];
		const char *p[2];
		size_t i = 0;

		memcpy(big, "GET /", 5);
		i = 5;
		while (i < 2000)
			big[i++] = 'a';
		memcpy(big + i, " HTTP/1.1\r\n\r\n", 13);
		i += 13;
		big[i] = '\0';
		p[0] = big;
		p[1] = NULL;
		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 414, "a 2000-byte target is 414", st, 414);
		t_ok(n < 400, "and the answer is under 400 bytes", NULL);
		t_ok(strstr(out, "aaaa") == NULL,
		     "with none of the target in it", NULL);
	}

	/* A method the program does not implement is 405 on the wire, with the
	 * Allow header, and a bare-LF request line is 400 -- both decided in the
	 * parser but only visible as bytes here. */
	{
		const char *p[] = { "DELETE / HTTP/1.1\r\nHost: x\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 405, "DELETE is 405 on the wire", st, 405);
		t_ok(strstr(out, "\r\nAllow: GET, POST\r\n") != NULL,
		     "with an Allow header", NULL);
	}
	{
		const char *p[] = { "GET / HTTP/1.1\nHost: x\n\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a bare-LF request is 400 on the wire", st, 400);
	}

	/* ---------------------------------------- the parent's ONE KDF grant
	 * MEASURED on the device on 2026-09-30, image r78a: POST /api/login answered
	 * `429 {"ok":false,"error":"ratelimit","retry_s":2}` in 0.030 s and went
	 * on answering it -- after 20 s of idle, and after a further 90 s of no
	 * requests at all -- while GET /api/status kept answering 200 from the
	 * same httpd.  The administrator could not log in again for the life of
	 * the process.
	 *
	 * These cases are that sequence, run against srv_loop()'s own arbitration
	 * with the clock supplied, so there is no sleep, no fork and no socket.
	 * The bucket in rl.c is NOT what did it, and test_rl.c's sweep is the
	 * evidence: a 90 s gap refills a login bucket to its burst from every
	 * state it can be in, and the smallest retry_s an empty login bucket can
	 * name is 5.  A constant 2 has one source, SRV_KDF_BUSY_S, and reaching it
	 * needs a holder -- so the holder was one that no longer existed.
	 */
	{
		uint32_t retry = 999u;
		const uint32_t ipa = 0x0a010164u;      /* 10.1.1.100 */
		const uint32_t ipb = 0x0a010165u;
		int got;

		srv_kdf_reset();
		got = srv_kdf_ask(0, ipa, 640000u, &retry);
		t_okf(got == 1, "control: a first login is granted the KDF", got,
		      1);
		retry = 999u;
		got = srv_kdf_ask(1, ipb, 640050u, &retry);
		t_okf(got == 0,
		      "control: a second asker is refused while one is in flight",
		      got, 0);
		t_okf(retry == SRV_KDF_BUSY_S,
		      "and the refusal is the busy constant", (long)retry,
		      (long)SRV_KDF_BUSY_S);

		/* The holder exited and was reaped before the parent read its
		 * release byte or its EOF.  srv_kdf_gone() is the line reap()
		 * runs, so this is that event and not a model of it. */
		srv_kdf_gone(0);
		retry = 999u;
		got = srv_kdf_ask(1, ipb, 640060u, &retry);
		t_okf(got == 1, "a grant whose holder was reaped is not still"
		      " held", got, 1);
		srv_kdf_gone(1);
		retry = 999u;
		got = srv_kdf_ask(2, ipa, 660060u, &retry);
		t_okf(got == 1, "and after 20 s of no requests a login is"
		      " granted", got, 1);
		srv_kdf_gone(2);
		retry = 999u;
		got = srv_kdf_ask(3, ipa, 750060u, &retry);
		t_okf(got == 1, "and after a further 90 s of no requests at all",
		      got, 1);
		srv_kdf_gone(3);
	}

	/* The property brokerd's own bucket suite asserts and this one did not:
	 * once the wait the limiter ANNOUNCED has passed, a correct password gets
	 * through.  The wait is read back from the refusal, not assumed. */
	{
		uint32_t retry = 999u, waited;
		const uint32_t ipc = 0x0a0101c8u;
		unsigned k;
		int ngrant = 0;

		srv_kdf_reset();
		for (k = 0; k < 8u; k++) {
			if (srv_kdf_ask(0, ipc, 100000u, &retry))
				ngrant++;
			srv_kdf_gone(0);
		}
		t_okf(ngrant == RL_KDF_IP_BURST, "the burst, and only the burst",
		      ngrant, RL_KDF_IP_BURST);
		waited = retry;
		t_okf(waited >= 1u, "a refusal names a time to come back",
		      (long)waited, 11);
		retry = 999u;
		ngrant = srv_kdf_ask(0, ipc, 100000u + waited * 1000u, &retry);
		t_okf(ngrant == 1, "and at that time the login IS granted", ngrant,
		      1);
		srv_kdf_gone(0);
	}

	/* A refused attempt must not push the next grant further out.  Two runs
	 * from the same drained state: one that waits quietly, one that is refused
	 * at every 100 ms tick of the wait.  Both must be granted at the same
	 * clock reading, or a client that retries can never get in. */
	{
		const uint32_t ipd = 0x0a0101c9u;
		const uint32_t t0 = 200000u;
		uint32_t retry = 0u;
		unsigned k, quiet = 0u, noisy = 0u;

		for (k = 1u; k <= 300u && quiet == 0u; k++) {
			unsigned j;

			srv_kdf_reset();
			for (j = 0; j < 4u; j++) {
				(void)srv_kdf_ask(0, ipd, t0, &retry);
				srv_kdf_gone(0);
			}
			if (srv_kdf_ask(0, ipd, t0 + k * 100u, &retry))
				quiet = k;
			srv_kdf_gone(0);
		}
		srv_kdf_reset();
		for (k = 0; k < 4u; k++) {
			(void)srv_kdf_ask(0, ipd, t0, &retry);
			srv_kdf_gone(0);
		}
		for (k = 1u; k <= 300u; k++) {
			if (srv_kdf_ask(0, ipd, t0 + k * 100u, &retry)) {
				noisy = k;
				break;
			}
			srv_kdf_gone(0);
		}
		/* The tick a quiet client gets in at, re-derived from the rate
		 * rather than copied: the slower bucket needs one whole token at
		 * RL_KDF_IP_RATE milli per second, in 100 ms ticks. */
		t_okf(quiet == (1000u / RL_KDF_IP_RATE) * 10u,
		      "a client that waits quietly is granted at the tick its"
		      " rate says", (long)quiet,
		      (long)((1000u / RL_KDF_IP_RATE) * 10u));
		t_okf(noisy == quiet,
		      "and a client refused at every tick of that wait is granted"
		      " at the same tick", (long)noisy, (long)quiet);
	}

	/* And a refusal must not charge a bucket that did not cause it.  Three
	 * other addresses drain the GLOBAL bucket; then one address is refused by
	 * it three times at a single instant, so no refill can hide the
	 * arithmetic.  Four seconds later the global holds exactly one token, and
	 * that address may have it only if its own bucket kept its burst. */
	{
		const uint32_t ipx = 0x0a0101d0u;
		const uint32_t t0 = 300000u;
		uint32_t retry = 0u;
		unsigned k;
		int got;

		srv_kdf_reset();
		for (k = 0; k < (unsigned)RL_KDF_BURST; k++) {
			(void)srv_kdf_ask(0, 0x0a0102f0u + k, t0, &retry);
			srv_kdf_gone(0);
		}
		for (k = 0; k < 3u; k++) {
			retry = 999u;
			got = srv_kdf_ask(0, ipx, t0, &retry);
			t_okf(got == 0, "the global bucket refuses an address that"
			      " never asked", got, 0);
			srv_kdf_gone(0);
		}
		t_okf(retry == (1000u + RL_KDF_RATE_MILLI - 1u) /
		      RL_KDF_RATE_MILLI + 1u,
		      "and by that bucket's own wait, not the busy constant",
		      (long)retry,
		      (long)((1000u + RL_KDF_RATE_MILLI - 1u) /
			     RL_KDF_RATE_MILLI + 1u));
		retry = 999u;
		got = srv_kdf_ask(0, ipx, t0 + 4000u, &retry);
		t_okf(got == 1, "a refusal the global caused did not charge the"
		      " address' own bucket", got, 1);
		srv_kdf_gone(0);
	}

	/* The guard shown permitting and refusing, and the refusal that is
	 * CORRECT: a holder that is still there keeps the grant for as long as it
	 * takes, because the bound on a running evaluation is the child's own
	 * alarm() and not a timer in the parent. */
	{
		uint32_t retry = 999u;
		const uint32_t ipe = 0x0a0101d8u;
		int got;

		srv_kdf_reset();
		got = srv_kdf_ask(0, ipe, 400000u, &retry);
		t_okf(got == 1, "control: the arbitration permits", got, 1);
		retry = 999u;
		got = srv_kdf_ask(1, ipe, 1000000u, &retry);
		t_okf(got == 0, "control: and refuses ten minutes later while a"
		      " live holder still holds it", got, 0);
		t_okf(retry == SRV_KDF_BUSY_S, "with the busy constant",
		      (long)retry, (long)SRV_KDF_BUSY_S);
		srv_kdf_gone(0);
	}

	/* The stand-in's own refusals first: nothing below may rely on it until
	 * it is shown saying no. */
	standin_cases();
	upload_cases();

	/* 45 before the upload; 17 stand-in controls (S); 135 upload cases (U). */
	return t_done(197);
}
