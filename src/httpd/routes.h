/* src/httpd/routes.h -- the route table, and what each route is allowed to do.
 *
 * httpd holds no state that matters: no config, no password, no session table.
 * Every route that changes or reads anything turns into one typed op on the
 * broker socket (SPEC-R7 section 6) and renders the answer.  That is the whole
 * of D7: the process that parses attacker bytes is not the process that can act.
 *
 * WHAT IS CHECKED HERE AND WHAT IS CHECKED IN brokerd.  httpd checks the SHAPE
 * of authority -- a session cookie that is 32 hex digits, a CSRF header that is
 * 32 hex digits and equals the companion cookie in constant time -- and brokerd
 * checks the SUBSTANCE, because only brokerd has the session table.  Neither is
 * a substitute for the other: httpd's check exists so a cross-site POST dies at
 * the edge without spending a broker round trip, and brokerd's is the one that
 * decides.
 *
 * WHAT IT DOES NOT ESTABLISH.  Nothing here has spoken to a broker: the route
 * tests link a fake bk_call.  And no route can be right about the config schema
 * beyond what stub/cfg.h transcribes; when src/lib/schema.c lands, the table is
 * one include away and the values it produces must be diffed against it.
 */
#ifndef RLXFW_HTTPD_ROUTES_H
#define RLXFW_HTTPD_ROUTES_H

#include <stddef.h>
#include <stdint.h>

#include "http.h"

#define RSP_BODY_MAX 6144   /* a PING body is <= 2048 bytes of text, and escaping
			     * it can double it, plus the JSON around it */

struct http_rsp {
	int      status;
	const char *ctype;              /* a fixed string, never input */
	uint32_t retry_after;           /* 0 = no Retry-After header */
	uint8_t  nostore;               /* Cache-Control: no-store */
	uint8_t  allow_get_post;        /* emit an Allow header (405) */
	char     cookies[320];          /* zero to two Set-Cookie lines, CRLF each */
	size_t   blen;
	char     body[RSP_BODY_MAX];
	int      fd;                    /* >= 0: send this file, not body */
	uint32_t fsize;
};

/* The parent's answer to "may I spend a KDF evaluation?".  1 = yes, 0 = no, and
 * on no *retry_s says when.  A NULL grant function means "always yes", which is
 * what the mutation control in the tests uses to show the limiter is load
 * bearing rather than decorative. */
struct route_env {
	const char *sock;               /* broker socket path */
	uint32_t    client_ip;
	int       (*kdf_grant)(void *ctx, uint32_t *retry_s);
	void      (*kdf_release)(void *ctx);
	void       *ctx;
};

void route_rsp_init(struct http_rsp *rs);
int  route_dispatch(const struct http_req *rq, struct http_rsp *rs,
		    const struct route_env *env);

/* Serialise the status line and every header into out[0..cap).  Returns the
 * length, or -1 if it did not fit.  The security headers of SPEC-R7 section 7 are
 * emitted here, on every response, with no way for a route to skip them. */
int  route_headers(const struct http_rsp *rs, char *out, size_t cap);

/* Exposed for the tests: the fixed error-body writer.  `code` is one of this
 * file's own tokens, never a byte from the request. */
void route_err(struct http_rsp *rs, int status, const char *code);

/* Exposed for the tests: constant-time equality over exactly 32 bytes. */
int  route_ct_eq32(const char *a, const char *b);

#endif /* RLXFW_HTTPD_ROUTES_H */
