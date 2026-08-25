#!/usr/bin/env python3
"""reply-size.py -- what the loader will send back, in bytes, before it sends it.

WHY THIS IS A TOOL AND NOT A FORMULA IN A DOCUMENT
--------------------------------------------------
`SPEC.md` LDR-07 carries the formula and on 2026-08-25 it went 15 for 15 across
one seating.  The one prediction that missed was not the formula: block 3
predicted 214 bytes and the capture was 213, because `DW 81000400 16` is
fourteen characters and a person counted fifteen.  `tools/check-predictions.py`
verifies that a prediction file predates its capture; it does not verify the
arithmetic inside it, and both arithmetic errors that seating were in blocks
written at the bench rather than at the desk.

So: the count that goes into a prediction block comes out of this, and `len()`
does the counting.

WHAT A PREDICTED REPLY LENGTH IS WORTH
--------------------------------------
It is a control that costs nothing and that a truncated or a stale capture
cannot pass.  Short by 47 -- a `DW` line went missing.  Short by 9 -- the prompt
never arrived.  Short by anything else -- it is not the reply to the command
that was sent.  Two states that are NOT misses have their own names here,
because a capture that came back 24 bytes when 71 were predicted is telling you
something specific and `MISS` would throw it away:

    ECHO-ONLY        the command was echoed and the prompt came back with no
                     output at all.  `bench/2026-08-24b/CONT.log`, 24 bytes:
                     the first command after a USB re-enumeration is echoed and
                     not acted on (C-19).
    UNKNOWN-COMMAND  the loader answered `Unknown command !`.
                     `bench/2026-08-24/A0-reopen-control.log`, 44 bytes.

THE MODEL, AND WHERE EVERY CONSTANT IN IT CAME FROM
---------------------------------------------------
Every constant below was derived by fitting `bytes - len(cmd)` across every
capture in `bench/` that carries a `sent` field and no ESC streaming -- 133 of
them -- and NOT by reading the loader's source or by counting characters in a
terminal.  The residual is a single value per command family or the family is
not modelled.  `--self-test` re-derives them from the fixtures and refuses to
report if any control fails.

    reply = len(cmd) + 2 + body + 9

        + 2   the LF CR the loader emits after echoing the command
        + 9   `<RealTek>`, the prompt, with no trailing newline
        body  per family, below

    family   body                          samples   fitted residual
    ------   ---------------------------   -------   ---------------
    DW       47 * ceil(n / 4)              91        11
    EW       0                             10        11
    EB       0                             1         11
    Y        23                            6         34
    PHYR     68                            5         79
    FLR      81, AND NO PROMPT             6         81

`DW`'s 47 is one output line: `\r` + `AAAAAAAA:` + four `\t`-plus-eight-hex
groups + `\n`.  The `ceil` is LDR-07's carry trap -- the loop steps `i` by 4 and
tests `i < n`, so `DW <addr> 1` through `DW <addr> 4` all print four words, and
`DW <addr> 10` prints twelve.  The carry is UPWARD, so a length given too small
never says so: the read-back is always whole lines and looks complete.

`FLR` does not end at `<RealTek>`.  It ends at `(Y)es , (N)o ? --> ` and waits.
That is why its residual is 81 and not 81 + 9, and a tool that added the prompt
to every family would be wrong by nine bytes on exactly the command that writes
to RAM from flash.

NOT MODELLED, AND EACH ONE FOR A STATED REASON
-----------------------------------------------
    DB       one sample.  The header row and the per-row format cannot be
             separated from a single length.
    J        two samples, 1779 each -- but that is a property of the IMAGE that
             booted, not of the command.  A different image gives a different
             number and the model would be a coincidence with n=2.
    MDIOR    one sample, and the length depends on how many PHY addresses answer.

An unmodelled family is reported as UNMODELLED and is never counted as a hit.
A tool whose "0 misses" includes everything it declined to look at is the defect
this project calls a sweep with no positive control.
"""

import argparse
import glob
import json
import math
import os
import sys

ECHO_TAIL = 2            # the LF CR after the command echo
PROMPT = 9               # '<RealTek>'
UNKNOWN_BODY = 20        # 'Unknown command !' + CR LF + CR
DW_LINE = 47             # one DW output line, terminator included


def _dw_body(argv):
    if len(argv) < 2:
        raise ValueError("DW needs an address and a length")
    n = int(argv[1], 10)          # LDR-07: the address is hex, the LENGTH is decimal
    if n < 0:
        raise ValueError("negative length")
    return DW_LINE * math.ceil(n / 4)


# family -> (body function, sample count behind it, ends with the prompt)
MODELS = {
    "DW":   (_dw_body,          91, True),
    "EW":   (lambda a: 0,       10, True),
    "EB":   (lambda a: 0,        1, True),
    "Y":    (lambda a: 23,       6, True),
    "PHYR": (lambda a: 68,       5, True),
    # 79 and not 81: the fitted residual is `bytes - len(cmd)` and it already
    # contains the two-byte echo tail. For every family that ends at the prompt
    # the residual is body + 11; FLR has no prompt, so its residual is body + 2.
    # Writing 81 here made the FLR fixture predict 106 against a measured 104 --
    # caught by control C2 on the first run of this file, which is the whole
    # reason the controls run before anything is reported.
    "FLR":  (lambda a: 79,       6, False),
}

UNMODELLED = {
    "DB":    "one sample; the header row and the per-row format are not separable from it",
    "J":     "two samples of 1779, but that is the booted image speaking, not the command",
    "MDIOR": "one sample, and the length depends on how many PHY addresses answer",
}

# Fixtures: every one is a real capture, named. The self-test is these.
FIXTURES = [
    # (command, bytes, expected state, capture)
    ("DW 8040EB40 32", 401, "OK",              "bench/2026-08-25/H0b.log"),
    ("DW 8040DBC0 1",   71, "OK",              "bench/2026-08-25/A0.log"),
    ("DW 80000000 8",  118, "OK",              "bench/2026-08-25/H0c.log"),
    ("DW 80A00000 8",  118, "OK",              "bench/2026-08-25/H0d-a.log"),
    ("DW BB804128 8",  118, "OK",              "bench/2026-08-25/E13-pos1-wan.log"),
    ("DW 81000400 16", 213, "OK",              "bench/2026-08-24b/C7a-rb.log"),
    ("EW 81000000 DEADBEEF CAFEBABE", 40, "OK", "bench/2026-08-24/C1.log"),
    ("EW 81000102 11111111",  31, "OK",        "bench/2026-08-24/C3a.log"),
    ("EB 81000200 41 42 43",  31, "OK",        "bench/2026-08-24/C4a.log"),
    ("Y",                     35, "OK",        "bench/2026-08-24c/G8pre-y0.log"),
    ("PHYR 1 5",              87, "OK",        "bench/2026-08-24b/E12b.log"),
    ("PHYR 0 1",              87, "OK",        "bench/2026-08-24b/E12c.log"),
    ("FLR 80A00000 000000 100", 104, "OK",     "bench/2026-08-24c/G8pre-flr0.log"),
    ("DW 8040DCE8 1",         24, "ECHO-ONLY", "bench/2026-08-24b/CONT.log"),
    ("DW 8040DBC0 1",         44, "UNKNOWN-COMMAND",
                                               "bench/2026-08-24/A0-reopen-control.log"),
    ("DB 81000200 4",        153, "UNMODELLED", "bench/2026-08-24/C4b.log"),
    ("J 80500000",          1789, "UNMODELLED", "bench/2026-08-24c/G6.log"),
]


def predict(cmd):
    """(bytes, derivation) for a modelled command; (None, reason) otherwise."""
    cmd = cmd.strip()
    if not cmd:
        return None, "empty command"
    argv = cmd.split()
    fam = argv[0]
    if fam in UNMODELLED:
        return None, "not modelled: " + UNMODELLED[fam]
    if fam not in MODELS:
        return None, "no model for command family %r" % fam
    body_fn, n, has_prompt = MODELS[fam]
    body = body_fn(argv[1:])
    tail = PROMPT if has_prompt else 0
    total = len(cmd) + ECHO_TAIL + body + tail
    how = "len(%r)=%d + %d echo tail + %d body + %d prompt" % (
        cmd, len(cmd), ECHO_TAIL, body, tail)
    if fam == "DW":
        n_words = int(argv[2], 10)
        how += "   [%d words -> %d lines x %d, LDR-07 rounds UP]" % (
            n_words, math.ceil(n_words / 4), DW_LINE)
    how += "   [model fitted on n=%d captures]" % n
    return total, how


def classify(cmd, nbytes):
    """(state, predicted, delta). state is one of OK / ECHO-ONLY /
    UNKNOWN-COMMAND / SHORT / LONG / UNMODELLED."""
    want, how = predict(cmd)
    if want is None:
        return "UNMODELLED", None, None
    if nbytes == want:
        return "OK", want, 0
    body_seen = nbytes - len(cmd.strip()) - ECHO_TAIL - PROMPT
    if body_seen == 0:
        return "ECHO-ONLY", want, nbytes - want
    if body_seen == UNKNOWN_BODY:
        return "UNKNOWN-COMMAND", want, nbytes - want
    return ("SHORT" if nbytes < want else "LONG"), want, nbytes - want


# --------------------------------------------------------------------------
# controls. Nothing reports until all of them pass.
# --------------------------------------------------------------------------

def controls():
    out, bad = [], 0

    def ck(name, want, got):
        nonlocal bad
        ok = (want == got)
        if not ok:
            bad += 1
        out.append("  %-4s %-52s %s" % ("ok" if ok else "FAIL", name,
                                        got if ok else "expected %r, got %r" % (want, got)))

    # 1. population. A checker with an empty fixture table passes vacuously.
    ck("C1 the fixture table is not empty", True, len(FIXTURES) >= 15)

    # 2. positive. Every fixture reaches the state it was recorded with.
    hits = sum(1 for c, b, st, _ in FIXTURES if classify(c, b)[0] == st)
    ck("C2 every fixture classifies as recorded", len(FIXTURES), hits)

    # 3. negative. One byte off must not be OK -- otherwise C2 proves nothing.
    off = [classify(c, b + 1)[0] for c, b, st, _ in FIXTURES if st == "OK"]
    ck("C3 +1 byte is never OK", True, all(s != "OK" for s in off))
    ck("C3b and it reads as LONG", True, all(s == "LONG" for s in off))

    # 4. LDR-07's carry, in both directions.
    ck("C4 DW 1..4 all predict the same",
       True, len({predict("DW 80A00000 %d" % k)[0] for k in (1, 2, 3, 4)}) == 1)
    ck("C4b DW 5 costs one more line",
       DW_LINE, predict("DW 80A00000 5")[0] - predict("DW 80A00000 4")[0])
    # Same command length on both sides, or this measures the decimal digits of
    # the length argument instead of the number of lines. (It did, on the first
    # run: 142 against an expected 141.)
    ck("C4c DW 10 prints three lines, DW 04 one",
       2 * DW_LINE, predict("DW 80A00000 10")[0] - predict("DW 80A00000 04")[0])

    # 5/6. The two named states are reachable and distinct from a miss.
    ck("C5 a body of 0 reads ECHO-ONLY", "ECHO-ONLY", classify("DW 8040DCE8 1", 24)[0])
    ck("C6 a body of 20 reads UNKNOWN-COMMAND",
       "UNKNOWN-COMMAND", classify("DW 8040DBC0 1", 44)[0])

    # 7. Declining to model is not a hit.
    ck("C7 DB is UNMODELLED, not OK", "UNMODELLED", classify("DB 81000200 4", 153)[0])
    ck("C7b J is UNMODELLED, not OK", "UNMODELLED", classify("J 80500000", 1789)[0])

    # 8. THE ONE THAT MOTIVATED THE TOOL. `DW 81000400 16` is fourteen
    #    characters; on 2026-08-25 a person counted fifteen and block 3
    #    predicted 214 against a measured 213.
    ck("C8 'DW 81000400 16' is 14 chars, so 213 and not 214",
       213, predict("DW 81000400 16")[0])

    return out, bad


# --------------------------------------------------------------------------

def cmd_predict(args):
    for c in args.command:
        want, how = predict(c)
        if want is None:
            print("%-40s  --      %s" % (c, how))
        else:
            print("%-40s  %6d  %s" % (c, want, how))
    return 0


def cmd_check(args):
    metas = []
    for p in args.path:
        if os.path.isdir(p):
            metas += sorted(glob.glob(os.path.join(p, "**", "*.meta.json"),
                                      recursive=True))
        else:
            metas.append(p)
    if not metas:
        print("no capture metadata under: %s" % " ".join(args.path), file=sys.stderr)
        return 2

    tally = {}
    rows = []
    skipped_esc = 0
    for p in metas:
        try:
            m = json.load(open(p, encoding="utf-8"))
        except Exception as e:                    # noqa: BLE001
            rows.append((p, "", None, "UNREADABLE", None, str(e)))
            tally["UNREADABLE"] = tally.get("UNREADABLE", 0) + 1
            continue
        sent = (m.get("sent") or "").strip()
        esc = (m.get("esc_seconds") or 0) + (m.get("esc_after_seconds") or 0)
        if esc:
            # An ESC-streaming capture holds boot text as well as the reply, so
            # its byte count is not this model's to predict. Counted, not hidden.
            skipped_esc += 1
            continue
        if not sent:
            tally["NO-COMMAND"] = tally.get("NO-COMMAND", 0) + 1
            continue
        st, want, delta = classify(sent, m.get("bytes"))
        tally[st] = tally.get(st, 0) + 1
        rows.append((p, sent, m.get("bytes"), st, want, delta))

    for p, sent, got, st, want, delta in rows:
        if st in ("OK",) and not args.all:
            continue
        d = "" if delta in (None, 0) else " (%+d)" % delta
        print("  %-14s %-34s got %-6s want %-6s%s   %s" % (
            st, sent, got, "--" if want is None else want, d, p))

    print()
    print("  captures with a command and no ESC stream: %d" % sum(tally.values()))
    for k in sorted(tally):
        print("    %-16s %d" % (k, tally[k]))
    if skipped_esc:
        print("    %-16s %d   (boot text in the same capture -- out of model)"
              % ("ESC-STREAMED", skipped_esc))

    # The population control for THIS run: a sweep that looked at nothing must
    # not report zero misses.
    modelled = sum(v for k, v in tally.items() if k not in ("UNMODELLED", "NO-COMMAND"))
    if modelled == 0:
        print("\nRESULT: refused -- 0 modelled captures were examined, so a clean"
              " result would mean nothing")
        return 2
    misses = tally.get("SHORT", 0) + tally.get("LONG", 0) + tally.get("UNREADABLE", 0)
    if misses:
        print("\nRESULT: %d modelled, %d unexplained" % (modelled, misses))
        return 1
    print("\nRESULT: %d modelled, 0 unexplained" % modelled)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode")

    p = sub.add_parser("predict", help="bytes the loader will send back")
    p.add_argument("command", nargs="+")
    p.set_defaults(fn=cmd_predict)

    p = sub.add_parser("check", help="classify captures against the model")
    p.add_argument("path", nargs="+")
    p.add_argument("--all", action="store_true", help="print the OK rows too")
    p.set_defaults(fn=cmd_check)

    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and stop")
    args = ap.parse_args()

    if args.self_test:
        out, bad = controls()
        print("=== reply-size.py controls ===")
        print("\n".join(out))
        print()
        print("RESULT: %d passed, %d failed" % (len(out) - bad, bad))
        return 1 if bad else 0

    # Controls first, always. A tool that reports on a file before proving it
    # can fail is a tool reporting its own opinion.
    out, bad = controls()
    if bad:
        print("=== reply-size.py controls ===", file=sys.stderr)
        print("\n".join(out), file=sys.stderr)
        print("\nREFUSING to report: %d control(s) failed" % bad, file=sys.stderr)
        return 2

    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
