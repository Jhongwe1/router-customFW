#!/usr/bin/env python3
"""citime.py -- what a CI run cost on the SUITE side, derived rather than typed.

WHY IT EXISTS
-------------
`PROGRESS.md`'s `CI-5` carries one number per run: the `instruments` job's
summed step time minus its package-install step.  That number has now been
derived by hand four times, and the hand has slipped twice.

  * 2026-09-03 -- the row quoted `exec`, the sum of every step, as "the suite
    side".  `apt` is a step, so `exec` contains it, and the one run whose
    `apt` was 650 s is exactly the run whose `exec` was 1183 s.  A total that
    contains the noisiest term cannot be evidence that the rest is quiet.
    Corrected in place to `exec - apt`.
  * 2026-09-06 (this file's reason for existing) -- the row states that
    "`text` / `lint` / `census` have no `apt` step".  量: `lint` has had one
    since `970f041`, the commit that first put `apt` in `ci.yml` at all --
    `Run sudo apt-get update -qq && sudo apt-get install -y -qq shellcheck`.
    The row's OWN stated rule (a step named `apt`, or one whose name begins
    `Run sudo apt-get`) catches it.  So the rule and the sentence beside it
    disagreed, and the sentence is the one that was read.

The second one is not a typo.  It is what made a mixed population invisible:
believing `lint` has no `apt` makes "the run's `apt`" and "the `instruments`
job's `apt`" the same quantity, and the two numbers were then written side by
side (`instruments exec - apt = 534`, `apt 22 s`) as though they came from one
place.  They do not: 534 is `instruments` alone, and 22 is `instruments` (16)
plus `lint` (6).

**A rule that lives in prose drifts away from the number it governs.**  This
file is that rule as code, and it records both `apt` figures separately so the
ambiguity cannot come back.

WHAT IT REFUSES TO DO
---------------------
It never prints a bare `exec`.  Every row shows `exec`, `apt` and
`exec - apt` together, under those names, so quoting the wrong one is a choice
someone made rather than an accident the format allowed.

WHAT `ci-census.py` OWNS AND WHAT THIS OWNS
-------------------------------------------
`ci-census.py` answers *did every declared suite run*.  It is the arbiter of
coverage and this file does not restate any of its counts.  This file answers
*how long the suite side took*, which the census does not measure.  They read
the same runs and share no number.

THE SERIES IS DERIVED, NOT MAINTAINED
-------------------------------------
`CI-5` sat at n=5 for three segments while seven new points were written into
`LOG.md` and never into the owner.  A hand-maintained list has exactly that
failure mode.  `citime record` writes rows into `tools/ci-suite-cost.tsv` from
`gh`, `citime stats` recomputes n and the band from the file, and
`citime check` asks GitHub which runs have no row here -- so a missed segment
is a red line rather than a number that quietly stops moving.

CONTROLS
--------
Every one of these is a claim the tool would otherwise be making silently.

  A1  a step missing either timestamp REFUSES the row.  Treating it as zero
      would shorten a job and look like a fast suite.
  A2  a run in which the `apt` rule fires zero times is REPORTED, not given
      `suite_cost = exec`.  A rule that cannot fire proves nothing.
  A3  the loose rule -- substring `apt` -- is evaluated alongside the strict
      one and its extra hits are PRINTED BY NAME.  On this repository there are
      SIX and the tool prints all six: `capture dir`, `merge the captures`,
      `replay-capture mutation suite`, `replay-capture self-test`,
      `test-console-capture` and `test-console-capture-mutants` -- the word
      *capture* contains *apt*.  The reason the rule is written strictly
      belongs in the output, where it is checked, and not only in a comment.

      🔴 *This paragraph said FOUR until 2026-09-06, naming the first four, and
      the sentence began "On this repository they are".  It did not: those four
      are the names in `_fixture_normal()` below, and the two missing ones are
      real steps of the real `instruments` job.  The tool has printed all six
      on every run; the docstring enumerated the fixture and called it the
      repository.  Re-derived by running `record` against five runs and reading
      the A3 line, which is identical on all five.*
  A4  the set of job names is recorded per row, and `stats` refuses to pool
      rows whose job sets differ.  A series that silently spans two CI shapes
      is not one population.
  A5  a job whose conclusion is not `success` refuses the row.  A failed job
      stopped early, so its duration is not a cost.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

TSV_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "ci-suite-cost.tsv")

COLUMNS = ["run_id", "created_utc", "sha7", "jobs",
           "text_s", "lint_s", "lint_apt_s",
           "instr_s", "instr_apt_s", "suite_cost_s", "census_s"]

# The rule.  It is here, once, and every reader of this file gets the same one.
def is_apt(step_name):
    """A package-install step.  Name equality, or a `Run sudo apt-get` prefix.

    NOT a substring test -- see A3 in the module docstring."""
    return step_name == "apt" or step_name.startswith("Run sudo apt-get")


def is_apt_loose(step_name):
    """The wrong rule, kept so A3 can show what it would have caught."""
    return "apt" in step_name.lower()


class Refused(Exception):
    """A row that must not be written, with the control that refused it."""


def _parse(ts):
    if not ts:
        return None
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def job_costs(job):
    """(exec_s, apt_s, apt_n, loose_extra_names) for one job.  Raises Refused."""
    name = job.get("name", "?")
    if job.get("conclusion") != "success":                      # A5
        raise Refused("A5 job %r conclusion=%r" % (name, job.get("conclusion")))
    total = apt_s = 0.0
    apt_n = 0
    loose_extra = []
    for st in job.get("steps", []):
        a, b = _parse(st.get("startedAt")), _parse(st.get("completedAt"))
        if a is None or b is None:                              # A1
            raise Refused("A1 job %r step %r missing a timestamp"
                          % (name, st.get("name")))
        d = (b - a).total_seconds()
        total += d
        sn = st.get("name", "")
        if is_apt(sn):
            apt_s += d
            apt_n += 1
        elif is_apt_loose(sn):
            loose_extra.append(sn)
    return total, apt_s, apt_n, loose_extra


def run_row(data):
    """One TSV row (dict) from a `gh run view --json jobs,...` payload."""
    jobs = {j["name"]: j for j in data.get("jobs", [])}
    row = {"run_id": str(data["databaseId"]),
           "created_utc": data.get("createdAt", ""),
           "sha7": (data.get("headSha") or "")[:7],
           "jobs": ",".join(sorted(jobs))}
    apt_total_n = 0
    loose_extra = []
    per = {}
    for jn, job in jobs.items():
        e, a, n, extra = job_costs(job)
        per[jn] = (e, a)
        apt_total_n += n
        loose_extra.extend(extra)
    if apt_total_n == 0:                                        # A2
        raise Refused("A2 the apt rule fired zero times in run %s"
                      % row["run_id"])
    row["text_s"] = "%.0f" % per.get("text", (float("nan"),))[0]
    row["lint_s"] = "%.0f" % per.get("lint", (float("nan"),))[0]
    row["lint_apt_s"] = "%.0f" % per.get("lint", (0, float("nan")))[1]
    ie, ia = per.get("instruments", (float("nan"), float("nan")))
    row["instr_s"] = "%.0f" % ie
    row["instr_apt_s"] = "%.0f" % ia
    row["suite_cost_s"] = "%.0f" % (ie - ia)
    row["census_s"] = "%.0f" % per.get("census", (float("nan"),))[0]
    return row, sorted(set(loose_extra))


# --------------------------------------------------------------- tsv i/o
def read_tsv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if parts == COLUMNS:            # the column header, not a row
                continue
            if len(parts) != len(COLUMNS):
                raise SystemExit("citime: %s: %d columns, want %d: %r"
                                 % (path, len(parts), len(COLUMNS), line[:80]))
            rows.append(dict(zip(COLUMNS, parts)))
    return rows


HEADER = """\
# ci-suite-cost.tsv -- one row per CI run, written by tools/citime.py.
#
# suite_cost_s = instr_s - instr_apt_s, and it is the ONLY column PROGRESS.md's
# CI-5 quotes.  instr_s contains the package install and must never be quoted
# on its own; lint_apt_s is here because a run's apt is NOT the instruments
# job's apt, and writing the two side by side without saying which is which is
# the mistake this file exists to make impossible.
#
# Regenerate a row:  tools/citime.py record <run-id>
# Recompute the band: tools/citime.py stats
# Find missing runs:  tools/citime.py check --last 40
#
"""


def write_tsv(path, rows):
    rows = sorted(rows, key=lambda r: r["created_utc"])
    body = "".join("\t".join(r[c] for c in COLUMNS) + "\n" for r in rows)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(HEADER + "\t".join(COLUMNS) + "\n" + body)
    os.replace(tmp, path)


def _gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("citime: gh %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return json.loads(r.stdout)


# ------------------------------------------------------------- subcommands
def cmd_record(a):
    ids = list(a.runs)
    if a.last:
        listing = _gh(["run", "list", "--limit", str(a.last),
                       "--json", "databaseId,conclusion"])
        ids += [str(r["databaseId"]) for r in listing
                if r["conclusion"] == "success"]
    if not ids:
        raise SystemExit("citime record: give run ids or --last N")
    existing = {r["run_id"]: r for r in read_tsv(a.tsv)}
    added = skipped = refused = 0
    for rid in ids:
        if rid in existing and not a.force:
            skipped += 1
            continue
        data = _gh(["run", "view", rid,
                    "--json", "jobs,databaseId,headSha,createdAt"])
        try:
            row, extra = run_row(data)
        except Refused as e:
            print("  refused %s: %s" % (rid, e))
            refused += 1
            continue
        existing[rid] = row
        added += 1
        print("  %s  %s  suite_cost=%s  (instr %s - apt %s; lint apt %s)"
              % (rid, row["sha7"], row["suite_cost_s"],
                 row["instr_s"], row["instr_apt_s"], row["lint_apt_s"]))
        if extra:                                               # A3
            print("     A3 substring rule would also have caught: %s"
                  % "; ".join(extra))
    write_tsv(a.tsv, list(existing.values()))
    print("recorded %d, already present %d, refused %d -> %s"
          % (added, skipped, refused, a.tsv))
    return 0


def band(vals):
    lo, hi = min(vals), max(vals)
    mid = (lo + hi) / 2.0
    half = (hi - lo) / 2.0
    return lo, hi, hi - lo, mid, half, (100.0 * half / mid if mid else float("nan"))


#: The changepoint `CI-5` sits on, and the convention for the row that lands ON
#: it.  Both halves are here because the second one was written down nowhere and
#: cost a disagreement inside one segment: 2026-09-06, one hand sliced with `>`
#: and got n=32 where the owner said 29+4=33.  The permutation test that located
#: this point put the changepoint run at the HEAD of the right segment (left
#: n=16 mean 543.75, right n=28), so the slice is `>=`.  A boundary convention
#: that lives in prose is the same defect as an `apt` rule that lives in prose.
CHANGEPOINT = "2026-09-01T14:27:11Z"


def cmd_stats(a):
    rows = read_tsv(a.tsv)
    if not rows:
        raise SystemExit("citime stats: no rows in %s" % a.tsv)
    if a.since:
        cut = CHANGEPOINT if a.since == "changepoint" else a.since
        before = [r for r in rows if r["created_utc"] < cut]
        rows = [r for r in rows if r["created_utc"] >= cut]
        print("--since %s: %d row(s) at or after it, %d before "
              "(the row ON the boundary is the FIRST of this segment)"
              % (cut, len(rows), len(before)))
        if not rows:
            raise SystemExit("citime stats: no rows at or after %s" % cut)
    groups = {}
    for r in rows:
        groups.setdefault(r["jobs"], []).append(r)
    if len(groups) > 1 and not a.pool:                          # A4
        print("A4: %d different job sets in this file; they are not one "
              "population. Reporting each separately (--pool to override)."
              % len(groups))
    rc = 0
    for jobs, grp in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        vals = [int(r["suite_cost_s"]) for r in grp]
        lo, hi, rng, mid, half, pct = band(vals)
        print()
        print("job set: %s" % jobs)
        print("  n = %d   %s" % (len(vals), " ".join(str(v) for v in vals)))
        print("  range %d..%d = %d s   midpoint %.1f   half-width %.1f   +/- %.2f %%"
              % (lo, hi, rng, mid, half, pct))
        print("  mean %.2f   median %.1f"
              % (sum(vals) / len(vals), sorted(vals)[len(vals) // 2]))
        if len(vals) >= 4:
            n0 = min(5, len(vals) - 1)
            first, rest = vals[:n0], vals[n0:]
            inside = all(min(first) <= v <= max(first) for v in rest)
            m = len(rest)
            p = (n0 * (n0 - 1)) / float((n0 + m) * (n0 + m - 1))
            print("  first %d span %d..%d; all %d later points inside: %s"
                  % (n0, min(first), max(first), m, "YES" if inside else "no"))
            print("  under exchangeability with no ties, P(that) = "
                  "%d*%d/(%d*%d) = %.4f -- ties only raise it, so this is a "
                  "LOWER bound on the p-value" % (n0, n0 - 1, n0 + m, n0 + m - 1, p))
    return rc


def cmd_check(a):
    rows = {r["run_id"] for r in read_tsv(a.tsv)}
    listing = _gh(["run", "list", "--limit", str(a.last),
                   "--json", "databaseId,conclusion,createdAt,headSha"])
    missing = [r for r in listing
               if r["conclusion"] == "success" and str(r["databaseId"]) not in rows]
    print("%d successful runs in the last %d; %d have a row here; %d missing"
          % (sum(1 for r in listing if r["conclusion"] == "success"),
             a.last, len(rows), len(missing)))
    for r in missing:
        print("  MISSING %s  %s  %s"
              % (r["databaseId"], r["createdAt"], r["headSha"][:7]))
    return 1 if missing else 0


def cmd_derive(a):
    for p in a.json_files:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        try:
            row, extra = run_row(data)
        except Refused as e:
            print("%s: REFUSED %s" % (p, e))
            continue
        print("%s  %s  exec=%s  apt=%s  exec-apt=%s  (lint apt %s)"
              % (row["run_id"], row["sha7"], row["instr_s"],
                 row["instr_apt_s"], row["suite_cost_s"], row["lint_apt_s"]))
        if extra:
            print("   A3 substring rule would also have caught: %s" % "; ".join(extra))
    return 0


# ------------------------------------------------------------------ fixtures
def _job(name, steps, conclusion="success"):
    """Steps laid back to back from a fixed epoch, so every duration is exact."""
    out = []
    cur = datetime(2026, 9, 6, 8, 0, 0)
    for sname, dur in steps:
        end = cur + timedelta(seconds=dur)
        out.append({"name": sname,
                    "startedAt": cur.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completedAt": end.strftime("%Y-%m-%dT%H:%M:%SZ")})
        cur = end
    return {"name": name, "conclusion": conclusion, "steps": out}


def _run(rid, jobs, sha="abcdef1234567"):
    return {"databaseId": int(rid), "headSha": sha,
            "createdAt": "2026-09-06T08:00:00Z", "jobs": jobs}


def _fixture_normal():
    return _run(1, [
        _job("instruments", [("Set up job", 1), ("apt", 16),
                             ("capture dir", 0), ("suiteA", 500), ("suiteB", 33)]),
        _job("text", [("capture dir", 0), ("spec-check", 4),
                      ("replay-capture self-test", 0), ("suiteC", 137)]),
        _job("lint", [("Run sudo apt-get update -qq && sudo apt-get install -y -qq shellcheck", 6),
                      ("shellcheck", 8)]),
        _job("census", [("merge the captures", 0), ("census", 4)]),
    ])


# ------------------------------------------------------------------ selftest
def selftest():
    ok, bad = [], []

    def case(cid, what, fn):
        try:
            fn()
        except AssertionError as e:
            bad.append((cid, what, str(e)))
        except Exception as e:                                   # noqa: BLE001
            bad.append((cid, what, "%s: %s" % (type(e).__name__, e)))
        else:
            ok.append((cid, what))

    # P1 -- the arithmetic, on a fixture whose answer is known by hand.
    def p1():
        row, _ = run_row(_fixture_normal())
        assert row["instr_s"] == "550", row
        assert row["instr_apt_s"] == "16", row
        assert row["suite_cost_s"] == "534", row
        assert row["text_s"] == "141", row
        assert row["census_s"] == "4", row
    case("P1", "exec / apt / exec-apt on a hand-computed fixture", p1)

    # P2 -- lint's apt is recorded SEPARATELY and is not folded into the cost.
    def p2():
        row, _ = run_row(_fixture_normal())
        assert row["lint_apt_s"] == "6", row
        assert row["lint_s"] == "14", row
        # the cost must not have moved because lint has an apt step
        assert row["suite_cost_s"] == "534", row
    case("P2", "lint's apt is a separate column and does not enter suite_cost", p2)

    # P3 -- A3: the substring rule catches `capture`, the strict rule does not.
    def p3():
        _, extra = run_row(_fixture_normal())
        assert "capture dir" in extra, extra
        assert "merge the captures" in extra, extra
        assert "replay-capture self-test" in extra, extra
        assert not any(is_apt(n) for n in extra), extra
    case("P3", "A3 names what a substring rule would wrongly call apt", p3)

    # P4 -- A1: a null timestamp refuses the row rather than counting zero.
    def p4():
        d = _fixture_normal()
        d["jobs"][0]["steps"][3]["completedAt"] = None
        try:
            run_row(d)
        except Refused as e:
            assert "A1" in str(e), e
        else:
            raise AssertionError("A1 did not fire on a null timestamp")
    case("P4", "A1 refuses a step with a missing timestamp", p4)

    # P5 -- A2: a run with no apt step at all is refused, not silently costed.
    def p5():
        d = _fixture_normal()
        for j in d["jobs"]:
            j["steps"] = [s for s in j["steps"] if not is_apt(s["name"])]
        try:
            run_row(d)
        except Refused as e:
            assert "A2" in str(e), e
        else:
            raise AssertionError("A2 did not fire on a run with no apt step")
    case("P5", "A2 refuses a run in which the apt rule never fires", p5)

    # P6 -- A5: a failed job refuses the row.
    def p6():
        d = _fixture_normal()
        d["jobs"][0]["conclusion"] = "failure"
        try:
            run_row(d)
        except Refused as e:
            assert "A5" in str(e), e
        else:
            raise AssertionError("A5 did not fire on a failed job")
    case("P6", "A5 refuses a row from a job that did not succeed", p6)

    # P7 -- the band arithmetic, against a series computed by hand.
    def p7():
        vals = [536, 537, 533, 533, 523, 532, 529, 532, 533,
                532, 530, 525, 534, 533, 534, 536, 535]
        lo, hi, rng, mid, half, pct = band(vals)
        assert (lo, hi, rng) == (523, 537, 14), (lo, hi, rng)
        assert abs(mid - 530.0) < 1e-9, mid
        assert abs(half - 7.0) < 1e-9, half
        assert abs(pct - 1.320754716981132) < 1e-9, pct
    case("P7", "band arithmetic on the n=17 series", p7)

    # P8 -- tsv round trip, and the refusal on a wrong column count.
    def p8():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.tsv")
            row, _ = run_row(_fixture_normal())
            write_tsv(p, [row])
            back = read_tsv(p)
            assert len(back) == 1 and back[0]["suite_cost_s"] == "534", back
            with open(p, "a", encoding="utf-8") as fh:
                fh.write("too\tfew\n")
            try:
                read_tsv(p)
            except SystemExit as e:
                assert "columns" in str(e), e
            else:
                raise AssertionError("read_tsv accepted a short row")
    case("P8", "tsv round trip, and a short row is refused", p8)

    # P9 -- NEGATIVE CONTROL.  The suite above must be able to FAIL.  If the
    # rule is replaced by one that matches nothing, P1/P2/P5 must break.  A
    # green suite whose rule can be gutted without noticing is not a check.
    def p9():
        global is_apt
        keep = is_apt
        try:
            is_apt = lambda n: False                             # noqa: E731
            broke = False
            try:
                run_row(_fixture_normal())
            except Refused as e:
                broke = "A2" in str(e)
            assert broke, "gutting the apt rule did not break run_row"
        finally:
            is_apt = keep
        # and the real rule must still work afterwards
        row, _ = run_row(_fixture_normal())
        assert row["suite_cost_s"] == "534", row
    case("P9", "negative control: gutting the apt rule breaks the suite", p9)

    # P10 -- the boundary convention, which is the whole reason --since exists.
    # A row whose created_utc EQUALS the changepoint belongs to the segment
    # that STARTS there. Nothing recorded that until 2026-09-06, and slicing it
    # the other way gives n=32 where the owner's own figures give 33 -- inside
    # one segment, from the same file.
    def p10():
        rows = [{"created_utc": "2026-09-01T14:00:00Z", "suite_cost_s": "548"},
                {"created_utc": CHANGEPOINT,            "suite_cost_s": "529"},
                {"created_utc": "2026-09-01T15:00:00Z", "suite_cost_s": "531"}]
        after = [r for r in rows if r["created_utc"] >= CHANGEPOINT]
        before = [r for r in rows if r["created_utc"] < CHANGEPOINT]
        assert len(after) == 2, after
        assert len(before) == 1, before
        assert after[0]["suite_cost_s"] == "529", after
        # and the wrong convention, stated so it cannot be re-chosen silently
        wrong = [r for r in rows if r["created_utc"] > CHANGEPOINT]
        assert len(wrong) == 1, wrong
    case("P10", "the changepoint row is the FIRST of the right segment", p10)

    for cid, what in ok:
        print("  ok   %-4s %s" % (cid, what))
    for cid, what, why in bad:
        print("  FAIL %-4s %s -- %s" % (cid, what, why))
    print("RESULT: %d/%d" % (len(ok), len(ok) + len(bad)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tsv", default=TSV_DEFAULT)
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("record", help="fetch runs with gh and add rows")
    r.add_argument("runs", nargs="*")
    r.add_argument("--last", type=int, default=0)
    r.add_argument("--force", action="store_true", help="rewrite an existing row")
    r.set_defaults(fn=cmd_record)

    s = sub.add_parser("stats", help="recompute n and the band from the tsv")
    s.add_argument("--since", default=None,
                   help="an ISO timestamp, or the word `changepoint` for "
                        "CI-5's own (%s). The row ON the boundary belongs to "
                        "the segment that STARTS there." % CHANGEPOINT)
    s.add_argument("--pool", action="store_true",
                   help="pool rows whose job sets differ (A4 says do not)")
    s.set_defaults(fn=cmd_stats)

    c = sub.add_parser("check", help="runs on GitHub with no row here")
    c.add_argument("--last", type=int, default=40)
    c.set_defaults(fn=cmd_check)

    d = sub.add_parser("derive", help="print rows from saved gh json, no network")
    d.add_argument("json_files", nargs="+")
    d.set_defaults(fn=cmd_derive)

    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not a.cmd:
        ap.print_help()
        return 2
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
