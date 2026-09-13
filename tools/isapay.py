#!/usr/bin/env python3
"""isapay.py -- `R1a`'s payload, generated from one table and checked three ways.

`probe4` asks, of each encoding in `tools/isa-payload.tsv`, the three-way
question `plan/router-rebuild-plan.md:1007` states:

    traps (with ExcCode)  /  does not trap and is RIGHT  /  does not trap and
    is WRONG

and `:753-757` calls the third cell 「最危險的那格」.  `PROGRESS.md:121`'s risk
column says why a generator exists rather than 45 hand-written cells:

    a payload that compares in-place reports a boolean and throws the value away

so the payload records the VALUE and this tool computes the verdict at the desk.

THREE SOURCES FOR EVERY ENCODING, and they are conceptually independent:

    1. the `word` column, written by hand;
    2. `encode`, which builds the word from the `fields` column;
    3. `verify`, which disassembles the BUILT ARTEFACT with binutils and
       requires the decode to name this row.

(1) and (2) catch arithmetic; only (3) catches a wrong belief about the
encoding layout, because it is the only one this repository did not write.

TWO SOURCES FOR EVERY EXPECTED CONSTANT:

    1. the `expect` column, written by hand;
    2. `model`, an implementation of the instruction's semantics written from
       the ISA definition and not from the encoding.

and, for the rows whose `qemu` column predicts `run`, a third: qemu executes
the same cell on a 24Kf and its answer is the MIPS specification's answer.
⚠️ That is NOT evidence about this device -- `plan:706` (D14-1) forbids
exactly that reading -- it is evidence about what the correct answer IS.  The
device's answer is the measurement; the oracle only says what it would have to
equal to be right.

Usage
    isapay.py population            the plan's groups, joined to the census
    isapay.py encode                source 1 against source 2, per row
    isapay.py model                 the expected constants, two sources
    isapay.py emit [--check]        generate cells4.S and probe4rows.h
    isapay.py verify ELF            source 3: disassemble what was built
    isapay.py verdict LOG --base A  three-way, from a `DW` read-back or qemu
    isapay.py --self-test           the controls

Exit
    0  clean
    1  a finding
    3  REFUSED -- something would not parse or a control failed, so nothing is
       reported.  An empty table and a table of absences are different answers.
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TSV = os.path.join(HERE, "isa-payload.tsv")
CENSUS = os.path.join(HERE, "isa-census.tsv")
CELLS_S = os.path.join(HERE, "rlxprobe", "cells4.S")
ROWS_H = os.path.join(HERE, "rlxprobe", "probe4rows.h")
ROWS_MK = os.path.join(HERE, "rlxprobe", "probe4rows.mk")

COLUMNS = ["group", "name", "shape", "fields", "word", "in_a", "in_b",
           "mem0", "mem1", "seed", "read", "expect", "qemu", "why"]

# The plan's nine groups (`plan/router-rebuild-plan.md:1011-1022`) plus the two
# rows that are not single instructions.  `population` requires every one of
# these to have at least one row, so deleting a group is loud rather than
# silent -- which is the failure this table exists because of.
PLAN_GROUPS = ["baseline", "reserved", "unaligned", "mips2", "mips32r1",
               "mips32r2", "mips16", "cop1", "ase", "nx"]

# Groups that carry rows the census derives but the plan does not name.  They
# are legal and they are NOT plan groups, so they are listed separately rather
# than quietly added to the list above.
EXTRA_GROUPS = ["census", "lexra-cp0", "cop3", "traps"]

# A plan group with no rows, DECLARED, with the reason and the experiment that
# would fill it.  The shape is `C8C_EXEMPT`'s: an exemption by name with a
# control, so a declared omission passes and an undeclared one fails.  A check
# that is red on every run is a check nobody reads.
DEFERRED_GROUPS = {
    "mips16": "needs a `-mips16`-assembled function and a return path in MIPS16 "
              "mode, which is a second execution context this payload does not "
              "have. `jalx` is excluded for the same reason and is the row that "
              "would enter it: if it retires, control lands in MIPS16 mode at an "
              "address decided by a 26-bit field, and the cost of being wrong is "
              "a power cycle.",
    "nx": "needs the I-side flush around a word written into a data region, and "
          "that is probe1's `R1d` sequence applied to a page this payload does "
          "not otherwise touch. One row, one new template, and it is the only "
          "row here that would WRITE instructions -- so it goes in a step whose "
          "card can say so, not into a sweep of 55.",
}

SHAPES = {"alu": "val", "load": "val", "store": "val",
          "hilo": "hilo", "machilo": "machilo",
          "branch": "branch", "jr": "jr", "nx": "nx"}

# The `machilo` template primes HI and LO to these before the probed word.
#
# It buys two things and the second was not the reason it was written.  ①  A
# multiply-ACCUMULATE has no single computable answer when the accumulator's
# contents at cell entry are whatever the previous row left, and priming turns
# `madd` from a trap-only row into one with all three verdicts.  ②  For the
# eight Lexra MAC encodings, whose semantics this project has NOT read -- the
# public patch gives encodings and operand formats, not behaviour -- priming
# makes *the accumulator did not move* a distinguishable outcome from *the
# accumulator moved*, which separates "retired as a no-op" from "did something
# MAC-shaped" without knowing what the something is.
#
# One owner: the template formats these in and the models import them.
MAC_HI_PRIME = 0x0BAD0000
MAC_LO_PRIME = 0xF00D0000

# Opcode classes, used only to check that a row's declared `shape` agrees with
# its own opcode.  A free cross-check: a row that says `alu` and encodes a
# store has one of the two columns wrong.
LOAD_OPS = {0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x30, 0x31, 0x32,
            0x33, 0x35, 0x37}
STORE_OPS = {0x28, 0x29, 0x2A, 0x2B, 0x2E, 0x38, 0x39, 0x3A, 0x3B, 0x3D, 0x3F}

# The scratch block the cells read and write.  One copy of this arithmetic in
# the asm, one in the C header, both emitted from here.
OFF = {"in_a": 0, "in_b": 4, "seed": 8, "mem0": 16, "mem1": 20,
       "out_gpr": 24, "out_m0": 28, "out_m1": 32, "out_aux": 36}
SCRATCH_BYTES = 48

# Words recorded per row in the result block.  8 is a power of two on purpose:
# a `DW` read-back's row arithmetic is then a shift, and a short reply is
# visible as a partial row rather than as a shifted table.
ROW_WORDS = 8
ROW_TAG_BASE = 0x52340000       # 'R4' << 16; row index in the low half


class Refuse(Exception):
    pass


def _hx(s, what):
    s = s.strip()
    if s == "-":
        return None
    try:
        return int(s, 0) & 0xFFFFFFFF
    except ValueError:
        raise Refuse("%s: not a number: %r" % (what, s))


def load_rows(path=TSV):
    """Parse the table.  Refuses rather than reporting a short table."""
    if not os.path.exists(path):
        raise Refuse("no table at %s" % path)
    txt = io.open(path, encoding="utf-8").read()
    lines = [l for l in txt.split("\n") if l.strip() and not l.startswith("#")]
    if not lines:
        raise Refuse("%s has no rows" % path)
    hdr = lines[0].split("\t")
    if hdr != COLUMNS:
        raise Refuse("header is %r, expected %r" % (hdr, COLUMNS))
    rows = []
    seen = set()
    for i, l in enumerate(lines[1:]):
        f = l.split("\t")
        if len(f) != len(COLUMNS):
            raise Refuse("row %d has %d fields, expected %d: %r"
                         % (i, len(f), len(COLUMNS), l[:60]))
        r = dict(zip(COLUMNS, f))
        if "|" in l:
            raise Refuse("row %s contains a pipe" % r["name"])
        if r["name"] in seen:
            raise Refuse("duplicate name %r -- one quantity, two atomic units"
                         % r["name"])
        seen.add(r["name"])
        if r["shape"] not in SHAPES:
            raise Refuse("row %s: unknown shape %r" % (r["name"], r["shape"]))
        if r["read"] not in ("gpr", "m0", "m1", "aux"):
            raise Refuse("row %s: unknown read %r" % (r["name"], r["read"]))
        # `run`, `trap`, or `trap:N` -- N being the ExcCode this row predicts.
        # `plan:738` is why the number is worth pre-registering: *any other
        # ExcCode is a finding to write down, not an error*, and a finding you
        # only recognise after the fact is one you argued yourself into.
        q = r["qemu"]
        r["qemu_exc"] = None
        if q.startswith("trap:"):
            r["qemu_kind"] = "trap"
            r["qemu_exc"] = _hx(q[5:], "row %s qemu ExcCode" % r["name"])
            if r["qemu_exc"] is None or r["qemu_exc"] > 31:
                raise Refuse("row %s: ExcCode %r is not 0..31" % (r["name"], q))
        elif q in ("run", "trap"):
            r["qemu_kind"] = q
        else:
            raise Refuse("row %s: qemu must be run, trap or trap:N, got %r"
                         % (r["name"], q))
        if r["group"] not in PLAN_GROUPS + EXTRA_GROUPS:
            raise Refuse("row %s: unknown group %r" % (r["name"], r["group"]))
        for k in ("in_a", "in_b", "mem0", "mem1", "seed"):
            r[k + "_v"] = _hx(r[k], "row %s %s" % (r["name"], k))
            if r[k + "_v"] is None:
                raise Refuse("row %s: %s may not be '-'" % (r["name"], k))
        r["word_v"] = _hx(r["word"], "row %s word" % r["name"])
        if r["word_v"] is None:
            raise Refuse("row %s: word may not be '-'" % r["name"])
        r["expect_v"] = _hx(r["expect"], "row %s expect" % r["name"])
        r["idx"] = i
        r["fields_d"] = parse_fields(r["fields"], r["name"])
        # THE RESERVED ROW'S TRAP FOR THE ANSWER CHECKER, and it is a
        # REQUIREMENT rather than an exemption.
        #
        # `plan:761` says the reserved encoding is fed to the trap check AND to
        # the answer check, and that an answer check which calls it RIGHT voids
        # the table.  The way an answer checker gets that wrong is by reading
        # the recorded value and not the exception count -- so the reserved row
        # sets `expect` EQUAL to `seed`, which is what the value will still be
        # after a trap.  A checker that consults the count says TRAPS; a checker
        # that does not says RIGHT, and `check_controls` voids on RIGHT.
        #
        # For every other row the same equality is a defect, because there
        # "wrote the right answer" and "wrote nothing" would be one reading.
        # One rule, opposite signs, and both are enforced here so neither can
        # be lost by editing the table.
        if r["group"] == "reserved":
            if r["expect_v"] != r["seed_v"]:
                raise Refuse(
                    "row %s is in group reserved, so its expect (0x%08X) must "
                    "EQUAL its seed (0x%08X): that equality is the trap laid "
                    "for the answer checker (plan:761)"
                    % (r["name"], r["expect_v"] or 0, r["seed_v"]))
        elif r["expect_v"] is not None:
            # The value the recorded word ALREADY HOLDS if the probed
            # instruction does nothing.  It is not always the seed: a row that
            # reads `m0` is untouched-equal to `mem0`, and comparing such a row
            # against the seed would be checking a rule against the wrong
            # quantity -- which is how a check comes out green on every row it
            # was never able to test.
            # WHAT THE RECORDED WORD HOLDS IF THE PROBED INSTRUCTION DID
            # NOTHING, and it is per-TEMPLATE rather than per-row: the branch
            # and jump templates pre-set $2 to NOTTAKEN, and `machilo` ends in
            # `mflo`/`mfhi`, so in neither case is the seed what survives.
            # Comparing against the seed there is a check aimed at a quantity
            # the cell overwrote -- green on every row it could never test.
            # `None` means this template cannot say, and the check is skipped
            # rather than made up: `hilo` leaves HI and LO holding whatever the
            # previous row left, which is exactly the thing `machilo` exists to
            # fix.
            t = SHAPES[r["shape"]]
            if t in ("branch", "jr"):
                un = {"gpr": NOTTAKEN, "aux": 0}
            elif t == "machilo":
                un = {"gpr": MAC_LO_PRIME, "aux": MAC_HI_PRIME}
            elif t == "hilo":
                un = {"gpr": None, "aux": None}
            else:
                un = {"gpr": r["seed_v"], "aux": 0}
            un["m0"] = r["mem0_v"]
            un["m1"] = r["mem1_v"]
            untouched = un[r["read"]]
            if untouched is not None and r["expect_v"] == untouched:
                raise Refuse(
                    "row %s reads %s, whose untouched value is 0x%08X, and "
                    "that is its expect: 'did the right thing' and 'did "
                    "nothing' would be one reading"
                    % (r["name"], r["read"], untouched))
        rows.append(r)
    return rows


def parse_fields(spec, name):
    d = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise Refuse("row %s: field %r has no '='" % (name, part))
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in ("op", "rs", "rt", "rd", "sh", "fn", "imm"):
            raise Refuse("row %s: unknown field %r" % (name, k))
        if k in d:
            raise Refuse("row %s: field %r given twice" % (name, k))
        d[k] = _hx(v, "row %s field %s" % (name, k))
    if "op" not in d:
        raise Refuse("row %s: fields has no op" % name)
    return d


def encode_fields(d, name):
    """Source 2.  Builds the word from the fields, with the widths checked.

    The width check is not decoration: a field that does not fit is an
    encoding this table cannot express, and silently truncating it would
    produce a word that assembles, runs, and answers a different question.
    """
    op = d["op"]
    if op > 0x3F:
        raise Refuse("row %s: op 0x%X does not fit 6 bits" % (name, op))
    has_imm = "imm" in d
    if has_imm and ("rd" in d or "sh" in d or "fn" in d):
        raise Refuse("row %s: imm given with an R-type field" % name)
    w = op << 26
    for k, shift, width in (("rs", 21, 5), ("rt", 16, 5)):
        v = d.get(k, 0)
        if v >= (1 << width):
            raise Refuse("row %s: %s %d does not fit %d bits"
                         % (name, k, v, width))
        w |= v << shift
    if has_imm:
        v = d["imm"]
        # The immediate is signed on every I-type this table uses; accept the
        # two's-complement spelling and the negative one, and refuse anything
        # that is neither.
        if v > 0xFFFF and not (0xFFFF0000 <= v <= 0xFFFFFFFF):
            raise Refuse("row %s: imm 0x%X does not fit 16 bits" % (name, v))
        w |= v & 0xFFFF
    else:
        for k, shift, width in (("rd", 11, 5), ("sh", 6, 5), ("fn", 0, 6)):
            v = d.get(k, 0)
            if v >= (1 << width):
                raise Refuse("row %s: %s %d does not fit %d bits"
                             % (name, k, v, width))
            w |= v << shift
    return w & 0xFFFFFFFF


# --------------------------------------------------------------------------
# The model.  Source 2 for the expected constant.
#
# Written from the instruction definitions, NOT from the encoding: each
# function takes named values, so a wrong `rs`/`rt` assignment in the table
# cannot propagate into the expectation.  A name with no entry here is a row
# whose answer this tool will not vouch for, and `model` says so per row rather
# than defaulting to the table's own number.
# --------------------------------------------------------------------------
def _u32(x):
    return x & 0xFFFFFFFF


def _s32(x):
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


def _bytes_be(w):
    return [(w >> 24) & 0xFF, (w >> 16) & 0xFF, (w >> 8) & 0xFF, w & 0xFF]


def _mem_byte(m0, m1, off):
    """The byte at `off` from the base of the two-word memory operand, big-endian."""
    if off < 4:
        return _bytes_be(m0)[off]
    if off < 8:
        return _bytes_be(m1)[off - 4]
    raise Refuse("memory offset %d is outside the two-word operand" % off)


def _mem_word(m0, m1, off):
    if off == 0:
        return m0
    if off == 4:
        return m1
    raise Refuse("unaligned word at offset %d" % off)


def m_add(a, b, **k):
    # MIPS-I ADD traps on signed overflow.  The table's operands are checked
    # against that below, so the model returns the sum and `model` refuses a
    # row that would overflow -- a trap from the positive control would be a
    # table defect wearing a measurement's clothes.
    s = _s32(a) + _s32(b)
    if s < -(1 << 31) or s > (1 << 31) - 1:
        raise Refuse("add operands overflow -- the positive control would trap")
    return _u32(s)


def m_addu(a, b, **k):
    return _u32(a + b)


def m_sub(a, b, **k):
    s = _s32(a) - _s32(b)
    if s < -(1 << 31) or s > (1 << 31) - 1:
        raise Refuse("sub operands overflow")
    return _u32(s)


def m_and(a, b, **k):
    return _u32(a & b)


def m_or(a, b, **k):
    return _u32(a | b)


def m_xor(a, b, **k):
    return _u32(a ^ b)


def m_sll(b, sh, **k):
    return _u32(b << sh)


def m_srl(b, sh, **k):
    return _u32(b >> sh)


def m_sra(b, sh, **k):
    return _u32(_s32(b) >> sh)


def m_slt(a, b, **k):
    return 1 if _s32(a) < _s32(b) else 0


def m_sltu(a, b, **k):
    return 1 if _u32(a) < _u32(b) else 0


def m_lw(m0, m1, imm, **k):
    return _mem_word(m0, m1, imm)


def m_sw(b, **k):
    return _u32(b)


def m_lb(m0, m1, imm, **k):
    v = _mem_byte(m0, m1, imm)
    return _u32(v - 256 if v & 0x80 else v)


def m_lbu(m0, m1, imm, **k):
    return _mem_byte(m0, m1, imm)


def m_lwl(m0, m1, imm, seed, **k):
    """Big-endian LWL.

    vAddr = base + imm; the aligned word W containing it is loaded into the
    MOST significant part of rt, shifted left by the byte position, and rt's
    remaining low bytes are preserved.  `MIPS-I` A-79.
    """
    byte = imm & 3
    w = _mem_word(m0, m1, imm & ~3)
    keep = (1 << (8 * byte)) - 1
    return _u32((w << (8 * byte)) | (seed & keep))


def m_lwr(m0, m1, imm, seed, **k):
    """Big-endian LWR.

    vAddr = base + imm; the aligned word W containing it is shifted RIGHT so
    that the byte at vAddr lands in rt's least significant position, and rt's
    remaining high bytes are preserved.  On big-endian LWR at byte 3 loads the
    whole word.
    """
    byte = imm & 3
    w = _mem_word(m0, m1, imm & ~3)
    shift = 8 * (3 - byte)
    nkeep = 8 * (3 - byte)
    keep = _u32(~((1 << (32 - nkeep)) - 1)) if nkeep else 0
    return _u32((w >> shift) | (seed & keep))


def m_swl(b, m0, m1, imm, **k):
    """Big-endian SWL -- the MOST significant bytes of rt go to vAddr onward."""
    byte = imm & 3
    w = _mem_word(m0, m1, imm & ~3)
    n = 4 - byte                       # bytes written
    mem = _bytes_be(w)
    src = _bytes_be(b)
    for i in range(n):
        mem[byte + i] = src[i]
    return _u32((mem[0] << 24) | (mem[1] << 16) | (mem[2] << 8) | mem[3])


def m_swr(b, m0, m1, imm, **k):
    """Big-endian SWR -- the LEAST significant bytes of rt go up to vAddr."""
    byte = imm & 3
    w = _mem_word(m0, m1, imm & ~3)
    n = byte + 1                       # bytes written
    mem = _bytes_be(w)
    src = _bytes_be(b)
    for i in range(n):
        mem[byte - i] = src[3 - i]
    return _u32((mem[0] << 24) | (mem[1] << 16) | (mem[2] << 8) | mem[3])


def m_mult_lo(a, b, **k):
    return _u32(_s32(a) * _s32(b))


def m_mult_hi(a, b, **k):
    return _u32((_s32(a) * _s32(b)) >> 32)


def m_multu_lo(a, b, **k):
    return _u32(_u32(a) * _u32(b))


def m_multu_hi(a, b, **k):
    return _u32((_u32(a) * _u32(b)) >> 32)


def m_clz(a, **k):
    v = _u32(a)
    n = 0
    while n < 32 and not (v & 0x80000000):
        n += 1
        v = _u32(v << 1)
    return n


def m_clo(a, **k):
    v = _u32(a)
    n = 0
    while n < 32 and (v & 0x80000000):
        n += 1
        v = _u32(v << 1)
    return n


def m_mul(a, b, **k):
    return _u32(_s32(a) * _s32(b))


def m_movz(a, b, seed, **k):
    return _u32(a) if _u32(b) == 0 else _u32(seed)


def m_movn(a, b, seed, **k):
    return _u32(a) if _u32(b) != 0 else _u32(seed)


def m_ext(a, sh, sz, **k):
    return _u32((a >> sh) & ((1 << sz) - 1))


def m_seb(b, **k):
    v = b & 0xFF
    return _u32(v - 256 if v & 0x80 else v)


def m_seh(b, **k):
    v = b & 0xFFFF
    return _u32(v - 65536 if v & 0x8000 else v)


def m_wsbh(b, **k):
    return _u32(((b & 0x00FF0000) << 8) | ((b & 0xFF000000) >> 8) |
                ((b & 0x000000FF) << 8) | ((b & 0x0000FF00) >> 8))


def m_rotr(b, sh, **k):
    sh &= 31
    if sh == 0:
        return _u32(b)
    return _u32((b >> sh) | (b << (32 - sh)))


def _madd_acc(a, b):
    """HI:LO += rs*rt, starting from the primed accumulator.

    Signed, because `madd` is.  The primers are imported from the template's
    own constants, so a change there cannot leave this arithmetic behind.
    """
    acc = (MAC_HI_PRIME << 32) | MAC_LO_PRIME
    return (acc + _s32(a) * _s32(b)) & ((1 << 64) - 1)


def m_madd(a, b, **k):
    return _u32(_madd_acc(a, b))


def m_madd_hi(a, b, **k):
    return _u32(_madd_acc(a, b) >> 32)


def m_ins(a, seed, sh, rd, **k):
    """INS rt, rs, pos, size -- `rd` holds pos+size-1, `sh` holds pos."""
    pos, size = sh, rd - sh + 1
    if size < 1 or pos + size > 32:
        raise Refuse("ins: pos %d size %d is outside the word" % (pos, size))
    mask = ((1 << size) - 1) << pos
    return _u32((seed & ~mask) | ((a & ((1 << size) - 1)) << pos))


def m_ext2(a, sh, rd, **k):
    """EXT rt, rs, pos, size -- `rd` holds size-1, `sh` holds pos."""
    pos, size = sh, rd + 1
    if pos + size > 32:
        raise Refuse("ext: pos %d size %d is outside the word" % (pos, size))
    return _u32((a >> pos) & ((1 << size) - 1))


# The branch and jump templates encode TAKEN and NOT-TAKEN as two constants, so
# every one of these is the condition itself rather than a stand-in for it.
TAKEN, NOTTAKEN = 0x0600, 0x0BAD


def m_beq(a, b, **k):
    return TAKEN if _u32(a) == _u32(b) else NOTTAKEN


def m_bne(a, b, **k):
    return TAKEN if _u32(a) != _u32(b) else NOTTAKEN


def m_blez(a, **k):
    return TAKEN if _s32(a) <= 0 else NOTTAKEN


def m_bgtz(a, **k):
    return TAKEN if _s32(a) > 0 else NOTTAKEN


def m_jr(**k):
    return TAKEN


# name -> (model function, which recorded word it produces)
MODELS = {
    "add": (m_add, "gpr"), "addu": (m_addu, "gpr"), "sub": (m_sub, "gpr"),
    "and": (m_and, "gpr"), "or": (m_or, "gpr"), "xor": (m_xor, "gpr"),
    "sll": (m_sll, "gpr"), "srl": (m_srl, "gpr"), "sra": (m_sra, "gpr"),
    "slt": (m_slt, "gpr"), "sltu": (m_sltu, "gpr"),
    "lw": (m_lw, "gpr"), "lb": (m_lb, "gpr"), "lbu": (m_lbu, "gpr"),
    "sw": (m_sw, "m0"),
    "lwl": (m_lwl, "gpr"), "lwr": (m_lwr, "gpr"),
    "swl": (m_swl, "m0"), "swr": (m_swr, "m0"),
    "mult": (m_mult_lo, "gpr"), "multu": (m_multu_lo, "gpr"),
    "mult_hi": (m_mult_hi, "aux"),
    "madd": (m_madd, "gpr"), "madd_hi": (m_madd_hi, "aux"),
    "clz": (m_clz, "gpr"), "clo": (m_clo, "gpr"), "mul": (m_mul, "gpr"),
    "movz": (m_movz, "gpr"), "movn": (m_movn, "gpr"),
    "seb": (m_seb, "gpr"), "seh": (m_seh, "gpr"), "wsbh": (m_wsbh, "gpr"),
    "rotr": (m_rotr, "gpr"),
    "ext": (m_ext2, "gpr"), "ins": (m_ins, "gpr"),
    "beq": (m_beq, "gpr"), "bne": (m_bne, "gpr"),
    "beql": (m_beq, "gpr"), "bnel": (m_bne, "gpr"),
    "blezl": (m_blez, "gpr"), "bgtzl": (m_bgtz, "gpr"),
    "jr": (m_jr, "gpr"),
    # `ll` is `lw` on any implementation that has it -- the link bit it also
    # sets is invisible to this cell.  `sc` deliberately has NO model: without
    # a preceding `ll` to the same address its outcome is architecturally
    # unspecified, so there is no single computable constant and the table says
    # `-` rather than inventing one.  `docs/isa-payload.md` § 6 carries the
    # two-word cell that would close it.
    "ll": (m_lw, "gpr"),
}


def model_row(r):
    """Return (value, note).  `value` is None when this tool will not vouch."""
    base = r["name"]
    if base not in MODELS:
        return None, "no model -- this row's expectation has ONE source"
    fn, produces = MODELS[base]
    if produces != r["read"]:
        raise Refuse("row %s: model produces %s, table reads %s"
                     % (r["name"], produces, r["read"]))
    d = r["fields_d"]
    imm = d.get("imm", 0)
    if imm > 0x7FFF:
        imm = imm - 0x10000
    # `rd` and `sh` are passed RAW.  `ext` and `ins` both put a size in `rd`
    # and both mean something different by it (size-1 against pos+size-1), so
    # the tool deriving one `sz` for them would be the encoding layout leaking
    # into the semantics -- which is the separation this model exists for.
    kw = dict(a=r["in_a_v"], b=r["in_b_v"], m0=r["mem0_v"], m1=r["mem1_v"],
              seed=r["seed_v"], sh=d.get("sh", 0), rd=d.get("rd", 0), imm=imm)
    try:
        return fn(**kw), "model"
    except TypeError as e:
        raise Refuse("row %s: model signature mismatch: %s" % (r["name"], e))


# --------------------------------------------------------------------------
# Cell templates.  The register allocation is FIXED for every row, which is
# the whole reason a generator beats 45 hand-written cells: the encoding's
# rs/rt/rd fields and the setup code that fills those registers come out of
# one place and cannot drift apart.
#
#   $8   input A        $9   input B       $10  memory operand base
#   $2   result         $11  aux result    $24  the scratch pointer
#
# $24 is never an operand of a probed instruction, so a probed instruction
# cannot destroy the pointer the cell needs to record its own answer.
# --------------------------------------------------------------------------
PROLOGUE = """\
	.globl	rlx_p4_{name}
	.ent	rlx_p4_{name}
	.type	rlx_p4_{name}, @function
rlx_p4_{name}:
	addu	$24, $4, $0		/* scratch, before SAFE_A0 takes $4 */
	SAFE_A0
	lw	$8, {in_a}($24)
	lw	$9, {in_b}($24)
	lw	$2, {seed}($24)
	addiu	$10, $24, {mem0}
	nop				/* LOAD DELAY SLOT for $2 */
"""

EPILOGUE = """\
	sw	$2, {out_gpr}($24)
	lw	$8, {mem0}($24)
	nop				/* LOAD DELAY SLOT */
	sw	$8, {out_m0}($24)
	lw	$9, {mem1}($24)
	nop				/* LOAD DELAY SLOT */
	sw	$9, {out_m1}($24)
	jr	$31
	nop
	.end	rlx_p4_{name}

"""

T_VAL = """\
	.globl	rlx_p4_{name}_w
rlx_p4_{name}_w:
	.word	0x{word:08X}		/* {name}: {why} */
	nop
	nop
	sw	$0, {out_aux}($24)
"""

T_HILO = """\
	.globl	rlx_p4_{name}_w
rlx_p4_{name}_w:
	.word	0x{word:08X}		/* {name}: {why} */
	nop
	nop				/* MIPS-I: two instructions before mflo */
	mflo	$2
	nop
	nop
	mfhi	$11
	nop
	nop
	sw	$11, {out_aux}($24)
"""

# Same as T_HILO with the accumulator primed to a known value first.  $11 is
# the aux register and is not an operand of any probed instruction, so forming
# the primers in it costs the table nothing.
T_MACHILO = """\
	lui	$11, 0x{hi_prime:04X}
	mthi	$11
	nop
	nop				/* MIPS-I: two instructions after mthi */
	lui	$11, 0x{lo_prime:04X}
	mtlo	$11
	nop
	nop
	.globl	rlx_p4_{name}_w
rlx_p4_{name}_w:
	.word	0x{word:08X}		/* {name}: {why} */
	nop
	nop
	mflo	$2
	nop
	nop
	mfhi	$11
	nop
	nop
	sw	$11, {out_aux}($24)
"""

# The branch template.  The probed branch is at +0; its delay slot at +4; the
# NOT-TAKEN path at +8; an unconditional hop over the taken path at +12 with
# its own delay slot at +16; the TAKEN path at +20.  So the probed branch's
# offset field is (0x14 - 0x4) >> 2 = 4, and `encode` checks the table agrees.
BRANCH_IMM = 4
T_BRANCH = """\
	.globl	rlx_p4_{name}_w
rlx_p4_{name}_w:
	.word	0x{word:08X}		/* {name}: {why} */
	nop				/* the branch delay slot, filled by hand */
	addiu	$2, $0, 0x0BAD		/* NOT TAKEN lands here */
	beq	$0, $0, 8f
	nop
	addiu	$2, $0, 0x0600		/* TAKEN lands here */
8:
	sw	$0, {out_aux}($24)
"""

# `jr` needs a register holding a label.  $11 is the aux register and is not an
# operand of any probed instruction, so forming the address in it costs nothing
# the table has to know about.
#
# 🔴 THE FIRST DRAFT OF THIS TEMPLATE PUT BOTH PATHS ON THE SAME VALUE.  It set
# `0x0BAD` on the fall-through and then FELL INTO the taken label, which sets
# `0x0600` -- so a `jr` that did nothing and a `jr` that jumped were one
# reading, and every row using it would have read RIGHT whatever happened.  The
# fall-through now branches over the taken marker.  The same mistake is not
# possible in T_BRANCH, whose hop was there from the start; it is recorded here
# because a template that cannot express failure is the payload version of an
# answer checker that always says yes.
T_JR = """\
	lui	$11, %hi(.Lp4_{name}_tgt)
	addiu	$11, $11, %lo(.Lp4_{name}_tgt)
	addiu	$2, $0, 0x0BAD		/* if the jump does nothing, this stands */
	nop
	.globl	rlx_p4_{name}_w
rlx_p4_{name}_w:
	.word	0x{word:08X}		/* {name}: {why} */
	nop				/* the jump delay slot, filled by hand */
	beq	$0, $0, .Lp4_{name}_end	/* FELL THROUGH -- $2 stays 0x0BAD */
	nop
.Lp4_{name}_tgt:
	addiu	$2, $0, 0x0600		/* TAKEN */
.Lp4_{name}_end:
	sw	$0, {out_aux}($24)
"""

TEMPLATES = {"val": T_VAL, "hilo": T_HILO, "machilo": T_MACHILO,
             "branch": T_BRANCH, "jr": T_JR}

HEADER_S = """\
/* cells4.S -- GENERATED by tools/isapay.py from tools/isa-payload.tsv.
 *
 * DO NOT EDIT.  `isapay.py emit --check` fails if this file and the table have
 * drifted, and that check is a case in `tools/test-hazpay.py`.
 *
 * 🔴 2026-09-13: that sentence named `tools/test-isapay.py` from the day it
 * was written and THAT FILE HAS NEVER EXISTED, so the check it promises was
 * run by nothing -- CI runs only `--self-test`, and no make target generated
 * this file either.  A stale or hand-edited `cells4.S` therefore built and
 * shipped.  `tools/rlxprobe/Makefile` now runs `emit --check` as a build
 * prerequisite as well, so the claim has two enforcers rather than one
 * comment.
 *
 * Assembled under `.set noreorder`, `.set noat` and `.set nomacro`, so every
 * instruction here is one the generator wrote.  `tools/hazlint` gates the
 * build; every load delay slot below is filled explicitly and the gate is what
 * says so.
 *
 * Register allocation, identical in every cell:
 *
 *     $8   input A       $9   input B      $10  memory operand base
 *     $2   result        $11  aux          $24  the scratch pointer
 *
 * $24 is never an operand of a probed instruction.  A probed instruction that
 * misbehaves therefore cannot destroy the pointer the cell needs in order to
 * record that it misbehaved.
 *
 * ⚠️ EVERY PROBED ENCODING IS A `.word`, NEVER A MNEMONIC.  An assembler's
 * dictionary is not this core's instruction set -- `docs/toolchain-comparison.md`
 * measures three toolchains disagreeing about which mnemonics exist -- and a
 * row that assembles is not a row that was encoded as intended.
 * `isapay.py verify` disassembles the built artefact and is the check.
 */
	.set	noreorder
	.set	noat
	.set	nomacro
#include "rlxasm.h"

	.text

"""

HEADER_H = """\
/* probe4rows.h -- GENERATED by tools/isapay.py from tools/isa-payload.tsv.
 * DO NOT EDIT.  See cells4.S.
 */
#ifndef PROBE4ROWS_H
#define PROBE4ROWS_H

#define P4_ROWS		{nrows}u
#define P4_ROW_WORDS	{row_words}u
#define P4_TAG_BASE	0x{tag_base:08X}u
#define P4_SCRATCH_B	{scratch}u

struct p4_row {{
	void (*cell)(void *);
	unsigned int in_a;
	unsigned int in_b;
	unsigned int mem0;
	unsigned int mem1;
	unsigned int seed;
}};

{protos}
static const struct p4_row p4_rows[P4_ROWS] = {{
{inits}}};

/* Row names, for the banner.  One string per row, same order. */
static const char *const p4_names[P4_ROWS] = {{
{names}}};

#endif /* PROBE4ROWS_H */
"""


def gen_asm(rows):
    out = [HEADER_S]
    for r in rows:
        body = TEMPLATES[SHAPES[r["shape"]]]
        o = dict(OFF)
        o.update(name=r["name"], word=r["word_v"], why=r["why"],
                 hi_prime=MAC_HI_PRIME >> 16, lo_prime=MAC_LO_PRIME >> 16)
        out.append(PROLOGUE.format(**o))
        out.append(body.format(**o))
        out.append(EPILOGUE.format(**o))
    return "".join(out)


def gen_header(rows):
    protos = "".join("void rlx_p4_%s(void *);\n" % r["name"] for r in rows)
    inits = "".join(
        "\t{ rlx_p4_%s, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu },\n"
        % (r["name"], r["in_a_v"], r["in_b_v"], r["mem0_v"], r["mem1_v"],
           r["seed_v"]) for r in rows)
    names = "".join('\t"%s",\n' % r["name"] for r in rows)
    return HEADER_H.format(nrows=len(rows), row_words=ROW_WORDS,
                           tag_base=ROW_TAG_BASE, scratch=SCRATCH_BYTES,
                           protos=protos, inits=inits, names=names)


def write_if_changed(path, text, check_only):
    old = io.open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == text:
        return False
    if check_only:
        return True
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)
    return True


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------
def cmd_encode(rows, quiet=False):
    bad = 0
    for r in rows:
        want = encode_fields(r["fields_d"], r["name"])
        got = r["word_v"]
        ok = want == got
        if SHAPES[r["shape"]] == "branch" and r["fields_d"].get("imm") != BRANCH_IMM:
            if not quiet:
                print("  %-12s BRANCH imm is %s, the template needs %d"
                      % (r["name"], r["fields_d"].get("imm"), BRANCH_IMM))
            bad += 1
        op = r["fields_d"]["op"]
        declared = r["shape"]
        cls = ("load" if op in LOAD_OPS else
               "store" if op in STORE_OPS else None)
        if cls and declared not in (cls, "hilo", "branch", "jr", "nx"):
            if not quiet:
                print("  %-12s op 0x%02X is a %s and the row declares %s"
                      % (r["name"], op, cls, declared))
            bad += 1
        if not ok:
            bad += 1
        if not quiet:
            print("  %-12s %-34s hand 0x%08X  fields 0x%08X  %s"
                  % (r["name"], r["fields"], got, want, "ok" if ok else "DIFFER"))
    if not quiet:
        print("encode: %d row(s), %d finding(s)" % (len(rows), bad))
    return 1 if bad else 0


def cmd_model(rows, quiet=False):
    bad = 0
    nomodel = []
    for r in rows:
        if r["expect_v"] is None:
            if not quiet:
                print("  %-12s expect '-'  -- a row with no answer, trap-only"
                      % r["name"])
            continue
        if r["group"] == "reserved":
            if not quiet:
                print("  %-12s hand 0x%08X  == seed BY DESIGN -- the trap laid "
                      "for the answer checker (plan:761)"
                      % (r["name"], r["expect_v"]))
            continue
        v, note = model_row(r)
        if v is None:
            nomodel.append(r["name"])
            if not quiet:
                print("  %-12s hand 0x%08X  %s" % (r["name"], r["expect_v"], note))
            continue
        ok = _u32(v) == r["expect_v"]
        if not ok:
            bad += 1
        if not quiet:
            print("  %-12s hand 0x%08X  model 0x%08X  %s"
                  % (r["name"], r["expect_v"], _u32(v), "ok" if ok else "DIFFER"))
    if not quiet:
        print("model: %d row(s), %d finding(s)" % (len(rows), bad))
        # Naming them is the point.  A row with no model has ONE source for its
        # expected constant, and a count alone lets that fact sit in a number
        # nobody reads.  `docs/isa-payload.md` carries the reason for each.
        if nomodel:
            print("  ONE SOURCE ONLY (%d): %s" % (len(nomodel), " ".join(nomodel)))
    return 1 if bad else 0


def census_names():
    if not os.path.exists(CENSUS):
        raise Refuse("no census at %s" % CENSUS)
    out = {}
    lines = [l for l in io.open(CENSUS, encoding="utf-8").read().split("\n")
             if l.strip() and not l.startswith("#")]
    hdr = lines[0].split("\t")
    for l in lines[1:]:
        f = l.split("\t")
        if len(f) < len(hdr):
            continue
        d = dict(zip(hdr, f))
        if d.get("kind") == "r1a":
            out[d["name"]] = d
    return out


def cmd_population(rows, quiet=False):
    """The join the sixty-third segment's opening scan says has to exist.

    The payload's population and the prior-art census are DIFFERENT sets with
    different jobs, and the failure this reports is not that they differ -- it
    is a difference nobody wrote down.
    """
    bad = 0
    have = {}
    for r in rows:
        have.setdefault(r["group"], []).append(r["name"])
    print("  plan groups (plan/router-rebuild-plan.md:1011-1022):")
    for g in PLAN_GROUPS:
        n = len(have.get(g, []))
        if n:
            flag = ""
        elif g in DEFERRED_GROUPS:
            flag = "   DEFERRED, declared"
        else:
            flag = "   <- EMPTY, and the plan names this group"
            bad += 1
        print("    %-10s %2d%s" % (g, n, flag))
    # The control on the exemption, in the other direction: a deferred group
    # that has grown rows is an exemption nobody removed.
    for g, why in sorted(DEFERRED_GROUPS.items()):
        if have.get(g):
            print("    %-10s has %d row(s) and is still on the DEFERRED list"
                  % (g, len(have[g])))
            bad += 1
    if not quiet:
        for g, why in sorted(DEFERRED_GROUPS.items()):
            if not have.get(g):
                print("      %s deferred: %s" % (g, why))
    extra = sorted(set(have) - set(PLAN_GROUPS))
    for g in extra:
        print("    %-10s %2d   (not a plan group)" % (g, len(have[g])))
    cen = census_names()
    mine = set(r["name"] for r in rows)
    only_payload = sorted(mine - set(cen))
    only_census = sorted(set(cen) - mine)
    print()
    print("  in the payload, not in the census: %d" % len(only_payload))
    if not quiet and only_payload:
        print("    " + " ".join(only_payload))
    print("  in the census, not in the payload: %d" % len(only_census))
    if not quiet and only_census:
        print("    " + " ".join(only_census))
    print("  in both: %d" % len(mine & set(cen)))
    print("population: %d payload row(s), %d census r1a row(s), %d finding(s)"
          % (len(rows), len(cen), bad))
    return 1 if bad else 0


HEADER_MK = """\
# probe4rows.mk -- GENERATED by tools/isapay.py from tools/isa-payload.tsv.
# DO NOT EDIT.  Included by tools/rlxprobe/Makefile.
#
# The result block's length is a FUNCTION of the row count, so it is emitted
# here rather than typed into the Makefile beside a second copy of the
# arithmetic.  probe0..probe3 each carry that second copy and
# `tools/test-rlxprobe.sh` exists partly to keep them honest; probe4 removes
# the class instead.  probe4.c re-derives the same number at compile time and
# refuses to build if it disagrees, so the two consumers still check each other.
P4_ROWS      := {nrows}
RB_WORDS_probe4 := {rb_words}
"""


def rb_words(nrows):
    """33 + 8R: 32 header words, 8 per row, one seal.

    1 mod 4 for every R, which is what makes `DW base RB_WORDS` return a word
    past the seal STRUCTURALLY rather than by a remainder that happened to
    fall out -- and that word is where a payload writing past its own block
    writes first.
    """
    return 33 + 8 * nrows


def cmd_emit(rows, check_only):
    a = gen_asm(rows)
    h = gen_header(rows)
    m = HEADER_MK.format(nrows=len(rows), rb_words=rb_words(len(rows)))
    ca = write_if_changed(CELLS_S, a, check_only)
    ch = write_if_changed(ROWS_H, h, check_only)
    cm = write_if_changed(ROWS_MK, m, check_only)
    if check_only:
        stale = [n for n, c in (("cells4.S", ca), ("probe4rows.h", ch),
                                ("probe4rows.mk", cm)) if c]
        if stale:
            print("emit --check: STALE -- %s differ(s) from the table"
                  % ", ".join(stale))
            return 1
        print("emit --check: all three generated files match the table")
        return 0
    for n, c in (("cells4.S", ca), ("probe4rows.h", ch), ("probe4rows.mk", cm)):
        print("emit: %-14s %s" % (n, "written" if c else "unchanged"))
    print("      %d row(s), %d bytes of asm, RB_WORDS %d"
          % (len(rows), len(a), rb_words(len(rows))))
    return 0


DIS_RE = re.compile(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)$")

# Groups whose rows MUST be named by a MIPS-I disassembler, because they claim
# to BE MIPS-I.  A `.word` there is a finding.
#
# Everywhere else a refusal is DATA rather than a defect: `objdump -m mips:3000`
# declining to name an encoding is one more reading of where the MIPS-I boundary
# is, and turning it into a failure would be forcing the instrument to agree
# with the table.  What is still a finding in every group is the decoder
# actively naming something ELSE -- that is a row whose name and encoding
# disagree, and it is the one defect neither `encode` nor `model` can see.
MNEMONIC_REQUIRED = {"baseline", "unaligned"}

# The reserved row is the one place a NAME would be the finding.
NO_MNEMONIC_GROUPS = {"reserved", "ase", "lexra-cp0"}

# A row whose name is not the mnemonic, with the reason.  Kept small and
# commented one by one rather than given a table column: an alias is a claim
# that two names are the same instruction, and that claim wants a sentence.
# name -> (what a MIPS-I disassembler calls it, why the two differ).
#
# 🔴 THE FIRST VERSION OF THIS DERIVED THE MNEMONIC BY STRIPPING TRAILING
# DIGITS, so that `cache10` would reduce to `cache` -- and it also reduced
# `mfc1` to `mfc`, `lwc3` to `lwc` and `mtc3` to `mtc`.  Nine rows reported
# `binutils decodes it as 'mfc1' and the row is named 'mfc1'`, which is what a
# check looks like when its own normaliser is wrong: the two strings it printed
# were identical.  There is no rule that separates a digit that is an operand
# from a digit that is part of the name, so each one is written down instead.
MNEMONIC_ALIAS = {
    "cache10": ("cache", "the digits are the cache OP field, not the name"),
    "cache11": ("cache", "the digits are the cache OP field, not the name"),
    "cache15": ("cache", "the digits are the cache OP field, not the name"),
    "cache19": ("cache", "the digits are the cache OP field, not the name"),
    # 🟢 THE DUAL-MEANING ROWS.  Each of these opcodes names one instruction in
    # MIPS-I and a different one in a later level, and this die is a MIPS-I
    # core being asked about later levels -- so the row is named for the
    # question and the decoder answers about the machine.  量 2026-09-13, from
    # `objdump -m mips:3000` on this payload's own artefact.
    "pref": ("lwc3", "opcode 0x33 is lwc3 in MIPS-I, reassigned to pref at MIPS32"),
    "ll":   ("lwc0", "opcode 0x30 is lwc0 in MIPS-I, reassigned to ll at MIPS-II"),
    "sc":   ("swc0", "opcode 0x38 is swc0 in MIPS-I, reassigned to sc at MIPS-II"),
}


def expected_mnemonic(name):
    """The mnemonic the row's NAME claims, as a MIPS-I decoder would spell it.

    A row named for one instruction that encodes another is the one defect
    neither `encode` nor `model` can see: both of them read the table's own
    fields, and the table's own fields are what would be wrong.
    """
    if name in MNEMONIC_ALIAS:
        return MNEMONIC_ALIAS[name][0]
    return name.split("_")[0]


def decode_ok(r, dis):
    """Source 3's actual question.  Returns (ok, why)."""
    tok = dis.split()[0] if dis.split() else ""
    unnamed = tok in (".word", ".short", ".byte")
    if r["group"] in NO_MNEMONIC_GROUPS:
        if unnamed:
            return True, "declined, as this group predicts"
        return False, ("binutils names it %r, and group %s predicts an encoding "
                       "no MIPS assembler assigns" % (tok, r["group"]))
    if unnamed:
        if r["group"] in MNEMONIC_REQUIRED:
            return False, ("binutils declines to name it, and the row claims "
                           "MIPS-I %r" % r["name"])
        return True, "declined at mips:3000 -- a reading, not a defect"
    want = expected_mnemonic(r["name"])
    if tok != want:
        return False, ("binutils decodes it as %r and the row is named %r"
                       % (tok, r["name"]))
    if r["name"] in MNEMONIC_ALIAS and MNEMONIC_ALIAS[r["name"]][0] != r["name"]:
        # Printed on every run rather than absorbed into the alias table: an
        # encoding with two names is a finding about the instruction set, and a
        # finding that only shows up the once is one the next reader will meet
        # again from scratch.
        return True, "DUAL: %s" % MNEMONIC_ALIAS[r["name"]][1]
    return True, tok


def cmd_verify(rows, elf, objdump=None, quiet=False, strict=False):
    """Source 3.  The only one this repository did not write.

    Disassembles the linked artefact and requires, for every row, that the word
    at `rlx_p4_<name>_w` is the table's word and that binutils' own decode of
    it names something consistent with the row.  A row whose decode binutils
    refuses to name at all is reported rather than passed: `.word` is a
    directive, so an encoding this core cannot execute still assembles.
    """
    objdump = objdump or os.environ.get("OBJDUMP", "mips-linux-gnu-objdump")
    if not os.path.exists(elf):
        raise Refuse("no artefact at %s" % elf)
    try:
        p = subprocess.run([objdump, "-d", "-m", "mips:3000", elf],
                           capture_output=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise Refuse("%s not on PATH -- source 3 cannot run, and an absent "
                     "check is not a passing check" % objdump)
    if p.returncode != 0:
        raise Refuse("%s exited %d" % (objdump, p.returncode))
    at = {}
    probe_addrs = set()
    cur = None
    for line in p.stdout.split("\n"):
        m = re.match(r"^([0-9a-f]+) <(.+)>:$", line.strip())
        if m:
            cur = m.group(2)
            if cur.endswith("_w"):
                probe_addrs.add(int(m.group(1), 16))
            continue
        m = DIS_RE.match(line)
        if m and cur and cur.endswith("_w"):
            at.setdefault(cur, []).append((m.group(2), m.group(3).strip()))
    bad = 0
    for r in rows:
        sym = "rlx_p4_%s_w" % r["name"]
        got = at.get(sym)
        if not got:
            print("  %-12s NOT FOUND in the artefact as %s" % (r["name"], sym))
            bad += 1
            continue
        hexw, dis = got[0]
        w = int(hexw, 16)
        if w != r["word_v"]:
            print("  %-12s artefact has 0x%08X, the table says 0x%08X"
                  % (r["name"], w, r["word_v"]))
            bad += 1
            continue
        dok, why = decode_ok(r, dis)
        if not dok:
            print("  %-12s 0x%08X  %-22s FINDING: %s" % (r["name"], w, dis, why))
            bad += 1
            continue
        if not quiet:
            print("  %-12s 0x%08X  %-22s %s" % (r["name"], w, dis, why))
    if strict:
        bad += _verify_converse(elf, probe_addrs, quiet)
    if not quiet:
        print("verify%s: %d row(s) against %s, %d finding(s)"
              % (" --strict" if strict else "", len(rows),
                 os.path.basename(elf), bad))
    return 1 if bad else 0


ISA_HIT_RE = re.compile(r"^\s*0x([0-9a-fA-F]{8})\s+([0-9a-fA-F]{8})\s")


def converse_stray(isa_text, probe_addrs):
    """The pure half of the converse check, so its control can run anywhere.

    Returns (hits seen, list of strays).  Split out of `_verify_converse`
    because that one needs a cross-compiled ELF and `tools/hazlint`, and a
    control that only runs where a cross-compiler is installed is a control CI
    never executes -- which this repository has already measured happening to
    two whole suites.
    """
    stray = []
    seen = 0
    for line in isa_text.split("\n"):
        m = ISA_HIT_RE.match(line)
        if not m:
            continue
        seen += 1
        a = int(m.group(1), 16)
        if a not in probe_addrs:
            stray.append((a, m.group(2), line.strip()))
    return seen, stray


def _verify_converse(elf, probe_addrs, quiet):
    """THE OTHER DIRECTION, and it is the one that matters.

    The rest of `verify` checks that every word the table declares is in the
    artefact.  It cannot see the opposite defect -- a non-MIPS-I instruction in
    the FRAMEWORK code, which nothing declared and which would execute on every
    row.  `tools/test-rlxprobe.sh` guards that for probe0..probe3 with a
    hardcoded list per payload; probe4's list is the table, and 量 2026-09-13
    that suite passes probe4 without looking at it.

    The check is NOT a comparison of word values.  It is an address test:
    **every non-MIPS-I word `hazlint --isa` can see must sit at a declared
    probe symbol.**  Formulated that way it does not depend on `hazlint`
    knowing every encoding this table probes -- opcode 0x3C and opcode 0x1E are
    not in its tables at all -- and it still refuses exactly the leak it is for.

    ⚠️ Its limit, stated rather than left to be found: `hazlint`'s own ISA
    table bounds what it can see, so this says *no non-MIPS-I word THAT HAZLINT
    RECOGNISES is outside a probe site*, which is weaker than *no such word
    exists*.
    """
    hz = os.path.join(HERE, "hazlint")
    if not os.path.exists(hz):
        raise Refuse("no tools/hazlint -- the converse check cannot run, and "
                     "an absent check is not a passing check")
    env = dict(os.environ)
    env["HAZLINT_CHILD"] = "1"      # K17: suppress the tool's own control block
    p = subprocess.run([sys.executable, hz, "--isa", elf], env=env,
                       capture_output=True, encoding="utf-8", errors="replace")
    if p.returncode not in (0, 1):
        raise Refuse("hazlint --isa exited %d" % p.returncode)
    seen, stray = converse_stray(p.stdout, probe_addrs)
    if not quiet:
        print("  converse: %d non-MIPS-I word(s) hazlint can see, %d declared "
              "probe site(s)" % (seen, len(probe_addrs)))
    for a, w, line in stray:
        print("  STRAY 0x%08X %s -- outside every declared probe symbol" % (a, w))
    return len(stray)


# --------------------------------------------------------------------------
# The desk-side verdict.  THE PAYLOAD NEVER DOES THIS.
# --------------------------------------------------------------------------
V_TRAP, V_RIGHT, V_WRONG, V_NORUN = "TRAPS", "RIGHT", "WRONG", "NOT-RUN"
# A fourth verdict, and it is not a weaker RIGHT.  `plan:716-719` (D14-5):
# *「沒有 trap」不構成「支援」的證據*.  A row with no computable answer can
# only ever report that it did not trap, so it gets its own word rather than
# being folded into either of the two that mean something.
V_RAN = "RAN"


def verdict_row(r, rec):
    """rec = (tag, n, cause, epc, gpr, m0, m1, aux).  Returns (verdict, value)."""
    tag, n, cause, epc, gpr, m0, m1, aux = rec
    want_tag = ROW_TAG_BASE | r["idx"]
    if tag != want_tag:
        return V_NORUN, None
    val = {"gpr": gpr, "m0": m0, "m1": m1, "aux": aux}[r["read"]]
    if n:
        return V_TRAP, val
    if r["expect_v"] is None:
        return V_RAN, val
    return (V_RIGHT if val == r["expect_v"] else V_WRONG), val


ROW_RE = re.compile(r"^P4\s+([0-9a-fA-F]{8})\s+(\S+)((?:\s+[0-9a-fA-F]{8}){8})\s*$")

# Pre-registered qemu predictions that the qemu run REFUTED, 量 2026-09-13,
# each with what it actually did and why.
#
# 🔴 THE PREDICTIONS THEMSELVES ARE NOT EDITED.  Changing a prediction to match
# the run is repairing the instrument to agree with the experiment, which this
# project refused once already when `IRQ-13`'s 1 % tolerance could have been
# widened instead of the window moved.  What changes is the bookkeeping: a
# refutation that has been chased to a cause is recorded, and a NEW one is
# still a finding -- so the check keeps its teeth without being red forever.
QEMU_REFUTED = {
    "rdhwr": ("RAN", "qemu's 24Kf decodes 0x7C02E83B as `rdhwr v0,$29` (量, "
                     "objdump -m mips:isa32r2) and MIPS32r2 does not gate rdhwr "
                     "on HWREna in kernel mode, so it executes and returns the "
                     "0 that nothing has written into HWR 29"),
    "mfc2":   ("TRAPS ExcCode 10", "predicted CpU and got RI: a 24Kf implements "
                                   "no CP2 at all, so opcode 0x12 is not decoded "
                                   "as a coprocessor instruction and never "
                                   "reaches the enable check"),
    "ltw":    ("RAN", "🔴 A FINDING ABOUT THE INSTRUMENT. Both `mips:3000` and "
                      "`mips:isa32r2` DECLINE to name 0x7940003C -- 量 -- and "
                      "qemu-system-mips 8.2.2 on -M malta retires it with no "
                      "exception. So the qemu arm cannot be the negative control "
                      "for this row, and this row is the one whose membership "
                      "word names this core by number"),
}


def read_rows(path, nrows):
    """Parse a capture into the flat result block.

    Two input shapes, because the payload has two channels and they must agree:

      * the payload's own `P4 <idx> <name> <8 words>` lines -- the only channel
        qemu has, and a second one on the device;
      * a loader `DW` read-back of the result block.

    Only the first is implemented here.  The `DW` parser is `R1-pub-3`'s, and
    it is NOT written blind: `tools/rbcheck.py` already parses that format for
    probe3 and the seating's card is where the two are compared.  A parser
    written now against a capture that does not exist would be a second
    implementation of a format nobody has read yet.
    """
    words = [None] * (nrows * ROW_WORDS)
    seen = {}
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    for line in txt.replace("\r", "\n").split("\n"):
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        idx = int(m.group(1), 16)
        vals = [int(x, 16) for x in m.group(3).split()]
        if idx >= nrows:
            raise Refuse("capture has row index %d and the table has %d rows"
                         % (idx, nrows))
        if idx in seen and seen[idx] != vals:
            raise Refuse("row %d appears twice with different values" % idx)
        seen[idx] = vals
        words[idx * ROW_WORDS:(idx + 1) * ROW_WORDS] = vals
    if not seen:
        raise Refuse("no `P4 ` rows in %s -- an empty capture and a capture of "
                     "absences are different answers" % path)
    return words, sorted(seen)


def exccode(cause):
    return (cause >> 2) & 0x1F


def cmd_verdict(rows, path, arm="device", quiet=False):
    """The three-way verdict, computed HERE and never in the payload.

    `arm` is `qemu` or `device`.  On the qemu arm the `qemu` column is a
    PRE-REGISTERED prediction and this compares against it; on the device arm
    it is not evidence at all -- `plan:706` (D14-1) -- and is printed only so
    the two columns can be read side by side.
    """
    words, present = read_rows(path, len(rows))
    out = []
    for r in rows:
        base = r["idx"] * ROW_WORDS
        rec = tuple(words[base:base + ROW_WORDS])
        if any(x is None for x in rec):
            out.append((r, V_NORUN, None, None))
            continue
        v, val = verdict_row(r, rec)
        out.append((r, v, val, rec))

    tally = {}
    mispredicted = []
    for r, v, val, rec in out:
        tally[v] = tally.get(v, 0) + 1
        if arm != "qemu":
            continue
        want = r["qemu_kind"]
        got = "trap" if v == V_TRAP else "run"
        exc = exccode(rec[2]) if rec and rec[1] else None
        if got != want or (r["qemu_exc"] is not None and exc != r["qemu_exc"]):
            mispredicted.append((r, v, exc))

    if not quiet:
        print("  %-10s %-10s %-8s %-9s %-9s %s"
              % ("row", "group", "verdict", "value", "expect", "cause"))
        for r, v, val, rec in out:
            cs = ("ExcCode %-2d" % exccode(rec[2])) if (rec and rec[1]) else "-"
            print("  %-10s %-10s %-8s %-9s %-9s %s"
                  % (r["name"], r["group"], v,
                     ("%08X" % val) if val is not None else "-",
                     ("%08X" % r["expect_v"]) if r["expect_v"] is not None else "-",
                     cs))
    print()
    print("verdict (%s arm): %d row(s), %s"
          % (arm, len(rows),
             ", ".join("%s %d" % (k, tally[k]) for k in sorted(tally))))

    findings = check_controls(out)
    for f in findings:
        print("  CONTROL: %s" % f)
    novel = []
    if arm == "qemu":
        print("  pre-registered qemu predictions: %d of %d hit"
              % (len(rows) - len(mispredicted), len(rows)))
        for r, v, exc in mispredicted:
            got = v if exc is None else "%s ExcCode %d" % (v, exc)
            known = QEMU_REFUTED.get(r["name"])
            tag = "recorded" if known and known[0] == got else "NEW"
            if tag == "NEW":
                novel.append(r["name"])
            print("    %-10s predicted %-9s got %-22s %s"
                  % (r["name"], r["qemu"], got, tag))
            if known and tag == "recorded":
                print("      %s" % known[1])
        # The other direction: a row on the refuted list that now agrees is an
        # entry nobody removed, and the list would quietly stop being a record
        # of what happened.
        seen = set(r["name"] for r, _, _ in mispredicted)
        for n in sorted(set(QEMU_REFUTED) - seen):
            print("    %-10s is on the refuted list and now AGREES with its "
                  "prediction -- the list is stale" % n)
            novel.append(n)
    return 1 if (findings or novel) else 0


def check_controls(out):
    """The two-sided control on the answer checker itself.

    `plan:761` -- if the answer checker says the reserved encoding ANSWERED
    CORRECTLY, the checker is wrong and the whole table is void.  And the
    positive half, `plan:1074`: the baseline group must come back RIGHT, or the
    checker has never been shown able to say RIGHT at all.
    """
    findings = []
    base = [(r, v) for r, v, _, _ in out if r["group"] == "baseline"]
    res = [(r, v) for r, v, _, _ in out if r["group"] == "reserved"]
    if not base:
        findings.append("no baseline rows -- the answer checker has no positive "
                        "control and plan:1074's pass condition cannot be met")
    for r, v in base:
        if v != V_RIGHT:
            findings.append("POSITIVE CONTROL %s read %s, not RIGHT" % (r["name"], v))
    if not res:
        findings.append("no reserved row -- plan:1075's negative control is absent "
                        "and the table is void without it")
    for r, v in res:
        if v == V_RIGHT:
            findings.append("NEGATIVE CONTROL %s read RIGHT -- the answer checker "
                            "is wrong and the table is VOID (plan:761)" % r["name"])
    return findings


# --------------------------------------------------------------------------
def self_test():
    """Controls.  A tool that cannot fail proves nothing."""
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

    rows = load_rows()

    # T0 -- the committed table is clean, and the rest of the run is refused if
    # it is not: every case below would otherwise be measuring a broken table.
    def t0():
        assert cmd_encode(rows, quiet=True) == 0, "encode is not clean"
        assert cmd_model(rows, quiet=True) == 0, "model is not clean"
    case("T0  the committed table passes encode and model", t0)
    if cmd_encode(rows, quiet=True) or cmd_model(rows, quiet=True):
        print("REFUSING: the committed table already fails -- every control "
              "below would 'pass' against a table that is already wrong")
        return 3

    # T1..T7 -- the parser refuses, one per rule.
    def mk(body):
        import tempfile
        fd, p = tempfile.mkstemp(suffix=".tsv")
        os.close(fd)
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(COLUMNS) + "\n" + body)
        return p

    # The fixture is named `add` and not `t`, and that is not cosmetic: the
    # first draft named it `t`, `MODELS` has no `t`, so T9's mutation took the
    # "no model" branch and the control could not fire.  T9 reported that
    # correctly, which is the only reason it was found.
    good = ("baseline\tadd\talu\top=0,rs=8,rt=9,rd=2,fn=0x20\t0x01091020\t0x1\t0x2"
            "\t0x0\t0x0\t0xDEAD\tgpr\t0x3\trun\twhy\n")
    case("T1  a duplicate name refuses",
         lambda: refuses(lambda: load_rows(mk(good + good)), "two rows named add"))
    case("T2  an unknown shape refuses",
         lambda: refuses(lambda: load_rows(mk(good.replace("\talu\t", "\tzzz\t"))),
                         "shape zzz"))
    case("T3  a short row refuses",
         lambda: refuses(lambda: load_rows(mk("a\tb\tc\n")), "3 fields"))
    case("T4  a pipe in a row refuses",
         lambda: refuses(lambda: load_rows(mk(good.replace("why", "a|b"))),
                         "pipe would break spec-check C8"))
    case("T5  an unknown group refuses",
         lambda: refuses(lambda: load_rows(mk(good.replace("baseline\t", "zz\t", 1))),
                         "group zz"))
    case("T6  a qemu column that is neither run nor trap refuses",
         lambda: refuses(lambda: load_rows(mk(good.replace("\trun\t", "\tmaybe\t"))),
                         "qemu maybe"))
    case("T7  a field that does not fit its width refuses",
         lambda: refuses(lambda: encode_fields({"op": 0, "rs": 99}, "t"),
                         "rs 99 needs 7 bits"))

    # T8 -- the encode control: one wrong word must be caught.
    def t8():
        p = mk(good.replace("0x01091020", "0x01091021"))
        rr = load_rows(p)
        assert cmd_encode(rr, quiet=True) == 1, "a wrong word was not caught"
    case("T8  encode catches a word that disagrees with its fields", t8)

    # T9 -- the model control.
    def t9():
        p = mk(good.replace("\t0x3\t", "\t0x4\t"))
        rr = load_rows(p)
        assert cmd_model(rr, quiet=True) == 1, "a wrong expectation was not caught"
    case("T9  model catches an expectation that disagrees with the semantics", t9)

    # T10 -- expect == seed is refused on an ordinary row, because the two
    # readings collapse.
    case("T10 an ordinary row whose expect equals its seed refuses",
         lambda: refuses(
             lambda: load_rows(mk(good.replace("\t0xDEAD\tgpr\t0x3\t",
                                               "\t0x3\tgpr\t0x3\t"))),
             "expect == seed on a baseline row"))

    # T10b -- and the OPPOSITE sign on the reserved row.  The equality that is
    # a defect above is the control there, so a reserved row without it is
    # refused too.  One rule, both directions, neither loseable by editing.
    reserved_bad = ("reserved\tt2\talu\top=0,fn=0x0E\t0x0000000E\t0x0\t0x0\t0x0"
                    "\t0x0\t0xDEAD\tgpr\t0x1234\ttrap\twhy\n")
    case("T10b a reserved row whose expect does NOT equal its seed refuses",
         lambda: refuses(lambda: load_rows(mk(reserved_bad)),
                         "the trap for the answer checker would not be laid"))
    case("T10c the same reserved row with expect == seed parses",
         lambda: load_rows(mk(reserved_bad.replace("\t0x1234\t", "\t0xDEAD\t"))))

    # T11 -- the shape/opcode cross-check.
    def t11():
        p = mk(good.replace("\talu\top=0,rs=8,rt=9,rd=2,fn=0x20\t0x01091020",
                            "\talu\top=0x23,rs=10,rt=2,imm=0\t0x8D420000"))
        rr = load_rows(p)
        assert cmd_encode(rr, quiet=True) == 1, "a load declared alu was not caught"
    case("T11 a load opcode declared as alu is a finding", t11)

    # T12 -- the generated files are a function of the table.
    def t12():
        a1 = gen_asm(rows)
        a2 = gen_asm(rows)
        assert a1 == a2, "generation is not deterministic"
        assert "rlx_p4_%s_w" % rows[0]["name"] in a1, "no probe symbol emitted"
        assert ".set\tnoreorder" in a1, "the cells are not under noreorder"
    case("T12 generation is deterministic and emits the probe symbols", t12)

    # T13 -- every load in the generated asm is followed by something that does
    # not read it.  This is hazlint's own question, asked here so a generator
    # change is caught before a build.
    def t13():
        a = gen_asm(rows)
        lines = [l.split("/*")[0].strip() for l in a.split("\n")]
        lines = [l for l in lines if l and not l.startswith(".")
                 and not l.endswith(":")]
        bad = []
        for i, l in enumerate(lines[:-1]):
            m = re.match(r"^lw\s+\$(\d+),", l)
            if not m:
                continue
            reg = "$" + m.group(1)
            nxt = lines[i + 1]
            if re.search(r"(^|[\s,])" + re.escape(reg) + r"(\s|,|\()", nxt):
                bad.append((l, nxt))
        assert not bad, "load-use in the generated asm: %r" % bad[:2]
    case("T13 no generated load is read by the next instruction", t13)

    # T14 -- the verdict function's three cells, each reached.
    def t14():
        r = dict(rows[0])
        r["idx"] = 0
        tag = ROW_TAG_BASE
        e = r["expect_v"]
        assert verdict_row(r, (tag, 1, 0x28, 0, 0, 0, 0, 0))[0] == V_TRAP
        assert verdict_row(r, (tag, 0, 0, 0, e, 0, 0, 0))[0] == V_RIGHT
        assert verdict_row(r, (tag, 0, 0, 0, _u32(e + 1), 0, 0, 0))[0] == V_WRONG
        assert verdict_row(r, (0, 0, 0, 0, e, 0, 0, 0))[0] == V_NORUN
        assert exccode(0x28) == 10, "ExcCode extraction"
    case("T14 all three verdict cells and NOT-RUN are reachable", t14)

    # T15 -- the two-sided control on the answer checker.
    def t15():
        bl = [r for r in rows if r["group"] == "baseline"][0]
        rv = [r for r in rows if r["group"] == "reserved"][0]
        good_out = [(bl, V_RIGHT, 0, None), (rv, V_TRAP, 0, None)]
        assert check_controls(good_out) == [], "a healthy table reported findings"
        bad1 = [(bl, V_WRONG, 0, None), (rv, V_TRAP, 0, None)]
        assert check_controls(bad1), "a failing POSITIVE control was not caught"
        bad2 = [(bl, V_RIGHT, 0, None), (rv, V_RIGHT, 0, None)]
        f = check_controls(bad2)
        assert any("VOID" in x for x in f), "a RIGHT reserved row did not void"
        assert check_controls([(rv, V_TRAP, 0, None)]), "no baseline was not caught"
        assert check_controls([(bl, V_RIGHT, 0, None)]), "no reserved was not caught"
    case("T15 the answer checker's own controls fire in both directions", t15)

    # T16 -- lwl/lwr/swl/swr against hand-worked big-endian examples.  These
    # are the rows Lexra is said to have removed, so the model has to be right
    # about them for the WRONG cell to mean anything.
    def t16():
        M0, M1, SD = 0xA5A5F00D, 0x5A5A0FF2, 0x11223344
        assert m_lwl(m0=M0, m1=M1, imm=1, seed=SD) == 0xA5F00D44, "lwl@1"
        assert m_lwl(m0=M0, m1=M1, imm=0, seed=SD) == 0xA5A5F00D, "lwl@0"
        assert m_lwr(m0=M0, m1=M1, imm=3, seed=SD) == 0xA5A5F00D, "lwr@3"
        assert m_lwr(m0=M0, m1=M1, imm=1, seed=SD) == 0x1122A5A5, "lwr@1"
        assert m_swl(b=0xAABBCCDD, m0=0, m1=0, imm=1) == 0x00AABBCC, "swl@1"
        # 🔴 This value was 0xCCDD0000 in the first draft and the model said
        # 0xBBCCDD00.  Hand-worked: big-endian SWR at byte 2 writes memory
        # bytes 0..2 from rt's bytes 1..3, so BB CC DD 00.  The model was right
        # and the assertion was wrong -- recorded because a control that only
        # ever agrees with the thing it checks is not a control.
        assert m_swr(b=0xAABBCCDD, m0=0, m1=0, imm=2) == 0xBBCCDD00, "swr@2"
    case("T16 the unaligned model matches hand-worked big-endian examples", t16)

    # T16b -- the pair, which is a STRONGER control than any single value: the
    # only reason these four instructions exist is that `lwl A` + `lwr A+3`
    # reconstructs an unaligned word and `swl`/`swr` write one back.  If the
    # shift directions were mirrored, every individual value above could still
    # be defended and the pair would not close.
    def t16b():
        W0, W1 = 0x11223344, 0x55667788
        # the unaligned word at byte offset 1 is 22 33 44 55
        got = m_lwl(m0=W0, m1=W1, imm=1, seed=0xFFFFFFFF)
        got = m_lwr(m0=W0, m1=W1, imm=4, seed=got)
        assert got == 0x22334455, "lwl/lwr pair gave 0x%08X" % got
        # and writing 0xAABBCCDD back to that same unaligned address
        n0 = m_swl(b=0xAABBCCDD, m0=W0, m1=W1, imm=1)
        n1 = m_swr(b=0xAABBCCDD, m0=W0, m1=W1, imm=4)
        assert n0 == 0x11AABBCC, "swl leg gave 0x%08X" % n0
        assert n1 == 0xDD667788, "swr leg gave 0x%08X" % n1
    case("T16b the lwl/lwr and swl/swr PAIRS reconstruct an unaligned word", t16b)

    # T18 -- source 3's own question, unit-tested without an artefact.  This is
    # the ONLY check that can catch a row named for one instruction and
    # encoding another: `encode` and `model` both read the table's own fields,
    # and the table's own fields are what would be wrong.
    def t18():
        rr = {"name": "add", "group": "baseline"}
        assert decode_ok(rr, "add\tv0,t0,t1")[0], "a correct decode was rejected"
        assert not decode_ok(rr, "lw\tv0,0(t2)")[0], "a wrong mnemonic passed"
        assert not decode_ok(rr, ".word\t0xe")[0], \
            "an unnamed encoding passed on a row that claims a mnemonic"
        res = {"name": "special0e", "group": "reserved"}
        assert decode_ok(res, ".word\t0xe")[0], "the reserved row was rejected"
        assert not decode_ok(res, "add\tv0,t0,t1")[0], \
            "a NAMED encoding passed on a row that claims to be reserved"
        assert expected_mnemonic("cache10") == "cache"
        assert expected_mnemonic("mult_hi") == "mult"
        assert expected_mnemonic("add") == "add"
        # The nine rows the first normaliser broke: a digit that is part of the
        # mnemonic must survive.
        for n in ("mfc1", "mfc2", "mfc3", "lwc1", "swc1", "lwc3", "swc3",
                  "cfc3", "mtc3"):
            assert expected_mnemonic(n) == n, "digit stripped from %s" % n
    case("T18 verify's decode check fires in both directions", t18)

    # T18b -- the dual-meaning rows are REPORTED and not absorbed.  An alias
    # that silences a finding is worse than no alias.
    def t18b():
        for n, (m1, why) in MNEMONIC_ALIAS.items():
            if m1 == n:
                continue
            ok, msg = decode_ok({"name": n, "group": "mips2"}, m1 + "\tx")
            assert ok, "the alias for %s does not accept its own mnemonic" % n
            if n in ("ll", "sc", "pref"):
                assert msg.startswith("DUAL:"), \
                    "%s is a dual-meaning row and verify did not say so" % n
        ok, _ = decode_ok({"name": "ll", "group": "mips2"}, "ll\tx")
        assert not ok, "a MIPS-II decode of the ll row was not a finding"
    case("T18b every dual-meaning row says so on every run", t18b)

    # T19 -- the converse check, both directions, without a cross-compiler.
    # 量 2026-09-13: run for real against `probe3.elf`, which declares none of
    # these words, it reports EIGHT strays -- probe3's `mfc3` stubs.  That is
    # the shape this guards: a non-MIPS-I word in framework code, which nothing
    # declared and which would execute on every row.
    def t19():
        text = ("      mfc3               MIPS-I COP3     1\n"
                "          0x80501c80  4c020000  |L...|   mfc3  v0,$0\n"
                "      swl                MIPS-I unaligned    1\n"
                "          0x80502000  a9490001  |.I..|   swl   t1,1(t2)\n")
        seen, stray = converse_stray(text, {0x80501C80, 0x80502000})
        assert seen == 2, "saw %d hits, expected 2" % seen
        assert not stray, "a declared probe site was called a stray"
        seen, stray = converse_stray(text, {0x80501C80})
        assert len(stray) == 1 and stray[0][0] == 0x80502000, \
            "an undeclared non-MIPS-I word was not caught"
        seen, stray = converse_stray("", {0x80501C80})
        assert seen == 0 and not stray, "empty input is not an empty answer"
    case("T19 the converse check catches a word outside every probe site", t19)

    # T17 -- the population join reports a difference rather than hiding it.
    def t17():
        mine = set(r["name"] for r in rows)
        cen = set(census_names())
        assert mine - cen or cen - mine, \
            "the two populations are identical, which this join exists to deny"
    case("T17 payload and census populations are joined, not assumed equal", t17)

    print("self-test: %d of %d" % (ok, n))
    return 0 if ok == n else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", nargs="?",
                    choices=["population", "encode", "model", "emit", "verify",
                             "verdict"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="also require every non-MIPS-I word hazlint can see "
                         "to sit at a declared probe symbol")
    ap.add_argument("--arm", choices=["qemu", "device"], default="device")
    ap.add_argument("--objdump")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test()
        if not a.mode:
            ap.print_help()
            return 3
        rows = load_rows()
        if a.mode == "encode":
            return cmd_encode(rows, a.quiet)
        if a.mode == "model":
            return cmd_model(rows, a.quiet)
        if a.mode == "population":
            return cmd_population(rows, a.quiet)
        if a.mode == "emit":
            return cmd_emit(rows, a.check)
        if a.mode == "verify":
            if not a.arg:
                raise Refuse("verify needs an ELF")
            return cmd_verify(rows, a.arg, a.objdump, a.quiet, a.strict)
        if a.mode == "verdict":
            if not a.arg:
                raise Refuse("verdict needs a capture")
            return cmd_verdict(rows, a.arg, a.arm, a.quiet)
    except Refuse as e:
        print("REFUSED: %s" % e)
        return 3
    return 3


if __name__ == "__main__":
    sys.exit(main())
