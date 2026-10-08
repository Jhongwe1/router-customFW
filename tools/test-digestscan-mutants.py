#!/usr/bin/env python3
"""test-digestscan-mutants -- the mutation suite for tools/digestscan.py.

WHY IT ARRIVES WITH THE TOOL, not after it
------------------------------------------
`tools/flashwin.py` and `tools/leakscan.py` are this repository's other two
guards on `H601`, and both were green on every control they had while their
first adversarial passes left mutants alive -- 24 of 45 for `flashwin`, three
of them printing this unit's MAC; eight of 23 for `leakscan`.  A leak guard
whose controls have not been shown to fail is the claim `CLAUDE.md` says a
green suite is: a claim about its controls.  So this suite ships in the same
commit as the tool.

WHAT IT COVERS, AND WHAT IT DOES NOT
------------------------------------
Every row mutates the tool and names the self-test case that must turn red:
the window enumeration and its forbidden-overlap filter, the constant filter,
`N`, the three chain rules (separators, `0x`, the `DW` address column), both
lookup directions, the occurrence key, every exemption rule (one row exempting
one hit among them), `check`'s `K2` proxy, the identity refusal, the
empty-population refusal, the exit code, the verdict's silence about what it
matched, and two candidate families (`dw:`, `mactext:`).

⚠️ **The R-block is not mutated here.**  `R1`-`R3` read this unit's 4 MiB
dump, which a runner does not have, and this suite runs the self-test with
`FWRE_WORK` pointed at an empty directory so its verdicts are the same on a
runner and at the desk.  The code the R-block exercises -- `load_dump`,
`complement_digest`, `identity_expected`, `match_text` -- is reached by the
synthetic `F` and `M` cases, which ARE mutated; the real-material assertions
themselves are not.

THE THREE ROWS THAT ARE NOT MUTATIONS, as `test-flashwin-mutants.py` has them
  B0  the unmutated tool must pass IN THE TEMP TREE, or every kill is free.
  A0  every anchor occurs exactly once in the tool.
  W0  a kill counts only if the case the row NAMES went red -- `rc != 0` alone
      is how five rows of `test-replay-capture-mutants.py` once counted as
      kills while turning nothing red.

The temp tree holds real directories and copies of the four files the
self-test reads (`flashwin.py`, which it imports; `ci-expected.tsv`, for
`Q1`; the driver source, for `M6b` and `F3`).

Run:  /usr/bin/python3 tools/test-digestscan-mutants.py [--jobs 8] [--only MN1,MN5]

`--jobs` runs mutants side by side, each in its own temp tree; the lines are
printed in row order whatever order they finish in.
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
SRC = os.path.join(ROOT, "tools", "digestscan.py")

FIXTURES = [
    "tools/flashwin.py",
    "tools/ci-expected.tsv",
    "config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c",
]

MUT = [
    # ---- what is a candidate -------------------------------------------
    ("MN1  N raised from 8 to 9                              (kills M3)",
     "MIN_HEX = 8\n",
     "MIN_HEX = 9\n"),
    ("MN2  the forbidden-overlap filter inverted             (kills W1)",
     "        if flashwin.overlaps_forbidden(at, n) is not None:\n"
     "            labs = labels[(at, n)]",
     "        if flashwin.overlaps_forbidden(at, n) is None:\n"
     "            labs = labels[(at, n)]"),
    ("MN3  the constant filter dropped                       (kills W2)",
     "MIN_DISTINCT_FORBIDDEN = 2\n",
     "MIN_DISTINCT_FORBIDDEN = 0\n"),
    ("MN4  the DW renderings are not candidates              (kills M10)",
     "            for kind, fn in TEXT_KINDS:\n"
     "                self.add(kind, fn(text), lab)",
     "            for kind, fn in ():\n"
     "                self.add(kind, fn(text), lab)"),
    ("MN5  the MAC's text forms are not candidates           (kills M11)",
     "                    for kind, fn in TEXT_KINDS:\n"
     '                        self.add(kind, fn((s + nl).encode("ascii")), lab)',
     "                    for kind, fn in ():\n"
     '                        self.add(kind, fn((s + nl).encode("ascii")), lab)'),

    # ---- the channel ----------------------------------------------------
    ("MN6  tokens never join a chain                         (kills M5)",
     r'''GAP = re.compile(r"[ \t\r\n\"',:+\\]*")''',
     r'''GAP = re.compile(r"(?!)")'''),
    ("MN7  the 0x prefix is not stripped                     (kills M6)",
     r'''TOKEN = re.compile(r"0[xX]([0-9A-Fa-f]{2,})|([0-9A-Fa-f]{2,})")''',
     r'''TOKEN = re.compile(r"(?!)x([0-9A-Fa-f]{2,})|([0-9A-Fa-f]{2,})")'''),
    ("MN8  the DW address column joins the stream            (kills M10b)",
     '        if ln == 8 and text.startswith(":", end):',
     "        if False:"),

    # ---- the match ------------------------------------------------------
    ("MN9  suffixes are never looked up                      (kills M7)",
     "            if b >= n:\n"
     "                for ci in cs.suf.get(s[b - n:b], ()):",
     "            if False:\n"
     "                for ci in cs.suf.get(s[b - n:b], ()):"),
    ("MN10 two occurrences in one chain collapse to one      (kills M12)",
     "                    key = (a, a + k, ci)",
     "                    key = (0, k, ci)"),

    # ---- exemptions -----------------------------------------------------
    ("MN11 an exemption ignores the line number              (kills E3)",
     "            if (ep == path and el == line and ekind == kind and elab in labels",
     "            if (ep == path and ekind == kind and elab in labels"),
    ("MN12 a stale exemption is never reported               (kills E2)",
     "        if used[i]:\n            continue",
     "        if True:\n            continue"),
    ("MN13 an exemption applies to any file of its name      (kills E5)",
     "        if mine is not None and mine == theirs:",
     "        if True:"),
    # The hole the 2026-10-08 rows opened: FLS-14's line holds one prefix
    # twice, and a row that took every hit of its name would let a third copy
    # through -- while its second row read STALE.
    ("MN18 one exemption row exempts every hit of its name   (kills E6)",
     "            if used[i]:\n"
     "                continue          # one row exempts one hit -- EXEMPTIONS",
     "            if False:\n"
     "                continue          # one row exempts one hit -- EXEMPTIONS"),
    ("MN19 K2's proxy ignores the digits a row names         (kills E7)",
     "            if lo <= off < hi and len(s) - a >= digits:",
     "            if lo <= off < hi:"),

    # ---- the command line -----------------------------------------------
    ("MN14 the dump's identity is not checked                (kills F3)",
     "    if complement_digest(dump) != want:",
     "    if False:"),
    ("MN15 a scan of zero files is not refused at once       (kills F6)",
     "    if not rels:\n        _fail(f\"the population is empty",
     "    if False:\n        _fail(f\"the population is empty"),
    ("MN16 a scan with findings exits 0                      (kills F4)",
     '            f"{len(stale)} stale exemption(s); {len(exempt)} exempt")\n'
     "        return 1",
     '            f"{len(stale)} stale exemption(s); {len(exempt)} exempt")\n'
     "        return 0"),
    # 🔴 THE ONE THAT MATTERS.  A verdict that prints the digest it found is
    # the failure this tool exists to prevent, and it looks like a more
    # helpful tool.
    ("MN17 the verdict PRINTS the matched digest             (kills F4)",
     '    return (f"{path}:{span}  {labels[0]}{more}  {kind}  "',
     '    return (f"{path}:{span} {d} {labels[0]}{more}  {kind}  "'),
    ("MQ1  the printed skip label drifts from the table      (kills Q1)",
     "SKIP_LABEL = \"R-block this unit's flash dump\"",
     "SKIP_LABEL = \"R-block this unit's flash dump (drifted)\""),
]


def make_tree(d):
    """Real directories, copies not links -- see the header."""
    work = os.path.join(d, "router-rebuild")
    os.makedirs(os.path.join(work, "tools"))
    for rel in FIXTURES:
        dst = os.path.join(work, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(ROOT, rel), dst)
    return work


def run(path, cwd, d):
    # FWRE_WORK at an empty directory: the R-block stands down the same way
    # on a runner and at the desk, so a kill means the same thing on both.
    env = dict(os.environ, FWRE_WORK=os.path.join(d, "no-fwre-work"))
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd, env=env)
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

    src = open(SRC, encoding="utf-8").read()

    # --- B0 ----------------------------------------------------------------
    d0 = tempfile.mkdtemp()
    try:
        w0 = make_tree(d0)
        t0 = os.path.join(w0, "tools", "digestscan.py")
        shutil.copy(SRC, t0)
        r0, out0 = run(t0, w0, d0)
        ok0 = r0 == 0
        print(f"  {'ok  ' if ok0 else 'FAIL'}  B0  the UNMUTATED tool is green "
              f"through this temp root   rc={r0}")
        if not ok0:
            print(out0[-2000:])
            print("🔴 REFUSING: every kill below would be free")
            return 1
    finally:
        shutil.rmtree(d0, ignore_errors=True)

    # --- A0 ----------------------------------------------------------------
    amb = [(row[0], src.count(row[1])) for row in rows if src.count(row[1]) != 1]
    print(f"  {'ok  ' if not amb else 'FAIL'}  A0  every anchor occurs exactly "
          f"once in digestscan.py   {len(rows)} mutation(s)")
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
            tgt = os.path.join(work, "tools", "digestscan.py")
            with open(tgt, "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            try:
                compile(open(tgt, encoding="utf-8").read(), tgt, "exec")
            except SyntaxError as e:
                return (f"  FAIL  {name}   INVALID-MUTANT: {e}",
                        name + "  [INVALID-MUTANT]")
            rc, out = run(tgt, work, d)
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
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls do "
              f"not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(rows)} mutations killed, each turning the case it names red")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
