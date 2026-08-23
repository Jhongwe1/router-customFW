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
mtime is not a cryptographic timestamp.  ``touch -d`` rewrites it.  This proves
ordering to a cooperative auditor and to future-me; it proves nothing against
someone willing to forge it.  Said here rather than left for a reader to work
out.

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

Run:  python3 tools/check-predictions.py bench/<dir>/PREDICTIONS-<block>.md
"""

import os
import re
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


# --------------------------------------------------------------------------
# Controls.  Four, and three of them must FAIL, because a checker that cannot
# report a violation proves nothing about the file it is pointed at.
# --------------------------------------------------------------------------

def controls():
    """Run the four controls.  Return a list of failures (empty == all good)."""
    bad = []
    with tempfile.TemporaryDirectory() as d:
        def write(name, body):
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body)
            return p

        def capture(name):
            p = os.path.join(d, name + ".log")
            with open(p, "wb") as fh:
                fh.write(b"stand-in\n")
            return p

        # P1 -- prediction first, capture second: must pass.
        pred = write("P1.md", "```cells\n" + os.path.join(d, "p1") + "\n```\n")
        time.sleep(0.02)
        capture("p1")
        v, c = check(pred, quiet=True)
        if v:
            bad.append(f"P1 a prediction written before its capture was reported "
                       f"as a violation ({v})")

        # N1 -- capture first, prediction second: must be caught.  This is the
        # whole point of the tool and the one case it exists to catch.
        capture("n1")
        time.sleep(0.02)
        pred = write("N1.md", "```cells\n" + os.path.join(d, "n1") + "\n```\n")
        v, c = check(pred, quiet=True)
        if len(v) != 1:
            bad.append("N1 a capture OLDER than its prediction was not caught")

        # N2 -- a predicted cell with no capture at all: must be caught, not
        # silently skipped.  A cell that never ran reads as a pass otherwise,
        # which is how A2 and E5 were recorded as done.
        pred = write("N2.md", "```cells\n" + os.path.join(d, "absent") + "\n```\n")
        v, c = check(pred, quiet=True)
        if len(v) != 1:
            bad.append("N2 a predicted cell whose capture does not exist was "
                       "not caught")

        # N3 -- an empty cells block: must refuse rather than report clean.
        pred = write("N3.md", "```cells\n```\n")
        try:
            check(pred, quiet=True)
            bad.append("N3 an empty cells block reported a clean result")
        except ValueError:
            pass
    return bad


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    print("check-predictions controls")
    bad = controls()
    for b in bad:
        print(f"  FAIL  {b}")
    if bad:
        print("\n  controls failed -- refusing to report on the file")
        return 2
    print("  ok    P1 prediction-before-capture passes")
    print("  ok    N1 capture-before-prediction is caught")
    print("  ok    N2 a predicted cell with no capture is caught")
    print("  ok    N3 an empty cells block is refused, not reported clean")
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
