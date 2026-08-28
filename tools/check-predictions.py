#!/usr/bin/env python3
"""Check that a predictions file was written BEFORE the captures it predicts.

Why this exists
---------------
``RUNSHEET.md`` house rule 2: *"Every cell carries its expected value, computed
before the visit.  A cell whose expectation is written afterwards illustrates;
it cannot refute."*  When the operator drove the session cell by cell, that rule
enforced itself -- the expectation was in a message that had already been sent.
From 2026-08-24 the console is driven directly, and a prediction written after
the reading is indistinguishable from one written before it.  This makes the
ordering checkable by anyone, afterwards, from the filesystem.

The instrument is the same one ``E2b`` used to measure the timer: a capture's
``.log`` mtime is the moment its last byte landed (verified 2026-08-24 --
``E1b``'s mtime is 117 ms after its ``started_wallclock``, exactly the round trip
for 71 bytes at 38400, and ``A-catch``'s is 25.2 s after, matching the last ESC
in its ``.timing``).

What it does NOT prove
----------------------
mtime is not a cryptographic timestamp.  ``touch -d`` rewrites it.

🔴 **And it does not survive git.**  Measured 2026-08-29, on two independent
``git clone --depth 1`` of this repository: a checkout writes every file fresh,
so the whole of ``bench/`` carries a handful of mtimes spanning tens of
milliseconds and **128 of 156 cells read as "capture is OLDER than the
prediction"**.  There is no ordering signal left in a clone at all.  That is not
a forgery scenario -- it is what clone, checkout, stash pop, rebase and merge do
routinely -- and it is why this tool is a **pre-push gate on the machine that
took the captures** and is not, and cannot be, a CI gate in this form.

The fix that would make it one is known and is not built here: every capture
already carries a committed ``started_wallclock`` in its ``.meta.json`` (量: all
136 resolvable cells have one), so the capture side is clone-stable.  The
prediction side has no committed timestamp, and adding one means a declared
``written:`` line inside the predictions file -- a change to the format that the
blocks already frozen cannot have.  Carried forward rather than half-done.

So: this proves ordering to a cooperative auditor **standing at the machine the
captures were taken on**; it proves nothing after a push, and nothing against
someone willing to forge an mtime.  Said here rather than left for a reader to
work out.

Consequence for use: **never edit a predictions file after its block has run.**
Even fixing a typo updates the mtime and the check fails -- which is the correct
behaviour and will look like a false alarm.  Corrections go in a new file.

Format
------
The predictions file is Markdown with one fenced block whose info string is
``cells``, holding one capture prefix per line (no extension, blank lines and
``#`` comments ignored)::

    ```cells
    bench/2026-08-24b/E12b
    bench/2026-08-24b/E12c
    ```

Modes
-----
``<file>``
    the per-file check.  Reports one line per named cell and exits 1 if any
    capture is missing or out of order.

``--self-test``
    the controls and nothing else.  Fifteen of them, and **eight must fail** --
    six of the fifteen drive this file as a subprocess and assert its exit
    code, because the exit code is the entire content of a gate and calling the
    functions directly cannot see it.

``--sweep <root>``
    every ``PREDICTIONS-*.md`` under ``root``, checked for **ordering only**.
    A predicted cell with no capture is REPORTED and is not a failure: a seating
    that stopped early is a fact about the seating.  What this catches is a
    capture that is OLDER than the prediction naming it.

    ⚠️ What ``--sweep`` cannot catch, each measured 2026-08-29: a **renamed**
    capture directory (every cell becomes "no capture"), a **typo'd** cell path
    (same), a run from the **wrong working directory** (cell paths resolve
    against the cwd, never against the predictions file), and **a capture
    nobody predicted** -- the sweep walks predictions to captures and never the
    other way.  The first three are why it refuses when nothing resolves; the
    fourth is unbuilt and carried forward.

Run:  python3 tools/check-predictions.py bench/<dir>/PREDICTIONS-<block>.md
      python3 tools/check-predictions.py --self-test
      python3 tools/check-predictions.py --sweep bench
"""

import glob
import os
import re
import subprocess
import sys
import tempfile
import time

FENCE = re.compile(r"^```cells\s*$")
ENDFENCE = re.compile(r"^```\s*$")


def parse_cells(path):
    """Return the capture prefixes named in the file's ``cells`` block."""
    cells, inside, seen_block = [], False, False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not inside and FENCE.match(line):
                inside, seen_block = True, True
                continue
            if inside:
                if ENDFENCE.match(line):
                    inside = False
                    continue
                s = line.strip()
                if s and not s.startswith("#"):
                    cells.append(s)
    return cells, seen_block


def check(path, quiet=False):
    """Return (violations, checked) or raise ValueError for an unusable file."""
    if not os.path.exists(path):
        raise ValueError(f"{path}: no such file")
    cells, seen_block = parse_cells(path)
    if not seen_block:
        raise ValueError(f"{path}: no ```cells block -- nothing to check")
    if not cells:
        # A tool that reports "0 violations" over 0 cells is making a claim it
        # cannot support.  CLAUDE.md: a tool reporting 0 needs a positive
        # control; here the honest answer is to refuse.
        raise ValueError(f"{path}: the ```cells block is empty -- refusing to "
                         "report a clean result over nothing")
    tp = os.path.getmtime(path)
    violations = []
    for cell in cells:
        log = cell + ".log"
        if not os.path.exists(log):
            violations.append((cell, None, "no capture -- a predicted cell that "
                                           "never ran is not a pass"))
            continue
        tc = os.path.getmtime(log)
        margin = tc - tp
        if margin <= 0:
            violations.append((cell, margin, "capture is OLDER than the "
                                             "prediction"))
        elif not quiet:
            print(f"  ok    {cell:44s} +{margin:9.3f} s after the prediction")
    for cell, margin, why in violations:
        if not quiet:
            m = "        " if margin is None else f"{margin:+9.3f} s"
            print(f"  FAIL  {cell:44s} {m}  {why}")
    return violations, cells


class Sweep:
    """The result of one ``--sweep``, with an arithmetic that partitions.

    ``cells == ordered + absent + out_of_order`` always, and ``unreadable`` is
    counted separately because a file whose block cannot be parsed contributes
    no cells at all.  The first version folded the two together and printed
    ``7 + 1 + 1`` over 8 cells, in a repository whose census tool exists to make
    arithmetic close.
    """

    def __init__(self):
        self.files = []
        self.cells = 0
        self.ordered = 0
        self.absent = 0
        self.out_of_order = []   # (path, cell)
        self.unreadable = []     # (path, why)

    @property
    def red(self):
        return bool(self.out_of_order) or bool(self.unreadable)


def sweep(root, quiet=False):
    """Ordering only, over every ``PREDICTIONS-*.md`` under *root*."""
    r = Sweep()
    r.files = sorted(glob.glob(os.path.join(root, "**", "PREDICTIONS-*.md"),
                               recursive=True))
    for path in r.files:
        try:
            cells, seen_block = parse_cells(path)
            tp = os.path.getmtime(path)
        except (OSError, UnicodeDecodeError) as e:
            # A predictions file this tool cannot read is a malformed record,
            # not an absent one.  UnicodeDecodeError is a ValueError, not an
            # OSError, and the first version let it out as a traceback.
            r.unreadable.append((path, f"{type(e).__name__}: {e}"))
            continue
        if not seen_block or not cells:
            r.unreadable.append((path, "no usable ```cells block"))
            continue
        for cell in cells:
            r.cells += 1
            log = cell + ".log"
            if not os.path.exists(log):
                r.absent += 1
                continue
            if os.path.getmtime(log) - tp <= 0:
                r.out_of_order.append((path, cell))
            else:
                r.ordered += 1
    if not quiet:
        for path, why in r.unreadable:
            print(f"  RED   {path}  {why}")
        for path, cell in r.out_of_order:
            print(f"  RED   {path} -> {cell}  capture is OLDER than the "
                  f"prediction")
    return r


# --------------------------------------------------------------------------
# Controls.  Fifteen, and EIGHT of them must fail, because a checker that
# cannot report a violation proves nothing about the file it is pointed at.
#
# Six drive this file as a subprocess.  That is not belt-and-braces: a mutation
# pass on 2026-08-29 built fifteen mutants of this tool and eight survived the
# six function-level controls, including one that made `cmd_sweep` return 0 on
# a real regression and one that deleted the empty-root refusal.  Neither is
# visible to a control that calls sweep() as a function, because the exit code
# is the entire content of a gate.  `test-hazlint`'s TC-j is the same lesson.
# --------------------------------------------------------------------------

LABELS = (
    "P1 prediction-before-capture passes",
    "N1 capture-before-prediction is caught",
    "N2 a predicted cell with no capture is caught",
    "N3 an empty cells block is refused, not reported clean",
    "P2 a stopped seating sweeps green with the absent cell reported",
    "N4 a capture older than its prediction is a sweep regression",
    "N5 a capture whose mtime EQUALS the prediction's is a regression",
    "N6 a malformed cells block is a sweep regression, not a skip",
    "N7 the guilty file is found when it is not the first one",
    "P3 a predictions file three directories down is seen",
    "A1 the summary arithmetic partitions: cells == ordered+absent+out",
    "X1 CLI: a clean tree exits 0",
    "X2 CLI: a regression exits 1",
    "X3 CLI: an empty root is REFUSED (exit 2), not reported green",
    "X4 CLI: a tree where nothing resolves is REFUSED, not reported green",
)


#: Set in the environment of every subprocess a control spawns.  Two jobs:
#: `--sweep` runs its controls first, and a control that spawns `--sweep` would
#: therefore spawn its own controls -- measured, on the first run: the process
#: tree grew without bound and the suite had to be killed at 120 s.  The flag
#: `--no-controls` is what breaks the recursion; this variable makes it
#: STRUCTURAL, because a control that forgot the flag would otherwise re-enter.
RECURSION_GUARD = "RLXFW_CHECKPRED_IN_CONTROL"


def _cli(*args):
    """Run this file as a subprocess.  Returns (rc, stdout+stderr)."""
    env = dict(os.environ)
    env[RECURSION_GUARD] = "1"
    p = subprocess.run([sys.executable, os.path.abspath(__file__)] + list(args),
                       capture_output=True, text=True, env=env, timeout=60)
    return p.returncode, p.stdout + p.stderr


def controls():
    """Run the controls.  Return (failures, labels_actually_run).

    Refuses outright inside a control's own subprocess: see RECURSION_GUARD.

    The second value is the point: ``run_controls`` prints one line per label
    that RAN, and refuses if the set does not match ``LABELS``.  Printing a
    constant tuple of six labels whenever nothing failed is how a suite reports
    six controls with none of them having executed -- measured on this very
    file, by deleting the N3 block and watching ``--self-test`` still print
    ``ok N3``.
    """
    if os.environ.get(RECURSION_GUARD):
        raise RuntimeError("controls() re-entered inside a control's own "
                           "subprocess -- pass --no-controls")
    bad, ran = [], []

    def ck(label, ok, why=""):
        ran.append(label)
        if not ok:
            bad.append(f"{label}{(' -- ' + why) if why else ''}")

    with tempfile.TemporaryDirectory() as d:
        def write(name, body):
            p = os.path.join(d, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body)
            return p

        def capture(name):
            p = os.path.join(d, name + ".log")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(b"stand-in\n")
            return p

        def block(path, *cells):
            return write(path, "```cells\n" + "\n".join(cells) + "\n```\n")

        # ---- the per-file check -------------------------------------------
        pred = block("P1.md", os.path.join(d, "p1"))
        time.sleep(0.02)
        capture("p1")
        v, _ = check(pred, quiet=True)
        ck(LABELS[0], not v, f"reported {len(v)} violations")

        capture("n1")
        time.sleep(0.02)
        pred = block("N1.md", os.path.join(d, "n1"))
        v, _ = check(pred, quiet=True)
        ck(LABELS[1], len(v) == 1, f"{len(v)} violations")

        pred = block("N2.md", os.path.join(d, "absent"))
        v, _ = check(pred, quiet=True)
        ck(LABELS[2], len(v) == 1, f"{len(v)} violations")

        pred = write("N3.md", "```cells\n```\n")
        try:
            check(pred, quiet=True)
            ck(LABELS[3], False, "an empty cells block reported a clean result")
        except ValueError:
            ck(LABELS[3], True)

        # ---- the sweep -----------------------------------------------------
        # P2: one cell ran, one never did.  Green, with the absent one counted.
        # This is bench/2026-08-25b's block3 exactly, which reports `1 of 3`.
        sw = os.path.join(d, "sb", "2026-01-01")
        os.makedirs(sw)
        block(os.path.join("sb", "2026-01-01", "PREDICTIONS-p2.md"),
              os.path.join(sw, "ran"), os.path.join(sw, "never"))
        time.sleep(0.02)
        capture(os.path.join("sb", "2026-01-01", "ran"))
        r = sweep(os.path.join(d, "sb"), quiet=True)
        ck(LABELS[4], not r.red and r.absent == 1 and r.ordered == 1
           and r.cells == 2 and len(r.files) == 1,
           f"red={r.red} absent={r.absent} ordered={r.ordered} cells={r.cells}")

        # A1 rides on the same reading: the three buckets must partition.
        ck(LABELS[10], r.cells == r.ordered + r.absent + len(r.out_of_order),
           f"{r.cells} != {r.ordered}+{r.absent}+{len(r.out_of_order)}")

        # N4: a capture older than the prediction naming it.
        capture(os.path.join("sb", "2026-01-01", "never"))
        time.sleep(0.02)
        n4 = block(os.path.join("sb", "2026-01-01", "PREDICTIONS-n4.md"),
                   os.path.join(sw, "never"))
        r = sweep(os.path.join(d, "sb"), quiet=True)
        ck(LABELS[5], len(r.out_of_order) == 1,
           f"{len(r.out_of_order)} regressions")
        os.remove(n4)

        # N5: margin EXACTLY zero.  The boundary the `<= 0` test turns on, and
        # it is the one a git checkout lands on -- 83 of 136 cells in a fresh
        # clone had a margin of exactly 0.0.
        eq = os.path.join(d, "sb", "2026-01-02")
        os.makedirs(eq)
        p_eq = block(os.path.join("sb", "2026-01-02", "PREDICTIONS-n5.md"),
                     os.path.join(eq, "same"))
        c_eq = capture(os.path.join("sb", "2026-01-02", "same"))
        stamp = 1_700_000_000
        os.utime(p_eq, (stamp, stamp))
        os.utime(c_eq, (stamp, stamp))
        r = sweep(os.path.join(d, "sb", "2026-01-02"), quiet=True)
        ck(LABELS[6], len(r.out_of_order) == 1,
           f"{len(r.out_of_order)} regressions at margin 0")

        # N6: a malformed block must be a regression, not a silent skip.
        bad_dir = os.path.join(d, "sb2", "2026-01-03")
        os.makedirs(bad_dir)
        write(os.path.join("sb2", "2026-01-03", "PREDICTIONS-bad.md"),
              "no fence at all\n")
        r = sweep(os.path.join(d, "sb2"), quiet=True)
        ck(LABELS[7], len(r.unreadable) == 1 and r.red,
           f"unreadable={len(r.unreadable)} red={r.red}")

        # N7: the guilty file must be found when it is NOT the first.  A mutant
        # that swept only files[:1] survived every earlier control, because the
        # fixture happened to sort the guilty file first.
        two = os.path.join(d, "sb3", "2026-01-04")
        os.makedirs(two)
        block(os.path.join("sb3", "2026-01-04", "PREDICTIONS-aaa.md"),
              os.path.join(two, "good"))
        time.sleep(0.02)
        capture(os.path.join("sb3", "2026-01-04", "good"))
        capture(os.path.join("sb3", "2026-01-04", "stale"))
        time.sleep(0.02)
        block(os.path.join("sb3", "2026-01-04", "PREDICTIONS-zzz.md"),
              os.path.join(two, "stale"))
        r = sweep(os.path.join(d, "sb3"), quiet=True)
        ck(LABELS[8], len(r.out_of_order) == 1 and len(r.files) == 2
           and r.out_of_order[0][0].endswith("zzz.md"),
           f"files={len(r.files)} regressions={len(r.out_of_order)}")

        # P3: recursion.  `**` with recursive=False silently sees one level,
        # and every real file in bench/ sits at exactly the depth the controls
        # used, so nothing would have noticed.
        deep = os.path.join(d, "sb4", "a", "b", "c")
        os.makedirs(deep)
        block(os.path.join("sb4", "a", "b", "c", "PREDICTIONS-deep.md"),
              os.path.join(deep, "cell"))
        time.sleep(0.02)
        capture(os.path.join("sb4", "a", "b", "c", "cell"))
        r = sweep(os.path.join(d, "sb4"), quiet=True)
        ck(LABELS[9], len(r.files) == 1 and r.ordered == 1,
           f"files={len(r.files)} ordered={r.ordered}")

        # ---- the exit contract, as a subprocess ----------------------------
        # `--no-controls` because `--sweep` runs its controls first and this IS
        # a control.  What is under test is `sweep_report`, which both paths
        # share, so a mutant in the exit contract dies here either way.
        rc, _ = _cli("--sweep", "--no-controls", os.path.join(d, "sb4"))
        ck(LABELS[11], rc == 0, f"exit {rc}")

        rc, _ = _cli("--sweep", "--no-controls", os.path.join(d, "sb3"))
        ck(LABELS[12], rc == 1, f"exit {rc}")

        # X3 and X4 both end in exit 2, so each asserts its OWN message.  A
        # mutation pass caught that: with only the exit code checked, deleting
        # the empty-root refusal left X3 green, because the nothing-resolves
        # refusal one line below also fires on an empty root.
        empty = os.path.join(d, "sb5")
        os.makedirs(empty)
        rc, out = _cli("--sweep", "--no-controls", empty)
        ck(LABELS[13], rc == 2 and "no PREDICTIONS-*.md" in out,
           f"exit {rc}, message {out.strip().splitlines()[-1:]}")

        # X4: files exist, and not one cell resolves.  This is a renamed
        # capture directory, a typo'd path, and the wrong working directory --
        # all three arrive here, and all three used to be reported green.
        none = os.path.join(d, "sb6", "2026-01-05")
        os.makedirs(none)
        block(os.path.join("sb6", "2026-01-05", "PREDICTIONS-none.md"),
              os.path.join(none, "nothing-here"))
        rc, out = _cli("--sweep", "--no-controls", os.path.join(d, "sb6"))
        ck(LABELS[14], rc == 2 and "NOT ONE cell resolved" in out,
           f"exit {rc}, message {out.strip().splitlines()[-1:]}")

    return bad, ran


def run_controls():
    """Print the controls.  Non-zero if any misbehaved OR any did not run."""
    print("check-predictions controls")
    bad, ran = controls()
    for b in bad:
        print(f"  FAIL  {b}")
    missing = [l for l in LABELS if l not in ran]
    for m in missing:
        print(f"  FAIL  {m} -- DID NOT RUN")
    for label in LABELS:
        if label in ran and not any(b.startswith(label) for b in bad):
            print(f"  ok    {label}")
    return 2 if (bad or missing) else 0


def cmd_sweep(root, with_controls=True):
    if with_controls:
        rc = run_controls()
        if rc:
            print("\n  controls failed -- refusing to report on the tree")
            return rc
        print()
    print(f"check-predictions --sweep {root}")
    r = sweep(root)
    if not r.files:
        print(f"  refused -- no PREDICTIONS-*.md under {root}, so a green "
              f"result would mean nothing")
        return 2
    if r.ordered == 0 and not r.red:
        print(f"  refused -- {len(r.files)} prediction file(s) and NOT ONE cell "
              f"resolved to a capture. That is a renamed directory, a typo'd "
              f"path or the wrong working directory, and all three used to "
              f"read as green")
        return 2
    print(f"  {len(r.files)} prediction file(s), {r.cells} cell(s): "
          f"{r.ordered} ordered, {r.absent} with no capture yet, "
          f"{len(r.out_of_order)} OUT OF ORDER"
          + (f", {len(r.unreadable)} unreadable" if r.unreadable else ""))
    if r.absent and not r.red:
        print("  a cell with no capture is a seating that stopped, not a "
              "violation -- run the per-file check to see which")
    return 1 if r.red else 0


def main(argv):
    # argv is sys.argv, so argv[0] is this script.
    if len(argv) > 1 and argv[1] == "--self-test":
        return run_controls()
    if len(argv) > 1 and argv[1] == "--sweep":
        rest = argv[2:]
        # `--no-controls` exists for the controls themselves, which spawn this
        # file and would otherwise spawn their own controls.  A human should
        # never pass it: a gate that has not shown it can fail is not a gate.
        with_controls = "--no-controls" not in rest
        rest = [a for a in rest if a != "--no-controls"]
        return cmd_sweep(rest[0] if rest else "bench", with_controls)
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    rc = run_controls()
    if rc:
        print("\n  controls failed -- refusing to report on the file")
        return rc
    print()
    print(f"check-predictions {argv[1]}")
    try:
        violations, cells = check(argv[1])
    except ValueError as e:
        print(f"  {e}", file=sys.stderr)
        return 2
    print()
    print(f"  {len(cells) - len(violations)} of {len(cells)} captures came "
          f"after the prediction, {len(violations)} did not")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
