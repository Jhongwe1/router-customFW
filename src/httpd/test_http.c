/* src/httpd/test_http.c -- the request-parser sweep and the traversal battery.
 *
 * Three things are being asked here, and only the first is about a single input:
 *
 *  1. Does the parser answer the right status for each malformed shape?
 *  2. TRUNCATION: fed the first L bytes of a valid request, for every L, does it
 *     ever say "complete" before it is, and does it ever read past L?  (The second
 *     half of that question is ASAN's, so this file is only useful under it.)
 *  3. CORRUPTION: with one byte of a valid request replaced, is the result either
 *     a refusal or the SAME request?  A parser that quietly accepts a corrupted
 *     Content-Length, or a second Cookie header, or a NUL in a token, is how two
 *     parsers in a chain come to disagree about where a request ends.
 *
 * The traversal battery is a separate list of thirty targets.  Every one must be
 * refused by http_decode_path(), and the positive control -- that
 * `/static/style.css` decodes and is SERVED -- is in test_routes.c, where a real
 * file exists to serve.  A battery without that control proves only that the
 * function can say no.
 *
 * Mutation controls, run by `make mutate`: removing the ".." refusal must make the
 * traversal battery red, and removing the header-count cap must make the sweep
 * red.  If either stays green the file is not testing what it says.
 */

#include "http.h"
#include "testlib.h"

#include <string.h>

/* A valid POST with every header the program looks at.  The sweep and the
 * corruption loop both work over this. */
static const char REQ[] =
	"POST /api/config HTTP/1.1\r\n"
	"Host: 10.1.1.1\r\n"
	"Cookie: rlxs=0123456789abcdef0123456789abcdef; "
		"rlxc=fedcba9876543210fedcba9876543210\r\n"
	"X-RLX-CSRF: fedcba9876543210fedcba9876543210\r\n"
	"Content-Type: application/json\r\n"
	"Content-Length: 27\r\n"
	"\r\n"
	"{\"sys.hostname\":\"router-1\"}";

#define REQLEN (sizeof(REQ) - 1)
#define BODYLEN 27
#define BODYOFF (REQLEN - BODYLEN)

static int parse_str(const char *s, struct http_req *r)
{
	return http_parse_all((const uint8_t *)s, strlen(s), r);
}

static void case_status(const char *req, int want, const char *name)
{
	struct http_req r;
	int rc = parse_str(req, &r);

	t_okf(rc == -want, name, rc, -want);
}

/* Every target in the battery must come back negative.  The status is checked
 * too, because 414 for an overlong name and 400 for a dot segment are different
 * findings and collapsing them would hide one of them moving. */
static void refuse_path(const char *target, const char *name)
{
	char out[HTTP_PATH_MAX];
	int rc = http_decode_path(target, strlen(target), out, sizeof(out));

	t_okf(rc < 0, name, rc, -1);
}

int main(void)
{
	struct http_req ref, r;
	size_t cut, off;
	unsigned k;
	int accepted_early = 0;
	int crashed = 0;
	int sweep_cases = 0;
	int corrupt_cases = 0;
	int corrupt_differed = 0;
	char buf[8192];
	char path[HTTP_PATH_MAX];

	/* ------------------------------------------------- the reference parse */
	t_okf(parse_str(REQ, &ref) == 1, "the reference request parses",
	      parse_str(REQ, &ref), 1);
	t_okf(ref.method == HM_POST, "method POST", ref.method, HM_POST);
	t_ok(strcmp(ref.path, "/api/config") == 0, "path", ref.path);
	t_okf(ref.clen == BODYLEN, "Content-Length", (long)ref.clen, BODYLEN);
	t_okf(ref.body_len == BODYLEN, "body length", (long)ref.body_len, BODYLEN);
	t_ok(strcmp(ref.sess, "0123456789abcdef0123456789abcdef") == 0,
	     "session cookie", ref.sess);
	t_ok(strcmp(ref.ccsrf, "fedcba9876543210fedcba9876543210") == 0,
	     "csrf cookie", ref.ccsrf);
	t_ok(strcmp(ref.hcsrf, "fedcba9876543210fedcba9876543210") == 0,
	     "csrf header", ref.hcsrf);
	t_okf(ref.is_json == 1, "Content-Type recognised", ref.is_json, 1);

	/* --------------------------------------------------- the shape refusals */
	{
		struct http_req g;

		t_okf(parse_str("GET / HTTP/1.1\r\n\r\n", &g) == 1,
		      "a bare GET with no headers", 0, 1);
		t_okf(parse_str("GET / HTTP/1.0\r\n\r\n", &g) == 1,
		      "HTTP/1.0 is accepted", 0, 1);
	}
	case_status("GET /\r\n\r\n", 400, "HTTP/0.9 (no version) refused");
	case_status("GET / HTTP/2.0\r\n\r\n", 505, "HTTP/2.0 refused with 505");
	case_status("GET / HTTP/1.9\r\n\r\n", 505, "HTTP/1.9 refused with 505");
	case_status("GET / XTTP/1.1\r\n\r\n", 400, "a non-HTTP version token");
	case_status("PUT / HTTP/1.1\r\n\r\n", 405, "PUT refused with 405");
	case_status("HEAD / HTTP/1.1\r\n\r\n", 405, "HEAD refused with 405");
	case_status("OPTIONS / HTTP/1.1\r\n\r\n", 405, "OPTIONS refused with 405");
	case_status(" / HTTP/1.1\r\n\r\n", 400, "an empty method");
	case_status("GET  / HTTP/1.1\r\n\r\n", 400, "two spaces after the method");
	case_status("GET /  HTTP/1.1\r\n\r\n", 400, "two spaces before the version");
	case_status("GET * HTTP/1.1\r\n\r\n", 400, "asterisk-form target");
	case_status("GET http://x/y HTTP/1.1\r\n\r\n", 400, "absolute-form target");
	case_status("GET / HTTP/1.1\n\n", 400, "a bare LF ends nothing");
	case_status("GET / HTTP/1.1\r\r\n", 400, "a CR not followed by LF");
	case_status("GET / HTTP/1.1\r\n Host: x\r\n\r\n", 400,
		    "an obs-fold continuation line");
	case_status("GET / HTTP/1.1\r\nHost\r\n\r\n", 400, "a header with no colon");
	case_status("GET / HTTP/1.1\r\n: x\r\n\r\n", 400, "a header with no name");
	case_status("POST /api/login HTTP/1.1\r\n\r\n", 411,
		    "a POST with no Content-Length");
	case_status("POST /api/login HTTP/1.1\r\nContent-Length: 4097\r\n\r\n", 413,
		    "Content-Length over the body cap");
	case_status("POST /api/login HTTP/1.1\r\nContent-Length: 4\r\n"
		    "Content-Length: 5\r\n\r\nabcd", 400,
		    "two Content-Length headers");
	case_status("POST /api/login HTTP/1.1\r\nContent-Length: +4\r\n\r\nabcd",
		    400, "a signed Content-Length");
	case_status("POST /api/login HTTP/1.1\r\nContent-Length: 0x4\r\n\r\nabcd",
		    400, "a hex Content-Length");
	{
		struct http_req g;

		t_okf(parse_str("POST /api/login HTTP/1.1\r\n"
				"Content-Length: 4 \r\n\r\nabcd", &g) == 1,
		      "a trailing space in Content-Length is trimmed", 0, 1);
	}
	case_status("POST /api/login HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n",
		    501, "chunked refused with 501");
	case_status("POST /api/login HTTP/1.1\r\nTransfer-Encoding: identity\r\n\r\n",
		    501, "any Transfer-Encoding refused with 501");
	case_status("GET / HTTP/1.1\r\nContent-Length: 4\r\n\r\nabcd", 400,
		    "a GET with a body");
	case_status("GET / HTTP/1.1\r\nCookie: a=b\r\nCookie: c=d\r\n\r\n", 400,
		    "two Cookie headers");
	case_status("GET / HTTP/1.1\r\nX-RLX-CSRF: a\r\nX-RLX-CSRF: b\r\n\r\n", 400,
		    "two X-RLX-CSRF headers");

	/* A NUL byte anywhere in the head. */
	{
		static const char req[] = "GET /\0 HTTP/1.1\r\n\r\n";

		t_okf(http_parse_all((const uint8_t *)req, sizeof(req) - 1, &r)
		      == -400, "a NUL in the request line", 0, -400);
	}

	/* The three counted limits, each at the boundary and one past it. */
	{
		size_t n = 0;

		memcpy(buf, "GET /", 5);
		n = 5;
		while (n < 1024)
			buf[n++] = 'a';
		memcpy(buf + n, " HTTP/1.1\r\n\r\n", 13);
		n += 13;
		t_okf(http_parse_all((const uint8_t *)buf, n, &r) == -414,
		      "a request line at the 1024-byte cap", 0, -414);
	}
	{
		size_t n = 0;
		unsigned i;

		memcpy(buf, "GET / HTTP/1.1\r\n", 16);
		n = 16;
		for (i = 0; i < HTTP_HDR_LINES_MAX; i++)
			n += (size_t)snprintf(buf + n, sizeof(buf) - n,
					      "X-H%u: v\r\n", i);
		memcpy(buf + n, "\r\n", 2);
		n += 2;
		t_okf(http_parse_all((const uint8_t *)buf, n, &r) == 1,
		      "exactly 32 header lines is accepted", 0, 1);

		n = 16;
		for (i = 0; i < HTTP_HDR_LINES_MAX + 1; i++)
			n += (size_t)snprintf(buf + n, sizeof(buf) - n,
					      "X-H%u: v\r\n", i);
		memcpy(buf + n, "\r\n", 2);
		n += 2;
		t_okf(http_parse_all((const uint8_t *)buf, n, &r) == -431,
		      "33 header lines is refused with 431", 0, -431);
	}
	{
		size_t n = 16;
		unsigned i;

		/* Long-but-few headers: the 4096-byte total, not the line count. */
		memcpy(buf, "GET / HTTP/1.1\r\n", 16);
		for (i = 0; i < 8; i++) {
			memcpy(buf + n, "X-Pad: ", 7);
			n += 7;
			memset(buf + n, 'p', 600);
			n += 600;
			memcpy(buf + n, "\r\n", 2);
			n += 2;
		}
		memcpy(buf + n, "\r\n", 2);
		n += 2;
		t_okf(http_parse_all((const uint8_t *)buf, n, &r) == -431,
		      "over 4096 bytes of headers is refused with 431", 0, -431);
	}

	/* A body that arrives in two feeds, and a body longer than announced. */
	{
		struct http_parser ps;
		size_t used = 0;
		int rc;

		http_parse_init(&ps, &r);
		rc = http_feed(&ps, (const uint8_t *)REQ, BODYOFF + 10, &used);
		t_okf(rc == 0, "a request split mid-body needs more", rc, 0);
		rc = http_feed(&ps, (const uint8_t *)REQ + BODYOFF + 10,
			       REQLEN - BODYOFF - 10, &used);
		t_okf(rc == 1, "the second feed completes it", rc, 1);
		t_ok(memcmp(r.body, REQ + BODYOFF, BODYLEN) == 0,
		     "the reassembled body is the original", NULL);
	}
	{
		struct http_parser ps;
		size_t used = 0;
		int rc;

		http_parse_init(&ps, &r);
		memcpy(buf, REQ, REQLEN);
		memcpy(buf + REQLEN, "EXTRA-BYTES-AFTER-THE-BODY", 26);
		rc = http_feed(&ps, (const uint8_t *)buf, REQLEN + 26, &used);
		t_okf(rc == 1, "trailing bytes do not extend the body", rc, 1);
		t_okf(used == REQLEN, "and are not consumed", (long)used,
		      (long)REQLEN);
		t_okf(r.body_len == BODYLEN, "body still 27 bytes",
		      (long)r.body_len, BODYLEN);
	}

	/* ----------------------------------------- 2. truncation at every length */
	for (cut = 0; cut < REQLEN; cut++) {
		struct http_parser ps;
		size_t used = 0;
		int rc;

		http_parse_init(&ps, &r);
		rc = http_feed(&ps, (const uint8_t *)REQ, cut, &used);
		sweep_cases++;
		if (rc == 1)
			accepted_early++;
		if (rc > 1 || rc < -600)
			crashed++;
	}
	t_okf(accepted_early == 0,
	      "no proper prefix of the request is reported complete",
	      accepted_early, 0);
	t_okf(crashed == 0, "no prefix produced a status outside the table",
	      crashed, 0);

	/* --------------------------------------- 3. single-byte corruption sweep
	 *
	 * The obvious invariant -- "accepted implies identical to the reference"
	 * -- is FALSE, and finding that out was worth the run: flipping a hex
	 * digit of the session cookie produces a different, perfectly valid
	 * session, and shortening Content-Length produces a shorter, perfectly
	 * valid body.  779 of 1,545 corruptions were accepted-and-different on
	 * the first run.  A test that demanded identity would have to be relaxed
	 * to pass, which is the one thing not allowed.
	 *
	 * So the invariant is stated per REGION instead: a corruption inside one
	 * header may change only the fields that header feeds.  That is the
	 * property that matters -- a byte in `Host:` must not be able to change
	 * the session, and a byte in the body must not be able to change the path
	 * -- and it is strictly stronger than "does not crash".  The regions are
	 * found by searching REQ, so editing REQ cannot silently misalign them.
	 */
	{
		static const unsigned char subs[] = { 0x00, 0x0a, 0x0d, 0x20,
						      0x25, 0x2f, 0x41, 0xff };
		/* field bits */
#define F_LINE  0x01   /* method, ver_minor, path, pathlen */
#define F_CLEN  0x02   /* has_clen, clen, body_len (and so the body) */
#define F_SESS  0x04
#define F_CCSRF 0x08
#define F_HCSRF 0x10
#define F_CTYPE 0x20
#define F_BODY  0x40
		struct region { size_t lo, hi; unsigned allow; const char *name; };
		struct region reg[7];
		size_t nreg = 0;
		const char *p;
		int outside = 0;
		const char *worst = "none";

		p = strstr(REQ, "\r\n");
		reg[nreg].lo = 0;
		reg[nreg].hi = (size_t)(p - REQ) + 2;
		reg[nreg].allow = F_LINE;
		reg[nreg].name = "request line";
		nreg++;
		{
			static const struct { const char *hdr; unsigned allow;
					      const char *name; } hs[] = {
				{ "Host:", 0, "Host (ignored entirely)" },
				{ "Cookie:", F_SESS | F_CCSRF, "Cookie" },
				{ "X-RLX-CSRF:", F_HCSRF, "X-RLX-CSRF" },
				{ "Content-Type:", F_CTYPE, "Content-Type" },
				{ "Content-Length:", F_CLEN | F_BODY,
				  "Content-Length" }
			};
			unsigned h;

			for (h = 0; h < sizeof(hs) / sizeof(hs[0]); h++) {
				const char *s = strstr(REQ, hs[h].hdr);
				const char *e;

				if (s == NULL)
					continue;
				e = strstr(s, "\r\n");
				reg[nreg].lo = (size_t)(s - REQ);
				reg[nreg].hi = (size_t)(e - REQ) + 2;
				reg[nreg].allow = hs[h].allow;
				reg[nreg].name = hs[h].name;
				nreg++;
			}
		}
		reg[nreg].lo = BODYOFF;
		reg[nreg].hi = REQLEN;
		reg[nreg].allow = F_BODY;
		reg[nreg].name = "body";
		nreg++;

		for (off = 0; off < REQLEN; off++) {
			unsigned allow = 0;
			unsigned ri;
			int known = 0;

			for (ri = 0; ri < nreg; ri++) {
				if (off >= reg[ri].lo && off < reg[ri].hi) {
					allow = reg[ri].allow;
					known = 1;
					break;
				}
			}
			/* the blank line between headers and body belongs to no
			 * header; a corruption there must be refused outright */
			if (!known)
				allow = 0;

			for (k = 0; k < sizeof(subs); k++) {
				struct http_req c;
				unsigned diff = 0;
				int rc;

				memcpy(buf, REQ, REQLEN);
				if ((unsigned char)buf[off] == subs[k])
					continue;
				buf[off] = (char)subs[k];
				rc = http_parse_all((const uint8_t *)buf, REQLEN,
						    &c);
				corrupt_cases++;
				if (rc != 1)
					continue;       /* refused: always fine */
				if (c.method != ref.method ||
				    c.ver_minor != ref.ver_minor ||
				    c.pathlen != ref.pathlen ||
				    strcmp(c.path, ref.path) != 0)
					diff |= F_LINE;
				if (c.has_clen != ref.has_clen ||
				    c.clen != ref.clen)
					diff |= F_CLEN;
				if (strcmp(c.sess, ref.sess) != 0)
					diff |= F_SESS;
				if (strcmp(c.ccsrf, ref.ccsrf) != 0)
					diff |= F_CCSRF;
				if (strcmp(c.hcsrf, ref.hcsrf) != 0)
					diff |= F_HCSRF;
				if (c.is_json != ref.is_json)
					diff |= F_CTYPE;
				if (c.body_len != ref.body_len ||
				    memcmp(c.body, ref.body, ref.body_len) != 0)
					diff |= F_BODY;
				if (diff & ~allow) {
					corrupt_differed++;
					if (!outside) {
						worst = "see offset below";
						(void)printf("# first out-of-region"
							     " difference at off"
							     " %lu sub 0x%02x:"
							     " diff 0x%02x allow"
							     " 0x%02x\n",
							     (unsigned long)off,
							     subs[k], diff, allow);
					}
					outside = 1;
				}
				/* Structural invariants, for every accepted parse
				 * regardless of region. */
				if (c.pathlen != strlen(c.path) ||
				    c.path[0] != '/' ||
				    c.clen > HTTP_BODY_MAX ||
				    c.body_len != c.clen ||
				    (c.sess[0] != '\0' && !http_is_hex32(c.sess)) ||
				    (c.hcsrf[0] != '\0' &&
				     !http_is_hex32(c.hcsrf)) ||
				    (c.ccsrf[0] != '\0' &&
				     !http_is_hex32(c.ccsrf)))
					crashed++;
			}
		}
		(void)worst;
	}
	t_okf(corrupt_differed == 0,
	      "no corruption changed a field outside the region it lies in",
	      corrupt_differed, 0);
	t_okf(crashed == 0,
	      "every accepted parse held the structural invariants", crashed, 0);
	t_ok(corrupt_cases > 1200, "the corruption sweep ran its cases", NULL);
	(void)printf("# sweep: %d truncations, %d corruptions\n",
		     sweep_cases, corrupt_cases);

	/* ------------------------------------------- the traversal battery (30) */
	refuse_path("/static/../etc/passwd", "T01 plain ..");
	refuse_path("/static/%2e%2e/etc/passwd", "T02 encoded .. lower");
	refuse_path("/static/%2E%2E/etc/passwd", "T03 encoded .. upper");
	refuse_path("/static/..%2fetc/passwd", "T04 encoded slash after ..");
	refuse_path("/static/%2e%2e%2fetc/passwd", "T05 both encoded");
	refuse_path("/static/%252e%252e/etc", "T06 double-encoded ..");
	refuse_path("/static/%25%32%65%25%32%65/etc", "T07 triple-encoded ..");
	refuse_path("/static/..%5cetc", "T08 encoded backslash");
	refuse_path("/static/..\\etc", "T09 raw backslash");
	refuse_path("/static/%00", "T10 encoded NUL alone");
	refuse_path("/static/style.css%00.txt", "T11 NUL truncation");
	refuse_path("/../index.html", "T12 .. above the root");
	refuse_path("//etc/passwd", "T13 empty first segment");
	refuse_path("/static//style.css", "T14 empty middle segment");
	refuse_path("../index.html", "T15 no leading slash");
	refuse_path("/static/.", "T16 a single dot segment");
	refuse_path("/static/..", "T17 a trailing .. segment");
	refuse_path("/static/./style.css", "T18 a dot segment mid-path");
	refuse_path("/static/%2f%2e%2e%2fstyle.css", "T19 all separators encoded");
	refuse_path("/static/style.css/../../etc/passwd", "T20 .. after a file");
	refuse_path("/static/%u002e%u002e/", "T21 IIS-style %u escape");
	refuse_path("/static/..;/etc", "T22 a semicolon parameter");
	refuse_path("/static/\\..\\..\\etc", "T23 all backslashes");
	refuse_path("/static/..%00/etc", "T24 NUL inside a .. segment");
	refuse_path("/static/ ..", "T25 a raw space");
	refuse_path("/static/%", "T26 a bare percent");
	refuse_path("/static/%2", "T27 a one-digit percent");
	refuse_path("/static/%zz", "T28 a non-hex percent");
	refuse_path("/static/a/b/c", "T29 three segments deep");
	refuse_path("/static/style.css/", "T30 a trailing slash");
	{
		/* an overlong name: 400 or 414, never accepted */
		size_t n = 0;

		memcpy(buf, "/static/", 8);
		n = 8;
		while (n < 300)
			buf[n++] = 'a';
		buf[n] = '\0';
		t_ok(http_decode_path(buf, n, path, sizeof(path)) < 0,
		     "T31 a 292-byte name", NULL);
	}
	refuse_path("/static/\x80\x81", "T32 bytes above 0x7f");
	refuse_path("/static/..%c0%af", "T33 the overlong UTF-8 slash");
	refuse_path("/api/config/../status", "T34 .. inside the API space");

	/* The decode side's positive controls: legitimate targets survive, and the
	 * query string is dropped rather than becoming part of the path. */
	t_ok(http_decode_path("/static/style.css", 17, path, sizeof(path)) == 17 &&
	     strcmp(path, "/static/style.css") == 0,
	     "P1 /static/style.css decodes unchanged", path);
	t_ok(http_decode_path("/", 1, path, sizeof(path)) == 1 &&
	     strcmp(path, "/") == 0, "P2 the root decodes", path);
	t_ok(http_decode_path("/api/status?x=1", 15, path, sizeof(path)) == 11 &&
	     strcmp(path, "/api/status") == 0, "P3 the query is dropped", path);
	t_ok(http_decode_path("/static/a%2Db.css", 17, path, sizeof(path)) == 15 &&
	     strcmp(path, "/static/a-b.css") == 0,
	     "P4 a harmless percent escape decodes", path);
	t_ok(http_decode_path("/static/.hidden", 15, path, sizeof(path)) == 15,
	     "P5 a leading dot in a name is not a dot segment", path);

	/* the MIME table, including the refusal that makes it a table */
	t_ok(http_mime("style.css") != NULL, "MIME .css", NULL);
	t_ok(http_mime("index.html") != NULL, "MIME .html", NULL);
	t_ok(http_mime("app.js") != NULL, "MIME .js", NULL);
	t_ok(http_mime("x.cgi") == NULL, "MIME .cgi is not in the table", NULL);
	t_ok(http_mime("x.sh") == NULL, "MIME .sh is not in the table", NULL);
	t_ok(http_mime("noext") == NULL, "MIME no extension", NULL);
	t_ok(http_mime(".css") == NULL, "MIME a bare extension is not a name", NULL);

	/* the 32-hex token check */
	t_ok(http_is_hex32("0123456789abcdef0123456789abcdef"), "hex32 accepts",
	     NULL);
	t_ok(!http_is_hex32("0123456789abcdef0123456789abcde"), "hex32 too short",
	     NULL);
	t_ok(!http_is_hex32("0123456789abcdef0123456789abcdefx"), "hex32 too long",
	     NULL);
	t_ok(!http_is_hex32("0123456789abcdef0123456789abcdeg"), "hex32 non-hex",
	     NULL);

	return t_done(100);
}
