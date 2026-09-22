#!/usr/bin/env python3
r"""docsize -- a state document may not outgrow its declared budget.

WHY.  量 2026-08-23 -> 2026-09-23: `CLAUDE.md` 81 -> 1,450 lines, `PROGRESS.md`
7,550 -> 1,025,800 bytes with table cells past 31 KB, because every session
appended and nothing measured size.  `BUDGET` is a ratchet in `cfcensus`'s
sense, red in BOTH directions: a document may pass its number only in a commit
that raises it, and fall under `FLOOR` % of it only in one that lowers it.

WHAT IT MEASURES.  Files are read as bytes and split on `\n` only -- what
`grep -n`, `sed -n` and `LC_ALL=C awk` do -- so a `\r` is a byte of its line.
  FILE:lines            the `\n` count, +1 if the last line is unterminated
                        (= `grep -c ''`; `wc -l` misses that one line)
  FILE:bytes            bytes on disk (= `wc -c`): UTF-8 bytes, not characters
  FILE:maxline          bytes of the longest line, its `\n` excluded
  FILE#SECTION:bytes    from the line that EQUALS `## SECTION` up to, not
                        including, the next line starting `## `, or EOF;
                        a `### ` does not end it (= `sed -n 'A,Bp' | wc -c`)
  FILE#SECTION:maxline  the longest line inside that span
The measure follows the LAST `:` of a key and the section its FIRST `#`.

WHAT IT CANNOT SEE
  * Size, not readability.  A short document can be stale, wrong or unreadable.
  * It does not stop a budget being raised in the commit that grows the file.
    It makes the raise a line in the diff; review is what reads that line.
  * It is not a markdown parser: a `## ` line inside a code fence ends a
    section, exactly as `grep '^## '` says it does, and a `# ` line does not.
  * Only what `BUDGET` names.  A section or file it does not name grows freely.

REFUTATION CONDITIONS, written before the code
  * A key whose file or section does not exist FAILs, never skips: a budget
    nothing measures is a line that cannot fail (`cfcensus` L4/L14's shape).
    A heading that occurs twice FAILs too: measuring the first hides the rest.
  * One byte over must FAIL (Z2) and exactly-at must pass (Z3).  Z11 and Z11b
    invert and tighten the comparison through a hook and require Z2's and
    Z3's OWN predicates to catch the mutant, or those two are decoration.
  * The live check prints exactly len(BUDGET) case lines whatever the files
    hold, read with `ci-census`'s own parser (Z12), because the census
    declares a fixed count per suite.
  * Python drops a duplicated dict key in silence, so `BUDGET` and `NO_FLOOR`
    are also read back from this file's source: a key written twice, or a
    table changed after its literal, is a refusal (Z16; Z18 on this file).
  * Under `FLOOR` (50 %) of its budget a measure FAILs -- the other half of
    the ratchet, `cfcensus`'s both-directions rule (Z13, Z13b).  A key in
    `NO_FLOOR` has a ceiling only (Z20, Z20b), and an entry naming no
    `BUDGET` key is a stale exemption, so a refusal (Z21).

Usage
-----
    docsize.py                the controls, then the live check
    docsize.py --self-test    the controls only; no state document is read
    docsize.py check          the live check only
    docsize.py report         every measure against its budget; exits 0
    add --root DIR            to measure another checkout (default: ../)

Exit: 0 clean, 1 findings, 2 refusal (no repository root, BUDGET empty or
malformed).  A refusal prints no case line.
"""
import ast
import contextlib
import importlib.util
import io
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile

try:                                    # a CJK heading through a cp950 console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                       # pragma: no cover - older than 3.7
    pass

VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Each number is a CEILING.  `FLOOR` below is the other half of the ratchet,
# and `NO_FLOOR` names the keys that have a ceiling only.
# `CLAUDE.md`, 量 2026-09-23 in the commit that rewrote it to rules only: 340
# lines, 23,449 bytes, longest line 628 (line 140, a row of its Never table).
# Before the rewrite it was 1,450 lines and 127,686 bytes.
# `PROGRESS.md` whole file, 量 2026-09-23 at e36acb4: 961,431 bytes, longest
# line 31,772 (line 2143, § Carried forward).
# Every derived number is its measure +3 %, rounded UP to three significant
# figures, so it can be re-derived rather than trusted.
# § Now is NOT derived from a measurement: 6,000 bytes, and 1,000 bytes for
# any one line, are fixed caps -- a state row longer than ~1 KB is the disease
# this tool exists for.  (量 at e36acb4, for scale: 4,645 bytes, longest line
# 499 -- under half of its cap, which is one reason it is in `NO_FLOOR`.)
# Raising a number later is allowed and is the point: it is a changed line in
# a diff, and the commit that changes it says why.  Keys are string literals
# and values integer literals, each written once -- `require_literal` refuses
# anything else, because Python keeps the LAST of two equal keys in silence.
BUDGET = {
    "CLAUDE.md:lines": 351,
    "CLAUDE.md:bytes": 24200,
    "CLAUDE.md:maxline": 647,
    "PROGRESS.md:bytes": 991000,
    "PROGRESS.md:maxline": 32800,
    "PROGRESS.md#Now:bytes": 6000,
    "PROGRESS.md#Now:maxline": 1000,
}

# Keys with a CEILING ONLY.  § Now is rewritten every session and its size
# moves both ways for legitimate reasons, so there the cap IS the rule --
# "state is short" -- and a floor would be noise: red on an ordinary session,
# for the wrong reason, which trains a reader to stop reading reds.  The floor
# belongs on budgets that should only ever come DOWN after a one-time
# compaction (`CLAUDE.md`, `PROGRESS.md` whole file).  Every entry must name a
# `BUDGET` key -- one that names none exempts nothing and is refused as stale.
# A set literal, read back from the source like `BUDGET` (`require_literal`).
NO_FLOOR = {
    "PROGRESS.md#Now:bytes",
    "PROGRESS.md#Now:maxline",
}

FILE_MEASURES = ("lines", "bytes", "maxline")
SECTION_MEASURES = ("bytes", "maxline")
SUPPORTED = ("FILE:lines, FILE:bytes, FILE:maxline, FILE#SECTION:bytes, "
             "FILE#SECTION:maxline")
#: THE OTHER HALF OF THE RATCHET, in percent.  A measure under this share of
#: its budget FAILs, because the budget can come down and the commit that
#: shrank the document is the one that must lower it -- `cfcensus`'s rule that
#: a debt paid without being recorded is red too.  A ceiling alone only ever
#: loosens: the day a document is cut in half, its old number would go on
#: certifying the old size.  Every key has it except those in `NO_FLOOR`.
FLOOR = 50


class Refused(Exception):
    """No reading is possible.  Exit 2, and not one case line printed."""


def at_most(measured, budget):
    """THE CEILING.  Every caller below takes it as `compare`, so that Z11
    can hand in a mutant and show Z2 is what notices."""
    return measured <= budget


def at_least_floor(measured, budget):
    """THE FLOOR.  Every caller below takes it as `floor`, so that Z13b can
    remove or tighten it and show Z13 is what notices.  Integers only, so the
    boundary is exact: 50 of 100 passes and 49 of 100 does not."""
    return measured * 100 >= FLOOR * budget


# ------------------------------------------------------------------ the table
def parse_key(key):
    """'FILE:measure' or 'FILE#SECTION:measure' -> (file, section, measure).

    Refused, never guessed: a key that means nothing would measure nothing,
    and a budget nothing measures cannot fail.
    """
    if not isinstance(key, str) or ":" not in key:
        raise Refused("key %r is not one of %s" % (key, SUPPORTED))
    target, what = key.rsplit(":", 1)
    path, sep, section = target.partition("#")
    section = section if sep else None
    if (not path or path in (".", "..") or path.startswith("/")
            or "\\" in path or re.match(r"^[A-Za-z]:", path)
            or posixpath.normpath(path) != path
            or path.split("/")[0] == ".."):
        raise Refused("key %r: %r is not a normalised path inside the "
                      "repository (no leading /, no .., no ./, no \\)"
                      % (key, path))
    if section is not None:
        if not section or section != section.strip() or "\n" in section:
            raise Refused("key %r: the section name is empty or padded -- it "
                          "must be the exact heading text after `## `" % key)
        if what not in SECTION_MEASURES:
            raise Refused("key %r: a section has no measure %r -- one of %s"
                          % (key, what, SUPPORTED))
    elif what not in FILE_MEASURES:
        raise Refused("key %r: unknown measure %r -- one of %s"
                      % (key, what, SUPPORTED))
    return path, section, what


def validate_budget(budget, no_floor=frozenset()):
    """Refused unless every key parses, every value is an int >= 0, and every
    `NO_FLOOR` entry names a `BUDGET` key.  Every problem is named at once."""
    if not isinstance(budget, dict):
        raise Refused("BUDGET is a %s, not a dict" % type(budget).__name__)
    if not budget:
        raise Refused("BUDGET is empty -- a check over no budget prints "
                      "0 of 0 and cannot fail")
    bad = []
    for key, cap in budget.items():
        try:
            parse_key(key)
        except Refused as e:
            bad.append(str(e))
        if type(cap) is not int or cap < 0:        # a bool is an int subclass
            bad.append("%r: budget %r is not an int >= 0" % (key, cap))
    if not isinstance(no_floor, (set, frozenset)):
        bad.append("NO_FLOOR is a %s, not a set" % type(no_floor).__name__)
    else:
        for key in sorted(no_floor, key=repr):
            if not isinstance(key, str) or key not in budget:
                bad.append("NO_FLOOR names %r, which is not a BUDGET key -- "
                           "an exemption that exempts nothing is stale; "
                           "delete it" % (key,))
    if bad:
        raise Refused("the tables are malformed: " + "; ".join(bad))


def _parse(source):
    try:
        return ast.parse(source)
    except SyntaxError as e:
        raise Refused("the source declaring the tables does not parse: %s"
                      % e)


def _assignment(tree, name):
    """The ONE module-level statement that binds `name`.  None, or several --
    `|=` included -- and the table in the diff is not the one that runs."""
    found = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            found.append(node)
    if len(found) != 1:
        raise Refused("%s is assigned %d times at module level -- one literal "
                      "table, or the table in the diff is not the one that "
                      "runs" % (name, len(found)))
    return found[0]


def literal_set(tree, name="NO_FLOOR"):
    """`NO_FLOOR` as WRITTEN -> set.  A literal set of strings (`set()` when
    empty), or Refused."""
    node = _assignment(tree, name)
    try:
        value = (ast.literal_eval(node.value)
                 if isinstance(node, ast.Assign) else None)
    except ValueError:
        value = None
    if not (isinstance(value, set)
            and all(isinstance(k, str) for k in value)):
        raise Refused("%s must be assigned a literal set of BUDGET keys"
                      % name)
    return value


def literal_budget(tree, name="BUDGET"):
    """The table as WRITTEN -> dict.  Refused unless it is one module-level
    dict display with string-literal keys, none written twice, and literal
    values."""
    node = _assignment(tree, name)
    if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)):
        raise Refused("%s is not assigned a {...} display" % name)
    keys = []
    for k in node.value.keys:
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
            raise Refused("every %s key must be a string literal, or a key "
                          "written twice cannot be seen" % name)
        keys.append(k.value)
    twice = sorted(set(k for k in keys if keys.count(k) > 1))
    if twice:
        raise Refused("%s writes %s more than once -- Python keeps the LAST "
                      "and drops the rest without a word" % (name, twice))
    try:
        return ast.literal_eval(node.value)
    except ValueError:
        raise Refused("every %s value must be a literal, so the diff that "
                      "raises one shows the number" % name)


def require_literal(source, budget, no_floor=None):
    """Refused unless the tables that RUN are the tables that are WRITTEN.
    `no_floor` None skips `NO_FLOOR`, for a source that declares only
    `BUDGET`; the live path always passes it."""
    tree = _parse(source)
    if literal_budget(tree) != budget:
        raise Refused("BUDGET at run time differs from its literal in the "
                      "source -- something changed the table after it was "
                      "written")
    if no_floor is not None and literal_set(tree) != set(no_floor):
        raise Refused("NO_FLOOR at run time differs from its literal in the "
                      "source -- something exempted a key from the floor "
                      "after the set was written")


def own_source():
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            return fh.read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Refused("cannot read this tool's own source to check the "
                      "tables' literals: %s" % e)


def require_root(root):
    if not os.path.isdir(root):
        raise Refused("%s is not a directory" % root)
    if not os.path.exists(os.path.join(root, ".git")):
        raise Refused("%s has no .git, so it is not a repository root -- "
                      "every budget would read as a missing file and say "
                      "nothing about any repository" % root)


# ------------------------------------------------------------------ measuring
def resolve(root, rel):
    """-> the file's path, or None.  Every component must match with its
    EXACT case: on NTFS `claude.md` opens `CLAUDE.md`, and a key that is green
    at this desk and red on CI is the one outcome a size gate must not have."""
    cur = root
    for part in rel.split("/"):
        try:
            names = os.listdir(cur)
        except OSError:
            return None
        if part not in names:
            return None
        cur = os.path.join(cur, part)
    return cur if os.path.isfile(cur) else None


def line_spans(blob):
    """(start, end) of every line's content, its `\\n` excluded.  A final
    unterminated line is a line; a final `\\n` does not open another."""
    spans, pos, n = [], 0, len(blob)
    while pos < n:
        nl = blob.find(b"\n", pos)
        if nl < 0:
            spans.append((pos, n))
            break
        spans.append((pos, nl))
        pos = nl + 1
    return spans


def measure(blob, section, what):
    """-> (value, where, problem).  `value` is None exactly when `problem`
    says why nothing could be measured."""
    spans = line_spans(blob)

    def text(i):
        return blob[spans[i][0]:spans[i][1]]

    lo, hi, start, end, where = 0, len(spans), 0, len(blob), "whole file"
    if section is not None:
        want = b"## " + section.encode("utf-8")
        hits = [i for i in range(len(spans)) if text(i) == want]
        if len(hits) > 1:
            return None, None, ("`## %s` heads %d sections (lines %s) -- "
                                "measuring the first would hide the rest"
                                % (section, len(hits),
                                   ", ".join(str(i + 1) for i in hits)))
        if not hits:
            near = [str(i + 1) for i in range(len(spans))
                    if text(i).startswith(b"## ")
                    and (text(i).rstrip() == want
                         or text(i).startswith(want))]
            return None, None, (
                "no line equals `## %s`%s -- a budget nothing measures "
                "cannot fail" % (section,
                                 " (near miss at line %s; the heading must "
                                 "match exactly)" % ", ".join(near[:3])
                                 if near else ""))
        lo = hits[0]
        hi = next((j for j in range(lo + 1, len(spans))
                   if text(j).startswith(b"## ")), len(spans))
        start = spans[lo][0]
        end = spans[hi][0] if hi < len(spans) else len(blob)
        where = "lines %d-%d" % (lo + 1, hi)
    if what == "bytes":
        return end - start, where, None
    if what == "lines":
        return hi - lo, where, None
    if hi == lo:                                              # maxline
        return 0, "no lines", None
    best = max(range(lo, hi), key=lambda k: spans[k][1] - spans[k][0])
    return spans[best][1] - spans[best][0], "line %d" % (best + 1), None


class Result(object):
    __slots__ = ("key", "budget", "value", "where", "problem", "good",
                 "exempt")

    def __init__(self, key, budget, value, where, problem, good, exempt):
        self.key, self.budget, self.value = key, budget, value
        self.where, self.problem, self.good = where, problem, good
        self.exempt = exempt


def evaluate(root, budget, compare=None, floor=None, no_floor=frozenset()):
    """One Result per key, in the table's order.  Validation is the caller's;
    this measures, and judges each measure against its ceiling and -- unless
    its key is in `no_floor` -- its floor.  The exemption lifts the floor
    only: an exempt key over its ceiling still FAILs (Z20)."""
    compare = compare or at_most
    floor = floor or at_least_floor
    blobs, out = {}, []
    for key, cap in budget.items():
        path, section, what = parse_key(key)
        if path not in blobs:
            full = resolve(root, path)
            try:
                blobs[path] = None
                if full is not None:
                    with open(full, "rb") as fh:
                        blobs[path] = fh.read()
            except OSError as e:
                blobs[path] = e
        blob = blobs[path]
        if blob is None:
            value, where, problem = (None, None, "no such file %s -- a budget "
                                     "nothing measures cannot fail" % path)
        elif isinstance(blob, OSError):
            value, where, problem = None, None, "cannot read %s: %s" % (path,
                                                                        blob)
        else:
            value, where, problem = measure(blob, section, what)
        good = (problem is None and compare(value, cap)
                and (key in no_floor or floor(value, cap)))
        out.append(Result(key, cap, value, where, problem, good,
                          key in no_floor))
    return out


def pct(value, budget):
    return "%.1f %%" % (100.0 * value / budget) if budget else "n/a"


def under_floor(r):
    """For the WORDS of a line, never its verdict -- that is `floor`'s, so a
    mutant floor shows up as a line whose token and words disagree."""
    return (r.problem is None and not r.exempt
            and r.value * 100 < FLOOR * r.budget)


def floor_of(budget):
    """The smallest measure that passes the floor.  Printed instead of a
    rounded percentage, which reads `50.0 %` for 4,645 of 9,291 and so looks
    like a pass on a line that says FAIL."""
    return -(-FLOOR * budget // 100)


def case_lines(results):
    """EXACTLY one two-space case line per result, whatever was measured, and
    nothing else, so no other line can be read as one of this suite's cases."""
    w = max(len(r.key) for r in results)
    lines = []
    for r in results:
        if r.problem is not None:
            detail = r.problem
        elif r.value > r.budget:
            detail = "%d of %d -- OVER by %d (%s), %s" % (
                r.value, r.budget, r.value - r.budget,
                pct(r.value, r.budget), r.where)
        elif under_floor(r):
            detail = ("%d of %d -- UNDER the %d %% floor of %d: the budget "
                      "can come down -- lower it in this commit, %s"
                      % (r.value, r.budget, FLOOR, floor_of(r.budget),
                         r.where))
        else:
            detail = "%d of %d, %d to spare (%s), %s" % (
                r.value, r.budget, r.budget - r.value,
                pct(r.value, r.budget), r.where)
        if r.exempt:
            detail += ", no floor"
        lines.append("  %s  %-*s  %s" % ("ok  " if r.good else "FAIL", w,
                                         r.key, detail))
    return lines


def prepare(root, budget, source=None, compare=None, floor=None,
            no_floor=frozenset()):
    """Everything that can refuse, BEFORE anything is printed.  A source is
    passed only on the live path, which also passes the real `NO_FLOOR`."""
    require_root(root)
    validate_budget(budget, no_floor)
    if source is not None:
        require_literal(source, budget, no_floor)
    return evaluate(root, budget, compare, floor, no_floor)


def run_check(root, budget, source=None, compare=None, floor=None,
              no_floor=frozenset()):
    """The live check's whole path.  -> (rc, n_ok, n_cases)."""
    try:
        results = prepare(root, budget, source, compare, floor, no_floor)
    except Refused as e:
        print("REFUSING: %s" % e)
        return 2, 0, 0
    for ln in case_lines(results):
        print(ln)
    n_ok = sum(1 for r in results if r.good)
    return (0 if n_ok == len(results) else 1), n_ok, len(results)


def report(root, budget, source=None, no_floor=frozenset()):
    """Every measure against both halves of its budget.  Asserts nothing, so
    it exits 0 -- unless it cannot measure at all, which is a refusal."""
    try:
        results = prepare(root, budget, source, no_floor=no_floor)
    except Refused as e:
        print("REFUSING: %s" % e)
        return 2
    w = max([len("measure")] + [len(r.key) for r in results])
    print("report -- nothing here is asserted; `check` is the gate")
    print("    %-*s %9s %9s %9s %8s  %s"
          % (w, "measure", "now", "budget", "spare", "used", "where"))
    for r in results:
        if r.problem is not None:
            print("    %-*s %9s %9d %9s %8s  NOT MEASURED: %s"
                  % (w, r.key, "-", r.budget, "-", "-", r.problem))
            continue
        flag = ""
        if r.value > r.budget:
            flag = "  OVER by %d" % (r.value - r.budget)
        elif under_floor(r):
            flag = ("  UNDER the %d %% floor of %d -- lower it in this commit"
                    % (FLOOR, floor_of(r.budget)))
        elif r.exempt:
            flag = "  no floor"
        print("    %-*s %9d %9d %9d %8s  %s%s"
              % (w, r.key, r.value, r.budget, r.budget - r.value,
                 pct(r.value, r.budget), r.where, flag))
    return 0


# ------------------------------------------------------------------ controls
# Every fixture is written under tempfile, as bytes, so nothing here reads a
# live document and no size a commit can move reaches a verdict.  Every nested
# run is captured: a nested `  ok` reaching stdout would be counted by
# `ci-census` as one of this suite's own cases.
_ANY_CASE = re.compile(r"^ {2}(ok|FAIL|skip)\b", re.M)


def _n_cases(text):
    return len(_ANY_CASE.findall(text))


def _line_for(text, key):
    m = re.search(r"^ {2}(ok|FAIL)\s{2,}%s\s.*$" % re.escape(key), text, re.M)
    return (m.group(1), m.group(0).strip()) if m else (None, "(no line)")


def _fixture(tmp, name, files, git=True):
    root = os.path.join(tmp, name)
    os.makedirs(root)
    if git:
        os.makedirs(os.path.join(root, ".git"))
    for rel, blob in files.items():
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "wb") as fh:                   # bytes: no \r\n on Windows
            fh.write(blob)
    return root


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ret = fn(*a, **k)
    return ret, buf.getvalue()


TEN = b"0123456789"                      # ten bytes: one unterminated line


def _over(tmp, name, compare=None):
    """Z2's fixture: ten bytes against a budget of nine."""
    root = _fixture(tmp, name, {"x.md": TEN})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md:bytes": 9},
                               compare=compare)
    return rc, out


def _over_holds(rc, out):
    """Z2's predicate, kept apart so Z11 can apply it to a mutant's output."""
    tok, ln = _line_for(out, "x.md:bytes")
    return rc == 1 and tok == "FAIL" and "10 of 9" in ln and "OVER by 1" in ln


def _at(tmp, name, compare=None):
    """Z3's fixture: ten bytes against a budget of ten."""
    root = _fixture(tmp, name, {"x.md": TEN})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md:bytes": 10},
                               compare=compare)
    return rc, out


def _at_holds(rc, out):
    tok, ln = _line_for(out, "x.md:bytes")
    return rc == 0 and tok == "ok" and "10 of 10" in ln


def z1(tmp):
    root = _fixture(tmp, "z1", {"x.md": TEN})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md:bytes": 11})
    tok, ln = _line_for(out, "x.md:bytes")
    return (rc == 0 and tok == "ok" and "10 of 11" in ln,
            "rc=%d | %s" % (rc, ln))


def z2(tmp):
    rc, out = _over(tmp, "z2")
    return _over_holds(rc, out), "rc=%d | %s" % (rc, _line_for(out,
                                                             "x.md:bytes")[1])


def z3(tmp):
    rc, out = _at(tmp, "z3")
    return _at_holds(rc, out), "rc=%d | %s" % (rc, _line_for(out,
                                                           "x.md:bytes")[1])


def z4(tmp):
    # THE CONVENTION: the `\n` count, plus one for an unterminated last line
    # -- what `grep -c ''` and `awk 'END{print NR}'` print.  `wc -l` gives
    # 3, 2, 0, 2 for these four; the second is the line it does not count.
    files = {"t.md": b"a\nb\nc\n", "u.md": b"a\nb\nc", "e.md": b"",
             "n.md": b"\n\n"}
    want = {"t.md": 3, "u.md": 3, "e.md": 0, "n.md": 2}
    root = _fixture(tmp, "z4", files)
    got = dict((r.key.split(":")[0], r.value) for r in
               evaluate(root, dict((f + ":lines", 99) for f in sorted(files))))
    return got == want, ("with a final \\n %s, without %s, empty %s, two bare "
                         "\\n %s (by hand 3, 3, 0, 2)"
                         % (got.get("t.md"), got.get("u.md"), got.get("e.md"),
                            got.get("n.md")))


# By hand, line by line, and NOT by the function under test: `## Now\n` 7,
# `\n` 1, three table rows of 10, `\n` 1, `### Sub\n` 8, `text\n` 5 -- 52.
# `## Later: C# notes\n` 19 + `more\n` 5 -- 24, to EOF.  Leaving out the
# heading, the `\n`s, or stopping at the `### ` would give 45, 44 or 39.  The
# second heading carries a `:` and a `#` on purpose: its key only parses if the
# measure is split at the LAST `:` and the section at the FIRST `#`.
SECTION_DOC = (b"# Title\n"
               b"\n"
               b"## Now\n"
               b"\n"
               b"| a | b |\n"
               b"|---|---|\n"
               b"| 1 | 2 |\n"
               b"\n"
               b"### Sub\n"
               b"text\n"
               b"## Later: C# notes\n"
               b"more\n")


def z5(tmp):
    root = _fixture(tmp, "z5", {"s.md": SECTION_DOC})
    got = [r.value for r in evaluate(root, {
        "s.md#Now:bytes": 999, "s.md#Later: C# notes:bytes": 999})]
    return got == [52, 24], ("`## Now` %s bytes (by hand 52); `## Later: C# "
                             "notes`, to EOF, %s (by hand 24)" % (got[0],
                                                                 got[1]))


LONG_DOC = (b"## Now\n"
            b"short line 1\n" b"short line 2\n" b"short line 3\n"
            b"short line 4\n"
            b"## Later\n" + b"x" * 500 + b"\n" b"tail\n")


def z6(tmp):
    root = _fixture(tmp, "z6", {"m.md": LONG_DOC})
    by = dict((r.key, r) for r in evaluate(root, {
        "m.md:maxline": 100, "m.md:bytes": 1000, "m.md:lines": 10,
        "m.md#Now:maxline": 20}))
    ml, sec = by["m.md:maxline"], by["m.md#Now:maxline"]
    good = (not ml.good and ml.value == 500 and ml.where == "line 7"
            and by["m.md:bytes"].good and by["m.md:lines"].good
            and sec.good and sec.value == 12)
    return good, ("maxline %s at %s FAILs while bytes %s and lines %s pass; "
                  "§ Now's maxline is %s, the long line being outside it"
                  % (ml.value, ml.where, by["m.md:bytes"].value,
                     by["m.md:lines"].value, sec.value))


def z7(tmp):
    root = _fixture(tmp, "z7", {"x.md": b"hello\n"})
    (rc, _n, _t), out = _quiet(run_check, root, {"nope.md:lines": 10,
                                                 "X.md:bytes": 100})
    a, la = _line_for(out, "nope.md:lines")
    b, lb = _line_for(out, "X.md:bytes")
    # The wrong-case half can only discriminate where the filesystem folds
    # case -- NTFS at the desk, not ext4 on CI -- and the line says which.
    # 🔴 The REASON is asserted, not only the token: 量 2026-09-23, once the
    # floor existed, a lookup that ignored case found `x.md`, measured 6 of
    # 100, and FAILed for the FLOOR -- so a token-only check passed a mutant
    # this control exists to catch.  A FAIL for the wrong reason is not a pass.
    folds = os.path.exists(os.path.join(root, "X.md"))
    why = "no such file" in la and "no such file" in lb
    good = rc == 1 and _n_cases(out) == 2 and a == b == "FAIL" and why
    return (good,
            "rc=%d; nope.md %s and X.md, where only x.md exists, %s, %s -- "
            "this filesystem %s"
            % (rc, a, b, "both as `no such file`" if why else
               "NOT both as `no such file`",
               "FOLDS case, so that half is load-bearing here" if folds
               else "keeps case, so that half cannot discriminate here"))


def z8(tmp):
    # Three ways to be absent: a heading that only STARTS with the name, one
    # that differs by a trailing space -- the exact rule, not a lenient one --
    # and none at all.  The first two are named as near misses.
    root = _fixture(tmp, "z8", {"x.md": b"## Now (archive)\nold\n"
                                        b"## Next \nnew\n"})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md#Now:bytes": 100,
                                                 "x.md#Next:bytes": 100,
                                                 "x.md#Later:bytes": 100})
    a, la = _line_for(out, "x.md#Now:bytes")
    b, lb = _line_for(out, "x.md#Next:bytes")
    c, lc = _line_for(out, "x.md#Later:bytes")
    good = (rc == 1 and a == b == c == "FAIL"
            and all("no line equals" in ln for ln in (la, lb, lc))
            and "near miss at line 1" in la and "near miss at line 3" in lb
            and "near miss" not in lc)
    return good, "rc=%d, 3 FAIL | %s" % (rc, la)


def z9(tmp):
    root = _fixture(tmp, "z9", {"x.md": b"hello\n"})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md:bytes": 10,
                                                 "x.md:words": 10})
    good = (rc == 2 and "REFUSING" in out and "'words'" in out
            and _n_cases(out) == 0)
    return good, ("rc=%d, %d case line(s) -- the well-formed key beside it "
                  "was not printed either" % (rc, _n_cases(out)))


def z10(tmp):
    # 中 is U+4E2D: one character, three bytes.  `## 現在\n內容\n` is by hand
    # 3 + 6 + 1 + 6 + 1 = 17 bytes and 5 characters.
    root = _fixture(tmp, "z10", {"c.md": b"\xe4\xb8\xad",
                                 "d.md": "## 現在\n內容\n".encode("utf-8")})
    by = dict((r.key, r) for r in evaluate(root, {
        "c.md:bytes": 1, "c.md:maxline": 2, "d.md#現在:bytes": 17}))
    cb, cm, d = by["c.md:bytes"], by["c.md:maxline"], by["d.md#現在:bytes"]
    good = (cb.value == 3 and not cb.good and cm.value == 3 and not cm.good
            and d.value == 17 and d.good)
    return good, ("one CJK character is %s bytes and its line %s; a CJK "
                  "section is %s bytes (by hand 3, 3, 17)"
                  % (cb.value, cm.value, d.value))


def z11(tmp):
    rc, out = _over(tmp, "z11", compare=lambda m, b: not (m <= b))
    live = _line_for(out, "x.md:bytes")[0] == "ok"      # the hook IS the gate
    caught = not _over_holds(rc, out)
    return live and caught, ("inverted: Z2's fixture now reads %s rc=%d, and "
                             "Z2's own predicate %s"
                             % (_line_for(out, "x.md:bytes")[0], rc,
                                "catches it" if caught else "DOES NOT"))


def z11b(tmp):
    rc, out = _at(tmp, "z11b", compare=lambda m, b: m < b)
    live = _line_for(out, "x.md:bytes")[0] == "FAIL"
    caught = not _at_holds(rc, out)
    return live and caught, ("strict <: Z3's fixture now reads %s rc=%d, and "
                             "Z3's own predicate %s"
                             % (_line_for(out, "x.md:bytes")[0], rc,
                                "catches it" if caught else "DOES NOT"))


def _census():
    """`ci-census`'s own `parse_capture` and `misindented`, imported and not
    restated: the contract is the census's, so the control reads with it.
    Bytecode is not written, so a run from the source tree leaves no `.pyc`
    for `desk-sweep`'s fidelity check to find."""
    spec = importlib.util.spec_from_file_location(
        "_docsize_ci_census", os.path.join(HERE, "ci-census.py"))
    mod = importlib.util.module_from_spec(spec)
    old, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod.parse_capture, mod.misindented


def z12(tmp):
    try:
        parse, misindented = _census()
    except Exception as e:
        return False, "cannot load ci-census's parser: %r" % e
    budget = {"a.md:lines": 3, "a.md:bytes": 20, "a.md:maxline": 10,
              "a.md#Now:bytes": 20, "a.md#Now:maxline": 10, "b.md:bytes": 3}
    # "mixed" holds every kind of FAIL at once -- over (b.md), under the floor
    # (a.md:lines, 1 of 3) and missing (both § Now keys) -- so the count is
    # shown to hold whichever way a key goes red.
    corpora = (("all present", {"a.md": b"## Now\nshort\n", "b.md": b"b\n"},
                (6, 0)),
               ("nothing", {}, (0, 6)),
               ("mixed", {"a.md": b"no heading\n", "b.md": b"0123456789\n"},
                (2, 4)))
    good, seen = True, []
    for i, (name, files, want) in enumerate(corpora):
        _r, out = _quiet(run_check, _fixture(tmp, "z12-%d" % i, files), budget)
        ok, fails, skips, unparsable = parse(out)
        good = (good and (ok, fails) == want and not skips and not unparsable
                and misindented(out)[0] == 0)
        if name == "mixed":
            good = good and all(s in out for s in ("OVER by", "UNDER the",
                                                   "no line equals"))
        seen.append("%s %d+%d" % (name, ok, fails))
    return good, ("%d keys -> %s (over, under the floor, missing); 0 skip, "
                  "0 unparsable, 0 misindented" % (len(budget),
                                                   ", ".join(seen)))


def _floor_run(tmp, name, floor=None):
    """Z13's fixture: 49 and 50 bytes, each against a budget of 100."""
    root = _fixture(tmp, name, {"u.md": b"x" * 49, "v.md": b"x" * 50})
    (rc, _n, _t), out = _quiet(run_check, root, {"u.md:bytes": 100,
                                                 "v.md:bytes": 100},
                               floor=floor)
    return rc, out


def _floor_holds(rc, out):
    """Z13's predicate, kept apart so Z13b can apply it to a mutant's run."""
    u, lu = _line_for(out, "u.md:bytes")
    v, lv = _line_for(out, "v.md:bytes")
    return (rc == 1 and _n_cases(out) == 2
            and u == "FAIL" and "49 of 100" in lu
            and "lower it in this commit" in lu
            and v == "ok" and "50 of 100" in lv)


def z13(tmp):
    rc, out = _floor_run(tmp, "z13")
    lu = _line_for(out, "u.md:bytes")[1]
    # The printed floor is the smallest PASSING value, by hand: half of 99 is
    # 49.5, so 50; half of 9,291 is 4,645.5, so 4,646 -- a rounded-down floor
    # would print a line saying 4,645 is under a floor of 4,645.
    shown = [floor_of(b) for b in (99, 100, 9291)]
    return (_floor_holds(rc, out) and "floor of 50:" in lu
            and shown == [50, 50, 4646],
            "rc=%d | %s | floor of 99, 100, 9291 = %s (by hand 50, 50, 4646)"
            % (rc, lu, shown))


def z13b(tmp):
    rc1, out1 = _floor_run(tmp, "z13b-off", floor=lambda m, b: True)
    rc2, out2 = _floor_run(tmp, "z13b-strict",
                           floor=lambda m, b: m * 100 > FLOOR * b)
    off = _line_for(out1, "u.md:bytes")[0]          # each hook IS the gate
    strict = _line_for(out2, "v.md:bytes")[0]
    caught = not _floor_holds(rc1, out1) and not _floor_holds(rc2, out2)
    return (off == "ok" and strict == "FAIL" and caught,
            "floor removed: 49 of 100 reads %s; floor strict: 50 of 100 reads "
            "%s; Z13's own predicate %s" % (off, strict, "catches both"
                                             if caught else "DOES NOT"))


def z14(tmp):
    root = _fixture(tmp, "z14", {"x.md": b"## Now\na\n## Other\nb\n"
                                         b"## Now\nc\n"})
    (rc, _n, _t), out = _quiet(run_check, root, {"x.md#Now:bytes": 1000})
    tok, ln = _line_for(out, "x.md#Now:bytes")
    return rc == 1 and tok == "FAIL" and "(lines 1, 5)" in ln, "rc=%d | %s" % (
        rc, ln)


MALFORMED = (
    ("empty", {}),
    ("a list", [("x.md:bytes", 10)]),
    ("a bool value", {"x.md:bytes": True}),
    ("a negative value", {"x.md:bytes": -1}),
    ("a float value", {"x.md:bytes": 10.0}),
    ("no measure", {"x.md": 10}),
    ("lines of a section", {"x.md#Now:lines": 10}),
    ("an empty section", {"x.md#:bytes": 10}),
    ("a padded section", {"x.md# Now:bytes": 10}),
    ("no file", {":bytes": 10}),
    ("a path out of the root", {"../x.md:bytes": 10}),
    ("an absolute path", {"/x.md:bytes": 10}),
    ("an unnormalised path", {"./x.md:bytes": 10}),
    ("a backslash", {"sub\\x.md:bytes": 10}),
)


def z15(tmp):
    root = _fixture(tmp, "z15", {"x.md": b"## Now\nhello\n"})
    (rc0, _n, _t), out0 = _quiet(run_check, root, {"x.md:bytes": 10,
                                                   "x.md#Now:bytes": 10})
    control = rc0 in (0, 1) and _n_cases(out0) == 2
    missed = []
    for name, bad in MALFORMED:
        (rc, _n, _t), out = _quiet(run_check, root, bad)
        if not (rc == 2 and "REFUSING" in out and _n_cases(out) == 0):
            missed.append(name)
    if control and not missed:
        return True, ("%d malformed tables refused with no case line; the "
                      "well-formed control was not" % len(MALFORMED))
    return False, "NOT refused: %s; control rc=%d" % (missed, rc0)


_SRC_OK = 'BUDGET = {\n    "a.md:lines": 1,\n    "a.md:bytes": 2,\n}\n'
_SRC_BAD = (
    ("a key written twice",
     'BUDGET = {\n    "a.md:lines": 1,\n    "a.md:bytes": 2,\n'
     '    "a.md:lines": 900,\n}\n'),
    ("assigned twice", _SRC_OK + 'BUDGET = {"a.md:lines": 900}\n'),
    ("widened in place", _SRC_OK + 'BUDGET |= {"a.md:lines": 900}\n'),
    ("changed after its literal", _SRC_OK + 'BUDGET["a.md:lines"] = 900\n'),
    ("not a {...} display", 'BUDGET = dict([("a.md:lines", 1)])\n'),
    ("a computed value", 'BUDGET = {"a.md:lines": 128 * 8}\n'),
)


# The same rule for `NO_FLOOR`: a set changed after its literal switches a
# floor off with a line nobody reads as the table.
_SRC_NF = _SRC_OK + 'NO_FLOOR = {\n    "a.md:bytes",\n}\n'
_SRC_NF_BAD = (
    ("NO_FLOOR widened after its literal",
     _SRC_NF + 'NO_FLOOR.add("a.md:lines")\n'),
    ("NO_FLOOR assigned twice", _SRC_NF + 'NO_FLOOR = {"a.md:lines"}\n'),
    ("NO_FLOOR a list", _SRC_OK + 'NO_FLOOR = ["a.md:bytes"]\n'),
)


def _runtime(src):
    """What Python itself builds from `src`: the tables no reader sees."""
    ns = {}
    exec(compile(src, "<docsize-z16>", "exec"), ns)
    return ns


def _literal_refused(src, with_no_floor):
    ns = _runtime(src)
    try:
        require_literal(src, ns["BUDGET"],
                        ns["NO_FLOOR"] if with_no_floor else None)
        return False
    except Refused:
        return True


def z16(tmp):
    control = (not _literal_refused(_SRC_OK, False)
               and not _literal_refused(_SRC_NF, True))
    missed = [n for n, s in _SRC_BAD if not _literal_refused(s, False)]
    missed += [n for n, s in _SRC_NF_BAD if not _literal_refused(s, True)]
    kept = _runtime(_SRC_BAD[0][1])["BUDGET"]["a.md:lines"]
    n = len(_SRC_BAD) + len(_SRC_NF_BAD)
    good = control and not missed and kept == 900
    return good, ("Python kept %d of the two `a.md:lines`; %d of %d rewritten "
                  "tables refused, %d of them NO_FLOOR%s; the clean ones %s"
                  % (kept, n - len(missed), n, len(_SRC_NF_BAD),
                     " -- NOT %s" % missed if missed else "",
                     "passed" if control else "were REFUSED"))


def z17(tmp):
    root = _fixture(tmp, "z17", {"x.md": b"hello\n"}, git=False)
    (rc1, _n, _t), out1 = _quiet(run_check, root, {"x.md:bytes": 10})
    os.makedirs(os.path.join(root, ".git"))
    (rc2, _n, _t), out2 = _quiet(run_check, root, {"x.md:bytes": 10})
    good = (rc1 == 2 and "REFUSING" in out1 and _n_cases(out1) == 0
            and rc2 == 0 and _n_cases(out2) == 1)
    return good, "without .git rc=%d, %d case(s); with it rc=%d, %d" % (
        rc1, _n_cases(out1), rc2, _n_cases(out2))


def _twice(src):
    """`src` with BUDGET rebuilt so that its first key is written AGAIN as the
    last entry -- the edit Python accepts without a word, the second value
    winning.  Rebuilt from the parsed table, so it survives any reformatting
    of the literal."""
    node = [n for n in ast.parse(src).body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "BUDGET"
                    for t in n.targets)][0]
    table = ast.literal_eval(node.value)
    rows = list(table.items()) + [(next(iter(table)), 10 ** 9)]
    lines = src.split("\n")
    lines[node.lineno - 1:node.end_lineno] = [
        "BUDGET = {\n%s}" % "".join("    %r: %d,\n" % kv for kv in rows)]
    return "\n".join(lines)


def _widen(src):
    """`src` with one more `BUDGET` key added to `NO_FLOOR` at run time,
    AFTER its literal -- a floor switched off by a line nobody reads as the
    table.  The key is the first one the literal does not already exempt."""
    body = ast.parse(src).body

    def bound(name):
        return [n for n in body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name
                        for t in n.targets)][0]

    exempt = bound("NO_FLOOR")
    key = next(k for k in ast.literal_eval(bound("BUDGET").value)
               if k not in ast.literal_eval(exempt.value))
    lines = src.split("\n")
    lines.insert(exempt.end_lineno, "NO_FLOOR.add(%r)" % key)
    return "\n".join(lines)


def _as_process(tmp, name, text, root):
    """Run `text` as this tool, in a real process -> (rc, stdout)."""
    path = os.path.join(tmp, name)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    r = subprocess.run([sys.executable, path, "check", "--root", root],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace").replace("\r\n",
                                                                     "\n")


def z18(tmp):
    # The entry point as a PROCESS, three times, from this file's own source:
    # as written, with a BUDGET key written twice, and with NO_FLOOR widened
    # after its literal.  An empty repository, so no size a commit can move
    # reaches the verdict; a real process, so the exit code is the one CI
    # reads and not a return value.  A control that exercises a helper does
    # not exercise its caller (`bootbytes` K5).
    root = _fixture(tmp, "z18", {})
    src = own_source()
    rc1, out1 = _as_process(tmp, "z18-as-written.py", src, root)
    rc2, out2 = _as_process(tmp, "z18-key-twice.py", _twice(src), root)
    rc3, out3 = _as_process(tmp, "z18-no-floor-widened.py", _widen(src), root)
    fails = [ln for ln in out1.splitlines() if ln.startswith("  FAIL  ")]
    good = (rc1 == 1 and _n_cases(out1) == len(BUDGET) == len(fails)
            and all("no such file" in ln for ln in fails)
            and rc2 == 2 and "more than once" in out2 and _n_cases(out2) == 0
            and rc3 == 2 and "NO_FLOOR at run time" in out3
            and _n_cases(out3) == 0)
    return good, ("as written: rc=%d, %d FAIL of %d key(s), each `no such "
                  "file`; first key written twice: rc=%d; NO_FLOOR widened "
                  "after its literal: rc=%d; %d case line(s) from the last two"
                  % (rc1, len(fails), len(BUDGET), rc2, rc3,
                     _n_cases(out2) + _n_cases(out3)))


def z19(tmp):
    # x.md:lines and x.md:maxline are both 1 and 10 of 100 -- under the floor
    # -- and only the second is exempt, so exactly one row may say UNDER.
    root = _fixture(tmp, "z19", {"x.md": TEN})
    rc, out = _quiet(report, root, {"x.md:bytes": 9, "y.md:bytes": 5,
                                    "x.md:lines": 100, "x.md:maxline": 100},
                     no_floor=frozenset({"x.md:maxline"}))
    good = (rc == 0 and "OVER by 1" in out and "NOT MEASURED" in out
            and out.count("UNDER the %d %% floor" % FLOOR) == 1
            and "no floor" in out and _n_cases(out) == 0)
    return good, ("over, missing, under the floor, exempt: rc=%d, each "
                  "flagged once, %d case line(s)" % (rc, _n_cases(out)))


#: Z20's exemption: both fixture keys have a ceiling only.
_EXEMPT = frozenset({"n.md:bytes", "m.md:bytes"})


def _exempt_run(tmp, name, no_floor):
    """Z20's fixture: n.md at 10 % of its budget, m.md one byte over."""
    root = _fixture(tmp, name, {"n.md": b"x" * 10, "m.md": b"x" * 11})
    (rc, _n, _t), out = _quiet(run_check, root, {"n.md:bytes": 100,
                                                 "m.md:bytes": 10},
                               no_floor=no_floor)
    return rc, out


def _exempt_holds(rc, out):
    """Z20's predicate, kept apart so Z20b can apply it without the
    exemption.  The exempt key at 10 % passes; the exempt key over its
    ceiling still FAILs, so the exemption lifts the floor and nothing else."""
    n, ln = _line_for(out, "n.md:bytes")
    m, lm = _line_for(out, "m.md:bytes")
    return (rc == 1 and _n_cases(out) == 2
            and n == "ok" and "10 of 100, 90 to spare" in ln
            and "no floor" in ln and "UNDER" not in ln
            and m == "FAIL" and "OVER by 1" in lm)


def z20(tmp):
    rc, out = _exempt_run(tmp, "z20", _EXEMPT)
    return _exempt_holds(rc, out), ("rc=%d | %s | and over its ceiling: %s"
                                    % (rc, _line_for(out, "n.md:bytes")[1],
                                       _line_for(out, "m.md:bytes")[0]))


def z20b(tmp):
    rc, out = _exempt_run(tmp, "z20b", frozenset())
    n = _line_for(out, "n.md:bytes")[0]
    caught = not _exempt_holds(rc, out)
    return n == "FAIL" and caught, ("without the exemption the same 10 of 100 "
                                    "reads %s, and Z20's own predicate %s"
                                    % (n, "catches it" if caught else
                                       "DOES NOT"))


def z21(tmp):
    root = _fixture(tmp, "z21", {"x.md": TEN})
    budget = {"x.md:bytes": 10}
    (rc0, _n, _t), out0 = _quiet(run_check, root, budget,
                                 no_floor=frozenset({"x.md:bytes"}))
    control = rc0 == 0 and _n_cases(out0) == 1
    missed = []
    for name, bad in (("names no BUDGET key", {"x.md:lines"}),
                      ("is a list", ["x.md:bytes"]),
                      ("holds a non-string", {1})):
        (rc, _n, _t), out = _quiet(run_check, root, budget, no_floor=bad)
        if not (rc == 2 and "REFUSING" in out and _n_cases(out) == 0
                and ("stale" in out or "not a set" in out)):
            missed.append(name)
    if control and not missed:
        return True, ("a stale entry, a list and a non-string are refused "
                      "with no case line; a valid exemption is not")
    return False, "NOT refused: %s; control rc=%d" % (missed, rc0)


CONTROLS = (
    ("Z1   a file under its budget passes", z1),
    ("Z2   one byte over FAILs, with measured, budget, excess", z2),
    ("Z3   exactly at the budget passes: the boundary is <=", z3),
    ("Z4   lines = the \\n count, +1 for an unterminated last", z4),
    ("Z5   a section runs to the next `## `, its `### ` inside", z5),
    ("Z6   maxline finds one long line in a small file", z6),
    ("Z7   a key naming a missing file FAILs, wrong case too", z7),
    ("Z8   a key naming a missing section FAILs", z8),
    ("Z9   an unknown measure is a refusal, no case line", z9),
    ("Z10  bytes are UTF-8 bytes, not characters", z10),
    ("Z11  Z2 is load-bearing: inverted comparison caught", z11),
    ("Z11b Z3 is load-bearing: strict < caught", z11b),
    ("Z12  case lines = len(budget) on any corpus, per ci-census", z12),
    ("Z13  under the 50 % floor FAILs (49/100), at it passes", z13),
    ("Z13b the floor is load-bearing: removed and strict caught", z13b),
    ("Z14  a heading written twice FAILs, never first-match", z14),
    ("Z15  every other malformed BUDGET is a refusal", z15),
    ("Z16  a twice-written key or a changed table is refused", z16),
    ("Z17  a root with no .git is refused, one with it is not", z17),
    ("Z18  the entry point as a process: exit 1, then exit 2", z18),
    ("Z19  report flags over/missing/floor/exempt, exits 0", z19),
    ("Z20  NO_FLOOR: 10 % passes, over the ceiling still FAILs", z20),
    ("Z20b NO_FLOOR is load-bearing: without it, 10 % FAILs", z20b),
    ("Z21  a NO_FLOOR entry naming no BUDGET key is refused", z21),
)


def self_test():
    """-> (n_ok, n_controls).  One case line per control, even for one that
    raises: a control that crashes is a control that failed."""
    tmp = tempfile.mkdtemp(prefix="docsize-")
    n_ok = 0
    try:
        for label, fn in CONTROLS:
            try:
                good, detail = fn(tmp)
            except Exception as e:
                good, detail = False, "raised %s: %s" % (type(e).__name__, e)
            n_ok += 1 if good else 0
            print("  %s  %-58s %s" % ("ok  " if good else "FAIL", label,
                                      detail))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return n_ok, len(CONTROLS)


# ------------------------------------------------------------------ entry
def main(argv):
    mode, root, i = "all", ROOT, 0
    while i < len(argv):
        a = argv[i]
        if a == "--root" and i + 1 < len(argv):
            root, i = os.path.abspath(argv[i + 1]), i + 2
            continue
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        pick = {"--self-test": "self-test", "check": "check",
                "report": "report"}.get(a)
        if pick is None or mode != "all":
            print("REFUSING: argument %r -- usage: docsize.py [--self-test | "
                  "check | report] [--root DIR]" % a)
            return 2
        mode, i = pick, i + 1

    print("docsize %s  --  a state document may not outgrow its budget"
          % VERSION)
    if mode == "self-test":
        n_ok, n = self_test()
        print("%d of %d ok" % (n_ok, n))
        return 0 if n_ok == n else 1
    try:
        src = own_source()
    except Refused as e:
        print("REFUSING: %s" % e)
        return 2
    if mode == "report":
        return report(root, BUDGET, source=src, no_floor=NO_FLOOR)
    if mode == "check":
        rc, n_ok, n = run_check(root, BUDGET, source=src, no_floor=NO_FLOOR)
        if rc != 2:
            print("%d of %d ok" % (n_ok, n))
        return rc

    print("=== CONTROLS ===")
    c_ok, c_n = self_test()
    print("    controls: %d of %d ok" % (c_ok, c_n))
    if c_ok != c_n:
        print("NOT RUN: the live check.  A check whose controls failed "
              "reports findings that are the instrument.")
        return 1
    print("=== THIS REPOSITORY ===")
    rc, n_ok, n = run_check(root, BUDGET, source=src, no_floor=NO_FLOOR)
    if rc == 2:
        return 2
    print("    budgets: %d of %d ok" % (n_ok, n))
    print("%d of %d ok" % (c_ok + n_ok, c_n + n))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
