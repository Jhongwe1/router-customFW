#!/usr/bin/env python3
"""mutate.py -- plant one named defect in a COPY of a source file.

A green test suite is a claim about its controls, and the only way to test that
claim is to break the thing the suite says it checks and watch it go red.  This
script does exactly that, on a copy of the tree under $O/mutate, and it REFUSES
rather than silently doing nothing if the code it is meant to cut has moved: an
anchor that no longer matches means the control stopped being a control, which is
worse than a failing build.

Defects, each named by the check it removes:

  traversal   the ".." and "." segment refusals in http_decode_path(), including
              the whole-string strstr() backstop.  src/httpd/test_http.c's
              path-traversal battery must go red.
  hdrcap      the "more than HTTP_HDR_LINES_MAX header lines" refusal in
              http_feed().  The request-parser sweep must go red.
  offbyone    the fuzzing control: parse_header()'s header-name bound becomes `>`
              instead of `>=`, so a header whose NAME is exactly 64 characters
              writes `name[64] = '\\0'` one byte past a 64-byte local array.  This
              is the defect the fuzzer has to find, and it is NOT in the test
              suite's sights -- the point is that the fuzzer finds what the tests
              do not.

  linebound   the off-by-one that was planted FIRST, and the reason it is not the
              control: http_feed()'s line-buffer bound becomes `>` instead of `>=`,
              so `line[1025]` is written in a 1025-byte array.  量 2026-09-30: the
              mutant returns 0 on the exact input that triggers it, under
              -fsanitize=address, because `line` is a MEMBER of struct
              http_parser and the struct's next member (`r`, a pointer) is 4-byte
              aligned -- so byte 1025 lands in the struct's own padding.  ASan
              instruments object boundaries, not intra-object ones, and this write
              never leaves the object.  The defect is real and the sanitizer cannot
              see it; that is a fact about ASan and an argument for keeping parser
              scratch in bare local arrays, which get their own redzones.  Kept
              here named, so the next reader does not spend fifteen minutes of
              fuzzing finding it out again.

The streaming upload's controls (POST /api/firmware, upload.c and the parser's
bound for it).  Each is planted in a copy and src/httpd/test_serve.c must go red;
`make mutate` builds and runs the unmutated copy first and requires it green, so
a red mutant is the mutation's and not the tree's:

  upl_prebegin   a body byte forwarded before BEGIN's OK: BEGIN's refusal no
                 longer stops the upload, so the pieces go out after it.
  upl_bound      the 413 bound skipped: neither the header line nor the end of
                 the headers refuses a Content-Length past HTTP_UPLOAD_MAX for
                 the upload route, so BEGIN is called with 1,179,649.
  upl_bound_line only the header line's bound skipped; the end-of-headers check
                 still answers 413, so only the case that sends no blank line --
                 "refused AT the header line" -- can see it.
  upl_offset     an off-by-one in each DATA's offset.
  upl_piece      the piece size 2,045: one past UPD_DATA_MAX, so a DATA body is
                 2,049 bytes, one past what bk_call() sends (the buffer grows
                 with it, so the mutant is wrong and not undefined).
  upl_endafter   END sent after a DATA refusal.

Usage:  mutate.py <defect> <file.c>
Exit:   0 planted, 2 usage, 3 the anchor did not match (the control is broken).
"""

import sys

DEFECTS = {}


def defect(name):
    def deco(fn):
        DEFECTS[name] = fn
        return fn
    return deco


def cut(src, anchor, repl, what):
    if anchor not in src:
        sys.stderr.write(
            "mutate.py: REFUSED: the anchor for %s is not in the file.\n"
            "           The control cannot be planted, so it is not a control.\n"
            % what)
        sys.exit(3)
    if src.count(anchor) != 1:
        sys.stderr.write(
            "mutate.py: REFUSED: the anchor for %s matches %d times, not once.\n"
            % (what, src.count(anchor)))
        sys.exit(3)
    return src.replace(anchor, repl, 1)


@defect("traversal")
def m_traversal(s):
    s = cut(s, """			if (seglen == 1 && out[segstart] == '.')
				return -400;  /* "." */
			if (seglen == 2 && out[segstart] == '.' &&
			    out[segstart + 1] == '.')
				return -400;  /* ".." */
""", "", "the mid-path dot-segment refusals")
    s = cut(s, """	if (seglen == 1 && out[segstart] == '.')
		return -400;
	if (seglen == 2 && out[segstart] == '.' && out[segstart + 1] == '.')
		return -400;
""", "", "the final-segment dot refusals")
    s = cut(s, """	if (strstr(out, "..") != NULL)
		return -400;
""", "", "the whole-string .. backstop")
    return s


@defect("hdrcap")
def m_hdrcap(s):
    return cut(s, """				ps->nhdr++;
				if (ps->nhdr > HTTP_HDR_LINES_MAX) {
					ps->state = HS_ERR;
					ps->status = 431;
					*used = i;
					return -431;
				}
""", """				ps->nhdr++;
""", "the header-line count cap")


@defect("offbyone")
def m_offbyone(s):
    """parse_header()'s `name` is a BARE local array, so ASan gives it its own
    redzone and a one-byte overflow of it is a reported stack-buffer-overflow."""
    return cut(s, """	if (nlen >= sizeof(name))""",
               """	if (nlen > sizeof(name))""",
               "the header-name length bound")


@defect("linebound")
def m_linebound(s):
    return cut(s, """			if (ps->linelen >= cap) {""",
               """			if (ps->linelen > cap) {""",
               "the line-buffer bound")


# ---- the streaming upload's controls: upload.c, and http.c's bound for it ----

@defect("upl_prebegin")
def m_upl_prebegin(s):
    return cut(s, """	if (up_call(env, c, OP_UPDATE_BEGIN, 4, rs) != 0)
		return rs->status;
""", """	(void)up_call(env, c, OP_UPDATE_BEGIN, 4, rs);
""", "BEGIN's verdict stopping the upload")


def _bound_line(s):
    return cut(s, """		if (v > (ps->r->stream ? HTTP_UPLOAD_MAX : HTTP_BODY_MAX))""",
               """		if (!ps->r->stream && v > HTTP_BODY_MAX)""",
               "the upload route's bound at the header line")


@defect("upl_bound")
def m_upl_bound(s):
    s = _bound_line(s)
    return cut(s, """			if (r->clen > HTTP_UPLOAD_MAX)
				return -413;
			ps->state = HS_STREAM;
""", """			ps->state = HS_STREAM;
""", "the upload route's bound at the end of the headers")


@defect("upl_bound_line")
def m_upl_bound_line(s):
    return _bound_line(s)


@defect("upl_offset")
def m_upl_offset(s):
    return cut(s, """		proto_put_be32(c->msg, off);""",
               """		proto_put_be32(c->msg, off + 1);""",
               "each DATA's offset")


@defect("upl_piece")
def m_upl_piece(s):
    s = cut(s, """	uint8_t        msg[4 + UPD_DATA_MAX];""",
            """	uint8_t        msg[4 + UPD_DATA_MAX + 1];""",
            "the piece buffer")
    return cut(s, """		if (want > UPD_DATA_MAX)
			want = UPD_DATA_MAX;
""", """		if (want > UPD_DATA_MAX + 1)
			want = UPD_DATA_MAX + 1;
""", "the piece size")


@defect("upl_endafter")
def m_upl_endafter(s):
    return cut(s, """		if (up_call(env, c, OP_UPDATE_DATA, 4 + want, rs) != 0)
			return rs->status;
""", """		if (up_call(env, c, OP_UPDATE_DATA, 4 + want, rs) != 0) {
			proto_put_be32(c->msg, total);
			(void)up_call(env, c, OP_UPDATE_END, 4, rs);
			return rs->status;
		}
""", "the stop after a DATA refusal")


def main(argv):
    if len(argv) != 3 or argv[1] not in DEFECTS:
        sys.stderr.write("usage: mutate.py {%s} <file.c>\n"
                         % "|".join(sorted(DEFECTS)))
        return 2
    path = argv[2]
    with open(path, "r") as f:
        src = f.read()
    out = DEFECTS[argv[1]](src)
    if out == src:
        sys.stderr.write("mutate.py: REFUSED: nothing changed\n")
        return 3
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(out)
    import os
    os.replace(tmp, path)
    sys.stdout.write("planted %s in %s\n" % (argv[1], path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
