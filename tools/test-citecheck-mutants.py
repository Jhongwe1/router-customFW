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
