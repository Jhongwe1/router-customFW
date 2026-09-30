/* src/httpd/http.h -- the request parser and the response writer.
 *
 * WHY THIS FILE IS THE ONE THAT MATTERS.  The vendor's `boa` took request bytes
 * into a shell (D7).  rlxfw's httpd cannot: there is no `system()` anywhere in
 * the image.  What is left is the parser itself, and a parser is the last thing
 * an unauthenticated peer can reach.  So it is a flat state machine over a byte
 * stream with no recursion, no VLA, no `alloca` and no allocation; every buffer
 * in `struct http_req` is a fixed array, and every store into one is preceded by
 * a comparison against its size.
 *
 * The parser is fed incrementally and never sees the whole request at once, so
 * it can enforce the byte limits before the bytes are in memory.  It returns
 * the HTTP status to answer with, so a caller never has to invent one.
 *
 * WHAT IT DOES NOT ESTABLISH.  Nothing here is a claim about authentication or
 * authorisation: this file decides only that the bytes are a request of a shape
 * the program understands.  Routing, sessions, CSRF and the broker are
 * routes.c's.  No TLS: HTTP only (SPEC-R7 puts R7g out of the gate).
 */
#ifndef RLXFW_HTTP_H
#define RLXFW_HTTP_H

#include <stddef.h>
#include <stdint.h>

/* SPEC-R7 section 7 limits, all of them. */
#define HTTP_REQLINE_MAX   1024   /* the request line, CRLF excluded */
#define HTTP_LINE_MAX      1024   /* one header line, CRLF excluded */
#define HTTP_HDR_LINES_MAX   32
#define HTTP_HDR_BYTES_MAX 4096   /* total, CRLFs included */
#define HTTP_BODY_MAX      4096
#define HTTP_PATH_MAX       128   /* decoded request path, NUL included */
#define HTTP_NAME_MAX        64   /* a /static/<name> component */
#define HTTP_TOK_MAX         33   /* 32 hex characters and a NUL */

#define HTTP_HDR_TIMEOUT_S  5
#define HTTP_BODY_TIMEOUT_S 10
#define HTTP_CONN_MAX       8

enum http_method { HM_NONE = 0, HM_GET, HM_POST };

struct http_req {
	uint8_t  method;                  /* enum http_method */
	uint8_t  ver_minor;               /* 0 for HTTP/1.0, 1 for HTTP/1.1 */
	uint16_t pathlen;
	char     path[HTTP_PATH_MAX];     /* percent-decoded and validated */
	uint8_t  has_clen;
	uint8_t  chunked;                 /* Transfer-Encoding present -> 501 */
	uint32_t clen;
	char     sess[HTTP_TOK_MAX];      /* cookie rlxs, "" when absent */
	char     ccsrf[HTTP_TOK_MAX];     /* cookie rlxc, "" when absent */
	char     hcsrf[HTTP_TOK_MAX];     /* header X-RLX-CSRF, "" when absent */
	uint8_t  is_json;                 /* Content-Type is application/json */
	uint32_t body_len;
	uint8_t  body[HTTP_BODY_MAX + 1];
};

enum http_state { HS_REQLINE = 0, HS_HEADERS, HS_BODY, HS_DONE, HS_ERR };

struct http_parser {
	uint8_t  state;
	uint16_t linelen;
	uint8_t  saw_cr;
	uint16_t nhdr;
	uint32_t hdrbytes;
	uint32_t bodygot;
	int      status;                  /* the status to answer with on refusal */
	uint8_t  seen_clen;
	uint8_t  seen_te;
	uint8_t  seen_cookie;
	uint8_t  seen_csrf;
	uint8_t  seen_ctype;
	char     line[HTTP_LINE_MAX + 1];
	struct http_req *r;
};

/* Feeding.  http_feed returns:
 *    0  more bytes are needed
 *    1  the request is complete
 *   <0  refused; -(*) is the HTTP status to send, and nothing is echoed
 * *used is always set to the number of bytes consumed from p. */
void http_parse_init(struct http_parser *ps, struct http_req *r);
int  http_feed(struct http_parser *ps, const uint8_t *p, size_t n, size_t *used);

/* One-shot, for the tests and the fuzz harness. */
int  http_parse_all(const uint8_t *p, size_t n, struct http_req *r);

/* Percent-decode and validate a request target into out[0..cap).  Returns the
 * decoded length, or a negative HTTP status.  Exposed because the traversal
 * battery tests it directly. */
int  http_decode_path(const char *target, size_t tlen, char *out, size_t cap);

/* The fixed MIME table.  NULL when the extension is not in it: httpd answers
 * 404 rather than guessing a type for a file it cannot name. */
const char *http_mime(const char *name);

/* 1 when s is exactly 32 lowercase-or-uppercase hex digits. */
int  http_is_hex32(const char *s);

/* A status's reason phrase.  A fixed table; never input. */
const char *http_reason(int status);

#endif /* RLXFW_HTTP_H */
