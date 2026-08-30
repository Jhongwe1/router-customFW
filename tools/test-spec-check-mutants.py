#!/usr/bin/env python3
"""test-spec-check-mutants -- the mutation suite for `spec-check`'s C10.

Why this file exists
--------------------
`tools/spec-check.py` gained `C10` on 2026-08-30: a paragraph whose backtick
RUNS cannot pair, so a code span is left open and swallows the prose after it.
Three instances were in the repository when it was written, and one of them had
been committed for a day while `C8`, `C8b`, `C8c` and `C9` all passed over it --
`notes/kernel-build.md` rendered a whole sentence as code while `0x2B0000`, the
number the sentence is about, rendered as prose.

The same day, `tools/test-console-capture-mutants.py` found TEN live mutants
behind a suite that reported 40/40 green.  The lesson was not about that guard:
**a green control suite is a claim about the suite**, and the only way to hold
it is to mutate the thing the controls are about and require them to go red.

So this file exists before `C10` is trusted, not after it fails.

What a mutation proves, and what it does not
--------------------------------------------
Each row edits `tools/spec-check.py` at anchors that must occur EXACTLY ONCE,
then requires `spec-check.py --self-test` -- all fifteen table controls plus the
nine SPEC.md controls -- to go red against the result.  A row that survives
names a control that does not work.  It does NOT prove `C10` is correct; only
that the controls can tell this particular wrong checker from the right one.

An anchor that does not occur exactly once is reported as a **SURVIVOR**, never
skipped.  A mutation suite that silently applies nothing is the
"a tool reporting 0 is making a claim" failure this repository keeps catching.

Two phases, and the second exists because the first could not see half the tool
-------------------------------------------------------------------------------
🔴 An adversarial pass on 2026-08-30 found that `main()` runs `controls()` and
`table_controls()` and then **returns on `--self-test`, before `check_tables()`
is ever called** -- and `table_controls` calls the finding functions directly.
So a `--self-test` criterion **cannot reach `check_tables` or `report_tables` by
construction**: seven hand-written mutants survived all three CI gates, two of
them (`P1`, `P2` below) silently disabling `C10` over the whole repository while
every gate stayed green.

* **Phase 1** mutates `C10` and its helpers and requires `--self-test` to go red.
* **Phase 2** plants a real `C10` defect in a **tracked** file inside the temp
  root and runs the **full** `spec-check.py`, so the wiring is on the path. The
  planted file is under `bench/`, which is also what kills an exemption keyed on
  a path prefix rather than on the dict.

Phase 2 carries its own positive control: the **unmutated** tool against the
planted tree must be RED. Without it every phase-2 row would "kill" a run that
was already failing for some other reason.

How the mutant is run
---------------------
`spec-check.py` computes `ROOT` from its own path, so a mutant cannot simply be
run from `/tmp`.  Each mutant gets a temporary root holding a symlink to every
top-level entry of the real repository (including `.git`, so `git ls-files`
still answers, which `T7` requires) and a `tools/` directory holding symlinks to
every sibling tool plus the mutated `spec-check.py` as a real file.  量: a
clean copy through that harness exits 0 and a `C10`-never-fires mutant exits 2,
which is what says the harness itself is wired up.

Known limits, stated rather than left for a reader to find
----------------------------------------------------------
This suite mutates `C10` and its two helpers only.  `C1`-`C9` are covered by
`spec-check`'s own `M1`-`M9` and `T1`-`T10`, and nothing here re-runs those as
mutations.  A mutant that changes only a message's wording beyond the substring
each control greps for is not modelled.
"""
import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "tools", "spec-check.py")

# ---- anchors -------------------------------------------------------------
FIRE = "        if _runs_unpairable(text):"
PAIR_SCAN = "        while m < len(runs) and runs[m] != runs[k]:"
PARA_BLANK = "        if not ln.strip():"
PARA_MASK = "        if mask[i - 1]:"
PARA_TAIL = "    if cur:\n        yield start, '\\n'.join(cur)"
EXEMPT = "    exempt = honour_exempt and path in C10_EXEMPT"
FASTPATH = "        if '`' not in text:\n            continue"
NEVERCLOSE = "            return True\n        k = m + 1"
LINENO = "            out.append(('C10', f'{path}:{start}: a backtick run in this '"
LOOP = "    for start, text in paragraph_blocks(lines, mask):"

MUT = [
    # --- the check does not fire, or always fires ------------------------
    ("N1", "C10 never reports",
     [(FIRE, "        if False:")]),
    ("N2", "C10 reports on every paragraph",
     [(FIRE, "        if True:")]),
    ("N3", "the unpairable branch returns False instead of True",
     [(NEVERCLOSE, "            return False\n        k = m + 1")]),

    # --- run LENGTH vs backtick COUNT.  T14 is the control. --------------
    ("N4", "pair runs regardless of length, i.e. count parity",
     [(PAIR_SCAN, "        while m < len(runs) and False:")]),

    # --- the paragraph boundary.  T15 is the control. --------------------
    ("N5", "blank lines do not end a paragraph, so pairing is file-wide",
     [(PARA_BLANK, "        if False:")]),
    ("N6", "the final paragraph is never yielded",
     [(PARA_TAIL, "    if False:\n        yield start, '\\n'.join(cur)")]),
    ("N7", "only the last paragraph of a file is examined",
     [(LOOP, "    for start, text in list(paragraph_blocks(lines, mask))[-1:]:")]),

    # --- the fence mask --------------------------------------------------
    ("N8", "fenced blocks are scanned as prose",
     [(PARA_MASK, "        if False:")]),

    # --- the exemption ---------------------------------------------------
    ("N9", "every file is exempt, not only the listed one",
     [(EXEMPT, "    exempt = honour_exempt")]),
    ("N10", "honour_exempt is ignored, so T13 can never see past the exemption",
     [(EXEMPT, "    exempt = path in C10_EXEMPT")]),

    # --- the report ------------------------------------------------------
    ("N11", "the fast path skips every paragraph",
     [(FASTPATH, "        if True:\n            continue")]),
    ("N12", "the reported line number is off by one",
     [(LINENO, "            out.append(('C10', f'{path}:{start + 1}: a backtick run in this '")]),
]


# ---- phase 2: mutations the --self-test criterion cannot reach ----------
WIRE = "        pf, npara = paragraph_findings(rel, lines, m)"
REPORT = ("              'is only whitespace, and no paragraph leaving a span open')\n"
          "        return 0\n"
          "    for c, msg in sorted(findings):")
EXEMPT2 = "    exempt = honour_exempt and path in C10_EXEMPT"
ROWSKIP = "        if '`' not in text:"
RUNSCAN = "            runs.append(j - i)"

MUT2 = [
    ("P1", "check_tables never collects the C10 findings",
     [(WIRE, "        pf, npara = paragraph_findings(rel, lines, m)\n        pf = []")]),
    ("P2", "report_tables drops every C10 finding",
     [(REPORT, "              'is only whitespace, and no paragraph leaving a span open')\n"
               "        return 0\n"
               "    findings = [f for f in findings if f[0] != 'C10']\n"
               "    for c, msg in sorted(findings):")]),
    ("P3", "the exemption is keyed on a path prefix, not the dict",
     [(EXEMPT2, EXEMPT2 + "\n    exempt = honour_exempt and path.startswith('bench/')")]),
    ("P4", "a paragraph holding a table row is skipped",
     [(ROWSKIP, "        if text.lstrip().startswith('|'):\n            continue\n"
                "        if '`' not in text:")]),
    ("P5", "runs of three or more are not recorded at all",
     [(RUNSCAN, "            if j - i < 3:\n                runs.append(j - i)")]),
]


def apply_mutation(src, edits):
    """Exactly-once per anchor, or nothing."""
    for anchor, _repl in edits:
        n = src.count(anchor)
        if n != 1:
            return None, f"anchor occurs {n} time(s), not once: {anchor[:52]!r}"
    out = src
    for anchor, repl in edits:
        out = out.replace(anchor, repl, 1)
    if out == src:
        return None, "the edits cancelled: the file is unchanged"
    return out, None


# The tracked file phase 2 plants its defect in. It must be under bench/ so a
# path-prefix exemption is caught, and it must already be tracked or
# `git ls-files` -- which is what check_tables walks -- will not name it.
PLANT_PATH = "bench/README.md"
# Three runs of one: the first pairs with the second and the third can never
# close. A single unpaired run would also fire, but this shape is the one that
# actually shifts a pairing, which is what the message now says.
PLANT_TEXT = (
    # (a) prose, three runs: the first two pair and the pairing SHIFTS, which
    #     is the notes/kernel-build.md shape and the only one whose rendering
    #     really does swallow prose.
    "\n\nthe `0x2D0000 value, see `foo` below.\n"
    # (b) a TABLE ROW carrying the same shape. Without it P4 -- a mutant that
    #     skips any paragraph that is a table row -- cannot be exercised, and
    #     table rows are 624 of this tree's tick-carrying blocks.
    "\n| id | note |\n|---|---|\n| `A-99` | the `0x2B0000 value, see `bar` here |\n"
    # (c) a run of THREE that can never close, after two that pair. Runs
    #     [1,1,3] fire only if runs of three are counted at all, so this is
    #     what P5 needs; [3,...] would fire either way.
    "\nclosed `a` here and then ``` at the end.\n"
)


def make_root(mutated, planted=False):
    """A temp root whose ROOT resolves, holding the mutant as a real file.

    With `planted`, PLANT_PATH is materialised as a REAL file carrying a C10
    defect: every directory on its path becomes a real directory whose other
    entries are symlinks, so `git ls-files` still names it and check_tables
    reads the planted copy.
    """
    d = tempfile.mkdtemp(prefix="sc-mut-")
    os.mkdir(os.path.join(d, "tools"))
    parts = PLANT_PATH.split("/") if planted else []
    skip_top = {"tools"} | ({parts[0]} if parts else set())
    for e in os.listdir(ROOT):
        if e in skip_top:
            continue
        os.symlink(os.path.join(ROOT, e), os.path.join(d, e))
    for e in os.listdir(os.path.join(ROOT, "tools")):
        if e == "spec-check.py":
            continue
        os.symlink(os.path.join(ROOT, "tools", e), os.path.join(d, "tools", e))
    if planted:
        real, srcd = d, ROOT
        for i, p in enumerate(parts[:-1]):
            os.mkdir(os.path.join(real, p))
            for e in os.listdir(os.path.join(srcd, p)):
                if e == parts[i + 1]:
                    continue
                os.symlink(os.path.join(srcd, p, e), os.path.join(real, p, e))
            real, srcd = os.path.join(real, p), os.path.join(srcd, p)
        body = open(os.path.join(srcd, parts[-1]), encoding="utf-8").read()
        with open(os.path.join(real, parts[-1]), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(body + PLANT_TEXT)
    tgt = os.path.join(d, "tools", "spec-check.py")
    with open(tgt, "w", encoding="utf-8", newline="\n") as f:
        f.write(mutated)
    return d, tgt


def run_self_test(tool_path, cwd):
    return subprocess.run([sys.executable, tool_path, "--self-test"],
                          capture_output=True, text=True, cwd=cwd, timeout=300)


def run_full(tool_path, cwd):
    """The whole tool, so check_tables and report_tables are on the path."""
    return subprocess.run([sys.executable, tool_path],
                          capture_output=True, text=True, cwd=cwd, timeout=600)


def count_planted(stdout):
    """C10 findings naming the planted file. Counting rather than testing for
    presence is what makes suppressing ONE of three defects visible."""
    return sum(1 for ln in stdout.split("\n")
               if "C10" in ln and PLANT_PATH in ln)


def one2(row, src, want):
    """Phase 2: the mutant must report FEWER planted defects than the real tool."""
    mid, what, edits = row
    mutated, why = apply_mutation(src, edits)
    if mutated is None:
        return mid, what, False, f"[NOT APPLIED: {why}]"
    d = None
    try:
        d, tgt = make_root(mutated, planted=True)
        r = run_full(tgt, d)
        got = count_planted(r.stdout)
        killed = got < want
        note = (f"{got}/{want} planted defect(s) still reported -- SURVIVOR"
                if not killed else
                f"reports {got} of the {want} planted defects (rc={r.returncode})")
        return mid, what, killed, note
    except subprocess.TimeoutExpired:
        return mid, what, True, "by timeout"
    finally:
        if d:
            shutil.rmtree(d, ignore_errors=True)


def one(row, src):
    mid, what, edits = row
    mutated, why = apply_mutation(src, edits)
    if mutated is None:
        return mid, what, False, f"[NOT APPLIED: {why}]"
    d = None
    try:
        d, tgt = make_root(mutated)
        r = run_self_test(tgt, d)
        killed = r.returncode != 0
        red = sorted({ln.split()[1] for ln in r.stdout.split("\n")
                      if ln.startswith("  FAIL  ") and len(ln.split()) > 1})
        note = "by " + ",".join(red) if red else f"rc={r.returncode}, no FAIL line"
        return mid, what, killed, note
    except subprocess.TimeoutExpired:
        return mid, what, True, "by timeout"
    finally:
        if d:
            shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", default=None, help="comma-separated mutation ids")
    a = ap.parse_args()

    rows = MUT
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        rows = [r for r in MUT if r[0] in want]
        missing = want - {r[0] for r in rows}
        if missing:
            sys.exit(f"no such mutation id(s): {sorted(missing)}")

    src = open(SRC, encoding="utf-8").read()

    # The baseline.  Without it a self-test that is already red would "kill"
    # every mutation and this file would report a clean sweep over nothing.
    t0 = time.monotonic()
    d, tgt = make_root(src)
    try:
        base = run_self_test(tgt, d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if base.returncode != 0:
        print(base.stdout[-2000:])
        sys.exit("REFUSING: the unmutated self-test already fails "
                 f"(rc={base.returncode}) -- every mutation below would 'kill' "
                 "a suite that was already red")
    ncontrols = sum(1 for ln in base.stdout.split("\n") if ln.startswith("  ok    "))
    print(f"baseline: the unmutated self-test is green through the temp-root "
          f"harness, {ncontrols} control(s), {time.monotonic() - t0:.0f}s")
    print(f"{len(rows)} mutation(s), {a.jobs} at a time\n")

    # Phase 2's own positive control: the UNMUTATED tool against the planted
    # tree must be RED and must name the planted file. Without it, a phase-2
    # row would "kill" on a run that never saw the defect at all.
    d2, t2 = make_root(src, planted=True)
    try:
        base2 = run_full(t2, d2)
    finally:
        shutil.rmtree(d2, ignore_errors=True)
    want = count_planted(base2.stdout)
    if want < 3:
        print(base2.stdout[-2500:])
        sys.exit(f"REFUSING: the unmutated tool reports {want} of the 3 planted "
                 f"C10 defects, so a phase-2 row could 'kill' a run that never "
                 f"saw the defect its mutation is about")
    print(f"phase-2 control: the unmutated tool reports all {want} planted "
          f"defects in {PLANT_PATH} (rc={base2.returncode})\n")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for mid, what, killed, note in ex.map(lambda r: one(r, src), rows):
            results[mid] = (what, killed, note)

    rows2 = MUT2 if not a.only else [r for r in MUT2 if r[0] in
                                     {s.strip() for s in a.only.split(",")}]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for mid, what, killed, note in ex.map(lambda r: one2(r, src, want), rows2):
            results[mid] = (what, killed, note)

    killed = 0
    print("  -- phase 1: --self-test must go red --")
    for mid, _what, _e in rows:
        what, k, note = results[mid]
        if k:
            print(f"  ok      {mid:4s} killed   {what:58s} {note}")
            killed += 1
        else:
            print(f"  FAIL    {mid:4s} SURVIVED {what:58s} {note}")
    print()
    print("  -- phase 2: the full run must stop reporting a real planted defect --")
    for mid, _what, _e in rows2:
        what, k, note = results[mid]
        if k:
            print(f"  ok      {mid:4s} killed   {what:58s} {note}")
            killed += 1
        else:
            print(f"  FAIL    {mid:4s} SURVIVED {what:58s} {note}")
    print()
    rows = rows + rows2
    n = len(rows)
    if killed == n:
        print(f"  ok    {killed}/{n} mutants killed: the C10 controls can tell "
              f"each of these wrong checkers from the right one")
        return 0
    print(f"  FAIL  {killed}/{n} killed, {n - killed} SURVIVED -- each survivor "
          f"names a control that does not work")
    return 1


if __name__ == "__main__":
    sys.exit(main())
