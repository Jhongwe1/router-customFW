#!/usr/bin/env python3
"""test-entrycheck-mutants -- the mutation suite for tools/entrycheck.py.

WHY IT ARRIVES WITH THE TOOL
----------------------------
entrycheck reads gate P5e's definition of done, and a green self-test is a
claim about its controls.  Each row below breaks one row's comparison or
definition, or one of the two rules that keep a verdict honest (an UNMEASURED
row fails `check`; a waived row never reads PASS), and names the self-test
case that must turn red.

WHAT IT COVERS, AND WHAT IT DOES NOT
------------------------------------
Thirteen rows of the DoD are mutated here: E1's boundary, E2's CJK rule, E5's
escaped pipe, E6's badge rule, E8w's large flag, E10's per-section limit, E14's
`if: false`, E14w's whole-line match, E15's hop limit, E16's path-start rule,
E17's directory-free driver pattern, E19's qemu transcripts as records, and
E21's term list -- plus the by-name exemption mechanism E16, E19 and E21
share (CLAUDE.md's exemption from E16 and E19 is the case it names).  The
other rows' controls are self-test cases that no mutant here exercises: E3,
E4, E7, E8, E9, E11, E12, E13, E18 and E20.

THE ROWS THAT ARE NOT MUTATIONS, as test-digestscan-mutants.py has them
  B0  the unmutated tool must pass IN THE TEMP TREE, or every kill is free.
  A0  every anchor occurs exactly once in the tool.
  W0  a kill counts only if the case the row NAMES went red -- rc != 0 alone
      is not a kill.

The temp tree holds real directories and copies of the three files the
self-test reads: the tool, and the two sources E14w's Q1/Q2 re-read
(src/Makefile, src/rlxboot/test/run-host-tests.sh).

Run:  /usr/bin/python3 tools/test-entrycheck-mutants.py [--jobs 8] [--only MN1,MV2]
"""
import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "entrycheck.py")

FIXTURES = [
    "src/Makefile",
    "src/rlxboot/test/run-host-tests.sh",
]

MUT = [
    # ---- comparisons -----------------------------------------------------
    ("MN1  E1's limit read as < 150, not <= 150                (kills E1p)",
     '    return (PASS if n <= 150 else RED), f"{n} lines", []',
     '    return (PASS if n < 150 else RED), f"{n} lines", []'),
    ("MN6  E10's per-section limit dropped                     (kills E10s)",
     "    ok = total <= 300 and not over",
     "    ok = total <= 300"),
    ("MN9  E15 follows three hops, not two                     (kills E15h)",
     "MAX_HOPS = 2\n",
     "MAX_HOPS = 3\n"),

    # ---- definitions -----------------------------------------------------
    ("MN2  a CJK run counts as one word                        (kills E2c)",
     "        for ch in tok:\n            if is_cjk(ch):",
     "        for ch in tok:\n            if False:"),
    ("MN3  an escaped pipe splits a cell                       (kills E5e)",
     r'''        if ch == "\\" and i + 1 < len(s):''',
     "        if False:"),
    ("MN4  a badge counts as E6's image                        (kills E6r)",
     "        if any(b in tgt.lower() for b in BADGE):",
     "        if False:"),
    ("MN5  E8w ignores the page's large flag                   (kills E8wr)",
     "        if large:\n            big.append(name)",
     "        if False:\n            big.append(name)"),
    ("MN7  a step under `if: false` still counts               (kills E14f)",
     '    return c in ("false", "${{false}}")',
     "    return False"),
    ("MN8  E14w accepts its line inside a longer line          (kills E14wx)",
     "    missing = [w for w in want if w not in lines]",
     "    missing = [w for w in want if not any(w in ln for ln in lines)]"),
    ("MN10 'plan/' matches inside another path                 (kills E16p)",
     r'''E16_PATH = re.compile(r"(?<![\w./\\-])(?:\.{1,2}/)*plan/")''',
     r'''E16_PATH = re.compile(r"(?:\.{1,2}/)*plan/")'''),
    ("MN11 E17's drivers looked for under config/rlxfw-src/   (kills E17p)",
     r'''DRIVER_PATH = re.compile(r"^(.+?)/linux-2\.6\.30/drivers/(?:.+/)?"''',
     r'''DRIVER_PATH = re.compile(r"^(config/rlxfw-src)/linux-2\.6\.30/drivers/(?:.+/)?"'''),
    ("MN12 qemu/<date>*/ transcripts are not records           (kills E19p)",
     r'''RECORD_DIR_RE = re.compile(r"^qemu/20[0-9]{2}-[0-9]{2}-[0-9]{2}[^/]*/")''',
     r'''RECORD_DIR_RE = re.compile(r"(?!)")'''),
    ("MN13 E21's list loses a term                             (kills E21r)",
     '                    r"|résumé|resumé|résume|portfolio")',
     '                    r"|résumé|resumé|résume")'),
    ("MN14 a by-name exemption is never applied                (kills E16p)",
     "        if p in names:\n            continue",
     "        if False:\n            continue"),

    # ---- the verdict logic -----------------------------------------------
    ("MV1  an UNMEASURED online row passes check               (kills U1)",
     "    ok = not red and not stale and not un_off and (offline or not un_on)",
     "    ok = not red and not stale and not un_off"),
    ("MV2  a waived row is reported PASS                       (kills W1)",
     "            if v == RED:\n                v = WAIVED",
     "            if v == RED:\n                v = PASS"),
]


def make_tree(d):
    """Real directories, copies not links."""
    work = os.path.join(d, "router-rebuild")
    os.makedirs(os.path.join(work, "tools"))
    for rel in FIXTURES:
        dst = os.path.join(work, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(ROOT, rel), dst)
    return work


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=cwd)
    return r.returncode, r.stdout


CASE = re.compile(r"^  FAIL  +([A-Z][0-9A-Za-z]*)\b", re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="comma-separated mutation ids")
    ap.add_argument("--jobs", type=int, default=1, help="mutants at once")
    args = ap.parse_args()
    rows = MUT
    if args.only:
        want = {x.strip() for x in args.only.split(",")}
        rows = [r for r in MUT if r[0].split()[0] in want]
        missing = want - {r[0].split()[0] for r in MUT}
        if missing:
            sys.exit(f"no such mutation(s): {sorted(missing)}")

    try:
        src = open(SRC, encoding="utf-8").read()
    except OSError as e:
        sys.exit(f"cannot read {SRC}: {e.strerror}")

    # --- B0 ----------------------------------------------------------------
    d0 = tempfile.mkdtemp()
    try:
        w0 = make_tree(d0)
        t0 = os.path.join(w0, "tools", "entrycheck.py")
        shutil.copy(SRC, t0)
        r0, out0 = run(t0, w0)
        ok0 = r0 == 0
        print(f"  {'ok  ' if ok0 else 'FAIL'}  B0  the UNMUTATED tool is green "
              f"through this temp root   rc={r0}")
        if not ok0:
            for ln in out0.splitlines()[-40:]:
                print("        | " + ln)
            print("REFUSING: every kill below would be free")
            return 1
    finally:
        shutil.rmtree(d0, ignore_errors=True)

    # --- A0 ----------------------------------------------------------------
    amb = [(row[0], src.count(row[1])) for row in rows if src.count(row[1]) != 1]
    print(f"  {'ok  ' if not amb else 'FAIL'}  A0  every anchor occurs exactly "
          f"once in entrycheck.py   {len(rows)} mutation(s)")
    for name, n in amb:
        print(f"          AMBIGUOUS-ANCHOR ({n}x): {name}")
    if amb:
        return 1
    print()

    def one(row):
        """-> (the line to print, the survivor entry or None)."""
        name, old, new = row
        d = tempfile.mkdtemp()
        try:
            work = make_tree(d)
            tgt = os.path.join(work, "tools", "entrycheck.py")
            with open(tgt, "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            try:
                compile(open(tgt, encoding="utf-8").read(), tgt, "exec")
            except SyntaxError as e:
                return (f"  FAIL  {name}   INVALID-MUTANT: {e}",
                        name + "  [INVALID-MUTANT]")
            rc, out = run(tgt, work)
            killed = rc != 0
            wrong = ""
            want = re.search(r"\(kills ([A-Z][0-9A-Za-z]*)\)", name)
            if killed and want:
                tag = want.group(1)
                if not re.search(r"^  FAIL  +" + tag + r"\b", out, re.M):
                    red = sorted(set(CASE.findall(out)))
                    killed = False
                    wrong = (f"  WRONG-CASE: wanted {tag} red, red were "
                             f"{red or 'none -- it did not reach the controls'}")
            line = (f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                    f"rc={rc} ({'killed' if killed else 'SURVIVED'}){wrong}")
            return line, (None if killed else name + wrong)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    with concurrent.futures.ThreadPoolExecutor(max(1, args.jobs)) as pool:
        results = list(pool.map(one, rows))
    survived = []
    for line, lost in results:
        print(line)
        if lost:
            survived.append(lost)

    print()
    if survived:
        print(f"{len(survived)} MUTATION(S) SURVIVED -- those controls do "
              f"not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(rows)} mutations killed, each turning the case it names red")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
