#!/usr/bin/env python3
"""test-citecheck-mutants -- the mutation suite for tools/citecheck.py.

Thirty-three green controls is a claim about the controls.  Every mutation
below must make `citecheck.py --self-test` exit non-zero, and every row NAMES
the control it is supposed to turn red -- that naming is not decoration:
`tools/flashwin.py`'s first mutation pass reported 8/8 killed and every kill
was invalid, because the harness was red before any mutation was applied.

So the first case is the unmutated baseline through the same harness, and
`B0-IN-TREE` runs the unmutated tool INSIDE the temp tree, which is where every
mutation is judged.  A tree missing a file the tool reads makes the whole run
red before anything is mutated, and a list of kills looks identical either way;
量 2026-08-31, exactly that happened to test-replay-capture-mutants.  citecheck
imports `spec-check.py` from beside itself, so the temp tree needs both files
and a run that forgot one would "kill" everything.

A mutation whose anchor is MISSING is reported as a SURVIVOR and not as a skip.
A moved anchor and a mutation that changed nothing are the same exit code, and
only one of them is fine.

⚠️ WHAT THIS SUITE DOES NOT REACH, stated rather than left to be found: it runs
`--self-test` only, so a property that is asserted exclusively by
`tools/test-citecheck.sh` -- the shape of the committed baseline FILE, six
columns and no duplicate keys -- has no mutant here.  The two properties that
were shell-only when this was written, `--write-baseline` not touching the file
and the two-space case-line contract, were moved INTO `--self-test` as `T24`
and `T25` for exactly this reason, and `M22`/`M23` are their mutants.

`M24`-`M50` are the rename section (`T27`-`T37`), one per branch.  Three kinds
of line there carry none, and why is stated rather than left to be found: the
caches (a cache that always recomputes gives the same answers, only slower);
the parser's fall-through for a status other than A, D or R, which
`--diff-filter=ADR` never emits; and `_back` running out of events, which
needs a history whose root commit's adds are hidden -- every path's history
begins with an add.  量 2026-10-09, the first run had a twenty-eighth: it
dropped `moved_to`'s check that an event ENDED a life at the path, and it
SURVIVED, because a life walked forward from its start reaches the same end.
The check was an economy and not a guard; it is now an index with no branch.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/citecheck.py")
SPEC = os.path.join(ROOT, "tools/spec-check.py")

MUT = [
    # ---------------------------------------------------- the refusals
    ("M1  the shallow-clone refusal removed                (kills T3)",
     '    if shallow:\n        _refuse("this is a SHALLOW clone.',
     '    if False:\n        _refuse("this is a SHALLOW clone.'),

    ("M2  the empty-population refusal removed             (kills T22)",
     '    if nmd == 0:\n        _refuse(',
     '    if False:\n        _refuse('),

    ("M3  the no-citations-at-all refusal removed          (kills T5/T10/T11)",
     '    if not cites and not ambig:\n        _refuse(',
     '    if False:\n        _refuse('),

    # ---------------------------------------------------- the oracle itself
    ("M4  the cited file is read NOW instead of at the citing commit (T1)",
     '        old = then(sha, c.target)',
     '        old = cur(c.target)'),

    ("M5  a line split on \\r as well as \\n, the original defect (kills T19)",
     '    return blob.decode("utf-8", "replace").split("\\n")',
     '    return blob.decode("utf-8", "replace").splitlines()'),

    ("M6  an uncommitted citing line oracled anyway        (kills T26)",
     '        if sha == ZERO:',
     '        if False:'),

    # ---------------------------------------------------- the filters
    ("M7  the fence mask ignored                           (kills T5)",
     '        if ln - 1 < len(mask) and mask[ln - 1]:',
     '        if False:'),

    ("M8  the transcript filter removed                    (kills T10)",
     '        if text[m.end():m.end() + 1] == ":":',
     '        if False:'),

    # 🔴 M9 mutates the LOOKBEHIND and not a filter, because the explicit
    # URL filter this row used to mutate could not fire -- removing it
    # killed nothing, which is how it was found.  `/` is in the
    # lookbehind's class, so in `https://example.com:8080` the only
    # position where the host could start is preceded by `/` and is
    # rejected before any filter runs.  The filter is gone; this mutates
    # the thing that actually does the work.
    ("M9  `/` dropped from the lookbehind class            (kills T6)",
     r"    r'(?<![0-9A-Za-z_./+-])'",
     r"    r'(?<![0-9A-Za-z_.+-])'"),

    ("M10 the self-reference filter removed                (kills T11)",
     '        if SELFREF_RX.search(lines[ln - 1] if ln - 1 < len(lines) else ""):',
     '        if False:'),

    ("M11 an ambiguous basename resolved to the first      (kills T12)",
     '            elif len(cands) > 1:                                   # class 8',
     '            elif False:'),

    ("M12 the dotted extension made optional               (kills T7/T8/T9)",
     r"    r'((?:[A-Za-z0-9_.+-]+/)*[A-Za-z0-9_+-]+\.[A-Za-z][A-Za-z0-9_+-]*)'",
     r"    r'((?:[A-Za-z0-9_.+-]+/)*[A-Za-z0-9_+-]+(?:\.[A-Za-z][A-Za-z0-9_+-]*)?)'"),

    ("M13 SRCREF_EXEMPT ignored                            (kills T20)",
     '        if SC.srcref_exempt(rel):',
     '        if False:'),

    # ---------------------------------------------------- the escape decode
    ("M14 escapes not decoded, so a .tsv cannot be quoted  (kills T13)",
     '    for a, b in ESCAPES:\n        s = s.replace(a, b)\n    return s',
     '    return s'),

    ("M15 the token tolerance made infinite                (kills T13b)",
     'TOKEN_TOL = 3',
     'TOKEN_TOL = 10 ** 9'),

    # ---------------------------------------------------- the zero-oracle checks
    ("M16 M1 past-end-of-file not reported                 (kills T14)",
     '        if c.start > n or (c.end is not None and c.end > n):',
     '        if False:'),

    ("M17 M2 an inverted range not reported                (kills T15)",
     '        if c.end is not None and c.end < c.start:',
     '        if False:'),

    ("M18 M3 a now-blank cited line not reported           (kills T16)",
     '        if not SC._norm(cl[c.start - 1]):',
     '        if False:'),

    # ---------------------------------------------------- the baseline
    ("M19 the baseline sweep FORWARD disabled              (kills T17)",
     '    new = [f for f in findings if baseline_key(f) not in want]',
     '    new = []'),

    ("M20 the baseline sweep REVERSE disabled              (kills T18)",
     '    stale = [r for r in rows\n'
     '             if (r.kind, r.src, r.path, r.start, r.digest) not in have\n'
     '             and r.src not in suspended]',
     '    stale = []'),

    ("M21 a malformed baseline row silently skipped        (kills T18b)",
     '            if len(parts) < 5:\n                bad.append((i, raw))',
     '            if len(parts) < 5:\n                pass'),

    # ---------------------------------------------------- the two shell-only ones
    ("M22 --write-baseline writes the file in place        (kills T24)",
     '        sys.stdout.write(baseline_text(fs + secondary(root, cites, rev)))',
     '        _t = baseline_text(fs + secondary(root, cites, rev))\n'
     '        open(baseline, "w", encoding="utf-8").write(_t)\n'
     '        sys.stdout.write(_t)'),

    ("M23 a case line printed at FOUR spaces               (kills T25)",
     '            self.lines.append("  ok     %-54s %s" % (label, detail))',
     '            self.lines.append("    ok     %-54s %s" % (label, detail))'),

    # ---------------------------------------------------- renames (T27-T37)
    # A move must not blind the oracle.  One row per branch of citecheck's
    # `renames, from git`, each naming the case it must turn red.
    ("M24 the oracle's second read, under the old name     (kills T27)",
     '        old = then(sha, c.target) or _followed(then, history, sha, '
     'c.target, v)',
     '        old = then(sha, c.target)'),

    ("M25 a followed verdict not counted                   (kills T27)",
     '    v["FOLLOWED"] += old is not None',
     '    pass'),

    ("M26 renames=False reads history all the same        (kills T27b)",
     '            ev = self._index() + self._log() if self.renames else []',
     '            ev = self._index() + self._log()'),

    ("M27 git log told to detect no renames                (kills T27)",
     '        _rc, out = git(self.root, "log", "-M", "--topo-order",',
     '        _rc, out = git(self.root, "log", "--no-renames", "--topo-order",'),

    ("M28 a rename line of --name-status -z not parsed     (kills T27)",
     '        if st[:1] == "R" and i + 2 < len(f):',
     '        if False:'),

    ("M29 an add or a delete line not parsed               (kills T30)",
     '        elif st in ("A", "D") and i + 1 < len(f):',
     '        elif False:'),

    ("M30 the index not read against HEAD                  (kills T37)",
     '        if self.rev is not None:\n            return []',
     '        if True:\n            return []'),

    ("M31 the index not younger than every commit          (kills T37)",
     '        if b == INDEX:\n            return True',
     '        if False:\n            return True'),

    ("M32 a walk back that leaves its line of history      (kills T34)",
     '            if line is not None and not self.descends(c, line):',
     '            if False:'),

    ("M33 an event at or before the citing commit ignored  (kills T27)",
     '            if self.descends(c, sha):\n                return p',
     '            if False:\n                return p'),

    ("M34 a rename into the path not stepped back through  (kills T27)",
     '            if kind == "R" and new == p:',
     '            if False:'),

    ("M35 an add after the citing commit walked past       (kills T30)",
     '            return None             # created after it, or its line '
     'breaks here',
     '            continue'),

    ("M36 an old path that went to two places: one picked  (kills T35)",
     '            one = len(dests) == 1 and not dead',
     '            one = len(dests) >= 1 and not dead'),

    ("M37 a deletion beside a move ignored                 (kills T35)",
     '            one = len(dests) == 1 and not dead',
     '            one = len(dests) == 1'),

    ("M38 an old path matched exactly, never as a suffix   (kills T31)",
     '            for x in (olds if suffix else [p for p in olds if p == path]):',
     '            for x in [p for p in olds if p == path]:'),

    ("M39 a deleted file counted as a place it went to     (kills T30)",
     '            dests.discard(None)',
     '            pass'),

    ("M40 a forward walk that reaches the tip finds nothing (kills T29)",
     '            if n is None:\n                return q',
     '            if n is None:\n                return None'),

    ("M41 a forward walk that leaves its line of history   (kills T34)",
     '            if not self.descends(c, c2):',
     '            if False:'),

    ("M42 a second move not followed forward               (kills T33)",
     '            if kind == "R" and old == q:',
     '            if False:'),

    ("M43 a delete walked past, forward                    (kills T30)",
     "            return None             # deleted: this file's line ends",
     '            continue'),

    ("M44 a path with a tracked candidate asks history too (kills T12)",
     '        if hit:\n            return hit',
     '        if False:\n            return hit'),

    ("M45 an untracked path not resolved through history   (kills T29)",
     '        if dest:\n            self.counts["renamed"] += 1',
     '        if False:\n            self.counts["renamed"] += 1'),

    ("M46 a refused rename not counted                     (kills T35)",
     '        self.counts["rename-refused"] += refused',
     '        pass'),

    ("M47 baseline rows not read through history          (kills T36)",
     '    rows, moved = rows_now(rows, cites.history)',
     '    moved = 0'),

    ("M48 an M3 row's digest not re-derived for its new path (kills T36)",
     '                dg = digest(key(path, r.start))',
     '                pass'),

    ("M49 a moved CITING file not read through history     (kills T36)",
     '        src, path, dg = now(r.src), now(r.path), r.digest',
     '        src, path, dg = r.src, now(r.path), r.digest'),

    ("M50 a TRACKED row path read through history anyway   (kills T36)",
     '        return p if p in history.tracked else (',
     '        return p if False else ('),
]


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, cwd=cwd)
    return r.returncode


def main():
    base = run(SRC, ROOT)
    if base != 0:
        sys.exit("REFUSING: the unmutated self-test already fails "
                 f"(rc={base}) -- every mutation below would 'kill' a suite "
                 "that was already red")
    print(f"baseline: unmutated --self-test rc={base}  (B0, and it is a case)")

    src = open(SRC, encoding="utf-8").read()
    survived = []
    for name, old, new in MUT:
        d = tempfile.mkdtemp(prefix="citecheck-mut-")
        try:
            work = os.path.join(d, "router-rebuild")
            os.makedirs(os.path.join(work, "tools"))
            # 🔴 B0-IN-TREE.  citecheck imports spec-check from beside itself
            # for fence_mask / code_spans / _norm / SRCREF_EXEMPT; a temp tree
            # without it refuses, every mutant "dies", and the output is
            # indistinguishable from a suite that works.
            shutil.copy(SPEC, os.path.join(work, "tools/spec-check.py"))
            tgt = os.path.join(work, "tools/citecheck.py")
            shutil.copy(SRC, tgt)
            if run(tgt, work) != 0:
                sys.exit(f"REFUSING at {name}: the UNMUTATED tool fails in the "
                         f"temp tree, so every kill below would be invalid")
            n = src.count(old)
            if n != 1:
                survived.append(f"{name}  [anchor occurs {n} times, "
                                f"not applied]")
                print(f"  FAIL  {name}   ANCHOR x{n} (not applied)")
                continue
            open(tgt, "w", encoding="utf-8").write(src.replace(old, new, 1))
            rc = run(tgt, work)
            killed = rc != 0
            # `  ok  ` / `  FAIL  ` is the shape tools/ci-census.py parses.
            print(f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                  f"rc={rc} ({'killed' if killed else 'SURVIVED'})")
            if not killed:
                survived.append(name)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if survived:
        print(f"{len(survived)} MUTATION(S) SURVIVED -- those controls do not "
              f"work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(MUT)} mutations killed")
    return 0


sys.exit(main())
