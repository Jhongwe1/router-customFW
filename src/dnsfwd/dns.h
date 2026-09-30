/* dns.h -- dnsfwd's wire codec, forwarding policy and in-flight table.
 *
 * ---------------------------------------------------------------------------
 * WHY THIS FILE EXISTS
 * ---------------------------------------------------------------------------
 *
 * The vendor's DNS forwarder is `dnsmasq`, and 讀 SPEC.md FW-20 it imports
 * `popen`.  R7's pass condition is `system()`/`popen()` count = 0 over the
 * shipped rootfs, so shipping dnsmasq would fail the gate by itself.  The
 * plan's ruling (plan § R7f item 3) is to write the forwarder: UDP only,
 * forward only, a bounded parser, refuses recursion.
 *
 * Everything here is pure: no syscall, no global, no allocation, no recursion,
 * no VLA.  The I/O the daemon needs is a vtable (`struct dns_io`) the caller
 * fills in, so the host tests drive the whole forwarder without opening a
 * socket -- the bench owns the interfaces and the tests must not touch them.
 *
 * Both directions are hostile input.  A LAN client's query is obviously
 * attacker-controlled; an upstream's reply is too, because an off-path
 * attacker can race it (that is the Kaminsky attack), and the upstream itself
 * is not trusted to be well-formed.  So `dns_parse_query` and
 * `dns_parse_reply` are the same kind of function with the same guards, and
 * both are fuzz targets (src/fuzz/fuzz_dns.c).
 */

#ifndef DNSFWD_DNS_H
#define DNSFWD_DNS_H

#include <stddef.h>
#include <stdint.h>

/* ------------------------------------------------------------------------ */
/* Bounds.  Every one of these is a hard cap, never a hint.                 */
/* ------------------------------------------------------------------------ */

#define DNS_MSG_MAX      512   /* RFC 1035 s 2.3.4: UDP payload without EDNS0 */
#define DNS_NAME_MAX     255   /* RFC 1035 s 2.3.4: whole encoded name        */
#define DNS_LABEL_MAX     63   /* RFC 1035 s 2.3.4: one label                 */
#define DNS_HDR_LEN       12
#define DNS_PTR_JUMPS_MAX 64   /* third, redundant guard; see dns_decode_name */
#define DNS_RR_WALK_MAX   45   /* (512 - 12 - 5) / 11, the most RRs that fit  */
#define DNS_RR_KEEP       16   /* answer RRs described to the caller          */

#define DNS_PORT          53
#define DNS_CLASS_IN       1
#define DNS_TYPE_A         1
#define DNS_TYPE_CNAME     5
#define DNS_TYPE_AAAA     28
#define DNS_TYPE_OPT      41   /* EDNS0; refused, see notes/dnsfwd.md         */

/* RCODEs we ever emit ourselves. */
#define DNS_RCODE_NOERROR  0
#define DNS_RCODE_FORMERR  1
#define DNS_RCODE_SERVFAIL 2
#define DNS_RCODE_NXDOMAIN 3
#define DNS_RCODE_NOTIMP   4
#define DNS_RCODE_REFUSED  5

/* Header flag bits, host order, as decoded by dns_get16. */
#define DNS_F_QR     0x8000u
#define DNS_F_OPMASK 0x7800u
#define DNS_F_AA     0x0400u
#define DNS_F_TC     0x0200u
#define DNS_F_RD     0x0100u
#define DNS_F_RA     0x0080u
#define DNS_F_Z      0x0040u
#define DNS_F_RCMASK 0x000Fu

/* ------------------------------------------------------------------------ */
/* Errors.  Returned negated: a function returns 0 or -DNSE_*.              */
/* ------------------------------------------------------------------------ */
enum dns_err {
	DNSE_SHORT = 1,  /* fewer bytes left than the structure needs        */
	DNSE_LABEL,      /* a length byte that is neither 0, 1..63 nor 0xC0+ */
	DNSE_PTR,        /* a compression pointer that does not go backwards */
	DNSE_NAME,       /* the decoded name would exceed 255 bytes          */
	DNSE_JUMPS,      /* more than DNS_PTR_JUMPS_MAX pointers followed    */
	DNSE_QDCOUNT,    /* QDCOUNT is not exactly 1                         */
	DNSE_OPCODE,     /* OPCODE is not QUERY                              */
	DNSE_QR,         /* the QR bit is wrong for this direction           */
	DNSE_RD,         /* RD = 0: an iterative query, which we cannot do   */
	DNSE_EDNS,       /* an OPT record is present                         */
	DNSE_CLASS,      /* QCLASS is not IN                                 */
	DNSE_TRAIL,      /* bytes after the last record                      */
	DNSE_RRCOUNT,    /* the counts claim more RRs than 512 bytes hold    */
	DNSE_CAP,        /* the output buffer is too small                   */
	DNSE_Z,          /* a reserved header bit is set                     */
	DNSE_LONG        /* more than 512 bytes: not a message we accept     */
};
const char *dns_strerr(int e);

/* ------------------------------------------------------------------------ */
/* Decoded shapes.  Nothing here is ever memcpy'd off the wire.             */
/* ------------------------------------------------------------------------ */

struct dns_hdr {
	uint16_t id, flags, qd, an, ns, ar;
};

/* `name` holds the name in UNCOMPRESSED wire form -- length-prefixed labels
 * ending in a single 0 byte -- so nlen counts that terminator and is 1 for
 * the root.  Storing the decoded form, never the on-wire bytes, is what keeps
 * an attacker's compression pointers out of anything we re-emit. */
struct dns_question {
	uint8_t  name[DNS_NAME_MAX];
	uint8_t  nlen;
	uint16_t qtype, qclass;
};

struct dns_rr {
	uint8_t  name[DNS_NAME_MAX];
	uint8_t  nlen;
	uint16_t type, rclass;
	uint32_t ttl;
	uint16_t rdlen;
	uint16_t rdoff;          /* offset of rdata inside the message */
};

struct dns_reply {
	struct dns_hdr      h;
	struct dns_question q;
	struct dns_rr       an[DNS_RR_KEEP];
	uint16_t            n_an;      /* answer RRs described below           */
	uint16_t            n_walked;  /* every RR bounds-checked, all sections */
};

/* `have_q` says whether `q` was filled.  It matters on the error path: a
 * failure found in the 12-byte header leaves no question we are willing to
 * echo, so the error reply carries QDCOUNT 0; a failure found after the
 * question decoded (RD = 0, a class we do not serve, an OPT record) can echo
 * it, which is what a stub resolver wants to see. */
struct dns_query {
	struct dns_hdr      h;
	struct dns_question q;
	int                 have_q;
};

/* ------------------------------------------------------------------------ */
/* Codec                                                                    */
/* ------------------------------------------------------------------------ */

/* Explicit shifts, never a cast of a pointer to uint16_t*: the target is
 * big-endian and the host is little-endian, and MIPS-I faults on an unaligned
 * halfword load. */
uint16_t dns_get16(const uint8_t *p);
uint32_t dns_get32(const uint8_t *p);
void     dns_put16(uint8_t *p, uint16_t v);
void     dns_put32(uint8_t *p, uint32_t v);

/* Decode the name at `pos`.  `*next` is set to the offset just past the name
 * AS IT APPEARS AT `pos` (a compression pointer is two bytes there, whatever
 * it expands to), which is what a caller must use to keep walking.
 *
 * The termination argument, because this is where the classic infinite loop
 * lives -- three independent guards, any one of which suffices:
 *   1. a pointer's target must be strictly less than the offset of the
 *      pointer's own first byte;
 *   2. every target must be strictly less than the previous target (the
 *      sequence of targets strictly decreases, so it cannot revisit);
 *   3. at most DNS_PTR_JUMPS_MAX pointers are followed.
 * Guard 1 alone is NOT sufficient and that is not obvious: targets 20, 25, 30
 * each below their own pointer's offset can still form a cycle.  Guard 2 is
 * the one that makes termination provable; guard 3 is there because a proof
 * that depends on reading this comment correctly is not a guard. */
int dns_decode_name(const uint8_t *msg, size_t n, size_t pos,
                    uint8_t *out, size_t outcap, uint8_t *outlen, size_t *next);

/* Case-insensitive (ASCII) comparison of two uncompressed wire-form names. */
int dns_name_eq(const uint8_t *a, uint8_t alen, const uint8_t *b, uint8_t blen);

int dns_parse_query(const uint8_t *msg, size_t n, struct dns_query *out);
int dns_parse_reply(const uint8_t *msg, size_t n, struct dns_reply *out);

/* Encode a fresh query for `q` with id `id`.  Returns bytes written. */
int dns_encode_query(const struct dns_question *q, uint16_t id, int rd,
                     uint8_t *out, size_t cap);

/* A header-and-question-only reply with `rcode`.  `q` may be NULL, in which
 * case QDCOUNT is 0 -- used when the query did not parse far enough to have a
 * question we are willing to echo. */
int dns_encode_error(uint16_t id, const struct dns_question *q, uint8_t rcode,
                     uint8_t *out, size_t cap);

/* ------------------------------------------------------------------------ */
/* Forwarding policy                                                        */
/* ------------------------------------------------------------------------ */

/* 1 if `src` may ask us at all: inside the LAN prefix, and neither the
 * network nor the broadcast address of it, and not 0.0.0.0.  All arguments in
 * host order.  An open forwarder is a reflection/amplification weapon, so the
 * default is no. */
int dns_on_lan(uint32_t src, uint32_t lan_ip, uint32_t lan_mask);

#define DNS_INFLIGHT_MAX   64
#define DNS_TIMEOUT_MS   4000
#define DNS_RATE_SLOTS     32
#define DNS_RATE_CAP_M  40000   /* 40 queries of burst, in milli-tokens */
#define DNS_RATE_FILL_M    20   /* milli-tokens per ms = 20 queries/s   */
#define DNS_RATE_COST_M  1000

struct dns_inflight {
	int      used;
	uint32_t caddr;              /* client address, host order   */
	uint16_t cport;              /* client port, host order      */
	uint16_t cid;                /* the client's own query ID    */
	uint16_t uid;                /* the random ID we sent out    */
	uint32_t t_ms;               /* monotonic ms at send time    */
	struct dns_question q;
};

struct dns_table {
	struct dns_inflight e[DNS_INFLIGHT_MAX];
	unsigned n_used;
};

void dns_table_init(struct dns_table *t);
/* index, or -1 when full.  A full table drops the new query; it never grows. */
int  dns_table_add(struct dns_table *t, uint32_t caddr, uint16_t cport,
                   uint16_t cid, uint16_t uid, const struct dns_question *q,
                   uint32_t now_ms);
/* The Kaminsky check, minus the address/port half the caller holds: an entry
 * matches only if the upstream ID AND the whole question section agree. */
int  dns_table_match(const struct dns_table *t, uint16_t uid,
                     const struct dns_question *q);
/* 1 if some entry already went out with this upstream ID.  The caller redraws
 * rather than let two in-flight queries share an ID, which would make a reply
 * ambiguous between them. */
int  dns_table_uid_used(const struct dns_table *t, uint16_t uid);
void dns_table_free(struct dns_table *t, int i);
/* Fills `out` with the indices that timed out; returns how many. */
int  dns_table_expire(struct dns_table *t, uint32_t now_ms,
                      int *out, int outcap);

struct dns_rate {
	struct {
		int      used;
		uint32_t addr;
		int32_t  tok_m;
		uint32_t t_ms;
	} s[DNS_RATE_SLOTS];
};
void dns_rate_init(struct dns_rate *r);
int  dns_rate_allow(struct dns_rate *r, uint32_t addr, uint32_t now_ms);

/* ------------------------------------------------------------------------ */
/* The forwarder, over an injectable I/O layer                              */
/* ------------------------------------------------------------------------ */

#define DNS_SOCK_CLIENT   0
#define DNS_SOCK_UPSTREAM 1

struct dns_io {
	/* >= 0 bytes sent, or -errno.  Addresses and ports are host order. */
	int (*send)(void *ctx, int which, const uint8_t *buf, size_t n,
	            uint32_t addr, uint16_t port);
	int (*rand16)(void *ctx, uint16_t *out);      /* 0, or -errno */
	uint32_t (*now_ms)(void *ctx);
	void (*logline)(void *ctx, const char *msg);
	void *ctx;
};

struct dns_stats {
	unsigned q_in, q_fwd, r_in, r_out;
	unsigned d_offlan, d_rate, d_parse, d_full, d_spoof, d_rand;
	unsigned e_formerr, e_refused, e_notimp, e_servfail;
	unsigned t_expired;
};

struct dnsfwd {
	struct dns_io    io;
	uint32_t         lan_ip, lan_mask, upstream;   /* host order */
	uint16_t         upstream_port;
	struct dns_table tbl;
	struct dns_rate  rate;
	struct dns_stats st;
};

void dnsfwd_init(struct dnsfwd *d, const struct dns_io *io);
void dnsfwd_config(struct dnsfwd *d, uint32_t lan_ip, uint32_t lan_mask,
                   uint32_t upstream);

/* A datagram arrived on :53.  Returns 0 when it was forwarded, or -DNSE_* /
 * a small negative policy code when it was answered or dropped.  Never
 * anything but bounded work. */
#define DNSFWD_DROPPED (-100)
int dnsfwd_on_client(struct dnsfwd *d, const uint8_t *buf, size_t n,
                     uint32_t src, uint16_t sport);
/* A datagram arrived on the upstream socket. */
int dnsfwd_on_upstream(struct dnsfwd *d, const uint8_t *buf, size_t n,
                       uint32_t src, uint16_t sport);
/* SERVFAIL every in-flight query older than DNS_TIMEOUT_MS. */
int dnsfwd_tick(struct dnsfwd *d);

#endif /* DNSFWD_DNS_H */
