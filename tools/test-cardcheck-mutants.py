#!/usr/bin/env python3
"""test-cardcheck-mutants -- the mutation suite for tools/cardcheck.py.

Every mutation must make `--self-test` exit non-zero, and every row NAMES the
control it must turn red.  That naming is not decoration: `tools/flashwin.py`'s
first mutation pass reported 8/8 killed and **every kill was invalid**, because
the harness was red before any mutation was applied.

🔴 **So the FIRST case is the unmutated baseline through the same harness**, and
a mutation whose anchor is missing is reported as a SURVIVOR rather than skipped
-- a moved anchor and a mutation that changed nothing look identical from the
exit code, and only one of them is fine.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/cardcheck.py")

MUT = [
    ("M1  the NOT-IN-IMAGE verdict deleted                  (kills A2)",
     'issues.append(f"{base}: NOT IN IMAGE -- not among the "',
     'pass  # issues.append(f"{base}: NOT IN IMAGE -- not among the "'),

    ("M2  every name treated as invocable                   (kills A2)",
     "        if base in names:\n            continue",
     "        if True:\n            continue"),

    ("M3  the redirection target check deleted              (kills A9)",
     "    for t in redirect_targets(cmd):",
     "    for t in []:"),

    ("M4  only the FIRST word of a pipeline is checked      (kills A10)",
     "        if w in SEPARATORS:\n            expect_cmd = True",
     "        if w in SEPARATORS:\n            expect_cmd = False"),

    ("M5  a redirection TARGET is treated as a command      (kills B6)     ",
     '        if re.match(r"^\\d*[<>]{1,2}$", w):          # a free redirection\n'
     "            i += 2                                  # skip it AND its target",
     '        if re.match(r"^\\d*[<>]{1,2}$", w):          # a free redirection\n'
     "            i += 1"),

    ("M6  loader verbs looked up as shell names             (kills A7)",
     '    if first in LOADER_VERBS:\n        return "LOADER", []',
     '    if False:\n        return "LOADER", []'),

    ("M7  MDIOR removed from the verb list                  (kills B2)",
     '"PHYR", "PHYW", "MDIOR", "MDIOW",',
     '"PHYR", "PHYW", "MDIOW",'),

    ("M8  a card with no --send reports clean               (kills A12)",
     "    if not pairs:\n        raise Refuse(",
     "    if False:\n        raise Refuse("),

    ("M9  an empty declaration is accepted                  (kills A18)",
     "    if rows == 0:\n        raise Refuse(",
     "    if False:\n        raise Refuse("),

    ("M10 `nod` entries made invocable                      (kills B7)      ",
     '        if kind in ("slink", "file"):',
     '        if kind in ("slink", "file", "nod"):'),

    ("M11 the missing cardnum fence reports instead of refusing (kills A13)",
     "    if not m:\n        raise Refuse(",
     "    if not m and False:\n        raise Refuse("),

    ("M12 a number mismatch is not counted                  (kills A15)",
     "        if got.lower() != want.lower():",
     "        if False:"),

    ("M13 an unknown expression evaluates to the empty string (kills A17)",
     '    raise Refuse(f"unknown expression `{op}`")',
     '    return ""'),

    ("M14 dwreply returns the tuple, not the byte count     (kills A16)",
     "        if isinstance(got, tuple):\n            got = got[0]",
     "        if False:\n            got = got[0]"),

    ("M15 the absence declaration suppresses EVERYTHING     (kills B4)",
     '        keep = [i for i in issues if i.split(":")[0] not in absent]',
     "        keep = [] if absent else issues"),

    ("M16 the cell id is dropped from the report            (kills B5)",
     '        report(f"  FAIL  {cid}: {cmd}")',
     '        report(f"  FAIL  {cmd}")'),

    ("M17 zerorun-tail counts from the front                (kills A14)",
     "        while n < len(blob) and blob[len(blob) - 1 - n] == 0:",
     "        while n < len(blob) and blob[n] == 0:"),

    ("M18 word32 read little-endian                         (kills A14)",
     'return "%08X" % int.from_bytes(blob[off:off + 4], "big")',
     'return "%08X" % int.from_bytes(blob[off:off + 4], "little")'),
]


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode


def main():
    base = run(SRC, ROOT)
    if base != 0:
        sys.exit(f"REFUSING: the unmutated controls already fail (rc={base}). "
                 f"Every 'kill' below would be invalid -- this is the "
                 f"flashwin pass's own defect and it is not repeated.")
    print(f"baseline: unmutated --self-test rc={base}  (B0, and it is a case)\n")

    src = open(SRC, encoding="utf-8").read()
    survived = []
    for name, old, new in MUT:
        d = tempfile.mkdtemp()
        try:
            work = os.path.join(d, "router-rebuild")
            os.makedirs(os.path.join(work, "tools"))
            for rel in ("bench", "config"):
                shutil.copytree(os.path.join(ROOT, rel),
                                os.path.join(work, rel), symlinks=True)
            shutil.copy(os.path.join(ROOT, "tools/reply-size.py"),
                        os.path.join(work, "tools/reply-size.py"))
            shutil.copy(os.path.join(ROOT, "tools/ci-expected.tsv"),
                        os.path.join(work, "tools/ci-expected.tsv"))
            tgt = os.path.join(work, "tools/cardcheck.py")
            # 🔴 B0-IN-TREE.  The baseline above runs from the REAL root; this
            # runs the UNMUTATED tool from the temp tree, which is where every
            # mutation is judged.  A tree missing a file the tool reads makes
            # the whole run red before any mutation is applied, and a list of
            # kills looks identical either way.  量 2026-08-31: exactly that
            # happened to test-replay-capture-mutants, and the only thing that
            # caught it was a row required to SURVIVE.
            shutil.copy(SRC, tgt)
            if run(tgt, work) != 0:
                sys.exit(f"REFUSING at {name}: the UNMUTATED tool fails in the "
                         f"temp tree, so every kill would be invalid")
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
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls "
              f"do not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(MUT)} mutations killed")
    return 0


sys.exit(main())
