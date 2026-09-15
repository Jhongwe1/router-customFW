#!/usr/bin/env python3
"""Count MIPS encodings in an artefact BY OPCODE, never by what objdump calls
them.

WHY THIS EXISTS, and it is a measurement rather than a preference.

量 2026-09-15: the rsdk binutils shipped with this project's own toolchains
print

    400664:  0231280b   0x231280b

-- the raw word, no mnemonic -- for `movn`, which is plainly SPECIAL funct
0x0B.  Forcing `-m mips:isa32` names it.

🔴 **That is NOT a defect, and the first draft of this file called it one.**
`docs/isa-payload.md` already holds the principle, under the heading *What
`objdump -m mips:3000` declines to name is a reading, not a defect*: a decoder
told MIPS-I is CORRECT to decline a MIPS-IV encoding, and `movz`/`movn` are
MIPS-IV.  The rsdk driver's default decoder is MIPS-I, so it declines them by
being right.

**The trap is one level up, and it is what this tool is for.**  A CENSUS that
decodes at one ISA level cannot see encodings from another, so a count taken
by grepping a disassembly for a mnemonic is a lower bound wearing a total's
clothes -- and on this toolchain the default level is exactly the one that
hides the encodings this project cares most about.  Decoding the words has no
ISA level at all.

A second, independent trap in the same idiom: GNU `grep -E` does not
interpret `\\t`.  `grep -cE '\\tlw\\b'` over a disassembly returns **0**, and
zero is also the answer a clean file would give.

Both are the shape this project keeps recording -- a number that is wrong in
the direction that looks like success -- so the answer is to decode the words.

Usage
    elfops.py count FILE [--ops a,b,c] [--raw --base ADDR]
    elfops.py where FILE --op NAME [--raw --base ADDR]
    elfops.py --self-test

Exit
    0  clean
    1  a finding (`where` with --expect, or count mismatch)
    3  REFUSED -- the file would not parse, so nothing is reported
"""
import argparse
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


class Refuse(Exception):
    pass


# op == 0 is SPECIAL; the key is then the funct field.  Everything else keys
# on the 6-bit opcode.
#
# 🔴 THE SOURCE, and the first draft of this comment cited a file it had not
# opened.  It said *"cross-checked against `arch/rlx/include/asm/inst.h`'s own
# enum"*, and 量 2026-09-15 that header holds `fmovz_op = 0x12` and
# `fmovn_op = 0x13` -- the COP1 FLOATING-POINT variants, a different field of
# a different opcode -- and no integer `movz`/`movn` at all.  A citation
# which, if anyone had followed it, would have supplied the wrong numbers.
#
# The values are written from the MIPS ISA definition.  The SECOND source is
# empirical and it is control C7: `tools/hazlint`'s independently written
# classifier, over a real artefact, compared ADDRESS FOR ADDRESS rather than
# by count.  That is a stronger second source than a header would have been,
# because it can disagree about a file that exists.
SPECIAL = {
    0x0A: "movz",
    0x0B: "movn",
    0x0C: "syscall",
    0x0D: "break",
    0x0F: "sync",
    0x34: "teq",
    0x30: "tge",
    0x31: "tgeu",
    0x32: "tlt",
    0x33: "tltu",
    0x36: "tne",
}
OPCODE = {
    0x22: "lwl",
    0x26: "lwr",
    0x2A: "swl",
    0x2E: "swr",
    0x30: "ll",
    0x38: "sc",
    0x31: "lwc1",
    0x39: "swc1",
    0x33: "lwc3",
    0x3B: "swc3",
}
NAMES = sorted(set(SPECIAL.values()) | set(OPCODE.values()))

DEFAULT_OPS = ("break", "movz", "movn", "sync", "lwl", "lwr", "swl", "swr",
               "ll", "sc")


def classify(w):
    """The name of this word's encoding, or None.  One place, one rule."""
    op = (w >> 26) & 0x3F
    if op == 0:
        return SPECIAL.get(w & 0x3F)
    return OPCODE.get(op)


def exec_spans(blob, raw=False, base=0):
    """[(name, vma, bytes)] for every executable span.

    On an ELF: PROGBITS sections carrying SHF_EXECINSTR.  Raw: the whole file
    at `base`, which is how `stage2.bin` and a loader dump are read.
    """
    if raw:
        return [("(raw)", base, blob)]
    if blob[:4] != b"\x7fELF":
        raise Refuse("not an ELF and --raw was not given")
    if blob[4] != 1:
        raise Refuse("not ELFCLASS32")
    if blob[5] != 2:
        raise Refuse("not big-endian -- this project's target is EB and a "
                     "little-endian file here is a different device")
    shoff, = struct.unpack(">I", blob[32:36])
    shentsize, shnum, shstrndx = struct.unpack(">HHH", blob[46:52])
    if shoff == 0 or shnum == 0:
        raise Refuse("no section headers; use --raw --base ADDR")

    def sh(i):
        o = shoff + i * shentsize
        if o + 24 > len(blob):
            raise Refuse("section header %d runs past the end of the file" % i)
        return struct.unpack(">IIIIII", blob[o:o + 24])

    _n, _t, _f, _a, stroff, _s = sh(shstrndx)
    out = []
    for i in range(shnum):
        name, typ, flags, addr, off, size = sh(i)
        if typ != 1 or not (flags & 0x4) or size == 0:
            continue
        end = blob.index(b"\0", stroff + name)
        nm = blob[stroff + name:end].decode("ascii", "replace")
        out.append((nm, addr, blob[off:off + size]))
    if not out:
        raise Refuse("no executable PROGBITS section -- an artefact with no "
                     "code is not a clean artefact, it is the wrong file")
    return out


def scan(spans, ops, lo=None, hi=None):
    """(counts, sites).  `sites` is [(vma, name, word)] in address order.

    🔴 `lo`/`hi` are not a convenience.  量 2026-09-15: scanning ALL of
    `stage2.bin` -- a loader dump with code and data in one blob -- finds
    **twelve** `movn`, where `tools/hazlint`'s K6a pins six.  The six extra
    are all the same word, `0x0000004B`, at 0x8040D800/820/840 and
    0x8040DB00/B20/B40 -- a data table, decoded as `movn $0,$0,$0`.  An
    opcode census over a mixed blob OVER-COUNTS, and the over-count is
    indistinguishable from a measurement.  An ELF says which bytes are code;
    a raw dump does not, and this is where you say so.
    """
    want = set(ops)
    counts = dict((o, 0) for o in ops)
    sites = []
    for _nm, vma, data in spans:
        n = len(data) - (len(data) % 4)
        for k in range(0, n, 4):
            a = vma + k
            if (lo is not None and a < lo) or (hi is not None and a >= hi):
                continue
            w, = struct.unpack(">I", data[k:k + 4])
            c = classify(w)
            if c in want:
                counts[c] += 1
                sites.append((a, c, w))
    return counts, sites


def hazlint_stage2_pins():
    """The `stage2.bin` code/data boundary and K6a's pinned address lists.

    READ OUT OF `tools/hazlint`, not restated here.  The boundary is a fact
    about the artefact and has exactly one owner; this tool is a second
    implementation of the DECODER, not a second opinion about where the
    loader's code ends.  `tools/flashmap.py` imports `flashwin`'s rule for
    the same reason rather than copying it.

    Parsed rather than imported because `tools/hazlint` has no `.py`
    extension and importing it would run its module body for a constant.
    """
    import ast
    import re as _re
    src = io_open_text(os.path.join(HERE, "hazlint"))
    out = {}
    for k in ("STAGE2_CODE_HI", "STAGE2_MOVZ", "STAGE2_MOVN"):
        m = _re.search(r"^%s\s*=\s*((?:[^\n]|\n\s+)+?)\n(?=\S|\n)" % k,
                       src, _re.M)
        if not m:
            raise Refuse("tools/hazlint no longer defines %s, so the "
                         "cross-check has lost its other implementation" % k)
        out[k] = ast.literal_eval(m.group(1).strip())
    return out


def io_open_text(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def read(path, raw, base):
    if not os.path.exists(path):
        raise Refuse("no file at %s" % path)
    return exec_spans(open(path, "rb").read(), raw, base)


def cmd_count(path, ops, raw, base, quiet=False, lo=None, hi=None):
    spans = read(path, raw, base)
    counts, _sites = scan(spans, ops, lo, hi)
    if not quiet:
        for nm, vma, data in spans:
            print("  span %-12s vma 0x%08X  %d bytes" % (nm, vma, len(data)))
    total = 0
    for o in ops:
        print("  %-8s %d" % (o, counts[o]))
        total += counts[o]
    print("total %d over %d span(s)" % (total, len(spans)))
    return 0


def cmd_where(path, op, raw, base, expect=None, lo=None, hi=None):
    if op not in NAMES:
        raise Refuse("%s is not an encoding this tool decodes; it knows %s"
                     % (op, ", ".join(NAMES)))
    spans = read(path, raw, base)
    counts, sites = scan(spans, [op], lo, hi)
    for vma, _c, w in sites:
        print("  0x%08X  %08x" % (vma, w))
    print("%s %d" % (op, counts[op]))
    if expect is not None and counts[op] != expect:
        print("FINDING: expected %d, found %d" % (expect, counts[op]))
        return 1
    return 0


# ---------------------------------------------------------------------------
# Controls.  A tool that cannot fail proves nothing.
# ---------------------------------------------------------------------------

def _be(words):
    return b"".join(struct.pack(">I", w) for w in words)


def _fake_elf(text_words, vma=0x400000):
    """A minimal big-endian ELF32 with one PROGBITS+EXECINSTR section.

    Built rather than checked in, because a fixture binary in this repository
    would be a file nobody can regenerate.
    """
    text = _be(text_words)
    shstr = b"\0.text\0.shstrtab\0"
    ehsize, shentsize, shnum = 52, 40, 3
    off_text = ehsize
    off_shstr = off_text + len(text)
    shoff = off_shstr + len(shstr)
    eh = (b"\x7fELF" + bytes([1, 2, 1, 0]) + b"\0" * 8
          + struct.pack(">HHIIIIIHHHHHH", 2, 8, 1, vma, 0, shoff, 0x1001,
                        ehsize, 32, 0, shentsize, shnum, 2))
    sh0 = struct.pack(">IIIIIIIIII", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    sh1 = struct.pack(">IIIIIIIIII", 1, 1, 0x6, vma, off_text, len(text),
                      0, 0, 4, 0)
    sh2 = struct.pack(">IIIIIIIIII", 7, 3, 0, 0, off_shstr, len(shstr),
                      0, 0, 1, 0)
    return eh + text + shstr + sh0 + sh1 + sh2


def self_test():
    n = ok = 0

    def case(label, fn):
        nonlocal n, ok
        n += 1
        try:
            fn()
            ok += 1
            print("  ok    %s" % label)
        except AssertionError as e:
            print("  FAIL  %s -- %s" % (label, e))
        except Exception as e:
            print("  FAIL  %s -- %s: %s" % (label, type(e).__name__, e))

    def refuses(fn, why):
        try:
            fn()
        except Refuse:
            return
        raise AssertionError("did not refuse: %s" % why)

    print("=== elfops controls ===")

    def c1():
        assert classify(0x0000000D) == "break", "break is SPECIAL funct 0x0D"
        assert classify(0x0231280B) == "movn", "the word objdump would not name"
        assert classify(0x0231280A) == "movz"
        assert classify(0x0000000F) == "sync"
        assert classify(0x89420001) == "lwl", "opcode 0x22"
        assert classify(0xC1420000) == "ll", "opcode 0x30"
        assert classify(0xE1490000) == "sc", "opcode 0x38"
        assert classify(0x01091020) is None, "`add` is not an encoding we count"
        assert classify(0x00000000) is None, "`nop` is SPECIAL funct 0, not ours"
    case("C1  the decoder names the encodings objdump declines to", c1)

    def c2():
        # The POSITIVE control.  A synthesised span with a known census.
        words = [0x00000000, 0x0000000D, 0x01091020, 0x0231280B,
                 0x0231280A, 0x0000000D, 0x89420001, 0x0000000F]
        spans = exec_spans(_fake_elf(words))
        counts, sites = scan(spans, DEFAULT_OPS)
        assert counts["break"] == 2, counts
        assert counts["movn"] == 1 and counts["movz"] == 1, counts
        assert counts["lwl"] == 1 and counts["sync"] == 1, counts
        assert counts["ll"] == 0 and counts["sc"] == 0, counts
        assert len(sites) == 6, sites
        assert sites[0][0] == 0x400004, "the first site's vma"
        assert sites[-1][0] == 0x40001C, "the last site's vma"
    case("C2  a synthesised span is counted exactly, with its addresses", c2)

    def c3():
        # The NEGATIVE half: a span with none of them must read zero, and a
        # zero from an EMPTY scan must not look like a zero from a clean one.
        spans = exec_spans(_fake_elf([0x01091020, 0x00000000, 0x8C420000]))
        counts, sites = scan(spans, DEFAULT_OPS)
        assert sum(counts.values()) == 0 and not sites, counts
        assert len(spans) == 1 and len(spans[0][2]) == 12, "the span was read"
    case("C3  a clean span reads zero AND is shown to have been read", c3)

    def c4():
        refuses(lambda: exec_spans(b"not an elf at all"),
                "a non-ELF without --raw")
        refuses(lambda: exec_spans(b"\x7fELF" + bytes([1, 1, 1, 0]) + b"\0" * 60),
                "a little-endian ELF")
        refuses(lambda: exec_spans(b"\x7fELF" + bytes([2, 2, 1, 0]) + b"\0" * 60),
                "an ELFCLASS64 file")
        # An ELF with no executable content is the WRONG FILE, not a clean
        # one, and this is the trap one door down: 量 2026-09-15,
        # `tools/hazlint` handed an `ar` archive does not refuse -- it falls
        # through to raw mode, decodes the archive headers and symbol table as
        # instructions, and reports `212 violation(s)`.  A container scanned
        # as code produces a number, and the number is about nothing.
        refuses(lambda: exec_spans(_fake_elf([])), "an ELF with an empty .text")
    case("C4  four malformed inputs are refused rather than scored", c4)

    def c5():
        # RAW mode, and the reason it exists: `stage2.bin` is a loader dump
        # with no ELF headers at all.
        words = [0x0000000D, 0x0231280B]
        spans = exec_spans(_be(words), raw=True, base=0x80400000)
        counts, sites = scan(spans, DEFAULT_OPS)
        assert counts["break"] == 1 and counts["movn"] == 1, counts
        assert sites[0][0] == 0x80400000 and sites[1][0] == 0x80400004, sites
    case("C5  raw mode scores the same words at the base it is given", c5)

    def c6():
        # A trailing partial word must be dropped, not read past.
        spans = exec_spans(_be([0x0000000D]) + b"\xAB\xCD", raw=True)
        counts, _ = scan(spans, DEFAULT_OPS)
        assert counts["break"] == 1, counts
    case("C6  a span that is not a whole number of words does not run off", c6)

    # C7 -- the cross-check against an INDEPENDENT implementation's pinned
    # number.  `tools/hazlint`'s K6a pins `stage2.bin` at movz 12 / movn 6;
    # this decoder was written without reading that code.  Two
    # implementations, one artefact, one expected pair.
    stage2 = os.path.join(os.environ.get("FWRE_WORK", "/home/key/fwre-work"),
                          "stage2.bin")
    if os.path.exists(stage2):
        def c7():
            pins = hazlint_stage2_pins()
            hi = pins["STAGE2_CODE_HI"]
            spans = exec_spans(open(stage2, "rb").read(), raw=True,
                               base=0x80400000)
            _c, sites = scan(spans, ["movz", "movn"], None, hi)
            movz = sorted(a for a, c, _w in sites if c == "movz")
            movn = sorted(a for a, c, _w in sites if c == "movn")
            # ADDRESSES, not counts.  hazlint's own K6 comment says why: "a
            # count cannot see a word getting the wrong ANSWER as long as the
            # total is unchanged -- which is exactly what the 2026-08-27
            # defect was."
            assert movz == pins["STAGE2_MOVZ"], \
                "movz addresses differ from hazlint's pin: %s" \
                % [hex(x) for x in movz]
            assert movn == pins["STAGE2_MOVN"], \
                "movn addresses differ from hazlint's pin: %s" \
                % [hex(x) for x in movn]
        case("C7  the code region agrees with hazlint's K6a ADDRESS pins, "
             "one for one", c7)

        def c8():
            # 🔴 THE FINDING THAT MADE `--range` EXIST, kept as a control.
            # Over the WHOLE dump this decoder reads six extra `movn`, all of
            # them the same word, all of them above the code boundary.  They
            # are a data table read as instructions.  The first draft of C7
            # scanned the whole file and reported `movn 12` against hazlint's
            # 6, which looked like two implementations disagreeing about an
            # ENCODING and was two implementations disagreeing about a RANGE.
            pins = hazlint_stage2_pins()
            hi = pins["STAGE2_CODE_HI"]
            spans = exec_spans(open(stage2, "rb").read(), raw=True,
                               base=0x80400000)
            _c, all_sites = scan(spans, ["movn"])
            extra = [(a, w) for a, c, w in all_sites if a >= hi]
            assert len(extra) == 6, \
                "the data region's spurious movn count moved: %d" % len(extra)
            assert all(w == 0x0000004B for _a, w in extra), \
                "the spurious words are not all 0x0000004B any more"
            assert len(all_sites) == 6 + len(pins["STAGE2_MOVN"]), \
                "whole-file movn is no longer code + data"
        case("C8  a whole-blob scan OVER-counts, and by exactly the data "
             "table that made it", c8)
    else:
        # The census parses a skip line as `  skip   <label>  <reason>`
        # with two or more spaces on each side of the label, and the label is
        # what `tools/ci-expected.tsv` keys `covers` on.  A skip line in any
        # other shape is a case that vanished with neither a FAIL nor a skip,
        # which `tools/ci-census.py`'s own header says nothing counting skip
        # LINES could have seen.
        print("  skip   %-52s %s"
              % ("stage2.bin",
                 "absent -- 2 cases; C7/C8 are the only controls here that "
                 "use a SECOND implementation (hazlint's K6a address pins), "
                 "and stage2.bin is this unit's own bootloader and cannot be "
                 "committed"))

    print("self-test: %d of %d" % (ok, n))
    return 0 if ok == n else 1


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mode", nargs="?", choices=["count", "where"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--ops", default=",".join(DEFAULT_OPS))
    ap.add_argument("--op")
    ap.add_argument("--expect", type=int)
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("--base", default="0")
    ap.add_argument("--range", dest="rng",
                    help="LO:HI, addresses only. A raw dump does not say "
                         "which bytes are code and a scan of its data is an "
                         "over-count that looks like a measurement")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test()
        if not a.mode or not a.file:
            ap.print_help()
            return 3
        base = int(a.base, 0)
        lo = hi = None
        if a.rng:
            if ":" not in a.rng:
                raise Refuse("--range wants LO:HI")
            x, y = a.rng.split(":", 1)
            lo, hi = int(x, 0), int(y, 0)
            if hi <= lo:
                raise Refuse("--range %s is empty or inverted" % a.rng)
        if a.mode == "count":
            ops = [o.strip() for o in a.ops.split(",") if o.strip()]
            for o in ops:
                if o not in NAMES:
                    raise Refuse("%s is not an encoding this tool decodes" % o)
            return cmd_count(a.file, ops, a.raw, base, a.quiet, lo, hi)
        if a.mode == "where":
            if not a.op:
                raise Refuse("where needs --op")
            return cmd_where(a.file, a.op, a.raw, base, a.expect, lo, hi)
    except Refuse as e:
        print("REFUSED: %s" % e)
        return 3
    return 3


if __name__ == "__main__":
    sys.exit(main())
