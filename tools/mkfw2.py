#!/usr/bin/env python3
"""Build and verify an `RLXU` update container -- the host side of gate `R8a`.

`SPEC-R8a.md` § 2 pins the format and `notes/update-chain.md` § 1 is the table
this file is checked against; this file is its only producer, and `verify`
is a second implementation of the check `src/rlxboot/container.c` makes on the
device.  Two implementations of one rule is the point: the target's verifier is
C on a big-endian Lexra core with no libc, this one is Python on a host, and a
container that one accepts and the other rejects is a finding in whichever is
wrong.

The container (all integers big-endian; header 96 B, signature 64 B, payload)
-----------------------------------------------------------------------------
    0   4  magic 'RLXU'          28  32  payload SHA-256
    4   2  format = 2            60   4  recipe id (what RLXFW-ID0 prints)
    6   2  header_len = 96       64   4  flash_at -- the DECLARED destination
    8   4  version 1..0xFFFFFFFE 68   4  flash_form -- WHOL / PAYL / zero
   12   4  payload_len <= 3 MiB  72  24  reserved, ALL ZERO
   16   4  load_addr             96  64  Ed25519 over bytes 0..95
   20   4  entry_addr           160   n  payload
   24   4  flags -- 0 in R8a; any unknown bit set -> reject

FORMAT 2, AND WHY THE NUMBER MOVED (the ruling of 2026-10-04, `R8b` item 3)
---------------------------------------------------------------------------
In format 1 the flash destination was an OPTIONAL argument to this tool and
entered no byte of the container.  量 on format 1: `build` with no
`--flash-at` exited 0 and emitted a container, and the container it emitted
was **byte-identical** to the one built with `--flash-at 0x030000` -- so the
destination check was a check that could be skipped by omission, and nothing
downstream could tell a checked container from an unchecked one.  That was
`R8b`'s precondition ③, half-met.

Format 2 spends the first 8 of the 32 reserved bytes on `flash_at` and
`flash_form`, inside the signed region; the sentinel `0xFFFFFFFF` means *not
for flash*:

* `build` requires **exactly one** of `--flash-at ADDR` and `--not-for-flash`,
  and `--flash-at` requires `--flash-form whole|payload`.  Omission is a
  refusal, so neither declaration can be skipped; and whichever is given, it
  is signed.
* `verify --write-at ADDR --write-form F` refuses a container whose signed
  `flash_at` is not `ADDR` **or** whose `flash_form` is not `F`, and refuses
  one that declares nothing at all.  An undeclared container may never be
  written to flash.
* The format itself refuses a declared destination whose LANDING RANGE is
  inside the loader region, inside `H601`, or running off the end of the chip
  -- the ranges nothing can license, through
  `flashguard.check_unrecoverable`.  The rescue slot is NOT refused by the
  format: it is licensable, and the BUILD is where that gate is
  (`flashguard.check_licensed`).

WHY THE FORM IS SIGNED TOO (the fourth decision, added 2026-10-04 after the
`R8b` item-5 agent measured the hole).  量 in this tree: a container built
over a `cr6c`-headed payload reads `RLXU` at offset 0 and `cr6c` at offset
160, and format 1's guard was handed `BODY + len(payload)` -- the whole
container.  So if the container is what lands at `0x020000`, the base reads
`RLXU`, the stock loader's `check_image()` returns 0, and `rlxboot-rescue`
never boots (`FW-168`, `notes/update-chain.md` § 5-6): every guard passes and
the rescue is dead.  For a slot destination landing the container is exactly
right, because a slot must carry no header the loader recognises.  The two
are opposite requirements for two destinations, so an unauthenticated writer
must not be the one that chooses: the choice is `flash_form`, it is inside the
signed header, and `--write-form` is what a writer must state to be let
through.  **What is NOT decided here**: which destinations must boot.  That is
work-order item 5's (`FW-168`'s two opposite properties, each with its own
control); this file reports the landing bytes and whether the landing base is
one of the loader's six scan candidates, and refuses nothing on that basis.

The format number moved rather than reusing a reserved byte quietly, so a
format-1 container is refused by name at step 1 instead of being reinterpreted:
its zero bytes at 64..67 would have read as "destination 0x000000", which is a
sentence that container never said.  Nothing has ever been flashed, so no
device holds a verifier that expects format 1.

Verification order, and it is part of the format because it bounds what a
hostile container can do before it is trusted:

   1  magic, format, header_len
   2  the field bounds -- including that load_addr and load_addr+payload_len
      lie in RAM, that the destination overlaps neither `rlxboot` itself nor
      the container's own staging buffer, and that the declared flash
      destination is neither unrecoverable nor at odds with where the caller
      says it is writing
   3  the Ed25519 signature over the 96 header bytes
   4  only then the payload's SHA-256, over payload_len bytes
   5  the version against the anti-rollback counter

**Nothing is copied anywhere before step 4 passes**, and `verify` reports the
steps in that order so a capture of the target's output and a run of this tool
can be read side by side.  ⚠️ The ORDER WITHIN step 2 is not the same in the
two implementations and never was: this file checks `reserved` first and
`container.c` checks `version` first, so a container that violates two step-2
bounds can be refused by different field names on host and device.  Every case
in both suites therefore violates exactly one bound at a time.

Three refusals `build` makes that are not about the format
---------------------------------------------------------
* **A destination inside a forbidden flash range.**  `tools/flashguard.py` owns
  the ranges and this file imports it; plan precondition ③ is exactly this,
  with the positive control that a permitted range really is permitted.  Since
  the 2026-10-04 ruling the rescue slot is licensable: the refusal stands
  unless the owner's dated `owner-yes` row names this base, this length, this
  region and this payload's digest (`--owner-yes FILE`).  Both arms are `C18`
  and `C18b`.
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
  refuses if it is recognised.  ⚠️ This is also why a licensed `--flash-at
  0x020000` does not make this tool the producer of `rlxboot-rescue`: that
  image must be recognised by the stock loader on purpose
  (`notes/update-chain.md` § 6), and this tool refuses to emit anything that
  is.  Work-order item 5 is where those two opposite properties meet.

Nothing here writes flash.  This file emits no loader command at all, and
`tools/test-mkfw2.sh` `X1`-`X3` assert that the four flash-write verbs appear
in none of these tools' output.

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

VERSION = "mkfw2 1.1"

MAGIC = 0x524C5855            # 'RLXU'
FORMAT = 2
HEADER_LEN = 96
SIG_LEN = 64
BODY = HEADER_LEN + SIG_LEN   # 160, where the payload starts
MAX_PAYLOAD = 0x00300000      # 3 MiB, SPEC-R8a 2
VERSION_MIN, VERSION_MAX = 1, 0xFFFFFFFE
KNOWN_FLAGS = 0x00000000      # R8a: bit 0 is RESERVED for LZMA and unset

# Format 2's two new fields, and the 24 bytes left over.
FLASH_OFF = 64
FLASH_NONE = 0xFFFFFFFF       # "this container is not for flash"
FORM_OFF = 68
RESV_OFF = 72
RESV_LEN = 24
# The landing form, as printable words so a hex dump reads them.
FORM_NONE = 0x00000000
FORM_WHOLE = 0x57484F4C       # "WHOL" -- the whole container lands
FORM_PAYLOAD = 0x5041594C     # "PAYL" -- the payload lands, prefix stripped
FORM_NAME = {FORM_NONE: "none", FORM_WHOLE: "whole", FORM_PAYLOAD: "payload"}
FORM_WORD = {"none": FORM_NONE, "whole": FORM_WHOLE, "payload": FORM_PAYLOAD}

# 讀 `docs/loader-command-semantics.md` § a and `notes/update-chain.md` § 5:
# the stock loader scans these six 64 KiB bases and boots the LOWEST that
# passes `check_image()`.  Named here so `build` and `verify` can report
# whether a landing base is one of them.  Nothing is refused on this basis --
# which destinations must boot is work-order item 5's decision.
SCAN_CANDIDATES = (0x010000, 0x020000, 0x030000, 0x040000, 0x050000, 0x060000)

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
                digest, recipe_id, flash_at, flash_form):
    """The 96 header bytes.  `struct` with '>' is the only endian statement."""
    if len(digest) != 32:
        raise ValueError("a SHA-256 digest is 32 bytes, not %d" % len(digest))
    if len(recipe_id) != 4:
        raise ValueError("a recipe id is 4 bytes, not %d" % len(recipe_id))
    if flash_at is None or flash_form is None:
        raise ValueError("flash_at and flash_form are not optional in format "
                         "%d: pass an offset and a form, or FLASH_NONE and "
                         "FORM_NONE" % FORMAT)
    h = struct.pack(">IHHIIIII32s4sII", MAGIC, FORMAT, HEADER_LEN, version,
                    payload_len, load_addr, entry_addr, flags, digest,
                    recipe_id, flash_at, flash_form)
    h += b"\x00" * RESV_LEN                   # reserved, bytes 72..95
    if len(h) != HEADER_LEN:
        raise ValueError("header packed to %d bytes, not %d"
                         % (len(h), HEADER_LEN))
    return h


def unpack_header(h):
    """The 96 header bytes -> a dict.  No validation; `checks()` does that."""
    (magic, fmt, hlen, version, plen, load, entry, flags, digest,
     recipe, flash_at, form) = struct.unpack_from(">IHHIIIII32s4sII", h, 0)
    return {"magic": magic, "format": fmt, "header_len": hlen,
            "version": version, "payload_len": plen, "load_addr": load,
            "entry_addr": entry, "flags": flags, "digest": digest,
            "recipe_id": recipe, "flash_at": flash_at, "flash_form": form,
            "reserved": h[RESV_OFF:HEADER_LEN]}


def flash_at_text(v):
    """-> how a declared destination is printed, in one place."""
    return "none" if v == FLASH_NONE else "0x%06X" % v


def form_text(v):
    """-> how a landing form is printed.  An unknown word prints as hex, so a
    refusal about one does not pretend to name it."""
    return FORM_NAME.get(v, "0x%08X (not a form)" % v)


def landing_len(flash_at, form, payload_len):
    """-> how many bytes land at `flash_at`, or None if the pair is not
    consistent.  THE ONE PLACE the form becomes a length, on this side."""
    if flash_at == FLASH_NONE:
        return 0 if form == FORM_NONE else None
    if form == FORM_WHOLE:
        return BODY + payload_len
    if form == FORM_PAYLOAD:
        return payload_len
    return None


def landing(blob):
    """-> (base, nbytes, form, first4) for what a writer would program, read
    out of the SIGNED header.  `base` is None when nothing is declared.

    It exists so `build` and `verify` report the same four things, and because
    'what actually lands' is the question `FW-168` turns on: for the whole
    container that is `RLXU` at the base, for the payload it is whatever the
    payload's own first word is.
    """
    f = unpack_header(blob[:HEADER_LEN])
    n = landing_len(f["flash_at"], f["flash_form"], f["payload_len"])
    if f["flash_at"] == FLASH_NONE or n is None:
        return None, n, f["flash_form"], b""
    first = (blob[:4] if f["flash_form"] == FORM_WHOLE
             else blob[BODY:BODY + 4])
    return f["flash_at"], n, f["flash_form"], first


def landing_lines(blob):
    """-> the lines `build` and `verify` both print about what lands.

    A REPORT AND NOT A REFUSAL, and that is a decision: whether a destination
    must boot from flash is work-order item 5's (`FW-168`), and a refusal here
    would make this file the owner of a policy it cannot see the whole of.
    What it can do is make the consequence visible before anyone writes.
    """
    base, n, form, first = landing(blob)
    if base is None:
        return ["  landing            nothing -- the container declares no "
                "flash destination (form %s)" % form_text(form)]
    out = ["  landing            0x%06X+0x%X, form %s -- the %s lands there"
           % (base, n, form_text(form),
              "whole container" if form == FORM_WHOLE else "payload alone")]
    out.append("  landing bytes      %r at 0x%06X" % (first, base))
    scan = base in SCAN_CANDIDATES
    rec = first in CHECK_IMAGE_SIGS or first in BURN_SIGS
    out.append("  landing scanned    0x%06X %s one of the loader's six scan "
               "candidates" % (base, "IS" if scan else "is NOT"))
    out.append("  landing verdict    %s"
               % ("the stock loader reads a header it recognises at the "
                  "landing base, so this can boot without rlxboot"
                  if rec else
                  "the stock loader reads no header it recognises at the "
                  "landing base, so it cannot boot this from flash"))
    if scan != rec:
        out.append("  landing 🔴         a scan candidate that cannot boot, "
                   "or a bootable image where nothing scans -- FW-168 wants "
                   "both properties and this is item 5's call, not a refusal "
                   "this tool makes")
    return out


def checks(blob, pubkey, counter=0, write_at=None, write_form=None):
    """-> [(step, name, ok, detail)] in SPEC-R8a 2's order, stopping at the
    first failure.

    `write_at` is where the CALLER says it is about to write this container in
    flash, or None for "I am writing nothing", and `write_form` is as what.
    Neither is part of the container and neither is signed -- they are the
    other half of the comparison the signed `flash_at` and `flash_form` exist
    for.  A `write_at` without a `write_form` reads as form `none`, which
    matches no declared container: the fail-safe direction.

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
                "%d, want %d%s" % (f["format"], FORMAT,
                                   "  (format 1 has no signed flash "
                                   "destination; rebuild it)"
                                   if f["format"] == 1 else "")):
        return out
    if not step(1, "header_len", f["header_len"] == HEADER_LEN,
                "%d, want %d" % (f["header_len"], HEADER_LEN)):
        return out

    # ---- step 2: the field bounds
    if not step(2, "reserved", f["reserved"] == b"\x00" * RESV_LEN,
                "%d non-zero byte(s) in %d at offset %d"
                % (sum(1 for b in f["reserved"] if b), RESV_LEN, RESV_OFF)):
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
    # The destination and the form must agree about whether there is one, and
    # the form is what fixes how many bytes land.  A form nobody checked is a
    # length nobody checked, so this comes before the range check.
    fa, fo = f["flash_at"], f["flash_form"]
    nland = landing_len(fa, fo, plen)
    if not step(2, "flash_form", nland is not None,
                "destination %s with form %s -- a destination needs one of "
                "whole/payload and no destination needs form none"
                % (flash_at_text(fa), form_text(fo))):
        return out
    # The declared LANDING range, against the ranges NOTHING can license.
    # `plen` is bounded by the two steps above before it is used here.
    if fa == FLASH_NONE:
        step(2, "flash_dst", True, "none -- not for flash")
    else:
        bad = flashguard.check_unrecoverable(fa, nland)
        if not step(2, "flash_dst", bad is None,
                    "0x%06X+0x%X overlaps %s" % (fa, nland, bad)
                    if bad is not None else
                    "0x%06X+0x%X (form %s), clear of the loader region, H601 "
                    "and the chip's end" % (fa, nland, form_text(fo))):
            return out
    # And against where -- and as what -- the caller says it is writing.  An
    # undeclared container may never be written to flash: that is the whole
    # point of making the declaration non-optional.
    if write_at is None:
        step(2, "flash_match", True, "no write declared by the caller")
    else:
        wf = FORM_NONE if write_form is None else write_form
        if not step(2, "flash_match", fa == write_at and fo == wf,
                    "the container declares %s form %s and the caller is "
                    "writing 0x%06X form %s"
                    % (flash_at_text(fa), form_text(fo), write_at,
                       form_text(wf))):
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

    `burn()`'s eight section signatures are checked too, because the burn word
    and a section header are the *other* way the loader acts on a file.

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


def guard_destination(flash_at, nbytes, licence=None, digest_hex=None):
    """Refuse a forbidden flash destination.  flashguard owns the ranges.

    -> the (date, row) of the licence that permitted a licensable range, or
    None when no licence was needed or none was offered.  `flash_at is None`
    means `--not-for-flash`: nothing is declared, so there is nothing to
    check, and the container says so in a signed byte.
    """
    if flash_at is None:
        return None
    try:
        r = flashguard.check_licensed(flash_at, nbytes, licence, digest_hex)
    except ValueError as exc:
        die("--flash-at: %s" % exc)
    if r is not None:
        die("refusing to build for flash destination 0x%06X+0x%X: it overlaps "
            "%s" % (flash_at, nbytes, r), code=3)
    return flashguard.licence_grant(flash_at, nbytes, licence, digest_hex)


def build(payload, version, load_addr, entry_addr, recipe_id, seed,
          flash_at, flash_form, flags=0):
    """-> the container bytes.  Every § 2 field, and it refuses to emit a
    container its own `verify` would reject: a builder that can produce a
    malformation is a builder that will.

    `flash_at` and `flash_form` are REQUIRED and have no default.
    `FLASH_NONE`/`FORM_NONE` is how a caller says "not for flash"; there is no
    way to say nothing, because in format 1 saying nothing was the defect.
    """
    digest = hashlib.sha256(payload).digest()
    header = pack_header(version, len(payload), load_addr, entry_addr, flags,
                         digest, recipe_id, flash_at, flash_form)
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


def read_licence(path):
    """-> (text, sha256 of the text) for the owner's ```owner-yes file."""
    if not os.path.isfile(path):
        die("no such licence file: %s" % path)
    raw = open(path, "rb").read()
    return raw.decode("utf-8", "replace"), hashlib.sha256(raw).hexdigest()


def cmd_build(args):
    # 🔴 THE DECLARATION IS NOT OPTIONAL.  Exactly one of the two, checked
    # before anything is read, because "I forgot" and "it is not for flash"
    # were the same argv in format 1 and that is what made ③ skippable.
    if (args.flash_at is None) == (not args.not_for_flash):
        die("exactly one of --flash-at ADDR and --not-for-flash is required: "
            "the destination is part of what this tool SIGNS (format %d), so "
            "omitting it is not the same as declaring there is none"
            % FORMAT)
    # 🔴 AND THE FORM IS NOT OPTIONAL EITHER.  Whether the writer lands the
    # whole container or the payload alone decides whether a rescue slot can
    # boot at all (FW-168), so it is declared, signed and compared -- never
    # defaulted.
    if args.flash_at is not None and not args.flash_form:
        die("--flash-at needs --flash-form whole|payload: the form decides "
            "how many bytes land and what the loader reads at the landing "
            "base, and a default would be this tool choosing whether a "
            "rescue slot can boot")
    if args.flash_at is None and args.flash_form:
        die("--flash-form without --flash-at declares a form for a "
            "destination that does not exist")
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
    pay_sha = hashlib.sha256(payload).hexdigest()
    lic_text = lic_sha = None
    if args.owner_yes:
        lic_text, lic_sha = read_licence(args.owner_yes)
    flash_at = FLASH_NONE if args.flash_at is None else args.flash_at
    flash_form = (FORM_NONE if args.flash_form is None
                  else FORM_WORD[args.flash_form])
    # The guard sees the LANDING length, not the container length: for form
    # `payload` the writer strips the 160-byte prefix, so 160 fewer bytes land
    # and the licence row names the range that is actually programmed.
    nland = landing_len(flash_at, flash_form, len(payload))
    if nland is None:
        die("the destination and the form disagree: %s with form %s"
            % (flash_at_text(flash_at), form_text(flash_form)))
    grant = guard_destination(args.flash_at, nland, lic_text, pay_sha)
    recipe = parse_recipe(args.recipe_id)
    seed = rlxsign.read_seed(vars(args))
    try:
        blob = build(payload, args.version, args.load_addr, args.entry_addr,
                     recipe, seed, flash_at, flash_form, args.flags)
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
    print("  payload sha256     %s" % pay_sha)
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
    if args.flash_at is None:
        print("  flash destination  none, SIGNED as 0x%08X -- this container "
              "may not be written to flash by any caller that declares "
              "where it is writing" % FLASH_NONE)
    else:
        print("  flash destination  0x%06X+0x%X form %s -- PERMITTED by "
              "flashguard, and SIGNED into header bytes %d..%d"
              % (args.flash_at, nland, args.flash_form, FLASH_OFF,
                 FORM_OFF + 3))
    for ln in landing_lines(blob):
        print(ln)
    if grant is not None:
        date, row = grant
        print("  licence            the owner's yes of %s" % date)
        print("  licence row        %s" % row)
        print("  licence file       %s  sha256 %s" % (args.owner_yes, lic_sha))
    elif lic_sha is not None:
        print("  licence            %s was read and no row was needed"
              % args.owner_yes)
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
    if args.write_at is None and args.write_form:
        die("--write-form without --write-at: a form is what a WRITE is in, "
            "and this caller is not writing")
    wform = None if args.write_form is None else FORM_WORD[args.write_form]
    print("  caller writes to   %s"
          % ("nothing" if args.write_at is None else
             "0x%06X, form %s" % (args.write_at, form_text(wform))))
    rows = checks(blob, pub, args.counter, args.write_at, wform)
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
              "version %d, recipe %s, flash destination %s form %s"
              % (f["payload_len"], f["load_addr"], f["entry_addr"],
                 f["version"], f["recipe_id"].hex(),
                 flash_at_text(f["flash_at"]), form_text(f["flash_form"])))
        for ln in landing_lines(blob):
            print(ln)
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
             recipe_id=bytes.fromhex("3685a3a4"), flash_at=FLASH_NONE,
             flash_form=FORM_NONE)


def _sample(n=4096):
    return bytes((i * 13 + 5) & 0xFF for i in range(n))


def _good_container(payload=None, **kw):
    a = dict(_GOOD)
    a.update(kw)
    return build(payload if payload is not None else _sample(), seed=DEV, **a)


def _resign(blob):
    """Re-sign a mutated header so the refusal is the FIELD's, not step 3's."""
    return (bytes(blob[:HEADER_LEN])
            + rlxsign.sign(DEV, bytes(blob[:HEADER_LEN]))
            + bytes(blob[BODY:]))


def _first_bad(blob, counter=0, write_at=None, write_form=None):
    pub = rlxsign.secret_to_public(DEV)
    for n, name, ok, _ in checks(blob, pub, counter, write_at, write_form):
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
        (f["magic"] == MAGIC and f["format"] == FORMAT
         and f["header_len"] == 96
         and f["version"] == 7 and f["payload_len"] == 4096
         and f["load_addr"] == 0x80500000 and f["entry_addr"] == 0x80500000
         and f["flags"] == 0 and f["recipe_id"].hex() == "3685a3a4"
         and f["flash_at"] == FLASH_NONE and f["flash_form"] == FORM_NONE
         and f["reserved"] == b"\x00" * RESV_LEN
         and good[:4] == b"RLXU"),
        "magic bytes %r at offset 0, format %d" % (good[:4], f["format"]))
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
        ("format 1 (the old one)", 4, ">H", 1, "1/format"),
        ("format 3", 4, ">H", 3, "1/format"),
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
        # format 2: a destination with no form, and a form that is not a form
        ("flash_at 0x030000 with form none", FLASH_OFF, ">I", 0x030000,
         "2/flash_form"),
        ("form WHOL with no destination", FORM_OFF, ">I", FORM_WHOLE,
         "2/flash_form"),
        ("form PAYL with no destination", FORM_OFF, ">I", FORM_PAYLOAD,
         "2/flash_form"),
    ]
    miss = []
    for name, off, fmt, val, want2 in named:
        bad = bytearray(good)
        struct.pack_into(fmt, bad, off, val)
        got = _first_bad(bytes(bad))
        # Re-sign so the rejection is the FIELD's, not the signature's: an
        # unsigned mutation would be caught at step 3 and prove nothing about
        # the bound.  Step 3 comes after step 2, so a correctly signed bad
        # field must still be refused by name.
        got2 = _first_bad(_resign(bad))
        if got2 != want2:
            miss.append("%s -> %s (want %s)" % (name, got2, want2))
        if got is None:
            miss.append("%s unsigned was ACCEPTED" % name)
    add("C6", "each of %d field bounds is rejected BY NAME, re-signed so the "
        "bound is what refuses" % len(named), not miss,
        "; ".join(miss) or "all by name")

    # C6b/C6c drive the DESTINATION field on a base container that declares a
    # form, because on `good` -- which declares none -- every destination is
    # refused as `2/flash_form` first and `2/flash_dst` would never be
    # reached.  A case refused for the wrong reason is a case that proves
    # nothing.
    goodw = _good_container(flash_at=0x030000, flash_form=FORM_WHOLE)
    dstbad = [
        ("0x000000, the loader", 0x000000),
        ("0x006000, H601", 0x006000),
        ("0x005000, straddling into H601", 0x005000),
        ("0x3FF000, running off the chip", 0x3FF000),
        ("0xFFFFFFFE, past the chip entirely", 0xFFFFFFFE),
    ]
    miss2 = []
    for name, val in dstbad:
        bad = bytearray(goodw)
        struct.pack_into(">I", bad, FLASH_OFF, val)
        got = _first_bad(_resign(bad))
        if got != "2/flash_dst":
            miss2.append("%s -> %s" % (name, got))
    add("C6b", "each of %d forbidden DESTINATIONS is rejected as flash_dst, "
        "re-signed" % len(dstbad), not miss2,
        "; ".join(miss2) or "%d by name" % len(dstbad))
    # 🔴 C6c is C6b's positive control: the destinations the FORMAT permits
    # must pass step 2, or `2/flash_dst` would be a check that refuses every
    # declaration.  The rescue slot is among them -- the format permits a
    # container declaring it and the BUILD is where the licence is demanded.
    okd = []
    for name, val in (("0x008000, the first byte above H601", 0x008000),
                      ("0x020000, the rescue slot", 0x020000),
                      ("0x030000, a plain slot base", 0x030000),
                      ("0x3FEF00, ending inside the chip", 0x3FEF00)):
        bad = bytearray(goodw)
        struct.pack_into(">I", bad, FLASH_OFF, val)
        got = _first_bad(_resign(bad))
        if got is not None:
            okd.append("%s -> %s" % (name, got))
    add("C6c", "the 4 destinations the format PERMITS pass step 2 (C6b's "
        "positive control)", not okd, "; ".join(okd) or "4 permitted")
    # and a form word that is neither WHOL nor PAYL nor none
    fmiss = []
    for val in (0x00000001, 0x57484F4D, 0x5041594D, 0xFFFFFFFF):
        bad = bytearray(goodw)
        struct.pack_into(">I", bad, FORM_OFF, val)
        if _first_bad(_resign(bad)) != "2/flash_form":
            fmiss.append("0x%08X" % val)
    add("C6d", "a form word that is not one of the three is rejected as "
        "flash_form (4 probes)", not fmiss,
        "; ".join(fmiss) or "4 by name")

    # reserved bytes: every one of the 28, individually
    rmiss = []
    for i in range(RESV_LEN):
        bad = bytearray(good)
        bad[RESV_OFF + i] = 0xA5
        if _first_bad(_resign(bad)) != "2/reserved":
            rmiss.append(i)
    add("C7", "a non-zero byte in ANY of the %d reserved bytes at offset %d "
        "is rejected" % (RESV_LEN, RESV_OFF), not rmiss,
        "offsets missed: %r" % rmiss if rmiss else "all %d" % RESV_LEN)

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
    nm = []
    for base_ in ("nfjrom", "boot.img", "NFJROM", "Boot.IMG"):
        try:
            guard_output_name("/tmp/out/" + base_)
            nm.append(base_ + " ALLOWED")
        except SystemExit:
            pass
    ok_names = []
    for base_ in ("slotA.rlxu", "nfjrom.rlxu", "boot.img.bin", "myboot.img2"):
        try:
            guard_output_name("/tmp/out/" + base_)
        except SystemExit:
            ok_names.append(base_ + " REFUSED")
    add("C17", "an output named nfjrom or boot.img is refused (any case), and "
        "4 near-misses are NOT", not nm and not ok_names,
        "; ".join(nm + ok_names) or "2 refused, 4 permitted")

    fm = []
    for at, n, want2 in ((0x000000, 0x1000, True), (0x006000, 0x1000, True),
                         (0x020000, 0x1000, True), (0x008000, 0x1000, False),
                         (0x030000, 0x1000, False), (0x060000, 0x1000, False)):
        try:
            guard_destination(at, n)
            refused = False
        except SystemExit:
            refused = True
        if refused != want2:
            fm.append("0x%06X %s" % (at, "allowed" if want2 else "refused"))
    add("C18", "build refuses the 3 forbidden destinations with NO licence "
        "and PERMITS 3 legitimate neighbours", not fm,
        "; ".join(fm) or "3 refused, 3 permitted")

    # 🔴 C18b IS THE LICENSED ARM.  Without it C18 is a guard shown only
    # refusing, and the 2026-10-04 ruling would be a rule nobody can satisfy.
    pay = _sample(1024)
    pay_sha = hashlib.sha256(pay).hexdigest()
    # The rescue slot is written in PAYLOAD form, so the landing length is the
    # payload's and not the container's -- 160 bytes fewer, and the licence
    # names the range that is actually programmed.
    nb = len(pay)
    row = "2026-10-04\t%s" % flashguard.licence_payload(0x020000, nb,
                                                        "rescue", pay_sha)
    lic = "```owner-yes\n%s\n```\n" % row
    try:
        g = guard_destination(0x020000, nb, lic, pay_sha)
        c18b = "permitted under %s" % (g[0] if g else "NO GRANT")
    except SystemExit:
        c18b = "REFUSED"
    add("C18b", "the SAME 0x020000 destination WITH the owner's dated row is "
        "permitted, and the grant carries the date", c18b.startswith(
            "permitted under 2026-"), c18b)
    # and the other direction on the same licence: one byte more is not it
    try:
        guard_destination(0x020000, nb + 1, lic, pay_sha)
        c18c = "ALLOWED"
    except SystemExit:
        c18c = "refused"
    add("C18c", "that licence does not cover one byte more", c18c == "refused",
        "the row names the length")

    # build() refuses to emit a malformation: entry outside the payload
    try:
        _good_container(entry_addr=0x80600000)
        c19 = "ACCEPTED"
    except ValueError as exc:
        c19 = "refused: %s" % str(exc)[:44]
    add("C19", "build() REFUSES to emit a container its own verify rejects",
        c19.startswith("refused"), c19)
    # and the same for a destination the format forbids, which build() cannot
    # be talked into emitting even with no guard call in front of it
    try:
        _good_container(flash_at=0x000000, flash_form=FORM_WHOLE)
        c19b = "ACCEPTED"
    except ValueError as exc:
        c19b = "refused: %s" % str(exc)[:40]
    add("C19b", "build() REFUSES to emit a container declaring the loader "
        "region, with no guard call in front of it",
        c19b.startswith("refused"), c19b)

    # ------------------------------------- C21-C25  the signed destination
    none_c = _good_container(payload=_sample(2048))
    flash_c = _good_container(payload=_sample(2048), flash_at=0x030000,
                              flash_form=FORM_WHOLE)
    add("C21", "--not-for-flash is SIGNED as 0x%08X / form none at bytes "
        "%d..%d" % (FLASH_NONE, FLASH_OFF, FORM_OFF + 3),
        none_c[FLASH_OFF:FLASH_OFF + 4] == b"\xFF\xFF\xFF\xFF"
        and none_c[FORM_OFF:FORM_OFF + 4] == b"\x00\x00\x00\x00"
        and none_c[RESV_OFF:HEADER_LEN] == b"\x00" * RESV_LEN,
        "bytes %s %s, then %d zero reserved bytes"
        % (none_c[FLASH_OFF:FLASH_OFF + 4].hex(),
           none_c[FORM_OFF:FORM_OFF + 4].hex(), RESV_LEN))
    # 🔴 C22 IS THE NEGATIVE OF WHAT FORMAT 1 MEASURED.  量 on format 1 the
    # two containers had the SAME sha256; here they must differ in the two
    # declaration fields AND in the signature, or neither is signed.
    add("C22", "the same payload declared for 0x030000 differs from the "
        "not-for-flash one in the two FIELDS and in the SIGNATURE",
        len(none_c) == len(flash_c)
        and none_c[FLASH_OFF:FORM_OFF + 4] != flash_c[FLASH_OFF:FORM_OFF + 4]
        and none_c[HEADER_LEN:BODY] != flash_c[HEADER_LEN:BODY]
        and none_c[BODY:] == flash_c[BODY:]
        and none_c[:FLASH_OFF] == flash_c[:FLASH_OFF],
        "fields %s vs %s, same payload bytes, same first 64"
        % (none_c[FLASH_OFF:FORM_OFF + 4].hex(),
           flash_c[FLASH_OFF:FORM_OFF + 4].hex()))
    # tampering with the field without re-signing is caught at step 3
    t = bytearray(flash_c)
    struct.pack_into(">I", t, FLASH_OFF, 0x020000)
    add("C23", "moving the declared destination WITHOUT re-signing is caught "
        "at the signature", _first_bad(bytes(t)) == "3/signature",
        _first_bad(bytes(t)))
    # and re-signed, it is caught by the mismatch instead -- which is the
    # check that makes the signed field load-bearing rather than decorative
    rs = _resign(t)
    add("C23b", "re-signed, it is accepted on its own terms and REFUSED "
        "against the write the caller declares",
        _first_bad(rs) is None
        and _first_bad(rs, write_at=0x030000,
                       write_form=FORM_WHOLE) == "2/flash_match"
        and _first_bad(rs, write_at=0x020000,
                       write_form=FORM_WHOLE) is None,
        "0x020000 declared: ok with no write, 2/flash_match against "
        "0x030000, ok against 0x020000")
    add("C24", "an UNDECLARED container is refused against any write",
        _first_bad(none_c, write_at=0x030000,
                   write_form=FORM_WHOLE) == "2/flash_match"
        and _first_bad(none_c, write_at=0x020000,
                       write_form=FORM_PAYLOAD) == "2/flash_match"
        and _first_bad(none_c) is None,
        "2/flash_match for both, and accepted when nothing is written")
    add("C25", "a container declared for 0x030000 whole is ACCEPTED against a "
        "write of 0x030000 whole (the permitting arm of flash_match)",
        _first_bad(flash_c, write_at=0x030000, write_form=FORM_WHOLE) is None,
        "the match permits as well as refuses")
    # 🔴 C25b IS THE FOURTH DECISION.  The offset agrees and only the FORM
    # differs, so this is the case that fails if the form is signed but not
    # compared -- the writer choosing whether to strip the 160-byte prefix,
    # which is what decides whether a rescue slot can boot at all.
    add("C25b", "the same container is REFUSED against a write of 0x030000 "
        "PAYLOAD -- the offset agrees and only the form differs",
        _first_bad(flash_c, write_at=0x030000,
                   write_form=FORM_PAYLOAD) == "2/flash_match"
        and _first_bad(flash_c, write_at=0x030000,
                       write_form=None) == "2/flash_match",
        "2/flash_match for the wrong form and for a caller that names none")

    # ------------------------------------- C26  the declaration is required
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "payload.bin")
        with open(p, "wb") as fh:
            fh.write(_sample(8192))
        argv0 = ["build", "--payload", p, "--version", "3",
                 "--load-addr", "0x80500000", "--entry-addr", "0x80500000",
                 "--recipe-id", "3685a3a4", "--dev-seed"]

        def run(extra, out):
            # stderr is captured too: `die` writes there, and a self-test that
            # let its own refusals through would put unparsable lines in the
            # CI capture `ci-census` reads.
            cap, err = io.StringIO(), io.StringIO()
            try:
                with contextlib.redirect_stdout(cap):
                    with contextlib.redirect_stderr(err):
                        rc = main(argv0 + ["--out", os.path.join(tmp, out)]
                                  + extra)
                return rc, cap.getvalue()
            except SystemExit as exc:
                return exc.code, cap.getvalue()

        rc_none, _ = run([], "a.rlxu")
        rc_both, _ = run(["--flash-at", "0x030000", "--flash-form", "whole",
                          "--not-for-flash"], "b.rlxu")
        rc_one, o_one = run(["--flash-at", "0x030000",
                             "--flash-form", "whole"], "c.rlxu")
        rc_nf, o_nf = run(["--not-for-flash"], "d.rlxu")
        add("C26", "build with NEITHER declaration is refused 3, with BOTH "
            "refused 3, and with either one alone exits 0",
            rc_none == 3 and rc_both == 3 and rc_one == 0 and rc_nf == 0
            and not os.path.exists(os.path.join(tmp, "a.rlxu")),
            "neither %s, both %s, --flash-at %s, --not-for-flash %s, and no "
            "file was written for the refused one"
            % (rc_none, rc_both, rc_one, rc_nf))
        add("C26b", "and the build line says which destination was signed",
            "SIGNED into header bytes 64..71" in o_one
            and "may not be written to flash" in o_nf,
            "both forms print what they signed")
        # 🔴 C26c: the FORM is required too, and a form with no destination is
        # refused.  Without this, `--flash-at` alone would have a default and
        # the tool would be choosing whether a rescue slot can boot.
        rc_nofm, _ = run(["--flash-at", "0x030000"], "e.rlxu")
        rc_fmonly, _ = run(["--flash-form", "whole"], "f.rlxu")
        add("C26c", "--flash-at without --flash-form is refused 3, and "
            "--flash-form without --flash-at is refused 3",
            rc_nofm == 3 and rc_fmonly == 3
            and not os.path.exists(os.path.join(tmp, "e.rlxu")),
            "no form %s, no destination %s, and neither wrote a container"
            % (rc_nofm, rc_fmonly))

        # --------------------------- C29  what actually lands
        # 🔴 THE MEASUREMENT THE FOURTH DECISION TURNS ON.  The same
        # cr6c-headed payload, declared both ways: in `whole` form the loader
        # would read 'RLXU' at the landing base and `check_image()` returns 0,
        # so a rescue slot would be dead; in `payload` form it reads 'cr6c'.
        cr6c = (b"cr6c" + struct.pack(">3I", 0x80500000, 0x020000, 1024)
                + _sample(1024))
        pc = os.path.join(tmp, "cr6c.bin")
        with open(pc, "wb") as fh:
            fh.write(cr6c)
        cw = build(cr6c, 7, 0x80500000, 0x80500000,
                   bytes.fromhex("3685a3a4"), DEV, 0x030000, FORM_WHOLE)
        cp = build(cr6c, 7, 0x80500000, 0x80500000,
                   bytes.fromhex("3685a3a4"), DEV, 0x030000, FORM_PAYLOAD)
        bw, nw, fw2, firstw = landing(cw)
        bp, np_, fp, firstp = landing(cp)
        add("C29", "the same payload lands as 'RLXU'+%d bytes in whole form "
            "and as 'cr6c'+%d bytes in payload form" % (BODY + len(cr6c),
                                                        len(cr6c)),
            bw == bp == 0x030000 and firstw == b"RLXU" and firstp == b"cr6c"
            and nw == BODY + len(cr6c) and np_ == len(cr6c)
            and nw - np_ == BODY,
            "whole %r+%d, payload %r+%d, the %d-byte prefix is the difference"
            % (firstw, nw, firstp, np_, nw - np_))
        add("C29b", "and the report says whether the landing base is one the "
            "loader scans, in both directions",
            any("IS one of the loader's six" in ln
                for ln in landing_lines(cw))
            and any("is NOT one of the loader's six" in ln for ln in
                    landing_lines(build(cr6c, 7, 0x80500000, 0x80500000,
                                        bytes.fromhex("3685a3a4"), DEV,
                                        0x070000, FORM_PAYLOAD))),
            "0x030000 is a scan candidate, 0x070000 is not")

        # --------------------------- C27  the licensed build, end to end
        # ⚠️ THE ROW BELOW IS A FIXTURE, NOT A LICENCE.  It is written by this
        # control so that the permitting arm can be exercised at all, and it
        # names a synthetic payload that is no image of anything.  Only the
        # owner's own words on the date they were said make a real one; what
        # these tools enforce is that a row exists, parses and names exactly
        # this write (`flashguard.parse_licence`'s own note).
        lic_p = os.path.join(tmp, "licence.md")
        pay8 = _sample(8192)
        nb8 = len(pay8)          # payload form: the landing length
        rowl = "2026-10-04\t%s" % flashguard.licence_payload(
            0x020000, nb8, "rescue", hashlib.sha256(pay8).hexdigest())
        with open(lic_p, "w") as fh:
            fh.write("# a FIXTURE standing in for the owner's licence\n\n"
                     "```owner-yes\n%s\n```\n" % rowl)
        rc_nolic, _ = run(["--flash-at", "0x020000",
                           "--flash-form", "payload"], "r1.rlxu")
        rc_lic, o_lic = run(["--flash-at", "0x020000",
                             "--flash-form", "payload",
                             "--owner-yes", lic_p], "r2.rlxu")
        # and the form arm of the licence: the same row does not cover the
        # whole-container landing, because that is 160 more bytes
        rc_wform, _ = run(["--flash-at", "0x020000", "--flash-form", "whole",
                           "--owner-yes", lic_p], "r3.rlxu")
        built = os.path.join(tmp, "r2.rlxu")
        blob2 = open(built, "rb").read() if os.path.exists(built) else b""
        signed = blob2[FLASH_OFF:FORM_OFF + 4]
        add("C27", "0x020000 is REFUSED without the licence and BUILT with "
            "it, and the built container SIGNS 0x00020000 and 'PAYL'",
            rc_nolic == 3 and rc_lic == 0
            and signed.hex() == "000200005041594c"
            and "the owner's yes of 2026-10-04" in o_lic,
            "no licence %s, licence %s, fields %s"
            % (rc_nolic, rc_lic, signed.hex() or "no file"))
        add("C27b", "and that row does not license the WHOLE-container "
            "landing at the same base", rc_wform == 3,
            "the licence names the landing length, which the form decides")

        # --------------------------- C20  round trip on disk
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
                       "--flash-at", "0x030000", "--flash-form", "whole"])
            rc2 = main(["verify", o, "--dev-seed", "--stock-loader"])
            rc3 = main(["verify", o, "--dev-seed", "--write-at", "0x030000",
                        "--write-form", "whole"])
            rc4 = main(["verify", o, "--dev-seed", "--write-at", "0x020000",
                        "--write-form", "whole"])
            rc5 = main(["verify", o, "--dev-seed", "--write-at", "0x030000",
                        "--write-form", "payload"])
        add("C20", "build then verify through the CLI, on disk, exit 0/0, and "
            "--write-at/--write-form agree 0 / disagree 1 / 1",
            rc == 0 and rc2 == 0 and rc3 == 0 and rc4 == 1 and rc5 == 1
            and os.path.getsize(o) == BODY + 8192
            and "NOT AN IMAGE" in cap.getvalue(),
            "build %d, verify %d, match %d, wrong base %d, wrong form %d, "
            "%d bytes" % (rc, rc2, rc3, rc4, rc5, os.path.getsize(o)))

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
                   help="the flash destination this container is FOR, checked "
                        "against flashguard and then SIGNED into the header.  "
                        "Nothing here writes flash; this is a refusal and a "
                        "declaration, not a write")
    b.add_argument("--flash-form", choices=("whole", "payload"), default=None,
                   help="what lands at --flash-at: the `whole` 160+n "
                        "container, or the `payload` alone with the prefix "
                        "stripped.  Required with --flash-at, SIGNED, and "
                        "compared against a writer's own --write-form")
    b.add_argument("--not-for-flash", action="store_true",
                   help="declare that this container has no flash "
                        "destination.  Exactly one of this and --flash-at is "
                        "required: omitting both is a refusal")
    b.add_argument("--owner-yes",
                   help="a file carrying the owner's dated ```owner-yes "
                        "fence, needed for a licensable destination")
    keyargs(b)
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="check an RLXU container")
    v.add_argument("container")
    v.add_argument("--pubkey-hex")
    v.add_argument("--counter", type=lambda s: int(s, 0), default=0,
                   help="the anti-rollback counter to test the version "
                        "against (default 0: today's region is erased)")
    v.add_argument("--write-at", type=lambda s: int(s, 0), default=None,
                   help="the flash offset the caller is about to write this "
                        "container to.  The container's SIGNED destination "
                        "must equal it, and an undeclared container is "
                        "refused.  Default: the caller writes nothing")
    v.add_argument("--write-form", choices=("whole", "payload"), default=None,
                   help="what the caller is about to write at --write-at.  "
                        "The container's SIGNED form must equal it; a caller "
                        "that would strip a prefix the container did not ask "
                        "it to strip is refused even when the offset agrees")
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
