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
