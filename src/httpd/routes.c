/* src/httpd/routes.c -- the route table and the eleven handlers.
 *
 * Nothing in this file writes a byte that came from the request into a response.
 * Every error body is one of the fixed tokens in the err_* calls below, chosen by
 * a switch, and the only variable-length thing that ever reaches a body is the
 * PING output, which arrives from brokerd as the stdout of a program brokerd ran
 * with a four-byte typed target -- and it is filtered byte by byte on the way out
 * anyway (ping_sanitise).  That is why there is no "reflected" case in the tests:
 * there is no code path that could produce one.
 *
 * WHY THE CSRF CHECK IS A DOUBLE SUBMIT.  httpd cannot verify a CSRF token on its
 * own: the token is brokerd's random value and httpd has no session table to look
 * it up in.  What httpd can do is require the token to arrive twice, once in the
 * `X-RLX-CSRF` header and once in a companion `rlxc` cookie, and compare the two
 * in constant time.  `SameSite=Strict` on both cookies means a cross-site request
 * carries neither, so the check fails at the edge without a broker round trip.
 * brokerd then compares the header's value against the session's real token,
 * which is the check that decides.  The cookie is an addition to SPEC-R7 section
 * 7 and it is named in the report.
 */

/* _GNU_SOURCE before the first include, for O_NOFOLLOW: uClibc 0.9.30's fcntl.h
 * hides it behind __USE_GNU, and -std=gnu99 alone does not define it.  Without it
 * this file builds on the host and fails on the target, which is exactly the class
 * of difference the target build exists to catch. */
#define _GNU_SOURCE 1

#include "routes.h"

#include "json.h"
#include "cfg.h"
#include "schema.h"
#include "client.h"

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

/* ------------------------------------------------------------ small helpers */

/* Constant-time equality over exactly 32 bytes.  It is five lines and it is
 * deliberately NOT ct_memeq() from src/lib/kdf.h: httpd links no crypto at all,
 * so nothing about the KDF -- not its code, not its 4 MiB working set -- is in
 * the address space that parses attacker bytes.  The duplication is the point. */
int route_ct_eq32(const char *a, const char *b)
{
	volatile unsigned char acc = 0;
	int i;

	for (i = 0; i < 32; i++)
		acc |= (unsigned char)(a[i] ^ b[i]);
	return acc == 0;
}

static int unhex16(const char *s, uint8_t out[16])
{
	int i;

	for (i = 0; i < 16; i++) {
		int h = 0, l = 0, k;

		for (k = 0; k < 2; k++) {
			int c = (unsigned char)s[i * 2 + k];
			int v;

			if (c >= '0' && c <= '9')
				v = c - '0';
			else if (c >= 'a' && c <= 'f')
				v = c - 'a' + 10;
			else if (c >= 'A' && c <= 'F')
				v = c - 'A' + 10;
			else
				return -1;
			if (k == 0)
				h = v;
			else
				l = v;
		}
		out[i] = (uint8_t)((h << 4) | l);
	}
	return 0;
}

static void hex16(const uint8_t in[16], char out[33])
{
	static const char d[] = "0123456789abcdef";
	int i;

	for (i = 0; i < 16; i++) {
		out[i * 2] = d[(in[i] >> 4) & 0x0f];
		out[i * 2 + 1] = d[in[i] & 0x0f];
	}
	out[32] = '\0';
}

static void put16be(uint8_t *p, uint16_t v)
{
	p[0] = (uint8_t)((v >> 8) & 0xffu);
	p[1] = (uint8_t)(v & 0xffu);
}

static uint16_t get16be(const uint8_t *p)
{
	return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

static uint32_t get32be(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
	       ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

/* Strict dotted quad: four decimal octets, no leading zero, nothing else. */
static int parse_ipv4(const char *s, size_t n, uint8_t out[4])
{
	size_t i = 0;
	int oct;

	for (oct = 0; oct < 4; oct++) {
		unsigned v = 0;
		size_t d = 0;

		if (oct > 0) {
			if (i >= n || s[i] != '.')
				return -1;
			i++;
		}
		while (i < n && s[i] >= '0' && s[i] <= '9') {
			v = v * 10u + (unsigned)(s[i] - '0');
			if (v > 255u)
				return -1;
			i++;
			d++;
			if (d > 3)
				return -1;
		}
		if (d == 0)
			return -1;
		if (d > 1 && s[i - d] == '0')
			return -1;
		out[oct] = (uint8_t)v;
	}
	return (i == n) ? 0 : -1;
}

static void ip_to_text(const uint8_t *v, char *out, size_t cap)
{
	char tmp[20];
	size_t o = 0;
	int i;

	for (i = 0; i < 4; i++) {
		unsigned x = v[i];
		char d[3];
		int nd = 0;

		if (i > 0 && o + 1 < sizeof(tmp))
			tmp[o++] = '.';
		if (x == 0) {
			d[nd++] = '0';
		} else {
			while (x > 0 && nd < 3) {
				d[nd++] = (char)('0' + (x % 10u));
				x /= 10u;
			}
		}
		while (nd > 0 && o + 1 < sizeof(tmp))
			tmp[o++] = d[--nd];
	}
	tmp[o] = '\0';
	if (cap > 0) {
		size_t l = (o < cap - 1) ? o : cap - 1;

		memcpy(out, tmp, l);
		out[l] = '\0';
	}
}

/* ------------------------------------------------------------- the responses */

void route_rsp_init(struct http_rsp *rs)
{
	memset(rs, 0, sizeof(*rs));
	rs->status = 500;
	rs->ctype = "application/json";
	rs->fd = -1;
	rs->cookies[0] = '\0';
}

static void body_json(struct http_rsp *rs, const struct json_w *w)
{
	if (json_w_done(w) != 0) {
		/* The only way here is a response that outgrew its buffer, which
		 * is this program's bug and not the peer's; say so with a fixed
		 * body rather than sending a truncated document. */
		rs->status = 500;
		rs->blen = 0;
		memcpy(rs->body, "{\"error\":\"toolong\"}", 19);
		rs->blen = 19;
		return;
	}
	rs->blen = w->len;
}

void route_err(struct http_rsp *rs, int status, const char *code)
{
	struct json_w w;

	rs->status = status;
	rs->ctype = "application/json";
	rs->fd = -1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 0);
	json_w_str(&w, "error", code);
	json_w_obj_close(&w);
	body_json(rs, &w);
}

static void ok_empty(struct http_rsp *rs)
{
	struct json_w w;

	rs->status = 200;
	rs->ctype = "application/json";
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	json_w_obj_close(&w);
	body_json(rs, &w);
}

/* ------------------------------------------------------ broker status mapping */

/* One place, so no handler invents a mapping.  `body` is the broker's response
 * body, used only for the two statuses SPEC-R7 gives a body to. */
static void map_broker(struct http_rsp *rs, const struct bk_resp *br)
{
	switch (br->status) {
	case BK_BADREQ:
		route_err(rs, 400, "badreq");
		return;
	case BK_PERM:
		route_err(rs, 403, "perm");
		return;
	case BK_AUTH:
		route_err(rs, 401, "auth");
		return;
	case BK_LOCKED: {
		struct json_w w;
		uint32_t s = (br->body_len >= 4) ? get32be(br->body) : 60u;

		if (s > 3600u)
			s = 3600u;
		rs->status = 429;
		rs->retry_after = s;
		json_w_init(&w, rs->body, sizeof(rs->body));
		json_w_obj_open(&w);
		json_w_bool(&w, "ok", 0);
		json_w_str(&w, "error", "locked");
		json_w_num(&w, "retry_s", s);
		json_w_obj_close(&w);
		body_json(rs, &w);
		return;
	}
	case BK_INVAL: {
		struct json_w w;
		uint32_t id = (br->body_len >= 2) ? get16be(br->body) : 0u;

		/* The key id goes back as a NUMBER, not as its name and not as
		 * the text the peer sent: the page maps ids from its own table.
		 * No response in this program contains request bytes. */
		rs->status = 400;
		json_w_init(&w, rs->body, sizeof(rs->body));
		json_w_obj_open(&w);
		json_w_bool(&w, "ok", 0);
		json_w_str(&w, "error", "inval");
		json_w_num(&w, "key", id);
		json_w_obj_close(&w);
		body_json(rs, &w);
		return;
	}
	case BK_IO:
		route_err(rs, 500, "io");
		return;
	case BK_NOENT:
		route_err(rs, 404, "noent");
		return;
	case BK_BUSY:
		route_err(rs, 503, "busy");
		return;
	case BK_NOTSUP:
		route_err(rs, 501, "notsup");
		return;
	case BK_NOENTROPY:
		/* 量 2026-09-30 on this board: entropy_avail read 0 at 768 s and
		 * at 1613 s of uptime, so this is the answer a password change
		 * gets TODAY.  It is a 503 and it says why: the alternative is a
		 * salt that is not random, and a weak salt that nobody is told
		 * about is worse than a refusal the user can read. */
		route_err(rs, 503, "noentropy");
		return;
	default:
		route_err(rs, 500, "broker");
		return;
	}
}

static int call_broker(const struct route_env *env, uint8_t op,
		       const struct http_req *rq,
		       const uint8_t *body, uint32_t blen,
		       struct bk_resp *br, struct http_rsp *rs)
{
	struct bk_req q;
	int rc;

	memset(&q, 0, sizeof(q));
	q.op = op;
	q.client_ip = env->client_ip;
	q.body = body;
	q.body_len = blen;
	if (rq->sess[0] != '\0' && unhex16(rq->sess, q.session) != 0) {
		route_err(rs, 400, "session");
		return -1;
	}
	if (rq->hcsrf[0] != '\0' && unhex16(rq->hcsrf, q.csrf) != 0) {
		route_err(rs, 400, "csrf");
		return -1;
	}

	rc = bk_call(env->sock, &q, br);
	if (rc != 0) {
		/* The broker is the whole of this program's ability to act.  If
		 * it cannot be reached, say 503 and nothing about why. */
		route_err(rs, 503, "broker");
		return -1;
	}
	if (br->status != BK_OK) {
		map_broker(rs, br);
		return -1;
	}
	return 0;
}

/* ------------------------------------------------------------ static content */

static int send_file(struct http_rsp *rs, const char *relpath, const char *ctype)
{
	struct stat st;
	int fd;

	/* O_NOFOLLOW: a symlink in the web root is refused at open time as well
	 * as by `make chrootcheck`.  Two independent readings of the same rule,
	 * one at build time over the tree and one at run time per request. */
	fd = open(relpath, O_RDONLY | O_NOFOLLOW);
	if (fd < 0) {
		route_err(rs, 404, "nofile");
		return -1;
	}
	{
		int fl = fcntl(fd, F_GETFD, 0);

		if (fl >= 0)
			(void)fcntl(fd, F_SETFD, fl | FD_CLOEXEC);
	}
	if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode)) {
		(void)close(fd);
		route_err(rs, 404, "nofile");
		return -1;
	}
	/* An executable bit inside the web root is a gate failure, not a file to
	 * serve.  chrootcheck refuses the tree at build time; this refuses the
	 * request at run time, on the chance the tree changed underneath. */
	if ((st.st_mode & (S_IXUSR | S_IXGRP | S_IXOTH)) != 0) {
		(void)close(fd);
		route_err(rs, 404, "nofile");
		return -1;
	}
	if (st.st_size < 0 || st.st_size > 262144) {
		(void)close(fd);
		route_err(rs, 404, "nofile");
		return -1;
	}
	rs->status = 200;
	rs->ctype = ctype;
	rs->fd = fd;
	rs->fsize = (uint32_t)st.st_size;
	rs->blen = 0;
	return 0;
}

static void route_static(const struct http_req *rq, struct http_rsp *rs,
			 const struct route_env *env)
{
	const char *name = rq->path + 8;          /* past "/static/" */
	const char *type;
	char rel[8 + HTTP_NAME_MAX + 1];
	size_t nl;

	(void)env;
	nl = strlen(name);
	if (nl == 0 || nl > HTTP_NAME_MAX) {
		route_err(rs, 404, "nofile");
		return;
	}
	/* http_decode_path() already refused everything outside
	 * [A-Za-z0-9._-] and '/', every "." and ".." segment and every encoded
	 * separator.  This is the second reading, over the one component that
	 * will become a filename: no '/' at all may survive here. */
	if (memchr(name, '/', nl) != NULL) {
		route_err(rs, 404, "nofile");
		return;
	}
	type = http_mime(name);
	if (type == NULL) {
		route_err(rs, 404, "nofile");
		return;
	}
	memcpy(rel, "static/", 7);
	memcpy(rel + 7, name, nl);
	rel[7 + nl] = '\0';
	(void)send_file(rs, rel, type);
}

/* ------------------------------------------------------------------- handlers */

static void h_index(const struct http_req *rq, struct http_rsp *rs,
		    const struct route_env *env)
{
	(void)rq;
	(void)env;
	(void)send_file(rs, "index.html", "text/html; charset=utf-8");
}

/* GET /api/status.  Renders the TLVs of SPEC-R7 op 0x04.  Without a session the
 * broker returns only 0x8001, 0x8006 and 0x8008, and this renders whatever came
 * back rather than assuming which. */
static void h_status(const struct http_req *rq, struct http_rsp *rs,
		     const struct route_env *env)
{
	struct bk_resp br;
	struct json_w w;
	uint32_t i = 0;

	if (call_broker(env, BK_STATUS, rq, NULL, 0, &br, rs) != 0)
		return;

	rs->status = 200;
	rs->nostore = 1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	while (i + 4 <= br.body_len) {
		uint16_t t = get16be(br.body + i);
		uint16_t l = get16be(br.body + i + 2);
		const uint8_t *v = br.body + i + 4;

		if ((uint32_t)l > br.body_len - i - 4)
			break;
		switch (t) {
		case 0x8001:
			if (l == 4)
				json_w_num(&w, "uptime_s", get32be(v));
			break;
		case 0x8002:
			if (l == 4)
				json_w_num(&w, "load1x100", get32be(v));
			break;
		case 0x8003:
			if (l == 4)
				json_w_num(&w, "memfree_kb", get32be(v));
			break;
		case 0x8004:
			if (l == 1)
				json_w_num(&w, "cfg_source", v[0]);
			break;
		case 0x8005:
			if (l == 4)
				json_w_num(&w, "cfg_seq", get32be(v));
			break;
		case 0x8006:
			if (l <= 32)
				json_w_strn(&w, "version", (const char *)v, l);
			break;
		case 0x8007:
			if (l == 4)
				json_w_num(&w, "entropy_avail", get32be(v));
			break;
		case 0x8008:
			if (l == 1)
				json_w_bool(&w, "auth_ready", v[0] != 0);
			break;
		default:
			break;
		}
		i += 4u + l;
	}
	json_w_obj_close(&w);
	body_json(rs, &w);
}

static void set_cookies(struct http_rsp *rs, const char *sess, const char *csrf)
{
	/* Two cookies, both SameSite=Strict, both Path=/.  `rlxs` is HttpOnly so
	 * the page's script cannot read the session; `rlxc` deliberately is NOT,
	 * because the script has to copy it into the X-RLX-CSRF header -- that is
	 * what makes the double submit possible.  Neither is Secure: there is no
	 * TLS in R7 (SPEC-R7 puts R7g out of the gate), and a Secure cookie over
	 * plain HTTP is a cookie that is never sent. */
	/* Every length comes from strlen, and there is not one hand-counted byte
	 * count left in this function.  The version this replaced had six, and one
	 * of them was wrong: the logout `rlxc` line was copied as 54 bytes when the
	 * literal is 55, so the trailing LF was dropped and the response head
	 * carried a bare CR.  test_routes.c matched the cookie as a SUBSTRING and
	 * passed; it now matches through the CRLF, which is why the case below is
	 * written with "\r\n" in it. */
	size_t o = 0;
	size_t cap = sizeof(rs->cookies);
	int i;

	rs->cookies[0] = '\0';
	for (i = 0; i < 2; i++) {
		const char *name = (i == 0) ? "Set-Cookie: rlxs=" :
					      "Set-Cookie: rlxc=";
		const char *val = (i == 0) ? sess : csrf;
		const char *attr;
		size_t need;

		if (val == NULL) {
			/* the expiring form, when logout clears them */
			attr = (i == 0)
				? "; Path=/; HttpOnly; SameSite=Strict; Max-Age=0\r\n"
				: "; Path=/; SameSite=Strict; Max-Age=0\r\n";
			val = "";
		} else {
			attr = (i == 0) ? "; Path=/; HttpOnly; SameSite=Strict\r\n"
					: "; Path=/; SameSite=Strict\r\n";
		}
		need = strlen(name) + strlen(val) + strlen(attr);
		if (o + need + 1 > cap) {
			rs->cookies[0] = '\0';   /* all or nothing */
			return;
		}
		memcpy(rs->cookies + o, name, strlen(name));
		o += strlen(name);
		memcpy(rs->cookies + o, val, strlen(val));
		o += strlen(val);
		memcpy(rs->cookies + o, attr, strlen(attr));
		o += strlen(attr);
		rs->cookies[o] = '\0';
	}
}

static void h_login(const struct http_req *rq, struct http_rsp *rs,
		    const struct route_env *env)
{
	struct json_obj o;
	const struct json_member *m;
	struct bk_resp br;
	struct json_w w;
	char sess[33], csrf[33];
	uint32_t retry = 0;
	int rc;

	rc = json_parse(rq->body, rq->body_len, &o);
	if (rc != 0) {
		route_err(rs, 400, json_errname(rc));
		return;
	}
	m = json_get(&o, "password");
	if (m == NULL || m->type != JT_STR || m->slen == 0) {
		route_err(rs, 400, "field");
		return;
	}

	/* plan D8 v6 ruling 2: the limiter runs BEFORE the KDF, on this side, so
	 * a refused attempt never reaches brokerd and never allocates the
	 * scrypt working set.  The parent owns the bucket (rl.h says why). */
	if (env->kdf_grant != NULL && !env->kdf_grant(env->ctx, &retry)) {
		struct json_w e;

		rs->status = 429;
		rs->retry_after = (retry == 0) ? 1u : retry;
		rs->nostore = 1;
		json_w_init(&e, rs->body, sizeof(rs->body));
		json_w_obj_open(&e);
		json_w_bool(&e, "ok", 0);
		json_w_str(&e, "error", "ratelimit");
		json_w_num(&e, "retry_s", rs->retry_after);
		json_w_obj_close(&e);
		body_json(rs, &e);
		return;
	}

	rc = call_broker(env, BK_LOGIN, rq, (const uint8_t *)m->sval, m->slen,
			 &br, rs);
	if (env->kdf_release != NULL)
		env->kdf_release(env->ctx);
	if (rc != 0)
		return;

	if (br.body_len < 36) {
		route_err(rs, 500, "broker");
		return;
	}
	hex16(br.body, sess);
	hex16(br.body + 16, csrf);
	set_cookies(rs, sess, csrf);

	rs->status = 200;
	rs->nostore = 1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	json_w_str(&w, "csrf", csrf);
	json_w_num(&w, "ttl_s", get32be(br.body + 32));
	json_w_obj_close(&w);
	body_json(rs, &w);
}

static void h_logout(const struct http_req *rq, struct http_rsp *rs,
		     const struct route_env *env)
{
	struct bk_resp br;

	if (call_broker(env, BK_LOGOUT, rq, NULL, 0, &br, rs) != 0)
		return;
	set_cookies(rs, NULL, NULL);
	rs->nostore = 1;
	ok_empty(rs);
}

static void h_config_get(const struct http_req *rq, struct http_rsp *rs,
			 const struct route_env *env)
{
	uint8_t ids[2 * CFG_NKEYS];
	uint32_t nids = 0;
	struct bk_resp br;
	struct json_w w, inner;
	char scratch[2048];
	unsigned i;
	uint32_t off = 0;

	for (i = 0; i < CFG_NKEYS; i++) {
		const struct cfg_key *k = cfg_key_at(i);

		if (k == NULL || k->web == WEB_HIDDEN)
			continue;
		put16be(ids + nids, k->id);
		nids += 2;
	}
	if (call_broker(env, BK_GET, rq, ids, nids, &br, rs) != 0)
		return;

	json_w_init(&inner, scratch, sizeof(scratch));
	json_w_obj_open(&inner);
	while (off + 4 <= br.body_len) {
		uint16_t t = get16be(br.body + off);
		uint16_t l = get16be(br.body + off + 2);
		const uint8_t *v = br.body + off + 4;
		const struct cfg_key *k;

		if ((uint32_t)l > br.body_len - off - 4)
			break;
		k = cfg_key_by_id(t);
		off += 4u + l;
		if (k == NULL || k->web == WEB_HIDDEN)
			continue;
		switch (k->type) {
		case CT_BOOL:
			if (l == 1)
				json_w_bool(&inner, k->name, v[0] != 0);
			break;
		case CT_ENUM:
			if (l == 1)
				json_w_num(&inner, k->name, v[0]);
			break;
		case CT_U16:
			if (l == 2)
				json_w_num(&inner, k->name, get16be(v));
			break;
		case CT_U32:
			if (l == 4)
				json_w_num(&inner, k->name, get32be(v));
			break;
		case CT_IPV4:
			if (l == 4) {
				char txt[16];

				ip_to_text(v, txt, sizeof(txt));
				json_w_str(&inner, k->name, txt);
			}
			break;
		case CT_STR:
			if (l <= JSON_STR_MAX)
				json_w_strn(&inner, k->name, (const char *)v, l);
			break;
		default:
			break;                  /* BYTES is never web-readable */
		}
	}
	json_w_obj_close(&inner);
	if (json_w_done(&inner) != 0) {
		route_err(rs, 500, "toolong");
		return;
	}

	rs->status = 200;
	rs->nostore = 1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	json_w_raw(&w, "config", scratch);
	json_w_obj_close(&w);
	body_json(rs, &w);
}

/* One member of the POST body into a TLV value.  Returns the value length, or a
 * negative marker: -1 unknown key, -2 read-only, -3 wrong type, -4 out of
 * bounds.  No branch of it copies more than `cap` bytes. */
static int member_to_value(const struct json_member *m, const struct cfg_key *k,
			   uint8_t *out, size_t cap)
{
	if (k->web != WEB_RW)
		return -2;
	switch (k->type) {
	case CT_BOOL:
		if (cap < 1)
			return -4;
		if (m->type == JT_BOOL)
			out[0] = (uint8_t)(m->nval ? 1 : 0);
		else if (m->type == JT_NUM && m->nval <= 1u)
			out[0] = (uint8_t)m->nval;
		else
			return -3;
		return 1;
	case CT_ENUM:
		if (cap < 1)
			return -4;
		if (m->type != JT_NUM)
			return -3;
		if (m->nval > k->max)
			return -4;
		out[0] = (uint8_t)m->nval;
		return 1;
	case CT_U16:
		if (cap < 2)
			return -4;
		if (m->type != JT_NUM)
			return -3;
		if (m->nval > 65535u || m->nval < k->min || m->nval > k->max)
			return -4;
		put16be(out, (uint16_t)m->nval);
		return 2;
	case CT_U32:
		if (cap < 4)
			return -4;
		if (m->type != JT_NUM)
			return -3;
		if (m->nval < k->min || m->nval > k->max)
			return -4;
		out[0] = (uint8_t)((m->nval >> 24) & 0xffu);
		out[1] = (uint8_t)((m->nval >> 16) & 0xffu);
		out[2] = (uint8_t)((m->nval >> 8) & 0xffu);
		out[3] = (uint8_t)(m->nval & 0xffu);
		return 4;
	case CT_IPV4:
		if (cap < 4)
			return -4;
		if (m->type != JT_STR)
			return -3;
		if (parse_ipv4(m->sval, m->slen, out) != 0)
			return -4;
		return 4;
	case CT_STR:
		if (m->type != JT_STR)
			return -3;
		if (m->slen < k->min || m->slen > k->max)
			return -4;
		if ((size_t)m->slen > cap)
			return -4;
		memcpy(out, m->sval, m->slen);
		return m->slen;
	default:
		return -2;                      /* BYTES: never from the web */
	}
}

static void h_config_set(const struct http_req *rq, struct http_rsp *rs,
			 const struct route_env *env)
{
	struct json_obj o;
	struct bk_resp br;
	uint8_t tlv[BK_BODY_IN_MAX];
	uint32_t used = 0;
	uint16_t order[JSON_KEYS_MAX];
	unsigned n = 0, i, j;
	int rc;

	rc = json_parse(rq->body, rq->body_len, &o);
	if (rc != 0) {
		route_err(rs, 400, json_errname(rc));
		return;
	}
	if (o.n == 0) {
		route_err(rs, 400, "empty");
		return;
	}

	/* Resolve every name first, so a body that names one bad key changes
	 * nothing: the broker is not called until all of them are known good. */
	for (i = 0; i < o.n; i++) {
		const struct cfg_key *k = cfg_key_by_name(o.m[i].key);

		if (k == NULL) {
			route_err(rs, 400, "badkey");
			return;
		}
		if (k->web != WEB_RW) {
			route_err(rs, 403, "readonly");
			return;
		}
		order[n++] = k->id;
	}

	/* SPEC-R7 section 5: TLV ids strictly ascending.  Insertion sort over at
	 * most JSON_KEYS_MAX ids; duplicates cannot exist because json_parse
	 * refuses a duplicate key. */
	for (i = 1; i < n; i++) {
		uint16_t v = order[i];

		j = i;
		while (j > 0 && order[j - 1] > v) {
			order[j] = order[j - 1];
			j--;
		}
		order[j] = v;
	}

	for (i = 0; i < n; i++) {
		const struct cfg_key *k = cfg_key_by_id(order[i]);
		const struct json_member *m;
		int vl;

		if (k == NULL) {
			route_err(rs, 500, "table");
			return;
		}
		m = json_get(&o, k->name);
		if (m == NULL) {
			route_err(rs, 500, "table");
			return;
		}
		if (used + 4u > sizeof(tlv)) {
			route_err(rs, 413, "toolong");
			return;
		}
		vl = member_to_value(m, k, tlv + used + 4, sizeof(tlv) - used - 4);
		if (vl < 0) {
			if (vl == -1)
				route_err(rs, 400, "badkey");
			else if (vl == -2)
				route_err(rs, 403, "readonly");
			else if (vl == -3)
				route_err(rs, 400, "badtype");
			else
				route_err(rs, 400, "range");
			return;
		}
		put16be(tlv + used, k->id);
		put16be(tlv + used + 2, (uint16_t)vl);
		used += 4u + (uint32_t)vl;
	}

	if (call_broker(env, BK_SET, rq, tlv, used, &br, rs) != 0)
		return;
	rs->nostore = 1;
	ok_empty(rs);
}

static void h_password(const struct http_req *rq, struct http_rsp *rs,
		       const struct route_env *env)
{
	struct json_obj o;
	const struct json_member *mo, *mn;
	struct bk_resp br;
	uint8_t body[1 + 64 + 1 + 64];
	uint32_t used = 0;
	uint32_t retry = 0;
	int rc;

	rc = json_parse(rq->body, rq->body_len, &o);
	if (rc != 0) {
		route_err(rs, 400, json_errname(rc));
		return;
	}
	mo = json_get(&o, "old");
	mn = json_get(&o, "new");
	if (mo == NULL || mn == NULL || mo->type != JT_STR || mn->type != JT_STR) {
		route_err(rs, 400, "field");
		return;
	}
	if (mn->slen < 8 || mn->slen > 64 || mo->slen > 64) {
		route_err(rs, 400, "pwlen");
		return;
	}

	/* PWSET runs the KDF twice (verify the old, derive the new), so it goes
	 * through the same grant as LOGIN.  It needs a session already, so this
	 * is not an unauthenticated path -- but a session holder is not allowed
	 * to occupy the broker either. */
	if (env->kdf_grant != NULL && !env->kdf_grant(env->ctx, &retry)) {
		rs->retry_after = (retry == 0) ? 1u : retry;
		rs->nostore = 1;
		route_err(rs, 429, "ratelimit");
		return;
	}

	body[used++] = (uint8_t)mo->slen;
	memcpy(body + used, mo->sval, mo->slen);
	used += mo->slen;
	body[used++] = (uint8_t)mn->slen;
	memcpy(body + used, mn->sval, mn->slen);
	used += mn->slen;

	rc = call_broker(env, BK_PWSET, rq, body, used, &br, rs);
	memset(body, 0, sizeof(body));
	if (env->kdf_release != NULL)
		env->kdf_release(env->ctx);
	if (rc != 0)
		return;
	rs->nostore = 1;
	ok_empty(rs);
}

/* Everything the broker hands back from a PING is the stdout of a program.  It
 * is filtered to printable ASCII and newline here, before the JSON writer sees
 * it, so no byte sequence in it can change the shape of the response. */
static size_t ping_sanitise(const uint8_t *in, size_t n, char *out, size_t cap)
{
	size_t i, o = 0;

	for (i = 0; i < n && o < cap; i++) {
		unsigned char c = in[i];

		if (c == '\n' || (c >= 0x20 && c < 0x7f))
			out[o++] = (char)c;
		else if (c == '\r' || c == '\t')
			out[o++] = ' ';
		else
			out[o++] = '.';
	}
	return o;
}

static void h_ping(const struct http_req *rq, struct http_rsp *rs,
		   const struct route_env *env)
{
	struct json_obj o;
	const struct json_member *mt, *mc;
	struct bk_resp br;
	struct json_w w;
	uint8_t body[5];
	char text[2048];
	size_t tl;
	int rc;

	rc = json_parse(rq->body, rq->body_len, &o);
	if (rc != 0) {
		route_err(rs, 400, json_errname(rc));
		return;
	}
	mt = json_get(&o, "target");
	mc = json_get(&o, "count");
	if (mt == NULL || mt->type != JT_STR || mc == NULL || mc->type != JT_NUM) {
		route_err(rs, 400, "field");
		return;
	}
	if (mc->nval < 1u || mc->nval > 5u) {
		route_err(rs, 400, "range");
		return;
	}
	if (parse_ipv4(mt->sval, mt->slen, body) != 0) {
		route_err(rs, 400, "target");
		return;
	}
	body[4] = (uint8_t)mc->nval;

	if (call_broker(env, BK_PING, rq, body, sizeof(body), &br, rs) != 0)
		return;

	tl = ping_sanitise(br.body, br.body_len, text, sizeof(text) - 1);
	text[tl] = '\0';
	rs->status = 200;
	rs->nostore = 1;
	json_w_init(&w, rs->body, sizeof(rs->body));
	json_w_obj_open(&w);
	json_w_bool(&w, "ok", 1);
	json_w_strn(&w, "output", text, tl);
	json_w_obj_close(&w);
	body_json(rs, &w);
}

static void h_reboot(const struct http_req *rq, struct http_rsp *rs,
		     const struct route_env *env)
{
	struct bk_resp br;

	if (call_broker(env, BK_REBOOT, rq, NULL, 0, &br, rs) != 0)
		return;
	rs->nostore = 1;
	ok_empty(rs);
}

/* POST /api/firmware.  SPEC-R7 reserves ops 0x20..0x22 for R8 and says NOTSUP in
 * R7, so httpd answers 501 without a broker round trip -- but only after the same
 * session and CSRF checks as any other state-changing route, so the route does
 * not become an unauthenticated probe for whether a firmware path exists. */
static void h_firmware(const struct http_req *rq, struct http_rsp *rs,
		       const struct route_env *env)
{
	(void)rq;
	(void)env;
	rs->nostore = 1;
	route_err(rs, 501, "notsup");
}

/* ----------------------------------------------------------- the route table */

#define RF_GET   0x01
#define RF_POST  0x02
#define RF_SESS  0x04   /* a session cookie must be present and well formed */
#define RF_CSRF  0x08   /* state changing: X-RLX-CSRF must match the rlxc cookie */
#define RF_API   0x10   /* Cache-Control: no-store, and errors are JSON */
#define RF_PFX   0x20   /* match by prefix, not exact */

struct route {
	const char *path;
	uint8_t methods;
	uint8_t flags;
	void (*fn)(const struct http_req *, struct http_rsp *,
		   const struct route_env *);
};

static const struct route routes[] = {
	{ "/",              RF_GET,  0,                            h_index },
	{ "/static/",       RF_GET,  RF_PFX,                       route_static },
	{ "/api/status",    RF_GET,  RF_API,                       h_status },
	{ "/api/login",     RF_POST, RF_API,                       h_login },
	{ "/api/logout",    RF_POST, RF_API | RF_SESS | RF_CSRF,   h_logout },
	{ "/api/config",    RF_GET,  RF_API | RF_SESS,             h_config_get },
	{ "/api/config",    RF_POST, RF_API | RF_SESS | RF_CSRF,   h_config_set },
	{ "/api/password",  RF_POST, RF_API | RF_SESS | RF_CSRF,   h_password },
	{ "/api/ping",      RF_POST, RF_API | RF_SESS | RF_CSRF,   h_ping },
	{ "/api/reboot",    RF_POST, RF_API | RF_SESS | RF_CSRF,   h_reboot },
	{ "/api/firmware",  RF_POST, RF_API | RF_SESS | RF_CSRF,   h_firmware }
};

#define NROUTES (sizeof(routes) / sizeof(routes[0]))

int route_dispatch(const struct http_req *rq, struct http_rsp *rs,
		   const struct route_env *env)
{
	unsigned i;
	int path_found = 0;
	const struct route *r = NULL;
	uint8_t want = (rq->method == HM_GET) ? RF_GET : RF_POST;

	route_rsp_init(rs);

	for (i = 0; i < NROUTES; i++) {
		int match;

		if (routes[i].flags & RF_PFX)
			match = (strncmp(rq->path, routes[i].path,
					 strlen(routes[i].path)) == 0);
		else
			match = (strcmp(rq->path, routes[i].path) == 0);
		if (!match)
			continue;
		path_found = 1;
		if (routes[i].methods & want) {
			r = &routes[i];
			break;
		}
	}

	if (r == NULL) {
		if (path_found) {
			rs->allow_get_post = 1;
			route_err(rs, 405, "method");
		} else {
			route_err(rs, 404, "notfound");
		}
		return 0;
	}

	if (r->flags & RF_API)
		rs->nostore = 1;

	if (r->flags & RF_SESS) {
		if (rq->sess[0] == '\0') {
			route_err(rs, 401, "nosession");
			rs->nostore = 1;
			return 0;
		}
	}
	if (r->flags & RF_CSRF) {
		/* Presence, form, and the double submit -- in constant time, and
		 * before anything else touches the body. */
		if (rq->hcsrf[0] == '\0' || rq->ccsrf[0] == '\0' ||
		    !route_ct_eq32(rq->hcsrf, rq->ccsrf)) {
			route_err(rs, 403, "csrf");
			rs->nostore = 1;
			return 0;
		}
	}
	if ((r->methods & RF_POST) && rq->method == HM_POST &&
	    (r->flags & RF_API) && rq->body_len == 0) {
		route_err(rs, 400, "nobody");
		rs->nostore = 1;
		return 0;
	}

	r->fn(rq, rs, env);
	if (r->flags & RF_API)
		rs->nostore = 1;
	return 0;
}

/* ------------------------------------------------------------ the header block */

static void app(char *out, size_t cap, size_t *o, const char *s)
{
	size_t l = strlen(s);

	if (*o + l + 1 > cap) {
		*o = cap + 1;             /* mark overflow; caller returns -1 */
		return;
	}
	memcpy(out + *o, s, l);
	*o += l;
	out[*o] = '\0';
}

static void appnum(char *out, size_t cap, size_t *o, uint32_t v)
{
	char d[12];
	size_t n = 0;

	if (v == 0) {
		d[n++] = '0';
	} else {
		char t[12];
		size_t k = 0;

		while (v > 0 && k < sizeof(t)) {
			t[k++] = (char)('0' + (v % 10u));
			v /= 10u;
		}
		while (k > 0)
			d[n++] = t[--k];
	}
	d[n] = '\0';
	app(out, cap, o, d);
}

int route_headers(const struct http_rsp *rs, char *out, size_t cap)
{
	size_t o = 0;
	uint32_t clen = (rs->fd >= 0) ? rs->fsize : (uint32_t)rs->blen;

	app(out, cap, &o, "HTTP/1.1 ");
	appnum(out, cap, &o, (uint32_t)rs->status);
	app(out, cap, &o, " ");
	app(out, cap, &o, http_reason(rs->status));
	app(out, cap, &o, "\r\n");

	/* SPEC-R7 section 7: these three on EVERY response, and there is no
	 * route that can skip them because no route writes this block. */
	app(out, cap, &o, "X-Frame-Options: DENY\r\n");
	app(out, cap, &o, "Content-Security-Policy: default-src 'self'\r\n");
	app(out, cap, &o, "X-Content-Type-Options: nosniff\r\n");
	app(out, cap, &o, "Connection: close\r\n");

	app(out, cap, &o, "Content-Type: ");
	app(out, cap, &o, rs->ctype != NULL ? rs->ctype : "application/json");
	app(out, cap, &o, "\r\n");

	app(out, cap, &o, "Content-Length: ");
	appnum(out, cap, &o, clen);
	app(out, cap, &o, "\r\n");

	if (rs->nostore)
		app(out, cap, &o, "Cache-Control: no-store\r\n");
	if (rs->retry_after > 0) {
		app(out, cap, &o, "Retry-After: ");
		appnum(out, cap, &o, rs->retry_after);
		app(out, cap, &o, "\r\n");
	}
	if (rs->allow_get_post)
		app(out, cap, &o, "Allow: GET, POST\r\n");
	if (rs->cookies[0] != '\0')
		app(out, cap, &o, rs->cookies);

	app(out, cap, &o, "\r\n");
	if (o > cap)
		return -1;
	return (int)o;
}
