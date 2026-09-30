/* src/lib/proto.c -- the broker wire codec.  See proto.h for the contract.
 *
 * Every bound in this file is checked against the bytes actually present, not
 * against a length taken off the wire.  `body_len` is validated the instant
 * the 48th header byte lands and before any body byte is stored, so
 * `rx->want` can never exceed sizeof(rx->req.body).
 */
#include <string.h>

#include "proto.h"

uint16_t proto_be16(const uint8_t *p)
{
	return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

uint32_t proto_be32(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
	       ((uint32_t)p[2] << 8)  | (uint32_t)p[3];
}

void proto_put_be16(uint8_t *p, uint16_t v)
{
	p[0] = (uint8_t)(v >> 8);
	p[1] = (uint8_t)(v & 0xFFu);
}

void proto_put_be32(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)(v >> 24);
	p[1] = (uint8_t)((v >> 16) & 0xFFu);
	p[2] = (uint8_t)((v >> 8) & 0xFFu);
	p[3] = (uint8_t)(v & 0xFFu);
}

/* ---------------------------------------------------------------- decoder */

void proto_rx_init(struct proto_rx *rx)
{
	if (rx == 0)
		return;
	/* memset over our own object, never over wire bytes. */
	memset(rx, 0, sizeof(*rx));
	rx->state = PRX_HDR;
	rx->err = 0;
	rx->have = 0;
	rx->want = PROTO_REQ_HDR;
}

/* Called once, with exactly PROTO_REQ_HDR bytes in hdr[].  Returns 0 or a
 * negative PROTO_E_*.  This is the whole of the header's grammar. */
static int rx_header(struct proto_rx *rx, const uint8_t *hdr)
{
	uint32_t magic, blen;
	uint16_t flags;

	magic = proto_be32(hdr + PROTO_RQ_O_MAGIC);
	if (magic != PROTO_REQ_MAGIC)
		return PROTO_E_MAGIC;

	if (hdr[PROTO_RQ_O_VERSION] != PROTO_VERSION)
		return PROTO_E_VERSION;

	flags = proto_be16(hdr + PROTO_RQ_O_FLAGS);
	if (flags != 0)
		return PROTO_E_FLAGS;

	blen = proto_be32(hdr + PROTO_RQ_O_BODYLEN);
	/* The bound.  Dropping this line is the planted mutation in the test
	 * suite (test_proto.c, MUT_NO_BODYLEN_BOUND): without it `rx->want`
	 * takes an attacker's 32-bit value and the body copy walks off
	 * rx->req.body. */
	if (blen > PROTO_REQ_BODY_MAX)
		return PROTO_E_BODYLEN;

	rx->req.version = hdr[PROTO_RQ_O_VERSION];
	rx->req.op      = hdr[PROTO_RQ_O_OP];
	rx->req.flags   = flags;
	memcpy(rx->req.session, hdr + PROTO_RQ_O_SESSION, PROTO_TOK_LEN);
	memcpy(rx->req.csrf,    hdr + PROTO_RQ_O_CSRF,    PROTO_TOK_LEN);
	rx->req.client_ip = proto_be32(hdr + PROTO_RQ_O_CLIENTIP);
	rx->req.body_len  = blen;
	return 0;
}

int proto_rx_feed(struct proto_rx *rx, const uint8_t *p, size_t n, size_t *used)
{
	size_t consumed = 0;

	if (used != 0)
		*used = 0;
	if (rx == 0 || (p == 0 && n != 0))
		return PROTO_E_INVAL;
	if (rx->state == PRX_ERR)
		return rx->err;
	if (rx->state == PRX_DONE)
		return PRX_DONE;

	/* Two sections at most, so a bounded loop of two iterations; no
	 * recursion and no unbounded spin (each iteration either consumes a
	 * byte or returns). */
	for (;;) {
		size_t room, take;
		uint8_t *dst;
		uint32_t cap;

		if (rx->state == PRX_HDR) {
			/* The header lands in its own fixed 48-byte buffer and
			 * is not believed until all 48 bytes are there. */
			cap = (uint32_t)sizeof(rx->hdrbuf);
			dst = rx->hdrbuf;
		} else {
			cap = rx->req.body_len;
			dst = rx->req.body;
		}

		if (rx->have > cap || rx->want > cap) {
			/* Unreachable by construction; refuse rather than
			 * trust the invariant. */
			rx->state = PRX_ERR;
			rx->err = PROTO_E_INVAL;
			if (used != 0)
				*used = consumed;
			return rx->err;
		}

		room = (size_t)(rx->want - rx->have);
		if (room == 0)
			take = 0;
		else {
			take = n - consumed;
			if (take > room)
				take = room;
		}
		if (take != 0) {
			memcpy(dst + rx->have, p + consumed, take);
			rx->have += (uint32_t)take;
			consumed += take;
		}

		if (rx->have < rx->want) {
			if (used != 0)
				*used = consumed;
			return rx->state;          /* PRX_HDR or PRX_BODY */
		}

		/* The current section is complete. */
		if (rx->state == PRX_HDR) {
			int rc = rx_header(rx, rx->hdrbuf);
			if (rc != 0) {
				rx->state = PRX_ERR;
				rx->err = rc;
				if (used != 0)
					*used = consumed;
				return rc;
			}
			if (rx->req.body_len == 0) {
				rx->state = PRX_DONE;
				if (used != 0)
					*used = consumed;
				return PRX_DONE;
			}
			rx->state = PRX_BODY;
			rx->have = 0;
			rx->want = rx->req.body_len;
			if (consumed == n) {
				if (used != 0)
					*used = consumed;
				return PRX_BODY;
			}
			continue;                  /* second and last pass */
		}

		rx->state = PRX_DONE;
		if (used != 0)
			*used = consumed;
		return PRX_DONE;
	}
}

int proto_decode_req(const uint8_t *buf, size_t n, struct proto_req *out)
{
	struct proto_rx rx;
	size_t used = 0;
	int rc;

	if (out == 0 || (buf == 0 && n != 0))
		return PROTO_E_INVAL;

	proto_rx_init(&rx);
	rc = proto_rx_feed(&rx, buf, n, &used);
	if (rc < 0)
		return rc;
	if (rc != PRX_DONE)
		return PROTO_E_SHORT;
	*out = rx.req;                     /* struct copy between our own objects */
	return (int)used;
}

/* ---------------------------------------------------------------- encoder */

int proto_encode_req(const struct proto_req *rq, uint8_t *buf, size_t n)
{
	size_t total;

	if (rq == 0 || buf == 0)
		return PROTO_E_INVAL;
	if (rq->body_len > PROTO_REQ_BODY_MAX)
		return PROTO_E_BODYLEN;
	total = (size_t)PROTO_REQ_HDR + (size_t)rq->body_len;
	if (n < total)
		return PROTO_E_SHORT;

	memset(buf, 0, (size_t)PROTO_REQ_HDR);
	proto_put_be32(buf + PROTO_RQ_O_MAGIC, PROTO_REQ_MAGIC);
	buf[PROTO_RQ_O_VERSION] = PROTO_VERSION;
	buf[PROTO_RQ_O_OP] = rq->op;
	proto_put_be16(buf + PROTO_RQ_O_FLAGS, 0);
	memcpy(buf + PROTO_RQ_O_SESSION, rq->session, PROTO_TOK_LEN);
	memcpy(buf + PROTO_RQ_O_CSRF,    rq->csrf,    PROTO_TOK_LEN);
	proto_put_be32(buf + PROTO_RQ_O_CLIENTIP, rq->client_ip);
	proto_put_be32(buf + PROTO_RQ_O_BODYLEN, rq->body_len);
	if (rq->body_len != 0)
		memcpy(buf + PROTO_REQ_HDR, rq->body, (size_t)rq->body_len);
	return (int)total;
}

int proto_encode_resp(const struct proto_resp *rs, uint8_t *buf, size_t n)
{
	size_t total;

	if (rs == 0 || buf == 0)
		return PROTO_E_INVAL;
	if (rs->body_len > PROTO_RESP_BODY_MAX)
		return PROTO_E_BODYLEN;
	total = (size_t)PROTO_RESP_HDR + (size_t)rs->body_len;
	if (n < total)
		return PROTO_E_SHORT;

	proto_put_be32(buf + PROTO_RS_O_MAGIC, PROTO_RESP_MAGIC);
	buf[PROTO_RS_O_VERSION] = PROTO_VERSION;
	buf[PROTO_RS_O_STATUS] = rs->status;
	proto_put_be16(buf + PROTO_RS_O_RESERVED, 0);
	proto_put_be32(buf + PROTO_RS_O_BODYLEN, rs->body_len);
	if (rs->body_len != 0)
		memcpy(buf + PROTO_RESP_HDR, rs->body, (size_t)rs->body_len);
	return (int)total;
}

int proto_decode_resp(const uint8_t *buf, size_t n, struct proto_resp *out)
{
	uint32_t blen;

	if (out == 0 || buf == 0)
		return PROTO_E_INVAL;
	if (n < PROTO_RESP_HDR)
		return PROTO_E_SHORT;
	if (proto_be32(buf + PROTO_RS_O_MAGIC) != PROTO_RESP_MAGIC)
		return PROTO_E_MAGIC;
	if (buf[PROTO_RS_O_VERSION] != PROTO_VERSION)
		return PROTO_E_VERSION;
	if (proto_be16(buf + PROTO_RS_O_RESERVED) != 0)
		return PROTO_E_RESERVED;
	blen = proto_be32(buf + PROTO_RS_O_BODYLEN);
	if (blen > PROTO_RESP_BODY_MAX)
		return PROTO_E_BODYLEN;
	if (n < (size_t)PROTO_RESP_HDR + (size_t)blen)
		return PROTO_E_SHORT;

	memset(out, 0, sizeof(*out));
	out->version = buf[PROTO_RS_O_VERSION];
	out->status = buf[PROTO_RS_O_STATUS];
	out->reserved = 0;
	out->body_len = blen;
	if (blen != 0)
		memcpy(out->body, buf + PROTO_RESP_HDR, (size_t)blen);
	return (int)((size_t)PROTO_RESP_HDR + (size_t)blen);
}

/* ------------------------------------------------------------ TLV helpers */

int proto_tlv_put(uint8_t *buf, size_t cap, size_t *off,
                  uint16_t type, const uint8_t *val, uint16_t len)
{
	size_t o;

	if (buf == 0 || off == 0 || (val == 0 && len != 0))
		return -1;
	o = *off;
	if (o > cap || cap - o < (size_t)4 + (size_t)len)
		return -1;
	proto_put_be16(buf + o, type);
	proto_put_be16(buf + o + 2, len);
	if (len != 0)
		memcpy(buf + o + 4, val, (size_t)len);
	*off = o + 4 + (size_t)len;
	return 0;
}

int proto_tlv_put_u8(uint8_t *buf, size_t cap, size_t *off, uint16_t type, uint8_t v)
{
	return proto_tlv_put(buf, cap, off, type, &v, 1);
}

int proto_tlv_put_u32(uint8_t *buf, size_t cap, size_t *off, uint16_t type, uint32_t v)
{
	uint8_t b[4];

	proto_put_be32(b, v);
	return proto_tlv_put(buf, cap, off, type, b, 4);
}

int proto_tlv_get(const uint8_t *buf, size_t n, size_t *off,
                  uint16_t *type, const uint8_t **val, uint16_t *len)
{
	size_t o;
	uint16_t l;

	if (buf == 0 || off == 0 || type == 0 || val == 0 || len == 0)
		return -1;
	o = *off;
	if (o > n || n - o < 4)
		return -1;
	*type = proto_be16(buf + o);
	l = proto_be16(buf + o + 2);
	if (n - o - 4 < (size_t)l)
		return -1;
	*val = buf + o + 4;
	*len = l;
	*off = o + 4 + (size_t)l;
	return 0;
}
