#!/usr/bin/env python3
"""test-flashwin-mutants -- the mutation suite for tools/flashwin.py.

WHY THIS ARRIVES LAST OF ALL OF THEM
------------------------------------
🔴 `flashwin.py` is the tool three other files in `tools/` cite as the reason
their own mutation suite has a baseline case.  量 2026-08-30: an adversarial
pass over it reported **8 of 8 killed** and **every kill was invalid** -- the
harness symlinked the repository root, `_inside_repo` resolves with
`realpath`, and the UNMUTATED file was already 22/24 through that harness.  A
second pass with 45 mutants left **24 alive**, three of which printed this
unit's MAC.  Both passes were run in a scratch directory and neither was
committed, so the file that taught this repository what an invalid kill looks
like is the one with no suite of its own.

WHAT THIS COVERS AND WHAT IT DOES NOT, stated rather than implied
-----------------------------------------------------------------
`MS1`..`MS12` mutate **`scan`**, which is new on 2026-08-31 and is the reason
this file exists now.  `MQ1` is the skip-label control CI forced on 2026-08-31.
`MR1`..`MR5` mutate the highest-stakes parts of the
older half -- the publication guard in `render`, its two interval bounds, and
the ordering property in `normalise` -- and they are **five rows, not a
pass**.  ⚠️ **`render`'s
formatter, its argument handling and `normalise`'s parser are NOT covered
here.**  A suite that covers part of a file and does not say so reads as a
suite that covers the file.

The three rows that are not mutations
-------------------------------------
  B0  the unmutated tool must pass IN THE TEMP TREE.  Not only at the real
      root: the 2026-08-30 invalid pass is exactly the difference between the
      two, and it is why the temp tree below holds REAL directories rather
      than symlinks.

  A0  every anchor must occur exactly once.  `str.replace(old, new, 1)` takes
      the first match, so an anchor that has become ambiguous silently mutates
      somewhere else and still exits non-zero -- still reading as *killed*.

  W0  a kill is only valid if it turned the case the row NAMES red.  A
      mutation that crashes the tool before it reaches its controls exits
      non-zero too.  量 2026-08-31 in `test-replay-capture-mutants.py`, the
      same evening: FIVE of its fourteen rows were counted as kills on
      `rc != 0` alone and turned no case red at all.

THE TEMP TREE, and the one thing it may not do
-----------------------------------------------
`flashwin.py` computes the repository root from its own `__file__` and
`_inside_repo` resolves with `os.path.realpath`.  So `C7`/`C7b`/`C7c` -- the
cases that refuse to write a forbidden window inside the repository -- are
about THIS root, and a symlink farm sends `realpath` back to the real tree and
makes them fail on the unmutated file.  Every directory here is therefore
real, and only the three capture files the controls name are copied in.

Run:  /usr/bin/python3 tools/test-flashwin-mutants.py [--only MS1,MR2]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "flashwin.py")

#: The captures `flashwin`'s own controls name.  Copied rather than symlinked,
#: for the `realpath` reason in the header.
FIXTURES = [
    "bench/2026-08-24d/G8a-rd0.log",
    "bench/2026-08-24d/G8a-rd6.log",
    "bench/2026-08-31c/K-P3.log",
]

MUT = [
    # ---- scan: the probe set --------------------------------------------
    ("MS1  the entropy filter dropped                       (kills S4)",
     "            if (len(w) == SCAN_WINDOW and len(set(w)) >= SCAN_MIN_DISTINCT\n"
     "                    and w not in seen):",
     "            if (len(w) == SCAN_WINDOW and len(set(w)) >= 0\n"
     "                    and w not in seen):"),
    ("MS2  the empty-probe-set refusal deleted              (kills S6)",
     "    if not probes:\n        _fail(",
     "    if False:\n        _fail("),
    # MS3 -- the probe set becomes ALIGNED again, which is the scheme this
    # tool started with.  S2 buries the window at capture offset 64 and takes
    # it from flash 0x110, so an aligned-only probe set still contains it;
    # what it loses is every offset in between, and S5b's xxd fixture starts
    # at 0x100.  The case that sees it is S1, which counts.
    ("MS3  the probe set goes back to ALIGNED windows       (kills S1)",
     "        for at in range(lo, hi - SCAN_WINDOW + 1):",
     "        for at in range(lo, hi - SCAN_WINDOW + 1, SCAN_WINDOW):"),

    # ---- scan: the matcher ----------------------------------------------
    ("MS4  the matcher never finds anything                 (kills S2)",
     "            i = data.find(needle, start)",
     "            i = -1"),
    ("MS5  only the FIRST occurrence of a needle is taken   (kills S2b)",
     "            start = i + 1",
     "            break"),
    ("MS6  the RAW channel dropped                          (kills S2)",
     '    for channel, data in (("raw", blob), ("hex", hex_stream(blob))):',
     '    for channel, data in (("hex", hex_stream(blob)),):'),
    ("MS7  the HEX channel dropped                          (kills S5)",
     '    for channel, data in (("hex", hex_stream(blob)),):',
     '    for channel, data in (("raw", blob),):',
     "chain"),

    # ---- scan: the hex stream -------------------------------------------
    ("MS8  the DW address column is NOT dropped             (kills S5)",
     '        if end < len(text) and text[end:end + 1] == b":":\n'
     "            continue",
     '        if False:\n            continue'),
    ("MS9  only eight-digit hex tokens are decoded          (kills S5b)",
     "        if len(tok) < 4 or len(tok) % 2:",
     "        if len(tok) != 8:"),

    # ---- scan: the verdict ----------------------------------------------
    ("MS10 a file with hits exits 0                         (kills S7)",
     '        print(f"  \\033[31m{nhit} HIT(S)\\033[0m -- a committed file holds "\n'
     '              f"content from a region that may not be published")\n'
     "        return 1",
     '        print(f"  \\033[31m{nhit} HIT(S)\\033[0m -- a committed file holds "\n'
     '              f"content from a region that may not be published")\n'
     "        return 0"),
    # MS11 -- 🔴 THE ONE THAT MATTERS.  A verdict that prints the bytes it
    # found is the failure this whole subcommand exists to avoid, and it looks
    # like a more helpful tool.
    ("MS11 the verdict PRINTS the matched bytes             (kills S7)",
     '            print(f"  \\033[31mHIT\\033[0m   {p}  {channel} channel, "',
     '            print("  " + blob[off:off + n].hex())\n'
     '            print(f"  \\033[31mHIT\\033[0m   {p}  {channel} channel, "'),
    ("MS12 the sweep's empty-population refusal deleted     (kills S8)",
     "        if not paths:\n            _fail(",
     "        if False:\n            _fail("),

    # ---- the skip label, and CI is why this row exists -------------------
    # 🔴 CI run 33410057391 went red on UNEXPECTED-SKIP while this suite
    # was 40/40 green on the bench, because the table's allowed-skip column
    # and the tool's printed label had drifted apart. Q1 is the fix; MQ1 is
    # what says Q1 works. ⚠️ A mutation can only express the drift in one
    # direction -- the TOOL moving -- and the direction that actually
    # happened was the TABLE moving, which no mutation of this file can
    # reach. Q1 catches both because it compares them; MQ1 shows it does.
    ("MQ1  the printed skip label drifts from the table   (kills Q1)",
     'SKIP_LABEL = "this unit\'s flash dump"',
     'SKIP_LABEL = "this unit\'s flash dump (drifted)"'),

    # ---- render / normalise: five rows, not a pass ----------------------
    ("MR1  the publication guard deleted                    (kills C6)",
     "    hit = overlaps_forbidden(args.at, args.bytes)",
     "    hit = None"),
    ("MR2  _inside_repo always answers OUTSIDE              (kills C7)",
     "    return p == root or p.startswith(root + os.sep)",
     "    return False"),
    # ⚠️ MR3 IS LABELLED C10 AND NOT C9, AND W0 IS WHY.  Its first version
    # named C9; 量, C9 stays GREEN under it (C9's straddle and last-byte
    # probes both still answer, because they end well above `lo + 1`) and C10
    # -- the case written for exactly this off-by-one -- is the one that goes
    # red.  The label follows the measurement.  C9 gets MR5 instead, at the
    # other end of the interval, so it is not a case with no mutation.
    ("MR3  overlaps_forbidden is off by one at the low end  (kills C10)",
     "        if at < hi and end > lo:",
     "        if at < hi and end > lo + 1:"),
    ("MR5  overlaps_forbidden is CLOSED at the high end     (kills C9)",
     "        if at < hi and end > lo:",
     "        if at <= hi and end > lo:",
     "exclusive"),
    ("MR4  normalise sorts the words                        (kills N8)",
     '        out.append(b"\\t".join(words))',
     '        out.append(b"\\t".join(sorted(words)))'),
]


def make_tree(d):
    """Real directories only -- see the header.  `flashwin` resolves the
    repository root with `realpath`, so a symlinked tree makes C7/C7b/C7c fail
    on the UNMUTATED file and every kill invalid."""
    work = os.path.join(d, "router-rebuild")
    os.makedirs(os.path.join(work, "tools"))
    # 🔴 `ci-expected.tsv` MUST be here: `Q1` reads it through the repository
    # root, which is this temp tree.  Leaving it out makes the UNMUTATED tool
    # red and every kill free -- B0 refused on exactly that while MQ1 was
    # being added, and `test-replay-capture-mutants.py` records the same
    # defect one tool over.
    shutil.copy(os.path.join(ROOT, "tools/ci-expected.tsv"),
                os.path.join(work, "tools/ci-expected.tsv"))
    for rel in FIXTURES:
        dst = os.path.join(work, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(ROOT, rel), dst)
    return work


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout


CASE = re.compile(r"^  FAIL  +([A-Z][0-9A-Za-z]*)\b", re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None,
                    help="comma-separated mutation ids")
    args = ap.parse_args()
    rows = MUT
    if args.only:
        want = {x.strip() for x in args.only.split(",")}
        rows = [r for r in MUT if r[0].split()[0] in want]
        missing = want - {r[0].split()[0] for r in MUT}
        if missing:
            sys.exit(f"no such mutation(s): {sorted(missing)}")

    src = open(SRC, encoding="utf-8").read()

    # --- B0, and the run stops here if it is not green -------------------
    d0 = tempfile.mkdtemp()
    try:
        w0 = make_tree(d0)
        t0 = os.path.join(w0, "tools/flashwin.py")
        shutil.copy(SRC, t0)
        r0, out0 = run(t0, w0)
        ok0 = r0 == 0
        print(f"  {'ok  ' if ok0 else 'FAIL'}  B0  the UNMUTATED tool is green "
              f"through this temp root   rc={r0}")
        if not ok0:
            print(out0[-2000:])
            print("🔴 REFUSING: every kill below would be free")
            return 1
    finally:
        shutil.rmtree(d0, ignore_errors=True)

    # --- A0 --------------------------------------------------------------
    # `chain` rows mutate the OUTPUT of an earlier row, so their anchor is
    # counted against that intermediate text rather than against the source.
    amb = []
    seen_anchor = set()
    for row in rows:
        old = row[1]
        if len(row) > 3 and row[3] == "chain":
            continue
        n = src.count(old)
        if n != 1:
            amb.append((row[0], n))
        # Two rows MAY share an anchor -- MR3 and MR5 mutate the same `if` in
        # opposite directions -- but only if they say so, because an anchor
        # repeated by accident is the class A0 exists for.
        if old in seen_anchor and not (len(row) > 3
                                       and row[3] == "exclusive"):
            amb.append((row[0] + "  [anchor shared, not declared]", 1))
        seen_anchor.add(old)
    print(f"  {'ok  ' if not amb else 'FAIL'}  A0  every anchor occurs exactly "
          f"once in flashwin.py   {len(rows)} mutation(s)")
    for name, n in amb:
        print(f"          AMBIGUOUS-ANCHOR ({n}x): {name}")
    if amb:
        print(f"🔴 {len(amb)} MUTATION(S) HAVE AN ANCHOR THAT IS NOT UNIQUE")
        return 1
    print()

    survived = []
    for row in rows:
        name, old, new = row[0], row[1], row[2]
        chained = len(row) > 3 and row[3] == "chain"
        d = tempfile.mkdtemp()
        try:
            work = make_tree(d)
            tgt = os.path.join(work, "tools/flashwin.py")
            base = src
            if chained:
                # MS7 removes the hex channel from a line MS6 already
                # rewrote; apply MS6 first so the anchor exists.
                base = src.replace(MUT[6 - 1][1], MUT[6 - 1][2], 1)
                if base.count(old) != 1:
                    print(f"  FAIL  {name}   CHAIN ANCHOR x{base.count(old)}")
                    survived.append(name + "  [chain anchor]")
                    continue
            with open(tgt, "w", encoding="utf-8") as f:
                f.write(base.replace(old, new, 1))
            try:
                compile(open(tgt, encoding="utf-8").read(), tgt, "exec")
            except SyntaxError as e:
                print(f"  FAIL  {name}   INVALID-MUTANT: {e}")
                survived.append(name + "  [INVALID-MUTANT]")
                continue
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
            print(f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                  f"rc={rc} ({'killed' if killed else 'SURVIVED'}){wrong}")
            if not killed:
                survived.append(name + wrong)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if survived:
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls do "
              f"not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(rows)} mutations killed, each turning the case it names red")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
