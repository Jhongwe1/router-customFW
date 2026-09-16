#!/usr/bin/env python3
"""citecheck -- does a `FILE:NNN` citation in this repository's prose still
point at the row it was written against?

This repository cites its own files by line number.  A line number is the one
kind of citation here that goes wrong SILENTLY: the cited line still exists, so
"does that line exist" passes, and nothing compares the line to what the citing
sentence says is on it.  Insert a paragraph above a cited row and every citation
below it now names a different row, in a file nobody touched, with no diff to
review.

`spec-check`'s `C11` already does this for ONE population -- the payload sources
under `config/rlxfw-src/`, matched by basename, token-checked.  This is the same
idea over every tracked file, and it uses an oracle C11 does not have: git.

THE ORACLE, and what would prove it wrong
-----------------------------------------
For each citation, `git blame` the CITING line to get the commit that last wrote
it; read the cited file AS IT WAS at that commit; take line NNN's content then;
find where that content is NOW.

  STABLE   the same content is still at line NNN
  ROT      it is somewhere else, and the report says where
  CHANGED  that content no longer occurs at all -- undecidable, reported and
           NOT red.  This is the declared blind spot and it is 16 citations
           today; a rewritten line is indistinguishable from a deleted one

🔴 THE ORACLE'S UNIT IS A LINE, AND ANY EDIT TO THAT LINE RESETS IT.
量 2026-09-16 (eightieth segment), by CI going red where the desk was green:
`PROGRESS.md`'s `LEDGER-3` row cites `tools/ledgerscan.py:505` for a line that
moved to `:522` long ago.  That rot was KNOWN and on the baseline.  The segment
appended a re-ownership note to a DIFFERENT CELL of the same row -- and because
blame is per LINE, the citing line's blame moved to today, so the oracle read
today's file against today's line number and called it STABLE.  `C4` caught it,
because the baseline is swept in both directions and a row that stops naming a
finding is reported.

  * **The baseline header says *repair the citation and the blame moves*.  It
    does not say that ANY edit to the citing line moves it, and that is the
    gap.**  The damage is bounded -- laundering can only hide rot that was
    already rot, and the baseline is the register of exactly those -- but rot
    that is NEW in the same commit that edits its row is laundered and never
    recorded.  There is no control for that case.
  * **In this repository a line is not a sentence.**  量 2026-09-16: 117
    citations live on 64 lines of `PROGRESS.md`, and one table row carries
    NINE.  Touching one cell re-blames all of them.
  * 🔴 **And the desk cannot see any of it.**  On a dirty tree this tool
    says so -- *their baseline rows are suspended* -- and suspends every
    baseline row belonging to a modified citing file.  A closeout run at a desk
    with twenty edited rows is a run with those rows switched off.  **Run it
    again after the commit, on the clean tree, before pushing.**  That is what
    CI does and it is why CI saw this and the desk did not.

REFUTATION CONDITIONS, written before the code:

  * If this tool reports ~100 % STABLE, it is measuring nothing.  量 2026-09-15:
    on a `--depth 1` clone `git blame PROGRESS.md` attributes every line to ONE
    commit where a full clone attributes them to 132, so the "cited file at the
    citing commit" is the cited file NOW and every citation is trivially stable.
    That is a tool that cannot fail, so a shallow repository is a REFUSAL and
    not a clean report.  `T3`.
  * If the oracle is right, a citation it calls ROT must be one a human reading
    the citing sentence agrees is now pointing at the wrong row.  Three were
    checked by hand before this was written; the third is the argument for the
    whole tool.  `SPEC.md:149` and `docs/rlx-cache-and-cp0.md:855` both cite
    `notes/cache-model.md:904` for the words *no measurement exists*.  That text
    is at 917.  Line 904 is now blank and 905 is the heading
    `## The geometry is measured -- 2026-08-29, on silicon`, so a reader
    following the citation lands on text reading as the opposite of the claim it
    was cited to support.
  * If the oracle is WRONG, the way it will be wrong is by calling a citation
    ROT that was never right in the first place, or by finding the content
    somewhere it does not mean.  Both are separated rather than argued:
    a cited line that was BLANK at write time is its own bucket (3 today), and
    content that now occurs at more than one line is reported with every
    candidate instead of the nearest one.
  * A check whose live reading is 0 -- ambiguity, past-EOF, inverted range, URL
    host:port -- is a claim, so each has a SYNTHETIC positive control in
    `--self-test` and none of them rests on "there are none today".

WHAT IT MEASURED WHEN IT WAS WRITTEN, AND THE FALSE FINDING IT MADE FIRST
------------------------------------------------------------------------
🔴 The first working version of this oracle reported 76 ROT.  Nineteen of them
were its own defect and every one of the nineteen was a capture log under
`bench/`, every one displaced by a negative amount.  量: `git show` read through
`subprocess(text=True)` goes through Python's universal-newline translation,
which turns a BARE `\r` into a line break.  `bench/2026-08-23/B.log` is 39 lines
of bytes and 59 lines that way -- this project's own captures carry bare `\r`
(`FW-49`: ash's line editor wraps the echo), so the two sides of the comparison
were numbering the same file differently.  Both sides now read BYTES and split
on `\n` only, which is what `grep -n`, `sed -n` and `awk` do and therefore what
a reader following a citation will see.  `T19` is that fixture, and it is the
most valuable control here because it is the one that reproduces a wrong answer
this tool actually gave.

⚠️ It leaves a real limit standing, stated rather than hidden: in a file holding
a bare `\r` the phrase "line N" is not well defined -- an editor and `sed -n`
disagree -- and the run prints how many cited files are in that state.  Seven
are.

量 2026-09-15 over HEAD: 1,119 `FILE:NNN` tokens in 138 tracked `.md` files;
239 live after the fence mask, the false-positive filters and `SRCREF_EXEMPT`;
163 STABLE, 53 ROT, 4 ROT at a line whose content now occurs more than once,
16 CHANGED, 3 blank-at-write-time.

WHAT IT DOES NOT DO
-------------------
  * It cannot tell whether a citation was CORRECT when it was written.  It
    compares the cited row then with the cited row now; a citation that named
    the wrong line from the start is STABLE here.
  * A range `FILE:NNN-MMM` is oracled on NNN only.  MMM is checked for being
    past end of file and for being less than NNN, and that is all.
  * An extensionless file is invisible to the scanner -- `Makefile:163` in
    `notes/kernel-build.md` is the one live instance and it is DECLARED rather
    than chased, because accepting a bare word before a colon is what makes
    `mips:3000` and `bits-31:4` into citations.  `T21`.
  * `src-vendor/` is a symlink and `upstream/` a gitlink, so citations into
    either resolve to nothing and are counted, not checked.  They are pinned and
    do not rot; that is the reason, and it stops being true the day a pin moves.
  * `_norm` collapses whitespace, so two lines differing only in indentation are
    the same line to this tool.  That direction loses findings, never invents
    them.

THE BASELINE, AND WHY IT IS KEYED ON CONTENT
--------------------------------------------
57 citations are rotted today and several sit in `PROGRESS.md` rows that frozen
bench cards pin BY LINE NUMBER, so they cannot all be repaired without
destroying the evidence `check-predictions` reads.  `tools/citecheck-baseline.tsv`
records them, and the gate fails on anything NEW.

🔴 A baseline keyed on a line number would rot exactly like the thing it
describes.  Each row is keyed on (kind, citing file, cited path, cited line,
sha256 of the cited row's content AT WRITE TIME).  Repair the citation and the
citing line's blame moves, the content at write time changes, and the row stops
matching -- which is reported, because the sweep runs in BOTH directions:

  C3  every finding is on the baseline        -- a new rot is red
  C4  every baseline row still names a finding -- a repaired or stale row is
      red, so the list cannot accrete unread.  This is `cardcheck`'s `B10` rule
      and `spec-check`'s `T22` rule: an exemption that is not load-bearing comes
      out rather than sitting there forever

`--write-baseline` prints a fresh table to STDOUT and never writes the file in
place, so adopting one is a deliberate act with a diff to review.

FALSE POSITIVES, each with a control
------------------------------------
  1  URL `host:port`         0 live -- synthetic control `T6`
  2  clock `HH:MM(:SS)`      1,218 in the corpus, rejected by needing a dotted
                             extension; `T7`
  3  hex range `0x..:0x..`   1 live, rejected the same way; `T8`
  4  histogram `{0.01:18}`   2, rejected because the character after the dot
                             must be a letter; `T9`
  5  transcript `F:N: text`  9 in the corpus -- quoted grep or compiler
                             output ABOUT A PAST STATE of a file.  Checking it
                             against today's file is guaranteed wrong.  FIVE of
                             the nine are inside a fence and the mask takes
                             them first, so 4 reach this filter and 3 are in
                             scope; the run prints the in-scope number.
                             `T10`, both directions
  6  fenced code blocks      14 in the corpus, 7 in scope, killed by
                             `spec-check`'s `fence_mask`; `T5`
  7  self-reference          this tool's report lines have the shape it scans
                             for, and they get pasted into the log.
                             `ledgerscan` went red exactly this way.  Any prose
                             line carrying a `CITE-*` token is skipped; `T11`
  8  basename ambiguity      181 citations resolve by SUFFIX, 48 of them into
                             `config/rlxfw-src/`, which mirrors the vendor
                             layout.  A path matching more than one tracked file
                             is REFUSED, never resolved -- `rlxfw-marks.py`'s
                             rule that an anchor occurs exactly once or the tool
                             declines.  0 live today, 4 in `LOG.md` (exempt),
                             all `README.md`; `T12`
  9  escape mismatch         `docs/isa-hazard.md:366` quotes a token containing
                             a literal `\t` where the `.tsv` holds a real tab.
                             The citation is correct and the comparator is
                             wrong, so `M4` decodes escapes; `T13`.  量: 20
                             citations carry a `(token)` tail and BOTH spellings
                             occur -- `SPEC.md:132` cites the same `.tsv` row
                             with a REAL tab in the markdown.  The run prints
                             that 20, because `0 findings` over a population of
                             0 and over a population of 20 are otherwise the
                             same line

Usage
-----
    citecheck.py [--root DIR]        controls, then the live sweep
    citecheck.py --self-test         the controls only
    citecheck.py --write-baseline    a fresh baseline table on stdout

Exit: 0 clean, 1 findings, 2 refusal.
"""
import binascii
import collections
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

try:                                    # a CJK repository through a cp950 pipe
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                       # pragma: no cover - 3.6 and earlier
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, "citecheck-baseline.tsv")


def _refuse(msg, code=2):
    print("REFUSING: " + msg)
    sys.exit(code)


def _load_spec_check():
    """`fence_mask`, `code_spans`, `_norm` and `SRCREF_EXEMPT` are spec-check's,
    and they are IMPORTED rather than restated.

    A second copy of the fence parser would be a second thing to keep right, and
    the reason this repository has a fence parser at all is that a throwaway one
    swallowed a file.  spec-check executes nothing at import but `HERE`/`ROOT`.
    """
    path = os.path.join(HERE, "spec-check.py")
    if not os.path.exists(path):
        _refuse(f"{path} is not there. Every filter here is spec-check's and "
                f"restating them would be a second copy to keep right")
    spec = importlib.util.spec_from_file_location("_citecheck_spec_check", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        _refuse(f"spec-check.py does not PARSE on this interpreter "
                f"({sys.version.split()[0]}): {e}. It carries an f-string with "
                f"a backslash in the expression part, which is legal from 3.12. "
                f"Run this under WSL's /usr/bin/python3")
    return mod


SC = _load_spec_check()

# 🔴 The path part must carry a DOTTED EXTENSION whose first character is a
# letter, and that single requirement is what rejects false-positive classes
# 2, 3 and 4 with no special case for any of them:
#
#   14:48                   no dot                  -> 1,218 rejected
#   0x80188000:0x8018C000   no dot                  -> 1 rejected
#   {0.01:18}               the dot is followed by a digit -> 2 rejected
#   bits-31:4, mips:3000    no dot
#
# It also costs class 10: `rtl8192cd/Makefile:163` has no extension and is not
# seen.  That is one live citation and it is declared, because the alternative
# -- accepting a bare word before a colon -- is what the three lines above are
# rejecting.
#
# 🔴 THE LOOKBEHIND IS WHAT CLOSES CLASS 1, AND THE EXPLICIT URL FILTER THAT
# USED TO SIT IN scan_file() HAS BEEN DELETED BECAUSE IT COULD NOT FIRE.
# 量 2026-09-15, by mutation: removing that filter killed nothing, because `/`
# is in the lookbehind's class, so in `https://example.com:8080` the only
# position where `example.com:8080` could start is preceded by `/` and is
# rejected before any filter runs.  The same is true of every deeper URL --
# `https://host/tools/spec-check.py:143` offers `tools/...` and
# `spec-check.py` as starts and both are preceded by `/`.  The count it
# maintained read 0 on every run and would have gone on reading 0 with the
# check deleted, which is this repository's own rule about a tool that cannot
# fail, inside this tool.
#
# ⚠️ And there is a SECOND reason a URL cannot become a finding, found the same
# way: a host name resolves to no tracked file, so even a scanned one is
# counted `unresolved` and never oracled.  That matters because it means `T6`
# cannot be written as "the finding count did not move" -- it would pass with
# the lookbehind gone.  It reads the `unresolved` counter instead, which is
# where a scanned URL would actually show up, and `M9` mutates the lookbehind.
CITE_RX = re.compile(
    r'(?<![0-9A-Za-z_./+-])'
    r'((?:[A-Za-z0-9_.+-]+/)*[A-Za-z0-9_+-]+\.[A-Za-z][A-Za-z0-9_+-]*)'
    r':(\d+)(?:-(\d+))?'
    r'(?![0-9])')

# Class 7.  This tool's own findings have the shape this tool scans for, and
# they are written into the log by hand.  `ledgerscan` has gone red exactly this
# way.  Every report line carries one of these tokens and every prose line
# carrying one is skipped, so a pasted report cannot become a population.
SELFREF_RX = re.compile(r'\bCITE-(?:ROT|MULTI|CHANGED|BLANK|AMBIG|M1|M2|M3|M4)\b')

# Class 9.  The house convention for a citation that has to survive a rewrite is
# `path:NNN (a token from that line)` -- spec-check's C11.  Inside a `.md` a tab
# is written `\t`; inside the `.tsv` it is a tab.  Decoding is what lets a `.tsv`
# be quoted at all.
TOKEN_RX = re.compile(r'^\s*\((.+)\)\s*$')
TOKEN_TOL = 3

ESCAPES = (("\\\\", "\x00"), ("\\t", "\t"), ("\\n", " "), ("\x00", "\\"))


def decode_escapes(s):
    for a, b in ESCAPES:
        s = s.replace(a, b)
    return s


# ---------------------------------------------------------------- git, in bytes
def git(root, *args):
    """Bytes in, bytes out.  Never `text=True`.

    量 2026-09-15: `text=True` applies universal-newline translation, and a bare
    `\r` -- which this project's own captures are full of -- becomes a line
    break.  It read `bench/2026-08-23/B.log` as 59 lines where the file has 39,
    and produced nineteen rotted citations that were not rotted.
    """
    r = subprocess.run(["git", "-C", root] + list(args), capture_output=True)
    return r.returncode, r.stdout


def git_lines(root, *args):
    rc, out = git(root, *args)
    return rc, out.decode("utf-8", "replace").split("\n")


def split_lines(blob):
    """`\n` ONLY, on both sides of every comparison in this file.

    Which convention is right for a file holding a bare `\r` is genuinely
    undecided -- an editor and `sed -n` disagree -- but the two sides must agree
    with EACH OTHER or the comparison measures the convention.  `\n` is the one
    `grep -n`, `sed -n` and `awk` use, so it is the one a reader following a
    citation will land on.
    """
    return blob.decode("utf-8", "replace").split("\n")


def read_lines(root, rel, rev=None):
    if rev:
        rc, out = git(root, "show", f"{rev}:{rel}")
        return None if rc != 0 else split_lines(out)
    try:
        with open(os.path.join(root, rel), "rb") as fh:
            return split_lines(fh.read())
    except OSError:
        return None


def is_shallow(root):
    rc, out = git(root, "rev-parse", "--is-shallow-repository")
    if rc != 0:
        return None
    return out.decode().strip() == "true"


def ls_files(root, pat, rev=None):
    if rev:
        rc, lines = git_lines(root, "ls-tree", "-r", "--name-only", rev)
        if rc != 0:
            return []
        import fnmatch
        return [p for p in lines if p.strip() and fnmatch.fnmatch(p, pat)]
    rc, lines = git_lines(root, "ls-files", pat)
    return [] if rc != 0 else [p for p in lines if p.strip()]


def dirty_files(root):
    """Tracked paths the working tree has changed.

    Needed because the oracle cannot speak about a citing line that is not
    committed: `git blame` gives it the all-zero sha, there is no "the cited
    file as it was at the citing commit", and using the working tree for both
    sides would make every such citation trivially stable -- the shallow-clone
    failure one line at a time.  So those citations are SKIPPED, and C4's
    reverse sweep is suspended for exactly those files rather than reporting
    their baseline rows as repaired.
    """
    rc, lines = git_lines(root, "status", "--porcelain")
    if rc != 0:
        return set()
    out = set()
    for ln in lines:
        if len(ln) < 4:
            continue
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ")[-1]
        out.add(p.strip().strip('"'))
    return out


def blame_shas(root, rel, rev=None):
    """final-line -> sha, from `git blame --incremental`.

    `--incremental` rather than `--line-porcelain` because the porcelain form
    repeats the file's whole content in its output: 量 6.9 MB against 255 KB
    over six of this repository's files, for the same answer.
    """
    rc, out = git(root, "blame", "--incremental",
                  *( [rev] if rev else [] ), "--", rel)
    if rc != 0:
        return None
    shas = {}
    for line in out.decode("utf-8", "replace").split("\n"):
        m = re.match(r'^([0-9a-f]{40}) \d+ (\d+) (\d+)$', line)
        if m:
            sha, first, n = m.group(1), int(m.group(2)), int(m.group(3))
            for k in range(first, first + n):
                shas[k] = sha
    return shas


# ------------------------------------------------------------------ the scanner
Cite = collections.namedtuple(
    "Cite", "src srcline path start end target token")

FILTERS = ("fenced", "transcript", "selfref", "unresolved", "ambiguous")


def suffix_index(tracked):
    idx = collections.defaultdict(list)
    for t in tracked:
        parts = t.split("/")
        for i in range(len(parts)):
            idx["/".join(parts[i:])].append(t)
    return idx


def scan_file(rel, text, tracked_set, idx, counts, ambig_out):
    """Every citation in one file's prose, with the false-positive classes
    counted rather than silently dropped."""
    lines = text.split("\n")
    mask = SC.fence_mask(lines)
    prose = "\n".join("" if mask[i] else ln for i, ln in enumerate(lines))
    spans = list(SC.code_spans(prose))
    out = []
    for m in CITE_RX.finditer(text):
        ln = text.count("\n", 0, m.start()) + 1
        if ln - 1 < len(mask) and mask[ln - 1]:
            counts["fenced"] += 1                                  # class 6
            continue
        if text[m.end():m.end() + 1] == ":":
            counts["transcript"] += 1                              # class 5
            continue
        if SELFREF_RX.search(lines[ln - 1] if ln - 1 < len(lines) else ""):
            counts["selfref"] += 1                                 # class 7
            continue
        path = m.group(1)
        if path in tracked_set:
            target = path
        else:
            cands = idx.get(path, [])
            if len(cands) == 1:
                target = cands[0]
            elif len(cands) > 1:                                   # class 8
                counts["ambiguous"] += 1
                ambig_out.append((rel, ln, path, sorted(cands)))
                continue
            else:
                counts["unresolved"] += 1
                continue
        tok = None
        pos = prose.find(m.group(0), max(0, m.start() - 400))
        if pos >= 0:
            for a, b, content in spans:
                if a <= pos < b:
                    t = TOKEN_RX.match(content[pos - a + len(m.group(0)):])
                    if t:
                        tok = t.group(1)
                    break
        end = int(m.group(3)) if m.group(3) else None
        out.append(Cite(rel, ln, path, int(m.group(2)), end, target, tok))
    return out


def scan(root, rev=None):
    """(citations, filter counts, ambiguous, how many `.md` were walked)."""
    mds = sorted(p for p in ls_files(root, "*.md", rev)
                 if not p.startswith("upstream/"))
    tracked = ls_files(root, "*", rev)
    tracked_set = set(tracked)
    idx = suffix_index(tracked)
    counts = collections.Counter({k: 0 for k in FILTERS})
    counts["exempt"] = 0
    ambig, cites = [], []
    for rel in mds:
        if SC.srcref_exempt(rel):
            counts["exempt"] += 1
            continue
        blob = read_lines(root, rel, rev)
        if blob is None:
            continue
        cites.extend(scan_file(rel, "\n".join(blob), tracked_set, idx,
                               counts, ambig))
    return cites, counts, ambig, len(mds)


# ------------------------------------------------------------------- the oracle
Finding = collections.namedtuple("Finding", "kind cite verdict where digest note")

ZERO = "0" * 40


def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def oracle(root, cites, rev=None):
    """Classify every citation.  Returns (findings, verdict counts, blind)."""
    blame, at, now = {}, {}, {}

    def cur(path):
        if path not in now:
            now[path] = read_lines(root, path, rev)
        return now[path]

    def then(sha, path):
        k = (sha, path)
        if k not in at:
            rc, out = git(root, "show", f"{sha}:{path}")
            at[k] = None if rc != 0 else split_lines(out)
        return at[k]

    v = collections.Counter()
    findings, blind = [], []
    for c in cites:
        if c.src not in blame:
            blame[c.src] = blame_shas(root, c.src, rev)
        shas = blame[c.src]
        if shas is None:
            v["NO-BLAME"] += 1
            continue
        sha = shas.get(c.srcline)
        if sha is None:
            v["NO-BLAME"] += 1
            continue
        if sha == ZERO:
            # The citing line is not committed, so there is no "as it was at
            # the citing commit" to read.  Reported rather than passed: with
            # the working tree as both sides every such citation is trivially
            # stable, which is the shallow-clone failure one line at a time.
            v["UNCOMMITTED"] += 1
            blind.append(("BLANK", c, "the citing line is not committed yet"))
            continue
        old = then(sha, c.target)
        if old is None:
            v["ABSENT-THEN"] += 1
            blind.append(("BLANK", c, f"{c.target} did not exist at {sha[:8]}"))
            continue
        if c.start < 1 or c.start > len(old):
            v["EOF-THEN"] += 1
            blind.append(("BLANK", c, f"line {c.start} was past the end of "
                                      f"{c.target} ({len(old)} lines) when the "
                                      f"citation was written"))
            continue
        orig = SC._norm(old[c.start - 1])
        if not orig:
            v["BLANK-THEN"] += 1
            blind.append(("BLANK", c, f"{c.target}:{c.start} was BLANK at "
                                      f"{sha[:8]}, so there is nothing to "
                                      f"follow"))
            continue
        cl = cur(c.target)
        if cl is None:
            v["ABSENT-NOW"] += 1
            blind.append(("BLANK", c, f"{c.target} is gone"))
            continue
        hits = [k for k, s in enumerate(cl, 1) if SC._norm(s) == orig]
        if c.start <= len(cl) and SC._norm(cl[c.start - 1]) == orig:
            v["STABLE"] += 1
            continue
        if len(hits) == 1:
            v["ROT"] += 1
            findings.append(Finding("ROT", c, "ROT", [hits[0]], digest(orig),
                                    orig[:70]))
        elif len(hits) > 1:
            # Reported with EVERY candidate rather than the nearest one.  A
            # generic row -- `esac`, a table separator -- is still rot, but
            # "it moved to line N" would be an invention.
            v["ROT-MULTI"] += 1
            findings.append(Finding("ROT", c, "MULTI", hits, digest(orig),
                                    orig[:70]))
        else:
            v["CHANGED"] += 1
            blind.append(("CHANGED", c, f"that row's content is nowhere in "
                                        f"{c.target} any more: {orig[:60]!r}"))
    return findings, v, blind


# -------------------------------------------------- the checks that need no git
def secondary(root, cites, rev=None):
    """M1/M2/M3/M4 -- every one of them independent of blame.

    M3 is the one that earns its place: `the cited line is now blank` catches
    rot with no oracle at all, so it still works in a clone the oracle refuses.
    It OVERLAPS the oracle by construction and the overlap is printed.
    """
    out = []
    cache = {}

    def cur(p):
        if p not in cache:
            cache[p] = read_lines(root, p, rev)
        return cache[p]

    for c in cites:
        cl = cur(c.target)
        if cl is None:
            continue
        n = len(cl)
        if c.start > n or (c.end is not None and c.end > n):
            out.append(Finding("M1", c, "EOF", [n], digest(f"eof:{c.target}"),
                               f"{c.target} has {n} lines"))
            continue
        if c.end is not None and c.end < c.start:
            out.append(Finding("M2", c, "INVERTED", [], digest("inv"),
                               f"{c.start}-{c.end} counts backwards"))
            continue
        if not SC._norm(cl[c.start - 1]):
            out.append(Finding("M3", c, "BLANK-NOW", [],
                               digest(f"m3:{c.target}:{c.start}"),
                               f"{c.target}:{c.start} is a blank line"))
        if c.token:
            want = SC._norm(decode_escapes(c.token))
            if not want or "`" in want:
                continue
            lo = max(1, c.start - TOKEN_TOL)
            hi = min(n, c.start + TOKEN_TOL)
            if any(want in SC._norm(cl[k - 1]) for k in range(lo, hi + 1)):
                continue
            where = [k for k, s in enumerate(cl, 1) if want in SC._norm(s)]
            out.append(Finding("M4", c, "TOKEN", where[:4],
                               digest(f"m4:{c.target}:{c.start}:{want}"),
                               f"the quoted token is not within {TOKEN_TOL} "
                               f"lines of {c.start}"))
    return out


# ---------------------------------------------------------------- the baseline
BaseRow = collections.namedtuple("BaseRow", "kind src path start digest note")


def baseline_key(f):
    return (f.kind, f.cite.src, f.cite.target, f.cite.start, f.digest)


def load_baseline(path=BASELINE):
    rows, bad = [], []
    if not os.path.exists(path):
        return rows, bad
    with open(path, "rb") as fh:
        for i, raw in enumerate(split_lines(fh.read()), 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            parts = raw.split("\t")
            if len(parts) < 5:
                bad.append((i, raw))
                continue
            try:
                start = int(parts[3])
            except ValueError:
                bad.append((i, raw))
                continue
            rows.append(BaseRow(parts[0], parts[1], parts[2], start, parts[4],
                                parts[5] if len(parts) > 5 else ""))
    return rows, bad


def baseline_text(findings):
    out = [
        "# tools/citecheck-baseline.tsv -- the rot that was already there.",
        "#",
        "# Generated by `tools/citecheck.py --write-baseline` and reviewed by",
        "# hand.  A row here says: this citation is rotted, it is KNOWN, and it",
        "# is not what this gate is looking for.  The gate fails on anything",
        "# new.",
        "#",
        "# 🔴 KEYED ON CONTENT, NOT ON A LINE NUMBER.  A baseline keyed on the",
        "# line a citation points at would rot exactly like the citations it",
        "# describes.  The key is",
        "#",
        "#     kind  citing-file  cited-path  cited-line  sha256-16",
        "#",
        "# where the digest is of the cited row's content AT THE COMMIT THAT",
        "# LAST WROTE THE CITING LINE.  Repair the citation and the citing",
        "# line's blame moves, the digest changes, and the row stops matching",
        "# -- which citecheck's C4 REPORTS, because a baseline that can only",
        "# grow is a list nobody reads.  Delete the row in the same commit as",
        "# the repair.",
        "#",
        "# The note column is not part of the key.  It is the first 70",
        "# characters of the row as it read when the citation was written, so a",
        "# reviewer can see what the citation was for without running git.",
        "#",
        "# kind\tciting-file\tcited-path\tcited-line\tsha256-16\tthe row, then",
    ]
    # One row per KEY.  A citing line may carry the same citation twice --
    # `PROGRESS.md:1706` writes `SPEC.md:144` in two different sentences -- and
    # two rows saying the same thing is a list that looks longer than it is.
    seen = set()
    for f in sorted(findings, key=lambda f: (f.kind, f.cite.src,
                                             f.cite.srcline, f.cite.target,
                                             f.cite.start)):
        k = baseline_key(f)
        if k in seen:
            continue
        seen.add(k)
        note = " ".join(f.note.split())[:70]
        out.append(f"{f.kind}\t{f.cite.src}\t{f.cite.target}\t{f.cite.start}\t"
                   f"{f.digest}\t{note}")
    return "\n".join(out) + "\n"


# -------------------------------------------------------------------- reporting
class Cases:
    def __init__(self):
        self.ok = self.bad = 0
        self.lines = []

    def case(self, label, good, detail):
        if good:
            self.ok += 1
            self.lines.append("  ok     %-54s %s" % (label, detail))
        else:
            self.bad += 1
            self.lines.append("  FAIL   %s  %s" % (label, detail))

    def dump(self):
        for ln in self.lines:
            print(ln)


def sweep(root=ROOT, baseline_path=BASELINE, rev=None):
    """The live run.  ONE case line per CHECK, never per citation.

    🔴 `ci.yml` records that a census row moving when a capture is added is the
    single largest source of CI failure in this repository -- `test-boot-timeline`
    went red on three consecutive seatings for it.  So the count of `ok` lines
    here is a property of this file and not of the corpus, and `T23` is the
    control: two fixtures whose citation counts differ by an order of magnitude
    must print the same number of cases.
    """
    shallow = is_shallow(root)
    if shallow is None:
        _refuse(f"{root} is not a git repository, or git is not available. "
                f"The oracle is `git blame` and there is no reading without it")
    if shallow:
        _refuse("this is a SHALLOW clone. 量 2026-09-15: on a --depth 1 clone "
                "`git blame PROGRESS.md` attributes every line to 1 commit "
                "against 132 in a full clone, so every citation reads STABLE "
                "and this tool cannot fail. Check out with fetch-depth: 0")

    cites, counts, ambig, nmd = scan(root, rev)
    if nmd == 0:
        _refuse(f"no tracked `.md` under {root}. A sweep over an empty "
                f"population reports 0 findings and means nothing")
    if not cites and not ambig:
        _refuse(f"{nmd} tracked `.md` and not one FILE:NNN citation in any of "
                f"them. That is a scanner that matched nothing, not a clean "
                f"repository")

    findings, v, blind = oracle(root, cites, rev)
    findings += secondary(root, cites, rev)
    rows, bad = load_baseline(baseline_path)
    # 🔴 A baseline row whose CITING FILE is dirty cannot be judged in either
    # direction, because the oracle refused that file's modified lines.  It is
    # SUSPENDED and counted, not silently kept and not reported as repaired.
    suspended = set() if rev else dirty_files(root)

    have = collections.Counter(baseline_key(f) for f in findings)
    want = collections.Counter((r.kind, r.src, r.path, r.start, r.digest)
                               for r in rows)
    new = [f for f in findings if baseline_key(f) not in want]
    stale = [r for r in rows
             if (r.kind, r.src, r.path, r.start, r.digest) not in have
             and r.src not in suspended]
    held = [r for r in rows if r.src in suspended]

    c = Cases()
    c.case("C1  the population is real",
           True,
           f"{len(cites)} citations over {nmd} tracked .md "
           f"({counts['exempt']} files exempt)")
    c.case("C2  no path resolves to more than one tracked file",
           not ambig,
           f"{len(ambig)} ambiguous" if ambig else "0 ambiguous")
    c.case("C3  every rotted citation is on the baseline",
           not new,
           f"{len(new)} NOT on the baseline" if new else
           f"0 new, {len(findings)} known")
    c.case("C4  every baseline row still names a finding",
           not stale and not bad,
           f"{len(stale)} stale, {len(bad)} malformed" if (stale or bad) else
           f"{len(rows)} rows, {len(held)} suspended (citing file dirty)")
    m1 = [f for f in findings if f.kind == "M1"]
    m2 = [f for f in findings if f.kind == "M2"]
    m3 = [f for f in findings if f.kind == "M3"]
    m4 = [f for f in findings if f.kind == "M4"]
    n3 = [f for f in m3 if baseline_key(f) not in want]
    n4 = [f for f in m4 if baseline_key(f) not in want]
    c.case("C5  M1 no citation past the end of its file", not m1, f"{len(m1)}")
    c.case("C6  M2 no range that counts backwards", not m2, f"{len(m2)}")
    c.case("C7  M3 no NEW citation onto a now-blank line", not n3,
           f"{len(n3)} new of {len(m3)}")
    ntok = sum(1 for x in cites if x.token)
    c.case("C8  M4 a quoted token is still beside its line", not n4,
           f"{len(n4)} new of {len(m4)}, over {ntok} citation(s) that carry "
           f"a token")
    c.dump()

    # Four-space indent: NOT a case line.  `ci-census` anchors on exactly two
    # leading spaces, so these numbers are readable without moving a census row.
    print()
    print(f"    verdicts   STABLE {v['STABLE']}  ROT {v['ROT']}  "
          f"ROT-at-a-repeated-row {v['ROT-MULTI']}  CHANGED {v['CHANGED']}")
    print(f"    blind      CHANGED {v['CHANGED']}  blank-at-write-time "
          f"{v['BLANK-THEN']}  uncommitted {v['UNCOMMITTED']}  "
          f"absent-then {v['ABSENT-THEN']}  past-EOF-then {v['EOF-THEN']}")
    if suspended & {c2.src for c2 in cites}:
        print(f"    ⚠ reading the WORKING TREE, and "
              f"{len(suspended & {c2.src for c2 in cites})} citing file(s) are "
              f"modified: their changed lines have no oracle and their "
              f"baseline rows are suspended. `--rev HEAD` reads the committed "
              f"tree instead")
    rotkeys = {(f.cite.src, f.cite.srcline, f.cite.target, f.cite.start)
               for f in findings if f.kind == "ROT"}
    ov = sum(1 for f in m3 if (f.cite.src, f.cite.srcline, f.cite.target,
                               f.cite.start) in rotkeys)
    print(f"    M3         {len(m3)} citations point at a line that is blank "
          f"NOW; {ov} of them the oracle already calls ROT, {len(m3) - ov} it "
          f"does not -- that remainder is what M3 is worth")
    print(f"    filters    fenced {counts['fenced']}  transcript "
          f"{counts['transcript']}  self-reference {counts['selfref']}  "
          f"ambiguous {counts['ambiguous']}  unresolved "
          f"{counts['unresolved']}")
    cr = sorted({f.cite.target for f in findings} |
                {c2.target for c2 in cites})
    crn = [p for p in cr
           if (read_lines(root, p) or []) and any("\r" in s
                                                  for s in read_lines(root, p))]
    print(f"    ⚠ {len(crn)} cited file(s) hold a bare CR, so `line N` in them "
          f"is not well defined; this tool splits on \\n only")

    if new or stale or bad or ambig or m1 or m2:
        print()
        for f in sorted(new, key=lambda f: (f.cite.src, f.cite.srcline)):
            print(f"    CITE-{f.kind:<6s} {f.cite.src}:{f.cite.srcline} cites "
                  f"{f.cite.path}:{f.cite.start} -- "
                  f"{_where(f)}   [{f.note}]")
        for r in stale:
            print(f"    CITE-BLANK    {r.src} -> {r.path}:{r.start} is on the "
                  f"baseline and is NOT a finding any more. Repaired? delete "
                  f"the row. [{r.note}]")
        for i, raw in bad:
            print(f"    CITE-BLANK    baseline line {i} is malformed: {raw!r}")
        for src, ln, path, cands in ambig:
            print(f"    CITE-AMBIG    {src}:{ln} cites `{path}`, which is "
                  f"{len(cands)} tracked files. Write the path from the repo "
                  f"root: {', '.join(cands[:3])}")
        for f in m1 + m2:
            print(f"    CITE-{f.kind}      {f.cite.src}:{f.cite.srcline} -- "
                  f"{f.note}")

    print()
    if c.bad:
        print(f"RESULT: {c.ok} passed, {c.bad} failed")
        return 1
    print(f"RESULT: {c.ok} passed, 0 failed")
    return 0


def _where(f):
    if f.kind != "ROT":
        return f.note
    if f.verdict == "MULTI":
        return (f"that row is now at {f.where} -- it occurs more than once, so "
                f"this names every candidate")
    return f"that row is now at line {f.where[0]}"


# ------------------------------------------------------------------- the controls
def _run(argv, cwd=None):
    """A REAL subprocess, so at least one control reads a real exit code.

    It passes `--sweep-only`.  Without it the child would run the controls --
    including this one -- and recurse forever; 量 2026-09-15, the first draft
    did exactly that and had to be killed.
    """
    r = subprocess.run([sys.executable, os.path.join(HERE, "citecheck.py"),
                        "--sweep-only"] + argv, capture_output=True, cwd=cwd)
    return r.returncode, r.stdout.decode("utf-8", "replace") + \
        r.stderr.decode("utf-8", "replace")


def _repo(d, files, message="one"):
    os.makedirs(d, exist_ok=True)
    for rel, blob in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(blob if isinstance(blob, bytes) else blob.encode("utf-8"))
    for a in (["init", "-q"], ["config", "core.autocrlf", "false"],
              ["config", "core.fileMode", "false"],
              ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        git(d, *a)
    git(d, "add", "-A")
    git(d, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)


def _edit(d, rel, blob, message="two"):
    with open(os.path.join(d, rel), "wb") as fh:
        fh.write(blob if isinstance(blob, bytes) else blob.encode("utf-8"))
    git(d, "add", "-A")
    git(d, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)


def _sweep_out(d, baseline=None):
    """Run the sweep in-process against a fixture and capture its report."""
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = sweep(root=d, baseline_path=baseline or os.path.join(d, ".none"))
    except SystemExit as e:
        rc = e.code
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


BODY = "\n".join(f"line {i}" for i in range(1, 13)) + "\n"


def self_test():
    c = Cases()
    tmp = tempfile.mkdtemp(prefix="citecheck-")

    def d(name):
        return os.path.join(tmp, name)

    def cites(n=1):
        return (f"# fixture\n\nThe thing is at `src/b.txt:{n}` and that is "
                f"that.\n")

    # ---- T1/T2: the positive control the whole tool rests on ----------------
    a = d("t1")
    _repo(a, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(a, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(a)
    c.case("T1  a planted rot is found, and where it went",
           rc == 1 and "now at line 5" in o and "CITE-ROT" in o,
           f"rc={rc} " + ("said line 5" if "now at line 5" in o else o[:80]))

    b = d("t2")
    _repo(b, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(b, "src/b.txt", BODY + "trailing\n")
    rc, o = _sweep_out(b)
    c.case("T2  and an untouched citation is not",
           rc == 0 and "STABLE 1" in o, f"rc={rc}")

    # ---- T3: (a) shallow clone is a REFUSAL, not a clean report -------------
    sh = d("t3")
    src = d("t3src")
    _repo(src, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(src, "src/b.txt", "x\ny\n" + BODY)
    rc0, _ = git(tmp, "clone", "-q", "--depth", "1",
                 "file://" + src.replace(os.sep, "/"), sh)
    ok_sh = is_shallow(sh) is True
    rc, o = _run(["--root", sh])
    c.case("T3  a shallow clone is REFUSED",
           ok_sh and rc == 2 and "REFUSING" in o and "SHALLOW" in o,
           f"shallow={ok_sh} rc={rc}")
    rc2, o2 = _sweep_out(src)
    c.case("T3b and the same tree at full depth is NOT refused",
           rc2 == 1 and "CITE-ROT" in o2,
           f"rc={rc2} -- the refusal is about depth, not about the tree")

    # ---- T4/T22: no git, no population --------------------------------------
    e = d("t4")
    os.makedirs(e)
    rc, o = _run(["--root", e])
    c.case("T4  a directory that is not a repository is REFUSED",
           rc == 2 and "REFUSING" in o, f"rc={rc}")
    g = d("t22")
    _repo(g, {"src/b.txt": BODY})
    rc, o = _sweep_out(g)
    # 🔴 The exit code alone is not enough: with this refusal deleted the NEXT
    # one fires and the code is 2 either way.  量 by mutation -- `M2` survived
    # a version of this case that read only rc.
    c.case("T22 a repository with no tracked .md is REFUSED",
           rc == 2 and "no tracked" in o, f"rc={rc}, and it named the reason")
    h = d("t22b")
    _repo(h, {"a.md": "# nothing cited here\n", "src/b.txt": BODY})
    rc, o = _sweep_out(h)
    c.case("T22b .md with no citation at all is REFUSED",
           rc == 2 and "not one FILE:NNN" in o, f"rc={rc}")

    # ---- T5: class 6, fenced code blocks ------------------------------------
    f1 = d("t5")
    _repo(f1, {"a.md": "# f\n\n```\nsrc/b.txt:3\n```\n", "src/b.txt": BODY})
    _edit(f1, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(f1)
    c.case("T5  a citation inside a fence is not scanned",
           rc == 2 and "not one FILE:NNN" in o, f"rc={rc} (fenced, so no pop.)")
    f2 = d("t5b")
    _repo(f2, {"a.md": "# f\n\nsrc/b.txt:3\n", "src/b.txt": BODY})
    _edit(f2, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(f2)
    c.case("T5b and the SAME line outside one is",
           rc == 1 and "CITE-ROT" in o, f"rc={rc}")

    # ---- T6..T9: classes 1-4, every one of them 0 in the live corpus --------
    def rejected(name, body):
        """The body's decoy must not be SCANNED, which is a stronger claim
        than must not be a finding.

        🔴 The first version of this helper asserted only `1 citations`, and
        `M9` -- the lookbehind that rejects a URL host -- SURVIVED it, because
        a scanned `example.com:8080` resolves to no tracked file and is
        counted as `unresolved` rather than as a citation.  Both counters are
        read now, so the case fails at the point the decoy is first looked at
        instead of at the point it would have become a finding.
        """
        p = d(name)
        _repo(p, {"a.md": body + "\n\nreal: `src/b.txt:3`\n",
                  "src/b.txt": BODY})
        _edit(p, "src/b.txt", "x\ny\n" + BODY)
        rc, o = _sweep_out(p)
        return rc == 1 and "1 citations" in o and "unresolved 0" in o
    c.case("T6  a URL host:port is not a citation (SYNTHETIC: 0 live)",
           rejected("t6", "See https://example.com:8080 and "
                          "http://a.b.co:443 for it."), "class 1")
    c.case("T7  a clock time is not a citation",
           rejected("t7", "At 14:48 and 23:37:05 it printed."), "class 2")
    c.case("T8  a hex range is not a citation",
           rejected("t8", "The window 0x80188000:0x8018C000 is cached."),
           "class 3")
    c.case("T9  a histogram bucket is not a citation",
           rejected("t9", "Buckets {0.01:18} {0.5:3} over the run."),
           "class 4")

    # ---- T10: class 5, a transcript is ABOUT A PAST STATE -------------------
    t1 = d("t10")
    _repo(t1, {"a.md": "It printed `src/b.txt:3: warning here`.\n",
               "src/b.txt": BODY})
    _edit(t1, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(t1)
    c.case("T10 a quoted grep/compiler transcript is not scanned",
           rc == 2 and "not one FILE:NNN" in o, f"rc={rc}")
    t2 = d("t10b")
    _repo(t2, {"a.md": "It is at `src/b.txt:3` today.\n", "src/b.txt": BODY})
    _edit(t2, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(t2)
    c.case("T10b and the same token without the trailing colon is",
           rc == 1 and "CITE-ROT" in o, f"rc={rc}")

    # ---- T11: class 7, this tool's own output --------------------------------
    s1 = d("t11")
    _repo(s1, {"a.md": "    CITE-ROT     x.md:1 cites src/b.txt:3 -- moved\n",
               "src/b.txt": BODY})
    _edit(s1, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(s1)
    c.case("T11 a pasted report line is not a population",
           rc == 2 and "not one FILE:NNN" in o, f"rc={rc}")
    s2 = d("t11b")
    _repo(s2, {"a.md": "    x.md:1 cites src/b.txt:3 -- moved\n",
               "src/b.txt": BODY})
    _edit(s2, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(s2)
    c.case("T11b and the same line without the token IS",
           rc == 1 and "CITE-ROT" in o, f"rc={rc}")

    # ---- T12: class 8, refuse rather than pick --------------------------------
    am = d("t12")
    _repo(am, {"a.md": "at `b.txt:3`\n", "x/b.txt": BODY, "y/b.txt": BODY})
    rc, o = _sweep_out(am)
    c.case("T12 an ambiguous basename is REFUSED, never resolved",
           rc == 1 and "CITE-AMBIG" in o and "1 ambiguous" in o, f"rc={rc}")
    am2 = d("t12b")
    _repo(am2, {"a.md": "at `b.txt:3`\n", "x/b.txt": BODY})
    _edit(am2, "x/b.txt", "q\n" + BODY)
    rc, o = _sweep_out(am2)
    c.case("T12b and a basename with ONE candidate resolves",
           rc == 1 and "CITE-ROT" in o and "0 ambiguous" in o, f"rc={rc}")

    # ---- T13: class 9, the comparator, not the citation ----------------------
    tsv = "a\tb\nstoredata\tlu_sd_d0\nc\td\n"
    k1 = d("t13")
    _repo(k1, {"a.md": "row `t/x.tsv:2 (storedata\\tlu_sd_d0)` is it\n",
               "t/x.tsv": tsv})
    rc, o = _sweep_out(k1)
    c.case("T13 a literal \\t in a quoted token matches a real tab",
           rc == 0 and "M4 a quoted token" in o and "0 new of 0" in o,
           f"rc={rc}")
    k3 = d("t13c")
    # 🔴 `M15` -- TOKEN_TOL made infinite -- survived a suite whose only M4
    # failure case used a token that is ABSENT, because an absent token is not
    # found at any tolerance.  This one is PRESENT and far away, so it is the
    # case the tolerance is actually load-bearing for.
    far = "".join(f"row {i}\n" for i in range(1, 10)) + "needle here\n"
    _repo(k3, {"a.md": "row `t/y.tsv:2 (needle here)` is it\n", "t/y.tsv": far})
    rc, o = _sweep_out(k3)
    c.case("T13c a token PRESENT but far from its line still fails",
           rc == 1 and "CITE-M4" in o, f"rc={rc}, it is 8 lines away")
    k2 = d("t13b")
    _repo(k2, {"a.md": "row `t/x.tsv:2 (storedata\\tNOT_THIS)` is it\n",
               "t/x.tsv": tsv})
    rc, o = _sweep_out(k2)
    c.case("T13b and a token that is genuinely absent still fails",
           rc == 1 and "CITE-M4" in o, f"rc={rc}")

    # ---- T14/T15/T16: the zero-oracle checks, all 0 live ---------------------
    p1 = d("t14")
    _repo(p1, {"a.md": "at `src/b.txt:900`\n", "src/b.txt": BODY})
    rc, o = _sweep_out(p1)
    c.case("T14 M1 a citation past end of file (SYNTHETIC: 0 live)",
           rc == 1 and "CITE-M1" in o, f"rc={rc}")
    p2 = d("t15")
    _repo(p2, {"a.md": "at `src/b.txt:9-4`\n", "src/b.txt": BODY})
    rc, o = _sweep_out(p2)
    c.case("T15 M2 an inverted range (SYNTHETIC: 0 live)",
           rc == 1 and "CITE-M2" in o, f"rc={rc}")
    p3 = d("t16")
    _repo(p3, {"a.md": "at `src/b.txt:3`\n",
               "src/b.txt": "one\ntwo\nthree\n"})
    _edit(p3, "src/b.txt", "one\ntwo\n\nthree\n")
    rc, o = _sweep_out(p3)
    c.case("T16 M3 the cited line is now blank, with no oracle at all",
           rc == 1 and "CITE-M3" in o, f"rc={rc}")

    # ---- T17/T18: the baseline, in BOTH directions ---------------------------
    bl = d("t17")
    _repo(bl, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(bl, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(bl)
    cites_found, counts, ambig, _ = scan(bl)
    fs, _v, _b = oracle(bl, cites_found)
    bpath = os.path.join(tmp, "bl.tsv")
    with open(bpath, "wb") as fh:
        fh.write(baseline_text(fs).encode("utf-8"))
    rc2, o2 = _sweep_out(bl, baseline=bpath)
    c.case("T17 a rot ON the baseline is not new",
           rc == 1 and rc2 == 0 and "0 new, 1 known" in o2,
           f"without={rc} with={rc2}")
    with open(bpath, "ab") as fh:
        fh.write(b"ROT\ta.md\tsrc/b.txt\t99\tdeadbeefdeadbeef\tinvented\n")
    rc3, o3 = _sweep_out(bl, baseline=bpath)
    c.case("T18 a baseline row naming no finding is REPORTED",
           rc3 == 1 and "1 stale" in o3, f"rc={rc3}")
    with open(bpath, "ab") as fh:
        fh.write(b"ROT\tonly-three-columns\n")
    rc4, o4 = _sweep_out(bl, baseline=bpath)
    c.case("T18b and a malformed row is not silently skipped",
           rc4 == 1 and "1 malformed" in o4, f"rc={rc4}")

    # ---- T19: the false finding this tool actually made ---------------------
    #
    # A capture log with a BARE \r.  `git show` through text=True reads it as
    # more lines than it has, the two sides of the comparison disagree about
    # numbering, and nineteen unrotted citations are reported as rotted.
    # 🔴 The first version of this case asserted STABLE, and `M5` -- split the
    # file on \r as well -- SURVIVED it, because a change applied to BOTH sides
    # of the comparison keeps them agreeing with each other.  What the
    # convention decides is the NUMBER, so the case has to read one.  The
    # fixture is built so the two conventions give different answers: the
    # insertion is one \n-line and two splitlines()-lines.
    cr = d("t19")
    v1 = b"A\r\nB\rC\nD\nE\n"          # \n: 4 lines, "D" is line 3
    v2 = b"Z\rY\n" + v1                 # \n: "D" is line 4; splitlines: 5
    _repo(cr, {"a.md": "see `bench/x.log:3`\n", "bench/x.log": v1})
    _edit(cr, "bench/x.log", v2)
    rc, o = _sweep_out(cr)
    c.case("T19 a cited file with a bare CR is numbered on \\n only",
           rc == 1 and "now at line 4" in o and "bare CR" in o,
           f"rc={rc}; \\n says 4 and splitlines() says "
           f"{v2.decode().splitlines().index('D') + 1}")
    st = d("t19b")
    _repo(st, {"a.md": "see `bench/x.log:3`\n", "bench/x.log": v1})
    _edit(st, "a.md", "see `bench/x.log:3` still\n")
    rc, o = _sweep_out(st)
    c.case("T19b and an untouched one with a bare CR is STABLE",
           rc == 0 and "STABLE 1" in o, f"rc={rc}")

    # ---- T26: a citing line that is not committed has NO oracle ------------
    #
    # `git blame` gives an uncommitted line the all-zero sha, so there is no
    # "the cited file as it was at the citing commit" to read.  Using the
    # working tree for both sides would make every such citation trivially
    # stable, which is the shallow-clone failure one line at a time.  So the
    # citation is skipped AND the baseline rows for that file are suspended
    # rather than reported as repaired.
    uc = d("t26")
    _repo(uc, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(uc, "src/b.txt", "x\ny\n" + BODY)
    cs, _c2, _a2, _n2 = scan(uc)
    fs2, _v2, _b2 = oracle(uc, cs)
    bp2 = os.path.join(tmp, "t26.tsv")
    with open(bp2, "wb") as fh:
        fh.write(baseline_text(fs2).encode("utf-8"))
    rc, o = _sweep_out(uc, baseline=bp2)
    ok_before = rc == 0
    with open(os.path.join(uc, "a.md"), "wb") as fh:
        fh.write(cites(3).replace("that is that", "that is still that")
                 .encode("utf-8"))
    rc, o = _sweep_out(uc, baseline=bp2)
    c.case("T26 an uncommitted citing line is skipped, not assumed stable",
           ok_before and rc == 0 and "uncommitted 1" in o
           and "1 suspended" in o,
           f"clean={int(ok_before)} dirty rc={rc}")

    # ---- T20: SRCREF_EXEMPT is load-bearing ---------------------------------
    ex = d("t20")
    _repo(ex, {"LOG.md": cites(3), "bench/r.md": cites(3),
               "notes/n.md": cites(3), "src/b.txt": BODY})
    _edit(ex, "src/b.txt", "x\ny\n" + BODY)
    rc, o = _sweep_out(ex)
    c.case("T20 SRCREF_EXEMPT is load-bearing: the dated records are skipped",
           rc == 1 and "1 citations" in o and "2 files exempt" in o,
           f"rc={rc} -- only notes/n.md is in scope")

    # ---- T21: the declared false negative ------------------------------------
    mk = d("t21")
    _repo(mk, {"a.md": "at `rtl8192cd/Makefile:3` and at `src/b.txt:3`\n",
               "rtl8192cd/Makefile": BODY, "src/b.txt": BODY})
    _edit(mk, "rtl8192cd/Makefile", "x\ny\n" + BODY)
    rc, o = _sweep_out(mk)
    c.case("T21 an extensionless file is a DECLARED false negative",
           rc == 0 and "1 citations" in o,
           "Makefile:3 is not seen and the run is clean")

    # ---- T23: the case count does not move with the corpus -------------------
    small = d("t23a")
    _repo(small, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(small, "src/b.txt", "x\n" + BODY)
    big = d("t23b")
    body = "".join(f"Row {i} is at `src/b.txt:{(i % 11) + 1}`.\n\n"
                   for i in range(1, 13))
    _repo(big, {"a.md": "# many\n\n" + body, "src/b.txt": BODY})
    _edit(big, "src/b.txt", "x\n" + BODY)
    _, o1 = _sweep_out(small)
    _, o2 = _sweep_out(big)
    n1 = len(re.findall(r"^ {2}(?:ok|FAIL)\b", o1, re.M))
    n2 = len(re.findall(r"^ {2}(?:ok|FAIL)\b", o2, re.M))
    g1 = re.search(r"(\d+) citations", o1)
    g2 = re.search(r"(\d+) citations", o2)
    c.case("T23 the case count is invariant to the corpus size",
           n1 == n2 and n1 > 0 and g1 and g2 and g1.group(1) != g2.group(1),
           f"{g1.group(1) if g1 else '?'} citations -> {n1} cases; "
           f"{g2.group(1) if g2 else '?'} -> {n2}")

    # ---- T24: --write-baseline may not silence the gate on its own ---------
    wb = d("t24")
    _repo(wb, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(wb, "src/b.txt", "x\ny\n" + BODY)
    bpath2 = os.path.join(tmp, "t24.tsv")
    with open(bpath2, "wb") as fh:
        fh.write(b"# a baseline nobody generated\n")
    before = open(bpath2, "rb").read()
    rc, o = _run(["--write-baseline", "--root", wb, "--baseline", bpath2])
    after = open(bpath2, "rb").read()
    c.case("T24 --write-baseline writes stdout, never the file",
           rc == 0 and before == after and "\tsrc/b.txt\t" in o,
           "a gate that can rewrite its own allow-list in place is a gate "
           "that gets silenced by a keystroke")

    # ---- T25: the two-space contract with ci-census ------------------------
    sp = d("t25")
    _repo(sp, {"a.md": cites(3), "src/b.txt": BODY})
    _edit(sp, "src/b.txt", "x\ny\n" + BODY)
    _rc, so = _sweep_out(sp)
    exact = len(re.findall(r"^ {2}(?:ok|FAIL|skip)\b", so, re.M))
    anyn = len(re.findall(r"^ +(?:ok|FAIL|skip)\b", so, re.M))
    c.case("T25 every case line is at EXACTLY two spaces",
           exact == anyn and exact > 1,
           f"{exact} at two, {anyn} at any indent -- four spaces makes "
           f"ci-census read ok, fails and skips ALL as zero")

    c.dump()
    print()
    try:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception:
        pass
    if c.bad:
        print(f"RESULT: {c.ok} passed, {c.bad} failed")
        return 1
    print(f"RESULT: {c.ok} passed, 0 failed")
    return 0


def main(argv):
    root, baseline, only_self, write = ROOT, BASELINE, False, False
    no_controls, rev = False, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            i += 1
            root = os.path.abspath(argv[i])
        elif a == "--baseline":
            i += 1
            baseline = os.path.abspath(argv[i])
        elif a == "--self-test":
            only_self = True
        elif a == "--sweep-only":
            # Used by the controls, which need a real exit code out of a real
            # process.  Not for a build: a sweep with no controls in front of
            # it is a reading from an instrument nobody checked.
            no_controls = True
        elif a == "--rev":
            i += 1
            rev = argv[i]
        elif a == "--write-baseline":
            write = True
        elif a in ("-h", "--help"):
            print(__doc__.split("Usage")[-1])
            return 0
        else:
            _refuse(f"unknown argument {a!r}")
        i += 1

    if write:
        # Deliberately STDOUT.  A gate that can rewrite its own allow-list in
        # place is a gate that gets silenced by a keystroke; this one needs a
        # redirect and a diff.
        cites, _c, _a, _n = scan(root, rev)
        fs, _v, _b = oracle(root, cites, rev)
        sys.stdout.write(baseline_text(fs + secondary(root, cites, rev)))
        return 0

    if no_controls:
        return sweep(root=root, baseline_path=baseline, rev=rev)

    print("=== CONTROLS ===")
    rc = self_test()
    if only_self:
        return rc
    if rc:
        _refuse("the controls above failed. Nothing below them would mean "
                "anything -- a sweep whose instrument is broken reports "
                "findings that are the instrument", 1)
    print()
    print("=== THIS REPOSITORY ===")
    return sweep(root=root, baseline_path=baseline, rev=rev)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
