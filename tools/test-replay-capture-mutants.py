#!/usr/bin/env python3
"""test-replay-capture-mutants -- the mutation suite for tools/replay-capture.py.

Baseline first, every row names the control it must turn red, and an anchor that
does not occur exactly once is a SURVIVOR rather than a skip.  The reasons are
`tools/flashwin.py`'s invalid 8/8 pass and `tools/test-rbcheck.py`'s M25, which
survived five controls because none of them exercised the branch it changed.
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/replay-capture.py")

MUT = [
    ("M1  count taken from THIS record instead of the next  (kills R1)",
     "        nxt = offs[i + 1] if i + 1 < len(tim) else len(blob)\n"
     "        recs.append((t - prev_t, nxt - off))",
     "        nxt = offs[i + 1] if i + 1 < len(tim) else len(blob)\n"
     "        recs.append((t - prev_t, off))"),

    ("M2  the last record's tail dropped                    (kills R1)",
     "        nxt = offs[i + 1] if i + 1 < len(tim) else len(blob)",
     "        nxt = offs[i + 1] if i + 1 < len(tim) else off"),

    ("M3  delay is the absolute timestamp, not a difference (kills R3)",
     "        recs.append((t - prev_t, nxt - off))",
     "        recs.append((t, nxt - off))"),

    # 🔴 DECLARED EQUIVALENT, with a proof, not a survivor.  Given offs[0]==0,
    # offsets non-decreasing and offs[-1] <= len(blob) -- all checked before it
    # -- the per-record counts telescope to exactly len(blob), so NO .timing
    # file can make this refusal fire.  It survived all sixteen controls on its
    # first run, and the honest reading is that it is an invariant assertion
    # rather than a guard.  An EQUIVALENT row must still be applied and run:
    # the suite requires it to survive, so a future edit that makes the check
    # reachable turns this row red in the other direction.
    ("M4  the byte-count reconciliation deleted        (EQUIVALENT, proved)",
     "    if total != len(blob):",
     "    if False:", "equivalent"),

    ("M5  backwards time accepted                           (kills R6)",
     "        if tim[i][1] < tim[i - 1][1]:",
     "        if False:"),

    ("M6  backwards offsets accepted                        (kills R7)",
     "        if offs[i] < offs[i - 1]:",
     "        if False:"),

    ("M7  an offset past the end of the .log accepted       (kills R5)",
     "    if offs[-1] > len(blob):",
     "    if False:"),

    ("M8  a first offset that is not 0 accepted             (kills R9)",
     "    if offs[0] != 0:",
     "    if False:"),

    ("M9  an empty .timing accepted                         (kills R8)",
     "    if not out:\n        raise Refuse(",
     "    if False:\n        raise Refuse("),

    ("M10 a missing sidecar accepted                        (kills R11)",
     "        if not os.path.exists(p):",
     "        if False:"),

    ("M11 the typescript header dropped                     (kills R12)",
     "        f.write(TYPESCRIPT_HEADER)\n        f.write(blob)",
     "        f.write(blob)"),

    ("M12 the header made two lines                         (kills R12)",
     'b"tools/replay-capture.py\\n")',
     'b"tools/replay-capture.py\\n\\nsecond line\\n")'),

    ("M13 comment lines in .timing parsed as records        (kills R8)",
     '            if not line or line.startswith("#"):',
     "            if not line:"),

    ("M14 a malformed field count accepted                  (kills R10)",
     "            if len(parts) != 2:",
     "            if False:"),
]


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode


def main():
    base = run(SRC, ROOT)
    if base != 0:
        sys.exit(f"REFUSING: the unmutated controls already fail (rc={base}); "
                 f"every kill below would be invalid")
    print(f"baseline: unmutated --self-test rc={base}  (and it is a case)\n")

    src = open(SRC, encoding="utf-8").read()
    survived = []
    for row in MUT:
        name, old, new = row[0], row[1], row[2]
        equivalent = len(row) > 3 and row[3] == "equivalent"
        d = tempfile.mkdtemp()
        try:
            work = os.path.join(d, "router-rebuild")
            os.makedirs(os.path.join(work, "tools"))
            shutil.copytree(os.path.join(ROOT, "bench"),
                            os.path.join(work, "bench"), symlinks=True)
            # 🔴 `ci-expected.tsv` MUST be in the temp tree, and leaving it out
            # was a harness defect that made every kill invalid -- `R14` reads
            # it, so without it R14 failed under every mutation and the suite
            # reported 14/14 killed on a tree where nothing could pass.
            # 量 2026-08-31: the ONLY thing that caught it was M4, the row
            # required to SURVIVE.  An always-red harness and a working one are
            # indistinguishable from a list of kills; they are not
            # indistinguishable once something has to live.  That is the second
            # reason the EQUIVALENT category exists, and it was not the reason
            # it was written.
            shutil.copy(os.path.join(ROOT, "tools/ci-expected.tsv"),
                        os.path.join(work, "tools/ci-expected.tsv"))
            tgt = os.path.join(work, "tools/replay-capture.py")
            # B0-IN-TREE, see the paragraph above: the unmutated tool must pass
            # HERE, not only at the real root.
            shutil.copy(SRC, tgt)
            if run(tgt, work) != 0:
                sys.exit(f"REFUSING at {name}: the UNMUTATED tool fails in the "
                         f"temp tree, so every kill would be invalid")
            n = src.count(old)
            if n != 1:
                survived.append(f"{name}  [anchor occurs {n} times]")
                print(f"  FAIL  {name}   ANCHOR x{n} (not applied)")
                continue
            open(tgt, "w", encoding="utf-8").write(src.replace(old, new, 1))
            rc = run(tgt, work)
            killed = rc != 0
            if equivalent:
                # An equivalent mutant must SURVIVE.  If it starts being killed
                # the proof above has stopped holding, and that is a finding.
                good = not killed
                print(f"  {'ok  ' if good else 'FAIL'}  {name}   "
                      f"rc={rc} ({'survived, as proved' if good else
                                  'KILLED -- the equivalence proof is stale'})")
                if not good:
                    survived.append(name + "  [equivalence proof is stale]")
                continue
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
    eq = sum(1 for r in MUT if len(r) > 3 and r[3] == "equivalent")
    print(f"all {len(MUT) - eq} mutations killed"
          + (f", {eq} declared EQUIVALENT and survived as proved" if eq else ""))
    return 0


sys.exit(main())
