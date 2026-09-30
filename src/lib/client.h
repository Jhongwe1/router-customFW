/* src/lib/client.h -- the broker client, used by httpd, dnsfwd and cfgstore.
 * Pinned by SPEC-R7 § 6; bk_call() connects, writes one request, reads one
 * response, closes.  Blocking with timeouts, no threads, no globals.
 */
#ifndef RLXFW_CLIENT_H
#define RLXFW_CLIENT_H

#include <stdint.h>

#include "proto.h"

struct bk_req {
	uint8_t  op;
	uint8_t  session[16];
	uint8_t  csrf[16];
	uint32_t client_ip;
	const uint8_t *body;
	uint32_t body_len;
};

struct bk_resp {
	uint8_t  status;
	uint32_t body_len;
	uint8_t  body[4096];
};

/* 0 on a complete response, or -errno.  -ETIMEDOUT when the broker did not
 * answer inside the call timeout; -EPROTO when what came back is not a
 * response frame. */
int bk_call(const char *sock_path, const struct bk_req *rq, struct bk_resp *rs);

/* The timeouts bk_call uses, exposed so a caller (httpd, with its own 10 s
 * budget) can shorten them.  Seconds; 0 means "leave as is". */
void bk_set_timeouts(int connect_s, int io_s);

/* ---- BK_* spellings, for the callers that were written against the stubs ---
 *
 * httpd and dnsfwd were built in parallel with this file and each carried a
 * local stand-in that named SPEC-R7 § 6's ops and statuses `BK_*`; proto.h
 * names them `OP_*` and `ST_*`.  量 `R7-8`: the two sets agreed on every
 * value.  These are aliases, not a second transcription -- each expands to
 * proto.h's enumerator, so there is still exactly one place a number is
 * written, and a change to proto.h reaches these without an edit.
 *
 * dnsfwd's stand-in spelled GET `BK_OP_GET`; httpd's spelled it `BK_GET`.
 * Both are here rather than editing one of the two call sites to match the
 * other, which would be a behaviour-free diff in someone else's program. */
#define BK_OK        ST_OK
#define BK_BADREQ    ST_BADREQ
#define BK_PERM      ST_PERM
#define BK_AUTH      ST_AUTH
#define BK_LOCKED    ST_LOCKED
#define BK_INVAL     ST_INVAL
#define BK_IO        ST_IO
#define BK_NOENT     ST_NOENT
#define BK_BUSY      ST_BUSY
#define BK_NOTSUP    ST_NOTSUP
#define BK_NOENTROPY ST_NOENTROPY

#define BK_GET       OP_GET
#define BK_SET       OP_SET
#define BK_REBOOT    OP_REBOOT
#define BK_STATUS    OP_STATUS
#define BK_PING      OP_PING
#define BK_LOGIN     OP_LOGIN
#define BK_LOGOUT    OP_LOGOUT
#define BK_PWSET     OP_PWSET
#define BK_OP_GET    OP_GET

#define BK_REQ_MAGIC     PROTO_REQ_MAGIC
#define BK_RESP_MAGIC    PROTO_RESP_MAGIC
#define BK_VERSION       PROTO_VERSION
#define BK_REQ_HDR       PROTO_REQ_HDR
#define BK_RESP_HDR      PROTO_RESP_HDR
#define BK_BODY_IN_MAX   PROTO_REQ_BODY_MAX
#define BK_BODY_OUT_MAX  PROTO_RESP_BODY_MAX

#endif /* RLXFW_CLIENT_H */
