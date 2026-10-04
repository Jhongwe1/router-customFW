#!/usr/bin/env python3
"""Produce the `cr6c` image the stock loader must scan, and prove nothing else is.

`FW-168` is this file's whole reason.  量: `cvimg`'s `linux-ro` option writes
`cr6b`, `check_image()` accepts only `cs6c` and `cr6c`, and so rlxfw's own
`linux.bin` has never been an image the stock loader would boot.  That does not
touch `R8a`, which boots from RAM.  It decides `R8b`, where **one producer has to
guarantee two opposite properties, each with its own control**:

  (1) at flash `0x010000` (`rlxboot`) and `0x020000` (`rlxboot-rescue`) there
      MUST be a header `check_image()` accepts -- signature `cr6c`, and the
      16-bit big-endian sum of the `len` payload bytes zero -- because being
      scanned and jumped to by the stock loader is how those two run at all;

  (2) at every other 64 KiB-aligned offset the loader scans -- `0x030000`,
      `0x040000`, `0x050000`, `0x060000`, the erased barrier -- and in the slots
      it does not scan, there must be NO header any of the loader's ten
      signatures matches, because that path goes through neither the Ed25519
      check nor the anti-rollback counter (plan § D6, `notes/update-chain.md`
      § 5).

`wrap` is (1) and `scan` is the instrument for both.  Nothing restated: the two
`check_image()` signatures come from `mkfw2.CHECK_IMAGE_SIGS`, `burn()`'s eight
from `mkfw2.BURN_SIGS`, the 16-bit sum from `rtkimage.sum16`, the chip size and
the forbidden ranges from `flashguard`.  `K1` is what goes red if any of those
is ever copied in here instead.

WHY AN ERASED BARRIER IS SAFE AND NOT MERELY UNBOOTABLE
------------------------------------------------------
讀 `docs/loader-command-semantics.md` § "The signature test": `check_image()`
copies the 16-byte header, **then** `memcmp`s the signature (step 2), and only
**then** calls `flash_read(header.startAddr, offset+16, header.len)` (step 3).
The copy is downstream of the signature.  An erased NOR word reads `0xFFFFFFFF`,
which matches none of the ten, so an erased candidate is rejected before
`startAddr` and `len` are ever used -- had the order been the other way, a
barrier candidate would ask the loader to copy 4,294,967,295 bytes to
`0xFFFFFFFF`.  That ordering is what makes (2) a containment rule rather than a
hope, and it is read out of this unit's own code rather than assumed.

WHAT THIS FILE DOES NOT DO
--------------------------
It writes no flash and emits no loader command -- `K14` sweeps its own output for
the four verbs.  `wrap` writes one local file.  A declared destination is
REPORTED against `flashguard` and not gated on, because `flashguard` guards a
**write** and this is a file: today `flashguard` refuses `0x020000` outright (the
rescue slot's own row), so gating here would mean the rescue image could not be
produced at all.  The gate on a write is `mkfw2 build --flash-at`, and that
refusal is this tool's banner rather than its silence.

It also establishes nothing about whether the loader *will* boot what it makes.
`check_image()` is reproduced here from a reading of one unit's `stage2.bin`;
`bank_offset` has never been read for this build (plan § D5), and if it is not 0
the whole candidate table shifts and both properties move with it.

Exit
    0  produced / every candidate has the verdict the policy requires
    1  a candidate has the wrong verdict, or an input image is malformed
    2  a control failed (`--self-test`)
    3  usage / input refusal.  One line, a reason, never a traceback
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashguard   # noqa: E402  -- the forbidden ranges and the chip size
import mkfw2        # noqa: E402  -- the ten signatures and the RLXU verdict
import rlxsign      # noqa: E402  -- the development seed, for K6's fixture
from rtkimage import sum16   # noqa: E402  -- the 16-bit sum has one owner

VERSION = "mkcr6c 1.0"

# 讀 `SPEC.md` `FW-12`: `IMG_HEADER_T` is 16 bytes, big-endian --
# `signature[4]`, `startAddr`, `burnAddr`, `len` -- and the payload is the
# binary plus TWO bytes whose value makes `check_image()`'s 16-bit sum zero.
# `len` counts those two.  量 on two real images: the drop's own `linux.bin` is
# 854,034 = 16 + 854,016 + 2 with `len` 854,018, and this unit's flash
# `0x060000` is 987,154 = 16 + 987,136 + 2 with `len` 987,138 (`FLM-09`).
HDR_LEN = 16
TAIL_LEN = 2

# 讀 `docs/loader-command-semantics.md`: `rtk.h`'s `FW_SIGNATURE_WITH_ROOT`.
# `check_image()` returns 2 for it and `doBooting()` is satisfied by 2 alone,
# so `cs6c` is located and then rejected.  The PAIR is `mkfw2`'s to own; this
# is the one of the two that a producer may emit, and `K1` fails if `mkfw2`
# stops listing it.
CR6C = b"cr6c"

# The loader's scan, derived the way the loader derives it rather than written
# out as six numbers.  讀 `docs/loader-command-semantics.md` § a: three fixed
# probes at `0x80408084`, then a sweep from `0x030000` to `0x060000` at stride
# `0x010000` that skips the three already tried.  `K1` checks the derivation
# against the six-offset line in that document, which is the second source.
FIXED_PROBES = (0x010000, 0x020000, 0x030000)
SWEEP_START, SWEEP_END, SWEEP_STEP = 0x030000, 0x060000, 0x010000

# The policy, and it is the two properties as address sets.  讀 `FW-167` /
# `notes/update-chain.md` § 6 for why the barrier is four candidates wide: at
# the obvious slot base `0x030000` four of the six candidates fall INSIDE slot
# A, so the lowest usable slot base is `0x070000` and `0x030000`-`0x06FFFF` is
# left erased.  `K11` requires these two sets to partition the candidates, so
# a candidate cannot be dropped from the policy by being left out of both.
MUST_BOOT = (0x010000, 0x020000)                      # rlxboot, rlxboot-rescue
MUST_NOT_BOOT = (0x030000, 0x040000, 0x050000, 0x060000)   # the erased barrier

# One 64 KiB loader step.  An image that overran its region would put bytes at
# the next candidate, and the barrier's claim is about what is THERE.
REGION_BYTES = 0x010000
ERASED = 0xFF

# The document that owns the candidate table, for `K1`'s second source.
_HERE = os.path.dirname(os.path.abspath(__file__))
SEMANTICS_DOC = os.path.join(os.path.dirname(_HERE), "docs",
                             "loader-command-semantics.md")


def die(msg, code=3):
    """The house refusal: one line, a reason, no traceback."""
    print("mkcr6c: %s" % msg, file=sys.stderr)
    raise SystemExit(code)


# --------------------------------------------------------------------------
# the loader's scan table
# --------------------------------------------------------------------------
def scan_candidates():
    """-> the six 64 KiB-aligned offsets `check_image()` is called on, in the
    order the loader tries them: the three fixed probes, then the sweep with
    the three skipped.  Derived, not listed."""
    out = list(FIXED_PROBES)
    i = SWEEP_START
    while i <= SWEEP_END:
        if i not in FIXED_PROBES:
            out.append(i)
        i += SWEEP_STEP
    return tuple(out)


def candidates_from_doc():
    """-> the same six, parsed out of the document that owns them, or None.

    The second source for `K1`.  `docs/loader-command-semantics.md` § a prints
    the candidate set as one line of six hex offsets; if that line moves or
    changes, this returns something else and `K1` goes red rather than this
    file's derivation drifting away from the reading it came from.
    """
    try:
        with open(SEMANTICS_DOC, "r", encoding="utf-8") as fh:
            for ln in fh:
                parts = ln.split()
                if len(parts) != 6:
                    continue
                if all(p.startswith("0x") and len(p) == 8 for p in parts):
                    try:
                        return tuple(int(p, 16) for p in parts)
                    except ValueError:
                        continue
    except OSError:
        return None
    return None


# --------------------------------------------------------------------------
# check_image(), as a predicate rather than a report
# --------------------------------------------------------------------------
def check_image_ret(blob, off=0):
    """-> (ret, s16, detail).  What `check_image()` returns for a header at
    `blob[off]`, and the 16-bit sum it would then require to be zero.

    `off` exists so a 4 MiB chip map is read in place: slicing it once per
    candidate would copy megabytes to answer a question about sixteen bytes.

    `ret` is 0 (no signature matched), 1 (`cs6c`) or 2 (`cr6c`).  `s16` is None
    when `ret` is 0, because the copy is step 3 and the signature is step 2 --
    a candidate that fails the signature is never summed.  It is also None when
    `len` asks for more bytes than are there, which is UNDETERMINED behaviour
    rather than a zero: nothing in this project has read what the loader does
    with an over-long `len`, so this reports it instead of deciding it.

    BOOTABLE IS NARROWER THAN RECOGNISED, and that is the point `K16` makes:
    `mkfw2.stock_loader_verdict` answers *does the loader read a header it
    knows*, which is the right question for property (2).  `doBooting()` boots
    only on ret == 2 with a zero sum, which is the right question for (1).
    """
    if len(blob) - off < HDR_LEN:
        return 0, None, "fewer than %d bytes to read a header" % HDR_LEN
    sig = bytes(blob[off:off + 4])
    if sig == b"cs6c":
        ret = 1
    elif sig == CR6C:
        ret = 2
    else:
        return 0, None, "signature %r is neither 'cs6c' nor 'cr6c'" % sig
    start, flashoff, length = struct.unpack_from(
        ">3I", bytes(blob[off:off + HDR_LEN]), 4)
    body = bytes(blob[off + HDR_LEN:off + HDR_LEN + length])
    if len(body) != length:
        return ret, None, ("startAddr 0x%08X flashOff 0x%08X len %d -- only %d "
                           "bytes follow the header, so the sum is UNDETERMINED"
                           % (start, flashoff, length, len(body)))
    return ret, sum16(body), ("startAddr 0x%08X flashOff 0x%08X len %d"
                              % (start, flashoff, length))


def bootable(blob, off=0):
    """-> True when `doBooting()` would boot this header.  ret 2 AND sum 0."""
    ret, s16, _ = check_image_ret(blob, off)
    return ret == 2 and s16 == 0


# --------------------------------------------------------------------------
# property (1): the producer
# --------------------------------------------------------------------------
def build_image(binary, start_addr, flash_at):
    """-> the bytes that go at `flash_at`: a `cr6c` header, the binary, and the
    two bytes that make the sum zero.

    An ODD-length binary is refused rather than padded.  `rtkimage.sum16` pads
    one zero byte so that it has one behaviour, but `check_image()` sums the RAM
    copy as halfwords over `len` bytes -- an odd `len` makes the last halfword a
    read this project has not characterised, and both real images are even.
    """
    if len(binary) == 0:
        raise ValueError("an empty binary has nothing to boot")
    if len(binary) % 2:
        raise ValueError(
            "the binary is %d bytes, which is odd: check_image() sums the RAM "
            "copy as 16-bit halfwords over `len` bytes and an odd `len` makes "
            "the last halfword a read nothing here has characterised.  Both "
            "real cr6c images are even (FW-12)" % len(binary))
    for name, v in (("--start-addr", start_addr), ("--flash-at", flash_at)):
        if not 0 <= v <= 0xFFFFFFFF:
            raise ValueError("%s 0x%X does not fit the 32-bit header field"
                             % (name, v))
    tail = struct.pack(">H", (-sum16(binary)) & 0xFFFF)
    payload = binary + tail
    header = CR6C + struct.pack(">3I", start_addr, flash_at, len(payload))
    if len(header) != HDR_LEN:
        raise ValueError("header packed to %d bytes, not %d"
                         % (len(header), HDR_LEN))
    return header + payload


def gate_image(img, flash_at, region_bytes=REGION_BYTES):
    """Raise unless `img` satisfies property (1) at `flash_at`.  -> [lines].

    A producer that can emit an image the loader will not boot is a producer
    that will, so this runs between `build_image` and the write and the write
    does not happen without it.  Four conditions, and each is a separate
    refusal because they fail for different reasons:

      * the destination is one of the two regions that MUST boot.  A `cr6c`
        header anywhere else is property (2)'s hazard made by hand -- at a
        barrier candidate it boots an unsigned image, and off the table it is
        a header for nobody that still has to be argued about later;
      * `check_image()` returns 2, not 0 and not 1;
      * the sum over the `len` payload bytes is zero;
      * header + payload fits one 64 KiB region, so no byte of it lands on the
        next candidate and the barrier's erased claim still describes it.
    """
    lines = []
    if flash_at not in MUST_BOOT:
        why = ("a barrier candidate, which MUST NOT carry one (FW-167)"
               if flash_at in MUST_NOT_BOOT else
               "not on the loader's scan table at all, so a header there is "
               "never read and only creates FW-168's second hazard")
        raise ValueError(
            "refusing to emit a cr6c header for 0x%06X: %s.  The two "
            "destinations that must carry one are %s"
            % (flash_at, why, " ".join("0x%06X" % a for a in MUST_BOOT)))
    if len(img) > region_bytes:
        raise ValueError(
            "the image is %d bytes and one loader region is %d: %d bytes would "
            "land at 0x%06X, the next scan candidate, and the barrier's claim "
            "is about what is THERE (FW-167)"
            % (len(img), region_bytes, len(img) - region_bytes,
               flash_at + region_bytes))
    ret, s16, detail = check_image_ret(img)
    if ret != 2:
        raise ValueError("refusing to emit an image check_image() returns %d "
                         "for: %s.  Only 2 satisfies doBooting()" % (ret, detail))
    if s16 != 0:
        raise ValueError("refusing to emit an image whose 16-bit sum is 0x%04X; "
                         "check_image() requires 0 (C-4, LDR-18)" % s16)
    lines.append("  check_image()      returns 2, sum16 0x%04X -- BOOTABLE" % s16)
    # The second source over the same bytes, and it is not this code.
    recognised, rl = mkfw2.stock_loader_verdict(bytes(img))
    if not recognised:
        raise ValueError("mkfw2.stock_loader_verdict does not recognise an "
                         "image this file calls bootable; one of the two is "
                         "wrong and it is not for this tool to decide which")
    lines.append("  mkfw2 verdict      RECOGNISED (%s)" % rl[0].split(": ")[-1])
    return lines


def cmd_wrap(args):
    if not os.path.isfile(args.inp):
        die("no such binary: %s" % args.inp)
    with open(args.inp, "rb") as fh:
        binary = fh.read()
    try:
        img = build_image(binary, args.start_addr, args.flash_at)
        lines = gate_image(img, args.flash_at, args.region_bytes)
    except ValueError as exc:
        die(str(exc), code=1)
    # Never open(path,'w') before the content exists.
    tmp = args.out + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(img)
    os.replace(tmp, args.out)
    print("%s -- wrap" % VERSION)
    print("  binary             %s" % args.inp)
    print("  binary bytes       %d" % len(binary))
    print("  image              %s" % args.out)
    print("  image bytes        %d  (%d header + %d binary + %d sum tail)"
          % (len(img), HDR_LEN, len(binary), TAIL_LEN))
    print("  signature          %s" % CR6C.decode())
    print("  startAddr          0x%08X   where the loader copies it and jumps"
          % args.start_addr)
    print("  flashOff           0x%06X" % args.flash_at)
    print("  len                %d  (binary + the %d sum bytes)"
          % (len(binary) + TAIL_LEN, TAIL_LEN))
    for ln in lines:
        print(ln)
    print("  region             0x%06X-0x%06X, %d of %d bytes used"
          % (args.flash_at, args.flash_at + args.region_bytes - 1,
             len(img), args.region_bytes))
    # REPORTED, not gated.  See the module docstring: flashguard guards a write.
    r = flashguard.check(args.flash_at, len(img))
    print("  flashguard         %s" % ("PERMITTED" if r is None
                                       else "REFUSED -- %s" % r))
    if r is not None:
        print("  -> so this image cannot be published through `mkfw2 build "
              "--flash-at 0x%06X` today.  Nothing here writes flash; the "
              "refusal is on a destination, and it is the right default until "
              "the owner rules otherwise." % args.flash_at)
    return 0


# --------------------------------------------------------------------------
# property (2) and property (1) together: the scan
# --------------------------------------------------------------------------
def place(chip_bytes, placements):
    """-> a bytearray of an erased chip with each file stamped at its offset.

    Erased is 0xFF, which is what a NOR word reads before it is programmed, and
    it is the whole reason the barrier is provably unbootable: 0xFFFFFFFF is
    none of the loader's ten signatures.
    """
    m = bytearray([ERASED]) * chip_bytes
    taken = []
    for off, path, blob in placements:
        end = off + len(blob)
        if end > chip_bytes:
            die("0x%06X+0x%X (%s) ends at 0x%06X, past the %d-byte chip"
                % (off, len(blob), path, end, chip_bytes), code=1)
        for o2, p2, b2 in taken:
            if off < o2 + len(b2) and end > o2:
                die("0x%06X+0x%X (%s) overlaps 0x%06X+0x%X (%s); a map whose "
                    "placements overlap does not describe a chip"
                    % (off, len(blob), path, o2, len(b2), p2), code=1)
        m[off:end] = blob
        taken.append((off, path, blob))
    return m


def cmd_scan(args):
    placements = []
    for spec in args.place or []:
        if "=" not in spec:
            die("--place takes OFFSET=FILE, got %r" % spec)
        off_s, path = spec.split("=", 1)
        try:
            off = int(off_s, 0)
        except ValueError:
            die("--place offset %r is not a number" % off_s)
        if not os.path.isfile(path):
            die("--place 0x%06X: no such file: %s" % (off, path))
        with open(path, "rb") as fh:
            placements.append((off, path, fh.read()))
    m = place(args.chip_bytes, placements)
    cands = scan_candidates()

    print("%s -- scan" % VERSION)
    print("  chip               %d bytes, erased 0x%02X" % (args.chip_bytes,
                                                            ERASED))
    print("  placements         %d" % len(placements))
    for off, path, blob in placements:
        g = flashguard.check(off, len(blob))
        print("    0x%06X+0x%-8X %-34s flashguard %s"
              % (off, len(blob), os.path.basename(path),
                 "PERMITTED" if g is None else "REFUSED (%s)" % g.rid))
    print("")
    print("  the loader's scan, in the order it tries them "
          "(%d candidates, derived):" % len(cands))
    print("    %-10s %-9s %-7s %-8s %s"
          % ("candidate", "policy", "ret", "sum16", "verdict"))

    bad = []
    for c in cands:
        ret, s16, detail = check_image_ret(m, c)
        boots = ret == 2 and s16 == 0
        must = c in MUST_BOOT
        ok = boots == must
        if not ok:
            bad.append((c, must, boots, detail))
        print("    0x%06X   %-9s %-7s %-8s %s"
              % (c, "MUST" if must else "must-not", ret,
                 "-" if s16 is None else "0x%04X" % s16,
                 ("%s  %s" % ("BOOTS" if boots else "no", "ok" if ok
                              else "*** WRONG ***"))))
        print("                 %s" % detail)

    outside = [(o, p, b) for o, p, b in placements if o not in cands]
    if outside:
        print("")
        print("  placements OUTSIDE the scan table -- the slots.  FW-168's "
              "other half: a slot must deliberately carry no header the loader")
        print("  knows, because the scan does not go through rlxboot and so "
              "goes through neither the signature nor the counter.")
        for off, path, blob in outside:
            recognised, rl = mkfw2.stock_loader_verdict(bytes(blob[:HDR_LEN]))
            if recognised:
                bad.append((off, False, True,
                            "a placement outside the scan table that the "
                            "loader still recognises"))
            print("    0x%06X   %-34s %s" % (off, os.path.basename(path),
                                             "*** RECOGNISED ***" if recognised
                                             else "not recognised"))
            print("                 %s" % rl[0].strip())

    print("")
    if bad:
        for c, must, boots, detail in bad:
            print("  WRONG  0x%06X  policy %s, measured %s -- %s"
                  % (c, "MUST BOOT" if must else "MUST NOT BOOT",
                     "BOOTS" if boots else "does not boot", detail),
                  file=sys.stderr)
        print("mkcr6c: %d of %d candidates has the wrong verdict"
              % (len(bad), len(cands) + len(outside)), file=sys.stderr)
        return 1
    print("  %d candidates and %d slot placements all have the verdict the "
          "policy requires" % (len(cands), len(outside)))
    return 0


# --------------------------------------------------------------------------
# the controls
# --------------------------------------------------------------------------
def _fixture_binary(n=4096, fill=b"\xA5"):
    """A deterministic binary of even length.  Not a payload; the properties
    this file checks are properties of a header and a sum, and a fixture whose
    bytes were random would make `K2`'s sum unreproducible."""
    return (fill * n)[:n]


def self_test():
    rows = []

    def add(cid, what, ok, detail=""):
        rows.append((cid, what, bool(ok), detail))

    # ------------------------------------------- K1  nothing is restated here
    doc = candidates_from_doc()
    derived = scan_candidates()
    add("K1", "the 2 check_image() signatures, burn()'s 8, the chip size and "
        "the 6 candidates all come from their owners",
        CR6C in mkfw2.CHECK_IMAGE_SIGS and b"cs6c" in mkfw2.CHECK_IMAGE_SIGS
        and len(mkfw2.BURN_SIGS) == 8
        and flashguard.CHIP_SIZE == 0x00400000
        and doc is not None and tuple(sorted(doc)) == tuple(sorted(derived)),
        "doc %s, derived %s"
        % ("-" if doc is None else " ".join("0x%06X" % a for a in doc),
           " ".join("0x%06X" % a for a in derived)))
    add("K11", "MUST_BOOT and MUST_NOT_BOOT PARTITION the candidates -- a "
        "candidate cannot be dropped by being left out of both",
        set(MUST_BOOT) | set(MUST_NOT_BOOT) == set(derived)
        and not (set(MUST_BOOT) & set(MUST_NOT_BOOT))
        and len(MUST_BOOT) + len(MUST_NOT_BOOT) == len(derived),
        "%d + %d = %d" % (len(MUST_BOOT), len(MUST_NOT_BOOT), len(derived)))

    # ====================== property (1): a cr6c header where it MUST be =====
    good = build_image(_fixture_binary(), 0x81800000, 0x020000)
    ret, s16, _ = check_image_ret(good)
    add("K2", "GREEN ARM of property 1: the emitted image returns 2 with a "
        "ZERO sum, so doBooting() boots it",
        ret == 2 and s16 == 0 and bootable(good),
        "ret %d, sum16 0x%04X, %d bytes" % (ret, s16 or 0, len(good)))

    # 🔴 THE RED ARM, and the fixture is FW-168's own defect: the signature
    # rlxfw's pipeline really writes.  One byte of the four.
    cr6b = bytearray(good)
    cr6b[3:4] = b"b"          # 'cr6c' -> 'cr6b', the fourth byte, FW-168's own
    ret_b, s16_b, det_b = check_image_ret(bytes(cr6b))
    rec_b, _ = mkfw2.stock_loader_verdict(bytes(cr6b))
    add("K3", "RED ARM of property 1, fixture `cr6b`: FW-168's own byte makes "
        "it ret 0, never summed, and mkfw2 agrees it is not recognised",
        ret_b == 0 and s16_b is None and not bootable(bytes(cr6b))
        and not rec_b, det_b)

    # 🔴 The SECOND red arm, and it fails for the other of the two independent
    # conditions `rtkimage.py` fails a container on: the signature is right and
    # the sum is not.  A control that only ever breaks the signature would not
    # show the sum being checked at all.
    nosum = CR6C + struct.pack(">3I", 0x81800000, 0x020000, 4096) \
        + _fixture_binary()
    ret_n, s16_n, det_n = check_image_ret(nosum)
    add("K4", "RED ARM 2 of property 1, fixture with the 2 sum bytes dropped: "
        "ret is 2 and the sum is NOT zero, so it does not boot",
        ret_n == 2 and s16_n not in (None, 0) and not bootable(nosum),
        det_n + " sum16 0x%04X" % (s16_n or 0))

    # The producer's own gate, shown refusing AND permitting.
    gate = []
    try:
        gate_image(good, 0x020000)
        g_good = "permitted"
    except ValueError as exc:
        g_good = "REFUSED: %s" % str(exc)[:50]
        gate.append("the good image was refused")
    for label, blob in (("cr6b", bytes(cr6b)), ("no-sum", nosum)):
        try:
            gate_image(blob, 0x020000)
            gate.append("%s was permitted" % label)
        except ValueError:
            pass
    add("K5", "the producer's gate PERMITS the good image and REFUSES both "
        "fixtures -- a gate shown both ways",
        not gate, "; ".join(gate) or "1 %s, 2 refused" % g_good)

    add("K16", "`cs6c` with a zero sum is RECOGNISED and still does NOT boot: "
        "only ret 2 satisfies doBooting()",
        (lambda b: check_image_ret(b)[0] == 1 and not bootable(b)
         and mkfw2.stock_loader_verdict(b)[0])(
            b"cs6c" + good[4:]),
        "ret 1, and mkfw2 calls it recognised -- bootable is narrower")

    # ====================== property (2): no recognisable header elsewhere ====
    erased16 = bytes([ERASED]) * HDR_LEN
    rec_e, el = mkfw2.stock_loader_verdict(erased16)
    add("K9", "GREEN ARM of property 2: an erased region (0xFFFFFFFF) matches "
        "none of the loader's 10 signatures",
        not rec_e and not bootable(erased16),
        el[0].split("-- ")[-1][:52])
    # 🔴 and the control on that negative, because a function that said "not
    # recognised" about everything would pass K9 and mean nothing.  mkfw2's own
    # C15, re-run here over THIS file's bytes.
    rec_c, _ = mkfw2.stock_loader_verdict(bytes(good[:HDR_LEN]))
    rec_bn, _ = mkfw2.stock_loader_verdict(b"boot" + bytes(12))
    add("K10", "RED ARM of property 2's instrument: the same function DOES "
        "recognise this file's cr6c header and a `boot` section",
        rec_c and rec_bn, "cr6c %s, boot %s" % (rec_c, rec_bn))

    # The region bound, both ways, on the exact boundary.
    exact = build_image(_fixture_binary(REGION_BYTES - HDR_LEN - TAIL_LEN),
                        0x81800000, 0x020000)
    over = build_image(_fixture_binary(REGION_BYTES - HDR_LEN - TAIL_LEN + 2),
                       0x81800000, 0x020000)
    rb = []
    try:
        gate_image(exact, 0x020000)
    except ValueError as exc:
        rb.append("the exactly-fitting image was refused: %s" % str(exc)[:40])
    try:
        gate_image(over, 0x020000)
        rb.append("an image 2 bytes too long was permitted")
    except ValueError:
        pass
    add("K12", "the region bound both ways: %d bytes exactly FITS and %d is "
        "REFUSED, so no byte reaches the next candidate"
        % (len(exact), len(over)), not rb,
        "; ".join(rb) or "0x%06X is one loader step" % REGION_BYTES)

    # The destination rule, both ways.
    dest = []
    for at in MUST_BOOT:
        try:
            gate_image(build_image(_fixture_binary(), 0x81800000, at), at)
        except ValueError as exc:
            dest.append("0x%06X refused: %s" % (at, str(exc)[:38]))
    for at in tuple(MUST_NOT_BOOT) + (0x070000, 0x190000):
        try:
            gate_image(build_image(_fixture_binary(), 0x81800000, at), at)
            dest.append("0x%06X permitted" % at)
        except ValueError:
            pass
    add("K13", "a cr6c header is produced for the 2 MUST destinations and "
        "REFUSED for the 4 barrier candidates and both slot bases",
        not dest, "; ".join(dest) or "2 permitted, 6 refused")

    add("K14", "an odd-length binary is REFUSED rather than padded",
        _raises(lambda: build_image(b"\x00" * 4097, 0x81800000, 0x020000))
        and not _raises(lambda: build_image(b"\x00" * 4096, 0x81800000,
                                            0x020000)),
        "sum16 pads, check_image() does not -- and 4096 is still accepted")

    # ---------------------------------------- K6-K8  the scan, both arms
    # 🔄 2026-10-04: `flash_at` and `flash_form` became REQUIRED when the
    # container went to format 2 (`R8b` item 3).  They are NOT `FLASH_NONE`
    # here: the `intended` layout below places this container at 0x070000
    # and calls it an RLXU slot, and a slot lands WHOLE -- which is the
    # distinction the form field exists to carry.
    slot = mkfw2.build(_fixture_binary(1024), 1, 0x80500000, 0x80500000,
                       b"\xde\xad\xbe\xef", rlxsign.DEV_SEED,
                       0x070000, mkfw2.FORM_WHOLE)
    rlxboot_img = build_image(_fixture_binary(2048), 0x81800000, 0x010000)
    rescue_img = build_image(_fixture_binary(2048), 0x81800000, 0x020000)

    def _scan_rc(pl):
        """-> the offsets whose verdict disagrees with the policy.  This is the
        same arithmetic `cmd_scan` prints, so a red arm here is a non-zero exit
        there; the printing is what is left out."""
        m = place(flashguard.CHIP_SIZE, pl)
        cs = scan_candidates()
        rc_bad = [c for c in cs if bootable(m, c) != (c in MUST_BOOT)]
        rc_bad += [off for off, _p, blob in pl
                   if off not in cs
                   and mkfw2.stock_loader_verdict(bytes(blob[:HDR_LEN]))[0]]
        return rc_bad

    intended = [(0x010000, "rlxboot", rlxboot_img),
                (0x020000, "rescue", rescue_img),
                (0x070000, "slotA.rlxu", slot)]
    add("K6", "GREEN ARM of the scan: the intended layout -- rlxboot, rescue, "
        "an erased barrier and an RLXU slot -- gets every verdict right",
        _scan_rc(intended) == [], "0 wrong of 6 candidates + 1 slot")

    # 🔴 RED ARM ONE: the obvious layout FW-167 rejects.  A cr6c image at
    # 0x030000 is a barrier candidate that boots, which is the unsigned path.
    at30 = build_image(_fixture_binary(2048), 0x81800000, 0x010000)
    add("K7", "RED ARM of the scan: a cr6c image also stamped at 0x030000 -- a "
        "barrier candidate that boots -- is caught",
        _scan_rc(intended + [(0x030000, "stray", at30)]) == [0x030000],
        "0x030000 MUST NOT boot and does")

    # 🔴 RED ARM TWO: FW-168's other half.  A slot whose first four bytes the
    # loader knows is a slot bootable without rlxboot.
    badslot = CR6C + bytes(slot[4:])
    add("K8", "RED ARM 2 of the scan: a SLOT whose first 4 bytes read cr6c is "
        "caught although 0x070000 is not scanned",
        _scan_rc([(0x010000, "rlxboot", rlxboot_img),
                  (0x020000, "rescue", rescue_img),
                  (0x070000, "slotA", badslot)]) == [0x070000],
        "FW-168: the slot must deliberately carry no header")

    # 🔴 RED ARM THREE: property (1) at scan level.  The rescue ABSENT.
    add("K15", "RED ARM 3: with 0x020000 left erased the MUST arm fires -- a "
        "scan that only ever checks the must-nots is half a check",
        _scan_rc([(0x010000, "rlxboot", rlxboot_img),
                  (0x070000, "slotA.rlxu", slot)]) == [0x020000],
        "0x020000 MUST boot and does not")

    # ---------------------------------------- K17  no flash verb is emitted
    # 🔴 The verbs are built from their letters, not written: a case that says
    # the words is a case that plants them.  `flashguard`'s F17 is the precedent
    # and `test-mkfw2.sh` X1 is what caught it there.
    verbs = ["".join(c) for c in (("F", "L", "W"), ("E", "W"), ("E", "B"),
                                  ("A", "U", "T", "O", "B", "U", "R", "N"))]
    src = open(os.path.abspath(__file__), "rb").read().decode("utf-8")
    printing = "".join(ln for ln in src.splitlines() if "print(" in ln)
    emitted = [v for v in verbs if v in printing]
    add("K17", "this file prints none of the 4 flash-write verbs",
        not emitted, "%d verbs checked, %d found" % (len(verbs), len(emitted)))

    print("%s -- self-test" % VERSION)
    ok = fail = 0
    for cid, what, good_, detail in rows:
        if good_:
            ok += 1
            print("  ok     %-4s %-70s %s" % (cid, what, detail))
        else:
            fail += 1
            print("  FAIL   %-4s %-70s %s" % (cid, what, detail))
    print("  %d passed, %d failed" % (ok, fail))
    return 2 if fail else 0


def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="mkcr6c.py", description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    w = sub.add_parser("wrap", help="make the cr6c image for a MUST-boot region")
    w.add_argument("--in", dest="inp", required=True,
                   help="the raw payload binary, even length")
    w.add_argument("--out", required=True)
    w.add_argument("--start-addr", required=True, type=lambda s: int(s, 0),
                   help="where the loader copies the payload and jumps")
    w.add_argument("--flash-at", required=True, type=lambda s: int(s, 0),
                   help="the flash offset, one of %s"
                        % " ".join("0x%06X" % a for a in MUST_BOOT))
    w.add_argument("--region-bytes", type=lambda s: int(s, 0),
                   default=REGION_BYTES,
                   help="one loader step; the image may not exceed it")
    w.set_defaults(func=cmd_wrap)

    s = sub.add_parser("scan", help="every scan candidate's check_image() verdict")
    s.add_argument("--place", action="append", metavar="OFFSET=FILE",
                   help="stamp FILE at OFFSET; repeatable.  Everything else "
                        "is erased")
    s.add_argument("--chip-bytes", type=lambda s_: int(s_, 0),
                   default=flashguard.CHIP_SIZE)
    s.set_defaults(func=cmd_scan)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        die("no subcommand.  `wrap` makes the image, `scan` checks a layout")
    return args.func(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        die("interrupted")
    except (ValueError, OSError, struct.error) as exc:
        die("%s" % exc)
