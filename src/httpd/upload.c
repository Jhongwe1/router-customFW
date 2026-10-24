/* src/httpd/upload.c -- POST /api/firmware, streamed to brokerd (upload.h).
 *
 * WHAT THIS FILE HOLDS, and the bound on each:
 *   - one piece.  `msg` is the 4-byte offset and UPD_DATA_MAX bytes, 2,048 in
 *     all, which is PROTO_REQ_BODY_MAX: the largest body bk_call() sends.  A
 *     piece is filled to UPD_DATA_MAX before it goes, so an n-byte body is
 *     ceil(n / UPD_DATA_MAX) DATA calls whatever sizes the peer's segments come
 *     in, and only the last is short;
 *   - no file.  Its descriptors are the peer's socket and bk_call()'s one socket
 *     per call to the broker, the door every other route already uses;
 *   - no body byte leaves before BEGIN's OK.  The bytes srv_conn() read past the
 *     blank line sit in its receive buffer while the gate and BEGIN run -- one
 *     read() of 2,048 cannot stop at a blank line it has not yet seen -- and are
 *     copied into the first piece only after BEGIN said OK.
 *
 * WHY BROKERD'S OWN COUNT IS CHECKED.  Every DATA OK carries UPD_T_RECEIVED, the
 * bytes brokerd holds.  A count that is not this file's offset plus the piece is
 * a client and a broker that disagree about where the image is, and the answer
 * is 500 with no END: END is the one call that could act on the disagreement.
 *
 * WHAT IT DOES NOT ESTABLISH.  upload.h says it: a stand-in, not brokerd, has
 * answered every call this file has made, and nothing here has run on the
 * device.
 */

#include "upload.h"

#include "client.h"
#include "json.h"
#include "proto.h"

#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

/* The call's state, in one place so upload_run() can zero all of it: the
 * request header (the session and CSRF tokens), the last reply, the piece. */
struct up_ctx {
	struct bk_req  q;
	struct bk_resp br;
	uint8_t        msg[4 + UPD_DATA_MAX];
};

static unsigned up_alarm(const struct route_env *env, unsigned secs)
{
	if (env->alarm_fn != NULL)
		return env->alarm_fn(secs);
	return alarm(secs);
}

static ssize_t up_read(int fd, uint8_t *p, size_t n)
{
	ssize_t r;

	if (fd < 0)
		return 0;               /* no socket: the body ends here */
	do {
		r = read(fd, p, n);
	} while (r < 0 && errno == EINTR);
	return r;
}

/* The value of the first TLV of type `want` in a reply, or -1. */
static int up_tlv(const struct bk_resp *br, uint16_t want,
		  const uint8_t **val, uint16_t *len)
{
	size_t off = 0;
	uint16_t t;

	while (proto_tlv_get(br->body, br->body_len, &off, &t, val, len) == 0) {
		if (t == want)
			return 0;
	}
	return -1;
}

/* The reason brokerd named, if it is one: 1..UPD_REASON_MAX bytes of [a-z0-9_],
 * the alphabet every name of notes/self-update.md §§ 4.4 and 4.6 and of
 * src/rlxboot/container.c is spelled in.  Anything else is not rendered, so no
 * byte this function did not vet reaches the JSON writer. */
static int up_reason(const struct bk_resp *br, const char **why, uint16_t *wl)
{
	const uint8_t *v;
	uint16_t l, i;

	if (up_tlv(br, UPD_T_REASON, &v, &l) != 0)
		return -1;
	if (l == 0 || l > UPD_REASON_MAX)
		return -1;
	for (i = 0; i < l; i++) {
		uint8_t c = v[i];

		if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
		      c == '_'))
			return -1;
	}
	*why = (const char *)v;
	*wl = l;
	return 0;
}

/* A refusal of one of the three ops: the HTTP status every route gives that
 * broker status, and the update form of the body when brokerd named a reason.
 * Without one -- the broker's own gate refuses AUTH or PERM before an op runs --
 * the body is the one every other route sends for that status. */
static void up_refused(struct http_rsp *rs, const struct bk_resp *br)
{
	struct json_w w;
	const char *why;
	uint16_t wl;

	route_map_status(rs, br->status, NULL, 0);
	if (up_reason(br, &why, &wl) != 0)
		return;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 0);
	json_w_str(&w, "error", "update");
	json_w_strn(&w, "reason", why, wl);
	json_w_obj_close(&w);
	if (json_w_done(&w) != 0) {
		route_err(rs, 500, "toolong");
		return;
	}
	rs->blen = w.len;
}

/* One broker call.  0 = OK and c->br is the reply; -1 = *rs is the answer. */
static int up_call(const struct route_env *env, struct up_ctx *c, uint8_t op,
		   uint32_t blen, struct http_rsp *rs)
{
	c->q.op = op;
	c->q.body = c->msg;
	c->q.body_len = blen;
	if (bk_call(env->sock, &c->q, &c->br) != 0) {
		/* as call_broker(): unreachable is 503, and nothing about why */
		route_err(rs, 503, "broker");
		return -1;
	}
	if (c->br.status != BK_OK) {
		up_refused(rs, &c->br);
		return -1;
	}
	return 0;
}

/* END's OK: {"ok":true,"slot":"A","version":7}, or 500 when the reply does not
 * carry both TLVs in their declared shapes. */
static void up_verdict(struct http_rsp *rs, const struct bk_resp *br)
{
	const uint8_t *dv, *vv;
	uint16_t dl, vl;
	struct json_w w;
	char slot[2];

	if (up_tlv(br, UPD_T_DEST, &dv, &dl) != 0 || dl != 1 ||
	    (dv[0] != 'A' && dv[0] != 'B') ||
	    up_tlv(br, UPD_T_VERSION, &vv, &vl) != 0 || vl != 4) {
		route_err(rs, 500, "broker");
		return;
	}
	slot[0] = (char)dv[0];
	slot[1] = '\0';
	rs->status = 200;
	rs->ctype = "application/json";
	rs->fd = -1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	json_w_str(&w, "slot", slot);
	json_w_num(&w, "version", proto_be32(vv));
	json_w_obj_close(&w);
	if (json_w_done(&w) != 0) {
		route_err(rs, 500, "toolong");
		return;
	}
	rs->blen = w.len;
}

static int up_stream(int fd, const struct http_req *rq, const uint8_t *pre,
		     size_t npre, const struct route_env *env,
		     struct http_rsp *rs, struct up_ctx *c)
{
	uint32_t total = rq->clen;
	uint32_t off = 0;
	unsigned left;

	/* 1. The gate.  A refusal here has made no broker call. */
	if (route_stream_gate(rq, rs) != 0)
		return rs->status;
	if (route_bk_req(env, rq, &c->q, rs) != 0)
		return rs->status;

	/* 2. BEGIN: the declared length, and nothing of the body. */
	proto_put_be32(c->msg, total);
	if (up_call(env, c, OP_UPDATE_BEGIN, 4, rs) != 0)
		return rs->status;

	/* 3. Only now does the child's bound become the upload's. */
	(void)up_alarm(env, HTTP_UPLOAD_ALARM_S);

	if (npre > total)
		npre = total;           /* bytes past Content-Length are not body */

	/* 4. The pieces. */
	while (off < total) {
		uint32_t want = total - off;
		uint32_t have = 0;
		const uint8_t *v;
		uint16_t l;

		if (want > UPD_DATA_MAX)
			want = UPD_DATA_MAX;
		while (have < want) {
			ssize_t r;

			if (npre > 0) {
				size_t take = want - have;

				if (take > npre)
					take = npre;
				memcpy(c->msg + 4 + have, pre, take);
				pre += take;
				npre -= take;
				have += (uint32_t)take;
				continue;
			}
			r = up_read(fd, c->msg + 4 + have, want - have);
			if (r == 0) {
				/* srv_conn()'s own answer to a request cut short;
				 * no END, so brokerd's staging is never verified */
				route_err(rs, 400, "short");
				return rs->status;
			}
			if (r < 0) {
				if (errno == EAGAIN || errno == EWOULDBLOCK) {
					route_err(rs, 408, "timeout");
					return rs->status;
				}
				return -1;      /* the peer is gone: no answer */
			}
			have += (uint32_t)r;
		}
		proto_put_be32(c->msg, off);
		if (up_call(env, c, OP_UPDATE_DATA, 4 + want, rs) != 0)
			return rs->status;
		if (up_tlv(&c->br, UPD_T_RECEIVED, &v, &l) != 0 || l != 4 ||
		    proto_be32(v) != off + want) {
			route_err(rs, 500, "broker");
			return rs->status;
		}
		off += want;
	}

	/* 5. END, only with its whole deadline inside what is left of the alarm.
	 * alarm(0) reads and cancels; the same value goes straight back. */
	left = up_alarm(env, 0);
	if (left != 0)
		(void)up_alarm(env, left);
	if (left < UPLOAD_END_NEED_S) {
		route_err(rs, 408, "timeout");
		return rs->status;
	}
	bk_set_timeouts(UPLOAD_END_CONNECT_S, UPLOAD_END_IO_S);
	proto_put_be32(c->msg, total);
	if (up_call(env, c, OP_UPDATE_END, 4, rs) != 0)
		return rs->status;

	/* 6. The verdict. */
	up_verdict(rs, &c->br);
	return rs->status;
}

int upload_run(int fd, const struct http_req *rq, const uint8_t *pre,
	       size_t npre, const struct route_env *env, struct http_rsp *rs)
{
	struct up_ctx c;
	int ret;

	memset(&c, 0, sizeof(c));
	route_rsp_init(rs);
	ret = up_stream(fd, rq, pre, npre, env, rs, &c);
	rs->nostore = 1;
	/* The tokens and the last piece leave the stack zeroed, as srv_conn()
	 * zeroes the request they came from. */
	memset(&c, 0, sizeof(c));
	return ret;
}
