/* src/httpd/http.c -- the bounded request parser declared in http.h.
 *
 * Shape: one switch over `ps->state`, one byte at a time for the two line
 * states and a bounded memcpy for the body.  There is no function in this file
 * that calls another function in this file except the small validators, and none
 * of them calls back, so the call graph is a tree two deep and the stack frame
 * of http_feed() is a constant.
 *
 * STRICTNESS THAT IS DELIBERATE, because a tolerant HTTP parser in front of
 * anything is a request-smuggling primitive:
 *   - CRLF only.  A bare LF, or a CR not followed by LF, is 400.
 *   - No obs-fold: a header line beginning with SP or HT is 400.
 *   - A second Content-Length, Transfer-Encoding, Cookie, X-RLX-CSRF or
 *     Content-Type header is 400, not a last-wins merge.
 *   - Any Transfer-Encoding at all is 501 (SPEC-R7: chunked -> 501).
 *   - origin-form targets only: the target must begin with '/'.  An
 *     absolute-form URI, an authority-form target and `*` are 400.
 *   - A body without Content-Length is 411; a Content-Length on a GET is 400.
 * The sweep in test_http.c truncates a valid request at every length and
 * corrupts single bytes across it looking for a path around one of these.
 */

#include "http.h"

#include <string.h>

/* ------------------------------------------------------------- small helpers */

static int ci_eq(const char *a, const char *b)
{
	/* ASCII case-insensitive compare of NUL-terminated strings. */
	while (*a != '\0' && *b != '\0') {
		int ca = (unsigned char)*a;
		int cb = (unsigned char)*b;

		if (ca >= 'A' && ca <= 'Z')
			ca += 32;
		if (cb >= 'A' && cb <= 'Z')
			cb += 32;
		if (ca != cb)
			return 0;
		a++;
		b++;
	}
	return *a == '\0' && *b == '\0';
}

static int hexdig(int c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

int http_is_hex32(const char *s)
{
	int i;

	for (i = 0; i < 32; i++) {
		if (hexdig((unsigned char)s[i]) < 0)
			return 0;
	}
	return s[32] == '\0';
}

const char *http_reason(int status)
{
	switch (status) {
	case 200: return "OK";
	case 204: return "No Content";
	case 400: return "Bad Request";
	case 401: return "Unauthorized";
	case 403: return "Forbidden";
	case 404: return "Not Found";
	case 405: return "Method Not Allowed";
	case 408: return "Request Timeout";
	case 411: return "Length Required";
	case 413: return "Payload Too Large";
	case 414: return "URI Too Long";
	case 429: return "Too Many Requests";
	case 431: return "Request Header Fields Too Large";
	case 500: return "Internal Server Error";
	case 501: return "Not Implemented";
	case 503: return "Service Unavailable";
	case 505: return "HTTP Version Not Supported";
	default:  return "Error";
	}
}

/* The fixed MIME table.  An extension that is not here is a 404: httpd will not
 * invent application/octet-stream for a file it cannot name, because a file it
 * cannot name should not be in the web root. */
const char *http_mime(const char *name)
{
	static const struct { const char *ext; const char *type; } tab[] = {
		{ ".html", "text/html; charset=utf-8" },
		{ ".css",  "text/css; charset=utf-8" },
		{ ".js",   "application/javascript; charset=utf-8" },
		{ ".txt",  "text/plain; charset=utf-8" },
		{ ".svg",  "image/svg+xml" },
		{ ".ico",  "image/x-icon" },
		{ ".png",  "image/png" }
	};
	size_t nl = strlen(name);
	unsigned i;

	for (i = 0; i < sizeof(tab) / sizeof(tab[0]); i++) {
		size_t el = strlen(tab[i].ext);

		if (nl > el && ci_eq(name + (nl - el), tab[i].ext))
			return tab[i].type;
	}
	return NULL;
}

/* ----------------------------------------------------- path decode + checks */

/* The only bytes a decoded path may hold.  Note what is absent: '%', '\\',
 * ':', '~', ' ' and every byte outside printable ASCII.  A '%' is absent on
 * purpose: it is what makes double-encoding impossible rather than merely
 * detected, because `%252e` decodes to a literal '%' and dies here. */
static int path_byte_ok(int c)
{
	if (c >= 'A' && c <= 'Z')
		return 1;
	if (c >= 'a' && c <= 'z')
		return 1;
	if (c >= '0' && c <= '9')
		return 1;
	return c == '/' || c == '.' || c == '_' || c == '-';
}

int http_decode_path(const char *target, size_t tlen, char *out, size_t cap)
{
	size_t i = 0;
	size_t o = 0;
	size_t seglen = 0;
	size_t segstart = 1;
	size_t nseg = 0;

	if (cap < 2)
		return -500;
	if (tlen == 0)
		return -400;
	if (target[0] != '/')
		return -400;              /* origin-form only */

	out[o++] = '/';
	i = 1;

	for (; i < tlen; i++) {
		int c = (unsigned char)target[i];

		if (c == '?')
			break;                /* the query is not part of the path */

		if (c == '%') {
			int h, l;

			if (tlen - i < 3)
				return -400;
			h = hexdig((unsigned char)target[i + 1]);
			l = hexdig((unsigned char)target[i + 2]);
			if (h < 0 || l < 0)
				return -400;
			c = (h << 4) | l;
			i += 2;
			if (c == 0x00)
				return -400;  /* NUL injection */
			if (c == '/' || c == '\\' || c == '%')
				return -400;  /* encoded separator or re-encode */
			if (!path_byte_ok(c))
				return -400;
		} else if (!path_byte_ok(c)) {
			return -400;          /* includes '\\', ' ', 0x00, >= 0x80 */
		}

		if (c == '/') {
			if (seglen == 0)
				return -400;  /* "//" or a leading empty segment */
			if (seglen == 1 && out[segstart] == '.')
				return -400;  /* "." */
			if (seglen == 2 && out[segstart] == '.' &&
			    out[segstart + 1] == '.')
				return -400;  /* ".." */
			nseg++;
			if (nseg > 2)
				return -400;  /* this server is two deep */
			seglen = 0;
			if (o + 1 >= cap)
				return -414;
			out[o++] = '/';
			segstart = o;
			continue;
		}

		if (o + 1 >= cap)
			return -414;
		out[o++] = (char)c;
		seglen++;
		if (seglen > HTTP_NAME_MAX)
			return -414;
	}

	/* the last segment, which has no '/' after it to trigger the check */
	if (seglen == 1 && out[segstart] == '.')
		return -400;
	if (seglen == 2 && out[segstart] == '.' && out[segstart + 1] == '.')
		return -400;
	if (seglen == 0 && o > 1)
		return -400;                  /* a trailing '/' is not a resource */
	if (seglen > 0) {
		nseg++;
		if (nseg > 2)
			return -400;
	}

	out[o] = '\0';
	/* Two independent readings of the same refusal: the segment walk above
	 * cannot leave a ".." behind, and this one says so about the whole
	 * string.  It is cheap, and it is the check a reader can verify. */
	if (strstr(out, "..") != NULL)
		return -400;
	if (strstr(out, "//") != NULL)
		return -400;
	return (int)o;
}

/* ------------------------------------------------------------- request line */

static int parse_reqline(struct http_parser *ps)
{
	char *s = ps->line;
	size_t n = ps->linelen;
	size_t i = 0;
	size_t mstart, mlen, tstart, tlen;
	int rc;

	/* METHOD SP TARGET SP HTTP/1.x -- exactly one space between each. */
	mstart = 0;
	while (i < n && s[i] != ' ')
		i++;
	mlen = i - mstart;
	if (i >= n)
		return -400;
	i++;                                  /* the single space */
	tstart = i;
	while (i < n && s[i] != ' ')
		i++;
	tlen = i - tstart;
	if (i >= n)
		return -400;                  /* HTTP/0.9 has no version: refuse */
	i++;

	if (n - i != 8)
		return -400;
	if (memcmp(s + i, "HTTP/1.", 7) != 0) {
		if (memcmp(s + i, "HTTP/", 5) == 0)
			return -505;
		return -400;
	}
	if (s[i + 7] == '0')
		ps->r->ver_minor = 0;
	else if (s[i + 7] == '1')
		ps->r->ver_minor = 1;
	else
		return -505;

	if (mlen == 3 && memcmp(s + mstart, "GET", 3) == 0)
		ps->r->method = HM_GET;
	else if (mlen == 4 && memcmp(s + mstart, "POST", 4) == 0)
		ps->r->method = HM_POST;
	else if (mlen == 0)
		return -400;
	else
		return -405;                  /* a known-shape method we do not do */

	if (tlen == 0)
		return -400;
	if (tlen > HTTP_REQLINE_MAX)
		return -414;

	rc = http_decode_path(s + tstart, tlen, ps->r->path, sizeof(ps->r->path));
	if (rc < 0)
		return rc;
	ps->r->pathlen = (uint16_t)rc;
	return 0;
}

/* ------------------------------------------------------------------ headers */

/* Copy a 32-hex token out of a cookie or header value.  Anything that is not
 * exactly 32 hex digits leaves the destination empty: a malformed token is an
 * absent token, never a truncated one. */
static void take_tok32(char *dst, const char *val, size_t vlen)
{
	dst[0] = '\0';
	if (vlen != 32)
		return;
	memcpy(dst, val, 32);
	dst[32] = '\0';
	if (!http_is_hex32(dst))
		dst[0] = '\0';
}

/* Cookie: NAME=VALUE pairs separated by "; ".  Only two names are looked for and
 * everything else is ignored; no cookie value is ever stored unvalidated. */
static void parse_cookie(struct http_req *r, const char *v, size_t n)
{
	size_t i = 0;

	while (i < n) {
		size_t ks, ke, vs, ve;

		while (i < n && (v[i] == ' ' || v[i] == '\t' || v[i] == ';'))
			i++;
		ks = i;
		while (i < n && v[i] != '=' && v[i] != ';')
			i++;
		ke = i;
		if (i >= n || v[i] != '=') {
			while (i < n && v[i] != ';')
				i++;
			continue;
		}
		i++;
		vs = i;
		while (i < n && v[i] != ';')
			i++;
		ve = i;

		if (ke - ks == 4 && memcmp(v + ks, "rlxs", 4) == 0)
			take_tok32(r->sess, v + vs, ve - vs);
		else if (ke - ks == 4 && memcmp(v + ks, "rlxc", 4) == 0)
			take_tok32(r->ccsrf, v + vs, ve - vs);
	}
}

static int parse_u32_strict(const char *s, size_t n, uint32_t *out)
{
	uint32_t v = 0;
	size_t i;

	if (n == 0 || n > 10)
		return -1;
	for (i = 0; i < n; i++) {
		unsigned d;

		if (s[i] < '0' || s[i] > '9')
			return -1;
		d = (unsigned)(s[i] - '0');
		if (v > 429496729u || (v == 429496729u && d > 5u))
			return -1;
		v = v * 10u + d;
	}
	*out = v;
	return 0;
}

static int parse_header(struct http_parser *ps)
{
	char *s = ps->line;
	size_t n = ps->linelen;
	size_t i = 0;
	size_t nlen, vs, vlen;
	char name[64];

	if (n > 0 && (s[0] == ' ' || s[0] == '\t'))
		return -400;                  /* obs-fold */

	while (i < n && s[i] != ':')
		i++;
	if (i == 0 || i >= n)
		return -400;
	nlen = i;
	i++;                                  /* past ':' */
	while (i < n && (s[i] == ' ' || s[i] == '\t'))
		i++;
	vs = i;
	vlen = n - vs;
	while (vlen > 0 && (s[vs + vlen - 1] == ' ' || s[vs + vlen - 1] == '\t'))
		vlen--;

	if (nlen >= sizeof(name))
		return 0;                     /* a name we cannot hold is not ours */
	memcpy(name, s, nlen);
	name[nlen] = '\0';

	if (ci_eq(name, "content-length")) {
		uint32_t v;

		if (ps->seen_clen)
			return -400;
		ps->seen_clen = 1;
		if (parse_u32_strict(s + vs, vlen, &v) != 0)
			return -400;
		if (v > HTTP_BODY_MAX)
			return -413;
		ps->r->has_clen = 1;
		ps->r->clen = v;
	} else if (ci_eq(name, "transfer-encoding")) {
		if (ps->seen_te)
			return -400;
		ps->seen_te = 1;
		ps->r->chunked = 1;
		return -501;                  /* SPEC-R7: chunked -> 501 */
	} else if (ci_eq(name, "cookie")) {
		if (ps->seen_cookie)
			return -400;
		ps->seen_cookie = 1;
		parse_cookie(ps->r, s + vs, vlen);
	} else if (ci_eq(name, "x-rlx-csrf")) {
		if (ps->seen_csrf)
			return -400;
		ps->seen_csrf = 1;
		take_tok32(ps->r->hcsrf, s + vs, vlen);
	} else if (ci_eq(name, "content-type")) {
		size_t l = vlen;

		if (ps->seen_ctype)
			return -400;
		ps->seen_ctype = 1;
		/* Only the media type is looked at, and only for one value. */
		if (l >= 16 && memcmp(s + vs, "application/json", 16) == 0)
			ps->r->is_json = 1;
	}
	return 0;
}

/* ------------------------------------------------------------------ feeding */

void http_parse_init(struct http_parser *ps, struct http_req *r)
{
	memset(ps, 0, sizeof(*ps));
	memset(r, 0, sizeof(*r));
	ps->state = HS_REQLINE;
	ps->status = 400;
	ps->r = r;
}

static int end_of_headers(struct http_parser *ps)
{
	struct http_req *r = ps->r;

	if (r->chunked)
		return -501;
	if (r->method == HM_POST) {
		if (!r->has_clen)
			return -411;
		if (r->clen > HTTP_BODY_MAX)
			return -413;
		if (r->clen == 0) {
			ps->state = HS_DONE;
			return 1;
		}
		ps->state = HS_BODY;
		return 0;
	}
	/* GET: a Content-Length is refused rather than ignored, because
	 * "ignored" is how a request gets read twice by two parsers. */
	if (r->has_clen && r->clen != 0)
		return -400;
	ps->state = HS_DONE;
	return 1;
}

int http_feed(struct http_parser *ps, const uint8_t *p, size_t n, size_t *used)
{
	size_t i = 0;

	*used = 0;
	if (ps->state == HS_ERR)
		return -ps->status;
	if (ps->state == HS_DONE)
		return 1;

	while (i < n) {
		if (ps->state == HS_BODY) {
			size_t want = ps->r->clen - ps->bodygot;
			size_t have = n - i;
			size_t take = (have < want) ? have : want;

			/* clen was bounded by HTTP_BODY_MAX when it was parsed,
			 * and bodygot never passes clen, so this cannot pass the
			 * end of r->body.  Asserted again here anyway. */
			if (ps->bodygot + take > HTTP_BODY_MAX) {
				ps->state = HS_ERR;
				ps->status = 413;
				*used = i;
				return -413;
			}
			memcpy(ps->r->body + ps->bodygot, p + i, take);
			ps->bodygot += (uint32_t)take;
			i += take;
			if (ps->bodygot == ps->r->clen) {
				ps->r->body_len = ps->bodygot;
				ps->r->body[ps->bodygot] = '\0';
				ps->state = HS_DONE;
				*used = i;
				return 1;
			}
			continue;
		}

		{
			int c = (int)p[i++];
			int rc;
			int in_reqline;
			size_t cap;

			if (ps->saw_cr) {
				ps->saw_cr = 0;
				if (c != '\n') {
					ps->state = HS_ERR;
					ps->status = 400;
					*used = i;
					return -400;
				}
				/* a complete line sits in ps->line[0..linelen) */
				if (ps->state == HS_REQLINE) {
					ps->hdrbytes += ps->linelen + 2;
					rc = parse_reqline(ps);
					if (rc < 0) {
						ps->state = HS_ERR;
						ps->status = -rc;
						*used = i;
						return rc;
					}
					ps->state = HS_HEADERS;
					ps->linelen = 0;
					continue;
				}
				ps->hdrbytes += ps->linelen + 2;
				if (ps->hdrbytes > HTTP_HDR_BYTES_MAX) {
					ps->state = HS_ERR;
					ps->status = 431;
					*used = i;
					return -431;
				}
				if (ps->linelen == 0) {
					rc = end_of_headers(ps);
					if (rc < 0) {
						ps->state = HS_ERR;
						ps->status = -rc;
						*used = i;
						return rc;
					}
					if (rc == 1) {
						*used = i;
						return 1;
					}
					continue;
				}
				ps->nhdr++;
				if (ps->nhdr > HTTP_HDR_LINES_MAX) {
					ps->state = HS_ERR;
					ps->status = 431;
					*used = i;
					return -431;
				}
				rc = parse_header(ps);
				if (rc < 0) {
					ps->state = HS_ERR;
					ps->status = -rc;
					*used = i;
					return rc;
				}
				ps->linelen = 0;
				continue;
			}

			if (c == '\r') {
				ps->saw_cr = 1;
				continue;
			}
			if (c == '\n') {
				ps->state = HS_ERR;   /* bare LF */
				ps->status = 400;
				*used = i;
				return -400;
			}
			if (c == 0x00) {
				ps->state = HS_ERR;
				ps->status = 400;
				*used = i;
				return -400;
			}

			in_reqline = (ps->state == HS_REQLINE);
			cap = in_reqline ? HTTP_REQLINE_MAX : HTTP_LINE_MAX;
			if (ps->linelen >= cap) {
				/* 414 for the target, 431 for a header field: the
				 * two limits answer with different statuses even
				 * though today they are the same number. */
				ps->state = HS_ERR;
				ps->status = in_reqline ? 414 : 431;
				*used = i;
				return -ps->status;
			}
			/* One header line may not be longer than the whole header
			 * budget either; hdrbytes is only added at end of line, so
			 * the running total is checked here too. */
			if (!in_reqline &&
			    ps->hdrbytes + ps->linelen + 2 > HTTP_HDR_BYTES_MAX) {
				ps->state = HS_ERR;
				ps->status = 431;
				*used = i;
				return -431;
			}
			ps->line[ps->linelen++] = (char)c;
			ps->line[ps->linelen] = '\0';
		}
	}

	*used = i;
	return 0;
}

int http_parse_all(const uint8_t *p, size_t n, struct http_req *r)
{
	struct http_parser ps;
	size_t used = 0;
	int rc;

	http_parse_init(&ps, r);
	rc = http_feed(&ps, p, n, &used);
	if (rc == 0)
		return -400;                  /* truncated: incomplete is refused */
	return rc;
}
