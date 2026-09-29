#!/usr/bin/env python3
r"""citeresolve -- what did a line-number citation in a RECORD cite, and where
does that text live now?

A record -- `LOG.md`, `bench/`, `CHANGELOG.md`, `docs/history/`, a
`docs/GATE-RESULTS.md` entry -- is never edited after the segment that wrote
it, so its `FILE:NNN` citations are never repaired.  The rule is that such a
number resolves against FILE AS IT WAS AT THE RECORD'S COMMIT.  Once text
moves -- `R1y` moves `PROGRESS.md`'s closed regions verbatim into
`docs/history/` -- today's line NNN is unrelated text and nothing says so
(`notes/record-integrity.md` § 5.3).  This reads a citation the way the rule
says, then finds the text it cited in today's tree.  A reading, not a gate.

    citeresolve.py FILE[:N|:A-B] [...] [--cited PATH] [--rev REV] [--tsv]
                   [--show K] [--root DIR]
    citeresolve.py FILE --date YYYY-MM-DD [...]
    citeresolve.py --self-test

INPUTS.  FILE is a tracked file read AT HEAD with `git cat-file` (never `git
show`: it prints a tree's listing and exits 0).  `:N` or `:A-B` selects citing
lines, none selects the file; `--date` selects every entry headed `## DATE`,
up to the next level-1 or level-2 heading outside a fence -- by date, never by
position, and ALL of them when several share the date.  `--cited PATH` keeps
the citations whose file resolves to PATH.  Every file is read as bytes, a
leading BOM dropped, decoded as UTF-8 with bad bytes replaced, and split on
`\n` ONLY, a final newline ending the last line (docmove's numbering, which is
`sed -n`'s).  The grammar is citecheck's: `CITE_RX` and `scan_file` are
imported, so fenced, transcript and self-reference lines are skipped the same
way.  To it this adds the comma list `FILE:A,B-C,D`, of which citecheck reads
only `A` (§ 5.1); every element is resolved here.

FOR EACH CITATION
  dated    `git blame -C` at HEAD, over the whole citing file: the commit that
           last changed the citing line's TEXT, followed through a move inside
           the file and out of a file the same commit changed.  -C includes
           -M's in-file detection, at -M's threshold (量: a moved block of 26
           or 34 alphanumerics is followed by -C alone, one of 14 by neither),
           so -M is not passed.  NOT citecheck's `blame_shas`, which has no
           flag, and why is a measurement.  量 2026-09-30, plain blame dates
           9,659 of `LOG.md`'s 33,437 lines to `10b8fbc6`, which only moved two
           entries to the end, and agrees on 346 of 425 citing lines with the
           oldest commit whose patch added that exact line; -C agrees on 423.
           A line `R1y` moves into `docs/history/` is dated by the move unless
           blame looks across files: 11 of 11 citing lines in the two history
           files that carry any go back to the `PROGRESS.md` or `CLAUDE.md`
           commit holding that line.  Whole-file, because `-L` changes what the
           move detection finds (10 of 425 differ).  A configured
           `blame.ignoreRevsFile` is followed and SAID: git 2.43 cannot clear
           it from the command line.
           `--rev REV` dates every citation at REV instead.
           RE-DATED is printed when the dating commit removed, from the file
           blame traced the line to, a line carrying the same citation text:
           the line was edited after it was written, and what is read below
           may postdate the citation (§ 5.6).  The oldest commit whose change
           added that text (`git log -S`) is named as a hint; the dating stays.
  cited    the path as `git ls-tree` had it at that commit (exact, else the one
           tracked path it is a suffix of -- citecheck's resolution, in the
           citing commit's tree instead of HEAD's), and lines A..B of that
           blob.
           Refused per citation and never globally: absent then, inside the
           `upstream` gitlink, a suffix of two paths, past the end, backwards.
           BEFORE: the dating commit changed those very lines, so the author
           may have been reading either side.  The rule takes the commit's;
           the parent's first line is printed beside it.  量 over `LOG.md`:
           81 of the 323 citations it can read there.
           HINT, on a line past the end: the newest earlier commit whose file
           had that line, for --rev.
  now      every tracked blob at HEAD holding the cited text, compared after
           docmove's normalisation -- `unquote`, then `normalise`: a run of
           ASCII whitespace is one space, stripped; U+00A0 is text.  A range
           must be there INTACT, as consecutive lines.  Listed cited file
           first, then `docs/history/`, then the rest.  A match at the cited
           file's own lines is marked `the cited line, unchanged`.
  verdict  one | many | ambiguous -- blank when it was cited, or more than one
           match for text under docmove's 40 code points or a table
           separator | not found verbatim | refused.

EXIT: 0 when it ran, whatever it found; 2 refusal -- not a repository, a
shallow clone without --rev (blame would date every line to the graft), FILE
not tracked at HEAD, a selection past its end, no entry with that date, a REV
that is not a commit.  --self-test: 0 every control passed, 1 otherwise.
About 25 s over the whole of `LOG.md`: its blame is 10-13 s of that.

WHAT IT CANNOT SEE
  * Text that changed.  A row that grew in place after it was cited -- § 5.3
    measured that as the usual fate of a `PROGRESS.md` row -- is `not found
    verbatim`, and so is a paragraph re-wrapped across lines, which docmove
    still calls conserved.  It says where the words are, never where they
    went.
  * Whether the citation was right when written (§ 5.2).  It reports what line
    N held; the sentence citing it is for a reader.  Nor which side of a
    change the author read when one commit both cited and changed a line
    (BEFORE), nor a number the citing sentence gives as history -- `370 ->
    451` reads 370 in the commit that already had 451.
  * A re-dating that removed no line carrying the same text -- the citation's
    number changed in the same edit -- and a move blame does not recognise
    (under 20 alphanumeric characters, or from a file the commit did not
    change).  The hint names the first commit that added that text ANYWHERE in
    the file, which is not always this line.
  * The working tree.  Both the citing file and the search are read at HEAD,
    so an uncommitted move is invisible until it is committed.
  * What the grammar does not parse: an extensionless file (`Makefile:163`),
    a bare `:758` after a `、`, a citation inside a fence, and a thousands
    comma -- `LOG.md:30,599` reads as lines 30 and 599.
  * Anything under `upstream/` (refused: inside the gitlink), or under
    `src-vendor/` or `plan/` (refused: absent at the citing commit, since
    neither is tracked).
  * A file holding a bare CR has no single meaning of "line N" (citecheck's
    T19); this counts `\n`, as `sed -n` does.

REFUTATION.  It is wrong if the text it reports is not line N of the cited
file at the dating commit (R1-R3, R10 against the fixture's own lists, R11
under --rev); if a path resolves other than in that commit's tree (R19, a
file deleted since; R20, a basename, and two that share one); if moved text
is not reported where it is (R1-R3, R9, R19); if text that is gone is
reported found (R4, including a range whose first line moved and whose second
did not; R9's U+00A0 copy); if a move re-dates a citation (R17 inside the
file, R18 across files, each with the control that a weaker blame DOES
re-date it there); if a generic line is called `one` (R5); if the prefilter
drops a line docmove's normalisation matches (R16); if a hint fires where it
should not or stays silent where it should (R12, R21); if --date selects by
position (R13); or if the dating is not load-bearing -- R14 dates every
citation at HEAD and requires R1-R3 to go red.  RE-DATED, BEFORE and HINT
never change a verdict.
"""

import argparse
import collections
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Before the imports below: loading citecheck, docmove and spec-check must not
# write `.pyc` into the tree they run from, which a desk sweep reports as "the
# source moved" (docmove's D16 guards the same write).
sys.dont_write_bytecode = True

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # a replaced or detached stdout
    pass

VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GIT = "git"
SHOW = 8
HISTORY = "docs/history/"
BLAME_FLAGS = ("-C",)
#: `git -C ROOT` must mean ROOT: an inherited GIT_DIR -- a hook sets one --
#: would read another repository (docmove's D12).
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE")
BOM = b"\xef\xbb\xbf"
WSB = b" \t\r\f\v"                                 # docmove's WS, less `\n`
QLINE = re.compile(rb"(?m)^>+(.*)$")
BLAME_HEAD = re.compile(rb"^([0-9a-f]{40}) (\d+) (\d+) (\d+)$")
TARGET_RX = re.compile(r"^(.+?):(\d+)(?:-(\d+))?$")
CONT_RX = re.compile(r",(\d+)(?:-(\d+))?(?![0-9])")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ENTRY_RX = re.compile(r"^## (\d{4}-\d{2}-\d{2})(?![0-9])")
HEADING_RX = re.compile(r"^#{1,2} ")
SEPARATOR_RX = re.compile(r"^(?=.*\|)(?=.*-)[|: -]+$")
TSV_COLUMNS = ("citing", "line", "element", "written", "resolved", "from",
               "to", "dated", "how", "origin", "redated", "verdict",
               "matches", "locations", "before", "hint", "text")
REFUSALS = (("absent", "absent at the citing commit"),
            ("gitlink", "inside the gitlink"),
            ("suffix", "a suffix of two paths"),
            ("past", "past the end"),
            ("backwards", "backwards"),
            ("undated", "no dating commit"))


class Refusal(Exception):
    """An input this tool cannot honestly report on.  Exit 2."""


def _load(name):
    """citecheck and docmove are IMPORTED rather than restated: a second copy
    of the citation grammar or of the normalisation would be a second thing to
    keep right, and the two tools' readings would drift apart silently."""
    path = os.path.join(HERE, name + ".py")
    if not os.path.isfile(path):
        print("REFUSING: %s is not there, and this tool's grammar and "
              "normalisation are that file's" % path)
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("_citeresolve_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CC = _load("citecheck")      # CITE_RX, scan_file, suffix_index, is_shallow
DM = _load("docmove")        # normalise, unquote, MIN_CHARS, shown


def _env():
    return {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}


def _git(root, *args):
    """-> (rc, stdout bytes, stderr text).  Bytes, never `text=True`: universal
    newlines turn a bare CR into a line break (citecheck's T19)."""
    try:
        r = subprocess.run([GIT, "-C", root] + list(args),
                           capture_output=True, env=_env())
    except OSError as e:
        raise Refusal("git is not available (%s: %s)" % (GIT, e))
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace").strip()


def blob_lines(blob):
    """-> (text lines, byte lines), numbered as `sed -n` numbers them."""
    if blob.startswith(BOM):
        blob = blob[len(BOM):]
    raw = blob.split(b"\n")
    if raw and raw[-1] == b"":
        raw.pop()
    return [r.decode("utf-8", "replace") for r in raw], raw


def norm(text):
    """docmove's normalisation of one line: its blockquote marker stripped, a
    run of ASCII whitespace made one space, and the ends stripped."""
    return DM.normalise(DM.unquote(text))


def key(raw):
    """The prefilter's key for one line: every ASCII whitespace byte deleted,
    then every leading `>`.  For UTF-8 lines norm(a) == norm(b) implies
    key(a) == key(b): normalising changes whitespace only, and `unquote`
    deletes a prefix made of whitespace and `>`.  So a line the prefilter
    drops could not have matched -- R16 checks that rather than trusting this
    paragraph.  Two lines differing only in bytes that are not UTF-8 decode
    alike and key apart; the prefilter keeps them apart, the stricter reading,
    since they are not the same bytes."""
    return raw.translate(None, WSB).lstrip(b">")


class Repo(object):
    """One repository, read through one `git cat-file --batch`."""

    def __init__(self, root):
        self.root = root
        self.trees = {}
        try:
            self.proc = subprocess.Popen(
                [GIT, "-C", root, "cat-file", "--batch"], env=_env(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, bufsize=1 << 20)
        except OSError as e:
            raise Refusal("git is not available (%s: %s)" % (GIT, e))

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait()
        except (OSError, ValueError):
            pass

    def read(self, name):
        """-> (type, bytes) of `name`, or (None, None) when git has none."""
        self.proc.stdin.write(name.encode("utf-8") + b"\n")
        self.proc.stdin.flush()
        head = self.proc.stdout.readline().split()
        if len(head) != 3:                      # `<name> missing`, ambiguous
            return None, None
        data = self.proc.stdout.read(int(head[2]))
        self.proc.stdout.read(1)
        return head[1].decode(), data

    def tree(self, rev):
        """-> (blobs as [(path, sha)], suffix index, gitlinks) of `rev`."""
        if rev not in self.trees:
            rc, out, err = _git(self.root, "ls-tree", "-r", "-z",
                                "--full-tree", rev)
            if rc != 0:
                raise Refusal("git ls-tree %s failed: %s" % (rev, err))
            blobs, links = [], []
            for rec in out.split(b"\0"):
                if not rec:
                    continue
                meta, path = rec.split(b"\t", 1)
                mode, typ, sha = meta.split(b" ")
                p = path.decode("utf-8", "replace")
                if mode == b"160000":
                    links.append(p)
                elif typ == b"blob" and mode in (b"100644", b"100755"):
                    blobs.append((p, sha.decode()))
            self.trees[rev] = (blobs, CC.suffix_index([p for p, _s in blobs]),
                               links)
        return self.trees[rev]

    def resolve(self, sha, written):
        """-> (path, how, blob) or (None, (kind, why), None), in the tree of
        `sha`."""
        typ, data = self.read("%s:%s" % (sha, written))
        if typ == "blob":
            return written, "exact", data
        _blobs, idx, links = self.tree(sha)
        for g in links:
            if written == g or written.startswith(g + "/"):
                return None, ("gitlink", "inside the gitlink `%s`, which this "
                                         "tool does not read" % g), None
        cands = idx.get(written, [])
        if len(cands) > 1:
            return None, ("suffix", "`%s` is a suffix of %d paths at %s: %s"
                          % (written, len(cands), sha[:8],
                             ", ".join(sorted(cands)[:3]))), None
        if not cands:
            return None, ("absent", "`%s` is not a file in the tree of %s"
                          % (written, sha[:8])), None
        typ, data = self.read("%s:%s" % (sha, cands[0]))
        if typ != "blob":
            return None, ("absent", "`%s` did not read as a blob"
                          % cands[0]), None
        return cands[0], "by suffix", data


# ------------------------------------------------------------------ the scan
Element = collections.namedtuple(
    "Element", "src srcline col literal written first last k n")


class _Everything(object):
    """A tracked set that holds every path, so `scan_file` resolves nothing and
    drops nothing as `unresolved`: which file a path names is decided per
    citation, in the tree of the commit that dates it, not in HEAD's."""

    def __contains__(self, path):
        return True


def _mkey(m):
    return (m.group(1), int(m.group(2)),
            int(m.group(3)) if m.group(3) else None)


def scan(rel, lines, wanted):
    """-> (elements, tokens of the citation shape not read as citations, the
    filter counts over the whole file) for the citing lines in `wanted`, a
    set of line numbers, or None for every line."""
    counts = collections.Counter({k: 0 for k in CC.FILTERS})
    cites = CC.scan_file(rel, "\n".join(lines), _Everything(), {}, counts, [])
    if wanted is not None:
        cites = [c for c in cites if c.srcline in wanted]
    by_line = collections.defaultdict(list)
    for c in cites:
        by_line[c.srcline].append(c)
    shape = sum(len(CC.CITE_RX.findall(lines[n - 1]))
                for n in (wanted if wanted is not None
                          else range(1, len(lines) + 1)))
    out = []
    for n in sorted(by_line):
        text = lines[n - 1]
        # scan_file's order, and its transcript rule, so the k-th citation it
        # returned for a key is the k-th match here with that key.
        ms = [m for m in CC.CITE_RX.finditer(text)
              if text[m.end():m.end() + 1] != ":"]
        used = set()
        for c in by_line[n]:
            want = (c.path, c.start, c.end)
            hit = [i for i, m in enumerate(ms)
                   if i not in used and _mkey(m) == want]
            if not hit:
                raise Refusal("%s:%d: scan_file returned %s:%d and this line "
                              "has no such match -- citecheck's grammar moved"
                              % (rel, n, c.path, c.start))
            used.add(hit[0])
            m = ms[hit[0]]
            parts = [(c.start, c.end if c.end is not None else c.start)]
            pos = m.end()
            while True:
                m2 = CONT_RX.match(text, pos)
                if not m2:
                    break
                a = int(m2.group(1))
                parts.append((a, int(m2.group(2)) if m2.group(2) else a))
                pos = m2.end()
            literal = text[m.start():pos]
            for k, (a, b) in enumerate(parts, 1):
                out.append(Element(rel, n, m.start(), literal, c.path, a, b,
                                   k, len(parts)))
    return out, shape - len(cites), counts


def dated_entries(lines, date):
    """-> [(first, last)] of every entry headed `## DATE`, in file order."""
    mask = CC.SC.fence_mask(lines)
    heads = [i for i, ln in enumerate(lines)
             if not mask[i] and HEADING_RX.match(ln)]
    out = []
    for k, i in enumerate(heads):
        m = ENTRY_RX.match(lines[i])
        if m and m.group(1) == date:
            out.append((i + 1, heads[k + 1] if k + 1 < len(heads)
                        else len(lines)))
    return out


# ---------------------------------------------------------------- the dating
def blame(root, rel, flags):
    """{final line: (sha, the file blame traced it to, the line there)}.

    Restated from citecheck's `blame_shas` -- the same `--incremental` format,
    with the original line kept as well -- because that one takes no flags and
    drops the `filename` each chunk carries, and this needs both."""
    rc, out, err = _git(root, "blame", "--incremental", *flags, "HEAD", "--",
                        rel)
    if rc != 0:
        raise Refusal("`git blame %s HEAD -- %s` failed: %s"
                      % (" ".join(flags), rel, err))
    got, cur = {}, None
    for line in out.split(b"\n"):
        m = BLAME_HEAD.match(line)
        if m:
            cur = [int(x) if i else x.decode()
                   for i, x in enumerate(m.groups())]
        elif line.startswith(b"filename ") and cur:
            name = line[len(b"filename "):].decode("utf-8", "replace")
            if name[:1] == '"' and name[-1:] == '"':       # C-quoted by git
                name = name[1:-1]
            sha, orig, final, n = cur
            for k in range(n):
                got[final + k] = (sha, name, orig + k)
            cur = None
    return got


def blame_dater(root, rel, lines):
    """The default dating -- and the seam R14 replaces with HEAD."""
    got = blame(root, rel, BLAME_FLAGS)
    return {n: got.get(n) for n in lines}


def removed_by(root, origin, shas):
    """{sha: the bytes of every line that commit removed from `origin`}, from
    ONE `git log --no-walk -p -U0`.  Hunk lines only: a removed `- item` is
    `-- item` in the patch and is kept."""
    rc, out, err = _git(root, "log", "--no-walk=unsorted", "-p", "-U0", "-a",
                        "--no-color", "--no-ext-diff", "--no-textconv",
                        "--format=%x00%H", *sorted(shas), "--", origin)
    if rc != 0:
        raise Refusal("`git log -p -- %s` failed: %s" % (origin, err))
    got, cur, hunk, rem = {}, None, False, []
    for line in out.split(b"\n") + [b"\x00"]:
        if line.startswith(b"\x00"):
            if cur:
                got[cur] = b"\n".join(rem)
            cur, hunk, rem = line[1:].decode(), False, []
        elif line.startswith(b"diff --git "):
            hunk = False
        elif line.startswith(b"@@"):
            hunk = True
        elif hunk and line.startswith(b"-"):
            rem.append(line[1:])
    return got


def first_commit(root, origin, literal):
    """The oldest commit that changed how often `literal` occurs in `origin`
    (`git log -S`), or None."""
    rc, out, _err = _git(root, "log", "-S" + literal, "--format=%H",
                         "--reverse", "HEAD", "--", origin)
    shas = out.decode().split()
    return shas[0] if rc == 0 and shas else None


# --------------------------------------------------------------- the search
class Query(object):
    """One cited block, and where it is now."""

    def __init__(self, block, akeys):
        self.block = block
        self.anchor = max(range(len(block)), key=lambda i: (len(block[i]), -i))
        self.akey = akeys[self.anchor]
        self.hits = []


def search_head(repo, queries):
    """Every tracked blob at HEAD, once.  A blob whose line keys meet no
    query's anchor key is skipped without decoding it; in the rest, a line is
    a match when its normalisation equals the anchor's and the lines around
    it equal the rest of the block.  -> (blobs read, binary skipped)."""
    by_key = collections.defaultdict(list)
    for q in queries:
        by_key[q.akey].append(q)
    blobs, _idx, _links = repo.tree("HEAD")
    nbin = 0
    for path, bsha in blobs:
        _typ, data = repo.read(bsha)
        if data is None:
            continue
        if b"\0" in data:
            nbin += 1
            continue
        if data.startswith(BOM):
            data = data[len(BOM):]
        flat = data.translate(None, WSB)
        have = set(flat.split(b"\n"))
        if b">" in flat:
            have.update(QLINE.findall(flat))
        hit = have.intersection(by_key)
        if not hit:
            continue
        raw = data.split(b"\n")
        if raw and raw[-1] == b"":
            raw.pop()
        memo = {}

        def at(i):
            if i not in memo:
                memo[i] = norm(raw[i].decode("utf-8", "replace"))
            return memo[i]
        for i, rb in enumerate(raw):
            kb = key(rb)
            if kb not in hit:
                continue
            for q in by_key[kb]:
                s = i - q.anchor
                if (at(i) == q.block[q.anchor] and s >= 0
                        and s + len(q.block) <= len(raw)
                        and all(at(s + j) == q.block[j]
                                for j in range(len(q.block)))):
                    q.hits.append((path, s + 1))
    return len(blobs), nbin


# ----------------------------------------------------------------- resolving
class Result(object):
    """One element of one citation, as far as it got."""

    def __init__(self, el):
        self.el = el
        self.sha = self.how = self.origin = self.oline = None
        self.path = self.found = self.why = self.kind = None
        self.redated = self.first = self.query = self.verdict = None
        self.parent = self.hint = None
        self.text, self.akeys, self.locs = [], [], []

    def refuse(self, kind, why):
        self.verdict, self.kind, self.why = "refused", kind, why


def resolve(a, dater):
    root = os.path.abspath(a.root)
    shallow = CC.is_shallow(root)
    if shallow is None:
        raise Refusal("%s is not a git repository, or git is not available"
                      % root)
    if shallow and not a.rev:
        raise Refusal("%s is a SHALLOW clone: blame would date every line "
                      "older than the graft to the graft itself. Use a full "
                      "clone, or date every citation with --rev" % root)
    if not a.targets:
        raise Refusal("no FILE given")
    if a.date and not DATE_RX.match(a.date):
        raise Refusal("--date wants YYYY-MM-DD, got %r" % a.date)
    if a.show < 0:
        raise Refusal("--show must be 0 or more, got %d" % a.show)
    rc, out, _err = _git(root, "rev-parse", "--verify", "-q", "HEAD^{commit}")
    if rc != 0:
        raise Refusal("%s has no HEAD commit" % root)
    head = out.decode().strip()
    rev = None
    if a.rev:
        rc, out, _err = _git(root, "rev-parse", "--verify", "-q",
                             a.rev + "^{commit}")
        if rc != 0:
            raise Refusal("--rev %s is not a commit in %s" % (a.rev, root))
        rev = out.decode().strip()
    repo = Repo(root)
    try:
        res = _resolve(a, dater, root, repo, head, rev)
    finally:
        repo.close()
    res["root"] = root
    return res


def _selection(a):
    """-> (files in order, files taken whole, {file: [(first, last)]})."""
    order, whole, ranges = [], set(), collections.defaultdict(list)
    for spec in a.targets:
        m = TARGET_RX.match(spec)
        rel = m.group(1) if m else spec
        if rel not in order:
            order.append(rel)
        if not m:
            whole.add(rel)
            continue
        if a.date:
            raise Refusal("%s: --date selects its own lines; give FILE "
                          "without :N" % spec)
        first = int(m.group(2))
        last = int(m.group(3)) if m.group(3) else first
        if first < 1 or last < first:
            raise Refusal("%s: a selection is N or A-B with 1 <= A <= B"
                          % spec)
        ranges[rel].append((first, last))
    return order, whole, ranges


def _cited_may_be(a, written):
    """Can `written` resolve to --cited PATH at some commit?  Only when it is
    PATH or a suffix of it, so nothing else needs dating or reading."""
    return (not a.cited or a.cited == written
            or a.cited.endswith("/" + written))


def _resolve(a, dater, root, repo, head, rev):
    order, whole, ranges = _selection(a)
    results, notes, stats = [], [], collections.Counter()
    rc, out, _e = _git(root, "config", "--get-all", "blame.ignoreRevsFile")
    if rc == 0 and out.strip() and not rev:
        # Said, not cleared: git 2.43 opens a configured file before the
        # command line can empty the list (`-c blame.ignoreRevsFile=` does not
        # either, 量).  And its heuristic is not a dating to trust: on the 79
        # citing lines of `LOG.md` that `10b8fbc6` moved it agreed with the
        # first commit that added the line on 15, where -M agreed on 77.
        notes.append("blame.ignoreRevsFile is set (%s): git re-attributes the "
                     "lines of the commits it lists by a heuristic, and the "
                     "dating below follows it" % ", ".join(
                         out.decode("utf-8", "replace").split()))
    for rel in order:
        typ, blob = repo.read("HEAD:" + rel)
        if typ != "blob":
            raise Refusal("%s is not tracked at HEAD (%s)" % (
                rel, "a tree" if typ == "tree" else "git has no such file"))
        lines, _raw = blob_lines(blob)
        sel = None if rel in whole else ranges[rel]
        if a.date:
            sel = dated_entries(lines, a.date)
            if not sel:
                raise Refusal("%s has no entry headed `## %s`" % (rel, a.date))
            notes.append("%s: %d entr%s headed `## %s`, lines %s" % (
                rel, len(sel), "y" if len(sel) == 1 else "ies",
                a.date, ", ".join("%d-%d" % r for r in sel)))
        wanted = None
        if sel is not None:
            wanted = set()
            for f, l in sel:
                if l > len(lines):
                    raise Refusal("%s:%d-%d: %s has %d lines at HEAD"
                                  % (rel, f, l, rel, len(lines)))
                wanted.update(range(f, l + 1))
        rc, _o, _e = _git(root, "diff", "--quiet", "HEAD", "--", rel)
        if rc == 1:
            notes.append("%s differs from HEAD in the working tree; the line "
                         "numbers here are HEAD's" % rel)
        els, filtered, counts = scan(rel, lines, wanted)
        stats["lines"] += len(wanted) if wanted is not None else len(lines)
        stats["filtered"] += filtered
        stats["whole"] += 1 if wanted is None else 0
        for k in ("fenced", "transcript", "selfref"):
            stats[k] += counts[k]
        kept = [e for e in els if _cited_may_be(a, e.written)]
        stats["cited-out"] += len(els) - len(kept)
        results.extend(_date_and_read(dater, root, repo, rel, kept, rev))
    if a.cited:
        kept = [r for r in results if a.cited in (r.path, r.el.written)]
        stats["cited-out"] += len(results) - len(kept)
        results = kept
    queries = []
    for r in results:
        if r.verdict is None and any(r.text):
            r.query = Query(r.text, r.akeys)
            queries.append(r.query)
    scanned = search_head(repo, queries) if queries else (0, 0)
    for r in results:
        _verdict(r)
    return {"results": results, "notes": notes, "stats": stats, "head": head,
            "rev": rev, "scanned": scanned, "files": order}


def _date_and_read(dater, root, repo, rel, els, rev):
    out = [Result(e) for e in els]
    if not out:
        return out
    need = sorted(set(e.srcline for e in els))
    dates = (dict((n, (rev, rel, n)) for n in need) if rev
             else dater(root, rel, need))
    for r in out:
        d = dates.get(r.el.srcline)
        r.how = "--rev" if rev else "blame " + " ".join(BLAME_FLAGS)
        if not d or not d[0] or d[0] == CC.ZERO:
            r.refuse("undated", "no commit dates this line")
            continue
        r.sha, r.origin, r.oline = d
    if not rev:
        _redating(root, [r for r in out if r.sha])
    blobs = {}
    for r in out:
        if not r.sha:
            continue
        e = r.el
        k = (r.sha, e.written)
        if k not in blobs:
            path, how, data = repo.resolve(r.sha, e.written)
            parent = None
            if path:
                typ, pdata = repo.read("%s^:%s" % (r.sha, path))
                if typ == "blob" and pdata != data:
                    parent = blob_lines(pdata)[0]
            blobs[k] = (path, how, blob_lines(data) if path else None, parent)
        path, how, data, parent = blobs[k]
        if path is None:
            r.refuse(*how)
            continue
        r.path, r.found = path, how
        lines, raw = data
        if e.last < e.first:
            r.refuse("backwards", "%d-%d counts backwards" % (e.first, e.last))
        elif e.first < 1:
            r.refuse("past", "there is no line %d" % e.first)
        elif e.last > len(lines):
            r.refuse("past", "line %d is past the end of %s, which had %d "
                             "lines at %s" % (e.last, path, len(lines),
                                              r.sha[:8]))
            r.hint = last_had(root, repo, r.sha, path, e.last)
        else:
            r.text = [norm(t) for t in lines[e.first - 1:e.last]]
            r.akeys = [key(b) for b in raw[e.first - 1:e.last]]
            # The dating commit may have changed the very lines it cites, and
            # then nothing says which side the author was reading.  The rule
            # is the commit's side; the parent's is shown beside it.
            seg = parent[e.first - 1:e.last] if parent is not None else None
            if seg is not None and seg != lines[e.first - 1:e.last]:
                r.parent = (norm(seg[0]) or "(blank)"
                            if len(seg) == len(r.text) else
                            "(past the end there: %d lines)" % len(parent))
    return out


def last_had(root, repo, sha, path, n):
    """The newest commit before `sha` whose `path` had a line `n`, or None:
    where to point --rev when a citation is past the end at its date.  Walks
    at most 50 of the file's own commits."""
    rc, out, _err = _git(root, "log", "--format=%H", "-50", sha + "^", "--",
                         path)
    for c in (out.decode().split() if rc == 0 else []):
        typ, data = repo.read("%s:%s" % (c, path))
        if typ == "blob" and len(blob_lines(data)[1]) >= n:
            return c
    return None


def _redating(root, results):
    """RE-DATED: the dating commit removed, from the file blame traced the
    line to, a line carrying the same citation text."""
    by_origin = collections.defaultdict(set)
    for r in results:
        by_origin[r.origin].add(r.sha)
    removed = {}
    for origin, shas in by_origin.items():
        for sha, rem in removed_by(root, origin, shas).items():
            removed[(sha, origin)] = rem
    firsts = {}
    for r in results:
        lit = r.el.literal
        r.redated = lit.encode("utf-8") in removed.get((r.sha, r.origin), b"")
        if r.redated:
            if (r.origin, lit) not in firsts:
                firsts[(r.origin, lit)] = first_commit(root, r.origin, lit)
            r.first = firsts[(r.origin, lit)]


def _tier(r, path):
    if path == r.path:
        return 0
    return 1 if path.startswith(HISTORY) else 2


def _verdict(r):
    if r.verdict == "refused":
        return
    if not any(r.text):
        r.verdict = "ambiguous"
        r.why = "blank at %s: there is nothing to follow" % r.sha[:8]
        return
    hits = sorted(r.query.hits, key=lambda h: (_tier(r, h[0]), h[0], h[1]))
    r.locs = hits
    joined = DM.normalise(" ".join(r.text))
    short = len(joined) < DM.MIN_CHARS
    sep = all(not s or SEPARATOR_RX.match(s) for s in r.text)
    if not hits:
        r.verdict = "not found verbatim"
        r.why = "no tracked file at HEAD holds %s intact" % (
            "that line" if len(r.text) == 1 else "those %d lines"
            % len(r.text))
    elif len(hits) == 1:
        r.verdict = "one"
    elif short or sep:
        r.verdict = "ambiguous"
        r.why = "%d matches for %s" % (len(hits), "a table separator" if sep
                                      else "text of %d code points, under "
                                      "docmove's %d" % (len(joined),
                                                        DM.MIN_CHARS))
    else:
        r.verdict = "many"


# ----------------------------------------------------------------- reporting
def _loc(r, path, line):
    n = len(r.text)
    where = "%s:%d" % (path, line) if n == 1 else "%s:%d-%d" % (
        path, line, line + n - 1)
    if path == r.path and line == r.el.first:
        where += "  (the cited line, unchanged)"
    return where


def _span(e):
    return "%d" % e.first if e.first == e.last else "%d-%d" % (e.first, e.last)


def _origin(r):
    if r.origin and (r.origin != r.el.src or r.oline != r.el.srcline):
        return "%s:%d" % (r.origin, r.oline)
    return ""


def report(res, a, out, err):
    results = res["results"]
    if a.tsv:
        print("\t".join(TSV_COLUMNS), file=out)
        for r in results:
            e = r.el
            locs = [_loc(r, p, n).split("  ")[0] for p, n in r.locs[:a.show]]
            if len(r.locs) > a.show:
                locs.append("+%d more" % (len(r.locs) - a.show))
            row = [e.src, str(e.srcline), "%d/%d" % (e.k, e.n), e.written,
                   r.path or "", str(e.first), str(e.last),
                   (r.sha or "")[:12], r.how or "", _origin(r),
                   "" if r.redated is None else ("yes" if r.redated else "no"),
                   r.verdict.replace(" ", "-"), str(len(r.locs)),
                   ";".join(locs), DM.shown(r.parent or "", 100),
                   (r.hint or "")[:12],
                   DM.shown(r.text[0] if r.text else "", 100)]
            # Escaped, never cut: a cell cut at a fixed width ends a location
            # list in the middle of a path.  The text column is capped above.
            print("\t".join(DM.shown(x, len(x)) for x in row), file=out)
        _summary(res, a, err)
        return
    dates = _dates(res["root"], set(r.sha for r in results if r.sha) |
                   set(r.first for r in results if r.first) |
                   set(r.hint for r in results if r.hint))
    print("citeresolve %s  --  %s at HEAD %s; dated by %s" % (
        VERSION, ", ".join(res["files"]), res["head"][:8],
        "--rev %s" % res["rev"][:8] if res["rev"] else
        "git blame " + " ".join(BLAME_FLAGS)), file=out)
    for n in res["notes"]:
        print("note     %s" % DM.shown(n, 400), file=out)
    for r in results:
        e = r.el
        print("", file=out)
        tail = "" if e.n == 1 else "   (%d of %d in `%s`; citecheck reads " \
            "only the first)" % (e.k, e.n, DM.shown(e.literal, 80))
        print("%s:%d  %s:%s%s" % (e.src, e.srcline, e.written, _span(e),
                                  tail), file=out)
        if r.sha:
            line = "    dated    %s %s  %s" % (r.sha[:8], dates.get(r.sha, ""),
                                              r.how)
            if _origin(r):
                line += ", traced to %s" % _origin(r)
            print(line, file=out)
        if r.redated:
            line = ("    RE-DATED %s removed a line from %s that already "
                    "carried `%s`" % (r.sha[:8], r.origin,
                                      DM.shown(e.literal, 80)))
            if r.first:
                line += "; `git log -S` finds it first at %s (%s)" % (
                    r.first[:8], dates.get(r.first, "?"))
            print(line, file=out)
        if r.path:
            print("    read     %s:%s at %s%s" % (
                r.path, _span(e), r.sha[:8],
                "" if r.found == "exact" else "  (`%s` %s)" % (e.written,
                                                              r.found)),
                file=out)
        if r.text:
            more = "" if len(r.text) == 1 else "   (+%d more line%s)" % (
                len(r.text) - 1, "" if len(r.text) == 2 else "s")
            print("    text     %s%s" % (DM.shown(r.text[0] or "(blank)",
                                                  100), more), file=out)
        if r.parent is not None:
            print("    before   %s also changed these lines; at its parent "
                  "they began: %s" % (r.sha[:8], DM.shown(r.parent, 100)),
                  file=out)
        v = r.verdict + (" -- " + r.why if r.why else "")
        print("    verdict  %s" % DM.shown(v, 400), file=out)
        if r.hint:
            print("    hint     %s last had line %d at %s (%s): --rev %s "
                  "reads it there" % (r.path, e.last, r.hint[:8],
                                      dates.get(r.hint, "?"), r.hint[:8]),
                  file=out)
        for p, n in r.locs[:a.show]:
            print("    now      %s" % _loc(r, p, n), file=out)
        if len(r.locs) > a.show:
            print("    now      ... and %d more (--show %d)"
                  % (len(r.locs) - a.show, a.show), file=out)
    print("", file=out)
    _summary(res, a, out)


def _summary(res, a, out):
    results, st = res["results"], res["stats"]
    v = collections.Counter(r.verdict for r in results)
    lines = len(set((r.el.src, r.el.srcline) for r in results))
    print("summary  %d citation element(s) on %d citing line(s) of %d "
          "selected: one %d  many %d  ambiguous %d  not found verbatim %d  "
          "refused %d" % (len(results), lines, st["lines"], v["one"],
                          v["many"], v["ambiguous"], v["not found verbatim"],
                          v["refused"]), file=out)
    kinds = collections.Counter(r.kind for r in results if r.kind)
    if kinds:
        print("summary  refused: %s" % ",  ".join(
            "%s %d" % (label, kinds[k]) for k, label in REFUSALS if kinds[k]),
            file=out)
    same = sum(1 for r in results
               if any(p == r.path and n == r.el.first for p, n in r.locs))
    red = sum(1 for r in results if r.redated)
    moved = sum(1 for r in results if _origin(r))
    print("summary  still at the cited line %d  re-dated %d  traced by blame "
          "to another line or file %d  comma-list elements past the first %d"
          % (same, red, moved, sum(1 for r in results if r.el.k > 1)),
          file=out)
    print("summary  dated by a commit that also changed the cited lines %d"
          % sum(1 for r in results if r.parent is not None), file=out)
    if a.cited:
        print("summary  --cited %s kept %d and dropped %d" % (
            a.cited, len(results), st["cited-out"]), file=out)
    detail = ""
    if st["whole"] and st["whole"] == len(res["files"]):
        detail = " (fenced %d, transcript %d, self-reference %d)" % (
            st["fenced"], st["transcript"], st["selfref"])
    print("summary  %d token(s) of the citation shape on those lines were "
          "not read as citations%s" % (st["filtered"], detail), file=out)
    nb, nbin = res["scanned"]
    print("summary  searched %d tracked blob(s) at HEAD %s, %d binary skipped"
          % (nb, res["head"][:8], nbin), file=out)


def _dates(root, shas):
    if not shas:
        return {}
    rc, out, _err = _git(root, "log", "--no-walk=unsorted", "--format=%H %cs",
                         *sorted(shas))
    got = {}
    if rc == 0:
        for ln in out.decode("utf-8", "replace").split("\n"):
            p = ln.split()
            if len(p) == 2:
                got[p[0]] = p[1]
    return got


def run(argv, out, err=None, dater=None):
    """The whole command path, argument parsing included -> exit code.  The
    self-test drives THIS rather than an inner helper, so each control
    exercises what the command line exercises (docmove's `run`).  `dater` is
    the seam R14 uses to date every citation at HEAD."""
    ap = argparse.ArgumentParser(prog="citeresolve.py")
    ap.add_argument("targets", nargs="*", metavar="FILE[:N|:A-B]")
    ap.add_argument("--date", metavar="YYYY-MM-DD")
    ap.add_argument("--cited", metavar="PATH")
    ap.add_argument("--rev", metavar="REV")
    ap.add_argument("--tsv", action="store_true")
    ap.add_argument("--show", type=int, default=SHOW, metavar="K")
    ap.add_argument("--root", default=ROOT)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        res = resolve(a, dater or blame_dater)
    except Refusal as e:
        print("REFUSING: %s" % DM.shown(str(e), 2000), file=out)
        return 2
    report(res, a, out, sys.stderr if err is None else err)
    return 0


# ----------------------------------------------------------------- self-test
A1 = ["# A, the cited document",
      "",
      "Alpha row: the loader region is intact over all of it, bracket 1,024.",
      "",
      "Bravo row: a tool reporting zero is making a claim about its controls.",
      "Charlie row: nothing counts until its refutation condition is written.",
      "Delta row: this line is edited in place and will not survive verbatim.",
      "Echo row: this line stays in A.md and only moves with the insertion.",
      "| --- | --- |",
      "## Notes",
      "Foxtrot row: cited by a log line that a later commit edits in place.",
      "Golf row: moved out into a blockquote, with its whitespace changed."]
A2 = ["Inserted one: a new first line, so every row below moves down.",
      "Inserted two: and a second.",
      "Inserted three: so `A.md:3` now names this line and not Alpha.",
      "# A, the cited document",
      "",
      "Delta row: EDITED in place, so this line does not survive verbatim.",
      "Echo row: this line stays in A.md and only moves with the insertion.",
      "| --- | --- |",
      "## Notes",
      "Foxtrot row: cited by a log line that a later commit edits in place.",
      "| --- | --- |"]
D1 = ["# D", "Juliet row: a file deleted after it was cited, its row kept."]
HIST = ["# A, the rows that moved",
        "",
        "Some new words above the moved rows.",
        A1[2],
        "",
        "More new words between them.",
        A1[4],
        A1[5],
        D1[1]]
GOLF_QUOTED = "> \t" + A1[11].replace(": ", ":   ").replace(", ", ",  ")
GOLF_NBSP = A1[11].replace(" changed", chr(0xA0) + "changed")
OTHER = ["# other", "", "| a | b |", "| --- | --- |", "## Notes", GOLF_NBSP]
C1 = ["# C", "Hotel row: C.md is never edited, so this citation still holds."]
CR1 = b"A\r\nB\rC\nIndia row: a capture line after a bare CR, counted on LF.\n"
CR2 = b"Z\rY\n" + CR1
LOG1 = ["# log",
        "",
        "## 2026-01-01 -- the first entry",
        "Alpha is at `A.md:3`.",
        "The pair is at `A.md:5-6`.",
        "A comma list: `A.md:3,5,8`.",
        "Delta is at `A.md:7`.",
        "The separator is `A.md:9` and the heading is `A.md:10`.",
        "A blank line: `A.md:2`.",
        "Hotel is at `C.md:2`.",
        "Foxtrot is at `A.md:11`.",
        "Golf is at `A.md:12`.",
        "India is at `bench/x.log:3`.",
        "Not yet written: `B.md:1`; past the end: `A.md:40`.",
        "A range the move split: `A.md:6-7`.",
        "Juliet, in a file deleted since: `D.md:2`.",
        "India by its basename: `x.log:3`.",
        "A basename two files share: `dup.md:1`."]
LOG3 = list(LOG1)
LOG3[10] = "Foxtrot is at `A.md:11`, and a later commit edited this sentence."
# R17 and R18: moves.  N1 -> N2 pushes N.md:3's text down by two lines.
N1 = ["# N", "", "Kilo row: the text N.md:3 held when both moves were cited.",
      "Lima row: a second row, so the file has more than one."]
N2 = ["Mike: an inserted first line.", "November: and a second."] + N1
E1 = ["## 2026-01-01 -- the entry that a later commit moves to the end",
      "Kilo is at `N.md:3`, and this sentence is long enough to move whole.",
      "A second line of the same entry, so the moved block has some weight."]
E2 = ["## 2026-01-02 -- a longer entry the diff keeps in place",
      "Papa: an entry that does not cite anything and is several lines long.",
      "Quebec: its second line, long enough to anchor the diff here.",
      "Romeo: its third line, so it outweighs the entry that moves.",
      "Sierra: its fourth line.", "Tango: its fifth line."]
ROW = "| `S-1` | the row cites `N.md:3` for the Kilo claim, moved verbatim |"
S1 = ["# S, a state document", "", "| id | text |", "|---|---|", ROW,
      "| `S-2` | the row that stays behind in the state document |"]


def _text(lines):
    return "\n".join(lines) + "\n"


class _Fixture(object):
    """A throwaway repository.  Its git runs HERMETIC, as docmove's `_repo`:
    no inherited GIT_* variable, an empty global config, no system config, so
    no hook, signing, autocrlf or `blame.ignoreRevsFile` of this host changes
    what is committed or how it is blamed."""

    def __init__(self, tmp, name):
        self.dir = os.path.join(tmp, name)
        os.makedirs(self.dir)
        cfg = os.path.join(tmp, "empty.gitconfig")
        if not os.path.exists(cfg):
            open(cfg, "wb").close()
        self.env = dict((k, v) for k, v in os.environ.items()
                        if not k.startswith("GIT_"))
        self.env.update(GIT_CONFIG_GLOBAL=cfg, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="citeresolve",
                        GIT_AUTHOR_EMAIL="citeresolve@invalid",
                        GIT_COMMITTER_NAME="citeresolve",
                        GIT_COMMITTER_EMAIL="citeresolve@invalid")
        self.shas = []
        self.git("init", "-q")

    def git(self, *args):
        r = subprocess.run([GIT, "-C", self.dir] + list(args),
                           capture_output=True, env=self.env)
        if r.returncode:
            raise RuntimeError("fixture `git %s` rc %d: %s" % (
                args[0], r.returncode,
                r.stderr.decode("utf-8", "replace").strip()))
        return r.stdout

    def commit(self, files, message):
        for rel, data in files.items():
            p = os.path.join(self.dir, rel)
            if data is None:
                os.remove(p)
                continue
            if not os.path.isdir(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            with open(p, "wb") as fh:
                fh.write(data if isinstance(data, bytes)
                         else data.encode("utf-8"))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        self.shas.append(self.git("rev-parse", "HEAD").decode().strip())
        return self.shas[-1]

    def _as_fixture(self, fn):
        saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.env)
        try:
            return fn()
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def run(self, argv, dater=None):
        """In process, under the fixture's environment."""
        buf, err = io.StringIO(), io.StringIO()
        rc = self._as_fixture(lambda: run(argv + ["--root", self.dir], buf,
                                          err, dater=dater))
        return rc, buf.getvalue()

    def blame(self, rel, flags):
        return self._as_fixture(lambda: blame(self.dir, rel, flags))

    def proc(self, argv):
        """A REAL process, so a refusal is read from a real exit code."""
        r = subprocess.run([sys.executable, os.path.abspath(__file__)] + argv,
                           capture_output=True, env=self.env)
        return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def _main_fixture(tmp):
    fx = _Fixture(tmp, "main")
    fx.commit({"A.md": _text(A1), "C.md": _text(C1), "bench/x.log": CR1,
               "D.md": _text(D1), "LOG.md": _text(LOG1),
               "notes/dup.md": "# one of two files named dup.md\n",
               "docs/dup.md": "# the other file named dup.md\n"},
              "one: the log cites A.md")
    fx.commit({"A.md": _text(A2), "hist/A-old.md": _text(HIST),
               "hist/G.md": GOLF_QUOTED + "\n", "notes/other.md": _text(OTHER),
               "B.md": "# B, which exists only from the second commit\n",
               "bench/x.log": CR2, "D.md": None}, "two: rows move out")
    fx.commit({"LOG.md": _text(LOG3)}, "three: a log line is edited")
    return fx


def _blocks(out):
    """-> {citing line: [block text]}, one entry per element, in order."""
    got = collections.defaultdict(list)
    for chunk in out.split("\n\n"):
        m = re.match(r"^\S+:(\d+)  ", chunk)
        if m:
            got[int(m.group(1))].append(chunk)
    return got


def _now(chunk):
    return [ln.split("now      ", 1)[1].split("  (")[0]
            for ln in chunk.split("\n") if ln.startswith("    now      ")]


def _verdict_of(chunk):
    m = re.search(r"^    verdict  (.*)$", chunk, re.M)
    return m.group(1) if m else None


def _dated(chunk):
    m = re.search(r"^    dated    ([0-9a-f]{8}) ", chunk, re.M)
    return m.group(1) if m else None


def _where(lines, text):
    return lines.index(text) + 1


def r1(fx, dater=None):
    rc, out = fx.run(["LOG.md:4"], dater)
    b = _blocks(out).get(4, [""])[0]
    want = "hist/A-old.md:%d" % _where(HIST, A1[2])
    good = (rc == 0 and ("text     " + A1[2]) in b and _now(b) == [want]
            and _verdict_of(b) == "one" and _dated(b) == fx.shas[0][:8])
    return good, "rc %d, now %s, want %s" % (rc, _now(b), want)


def r2(fx, dater=None):
    rc, out = fx.run(["LOG.md:5"], dater)
    b = _blocks(out).get(5, [""])[0]
    s = _where(HIST, A1[4])
    want = "hist/A-old.md:%d-%d" % (s, s + 1)
    good = (rc == 0 and _now(b) == [want] and _verdict_of(b) == "one"
            and "(+1 more line)" in b)
    return good, "rc %d, now %s, want %s" % (rc, _now(b), want)


def r3(fx, dater=None):
    lit = "A.md:3,5,8"
    seen = [m.group(0) for m in CC.CITE_RX.finditer(LOG1[5])]
    rc, out = fx.run(["LOG.md:6"], dater)
    bs = _blocks(out).get(6, [])
    got = [_now(b) for b in bs]
    want = [["hist/A-old.md:%d" % _where(HIST, A1[2])],
            ["hist/A-old.md:%d" % _where(HIST, A1[4])],
            ["A.md:%d" % _where(A2, A1[7])]]
    good = (rc == 0 and seen == ["A.md:3"] and got == want
            and all("of 3 in `%s`" % lit in b for b in bs))
    return good, ("citecheck's CITE_RX sees %s; here %d element(s), now %s"
                  % (seen, len(bs), got))


def r4(fx, dater=None):
    rc, out = fx.run(["LOG.md:7", "LOG.md:15"], dater)
    bl = _blocks(out)
    b, split = bl.get(7, [""])[0], bl.get(15, [""])[0]
    v, w = _verdict_of(b) or "", _verdict_of(split) or ""
    # The split range: its first line IS in hist/A-old.md, and only the
    # intact-block rule keeps that from being reported as where it went.
    first_moved = A1[5] in HIST
    return (rc == 0 and v.startswith("not found verbatim") and not _now(b)
            and ("text     " + A1[6]) in b and first_moved
            and w.startswith("not found verbatim") and not _now(split)), (
        "rc %d; changed line: %s; range whose first line moved: %s"
        % (rc, v[:18], w[:18]))


def r5(fx, dater=None):
    rc, out = fx.run(["LOG.md:8-9"], dater)
    bl = _blocks(out)
    sep, head = (bl.get(8, []) + ["", ""])[:2]
    blank = bl.get(9, [""])[0]
    vs = [_verdict_of(x) or "" for x in (sep, head, blank)]
    good = (rc == 0 and vs[0].startswith("ambiguous -- 3 matches for a table "
                                         "separator")
            and vs[1].startswith("ambiguous -- 2 matches for text of 8")
            and vs[2].startswith("ambiguous -- blank at"))
    return good, "rc %d: %s" % (rc, " | ".join(v[:34] for v in vs))


def r6(fx, dater=None):
    rc, out = fx.run(["LOG.md:10"], dater)
    b = _blocks(out).get(10, [""])[0]
    return (rc == 0 and _verdict_of(b) == "one"
            and "    now      C.md:2  (the cited line, unchanged)" in b
            and "still at the cited line 1" in out), "rc %d" % rc


def r7(fx, dater=None):
    rc, out = fx.run(["LOG.md"], dater)
    bl = _blocks(out)
    vs = [_verdict_of(x) or "" for x in bl.get(14, [])]
    good = (rc == 0 and len(vs) == 2
            and vs[0].startswith("refused -- `B.md` is not a file in the tree")
            and vs[1].startswith("refused -- line 40 is past the end of A.md, "
                                 "which had 12 lines")
            and _verdict_of(bl.get(4, [""])[0]) == "one"
            and "19 citation element(s) on 15 citing line(s)" in out
            and "refused: absent at the citing commit 1,  a suffix of two "
                "paths 1,  past the end 1" in out)
    return good, "rc %d; line 14: %s" % (rc, [v[:30] for v in vs])


def r8(fx, dater=None):
    tmp = os.path.dirname(fx.dir)
    bare = os.path.join(tmp, "not-a-repo")
    os.makedirs(bare, exist_ok=True)
    shallow = os.path.join(tmp, "shallow")
    fx.git("clone", "-q", "--depth", "1", "file://" + fx.dir, shallow)
    with open(os.path.join(fx.dir, "untracked.md"), "wb") as fh:
        fh.write(b"cites `A.md:3`\n")
    try:
        runs = [("not a repository", ["LOG.md", "--root", bare],
                 "not a git repository"),
                ("untracked", ["untracked.md", "--root", fx.dir],
                 "not tracked at HEAD"),
                ("past the end", ["LOG.md:99", "--root", fx.dir],
                 "has 18 lines at HEAD"),
                ("shallow", ["LOG.md", "--root", shallow], "SHALLOW"),
                ("no such date", ["LOG.md", "--date", "2026-01-04", "--root",
                                  fx.dir], "no entry headed"),
                ("no such rev", ["LOG.md", "--rev", "nosuchrev", "--root",
                                 fx.dir], "is not a commit")]
        got = []
        for name, argv, why in runs:
            rc, out = fx.proc(argv)
            got.append((name, rc == 2 and "REFUSING: " in out and why in out
                        and "Traceback" not in out))
    finally:
        os.remove(os.path.join(fx.dir, "untracked.md"))
    bad = [n for n, g in got if not g]
    return not bad, "%d of %d refused with their reason%s" % (
        len(got) - len(bad), len(got), "; NOT: %s" % bad if bad else "")


def r9(fx, dater=None):
    rc, out = fx.run(["LOG.md:12"], dater)
    b = _blocks(out).get(12, [""])[0]
    return (rc == 0 and _now(b) == ["hist/G.md:1"] and _verdict_of(b) == "one"
            and GOLF_NBSP != A1[11]), "rc %d, now %s" % (rc, _now(b))


def r10(fx, dater=None):
    rc, out = fx.run(["LOG.md:13"], dater)
    b = _blocks(out).get(13, [""])[0]
    lf = CR2.split(b"\n").index(CR1.split(b"\n")[2]) + 1
    uni = CR2.decode().splitlines().index(CR1.decode().splitlines()[-1]) + 1
    return (rc == 0 and lf != uni and _now(b) == ["bench/x.log:%d" % lf]), (
        "now %s; `\\n` says %d, splitlines() %d" % (_now(b), lf, uni))


def r11(fx, dater=None):
    rc, out = fx.run(["LOG.md:4", "--rev", fx.shas[1]], dater)
    b = _blocks(out).get(4, [""])[0]
    return (rc == 0 and ("text     " + A2[2]) in b and "--rev" in b
            and _dated(b) == fx.shas[1][:8]), "rc %d" % rc


def r12(fx, dater=None):
    rc, out = fx.run(["LOG.md:4", "LOG.md:11"], dater)
    bl = _blocks(out)
    b4, b11 = bl.get(4, [""])[0], bl.get(11, [""])[0]
    good = (rc == 0 and "RE-DATED" not in b4 and "RE-DATED" in b11
            and ("finds it first at %s" % fx.shas[0][:8]) in b11
            and _dated(b11) == fx.shas[2][:8]
            and ("text     " + A2[10]) in b11)
    return good, "rc %d; line 11 re-dated %s" % (rc, "RE-DATED" in b11)


def r13(fx, dater=None):
    tmp = os.path.dirname(fx.dir)
    e1 = ["## 2026-01-02 -- morning", "Alpha is at `A.md:3`.", ""]
    e2 = ["## 2026-01-03 -- the next day", "Bravo is at `A.md:5`.", ""]
    e3 = ["## 2026-01-02 -- evening, the same date", "Charlie: `A.md:6`.", ""]
    sets = []
    for name, order in (("date-a", [e1, e2, e3]), ("date-b", [e2, e3, e1])):
        f = _Fixture(tmp, name)
        f.commit({"A.md": _text(A1),
                  "LOG.md": _text(["# log", ""] + sum(order, []))}, "one")
        got = []
        for d in ("2026-01-02", "2026-01-03"):
            rc, out = f.run(["LOG.md", "--date", d])
            got.append((rc, sorted((c.split("\n")[0].split("  ")[1],
                                    _verdict_of(c))
                                   for cs in _blocks(out).values()
                                   for c in cs)))
        sets.append(got)
    want = [(0, [("A.md:3", "one"), ("A.md:6", "one")]),
            (0, [("A.md:5", "one")])]
    return sets[0] == sets[1] == want, "both orders: %s" % sets[0]


def r14(fx, dater=None):
    """The mutation control: date every citation at HEAD."""
    cases = [("R1", r1), ("R2", r2), ("R3", r3)]
    red = [n for n, f in cases if not f(fx)[0]]
    if red:
        return False, "unmutated control is already red: %s" % red
    head = fx.shas[-1]

    def at_head(root, rel, lines):
        return dict((n, (head, rel, n)) for n in lines)
    survived = [n for n, f in cases if f(fx, at_head)[0]]
    return not survived, "dated at HEAD, %d of %d go red%s" % (
        len(cases) - len(survived), len(cases),
        "; SURVIVED %s" % survived if survived else "")


def r15(fx, dater=None):
    rc1, text = fx.run(["LOG.md"], dater)
    rc2, tsv = fx.run(["LOG.md", "--tsv"], dater)
    rows = [r.split("\t") for r in tsv.rstrip("\n").split("\n")]
    tv = [_verdict_of(c).split(" -- ")[0].replace(" ", "-")
          for cs in [v for _k, v in sorted(_blocks(text).items())]
          for c in cs]
    col = TSV_COLUMNS.index("verdict")
    # A location list long enough that a cell cut at a fixed width would end
    # inside a path: every entry must parse, and there must be all of them.
    f = _Fixture(os.path.dirname(fx.dir), "wide")
    f.commit({"W.md": _text(["| --- | --- |"] * 60),
              "LOG.md": _text(["# log", "`W.md:1`"])}, "one")
    rc3, wide = f.run(["LOG.md", "--tsv", "--show", "1000"])
    wr = [r.split("\t") for r in wide.rstrip("\n").split("\n")][1:]
    locs = wr[0][TSV_COLUMNS.index("locations")].split(";") if wr else []
    parsed = [x for x in locs if re.match(r"^W\.md:\d+$", x)]
    good = (rc1 == rc2 == rc3 == 0 and tuple(rows[0]) == TSV_COLUMNS
            and all(len(r) == len(TSV_COLUMNS) for r in rows)
            and [r[col] for r in rows[1:]] == tv and len(tv) == 19
            and len(parsed) == len(locs) == 60 and len(";".join(locs)) > 400)
    return good, "%d row(s) of %d column(s); a %d-entry location list, %d " \
        "parsed" % (len(rows) - 1, len(TSV_COLUMNS), len(locs), len(parsed))


def r16(fx, dater=None):
    lines = [b"a b", b"a  b", b"\ta\tb\r", b"> a b", b"> > a\tb", b">a b",
             b" \t> a b ", b">\t>  a \x0b b\x0c", b"ab", b"a\xc2\xa0b",
             b"a\xe3\x80\x80b", b"\xef\xbb\xbfa b", b">", b"", b"> >", b"a>b",
             b"| --- | --- |", b"|---|---|", b"  | --- |   --- |  "]
    for p in (os.path.abspath(__file__), os.path.join(HERE, "docmove.py"),
              os.path.join(HERE, "citecheck.py")):
        with open(p, "rb") as fh:
            lines.extend(fh.read().split(b"\n"))
    groups = collections.defaultdict(set)
    for raw in lines:
        groups[norm(raw.decode("utf-8"))].add(key(raw))
    split = [g for g, ks in groups.items() if len(ks) > 1]
    nbsp = norm("a" + chr(0xA0) + "b") != norm("a b")
    # The declared exception, asserted so it cannot change unnoticed: two
    # different bytes that are not UTF-8 decode alike and key apart.
    bad = (norm(b"a \xff b".decode("utf-8", "replace"))
           == norm(b"a \xfe b".decode("utf-8", "replace"))
           and key(b"a \xff b") != key(b"a \xfe b"))
    return (not split and nbsp and bad and len(groups["a b"]) == 1
            and len(lines) > 1000), (
        "%d UTF-8 lines, %d normalised forms, %d with two keys; U+00A0 is "
        "text: %s; non-UTF-8 bytes kept apart: %s"
        % (len(lines), len(groups), len(split), nbsp, bad))


def r17(fx, dater=None):
    """`10b8fbc6`, reproduced: an entry moved to the end of the log."""
    f = _Fixture(os.path.dirname(fx.dir), "move-in-file")
    c1 = f.commit({"N.md": _text(N1),
                   "LOG.md": _text(["# log", ""] + E1 + [""] + E2)}, "one")
    f.commit({"N.md": _text(N2)}, "two: N.md grows at the top")
    c3 = f.commit({"LOG.md": _text(["# log", ""] + E2 + [""] + E1)},
                  "three: the first entry moves to the end, nothing else")
    n = 2 + len(E2) + 1 + 2
    plain = f.blame("LOG.md", ())
    rc, out = f.run(["LOG.md:%d" % n], dater)
    b = _blocks(out).get(n, [""])[0]
    good = (plain.get(n, ("",))[0] == c3 and _dated(b) == c1[:8]
            and ("text     " + N1[2]) in b and _now(b) == ["N.md:5"]
            and "RE-DATED" not in b)
    return good, "plain blame dates the moved line %s (the move is %s); " \
        "here %s, now %s" % (plain.get(n, ("?",))[0][:8], c3[:8], _dated(b),
                             _now(b))


def r18(fx, dater=None):
    """`R1y`, reproduced: a row moved verbatim into a history file."""
    f = _Fixture(os.path.dirname(fx.dir), "move-across-files")
    c1 = f.commit({"N.md": _text(N1), "S.md": _text(S1)}, "one")
    f.commit({"N.md": _text(N2)}, "two: N.md grows at the top")
    hist = ["# S, rows moved here verbatim", "", "| id | text |", "|---|---|",
            ROW]
    c3 = f.commit({"S.md": _text([x for x in S1 if x != ROW]),
                   "hist/S-old.md": _text(hist)}, "three: the row moves")
    n = _where(hist, ROW)
    m_only = f.blame("hist/S-old.md", ("-M",))
    rc, out = f.run(["hist/S-old.md:%d" % n], dater)
    b = _blocks(out).get(n, [""])[0]
    good = (m_only.get(n, ("",))[0] == c3 and _dated(b) == c1[:8]
            and "traced to S.md:%d" % _where(S1, ROW) in b
            and ("text     " + N1[2]) in b and _now(b) == ["N.md:5"])
    return good, "-M alone dates the moved row %s (the move is %s); here " \
        "%s, now %s" % (m_only.get(n, ("?",))[0][:8], c3[:8], _dated(b),
                        _now(b))


def r19(fx, dater=None):
    """A file deleted since: citecheck's own scan, which resolves paths in
    HEAD's tree, drops this citation as `unresolved` before any oracle runs."""
    rc, out = fx.run(["LOG.md:16"], dater)
    b = _blocks(out).get(16, [""])[0]
    want = "hist/A-old.md:%d" % _where(HIST, D1[1])
    gone = fx.git("ls-tree", "-r", "--name-only", "HEAD").decode().split()
    good = (rc == 0 and "D.md" not in gone and _dated(b) == fx.shas[0][:8]
            and "    read     D.md:2 at " in b and _now(b) == [want]
            and _verdict_of(b) == "one")
    return good, "rc %d, now %s, want %s" % (rc, _now(b), want)


def r20(fx, dater=None):
    """A basename, resolved in the citing commit's tree, as citecheck
    resolves one in HEAD's; two candidates are refused, never picked."""
    rc, out = fx.run(["LOG.md:17-18"], dater)
    bl = _blocks(out)
    b17, b18 = bl.get(17, [""])[0], bl.get(18, [""])[0]
    v = _verdict_of(b18) or ""
    good = (rc == 0 and "    read     bench/x.log:3 at " in b17
            and "(`x.log` by suffix)" in b17 and _now(b17) == ["bench/x.log:4"]
            and v.startswith("refused -- `dup.md` is a suffix of 2 paths"))
    return good, "rc %d, x.log now %s; dup.md: %s" % (rc, _now(b17), v[:40])


def r21(fx, dater=None):
    """One commit that both cites a file and changes it; one that cites a
    line its own commit cut off; one that cites a file it did not touch."""
    f = _Fixture(os.path.dirname(fx.dir), "same-commit")
    log = ["# log", "one: `N.md:3`."]
    f.commit({"N.md": _text(N1), "C.md": _text(C1), "LOG.md": _text(log)},
             "one")
    log += ["two: `N.md:3` again.", "two-b: `C.md:1`, a line two left alone."]
    c2 = f.commit({"N.md": _text(N2), "C.md": _text(C1 + ["appended."]),
                   "LOG.md": _text(log)}, "two: changes N.md:3 and C.md")
    log += ["three: `N.md:6`.", "four: `C.md:2`."]
    f.commit({"N.md": _text(["# N", "only two lines now."]),
              "LOG.md": _text(log)}, "three")
    rc, out = f.run(["LOG.md"], dater)
    bl = _blocks(out)
    b = dict((n, bl.get(n, [""])[0]) for n in range(2, 7))
    # And a configured blame.ignoreRevsFile is said, where it was not before.
    ign = os.path.join(os.path.dirname(fx.dir), "ignore-revs")
    open(ign, "wb").close()
    f.git("config", "blame.ignoreRevsFile", ign)
    rc2, out2 = f.run(["LOG.md:2"], dater)
    note = "note     blame.ignoreRevsFile is set (%s)" % ign
    good = (rc == 0 and all("    before" not in b[n] for n in (2, 4, 6))
            and ("    before   %s also changed these lines; at its parent "
                 "they began: %s" % (c2[:8], N1[2])) in b[3]
            and ("text     " + N2[2]) in b[3]
            and ("hint     N.md last had line 6 at %s" % c2[:8]) in b[5]
            and "dated by a commit that also changed the cited lines 1" in out
            and rc2 == 0 and note not in out and note in out2)
    return good, "rc %d; before on %s; hint on line 5: %s; ignoreRevsFile " \
        "said: %s" % (rc, [n for n in b if "    before" in b[n]],
                      "hint" in b[5], note in out2)


CASES = [
    ("R1", r1, "a citation reads the cited file at the citing commit, and "
               "finds that text where it moved"),
    ("R2", r2, "a range is found INTACT, as consecutive lines, where it "
               "moved"),
    ("R3", r3, "every element of a comma list is resolved; citecheck's "
               "CITE_RX sees only the first"),
    ("R4", r4, "a line changed in place, and a range the move split, are "
               "`not found verbatim`"),
    ("R5", r5, "a table separator, a short heading and a blank line are "
               "`ambiguous`"),
    ("R6", r6, "an untouched citation is marked `the cited line, "
               "unchanged`"),
    ("R7", r7, "a file absent, or a line past the end, at the citing commit "
               "is refused per citation; the run goes on"),
    ("R8", r8, "every global refusal exits 2 with its reason, from a real "
               "process"),
    ("R9", r9, "docmove's normalisation: a re-quoted, re-spaced copy is "
               "found, a U+00A0 copy is not"),
    ("R10", r10, "a cited file with a bare CR is numbered on `\\n` only"),
    ("R11", r11, "--rev dates every citation at REV"),
    ("R12", r12, "a citing line edited after it was written is flagged "
                 "RE-DATED, with its first commit"),
    ("R13", r13, "--date selects every entry with that date, the same set "
                 "in either order"),
    ("R14", r14, "the dating is load-bearing: dated at HEAD, R1-R3 go red"),
    ("R15", r15, "--tsv carries one row per element, fixed columns, the "
                 "same verdicts, and no cell cut short"),
    ("R16", r16, "the prefilter key never separates lines docmove's "
                 "normalisation joins"),
    ("R17", r17, "an entry moved inside the citing file keeps its date; "
                 "plain blame re-dates it"),
    ("R18", r18, "a row moved into a history file keeps its date; blame -M "
                 "alone re-dates it"),
    ("R19", r19, "a file deleted since is read in the citing commit's tree, "
                 "and found where its row went"),
    ("R20", r20, "a basename resolves by suffix in the citing commit's tree; "
                 "two candidates are refused"),
    ("R21", r21, "a dating commit that changed the cited lines shows their "
                 "parent; past the end names where they last were; a set "
                 "blame.ignoreRevsFile is said"),
]


def case_line(good, name, text):
    print("  %s  %-4s %s" % ("ok  " if good else "FAIL", name, text))


def self_test():
    print("citeresolve %s self-test  --  %d controls, each one able to fail"
          % (VERSION, len(CASES)))
    tmp = tempfile.mkdtemp(prefix="citeresolve-")
    passed = 0
    try:
        fx = _main_fixture(tmp)
        for name, fn, text in CASES:
            try:
                good, detail = fn(fx)
            except Exception as e:   # a control that crashes is one that fails
                good, detail = False, "raised %s: %s" % (type(e).__name__, e)
            case_line(good, name, "%s (%s)" % (
                text, DM.shown(DM.normalise(str(detail)), 400)))
            passed += 1 if good else 0
    except Exception as e:
        print("  FAIL  R0   the fixture could not be built (%s: %s)"
              % (type(e).__name__, DM.shown(str(e), 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("%d of %d ok" % (passed, len(CASES)))
    return 0 if passed == len(CASES) else 1


def main(argv):
    for k in GIT_REDIRECTS:
        os.environ.pop(k, None)
    if argv == ["--self-test"]:
        return self_test()
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    return run(argv, sys.stdout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
