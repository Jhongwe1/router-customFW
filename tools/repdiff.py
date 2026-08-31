#!/usr/bin/env python3
"""repdiff -- where do two builds of the same tree differ, and what are the bytes?

`P4a`, 2026-09-01.  `sha256sum` answers whether two builds match.  When they do
not it says nothing at all, and "not reproducible" is not a finding -- the
finding is WHICH bytes and WHY.  量 2026-08-31: `rep8` and `rep4`, the same
`.config` and the same 15 marks, differ in 84 of 3,935,472 bytes; `sha256sum`
could not tell those 84 from 84 bytes of miscompiled `.text`, and the two would
have meant completely different gates.

WHAT IT DOES.  Byte-diffs two ELF32 big-endian images, groups the differences
into runs, and puts each run in a section and, for allocated sections, in a
symbol.  It prints the surrounding bytes as text, because on this project the
answer has twice been a string a human could read at a glance.

WHY IT PARSES ELF ITSELF INSTEAD OF CALLING readelf.
  * The rsdk `readelf` is a VENDOR BINARY.  CLAUDE.md: running one is not a
    read-only act -- 2026-08-28 a census that ran every executable in three
    rsdk bin/ directories with `--version` deleted 2,580 tracked files from a
    pinned clone.  Anything that runs one has to go through
    `tools/vendor-tripwire.sh` from a scratch directory, which is a lot of
    machinery to read a section header table.
  * The host `readelf` is a third party whose output format is not this
    project's to pin, and parsing its text is a second thing that can be wrong.
  * ELF32's section header is ten big-endian words.  Reading it directly is
    smaller than either alternative and is checkable by the controls below.

WHAT IT REFUSES.  Anything that is not ELF32 big-endian.  This project is one
device and one endianness; silently reading an ELF64 little-endian host object
with the same code would produce section offsets that are garbage and a report
that looks exactly like a real one.

🔴 THE CONTROL THAT MAKES THE OTHERS MEAN ANYTHING is `D2`, not `D1`.  A tool
that reported "0 differing bytes" for every input would pass `D1` -- a file
against itself -- and every summary line it printed would be true.  `D2` is
what says it can report a difference at all, and `D5` is what says the grouping
is not "everything is one run".

Usage
    tools/repdiff.py A B [--gap N] [--limit N]
    tools/repdiff.py --self-test

Exit codes:  0 identical (or self-test passed) · 1 they differ · 2 refused
"""

import os
import struct
import sys

VERSION = "1.0"

SHT_NOBITS = 8
SHF_ALLOC = 0x2
DEFAULT_GAP = 8


class Refuse(Exception):
    pass


# --------------------------------------------------------------------------
# ELF32 big-endian, read directly
# --------------------------------------------------------------------------

class Elf32BE(object):
    def __init__(self, blob, name="<blob>"):
        self.b, self.name = blob, name
        if len(blob) < 52:
            raise Refuse("%s: %d bytes, too short for an ELF32 header" % (name, len(blob)))
        if blob[:4] != b"\x7fELF":
            raise Refuse("%s: no ELF magic -- this tool reads ELF images, not "
                         "raw binaries" % name)
        if blob[4] != 1:
            raise Refuse("%s: EI_CLASS=%d, not ELF32. Reading it as ELF32 would "
                         "produce section offsets that are garbage and a report "
                         "that looks real" % (name, blob[4]))
        if blob[5] != 2:
            raise Refuse("%s: EI_DATA=%d, not big-endian. This project is one "
                         "device and one endianness" % (name, blob[5]))
        (self.e_type, self.e_machine, self.e_version, self.e_entry,
         self.e_phoff, self.e_shoff, self.e_flags, self.e_ehsize,
         self.e_phentsize, self.e_phnum, self.e_shentsize, self.e_shnum,
         self.e_shstrndx) = struct.unpack_from(">HHIIIIIHHHHHH", blob, 16)
        self.sections = []
        for i in range(self.e_shnum):
            o = self.e_shoff + i * self.e_shentsize
            if o + 40 > len(blob):
                raise Refuse("%s: section header %d runs past the end of the "
                             "file" % (name, i))
            (nm, typ, flags, addr, off, size, link, info, align,
             entsize) = struct.unpack_from(">IIIIIIIIII", blob, o)
            self.sections.append(dict(idx=i, name_off=nm, type=typ, flags=flags,
                                      addr=addr, off=off, size=size, link=link,
                                      entsize=entsize, name="?"))
        if self.e_shstrndx < len(self.sections):
            sh = self.sections[self.e_shstrndx]
            st = blob[sh["off"]:sh["off"] + sh["size"]]
            for s in self.sections:
                e = st.find(b"\0", s["name_off"])
                if e >= 0:
                    s["name"] = st[s["name_off"]:e].decode("ascii", "replace")

    def section_named(self, n):
        for s in self.sections:
            if s["name"] == n:
                return s
        return None

    def sections_at(self, off):
        """Sections whose FILE image contains this offset.

        SHT_NOBITS is excluded: .bss occupies no file space, and a tool that
        included it would attribute a difference to a section that cannot
        contain one.
        """
        return [s for s in self.sections
                if s["type"] != SHT_NOBITS and s["size"]
                and s["off"] <= off < s["off"] + s["size"]]

    def symbols(self):
        out = []
        symtab = self.section_named(".symtab")
        if not symtab or symtab["link"] >= len(self.sections):
            return out
        strtab = self.sections[symtab["link"]]
        st = self.b[strtab["off"]:strtab["off"] + strtab["size"]]
        n = symtab["size"] // 16 if symtab["size"] else 0
        for i in range(n):
            o = symtab["off"] + i * 16
            if o + 16 > len(self.b):
                break
            nm, val, sz, info, other, shndx = struct.unpack_from(">IIIBBH", self.b, o)
            e = st.find(b"\0", nm)
            out.append(dict(name=st[nm:e].decode("ascii", "replace") if e >= 0 else "?",
                            value=val, size=sz, shndx=shndx))
        return out


# --------------------------------------------------------------------------
# the diff
# --------------------------------------------------------------------------

def runs(offsets, gap=DEFAULT_GAP):
    """Group sorted offsets into [lo, hi] runs, joining anything <= gap apart."""
    if not offsets:
        return []
    out, cur = [], [offsets[0], offsets[0]]
    for o in offsets[1:]:
        if o - cur[1] <= gap:
            cur[1] = o
        else:
            out.append((cur[0], cur[1]))
            cur = [o, o]
    out.append((cur[0], cur[1]))
    return out


def symbol_at(elf, syms, sec, off):
    """The symbol covering a file offset in an allocated section, or None."""
    if not (sec["flags"] & SHF_ALLOC):
        return None
    vaddr = sec["addr"] + (off - sec["off"])
    best = None
    for y in syms:
        if y["shndx"] in (0, 0xFFF1) or not y["name"]:
            continue
        if y["value"] <= vaddr and (y["size"] == 0 or vaddr < y["value"] + y["size"]):
            if best is None or y["value"] > best["value"]:
                best = y
    if best is None:
        return None
    return (best["name"], vaddr - best["value"], vaddr)


def printable(bs):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in bs)


def compare(a_blob, b_blob, a_name="A", b_name="B", gap=DEFAULT_GAP):
    """-> (n_common, diff_offsets, runs, elf_of_A). Raises Refuse on non-ELF."""
    elf = Elf32BE(a_blob, a_name)
    Elf32BE(b_blob, b_name)          # parsed for its refusals, not its tables
    n = min(len(a_blob), len(b_blob))
    diffs = [i for i in range(n) if a_blob[i] != b_blob[i]]
    return n, diffs, runs(diffs, gap), elf


def report(a_path, b_path, gap=DEFAULT_GAP, limit=0, out=sys.stdout):
    a = open(a_path, "rb").read()
    b = open(b_path, "rb").read()
    n, diffs, rs, elf = compare(a, b, a_path, b_path, gap)
    syms = elf.symbols()
    print("repdiff %s" % VERSION, file=out)
    print("A %s  %d bytes" % (a_path, len(a)), file=out)
    print("B %s  %d bytes" % (b_path, len(b)), file=out)
    if len(a) != len(b):
        print("SIZES DIFFER -- only the common %d-byte prefix is mapped" % n,
              file=out)
    pct = (100.0 * len(diffs) / n) if n else 0.0
    print("differing bytes: %d of %d  (%.6f %%)" % (len(diffs), n, pct), file=out)
    if not diffs:
        print("IDENTICAL over the common prefix", file=out)
        return 0
    print("%d run(s), joined at gap<=%d" % (len(rs), gap), file=out)
    print("", file=out)
    shown = rs if not limit else rs[:limit]
    for lo, hi in shown:
        secs = elf.sections_at(lo)
        secn = ",".join(s["name"] for s in secs) or "(no section: header or padding)"
        sym = ""
        for s in secs:
            hit = symbol_at(elf, syms, s, lo)
            if hit:
                sym = "  sym=%s+0x%x (0x%08x)" % hit
                break
        cnt = sum(1 for d in diffs if lo <= d <= hi)
        print("--- 0x%06x..0x%06x  %d byte(s)  sec=%s%s" % (lo, hi, cnt, secn, sym),
              file=out)
        s0, s1 = max(0, lo - 80), min(n, hi + 80)
        print("   A |%s|" % printable(a[s0:s1]), file=out)
        print("   B |%s|" % printable(b[s0:s1]), file=out)
        print("", file=out)
    if limit and len(rs) > limit:
        print("... %d more run(s) not shown (--limit %d)" % (len(rs) - limit, limit),
              file=out)
    return 1


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

def _elf32be(text=b"", rodata=b"", bss_size=0, symbols=(), cls=1, data=2):
    """Build a minimal ELF32 big-endian image in memory.

    Synthetic on purpose.  The real comparands are 4 MB build products that a
    clone does not have, so a self-test that needed them would be an allowed
    skip everywhere -- and a control that does not run is not a control.
    """
    names = [b"", b".text", b".rodata", b".bss", b".symtab", b".strtab", b".shstrtab"]
    shstr = b"\0".join(names) + b"\0"
    noff = {}
    p = 0
    for nm in names:
        noff[nm] = p
        p += len(nm) + 1

    strtab = b"\0"
    symoff = {}
    for nm, _v, _s, _x in symbols:
        symoff[nm] = len(strtab)
        strtab += nm.encode() + b"\0"

    symtab = b"\0" * 16
    for nm, val, size, shndx in symbols:
        symtab += struct.pack(">IIIBBH", symoff[nm], val, size, 0x10, 0, shndx)

    body, offs = b"", {}
    for key, blob in ((".text", text), (".rodata", rodata),
                      (".symtab", symtab), (".strtab", strtab),
                      (".shstrtab", shstr)):
        while len(body) % 4:
            body += b"\0"
        offs[key] = 52 + len(body)
        body += blob

    while len(body) % 4:
        body += b"\0"
    shoff = 52 + len(body)

    def sh(nm, typ, flags, addr, off, size, link=0, entsize=0):
        return struct.pack(">IIIIIIIIII", noff[nm], typ, flags, addr, off, size,
                           link, 0, 4, entsize)

    shs = b"".join([
        sh(b"", 0, 0, 0, 0, 0),
        sh(b".text", 1, SHF_ALLOC | 0x4, 0x80000000, offs[".text"], len(text)),
        sh(b".rodata", 1, SHF_ALLOC, 0x80100000, offs[".rodata"], len(rodata)),
        # SHT_NOBITS: an offset inside a file region it does not own.
        sh(b".bss", SHT_NOBITS, SHF_ALLOC | 0x1, 0x80200000, offs[".text"], bss_size),
        sh(b".symtab", 2, 0, 0, offs[".symtab"], len(symtab), 5, 16),
        sh(b".strtab", 3, 0, 0, offs[".strtab"], len(strtab)),
        sh(b".shstrtab", 3, 0, 0, offs[".shstrtab"], len(shstr)),
    ])
    hdr = (b"\x7fELF" + bytes([cls, data, 1]) + b"\0" * 9 +
           struct.pack(">HHIIIIIHHHHHH", 2, 8, 1, 0x80000000, 0, shoff, 0,
                       52, 0, 0, 40, 7, 6))
    return hdr + body + shs


def _flip(blob, off):
    return blob[:off] + bytes([blob[off] ^ 0xFF]) + blob[off + 1:]


def run_controls(out=sys.stdout):
    ok = [True]
    n_ok = [0]
    n_bad = [0]

    def row(tag, name, good, detail=""):
        ok[0] = ok[0] and good
        (n_ok if good else n_bad)[0] += 1
        print("  %s  %-6s %-56s %s"
              % ("ok  " if good else "FAIL", tag, name, detail), file=out)

    def guarded(tag, name, fn):
        """Run one control's body; an exception is that control FAILING.

        🔴 The mutation suite's first run found this.  A control that raises
        instead of reporting takes every control after it down with it, and
        from outside the two are indistinguishable from a mutant nothing saw.
        `replay-capture` learned the same thing on 2026-08-31 from its own `W0`.
        """
        try:
            good, detail = fn()
        except Exception as ex:                       # noqa: BLE001 -- the point
            row(tag, name, False, "raised %s: %s" % (type(ex).__name__, str(ex)[:40]))
            return
        row(tag, name, good, detail)

    text = bytes(range(256)) * 4
    rodata = b"Linux version 2.6.30.9 (key@K) #1 Tue Sep 1 00:00:00 UTC 2026\0" + b"pad" * 40
    syms = (("start_kernel", 0x80000000, 256, 1),
            ("linux_banner", 0x80100000, 62, 2))
    A = _elf32be(text, rodata, bss_size=4096, symbols=syms)
    a = Elf32BE(A, "A")

    # D0 -- the population.  Every row below reads these fixtures; if the
    # builder is broken they are all vacuous.
    row("D0", "the fixture parses and has the sections it declares",
        {s["name"] for s in a.sections} >= {".text", ".rodata", ".bss", ".symtab"},
        "%d sections" % len(a.sections))
    t = a.section_named(".text")
    r = a.section_named(".rodata")
    row("D0b", "and .text / .rodata carry the bytes they were given",
        A[t["off"]:t["off"] + t["size"]] == text
        and A[r["off"]:r["off"] + r["size"]] == rodata)

    # D1 -- the negative control.  Meaningless without D2.
    n, d, rs, _ = compare(A, A)
    row("D1", "a file against itself reports 0 differing bytes",
        len(d) == 0 and rs == [], "%d" % len(d))

    # D2 -- 🔴 the control that makes D1 mean anything.
    B = _flip(A, t["off"] + 10)
    n, d, rs, e = compare(A, B)
    secs = e.sections_at(d[0]) if d else []
    row("D2", "one flipped byte in .text is found and placed",
        len(d) == 1 and len(rs) == 1 and [s["name"] for s in secs] == [".text"],
        "%d byte(s), sec=%s" % (len(d), ",".join(s["name"] for s in secs)))
    hit = symbol_at(e, e.symbols(), secs[0], d[0]) if secs else None
    row("D2b", "and attributed to the symbol that covers it",
        hit is not None and hit[0] == "start_kernel" and hit[1] == 10,
        str(hit))

    # D3 -- a different section, so D2 is not "it always says .text".
    B = _flip(A, r["off"] + 20)
    n, d, rs, e = compare(A, B)
    secs = e.sections_at(d[0]) if d else []
    hit = symbol_at(e, e.symbols(), secs[0], d[0]) if secs else None
    row("D3", "a flipped byte in .rodata is placed in .rodata",
        [s["name"] for s in secs] == [".rodata"] and hit and hit[0] == "linux_banner",
        "%s %s" % (",".join(s["name"] for s in secs), hit))

    # D4 -- SHT_NOBITS owns no file bytes.  The fixture's .bss deliberately
    # declares .text's offset; a tool that ignored sh_type would report both.
    B = _flip(A, t["off"] + 30)
    n, d, rs, e = compare(A, B)
    names = [s["name"] for s in e.sections_at(d[0])]
    row("D4", ".bss is never blamed for a byte in the file image",
        names == [".text"], ",".join(names))

    # D5 -- the grouping, both directions.
    B = _flip(_flip(A, t["off"] + 40), t["off"] + 44)
    n, d, rs, _ = compare(A, B)
    row("D5", "two flips 4 apart are ONE run", len(d) == 2 and len(rs) == 1,
        "%d diff, %d run" % (len(d), len(rs)))
    B = _flip(_flip(A, t["off"] + 40), t["off"] + 140)
    n, d, rs, _ = compare(A, B)
    row("D5b", "two flips 100 apart are TWO runs", len(d) == 2 and len(rs) == 2,
        "%d diff, %d run" % (len(d), len(rs)))

    # D6 -- different sizes.  Only the common prefix is mapped, and the count
    # is against that prefix rather than against the longer file.
    def _d6():
        n, d, rs, _ = compare(A, A + b"tail")
        return (n == len(A) and len(d) == 0), "n=%d" % n
    guarded("D6", "a longer B maps only the common prefix", _d6)

    # D7/D8 -- the refusals.  Each is a class that would otherwise produce a
    # report full of garbage offsets that looks exactly like a real one.
    # 🔴 D7's first fixture was `b"not an elf..."`, which the CLASS check
    # refused before the magic check was ever reached -- so deleting the magic
    # check left D7 green.  Found by the mutation suite on its first run.  This
    # one is a valid image with the magic byte alone corrupted, so it can be
    # refused by nothing else.
    no_magic = b"\x00" + A[1:]
    for tag, blob, what in (
            ("D7", no_magic, "an image whose ONLY defect is the magic"),
            ("D7c", b"not an elf at all, just some bytes" * 4, "a raw binary"),
            ("D8", _elf32be(text, rodata, data=1), "a little-endian ELF"),
            ("D8b", _elf32be(text, rodata, cls=2), "an ELF64 input"),
            ("D7b", b"\x7fELF\x01\x02", "a truncated header")):
        # 🔴 The exception TYPE is asserted, not just that one was raised.  A
        # `struct.error` from unpacking past the end is a crash, not a refusal,
        # and a control that accepted either would be green for a tool that had
        # stopped refusing and started crashing.
        try:
            compare(blob, blob)
            row(tag, "%s is refused" % what, False, "accepted")
        except Refuse as ex:
            row(tag, "%s is refused" % what, True, str(ex)[:40])
        except Exception as ex:                       # noqa: BLE001
            row(tag, "%s is refused" % what, False,
                "raised %s, not Refuse" % type(ex).__name__)

    # D9 -- 🔴 the refusal fires on either side, not only on A.  The first
    # version parsed B for nothing and this is what would have caught it.
    try:
        compare(A, b"not an elf" * 8)
        row("D9", "a bad B is refused too, not only a bad A", False, "accepted")
    except Refuse as ex:
        row("D9", "a bad B is refused too, not only a bad A", True, str(ex)[:44])

    print("", file=out)
    if ok[0]:
        print("RESULT: \033[32m%d passed, 0 failed\033[0m" % n_ok[0], file=out)
    else:
        print("RESULT: %d passed, \033[31m%d failed\033[0m" % (n_ok[0], n_bad[0]),
              file=out)
    return 0 if ok[0] else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        return run_controls()
    args = [a for a in argv[1:] if not a.startswith("--")]
    gap = DEFAULT_GAP
    limit = 0
    if "--gap" in argv:
        gap = int(argv[argv.index("--gap") + 1])
        args = [a for a in args if a != str(gap)]
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
        args = [a for a in args if a != str(limit)]
    if len(args) != 2:
        print(__doc__.strip().split("Usage")[-1], file=sys.stderr)
        return 2
    try:
        return report(args[0], args[1], gap=gap, limit=limit)
    except Refuse as ex:
        print("REFUSED: %s" % ex, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
