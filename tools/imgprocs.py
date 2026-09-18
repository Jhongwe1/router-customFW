#!/usr/bin/env python3
"""Which of the vendor's /proc entries survive into a built image.

WHY THIS EXISTS
---------------
`SPEC.md` `FW-46`: nothing in this repository could ask *can this image run
this command* before a bench card was frozen, and `FW-26` is the same class
one instance earlier.  A card that names a `/proc` file the image does not
have produces a capture holding `No such file or directory` — and
`check-predictions` scores existence and mtime, **not content**, so that cell
reports as a pass.

量 2026-09-19 (seating 27): two cells of a frozen card named
`/proc/rtl865x/vlan` and `/proc/rtl865x/pvid`, and **neither exists in the
image**.  The vendor registers 42 entries; rlxfw's board template keeps 13.
This tool is what caught it, before power.

THE METHOD, AND WHY IT IS NOT A PLAIN `grep`
--------------------------------------------
A `/proc` entry's name reaches the image as a NUL-terminated `.rodata` string
literal, so the search is for `b"\\x00name\\x00"` and not for the bare name —
a short name like `l2`, `ip` or `mac` is a substring of a dozen other
literals, and a plain find would report every one of them as present.

The names are read out of the vendor's own registration sites
(`create_proc_entry("<name>", …)`), so the population is *what the driver
registers* rather than a list somebody typed.

CONTROLS, and they are the point
--------------------------------
A tool reporting `0` is making a claim.  Every run prints four:
  * `port_status` and `memory` — read on this die, must be PRESENT
  * `rtl819x-switch` — this project's own driver, must be PRESENT
  * a synthetic name — must be ABSENT
If the three positives do not fire, the search is broken and the absences
below it mean nothing.

WHAT IT CANNOT DO
-----------------
It reads a **flat** image (`vmlinux_img`, the `objcopy -O binary` output), not
an ELF and not a compressed `nfjrom`: a `RLXFW`-style string count over an
LZMA stream is 0 for every image including one's own.  And a name present in
`.rodata` is a name the code *can* register; it is not proof that the
registration ran.  The device's own `ls /proc/rtl865x/` is the other half and
costs one cell.

usage
    imgprocs.py <flat-image> [<vendor-source.c>]
"""
import os
import re
import sys

DEFAULT_SRC = ("/home/key/fwre-work/rebuild/src-vendor/rtl819x-toolchain/"
               "linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c")

CONTROLS = (("port_status", True), ("memory", True),
            ("rtl819x-switch", True), ("zzzz-not-a-name", False))


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 3
    img_path = argv[1]
    src_path = argv[2] if len(argv) > 2 else DEFAULT_SRC
    for p in (img_path, src_path):
        if not os.path.isfile(p):
            print("REFUSED: no such file: %s" % p)
            return 3

    txt = open(src_path, encoding="utf-8", errors="replace").read()
    names = []
    for m in re.finditer(r'create_proc_(?:read_)?entry\s*\(\s*"([^"]+)"', txt):
        if m.group(1) not in names:
            names.append(m.group(1))
    if not names:
        print("REFUSED: no create_proc_entry sites in %s -- the population "
              "would be empty and a green here would be a claim about "
              "nothing" % src_path)
        return 2
    print("imgprocs 1.0")
    print("  image   %s  (%d bytes)" % (img_path, os.path.getsize(img_path)))
    print("  source  %s" % src_path)
    print("  vendor registers %d distinct entry name(s)" % len(names))

    with open(img_path, "rb") as fh:
        img = fh.read()

    def count(n):
        return img.count(b"\x00" + n.encode() + b"\x00")

    print("")
    print("controls")
    bad = 0
    for n, want_present in CONTROLS:
        c = count(n)
        ok = (c > 0) == want_present
        if not ok:
            bad += 1
        print("  %-18s %d   %s   %s"
              % (n, c, "present" if want_present else "absent",
                 "ok" if ok else "FAILED"))
    if bad:
        print("")
        print("REFUSED: %d control(s) failed -- the search is broken and the "
              "absences below would be meaningless." % bad)
        return 2

    present = [n for n in names if count(n)]
    absent = [n for n in names if not count(n)]
    print("")
    print("PRESENT in this image (%d of %d):" % (len(present), len(names)))
    for n in present:
        print("    %s" % n)
    print("")
    print("ABSENT from this image (%d of %d):" % (len(absent), len(names)))
    print("    " + " ".join(absent))
    print("")
    print("  A name here is a name a bench card must not `cat`.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
