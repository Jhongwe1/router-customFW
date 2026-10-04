#!/usr/bin/env python3
"""ctrwin.py -- the counter's flash window, and since R8b the two slot windows,
against the forbidden list, through `tools/flashwin.py` rather than through a
restatement of the rule.

`CLAUDE.md`: *"new tools import `flashwin.overlaps_forbidden` rather than restate
the rule."*  `src/rlxboot/flashread.c` cannot: it is C in a freestanding payload,
so its two compile-time refusals spell the `H601` range out.  This is the check
that is not a restatement -- it reads the offset and the length out of
`src/rlxboot/rlxboot.h` and `container.h` and asks `flashwin` itself.

    ctrwin.py <repo>

Exit 0 clean, 1 the counter window is forbidden, 2 refused (could not read a
constant, or the control did not fire).
"""

import os
import re
import sys


def grab(path, name, base=16):
    txt = open(path, "r", encoding="utf-8").read()
    m = re.search(r"^#define\s+%s\s+0x([0-9A-Fa-f]+)UL" % name, txt, re.M)
    if m:
        return int(m.group(1), base)
    m = re.search(r"^#define\s+%s\s+(\d+)\s*$" % name, txt, re.M)
    if m:
        return int(m.group(1), 10)
    sys.stderr.write("ctrwin: cannot read %s out of %s\n" % (name, path))
    raise SystemExit(2)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: ctrwin.py <repo>\n")
        return 2
    repo = sys.argv[1]
    sys.path.insert(0, os.path.join(repo, "tools"))
    try:
        import flashwin
    except ImportError as e:
        sys.stderr.write("ctrwin: cannot import tools/flashwin.py: %s\n" % e)
        return 2

    rh = os.path.join(repo, "src", "rlxboot", "rlxboot.h")
    at = grab(rh, "RLXB_CTR_FLASH")
    n = grab(os.path.join(repo, "src", "rlxboot", "container.h"), "RLXU_CTR_BYTES")

    hit = flashwin.overlaps_forbidden(at, n)
    print("ctrwin: the counter window is 0x%06X + %d bytes" % (at, n))
    if hit:
        print("ctrwin: REFUSED -- it overlaps 0x%06X-0x%06X (%s)"
              % (hit[0], hit[1] - 1, hit[2]))
        return 1

    # R8b: the two slot windows `slots.c` reads, through the same function.
    # `slots.c`'s compile-time refusals restate the R8b layout; this asks
    # `flashwin` itself, as the counter's check does.
    size = grab(rh, "RLXB_SLOT_SIZE")
    for name in ("A", "B"):
        sat = grab(rh, "RLXB_SLOT_%s_FLASH" % name)
        hit = flashwin.overlaps_forbidden(sat, size)
        print("ctrwin: slot %s's window is 0x%06X + %d bytes" % (name, sat, size))
        if hit:
            print("ctrwin: REFUSED -- it overlaps 0x%06X-0x%06X (%s)"
                  % (hit[0], hit[1] - 1, hit[2]))
            return 1

    # THE CONTROL.  A checker that always says "clear" is not a checker: a window
    # placed inside H601 must come back forbidden, and one ending exactly at its
    # base must not.  Both directions, and `flashwin`'s own docstring says the
    # boundary is the case that gets this wrong.
    inside = flashwin.overlaps_forbidden(0x006800, n)
    abutting = flashwin.overlaps_forbidden(0x006000 - n, n)
    if inside is None:
        print("ctrwin: REFUSED -- a window inside the forbidden region came back"
              " clear; the check is broken")
        return 2
    if abutting is not None:
        print("ctrwin: REFUSED -- a window ENDING at the forbidden base came back"
              " forbidden; the check is not discriminating on the boundary")
        return 2
    print("ctrwin: ok -- clear, and the control fires both ways"
          " (inside -> %s, abutting -> clear)" % inside[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
