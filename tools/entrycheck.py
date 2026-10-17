#!/usr/bin/env python3
"""entrycheck -- gate P5e's definition of done, read one measured row at a time.

WHY IT EXISTS
-------------
P5e makes this repository readable to someone who has never seen it: a README
that fits a screen, records split so that GitHub shows them, entry pages, and
a CI job that builds code.  Its definition of done is a table of targets, and
this tool reads every one of them, so the gate cannot be declared done by eye.
It is built to this repository's rule that a tool printing 0 or PASS is making
a claim: every row has a self-test fixture that must read PASS and one that
must read RED, and a row that could not be measured never prints PASS.

USAGE
-----
  entrycheck.py report [--root DIR] [INPUTS] [--offline] [--waive ID=REASON]...
  entrycheck.py check  [--root DIR] [INPUTS] [--offline] [--waive ID=REASON]...
  entrycheck.py --self-test

`--root` defaults to the repository this file is in.  INPUTS, read by the four
online rows -- this tool never touches the network; `gh` exists only on the
Windows side of the desk and WSL's DNS is unreliable, so fetching happens
outside it and a missing input is UNMEASURED, never PASS:

  --gh-json FILE   the output of `gh repo view Jhongwe1/router-customFW
                   --json primaryLanguage,repositoryTopics`          (E12, E13)
  --blob-html DIR  every root-level .md's GitHub blob page AT HEAD, saved as
                   DIR/<name> or DIR/<name>.html, e.g.
                   curl -sL https://github.com/Jhongwe1/router-customFW/blob/<sha>/<name> -o DIR/<name>
                                                                           (E8w)
  --ci-log FILE    `gh run view <run-id> --log` of the CI run on HEAD     (E14w)

A UTF-8 or UTF-16 byte-order mark on any input is accepted (PowerShell's `>`
writes one).  An input that is named but cannot be read is a refusal.

VERDICTS
--------
  PASS        measured, and the target holds.
  RED         measured, and the target does not hold.
  WAIVED      `--waive ID=REASON` on a row the DoD lets be waived (E17, E18)
              that measures RED.  Never PASS: the measured value and the
              reason are printed beside it.  Waiving any other row is refused.
              A waiver on a row that measures PASS is STALE and fails `check`,
              so a waiver goes red when it stops being needed; a waiver on an
              UNMEASURED row is not applied.
  UNMEASURED  the input was not given, does not establish what it claims (a
              page of another commit, a log that does not name HEAD), or the
              row's population is empty.

`check` exits 0 only if every row is PASS or WAIVED and no waiver is stale.
`--offline` measures the offline rows only, prints how many rows were not
measured and which, and refuses the online inputs, which it would otherwise
have to ignore; it never excuses an OFFLINE row that could not be measured.
`report` always exits 0 unless it refuses.  Exit 2 is a refusal, with a reason
on stderr and never a traceback.

RECORDS
-------
Excluded wherever a row says "non-record": bench/, docs/history/, docs/log/,
every qemu/<date>*/ run-transcript directory (the 2026-10-09 ruling), LOG.md,
CHANGELOG.md, docs/GATE-RESULTS.md, and RUNSHEET.md -- the last at any path,
because E9 moves it off the root and it stays a record wherever it lands.
upstream/ is a submodule, one gitlink in `git ls-files`, and is never read.

EXEMPTIONS
----------
By name only, in EXEMPT, and printed beside the row: CLAUDE.md from E16 and
E19 (the 2026-10-09 ruling: its table describes the private plan directory
and defines $FWRE_WORK's path -- not E21), and this tool and its mutation
suite from E21, whose pattern they must carry.  Swept both ways: an entry
naming an untracked file, or a file its row no longer hits, is STALE and the
row is RED.

ROWS
----
Every definition is printed by `report` beside its value; ROWS below holds the
text.  The populations are `git ls-files` of --root -- tracked paths only, read
from the working tree, which `report` says is or is not HEAD's.

WHAT IT DOES NOT ESTABLISH
--------------------------
  * that the README reads well: E1-E7 measure size and shape, not prose.
  * GitHub's rendering, except for E8w, which reads the pages GitHub served
    (its parser was calibrated on the pages GitHub served for fb5a5d17 on
    2026-10-09).  E2/E5's word and cell rules follow the GFM spec as written
    here and were not compared with GitHub's rendering of any input.
  * E6 accepts an absolute image URL without fetching it.
  * E14 reads the workflow's text: a step it finds may still fail, which is
    E14w's to see.  E14w reads one log file and does not check which job
    printed the lines.
  * E15 counts a link as a hop whether or not the target renders; it refuses
    root files and records as stepping stones for that reason (ROWS).
  * E16, E19 and E21 find the spellings they list and no other.

CAUTION
-------
`report` prints its definitions, and they spell the strings E16, E19 and E21
count.  A saved report belongs under a record path (bench/, docs/history/,
docs/log/, LOG.md); anywhere else it counts itself.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse

TOOL_VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_SLUG = "Jhongwe1/router-customFW"

PASS, RED, WAIVED, UNMEASURED = "PASS", "RED", "WAIVED", "UNMEASURED"

# --------------------------------------------------------------------------
# records and populations
# --------------------------------------------------------------------------

RECORD_DIRS = ("bench/", "docs/history/", "docs/log/")
#: qemu/<yyyy-mm-dd><suffix>/: run transcripts, evidence like bench/.
RECORD_DIR_RE = re.compile(r"^qemu/20[0-9]{2}-[0-9]{2}-[0-9]{2}[^/]*/")
RECORD_FILES = ("LOG.md", "CHANGELOG.md", "docs/GATE-RESULTS.md", "RUNSHEET.md")
RECORD_ANYWHERE = ("runsheet.md",)        # basename, case-insensitive
NEVER_READ = ("upstream/",)
RECORD_SET_TEXT = ("bench/  docs/history/  docs/log/  qemu/20??-??-??*/  "
                   "LOG.md  CHANGELOG.md  docs/GATE-RESULTS.md  "
                   "RUNSHEET.md (at any path)")


def is_record(path: str) -> bool:
    return (path in RECORD_FILES or path.startswith(RECORD_DIRS)
            or bool(RECORD_DIR_RE.match(path))
            or posixpath.basename(path).lower() in RECORD_ANYWHERE)


#: E19's two strings, assembled so that this file does not carry them.
HOME_KEY = "/" + "home" + "/key"
WIN_USER = "Key" + "20"
E19_RE = re.compile(re.escape(HOME_KEY).encode() + rb"(?![A-Za-z0-9_])|"
                    + rb"(?<![A-Za-z0-9_])" + WIN_USER.encode() + rb"(?![0-9])")

#: E21: the framing terms, matched against case-folded text (`e21_text`).
#: 'résumé' with one accent dropped either way is the same word; 'resume'
#: with none is a technical word here and never matches.
E21_RE = re.compile(r"求職|招募|面試|履歷|作品集|recruit|hiring|interview"
                    r"|résumé|resumé|résume|portfolio")

#: Exempt by name, row by row.  An entry must name a tracked file that its
#: row's own pattern still hits; one that does not is STALE and turns the row
#: red, so an exemption goes red when it stops being needed.  An exemption is
#: printed beside its row, never applied silently.
EXEMPT = {
    # 2026-10-09 ruling: CLAUDE.md's "Where things are" table describes the
    # private plan/ directory and defines $FWRE_WORK's path -- information
    # for a reader, not a dead pointer.  It is NOT exempt from E21.
    "E16": ("CLAUDE.md",),
    "E19": ("CLAUDE.md",),
    # These two define and test E21's pattern, so they must carry it.
    "E21": ("tools/entrycheck.py", "tools/test-entrycheck-mutants.py"),
}
E21_EXEMPT = EXEMPT["E21"]

#: E4's status glyphs.  U+26A0 counts with or without U+FE0F.
STATUS_GLYPHS = (("\U0001F534", "U+1F534"), ("\U0001F7E2", "U+1F7E2"),
                 ("\U0001F504", "U+1F504"), ("\U0001F195", "U+1F195"),
                 ("\u26A0\uFE0F", "U+26A0 (+FE0F)"), ("\u2705", "U+2705"),
                 ("\u274C", "U+274C"))

#: E18's emoji: U+1F000-U+1FAFF, U+FE0F, U+26A0, and the BMP code points
#: whose Emoji_Presentation is Yes (Unicode emoji-data.txt).
EMOJI_BMP = frozenset([
    0x231A, 0x231B, 0x23E9, 0x23EA, 0x23EB, 0x23EC, 0x23F0, 0x23F3, 0x25FD,
    0x25FE, 0x2614, 0x2615, *range(0x2648, 0x2654), 0x267F, 0x2693, 0x26A1,
    0x26AA, 0x26AB, 0x26BD, 0x26BE, 0x26C4, 0x26C5, 0x26CE, 0x26D4, 0x26EA,
    0x26F2, 0x26F3, 0x26F5, 0x26FA, 0x26FD, 0x2705, 0x270A, 0x270B, 0x2728,
    0x274C, 0x274E, 0x2753, 0x2754, 0x2755, 0x2757, 0x2795, 0x2796, 0x2797,
    0x27B0, 0x27BF, 0x2B1B, 0x2B1C, 0x2B50, 0x2B55, 0x26A0, 0xFE0F])
E18_MARKS = ("量", "讀", "推")


def is_emoji(ch: str) -> bool:
    o = ord(ch)
    return 0x1F000 <= o <= 0x1FAFF or o in EMOJI_BMP


def _fail(msg: str) -> "NoReturn":  # noqa: F821
    """A refusal: a reason on stderr, rc 2, never a traceback."""
    print(f"entrycheck: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _git_env():
    env = dict(os.environ)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
              "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR"):
        env.pop(k, None)
    return env


def _git(root, *args):
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-C", root] + list(args),
                           capture_output=True, env=_git_env())
    except OSError as e:
        _fail(f"cannot run git: {e.strerror}")
    return r


def decode(data: bytes) -> str:
    """UTF-8, or UTF-16 by its byte-order mark; a UTF-8 BOM is dropped."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", "replace")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("utf-8", "replace")


def e21_text(data: bytes) -> str:
    """E21's view of a file: decoded, NFC, case-folded, NFC again, so that a
    decomposed capital 'RE\\u0301SUME\\u0301' and 'résumé' are one string.
    Folding first and matching exactly is the same test as a case-insensitive
    match for these terms, at a third of its cost on this tree."""
    t = unicodedata.normalize("NFC", decode(data)).casefold()
    return unicodedata.normalize("NFC", t)


class Tree:
    """The tracked population of one work tree."""

    def __init__(self, root: str):
        if not os.path.isdir(root):
            _fail(f"--root {root} is not a directory")
        self.root = os.path.abspath(root)
        r = _git(self.root, "rev-parse", "--show-toplevel")
        if r.returncode:
            _fail(f"{self.root} is not inside a git work tree")
        top = r.stdout.decode("utf-8", "replace").strip()
        if os.path.realpath(top) != os.path.realpath(self.root):
            _fail(f"--root must be the top of its work tree ({top}), not "
                  f"{self.root}: every path below is relative to the top")
        r = _git(self.root, "rev-parse", "--verify", "-q", "HEAD")
        if r.returncode:
            _fail(f"{self.root} has no commit; the online rows compare against "
                  f"HEAD")
        self.head = r.stdout.decode().strip()
        r = _git(self.root, "ls-files", "-s", "-z")
        if r.returncode:
            _fail(f"`git ls-files` failed in {self.root}")
        self.files = {}           # path -> mode, regular files and symlinks
        self.gitlinks = []
        for ent in r.stdout.decode("utf-8", "surrogateescape").split("\0"):
            if not ent:
                continue
            meta, path = ent.split("\t", 1)
            mode = meta.split()[0]
            if mode == "160000":
                self.gitlinks.append(path)
            elif not path.startswith(NEVER_READ):
                self.files[path] = mode
        if not self.files:
            _fail(f"{self.root} tracks no file: every row would be measured "
                  f"over nothing")
        r = _git(self.root, "status", "--porcelain", "--untracked-files=no")
        self.dirty = [ln for ln in r.stdout.decode("utf-8", "replace").split("\n")
                      if ln.strip()] if r.returncode == 0 else ["(git status failed)"]
        self.dirs = set()
        for p in self.files:
            d = posixpath.dirname(p)
            while d and d not in self.dirs:
                self.dirs.add(d)
                d = posixpath.dirname(d)
        self._text = {}

    def tracked(self, path: str) -> bool:
        return path in self.files

    def data(self, path: str):
        """The bytes git would store: a symlink's target, a file's content."""
        full = os.path.join(self.root, path)
        try:
            if self.files.get(path) == "120000":
                return os.readlink(full).encode("utf-8", "surrogateescape")
            with open(full, "rb") as fh:
                return fh.read()
        except OSError:
            return None

    def text(self, path: str):
        if path not in self._text:
            b = self.data(path)
            self._text[path] = (None if b is None
                                else decode(b).replace("\r\n", "\n"))
        return self._text[path]

    def size(self, path: str):
        try:
            return os.path.getsize(os.path.join(self.root, path))
        except OSError:
            return None


# --------------------------------------------------------------------------
# markdown
# --------------------------------------------------------------------------

FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FENCE_CLOSE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
H2_START = re.compile(r"^ {0,3}##(?:[ \t]|$)")

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
LINK_DEF = re.compile(r"^ {0,3}\[((?:[^\[\]\\]|\\.)+)\]:[ \t]*<?([^\s>]+)>?.*$",
                      re.M)
_TXT = r"((?:[^\[\]\\]|\\.|\[(?:[^\[\]\\]|\\.)*\])*)"
_DST = r"[ \t]*(<[^<>\n]*>|(?:[^\s()\\]|\\.|\((?:[^\s()\\]|\\.)*\))*)"
_TTL = (r"(?:\s+(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'"
        r"|\((?:[^()\\]|\\.)*\)))?[ \t]*")
INLINE = re.compile(r"(!?)\[" + _TXT + r"\]\(" + _DST + _TTL + r"\)")
REFLINK = re.compile(r"(!?)\[" + _TXT + r"\]\[((?:[^\[\]\\]|\\.)*)\]")
IMG_INLINE = re.compile(r"!\[" + _TXT + r"\]\(" + _DST + _TTL + r"\)")
IMG_REF = re.compile(r"!\[" + _TXT + r"\]\[((?:[^\[\]\\]|\\.)*)\]")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
HTML_TAG = re.compile(
    r"</?(?:a|abbr|b|br|center|code|dd|del|details|div|dl|dt|em|figcaption"
    r"|figure|h[1-6]|hr|i|img|ins|kbd|li|ol|p|picture|pre|q|s|samp|small"
    r"|source|span|strong|sub|summary|sup|table|tbody|td|tfoot|th|thead|tr"
    r"|tt|u|ul|var|video)\b[^<>]*>", re.I)
IMG_TAG = re.compile(r"<img\b[^<>]*?\bsrc\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
                     re.I)
A_TAG = re.compile(r"<a\b[^<>]*?\bhref\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
                   re.I)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
BADGE = ("badge", "shields.io")

CJK_RANGES = ((0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
              (0xF900, 0xFAFF), (0x20000, 0x2FA1F))


def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)


def line_count(text: str) -> int:
    """'\\n'-terminated lines, plus one if the text does not end in '\\n'."""
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def md_lines(text: str):
    """[(lineno, line, kind, info)]: kind 'text', 'fence' (a delimiter) or
    'code' (inside a fence whose info string is `info`)."""
    out, fence = [], None
    for n, line in enumerate(text.split("\n"), 1):
        if fence is None:
            m = FENCE_OPEN.match(line)
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)), m.group(2).strip())
                out.append((n, line, "fence", fence[2]))
            else:
                out.append((n, line, "text", ""))
            continue
        m = FENCE_CLOSE.match(line)
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
            out.append((n, line, "fence", fence[2]))
            fence = None
        else:
            out.append((n, line, "code", fence[2]))
    return out


def md_headings(mdl):
    for n, line, kind, _info in mdl:
        if kind != "text":
            continue
        m = ATX.match(line)
        if m:
            t = re.sub(r"(?:^|[ \t]+)#+[ \t]*$", "", m.group(2) or "").strip()
            yield n, len(m.group(1)), t


def first_screen(mdl):
    """(the lines before the first level-2 ATX heading, that heading's line)."""
    for idx, (n, line, kind, _info) in enumerate(mdl):
        if kind == "text" and H2_START.match(line):
            return mdl[:idx], n
    return mdl, None


def _is_mermaid(info: str) -> bool:
    """The info string GitHub renders as a diagram: `mermaid`, lower case."""
    return info.split()[:1] == ["mermaid"]


def _blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def _label(s: str) -> str:
    return " ".join(s.split()).casefold()


def _visible_links(s: str) -> str:
    """Images to nothing, links to their text; repeated for nesting."""
    def sub(m):
        return "" if m.group(1) else m.group(2)
    prev = None
    while prev != s:
        prev = s
        s = INLINE.sub(sub, s)
        s = REFLINK.sub(sub, s)
    return s


def prose(text: str) -> str:
    """What a reader sees of `text` as words (E2's and E5's removals)."""
    text = HTML_COMMENT.sub(" ", text)
    text = LINK_DEF.sub(" ", text)
    spans = []

    def stash(m):
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"
    text = CODE_SPAN.sub(stash, text)
    text = _visible_links(text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)
    text = HTML_TAG.sub(" ", text)
    return html.unescape(text)


def count_words(s: str) -> int:
    """Whitespace-separated tokens holding a letter or digit; each CJK
    ideograph or kana is a word of its own."""
    n = 0
    for tok in s.split():
        run = False
        for ch in tok:
            if is_cjk(ch):
                if run:
                    n += 1
                run = False
                n += 1
            elif ch.isalnum():
                run = True
        if run:
            n += 1
    return n


def screen_words(mdl_subset) -> int:
    keep = []
    for _n, line, kind, info in mdl_subset:
        if kind == "text" or (kind == "code" and not _is_mermaid(info)):
            keep.append(line)
        else:
            keep.append("")
    return count_words(prose("\n".join(keep)))


def split_cells(row: str):
    """GFM: split on every '|' not escaped by a backslash -- inside code spans
    too, as GitHub does -- and drop the edge cells a leading or trailing pipe
    makes."""
    s = row.strip()
    cells, cur, i, last_sep = [], [], 0, -1
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur))
            cur = []
            last_sep = i
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur))
    if s.startswith("|"):
        cells = cells[1:]
    if cells and last_sep == len(s) - 1 and len(s) > 1:
        cells = cells[:-1]
    return [c.strip() for c in cells]


DELIM_ROW = re.compile(r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")


def md_tables(mdl):
    """[[(lineno, [cells])]], header row first, cells past the header's count
    dropped."""
    out, k = [], 0
    while k < len(mdl):
        n, line, kind, _info = mdl[k]
        if (kind == "text" and "|" in line and DELIM_ROW.match(line) and k > 0
                and mdl[k - 1][2] == "text" and "|" in mdl[k - 1][1]):
            head = split_cells(mdl[k - 1][1])
            if len(head) == len(split_cells(line)):
                rows = [(mdl[k - 1][0], head)]
                j = k + 1
                while j < len(mdl):
                    jn, jl, jk, _ = mdl[j]
                    if (jk != "text" or not jl.strip() or ATX.match(jl)
                            or jl.lstrip().startswith(">")):
                        break
                    rows.append((jn, split_cells(jl)[:len(head)]))
                    j += 1
                out.append(rows)
                k = j
                continue
        k += 1
    return out


def _masked_body(text: str, mdl=None) -> str:
    """Text lines only (fenced code blanked), comments and code spans blanked,
    offsets and line numbers kept."""
    mdl = mdl if mdl is not None else md_lines(text)
    body = "\n".join(line if kind == "text" else "" for _n, line, kind, _ in mdl)
    body = HTML_COMMENT.sub(_blank, body)
    return CODE_SPAN.sub(_blank, body)


def _lineno(body: str, pos: int) -> int:
    return body.count("\n", 0, pos) + 1


def _defs(body: str):
    d = {}
    for m in LINK_DEF.finditer(body):
        d.setdefault(_label(m.group(1)), m.group(2))
    return d


def md_links(text: str):
    """[(lineno, destination)] of every link that is not an image, outside
    fenced code, code spans and HTML comments."""
    body = _masked_body(text)
    defs = _defs(body)
    out = []
    for m in INLINE.finditer(body):
        if not m.group(1):
            out.append((_lineno(body, m.start()), m.group(3)))
    for m in REFLINK.finditer(body):
        if not m.group(1):
            lab = _label(m.group(3) or m.group(2))
            if lab in defs:
                out.append((_lineno(body, m.start()), defs[lab]))
    for m in A_TAG.finditer(body):
        out.append((_lineno(body, m.start()), m.group(1).strip("\"'")))
    return out


def md_images(body: str, defs):
    """[(offset, target)] of images in an already-masked body."""
    out = []
    for m in IMG_INLINE.finditer(body):
        out.append((m.start(), m.group(2)))
    for m in IMG_REF.finditer(body):
        lab = _label(m.group(2) or m.group(1))
        if lab in defs:
            out.append((m.start(), defs[lab]))
    for m in IMG_TAG.finditer(body):
        out.append((m.start(), m.group(1).strip("\"'")))
    return sorted(out)


def resolve(tree: Tree, src: str, dest: str):
    """-> (tracked path the link reaches or None, the path it names or None).
    A tracked directory reaches its README.md."""
    d = dest.strip()
    if d.startswith("<") and d.endswith(">"):
        d = d[1:-1].strip()
    if not d or d.startswith(("#", "//")) or SCHEME.match(d):
        return None, None
    d = d.split("#", 1)[0].split("?", 1)[0]
    if not d:
        return None, None
    d = urllib.parse.unquote(d)
    if d.startswith("/"):
        cand = posixpath.normpath(d.lstrip("/") or ".")
    else:
        cand = posixpath.normpath(posixpath.join(posixpath.dirname(src), d))
    if cand == ".":
        cand = ""
    if cand == ".." or cand.startswith("../"):
        return None, cand
    if cand in tree.files:
        return cand, cand
    if cand == "" or cand in tree.dirs:
        readme = posixpath.join(cand, "README.md") if cand else "README.md"
        return (readme if readme in tree.files else None), readme
    return None, cand


# --------------------------------------------------------------------------
# a GitHub workflow, read as the block YAML it is written in
# --------------------------------------------------------------------------

_YKEY = re.compile(r"""^("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"\-][^:#]*?|-[^\s][^:#]*?)[ \t]*:(?:[ \t]+(.*))?$""")


def yaml_blocks(text: str):
    """The block YAML a workflow is written in: mappings and sequences by
    indentation, plain (multi-line too) and quoted scalars, `|` and `>`
    block scalars.  A flow collection stays a string.  A line it cannot place
    raises ValueError with its number."""
    raw = text.replace("\r\n", "\n").split("\n")
    n = len(raw)
    pos = 0

    def ind(s):
        return len(s) - len(s.lstrip(" "))

    def skip():
        nonlocal pos
        while pos < n and (not raw[pos].strip()
                           or raw[pos].lstrip().startswith("#")):
            pos += 1

    def plain(v):
        m = re.search(r"[ \t]#", v)
        return (v[:m.start()] if m else v).strip()

    def scalar(v):
        v = v.strip()
        if v.startswith('"'):
            out, i = [], 1
            while i < len(v):
                c = v[i]
                if c == "\\" and i + 1 < len(v):
                    out.append({"n": "\n", "t": "\t", '"': '"',
                                "\\": "\\"}.get(v[i + 1], "\\" + v[i + 1]))
                    i += 2
                    continue
                if c == '"':
                    return "".join(out)
                out.append(c)
                i += 1
            raise ValueError(f"line {pos}: an unterminated double-quoted scalar")
        if v.startswith("'"):
            out, i = [], 1
            while i < len(v):
                if v[i] == "'":
                    if v[i + 1:i + 2] == "'":
                        out.append("'")
                        i += 2
                        continue
                    return "".join(out)
                out.append(v[i])
                i += 1
            raise ValueError(f"line {pos}: an unterminated single-quoted scalar")
        return plain(v)

    def block_scalar(header, parent):
        nonlocal pos
        lines = []
        while pos < n:
            s = raw[pos]
            if s.strip() and ind(s) <= parent:
                break
            lines.append(s)
            pos += 1
        while lines and not lines[-1].strip():
            lines.pop()
        body = [ln for ln in lines if ln.strip()]
        base = min(ind(ln) for ln in body) if body else 0
        lines = [ln[base:] if ln.strip() else "" for ln in lines]
        if header.startswith("|"):
            return "\n".join(lines)
        out, para = [], []
        for ln in lines:
            if ln.strip():
                para.append(ln.strip())
            else:
                if para:
                    out.append(" ".join(para))
                    para = []
                out.append("")
        if para:
            out.append(" ".join(para))
        return "\n".join(out)

    def node(min_ind):
        nonlocal pos
        skip()
        if pos >= n or ind(raw[pos]) < min_ind:
            return None
        t = raw[pos].strip()
        if t == "-" or t.startswith("- "):
            return seq(ind(raw[pos]))
        if not _YKEY.match(t):
            # a scalar on the line(s) under its key: `run:` then the command
            if t[:1] in ("'", '"'):
                pos += 1
                return scalar(t)
            i0, parts = ind(raw[pos]), []
            while pos < n and (not raw[pos].strip() or ind(raw[pos]) >= i0):
                if raw[pos].strip() and not raw[pos].lstrip().startswith("#"):
                    parts.append(plain(raw[pos]))
                pos += 1
            return " ".join(parts)
        return mapping(ind(raw[pos]))

    def seq(i):
        nonlocal pos
        items = []
        while True:
            skip()
            if pos >= n:
                break
            s = raw[pos]
            t = s.strip()
            if ind(s) != i or not (t == "-" or t.startswith("- ")):
                break
            after = s[i + 1:]
            rest = after.lstrip(" ")
            if not rest or rest.startswith("#"):
                pos += 1
                items.append(node(i + 1))
                continue
            at = i + 1 + (len(after) - len(rest))
            if _YKEY.match(rest):
                raw[pos] = " " * at + rest
                items.append(mapping(at))
            else:
                pos += 1
                items.append(scalar(rest))
        return items

    def mapping(i):
        nonlocal pos
        d = {}
        while True:
            skip()
            if pos >= n:
                break
            s = raw[pos]
            if ind(s) < i:
                break
            if ind(s) > i:
                raise ValueError(f"line {pos + 1}: indented {ind(s)} where a "
                                 f"key at {i} was expected")
            t = s.strip()
            if t == "-" or t.startswith("- "):
                break
            m = _YKEY.match(t)
            if not m:
                raise ValueError(f"line {pos + 1}: not a `key: value` line")
            k = m.group(1)
            key = scalar(k) if k[0] in "'\"" else k.strip()
            val = m.group(2)
            pos += 1
            if val is None or plain(val) == "":
                skip()
                if (pos < n and ind(raw[pos]) == i
                        and (raw[pos].strip() == "-"
                             or raw[pos].strip().startswith("- "))):
                    d[key] = seq(i)
                else:
                    d[key] = node(i + 1)
            elif re.match(r"^[|>][-+0-9]*[ \t]*(?:#.*)?$", val.strip()):
                d[key] = block_scalar(val.strip(), i)
            else:
                v = scalar(val)
                if val.strip()[:1] not in ("'", '"'):
                    more = []
                    while (pos < n and raw[pos].strip() and ind(raw[pos]) > i
                           and not raw[pos].lstrip().startswith("#")):
                        more.append(plain(raw[pos]))
                        pos += 1
                    if more:
                        v = " ".join([v] + more)
                d[key] = v
        return d

    skip()
    if pos < n and raw[pos].strip() == "---":
        pos += 1
    doc = node(0)
    skip()
    if pos < n:
        raise ValueError(f"line {pos + 1}: left over after the document")
    return doc


def _disabled(cond) -> bool:
    if not isinstance(cond, str):
        return cond is False
    c = re.sub(r"\s+", "", cond).lower()
    return c in ("false", "${{false}}")


SEPARATORS = {"&&", "||", ";", "|", "&", ";;", "|&", "(", ")", "{", "}"}
WRAPPERS = {"env", "sudo", "time", "nice", "exec", "command", "nohup"}


def shell_commands(script: str):
    """[argv] of the simple commands in a shell script: comment lines and
    comments dropped, backslash-newline joined, split on && || ; | & ( ) and
    newlines, redirections removed, leading VAR=value and wrappers dropped."""
    out = []
    for line in script.replace("\\\n", " ").split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        try:
            toks = list(lex)
        except ValueError:
            toks = line.split()
        cur, skip_next = [], False
        for t in toks:
            if skip_next:
                skip_next = False
                continue
            if t in SEPARATORS:
                if cur:
                    out.append(cur)
                cur = []
            elif t and set(t) <= set("<>&"):
                if cur and cur[-1].isdigit():
                    cur.pop()
                skip_next = True
            else:
                cur.append(t)
        if cur:
            out.append(cur)
    cleaned = []
    for argv in out:
        while argv and (argv[0] in WRAPPERS or re.match(r"^[A-Za-z_]\w*=", argv[0])):
            argv = argv[1:]
        if argv:
            cleaned.append(argv)
    return cleaned


def _is_make(word: str) -> bool:
    return (posixpath.basename(word) in ("make", "gmake")
            or word in ("$(MAKE)", "${MAKE}", "$MAKE"))


def make_call(argv, cwd: str):
    """(directory relative to the repository top, goals) of a make argv."""
    d, goals, i = cwd, [], 1

    def go(rel):
        p = posixpath.normpath(posixpath.join(d, rel))
        return "" if p == "." else p
    while i < len(argv):
        a = argv[i]
        if a in ("-C", "--directory") and i + 1 < len(argv):
            d = go(argv[i + 1])
            i += 2
            continue
        if a.startswith("--directory="):
            d = go(a.split("=", 1)[1])
        elif a.startswith("-C") and len(a) > 2:
            d = go(a[2:])
        elif a in ("-f", "--file", "--makefile", "-I", "--include-dir", "-o",
                   "--old-file", "--assume-old", "-W", "--what-if",
                   "--new-file", "--assume-new"):
            i += 2
            continue
        elif a in ("-j", "--jobs", "-l", "--load-average", "--max-load"):
            if i + 1 < len(argv) and re.match(r"^\d+(?:\.\d+)?$", argv[i + 1]):
                i += 1
        elif not a.startswith("-") and "=" not in a:
            goals.append(a)
        i += 1
    return d, goals


def makefile_rules(text: str):
    """({target: (prerequisites, recipe lines)}, default goal) of the explicit
    rules of a Makefile."""
    rules, order, cur = {}, [], None
    for line in text.replace("\\\n", " ").split("\n"):
        if line.startswith("\t"):
            if cur:
                for t in cur:
                    rules[t][1].append(line[1:])
            continue
        s = line.split("#", 1)[0].rstrip()
        if not s.strip():
            continue
        m = re.match(r"^([^:=#\t][^:=#]*?)[ \t]*:(?![=:])(.*)$", s)
        if m and "=" not in m.group(1):
            targets = m.group(1).split()
            head, _sep, inline = m.group(2).partition(";")
            prereqs = [] if "=" in head else head.split()
            for t in targets:
                rules.setdefault(t, ([], []))
                rules[t][0].extend(prereqs)
                if inline.strip():
                    rules[t][1].append(inline.strip())
                if not t.startswith(".") and "%" not in t:
                    order.append(t)
            cur = targets
            continue
        cur = None
    return rules, (order[0] if order else None)


def _recipe_script(line: str) -> str:
    """A recipe line as the shell sees it, near enough: the @+- prefixes
    gone, `$(MAKE)` read as make, any other `$(VAR)` kept as one opaque word,
    and `$$` as `$`."""
    line = re.sub(r"^[@+\-\s]+", "", line)

    def var(m):
        name = m.group(1) or m.group(2)
        return "make" if name == "MAKE" else f"__{name}__"
    line = re.sub(r"\$\((\w+)\)|\$\{(\w+)\}", var, line)
    return line.replace("$$", "$")


def find_suites(tree: Tree, doc, wfname: str = "ci.yml"):
    """{'userspace': [...], 'rlxboot': [...]}: where the workflow runs each."""
    found = {"userspace": [], "rlxboot": []}
    src_rules, _ = makefile_rules(tree.text("src/Makefile") or "")
    rlxboot_goal_runs_hosttest = any(
        "hosttest" in ln for ln in src_rules.get("rlxboot", ([], []))[1])

    def take(argv, cwd, where, depth):
        if not argv:
            return cwd
        if argv[0] == "cd":
            if len(argv) > 1:
                p = posixpath.normpath(posixpath.join(cwd, argv[1]))
                return "" if p == "." else p
            return ""
        shown = " ".join(argv)
        if _is_make(argv[0]):
            d, goals = make_call(argv, cwd)
            if d == "src" and "test" in goals:
                found["userspace"].append(f"{where}: {shown}")
            if (d == "src/rlxboot" and "hosttest" in goals) or (
                    d == "src" and "rlxboot" in goals and rlxboot_goal_runs_hosttest):
                found["rlxboot"].append(f"{where}: {shown}")
            if d == "" and depth < 4:
                mk = next((m for m in ("GNUmakefile", "makefile", "Makefile")
                           if m in tree.files), None)
                if mk:
                    rules, default = makefile_rules(tree.text(mk) or "")
                    seen = set()
                    todo = list(goals) or ([default] if default else [])
                    while todo:
                        g = todo.pop(0)
                        if g in seen or g not in rules:
                            continue
                        seen.add(g)
                        todo.extend(rules[g][0])
                        for rl in rules[g][1]:
                            for sub in shell_commands(_recipe_script(rl)):
                                take(sub, "", f"{where} -> {mk}:{g}", depth + 1)
            return cwd
        script = argv[0]
        if script in ("sh", "bash", "/bin/sh", "/bin/bash") and len(argv) > 1:
            script = argv[1]
        p = posixpath.normpath(posixpath.join(cwd, script))
        if p == "src/rlxboot/test/run-host-tests.sh":
            found["rlxboot"].append(f"{where}: {shown}")
        return cwd

    jobs = doc.get("jobs") if isinstance(doc, dict) else None
    if not isinstance(jobs, dict):
        return found, "the workflow has no `jobs:` mapping"
    for jname, job in jobs.items():
        if not isinstance(job, dict) or _disabled(job.get("if")):
            continue
        for k, step in enumerate(job.get("steps") or [], 1):
            if not isinstance(step, dict) or "run" not in step:
                continue
            if _disabled(step.get("if")):
                continue
            wd = step.get("working-directory")
            cwd = posixpath.normpath(wd) if isinstance(wd, str) and wd else ""
            cwd = "" if cwd == "." else cwd
            where = f"{wfname} job `{jname}` step {k}"
            for argv in shell_commands(str(step["run"])):
                cwd = take(argv, cwd, where, 0)
    return found, None


# --------------------------------------------------------------------------
# the online inputs
# --------------------------------------------------------------------------

EMBEDDED = re.compile(r"<script\b[^>]*data-target=\"react-app\.embeddedData\""
                      r"[^>]*>(.*?)</script>", re.S)
BANNER = "Sorry about that"


def _dig(o, *keys):
    for k in keys:
        if not isinstance(o, dict) or k not in o:
            return None
        o = o[k]
    return o


def read_blob_page(page: str):
    """(path, commit, large, rendered) from a saved GitHub blob page, or a
    string saying why the page cannot be read as one."""
    m = EMBEDDED.search(page)
    if not m:
        return "no react-app embedded payload: not a GitHub blob page, or " \
               "GitHub changed its markup"
    try:
        j = json.loads(m.group(1))
    except ValueError as e:
        return f"the embedded payload is not JSON ({e})"
    path = (_dig(j, "payload", "codeViewLayoutRoute", "path")
            or _dig(j, "payload", "codeViewBlobRoute", "path"))
    oid = (_dig(j, "payload", "codeViewLayoutRoute", "refInfo", "currentOid")
           or _dig(j, "payload", "codeViewBlobLayoutRoute", "refInfo",
                   "currentOid"))
    large = _dig(j, "payload", "codeViewBlobLayoutRoute", "blob", "large")
    if not isinstance(large, bool):
        return "the payload has no blob.large flag -- a 404 page, or GitHub " \
               "changed its payload"
    rich = _dig(j, "payload", "codeViewBlobRoute", "richText")
    return path, oid, large, isinstance(rich, str) and bool(rich)


GH_PREFIX = re.compile(r"^[^\t\n]*\t[^\t\n]*\t(?=\d{4}-\d\d-\d\dT)")
LOG_TS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SRC_TEST_ECHO = re.compile(r"test: \$\$n of \$\(words \$\(PROGS\)\) program "
                           r"suites ran and passed")
PROGS_DEF = re.compile(r"^PROGS[ \t]*[:?]?=[ \t]*(.*)$", re.M)
HOSTSUITE_ECHO = re.compile(r"^[ \t]*echo[ \t]+([\"'])host suite: PASS\1[ \t]*$", re.M)
HOSTSUITE_LINE = "host suite: PASS"


def log_lines(text: str):
    for raw in text.split("\n"):
        s = ANSI.sub("", raw.rstrip("\r"))
        s = GH_PREFIX.sub("", s, count=1).lstrip("\ufeff")
        yield LOG_TS.sub("", s, count=1).rstrip()


class Inputs:
    def __init__(self, gh_json=None, blob_dir=None, ci_log=None, offline=False):
        self.gh_json, self.blob_dir, self.ci_log = gh_json, blob_dir, ci_log
        self.offline = offline


def _read_input(path: str, what: str) -> str:
    try:
        with open(path, "rb") as fh:
            return decode(fh.read())
    except OSError as e:
        _fail(f"{what} {path}: {e.strerror}")


# --------------------------------------------------------------------------
# the rows
# --------------------------------------------------------------------------

def _need(tree, path):
    t = tree.text(path) if tree.tracked(path) else None
    return t


def e1(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    n = line_count(t)
    return (PASS if n <= 150 else RED), f"{n} lines", []


def e2(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    screen, h2 = first_screen(md_lines(t))
    n = screen_words(screen)
    where = (f"lines 1-{h2 - 1}, before the first `## ` at :{h2}" if h2
             else "the whole file: it has no `## ` heading")
    return (PASS if n <= 200 else RED), f"{n} words", [f"first screen = {where}"]


DATE_RE = re.compile(r"(?<![0-9])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")


def e3(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    hits = [(t.count("\n", 0, m.start()) + 1, m.group(0))
            for m in DATE_RE.finditer(t)]
    ev = [f"first: :{ln} {d}" for ln, d in hits[:3]]
    return (PASS if len(hits) <= 1 else RED), f"{len(hits)} dates", ev


def e4(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    counts = []
    for glyph, name in STATUS_GLYPHS:
        c = t.count(glyph[0])
        counts.append((glyph, name, c))
    total = sum(c for _g, _n, c in counts)
    shown = "  ".join(f"{g} {c}" for g, _n, c in counts)
    status = {g[0] for g, _n, _c in counts}
    other = {}
    for ch in t:
        if is_emoji(ch) and ch not in status and ch != "\uFE0F":
            other[ch] = other.get(ch, 0) + 1
    ev = [f"per glyph: {shown}"]
    if other:
        ev.append("other emoji, not counted: "
                  + "  ".join(f"{ch} U+{ord(ch):04X} x{c}"
                              for ch, c in sorted(other.items())))
    return (PASS if total == 0 else RED), f"{total} status emoji", ev


def e5(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    best = None
    ncells = 0
    mdl = md_lines(t)
    tables = md_tables(mdl)
    seen = set()
    for rows in tables:
        seen.add(rows[0][0] + 1)                    # the delimiter row
        for ln, cells in rows:
            seen.add(ln)
            for ci, cell in enumerate(cells, 1):
                ncells += 1
                w = count_words(prose(cell.replace("\\|", "|")))
                if best is None or w > best[0]:
                    best = (w, ln, ci, cell)
    # The control on the parser: a line that starts with '|' and is in no
    # table it recognised.  With no table at all, such a line makes the row
    # UNMEASURED -- "no cell is long" must not rest on a parser that missed
    # the table.
    loose = [n for n, line, kind, _ in mdl
             if kind == "text" and line.lstrip().startswith("|") and n not in seen]
    note = ([f"{len(loose)} line(s) start with '|' outside every table "
             f"recognised, first :{loose[0]}"] if loose else [])
    if best is None:
        if loose:
            return UNMEASURED, "no table recognised", note
        return PASS, "no table", ["README.md has no GFM table and no line "
                                  "starting with '|'"]
    w, ln, ci, cell = best
    pv = " ".join(cell.split())[:70]
    return ((PASS if w <= 60 else RED), f"{w} words at :{ln}",
            [f"{len(tables)} table(s), {ncells} cells; longest: line {ln}, "
             f"column {ci}: {pv!r}..."] + note)


def e6(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    mdl = md_lines(t)
    screen, _h2 = first_screen(mdl)
    found, refused = [], []
    k = 0
    while k < len(screen):
        n, _line, kind, info = screen[k]
        if kind == "fence" and _is_mermaid(info):
            j, body = k + 1, False
            while j < len(screen) and screen[j][2] == "code":
                body = body or bool(screen[j][1].strip())
                j += 1
            if j < len(screen) and body:
                found.append(f":{n} a mermaid fence")
            k = j + 1
            continue
        k += 1
    body = _masked_body(t, screen)
    defs = _defs(_masked_body(t, mdl))
    for off, target in md_images(body, defs):
        ln = _lineno(body, off)
        tgt = target.strip().strip("<>")
        if any(b in tgt.lower() for b in BADGE):
            refused.append(f":{ln} {tgt} is a badge")
            continue
        if SCHEME.match(tgt) or tgt.startswith("//"):
            found.append(f":{ln} an image at {tgt} (absolute; not fetched)")
            continue
        got, named = resolve(tree, "README.md", tgt)
        if got:
            found.append(f":{ln} an image, {got}")
        else:
            refused.append(f":{ln} {tgt} -> {named or '?'} is not tracked")
    ev = found + [f"not counted: {r}" for r in refused]
    return ((PASS if found else RED),
            f"{len(found)} diagram/image" + ("" if len(found) == 1 else "s"), ev)


def e7(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    mdl = md_lines(t)
    heads = list(md_headings(mdl))
    cands = []
    for idx, (n, level, text) in enumerate(heads):
        if not re.search(r"build", text, re.I):
            continue
        end = next((hn for hn, hl, _t in heads[idx + 1:] if hl <= level),
                   len(mdl) + 1)
        sect = [x for x in mdl if n < x[0] < end]
        nonblank = sum(1 for x in sect if x[1].strip())
        body_text = "\n".join(x[1] if x[2] == "text" else "" for x in sect)
        links = []
        for _ln, dest in md_links(body_text):
            got, named = resolve(tree, "README.md", dest)
            links.append((got, named))
        good = any(g == "docs/build.md" for g, _nm in links)
        named = any(nm == "docs/build.md" for _g, nm in links)
        cands.append((n, level, text, nonblank, good, named))
    if not cands:
        return RED, "no section", ["no heading matches /build/i"]
    ev = []
    ok = False
    for n, level, text, nonblank, good, named in cands:
        why = []
        if nonblank > 10:
            why.append(f"{nonblank} non-blank body lines")
        if not good:
            why.append("names docs/build.md, which is not tracked" if named
                       else "no link reaching docs/build.md")
        ev.append(f":{n} {'#' * level} {text} -- "
                  + ("passes" if not why else "; ".join(why)))
        ok = ok or not why
    best = next((c for c in cands if c[3] <= 10 and c[4]), cands[0])
    return ((PASS if ok else RED),
            f"`{best[2][:30]}`: {best[3]} lines" + ("" if best[4] else ", no link"),
            ev)


def e8(tree, inp):
    if not tree.tracked("LOG.md"):
        return UNMEASURED, "LOG.md is not tracked", []
    n = tree.size("LOG.md")
    if n is None:
        return UNMEASURED, "LOG.md cannot be read", []
    return (PASS if n <= 1_000_000 else RED), f"{n:,} bytes", []


def e8w(tree, inp):
    if not inp.blob_dir:
        return UNMEASURED, "no --blob-html", []
    names = sorted(p for p in tree.files if "/" not in p and p.endswith(".md"))
    if not names:
        return UNMEASURED, "no root-level .md", []
    big, unread, ev = [], [], []
    for name in names:
        page = None
        for cand in (name, name + ".html"):
            fp = os.path.join(inp.blob_dir, cand)
            if os.path.isfile(fp):
                page = _read_input(fp, "--blob-html page")
                break
        if page is None:
            unread.append(name)
            ev.append(f"{name}: no saved page")
            continue
        r = read_blob_page(page)
        if isinstance(r, str):
            unread.append(name)
            ev.append(f"{name}: {r}")
            continue
        path, oid, large, rendered = r
        if path != name:
            unread.append(name)
            ev.append(f"{name}: the page is for {path!r}")
            continue
        if oid != tree.head:
            unread.append(name)
            ev.append(f"{name}: the page shows commit {str(oid)[:12]}, "
                      f"not HEAD {tree.head[:12]}")
            continue
        phrase = BANNER in page
        own = BANNER in (tree.text(name) or "")
        size = tree.size(name) or 0
        shown = ("not shown" if large else
                 "shown as markdown" if rendered else "shown as source")
        if large:
            big.append(name)
            ev.append(f"{name}: {size:,} bytes, large=true, "
                      f"{'banner present' if phrase else 'NO banner'} -- {shown}")
        elif phrase and not own:
            unread.append(name)
            ev.append(f"{name}: '{BANNER}' is on the page, large=false, and "
                      f"the file does not carry the phrase -- unexplained")
        else:
            ev.append(f"{name}: {size:,} bytes, {shown}"
                      + (" (the phrase on the page is the file's own text)"
                         if phrase else ""))
    if big:
        return RED, f"{len(big)} of {len(names)} not shown", ev
    if unread:
        return UNMEASURED, f"{len(unread)} of {len(names)} pages unread", ev
    return PASS, f"0 of {len(names)} not shown", ev


def e9(tree, inp):
    at_root = [p for p in tree.files if "/" not in p and p.lower() == "runsheet.md"]
    elsewhere = [p for p in tree.files if "/" in p
                 and posixpath.basename(p).lower() == "runsheet.md"]
    ev = [f"elsewhere: {', '.join(elsewhere)}"] if elsewhere else []
    if at_root:
        return RED, "at the root", ev
    return PASS, "not at the root", ev


def e10(tree, inp):
    t = _need(tree, "CHANGELOG.md")
    if t is None:
        return UNMEASURED, "CHANGELOG.md is not tracked", []
    mdl = md_lines(t)
    total = line_count(t)
    heads = [(n, lv, tx) for n, lv, tx in md_headings(mdl) if lv <= 2]
    sects = []
    for idx, (n, lv, tx) in enumerate(heads):
        if lv != 2:
            continue
        end = heads[idx + 1][0] if idx + 1 < len(heads) else total + 1
        sects.append((end - n, n, tx))
    if not sects:
        return UNMEASURED, f"{total} lines, no `## ` section", [
            "the per-section limit has nothing to measure"]
    longest = max(sects)
    over = [s for s in sects if s[0] > 40]
    ev = [f"{len(sects)} sections, {len(over)} over 40; longest `## "
          f"{longest[2][:40]}` {longest[0]} lines at :{longest[1]}"]
    ok = total <= 300 and not over
    return ((PASS if ok else RED),
            f"{total} lines; longest section {longest[0]}", ev)


def e11(tree, inp):
    t = _need(tree, "PROGRESS.md")
    if t is None:
        return UNMEASURED, "PROGRESS.md is not tracked", []
    n = line_count(t)
    return (PASS if n <= 200 else RED), f"{n} lines", []


def _gh(inp):
    if not inp.gh_json:
        return None, "no --gh-json"
    text = _read_input(inp.gh_json, "--gh-json")
    try:
        j = json.loads(text)
    except ValueError as e:
        return None, f"--gh-json is not JSON ({e})"
    if not isinstance(j, dict):
        return None, "--gh-json is not a JSON object"
    nwo = j.get("nameWithOwner")
    if nwo is not None and nwo != REPO_SLUG:
        return None, f"--gh-json describes {nwo}, not {REPO_SLUG}"
    return j, None


def e12(tree, inp):
    j, why = _gh(inp)
    if j is None:
        return UNMEASURED, why, []
    if "primaryLanguage" not in j:
        return UNMEASURED, "--gh-json has no primaryLanguage", []
    pl = j["primaryLanguage"]
    name = pl.get("name") if isinstance(pl, dict) else None
    shown = name or "none"
    return (PASS if name == "C" else RED), shown, []


def e13(tree, inp):
    j, why = _gh(inp)
    if j is None:
        return UNMEASURED, why, []
    if "repositoryTopics" not in j:
        return UNMEASURED, "--gh-json has no repositoryTopics", []
    tp = j["repositoryTopics"] or []
    if not isinstance(tp, list):
        return UNMEASURED, "repositoryTopics is not a list", []
    names = [x.get("name") if isinstance(x, dict) else str(x) for x in tp]
    return ((PASS if len(names) >= 8 else RED), f"{len(names)} topics",
            [", ".join(map(str, names))] if names else [])


WORKFLOWS = ".github/workflows/"


def workflow_files(tree):
    """The workflow files GitHub runs: tracked .yml and .yaml directly under
    .github/workflows/, sorted.  GitHub reads no subdirectory of it."""
    return sorted(p for p in tree.files
                  if p.startswith(WORKFLOWS) and "/" not in p[len(WORKFLOWS):]
                  and p.endswith((".yml", ".yaml")))


def e14(tree, inp):
    # Every workflow, not ci.yml alone: P5e-4 puts the code in a workflow of
    # its own so that one badge reports code, and the row asks for a CI job
    # that builds and tests it, wherever that job is declared.
    wfs = workflow_files(tree)
    if not wfs:
        return UNMEASURED, f"no workflow under {WORKFLOWS}", []
    found = {"userspace": [], "rlxboot": []}
    for wf in wfs:
        t = _need(tree, wf)
        if t is None:
            return UNMEASURED, f"{wf} cannot be read", []
        try:
            doc = yaml_blocks(t)
        except ValueError as e:
            return UNMEASURED, f"cannot read {wf}", [str(e)]
        got, why = find_suites(tree, doc, posixpath.basename(wf))
        if why:
            return UNMEASURED, f"{wf}: {why}", []
        for k in found:
            found[k] += got[k]
    ev = [f"read {len(wfs)} workflow(s): "
          + ", ".join(posixpath.basename(w) for w in wfs)]
    for k, label in (("userspace", "userspace host suite"),
                     ("rlxboot", "rlxboot hosttest")):
        ev.append(f"{label}: " + ("; ".join(found[k][:2]) if found[k]
                                  else "not run by any step"))
    both = bool(found["userspace"]) and bool(found["rlxboot"])
    have = [k for k in ("userspace", "rlxboot") if found[k]]
    return ((PASS if both else RED),
            ("both run" if both else
             (f"only {have[0]}" if have else "neither runs")), ev)


def e14w(tree, inp):
    if not inp.ci_log:
        return UNMEASURED, "no --ci-log", []
    mk = tree.text("src/Makefile") if tree.tracked("src/Makefile") else None
    mk = mk.replace("\\\n", " ") if mk else mk
    hs = (tree.text("src/rlxboot/test/run-host-tests.sh")
          if tree.tracked("src/rlxboot/test/run-host-tests.sh") else None)
    if not mk or not SRC_TEST_ECHO.search(mk) or not PROGS_DEF.search(mk):
        return UNMEASURED, "src/Makefile no longer prints the line", [
            "its `test` goal's summary echo or PROGS changed; this row's "
            "expected line must follow it"]
    if not hs or not HOSTSUITE_ECHO.search(hs):
        return UNMEASURED, "run-host-tests.sh no longer prints the line", []
    nprogs = len(PROGS_DEF.search(mk).group(1).split("#", 1)[0].split())
    want = [f"test: {nprogs} of {nprogs} program suites ran and passed",
            HOSTSUITE_LINE]
    text = _read_input(inp.ci_log, "--ci-log")
    if not re.search(r"(?<![0-9a-f])" + tree.head + r"(?![0-9a-f])", text):
        return UNMEASURED, "the log does not name HEAD", [
            f"HEAD {tree.head} appears nowhere in it: not evidence about "
            f"this commit"]
    lines = set(log_lines(text))
    missing = [w for w in want if w not in lines]
    ev = [f"wanted, as whole lines: {want[0]!r} and {want[1]!r}"]
    if missing:
        return RED, f"{len(missing)} of 2 lines missing", ev + [
            "missing: " + "; ".join(repr(m) for m in missing)]
    return PASS, "both lines, log of HEAD", ev


MAX_HOPS = 2


def _stepping(path: str) -> bool:
    """A file whose links count as a hop: docs/README.md, a non-record .md
    under docs/ or notes/, or a README.md under docs/ (a record directory's
    index)."""
    if path == "docs/README.md":
        return True
    if not (path.startswith(("docs/", "notes/")) and path.endswith(".md")):
        return False
    return not is_record(path) or (path.startswith("docs/")
                                    and posixpath.basename(path) == "README.md")


def e15(tree, inp):
    pop = sorted(p for p in tree.files
                 if p.endswith(".md") and p.startswith(("docs/", "notes/")))
    start = "docs/README.md"
    if start not in tree.files:
        return RED, "no docs/README.md", [
            f"{len(pop)} .md under docs/ and notes/, none reachable"]
    depth = {start: 0}
    frontier = [start]
    for d in range(1, MAX_HOPS + 1):
        nxt = []
        for p in frontier:
            if not _stepping(p):
                continue
            for _ln, dest in md_links(tree.text(p) or ""):
                got, _named = resolve(tree, p, dest)
                if got and got.endswith(".md") and got not in depth:
                    depth[got] = d
                    nxt.append(got)
        frontier = nxt
    unreach = [p for p in pop if p not in depth]
    ev = [f"{len(pop)} .md under docs/ and notes/; "
          f"{sum(1 for p in pop if depth.get(p) == 1)} at 1 hop, "
          f"{sum(1 for p in pop if depth.get(p) == 2)} at 2"]
    if unreach:
        ev.append("unreachable: " + ", ".join(unreach))
    return ((PASS if not unreach else RED),
            f"{len(unreach)} of {len(pop)} unreachable", ev)


E16_PATH = re.compile(r"(?<![\w./\\-])(?:\.{1,2}/)*plan/")
E16_SPAN = re.compile(r"(?<!`)`plan`(?!`)")


def _nonrecord(tree):
    return sorted(p for p in tree.files if not is_record(p))


def split_exempt(rid, tree, counts):
    """counts: {path: hits} over a row's population.  -> (the counted hits as
    [(n, path)], the exemptions' evidence lines, the stale entries).  Swept
    both ways: a hit outside EXEMPT counts, and an entry naming no tracked
    file, or a file its row no longer hits, is stale."""
    names = EXEMPT.get(rid, ())
    per = []
    for p, n in counts.items():
        if p in names:
            continue
        if n:
            per.append((n, p))
    ev, stale = [], []
    for p in names:
        n = counts.get(p, 0)
        if not tree.tracked(p):
            stale.append(p)
            ev.append(f"exempt by name: {p} -- STALE: not tracked")
        elif not n:
            stale.append(p)
            ev.append(f"exempt by name: {p} -- STALE: no hit")
        else:
            ev.append(f"exempt by name: {p} -- {n} hits, needed")
    return sorted(per, key=lambda x: (-x[0], x[1])), ev, stale


def _counted(per, stale):
    value = f"{sum(n for n, _p in per)} in {len(per)} files"
    if stale:
        value += f"; {len(stale)} stale exemption" + ("s" if len(stale) > 1 else "")
    return (PASS if not per and not stale else RED), value


def e16(tree, inp):
    counts, parts = {}, {}
    for p in _nonrecord(tree):
        if not p.endswith(".md"):
            continue
        t = tree.text(p) or ""
        a, b = len(E16_PATH.findall(t)), len(E16_SPAN.findall(t))
        counts[p], parts[p] = a + b, (a, b)
    per, exev, stale = split_exempt("E16", tree, counts)
    ev = [f"{n:>4}  {p}   (path {parts[p][0]}, `plan` {parts[p][1]})"
          for n, p in per] + exev
    verdict, value = _counted(per, stale)
    return verdict, value, ev


DRIVER_PATH = re.compile(r"^(.+?)/linux-2\.6\.30/drivers/(?:.+/)?"
                         r"(?:rtl819x-|rlxfw-)[^/]*\.c$")
INCLUDE = re.compile(r"^[ \t]*#[ \t]*include\b")


def drivers(tree):
    return sorted(p for p in tree.files if DRIVER_PATH.match(p))


def e17(tree, inp):
    drv = drivers(tree)
    if not drv:
        return UNMEASURED, "no driver found", [
            "no tracked */linux-2.6.30/drivers/**/rtl819x-*.c or rlxfw-*.c: "
            "an empty population passes nothing"]
    rows, none = [], []
    for p in drv:
        lines = (tree.text(p) or "").split("\n")
        first = next((i for i, ln in enumerate(lines, 1) if INCLUDE.match(ln)),
                     None)
        if first is None:
            none.append(p)
        else:
            rows.append((first, p))
    over = [(n, p) for n, p in rows if n > 60]
    ev = [f"{n:>5}  {p}" for n, p in sorted(rows, reverse=True)]
    ev += [f"  --   {p}: no #include line" for p in none]
    worst = max(rows)[0] if rows else None
    if over:
        return RED, f"{len(over)} of {len(drv)} over 60; worst {worst}", ev
    if none:
        return UNMEASURED, f"{len(none)} of {len(drv)} have no #include", ev
    return PASS, f"{len(drv)} drivers; worst {worst}", ev


def e18(tree, inp):
    drv = drivers(tree)
    if not drv:
        return UNMEASURED, "no kernel tree found", [
            "the kernel roots are found through E17's drivers, and there are none"]
    roots = sorted({DRIVER_PATH.match(p).group(1) + "/" for p in drv})
    pop = sorted(p for p in tree.files if p.endswith((".c", ".h"))
                 and p.startswith(tuple(roots) + ("src/",)))
    per = []
    for p in pop:
        t = tree.text(p) or ""
        emo = sum(1 for ch in t if is_emoji(ch))
        marks = sum(t.count(m) for m in E18_MARKS)
        if emo or marks:
            per.append((p, emo, marks))
    ev = [f"population: {len(pop)} .c/.h under {', '.join(roots)} and src/"]
    ev += [f"{p}   (emoji {e}, marks {m})" for p, e, m in per]
    return ((PASS if not per else RED),
            f"{len(per)} of {len(pop)} files", ev)


def e19(tree, inp):
    counts = {}
    for p in _nonrecord(tree):
        b = tree.data(p)
        if b is not None:
            counts[p] = len(E19_RE.findall(b))
    per, exev, stale = split_exempt("E19", tree, counts)
    ev = [f"{n:>4}  {p}" for n, p in per] + exev
    value = f"{len(per)} files ({sum(n for n, _p in per)} hits)"
    if stale:
        value += f"; {len(stale)} stale exemption" + ("s" if len(stale) > 1 else "")
    return (PASS if not per and not stale else RED), value, ev


def e20(tree, inp):
    t = _need(tree, "README.md")
    if t is None:
        return UNMEASURED, "README.md is not tracked", []
    n = t.count("7UjzFiAmzVs")
    return (PASS if n == 0 else RED), f"{n} occurrences", []


def e21(tree, inp):
    counts = {}
    for p in _nonrecord(tree):
        b = tree.data(p)
        if b is not None:
            counts[p] = len(E21_RE.findall(e21_text(b)))
    per, exev, stale = split_exempt("E21", tree, counts)
    ev = [f"{n:>4}  {p}" for n, p in per] + exev
    verdict, value = _counted(per, stale)
    return verdict, value, ev


class Row:
    def __init__(self, rid, title, target, fn, method, online=False,
                 waivable=False):
        self.rid, self.title, self.target, self.fn = rid, title, target, fn
        self.method, self.online, self.waivable = method, online, waivable


WORDS = ("a word is a whitespace-separated token holding a letter or a digit; "
         "each CJK ideograph or kana is one word, since CJK prose has no "
         "spaces; a token of punctuation or emoji alone is none. Removed "
         "first: HTML comments, link reference definitions, images and "
         "badges (no words), every link's URL and title (its text stays), "
         "the HTML tags of a fixed list; entities are decoded.")

ROWS = [
    Row("E1", "README.md lines", "<= 150", e1,
        "lines = '\\n'-terminated lines, plus one if the file does not end "
        "in '\\n'"),
    Row("E2", "README first-screen words", "<= 200", e2,
        "first screen = every line before the first level-2 ATX heading "
        "(' {0,3}##' then a space, a tab or the end of the line) outside "
        "fenced code; fence delimiter lines and ```mermaid bodies are not "
        "prose. " + WORDS),
    Row("E3", "README dates", "<= 1", e3,
        "matches of (?<![0-9])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9]) anywhere "
        "in README.md, code and URLs included"),
    Row("E4", "README status emoji", "= 0", e4,
        "occurrences in README.md of U+1F534, U+1F7E2, U+1F504, U+1F195, "
        "U+26A0 (with or without U+FE0F), U+2705, U+274C; other emoji are "
        "listed and not counted"),
    Row("E5", "README longest table cell", "<= 60 words", e5,
        "GFM tables outside fences: a delimiter row (cells ':?-+:?', at "
        "least one '|') under a header row of the same cell count; body rows "
        "run to a blank line, a heading, a fence or a '>'. A row splits on "
        "every '|' not escaped by a backslash, inside code spans too -- GFM "
        "renders it so; cells past the header's count are dropped, as GitHub "
        "drops them. Words as E2."),
    Row("E6", "README first screen has a diagram", ">= 1", e6,
        "in E2's first screen: a ```mermaid or ~~~mermaid fence (the info "
        "string GitHub draws, lower case) with a non-blank body, or an image "
        "-- '![alt](target)', '![alt][ref]' or "
        "<img src>, outside code spans. A target containing 'badge' or "
        "'shields.io' is a badge and does not count; a relative target must "
        "be tracked; an absolute URL is accepted unfetched."),
    Row("E7", "README build section", "<= 10 lines, links docs/build.md", e7,
        "an ATX heading of any level matching /build/i; its section runs to "
        "the next heading of the same or a higher level; its body holds <= 10 "
        "non-blank lines and a link that reaches the tracked file "
        "docs/build.md (links resolved as E15)"),
    Row("E8", "LOG.md size", "<= 1,000,000 bytes", e8,
        "the size in bytes of LOG.md in the working tree"),
    Row("E8w", "root .md shown by GitHub", "0 not shown", e8w,
        "for every root-level tracked .md, its saved blob page (--blob-html), "
        "read through the page's react-app JSON: the page must be for that "
        "path and for HEAD (refInfo.currentOid). blob.large=true is GitHub's "
        "'Sorry about that, but we can't show files that are this big'. The "
        "phrase on a page with large=false is explained only by the file's "
        "own text; otherwise the page is unexplained and the row UNMEASURED.",
        online=True),
    Row("E9", "RUNSHEET.md off the root", "absent at root", e9,
        "no tracked path at the repository root is RUNSHEET.md (any case)"),
    Row("E10", "CHANGELOG.md size", "<= 300 lines, sections <= 40", e10,
        "lines as E1; a section runs from its '## ' heading to the line "
        "before the next level-1 or level-2 heading outside fences, or the "
        "end of the file. No '## ' section is UNMEASURED."),
    Row("E11", "PROGRESS.md lines", "<= 200", e11,
        "lines as E1 (docsize owns its byte budget)"),
    Row("E12", "GitHub primary language", "= C", e12,
        "--gh-json: primaryLanguage.name", online=True),
    Row("E13", "GitHub topics", ">= 8", e13,
        "--gh-json: the entries of repositoryTopics (null reads 0)",
        online=True),
    Row("E14", "CI builds code", "host suites wired", e14,
        "every tracked .yml and .yaml directly under .github/workflows/ (GitHub "
        "reads no subdirectory), each read as block YAML; its `on:` is not "
        "read, so a workflow never triggered still counts. Every run: of every "
        "step whose job and step `if:` is not literally false; comment lines "
        "dropped, continuations joined, split on && || ; | & ( ), `cd DIR` "
        "and working-directory followed. Userspace: make in src (-C, "
        "--directory or cd) with goal `test`. rlxboot: make in src/rlxboot "
        "with goal `hosttest`, make in src with goal `rlxboot` while "
        "src/Makefile's rlxboot recipe names hosttest, or "
        "src/rlxboot/test/run-host-tests.sh run directly. A make at the top "
        "is followed into the tracked top-level Makefile's recipes."),
    Row("E14w", "CI log shows both suites passed", "both lines", e14w,
        "--ci-log, a log naming HEAD's full sha, holding as whole lines -- "
        "after stripping a `gh run view --log` 'job<TAB>step<TAB>' prefix, a "
        "timestamp and colour codes -- src/Makefile's 'test: N of N program "
        "suites ran and passed' (N = the words of PROGS) and "
        "run-host-tests.sh's 'host suite: PASS'. Both sources are re-read: if "
        "either echo changed, the row is UNMEASURED.", online=True),
    Row("E15", "docs/README.md reaches every doc", "0 unreachable in 2 hops",
        e15,
        "relative links in tracked .md files (inline, reference, <a href>; "
        "images and links in code are not links; #anchor and ?query "
        "stripped; percent-decoded; a leading '/' is the repository top); a "
        "link to a tracked directory reaches its README.md. Breadth-first "
        "from docs/README.md, 2 hops. A hop may leave docs/README.md, a "
        "non-record .md under docs/ or notes/, or a README.md under docs/; "
        "root files and records are not stepping stones -- at fb5a5d17 "
        "GitHub showed SPEC.md, RUNSHEET.md and docs/GATE-RESULTS.md as "
        "source and LOG.md not at all, so a reader cannot follow their "
        "links. Population: every tracked .md under docs/ and notes/, "
        "records included."),
    Row("E16", "plan/ references", "= 0", e16,
        "non-record tracked .md files: the path 'plan/' at the start of a "
        "path token, optionally after './' or '../' "
        "((?<![\\w./\\\\-])(?:\\.{1,2}/)*plan/ -- 'upstream/plan/' and "
        "'planned' do not match), plus the code span `plan`. Exempt by name, "
        "needing a hit or the row is RED: " + ", ".join(EXEMPT["E16"])
        + " (the 2026-10-09 ruling: its table describes the private "
        "directory)."),
    Row("E17", "driver header length", "first #include <= 60", e17,
        "drivers = tracked paths */linux-2.6.30/drivers/**/rtl819x-*.c and "
        "rlxfw-*.c, found by pattern and not by directory; per driver the "
        "number of its first line matching ^[ \\t]*#[ \\t]*include. No driver "
        "is UNMEASURED.", waivable=True),
    Row("E18", "emoji and marks in C", "= 0 files", e18,
        "tracked .c/.h under each kernel root (the path before "
        "'/linux-2.6.30/' of E17's drivers) and under src/, holding an emoji "
        "(U+1F000-U+1FAFF, U+FE0F, U+26A0, the BMP Emoji_Presentation code "
        "points) or 量/讀/推. No driver means no kernel root: UNMEASURED.",
        waivable=True),
    Row("E19", "personal paths", "= 0 files", e19,
        "non-record tracked files, their bytes (a symlink's target): '"
        + HOME_KEY + "' not followed by [A-Za-z0-9_], or '" + WIN_USER
        + "' not preceded by [A-Za-z0-9_] nor followed by a digit. Exempt by "
        "name, needing a hit or the row is RED: " + ", ".join(EXEMPT["E19"])
        + " (the 2026-10-09 ruling: its table defines $FWRE_WORK's path)."),
    Row("E20", "README video is not v0.2's", "= 0", e20,
        "occurrences of 7UjzFiAmzVs in README.md"),
    Row("E21", "framing terms", "= 0", e21,
        "non-record tracked files decoded as UTF-8, NFC-normalised and "
        "case-folded: " + E21_RE.pattern + " -- 'resume', 'presume' "
        "and 'RESUME' carry no accent and do not match. Exempt by name, each "
        "needing a hit or the row is RED: " + ", ".join(E21_EXEMPT) + "."),
]
ROW = {r.rid: r for r in ROWS}
ONLINE = [r.rid for r in ROWS if r.online]
WAIVABLE = [r.rid for r in ROWS if r.waivable]


class Result:
    def __init__(self, rid, verdict, value, evidence):
        self.rid, self.verdict, self.value = rid, verdict, value
        self.evidence = list(evidence)


def measure(tree: Tree, inp: Inputs):
    out = {}
    for row in ROWS:
        if row.online and inp.offline:
            out[row.rid] = Result(row.rid, UNMEASURED, "not measured (--offline)", [])
            continue
        v, val, ev = row.fn(tree, inp)
        if v not in (PASS, RED, UNMEASURED):
            raise AssertionError(f"{row.rid} returned {v!r}")
        out[row.rid] = Result(row.rid, v, val, ev)
    return out


def decide(results, waivers, offline):
    """(final verdicts, notes, ok, red, unmeasured online, unmeasured offline,
    stale waivers).  `ok` is check's exit-0 condition."""
    final, notes, stale = {}, [], []
    for row in ROWS:
        v = results[row.rid].verdict
        if row.rid in waivers:
            if v == RED:
                v = WAIVED
                notes.append(f"{row.rid} WAIVED (measured RED: "
                             f"{results[row.rid].value}) -- {waivers[row.rid]}")
            elif v == PASS:
                stale.append(row.rid)
                notes.append(f"{row.rid} STALE WAIVER: the row measures PASS; "
                             f"remove --waive {row.rid}")
            else:
                notes.append(f"{row.rid} waiver not applied: the row was not "
                             f"measured, and a waiver is for a measured RED")
        final[row.rid] = v
    red = [r for r in final if final[r] == RED]
    un_on = [r for r in final if final[r] == UNMEASURED and ROW[r].online]
    un_off = [r for r in final if final[r] == UNMEASURED and not ROW[r].online]
    ok = not red and not stale and not un_off and (offline or not un_on)
    return final, notes, ok, red, un_on, un_off, stale


def parse_waivers(specs):
    w = {}
    for s in specs or []:
        rid, sep, reason = s.partition("=")
        rid, reason = rid.strip(), reason.strip()
        if not sep or not reason:
            _fail(f"--waive {s!r}: write --waive ID=REASON, and the reason is "
                  f"not optional")
        if rid not in ROW:
            _fail(f"--waive {rid}: no such row")
        if not ROW[rid].waivable:
            _fail(f"--waive {rid}: not waivable -- the DoD allows a waiver on "
                  f"{' and '.join(WAIVABLE)} only")
        if rid in w:
            _fail(f"--waive {rid} given twice")
        w[rid] = reason
    return w


def print_table(results, final, out):
    print(f"  {'id':<5} {'verdict':<10} {'value':<40} target", file=out)
    for row in ROWS:
        r = results[row.rid]
        print(f"  {row.rid:<5} {final[row.rid]:<10} {r.value:<40} {row.target}",
              file=out)


def _wrap(text, width=76, indent="              "):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return ("\n" + indent).join(lines)


def header(tree, out):
    print(f"entrycheck {TOOL_VERSION} -- gate P5e's definition of done", file=out)
    print(f"  root       {tree.root}", file=out)
    print(f"  HEAD       {tree.head}", file=out)
    print("  tree       " + ("clean against HEAD (tracked files)" if not tree.dirty
                             else f"{len(tree.dirty)} tracked path(s) differ "
                                  f"from HEAD: the offline rows read the "
                                  f"working tree, the online rows HEAD"),
          file=out)
    print(f"  tracked    {len(tree.files):,} files read from the working tree; "
          f"{len(tree.gitlinks)} gitlink(s) never read "
          f"({', '.join(tree.gitlinks) or 'none'})", file=out)
    nrec = sum(1 for p in tree.files if is_record(p))
    print(f"  records    {RECORD_SET_TEXT}", file=out)
    print(f"             {nrec:,} tracked files are records; "
          f"{len(tree.files) - nrec:,} are not", file=out)


def cmd_report(args) -> int:
    tree, inp, waivers = _setup(args)
    results = measure(tree, inp)
    final, notes, ok, red, un_on, un_off, stale = decide(results, waivers,
                                                         inp.offline)
    out = sys.stdout
    header(tree, out)
    print(file=out)
    print_table(results, final, out)
    print(file=out)
    for row in ROWS:
        r = results[row.rid]
        print(f"{row.rid}  {row.title} -- {final[row.rid]}"
              + ("   (online)" if row.online else ""), file=out)
        print(f"    value     {r.value}", file=out)
        print(f"    target    {row.target}", file=out)
        print(f"    measured  {_wrap(row.method)}", file=out)
        for e in r.evidence:
            print(f"    evidence  {e}", file=out)
        print(file=out)
    _summary(final, notes, ok, red, un_on, un_off, inp.offline, out)
    return 0


def _summary(final, notes, ok, red, un_on, un_off, offline, out):
    counts = {v: sum(1 for x in final.values() if x == v)
              for v in (PASS, RED, WAIVED, UNMEASURED)}
    print(f"{len(final)} rows: " + ", ".join(f"{counts[v]} {v}"
                                            for v in (PASS, RED, WAIVED, UNMEASURED)),
          file=out)
    if red:
        print(f"RED: {', '.join(red)}", file=out)
    for n in notes:
        print(n, file=out)
    unmeasured = un_on + un_off
    if unmeasured:
        print(f"{len(unmeasured)} rows not measured: {', '.join(unmeasured)}",
              file=out)
        if un_on and offline:
            print(f"  --offline: {', '.join(un_on)} are online rows and do not "
                  f"decide", file=out)
        if un_off:
            print(f"  {', '.join(un_off)}: offline, and --offline never excuses "
                  f"an offline row", file=out)


def cmd_check(args) -> int:
    tree, inp, waivers = _setup(args)
    results = measure(tree, inp)
    final, notes, ok, red, un_on, un_off, stale = decide(results, waivers,
                                                         inp.offline)
    out = sys.stdout
    header(tree, out)
    print(file=out)
    print_table(results, final, out)
    print(file=out)
    _summary(final, notes, ok, red, un_on, un_off, inp.offline, out)
    print(f"check: {'PASS' if ok else 'FAIL'}" + ("" if ok else " (exit 1)"),
          file=out)
    return 0 if ok else 1


def _setup(args):
    waivers = parse_waivers(args.waive)
    if args.offline:
        given = [n for n, v in (("--gh-json", args.gh_json),
                                ("--blob-html", args.blob_html),
                                ("--ci-log", args.ci_log)) if v]
        if given:
            _fail(f"--offline and {', '.join(given)} contradict: --offline "
                  f"decides on the offline rows only, and an online input it "
                  f"would have to ignore is refused instead")
    if args.blob_html and not os.path.isdir(args.blob_html):
        _fail(f"--blob-html {args.blob_html} is not a directory")
    for flag, v in (("--gh-json", args.gh_json), ("--ci-log", args.ci_log)):
        if v and not os.path.isfile(v):
            _fail(f"{flag} {v} is not a file")
    tree = Tree(args.root)
    return tree, Inputs(args.gh_json, args.blob_html, args.ci_log,
                        args.offline), waivers


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def _w(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    with open(p, "wb") as fh:
        fh.write(data)
    return p


class Fixtures:
    """Throwaway repositories whose git runs hermetic: no inherited GIT_*
    variable, an empty global config, no system config."""

    def __init__(self, td):
        self.td, self.k = td, 0
        cfg = _w(td, "empty.gitconfig", b"")
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=cfg, GIT_CONFIG_NOSYSTEM="1",
                   GIT_AUTHOR_NAME="entrycheck", GIT_AUTHOR_EMAIL="e@invalid",
                   GIT_COMMITTER_NAME="entrycheck",
                   GIT_COMMITTER_EMAIL="e@invalid")
        self.env = env

    def git(self, root, *args):
        r = subprocess.run(["git", "-C", root] + list(args),
                           capture_output=True, env=self.env)
        if r.returncode:
            raise RuntimeError(f"fixture git {args[0]}: "
                               + r.stderr.decode("utf-8", "replace").strip())
        return r.stdout.decode()

    def repo(self, files):
        self.k += 1
        root = os.path.join(self.td, f"repo{self.k}")
        os.makedirs(root)
        for rel, data in files.items():
            if data is not None:
                _w(root, rel, data)
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "fixture")
        return root

    def head(self, root):
        return self.git(root, "rev-parse", "HEAD").strip()

    def inputs(self, root, name="in", lang="C", topics=8, pages=None, log=None):
        """Online inputs for `root`, all of them passing unless overridden."""
        d = os.path.join(self.td, f"{name}{self.k}")
        os.makedirs(d, exist_ok=True)
        head = self.head(root)
        gh = {"primaryLanguage": {"name": lang} if lang else None,
              "repositoryTopics": [{"name": f"t{i}"} for i in range(topics)]}
        ghp = _w(d, "gh.json", json.dumps(gh))
        bd = os.path.join(d, "blob")
        os.makedirs(bd, exist_ok=True)
        names = sorted(f for f in os.listdir(root) if f.endswith(".md"))
        for nm in names:
            spec = (pages or {}).get(nm, {})
            if spec is None:
                continue
            with open(os.path.join(root, nm), encoding="utf-8") as fh:
                own = fh.read()
            _w(bd, nm, fake_page(nm, spec.get("oid", head),
                                 spec.get("large", False),
                                 spec.get("banner"), own[:400]))
        lg = _w(d, "ci.log", log if log is not None else fake_log(head))
        return Inputs(ghp, bd, lg)


def fake_page(path, oid, large, banner=None, body=""):
    """A blob page with the structure GitHub served on 2026-10-09: the title,
    the react-app embedded JSON, the too-large banner when large, and the
    server-rendered article."""
    payload = {"payload": {
        "codeViewBlobRoute": {"richText": None if large else
                              "<article class=\"markdown-body\">x</article>",
                              "richTextTruncated": False},
        "codeViewLayoutRoute": {"path": path,
                                "refInfo": {"name": oid, "currentOid": oid}},
        "codeViewBlobLayoutRoute": {"blob": {"large": large,
                                             "displayName": path},
                                    "refInfo": {"currentOid": oid}}}}
    if banner is None:
        banner = large
    ban = ("<div class=\"BlobContent-module__tooLargeError__n0H_w\"><a>View "
           "raw</a><p>(Sorry about that, but we can\u2019t show files that "
           "are this big right now.)</p></div>") if banner else ""
    art = "" if large else ("<article class=\"markdown-body\"><p>"
                            + html.escape(body) + "</p></article>")
    js = json.dumps(payload).replace("<", "\\u003c")
    return (f"<!DOCTYPE html><html><head><title>router-customFW/{path} at {oid}"
            f" \u00b7 {REPO_SLUG} \u00b7 GitHub</title></head><body>"
            f"<script type=\"application/json\" data-target=\"react-app."
            f"embeddedData\">{js}</script>{ban}{art}</body></html>")


def fake_log(head, progs=2, userspace=True, hostsuite=True, raw=False):
    ts = "2026-10-09T10:00:0{}.1234567Z "
    rows = [("build", "Set up job", "Current runner version: '2.329.0'"),
            ("build", "Run actions/checkout@v4",
             "[command]/usr/bin/git log -1 --format='%H'"),
            ("build", "Run actions/checkout@v4", f"'{head}'"),
            ("build", "userspace", "===== test: init =====")]
    if userspace:
        rows.append(("build", "userspace",
                     f"test: {progs} of {progs} program suites ran and passed"))
    if hostsuite:
        rows.append(("build", "rlxboot", "host suite: PASS"))
    if raw:
        return "".join(ts.format(i) + t + "\r\n" for i, (_j, _s, t) in enumerate(rows))
    return "".join(f"{j}\t{s}\t" + ts.format(i) + t + "\n"
                   for i, (j, s, t) in enumerate(rows))


FILL = "word"


def fx_readme(first=187, cjk="量測讀取", cell=60, build_lines=10,
              build_head="## Build", dates=1, extra_lines=0, mermaid=True,
              extra_first="", extra_notes="", cell_row=None, below=""):
    lines = ["# Demo", "",
             "[![CI](https://img.shields.io/badge/ci-green.svg)]"
             "(https://example.invalid/ci) <!-- five words are not counted -->",
             "", f"{cjk} is measured.", "",
             "Read [the build guide](docs/build.md \"Build\") first, &amp; "
             "<b>then</b> \U0001F3AC.", ""]
    if mermaid:
        lines += ["```mermaid", "graph LR", "  a[source] --> b[image]", "```", ""]
    lines += [" ".join([FILL] * first) + extra_first, ""]
    lines += [build_head, "", "Build it as [docs/build.md](docs/build.md) says."]
    lines += [f"step {i}" for i in range(2, build_lines + 1)]
    lines += ["", "## Table", "", "| Cell | Note |", "|---|---|",
              cell_row if cell_row is not None
              else "| " + " ".join([FILL] * cell) + " | short |", ""]
    lines += ["## Notes", "", "Released " + " and ".join(
        ["2026-10-09"] * dates) + "." + extra_notes, ""]
    if below:
        lines += below.split("\n")
    while len(lines) < 150 + extra_lines:
        lines.append("pad")
    return "\n".join(lines) + "\n"


def fx_changelog(pre=20, sects=(40,) * 7, headed=True):
    lines = ["# Changelog"] + [f"preamble {i}" for i in range(1, pre)]
    for k, n in enumerate(sects):
        lines.append(f"## v0.{k}" if headed else f"### v0.{k}")
        lines += [f"- item {i}" for i in range(1, n)]
    return "\n".join(lines) + "\n"


CI_PASS = """\
name: ci
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 1 }
      - name: userspace
        if: "${{ !cancelled() }}"
        run: make -C src host test O=$RUNNER_TEMP/u 2>&1 | tee u.out; exit "${PIPESTATUS[0]}"
      - name: rlxboot
        run: |
          # the loader's host suite
          make -C src/rlxboot hosttest \\
            O=$RUNNER_TEMP/r
"""

SRC_MAKEFILE = """\
PROGS   := init cfgstore

test:
\t@set -e; n=0; for p in $(PROGS); do \\
\t   n=$$((n+1)); \\
\t done; \\
\t echo "test: $$n of $(words $(PROGS)) program suites ran and passed"

rlxboot:
\t@$(MAKE) --no-print-directory -C $(HERE)rlxboot hosttest O=$(O)/rlxboot
"""


def fx_log(size=None):
    """LOG.md: a record carrying an E19 and an E21 hit, padded to `size`
    bytes when given (E8's boundary cases only: a 1 MB file in every
    fixture costs a tenth of a second each)."""
    log = ("# Log\n\n" + HOME_KEY + "/fwre-work is a record's business, and so "
           "is a recruit.\n")
    if size is not None:
        log += "x" * (size - len(log.encode()) - 1) + "\n"
    return log


def base_files():
    log = fx_log()
    f = {
        "README.md": fx_readme(),
        "LOG.md": log,
        "CHANGELOG.md": fx_changelog(),
        "PROGRESS.md": "".join(f"progress {i}\n" for i in range(1, 201)),
        "docs/README.md": ("# Docs\n\n- [build](build.md)\n- [notes](../notes/)\n"
                           "- [history](history/)\n"),
        "docs/build.md": "# Build\n\nmake -C src host test O=/tmp/o\n",
        "docs/history/README.md": "# History\n\n- [old](old.md)\n",
        "docs/history/old.md": "# Old\n\nan old record, plan/ and all\n",
        "notes/README.md": "# Notes\n\n- [a](a.md#top)\n",
        "notes/a.md": ("# A\n\nplanned work, upstream/plan/README.md and "
                       "subplan/x are not references; resume, presume, "
                       "RESUME and resumed are technical words.\n"),
        ".github/workflows/ci.yml": CI_PASS,
        "src/Makefile": SRC_MAKEFILE,
        "src/rlxboot/test/run-host-tests.sh": ("#!/bin/sh\nset -e\n"
                                               "echo \"host suite: PASS\"\n"),
        "kernel/linux-2.6.30/drivers/net/rtl819x-nic.c":
            "".join(f"/* header {i} */\n" for i in range(1, 60))
            + "#include <linux/kernel.h>\n",
        "kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c":
            "/* x */\n\n#include <linux/random.h>\n",
        "kernel/linux-2.6.30/include/rlxfw.h":
            "/* \u00a7 4.1 \u2192 \u2264 \u00d7 \u2460: not emoji */\n",
        "other/drivers/rtl819x-fake.c":
            "".join("/* */\n" for _ in range(99)) + "#include <x.h>\n",
        "src/init/main.c": "int main(void) { return 0; }\n",
        "tools/fake.c": "/* \U0001F534 outside every population */\n",
        "tools/fake.sh": ("#!/bin/sh\n# " + HOME_KEY + "s and Mon" + WIN_USER
                          + " are not hits\n"),
        "qemu/README.md": "# qemu\n",
        "qemu/2026-08-31b/probe3.txt": "ran from " + HOME_KEY + "/fwre-work\n",
        "tools/entrycheck.py": "# carries the pattern: hiring\n",
        "tools/test-entrycheck-mutants.py": "# carries the pattern: r\u00e9sum\u00e9\n",
        # Exempt from E16 and E19 by name, and carrying one hit of each.
        "CLAUDE.md": ("# CLAUDE.md\n\n| | |\n|---|---|\n| `plan/` | private, "
                      "gitignored |\n| `$FWRE_WORK` | " + HOME_KEY
                      + "/fwre-work |\n"),
    }
    return f


def self_test() -> int:
    ok = fail = 0

    def check_(cid, desc, cond, detail=""):
        nonlocal ok, fail
        if cond:
            print(f"  ok    {cid} {desc}")
            ok += 1
        else:
            print(f"  FAIL  {cid} {desc}" + (f": {detail}" if detail else ""))
            fail += 1

    print(f"entrycheck {TOOL_VERSION} self-test")
    print()
    try:
        r = subprocess.run(["git", "--version"], capture_output=True)
        have_git = r.returncode == 0
    except OSError:
        have_git = False
    if not have_git:
        print("  FAIL  G0 git is not available: every fixture is a repository")
        print()
        print("  0 passed, 1 failed")
        return 1

    with tempfile.TemporaryDirectory(prefix="entrycheck-") as td:
        fx = Fixtures(td)
        base = base_files()

        def run(files, inp=None, offline=False):
            root = fx.repo(files)
            if inp is None:
                i = Inputs(offline=offline)
            else:
                i = inp(root)
            return root, measure(Tree(root), i)

        def verdict_case(cid, desc, rid, want, files, inp=None):
            _root, res = run(files, inp)
            r = res[rid]
            check_(cid, f"{desc} -> {want}", r.verdict == want,
                   f"got {r.verdict} ({r.value}; "
                   + "; ".join(r.evidence[:3]) + ")")
            return r

        # ---- the base: every row at its boundary, every row PASS ----------
        broot = fx.repo(base)
        binp = fx.inputs(broot, "base")
        btree = Tree(broot)
        bres = measure(btree, binp)
        for row in ROWS:
            r = bres[row.rid]
            where = ("E8b holds its boundary" if row.rid == "E8" else
                     "at the row's boundary where it has one")
            check_(f"{row.rid}p", f"the base fixture reads PASS ({row.target}; "
                   f"{where})", r.verdict == PASS,
                   f"got {r.verdict} ({r.value}; " + "; ".join(r.evidence[:3]) + ")")

        def files_with(path, data):
            f = dict(base)
            f[path] = data
            return f

        def without(*paths):
            return {k: v for k, v in base.items() if k not in paths}

        def on_base(cid, desc, rid, want, **kw):
            i = fx.inputs(broot, cid, **kw)
            r = measure(btree, i)[rid]
            check_(cid, f"{desc} -> {want}", r.verdict == want,
                   f"got {r.verdict} ({r.value}; " + "; ".join(r.evidence[:3]) + ")")

        # ---- E1-E7, E20: README --------------------------------------------
        verdict_case("E1r", "README.md of 151 lines", "E1", RED,
                     files_with("README.md", fx_readme(extra_lines=1)))
        verdict_case("E2r", "a first screen of 201 words", "E2", RED,
                     files_with("README.md", fx_readme(first=188)))
        verdict_case("E2c", "201 words only because each CJK ideograph is a word",
                     "E2", RED, files_with("README.md", fx_readme(cjk="量測讀取推")))
        verdict_case("E2h", "200 words beside an HTML comment, a link title and "
                     "an image's alt text in the first screen", "E2", PASS,
                     files_with("README.md", fx_readme(
                         first=186, extra_first=" <!-- ten more words that are "
                         "hidden from every reader of the page --> "
                         "[x](https://example.invalid/a \"a title of words\") "
                         "![alt text words](docs/arch.svg)")))
        verdict_case("E3r", "two dates", "E3", RED,
                     files_with("README.md", fx_readme(dates=2)))
        verdict_case("E4r", "one U+2705", "E4", RED,
                     files_with("README.md", fx_readme(extra_notes=" \u2705")))
        verdict_case("E4b", "one U+26A0 without U+FE0F", "E4", RED,
                     files_with("README.md", fx_readme(extra_notes=" \u26A0 note")))
        verdict_case("E5r", "a 61-word cell", "E5", RED,
                     files_with("README.md", fx_readme(cell=61)))
        verdict_case("E5e", "a 61-word cell holding an escaped pipe", "E5", RED,
                     files_with("README.md", fx_readme(
                         cell_row="| " + " ".join([FILL] * 30) + " \\| "
                         + " ".join([FILL] * 31) + " | short |")))
        verdict_case("E5c", "a pipe inside a code span splits the cell, as GFM "
                     "renders it", "E5", PASS,
                     files_with("README.md", fx_readme(
                         cell_row="| " + " ".join([FILL] * 30) + " `a|b` "
                         + " ".join([FILL] * 30) + " | short |")))
        verdict_case("E5x", "a 61-word cell past the header's cell count is "
                     "dropped, as GitHub drops it", "E5", PASS,
                     files_with("README.md", fx_readme(
                         cell_row="| a | b | " + " ".join([FILL] * 61) + " |")))
        # The parser's control: rows that start with '|' and no table it
        # recognises (no delimiter row) must not read as "no long cell".
        verdict_case("E5u", "lines starting with '|' and no table recognised",
                     "E5", UNMEASURED, files_with("README.md", fx_readme().replace(
                         "| Cell | Note |\n|---|---|\n", "| Cell | Note |\n")))
        verdict_case("E6r", "no diagram and a badge as the only image", "E6", RED,
                     files_with("README.md", fx_readme(mermaid=False, first=187)))
        f = files_with("README.md", fx_readme(mermaid=False,
                                              extra_first=" ![arch](docs/arch.svg)"))
        f["docs/arch.svg"] = "<svg xmlns=\"http://www.w3.org/2000/svg\"/>\n"
        verdict_case("E6i", "an image whose relative target is tracked", "E6",
                     PASS, f)
        verdict_case("E6m", "an image whose relative target is not tracked",
                     "E6", RED, files_with("README.md", fx_readme(
                         mermaid=False, extra_first=" ![arch](docs/arch.svg)")))
        verdict_case("E6h", "a mermaid fence below the first `## `", "E6", RED,
                     files_with("README.md", fx_readme(
                         mermaid=False, below="```mermaid\ngraph LR\n  a --> b\n```")))
        f = files_with("README.md", fx_readme(
            mermaid=False, extra_first=" <img src=\"docs/arch.svg\" width=\"600\">"))
        f["docs/arch.svg"] = "<svg xmlns=\"http://www.w3.org/2000/svg\"/>\n"
        verdict_case("E6t", "an HTML <img> with a tracked target", "E6", PASS, f)
        verdict_case("E7r", "no heading matching /build/i", "E7", RED,
                     files_with("README.md", fx_readme(build_head="## Make")))
        verdict_case("E7n", "a build section of 11 non-blank lines", "E7", RED,
                     files_with("README.md", fx_readme(build_lines=11)))
        verdict_case("E7t", "a link naming docs/build.md, which is not tracked",
                     "E7", RED, without("docs/build.md"))
        verdict_case("E20r", "README carries the v0.2 replay's video id", "E20",
                     RED, files_with("README.md", fx_readme(
                         extra_notes=" https://youtu.be/7UjzFiAmzVs")))
        verdict_case("E1u", "README.md not tracked", "E1", UNMEASURED,
                     without("README.md"))

        # ---- E8-E11: sizes -------------------------------------------------
        verdict_case("E8b", "LOG.md of exactly 1,000,000 bytes", "E8", PASS,
                     files_with("LOG.md", fx_log(1_000_000)))
        verdict_case("E8r", "LOG.md of 1,000,001 bytes", "E8", RED,
                     files_with("LOG.md", fx_log(1_000_001)))
        verdict_case("E9r", "RUNSHEET.md at the root", "E9", RED,
                     files_with("RUNSHEET.md", "# Runsheet\n"))
        f = files_with("docs/history/RUNSHEET.md", "# Runsheet\n")
        verdict_case("E9m", "RUNSHEET.md moved under docs/history/", "E9", PASS, f)
        verdict_case("E10r", "CHANGELOG.md of 301 lines", "E10", RED,
                     files_with("CHANGELOG.md", fx_changelog(pre=21)))
        verdict_case("E10s", "one CHANGELOG section of 41 lines, 300 in all",
                     "E10", RED, files_with("CHANGELOG.md", fx_changelog(
                         pre=19, sects=(40,) * 6 + (41,))))
        verdict_case("E10u", "a CHANGELOG with no `## ` section", "E10",
                     UNMEASURED, files_with("CHANGELOG.md",
                                            fx_changelog(headed=False)))
        verdict_case("E11r", "PROGRESS.md of 201 lines", "E11", RED,
                     files_with("PROGRESS.md", base["PROGRESS.md"] + "one more\n"))

        # ---- E8w: GitHub's blob pages ---------------------------------------
        on_base("E8wr", "LOG.md's page says large, with the banner", "E8w", RED,
                pages={"LOG.md": {"large": True}})
        on_base("E8wl", "LOG.md's page says large, with no banner", "E8w", RED,
                pages={"LOG.md": {"large": True, "banner": False}})
        on_base("E8wu", "CHANGELOG.md's page missing", "E8w", UNMEASURED,
                pages={"CHANGELOG.md": None})
        on_base("E8wo", "a page of another commit", "E8w", UNMEASURED,
                pages={"PROGRESS.md": {"oid": "0" * 40}})
        on_base("E8wb", "the banner on a large=false page the file does not "
                "explain", "E8w", UNMEASURED,
                pages={"README.md": {"banner": True}})
        qf = files_with("README.md", fx_readme(
            extra_notes=" GitHub says Sorry about that for big files."))
        qroot = fx.repo(qf)
        qi = fx.inputs(qroot, "E8wq", pages={"README.md": {"banner": True}})
        r = measure(Tree(qroot), qi)["E8w"]
        check_("E8wq", "the phrase on a large=false page that the file itself "
               "carries -> PASS", r.verdict == PASS,
               f"got {r.verdict} ({r.value}; " + "; ".join(r.evidence) + ")")

        # ---- E12/E13: gh repo view ------------------------------------------
        on_base("E12r", "primaryLanguage Python", "E12", RED, lang="Python")
        on_base("E12n", "primaryLanguage null", "E12", RED, lang=None)
        on_base("E13r", "7 topics", "E13", RED, topics=7)
        d = os.path.join(td, "ghjson")
        os.makedirs(d)
        p = _w(d, "bom.json", b"\xef\xbb\xbf" + json.dumps(
            {"primaryLanguage": {"name": "C"}, "repositoryTopics": None}).encode())
        r = measure(btree, Inputs(gh_json=p))
        check_("E13n", "repositoryTopics null, behind a UTF-8 BOM -> RED, and "
               "E12 still reads C", r["E13"].verdict == RED
               and r["E12"].verdict == PASS,
               f"E13 {r['E13'].verdict} {r['E13'].value}, E12 {r['E12'].verdict}")
        p = _w(d, "nolang.json", json.dumps({"repositoryTopics": []}))
        r = measure(btree, Inputs(gh_json=p))
        check_("E12u", "a gh JSON without primaryLanguage -> UNMEASURED",
               r["E12"].verdict == UNMEASURED, f"got {r['E12'].verdict}")
        p = _w(d, "other.json", json.dumps({"nameWithOwner": "someone/else",
                                            "primaryLanguage": {"name": "C"}}))
        r = measure(btree, Inputs(gh_json=p))
        check_("E12o", "a gh JSON of another repository -> UNMEASURED",
               r["E12"].verdict == UNMEASURED, f"got {r['E12'].verdict}")

        # ---- E14: the workflow ----------------------------------------------
        verdict_case("E14r", "a workflow that runs no rlxboot hosttest", "E14",
                     RED, files_with(".github/workflows/ci.yml",
                                     CI_PASS.split("      - name: rlxboot")[0]))
        # The command sits in a trailing comment AFTER a `;`: read without
        # comment handling, `;` would split it off as a command of its own.
        verdict_case("E14c", "the rlxboot make only inside a trailing shell "
                     "comment, after a `;`", "E14", RED,
                     files_with(".github/workflows/ci.yml", CI_PASS.replace(
                         "          make -C src/rlxboot hosttest \\\n"
                         "            O=$RUNNER_TEMP/r\n",
                         "          true  # off for now; make -C src/rlxboot "
                         "hosttest O=x\n")))
        verdict_case("E14f", "the userspace step under `if: false`", "E14", RED,
                     files_with(".github/workflows/ci.yml", CI_PASS.replace(
                         "        if: \"${{ !cancelled() }}\"\n",
                         "        if: ${{ false }}\n")))
        f = files_with(".github/workflows/ci.yml", CI_PASS.replace(
            "make -C src host test O=$RUNNER_TEMP/u", "make ci-host O=/tmp/u")
            .split("      - name: rlxboot")[0])
        f["Makefile"] = ("ci-host: userspace loader\n\nuserspace:\n"
                         "\t$(MAKE) -C src host test O=$(O)/u\n\nloader:\n"
                         "\t@$(MAKE) -C src rlxboot O=$(O)/r\n")
        verdict_case("E14m", "a top-level Makefile goal whose prerequisites run "
                     "both", "E14", PASS, f)
        verdict_case("E14n", "a `run:` whose command sits on the line under it",
                     "E14", PASS, files_with(
                         ".github/workflows/ci.yml",
                         "jobs:\n  b:\n    steps:\n      - run:\n          make -C "
                         "src host test\n          O=/tmp/o\n      - run: make -C "
                         "src/rlxboot hosttest O=/tmp/r\n"))
        verdict_case("E14d", "`cd src && make test` and run-host-tests.sh run "
                     "directly", "E14", PASS, files_with(
                         ".github/workflows/ci.yml",
                         "jobs:\n  b:\n    steps:\n      - run: cd src && make "
                         "test O=/tmp/o\n      - run: sh "
                         "src/rlxboot/test/run-host-tests.sh . gcc clang /tmp/h\n"))
        verdict_case("E14g", "make in src with goal rlxboot while src/Makefile's "
                     "rlxboot recipe does not name hosttest", "E14", RED,
                     dict(files_with(".github/workflows/ci.yml",
                                     "jobs:\n  b:\n    steps:\n      - run: make "
                                     "-C src host test rlxboot O=/tmp/o\n"),
                          **{"src/Makefile": SRC_MAKEFILE.replace(
                              " hosttest O=$(O)/rlxboot", " payload")}))

        # ---- E14 reads every workflow, not ci.yml alone (P5e-4) -------------
        ci_none = CI_PASS.split("      - name: userspace")[0]
        wf_rlx = ci_none + "      - name: rlxboot" + CI_PASS.split(
            "      - name: rlxboot")[1]

        def with_wf(path, data, ci=ci_none):
            f = files_with(".github/workflows/ci.yml", ci)
            f[path] = data
            return f
        verdict_case("E14b", "ci.yml runs neither suite and build.yml runs "
                     "both", "E14", PASS,
                     with_wf(".github/workflows/build.yml", CI_PASS))
        verdict_case("E14e", "the same workflow named build.yaml", "E14", PASS,
                     with_wf(".github/workflows/build.yaml", CI_PASS))
        verdict_case("E14s", "both suites only in a workflow under a "
                     "subdirectory, which GitHub does not run", "E14", RED,
                     with_wf(".github/workflows/old/build.yml", CI_PASS))
        verdict_case("E14v", "the userspace suite in ci.yml and rlxboot's in "
                     "build.yml", "E14", PASS,
                     with_wf(".github/workflows/build.yml", wf_rlx,
                             ci=CI_PASS.split("      - name: rlxboot")[0]))
        verdict_case("E14x", "a second workflow that does not parse", "E14",
                     UNMEASURED,
                     with_wf(".github/workflows/build.yml",
                             "jobs:\n  b:\n    steps:\n   - run: x\n",
                             ci=CI_PASS))
        verdict_case("E14u", "no workflow at all", "E14", UNMEASURED,
                     without(".github/workflows/ci.yml"))

        # ---- E14w: the CI log -----------------------------------------------
        on_base("E14wr", "a log without `host suite: PASS`", "E14w", RED,
                log=fake_log(fx.head(broot), hostsuite=False))
        on_base("E14wo", "a log of another commit", "E14w", UNMEASURED,
                log=fake_log("1" * 40))
        on_base("E14wx", "the userspace line only inside a longer line (an "
                "echoed command)", "E14w", RED,
                log=fake_log(fx.head(broot), userspace=False)
                + "build\tuserspace\t2026-10-09T10:00:09.0Z echo \"test: 2 of 2 "
                "program suites ran and passed\"\n")
        on_base("E14wt", "a raw per-job log, timestamps and CRLF, no gh prefix",
                "E14w", PASS, log=fake_log(fx.head(broot), raw=True))
        root3 = fx.repo(files_with("src/Makefile", SRC_MAKEFILE.replace(
            "init cfgstore", "init cfgstore brokerd")))
        r = measure(Tree(root3), fx.inputs(root3, "E14ws"))["E14w"]
        check_("E14ws", "PROGS grows to three, the log still says 2 of 2 -> RED",
               r.verdict == RED, f"got {r.verdict} ({r.value})")
        root4 = fx.repo(files_with("src/Makefile", SRC_MAKEFILE.replace(
            "program suites ran and passed", "suites passed")))
        r = measure(Tree(root4), fx.inputs(root4, "E14we"))["E14w"]
        check_("E14we", "src/Makefile's echo changed -> UNMEASURED, not a stale "
               "PASS", r.verdict == UNMEASURED, f"got {r.verdict} ({r.value})")

        # ---- E15: the docs index ---------------------------------------------
        verdict_case("E15r", "an orphan notes/b.md", "E15", RED,
                     files_with("notes/b.md", "# B\n"))
        # docs/README.md -> notes/README.md -> notes/a.md -> notes/b.md: b is
        # the one file at hop 3, so this case is the 2-versus-3 boundary.
        f = files_with("notes/a.md", base["notes/a.md"] + "\nsee [b](b.md)\n")
        f["notes/b.md"] = "# B\n"
        verdict_case("E15h", "notes/b.md exactly three hops away", "E15", RED, f)
        verdict_case("E15x", "no docs/README.md", "E15", RED,
                     without("docs/README.md"))
        f = files_with("docs/README.md", base["docs/README.md"]
                       + "- [progress](../PROGRESS.md)\n")
        f["PROGRESS.md"] = base["PROGRESS.md"].replace(
            "progress 1\n", "[d](notes/d.md)\n", 1)
        f["notes/d.md"] = "# D\n"
        verdict_case("E15s", "notes/d.md reached only through a root file", "E15",
                     RED, f)
        f = files_with("notes/README.md", base["notes/README.md"]
                       + "\n`[b](b.md)` is code, not a link\n")
        f["notes/b.md"] = "# B\n"
        verdict_case("E15c", "notes/b.md linked only from a code span", "E15",
                     RED, f)

        # ---- E16-E21: populations --------------------------------------------
        verdict_case("E16r", "a `plan/README.md` reference in a doc", "E16", RED,
                     files_with("docs/build.md", base["docs/build.md"]
                                + "\nsee `plan/README.md`\n"))
        verdict_case("E16b", "the code span `plan`", "E16", RED,
                     files_with("notes/a.md", base["notes/a.md"]
                                + "\n`plan` \u00a7 6 says so\n"))
        verdict_case("E16d", "../plan/x.md from notes/", "E16", RED,
                     files_with("notes/a.md", base["notes/a.md"]
                                + "\n[x](../plan/x.md)\n"))
        verdict_case("E17r", "a driver's first #include at line 61", "E17", RED,
                     files_with("kernel/linux-2.6.30/drivers/net/rtl819x-nic.c",
                                "/* one more */\n" + base[
                                    "kernel/linux-2.6.30/drivers/net/rtl819x-nic.c"]))
        verdict_case("E17u", "no driver anywhere", "E17", UNMEASURED,
                     without("kernel/linux-2.6.30/drivers/net/rtl819x-nic.c",
                             "kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c"))
        f = without("kernel/linux-2.6.30/drivers/net/rtl819x-nic.c")
        f["config/linux-2.6.30/drivers/net/rtl819x-nic.c"] = (
            "".join("/* */\n" for _ in range(70)) + "#include <x.h>\n")
        verdict_case("E17k", "a driver under config/ is found too",
                     "E17", RED, f)
        verdict_case("E18r", "a 量 in a header under the kernel root", "E18", RED,
                     files_with("kernel/linux-2.6.30/include/rlxfw.h",
                                "/* \u91cf 2026 */\n"))
        verdict_case("E18e", "a U+26A0 U+FE0F in src/", "E18", RED,
                     files_with("src/init/main.c",
                                "/* \u26a0\ufe0f */\nint main(void){return 0;}\n"))
        verdict_case("E19r", "the WSL home path in a tool", "E19", RED,
                     files_with("tools/fake.sh", "#!/bin/sh\ncd " + HOME_KEY
                                + "/fwre-work\n"))
        verdict_case("E19w", "the Windows user name in a doc", "E19", RED,
                     files_with("docs/build.md", base["docs/build.md"]
                                + "C:\\Users\\" + WIN_USER + "\\x\n"))
        verdict_case("E19q", "the qemu transcript's path, copied into a "
                     "non-record qemu/README.md", "E19", RED,
                     files_with("qemu/README.md", "# qemu\n\nran from "
                                + HOME_KEY + "/fwre-work\n"))
        verdict_case("E21r", "'portfolio' in a note", "E21", RED,
                     files_with("notes/a.md", base["notes/a.md"] + "\nportfolio\n"))
        verdict_case("E21j", "履歷 in a doc", "E21", RED,
                     files_with("docs/build.md", base["docs/build.md"] + "\n履歷\n"))
        verdict_case("E21a", "'Re\u0301sume\u0301', capital and decomposed, in a "
                     "note", "E21", RED,
                     files_with("notes/a.md", base["notes/a.md"]
                                + "\nRe\u0301sume\u0301\n"))
        verdict_case("E21s", "an exempt file that no longer carries a hit (a "
                     "stale exemption)", "E21", RED,
                     files_with("tools/test-entrycheck-mutants.py", "# clean\n"))
        verdict_case("E21m", "an exempt file that is not tracked", "E21", RED,
                     without("tools/entrycheck.py"))

        # ---- CLAUDE.md's exemptions from E16 and E19 (2026-10-09 ruling) ----
        # The base carries one hit of each in CLAUDE.md and reads PASS (E16p,
        # E19p): the exemptions permit.  Below, each goes stale both ways and
        # reads RED, the name is matched exactly, and E21 is not exempted.
        for rid in ("E16", "E19"):
            r = bres[rid]
            check_(f"{rid}k", f"the base's {rid} PASS rests on CLAUDE.md's "
                   f"exemption, and the row's evidence says so",
                   r.verdict == PASS and any(
                       e.startswith("exempt by name: CLAUDE.md -- ")
                       and e.endswith("needed") for e in r.evidence),
                   f"got {r.verdict}; " + "; ".join(r.evidence[-2:]))
        verdict_case("E16e", "CLAUDE.md no longer names the plan directory: "
                     "its exemption is stale", "E16", RED,
                     files_with("CLAUDE.md", "# CLAUDE.md\n\n| `$FWRE_WORK` | "
                                + HOME_KEY + "/fwre-work |\n"))
        verdict_case("E19e", "CLAUDE.md no longer carries the path: its "
                     "exemption is stale", "E19", RED,
                     files_with("CLAUDE.md", "# CLAUDE.md\n\n| `plan/` | "
                                "private |\n"))
        xroot = fx.repo(without("CLAUDE.md"))
        xres = measure(Tree(xroot), Inputs())
        for rid in ("E16", "E19"):
            r = xres[rid]
            check_(f"{rid}x", f"CLAUDE.md not tracked: {rid}'s exemption is "
                   f"stale -> RED", r.verdict == RED and "stale" in r.value,
                   f"got {r.verdict} ({r.value})")
        verdict_case("E16n", "a docs/CLAUDE.md is not the exempt file: the name "
                     "is matched whole", "E16", RED,
                     files_with("docs/CLAUDE.md", "see `plan/README.md`\n"))
        verdict_case("E21c", "CLAUDE.md carrying a framing term: E21 does not "
                     "exempt it", "E21", RED,
                     files_with("CLAUDE.md", base["CLAUDE.md"] + "\nportfolio\n"))

        # ---- the command line: check, waivers, --offline, refusals -----------
        me = os.path.abspath(__file__)

        def cli(*args):
            r = subprocess.run([sys.executable, me] + list(args),
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            return r.returncode, r.stdout, r.stderr

        def ins(i):
            return ["--gh-json", i.gh_json, "--blob-html", i.blob_dir,
                    "--ci-log", i.ci_log]

        rc, out, err = cli("check", "--root", broot, *ins(binp))
        check_("X1", "check on the all-PASS base with every input exits 0",
               rc == 0 and "check: PASS" in out, f"rc {rc}: {err.strip()[:200]}")
        r1root = fx.repo(files_with("README.md", fx_readme(extra_lines=1)))
        r1inp = fx.inputs(r1root, "X2")
        rc, out, err = cli("check", "--root", r1root, *ins(r1inp))
        check_("X2", "check with one row RED exits 1 and names it",
               rc == 1 and "RED: E1" in out, f"rc {rc}")
        rc, out, err = cli("report", "--root", broot)
        rows = {ln.split()[0]: ln.split()[1] for ln in out.split("\n")
                if re.match(r"^  E\d+w? ", ln)}
        check_("X3", "report without inputs prints every online row UNMEASURED, "
               "never PASS", rc == 0 and all(rows.get(x) == UNMEASURED
                                             for x in ONLINE)
               and len(rows) == len(ROWS), f"rc {rc}, rows {rows}")
        check_("X4", "report prints the record set", "qemu/20??-??-??*/" in out
               and "RUNSHEET.md (at any path)" in out, "not printed")
        rc, out, err = cli("check", "--root", broot)
        check_("U1", "check without online inputs exits 1: UNMEASURED fails",
               rc == 1 and "4 rows not measured: E8w, E12, E13, E14w" in out,
               f"rc {rc}")
        rc, out, err = cli("check", "--root", broot, "--offline")
        check_("U2", "check --offline on the all-PASS base exits 0 and says "
               "which rows it did not measure",
               rc == 0 and "4 rows not measured: E8w, E12, E13, E14w" in out,
               f"rc {rc}: {out[-300:]}")
        rc, out, err = cli("check", "--root", broot, "--offline", "--gh-json",
                           binp.gh_json)
        check_("U3", "--offline with an online input is refused", rc == 2
               and "contradict" in err and "Traceback" not in err, f"rc {rc}")
        u4 = fx.repo(without("kernel/linux-2.6.30/drivers/net/rtl819x-nic.c",
                             "kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c"))
        rc, out, err = cli("check", "--root", u4, "--offline")
        check_("U4", "--offline never excuses an offline row that is UNMEASURED",
               rc == 1 and "E17" in out and "never excuses" in out, f"rc {rc}")
        w1root = fx.repo(files_with(
            "kernel/linux-2.6.30/drivers/net/rtl819x-nic.c",
            "/* one more */\n" + base["kernel/linux-2.6.30/drivers/net/rtl819x-nic.c"]))
        w1inp = fx.inputs(w1root, "W1")
        rc, out, err = cli("check", "--root", w1root, *ins(w1inp),
                           "--waive", "E17=vendor-style headers kept")
        check_("W1", "a RED E17 waived reads WAIVED with its reason, and check "
               "exits 0", rc == 0 and re.search(r"^  E17 +WAIVED ", out, re.M)
               and "vendor-style headers kept" in out, f"rc {rc}")
        rc, out, err = cli("check", "--root", w1root, *ins(w1inp))
        check_("W1b", "the same tree without the waiver exits 1", rc == 1,
               f"rc {rc}")
        rc, out, err = cli("check", "--root", broot, *ins(binp),
                           "--waive", "E17=not needed")
        check_("W2", "a waiver on a row that measures PASS is stale and fails "
               "check", rc == 1 and "STALE WAIVER" in out, f"rc {rc}")
        rc, out, err = cli("check", "--root", broot, "--waive", "E1=too long")
        check_("W3", "waiving a row the DoD does not let be waived is refused",
               rc == 2 and "not waivable" in err and "Traceback" not in err,
               f"rc {rc}")
        rc, out, err = cli("check", "--root", broot, "--waive", "E17=")
        check_("W4", "a waiver without a reason is refused",
               rc == 2 and "reason" in err, f"rc {rc}")
        nogit = os.path.join(td, "not-a-repo")
        os.makedirs(nogit)
        rc, out, err = cli("report", "--root", nogit)
        check_("R1", "--root outside a work tree is refused with a reason",
               rc == 2 and err.startswith("entrycheck:")
               and "Traceback" not in err, f"rc {rc}: {err.strip()[:120]}")
        rc, out, err = cli("report", "--root", broot, "--blob-html",
                           os.path.join(td, "nowhere"))
        check_("R2", "--blob-html naming no directory is refused", rc == 2
               and "not a directory" in err, f"rc {rc}")
        rc, out, err = cli("report", "--root", broot, "--ci-log",
                           os.path.join(td, "nowhere.log"))
        check_("R3", "--ci-log naming no file is refused", rc == 2
               and "not a file" in err, f"rc {rc}")

        # ---- Q: the two sources E14w reads, in this repository ---------------
        mk = os.path.join(ROOT, "src", "Makefile")
        hs = os.path.join(ROOT, "src", "rlxboot", "test", "run-host-tests.sh")
        try:
            mkt = open(mk, encoding="utf-8").read()
        except OSError as e:
            mkt = ""
            print(f"        cannot read {mk}: {e.strerror}")
        try:
            hst = open(hs, encoding="utf-8").read()
        except OSError as e:
            hst = ""
            print(f"        cannot read {hs}: {e.strerror}")
        check_("Q1", "src/Makefile still prints the summary line E14w waits for",
               bool(SRC_TEST_ECHO.search(mkt)) and bool(PROGS_DEF.search(mkt)),
               "its `test` echo or PROGS changed")
        check_("Q2", "run-host-tests.sh still prints `host suite: PASS`",
               bool(HOSTSUITE_ECHO.search(hst)), "its last echo changed")

    print()
    print(f"  {ok} passed, {fail} failed")
    return 0 if fail == 0 else 1


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")
    for name, fn, hlp in (("report", cmd_report, "every row, value, target, "
                           "verdict and definition"),
                          ("check", cmd_check, "exit 0 only if every row is "
                           "PASS or WAIVED")):
        p = sub.add_parser(name, help=hlp)
        p.add_argument("--root", default=ROOT, help="the work tree (default: "
                       "the repository this file is in)")
        p.add_argument("--gh-json", default=None, metavar="FILE")
        p.add_argument("--blob-html", default=None, metavar="DIR")
        p.add_argument("--ci-log", default=None, metavar="FILE")
        p.add_argument("--offline", action="store_true",
                       help="measure the offline rows only")
        p.add_argument("--waive", action="append", default=None,
                       metavar="ID=REASON", help="E17 or E18 only; repeatable")
        p.set_defaults(func=fn)
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_help()
        return 2
    try:
        return args.func(args)
    except OSError as e:
        _fail(f"{e.filename or ''}: {e.strerror}")
    except Exception as e:      # a defect, not a verdict: say where, rc 3
        tb = e.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        at = f" at line {tb.tb_lineno}" if tb is not None else ""
        print(f"entrycheck: internal error{at}: {type(e).__name__}: {e} -- a "
              f"defect in this tool, not a verdict", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
