#!/usr/bin/env python3
"""Count MIPS primary opcodes by linear scan over 4-byte aligned big-endian words.

Why a linear scan rather than a disassembler
--------------------------------------------
For a raw image loaded at a 4-byte aligned address, every instruction in the
file lies at a file offset congruent to 0 mod 4. Scanning all aligned words is
therefore a *superset* of the instructions: it can count data as code, but it
cannot miss an instruction. So every count this prints is an upper bound, and
exactly one kind of result is rigorous -- a zero. That is the result the
lwl/lwr question needs, which is why the cheap instrument is the right one.

The expensive instrument is still required when a count is non-zero: each hit
has to be adjudicated as code or data, and this prints the addresses so that it
can be.

This does not use `objdump -d`. On a binary whose section headers have been
stripped -- which is what /bin/boa on this device is -- `objdump -d` emits no
disassembly at all and every mnemonic count comes back 0. A tool that cannot
see is still willing to report a number.

Usage
    opcount.py FILE [--base ADDR] [--range LO:HI] [--elf] [--profile]

    --base    virtual address of file offset 0 (raw images)
    --range   restrict to a file-offset range, LO:HI, hex accepted
    --elf     take the scan range from the executable PT_LOAD segments
    --profile per-block signals, to tell code from strings and symbol tables
    --block   profile block size in bytes (default 4096)
"""

import struct
import sys

# Primary opcode (bits 31:26) -> name, and the ISA level that first defines it.
# Only the rows that decide something for this project are named; the rest are
# printed by number.
NAMED = {
    0x00: ("SPECIAL", ""), 0x01: ("REGIMM", ""), 0x02: ("j", ""), 0x03: ("jal", ""),
    0x04: ("beq", ""), 0x05: ("bne", ""), 0x06: ("blez", ""), 0x07: ("bgtz", ""),
    0x08: ("addi", ""), 0x09: ("addiu", ""), 0x0A: ("slti", ""), 0x0B: ("sltiu", ""),
    0x0C: ("andi", ""), 0x0D: ("ori", ""), 0x0E: ("xori", ""), 0x0F: ("lui", ""),
    0x10: ("COP0", ""), 0x11: ("COP1/FPU", "FPU"), 0x12: ("COP2", ""),
    # 0x13 read ("COP1X", "MIPS-IV") until 2026-08-27, which is the answer for a
    # MIPS-IV core. This one is MIPS-I (Config.M = 0, measured), and there the
    # opcode is COP3 -- the coprocessor this part wires its 16 KiB I-MEM and
    # 8 KiB D-MEM window registers to. Same defect, same day, in tools/hazlint,
    # whose version note carries the two sources; the short form is that COP3 is
    # MIPS I and II, MIPS III removed it, MIPS IV reused the opcode.
    #
    # The level column says "MIPS-I, optional" rather than "" because MIPS IV
    # Rev 3.2 A 8.3.4 calls COP3 "optional and implementation-specific" at those
    # levels -- so unlike COP0 and COP2 a hit here is not settled by the ISA.
    0x13: ("COP3", "MIPS-I, optional"),
    0x14: ("beql", "MIPS-II"), 0x15: ("bnel", "MIPS-II"),
    0x16: ("blezl", "MIPS-II"), 0x17: ("bgtzl", "MIPS-II"),
    0x1C: ("SPECIAL2", "MIPS32"), 0x1D: ("jalx", "MIPS16"),
    0x1F: ("SPECIAL3", "MIPS32r2"),
    0x20: ("lb", ""), 0x21: ("lh", ""), 0x22: ("lwl", "MIPS-I unaligned"),
    0x23: ("lw", ""), 0x24: ("lbu", ""), 0x25: ("lhu", ""),
    0x26: ("lwr", "MIPS-I unaligned"),
    0x28: ("sb", ""), 0x29: ("sh", ""), 0x2A: ("swl", "MIPS-I unaligned"),
    0x2B: ("sw", ""), 0x2E: ("swr", "MIPS-I unaligned"),
    0x2F: ("cache", "MIPS-II"),
    0x30: ("ll", "MIPS-II"), 0x31: ("lwc1", "FPU"),
    # 0x33 read ("pref", "MIPS-IV") until 2026-08-27 and it is the SAME
    # reallocation as 0x13's: MIPS I puts LWC3 here and SWC3 at 0x3B, MIPS
    # III shows both as removed, MIPS IV gives 0x33 to PREF. 量 with this
    # project's own toolchain: `-march=mips1` REFUSES `pref` and ACCEPTS
    # `lwc3` at the same 32 bits.
    0x33: ("lwc3", "MIPS-I, optional"), 0x3B: ("swc3", "MIPS-I, optional"),
    0x35: ("ldc1", "FPU"), 0x38: ("sc", "MIPS-II"), 0x39: ("swc1", "FPU"),
    0x3D: ("sdc1", "FPU"),
}

# The rows this project actually decides on. Printed with hit addresses.
DECIDES = [0x22, 0x26, 0x2A, 0x2E, 0x2F, 0x30, 0x38, 0x33,
           0x14, 0x15, 0x16, 0x17, 0x1C, 0x1F, 0x11, 0x31, 0x35, 0x39, 0x3D, 0x1D]

# Opcodes that dominate real MIPS code. Used only as a code/data signal.
COMMON = {0x00, 0x02, 0x03, 0x04, 0x05, 0x08, 0x09, 0x0C, 0x0D, 0x0E, 0x0F,
          0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B}

SPECIAL_SYNC = 0x0F   # SPECIAL funct for `sync`, MIPS-II


def elf_exec_ranges(b):
    """(offset, size, vaddr) of every executable PT_LOAD, from program headers.

    Program headers, not section headers: a stripped binary still has to be
    loadable, so the segments survive where the sections do not.
    """
    if b[:4] != b"\x7fELF" or b[4] != 1 or b[5] != 2:
        sys.exit("not a big-endian ELF32")
    phoff, = struct.unpack_from(">I", b, 0x1C)
    phentsize, phnum = struct.unpack_from(">HH", b, 0x2A)
    out = []
    for i in range(phnum):
        o = phoff + i * phentsize
        p_type, p_offset, p_vaddr, _, p_filesz, _, p_flags, _ = \
            struct.unpack_from(">8I", b, o)
        if p_type == 1 and (p_flags & 1):      # PT_LOAD, PF_X
            out.append((p_offset, p_filesz, p_vaddr))
    return out


def scan(words):
    hist = [0] * 64
    hits = {op: [] for op in DECIDES}
    sync = 0
    for addr, w in words:
        op = w >> 26
        hist[op] += 1
        if op in hits:
            hits[op].append(addr)
        if op == 0 and (w & 0x3F) == SPECIAL_SYNC and w != 0:
            sync += 1
    return hist, hits, sync


def profile(words, block=4096):
    rows, buf, start = [], [], None
    for addr, w in words:
        if start is None:
            start = addr
        buf.append(w)
        if len(buf) * 4 >= block:
            rows.append((start, buf)); buf, start = [], None
    if buf:
        rows.append((start, buf))
    print("\n  block          n   common%  zero%  ascii%   reading")
    for start, ws in rows:
        n = len(ws)
        common = sum(1 for w in ws if (w >> 26) in COMMON) * 100 // n
        zero = sum(1 for w in ws if w == 0) * 100 // n
        asc = sum(1 for w in ws if all(0x20 <= ((w >> s) & 0xFF) <= 0x7E
                                       for s in (24, 16, 8, 0))) * 100 // n
        if asc > 40:
            read = "strings"
        elif common > 80 and asc < 15:
            read = "code"
        elif zero > 60:
            read = "padding"
        else:
            read = "mixed / data"
        print("  %08x %6d   %5d  %5d  %6d   %s" % (start, n, common, zero, asc, read))


def main(argv):
    path = argv[0]
    base, rng, use_elf, want_profile, block = 0, None, False, False, 4096
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--base":
            base = int(argv[i + 1], 0); i += 2
        elif a == "--range":
            lo, hi = argv[i + 1].split(":"); rng = (int(lo, 0), int(hi, 0)); i += 2
        elif a == "--elf":
            use_elf = True; i += 1
        elif a == "--profile":
            want_profile = True; i += 1
        elif a == "--block":
            block = int(argv[i + 1], 0); i += 2
        else:
            sys.exit("unknown argument %s" % a)

    b = open(path, "rb").read()
    if use_elf:
        ranges = elf_exec_ranges(b)
    elif rng:
        ranges = [(rng[0], rng[1] - rng[0], base + rng[0])]
    else:
        ranges = [(0, len(b), base)]

    words = []
    for off, size, vaddr in ranges:
        size -= size % 4
        for k in range(0, size, 4):
            words.append((vaddr + k, struct.unpack_from(">I", b, off + k)[0]))

    print("file      %s  (%d bytes)" % (path, len(b)))
    for off, size, vaddr in ranges:
        print("scanned   file[0x%x .. 0x%x)  ->  vma[0x%x .. 0x%x)"
              % (off, off + size, vaddr, vaddr + size))
    print("words     %d" % len(words))
    if not words:
        sys.exit("nothing to scan")

    hist, hits, sync = scan(words)

    if want_profile:
        profile(words, block)

    print("\n  primary opcode histogram (all 64 bins, count > 0)")
    for op in range(64):
        if hist[op]:
            name, isa = NAMED.get(op, ("-", ""))
            print("  0x%02x %-10s %8d  %s" % (op, name, hist[op], isa))

    print("\n  what this project decides on")
    print("  %-12s %-18s %8s  %s" % ("opcode", "instruction", "count", "first hits"))
    for op in DECIDES:
        name, isa = NAMED[op]
        h = hits[op]
        where = " ".join("%08x" % a for a in h[:6]) + (" ..." if len(h) > 6 else "")
        print("  0x%02x         %-18s %8d  %s" % (op, name, len(h), where))
    print("  SPECIAL/0x0f %-18s %8d" % ("sync (MIPS-II)", sync))

    four = sum(len(hits[op]) for op in (0x22, 0x26, 0x2A, 0x2E))
    print("\n  lwl + lwr + swl + swr = %d   (upper bound: a linear scan counts data as code)"
          % four)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
