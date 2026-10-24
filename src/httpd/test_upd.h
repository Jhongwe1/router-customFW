/* src/httpd/test_upd.h -- brokerd's half of the three update ops, as a stand-in
 * that speaks src/lib/proto.h's wire format and nothing looser.
 *
 * It answers every update call test_serve.c and test_routes.c make, so it has to
 * be able to say no at each step, or the cases built on it could not fail.  It
 * refuses, the way notes/self-update.md § 4.2 says brokerd will: a DATA whose
 * offset is not the count it holds (and then stays poisoned until a new BEGIN),
 * a piece past the declared total, a DATA before BEGIN, an END over an
 * incomplete or poisoned staging, a body of the wrong length for its op, a total
 * over a slot, and -- when told to check them -- the wrong session or CSRF token
 * or client address.  On command it also refuses at BEGIN, at the k-th DATA and
 * at END, with a reason or without one, and answers OK bodies that are wrong.
 * test_serve.c's S-cases call it directly and show each refusal firing.
 *
 * It also stands in for bk_set_timeouts() and for alarm(2) (route_env.alarm_fn),
 * and writes every event into one log, in order: B D E for the three ops, T for
 * bk_set_timeouts(), A for an alarm armed and a for one read with alarm(0).  A
 * case asserts the whole sequence as one string.
 *
 * WHAT IT DOES NOT ESTABLISH.  That brokerd answers this way: this is written
 * from the pinned format, and brokerd's side is its own suite's.
 */
#ifndef RLXFW_HTTPD_TEST_UPD_H
#define RLXFW_HTTPD_TEST_UPD_H

#include "client.h"
#include "http.h"
#include "proto.h"

#include <errno.h>
#include <string.h>

#define UPD_LOG_MAX 1024
#define UPD_FNV0    2166136261u

static struct {
	/* ---- what it is told */
	uint8_t     begin_st;       /* ST_OK, or the status BEGIN refuses with */
	const char *begin_why;      /* that refusal's UPD_T_REASON; NULL = none */
	uint32_t    data_k;         /* the 1-based DATA call that refuses; 0 none */
	uint8_t     data_st;
	const char *data_why;
	uint8_t     end_st;
	const char *end_why;
	uint8_t     dest;           /* UPD_T_DEST in BEGIN OK and END OK */
	uint32_t    version;        /* UPD_T_VERSION in END OK */
	uint32_t    recv_skew;      /* added to UPD_T_RECEIVED: a broker that
				     * disagrees about the count */
	int         no_received;    /* DATA OK without UPD_T_RECEIVED */
	int         no_version;     /* END OK without UPD_T_VERSION */
	int         fail;           /* bk_call() itself fails on the update ops */
	int         check_tokens;   /* compare the three below on every call */
	uint8_t     sess[16];
	uint8_t     csrf[16];
	uint32_t    ip;
	unsigned    alarm_left;     /* the alarm as the stand-in keeps it */
	unsigned    alarm_elapsed;  /* seconds to pretend passed, at a read */
	/* ---- what it saw */
	int         calls;          /* update calls that reached it */
	int         oversize;       /* bodies bk_call() refuses before sending */
	int         nbegin, ndata, nend, nother;
	int         refused;        /* a refusal has been answered */
	int         after_refusal;  /* calls that came after one */
	uint32_t    total;          /* BEGIN's u32 */
	uint32_t    end_total;      /* END's u32 */
	uint32_t    received;
	int         active;         /* a staging exists */
	int         poisoned;
	int         bad_frame;      /* a body of the wrong length for its op */
	int         bad_offset;     /* DATA whose offset was not `received` */
	int         past_total;     /* DATA beyond BEGIN's total */
	int         short_mid;      /* a short piece that was not the last */
	uint32_t    last_len;       /* the latest accepted DATA's byte count */
	uint32_t    hash;           /* FNV-1a over the accepted bytes, in order */
	int         ntimeouts;
	int         to_connect, to_io;
	int         nalarm;
	unsigned    alarm_first;    /* the first non-zero value armed */
	char        log[UPD_LOG_MAX + 1];
} upd;

static inline void upd_reset(void)
{
	memset(&upd, 0, sizeof(upd));
	upd.begin_st = ST_OK;
	upd.data_st = ST_OK;
	upd.end_st = ST_OK;
	upd.dest = 'B';
	upd.version = 7;
	upd.hash = UPD_FNV0;
	upd.alarm_left = 20;        /* the child's own, 5 + 10 + 5 */
}

static inline uint32_t upd_fnv(uint32_t h, const uint8_t *p, size_t n)
{
	size_t i;

	for (i = 0; i < n; i++) {
		h ^= p[i];
		h *= 16777619u;
	}
	return h;
}

/* The body every case streams: byte i of it, from its index alone. */
static inline uint8_t upd_byte(uint32_t i)
{
	uint32_t x = i * 2654435761u;

	x ^= x >> 15;
	x *= 2246822519u;
	x ^= x >> 13;
	return (uint8_t)(x & 0xffu);
}

static inline uint32_t upd_hash_of(uint32_t n)
{
	uint32_t h = UPD_FNV0;
	uint32_t i;

	for (i = 0; i < n; i++) {
		uint8_t b = upd_byte(i);

		h = upd_fnv(h, &b, 1);
	}
	return h;
}

static inline void upd_log(char c)
{
	size_t l = strlen(upd.log);

	if (l < UPD_LOG_MAX) {
		upd.log[l] = c;
		upd.log[l + 1] = '\0';
	}
}

static inline int upd_hexval(int c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	return -1;
}

/* The tokens a case's request carries, as the bytes a call must hold. */
static inline void upd_expect(const char *sess_hex, const char *csrf_hex,
			      uint32_t ip)
{
	int i;

	for (i = 0; i < 16; i++) {
		upd.sess[i] = (uint8_t)((upd_hexval(sess_hex[2 * i]) << 4) |
					upd_hexval(sess_hex[2 * i + 1]));
		upd.csrf[i] = (uint8_t)((upd_hexval(csrf_hex[2 * i]) << 4) |
					upd_hexval(csrf_hex[2 * i + 1]));
	}
	upd.ip = ip;
	upd.check_tokens = 1;
}

static inline int upd_no(struct bk_resp *rs, uint8_t st, const char *why)
{
	size_t off = 0;

	memset(rs, 0, sizeof(*rs));
	rs->status = st;
	if (why != NULL)
		(void)proto_tlv_put(rs->body, sizeof(rs->body), &off,
				    UPD_T_REASON, (const uint8_t *)why,
				    (uint16_t)strlen(why));
	rs->body_len = (uint32_t)off;
	upd.refused = 1;
	return 0;
}

static inline int upd_begin(const struct bk_req *rq, struct bk_resp *rs)
{
	size_t off = 0;

	if (rq->body_len != 4) {
		upd.bad_frame++;
		return upd_no(rs, ST_INVAL, "badlen");
	}
	upd.total = proto_be32(rq->body);
	if (upd.begin_st != ST_OK)
		return upd_no(rs, upd.begin_st, upd.begin_why);
	if (upd.total > HTTP_UPLOAD_MAX)
		return upd_no(rs, ST_INVAL, "too_big");
	upd.active = 1;
	upd.poisoned = 0;
	upd.received = 0;
	upd.last_len = 0;
	upd.hash = UPD_FNV0;
	rs->status = ST_OK;
	(void)proto_tlv_put_u8(rs->body, sizeof(rs->body), &off, UPD_T_DEST,
			       upd.dest);
	rs->body_len = (uint32_t)off;
	return 0;
}

static inline int upd_data(const struct bk_req *rq, struct bk_resp *rs)
{
	size_t off = 0;
	uint32_t o, n;

	if (rq->body_len < 5) {
		upd.bad_frame++;
		return upd_no(rs, ST_INVAL, "badlen");
	}
	o = proto_be32(rq->body);
	n = rq->body_len - 4;
	if (!upd.active || upd.poisoned)
		return upd_no(rs, ST_INVAL, "sequence");
	if (o != upd.received) {
		upd.bad_offset++;
		upd.poisoned = 1;
		return upd_no(rs, ST_INVAL, "sequence");
	}
	if (n > upd.total - upd.received) {
		upd.past_total++;
		upd.poisoned = 1;
		return upd_no(rs, ST_INVAL, "sequence");
	}
	if ((uint32_t)upd.ndata == upd.data_k)
		return upd_no(rs, upd.data_st, upd.data_why);
	if (upd.last_len != 0 && upd.last_len != UPD_DATA_MAX)
		upd.short_mid++;
	upd.last_len = n;
	upd.hash = upd_fnv(upd.hash, rq->body + 4, n);
	upd.received += n;
	rs->status = ST_OK;
	if (!upd.no_received)
		(void)proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
					UPD_T_RECEIVED,
					upd.received + upd.recv_skew);
	rs->body_len = (uint32_t)off;
	return 0;
}

static inline int upd_end(const struct bk_req *rq, struct bk_resp *rs)
{
	size_t off = 0;

	if (rq->body_len != 4) {
		upd.bad_frame++;
		return upd_no(rs, ST_INVAL, "badlen");
	}
	upd.end_total = proto_be32(rq->body);
	if (!upd.active || upd.poisoned)
		return upd_no(rs, ST_INVAL, "sequence");
	if (upd.end_total != upd.total || upd.received != upd.total)
		return upd_no(rs, ST_INVAL, "incomplete");
	upd.active = 0;
	if (upd.end_st != ST_OK)
		return upd_no(rs, upd.end_st, upd.end_why);
	rs->status = ST_OK;
	(void)proto_tlv_put_u8(rs->body, sizeof(rs->body), &off, UPD_T_DEST,
			       upd.dest);
	if (!upd.no_version)
		(void)proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
					UPD_T_VERSION, upd.version);
	rs->body_len = (uint32_t)off;
	return 0;
}

/* The update ops' half of bk_call(), with bk_call()'s own first refusal. */
static inline int upd_call(const struct bk_req *rq, struct bk_resp *rs)
{
	if (rq->body_len > PROTO_REQ_BODY_MAX) {
		upd.oversize++;
		return -EMSGSIZE;
	}
	if (rq->body_len != 0 && rq->body == NULL)
		return -EINVAL;
	upd.calls++;
	if (upd.refused)
		upd.after_refusal++;
	switch (rq->op) {
	case OP_UPDATE_BEGIN:
		upd.nbegin++;
		upd_log('B');
		break;
	case OP_UPDATE_DATA:
		upd.ndata++;
		upd_log('D');
		break;
	case OP_UPDATE_END:
		upd.nend++;
		upd_log('E');
		break;
	default:
		upd.nother++;
		upd_log('?');
		return upd_no(rs, ST_NOTSUP, NULL);
	}
	if (upd.fail)
		return -ECONNREFUSED;
	if (upd.check_tokens) {
		/* brokerd's gate: no session is AUTH, a CSRF mismatch PERM,
		 * and neither carries a reason (src/brokerd/ops.c bk_dispatch) */
		if (memcmp(rq->session, upd.sess, 16) != 0 || rq->client_ip != upd.ip)
			return upd_no(rs, ST_AUTH, NULL);
		if (memcmp(rq->csrf, upd.csrf, 16) != 0)
			return upd_no(rs, ST_PERM, NULL);
	}
	if (rq->op == OP_UPDATE_BEGIN)
		return upd_begin(rq, rs);
	if (rq->op == OP_UPDATE_DATA)
		return upd_data(rq, rs);
	return upd_end(rq, rs);
}

/* client.c's, replaced: every including program links no client.c. */
void bk_set_timeouts(int connect_s, int io_s)
{
	upd.ntimeouts++;
	upd.to_connect = connect_s;
	upd.to_io = io_s;
	upd_log('T');
}

/* alarm(2), as route_env.alarm_fn: returns what was left, arms `secs`.  A read
 * (secs 0) first pretends alarm_elapsed seconds passed. */
static inline unsigned upd_alarm(unsigned secs)
{
	unsigned prev = upd.alarm_left;

	if (secs == 0) {
		prev = (prev > upd.alarm_elapsed) ? prev - upd.alarm_elapsed : 0;
		upd_log('a');
	} else {
		if (upd.alarm_first == 0)
			upd.alarm_first = secs;
		upd_log('A');
	}
	upd.nalarm++;
	upd.alarm_left = secs;
	return prev;
}

/* The log a whole accepted upload of n bytes writes. */
static inline void upd_want_log(char *out, size_t cap, uint32_t n)
{
	uint32_t k = (n + UPD_DATA_MAX - 1) / UPD_DATA_MAX;
	size_t o = 0;
	uint32_t i;

	if (cap < (size_t)k + 8) {
		out[0] = '\0';
		return;
	}
	out[o++] = 'B';
	out[o++] = 'A';
	for (i = 0; i < k; i++)
		out[o++] = 'D';
	out[o++] = 'a';
	out[o++] = 'A';
	out[o++] = 'T';
	out[o++] = 'E';
	out[o] = '\0';
}

#endif /* RLXFW_HTTPD_TEST_UPD_H */
