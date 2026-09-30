/* src/httpd/test_json.c -- the JSON parser battery.
 *
 * The cases are grouped by what they are trying to reach, not by what they look
 * like: a nesting bomb, a number that does not fit, a string that does not fit, a
 * duplicate key, a truncation at every offset, and the writer's own bound.  The
 * point of the truncation loop is that a parser is usually correct on whole
 * documents and wrong on partial ones.
 */

#include "json.h"
#include "testlib.h"

#include <string.h>

static void case_err(const char *doc, int want, const char *name)
{
	struct json_obj o;
	int rc = json_parse(doc, strlen(doc), &o);

	t_okf(rc == -want, name, rc, -want);
}

static void case_ok(const char *doc, const char *name)
{
	struct json_obj o;
	int rc = json_parse(doc, strlen(doc), &o);

	t_okf(rc == 0, name, rc, 0);
}

int main(void)
{
	struct json_obj o;
	char big[JSON_DOC_MAX + 64];
	char buf[64];
	struct json_w w;
	unsigned i;

	/* ------------------------------------------------ accepted documents */
	case_ok("{}", "empty object");
	case_ok("{\"a\":1}", "one number");
	case_ok("  {  \"a\" : 1 , \"b\" : \"x\" }  ", "whitespace everywhere");
	case_ok("{\"a\":true,\"b\":false,\"c\":null}", "the three literals");
	case_ok("{\"a\":0}", "zero");
	case_ok("{\"a\":4294967295}", "u32 max");
	case_ok("{\"a\":\"\"}", "empty string value");
	case_ok("{\"a\":\"\\\"\\\\\\/\\b\\f\\n\\r\\t\"}", "the eight simple escapes");
	case_ok("{\"a\":\"\\u0041\"}", "a \\u escape inside printable ASCII");

	/* ----------------------------------------------------- refusals, each
	 * naming the rule it is aimed at */
	case_err("", JSONE_SYNTAX, "empty input");
	case_err("[]", JSONE_SYNTAX, "top level array");
	case_err("1", JSONE_SYNTAX, "top level number");
	case_err("\"x\"", JSONE_SYNTAX, "top level string");
	case_err("{", JSONE_SYNTAX, "truncated after brace");
	case_err("{\"a\"", JSONE_SYNTAX, "truncated after key");
	case_err("{\"a\":", JSONE_SYNTAX, "truncated after colon");
	case_err("{\"a\":1", JSONE_SYNTAX, "truncated before close");
	case_err("{\"a\":1,}", JSONE_SYNTAX, "trailing comma");
	case_err("{,}", JSONE_SYNTAX, "leading comma");
	case_err("{\"a\" 1}", JSONE_SYNTAX, "missing colon");
	case_err("{a:1}", JSONE_SYNTAX, "unquoted key");
	case_err("{\"\":1}", JSONE_SYNTAX, "empty key");
	case_err("{}}", JSONE_TRAIL, "trailing brace");
	case_err("{} x", JSONE_TRAIL, "trailing text");
	case_err("{\"a\":{\"b\":1}}", JSONE_DEPTH, "nested object");
	case_err("{\"a\":[1]}", JSONE_DEPTH, "array value");
	case_err("{\"a\":-1}", JSONE_NUM, "negative number");
	case_err("{\"a\":+1}", JSONE_NUM, "explicit plus");
	case_err("{\"a\":1.5}", JSONE_NUM, "fraction");
	case_err("{\"a\":1e3}", JSONE_NUM, "exponent");
	case_err("{\"a\":01}", JSONE_NUM, "leading zero");
	case_err("{\"a\":4294967296}", JSONE_NUM, "u32 max plus one");
	case_err("{\"a\":99999999999999999999}", JSONE_NUM, "a huge number");
	case_err("{\"a\":1,\"a\":2}", JSONE_DUP, "duplicate key");
	case_err("{\"a\":tru}", JSONE_SYNTAX, "truncated literal");
	case_err("{\"a\":TRUE}", JSONE_SYNTAX, "uppercase literal");
	case_err("{\"a\":\"\\x41\"}", JSONE_ESC, "unknown escape");
	case_err("{\"a\":\"\\u00ff\"}", JSONE_ESC, "\\u above 0x7e");
	case_err("{\"a\":\"\\u0000\"}", JSONE_ESC, "\\u0000");
	case_err("{\"a\":\"\\ud83d\"}", JSONE_ESC, "a surrogate half");
	/* `\u00"}` has four bytes after the u, so the parser reads them and finds
	 * '"' is not a hex digit: that is a bad escape, not a short document.  The
	 * expectation written before the run said SYNTAX; the code's answer is the
	 * more accurate of the two and both are refusals, so the test moved, not
	 * the parser.  The genuinely short case is the line below it. */
	case_err("{\"a\":\"\\u00\"}", JSONE_ESC, "\\u with a non-hex digit");
	case_err("{\"a\":\"\\u0", JSONE_SYNTAX, "\\u with fewer than four bytes left");
	case_err("{\"a\":\"x\ty\"}", JSONE_CHAR, "raw tab in a string");
	case_err("{\"a\":\"\x80\"}", JSONE_CHAR, "a byte above 0x7f");

	/* A NUL anywhere, which needs an explicit length rather than strlen. */
	{
		static const char doc[] = "{\"a\":\"x\0y\"}";
		int rc = json_parse(doc, sizeof(doc) - 1, &o);

		t_okf(rc == -JSONE_NUL, "a NUL inside the document", rc,
		      -JSONE_NUL);
	}

	/* A deeply nested input: this is the case a recursive parser dies on, and
	 * it must cost exactly one comparison here. */
	{
		size_t n = 0;

		big[n++] = '{';
		big[n++] = '"';
		big[n++] = 'a';
		big[n++] = '"';
		big[n++] = ':';
		while (n < 2000)
			big[n++] = '[';
		big[n] = '\0';
		{
			int rc = json_parse(big, n, &o);

			t_okf(rc == -JSONE_DEPTH, "2000 open brackets", rc,
			      -JSONE_DEPTH);
		}
	}

	/* A long string, one byte over the slot, and one byte under it. */
	{
		size_t n = 0;

		big[n++] = '{';
		big[n++] = '"';
		big[n++] = 'a';
		big[n++] = '"';
		big[n++] = ':';
		big[n++] = '"';
		for (i = 0; i < JSON_STR_MAX; i++)
			big[n++] = 'x';
		big[n++] = '"';
		big[n++] = '}';
		big[n] = '\0';
		t_okf(json_parse(big, n, &o) == 0, "a string of exactly 64",
		      json_parse(big, n, &o), 0);

		n = 0;
		big[n++] = '{';
		big[n++] = '"';
		big[n++] = 'a';
		big[n++] = '"';
		big[n++] = ':';
		big[n++] = '"';
		for (i = 0; i < JSON_STR_MAX + 1; i++)
			big[n++] = 'x';
		big[n++] = '"';
		big[n++] = '}';
		big[n] = '\0';
		t_okf(json_parse(big, n, &o) == -JSONE_LONG,
		      "a string of 65 is refused", json_parse(big, n, &o),
		      -JSONE_LONG);
	}

	/* A key over the slot, and more members than the table holds. */
	{
		size_t n = 0;

		big[n++] = '{';
		big[n++] = '"';
		for (i = 0; i < JSON_STR_MAX + 1; i++)
			big[n++] = 'k';
		big[n++] = '"';
		big[n++] = ':';
		big[n++] = '1';
		big[n++] = '}';
		big[n] = '\0';
		t_ok(json_parse(big, n, &o) == -JSONE_LONG, "a 65-byte key", NULL);

		n = 0;
		big[n++] = '{';
		for (i = 0; i < JSON_KEYS_MAX + 4; i++) {
			int k = (int)snprintf(big + n, sizeof(big) - n,
					      "%s\"k%u\":1", i ? "," : "", i);

			if (k < 0)
				break;
			n += (size_t)k;
		}
		big[n++] = '}';
		big[n] = '\0';
		t_ok(json_parse(big, n, &o) == -JSONE_MANY,
		     "more members than the table holds", NULL);
	}

	/* A document over the hard cap. */
	{
		size_t n;

		memset(big, 'x', sizeof(big));
		big[0] = '{';
		n = JSON_DOC_MAX + 1;
		t_ok(json_parse(big, n, &o) == -JSONE_BIG,
		     "a document over JSON_DOC_MAX", NULL);
	}

	/* Truncation at every offset of a valid document: none may be accepted
	 * except the whole thing, and none may read past its length (ASAN). */
	{
		static const char doc[] =
			"{\"sys.hostname\":\"router-1\",\"dhcpd.enable\":true,"
			"\"dhcpd.lease\":86400}";
		size_t len = sizeof(doc) - 1;
		size_t cut;
		int accepted = 0;

		for (cut = 0; cut < len; cut++) {
			if (json_parse(doc, cut, &o) == 0)
				accepted++;
		}
		t_okf(accepted == 0, "no proper prefix of a document is accepted",
		      accepted, 0);
		t_okf(json_parse(doc, len, &o) == 0, "the whole document parses",
		      json_parse(doc, len, &o), 0);
		t_okf(o.n == 3, "three members", o.n, 3);
	}

	/* Values arrive where they are asked for. */
	{
		const struct json_member *m;

		(void)json_parse("{\"a\":\"xy\",\"b\":7,\"c\":true}", 25, &o);
		m = json_get(&o, "a");
		t_ok(m != NULL && m->type == JT_STR && m->slen == 2 &&
		     strcmp(m->sval, "xy") == 0, "string value read back", NULL);
		m = json_get(&o, "b");
		t_ok(m != NULL && m->type == JT_NUM && m->nval == 7,
		     "number value read back", NULL);
		m = json_get(&o, "c");
		t_ok(m != NULL && m->type == JT_BOOL && m->nval == 1,
		     "bool value read back", NULL);
		t_ok(json_get(&o, "zz") == NULL, "an absent key is NULL", NULL);
	}

	/* The writer: it must refuse to overflow rather than truncate silently. */
	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_str(&w, "k", "v");
	json_w_num(&w, "n", 4294967295u);
	json_w_bool(&w, "b", 1);
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) == 0 &&
	     strcmp(buf, "{\"k\":\"v\",\"n\":4294967295,\"b\":true}") == 0,
	     "writer output", buf);

	json_w_init(&w, buf, 8);
	json_w_obj_open(&w);
	json_w_str(&w, "key", "a long value that cannot fit");
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) != 0, "the writer reports truncation", NULL);

	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_str(&w, "k", "a\"b\\c");
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) == 0 && strcmp(buf, "{\"k\":\"a\\\"b\\\\c\"}") == 0,
	     "the writer escapes quote and backslash", buf);

	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_strn(&w, "k", "a\x01z", 3);
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) != 0,
	     "the writer refuses a control byte rather than emitting it", NULL);

	/* The three whitespace controls ARE escaped, because a PING body is the
	 * lines of a program's stdout and refusing a newline would turn a working
	 * diagnostic into a 500.  Found by test_routes.c's ping case, not by
	 * reading this file. */
	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_strn(&w, "k", "a\nb\tc\rd", 7);
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) == 0 &&
	     strcmp(buf, "{\"k\":\"a\\nb\\tc\\rd\"}") == 0,
	     "newline, tab and CR are escaped", buf);
	t_ok(json_parse(buf, strlen(buf), &o) == 0 && o.n == 1 &&
	     o.m[0].slen == 7 && o.m[0].sval[1] == '\n',
	     "and the parser reads them back", NULL);

	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_strn(&w, "k", "a\x7fz", 3);
	json_w_obj_close(&w);
	t_ok(json_w_done(&w) != 0, "the writer refuses 0x7f", NULL);

	/* The parser's own round trip: what the writer writes, the parser reads. */
	json_w_init(&w, buf, sizeof(buf));
	json_w_obj_open(&w);
	json_w_str(&w, "a", "b");
	json_w_num(&w, "c", 12345);
	json_w_obj_close(&w);
	t_ok(json_parse(buf, strlen(buf), &o) == 0 && o.n == 2,
	     "writer output parses back", NULL);

	return t_done(60);
}
