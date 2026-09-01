#!/usr/bin/env python3
"""xcheck -- do two committed instruments agree about one artefact?

`TOOL-1`.  量 2026-09-01: `tools/looptime.py` and `tools/boot-timeline.py`
both read a boot capture's `.timing`, one of them modelled the power-on
line-transition prefix and the other did not, and on six of fifteen cold
captures they differed by 0.321-0.350 s -- while `SPEC.md` `CLK-18` cited the
one without the model.  `looptime` was fixed.  **The class was not**: nothing
in this repository asserts that two tools reading one file agree, and
`ci-census` counts cases per suite and never across suites.

WHAT THIS IS AND WHAT IT IS NOT
-------------------------------
It is a table of IDENTITIES, each one a statement that two independent
implementations must produce the same number for the same input, and a sweep
that checks every identity over every artefact both sides can read.

🔴 It is NOT a second implementation of either tool.  It imports both and
compares them.  A third implementation would be a third thing that can be
wrong, and the question here is whether the two that are already committed and
already cited agree.

⚠️ AND IT DOES NOT RETROACTIVELY CATCH `CLK-18`.  The quantity `X3` compares --
`looptime`'s `lead_to_boot` -- did not exist before the fix, so no check over
these two tools could have fired on the original defect.  What `X3` does is
make a REVERT of that fix red, and pin the two anchors to each other from here
on.  Saying it would have caught the bug it was written after would be exactly
the kind of claim this project does not make.

THE IDENTITIES
--------------
`X1`  THE `.timing` PARSE.  `looptime.read_timing` and
      `boot-timeline.read_timing` are separate implementations of one format.
      For every artefact both can read they must return the same list of
      `(offset, seconds)`.
      🔴 They are not the same code and they differ in THREE ways this corpus
      does not exercise, each of which is a control below:
        * `boot-timeline` sorts its rows; `looptime` does not -- and
          `looptime.at_offset` BREAKS out of its scan at the first row past the
          offset, which is correct only on sorted input (`C1`);
        * on a line that is not `<int> <float>`, `looptime` refuses with the
          file and the line; `boot-timeline` raises `ValueError` out of
          `line.split()` (`C2`);
        * on an empty file, `looptime` refuses; `boot-timeline` returns `[]`
          and lets its caller report `.timing is empty` (`C3`).
      None of the three is reachable from a capture `console-capture.py`
      wrote, which is why they have sat there.  They are recorded as a
      divergence rather than repaired, because repairing one tool to match the
      other is a decision about which behaviour is right and that is not this
      file's to make.

`X2`  THE OFFSET -> TIME LOOKUP.  `looptime.at_offset` is a linear scan with an
      early break; `boot-timeline.t_of` is `bisect_right - 1`.  For every byte
      offset they must return the same timestamp -- including 0, the last byte,
      one past the end, and a negative offset, where both must return `None`.

`X3`  THE PUBLISHED INTERVAL, and it is an EXACT identity rather than a
      tolerance.  `boot-timeline`'s `artifact` anchors on the CR of
      `\\r\\nBooting`; `looptime`'s `lead_to_boot` anchors on the `B`.  So the
      two are two bytes apart and

          lead_to_boot - artifact  ==  at_offset(d0 + 2) - at_offset(d0)

      exactly -- zero when one `read()` delivered both bytes, and exactly the
      inter-read gap when it did not.  Nothing here is allowed to be "close
      enough": a tolerance is where a 2 ms anchor error hides.

WHY THE SWEEP DECLARES NO POPULATION SIZE
-----------------------------------------
`test-boot-timeline`'s `B2` hardcoded *N cold, M warm* and went red on GitHub
three seatings running, because a seating adds captures and the count moves.
This sweep asserts PROPERTIES and reports counts; the only count it enforces is
a FLOOR -- at least one artefact must reach each identity -- because a sweep
that silently compares nothing prints the same "0 disagreements" as a sweep
that compares everything.

Run:  /usr/bin/python3 tools/xcheck.py sweep [--root bench] [-v]
      /usr/bin/python3 tools/xcheck.py --self-test

Exit codes:  0 ok · 1 an identity failed · 2 refused before comparing anything
"""
import argparse
import importlib.util
import os
import sys
import tempfile

VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

# Mutation hooks.  `--self-test` sets these to prove each identity can fail;
# nothing else ever writes them, and `sweep` refuses if any is set.
MUT = {"x1_drop_last": False, "x2_shift": False, "x3_bias": 0.0}


class Refused(Exception):
    pass


def load(fname, modname):
    """Import a tool by path.  `boot-timeline.py` has a hyphen in it."""
    path = os.path.join(TOOLS, fname)
    if not os.path.isfile(path):
        raise Refused("no %s beside this file" % fname)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


LT = load("looptime.py", "_xc_looptime")
BT = load("boot-timeline.py", "_xc_boot_timeline")


# --------------------------------------------------------------- the sides
def side_lt_parse(prefix):
    rows = LT.read_timing(prefix)
    if MUT["x1_drop_last"]:
        rows = rows[:-1]
    return rows


def side_bt_parse(prefix):
    return BT.read_timing(prefix + ".timing")


def side_lt_at(rows, off):
    return LT.at_offset(rows, off)


def side_bt_at(rows, off):
    offs = [r[0] for r in rows]
    if MUT["x2_shift"]:
        off = off + 1
    return BT.t_of(rows, offs, off)[0]


def describe_failure(exc):
    """Two tools failing on one input is agreement only if they fail the same
    way.  A refusal naming the file and a ValueError out of str.split() are
    not the same event, and calling both 'it errored' is how a divergence
    stays invisible."""
    return "%s: %s" % (type(exc).__name__, exc)


# ------------------------------------------------------------- identity X1
def x1(prefix):
    """-> (verdict, detail).  verdict in AGREE / DIFFER / BOTH-REFUSE."""
    ea = eb = None
    try:
        a = side_lt_parse(prefix)
    except Exception as exc:            # noqa: BLE001 -- the failure IS the datum
        a, ea = None, exc
    try:
        b = side_bt_parse(prefix)
    except Exception as exc:            # noqa: BLE001
        b, eb = None, exc
    if ea is not None or eb is not None:
        if ea is not None and eb is not None:
            if type(ea) is type(eb):
                return "BOTH-REFUSE", describe_failure(ea)
            return "DIFFER", ("different failure modes: looptime %s / "
                              "boot-timeline %s"
                              % (describe_failure(ea), describe_failure(eb)))
        which = "boot-timeline" if ea is None else "looptime"
        other = ea if ea is not None else eb
        return "DIFFER", ("only %s produced rows; the other raised %s"
                          % (which, describe_failure(other)))
    if a == b:
        return "AGREE", "%d row(s)" % len(a)
    if sorted(a) == sorted(b):
        return "DIFFER", ("same %d rows in a different ORDER -- looptime does "
                          "not sort and its at_offset breaks early" % len(a))
    return "DIFFER", "looptime %d row(s), boot-timeline %d row(s)" % (len(a), len(b))


# ------------------------------------------------------------- identity X2
def x2(prefix, rows, nbytes, sample_cap=400):
    """Every offset both sides can be asked about must give one timestamp."""
    offs = sorted({r[0] for r in rows})
    if len(offs) > sample_cap:
        step = len(offs) // sample_cap + 1
        offs = offs[::step] + [offs[-1]]
    probes = [-1, 0, nbytes - 1, nbytes, nbytes + 1000]
    for o in offs:
        probes += [o - 1, o, o + 1]
    bad = []
    for o in sorted(set(probes)):
        ta = side_lt_at(rows, o)
        tb = side_bt_at(rows, o)
        if ta != tb:
            bad.append((o, ta, tb))
    return ("AGREE" if not bad else "DIFFER"), bad, len(set(probes))


# ------------------------------------------------------------- identity X3
def x3(prefix, rows):
    """-> (verdict, detail, residual, gap) or (None, reason, None, None)."""
    log = prefix + ".log"
    raw = open(log, "rb").read()
    bt = BT.analyse(log, "C")
    if bt is None or "error" in bt or bt.get("artifact") is None:
        return None, "boot-timeline reports no artifact interval", None, None
    lt = LT.to_prompt(prefix, LT.DEFAULT_MARKER, LT.BOOT_MARKER)
    if not lt.get("boot_found") or "lead_to_boot" not in lt:
        return None, "looptime reports no lead_to_boot", None, None

    d0 = raw.find(b"\r\n" + BT.BOOTING)
    if d0 < 0:
        return None, "no \\r\\nBooting in the log", None, None
    gap = side_lt_at(rows, d0 + 2) - side_lt_at(rows, d0)
    residual = lt["lead_to_boot"] + MUT["x3_bias"] - bt["artifact"]
    ok = abs(residual - gap) <= 1e-12
    detail = ("lead %.6f  artifact %.6f  residual %.6f  gap(d0,d0+2) %.6f"
              % (lt["lead_to_boot"], bt["artifact"], residual, gap))
    return ("AGREE" if ok else "DIFFER"), detail, residual, gap


# ------------------------------------------------------------------ corpus
def corpus(root):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for f in sorted(files):
            if not f.endswith(".log"):
                continue
            prefix = os.path.join(dirpath, f[:-4])
            if os.path.isfile(prefix + ".timing"):
                out.append(prefix)
    return sorted(out)


def sweep(root, verbose=False, out=sys.stdout):
    if MUT["x1_drop_last"] or MUT["x2_shift"] or MUT["x3_bias"]:
        raise Refused("a mutation hook is set; sweep is for real artefacts only")
    if not os.path.isdir(root):
        raise Refused("no such directory: %s" % root)
    caps = corpus(root)
    if not caps:
        raise Refused("%s holds no .log with a .timing beside it" % root)

    n1 = n1bad = 0
    n2 = n2bad = 0
    n3 = n3bad = 0
    same_read = split_read = 0
    x3rows = []
    failures = []

    for prefix in caps:
        rel = os.path.relpath(prefix, ROOT).replace(os.sep, "/")
        v1, d1 = x1(prefix)
        n1 += 1
        if v1 == "DIFFER":
            n1bad += 1
            failures.append(("X1", rel, d1))
        if v1 != "AGREE":
            continue
        rows = side_lt_parse(prefix)
        nbytes = os.path.getsize(prefix + ".log")
        v2, bad2, nprobe = x2(prefix, rows, nbytes)
        n2 += 1
        if v2 == "DIFFER":
            n2bad += 1
            failures.append(("X2", rel, "%d of %d probe(s) differ, first %r"
                             % (len(bad2), nprobe, bad2[0])))
        v3, d3, residual, gap = x3(prefix, rows)
        if v3 is None:
            continue
        n3 += 1
        if gap == 0.0:
            same_read += 1
        else:
            split_read += 1
        x3rows.append((rel, residual, gap))
        if v3 == "DIFFER":
            n3bad += 1
            failures.append(("X3", rel, d3))

    print("xcheck %s   root=%s" % (VERSION, root), file=out)
    print("", file=out)
    print("  %-4s %-46s %8s %8s" % ("id", "identity", "compared", "differ"),
          file=out)
    print("  %-4s %-46s %8s %8s" % ("--", "--------", "--------", "------"),
          file=out)
    print("  %-4s %-46s %8d %8d" % ("X1", "the .timing parse", n1, n1bad), file=out)
    print("  %-4s %-46s %8d %8d" % ("X2", "the offset -> time lookup", n2, n2bad),
          file=out)
    print("  %-4s %-46s %8d %8d" % ("X3", "lead - artifact == gap(d0, d0+2)",
                                    n3, n3bad), file=out)
    print("", file=out)
    print("  X3's population, split by whether one read() delivered both anchors:",
          file=out)
    print("    both bytes in one read (residual must be exactly 0.0)   %d" % same_read,
          file=out)
    print("    the two bytes straddle a read boundary                  %d" % split_read,
          file=out)
    if verbose and x3rows:
        print("", file=out)
        for rel, residual, gap in x3rows:
            print("      %-44s residual %.6f  gap %.6f" % (rel, residual, gap),
                  file=out)

    # The floor, not an equality: a seating adds captures and a hardcoded
    # population is the class that put three commits red on 2026-08-31.
    floors = [("X1", n1, 1), ("X2", n2, 1), ("X3", n3, 1)]
    empty = [i for i, n, f in floors if n < f]
    print("", file=out)
    if empty:
        print("  REFUSED: %s compared nothing. A sweep with an empty population "
              "prints the same summary as a clean one." % ", ".join(empty), file=out)
        return 2
    if failures:
        print("  %d disagreement(s):" % len(failures), file=out)
        for ident, rel, detail in failures:
            print("    %-3s %-44s %s" % (ident, rel, detail), file=out)
        print("", file=out)
        print("RESULT: two committed instruments disagree about a committed "
              "artefact", file=out)
        return 1
    print("  ok  every identity holds on every artefact both sides could read",
          file=out)
    print("", file=out)
    print("RESULT: %d artefact(s), 3 identities, 0 disagreements -- and the "
          "controls in --self-test are what make that sentence mean something"
          % len(caps), file=out)
    return 0


# --------------------------------------------------------------- self-test
def write_capture(d, name, log_bytes, rows):
    with open(os.path.join(d, name + ".log"), "wb") as fh:
        fh.write(log_bytes)
    with open(os.path.join(d, name + ".timing"), "w", encoding="utf-8") as fh:
        for off, t in rows:
            fh.write("%d %.6f\n" % (off, t))
    return os.path.join(d, name)


def selftest(out=sys.stdout):
    print("xcheck %s --self-test" % VERSION, file=out)
    passed = failed = 0

    def ck(cid, label, expect, got):
        nonlocal passed, failed
        if expect == got:
            print("  ok     %-4s %-52s %s" % (cid, label, got), file=out)
            passed += 1
        else:
            print("  FAIL   %-4s %-52s expected %r, got %r"
                  % (cid, label, expect, got), file=out)
            failed += 1

    # A boot-shaped log: one idle byte, then the device's own CRLF Booting...
    body = (b"\x00" + b"\r\nBooting...\x00chipName: 8196C\r\n"
            b"---RealTek(RTL8196E)\r\nramSize: 32M \r\n<RealTek>")
    d0 = body.find(b"\r\nBooting...")
    assert d0 == 1, d0

    with tempfile.TemporaryDirectory() as d:
        # ---- C6: both anchors inside ONE read -> residual exactly 0.0
        rows_same = [(0, 0.000000), (0 + len(body), 0.500000)]
        p6 = write_capture(d, "same", body, rows_same)
        rows = side_lt_parse(p6)
        v, detail, residual, gap = x3(p6, rows)
        ck("C6", "one read delivers both anchors", ("AGREE", 0.0, 0.0),
           (v, round(residual, 12), round(gap, 12)))

        # ---- C5: the two anchors STRADDLE a read boundary, known gap
        # read 1 delivers bytes 0..1 (the idle byte and the CR); read 2 the rest
        rows_split = [(0, 0.100000), (2, 0.140000), (len(body), 0.900000)]
        p5 = write_capture(d, "split", body, rows_split)
        rows = side_lt_parse(p5)
        v, detail, residual, gap = x3(p5, rows)
        ck("C5", "anchors straddle a read: residual == the gap", ("AGREE", 0.04),
           (v, round(residual, 6)))
        ck("C5b", "and the residual is not zero", True, round(residual, 6) > 0.0)

        # ---- C4: the NEGATIVE control for C1..C3.  Comments and blank lines
        # are handled the same way by both, so not every synthetic input makes
        # them differ -- without this, C1..C3 would only show the checker is
        # trigger-happy.
        with open(p6 + ".timing", "w", encoding="utf-8") as fh:
            fh.write("# a comment\n\n0 0.000000\n\n   \n%d 0.500000\n# tail\n"
                     % len(body))
        ck("C4", "comments and blank lines: both skip them", "AGREE", x1(p6)[0])

        # ---- C1: unsorted rows.  boot-timeline sorts, looptime does not.
        with open(p6 + ".timing", "w", encoding="utf-8") as fh:
            fh.write("%d 0.500000\n0 0.000000\n" % len(body))
        v, detail = x1(p6)
        ck("C1", "rows out of order: the two parses differ", "DIFFER", v)
        ck("C1b", "and it is named as an ORDER difference", True,
           "different ORDER" in detail)

        # ---- C2: a malformed line, and the failure MODES differ
        with open(p6 + ".timing", "w", encoding="utf-8") as fh:
            fh.write("0 0.000000\nthis is not a timing row at all\n")
        v, detail = x1(p6)
        ck("C2", "a malformed line: different failure modes", "DIFFER", v)
        ck("C2b", "and both sides' exception types are named", True,
           "looptime" in detail and "boot-timeline" in detail)

        # ---- C3: an empty .timing
        open(p6 + ".timing", "w", encoding="utf-8").close()
        ck("C3", "an empty .timing: one refuses, one returns []", "DIFFER",
           x1(p6)[0])

        # ---- C7: X2 over a real-shaped row list, unmutated
        p7 = write_capture(d, "lookup", body, rows_split)
        rows = side_lt_parse(p7)
        v2, bad2, nprobe = x2(p7, rows, len(body))
        ck("C7", "the two lookups agree at every probed offset", "AGREE", v2)
        ck("C7b", "and the probe set is not empty", True, nprobe >= 8)
        ck("C7c", "a negative offset gives None on both sides", (None, None),
           (side_lt_at(rows, -1), side_bt_at(rows, -1)))

        # ---- M0: the harness control.  A runner that reports every mutant
        # killed and a runner that is itself broken print the same thing;
        # 2026-08-31 paid for that with test-flashwin-mutants' first run.
        ck("M0", "unmutated: X1/X2/X3 all agree on the fixture",
           ("AGREE", "AGREE", "AGREE"),
           (x1(p5)[0], x2(p5, side_lt_parse(p5), len(body))[0], x3(p5, side_lt_parse(p5))[0]))

        # ---- M1..M3: each identity must be able to go red
        MUT["x3_bias"] = 1e-3
        ck("M1", "X3 red when one side's interval is biased 1 ms", "DIFFER",
           x3(p5, side_lt_parse(p5))[0])
        MUT["x3_bias"] = 0.0

        MUT["x1_drop_last"] = True
        ck("M2", "X1 red when one parse loses a row", "DIFFER", x1(p5)[0])
        MUT["x1_drop_last"] = False

        MUT["x2_shift"] = True
        ck("M3", "X2 red when one lookup is off by one byte", "DIFFER",
           x2(p5, side_lt_parse(p5), len(body))[0])
        MUT["x2_shift"] = False

        # ---- M4: sweep must REFUSE while a hook is set
        MUT["x2_shift"] = True
        try:
            sweep(d, out=open(os.devnull, "w"))
            got = "no refusal"
        except Refused:
            got = "refused"
        MUT["x2_shift"] = False
        ck("M4", "sweep refuses to run with a mutation hook set", "refused", got)

        # ---- C8: an empty corpus is REFUSED, not reported as clean
        with tempfile.TemporaryDirectory() as empty:
            try:
                sweep(empty, out=open(os.devnull, "w"))
                got = "no refusal"
            except Refused:
                got = "refused"
        ck("C8", "a corpus with no captures is refused", "refused", got)

    print("", file=out)
    print("RESULT: %d passed, %d failed" % (passed, failed), file=out)
    return 0 if failed == 0 else 1


def main():
    ap = argparse.ArgumentParser(
        description="cross-tool agreement about one artefact (TOOL-1)")
    ap.add_argument("mode", nargs="?", choices=["sweep"])
    ap.add_argument("--root", default=os.path.join(ROOT, "bench"))
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    try:
        if a.self_test:
            return selftest()
        if a.mode == "sweep":
            return sweep(a.root, a.verbose)
    except Refused as exc:
        print("xcheck: %s" % exc, file=sys.stderr)
        return 2
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
