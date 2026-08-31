#!/usr/bin/env python3
"""test-replay-capture-mutants -- the mutation suite for tools/replay-capture.py.

Baseline first, every row names the control it must turn red, and an anchor that
does not occur exactly once is a SURVIVOR rather than a skip.  The reasons are
`tools/flashwin.py`'s invalid 8/8 pass and `tools/test-rbcheck.py`'s M25, which
survived five controls because none of them exercised the branch it changed.

The three rows that are not mutations:

  B0  the unmutated tool must pass IN THE TEMP TREE, not only at the real
      root.  This suite reported 14/14 to a tree where nothing could pass, on
      2026-08-31, because `tools/ci-expected.tsv` was not copied into it.

  A0  every anchor must occur exactly once.  Checked per row rather than up
      front here, and an ambiguous anchor is a SURVIVOR, never a skip.

  W0  🔴 ADDED 2026-08-31 (twentieth), and it was missing from the file whose
      own header names the defect it prevents.  Until today `rc != 0` alone
      counted as a kill -- so a mutation that crashed the tool before it
      reached its controls, or that turned some OTHER control red, was
      indistinguishable from one that broke the control it names.  A kill now
      requires the NAMED case to be red; anything else prints WRONG-CASE and
      is a survivor.
"""
import os
import re
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

    # --- M15..M19 -- the reel, added 2026-08-31 (twentieth) with R15..R18 ---
    ("M15 the reel total drops the pause term                (kills R16)",
     "    return segs, cap, pau, cap + pau",
     "    return segs, cap, pau, cap"),
    # M16 -- one row is still a reel to R15 and to R16 (both stay consistent
    # with what they read), and only the population control can see it.
    ("M16 read_reel stops after the first row                (kills R17)",
     "            rows.append((p[0], p[1], float(p[2]) if len(p) > 2 else 1.5))",
     "            rows.append((p[0], p[1], float(p[2]) if len(p) > 2 else 1.5))\n"
     "            break"),
    ("M17 the empty-reel refusal deleted                     (kills R17b)",
     '    if not rows:\n        raise Refuse(f"{tsv} has no segments")',
     '    if False:\n        raise Refuse(f"{tsv} has no segments")'),
    ("M18 the `must be under bench/` guard deleted           (kills R18)",
     '            if not p[0].startswith("bench/"):',
     "            if False:"),
    # M19 -- 🔴 the mutation R15b was written for.  A budget that skips a
    # segment it cannot open reports a shorter reel and a clean run, and every
    # other control here reads the REAL reel, in which nothing is missing.
    ("M19 a segment that cannot be opened is skipped         (kills R15b)",
     "        recs, blob = convert(os.path.join(ROOT, prefix))",
     "        try:\n"
     "            recs, blob = convert(os.path.join(ROOT, prefix))\n"
     "        except Refuse:\n"
     "            continue"),
]


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout


def main():
    base, _ = run(SRC, ROOT)
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
            # And `config/`, for the same reason: R15..R18 read
            # `config/r3-11-reel.tsv` through ROOT, which is this temp tree.
            shutil.copytree(os.path.join(ROOT, "config"),
                            os.path.join(work, "config"), symlinks=True)
            tgt = os.path.join(work, "tools/replay-capture.py")
            # B0-IN-TREE, see the paragraph above: the unmutated tool must pass
            # HERE, not only at the real root.
            shutil.copy(SRC, tgt)
            if run(tgt, work)[0] != 0:
                sys.exit(f"REFUSING at {name}: the UNMUTATED tool fails in the "
                         f"temp tree, so every kill would be invalid")
            n = src.count(old)
            if n != 1:
                survived.append(f"{name}  [anchor occurs {n} times]")
                print(f"  FAIL  {name}   ANCHOR x{n} (not applied)")
                continue
            open(tgt, "w", encoding="utf-8").write(src.replace(old, new, 1))
            rc, out = run(tgt, work)
            killed = rc != 0
            # 🔴 W0, added 2026-08-31 (twentieth).  Until today `rc != 0` alone
            # was a kill here -- which is exactly the shape this file's own
            # header calls out as `flashwin`'s invalid 8/8 pass, applied to
            # itself.  A mutation that makes the tool crash before it reaches
            # its controls exits non-zero too, and so does one that turns some
            # OTHER control red.  A kill counts only if the case the row NAMES
            # went red; anything else is reported WRONG-CASE, which is a
            # survivor with a different name.
            wrong = ""
            want = re.search(r"\(kills (R[0-9]+[a-z]?)\)", name)
            if killed and want and not equivalent:
                tag = want.group(1)
                if not re.search(r"^  FAIL  +" + tag + r"\b", out, re.M):
                    red = sorted(set(re.findall(r"^  FAIL  +(R[0-9]+[a-z]?)\b",
                                                out, re.M)))
                    killed = False
                    wrong = (f"  WRONG-CASE: wanted {tag} red, red were "
                             f"{red or 'none -- it did not reach the controls'}")
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
                  f"rc={rc} ({'killed' if killed else 'SURVIVED'}){wrong}")
            if not killed:
                survived.append(name + wrong)
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
