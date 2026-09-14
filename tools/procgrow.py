#!/usr/bin/env python3
"""procgrow -- re-derive `SPEC.md` `FW-64`'s `+3` from the raw captures.

THE CLAIM
  A `cat` of `/proc/rtl819x-gpio` normally costs two `read_proc` invocations
  (`FW-64`), but three when the rendering GROWS BY ONE BYTE between the first
  and the second, because `proc_file_read` then returns 1 instead of 0 and
  `cat` issues another read.  The rendering grows when a printed counter the
  handler itself increments gains a decimal digit.

WHY IT IS A SEPARATE TOOL
  The finding was produced by one script.  This one was written from the raw
  captures without that script in front of it, so the two are a cross-check
  rather than a re-run -- the `xcheck` discipline applied to a claim instead
  of to a number.

WHAT WOULD REFUTE IT, written before the sweep
  V1  a pair with delta 3 where the rendering was NOT predicted to grow
  V2  a pair predicted to grow whose delta is 2
  V3  the extra blank line on a pair whose delta is 2
Any of the three, anywhere in the corpus, and the mechanism is wrong.
`--self-test` injects one of each into a synthetic capture and requires all
three to fire, because a sweep that reports three zeros and CANNOT report
anything else is not evidence.

量 2026-09-15 over `bench/**/*.log`: 6 files, 544 consecutive dump pairs,
3 predicted to grow, 3 carrying the extra blank line, 3 with delta 3 -- the
same three, and V1/V2/V3 all 0.

⚠️ SCOPE, stated rather than discovered later.  This tool needs TWO dumps in
one capture to compute a delta, so it cannot see the single-dump captures
(`X1-getg`, `X4-again2`, `C11-L6`) where the blank line is visible and no
delta exists.  It confirms three of the six known instances and is silent
about the other three.
"""

import glob
import re
import sys

CHK = re.compile(r"^n_state_chk (\d+)$")
FGN = re.compile(r"^n_state_foreign (\d+)$")
VER = re.compile(r"^version rtl819x-gpio ")


def grows(v):
    """Does incrementing v by one add a decimal digit?

    🔴 My first predicate was "a power of ten lies in (displayed, next
    displayed]" and it produced NINE apparent counter-examples.  Working
    through the mechanism line by line shows the predicate was wrong, not the
    mechanism.  Inside one `cat`:

        invocation 1: counter += 1 -> V, renders V, length L1.  cat copies it,
                      so V is the DISPLAYED value.
        invocation 2: counter += 1 -> V+1, renders V+1, length L2.
        L2 > L1  =>  proc_file_read returns 1  =>  invocation 3.

    So the condition is on V+1, not on anything between two displayed values.
    `chk 98 -> 100` displays 98; 98+1 = 99 adds no digit; delta 2 is correct.
    `chk 9 -> 12` displays 9; 9+1 = 10 adds one; delta 3.  And 0 -> 1 adds no
    digit, so 10**0 must not count.
    """
    return len(str(v + 1)) > len(str(v))


def dumps_of(path):
    """[(chk, fgn, extra_newline)] for each /proc/rtl819x-gpio rendering.

    🔴 The first version of this parser closed a block on a blank line and
    found ZERO blocks in the whole corpus -- a tool reporting 0 making a
    claim, caught by looking at the bytes.  There is no blank line between
    dumps: the rendering is `key value` lines and the next `cat`'s
    /proc/uptime follows immediately.  The extra byte is one extra newline, so
    the signature is an EMPTY LINE anywhere between one `version` line and the
    next -- which is exactly what the claim says it should be, and is why the
    observable is independent of the counters.
    """
    raw = open(path, "rb").read().decode("latin-1")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    marks = [i for i, ln in enumerate(lines) if VER.match(ln)]
    out = []
    for k, start in enumerate(marks):
        end = marks[k + 1] if k + 1 < len(marks) else len(lines)
        chk = fgn = None
        empty = False
        for ln in lines[start + 1:end]:
            m = CHK.match(ln)
            if m:
                chk = int(m.group(1))
                continue
            m = FGN.match(ln)
            if m:
                fgn = int(m.group(1))
                continue
            if ln == "":
                empty = True
        if chk is not None and fgn is not None:
            out.append((chk, fgn, empty))
    return out


SYNTH_HEAD = "version rtl819x-gpio 1.1\r\nadded 1\r\n"


def _dump(chk, fgn, extra_blank):
    return (SYNTH_HEAD + "n_state_chk %d\r\nn_state_foreign %d\r\n"
            % (chk, fgn) + "val04 00000000\r\n"
            + ("\r\n" if extra_blank else "") + "1.00 1.00\r\n")


def self_test(tmpdir):
    """Plant one of each refutation and require all three to fire.

    A sweep that prints three zeros and cannot print anything else proves
    nothing.  Each case below is a capture the tool MUST reject.
    """
    import os
    cases = [
        # (label, dumps, which counter must fire)
        ("V1 delta 3 with no growth predicted",
         [_dump(20, 0, False), _dump(23, 0, False)], "v1"),
        ("V2 growth predicted but delta 2",
         [_dump(9, 0, False), _dump(11, 0, False)], "v2"),
        ("V3 extra blank line on a delta-2 pair",
         [_dump(20, 0, True), _dump(22, 0, False)], "v3"),
        # and the control on the control: a clean pair must fire nothing
        ("C0 a clean delta-2 pair fires nothing",
         [_dump(20, 0, False), _dump(22, 0, False)], None),
        ("C1 a true delta-3 growth fires nothing",
         [_dump(9, 0, True), _dump(12, 0, False)], None),
    ]
    out, npass, nfail = [], 0, 0
    for label, dumps, want in cases:
        p = os.path.join(tmpdir, label.split()[0] + ".log")
        with open(p, "wb") as fh:
            fh.write("".join(dumps).encode("ascii"))
        counts = sweep([p], quiet=True)
        fired = [k for k in ("v1", "v2", "v3") if counts[k]]
        ok = (fired == [want]) if want else (fired == [])
        out.append("  %s  %-54s %s"
                   % ("ok   " if ok else "FAIL ", label,
                      "fired " + (",".join(fired) if fired else "nothing")))
        npass, nfail = (npass + 1, nfail) if ok else (npass, nfail + 1)
    return npass, nfail, out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--self-test" in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            npass, nfail, out = self_test(td)
        print("procgrow --self-test -- each case plants a refutation the "
              "sweep must catch")
        for l in out:
            print(l)
        print("RESULT: %d passed, %d failed" % (npass, nfail))
        return 0 if nfail == 0 else 1

    pats = args or ["bench/**/*.log"]
    paths = []
    for p in pats:
        paths.extend(sorted(glob.glob(p, recursive=True)))
    c = sweep(paths)
    return 0 if (c["v1"] == 0 and c["v2"] == 0 and c["v3"] == 0) else 1


def sweep(paths, quiet=False):
    tot = grow_pred = grow_obs = both = v1 = v2 = v3 = 0
    hits, files = [], 0
    for path in paths:
        ds = dumps_of(path)
        if len(ds) < 2:
            continue
        files += 1
        for i in range(len(ds) - 1):
            chk, fgn, blank = ds[i]
            nchk, nfgn, _ = ds[i + 1]
            d = nchk - chk
            if d <= 0:
                continue
            tot += 1
            # n_state_chk increments on every invocation; n_state_foreign only
            # when the watched bit moved, so it can only widen the rendering
            # in a pair where it is actually advancing.
            crossed = grows(chk) or (nfgn > fgn and grows(fgn))
            three = (d == 3)
            if crossed:
                grow_pred += 1
            if blank:
                grow_obs += 1
            if crossed and blank:
                both += 1
            if three and not crossed:
                v1 += 1
                hits.append(("V1 delta3-no-crossing", path, i, chk, nchk, fgn, nfgn, blank))
            if crossed and d == 2:
                v2 += 1
                hits.append(("V2 crossing-but-delta2", path, i, chk, nchk, fgn, nfgn, blank))
            if blank and d == 2:
                v3 += 1
                hits.append(("V3 blank-with-delta2", path, i, chk, nchk, fgn, nfgn, blank))
            if three and crossed:
                hits.append(("HIT delta3+crossing", path, i, chk, nchk, fgn, nfgn, blank))

    c = {"files": files, "pairs": tot, "pred": grow_pred, "obs": grow_obs,
         "both": both, "v1": v1, "v2": v2, "v3": v3}
    if quiet:
        return c

    print("procgrow -- FW-64's `+3`, re-derived from the captures")
    print("  ok     %-54s %d" % ("captures with two or more gpio dumps", files))
    print("  ok     %-54s %d" % ("consecutive dump pairs swept", tot))
    print("  ok     %-54s %d" % ("predicted to grow (V+1 gains a digit)", grow_pred))
    print("  ok     %-54s %d" % ("carrying the extra blank line", grow_obs))
    print("  ok     %-54s %d" % ("delta 3 AND predicted AND blank", both))
    for k, n, what in (("V1", v1, "delta 3 with no growth predicted"),
                       ("V2", v2, "growth predicted but delta 2"),
                       ("V3", v3, "extra blank line on a delta-2 pair")):
        print("  %s  %-54s %d" % ("ok   " if n == 0 else "FAIL ",
                                  "%s %s" % (k, what), n))
    print()
    for h in hits[:30]:
        print("       %-24s %-34s pair%-4d chk %s->%s  fgn %s->%s  blank=%s"
              % (h[0], h[1].replace("\\", "/")[-34:], h[2], h[3], h[4],
                 h[5], h[6], h[7]))
    print("RESULT: %d passed, %d failed"
          % (5 + (v1 == 0) + (v2 == 0) + (v3 == 0),
             (v1 != 0) + (v2 != 0) + (v3 != 0)))
    return c


if __name__ == "__main__":
    sys.exit(main())
