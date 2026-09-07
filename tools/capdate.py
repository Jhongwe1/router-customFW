#!/usr/bin/env python3
"""Does a capture's committed ``started_wallclock`` agree with the ``bench/``
directory it was written into?

Why this exists
---------------
``RUNSHEET.md`` § *Four rules about the card's lifecycle*, rule 3, ends with a
⚠️ naming exactly this gap:

    What this does not fix: nothing forces the directory's name to match the
    day the captures were actually taken.  That check would have to read a
    capture's ``.meta.json`` ``started_wallclock`` and compare it with the
    path, and no tool here does.

Three consecutive seatings hit rule 3, and all three were caught by a human
re-measuring the date rather than by anything in this repository.  The third
(2026-09-08, seating 16) was caught sixteen minutes before the board was
powered, and the fix -- holding the power until after midnight so the first
capture's own clock decided the name -- worked only because *no cell had run
yet*.  One capture later and the rename would have cost a cell.

Why it is a SEPARATE tool from ``check-predictions.py``
------------------------------------------------------
``check-predictions`` proves *ordering* from mtimes, and its own docstring
says at length why it can never be a CI gate: a ``git clone`` writes every
file fresh, so 128 of 156 cells read as "capture is OLDER than the
prediction" in a clean checkout.  There is no ordering signal left after a
push.

``started_wallclock`` is **committed content**.  It survives clone, checkout,
stash, rebase and merge unchanged.  So this check is exactly the half of rule
3 that CAN be a CI gate, and putting it inside a tool that is documented as
un-CI-able would bury it.

What it checks
--------------
``D1`` (hard)   the directory's date must be one of the dates on which its
                captures were actually taken.  A directory named for a day
                *none* of its captures happened on is the failure rule 3
                describes, and it has no allow-list: there is no legitimate
                reason for it.
``D2`` (report) a directory whose captures span more than one local date is
                reported with the split.  This is NOT an error -- seating 16
                ran 00:00:02 to 00:32:16 and a seating that starts at 23:50
                legitimately spans two days -- but a reader should be told,
                because every downstream count that says "the seating of
                <date>" is then approximate.
``D3`` (scope)  a directory that holds captures but from which not one
                ``started_wallclock`` could be read is RED, not green.  A
                tool reporting zero mismatches over zero readable timestamps
                is making a claim it cannot support.

What it does NOT prove
----------------------
* ``started_wallclock`` is written by ``console-capture.py`` from the host's
  clock (``time.strftime("%Y-%m-%dT%H:%M:%S%z")``).  If the host clock is
  wrong, this tool agrees with it enthusiastically.  It checks *consistency*
  between two things the operator controls, not correctness against the world.
* It says nothing about whether the predictions were written first.  That is
  ``check-predictions``, and the two answer different questions.
* A capture can be copied into a directory after the fact.  This catches the
  *directory* being wrong, not a *file* being moved.

The local date, not UTC
-----------------------
``bench/<date>`` is named for the operator's local day, so the comparison uses
the date in the capture's **own** UTC offset.  ``2026-01-03T00:30:00+0800`` is
2026-01-03 here and 2026-01-02 in UTC; converting would make every seating
between midnight and 08:00 look misfiled.  ``C6`` is the control on that.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

DIR_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[a-z]?$")

#: Directories this check found wrong on its first run and that may NOT be
#: renamed.  Listed BY NAME, never by date or by pattern, for the same reason
#: flashwin's ``A20`` names its two frozen cards: an exception keyed on
#: anything else silently covers cases nobody has looked at.
#:
#: 量 2026-09-08, on this tool's first sweep of the real corpus.  Both hold
#: captures taken entirely on 2026-08-29 (22:59:15-23:13:02 and
#: 23:16:42-23:26:29) in a directory named 2026-08-30, and ``git log
#: --diff-filter=A`` shows both directories were created BEFORE those captures
#: existed.  So the name was a prediction that the seating would cross
#: midnight, and it did not -- which is exactly the failure ``RUNSHEET`` rule
#: 3 describes, seven days before that rule was written and by eight days the
#: earliest instance in this repository.  Nobody found it by reading.
#:
#: 🔴 They are not renamed, and the reason is measured rather than assumed:
#: 量 2026-09-08, ``git grep`` outside the captures themselves finds 40
#: references to the first across 23 files and 84 to the second across 17,
#: including two FROZEN cards, ``tools/rbcheck.py``,
#: ``tools/rlxprobe/probe3.c`` and ``tools/test-console-capture.sh``.
#: Editing a frozen card is what lifecycle rule 1 records the cost of.  This
#: is the same decision seating 15 made about its malformed ``cells`` fence:
#: do not repair the artefact, teach the checker.
KNOWN_MISNAMED = {
    "2026-08-30": "captures 2026-08-29 22:59:15-23:13:02; directory created "
                  "2026-08-29 18:58:02 (68b0bec) before any of them existed",
    "2026-08-30b": "captures 2026-08-29 23:16:42-23:26:29; directory created "
                   "2026-08-29 05:26:29 (114bf3c) before any of them existed",
}

#: Set in the environment of every subprocess a control spawns, so a control
#: that re-entered the tool cannot recursively run the controls again.  Same
#: mechanism and same reason as check-predictions.py's RECURSION_GUARD.
RECURSION_GUARD = "RLXFW_CAPDATE_IN_CONTROL"


def dir_date(path):
    """The date a bench directory's NAME claims, or None.

    The optional trailing letter is a same-day sequence marker
    (``2026-09-06b``), not part of the date.
    """
    m = DIR_DATE.match(os.path.basename(path.rstrip("/\\")))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def capture_date(meta_path):
    """(date, reason).  Exactly one of the two is None.

    The date is in the capture's OWN offset -- see the module docstring.
    """
    try:
        with open(meta_path, encoding="utf-8") as fh:
            j = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "unreadable: %s" % exc
    s = j.get("started_wallclock")
    if not isinstance(s, str) or not s:
        return None, "no started_wallclock"
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None, "started_wallclock %r does not parse" % s
    return dt.date(), None


class DirReport(object):
    def __init__(self, path, claimed, known=None):
        self.path = path
        self.claimed = claimed
        self.by_date = {}
        self.unreadable = []
        #: injected so the controls can exercise the exception machinery with
        #: their own list instead of the real one
        self.known = KNOWN_MISNAMED if known is None else known

    @property
    def n(self):
        return sum(len(v) for v in self.by_date.values()) + len(self.unreadable)

    @property
    def n_dated(self):
        return sum(len(v) for v in self.by_date.values())

    def _raw(self):
        """The verdict before the exception list is consulted."""
        if self.claimed is None:
            return "SKIP", "directory name is not a date"
        if self.n == 0:
            return "SKIP", "no captures"
        if self.n_dated == 0:
            return "RED", ("D3: %d capture(s) and not one readable "
                           "started_wallclock" % self.n)
        if self.claimed not in self.by_date:
            got = ", ".join("%s x%d" % (d.isoformat(), len(v))
                            for d, v in sorted(self.by_date.items()))
            return "RED", ("D1: named %s, but no capture was taken then "
                           "-- captures are on %s"
                           % (self.claimed.isoformat(), got))
        if len(self.by_date) > 1:
            got = ", ".join("%s x%d" % (d.isoformat(), len(v))
                            for d, v in sorted(self.by_date.items()))
            return "SPAN", ("D2: captures span %d dates: %s"
                            % (len(self.by_date), got))
        return "OK", "%d capture(s), all %s" % (
            self.n_dated, self.claimed.isoformat())

    def verdict(self):
        """('OK'|'SPAN'|'RED'|'KNOWN'|'STALE'|'SKIP', message).

        The exception list is consulted in BOTH directions.  A listed
        directory that is red becomes ``KNOWN``; a listed directory that is
        no longer red becomes ``STALE`` and is an error, because a list that
        keeps entries which no longer apply is a list nobody audits.  Same
        shape as flashwin's ``B10``.
        """
        v, msg = self._raw()
        name = os.path.basename(self.path.rstrip("/\\"))
        listed = self.known.get(name)
        if listed is None:
            return v, msg
        if v == "RED":
            return "KNOWN", "%s  [declared: %s]" % (msg, listed)
        return "STALE", ("this directory is in KNOWN_MISNAMED and is no "
                         "longer wrong (%s) -- remove the entry" % msg)


def scan(root, known=None):
    """Return (reports, n_meta).  One report per immediate subdirectory."""
    reports = []
    n_meta = 0
    if not os.path.isdir(root):
        return reports, n_meta
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        rep = DirReport(d, dir_date(d), known)
        for meta in sorted(glob.glob(os.path.join(d, "*.meta.json"))):
            n_meta += 1
            when, why = capture_date(meta)
            if when is None:
                rep.unreadable.append((os.path.basename(meta), why))
            else:
                rep.by_date.setdefault(when, []).append(
                    os.path.basename(meta))
        reports.append(rep)
    return reports, n_meta


def sweep(root, quiet=False, known=None):
    """Print the report.  Return an exit code.

    2 rather than 1 when the population is empty: a sweep that visited no
    captures has not checked anything, and reporting that as a pass is the
    failure this repository names in four other tools.
    """
    if known is None:
        known = KNOWN_MISNAMED
    reports, n_meta = scan(root, known)
    counts = {}
    for rep in reports:
        v, msg = rep.verdict()
        counts[v] = counts.get(v, 0) + 1
        if quiet and v in ("SKIP", "OK"):
            continue
        print("  %-5s %-24s %s" % (v, os.path.basename(rep.path), msg))
        if v in ("RED", "KNOWN"):
            for fn, why in rep.unreadable[:4]:
                print("          %s: %s" % (fn, why))

    # The exception list, swept in the other direction: an entry naming a
    # directory that is not here at all is as stale as one naming a directory
    # that is now correct, and only this loop can see it.
    seen = set(os.path.basename(r.path.rstrip("/\\")) for r in reports)
    absent = sorted(k for k in known if k not in seen)
    for k in absent:
        print("  STALE %-24s in KNOWN_MISNAMED but no such directory under %s"
              % (k, root))
    counts["STALE"] = counts.get("STALE", 0) + len(absent)

    print("capdate: %d directories, %d captures, %d OK, %d spanning, "
          "%d declared, %d RED, %d stale"
          % (len(reports), n_meta, counts.get("OK", 0), counts.get("SPAN", 0),
             counts.get("KNOWN", 0), counts.get("RED", 0),
             counts.get("STALE", 0)))
    if n_meta == 0:
        print("capdate: REFUSING -- no captures under %r, so a green here "
              "would be a claim about nothing" % root)
        return 2
    return 1 if (counts.get("RED") or counts.get("STALE")) else 0


# ---------------------------------------------------------------------------
# Controls.  Every one of them builds its own tree; none reads bench/.
# ---------------------------------------------------------------------------

def _mk(d, name, stamp):
    os.makedirs(d, exist_ok=True)
    body = {"tool_version": "1.3", "baud": 38400}
    if stamp is not None:
        body["started_wallclock"] = stamp
    with open(os.path.join(d, name + ".meta.json"), "w",
              encoding="utf-8") as fh:
        json.dump(body, fh)
    with open(os.path.join(d, name + ".log"), "wb") as fh:
        fh.write(b"x\r\n")


def controls():
    """Run the controls.  Return (failures, labels that actually ran)."""
    if os.environ.get(RECURSION_GUARD):
        raise RuntimeError("controls() re-entered inside a control")
    import tempfile

    bad = []
    ran = []

    def ck(label, ok, why=""):
        ran.append(label)
        if not ok:
            bad.append("%s: %s" % (label, why))
        # Two leading spaces and then two more after the verdict, because
        # tools/ci-census.py's OK_RE is `^ {2}ok\s{2,}(.*)$` and a suite whose
        # lines it cannot parse reports `ran 0/13` with no failure -- which is
        # the shape this repository calls a census mismatch. 量 2026-09-08:
        # the first draft used four leading spaces and did exactly that.
        print("  %-5s %-6s %s" % ("ok" if ok else "FAIL", label,
                                  "" if ok else "-- " + why))

    with tempfile.TemporaryDirectory() as tmp:
        # C1 positive: a directory named for a day nothing happened on.
        root = os.path.join(tmp, "c1")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-03T10:00:00+0800")
        reps, _ = scan(root, {})
        ck("C1", reps and reps[0].verdict()[0] == "RED",
           "a directory named for a day none of its captures happened on "
           "must be RED; got %r" % ((reps[0].verdict() if reps else None),))

        # C2 negative: the agreeing case must be green.  Without this, C1
        # passes for a tool that says RED to everything.
        root = os.path.join(tmp, "c2")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-02T10:00:00+0800")
        reps, _ = scan(root, {})
        ck("C2", reps and reps[0].verdict()[0] == "OK",
           "an agreeing directory must be OK; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C3 a seating that crosses midnight is SPAN, not RED.
        root = os.path.join(tmp, "c3")
        d = os.path.join(root, "2026-01-02")
        _mk(d, "a", "2026-01-02T23:55:00+0800")
        _mk(d, "b", "2026-01-03T00:05:00+0800")
        reps, _ = scan(root, {})
        ck("C3", reps and reps[0].verdict()[0] == "SPAN",
           "a midnight-crossing seating must be SPAN; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C4 scope: captures present, no timestamp readable -> RED.
        root = os.path.join(tmp, "c4")
        _mk(os.path.join(root, "2026-01-02"), "a", None)
        reps, _ = scan(root, {})
        ck("C4", reps and reps[0].verdict()[0] == "RED",
           "captures with no readable timestamp must be RED, not OK; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C5 the same-day sequence letter is not part of the date.
        root = os.path.join(tmp, "c5")
        _mk(os.path.join(root, "2026-01-02c"), "a",
            "2026-01-02T10:00:00+0800")
        reps, _ = scan(root, {})
        ck("C5", reps and reps[0].verdict()[0] == "OK",
           "2026-01-02c must parse as 2026-01-02; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C6 THE ONE THAT MATTERS: the local date, not UTC.  This capture is
        # 2026-01-02T16:30Z, so a tool that normalised to UTC would call the
        # directory wrong.  It is 2026-01-03 where the operator is standing.
        root = os.path.join(tmp, "c6")
        _mk(os.path.join(root, "2026-01-03"), "a",
            "2026-01-03T00:30:00+0800")
        reps, _ = scan(root, {})
        ck("C6", reps and reps[0].verdict()[0] == "OK",
           "the comparison must use the capture's own offset, not UTC; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C7 an empty root must REFUSE, not pass.
        root = os.path.join(tmp, "c7")
        os.makedirs(root)
        ck("C7", sweep(root, quiet=True, known={}) == 2,
           "an empty root must refuse (2), not report a pass")

        # C8 a directory whose name is not a date is SKIP, and a SKIP must not
        # be counted as OK -- otherwise bench/README.md's neighbours would
        # inflate the pass count.
        root = os.path.join(tmp, "c8")
        _mk(os.path.join(root, "scratch"), "a", "2026-01-02T10:00:00+0800")
        reps, _ = scan(root, {})
        ck("C8", reps and reps[0].verdict()[0] == "SKIP",
           "a directory that is not named for a date must SKIP; got %r"
           % ((reps[0].verdict() if reps else None),))

        # C9 a RED must reach the exit code, not only the printout.  A tool
        # whose finding does not change its status is a tool nothing gates on.
        root = os.path.join(tmp, "c9")
        _mk(os.path.join(root, "2026-01-02"), "a",
            "2026-01-03T10:00:00+0800")
        ck("C9", sweep(root, quiet=True, known={}) == 1,
           "a RED must make the exit code 1")

        # -------- the exception list, both directions --------

        # C10 a listed directory that IS wrong is declared, and green.
        root = os.path.join(tmp, "c10")
        _mk(os.path.join(root, "2026-01-02"), "a",
            "2026-01-03T10:00:00+0800")
        rc = sweep(root, quiet=True, known={"2026-01-02": "declared for C10"})
        ck("C10", rc == 0, "a declared misnaming must not be an error; rc=%d"
                           % rc)

        # C11 THE OTHER DIRECTION: a listed directory that is no longer wrong
        # must be STALE and must fail.  Without this the list can keep entries
        # that stopped applying and nobody would ever be told.
        root = os.path.join(tmp, "c11")
        _mk(os.path.join(root, "2026-01-02"), "a",
            "2026-01-02T10:00:00+0800")
        rc = sweep(root, quiet=True, known={"2026-01-02": "declared for C11"})
        ck("C11", rc == 1,
           "an exception that no longer applies must fail; rc=%d" % rc)

        # C12 an entry naming a directory that is not there at all is stale
        # too, and only the reverse loop can see it.
        root = os.path.join(tmp, "c12")
        _mk(os.path.join(root, "2026-01-02"), "a",
            "2026-01-02T10:00:00+0800")
        rc = sweep(root, quiet=True, known={"2026-05-05": "names nothing"})
        ck("C12", rc == 1,
           "an exception naming an absent directory must fail; rc=%d" % rc)

        # C13 the list is BY NAME.  One declared directory must not make a
        # second, undeclared one green -- which is what a date- or
        # pattern-keyed exception would do.
        root = os.path.join(tmp, "c13")
        _mk(os.path.join(root, "2026-01-02"), "a",
            "2026-01-03T10:00:00+0800")
        _mk(os.path.join(root, "2026-01-04"), "a",
            "2026-01-05T10:00:00+0800")
        reps, _ = scan(root, {"2026-01-02": "declared for C13"})
        got = dict((os.path.basename(r.path), r.verdict()[0]) for r in reps)
        ck("C13", got == {"2026-01-02": "KNOWN", "2026-01-04": "RED"},
           "an exception must cover only the directory it names; got %r"
           % (got,))

    return bad, ran


def run_controls():
    print("capdate controls")
    bad, ran = controls()
    expected = 13
    if len(ran) != expected:
        print("capdate: REFUSING -- %d controls ran, %d expected. A control "
              "set that did not execute proves nothing." % (len(ran), expected))
        return 2
    if bad:
        for b in bad:
            print("  " + b)
        return 2
    print("  %d/%d controls ok" % (len(ran), expected))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="check bench/<date>/ against each capture's committed "
                    "started_wallclock")
    ap.add_argument("root", nargs="?", default="bench",
                    help="the directory holding one subdirectory per seating "
                         "(default: bench)")
    ap.add_argument("--no-controls", action="store_true",
                    help="skip the controls (they are run first by default)")
    ap.add_argument("--quiet", action="store_true",
                    help="print only SPAN and RED directories")
    args = ap.parse_args(argv)

    if not args.no_controls:
        rc = run_controls()
        if rc:
            return rc
    return sweep(args.root, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
