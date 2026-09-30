/* src/httpd/test_routes.c -- the route matrix, the broker status mapping, the
 * headers, and the traversal battery's positive control.
 *
 * bk_call() is replaced here by a programmable fake, so a route's behaviour can be
 * separated from a broker's.  The fake counts its calls, which is what makes the
 * rate-limit case a real test: a refused login must answer 429 AND the broker must
 * not have been called at all (plan D8 v6 ruling 2 -- the limiter runs before the
 * KDF, on this side).
 *
 * The matrix is every route x (session absent, present) x (CSRF absent, wrong,
 * right).  A route that needs neither is listed too, because "this route does not
 * need a session" is a claim that can rot.
 */

#include "routes.h"
#include "testlib.h"

#include "cfg.h"
#include "schema.h"
#include "client.h"

#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

/* ------------------------------------------------------------- the fake broker */

static struct {
	int calls;
	uint8_t last_op;
	uint8_t status;
	uint32_t body_len;
	uint8_t body[4096];
	uint8_t last_body[2048];
	uint32_t last_body_len;
	uint8_t last_session[16];
	int fail;                 /* make bk_call itself fail */
} fake;

int bk_call(const char *sock_path, const struct bk_req *rq, struct bk_resp *rs)
{
	(void)sock_path;
	fake.calls++;
	fake.last_op = rq->op;
	memcpy(fake.last_session, rq->session, 16);
	fake.last_body_len = rq->body_len;
	if (rq->body_len > 0 && rq->body_len <= sizeof(fake.last_body))
		memcpy(fake.last_body, rq->body, rq->body_len);
	if (fake.fail)
		return -111;
	memset(rs, 0, sizeof(*rs));
	rs->status = fake.status;
	rs->body_len = fake.body_len;
	if (fake.body_len > 0)
		memcpy(rs->body, fake.body, fake.body_len);
	return 0;
}

static void fake_reset(void)
{
	memset(&fake, 0, sizeof(fake));
	fake.status = BK_OK;
}

/* A LOGIN response: session[16] + csrf[16] + ttl u32. */
static void fake_login_body(void)
{
	unsigned i;

	for (i = 0; i < 16; i++)
		fake.body[i] = (uint8_t)(0x11 * (i + 1));
	for (i = 0; i < 16; i++)
		fake.body[16 + i] = (uint8_t)(0xa0 + i);
	fake.body[32] = 0;
	fake.body[33] = 0;
	fake.body[34] = 0x03;
	fake.body[35] = 0x84;         /* 900 */
	fake.body_len = 36;
}

/* ----------------------------------------------------------- the grant callback */

static int grant_yes_calls;
static int grant_no_calls;

static int grant_yes(void *ctx, uint32_t *retry_s)
{
	(void)ctx;
	*retry_s = 0;
	grant_yes_calls++;
	return 1;
}

static int grant_no(void *ctx, uint32_t *retry_s)
{
	(void)ctx;
	*retry_s = 7;
	grant_no_calls++;
	return 0;
}

/* ------------------------------------------------------------------- the driver */

#define SESS "0123456789abcdef0123456789abcdef"
#define CSRF "fedcba9876543210fedcba9876543210"
#define OTHR "00000000000000000000000000000001"

static struct route_env env_yes;
static struct route_env env_no;

/* Build a request, parse it, dispatch it, and hand back the response. */
static int run(const char *method, const char *path, const char *sess,
	       const char *csrf_hdr, const char *csrf_cookie, const char *body,
	       struct http_rsp *rs, const struct route_env *env)
{
	char req[4096];
	struct http_req rq;
	size_t n = 0;
	int rc;

	n += (size_t)snprintf(req + n, sizeof(req) - n, "%s %s HTTP/1.1\r\n",
			      method, path);
	n += (size_t)snprintf(req + n, sizeof(req) - n, "Host: 10.1.1.1\r\n");
	if (sess != NULL || csrf_cookie != NULL) {
		n += (size_t)snprintf(req + n, sizeof(req) - n, "Cookie:");
		if (sess != NULL)
			n += (size_t)snprintf(req + n, sizeof(req) - n,
					      " rlxs=%s;", sess);
		if (csrf_cookie != NULL)
			n += (size_t)snprintf(req + n, sizeof(req) - n,
					      " rlxc=%s;", csrf_cookie);
		n += (size_t)snprintf(req + n, sizeof(req) - n, "\r\n");
	}
	if (csrf_hdr != NULL)
		n += (size_t)snprintf(req + n, sizeof(req) - n,
				      "X-RLX-CSRF: %s\r\n", csrf_hdr);
	if (body != NULL)
		n += (size_t)snprintf(req + n, sizeof(req) - n,
				      "Content-Type: application/json\r\n"
				      "Content-Length: %u\r\n",
				      (unsigned)strlen(body));
	n += (size_t)snprintf(req + n, sizeof(req) - n, "\r\n");
	if (body != NULL) {
		size_t bl = strlen(body);

		memcpy(req + n, body, bl);
		n += bl;
	}

	rc = http_parse_all((const uint8_t *)req, n, &rq);
	if (rc != 1) {
		route_rsp_init(rs);
		rs->status = -rc;
		return rs->status;
	}
	(void)route_dispatch(&rq, rs, env);
	if (rs->fd >= 0) {
		(void)close(rs->fd);
		rs->fd = -1;
	}
	return rs->status;
}

static void mcase(const char *name, const char *method, const char *path,
		  const char *sess, const char *hdr, const char *ck,
		  const char *body, int want)
{
	struct http_rsp rs;
	int got;

	fake_reset();
	if (strcmp(path, "/api/login") == 0)
		fake_login_body();
	got = run(method, path, sess, hdr, ck, body, &rs, &env_yes);
	t_okf(got == want, name, got, want);
}

static int hdr_has(const struct http_rsp *rs, const char *needle)
{
	char h[2048];

	if (route_headers(rs, h, sizeof(h)) < 0)
		return 0;
	return strstr(h, needle) != NULL;
}

int main(void)
{
	char tmpl[] = "/tmp/rlxhttpdXXXXXX";     /* replaced below */
	char dir[512];
	struct http_rsp rs;
	const char *tmp;

	env_yes.sock = "/run/broker.sock";
	env_yes.client_ip = 0x0a010164u;
	env_yes.kdf_grant = grant_yes;
	env_yes.kdf_release = NULL;
	env_no = env_yes;
	env_no.kdf_grant = grant_no;

	/* A web root to serve from.  TMPDIR is honoured so the test never depends
	 * on /tmp, which this project treats as volatile. */
	tmp = getenv("TMPDIR");
	(void)snprintf(dir, sizeof(dir), "%s/rlxhttpdXXXXXX",
		       (tmp != NULL && tmp[0] != '\0') ? tmp : ".");
	(void)tmpl;
	if (mkdtemp(dir) == NULL) {
		(void)printf("not ok - could not make a temporary web root\n");
		return 1;
	}
	{
		char p[600];
		FILE *f;

		(void)snprintf(p, sizeof(p), "%s/index.html", dir);
		f = fopen(p, "w");
		if (f != NULL) {
			(void)fputs("<!doctype html><title>rlxfw</title>\n", f);
			(void)fclose(f);
			(void)chmod(p, 0644);
		}
		(void)snprintf(p, sizeof(p), "%s/static", dir);
		(void)mkdir(p, 0755);
		(void)snprintf(p, sizeof(p), "%s/static/style.css", dir);
		f = fopen(p, "w");
		if (f != NULL) {
			(void)fputs("body{color:#111}\n", f);
			(void)fclose(f);
			(void)chmod(p, 0644);
		}
		/* An executable file, to show send_file() refusing one at run time
		 * as well as chrootcheck refusing one at build time. */
		(void)snprintf(p, sizeof(p), "%s/static/evil.css", dir);
		f = fopen(p, "w");
		if (f != NULL) {
			(void)fputs("x\n", f);
			(void)fclose(f);
			(void)chmod(p, 0755);
		}
		/* A symlink out of the tree, for O_NOFOLLOW. */
		(void)snprintf(p, sizeof(p), "%s/static/out.css", dir);
		if (symlink("/etc/passwd", p) != 0)
			(void)printf("# note: symlink() failed here\n");
	}
	if (chdir(dir) != 0) {
		(void)printf("not ok - could not chdir into the web root\n");
		return 1;
	}

	/* ------------------------------------------- the traversal positive control
	 * The battery in test_http.c proves the decoder can say no.  This proves it
	 * can say yes, which is the half that makes the no's meaningful. */
	fake_reset();
	t_okf(run("GET", "/static/style.css", NULL, NULL, NULL, NULL, &rs,
		  &env_yes) == 200, "P /static/style.css is SERVED", rs.status,
	      200);
	t_ok(rs.ctype != NULL && strstr(rs.ctype, "text/css") != NULL,
	     "P and with the CSS type from the fixed table", rs.ctype);
	t_okf(run("GET", "/", NULL, NULL, NULL, NULL, &rs, &env_yes) == 200,
	      "P / serves index.html", rs.status, 200);
	t_okf(run("GET", "/static/evil.css", NULL, NULL, NULL, NULL, &rs, &env_yes)
	      == 404, "an executable file in the web root is not served", rs.status,
	      404);
	t_okf(run("GET", "/static/out.css", NULL, NULL, NULL, NULL, &rs, &env_yes)
	      == 404, "a symlink out of the tree is not followed", rs.status, 404);
	t_okf(run("GET", "/static/../index.html", NULL, NULL, NULL, NULL, &rs,
		  &env_yes) == 400, "traversal through the route layer is 400",
	      rs.status, 400);
	t_okf(run("GET", "/static/nosuch.css", NULL, NULL, NULL, NULL, &rs,
		  &env_yes) == 404, "an absent file is 404", rs.status, 404);
	t_okf(run("GET", "/static/style.sh", NULL, NULL, NULL, NULL, &rs, &env_yes)
	      == 404, "an extension outside the MIME table is 404", rs.status, 404);

	/* ---------------------------------------------------------- the matrix */
	/* GET /, /static, /api/status: no session, no CSRF. */
	mcase("M01 GET / no session", "GET", "/", NULL, NULL, NULL, NULL, 200);
	mcase("M02 GET / with session", "GET", "/", SESS, CSRF, CSRF, NULL, 200);
	mcase("M03 GET /api/status no session", "GET", "/api/status", NULL, NULL,
	      NULL, NULL, 200);
	mcase("M04 GET /api/status with session", "GET", "/api/status", SESS, NULL,
	      NULL, NULL, 200);

	/* POST /api/login: no session and no CSRF needed, but a JSON body is. */
	mcase("M05 POST /api/login", "POST", "/api/login", NULL, NULL, NULL,
	      "{\"password\":\"hunter2hunter2\"}", 200);
	mcase("M06 POST /api/login no body", "POST", "/api/login", NULL, NULL, NULL,
	      NULL, 411);
	mcase("M07 POST /api/login empty object", "POST", "/api/login", NULL, NULL,
	      NULL, "{}", 400);
	mcase("M08 POST /api/login wrong field type", "POST", "/api/login", NULL,
	      NULL, NULL, "{\"password\":1}", 400);

	/* The state-changing routes, all four cells each. */
	{
		static const char *paths[] = { "/api/logout", "/api/config",
					       "/api/password", "/api/ping",
					       "/api/reboot", "/api/firmware" };
		static const char *bodies[] = {
			"{}",
			"{\"sys.hostname\":\"rlxfw-1\"}",
			"{\"old\":\"aaaaaaaa\",\"new\":\"bbbbbbbb\"}",
			"{\"target\":\"10.1.1.2\",\"count\":2}",
			"{}",
			"{}"
		};
		static const int want_ok[] = { 200, 200, 200, 200, 200, 501 };
		unsigned i;
		char nm[64];

		for (i = 0; i < sizeof(paths) / sizeof(paths[0]); i++) {
			(void)snprintf(nm, sizeof(nm), "M %s no session", paths[i]);
			mcase(nm, "POST", paths[i], NULL, CSRF, CSRF, bodies[i],
			      401);
			(void)snprintf(nm, sizeof(nm), "M %s session, no csrf",
				       paths[i]);
			mcase(nm, "POST", paths[i], SESS, NULL, NULL, bodies[i],
			      403);
			(void)snprintf(nm, sizeof(nm), "M %s session, wrong csrf",
				       paths[i]);
			mcase(nm, "POST", paths[i], SESS, OTHR, CSRF, bodies[i],
			      403);
			(void)snprintf(nm, sizeof(nm),
				       "M %s session, header but no cookie",
				       paths[i]);
			mcase(nm, "POST", paths[i], SESS, CSRF, NULL, bodies[i],
			      403);
			(void)snprintf(nm, sizeof(nm), "M %s session, right csrf",
				       paths[i]);
			mcase(nm, "POST", paths[i], SESS, CSRF, CSRF, bodies[i],
			      want_ok[i]);
		}
	}

	/* GET /api/config needs a session but no CSRF (it changes nothing). */
	mcase("M GET /api/config no session", "GET", "/api/config", NULL, NULL,
	      NULL, NULL, 401);
	mcase("M GET /api/config with session", "GET", "/api/config", SESS, NULL,
	      NULL, NULL, 200);

	/* The wrong method on a known path is 405, with an Allow header. */
	mcase("M405 GET /api/login", "GET", "/api/login", NULL, NULL, NULL, NULL,
	      405);
	mcase("M405 POST /api/status", "POST", "/api/status", SESS, CSRF, CSRF,
	      "{}", 405);
	mcase("M405 POST /", "POST", "/", NULL, NULL, NULL, "{}", 405);
	fake_reset();
	(void)run("GET", "/api/login", NULL, NULL, NULL, NULL, &rs, &env_yes);
	t_ok(hdr_has(&rs, "Allow: GET, POST\r\n"), "405 carries an Allow header",
	     NULL);

	/* 404, and its shape. */
	fake_reset();
	t_okf(run("GET", "/nope", NULL, NULL, NULL, NULL, &rs, &env_yes) == 404,
	      "M404 an unknown path", rs.status, 404);
	t_ok(rs.blen == strlen("{\"ok\":false,\"error\":\"notfound\"}") &&
	     memcmp(rs.body, "{\"ok\":false,\"error\":\"notfound\"}",
		    rs.blen) == 0, "404 shape is the fixed document", rs.body);
	/* and it reflects nothing: the path's own bytes are not in the answer */
	fake_reset();
	(void)run("GET", "/nope-MARKER-7e1", NULL, NULL, NULL, NULL, &rs, &env_yes);
	t_ok(strstr(rs.body, "MARKER") == NULL,
	     "no request byte is echoed into the 404 body", rs.body);
	{
		char h[2048];

		(void)route_headers(&rs, h, sizeof(h));
		t_ok(strstr(h, "MARKER") == NULL,
		     "nor into any response header", NULL);
	}

	/* ------------------------------------------------ the broker's statuses */
	{
		static const struct { uint8_t bs; int want; const char *name; } m[] = {
			{ BK_BADREQ,    400, "BADREQ -> 400" },
			{ BK_PERM,      403, "PERM -> 403" },
			{ BK_AUTH,      401, "AUTH -> 401" },
			{ BK_LOCKED,    429, "LOCKED -> 429" },
			{ BK_INVAL,     400, "INVAL -> 400" },
			{ BK_IO,        500, "IO -> 500" },
			{ BK_NOENT,     404, "NOENT -> 404" },
			{ BK_BUSY,      503, "BUSY -> 503" },
			{ BK_NOTSUP,    501, "NOTSUP -> 501" },
			{ BK_NOENTROPY, 503, "NOENTROPY -> 503" }
		};
		unsigned i;

		for (i = 0; i < sizeof(m) / sizeof(m[0]); i++) {
			fake_reset();
			fake.status = m[i].bs;
			if (m[i].bs == BK_LOCKED) {
				fake.body[0] = 0;
				fake.body[1] = 0;
				fake.body[2] = 0;
				fake.body[3] = 60;
				fake.body_len = 4;
			}
			if (m[i].bs == BK_INVAL) {
				fake.body[0] = 0x00;
				fake.body[1] = 0x10;
				fake.body_len = 2;
			}
			t_okf(run("GET", "/api/status", SESS, NULL, NULL, NULL,
				  &rs, &env_yes) == m[i].want, m[i].name,
			      rs.status, m[i].want);
		}
	}

	/* NOENTROPY must be visible to the user as its own reason, not as a
	 * generic failure: 量 2026-09-30, entropy_avail read 0 on this board, so
	 * this is the answer a password change gets today. */
	fake_reset();
	fake.status = BK_NOENTROPY;
	(void)run("POST", "/api/password", SESS, CSRF, CSRF,
		  "{\"old\":\"aaaaaaaa\",\"new\":\"bbbbbbbb\"}", &rs, &env_yes);
	t_ok(strstr(rs.body, "\"noentropy\"") != NULL,
	     "the NOENTROPY reason reaches the user verbatim", rs.body);
	t_okf(rs.status == 503, "and as a 503", rs.status, 503);

	/* LOCKED carries a Retry-After taken from the broker's own seconds. */
	fake_reset();
	fake.status = BK_LOCKED;
	fake.body[3] = 60;
	fake.body_len = 4;
	(void)run("POST", "/api/login", NULL, NULL, NULL,
		  "{\"password\":\"x\"}", &rs, &env_yes);
	t_okf(rs.retry_after == 60, "LOCKED sets Retry-After from the broker",
	      (long)rs.retry_after, 60);
	t_ok(hdr_has(&rs, "Retry-After: 60\r\n"), "and it reaches the headers",
	     NULL);

	/* A broker that cannot be reached is 503 and says nothing else. */
	fake_reset();
	fake.fail = 1;
	t_okf(run("GET", "/api/status", SESS, NULL, NULL, NULL, &rs, &env_yes)
	      == 503, "an unreachable broker is 503", rs.status, 503);

	/* ------------------------------- the limiter runs BEFORE the broker call */
	fake_reset();
	fake_login_body();
	grant_no_calls = 0;
	t_okf(run("POST", "/api/login", NULL, NULL, NULL,
		  "{\"password\":\"hunter2hunter2\"}", &rs, &env_no) == 429,
	      "a refused KDF grant answers 429", rs.status, 429);
	t_okf(fake.calls == 0, "and the broker was NOT called", fake.calls, 0);
	t_okf(rs.retry_after == 7, "with the parent's own Retry-After",
	      (long)rs.retry_after, 7);
	t_okf(grant_no_calls == 1, "the grant was asked exactly once",
	      grant_no_calls, 1);

	fake_reset();
	fake_login_body();
	grant_yes_calls = 0;
	t_okf(run("POST", "/api/login", NULL, NULL, NULL,
		  "{\"password\":\"hunter2hunter2\"}", &rs, &env_yes) == 200,
	      "control: a granted login DOES reach the broker", rs.status, 200);
	t_okf(fake.calls == 1, "exactly one broker call", fake.calls, 1);
	t_okf(fake.last_op == BK_LOGIN, "and it was LOGIN", fake.last_op,
	      BK_LOGIN);

	/* The login response's cookies. */
	fake_reset();
	fake_login_body();
	(void)run("POST", "/api/login", NULL, NULL, NULL,
		  "{\"password\":\"hunter2hunter2\"}", &rs, &env_yes);
	/* 0x11 * 16 is 0x110, which truncates to 0x10 -- the expectation written
	 * before the run said ...ff00 and the arithmetic said ...ff10.  The fake's
	 * bytes are what they are; it is the expectation that was wrong. */
	t_ok(hdr_has(&rs, "Set-Cookie: rlxs=1122334455667788"
		     "99aabbccddeeff10; Path=/; HttpOnly; SameSite=Strict\r\n"),
	     "the session cookie is HttpOnly and SameSite=Strict", rs.cookies);
	t_ok(hdr_has(&rs, "Set-Cookie: rlxc=a0a1a2a3a4a5a6a7a8a9aaabacadaeaf;"
		     " Path=/; SameSite=Strict\r\n"),
	     "the CSRF companion cookie is readable by the page", rs.cookies);
	t_ok(strstr(rs.body, "\"csrf\":\"a0a1a2a3a4a5a6a7a8a9aaabacadaeaf\"")
	     != NULL, "and the token is in the body for the page to send back",
	     rs.body);
	t_ok(strstr(rs.body, "\"ttl_s\":900") != NULL, "with the broker's TTL",
	     rs.body);

	/* Logout clears both cookies. */
	fake_reset();
	(void)run("POST", "/api/logout", SESS, CSRF, CSRF, "{}", &rs, &env_yes);
	/* Through the CRLF, not as a substring.  The substring form of these two
	 * cases passed while the rlxc line was one byte short of its own literal
	 * and the head carried a bare CR. */
	t_ok(hdr_has(&rs, "Set-Cookie: rlxs=; Path=/; HttpOnly; SameSite=Strict;"
		     " Max-Age=0\r\n"),
	     "logout expires the session cookie", rs.cookies);
	t_ok(hdr_has(&rs, "Set-Cookie: rlxc=; Path=/; SameSite=Strict;"
		     " Max-Age=0\r\n"),
	     "logout expires the CSRF cookie", rs.cookies);
	/* and the whole header block must hold no CR that is not part of a CRLF */
	{
		char h[2048];
		int hl = route_headers(&rs, h, sizeof(h));
		int lone = 0;
		int i;

		for (i = 0; i < hl; i++) {
			if (h[i] == '\r' && (i + 1 >= hl || h[i + 1] != '\n'))
				lone++;
			if (h[i] == '\n' && (i == 0 || h[i - 1] != '\r'))
				lone++;
		}
		t_okf(lone == 0, "no bare CR or bare LF anywhere in the head", lone,
		      0);
	}

	/* ----------------------------------------------- headers on EVERY answer */
	{
		static const char *needles[] = {
			"X-Frame-Options: DENY\r\n",
			"Content-Security-Policy: default-src 'self'\r\n",
			"X-Content-Type-Options: nosniff\r\n",
			"Connection: close\r\n"
		};
		static const char *paths[] = { "/", "/static/style.css",
					       "/api/status", "/nope" };
		unsigned i, j;
		char nm[96];

		for (i = 0; i < sizeof(paths) / sizeof(paths[0]); i++) {
			fake_reset();
			(void)run("GET", paths[i], SESS, NULL, NULL, NULL, &rs,
				  &env_yes);
			for (j = 0; j < sizeof(needles) / sizeof(needles[0]); j++) {
				(void)snprintf(nm, sizeof(nm), "H %s carries %.28s",
					       paths[i], needles[j]);
				t_ok(hdr_has(&rs, needles[j]), nm, NULL);
			}
		}
	}
	fake_reset();
	(void)run("GET", "/api/status", NULL, NULL, NULL, NULL, &rs, &env_yes);
	t_ok(hdr_has(&rs, "Cache-Control: no-store\r\n"),
	     "/api/* carries Cache-Control: no-store", NULL);
	fake_reset();
	(void)run("GET", "/static/style.css", NULL, NULL, NULL, NULL, &rs,
		  &env_yes);
	t_ok(!hdr_has(&rs, "Cache-Control: no-store\r\n"),
	     "control: a static file does NOT (so the check can tell them apart)",
	     NULL);

	/* --------------------------------------------- the config SET encoding */
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"dhcpd.lease\":600,\"sys.hostname\":\"box\","
		  "\"lan.ipaddr\":\"10.1.1.1\"}", &rs, &env_yes);
	t_okf(rs.status == 200, "a three-key SET is accepted", rs.status, 200);
	t_okf(fake.last_op == BK_SET, "as op SET", fake.last_op, BK_SET);
	{
		/* ids must be strictly ascending: 0x0001, 0x0010, 0x0023 */
		const uint8_t *b = fake.last_body;
		int asc = 1;
		uint32_t o = 0;
		uint16_t prev = 0;
		int ntlv = 0;

		while (o + 4 <= fake.last_body_len) {
			uint16_t id = (uint16_t)((b[o] << 8) | b[o + 1]);
			uint16_t l = (uint16_t)((b[o + 2] << 8) | b[o + 3]);

			if (ntlv > 0 && id <= prev)
				asc = 0;
			prev = id;
			ntlv++;
			o += 4u + l;
		}
		t_okf(ntlv == 3, "three TLVs", ntlv, 3);
		t_ok(asc == 1, "with strictly ascending ids", NULL);
		t_okf(o == fake.last_body_len, "and no trailing bytes", (long)o,
		      (long)fake.last_body_len);
	}
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"http.port\":8080}", &rs, &env_yes);
	t_okf(rs.status == 403, "a read-only key is refused", rs.status, 403);
	t_okf(fake.calls == 0, "and the broker is not called", fake.calls, 0);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"admin.pwhash\":\"x\"}", &rs, &env_yes);
	t_okf(rs.status == 403, "the hidden key is refused too", rs.status, 403);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF, "{\"no.such\":1}", &rs,
		  &env_yes);
	t_okf(rs.status == 400, "an unknown key is 400", rs.status, 400);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"dhcpd.lease\":1}", &rs, &env_yes);
	t_okf(rs.status == 400, "a value under the schema minimum is 400",
	      rs.status, 400);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"lan.ipaddr\":\"10.1.1.256\"}", &rs, &env_yes);
	t_okf(rs.status == 400, "an octet over 255 is 400", rs.status, 400);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"lan.ipaddr\":\"010.1.1.1\"}", &rs, &env_yes);
	t_okf(rs.status == 400, "a leading zero in an octet is 400", rs.status,
	      400);
	fake_reset();
	(void)run("POST", "/api/config", SESS, CSRF, CSRF,
		  "{\"dhcpd.lease\":\"600\"}", &rs, &env_yes);
	t_okf(rs.status == 400, "a string where a number belongs is 400", rs.status,
	      400);

	/* PING: the target crosses as four bytes, never as text. */
	fake_reset();
	memcpy(fake.body, "2 packets transmitted\n", 22);
	fake.body_len = 22;
	(void)run("POST", "/api/ping", SESS, CSRF, CSRF,
		  "{\"target\":\"10.1.1.2\",\"count\":2}", &rs, &env_yes);
	t_okf(rs.status == 200, "a ping is accepted", rs.status, 200);
	t_okf(fake.last_body_len == 5, "its body is five bytes",
	      (long)fake.last_body_len, 5);
	t_ok(fake.last_body[0] == 10 && fake.last_body[1] == 1 &&
	     fake.last_body[2] == 1 && fake.last_body[3] == 2 &&
	     fake.last_body[4] == 2, "four typed octets and a count", NULL);
	fake_reset();
	(void)run("POST", "/api/ping", SESS, CSRF, CSRF,
		  "{\"target\":\"10.1.1.2; reboot\",\"count\":1}", &rs, &env_yes);
	t_okf(rs.status == 400, "a shell metacharacter in the target is 400",
	      rs.status, 400);
	fake_reset();
	(void)run("POST", "/api/ping", SESS, CSRF, CSRF,
		  "{\"target\":\"10.1.1.2\",\"count\":9}", &rs, &env_yes);
	t_okf(rs.status == 400, "a count over five is 400", rs.status, 400);

	/* A ping output with control bytes in it: sanitised, never reflected raw. */
	fake_reset();
	fake.body[0] = 'a';
	fake.body[1] = 0x1b;
	fake.body[2] = '[';
	fake.body[3] = '2';
	fake.body[4] = 'J';
	fake.body[5] = '\n';
	fake.body[6] = 0xff;
	fake.body_len = 7;
	(void)run("POST", "/api/ping", SESS, CSRF, CSRF,
		  "{\"target\":\"10.1.1.2\",\"count\":1}", &rs, &env_yes);
	t_ok(memchr(rs.body, 0x1b, rs.blen) == NULL,
	     "an escape byte in the ping output does not reach the response",
	     NULL);
	t_ok(memchr(rs.body, 0xff, rs.blen) == NULL,
	     "nor does a byte above 0x7f", NULL);

	/* STATUS TLVs render, and an unknown TLV is skipped rather than fatal. */
	fake_reset();
	{
		uint8_t *b = fake.body;
		uint32_t o = 0;

		b[o++] = 0x80; b[o++] = 0x01; b[o++] = 0; b[o++] = 4;
		b[o++] = 0; b[o++] = 0; b[o++] = 0x03; b[o++] = 0x00;  /* 768 */
		b[o++] = 0x80; b[o++] = 0x07; b[o++] = 0; b[o++] = 4;
		b[o++] = 0; b[o++] = 0; b[o++] = 0; b[o++] = 0;        /* entropy 0 */
		b[o++] = 0x80; b[o++] = 0x08; b[o++] = 0; b[o++] = 1;
		b[o++] = 0;                                            /* not ready */
		b[o++] = 0x9f; b[o++] = 0xff; b[o++] = 0; b[o++] = 2;
		b[o++] = 1; b[o++] = 2;                                /* unknown */
		fake.body_len = o;
	}
	(void)run("GET", "/api/status", SESS, NULL, NULL, NULL, &rs, &env_yes);
	t_ok(strstr(rs.body, "\"uptime_s\":768") != NULL, "STATUS uptime renders",
	     rs.body);
	t_ok(strstr(rs.body, "\"entropy_avail\":0") != NULL,
	     "STATUS entropy_avail 0 renders (量 2026-09-30 on this board)",
	     rs.body);
	t_ok(strstr(rs.body, "\"auth_ready\":false") != NULL,
	     "STATUS auth_ready false renders", rs.body);

	/* A truncated TLV stream must stop, not walk off the end (ASAN). */
	fake_reset();
	fake.body[0] = 0x80;
	fake.body[1] = 0x01;
	fake.body[2] = 0x00;
	fake.body[3] = 0x40;          /* claims 64 bytes */
	fake.body_len = 6;            /* but only 2 follow */
	t_okf(run("GET", "/api/status", SESS, NULL, NULL, NULL, &rs, &env_yes)
	      == 200, "a truncated TLV stream is survived", rs.status, 200);

	/* constant-time compare: both directions */
	t_ok(route_ct_eq32(CSRF, CSRF) == 1, "ct_eq32 equal", NULL);
	t_ok(route_ct_eq32(CSRF, OTHR) == 0, "ct_eq32 different", NULL);
	{
		char a[33], b2[33];

		memcpy(a, CSRF, 33);
		memcpy(b2, CSRF, 33);
		b2[31] = (char)(b2[31] ^ 1);
		t_ok(route_ct_eq32(a, b2) == 0,
		     "ct_eq32 sees a difference in the LAST byte", NULL);
		memcpy(b2, CSRF, 33);
		b2[0] = (char)(b2[0] ^ 1);
		t_ok(route_ct_eq32(a, b2) == 0,
		     "and in the first (so it is not comparing a prefix)", NULL);
	}

	/* The stub schema table, printed so a reviewer can diff it against agent
	 * B's src/lib/schema.c by eye.  Nothing here checks them against each
	 * other; that reconciliation is an open item, not a passing test. */
	{
		unsigned i;

		(void)printf("# stub schema table (SPEC-R7 section 4):\n");
		for (i = 0; i < CFG_NKEYS; i++) {
			const struct cfg_key *k = cfg_key_at(i);

			(void)printf("#   0x%04x %-14s type=%u web=%u\n",
				     k->id, k->name, k->type, k->web);
		}
		t_ok(cfg_key_at(CFG_NKEYS) == NULL,
		     "the key table refuses an index past its end", NULL);
		t_ok(cfg_key_by_name("admin.pwhash") != NULL &&
		     cfg_key_by_name("admin.pwhash")->web == WEB_HIDDEN,
		     "admin.pwhash is WEB_HIDDEN in the table", NULL);
	}

	return t_done(120);
}
