#!/usr/bin/env python3
"""emueq -- the checker behind `R1C-1-c`.

`R1C-1` (`docs/isa-prior-art.md` § 9.3) decides that `R1c` runs on rlxfw's own
image rather than on the vendor's, and the whole decision rests on one measured
sentence: **rlxfw's kernel and the vendor's have the same emulation surface.**

That sentence can stop being true silently.  Somebody adds one line to
`config/rlxfw-kernel.delta`, the line happens to name a symbol that gates code
on `arch/rlx`'s exception path, and every published number in § 9.2.1 becomes
wrong with nothing going red.  `R1C-1-c` is written as a refutation condition
and it says in terms that it is *not a promise, it is a checker*.  This is it.

WHAT IT ASSERTS, and both directions matter
-------------------------------------------
  E1  every symbol that is BOTH in `config/rlxfw-kernel.delta` AND flagged as
      naming code on the exception path must appear in `ALLOW` below, with a
      reason.  A new one is a finding.
  E2  every `ALLOW` entry must still be in the delta.  An entry that is no
      longer needed is a finding, so the allow-list cannot accrete unreported --
      the shape `cardcheck`'s `B10` already uses on its own exemptions.
  E3  every `ALLOW` entry must still be flagged as on the exception path.  If a
      refresh reclassifies it, the exemption is stale and says nothing.
  E4  the delta's symbol column and the table's symbol column must both parse;
      a row that does not is a REFUSAL, not a pass.

WHY THE TABLE IS COMMITTED RATHER THAN SWEPT
--------------------------------------------
`src-vendor/` is a symlink into `$FWRE_WORK`, so it is DANGLING in CI and a
sweep of the vendor tree cannot run there.  The same split `isa-census.tsv` and
`isacensus` already use: `refresh` derives the table at the desk from the pinned
drop, `check` reads the committed table and runs anywhere.  A stale table is not
silent either -- `refresh` rewrites it and the diff is the report.

WHAT IT DOES NOT ASSERT, stated rather than left to be found
------------------------------------------------------------
  * The table is built from symbol NAMES appearing in `arch/rlx`'s own sources.
    A symbol that changes the behaviour of a function `arch/rlx` calls, without
    being named under `arch/rlx`, is outside it.  `config/emu-path-symbols.tsv`
    says so in its own header.
  * `exc_path` is decided by FILE, from a list in `refresh`, so that the
    classification is a property of the tree rather than of anyone's judgement
    about a particular `#ifdef`.  Adding a file to that list is a code change
    with a diff, which is the point.
  * It says nothing about the vendor's SHIPPED binary, whose configuration is
    unrecoverable -- `# CONFIG_IKCONFIG is not set`, § 9.2.1 item 3.

Exit codes: 0 clean, 1 a finding, 3 REFUSED.
"""

import io
import os
import sys
import tempfile

VERSION = "1.0"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "config", "emu-path-symbols.tsv")
DELTA = os.path.join(ROOT, "config", "rlxfw-kernel.delta")

# Files that ARE the exception/emulation path.  Used by `refresh` only; `check`
# reads the flag the table carries, so the two cannot drift without a diff.
EXC_FILES = (
    "arch/rlx/kernel/traps.c",
    "arch/rlx/kernel/unaligned.c",
    "arch/rlx/kernel/genex.S",
    "arch/rlx/kernel/process.c",
    "arch/rlx/kernel/syscall.c",
    "arch/rlx/kernel/branch.c",
)

# The population `refresh` sweeps.
SRC_GLOBS = ("arch/rlx/kernel/*.c", "arch/rlx/kernel/*.S",
             "arch/rlx/mm/*.c", "arch/rlx/mm/*.S")

# ---------------------------------------------------------------------------
# The allow-list.  One entry per symbol that is in the delta AND on the
# exception path.  A reason is mandatory and is checked for length, because an
# exemption with no reason is an exemption nobody can review.
# ---------------------------------------------------------------------------
ALLOW = {
    "CONFIG_RTL_WTDOG":
        "y -> n.  Four sites, and none is an emulation function: "
        "rlx-cevt.c:31 and :151 are the vendor tick handler's watchdog kick, "
        "and traps.c:316 and :534 are inside die() and do_bp() -- the first "
        "sets a fault flag, the second adds a die(\"Oops\") for bcode 7 "
        "(integer divide by zero).  do_bp handles `break`, and 量 `break` and "
        "`syscall` appear in neither the 45-row census nor the 75-row payload "
        "table, so no encoding R1c issues can enter it.  The residual is the "
        "HARNESS rather than a row -- gcc emits `break 7` for integer division "
        "by zero -- and that is `R1C-1-b`'s objdump gate, not this one's.",
}

MIN_REASON = 80


class Refused(Exception):
    pass


def read_text(path):
    if not os.path.exists(path):
        raise Refused("%s does not exist" % os.path.relpath(path, ROOT))
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_table(text, where="table"):
    """config/emu-path-symbols.tsv -> {symbol: (n_files, exc_path, files)}"""
    rows = {}
    lines = [l for l in text.split("\n") if l.strip() and not l.startswith("#")]
    if not lines:
        raise Refused("%s is empty" % where)
    head = lines[0].split("\t")
    want = ["symbol", "n_files", "exc_path", "files"]
    if head != want:
        raise Refused("%s header is %r, want %r" % (where, head, want))
    for i, line in enumerate(lines[1:], start=2):
        f = line.split("\t")
        if len(f) != 4:
            raise Refused("%s row %d has %d fields, want 4" % (where, i, len(f)))
        sym, n, exc, files = f[0], f[1], f[2], f[3]
        if not sym.startswith("CONFIG_"):
            raise Refused("%s row %d: %r is not a CONFIG_ symbol" % (where, i, sym))
        if exc not in ("y", "n"):
            raise Refused("%s row %d: exc_path is %r, want y or n" % (where, i, exc))
        if not n.isdigit():
            raise Refused("%s row %d: n_files is %r" % (where, i, n))
        if sym in rows:
            raise Refused("%s row %d: %s appears twice" % (where, i, sym))
        rows[sym] = (int(n), exc, files)
    return rows


def parse_delta(text, where="delta"):
    """config/rlxfw-kernel.delta -> {symbol: (action, frm, to)}"""
    out = {}
    n = 0
    for i, line in enumerate(text.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        n += 1
        f = line.split("\t")
        if len(f) < 2:
            raise Refused("%s line %d has %d tab-separated field(s), want at "
                          "least 2" % (where, i, len(f)))
        sym = f[1].strip()
        if not sym.startswith("CONFIG_"):
            raise Refused("%s line %d: column 2 is %r, not a CONFIG_ symbol"
                          % (where, i, sym))
        out[sym] = (f[0].strip(), f[2] if len(f) > 2 else "",
                    f[3] if len(f) > 3 else "")
    if n == 0:
        raise Refused("%s carries no data line" % where)
    return out


def check(table_text, delta_text, allow=None):
    """Returns (findings, stats).  Pure -- the self-test drives it on fixtures."""
    allow = ALLOW if allow is None else allow
    table = parse_table(table_text)
    delta = parse_delta(delta_text)
    findings = []

    exc = set(s for s, v in table.items() if v[1] == "y")
    inter = sorted(set(delta) & exc)

    for sym in inter:                                             # E1
        if sym not in allow:
            findings.append(
                "E1 %s is in the delta (%s) and names code on the exception "
                "path (%s) and is not allowed. Either it does not belong in "
                "the delta, or R1C-1's equivalence argument has to be re-taken "
                "-- docs/isa-prior-art.md section 9.2.1 item 1."
                % (sym, delta[sym][0], table[sym][2]))
        elif len(allow[sym]) < MIN_REASON:
            findings.append(
                "E1 %s is allowed with a %d-character reason; an exemption "
                "shorter than %d characters is one nobody can review"
                % (sym, len(allow[sym]), MIN_REASON))

    for sym in sorted(allow):                                     # E2
        if sym not in delta:
            findings.append(
                "E2 %s is on the allow-list and is no longer in the delta. "
                "An allow-list that outlives what it excuses grows without "
                "anyone reading it." % sym)
            continue
        if sym not in table:                                      # E3a
            findings.append(
                "E3 %s is on the allow-list and is not in the symbol table at "
                "all -- refresh the table, or the exemption covers nothing"
                % sym)
        elif table[sym][1] != "y":                                # E3b
            findings.append(
                "E3 %s is on the allow-list but the table no longer flags it "
                "as on the exception path. The exemption is stale and says "
                "nothing." % sym)

    stats = {
        "table_rows": len(table),
        "exc_rows": len(exc),
        "delta_rows": len(delta),
        "intersection": len(inter),
        "allowed": len(allow),
        "intersection_syms": inter,
    }
    return findings, stats


# ---------------------------------------------------------------------------
def cmd_population():
    table = parse_table(read_text(TABLE))
    delta = parse_delta(read_text(DELTA))
    exc = sorted(s for s, v in table.items() if v[1] == "y")
    print("emueq %s -- population" % VERSION)
    print("  symbols named in arch/rlx's own sources : %d" % len(table))
    print("  of those, on the exception path         : %d" % len(exc))
    print("  symbol lines in rlxfw-kernel.delta      : %d" % len(delta))
    print("  intersection                            : %d"
          % len(set(delta) & set(exc)))
    print()
    print("  the exception path, by symbol:")
    for s in exc:
        mark = "  <-- IN THE DELTA" if s in delta else ""
        print("    %-28s %s%s" % (s, table[s][2], mark))
    return 0


def cmd_check():
    findings, st = check(read_text(TABLE), read_text(DELTA))
    print("emueq %s -- check" % VERSION)
    print("  %d symbol(s) in the table, %d on the exception path, "
          "%d in the delta" % (st["table_rows"], st["exc_rows"], st["delta_rows"]))
    print("  intersection: %d -- %s"
          % (st["intersection"], ", ".join(st["intersection_syms"]) or "(none)"))
    print("  allow-list  : %d" % st["allowed"])
    if findings:
        print()
        for f in findings:
            print("  FAIL [%s]" % f)
        print()
        print("RESULT: %d finding(s)" % len(findings))
        return 1
    print()
    print("  ok  no configuration difference of rlxfw's reaches arch/rlx's "
          "exception path except the one that is allowed, and the allow-list "
          "excuses nothing that is gone")
    return 0


def cmd_refresh(kroot):
    """Desk only.  Re-derives the table from the pinned vendor drop."""
    import glob
    import re
    if not os.path.isdir(kroot):
        raise Refused("kernel root %s does not exist -- refresh runs at the "
                      "desk, against the pinned drop, and cannot run in CI "
                      "where src-vendor is a dangling symlink" % kroot)
    files = []
    for g in SRC_GLOBS:
        files.extend(sorted(glob.glob(os.path.join(kroot, g))))
    if not files:
        raise Refused("no source file matched %s under %s"
                      % (", ".join(SRC_GLOBS), kroot))
    pat = re.compile(r"CONFIG_[A-Z0-9_]+")
    per = {}
    for full in files:
        rel = os.path.relpath(full, kroot).replace(os.sep, "/")
        with io.open(full, encoding="utf-8", errors="replace") as fh:
            for sym in set(pat.findall(fh.read())):
                per.setdefault(sym, set()).add(rel)
    out = ["# Every CONFIG_ symbol NAMED in arch/rlx's own sources, with the",
           "# files that name it.  Derived by `tools/emueq.py refresh`; the",
           "# checker that reads it is `tools/emueq.py check`, and what it is",
           "# for is `docs/isa-prior-art.md` section 9.3's `R1C-1-c`.",
           "#",
           "# exc_path is decided by FILE, not by judgement about a particular",
           "# #ifdef.  The list is EXC_FILES in tools/emueq.py, so changing it",
           "# is a code change with a diff.",
           "#",
           "# LIMIT, stated rather than left to be found: this is a sweep of",
           "# symbol NAMES under arch/rlx.  A symbol that changes the behaviour",
           "# of a function arch/rlx calls, without being named under arch/rlx,",
           "# is outside this table and outside the check that reads it.",
           "#",
           "symbol\tn_files\texc_path\tfiles"]
    n_exc = 0
    for sym in sorted(per):
        fl = sorted(per[sym])
        exc = "y" if any(f in EXC_FILES for f in fl) else "n"
        if exc == "y":
            n_exc += 1
        out.append("%s\t%d\t%s\t%s" % (sym, len(fl), exc, ",".join(fl)))
    tmp = TABLE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    os.replace(tmp, TABLE)
    print("emueq %s -- refresh" % VERSION)
    print("  swept %d source file(s) under %s" % (len(files), kroot))
    print("  wrote %d symbol(s), %d on the exception path, to %s"
          % (len(per), n_exc, os.path.relpath(TABLE, ROOT)))
    # \U0001F534 The `files` column is path-shaped, so every refresh CITES vendor
    # source as far as `tools/ledgerscan.py` is concerned -- and on 2026-09-14
    # that turned CI red on `arch/rlx/kernel/irq.c`, a file nobody opened.  The
    # coupling was invisible; the tool that causes it now says so out loud, and
    # names the paths, so the operator does not have to notice.
    paths = sorted({p for fl in per.values() for p in fl})
    print()
    print("  \U0001F534 this table CITES %d vendor source path(s). `ledgerscan` "
          "cannot tell" % len(paths))
    print("     a generated enumeration from a file somebody read, so run")
    print("       /usr/bin/python3 tools/ledgerscan.py check")
    print("     before committing. A path in an in-scope domain that is not in")
    print("     docs/blind-write-ledger.md turns CI red, and the desk sweep")
    print("     cannot catch it because this file is written after the sweep.")
    return 0


# ---------------------------------------------------------------------------
def self_test():
    table = read_text(TABLE)
    delta = read_text(DELTA)
    results = []

    def case(name, fn):
        try:
            fn()
        except AssertionError as exc:
            results.append((False, name, str(exc)))
        except Exception as exc:                     # noqa: BLE001
            results.append((False, name, "%s: %s" % (type(exc).__name__, exc)))
        else:
            results.append((True, name, ""))

    def fires(t, d, prefix, allow=None):
        f, _ = check(t, d, allow)
        hits = [x for x in f if x.startswith(prefix)]
        assert hits, "expected a %s finding, got %r" % (prefix, f)
        return hits

    def refuses(t, d, needle):
        try:
            check(t, d)
        except Refused as exc:
            assert needle in str(exc), "refusal was %r, wanted %r" % (exc, needle)
            return
        raise AssertionError("expected a refusal mentioning %r" % needle)

    # E0 -- the committed pair must be clean, or every control below would be
    # "killing" a check that was already red.
    def t0():
        f, st = check(table, delta)
        assert not f, "the committed pair is already red: %r" % f
        assert st["intersection"] >= 1, \
            "the intersection is empty, so E1 cannot fail on this corpus and " \
            "T1 proves nothing"
        assert st["allowed"] >= 1, "the allow-list is empty"
    case("T0  the committed pair is clean AND the intersection is non-empty", t0)

    # --- E1: a new delta symbol on the exception path ---------------------
    def t1():
        d = delta + "\nset\tCONFIG_CPU_HAS_LLSC\tn\ty\t-\tinvented by the self-test\n"
        h = fires(table, d, "E1")
        assert "CONFIG_CPU_HAS_LLSC" in h[0], h
    case("T1  a delta line naming an emulation gate fires E1", t1)

    def t2():
        d = delta + "\nset\tCONFIG_CPU_HAS_SYNC\tn\ty\t-\tinvented\n"
        fires(table, d, "E1")
    case("T2  a second emulation gate fires E1 too", t2)

    def t3():
        d = delta + "\nset\tCONFIG_CPU_HAS_ULS\ty\tn\t-\tinvented\n"
        fires(table, d, "E1")
    case("T3  the unaligned gate fires E1", t3)

    def t4():
        d = delta + "\nset\tCONFIG_SWAP\tn\ty\t-\tinvented\n"
        f, _ = check(table, d)
        assert not f, "a delta symbol NOT on the exception path must not fire: %r" % f
    case("T4  a delta symbol off the exception path is clean -- E1 is not "
         "firing on everything", t4)

    def t5():
        f, _ = check(table, delta, allow={})
        assert any(x.startswith("E1") for x in f), \
            "with an empty allow-list the real intersection must fire: %r" % f
    case("T5  with the allow-list emptied the committed pair goes red -- the "
         "pass in T0 is not a pass by excusing nothing", t5)

    def t6():
        a = {"CONFIG_RTL_WTDOG": "too short"}
        f, _ = check(table, delta, allow=a)
        assert any("character reason" in x for x in f), \
            "a reason under %d characters must fire: %r" % (MIN_REASON, f)
    case("T6  an exemption with a stub reason fires", t6)

    # --- E2 / E3: the allow-list cannot accrete ---------------------------
    def t7():
        a = dict(ALLOW)
        a["CONFIG_NOT_IN_THE_DELTA_AT_ALL"] = "x" * (MIN_REASON + 1)
        f, _ = check(table, delta, allow=a)
        assert any(x.startswith("E2") for x in f), f
    case("T7  an allow-list entry that is not in the delta fires E2", t7)

    def t8():
        a = dict(ALLOW)
        a["CONFIG_BLK_DEV_INITRD"] = "x" * (MIN_REASON + 1)
        f, _ = check(table, delta, allow=a)
        assert any(x.startswith("E3") for x in f), \
            "a delta symbol that is NOT on the exception path must fire E3 " \
            "when it is excused: %r" % f
    case("T8  an allow-list entry the table does not flag fires E3", t8)

    def t9():
        t = table.replace("CONFIG_RTL_WTDOG\t2\ty\t", "CONFIG_RTL_WTDOG\t2\tn\t")
        assert t != table, "the fixture mutation did not apply"
        f, _ = check(t, delta)
        assert any(x.startswith("E3") for x in f), f
    case("T9  reclassifying the allowed symbol to exc_path=n fires E3", t9)

    def t10():
        t = "\n".join(l for l in table.split("\n")
                      if not l.startswith("CONFIG_RTL_WTDOG\t"))
        f, _ = check(t, delta)
        assert any(x.startswith("E3") for x in f), f
    case("T10 deleting the allowed symbol from the table fires E3", t10)

    # --- E4: malformed input is a REFUSAL, not a pass ---------------------
    case("T11 a table with the wrong header is refused",
         lambda: refuses(table.replace("symbol\tn_files", "sym\tn_files"),
                         delta, "header"))
    case("T12 a table row with the wrong field count is refused",
         lambda: refuses(table + "\nCONFIG_X\t1\ty\n", delta, "want 4"))
    case("T13 a table row with a bad exc_path value is refused",
         lambda: refuses(table + "\nCONFIG_X\t1\tmaybe\ta.c\n", delta, "exc_path"))
    case("T14 a duplicated table symbol is refused",
         lambda: refuses(table + "\nCONFIG_RTL_WTDOG\t2\ty\ta.c\n", delta,
                         "appears twice"))
    case("T15 a delta line whose column 2 is not a CONFIG_ symbol is refused",
         lambda: refuses(table, delta + "\nset\tnot_a_symbol\tn\ty\t-\tx\n",
                         "not a CONFIG_ symbol"))
    case("T16 an empty delta is refused",
         lambda: refuses(table, "# only comments\n", "no data line"))
    case("T17 an empty table is refused",
         lambda: refuses("# only comments\n", delta, "empty"))

    def t18():
        try:
            read_text(os.path.join(tempfile.gettempdir(), "emueq-absent-xyz"))
        except Refused as exc:
            assert "does not exist" in str(exc)
            return
        raise AssertionError("a missing file must be refused")
    case("T18 a missing input file is refused rather than treated as empty", t18)

    print("emueq %s -- self-test" % VERSION)
    for ok, name, why in results:
        print("  %-5s %s%s" % ("ok" if ok else "FAIL", name,
                               "" if ok else "\n          " + why))
    bad = sum(1 for ok, _, _ in results if not ok)
    print()
    print("RESULT: %d passed, %d failed" % (len(results) - bad, bad))
    return 1 if bad else 0


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        print("usage: emueq.py population | check | refresh <kernel-root> | "
              "--self-test")
        return 0
    try:
        if args[0] == "--self-test":
            return self_test()
        if args[0] == "population":
            return cmd_population()
        if args[0] == "check":
            return cmd_check()
        if args[0] == "refresh":
            if len(args) < 2:
                raise Refused("refresh needs the kernel root, e.g. "
                              "$FWRE_WORK/rebuild/src-vendor/rtl819x-toolchain/"
                              "linux-2.6.30")
            return cmd_refresh(args[1])
    except Refused as exc:
        print("REFUSED: %s" % exc)
        return 3
    print("REFUSED: unknown mode %r" % args[0])
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
