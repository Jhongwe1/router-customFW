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
    tools/rlxfw-marks.py verify   --decl F --image F [--absent F]... [--map F]
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
COLS = ("id", "file", "position", "anchor", "insert", "witness", "reason")

# MARK-1.  A `witness` is what a BUILD row leaves in the artefact.
#
# 量 2026-09-03: `verify`'s sentence -- *present exactly once in mine, absent
# from the vendor's* -- covered 12 marks and NOT the 642-line driver that `MK2`
# brings in, because an `obj-y +=` line has no string of its own.  A row that
# links a whole file into the image was the one row `verify` said nothing
# about, and `check` cannot help: `check` reads the TREE, so it only ever says
# the Makefile line is there.  A driver that compiles and is not linked is
# green under both.
#
# TWO FORMS, and the second exists because a measurement forced it:
#
#   str:<literal>   the bytes must be in the image at least once, and in none
#                   of the --absent artefacts.  The same test a mark gets.
#   sym:<name>      the symbol must be in System.map (--map).
#
# 🔴 A string-only column would not have worked, and finding out why is the
# reason the column is typed.  `rlxfw_mark.c` -- the file `MK` links -- holds
# NO string literal unique to it.  Its only literal is the hex table
# "0123456789ABCDEF", which lib/vsnprintf.c's own table contains as a prefix,
# so it is in the vendor's image too.  The obvious substitute, `RLXFW-`, is
# emitted by the CALL SITES in init/main.c and setup.c, not by this file: it
# would be present in an image where rlxfw_mark.o failed to link, which makes
# it a FALSE witness rather than a weak one.  So `MK` gets a symbol and `MK2`
# gets a string, and neither is a stand-in for the other.
WITNESS_KINDS = ("str", "sym")

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
        self.wkind = self.wval = None
        w = self.witness.strip()
        if w:
            if ":" not in w:
                die("%s:%d: witness %r has no kind. Write `str:<literal>` or "
                    "`sym:<name>`" % (self.file, lineno, w))
            k, v = w.split(":", 1)
            if k not in WITNESS_KINDS:
                die("%s:%d: witness kind %r is not one of: %s"
                    % (self.file, lineno, k, ", ".join(WITNESS_KINDS)))
            if not v:
                die("%s:%d: witness %r has an empty value" % (self.file,
                                                              lineno, w))
            self.wkind, self.wval = k, v
        m = CALL_RE.match(self.insert)
        if not m:
            if OBJ_RE.match(self.insert) or self.insert == INCLUDE:
                self.kind = "build"
                self.computed, self.tag, self.expr = False, None, None
                # An `obj-y +=` row links a FILE into the image, and that file
                # is what nothing checked. The include rows link nothing, so
                # they must NOT carry one -- a witness there would be a claim
                # about somebody else's object.
                links_a_file = bool(OBJ_RE.match(self.insert))
                if links_a_file and not self.wkind:
                    die("%s:%d: %s links a file into the image and declares "
                        "no witness. `verify` would then say nothing at all "
                        "about that file -- which is the state MARK-1 records"
                        % (self.file, lineno, self.id))
                if not links_a_file and self.wkind:
                    die("%s:%d: %s inserts an #include, which links nothing, "
                        "so a witness here would be a claim about an object "
                        "this row does not bring in"
                        % (self.file, lineno, self.id))
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
        if self.wkind:
            die("%s:%d: %s is a mark, and a mark's witness is its own string. "
                "A second declaration here would be a second owner of one "
                "check" % (self.file, lineno, self.id))
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


def _copy_if_different(s, d):
    """-> True when the file was written.

    Not `shutil.copyfile` unconditionally: kbuild triggers on mtime, so
    re-copying an identical file forces its object to rebuild and puts a floor
    under every incremental measurement. `INC-1` is a measurement of that
    floor, so the instrument must not create one.
    """
    if os.path.isfile(d):
        with open(s, "rb") as a, open(d, "rb") as b:
            if a.read() == b.read():
                return False
    shutil.copyfile(s, d)
    return True


def tree_mark_state(decl, tree):
    """-> ('clean' | 'applied' | 'partial', rows, detail)

    The three states a staged tree can be in, and the reason there are three
    rather than two:

    * ``clean``   -- every declared insert occurs **zero** times. `apply` runs.
    * ``applied`` -- every declared insert occurs **exactly once, at its
      anchor**. `apply --if-needed` is a no-op and exits 0.
    * ``partial`` -- anything else: some present and some not, one present
      twice, one present at the wrong place. 🔴 **This is the state `A4`
      exists to refuse and `--if-needed` must not launder.** A partially
      marked tree builds, and what it builds is not what the declaration
      describes -- a doubled mark reads in a capture as a boot loop.
    """
    rows, _ = parse_decl(decl)
    counts = {}
    for r in rows:
        p = os.path.join(tree, r.file)
        if not os.path.isfile(p):
            return "partial", rows, "%s: no such file under %s" % (r.file, tree)
        with io.open(p, encoding="utf-8", errors="surrogateescape") as f:
            lines = f.read().split("\n")
        counts[r.id] = sum(1 for ln in lines if norm(ln) == norm(r.insert))
    if all(n == 0 for n in counts.values()):
        return "clean", rows, ""
    _, bad = check_marks(decl, tree)
    if not bad:
        return "applied", rows, ""
    present = [i for i, n in counts.items() if n]
    return ("partial", rows,
            "%d of %d insert(s) present (%s); %s"
            % (len(present), len(rows), ", ".join(sorted(present)),
               "; ".join("%s: %s" % (r.id, why) for r, why in bad[:3])))


def apply_marks(decl, tree, src, quiet=False, if_needed=False):
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
    copied = [rel for rel, s, d in staged if _copy_if_different(s, d)]

    # --if-needed: the idempotent path, and it refuses the middle state.
    # It runs AFTER --src is staged, because a tree can be correctly marked
    # and still be missing a file of mine that changed.
    if if_needed:
        state, rows, detail = tree_mark_state(decl, tree)
        if state == "applied":
            if not quiet:
                print("rlxfw-marks %s" % VERSION)
                print("tree        %s" % tree)
                print("  already   %d mark(s) present at their anchors; "
                      "nothing inserted" % len(rows))
                for rel in copied:
                    print("  restaged  %s (content differed)" % rel)
            return rows
        if state == "partial":
            die("this tree is PARTIALLY marked and --if-needed will not "
                "repair it: %s. A tree in this state builds, and what it "
                "builds is not what %s describes. Re-stage it."
                % (detail, decl))
        # state == "clean": fall through and apply

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
            print("  staged    %s%s"
                  % (rel, "" if rel in copied else "  (unchanged, not rewritten)"))
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


def _symbols(path):
    """The symbol names in a System.map, as a set.

    `nm`-style: `<addr> <type> <name>`.  Only the third field is taken, so a
    symbol whose NAME contains another symbol's name cannot match by accident
    -- which is the same collision `_no_prefix` exists for one layer up.
    """
    out = set()
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            p = ln.split()
            if len(p) >= 3:
                out.add(p[2])
    return out


def verify_marks(decl, image, absent, mapfile=None):
    """Every mark string is in the image once, and in none of `absent`.

    The second half is what makes a mark a discriminator rather than a label.
    `RUNSHEET` P6 is this shape and it is why it carries FOUR numbers: without
    the positive one, the three zeros are also what a broken grep prints.

    MARK-1: build rows that link a file carry a `witness` and it is checked
    here too -- a `str:` against the same image and the same `absent` list, a
    `sym:` against `mapfile`.
    """
    rows, _ = parse_decl(decl)
    marks = [r for r in rows if r.kind == "mark"]
    wits = [r for r in rows if r.wkind]
    if not marks:
        die("%s declares no mark, only build rows. `verify` would then read an "
            "image and check nothing" % decl)
    res = []
    for r in marks:
        s = r.string.encode("ascii")
        got = _count(image, s)
        outs = [(a, _count(a, s)) for a in absent]
        res.append((r, got, outs))

    # 🔴 An `--absent` artefact that carries TWO OR MORE distinct declared mark
    # strings is one of MY images, and using it as the negative control is a
    # category error rather than a failing check.
    #
    # 量 2026-09-04, the first real run of the witness column: `--absent
    # r51a.vmlinux.elf` was passed, and every one of the twelve marks and the
    # `MK2` witness went red -- correctly, because that file is a build of this
    # declaration from the day before.  Thirteen rows said *not a
    # discriminator* and the tool had no way to say *you handed me your own
    # image*.
    #
    # 🔴 THE THRESHOLD IS TWO, AND THE FIRST DRAFT'S ONE WAS WRONG.  That
    # version refused any artefact containing `RLXFW-` at all, and it broke
    # `A11` -- the control that checks `verify` fails when a mark turns up in
    # the vendor's image, which needs exactly one contaminating hit to exist.
    # **One mark in a foreign artefact is a FINDING and A11 is what tests it;
    # two or more distinct ones is a build of this declaration.**  A vendor
    # image containing one of my strings by accident is conceivable; one
    # containing twelve is not.
    #
    # ⚠️ Keying on `RLXFW-ID0=` alone was considered and rejected: it is
    # present in every CURRENT build of mine and absent from a vendor's, which
    # is exactly the shape wanted -- but it under-detects a build of mine from
    # before that row existed, and `quietm.vmlinux.elf` (2026-08-28) is
    # measurably such a file.
    for path in absent:
        hits = [r.tag for r in marks
                if _count(path, r.string.encode("ascii"))]
        if len(hits) >= 2:
            die("--absent %s contains %d of this declaration's %d mark "
                "strings (%s), so it is a build of THIS declaration. A "
                "negative control has to be an artefact that is not one of "
                "mine -- the vendor's vmlinux, or a build from before the row "
                "existed. Every row would go red and none of the reds would "
                "be about the image under test"
                % (path, len(hits), len(marks), ", ".join(hits[:5])))

    # 🔴 A `sym:` witness with no --map is a REFUSAL, not a skip.  A skip would
    # print a green RESULT over a check that did not run, which is the exact
    # shape of the hole MARK-1 opened on.
    if any(r.wkind == "sym" for r in wits) and not mapfile:
        die("%s declares %d sym: witness(es) and no --map was given. Skipping "
            "them would print a green result over a check that did not run"
            % (decl, sum(1 for r in wits if r.wkind == "sym")))
    syms = _symbols(mapfile) if mapfile else set()

    wres = []
    for r in wits:
        if r.wkind == "str":
            s = r.wval.encode("ascii")
            got = _count(image, s)
            outs = [(a, _count(a, s)) for a in absent]
            ok = got >= 1 and not any(n for _, n in outs)
        else:
            got = 1 if r.wval in syms else 0
            outs = []
            ok = bool(got)
        wres.append((r, got, outs, ok))
    return marks, res, wres


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

_C_FILE = "int f(void)\n{\n\tint ret = 0;\n\n\tone();\n\ttwo();\n\treturn ret;\n}\n"
_HDR = "# id\tfile\tposition\tanchor\tinsert\twitness\treason\n"


def _decl(*rows):
    """A 6-tuple is padded with an EMPTY witness, so the twenty existing
    cases keep their meaning without twenty edits; a 7-tuple carries one.
    W8 is what says the file itself still requires seven fields."""
    out = []
    for r in rows:
        r = tuple(r)
        if len(r) == 6:
            r = r[:5] + ("",) + r[5:]
        out.append("\t".join(r) + "\n")
    return _HDR + "".join(out)


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
        _, res, _w = verify_marks(d, mine, [theirs])
        r0, got, outs = res[0]
        ck("A10 verify: present in mine, absent from theirs",
           got == 1 and outs[0][1] == 0, "mine %d, theirs %d" % (got,
                                                                 outs[0][1]))

        # A11 -- and it fails both ways round.
        open(theirs, "wb").write(b"..RLXFW-B0\n..")
        _, res, _w = verify_marks(d, mine, [theirs])
        contaminated = res[0][2][0][1]
        open(mine, "wb").write(b"..nothing..")
        _, res, _w = verify_marks(d, mine, [theirs])
        ck("A11 verify fails when the mark is in the vendor image, and when "
           "it is missing from mine",
           contaminated == 1 and res[0][1] == 0,
           "vendor hit %d, mine %d" % (contaminated, res[0][1]))

        # ---------------------------------------------------------- MARK-1
        # W1..W8.  A build row that LINKS A FILE has to say what that file
        # leaves behind, and `verify` has to check it.  量 2026-09-03: before
        # this column, `verify`'s sentence covered 12 marks and said nothing
        # at all about the 642-line driver `MK2` brings in.
        mkrow = ("MK9", "sub/Makefile", "after", "obj-y += x.o",
                 "obj-y += drv.o", "str:mydriver-name", "links a driver")
        markrow = ("B0", "sub/a.c", "after", "one();",
                   'rlxfw_mark("B0");', "", "r")
        d20 = os.path.join(tmp, "d20")
        io.open(d20, "w").write(_decl(markrow, mkrow))
        rr, _ = parse_decl(d20)
        ck("W1  a build row's witness parses",
           rr[1].wkind == "str" and rr[1].wval == "mydriver-name",
           "%s:%s" % (rr[1].wkind, rr[1].wval))

        # W2 -- THE ROW THAT MARK-1 IS ABOUT.  An obj-y row with no witness
        # is refused, because that is exactly the state `verify` was silent
        # about, and a silence is what this column removes.
        d21 = os.path.join(tmp, "d21")
        io.open(d21, "w").write(_decl(markrow, mkrow[:5] + ("", mkrow[6])))
        ok, why = refuses(parse_decl, d21)
        ck("W2  an obj-y row with NO witness is refused", ok, why)

        # W3 -- and an #include row must NOT have one: it links no object, so
        # a witness there would be a claim about somebody else's file.
        d22 = os.path.join(tmp, "d22")
        io.open(d22, "w").write(_decl(markrow,
            ("IN9", "sub/a.c", "after", "one();",
             "#include <linux/rlxfw-mark.h>", "sym:whatever", "r")))
        ok, why = refuses(parse_decl, d22)
        ck("W3  an #include row with a witness is refused", ok, why)

        # W4 -- nor may a MARK carry one; its witness is its own string, and
        # a second declaration would be a second owner of one check.
        d23 = os.path.join(tmp, "d23")
        io.open(d23, "w").write(_decl(
            ("B0", "sub/a.c", "after", "one();", 'rlxfw_mark("B0");',
             "str:anything", "r")))
        ok, why = refuses(parse_decl, d23)
        ck("W4  a mark row with a witness is refused", ok, why)

        # W5 -- an unknown witness kind, and a witness with no kind at all.
        for sfx, bad_w, what in (("a", "nope:x", "unknown kind"),
                                 ("b", "bare", "no kind"),
                                 ("c", "str:", "empty value")):
            dd = os.path.join(tmp, "d24" + sfx)
            io.open(dd, "w").write(_decl(markrow, mkrow[:5] + (bad_w,
                                                               mkrow[6])))
            ok, why = refuses(parse_decl, dd)
            ck("W5%s witness %-8s (%s) is refused" % (sfx, bad_w, what),
               ok, why)

        # W6 -- verify CHECKS a str: witness, both ways, on the same two
        # artefacts the marks are checked on.  The negative half is the point:
        # a witness present in the vendor's image proves nothing about mine.
        open(mine, "wb").write(b"..RLXFW-B0\n..mydriver-name..")
        open(theirs, "wb").write(b"..nothing here..")
        _m, _r, w = verify_marks(d20, mine, [theirs])
        ck("W6  verify: a str: witness present in mine, absent from theirs",
           len(w) == 1 and w[0][3] is True, str([(x[1], x[3]) for x in w]))
        open(theirs, "wb").write(b"..mydriver-name..")
        _m, _r, w2 = verify_marks(d20, mine, [theirs])
        open(mine, "wb").write(b"..RLXFW-B0\n..")
        _m, _r, w3 = verify_marks(d20, mine, [theirs])
        ck("W6b and it fails when the witness is in the vendor's image, "
           "and when it is missing from mine",
           w2[0][3] is False and w3[0][3] is False,
           "contaminated %s, missing %s" % (w2[0][3], w3[0][3]))

        # W7 -- a sym: witness is read from System.map, and 🔴 a sym: witness
        # with NO --map is a REFUSAL.  Skipping it would print a green result
        # over a check that did not run, which is the hole this column closes
        # written one level up.
        symrow = ("MK8", "sub/Makefile", "after", "obj-y += y.o",
                  "obj-y += sym.o", "sym:my_symbol", "links a file")
        d26 = os.path.join(tmp, "d26")
        io.open(d26, "w").write(_decl(markrow, symrow))
        mp = os.path.join(tmp, "System.map")
        io.open(mp, "w").write("80000000 T my_symbol\n80000010 t other\n")
        open(mine, "wb").write(b"..RLXFW-B0\n..")
        _m, _r, w = verify_marks(d26, mine, [theirs], mp)
        ck("W7  verify: a sym: witness found in System.map",
           w[0][3] is True, str(w[0][:3]))
        io.open(mp, "w").write("80000000 T something_else\n")
        _m, _r, w = verify_marks(d26, mine, [theirs], mp)
        ck("W7b and absent from it is a failure", w[0][3] is False,
           str(w[0][:3]))
        ok, why = refuses(verify_marks, d26, mine, [theirs])
        ck("W7c a sym: witness with no --map REFUSES rather than skipping",
           ok, why)

        # W7d -- a System.map name is matched as a whole FIELD, not as a
        # substring, so `my_symbol` does not match `my_symbol_extra`.  Same
        # collision _no_prefix exists for one layer up.
        io.open(mp, "w").write("80000000 T my_symbol_extra\n")
        _m, _r, w = verify_marks(d26, mine, [theirs], mp)
        ck("W7d a longer symbol containing the witness does not match",
           w[0][3] is False, str(w[0][:3]))

        # W9 -- an --absent artefact carrying TWO OR MORE of this declaration's
        # marks is one of mine and is refused as a control.
        # 量 2026-09-04: the first real run of this column was given one of my
        # own builds as the negative control, and thirteen rows went red for a
        # reason that had nothing to do with the image under test.
        #
        # 🔴 W9c is the case the first draft of this guard BROKE.  It refused
        # on one hit, which is exactly what A11 needs to exist -- so the guard
        # and an older control were making incompatible claims about the same
        # file, and only running both found it.
        d29 = os.path.join(tmp, "d29")
        io.open(d29, "w").write(_decl(
            ("B0", "sub/a.c", "after", "one();", 'rlxfw_mark("B0");', "r"),
            ("B1", "sub/b.c", "after", "two();", 'rlxfw_mark("B1");', "r")))
        open(mine, "wb").write(b"..RLXFW-B0\n..RLXFW-B1\n..")
        open(theirs, "wb").write(b"..RLXFW-B0\n..RLXFW-B1\n..")
        ok, why = refuses(verify_marks, d29, mine, [theirs])
        ck("W9  an --absent artefact with TWO of my marks is refused", ok, why)
        open(theirs, "wb").write(b"..RLXFW-B0\n..")
        _m, res9, _w = verify_marks(d29, mine, [theirs])
        ck("W9b ONE mark in a foreign artefact is a FINDING, not a refusal -- "
           "it is reported and A11 is what tests it",
           res9[0][2][0][1] == 1 and res9[1][2][0][1] == 0,
           str([(r.tag, o) for r, _g, o in res9]))
        open(mine, "wb").write(b"..RLXFW-B0\n..mydriver-name..")
        open(theirs, "wb").write(b"..a vendor image..")
        _m, _r, w = verify_marks(d20, mine, [theirs])
        ck("W9c and a clean one is accepted", w[0][3] is True, str(w[0][:3]))

        # W8 -- the column count is fixed at seven.  A six-field row is an
        # error and NOT a row with an empty witness: a dropped tab would
        # otherwise merge `witness` into `reason` silently, which is the shape
        # this file's own header warns about.
        d27 = os.path.join(tmp, "d27")
        io.open(d27, "w").write(
            "# id\tfile\tposition\tanchor\tinsert\twitness\treason\n"
            "B0\tsub/a.c\tafter\tone();\trlxfw_mark(\"B0\");\tr\n")
        ok, why = refuses(parse_decl, d27)
        ck("W8  a six-field row is an error, not an empty witness", ok, why)

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

        # ------------------------------------------------------------------
        # A18-A24 -- the idempotent path (`INC-1`, R5-0, 2026-09-02).
        #
        # It exists because `INC-1` cannot be measured without it: the cost of
        # one real edit on a REUSED tree is unmeasured, every number so far is
        # a no-op or a `touch`, and A4 refuses to run twice on one tree at
        # all.  The whole difficulty is that the fix must not become "already
        # there, call it success" -- that would delete A4, and A4 is guarding
        # a doubled mark, which reads in a capture as a boot loop.
        # ------------------------------------------------------------------
        d18 = os.path.join(tmp, "d18")
        io.open(d18, "w").write(_decl(
            ("X1", "sub/a.c", "after", "one();", 'rlxfw_mark("B01");', "r"),
            ("X2", "sub/a.c", "after", "two();", 'rlxfw_mark("B02");', "r")))

        # A18 -- a clean tree is `clean`, and --if-needed applies to it.
        fresh()
        st, _rw, _d = tree_mark_state(d18, tree)
        ck("A18 a clean tree reads as clean", st == "clean", st)
        apply_marks(d18, tree, src, quiet=True, if_needed=True)
        _r, bad = check_marks(d18, tree)
        ck("A18b --if-needed applies to a clean tree", not bad, str(bad))

        # A19 -- and the SECOND call is a no-op rather than a refusal or a
        # doubled insert.  This is the whole point.
        st, _rw, _d = tree_mark_state(d18, tree)
        ck("A19 a marked tree reads as applied", st == "applied", st)
        apply_marks(d18, tree, src, quiet=True, if_needed=True)
        with io.open(os.path.join(tree, "sub", "a.c"),
                     encoding="utf-8", errors="surrogateescape") as f:
            body = f.read()
        ck("A19b --if-needed does not insert twice",
           body.count('rlxfw_mark("B01");') == 1,
           "%d occurrence(s)" % body.count('rlxfw_mark("B01");'))

        # A20 -- WITHOUT --if-needed the same tree is still refused. A4 is not
        # weakened by the new path; it is bypassed only when asked.
        ok, why = refuses(apply_marks, d18, tree, src, quiet=True)
        ck("A20 plain apply on a marked tree still refuses", ok, why)

        # A21 -- 🔴 the middle state.  One mark present, one not: --if-needed
        # must REFUSE, because neither applying nor skipping is right.
        lines = body.split("\n")
        lines = [ln for ln in lines if 'rlxfw_mark("B02");' not in ln]
        with io.open(os.path.join(tree, "sub", "a.c"), "w",
                     encoding="utf-8", errors="surrogateescape",
                     newline="") as f:
            f.write("\n".join(lines))
        st, _rw, det = tree_mark_state(d18, tree)
        ck("A21 a half-marked tree reads as partial", st == "partial", st)
        ok, why = refuses(apply_marks, d18, tree, src, quiet=True,
                          if_needed=True)
        ck("A21b --if-needed REFUSES a partial tree", ok, why)

        # A22 -- a DOUBLED mark is partial too, not applied. This is the state
        # A4 was written for, reached from the other direction.
        fresh()
        apply_marks(d18, tree, src, quiet=True)
        p22 = os.path.join(tree, "sub", "a.c")
        with io.open(p22, encoding="utf-8", errors="surrogateescape") as f:
            t22 = f.read()
        t22 = t22.replace('rlxfw_mark("B01");',
                          'rlxfw_mark("B01");\n    rlxfw_mark("B01");', 1)
        with io.open(p22, "w", encoding="utf-8", errors="surrogateescape",
                     newline="") as f:
            f.write(t22)
        st, _rw, _d = tree_mark_state(d18, tree)
        ck("A22 a doubled mark reads as partial, never applied",
           st == "partial", st)
        ok, why = refuses(apply_marks, d18, tree, src, quiet=True,
                          if_needed=True)
        ck("A22b --if-needed refuses it", ok, why)

        # A23 -- _copy_if_different does not rewrite an identical file. kbuild
        # triggers on mtime, so a tool that re-copies unconditionally puts a
        # floor under every incremental measurement -- and INC-1 is a
        # measurement of that floor.
        s23 = os.path.join(src, "mine.c")
        d23 = os.path.join(tree, "mine.c")
        shutil.copyfile(s23, d23)
        before = os.stat(d23).st_mtime_ns
        os.utime(d23, ns=(before - 10 ** 9, before - 10 ** 9))
        stamp = os.stat(d23).st_mtime_ns
        wrote = _copy_if_different(s23, d23)
        ck("A23 an identical file is not rewritten",
           wrote is False and os.stat(d23).st_mtime_ns == stamp,
           "wrote=%s mtime moved=%s"
           % (wrote, os.stat(d23).st_mtime_ns != stamp))

        # A24 -- the positive control on A23: a CHANGED file is written. A
        # copier that never writes would pass A23.
        with io.open(s23, "w") as f:
            f.write("void rlxfw_mark(const char *s){(void)s;/*v2*/}\n")
        wrote = _copy_if_different(s23, d23)
        with io.open(d23) as f:
            got = f.read()
        ck("A24 a changed file IS written",
           wrote is True and "v2" in got, "wrote=%s content=%r" % (wrote, got))

        # A25 -- the RESULT line says which of the two things happened, and
        # BOTH forms are readable by the one pattern in rlxfw-kbuild.sh. The
        # driver parses this line and exits 3 on an empty count, so a message
        # that got more honest must not break its reader.
        import io as _io25
        import contextlib
        kb_rx = re.compile(
            r"^RESULT: (\d+) mark\(s\) (.*) and read back", re.M)
        fresh()
        got = []
        for _ in range(2):
            buf = _io25.StringIO()
            with contextlib.redirect_stdout(buf):
                rc25 = main(["apply", "--decl", d18, "--tree", tree,
                             "--src", src, "--if-needed"])
            plain = re.sub(r"\x1b\[[0-9;]*m", "", buf.getvalue())
            m25 = kb_rx.search(plain)
            got.append((rc25, m25.group(1) if m25 else None,
                        m25.group(2) if m25 else None))
        ck("A25 first --if-needed run reports `applied`",
           got[0] == (0, "2", "applied"), str(got[0]))
        ck("A25b second reports `already present`, same count",
           got[1] == (0, "2", "already present"), str(got[1]))
        ck("A25c the driver's pattern reads a count from BOTH",
           got[0][1] == got[1][1] == "2",
           "an empty count makes rlxfw-kbuild.sh exit 3")
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
    a = {"decl": None, "tree": None, "src": None, "image": None,
         "map": None, "absent": []}
    if_needed = False
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == "--absent":
            a["absent"].append(argv[i + 1]); i += 2
        elif x == "--if-needed":
            if_needed = True; i += 1
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
        # The state is read BEFORE the call, so the RESULT line can say what
        # actually happened. A line reading `applied` after a run that
        # inserted nothing is the kind of second-hand number this repository
        # keeps finding in its own prose.
        pre = None
        if if_needed:
            pre, _rw, _d = tree_mark_state(a["decl"], a["tree"])
        apply_marks(a["decl"], a["tree"], a["src"], if_needed=if_needed)
        rows, bad = check_marks(a["decl"], a["tree"])
        if bad:
            for r, why in bad:
                print("  %-4s %s: %s" % (r.id, r.file, why))
            print("REFUSED: apply ran and check does not agree with it")
            return 2
        print("")
        verb = "already present" if pre == "applied" else "applied"
        print("RESULT: \033[32m%d mark(s) %s and read back\033[0m"
              % (len(rows), verb))
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
        rows, res, wres = verify_marks(a["decl"], a["image"], a["absent"],
                                       a["map"])
        print("rlxfw-marks %s" % VERSION)
        print("image       %s" % a["image"])
        if a["map"]:
            print("map         %s" % a["map"])
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
        # MARK-1's rows, printed apart: a witness is a different claim from a
        # mark (a whole file reached the image, not a line printed on the
        # wire) and merging the two counts would hide which kind failed.
        wbad = 0
        if wres:
            print("")
            print("witnesses   (MARK-1: what a build row leaves in the "
                  "artefact)")
            for r, got, outs, ok in wres:
                o = " ".join("%s:%d" % (os.path.basename(f), n)
                             for f, n in outs)
                if not ok:
                    wbad += 1
                print("  %-4s %-4s %-22s mine:%d %s%s"
                      % (r.id, r.wkind + ":", r.wval, got, o,
                         "" if ok else "  <- must be >=1 here and 0 there"))
        print("")
        if bad or wbad or not a["absent"]:
            print("RESULT: \033[31m%d mark(s) and %d witness(es) not a "
                  "discriminator\033[0m" % (bad, wbad))
            return 1
        print("RESULT: \033[32mall %d mark(s) present once in the image, %d "
              "witness(es) present, and absent from %d vendor artefact(s)"
              "\033[0m" % (len(rows), len(wres), len(a["absent"])))
        return 0

    die("unknown command %r" % cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
