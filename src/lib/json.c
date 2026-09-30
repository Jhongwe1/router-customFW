/* src/lib/json.c -- the parser and writer declared in json.h.
 *
 * The parser is one pass with an explicit cursor.  There is no recursion and no
 * function that can be entered twice for the same document, so a nesting bomb
 * cannot grow the stack: the only nesting this file knows about is the one
 * object it is looking for, and a second `{` is an error code.
 *
 * Every read of the input goes through the same three guards: the cursor is
 * compared against `n` before the byte is fetched, the byte is checked against
 * the set its position allows, and a length is checked against the destination
 * slot before the byte is stored.  The tests in src/httpd/test_json.c truncate a
 * valid document at every offset to look for a path that skips one of them.
 *
 * It does not establish that a value is legal for the config schema.
 */

#include "json.h"

#include <string.h>

/* ------------------------------------------------------------------ parser */

struct jp {
	const unsigned char *p;
	size_t n;
	size_t i;
};

static int jp_eof(const struct jp *s)
{
	return s->i >= s->n;
}

static int jp_peek(const struct jp *s)
{
	if (s->i >= s->n)
		return -1;
	return (int)s->p[s->i];
}

static void jp_skip_ws(struct jp *s)
{
	while (s->i < s->n) {
		unsigned char c = s->p[s->i];
		if (c == ' ' || c == '\t' || c == '\r' || c == '\n')
			s->i++;
		else
			break;
	}
}

static int hexval(int c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

/* A JSON string into dst[0..cap-1], NUL-terminated.  *outlen is the unescaped
 * length.  The opening quote has NOT been consumed. */
static int jp_string(struct jp *s, char *dst, size_t cap, uint8_t *outlen)
{
	size_t len = 0;

	if (jp_peek(s) != '"')
		return -JSONE_SYNTAX;
	s->i++;

	for (;;) {
		int c;

		if (jp_eof(s))
			return -JSONE_SYNTAX;        /* unterminated */
		c = (int)s->p[s->i++];

		if (c == '"') {
			dst[len] = '\0';
			*outlen = (uint8_t)len;
			return 0;
		}
		if (c == 0x00)
			return -JSONE_NUL;
		if (c < 0x20)
			return -JSONE_CHAR;          /* raw control byte */
		if (c >= 0x80)
			return -JSONE_CHAR;          /* this API is ASCII only */

		if (c == '\\') {
			int e;

			if (jp_eof(s))
				return -JSONE_SYNTAX;
			e = (int)s->p[s->i++];
			switch (e) {
			case '"':  c = '"';  break;
			case '\\': c = '\\'; break;
			case '/':  c = '/';  break;
			case 'b':  c = 0x08; break;
			case 'f':  c = 0x0c; break;
			case 'n':  c = 0x0a; break;
			case 'r':  c = 0x0d; break;
			case 't':  c = 0x09; break;
			case 'u': {
				int h0, h1, h2, h3, v;

				if (s->n - s->i < 4)
					return -JSONE_SYNTAX;
				h0 = hexval((int)s->p[s->i + 0]);
				h1 = hexval((int)s->p[s->i + 1]);
				h2 = hexval((int)s->p[s->i + 2]);
				h3 = hexval((int)s->p[s->i + 3]);
				if (h0 < 0 || h1 < 0 || h2 < 0 || h3 < 0)
					return -JSONE_ESC;
				v = (h0 << 12) | (h1 << 8) | (h2 << 4) | h3;
				/* No surrogate arithmetic exists in this file, so
				 * refuse everything that would need it, and every
				 * byte a raw character may not be either. */
				if (v < 0x20 || v > 0x7e)
					return -JSONE_ESC;
				s->i += 4;
				c = v;
				break;
			}
			default:
				return -JSONE_ESC;
			}
		}

		if (len + 1 >= cap)
			return -JSONE_LONG;
		dst[len++] = (char)c;
	}
}

/* A bare unsigned 32-bit integer: no sign, no fraction, no exponent, no leading
 * zero.  Anything else is -JSONE_NUM, including a value that would wrap. */
static int jp_u32(struct jp *s, uint32_t *out)
{
	uint32_t v = 0;
	size_t start = s->i;
	size_t digits = 0;

	if (jp_eof(s))
		return -JSONE_SYNTAX;
	if (s->p[s->i] == '-' || s->p[s->i] == '+')
		return -JSONE_NUM;

	while (s->i < s->n && s->p[s->i] >= '0' && s->p[s->i] <= '9') {
		unsigned d = (unsigned)(s->p[s->i] - '0');

		if (v > 429496729u || (v == 429496729u && d > 5u))
			return -JSONE_NUM;
		v = v * 10u + d;
		s->i++;
		digits++;
	}
	if (digits == 0)
		return -JSONE_SYNTAX;
	if (digits > 1 && s->p[start] == '0')
		return -JSONE_NUM;               /* leading zero */
	if (s->i < s->n) {
		unsigned char c = s->p[s->i];

		if (c == '.' || c == 'e' || c == 'E')
			return -JSONE_NUM;       /* float or exponent */
	}
	*out = v;
	return 0;
}

static int jp_lit(struct jp *s, const char *word)
{
	size_t l = strlen(word);

	if (s->n - s->i < l)
		return -JSONE_SYNTAX;
	if (memcmp(s->p + s->i, word, l) != 0)
		return -JSONE_SYNTAX;
	s->i += l;
	return 0;
}

int json_parse(const void *p, size_t n, struct json_obj *out)
{
	struct jp s;
	int rc;

	memset(out, 0, sizeof(*out));
	if (n > JSON_DOC_MAX)
		return -JSONE_BIG;

	s.p = (const unsigned char *)p;
	s.n = n;
	s.i = 0;

	/* A NUL anywhere voids the document: a caller that hands a value to a
	 * C-string interface must not be able to be given a truncation. */
	if (memchr(p, 0, n) != NULL)
		return -JSONE_NUL;

	jp_skip_ws(&s);
	if (jp_peek(&s) != '{')
		return -JSONE_SYNTAX;
	s.i++;
	jp_skip_ws(&s);

	if (jp_peek(&s) == '}') {
		s.i++;
		goto tail;
	}

	for (;;) {
		struct json_member *m;
		unsigned k;
		int c;

		if (out->n >= JSON_KEYS_MAX)
			return -JSONE_MANY;
		m = &out->m[out->n];

		jp_skip_ws(&s);
		rc = jp_string(&s, m->key, sizeof(m->key), &m->klen);
		if (rc != 0)
			return rc;
		if (m->klen == 0)
			return -JSONE_SYNTAX;            /* "" is not a key here */

		for (k = 0; k < out->n; k++) {
			if (out->m[k].klen == m->klen &&
			    memcmp(out->m[k].key, m->key, m->klen) == 0)
				return -JSONE_DUP;
		}

		jp_skip_ws(&s);
		if (jp_peek(&s) != ':')
			return -JSONE_SYNTAX;
		s.i++;
		jp_skip_ws(&s);

		c = jp_peek(&s);
		if (c < 0)
			return -JSONE_SYNTAX;
		if (c == '{' || c == '[')
			return -JSONE_DEPTH;
		if (c == '"') {
			rc = jp_string(&s, m->sval, sizeof(m->sval), &m->slen);
			if (rc != 0)
				return rc;
			m->type = JT_STR;
		} else if (c == 't') {
			rc = jp_lit(&s, "true");
			if (rc != 0)
				return rc;
			m->type = JT_BOOL;
			m->nval = 1;
		} else if (c == 'f') {
			rc = jp_lit(&s, "false");
			if (rc != 0)
				return rc;
			m->type = JT_BOOL;
			m->nval = 0;
		} else if (c == 'n') {
			rc = jp_lit(&s, "null");
			if (rc != 0)
				return rc;
			m->type = JT_NULL;
		} else {
			rc = jp_u32(&s, &m->nval);
			if (rc != 0)
				return rc;
			m->type = JT_NUM;
		}
		out->n++;

		jp_skip_ws(&s);
		c = jp_peek(&s);
		if (c == ',') {
			s.i++;
			continue;
		}
		if (c == '}') {
			s.i++;
			break;
		}
		return -JSONE_SYNTAX;
	}

tail:
	jp_skip_ws(&s);
	if (!jp_eof(&s))
		return -JSONE_TRAIL;
	return 0;
}

const struct json_member *json_get(const struct json_obj *o, const char *key)
{
	size_t l = strlen(key);
	unsigned i;

	if (l > JSON_STR_MAX)
		return NULL;
	for (i = 0; i < o->n; i++) {
		if (o->m[i].klen == (uint8_t)l &&
		    memcmp(o->m[i].key, key, l) == 0)
			return &o->m[i];
	}
	return NULL;
}

const char *json_errname(int err)
{
	switch (err < 0 ? -err : err) {
	case JSONE_SYNTAX: return "syntax";
	case JSONE_DEPTH:  return "depth";
	case JSONE_LONG:   return "long";
	case JSONE_MANY:   return "many";
	case JSONE_DUP:    return "dup";
	case JSONE_NUM:    return "num";
	case JSONE_NUL:    return "nul";
	case JSONE_CHAR:   return "char";
	case JSONE_ESC:    return "esc";
	case JSONE_TRAIL:  return "trail";
	case JSONE_BIG:    return "big";
	case 0:            return "ok";
	default:           return "err";
	}
}

/* ------------------------------------------------------------------ writer */

static void jw_put(struct json_w *w, const char *s, size_t n)
{
	if (w->err)
		return;
	if (w->len + n + 1 > w->cap) {
		w->err = 1;
		return;
	}
	memcpy(w->buf + w->len, s, n);
	w->len += n;
	w->buf[w->len] = '\0';
}

static void jw_ch(struct json_w *w, char c)
{
	jw_put(w, &c, 1);
}

void json_w_init(struct json_w *w, char *buf, size_t cap)
{
	w->buf = buf;
	w->cap = cap;
	w->len = 0;
	w->err = (cap == 0);
	w->nmemb = 0;
	if (cap > 0)
		buf[0] = '\0';
}

void json_w_obj_open(struct json_w *w)
{
	jw_ch(w, '{');
	w->nmemb = 0;
}

void json_w_obj_close(struct json_w *w)
{
	jw_ch(w, '}');
}

void json_w_key(struct json_w *w, const char *key)
{
	if (w->nmemb)
		jw_ch(w, ',');
	w->nmemb++;
	jw_ch(w, '"');
	jw_put(w, key, strlen(key));
	jw_put(w, "\":", 2);
}

/* Escapes every byte a JSON string may not hold, and refuses (sticky error)
 * every byte this API does not allow out, rather than emitting it raw.  A value
 * that reaches here is either from our own tables or from the config store,
 * whose charsets are ASCII; the escape is the second guard, not the first. */
void json_w_strn(struct json_w *w, const char *key, const char *val, size_t n)
{
	size_t i;

	json_w_key(w, key);
	jw_ch(w, '"');
	for (i = 0; i < n; i++) {
		unsigned char c = (unsigned char)val[i];

		char e[2];

		e[0] = '\\';
		if (c == '"' || c == '\\') {
			e[1] = (char)c;
			jw_put(w, e, 2);
		} else if (c == '\n' || c == '\r' || c == '\t') {
			/* The three whitespace controls are escaped rather than
			 * refused: a PING body is the several lines of a
			 * program's stdout, and refusing them would turn a
			 * working diagnostic into a 500.  Every OTHER control
			 * byte, and every byte above 0x7e, is still a refusal --
			 * the caller sanitises first (routes.c ping_sanitise)
			 * and this is the second guard, not the first. */
			e[1] = (c == '\n') ? 'n' : (c == '\r') ? 'r' : 't';
			jw_put(w, e, 2);
		} else if (c < 0x20 || c >= 0x7f) {
			w->err = 1;       /* not representable by this writer */
			return;
		} else {
			jw_ch(w, (char)c);
		}
	}
	jw_ch(w, '"');
}

void json_w_str(struct json_w *w, const char *key, const char *val)
{
	json_w_strn(w, key, val, strlen(val));
}

void json_w_num(struct json_w *w, const char *key, uint32_t v)
{
	char d[12];
	size_t i = sizeof(d);

	json_w_key(w, key);
	if (v == 0) {
		jw_ch(w, '0');
		return;
	}
	while (v > 0 && i > 0) {
		d[--i] = (char)('0' + (v % 10u));
		v /= 10u;
	}
	jw_put(w, d + i, sizeof(d) - i);
}

void json_w_bool(struct json_w *w, const char *key, int v)
{
	json_w_key(w, key);
	if (v)
		jw_put(w, "true", 4);
	else
		jw_put(w, "false", 5);
}

/* A value the caller has already rendered (a nested object built by the same
 * writer).  `raw` must come from this file's own output, never from input. */
void json_w_raw(struct json_w *w, const char *key, const char *raw)
{
	json_w_key(w, key);
	jw_put(w, raw, strlen(raw));
}

int json_w_done(const struct json_w *w)
{
	return w->err ? -1 : 0;
}
