#!/usr/bin/env python3
r"""docmove -- prove that moving text out of a document lost none of it.

A state document is restructured by MOVING its history, verbatim, into archive
files and rewriting it short, under the rule that nothing may be lost.  This
checks the rule: every block of the BEFORE text must appear intact in ONE of
the AFTER files.  Text that exists only in the after files is not checked.

    docmove.py check --before REV:PATH [...] --after PATH [...] [--root DIR]
                     [--min-chars N] [--allow-drop FILE] [--show-missing K]
    docmove.py [--self-test]

INPUTS.  `REV:PATH` is read with `git cat-file blob` in --root (default: this
repository); `:PATH` is the index.  NOT `git show`: 量 2026-09-23, `git show
HEAD:tools` exits 0 and prints the tree's listing, which would be read as a
document (D15).  An argument with no colon, or starting with a drive letter,
`/`, `.` or `\`, is a file relative to --root.  --after and --allow-drop take
both forms.  Everything is read as BYTES, decoded as UTF-8 (a leading BOM
dropped) and split on `\n` ONLY -- a bare `\r` is not a line break (D13);
universal newlines once made a sibling tool invent 19 false findings here.

BLOCKS, after a leading blockquote marker (`>`, optional indentation and one
optional space, repeated for `> >`) is stripped from every line: (1) a ```
fence, fence lines included, is ONE block, closed by a line of backticks only
at least as long as the opener; (2) every line whose stripped form starts with
`|` is its own block; (3) otherwise a maximal run of non-blank lines.
NORMALISATION: every run of ASCII whitespace becomes one space, then strip;
nothing else (U+00A0 is text: D5).  Each after-file is normalised the same
way, as ONE string.  A
block is CONSERVED if its normalised text is a substring of one after-file's;
it may not be split across two (D4).  Blocks under --min-chars (default 40
code points) are counted `short`, not checked, and their share is printed.

--allow-drop is a TSV of `<sha256-16><TAB><reason>`: the first 16 hex of
sha256 over the block's normalised UTF-8, printed beside every missing block.
It is checked in BOTH directions, like citecheck's C4: an entry naming no
block, a conserved block, or a block too short to be checked is itself stale.

EXIT: 0 every checked block conserved; 1 findings (missing blocks, stale
allow entries); 2 refusal -- an unreadable input, a before-document with no
checkable block, an after-file that does not exist, no git.  An empty
population is a refusal, never a clean pass (D11).  The last line is the
verdict and is derived from the same value as the exit code.

WHAT IT CANNOT SEE
  * A block rewritten on purpose is reported missing.  That is the point; the
    allow-list is how a deliberate drop is declared, with its reason.
  * Added text, and what a moved block MEANS in its new context.
  * Whitespace-only edits, and a leading `>` added or removed on any line.
  * Structure inside one after-file: a paragraph split in two by a blank line
    there still counts as conserved, because the after-file is one string.
  * Anything under --min-chars: most headings and table separator rows.
  * Granularity cuts the other way: a list with no blank line between items,
    or a blockquote with no `>`-only line, is ONE block, so moving part of it
    reports all of it missing.  Archive the old block whole, then rewrite.

REFUTATION.  The tool is wrong if a block it calls conserved is not intact in
a single after-file (D2, D4, D5 -- and D14 runs them against broken matchers
and requires them to go red), if a block present verbatim is called missing
(D1, D3, D6, D7, D8), or if a line number disagrees with `sed -n` (D13).
"""

import argparse
import hashlib
import importlib.util
import io
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # a replaced or detached stdout
    pass

VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GIT = "git"
MIN_CHARS = 40
SHOW_MISSING = 20
PREVIEW = 100

WS = " \t\n\r\f\v"
WS_RUN = re.compile(r"[ \t\n\r\f\v]+")
QUOTE = re.compile(r"^(?:[ \t]*>[ ]?)+")
FENCE_OPEN = re.compile(r"^(`{3,})[^`]*$")  # CommonMark: no backtick in info
ALLOW_ROW = re.compile(r"^([0-9a-f]{16})\t(.*)$")
DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
#: `git -C ROOT` must mean ROOT: an inherited GIT_DIR -- a hook sets one --
#: would silently read another repository (D12).  `_repo` strips EVERY GIT_*
#: for the same reason, where the cost would be a commit in the wrong place.
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE")

USAGE = ("usage: docmove.py check --before REV:PATH [...] --after PATH [...]\n"
         "                        [--root DIR] [--min-chars N] "
         "[--allow-drop FILE] [--show-missing K]\n"
         "       docmove.py [--self-test]")


class Refusal(Exception):
    """An input this tool cannot honestly report on.  Exit 2."""


def normalise(text):
    return WS_RUN.sub(" ", text).strip(" ")


def unquote(line):
    return QUOTE.sub("", line, count=1)


def digest16(norm):
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


class Block(object):
    __slots__ = ("src", "start", "end", "kind", "norm", "digest")

    def __init__(self, src, start, end, kind, lines):
        self.src, self.start, self.end, self.kind = src, start, end, kind
        self.norm = normalise("\n".join(lines))
        self.digest = digest16(self.norm)

    def where(self):
        return "%s:%d-%d" % (self.src, self.start, self.end)


def lines_of(text):
    """`\n` ONLY.  A final newline ends the last line rather than starting an
    empty one, so the numbering is `sed -n`'s and `grep -n`'s."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def split_blocks(src, text):
    """-> (blocks, warnings) for one before-document."""
    lines = [unquote(ln) for ln in lines_of(text)]
    blocks, warnings, run = [], [], []

    def flush():
        if run:
            blocks.append(Block(src, run[0][0], run[-1][0], "para",
                                [ln for _no, ln in run]))
            del run[:]

    i = 0
    while i < len(lines):
        st = lines[i].strip(WS)
        m = FENCE_OPEN.match(st)
        if m:
            flush()
            width, j = len(m.group(1)), i + 1
            while j < len(lines):
                close = lines[j].strip(WS)
                if close and close.strip("`") == "" and len(close) >= width:
                    break
                j += 1
            if j == len(lines):
                warnings.append("%s:%d: this fence never closes, so the %d "
                                "line(s) to the end are ONE block"
                                % (src, i + 1, len(lines) - i))
                j -= 1
            blocks.append(Block(src, i + 1, j + 1, "fence", lines[i:j + 1]))
            i = j + 1
            continue
        if not st:
            flush()
        elif st.startswith("|"):
            flush()
            blocks.append(Block(src, i + 1, i + 1, "row", [lines[i]]))
        else:
            run.append((i + 1, lines[i]))
        i += 1
    flush()
    return blocks, warnings


def after_text(text):
    return normalise("\n".join(unquote(ln) for ln in lines_of(text)))


def parse_spec(spec):
    """-> (rev, path); rev is None for a file in the working tree."""
    if ":" not in spec or DRIVE.match(spec) or spec[:1] in ("/", ".", "\\"):
        return None, spec
    rev, path = spec.split(":", 1)
    return rev, path


def read_input(spec, root, git):
    """-> the decoded text.  Bytes in, never universal newlines."""
    rev, path = parse_spec(spec)
    if rev is None:
        full = path if os.path.isabs(path) else os.path.join(root, path)
        try:
            with open(full, "rb") as fh:
                blob = fh.read()
        except OSError as e:
            raise Refusal("%s: cannot read %s (%s)"
                          % (spec, full, e.strerror or e))
    else:
        env = {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}
        try:
            r = subprocess.run([git, "-C", root, "cat-file", "blob",
                                "%s:%s" % (rev, path)],
                               capture_output=True, env=env)
        except OSError as e:
            raise Refusal("%s: git is not available (%s: %s)" % (spec, git, e))
        if r.returncode != 0:
            err = r.stderr.decode("utf-8", "replace").strip()
            raise Refusal("%s: git cannot read it as a file in %s (%s)"
                          % (spec, root, err or "rc %d" % r.returncode))
        blob = r.stdout
    try:
        return blob.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise Refusal("%s: not UTF-8 at byte %d" % (spec, e.start))


def load_allow(spec, root, git):
    """-> {digest: (line, reason)}.  A malformed row is a refusal: there is no
    way to know which block it meant."""
    out = {}
    for no, raw in enumerate(lines_of(read_input(spec, root, git)), 1):
        line = raw.rstrip(WS)
        if not line.strip(WS) or line.lstrip(WS).startswith("#"):
            continue
        m = ALLOW_ROW.match(line)
        if not m or not m.group(2).strip(WS):
            raise Refusal("--allow-drop %s:%d: want <16 lowercase hex><TAB>"
                          "<reason>, got %r" % (spec, no, line[:60]))
        if m.group(1) in out:
            raise Refusal("--allow-drop %s:%d: %s is listed twice (first at "
                          "line %d)" % (spec, no, m.group(1),
                                        out[m.group(1)][0]))
        out[m.group(1)] = (no, m.group(2).strip(WS))
    return out


def find_home(needle, hays):
    """THE MATCHER: the index of the first after-file whose normalised text
    contains `needle` whole, else None.  D14 swaps in broken ones."""
    for i, hay in enumerate(hays):
        if needle in hay:
            return i
    return None


def shown(text, n=PREVIEW):
    """`text[:n]` made safe to print on ONE line.  ci-census splits a capture
    with str.splitlines(), which also breaks at U+2028, U+0085 and \x1c-\x1e,
    so printing one raw could forge a case line (D16)."""
    out = []
    for c in text[:n]:
        if unicodedata.category(c) in ("Cc", "Zl", "Zp"):
            o = ord(c)
            out.append("\\x%02x" % o if o <= 0xff else "\\u%04x" % o)
        else:
            out.append(c)
    return "".join(out)


def check(a, matcher, git):
    """Read everything, then decide.  Raises Refusal before deciding anything."""
    root = os.path.abspath(a.root)
    if a.min_chars < 1:
        raise Refusal("--min-chars must be at least 1, got %d" % a.min_chars)
    if a.show_missing < 0:
        raise Refusal("--show-missing must be 0 or more, got %d"
                      % a.show_missing)
    docs = []
    for spec in a.before:
        text = read_input(spec, root, git)
        blocks, warns = split_blocks(spec, text)
        if not any(len(b.norm) >= a.min_chars for b in blocks):
            raise Refusal("%s: %d block(s) and none reaches --min-chars %d -- "
                          "a before-document with nothing to check is a "
                          "refusal, not a clean pass"
                          % (spec, len(blocks), a.min_chars))
        docs.append({"spec": spec, "lines": len(lines_of(text)),
                     "blocks": blocks, "warnings": warns})
    afters = [{"spec": s, "text": after_text(read_input(s, root, git))}
              for s in a.after]
    allow = load_allow(a.allow_drop, root, git) if a.allow_drop else {}

    hays = [x["text"] for x in afters]
    blocks = [b for d in docs for b in d["blocks"]]
    short = [b for b in blocks if len(b.norm) < a.min_chars]
    checked = [b for b in blocks if len(b.norm) >= a.min_chars]
    home = {}
    for b in checked:
        if b.norm not in home:
            home[b.norm] = matcher(b.norm, hays)
    conserved = [(b, home[b.norm]) for b in checked
                 if home[b.norm] is not None]
    lost = [b for b in checked if home[b.norm] is None]
    allowed = [b for b in lost if b.digest in allow]
    missing = [b for b in lost if b.digest not in allow]

    # The allow-list in the OTHER direction: an entry is load-bearing only if
    # it names a block that is checked and missing.  Same text, same digest,
    # same fate, so the first block carrying a digest speaks for all of them.
    first = {}
    for b in blocks:
        first.setdefault(b.digest, b)
    lost_digests = set(b.digest for b in lost)
    stale = []
    for dg, (no, reason) in sorted(allow.items(), key=lambda kv: kv[1][0]):
        if dg in lost_digests:
            continue
        b = first.get(dg)
        if b is None:
            kind, why = "none", "names no block of the before-set"
        elif len(b.norm) < a.min_chars:
            kind, why = "short", ("names %s, which is under --min-chars and "
                                  "never checked" % b.where())
        else:
            kind, why = "conserved", ("names %s, which IS conserved, in %s"
                                      % (b.where(),
                                         afters[home[b.norm]]["spec"]))
        stale.append({"digest": dg, "line": no, "reason": reason,
                      "kind": kind, "why": why})

    if len(checked) != len(conserved) + len(allowed) + len(missing):
        raise AssertionError("the counts do not partition the checked set")
    return {"rc": 1 if (missing or stale) else 0, "docs": docs,
            "afters": afters, "allow": allow, "blocks": blocks,
            "short": short, "checked": checked, "conserved": conserved,
            "allowed": allowed, "missing": missing, "stale": stale}


def case_line(out, good, name, text):
    print("  %s  %-4s %s" % ("ok  " if good else "FAIL", name, text), file=out)


def report(res, a, out):
    for d in res["docs"]:
        print("    before  %s  %d line(s), %d block(s)"
              % (d["spec"], d["lines"], len(d["blocks"])), file=out)
    for x in res["afters"]:
        print("    after   %s  %d normalised char(s)"
              % (x["spec"], len(x["text"])), file=out)
    for d in res["docs"]:
        for w in d["warnings"]:
            print("    warning %s" % w, file=out)

    n, missing = len(res["checked"]), res["missing"]
    case_line(out, not missing, "M1",
              "every checked block is intact in one after-file: %d conserved"
              " and %d allowed, of %d" % (len(res["conserved"]),
                                          len(res["allowed"]), n)
              if not missing else
              "%d of %d checked block(s) are intact in NO after-file"
              % (len(missing), n))
    k = a.show_missing
    for b in missing[:k]:
        print("    %s  %s  %s" % (b.where(), b.digest, shown(b.norm)),
              file=out)
    if len(missing) > k:
        print("    ... and %d more not shown (--show-missing %d)"
              % (len(missing) - k, k), file=out)

    stale, n_allow = res["stale"], len(res["allow"])
    case_line(out, not stale, "M2",
              "every --allow-drop entry names a checked, missing block: "
              "%d of %d" % (n_allow, n_allow)
              if not stale else
              "%d of %d --allow-drop entr(ies) are stale" % (len(stale),
                                                              n_allow))
    for s in stale:
        print("    line %d  %s  %s -- %s" % (s["line"], s["digest"],
                                            shown(s["reason"], 60), s["why"]),
              file=out)

    all_chars = sum(len(b.norm) for b in res["blocks"])
    short_chars = sum(len(b.norm) for b in res["short"])
    print("    short blocks hold %d of %d normalised char(s), %.2f %%, and "
          "are NOT checked" % (short_chars, all_chars,
                               100.0 * short_chars / all_chars), file=out)
    print("verdict %s  before-blocks %d  checked %d  conserved %d  missing %d"
          "  short %d  allowed %d  stale-allow %d"
          % ("CONSERVED" if res["rc"] == 0 else "FINDINGS", len(res["blocks"]),
             n, len(res["conserved"]), len(missing), len(res["short"]),
             len(res["allowed"]), len(stale)), file=out)


def run(argv, out, matcher=None, git=None):
    """The whole `check` path, argument parsing included.  -> (rc, result).
    The self-test drives THIS rather than an inner helper, so each control
    exercises what the command line exercises."""
    matcher = find_home if matcher is None else matcher
    git = GIT if git is None else git
    if not argv or argv[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2, None
    ap = argparse.ArgumentParser(prog="docmove.py check")
    ap.add_argument("--before", nargs="+", required=True, metavar="REV:PATH")
    ap.add_argument("--after", nargs="+", required=True, metavar="PATH")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--min-chars", type=int, default=MIN_CHARS)
    ap.add_argument("--allow-drop", metavar="FILE")
    ap.add_argument("--show-missing", type=int, default=SHOW_MISSING)
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return (2 if e.code else 0), None
    print("docmove %s  --  every block of the before-set, intact in ONE "
          "after-file" % VERSION, file=out)
    try:
        res = check(a, matcher, git)
    except Refusal as e:
        print("verdict REFUSED  %s" % shown(str(e), 2000), file=out)
        return 2, None
    report(res, a, out)
    return res["rc"], res


# --------------------------------------------------------------- self-test
ALPHA = ("Alpha: the loader region is intact over all of it, and the\n"
         "bracket stands at 1,024 bytes of 4,194,304.")
BRAVO = ("Bravo: a tool reporting zero is making a claim, so every sweep\n"
         "needs a positive control that can fail.")
# Written out BY HAND, so D10's digests do not come from normalise().
ALPHA_NORM = ("Alpha: the loader region is intact over all of it, and the "
              "bracket stands at 1,024 bytes of 4,194,304.")
BRAVO_NORM = ("Bravo: a tool reporting zero is making a claim, so every sweep "
              "needs a positive control that can fail.")
CHARLIE = ("Charlie: nothing counts as a result until its refutation\n"
           "condition is written first, and a negative result\n"
           "stays in place.")
CHARLIE_REWRAPPED = ("  Charlie: nothing counts as a result\n"
                     "\tuntil its refutation condition is written first,   "
                     "and a\nnegative result stays in place.")
HALF1 = "Delta, first half: the tick is mine from boot on eleven boots,"
HALF2 = "Delta, second half: and the clocksource half is still jiffies."
ECHO = ("Echo: the bracket ran twice on one seating, 1,024 bytes of\n"
        "4,194,304, all byte-identical, and for the first time with an "
        "observed vendor-firmware boot bracketed between the two rounds; "
        "but no full re-dump ran.")
ECHO_EDIT = ECHO[:-4] + "run."
# chr(), never a literal: an invisible character in a fixture is one an editor
# can normalise away without a diff anyone would read.
ECHO_NBSP = ECHO.replace("no full", "no" + chr(0xA0) + "full")
QUOTED = ("> Foxtrot: the first quoted paragraph, long enough to be\n"
          "> checked by the tool.\n"
          ">\n"
          "> > Golf: a nested quote and a second paragraph, also long\n"
          "> > enough to be checked on its own.\n")
PLAIN_F = ("Foxtrot: the first quoted paragraph, long enough to be\n"
           "checked by the tool.\n")
PLAIN_G = ("Golf: a nested quote and a second paragraph, also long\n"
           "enough to be checked on its own.\n")
TABLE_BEFORE = ("| id | text |\n"
                "|----|------|\n"
                "| R1 | the first row is long enough to be checked by the tool |\n"
                "| R2 | the second row is also long enough to be checked by it |\n")
TABLE_AFTER = ("| key | rows moved here from another table |\n"
               "|-----|-----------------------------------|\n"
               "| R2 | the second row is ALSO long enough to be checked by it |\n"
               "| R1 | the first row is long enough to be checked by the tool |\n")
FENCED = ("Hotel: an intro paragraph long enough to be checked by the tool.\n"
          "\n"
          "```sh\n"
          "first command --with a long enough argument list here\n"
          "| a line inside the fence that only looks like a row |\n"
          "\n"
          "second half of the fence, after a blank line inside it\n"
          "```\n"
          "\n"
          "India: an outro paragraph long enough to be checked as well.\n")
SHORT39 = "Juliet: this block is 39 characters ok."
EXACT40 = "Kilo: and this block holds 40 characters"
CR_DOC = (b"Lima: one paragraph line that is long enough to be checked\r\r"
          b"and it is STILL line one, because a bare CR is not a break\n"
          b"| Mike: a table row long enough to check |\r| still that row |\n"
          b"\n"
          b"November: the last block, long enough to be checked by the tool\n")
LONG_NAME = "a-file-whose-name-is-long-enough-to-be-a-checkable-block.md"


class _Tmp(object):
    """A temp directory that survives Windows' read-only git objects."""

    def __enter__(self):
        self.t = tempfile.TemporaryDirectory(prefix="docmove-",
                                             ignore_cleanup_errors=True)
        return self.t.name

    def __exit__(self, *exc):
        self.t.cleanup()
        return False


def _w(d, name, data):
    p = os.path.join(d, name)
    if not os.path.isdir(os.path.dirname(p)):
        os.makedirs(os.path.dirname(p))
    with open(p, "wb") as fh:
        fh.write(data.encode("utf-8") if isinstance(data, str) else data)
    return p


def _check(root, before, after, matcher, extra=(), git=None):
    buf = io.StringIO()
    argv = (["check", "--root", root, "--before"] + list(before)
            + ["--after"] + list(after) + list(extra))
    rc, res = run(argv, buf, matcher=matcher, git=git)
    return rc, res, buf.getvalue()


def _verdict(out):
    last = out.rstrip("\n").split("\n")[-1].split()
    return last[1] if len(last) > 1 and last[0] == "verdict" else None


def _where(blocks):
    return [b.where() for b in blocks]


def _repo(tmp, files, staged=None, then=None, name="repo"):
    """A throwaway repository: commit `files`, stage `staged`, then leave
    `then` in the working tree.  Its git runs HERMETIC -- no inherited GIT_*
    variable, an empty global config, no system config -- so no hook, signing
    or autocrlf setting of this host, and no missing identity on a CI runner,
    changes what is committed.  Nothing here touches docmove's own repo."""
    repo = os.path.join(tmp, name)
    os.makedirs(repo)
    cfg = _w(tmp, "empty.gitconfig", b"")
    env = dict((k, v) for k, v in os.environ.items()
               if not k.startswith("GIT_"))
    env.update(GIT_CONFIG_GLOBAL=cfg, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="docmove", GIT_AUTHOR_EMAIL="docmove@invalid",
               GIT_COMMITTER_NAME="docmove",
               GIT_COMMITTER_EMAIL="docmove@invalid")

    def git(*args):
        r = subprocess.run([GIT, "-C", repo] + list(args),
                           capture_output=True, env=env)
        if r.returncode:
            raise RuntimeError("fixture `git %s` rc %d: %s" % (
                args[0], r.returncode,
                r.stderr.decode("utf-8", "replace").strip()))

    for n, data in files.items():
        _w(repo, n, data)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "docmove fixture")
    if staged:
        for n, data in staged.items():
            _w(repo, n, data)
        git("add", "-A")
    for n, data in (then or {}).items():
        _w(repo, n, data)
    return repo


def d1(m):
    with _Tmp() as t:
        _w(t, "before.md", "# Title\n\n" + ALPHA + "\n\n" + BRAVO + "\n")
        _w(t, "a1.md", "# Archive one\n\nNew words.\n\n" + ALPHA + "\n")
        _w(t, "a2.md", "Other new words.\n\n" + BRAVO + "\n\nNew tail.\n")
        rc, res, out = _check(t, ["before.md"], ["a1.md", "a2.md"], m)
        if res is None:
            return False, "rc %d, no result" % rc
        homes = sorted((b.where(), res["afters"][i]["spec"])
                       for b, i in res["conserved"])
        want = [("before.md:3-4", "a1.md"), ("before.md:6-7", "a2.md")]
        return (rc == 0 and homes == want and _verdict(out) == "CONSERVED",
                "rc %d, found %s" % (rc, homes))


def d2(m):
    with _Tmp() as t:
        _w(t, "before.md", ALPHA + "\n\n" + BRAVO + "\n")
        _w(t, "after.md", ALPHA + "\n")
        rc, res, out = _check(t, ["before.md"], ["after.md"], m)
        got = _where(res["missing"]) if res else None
        return (rc == 1 and got == ["before.md:4-5"]
                and "    before.md:4-5  " in out
                and _verdict(out) == "FINDINGS",
                "rc %d, missing %s" % (rc, got))


def d3(m):
    if CHARLIE in CHARLIE_REWRAPPED or CHARLIE.split() != \
            CHARLIE_REWRAPPED.split():
        return False, "the fixture is not a re-wrap of the same words"
    with _Tmp() as t:
        _w(t, "before.md", CHARLIE + "\n")
        _w(t, "after.md", "New intro.\n\n" + CHARLIE_REWRAPPED + "\n")
        rc, res, _out = _check(t, ["before.md"], ["after.md"], m)
        n = len(res["conserved"]) if res else None
        return rc == 0 and n == 1, "rc %d, conserved %s" % (rc, n)


def d4(m):
    with _Tmp() as t:
        _w(t, "before.md", HALF1 + "\n" + HALF2 + "\n")
        _w(t, "h1.md", HALF1 + "\n")
        _w(t, "h2.md", HALF2 + "\n")
        _w(t, "halves.md", HALF1 + "\n\n" + HALF2 + "\n")
        # The control on the fixture: each half, on its own, IS found, so the
        # only thing that can make the whole block missing is the split.
        rc0, _r0, _o0 = _check(t, ["halves.md"], ["h1.md", "h2.md"], m)
        rc, res, _out = _check(t, ["before.md"], ["h1.md", "h2.md"], m)
        got = _where(res["missing"]) if res else None
        return (rc0 == 0 and rc == 1 and got == ["before.md:1-2"],
                "halves alone rc %d, whole block rc %d, missing %s"
                % (rc0, rc, got))


def d5(m):
    got = []
    for label, edited in (("a letter", ECHO_EDIT),
                          ("a space made U+00A0", ECHO_NBSP)):
        diff = [i for i, (x, y) in enumerate(zip(ECHO, edited)) if x != y]
        if len(ECHO) != len(edited) or len(diff) != 1 or diff[0] < PREVIEW:
            return False, "%s: not ONE late character: %s" % (label, diff)
        with _Tmp() as t:
            _w(t, "before.md", ECHO + "\n")
            _w(t, "after.md", edited + "\n")
            rc, res, _out = _check(t, ["before.md"], ["after.md"], m)
            lost = _where(res["missing"]) if res else None
            got.append((label, diff[0], rc,
                        rc == 1 and lost == ["before.md:1-2"]))
    return all(g[3] for g in got), "; ".join(
        "%s at offset %d: rc %d" % g[:3] for g in got)


def d6(m):
    if PLAIN_F in QUOTED or "> Foxtrot" in PLAIN_F + PLAIN_G:
        return False, "the fixture does not need the marker stripped"
    with _Tmp() as t:
        _w(t, "quoted.md", QUOTED)
        _w(t, "plain.md", PLAIN_F + "\n" + PLAIN_G)
        _w(t, "f.md", PLAIN_F)
        _w(t, "g.md", PLAIN_G)
        # Out of the quote, into TWO files: this also requires a lone `>` to
        # be a blank line, or the two quoted paragraphs are one block.
        rc1, r1, _o1 = _check(t, ["quoted.md"], ["f.md", "g.md"], m)
        # ...and back in.
        rc2, r2, _o2 = _check(t, ["plain.md"], ["quoted.md"], m)
        n1 = len(r1["conserved"]) if r1 else None
        n2 = len(r2["conserved"]) if r2 else None
        return (rc1 == 0 and n1 == 2 and rc2 == 0 and n2 == 2,
                "out of the quote rc %d (%s conserved), into it rc %d (%s)"
                % (rc1, n1, rc2, n2))


def d7(m):
    with _Tmp() as t:
        _w(t, "before.md", TABLE_BEFORE)
        _w(t, "after.md", "New intro.\n\n" + TABLE_AFTER)
        rc, res, _out = _check(t, ["before.md"], ["after.md"], m)
        if res is None:
            return False, "rc %d, no result" % rc
        kinds = [(b.where(), b.kind) for b in res["blocks"]]
        kept = [b.where() for b, _i in res["conserved"]]
        lost = _where(res["missing"])
        good = (rc == 1 and len(kinds) == 4
                and all(k == "row" for _w2, k in kinds)
                and kept == ["before.md:3-3"] and lost == ["before.md:4-4"])
        return good, "rc %d, rows %d, moved %s, edited %s" % (
            rc, len(kinds), kept, lost)


def d8(m):
    lines = FENCED.split("\n")
    with _Tmp() as t:
        _w(t, "before.md", FENCED)
        _w(t, "moved.md", "Archive.\n\n" + FENCED + "\nNew tail.\n")
        _w(t, "top.md", "\n".join(lines[:5]) + "\n")
        _w(t, "bottom.md", "\n".join(lines[5:]))
        rc1, r1, _o1 = _check(t, ["before.md"], ["moved.md"], m)
        # The negative half: the fence cut in two at its inner blank line,
        # one half per file.  Were it several blocks, each would be found.
        rc2, r2, _o2 = _check(t, ["before.md"], ["top.md", "bottom.md"], m)
        shape = [(b.where(), b.kind) for b in r1["blocks"]] if r1 else None
        want = [("before.md:1-1", "para"), ("before.md:3-8", "fence"),
                ("before.md:10-10", "para")]
        lost = _where(r2["missing"]) if r2 else None
        return (rc1 == 0 and shape == want and rc2 == 1
                and lost == ["before.md:3-8"],
                "blocks %s; verbatim rc %d; cut in two rc %d, missing %s"
                % ([w for w, _k in shape or []], rc1, rc2, lost))


def d9(m):
    # The CJK pair pins CODE POINTS: 39 of them are 117 bytes, and SPEC.md
    # is mostly CJK, so a byte count would check what should be short.
    cjk39, cjk40 = chr(0x91CF) * 39, chr(0x8B80) * 40
    if (len(SHORT39), len(EXACT40)) != (39, 40):
        return False, "fixture lengths %d/%d" % (len(SHORT39), len(EXACT40))
    with _Tmp() as t:
        _w(t, "before.md", "\n\n".join(
            (SHORT39, EXACT40, cjk39, cjk40, ALPHA)) + "\n")
        _w(t, "after.md", ALPHA + "\n")
        rc1, r1, _o1 = _check(t, ["before.md"], ["after.md"], m,
                              ["--min-chars", "40"])
        rc2, r2, _o2 = _check(t, ["before.md"], ["after.md"], m,
                              ["--min-chars", "41"])
        if r1 is None or r2 is None:
            return False, "rc %d / %d, no result" % (rc1, rc2)
        g1 = (rc1 == 1
              and _where(r1["short"]) == ["before.md:1-1", "before.md:5-5"]
              and len(r1["checked"]) == 3
              and _where(r1["missing"]) == ["before.md:3-3",
                                            "before.md:7-7"])
        g2 = rc2 == 0 and len(r2["short"]) == 4 and not r2["missing"]
        return g1 and g2, ("at 40: short %s, missing %s, rc %d; at 41: "
                           "short %d, rc %d" % (_where(r1["short"]),
                                                _where(r1["missing"]), rc1,
                                                len(r2["short"]), rc2))


def d10(m):
    def h(s):
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
    dig_b, dig_a, dig_s = h(BRAVO_NORM), h(ALPHA_NORM), h(SHORT39)
    dig_none = h("a block that exists nowhere in the before-set at all")
    base = "# a comment, then a blank line\n\n%s\tBravo retired on purpose\n" \
        % dig_b
    with _Tmp() as t:
        _w(t, "before.md", ALPHA + "\n\n" + BRAVO + "\n\n" + SHORT39 + "\n")
        _w(t, "after.md", ALPHA + "\n")
        _w(t, "ok.tsv", base)
        _w(t, "none.tsv", base + "%s\tnames nothing\n" % dig_none)
        _w(t, "kept.tsv", base + "%s\tAlpha was kept\n" % dig_a)
        _w(t, "short.tsv", base + "%s\ttoo short to matter\n" % dig_s)
        rc0, _r0, o0 = _check(t, ["before.md"], ["after.md"], m)
        got = {}
        for f in ("ok", "none", "kept", "short"):
            rc, res, _out = _check(t, ["before.md"], ["after.md"], m,
                                   ["--allow-drop", f + ".tsv"])
            got[f] = (rc, [s["kind"] for s in (res or {}).get("stale", [])],
                      len((res or {}).get("allowed", [])))
        want = {"ok": (0, [], 1), "none": (1, ["none"], 1),
                "kept": (1, ["conserved"], 1), "short": (1, ["short"], 1)}
        # rc0: with no allow-list, Bravo is missing and its digest -- derived
        # here by hand, not by digest16() -- is the one printed beside it.
        good = (rc0 == 1 and ("    before.md:4-5  %s  " % dig_b) in o0
                and got == want)
        return good, "no list rc %d; %s" % (rc0, got)


def d11(m):
    with _Tmp() as t:
        _w(t, "empty.md", b"")
        _w(t, "short.md", "# Title\n\nshort para\n\n| a | b |\n")
        _w(t, "good.md", ALPHA + "\n")
        runs = [_check(t, ["empty.md"], ["good.md"], m),
                _check(t, ["short.md"], ["good.md"], m),
                _check(t, ["good.md", "empty.md"], ["good.md"], m)]
        got = [(rc, _verdict(out)) for rc, _res, out in runs]
        return (got == [(2, "REFUSED")] * 3,
                "empty, all-short, and one empty among good: %s" % got)


def d12(m):
    with _Tmp() as t:
        repo = _repo(t, {"doc.md": ALPHA + "\n\n" + BRAVO + "\n"},
                     then={"doc.md": ALPHA + "\n\n" + CHARLIE + "\n"})
        decoy = _repo(t, {"doc.md": CHARLIE + "\n"}, name="decoy")
        rc1, r1, _o1 = _check(repo, ["HEAD:doc.md"], ["doc.md"], m)
        rc2, r2, _o2 = _check(repo, ["doc.md"], ["doc.md"], m)
        # An inherited GIT_DIR -- a hook sets one -- must not redirect the
        # read: --root names the repository, and here GIT_DIR names a decoy.
        saved = os.environ.get("GIT_DIR")
        os.environ["GIT_DIR"] = os.path.join(decoy, ".git")
        try:
            rc3, r3, _o3 = _check(repo, ["HEAD:doc.md"], ["doc.md"], m)
        finally:
            if saved is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = saved
        if r1 is None or r2 is None or r3 is None:
            return False, "rc %d / %d / %d, no result" % (rc1, rc2, rc3)
        s1 = set(b.norm for b in r1["blocks"])
        s2 = set(b.norm for b in r2["blocks"])
        s3 = set(b.norm for b in r3["blocks"])
        good = (rc1 == 1 and _where(r1["missing"]) == ["HEAD:doc.md:4-5"]
                and BRAVO_NORM in s1 and BRAVO_NORM not in s2
                and s1 != s2 and rc2 == 0 and s3 == s1)
        return good, ("HEAD:doc.md rc %d missing %s; working doc.md rc %d; "
                      "block sets differ: %s; with GIT_DIR set to a decoy, "
                      "HEAD:doc.md still read from --root: %s"
                      % (rc1, _where(r1["missing"]), rc2, s1 != s2,
                         s3 == s1))


def d13(m):
    want = [("cr.md:1-1", "para"), ("cr.md:2-2", "row"), ("cr.md:4-4", "para")]
    # The control on the fixture: read with universal newlines, the same
    # bytes are five blocks, not three -- so the hazard is really in them.
    uni, _w3 = split_blocks("cr.md", "\n".join(
        CR_DOC.decode("utf-8").splitlines()))
    with _Tmp() as t:
        # bom.md is the same document behind a UTF-8 BOM, which is encoding
        # and not text: it must read identically and be found in cr.md.
        repo = _repo(t, {"cr.md": CR_DOC, "bom.md": b"\xef\xbb\xbf" + CR_DOC})
        got = []
        for spec in ("cr.md", "HEAD:cr.md", "HEAD:bom.md"):
            rc, res, _out = _check(repo, [spec], ["cr.md"], m)
            shape = [(b.where().replace("HEAD:", "").replace("bom.md", "cr.md"),
                      b.kind) for b in res["blocks"]] if res else None
            got.append((spec, rc, shape == want))
        good = len(uni) == 5 and got == [("cr.md", 0, True),
                                         ("HEAD:cr.md", 0, True),
                                         ("HEAD:bom.md", 0, True)]
        return good, ("working file, HEAD, and HEAD behind a BOM all %s: %s; "
                      "universal newlines would give %d block(s)"
                      % ([w for w, _k in want], got, len(uni)))


# D14's mutation table: each broken matcher, and the cases it must turn red.
MUTANTS = [
    ("ALWAYS", lambda needle, hays: 0 if hays else None, ["D2", "D4", "D5"]),
    ("NEVER", lambda needle, hays: None, ["D1", "D3", "D6"]),
    ("JOINED", lambda needle, hays: 0 if needle in " ".join(hays) else None,
     ["D4"]),
    ("PREFIX40", lambda needle, hays: next(
        (i for i, h in enumerate(hays) if needle[:40] in h), None), ["D5"]),
]


def d14(m):
    fns = dict((n, f) for n, f, _t in CASES)
    targets = sorted(set(c for _n, _f, cs in MUTANTS for c in cs))
    # The unmutated control first: a kill only counts against a case that
    # is green without the mutant.
    red = [c for c in targets if not fns[c](m)[0]]
    if red:
        return False, "unmutated control is already red: %s" % red
    survivors, kills = [], 0
    for name, fn, cases in MUTANTS:
        for c in cases:
            if fns[c](fn)[0]:
                survivors.append("%s/%s" % (name, c))
            else:
                kills += 1
    return (not survivors,
            "%d matcher mutant(s), %d required kill(s), %d killed%s"
            % (len(MUTANTS), kills + len(survivors), kills,
               "; SURVIVED %s" % survivors if survivors else ""))


def d15(m):
    with _Tmp() as t:
        repo = _repo(t, {"doc.md": ALPHA + "\n",
                         "sub/" + LONG_NAME: BRAVO + "\n",
                         "sub/other.md": BRAVO + "\n",
                         "latin1.md": b"caf\xe9: " + ALPHA.encode() + b"\n"})
        _w(repo, "bad.tsv", "xyz\tnot a digest\n")
        runs = [
            ("bad rev", _check(repo, ["HEAD:nope.md"], ["doc.md"], m)),
            ("a tree", _check(repo, ["HEAD:sub"], ["doc.md"], m)),
            ("no after", _check(repo, ["doc.md"], ["missing.md"], m)),
            ("not UTF-8", _check(repo, ["latin1.md"], ["doc.md"], m)),
            ("bad allow row", _check(repo, ["doc.md"], ["doc.md"], m,
                                     ["--allow-drop", "bad.tsv"])),
            ("no git", _check(repo, ["HEAD:doc.md"], ["doc.md"], m,
                              git="docmove-no-such-git")),
        ]
        bad = [n for n, (rc, _res, out) in runs
               if rc != 2 or _verdict(out) != "REFUSED"
               or "before-blocks" in out]
        # `git show HEAD:sub` exits 0 with a listing in which LONG_NAME makes
        # a checkable block, so the population rule would NOT refuse it: "a
        # tree" is what makes `cat-file blob` load-bearing rather than taste.
        return not bad, "%d of %d refused%s" % (
            len(runs) - len(bad), len(runs),
            "; NOT refused: %s" % bad if bad else "")


def d16(m):
    path = os.path.join(HERE, "ci-census.py")
    # No .pyc: a self-test must not write into the tree it runs from, which is
    # the write a desk sweep reports as "the source moved".
    saved, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec = importlib.util.spec_from_file_location("ci_census", path)
        ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci)
    except Exception as e:
        return False, "cannot load %s: %s" % (path, e)
    finally:
        sys.dont_write_bytecode = saved
    forged = chr(0x2028) + "  ok    D99 a forged case line"
    with _Tmp() as t:
        _w(t, "before.md", ALPHA + "\n\nok  a missing block whose text "
           "starts like a case line, and then" + forged + "\n")
        _w(t, "after.md", ALPHA + "\n")
        _w(t, "allow.tsv", "%s\tstale, and the reason carries%s\n"
           % (digest16("nothing"), forged))
        rc, _res, out = _check(t, ["before.md"], ["after.md"], m,
                               ["--allow-drop", "allow.tsv"])
    parsed = ci.parse_capture(out)
    mis = ci.misindented(out)[0]
    # The control on the fixture: printed raw, the reason IS a case line.
    raw = ci.parse_capture("    line 1  x  " + forged + "\n")[0]
    good = (rc == 1 and parsed == (0, 2, [], []) and mis == 0 and raw == 1)
    return good, ("ci-census reads %d ok, %d FAIL, %d skip, %d unparsable, "
                  "%d misindented; the raw reason alone would read %d ok"
                  % (parsed[0], parsed[1], len(parsed[2]), len(parsed[3]),
                     mis, raw))


def d17(m):
    four = ("````md\n```\nnot closed by three backticks, long enough\n```\n"
            "still inside the four-backtick fence, long enough\n````\n")
    unclosed = ("Oscar: a paragraph long enough to be checked by the tool.\n"
                "\n```\nan unclosed fence, long enough to be a checkable "
                "block\n\nand more text after a blank line inside it\n")
    inline = ("```x``` is inline code at the start of a line, not a fence\n"
              "\nPapa: another paragraph long enough to be checked by it.\n")
    with _Tmp() as t:
        got = []
        for name, text, want in (
                ("four.md", four, [("four.md:1-6", "fence")]),
                ("unclosed.md", unclosed, [("unclosed.md:1-1", "para"),
                                           ("unclosed.md:3-6", "fence")]),
                ("inline.md", inline, [("inline.md:1-1", "para"),
                                       ("inline.md:3-3", "para")])):
            _w(t, name, text)
            rc, res, out = _check(t, [name], [name], m)
            shape = [(b.where(), b.kind) for b in res["blocks"]] if res \
                else None
            warned = "    warning unclosed.md:3: " in out
            got.append((name, rc == 0 and shape == want
                        and warned == (name == "unclosed.md")))
        return all(g for _n, g in got), "%s" % got


def d18(m):
    # Pure, so the Windows rule is exercised on every OS.
    forms = [("HEAD:CLAUDE.md", ("HEAD", "CLAUDE.md")),
             (":CLAUDE.md", ("", "CLAUDE.md")),
             ("HEAD~1:docs/a:b.md", ("HEAD~1", "docs/a:b.md")),
             ("CLAUDE.md", (None, "CLAUDE.md")),
             ("C:\\repo\\CLAUDE.md", (None, "C:\\repo\\CLAUDE.md")),
             ("c:/repo/CLAUDE.md", (None, "c:/repo/CLAUDE.md")),
             ("./a:b.md", (None, "./a:b.md")),
             ("/abs/a:b.md", (None, "/abs/a:b.md"))]
    wrong = [s for s, want in forms if parse_spec(s) != want]
    # One file in three states -- HEAD Alpha, index Bravo, working Charlie --
    # so each form is seen to read ITS state and not a neighbour's.
    with _Tmp() as t:
        repo = _repo(t, {"doc.md": ALPHA + "\n"},
                     staged={"doc.md": BRAVO + "\n"},
                     then={"doc.md": CHARLIE + "\n",
                           "all.md": "\n\n".join((ALPHA, BRAVO, CHARLIE))})
        want = {"HEAD:doc.md": ALPHA_NORM, ":doc.md": BRAVO_NORM,
                "doc.md": normalise(CHARLIE),
                os.path.join(repo, "doc.md"): normalise(CHARLIE)}
        read = {}
        for spec in want:
            rc, res, _out = _check(repo, [spec], ["all.md"], m)
            read[spec] = ([b.norm for b in res["blocks"]] == [want[spec]]
                          and rc == 0) if res else "rc %d" % rc
    bad = [s for s in read if read[s] is not True]
    return not wrong and not bad, (
        "%d of %d forms parse as specified%s; HEAD, the index, the working "
        "file and its absolute path each read their own state: %s"
        % (len(forms) - len(wrong), len(forms),
           "; WRONG %s" % wrong if wrong else "",
           "yes" if not bad else "NO for %s" % bad))


CASES = [
    ("D1", d1, "a block moved verbatim to a second after-file is conserved, "
               "and found in THAT file"),
    ("D2", d2, "a dropped block is reported missing, at its own lines, "
               "and the run exits 1"),
    ("D3", d3, "a re-wrapped paragraph, same words, is conserved"),
    ("D4", d4, "a block split across two after-files is NOT conserved"),
    ("D5", d5, "one character changed late in a block makes it missing, "
               "a letter or a space made U+00A0"),
    ("D6", d6, "a blockquoted paragraph moved out of the quote is conserved, "
               "and back in"),
    ("D7", d7, "a table row moved to another table is conserved; one with an "
               "edited cell is missing"),
    ("D8", d8, "a fenced block is ONE block: conserved verbatim, missing "
               "when cut in two"),
    ("D9", d9, "blocks under --min-chars are short and unchecked; the "
               "boundary is `<`, in code points"),
    ("D10", d10, "--allow-drop exempts a missing block; a stale, a conserved "
                 "or a short entry is a finding"),
    ("D11", d11, "an empty or all-short before-document is a REFUSAL, "
                 "not a clean pass"),
    ("D12", d12, "REV:PATH reads git: HEAD:file and the working file give "
                 "different block sets, and GIT_DIR cannot redirect it"),
    ("D13", d13, "bytes: a bare CR splits nothing and a BOM is not text, "
                 "from the working tree or from git"),
    ("D14", d14, "the matcher controls are load-bearing: broken matchers "
                 "turn D1-D6 red"),
    ("D15", d15, "every unreadable input is a refusal, including a tree "
                 "named as a file"),
    ("D16", d16, "the output cannot forge a ci-census case line"),
    ("D17", d17, "fence edges: a longer fence, an unclosed one (warned), "
                 "an inline ``` line"),
    ("D18", d18, "argument forms: REV:PATH, :PATH (the index), a file, and "
                 "a drive-letter path"),
]


def self_test():
    print("docmove %s self-test  --  %d controls, each one able to fail"
          % (VERSION, len(CASES)))
    passed = 0
    for name, fn, text in CASES:
        try:
            good, detail = fn(find_home)
        except Exception as e:  # a control that crashes is a control that fails
            good, detail = False, "raised %s: %s" % (type(e).__name__, e)
        case_line(sys.stdout, good, name,
                  "%s (%s)" % (text, shown(normalise(str(detail)), 600)))
        passed += 1 if good else 0
    print("%d of %d ok" % (passed, len(CASES)))
    return 0 if passed == len(CASES) else 1


def main(argv):
    if not argv or argv == ["--self-test"]:
        return self_test()
    if argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    rc, _res = run(argv, sys.stdout)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
