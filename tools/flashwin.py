#!/usr/bin/env python3
"""Render the loader's ``DW`` reply for a window of flash, from a dump.

Why this exists
---------------
``RUNSHEET.md`` ``G8a``/``G8b`` bracket a seating with two ``FLR``+``DW`` reads
of flash, and the check is a ``cmp`` against captures taken on 2026-08-24.  That
works for the two regions those captures cover -- ``0x000000`` (the loader head)
and ``0x060000`` (the ``cr6c`` header) -- and it does not work for the one region
that matters most.

**``H601`` at ``0x006000``-``0x007FFF`` has never been in that bracket**, and it
is the region ``CLAUDE.md`` marks *"this unit's MAC and radio calibration, not
restored by reset"*.  ``bench/2026-08-30b/L3.log`` is why it stopped being
theoretical: this project's own kernel instantiated an MTD partition
``0x000000-0x130000``, which contains it.

There is no committed capture of ``H601`` to ``cmp`` against and there can never
be one -- the bytes identify one physical device, ``CLAUDE.md`` forbids
committing them and ``tools/audit-bench-log.py`` would (correctly) fire on them.
So the expectation is computed here instead, from
``$FWRE_WORK/dumps/flash-n150rt-console-2.bin``, and the operator compares at the
bench.  **The reading stays out of the repository; the CONTROL does not.**

The control, and it is the whole argument
-----------------------------------------
The same renderer, applied to flash ``0x000000`` and ``0x060000``, must reproduce
``bench/2026-08-24d/G8a-rd0.log`` and ``G8a-rd6.log`` **byte for byte** -- two
777-byte captures taken off this device on 2026-08-24 through the loader.  量
2026-08-30: both reproduce, from both committed dumps, which are themselves
byte-identical over all 4,194,304 bytes.

So a reader who cannot see the ``H601`` rendering can still see that the
instrument which produced it reproduces two readings they CAN see.  That is the
part of the evidence that survives publication.

Where this will fail, stated before it is used
-----------------------------------------------
1. It renders one *format* -- ``%08X:`` then four tab-separated ``%08X`` then
   ``\\n\\r``, read off ``bench/2026-08-24d/G8a-rd0.log`` and confirmed against
   ``docs/loader-command-semantics.md``.  The real-material controls exercise
   exactly one word count (64) at two offsets.  A different length, a different
   pad or a different separator is outside what has been checked.
2. It assumes the dump's byte offset is the loader's flash offset.  That is
   checked at ``0x000000`` and ``0x060000`` and nowhere else.
3. ``FORBIDDEN`` below is a hardcoded copy of ``CLAUDE.md``'s list.  A third
   region added there and not here is a silent gap, and nothing checks the two
   against each other.
4. A match proves the window is unchanged **since the dump**, not that nothing
   was written: two writes that cancel, or a write outside the window, are
   invisible.  Three 256-byte windows are **768 bytes of 4,194,304** -- 0.018 %.

Usage
-----
    flashwin.py render --dump <file> --at 0x000000 --ram 0x80A00000
    flashwin.py render --dump <file> --at 0x006000 --ram 0x80A00200 --out <path>
    flashwin.py scan bench/2026-08-31c/K-P3.log --dump <file>
    flashwin.py scan --sweep bench --dump <file>
    flashwin.py --self-test

A window overlapping a ``FORBIDDEN`` region may not be printed and may not be
written inside this repository; ``--out`` to a path outside it is the only way
to get it, and that is enforced here rather than remembered.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile

TOOL_VERSION = "1.0"

# 🔴 THE SKIP LABEL IS ONE VARIABLE USED THREE TIMES: printed by the skip
# line, printed again in the summary, and checked by `Q1` against
# `tools/ci-expected.tsv`, which is what `tools/ci-census.py` reads on the
# runner.  量, CI run 33410057391: this session edited the table's column
# and left the two string literals here alone, and the suite was 40/40
# GREEN on the bench while CI went red on `UNEXPECTED-SKIP`.  **The bench
# cannot see that class** -- with `$FWRE_WORK` present the cases RUN, no
# skip line is printed, and no label is ever compared.  Third time in this
# repository: `test-kbuild-cflags` C1, `leakscan` Q1, `replay-capture` R14.
SKIP_LABEL = "this unit's flash dump"

# Copied from CLAUDE.md's "Never" table. `H601` is the one that cannot be
# published; the loader region is forbidden to WRITE but its bytes are the
# vendor's code and are already committed in bench/2026-08-24d/G8a-rd0.log, so
# it is not listed here. This list is about PUBLICATION, not about writing.
FORBIDDEN = [
    (0x006000, 0x008000, "H601 -- this unit's MAC and radio calibration"),
]


def _fail(msg: str) -> "NoReturn":  # noqa: F821
    print(f"flashwin: {msg}", file=sys.stderr)
    raise SystemExit(2)


def overlaps_forbidden(at: int, nbytes: int):
    """Half-open [at, at+nbytes) against half-open [lo, hi).

    The two boundary cases are C9's, in both directions: a window ENDING at
    0x006000 is clear and a window whose last byte is 0x006000 is not.
    """
    end = at + nbytes
    for lo, hi, why in FORBIDDEN:
        if at < hi and end > lo:
            return (lo, hi, why)
    return None


def render_dw(ram_base: int, data: bytes, cmd: str) -> bytes:
    """The loader's `DW` reply for `data` placed at `ram_base`.

    Format read off bench/2026-08-24d/G8a-rd0.log and cross-read in
    docs/loader-command-semantics.md: the echoed command then `\\n\\r`, then one
    line per four words as `%08X:` + four `\\t%08X`, each ending `\\n\\r`, then
    the prompt with no line ending of its own. 47 bytes a line, which is the
    same 47 `tools/reply-size.py` fits its model on.
    """
    if len(data) % 16:
        _fail(f"{len(data)} bytes is not a whole number of 4-word lines")
    out = [cmd.encode("ascii") + b"\n\r"]
    for i in range(0, len(data), 16):
        words = [int.from_bytes(data[i + k:i + k + 4], "big") for k in range(0, 16, 4)]
        line = "%08X:" % (ram_base + i) + "".join("\t%08X" % w for w in words)
        out.append(line.encode("ascii") + b"\n\r")
    out.append(b"<RealTek>")
    return b"".join(out)


DW_ECHO = re.compile(rb"^DW ([0-9A-Fa-f]{8}) (\d+)\n\r")
DW_LINE = re.compile(rb"^([0-9A-Fa-f]{8}):((?:\t[0-9A-Fa-f]{8})+)\n\r")


def normalise_dw(text: bytes) -> bytes:
    """A `DW` reply reduced to its DATA, with the echo and the address column
    removed.  Refuses anything that does not parse as one.

    🔴 Why this exists, 2026-08-30 (fourteenth session).  The flash bracket
    compares a capture against a committed one with `cmp`, byte for byte -- and
    a `DW` reply carries the typed command and a `%08X:` address column, both
    of which contain the RAM DESTINATION.  So two reads of the SAME flash
    window into DIFFERENT RAM addresses do not compare equal, and the bracket's
    second half was forced to reuse the first half's destination.

    That reuse costs a control.  If the destination is the same every time,
    *the RAM already held these bytes* is not excluded, and an `FLR` that did
    nothing looks exactly like one that worked.  Normalising to the data lets
    the next block read into a different address AND take a pre-read of the
    destination first, which is the negative control this bracket has never
    had.  `bench/README.md` records the bracket; `SPEC.md` `FLS-20` records
    what it does and does not buy.

    ⚠️ It removes the address ON PURPOSE, so it cannot see a reply that landed
    at the wrong address.  The `FLR` echo check is what covers that, and the
    card keeps it.
    """
    lines = text.split(b"\n\r")
    if not lines or not DW_ECHO.match(text):
        _fail("not a DW reply: no `DW <addr> <words>` echo at the start")
    out, n = [], 0
    for raw in lines[1:]:
        if raw == b"<RealTek>" or raw == b"":
            continue
        m = DW_LINE.match(raw + b"\n\r")
        if not m:
            _fail(f"not a DW data line: {raw[:32]!r}")
        words = m.group(2).split(b"\t")[1:]
        out.append(b"\t".join(words))
        n += len(words)
    if not n:
        _fail("a DW reply with no data lines is not a reading")
    return b"\n".join(out) + b"\n"


def cmd_normalise(args) -> int:
    with open(args.file, "rb") as f:
        text = f.read()
    data = normalise_dw(text)
    if args.out:
        tmp = args.out + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, args.out)
        print(f"  {args.out}  {len(data)} bytes, "
              f"{len(data.split(chr(10).encode())) - 1} line(s)")
        return 0
    sys.stdout.buffer.write(data)
    return 0


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _inside_repo(path: str) -> bool:
    root = os.path.realpath(_repo_root())
    p = os.path.realpath(os.path.abspath(path))
    return p == root or p.startswith(root + os.sep)


def cmd_render(args) -> int:
    if args.bytes % 16:
        _fail(f"--bytes {args.bytes} is not a multiple of 16")
    with open(args.dump, "rb") as f:
        f.seek(args.at)
        data = f.read(args.bytes)
    if len(data) != args.bytes:
        _fail(f"the dump holds only {len(data)} bytes at 0x{args.at:06X}")

    words = args.bytes // 4
    cmd = f"DW {args.ram:08X} {words}"
    text = render_dw(args.ram, data, cmd)

    hit = overlaps_forbidden(args.at, args.bytes)
    if hit is not None:
        lo, hi, why = hit
        if not args.out:
            _fail(
                f"0x{args.at:06X}+{args.bytes} overlaps 0x{lo:06X}-0x{hi - 1:06X} "
                f"({why}).\n"
                "  These bytes identify one physical device. CLAUDE.md forbids "
                "committing them\n"
                "  and this tool will not print them. Pass --out with a path "
                "OUTSIDE this\n"
                "  repository -- $FWRE_WORK/rebuild/bench-only/ is where the "
                "uploaded images live\n"
                "  for the same reason."
            )
        if _inside_repo(args.out):
            _fail(
                f"--out {args.out} is inside {_repo_root()}.\n"
                f"  0x{args.at:06X}+{args.bytes} overlaps 0x{lo:06X}-0x{hi - 1:06X} "
                f"({why}) and may not be written there."
            )

    if args.out:
        tmp = args.out + ".tmp"
        with open(tmp, "wb") as f:
            f.write(text)
        os.replace(tmp, args.out)
        print(f"  {args.out}  {len(text)} bytes"
              f"{'  [not shown: ' + hit[2] + ']' if hit else ''}")
        if hit is None:
            print(f"  sha256 {hashlib.sha256(text).hexdigest()}")
        else:
            # Deliberately no hash. A digest over a window whose only unknown is
            # 24 bits of MAC is brute-forceable by anyone who knows the format,
            # so publishing one publishes the address. The verdict is what gets
            # written down: this file against the round-A file, cmp, same/differ.
            print("  sha256 withheld: with the rest of the window known this "
                  "would be a 2^24 search for the MAC")
        return 0

    sys.stdout.buffer.write(text)
    sys.stdout.buffer.write(b"\n")
    print(f"# {len(text)} bytes, sha256 {hashlib.sha256(text).hexdigest()}",
          file=sys.stderr)
    return 0



# --------------------------------------------------------------------------
# scan -- does a capture that is ALREADY COMMITTED contain forbidden content
# --------------------------------------------------------------------------
#
# 🔴 THE THIRD CONTAINMENT SHAPE, and neither of the first two reaches it.
# `render`'s guard governs what may be PRINTED and where a rendering may be
# WRITTEN.  `flrbracket run`'s guard governs where a BRACKET's read-back and
# pre-read may land.  Both act at the moment a file is produced.  Nothing
# asked the other question: *is there forbidden content in a file this
# repository has already committed?*
#
# The incident that names it, 量 2026-08-31 (seating 8): `K-P3` is
# `DW 80A00000 2000` -- a 32 KiB read of RAM -- and it spans `0x80A00600` and
# `0x80A00700`, the two destinations the `H601` windows are read into.  Its
# output lands in `bench/`.  It was safe because `K-guard600`/`K-guard700`
# read `0/64` retained words, which is to say **because the experiment came
# out the expected way**.  `CLAUDE.md` already records that a containment rule
# whose correctness depends on an experiment's outcome is not a containment
# rule; this is that sentence with an instrument behind it.
#
# WHAT IT DOES AND DOES NOT DETECT, stated before it is used
# ----------------------------------------------------------
# It detects a contiguous run of **>= 16 bytes** of a `FORBIDDEN` region --
# any 16 bytes, at any offset, no alignment condition -- provided those 16
# bytes carry at least `SCAN_MIN_DISTINCT` distinct byte values.  Raw bytes
# and hexadecimal text both, through one matcher on two channels:
#
#   RAW  the file's own bytes -- a binary that should never have been
#        committed.
#   HEX  every maximal run of hexadecimal digits in the file, with any token
#        immediately followed by `:` DROPPED (that is a `DW` reply's address
#        column, and leaving it in would break the byte stream every 16
#        bytes), concatenated and decoded.  This is the channel that sees a
#        `DW` capture, and it does not care how the words are grouped.
#
# ⚠️ What it does NOT see, and each of these is a real gap:
#   * a run shorter than 16 bytes -- INCLUDING A BARE SIX-BYTE MAC.  That is
#     `tools/leakscan.py`'s shape: it knows the patterns an address takes and
#     this tool knows only *these bytes came from that window*.  The two are
#     complements and neither subsumes the other.
#   * a byte-swapped or little-endian rendering.  The loader prints
#     big-endian, which is the flash's own order, so the channel that matters
#     here is covered; a capture from some other instrument may not be.
#   * anything under a compression or an encoding that is not plain hex.
#   * a region not in `FORBIDDEN`.  `FORBIDDEN` is `H601` alone, deliberately:
#     the loader region's bytes are the vendor's code and are already
#     committed in `bench/2026-08-24d/G8a-rd0.log`.
#
# THE PROBE SET IS EVERY WINDOW, NOT EVERY SIXTEENTH, AND THAT IS AFFORDABLE
# FOR A MEASURED REASON.  The first version searched for the region's 16-byte
# windows at ALIGNED offsets, which buys a guarantee with a caveat in it (any
# run of >= 31 bytes contains a whole aligned window; a run of 16..30 may be
# missed).  量 2026-08-31: at a 16-byte window and a 4-distinct-value floor,
# taking EVERY offset costs **113 distinct needles**, which is FEWER than the
# 512 aligned ones -- because 98.22 % of `H601` is a single repeated byte
# value and the whole region holds only 40 distinct values at all.  So the
# caveat is dropped rather than documented.
#
# THE ENTROPY FILTER IS ON THE REFERENCE SIDE, not on the capture's.  A window
# of the region holding fewer than `SCAN_MIN_DISTINCT` distinct byte values is
# NOT searched for: finding sixteen identical bytes in a capture says nothing
# about this device, and a filter applied to the capture instead would be
# deciding what to report after seeing the match.  量 at a 16-byte window:
# >= 3 distinct gives 136 needles, >= 4 gives 113, >= 5 gives 93.  **4 is a
# choice, 推**, and the sweep below is what says it does not fire on the
# record as it stands.
SCAN_WINDOW = 16
SCAN_MIN_DISTINCT = 4

HEXRUN = re.compile(rb"[0-9A-Fa-f]+")


def hex_stream(text: bytes) -> bytes:
    """The capture's hexadecimal, decoded, with `DW` address columns dropped.

    A token is an address column when the character after it is `:`.  That is
    read off the one format this repository has: `%08X:` then tab-separated
    `%08X` words (`render_dw` above, and `docs/loader-command-semantics.md`).
    """
    out = bytearray()
    for m in HEXRUN.finditer(text):
        end = m.end()
        if end < len(text) and text[end:end + 1] == b":":
            continue
        tok = m.group(0)
        if len(tok) < 4 or len(tok) % 2:
            continue
        out += bytes.fromhex(tok.decode("ascii"))
    return bytes(out)


def scan_probes(dump: bytes, regions):
    """-> [(needle, flash_offset)] -- the aligned windows worth searching for.

    Refuses an empty result: a probe list that is empty makes every scan
    report CLEAN, which is this repository's "a tool reporting 0 is making a
    claim" in one line.
    """
    probes, seen = [], set()
    for lo, hi, _why in regions:
        for at in range(lo, hi - SCAN_WINDOW + 1):
            w = dump[at:at + SCAN_WINDOW]
            if (len(w) == SCAN_WINDOW and len(set(w)) >= SCAN_MIN_DISTINCT
                    and w not in seen):
                seen.add(w)
                probes.append((w, at))
    if not probes:
        _fail("no probe survived the entropy filter -- every window of every "
              "forbidden region is a repeated byte, or the dump is wrong. A "
              "scan with no probes reports CLEAN on everything")
    return probes


def scan_bytes(data: bytes, probes):
    """-> [(channel_offset, flash_offset, run_len)], never any content.

    Overlapping probe matches are merged into one interval, so a 256-byte
    copy is reported as ONE finding rather than as the ~113 overlapping
    needles that found it.  The flash offset kept is the lowest of the
    merged set, which is where the run starts in the region.
    """
    hits = []
    for needle, at in probes:
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            hits.append((i, at))
            start = i + 1
    if not hits:
        return []
    hits.sort()
    runs = []
    beg, end, flash = hits[0][0], hits[0][0] + SCAN_WINDOW, hits[0][1]
    for i, at in hits[1:]:
        if i <= end:                      # overlapping or touching
            end = max(end, i + SCAN_WINDOW)
            flash = min(flash, at)
        else:
            runs.append((beg, flash, end - beg))
            beg, end, flash = i, i + SCAN_WINDOW, at
    runs.append((beg, flash, end - beg))
    return runs


def scan_capture(blob: bytes, probes):
    """-> [(channel, channel_offset, flash_offset, run_len)]."""
    found = []
    for channel, data in (("raw", blob), ("hex", hex_stream(blob))):
        for off, at, n in scan_bytes(data, probes):
            found.append((channel, off, at, n))
    return found


def cmd_scan(args) -> int:
    with open(args.dump, "rb") as f:
        dump = f.read()
    probes = scan_probes(dump, FORBIDDEN)

    if args.sweep:
        # 🔴 `upstream/` IS NOT EXCLUDED BY DEFAULT, and the first version of
        # this walk excluded it.  量 2026-08-31, the run that made the point:
        # with it excluded the sweep of this whole repository was CLEAN, and
        # with it included there is one hit -- `upstream/BENCH-LOG.md`, sixteen
        # bytes of `H601` as a hexdump line, in a PUBLIC repository, which
        # neither `leakscan` nor `audit-bench-log` names (both look for the
        # text SHAPES an address takes, and a hexdump of flash has none).  A
        # default that hides the only finding the tool has ever made is not a
        # default.  `--exclude` is how a sweep declines a tree, so the decision
        # is on the command line where a reader can see it.  `.git` is skipped
        # because its objects are zlib-compressed and no verbatim run survives
        # in them; that is a cost argument, not a containment one.
        skip = set(args.exclude or ())
        paths = []
        for root, dirs, files in os.walk(args.sweep):
            dirs[:] = [d for d in dirs if d != ".git" and d not in skip]
            for name in sorted(files):
                paths.append(os.path.join(root, name))
        if not paths:
            _fail(f"--sweep {args.sweep} walked zero files -- a sweep of an "
                  f"empty population reports CLEAN and means nothing")
    else:
        if not args.file:
            _fail("scan needs a FILE or --sweep DIR")
        paths = [args.file]

    nhit = 0
    for p in paths:
        try:
            with open(p, "rb") as f:
                blob = f.read()
        except OSError as e:
            print(f"  SKIP  {p}  {e}")
            continue
        for channel, off, at, n in scan_capture(blob, probes):
            nhit += 1
            # The verdict carries WHERE, never WHAT: the flash offsets are
            # public (CLAUDE.md names the region) and the capture offset is a
            # position in a file the reader already has. No byte of the window
            # and no digest of it is printed -- see cmd_render on why a digest
            # over this window is a 2^24 search for the MAC.
            print(f"  \033[31mHIT\033[0m   {p}  {channel} channel, "
                  f"offset {off} .. {off + n - 1}, {n} byte(s) of flash "
                  f"0x{at:06X}")
    print(f"  {len(paths)} file(s) scanned, {len(probes)} distinct probe(s) "
          f"of {SCAN_WINDOW} bytes ({SCAN_MIN_DISTINCT}+ distinct values)")
    if nhit:
        print(f"  \033[31m{nhit} HIT(S)\033[0m -- a committed file holds "
              f"content from a region that may not be published")
        return 1
    print("  CLEAN")
    return 0

# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

REAL0 = "bench/2026-08-24d/G8a-rd0.log"
REAL6 = "bench/2026-08-24d/G8a-rd6.log"


def self_test() -> int:
    """The controls.

    🔴 Rewritten 2026-08-30 after an adversarial pass ran 45 mutants against
    the first version and **24 survived**. Three of the survivors printed this
    unit's MAC: one wrote the rendering to stdout on the refusal path, one
    printed the withheld digest on the line above the word "withheld", and one
    never opened the dump at all. The common cause was that the only cases
    driving ``cmd_render`` used a single argument triple and an all-zero dump,
    and that ``R1``/``R2`` called ``render_dw()`` in process, so everything
    between "open the file" and "format the words" had no control over it.

    What that means for the shape below: **every case that can leak drives the
    real command line as a subprocess and asserts on stdout**, and R1/R2 go
    through ``--out`` and ``cmp`` rather than through the library.
    """
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

    HEX64 = re.compile(r"\b[0-9a-f]{64}\b")

    print("flashwin self-test")
    print()

    # --- C1 one line, exact text ------------------------------------------
    data = bytes.fromhex("0BF0000400000000000000000000000000")[:16]
    got = render_dw(0x80A00000, data, "DW 80A00000 4")
    want = (b"DW 80A00000 4\n\r"
            b"80A00000:\t0BF00004\t00000000\t00000000\t00000000\n\r"
            b"<RealTek>")
    if got == want:
        good("C1 one line renders exactly, and the words are big-endian")
    else:
        bad(f"C1 rendered {got!r}")

    # --- C2 the 256-byte shape, against reply-size.py's own model ----------
    blob = bytes(range(256))
    got = render_dw(0x80A00000, blob, "DW 80A00000 64")
    if len(got) == 777 and got.count(b"\n\r") == 17:
        good("C2 256 bytes render to 777 bytes in 16 lines -- reply-size.py's number")
    else:
        bad(f"C2 rendered {len(got)} bytes, {got.count(chr(10).encode())} line ends")

    # --- C3 the address column is the RAM base, not the flash offset -------
    got = render_dw(0x80A00100, blob, "DW 80A00100 64")
    if b"80A00100:" in got and b"80A001F0:" in got and b"00006000:" not in got:
        good("C3 the address column counts from the RAM base and steps by 16")
    else:
        bad("C3 the address column is wrong")

    # --- C4 position sensitivity ------------------------------------------
    a = render_dw(0x80A00000, blob, "DW 80A00000 64").split(b"\n\r")
    mut = bytearray(blob)
    mut[0x37] ^= 0x01
    b = render_dw(0x80A00000, bytes(mut), "DW 80A00000 64").split(b"\n\r")
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if diff == [4]:
        good("C4 one flipped byte moves exactly one line, and it is the right one")
    else:
        bad(f"C4 a flip at 0x37 changed lines {diff}, wanted [4]")

    # --- C5 MUST FAIL: little-endian is a different rendering --------------
    le = [int.from_bytes(blob[k:k + 4], "little") for k in range(0, 16, 4)]
    letext = ("80A00000:" + "".join("\t%08X" % w for w in le)).encode()
    if letext in render_dw(0x80A00000, blob, "DW 80A00000 64"):
        bad("C5 a little-endian rendering matched -- C1 cannot tell the two apart")
    else:
        good("C5 a little-endian rendering does NOT match, so C1 is testing the order")

    root = _repo_root()
    here = os.path.abspath(__file__)

    with tempfile.TemporaryDirectory() as td:
        # A dump whose bytes are NOT all equal, so a case that renders the wrong
        # window renders visibly different text. The all-zero dump the first
        # version used is why seven wrong-window mutants survived.
        dump = os.path.join(td, "d.bin")
        with open(dump, "wb") as f:
            f.write(bytes((i * 7 + (i >> 8) * 13) & 0xFF for i in range(0x10000)))

        def run(*a):
            return subprocess.run([sys.executable, here, *a],
                                  capture_output=True, text=True)

        def refused(r, why, must_say=None):
            """A refusal is rc != 0, NOTHING on stdout, and a named reason.

            The stdout clause is the one that matters and the one the first
            version left out: a mutant that printed the rendering and then
            refused passed every check it had.
            """
            if r.returncode == 0:
                return f"rc=0 (expected a refusal) for {why}"
            if r.stdout:
                return f"{len(r.stdout)} byte(s) on STDOUT for {why}: {r.stdout[:40]!r}"
            if HEX64.search(r.stdout) or HEX64.search(r.stderr):
                return f"a 64-hex digest was printed for {why}"
            if must_say and must_say not in r.stderr:
                return f"stderr does not say {must_say!r} for {why}"
            return None

        # --- C6 forbidden, no --out -------------------------------------
        e = refused(run("render", "--dump", dump, "--at", "0x6000",
                        "--ram", "0x80A00200"),
                    "a forbidden window with no --out",
                    "identify one physical device")
        if e:
            bad(f"C6 {e}")
        else:
            good("C6 a forbidden window with no --out is refused, rc!=0, and stdout is EMPTY")

        # --- C7 forbidden, --out inside the repository ------------------
        inside = os.path.join(root, "flashwin-selftest-must-not-exist.txt")
        e = refused(run("render", "--dump", dump, "--at", "0x6000",
                        "--ram", "0x80A00200", "--out", inside),
                    "--out inside the repository", "is inside")
        stray = [p for p in (inside, inside + ".tmp") if os.path.exists(p)]
        for p in stray:
            os.unlink(p)
        if e:
            bad(f"C7 {e}")
        elif stray:
            bad(f"C7 left {stray} behind -- a .tmp sibling is still a file in the repo")
        else:
            good("C7 a forbidden window may not be written inside the repository, "
                 "and no .tmp sibling is left")

        # --- C7b a repo SUBDIRECTORY is inside the repository -----------
        sub = os.path.join(root, "bench", "flashwin-selftest-must-not-exist.txt")
        e = refused(run("render", "--dump", dump, "--at", "0x6000",
                        "--ram", "0x80A00200", "--out", sub),
                    "--out inside bench/", "is inside")
        stray = [p for p in (sub, sub + ".tmp") if os.path.exists(p)]
        for p in stray:
            os.unlink(p)
        if e or stray:
            bad(f"C7b {e or ('left ' + str(stray))} -- only the repo ROOT was guarded")
        else:
            good("C7b a repository SUBDIRECTORY is inside it too, not just the root")

        # --- C7c the guard resolves symlinks ----------------------------
        link = os.path.join(td, "linktorepo")
        linked_ok = True
        try:
            os.symlink(os.path.join(root, "bench"), link)
        except (OSError, NotImplementedError):
            linked_ok = False
        if not linked_ok:
            skips.append(("C7c symlinks", 1))
            print("  skip   symlinks unavailable on this filesystem                 "
                  "C7c needs os.symlink (1 case)")
        else:
            target = os.path.join(link, "flashwin-selftest-must-not-exist.txt")
            e = refused(run("render", "--dump", dump, "--at", "0x6000",
                            "--ram", "0x80A00200", "--out", target),
                        "--out through a symlink into the repository", "is inside")
            real = os.path.join(root, "bench", "flashwin-selftest-must-not-exist.txt")
            stray = [p for p in (real, real + ".tmp") if os.path.exists(p)]
            for p in stray:
                os.unlink(p)
            if e or stray:
                bad(f"C7c {e or ('left ' + str(stray))} -- the guard compares strings, "
                    "not resolved paths")
            else:
                good("C7c a symlink pointing into the repository is still inside it")

        # --- C8 forbidden, --out outside: allowed, and NO digest --------
        outside = os.path.join(td, "h601.txt")
        r = run("render", "--dump", dump, "--at", "0x6000", "--ram", "0x80A00200",
                "--out", outside)
        digest = HEX64.search(r.stdout) or HEX64.search(r.stderr)
        # The bytes, not the size. `dump` here is synthetic -- the self-test built
        # it -- so comparing the content leaks nothing and is the only thing that
        # can tell a correct write from a 777-byte file of zeros.
        with open(dump, "rb") as f:
            f.seek(0x6000)
            want_h = render_dw(0x80A00200, f.read(0x100), "DW 80A00200 64")
        got_h = open(outside, "rb").read() if os.path.exists(outside) else b""
        if r.returncode != 0:
            bad(f"C8 rc={r.returncode}")
        elif got_h != want_h:
            bad(f"C8 the file written is not the rendering of that window "
                f"({len(got_h)} bytes) -- a size check alone passes on a file of zeros")
        elif digest:
            bad("C8 a 64-hex digest was printed for a forbidden window -- with the "
                "rest of the window known that is a 2^24 search for the MAC")
        elif "sha256 withheld" not in r.stdout:
            bad("C8 the withholding is not stated")
        elif os.path.exists(outside + ".tmp"):
            bad("C8 left a .tmp sibling behind")
        else:
            good("C8 --out outside the repository is accepted, and NO digest is printed")

        # --- C8b the guard is not conditioned on --bytes or --ram -------
        e1 = refused(run("render", "--dump", dump, "--at", "0x6000", "--bytes", "0x10",
                         "--ram", "0x80A00200"), "a 16-byte forbidden window")
        e2 = refused(run("render", "--dump", dump, "--at", "0x6000", "--bytes", "0x100",
                         "--ram", "0x81000000"), "a forbidden window at another RAM base")
        # A STRADDLE, through the command line. Every other guard case starts on a
        # 4 KiB boundary, so a wiring mutant that rounds the address down before
        # testing it passes all of them -- and C9 tests the function, not the
        # wiring. This window starts BELOW the region and ends inside it.
        e3 = refused(run("render", "--dump", dump, "--at", "0x5F80", "--bytes", "0x100",
                         "--ram", "0x80A00200"), "a window straddling the lower bound")
        if e1 or e2 or e3:
            bad(f"C8b {e1 or e2 or e3} -- the guard is conditioned on an argument or "
                "sees a rounded address, and every other case here starts page-aligned")
        else:
            good("C8b the guard holds when --bytes and --ram change and on a straddle, "
                 "so C6-C8 are not testing one page-aligned triple")

        # --- C8c the region's LAST byte is inside it --------------------
        e = refused(run("render", "--dump", dump, "--at", "0x7FF0", "--bytes", "0x10",
                        "--ram", "0x80A00200"), "the region's last line")
        e2 = refused(run("render", "--dump", dump, "--at", "0x7FFF", "--bytes", "0x10",
                         "--ram", "0x80A00200"), "a window starting at hi-1")
        above = run("render", "--dump", dump, "--at", "0x8000", "--bytes", "0x10",
                    "--ram", "0x80A00200")
        if e or e2:
            bad(f"C8c {e or e2} -- the upper bound leaks")
        elif above.returncode != 0 or not above.stdout:
            bad("C8c the first window ABOVE the region was refused -- the bound is "
                "too wide and the case cannot tell a guard from a blanket refusal")
        else:
            good("C8c the region's last byte is guarded and the byte above it is not")

        # --- C8d the allowed path, end to end ---------------------------
        allowed = os.path.join(td, "allowed.txt")
        r = run("render", "--dump", dump, "--at", "0x1000", "--ram", "0x80A00000",
                "--out", allowed)
        with open(dump, "rb") as f:
            f.seek(0x1000)
            expect = render_dw(0x80A00000, f.read(0x100), "DW 80A00000 64")
        got = open(allowed, "rb").read() if os.path.exists(allowed) else b""
        m = HEX64.search(r.stdout)
        if r.returncode != 0:
            bad(f"C8d the allowed path exited {r.returncode}")
        elif got != expect:
            bad("C8d the file written is not the rendering of that window -- "
                "the dump/seek path has no other control")
        elif not m or m.group(0) != hashlib.sha256(expect).hexdigest():
            bad("C8d the digest printed for an allowed window is missing or wrong")
        else:
            good("C8d an allowed window is written correctly and its digest is printed")

        # --- C8e the refusals that are not about publication ------------
        r1 = run("render", "--dump", dump, "--at", "0x1000", "--bytes", "0x18",
                 "--ram", "0x80A00000")
        r2 = run("render", "--dump", dump, "--at", "0xFF00", "--bytes", "0x1000",
                 "--ram", "0x80A00000")
        # WHICH refusal, not just that one happened: `render_dw` has a `% 16` check
        # of its own that shadows `cmd_render`'s, so a case asserting only rc!=0
        # cannot tell the two apart and deleting the outer one is invisible.
        if r1.returncode == 0:
            bad("C8e --bytes 0x18 was accepted; a partial line renders silently")
        elif "not a multiple of 16" not in r1.stderr:
            bad(f"C8e --bytes 0x18 was refused for the wrong reason: {r1.stderr.strip()[:70]}")
        elif r2.returncode == 0:
            bad("C8e a window past the end of the dump was accepted; a short read "
                "renders a short window and the cmp at the bench then fails for "
                "the wrong reason")
        else:
            good("C8e a non-multiple-of-16 length and a short read are both refused")

        # --- C9 the overlap boundary, in BOTH directions ------------------
        clear = overlaps_forbidden(0x005F00, 0x100)      # ends exactly at 0x6000
        straddle = overlaps_forbidden(0x005F80, 0x100)   # last byte is inside
        last = overlaps_forbidden(0x007FFF, 0x1)         # the region's last byte
        touch_hi = overlaps_forbidden(0x008000, 0x100)   # starts exactly at hi
        if clear is None and straddle is not None and last is not None and touch_hi is None:
            good("C9 the overlap test is half-open at both ends, catches a straddle, "
                 "and includes the region's last byte")
        else:
            bad(f"C9 clear={clear} straddle={straddle} last={last} touch_hi={touch_hi}")

        # --- C10 MUST FAIL: the off-by-one mutants, both ends -------------
        def mutant_lo(at, n):
            for lo, hi, why in FORBIDDEN:
                if at < hi and at + n > lo + 1:
                    return (lo, hi, why)
            return None

        def mutant_hi(at, n):
            for lo, hi, why in FORBIDDEN:
                if at < hi - 1 and at + n > lo:
                    return (lo, hi, why)
            return None
        lo_caught = (mutant_lo(0x006000, 1) is None
                     and overlaps_forbidden(0x006000, 1) is not None)
        hi_caught = (mutant_hi(0x007FFF, 1) is None
                     and overlaps_forbidden(0x007FFF, 1) is not None)
        if lo_caught and hi_caught:
            good("C10 an off-by-one at either end misses a real byte, and C9 catches both")
        else:
            bad(f"C10 lo_caught={lo_caught} hi_caught={hi_caught} -- C9 is not "
                "testing that boundary")

        # --- N1-N5 `normalise`, and every one runs without the dump --------
        # The whole point of the subcommand is that the RAM address drops out,
        # so the controls are about equality ACROSS addresses and inequality
        # across windows. The committed capture is the fixture; no dump.
        cap0 = os.path.join(root, REAL0)
        cap6 = os.path.join(root, REAL6)
        if not (os.path.exists(cap0) and os.path.exists(cap6)):
            bad(f"N1-N5 {REAL0} or {REAL6} is missing -- that is a broken "
                "reference in this repository, not an allowed skip")
        else:
            raw0 = open(cap0, "rb").read()
            raw6 = open(cap6, "rb").read()
            n0 = normalise_dw(raw0)
            n6 = normalise_dw(raw6)
            words0 = n0.split(b"\n")[:-1]
            if len(words0) == 16 and all(len(w.split(b"\t")) == 4
                                         for w in words0):
                good(f"N1 `normalise` reduces {REAL0} to 16 lines of 4 words "
                     f"({len(n0)} bytes from {len(raw0)})")
            else:
                bad(f"N1 {len(words0)} line(s), not 16 lines of 4 words")

            # N2 -- THE case. Same flash bytes, a DIFFERENT RAM destination,
            # identical normalised output. Without this the next block cannot
            # move its destination, and without moving it there is no
            # pre-read control.
            data0 = b"".join(bytes.fromhex(w.decode())
                             for line in words0 for w in line.split(b"\t"))
            other = render_dw(0x80B50000, data0, "DW 80B50000 64")
            if normalise_dw(other) == n0:
                good("N2 the same window at RAM 0x80B50000 normalises "
                     "identically to the capture taken at 0x80A00000")
            else:
                bad("N2 the same window at a different RAM address does NOT "
                    "normalise equal -- the address is not being stripped")

            if n0 != n6:
                good("N3 two DIFFERENT windows do not normalise equal "
                     "(the control on N2)")
            else:
                bad("N3 0x000000 and 0x060000 normalise to the same bytes")

            if b":" not in n0 and b"80A00000" not in n0:
                good("N4 the normalised output carries no address field")
            else:
                bad("N4 an address survived normalisation")

            notdw = os.path.join(td, "notdw.txt")
            with open(notdw, "w", encoding="utf-8") as f:
                f.write("hello\n\rthere\n\r<RealTek>")
            r = run("normalise", notdw)
            why = refused(r, "a file that is not a DW reply", "not a DW reply")
            if why:
                bad(f"N5 {why}")
            else:
                good("N5 a file that is not a DW reply is refused, with the "
                     "reason and nothing on stdout")

            # 🔴 N6/N7/N8 exist because an adversarial pass over `normalise`
            # ran eight mutants against N1-N5 and THREE survived. (The pass
            # itself had to be rerun: the first attempt reported 8 of 8 killed,
            # every one "killed by C7b,C7c", and 量 the UNMUTATED file through
            # that same symlinked temp root was already 22/24 -- C7b/C7c resolve
            # the repository root with `realpath`, which a symlink farm sends
            # back to the real tree. Every kill was invalid.)
            badline = os.path.join(td, "badline.txt")
            with open(badline, "wb") as f:
                f.write(b"DW 80A00000 4\n\rnot a data line\n\r<RealTek>")
            r = run("normalise", badline)
            why = refused(r, "a valid echo with a malformed data line",
                          "not a DW data line")
            if why:
                bad(f"N6 {why}")
            else:
                good("N6 a valid DW echo with a malformed data line is refused "
                     "-- N5 only covers a missing echo")

            nodata = os.path.join(td, "nodata.txt")
            with open(nodata, "wb") as f:
                f.write(b"DW 80A00000 4\n\r<RealTek>")
            r = run("normalise", nodata)
            why = refused(r, "a DW reply with no data lines", "no data lines")
            if why:
                bad(f"N7 {why}")
            else:
                good("N7 a DW reply carrying no data at all is refused rather "
                     "than normalised to nothing")

            # N8 -- ORDER is part of the reading. Without this, a normaliser
            # that sorted the words would make two different windows with the
            # same multiset compare equal, and N3 could not see it because its
            # two windows differ in content as well as in order.
            swapped = bytearray(data0)
            swapped[0:4], swapped[4:8] = data0[4:8], data0[0:4]
            other2 = render_dw(0x80A00000, bytes(swapped), "DW 80A00000 64")
            if normalise_dw(other2) != n0:
                good("N8 swapping two words changes the normalised output, so "
                     "word order is part of the reading")
            else:
                bad("N8 a window with two words swapped normalises equal -- "
                    "order is being discarded")


        # ------------------------------------------------------------------
        # S1..S9 -- `scan`.  A capture that is ALREADY COMMITTED.
        # ------------------------------------------------------------------
        # 🔴 S4 and S6 are the reason S2 means anything.  A scanner whose
        # probe set is empty reports CLEAN on every input, exits 0, and looks
        # exactly like a scanner that works -- this repository's own "a tool
        # reporting 0 is making a claim", in the one place where a false CLEAN
        # is a published MAC.
        REG = [(0x100, 0x200, "synthetic forbidden region")]
        # A synthetic dump: 0x000-0x0FF and 0x200+ are one repeated byte, and
        # the "region" 0x100-0x1FF holds content.  Its second half is a single
        # repeated byte so that the entropy filter has something to reject
        # INSIDE the region, which is what S4 needs.
        sdump = bytearray(b"\xAA" * 0x400)
        content = bytes((i * 37 + 11) & 0xFF for i in range(0x80))
        sdump[0x100:0x180] = content
        sdump = bytes(sdump)
        sprobes = scan_probes(sdump, REG)

        n_expect = sum(
            1 for at in range(0x100, 0x200 - SCAN_WINDOW + 1)
            if len(set(sdump[at:at + SCAN_WINDOW])) >= SCAN_MIN_DISTINCT)
        if sprobes and len(sprobes) == n_expect and n_expect < 0x100:
            good(f"S1 the probe set is the region's windows that survive the "
                 f"entropy filter: {len(sprobes)} of {0x200 - 0x100 - SCAN_WINDOW + 1}")
        else:
            bad(f"S1 {len(sprobes)} probe(s), expected {n_expect}")

        # S2 POSITIVE -- exactly SCAN_WINDOW bytes of the region, buried in
        # filler that is NOT from the region.
        filler = bytes((i * 5 + 3) & 0xFF for i in range(64))
        cap = filler + sdump[0x110:0x110 + SCAN_WINDOW] + filler
        f2 = scan_capture(cap, sprobes)
        if (len(f2) == 1 and f2[0][0] == "raw" and f2[0][1] == 64
                and f2[0][2] == 0x110 and f2[0][3] == SCAN_WINDOW):
            good(f"S2 POSITIVE: {SCAN_WINDOW} bytes of the region are found, "
                 f"at the right capture offset and the right flash offset")
        else:
            bad(f"S2 {f2}")

        # S2b THE SAME WINDOW TWICE.  🔴 Not a hypothetical: `K-P3` is one
        # `DW` spanning BOTH `H601` RAM destinations, so the shape this
        # subcommand was written for is a capture holding the window more than
        # once.  量: a matcher that stopped at the first occurrence of each
        # needle survived every other case here.
        cap2 = (filler + sdump[0x110:0x110 + SCAN_WINDOW]
                + filler + sdump[0x110:0x110 + SCAN_WINDOW] + filler)
        f2b = scan_capture(cap2, sprobes)
        if len(f2b) == 2 and all(x[3] == SCAN_WINDOW for x in f2b):
            good("S2b the SAME window occurring twice is reported twice, not "
                 "once -- the shape K-P3 has")
        else:
            bad(f"S2b {len(f2b)} finding(s), wanted 2: {f2b}")

        # S3 NEGATIVE -- the same length of bytes from OUTSIDE the region.
        f3 = scan_capture(filler + sdump[0x000:0x000 + 64] + filler, sprobes)
        if not f3:
            good("S3 NEGATIVE: a capture of bytes from outside the region is "
                 "CLEAN, so S2 is not matching on length or on filler")
        else:
            bad(f"S3 {f3}")

        # S4 the entropy filter, and it is the control on S2.  The region's
        # own second half is one repeated byte; a capture of it must be CLEAN
        # even though those bytes ARE inside the forbidden region.
        f4 = scan_capture(filler + sdump[0x190:0x1A0] + filler, sprobes)
        if not f4:
            good("S4 a stretch of one repeated byte INSIDE the region is not "
                 "a hit -- the filter is on the reference side")
        else:
            bad(f"S4 a low-entropy window matched: {f4}")

        # S5 the HEX channel, and the address column.  The same 16 bytes
        # rendered as a `DW` reply must hit; a file whose only hexadecimal is
        # `DW` ADDRESS COLUMNS must not.
        dw = render_dw(0x80A00000, sdump[0x100:0x180], "DW 80A00000 32")
        f5 = scan_capture(dw, sprobes)
        addr_only = b"".join(b"%08X:\n\r" % (0x80A00000 + 16 * k)
                             for k in range(16))
        f5b = scan_capture(addr_only, sprobes)
        # 🔴 THE LENGTH IS THE ASSERTION, not the fact of a hit.  A `DW`
        # rendering of 128 contiguous region bytes must come back as ONE run
        # of 128.  If the address column were left in the hex stream, each
        # 16-byte line would still match on its own and the fact of a hit
        # would be unchanged -- eight runs of 16 instead of one of 128, and a
        # window straddling a line boundary lost entirely.  量: a mutation
        # deleting the address-column rule survived the weaker form.
        if (len(f5) == 1 and f5[0][0] == "hex" and f5[0][3] == 0x80
                and not f5b):
            good("S5 a `DW` rendering of 128 region bytes is ONE run of 128 "
                 "in the HEX channel, so the address column is out of the "
                 "stream; address columns alone are CLEAN")
        elif not f5:
            bad("S5 a `DW` rendering of the window was NOT found -- the hex "
                "channel or the address-column rule is wrong")
        else:
            bad(f"S5 hits={f5} (wanted one run of 128) address-only={f5b}")

        # S5b THE `xxd` SHAPE -- four-hex groups, not eight.  🔴 This is not
        # a hypothetical format: the only hit this subcommand has ever made on
        # real material is `upstream/BENCH-LOG.md` line 2557, which is exactly
        # this, and a `hex_stream` that only accepted eight-digit tokens would
        # have reported that file CLEAN.
        w = sdump[0x100:0x120]
        xxd = b"".join(
            b"%08x: " % (0x6000 + 16 * k)
            + b" ".join(b"%04x" % int.from_bytes(w[16 * k + 2 * j:
                                                   16 * k + 2 * j + 2], "big")
                        for j in range(8))
            + b"  ................\n"
            for k in range(2))
        f5c = scan_capture(xxd, sprobes)
        if f5c and all(c == "hex" for c, _, _, _ in f5c):
            good("S5b the HEX channel finds the window in an `xxd`-style dump "
                 "with FOUR-digit groups, which is the shape of the one real "
                 "finding this subcommand has made")
        else:
            bad(f"S5b an xxd-style rendering was not found: {f5c}")

        # S6 REFUSAL -- a region with no window above the floor must REFUSE,
        # not report CLEAN.  This is S1's failure mode as an exit code.
        flat = bytes(b"\xAA" * 0x400)
        # Through the library rather than the CLI: the CLI's region list is
        # `FORBIDDEN`, and this case is about an arbitrary region.
        try:
            scan_probes(flat, REG)
            bad("S6 a region with no window above the entropy floor did NOT "
                "refuse -- every scan would report CLEAN")
        except SystemExit:
            good("S6 a region with no window above the entropy floor REFUSES "
                 "rather than reporting CLEAN on everything")

        # S7 the verdict carries no bytes.  Through the command line, on a
        # file that HITS, asserting on stdout: no 64-hex digest, and none of
        # the region's own probe bytes in any of the three renderings a
        # careless implementation would use.
        hitfile = os.path.join(td, "hits.bin")
        dumpfile = os.path.join(td, "sdump.bin")
        # `FORBIDDEN` is H601, so S7 drives the REAL region offsets on a
        # SYNTHETIC dump: the same code path end to end, and nothing of this
        # device is on disk for the case to leak even if it fails.
        real = bytearray(b"\xAA" * 0x8000)
        real[0x6000:0x6080] = content
        with open(dumpfile, "wb") as f:
            f.write(bytes(real))
        with open(hitfile, "wb") as f:
            f.write(filler + bytes(real[0x6000:0x6080]) + filler)
        r7 = run("scan", hitfile, "--dump", dumpfile)
        leaked = []
        blob7 = bytes(real[0x6000:0x6010])
        for rendering in (blob7,
                          blob7.hex().encode(),
                          blob7.hex().upper().encode(),
                          b"".join(b"%02X " % b for b in blob7)):
            if rendering in r7.stdout.encode("utf-8", "replace"):
                leaked.append(rendering[:12])
        if r7.returncode != 1:
            bad(f"S7 a hitting file exited {r7.returncode}, wanted 1")
        elif "HIT" not in r7.stdout:
            bad("S7 no HIT was printed for a file that contains the window")
        elif leaked:
            bad(f"S7 the verdict PRINTED window bytes: {leaked}")
        elif HEX64.search(r7.stdout):
            bad("S7 a 64-hex digest was printed -- a digest over this window "
                "is a 2^24 search for the MAC")
        else:
            good("S7 a HIT prints where and how many, and no byte of the "
                 "window in any of four renderings, and no digest")

        # S8 the sweep's population control.
        emptydir = os.path.join(td, "emptysweep")
        os.makedirs(emptydir, exist_ok=True)
        e8 = refused(run("scan", "--sweep", emptydir, "--dump", dumpfile),
                     "a sweep of an empty directory", "walked zero files")
        if e8:
            bad(f"S8 {e8}")
        else:
            good("S8 a sweep that walks zero files REFUSES rather than "
                 "reporting CLEAN")

        # --- R1/R2/R3 the real material, THROUGH THE COMMAND LINE ---------
        work = os.environ.get("FWRE_WORK", "/home/key/fwre-work")
        d2p = os.path.join(work, "dumps", "flash-n150rt-console-2.bin")
        d1p = os.path.join(work, "dumps", "flash-n150rt-console-1.bin")
        cap0 = os.path.join(root, REAL0)
        cap6 = os.path.join(root, REAL6)
        have_dumps = os.path.exists(d1p) and os.path.exists(d2p)
        have_caps = os.path.exists(cap0) and os.path.exists(cap6)

        if not have_caps:
            # A DIFFERENT skip from the dumps one, because a renamed capture is a
            # defect in this repository and a missing dump is not.
            bad(f"R1-R2 {REAL0} or {REAL6} is missing from this repository -- "
                "that is not an allowed skip, it is a broken reference")
        elif not have_dumps:
            skips.append((SKIP_LABEL, 6))
            print("  skip   %-52s %s" % (
                SKIP_LABEL,
                "R1-R3 and S9a-S9c need "
                "$FWRE_WORK/dumps/flash-n150rt-console-{1,2}.bin -- "
                "4 MiB of this unit's own flash, which can never be committed "
                "(covers 6)"))
        else:
            with open(d1p, "rb") as f:
                d1 = f.read()
            with open(d2p, "rb") as f:
                d2 = f.read()
            if d1 == d2 and len(d1) == 4194304:
                good("R3 the two 2026-08-16 dumps are byte-identical over all "
                     "4,194,304 bytes")
            else:
                bad("R3 the two dumps differ, so 'the dump' is not one artefact")
            for label, real, flash, ram in (("R1", cap0, 0x000000, 0x80A00000),
                                            ("R2", cap6, 0x060000, 0x80A00100)):
                out = os.path.join(td, label + ".txt")
                r = run("render", "--dump", d2p, "--at", hex(flash),
                        "--ram", hex(ram), "--out", out)
                got = open(out, "rb").read() if os.path.exists(out) else b""
                want = open(real, "rb").read()
                if r.returncode != 0:
                    bad(f"{label} the CLI exited {r.returncode}")
                elif got != want:
                    bad(f"{label} does NOT reproduce {os.path.relpath(real, root)} "
                        f"({len(got)} bytes rendered, {len(want)} expected)")
                else:
                    good(f"{label} `render --at {flash:#08x}` reproduces "
                         f"{os.path.relpath(real, root)} byte for byte "
                         f"({len(want)} bytes), through the command line")

            # --- S9a/S9b/S9c -- `scan` on real material --------------------
            # 🔴 The positive control is the one that cannot be synthesised:
            # a rendering of the REAL H601 window, written outside the
            # repository, must HIT.  S9b is its negative (a region no rule
            # forbids) and S9c is the file the whole subcommand exists for.
            h601 = os.path.join(td, "s9-h601.txt")
            r = run("render", "--dump", d2p, "--at", "0x6000",
                    "--ram", "0x80A00200", "--out", h601)
            r9a = run("scan", h601, "--dump", d2p)
            if r.returncode != 0:
                bad(f"S9a the render for the control exited {r.returncode}")
            elif r9a.returncode != 1 or "HIT" not in r9a.stdout:
                bad("S9a a rendering of the REAL H601 window was NOT flagged "
                    "-- the scan reports CLEAN on the thing it exists for")
            else:
                good("S9a POSITIVE, real material: a rendering of the real "
                     "H601 window HITS")
            try:
                os.unlink(h601)
            except OSError:
                pass

            r9b = run("scan", os.path.join(root, REAL0), "--dump", d2p)
            if r9b.returncode == 0 and "CLEAN" in r9b.stdout:
                good(f"S9b NEGATIVE, real material: {REAL0} -- a committed "
                     f"capture of flash 0x000000 -- is CLEAN")
            else:
                bad(f"S9b {REAL0} was flagged (rc={r9b.returncode})")

            kp3 = os.path.join(root, "bench/2026-08-31c/K-P3.log")
            if not os.path.exists(kp3):
                bad("S9c bench/2026-08-31c/K-P3.log is missing -- that is a "
                    "broken reference, not an allowed skip")
            else:
                r9c = run("scan", kp3, "--dump", d2p)
                if r9c.returncode == 0 and "CLEAN" in r9c.stdout:
                    good("S9c the incident file -- K-P3, a 32 KiB DW spanning "
                         "both H601 destinations -- is CLEAN by machine")
                else:
                    bad(f"S9c K-P3 was flagged (rc={r9c.returncode})")

    # --- Q1 -- the label this suite PRINTS must be the one the table
    # allows.  It reads `tools/ci-expected.tsv` and so it runs on a bench
    # WITH the dump (where nothing else compares the label) and on a runner
    # without it.  That is the whole point: the configuration that can see
    # the drift is not the one the push happens from.
    tsv = os.path.join(_repo_root(), "tools", "ci-expected.tsv")
    want, found = None, False
    try:
        with open(tsv, encoding="utf-8") as fh:
            for line in fh:
                c = line.rstrip("\n").split("\t")
                if c and c[0] == "flashwin" and len(c) > 2 and c[2] != "-":
                    found, want = True, c[2]
    except OSError as e:
        want = f"<{e}>"
    if found and want == SKIP_LABEL:
        good(f"Q1 the printed skip label is the one ci-expected allows  "
             f"({SKIP_LABEL!r})")
    else:
        bad(f"Q1 this suite prints {SKIP_LABEL!r}; ci-expected.tsv says "
            f"{want!r} -- ci-census counts a skip only on an exact match, "
            f"and a bench with the dump never compares them")

    print()
    if skips:
        for lbl, n in skips:
            print(f"  (skipped: {lbl}, {n} case(s))")
    print(f"  {ok} passed, {fail} failed")
    return 0 if fail == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("render", help="render a DW reply for a flash window")
    r.add_argument("--dump", required=True, help="a full flash dump")
    r.add_argument("--at", required=True, type=lambda s: int(s, 0),
                   help="flash offset, e.g. 0x006000")
    r.add_argument("--ram", required=True, type=lambda s: int(s, 0),
                   help="the RAM address FLR will land it at, e.g. 0x80A00200")
    r.add_argument("--bytes", type=lambda s: int(s, 0), default=0x100,
                   help="window length, multiple of 16 (default 0x100)")
    r.add_argument("--out", default=None,
                   help="write here instead of stdout; REQUIRED, and required "
                        "to be outside this repository, for a window that "
                        "overlaps a forbidden region")
    r.set_defaults(func=cmd_render)

    sc = sub.add_parser("scan",
                        help="does an ALREADY COMMITTED capture contain "
                             "content from a forbidden flash region")
    sc.add_argument("file", nargs="?", help="a capture to scan")
    sc.add_argument("--dump", required=True,
                    help="the reference flash dump the regions are read from")
    sc.add_argument("--sweep", default=None,
                    help="walk this directory instead of scanning one file")
    sc.add_argument("--exclude", action="append", default=None,
                    metavar="NAME",
                    help="directory name to skip during --sweep; repeatable. "
                         "`.git` is always skipped (compressed objects). "
                         "Nothing else is, on purpose -- see cmd_scan")
    sc.set_defaults(func=cmd_scan)

    n = sub.add_parser("normalise",
                       help="strip a DW reply to its data, so two reads of "
                            "one flash window into DIFFERENT RAM addresses "
                            "compare equal")
    n.add_argument("file", help="a DW capture")
    n.add_argument("--out", default=None, help="write here instead of stdout")
    n.set_defaults(func=cmd_normalise)

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
