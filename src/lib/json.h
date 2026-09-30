/* src/lib/json.h -- a bounded, flat JSON object reader for rlxfw's web API.
 *
 * WHAT IT IS.  A hand-written recursive-descent-free parser over a byte range
 * that is already in memory.  It accepts exactly one shape: a single JSON
 * object whose members' values are strings, unsigned 32-bit integers, `true`,
 * `false` or `null`.  Depth is one: a `{` or `[` in a value position is a
 * refusal, not a recursion.  There is no allocation, no VLA and no recursion in
 * the whole file, so its stack use is a constant the compiler can be asked for.
 *
 * WHAT IT DELIBERATELY REFUSES, and each of these is narrower than RFC 8259:
 *   - nested objects and arrays (JSONE_DEPTH)
 *   - numbers that are not a bare u32: a sign, a fraction, an exponent, a
 *     leading zero, or a value above 4294967295 (JSONE_NUM)
 *   - strings longer than JSON_STR_MAX *after* unescaping (JSONE_LONG)
 *   - any byte >= 0x80 and any raw control byte < 0x20 inside a string
 *   - `\u` escapes outside 0x20..0x7E, so no surrogate arithmetic exists here
 *   - a duplicate key (JSONE_DUP), so a caller can never be split between two
 *     readings of the same document
 *   - a NUL anywhere in the document (JSONE_NUL): this parser takes a length,
 *     and a caller that later treats a value as a C string must not be able to
 *     be handed a truncation
 *   - trailing bytes after the closing brace (JSONE_TRAIL)
 *
 * WHAT IT DOES NOT ESTABLISH.  That the values are *valid* for the config
 * schema: bounds, charsets and cross-field rules belong to cfg_set() and
 * cfg_validate().  This file only decides that the document is well formed and
 * that every value fits a fixed-size slot.
 */
#ifndef RLXFW_JSON_H
#define RLXFW_JSON_H

#include <stddef.h>
#include <stdint.h>

#define JSON_KEYS_MAX  24   /* members in one object */
#define JSON_STR_MAX   64   /* SPEC-R7 section 7: strings <= 64 bytes */
#define JSON_DOC_MAX 4096   /* the HTTP body limit; longer input is refused */

enum json_type { JT_STR = 1, JT_NUM, JT_BOOL, JT_NULL };

enum {
	JSONE_SYNTAX = 1,   /* not JSON, or not an object */
	JSONE_DEPTH,        /* an object or array in a value position */
	JSONE_LONG,         /* a key or string value over JSON_STR_MAX */
	JSONE_MANY,         /* over JSON_KEYS_MAX members */
	JSONE_DUP,          /* the same key twice */
	JSONE_NUM,          /* not a bare u32 */
	JSONE_NUL,          /* a 0x00 byte in the document */
	JSONE_CHAR,         /* a byte a string may not hold */
	JSONE_ESC,          /* an escape this parser does not accept */
	JSONE_TRAIL,        /* bytes after the closing brace */
	JSONE_BIG           /* the document is longer than JSON_DOC_MAX */
};

struct json_member {
	uint8_t  type;                  /* enum json_type */
	uint8_t  klen;
	uint8_t  slen;                  /* JT_STR: unescaped length */
	char     key[JSON_STR_MAX + 1];
	char     sval[JSON_STR_MAX + 1];/* JT_STR only, NUL-terminated */
	uint32_t nval;                  /* JT_NUM, or 0/1 for JT_BOOL */
};

struct json_obj {
	uint8_t n;
	struct json_member m[JSON_KEYS_MAX];
};

/* Parse exactly one object from p[0..n).  0 on success, -JSONE_* on refusal.
 * On refusal *out is left with n = 0; nothing partial is visible. */
int json_parse(const void *p, size_t n, struct json_obj *out);

/* NULL when the key is absent.  `key` is a NUL-terminated C string from the
 * caller's own .rodata, never from the network. */
const struct json_member *json_get(const struct json_obj *o, const char *key);

/* The name of a refusal, for a log line.  Never contains document bytes. */
const char *json_errname(int err);

/* ---- writer: a bounded appender, so no route builds a body with sprintf ---- */
struct json_w {
	char  *buf;
	size_t cap;
	size_t len;
	int    err;    /* sticky: 1 once anything did not fit */
	int    nmemb;  /* members written at the current level */
};

void json_w_init(struct json_w *w, char *buf, size_t cap);
void json_w_obj_open(struct json_w *w);
void json_w_obj_close(struct json_w *w);
void json_w_key(struct json_w *w, const char *key);
void json_w_str(struct json_w *w, const char *key, const char *val);
void json_w_strn(struct json_w *w, const char *key, const char *val, size_t n);
void json_w_num(struct json_w *w, const char *key, uint32_t v);
void json_w_bool(struct json_w *w, const char *key, int v);
void json_w_raw(struct json_w *w, const char *key, const char *raw);
int  json_w_done(const struct json_w *w);   /* 0 ok, -1 truncated */

#endif /* RLXFW_JSON_H */
