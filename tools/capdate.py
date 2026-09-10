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
``D4`` (index)  every directory under ``root`` must appear exactly once
                in ``README.md``'s index section, and every row of that
                index must name a directory that exists.  Both
                directions, because a row left behind by a rename is as
                wrong as a directory nobody added.  An absent index
                section is RED, not a skip.  ``BRD-README-1``.

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


# ---------------------------------------------------------------------------
# D4.  The index in bench/README.md, swept in BOTH directions.
#
# ``BRD-README-1``: the file opens by calling itself the evidence behind
# RUNSHEET's Results tables, it reads as a per-directory index, and 量
# 2026-09-11 it named 16 of 29 -- with the last five seatings in a row absent.
# It drifted for five seatings because nothing here could see it.
#
# 🔴 The carried-forward item proposed ``ls -d bench/2026-* | wc -l`` against
# ``grep -c '^## 2026'`` as the whole check.  That is a COUNT comparison and it
# passes on a duplicate plus a miss, which is one of the shapes a drifting
# index actually produces.  This is set-based and reports both directions, the
# way ledgerscan, flashwin scan and sweep()'s own STALE loop already do.
#
# 🔴 And it lives beside sweep() rather than inside it.  Its subject is
# `bench/` as a published record, not "a directory tree" -- the controls below
# sweep synthetic trees that have no README at all, and a D4 inside sweep()
# turns four of them red for a reason unrelated to what they test.  量: the
# first draft did that and C7 is what reported it.
# ---------------------------------------------------------------------------

#: The exact heading the index section sits under.  A heading and not an HTML
#: comment, because a marker a reader cannot see is a marker a reader will
#: delete; and an exact string rather than a pattern, because bench/README.md
#: is 1,400 lines of narrative that quotes directory names constantly and any
#: looser rule would pick a paragraph up as a row.
INDEX_HEADING = "## Index \u2014 every directory here, and who owns its record"

BENCH_DIRNAME = re.compile(r"^2026-\d\d-\d\d[a-z]?$")


def index_rows(readme_path):
    """Return (rows, found_section).

    A row is a Markdown table row inside the index section whose first cell is
    a directory name, optionally backticked and optionally bolded.  The
    section ends at the next ``## `` heading, so a table after it is not read.
    """
    try:
        with open(readme_path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return [], False
    start = None
    for i, line in enumerate(lines):
        if line.strip() == INDEX_HEADING:
            start = i
            break
    if start is None:
        return [], False
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip().strip("*").strip("`").strip()
        if BENCH_DIRNAME.match(cell):
            rows.append(cell)
    return rows, True


def index_coverage(root, readme_path):
    """Return (missing, orphan, dup, found, n_on_disk).

    ``missing`` is on disk and not in the index; ``orphan`` is in the index
    and not on disk.  Neither direction is optional: a row left behind by a
    rename is as wrong as a directory nobody added.
    """
    on_disk = sorted(
        n for n in (os.listdir(root) if os.path.isdir(root) else [])
        if BENCH_DIRNAME.match(n) and os.path.isdir(os.path.join(root, n)))
    rows, found = index_rows(readme_path)
    missing = [d for d in on_disk if d not in rows]
    orphan = [r for r in rows if r not in on_disk]
    dup = sorted(r for r in set(rows) if rows.count(r) > 1)
    return missing, orphan, dup, found, len(on_disk)


def index_check(root):
    """Print D4 and return an exit code.  0 clean, 1 findings, 2 no section.

    2 and not 1 for a missing section, for sweep()'s reason: a check that
    reported nothing because it could not find its subject has not checked
    anything, and a green there is a claim about nothing.
    """
    readme = os.path.join(root, "README.md")
    missing, orphan, dup, found, n_dirs = index_coverage(root, readme)
    if not found:
        print("  D4    REFUSING -- %s has no %r section, so this check has "
              "nothing to report on" % (readme, INDEX_HEADING))
        return 2
    for d in missing:
        print("  D4    %-24s on disk and not in the index" % d)
    for d in orphan:
        print("  D4    %-24s in the index and no such directory" % d)
    for d in dup:
        print("  D4    %-24s named twice in the index" % d)
    bad = len(missing) + len(orphan) + len(dup)
    if not bad:
        print("  D4    index covers all %d directories, both directions"
              % n_dirs)
    return 1 if bad else 0


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

        # ------------------------------------------------------------------
        # D4's controls.  Four, and C15 is the one that makes the other three
        # mean anything: without a case that must come out clean, C14/C16/C17
        # all pass for a checker that calls every directory missing.
        # ------------------------------------------------------------------
        def _readme(path, listed):
            body = ["# bench/", "", INDEX_HEADING, "",
                    "| dir | note |", "|---|---|"]
            body += ["| `%s` | x |" % d for d in listed]
            body += ["", "## After the index", "",
                     "| dir | note |", "|---|---|", "| `2026-12-31` | x |"]
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(body) + "\n")

        root = os.path.join(tmp, "c14")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-02T10:00:00+0800")
        _mk(os.path.join(root, "2026-01-03"), "a", "2026-01-03T10:00:00+0800")
        _readme(os.path.join(root, "README.md"), ["2026-01-02"])
        miss, orph, dup, found, n = index_coverage(
            root, os.path.join(root, "README.md"))
        ck("C14", found and miss == ["2026-01-03"] and not orph and n == 2,
           "a directory on disk and not in the index must be reported; got "
           "found=%r missing=%r orphan=%r n=%r" % (found, miss, orph, n))

        # C15 negative: a complete index must come out clean, AND the table
        # after the next heading must not contribute a row -- which is what
        # makes the section delimiter a delimiter rather than a decoration.
        root = os.path.join(tmp, "c15")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-02T10:00:00+0800")
        _mk(os.path.join(root, "2026-01-03"), "a", "2026-01-03T10:00:00+0800")
        _readme(os.path.join(root, "README.md"), ["2026-01-02", "2026-01-03"])
        miss, orph, dup, found, n = index_coverage(
            root, os.path.join(root, "README.md"))
        ck("C15", found and not miss and not orph and not dup and n == 2,
           "a complete index must be clean and the table after the next "
           "heading must not be read; got missing=%r orphan=%r dup=%r"
           % (miss, orph, dup))

        # C16 positive, the other direction: a row naming no directory.
        root = os.path.join(tmp, "c16")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-02T10:00:00+0800")
        _readme(os.path.join(root, "README.md"), ["2026-01-02", "2026-01-09"])
        miss, orph, dup, found, n = index_coverage(
            root, os.path.join(root, "README.md"))
        ck("C16", found and not miss and orph == ["2026-01-09"],
           "an index row naming no directory must be reported; got "
           "missing=%r orphan=%r" % (miss, orph))

        # C17: no section at all must REFUSE with 2, not report a clean
        # sweep.  A count check would have read this as `0 == 0` and gone
        # green, which is the whole reason D4 is set-based.
        root = os.path.join(tmp, "c17")
        _mk(os.path.join(root, "2026-01-02"), "a", "2026-01-02T10:00:00+0800")
        with open(os.path.join(root, "README.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# bench/\n\nno index here\n")
        os.environ[RECURSION_GUARD] = "1"
        try:
            rc17 = index_check(root)
        finally:
            os.environ.pop(RECURSION_GUARD, None)
        ck("C17", rc17 == 2,
           "an absent index section must return 2, not a clean 0; got %r"
           % (rc17,))

    return bad, ran


def run_controls():
    print("capdate controls")
    bad, ran = controls()
    expected = 17
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
    rc = sweep(args.root, quiet=args.quiet)
    rc4 = index_check(args.root)
    return rc or rc4


if __name__ == "__main__":
    sys.exit(main())
