#!/usr/bin/env python3
"""Read one FIELD out of a console capture, and refuse rather than guess.

Why this exists
---------------
Seating 16 (2026-09-08) produced five defects of mine.  Four were false stops
and four had one root cause, and both halves are this tool's specification:

* **CRLF.**  Every capture line ends ``\\r\\n``.  ``awk``'s ``$2`` is therefore
  ``"1\\r"`` and ``[ "1\\r" = "1" ]`` is false.  Three gates reported STOP or
  VOID on cells that had **passed**, and each one *printed the correct value
  beside the wrong verdict*, because a carriage return is invisible in
  display.  (量 2026-09-08: it is invisible in ``cat -A`` under Git Bash too --
  that shell translates the file on the way in, so the tool you would reach
  for to make a CR visible hides it.  ``od -c`` or Python on the raw bytes.)
* **Marks are not fields.**  ``C1-TW``'s gate looked for the string
  ``S-TRYW=00000001``.  The kernel's ``rlxfw_mark()`` and busybox ash's echo of
  the typed line are written to the console *concurrently* and interleave
  character by character (``FW-47``, ``FW-41``'s family), so the mark's head is
  shredded.  Marks come from ``write_proc`` and are emitted DURING the echo;
  fields come from ``read_proc`` and are emitted AFTER it.  **Gate on fields.**
  This tool refuses a name that looks like a mark, with the reason, instead of
  returning empty and letting the caller read that as a failed assertion.

Two more refusals were added from measurements taken while writing it:

* **A field that occurs more than once is not a value.**  ``X14-fast`` has
  ``dat`` fifteen times (a ``for`` loop over ``/proc/rtl819x-gpio``) and
  ``TM-6`` reads the same ``/proc`` file twice around a ``sleep``.  A tool that
  silently returned the first or the last would give a confident answer to an
  ambiguous question.  ``--nth`` and ``--all`` exist; the bare ``get`` refuses.
* **A number has no guessable base.**  ``n_writes 0`` is decimal and
  ``sfcr FFC00000`` is hexadecimal, in the same dump, with no prefix on either.
  ``FW-35`` is in this repository because ``awk`` read ``8001e714`` as
  scientific notation and made every address equal to every other.  So ``num``
  and ``sub`` **require** ``--base``; there is no auto-detection to be wrong.

The echoed command is removed before anything is parsed
-------------------------------------------------------
``cat /proc/rtl819x-spi`` is two whitespace-separated tokens and would parse as
a field named ``cat``.  So the echo is matched against ``meta["sent"]`` and
skipped -- and the matcher steps over ``\\r``/``\\n``, because 量 2026-09-08
busybox ash's line editor wraps the echo with ``\\r\\r\\n`` at the terminal
width: 33 of the corpus's 720 captures with a ``sent`` carry exactly one such
wrap, all of them with ``len(sent) >= 80`` (``FW-49``).  A matcher that stopped
at the first newline would find the wrap and call it the end of the command.

When the echo cannot be matched -- 量 7 of 720 captures -- the whole log is
parsed and the report says so, rather than the tool pretending it knows where
the command ended.

Self-test
---------
``selftest`` runs against captures **already committed to this repository whose
answers are known**, and every other mode runs it first and refuses to answer
if it fails.  That is the same shape as ``console-capture.py``'s guard: the
instrument proves it works before it is used, not after it has produced a
number somebody acted on.

Exit codes
  0  ok / the comparison held
  1  the comparison failed
  2  the tool refused (self-test failed, ambiguous field, a mark name, a
     missing file, no base given)
  3  the field is absent
"""

import argparse
import glob
import json
import os
import re
import sys

FIELD = re.compile(r"^([a-z][a-z0-9_]*) (\S+)$")
MARKISH = re.compile(r"(^RLXFW-)|=|-")

EXIT_OK, EXIT_DIFFER, EXIT_REFUSED, EXIT_ABSENT = 0, 1, 2, 3


class Refused(Exception):
    pass


def read_capture(prefix):
    """(log_text, sent_or_None).  `prefix` may carry .log or not."""
    if prefix.endswith(".log"):
        prefix = prefix[:-4]
    logp, metap = prefix + ".log", prefix + ".meta.json"
    if not os.path.exists(logp):
        raise Refused("no such capture: %s" % logp)
    log = open(logp, "rb").read().decode("utf-8", "replace")
    sent = None
    if os.path.exists(metap):
        try:
            sent = json.load(open(metap, encoding="utf-8")).get("sent")
        except ValueError:
            sent = None
    return log, sent


def echo_end(log, sent):
    """Offset one past the echoed command, or None if it does not match.

    Steps over CR and LF, so a line-editor wrap inside the echo is not
    mistaken for the end of the command.
    """
    if not sent:
        return None
    i = j = 0
    while i < len(log) and j < len(sent):
        c = log[i]
        if c == "\r" or c == "\n":
            i += 1
            continue
        if c != sent[j]:
            return None
        i += 1
        j += 1
    return i if j == len(sent) else None


def fields(log, sent):
    """(mapping name -> [values in order], echo_matched)."""
    ee = echo_end(log, sent)
    body = log[ee:] if ee is not None else log
    out = {}
    for raw in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = FIELD.match(raw.strip())
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return out, ee is not None


def pick(values, name, nth=None):
    if not values:
        raise KeyError(name)
    if nth is not None:
        if not 1 <= nth <= len(values):
            raise Refused("--nth %d out of range: %r occurs %d time(s)"
                          % (nth, name, len(values)))
        return values[nth - 1]
    if len(values) > 1:
        raise Refused(
            "%r occurs %d times in this capture (%s). A single value here "
            "would be an answer to a question nobody asked -- use --nth K or "
            "--all." % (name, len(values), ", ".join(values[:6])))
    return values[0]


def check_name(name):
    if name.startswith("RLXFW-") or "=" in name:
        raise Refused(
            "%r is a MARK, not a field. Marks come from write_proc and are "
            "emitted during the shell's echo, which they interleave with "
            "character by character (FW-47); fields come from read_proc and "
            "arrive clean. Gate on the field." % name)
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise Refused("%r is not a field name (want ^[a-z][a-z0-9_]*$)" % name)


def to_int(text, base, what):
    try:
        return int(text, base)
    except ValueError:
        raise Refused("%s = %r is not base-%d" % (what, text, base))


# ---------------------------------------------------------------------------
# Self-test.  Fixtures are committed captures whose answers are known.
# ---------------------------------------------------------------------------

#: (prefix, why it was chosen).  All are in this repository.
FIX_VF = "bench/2026-09-08/C1-VF"     # sent 55 chars, echo not wrapped
FIX_NG = "bench/2026-09-08/C1-NG"     # sent 98 chars, echo WRAPPED (FW-49)
FIX_P = "bench/2026-09-08/C1-P"       # sent is `cat /proc/rtl819x-spi`
FIX_REP = "bench/2026-09-06c/X14-fast"  # `dat` occurs 15 times


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def selftest(verbose=True):
    """Return (failures, labels that ran)."""
    root = _repo_root()
    bad, ran = [], []

    def ck(label, ok, why=""):
        ran.append(label)
        if not ok:
            bad.append("%s: %s" % (label, why))
        if verbose:
            # See capdate.py's ck(): tools/ci-census.py parses
            # `^ {2}(ok|FAIL|skip)\s{2,}`, and a suite it cannot parse reports
            # `ran 0/10` with zero failures.
            print("  %-5s %-6s %s" % ("ok" if ok else "FAIL", label,
                                      "" if ok else "-- " + why))

    def load(rel):
        return read_capture(os.path.join(root, rel))

    # K10 first: the population control.  A self-test that cannot find its
    # fixtures must refuse, not pass silently over nothing.
    missing = [p for p in (FIX_VF, FIX_NG, FIX_P, FIX_REP)
               if not os.path.exists(os.path.join(root, p + ".log"))]
    ck("K10", not missing,
       "fixtures missing, so nothing below was really tested: %r" % (missing,))
    if missing:
        return bad, ran

    log, sent = load(FIX_VF)
    f, matched = fields(log, sent)

    # K1 a known field on a known capture.
    ck("K1", f.get("cmp_bytes") == ["4194304"],
       "C1-VF cmp_bytes should be ['4194304'], got %r" % (f.get("cmp_bytes"),))

    # K2 THE DEFECT.  The raw bytes end \r\n; the value must not.
    ck("K2", "\r" not in "".join(v[0] for v in f.values()) and
             log.count("\r\n") > 10 and pick(f["n_writes"], "n") == "0",
       "the capture must really contain CRLF and the value must not carry it")

    # K3 negative control: an absent key is absent, not a value.
    ck("K3", "no_such_field" not in f,
       "an absent key must not appear")

    # K4 negative control: arithmetic on two fields, and the answer is a THIRD
    # field of the same dump -- so this checks the numbers, not just the parse.
    try:
        d = (to_int(pick(f["cmp_bytes"], "a"), 10, "a")
             - to_int(pick(f["digest_bytes"], "b"), 10, "b"))
        ok4 = d == to_int(pick(f["h601_skipped"], "c"), 10, "c") == 8192
    except (Refused, KeyError) as exc:
        d, ok4 = exc, False
    ck("K4", ok4,
       "cmp_bytes - digest_bytes must equal h601_skipped = 8192, got %r" % (d,))

    # K5 a mark name must be REFUSED, not returned empty.  An empty answer
    # reads to a caller as a failed assertion; a refusal does not.
    try:
        check_name("RLXFW-S-TRYW")
        ok5 = False
    except Refused:
        ok5 = True
    ck("K5", ok5, "a mark name must refuse")

    # K6 a repeated field must refuse rather than pick.
    rlog, rsent = load(FIX_REP)
    rf, _ = fields(rlog, rsent)
    try:
        pick(rf.get("dat", []), "dat")
        ok6 = False
    except Refused:
        ok6 = len(rf.get("dat", [])) == 15
    ck("K6", ok6, "X14-fast `dat` occurs %d times and must refuse a bare get"
                  % len(rf.get("dat", [])))

    # K7 the echoed command must not become a field.  C1-P's command is
    # `cat /proc/rtl819x-spi`: two tokens, and `cat` matches the field syntax.
    plog, psent = load(FIX_P)
    pf, pmatched = fields(plog, psent)
    ck("K7", pmatched and "cat" not in pf,
       "`cat` from the echoed command must not be a field (echo_matched=%s, "
       "cat=%r)" % (pmatched, pf.get("cat")))

    # K8 a WRAPPED echo (FW-49) must still be stripped and the fields found.
    nlog, nsent = load(FIX_NG)
    nf, nmatched = fields(nlog, nsent)
    ck("K8", (len(nsent) >= 80 and "\r\r\n" in nlog[:len(nsent) + 8]
              and nmatched and nf.get("corrupt_at") == ["1048576"]),
       "C1-NG has a %d-char command that wraps; fields must still parse "
       "(matched=%s corrupt_at=%r)"
       % (len(nsent or ""), nmatched, nf.get("corrupt_at")))

    # K9 the comparison must be able to FAIL.  Without this, K1 passes for a
    # tool that says yes to everything.
    ck("K9", pick(f["cmp_bytes"], "x") != "4194305",
       "a wrong expected value must not compare equal")

    return bad, ran


def run_selftest(quiet=False):
    if not quiet:
        print("capfield self-test")
    bad, ran = selftest(verbose=not quiet)
    expected = 10
    if len(ran) != expected:
        print("capfield: REFUSING -- %d self-test checks ran, %d expected"
              % (len(ran), expected))
        return EXIT_REFUSED
    if bad:
        for b in bad:
            print("  " + b)
        print("capfield: REFUSING -- the comparison itself is broken, so no "
              "answer from it would mean anything")
        return EXIT_REFUSED
    if not quiet:
        print("  %d/%d ok" % (len(ran), expected))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="read a field from a console capture, or refuse")
    ap.add_argument("--no-selftest", action="store_true",
                    help="skip the self-test (it runs first by default)")
    sub = ap.add_subparsers(dest="cmd")

    def cap(p):
        p.add_argument("capture", help="capture prefix, with or without .log")

    p = sub.add_parser("get", help="print one field's value")
    cap(p)
    p.add_argument("field")
    p.add_argument("--nth", type=int, help="1-based, when the field repeats")
    p.add_argument("--all", action="store_true", help="print every occurrence")

    p = sub.add_parser("eq", help="compare a field with a literal")
    cap(p)
    p.add_argument("field")
    p.add_argument("expected")
    p.add_argument("--nth", type=int)

    p = sub.add_parser("num", help="print a field as a number")
    cap(p)
    p.add_argument("field")
    p.add_argument("--base", type=int, required=True, choices=(10, 16))
    p.add_argument("--nth", type=int)

    p = sub.add_parser("sub", help="print fieldA - fieldB")
    cap(p)
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--base", type=int, required=True, choices=(10, 16))

    p = sub.add_parser("dump", help="print every field, one per line")
    cap(p)

    sub.add_parser("selftest", help="run the self-test and stop")

    args = ap.parse_args(argv)
    if args.cmd is None:
        ap.print_help()
        return EXIT_REFUSED
    if args.cmd == "selftest":
        return run_selftest()
    if not args.no_selftest:
        rc = run_selftest(quiet=True)
        if rc:
            run_selftest()
            return rc

    try:
        log, sent = read_capture(args.capture)
        f, matched = fields(log, sent)
        if not matched and sent:
            print("capfield: WARNING -- the echoed command did not match "
                  "meta['sent'], so the whole log was parsed", file=sys.stderr)

        if args.cmd == "dump":
            for k in sorted(f):
                for v in f[k]:
                    print("%s %s" % (k, v))
            return EXIT_OK

        name = args.field if args.cmd in ("get", "eq", "num") else None
        if name is not None:
            check_name(name)
            if name not in f:
                print("capfield: %r is not a field of %s"
                      % (name, args.capture), file=sys.stderr)
                return EXIT_ABSENT

        if args.cmd == "get":
            if args.all:
                for v in f[name]:
                    print(v)
                return EXIT_OK
            print(pick(f[name], name, args.nth))
            return EXIT_OK

        if args.cmd == "eq":
            got = pick(f[name], name, args.nth)
            if got == args.expected:
                print("ok %s = %s" % (name, got))
                return EXIT_OK
            print("DIFFER %s = %r, expected %r" % (name, got, args.expected))
            return EXIT_DIFFER

        if args.cmd == "num":
            print(to_int(pick(f[name], name, args.nth), args.base, name))
            return EXIT_OK

        if args.cmd == "sub":
            for n in (args.a, args.b):
                check_name(n)
                if n not in f:
                    print("capfield: %r is not a field of %s"
                          % (n, args.capture), file=sys.stderr)
                    return EXIT_ABSENT
            print(to_int(pick(f[args.a], args.a), args.base, args.a)
                  - to_int(pick(f[args.b], args.b), args.base, args.b))
            return EXIT_OK
    except Refused as exc:
        print("capfield: REFUSED -- %s" % exc, file=sys.stderr)
        return EXIT_REFUSED
    return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
