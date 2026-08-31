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

# EXACTLY two leading spaces, not `^\s*`.
#
# Every suite in this repository prints its case lines with a two-space indent,
# measured across all twelve captures on 2026-08-27. A tool a suite INVOKES may
# print lines of the same shape at a deeper indent -- `tools/test-rlxprobe.sh`
# re-indents `tools/hazlint`'s twelve controls into its own stdout by twelve
# spaces -- and `^\s*` counted those as cases of the outer suite. Measured on
# the bench machine with the cross compiler present and $FWRE_WORK empty, that
# read test-rlxprobe as 116 ok / 107 FAIL against a bench total of 202 and
# turned the census red for a reason that was not a missing case.
#
# It never fired in CI, because CI deliberately does not install the cross
# compiler and the suite then prints one skip line. That is what makes it worth
# recording rather than shrugging at: the configuration `ci-expected.tsv`
# documents in that suite's own row -- 101 ok / 101 FAIL -- was one this tool
# could not reproduce, so the number in the table had no instrument behind it.
# C11 is the control.
OK_RE = re.compile(r"^ {2}ok\s{2,}(.*)$")
FAIL_RE = re.compile(r"^ {2}FAIL\s{2,}(.*)$")
# A skip line is `  skip   <label padded>  <reason>`.  The label is what the
# table keys on, and it is separated from the reason by two or more spaces --
# every suite here uses a %-Ns pad, so that separation is real and not a guess.
SKIP_RE = re.compile(r"^ {2}skip\s{2,}(\S(?:.*?\S)?)\s{2,}(.*)$")
# ...except a skip whose reason is empty, which no suite writes today but which
# would otherwise vanish rather than being reported as unparsable.
SKIP_BARE_RE = re.compile(r"^ {2}skip\s{2,}(\S(?:.*?\S)?)\s*$")
# ...and the same anchor on the unparsable check, or a nested tool's lines would
# stop being counted and start being reported as malformed instead.
UNPARSABLE_RE = re.compile(r"^ {2}(ok|FAIL|skip)\b")


def load_table(path):
    """Return {suite: (bench_total, {label: covers}, {label: reason})}, declared.

    A `# not-run-total: N` header is read as DATA, not as a comment.  Before
    2026-08-29 the expected total lived only in a prose comment in
    `.github/workflows/ci.yml`, and nothing compared it to anything: 量, the
    green run of 2026-08-28 14:18 printed **373** while that comment said
    **362**, so it had been wrong by 11 for at least a day, in the file whose
    own header spends forty lines warning about "a number that was true once".
    A total that is checked is a total that cannot do that.
    """
    suites = {}
    declared_total = None
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if line.lstrip().startswith("# not-run-total:"):
                declared_total = int(line.split(":", 1)[1].strip())
                continue
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
    out = {k: (v[0], v[1], v[2]) for k, v in suites.items()}

    # 🔴 C17/C18 -- THE TABLE'S OWN ARITHMETIC, checked before any capture is
    # read.  量 2026-08-31, CI run 33365083894: `test-rlxprobe`'s total was
    # raised 202 -> 206 and its `everything` row's COVERS column was left at
    # 202, so the census reported `0+0+202 != 206` on the runner and the
    # not-run-total came out 4 short.  **The bench cannot see that class**: on
    # this machine the suite RUNS, prints no skip line, and the covers column is
    # never used -- the same blindness `test-kbuild-cflags`' C1 has.  These two
    # checks read only the table, so they fire in every configuration.
    #
    # ⚠️ **A SUITE'S SKIP ROWS ARE ALTERNATIVES, NOT ADDITIVE**, and the first
    # version of this check summed them.  量 2026-08-31, on the first run of
    # C19: `test-vendor-tripwire` declares `the vendor trees` covering all 32,
    # `T10 the incident's own binary` covering 2 and `T13 default discovery`
    # covering 2 -- 36 against a total of 32.  Nothing is wrong with it.  Which
    # rows fire depends on the CONFIGURATION: with no vendor drop at all the
    # first one stands the whole suite down; on a runner that has the drops but
    # no `--live`, the other two fire and cover 4.  So the sum is not a quantity
    # this table ever claims.  **Per row is what is checkable.**
    for suite, (total, labels, _reasons) in out.items():
        for label, covers in labels.items():
            if covers > total:
                raise SystemExit(
                    f"{path}: {suite}'s skip `{label}` covers {covers} case(s) "
                    f"out of a total of {total} -- one skip cannot stand down "
                    f"more cases than the suite has")
        if "everything" in labels and labels["everything"] != total:
            raise SystemExit(
                f"{path}: {suite}'s allowed skip is `everything` but it covers "
                f"{labels['everything']} of {total} case(s). Those two numbers "
                f"move together by definition, and on a machine where the suite "
                f"RUNS nothing compares them -- which is how 2026-08-31 pushed "
                f"a table that was 4 short.")
    return out, declared_total


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
        if UNPARSABLE_RE.match(line):
            unparsable.append(line)
    return ok, fails, skips, unparsable


def census(table, capdir, only=None, check_arithmetic=True, out=sys.stdout, declared_total=None):
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
        # `tools/test-hazlint.sh` is 96 cases and its population control is a
        # 56 KiB vendor bootloader that may not be redistributed, so on a runner
        # it does not skip -- it FAILS 30 of them, because hazlint refuses to
        # report without that control and the refusal is correct.  Leaving it
        # out of CI is the right call; leaving it out of the ARITHMETIC is how a
        # badge becomes a claim that cannot fail.
        #
        # Those two numbers read 56 and 14 until 2026-08-27, and the 14 was
        # wrong on the day it was written or soon after: HEAD's own pair
        # measured 26.  A comment is not a control.  This one is prose about a
        # suite this file deliberately does not run, so there is nothing here
        # to check it -- which is the reason it now carries the date it was
        # measured, the same rule `ci-expected.tsv` already runs on.
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
    if declared_total is not None and declared_total != not_run:
        red = True
        lines.append(f"  \033[31mNOT-RUN-TOTAL MISMATCH\033[0m: the table "
                     f"declares {declared_total} and this job did not run "
                     f"{not_run}.")
        lines.append("  A suite grew or shrank and the total nobody checks did "
                     "not follow. Update `# not-run-total:`")
    elif declared_total is None:
        lines.append("  (the table declares no `# not-run-total:`, so this "
                     "number is not checked against anything)")
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
        table, _ = load_table(tpath)
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

        # C15 the NOT-RUN total, declared in the table and CHECKED.
        # Before 2026-08-29 this number lived only in a prose comment in
        # ci.yml, and 量: the green run of 2026-08-28 14:18 printed 373 while
        # that comment said 362. Nothing compared them, so it had been wrong
        # for at least a day. Both directions are asserted here, because a
        # check that only fires when the total is too LOW would pass on a
        # suite that quietly shrank -- which is this tool's whole subject.
        red, out_lines = census(table, cap, out=buf, declared_total=4)
        ck("C15 the declared not-run total matches -> green", red, False)
        red, out_lines = census(table, cap, out=buf, declared_total=3)
        ck("C15 declared too LOW -> red", red, True)
        ck("C15 and it says which two numbers disagree", True,
           any("NOT-RUN-TOTAL MISMATCH" in ln for ln in out_lines))
        red, _ = census(table, cap, out=buf, declared_total=99)
        ck("C15 declared too HIGH -> red", red, True)
        red, out_lines = census(table, cap, out=buf, declared_total=None)
        ck("C15 no declaration -> green, and it SAYS the number is unchecked",
           any("not checked against anything" in ln for ln in out_lines), True)

        # C5 a suite in the table that produced no output at all
        os.remove(os.path.join(cap, "alpha.out"))
        red, _ = census(table, cap, out=buf)
        ck("C5 a suite in the table with no .out -> red, not silently absent", red, True)
        _write(cap, "alpha.out", clean)

        # C16 -- the not-run-total check must not fire under --only, and
        # must still fire without it.  Both directions, because a fix that
        # disabled the check outright would pass the first half alone.
        red, out_lines = census(table, cap, only={"alpha"},
                                out=buf, declared_total=None)
        ck("C16 --only: no NOT-RUN-TOTAL line at all",
           any("NOT-RUN-TOTAL" in ln for ln in out_lines), False)
        red, out_lines = census(table, cap, out=buf, declared_total=99)
        ck("C16 and without --only it still fires",
           any("NOT-RUN-TOTAL MISMATCH" in ln for ln in out_lines), True)

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
        table2, _ = load_table(t2)
        red, out_lines = census(table2, cap, out=buf)
        ck("C9 a *bench-only* suite with no .out -> green", red, False)
        ck("C9b and its cases are in the not-run total",
           any("NOT RUN IN THIS JOB: 11" in ln for ln in out_lines), True)

        # C10 ... but if it DID produce output, the table and reality disagree
        _write(cap, "gamma.out", "  ok    case 0\n")
        red, _ = census(table2, cap, out=buf)
        ck("C10 *bench-only* plus a real .out -> red", red, True)
        os.remove(os.path.join(cap, "gamma.out"))

        # C11 a tool a suite INVOKES prints lines of the same shape at a deeper
        # indent, and they are not cases of the suite. `tools/test-rlxprobe.sh`
        # re-indents hazlint's twelve controls into its stdout by twelve spaces;
        # with `^\s*` this fixture reads 12 ok and the arithmetic goes red for a
        # reason that is not a missing case. Both halves are asserted, because a
        # parser that dropped BOTH indents would also pass the first half.
        nested = ("".join(f"  ok    case {i}\n" for i in range(10))
                  + "            ok    K4  population control  a nested tool\n"
                  + "            FAIL  K9  and one of its controls is red\n")
        _write(cap, "alpha.out", nested)
        red, _ = census(table, cap, out=buf)
        ck("C11 a nested tool's deeper-indented ok/FAIL lines are not cases", red, False)
        ok_n, fail_n, _, unp = parse_capture(nested)
        ck("C11b and the outer suite's own ten still are", (ok_n, fail_n, unp), (10, 0, []))
        _write(cap, "alpha.out", clean)

        # C8 the table itself must refuse two different totals for one suite
        bad = _write(d, "bad.tsv", TABLE + "alpha\t11\t-\t0\t-\n")
        try:
            load_table(bad)
            ck("C8 two bench totals for one suite -> refused", False, True)
        except SystemExit:
            ck("C8 two bench totals for one suite -> refused", True, True)

        # 🔴 C17/C18 -- the table's OWN arithmetic, and both exist because of
        # CI run 33365083894.  `test-rlxprobe`'s total went 202 -> 206 and its
        # `everything` row's covers column stayed at 202; the census went red on
        # the runner and the bench could not see it, because on a machine where
        # the suite RUNS the covers column is never read.  These two need no
        # capture at all -- they read the table -- so they fire everywhere.
        b2 = _write(d, "bad2.tsv",
                    "# suite\tbench_total\tallowed_skip_label\tcovers\treason\n"
                    "delta\t10\teverything\t7\tthe whole suite stands down\n")
        try:
            load_table(b2)
            ck("C17 `everything` covering fewer than the total -> refused",
               False, True)
        except SystemExit:
            ck("C17 `everything` covering fewer than the total -> refused",
               True, True)

        # C17b the positive control: `everything` that DOES cover the total must
        # be accepted, or C17 would be satisfied by refusing every table.
        g2 = _write(d, "good2.tsv",
                    "# suite\tbench_total\tallowed_skip_label\tcovers\treason\n"
                    "delta\t10\teverything\t10\tthe whole suite stands down\n")
        try:
            load_table(g2)
            ck("C17b and `everything` covering all of them is accepted",
               True, True)
        except SystemExit:
            ck("C17b and `everything` covering all of them is accepted",
               False, True)

        # C18 ONE skip row may not cover more cases than the suite has.
        # 🔴 The first version of this SUMMED a suite's rows, and C19 refuted it
        # on its first run: `test-vendor-tripwire` legitimately declares three
        # ALTERNATIVE skips -- 32 + 2 + 2 = 36 against a total of 32 -- because
        # which one fires depends on the configuration. Per row is checkable;
        # the sum is not a quantity this table ever claims. C18b is that shape.
        b3 = _write(d, "bad3.tsv",
                    "# suite\tbench_total\tallowed_skip_label\tcovers\treason\n"
                    "eps\t10\tfirst\t11\t-\n")
        try:
            load_table(b3)
            ck("C18 one skip covering more than the suite has -> refused",
               False, True)
        except SystemExit:
            ck("C18 one skip covering more than the suite has -> refused",
               True, True)

        # C18b its positive control, and it is the shape C18's first version
        # got wrong: two ALTERNATIVE skips that sum past the total are fine.
        g3 = _write(d, "good3.tsv",
                    "# suite\tbench_total\tallowed_skip_label\tcovers\treason\n"
                    "eps\t10\tfirst\t10\t-\n"
                    "eps\t10\tsecond\t3\t-\n")
        try:
            load_table(g3)
            ck("C18b alternative skips summing past the total are accepted",
               True, True)
        except SystemExit:
            ck("C18b alternative skips summing past the total are accepted",
               False, True)

        # C19 🔴 THE REAL TABLE, not a fixture. C17/C18 above prove the checks
        # work; this one puts `tools/ci-expected.tsv` itself through them, which
        # is the thing that was actually wrong on 2026-08-31.
        real = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ci-expected.tsv")
        try:
            load_table(real)
            ck("C19 the repository's own ci-expected.tsv passes both",
               True, True)
        except SystemExit as e:
            print(f"        {e}")
            ck("C19 the repository's own ci-expected.tsv passes both",
               False, True)

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
    table, declared = load_table(args[0])
    # 🔴 The not-run-total check belongs to a WHOLE-TABLE census and to
    # nothing else.  量 2026-08-30: `CLAUDE.md`'s own pre-push step is
    # `--only <the suites you touched>`, and on the machine the push happens
    # from -- which has $FWRE_WORK and so runs everything -- that command
    # could never go green, because `not-run-total` describes a RUNNER.
    # A documented procedure that cannot pass is one nobody follows, or one
    # whose red everybody learns to read past.  `C16` is the control.
    red, _ = census(table, args[1], only=only,
                    declared_total=None if only else declared)
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
