#!/usr/bin/env python3
"""uspacescan -- is `system()`/`popen()` in rlxfw's userspace?  Two sources, and
each one can come back red.

WHY THIS FILE EXISTS, AND WHAT WAS WRONG WITH THE TWO SOURCES BEFORE IT
=======================================================================
`R7`'s pass condition is "`system()`/`popen()` reference count = 0, from two
independent sources of different kind".  The two sources named on 2026-08-25
were designed against the VENDOR rootfs, which is dynamically linked, and both
of them are VACUOUS on rlxfw's own binaries, which are statically linked and
stripped:

  * a `PT_DYNAMIC` -> `DT_SYMTAB` walk returns 0 on a static ELF BY
    CONSTRUCTION, because there is no `PT_DYNAMIC` segment at all.  0 is also
    the passing answer, so the instrument cannot fail.  This is the same defect
    `notes/rootfs-census.md` already records about `readelf --dyn-syms` on the
    vendor files ("that is the shape of a tool that cannot fail"), and the same
    class as `R-22`/`R-28`.
  * `nm --undefined-only` on a LINKED static ELF does not list `system`.  If
    `system` were used, the linker would have pulled `system.os` out of
    `libc.a` and the symbol would be DEFINED (`T`/`W`), not undefined.  So the
    absence of an undefined `system` is the normal state of both a clean binary
    and a filthy one.

So the two sources are re-specified.  Precise wording, to be pasted into
`SPEC.md`:

  SOURCE (1) -- THE SHIPPED BYTES.  Over one linked target ELF, possibly
  stripped.  A name is PRESENT when the executable image contains an
  implementation of it, decided by whichever of these apply, all of which are
  computed from the file alone:
    (1a) DYNAMIC IMPORT WALK.  If a `PT_DYNAMIC` segment exists, walk it to
         `DT_SYMTAB`/`DT_STRTAB`, take the entry count from `DT_HASH`'s nchain
         (cross-checked against `DT_MIPS_SYMTABNO` when present), and count the
         entries whose `st_shndx` is `SHN_UNDEF`.  This needs no section
         headers, so it works on the vendor's files, which have none.
    (1b) SYMBOL TABLE.  If `.symtab` survives, a defined `FUNC` entry of that
         name in an executable section is PRESENT.
    (1c) RELOCATION-MASKED CODE FINGERPRINT -- the method that survives
         `strip`.  Take the archive member of the target `libc.a` that defines
         the name, take that symbol's bytes out of the member's executable
         section, and zero every field a relocation in the matching `.rel`
         section writes into (the fields the linker is free to change:
         HI16/LO16/GOT16/CALL16 immediates, the 26-bit `j`/`jal` target, a
         whole `R_MIPS_32` word).  Search every executable section of the
         target for that masked pattern, masking the same offsets in each
         window.  A match is the name's entry point.  The masking rule is read
         out of the member's own relocation table; it is not a guess.
  A located entry is then cross-read two ways, both decidable: whether its
  address appears in `.got` (on this toolchain every libc call is
  `lw $t9,%got(f)($gp); jalr $t9`, so a GOT slot holding the entry IS the call),
  and how many `jal`/`j` in `.text` target it directly.
  The verdict is PRESENCE, which over-reports rather than under-reports: it says
  the code is in the bytes that ship, not that a path reaches it.

  SOURCE (2) -- THE PRE-LINK OBJECTS.  Over every `*.o` that went into the
  program, read with this tool's own ELF reader (no `nm` subprocess).  A name is
  REFERENCED when some object holds a symbol of that name with
  `st_shndx == SHN_UNDEF` and binding GLOBAL or WEAK -- which is exactly what a
  compiled call site leaves behind, and is present in the object whether or not
  the link later resolves it.  Optionally cross-checked with the toolchain's
  `mips-linux-nm -u`, and a disagreement is a failure, not a vote.

They are independent and of different kind: (1) reads the linked image and the
vendor library's code, (2) reads the compiler's output and never looks at
libc.  (1) can see a forbidden function the program never asked for; (2) can
see a call the linker later discarded.  DISAGREEMENT IS AN ERROR, NOT A VOTE:
if one says clean and the other says dirty, this tool exits non-zero and names
the file.

WHAT SOURCE (1c) GETS WRONG, STATED BEFORE ANY RESULT IS QUOTED
===============================================================
FALSE POSITIVES
  * A fingerprint whose distinguishing bytes are all relocated matches every
    function shaped like it.  量 on this toolchain: `vfork`'s implementation is
    the seven-word PIC thunk
        lui $gp,%hi(_gp_disp); addiu $gp,%lo(_gp_disp); addu $gp,$gp,$t9
        lw $t9,%got(X)($gp); nop; jr $t9; nop
    and three of its seven words are relocated, leaving THREE distinct unmasked
    words -- so it matched five unrelated thunks in `iperf3`.  Every other name
    in the table leaves 19 to 131 distinct unmasked words.  So the tool
    measures `distinct unmasked words` per fingerprint and REFUSES to use one
    below `--fp-distinct` (default 8, chosen with 3 on one side and 19 on the
    other), reporting UNDECIDED for that name rather than a number.
  * PRESENCE is not USE.  The linker pulls in an archive member because
    something referenced the symbol; it does not prove a live path reaches it.
    A forbidden function dragged in by another libc function would be reported.
    That is the direction this instrument is deliberately wrong in.
FALSE NEGATIVES
  * A fingerprint is built from ONE `libc.a`.  A program linked against a
    different build of the same libc -- different compiler flags, different
    `-O`, `--gc-sections`, a patched source -- has different unmasked bytes and
    will NOT match.  So source (1c) answers "is THIS libc's implementation in
    the file", and the `--libc` it was given is printed with every verdict.
  * An inlined or open-coded equivalent (a hand-written `execve` of `/bin/sh`)
    is not this libc's `system` and is invisible to all of (1a), (1b), (1c).
    R7's ban on `sh -c` is not established by this tool; `hazpay`/review is.
  * A name with no implementation in the archive gets no fingerprint.  That is
    reported as UNDECIDED (`NOFP`), never as 0 -- and the table carries
    `wordexp` as a CONTROL row so that every run demonstrates it.

AND THE ANTI-VACUITY RULE, WHICH IS THE POINT OF THE REWRITE
============================================================
A STRIPPED ELF WITH NO `PT_DYNAMIC` AND NO FINGERPRINT SOURCE IS REFUSED, NOT
PASSED.  There is nothing in such a file that either old source could read, so
0 would be a statement about the instrument.  Pass `--libc` (or have the
default toolchain present) or the file is not scanned.

REACHABILITY IS NOT CLAIMED, AND THE NUMBER THAT MAKES IT UNDECIDABLE IS
PRINTED
=======================================================================
The brief for this tool asked whether reachability from `_start` could be
decided by decoding `jal`/`j`/`jalr`.  量 on this toolchain it cannot, and the
reason is the ABI rather than a limit of the decoder: the rsdk gcc compiles
`abicalls` PIC (`e_flags` 0x1007 on `linkprobe` and `iperf3`, 0x1005 on
`uprobe`/`ucost`), so a call to a libc function is
`lw $t9,%got(f)($gp); jalr $t9` and there is no `jal` to it anywhere.  This
tool therefore prints, per file, the count of register-indirect transfers in
`.text` (`jalr`, and `jr` on a register other than `$ra`) and reports
`reach=INDIRECT`.  It does not run a BFS that would return UNDECIDED on every
real input; it reports the measurement that makes the answer undecidable.
What it does decide is the GOT/`jal` reference count above.

Usage
    uspacescan.py scan --elf F... [--objdir D...] [--pair ELF=OBJDIR]
                       [--libc libc.a] [--nm PATH] [--only N,N] [--json OUT]
    uspacescan.py --vendor-census DIR [--only N,N] [--json OUT]
    uspacescan.py --self-test [--allow-skip] [--tc DIR] [--trip PATH]

An ELF with no `--pair` (and no object directory whose name matches its stem) is
reported UNPAIRED: its source-(1) findings still stand and still set the exit
code, but agreement between the two sources is NOT claimed for it.
`--only system,popen` narrows the table to the two names the 2026-08-25 census
counted; without it the census is a six-name measurement and says so rather than
being compared with a published two-name number.

Exit
    0  clean -- every scanned file is free of every FORBIDDEN name
    1  a finding -- a FORBIDDEN name is present or referenced
    2  the two sources disagree about a file, or `nm` disagrees with source (2)
    3  REFUSED -- a control did not hold, or something could not be decided, so
       nothing is reported.  A refusal is one line and never a traceback.
"""
import argparse
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_TABLE = os.path.join(HERE, "uspacescan-names.tsv")
DEFAULT_TC = os.path.join(
    os.environ.get("FWRE_WORK", "/home/key/fwre-work"),
    "rebuild", "src-vendor", "rtl819x-toolchain", "toolchain",
    "rsdk-1.3.6-4181-EB-2.6.30-0.9.30")
DEFAULT_TRIP = os.path.join(REPO, "tools", "vendor-tripwire.sh")


class Refuse(Exception):
    """Anything the tool will not answer.  Printed as one line, exit 3."""


# ---------------------------------------------------------------------------
# The name table.  Data: see tools/uspacescan-names.tsv.
# ---------------------------------------------------------------------------
CLASSES = ("FORBIDDEN", "ALLOWED", "CONTROL")
EXPECTS = ("-", "ZERO", "NOFP")


def load_table(path):
    rows = []
    seen = set()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.rstrip("\n").rstrip("\r")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                f = line.split("\t")
                if len(f) < 4:
                    raise Refuse("%s:%d has %d tab-separated fields, wanted 4"
                                 % (path, lineno, len(f)))
                name, cls, expect = f[0].strip(), f[1].strip(), f[2].strip()
                if cls not in CLASSES:
                    raise Refuse("%s:%d class %r is not one of %s"
                                 % (path, lineno, cls, "/".join(CLASSES)))
                if expect not in EXPECTS:
                    raise Refuse("%s:%d expect %r is not one of %s"
                                 % (path, lineno, expect, "/".join(EXPECTS)))
                if cls == "CONTROL" and expect == "-":
                    raise Refuse("%s:%d a CONTROL row needs an expect"
                                 % (path, lineno))
                if name in seen:
                    raise Refuse("%s:%d %r appears twice" % (path, lineno, name))
                seen.add(name)
                rows.append(dict(name=name, cls=cls, expect=expect,
                                 why=f[3].strip()))
    except OSError as e:
        raise Refuse("cannot read the name table %s: %s" % (path, e))
    if not rows:
        raise Refuse("the name table %s holds no rows" % path)
    for cls in ("FORBIDDEN", "ALLOWED", "CONTROL"):
        if not [r for r in rows if r["cls"] == cls]:
            raise Refuse("the name table %s holds no %s row; a table with no %s "
                         "row cannot be shown working" % (path, cls, cls))
    return rows


# ---------------------------------------------------------------------------
# ELF, read here rather than shelled out, so nothing depends on a binutils
# build and so a malformed file becomes a refusal instead of a traceback.
# ---------------------------------------------------------------------------
SHN_UNDEF, SHN_ABS = 0, 0xFFF1
SHT_PROGBITS, SHT_SYMTAB, SHT_REL, SHT_NOBITS, SHT_DYNSYM = 1, 2, 9, 8, 11
SHF_EXECINSTR = 0x4
PT_LOAD, PT_DYNAMIC = 1, 2
STB_GLOBAL, STB_WEAK = 1, 2
STT_FUNC = 2
DT_NULL, DT_HASH, DT_STRTAB, DT_SYMTAB, DT_STRSZ, DT_SYMENT = 0, 4, 5, 6, 10, 11
DT_MIPS_SYMTABNO = 0x70000011

# Which bits of an instruction word a relocation is free to rewrite.  Read off
# the MIPS o32 ABI; every type this toolchain emits into an executable section
# is listed, and an unlisted type makes the fingerprint UNDECIDED rather than
# silently unmasked.
RELOC_MASK = {
    2: 0xFFFFFFFF,   # R_MIPS_32
    4: 0x03FFFFFF,   # R_MIPS_26
    5: 0x0000FFFF,   # R_MIPS_HI16
    6: 0x0000FFFF,   # R_MIPS_LO16
    7: 0x0000FFFF,   # R_MIPS_GPREL16
    9: 0x0000FFFF,   # R_MIPS_GOT16
    10: 0x0000FFFF,  # R_MIPS_PC16
    11: 0x0000FFFF,  # R_MIPS_CALL16
}


class Elf(object):
    """A 32-bit ELF, either endianness.  Section headers optional."""

    def __init__(self, blob, path="<bytes>"):
        self.path = path
        self.blob = blob
        if len(blob) < 52 or blob[:4] != b"\x7fELF":
            raise Refuse("%s is not an ELF file" % path)
        if blob[4] != 1:
            raise Refuse("%s is not 32-bit ELF (EI_CLASS=%d); this tool reads "
                         "the o32 MIPS shape only" % (path, blob[4]))
        if blob[5] == 2:
            self.e = ">"
        elif blob[5] == 1:
            self.e = "<"
        else:
            raise Refuse("%s has EI_DATA=%d, neither LSB nor MSB"
                         % (path, blob[5]))
        self.etype, self.machine = self.u("HH", 0x10)
        self.entry, self.phoff, self.shoff = self.u("III", 0x18)
        self.eflags, = self.u("I", 0x24)
        self.phentsize, self.phnum = self.u("HH", 0x2A)
        self.shentsize, self.shnum, self.shstrndx = self.u("HHH", 0x2E)
        self.phdrs = self._phdrs()
        self.sections = self._sections()

    def u(self, fmt, off):
        try:
            return struct.unpack_from(self.e + fmt, self.blob, off)
        except struct.error:
            raise Refuse("%s: truncated at offset %#x (wanted %s)"
                         % (self.path, off, fmt))

    def _phdrs(self):
        out = []
        if not self.phoff or not self.phnum:
            return out
        for i in range(self.phnum):
            o = self.phoff + i * self.phentsize
            ty, off, vaddr, paddr, filesz, memsz, fl, al = self.u("8I", o)
            out.append(dict(type=ty, off=off, vaddr=vaddr, filesz=filesz,
                            memsz=memsz, flags=fl))
        return out

    def _sections(self):
        out = []
        if not self.shoff or not self.shnum:
            return out
        for i in range(self.shnum):
            o = self.shoff + i * self.shentsize
            nm, ty, fl, addr, off, size, link, info, al, es = self.u("10I", o)
            out.append(dict(i=i, nameoff=nm, type=ty, flags=fl, addr=addr,
                            off=off, size=size, link=link, info=info,
                            entsize=es, name=""))
        if self.shstrndx < len(out):
            base = out[self.shstrndx]["off"]
            for s in out:
                s["name"] = self.cstr(base + s["nameoff"])
        return out

    def cstr(self, off):
        if off >= len(self.blob):
            raise Refuse("%s: string offset %#x past end of file"
                         % (self.path, off))
        end = self.blob.find(b"\0", off)
        if end < 0:
            end = len(self.blob)
        return self.blob[off:end].decode("latin-1")

    def sec(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def body(self, s):
        if s["type"] == SHT_NOBITS:
            return b""
        return self.blob[s["off"]:s["off"] + s["size"]]

    def exec_sections(self):
        """Sections whose bytes execute.  Empty when there are no section
        headers, and the caller must notice rather than read that as clean."""
        return [s for s in self.sections
                if s["type"] == SHT_PROGBITS and (s["flags"] & SHF_EXECINSTR)]

    # -- symbols -----------------------------------------------------------
    def symbols(self, sectype=SHT_SYMTAB):
        st = None
        for s in self.sections:
            if s["type"] == sectype:
                st = s
                break
        if st is None or st["entsize"] != 16 or st["link"] >= len(self.sections):
            return None
        strs = self.sections[st["link"]]["off"]
        out = []
        for k in range(st["size"] // 16):
            o = st["off"] + k * 16
            nameoff, value, size, info, other, shndx = self.u("IIIBBH", o)
            out.append(dict(name=self.cstr(strs + nameoff), value=value,
                            size=size, bind=info >> 4, type=info & 0xF,
                            shndx=shndx))
        return out

    # -- the dynamic segment, with no section headers needed ---------------
    def v2off(self, vaddr):
        for p in self.phdrs:
            if p["type"] == PT_LOAD and p["filesz"] and \
               p["vaddr"] <= vaddr < p["vaddr"] + p["filesz"]:
                return p["off"] + (vaddr - p["vaddr"])
        return None

    def dynamic(self):
        """{tag: value} of PT_DYNAMIC, or None when there is no such segment."""
        seg = None
        for p in self.phdrs:
            if p["type"] == PT_DYNAMIC:
                seg = p
                break
        if seg is None:
            return None
        d = {}
        o = seg["off"]
        end = min(seg["off"] + seg["filesz"], len(self.blob))
        while o + 8 <= end:
            tag, val = self.u("II", o)
            if tag == DT_NULL:
                break
            d.setdefault(tag, val)
            o += 8
        return d

    def dynsyms(self):
        """Every .dynsym entry, read through PT_DYNAMIC.  Works on the vendor's
        files, which carry no section headers at all."""
        d = self.dynamic()
        if d is None:
            return None
        symv, strv = d.get(DT_SYMTAB), d.get(DT_STRTAB)
        if symv is None or strv is None:
            raise Refuse("%s: PT_DYNAMIC has no DT_SYMTAB/DT_STRTAB" % self.path)
        syment = d.get(DT_SYMENT, 16)
        if syment != 16:
            raise Refuse("%s: DT_SYMENT is %d, not 16" % (self.path, syment))
        symo, stro = self.v2off(symv), self.v2off(strv)
        if symo is None or stro is None:
            raise Refuse("%s: DT_SYMTAB/DT_STRTAB fall outside every PT_LOAD"
                         % self.path)
        n = None
        hv = d.get(DT_HASH)
        if hv is not None:
            ho = self.v2off(hv)
            if ho is not None:
                nbucket, nchain = self.u("II", ho)
                n = nchain
        n2 = d.get(DT_MIPS_SYMTABNO)
        if n is None:
            n = n2
        elif n2 is not None and n2 != n:
            raise Refuse("%s: DT_HASH nchain=%d but DT_MIPS_SYMTABNO=%d; the "
                         "symbol count has two answers" % (self.path, n, n2))
        if n is None:
            raise Refuse("%s: neither DT_HASH nor DT_MIPS_SYMTABNO gives a "
                         ".dynsym entry count" % self.path)
        if symo + n * 16 > len(self.blob):
            raise Refuse("%s: .dynsym claims %d entries, which runs past the "
                         "end of the file" % (self.path, n))
        out = []
        for k in range(n):
            o = symo + k * 16
            nameoff, value, size, info, other, shndx = self.u("IIIBBH", o)
            out.append(dict(name=self.cstr(stro + nameoff), value=value,
                            size=size, bind=info >> 4, type=info & 0xF,
                            shndx=shndx))
        return out


# ---------------------------------------------------------------------------
# `ar`, read here for the same reason as ELF.
# ---------------------------------------------------------------------------
def ar_members(path):
    try:
        blob = open(path, "rb").read()
    except OSError as e:
        raise Refuse("cannot read the archive %s: %s" % (path, e))
    if blob[:8] != b"!<arch>\n":
        raise Refuse("%s is not an ar archive" % path)
    out, longnames, p = [], b"", 8
    while p + 60 <= len(blob):
        raw = blob[p:p + 16].rstrip()
        try:
            size = int(blob[p + 48:p + 58].decode("latin-1").strip())
        except ValueError:
            raise Refuse("%s: malformed member header at %#x" % (path, p))
        data = blob[p + 60:p + 60 + size]
        nm = raw.decode("latin-1")
        if nm == "//":
            longnames = data
        elif nm.startswith("/") and nm[1:].isdigit():
            o = int(nm[1:])
            e = longnames.find(b"/", o)
            out.append((longnames[o:e if e >= 0 else None].decode("latin-1"),
                        data))
        elif nm not in ("/", "/SYM64/"):
            out.append((nm.rstrip("/"), data))
        p += 60 + size + (size & 1)
    if not out:
        raise Refuse("%s holds no members" % path)
    return out


# ---------------------------------------------------------------------------
# Source (1c): the relocation-masked code fingerprint.
# ---------------------------------------------------------------------------
class Fingerprint(object):
    def __init__(self, name, member, pattern, mask, distinct, endian):
        self.name = name
        self.member = member
        self.pattern = pattern      # bytes, with every relocated field zeroed
        self.mask = mask            # [(offset, mask)] relative to the pattern
        self.distinct = distinct    # distinct unmasked 32-bit words
        self.endian = endian

    def __len__(self):
        return len(self.pattern)


def build_fingerprints(libc, names):
    """{name: Fingerprint or None} from one archive.  None = no member defines
    it, which the caller must report as UNDECIDED, never as 0."""
    out = dict((n, None) for n in names)
    want = set(names)
    for member, data in ar_members(libc):
        if not want:
            break
        if not data.startswith(b"\x7fELF"):
            continue
        try:
            el = Elf(data, "%s(%s)" % (libc, member))
        except Refuse:
            continue
        syms = el.symbols()
        if syms is None:
            continue
        for s in syms:
            if s["name"] not in want:
                continue
            if s["type"] != STT_FUNC or s["size"] == 0:
                continue
            if s["shndx"] in (SHN_UNDEF, SHN_ABS) or \
               s["shndx"] >= len(el.sections):
                continue
            sec = el.sections[s["shndx"]]
            if not (sec["flags"] & SHF_EXECINSTR):
                continue
            lo, n = s["value"], s["size"]
            if n % 4 or lo % 4 or lo + n > sec["size"]:
                continue
            body = bytearray(el.body(sec)[lo:lo + n])
            rel = el.sec(".rel" + sec["name"])
            mask = []
            if rel is not None and rel["entsize"] == 8:
                for k in range(rel["size"] // 8):
                    roff, info = el.u("II", rel["off"] + k * 8)
                    rtype = info & 0xFF
                    if not (lo <= roff < lo + n):
                        continue
                    m = RELOC_MASK.get(rtype)
                    if m is None:
                        # An unlisted relocation type would leave a field
                        # unmasked that the linker may have rewritten, so the
                        # fingerprint would be wrong in the passing direction.
                        mask = None
                        break
                    mask.append((roff - lo, m))
            if mask is None:
                continue
            for roff, m in mask:
                w, = struct.unpack_from(el.e + "I", body, roff)
                struct.pack_into(el.e + "I", body, roff, w & ~m)
            masked_off = set(o for o, _ in mask)
            dis = set()
            for i in range(0, n, 4):
                if i in masked_off:
                    continue
                dis.add(struct.unpack_from(el.e + "I", body, i)[0])
            out[s["name"]] = Fingerprint(s["name"], member, bytes(body),
                                         mask, len(dis), el.e)
            want.discard(s["name"])
    return out


def fp_anchor(fp):
    """The longest run of consecutive UNMASKED bytes in the pattern, as
    (offset, bytes).  Only an index: it makes the search cheap and cannot
    change its answer, because every candidate is still compared in full."""
    masked = set()
    for roff, m in fp.mask:
        for k in range(4):
            masked.add(roff + k)
    best = (0, 0)
    run = 0
    for i in range(len(fp.pattern) + 1):
        if i < len(fp.pattern) and i not in masked:
            run += 1
        else:
            if run > best[1]:
                best = (i - run, run)
            run = 0
    off, ln = best
    return off, fp.pattern[off:off + ln]


def fp_search(el, fp):
    """Every address in an executable section where the masked pattern sits.
    The anchor narrows the candidates; each one is then compared over the whole
    pattern with the same fields masked, so the anchor is an index and not a
    weaker test."""
    hits = []
    n = len(fp.pattern)
    aoff, anchor = fp_anchor(fp)
    for sec in el.exec_sections():
        hay = el.body(sec)
        if len(hay) < n:
            continue
        cands = []
        if len(anchor) >= 8:
            k = hay.find(anchor)
            while k >= 0:
                base = k - aoff
                if base >= 0 and base % 4 == 0 and base + n <= len(hay):
                    cands.append(base)
                k = hay.find(anchor, k + 1)
        else:
            cands = range(0, len(hay) - n + 1, 4)
        for base in cands:
            win = bytearray(hay[base:base + n])
            for roff, m in fp.mask:
                w, = struct.unpack_from(el.e + "I", win, roff)
                struct.pack_into(el.e + "I", win, roff, w & ~m)
            if bytes(win) == fp.pattern:
                hits.append(sec["addr"] + base)
    return hits


# ---------------------------------------------------------------------------
# Reference counting: the GOT, and direct jal/j.  Both decidable.
# ---------------------------------------------------------------------------
GP_BIAS = 0x7FF0       # o32: _gp = .got + 0x7ff0.  Checked against `_gp`
                       # whenever a symbol table survives (control T8).


def got_words(el):
    got = el.sec(".got")
    if got is None or got["type"] == SHT_NOBITS:
        return None, None
    body = el.body(got)
    words = [struct.unpack_from(el.e + "I", body, i)[0]
             for i in range(0, len(body) - 3, 4)]
    return got["addr"], words


def count_direct_calls(el, target):
    """jal/j whose 26-bit target is `target`.  Region-exact: the top four bits
    come from the delay-slot PC, as the hardware computes them."""
    n = 0
    for sec in el.exec_sections():
        hay = el.body(sec)
        for i in range(0, len(hay) - 3, 4):
            w, = struct.unpack_from(el.e + "I", hay, i)
            op = w >> 26
            if op not in (2, 3):
                continue
            pc = sec["addr"] + i
            if (((pc + 4) & 0xF0000000) | ((w & 0x03FFFFFF) << 2)) == target:
                n += 1
    return n


def count_indirect_transfers(el):
    """`jalr`, and `jr` on a register other than $ra.  The number that makes
    reachability from _start undecidable on this ABI."""
    n = 0
    for sec in el.exec_sections():
        hay = el.body(sec)
        for i in range(0, len(hay) - 3, 4):
            w, = struct.unpack_from(el.e + "I", hay, i)
            if (w >> 26) != 0:
                continue
            funct = w & 0x3F
            rs = (w >> 21) & 0x1F
            if funct == 9:
                n += 1
            elif funct == 8 and rs != 31:
                n += 1
    return n


# ---------------------------------------------------------------------------
# SOURCE (1)
# ---------------------------------------------------------------------------
def source1(path, table, fps, fp_distinct):
    """One linked ELF -> {name: record}.  Raises Refuse when the file offers
    nothing either method can read -- 0 would be about the instrument."""
    try:
        blob = open(path, "rb").read()
    except OSError as e:
        raise Refuse("cannot read %s: %s" % (path, e))
    el = Elf(blob, path)
    dsyms = None
    try:
        dsyms = el.dynsyms()
    except Refuse as e:
        raise Refuse("%s: the dynamic import walk cannot run: %s"
                     % (path, e))
    syms = el.symbols()
    has_dyn = dsyms is not None
    has_sym = syms is not None
    usable_fp = [n for n in fps
                 if fps[n] is not None and fps[n].distinct >= fp_distinct]

    if not has_dyn and not has_sym and not usable_fp:
        raise Refuse(
            "%s is stripped, has no PT_DYNAMIC and no usable code fingerprint "
            "was supplied (--libc); 0 here would be a statement about the tool "
            "and not about the file" % path)
    if not el.exec_sections() and not has_dyn:
        raise Refuse("%s has no executable section headers and no PT_DYNAMIC; "
                     "there is nothing to scan" % path)

    gotaddr, gw = got_words(el)
    gp = (gotaddr + GP_BIAS) if gotaddr is not None else None
    gpsym = None
    if has_sym:
        for s in syms:
            if s["name"] == "_gp":
                gpsym = s["value"]
                break
    recs = {}
    for row in table:
        n = row["name"]
        r = dict(name=n, cls=row["cls"], imports=0, defined=0, fp_hits=[],
                 fp_len=None, fp_distinct=None, fp_member=None,
                 fp_state="NOFP", got_refs=0, direct_calls=0,
                 methods=[], present=False, undecided=None)
        if has_dyn:
            r["imports"] = len([s for s in dsyms
                                if s["name"] == n and s["shndx"] == SHN_UNDEF
                                and s["bind"] in (STB_GLOBAL, STB_WEAK)])
            r["methods"].append("dyn")
            if r["imports"]:
                r["present"] = True
        if has_sym:
            r["defined"] = len([s for s in syms
                                if s["name"] == n
                                and s["shndx"] not in (SHN_UNDEF,)
                                and s["type"] == STT_FUNC and s["size"]])
            r["methods"].append("symtab")
            if r["defined"]:
                r["present"] = True
        fp = fps.get(n)
        if fp is None:
            r["fp_state"] = "NOFP"
        elif fp.distinct < fp_distinct:
            r["fp_state"] = "WEAK"
            r["fp_len"] = len(fp)
            r["fp_distinct"] = fp.distinct
            r["fp_member"] = fp.member
        else:
            r["fp_state"] = "OK"
            r["fp_len"] = len(fp)
            r["fp_distinct"] = fp.distinct
            r["fp_member"] = fp.member
            r["methods"].append("fp")
            if el.exec_sections():
                r["fp_hits"] = fp_search(el, fp)
                if r["fp_hits"]:
                    r["present"] = True
        # A static file whose only possible method is the fingerprint, and the
        # fingerprint is not usable -> undecided, never 0.
        if not r["present"] and "fp" not in r["methods"] and not has_dyn \
           and not has_sym:
            r["undecided"] = r["fp_state"]
        for a in r["fp_hits"]:
            if gw is not None and a in gw:
                r["got_refs"] += 1
            r["direct_calls"] += count_direct_calls(el, a)
        recs[n] = r
    return dict(path=path, elf=el, shape=("dynamic" if has_dyn else "static"),
                stripped=(not has_sym), eflags=el.eflags, entry=el.entry,
                got=gotaddr, gp=gp, gp_symbol=gpsym,
                gp_convention_ok=(None if gpsym is None or gp is None
                                  else gpsym == gp),
                indirect=count_indirect_transfers(el) if el.exec_sections()
                else None,
                recs=recs)


# ---------------------------------------------------------------------------
# SOURCE (2)
# ---------------------------------------------------------------------------
def source2_object(path, names):
    """One .o -> {name: count of UND global/weak references}."""
    try:
        blob = open(path, "rb").read()
    except OSError as e:
        raise Refuse("cannot read %s: %s" % (path, e))
    el = Elf(blob, path)
    if el.etype != 1:
        raise Refuse("%s has e_type=%d; source (2) reads relocatable objects "
                     "(ET_REL) only" % (path, el.etype))
    syms = el.symbols()
    if syms is None:
        raise Refuse("%s has no .symtab; an object with no symbol table cannot "
                     "be read for undefined references, and 0 would be a "
                     "statement about the tool" % path)
    out = dict((n, 0) for n in names)
    for s in syms:
        if s["shndx"] == SHN_UNDEF and s["name"] in out and \
           s["bind"] in (STB_GLOBAL, STB_WEAK):
            out[s["name"]] += 1
    return out, len(syms)


def source2(objdir, table):
    objs = []
    if os.path.isdir(objdir):
        for fn in sorted(os.listdir(objdir)):
            if fn.endswith(".o") or fn.endswith(".os"):
                objs.append(os.path.join(objdir, fn))
    elif os.path.isfile(objdir):
        objs = [objdir]
    else:
        raise Refuse("no such object directory or file: %s" % objdir)
    if not objs:
        raise Refuse("%s holds no *.o; the SPEC requires each target Makefile "
                     "to keep them, and an empty directory would report 0"
                     % objdir)
    names = [r["name"] for r in table]
    per = {}
    tot = dict((n, 0) for n in names)
    nsyms = 0
    for o in objs:
        counts, k = source2_object(o, names)
        nsyms += k
        per[os.path.basename(o)] = counts
        for n in names:
            tot[n] += counts[n]
    return dict(objdir=objdir, objects=len(objs), symbols=nsyms,
                per=per, total=tot)


def nm_cross_check(nm, trip, objdir, table, scratch):
    """The toolchain's own `nm -u`, run through the tripwire from a scratch
    directory.  Returns {name: count} or raises Refuse."""
    objs = sorted(os.path.join(objdir, f) for f in os.listdir(objdir)
                  if f.endswith(".o") or f.endswith(".os"))
    names = set(r["name"] for r in table)
    out = dict((n, 0) for n in names)
    seen_any = 0          # the positive control on nm itself, see below
    for o in objs:
        cmd = [trip, "--quiet", "--", nm, "--undefined-only", o]
        try:
            p = subprocess.run(cmd, cwd=scratch, capture_output=True,
                               text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as e:
            raise Refuse("the nm cross-check could not run: %s" % e)
        if p.returncode not in (0,):
            raise Refuse("vendor-tripwire/nm exited %d on %s: %s"
                         % (p.returncode, o, (p.stderr or p.stdout).strip()
                            .splitlines()[:1]))
        for line in p.stdout.splitlines():
            f = line.split()
            if len(f) >= 2 and f[-2] in ("U", "w", "v"):
                seen_any += 1
                if f[-1] in names:
                    out[f[-1]] += 1
    # A cross-check that saw nothing at all agrees with 0 for free, and this
    # tool would then have printed "nm cross-check: agrees" on the strength of a
    # binary that is not nm.  Every object this project compiles has undefined
    # references (printf, socket, ...), so zero of them is the instrument, not
    # the population.
    if seen_any == 0:
        raise Refuse("the nm cross-check saw no undefined symbol at all in %d "
                     "object(s) under %s; a cross-check that reports nothing "
                     "agrees with 0 for free and is not evidence"
                     % (len(objs), objdir))
    return out


# ---------------------------------------------------------------------------
# The vendor census: the 2026-08-25 baseline, both methods, side by side.
# ---------------------------------------------------------------------------
PRINTABLE = re.compile(rb"^[\x20-\x7e]+$")


def string_scan_names(blob, names):
    """`notes/rootfs-census.md`'s method, reimplemented: NUL-delimited runs of
    printable bytes, matched WHOLE.  `.dynstr` is in the file whether or not
    section headers are, so every imported name is in the scanned set -- which
    is why the 2026-08-25 census used this and not `readelf --dyn-syms`.
    It is not an import walk: a hit may be a message string, an export, or a
    name in a symbol table that is only ever defined here.  Hence an upper
    bound, and hence the second method beside it."""
    out = dict((n, 0) for n in names)
    for chunk in blob.split(b"\0"):
        if not chunk or len(chunk) > 4096:
            continue
        if not PRINTABLE.match(chunk):
            continue
        s = chunk.decode("ascii")
        if s in out:
            out[s] += 1
    return out


def vendor_census(root, table, fps, fp_distinct):
    names = [r["name"] for r in table]
    forb = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    if not os.path.isdir(root):
        raise Refuse("no such directory: %s" % root)
    files, elves = 0, []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            files += 1
            try:
                with open(p, "rb") as fh:
                    magic = fh.read(4)
            except OSError:
                continue
            if magic == b"\x7fELF":
                elves.append(p)
    rows = []
    for p in sorted(elves):
        blob = open(p, "rb").read()
        rel = os.path.relpath(p, root)
        row = dict(path=rel, shape="?", str_hits={}, imports={},
                   str_dirty=False, imp_dirty=False, imp_state="ok")
        ss = string_scan_names(blob, names)
        row["str_hits"] = dict((k, v) for k, v in ss.items() if v)
        row["str_dirty"] = any(ss[n] for n in forb)
        try:
            el = Elf(blob, p)
            ds = el.dynsyms()
        except Refuse as e:
            row["imp_state"] = "REFUSED: %s" % e
            ds = None
        if ds is None:
            row["shape"] = "static"
            row["imp_state"] = "NO-PT_DYNAMIC (the import walk is blind here)"
        else:
            row["shape"] = "dynamic"
            imp = {}
            for n in names:
                c = len([s for s in ds if s["name"] == n
                         and s["shndx"] == SHN_UNDEF])
                if c:
                    imp[n] = c
            row["imports"] = imp
            row["imp_dirty"] = any(imp.get(n) for n in forb)
        rows.append(row)
    return dict(root=root, files=files, elves=len(elves), rows=rows,
                str_count=len([r for r in rows if r["str_dirty"]]),
                imp_count=len([r for r in rows if r["imp_dirty"]]),
                no_dynamic=len([r for r in rows if r["shape"] == "static"]))


# ---------------------------------------------------------------------------
# Synthetic ELF/AR builders.  Pure Python, so every control below runs with no
# cross compiler at all.
# ---------------------------------------------------------------------------
def _elf32be(etype, machine, entry, sections, phdrs=(), flags=0):
    """Assemble a 32-bit big-endian ELF from (name, type, flags, addr, body,
    link, info, entsize) tuples.  Section 0 is added here."""
    secs = [("", 0, 0, 0, b"", 0, 0, 0)] + list(sections)
    names = b"\0"
    nameoff = {}
    for s in secs[1:]:
        nameoff[s[0]] = len(names)
        names += s[0].encode() + b"\0"
    secs = secs + [(".shstrtab", SHT_PROGBITS, 0, 0, names, 0, 0, 0)]
    nameoff[".shstrtab"] = len(names)
    names += b".shstrtab\0"
    secs[-1] = (".shstrtab", 3, 0, 0, names, 0, 0, 0)
    hdr = 52
    phoff = hdr if phdrs else 0
    off = hdr + len(phdrs) * 32
    bodies, offs = [], []
    for s in secs:
        if s[1] == 0 or s[1] == SHT_NOBITS:
            offs.append(off)
            bodies.append(b"")
            continue
        pad = (-off) % 16
        off += pad
        bodies.append(b"\0" * pad + s[4])
        offs.append(off)
        off += len(s[4])
    shoff = off + ((-off) % 4)
    out = bytearray()
    out += b"\x7fELF\x01\x02\x01" + b"\0" * 9
    out += struct.pack(">HHIIIIIHHHHHH", etype, machine, 1, entry, phoff,
                       shoff, flags, hdr, 32, len(phdrs), 40, len(secs),
                       len(secs) - 1)
    for p in phdrs:
        out += struct.pack(">8I", *p)
    for i, s in enumerate(secs):
        out += bodies[i]
    out += b"\0" * (shoff - len(out))
    for i, s in enumerate(secs):
        name, ty, fl, addr, bodyb, link, info, es = s
        size = 0 if ty == 0 else len(bodyb)
        out += struct.pack(">10I", nameoff.get(name, 0), ty, fl, addr,
                           offs[i], size, link, info, 16 if ty in (2, 11) else 4,
                           es)
    return bytes(out)


def _symtab(entries, strings):
    """entries: (nameoff, value, size, bind, type, shndx)."""
    b = b""
    for nameoff, value, size, bind, ty, shndx in entries:
        b += struct.pack(">IIIBBH", nameoff, value, size,
                         (bind << 4) | ty, 0, shndx)
    return b


def _strtab(names):
    out, off = b"\0", {}
    for n in names:
        off[n] = len(out)
        out += n.encode() + b"\0"
    return out, off


def synth_object(und_names, defined=()):
    """A relocatable ET_REL with `und_names` as SHN_UNDEF globals."""
    strs, off = _strtab(list(und_names) + list(defined))
    ents = [(0, 0, 0, 0, 0, 0)]
    for n in und_names:
        ents.append((off[n], 0, 0, STB_GLOBAL, 0, SHN_UNDEF))
    for n in defined:
        ents.append((off[n], 0, 4, STB_GLOBAL, STT_FUNC, 1))
    secs = [(".text", SHT_PROGBITS, SHF_EXECINSTR, 0, b"\0" * 16, 0, 0, 0),
            (".symtab", SHT_SYMTAB, 0, 0, _symtab(ents, strs), 3, 1, 16),
            (".strtab", 3, 0, 0, strs, 0, 0, 0)]
    return _elf32be(1, 8, 0, secs)


def synth_static_elf(defined_names, text=b"", addr=0x400100, stripped=False):
    """A static ET_EXEC with a .symtab defining names (or stripped)."""
    body = text or b"\0" * 64
    strs, off = _strtab(list(defined_names) + ["_gp"])
    ents = [(0, 0, 0, 0, 0, 0)]
    for i, n in enumerate(defined_names):
        ents.append((off[n], addr + 4 * i, 4, STB_GLOBAL, STT_FUNC, 1))
    ents.append((off["_gp"], 0x441000 + GP_BIAS, 0, STB_GLOBAL, 0, SHN_ABS))
    secs = [(".text", SHT_PROGBITS, SHF_EXECINSTR | 2, addr, body, 0, 0, 0),
            (".got", SHT_PROGBITS, 3, 0x441000, b"\0" * 16, 0, 0, 4)]
    if not stripped:
        # sh_link of .symtab is the index of .strtab AFTER the null section is
        # prepended: null,.text,.got,.symtab,.strtab -> 4.  It was 3 here for
        # one run, `symbols()` correctly declined to read the table, and control
        # C2 caught it -- which is what C2 is for.
        secs += [(".symtab", SHT_SYMTAB, 0, 0, _symtab(ents, strs), 4, 1, 16),
                 (".strtab", 3, 0, 0, strs, 0, 0, 0)]
    ph = [(PT_LOAD, 0, addr & ~0xFFF, addr & ~0xFFF, 0x1000, 0x1000, 5, 0x1000)]
    return _elf32be(2, 8, addr, secs, ph)


def synth_dynamic_elf(und_names, base=0x400000):
    """An ET_DYN/ET_EXEC with a real PT_DYNAMIC -> DT_SYMTAB/DT_STRTAB/DT_HASH,
    the shape source (1a) walks -- and with NO section headers for .dynsym, so
    the control exercises the path the vendor's files need."""
    strs, off = _strtab(list(und_names))
    ents = [(0, 0, 0, 0, 0, 0)]
    for n in und_names:
        ents.append((off[n], 0, 0, STB_GLOBAL, 0, SHN_UNDEF))
    dynsym = _symtab(ents, strs)
    nsym = len(ents)
    hashb = struct.pack(">II", 1, nsym) + struct.pack(">I", 0) + \
        b"\0" * (4 * nsym)
    # One PT_LOAD covering everything from file offset 0.
    blob = bytearray()
    hdr = 52
    nph = 2
    cur = hdr + nph * 32
    def place(b):
        nonlocal cur
        pad = (-cur) % 16
        o = cur + pad
        cur = o + len(b)
        return o, b"\0" * pad + b
    o_sym, p_sym = place(dynsym)
    o_str, p_str = place(strs)
    o_hash, p_hash = place(hashb)
    dyn = struct.pack(">II", DT_SYMTAB, base + o_sym) + \
        struct.pack(">II", DT_STRTAB, base + o_str) + \
        struct.pack(">II", DT_HASH, base + o_hash) + \
        struct.pack(">II", DT_SYMENT, 16) + \
        struct.pack(">II", DT_STRSZ, len(strs)) + \
        struct.pack(">II", DT_NULL, 0)
    o_dyn, p_dyn = place(dyn)
    total = cur
    out = bytearray()
    out += b"\x7fELF\x01\x02\x01" + b"\0" * 9
    out += struct.pack(">HHIIIIIHHHHHH", 2, 8, 1, base + hdr, hdr, 0, 0,
                       hdr, 32, nph, 40, 0, 0)
    out += struct.pack(">8I", PT_LOAD, 0, base, base, total, total, 5, 0x1000)
    out += struct.pack(">8I", PT_DYNAMIC, o_dyn, base + o_dyn, base + o_dyn,
                       len(dyn), len(dyn), 6, 4)
    out += p_sym + p_str + p_hash + p_dyn
    return bytes(out)


def synth_archive(members):
    """members: [(name, blob)] -> ar bytes."""
    out = bytearray(b"!<arch>\n")
    for name, blob in members:
        nm = (name + "/").ljust(16)[:16]
        out += nm.encode()
        out += b"0".ljust(12) + b"0".ljust(6) + b"0".ljust(6) + \
            b"100644".ljust(8) + str(len(blob)).ljust(10).encode() + b"`\n"
        out += blob
        if len(blob) & 1:
            out += b"\n"
    return bytes(out)


def synth_member_with_code(name, words, relocs):
    """A libc-like member defining `name` over `words`, with `relocs` as
    [(word_index, r_type)] so the fingerprint builder has a mask to read."""
    text = b"".join(struct.pack(">I", w) for w in words)
    strs, off = _strtab([name])
    ents = [(0, 0, 0, 0, 0, 0),
            (off[name], 0, len(text), STB_GLOBAL, STT_FUNC, 1)]
    relb = b"".join(struct.pack(">II", i * 4, (1 << 8) | t) for i, t in relocs)
    secs = [(".text", SHT_PROGBITS, SHF_EXECINSTR, 0, text, 0, 0, 0),
            (".rel.text", SHT_REL, 0, 0, relb, 3, 1, 8),
            (".symtab", SHT_SYMTAB, 0, 0, _symtab(ents, strs), 4, 1, 16),
            (".strtab", 3, 0, 0, strs, 0, 0, 0)]
    return _elf32be(1, 8, 0, secs)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def fmt_hits(a):
    return ",".join("%#x" % x for x in a) if a else "-"


def print_source1(s1, table, out=sys.stdout):
    el = s1["elf"]
    out.write("ELF  %s\n" % s1["path"])
    out.write("     shape=%s stripped=%s e_flags=%#x entry=%#x got=%s gp=%s\n"
              % (s1["shape"], s1["stripped"], s1["eflags"], s1["entry"],
                 "%#x" % s1["got"] if s1["got"] is not None else "-",
                 "%#x" % s1["gp"] if s1["gp"] is not None else "-"))
    if s1["gp_convention_ok"] is not None:
        out.write("     gp convention (.got + %#x == _gp): %s\n"
                  % (GP_BIAS, "confirmed" if s1["gp_convention_ok"]
                     else "REFUTED"))
    out.write("     register-indirect transfers in .text: %s -> reach=INDIRECT "
              "(not claimed)\n"
              % ("%d" % s1["indirect"] if s1["indirect"] is not None else "?"))
    out.write("     %-16s %-9s %-4s %-4s %-6s %-3s %-3s %-16s %s\n"
              % ("name", "class", "imp", "def", "fp", "got", "jal",
                 "verdict", "entry"))
    for row in table:
        r = s1["recs"][row["name"]]
        v = "PRESENT" if r["present"] else (
            "UNDECIDED(%s)" % r["undecided"] if r["undecided"] else "absent")
        out.write("     %-16s %-9s %-4d %-4d %-6s %-3d %-3d %-16s %s\n"
                  % (r["name"], r["cls"], r["imports"], r["defined"],
                     r["fp_state"], r["got_refs"], r["direct_calls"], v,
                     fmt_hits(r["fp_hits"])))


def print_source2(s2, table, out=sys.stdout):
    out.write("OBJ  %s   %d object(s), %d symbol(s)\n"
              % (s2["objdir"], s2["objects"], s2["symbols"]))
    for row in table:
        n = row["name"]
        c = s2["total"][n]
        who = [o for o, d in sorted(s2["per"].items()) if d[n]]
        out.write("     %-16s %-9s UND=%-3d %s\n"
                  % (n, row["cls"], c, " ".join(who) if who else "-"))


# ---------------------------------------------------------------------------
# The controls that run on every scan, in pure Python.
# ---------------------------------------------------------------------------
def inline_controls(table, fp_distinct):
    """Seven controls on the instrument itself, over synthetic fixtures.  Every
    `scan` runs them and refuses to report if any fails: a source that has not
    been shown flagging a planted positive in the same process is not a source.
    Returns [(label, expected, got)]."""
    res = []
    forb = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    allo = [r["name"] for r in table if r["cls"] == "ALLOWED"]
    if not forb or not allo:
        raise Refuse("the name table has no FORBIDDEN or no ALLOWED row, so "
                     "the controls cannot be run")
    f0, a0 = forb[0], allo[0]
    names = [r["name"] for r in table]
    nofps = dict((n, None) for n in names)

    with tempfile.TemporaryDirectory() as td:
        def w(n, b):
            p = os.path.join(td, n)
            open(p, "wb").write(b)
            return p

        # C1  planted positive, source (1a): a real PT_DYNAMIC import walk.
        p = w("dyn_pos", synth_dynamic_elf([f0, a0, "malloc"]))
        s = source1(p, table, nofps, fp_distinct)
        res.append(("C1 (1a) PT_DYNAMIC walk flags the planted %s" % f0,
                    "1/PRESENT", "%d/%s" % (s["recs"][f0]["imports"],
                                            "PRESENT" if s["recs"][f0]["present"]
                                            else "absent")))
        res.append(("C1b (1a) the ALLOWED %s is counted, not flagged" % a0,
                    "1/PRESENT", "%d/%s" % (s["recs"][a0]["imports"],
                                            "PRESENT" if s["recs"][a0]["present"]
                                            else "absent")))
        # C2  planted positive, source (1b): the symbol table.
        p = w("sta_pos", synth_static_elf([f0, "main"]))
        s = source1(p, table, nofps, fp_distinct)
        res.append(("C2 (1b) .symtab flags the planted %s" % f0,
                    "1/PRESENT", "%d/%s" % (s["recs"][f0]["defined"],
                                            "PRESENT" if s["recs"][f0]["present"]
                                            else "absent")))
        # C3  negative control: the same shapes with the name absent.
        p = w("dyn_neg", synth_dynamic_elf(["malloc", "strcpy"]))
        s = source1(p, table, nofps, fp_distinct)
        res.append(("C3 (1a) a file without it reports 0",
                    "0/absent", "%d/%s" % (s["recs"][f0]["imports"],
                                           "PRESENT" if s["recs"][f0]["present"]
                                           else "absent")))
        p = w("sta_neg", synth_static_elf(["main"]))
        s = source1(p, table, nofps, fp_distinct)
        res.append(("C3b (1b) a file without it reports 0",
                    "0/absent", "%d/%s" % (s["recs"][f0]["defined"],
                                           "PRESENT" if s["recs"][f0]["present"]
                                           else "absent")))
        # C4  the anti-vacuity rule: a stripped static ELF with no fingerprint
        #     source must REFUSE, not pass.
        p = w("sta_stripped", synth_static_elf([], stripped=True))
        try:
            source1(p, table, nofps, fp_distinct)
            got = "reported"
        except Refuse:
            got = "REFUSED"
        res.append(("C4 a stripped static ELF with no fingerprint is refused",
                    "REFUSED", got))
        # C5  the fingerprint, both directions.  Reference member: 24 words,
        #     three of them relocated (HI16, LO16 and a 26-bit jal target).  The
        #     "linked" copy rewrites exactly the relocated fields; the
        #     "different" copy rewrites an unmasked one.  The relocated word 23
        #     is a `jal` in BOTH copies: R_MIPS_26 masks 26 bits and leaves the
        #     opcode, so a reference holding `jr $ra` there would be a fixture
        #     that could never match -- which is how this control first read.
        base = [0x3C1C0001, 0x279C1234, 0x0399E021] + \
               [0x24020000 | (i * 7 + 3) for i in range(20)] + [0x0C000000]
        relocs = [(0, 5), (1, 6), (23, 4)]
        mem = synth_member_with_code(f0, base, relocs)
        arch = w("mini.a", synth_archive([("%s.os" % f0, mem)]))
        fps = build_fingerprints(arch, names)
        fp = fps[f0]
        res.append(("C5 a fingerprint is built, %s distinct unmasked words"
                    % (fp.distinct if fp else "no"),
                    "ok", "ok" if fp and fp.distinct >= fp_distinct
                    else ("WEAK" if fp else "NOFP")))
        linked = list(base)
        linked[0] = 0x3C1C0042      # masked HI16 -> must not matter
        linked[1] = 0x279CBEEF      # masked LO16 -> must not matter
        linked[23] = 0x0C001234     # masked 26-bit target -> must not matter
        text = b"\0" * 32 + b"".join(struct.pack(">I", x) for x in linked)
        p = w("fp_pos", synth_static_elf([], text=text, stripped=True))
        s = source1(p, table, fps, fp_distinct)
        res.append(("C5b (1c) the masked fingerprint finds the relocated copy",
                    "1 hit 0x400120",
                    "%d hit %s" % (len(s["recs"][f0]["fp_hits"]),
                                   fmt_hits(s["recs"][f0]["fp_hits"]))))
        diff = list(linked)
        diff[10] ^= 0x00000100      # an UNMASKED word -> must break the match
        text = b"\0" * 32 + b"".join(struct.pack(">I", x) for x in diff)
        p = w("fp_neg", synth_static_elf([], text=text, stripped=True))
        s = source1(p, table, fps, fp_distinct)
        res.append(("C5c (1c) one changed unmasked word breaks the match",
                    "0 hits", "%d hits" % len(s["recs"][f0]["fp_hits"])))
        # C5d a degenerate fingerprint (everything distinguishing relocated) is
        #     refused as WEAK rather than used.
        thin = [0x3C1C0000, 0x279C0000, 0x0399E021, 0x8F990000, 0, 0x03200008, 0]
        mem2 = synth_member_with_code(f0, thin, [(0, 5), (1, 6), (3, 9)])
        arch2 = w("thin.a", synth_archive([("%s.os" % f0, mem2)]))
        fps2 = build_fingerprints(arch2, names)
        res.append(("C5d a fingerprint with %d distinct words is called WEAK"
                    % (fps2[f0].distinct if fps2[f0] else -1),
                    "WEAK", "WEAK" if fps2[f0] and
                    fps2[f0].distinct < fp_distinct else "used"))
        # C6  source (2), both directions.
        p = w("pos.o", synth_object([f0, a0]))
        s2, _ = source2_object(p, names)
        res.append(("C6 (2) an object's UND %s is found" % f0,
                    "1", "%d" % s2[f0]))
        res.append(("C6b (2) the ALLOWED %s is counted too" % a0,
                    "1", "%d" % s2[a0]))
        p = w("neg.o", synth_object(["malloc"], defined=[f0]))
        s2, _ = source2_object(p, names)
        res.append(("C6c (2) a DEFINED %s is not an undefined reference" % f0,
                    "0", "%d" % s2[f0]))
        # C7  the CONTROL rows of the table hold.
        for row in table:
            if row["cls"] != "CONTROL":
                continue
            if row["expect"] == "ZERO":
                p = w("ctl_%s" % row["name"], synth_dynamic_elf([f0, "malloc"]))
                s = source1(p, table, nofps, fp_distinct)
                r = s["recs"][row["name"]]
                res.append(("C7 CONTROL %s reports 0" % row["name"], "0",
                            "%d" % (r["imports"] + r["defined"] +
                                    len(r["fp_hits"]))))
    return res


def run_controls(table, fp_distinct, out=sys.stdout, label="CONTROLS"):
    res = inline_controls(table, fp_distinct)
    bad = [r for r in res if r[1] != r[2]]
    out.write("=== %s (synthetic fixtures, pure Python) ===\n" % label)
    for lab, exp, got in res:
        if exp == got:
            out.write("  ok     %-58s %s\n" % (lab, got))
        else:
            out.write("  FAIL   %-58s expected %s, got %s\n" % (lab, exp, got))
    out.write("  %d control(s), %d failed\n" % (len(res), len(bad)))
    return res, bad


# ---------------------------------------------------------------------------
# Toolchain-dependent controls (the self-test's second half)
# ---------------------------------------------------------------------------
POS_C = """/* uspacescan-fixtures/pos.c -- the planted positive.  It really does
 * call system(), with an argument the compiler cannot fold away, so the call
 * survives -Os and the linker really pulls system.os out of libc.a.
 * It is never installed and never runs: `tools/test-uspacescan.sh` compiles it
 * so that both sources can be shown going red.  */
#include <stdlib.h>

int main(int argc, char **argv)
{
\t(void)argc;
\treturn system(argv[1]);
}
"""

ALLOWED_C = """/* uspacescan-fixtures/allowed.c -- the allowed-call control.  execve with a
 * typed argv array is exactly what R7 permits, so this file must come back
 * CLEAN from both sources while being COUNTED by both: the guard is shown
 * permitting as well as refusing.  */
#include <unistd.h>

int main(int argc, char **argv)
{
\tchar *const av[] = { "busybox", "true", (char *)0 };
\tchar *const ev[] = { (char *)0 };
\t(void)argc;
\treturn execve(argv[1], av, ev);
}
"""


FIXTURES = os.path.join(HERE, "uspacescan-fixtures")


def fixture_text(name, embedded):
    """The fixture's source, preferring the tracked file under
    tools/uspacescan-fixtures/ and falling back to the copy embedded above, so
    the self-test still runs from a checkout that has the tool and nothing
    else.  Which one was used is printed with the controls."""
    p = os.path.join(FIXTURES, name)
    if os.path.isfile(p):
        try:
            return open(p, "r", encoding="utf-8").read(), p
        except OSError as e:
            raise Refuse("cannot read the fixture %s: %s" % (p, e))
    return embedded, "<built into uspacescan.py>"


def tc_build(tc, trip, scratch, fixtures, cflags):
    """Compile, link and strip every fixture with the target toolchain, inside
    ONE tripwire bracket, from a scratch directory.

    One bracket rather than one per command on purpose, and it is a cost
    decision with a stated price: each `vendor-tripwire.sh` invocation sleeps a
    second and takes `git status --ignored` over six vendor trees twice, so
    eight brackets cost about thirty seconds of the self-test's forty.  What is
    given up is attribution INSIDE the bracket: if a tree moves, the tripwire
    names the tree and the files but not which of the four compiler runs did it.
    The trees are still snapshotted before the first compiler starts and after
    the last one returns, so nothing runs outside a bracket.

    fixtures: [(stem, text)]  ->  {stem: (obj, elf, stripped)}
    """
    cc = os.path.join(tc, "bin", "mips-linux-gcc")
    strip = os.path.join(tc, "bin", "mips-linux-strip")
    for p in (cc, strip, trip):
        if not os.path.isfile(p):
            raise Refuse("no target toolchain at %s (%s missing)" % (tc, p))
    lines = ["set -e"]
    out = {}
    for stem, text in fixtures:
        src = os.path.join(scratch, stem + ".c")
        open(src, "w", encoding="utf-8").write(text)
        o = os.path.join(scratch, stem + ".o")
        e = os.path.join(scratch, stem + ".elf")
        s = os.path.join(scratch, stem + ".stripped")
        lines.append("'%s' %s -c '%s' -o '%s'"
                     % (cc, " ".join(cflags), src, o))
        lines.append("'%s' -static -o '%s' '%s'" % (cc, e, o))
        lines.append("cp '%s' '%s'" % (e, s))
        lines.append("'%s' '%s'" % (strip, s))
        out[stem] = (o, e, s)
    script = os.path.join(scratch, "build.sh")
    open(script, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    p = subprocess.run([trip, "--quiet", "--", "/bin/sh", script],
                       cwd=scratch, capture_output=True, text=True, timeout=900)
    if p.returncode != 0:
        raise Refuse("the fixture build exited %d: %s"
                     % (p.returncode,
                        (p.stderr or p.stdout).strip().replace("\n", " | ")
                        [:300]))
    for stem, (o, e, s) in out.items():
        for f in (o, e, s):
            if not os.path.isfile(f):
                raise Refuse("the fixture build reported success but %s does "
                             "not exist" % f)
    return out


TARGET_CFLAGS = ["-Os", "-std=gnu99", "-static", "-fno-builtin",
                 "-fno-strict-aliasing", "-fno-common"]


def toolchain_controls(table, fps, fp_distinct, tc, trip, scratch,
                       out=sys.stdout):
    res = []
    names = [r["name"] for r in table]
    forb = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    allo = [r["name"] for r in table if r["cls"] == "ALLOWED"]
    ptext, porigin = fixture_text("pos.c", POS_C)
    atext, aorigin = fixture_text("allowed.c", ALLOWED_C)
    out.write("  fixture pos.c      %s\n" % porigin)
    out.write("  fixture allowed.c  %s\n" % aorigin)
    if "system" not in ptext:
        raise Refuse("the pos.c fixture (%s) does not mention system(); a "
                     "planted positive that plants nothing is not a control"
                     % porigin)
    if "execve" not in atext:
        raise Refuse("the allowed.c fixture (%s) does not mention execve()"
                     % aorigin)
    built = tc_build(tc, trip, scratch,
                     [("pos", ptext), ("allowed", atext)], TARGET_CFLAGS)
    pobj, pelf, pstr = built["pos"]
    aobj, aelf, astr = built["allowed"]
    s_pe = source1(pelf, table, fps, fp_distinct)
    s_ps = source1(pstr, table, fps, fp_distinct)
    s_ae = source1(aelf, table, fps, fp_distinct)
    s_as = source1(astr, table, fps, fp_distinct)
    p2, _ = source2_object(pobj, names)
    a2, _ = source2_object(aobj, names)

    res.append(("T1 (1) the planted system() is PRESENT in the linked ELF",
                "PRESENT", "PRESENT" if s_pe["recs"]["system"]["present"]
                else "absent"))
    res.append(("T2 (1) and the answer is the SAME after mips-linux-strip",
                "PRESENT", "PRESENT" if s_ps["recs"]["system"]["present"]
                else "absent"))
    pe = fmt_hits(s_pe["recs"]["system"]["fp_hits"])
    ps = fmt_hits(s_ps["recs"]["system"]["fp_hits"])
    res.append(("T2b and at the same address, byte-level both times", pe, ps))
    res.append(("T2c the stripped file really has no .symtab",
                "True", "%s" % s_ps["stripped"]))
    res.append(("T3 (2) the planted object's UND system is found",
                "1", "%d" % p2["system"]))
    res.append(("T4 (1) the execve fixture is CLEAN of every FORBIDDEN name",
                "0 forbidden",
                "%d forbidden" % len([n for n in forb
                                      if s_ae["recs"][n]["present"]])))
    res.append(("T4b (1) and execve is COUNTED on it",
                "PRESENT", "PRESENT" if s_ae["recs"]["execve"]["present"]
                else "absent"))
    res.append(("T4c (1) the execve fixture stays clean after strip",
                "0 forbidden",
                "%d forbidden" % len([n for n in forb
                                      if s_as["recs"][n]["present"]])))
    res.append(("T5 (2) the execve object is clean and execve is counted",
                "0/1", "%d/%d" % (sum(a2[n] for n in forb), a2["execve"])))
    res.append(("T6 (1+2) a name that exists nowhere is 0 from both",
                "0/0", "%d/%d"
                % (s_pe["recs"]["zzz_not_a_symbol"]["imports"] +
                   s_pe["recs"]["zzz_not_a_symbol"]["defined"] +
                   len(s_pe["recs"]["zzz_not_a_symbol"]["fp_hits"]),
                   p2["zzz_not_a_symbol"])))
    weak = [n for n in names
            if fps.get(n) is not None and fps[n].distinct < fp_distinct]
    res.append(("T7 the degenerate fingerprint is named, not used: %s"
                % (",".join(weak) or "-"),
                "vfork", ",".join(weak) or "-"))
    res.append(("T7b and it comes back UNDECIDED on a stripped file, not 0",
                "UNDECIDED",
                "UNDECIDED" if (s_ps["recs"]["vfork"]["fp_state"] == "WEAK")
                else s_ps["recs"]["vfork"]["fp_state"]))
    res.append(("T8 gp convention .got+%#x == _gp on a real link" % GP_BIAS,
                "confirmed",
                "confirmed" if s_pe["gp_convention_ok"] else "REFUTED"))
    # T9  a forged disagreement must be an error, not a vote.  The pair is
    #     forged on purpose: source (2) is handed a `system` reference that the
    #     ELF beside it does not carry, which is the shape of an instrument
    #     failure and must never be resolved by taking the cleaner answer.
    tot = dict((n, 0) for n in names)
    tot["system"] = 1
    v = pair_verdict("forged", s_ae,
                     dict(objdir="forged", objects=1, symbols=1,
                          per={"x.o": {"system": 1}}, total=tot), table)
    res.append(("T9 (1) clean + (2) dirty is DISAGREE, not a vote",
                "DISAGREE", v["state"]))
    res.append(("T9b (1) dirty + (2) dirty agrees",
                "DIRTY", pair_verdict("p", s_pe, dict(
                    objdir="p", objects=1, symbols=1,
                    per={"pos.o": p2}, total=p2), table)["state"]))
    res.append(("T9c (1) clean + (2) clean agrees",
                "CLEAN", pair_verdict("a", s_ae, dict(
                    objdir="a", objects=1, symbols=1,
                    per={"allowed.o": a2}, total=a2), table)["state"]))
    return res, dict(pos_elf=pelf, pos_stripped=pstr, pos_obj=pobj,
                     allowed_elf=aelf, allowed_obj=aobj)


# ---------------------------------------------------------------------------
# Pairing and the disagreement rule
# ---------------------------------------------------------------------------
def pair_verdict(label, s1, s2, table):
    forb = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    d1 = sorted(n for n in forb if s1["recs"][n]["present"])
    d2 = sorted(n for n in forb if s2["total"][n])
    if d1 and d2:
        st = "DIRTY"
    elif not d1 and not d2:
        st = "CLEAN"
    else:
        st = "DISAGREE"
    return dict(label=label, state=st, source1=d1, source2=d2)


def undecided_forbidden(s1, table):
    return sorted(r["name"] for r in table if r["cls"] == "FORBIDDEN"
                  and s1["recs"][r["name"]]["undecided"])


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def default_libc(tc):
    p = os.path.join(tc, "lib", "libc.a")
    return p if os.path.isfile(p) else None


def cmd_scan(a, table, out=sys.stdout):
    res, bad = run_controls(table, a.fp_distinct, out)
    if bad:
        raise Refuse("%d of this run's own controls failed; nothing is "
                     "reported" % len(bad))
    names = [r["name"] for r in table]
    libc = a.libc or default_libc(a.tc)
    fps = dict((n, None) for n in names)
    if libc:
        fps = build_fingerprints(libc, names)
    out.write("\n=== FINGERPRINTS ===\n")
    out.write("libc   %s\n" % (libc or "NONE -- source (1c) is unavailable, so "
                               "a stripped static ELF will be REFUSED"))
    for row in table:
        fp = fps.get(row["name"])
        if fp is None:
            out.write("  %-16s NOFP    (no archive member defines it)\n"
                      % row["name"])
        else:
            out.write("  %-16s %-7s member=%-16s %4dB  %3d distinct unmasked "
                      "words\n" % (row["name"],
                                   "ok" if fp.distinct >= a.fp_distinct
                                   else "WEAK", fp.member, len(fp), fp.distinct))
    # the CONTROL rows' expectations about the fingerprint set
    for row in table:
        if row["cls"] == "CONTROL" and row["expect"] == "NOFP":
            if libc is None:
                out.write("  CONTROL %s: skipped, no libc supplied\n"
                          % row["name"])
            elif fps.get(row["name"]) is not None:
                raise Refuse("CONTROL row %s expects NOFP but a fingerprint "
                             "was built from %s; the control that proves an "
                             "unfingerprintable name comes back UNDECIDED no "
                             "longer holds" % (row["name"], libc))
            else:
                out.write("  ok     CONTROL %s -> NOFP (undecided, not 0)\n"
                          % row["name"])

    pairs = {}
    for p in a.pair or []:
        if "=" not in p:
            raise Refuse("--pair wants ELF=OBJDIR, got %r" % p)
        k, v = p.split("=", 1)
        pairs[os.path.abspath(k)] = v

    s1s, s2s = [], {}
    out.write("\n=== SOURCE (1): THE SHIPPED BYTES ===\n")
    for f in a.elf or []:
        s1 = source1(f, table, fps, a.fp_distinct)
        s1s.append(s1)
        print_source1(s1, table, out)
    out.write("\n=== SOURCE (2): THE PRE-LINK OBJECTS ===\n")
    for d in a.objdir or []:
        s2 = source2(d, table)
        s2s[os.path.abspath(d)] = s2
        print_source2(s2, table, out)
        if a.nm:
            with tempfile.TemporaryDirectory() as sc:
                got = nm_cross_check(a.nm, a.trip, d, table, sc)
            dis = [n for n in [r["name"] for r in table]
                   if got[n] != s2["total"][n]]
            if dis:
                raise Refuse("nm disagrees with source (2) on %s for %s"
                             % (d, ",".join(dis)))
            out.write("     nm cross-check: agrees on every name (and it did "
                      "see undefined symbols, so the agreement is not vacuous)"
                      "\n")

    out.write("\n=== TWO-SOURCE AGREEMENT ===\n")
    verdicts = []
    for s1 in s1s:
        stem = os.path.basename(s1["path"]).split(".")[0]
        od = pairs.get(os.path.abspath(s1["path"]))
        if od is None:
            for k, s2 in s2s.items():
                if os.path.basename(k.rstrip("/")) == stem:
                    od = k
                    break
        if od is None:
            out.write("  UNPAIRED  %-40s source (2) has no object directory "
                      "for it; agreement is NOT claimed\n"
                      % os.path.basename(s1["path"]))
            verdicts.append(dict(label=s1["path"], state="UNPAIRED",
                                 source1=sorted(
                                     n for n in [r["name"] for r in table
                                                 if r["cls"] == "FORBIDDEN"]
                                     if s1["recs"][n]["present"]),
                                 source2=None))
            continue
        v = pair_verdict(s1["path"], s1, s2s[os.path.abspath(od)], table)
        verdicts.append(v)
        out.write("  %-9s %-40s (1)=%s  (2)=%s\n"
                  % (v["state"], os.path.basename(s1["path"]),
                     ",".join(v["source1"]) or "clean",
                     ",".join(v["source2"]) or "clean"))

    out.write("\n=== VERDICT ===\n")
    rc = 0
    forbn = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    for s1 in s1s:
        u = undecided_forbidden(s1, table)
        if u:
            out.write("  UNDECIDED %s: %s\n"
                      % (os.path.basename(s1["path"]), ",".join(u)))
            rc = max(rc, 3)
    # Source (1)'s findings are reported per ELF whether or not an object
    # directory was paired with it.  They were once reported only through the
    # pair verdict, so `scan --elf <dirty file>` with no --objdir exited 0 --
    # the tool's own agreement bookkeeping swallowing a finding.
    # `test-uspacescan.sh` S1 is that case.
    for s1 in s1s:
        f = [n for n in forbn if s1["recs"][n]["present"]]
        if f:
            out.write("  FINDING   (1) %s  %s\n" % (s1["path"], ",".join(f)))
            rc = max(rc, 1)
    for d, s2 in sorted(s2s.items()):
        f = [n for n in forbn if s2["total"][n]]
        if f:
            out.write("  FINDING   (2) %s  %s\n" % (d, ",".join(f)))
            rc = max(rc, 1)
    for v in verdicts:
        if v["state"] == "DISAGREE":
            out.write("  DISAGREE  %s  (1)=%s  (2)=%s\n"
                      % (v["label"], ",".join(v["source1"]) or "clean",
                         ",".join(v["source2"]) or "clean"))
            rc = max(rc, 2)
    allo = [r["name"] for r in table if r["cls"] == "ALLOWED"]
    cnt = {}
    for s1 in s1s:
        for n in allo:
            if s1["recs"][n]["present"]:
                cnt[n] = cnt.get(n, 0) + 1
    out.write("  ALLOWED, counted not flagged: %s\n"
              % (", ".join("%s in %d ELF(s)" % (n, c)
                           for n, c in sorted(cnt.items())) or "none"))
    if rc == 0:
        out.write("  CLEAN: %d ELF(s) and %d object dir(s), 0 FORBIDDEN name "
                  "present or referenced\n" % (len(s1s), len(s2s)))
    if a.json:
        blob = dict(
            tool="uspacescan", libc=libc, fp_distinct=a.fp_distinct,
            table=[dict(name=r["name"], cls=r["cls"]) for r in table],
            fingerprints=dict(
                (n, None if fps.get(n) is None else dict(
                    member=fps[n].member, bytes=len(fps[n]),
                    distinct=fps[n].distinct)) for n in names),
            source1=[dict(
                path=s["path"], shape=s["shape"], stripped=s["stripped"],
                eflags=s["eflags"], indirect=s["indirect"],
                gp_convention_ok=s["gp_convention_ok"],
                names=dict((n, dict(
                    imports=r["imports"], defined=r["defined"],
                    fp_state=r["fp_state"], fp_hits=r["fp_hits"],
                    got_refs=r["got_refs"], direct_calls=r["direct_calls"],
                    present=r["present"], undecided=r["undecided"]))
                    for n, r in s["recs"].items())) for s in s1s],
            source2=[dict(objdir=s["objdir"], objects=s["objects"],
                          total=s["total"], per=s["per"])
                     for s in s2s.values()],
            agreement=[dict(label=v["label"], state=v["state"],
                            source1=v["source1"], source2=v["source2"])
                       for v in verdicts],
            exit=rc)
        tmp = a.json + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, indent=1, sort_keys=True)
        os.replace(tmp, a.json)
        out.write("  json      %s\n" % a.json)
    return rc


def cmd_vendor(a, table, out=sys.stdout):
    res, bad = run_controls(table, a.fp_distinct, out)
    if bad:
        raise Refuse("%d control(s) failed; the census is not reported"
                     % len(bad))
    names = [r["name"] for r in table]
    libc = a.libc or default_libc(a.tc)
    fps = build_fingerprints(libc, names) if libc else \
        dict((n, None) for n in names)
    c = vendor_census(a.vendor_census, table, fps, a.fp_distinct)
    forb = [r["name"] for r in table if r["cls"] == "FORBIDDEN"]
    baseline = (sorted(forb) == ["popen", "system"])
    out.write("\n=== VENDOR CENSUS  %s ===\n" % c["root"])
    out.write("  names counted                          %s\n" % ",".join(forb))
    out.write("  regular files (symlinks excluded)      %d\n" % c["files"])
    out.write("  ELF files                              %d\n" % c["elves"])
    out.write("  of those, with no PT_DYNAMIC           %d\n" % c["no_dynamic"])
    out.write("  ELFs matched by the STRING scan        %d%s\n"
              % (c["str_count"],
                 "   (notes/rootfs-census.md FW-20 says 31)" if baseline
                 else "   -- NOT comparable with FW-20's 31, which counted "
                      "system/popen only"))
    out.write("  ELFs matched by the IMPORT walk        %d%s\n"
              % (c["imp_count"],
                 "   (upstream says 28)" if baseline
                 else "   -- NOT comparable with upstream's 28, same reason"))
    sset = set(r["path"] for r in c["rows"] if r["str_dirty"])
    iset = set(r["path"] for r in c["rows"] if r["imp_dirty"])
    out.write("\n  string-only (a name in the file that is NOT an import):\n")
    for p in sorted(sset - iset):
        r = [x for x in c["rows"] if x["path"] == p][0]
        out.write("    %-34s %-8s %s\n"
                  % (p, r["shape"],
                     " ".join("%s=%d" % (k, v)
                              for k, v in sorted(r["str_hits"].items()))))
    out.write("  import-only (an import the string scan missed):\n")
    for p in sorted(iset - sset):
        out.write("    %s\n" % p)
    out.write("\n  the %d by the string scan:\n" % c["str_count"])
    for p in sorted(sset):
        out.write("    %s\n" % p)
    if a.json:
        tmp = a.json + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(dict(root=c["root"], files=c["files"], elves=c["elves"],
                           no_dynamic=c["no_dynamic"],
                           string_count=c["str_count"],
                           import_count=c["imp_count"],
                           string_only=sorted(sset - iset),
                           import_only=sorted(iset - sset),
                           rows=[dict(path=r["path"], shape=r["shape"],
                                      str_hits=r["str_hits"],
                                      imports=r["imports"],
                                      imp_state=r["imp_state"])
                                 for r in c["rows"]]),
                      fh, indent=1, sort_keys=True)
        os.replace(tmp, a.json)
        out.write("  json      %s\n" % a.json)
    return 0


def cmd_self_test(a, table, out=sys.stdout):
    res, bad = run_controls(table, a.fp_distinct, out, label="SELF-TEST, PART 1")
    names = [r["name"] for r in table]
    libc = a.libc or default_libc(a.tc)
    skipped = []
    out.write("\n=== SELF-TEST, PART 2: this libc's own fingerprints ===\n")
    if libc is None:
        out.write("  SKIPPED  no libc.a at %s; source (1c) and every control "
                  "built on it cannot run\n" % os.path.join(a.tc, "lib"))
        skipped.append("fingerprints (no libc.a)")
        fps = dict((n, None) for n in names)
    else:
        fps = build_fingerprints(libc, names)
        out.write("  libc  %s\n" % libc)
        for row in table:
            fp = fps.get(row["name"])
            out.write("  %-7s %-16s %s\n"
                      % ("ok" if fp and fp.distinct >= a.fp_distinct
                         else ("WEAK" if fp else "NOFP"), row["name"],
                         "member=%s %dB %d distinct" % (fp.member, len(fp),
                                                        fp.distinct)
                         if fp else "no archive member defines it"))
    out.write("\n=== SELF-TEST, PART 3: the target toolchain ===\n")
    cc = os.path.join(a.tc, "bin", "mips-linux-gcc")
    if libc is None or not os.path.isfile(cc) or not os.path.isfile(a.trip):
        out.write("  SKIPPED  the planted-positive, stripped, allowed-call and "
                  "disagreement controls need the cross compiler:\n")
        out.write("  SKIPPED    cc   %s  %s\n"
                  % (cc, "present" if os.path.isfile(cc) else "MISSING"))
        out.write("  SKIPPED    trip %s  %s\n"
                  % (a.trip, "present" if os.path.isfile(a.trip) else "MISSING"))
        out.write("  SKIPPED    libc %s\n" % (libc or "MISSING"))
        skipped.append("toolchain controls (T1-T9)")
    else:
        with tempfile.TemporaryDirectory(prefix="uspacescan-") as sc:
            tres, arts = toolchain_controls(table, fps, a.fp_distinct, a.tc,
                                            a.trip, sc, out)
            for lab, exp, got in tres:
                if exp == got:
                    out.write("  ok     %-58s %s\n" % (lab, got))
                else:
                    out.write("  FAIL   %-58s expected %s, got %s\n"
                              % (lab, exp, got))
            res = res + tres
            bad = bad + [r for r in tres if r[1] != r[2]]
    out.write("\n=== SELF-TEST RESULT ===\n")
    npass = len([r for r in res if r[1] == r[2]])
    if bad:
        out.write("  %d passed, %d FAILED, %d skipped group(s)\n"
                  % (npass, len(bad), len(skipped)))
        for lab, exp, got in bad:
            out.write("  FAILED  %s: expected %s, got %s\n" % (lab, exp, got))
        return 1
    if skipped:
        out.write("  %d passed, 0 failed, but %d control group(s) SKIPPED: %s\n"
                  % (npass, len(skipped), "; ".join(skipped)))
        if a.allow_skip:
            out.write("  --allow-skip given, so this exits 0 anyway.  A green "
                      "run that skipped a group certifies only what ran.\n")
            return 0
        out.write("  A self-test that could not run its planted positives is "
                  "not a green self-test.  Pass --allow-skip to accept it.\n")
        return 3
    out.write("  %d passed, 0 failed, 0 skipped\n" % npass)
    return 0


def parse_args(argv):
    p = argparse.ArgumentParser(add_help=True, prog="uspacescan.py",
                                description="R7's system()/popen() gate: two "
                                "sources over rlxfw's userspace, each able to "
                                "come back red.")
    p.add_argument("mode", nargs="?", default=None,
                   choices=["scan", "vendor-census"])
    p.add_argument("--elf", action="append", metavar="F")
    p.add_argument("--objdir", action="append", metavar="D")
    p.add_argument("--pair", action="append", metavar="ELF=OBJDIR")
    p.add_argument("--libc", metavar="libc.a")
    p.add_argument("--tc", default=DEFAULT_TC, metavar="DIR")
    p.add_argument("--trip", default=DEFAULT_TRIP, metavar="PATH")
    p.add_argument("--nm", metavar="PATH",
                   help="cross-check source (2) with this mips-linux-nm, "
                        "through the tripwire; a disagreement is a failure")
    p.add_argument("--table", default=DEFAULT_TABLE, metavar="TSV")
    p.add_argument("--fp-distinct", type=int, default=8, metavar="N",
                   help="reject a code fingerprint with fewer than N distinct "
                        "unmasked 32-bit words (default 8; 量 vfork has 3 and "
                        "every other name in the table has 19 or more)")
    p.add_argument("--only", metavar="N[,N]",
                   help="restrict the table to these names.  The census needs "
                        "it to be compared with a published number: FW-20's 31 "
                        "and upstream's 28 counted `system`/`popen` and nothing "
                        "else, while this tool's table is six names wide, so "
                        "the unrestricted count is a DIFFERENT measurement")
    p.add_argument("--vendor-census", metavar="DIR")
    p.add_argument("--json", metavar="OUT")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--allow-skip", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        table = load_table(a.table)
        if a.only:
            want = [n.strip() for n in a.only.split(",") if n.strip()]
            have = set(r["name"] for r in table)
            miss = [n for n in want if n not in have]
            if miss:
                raise Refuse("--only names %s, which the table %s does not "
                             "carry" % (",".join(miss), a.table))
            keep = [r for r in table
                    if r["name"] in want or r["cls"] == "CONTROL"]
            if not [r for r in keep if r["cls"] == "FORBIDDEN"]:
                raise Refuse("--only leaves no FORBIDDEN name, so nothing "
                             "could be found and 0 would mean nothing")
            if not [r for r in keep if r["cls"] == "ALLOWED"]:
                # The controls need one of each class, and a run with no
                # ALLOWED name cannot show the guard permitting.
                keep = keep + [r for r in table if r["cls"] == "ALLOWED"][:1]
            table = keep
        if a.self_test:
            return cmd_self_test(a, table)
        if a.vendor_census and a.mode in (None, "vendor-census"):
            return cmd_vendor(a, table)
        if a.mode == "scan":
            if not a.elf and not a.objdir:
                raise Refuse("scan needs at least one --elf or --objdir")
            return cmd_scan(a, table)
        raise Refuse("nothing to do; use `scan --elf F`, "
                     "`--vendor-census DIR` or `--self-test`")
    except Refuse as e:
        sys.stdout.flush()
        sys.stderr.write("REFUSED: %s\n" % e)
        return 3
    except KeyboardInterrupt:
        sys.stderr.write("REFUSED: interrupted\n")
        return 3
    except Exception as e:                                  # never a traceback
        sys.stdout.flush()
        sys.stderr.write("REFUSED: %s: %s\n" % (type(e).__name__, e))
        return 3


if __name__ == "__main__":
    sys.exit(main())
