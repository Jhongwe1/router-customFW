#!/usr/bin/env python3
"""Diff the register columns of two /proc/rtl819x-switch captures.

The `diff` VERB prints a count.  This is the evidence behind the count: it
reads the `r <name> <off> <live> <slot0> <both><dumb>` rows out of two
captures and says which registers moved.  CRLF is stripped first -- every
capture line is CRLF and `[ "1\\r" = "1" ]` is false.

usage: s87-diff.py A.log B.log [label]
"""
import re
import sys

ROW = re.compile(r"^r (\S+)\s+([0-9A-F]{4}) ([0-9A-F]{8}) ([0-9A-F]{8}) (\d)(\d)$")


def read(path):
    out = {}
    order = []
    with open(path, "rb") as fh:
        text = fh.read().replace(b"\r", b"").decode("utf-8", "replace")
    for ln in text.split("\n"):
        m = ROW.match(ln)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3), m.group(4),
                               m.group(5), m.group(6))
            order.append(m.group(1))
    return out, order


def main():
    a, order = read(sys.argv[1])
    b, _ = read(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) > 3 else ""
    if not a or not b:
        print("REFUSED: %d rows in A, %d rows in B" % (len(a), len(b)))
        return 2
    if len(a) != 37 or len(b) != 37:
        print("REFUSED: expected 37 rows each, got %d and %d" % (len(a), len(b)))
        return 2

    moved, same = [], []
    for n in order:
        if a[n][1] != b[n][1]:
            moved.append(n)
        else:
            same.append(n)

    print("%s" % label)
    print("  A = %s" % sys.argv[1])
    print("  B = %s" % sys.argv[2])
    print("  %d of 37 registers differ" % len(moved))
    print()
    print("  %-10s %-5s %-10s %-10s %s" % ("reg", "off", "A", "B", "dumb?"))
    for n in moved:
        print("  %-10s %-5s %-10s %-10s %s"
              % (n, a[n][0], a[n][1], b[n][1],
                 "written by dumb" if a[n][4] == "1" else ""))
    print()
    dumb_moved = [n for n in moved if a[n][4] == "1"]
    dumb_total = [n for n in order if a[n][4] == "1"]
    nondumb_moved = [n for n in moved if a[n][4] == "0"]
    print("  of the %d registers `dumb` writes, %d moved: %s"
          % (len(dumb_total), len(dumb_moved), " ".join(dumb_moved) or "(none)"))
    print("  of the %d it never writes,      %d moved: %s"
          % (37 - len(dumb_total), len(nondumb_moved),
             " ".join(nondumb_moved) or "(none)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
