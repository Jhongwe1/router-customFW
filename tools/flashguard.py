#!/usr/bin/env python3
"""Refuse a flash destination that would brick this device, or lose H601.

This is a REFUSAL, and it is the one new checker gate `R8a` justifies.  The
reason is in `docs/loader-flash-write.md` § 1, read out of this unit's own
loader: `burn()` at `0x80401318` matches a four-byte section signature, checks
a checksum, and writes -- and its **only** bound is the top one, the chip
capacity out of the SPI descriptor.  An overlong write is *truncated* at the
end of the chip rather than rejected, and

    **there is no lower bound at all.**

`boot` is one of the eight signatures `burn()` accepts, so the vendor's own
upgrade path will write flash offset 0 if a section header asks it to.  That
document's own sentence is the specification for this file: *"the rule in
`CLAUDE.md` -- never write `0x000000`-`0x005FFF` -- has to be enforced by our
own tooling.  **The device does not enforce it.**"*

There is one device and no spare.

A library first, a CLI second
----------------------------
`mkfw2.py` imports `permitted()`; so may anything else that computes a flash
destination.  Restating the ranges in a second file is how one of them drifts,
and `H601` is not restated even here: that range has exactly one owner,
`tools/flashwin.py`, and `permitted()` asks it through
`flashwin.overlaps_forbidden` rather than comparing numbers of its own.  `F3`
in `--self-test` is what fails if that delegation is ever replaced by a copy.

What this cannot see, stated before it is used
----------------------------------------------
* It guards a **destination range**, which is an argument someone computed.  It
  does not read the loader's `burnAddr`, it cannot see a `J` into code that
  writes flash, and it cannot see a TFTP upload made while `AUTOBURN` is armed
  (`cardcheck.py`'s `FW-113` note lists the same blind spots for the console
  side).  A permit from this file is not permission to write anything.
* It says nothing about whether a write is a good idea.  `0x060000` is
  PERMITTED here and holds the vendor kernel that gate `R9`'s vendor column
  needs; once that is overwritten it is gone.  `notes/update-chain.md`
  § "What a provisioning write destroys" is that argument, and it is a
  judgement for the owner, not a range check.
* Nothing in `R8a` writes flash.  This file emits no command, and
  `tools/test-mkfw2.sh` `X1`-`X3` assert that none of `FLW`, `EW`, `EB` or a
  non-zero `AUTOBURN` appears in what these tools print.

Exit
    0  the range is PERMITTED
    1  the range is REFUSED -- one line saying which region and why
    2  a control failed (`--self-test`)
    3  usage / input refusal
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashwin  # noqa: E402  -- the H601 rule has exactly one owner

VERSION = "flashguard 1.0"

# 量 `FLS-21`/`SPEC.md` § 11: 4 MiB SPI NOR, and `burn()` truncates rather than
# refuses at this boundary (`docs/loader-flash-write.md` § 1), so a destination
# that runs past it is a silently short write.  Refused, not clipped.
CHIP_SIZE = 0x00400000

# The ranges this file owns.  `H601` is deliberately ABSENT: it is delegated.
# Each row is (lo, hi_exclusive, id, why -- what is lost, not what the rule is).
OWN_FORBIDDEN = [
    (0x000000, 0x006000, "loader",
     "the boot loader (CLAUDE.md Never).  burn() has no lower bound "
     "(docs/loader-flash-write.md 1); a partial write here is an "
     "unrecoverable brick and there is no spare unit"),
    (0x020000, 0x030000, "rescue",
     "the read-only rescue slot rlxboot-rescue (plan D6).  The stock loader "
     "scans 0x020000, so this is the one image that still boots when "
     "0x010000 is broken; the update path never writes it"),
]

# What `flashwin` answers for, named here only so a refusal can say the id.
DELEGATED_ID = "H601"


class Refusal(object):
    """One refusal: which region, and what is lost.  Falsy is never a refusal."""

    __slots__ = ("lo", "hi", "rid", "why")

    def __init__(self, lo, hi, rid, why):
        self.lo, self.hi, self.rid, self.why = lo, hi, rid, why

    def __str__(self):
        return ("0x%06X-0x%06X %s: %s"
                % (self.lo, self.hi - 1, self.rid, self.why))


def forbidden_ranges():
    """-> [(lo, hi, id, why)] including the delegated one, sorted by lo.

    The `H601` row's bounds are read back OUT of `flashwin.FORBIDDEN` rather
    than written here, so a table printed by this file and a decision made by
    it cannot disagree.
    """
    rows = list(OWN_FORBIDDEN)
    for lo, hi, why in flashwin.FORBIDDEN:
        rows.append((lo, hi, DELEGATED_ID,
                     why + ".  Never restored by a reset, never published "
                           "(delegated to tools/flashwin.py)"))
    return sorted(rows)


def check(at, nbytes):
    """-> a Refusal for [at, at+nbytes), or None if the range is PERMITTED.

    Half-open on both sides, the same convention `flashwin.overlaps_forbidden`
    uses: a range ENDING at 0x006000 is clear, and a range whose last byte is
    0x006000 is not.  Both directions are cases `F4`-`F7`.
    """
    if not isinstance(at, int) or not isinstance(nbytes, int):
        raise ValueError("a flash range is two integers, got %r and %r"
                         % (type(at).__name__, type(nbytes).__name__))
    if nbytes <= 0:
        raise ValueError("a destination length of %d is not a range; a guard "
                         "asked about nothing cannot answer" % nbytes)
    if at < 0:
        raise ValueError("negative flash offset 0x%x" % at)
    end = at + nbytes
    if end > CHIP_SIZE:
        return Refusal(at, end, "off-chip",
                       "ends at 0x%06X, past the %d-byte chip.  burn() "
                       "TRUNCATES at capacity instead of refusing "
                       "(docs/loader-flash-write.md 1), so this is a "
                       "silently short write, not an error" % (end, CHIP_SIZE))
    # The delegated range first, so that H601 is never reported by a local
    # comparison even if someone later adds its numbers to OWN_FORBIDDEN.
    hit = flashwin.overlaps_forbidden(at, nbytes)
    if hit is not None:
        lo, hi, why = hit
        return Refusal(lo, hi, DELEGATED_ID, why)
    for lo, hi, rid, why in OWN_FORBIDDEN:
        if at < hi and end > lo:
            return Refusal(lo, hi, rid, why)
    return None


def permitted(at, nbytes):
    """-> True if [at, at+nbytes) may be a flash destination.  Never raises
    for a well-formed range; a malformed one is a ValueError, not a False."""
    return check(at, nbytes) is None


def refusal_text(at, nbytes):
    """-> the one-line refusal, or None.  The house format for a refusal."""
    r = check(at, nbytes)
    if r is None:
        return None
    return ("flashguard: REFUSED 0x%06X+0x%X (0x%06X-0x%06X) overlaps %s"
            % (at, nbytes, at, at + nbytes - 1, r))


# ---------------------------------------------------------------- the CLI
def die(msg, code=3):
    print("flashguard: %s" % msg, file=sys.stderr)
    raise SystemExit(code)


def cmd_check(args):
    try:
        r = check(args.at, args.bytes)
    except ValueError as exc:
        die(str(exc))
    if r is None:
        print("flashguard: PERMITTED 0x%06X+0x%X (0x%06X-0x%06X)"
              % (args.at, args.bytes, args.at, args.at + args.bytes - 1))
        return 0
    print(refusal_text(args.at, args.bytes), file=sys.stderr)
    return 1


def cmd_table(args):
    """The refusal AND permission table.  A guard is shown permitting too."""
    print("%s -- forbidden ranges" % VERSION)
    print("  %-17s %-8s %s" % ("range", "id", "why"))
    for lo, hi, rid, why in forbidden_ranges():
        print("  0x%06X-0x%06X %-8s %s" % (lo, hi - 1, rid, why))
    print("  0x%06X-          off-chip past the %d-byte chip"
          % (CHIP_SIZE, CHIP_SIZE))
    print("")
    print("  permitted, one probe per neighbour (a guard that refuses "
          "everything is not a guard):")
    for at, n, what in NEIGHBOURS:
        r = check(at, n)
        print("  %-9s 0x%06X+0x%-6X %s"
              % ("PERMIT" if r is None else "REFUSE", at, n, what))
    return 0


# For every forbidden range, the legitimate neighbour on each side that MUST be
# permitted.  These are the positive controls plan precondition 3 asks for, and
# they are data so that the table and the tests cannot drift apart.
NEIGHBOURS = [
    (0x005000, 0x1000, "the last 4 KiB below the loader region's top -- "
                       "REFUSED, it is inside"),
    (0x008000, 0x1000, "COMPDS/COMPCS, the first sector above H601"),
    (0x010000, 0x10000, "slot 0 / rlxboot at 0x010000 (plan D6)"),
    (0x030000, 0x10000, "the sector above the rescue slot"),
    (0x060000, 0x10000, "the vendor kernel's sector -- permitted, and it is "
                        "what R9's vendor column needs"),
    (0x3F0000, 0x200, "the anti-rollback bitmap (SPEC-R8a 4)"),
    (0x3FFE00, 0x200, "the last 512 bytes of the chip"),
]


def self_test():
    rows = []

    def add(cid, what, ok, detail=""):
        rows.append((cid, what, ok, detail))

    # ------------------------------------------------- F1-F2  it refuses
    for rid, probe in (("loader", 0x000000), ("loader", 0x005FFF),
                       ("H601", 0x006000), ("H601", 0x007FFF),
                       ("rescue", 0x020000), ("rescue", 0x02FFFF)):
        r = check(probe, 1)
        add("F1", "0x%06X (1 byte) is REFUSED as %s" % (probe, rid),
            r is not None and r.rid == rid,
            str(r).split(":")[0] if r else "PERMITTED -- the guard is open")
    whole = check(0x000000, CHIP_SIZE)
    add("F2", "the whole chip as one range is REFUSED",
        whole is not None, str(whole).split(":")[0] if whole else "PERMITTED")

    # ------------------------------------------------- F3  the delegation
    # 🔴 If `H601` is ever restated here instead of delegated, this is what
    # goes red: the probe asks flashwin directly and requires this file to
    # agree with it on all four corners, and requires OWN_FORBIDDEN to be
    # silent about the range.  A copied constant passes the first half and
    # fails the second.
    corners = (0x005FFF, 0x006000, 0x007FFF, 0x008000)
    agree = all((flashwin.overlaps_forbidden(a, 1) is not None)
                == (check(a, 1) is not None and check(a, 1).rid == "H601")
                for a in corners)
    not_restated = not any(lo <= 0x006000 < hi or lo < 0x008000 <= hi
                           for lo, hi, _, _ in OWN_FORBIDDEN)
    add("F3", "H601 is DELEGATED to flashwin, not restated here",
        agree and not_restated,
        "corners agree %s, OWN_FORBIDDEN silent %s" % (agree, not_restated))

    # ------------------------------------------------- F4-F7  the boundaries
    # 🔴 This is flashwin's C9 boundary case and it reads the opposite way
    # here.  0x005F00+0x100 ends exactly at 0x006000, so it is CLEAR of H601 --
    # and it is still refused, because the loader region owns it.  The two
    # ranges are adjacent, so "clear of H601" is not "permitted", and a guard
    # built out of flashwin alone would have let this one through.
    r4 = check(0x005F00, 0x100)
    add("F4", "0x005F00+0x100 ends clear of H601 and is REFUSED as loader",
        flashwin.overlaps_forbidden(0x005F00, 0x100) is None
        and r4 is not None and r4.rid == "loader",
        "flashwin says clear, flashguard says %s" % (r4.rid if r4 else "clear"))
    add("F5", "0x008000+0x1000, the sector above H601, IS permitted",
        permitted(0x008000, 0x1000), "positive control")
    add("F6", "0x01F000+0x1000, the sector below the rescue slot, IS "
        "permitted", permitted(0x01F000, 0x1000), "positive control")
    add("F7", "0x030000+0x1000, the sector above it, IS permitted",
        permitted(0x030000, 0x1000), "positive control")
    add("F8", "0x01F800+0x1000, straddling the rescue slot's start, is "
        "REFUSED", not permitted(0x01F800, 0x1000),
        "the last byte is inside")
    add("F9", "0x02F800+0x1000, straddling its end, is REFUSED",
        not permitted(0x02F800, 0x1000), "the first byte is inside")

    # ------------------------------------------- F10  the positive controls
    # The table's own neighbour list, driven.  Every row whose text does not
    # say REFUSED must be permitted, and the one that does must be refused --
    # so the list cannot be quietly emptied to make this green.
    good = []
    for at, n, what in NEIGHBOURS:
        want_refused = "REFUSED" in what
        good.append(permitted(at, n) != want_refused)
    add("F10", "every neighbour in the table gets the verdict its text "
        "claims (%d rows)" % len(NEIGHBOURS), all(good) and len(NEIGHBOURS) >= 6,
        "%d/%d" % (sum(good), len(NEIGHBOURS)))

    # ------------------------------------------- F11-F13  the chip bound
    add("F11", "a range ending exactly at the chip's end IS permitted",
        permitted(CHIP_SIZE - 0x1000, 0x1000), "0x3FF000+0x1000")
    r = check(CHIP_SIZE - 0x1000, 0x1001)
    add("F12", "one byte past the chip is REFUSED (burn() truncates, not "
        "refuses)", r is not None and r.rid == "off-chip",
        r.rid if r else "PERMITTED")
    # 🔴 量 by this guard, 2026-09-30, and it is the finding that fixes the
    # layout: today's rlxfw image is 1,114,112 bytes, so a FULL image based at
    # 0x010000 runs to 0x11FFFF and swallows the rescue slot whole.  The guard
    # said so before anyone drew a map.  0x010000 therefore holds `rlxboot`
    # alone (tens of KiB), and a full slot cannot start below 0x030000.
    r13 = check(0x010000, 1114112)
    add("F13", "a FULL 1,114,112-byte image based at 0x010000 is REFUSED",
        r13 is not None and r13.rid == "rescue",
        "0x010000-0x11FFFF swallows the rescue slot -- %s"
        % (r13.rid if r13 else "PERMITTED"))
    add("F13b", "the same image based at 0x030000 IS permitted",
        permitted(0x030000, 1114112), "0x030000-0x13FFFF, the lowest base "
                                      "above the rescue slot that fits")

    # ------------------------------------------- F14-F16  malformed input
    bad = []
    for at, n in ((0x010000, 0), (0x010000, -1), (-1, 0x1000)):
        try:
            check(at, n)
            bad.append("(0x%x,%d) was ANSWERED" % (at, n))
        except ValueError:
            pass
    add("F14", "a zero, negative or negative-offset range RAISES rather than "
        "being answered", not bad, "; ".join(bad) or "3 refused")
    try:
        check("0x10000", 0x1000)
        f15 = False
    except ValueError:
        f15 = True
    add("F15", "a string offset is refused, not compared", f15,
        "a str is never < an int in py3, so a silent False is the defect")
    add("F16", "refusal_text names the range and the region, on one line",
        (lambda t: t is not None and "\n" not in t and "REFUSED" in t
         and "0x020000" in t)(refusal_text(0x020000, 0x100)),
        (refusal_text(0x020000, 0x100) or "")[:60])

    # ------------------------------------------- F17  no flash verbs emitted
    # 🔴 The verbs are built from their letters rather than written, because
    # this case's own text is part of what the sweep in `test-mkfw2.sh` X1
    # reads: a case that says the words is a case that plants them.  That is
    # not paranoia, it is what X1 caught on its first run.
    verbs = ["".join(c) for c in (("F", "L", "W"), ("E", "W"), ("E", "B"),
                                  ("A", "U", "T", "O", "B", "U", "R", "N"))]
    src = open(os.path.abspath(__file__), "rb").read().decode("utf-8")
    printing = "".join(ln for ln in src.splitlines() if "print(" in ln)
    emitted = [v for v in verbs if v in printing]
    add("F17", "this file prints none of the four flash-write verbs",
        not emitted, "%d verbs checked, %d found" % (len(verbs),
                                                     len(emitted)))

    print("%s -- self-test" % VERSION)
    ok = fail = 0
    for cid, what, good_, detail in rows:
        if good_:
            ok += 1
            print("  ok     %-4s %-62s %s" % (cid, what, detail))
        else:
            fail += 1
            print("  FAIL   %-4s %-62s %s" % (cid, what, detail))
    print("  %d passed, %d failed" % (ok, fail))
    return 2 if fail else 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="flashguard.py", description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("check", help="is this destination range permitted")
    c.add_argument("--at", required=True, type=lambda s: int(s, 0),
                   help="flash offset, e.g. 0x030000")
    c.add_argument("--bytes", required=True, type=lambda s: int(s, 0),
                   help="length in bytes, e.g. 0x10000")
    c.set_defaults(func=cmd_check)

    t = sub.add_parser("table", help="the forbidden ranges AND the permitted "
                                     "neighbours")
    t.set_defaults(func=cmd_table)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        die("no subcommand.  `table` prints the ranges, `check` asks about one")
    return args.func(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        die("interrupted")
    except (ValueError, OSError) as exc:
        die("%s" % exc)
