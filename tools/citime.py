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
  A5  a job whose conclusion is not `success` refuses the ROW -- the whole
      row, not that job's column.

      🔴 *This read "a failed job stopped early, so its duration is not a
      cost" until 2026-09-07, and that sentence describes a case A5 is not
      deciding.*  量, on `34040804067`, by a `jq` re-derivation that does not
      share this file's code: the job that failed is `text`, `census` was
      **skipped**, and `instruments` ran 16 of 16 steps to success with its
      own `exec - apt` a complete **535** -- inside the band, and discarded.
      Nothing there stopped early.  The row is refused because **a row is a
      unit**: `text_s` and `census_s` would otherwise carry a truncated
      duration in a column that reads as a duration, which is the `exec`
      mistake this file was written to end.

      The behaviour is deliberately unchanged.  Relaxing A5 to admit a red
      run's `instruments` needs a per-cell validity marker, which is a larger
      format change than one data point is worth.  ⚠️  **Whether excluding
      red runs biases the band is NOT answered**: the one exclusion measured
      sat inside the band, n=1.
  A6  a run holding SOME BUT NOT ALL of the `BIG3` steps REFUSES the row.  A
      run holding none of them writes `-`.  The distinction is the column's
      reason for existing: two of the three sum to a smaller number than three
      do, and a smaller number in a cost column reads as a suite that got
      faster rather than as a suite that stopped running.  A shape with no
      BIG3 at all is A4's business -- a different population -- and not a
      defect in that run.
  A7  `stats` prints BIG3's SHARE of `suite_cost` on every run, with a floor,
      and exits non-zero below it.  BIG3 is quoted instead of the total
      because 量 2026-09-07 those three steps carry 94.4 % of the cost; if
      that stops being true the reason has expired, and a hardcoded set whose
      justification is only in a comment is the `A3` mistake again.  The floor
      itself is **推** (85 %, chosen with headroom), and P14 asserts it is a
      value a set can actually fall below.

  A8  a partition whose `big3_s` half-width exceeds a ceiling is REFUSED.
      A band is the claim *these rows are one population*, and a partition
      wide enough to hold two is that claim being false.  The ceiling is
      **推** (5 %) and the headroom is measured on BOTH sides, which `A7`'s
      floor is not: 量 2026-09-09, the three declared partitions measure
      0.996 / 0.699 / 0.787 % and the pooled view measures 31.778 %, so 5 % is
      5.0x above the worst honest partition and 6.4x below the dishonest one.
  A9  the same population is searched for the single split that best separates
      it, and a separation above a floor is REFUSED **with the row named**.
      A8 measures spread; A9 measures structure, and neither implies the
      other: a partition with one wild runner is wide with no step, and a step
      of 15 s on a 950 s base is a step inside a 1 % band.
      🔴 **A9's limit is stated rather than tuned away.**  量 2026-09-09, on
      everything before the second changepoint: `CHANGEPOINTS[0]` -- which a
      permutation test located in 2026-09-06 -- ranks **1 of 71** on
      `suite_cost_s` at **1.65 sd** and **2 of 71** on `big3_s` at **0.87 sd**,
      while a clean partition elsewhere in the same file reaches **3.58 sd**.
      **A9 could not have found it at any floor that does not fire on
      everything.**  It is a coarse instrument that runs on every `stats
      --since`, where the fine one ran once; that is the trade, and lowering
      the floor to reach CP1 would be repairing the instrument to agree with a
      result already held.

🔴  WHY `CHANGEPOINT` BECAME `CHANGEPOINTS`, WHICH IS THIS FILE'S OWN LESSON
----------------------------------------------------------------------------
量 2026-09-09 (fiftieth segment).  The comment above `BIG3` records the
2026-09-08 step in full -- `test-console-capture` 46 -> 59 cases and its mutant
suite 25 -> 39 mutants, 1,150 -> 2,301 units of work = 2.001x, `big3_s`
503 -> 954, confirmed against the runs' own wall clock to 6.9 %.  It was seen,
attributed and cross-checked.  **And `CHANGEPOINT`, twenty lines below it, was
not moved.**  So `stats --since changepoint` -- the command this file exists to
make `CI-5` quote -- pooled a 502 population with a 954 one and printed
`+/- 31.778 %` over n=69.  The two segments that needed the band typed
`--since 2026-09-08T20:43:13Z` by hand instead, which is the boundary back in
prose: exactly the state `P10` and `--since changepoint` were written to end.

**A rule as a hardcoded constant drifts the same way a rule in prose does.**
It is the fourth instance of one shape in this one file -- the `apt` rule, the
`A3` docstring, the BIG3 rule, and now the boundary -- and the first three were
each found by re-deriving rather than re-reading.  A8 and A9 are that
re-derivation as code: the tool now refuses to report a band over a population
it can see is two.

⚠️  WHAT `big3_s` DOES NOT SETTLE
--------------------------------
Why `test-spec-check-mutants` swings 12 s is **not answered**: 量 2026-09-07
at the desk, same commit, loadavg 0.00, three runs gave 36.14 / 42.04 / 48.77 s
(+/- 15.0 %), and every mechanism proposed so far has been declined by its own
control: parallelism twice (`--jobs 1` jitters just as far in absolute seconds,
and a second `--jobs 8` suite is the TIGHTEST step on CI at +/- 0.7 %), `/tmp`
accumulation (0 residual directories), and filesystem -- 量 2026-09-07, the
desk runs suites with the repo on 9p while CI does not, and 40 reads of one
file take 111-121 ms there against 40-43 ms on ext4, but the RELATIVE spread is
+/- 4.3 % against +/- 3.6 %, so it explains an absolute difference and not a
+/- 15 % swing.  Excluding the step from the quoted band is a decision about
what to quote, not an explanation, and this file does not pretend otherwise.
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
           "instr_s", "instr_apt_s", "suite_cost_s", "big3_s", "census_s"]

#: The three `instruments` steps `CI-5` quotes INSTEAD of `suite_cost_s`.
#:
#: 量 2026-09-07, per-step over every recorded run: these three carry roughly
#: **94 %** of the cost, their range is markedly tighter than the total's, and
#: the other twelve steps carry the rest of the cost with a WIDER range of
#: their own.  `suite_cost`'s outer edge is therefore mostly integer-second
#: quantisation on short steps -- fifteen terms each rounded to a whole second.
#:
#: 🔴 No band is written here, on purpose.  A first draft of this comment said
#: *"53 % of the band's width"*, which is `1 - BIG3_range/suite_cost_range` and
#: treats band widths as additive shares of one total.  They are not: on the
#: post-changepoint slice the three ranges are 7, 11 and 16 seconds, and
#: 7 + 11 = 18.  It also called `497..504` the 51-run figure when that is the
#: post-changepoint slice; all runs pooled gave `497..507`.  🔴 **And that
#: figure died on 2026-09-09**: run 34276448280 is **954**, so pooled is now
#: `497..954` (+-31.50 %) over 75 rows.  It is not drift -- it is this
#: repository's own change, fully attributable: `test-console-capture` went
#: 46 -> 59 cases and its mutant suite 25 -> 39 mutants, and that suite's work
#: is cases x mutants, 1,150 -> 2,301, a factor of 2.001.  `test-deskchan` did
#: not grow (60.19 s, desk sweep), and (954-60)/(502-60) = 2.02 against a
#: predicted 1.97.  🟢 Confirmed on the wall clock by a second source that
#: shares no code with this ledger, and the comparison is within ONE run:
#: 34276448280 took 17m40s = 1,060 s where 34260019516 took 9m38s = 578 s,
#: a wall difference of **482 s** against this ledger's **451 s** -- 31 s
#: apart, **6.9 %**, and the residual is the rest of the pipeline, which was
#: never claimed constant.  🔴 The first version of this comment said
#: *456 s against 452 s, 0.9 %*, and that paired the WALL CLOCK of one run
#: (34278435291) with the BIG3 of a DIFFERENT one (34276448280) because both
#: were 'this segment's'.  A number is only ever confirmed by another number
#: from the SAME row.  **Run
#: `stats` --
#: it prints both bands, and A7 prints the share.**
#:
#: 🔴 The set is HARDCODED rather than derived per run, on purpose.  A set
#: chosen from each run's own data is a different population per row, which is
#: the thing `A4` refuses.  `A7` reports the share on every `stats` run, so the
#: reason this set was chosen is CHECKED each time instead of being trusted
#: from this comment -- which is the `A3` docstring's mistake, one file up.
BIG3 = ("test-console-capture-mutants", "test-console-capture", "test-deskchan")

#: `A7`'s floor.  **推** -- 94.4 % is the measurement, 85 % is a choice with
#: headroom.  Below it, the reason `CI-5` quotes BIG3 rather than the total has
#: expired and `stats` says so and exits non-zero.
BIG3_FLOOR_PCT = 85.0

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


def step_seconds(job):
    """name -> summed seconds for one job.

    Repeated names are SUMMED, not overwritten: two steps sharing a name are
    two costs, and a dict that kept the last one would drop the first without
    saying so.  Steps with a missing timestamp are skipped here because `A1`
    in `job_costs` has already refused the whole row by the time this runs --
    every job goes through `job_costs` first.
    """
    out = {}
    for st in job.get("steps", []):
        a, b = _parse(st.get("startedAt")), _parse(st.get("completedAt"))
        if a is None or b is None:
            continue
        n = st.get("name", "")
        out[n] = out.get(n, 0.0) + (b - a).total_seconds()
    return out


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

    # BIG3, and A6.  Three outcomes, and the middle one is the whole point:
    #   all three present -> a number
    #   SOME present      -> REFUSED.  Summing two of the three is smaller than
    #                        summing three, and a smaller number in this column
    #                        reads as a suite that got faster.  Same shape as
    #                        A1: a missing term must not become a quiet zero.
    #   none present      -> "-".  This run's CI shape has no BIG3 at all,
    #                        which is A4's territory, not a defect in the run.
    ij = jobs.get("instruments")
    if ij is None:
        row["big3_s"] = "-"
    else:
        secs = step_seconds(ij)
        present = [n for n in BIG3 if n in secs]
        if not present:
            row["big3_s"] = "-"
        elif len(present) != len(BIG3):                          # A6
            raise Refused(
                "A6 run %s has %d of %d BIG3 steps; missing %s -- a partial "
                "sum reads as a faster suite"
                % (row["run_id"], len(present), len(BIG3),
                   ", ".join(sorted(set(BIG3) - set(present)))))
        else:
            row["big3_s"] = "%.0f" % sum(secs[n] for n in BIG3)
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
# suite_cost_s = instr_s - instr_apt_s.  instr_s contains the package install
# and must never be quoted on its own; lint_apt_s is here because a run's apt
# is NOT the instruments job's apt, and writing the two side by side without
# saying which is which is the mistake this file exists to make impossible.
#
# big3_s is the sum of the three instruments steps that carry 94.4 % of the
# cost, and it is what PROGRESS.md's CI-5 quotes.  suite_cost_s is the coarse
# sieve: 量 2026-09-07, twelve short steps carry 5.6 % of the cost and 53 % of
# suite_cost's band width, so its outer edge is mostly integer-second
# quantisation.  "-" means this run's CI shape has no BIG3 step at all; a run
# with SOME of them is refused by A6 rather than written down short.
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
        print("  %s  %s  BIG3=%s  suite_cost=%s  (instr %s - apt %s; lint apt %s)"
              % (rid, row["sha7"], row["big3_s"], row["suite_cost_s"],
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
#: 🔄 **A tuple since 2026-09-09, and the reason is in the docstring.**  One
#: string could not describe a series with two steps in it, and the second step
#: sat undeclared for a day while the comment above `BIG3` described it in
#: detail.  Oldest first.  Each entry is (timestamp, the quantity it was
#: LOCATED on, one line of evidence) -- the middle field because
#: `CHANGEPOINTS[0]` was located on `suite_cost_s` and is being applied to
#: `big3_s`, a column that did not exist when it was chosen.
CHANGEPOINTS = (
    ("2026-09-01T14:27:11Z", "suite_cost_s",
     "permutation test 2026-09-06; left n=16 mean 543.75, right n=28. "
     "量 2026-09-09: on big3_s this boundary is a 1.97 s mean shift "
     "(503.81 -> 501.84) against within-partition sd 3.49 and 1.80, so it is a "
     "suite_cost changepoint that big3_s barely sees -- A9 ranks it 2 of 71 "
     "at 0.87 sd and would not have found it"),
    ("2026-09-08T20:43:13Z", "big3_s",
     "e79ff63: test-console-capture 46->59 cases, its mutant suite 25->39 "
     "mutants, cases x mutants 1,150 -> 2,301 = 2.001x; big3_s 503 -> 954. "
     "量 2026-09-09: the largest adjacent jump in the whole series at 451 s "
     "against a second-largest of 13 s (34.7x), and A9 locates this exact row "
     "at 165.01 sd from either pooled view"),
)

#: The LATEST declared boundary -- the segment the series is currently in, and
#: what `--since changepoint` means.  The old single-string name is kept
#: because `P10` pins a convention about it and the convention did not change.
CHANGEPOINT = CHANGEPOINTS[-1][0]

#: `A8`'s ceiling on a partition's `big3_s` half-width, in percent.  **推**,
#: with headroom measured on both sides -- see A8 in the module docstring.
#: It governs `big3_s` and not `suite_cost_s`, because `suite_cost_s` is
#: already printed under the label *coarse sieve -- do not quote as the band*
#: and a check on a quantity nobody quotes is decoration.
PARTITION_MAX_PCT = 5.0

#: `A9`'s floor on the separation statistic, in pooled standard deviations.
#: **推**.  量 2026-09-09: the worst declared partition reaches 0.89 sd and the
#: weakest pooled view reaches 165.01, so 8.0 is 9.0x above one and 20.6x below
#: the other.
PARTITION_MIN_SEP_SD = 8.0


def separation(vals):
    """The single split that best separates `vals`, in pooled sd.

    Returns `(statistic, index)` where `index` is the FIRST element of the
    right segment -- `P10`'s convention, reused rather than restated.  Fewer
    than four points returns `(0.0, None)`: a split of three is one point
    against two, and this instrument makes no claim there.
    """
    n = len(vals)
    if n < 4:
        return 0.0, None
    best, bi = 0.0, None
    for k in range(2, n - 1):
        left, right = vals[:k], vals[k:]
        ml = sum(left) / float(len(left))
        mr = sum(right) / float(len(right))
        ss = (sum((v - ml) ** 2 for v in left) +
              sum((v - mr) ** 2 for v in right))
        sd = (ss / (n - 2)) ** 0.5
        if sd <= 1e-9:
            s = 0.0 if ml == mr else float("inf")
        else:
            s = abs(ml - mr) / sd
        if s > best:
            best, bi = s, k
    return best, bi


def audit_partition(vals, rows, quoted, indent="    ", quiet=False):
    """A8 and A9 on one population.  Returns (rc, fired) and prints its verdict.

    `quoted` is False for the bare pooled sieve, which the caller has already
    LABELLED as not a band.  Firing there on every invocation would make a red
    line that is always present, and this repository has measured what that
    does to a reader: *a local sweep that ends in two reds every time trains a
    reader to ignore reds*.  The line still prints; only the exit code is
    withheld.
    """
    say = (lambda *_: None) if quiet else print
    if len(vals) < 2:
        say("%sA8/A9: n=%d, nothing to partition" % (indent, len(vals)))
        return 0, False
    lo, hi = min(vals), max(vals)
    mid = (lo + hi) / 2.0
    pct = (100.0 * (hi - lo) / 2.0 / mid) if mid else float("nan")
    sep, idx = separation(vals)
    a8 = pct > PARTITION_MAX_PCT
    a9 = idx is not None and sep > PARTITION_MIN_SEP_SD
    where = ""
    if idx is not None and rows is not None and idx < len(rows):
        where = " at %s %s" % (rows[idx]["created_utc"], rows[idx]["sha7"])
    say("%sA8 half-width %.3f %% (ceiling %.1f) -- %s"
        % (indent, pct, PARTITION_MAX_PCT,
           "FIRED: this is not one population" if a8 else "ok"))
    say("%sA9 separation %.2f sd (floor %.1f)%s -- %s"
        % (indent, sep, PARTITION_MIN_SEP_SD, where,
           "FIRED: declare this boundary or explain it" if a9 else "ok"))
    fired = a8 or a9
    if fired and not quoted:
        say("%s   (pooled sieve: already labelled, so no exit code)" % indent)
    return (1 if (fired and quoted) else 0), fired


def cmd_stats(a):
    rows = read_tsv(a.tsv)
    if not rows:
        raise SystemExit("citime stats: no rows in %s" % a.tsv)
    if a.since:
        cut = CHANGEPOINTS[-1][0] if a.since == "changepoint" else a.since
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

        # ---- BIG3 first, because it is the one CI-5 quotes -----------------
        b3rows = [r for r in grp if r["big3_s"] != "-"]
        # A tool reporting 0 is making a claim, so this line prints every time.
        print("  BIG3 = %s" % " + ".join(BIG3))
        print("    rows with no BIG3 value: %d of %d" % (len(grp) - len(b3rows), len(grp)))
        if b3rows:
            b3 = [int(r["big3_s"]) for r in b3rows]
            l3, h3, r3, m3, hw3, p3 = band(b3)
            print("    n = %d   %s" % (len(b3), " ".join(str(v) for v in b3)))
            print("    range %d..%d = %d s   midpoint %.1f   half-width %.1f   "
                  "+/- %.2f %%" % (l3, h3, r3, m3, hw3, p3))
            print("    mean %.2f   median %.1f"
                  % (sum(b3) / len(b3), sorted(b3)[len(b3) // 2]))
            shares = [100.0 * int(r["big3_s"]) / int(r["suite_cost_s"])
                      for r in b3rows if int(r["suite_cost_s"])]
            if shares:                                           # A7
                slo, shi = min(shares), max(shares)
                over = slo >= BIG3_FLOOR_PCT
                print("    A7 share of suite_cost: %.1f..%.1f %% over %d row(s), "
                      "floor %.0f %% -- %s"
                      % (slo, shi, len(shares), BIG3_FLOOR_PCT,
                         "the set still dominates" if over else
                         "BELOW FLOOR: the reason CI-5 quotes BIG3 has expired"))
                if not over:
                    rc = 1
            # A8/A9.  `--since` is the caller CLAIMING a population; the bare
            # pooled view is not, and the difference is the exit code.
            arc, _ = audit_partition(b3, b3rows, quoted=bool(a.since))
            rc = rc or arc

        # ---- suite_cost second, labelled as what it now is -----------------
        print("  suite_cost (coarse sieve -- do not quote as the band):")
        print("    n = %d   %s" % (len(vals), " ".join(str(v) for v in vals)))
        print("    range %d..%d = %d s   midpoint %.1f   half-width %.1f   "
              "+/- %.2f %%" % (lo, hi, rng, mid, half, pct))
        print("    mean %.2f   median %.1f"
              % (sum(vals) / len(vals), sorted(vals)[len(vals) // 2]))
        if len(vals) >= 4:
            n0 = min(5, len(vals) - 1)
            first, rest = vals[:n0], vals[n0:]
            inside = all(min(first) <= v <= max(first) for v in rest)
            m = len(rest)
            p = (n0 * (n0 - 1)) / float((n0 + m) * (n0 + m - 1))
            print("    first %d span %d..%d; all %d later points inside: %s"
                  % (n0, min(first), max(first), m, "YES" if inside else "no"))
            print("    under exchangeability with no ties, P(that) = "
                  "%d*%d/(%d*%d) = %.4f -- ties only raise it, so this is a "
                  "LOWER bound on the p-value" % (n0, n0 - 1, n0 + m, n0 + m - 1, p))
    return rc


def cmd_segments(a):
    """Every declared partition, audited, with the pooled view as the control.

    The pooled view is printed LAST and deliberately: it is the positive
    control, and a run in which it does NOT fire is red.  A8 and A9 reporting
    clean on three partitions is a claim, and a claim needs a case that shows
    the instrument can still fail on this file today.
    """
    rows = read_tsv(a.tsv)
    if not rows:
        raise SystemExit("citime segments: no rows in %s" % a.tsv)
    rows.sort(key=lambda r: r["created_utc"])
    rows = [r for r in rows if r["big3_s"] not in ("", "-")]
    print("quantity: big3_s   (A8 and A9 govern the column CI-5 quotes)")
    print("declared changepoints: %d" % len(CHANGEPOINTS))
    for i, (ts, on, why) in enumerate(CHANGEPOINTS):
        print("  [%d] %s  located on %-13s %s" % (i, ts, on, why[:90]))
    bounds = [c[0] for c in CHANGEPOINTS]
    edges = [None] + bounds + [None]
    print()
    print("partitions (the row ON a boundary is the FIRST of its segment):")
    a8_bad, a9_bad, empty = [], [], []
    npart = 0
    for i in range(len(edges) - 1):
        a0, a1 = edges[i], edges[i + 1]
        grp = [r for r in rows
               if (a0 is None or r["created_utc"] >= a0)
               and (a1 is None or r["created_utc"] < a1)]
        label = "%s .. %s" % (a0 or "(start)", a1 or "(now)")
        npart += 1
        print("  %s   n=%d" % (label, len(grp)))
        if not grp:
            print("    EMPTY -- a declared boundary with no rows on one side "
                  "is a boundary this file cannot support")
            empty.append(label)
            continue
        vals = [int(r["big3_s"]) for r in grp]
        lo, hi = min(vals), max(vals)
        mid = (lo + hi) / 2.0
        pct = (100.0 * (hi - lo) / 2.0 / mid) if mid else float("nan")
        sep, idx = separation(vals)
        audit_partition(vals, grp, quoted=True)
        if pct > PARTITION_MAX_PCT:
            a8_bad.append("%s (%.3f %%)" % (label, pct))
        if idx is not None and sep > PARTITION_MIN_SEP_SD:
            a9_bad.append("%s (%.2f sd at %s %s)"
                          % (label, sep, grp[idx]["created_utc"],
                             grp[idx]["sha7"]))
    print()
    print("positive control -- the whole file pooled MUST fire, or A8 and A9")
    print("cannot fail on this corpus and the greens above prove nothing.")
    print("every control line is prefixed, so a grep for FIRED on a green run")
    print("lands here and knows it:")
    vals = [int(r["big3_s"]) for r in rows]
    _, fired = audit_partition(vals, rows, quoted=False,
                               indent="    [control] ")
    print()

    # The three cases.  The COUNT does not move when a changepoint is
    # declared -- one more partition is one more line above, not one more
    # case -- so `ci-expected.tsv` does not have to be edited to declare a
    # boundary, and a CENSUS-MISMATCH cannot become the cost of doing the
    # right thing.
    ok, bad = [], []
    (ok if not (a8_bad or empty) else bad).append(
        ("S1", "every declared partition is inside A8's ceiling (%d of %d)"
         % (npart - len(a8_bad) - len(empty), npart),
         "; ".join(a8_bad + ["EMPTY " + e for e in empty])))
    (ok if not a9_bad else bad).append(
        ("S2", "no declared partition holds a step A9 can see (%d of %d)"
         % (npart - len(a9_bad), npart), "; ".join(a9_bad)))
    (ok if fired else bad).append(
        ("S3", "positive control: the pooled series fires A8 and A9", ""))
    for cid, what, _why in ok:
        print("  ok   %-4s %s" % (cid, what))
    for cid, what, why in bad:
        print("  FAIL %-4s %s -- %s" % (cid, what, why or "see above"))
    print("RESULT: %d/%d" % (len(ok), len(ok) + len(bad)))
    return 1 if bad else 0


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
        print("%s  %s  exec=%s  apt=%s  exec-apt=%s  BIG3=%s  (lint apt %s)"
              % (row["run_id"], row["sha7"], row["instr_s"],
                 row["instr_apt_s"], row["suite_cost_s"], row["big3_s"],
                 row["lint_apt_s"]))
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


def _fixture_big3(drop=()):
    """A run that HAS the BIG3 steps.  `drop` removes some of them, which is
    the only way to reach A6's middle branch.

    Deliberately a separate fixture from `_fixture_normal()`: that one has no
    BIG3 step at all and must keep working, because a CI shape without them is
    A4's business and not an error.  Keeping the two apart is also why the A3
    docstring mistake -- reading the fixture's step names as the repository's
    -- cannot repeat here: this fixture's names ARE the real ones, and the case
    below asserts against numbers a hand can add, not against the corpus.
    """
    steps = [("Set up job", 1), ("apt", 16), ("capture dir", 0)]
    for n, d in (("test-console-capture-mutants", 361),
                 ("test-console-capture", 84),
                 ("test-deskchan", 58)):
        if n not in drop:
            steps.append((n, d))
    steps.append(("short", 31))
    return _run(2, [_job("instruments", steps),
                    _job("text", [("spec-check", 4)]),
                    _job("lint", [("Run sudo apt-get update -qq", 6)]),
                    _job("census", [("census", 4)])])


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
        # 🔄 The two neighbours were literals dated 2026-09-01 until
        # 2026-09-09, so this case would have broken the moment CHANGEPOINT
        # moved -- which is the event it exists to survive.  Derived now.
        cp = datetime.fromisoformat(CHANGEPOINT.replace("Z", "+00:00"))
        _e = (cp - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        _l = (cp + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = [{"created_utc": _e,          "suite_cost_s": "548"},
                {"created_utc": CHANGEPOINT, "suite_cost_s": "529"},
                {"created_utc": _l,          "suite_cost_s": "531"}]
        after = [r for r in rows if r["created_utc"] >= CHANGEPOINT]
        before = [r for r in rows if r["created_utc"] < CHANGEPOINT]
        assert len(after) == 2, after
        assert len(before) == 1, before
        assert after[0]["suite_cost_s"] == "529", after
        # and the wrong convention, stated so it cannot be re-chosen silently
        wrong = [r for r in rows if r["created_utc"] > CHANGEPOINT]
        assert len(wrong) == 1, wrong
    case("P10", "the changepoint row is the FIRST of the right segment", p10)

    # P11 -- BIG3 arithmetic, on a fixture whose answer a hand can add:
    # 361 + 84 + 58 = 503, and suite_cost is 1+0+503+31 = 535.
    def p11():
        row, _ = run_row(_fixture_big3())
        assert row["big3_s"] == "503", row
        assert row["suite_cost_s"] == "535", row
        # and the three are a SUBSET of the cost, never equal to it
        assert int(row["big3_s"]) < int(row["suite_cost_s"]), row
    case("P11", "BIG3 sums the three named steps and nothing else", p11)

    # P12 -- A6's middle branch.  Dropping ONE of the three must refuse the row.
    # This is the case the whole column exists for: 84 + 58 = 142 is a perfectly
    # plausible-looking number, and writing it down is how a suite that stopped
    # running becomes a suite that got faster.
    def p12():
        for drop in (("test-deskchan",),
                     ("test-console-capture", "test-deskchan")):
            try:
                run_row(_fixture_big3(drop=drop))
            except Refused as e:
                assert "A6" in str(e), e
                for missing in drop:
                    assert missing in str(e), (e, missing)
            else:
                raise AssertionError("A6 did not fire, dropped %r" % (drop,))
    case("P12", "A6 refuses a partial BIG3 instead of writing a short sum", p12)

    # P13 -- the third branch, and the reason it is not a refusal: a CI shape
    # with NO BIG3 step is A4's business, not a broken run.  `_fixture_normal`
    # is exactly that shape, so P1..P9 keep working.
    def p13():
        row, _ = run_row(_fixture_normal())
        assert row["big3_s"] == "-", row
        assert row["suite_cost_s"] == "534", row
    case("P13", "no BIG3 step at all is '-', not a refusal and not a zero", p13)

    # P14 -- A7's share, computed on the fixture rather than quoted from the
    # comment above BIG3.  503/535 = 94.0 %, over the 85 % floor.
    def p14():
        row, _ = run_row(_fixture_big3())
        share = 100.0 * int(row["big3_s"]) / int(row["suite_cost_s"])
        assert 93.0 < share < 95.0, share
        assert share >= BIG3_FLOOR_PCT, (share, BIG3_FLOOR_PCT)
        # the floor has to be able to fail, or A7 is decoration
        assert 20.0 < BIG3_FLOOR_PCT < 99.0, BIG3_FLOOR_PCT
    case("P14", "A7's share is derived, and the floor is one a set can fall below", p14)

    # P15 -- negative control for the column, in the shape P9 uses for apt:
    # empty the BIG3 set and the arithmetic must collapse, not quietly agree.
    def p15():
        global BIG3
        keep = BIG3
        BIG3 = ()
        try:
            row, _ = run_row(_fixture_big3())
            assert row["big3_s"] == "-", (
                "with BIG3 empty every run should look like it has none; "
                "got %r" % row["big3_s"])
        finally:
            BIG3 = keep
        row, _ = run_row(_fixture_big3())
        assert row["big3_s"] == "503", row
    case("P15", "negative control: an empty BIG3 set cannot report a number", p15)

    # ---- A8 / A9, added 2026-09-09 ------------------------------------
    # A step-free series and a stepped one, both synthetic, both with answers
    # a hand can check.  Neither reads ci-suite-cost.tsv: a case built on the
    # corpus changes meaning as the corpus grows, which is the A3 mistake in
    # the other direction.
    def _flat():
        return [954, 957, 954, 956, 953, 956, 957, 945, 958, 960, 947]

    def _stepped():
        return [502, 504, 499, 503, 502, 954, 957, 954, 956, 953]

    def _rows(vals):
        return [{"created_utc": "2026-09-0%dT00:00:0%dZ" % (1 + i // 9, i % 9),
                 "sha7": "r%06d" % i, "big3_s": str(v)}
                for i, v in enumerate(vals)]

    # P16 -- A8 fires on a partition wide enough to hold two populations, and
    # the ceiling is a value a real series can cross (P14's shape).
    def p16():
        vals = _stepped()
        rc, fired = audit_partition(vals, _rows(vals), quoted=True, quiet=True)
        assert fired and rc == 1, (rc, fired)
        lo, hi = min(vals), max(vals)
        pct = 100.0 * (hi - lo) / 2.0 / ((lo + hi) / 2.0)
        assert pct > PARTITION_MAX_PCT, (pct, PARTITION_MAX_PCT)
        # 🔴 The first draft of this line asserted 31.23 % and read the
        # minimum off the series by eye as 502.  It is 499.  The case failed,
        # the tool was right, and the number stays hand-derived rather than
        # copied from the failure message: 229 / 728 = 31.456 %.
        assert (lo, hi) == (499, 957), (lo, hi)
        assert abs(pct - (100.0 * 229.0 / 728.0)) < 1e-9, pct
        assert abs(pct - 31.456) < 0.001, pct
        # and the VERDICT is printed, not merely returned -- the output is the
        # product, so one case reads it.
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            audit_partition(vals, _rows(vals), quoted=True)
        out = buf.getvalue()
        assert "A8 half-width 31.456 %" in out, out
        assert "FIRED: this is not one population" in out, out
        assert "FIRED: declare this boundary or explain it" in out, out
        assert "r000005" in out, ("A9 must name the row", out)
    case("P16", "A8 refuses a partition that is two populations", p16)

    # P17 -- the other branch, and the NEGATIVE CONTROL on the ceiling itself.
    # A clean partition must pass; and with the ceiling at 0 the SAME rows must
    # fail, because a ceiling nothing can cross is decoration.
    def p17():
        global PARTITION_MAX_PCT
        vals = _flat()
        rc, fired = audit_partition(vals, _rows(vals), quoted=True, quiet=True)
        assert rc == 0 and not fired, (rc, fired)
        keep = PARTITION_MAX_PCT
        PARTITION_MAX_PCT = 0.0
        try:
            rc2, fired2 = audit_partition(vals, _rows(vals), quoted=True,
                                          quiet=True)
            assert rc2 == 1 and fired2, (rc2, fired2)
        finally:
            PARTITION_MAX_PCT = keep
        rc3, _ = audit_partition(vals, _rows(vals), quoted=True, quiet=True)
        assert rc3 == 0, rc3
    case("P17", "A8 passes one population, and its ceiling can be crossed", p17)

    # P18 -- A9 LOCATES the step, and the index is the FIRST row of the right
    # segment.  Getting this off by one would name the wrong commit, which is
    # the whole output of the check.
    def p18():
        vals = _stepped()
        sep, idx = separation(vals)
        assert idx == 5, ("want the first row of the right segment", idx)
        assert vals[idx] == 954, vals[idx]
        assert vals[idx - 1] == 502, vals[idx - 1]
        assert sep > PARTITION_MIN_SEP_SD, sep
    case("P18", "A9 names the first row of the right segment", p18)

    # P19 -- NEGATIVE CONTROL on the locator.  A locator that always names a
    # split is not a locator.  The flat series must come out below the floor,
    # and a series of three must return no index at all rather than a guess.
    def p19():
        sep, idx = separation(_flat())
        assert idx is not None, "the flat series has enough points to split"
        assert sep < PARTITION_MIN_SEP_SD, sep
        s2, i2 = separation([954, 957, 954])
        assert i2 is None and s2 == 0.0, (s2, i2)
    case("P19", "negative control: A9 finds no step in one population", p19)

    # P20 -- what `--since changepoint` resolves to, stated with the wrong
    # answer beside it, in P10's shape.  Reading the FIRST entry is the state
    # this file was in on 2026-09-08 and it is a live mistake, not a
    # hypothetical: it pooled n=69 and printed +/- 31.778 %.
    def p20():
        assert len(CHANGEPOINTS) >= 2, CHANGEPOINTS
        stamps = [c[0] for c in CHANGEPOINTS]
        assert stamps == sorted(stamps), ("oldest first", stamps)
        assert len(set(stamps)) == len(stamps), stamps
        assert CHANGEPOINT == stamps[-1], (CHANGEPOINT, stamps)
        assert CHANGEPOINT != stamps[0], (
            "the FIRST entry is the wrong answer and is what was resolved "
            "until 2026-09-09")
        for ts, on, why in CHANGEPOINTS:
            assert ts.endswith("Z") and len(ts) == 20, ts
            assert on in COLUMNS, (on, "located on a column that exists")
            assert len(why) > 40, (ts, why)
    case("P20", "--since changepoint is the LATEST boundary, not the first", p20)

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
                   help="an ISO timestamp, or the word `changepoint` for the "
                        "LATEST declared boundary (%s of %d). The row ON the "
                        "boundary belongs to the segment that STARTS there. "
                        "Giving --since is CLAIMING a population, so A8 and A9 "
                        "carry an exit code there and not on the pooled view."
                        % (CHANGEPOINT, len(CHANGEPOINTS)))
    s.add_argument("--pool", action="store_true",
                   help="pool rows whose job sets differ (A4 says do not)")
    s.set_defaults(fn=cmd_stats)

    g = sub.add_parser("segments", help="audit every declared partition, "
                                        "with the pooled view as the control")
    g.set_defaults(fn=cmd_segments)

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
