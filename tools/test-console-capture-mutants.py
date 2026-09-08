#!/usr/bin/env python3
"""test-console-capture-mutants -- the mutation suite for the terminator guard.

Why this file exists, and it is not a style preference
-----------------------------------------------------
`tools/console-capture.py` gained a refusal on 2026-08-30: a `capture` with
neither `--seconds` nor `--idle` never returns, so it is refused before the port
is opened.  `tools/test-console-capture.sh` went 29 -> 40 cases in the same
change and reported 40/40.

An adversarial pass the same evening ran 21 mutants of that guard against those
forty cases and **nine survived**.  This file re-ran the question with 25
mutants on 2026-08-30 and **ten survived** -- the extra one is E2, a refusal
written to stdout instead of stderr, which no case could see because every one
of them redirected `2>&1`.  Four of the ten are the ones that matter:

  * the guard can be WAIVED by any flag the new cases leave at default.
    `if args.esc > 0: return` in front of it is invisible to N18-N21, and
    `--esc 25` is `A-catch`'s own shape -- 量 on a pty, that mutant with
    `--esc 1` and no terminator gives `rc=124` after 8 s with the `.meta.json`
    lost, which is exactly the failure the guard was added for, back.
  * **no case in the forty asserted an exit code.**  `_fail` raising
    `SystemExit(0)` is green, and a card written `cmd || abort` reads a refusal
    as a success.
  * the refusal message is checked by one substring, so a mutant naming a flag
    that does not exist passes.
  * the guard moved BELOW the overwrite refusal passes, which also inverts which
    error an operator sees first.

"Nine survived" was a sentence in a log that nothing re-ran.  This file is what
makes it a number that can go red.  Same shape as `tools/test-rbcheck.py`, and
for the same reason.

What a mutation proves, and what it does not
--------------------------------------------
Each row edits `console-capture.py` at one or more asserted anchors and requires
the whole of `tools/test-console-capture.sh` to go red against the result.  A
row that survives names a control that does not work.  It does NOT prove the
tool is correct -- only that the suite can tell this particular wrong tool from
the right one.

Mutants run against the FULL suite rather than a fast subset on purpose: the
claim being tested is *"the committed cases catch it"*, and a proxy for the
suite would be a different claim.  They run in parallel because the cases are
sleep-bound (ptys and played gaps), not CPU-bound.

Anchors are asserted and must occur EXACTLY ONCE.  A mutation whose anchor has
moved is reported as a SURVIVOR, never skipped -- a mutation suite that silently
applies nothing is the "a tool reporting 0 is making a claim" failure this
repository keeps catching, and `tools/rlxfw-marks.py` refuses on the same rule.

Run:  /usr/bin/python3 tools/test-console-capture-mutants.py
      ... --jobs N          (default 6)
      ... --only W1,E1      (one or more ids, for iterating on a single control)
"""
import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/console-capture.py")
SUITE = os.path.join(ROOT, "tools/test-console-capture.sh")

# The guard and its neighbourhood, verbatim, as named anchors so a row says
# which part of the tool it broke rather than quoting a line twice.
GUARD_IF = "    if args.seconds <= 0 and args.idle <= 0:"
GUARD_CALL = "    _check_send(args.send)\n    _check_terminator(args)"
GUARD_MSG = ('            "capture needs a terminator: pass --seconds N or '
             '--idle N (or both).\\n"')
META_PAIR = '        "seconds": args.seconds,\n        "idle": args.idle,'
MAKEDIRS = ('    os.makedirs(os.path.dirname(os.path.abspath(log_path)) or ".",'
            ' exist_ok=True)')
OPEN_PORT = "        ser = serial.Serial(args.port, args.baud, timeout=0)"
FAIL_EXIT = "    raise SystemExit(2)"
FAIL_PRINT = '    print(f"console-capture: {msg}", file=sys.stderr)'
CLIFF = "    n = len(value)\n    if n >= 128:"
WHITESPACE = "    if value != value.strip():"

# --until, 2026-09-09.  Twelve more, and they are here rather than in a file of
# their own because the question is the same one: does the committed suite tell
# this wrong tool from the right one?  The flag has two break sites, two arming
# decisions and three pieces of arithmetic, and every one of them can be broken
# in a way that leaves a capture looking successful -- which is the failure mode
# that costs a power cycle, not a red suite.
U_ESC_BREAK = ("                    drain(args.esc_period)\n"
               "                    if until_at is not None:")
U_FINAL_BREAK = ('                if until_at is not None:\n'
                 '                    stop_reason = f"--until matched at offset {until_at}"')
U_SEARCH = "                        m = until_re.search(matchbuf)"
U_ARM_INIT = ("        until_armed = until_re is not None and not args.esc "
              "and args.send is None")
U_ARM_BODY = ("            nonlocal until_armed, matchbuf_base\n"
              "            if until_re is None:\n"
              "                return")
U_CALL = ("    _check_send(args.send)\n    _check_terminator(args)\n"
          "    _check_until(args)")
U_EMPTY = '    if args.until == "":'
U_BASE_SET = "            matchbuf_base = offset"
U_BASE_ADV = "                        matchbuf_base += drop"
U_AT = "                            until_at = matchbuf_base + m.start()"
U_META = '        "until": args.until,\n        "until_offset": None,'
U_ENDED = '                    meta["esc"]["esc_after"]["ended_on_until"] = True'
U_META_END = "    meta[\"until_offset\"] = until_at"

# id, what it does, [(anchor, replacement), ...]
#
# The classes are named because a class with one member is a class nobody has
# tested the edge of.  WAIVER produced a real never-returning capture on a pty;
# POSITION and CONTRACT are the two the first forty cases were blind to as a
# class rather than as an instance.
MUT = [
    # --- WAIVER: an early return on a flag the guard has no business reading --
    # 量 2026-08-29: DEFAULT_BAUD = 38400, DEFAULT_CR_SETTLE = 2.0, so W6/W7
    # really are conditional waivers and not unconditional ones.
    ("W1", "guard waived by --esc (A-catch's own shape)",
     [(GUARD_IF, "    if args.esc > 0:\n        return\n" + GUARD_IF)]),
    ("W2", "guard waived by --esc-after",
     [(GUARD_IF, "    if args.esc_after > 0:\n        return\n" + GUARD_IF)]),
    ("W3", "guard waived whenever a command is sent",
     [(GUARD_IF, "    if args.send:\n        return\n" + GUARD_IF)]),
    ("W4", "guard waived by --no-cr",
     [(GUARD_IF, "    if args.no_cr:\n        return\n" + GUARD_IF)]),
    ("W5", "guard waived by --force",
     [(GUARD_IF, "    if args.force:\n        return\n" + GUARD_IF)]),
    ("W6", "guard waived by a non-default --cr-settle",
     [(GUARD_IF, "    if args.cr_settle != 2.0:\n        return\n" + GUARD_IF)]),
    ("W7", "guard waived by a non-default --baud",
     [(GUARD_IF, "    if args.baud != 38400:\n        return\n" + GUARD_IF)]),
    ("W8", "guard waived by a non-default --esc-period",
     [(GUARD_IF, "    if args.esc_period != 0.02:\n        return\n" + GUARD_IF)]),

    # --- CONDITION: the predicate itself --------------------------------
    ("C1", "zero accepted again (< 0 instead of <= 0)",
     [(GUARD_IF, "    if args.seconds < 0 and args.idle < 0:")]),
    ("C2", "and -> or, so BOTH flags become required",
     [(GUARD_IF, "    if args.seconds <= 0 or args.idle <= 0:")]),
    ("C3", "guard on --seconds only: every --idle capture refused",
     [(GUARD_IF, "    if args.seconds <= 0:")]),
    ("C4", "guard on --idle only: every --seconds capture refused",
     [(GUARD_IF, "    if args.idle <= 0:")]),
    ("C5", "the guard is dead",
     [(GUARD_IF, "    if False:")]),

    # --- POSITION: a MOVE is two edits, and writing it as one would be a
    #     different mutant (a delete, or a second call left in place) ------
    ("P1", "guard moved ABOVE _check_send: a bad line reports the wrong fault",
     [(GUARD_CALL, "    _check_terminator(args)\n    _check_send(args.send)")]),
    ("P2", "guard moved BELOW the overwrite refusal",
     [(GUARD_CALL, "    _check_send(args.send)"),
      (MAKEDIRS, "    _check_terminator(args)\n" + MAKEDIRS)]),
    ("P3", "guard moved BELOW the port open: the device is touched first",
     [(GUARD_CALL, "    _check_send(args.send)"),
      (OPEN_PORT, OPEN_PORT + "\n        _check_terminator(args)")]),

    # --- CONTRACT: what a refusal IS ------------------------------------
    ("E1", "a refusal exits 0, so `cmd || abort` reads it as success",
     [(FAIL_EXIT, "    raise SystemExit(0)")]),
    ("E2", "a refusal goes to STDOUT, so a card that redirects captures it",
     [(FAIL_PRINT, '    print(f"console-capture: {msg}")')]),
    ("M1", "the refusal names a flag that does not exist",
     [(GUARD_MSG,
       '            "capture needs a terminator: pass --timeout N.\\n"')]),

    # --- METADATA: the two fields the guard's twin change added ----------
    ("D1", "both terminator fields hardcoded",
     [(META_PAIR, '        "seconds": 0.0,\n        "idle": 0.0,')]),
    ("D2", "the two fields swapped",
     [(META_PAIR, '        "seconds": args.idle,\n        "idle": args.seconds,')]),
    ("D3", "both fields report --seconds",
     [(META_PAIR, '        "seconds": args.seconds,\n        "idle": args.seconds,')]),
    ("D4", "the two fields deleted",
     [(META_PAIR, "        # fields deleted")]),

    # --- the neighbours the guard must not be covering for ---------------
    # If either survives, the guard's cases are standing in for _check_send's
    # and P1 above is being killed by luck rather than by a case of its own.
    ("S1", "_check_send's 128-byte cliff moved to 129",
     [(CLIFF, "    n = len(value)\n    if n >= 129:")]),
    ("S2", "_check_send's leading-whitespace refusal deleted",
     [(WHITESPACE, "    if False:")]),

    # --- UNTIL: the two break sites -------------------------------------
    # Both of these leave a tool that still WORKS -- captures are taken, files
    # are written, nothing errors.  What they take away is the early stop, and
    # a card whose --esc-after was sized as a cap then runs it as a duration:
    # the board resets after the ESC stream has ended, the loader prompt goes
    # by uncaught, and the next thing on the console is the vendor firmware.
    # That is a power cycle, and it is invisible to every case that does not
    # look at where the run stopped.
    ("U1", "the --esc-after loop no longer breaks on the pattern",
     [(U_ESC_BREAK, "                    drain(args.esc_period)\n"
                    "                    if False:")]),
    ("U2", "the final read loop no longer breaks on the pattern",
     [(U_FINAL_BREAK, '                if False:\n'
                      '                    stop_reason = f"--until matched at offset {until_at}"')]),
    ("U3", "--until tested AFTER --seconds, so a caught event reads as a short window",
     [(U_FINAL_BREAK, "                if args.seconds and now - t0 >= args.seconds:\n"
                      '                    stop_reason = f"--seconds {args.seconds} elapsed"\n'
                      "                    break\n" + U_FINAL_BREAK)]),

    # --- UNTIL: what is searched ----------------------------------------
    ("U4", "the search is per read() chunk, so a split pattern is never seen",
     [(U_SEARCH, "                        m = until_re.search(chunk)")]),
    ("U5", "armed from the start, so the pre-send --esc window fires it",
     [(U_ARM_INIT, "        until_armed = until_re is not None")]),
    ("U6", "never armed at all",
     [(U_ARM_BODY, "            nonlocal until_armed, matchbuf_base\n"
                   "            if True:\n"
                   "                return")]),

    # --- UNTIL: the offset arithmetic -----------------------------------
    # Found by auditing the cases, not by a red run: until N39/N40 existed
    # every case armed on an empty log, so base and match position were the
    # same number and all three of these survived.
    ("U7", "the base is not taken at the arming point",
     [(U_BASE_SET, "            matchbuf_base = 0")]),
    ("U8", "the base does not advance when the window rolls",
     [(U_BASE_ADV, "                        pass")]),
    ("U9", "the offset is reported relative to the buffer, not to the .log",
     [(U_AT, "                            until_at = m.start()")]),

    # --- UNTIL: the refusals and the record -----------------------------
    ("U10", "_check_until moved ABOVE the terminator guard",
     [(U_CALL, "    _check_send(args.send)\n    _check_until(args)\n"
               "    _check_terminator(args)")]),
    ("U11", "the empty-pattern refusal deleted -- '' matches at offset 0 of everything",
     [(U_EMPTY, "    if False:")]),
    ("U12", "the metadata forgets which pattern was armed",
     [(U_META, '        "until": None,\n        "until_offset": None,')]),
    ("U13", "the ESC loop's early end is not recorded",
     [(U_ENDED, "                    pass")]),
    ("U14", "until_offset is never written back",
     [(U_META_END, '    meta["until_offset"] = None')]),
]


def apply_mutation(src, edits):
    """Exactly-once per anchor, or nothing.  A two-site anchor would make the
    mutant a different edit from the one the row's name claims, and a zero-site
    one would make it no edit at all."""
    out = src
    for anchor, repl in edits:
        n = out.count(anchor)
        if n != 1:
            return None, f"anchor occurs {n} time(s), not once: {anchor[:44]!r}"
    for anchor, repl in edits:
        out = out.replace(anchor, repl, 1)
    if out == src:
        return None, "the edits cancelled: the file is unchanged"
    return out, None


def run_suite(tool_path, cwd):
    env = dict(os.environ)
    env["CC_TOOL"] = tool_path
    return subprocess.run(["bash", SUITE], capture_output=True, text=True,
                          cwd=cwd, env=env)


def one(row, src):
    mid, what, edits = row
    d = tempfile.mkdtemp(prefix="cc-mut-")
    try:
        mutated, why = apply_mutation(src, edits)
        if mutated is None:
            return mid, False, f"[NOT APPLIED: {why}]"
        tgt = os.path.join(d, "console-capture.py")
        with open(tgt, "w", encoding="utf-8", newline="\n") as f:
            f.write(mutated)
        r = run_suite(tgt, d)
        killed = r.returncode != 0
        red = sorted({l[8:].split()[0] for l in r.stdout.split("\n")
                      if l.startswith("  FAIL  ") and len(l) > 8})
        note = "by " + ",".join(red) if red else f"rc={r.returncode}, no FAIL line"
        return mid, killed, note
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", default=None, help="comma-separated mutation ids")
    a = ap.parse_args()

    rows = MUT
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        rows = [r for r in MUT if r[0] in want]
        missing = want - {r[0] for r in rows}
        if missing:
            sys.exit(f"no such mutation id(s): {sorted(missing)}")

    src = open(SRC, encoding="utf-8").read()

    # The baseline.  Without it a suite that is already red would "kill" every
    # mutation and this file would report a clean sweep over nothing.
    t0 = time.monotonic()
    base = run_suite(SRC, ROOT)
    if base.returncode != 0:
        print(base.stdout[-2000:])
        sys.exit(f"REFUSING: the unmutated suite already fails "
                 f"(rc={base.returncode}) -- every mutation below would 'kill' "
                 f"on a suite that was already red")
    ncases = sum(1 for l in base.stdout.split("\n") if l.startswith("  ok    "))
    print(f"baseline: the unmutated suite is green, {ncases} case(s), "
          f"{time.monotonic() - t0:.0f}s")
    print(f"{len(rows)} mutation(s), {a.jobs} at a time\n")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for mid, killed, note in ex.map(lambda r: one(r, src), rows):
            results[mid] = (killed, note)

    survived = []
    for mid, what, _ in rows:
        killed, note = results[mid]
        # `  ok  ` / `  FAIL  ` is the vocabulary tools/ci-census.py parses.  A
        # suite that prints its own words is a suite the census reads as zero
        # cases -- 量 2026-08-30, when test-rbcheck.py printed KILLED/SURVIVED
        # and CI reported `ran 0/9`.
        print(f"  {'ok  ' if killed else 'FAIL'}  {mid:4s} {what:58s} "
              f"{'killed ' + note if killed else 'SURVIVED ' + note}")
        if not killed:
            survived.append(f"{mid}  {what}  {note}")

    print()
    print(f"  {len(rows) - len(survived)} passed, {len(survived)} failed "
          f"({time.monotonic() - t0:.0f}s wall)")
    if survived:
        print(f"\n  {len(survived)} MUTATION(S) SURVIVED -- those are controls "
              f"that do not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    return 0


sys.exit(main())
