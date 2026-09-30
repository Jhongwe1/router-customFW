/* src/fuzz/fuzz_json.c -- one file in, the flat JSON parser over it.
 *
 * Plain main(argc, argv), for the same reason as fuzz_http.c: the afl run and the
 * gcov run must be over the same harness or the coverage number is about a
 * program nobody fuzzed.
 *
 * After a successful parse it also walks the result and re-serialises it through
 * the writer, so the writer's bounds are in the fuzzer's reach too, and asserts
 * the invariants the parser promises -- the lengths agree with the NUL
 * terminators, and no member is of a type the enum does not have.
 */

#include "json.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define IN_MAX (JSON_DOC_MAX + 64)

int main(int argc, char **argv)
{
	static unsigned char in[IN_MAX];
	struct json_obj o;
	FILE *f;
	size_t n;
	int rc;

	if (argc < 2)
		return 0;
	f = fopen(argv[1], "rb");
	if (f == NULL)
		return 0;
	n = fread(in, 1, sizeof(in), f);
	(void)fclose(f);

	rc = json_parse(in, n, &o);
	if (rc != 0) {
		/* every refusal must have a name; an unnamed code means a new
		 * error path appeared without a name */
		if (strcmp(json_errname(rc), "err") == 0)
			abort();
		return 0;
	}

	if (o.n > JSON_KEYS_MAX)
		abort();
	{
		unsigned i;
		char out[JSON_DOC_MAX * 2];
		struct json_w w;

		json_w_init(&w, out, sizeof(out));
		json_w_obj_open(&w);
		for (i = 0; i < o.n; i++) {
			const struct json_member *m = &o.m[i];

			if (m->klen != strlen(m->key))
				abort();
			switch (m->type) {
			case JT_STR:
				if (m->slen != strlen(m->sval))
					abort();
				json_w_strn(&w, m->key, m->sval, m->slen);
				break;
			case JT_NUM:
				json_w_num(&w, m->key, m->nval);
				break;
			case JT_BOOL:
				if (m->nval > 1)
					abort();
				json_w_bool(&w, m->key, (int)m->nval);
				break;
			case JT_NULL:
				json_w_raw(&w, m->key, "null");
				break;
			default:
				abort();       /* a type outside the enum */
			}
			if (json_get(&o, m->key) != m) {
				/* json_get must find each member at its own slot:
				 * if it does not, the duplicate-key refusal has a
				 * hole in it. */
				abort();
			}
		}
		json_w_obj_close(&w);
		if (json_w_done(&w) == 0) {
			/* What the writer wrote must parse back to the same number
			 * of members.  A round trip that loses one is a bug in
			 * whichever half is wrong, and the fuzzer does not care
			 * which. */
			struct json_obj o2;

			if (json_parse(out, strlen(out), &o2) == 0 && o2.n != o.n)
				abort();
		}
	}
	return 0;
}
