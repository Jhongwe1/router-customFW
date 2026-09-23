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
``D5``-``D10``  a CARD's own declared date, ``CAPD-1``.  See *Cards* below.

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

Cards: ``D5``-``D10`` (``CAPD-1``)
----------------------------------
``D1`` can fire only once captures exist, and it checks the DIRECTORY.  From
``bench/2026-09-17b/PREDICTIONS-B25-block24.md`` on, a card carries its own
claim, ``**declared date 2026-09-17**``, and before this section nothing parsed
the date: ``cardcheck numbers`` counts the string and never reads it.  For
every ``PREDICTIONS-*.md`` under ``root``:

``D5``  the token is ``**declared date YYYY-MM-DD**`` with a date that exists,
        and a card holds one date.  Between its words: spaces, or ONE line
        break -- a wrap once split it, and Markdown still reads one bold span
        (``bench/2026-09-19/CORRECTIONS-block27.md`` F12).  Nested in other
        bold text is fine (three cards in ``bench/2026-09-20b``).  Any other
        ``**declared date`` is RED as malformed, never read as "no token".
``D6``  the date is the date part of the card's directory name.
``D7``  every capture the card's ``cells`` fence names, if it exists, has a
        ``.meta.json`` ``started_wallclock`` on that date in its own offset.
        Not captured yet: counted and named, not failed.  A ``.log`` with no
        ``.meta.json`` (a host command's redirected output): counted and named
        as undatable.  A ``.meta.json`` present with no readable date: RED.
        The fence grammar is ``check-predictions.py``'s, imported.
``D8``  every capture in the card's directory that no dated card fences --
        ``looprun``'s artefacts, ``X``-prefixed off-card cells -- is on the
        date too.  量 2026-09-23: 490 of those in the declaring directories
        against 317 dated fenced captures, so without ``D8`` the claim would
        cover the smaller part of every seating.
``D9``  ``**another day than `bench/<dir>/PREDICTIONS-<x>.md`**`` (backticks
        optional; the path written the way the card's cells are, from the
        directory above ``root``) says the two seatings are on different
        calendar days.  RED when the card declares no date, the path is not a
        card under ``root``, that card has no single valid date, or the two
        dates are equal.  With ``D7``/``D8`` green on both cards, no calendar
        day holds captures of both seatings.
``D10`` the rule's reach.  It starts at ``RULE_ANCHOR``, a card named rather
        than a date.  A card sorting at or after it with no token is RED
        unless ``UNDECLARED_BY_NAME`` names it; one before it is counted
        ``UNDECL`` and never failed, and how many there are is pinned in
        ``CARDS_BEFORE_RULE`` so that a card written into an older directory
        -- out of the rule's reach -- is a red rather than one more ``UNDECL``.

Both exception lists are swept in both directions, as ``KNOWN_MISNAMED`` is,
and a ``KNOWN_CARD_DATE`` entry covers only the codes it lists.

What the card checks do NOT prove:

* A ``.log`` with no ``.meta.json`` has no committed date and is never dated.
  量 2026-09-23: 88 fenced cells of the 18 declaring cards and 80 off-card
  captures are of that kind -- ``ping``, ``iperf3``, ``socat`` output.
* ``D9`` does not prove two sittings.  A seating ending 23:59 and the next
  starting 00:01 pass; the hours between the two seatings' captures are
  printed and not judged, because no threshold has been set by anyone.
* Before a seating, ``D6`` compares two predictions -- the card's date and the
  directory's name -- and both can be wrong together.  That is how
  ``2026-09-21/PREDICTIONS-B35-block33.md`` declared 2026-09-21 and ran every
  dated cell on 2026-09-20 (``KNOWN_CARD_DATE``).  Only a comparison with the
  host clock when the card is frozen could catch that before power, and it is
  not built here.
* A pre-anchor card added and another deleted in the same tree cancel in
  ``CARDS_BEFORE_RULE``.  And everything above about the host clock holds.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys
import textwrap

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


def capture_when(meta_path):
    """(datetime, reason).  Exactly one of the two is None.

    The datetime is aware and keeps the capture's OWN offset, so ``.date()``
    is the operator's local day -- see the module docstring.  The card checks
    need the time as well as the day (``D9`` prints the hours between two
    seatings), so this is the one reader and ``capture_date`` wraps it.
    """
    try:
        with open(meta_path, encoding="utf-8") as fh:
            j = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "unreadable: %s" % exc
    # A body that is valid JSON and not an object used to escape as an
    # AttributeError traceback from ``j.get``.
    s = j.get("started_wallclock") if isinstance(j, dict) else None
    if not isinstance(s, str) or not s:
        return None, "no started_wallclock"
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None, "started_wallclock %r does not parse" % s
    return dt, None


def capture_date(meta_path):
    """(date, reason).  Exactly one of the two is None.

    The date is in the capture's OWN offset -- see the module docstring.
    """
    dt, why = capture_when(meta_path)
    if dt is None:
        return None, why
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
# D5-D10.  A card's own declared date, ``CAPD-1``.  The module docstring's
# *Cards* section says what each check is and what none of them proves.
#
# These read CARDS where everything above reads directories, and they live in
# this file anyway: the question is the one D1 asks -- is a claimed seating
# date the day the committed clock recorded? -- answered from the same
# ``started_wallclock`` through the same reader.  A second tool reading that
# clock its own way is how the two would come to disagree.
# ---------------------------------------------------------------------------

#: Between a token's words: spaces or tabs, or ONE line break with any
#: indentation.  A blank line ends a Markdown paragraph, so it ends the token.
_WS = r"(?:[ \t]*\r?\n[ \t]*|[ \t]+)"

DECL_TOKEN = re.compile(r"\*\*declared" + _WS + r"date" + _WS
                        + r"(\d{4}-\d{2}-\d{2})\*\*")

#: Whatever STARTS a token, in any case.  An opening that does not complete
#: DECL_TOKEN is RED as malformed: read as "no token", a typo on a card before
#: the anchor would pass as one more UNDECL.
DECL_OPEN = re.compile(r"\*\*declared\s+date", re.I)

AWAY_TOKEN = re.compile(r"\*\*another" + _WS + r"day" + _WS + r"than" + _WS
                        + r"(`?)([^\s`*]+)\1\*\*")
AWAY_OPEN = re.compile(r"\*\*another\s+day\s+than", re.I)

#: ``D10``: where the rule begins -- the first card that carried the token.
#: 量 2026-09-23: 18 cards contain ``**declared date`` and none of them sorts
#: before this one.  A NAME and not a date, for ``KNOWN_MISNAMED``'s reason.
#: Cards sort by their path under ``root``, directory first.
RULE_ANCHOR = "2026-09-17b/PREDICTIONS-B25-block24.md"

#: 量 2026-09-23: 85 cards under bench/, 66 of them sorting before RULE_ANCHOR.
#: The module docstring says why the number is pinned and what it misses.
CARDS_BEFORE_RULE = 66

#: Cards at or after RULE_ANCHOR that carry no token, BY NAME.
UNDECLARED_BY_NAME = {
    "2026-09-20b/PREDICTIONS-B31-postmortem.md":
        "says of itself 'It is not a frozen card' (its section 0): written at "
        "the desk with the board parked at the loader, with no cells fence "
        "and no cardnum rows, and its first line dates it in prose ('Seating "
        "30, 2026-09-20, power cycle 1.') rather than with the token.  Its "
        "captures (P1-TXTHI ...) are in 2026-09-20b, where D8 dates them "
        "against that directory's three declaring cards",
}

#: Frozen cards whose declared date a check REFUTES, BY NAME and BY CODE: an
#: entry covers the codes it lists and nothing else.
#:
#: 量 2026-09-23, on this section's first sweep.  The card was committed
#: 2026-09-20 23:16:35 (``d9decda``) declaring 2026-09-21, for a power cycle
#: its own first line says was spent at 2026-09-20 22:29.  All 22 of its dated
#: fenced captures started 2026-09-20 23:16:54-23:27:08, and 24 of the 37
#: dated off-card captures in its directory 23:28:26-23:59:55; the seating
#: crossed midnight at ``W2-START`` (00:00:15), 33 minutes after its last
#: dated carded cell (its 7 host-log cells carry no date at all).  So the
#: directory's name predicted that the seating would cross midnight --
#: 2026-08-30's failure -- and the card repeated the prediction instead of
#: checking it.  ``D2`` saw a ``SPAN`` and nothing else.  Not edited, for
#: ``KNOWN_MISNAMED``'s reason.
KNOWN_CARD_DATE = {
    "2026-09-21/PREDICTIONS-B35-block33.md": (
        ("D7", "D8"),
        "declared 2026-09-21; its 22 dated fenced captures and 24 off-card "
        "ones ran 2026-09-20 23:16:54-23:59:55, before the seating crossed "
        "midnight at W2-START"),
}


class CardRefuse(Exception):
    """The card checks cannot report on this tree.  Exit 2, with the reason."""


#: check-predictions.py's ``parse_cells``, once loaded.
_FENCE_PARSER = []


def fence_parser():
    """The ``cells`` fence grammar, imported so that it has ONE owner.

    ``check-predictions.py`` defines what a fence is and which entries are
    malformed (its ``N8``, ``N9``).  A second parser here would be a second
    answer to which captures a card predicts, and the two would drift.
    """
    if _FENCE_PARSER:
        return _FENCE_PARSER[0]
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "check-predictions.py")
    try:
        spec = importlib.util.spec_from_file_location("checkpredictions", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = mod.parse_cells
    except (OSError, ImportError, SyntaxError, AttributeError) as exc:
        raise CardRefuse("cannot import the ```cells grammar from %s: %s"
                         % (path, exc))
    _FENCE_PARSER.append(fn)
    return fn


def _names(items, n=4):
    """Basenames of the first ``n`` items (strings, or pairs led by one)."""
    names = [os.path.basename(i[0] if isinstance(i, tuple) else i)
             for i in items]
    more = len(names) - n
    return ", ".join(names[:n]) + (" and %d more" % more if more > 0 else "")


def _by_date(pairs):
    """``2026-09-20 x22 (23:16:54-23:27:08)`` for (name, datetime) pairs."""
    groups = {}
    for _, dt in pairs:
        groups.setdefault(dt.date(), []).append(dt)
    return ", ".join("%s x%d (%s-%s)" % (
        d.isoformat(), len(v), min(v).strftime("%H:%M:%S"),
        max(v).strftime("%H:%M:%S")) for d, v in sorted(groups.items()))


def _unmatched(opener, token, text):
    """An excerpt of every ``opener`` match that does not begin a ``token``."""
    starts = set(m.start() for m in token.finditer(text))
    return [text[m.start():m.start() + 44]
            for m in opener.finditer(text) if m.start() not in starts]


class CardReport(object):
    """One card: what it declares, and what D5-D10 found about it."""

    def __init__(self, root_abs, path):
        self.path = os.path.abspath(path)
        self.rel = os.path.relpath(self.path, root_abs).replace(os.sep, "/")
        self.key = tuple(self.rel.split("/"))
        self.dir = os.path.dirname(self.path)
        self.tries = False      # holds a `**declared date` opening at all
        self.date = None        # its one valid declared date, else None
        self.away = []          # `another day than` targets, as written
        self.found = []         # (code, message)
        self.exempt = ()        # the KNOWN_CARD_DATE codes that cover it
        self.note = None        # an exception list's reason, when listed
        self.stale = []         # an exception that no longer applies
        self.info = []          # D9's facts, printed and not judged
        self.verdict = None
        self.fenced = []        # absolute prefixes its cells fence names
        self.dated = []         # (cell, datetime) on the declared date
        self.wrong = []         # (cell, datetime) on another date
        self.broken = []        # (cell, why): a .meta.json with no date
        self.no_meta = []       # cells with a .log and no .meta.json
        self.absent = []        # cells with neither

    @property
    def n_exist(self):
        return (len(self.dated) + len(self.wrong) + len(self.broken)
                + len(self.no_meta))

    def parse(self):
        """D5, and the D9 targets.  Reads the card's text and nothing else."""
        try:
            with open(self.path, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, ValueError) as exc:
            # RED wherever it sorts: a card this cannot read is not a card
            # without a token.
            self.tries = True
            self.found.append(("D5", "cannot read the card: %s" % exc))
            return
        self.tries = bool(DECL_OPEN.search(text))
        for bad in _unmatched(DECL_OPEN, DECL_TOKEN, text):
            self.found.append(("D5", "%r is not **declared date YYYY-MM-DD**"
                                     % bad))
        valid = []
        for m in DECL_TOKEN.finditer(text):
            s = m.group(1)
            try:
                d = datetime.date(int(s[:4]), int(s[5:7]), int(s[8:]))
            except ValueError:
                self.found.append(("D5", "declared date %s does not exist"
                                         % s))
                continue
            if d not in valid:
                valid.append(d)
        if len(valid) > 1:
            self.found.append(("D5", "declares %d different dates: %s" % (
                len(valid), ", ".join(d.isoformat() for d in valid))))
        if len(valid) == 1 and not self.found:
            self.date = valid[0]
        self.away = [m.group(2) for m in AWAY_TOKEN.finditer(text)]
        for bad in _unmatched(AWAY_OPEN, AWAY_TOKEN, text):
            self.found.append(("D9", "%r is not **another day than <card>**"
                                     % bad))

    def check_dir(self):
        """D6: the declared date is the day the directory is named for."""
        named = dir_date(self.dir)
        if named is None:
            self.found.append(("D6", "its directory %r is not named for a "
                                     "date" % os.path.basename(self.dir)))
        elif named != self.date:
            self.found.append(("D6", "declares %s in a directory named for %s"
                                     % (self.date.isoformat(),
                                        named.isoformat())))

    def check_fence(self, base, parse_cells):
        """D7: the captures its ``cells`` fence names, resolved from base."""
        try:
            cells, seen, bad = parse_cells(self.path)
        except (OSError, ValueError) as exc:
            self.found.append(("D7", "cannot read its ```cells fence: %s"
                                     % exc))
            return
        if bad:
            self.found.append(("D7", "%d malformed ```cells entr%s -- %s: %r"
                               % (len(bad), "y" if len(bad) == 1 else "ies",
                                  bad[0][1], bad[0][0][:60])))
            return
        if not seen or not cells:
            self.found.append(("D7", "declares a date and has no usable "
                                     "```cells fence, so the date is checked "
                                     "against nothing"))
            return
        for cell in cells:
            p = os.path.normpath(os.path.join(base, cell))
            self.fenced.append(p)
            if os.path.exists(p + ".meta.json"):
                when, why = capture_when(p + ".meta.json")
                if when is None:
                    self.broken.append((cell, why))
                elif when.date() != self.date:
                    self.wrong.append((cell, when))
                else:
                    self.dated.append((cell, when))
            elif os.path.exists(p + ".log"):
                self.no_meta.append(cell)
            else:
                self.absent.append(cell)
        if self.wrong:
            self.found.append(("D7", "%d of %d dated fenced capture(s) not on "
                                     "the declared %s: %s -- %s" % (
                                         len(self.wrong),
                                         len(self.wrong) + len(self.dated),
                                         self.date.isoformat(),
                                         _by_date(self.wrong),
                                         _names(self.wrong))))
        if self.broken:
            self.found.append(("D7", "%d fenced .meta.json with no readable "
                                     "date -- %s: %s" % (
                                         len(self.broken),
                                         os.path.basename(self.broken[0][0]),
                                         self.broken[0][1])))


def offcard(d, fenced):
    """(dated, no_meta, broken) for the captures in ``d`` that no prefix in
    the set ``fenced`` names.  A capture is a ``.meta.json`` or a ``.log``.
    dated is [(name, datetime)], no_meta [name], broken [(name, why)]."""
    metas = dict((os.path.normpath(m[:-len(".meta.json")]), m)
                 for m in glob.glob(os.path.join(d, "*.meta.json")))
    logs = set(os.path.normpath(p[:-len(".log")])
               for p in glob.glob(os.path.join(d, "*.log")))
    dated, no_meta, broken = [], [], []
    for stem in sorted(set(metas) | logs):
        if stem in fenced:
            continue
        name = os.path.basename(stem)
        if stem in metas:
            when, why = capture_when(metas[stem])
            if when is None:
                broken.append((name, why))
            else:
                dated.append((name, when))
        else:
            no_meta.append(name)
    return dated, no_meta, broken


class CardSweep(object):
    """What one card sweep found.  ``refused`` set means nothing was judged."""

    def __init__(self, anchor, n_before):
        self.anchor = anchor
        self.n_before = n_before
        self.cards = []
        self.refused = None
        self.pop = []           # (verdict, message): the pin, dead entries
        self.before = 0
        self.off = {}           # directory -> offcard() of it
        self.span = {}          # directory -> (first, last) datetime, or None

    def first_last(self, d):
        """The first and last ``started_wallclock`` in directory ``d``."""
        if d not in self.span:
            whens = [w for w, _ in (capture_when(m) for m in glob.glob(
                os.path.join(d, "*.meta.json"))) if w is not None]
            self.span[d] = (min(whens), max(whens)) if whens else None
        return self.span[d]


def card_scan(root, anchor=None, n_before=None, undeclared=None, known=None):
    """D5-D10 over every card under ``root``.  Returns a CardSweep.

    The four keywords default to this module's constants, read at CALL time,
    so the controls can hand in their own -- ``DirReport``'s ``known``, again.
    """
    anchor = RULE_ANCHOR if anchor is None else anchor
    n_before = CARDS_BEFORE_RULE if n_before is None else n_before
    undeclared = UNDECLARED_BY_NAME if undeclared is None else undeclared
    known = KNOWN_CARD_DATE if known is None else known
    r = CardSweep(anchor, n_before)
    root_abs = os.path.abspath(root)
    # Cells are written from the directory ABOVE root (``bench/<d>/X``), so
    # they resolve from there and never from the working directory, which
    # check-predictions' docstring names as one of three ways to read every
    # cell as absent.
    base = os.path.dirname(root_abs)
    r.cards = sorted((CardReport(root_abs, p) for p in glob.glob(
        os.path.join(root_abs, "**", "PREDICTIONS-*.md"), recursive=True)),
        key=lambda c: c.key)
    if not r.cards:
        r.refused = "no PREDICTIONS-*.md under %r" % root
        return r
    by_rel = dict((c.rel, c) for c in r.cards)
    if anchor not in by_rel:
        r.refused = ("the rule's anchor %s is not a card under %r, so which "
                     "cards must declare a date is undefined" % (anchor, root))
        return r
    try:
        parse_cells = fence_parser()
    except CardRefuse as exc:
        r.refused = str(exc)
        return r
    for c in r.cards:
        c.parse()
    if not any(c.tries for c in r.cards):
        r.refused = ("not one of %d card(s) declares a date, so a green here "
                     "would be a claim about nothing" % len(r.cards))
        return r

    dated = [c for c in r.cards if c.date is not None]
    for c in dated:
        c.check_dir()
        c.check_fence(base, parse_cells)
    n_cells = sum(len(c.fenced) for c in dated)
    if n_cells and not sum(c.n_exist for c in dated):
        r.refused = ("%d dated card(s) fence %d cell(s) and NOT ONE resolved "
                     "to a capture from %r: a renamed directory, a typo'd "
                     "path, or a root whose parent is not where the cells are "
                     "written from" % (len(dated), n_cells, base))
        return r

    # D8.  A capture in a declaring directory is either fenced by a dated card,
    # and D7 dated it, or off-card and dated here.  Nothing falls between.
    fenced = set(p for c in dated for p in c.fenced)
    for c in dated:
        if c.dir not in r.off:
            r.off[c.dir] = offcard(c.dir, fenced)
        odated, _, obroken = r.off[c.dir]
        wrong = [(n, t) for n, t in odated if t.date() != c.date]
        if wrong:
            c.found.append(("D8", "%d of %d dated off-card capture(s) in %s "
                                  "not on the declared %s: %s -- %s" % (
                                      len(wrong), len(odated),
                                      os.path.basename(c.dir),
                                      c.date.isoformat(), _by_date(wrong),
                                      _names(wrong))))
        if obroken:
            c.found.append(("D8", "%d off-card .meta.json in %s with no "
                                  "readable date -- %s: %s" % (
                                      len(obroken), os.path.basename(c.dir),
                                      obroken[0][0], obroken[0][1])))

    # D9.
    by_abs = dict((c.path, c) for c in r.cards)
    for c in r.cards:
        for target in c.away:
            where = "another day than %s" % target
            p = os.path.normpath(os.path.join(base, target))
            ref = by_abs.get(p)
            if c.date is None:
                c.found.append(("D9", "%s, with no single valid date of its "
                                      "own to compare" % where))
            elif ref is None:
                c.found.append(("D9", "%s: %s" % (
                    where, "not a card under %s" % root if os.path.exists(p)
                    else "no such file")))
            elif ref.date is None:
                c.found.append(("D9", "%s: that card declares no single valid "
                                      "date" % where))
            elif ref.date == c.date:
                c.found.append(("D9", "%s: both declare %s"
                                      % (where, c.date.isoformat())))
            else:
                a, b = r.first_last(ref.dir), r.first_last(c.dir)
                fact = "%s, which declares %s" % (where, ref.date.isoformat())
                if a is None or b is None:
                    fact += ", and one side has no dated capture yet"
                else:
                    fact += (", %.1f h from its directory's last capture (%s) "
                             "to this directory's first (%s)" % (
                                 (b[0] - a[1]).total_seconds() / 3600.0,
                                 a[1].strftime("%Y-%m-%d %H:%M:%S"),
                                 b[0].strftime("%Y-%m-%d %H:%M:%S")))
                c.info.append(fact)

    # D10.
    akey = tuple(anchor.split("/"))
    r.before = sum(1 for c in r.cards if c.key < akey)
    if r.before != n_before:
        r.pop.append(("RED", "D10: %d card(s) sort before the rule's anchor "
                             "%s where %d were counted -- a card in an older "
                             "directory is out of the rule's reach"
                             % (r.before, anchor, n_before)))
    for c in r.cards:
        if c.tries:
            continue
        if c.key < akey:
            c.verdict = "UNDECL"
        elif c.rel in undeclared:
            c.verdict, c.note = "EXEMPT", undeclared[c.rel]
        else:
            c.found.append(("D10", "no **declared date YYYY-MM-DD**, and it "
                                   "sorts at or after the rule's anchor %s"
                                   % anchor))

    # Both exception lists, in both directions.
    for rel in sorted(undeclared):
        c = by_rel.get(rel)
        if c is None:
            r.pop.append(("STALE", "%s is in UNDECLARED_BY_NAME and is not a "
                                   "card under %s" % (rel, root)))
        elif c.tries:
            c.stale.append("in UNDECLARED_BY_NAME and declares a date now "
                           "-- remove the entry")
        elif c.key < akey:
            c.stale.append("in UNDECLARED_BY_NAME and sorts before the "
                           "rule's anchor, where nothing needs it -- remove "
                           "the entry")
    for rel in sorted(known):
        codes, note = known[rel]
        c = by_rel.get(rel)
        if c is None:
            r.pop.append(("STALE", "%s is in KNOWN_CARD_DATE and is not a "
                                   "card under %s" % (rel, root)))
            continue
        c.exempt, c.note = tuple(codes), note
        have = set(code for code, _ in c.found)
        for code in codes:
            if code not in have:
                c.stale.append("in KNOWN_CARD_DATE for %s, and %s no longer "
                               "fires -- remove it" % (code, code))

    for c in r.cards:
        if [f for f in c.found if f[0] not in c.exempt]:
            c.verdict = "RED"
        elif c.stale:
            c.verdict = "STALE"
        elif c.found:
            c.verdict = "KNOWN"
        elif c.verdict is None:
            c.verdict = "OK"
    return r


def _card_line(c, r):
    """What a card declares, what its captures say, then every finding, D9
    fact and stale exception, on one line."""
    parts = []
    if c.date is not None:
        od, onm, _ = r.off.get(c.dir, ([], [], []))
        parts.append("declared %s; fenced %d: %d on it, %d not, %d with no "
                     ".meta.json, %d not captured yet; off-card in %s: %d "
                     "dated, %d with no .meta.json" % (
                         c.date.isoformat(), len(c.fenced), len(c.dated),
                         len(c.wrong) + len(c.broken), len(c.no_meta),
                         len(c.absent), os.path.basename(c.dir), len(od),
                         len(onm)))
    elif not c.tries:
        parts.append("no declared date")
    parts += ["%s: %s" % f for f in c.found]
    parts += c.info + c.stale
    line = "; ".join(parts)
    if c.note and c.verdict in ("KNOWN", "EXEMPT"):
        line += "  [declared: %s]" % c.note
    return line


def cards_check(root, quiet=False, report=print, **kw):
    """Print D5-D10 and return an exit code: 0 clean, 1 findings, 2 refused.

    2 for a refusal, for sweep()'s reason.  ``report`` is where the lines go,
    so the controls can run this for its exit code without printing it.
    """
    r = card_scan(root, **kw)
    report("capdate cards: each card's declared date against its directory "
           "and the captures (D5-D10)")
    if r.refused:
        report("capdate cards: REFUSING -- %s" % r.refused)
        return 2
    counts = {}
    for c in r.cards:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
        if c.verdict == "UNDECL" or (quiet and c.verdict in ("OK", "EXEMPT")):
            continue
        report("  %-6s %-42s %s" % (c.verdict, c.rel, _card_line(c, r)))
        if quiet and c.verdict != "RED":
            continue
        for label, cells in (("not captured yet", c.absent),
                             ("no .meta.json, so no date", c.no_meta)):
            if cells:
                report(textwrap.fill(
                    "%s (%d): %s" % (label, len(cells), ", ".join(
                        os.path.basename(x) for x in cells)),
                    width=100, initial_indent=" " * 9,
                    subsequent_indent=" " * 11))
    report("  UNDECL %d card(s) sort before the rule's anchor %s (pinned: "
           "%d); %d of them are UNDECL -- no token, and not failed for that"
           % (r.before, r.anchor, r.n_before, counts.get("UNDECL", 0)))
    for v, msg in r.pop:
        report("  %-6s %s" % (v, msg))

    dated = [c for c in r.cards if c.date is not None]
    offs = list(r.off.values())
    report("capdate cards: %d cards, %d declaring a date: %d OK, %d KNOWN, "
           "%d RED, %d STALE, %d EXEMPT, %d UNDECL; %d list or pin finding(s)"
           % (len(r.cards), sum(1 for c in r.cards if c.tries),
              counts.get("OK", 0), counts.get("KNOWN", 0),
              counts.get("RED", 0), counts.get("STALE", 0),
              counts.get("EXEMPT", 0), counts.get("UNDECL", 0), len(r.pop)))
    report("capdate cards: fenced %d = %d on their card's date + %d on "
           "another + %d unreadable + %d with no .meta.json + %d not captured "
           "yet; off-card in %d directories: %d dated + %d with no .meta.json"
           % (sum(len(c.fenced) for c in dated),
              sum(len(c.dated) for c in dated),
              sum(len(c.wrong) for c in dated),
              sum(len(c.broken) for c in dated),
              sum(len(c.no_meta) for c in dated),
              sum(len(c.absent) for c in dated), len(offs),
              sum(len(o[0]) for o in offs), sum(len(o[1]) for o in offs)))
    bad = counts.get("RED", 0) + counts.get("STALE", 0) + len(r.pop)
    return 1 if bad else 0


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

        # ------------------------------------------------------------------
        # D5-D10, the cards.  Each builds <tmp>/cNN/bench and writes its cells
        # the way real cards do, from the directory above root.  C20 is the
        # one that makes the rest mean anything: every RED below also passes
        # for a checker that calls every card RED.
        # ------------------------------------------------------------------
        import contextlib
        import io

        def _mute(*_a, **_k):
            pass

        def _log(d, name):
            """A host command's output: a .log and no .meta.json."""
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, name + ".log"), "wb") as fh:
                fh.write(b"PING 10.1.1.3\n")

        def _card(root, rel, head, cells):
            p = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("# card\n\n%s\n\n```cells\n%s\n```\n"
                         % (head, "\n".join(cells)))

        def _tree(n):
            return os.path.join(tmp, n, "bench")

        def _scan(root, anchor, n_before=0, undeclared=None, known=None):
            return card_scan(root, anchor=anchor, n_before=n_before,
                             undeclared=undeclared or {}, known=known or {})

        def _rc(root, anchor, n_before=0, undeclared=None, known=None):
            return cards_check(root, report=_mute, anchor=anchor,
                               n_before=n_before, undeclared=undeclared or {},
                               known=known or {})

        def _card_of(r, rel):
            return dict((c.rel, c) for c in r.cards).get(rel)

        def _v(r, rel):
            """(verdict, the codes still RED) for one card, or the refusal."""
            if r.refused:
                return ("REFUSED", r.refused)
            c = _card_of(r, rel)
            if c is None:
                return (None, None)
            return (c.verdict, sorted(set(
                code for code, _ in c.found if code not in c.exempt)))

        A = "2026-01-02/PREDICTIONS-A.md"
        A0 = "2026-01-01/PREDICTIONS-A0.md"
        C = "2026-01-03/PREDICTIONS-C.md"
        DAY = "**declared date 2026-01-02**"

        def _plain(n, head=DAY, stamp="2026-01-02T10:00:00+0800"):
            """<n>/bench with card A declaring by ``head``, fencing one
            capture taken at ``stamp``."""
            root = _tree(n)
            _mk(os.path.join(root, "2026-01-02"), "a", stamp)
            _card(root, A, head, ["bench/2026-01-02/a"])
            return root

        # C18 D6: a card declaring a day other than its directory's.  The
        # capture agrees with the card, so D6 is the only thing that can fire.
        root = _plain("c18", "**declared date 2026-01-03**",
                      "2026-01-03T10:00:00+0800")
        got = _v(_scan(root, A), A)
        ck("C18", got == ("RED", ["D6"]),
           "a card declaring a day other than its directory's must be RED on "
           "D6 alone; got %r" % (got,))

        # C19 D7: 00:10 the next LOCAL day is 16:10Z the SAME UTC day, so a
        # checker that normalised to UTC would pass this.
        root = _plain("c19", stamp="2026-01-03T00:10:00+0800")
        got = _v(_scan(root, A), A)
        ck("C19", got == ("RED", ["D7"]),
           "a fenced capture taken the next local day must be RED on D7; got "
           "%r" % (got,))

        # C20 THE NEGATIVE: everything agrees -- a fenced capture at 00:30
        # local (16:30Z the day BEFORE), a host log, a cell never run, and
        # two off-card captures, one dated the same day and one host log.
        # Green, with every count right: the absent and undatable cells are
        # counted and named, not failed.
        root = _tree("c20")
        d = os.path.join(root, "2026-01-02")
        _mk(d, "a", "2026-01-02T00:30:00+0800")
        _log(d, "h")
        _mk(d, "x", "2026-01-02T23:59:00+0800")
        _log(d, "y")
        _card(root, A, DAY, ["bench/2026-01-02/a", "bench/2026-01-02/h",
                             "bench/2026-01-02/n"])
        r = _scan(root, A)
        c = _card_of(r, A)
        off = r.off.get(os.path.abspath(d))
        got = (_v(r, A), c and (len(c.dated), c.no_meta, c.absent),
               off and (len(off[0]), off[1]))
        rc20 = _rc(root, A)
        ck("C20", got == (("OK", []), (1, ["bench/2026-01-02/h"],
                                       ["bench/2026-01-02/n"]), (1, ["y"]))
           and rc20 == 0,
           "the agreeing card must be OK with 1 dated, 1 host log and 1 "
           "absent fenced and 1+1 off-card, exit 0; got %r, rc=%r"
           % (got, rc20))

        # C21 nested in other bold text, as bench/2026-09-20b's three cards.
        root = _plain("c21", "**Seating 30, **declared date 2026-01-02**, "
                             "boot 1 of power cycle 1.** The board")
        r = _scan(root, A)
        c = _card_of(r, A)
        ck("C21", _v(r, A) == ("OK", [])
           and c.date == datetime.date(2026, 1, 2),
           "a token nested inside other bold text must parse; got %r"
           % (_v(r, A),))

        # C22 split by a line wrap, bench/2026-09-19/CORRECTIONS-block27.md
        # F12's shape exactly: the line that made a cardnum count read 0.
        root = _plain("c22", "Frozen before power, and a wrapper broke the "
                             "line inside the token:\n**declared date\n"
                             "2026-01-02** -- see F12.")
        r = _scan(root, A)
        c = _card_of(r, A)
        ck("C22", _v(r, A) == ("OK", [])
           and c.date == datetime.date(2026, 1, 2),
           "a token split across one line break must parse; got %r"
           % (_v(r, A),))

        # C23 but a BLANK line ends the paragraph and so the bold span.  Red
        # as malformed, which is what keeps C22's rule from being "anything".
        root = _plain("c23", "**declared date\n\n2026-01-02**")
        got = _v(_scan(root, A), A)
        ck("C23", got == ("RED", ["D5"]),
           "a token split by a blank line must be RED on D5 as malformed; got "
           "%r" % (got,))

        # C24 two different dates in one card.
        root = _plain("c24", DAY + ", and further down, **declared date "
                                   "2026-01-03**")
        got = _v(_scan(root, A), A)
        ck("C24", got == ("RED", ["D5"]),
           "a card declaring two different dates must be RED on D5; got %r"
           % (got,))

        # C25 a date the regex accepts and the calendar does not.
        F = "2026-02-28/PREDICTIONS-F.md"
        root = _tree("c25")
        _mk(os.path.join(root, "2026-02-28"), "a", "2026-02-28T10:00:00+0800")
        _card(root, F, "**declared date 2026-02-30**", ["bench/2026-02-28/a"])
        got = _v(_scan(root, F), F)
        ck("C25", got == ("RED", ["D5"]),
           "declared date 2026-02-30 must be RED on D5; got %r" % (got,))

        # C26 another day than a card that declares the SAME day.
        Bc = "2026-01-02b/PREDICTIONS-B.md"
        root = _plain("c26")
        _mk(os.path.join(root, "2026-01-02b"), "b", "2026-01-02T20:00:00+0800")
        _card(root, Bc, DAY + " -- **another day than "
                              "`bench/2026-01-02/PREDICTIONS-A.md`**",
              ["bench/2026-01-02b/b"])
        r = _scan(root, A)
        got = (_v(r, A), _v(r, Bc))
        ck("C26", got == (("OK", []), ("RED", ["D9"])),
           "another day than a card declaring the same day must be RED on D9; "
           "got %r" % (got,))

        # C27 THE NEGATIVE for C26/C28/C29: a different day is green, and the
        # hours between the two directories' captures are printed, computed.
        # Unquoted path, and a line break between the two tokens.
        root = _plain("c27", stamp="2026-01-02T22:00:00+0800")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T09:00:00+0800")
        _card(root, C, "**declared date 2026-01-03**\n**another day than "
                       "bench/2026-01-02/PREDICTIONS-A.md**",
              ["bench/2026-01-03/c"])
        r = _scan(root, A)
        c = _card_of(r, C)
        ck("C27", _v(r, C) == ("OK", [])
           and any("11.0 h" in i for i in (c.info if c else [])),
           "another day than a card declaring another day must be OK with "
           "11.0 h reported; got %r, %r" % (_v(r, C), c and c.info))

        # C28 another day than a card that does not exist.
        root = _tree("c28")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T09:00:00+0800")
        _card(root, C, "**declared date 2026-01-03** **another day than "
                       "`bench/2026-01-09/PREDICTIONS-Z.md`**",
              ["bench/2026-01-03/c"])
        got = _v(_scan(root, C), C)
        ck("C28", got == ("RED", ["D9"]),
           "another day than a missing card must be RED on D9; got %r"
           % (got,))

        # C29 another day than a card with no declared date.  That card sorts
        # before the anchor, so it is UNDECL and D9 is the only thing red.
        root = _tree("c29")
        _mk(os.path.join(root, "2026-01-01"), "z", "2026-01-01T10:00:00+0800")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T09:00:00+0800")
        _card(root, A0, "Seating 1, 2026-01-01, in prose only.",
              ["bench/2026-01-01/z"])
        _card(root, C, "**declared date 2026-01-03** **another day than "
                       "`bench/2026-01-01/PREDICTIONS-A0.md`**",
              ["bench/2026-01-03/c"])
        r = _scan(root, C, n_before=1)
        got = (_v(r, A0), _v(r, C))
        ck("C29", got == (("UNDECL", []), ("RED", ["D9"])),
           "another day than an undeclared card must be RED on D9; got %r"
           % (got,))

        # C30 D8: a capture no card fences, taken the next local day.
        root = _plain("c30")
        _mk(os.path.join(root, "2026-01-02"), "x", "2026-01-03T00:05:00+0800")
        got = _v(_scan(root, A), A)
        ck("C30", got == ("RED", ["D8"]),
           "an off-card capture on another day must be RED on D8; got %r"
           % (got,))

        # -------- D10: the rule's reach --------

        # C31 a card at or after the anchor with no token.
        root = _plain("c31")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T10:00:00+0800")
        _card(root, C, "Seating 3, in prose only.", ["bench/2026-01-03/c"])
        got = _v(_scan(root, A), C)
        ck("C31", got == ("RED", ["D10"]),
           "a card after the anchor with no token must be RED on D10; got %r"
           % (got,))

        # C32 THE NEGATIVE for C31 and C33: one before the anchor is counted
        # UNDECL and never failed, when the pin says one.
        root = _plain("c32")
        _mk(os.path.join(root, "2026-01-01"), "z", "2026-01-01T10:00:00+0800")
        _card(root, A0, "Seating 1, in prose only.", ["bench/2026-01-01/z"])
        got = _v(_scan(root, A, n_before=1), A0)
        rc32 = _rc(root, A, n_before=1)
        ck("C32", got == ("UNDECL", []) and rc32 == 0,
           "a card before the anchor with no token must be UNDECL, exit 0; "
           "got %r, rc=%r" % (got, rc32))

        # C33 the same tree against a pin of zero: a card has appeared where
        # the rule cannot reach it.
        r = _scan(root, A, n_before=0)
        rc33 = _rc(root, A, n_before=0)
        ck("C33", rc33 == 1 and any("D10" in m for _, m in r.pop),
           "a card count before the anchor that differs from the pin must "
           "exit 1 on D10; got rc=%r pop=%r" % (rc33, r.pop))

        # -------- the exception lists, both directions --------

        # C34 a listed card after the anchor with no token: EXEMPT, green.
        root = _plain("c34")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T10:00:00+0800")
        _card(root, C, "Seating 3, in prose only.", ["bench/2026-01-03/c"])
        und = {C: "declared for C34"}
        got = _v(_scan(root, A, undeclared=und), C)
        rc34 = _rc(root, A, undeclared=und)
        ck("C34", got == ("EXEMPT", []) and rc34 == 0,
           "a listed undeclared card must be EXEMPT, exit 0; got %r, rc=%r"
           % (got, rc34))

        # C35 listed, and it declares a date now: STALE, red.
        root = _plain("c35")
        _mk(os.path.join(root, "2026-01-03"), "c", "2026-01-03T10:00:00+0800")
        _card(root, C, "**declared date 2026-01-03**", ["bench/2026-01-03/c"])
        und = {C: "declared for C35"}
        got = _v(_scan(root, A, undeclared=und), C)
        rc35 = _rc(root, A, undeclared=und)
        ck("C35", got == ("STALE", []) and rc35 == 1,
           "an undeclared-list entry for a card that declares must be STALE, "
           "exit 1; got %r, rc=%r" % (got, rc35))

        # C36 an entry naming no card, in EACH list: only the reverse loops
        # can see them.
        root = _plain("c36")
        und = {"2026-05-05/PREDICTIONS-Q.md": "names nothing"}
        kno = {"2026-05-06/PREDICTIONS-R.md": (("D7",), "names nothing")}
        r = _scan(root, A, undeclared=und, known=kno)
        rc36 = _rc(root, A, undeclared=und, known=kno)
        ck("C36", len(r.pop) == 2 and rc36 == 1,
           "an entry naming no card must be STALE in both lists; got pop=%r "
           "rc=%r" % (r.pop, rc36))

        # C37 a card RED on D7 and listed for D7: KNOWN, green.
        root = _plain("c37", stamp="2026-01-03T10:00:00+0800")
        kno = {A: (("D7",), "declared for C37")}
        got = _v(_scan(root, A, known=kno), A)
        rc37 = _rc(root, A, known=kno)
        ck("C37", got == ("KNOWN", []) and rc37 == 0,
           "a listed refutation must be KNOWN, exit 0; got %r, rc=%r"
           % (got, rc37))

        # C38 an entry covers ONLY its codes: RED on D6 and D7, listed for D7,
        # stays RED on D6.  Keyed on the card alone, it would go green.
        root = _plain("c38", "**declared date 2026-01-03**",
                      "2026-01-04T10:00:00+0800")
        kno = {A: (("D7",), "declared for C38, D7 only")}
        got = _v(_scan(root, A, known=kno), A)
        rc38 = _rc(root, A, known=kno)
        ck("C38", got == ("RED", ["D6"]) and rc38 == 1,
           "an entry must not cover a code it does not list; got %r, rc=%r"
           % (got, rc38))

        # C39 listed for D7, and D7 no longer fires: STALE, red.
        root = _plain("c39")
        kno = {A: (("D7",), "declared for C39")}
        got = _v(_scan(root, A, known=kno), A)
        rc39 = _rc(root, A, known=kno)
        ck("C39", got == ("STALE", []) and rc39 == 1,
           "an entry whose code no longer fires must be STALE, exit 1; got "
           "%r, rc=%r" % (got, rc39))

        # -------- refusals: a green over nothing is a claim about nothing ----

        # C40 the anchor names no card: which cards must declare is undefined.
        root = _plain("c40")
        r = _scan(root, "2026-09-09/PREDICTIONS-none.md")
        rc40 = _rc(root, "2026-09-09/PREDICTIONS-none.md")
        ck("C40", rc40 == 2 and "anchor" in (r.refused or ""),
           "an anchor naming no card must refuse with 2; got rc=%r %r"
           % (rc40, r.refused))

        # C41 not one card declares a date.
        root = _plain("c41", "Seating 2, in prose only.")
        r = _scan(root, A)
        rc41 = _rc(root, A)
        ck("C41", rc41 == 2 and "not one" in (r.refused or ""),
           "a tree where no card declares must refuse with 2; got rc=%r %r"
           % (rc41, r.refused))

        # C42 cells fenced and NOT ONE resolves: every one reads "not captured
        # yet", which is also what a wrong base would print.
        root = _tree("c42")
        _card(root, A, DAY, ["bench/2026-01-02/never"])
        r = _scan(root, A)
        rc42 = _rc(root, A)
        ck("C42", rc42 == 2 and "NOT ONE" in (r.refused or ""),
           "fenced cells none of which resolves must refuse with 2; got rc=%r "
           "%r" % (rc42, r.refused))

        # C43 a .meta.json that is THERE and has no date is RED, not "no
        # .meta.json": the first is a broken record, the second a host log.
        root = _plain("c43", stamp=None)
        r = _scan(root, A)
        c = _card_of(r, A)
        ck("C43", _v(r, A) == ("RED", ["D7"]) and c and c.no_meta == [],
           "a fenced .meta.json with no started_wallclock must be RED on D7; "
           "got %r" % (_v(r, A),))

        # -------- the exit code, through main() --------
        # A finding that does not reach main()'s status is a finding nothing
        # gates on.  main() runs with this module's constants swapped for the
        # tree's and put back after, output swallowed.
        def _main(root, anchor):
            g = globals()
            names = ("RULE_ANCHOR", "CARDS_BEFORE_RULE", "UNDECLARED_BY_NAME",
                     "KNOWN_CARD_DATE", "KNOWN_MISNAMED")
            saved = dict((k, g[k]) for k in names)
            g.update(RULE_ANCHOR=anchor, CARDS_BEFORE_RULE=0,
                     UNDECLARED_BY_NAME={}, KNOWN_CARD_DATE={},
                     KNOWN_MISNAMED={})
            os.environ[RECURSION_GUARD] = "1"
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    return main([root, "--no-controls"])
            finally:
                g.update(saved)
                os.environ.pop(RECURSION_GUARD, None)

        # C44 a clean tree, README index and all: main() exits 0.
        root = _plain("c44")
        _readme(os.path.join(root, "README.md"), ["2026-01-02"])
        rc44 = _main(root, A)
        ck("C44", rc44 == 0,
           "main() over a clean tree must exit 0; got %r" % (rc44,))

        # C45 the same tree with the card RED: D1-D4 are all clean, so only
        # the card checks can make main() exit 1.
        root = _plain("c45", "**declared date 2026-01-03**")
        _readme(os.path.join(root, "README.md"), ["2026-01-02"])
        rc45 = _main(root, A)
        ck("C45", rc45 == 1,
           "main() must exit 1 when only a card is RED; got %r" % (rc45,))

    return bad, ran


def run_controls():
    print("capdate controls")
    bad, ran = controls()
    # 17 -> 45 on 2026-09-23 (``P2-2``, ``CAPD-1``): C18-C45 are the card
    # checks D5-D10.
    expected = 45
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
        description="check bench/<date>/, and each card's declared date, "
                    "against each capture's committed started_wallclock")
    ap.add_argument("root", nargs="?", default="bench",
                    help="the directory holding one subdirectory per seating "
                         "(default: bench)")
    ap.add_argument("--no-controls", action="store_true",
                    help="skip the controls (they are run first by default)")
    ap.add_argument("--quiet", action="store_true",
                    help="print only SPAN and RED directories, and only RED, "
                         "KNOWN and STALE cards")
    args = ap.parse_args(argv)

    if not args.no_controls:
        rc = run_controls()
        if rc:
            return rc
    rc = sweep(args.root, quiet=args.quiet)
    rc4 = index_check(args.root)
    rc5 = cards_check(args.root, quiet=args.quiet)
    return rc or rc4 or rc5


if __name__ == "__main__":
    sys.exit(main())
