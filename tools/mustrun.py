#!/usr/bin/env python3
"""mustrun -- which CI suites read files that changed, so a skipped full sweep
is auditable instead of invisible.

WHY IT EXISTS, and it is a measurement rather than a preference
---------------------------------------------------------------
量 2026-09-15, from this repository's own CI history: SIX runs went red
between 2026-09-13 and 2026-09-15, and every one of them was a committed
claim about the repository's own contents going stale -- caught by a gate that
already exists and already runs in CI.  Not one was a code defect.

    34745994861  2026-09-13  2ee0c6d  census/census
    34811279996  2026-09-14  1bbd587  instruments/tccensus
    34839959119  2026-09-14  6923b86  text/ledgerscan check (exit-code gate)
    34840698703  2026-09-14  383804a  text/ledgerscan check (exit-code gate)
    34958415918  2026-09-15  490f5f5  text/citecheck AND instruments/tccensus
    34972020564  2026-09-15  b40e40c  text/test-boot-timeline

⚠️ Six RUNS, SEVEN failing steps: 34958415918 carries two.  `3c4b171`'s own
message reads "six CI runs ... census/census, tccensus twice, ledgerscan check
twice, and citecheck -- and with this one that is six of six", which counts
steps in the list and runs in the total.  The table above is the reading.

`CLAUDE.md` already states the rule -- after a seating, run every suite that
can run on this host -- and `tools/desk-sweep.py` already does it by reading
`ci.yml` with PyYAML.  What failed is neither: 量 the full sweep costs about
1,002.7 s on ext4, so it gets skipped, and the hand-picked list that replaces
it misses exactly the suites whose INPUT DATA moved rather than whose code
moved.  A hand-picked list is a claim about which suites read what, made from
memory, with nothing checking it.

This tool makes that claim mechanical.  It does NOT replace the full sweep.
It makes the full sweep's skip auditable: run this, and what it names is the
floor.

METHOD
------
1. Enumerate the steps by IMPORTING `tools/desk-sweep.py`'s `enumerate_steps`,
   which parses `ci.yml` as YAML.  It is imported by path with
   `importlib` because the filename carries a hyphen and is not a legal module
   name -- the same idiom `tools/citecheck.py` and `tools/isacensus.py` use
   for `spec-check.py`.  The enumerator is not restated here, for the reason
   desk-sweep's own header gives: a line-based enumerator cannot see a YAML
   literal block or an inline `- run:`, and every desk sweep from 2026-08-25
   to 2026-09-07 skipped two steps of the `lint` job for exactly that.
   `C2` re-runs desk-sweep's own broken enumerator on the LIVE file and
   requires it to come out short, so that reason is a case and not a
   paragraph.
2. Derive each step's input path set statically: repo paths named in the
   step's `run:` text, plus repo paths named in the source of each
   `tools/*.py` / `tools/*.sh` the step invokes (`--depth`, default 3 --
   the measured fixed point, see `derive`).
   `git ls-files` with no glob becomes `*`, the whole tree.
3. Intersect with `git diff --name-only --no-renames <range>`.
4. Print the suites that must run and how many of the total that is.

WHAT WOULD REFUTE IT, written before the sweep
-----------------------------------------------
  V1  a historical red whose failing suite this tool does NOT name from the
      range CI actually tested.  Seven are baked in as `H1`..`H7`.
      ⚠️ THREE OF THE SEVEN ARE WEAK AND `H8` SAYS SO: `text/ledgerscan check`
      (H3, H4) and `text/citecheck` (H5) sweep `git ls-files`, so any
      non-empty diff names them whatever the derivation did, and they test
      nothing.  The four that carry the claim are H1 (`census/census`), H2 and
      H6 (`instruments/tccensus`) and H7 (`text/test-boot-timeline`), none of
      which sweeps the tree.  `H8` requires at least four of that kind, so a
      derivation that collapsed to `*` everywhere would go red instead of
      scoring 7 of 7.
  V2  a diff touching a path in no step's set that still names a suite --
      the matcher cannot report zero, so its zeros are worthless.
  V3  a range git cannot resolve, or a `ci.yml` that will not parse, coming
      back as an empty list instead of a refusal.
Any of the three and the tool is not evidence.  `--self-test` plants V2 and
V3 and requires both to fire.

🔴 THE RANGE IS THE PUSH, NOT THE COMMIT, and `H7` is why that sentence is
here.  CI runs once per push and a push can carry several commits.
`b40e40c`'s own diff is four `.md` files and names nothing; the capture
directory that turned `test-boot-timeline` red arrived in `0ff8c3c`, two
commits earlier in the same push.  So the range to hand this tool is
`<the sha of the last run>..HEAD`, and `H7` asserts BOTH halves: the push
range names the suite and the single commit does not.

LIMITS, stated here rather than discovered later
------------------------------------------------
* It is a STATIC over-approximation.  Naming a suite that did not need to run
  is harmless; the failure this exists to stop is the other one.
* It cannot see a path a tool builds at RUNTIME from data -- an
  `os.path.join(root, rel)` where `rel` comes from a table, a filename read
  out of a capture, a directory named by an argument this tool never sees.
  Those are invisible, and `git ls-files` -> `*` is the blunt instrument that
  covers most of them.
* The answer is derived from the CODE half of each tool.  A path named only
  in a comment is reported too, in its own `weaker` section, and does not set
  the answer -- see `code_half` for why that split is the difference between
  an instrument and `true`.  The stripping is conservative, so a trailing
  `# ...` on a line of code still counts as code.
* **It does not replace the full sweep.**  When `list` says it named most of
  the steps, the information is that the safe move is `desk-sweep.py run`.
* 🔴 THERE IS NO NEGATIVE CONTROL AVAILABLE ON THIS TREE, and the tool says so
  rather than being quiet about it.  Eleven live steps sweep `git ls-files`
  -- `spec-check`, both `ledgerscan` gates, `citecheck`, `leakscan`,
  `test-file-modes`, `test-vendor-tripwire`, both `emueq` steps and the
  citecheck mutation suite -- so `*` is in their sets and 量 2026-09-15
  **0 of 4,198 tracked paths name zero steps**.  `C5` therefore runs the
  negative control on a synthetic fixture, and `C11` asserts the REASON --
  that at least one live step reads the whole tree -- so if that ever stops
  being true, the control becomes available on the real tree and `C11` says so
  by going red.

Usage
    mustrun.py list [RANGE]     RANGE defaults to the working tree vs HEAD;
                                e.g. `HEAD~1..HEAD`, `<sha>..HEAD`, or a bare
                                rev meaning `<rev>^..<rev>`
    mustrun.py paths SUITE      the derived path set for one suite, with where
                                each pattern came from
    mustrun.py --self-test      the controls

Exit
    0  clean -- nothing must be re-run (or `paths` printed a set)
    1  a finding -- at least one suite reads something that changed
    3  REFUSED -- the range or the file could not be read, so nothing is
       reported.  An empty list and a failed derivation must not look the same
"""
import argparse
import fnmatch
import importlib.util
import os
import posixpath
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI_REL = os.path.join(".github", "workflows", "ci.yml")

# How far the step -> tool -> tool indirection is followed.  THREE is a
# measurement and not a taste; `derive` carries it and `C13` is the control.
DEFAULT_DEPTH = 3


class Refuse(Exception):
    pass


# ---------------------------------------------------------------------------
# Enumeration -- imported, never restated
# ---------------------------------------------------------------------------

def desk_sweep(root=ROOT):
    """`tools/desk-sweep.py` as a module.

    Imported by path: the filename has a hyphen, so `import desk_sweep` cannot
    reach it.  The module has no import-time side effects (everything is under
    `if __name__ == "__main__"`), which is why this is safe.
    """
    path = os.path.join(root, "tools", "desk-sweep.py")
    if not os.path.exists(path):
        raise Refuse("tools/desk-sweep.py is not there -- the step list has "
                     "exactly one owner and this tool will not grow a second")
    spec = importlib.util.spec_from_file_location("_mustrun_desk_sweep", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                       # pragma: no cover - refusal
        raise Refuse("tools/desk-sweep.py would not import: %s" % exc)
    for fn in ("enumerate_steps", "enumerate_steps_linewise"):
        if not hasattr(mod, fn):
            raise Refuse("tools/desk-sweep.py has no %s() any more -- the "
                         "enumerator this tool imports has moved" % fn)
    return mod


def steps_of(ci_path, root=ROOT):
    if not os.path.exists(ci_path):
        raise Refuse("no such workflow file: %s" % ci_path)
    try:
        steps = desk_sweep(root).enumerate_steps(ci_path)
    except Refuse:
        raise
    except Exception as exc:
        raise Refuse("%s would not parse as YAML: %s"
                     % (os.path.relpath(ci_path, root).replace(os.sep, "/"),
                        exc))
    if not steps:
        raise Refuse("%s declares no `run:` step at all -- an empty step list "
                     "and a failed parse must not look the same"
                     % os.path.relpath(ci_path, root).replace(os.sep, "/"))
    return steps


def step_id(step):
    return "%s/%s" % (step["job"], step["name"])


# ---------------------------------------------------------------------------
# The vocabulary of repo paths
#
# Derived from the tree rather than hardcoded, so a new top-level directory is
# seen the day it appears, with a hardcoded FLOOR so the derivation cannot
# silently collapse to nothing on a tree git will not answer about.
# ---------------------------------------------------------------------------

FLOOR_TOPS = ("bench", "config", "docs", "dt", "notes", "qemu", "refs",
              "study", "tools", "upstream", ".github")
FLOOR_FILES = ("SPEC.md", "README.md", "LOG.md", "PROGRESS.md", "RUNSHEET.md",
               "CHANGELOG.md", "CLAUDE.md", "SOURCES.json")


def _git(root, *args):
    r = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or ""), (r.stderr or "")


def vocabulary(root=ROOT):
    """(top-level directories, top-level files) this tree actually has."""
    tops, files = set(FLOOR_TOPS), set(FLOOR_FILES)
    rc, out, _ = _git(root, "ls-files")
    if rc == 0:
        for line in out.splitlines():
            line = line.strip().replace("\\", "/")
            if not line:
                continue
            if "/" in line:
                tops.add(line.split("/", 1)[0])
            else:
                files.add(line)
    return tops, files


_JOIN_RE = re.compile(r"os\.path\.join\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*"
                      r"([^()]*?)\)")
_STR_RE = re.compile(r"""['"]([^'"]+)['"]""")
_HERE_SH_RE = re.compile(r"\$\{?HERE\}?/([A-Za-z0-9_.\-]+)")
_LSF_RE = re.compile(r"ls[-_]files(.{0,60})")

# Which `os.path.join` BASE names are the repository, measured rather than
# guessed.  量 2026-09-15 over `tools/*.py`, every base identifier by count:
#
#   d 133   root 90   tmp 89   ROOT 75   HERE 38   work 37   td 16   tree 11
#   dirpath 10   s 8   run 8   unit 7   kdir 7   DROP 6   ... REPO 3   repo 1
#
# `root`/`ROOT`/`REPO`/`repo` are this repository; `HERE` is `tools/`; and
# everything else is a temporary directory, a fixture, or a vendor tree --
# `tree` (11) is `rlxfw-marks.py`'s STAGED vendor tree, not this one.
# 🔴 The distinction is not cosmetic.  `tools/test-tcheck.py` writes
# `os.path.join(REPO, "tools", "tcheck.py")`, and with only ROOT/HERE
# recognised the generic scanner fell back to matching the bare word `tools`
# inside that string -- a DIRECTORY pattern that matches every file under
# `tools/`.  量, before this: bare `tools` was in 31 of the 88 step sets and a
# one-file diff of `tools/test-boot-timeline.sh` named 36 steps.
JOIN_REPO = ("ROOT", "root", "REPO", "repo", "REPO_ROOT")
JOIN_HERE = ("HERE", "_HERE", "here")


def _join_tokens(text):
    """(patterns, spans) for every `os.path.join(...)` in the text.

    `spans` is every join's character range, recognised or not.  The caller
    BLANKS them before the generic path regex runs, so a literal segment that
    has already been consumed as part of a path cannot also be read as a
    bare directory name, and a join on a temp directory contributes nothing.

    Leading string literals only: `os.path.join(root, rel)` yields nothing,
    which is the runtime-built path this tool declares it cannot see.
    """
    out, spans = set(), []
    for m in _JOIN_RE.finditer(text):
        spans.append((m.start(), m.end()))
        base, rest = m.group(1), m.group(2)
        if base not in JOIN_REPO and base not in JOIN_HERE:
            continue
        segs = []
        for piece in rest.split(","):
            piece = piece.strip()
            if not piece:
                continue
            sm = _STR_RE.fullmatch(piece)
            if not sm:
                break                      # a variable: the rest is runtime
            segs.append(sm.group(1).strip("/"))
        if not segs:
            continue
        if base in JOIN_HERE:
            segs.insert(0, "tools")
        pat = posixpath.normpath("/".join(segs).replace("\\", "/"))
        if pat not in (".", "..") and not pat.startswith("../"):
            out.add(pat)
    return out, spans


def _lsfiles_tokens(text):
    """`git ls-files` -> the whole tree; `ls-files "*.md"` -> that glob.

    The whole tree is `*`.  That is blunt and it is the right direction: a
    sweep over every tracked file reads every tracked file.
    """
    out = set()
    for tail in _LSF_RE.findall(text):
        globs = [g for g in _STR_RE.findall(tail)
                 if any(c in g for c in "*?[") and "\n" not in g]
        if globs:
            out.update(globs)
        else:
            out.add("*")
    return out


def token_scan(text, tops, files):
    """Every repo path this blob of text names, as match patterns."""
    joined, spans = _join_tokens(text)
    # A join's own literals are already accounted for; blank the span so the
    # generic regex below cannot read one of its segments a second time as a
    # bare top-level directory.
    if spans:
        buf = list(text)
        for lo, hi in spans:
            for i in range(lo, hi):
                buf[i] = " "
        text = "".join(buf)
    out = {p for p in joined
           if p.split("/", 1)[0] in tops or p in files}
    out |= _lsfiles_tokens(text)
    for name in _HERE_SH_RE.findall(text):
        # `ROOT="$(cd "$HERE/.." && pwd)"` is the standard preamble of every
        # shell suite here; normalising drops the `tools/..` it would
        # otherwise contribute, which matches no file and reads as noise.
        pat = posixpath.normpath("tools/" + name)
        if pat not in (".", "..") and not pat.startswith("../"):
            out.add(pat)
    topalt = "|".join(re.escape(t) for t in
                      sorted(tops, key=len, reverse=True))
    path_re = re.compile(
        r"(?<![\w/.$-])(?:\$\{?ROOT\}?/|\./)?"
        r"((?:%s)(?:/[A-Za-z0-9_.*?\-\[\]{}]+)*)" % topalt)
    for m in path_re.finditer(text):
        out.add(m.group(1).rstrip("/."))
    filealt = "|".join(re.escape(f) for f in
                       sorted(files, key=len, reverse=True))
    file_re = re.compile(r"(?<![\w/.\-])(%s)(?![\w])" % filealt)
    for m in file_re.finditer(text):
        out.add(m.group(1))
    return {p for p in out if p}


_SCRIPT_RE = re.compile(r"(?<![\w/.\-])(tools/[A-Za-z0-9_.\-/]+\.(?:py|sh))")
_DOCSTR_RE = re.compile(r'("""|\'\'\').*?\1', re.S)


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def code_half(text, rel):
    """The part of a source file that is not prose.

    🔴 THIS SPLIT IS THE DIFFERENCE BETWEEN AN INSTRUMENT AND `true`, and it
    was a measurement, not a preference.  量 2026-09-15, before it existed:
    `b40e40c`'s four-file `.md` diff named **62 of 88** steps, and
    `text/test-boot-timeline` was one of them -- reached through `CLAUDE.md`
    named in a comment in `test-boot-timeline.sh`, and through `*` derived
    from the words `git ls-files` inside a COMMENT of `desk-sweep.py`, which
    was itself reached only because another comment names that file.
    `CLAUDE.md` alone named 51 of the 88.  A tool that names two thirds of the
    suites on any prose commit tells a reader nothing.

    A path a tool READS is named in its code.  A path named in its comments is
    documentation.  Both are kept and both are reported -- the prose half in
    its own section, so nothing is hidden -- but only the code half sets the
    answer.

    The stripping is deliberately CONSERVATIVE: whole-line `#` comments, and
    for Python also triple-quoted blocks.  A trailing `# ...` on a line of
    code is left in, because deciding whether that `#` is inside a string
    needs a parser and the error would be in the unsafe direction.
    """
    if rel.endswith(".py"):
        text = _DOCSTR_RE.sub("\n", text)
    if rel.endswith((".py", ".sh")):
        text = "\n".join(ln for ln in text.split("\n")
                         if not ln.lstrip().startswith("#"))
    return text


def derive(step, tops, files, root=ROOT, depth=DEFAULT_DEPTH):
    """{pattern: {"code": [origins], "prose": [origins]}} for one step.

    `depth` is how far the indirection is followed: the step's `run:` text is
    depth 0, the tools it names is depth 1, the tools THOSE name is depth 2.
    Only a tool named in the CODE half is followed, or a file mentioned in a
    comment drags its whole path set in behind it.

    量 2026-09-15, live ci.yml at 89 `run:` steps, over all 4,198 tracked
    paths -- code (step, pattern) pairs, steps whose set contains `*`, and how
    many paths get a DIFFERENT answer than they do at depth 5:

        depth 1   466 pairs    8 `*`   4,198 of 4,198 differ
        depth 2   659 pairs   11 `*`     133 of 4,198 differ
        depth 3   683 pairs   11 `*`       0
        depth 4   683 pairs   11 `*`       0
        depth 5   683 pairs   11 `*`       0

    ⚠️ The absolute counts move with every step added to `ci.yml` and every
    tool added to `tools/` -- this reading was taken while another session was
    adding both, and the pair count moved 676 -> 683 between two runs an hour
    apart.  The FIXED POINT is the finding, and `C13` re-derives it live.

    So THREE is the fixed point, and it is the default because the 133 paths
    depth 2 gets wrong are MISSES, not over-approximations: `SPEC.md`,
    `RUNSHEET.md`, `docs/loader-command-semantics.md` and 130 others all reach
    `text/cardcheck mutation suite`, which runs
    `tools/test-cardcheck-mutants.py`, which runs `tools/cardcheck.py`, which
    reads `RUNSHEET.md` -- three hops.  A miss is the failure this tool exists
    to stop.

    ⚠️ Wall clock is deliberately NOT in that table.  One derivation measured
    between 0.66 s and 2.29 s across runs on this desk with another process
    working the same tree, so the honest statement is the one the tool was
    asked for -- seconds, not the sweep's ~1,000 -- and `list` end to end on a
    one-file range measured 2.05 s.  The counts above are deterministic and
    the timings are not.

    `C13` asserts the fixed point on the live tree rather than trusting this
    table, so a fourth level of indirection added tomorrow turns it red
    instead of becoming a silent miss.
    """
    origins = {}

    def add(pat, why, kind):
        d = origins.setdefault(pat, {"code": [], "prose": []})
        if why not in d[kind]:
            d[kind].append(why)

    seen_src = set()
    # A `run:` block is a command, not a source file: all of it is code.
    frontier = [(step["cmd"], step["cmd"], "the step's own `run:`")]
    for level in range(depth + 1):
        nxt = []
        for whole, code, why in frontier:
            code_pats = token_scan(code, tops, files)
            for pat in token_scan(whole, tops, files):
                add(pat, why, "code" if pat in code_pats else "prose")
            if level == depth:
                continue
            for rel in _SCRIPT_RE.findall(code):
                if rel in seen_src:
                    continue
                full = os.path.join(root, *rel.split("/"))
                if not os.path.isfile(full):
                    continue
                seen_src.add(rel)
                src = _read(full)
                nxt.append((src, code_half(src, rel), rel))
        frontier = nxt
        if not frontier:
            break
    return origins


def matches(pat, path):
    """Does a changed repo path fall inside one derived pattern?"""
    if pat == "*":
        return True
    if any(c in pat for c in "*?["):
        # fnmatchcase, not fnmatch: fnmatch normcases on Windows, and on this
        # project the case of a filename is part of the finding.
        return (fnmatch.fnmatchcase(path, pat)
                or fnmatch.fnmatchcase(os.path.basename(path), pat))
    pat = pat.rstrip("/")
    return path == pat or path.startswith(pat + "/")


# ---------------------------------------------------------------------------
# What changed
# ---------------------------------------------------------------------------

def _verify(root, rev):
    rc, _, _ = _git(root, "rev-parse", "--verify", "--quiet", rev + "^{commit}")
    return rc == 0


def changed_paths(root, spec):
    """(paths, description).  Refuses rather than returning an empty list."""
    rc, _, _ = _git(root, "rev-parse", "--git-dir")
    if rc != 0:
        raise Refuse("%s is not a git repository" % root)
    if spec is None:
        rc, out, err = _git(root, "diff", "--name-only", "--no-renames", "HEAD")
        if rc != 0:
            raise Refuse("git diff against HEAD failed: %s" % err.strip())
        paths = set(out.split("\n"))
        rc2, out2, _ = _git(root, "ls-files", "--others", "--exclude-standard")
        if rc2 == 0:
            paths |= set(out2.split("\n"))
        desc = "the working tree vs HEAD (tracked changes plus untracked files)"
        return sorted(p.strip().replace("\\", "/") for p in paths if p.strip()), desc

    if ".." in spec:
        a, b = spec.split("..", 1)
        b = b.lstrip(".")
        a, b = a.strip(), (b.strip() or "HEAD")
        for side in (a, b):
            if not _verify(root, side):
                raise Refuse("git cannot resolve `%s` in the range `%s`"
                             % (side, spec))
        rng, desc = spec, "range %s" % spec
    else:
        if not _verify(root, spec):
            raise Refuse("git cannot resolve `%s`" % spec)
        rng = "%s^..%s" % (spec, spec)
        if not _verify(root, spec + "^"):
            raise Refuse("`%s` has no parent -- give an explicit A..B range"
                         % spec)
        desc = "the single commit %s (range %s)" % (spec, rng)
    rc, out, err = _git(root, "diff", "--name-only", "--no-renames", rng)
    if rc != 0:
        raise Refuse("git diff %s failed: %s" % (rng, err.strip()))
    return sorted(p.strip().replace("\\", "/")
                  for p in out.split("\n") if p.strip()), desc


# ---------------------------------------------------------------------------
# The three modes
# ---------------------------------------------------------------------------

def suite_sets(root=ROOT, ci_path=None, depth=DEFAULT_DEPTH):
    ci_path = ci_path or os.path.join(root, CI_REL)
    steps = steps_of(ci_path, root)
    tops, files = vocabulary(root)
    return steps, {step_id(s): derive(s, tops, files, root, depth)
                   for s in steps}


def named_by(sets, paths, kind="code"):
    """{suite: [(pattern, path), ...]} for the suites the paths reach.

    `kind` is "code" (a path the tool's own code names -- the answer) or
    "any" (code or prose -- the wider reading, printed beside it).
    """
    hit = {}
    for suite, pats in sets.items():
        for pat in sorted(pats):
            if kind == "code" and not pats[pat]["code"]:
                continue
            for p in paths:
                if matches(pat, p):
                    hit.setdefault(suite, []).append((pat, p))
                    break
    return hit


def cmd_list(root, spec, depth, out=sys.stdout):
    paths, desc = changed_paths(root, spec)
    steps, sets = suite_sets(root, depth=depth)
    hit = named_by(sets, paths)

    print("mustrun list -- CI suites that read something in this diff",
          file=out)
    print("  %s" % desc, file=out)
    print("  %d changed path(s), %d `run:` step(s) in ci.yml"
          % (len(paths), len(steps)), file=out)
    if not paths:
        print("  nothing changed: no suite is named", file=out)
        print("  0 of %d step(s) named" % len(steps), file=out)
        return 0
    if any(p == CI_REL.replace(os.sep, "/") for p in paths):
        print("  NOTE  .github/workflows/ci.yml itself changed -- the STEP "
              "LIST moved, which this tool reads and does not treat as an "
              "input of every step.  Re-enumerate before trusting the names "
              "below.", file=out)
    print(file=out)
    order = [step_id(s) for s in steps if step_id(s) in hit]
    for suite in order:
        pairs = hit[suite]
        shown = "; ".join("%s <- %s" % (pat, path) for pat, path in pairs[:3])
        if len(pairs) > 3:
            shown += "; (+%d more)" % (len(pairs) - 3)
        print("  MUST RUN  %-44s %s" % (suite, shown), file=out)
    print(file=out)
    print("  %d of %d step(s) named; %d not named"
          % (len(hit), len(steps), len(steps) - len(hit)), file=out)

    wide = named_by(sets, paths, kind="any")
    only_prose = [step_id(s) for s in steps
                  if step_id(s) in wide and step_id(s) not in hit]
    print("  %d more are named only through a path in a tool's COMMENTS, "
          "which is documentation rather than an input:" % len(only_prose),
          file=out)
    for suite in only_prose:
        pat, path = wide[suite][0]
        print("      weaker   %-42s %s <- %s" % (suite, pat, path), file=out)
    if len(steps) and len(hit) * 2 >= len(steps):
        print("  OVER HALF the steps are named.  That is information: the "
              "cheap move is `tools/desk-sweep.py run --dest <ext4 path>` "
              "rather than a hand-picked list.", file=out)
    return 1 if hit else 0


def cmd_paths(root, suite, depth, out=sys.stdout):
    steps, sets = suite_sets(root, depth=depth)
    ids = [step_id(s) for s in steps]
    if suite in sets:
        key = suite
    else:
        cand = [i for i in ids if i.split("/", 1)[1] == suite]
        if not cand:
            cand = [i for i in ids if suite in i]
        if not cand:
            raise Refuse("no step called `%s`.  `mustrun.py list` prints the "
                         "names, which are `<job>/<step name>`" % suite)
        if len(cand) > 1:
            raise Refuse("`%s` names %d steps (%s) -- give the full "
                         "`<job>/<name>`" % (suite, len(cand),
                                             ", ".join(cand)))
        key = cand[0]
    pats = sets[key]
    ncode = sum(1 for p in pats if pats[p]["code"])
    print("mustrun paths -- the input path set derived for one step", file=out)
    print("  step: %s" % key, file=out)
    print("  depth: %d (0 = the `run:` text, 1 = the tools it invokes, ...)"
          % depth, file=out)
    print("  CODE patterns decide the answer; PROSE ones are paths named only "
          "in a comment and are printed so the derivation can be audited",
          file=out)
    print(file=out)
    for pat in sorted(pats):
        for kind in ("code", "prose"):
            if pats[pat][kind]:
                print("  %-5s %-46s <- %s"
                      % (kind.upper(), pat, ", ".join(pats[pat][kind])),
                      file=out)
    print(file=out)
    print("  %d pattern(s): %d code, %d prose-only"
          % (len(pats), ncode, len(pats) - ncode), file=out)
    if "*" in pats and pats["*"]["code"]:
        print("  `*` is in the CODE set: the step sweeps the whole tree, so "
              "EVERY change names it.", file=out)
    return 0


# ---------------------------------------------------------------------------
# The controls
# ---------------------------------------------------------------------------

FIX_MAIN = """\
name: fixture
on: [push]
jobs:
  a:
    steps:
      - uses: actions/checkout@v4
      - name: docsonly
        run: cat docs/a.md
      - name: notesonly
        run: |
          cat notes/b.md
          echo done
      - run: shellcheck refs/*.sh
"""

FIX_TREE = FIX_MAIN + """\
      - name: sweeper
        run: /usr/bin/python3 tools/_fx_sweep.py
"""

FIX_SWEEP_SRC = """\
import subprocess
def all_tracked(root):
    return subprocess.run(["git", "ls-files"], cwd=root).stdout
"""

# The six red runs, with the step each one failed at.  Run id, ISO date, the
# sha of the run BEFORE it (the push's floor), the sha CI had at its head, and
# the `<job>/<step name>` that went red.  34958415918 carries two failing
# steps, which is why there are seven rows and six runs.
#
# 🔴 The floor is the previous run's head and it is DERIVED, not eyeballed.
# The first draft of this table had `H3`'s floor at `1bbd587` -- the run two
# before it -- because the list was read by hand in run-id order.  It still
# passed, because `ledgerscan check` sweeps the whole tree and would be named
# by any range at all, which is exactly the shape of a control agreeing for
# the wrong reason.  量, sorting `gh run list` by `createdAt` and asking git
# for the commit count: five of the six pushes carry ONE commit and
# `34972020564` carries THREE.  That one is `H7`.
HISTORY = [
    ("H1", 34745994861, "2026-09-13", "2618af3f", "2ee0c6d",
     "census/census"),
    ("H2", 34811279996, "2026-09-14", "1cf9ccf0", "1bbd587",
     "instruments/tccensus"),
    ("H3", 34839959119, "2026-09-14", "558cc657", "6923b86",
     "text/ledgerscan check (exit-code gate)"),
    ("H4", 34840698703, "2026-09-14", "6923b86",  "383804a",
     "text/ledgerscan check (exit-code gate)"),
    ("H5", 34958415918, "2026-09-15", "cbd1d0de", "490f5f5",
     "text/citecheck"),
    ("H6", 34958415918, "2026-09-15", "cbd1d0de", "490f5f5",
     "instruments/tccensus"),
    ("H7", 34972020564, "2026-09-15", "3248940",  "b40e40c",
     "text/test-boot-timeline"),
]


def self_test(root=ROOT, out=sys.stdout):
    import tempfile
    npass = nfail = 0

    def ck(label, cond, extra=""):
        nonlocal npass, nfail
        if cond:
            npass += 1
            print("  ok    %-58s %s" % (label, extra), file=out)
        else:
            nfail += 1
            print("  FAIL  %-58s %s" % (label, extra), file=out)

    print("mustrun --self-test -- V2 and V3 are planted and must fire",
          file=out)

    ci = os.path.join(root, CI_REL)
    try:
        ds = desk_sweep(root)
        steps = steps_of(ci, root)
    except Refuse as exc:
        print("REFUSED: %s" % exc, file=out)
        print("RESULT: 0 passed, 1 failed", file=out)
        return 1

    ck("C1  the step list comes from desk-sweep's own enumerator",
       len(steps) > 50 and all("cmd" in s for s in steps),
       "%d run steps" % len(steps))

    line = ds.enumerate_steps_linewise(ci)
    ck("C2  THE CONTROL ON C1: the line-based enumerator comes out SHORT",
       len(line) < len(steps), "%d of %d" % (len(line), len(steps)))

    tops, files = vocabulary(root)
    sets = {step_id(s): derive(s, tops, files, root, DEFAULT_DEPTH) for s in steps}
    scripted = [s for s in steps if _SCRIPT_RE.search(s["cmd"])]
    empty = [step_id(s) for s in scripted if not sets[step_id(s)]]
    ck("C3  every step that invokes a tool gets a non-empty path set",
       not empty, "%d such step(s), %d empty" % (len(scripted), len(empty)))

    tmp = tempfile.mkdtemp(prefix="mustrun-")
    os.makedirs(os.path.join(tmp, "tools"))
    with open(os.path.join(tmp, "tools", "_fx_sweep.py"), "w") as fh:
        fh.write(FIX_SWEEP_SRC)
    fmain = os.path.join(tmp, "main.yml")
    ftree = os.path.join(tmp, "tree.yml")
    with open(fmain, "w") as fh:
        fh.write(FIX_MAIN)
    with open(ftree, "w") as fh:
        fh.write(FIX_TREE)

    fsteps = ds.enumerate_steps(fmain)
    fsets = {step_id(s): derive(s, tops, files, tmp, DEFAULT_DEPTH) for s in fsteps}
    ck("C4  POSITIVE on the matcher: docs/a.md names the one step that "
       "reads docs",
       sorted(named_by(fsets, ["docs/a.md"])) == ["a/docsonly"],
       str(sorted(named_by(fsets, ["docs/a.md"]))))

    zero = named_by(fsets, ["bench/2026-09-15/C1-esc.log"])
    ck("C5  V2, THE NEGATIVE CONTROL: a path in no step's set names ZERO",
       zero == {}, "named %s" % (sorted(zero) or "nothing"))

    gsh = named_by(fsets, ["refs/x.sh"])
    gpy = named_by(fsets, ["refs/x.py"])
    ck("C6  a glob discriminates: refs/*.sh takes .sh and not .py",
       sorted(gsh) == ["a/#3"] and gpy == {},
       "%s / %s" % (sorted(gsh), sorted(gpy)))

    tsteps = ds.enumerate_steps(ftree)
    tsets = {step_id(s): derive(s, tops, files, tmp, DEFAULT_DEPTH) for s in tsteps}
    ck("C7  `git ls-files` with no glob becomes the whole tree",
       bool(tsets["a/sweeper"].get("*", {}).get("code"))
       and "a/sweeper" in named_by(tsets, ["bench/2026-09-15/C1-esc.log"]),
       "sweeper's set: %d pattern(s)" % len(tsets["a/sweeper"]))

    try:
        changed_paths(root, "nosuchrev1234..HEAD")
        r8 = "returned a list"
    except Refuse as exc:
        r8 = str(exc)
    ck("C8  V3a REFUSAL: a range git cannot resolve refuses",
       r8.startswith("git cannot resolve"), r8[:44])

    bad = os.path.join(tmp, "bad.yml")
    with open(bad, "w") as fh:
        fh.write("jobs:\n  a:\n    steps:\n      - name: x\n     run: [\n")
    try:
        steps_of(bad, root)
        r9 = "returned a list"
    except Refuse as exc:
        r9 = str(exc)
    ck("C9  V3b REFUSAL: a ci.yml that will not parse refuses",
       "would not parse" in r9 or "declares no `run:` step" in r9, r9[:44])

    one = named_by(sets, ["tools/test-boot-timeline.sh"])
    ck("C10 the over-approximation is not total: a one-path diff on the LIVE "
       "file names fewer than all steps",
       0 < len(one) < len(steps), "%d of %d" % (len(one), len(steps)))

    whole = sorted(k for k, v in sets.items() if v.get("*", {}).get("code"))
    ck("C11 THE REASON C5 IS SYNTHETIC: at least one live step sweeps the "
       "whole tree",
       bool(whole), "%d step(s), e.g. %s" % (len(whole),
                                             whole[0] if whole else "-"))

    narrow = named_by(sets, ["CLAUDE.md"], "code")
    widest = named_by(sets, ["CLAUDE.md"], "any")
    ck("C12 THE SPLIT IS LOAD-BEARING: a path named in comments reaches far "
       "more steps than a path named in code",
       len(narrow) < len(widest),
       "CLAUDE.md: %d code, %d code-or-prose, of %d"
       % (len(narrow), len(widest), len(steps)))

    # THE CONTROL ON THE DEFAULT DEPTH.  `derive`'s table says depth 3 is the
    # fixed point; this asserts it on the live tree instead of trusting the
    # table, so a fourth level of indirection added tomorrow turns it red
    # rather than becoming a silent miss.
    def npairs(d):
        st = {step_id(x): derive(x, tops, files, root, d) for x in steps}
        return sum(1 for k in st for q in st[k] if st[k][q]["code"])
    here, deeper = npairs(DEFAULT_DEPTH), npairs(DEFAULT_DEPTH + 1)
    ck("C13 the default depth is a FIXED POINT: one level deeper adds no "
       "pattern",
       here == deeper and here > 0,
       "depth %d: %d code pair(s); depth %d: %d"
       % (DEFAULT_DEPTH, here, DEFAULT_DEPTH + 1, deeper))

    # BOTH DIRECTIONS on the join reader, because getting one of them right is
    # what produced the defect: a repo-anchored join must yield the whole path
    # and NOT the bare directory, and a temp-directory join must yield nothing
    # at all rather than a top-level name lifted out of a fixture.
    good = token_scan('p = os.path.join(REPO, "tools", "tcheck.py")',
                      tops, files)
    fixt = token_scan('q = os.path.join(tmp, "bench", "x.log")', tops, files)
    ck("C14 a repo-anchored os.path.join yields the PATH and not the bare "
       "directory, and a temp-directory one yields nothing",
       good == {"tools/tcheck.py"} and fixt == set(),
       "REPO -> %s ; tmp -> %s" % (sorted(good), sorted(fixt)))

    # -- the historical controls --------------------------------------------
    need = sorted({s for _l, _r, _d, s, _h, _n in HISTORY}
                  | {h for _l, _r, _d, _s, h, _n in HISTORY})
    missing = [s for s in need if not _verify(root, s)]
    if missing:
        print("  skip   historical controls%s%s"
              % (" " * 29,
                 "this clone cannot reach %d of the %d shas the seven "
                 "controls need (%s) -- on a shallow checkout the ranges CI "
                 "actually tested do not exist, and a control that cannot "
                 "read its own population must stand down rather than pass"
                 % (len(missing), len(need), ", ".join(missing[:3]))),
              file=out)
    else:
        narrow = 0
        for label, run, date, floor, head, want in HISTORY:
            rng = "%s..%s" % (floor, head)
            try:
                paths, _ = changed_paths(root, rng)
                got = named_by(sets, paths)
            except Refuse:
                got, paths = {}, []
            # WHICH patterns named it, not just that something did.  And the
            # strength of the control is a property of the SUITE, not of which
            # pattern happened to match first: a suite whose set contains `*`
            # is named by ANY non-empty diff, so it would score a hit however
            # badly the derivation worked.
            pats = sorted({q for q, _p in got.get(want, [])})
            via = ", ".join("`%s`" % q for q in pats[:3]) or "-"
            sweeps = bool(sets.get(want, {}).get("*", {}).get("code"))
            if not sweeps:
                narrow += 1
            ck("%s  run %d %s %s -> %s" % (label, run, date, rng, want),
               want in got,
               "%d path(s), %d named; via %s%s"
               % (len(paths), len(got), via,
                  "  <- this SUITE sweeps git ls-files, so the control is WEAK"
                  if sweeps else ""))

        # H7's second half: the single commit is NOT enough, which is the
        # whole reason a range is the push and not the commit.
        try:
            p7, _ = changed_paths(root, "b40e40c")
            g7 = named_by(sets, p7)
            r7 = "text/test-boot-timeline" not in g7
        except Refuse:
            p7, g7, r7 = [], {}, False
        ck("H7b THE CONTROL ON H7: b40e40c's own commit does NOT name it",
           r7, "%d path(s), %d suite(s)" % (len(p7), len(g7)))

        # THE STRENGTH OF THE SEVEN, said out loud.  `text/ledgerscan check`
        # and `text/citecheck` sweep `git ls-files`, so H3, H4 and H5 are
        # named by any non-empty diff at all and prove nothing about the
        # derivation.  H1, H2, H6 and H7 name suites that do NOT sweep the
        # tree, and those four are the ones carrying the claim.
        ck("H8  THE CONTROL ON H1..H7: at least four of them name a suite "
           "that does NOT sweep the whole tree",
           narrow >= 4,
           "%d of %d; the other %d would be named by any non-empty diff"
           % (narrow, len(HISTORY), len(HISTORY) - narrow))

    print("RESULT: %d passed, %d failed" % (npass, nfail), file=out)
    return 0 if nfail == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="which CI suites read files that changed")
    ap.add_argument("mode", nargs="?", choices=["list", "paths"])
    ap.add_argument("arg", nargs="?",
                    help="list: a git range (default: the working tree vs "
                         "HEAD).  paths: a step name, `<job>/<name>`")
    ap.add_argument("--depth", type=int, default=DEFAULT_DEPTH,
                    help="how far to follow the step -> tool -> tool "
                         "indirection (default %d, the measured fixed point)"
                         % DEFAULT_DEPTH)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test(a.root)
        if a.mode == "list":
            return cmd_list(a.root, a.arg, a.depth)
        if a.mode == "paths":
            if not a.arg:
                raise Refuse("paths needs a step name")
            return cmd_paths(a.root, a.arg, a.depth)
        ap.print_help()
        return 3
    except Refuse as exc:
        print("REFUSED: %s" % exc)
        return 3


if __name__ == "__main__":
    sys.exit(main())
