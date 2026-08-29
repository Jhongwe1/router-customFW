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
            skips.append(("this unit's flash dump", 3))
            print("  skip   %-52s %s" % (
                "this unit's flash dump",
                "R1-R3 need $FWRE_WORK/dumps/flash-n150rt-console-{1,2}.bin -- "
                "4 MiB of this unit's own flash, which can never be committed "
                "(covers 3)"))
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

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
