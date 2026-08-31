#!/usr/bin/env python3
"""test-mkinitramfs-mutants -- the mutation suite for tools/mkinitramfs.py.

Every mutation below must make `self-test` exit non-zero **and turn the case it
NAMES red**.  A mutation that survives is a control that does not work.

WHY THIS ARRIVES FIVE SESSIONS AFTER IT WAS FIRST OWED
------------------------------------------------------
🔴 It could not be written.  `mkinitramfs.py`'s twenty-six controls were all
about the DECLARATION -- `parse_decl`, `check_required`, `resolve`, `emit_spec`
-- and `cmd_verify`, the half `CLAUDE.md` names as *the only one that can catch
a mark that compiled and is not in the image*, had **none**.  Mutating it would
have produced twenty-six survivors and said nothing.  `V1`..`V8` are that half's
first controls (2026-09-01) and this file is what says they work.

The three rows that are not mutations, and each of them cost this repository a
session to learn:

  B0  THE UNMUTATED TOOL MUST PASS IN THE TEMP TREE.  A red baseline kills every
      mutation for free.  `test-replay-capture-mutants` reported 14/14 to
      exactly that on 2026-08-31.

  A0  EVERY ANCHOR MUST OCCUR EXACTLY ONCE.  `str.replace(old, new, 1)` takes
      the first match, so an anchor that becomes ambiguous silently starts
      mutating somewhere else and still exits non-zero -- still reading as
      *killed*.  量 2026-09-01 in `test-rbcheck.py`, the same day.

  W0  A KILL IS ONLY VALID IF IT TURNED THE NAMED CASE RED.  A mutation that
      makes the tool crash before it reaches its controls exits non-zero too.
      量 2026-09-01, again in `test-rbcheck.py`: two of its rows named a case
      that stayed GREEN, and the repair was the control rather than the label.

Run:  /usr/bin/python3 tools/test-mkinitramfs-mutants.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/mkinitramfs.py")

MUT = [
    # 🔴 M1 AND M2 MUTATE THE `append`, NOT THE `if`, AND THAT IS THE WHOLE
    # DIFFERENCE.  Their first form disabled the branch condition, which let
    # control fall through to `elif w != h:` with `h` still None -- a
    # TypeError, a traceback, and a non-zero exit that read as *killed* while
    # the report was never produced.  W0 caught it (`red were none -- it did
    # not reach the controls`).  A mutation that CRASHES the tool tests nothing
    # about the control; these two make the report SILENT instead, which is
    # the defect a reader would actually ship.
    ("M1  the MISSING report made silent                    (kills V2)",
     '            bad.append(("MISSING", path,\n'
     '                        "declared, and not in the image"))',
     "            pass"),
    ("M2  the UNEXPECTED report made silent                 (kills V3)",
     '            bad.append(("UNEXPECTED", path,\n'
     '                        "in the image, in no declaration row"))',
     "            pass"),
    ("M3  the mode comparison dropped                       (kills V4)",
     "            if w[1] != h[1]:", "            if False:"),
    ("M4  the dev comparison dropped                        (kills V5)",
     "            if (w[2], w[3]) != (h[2], h[3]):", "            if False:"),
    ("M5  every difference reported as no difference        (kills V2)",
     "    if not bad:", "    if True:"),
    ("M6  the built-spec drift refusal deleted              (kills V7)",
     "        if want != got:", "        if False:"),
    # M7 -- the archive walk stops at the first entry.  A verify that reads one
    # entry reports five MISSING and nothing else, so V2 (which needs exactly
    # one MISSING, named) is the case that can see it and V1 is not.
    ("M7  the cpio walk stops after the first entry         (kills V1)",
     "        out.append((name, mode, fsize, rmaj, rmin))",
     "        out.append((name, mode, fsize, rmaj, rmin))\n        return out"),
    # M8 -- the section lookup matches anything.  `.notramfs` would then be
    # read as the archive and V6's refusal never fires.
    ("M8  the section name is not compared at all           (kills V6)",
     "        if nm == want:", "        if True:"),
    # M9 -- the declared shape forgets the dev pair, so a nod in the image can
    # be anything.  This is the DECLARATION side of the same property A26 bans:
    # a ban on the row is worth nothing if the image is never compared to it.
    # ⚠️ M9 IS LABELLED V1 AND NOT V5, AND W0 IS WHY.  With the declared dev
    # forced to 0:0 the CLEAN fixture already disagrees with its own image, so
    # the positive control is the case that goes red first; V5 still sees a
    # difference and still passes.  The label follows the measurement.
    ("M9  declared_shape drops the dev numbers              (kills V1)",
     "            dev = (int(maj), int(mnr))", "            dev = (0, 0)"),
    # M10 -- the exit code, not the report.  Every case above reads stdout too,
    # so a mutation that reports correctly and returns 0 must still be caught.
    ("M10 the failing return code turned into a pass        (kills V2)",
     '    print("\\033[31mFAILED\\033[0m  %d difference(s) between %s and %s"',
     '    return 0\n    print("\\033[31mFAILED\\033[0m  %d difference(s) between %s and %s"'),
]


def make_tree(d):
    """A tree the controls can run in.  They build every fixture in a temp
    directory of their own, so the tool alone is enough -- but `ROOT` is
    computed from the file's path, so it has to sit under a `tools/`."""
    work = os.path.join(d, "router-rebuild")
    os.makedirs(os.path.join(work, "tools"))
    return work


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout


def main():
    rc0, _ = run(SRC, ROOT)
    if rc0 != 0:
        sys.exit(f"REFUSING: the unmutated suite already fails (rc={rc0})")
    print(f"baseline: unmutated self-test rc={rc0}")

    src = open(SRC, encoding="utf-8").read()
    survived = []

    d0 = tempfile.mkdtemp()
    try:
        w0 = make_tree(d0)
        t0 = os.path.join(w0, "tools/mkinitramfs.py")
        shutil.copy(SRC, t0)
        r0, out0 = run(t0, w0)
        ok0 = r0 == 0
        print(f"  {'ok  ' if ok0 else 'FAIL'}  B0  the UNMUTATED tool passes in "
              f"the temp tree   rc={r0}")
        if not ok0:
            print(out0[-1500:])
            print("🔴 REFUSING: every kill below would be free")
            return 1
    finally:
        shutil.rmtree(d0, ignore_errors=True)

    amb = [(name, src.count(old)) for name, old, _new in MUT
           if src.count(old) != 1]
    print(f"  {'ok  ' if not amb else 'FAIL'}  A0  every anchor occurs exactly "
          f"once in mkinitramfs.py   {len(MUT)} anchored mutation(s)")
    for name, n in amb:
        print(f"          AMBIGUOUS-ANCHOR ({n}x): {name}")
    print()
    if amb:
        print(f"🔴 {len(amb)} MUTATION(S) HAVE AN ANCHOR THAT IS NOT UNIQUE -- "
              f"they would mutate the first match, not the intended one")
        return 1

    for name, old, new in MUT:
        d = tempfile.mkdtemp()
        try:
            work = make_tree(d)
            tgt = os.path.join(work, "tools/mkinitramfs.py")
            open(tgt, "w", encoding="utf-8").write(src.replace(old, new, 1))
            r, out = run(tgt, work)
            killed = r != 0
            want = re.search(r"\(kills (V[0-9]+)\)", name)
            wrong = ""
            if killed and want:
                tag = want.group(1)
                if not re.search(r"^  FAIL  +" + tag + r"\b", out, re.M):
                    red = sorted(set(re.findall(r"^  FAIL  +(V[0-9]+)\b",
                                                out, re.M)))
                    killed = False
                    wrong = (f"  WRONG-CASE: wanted {tag} red, red were "
                             f"{red or 'none -- it did not reach the controls'}")
            # `  ok  ` / `  FAIL  ` is the shape tools/ci-census.py parses.
            print(f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                  f"rc={r} ({'killed' if killed else 'SURVIVED'}){wrong}")
            if not killed:
                survived.append(name + wrong)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if survived:
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls do not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(MUT)} mutations killed")
    return 0


sys.exit(main())
