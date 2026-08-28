#!/usr/bin/env python3
"""Are rlxfw's boot marks in the tree that was built, and only there?

R3-6's gate.  This is the first time rlxfw changes a line of Realtek's source,
and the whole design is that the change is a TABLE rather than a patch: one row
per insertion, each naming the suspect it brackets.

WHY A TABLE AND NOT A .patch FILE.
`config/host-compat/` already holds a patch and `tools/rlxfw-kbuild.sh` already
stops if one does not apply, so a patch was available and was not chosen.  A
patch says WHAT changed; it has nowhere to say WHY this line and not the line
above it, and on this project the reason is the artefact.  A patch also carries
context lines, so it goes stale against a drop it still applies to -- the
failure `kconfig-delta` exists to prevent one layer up.  The table carries an
anchor that must occur EXACTLY ONCE, which is a stronger statement than "the
context matched somewhere".

WHY THE VENDOR TREE ON DISK IS NEVER WRITTEN.
`src-vendor/` is three pinned clones and `notes/kernel-build.md` 8 already made
re-staging mandatory for a different reason (the build rewrites
`data_MAC_REG_88E.c` inside its own source tree).  `apply` therefore refuses to
run on anything it can reach through `$FWRE_WORK/rebuild/src-vendor`, and
`tools/vendor-tripwire.sh` is the second line.

THE CHECK THAT ACTUALLY MATTERS IS `verify`, NOT `check`.
`check` reads the staged tree and answers "did the insertion happen".  That is
the weak question: a mark can be inserted into a file that is not compiled, or
into a function the linker discards, and `check` would still be green.
`verify` reads the BUILT vmlinux and answers "is this string in the artefact
that will be uploaded, exactly once, and absent from the vendor's".  Both halves
are load-bearing: without the second, a mark is not a discriminator, and
`PROGRESS.md`'s anti-DoD is the record of what that costs -- 2026-08-25, a
second `J 80500000` booted the vendor kernel and the banner looked like a pass.

Usage
    tools/rlxfw-marks.py apply    --decl F --tree DIR --src DIR
    tools/rlxfw-marks.py check    --decl F --tree DIR
    tools/rlxfw-marks.py verify   --decl F --image F [--absent F]...
    tools/rlxfw-marks.py self-test
"""

import io
import os
import re
import shutil
import sys
import tempfile

VERSION = "1.0"

POSITIONS = ("before", "after")
COLS = ("id", "file", "position", "anchor", "insert", "reason")

# What a mark string looks like in the emitted image.  `rlxfw_mark("B0")`
# becomes the bytes `RLXFW-` + `B0`; `rlxfw_markx("B2", x)` becomes
# `RLXFW-` + `B2` + `=`.  The literal in the source is the tag alone, so the
# string to grep for is derived here and never typed twice.
PREFIX = "RLXFW-"
CALL_RE = re.compile(r'^rlxfw_mark(x?)\("([A-Za-z0-9_.:-]+)"(?:,\s*(.+))?\);$')

# The one other shape a row may carry.  A file of mine has to reach the link,
# and that is a Kbuild line, not a mark.  The vocabulary is closed at exactly
# these two: anything else and this file would be a patch format whose reviewer
# has to read arbitrary C.
OBJ_RE = re.compile(r'^obj-y\s*\+=\s*[A-Za-z0-9_./-]+\.o$')

# And the prototype, which is one exact literal rather than a pattern: the
# call sites are under `EXTRA_CFLAGS += -Werror`, so without it they do not
# build -- but "the declaration file may insert #includes" is a door this
# project does not need open, so only this one string goes through.
INCLUDE = "#include <linux/rlxfw-mark.h>"


def die(msg):
    sys.stderr.write("rlxfw-marks: %s\n" % msg)
    raise SystemExit(3)


# --------------------------------------------------------------------------
# the declaration
# --------------------------------------------------------------------------

class Row(object):
    def __init__(self, d, lineno):
        self.__dict__.update(d)
        self.lineno = lineno
        m = CALL_RE.match(self.insert)
        if not m:
            if OBJ_RE.match(self.insert) or self.insert == INCLUDE:
                self.kind = "build"
                self.computed, self.tag, self.expr = False, None, None
                return
            die("%s:%d: insert %r is not one of the three shapes this file "
                "allows: `rlxfw_mark(\"TAG\");`, `rlxfw_markx(\"TAG\", expr);`, "
                "`obj-y += NAME.o`, or the exact literal %r. This file "
                "declares marks, and an arbitrary statement here would be a "
                "patch with no reviewer"
                % (self.file, lineno, self.insert, INCLUDE))
        self.kind = "mark"
        self.computed = bool(m.group(1))
        self.tag = m.group(2)
        self.expr = m.group(3)
        if self.computed and not self.expr:
            die("%s:%d: rlxfw_markx needs a value expression" % (self.file,
                                                                 lineno))
        if not self.computed and self.expr:
            die("%s:%d: rlxfw_mark takes no value; use rlxfw_markx"
                % (self.file, lineno))

    @property
    def string(self):
        """The bytes this row puts in the image, or None for a build row.

        The TERMINATOR is part of it, and that is not tidiness.  量 on the
        first real verify: `RLXFW-B1` was found twice in the image, because
        `RLXFW-B10` contains it.  The macros emit `"RLXFW-" tag "\\n"` for a
        plain mark and `"RLXFW-" tag "="` for a computed one, so including the
        terminator makes the search string the whole literal and B1 stops
        matching B10.  `_no_prefix` below is the other half: the collision is
        also real on the wire, where a human greps a capture and no tool is
        involved at all.
        """
        if self.kind != "mark":
            return None
        return PREFIX + self.tag + ("=" if self.computed else "\n")


def _no_prefix(path, rows):
    """No mark tag may be a prefix of another.

    量 2026-08-28, on the first real `verify`: `RLXFW-B1` was counted twice in
    the built image because `RLXFW-B10` contains it.  `string` now carries the
    terminator so the tool is no longer fooled -- but the ambiguity does not
    live in the tool.  It lives in the capture, where a human types
    `grep RLXFW-B1` and gets B10's line as well, and where a boot that stopped
    at B1 and a boot that reached B10 read the same at a glance.  Tags are
    zero-padded for this reason and the rule is enforced rather than
    remembered.
    """
    tags = [r.tag for r in rows if r.kind == "mark"]
    for a in tags:
        for b in tags:
            if a != b and b.startswith(a):
                die("%s: tag %r is a prefix of %r. A capture cannot be grepped "
                    "for one without matching the other, so the ladder would "
                    "not be readable by the person reading it. Pad them"
                    % (path, a, b))


def parse_decl(path, text=None):
    """[Row].  Tab separated, six columns, a comment is `#` at column 0.

    A line this parser does not understand is an error, never a skip.  The
    thing being declared is a change to somebody else's source; a typo that
    silently dropped a row would leave an undeclared edit in the tree, which
    is the state `notes/kernel-build.md` 8 spent a session recovering from.
    """
    if text is None:
        with io.open(path, encoding="utf-8") as f:
            text = f.read()
    rows, seen, headers = [], {}, {}
    for lineno, ln in enumerate(text.split("\n"), 1):
        if not ln.strip():
            continue
        if ln.startswith("#"):
            m = re.match(r"^#\s*([a-z0-9-]+):\s*(.*)$", ln)
            if m:
                headers.setdefault(m.group(1), m.group(2).strip())
            continue
        f = ln.split("\t")
        if len(f) != len(COLS):
            die("%s:%d: %d tab-separated fields, expected %d (%s)"
                % (path, lineno, len(f), len(COLS), ", ".join(COLS)))
        d = dict(zip(COLS, f))
        if d["position"] not in POSITIONS:
            die("%s:%d: position %r is not one of %s"
                % (path, lineno, d["position"], "/".join(POSITIONS)))
        if not d["reason"].strip():
            die("%s:%d: %s has no reason. Every row here is a line of "
                "somebody else's source and the reason is the artefact"
                % (path, lineno, d["id"]))
        if not d["anchor"].strip():
            die("%s:%d: %s has an empty anchor" % (path, lineno, d["id"]))
        r = Row(d, lineno)
        if r.id in seen:
            die("%s:%d: id %s already used at line %d"
                % (path, lineno, r.id, seen[r.id]))
        # Two rows at the same place is two owners of one insertion point, and
        # the order between them would be decided by file order rather than by
        # anybody's intent.
        key = (r.file, r.position, r.anchor)
        if key in seen:
            die("%s:%d: %s inserts at the same (file, position, anchor) as "
                "line %d. Two rows at one point means the order is an "
                "accident" % (path, lineno, r.id, seen[key]))
        seen[r.id] = lineno
        seen[key] = lineno
        rows.append(r)
    _no_prefix(path, rows)
    if not rows:
        die("%s: no rows. An empty declaration would make `check` pass on a "
            "tree with no marks in it" % path)
    return rows, headers


# --------------------------------------------------------------------------
# apply / check
# --------------------------------------------------------------------------

def norm(s):
    """Leading/trailing whitespace stripped, internal runs collapsed to one.

    The collapse is not cosmetic: Kbuild lines are tab-aligned
    (`obj-$(CONFIG_EARLY_PRINTK)\t+= early_printk.o`) and this declaration is
    tab-separated, so an anchor carrying a literal tab would split into two
    columns.  Comparing normalised means the declaration can spell the anchor
    with single spaces.  It costs nothing in exactness here, because the
    exactly-once rule below is what does the work: a collapse that made two
    different lines equal would make the anchor ambiguous, and an ambiguous
    anchor is refused rather than resolved.
    """
    return " ".join(s.split())


def _find_anchor(lines, anchor, what):
    """The single index whose normalised text equals `anchor`, or die.

    Exactly-once is the point.  A patch that matched "somewhere" is how an
    insertion lands in the wrong one of two similar functions.
    """
    a = norm(anchor)
    hits = [i for i, ln in enumerate(lines) if norm(ln) == a]
    if len(hits) == 0:
        die("%s: anchor not found: %r. Not skipped -- an anchor that moved is "
            "a drop that moved, and the mark would silently not be there"
            % (what, anchor))
    if len(hits) > 1:
        die("%s: anchor occurs %d times: %r. Refusing to pick one"
            % (what, len(hits), anchor))
    return hits[0]


def _indent(s):
    return s[:len(s) - len(s.lstrip())]


def apply_marks(decl, tree, src, quiet=False):
    rows, _ = parse_decl(decl)

    real = os.path.realpath(tree)
    for bad in ("src-vendor",):
        if os.sep + bad + os.sep in real + os.sep:
            die("--tree %s resolves under %s/. This writes into the tree it is "
                "given and the pinned clones are read-only; stage a copy "
                "first (tools/rlxfw-kbuild.sh does)" % (tree, bad))

    # my own sources first, so a missing one stops before anything is edited
    staged = []
    for dirpath, _, files in os.walk(src):
        for fn in files:
            s = os.path.join(dirpath, fn)
            rel = os.path.relpath(s, src)
            d = os.path.join(tree, rel)
            if not os.path.isdir(os.path.dirname(d)):
                die("--src carries %s but %s has no %s/ to put it in"
                    % (rel, tree, os.path.dirname(rel)))
            staged.append((rel, s, d))
    if not staged:
        die("--src %s is empty. The marks call rlxfw_mark(), which lives in a "
            "file of mine; without it the tree does not link" % src)
    for rel, s, d in staged:
        shutil.copyfile(s, d)

    done = 0
    for r in rows:
        p = os.path.join(tree, r.file)
        if not os.path.isfile(p):
            die("%s: no such file under %s (row %s)" % (r.file, tree, r.id))
        with io.open(p, encoding="utf-8", errors="surrogateescape") as f:
            lines = f.read().split("\n")
        # Applying twice would emit the mark twice, which reads in a capture
        # as a boot loop.  Refuse rather than skip: a partially applied tree
        # builds, and what it builds is not what this file describes.
        if any(norm(r.insert) == norm(ln) for ln in lines):
            die("%s: %s is already in %s. This tree is not clean; re-stage it"
                % (r.id, r.insert, r.file))
        i = _find_anchor(lines, r.anchor, "%s (%s)" % (r.id, r.file))
        at = i if r.position == "before" else i + 1
        lines.insert(at, _indent(lines[i]) + r.insert)
        with io.open(p, "w", encoding="utf-8", errors="surrogateescape",
                     newline="") as f:
            f.write("\n".join(lines))
        done += 1

    if not quiet:
        print("rlxfw-marks %s" % VERSION)
        print("declaration %s   (%d mark(s))" % (decl, len(rows)))
        print("tree        %s" % tree)
        for rel, _, _ in staged:
            print("  staged    %s" % rel)
        for r in rows:
            print("  %-4s %-34s %s %s" % (r.id, r.file, r.position, r.anchor))
    return rows


def check_marks(decl, tree):
    """Every declared insertion is in the staged tree, exactly once."""
    rows, _ = parse_decl(decl)
    bad = []
    for r in rows:
        p = os.path.join(tree, r.file)
        if not os.path.isfile(p):
            bad.append((r, "no such file"))
            continue
        with io.open(p, encoding="utf-8", errors="surrogateescape") as f:
            lines = f.read().split("\n")
        hits = [j for j, ln in enumerate(lines) if norm(ln) == norm(r.insert)]
        if len(hits) != 1:
            bad.append((r, "%d occurrence(s), expected 1" % len(hits)))
            continue
        i = hits[0]
        j = i - 1 if r.position == "after" else i + 1
        if not (0 <= j < len(lines)) or norm(lines[j]) != norm(r.anchor):
            bad.append((r, "present but not %s its anchor %r"
                        % (r.position, r.anchor)))
    return rows, bad


# --------------------------------------------------------------------------
# verify -- the half that reads the artefact
# --------------------------------------------------------------------------

def _count(path, needle):
    with open(path, "rb") as f:
        b = f.read()
    n, i = 0, b.find(needle)
    while i >= 0:
        n += 1
        i = b.find(needle, i + 1)
    return n


def verify_marks(decl, image, absent):
    """Every mark string is in the image once, and in none of `absent`.

    The second half is what makes a mark a discriminator rather than a label.
    `RUNSHEET` P6 is this shape and it is why it carries FOUR numbers: without
    the positive one, the three zeros are also what a broken grep prints.
    """
    rows, _ = parse_decl(decl)
    marks = [r for r in rows if r.kind == "mark"]
    if not marks:
        die("%s declares no mark, only build rows. `verify` would then read an "
            "image and check nothing" % decl)
    res = []
    for r in marks:
        s = r.string.encode("ascii")
        got = _count(image, s)
        outs = [(a, _count(a, s)) for a in absent]
        res.append((r, got, outs))
    return marks, res


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

_C_FILE = "int f(void)\n{\n\tint ret = 0;\n\n\tone();\n\ttwo();\n\treturn ret;\n}\n"
_HDR = "# id\tfile\tposition\tanchor\tinsert\treason\n"


def _decl(*rows):
    return _HDR + "".join("\t".join(r) + "\n" for r in rows)


def self_test():
    rows = []

    def ck(name, ok, detail):
        rows.append((name, bool(ok), detail))

    def refuses(fn, *a, **kw):
        try:
            fn(*a, **kw)
            return False, "returned"
        except SystemExit as e:
            return True, "exit %s" % e.code

    tmp = tempfile.mkdtemp(prefix="rlxfw-marks-")
    try:
        tree = os.path.join(tmp, "tree")
        src = os.path.join(tmp, "src")
        os.makedirs(os.path.join(tree, "sub"))
        os.makedirs(src)
        with io.open(os.path.join(src, "mine.c"), "w") as f:
            f.write("void rlxfw_mark(const char *s){(void)s;}\n")

        def fresh():
            with io.open(os.path.join(tree, "sub", "a.c"), "w") as f:
                f.write(_C_FILE)
            return os.path.join(tree, "sub", "a.c")

        good = ("B0", "sub/a.c", "after", "one();",
                'rlxfw_mark("B0");', "the reason")

        # A1 -- an anchor that is not there is an error, never a skip.
        fresh()
        d = os.path.join(tmp, "d1")
        io.open(d, "w").write(_decl(("B0", "sub/a.c", "after", "nosuch();",
                                     'rlxfw_mark("B0");', "r")))
        ok, why = refuses(apply_marks, d, tree, src, quiet=True)
        ck("A1  a missing anchor is an error", ok, why)

        # A2 -- an ambiguous anchor is an error.  Two identical lines is
        # exactly the shape a patch would resolve by picking the first.
        p = fresh()
        io.open(p, "a").write("\tone();\n")
        d = os.path.join(tmp, "d2")
        io.open(d, "w").write(_decl(good))
        ok, why = refuses(apply_marks, d, tree, src, quiet=True)
        ck("A2  an anchor occurring twice is an error", ok, why)

        # A3 -- it inserts on the right side, with the anchor's indentation.
        p = fresh()
        d = os.path.join(tmp, "d3")
        io.open(d, "w").write(_decl(good))
        apply_marks(d, tree, src, quiet=True)
        got = io.open(p).read().split("\n")
        i = got.index('\trlxfw_mark("B0");')
        ck("A3  inserted after the anchor, at its indentation",
           got[i - 1].strip() == "one();" and got[i].startswith("\t"),
           "line %d is %r, previous %r" % (i, got[i], got[i - 1]))

        # A3b -- and `before` really is the other side.  Without this A3 would
        # pass on a tool that ignored the column entirely.
        p = fresh()
        d = os.path.join(tmp, "d3b")
        io.open(d, "w").write(_decl(("B0", "sub/a.c", "before", "one();",
                                     'rlxfw_mark("B0");', "r")))
        apply_marks(d, tree, src, quiet=True)
        got = io.open(p).read().split("\n")
        i = got.index('\trlxfw_mark("B0");')
        ck("A3b before puts it on the other side",
           got[i + 1].strip() == "one();", "next line %r" % got[i + 1])

        # A4 -- applying to an already-marked tree refuses.  A doubled mark
        # reads in a capture as a boot loop.
        d = os.path.join(tmp, "d4")
        io.open(d, "w").write(_decl(good))
        p = fresh()
        apply_marks(d, tree, src, quiet=True)
        ok, why = refuses(apply_marks, d, tree, src, quiet=True)
        ck("A4  applying twice refuses", ok, why)

        # A5 -- check fails when a mark is gone from the tree.
        _, bad = check_marks(d, tree)
        clean = not bad
        fresh()
        _, bad2 = check_marks(d, tree)
        ck("A5  check passes on a marked tree and fails on a bare one",
           clean and len(bad2) == 1,
           "marked %d bad, bare %d bad" % (len(bad), len(bad2)))

        # A6 -- check fails when the mark is present but has MOVED away from
        # its anchor.  Without this, `check` would be satisfied by a grep.
        p = fresh()
        apply_marks(d, tree, src, quiet=True)
        txt = io.open(p).read().split("\n")
        txt.remove('\trlxfw_mark("B0");')
        txt.insert(1, '\trlxfw_mark("B0");')
        io.open(p, "w", newline="").write("\n".join(txt))
        _, bad3 = check_marks(d, tree)
        ck("A6  a mark that moved off its anchor fails check",
           len(bad3) == 1 and "anchor" in bad3[0][1],
           "; ".join("%s: %s" % (r.id, w) for r, w in bad3) or "nothing bad")

        # A7 -- a row with no reason is an error.
        d7 = os.path.join(tmp, "d7")
        io.open(d7, "w").write(_decl(("B0", "sub/a.c", "after", "one();",
                                      'rlxfw_mark("B0");', "")))
        ok, why = refuses(parse_decl, d7)
        ck("A7  a row with no reason is an error", ok, why)

        # A8 -- the insert must be a mark call and nothing else.  This file
        # would otherwise be a patch format with no reviewer.
        d8 = os.path.join(tmp, "d8")
        io.open(d8, "w").write(_decl(("B0", "sub/a.c", "after", "one();",
                                      "system(\"rm -rf /\");", "r")))
        ok, why = refuses(parse_decl, d8)
        ck("A8  an insert that is not a mark call is an error", ok, why)

        # A9 -- two rows at one insertion point is two owners.
        d9 = os.path.join(tmp, "d9")
        io.open(d9, "w").write(_decl(good, ("B1", "sub/a.c", "after", "one();",
                                            'rlxfw_mark("B1");', "r")))
        ok, why = refuses(parse_decl, d9)
        ck("A9  two rows at one insertion point is an error", ok, why)

        # A10 -- verify reads the ARTEFACT: present once in mine, absent from
        # theirs.  Both halves, because three zeros with no positive is also
        # what a broken reader prints.
        mine = os.path.join(tmp, "mine.bin")
        theirs = os.path.join(tmp, "theirs.bin")
        open(mine, "wb").write(b"..RLXFW-B0\n\0..")
        open(theirs, "wb").write(b"..nothing here..")
        _, res = verify_marks(d, mine, [theirs])
        r0, got, outs = res[0]
        ck("A10 verify: present in mine, absent from theirs",
           got == 1 and outs[0][1] == 0, "mine %d, theirs %d" % (got,
                                                                 outs[0][1]))

        # A11 -- and it fails both ways round.
        open(theirs, "wb").write(b"..RLXFW-B0\n..")
        _, res = verify_marks(d, mine, [theirs])
        contaminated = res[0][2][0][1]
        open(mine, "wb").write(b"..nothing..")
        _, res = verify_marks(d, mine, [theirs])
        ck("A11 verify fails when the mark is in the vendor image, and when "
           "it is missing from mine",
           contaminated == 1 and res[0][1] == 0,
           "vendor hit %d, mine %d" % (contaminated, res[0][1]))

        # A12 -- apply refuses to write into the pinned clones.
        fake = os.path.join(tmp, "src-vendor", "drop")
        os.makedirs(fake)
        ok, why = refuses(apply_marks, d, fake, src, quiet=True)
        ck("A12 apply refuses a tree under src-vendor/", ok, why)

        # A13 -- a declared source of mine that is missing is an error, and is
        # never replaced with something similar.  mkinitramfs A2's shape.
        empty = os.path.join(tmp, "empty-src")
        os.makedirs(empty)
        p = fresh()
        ok, why = refuses(apply_marks, d, tree, empty, quiet=True)
        ck("A13 an empty --src is an error", ok, why)

        # A14 -- the string that is looked for in the image is DERIVED from
        # the call, not typed twice.  markx adds the '='.
        d14 = os.path.join(tmp, "d14")
        io.open(d14, "w").write(_decl(
            ("B0", "sub/a.c", "after", "one();", 'rlxfw_mark("B0");', "r"),
            ("B2", "sub/a.c", "after", "two();",
             'rlxfw_markx("B2", read_c0_prid());', "r")))
        rr, _ = parse_decl(d14)
        ck("A14 the image string is derived from the call, never typed twice",
           rr[0].string == "RLXFW-B0\n" and rr[1].string == "RLXFW-B2="
           and rr[1].expr == "read_c0_prid()",
           "%r / %r, expr %r" % (rr[0].string, rr[1].string, rr[1].expr))

        # A15 -- an empty declaration would make `check` vacuously green.
        d15 = os.path.join(tmp, "d15")
        io.open(d15, "w").write(_HDR)
        ok, why = refuses(parse_decl, d15)
        ck("A15 an empty declaration is an error", ok, why)

        # A16 -- a tag that is a prefix of another is refused.  This is the
        # defect the first real `verify` found: RLXFW-B1 matched RLXFW-B10 in
        # the image AND would match it in a capture.
        d16 = os.path.join(tmp, "d16")
        io.open(d16, "w").write(_decl(
            ("X1", "sub/a.c", "after", "one();", 'rlxfw_mark("B1");', "r"),
            ("X2", "sub/a.c", "after", "two();", 'rlxfw_mark("B10");', "r")))
        ok, why = refuses(parse_decl, d16)
        ck("A16 a tag that is a prefix of another is refused", ok, why)

        # A17 -- and the search string carries its terminator, so even a tool
        # reading a padded set is looking for the whole literal.
        d17 = os.path.join(tmp, "d17")
        io.open(d17, "w").write(_decl(
            ("X1", "sub/a.c", "after", "one();", 'rlxfw_mark("B01");', "r"),
            ("X2", "sub/a.c", "after", "two();",
             'rlxfw_markx("B02", v());', "r")))
        rr, _ = parse_decl(d17)
        ck("A17 the search string carries the macro's terminator",
           rr[0].string == "RLXFW-B01\n" and rr[1].string == "RLXFW-B02=",
           "%r / %r" % (rr[0].string, rr[1].string))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("rlxfw-marks %s -- controls" % VERSION)
    nf = 0
    for name, ok, detail in rows:
        if not ok:
            nf += 1
        print("  %-5s %-58s %s" % ("ok" if ok else "FAIL", name, detail))
    print("")
    if nf:
        print("RESULT: %d passed, \033[31m%d failed\033[0m" % (len(rows) - nf,
                                                               nf))
        return 2
    print("RESULT: \033[32m%d passed, 0 failed\033[0m" % len(rows))
    return 0


# --------------------------------------------------------------------------

def main(argv):
    if not argv:
        sys.stderr.write(__doc__)
        return 3
    cmd, argv = argv[0], argv[1:]
    a = {"decl": None, "tree": None, "src": None, "image": None, "absent": []}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == "--absent":
            a["absent"].append(argv[i + 1]); i += 2
        elif x.startswith("--") and x[2:] in a:
            a[x[2:]] = argv[i + 1]; i += 2
        else:
            die("unknown option %s" % x)

    if cmd == "self-test":
        return self_test()

    if cmd == "apply":
        for k in ("decl", "tree", "src"):
            if not a[k]:
                die("apply needs --%s" % k)
        apply_marks(a["decl"], a["tree"], a["src"])
        rows, bad = check_marks(a["decl"], a["tree"])
        if bad:
            for r, why in bad:
                print("  %-4s %s: %s" % (r.id, r.file, why))
            print("REFUSED: apply ran and check does not agree with it")
            return 2
        print("")
        print("RESULT: \033[32m%d mark(s) applied and read back\033[0m"
              % len(rows))
        return 0

    if cmd == "check":
        for k in ("decl", "tree"):
            if not a[k]:
                die("check needs --%s" % k)
        rows, bad = check_marks(a["decl"], a["tree"])
        print("rlxfw-marks %s" % VERSION)
        print("declaration %s   (%d mark(s))" % (a["decl"], len(rows)))
        print("tree        %s" % a["tree"])
        for r, why in bad:
            print("  \033[31mBAD\033[0m  %-4s %-28s %s" % (r.id, r.file, why))
        print("")
        if bad:
            print("RESULT: \033[31m%d of %d mark(s) not as declared\033[0m"
                  % (len(bad), len(rows)))
            return 1
        print("RESULT: \033[32mall %d mark(s) present at their anchors\033[0m"
              % len(rows))
        return 0

    if cmd == "verify":
        if not a["decl"] or not a["image"]:
            die("verify needs --decl and --image")
        rows, res = verify_marks(a["decl"], a["image"], a["absent"])
        print("rlxfw-marks %s" % VERSION)
        print("image       %s" % a["image"])
        if not a["absent"]:
            print("  \033[31mno --absent file given\033[0m -- then `present in "
                  "mine` is a label, not a discriminator")
        bad = 0
        for r, got, outs in res:
            m = "" if got == 1 else "  <- must be 1"
            o = " ".join("%s:%d" % (os.path.basename(f), n) for f, n in outs)
            if got != 1 or any(n for _, n in outs):
                bad += 1
            shown = r.string.replace("\n", "\\n")
            print("  %-4s %-14s mine:%d %s%s" % (r.id, shown, got, o, m))
        print("")
        if bad or not a["absent"]:
            print("RESULT: \033[31m%d mark(s) not a discriminator\033[0m" % bad)
            return 1
        print("RESULT: \033[32mall %d mark(s) present once in the image and "
              "absent from %d vendor artefact(s)\033[0m"
              % (len(rows), len(a["absent"])))
        return 0

    die("unknown command %r" % cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
