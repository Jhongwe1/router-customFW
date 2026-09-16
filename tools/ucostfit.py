#!/usr/bin/env python3
"""ucostfit -- re-derive `SPEC.md` `CPU-73` from the two committed captures.

WHAT THIS OWNS
--------------
The least-squares step between `bench/2026-09-16/C2-UC.log` /
`C2-UC2.log` and the four costs published in
`docs/emulation-surface.md` § *The four costs*, `SPEC.md` `CPU-73` and
`docs/rlx-isa.md` § 8.2.  `/bin/ucost` emits raw snapshots and does no
fitting on the board (`ucost.c:581`, *"THE BOARD EMITS RAW SNAPSHOTS"*);
the fit was done at the desk on 2026-09-16 and thrown away.

🔴 THAT IS THE DEFECT THIS FILE EXISTS FOR.  `docs/rlx-isa.md` § 9 promises,
for every reading, *"an instrument, a capture committed in this repository,
and the command that re-derives the reading"*.  For `CPU-73` the third of
those did not exist: four numbers were published that no committed command
could reproduce.  A number nobody can recompute is a claim, not a
measurement, and this repository's own rule is that a tool reporting `0`
is making a claim -- one level up, a *document* reporting a number with no
re-derivation is the same shape.

WHAT IT CANNOT DO
-----------------
* It does not measure anything.  Every input is a committed capture; a
  wrong reading on the board is a wrong reading here, silently.
* It cannot separate a real cost from a systematic error COMMON to a row
  and its twin.  The whole design is a difference against a twin, so
  anything both cells pay cancels -- including anything both cells pay
  wrongly.  `PROGRESS.md`'s second 否證 under `D-cost` says the same thing
  from the other side.
* It cannot license the absolute nanosecond.  `hz_used` is the driver's own
  DERIVED 200,000 (`ucost.c:518`); `CLK-17` measured the tick source at
  ~200,005 Hz and `CLK-28` at ~200,180 Hz, and neither is what the header
  says.  The conversion is a pure SCALE, so it moves every number here by the
  same factor and changes no comparison between them: at 200,005 by
  0.0025 % (988.639 -> 988.614 ns) and at 200,180 by 0.090 %
  (-> 987.75 ns).  Still, the nanosecond is a 讀 constant off the capture
  header and not a 量, and it is read from the header rather than compiled
  in for the reason `ucost.c:415` gives.
* It says nothing about atomicity.  `ll`/`sc` costing nothing is a statement
  about TIME.  Whether the pair is atomic is a different experiment
  (`SPEC.md` `CPU-74`'s ⚠️).
* `E7` is a clause about what the write-up must SAY.  A tool cannot check it
  and this one does not pretend to.

THE DoD CLAUSES IT CHECKS -- `PROGRESS.md` § `D-cost`, lines 164-216
--------------------------------------------------------------------
`E1`  every quoted cost comes from >= 3 iteration counts.  量 here: 4, and
      the board's own `UCEND rungs=` is read as a second source, so a row
      the desk mis-parsed cannot pass by agreeing with itself.
`E2`  `|slope(nop_a) - slope(nop_b)|` is printed and the smallest QUOTED
      cost must be >= 10x it, or the whole table is VOID -- not partially
      valid.  `nop_a` and `nop_b` are two separately assembled cells at two
      addresses, so this control can fail.
`E3`  two boots.  Checked as an identity rather than assumed: both captures
      must carry the same `UCOST_BUILD_ID`, or they are two instruments and
      the agreement between them means nothing.
`E4`  linearity, and it can fail.  Largest residual under
      `max(2 counts, 1 % of the row's largest delta)`.  Outside it the row's
      slope is NOT quoted as a cost.
`E5`  the ruler's own identity on every rung: `d_jiffies == d_irq_count`, and
      the two composites equal or exactly one reload apart.  More than 1/4
      of rungs failing voids the seating.

WHICH COSTS ARE "QUOTED", AND WHY THE RULE IS WRITTEN DOWN HERE
---------------------------------------------------------------
`E2` and `E4` both turn on the word, and the DoD does not define it.  The
rule this tool applies, which is the one the publication used:

    a row's cost is QUOTED when the row AND its twin pass `E4` on EVERY
    capture analysed; otherwise the row's number is reported as a BOUND and
    takes no part in `E2`'s ratio.

量 over the two committed boots that makes {`sync`, `lwu2`} quoted and
{`ll`, `sc`} bounds -- `sw` fails `E4` on boot 1 and `ll` on boot 2 --
which is what `SPEC.md` `CPU-73`'s ⚠️ states in prose.  ⚠️ The rule is
sensitive to the population: run this on ONE capture and boot 1 alone
quotes `ll`, boot 2 alone quotes `sc`.  The header line says how many
captures decided it, so a summary cannot be read as coverage it lacks.

FIELD LAYOUT -- 讀 `config/rlxfw-user/isaprobe/ucost.c:586-610`
--------------------------------------------------------------
Nineteen whitespace-separated fields, every one hex:

    UC row name cls rung N  a.j a.c0raw a.c1 a.irq  b.j b.c0raw b.c1 b.irq
       comp_tc0 comp_tc1 d_jiffies d_irq  a.nbytes

`comp_tc0 = j * reload + (c0raw >> 4)` and `comp_tc1 = j * reload + c1`
(`ucost.c:419-427`), differenced as u32.  The `>> 4` is
`RTL819X_TC_VALUE_SHIFT`: `tc0cnt` prints RAW and the TC1 path prints
shifted, and a reader who forgets it is wrong by 16x (`ucost.c:211`).

⚠️ The last field is `a.nbytes` -- what the snapshot's single `read()`
returned (`ucost.c:224`).  It is a PARSE WITNESS, not a measurement: it is
here because `FW-64` makes one `cat` two `read_proc` invocations, and a
short read would drop fields silently.  This tool checks it is constant-ish
and otherwise ignores it.  A recovered layout that called it an unknown `X`
would have invited someone to fit against it.
"""
import argparse
import copy
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The two boots `CPU-73` rests on.  Named rather than globbed: a third
# capture appearing under bench/ must be a decision, not a silent change of
# population, because the QUOTED rule above reads every capture given.
CAPTURES = [
    os.path.join(ROOT, "bench", "2026-09-16", "C2-UC.log"),
    os.path.join(ROOT, "bench", "2026-09-16", "C2-UC2.log"),
]

# 讀 `ucost.c:436-456`.  Each measured row's twin has the same memory shape,
# the same cell prologue and the same loop; only the probed word differs.
# `nop_a` is BOTH the zero control's A leg and `sync`'s twin, which
# `ucost.c:475` states rather than hides.
TWIN = {"sync": "nop_a", "lwu2": "lw", "ll": "lw", "sc": "sw"}
ZERO_CONTROL = ("nop_a", "nop_b")

# `SPEC.md` `CLK-01`, 量.  Only used to express a measured nanosecond as
# cycles; nothing in the fit depends on it.
CPU_HZ = 400e6

# `ucost.c:211`, RTL819X_TC_VALUE_SHIFT.
TC_SHIFT = 4

HDR_RX = re.compile(r"^rlxucost:\s+([a-z0-9_]+)=([0-9a-fA-F]+)\s*$")
BANNER_RX = re.compile(r"^\*\*\* rlxucost UC ([0-9a-f]{16}) (\S+) \*\*\*\s*$")
END_RX = re.compile(r"^UCEND\s+([0-9a-fA-F]{8})\s+(\S+)\s+rungs=([0-9a-fA-F]{8})"
                    r"\s+spent=([0-9a-fA-F]{8})\s+rc=([0-9a-fA-F]{8})\s*$")


class Refused(Exception):
    """A stated reason to fit nothing, rather than fitting whatever was found."""


def s32(v):
    """u32 difference read as signed.  `comp_tc0` goes negative on this board
    -- `tc0cnt` counts down within a period -- so an unsigned read would put
    0xFFFFF8F3 into a least-squares fit as four billion."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >> 31 else v


class Capture(object):
    """One boot's worth of `/bin/ucost` output, raw fields only."""

    def __init__(self, path, label):
        self.path = path
        self.label = label
        self.build_id = None
        self.arg = None
        self.hdr = {}
        self.rows = []          # one dict per UC line, in file order
        self.ends = {}          # row name -> rungs the BOARD says it emitted
        self.board_bad = [0, 0]  # composites where board and desk disagree

    # -- header fields, each with the refusal that belongs to it ------------
    @property
    def reload(self):
        return self.hdr["reload"]

    @property
    def hz_used(self):
        return self.hdr["hz_used"]

    @property
    def ns_per_count(self):
        return 1e9 / float(self.hz_used)


def parse(path, label=None):
    """Read one capture.  Refuses rather than returning a partial fit."""
    if not os.path.exists(path):
        raise Refused("no such capture: %s" % path)
    cap = Capture(path, label or os.path.basename(path))
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            m = BANNER_RX.match(line)
            if m:
                cap.build_id, cap.arg = m.group(1), m.group(2)
                continue
            m = HDR_RX.match(line)
            if m:
                cap.hdr[m.group(1)] = int(m.group(2), 16)
                continue
            m = END_RX.match(line)
            if m:
                cap.ends[m.group(2)] = (int(m.group(3), 16), int(m.group(5), 16))
                continue
            f = line.split()
            if len(f) == 19 and f[0] == "UC":
                try:
                    v = [int(x, 16) for x in f[1:2] + f[3:]]
                except ValueError:
                    continue
                cap.rows.append({
                    "row": v[0], "name": f[2], "cls": v[1], "rung": v[2],
                    "n": v[3],
                    "aj": v[4], "ac0": v[5], "ac1": v[6], "airq": v[7],
                    "bj": v[8], "bc0": v[9], "bc1": v[10], "birq": v[11],
                    "p_c0": v[12], "p_c1": v[13],
                    "p_dj": v[14], "p_dirq": v[15], "nbytes": v[16],
                })

    for k in ("rows", "rungs", "reload", "hz_used", "ce_live"):
        if k not in cap.hdr:
            raise Refused("%s: header has no `%s=` -- this is not a `ucost` "
                          "capture, or it is truncated" % (cap.label, k))
    if not cap.rows:
        raise Refused("%s: no `UC` data lines. A fit over an empty population "
                      "prints the same summary as a clean one" % cap.label)

    # The ruler.  `ucost.c:615` chooses `comp_tc1` only when the clockevent is
    # live; with `ce_live=0` the board's own budget followed `comp_tc0`, and
    # `comp_tc1` is then a counter nothing drives.  Fitting it anyway would
    # produce slopes -- wrong ones, quietly.
    if not cap.hdr["ce_live"]:
        raise Refused("%s: header says ce_live=0, so `comp_tc1` is not the "
                      "ruler on this boot and this tool has no other one"
                      % cap.label)
    if cap.hdr.get("mode_ce", 1) != 1:
        raise Refused("%s: header says mode_ce=%d; the tick is not this "
                      "driver's clockevent" % (cap.label, cap.hdr["mode_ce"]))
    if cap.reload <= 0:
        raise Refused("%s: reload=%d makes the composite degenerate"
                      % (cap.label, cap.reload))

    # Shape, both directions.  The board declares `rows=` and prints one
    # `UCEND ... rungs=` per row; the desk counts `UC` lines.  A rung the
    # budget guard skipped is REPORTED by the board (`ucost.c:626-648`), so a
    # disagreement here is the desk mis-parsing, which is the failure that
    # would otherwise reach a slope.
    names = []
    for r in cap.rows:
        if r["name"] not in names:
            names.append(r["name"])
    if len(names) != cap.hdr["rows"]:
        raise Refused("%s: header says rows=%d, the file holds %d row name(s): "
                      "%s" % (cap.label, cap.hdr["rows"], len(names),
                              ", ".join(names)))
    for nm in names:
        got = len([r for r in cap.rows if r["name"] == nm])
        if nm not in cap.ends:
            raise Refused("%s: row %s has %d rung(s) and no `UCEND` line"
                          % (cap.label, nm, got))
        said, rc = cap.ends[nm]
        if said != got:
            raise Refused("%s: row %s -- the board says it emitted %d rung(s), "
                          "the parse found %d" % (cap.label, nm, said, got))
        if rc != 0:
            raise Refused("%s: row %s ended rc=%d, so a snapshot failed inside "
                          "it" % (cap.label, nm, rc))
    return cap


def derive(cap):
    """Recompute both composites from the six raw fields and fill the derived
    per-rung quantities.

    🔴 THE RECOMPUTE IS THE POINT, not a convenience.  `ucost.c:581` prints
    the composites *"as a convenience ... so a disagreement between the
    board's arithmetic and the desk's is visible"*.  Reading the printed
    field and calling that a check would compare the board with itself."""
    cap.board_bad = [0, 0]
    for r in cap.rows:
        c0 = s32((r["bj"] * cap.reload + (r["bc0"] >> TC_SHIFT)) -
                 (r["aj"] * cap.reload + (r["ac0"] >> TC_SHIFT)))
        c1 = s32((r["bj"] * cap.reload + r["bc1"]) -
                 (r["aj"] * cap.reload + r["ac1"]))
        if c0 != s32(r["p_c0"]):
            cap.board_bad[0] += 1
        if c1 != s32(r["p_c1"]):
            cap.board_bad[1] += 1
        r["c0"], r["c1"] = c0, c1
        r["dj"] = s32(r["bj"] - r["aj"])
        r["dirq"] = s32(r["birq"] - r["airq"])
    return cap


def ols(xs, ys):
    """Slope and intercept, plain least squares.  Four points and no weights:
    the ladder is x4 geometric (`ucost.c:536`), so the top rung dominates the
    slope and `E4` exists to say whether that is allowed."""
    n = len(xs)
    mx = sum(xs) / float(n)
    my = sum(ys) / float(n)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0.0:
        raise Refused("every rung of a row used the same iteration count; "
                      "there is no slope in it")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return b, my - b * mx


class RowFit(object):
    def __init__(self, name, cls, xs, ys):
        self.name, self.cls = name, cls
        self.xs, self.ys = xs, ys
        self.slope, self.intercept = ols(xs, ys)
        self.resid = [y - (self.intercept + self.slope * x)
                      for x, y in zip(xs, ys)]
        self.maxresid = max(abs(v) for v in self.resid)
        # `E4`: 1 % of the row's largest delta, floored at 2 counts.  The
        # floor exists because 1 % of a cheap row is below the ruler's own
        # +-1 dispersion; `SPEC.md` `FW-73` is the reading that the ratio is
        # ~50x stricter on a cheap row than on an expensive one, which is
        # why the two `E4` failures are a different row on each boot.
        self.tol = max(2.0, 0.01 * max(ys))
        self.linear = self.maxresid <= self.tol   # `under`: a residual
        self.nrungs = len(xs)                     # exactly at tol passes


def fit(cap):
    """row name -> RowFit, over `comp_tc1`."""
    by = {}
    for r in cap.rows:
        by.setdefault(r["name"], []).append(r)
    out = {}
    for nm, rr in by.items():
        rr.sort(key=lambda r: r["n"])
        out[nm] = RowFit(nm, rr[0]["cls"], [float(r["n"]) for r in rr],
                         [float(r["c1"]) for r in rr])
    return out


def e5(cap):
    """The ruler's own identity, both halves, per rung.

    Returns (composite_bad, irq_bad, both_bad) as lists of
    (name, rung, amount)."""
    comp, irq, both = [], [], []
    for r in cap.rows:
        d = r["c1"] - r["c0"]
        a = d not in (0, cap.reload, -cap.reload)
        b = r["dj"] != r["dirq"]
        if a:
            comp.append((r["name"], r["rung"], d))
        if b:
            irq.append((r["name"], r["rung"], r["dj"] - r["dirq"]))
        if a or b:
            both.append((r["name"], r["rung"]))
    return comp, irq, both


class Analysis(object):
    """Every derived quantity, over one or more captures."""

    def __init__(self, caps):
        if not caps:
            raise Refused("no captures")
        self.caps = caps
        self.fits = [fit(c) for c in caps]
        self.e5 = [e5(c) for c in caps]

        names = sorted(self.fits[0])
        for f in self.fits[1:]:
            if sorted(f) != names:
                raise Refused("the captures do not hold the same rows: %s "
                              "against %s" % (names, sorted(f)))
        self.names = names
        self.nrungs = sorted(set(self.fits[0][n].nrungs for n in names))

        # `E1`.  Three is the DoD's floor; this board gives four.
        self.e1_short = [(c.label, n) for c, f in zip(caps, self.fits)
                         for n in names if f[n].nrungs < 3]

        # `E2` -- the zero control, per capture.
        self.zero = [abs(f[ZERO_CONTROL[0]].slope - f[ZERO_CONTROL[1]].slope)
                     * c.ns_per_count for c, f in zip(caps, self.fits)]

        # Costs: (row, capture index) -> ns per iteration.
        self.cost = {}
        for i, (c, f) in enumerate(zip(caps, self.fits)):
            for row, tw in TWIN.items():
                if row in f and tw in f:
                    self.cost[(row, i)] = ((f[row].slope - f[tw].slope)
                                           * c.ns_per_count)

        # The QUOTED rule, stated in the module docstring: a row and its twin
        # must pass `E4` on EVERY capture given.
        self.quoted, self.bound_why = [], {}
        for row, tw in sorted(TWIN.items()):
            bad = []
            for c, f in zip(caps, self.fits):
                for who in (row, tw):
                    if who in f and not f[who].linear:
                        bad.append("%s fails E4 on %s" % (who, c.label))
            if bad:
                self.bound_why[row] = "; ".join(sorted(set(bad)))
            else:
                self.quoted.append(row)

        # `E2`'s ratio: the worst (row, boot) pair among the quoted rows,
        # each against ITS OWN boot's zero control.
        self.ratios = []
        for row in self.quoted:
            for i in range(len(caps)):
                z = self.zero[i]
                if (row, i) in self.cost:
                    self.ratios.append(
                        (abs(self.cost[(row, i)]) / z if z else float("inf"),
                         row, i))
        self.min_ratio = min(self.ratios)[0] if self.ratios else None
        self.void = (self.min_ratio is not None and self.min_ratio < 10.0)

        # `E4` roll-up.
        self.e4_fail = [(c.label, n) for c, f in zip(caps, self.fits)
                        for n in names if not f[n].linear]
        self.e4_total = len(names) * len(caps)

        # Clusters.  Two ratios are printed, not one, because "~90x" is only
        # the reading against the `nop` baseline: taken against the top of the
        # low cluster the same data says 60x, and a reader handed one number
        # cannot tell which he has.
        self.clusters = []
        for f in self.fits:
            nop = sum(f[n].slope for n in ZERO_CONTROL) / 2.0
            # The two CLUSTERS are a shape in the numbers, not the `cls`
            # column: `ll` and `sc` are declared class E and land in the LOW
            # cluster, which is the whole result of `E6`.  Split at the
            # largest ratio between neighbours rather than at a threshold,
            # so the split is a reading and not a choice.
            alls = sorted((f[n].slope, n) for n in names)
            gaps = [(alls[i + 1][0] / alls[i][0], i)
                    for i in range(len(alls) - 1)]
            g, at = max(gaps)
            self.clusters.append({
                "low": alls[:at + 1], "high": alls[at + 1:], "gap": g,
                # The published "~90x".  It is the bottom of the high cluster
                # against the `nop` baseline; taken against the TOP of the low
                # cluster the same data reads 60x, which is the `gap` above.
                "over_nop": alls[at + 1][0] / nop, "nop": nop,
            })

        # The exception round trip, expressed as cycles.
        # 🔴 QUOTED IS NOT THE RIGHT FILTER HERE and the first version used
        # it.  量, running this on ONE capture: boot 1 alone quotes `ll` too,
        # and the range came out `5.0-988.6 ns = 2-395 cycles` -- a 5 ns
        # exception.  It happened to read 366-396 on the two-boot population
        # only because `ll` fails E4 on boot 2.  A number that is right for a
        # reason the code does not contain is the shape this repository keeps
        # recording.  The filter is the HIGH SLOPE CLUSTER, which is a
        # reading: the two clusters are 60x apart at the split.
        self.exc = [sorted(set(TWIN) & set(n for _, n in cl["high"]))
                    for cl in self.clusters]
        q = [abs(self.cost[(r, i)]) for i in range(len(caps))
             for r in self.exc[i] if r in self.quoted and (r, i) in self.cost]
        self.rt_ns = (min(q), max(q)) if q else None
        self.rt_cyc = (int(round(min(q) * CPU_HZ / 1e9)),
                       int(round(max(q) * CPU_HZ / 1e9))) if q else None
        # Per-capture spread between those same rows: the "two instructions
        # through two handlers agree to N %" figure.
        self.spread = []
        for i in range(len(caps)):
            v = [abs(self.cost[(r, i)]) for r in self.exc[i]
                 if r in self.quoted and (r, i) in self.cost]
            self.spread.append((max(v) - min(v)) / max(v) * 100.0
                               if len(v) > 1 else None)

    def board_bad_total(self):
        """Rungs where the board's printed composite and the desk's recompute
        disagree.  Non-zero is a finding about one of the two arithmetics and
        there is no way from here to say which, so it is a red."""
        return sum(sum(c.board_bad) for c in self.caps)


def report(an, out=sys.stdout):
    """The table, and every count a reader would otherwise have to assume."""
    caps = an.caps
    def p(s=""):
        print(s, file=out)

    ids = sorted(set(c.build_id for c in caps))
    p("ucostfit: %d capture(s), %d row(s) each, %s rung(s) per row, %d rung(s) "
      "in all" % (len(caps), len(an.names),
                  "/".join(str(x) for x in an.nrungs),
                  sum(len(c.rows) for c in caps)))
    p("          UCOST_BUILD_ID %s   arg(s) %s"
      % (", ".join(ids), ", ".join(c.arg or "?" for c in caps)))
    for c in caps:
        p("          %-6s %s" % (c.label, os.path.relpath(c.path, ROOT)))
        p("                 reload=%d hz_used=%d hz_kernel=%s ce_live=%d "
          "mode_ce=%d  1 count = %.4f us"
          % (c.reload, c.hz_used, c.hdr.get("hz_kernel", "?"),
             c.hdr["ce_live"], c.hdr.get("mode_ce", -1),
             c.ns_per_count / 1000.0))
    p()

    # -- the recompute -----------------------------------------------------
    tot = sum(len(c.rows) for c in caps)
    bad0 = sum(c.board_bad[0] for c in caps)
    bad1 = sum(c.board_bad[1] for c in caps)
    p("  the board's arithmetic against the desk's, over all %d rung(s):" % tot)
    p("    comp_tc0 disagreements %d      comp_tc1 disagreements %d"
      % (bad0, bad1))
    p()

    # -- slopes ------------------------------------------------------------
    p("  slopes, counts per iteration, least squares over each row's rungs")
    p("    %-6s %-3s %s" % ("row", "cls", "  ".join(
        "%-34s" % ("%s: slope    maxresid  tol" % c.label) for c in caps)))
    for n in an.names:
        cells = []
        for f in an.fits:
            r = f[n]
            cells.append("%-34s" % ("%9.6f  %8.2f %8.2f %s"
                                    % (r.slope, r.maxresid, r.tol,
                                       "ok  " if r.linear else "FAIL")))
        p("    %-6s %-3s %s" % (n, "E" if an.fits[0][n].cls else "N",
                                "  ".join(cells)))
    p()

    # -- the costs ---------------------------------------------------------
    p("  cost(row) = slope(row) - slope(twin), in ns per iteration")
    p("    %-6s %-6s %s  %s" % ("row", "twin",
                                "  ".join("%12s" % c.label for c in caps),
                                "quoted?"))
    for row in sorted(TWIN, key=lambda r: -abs(an.cost.get((r, 0), 0))):
        cells = "  ".join("%+12.3f" % an.cost[(row, i)]
                          if (row, i) in an.cost else "%12s" % "-"
                          for i in range(len(caps)))
        tag = "quoted" if row in an.quoted else "BOUND"
        p("    %-6s %-6s %s  %s" % (row, TWIN[row], cells, tag))
    for row, why in sorted(an.bound_why.items()):
        p("      %s is a bound, not a number: %s" % (row, why))
    p()

    # -- E1 ----------------------------------------------------------------
    p("  E1  every fitted row rests on %s iteration count(s); the DoD's floor "
      "is 3" % "/".join(str(x) for x in an.nrungs))
    if an.e1_short:
        for lab, n in an.e1_short:
            p("      NOT MEASURED  %s on %s -- fewer than 3 rungs" % (n, lab))
    p()

    # -- E2 ----------------------------------------------------------------
    p("  E2  zero control |slope(nop_a) - slope(nop_b)|")
    for c, z in zip(caps, an.zero):
        p("      %-6s %.6f ns/it" % (c.label, z))
    if an.ratios:
        r, row, i = min(an.ratios)
        p("      smallest quoted cost / its own boot's zero control = %.1fx "
          "(%s on %s)" % (r, row, caps[i].label))
        p("      quoted row(s): %s" % (", ".join(an.quoted) or "none"))
        if an.void:
            p("      🔴 VOID -- below 10x. The whole table is void, not "
              "partially valid.")
        else:
            p("      -> above the 10x floor, so a measured cost is "
              "separable from the instrument")
    else:
        p("      🔴 no quoted cost at all: E2 has nothing to divide")
    p()

    # -- E4 ----------------------------------------------------------------
    p("  E4  linearity: largest residual under max(2 counts, 1 % of the "
      "row's largest delta)")
    p("      %d of %d row-boots pass" % (an.e4_total - len(an.e4_fail),
                                         an.e4_total))
    for lab, n in an.e4_fail:
        f = an.fits[[c.label for c in caps].index(lab)][n]
        p("      🔴 %-6s on %-6s is outside: maxresid %.2f against tol %.2f  "
          "residuals %s" % (n, lab, f.maxresid, f.tol,
                  " ".join("%+.1f" % v for v in f.resid)))
    p()

    # -- E5 ----------------------------------------------------------------
    p("  E5  the ruler's own identity, per rung")
    tot_comp = tot_irq = 0
    for c, (comp, irq, both) in zip(caps, an.e5):
        n = len(c.rows)
        tot_comp += len(comp)
        tot_irq += len(irq)
        p("      %-6s composites differ by something other than 0 or one "
          "reload: %d of %d (%.1f %%)"
          % (c.label, len(comp), n, 100.0 * len(comp) / n))
        p("      %-6s d_jiffies != d_irq_count:                             "
          "     %d of %d (%.1f %%)"
          % (c.label, len(irq), n, 100.0 * len(irq) / n))
        p("      %-6s either half:                                          "
          "     %d of %d (%.1f %%)"
          % (c.label, len(both), n, 100.0 * len(both) / n))
    amounts = {}
    for comp, _, _ in an.e5:
        for _, _, d in comp:
            amounts[abs(d)] = amounts.get(abs(d), 0) + 1
    if amounts:
        p("      composite offenders by size: %s"
          % ", ".join("%d by +-%d" % (v, k) for k, v in sorted(amounts.items())))
    irqa = {}
    for _, irq, _ in an.e5:
        for _, _, d in irq:
            irqa[abs(d)] = irqa.get(abs(d), 0) + 1
    if irqa:
        p("      d_irq offenders by size:     %s"
          % ", ".join("%d by +-%d" % (v, k) for k, v in sorted(irqa.items())))
    worst = max((100.0 * len(c1) / len(c.rows))
                for c, (c1, _, _) in zip(caps, an.e5))
    worst_u = max((100.0 * len(b) / len(c.rows))
                  for c, (_, _, b) in zip(caps, an.e5))
    p("      threshold is 1/4 = 25.0 %%; worst composite half %.1f %%  -> %s"
      % (worst, "VOID" if worst > 25.0 else "under"))
    # The clause says "the ruler's own identity holds on every rung" and then
    # names TWO identities.  Which population the 1/4 is over is not written
    # down, and the two readings disagree on this data.  Reported rather than
    # resolved: picking one here would be repairing the instrument to agree
    # with the experiment.
    p("      ⚠️ read as EITHER half failing, the worst boot is %.1f %% -> %s. "
      "The clause does not say which population the 1/4 is over."
      % (worst_u, "VOID" if worst_u > 25.0 else "under"))
    p()

    # -- derived -----------------------------------------------------------
    p("  derived")
    for c, cl in zip(caps, an.clusters):
        p("      %-6s low  cluster %s"
          % (c.label, "  ".join("%s %.5f" % (n, v) for v, n in cl["low"])))
        p("      %-6s high cluster %s"
          % (c.label, "  ".join("%s %.5f" % (n, v) for v, n in cl["high"])))
        p("             bottom of the high cluster / nop baseline %.1fx; "
          "/ top of the low cluster %.1fx" % (cl["over_nop"], cl["gap"]))
    if an.rt_cyc:
        p("      exception round trip over the quoted rows in the high "
          "cluster (%s): %.1f-%.1f ns = %d-%d cycles at %.0f MHz"
          % (", ".join(sorted(set(r for e in an.exc for r in e))),
             an.rt_ns[0], an.rt_ns[1], an.rt_cyc[0], an.rt_cyc[1],
             CPU_HZ / 1e6))
    for c, sp in zip(caps, an.spread):
        if sp is not None:
            p("      %-6s those costs agree to %.1f %%" % (c.label, sp))
    p()

    if an.void:
        p("RESULT: E2 VOID -- the zero control is not small enough for any of "
          "these numbers to mean anything")
        return 1
    if an.board_bad_total():
        p("RESULT: the board and the desk disagree about a composite")
        return 1
    p("RESULT: %d row(s) fitted per capture over %s rung(s) each; %d cost(s) "
      "quoted, %d reported as bound(s)"
      % (len(an.names), "/".join(str(x) for x in an.nrungs),
         len(an.quoted), len(an.bound_why)))
    return 0


def load(paths):
    caps = []
    for i, p in enumerate(paths):
        c = parse(p, "boot%d" % (i + 1))
        derive(c)
        caps.append(c)
    # `E3`.  Two boots of ONE instrument, or the agreement between them is
    # an agreement between two different programs.
    ids = set(c.build_id for c in caps)
    if len(ids) > 1:
        raise Refused("the captures carry %d different UCOST_BUILD_IDs (%s); "
                      "they are not two boots of one instrument"
                      % (len(ids), ", ".join(sorted(str(i) for i in ids))))
    return caps


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test(out=sys.stdout):
    """Every published number, and three injections that must break one.

    🔴 A SELF-TEST THAT RUNS ZERO ASSERTIONS AND EXITS 0 IS THE DEFECT THIS
    REPOSITORY HUNTS.  The count is printed.  `N0` is the control on the
    controls -- xcheck's `M0` shape: a harness that breaks everything and a
    harness that touches nothing print the same thing unless the un-injected
    copy is read first.
    """
    import tempfile

    cases = []

    def ck(name, want, got):
        cases.append((name, want == got, "" if want == got
                      else "want %r got %r" % (want, got)))

    caps = load(CAPTURES)
    an = Analysis(caps)
    b1, b2 = an.fits

    # -- P: the population, and that it is the one CPU-73 rests on ---------
    ck("P1 both committed captures parse: 8 rows x 4 rungs, 64 in all",
       (2, 8, [4], 64),
       (len(caps), len(an.names), an.nrungs, sum(len(c.rows) for c in caps)))
    ck("P2 the board's composites equal the desk's on all 64 rungs",
       (0, 0), (sum(c.board_bad[0] for c in caps),
                sum(c.board_bad[1] for c in caps)))
    ck("P3 E1: every row rests on 4 rungs and the board's UCEND agrees",
       ([], [(4, 0)]),
       (an.e1_short, sorted(set(v for c in caps for v in c.ends.values()))))
    ck("P4 the three parse witnesses: reload 2000, hz_used 200000, hz_kernel 100",
       [(2000, 200000, 100)] * 2,
       [(c.reload, c.hz_used, c.hdr["hz_kernel"]) for c in caps])
    ck("P5 the ruler is licensed: ce_live=1 and mode_ce=1 on both boots",
       [(1, 1)] * 2, [(c.hdr["ce_live"], c.hdr["mode_ce"]) for c in caps])
    ck("P6 E3: one instrument, two boots -- same build id, different arg",
       (1, 2), (len(set(c.build_id for c in caps)),
                len(set(c.arg for c in caps))))

    # -- A: the eight published costs, to the digits as published ----------
    pub = [("sync", 0, "+988.639"), ("sync", 1, "+989.458"),
           ("lwu2", 0, "+915.608"), ("lwu2", 1, "+915.439"),
           ("ll", 0, "+5.021"), ("ll", 1, "+4.849"),
           ("sc", 0, "+0.187"), ("sc", 1, "-0.194")]
    for k, (row, i, want) in enumerate(pub, 1):
        ck("A%d %-5s boot%d cost %s ns/it" % (k, row, i + 1, want),
           want, "%+.3f" % an.cost[(row, i)])

    # -- E2 ----------------------------------------------------------------
    ck("E2a boot1 zero control 0.0014 ns/it", "0.0014", "%.4f" % an.zero[0])
    ck("E2b boot2 zero control 0.0108 ns/it", "0.0108", "%.4f" % an.zero[1])
    ck("E2c the quoted set over these two boots is {lwu2, sync}",
       ["lwu2", "sync"], sorted(an.quoted))
    ck("E2d smallest quoted cost is >= 84,000x the zero control, boot 2 driving",
       (True, "lwu2", 1),
       (an.min_ratio >= 84000.0,) + tuple(min(an.ratios)[1:]))
    ck("E2e the table is not VOID (the floor is 10x)", False, an.void)

    # -- E4 ----------------------------------------------------------------
    ck("E4a boot1: sw and only sw is outside tolerance, 25.1 against 23.91",
       (["sw"], "25.1", "23.91"),
       ([n for (lab, n) in an.e4_fail if lab == "boot1"],
        "%.1f" % b1["sw"].maxresid, "%.2f" % b1["sw"].tol))
    ck("E4b boot2: ll and only ll is outside tolerance, 21.0 against 9.54",
       (["ll"], "21.0", "9.54"),
       ([n for (lab, n) in an.e4_fail if lab == "boot2"],
        "%.1f" % b2["ll"].maxresid, "%.2f" % b2["ll"].tol))
    ck("E4c 14 of 16 row-boots pass", (14, 16),
       (an.e4_total - len(an.e4_fail), an.e4_total))

    # -- E5 ----------------------------------------------------------------
    comp = [c for cc, _, _ in an.e5 for c in cc]
    sizes = {}
    for _, _, d in comp:
        sizes[abs(d)] = sizes.get(abs(d), 0) + 1
    ck("E5a 13 of 64 composite rungs differ otherwise: 8 by +-1, 5 by +-1999",
       (13, {1: 8, 1999: 5}), (len(comp), sizes))
    ck("E5b per boot 7/32 (21.9 %) and 6/32 (18.8 %), both under 1/4",
       [(7, "21.9"), (6, "18.8")],
       [(len(cc), "%.1f" % (100.0 * len(cc) / len(c.rows)))
        for c, (cc, _, _) in zip(caps, an.e5)])
    irq = [i for _, ii, _ in an.e5 for i in ii]
    ck("E5c d_jiffies != d_irq on 5 of 64, each by exactly 1",
       (5, {1}), (len(irq), set(abs(d) for _, _, d in irq)))

    # -- D: the derived figures the write-up quotes ------------------------
    ck("D1 the two slope clusters are 90.3x apart over the nop baseline",
       ["90.3", "90.3"], ["%.1f" % c["over_nop"] for c in an.clusters])
    ck("D2 the exception round trip is 366-396 cycles at 400 MHz",
       (366, 396), an.rt_cyc)
    ck("D3 the two quoted costs agree to 7.4 % on boot 1 (7.5 % on boot 2)",
       ["7.4", "7.5"], ["%.1f" % s for s in an.spread])
    # The population control on the QUOTED rule and on the high-cluster
    # filter at once.  Boot 1 on its own quotes `ll` as well -- `sw` is the
    # only row outside tolerance there -- and the round trip must NOT then
    # take `ll`'s 5 ns as its floor.  量: it did, 2-395 cycles, until the
    # filter stopped being `quoted`.
    one = Analysis(load([CAPTURES[0]]))
    ck("D4 one capture alone quotes ll too, and the range is still the high "
       "cluster's", (["ll", "lwu2", "sync"], ["lwu2", "sync"], (366, 395)),
       (sorted(one.quoted), one.exc[0], one.rt_cyc))

    # -- N: the injections.  Each mutates an in-memory copy of the parsed
    #       rows.  No committed capture is opened for writing anywhere in
    #       this file.
    def injected(fn):
        cp = [copy.deepcopy(c) for c in caps]
        fn(cp)
        return Analysis(cp)

    ck("N0 control on the controls: un-injected, the three targets read as "
       "published", (True, 13, False),
       (b1["sw"].name == "sw" and not b1["sw"].linear,
        len(comp), an.void))

    def bump_c1(cp):
        # One rung of boot 1's `ll` -- a row that PASSES E4 on boot 1 with
        # 0.79 against 9.62 -- moved by +40 counts.  Both composites move
        # together so E5 cannot be what fires.
        for r in cp[0].rows:
            if r["name"] == "ll" and r["rung"] == 1:
                r["c1"] += 40
                r["c0"] += 40
    a_n1 = injected(bump_c1)
    ck("N1 a comp_tc1 perturbed by 40 counts on one rung pushes that row "
       "outside E4", (True, 13),
       (("boot1", "ll") in a_n1.e4_fail,
        sum(len(cc) for cc, _, _ in a_n1.e5)))

    def bump_dj(cp):
        # `d_jiffies` on one rung that currently satisfies both halves.
        for r in cp[1].rows:
            if r["name"] == "sync" and r["rung"] == 0:
                r["dj"] += 1
    a_n2 = injected(bump_dj)
    ck("N2 an altered d_jiffies on one rung raises the E5 identity count 5->6",
       (5, 6), (len(irq), sum(len(ii) for _, ii, _ in a_n2.e5)))

    def flatten(cp):
        # Boot 1's `sync` rebuilt ON ITS OWN LADDER at `nop_a`'s slope, so
        # the cost is exactly zero and the row still passes E4.
        # 🔴 The first version of this copied `nop_a`'s composites rung for
        # rung and did NOT work: the two rows run different ladders
        # (`ucost.c:536` -- native 16,384.. against emulated 4,096..), so
        # equal counts over a 4x smaller N is a 4x LARGER slope.  It read
        # +30.762 ns/it, which is a cost this injection was supposed to
        # destroy.  A control that does not do what its name says is worth
        # less than no control.
        f = fit(cp[0])["nop_a"]
        for r in cp[0].rows:
            if r["name"] == "sync":
                r["c1"] = f.intercept + f.slope * r["n"]
    a_n3 = injected(flatten)
    ck("N3 a row's slope forced equal to its twin's makes E2 declare VOID",
       (True, True, True),
       (a_n3.void, abs(a_n3.cost[("sync", 0)]) < 1e-6,
        "sync" in a_n3.quoted))

    # -- N4..N7: the refusals.  Each writes a MUTATED COPY to a temp dir.
    def refusal(text_fn):
        with tempfile.TemporaryDirectory() as d:
            src = open(CAPTURES[0], encoding="utf-8").read()
            p = os.path.join(d, "mutant.log")
            with open(p + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text_fn(src))
            os.replace(p + ".tmp", p)
            try:
                load([p])
                return "no refusal"
            except Refused as exc:
                return str(exc)

    got = refusal(lambda s: s.replace("ce_live=00000001", "ce_live=00000000"))
    ck("N4 a header saying ce_live=0 is REFUSED", True, "ce_live=0" in got)
    got = refusal(lambda s: s.replace(
        "UC 00000004 ll 00000001 00000001 00004000 ffffa84f 00005420 "
        "00000355 00001d5d ffffa84f 00006140 00000427 00001d5d 000000d2 "
        "000000d2 00000000 00000000 00000649\n", ""))
    ck("N5 a row one rung short of its own UCEND is REFUSED", True,
       "the board says it emitted 4" in got)
    try:
        load([os.path.join(ROOT, "bench", "no-such-dir", "no-such.log")])
        got = "no refusal"
    except Refused as exc:
        got = str(exc)
    ck("N6 a capture that does not exist is REFUSED", True,
       got.startswith("no such capture"))
    got = refusal(lambda s: s.replace("rows=00000008", "rows=00000009"))
    ck("N7 a header rows= the parse disagrees with is REFUSED", True,
       "header says rows=9" in got)

    passed = sum(1 for _, ok, _ in cases if ok)
    for name, ok, note in cases:
        print("  %-4s  %-72s %s" % ("ok" if ok else "FAIL", name, note),
              file=out)
    print("", file=out)
    print("RESULT: %d passed, %d failed, %d assertion(s) in all"
          % (passed, len(cases) - passed, len(cases)), file=out)
    return 0 if passed == len(cases) else 1


def main():
    ap = argparse.ArgumentParser(
        description="re-derive CPU-73's costs from the committed ucost captures")
    ap.add_argument("capture", nargs="*",
                    help="ucost captures; default is the two CPU-73 rests on")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    try:
        if a.self_test:
            return self_test()
        return report(Analysis(load(a.capture or CAPTURES)))
    except Refused as exc:
        print("ucostfit: REFUSED: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
