#!/usr/bin/env python3
"""Count MIPS primary opcodes by linear scan over 4-byte aligned big-endian words.

Why a linear scan rather than a disassembler
--------------------------------------------
For a raw image of 32-bit MIPS loaded at a 4-byte aligned address, every
instruction in the file lies at a file offset congruent to 0 mod 4. Scanning all
aligned words is therefore a *superset* of the instructions: it can count data
as code, but it cannot miss an instruction. So every count this prints is an
upper bound, and exactly one kind of result is rigorous -- a zero. That is the
result the lwl/lwr question needs, which is why the cheap instrument is the
right one.

**The superset claim holds only where the code is 32-bit MIPS, and that is a
precondition to check rather than assume.** Corrected 2026-08-27: this unit's
own vendor kernel contains MIPS16 -- two-byte instructions, entered with `jalx`,
in and around the `.iram` section at `0x802B8000` -- and in such a region a
4-byte-aligned scan misses half the instructions outright and reads the other
half glued to a neighbour. There, a zero is not a result. `--mips16` is the
precondition test, and `notes/vendor-kernel-isa.md` §4.2 is where the finding
lives. The six vendor `boa`/`busybox` and `stage2.bin` were re-checked against
it and are clean, so the counts this project already has are unaffected; the
sentence that was wrong is fixed rather than left standing because its
conclusions survived.

The expensive instrument is still required when a count is non-zero: each hit
has to be adjudicated as code or data, and this prints the addresses so that it
can be.

This does not use `objdump -d`. On a binary whose section headers have been
stripped -- which is what /bin/boa on this device is -- `objdump -d` emits no
disassembly at all and every mnemonic count comes back 0. A tool that cannot
see is still willing to report a number.

Adjudicating a non-zero count: --pairs
--------------------------------------
The four unaligned instructions are emitted in pairs -- `lwl rt,k(b)` with
`lwr rt,k+3(b)` on a big-endian target, and the mirror image on a little-endian
one. `--pairs` looks for that idiom instead of for single opcodes: same rt, same
base register, byte offsets exactly three apart, within a few words of each
other. Four fields have to agree at once, so data words do not produce it in
quantity, and the pair's *orientation* is a second reading -- a big-endian image
must yield big-endian pairs, and if it yields little-endian ones the scan or the
load address is wrong. That makes this the instrument for a count that is not a
zero, where the plain histogram can only report an upper bound.

It is still not a disassembler. A paired hit inside a data island can happen;
what it cannot do is happen 84 times in a row.

Usage
    opcount.py FILE [--base ADDR] [--range LO:HI] [--elf] [--profile] [--pairs]

    --base    virtual address of file offset 0 (raw images)
    --range   restrict to a file-offset range, LO:HI, hex accepted
    --elf     take the scan range from the executable PT_LOAD segments
    --profile per-block signals, to tell code from strings and symbol tables
    --block   profile block size in bytes (default 4096)
    --pairs   report the lwl/lwr and swl/swr idiom, with its orientation
    --gap     how many words apart a pair may sit (default 4)
    --mips16  precondition test: is any of the scanned range MIPS16?
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
    # 0x2F read ("cache", "MIPS-II") until 2026-08-28, and the instrument that
    # refuted it landed in the same commit that left it standing. 量, vendor
    # binutils via tools/isa-probe.sh: `cache 0x11,0($4)` is REJECTED for
    # -march=mips1 AND -march=mips2 AND -march=lx4180, and ACCEPTED for
    # rlx4181/rlx5181/rlx5281/rlx4281. CACHE is MIPS-III/MIPS32; the RLX cores
    # carry it as an extension. This is the third row this project has had to
    # re-level the same way, after 0x13 COP1X->COP3 and 0x33 pref->lwc3.
    #
    # It is NOT evidence that this is a MIPS32 core -- `Config.M = 0` is 量 and
    # says otherwise. It is an extension on an R3000-class CP0.
    0x2F: ("cache", "MIPS-III/32; rlx4181 ext"),
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


PARTNER = {0x22: 0x26, 0x26: 0x22, 0x2A: 0x2E, 0x2E: 0x2A}
LEFT = {0x22, 0x2A}       # lwl, swl -- the halves whose offset is lower on BE


def _soff(imm):
    return imm - 0x10000 if imm & 0x8000 else imm


def find_pairs(words, gap=4):
    """The lwl/lwr and swl/swr idiom: same rt, same base, offsets 3 apart.

    Returns (pairs, unpaired) where a pair is
    (kind, addr_first, addr_second, distance_in_words, endianness).

    `endianness` is read off the pair rather than assumed: on a big-endian
    target the `l`-half sits at the LOWER byte offset. It is reported so that a
    scan of a big-endian image that comes back full of little-endian pairs is
    visible as a broken scan instead of as an answer.
    """
    n = len(words)
    taken = set()
    out = []
    for i in range(n):
        if i in taken:
            continue
        a1, w1 = words[i]
        op1 = w1 >> 26
        if op1 not in PARTNER:
            continue
        rs1, rt1, imm1 = (w1 >> 21) & 31, (w1 >> 16) & 31, w1 & 0xFFFF
        for j in range(i + 1, min(i + 1 + gap, n)):
            if j in taken:
                continue
            a2, w2 = words[j]
            if a2 != a1 + 4 * (j - i):
                break                      # ranges are not contiguous here
            if (w2 >> 26) != PARTNER[op1]:
                continue
            rs2, rt2, imm2 = (w2 >> 21) & 31, (w2 >> 16) & 31, w2 & 0xFFFF
            if rs1 != rs2 or rt1 != rt2:
                continue
            d = _soff(imm2) - _soff(imm1)
            if abs(d) != 3:
                continue
            lo_is_left = (d > 0) if op1 in LEFT else (d < 0)
            kind = "lw" if op1 in (0x22, 0x26) else "sw"
            out.append((kind, a1, a2, j - i, "BE" if lo_is_left else "LE"))
            taken.add(i)
            taken.add(j)
            break
    unpaired = {op: [] for op in PARTNER}
    for i in range(n):
        if i in taken:
            continue
        a, w = words[i]
        op = w >> 26
        if op in PARTNER:
            unpaired[op].append(a)
    return out, unpaired


def report_pairs(words, gap):
    prs, unpaired = find_pairs(words, gap)
    be = sum(1 for p in prs if p[4] == "BE")
    le = len(prs) - be
    nlw = sum(1 for p in prs if p[0] == "lw")
    print("\n  unaligned-access idiom  (same rt, same base, offsets 3 apart, "
          "within %d words)" % gap)
    print("  paired sites      %d      lwl/lwr %d   swl/swr %d" % (len(prs), nlw, len(prs) - nlw))
    print("  orientation       BE %d   LE %d" % (be, le))
    dist = {}
    for p in prs:
        dist[p[3]] = dist.get(p[3], 0) + 1
    print("  distance (words)  " + "  ".join("%d:%d" % (k, dist[k]) for k in sorted(dist)))
    left = sum(len(unpaired[op]) for op in unpaired)
    print("  unpaired halves   %d      lwl %d  lwr %d  swl %d  swr %d"
          % (left, len(unpaired[0x22]), len(unpaired[0x26]),
             len(unpaired[0x2A]), len(unpaired[0x2E])))
    if prs:
        print("  first pairs       " +
              " ".join("%08x/%08x" % (p[1], p[2]) for p in prs[:6]) +
              (" ..." if len(prs) > 6 else ""))
    if left:
        rest = sorted(a for op in unpaired for a in unpaired[op])
        print("  unpaired at       " + " ".join("%08x" % a for a in rest[:8]) +
              (" ..." if left > 8 else ""))
    return prs, unpaired


JALX = 0x1D
J_FORMAT = {0x02: "j", 0x03: "jal", JALX: "jalx"}


def _plausible(w):
    """A word that could be a 32-bit MIPS instruction.

    The naive test -- primary opcode in COMMON -- calls every small integer an
    instruction, because a small integer has opcode 0x00 = SPECIAL, so a table
    of small integers scores as 100 % code. Requiring the word to be exactly
    zero (nop) or at least 0x1000 removes those tables and keeps every real
    encoding: the smallest genuine SPECIAL forms used here, `sll rd,rt,1` =
    0x00031040 and `jr ra` = 0x03e00008, are both far above it.
    """
    if w == 0:
        return True
    if w < 0x1000:
        return False
    return (w >> 26) in COMMON


def _codeness(words, i, win=64):
    lo, hi = max(0, i - win), min(len(words), i + win)
    return sum(1 for k in range(lo, hi) if _plausible(words[k][1])) * 100 // (hi - lo)


def report_mips16(words, ranges):
    """Is any of the scanned range MIPS16? -- the precondition for every count
    above it.

    `jalx` is ONE way 32-bit code reaches MIPS16 code, and its 26-bit J-format
    field names a word address in the current 256 MB segment. So the test is: do
    opcode-0x1d words that sit in windows reading as 32-bit code have targets
    that land INSIDE the scanned range?

    ⚠️ **It is not the only way, and this test will not fire on the other one.**
    Bit 0 of a target address is the ISA-mode bit, so `jr`/`jalr` through a
    register holding an odd address enters MIPS16 -- which is how a MIPS16
    function reached through a pointer or an ops struct is called, and a
    Realtek `.iram` fast path is built out of exactly those. A region entered
    only that way is invisible here. Searched in this unit's kernel and not
    found (29 words hold an odd in-image address, all of them in data), so the
    reading for THIS artefact stands; not-found is not absent, and a stronger
    test would have to follow the odd constants.

    A 26-bit field ranges over 256 MB. If the scanned ranges total r bytes,
    random data puts about r/2^28 of its targets inside them -- for a 3 MB
    image, 1.3 %. So the base rate is the control, and `jal` and `j` are printed
    beside it because they are certainly jumps: whatever fraction THEY land
    in-range is what a jump instruction looks like on this artefact.

    Returns the number of in-range jalx targets, or -1 when the control did not
    fire. Zero means the range passed the precondition; a positive number means
    the counts above are not upper bounds and the region has to be disassembled
    instead of scanned.
    """
    # The UNION of the scanned ranges, not their convex hull. Corrected
    # 2026-08-28: with two PT_LOADs the hull includes the gap between them, so a
    # target landing in bytes that were never read counted as in-range, and the
    # base-rate control was computed over that gap too -- inflated 437x on the
    # two-segment case. hazlint's mips16_in_spans has always used the union, so
    # the project's two implementations of one test disagreed by construction.
    spans = sorted((v, v + (s - s % 4)) for _, s, v in ranges)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    in_range = lambda t: any(a <= t < b for a, b in merged)
    lo, hi = merged[0][0], merged[-1][1]
    span = sum(b - a for a, b in merged)
    base_pct = 100.0 * span / (1 << 28)

    out = {}
    for op in (JALX, 0x03, 0x02):
        sites, inr = [], []
        for i, (addr, w) in enumerate(words):
            if (w >> 26) != op:
                continue
            if _codeness(words, i) < 80:
                continue
            t = (addr & 0xF0000000) | ((w & 0x03FFFFFF) << 2)
            sites.append((addr, t))
            if in_range(t):
                inr.append(t)
        out[op] = (sites, inr)

    print("\n  MIPS16 precondition   scanned extent 0x%08x .. 0x%08x, %d bytes "
          "in %d range(s)" % (lo, hi, span, len(merged)))
    print("  a 26-bit J field spans 256 MB, so random data lands %.2f%% of its "
          "targets in range" % base_pct)
    print("  %-6s %10s %10s %8s" % ("opcode", "in-code", "target in range", "pct"))
    for op in (JALX, 0x03, 0x02):
        sites, inr = out[op]
        pct = (100.0 * len(inr) / len(sites)) if sites else 0.0
        print("  %-6s %10d %10d %13.1f%%   %s"
              % (J_FORMAT[op], len(sites), len(inr), pct,
                 "<-- control" if op != JALX else ""))

    # The control has to have fired before EITHER verdict means anything, and
    # until 2026-08-28 this guard sat inside the `if not inr:` branch, so it
    # gated only the zero. A wrong base then produced the tool's strongest
    # claim -- MIPS16 REACHED -- on an artefact whose control landed 0/40.
    # Raised by the adversarial review; the asymmetry was the defect, not the
    # threshold.
    #
    # 量 2026-08-27: `bin/boa` scanned with `--base 0` gives jalx 0 AND jal
    # 0/515 in range, because boa loads at 0x00400000 and every jal encodes an
    # absolute VMA -- so the zero was a wrong base address, not an absence of
    # MIPS16. Under `--elf` the same file gives jal 514/515 and the same jalx 0,
    # and only the second of those is a reading.
    n_jal = len(out[0x03][0])
    jal_pct = (100.0 * len(out[0x03][1]) / n_jal) if n_jal else 0.0
    inr = out[JALX][1]
    if n_jal < 20 or jal_pct < 50.0:
        print("  VERDICT  NOT ESTABLISHED -- the control did not fire:")
        print("           %d jal in code, %.1f%% landing in range. Either the "
              "base address is" % (n_jal, jal_pct))
        print("           wrong for this artefact or there is too little code "
              "to control on.")
        print("           A reading from an instrument that cannot be shown to "
              "fire is not a reading,")
        print("           and that holds for the %d jalx target(s) found here as "
              "much as for a zero." % len(inr))
        return -1
    if not inr:
        print("  VERDICT  no MIPS16 reached from this range, and the control "
              "fired (%.1f%% of %d jal in range). The counts above are upper "
              "bounds." % (jal_pct, n_jal))
        return 0

    clusters = []
    for t in sorted(inr):
        if clusters and t - clusters[-1][-1] <= 4096:
            clusters[-1].append(t)
        else:
            clusters.append([t])
    print("  VERDICT  MIPS16 REACHED -- %d jalx target(s), %d distinct, in %d "
          "cluster(s):" % (len(inr), len(set(inr)), len(clusters)))
    for c in clusters:
        print("           0x%08x .. 0x%08x   %d targets, %d distinct"
              % (c[0], c[-1], len(c), len(set(c))))
    print("           A 4-byte scan is NOT a superset of the instructions "
          "there. Disassemble, do not count.")
    return len(inr)


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
    want_pairs, gap, want_m16 = False, 4, False
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
        elif a == "--pairs":
            want_pairs = True; i += 1
        elif a == "--mips16":
            want_m16 = True; i += 1
        elif a == "--gap":
            gap = int(argv[i + 1], 0); i += 2
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

    if want_pairs:
        report_pairs(words, gap)
    if want_m16:
        report_mips16(words, ranges)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
