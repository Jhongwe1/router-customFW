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

THE RULING OF 2026-10-04, AND WHY IT IS A GUARD AND NOT A DELETION
------------------------------------------------------------------
`R8b` has to write `rlxboot-rescue` at `0x020000`, which this file forbade
outright, so `mkfw2 build --flash-at 0x020000` was refused -- 量 on this
tree's parent commit, exit 3, no file written.  A containment rule that is
relaxed because the experiment needs it is not a containment rule, so the
blanket refusal is NOT removed.  What is added is a second, narrower gate:

* `check()` is the blanket verdict and it is **unchanged**.  It knows nothing
  about licences, it cannot be passed one, and `0x020000` is refused by it
  today exactly as it was before.  Every existing caller keeps its verdict.
* `check_licensed()` is the only way to a permit inside a licensable region,
  and `LICENSABLE` holds the one region id that word applies to: `rescue`.
  `loader`, `H601` and `off-chip` are in `UNRECOVERABLE`, which no licence,
  no flag and no argument can open -- `check_licensed()` does not even read
  the licence for a range that hits one of them.
* A licence is the owner's own dated row, in the ```owner-yes fence
  `cardcheck.py` already owns, naming the region, the exact destination range
  and the exact payload digest.  Presence and exactness are what this file
  enforces; provenance it cannot (`cardcheck.owner_yes`'s own note).

The containment property this buys, stated so it can be refuted: **a permit
from `check_licensed()` implies the range is disjoint from `0x000000`-`0x007FFF`
and ends at or before the chip's end**, because a licensable permit requires
`[at, at+nbytes)` to lie wholly inside the licensed region's own bounds and
the only licensable region is `0x020000`-`0x02FFFF`.  `L4` and `L6` are the
cases: `L4` builds a correct-looking licence for every corner of the loader
region and of `H601` and requires the blanket refusal to stand; `L6` sweeps the
chip under the most permissive licence this file can construct and requires the
permitted set to be exactly the complement of the three unrecoverable ranges.

What this cannot see, stated before it is used
----------------------------------------------
* It guards a **destination range**, which is an argument someone computed.  It
  does not read the loader's `burnAddr`, it cannot see a `J` into code that
  writes flash, and it cannot see a TFTP upload made while the burn word is
  armed (`cardcheck.py`'s `FW-113` note lists the same blind spots for the
  console side).  A permit from this file is not permission to write anything,
  and a licence is not a write either: it is a dated row saying the owner
  looked at one payload for one destination.
* It says nothing about whether a write is a good idea.  `0x060000` is
  PERMITTED here and holds the vendor kernel that gate `R9`'s vendor column
  needs; once that is overwritten it is gone.  `notes/update-chain.md`
  § "What a provisioning write destroys" is that argument, and it is a
  judgement for the owner, not a range check.
* Nothing in `R8a` or in this ruling writes flash.  This file emits no command,
  and `tools/test-mkfw2.sh` `X1`-`X3` assert that none of the four flash-write
  verbs appears in what these tools print.

Exit
    0  the range is PERMITTED
    1  the range is REFUSED -- one line saying which region and why
    2  a control failed (`--self-test`)
    3  usage / input refusal
"""

import argparse
import datetime
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cardcheck  # noqa: E402  -- the ```owner-yes fence has exactly one owner
import flashwin   # noqa: E402  -- and so does the H601 rule

VERSION = "flashguard 1.1"

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

# ------------------------------------------------------------- the ruling ---
# The one region id a licence may name.  It is a tuple and not a parameter: a
# licensable set that a caller can extend is not a containment rule.
LICENSABLE = ("rescue",)

# The ids that no licence, no flag and no argument opens.  Written down so a
# refusal can say which class it belongs to, and swept BOTH WAYS by `L11`:
# every forbidden id is in exactly one of the two lists.
UNRECOVERABLE = ("loader", DELEGATED_ID, "off-chip")

# The fence is `cardcheck.py`'s -- the SAME compiled object, not a copy of its
# pattern, so `F18` can assert the delegation by identity.  The row grammar
# below is this file's, because what a flash destination licence names is not
# what a console payload licence names.
OWNER_YES_RE = cardcheck.OWNER_YES_RE
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


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


def region_bounds(rid):
    """-> (lo, hi) for a forbidden region id, read out of the same table the
    decision uses.  A licence's reach is this region and nothing wider."""
    for lo, hi, r, _ in forbidden_ranges():
        if r == rid:
            return lo, hi
    raise ValueError("no forbidden region is called %r" % rid)


def _range_args(at, nbytes):
    """The input refusals, shared by every entry point: a guard asked about
    nothing cannot answer, and a string offset must never be compared."""
    if not isinstance(at, int) or not isinstance(nbytes, int):
        raise ValueError("a flash range is two integers, got %r and %r"
                         % (type(at).__name__, type(nbytes).__name__))
    if nbytes <= 0:
        raise ValueError("a destination length of %d is not a range; a guard "
                         "asked about nothing cannot answer" % nbytes)
    if at < 0:
        raise ValueError("negative flash offset 0x%x" % at)


def _off_chip(at, end):
    return Refusal(at, end, "off-chip",
                   "ends at 0x%06X, past the %d-byte chip.  burn() "
                   "TRUNCATES at capacity instead of refusing "
                   "(docs/loader-flash-write.md 1), so this is a "
                   "silently short write, not an error" % (end, CHIP_SIZE))


def check(at, nbytes):
    """-> a Refusal for [at, at+nbytes), or None if the range is PERMITTED.

    THE BLANKET VERDICT, and the 2026-10-04 ruling did not change one of its
    answers.  It takes no licence argument on purpose: a function that can be
    handed a permission is a function every later caller has to be audited
    for.  `check_licensed()` is the narrow gate and it calls this one first.

    Half-open on both sides, the same convention `flashwin.overlaps_forbidden`
    uses: a range ENDING at 0x006000 is clear, and a range whose last byte is
    0x006000 is not.  Both directions are cases `F4`-`F7`.
    """
    _range_args(at, nbytes)
    end = at + nbytes
    if end > CHIP_SIZE:
        return _off_chip(at, end)
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


def check_unrecoverable(at, nbytes):
    """-> a Refusal if [at, at+nbytes) touches a range nothing can license.

    The subset of `check()` that is about losing the device rather than about
    policy: the loader region, `H601`, and off the end of the chip.  It exists
    because the `RLXU` container format has to refuse a DECLARED destination
    inside those ranges -- that refusal is the format's, not the build
    policy's, and `src/rlxboot/container.c` makes it on the device with
    `RLXU_FLASH_KEEPOUT_END` and `RLXU_CHIP_SIZE`.  `test-mkfw2.sh` `G1`
    reads those two constants out of `container.h` and requires them to equal
    what this function enforces, so the C copy cannot drift silently.

    The rescue slot is NOT here: it is licensable, so the format permits a
    container that declares it and the build policy is what refuses one.
    """
    _range_args(at, nbytes)
    end = at + nbytes
    if end > CHIP_SIZE:
        return _off_chip(at, end)
    hit = flashwin.overlaps_forbidden(at, nbytes)
    if hit is not None:
        lo, hi, why = hit
        return Refusal(lo, hi, DELEGATED_ID, why)
    for lo, hi, rid, why in OWN_FORBIDDEN:
        if rid in UNRECOVERABLE and at < hi and end > lo:
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


# ----------------------------------------------------------- the licence ---
def licence_payload(at, nbytes, rid, digest_hex):
    """-> the exact row payload that licenses this one write, and nothing else.

    Four things, in one canonical spelling, because a licence that names three
    of them licenses a fourth nobody looked at:

        flash-at 0x020000+0x0010A0 rescue <the payload's sha256>

    the base, the LENGTH (so a bigger image cannot ride the same row), the
    region id (so a row written for the rescue slot can never be read as a
    row for anything else) and the sha256 of the payload bytes -- the number
    `mkfw2 build` prints as `payload sha256` and `sha256sum` prints for the
    file.  The container's own digest is not usable here: it does not exist
    until after the build this row has to authorise.
    """
    if not isinstance(digest_hex, str) or not _SHA256_RE.fullmatch(digest_hex):
        raise ValueError("a payload digest is 64 lower-case hex digits, got "
                         "%r" % (digest_hex,))
    return ("flash-at 0x%06X+0x%06X %s %s"
            % (at, nbytes, rid, digest_hex))


def parse_licence(text):
    """-> ({payload: date}, [defects]).  Exactness, not provenance.

    The fence and the `YYYY-MM-DD<TAB>payload` row are `cardcheck.py`'s, and
    the reasoning there applies here unchanged: EXACT, with no whitespace
    normalisation, because two strings that normalise equal need not mean the
    same write.  A defect permits nothing -- a caller that sees a non-empty
    defect list must refuse, and `check_licensed()` does.

    WHERE THIS DIVERGES FROM `cardcheck.owner_yes`, and why.  A card is a
    closed unit, so a row that permits nothing on it is stale and is a defect
    there.  A licence file is not closed: it may legitimately carry rows for
    builds other than this one.  So an unused row is REPORTED by the `licence`
    subcommand and is not a defect, and a malformed row anywhere in the file
    IS one -- a file with a row nobody can parse cannot be trusted to mean
    what the rest of it says.
    """
    rows, defects = {}, []
    for m in OWNER_YES_RE.finditer(text):
        for ln in m.group(1).split("\n"):
            ln = ln.rstrip("\r")
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            date, tab, payload = ln.partition("\t")
            ok = bool(tab and payload and _DATE_RE.fullmatch(date))
            if ok:
                try:
                    datetime.date.fromisoformat(date)
                except ValueError:
                    ok = False
            if not ok:
                defects.append("row %r: want YYYY-MM-DD<TAB><the exact "
                               "licence payload>, with a real date" % ln)
                continue
            if payload in rows:
                defects.append("row %r: a second yes for one payload"
                               % ln)
                continue
            rows[payload] = date
    return rows, defects


def licence_grant(at, nbytes, licence, digest_hex):
    """-> (date, payload) if a well-formed licence covers this exact write.

    None when there is no licence, when it has a defect, or when no row names
    this range, this region and this digest.  It never looks at a range that
    `check()` permits and never at one `check_unrecoverable()` refuses -- the
    caller is `check_licensed()` and it has already decided both.
    """
    if licence is None:
        return None
    rows, defects = parse_licence(licence)
    if defects:
        return None
    r = check(at, nbytes)
    if r is None or r.rid not in LICENSABLE:
        return None
    want = licence_payload(at, nbytes, r.rid, digest_hex)
    if want not in rows:
        return None
    return rows[want], want


def check_licensed(at, nbytes, licence=None, digest_hex=None):
    """-> a Refusal, or None if this range may be a flash destination.

    The narrow gate.  Four conjuncts, and all four are needed for a permit
    inside a licensable region:

      1  the region is in `LICENSABLE`.  A range touching `loader`, `H601` or
         the end of the chip returns `check()`'s refusal and THE LICENCE IS
         NOT READ AT ALL -- not parsed, not opened, not reported on.
      2  `[at, at+nbytes)` lies wholly inside that region's own bounds.  This
         is the conjunct that makes the containment claim provable rather
         than argued: a licensed permit cannot reach outside `0x020000`-
         `0x02FFFF`, whatever a row says.
      3  a licence is presented and every row in it parses.
      4  one row names this base, this length, this region and this payload
         digest, under a real date.

    A range `check()` already permits is permitted here too, unchanged: this
    function widens nothing outside a licensable region.
    """
    r = check(at, nbytes)
    if r is None:
        return None
    if r.rid not in LICENSABLE:
        return r                      # conjunct 1: the licence is not read
    lo, hi = region_bounds(r.rid)
    if not (lo <= at and at + nbytes <= hi):
        return Refusal(r.lo, r.hi, r.rid, r.why + ".  A licence reaches only "
                       "inside 0x%06X-0x%06X and this range leaves it"
                       % (lo, hi - 1))
    if digest_hex is None:
        return Refusal(r.lo, r.hi, r.rid, r.why + ".  No payload digest was "
                       "offered, so no row can name this write")
    want = licence_payload(at, nbytes, r.rid, digest_hex)
    if licence is None:
        return Refusal(r.lo, r.hi, r.rid, r.why + ".  Licensable: the owner's "
                       "own dated row in a ```owner-yes fence would open it, "
                       "and it must read exactly `<YYYY-MM-DD><TAB>%s`" % want)
    rows, defects = parse_licence(licence)
    if defects:
        return Refusal(r.lo, r.hi, r.rid, r.why + ".  The licence has %d "
                       "defect(s) and a defect permits nothing: %s"
                       % (len(defects), "; ".join(defects[:2])))
    if want not in rows:
        return Refusal(r.lo, r.hi, r.rid, r.why + ".  The licence has %d "
                       "row(s) and none of them is `%s`" % (len(rows), want))
    return None


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


def cmd_licence(args):
    """The narrow gate through the CLI, shown refusing AND permitting."""
    text = None
    if args.owner_yes:
        if not os.path.isfile(args.owner_yes):
            die("no such licence file: %s" % args.owner_yes)
        text = open(args.owner_yes, "rb").read().decode("utf-8", "replace")
    try:
        r = check_licensed(args.at, args.bytes, text, args.sha256)
    except ValueError as exc:
        die(str(exc))
    if r is not None:
        print("flashguard: REFUSED 0x%06X+0x%X (0x%06X-0x%06X) overlaps %s"
              % (args.at, args.bytes, args.at, args.at + args.bytes - 1, r),
              file=sys.stderr)
        return 1
    g = licence_grant(args.at, args.bytes, text, args.sha256)
    if g is None:
        print("flashguard: PERMITTED 0x%06X+0x%X -- not a licensable range, "
              "no licence was needed or read"
              % (args.at, args.bytes))
    else:
        date, row = g
        print("flashguard: PERMITTED 0x%06X+0x%X under the owner's yes of %s"
              % (args.at, args.bytes, date))
        print("  row        %s" % row)
        print("  licence    %s  sha256 %s"
              % (args.owner_yes,
                 hashlib.sha256(text.encode("utf-8")).hexdigest()))
        print("  NOT A WRITE.  This is a dated row saying the owner looked at "
              "one payload for one destination.")
    return 0


def cmd_table(args):
    """The refusal AND permission table.  A guard is shown permitting too."""
    print("%s -- forbidden ranges" % VERSION)
    print("  %-17s %-8s %s" % ("range", "id", "why"))
    for lo, hi, rid, why in forbidden_ranges():
        print("  0x%06X-0x%06X %-8s %s" % (lo, hi - 1, rid, why))
    print("  0x%06X-          off-chip past the %d-byte chip"
          % (CHIP_SIZE, CHIP_SIZE))
    print("")
    print("  the 2026-10-04 ruling -- which refusals a licence can open:")
    for lo, hi, rid, _ in forbidden_ranges():
        lic = "LICENSABLE  " if rid in LICENSABLE else "unrecoverable"
        print("  ruling   %s 0x%06X-0x%06X %s" % (lic, lo, hi - 1, rid))
    print("  ruling   unrecoverable 0x%06X-          off-chip" % CHIP_SIZE)
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

# The licence the controls below are run against.  `L2` uses it as written and
# `L3` mutates it one field at a time; both read THIS text, so a mutation that
# the parser accepts cannot hide in a second copy.
_LIC_DATE = "2026-10-04"
_LIC_DIGEST = "a" * 64


def _fence(rows):
    return ("prose above the fence, which is not a row\n\n```owner-yes\n"
            + "".join(r + "\n" for r in rows) + "```\nprose below it\n")


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

    # ------------------------------------- F18-F19  the fence's one owner
    # 🔴 F18 is F3's shape for the licence fence: the regex IS cardcheck's
    # object, so a copied pattern fails this by identity even when the two
    # patterns still happen to be equal.
    add("F18", "the ```owner-yes fence is cardcheck's own object, not a copy",
        OWNER_YES_RE is cardcheck.OWNER_YES_RE,
        "id match %s" % (OWNER_YES_RE is cardcheck.OWNER_YES_RE))
    # And the date grammars agree on a probe list that contains what each
    # could get wrong: a real date, a leap day, a non-date, a short year, a
    # month that does not exist (which the regex accepts and the calendar
    # rejects -- so parse_licence must run both).
    probes = ["2026-10-04", "2024-02-29", "2026-13-01", "2026-1-04",
              "20261004", "not-a-date", "2026-02-30", ""]
    mine = [bool(_DATE_RE.fullmatch(p)) for p in probes]
    theirs = [bool(cardcheck._YES_DATE_RE.fullmatch(p)) for p in probes]
    cal = []
    for p in probes:
        rows_, defects_ = parse_licence(_fence(["%s\tx" % p]))
        cal.append(not defects_)
    add("F19", "the date grammar matches cardcheck's on %d probes, and the "
        "calendar refuses the 2 the regex accepts" % len(probes),
        mine == theirs and cal == [True, True, False, False, False, False,
                                   False, False],
        "regex %s, after the calendar %s" % (sum(mine), sum(cal)))

    # ------------------------------------- L1-L2  BOTH ARMS OF THE RULING
    # The rescue slot, one container-sized range, with and without the row.
    at, n = 0x020000, 0x0010A0
    good_row = "%s\t%s" % (_LIC_DATE,
                           licence_payload(at, n, "rescue", _LIC_DIGEST))
    lic = _fence([good_row])
    r1 = check_licensed(at, n, None, _LIC_DIGEST)
    add("L1", "0x020000+0x10A0 with NO licence is REFUSED, and the refusal "
        "names the row that would open it",
        r1 is not None and r1.rid == "rescue" and "Licensable" in r1.why
        and licence_payload(at, n, "rescue", _LIC_DIGEST) in r1.why,
        "rescue, and the required row is quoted")
    r2 = check_licensed(at, n, lic, _LIC_DIGEST)
    add("L2", "the SAME range WITH the owner's dated row IS PERMITTED",
        r2 is None, "permitted under %s"
        % (licence_grant(at, n, lic, _LIC_DIGEST) or ("none",))[0])
    # and the blanket API is untouched by the licence that just permitted it
    add("L2b", "check() still REFUSES that range while that licence exists",
        check(at, n) is not None and check(at, n).rid == "rescue",
        "the blanket verdict takes no licence argument")

    # ------------------------------------- L3  one field at a time
    # 🔴 Each mutant changes exactly ONE component of the row that worked, so
    # a permit cannot be scored for the wrong reason.
    muts = [
        ("the base", "%s\t%s" % (_LIC_DATE,
                                 licence_payload(0x021000, n, "rescue",
                                                 _LIC_DIGEST))),
        ("the length", "%s\t%s" % (_LIC_DATE,
                                   licence_payload(at, n + 1, "rescue",
                                                   _LIC_DIGEST))),
        ("the region id", "%s\t%s"
         % (_LIC_DATE, licence_payload(at, n, "loader", _LIC_DIGEST))),
        ("the digest", "%s\t%s"
         % (_LIC_DATE, licence_payload(at, n, "rescue", "b" * 64))),
        ("the date", "2026-13-04\t%s"
         % licence_payload(at, n, "rescue", _LIC_DIGEST)),
        ("the tab", "%s %s" % (_LIC_DATE,
                               licence_payload(at, n, "rescue", _LIC_DIGEST))),
        ("the verb", "%s\t%s" % (_LIC_DATE,
                                 licence_payload(at, n, "rescue",
                                                 _LIC_DIGEST).replace(
                                     "flash-at", "flash_at"))),
    ]
    surv = [name for name, row in muts
            if check_licensed(at, n, _fence([row]), _LIC_DIGEST) is None]
    add("L3", "every one of %d single-field mutations of that row is REFUSED"
        % len(muts), not surv, "; ".join(surv) or "%d/%d refused"
        % (len(muts), len(muts)))
    # the row outside the fence permits nothing either
    add("L3b", "the same row OUTSIDE the ```owner-yes fence permits nothing",
        check_licensed(at, n, good_row + "\n", _LIC_DIGEST) is not None,
        "the fence is what makes a row a row")

    # ------------------------------------- L4  THE CONTAINMENT CASE
    # 🔴 A correct-looking licence is built for every corner of every
    # unrecoverable range, with the right digest and today's date, and the
    # blanket refusal must stand on all of them.  A licence for `loader` is
    # not merely ineffective: `check_licensed` never reads it, so a defect in
    # the parser cannot become a permit here.
    # The two unrecoverable REGIONS, every corner of each.  `off-chip` is not
    # probed here on purpose: it is not a region, so it has no bounds a licence
    # could name, and `L6`, `L10b` and `F12` are where it is refused.
    opened = []
    probed = 0
    for probe in (0x000000, 0x000001, 0x005FFF, 0x006000, 0x007FFF,
                  0x003000):
        for nb in (1, 0x20, 0x1000):
            if check_unrecoverable(probe, nb) is None:
                continue          # not a containment probe; L6 sweeps those
            probed += 1
            rid = check(probe, nb).rid
            row = "%s\t%s" % (_LIC_DATE,
                              licence_payload(probe, nb, rid, _LIC_DIGEST))
            v = check_licensed(probe, nb, _fence([row]), _LIC_DIGEST)
            if v is None:
                opened.append("0x%06X+0x%X as %s" % (probe, nb, rid))
            elif v.rid not in UNRECOVERABLE:
                opened.append("0x%06X+0x%X refused as %s, not an "
                              "unrecoverable id" % (probe, nb, v.rid))
    # 🔴 `probed >= 15` is here because a loop that skipped every probe would
    # report "nothing was opened" and be scored green.  A tool reporting 0 is
    # making a claim, and the claim needs the count beside it.
    add("L4", "a correct-looking licence for the loader region or for H601 "
        "opens NOTHING (%d probes)" % probed,
        not opened and probed >= 15,
        "; ".join(opened[:2]) or "%d/%d still refused, each by an "
                                 "unrecoverable id" % (probed, probed))

    # ------------------------------------- L5  the licence's reach
    strays = []
    for a2, n2 in ((0x01F800, 0x1000), (0x02F800, 0x1000),
                   (0x020000, 0x10001), (0x01FFFF, 0x10002)):
        rr = check(a2, n2)
        rid = rr.rid if rr is not None else "rescue"
        row = "%s\t%s" % (_LIC_DATE, licence_payload(a2, n2, rid,
                                                     _LIC_DIGEST))
        if check_licensed(a2, n2, _fence([row]), _LIC_DIGEST) is None:
            strays.append("0x%06X+0x%X" % (a2, n2))
    add("L5", "a row naming a range that LEAVES the licensed region opens "
        "nothing (4 probes)", not strays,
        "; ".join(strays) or "4/4 refused")

    # ------------------------------------- L6  the chip-wide sweep
    # 🔴 THE REFUTATION CONDITION, run as a loop.  Under the most permissive
    # licence this file can construct -- a correct row for every probe -- the
    # permitted set must be EXACTLY the complement of loader, H601 and
    # off-chip.  If one byte of the first two ever becomes permitted, or the
    # rescue window does not become permitted, this is what says so.
    step = 0x400
    probes = list(range(0, CHIP_SIZE, step))
    for b in (0x005FFF, 0x006000, 0x007FFF, 0x008000, 0x01FFFF, 0x020000,
              0x02FFFF, 0x030000, CHIP_SIZE - 1):
        probes += [b - 1, b, b + 1]
    want_bad = good_cnt = 0
    wrong = []
    for a2 in sorted(set(p for p in probes if 0 <= p < CHIP_SIZE)):
        row = "%s\t%s" % (_LIC_DATE,
                          licence_payload(a2, 1, "rescue", _LIC_DIGEST))
        v = check_licensed(a2, 1, _fence([row]), _LIC_DIGEST)
        unrec = check_unrecoverable(a2, 1) is not None
        if unrec:
            want_bad += 1
            if v is None:
                wrong.append("0x%06X PERMITTED" % a2)
        else:
            good_cnt += 1
            if v is not None:
                wrong.append("0x%06X refused (%s)" % (a2, v.rid))
    add("L6", "under the most permissive licence, the permitted set is "
        "EXACTLY the complement of the unrecoverable ranges", not wrong,
        "%d probes: %d unrecoverable and refused, %d permitted; %d wrong"
        % (want_bad + good_cnt, want_bad, good_cnt, len(wrong)))

    # ------------------------------------- L7  defects permit nothing
    both = _fence(["not a row at all", good_row])
    add("L7", "a fence holding ONE malformed row and the correct row permits "
        "nothing", check_licensed(at, n, both, _LIC_DIGEST) is not None,
        "a defect permits nothing (cardcheck's rule)")
    dup = _fence([good_row, good_row])
    add("L8", "the correct row written TWICE permits nothing",
        check_licensed(at, n, dup, _LIC_DIGEST) is not None,
        "one yes per payload")
    try:
        check_licensed(at, n, lic, "A" * 64)
        l9 = "ANSWERED"
    except ValueError:
        l9 = "raised"
    add("L9", "an upper-case or malformed digest RAISES rather than being "
        "compared", l9 == "raised", l9)

    # ------------------------------------- L10  check_unrecoverable's arms
    ur = []
    for probe, want in ((0x000000, True), (0x005FFF, True), (0x006000, True),
                        (0x007FFF, True), (0x008000, False),
                        (0x010000, False), (0x020000, False),
                        (0x02FFFF, False), (0x030000, False),
                        (CHIP_SIZE - 1, False)):
        got = check_unrecoverable(probe, 1) is not None
        if got != want:
            ur.append("0x%06X %s" % (probe, "permitted" if want else "refused"))
    add("L10", "check_unrecoverable refuses the loader and H601 and PERMITS "
        "the rescue slot and 5 others", not ur,
        "; ".join(ur) or "4 refused, 6 permitted")
    add("L10b", "and it refuses one byte past the chip",
        (lambda r_: r_ is not None and r_.rid == "off-chip")(
            check_unrecoverable(CHIP_SIZE - 1, 2)),
        "off-chip")

    # ------------------------------------- L11  the exemption list, both ways
    # 🔴 CLAUDE.md: sweep the exemption list both ways.  Every forbidden id is
    # in exactly one of LICENSABLE and UNRECOVERABLE, and every id named in
    # either list is a real forbidden region -- so a typo in a list cannot
    # silently make a region licensable or leave one classified twice.
    ids = sorted(set([rid for _, _, rid, _ in forbidden_ranges()])
                 | {"off-chip"})
    unclassified = [i for i in ids
                    if (i in LICENSABLE) == (i in UNRECOVERABLE)]
    phantom = [i for i in list(LICENSABLE) + list(UNRECOVERABLE)
               if i not in ids]
    add("L11", "every forbidden id is in exactly one of LICENSABLE and "
        "UNRECOVERABLE, and neither list names a region that does not exist",
        not unclassified and not phantom,
        "ids %s; unclassified %s; phantom %s"
        % (len(ids), unclassified or "-", phantom or "-"))

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

    t = sub.add_parser("table", help="the forbidden ranges, the ruling, and "
                                     "the permitted neighbours")
    t.set_defaults(func=cmd_table)

    g = sub.add_parser("licence", help="the narrow gate: is this destination "
                                       "permitted for THIS payload under a "
                                       "dated owner-yes")
    g.add_argument("--at", required=True, type=lambda s: int(s, 0))
    g.add_argument("--bytes", required=True, type=lambda s: int(s, 0))
    g.add_argument("--sha256", required=True,
                   help="the payload's sha256, 64 lower-case hex digits")
    g.add_argument("--owner-yes", help="a file carrying the owner's dated "
                                       "```owner-yes fence")
    g.set_defaults(func=cmd_licence)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        die("no subcommand.  `table` prints the ranges, `check` asks about "
            "one, `licence` asks the narrow gate")
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
