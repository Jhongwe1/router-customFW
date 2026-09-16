#!/usr/bin/env python3
"""tcpay -- `probe6`'s generator, build gate and verdict reader.

`tools/isa-toolchain.tsv` is the owner.  This file turns it into the payload's
thunks, its row table and its per-variant compile rules; gates the linked image
against it in both directions; and reads the device's report back.

WHAT MAKES THIS DIFFERENT FROM `isapay` AND `hazpay`

`isapay` emits one INSTRUCTION per row and asks whether the die has it.
`hazpay` emits one hand-written SEQUENCE per row and asks how deep the pipeline
hazard goes.  Here every row is one COMPILER INVOCATION on one unchanged C file,
and the question is whether the code that compiler emits is wrong on this die.

So the thing that varies between rows is not in this repository at all -- it is
somebody else's compiler -- and the two consequences run through everything
below:

  * the payload cannot contain the expected answers.  Two of the three possible
    readings are constants this payload writes (the sentinel and the source
    word), so a comparison done in the image would be the image agreeing with
    itself.  `verdict` decides at the desk, exactly as `isapay` and `hazpay` do.
  * the BUILD is a reading.  `pad` in the table is a prediction about what a
    compiler will do, and `verify` checks it against the artefact word by word.
    A toolchain that changes its mind fails the build rather than quietly
    producing a row that cannot mean anything.

THE GATE, AND WHY IT IS NOT `hazlint` ALONE

`probe6` contains load-use violations ON PURPOSE -- that is the experiment --
so `hazlint` exiting 0 is a BUILD FAILURE here, the same inversion
`tools/hazdecl.py` carries for `probe5`.  `hazdecl` itself cannot be reused: its
`P5`..`P12` read `hazpay`'s row table and `isa-hazard.tsv`'s distances, which
this payload does not have.  So `gate` is hazdecl's resolution ③ -- run the
UNMODIFIED `hazlint` over the WHOLE linked image, no flag restricting what it
scans, and adjudicate its output in both directions -- re-implemented against
this table, plus one check that does not go through `hazlint` at all.

  G1  the number of violation RECORDS parsed equals the VIOLATIONS count.
      The control on this tool's own parser.  `hazdecl`'s `P1` records two
      parsers that were wrong about this same output on 2026-09-13, one of them
      reading a control line and reporting the same number for every case.
  G2  loads > 0.  A tool that is not looking reports zero loads, not zero
      violations.
  G3  unresolved successors == 0.  An unchecked successor is an unchecked load.
  G4  `hazlint`'s exit code is 1.  0 means every `nopad` variant was padded and
      the experiment is gone; 2 and 3 are refusals, and a refusal is not a
      verdict.
  G5  every violation sits at a declared `nopad` site -- load at the row's `lw`,
      successor at its `sw`.
  G6  every declared `nopad` site appears in the violation list.
  G7  NO `pad` row's site appears in the violation list.  This is the direction
      a gate that only counted violations could never have, and it is what
      proves the padding is really there.
  G8  THE SECOND INSTRUMENT, and it does not use `hazlint`.  For every row, the
      words at its site are read out of the ELF and must be exactly
      `lw v0,0(a1)` [`nop`] `sw v0,0(a0)`.  Two instruments, two claims, no
      overlap -- `hazdecl`'s `P12` in this table's vocabulary.

THE CONTROLS ON THE VERDICT

  `c_lock` must read LOCK and `c_open` must read OPEN.  Both are hand-written
  and neither goes through a compiler, so between them they say the harness can
  observe both answers.  A verdict with either missing or wrong is REFUSED, not
  reported: `plan:1074`'s two halves, and `CLAUDE.md`'s *a tool reporting 0 is
  making a claim*.

  Under `--arm qemu` EVERY row must read LOCK, because qemu interlocks.  A qemu
  run that reproduces the device's OPEN rows means the harness is reading
  something other than the hazard.  Forced anti-control, `hazpay`'s `C4`.

usage
    tcpay.py population
    tcpay.py emit [--check]
    tcpay.py verify ELF
    tcpay.py gate ELF [--hazlint PATH]
    tcpay.py verdict LOG [--arm device|qemu]
    tcpay.py --self-test

exit
    0  clean
    1  a finding
    3  REFUSED -- nothing parsed, a control failed, or no mode given
"""

import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# `TCPAY_TSV` exists for ONE reason and it is stated here rather than left to be
# found: four of the self-test's cases assert on this tool's EXIT CODE, and an
# exit code can only be read by running the tool as a subprocess -- `hazdecl`'s
# and `check-predictions`' suites both do the same.  A subprocess needs to be
# pointed at the synthetic table the case built.  It is never set in normal use;
# `population` prints the path it actually read so a run under it cannot be
# mistaken for a run against the committed table.
TSV = os.environ.get("TCPAY_TSV") or os.path.join(HERE, "isa-toolchain.tsv")
PROBE = os.path.join(HERE, "rlxprobe")

VERSION = "1.0"

# --- the constants the payload uses, and the reason each one is this value ----
#
# All three are `probe5`'s, on purpose: a reader who has the hazard ladder in
# front of them should not have to learn a second vocabulary to read this table.
# `tools/isa-hazard.tsv` uses A5A5F00D for *the producer's result* and B10CB10C
# for *the consumer's prior value*, and those are exactly the two roles here.
SRC_VAL = 0xA5A5F00D     # what the fragment's source cell holds -- the LOADED value
SENTINEL = 0xB10CB10C    # what v0 holds one instruction before the load -- the STALE value
DST_INIT = 0x5A5A0FF2    # what the destination holds before the call -- *the store never happened*

# The three instruction encodings the fragment is allowed to be.  Big-endian
# MIPS-I, and every column of `tools/isa-toolchain.tsv` was measured emitting
# exactly these on 2026-09-14 at the desk.
I_LW = 0x8CA20000        # lw   $v0, 0($a1)
I_NOP = 0x00000000       # nop
I_SW = 0xAC820000        # sw   $v0, 0($a0)

# Eight, and the same eight `probe5` uses, because a reader who has that ladder
# in front of them should not have to learn a second layout either.  w0 is the
# TAG: `P6_TAG_BASE | i`, written before the row runs, so a row that never ran is
# distinguishable from a row that ran and produced zeros -- poison, tag and
# result are three states, not two.
ROW_WORDS = 8
HDR_WORDS = 32
W_TAG, W_N, W_CAUSE, W_EPC, W_COLD, W_WARM, W_AUX, W_PRE = range(8)
TAG_BASE = 0x50060000

# --- the toolchains ----------------------------------------------------------
#
# 🔴 WHICH BINARY IS THE DRIVER IS A MEASUREMENT, NOT A GUESS.  `SPEC.md`
# `TC-50` / `docs/toolchain-comparison.md`: in rsdk-1.5.5 the file called
# `mips-linux-gcc` is a WRAPPER and the real driver is `mips-linux-xgcc`, while
# in the two 1.3.6 drops `mips-linux-gcc` is the driver and `rsdk-linux-gcc` is
# the wrapper.  A wrapper accepts one `-march` and refuses the others, so a
# table that named the wrong binary would report `build-fail` for half this
# population and look like a finding about the toolchain.
#
# `T4` is the host cross-compiler.  It is here as the INSTRUMENT'S OWN CONTROL
# -- every payload this project has ever run on this die was built with it, at
# `-march=mips1` -- and not as a fourth column of `R2c`, which names three rsdk
# releases and no other.
TOOLCHAINS = {
    "T1": ("rsdk-1.3.6-4181-EB-2.6.30-0.9.30", "mips-linux-gcc",
           "rsdk 1.3.6, gcc 3.4.6-1.3.6, binutils 2.16.94, 4181 release"),
    "T2": ("rsdk-1.3.6-5281-EB-2.6.30-0.9.30", "mips-linux-gcc",
           "rsdk 1.3.6, gcc 3.4.6-1.3.6, binutils 2.16.94, 5281 release"),
    "T3": ("rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714", "mips-linux-xgcc",
           "rsdk 1.5.5p4, gcc 4.4.5, binutils 2.19.92, 5281 release"),
    "T4": (None, "mips-linux-gnu-gcc",
           "host cross-compiler, gcc 12.4.0, binutils 2.42 -- the instrument"),
}

# The flags the FRAGMENT is built with.  Deliberately minimal and identical in
# every column: the only thing that may differ between two fragment objects is
# the driver and the `-march`.  `-Wall -Wextra -Werror` are NOT here, and
# `-fno-stack-protector` is NOT here -- `docs/toolchain-comparison.md` measured
# gcc 3.4.6 rejecting `-fstack-protector` outright, so the negative form is not
# safe to assume and a flag that only some columns accept is a second variable.
FRAG_CFLAGS = "-O2 -mabi=32 -msoft-float -EB -G0 -mno-abicalls -fno-pic"


class Refuse(Exception):
    pass


# ============================================================ the table

class Row(object):
    __slots__ = ("vid", "tc", "march", "pad", "expect", "why", "lineno")

    def __init__(self, vid, tc, march, pad, expect, why, lineno):
        self.vid = vid
        self.tc = tc
        self.march = march
        self.pad = pad
        self.expect = expect
        self.why = why
        self.lineno = lineno

    @property
    def is_control(self):
        return self.tc == "--"

    @property
    def sym(self):
        """The symbol whose FIRST instruction is the `lw`.

        Uniform across compiled variants and controls: `cells6.S` puts a global
        label immediately before the load in the controls too, so that every
        row's site is `rlxf_<vid> + 0` and `verify` needs no special case.
        """
        return "rlxf_" + self.vid

    @property
    def thunk(self):
        return "rlxp6_" + self.vid

    @property
    def words(self):
        """The instruction words this row's site must contain, as built."""
        if self.pad == "pad":
            return (I_LW, I_NOP, I_SW)
        return (I_LW, I_SW)


def read_table(path=TSV):
    if not os.path.isfile(path):
        raise Refuse("%s: no such file" % path)
    rows = []
    seen = set()
    hdr = None
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            if "|" in line:
                raise Refuse("%s:%d: a `|` in this file breaks spec-check C8's "
                             "cell count on any table that quotes it" % (path, n))
            f = line.split("\t")
            if hdr is None:
                hdr = f
                if hdr[:6] != ["vid", "tc", "march", "pad", "expect", "why"]:
                    raise Refuse("%s:%d: header is %r, not the six columns this "
                                 "tool knows" % (path, n, hdr))
                continue
            if len(f) != 6:
                raise Refuse("%s:%d: %d tab-separated fields, want 6"
                             % (path, n, len(f)))
            vid, tc, march, pad, expect, why = f
            if not re.match(r"^[a-z0-9_]+$", vid):
                raise Refuse("%s:%d: vid %r is not [a-z0-9_]+ -- it becomes a C "
                             "identifier and an asm label" % (path, n, vid))
            if vid in seen:
                raise Refuse("%s:%d: duplicate vid %r" % (path, n, vid))
            seen.add(vid)
            if tc != "--" and tc not in TOOLCHAINS:
                raise Refuse("%s:%d: toolchain %r is not in this tool's map"
                             % (path, n, tc))
            if pad not in ("pad", "nopad"):
                raise Refuse("%s:%d: pad is %r, want pad or nopad" % (path, n, pad))
            if expect not in ("lock", "open"):
                raise Refuse("%s:%d: expect is %r, want lock or open"
                             % (path, n, expect))
            # The prediction is a COMPOSITION and this is where that is enforced:
            # `pad` plus CPU-58 determines `expect`, so a row where they
            # disagree is a typo, not a hypothesis.  A future die on which d0 is
            # closed changes this rule; it does not get to change one row.
            want = "lock" if pad == "pad" else "open"
            if expect != want:
                raise Refuse("%s:%d: %s says pad=%s and expect=%s. expect is "
                             "DERIVED from pad plus CPU-58 (lu_sd_d0 OPEN); the "
                             "two cannot disagree row by row"
                             % (path, n, vid, pad, expect))
            if (tc == "--") != (march == "--"):
                raise Refuse("%s:%d: %s has tc=%r and march=%r -- a control has "
                             "neither, a variant has both" % (path, n, vid, tc, march))
            if not why.strip():
                raise Refuse("%s:%d: %s has an empty `why`" % (path, n, vid))
            rows.append(Row(vid, tc, march, pad, expect, why, n))
    if hdr is None:
        raise Refuse("%s: no header row" % path)
    if not rows:
        raise Refuse("%s: no rows. Reporting `0 of 0` on an empty population is "
                     "the failure this refusal exists to prevent" % path)
    ctl = [r.vid for r in rows if r.is_control]
    if "c_lock" not in ctl or "c_open" not in ctl:
        raise Refuse("%s: the two controls c_lock and c_open must both be "
                     "present. Found %r" % (path, ctl))
    return rows


def rb_words(rows):
    seal = HDR_WORDS + len(rows) * ROW_WORDS
    n = seal + 1
    # `LDR-07`: `DW a N` returns 4*ceil(N/4) words, so a block whose length is a
    # multiple of four returns no word past its own seal -- and an over-writing
    # payload writes UPWARD from the seal, which is exactly where the evidence
    # would be.  33 + 6R is 1 mod 4 for even R and 3 mod 4 for odd R, so it can
    # never be 0 -- but the guard is here rather than in a comment because the
    # row width is a constant somebody may change.
    if n % 4 == 0:
        raise Refuse("RB_WORDS = %d is a multiple of four, so a DW of exactly "
                     "that many words would return no poison past the seal and "
                     "an over-write would be invisible. Change ROW_WORDS." % n)
    return n


# ============================================================ emit

def emit_cells(rows):
    out = []
    a = out.append
    a("/* cells6.S -- GENERATED by tools/tcpay.py from tools/isa-toolchain.tsv.")
    a(" * DO NOT EDIT.  Edit the table.")
    a(" *")
    a(" * One thunk per row.  The thunk's whole job is to put the SENTINEL in")
    a(" * $v0 in the instruction immediately before the load, so that a store")
    a(" * which reads $v0 too early has a known value to read.  For a compiled")
    a(" * variant that instruction is the `jal`'s delay slot; for a control it")
    a(" * is written in line.  Both are the same shape and that is the point.")
    a(" *")
    a(" * $a0 = destination word, $a1 = source word, $a2 = the sentinel.")
    a(" */")
    a("#include \"rlxdefs.h\"")
    a("")
    a("\t.set\tnoreorder")
    a("\t.set\tnoat")
    a("\t.set\tnomacro")
    a("\t.text")
    a("")
    for r in rows:
        a("/* %s -- %s */" % (r.vid, r.why.strip()))
        a("\t.globl\t%s" % r.thunk)
        a("\t.ent\t%s" % r.thunk)
        a("%s:" % r.thunk)
        if r.is_control:
            # The control IS the site.  The global label sits immediately before
            # the load so that every row's site is `rlxf_<vid> + 0`.
            a("\tmove\t$v0, $a2")
            a("\t.globl\t%s" % r.sym)
            a("%s:" % r.sym)
            a("\tlw\t$v0, 0($a1)")
            if r.pad == "pad":
                a("\tnop")
            a("\tsw\t$v0, 0($a0)")
            a("\tjr\t$ra")
            a("\tnop")
        else:
            # `rlxf_<vid>` is defined by the variant's own object file, built by
            # a compiler that is under test.  Nothing here may assume anything
            # about it except the calling convention.
            a("\taddiu\t$sp, $sp, -8")
            a("\tsw\t$ra, 0($sp)")
            a("\tjal\t%s" % r.sym)
            a("\tmove\t$v0, $a2\t\t/* delay slot: the sentinel, one instruction"
              " before the callee's load */")
            a("\tlw\t$ra, 0($sp)")
            a("\tnop\t\t\t/* this payload's OWN load-use pad -- d0 is open on"
              " this die */")
            a("\taddiu\t$sp, $sp, 8")
            a("\tjr\t$ra")
            a("\tnop")
        a("\t.end\t%s" % r.thunk)
        a("")
    return "\n".join(out) + "\n"


def emit_rows_h(rows):
    out = []
    a = out.append
    a("/* probe6rows.h -- GENERATED by tools/tcpay.py.  DO NOT EDIT. */")
    a("#ifndef RLXPROBE6_ROWS_H")
    a("#define RLXPROBE6_ROWS_H")
    a("")
    a("#define P6_ROWS\t\t%uu" % len(rows))
    a("#define P6_ROW_WORDS\t%uu" % ROW_WORDS)
    a("#define P6_TAG_BASE\t0x%08Xu" % TAG_BASE)
    a("")
    a("#define P6_SRC_VAL\t0x%08Xu" % SRC_VAL)
    a("#define P6_SENTINEL\t0x%08Xu" % SENTINEL)
    a("#define P6_DST_INIT\t0x%08Xu" % DST_INIT)
    a("")
    # `unsigned`, not `unsigned long`: both are 32 bits on o32, but `rlxprobe.h`
    # defines `u32` as `unsigned int` and the payload is built `-Wall -Wextra
    # -Werror`, so the pointer types have to be the same type and not merely the
    # same width.
    a("typedef void (*p6_thunk)(volatile unsigned *d,")
    a("\t\t\t volatile const unsigned *s, unsigned sent);")
    a("")
    a("extern const char *const p6_names[P6_ROWS];")
    a("extern const p6_thunk p6_thunks[P6_ROWS];")
    a("")
    a("#endif")
    return "\n".join(out) + "\n"


def emit_rows_c(rows):
    out = []
    a = out.append
    a("/* probe6rows.c -- GENERATED by tools/tcpay.py.  DO NOT EDIT.")
    a(" *")
    a(" * A separate translation unit rather than an include, so that nothing in")
    a(" * the build holds two definitions of the row table -- probe5's rule.")
    a(" */")
    a("#include \"probe6rows.h\"")
    a("")
    for r in rows:
        a("void %s(volatile unsigned *d, volatile const unsigned *s,"
          " unsigned sent);" % r.thunk)
    a("")
    a("const char *const p6_names[P6_ROWS] = {")
    for r in rows:
        a("\t\"%s\"," % r.vid)
    a("};")
    a("")
    a("const p6_thunk p6_thunks[P6_ROWS] = {")
    for r in rows:
        a("\t%s," % r.thunk)
    a("};")
    return "\n".join(out) + "\n"


def emit_rows_mk(rows):
    """The per-variant compile rules.

    🔴 THE RULE NAMES THE DRIVER AND THE `-march` IN THE RECIPE AND IN THE
    OBJECT'S PATH.  `tools/rlxprobe/Makefile`'s `.flags` stamp covers `$(DEFS)`,
    `LOADADDR` and `STACK_SIZE` and NOT `CROSS` or `ARCH` -- so a rebuild after
    a toolchain change relinks nothing and ships the previous compiler's binary
    while `make show` prints the one that was asked for.  Here the object path
    contains the variant id, so two variants can never be one file; and the
    recipe's own text changes when the table does, which the `.mk`'s presence as
    a prerequisite turns into a rebuild.
    """
    out = []
    a = out.append
    a("# probe6rows.mk -- GENERATED by tools/tcpay.py.  DO NOT EDIT.")
    a("")
    a("P6_ROWS      := %d" % len(rows))
    a("RB_WORDS_probe6 := %d" % rb_words(rows))
    a("")
    a("FWRE_WORK    ?= /home/key/fwre-work")
    a("TCROOT       ?= $(FWRE_WORK)/rebuild/r2ab/tc")
    a("FRAG_CFLAGS  := %s" % FRAG_CFLAGS)
    a("")
    a("# 🔴 THE rsdk DRIVERS CANNOT READ A SOURCE FILE ON DrvFs, AND THIS IS A")
    a("# REFUSAL BECAUSE THE SYMPTOM POINTS AT THE WRONG THING.  量 2026-09-14,")
    a("# with the control beside it: `mips-linux-gcc` is a 32-bit i386 ELF, and")
    a("# `/mnt/c` hands it inode 49539595901085916 -- which does not fit a 32-bit")
    a("# `struct stat`, so `cc1` dies with")
    a("#")
    a("#     cc1: .../frag.c: Value too large for defined data type")
    a("#")
    a("# The SAME BYTES copied to ext4 compile to a 928-byte object.  The message")
    a("# names the source file and reads like a defect in it, which is why this")
    a("# is a named refusal and not a comment.  `CLAUDE.md`'s rule is *binaries")
    a("# and vendor source trees never live under /mnt/c*; this is its third face")
    a("# -- a vendor binary cannot READ a file there either.")
    a("ifeq ($(P),probe6)")
    a("ifneq ($(findstring /mnt/,$(abspath $(BUILD))),)")
    a("$(error probe6 needs BUILD= on a real Linux filesystem. $(abspath $(BUILD))"
      " is DrvFs, and the 32-bit rsdk drivers cannot stat a file there --"
      " `Value too large for defined data type`, which names frag.c and means"
      " the filesystem. Use BUILD=$(FWRE_WORK)/rebuild/<something>)")
    a("endif")
    a("endif")
    a("")
    a("# And the fragment is compiled from a COPY inside $(OBJDIR) for the same")
    a("# reason: `$(HERE)frag.c` is in the repository, which is on DrvFs.  The")
    a("# copy is a prerequisite rather than a recipe step so that `make -n` still")
    a("# reports honestly, and `cp -p` keeps the mtime so the copy is not newer")
    a("# than its source on every build.")
    a("$(OBJDIR)/frag.c: $(HERE)frag.c | $(OBJDIR)")
    a("\tcp -p $< $@")
    a("")
    variants = [r for r in rows if not r.is_control]
    # 🔴 Keyed on the payload name.  This file is `-include`d unconditionally, so
    # a bare `P6_FRAGOBJS` would be in scope for probe0..probe5 too and the link
    # line would pull ten foreign objects into an unrelated image.
    a("FRAGOBJS_probe6 := %s" % " ".join(
        "$(OBJDIR)/frag-%s.o" % r.vid for r in variants))
    a("")
    for r in variants:
        d, drv, _ = TOOLCHAINS[r.tc]
        cc = drv if d is None else "$(TCROOT)/%s/bin/%s" % (d, drv)
        a("# %s: %s, -march=%s" % (r.vid, TOOLCHAINS[r.tc][2], r.march))
        a("P6_CC_%s := %s" % (r.vid, cc))
        a("$(OBJDIR)/frag-%s.o: $(OBJDIR)/frag.c $(HERE)probe6rows.mk | $(OBJDIR)"
          % r.vid)
        a("\t@echo '  FRAG   %-8s %s -march=%s'" % (r.vid, drv, r.march))
        a("\t$(P6_CC_%s) -march=%s $(FRAG_CFLAGS) -Drlxf=%s -c -o $@ $<"
          % (r.vid, r.march, r.sym))
        a("")
    return "\n".join(out) + "\n"


GENERATED = (
    ("cells6.S", emit_cells),
    ("probe6rows.h", emit_rows_h),
    ("probe6rows.c", emit_rows_c),
    ("probe6rows.mk", emit_rows_mk),
)


def cmd_emit(rows, check):
    bad = 0
    for name, fn in GENERATED:
        path = os.path.join(PROBE, name)
        new = fn(rows)
        old = None
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                old = fh.read()
        if check:
            if old != new:
                print("  STALE  %s" % name)
                bad += 1
            else:
                print("  ok     %s" % name)
        else:
            if old == new:
                print("  same   %s" % name)
            else:
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(new)
                os.replace(tmp, path)
                print("  wrote  %s" % name)
    if check and bad:
        print("")
        print("%d generated file(s) do not match the table. Run "
              "`tcpay.py emit`." % bad)
        return 1
    return 0


# ============================================================ a minimal ELF reader

class Elf(object):
    """Just enough 32-bit big-endian ELF to read a symbol's instructions.

    Deliberately not objdump: a gate that shells out to a disassembler is a gate
    that depends on which binutils is on PATH, and this payload exists to
    compare three of them.
    """

    def __init__(self, path):
        with open(path, "rb") as fh:
            self.b = fh.read()
        if self.b[:4] != b"\x7fELF":
            raise Refuse("%s: not an ELF" % path)
        if self.b[4] != 1 or self.b[5] != 2:
            raise Refuse("%s: not 32-bit big-endian ELF" % path)
        (self.e_shoff,) = struct.unpack_from(">I", self.b, 0x20)
        (self.e_shentsize,) = struct.unpack_from(">H", self.b, 0x2E)
        (self.e_shnum,) = struct.unpack_from(">H", self.b, 0x30)
        (self.e_shstrndx,) = struct.unpack_from(">H", self.b, 0x32)
        self.sh = []
        for i in range(self.e_shnum):
            o = self.e_shoff + i * self.e_shentsize
            name, typ, flags, addr, off, size, link, info, align, entsize = \
                struct.unpack_from(">10I", self.b, o)
            self.sh.append(dict(name=name, type=typ, flags=flags, addr=addr,
                                off=off, size=size, link=link, entsize=entsize))
        strtab = self.sh[self.e_shstrndx]
        for s in self.sh:
            s["sname"] = self._cstr(strtab["off"] + s["name"])
        self.syms = {}
        for s in self.sh:
            if s["type"] != 2:                       # SHT_SYMTAB
                continue
            st = self.sh[s["link"]]
            n = s["size"] // 16
            for i in range(n):
                o = s["off"] + i * 16
                nm, val, sz, info, other, shndx = \
                    struct.unpack_from(">IIIBBH", self.b, o)
                name = self._cstr(st["off"] + nm)
                if name:
                    self.syms[name] = (val, sz, shndx)

    def _cstr(self, o):
        e = self.b.index(b"\x00", o)
        return self.b[o:e].decode("ascii", "replace")

    def words_at(self, vaddr, n):
        for s in self.sh:
            if s["type"] == 8:                       # SHT_NOBITS -- .bss
                continue
            if not (s["flags"] & 0x4):               # SHF_EXECINSTR
                continue
            if s["addr"] <= vaddr < s["addr"] + s["size"]:
                o = s["off"] + (vaddr - s["addr"])
                if o + 4 * n > len(self.b):
                    raise Refuse("0x%08x+%d words runs past the file" % (vaddr, n))
                return list(struct.unpack_from(">%dI" % n, self.b, o))
        raise Refuse("0x%08x is in no executable section" % vaddr)


MNEM = {I_LW: "lw   $v0,0($a1)", I_NOP: "nop", I_SW: "sw   $v0,0($a0)"}


def _mn(w):
    return MNEM.get(w, "0x%08X -- NOT one of the three this fragment may be" % w)


def cmd_verify(rows, path, quiet=False):
    """G8, standalone.  The shape of every row's site, read out of the ELF."""
    e = Elf(path)
    bad = 0
    if not quiet:
        print("verify: %s" % path)
        print("")
        print("  %-8s %-6s %-10s %s" % ("row", "pad", "addr", "as built"))
    for r in rows:
        if r.sym not in e.syms:
            print("  MISSING  %s -- no symbol %s in the image" % (r.vid, r.sym))
            bad += 1
            continue
        addr = e.syms[r.sym][0]
        want = r.words
        got = e.words_at(addr, len(want))
        ok = (got == list(want))
        if not ok:
            bad += 1
        if not quiet or not ok:
            mark = "ok    " if ok else "REFUTED"
            print("  %-8s %-6s 0x%08X %s" % (r.vid, r.pad, addr, mark))
            for i, (w, g) in enumerate(zip(want, got)):
                flag = " " if w == g else "<"
                print("      +%-2d  %s%s" % (i * 4, _mn(g), flag))
            if not ok:
                print("      the table says this build %ss. It does not."
                      % r.pad)
    if bad:
        print("")
        print("REFUSED: %d row(s) are not the shape the table declares. A row "
              "whose build is not what was predicted cannot be read as evidence "
              "about that compiler." % bad)
        return 1
    if not quiet:
        print("")
        print("  %d row(s), every site is exactly the declared shape."
              % len(rows))
    return 0


# ============================================================ gate

HZ_VIOL = re.compile(r"^\s*0x([0-9a-f]{8})\s+file\s+0x[0-9a-f]+\s+\S", re.M)


def run_hazlint(path, hazlint):
    p = subprocess.run([sys.executable, hazlint, path],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def parse_hazlint(text):
    """The violation records, plus the three counters G1..G3 need.

    A violation record is two consecutive address lines -- the load and the
    instruction that reads its result -- followed by a `reads $xx` line.  The
    counters are read from the summary block by name.
    """
    def counter(label):
        m = re.search(r"^\s+%s\s+(\d+)" % re.escape(label), text, re.M)
        return int(m.group(1)) if m else None

    loads = counter("loads (MIPS-I load-to-GPR, rt != $zero)")
    unres = counter("successor unresolved")
    viols = counter("VIOLATIONS")

    recs = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if "reads $" not in ln:
            continue
        a = None
        b = None
        for j in range(i - 1, max(-1, i - 4), -1):
            m = re.match(r"^\s*0x([0-9a-f]{8})\s", lines[j])
            if m:
                if b is None:
                    b = int(m.group(1), 16)
                else:
                    a = int(m.group(1), 16)
                    break
        if a is not None and b is not None:
            recs.append((a, b))
    return loads, unres, viols, recs


def cmd_gate(rows, path, hazlint):
    print("tcpay gate %s -- hazlint over the whole image, adjudicated both ways"
          % VERSION)
    print("")
    rc, text = run_hazlint(path, hazlint)
    loads, unres, viols, recs = parse_hazlint(text)
    findings = []

    if viols is None or loads is None or unres is None:
        print(text)
        raise Refuse("could not find hazlint's summary counters. Nothing is "
                     "reported about this image until the parser is trusted.")

    # G1 -- the control on this tool's own parser, first.
    if len(recs) != viols:
        findings.append("G1 parsed %d violation record(s), hazlint counted %d. "
                        "This tool's parser is wrong and every check below "
                        "would be reporting on it, not on the image."
                        % (len(recs), viols))
    # G2
    if loads == 0:
        findings.append("G2 hazlint found 0 loads. A tool that is not looking "
                        "reports zero loads, not zero violations.")
    # G3
    if unres != 0:
        findings.append("G3 %d unresolved successor(s). An unchecked successor "
                        "is an unchecked load." % unres)
    # G4
    if rc == 0:
        findings.append("G4 hazlint exited 0. For probe6 that is a BUILD "
                        "FAILURE: every `nopad` variant was padded, so the "
                        "experiment is not in this image.")
    elif rc not in (1,):
        findings.append("G4 hazlint exited %d. 2 and 3 are refusals, and a "
                        "refusal is not a verdict." % rc)

    e = Elf(path)
    sites = {}
    for r in rows:
        if r.sym not in e.syms:
            findings.append("G5 no symbol %s in the image" % r.sym)
            continue
        a = e.syms[r.sym][0]
        sites[a] = r

    declared = set()
    for a, r in sites.items():
        if r.pad == "nopad":
            declared.add((a, a + 4))

    seen = set(recs)
    # G5 -- every violation is at a declared nopad site
    for rec in sorted(seen):
        if rec not in declared:
            findings.append("G5 violation at load 0x%08X -> 0x%08X is at no "
                            "declared `nopad` site" % rec)
    # G6 -- every declared nopad site is in the violation list
    for rec in sorted(declared):
        if rec not in seen:
            findings.append("G6 declared `nopad` site %s (load 0x%08X) does not "
                            "appear in hazlint's violations -- it was padded "
                            "after all" % (sites[rec[0]].vid, rec[0]))
    # G7 -- no `pad` row appears
    for a, r in sorted(sites.items()):
        if r.pad == "pad":
            for rec in seen:
                if rec[0] == a:
                    findings.append("G7 `pad` row %s appears as a violation at "
                                    "0x%08X. Its padding is not there."
                                    % (r.vid, a))

    print("  hazlint rc=%d  loads=%s  unresolved=%s  violations=%s  parsed=%d"
          % (rc, loads, unres, viols, len(recs)))
    print("  declared nopad sites: %d   pad sites: %d"
          % (len(declared), sum(1 for r in rows if r.pad == "pad")))
    print("")

    # G8 -- the second instrument.
    g8 = cmd_verify(rows, path, quiet=True)
    if g8:
        findings.append("G8 the shape check refused -- see above.")

    if findings:
        for f in findings:
            print("  %s" % f)
        print("")
        print("RESULT: %d finding(s)." % len(findings))
        return 1
    print("  ok     G1..G8: every violation is a declared `nopad` site, every "
          "declared site is present,")
    print("         no `pad` row appears in either direction, and the shape "
          "check agrees without hazlint.")
    return 0


# ============================================================ verdict

ROW_RE = re.compile(
    r"^P6\s+([0-9a-f]{8})\s+([a-z0-9_]+)((?:\s+[0-9a-f]{8}){%d})\s*$" % ROW_WORDS,
    re.M | re.I)


def read_capture(path):
    with open(path, "rb") as fh:
        b = fh.read()
    return b.decode("ascii", "replace").replace("\r\n", "\n").replace("\r", "\n")


def cmd_verdict(rows, path, arm):
    text = read_capture(path)
    by_vid = {}
    for m in ROW_RE.finditer(text):
        idx = int(m.group(1), 16)
        vid = m.group(2)
        w = [int(x, 16) for x in m.group(3).split()]
        by_vid[vid] = (idx, w)
    if not by_vid:
        raise Refuse("no `P6 <idx> <vid> <6 words>` row parsed out of %s. "
                     "Nothing is reported: an empty parse and a payload that "
                     "printed nothing are the same bytes." % path)

    print("verdict (%s arm): %s" % (arm, path))
    print("")
    print("  %-8s %-6s %-8s %-10s %-10s %-10s %s"
          % ("row", "pad", "verdict", "cold", "warm", "aux", "note"))

    out = []
    for r in rows:
        if r.vid not in by_vid:
            out.append((r, "NOT-RUN", None, "no row in the capture"))
            continue
        idx, w = by_vid[r.vid]
        n, cause, epc = w[W_N], w[W_CAUSE], w[W_EPC]
        cold, warm, aux, pre = w[W_COLD], w[W_WARM], w[W_AUX], w[W_PRE]
        note = ""
        if w[W_TAG] != (TAG_BASE | idx):
            v = "NOT-RUN"
            note = ("tag is 0x%08X, want 0x%08X -- this row never started"
                    % (w[W_TAG], TAG_BASE | idx))
        elif n:
            v = "TRAPS"
            note = "n=%d cause=0x%08X epc=0x%08X" % (n, cause, epc)
        elif pre != DST_INIT:
            v = "VOID"
            note = ("destination read back 0x%08X before the call, want 0x%08X "
                    "-- the payload could not set up this row"
                    % (pre, DST_INIT))
        elif aux != SRC_VAL:
            v = "VOID"
            note = ("source word read back 0x%08X, want 0x%08X -- the load had "
                    "nothing to load" % (aux, SRC_VAL))
        elif cold != warm:
            v = "SPLIT"
            note = "cold and warm disagree"
        elif cold == SRC_VAL:
            v = "LOCK"
        elif cold == SENTINEL:
            v = "OPEN"
        elif cold == DST_INIT:
            v = "VOID"
            note = "destination untouched -- the store never happened"
        else:
            v = "OTHER"
            note = "neither constant"
        out.append((r, v, w, note))
        print("  %-8s %-6s %-8s %-10s %-10s %-10s %s"
              % (r.vid, r.pad, v, "%08X" % cold, "%08X" % warm,
                 "%08X" % aux, note))

    print("")
    tally = {}
    for _, v, _, _ in out:
        tally[v] = tally.get(v, 0) + 1
    print("  %d row(s), %s" % (len(out),
          ", ".join("%s %d" % (k, tally[k]) for k in sorted(tally))))
    print("")

    rc = check_controls(out, arm)
    if rc:
        return rc

    # 🔴 `expect` IS A CLAIM ABOUT THIS DIE, AND QEMU IS NOT THIS DIE.  Caught by
    # `T20`: the first version ran the comparison on both arms, so a qemu run
    # that held the forced anti-control perfectly -- every row LOCK, which is
    # what qemu interlocking MEANS -- was then reported as refuting every
    # `nopad` row's prediction.  The anti-control and the prediction are
    # opposite-signed on that arm, and a tool that reports both is reporting a
    # contradiction it created.
    if arm == "qemu":
        print("  the `expect` column is not read on this arm: it predicts what "
              "THIS DIE does, and an emulator that interlocks is required to "
              "disagree with it. That requirement is the anti-control above.")
        return 0

    print("  the table, read against its own predictions:")
    dis = []
    for r, v, _, _ in out:
        if v in ("LOCK", "OPEN"):
            want = r.expect.upper()
            if v != want:
                dis.append((r, v, want))
    for r, v, want in dis:
        print("    🔴 %-8s predicted %s, read %s" % (r.vid, want, v))
    if not dis:
        print("    every row read the verdict its `pad` column predicts.")
    else:
        print("")
        print("  %d row(s) refuted their prediction. A `nopad` row reading LOCK "
              "refutes CPU-58 under compiler-generated conditions; a `pad` row "
              "reading OPEN refutes the harness." % len(dis))
        return 1
    return 0


def check_controls(out, arm):
    """The two halves of `plan:1074`, plus the forced anti-control."""
    d = {r.vid: (v, w) for r, v, w, _ in out}
    if arm == "qemu":
        bad = [vid for vid, (v, _) in d.items() if v != "LOCK"]
        if bad:
            print("  REFUSED: under qemu every row must read LOCK, because qemu "
                  "interlocks. These did not: %s" % ", ".join(sorted(bad)))
            print("           A qemu run that reproduces the device's OPEN rows "
                  "means the harness is reading something other than the "
                  "hazard.")
            return 3
        print("  the forced anti-control held: %d of %d rows LOCK under qemu."
              % (len(d), len(d)))
        return 0
    missing = [v for v in ("c_lock", "c_open") if v not in d]
    if missing:
        print("  REFUSED: control row(s) %s are not in the capture. A table "
              "whose controls did not run says nothing." % ", ".join(missing))
        return 3
    if d["c_lock"][0] != "LOCK":
        print("  REFUSED: the POSITIVE control c_lock read %s, not LOCK. The "
              "harness cannot show a correct build reading correctly, so every "
              "OPEN below is unattributable." % d["c_lock"][0])
        return 3
    if d["c_open"][0] != "OPEN":
        print("  REFUSED: the NEGATIVE control c_open read %s, not OPEN. This "
              "die's d0 is not open today, so no compiled row can be read as "
              "evidence about a compiler. The table is void, not partly valid."
              % d["c_open"][0])
        return 3
    print("  both controls held: c_lock LOCK, c_open OPEN.")
    return 0


# ============================================================ population

def cmd_population(rows):
    print("tcpay population %s -- %s" % (VERSION, TSV))
    print("")
    print("  toolchains")
    for k in sorted(TOOLCHAINS):
        d, drv, desc = TOOLCHAINS[k]
        where = drv if d is None else "$TCROOT/%s/bin/%s" % (d, drv)
        print("    %-3s %-58s %s" % (k, where, desc))
    print("")
    print("  %-8s %-4s %-7s %-6s %-6s %s"
          % ("vid", "tc", "march", "pad", "expect", "site"))
    for r in rows:
        print("    %-6s %-4s %-7s %-6s %-6s %s"
              % (r.vid, r.tc, r.march, r.pad, r.expect, r.sym))
    print("")
    nv = sum(1 for r in rows if not r.is_control)
    print("  %d row(s): %d compiled variant(s), %d control(s)"
          % (len(rows), nv, len(rows) - nv))
    print("  P6_ROWS=%d  ROW_WORDS=%d  RB_WORDS=%d  RB_POISON_W=%d"
          % (len(rows), ROW_WORDS, rb_words(rows), rb_words(rows) + 8))
    tcs = sorted({r.tc for r in rows if not r.is_control})
    print("  toolchains reaching silicon: %s" % ", ".join(tcs))
    marches = sorted({r.march for r in rows if not r.is_control})
    print("  -march values reaching silicon: %s" % ", ".join(marches))
    return 0


# ============================================================ self-test

def self_test():
    rows_ok = 0
    failed = []

    def case(name, fn):
        nonlocal rows_ok
        try:
            fn()
        except AssertionError as ex:
            failed.append("%s: %s" % (name, ex))
            print("  \033[31mFAIL\033[0m   %s -- %s" % (name, ex))
        else:
            rows_ok += 1
            print("  ok     %s" % name)

    import tempfile

    def write(body):
        fd, p = tempfile.mkstemp(suffix=".tsv")
        os.close(fd)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        return p

    HDR = "vid\ttc\tmarch\tpad\texpect\twhy\n"
    GOOD = (HDR
            + "c_lock\t--\t--\tpad\tlock\tpositive\n"
            + "c_open\t--\t--\tnopad\topen\tnegative\n"
            + "v1\tT4\tmips1\tpad\tlock\tinstrument\n"
            + "v2\tT4\tmips32\tnopad\topen\tthe banned march\n")

    def refuses(body, frag):
        p = write(body)
        try:
            read_table(p)
        except Refuse as ex:
            assert frag in str(ex), "refused with %r, wanted %r" % (str(ex), frag)
            return
        finally:
            os.unlink(p)
        raise AssertionError("accepted a table it must refuse")

    # T1 -- the control on every refusal below: the good table must PASS.
    def t1():
        p = write(GOOD)
        try:
            r = read_table(p)
            assert len(r) == 4, "parsed %d rows" % len(r)
        finally:
            os.unlink(p)
    case("T1  a well-formed table parses (the control on T2..T9)", t1)

    case("T2  an empty population is refused, not reported as 0 of 0",
         lambda: refuses(HDR, "no rows"))
    case("T3  a missing control is refused",
         lambda: refuses(HDR + "v1\tT4\tmips1\tpad\tlock\tx\n",
                         "c_lock and c_open"))
    case("T4  pad and expect may not disagree",
         lambda: refuses(GOOD + "v3\tT4\tmips2\tnopad\tlock\tx\n",
                         "DERIVED from pad"))
    case("T5  an unknown toolchain is refused",
         lambda: refuses(GOOD + "v3\tT9\tmips2\tnopad\topen\tx\n",
                         "not in this tool's map"))
    case("T6  a duplicate vid is refused",
         lambda: refuses(GOOD + "v1\tT4\tmips2\tnopad\topen\tx\n", "duplicate"))
    case("T7  a control with a march is refused",
         lambda: refuses(HDR + "c_lock\t--\tmips1\tpad\tlock\tx\n"
                         + "c_open\t--\t--\tnopad\topen\tx\n",
                         "a control has"))
    case("T8  a pipe anywhere is refused (spec-check C8)",
         lambda: refuses(GOOD + "v3\tT4\tmips2\tnopad\topen\tx|y\n", "spec-check"))
    case("T9  an empty why is refused",
         lambda: refuses(GOOD + "v3\tT4\tmips2\tnopad\topen\t\n", "empty `why`"))

    # T10 -- the layout arithmetic, in both directions.
    def t10():
        p = write(GOOD)
        try:
            r = read_table(p)
            assert rb_words(r) == HDR_WORDS + 4 * ROW_WORDS + 1, "rb_words"
            assert rb_words(r) % 4 != 0, "a DW would show no poison past the seal"
        finally:
            os.unlink(p)
    case("T10 RB_WORDS is HDR + rows*width + 1 and is never 0 mod 4", t10)

    # T11 -- the emitted thunk differs between pad and nopad, and ONLY there.
    def t11():
        p = write(GOOD)
        try:
            r = read_table(p)
            s = emit_cells(r)
            assert "rlxf_c_lock" in s and "rlxf_c_open" in s, "control site labels"
            lock = s.split("rlxf_c_lock:")[1].split(".end")[0]
            opn = s.split("rlxf_c_open:")[1].split(".end")[0]
            assert "nop" in lock.split("sw")[0], "c_lock must be padded"
            assert "nop" not in opn.split("sw")[0], "c_open must NOT be padded"
        finally:
            os.unlink(p)
    case("T11 c_lock emits lw nop sw and c_open emits lw sw", t11)

    # T12 -- the sentinel reaches the delay slot of the jal, for every variant.
    def t12():
        p = write(GOOD)
        try:
            r = read_table(p)
            s = emit_cells(r)
            for vid in ("v1", "v2"):
                blk = s.split("rlxp6_%s:" % vid)[1].split(".end")[0]
                i = blk.index("jal\trlxf_%s" % vid)
                after = blk[i:].splitlines()[1]
                assert "move\t$v0, $a2" in after, \
                    "%s: delay slot is %r" % (vid, after.strip())
        finally:
            os.unlink(p)
    case("T12 every compiled variant primes $v0 in the jal's delay slot", t12)

    # T13 -- the generated Makefile names the right driver per column.
    def t13():
        p = write(GOOD)
        try:
            r = read_table(p)
            mk = emit_rows_mk(r)
            assert "P6_CC_v1 := mips-linux-gnu-gcc" in mk, "T4 driver"
            assert "-Drlxf=rlxf_v1" in mk, "symbol rename"
            assert "frag-v1.o" in mk and "frag-v2.o" in mk, "per-variant objects"
            assert "frag-c_lock.o" not in mk, "a control has no object"
            # keyed on the payload name: an unkeyed variable is in scope for
            # every payload, because the Makefile `-include`s this file always.
            assert "FRAGOBJS_probe6 :=" in mk, "the object list must be keyed"
            assert "\nP6_FRAGOBJS" not in mk, "an unkeyed object list is in scope everywhere"
        finally:
            os.unlink(p)
    case("T13 the generated rules give each variant its own object and driver",
         t13)

    # T14 -- rsdk 1.5.5's driver is the x-one.  The wrapper would refuse half
    # the population and it would look like a finding about the toolchain.
    def t14():
        assert TOOLCHAINS["T3"][1] == "mips-linux-xgcc", "T3 driver"
        assert TOOLCHAINS["T1"][1] == "mips-linux-gcc", "T1 driver"
    case("T14 T3's driver is mips-linux-xgcc and T1's is mips-linux-gcc (TC-50)",
         t14)

    # T15 -- the hazlint parser, against a captured shape.  G1 is the control on
    # it and this is the control on G1.
    def t15():
        sample = (
            "  loads (MIPS-I load-to-GPR, rt != $zero)          2\n"
            "  successor unresolved                             0\n"
            "  VIOLATIONS                                       1\n"
            "\n"
            "  0xff000000  file 0x40     lw    v0,0(a1)                  8ca20000\n"
            "  0xff000004                sll   v0,v0,2                   00021080\n"
            "                             reads $v0   [next word]\n")
        loads, unres, viols, recs = parse_hazlint(sample)
        assert loads == 2, "loads %r" % loads
        assert unres == 0, "unres %r" % unres
        assert viols == 1, "viols %r" % viols
        assert recs == [(0xff000000, 0xff000004)], "recs %r" % recs
    case("T15 the hazlint parser reads the counters and the record", t15)

    # T16 -- and it must NOT read a number off a control line.  This is the
    # exact failure `hazdecl`'s P1 records: two parsers, both printing 2.
    def t16():
        sample = ("  Expected: 2 violations\n"
                  "  loads (MIPS-I load-to-GPR, rt != $zero)          9\n"
                  "  successor unresolved                             0\n"
                  "  VIOLATIONS                                       0\n")
        loads, unres, viols, recs = parse_hazlint(sample)
        assert viols == 0, "read %r off a control line" % viols
        assert recs == [], "invented %d record(s)" % len(recs)
    case("T16 it does not read `Expected: N violations` as the verdict", t16)

    # T17..T20 -- the verdict, driven as a subprocess against synthetic captures
    # so the exit code is read rather than the classification re-implemented.
    def cap(vals, tagbreak=None):
        """vals: {vid: (n, cause, epc, cold, warm, aux, pre)}.

        The TAG is prepended here from the row index rather than written by the
        case, so no case can accidentally agree with a tag it is not.
        `tagbreak` names one row whose tag is left as POISON, which is what the
        block holds for a row the payload never reached."""
        out = ["*** rlxprobe P6 deadbeef ***"]
        for i, (vid, w) in enumerate(vals.items()):
            tag = 0xDEADC0DE if vid == tagbreak else (TAG_BASE | i)
            full = (tag,) + tuple(w)
            out.append("P6 %08x %s %s"
                       % (i, vid, " ".join("%08x" % x for x in full)))
        fd, p = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with open(p, "wb") as fh:
            fh.write(("\r\n".join(out) + "\r\n").encode())
        return p

    OK_LOCK = (0, 0, 0, SRC_VAL, SRC_VAL, SRC_VAL, DST_INIT)
    OK_OPEN = (0, 0, 0, SENTINEL, SENTINEL, SRC_VAL, DST_INIT)

    def verdict_rc(vals, arm="device", table=None, tagbreak=None):
        tp = write(table or GOOD)
        cp = cap(vals, tagbreak)
        try:
            p = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "verdict", cp,
                 "--arm", arm],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
                env=dict(os.environ, TCPAY_TSV=tp))
            return p.returncode, p.stdout
        finally:
            os.unlink(tp)
            os.unlink(cp)

    def t17():
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": OK_LOCK, "v2": OK_OPEN})
        assert rc == 0, "a table that meets every prediction exited %d:\n%s" % (rc, out)
        assert "every row read the verdict its `pad` column predicts" in out, out
    case("T17 a run that meets every prediction exits 0 (the control on T18-T20)",
         t17)

    def t18():
        rc, out = verdict_rc({"c_lock": OK_OPEN, "c_open": OK_OPEN,
                              "v1": OK_LOCK, "v2": OK_OPEN})
        assert rc == 3, "a failed POSITIVE control exited %d, want 3\n%s" % (rc, out)
        assert "unattributable" in out, out
    case("T18 a failed positive control REFUSES rather than reports", t18)

    def t19():
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_LOCK,
                              "v1": OK_LOCK, "v2": OK_OPEN})
        assert rc == 3, "a failed NEGATIVE control exited %d, want 3\n%s" % (rc, out)
        assert "void, not partly valid" in out, out
    case("T19 a failed negative control voids the table, it does not weaken it",
         t19)

    def t20():
        # every row LOCK is correct under qemu and a refutation on the device.
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_LOCK,
                              "v1": OK_LOCK, "v2": OK_LOCK}, arm="qemu")
        assert rc == 0, "qemu all-LOCK exited %d\n%s" % (rc, out)
        rc2, out2 = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                                "v1": OK_LOCK, "v2": OK_OPEN}, arm="qemu")
        assert rc2 == 3, "qemu with OPEN rows exited %d, want 3\n%s" % (rc2, out2)
    case("T20 under qemu all-LOCK passes and any OPEN refuses (the anti-control)",
         t20)

    def t21():
        # A row that traps, and a row whose source never read back, must not be
        # silently scored as LOCK or OPEN.
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": (1, 0x28, 0x80500000, 0, 0, SRC_VAL, DST_INIT),
                              "v2": OK_OPEN})
        assert "TRAPS" in out, out
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": (0, 0, 0, SRC_VAL, SRC_VAL, 0x11111111, DST_INIT),
                              "v2": OK_OPEN})
        assert "VOID" in out, out
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": (0, 0, 0, SRC_VAL, SENTINEL, SRC_VAL, DST_INIT),
                              "v2": OK_OPEN})
        assert "SPLIT" in out, out
        # and the tag: a row whose tag is poison never started, and that is a
        # different observation from a row that ran and produced zeros.
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": OK_LOCK, "v2": OK_OPEN},
                             tagbreak="v1")
        assert "NOT-RUN" in out, out
        assert "never started" in out, out
    case("T21 TRAPS, VOID and SPLIT are their own verdicts, not LOCK or OPEN",
         t21)

    def t22():
        rc, out = verdict_rc({"c_lock": OK_LOCK, "c_open": OK_OPEN,
                              "v1": OK_LOCK, "v2": OK_LOCK})
        assert rc == 1, "a refuted prediction exited %d, want 1\n%s" % (rc, out)
        assert "refutes CPU-58" in out, out
    case("T22 a `nopad` row reading LOCK is reported as refuting CPU-58", t22)

    print("")
    if failed:
        print("RESULT: \033[31m%d passed, %d failed\033[0m"
              % (rows_ok, len(failed)))
        return 2
    print("RESULT: \033[32m%d passed, 0 failed\033[0m" % rows_ok)
    return 0


# ============================================================ main

def main(argv):
    if not argv:
        print(__doc__)
        return 3
    if argv[0] == "--self-test":
        print("tcpay %s self-test" % VERSION)
        print("")
        return self_test()

    mode = argv[0]
    rest = argv[1:]
    rows = read_table()

    if mode == "population":
        return cmd_population(rows)
    if mode == "emit":
        return cmd_emit(rows, "--check" in rest)
    if mode == "verify":
        if not rest:
            raise Refuse("verify needs an ELF")
        return cmd_verify(rows, rest[0])
    if mode == "gate":
        if not rest:
            raise Refuse("gate needs an ELF")
        hz = os.path.join(HERE, "hazlint")
        if "--hazlint" in rest:
            hz = rest[rest.index("--hazlint") + 1]
        return cmd_gate(rows, rest[0], hz)
    if mode == "verdict":
        if not rest:
            raise Refuse("verdict needs a capture")
        arm = "device"
        if "--arm" in rest:
            arm = rest[rest.index("--arm") + 1]
            if arm not in ("device", "qemu"):
                raise Refuse("--arm is device or qemu, not %r" % arm)
        return cmd_verdict(rows, rest[0], arm)
    raise Refuse("unknown mode %r" % mode)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Refuse as e:
        print("REFUSED: %s" % e)
        sys.exit(3)
