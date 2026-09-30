#!/usr/bin/env python3
"""Build and verify an `RLXU` update container -- the host side of gate `R8a`.

`SPEC-R8a.md` § 2 pins the format; this file is its only producer, and `verify`
is a second implementation of the check `src/rlxboot/container.c` makes on the
device.  Two implementations of one rule is the point: the target's verifier is
C on a big-endian Lexra core with no libc, this one is Python on a host, and a
container that one accepts and the other rejects is a finding in whichever is
wrong.

The container (all integers big-endian; header 96 B, signature 64 B, payload)
-----------------------------------------------------------------------------
    0   4  magic 'RLXU'          28  32  payload SHA-256
    4   2  format = 1            60   4  recipe id (what RLXFW-ID0 prints)
    6   2  header_len = 96       64  32  reserved, ALL ZERO
    8   4  version 1..0xFFFFFFFE 96  64  Ed25519 over bytes 0..95
   12   4  payload_len <= 3 MiB 160   n  payload
   16   4  load_addr
   20   4  entry_addr            (must lie inside the payload's span)
   24   4  flags -- 0 in R8a; any unknown bit set -> reject

Verification order, and it is part of the format because it bounds what a
hostile container can do before it is trusted:

   1  magic, format, header_len
   2  the field bounds -- including that load_addr and load_addr+payload_len
      lie in RAM and that the destination overlaps neither `rlxboot` itself
      nor the container's own staging buffer
   3  the Ed25519 signature over the 96 header bytes
   4  only then the payload's SHA-256, over payload_len bytes
   5  the version against the anti-rollback counter

**Nothing is copied anywhere before step 4 passes**, and `verify` reports the
steps in that order so a capture of the target's output and a run of this tool
can be read side by side.

Three refusals `build` makes that are not about the format
---------------------------------------------------------
* **A destination inside a forbidden flash range.**  `tools/flashguard.py` owns
  the ranges and this file imports it; plan precondition ③ is exactly this,
  with the positive control that a permitted range really is permitted.
* **An output named `nfjrom` or `boot.img`.**  讀 `docs/loader-command-semantics.md`
  § b: those two names are matched in the loader's TFTP path and arm an
  auto-execute -- `nfjrom` at whatever load address is already set, `boot.img`
  at `0x80000000`.  A file with either name **takes the human out of the loop**,
  so nothing this tool writes may carry one.  The refusal is on the name, and it
  is why `R0` was told never to use either.
* **Anything the stock loader would accept as an image.**  Plan § D6: the loader
  scans six 64 KiB candidates and boots the first that passes `check_image()`,
  and that path does not go through `rlxboot`, so it does not go through the
  signature check or the anti-rollback counter.  If a slot image carried a
  header the loader recognised, corrupting one byte of `0x010000` would make
  the loader boot an old slot directly -- a rollback with no signal.  So `build`
  runs the desk reproduction of `check_image()` over what it just produced and
  refuses if it is recognised.

Nothing here writes flash.  This file emits no loader command at all, and
`tools/test-mkfw2.sh` `X1`-`X3` assert that `FLW`, `EW`, `EB` and a non-zero
`AUTOBURN` appear in none of these tools' output.

Exit
    0  built / verified
    1  the container is malformed, or a comparison the caller asked for failed
    2  a control failed (`--self-test`) -- nothing is reported
    3  usage / input refusal.  One line, a reason, never a traceback
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashguard  # noqa: E402  -- the forbidden ranges have one owner
import rlxsign     # noqa: E402  -- and the signature one implementation

VERSION = "mkfw2 1.0"

MAGIC = 0x524C5855            # 'RLXU'
FORMAT = 1
HEADER_LEN = 96
SIG_LEN = 64
BODY = HEADER_LEN + SIG_LEN   # 160, where the payload starts
MAX_PAYLOAD = 0x00300000      # 3 MiB, SPEC-R8a 2
VERSION_MIN, VERSION_MAX = 1, 0xFFFFFFFE
KNOWN_FLAGS = 0x00000000      # R8a: bit 0 is RESERVED for LZMA and unset

# SPEC-R8a § 4's memory map.  RAM is 32 MiB at 0x80000000 (量, `MEM-*`).
RAM_LO, RAM_HI = 0x80000000, 0x82000000
RLXBOOT_LO, RLXBOOT_HI = 0x81800000, 0x81900000   # rlxboot's own 1 MiB window
STAGE_LO = 0x81000000                             # where the loader TFTPs it

# 讀 `docs/loader-command-semantics.md` § b.  These two file names are matched
# in the loader's TFTP path and arm an auto-execute with nobody at the console.
AUTOEXEC_NAMES = ("nfjrom", "boot.img")

# 讀 `docs/loader-flash-write.md` § 1 and `docs/loader-command-semantics.md`
# § "the signature test".  `check_image()` takes 'cs6c' (returns 1) and 'cr6c'
# (returns 2, the only one the caller accepts); `burn()` matches these eight
# section signatures.  A container must be NONE of them at offset 0.
CHECK_IMAGE_SIGS = (b"cs6c", b"cr6c")
BURN_SIGS = (b"boot", b"sqsh", b"w6cp", b"jw6c", b"cwmp", b"ksap",
             b"ALL1", b"ALL2")


def die(msg, code=3):
    """The house refusal: one line, a reason, no traceback."""
    print("mkfw2: %s" % msg, file=sys.stderr)
    raise SystemExit(code)


# --------------------------------------------------------------------------
# the format
# --------------------------------------------------------------------------
def pack_header(version, payload_len, load_addr, entry_addr, flags,
                digest, recipe_id):
    """The 96 header bytes.  `struct` with '>' is the only endian statement."""
    if len(digest) != 32:
        raise ValueError("a SHA-256 digest is 32 bytes, not %d" % len(digest))
    if len(recipe_id) != 4:
        raise ValueError("a recipe id is 4 bytes, not %d" % len(recipe_id))
    h = struct.pack(">IHHIIIII32s4s", MAGIC, FORMAT, HEADER_LEN, version,
                    payload_len, load_addr, entry_addr, flags, digest,
                    recipe_id)
    h += b"\x00" * 32                         # reserved, bytes 64..95
    if len(h) != HEADER_LEN:
        raise ValueError("header packed to %d bytes, not %d"
                         % (len(h), HEADER_LEN))
    return h


def unpack_header(h):
    """The 96 header bytes -> a dict.  No validation; `checks()` does that."""
    (magic, fmt, hlen, version, plen, load, entry, flags, digest,
     recipe) = struct.unpack_from(">IHHIIIII32s4s", h, 0)
    return {"magic": magic, "format": fmt, "header_len": hlen,
            "version": version, "payload_len": plen, "load_addr": load,
            "entry_addr": entry, "flags": flags, "digest": digest,
            "recipe_id": recipe, "reserved": h[64:96]}


def checks(blob, pubkey, counter=0):
    """-> [(step, name, ok, detail)] in SPEC-R8a 2's order, stopping at the
    first failure.

    It STOPS rather than reporting every step, because the order is the
    specification: a tool that hashes a 3 MiB payload named by an unsigned
    header has already done work an attacker chose, and a tool that reports
    "digest ok, signature bad" has told the attacker the digest matched.
    """
    out = []

    def step(n, name, ok, detail=""):
        out.append((n, name, bool(ok), detail))
        return bool(ok)

    # ---- step 1: magic, format, header_len
    if len(blob) < BODY:
        step(1, "length", False,
             "%d bytes is shorter than the %d-byte header+signature"
             % (len(blob), BODY))
        return out
    h = blob[:HEADER_LEN]
    f = unpack_header(h)
    if not step(1, "magic", f["magic"] == MAGIC,
                "0x%08X, want 0x%08X (RLXU)" % (f["magic"], MAGIC)):
        return out
    if not step(1, "format", f["format"] == FORMAT,
                "%d, want %d" % (f["format"], FORMAT)):
        return out
    if not step(1, "header_len", f["header_len"] == HEADER_LEN,
                "%d, want %d" % (f["header_len"], HEADER_LEN)):
        return out

    # ---- step 2: the field bounds
    if not step(2, "reserved", f["reserved"] == b"\x00" * 32,
                "%d non-zero byte(s)" % sum(1 for b in f["reserved"] if b)):
        return out
    if not step(2, "flags", (f["flags"] & ~KNOWN_FLAGS) == 0,
                "0x%08X; unknown bits 0x%08X"
                % (f["flags"], f["flags"] & ~KNOWN_FLAGS)):
        return out
    if not step(2, "version", VERSION_MIN <= f["version"] <= VERSION_MAX,
                "%d, want %d..%d" % (f["version"], VERSION_MIN, VERSION_MAX)):
        return out
    plen = f["payload_len"]
    if not step(2, "payload_len", 0 < plen <= MAX_PAYLOAD,
                "%d, want 1..%d" % (plen, MAX_PAYLOAD)):
        return out
    if not step(2, "container_len", len(blob) == BODY + plen,
                "%d bytes, want %d (%d + payload_len %d)"
                % (len(blob), BODY + plen, BODY, plen)):
        return out
    load, end = f["load_addr"], f["load_addr"] + plen
    if not step(2, "load_addr_in_ram", RAM_LO <= load and end <= RAM_HI,
                "0x%08X-0x%08X, RAM is 0x%08X-0x%08X"
                % (load, end - 1, RAM_LO, RAM_HI - 1)):
        return out
    if not step(2, "no_overlap_rlxboot",
                not (load < RLXBOOT_HI and end > RLXBOOT_LO),
                "0x%08X-0x%08X vs rlxboot 0x%08X-0x%08X"
                % (load, end - 1, RLXBOOT_LO, RLXBOOT_HI - 1)):
        return out
    stage_end = STAGE_LO + len(blob)
    if not step(2, "no_overlap_container",
                not (load < stage_end and end > STAGE_LO),
                "0x%08X-0x%08X vs the staged container 0x%08X-0x%08X"
                % (load, end - 1, STAGE_LO, stage_end - 1)):
        return out
    if not step(2, "entry_in_payload", load <= f["entry_addr"] < end,
                "0x%08X, want 0x%08X..0x%08X"
                % (f["entry_addr"], load, end - 1)):
        return out

    # ---- step 3: the signature over the 96 header bytes, and nothing else
    sig = blob[HEADER_LEN:BODY]
    if not step(3, "signature", rlxsign.verify(pubkey, h, sig),
                "Ed25519 over bytes 0..95, key %s" % pubkey.hex()[:16]):
        return out

    # ---- step 4: only now is the payload touched
    got = hashlib.sha256(blob[BODY:BODY + plen]).digest()
    if not step(4, "payload_digest", got == f["digest"],
                "%s, header says %s" % (got.hex()[:16],
                                        f["digest"].hex()[:16])):
        return out

    # ---- step 5: anti-rollback
    step(5, "version_vs_counter", f["version"] >= counter,
         "version %d, counter %d (>= passes; SPEC-R8a 4 is a unary bitmap "
         "and today's region is erased, so the counter reads 0)"
         % (f["version"], counter))
    return out


# --------------------------------------------------------------------------
# the stock loader must NOT recognise this
# --------------------------------------------------------------------------
def stock_loader_verdict(blob):
    """-> (recognised, [lines]).  The desk reproduction of `check_image()`.

    讀 `docs/loader-command-semantics.md` § "The signature test": the loader
    copies a 16-byte header out of the flash window, `memcmp`s the signature
    against 'cs6c' then 'cr6c' -- built as immediates, not stored as strings --
    returns 1 or 2, reads `header.len` bytes into `header.startAddr`, and
    requires the 16-bit big-endian sum of the RAM copy to be zero.  Only the
    return value 2 satisfies the caller, so 'cs6c' is located and then rejected.

    `burn()`'s eight section signatures are checked too, because `AUTOBURN` and
    a section header are the *other* way the loader acts on a file.

    `tools/rtkimage.py` owns `sum16` and this function imports it rather than
    writing the sum again; if that import ever fails the caller must treat it as
    a control failure, not as "not recognised".
    """
    from rtkimage import sum16
    lines = []
    sig = blob[:4]
    hit = None
    for s in CHECK_IMAGE_SIGS:
        if sig == s:
            hit = s
    lines.append("  check_image() signature at 0x00: %r -- %s"
                 % (sig, "MATCHES %r" % hit if hit else
                    "not 'cs6c' and not 'cr6c'"))
    burn_hit = sig if sig in BURN_SIGS else None
    lines.append("  burn() section signature at 0x00: %r -- %s"
                 % (sig, "MATCHES" if burn_hit else
                    "none of " + " ".join(s.decode() for s in BURN_SIGS)))
    if hit is None and burn_hit is None:
        lines.append("  -> the loader reads no header it recognises here, so "
                     "it neither boots nor burns this file")
        return False, lines
    # It matched a signature; report the rest of check_image()'s rule so the
    # verdict is not "recognised" on the signature alone.
    start, flashoff, length = struct.unpack_from(">3I", blob, 4)
    s16 = sum16(blob[16:16 + length]) if len(blob) >= 16 + length else None
    lines.append("  startAddr 0x%08X  flash_offset 0x%08X  len %d"
                 % (start, flashoff, length))
    lines.append("  sum16 over the RAM copy: %s (check_image() requires 0)"
                 % ("0x%04X" % s16 if s16 is not None else "short read"))
    lines.append("  -> RECOGNISED as %r. THIS IS THE DEFECT plan D6 names: a "
                 "path that boots without rlxboot." % (hit or burn_hit))
    return True, lines


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def guard_output_name(path):
    """Refuse an output the loader would auto-execute.  Basename, any case."""
    base = os.path.basename(path)
    for bad in AUTOEXEC_NAMES:
        if base.lower() == bad:
            die("refusing to write %r: the loader's TFTP path matches that "
                "name and arms an AUTO-EXECUTE with nobody at the console "
                "(docs/loader-command-semantics.md b).  Pick any other name; "
                "the container's contents are not what is being refused"
                % base)


def guard_destination(flash_at, nbytes):
    """Refuse a forbidden flash destination.  flashguard owns the ranges."""
    if flash_at is None:
        return
    try:
        r = flashguard.check(flash_at, nbytes)
    except ValueError as exc:
        die("--flash-at: %s" % exc)
    if r is not None:
        die("refusing to build for flash destination 0x%06X+0x%X: it overlaps "
            "%s" % (flash_at, nbytes, r), code=3)


def build(payload, version, load_addr, entry_addr, recipe_id, seed,
          flags=0):
    """-> the container bytes.  Every § 2 field, and it refuses to emit a
    container its own `verify` would reject: a builder that can produce a
    malformation is a builder that will."""
    digest = hashlib.sha256(payload).digest()
    header = pack_header(version, len(payload), load_addr, entry_addr, flags,
                         digest, recipe_id)
    blob = header + rlxsign.sign(seed, header) + payload
    pub = rlxsign.secret_to_public(seed)
    bad = [(n, name, d) for n, name, ok, d in checks(blob, pub) if not ok]
    if bad:
        n, name, d = bad[0]
        raise ValueError("refusing to emit a container my own verify rejects: "
                         "step %d %s -- %s" % (n, name, d))
    recognised, _ = stock_loader_verdict(blob)
    if recognised:
        raise ValueError("refusing to emit a container the stock loader would "
                         "recognise as an image (plan D6): one corrupted byte "
                         "elsewhere could then boot it without rlxboot")
    return blob


def parse_recipe(s):
    t = s.strip().lower().replace("0x", "")
    try:
        b = bytes.fromhex(t)
    except ValueError:
        die("--recipe-id is not hex: %r" % s)
    if len(b) != 4:
        die("--recipe-id decodes to %d bytes; it is the 4 bytes whose hex "
            "RLXFW-ID0 prints" % len(b))
    return b


def cmd_build(args):
    if not os.path.isfile(args.payload):
        die("no such payload: %s" % args.payload)
    guard_output_name(args.out)
    payload = open(args.payload, "rb").read()
    if not payload:
        die("%s is empty; a container with no payload has nothing to verify"
            % args.payload)
    if len(payload) > MAX_PAYLOAD:
        die("payload is %d bytes and SPEC-R8a 2 caps payload_len at %d"
            % (len(payload), MAX_PAYLOAD))
    guard_destination(args.flash_at, BODY + len(payload))
    recipe = parse_recipe(args.recipe_id)
    seed = rlxsign.read_seed(vars(args))
    try:
        blob = build(payload, args.version, args.load_addr, args.entry_addr,
                     recipe, seed, args.flags)
    except ValueError as exc:
        die(str(exc), code=1)
    # Never open(path,'w') before the content exists.
    tmp = args.out + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(blob)
    os.replace(tmp, args.out)
    pub = rlxsign.secret_to_public(seed)
    print("%s -- build" % VERSION)
    print("  payload            %s" % args.payload)
    print("  payload bytes      %d" % len(payload))
    print("  payload sha256     %s" % hashlib.sha256(payload).hexdigest())
    print("  version            %d" % args.version)
    print("  load_addr          0x%08X" % args.load_addr)
    print("  entry_addr         0x%08X" % args.entry_addr)
    print("  flags              0x%08X" % args.flags)
    print("  recipe id          %s" % recipe.hex())
    print("  public key         %s" % pub.hex())
    print("  container          %s" % args.out)
    print("  container bytes    %d  (%d header + %d signature + %d payload)"
          % (len(blob), HEADER_LEN, SIG_LEN, len(payload)))
    print("  container sha256   %s" % hashlib.sha256(blob).hexdigest())
    if args.flash_at is not None:
        print("  flash destination  0x%06X+0x%X -- PERMITTED by flashguard"
              % (args.flash_at, len(blob)))
    print("  stock loader       does NOT recognise it (run `verify "
          "--stock-loader` for the proof)")
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------
def cmd_verify(args):
    if not os.path.isfile(args.container):
        die("no such container: %s" % args.container)
    blob = open(args.container, "rb").read()
    if args.pubkey_hex:
        try:
            pub = bytes.fromhex(args.pubkey_hex.strip())
        except ValueError:
            die("--pubkey-hex is not hex")
        if len(pub) != 32:
            die("a public key is 32 bytes, not %d" % len(pub))
    else:
        pub = rlxsign.secret_to_public(rlxsign.read_seed(vars(args)))
    print("%s -- verify" % VERSION)
    print("  container          %s  (%d bytes)" % (args.container, len(blob)))
    print("  public key         %s" % pub.hex())
    print("  counter            %d" % args.counter)
    rows = checks(blob, pub, args.counter)
    bad = 0
    for n, name, ok, detail in rows:
        print("  %-6s step %d %-22s %s" % ("ok" if ok else "REJECT", n, name,
                                           detail))
        if not ok:
            bad += 1
    if bad:
        print("  REJECTED at step %d (%s).  Nothing was copied anywhere."
              % (rows[-1][0], rows[-1][1]))
    else:
        f = unpack_header(blob[:HEADER_LEN])
        print("  ACCEPTED: %d-byte payload -> 0x%08X, entry 0x%08X, "
              "version %d, recipe %s"
              % (f["payload_len"], f["load_addr"], f["entry_addr"],
                 f["version"], f["recipe_id"].hex()))
    if args.stock_loader:
        recognised, lines = stock_loader_verdict(blob)
        print("")
        print("  the STOCK loader, over the same bytes "
              "(docs/loader-command-semantics.md 'The signature test'):")
        for ln in lines:
            print(ln)
        print("  stock loader verdict: %s"
              % ("RECOGNISED -- plan D6's defect" if recognised
                 else "NOT AN IMAGE"))
        if recognised:
            bad += 1
    return 1 if bad else 0


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
DEV = rlxsign.DEV_SEED
_GOOD = dict(version=7, load_addr=0x80500000, entry_addr=0x80500000,
             recipe_id=bytes.fromhex("3685a3a4"))


def _sample(n=4096):
    return bytes((i * 13 + 5) & 0xFF for i in range(n))


def _good_container(payload=None, **kw):
    a = dict(_GOOD)
    a.update(kw)
    return build(payload if payload is not None else _sample(), seed=DEV, **a)


def _first_bad(blob, counter=0):
    pub = rlxsign.secret_to_public(DEV)
    for n, name, ok, _ in checks(blob, pub, counter):
        if not ok:
            return "%d/%s" % (n, name)
    return None


def self_test():
    rows = []

    def add(cid, what, ok, detail=""):
        rows.append((cid, what, bool(ok), detail))

    pub = rlxsign.secret_to_public(DEV)

    # ---------------------------------------------- C1-C3  the positive one
    good = _good_container()
    add("C1", "a container built here VERIFIES", _first_bad(good) is None,
        "%d bytes" % len(good))
    f = unpack_header(good[:HEADER_LEN])
    add("C2", "every field is big-endian and reads back what it was given",
        (f["magic"] == MAGIC and f["format"] == 1 and f["header_len"] == 96
         and f["version"] == 7 and f["payload_len"] == 4096
         and f["load_addr"] == 0x80500000 and f["entry_addr"] == 0x80500000
         and f["flags"] == 0 and f["recipe_id"].hex() == "3685a3a4"
         and f["reserved"] == b"\x00" * 32
         and good[:4] == b"RLXU"),
        "magic bytes %r at offset 0" % good[:4])
    add("C3", "the signature covers the 96 header bytes and nothing else",
        rlxsign.verify(pub, good[:96], good[96:160])
        and not rlxsign.verify(pub, good[:95], good[96:160]),
        "verified over 0..95; the same signature over 0..94 does not verify")

    # ---------------------------------------------- C4  every field rejected
    # 🔴 The bit-flip sweep is the control that a verifier which returns True
    # is not green.  Every single-bit flip in the 96-byte header and the
    # 64-byte signature must be rejected: 160 x 8 = 1,280 flips.
    flips = rejected = 0
    for i in range(160):
        for b in range(8):
            bad = bytearray(good)
            bad[i] ^= 1 << b
            flips += 1
            if _first_bad(bytes(bad)) is not None:
                rejected += 1
    add("C4", "every single-bit flip in the header or signature is REJECTED",
        rejected == flips and flips == 1280, "%d/%d flips" % (rejected, flips))

    # A sample of payload flips -- the digest is what must catch these.
    pf = pr = 0
    for i in (0, 1, 7, 1000, 2047, 4095):
        for b in (0, 3, 7):
            bad = bytearray(good)
            bad[BODY + i] ^= 1 << b
            pf += 1
            if _first_bad(bytes(bad)) == "4/payload_digest":
                pr += 1
    add("C5", "a flipped PAYLOAD bit is rejected at step 4, the digest",
        pr == pf, "%d/%d flips, all at 4/payload_digest" % (pr, pf))

    # 🔴 C5b exists because C5 cannot catch a PREFIX comparison.  If step 4
    # compared only the digest's first byte, C5's 18 flips would still be
    # rejected about 93 % of the time -- the mutant would survive on luck, and
    # a control that depends on luck is not a control.  So: search for a
    # payload whose SHA-256 shares its FIRST BYTE with the original and differs
    # after it, and require that to be rejected.  `test-mkfw2.sh` M3 is the
    # one-byte mutant, and this is what makes it go red every time.
    base = _sample()
    want = hashlib.sha256(base).digest()
    collide = None
    for i in range(len(base)):
        for v in range(256):
            if v == base[i]:
                continue
            cand = bytearray(base)
            cand[i] = v
            d = hashlib.sha256(bytes(cand)).digest()
            if d[0] == want[0] and d != want:
                collide = bytes(cand)
                break
        if collide is not None:
            break
    if collide is None:
        add("C5b", "a payload whose digest shares only its FIRST BYTE is "
            "rejected", False, "no first-byte collision found in 4096x255 "
                               "candidates -- the search, not the tool, failed")
    else:
        forged = good[:BODY] + collide          # header and signature intact
        add("C5b", "a payload whose digest shares only its FIRST BYTE is "
            "rejected", _first_bad(forged) == "4/payload_digest",
            "digest %s vs %s -- same first byte, %s"
            % (hashlib.sha256(collide).hexdigest()[:8], want.hex()[:8],
               _first_bad(forged)))

    # ---------------------------------------------- C6  named-field bounds
    named = [
        ("magic", 0, ">I", MAGIC ^ 1, "1/magic"),
        ("format", 4, ">H", 2, "1/format"),
        ("header_len", 6, ">H", 64, "1/header_len"),
        ("version 0", 8, ">I", 0, "2/version"),
        ("version 0xFFFFFFFF", 8, ">I", 0xFFFFFFFF, "2/version"),
        ("payload_len 0", 12, ">I", 0, "2/payload_len"),
        ("payload_len over 3 MiB", 12, ">I", MAX_PAYLOAD + 1, "2/payload_len"),
        ("load_addr below RAM", 16, ">I", 0x7FFFF000, "2/load_addr_in_ram"),
        ("load_addr past RAM", 16, ">I", 0x81FFFF00, "2/load_addr_in_ram"),
        ("load_addr onto rlxboot", 16, ">I", 0x81800000,
         "2/no_overlap_rlxboot"),
        ("load_addr onto the staged container", 16, ">I", 0x81000000,
         "2/no_overlap_container"),
        ("flags unknown bit", 24, ">I", 0x00000002, "2/flags"),
        ("entry below the payload", 20, ">I", 0x804FFFFC, "2/entry_in_payload"),
        ("entry past the payload", 20, ">I", 0x80501000, "2/entry_in_payload"),
    ]
    miss = []
    for name, off, fmt, val, want in named:
        bad = bytearray(good)
        struct.pack_into(fmt, bad, off, val)
        got = _first_bad(bytes(bad))
        # Re-sign so the rejection is the FIELD's, not the signature's: an
        # unsigned mutation would be caught at step 3 and prove nothing about
        # the bound.  Step 3 comes after step 2, so a correctly signed bad
        # field must still be refused by name.
        resigned = bytes(bad[:96]) + rlxsign.sign(DEV, bytes(bad[:96])) \
            + bytes(bad[BODY:])
        got2 = _first_bad(resigned)
        if got2 != want:
            miss.append("%s -> %s (want %s)" % (name, got2, want))
        if got is None:
            miss.append("%s unsigned was ACCEPTED" % name)
    add("C6", "each of %d field bounds is rejected BY NAME, re-signed so the "
        "bound is what refuses" % len(named), not miss,
        "; ".join(miss) or "all by name")

    # reserved bytes: every one of the 32, individually
    rmiss = []
    for i in range(32):
        bad = bytearray(good)
        bad[64 + i] = 0xA5
        rs = bytes(bad[:96]) + rlxsign.sign(DEV, bytes(bad[:96])) \
            + bytes(bad[BODY:])
        if _first_bad(rs) != "2/reserved":
            rmiss.append(i)
    add("C7", "a non-zero byte in ANY of the 32 reserved bytes is rejected",
        not rmiss, "offsets missed: %r" % rmiss if rmiss else "all 32")

    # ---------------------------------------------- C8  truncation
    tmiss = [n for n in list(range(0, 200, 7)) + [len(good) - 1]
             if _first_bad(good[:n]) is None]
    add("C8", "a container truncated at any of %d lengths is REJECTED"
        % (len(range(0, 200, 7)) + 1), not tmiss,
        "accepted at %r" % tmiss if tmiss else "none accepted")
    add("C9", "a container with extra bytes appended is REJECTED",
        _first_bad(good + b"\0") == "2/container_len", "2/container_len")

    # ---------------------------------------------- C10  wrong key
    other = bytes([0x43]) * 32
    add("C10", "the same container under a DIFFERENT public key is rejected "
        "at step 3", any(not ok and n == 3 for n, _, ok, _ in
                         checks(good, rlxsign.secret_to_public(other))),
        "3/signature")

    # ---------------------------------------------- C11-C12  the order
    # Step 4 must not run before step 3 passes.  A container whose signature is
    # bad AND whose digest is bad must report the SIGNATURE -- if it reports
    # the digest, the payload was hashed on an unauthenticated header.
    bad = bytearray(good)
    bad[96] ^= 1
    bad[BODY] ^= 1
    add("C11", "a bad signature AND a bad digest reports the SIGNATURE, so "
        "the payload was not hashed", _first_bad(bytes(bad)) == "3/signature",
        _first_bad(bytes(bad)))
    bad = bytearray(good)
    struct.pack_into(">I", bad, 12, MAX_PAYLOAD + 1)   # payload_len absurd
    bad[96] ^= 1                                       # and the signature bad
    add("C12", "an absurd payload_len is caught at step 2, BEFORE the "
        "signature -- nothing is read at that length",
        _first_bad(bytes(bad)) == "2/payload_len", _first_bad(bytes(bad)))

    # ---------------------------------------------- C13  anti-rollback
    v = _good_container(version=5)
    add("C13", "version 5 vs counter 4/5/6 -> ok/ok/REJECT (>= passes)",
        _first_bad(v, 4) is None and _first_bad(v, 5) is None
        and _first_bad(v, 6) == "5/version_vs_counter",
        "the boundary is version >= counter")

    # ---------------------------------------------- C14  the stock loader
    recognised, lines = stock_loader_verdict(good)
    add("C14", "the STOCK loader does not recognise this container",
        not recognised, lines[-1].strip()[:60])
    # 🔴 and the control, because a check that cannot fire proves nothing: the
    # vendor's own shape MUST be recognised by the same function.
    vend = b"cr6c" + struct.pack(">3I", 0x80500000, 0x060000, 16) \
        + b"\0" * 16
    rec2, _ = stock_loader_verdict(vend)
    vend_burn = b"boot" + struct.pack(">3I", 0, 0, 16) + b"\0" * 16
    rec3, _ = stock_loader_verdict(vend_burn)
    add("C15", "the same function DOES recognise a 'cr6c' header and a 'boot' "
        "section (C14's control)", rec2 and rec3,
        "cr6c %s, boot %s" % (rec2, rec3))
    add("C16", "'RLXU' is none of check_image()'s 2 or burn()'s 8 signatures",
        b"RLXU" not in CHECK_IMAGE_SIGS and b"RLXU" not in BURN_SIGS,
        "2 + 8 = 10 signatures checked")

    # ---------------------------------------------- C17-C19  build refusals
    class _A(object):
        pass

    nm = []
    for base in ("nfjrom", "boot.img", "NFJROM", "Boot.IMG"):
        try:
            guard_output_name("/tmp/out/" + base)
            nm.append(base + " ALLOWED")
        except SystemExit:
            pass
    ok_names = []
    for base in ("slotA.rlxu", "nfjrom.rlxu", "boot.img.bin", "myboot.img2"):
        try:
            guard_output_name("/tmp/out/" + base)
        except SystemExit:
            ok_names.append(base + " REFUSED")
    add("C17", "an output named nfjrom or boot.img is refused (any case), and "
        "4 near-misses are NOT", not nm and not ok_names,
        "; ".join(nm + ok_names) or "2 refused, 4 permitted")

    fm = []
    for at, n, want in ((0x000000, 0x1000, True), (0x006000, 0x1000, True),
                        (0x020000, 0x1000, True), (0x008000, 0x1000, False),
                        (0x030000, 0x1000, False), (0x060000, 0x1000, False)):
        try:
            guard_destination(at, n)
            refused = False
        except SystemExit:
            refused = True
        if refused != want:
            fm.append("0x%06X %s" % (at, "allowed" if want else "refused"))
    add("C18", "build refuses the 3 forbidden destinations and PERMITS 3 "
        "legitimate neighbours", not fm, "; ".join(fm) or "3 refused, "
                                                          "3 permitted")

    # build() refuses to emit a malformation: entry outside the payload
    try:
        _good_container(entry_addr=0x80600000)
        c19 = "ACCEPTED"
    except ValueError as exc:
        c19 = "refused: %s" % str(exc)[:44]
    add("C19", "build() REFUSES to emit a container its own verify rejects",
        c19.startswith("refused"), c19)

    # ---------------------------------------------- C20  round trip on disk
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "payload.bin")
        with open(p, "wb") as fh:
            fh.write(_sample(8192))
        o = os.path.join(tmp, "c.rlxu")
        # The two CLI runs' own output is captured, not printed: this is a
        # control, and a control that buries the verdict list is harder to read
        # than one that reports a pass.  `verify --stock-loader` is run for its
        # exit code here; § "the proof" in notes/update-chain.md is the run
        # whose output a reader is meant to see.
        cap = io.StringIO()
        with contextlib.redirect_stdout(cap):
            rc = main(["build", "--payload", p, "--out", o, "--version", "3",
                       "--load-addr", "0x80500000",
                       "--entry-addr", "0x80500000",
                       "--recipe-id", "3685a3a4", "--dev-seed",
                       "--flash-at", "0x030000"])
            rc2 = main(["verify", o, "--dev-seed", "--stock-loader"])
        add("C20", "build then verify through the CLI, on disk, exit 0/0",
            rc == 0 and rc2 == 0 and os.path.getsize(o) == BODY + 8192
            and "NOT AN IMAGE" in cap.getvalue(),
            "build %d, verify %d, %d bytes, stock loader NOT AN IMAGE"
            % (rc, rc2, os.path.getsize(o)))

    print("%s -- self-test" % VERSION)
    ok = fail = 0
    for cid, what, good_, detail in rows:
        if good_:
            ok += 1
            print("  ok     %-4s %-64s %s" % (cid, what, detail))
        else:
            fail += 1
            print("  FAIL   %-4s %-64s %s" % (cid, what, detail))
    print("  %d passed, %d failed" % (ok, fail))
    return 2 if fail else 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="mkfw2.py", description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    def keyargs(p):
        p.add_argument("--seed-hex")
        p.add_argument("--seed-file")
        p.add_argument("--dev-seed", action="store_true",
                       help="SPEC-R8a 3's published development seed "
                            "(32 x 0x42) -- not a secret, never production")

    b = sub.add_parser("build", help="make an RLXU container")
    b.add_argument("--payload", required=True)
    b.add_argument("--out", required=True,
                   help="the container; never named nfjrom or boot.img")
    b.add_argument("--version", required=True, type=lambda s: int(s, 0),
                   help="the anti-rollback ordinal, 1..0xFFFFFFFE")
    b.add_argument("--load-addr", required=True, type=lambda s: int(s, 0))
    b.add_argument("--entry-addr", required=True, type=lambda s: int(s, 0))
    b.add_argument("--recipe-id", required=True,
                   help="4 bytes of hex -- what RLXFW-ID0 prints")
    b.add_argument("--flags", type=lambda s: int(s, 0), default=0)
    b.add_argument("--flash-at", type=lambda s: int(s, 0), default=None,
                   help="the flash destination this container is INTENDED for, "
                        "checked against flashguard.  Nothing here writes "
                        "flash; this is a refusal, not a write")
    keyargs(b)
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="check an RLXU container")
    v.add_argument("container")
    v.add_argument("--pubkey-hex")
    v.add_argument("--counter", type=lambda s: int(s, 0), default=0,
                   help="the anti-rollback counter to test the version "
                        "against (default 0: today's region is erased)")
    v.add_argument("--stock-loader", action="store_true",
                   help="also report what the stock loader makes of it")
    keyargs(v)
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        die("no subcommand.  `build` makes a container, `verify` checks one")
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
