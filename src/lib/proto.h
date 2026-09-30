/* src/lib/proto.h -- the broker wire codec (SPEC-R7 § 6).
 *
 * Two headers, both fixed size, every integer big-endian and decoded with
 * explicit shifts.  No struct is ever memcpy'd to or from the wire: the
 * on-wire layout and `struct proto_req` are independent, and the offsets
 * below are the only place the layout is written down.
 *
 * The request decoder is the attack surface (a uid-100 or uid-101 peer, and
 * on a compromised httpd an attacker's bytes, reach it).  It is therefore an
 * incremental state machine -- `proto_rx_*` -- that never reads past what it
 * was handed, holds no pointer into the caller's buffer, uses no VLA, no
 * recursion and no alloca, and whose only dynamic length (`body_len`) is
 * bounded before a single body byte is accepted.  `proto_decode_req` is the
 * one-shot wrapper over the same machine; `src/fuzz/fuzz_proto.c` drives both
 * and asserts they agree, so a split-read bug is a differential failure.
 */
#ifndef RLXFW_PROTO_H
#define RLXFW_PROTO_H

#include <stddef.h>
#include <stdint.h>

#define PROTO_REQ_MAGIC   0x524C5842u  /* "RLXB" */
#define PROTO_RESP_MAGIC  0x524C5852u  /* "RLXR" */
#define PROTO_VERSION     1

#define PROTO_REQ_HDR      48
#define PROTO_RESP_HDR     12
#define PROTO_REQ_BODY_MAX 2048
#define PROTO_RESP_BODY_MAX 4096
#define PROTO_REQ_MAX      (PROTO_REQ_HDR + PROTO_REQ_BODY_MAX)
#define PROTO_RESP_MAX     (PROTO_RESP_HDR + PROTO_RESP_BODY_MAX)

#define PROTO_TOK_LEN 16

/* Request header offsets.  Written once, here. */
#define PROTO_RQ_O_MAGIC   0
#define PROTO_RQ_O_VERSION 4
#define PROTO_RQ_O_OP      5
#define PROTO_RQ_O_FLAGS   6
#define PROTO_RQ_O_SESSION 8
#define PROTO_RQ_O_CSRF    24
#define PROTO_RQ_O_CLIENTIP 40
#define PROTO_RQ_O_BODYLEN 44

#define PROTO_RS_O_MAGIC   0
#define PROTO_RS_O_VERSION 4
#define PROTO_RS_O_STATUS  5
#define PROTO_RS_O_RESERVED 6
#define PROTO_RS_O_BODYLEN 8

/* Ops (SPEC-R7 § 6).  The codec does NOT judge op validity: an unknown op is
 * a well-formed request that the dispatcher answers NOTSUP.  Mixing the two
 * would turn "a future op" into "a malformed frame". */
enum {
	OP_GET    = 0x01,
	OP_SET    = 0x02,
	OP_REBOOT = 0x03,
	OP_STATUS = 0x04,
	OP_PING   = 0x05,
	OP_LOGIN  = 0x10,
	OP_LOGOUT = 0x11,
	OP_PWSET  = 0x12,
	OP_UPDATE_BEGIN = 0x20,
	OP_UPDATE_DATA  = 0x21,
	OP_UPDATE_END   = 0x22
};

/* Status codes (SPEC-R7 § 6). */
enum {
	ST_OK = 0, ST_BADREQ = 1, ST_PERM = 2, ST_AUTH = 3, ST_LOCKED = 4,
	ST_INVAL = 5, ST_IO = 6, ST_NOENT = 7, ST_BUSY = 8, ST_NOTSUP = 9,
	ST_NOENTROPY = 10
};

/* Codec errors.  All negative, all distinct, none overlapping a byte count. */
#define PROTO_E_SHORT   (-1)   /* incomplete: need more bytes */
#define PROTO_E_MAGIC   (-2)
#define PROTO_E_VERSION (-3)
#define PROTO_E_FLAGS   (-4)
#define PROTO_E_BODYLEN (-5)
#define PROTO_E_INVAL   (-6)   /* a null argument or an impossible capacity */
#define PROTO_E_RESERVED (-7)

struct proto_req {
	uint8_t  version;
	uint8_t  op;
	uint16_t flags;
	uint8_t  session[PROTO_TOK_LEN];
	uint8_t  csrf[PROTO_TOK_LEN];
	uint32_t client_ip;
	uint32_t body_len;
	uint8_t  body[PROTO_REQ_BODY_MAX];
};

struct proto_resp {
	uint8_t  version;
	uint8_t  status;
	uint16_t reserved;
	uint32_t body_len;
	uint8_t  body[PROTO_RESP_BODY_MAX];
};

/* ---- the incremental request decoder --------------------------------- */

enum proto_rx_state {
	PRX_HDR = 0,     /* filling the 48-byte header */
	PRX_BODY,        /* filling body_len bytes */
	PRX_DONE,        /* a complete request sits in ->req */
	PRX_ERR          /* refused; ->err says why and the machine is stuck */
};

struct proto_rx {
	int      state;
	int      err;
	uint32_t have;      /* bytes of the current section already stored */
	uint32_t want;      /* bytes the current section still needs in total */
	uint8_t  hdrbuf[PROTO_REQ_HDR];   /* the header, before it is believed */
	struct proto_req req;
};

void proto_rx_init(struct proto_rx *rx);

/* Feed up to n bytes.  *used is set to how many were consumed (0 when the
 * machine is already DONE or ERR).  Returns PRX_DONE, PRX_HDR/PRX_BODY (more
 * wanted) or a negative PROTO_E_* once and thereafter.  Never reads past
 * p[n-1]; never writes past its own fixed-size fields. */
int proto_rx_feed(struct proto_rx *rx, const uint8_t *p, size_t n, size_t *used);

/* One-shot: decode exactly one request out of buf[0..n).  Returns the number
 * of bytes consumed (48 + body_len) or a negative PROTO_E_*.  Trailing bytes
 * past the request are left for the caller and are NOT an error here -- the
 * broker rejects them at the connection layer, where "one request per
 * connection" is the rule that can see them. */
int proto_decode_req(const uint8_t *buf, size_t n, struct proto_req *out);

/* Encode. Returns bytes written or negative. */
int proto_encode_req(const struct proto_req *rq, uint8_t *buf, size_t n);
int proto_encode_resp(const struct proto_resp *rs, uint8_t *buf, size_t n);
int proto_decode_resp(const uint8_t *buf, size_t n, struct proto_resp *out);

/* ---- bounded big-endian helpers (used by both sides) ----------------- */
uint16_t proto_be16(const uint8_t *p);
uint32_t proto_be32(const uint8_t *p);
void     proto_put_be16(uint8_t *p, uint16_t v);
void     proto_put_be32(uint8_t *p, uint32_t v);

/* Bounded TLV writer/reader for op bodies (type u16 BE, len u16 BE, value).
 * Deliberately local to proto.c and named proto_tlv_*: src/lib/tlv.c belongs
 * to another agent and these four functions must not collide with it.  They
 * should collapse onto that file once both exist.  Returns 0/-1. */
int proto_tlv_put(uint8_t *buf, size_t cap, size_t *off,
                  uint16_t type, const uint8_t *val, uint16_t len);
int proto_tlv_put_u8(uint8_t *buf, size_t cap, size_t *off, uint16_t type, uint8_t v);
int proto_tlv_put_u32(uint8_t *buf, size_t cap, size_t *off, uint16_t type, uint32_t v);
/* Reads one TLV at *off.  On success advances *off and points *val into buf.
 * Returns 0, or -1 on a truncated or over-long TLV. */
int proto_tlv_get(const uint8_t *buf, size_t n, size_t *off,
                  uint16_t *type, const uint8_t **val, uint16_t *len);

#endif /* RLXFW_PROTO_H */
