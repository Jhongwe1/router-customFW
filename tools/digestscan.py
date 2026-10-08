#!/usr/bin/env python3
"""digestscan -- does a file carry a DIGEST of a flash window that may not be
published?

WHY THIS EXISTS
---------------
`PROGRESS.md` § Carried forward, `FLW-1`.  Three scanners already guard
`H601` -- flash `0x006000`-`0x007FFF`, this unit's MAC and radio calibration --
and each of them answers a different question:

  * `flashwin scan` finds the region's BYTES in a file, raw or as hex text;
  * `leakscan` finds the text SHAPES an address takes;
  * `audit-bench-log` finds topic keywords.

None of them can see a digest, and none of them is wrong not to: a sha256 holds
no byte of its preimage.  量 2026-09-07 (`notes/flash-digest-scope.md` § 2):
`flashwin scan --sweep . --exclude upstream` read 2,497 files and reported
CLEAN with `LOG.md` and `tools/leakscan.py` in the swept set -- each of them
carrying the full 64-hex sha256 of the whole 4 MiB image, `H601` inside it.

A digest of a window whose only unknown is the MAC IS the MAC.  `flashwin`'s
own refusal states it: with the rest of the window known, 24 unknown bits are a
2^24 search.  🔴 **And an abbreviation is not a mitigation.**  A k-bit prefix
leaves 2^24 * 2^-k false candidates: `FLS-14`'s 60 bits leave 2^-36, a 32-bit
prefix leaves 2^-8 = 0.004 -- the MAC, uniquely.  So a scanner for this has to
find prefixes and suffixes as short as the threat allows, not only whole
digests.

WHAT IT DOES
------------
1. CANDIDATES, computed in memory from the reference dump and never written or
   printed: every DIGEST KIND below over every window that
   `flashwin.overlaps_forbidden` says overlaps a forbidden region.  The
   forbidden table is IMPORTED from `tools/flashwin.py` -- one owner, and
   `CLAUDE.md` § Flash says new tools import it rather than restate it.  The
   windows (`inventory` prints them, labels and counts only):

     * every forbidden region whole (`H601@0x006000+0x2000`);
     * every ALIGNED power-of-two window from 256 B (`page@`, the `FLR` unit) to
       4 MiB (`whole@0x000000+0x400000`) -- 4 KiB sectors and 64 KiB blocks
       among them -- enumerated over the whole flash and kept only where
       `overlaps_forbidden` says so, so that call is load-bearing;
     * the windows this repository has USED (`USED`, `USED_FLR`, each with
       where it was used): the `FLR` windows, `mtd0`, the 64 KiB re-reads, the
       first 4 KiB of `H601` that `upstream/BENCH-LOG.md` baselines;
     * the MAC: its two copies (`FLS-22`: `0x006007` and `0x006013`, 6 bytes
       each), `nic1Addr` between them (the driver's struct note), the two
       16-byte `DW` lines that hold them, and the MAC as TEXT in six spellings
       with and without a trailing newline (`echo $mac | sha256sum`);
     * the `H6` hardware-settings block and its checksummed body, with the
       length read from the block's own header (`rtl819x-spi.c`, `h601` verb);
     * the loader's `DW` reply for every `FLR` window/RAM pair in `USED_FLR`,
       rendered by `flashwin.render_dw` -- the text `flashwin render` would
       hash -- and its `flashwin.normalise_dw` form.

   A window whose bytes INSIDE the forbidden region are one repeated value is
   dropped and counted: a digest of 4,096 zero bytes says nothing about this
   unit, and it is a digest other files may legitimately print.  The filter is
   on the candidate side, as `flashwin scan`'s entropy filter is, so it does not
   decide what to report after seeing a match.

   `--also IMAGE@OFFSET` adds the same windows over another image of flash
   (the 64 KiB re-reads under `$FWRE_WORK/dumps/`), so a digest of `H601` in a
   state other than the reference dump's is a candidate too -- `FLS-21`
   measured nine of its bytes changed and restored on this unit.

2. THE CHANNEL.  Every maximal run of two or more hex digits (a `0x`/`0X`
   prefix is dropped) is a token.  Tokens join into a CHAIN when they are the
   same class -- two digits (a byte list) or eight or more (a word or a
   literal) -- and what lies between them is only separators: whitespace,
   quotes, `,`, `:`, `+`, `\\`.  That one rule covers the three shapes this
   repository has actually used: a contiguous digest, a digest split across
   two string literals on two lines (`tools/leakscan.py:137`), and a C byte
   array (`rtl819x-spi.c`'s known-answer vectors and its `FLS-24` constant).
   An eight-digit token followed directly by `:` is a `DW` address column:
   dropped from the stream, as `flashwin.hex_stream` drops it, so the words
   either side of it join and a digest dumped across two `DW` lines is found
   whole -- and still looked up on its own, so an eight-digit abbreviation
   that happens to precede a colon is not lost.  `…` and `...` are NOT
   separators: they mark an elision, and each side is checked on its own.
   Case is ignored.

3. THE MATCH.  At every token START in a chain, the hex from there on is
   compared with every candidate's PREFIX; at every token END, the hex up to
   there with every candidate's SUFFIX.  A hit needs at least `N` matching
   digits and reports how many matched.  Never what.

4. THE VERDICT carries a path, a line, the window label, the digest kind and a
   count of digits.  🔴 No matched text, no candidate, no slice of either, in
   any output -- `F4` drives the command line and searches its output for every
   candidate.  Exit 0 clean (exempt hits allowed), 1 findings, 2 refusal.

DIGEST KINDS, and which this repository has printed over flash
---------------------------------------------------------------
  sha256  over each window's bytes and over the `DW` renderings: the kind
          this repository prints -- `FLS-14`, the driver's `d1_sha256` and
          `map`, `flashwin render`, `upstream/BENCH-LOG.md`'s baselines.
  md5     the same preimages: `upstream/BENCH-LOG.md` pipes a flash region
          through `md5sum` (`dd if=/dev/mtdblock0 ... | md5sum`).
  sha1    the same preimages: printed for no flash content of this unit that
          this repository holds (only for the vendor's published images), and
          covered because a kind costs one lookup per window.
  crc32   zlib's, eight digits, over each window's bytes only: printed for no
          flash content found here, covered for the same reason; at N = 8 only
          a WHOLE crc32 can match.
NOT covered: the loader's 16-bit image sum and the vendor's 8-bit `H6`
checksum (shorter than N -- see the last section), `cksum`'s CRC (decimal),
and the rest of `hashlib`, for which no use was found and each of which would
add to C below.

N, AND WHY IT IS 8
------------------
The threat sets the ceiling.  A k-digit prefix of a digest over a window
whose only unknown is the MAC leaves 2^24 * 16^-k false candidates standing:
0.004 at k = 8, 1.5e-5 at k = 10.  Every k >= 8 names the MAC, so an N above
8 lets a 32-bit abbreviation through -- and that is the form `RUNSHEET.md:13`,
`:401` and `notes/leak-surface.md:79` carry (`notes/flash-digest-scope.md`
§ 2).

The corpus sets the floor.  量 2026-10-09, `measure` over the tracked tree at
28a490c7 -- 17,671 files -- against the C = 166 candidates of the reference
dump, counting the lookups the matcher actually makes (token boundaries):

     N   lookups, prefix + suffix   distinct   expected false hits   P(any)
     8          872,802             188,513         0.034            0.0073
    10          279,041              54,857         4.2e-05          8.3e-06
    12          155,584              23,860         9.2e-08          1.4e-08
    16          123,508              25,766         1.1e-12          2.3e-13

With the ten 64 KiB re-reads given as `--also`, C = 245 and the N = 8 row
is 0.050 expected, P(any) 0.011 -- measured, not scaled.  So N = 8 costs
about one false hit in twenty scans of this tree, and N = 10 would buy that
back by missing every 32-bit form the repository is known to hold.  A false
hit names a line a person reads; a missed 32-bit prefix is the MAC.  ⚠️ It
is an expectation, not a bound: it assumes the candidates' digits are
uniform, which a digest's are.  And the first real scan argues against chance
on its own terms -- all seventeen of its hits (fifteen findings, two exempt)
are ONE candidate of the 166.

EXEMPTIONS, BY NAME
-------------------
An exemption names a file, a line, a window label, a digest kind and the
number of digits it covers, with the ruling that allows it.  Never a date,
never a pattern.  ONE ROW EXEMPTS ONE HIT: two hits of the same name -- the
same digits of the same digest twice on one line -- need two rows, and a
third copy is a finding.  Swept both ways: a hit no exemption names is a
finding, and so is an exemption that names no hit (`STALE`) -- which is what
makes it go red when the line moves or the digest is removed.  `check` holds
a dump-free proxy of the same join for CI (`K2`): each row's line still
starts a hex chain of the row's length.  A proxy: other hex of that length on
the line satisfies it too, so only the scan at the desk sees every removal.

What `EXEMPT` holds, and why.  Seventeen rows, and every one of them is the
same candidate: the sha256 of the whole 4 MiB image, `whole@0x000000+0x400000`.
  * Two rows under the owner's 2026-09-07 ruling: that digest in full, at
    `LOG.md:87` and split across two literals at `tools/leakscan.py:137`.  It
    is printable because `FLS-22` made the MAC public, not because 4 MiB is
    wide.
  * Fifteen rows under the main session's 2026-10-08 ruling (`LOG.md`, 130th
    segment, `FLW-1`; the owner may override it): every PREFIX of that same
    digest in the tracked tree, 量 at `1b13303d` -- eight or sixteen digits,
    fifteen hits on fourteen lines of eight files, `SPEC.md`'s `FLS-14` line
    holding two and so two rows.  A prefix of a digest already published in
    full discloses nothing more.
No other candidate is exempt: a digest of any other window, whole or as a
prefix, is a finding.  The key does not say prefix or suffix, so a row would
also take a suffix of the same length of the same digest that replaced its
prefix on the same line -- for this digest, published in full, that discloses
nothing more either.  `upstream/` is neither exempted nor read by default: its
46 hits at the pin (量 2026-10-09) are the owner's (`FLS-22`: as is).

WHAT IT CANNOT SEE, stated before it is used
--------------------------------------------
  * a digest SHORTER than `N` digits: the loader's 16-bit sum, the vendor's
    8-bit `H6` checksum (which is itself one of `H601`'s bytes), a 7-digit
    suffix such as `FLS-14`'s.  Each of those leaks bits; none can be told from
    ordinary hex at a usable false-match rate.
  * a fragment taken from the MIDDLE of a digest, or one glued to other hex on
    both sides.
  * any encoding but hex: base64 (`sha256-...`), decimal (`cksum`), a digest
    in an image or a PDF.
  * any digest kind but the four below, and any preimage but the windows
    above: a window at an unlisted offset or length, a byte-swapped image, a
    compressed one, a hexdump of a window, a capture file with framing other
    than `flashwin.render_dw`'s.
  * any state of `H601` that no image given to it holds.
  * a digest of a candidate (a hash of a hash).
  * a digest in digit groups other than pairs or runs of eight or more --
    `xxd -g2`'s four, say.  Those tokens are never looked up.
  * UTF-16 text: the channel reads bytes one per character.  量 2026-10-09:
    no tracked file and no `upstream/` file carries a UTF-16 byte-order mark;
    the two whose bytes alternate with NUL are binary fuzz seeds.
  * a submodule: in the default mode `upstream/` is one gitlink and is NOT
    read.  `--sweep upstream` reads it, and the default mode says how many
    gitlinks it skipped.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import os
import random
import re
import subprocess
import sys
import tempfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashwin  # noqa: E402  -- one owner for FORBIDDEN and overlaps_forbidden

TOOL_VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: 讀 `FLS-01`: 4 MiB.  A dump of any other size is refused, not scanned.
FLASH_SIZE = 0x400000

DUMP_REL = os.path.join("dumps", "flash-n150rt-console-2.bin")

#: The dump's identity, and why it is not a digest of the dump: `FLS-24`'s
#: sha256 over `H601`'s COMPLEMENT -- [0x000000,0x006000) and
#: [0x008000,0x400000), 4,186,112 bytes -- whose preimage holds no byte of
#: `H601` and which `flashwin` therefore prints.  It is read from the one place
#: it is written in full, the driver's compiled-in constant ("re-derived
#: 2026-09-07 ... by two independent routes"), so the dump and that constant
#: are two sources that must agree.  A wrong dump would make every candidate
#: wrong and every scan CLEAN; this is the refusal that prevents that.
IDENTITY_SRC = os.path.join("config", "rlxfw-src", "linux-2.6.30", "drivers",
                            "mtd", "devices", "rtl819x-spi.c")
IDENTITY_SYM = "rtl819x_spi_expect_d1"

#: N -- see the docstring.  Below 8 is refused: the chain rule above treats
#: tokens of three to seven digits as unjoinable, which is only sound when no
#: match can be that short.
MIN_HEX = 8
N_FLOOR = 8

#: One variable, used three times: printed by the skip line, by the summary,
#: and checked by `Q1` against `tools/ci-expected.tsv` -- the shape
#: `flashwin.SKIP_LABEL` and `leakscan.DUMP_SKIP_LABEL` both carry, for the
#: reason both record (a bench WITH the dump never prints the skip, so never
#: compares it).
SKIP_LABEL = "R-block this unit's flash dump"

#: A window whose bytes inside the forbidden region hold fewer distinct values
#: than this is not a candidate (see the docstring).
MIN_DISTINCT_FORBIDDEN = 2

#: Aligned window sizes, 256 B .. 4 MiB.
ALIGNED_SIZES = [1 << k for k in range(8, 23)]

#: Windows this repository has USED that overlap a forbidden region, and where.
#: 量 2026-10-09 at 28a490c7, by reading the record.  Each also falls out of
#: the aligned enumeration except `mtd0`; they are listed so the inventory says
#: which windows are KNOWN to have been read, and so a future change to the
#: aligned set cannot drop one silently.
USED = [
    (0x000000, FLASH_SIZE, "FLS-14 the whole dump"),
    (0x000000, 0x130000, "mtd0 `boot+cfg+linux` (notes/kernel-build.md § 18, "
                         "notes/update-chain.md)"),
    (0x000000, 0x10000, "the 64 KiB `config-region-*` re-reads (FLS-25)"),
    (0x000000, 0x8000, "the loader region and H601, the two never-write regions"),
    (0x006000, 0x2000, "H601 whole, the driver's `h601` verb"),
    (0x006000, 0x1000, "H601's first 4 KiB, upstream/BENCH-LOG.md's seven "
                       "baselines (notes/flash-digest-scope.md § 7)"),
    (0x006000, 0x100, "the FLR H601 window (FLS-20)"),
    (0x006400, 0x100, "the FLR canary page (FLS-21)"),
]

#: Every `FLR <dst> <src> <bytes>` in the tracked tree whose source window
#: overlaps a forbidden region.  量 2026-10-09 at 28a490c7; `check` `K1`
#: re-derives the set from the tree and refuses a drift in either direction.
USED_FLR = [
    (0x80A00200, 0x006000, 0x100),
    (0x80A00600, 0x006000, 0x100),
    (0x80A00A00, 0x006000, 0x100),
    (0x80A00E00, 0x006000, 0x100),
    (0x80A00300, 0x006400, 0x100),
    (0x80A00700, 0x006400, 0x100),
    (0x80A00B00, 0x006400, 0x100),
    (0x80A00F00, 0x006400, 0x100),
]

#: `FLS-22`: the MAC's two copies, six bytes each, read off the committed
#: record and not guessed.  `NIC1_AT` is `nic1Addr`, which the driver's struct
#: note (`rtl819x-spi.c`, `RTL819X_SPI_H601_NIC0`: boardVer(1) then
#: nic0Addr[6] then nic1Addr[6]) puts between them.
MAC_AT = (0x006007, 0x006013)
NIC1_AT = 0x00600D
#: `rtl819x-spi.c` `RTL819X_SPI_H601_HDR`: 'H' '6', two version digits, a
#: big-endian length.  `H6_LEN_MIN` is that file's `RTL819X_SPI_H601_LEN_MIN`.
H6_AT, H6_HDR, H6_LEN_MIN = 0x006000, 6, 14

RAW_KINDS = (
    ("sha256", lambda b: hashlib.sha256(b).hexdigest()),
    ("sha1", lambda b: hashlib.sha1(b).hexdigest()),
    ("md5", lambda b: hashlib.md5(b).hexdigest()),
    ("crc32", lambda b: "%08x" % (zlib.crc32(b) & 0xFFFFFFFF)),
)
TEXT_KINDS = RAW_KINDS[:3]

#: Exemptions, BY NAME: (path, line, window label, kind, digits, reason).
#: 🔴 Only the hits a ruling names, one row per hit, and every one the whole
#: image's sha256 (EXEMPTIONS in the docstring): in full under the owner's
#: 2026-09-07 ruling, and as a prefix under the main session's 2026-10-08
#: ruling, which the owner may override.  Every other hit is a finding until
#: a ruling names it here.
PREFIX_RULING = ("RULING 2026-10-08 (LOG.md, 130th segment, FLW-1): a prefix "
                 "of the whole-dump sha256 the 2026-09-07 ruling published in "
                 "full; a prefix discloses nothing more")
EXEMPT = [
    ("LOG.md", 87, "whole@0x000000+0x400000", "sha256", 64,
     "RULING 2026-09-07 (LOG.md, fortieth segment, § 八; SPEC.md FLS-14, "
     "FLS-24): the rule stands and its scope is written down -- the whole-"
     "image digest is printable because FLS-22 made the MAC public, not "
     "because 4 MiB is wide"),
    ("tools/leakscan.py", 137, "whole@0x000000+0x400000", "sha256", 64,
     "RULING 2026-09-07, the same ruling and the same digest, split across "
     "two literals (leakscan's DUMP_SHA256, its dump-identity check)"),
    # The fifteen prefixes, 量 at 1b13303d: fourteen lines, eight files.
    ("LOG.md", 18384, "whole@0x000000+0x400000", "sha256", 8, PREFIX_RULING),
    ("LOG.md", 18391, "whole@0x000000+0x400000", "sha256", 8, PREFIX_RULING),
    ("LOG.md", 18392, "whole@0x000000+0x400000", "sha256", 8, PREFIX_RULING),
    ("LOG.md", 18393, "whole@0x000000+0x400000", "sha256", 16, PREFIX_RULING),
    ("RUNSHEET.md", 13, "whole@0x000000+0x400000", "sha256", 8,
     PREFIX_RULING),
    ("RUNSHEET.md", 401, "whole@0x000000+0x400000", "sha256", 8,
     PREFIX_RULING),
    # FLS-14's line holds the prefix twice: two hits of one name, two rows.
    ("SPEC.md", 189, "whole@0x000000+0x400000", "sha256", 8, PREFIX_RULING),
    ("SPEC.md", 189, "whole@0x000000+0x400000", "sha256", 8, PREFIX_RULING),
    ("bench/2026-08-24c/PREDICTIONS-block5.md", 39,
     "whole@0x000000+0x400000", "sha256", 16, PREFIX_RULING),
    ("dt/rtl8196e-totolink-n150rt.dts", 111, "whole@0x000000+0x400000",
     "sha256", 8, PREFIX_RULING),
    ("notes/flash-digest-scope.md", 46, "whole@0x000000+0x400000", "sha256",
     8, PREFIX_RULING),
    ("notes/flash-digest-scope.md", 47, "whole@0x000000+0x400000", "sha256",
     8, PREFIX_RULING),
    ("notes/flash-digest-scope.md", 48, "whole@0x000000+0x400000", "sha256",
     16, PREFIX_RULING),
    ("notes/leak-surface.md", 79, "whole@0x000000+0x400000", "sha256", 8,
     PREFIX_RULING),
    ("tools/citecheck-baseline.tsv", 42, "whole@0x000000+0x400000", "sha256",
     8, PREFIX_RULING),
]


def _fail(msg: str) -> "NoReturn":  # noqa: F821
    """A refusal: a reason on stderr, rc 2, never a traceback."""
    print(f"digestscan: {msg}", file=sys.stderr)
    raise SystemExit(2)


# --------------------------------------------------------------------------
# candidates
# --------------------------------------------------------------------------

def size_name(n: int) -> str:
    names = {0x100: "page", 0x1000: "sector", 0x10000: "block64k",
             FLASH_SIZE: "whole"}
    if n in names:
        return names[n]
    if n >= 0x100000 and n % 0x100000 == 0:
        return "%dMiB" % (n >> 20)
    if n >= 0x400 and n % 0x400 == 0:
        return "%dKiB" % (n >> 10)
    return "%dB" % n


def wlabel(name: str, at: int, n: int) -> str:
    return "%s@0x%06X+0x%X" % (name, at, n)


def region_name(why: str) -> str:
    return why.split()[0]


def forbidden_distinct(image: bytes, base: int, at: int, n: int) -> int:
    """Distinct byte values of [at, at+n) INSIDE the forbidden regions."""
    vals = set()
    for lo, hi, _why in flashwin.FORBIDDEN:
        a, b = max(at, lo, base), min(at + n, hi, base + len(image))
        if a < b:
            vals.update(image[a - base:b - base])
    return len(vals)


def h6_windows(image: bytes, base: int):
    """The `H6` block and its body, length from the block's own header."""
    a = H6_AT - base
    if a < 0 or a + H6_HDR > len(image) or image[a:a + 2] != b"H6":
        return []
    ln = int.from_bytes(image[a + 4:a + 6], "big")
    if ln < H6_LEN_MIN or H6_AT + H6_HDR + ln > base + len(image):
        return []
    return [("hwset-block", H6_AT, H6_HDR + ln),
            ("hwset-body", H6_AT + H6_HDR, ln)]


def enumerate_windows(image: bytes, base: int):
    """-> [(primary label, [aliases], at, n)] over [base, base+len(image)),
    each overlapping a forbidden region, deduplicated by (at, n)."""
    lo, hi = base, base + len(image)
    order, labels = [], {}

    def add(name, at, n):
        if n <= 0 or at < lo or at + n > hi:
            return
        k = (at, n)
        if k not in labels:
            labels[k] = []
            order.append(k)
        lab = wlabel(name, at, n)
        if lab not in labels[k]:
            labels[k].append(lab)

    for flo, fhi, why in flashwin.FORBIDDEN:
        add(region_name(why), flo, fhi - flo)
    for n in ALIGNED_SIZES:
        for at in range(lo - lo % n, hi, n):
            add(size_name(n), at, n)
    for at, n, _why in USED:
        add("used", at, n)
    for at in MAC_AT:
        add("mac", at, 6)
        add("line16", at - at % 16, 16)
    add("nic1", NIC1_AT, 6)
    for name, at, n in h6_windows(image, base):
        add(name, at, n)

    out = []
    for at, n in order:
        if flashwin.overlaps_forbidden(at, n) is not None:
            labs = labels[(at, n)]
            out.append((labs[0], labs[1:], at, n))
    return out


def mac_texts(mac: bytes):
    h = mac.hex()
    pairs = [h[i:i + 2] for i in range(0, 12, 2)]
    forms = [("colon", ":".join(pairs)), ("dash", "-".join(pairs)),
             ("bare", h)]
    out = []
    for name, s in forms:
        out.append((name, s))
        out.append((name.upper(), s.upper()))
    return out


class CandidateSet:
    """Digests that may not appear.  One entry per distinct (kind, value),
    carrying every window label that produces it.  Never printed."""

    def __init__(self, n: int):
        self.n = n
        self.entries = []          # [(hex, kind, [labels])]
        self._key = {}
        self.pre, self.suf = {}, {}
        self.windows = 0
        self.dropped_constant = 0
        self.images = 0
        self.unmatchable = 0

    def add(self, kind: str, hexd: str, label: str):
        k = (kind, hexd)
        i = self._key.get(k)
        if i is None:
            i = len(self.entries)
            self._key[k] = i
            self.entries.append((hexd, kind, [label]))
            if len(hexd) >= self.n:
                self.pre.setdefault(hexd[:self.n], []).append(i)
                self.suf.setdefault(hexd[-self.n:], []).append(i)
            else:
                self.unmatchable += 1
        elif label not in self.entries[i][2]:
            self.entries[i][2].append(label)

    def add_image(self, image: bytes, base: int, tag: str = ""):
        if base < 0 or base + len(image) > FLASH_SIZE:
            _fail(f"an image of {len(image)} bytes at 0x{base:06X} does not "
                  f"fit a {FLASH_SIZE}-byte flash")
        self.images += 1
        for primary, aliases, at, n in enumerate_windows(image, base):
            if (forbidden_distinct(image, base, at, n)
                    < MIN_DISTINCT_FORBIDDEN):
                self.dropped_constant += 1
                continue
            self.windows += 1
            data = image[at - base:at - base + n]
            for kind, fn in RAW_KINDS:
                d = fn(data)
                for lab in [primary] + aliases:
                    self.add(kind, d, tag + lab)
        hi = base + len(image)
        for ram, src, nb in USED_FLR:
            if src < base or src + nb > hi:
                continue
            if flashwin.overlaps_forbidden(src, nb) is None:
                continue
            if (forbidden_distinct(image, base, src, nb)
                    < MIN_DISTINCT_FORBIDDEN):
                self.dropped_constant += 1
                continue
            self.windows += 1
            data = image[src - base:src - base + nb]
            text = flashwin.render_dw(ram, data, "DW %08X %d" % (ram, nb // 4))
            lab = tag + "dw:%s@ram0x%08X" % (wlabel("FLR", src, nb), ram)
            for kind, fn in TEXT_KINDS:
                self.add(kind, fn(text), lab)
            norm = flashwin.normalise_dw(text)
            for kind, fn in TEXT_KINDS:
                self.add(kind, fn(norm), tag + "dwnorm:" + wlabel("FLR", src, nb))
        for at in MAC_AT:
            if at < base or at + 6 > hi:
                continue
            mac = image[at - base:at - base + 6]
            if len(set(mac)) < MIN_DISTINCT_FORBIDDEN:
                self.dropped_constant += 1
                continue
            for name, s in mac_texts(mac):
                for nl in ("", "\n"):
                    lab = tag + "mactext:%s%s@0x%06X" % (
                        name, "+LF" if nl else "", at)
                    for kind, fn in TEXT_KINDS:
                        self.add(kind, fn((s + nl).encode("ascii")), lab)

    def kinds(self):
        out = {}
        for _h, kind, _l in self.entries:
            out[kind] = out.get(kind, 0) + 1
        return out


# --------------------------------------------------------------------------
# the dump, and its identity
# --------------------------------------------------------------------------

def default_dump() -> str:
    return os.path.join(os.environ.get("FWRE_WORK", "/home/key/fwre-work"),
                        DUMP_REL)


def identity_expected(src_path: str) -> str:
    """The `FLS-24` complement digest, read from the driver's C initialiser."""
    try:
        with open(src_path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except OSError as e:
        _fail(f"cannot read the identity source {src_path}: {e.strerror}")
    m = re.search(re.escape(IDENTITY_SYM) + r"\s*\[\s*32\s*\]\s*=\s*\{([^}]*)\}",
                  src)
    if not m:
        _fail(f"{src_path} holds no `{IDENTITY_SYM}[32] = {{...}}` -- the "
              f"dump's identity cannot be checked, and an unchecked dump makes "
              f"every scan CLEAN")
    vals = re.findall(r"0[xX]([0-9A-Fa-f]{2})\b", m.group(1))
    if len(vals) != 32:
        _fail(f"`{IDENTITY_SYM}` in {src_path} holds {len(vals)} byte(s), not 32")
    return "".join(vals).lower()


def complement_digest(dump: bytes) -> str:
    h = hashlib.sha256()
    pos = 0
    for lo, hi, _why in sorted(flashwin.FORBIDDEN):
        h.update(dump[pos:lo])
        pos = hi
    h.update(dump[pos:])
    return h.hexdigest()


def load_dump(path: str, identity_src: str) -> bytes:
    """Refuses -- rc 2, a reason, no traceback -- a missing, unreadable,
    wrongly sized or wrong dump."""
    if not os.path.exists(path):
        _fail(f"no dump at {path} -- the candidates are computed from this "
              f"unit's flash, and without it there is nothing to look for "
              f"(--dump PATH)")
    try:
        with open(path, "rb") as f:
            dump = f.read(FLASH_SIZE + 1)
    except OSError as e:
        _fail(f"cannot read the dump {path}: {e.strerror}")
    if len(dump) != FLASH_SIZE:
        _fail(f"{path} holds {len(dump)} byte(s), not {FLASH_SIZE} -- not a "
              f"whole-flash dump of this part (FLS-01)")
    want = identity_expected(identity_src)
    if complement_digest(dump) != want:
        _fail(f"{path} is not the reference dump: its sha256 over H601's "
              f"complement does not equal `{IDENTITY_SYM}` in "
              f"{os.path.relpath(identity_src, ROOT) if identity_src.startswith(ROOT) else identity_src} "
              f"(FLS-24) -- a wrong dump makes every candidate wrong and every "
              f"scan CLEAN")
    return dump


def parse_also(spec: str):
    path, _, off = spec.rpartition("@")
    if not path:
        path, off = spec, "0"
    try:
        base = int(off, 0)
    except ValueError:
        _fail(f"--also {spec}: the offset {off!r} is not a number")
    try:
        with open(path, "rb") as f:
            img = f.read(FLASH_SIZE + 1)
    except OSError as e:
        _fail(f"--also {spec}: {e.strerror}")
    return path, img, base


def build_candidates(dump: bytes, also=(), n: int = MIN_HEX) -> CandidateSet:
    cs = CandidateSet(n)
    cs.add_image(dump, 0)
    for path, img, base in also:
        cs.add_image(img, base, tag="also:%s:" % os.path.basename(path))
    return cs


# --------------------------------------------------------------------------
# the channel and the match
# --------------------------------------------------------------------------

TOKEN = re.compile(r"0[xX]([0-9A-Fa-f]{2,})|([0-9A-Fa-f]{2,})")
GAP = re.compile(r"[ \t\r\n\"',:+\\]*")


def chains(text: str):
    """Yield (hex, toks): a chain's lowercase hex and, per token,
    (start in hex, end in hex, offset in text)."""
    parts, toks, pos = [], [], 0
    pcls, pend = 0, -1
    for m in TOKEN.finditer(text):
        g = 1 if m.group(1) is not None else 2
        h = m.group(g)
        ln = len(h)
        cls = 2 if ln == 2 else (8 if ln >= 8 else 0)
        if cls == 0:
            if parts:
                yield "".join(parts).lower(), toks
                parts, toks, pos = [], [], 0
            pcls = 0
            continue
        end = m.end()
        if ln == 8 and text.startswith(":", end):
            # A `DW` address column (`%08X:`).  Dropped from the stream, as
            # `flashwin.hex_stream` drops it, so the words on either side of
            # it join when only separators surround it -- a digest held in
            # RAM and dumped by `DW` spans two lines and is found whole
            # (`M10b`).  It is still looked up on its own, so an eight-digit
            # abbreviation that happens to be followed by `:` is not lost.
            yield h.lower(), [(0, ln, m.start(g))]
            if parts and not (pcls == 8
                              and GAP.fullmatch(text, pend, m.start())):
                yield "".join(parts).lower(), toks
                parts, toks, pos = [], [], 0
            pcls, pend = 8, end + 1
            continue
        if parts and not (cls == pcls
                          and GAP.fullmatch(text, pend, m.start())):
            yield "".join(parts).lower(), toks
            parts, toks, pos = [], [], 0
        parts.append(h)
        toks.append((pos, pos + ln, m.start(g)))
        pos += ln
        pcls, pend = cls, end
    if parts:
        yield "".join(parts).lower(), toks


def _lcp(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def match_text(text: str, cs: CandidateSet):
    """-> [(start, end, entry, form, digits)], offsets into `text`.  The
    match itself is never part of the result."""
    n = cs.n
    out = []
    for s, toks in chains(text):
        if len(s) < n:
            continue
        found = {}
        for a, b, _off in toks:
            if len(s) - a >= n:
                for ci in cs.pre.get(s[a:a + n], ()):
                    d = cs.entries[ci][0]
                    k = _lcp(s[a:a + len(d)], d)
                    key = (a, a + k, ci)
                    if key not in found:
                        found[key] = "full" if k == len(d) else "prefix"
            if b >= n:
                for ci in cs.suf.get(s[b - n:b], ()):
                    d = cs.entries[ci][0]
                    k = _lcp(s[max(0, b - len(d)):b][::-1], d[::-1])
                    key = (b - k, b, ci)
                    if key not in found:
                        found[key] = "full" if k == len(d) else "suffix"
        if not found:
            continue
        starts = [t[0] for t in toks]
        for (a, b, ci), form in sorted(found.items()):
            out.append((_text_off(toks, starts, a),
                        _text_off(toks, starts, b - 1) + 1, ci, form, b - a))
    return out


def _text_off(toks, starts, i):
    j = bisect.bisect_right(starts, i) - 1
    a, _b, off = toks[j]
    return off + (i - a)


def line_of(text: str, off: int) -> int:
    return text.count("\n", 0, off) + 1


# --------------------------------------------------------------------------
# populations
# --------------------------------------------------------------------------

def tracked_paths(root: str):
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "-z"],
                           capture_output=True)
    except OSError as e:
        _fail(f"cannot run git: {e.strerror}")
    if r.returncode != 0:
        first = r.stderr.decode("utf-8", "replace").strip().splitlines()[:1]
        _fail(f"`git ls-files` failed in {root}: {first[0] if first else r.returncode}")
    return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0")
            if p]


def sweep_paths(top: str, exclude):
    if not os.path.isdir(top):
        _fail(f"--sweep {top} is not a directory")
    skip = {".git"} | set(exclude or ())
    out = []
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames[:] = sorted(d for d in dirnames if d not in skip)
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            out.append(os.path.relpath(full, top).replace(os.sep, "/"))
    return out


def read_member(top: str, rel: str):
    """-> (text, note).  The bytes as latin-1, one character per byte, so a
    binary or a capture holding NUL is read rather than skipped; a symlink is
    read as the link text git stores; a directory (a submodule gitlink) is
    not read and says so."""
    full = os.path.join(top, rel)
    if os.path.islink(full):
        return os.readlink(full), None
    if os.path.isdir(full):
        return None, "gitlink"
    try:
        with open(full, "rb") as f:
            return f.read().decode("latin-1"), None
    except OSError as e:
        return None, e.strerror or "unreadable"


# --------------------------------------------------------------------------
# scan, exemptions, verdict
# --------------------------------------------------------------------------

def scan_population(top, rels, cs, reader=read_member):
    """-> (hits, stats).  A hit is (path, line, endline, entry, form, digits);
    never the text."""
    hits, stats = [], {"read": 0, "gitlink": 0, "unreadable": 0}
    for rel in rels:
        text, note = reader(top, rel)
        if text is None:
            stats["gitlink" if note == "gitlink" else "unreadable"] += 1
            continue
        stats["read"] += 1
        for a, b, ci, form, k in match_text(text, cs):
            hits.append((rel, line_of(text, a), line_of(text, b - 1), ci,
                         form, k))
    return hits, stats


def applicable_exemptions(exemptions, top, population, reader, root=None):
    """-> the set of exempted paths that name THIS repository's file.

    🔴 An exemption names a file of this repository, not a relative path in
    whatever tree is being swept.  量 2026-10-09, the first `--sweep` of
    `upstream/`: it has a `LOG.md` of its own, the exemption for this
    repository's `LOG.md:87` was applied to it, and it came back STALE -- a
    finding about a file the exemption never named.  So in a sweep (or on
    stdin) an exemption applies -- and must match -- only where the swept file
    is byte-identical to the file at the same path in this repository, which
    is the case for an unpacked release archive and not for a foreign tree."""
    root = root or ROOT
    out = set()
    for e in exemptions:
        if e[0] not in population or e[0] in out:
            continue
        mine, _n = read_member(root, e[0])
        theirs, _n = reader(top, e[0])
        if mine is not None and mine == theirs:
            out.add(e[0])
    return out


def apply_exemptions(hits, cs, exemptions, population=None):
    """-> (findings, exempt, stale).  `population` None means every
    exemption must match (tracked mode); a set names the exempted paths that
    apply (see `applicable_exemptions`), and an exemption for any other path
    neither exempts nor goes stale.

    A row exempts at most ONE hit: the second hit of a name takes the next
    unused row of that name, or is a finding.  Taking the first unused row is
    exact, not merely greedy: a label belongs to one candidate per kind (one
    window, one digest), so the rows a hit can take are interchangeable."""
    used = [0] * len(exemptions)
    findings, exempt = [], []
    for h in hits:
        path, line, _end, ci, _form, k = h
        _d, kind, labels = cs.entries[ci]
        why = None
        for i, (ep, el, elab, ekind, edig, ereason) in enumerate(exemptions):
            if used[i]:
                continue          # one row exempts one hit -- EXEMPTIONS
            if population is not None and ep not in population:
                continue
            if (ep == path and el == line and ekind == kind and elab in labels
                    and edig == k):
                used[i] += 1
                why = ereason
                break
        if why is None:
            findings.append(h)
        else:
            exempt.append((h, why))
    stale = []
    for i, e in enumerate(exemptions):
        if used[i]:
            continue
        if population is not None and e[0] not in population:
            continue
        stale.append(e)
    return findings, exempt, stale


def fmt_hit(h, cs):
    path, line, end, ci, form, k = h
    d, kind, labels = cs.entries[ci]
    more = f" (+{len(labels) - 1} alias)" if len(labels) > 1 else ""
    span = f"{line}" if end == line else f"{line}-{end}"
    return (f"{path}:{span}  {labels[0]}{more}  {kind}  "
            f"{k} of {len(d)} hex digits ({form})")


def report(hits, stats, cs, exemptions, population, nfiles, out=print):
    findings, exempt, stale = apply_exemptions(hits, cs, exemptions,
                                               population)
    for h in findings:
        out(f"  \033[31mHIT\033[0m     {fmt_hit(h, cs)}")
    for h, why in exempt:
        out(f"  EXEMPT  {fmt_hit(h, cs)}  -- {why[:60]}")
    for e in stale:
        out(f"  \033[31mSTALE\033[0m   exemption {e[0]}:{e[1]} {e[2]} {e[3]} "
            f"{e[4]} -- names no hit; the line moved or the digest left it")
    out(f"  {stats['read']} file(s) read of {nfiles}, "
        f"{stats['gitlink']} submodule gitlink(s) not read"
        f"{' (a submodule is swept with --sweep DIR)' if stats['gitlink'] else ''}, "
        f"{stats['unreadable']} unreadable")
    nfind = len(findings) + len(stale)
    if nfind:
        out(f"  \033[31m{nfind} FINDING(S)\033[0m: {len(findings)} hit(s), "
            f"{len(stale)} stale exemption(s); {len(exempt)} exempt")
        return 1
    out(f"  CLEAN: 0 findings; {len(exempt)} exempt")
    return 0


def header(cs, out=print):
    kinds = ", ".join(f"{k} {v}" for k, v in sorted(cs.kinds().items()))
    out(f"digestscan {TOOL_VERSION}: N={cs.n}, {len(cs.entries)} candidate "
        f"digest(s) ({kinds}) over {cs.windows} window(s) of {cs.images} "
        f"image(s); {cs.dropped_constant} window(s) dropped as one repeated "
        f"value inside the forbidden region")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def check_n(n: int):
    if n < N_FLOOR:
        _fail(f"-N {n} is below {N_FLOOR}: tokens of three to seven digits "
              f"never join a chain, so a shorter match could be missed "
              f"silently -- see the docstring")
    if n > 64:
        _fail(f"-N {n} is longer than a sha256 and would match nothing")


def cmd_scan(args) -> int:
    check_n(args.n)
    dump = load_dump(args.dump or default_dump(),
                     args.identity_src or os.path.join(ROOT, IDENTITY_SRC))
    also = [parse_also(s) for s in (args.also or ())]
    cs = build_candidates(dump, also, args.n)
    del dump
    if args.stdin:
        data = sys.stdin.buffer.read().decode("latin-1")
        rels = [args.stdin]
        top = None

        def reader(_top, _rel):
            return data, None
    elif args.sweep:
        top = args.sweep
        rels = sweep_paths(top, args.exclude)
        reader = read_member
    else:
        top = ROOT
        rels = tracked_paths(top)
        reader = read_member
    if not rels:
        _fail(f"the population is empty -- a scan of zero files reports "
              f"CLEAN and means nothing")
    population = None
    if args.stdin or args.sweep:
        population = applicable_exemptions(EXEMPT, top, set(rels), reader)
    header(cs)
    if population is not None:
        print(f"  {len(population)} of {len(EXEMPT)} exemption(s) apply: an "
              f"exemption names this repository's file, and applies only "
              f"where the swept file is byte-identical to it")
    hits, stats = scan_population(top, rels, cs, reader)
    if stats["read"] == 0:
        _fail(f"{len(rels)} path(s) listed and none could be read")
    return report(hits, stats, cs, EXEMPT, population, len(rels))


def cmd_inventory(args) -> int:
    check_n(args.n)
    dump = load_dump(args.dump or default_dump(),
                     args.identity_src or os.path.join(ROOT, IDENTITY_SRC))
    also = [parse_also(s) for s in (args.also or ())]
    cs = build_candidates(dump, also, args.n)
    header(cs)
    for primary, aliases, at, n in enumerate_windows(dump, 0):
        kept = forbidden_distinct(dump, 0, at, n) >= MIN_DISTINCT_FORBIDDEN
        al = (" = " + ", ".join(aliases)) if aliases else ""
        print(f"  {'window' if kept else 'dropped'}  {primary}{al}")
    for ram, src, nb in USED_FLR:
        print(f"  dw      {wlabel('FLR', src, nb)}@ram0x{ram:08X}")
    print(f"  mactext {len(MAC_AT)} location(s) x 6 spellings x 2 line endings")
    return 0


def tokens_at_boundaries(text: str, n: int):
    """For `measure`: the N-digit strings this tool would look up."""
    starts, ends = [], []
    for s, toks in chains(text):
        if len(s) < n:
            continue
        for a, b, _off in toks:
            if len(s) - a >= n:
                starts.append(s[a:a + n])
            if b >= n:
                ends.append(s[b - n:b])
    return starts, ends


def cmd_measure(args) -> int:
    """Counts only: how many N-digit lookups a scan makes, how many distinct
    strings they are, and the false matches expected against C candidates
    whose prefixes and suffixes are uniformly random."""
    rels = (sweep_paths(args.sweep, args.exclude) if args.sweep
            else tracked_paths(ROOT))
    top = args.sweep or ROOT
    if args.candidates > 0:
        c = args.candidates
        csrc = "given by --candidates"
    else:
        dump = load_dump(args.dump or default_dump(), args.identity_src
                         or os.path.join(ROOT, IDENTITY_SRC))
        also = [parse_also(s) for s in (args.also or ())]
        c = len(build_candidates(dump, also, N_FLOOR).entries)
        csrc = "measured from the dump"
    ns = (8, 10, 12, 16)
    tot = {n: [0, 0, set(), set()] for n in ns}
    nread = 0
    for rel in rels:
        text, _note = read_member(top, rel)
        if text is None:
            continue
        nread += 1
        for n in ns:
            st, en = tokens_at_boundaries(text, n)
            tot[n][0] += len(st)
            tot[n][1] += len(en)
            tot[n][2].update(st)
            tot[n][3].update(en)
    print(f"digestscan measure: {nread} file(s) read of {len(rels)}; "
          f"C = {c} candidate digests ({csrc})")
    print("   N  prefix-lookups  suffix-lookups  distinct  "
          "expected-false-hits  P(any false hit)")
    import math
    for n in ns:
        a, b, ds, de = tot[n]
        lam_hits = (a + b) * c / 16.0 ** n
        lam_any = (len(ds) + len(de)) * c / 16.0 ** n
        print(f"  {n:2d}  {a:14d}  {b:14d}  {len(ds) + len(de):8d}  "
              f"{lam_hits:19.3g}  {1 - math.exp(-lam_any):.3g}")
    return 0


# --------------------------------------------------------------------------
# check -- dump-free joins between the tool's tables and the tree
# --------------------------------------------------------------------------

FLR_RE = re.compile(r"\bFLR +([0-9A-Fa-f]{6,8}) +([0-9A-Fa-f]{1,8}) +"
                    r"([0-9A-Fa-f]{1,8})\b")
FLR_EXT = (".md", ".json", ".py", ".tsv", ".log", ".txt", ".sh")


def flr_in_tree(root: str):
    found = {}
    for rel in tracked_paths(root):
        if not rel.endswith(FLR_EXT):
            continue
        text, _n = read_member(root, rel)
        if text is None or "FLR" not in text:
            continue
        for m in FLR_RE.finditer(text):
            dst, src, nb = (int(x, 16) for x in m.groups())
            if flashwin.overlaps_forbidden(src, nb) is not None:
                found.setdefault((dst, src, nb), rel)
    return found


def exemption_proxy(root: str, e):
    """Dump-free: the named line exists and a chain starting on it holds at
    least the named number of digits."""
    path, line, _lab, _kind, digits, _why = e
    text, note = read_member(root, path)
    if text is None:
        return f"{path} cannot be read ({note})"
    lines = text.split("\n")
    if line > len(lines):
        return f"{path} has {len(lines)} line(s), the exemption names {line}"
    lo = sum(len(x) + 1 for x in lines[:line - 1])
    hi = lo + len(lines[line - 1])
    for s, toks in chains(text):
        for a, _b, off in toks:
            if lo <= off < hi and len(s) - a >= digits:
                return None
    return (f"{path}:{line} starts no hex chain of {digits} digits -- the "
            f"exempted digest moved or left")


def cmd_check(_args) -> int:
    ok = bad = 0
    found = flr_in_tree(ROOT)
    table = set(USED_FLR)
    if not found:
        print("  FAIL  K1 no FLR triple over a forbidden window was found in "
              "the tree -- a derivation that finds nothing cannot confirm the "
              "table")
        bad += 1
    else:
        missing = sorted(set(found) - table)
        extra = sorted(table - set(found))
        if missing or extra:
            for t in missing:
                print(f"  FAIL  K1 FLR {t[0]:08X} {t[1]:06X} {t[2]:X} is in "
                      f"{found[t]} and not in USED_FLR")
            for t in extra:
                print(f"  FAIL  K1 USED_FLR row {t[0]:08X} {t[1]:06X} {t[2]:X} "
                      f"is in no tracked file")
            bad += 1
        else:
            print(f"  ok    K1 USED_FLR is exactly the {len(found)} FLR "
                  f"triple(s) over a forbidden window in the tracked tree")
            ok += 1
    errs = [x for x in (exemption_proxy(ROOT, e) for e in EXEMPT) if x]
    if errs:
        for x in errs:
            print(f"  FAIL  K2 {x}")
        bad += 1
    else:
        print(f"  ok    K2 each of the {len(EXEMPT)} exemption(s) names a line "
              f"that starts a hex chain of its recorded length")
        ok += 1
    print(f"  {ok} passed, {bad} failed")
    return 0 if bad == 0 else 1


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def synthetic_dump(seed: int = 0x5EED) -> bytes:
    """Seeded random bytes with H601's layout: an `H6` header and length, the
    MAC twice, a calibration stretch, a checksum, and a SECOND SECTOR THAT IS
    ALL ZERO so the constant filter has something real to drop."""
    rnd = random.Random(seed)
    b = bytearray(rnd.randbytes(FLASH_SIZE))
    b[0x6000:0x8000] = bytes(0x2000)
    ln = 0x48E
    b[0x6000:0x6006] = b"H601" + ln.to_bytes(2, "big")
    b[0x6006] = 0x01
    mac = bytes([0x02]) + rnd.randbytes(5)      # locally administered
    b[0x6007:0x600D] = mac
    b[0x6013:0x6019] = mac
    b[0x6040:0x6070] = rnd.randbytes(0x30)
    b[0x648A:0x6492] = rnd.randbytes(8)
    s = sum(b[0x6006:0x6006 + ln - 1]) & 0xFF
    b[0x6006 + ln - 1] = (-s) & 0xFF
    return bytes(b)


def self_test() -> int:
    ok = fail = 0
    skips = []

    def good(m):
        nonlocal ok
        print(f"  ok    {m}")
        ok += 1

    def bad(m):
        nonlocal fail
        print(f"  FAIL  {m}")
        fail += 1

    print(f"digestscan {TOOL_VERSION} self-test")
    print()
    sd = synthetic_dump()
    cs = build_candidates(sd, (), MIN_HEX)

    def cand(label, kind="sha256"):
        for d, k, labs in cs.entries:
            if k == kind and label in labs:
                return d
        return None

    def hits_of(text, c=None):
        return match_text(text, c or cs)

    def labels_of(hs, c=None):
        c = c or cs
        return [c.entries[h[2]][2][0] for h in hs]

    # --- W1 the aligned windows are exactly those overlapping H601 --------
    wins = enumerate_windows(sd, 0)
    aligned = {(at, n) for _p, _a, at, n in wins if n in ALIGNED_SIZES
               and at % n == 0}
    want = set()
    for n in ALIGNED_SIZES:
        for at in range(0, FLASH_SIZE, n):
            if any(at < hi and at + n > lo for lo, hi, _w in flashwin.FORBIDDEN):
                want.add((at, n))
    if aligned == want and len(want) == 72:
        good(f"W1 the aligned windows kept are exactly the {len(want)} that "
             f"overlap a forbidden region, 256 B to 4 MiB, and no other")
    else:
        bad(f"W1 {len(aligned)} aligned window(s) kept, {len(want)} expected "
            f"(missing {len(want - aligned)}, extra {len(aligned - want)})")

    # --- W2 the constant filter -------------------------------------------
    labs = {lab for _d, _k, ls in cs.entries for lab in ls}
    if ("sector@0x007000+0x1000" not in labs
            and "sector@0x006000+0x1000" in labs and cs.dropped_constant > 0):
        good(f"W2 an all-zero sector inside H601 is not a candidate, the "
             f"sector beside it is, and the drop is counted "
             f"({cs.dropped_constant})")
    else:
        bad("W2 the constant filter is wrong: the all-zero sector is a "
            "candidate, or the live one is not, or nothing was dropped")

    full = cand("sector@0x006000+0x1000")
    whole = cand("whole@0x000000+0x400000")
    if not full or not whole:
        bad("M0 the synthetic candidates are missing -- every case below "
            "would be vacuous")
        print(f"  {ok} passed, {fail} failed")
        return 1

    # --- M1 a full digest, on the right line -------------------------------
    h = hits_of(f"one\ntwo\nsha256 {full}  h601.bin\nfour\n")
    if (len(h) == 1 and h[0][3] == "full" and h[0][4] == 64
            and line_of("one\ntwo\n", h[0][0]) == 3):
        good("M1 a full 64-digit digest is found, as full, on its line")
    else:
        bad(f"M1 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M2 a 16-digit prefix ---------------------------------------------
    h = hits_of(f"| `{full[:16]}…` | the first 4 KiB |\n")
    if len(h) == 1 and h[0][3] == "prefix" and h[0][4] == 16:
        good("M2 a 16-digit prefix followed by an ellipsis is found, 16 digits")
    else:
        bad(f"M2 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M3 the N boundary, both sides, and N itself -----------------------
    # Absolute, not relative to MIN_HEX: the docstring's threat argument is
    # that a 32-bit prefix IS the MAC, so 8 digits must be found whatever the
    # constant says.  A case written as `MIN_HEX` digits would pass at 9.
    h_n = hits_of(f"sha256 {full[:8]}…\n")
    h_n1 = hits_of(f"sha256 {full[:7]}…\n")
    if MIN_HEX == 8 and len(h_n) == 1 and h_n[0][4] == 8 and not h_n1:
        good("M3 exactly 8 digits -- a 32-bit prefix -- are found and 7 are not")
    else:
        bad(f"M3 N={MIN_HEX}; 8 digits: {len(h_n)} hit(s); 7 digits: "
            f"{len(h_n1)} hit(s)")

    # --- M4 upper case -----------------------------------------------------
    h = hits_of(f"SHA256={full.upper()}\n")
    if len(h) == 1 and h[0][4] == 64:
        good("M4 an upper-case digest is found")
    else:
        bad(f"M4 {len(h)} hit(s)")

    # --- M5 split across two literals on two lines (leakscan.py:137) ------
    txt = (f'X = 1\nDUMP_SHA256 = ("{whole[:39]}"\n'
           f'               "{whole[39:]}")\n')
    h = hits_of(txt)
    if (len(h) == 1 and h[0][4] == 64 and h[0][3] == "full"
            and line_of(txt, h[0][0]) == 2 and line_of(txt, h[0][1] - 1) == 3):
        good("M5 a digest split across two literals on two lines is ONE "
             "full hit, lines 2-3 -- the tools/leakscan.py:137 shape")
    else:
        bad(f"M5 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M6 a C byte array across lines (rtl819x-spi.c's shape) -----------
    arr = ",\n\t".join(", ".join("0x%02X" % b for b in bytes.fromhex(full)[i:i + 8])
                       for i in range(0, 32, 8))
    txt = f"static const u8 want[32] = {{\n\t{arr},\n}};\n"
    h = hits_of(txt)
    if len(h) == 1 and h[0][4] == 64 and line_of(txt, h[0][0]) == 2:
        good("M6 a digest written as a C byte array across four lines is "
             "found whole -- the driver's shape")
    else:
        bad(f"M6 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M6b the same channel on REAL committed material, no dump ---------
    # sha256("abc") is FIPS 180-2's public vector and the driver compiles it
    # in as `rtl819x_spi_kat1_want`.  A candidate set holding only that value
    # must find it in the committed file, once, as a whole C array.
    drv = os.path.join(ROOT, IDENTITY_SRC)
    kat = CandidateSet(MIN_HEX)
    kat.add("sha256", hashlib.sha256(b"abc").hexdigest(), "kat:abc")
    text, note = read_member(ROOT, IDENTITY_SRC) if os.path.exists(drv) else (None, "missing")
    if text is None:
        bad(f"M6b {IDENTITY_SRC} cannot be read ({note}) -- a broken "
            f"reference in this repository, not an allowed skip")
    else:
        h = match_text(text, kat)
        if (len(h) == 1 and h[0][4] == 64
                and "rtl819x_spi_kat1_want" in text.split("\n")[line_of(text, h[0][0]) - 2]):
            good("M6b the C-array channel finds sha256(\"abc\") in the "
                 "committed driver, once, whole, where kat1_want begins")
        else:
            bad(f"M6b {len(h)} hit(s) of the public vector in the driver")

    # --- M7 a suffix ------------------------------------------------------
    h = hits_of(f"sha256 …{full[-16:]}\n")
    if len(h) == 1 and h[0][3] == "suffix" and h[0][4] == 16:
        good("M7 a 16-digit suffix after an ellipsis is found, as a suffix")
    else:
        bad(f"M7 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M8 the FLS-14 shape: 8 digits, an ellipsis, 7 digits -------------
    h = hits_of(f"`sha256 {whole[:8]}…{whole[-7:]}`\n")
    if len(h) == 1 and h[0][3] == "prefix" and h[0][4] == 8:
        good("M8 the FLS-14 shape is ONE prefix hit of 8; the 7-digit suffix "
             "is below N and is not")
    else:
        bad(f"M8 {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M9 NEGATIVE, and the twin that makes it mean something ----------
    off = hashlib.sha256(sd[0x0000:0x1000]).hexdigest()
    comp = complement_digest(sd)
    neg = f"sector 0: {off}\ncomplement: {comp}\n"
    twin = CandidateSet(MIN_HEX)
    twin.add("sha256", off, "sector@0x000000+0x1000")
    twin.add("sha256", comp, "complement")
    if not hits_of(neg) and len(match_text(neg, twin)) == 2:
        good("M9 NEGATIVE: digests of a sector below H601 and of H601's "
             "complement are not reported -- and the same text IS matched "
             "when they are candidates, so the negative is not vacuous")
    else:
        bad(f"M9 {len(hits_of(neg))} hit(s) on windows that overlap nothing "
            f"forbidden; twin {len(match_text(neg, twin))}")

    # --- M10 a DW capture: the address column joins nothing ---------------
    dw_ok = flashwin.render_dw(0x80A00000, sd[0x1000:0x1100],
                               "DW 80A00000 64").decode("ascii")
    dwh = flashwin.render_dw(0x80A00600, sd[0x6000:0x6100], "DW 80A00600 64")
    dwd = hashlib.sha256(dwh).hexdigest()
    h1 = hits_of(dw_ok)
    h2 = hits_of(f"sha256 of the read-back: {dwd}\n")
    if not h1 and len(h2) == 1 and labels_of(h2)[0].startswith("dw:"):
        good("M10 a DW capture of a public window is CLEAN, and the sha256 "
             "flashwin render would print for an H601 window is found as dw:")
    else:
        bad(f"M10 public capture {len(h1)} hit(s); H601 rendering "
            f"{labels_of(h2)}")

    # --- M10b a digest held in RAM and dumped by DW, across two lines -----
    dwdig = flashwin.render_dw(0x80A00000, bytes.fromhex(full),
                               "DW 80A00000 8").decode("ascii")
    h = hits_of(dwdig)
    if len(h) == 1 and h[0][4] == 64 and h[0][3] == "full":
        good("M10b a digest dumped by DW across two lines is ONE full hit -- "
             "the address column between them is dropped, not a break")
    else:
        bad(f"M10b {[(f, k) for _a, _b, _c, f, k in h]}")

    # --- M11 the MAC, as bytes and as text --------------------------------
    mac = sd[0x6007:0x600D]
    hb = hits_of(f"{hashlib.md5(mac).hexdigest()}\n")
    ht = hits_of(hashlib.sha256((":".join("%02x" % x for x in mac) + "\n")
                                .encode()).hexdigest() + "\n")
    if (len(hb) == 1 and labels_of(hb)[0].startswith("mac@0x006007")
            and len(ht) == 1 and labels_of(ht)[0].startswith("mactext:colon+LF")):
        good("M11 md5 of the MAC's six bytes and sha256 of `echo $mac` are "
             "both found, labelled as the MAC")
    else:
        bad(f"M11 bytes {labels_of(hb)} text {labels_of(ht)}")

    # --- M12 twice on a line is two hits ----------------------------------
    # Two full digests AND two 16-digit prefixes, each pair in ONE chain.
    # 量 2026-10-09, the mutation suite's first run: with full digests only,
    # a matcher that keyed every prefix hit in a chain to one slot survived,
    # because the suffix lookup found the second digest on its own.  Two
    # prefixes are visible to the prefix lookup alone.
    h = hits_of(f"{full} {full}\n")
    hp = hits_of(f"{full[:16]} {full[:16]}\n")
    if len(h) == 2 and len(hp) == 2 and all(x[4] == 16 for x in hp):
        good("M12 the same digest twice in one chain is two hits, whole or as "
             "two 16-digit prefixes")
    else:
        bad(f"M12 full x2: {len(h)} hit(s); prefix x2: {len(hp)} hit(s); "
            f"wanted 2 and 2")

    # --- E1-E7 exemptions, by name, both ways ------------------------------
    ci = [i for i, (_d, k, ls) in enumerate(cs.entries)
          if k == "sha256" and "sector@0x006000+0x1000" in ls][0]
    hit = ("a.md", 3, 3, ci, "full", 64)
    ex = [("a.md", 3, "sector@0x006000+0x1000", "sha256", 64, "test ruling")]
    f1, e1, s1 = apply_exemptions([hit], cs, ex)
    if not f1 and len(e1) == 1 and not s1:
        good("E1 a hit named exactly by an exemption is EXEMPT, not a finding")
    else:
        bad(f"E1 findings {len(f1)} exempt {len(e1)} stale {len(s1)}")
    f2, e2, s2 = apply_exemptions([], cs, ex)
    if not f2 and not e2 and len(s2) == 1:
        good("E2 an exemption that names no hit is STALE -- a finding")
    else:
        bad(f"E2 stale {len(s2)}")
    near = [("a.md", 4, "sector@0x006000+0x1000", "sha256", 64, "x"),
            ("a.md", 3, "page@0x006000+0x100", "sha256", 64, "x"),
            ("a.md", 3, "sector@0x006000+0x1000", "md5", 64, "x"),
            ("a.md", 3, "sector@0x006000+0x1000", "sha256", 16, "x")]
    f3, e3, s3 = apply_exemptions([hit], cs, near)
    if len(f3) == 1 and not e3 and len(s3) == 4:
        good("E3 an exemption one field off -- line, label, kind or digits -- "
             "exempts nothing and is itself stale")
    else:
        bad(f"E3 findings {len(f3)} exempt {len(e3)} stale {len(s3)}")
    f4, e4, s4 = apply_exemptions([], cs, ex, population={"b.md"})
    f5, e5, s5 = apply_exemptions([], cs, ex, population={"a.md"})
    if not s4 and len(s5) == 1:
        good("E4 in a sweep, an exemption for a file outside the population "
             "does not apply; one for a file inside it must match")
    else:
        bad(f"E4 outside {len(s4)} stale, inside {len(s5)} stale")
    # E5 -- the upstream/ incident: a swept tree's own `a.md` is not this
    # repository's `a.md`.  Hermetic: a fake repository root and two swept
    # trees, one holding the same bytes and one holding other bytes.
    with tempfile.TemporaryDirectory() as tr:
        for sub, body in (("repo", "same\n"), ("archive", "same\n"),
                          ("foreign", "other\n")):
            os.makedirs(os.path.join(tr, sub))
            with open(os.path.join(tr, sub, "a.md"), "w") as f:
                f.write(body)
        same = applicable_exemptions(ex, os.path.join(tr, "archive"),
                                     {"a.md"}, read_member,
                                     root=os.path.join(tr, "repo"))
        other = applicable_exemptions(ex, os.path.join(tr, "foreign"),
                                      {"a.md"}, read_member,
                                      root=os.path.join(tr, "repo"))
        _f6, _e6, s6 = apply_exemptions([], cs, ex, population=other)
    if same == {"a.md"} and not other and not s6:
        good("E5 an exemption applies to a swept file byte-identical to this "
             "repository's, and neither applies nor goes stale on a foreign "
             "tree's file of the same name -- the upstream/ LOG.md incident")
    else:
        bad(f"E5 identical tree {sorted(same)}, foreign tree {sorted(other)}, "
            f"stale on foreign {len(s6)}")
    # E6 -- one row exempts ONE hit.  `SPEC.md`'s FLS-14 line holds the same
    # 8-digit prefix twice: two hits of one name.  With one row the second
    # hit is a finding, not covered by the first; two rows exempt both; two
    # rows and one hit leave one STALE.
    fe1, ee1, se1 = apply_exemptions([hit, hit], cs, ex)
    fe2, ee2, se2 = apply_exemptions([hit, hit], cs, ex + ex)
    fe3, ee3, se3 = apply_exemptions([hit], cs, ex + ex)
    if (len(fe1) == 1 and len(ee1) == 1 and not se1
            and not fe2 and len(ee2) == 2 and not se2
            and not fe3 and len(ee3) == 1 and len(se3) == 1):
        good("E6 one row exempts one hit: two hits of one name and one row "
             "leave a finding, two rows exempt both, two rows and one hit "
             "leave one STALE")
    else:
        bad(f"E6 two hits/one row: {len(fe1)} finding(s); two hits/two rows: "
            f"{len(fe2)} finding(s), {len(se2)} stale; one hit/two rows: "
            f"{len(se3)} stale")
    # E7 -- `check`'s K2 proxy, both ways, hermetic: a row is permitted where
    # its line starts a hex chain of its length, and refused for one digit
    # more, on a line holding no hex, and past the end of the file.
    with tempfile.TemporaryDirectory() as tk:
        with open(os.path.join(tk, "a.md"), "w", encoding="utf-8") as f:
            f.write("plain words only\nsha256 0123456789abcdef… the first "
                    "4 KiB\nend\n")
        k_ok = exemption_proxy(tk, ("a.md", 2, "x", "sha256", 16, "t"))
        k_long = exemption_proxy(tk, ("a.md", 2, "x", "sha256", 17, "t"))
        k_nohex = exemption_proxy(tk, ("a.md", 1, "x", "sha256", 8, "t"))
        k_past = exemption_proxy(tk, ("a.md", 9, "x", "sha256", 8, "t"))
    if (k_ok is None and k_long and "a.md:2 " in k_long
            and k_nohex and "a.md:1 " in k_nohex
            and k_past and "names 9" in k_past):
        good("E7 K2's proxy permits a row whose line starts a hex chain of its "
             "length, and refuses one digit more, a line with no hex, and a "
             "line past the end")
    else:
        bad(f"E7 permit {k_ok!r}; 17 digits {k_long!r}; no hex {k_nohex!r}; "
            f"past the end {k_past!r}")

    # --- F1-F7 the command line, as a subprocess --------------------------
    here = os.path.abspath(__file__)
    # A run of six or more digits not introduced by `0x` -- every offset the
    # tool prints is in a label as `0x%06X`, and six digits of an offset can
    # sit inside a candidate by chance.  The second test closes that gap from
    # the other side: no candidate's first or last eight digits ANYWHERE.
    HEXRUN = re.compile(r"(?<![xX0-9A-Fa-f])[0-9A-Fa-f]{6,}")

    def run(*a, stdin=None):
        return subprocess.run([sys.executable, here, *a], input=stdin,
                              capture_output=True)

    def leaked(r):
        """How many places the output holds candidate digits."""
        blob = (r.stdout + r.stderr).decode("utf-8", "replace").lower()
        n = 0
        for m in HEXRUN.finditer(blob):
            if any(m.group(0) in d for d, _k, _l in cs.entries):
                n += 1
        for d, _k, _l in cs.entries:
            if d[:8] in blob or d[-8:] in blob:
                n += 1
        return n

    def refused(r, must_say):
        err = r.stderr.decode("utf-8", "replace")
        if r.returncode != 2:
            return f"rc={r.returncode}, wanted 2"
        if r.stdout:
            return f"{len(r.stdout)} byte(s) on stdout"
        if "Traceback" in err:
            return "a traceback, not a reason"
        if must_say not in err:
            return f"stderr does not say {must_say!r}"
        return None

    with tempfile.TemporaryDirectory() as td:
        dpath = os.path.join(td, "synthetic.bin")
        with open(dpath, "wb") as f:
            f.write(sd)
        idsrc = os.path.join(td, "identity.c")
        with open(idsrc, "w", encoding="ascii") as f:
            f.write("static const u8 %s[32] = {\n\t%s,\n};\n" % (
                IDENTITY_SYM, ", ".join("0x%02X" % x
                                        for x in bytes.fromhex(comp))))
        e = refused(run("scan", "--dump", os.path.join(td, "absent.bin"),
                        "--identity-src", idsrc, "--stdin", "x.md",
                        stdin=b""), "no dump at")
        if e:
            bad(f"F1 a missing dump: {e}")
        else:
            good("F1 a missing dump is refused: rc 2, a reason, nothing on "
                 "stdout, no traceback")
        short = os.path.join(td, "short.bin")
        with open(short, "wb") as f:
            f.write(sd[:0x100000])
        e = refused(run("scan", "--dump", short, "--identity-src", idsrc,
                        "--stdin", "x.md", stdin=b""), "not a whole-flash dump")
        if e:
            bad(f"F2 a 1 MiB dump: {e}")
        else:
            good("F2 a dump of the wrong size is refused with its reason")
        e = refused(run("scan", "--dump", dpath, "--identity-src", drv,
                        "--stdin", "x.md", stdin=b""), "not the reference dump")
        if e:
            bad(f"F3 a 4 MiB dump that is not this unit's: {e}")
        else:
            good("F3 a right-sized dump whose complement digest is not the "
                 "driver's FLS-24 constant is refused -- the wrong dump would "
                 "scan CLEAN")
        planted = (f"line one\nsha256 {full}\n| {whole[:16]}… |\n"
                   f"{hashlib.sha256(mac).hexdigest()}\n").encode()
        r = run("scan", "--dump", dpath, "--identity-src", idsrc,
                "--stdin", "planted.md", stdin=planted)
        out = r.stdout.decode("utf-8", "replace")
        nleak = leaked(r)
        if r.returncode != 1 or out.count("HIT") != 3:
            bad(f"F4 rc={r.returncode}, {out.count('HIT')} HIT line(s), "
                f"wanted rc 1 and 3")
        elif nleak:
            bad(f"F4 the verdict PRINTED {nleak} run(s) of candidate digits")
        elif "planted.md:2" not in out:
            bad("F4 the verdict does not name the line")
        else:
            good("F4 three planted digests are three HITs with rc 1, and the "
                 "output holds no six-digit run of any candidate")
        r = run("scan", "--dump", dpath, "--identity-src", idsrc,
                "--stdin", "clean.md", stdin=f"{off}\n{comp}\n".encode())
        out = r.stdout.decode("utf-8", "replace")
        if r.returncode == 0 and "CLEAN" in out and not leaked(r):
            good("F5 a file holding only permitted digests is CLEAN, rc 0")
        else:
            bad(f"F5 rc={r.returncode}")
        empty = os.path.join(td, "empty")
        os.makedirs(empty)
        e = refused(run("scan", "--dump", dpath, "--identity-src", idsrc,
                        "--sweep", empty), "population is empty")
        if e:
            bad(f"F6 an empty sweep: {e}")
        else:
            good("F6 a sweep of zero files is refused rather than CLEAN")
        e = refused(run("scan", "-N", str(N_FLOOR - 1), "--dump", dpath,
                        "--identity-src", idsrc, "--stdin", "x.md",
                        stdin=b""), "below")
        if e:
            bad(f"F7 N below the floor: {e}")
        else:
            good(f"F7 -N {N_FLOOR - 1} is refused with the reason")

    # --- Q1 the skip label is the one ci-expected.tsv allows -------------
    tsv = os.path.join(ROOT, "tools", "ci-expected.tsv")
    want_lab, found = None, False
    try:
        with open(tsv, encoding="utf-8") as fh:
            for line in fh:
                c = line.rstrip("\n").split("\t")
                if c and c[0] == "digestscan" and len(c) > 2 and c[2] != "-":
                    found, want_lab = True, c[2]
    except OSError as e:
        want_lab = f"<{e}>"
    if found and want_lab == SKIP_LABEL:
        good(f"Q1 the printed skip label is the one ci-expected allows "
             f"({SKIP_LABEL!r})")
    else:
        bad(f"Q1 this suite prints {SKIP_LABEL!r}; ci-expected.tsv says "
            f"{want_lab!r}")

    # --- R1-R3 the real material ---------------------------------------
    rd = default_dump()
    if not os.path.exists(rd):
        skips.append((SKIP_LABEL, 3))
        print("  skip   %-52s %s" % (
            SKIP_LABEL, "R1-R3 need $FWRE_WORK/dumps/flash-n150rt-console-2.bin "
            "-- 4 MiB of this unit's own flash, which can never be committed "
            "(covers 3)"))
    else:
        with open(rd, "rb") as f:
            real = f.read()
        want_id = identity_expected(drv)
        if len(real) == FLASH_SIZE and complement_digest(real) == want_id:
            good("R1 the dump's sha256 over H601's complement equals the "
                 "driver's FLS-24 constant -- two sources, one value")
        else:
            bad("R1 the dump is not the one FLS-24's constant was derived from")
        rcs = build_candidates(real, (), MIN_HEX)
        del real
        pos = {}
        for rel in ("LOG.md", "tools/leakscan.py"):
            t, _n = read_member(ROOT, rel)
            pos[rel] = [] if t is None else [
                (line_of(t, a), rcs.entries[ci][1], rcs.entries[ci][2], form, k)
                for a, _b, ci, form, k in match_text(t, rcs)]
        need = [("LOG.md", 87), ("tools/leakscan.py", 137)]
        got = all(any(ln == want_ln and kind == "sha256" and k == 64
                      and "whole@0x000000+0x400000" in labs
                      for ln, kind, labs, _f, k in pos[rel])
                  for rel, want_ln in need)
        hits_ex = [(rel, ln, ci, f, k)
                   for rel in pos for (ln, _kd, _l, f, k) in pos[rel]]
        if got:
            good("R2 POSITIVE: LOG.md:87 and tools/leakscan.py:137 are found -- "
                 "the whole image's sha256, 64 of 64 digits, the second split "
                 "across two literals")
        else:
            bad(f"R2 the two lines FLW-1 fixed in advance were not both found "
                f"({len(hits_ex)} hit(s) in the two files)")
        twin = CandidateSet(MIN_HEX)
        twin.add("sha256", want_id, "complement")
        bad3 = []
        nseen = 0
        for rel in ("SPEC.md", IDENTITY_SRC):
            t, _n = read_member(ROOT, rel)
            if t is None:
                bad3.append(f"{rel} unreadable")
                continue
            spans = [(a, b) for a, b, _c, _f, _k in match_text(t, twin)]
            nseen += len(spans)
            if not spans:
                bad3.append(f"the complement digest was not found in {rel}")
            for a, b, _c, _f, _k in match_text(t, rcs):
                if any(a < sb and b > sa for sa, sb in spans):
                    bad3.append(f"{rel}:{line_of(t, a)} reported")
        if not bad3:
            good(f"R3 NEGATIVE: FLS-24's complement digest -- found {nseen} "
                 f"time(s) in SPEC.md and the driver when it IS a candidate -- "
                 f"is not reported by the real candidate set")
        else:
            bad("R3 " + "; ".join(bad3))

    print()
    for lbl, nn in skips:
        print(f"  (skipped: {lbl}, {nn} case(s))")
    print(f"  {ok} passed, {fail} failed")
    return 0 if fail == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    def common(p, dump=True):
        p.add_argument("-N", dest="n", type=int, default=MIN_HEX,
                       help=f"minimum matching hex digits (default {MIN_HEX})")
        if dump:
            p.add_argument("--dump", default=None,
                           help="the reference 4 MiB dump (default "
                                "$FWRE_WORK/" + DUMP_REL + ")")
            p.add_argument("--identity-src", default=None,
                           help="the C source holding the FLS-24 constant "
                                "(default " + IDENTITY_SRC + ")")
            p.add_argument("--also", action="append", default=None,
                           metavar="IMAGE@OFFSET",
                           help="another image of flash at OFFSET; repeatable")

    s = sub.add_parser("scan", help="the verdict: the tracked tree, --sweep "
                                    "DIR, or --stdin NAME")
    common(s)
    g = s.add_mutually_exclusive_group()
    g.add_argument("--sweep", default=None, help="walk this directory")
    g.add_argument("--stdin", default=None, metavar="NAME",
                   help="scan standard input, reported as NAME")
    s.add_argument("--exclude", action="append", default=None, metavar="NAME",
                   help="directory name to skip in --sweep; `.git` always is")
    s.set_defaults(func=cmd_scan)

    i = sub.add_parser("inventory", help="the candidate windows, labels and "
                                         "counts only")
    common(i)
    i.set_defaults(func=cmd_inventory)

    m = sub.add_parser("measure", help="hex-run statistics for choosing N")
    common(m)
    m.add_argument("--sweep", default=None)
    m.add_argument("--exclude", action="append", default=None)
    m.add_argument("--candidates", type=int, default=0,
                   help="C, when no --dump is given")
    m.set_defaults(func=cmd_measure)

    c = sub.add_parser("check", help="dump-free joins: USED_FLR against the "
                                     "tree, EXEMPT against its lines")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
