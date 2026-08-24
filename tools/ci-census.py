#!/usr/bin/env python3
"""ci-census -- make a green build say how many checks it did not run.

Why this exists
---------------
This project's own rule is that a tool reporting `0` is making a claim, and that
every sweep needs a positive control because a tool that cannot fail proves
nothing.  A CI badge is exactly that shape of claim: green means "0 failures",
and 0 failures over a suite that quietly shrank by half is the failure mode the
rule exists to catch.

It is not hypothetical here.  Measured 2026-08-25 on a stock runner with no
`$FWRE_WORK`:

  * `tools/test-hazlint.sh` prints **8 skip lines that stand for 25 cases**, and
    the suite prints 39 case lines where the bench prints 56.  A skip LINE is
    not a skipped CASE, and only the second number is the one a reader wants.
  * `tools/test-rlxprobe.sh` prints **one** skip line -- `everything` -- that
    stands for 45, and then exits 0.
  * `tools/test-opcount.sh` prints a skip line that increments nothing, so its
    own summary reads `14 passed, 0 failed` and is green with a case missing.
  * `tools/test-rlxprobe.sh`, in the shape it had that morning, printed **21**
    case lines against a bench total of 23 when the toolchain was present and
    `stage2.bin` was not: two cases disappeared with neither a FAIL nor a skip
    line.  Nothing that counts skip lines could have seen that.  The arithmetic
    below does, and that is the case this tool exists for.

So the check is arithmetic, not pattern-matching:

    ok + FAIL + sum(covers of every skip printed) == the suite's bench total

`tools/ci-expected.tsv` carries one row per allowed skip, with how many cases
that skip stands for and why it is allowed.  A skip label that is not in the
table turns the build red; so does arithmetic that does not close; so does a
suite that is in the table and produced no output at all.

Usage
-----
    ci-census.py <expected.tsv> <capture-dir> [--only suite,suite]
    ci-census.py --self-test

`<capture-dir>` holds one `<suite>.out` per suite, each the verbatim stdout of
that suite.  `--only` restricts the table to the suites a given CI job ran, so a
job is not marked red for the suites another job owns.
"""

import os
import re
import sys
import tempfile

# A suite the table marks with this label is not run by CI at all, and its
# whole bench total counts as not run.
BENCH_ONLY = "*bench-only*"

OK_RE = re.compile(r"^\s*ok\s{2,}(.*)$")
FAIL_RE = re.compile(r"^\s*FAIL\s{2,}(.*)$")
# A skip line is `  skip   <label padded>  <reason>`.  The label is what the
# table keys on, and it is separated from the reason by two or more spaces --
# every suite here uses a %-Ns pad, so that separation is real and not a guess.
SKIP_RE = re.compile(r"^\s*skip\s{2,}(\S(?:.*?\S)?)\s{2,}(.*)$")
# ...except a skip whose reason is empty, which no suite writes today but which
# would otherwise vanish rather than being reported as unparsable.
SKIP_BARE_RE = re.compile(r"^\s*skip\s{2,}(\S(?:.*?\S)?)\s*$")


def load_table(path):
    """Return {suite: (bench_total, {label: covers}, {label: reason})}."""
    suites = {}
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = [p.strip() for p in line.split("\t") if p.strip() != ""]
            if len(parts) < 4:
                raise SystemExit(
                    f"{path}:{lineno}: need suite/total/label/covers[/reason], "
                    f"tab separated, got {len(parts)} field(s)")
            suite, total, label, covers = parts[0], parts[1], parts[2], parts[3]
            reason = parts[4] if len(parts) > 4 else ""
            entry = suites.setdefault(suite, [int(total), {}, {}])
            if entry[0] != int(total):
                raise SystemExit(
                    f"{path}:{lineno}: {suite} declared with two different "
                    f"bench totals, {entry[0]} and {total}")
            if label != "-":
                entry[1][label] = int(covers)
                entry[2][label] = reason
    return {k: (v[0], v[1], v[2]) for k, v in suites.items()}


def parse_capture(text):
    ok = fails = 0
    skips = []
    unparsable = []
    for line in text.splitlines():
        if OK_RE.match(line):
            ok += 1
            continue
        if FAIL_RE.match(line):
            fails += 1
            continue
        m = SKIP_RE.match(line) or SKIP_BARE_RE.match(line)
        if m:
            skips.append(m.group(1))
            continue
        if re.match(r"^\s*(ok|FAIL|skip)\b", line):
            unparsable.append(line)
    return ok, fails, skips, unparsable


def census(table, capdir, only=None, check_arithmetic=True, out=sys.stdout):
    """Return (red, lines). `red` is True when the build must fail."""
    red = False
    lines = []
    wanted = sorted(table) if only is None else [s for s in sorted(table) if s in only]
    if only is not None:
        for s in only:
            if s not in table:
                lines.append(f"  RED   {s}: --only names a suite that is not in the table")
                red = True

    not_run = 0
    for suite in wanted:
        total, allowed, reasons = table[suite]
        path = os.path.join(capdir, suite + ".out")

        # A suite marked BENCH_ONLY is one CI is not expected to run at all, and
        # the whole of it counts as not run.  It is in the table rather than
        # left out of it because a suite nobody lists is a suite nobody misses:
        # `tools/test-hazlint.sh` is 56 cases and its population control is a
        # 56 KiB vendor bootloader that may not be redistributed, so on a runner
        # it does not skip -- it FAILS 14 cases, because hazlint refuses to
        # report without that control and the refusal is correct.  Leaving it
        # out of CI is the right call; leaving it out of the ARITHMETIC is how a
        # badge becomes a claim that cannot fail.
        if BENCH_ONLY in allowed:
            if os.path.exists(path):
                lines.append(f"  RED   {suite}: marked {BENCH_ONLY} and yet "
                             f"{suite}.out exists -- one of the two is wrong")
                red = True
                continue
            not_run += total
            lines.append(f"  bench {suite:<24} ran   0/{total:<3} "
                         f"failed 0  not run {total}")
            lines.append(f"        - not run at all: {reasons[BENCH_ONLY]}")
            continue

        if not os.path.exists(path):
            lines.append(f"  RED   {suite}: no {suite}.out -- the suite is in the "
                         f"table and produced no output at all")
            red = True
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            ok, fails, skips, unparsable = parse_capture(fh.read())

        covered = 0
        bad_labels = []
        for label in skips:
            if label in allowed:
                covered += allowed[label]
            else:
                bad_labels.append(label)

        status = "ok"
        notes = []
        if fails:
            status, red = "RED", True
            notes.append(f"{fails} FAILED")
        if bad_labels:
            status, red = "RED", True
            for lb in bad_labels:
                notes.append(f"UNEXPECTED-SKIP {lb!r}")
        if unparsable:
            status, red = "RED", True
            notes.append(f"{len(unparsable)} line(s) start with ok/FAIL/skip and "
                         f"did not parse")
        if check_arithmetic and ok + fails + covered != total:
            status, red = "RED", True
            notes.append(f"CENSUS-MISMATCH {ok}+{fails}+{covered} != {total} -- "
                         f"cases went missing with neither a FAIL nor a skip line")

        not_run += covered
        lines.append(f"  {status:<5} {suite:<24} ran {ok:>3}/{total:<3} "
                     f"failed {fails}  not run {covered}"
                     + ("   " + "; ".join(notes) if notes else ""))
        for label in skips:
            if label in allowed:
                lines.append(f"        - not run: {label} "
                             f"({allowed[label]} case(s)) -- {reasons[label]}")

    lines.append("")
    lines.append(f"  NOT RUN IN THIS JOB: {not_run} case(s), every one of them "
                 f"named above.")
    lines.append("  A green result here means the cases that ran passed AND the "
                 "cases that did not run are the ones this repository")
    lines.append("  has already decided cannot run without a 56 KiB vendor "
                 "bootloader that may not be redistributed.")
    for ln in lines:
        print(ln, file=out)
    return red, lines


# --------------------------------------------------------------------------
# The controls.  Each one produces a finding the tool would otherwise miss, and
# each one can fail.
# --------------------------------------------------------------------------

TABLE = (
    "# suite\tbench_total\tallowed_skip_label\tcovers\treason\n"
    "alpha\t10\t-\t0\t-\n"
    "beta\t10\tneeds the moon\t4\tthe moon is not committable\n"
)


def _write(d, name, text):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def self_test():
    import io
    passed = failed = 0

    def ck(name, got, want):
        nonlocal passed, failed
        if got == want:
            print(f"  ok    {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}: red={got}, expected {want}")
            failed += 1

    with tempfile.TemporaryDirectory() as d:
        tpath = _write(d, "t.tsv", TABLE)
        table = load_table(tpath)
        cap = os.path.join(d, "cap")
        os.makedirs(cap)
        buf = io.StringIO()

        clean = "".join(f"  ok    case {i}\n" for i in range(10))
        skipped = ("".join(f"  ok    case {i}\n" for i in range(6))
                   + "  skip   needs the moon                 not present\n")

        # C1 a suite that ran everything is green
        _write(cap, "alpha.out", clean)
        _write(cap, "beta.out", skipped)
        red, _ = census(table, cap, out=buf)
        ck("C1 all cases run, one allowed skip covering the rest -> green", red, False)

        # C2 a FAIL line is red
        _write(cap, "alpha.out", clean.replace("  ok    case 3", "  FAIL  case 3", 1))
        red, _ = census(table, cap, out=buf)
        ck("C2 one FAIL line -> red", red, True)
        _write(cap, "alpha.out", clean)

        # C3 an unlisted skip label is red -- the whole point of the allow-list
        _write(cap, "beta.out", skipped + "  skip   needs a spare unit           none exists\n")
        red, _ = census(table, cap, out=buf)
        ck("C3 a skip label that is not in the table -> red", red, True)

        # C4 THE ONE THAT CATCHES VANISHING CASES: arithmetic that does not close
        _write(cap, "beta.out", "".join(f"  ok    case {i}\n" for i in range(5))
               + "  skip   needs the moon                 not present\n")
        red, _ = census(table, cap, out=buf)
        ck("C4 5 ok + 4 covered != 10 -> red, with no FAIL and no bad label", red, True)

        # C4b the mutation: with the arithmetic check removed, C4 goes green.
        # That is what makes C4 a test of the arithmetic and not of something else.
        red, _ = census(table, cap, check_arithmetic=False, out=buf)
        ck("C4b the same input with the arithmetic disabled -> green, so C4 tests it",
           red, False)
        _write(cap, "beta.out", skipped)

        # C5 a suite in the table that produced no output at all
        os.remove(os.path.join(cap, "alpha.out"))
        red, _ = census(table, cap, out=buf)
        ck("C5 a suite in the table with no .out -> red, not silently absent", red, True)
        _write(cap, "alpha.out", clean)

        # C6 --only naming a suite the table does not have
        red, _ = census(table, cap, only={"alpha", "gamma"}, out=buf)
        ck("C6 --only names a suite the table does not carry -> red", red, True)

        # C7 a malformed ok/FAIL/skip line is not silently dropped
        _write(cap, "alpha.out", clean.replace("  ok    case 3", "  skip", 1))
        red, _ = census(table, cap, out=buf)
        ck("C7 a `skip` with no label at all -> red rather than ignored", red, True)
        _write(cap, "alpha.out", clean)

        # C9 a bench-only suite is counted as wholly not run, and is green
        t2 = _write(d, "t2.tsv", TABLE
                    + "gamma\t7\t*bench-only*\t7\tneeds a file that cannot be committed\n")
        table2 = load_table(t2)
        red, out_lines = census(table2, cap, out=buf)
        ck("C9 a *bench-only* suite with no .out -> green", red, False)
        ck("C9b and its cases are in the not-run total",
           any("NOT RUN IN THIS JOB: 11" in ln for ln in out_lines), True)

        # C10 ... but if it DID produce output, the table and reality disagree
        _write(cap, "gamma.out", "  ok    case 0\n")
        red, _ = census(table2, cap, out=buf)
        ck("C10 *bench-only* plus a real .out -> red", red, True)
        os.remove(os.path.join(cap, "gamma.out"))

        # C8 the table itself must refuse two different totals for one suite
        bad = _write(d, "bad.tsv", TABLE + "alpha\t11\t-\t0\t-\n")
        try:
            load_table(bad)
            ck("C8 two bench totals for one suite -> refused", False, True)
        except SystemExit:
            ck("C8 two bench totals for one suite -> refused", True, True)

    print()
    print(f"  {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main(argv):
    if argv[:1] == ["--self-test"]:
        return self_test()
    only = None
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--only":
            only = set(argv[i + 1].split(","))
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if len(args) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    table = load_table(args[0])
    red, _ = census(table, args[1], only=only)
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
