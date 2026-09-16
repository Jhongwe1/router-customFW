#!/usr/bin/env python3
"""Predict a boot capture's byte count, and check the model against every
capture this repository already holds.

WHY THIS EXISTS
---------------
Seven images have had their boot-capture length predicted before power and hit
exactly -- 869, 1029, 1069, 1184, 1318, 1424, 1637.  Every one of those seven
was arithmetic done BY HAND in the card.  量 2026-09-17: no tool in `tools/`
computes it, and `rlxfw-marks.py` -- the one that owns the marks -- contains no
byte arithmetic at all.

The eighty-first segment's own closing lesson was that *recording a conclusion
without the re-runnable command that produced it is not recording it*.  This is
that command.

THE MODEL
---------
    boot_bytes = CONST + SUM over boot marks of
                     8 + len(tag)      for rlxfw_mark(tag)
                    17 + len(tag)      for rlxfw_markx(tag, v)

`rlxfw-mark.h:44-51` with `rlxfw_mark.c:85-114`: the macro emits
`"RLXFW-" tag "\\n"` as one .rodata literal and `rlxfw_puts` writes `\\r`
BEFORE the `\\n`, so a bare mark is `6 + len(tag) + 2`.  `rlxfw_puts_hex` adds
`=` and eight upper-case hex digits, unconditionally zero-padded -- the loop is
`for (i = 28; i >= 0; i -= 4)` -- so a value mark is `6 + len(tag) + 1 + 8 + 2`.

CONST is everything that is not a mark: the loader's four lines and the jump
echo, the vendor NIC driver's `panic_printk` banner, and the userspace tail.

🔴 CONST IS MEASURED HERE, NOT ASSUMED.  `--check` recomputes it from every
committed boot capture independently and requires ONE value across all of
them.  量 2026-09-17: **710 on 95 captures spanning seven images**, with each
mark line's own length asserted against the model as it goes.  If a future
image changes `/init` -- which `docs/mfgtest.md` says a manufacturing image
would -- that number moves and this check is what says so.

WHAT IT DOES NOT DO
-------------------
It does not decide which marks are on the BOOT path.  A mark inside a verb
fires when the verb is typed and belongs in no boot budget.  That is a fact
about reachability, and a regex over source cannot settle it -- so the boot
set is taken from the newest MEASURED capture, and any tag in the sources that
is not in it is reported as unclassified rather than guessed at.  A new mark
therefore makes this tool ask a question instead of inventing an answer.
"""

import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30")

MARK_LINE = re.compile(rb"^RLXFW-([A-Za-z0-9_-]+?)(=([0-9A-F]{8}))?\r\n$")
MARK_CALL = re.compile(r'rlxfw_(mark|markx)\(\s*"([A-Za-z0-9_-]+)"')

#: 量, and re-derived by `--check` on every run rather than trusted.
CONST = 710
#: The population floor.  A sweep that finds three captures and agrees with
#: itself proves nothing.
MIN_CAPTURES = 40


def cost(tag, valued):
    return (17 if valued else 8) + len(tag)


def captures():
    pat = os.path.join(ROOT, "bench", "**", "*boot*.log")
    for p in sorted(glob.glob(pat, recursive=True)):
        blob = open(p, "rb").read()
        if b"RLXFW-" in blob:
            yield p, blob


def marks_in(blob):
    """-> [(tag, valued)] in wire order, and the line's own length is
    asserted against the model rather than taken on faith."""
    out = []
    for line in blob.splitlines(keepends=True):
        m = MARK_LINE.match(line)
        if m:
            tag = m.group(1).decode()
            valued = m.group(2) is not None
            if len(line) != cost(tag, valued):
                raise AssertionError(
                    "the model disagrees with a real line: %r is %d bytes, "
                    "model says %d" % (line, len(line), cost(tag, valued)))
            out.append((tag, valued))
    return out


def source_marks():
    """Every mark the sources can emit, with its shape."""
    out = {}
    for path in glob.glob(os.path.join(SRC, "**", "*.c"), recursive=True):
        text = open(path, encoding="utf-8", errors="replace").read()
        for kind, tag in MARK_CALL.findall(text):
            out[tag] = (kind == "markx", os.path.relpath(path, SRC))
    return out


def check():
    consts, n, biggest = {}, 0, 0
    for path, blob in captures():
        ms = marks_in(blob)
        mb = sum(cost(t, v) for t, v in ms)
        consts.setdefault(len(blob) - mb, []).append((len(blob), path))
        n += 1
        biggest = max(biggest, len(ms))

    ok = fails = 0

    good = n >= MIN_CAPTURES
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K1",
                              "the capture corpus is a population (%d with "
                              "marks, floor %d)" % (n, MIN_CAPTURES)))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    good = len(consts) == 1 and CONST in consts
    totals = sorted({t for v in consts.values() for t, _ in v})
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K2",
                              "one non-mark constant across every capture: "
                              "%d, over totals %s" % (CONST, totals)
                              if good else
                              "the constant is NOT one value: %s"
                              % {k: len(v) for k, v in sorted(consts.items())}))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K3 is the control that K1 and K2 cannot be.  Both would pass on a model
    # that is wrong in a way every capture shares.  This one asserts the model
    # reproduces a number written down INDEPENDENTLY, in a frozen card.
    want = 1637
    hit = [t for t in totals if t == want]
    print("  %s  %-10s %s" % ("ok  " if hit else "FAIL", "K3",
                              "the corpus contains the 1,637 that "
                              "bench/2026-09-10 predicted before power"
                              if hit else
                              "1,637 is not among the totals: %s" % totals))
    ok, fails = (ok + 1, fails) if hit else (ok, fails + 1)

    good = biggest >= 50
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K4",
                              "the mark parser reaches a full image "
                              "(%d marks in the richest capture)" % biggest))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    print("%d of %d ok" % (ok, ok + fails))
    return 1 if fails else 0


def predict():
    """The boot set is the newest measured capture's; the sources are then
    diffed against it so a NEW tag is a question and not a silent zero."""
    newest, best = None, -1
    for path, blob in captures():
        ms = marks_in(blob)
        if len(ms) > best:
            newest, best = (path, blob, ms), len(ms)
    path, blob, ms = newest
    boot = [t for t, _v in ms]
    mb = sum(cost(t, v) for t, v in ms)

    print("baseline   %s" % os.path.relpath(path, ROOT))
    print("           %d bytes = %d const + %d marks (%d marks)"
          % (len(blob), len(blob) - mb, mb, len(ms)))

    src = source_marks()
    unseen = sorted(t for t in src if t not in set(boot))
    print()
    print("marks in the sources that this capture does NOT carry: %d"
          % len(unseen))
    print("  These are on-demand verbs or failure-path twins unless something")
    print("  says otherwise.  A tag here that SHOULD fire at boot is the one")
    print("  thing that would make the prediction below wrong.")
    for t in unseen:
        valued, where = src[t]
        print("    %-10s %-6s %-2d bytes  %s"
              % (t, "markx" if valued else "mark", cost(t, valued), where))

    print()
    print("PREDICTION for an image whose boot path is unchanged: %d bytes"
          % len(blob))
    print("  = %d const + %d marks.  Add `8 + len(tag)` or `17 + len(tag)`"
          % (len(blob) - mb, mb))
    print("  for each NEW boot mark, and re-derive the const if /init changes.")
    return 0


def main(argv):
    print("bootbytes 1.0  --  boot capture length, derived not copied")
    if len(argv) > 1 and argv[1] == "predict":
        return predict()
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
