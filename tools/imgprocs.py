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
image**.  The vendor registers 42 entries; rlxfw's board template registers 8
(量 the device's own `ls /proc/rtl865x/`, `bench/2026-09-22b/X8b-ASICLS`).
This tool is what caught it, before power.  🔄 2026-09-26: this line said 13
— the PRESENT count this tool prints, five of whose names are literals of
retained non-vendor code (`SPEC.md` `NET-42`).

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
  * `port_status` and `asicCounter` — read on this die, must be PRESENT, and
    VENDOR-UNIQUE: 量 2026-09-26, over the `.rodata`/`.data` of `r6b6q2`'s 667
    compiled objects one by one, each name's literal occurs in a vendor object
    and in no other
  * `rtl819x-switch` — this project's own driver, must be PRESENT
  * a synthetic name — must be ABSENT
If the three positives do not fire, the search is broken and the absences
below it mean nothing.  🔄 2026-09-26: `memory` was a positive control until
this date.  One of its two hits is `net/core/sock.o`, so it reads PRESENT on
an image with no vendor tree at all: a control that could not fail where a
vendor control has to.  The tool now REFUSES any vendor positive control that
is on `SHARED`, and `--self-test` fails if one is.

`--witness NAME` (repeatable, 2026-09-26, `R6b-7`) names an entry THIS image
must carry, with the same NUL-bounded search: absent, the run is REFUSED.
It is an option and not a fourth control because it is a property of one
image -- `rtl819x-mdio` exists from switch 1.3 on, and the images cards still
boot before that (`r6b2q`, `r6b6q`) must keep passing the default run.
`--self-test` shows it refusing and permitting (W1-W3).

WHAT IT CANNOT DO
-----------------
It reads a **flat** image (`vmlinux_img`, the `objcopy -O binary` output), not
an ELF and not a compressed `nfjrom`: a `RLXFW`-style string count over an
LZMA stream is 0 for every image including one's own.  And a name present in
`.rodata` is a name the code *can* register; it is not proof that the
registration ran — nor, for a name on `SHARED`, that the vendor's code is what
carries it.  The device's own `ls /proc/rtl865x/` is the other half and costs
one cell.  ABSENT is the half this tool can stand behind: a name absent from
the image is a name no object in it carries.

usage
    imgprocs.py <flat-image> [<vendor-source.c>] [--witness NAME]...
    imgprocs.py --self-test
"""
import os
import re
import sys

DEFAULT_SRC = ("/home/key/fwre-work/rebuild/src-vendor/rtl819x-toolchain/"
               "linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c")

#: rlxfw's own entry: a positive control that is not the vendor's.
OWN = "rtl819x-switch"

CONTROLS = (("port_status", True), ("asicCounter", True),
            (OWN, True), ("zzzz-not-a-name", False))

#: 量 2026-09-26 (`SPEC.md` `NET-42`): names of the vendor's `/proc/rtl865x/`
#: set whose NUL-delimited literal ALSO occurs in the `.rodata`/`.data` of a
#: retained, non-vendor object of `r6b6q2` (667 compiled objects searched one
#: by one; controls: `rtl819x-switch` found in `rtl819x-switch.o`, the
#: synthetic name nowhere).  PRESENT says nothing about the vendor for these.
SHARED = {"stats": "8192cd_proc.o",
          "arp": "arp.o, x_tables.o",
          "ip": "x_tables.o",
          "pppoe": "pppoe.o",
          "igmp": "igmp.o",
          "memory": "sock.o",
          "mac": "xt_mac.o"}


def parse_names(txt):
    """The distinct names at the vendor's registration sites, in order."""
    names = []
    for m in re.finditer(r'create_proc_(?:read_)?entry\s*\(\s*"([^"]+)"', txt):
        if m.group(1) not in names:
            names.append(m.group(1))
    return names


def parse_args(argv):
    """(positional args, witnesses, refusal or None) from argv[1:]."""
    args, witnesses = [], []
    i = 0
    while i < len(argv):
        if argv[i] == "--witness":
            if i + 1 >= len(argv) or not argv[i + 1]:
                return args, witnesses, "REFUSED: --witness needs a name"
            witnesses.append(argv[i + 1])
            i += 2
            continue
        args.append(argv[i])
        i += 1
    return args, witnesses, None


def count(img, n):
    return img.count(b"\x00" + n.encode() + b"\x00")


def evaluate(img, names, out, controls=None, witnesses=()):
    """The whole verdict on one image; `out` collects the printed lines.
    Returns 0 on a report, 2 on a refusal.  `controls` exists for the
    self-test, which must see the guard below refuse a bad set."""
    if controls is None:
        controls = CONTROLS
    if not names:
        out.append("REFUSED: no create_proc_entry sites in the source -- the "
                   "population would be empty and a green here would be a "
                   "claim about nothing")
        return 2
    cannot_fail = [n for n, want in controls
                   if want and n != OWN and n in SHARED]
    if cannot_fail:
        out.append("REFUSED: vendor positive control(s) %s also occur in "
                   "retained non-vendor code (SHARED) -- they read present "
                   "on an image with no vendor tree, so they cannot fail"
                   % ", ".join(cannot_fail))
        return 2
    out.append("")
    out.append("controls")
    bad = 0
    for n, want_present in controls:
        c = count(img, n)
        ok = (c > 0) == want_present
        if not ok:
            bad += 1
        out.append("  %-18s %d   %s   %s"
                   % (n, c, "present" if want_present else "absent",
                      "ok" if ok else "FAILED"))
    if bad:
        out.append("")
        out.append("REFUSED: %d control(s) failed -- the search is broken and "
                   "the absences below would be meaningless." % bad)
        return 2

    if witnesses:
        out.append("")
        out.append("witnesses (this image must carry each)")
        missing = 0
        for n in witnesses:
            c = count(img, n)
            missing += 0 if c else 1
            out.append("  %-18s %d   present   %s"
                       % (n, c, "ok" if c else "ABSENT"))
        if missing:
            out.append("")
            out.append("REFUSED: %d witness(es) absent -- this is not the "
                       "image the card was written for." % missing)
            return 2

    present = [n for n in names if count(img, n)]
    absent = [n for n in names if not count(img, n)]
    shared = [n for n in present if n in SHARED]
    out.append("")
    out.append("PRESENT in this image (%d of %d):" % (len(present), len(names)))
    for n in present:
        if n in SHARED:
            out.append("    %-16s shared: also in %s" % (n, SHARED[n]))
        else:
            out.append("    %s" % n)
    out.append("  %d of the %d are shared with retained non-vendor code: "
               "present there is not evidence the vendor registers them"
               % (len(shared), len(present)))
    out.append("")
    out.append("ABSENT from this image (%d of %d):" % (len(absent), len(names)))
    out.append("    " + " ".join(absent))
    out.append("")
    out.append("  A name here is a name a bench card must not `cat`.")
    return 0


def self_test():
    """Synthetic images only; no file is read.  Each case names what it
    catches, and the fixture list below is kept apart from `SHARED` so that
    shrinking `SHARED` is itself caught."""
    measured_nonvendor = ("stats", "arp", "ip", "pppoe", "igmp", "memory",
                          "mac")

    def img_of(*ns):
        return b"\x00" + b"\x00".join(n.encode() for n in ns) + b"\x00"

    positives = [n for n, w in CONTROLS if w]
    base = ["port_status", "asicCounter", "mmd", "vlan"]
    cases = []

    def case(label, ok, detail):
        cases.append((label, ok, detail))

    out = []
    rc = evaluate(img_of(*(positives + ["mmd"])), base, out)
    case("I1", rc == 0 and "    mmd" in out and "    vlan" in out[-3],
         "all positives present, synthetic absent -> rc 0, mmd PRESENT, "
         "vlan ABSENT (rc %d)" % rc)

    for p in positives:
        out = []
        rest = [q for q in positives if q != p]
        rc = evaluate(img_of(*(rest + ["mmd"])), base, out)
        case("I2-" + p, rc == 2, "positive control %s missing -> REFUSED "
             "(rc %d)" % (p, rc))

    out = []
    rc = evaluate(img_of(*(positives + ["zzzz-not-a-name"])), base, out)
    case("I3", rc == 2, "the synthetic name present -> REFUSED (rc %d)" % rc)

    vendor_free = img_of(*(measured_nonvendor + (OWN,)))
    fire = [p for p in positives if p != OWN and count(vendor_free, p)]
    case("I4", not fire, "no vendor positive control fires on an image "
         "holding only retained non-vendor literals and rlxfw's own "
         "(fired: %s)" % (", ".join(fire) or "none"))

    out = []
    rc = evaluate(vendor_free, base, out)
    case("I5", rc == 2, "that vendor-free image is REFUSED, not reported "
         "(rc %d)" % rc)

    lost = [n for n in measured_nonvendor if n not in SHARED]
    case("I6", not lost, "SHARED still carries every measured non-vendor "
         "name (missing: %s)" % (", ".join(lost) or "none"))

    out = []
    rc = evaluate(img_of(*(positives + ["memory"])), base + ["memory"], out)
    labelled = any(l.startswith("    memory") and "shared" in l for l in out)
    case("I7", rc == 0 and labelled, "a PRESENT name on SHARED is printed "
         "as shared (rc %d, labelled %s)" % (rc, labelled))

    case("I8", count(b"\x00ip_tables\x00", "ip") == 0
         and count(b"\x00ip\x00", "ip") == 1,
         "the literal is NUL-delimited: `ip` inside `ip_tables` is not `ip`")

    src = ('x = create_proc_entry("a", 0, d); '
           'y = create_proc_read_entry( "b", 0, d); '
           'z = create_proc_entry("a", 0, d);')
    case("I9", parse_names(src) == ["a", "b"],
         "registration sites parsed, both forms, duplicates once "
         "(got %s)" % parse_names(src))

    out = []
    rc = evaluate(img_of(*positives), [], out)
    case("I10", rc == 2, "an empty population is a refusal (rc %d)" % rc)

    out = []
    old = (("port_status", True), ("memory", True), (OWN, True),
           ("zzzz-not-a-name", False))
    rc = evaluate(img_of("port_status", "memory", OWN), base, out,
                  controls=old)
    refused = rc == 2 and any("cannot fail" in l for l in out)
    case("I11", refused, "the control set used until 2026-09-26, with "
         "`memory`, is refused before anything is counted, though every "
         "control in it would read ok (rc %d)" % rc)

    # --witness, both ways (R6b-7).  The witness is a name the default run
    # does not know, so only the option can make its absence a refusal.
    out = []
    rc = evaluate(img_of(*(positives + ["mmd", "rtl819x-mdio"])), base, out,
                  witnesses=["rtl819x-mdio"])
    carried = any(l.startswith("  rtl819x-mdio") and l.endswith("ok")
                  for l in out)
    case("W1", rc == 0 and carried, "a witness the image carries is printed "
         "ok and the run reports (rc %d, printed %s)" % (rc, carried))

    out = []
    rc = evaluate(img_of(*(positives + ["mmd"])), base, out,
                  witnesses=["rtl819x-mdio"])
    plain = []
    rc0 = evaluate(img_of(*(positives + ["mmd"])), base, plain)
    case("W2", rc == 2 and rc0 == 0
         and any("witness(es) absent" in l for l in out),
         "the same image without the witness entry is REFUSED with the "
         "option (rc %d) and reported without it (rc %d)" % (rc, rc0))

    got = parse_args(["img", "--witness", "a", "src", "--witness", "b"])
    bare = parse_args(["img", "--witness"])
    case("W3", got == (["img", "src"], ["a", "b"], None)
         and bare[2] is not None,
         "--witness repeats and leaves the positionals alone; a --witness "
         "with no name is a refusal (got %s; bare %s)" % (got, bare[2]))

    good = 0
    for label, ok, detail in cases:
        good += ok
        print("  %-4s %-14s %s" % ("ok" if ok else "FAIL", label, detail))
    print("%d of %d ok" % (good, len(cases)))
    return 0 if good == len(cases) else 1


def main(argv):
    if len(argv) >= 2 and argv[1] == "--self-test":
        print("imgprocs 1.2  --  self-test")
        return self_test()
    args, witnesses, err = parse_args(argv[1:])
    if err:
        print(err)
        return 3
    if not args or len(args) > 2:
        print(__doc__.strip())
        return 3
    img_path = args[0]
    src_path = args[1] if len(args) > 1 else DEFAULT_SRC
    for p in (img_path, src_path):
        if not os.path.isfile(p):
            print("REFUSED: no such file: %s" % p)
            return 3

    txt = open(src_path, encoding="utf-8", errors="replace").read()
    names = parse_names(txt)
    print("imgprocs 1.2")
    print("  image   %s  (%d bytes)" % (img_path, os.path.getsize(img_path)))
    print("  source  %s" % src_path)
    print("  vendor registers %d distinct entry name(s)" % len(names))

    with open(img_path, "rb") as fh:
        img = fh.read()
    out = []
    rc = evaluate(img, names, out, witnesses=witnesses)
    for line in out:
        print(line)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
