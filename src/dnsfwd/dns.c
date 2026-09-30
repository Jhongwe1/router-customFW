/* dns.c -- dnsfwd's parser, encoder, in-flight table and forwarding policy.
 *
 * No syscall, no global, no allocation, no recursion, no VLA, no alloca.
 * Every integer on the wire is decoded with explicit shifts: the target is
 * big-endian, the host that runs the tests is little-endian, and MIPS-I
 * faults on an unaligned halfword load, so a cast to `uint16_t *` would be
 * wrong twice over.
 *
 * Two build-time mutations exist so that the test suite can show its own
 * controls failing.  They are named, they are not dates or patterns, and
 * `make host`/`make target` REFUSE if either is defined (see the Makefile):
 *
 *   DNSFWD_MUT_NO_PTR_GUARD  removes the three compression-pointer
 *                            termination guards.  test_dns's self-pointer
 *                            case must then hang -- the classic bug.
 *   DNSFWD_MUT_NO_QMATCH     removes the question half of the Kaminsky check.
 *                            The "right ID, different question" anti-spoof
 *                            case must then go red.
 */

#include "dns.h"

#include <string.h>

/* ------------------------------------------------------------------------ */
/* Scalars                                                                  */
/* ------------------------------------------------------------------------ */

uint16_t dns_get16(const uint8_t *p)
{
	return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

uint32_t dns_get32(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
	       ((uint32_t)p[2] << 8)  | (uint32_t)p[3];
}

void dns_put16(uint8_t *p, uint16_t v)
{
	p[0] = (uint8_t)(v >> 8);
	p[1] = (uint8_t)(v & 0xFF);
}

void dns_put32(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)(v >> 24);
	p[1] = (uint8_t)(v >> 16);
	p[2] = (uint8_t)(v >> 8);
	p[3] = (uint8_t)(v & 0xFF);
}

const char *dns_strerr(int e)
{
	switch (e < 0 ? -e : e) {
	case 0:            return "ok";
	case DNSE_SHORT:   return "truncated";
	case DNSE_LABEL:   return "bad label length byte";
	case DNSE_PTR:     return "compression pointer not backwards";
	case DNSE_NAME:    return "name over 255 bytes";
	case DNSE_JUMPS:   return "too many compression pointers";
	case DNSE_QDCOUNT: return "QDCOUNT is not 1";
	case DNSE_OPCODE:  return "opcode is not QUERY";
	case DNSE_QR:      return "QR bit wrong for this direction";
	case DNSE_RD:      return "RD is 0: iterative query";
	case DNSE_EDNS:    return "OPT record present (no EDNS0)";
	case DNSE_CLASS:   return "QCLASS is not IN";
	case DNSE_TRAIL:   return "trailing bytes";
	case DNSE_RRCOUNT: return "more RRs than 512 bytes hold";
	case DNSE_CAP:     return "output buffer too small";
	case DNSE_Z:       return "reserved header bit set";
	case DNSE_LONG:    return "over 512 bytes";
	default:           return "unknown";
	}
}

/* ------------------------------------------------------------------------ */
/* Names                                                                    */
/* ------------------------------------------------------------------------ */

int dns_decode_name(const uint8_t *msg, size_t n, size_t pos,
                    uint8_t *out, size_t outcap, uint8_t *outlen, size_t *next)
{
	size_t limit  = n;   /* guard 2: every pointer target must be below this */
	size_t jumps  = 0;   /* guard 3                                          */
	size_t o      = 0;
	size_t after  = 0;
	int    followed = 0;

	if (out == 0 || outlen == 0 || next == 0) return -DNSE_CAP;
	if (outcap < 1 || outcap > DNS_NAME_MAX)  return -DNSE_CAP;

	for (;;) {
		uint8_t c;

		if (pos >= n) return -DNSE_SHORT;
		c = msg[pos];

		if ((c & 0xC0) == 0xC0) {
			size_t tgt;

			if (pos + 2 > n) return -DNSE_SHORT;
			tgt = ((size_t)(c & 0x3F) << 8) | (size_t)msg[pos + 1];
			if (!followed) {
				after    = pos + 2;
				followed = 1;
			}
#ifndef DNSFWD_MUT_NO_PTR_GUARD
			/* Guard 1: strictly backwards from the pointer itself.  NOT
			 * sufficient on its own: targets 20, 25, 30 can each be below
			 * their own pointer's offset and still form a cycle. */
			if (tgt >= pos)   return -DNSE_PTR;
			/* Guard 2: the sequence of targets strictly decreases, so no
			 * target can be visited twice.  This is the one that makes
			 * termination a proof rather than a hope. */
			if (tgt >= limit) return -DNSE_PTR;
			limit = tgt;
			/* Guard 3: a bound that holds even if the reasoning above is
			 * wrong. */
			if (++jumps > DNS_PTR_JUMPS_MAX) return -DNSE_JUMPS;
#else
			(void)limit;
			(void)jumps;
#endif
			pos = tgt;
			continue;
		}

		/* 0x40 and 0x80 in the top two bits are reserved by RFC 1035 s 4.1.4
		 * and have never been assigned.  Refuse them: this is the "offset
		 * with the top bits wrong" case. */
		if ((c & 0xC0) != 0x00) return -DNSE_LABEL;

		if (c == 0) {
			if (o + 1 > outcap) return -DNSE_NAME;
			out[o++] = 0;
			if (!followed) after = pos + 1;
			*outlen = (uint8_t)o;
			*next   = after;
			return 0;
		}

		/* c is 1..63 here by the encoding: (c & 0xC0) == 0 means c <= 0x3F,
		 * and 0x3F is DNS_LABEL_MAX.  The 63-byte label cap is therefore
		 * enforced by the two tests above and not by a third one that could
		 * never fire. */
		if (pos + 1 + (size_t)c > n) return -DNSE_SHORT;
		/* One byte of outcap is reserved for the terminating root label, so
		 * the 255-byte total includes it.  This is the cap that a name made
		 * of legal 63-byte labels runs into. */
		if (o + 1 + (size_t)c + 1 > outcap) return -DNSE_NAME;

		out[o++] = c;
		memcpy(out + o, msg + pos + 1, (size_t)c);
		o   += (size_t)c;
		pos += 1 + (size_t)c;
	}
}

static uint8_t lc(uint8_t c)
{
	return (uint8_t)((c >= 'A' && c <= 'Z') ? (c - 'A' + 'a') : c);
}

int dns_name_eq(const uint8_t *a, uint8_t alen, const uint8_t *b, uint8_t blen)
{
	size_t i = 0;

	if (alen != blen || alen == 0) return 0;
	/* Walk label by label so that a length byte is only ever compared with a
	 * length byte: lowercasing a length byte could otherwise make 65 and 97
	 * compare equal. */
	for (;;) {
		uint8_t la, lb;
		size_t  k;

		if (i >= alen) return 0;              /* no root label: malformed */
		la = a[i];
		lb = b[i];
		if (la != lb) return 0;
		if (la == 0)  return (size_t)(i + 1) == (size_t)alen;
		if (i + 1 + (size_t)la > alen) return 0;
		for (k = 0; k < (size_t)la; k++)
			if (lc(a[i + 1 + k]) != lc(b[i + 1 + k])) return 0;
		i += 1 + (size_t)la;
	}
}

/* ------------------------------------------------------------------------ */
/* Messages                                                                 */
/* ------------------------------------------------------------------------ */

static void hdr_decode(const uint8_t *msg, struct dns_hdr *h)
{
	h->id    = dns_get16(msg + 0);
	h->flags = dns_get16(msg + 2);
	h->qd    = dns_get16(msg + 4);
	h->an    = dns_get16(msg + 6);
	h->ns    = dns_get16(msg + 8);
	h->ar    = dns_get16(msg + 10);
}

static int question_decode(const uint8_t *msg, size_t n, size_t pos,
                           struct dns_question *q, size_t *next)
{
	int rc = dns_decode_name(msg, n, pos, q->name, sizeof q->name,
	                         &q->nlen, &pos);
	if (rc != 0) return rc;
	if (pos + 4 > n) return -DNSE_SHORT;
	q->qtype  = dns_get16(msg + pos);
	q->qclass = dns_get16(msg + pos + 2);
	*next = pos + 4;
	return 0;
}

int dns_parse_query(const uint8_t *msg, size_t n, struct dns_query *out)
{
	size_t pos;
	int    rc;

	memset(out, 0, sizeof *out);
	if (n < DNS_HDR_LEN)  return -DNSE_SHORT;
	if (n > DNS_MSG_MAX)  return -DNSE_LONG;
	hdr_decode(msg, &out->h);

	/* Header-level refusals first: none of them leaves a question we would
	 * echo back. */
	if (out->h.flags & DNS_F_QR)     return -DNSE_QR;
	if (out->h.flags & DNS_F_OPMASK) return -DNSE_OPCODE;
	if (out->h.qd != 1)              return -DNSE_QDCOUNT;
	if (out->h.an != 0 || out->h.ns != 0) return -DNSE_RRCOUNT;

	rc = question_decode(msg, n, DNS_HDR_LEN, &out->q, &pos);
	if (rc != 0) return rc;
	out->have_q = 1;

	if (out->q.qclass != DNS_CLASS_IN) return -DNSE_CLASS;
	/* Forward only.  RD = 0 asks for an iterative answer, which means "tell
	 * me who to ask next".  dnsfwd cannot iterate and must never pretend to,
	 * so it refuses instead of silently recursing on the client's behalf. */
	if (!(out->h.flags & DNS_F_RD))   return -DNSE_RD;
	/* Any additional record in a query is an OPT (EDNS0) or a TSIG.  R7 has
	 * no EDNS0: forwarding an OPT we do not parse would be a lie about our
	 * own buffer size, and stripping it would break the client's DO bit. */
	if (out->h.ar != 0)               return -DNSE_EDNS;
	if (pos != n)                     return -DNSE_TRAIL;
	return 0;
}

int dns_parse_reply(const uint8_t *msg, size_t n, struct dns_reply *out)
{
	size_t   pos;
	uint32_t total, i;
	int      rc;

	memset(out, 0, sizeof *out);
	if (n < DNS_HDR_LEN) return -DNSE_SHORT;
	if (n > DNS_MSG_MAX) return -DNSE_LONG;
	hdr_decode(msg, &out->h);

	if (!(out->h.flags & DNS_F_QR))   return -DNSE_QR;
	if (out->h.flags & DNS_F_OPMASK)  return -DNSE_OPCODE;
	if (out->h.flags & DNS_F_Z)       return -DNSE_Z;
	if (out->h.qd != 1)               return -DNSE_QDCOUNT;

	/* An RR is at least 11 bytes (a root name plus the 10 fixed bytes), so a
	 * 512-byte message cannot hold more than DNS_RR_WALK_MAX of them.  Refuse
	 * a header that claims 65,535 before walking anything: the walk would
	 * fail on the first short read anyway, but the bound keeps the work
	 * proportional to the bytes received. */
	total = (uint32_t)out->h.an + out->h.ns + out->h.ar;
	if (total > DNS_RR_WALK_MAX) return -DNSE_RRCOUNT;

	rc = question_decode(msg, n, DNS_HDR_LEN, &out->q, &pos);
	if (rc != 0) return rc;

	for (i = 0; i < total; i++) {
		uint8_t  nm[DNS_NAME_MAX];
		uint8_t  nl = 0;
		uint16_t type, rclass, rdlen;
		uint32_t ttl;

		rc = dns_decode_name(msg, n, pos, nm, sizeof nm, &nl, &pos);
		if (rc != 0) return rc;
		if (pos + 10 > n) return -DNSE_SHORT;
		type   = dns_get16(msg + pos);
		rclass = dns_get16(msg + pos + 2);
		ttl    = dns_get32(msg + pos + 4);
		rdlen  = dns_get16(msg + pos + 8);
		pos   += 10;
		if (pos + (size_t)rdlen > n) return -DNSE_SHORT;

		/* No EDNS0 in R7, in either direction.  An upstream that answers
		 * with an OPT record when we did not send one is broken, and we do
		 * not relay bytes whose meaning we decline to implement. */
		if (type == DNS_TYPE_OPT) return -DNSE_EDNS;

		if (i < out->h.an && out->n_an < DNS_RR_KEEP) {
			struct dns_rr *r = &out->an[out->n_an++];
			memcpy(r->name, nm, sizeof r->name);
			r->nlen   = nl;
			r->type   = type;
			r->rclass = rclass;
			r->ttl    = ttl;
			r->rdlen  = rdlen;
			r->rdoff  = (uint16_t)pos;
		}
		pos += (size_t)rdlen;
	}
	if (pos != n) return -DNSE_TRAIL;
	out->n_walked = (uint16_t)total;
	return 0;
}

int dns_encode_query(const struct dns_question *q, uint16_t id, int rd,
                     uint8_t *out, size_t cap)
{
	size_t need = (size_t)DNS_HDR_LEN + q->nlen + 4;

	/* nlen is uint8_t, so DNS_NAME_MAX (255) is the type's own ceiling and a
	 * `> DNS_NAME_MAX` test here would be dead code; only 0 can be wrong. */
	if (q->nlen == 0)                     return -DNSE_NAME;
	if (need > cap || need > DNS_MSG_MAX) return -DNSE_CAP;

	dns_put16(out + 0, id);
	dns_put16(out + 2, (uint16_t)(rd ? DNS_F_RD : 0));
	dns_put16(out + 4, 1);
	dns_put16(out + 6, 0);
	dns_put16(out + 8, 0);
	dns_put16(out + 10, 0);
	memcpy(out + DNS_HDR_LEN, q->name, q->nlen);
	dns_put16(out + DNS_HDR_LEN + q->nlen, q->qtype);
	dns_put16(out + DNS_HDR_LEN + q->nlen + 2, q->qclass);
	return (int)need;
}

int dns_encode_error(uint16_t id, const struct dns_question *q, uint8_t rcode,
                     uint8_t *out, size_t cap)
{
	size_t   need = DNS_HDR_LEN;
	uint16_t flags;

	if (q != 0) {
		if (q->nlen == 0) return -DNSE_NAME;   /* uint8_t caps the other end */
		need += (size_t)q->nlen + 4;
	}
	if (need > cap || need > DNS_MSG_MAX) return -DNSE_CAP;

	/* RA is set because dnsfwd does offer recursive service to the LAN, by
	 * forwarding; RD is echoed as 1 for the same reason. */
	flags = (uint16_t)(DNS_F_QR | DNS_F_RD | DNS_F_RA | (rcode & DNS_F_RCMASK));
	dns_put16(out + 0, id);
	dns_put16(out + 2, flags);
	dns_put16(out + 4, (uint16_t)(q != 0 ? 1 : 0));
	dns_put16(out + 6, 0);
	dns_put16(out + 8, 0);
	dns_put16(out + 10, 0);
	if (q != 0) {
		memcpy(out + DNS_HDR_LEN, q->name, q->nlen);
		dns_put16(out + DNS_HDR_LEN + q->nlen, q->qtype);
		dns_put16(out + DNS_HDR_LEN + q->nlen + 2, q->qclass);
	}
	return (int)need;
}

/* ------------------------------------------------------------------------ */
/* Policy: who may ask                                                      */
/* ------------------------------------------------------------------------ */

int dns_on_lan(uint32_t src, uint32_t lan_ip, uint32_t lan_mask)
{
	uint32_t net   = lan_ip & lan_mask;
	uint32_t bcast = net | (uint32_t)~lan_mask;

	if (src == 0)                    return 0;
	if ((src & lan_mask) != net)      return 0;
	if (src == net || src == bcast)   return 0;
	return 1;
}

/* ------------------------------------------------------------------------ */
/* In-flight table                                                          */
/* ------------------------------------------------------------------------ */

void dns_table_init(struct dns_table *t)
{
	memset(t, 0, sizeof *t);
}

int dns_table_add(struct dns_table *t, uint32_t caddr, uint16_t cport,
                  uint16_t cid, uint16_t uid, const struct dns_question *q,
                  uint32_t now_ms)
{
	int i;

	for (i = 0; i < DNS_INFLIGHT_MAX; i++) {
		if (t->e[i].used) continue;
		t->e[i].used  = 1;
		t->e[i].caddr = caddr;
		t->e[i].cport = cport;
		t->e[i].cid   = cid;
		t->e[i].uid   = uid;
		t->e[i].t_ms  = now_ms;
		t->e[i].q     = *q;         /* a decoded struct, never wire bytes */
		t->n_used++;
		return i;
	}
	return -1;                      /* full: drop the new query, never grow */
}

int dns_table_uid_used(const struct dns_table *t, uint16_t uid)
{
	int i;

	for (i = 0; i < DNS_INFLIGHT_MAX; i++)
		if (t->e[i].used && t->e[i].uid == uid) return 1;
	return 0;
}

int dns_table_match(const struct dns_table *t, uint16_t uid,
                    const struct dns_question *q)
{
	int i;

	for (i = 0; i < DNS_INFLIGHT_MAX; i++) {
		if (!t->e[i].used)      continue;
		if (t->e[i].uid != uid) continue;
#ifndef DNSFWD_MUT_NO_QMATCH
		if (t->e[i].q.qtype  != q->qtype)  continue;
		if (t->e[i].q.qclass != q->qclass) continue;
		if (!dns_name_eq(t->e[i].q.name, t->e[i].q.nlen,
		                 q->name, q->nlen)) continue;
#else
		(void)q;
#endif
		return i;
	}
	return -1;
}

void dns_table_free(struct dns_table *t, int i)
{
	if (i < 0 || i >= DNS_INFLIGHT_MAX) return;
	if (!t->e[i].used) return;
	memset(&t->e[i], 0, sizeof t->e[i]);
	t->n_used--;
}

int dns_table_expire(struct dns_table *t, uint32_t now_ms, int *out, int outcap)
{
	int i, k = 0;

	for (i = 0; i < DNS_INFLIGHT_MAX; i++) {
		if (!t->e[i].used) continue;
		/* Unsigned subtraction, so a monotonic millisecond counter wrapping
		 * at 2^32 (49.7 days) still gives the right elapsed time. */
		if ((uint32_t)(now_ms - t->e[i].t_ms) < DNS_TIMEOUT_MS) continue;
		if (k < outcap) out[k] = i;
		k++;
	}
	return k;
}

/* ------------------------------------------------------------------------ */
/* Per-source-address token bucket                                          */
/* ------------------------------------------------------------------------ */

void dns_rate_init(struct dns_rate *r)
{
	memset(r, 0, sizeof *r);
}

int dns_rate_allow(struct dns_rate *r, uint32_t addr, uint32_t now_ms)
{
	int      i, slot = -1, oldest = 0;
	uint32_t best = 0;

	for (i = 0; i < DNS_RATE_SLOTS; i++)
		if (r->s[i].used && r->s[i].addr == addr) { slot = i; break; }
	if (slot < 0)
		for (i = 0; i < DNS_RATE_SLOTS; i++)
			if (!r->s[i].used) { slot = i; break; }
	if (slot < 0) {
		/* Every slot is taken: recycle the least recently seen address.  An
		 * attacker who sprays 33 source addresses therefore gets a fresh
		 * bucket each time -- which is why the LAN check, not this table, is
		 * what stops amplification.  This bucket only stops one LAN host
		 * from starving the others. */
		for (i = 0; i < DNS_RATE_SLOTS; i++) {
			uint32_t age = now_ms - r->s[i].t_ms;
			if (age >= best) { best = age; oldest = i; }
		}
		slot = oldest;
		r->s[slot].used = 0;
	}

	if (!r->s[slot].used) {
		r->s[slot].used  = 1;
		r->s[slot].addr  = addr;
		r->s[slot].tok_m = DNS_RATE_CAP_M;
		r->s[slot].t_ms  = now_ms;
	} else {
		uint32_t dt  = now_ms - r->s[slot].t_ms;
		uint32_t add, tot;

		if (dt > 1000000u) dt = 1000000u;        /* 1e6 * 20 fits in 32 bits */
		add = dt * (uint32_t)DNS_RATE_FILL_M;
		tot = (uint32_t)r->s[slot].tok_m + add;
		if (tot > (uint32_t)DNS_RATE_CAP_M) tot = (uint32_t)DNS_RATE_CAP_M;
		r->s[slot].tok_m = (int32_t)tot;
		r->s[slot].t_ms  = now_ms;
	}

	if (r->s[slot].tok_m < DNS_RATE_COST_M) return 0;
	r->s[slot].tok_m -= DNS_RATE_COST_M;
	return 1;
}

/* ------------------------------------------------------------------------ */
/* The forwarder                                                            */
/* ------------------------------------------------------------------------ */

void dnsfwd_init(struct dnsfwd *d, const struct dns_io *io)
{
	memset(d, 0, sizeof *d);
	d->io            = *io;
	d->upstream_port = DNS_PORT;
	dns_table_init(&d->tbl);
	dns_rate_init(&d->rate);
}

void dnsfwd_config(struct dnsfwd *d, uint32_t lan_ip, uint32_t lan_mask,
                   uint32_t upstream)
{
	d->lan_ip   = lan_ip;
	d->lan_mask = lan_mask;
	d->upstream = upstream;
}

static void answer(struct dnsfwd *d, uint16_t id, const struct dns_question *q,
                   uint8_t rcode, uint32_t addr, uint16_t port)
{
	uint8_t out[DNS_MSG_MAX];
	int     len = dns_encode_error(id, q, rcode, out, sizeof out);

	if (len > 0)
		(void)d->io.send(d->io.ctx, DNS_SOCK_CLIENT, out, (size_t)len,
		                 addr, port);
}

int dnsfwd_on_client(struct dnsfwd *d, const uint8_t *buf, size_t n,
                     uint32_t src, uint16_t sport)
{
	struct dns_query q;
	uint8_t          out[DNS_MSG_MAX];
	uint32_t         now;
	uint16_t         uid = 0;
	int              rc, len, slot, tries;

	d->st.q_in++;

	/* An open forwarder is a reflection and amplification weapon: a 40-byte
	 * spoofed query returns a reply many times its size to a victim of the
	 * attacker's choosing.  So the source address is checked against the LAN
	 * prefix BEFORE anything is parsed, and a query from outside is dropped
	 * in silence -- an error reply would be the amplification. */
	if (!dns_on_lan(src, d->lan_ip, d->lan_mask)) {
		d->st.d_offlan++;
		return DNSFWD_DROPPED;
	}
	/* Port 0 is not a place a reply can go, so a query claiming it is either
	 * forged or broken; answering it would only put a datagram on the wire. */
	if (sport == 0) {
		d->st.d_offlan++;
		return DNSFWD_DROPPED;
	}
	now = d->io.now_ms(d->io.ctx);
	if (!dns_rate_allow(&d->rate, src, now)) {
		d->st.d_rate++;
		return DNSFWD_DROPPED;
	}

	rc = dns_parse_query(buf, n, &q);
	if (rc != 0) {
		uint8_t rcode;

		d->st.d_parse++;
		switch (-rc) {
		case DNSE_QR:                                  /* a reply on :53 */
			return DNSFWD_DROPPED;
		case DNSE_OPCODE:
		case DNSE_CLASS:
			rcode = DNS_RCODE_NOTIMP;  d->st.e_notimp++;  break;
		case DNSE_RD:
			rcode = DNS_RCODE_REFUSED; d->st.e_refused++; break;
		default:
			rcode = DNS_RCODE_FORMERR; d->st.e_formerr++; break;
		}
		if (n < 2) return DNSFWD_DROPPED;    /* not even an ID to answer to */
		answer(d, dns_get16(buf), q.have_q ? &q.q : 0, rcode, src, sport);
		return rc;
	}

	/* A fresh random 16-bit ID per outbound query, and never one already in
	 * flight (two entries sharing an ID would make a reply ambiguous).  Four
	 * draws, then give up: bounded work. */
	for (tries = 0; tries < 4; tries++) {
		if (d->io.rand16(d->io.ctx, &uid) != 0) {
			d->st.d_rand++;
			d->st.e_servfail++;
			answer(d, q.h.id, &q.q, DNS_RCODE_SERVFAIL, src, sport);
			return DNSFWD_DROPPED;
		}
		if (!dns_table_uid_used(&d->tbl, uid)) break;
	}
	if (tries == 4) {
		d->st.d_full++;
		return DNSFWD_DROPPED;
	}

	slot = dns_table_add(&d->tbl, src, sport, q.h.id, uid, &q.q, now);
	if (slot < 0) {
		/* A full table drops the new query rather than growing.  No reply:
		 * a SERVFAIL here would turn table pressure into outbound traffic. */
		d->st.d_full++;
		return DNSFWD_DROPPED;
	}

	len = dns_encode_query(&q.q, uid, 1, out, sizeof out);
	if (len < 0) {
		dns_table_free(&d->tbl, slot);
		d->st.e_servfail++;
		answer(d, q.h.id, &q.q, DNS_RCODE_SERVFAIL, src, sport);
		return len;
	}
	if (d->io.send(d->io.ctx, DNS_SOCK_UPSTREAM, out, (size_t)len,
	               d->upstream, d->upstream_port) < 0) {
		dns_table_free(&d->tbl, slot);
		d->st.e_servfail++;
		answer(d, q.h.id, &q.q, DNS_RCODE_SERVFAIL, src, sport);
		return DNSFWD_DROPPED;
	}
	d->st.q_fwd++;
	return 0;
}

int dnsfwd_on_upstream(struct dnsfwd *d, const uint8_t *buf, size_t n,
                       uint32_t src, uint16_t sport)
{
	struct dns_reply r;
	uint8_t          out[DNS_MSG_MAX];
	int              rc, i;

	d->st.r_in++;

	/* The Kaminsky check, all four halves.  An off-path attacker who guesses
	 * only the ID still has to match the source address, the source port and
	 * the question section; getting any one wrong drops the datagram and
	 * leaves the genuine reply still acceptable. */
	if (src != d->upstream || sport != d->upstream_port) {
		d->st.d_spoof++;
		return DNSFWD_DROPPED;
	}
	rc = dns_parse_reply(buf, n, &r);
	if (rc != 0) {
		d->st.d_parse++;
		return rc;
	}
	i = dns_table_match(&d->tbl, r.h.id, &r.q);
	if (i < 0) {
		d->st.d_spoof++;
		return DNSFWD_DROPPED;
	}

	/* Relay the upstream's own bytes -- but only after every record in every
	 * section has been walked and bounds-checked above -- with the two ID
	 * bytes rewritten to the client's.  Nothing else is touched, and no
	 * record is re-encoded, so a legitimate answer reaches the client
	 * unaltered.  The AUTHORITY section is never read for NS records: dnsfwd
	 * does not follow referrals. */
	memcpy(out, buf, n);
	dns_put16(out, d->tbl.e[i].cid);
	(void)d->io.send(d->io.ctx, DNS_SOCK_CLIENT, out, n,
	                 d->tbl.e[i].caddr, d->tbl.e[i].cport);
	dns_table_free(&d->tbl, i);
	d->st.r_out++;
	return 0;
}

int dnsfwd_tick(struct dnsfwd *d)
{
	int      idx[DNS_INFLIGHT_MAX];
	uint32_t now = d->io.now_ms(d->io.ctx);
	int      k, j;

	k = dns_table_expire(&d->tbl, now, idx, DNS_INFLIGHT_MAX);
	/* dns_table_expire returns the number that timed out, which can in
	 * principle exceed what it wrote into `idx`.  It cannot here -- the table
	 * holds at most DNS_INFLIGHT_MAX entries and that is the capacity passed
	 * -- but the loop below must not depend on a reader working that out. */
	if (k > DNS_INFLIGHT_MAX) k = DNS_INFLIGHT_MAX;
	for (j = 0; j < k; j++) {
		int i = idx[j];
		answer(d, d->tbl.e[i].cid, &d->tbl.e[i].q, DNS_RCODE_SERVFAIL,
		       d->tbl.e[i].caddr, d->tbl.e[i].cport);
		dns_table_free(&d->tbl, i);
		d->st.t_expired++;
		d->st.e_servfail++;
	}
	return k;
}
