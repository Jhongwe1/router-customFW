#!/usr/bin/env python3
"""hazpay -- generate and check `probe5`, `R1b`'s hazard ladder.

`plan/router-rebuild-plan.md:1031-1046` specifies the payload:

    這些 hazard 不會發 signal，它們安靜地算出錯的值。
    每個測試計算一個已知正確答案、且在 interlock 與非 interlock 下結果不同的值
    …
    每一列的輸出是「這個 hazard 外露 / 不外露 / 測不出來」，
    而「測不出來」是一個合法且要寫下來的結果。

and `PROGRESS.md:122`'s risk column states the way to lose it:

    A hazard test that the compiler has already fixed.  `-O` may insert the
    very `nop` the test exists to detect; the payload has to be read as built,
    not as written.

SO NOTHING HERE TRUSTS THE SOURCE.  The distance between a producer and its
consumer is asserted against the BUILT ARTEFACT's symbol table by
`tools/hazdecl.py`, and the hazard's presence is asserted against
`tools/hazlint`'s own output -- the unmodified build gate, read the other way
round.  `hazpay` generates; `hazdecl` refuses.

TWO SOURCES FOR EVERY CONSTANT, AND THE TWO CONSTANTS ARE DIFFERENT KINDS OF
CLAIM.  This is the load-bearing difference from `isapay`.

    lock  讀.  Ordinary ISA semantics.  `MODELS` derives it from the operands
          by name, without reading the `lock` column.
    open  推.  MIPS-I says reading a result too early is UNPREDICTABLE, so
          *the consumer sees the register's prior value* is a hypothesis about
          THIS IMPLEMENTATION.  `MODELS` derives it too, but from the same
          hypothesis -- which is why the docs mark it 推 and why `OTHER` is a
          reading and not a failure.

THE PAYLOAD COMPARES NOTHING.  It records eight words per row and
`hazpay verdict` decides at the desk, exactly as `probe4` does.  The expected
constants are not in the image.

C4 IS MANDATORY AND IT IS NOT OPTIONAL BOOKKEEPING.  `plan/DAY-ZERO.md:603`:

    每個 hazard 測試在 qemu 下必須給出「有 interlock」的相反答案。
    那證明測試本身有鑑別力 —— 否則你分不出「這顆有 interlock」和
    「我的測試沒測到東西」。

so the `qemu` column is `lock` for every row, the parser refuses anything else,
and a qemu-arm row that reads anything but LOCK is a finding that voids that
row.  There is no refuted-prediction allow-list here, unlike `isapay`'s
`QEMU_REFUTED`: a refuted hazard prediction is not a curiosity about qemu's
decoder, it is loss of discriminating power for the row.

usage
    hazpay.py population              the families, joined to the prior-art census
    hazpay.py model                   two sources for lock / open / ctl
    hazpay.py emit [--check]          write (or check) cells5.S, probe5rows.{h,mk}
    hazpay.py verify ELF [--strict]   the artefact: encodings and the distances
    hazpay.py verdict LOG [--arm A]   the desk verdict
    hazpay.py sites [ELF]             the hazard-site declaration hazdecl consumes
    hazpay.py --self-test

exit
    0  clean
    1  a finding
    3  REFUSED: nothing parsed, or a control failed, or no mode given
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TSV = os.path.join(HERE, "isa-hazard.tsv")
CENSUS = os.path.join(HERE, "isa-census.tsv")
CELLS_S = os.path.join(HERE, "rlxprobe", "cells5.S")
ROWS_H = os.path.join(HERE, "rlxprobe", "probe5rows.h")
ROWS_MK = os.path.join(HERE, "rlxprobe", "probe5rows.mk")
HAZLINT = os.path.join(HERE, "hazlint")

COLUMNS = ("family", "name", "dist", "kind", "in_a", "in_b", "mem0", "mem1",
           "seed", "read", "lock", "open", "ctl", "haz", "qemu", "dev", "why")

# The families, and the one place that says which of them exist.  `population`
# joins this against `docs/isa-prior-art.md` § 4's six rows in both directions:
# a family here with no census row, and a census row with no family, are both
# reportable.  The mapping is not one-to-one and that is the point -- § 4's
# single `store` row became three families once its shape was specified
# (量 2026-09-13), and its own text says specifying it was this step's first job.
FAMILIES = ("loaduse", "storedata", "storebase", "hilo", "cp0",
            "movcond", "movrd", "dslot", "storeprod", "hiloprime")

# Which census row each family answers.  The census's row labels are long
# sentences; these are the substrings that identify them, and `population`
# refuses if one of them stops matching -- a census row that was reworded is a
# join that silently found nothing.
CENSUS_KEY = {
    "loaduse":   "load then a reader",
    "storedata": "store, the class",
    "storebase": "store, the class",
    "hilo":      "mult/div then",
    "cp0":       "mtc0 then mfc0",
    "movcond":   "movz or movn",
    "movrd":     "movz or movn",
    "dslot":     "a load sitting in a delay slot",
    "storeprod": "store, the class",
    # `None` means CONTROL FAMILY, no census row BY DESIGN, and the reason is the
    # census's own: `docs/isa-prior-art.md` § 0 says it "does not claim that the
    # population is the ISA" and excludes what obviously works -- and
    # `docs/isa-payload.md` § 1 records that the instructions it excludes by that
    # rule are exactly `R1a`'s positive control.  A payload built from the census
    # alone therefore has no positive control.  `population` prints these rather
    # than skipping them, and the reverse direction still requires every census
    # row to have a family.
    "hiloprime": None,
}

READS = ("gpr", "m0", "m1")          # `aux` is the control's and never a row's
KINDS = ("haz", "ctl")
CHANNELS = ("main", "survey", "both", "none")

# Constants the TEMPLATES own.  They are here and not in the table because the
# asm formats them in and `MODELS` imports these same names, so the model cannot
# drift from the code that runs -- `isapay`'s `_madd_acc` is the precedent.
PRIME_LO = 0xCAFE0000       # what LO holds before `mult`
PRIME_HI = 0xBEEF0000       # and HI, so a half that did not move is visible
EPC_OLD = 0xA5A5A5A0        # CP0 14 before the write under test
EPC_NEW = 0x5A5A5A50        # and after it
CP0_EPC = 14

MOVN_W = 0x0109100B         # movn $2,$8,$9.  A WORD: 量 2026-09-13 that
                            # -march=mips1 REJECTS the mnemonic outright.

# The scratch block, byte offsets.  One owner; `probe5.c` reads these out of the
# generated header.  Offset 12 is USED here where `probe4` left it a hole: the
# `storebase` family needs a memory word holding `&mem0`, and a runtime address
# cannot come from the table.
OFF = {"in_a": 0, "in_b": 4, "seed": 8, "addr0": 12, "mem0": 16, "mem1": 20,
       "out_gpr": 24, "out_m0": 28, "out_m1": 32, "out_aux": 36}
SCRATCH_BYTES = 48

ROW_WORDS = 8
ROW_TAG_BASE = 0x52350000   # 'R5' << 16.  probe4's is 'R4' << 16, so a capture
                            # from one payload cannot be read as the other's.


class Refuse(Exception):
    pass


def _hx(s, what):
    s = s.strip()
    if s == "-":
        return None
    try:
        return int(s, 0) & 0xFFFFFFFF
    except ValueError:
        raise Refuse("%s: %r is not a number" % (what, s))


# --------------------------------------------------------------------------
# the table
# --------------------------------------------------------------------------

def load_rows(path=TSV):
    """Parse the table, and refuse rather than repair.

    Every refusal below is a row shape that would build, run, and answer a
    different question from the one the row claims to ask.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError as e:
        raise Refuse("cannot read %s: %s" % (path, e))

    body = [l for l in lines if l.strip() and not l.startswith("#")]
    if not body:
        raise Refuse("%s: no rows" % path)
    hdr = tuple(body[0].split("\t"))
    if hdr != COLUMNS:
        raise Refuse("%s: header is %r, expected %r" % (path, hdr, COLUMNS))

    rows, seen = [], set()
    for n, line in enumerate(body[1:]):
        f = line.split("\t")
        if len(f) != len(COLUMNS):
            raise Refuse("row %d: %d fields, expected %d"
                         % (n, len(f), len(COLUMNS)))
        if "|" in line:
            raise Refuse("row %d: a `|` -- spec-check C8 counts cells by pipe"
                         % n)
        r = dict(zip(COLUMNS, f))
        if r["name"] in seen:
            raise Refuse("duplicate name %s" % r["name"])
        seen.add(r["name"])

        if r["family"] not in FAMILIES:
            raise Refuse("row %s: family %s is not one of %s"
                         % (r["name"], r["family"], ",".join(FAMILIES)))
        if r["kind"] not in KINDS:
            raise Refuse("row %s: kind %s is not one of %s"
                         % (r["name"], r["kind"], ",".join(KINDS)))
        if r["read"] not in READS:
            raise Refuse("row %s: read %s is not one of %s (aux belongs to the "
                         "control, never to a row)"
                         % (r["name"], r["read"], ",".join(READS)))
        if r["haz"] not in CHANNELS:
            raise Refuse("row %s: haz %s is not one of %s"
                         % (r["name"], r["haz"], ",".join(CHANNELS)))
        if r["qemu"] != "lock":
            raise Refuse("row %s: qemu is %s. C4 (plan/DAY-ZERO.md:603, "
                         "plan:1074) makes the interlocked arm mandatory, so a "
                         "row predicting anything else is predicting that qemu "
                         "has no interlock" % (r["name"], r["qemu"]))
        if r["dev"] not in ("-", "lock", "open"):
            raise Refuse("row %s: dev %s is not -, lock or open"
                         % (r["name"], r["dev"]))
        try:
            r["dist"] = int(r["dist"], 10)
        except ValueError:
            raise Refuse("row %s: dist %r is not a decimal integer"
                         % (r["name"], r["dist"]))
        if r["dist"] < 0 or r["dist"] > 8:
            raise Refuse("row %s: dist %d is outside 0..8" % (r["name"], r["dist"]))

        for k in ("in_a", "in_b", "mem0", "mem1", "seed", "lock", "open", "ctl"):
            v = _hx(r[k], "row %s column %s" % (r["name"], k))
            if v is None:
                raise Refuse("row %s: %s is `-`. Every column here carries a "
                             "value: a hazard row with no expectation cannot "
                             "distinguish anything, which is what `kind` is for"
                             % (r["name"], k))
            r[k + "_v"] = v

        # THE RULE, AND ITS OPPOSITE SIGN.  A `haz` row whose two constants are
        # equal cannot tell "the hazard is closed" from "the hazard is open",
        # and every such row would read LOCK whatever the die did.  That is
        # `isapay`'s recorded `T_JR` defect -- a template that cannot express
        # failure -- as a table shape.  A `ctl` row is the other way round by
        # declaration, because there is nothing for it to distinguish.
        if r["kind"] == "haz" and r["lock_v"] == r["open_v"]:
            raise Refuse("row %s: lock == open == 0x%08X. The two readings "
                         "collapse and the row would read LOCK whatever "
                         "happened" % (r["name"], r["lock_v"]))
        # `probe5.c`'s `run_row` zeroes `out_aux` before the call and counts the
        # rows where it stayed zero (`H_AUX_ZERO`), so 0 is that payload's
        # sentinel for *the cell never reached its control*.  A row whose `ctl`
        # were 0 would make that sentinel and a passing control one word.
        if r["ctl_v"] == 0:
            raise Refuse("row %s: ctl is 0, which is probe5's sentinel for *the "
                         "cell never wrote its control*. The two readings would "
                         "collapse" % r["name"])

        if r["kind"] == "ctl" and r["lock_v"] != r["open_v"]:
            raise Refuse("row %s: kind is ctl but lock 0x%08X != open 0x%08X. "
                         "A control row declares that there is nothing to "
                         "distinguish; two different constants claim otherwise"
                         % (r["name"], r["lock_v"], r["open_v"]))

        # TWO SOURCES FOR THE CHANNEL, and the second one caught the first being
        # wrong.  `haz` is hand-written and `derived_channel` computes it from
        # family and distance; a disagreement is a row whose author believed
        # something wrong about the shape.
        #
        # 🔴 量 2026-09-13, by `tools/hazdecl.py` firing on its FIRST real build:
        # `ds_d1` was declared `none` on the reasoning that a padded rung carries
        # no hazard site.  That is true of the load-use check and FALSE of the
        # survey -- a load in a branch delay slot is in a delay slot at every
        # rung, because the padding sits between the branch TARGET and the
        # consumer and not between the branch and the load.  The `haz` column had
        # been conflating *is there a load-use violation here* with *is this shape
        # counted*, and for `dslot` those differ.
        want = derived_channel(r["family"], r["dist"], r["kind"])
        if r["haz"] != want:
            raise Refuse("row %s: haz is %s and family %s at dist %d derives "
                         "%s. %s"
                         % (r["name"], r["haz"], r["family"], r["dist"], want,
                            _channel_why(r["family"])))

        # The family's own preconditions.  These are the rows' ability to
        # produce the wrong answer, which is `PROGRESS.md:122`'s pass condition,
        # and they are per-family because "can this row fail" is not a generic
        # property.
        _family_precondition(r)

        r["idx"] = len(rows)
        rows.append(r)

    if not rows:
        raise Refuse("%s: header only" % path)
    return rows


# Which families appear in `hazlint --survey`'s three buckets, and whether that
# presence depends on the distance.  量 2026-09-13, nine shapes each with both
# controls, and the `dslot` row is the one that is not what it looks like.
SURVEY_DIST_FREE = ("dslot",)        # counted at EVERY rung: the load's POSITION
SURVEY_AT_D0 = ("hilo", "cp0")       # counted only when producer and consumer
                                     # are adjacent, which is what the shape is

# 🔴 AND THE MAIN CHECK NEEDS THIS, which the first draft of `derived_channel`
# did not have.  `hazlint`'s load-use rule is *for every LOAD, does an
# instruction that can execute next read the register that was loaded*, so a
# family whose producer is not a load is invisible to it at every rung.  `hilo`
# produces with `mult` and `cp0` with `mtc0`; `storeprod` produces with `sw`.
# 量 2026-09-13 on the first real build: 7 main-channel violations, and they are
# exactly the six load-producing families' d0 rungs.
PRODUCER_IS_LOAD = ("loaduse", "storedata", "storebase", "movcond", "movrd",
                    "dslot")


def derived_channel(family, dist, kind):
    """Which `hazlint` channels this rung's site must appear in, derived.

    `main` presence is *a LOAD whose consumer is the next instruction executed*,
    so it needs both `dist == 0` and a load-producing family.  Survey presence is
    family-specific, and for one family it does not depend on the distance at all.
    """
    if kind == "ctl":
        return "none"
    main = (dist == 0) and family in PRODUCER_IS_LOAD
    if family in SURVEY_DIST_FREE:
        surv = True
    elif family in SURVEY_AT_D0:
        surv = (dist == 0)
    else:
        surv = False
    if main and surv:
        return "both"
    if main:
        return "main"
    if surv:
        return "survey"
    return "none"


def _channel_why(family):
    bits = []
    if family in PRODUCER_IS_LOAD:
        bits.append("`%s` produces with a LOAD, so hazlint's load-use check sees "
                    "it at dist 0 and nowhere else" % family)
    else:
        bits.append("`%s` does NOT produce with a load, so hazlint's load-use "
                    "check is silent about it at every rung" % family)
    if family in SURVEY_DIST_FREE:
        bits.append("and the survey counts it at EVERY rung -- the load sits in a "
                    "branch delay slot whatever the padding, because the padding "
                    "is between the branch target and the consumer")
    elif family in SURVEY_AT_D0:
        bits.append("and the survey counts it only when producer and consumer are "
                    "adjacent, which is the shape the survey names")
    else:
        bits.append("and it has no survey bucket")
    return ", ".join(bits)


def _family_precondition(r):
    fam, n = r["family"], r["name"]
    a, b, m0, m1, seed = (r["in_a_v"], r["in_b_v"], r["mem0_v"], r["mem1_v"],
                          r["seed_v"])
    if fam in ("loaduse", "storedata", "dslot"):
        if m0 == b:
            raise Refuse("row %s: mem0 == in_b, so the loaded value and the "
                         "register's prior value are the same word and the "
                         "consumer cannot tell them apart" % n)
    elif fam == "storebase":
        if m0 == b or m1 == b:
            raise Refuse("row %s: in_b equals mem0 or mem1, so *which address "
                         "was written* cannot be read out of memory" % n)
        if m0 == m1:
            raise Refuse("row %s: mem0 == mem1, so the two candidate "
                         "destinations are indistinguishable" % n)
    elif fam == "hilo":
        prod = a * b
        if (prod & 0xFFFFFFFF) == PRIME_LO:
            raise Refuse("row %s: the product's low half equals the primed LO, "
                         "so *mflo read the new value* and *it read the old one* "
                         "are one reading" % n)
        if ((prod >> 32) & 0xFFFFFFFF) == PRIME_HI:
            raise Refuse("row %s: the product's high half equals the primed HI, "
                         "so the control cannot tell *mult ran* from *it did "
                         "not*" % n)
        if a >= 0x80000000 or b >= 0x80000000:
            raise Refuse("row %s: `mult` is SIGNED and an operand has its top "
                         "bit set, so the model's plain 64-bit split is the "
                         "wrong arithmetic for this row" % n)
    elif fam == "cp0":
        if (EPC_OLD & 3) or (EPC_NEW & 3):
            raise Refuse("the CP0 constants must be word-aligned: a core that "
                         "forces EPC's low two bits to zero would change the "
                         "read-back for a reason that is not the hazard")
        if EPC_OLD == EPC_NEW:
            raise Refuse("EPC_OLD == EPC_NEW: the write under test writes what "
                         "was already there")
    elif fam == "movcond":
        if b != 0:
            raise Refuse("row %s: movcond needs in_b == 0. in_b is the "
                         "condition register's PRIOR value and `movn` moves "
                         "when it is non-zero, so a non-zero prior value makes "
                         "both arms move and the row measures nothing" % n)
        if m0 == 0:
            raise Refuse("row %s: movcond needs mem0 != 0, or the interlocked "
                         "arm does not move either" % n)
        if a == seed:
            raise Refuse("row %s: in_a == seed, so *the move happened* and "
                         "*it did not* leave the same word in $2" % n)
    elif fam == "movrd":
        if b != 0:
            raise Refuse("row %s: movrd needs in_b == 0 so the condition is "
                         "FALSE and the move must not happen. With a non-zero "
                         "condition the move happens and the row stops being "
                         "about the destination at all" % n)
        if m0 == seed:
            raise Refuse("row %s: mem0 == seed, so *the load stood* and *the "
                         "stale destination was written back* are one reading"
                         % n)
    elif fam == "storeprod":
        if b == m0:
            raise Refuse("row %s: in_b == mem0, so the store cannot be seen to "
                         "have happened at all" % n)
    elif fam == "hiloprime":
        if PRIME_LO == PRIME_HI:
            raise Refuse("PRIME_LO == PRIME_HI: this row reads one from LO and "
                         "the other from HI, and equal primes would let a "
                         "misdirected read pass")
        if r["dist"] < 2:
            raise Refuse("row %s: dist %d. This row must sit BEYOND the "
                         "architectural mflo requirement, because its whole "
                         "point is that both machines agree -- a rung inside the "
                         "hazard window would be a hazard row wearing a "
                         "control's name" % (n, r["dist"]))


# --------------------------------------------------------------------------
# source 2 for the expectations: the semantics, written from the ISA and from
# the ONE hypothesis, never from the `lock`/`open`/`ctl` columns
# --------------------------------------------------------------------------
#
# Every model takes NAMED values, so a wrong operand assignment in the table
# cannot propagate into the expectation.  Each returns (lock, open, ctl).
#
# ⚠️ The `open` half of every one of these encodes the SAME hypothesis -- that
# the consumer sees the destination register's value from before the producer --
# so the two sources agree about `open` only in the sense that the arithmetic is
# done twice.  They are not two independent beliefs, and `docs/isa-hazard.md`
# says so rather than letting a reader infer otherwise from the word "model".

def m_loaduse(a, b, m0, m1, seed):
    return m0, b, m0                    # read gpr


def m_storedata(a, b, m0, m1, seed):
    return m0, b, m0                    # read m1: the word the store wrote


def m_storebase_m0(a, b, m0, m1, seed):
    # read m0: written, or left alone.  The control is the settled base as an
    # offset from the scratch pointer, which is 16 on both arms.
    return b, m0, OFF["mem0"]


def m_storebase_m1(a, b, m0, m1, seed):
    return m1, b, OFF["mem0"]           # read m1: left alone, or written


def m_hilo(a, b, m0, m1, seed):
    # `mult` is SIGNED; both operands are positive here, so the 64-bit product is
    # positive and its halves are the plain split.  The control is HI.
    prod = a * b
    return prod & 0xFFFFFFFF, PRIME_LO, (prod >> 32) & 0xFFFFFFFF


def m_cp0(a, b, m0, m1, seed):
    return EPC_NEW, EPC_OLD, EPC_NEW    # read gpr


def m_movcond(a, b, m0, m1, seed):
    # movn $2,$8,$9: move when $9 != 0.  Interlocked, $9 is mem0 (non-zero) so
    # the move happens and $2 becomes in_a.  Open, $9 is still in_b (zero) so it
    # does not and $2 keeps the seed.
    return a, seed, m0


def m_movrd(a, b, m0, m1, seed):
    # The destination is the loaded register and the condition is false.  A
    # write-enable implementation leaves the load standing; one that
    # read-selects and always writes puts the stale destination back.
    return m0, seed, m0


def m_dslot(a, b, m0, m1, seed):
    return m0, b, m0


def m_storeprod(a, b, m0, m1, seed):
    return b, b, b                      # read m0, and the two legs are equal


def m_hiloprime(a, b, m0, m1, seed):
    # No `mult` at all.  LO and HI hold the primes and both machines read them,
    # so the two legs are equal by declaration -- and what the row proves is that
    # `mtlo` and `mthi` WORK.  Without it the `hilo` family's `open` leg is
    # unfalsifiable: if the prime never landed, that family could only ever read
    # LOCK or OTHER, and *the prime did not land* would be indistinguishable from
    # *there is no hazard*.
    return PRIME_LO, PRIME_LO, PRIME_HI


MODELS = {
    "lu_alu_d0": (m_loaduse, "gpr"), "lu_alu_d1": (m_loaduse, "gpr"),
    "lu_alu_d2": (m_loaduse, "gpr"),
    "lu_sd_d0": (m_storedata, "m1"), "lu_sd_d1": (m_storedata, "m1"),
    "sb_m0_d0": (m_storebase_m0, "m0"), "sb_m0_d1": (m_storebase_m0, "m0"),
    "sb_m1_d0": (m_storebase_m1, "m1"), "sb_m1_d1": (m_storebase_m1, "m1"),
    "hl_d0": (m_hilo, "gpr"), "hl_d1": (m_hilo, "gpr"),
    "hl_d2": (m_hilo, "gpr"), "hl_d3": (m_hilo, "gpr"),
    "c0_d0": (m_cp0, "gpr"), "c0_d1": (m_cp0, "gpr"), "c0_d2": (m_cp0, "gpr"),
    "mc_d0": (m_movcond, "gpr"), "mc_d1": (m_movcond, "gpr"),
    "mr_d0": (m_movrd, "gpr"), "mr_d1": (m_movrd, "gpr"),
    "ds_d0": (m_dslot, "gpr"), "ds_d1": (m_dslot, "gpr"),
    "st_p": (m_storeprod, "m0"),
    "hl_ctl": (m_hiloprime, "gpr"),
}


def model_row(r):
    """(lock, open, ctl) from the semantics, or a Refuse if the model and the
    row disagree about which word they are talking about."""
    ent = MODELS.get(r["name"])
    if ent is None:
        return None, None, None
    fn, produces = ent
    if produces != r["read"]:
        raise Refuse("row %s: the model produces %s and the row reads %s -- a "
                     "model that computes one word cannot vouch for another"
                     % (r["name"], produces, r["read"]))
    return fn(a=r["in_a_v"], b=r["in_b_v"], m0=r["mem0_v"], m1=r["mem1_v"],
              seed=r["seed_v"])


# --------------------------------------------------------------------------
# the cell templates.  One per family; the family owns the sequence and the
# control, the table owns the operands and the distance.
# --------------------------------------------------------------------------

PROLOGUE = """\
\taddu\t$24, $4, $0\t\t/* scratch, before SAFE_A0 takes $4 */
\tSAFE_A0
\tlw\t$8, {in_a}($24)
\tlw\t$9, {in_b}($24)
\tlw\t$2, {seed}($24)
\taddiu\t$10, $24, {mem0}
\tnop\t\t\t\t/* LOAD DELAY SLOT for $2 */
"""

EPILOGUE = """\
\tsw\t$2, {out_gpr}($24)
\tlw\t$8, {mem0}($24)
\tnop\t\t\t\t/* LOAD DELAY SLOT */
\tsw\t$8, {out_m0}($24)
\tlw\t$9, {mem1}($24)
\tnop\t\t\t\t/* LOAD DELAY SLOT */
\tsw\t$9, {out_m1}($24)
\tjr\t$31
\tnop
\t.end\trlx_p5_{name}
"""

# Every body is written as four parts so the distance is the ONLY thing that
# varies between rungs: setup, the producer at `_p`, `dist` nops, the consumer
# at `_c`, then settle-and-control.  `gen_body` assembles them, so a rung cannot
# differ from its twin by anything else.

BODIES = {
    "loaduse": dict(
        setup="",
        producer="\tlw\t$9, 0($10)\n",
        consumer="\taddu\t$2, $9, $0\n",
        tail="\tnop\n\tnop\n"
             "\taddu\t$11, $9, $0\t\t/* control: $9, settled */\n"),
    "storedata": dict(
        setup="",
        producer="\tlw\t$9, 0($10)\n",
        consumer="\tsw\t$9, 4($10)\n",
        tail="\tnop\n\tnop\n"
             "\taddu\t$11, $9, $0\t\t/* control: $9, settled */\n"),
    "storebase": dict(
        # $10's PRIOR value is &mem1 and the loaded value is &mem0.  The two
        # differ in ONE BIT (16 against 20), so every bitwise mixture of the two
        # words is still one of the two addresses: containment is structural.
        # `addr0` is written by the payload in C, not stored here, because a
        # store into it would itself be the store-producer shape this table
        # declares not measurable.
        setup="\taddiu\t$10, $24, {mem1}\t\t/* $10 = &mem1, the base's PRIOR value */\n",
        producer="\tlw\t$10, {addr0}($24)\t\t/* -> &mem0, written by the payload */\n",
        consumer="\tsw\t$9, 0($10)\n",
        # The control is the settled BASE, expressed as an offset so the table can
        # name it: a runtime address cannot be a table constant but `$10 - $24`
        # can.  It is 16 on both arms, and it says the load landed EVENTUALLY --
        # which "the data register survived" did not say at all.
        tail="\tnop\n\tnop\n"
             "\tsubu\t$11, $10, $24\t\t/* control: the settled base, as an offset */\n"),
    "hilo": dict(
        setup="\tlui\t$11, 0x{lo_hi:04X}\n"
              "{lo_ori}"
              "\tmtlo\t$11\n\tnop\n\tnop\n"
              "\tlui\t$11, 0x{hi_hi:04X}\n"
              "{hi_ori}"
              "\tmthi\t$11\n\tnop\n\tnop\n",
        producer="\tmult\t$8, $9\n",
        consumer="\tmflo\t$2\n",
        # The control reads HI, not LO.  Two reasons and the second is the one
        # that matters: it makes the primed HI observable, so `mthi` stops being
        # a word in generated code that nothing can rule out; and HI is a
        # DIFFERENT register, so "LO's read port is hazarded" cannot reach the
        # control.  Re-reading LO would have shared a port with the reading.
        tail="\tnop\n\tnop\n"
             "\tmfhi\t$11\t\t\t/* control: HI, settled -- a different register */\n"),
    "cp0": dict(
        setup="\tlui\t$11, 0x{eo_hi:04X}\n"
              "{eo_ori}"
              "\tmtc0\t$11, ${cp0}\t\t\t/* EPC = OLD */\n"
              "\tnop\n\tnop\n\tnop\n"
              "\tlui\t$11, 0x{en_hi:04X}\n"
              "{en_ori}",
        producer="\tmtc0\t$11, ${cp0}\t\t\t/* EPC = NEW -- the write under test */\n",
        consumer="\tmfc0\t$2, ${cp0}\n",
        tail="\tnop\n\tnop\n"
             "\tmfc0\t$11, ${cp0}\t\t\t/* control: EPC, settled */\n"),
    "movcond": dict(
        setup="",
        producer="\tlw\t$9, 0($10)\t\t\t/* the CONDITION register */\n",
        consumer="\t.word\t0x{movn:08X}\t\t/* movn $2,$8,$9 */\n",
        tail="\tnop\n\tnop\n"
             "\taddu\t$11, $9, $0\t\t/* control: $9, settled */\n"),
    "movrd": dict(
        setup="",
        producer="\tlw\t$2, 0($10)\t\t\t/* the DESTINATION register */\n",
        consumer="\t.word\t0x{movn:08X}\t\t/* movn $2,$8,$9 -- $9 is 0, so no move */\n",
        tail="\tnop\n\tnop\n"
             "\tlw\t$11, 0($10)\t\t/* control: the memory operand, again */\n"
             "\tnop\n\tnop\n"),
    "dslot": dict(
        setup="\tbeq\t$0, $0, .Lp5_{name}_tgt\t/* always taken */\n",
        producer="\tlw\t$9, 0($10)\t\t\t/* the load, IN the delay slot */\n",
        consumer="\taddu\t$2, $9, $0\n",
        tail="\tnop\n\tnop\n"
             "\taddu\t$11, $9, $0\t\t/* control: $9, settled */\n",
        # the branch target sits between the slot and the padding, so the
        # consumer is `dist` instructions past it
        target=True),
    "storeprod": dict(
        setup="",
        producer="\tsw\t$9, 0($10)\n",
        consumer="\tlw\t$2, 0($10)\n",
        tail="\tnop\n\tnop\n"
             "\tlw\t$11, 0($10)\t\t/* control: the same word, again */\n"
             "\tnop\n\tnop\n"),
    # The prime, with NO `mult`.  Reads LO into the row's word and HI into the
    # control, so one cell says `mtlo` works and `mthi` works.  The `hilo` family
    # cannot say either: `mult` overwrites both halves, so a prime that never
    # landed and a hazard that is closed produce the same capture.
    "hiloprime": dict(
        setup="\tlui\t$11, 0x{hi_hi:04X}\n"
              "{hi_ori}"
              "\tmthi\t$11\n\tnop\n\tnop\n"
              "\tlui\t$11, 0x{lo_hi:04X}\n"
              "{lo_ori}",
        producer="\tmtlo\t$11\t\t\t/* the prime, and NO mult follows it */\n",
        consumer="\tmflo\t$2\n",
        tail="\tnop\n\tnop\n"
             "\tmfhi\t$11\t\t\t/* control: HI still holds ITS prime */\n"),
}


def _ori(reg, val, label):
    """`lui` alone when the low half is zero.  `ori x,x,0` is a no-op and a
    no-op in generated code is a word a reader has to rule out."""
    lo = val & 0xFFFF
    if lo == 0:
        return ""
    return "\tori\t$%d, $%d, 0x%04X\t\t/* %s */\n" % (reg, reg, lo, label)


def gen_body(r):
    b = BODIES[r["family"]]
    o = dict(OFF)
    o.update(name=r["name"], movn=MOVN_W, cp0=CP0_EPC,
             lo_hi=PRIME_LO >> 16, hi_hi=PRIME_HI >> 16,
             eo_hi=EPC_OLD >> 16, en_hi=EPC_NEW >> 16,
             lo_ori=_ori(11, PRIME_LO, "PRIME_LO low half"),
             hi_ori=_ori(11, PRIME_HI, "PRIME_HI low half"),
             eo_ori=_ori(11, EPC_OLD, "EPC_OLD low half"),
             en_ori=_ori(11, EPC_NEW, "EPC_NEW low half"))
    out = []
    out.append(b["setup"].format(**o))
    out.append("\t.globl\trlx_p5_%s_p\nrlx_p5_%s_p:\n" % (r["name"], r["name"]))
    out.append(b["producer"].format(**o))
    if b.get("target"):
        out.append(".Lp5_%s_tgt:\n" % r["name"])
    for i in range(r["dist"]):
        out.append("\tnop\t\t\t\t/* padding %d of %d */\n" % (i + 1, r["dist"]))
    out.append("\t.globl\trlx_p5_%s_c\nrlx_p5_%s_c:\n" % (r["name"], r["name"]))
    out.append(b["consumer"].format(**o))
    out.append(b["tail"].format(**o))
    out.append("\tsw\t$11, %d($24)\n" % OFF["out_aux"])
    return "".join(out)


HEADER_S = """\
/* cells5.S -- GENERATED by tools/hazpay.py from tools/isa-hazard.tsv.
 *
 * DO NOT EDIT.  `hazpay.py emit --check` fails if this file and the table have
 * drifted, and `tools/test-hazpay.py` runs that check.
 *
 * `R1b`'s hazard ladder.  Every cell is a PRODUCER, `dist` `nop`s, and a
 * CONSUMER, and the rungs of one family differ by nothing but the padding --
 * which is what makes a ladder a single-variable experiment rather than a set
 * of tests.
 *
 * THE CELLS HERE CONTAIN THE HAZARDS `tools/hazlint` EXISTS TO REFUSE, ON
 * PURPOSE, AND THAT IS WHY THE BUILD GATE FOR THIS PAYLOAD RUNS THE OTHER WAY
 * ROUND.  `tools/hazdecl.py` runs the unmodified `hazlint` over the whole
 * linked image and then adjudicates its output in both directions: every
 * violation it reports must sit at a declared site, every declared site must
 * appear, no padded rung may appear at all, and `hazlint` exiting 0 is a BUILD
 * FAILURE -- a payload with no hazards has had them compiled away.  Nothing is
 * filtered and no address window is passed: the image is scanned whole.
 *
 * Register allocation, identical in every cell:
 *
 *     $8   input A       $9   input B      $10  memory operand base
 *     $2   result        $11  aux          $24  the scratch pointer
 *
 * $24 is never an operand of a probed sequence.  `aux` is always the per-row
 * CONTROL -- what the producer produced, read once the hazard has settled --
 * and never a row's reading, so *the hazard is open* and *the producer never
 * produced* cannot arrive as the same word.
 *
 * ⚠️ `movn` is emitted as a `.word`.  量 2026-09-13: `-march=mips1` rejects the
 * mnemonic outright ("opcode not supported on this processor"), which is the
 * same trap `docs/toolchain-prior-art.md` recorded for `madd` one segment
 * earlier.  An assembler's dictionary is not this core's instruction set.
 */
\t.set\tnoreorder
\t.set\tnoat
\t.set\tnomacro
#include "rlxasm.h"

\t.text
"""

HEADER_H = """\
/* probe5rows.h -- GENERATED by tools/hazpay.py from tools/isa-hazard.tsv.
 * DO NOT EDIT.
 *
 * The expected constants are NOT here.  `probe5` records eight words per row
 * and `hazpay.py verdict` decides at the desk, so there is nothing in the image
 * for a wrong expectation to be silently right against.
 */
#ifndef PROBE5ROWS_H
#define PROBE5ROWS_H

#define P5_ROWS\t\t{nrows}u
#define P5_ROW_WORDS\t{row_words}u
#define P5_TAG_BASE\t0x{tag:08X}u
#define P5_SCRATCH_B\t{scratch}u

/* Byte offsets inside the scratch block.  Offset {addr0} holds `&mem0` and is
 * written by the payload in C: the `storebase` family loads a base address out
 * of memory, and a cell that STORED it there first would itself be the
 * store-producer shape `tools/isa-hazard.tsv` declares not measurable. */
#define P5_O_ADDR0\t{addr0}u
#define P5_O_MEM0\t{mem0}u

struct p5_row {{
\tvoid (*cell)(void *);
\tu32 in_a;
\tu32 in_b;
\tu32 mem0;
\tu32 mem1;
\tu32 seed;
}};

{protos}
extern const struct p5_row p5_rows[P5_ROWS];
extern const char *const p5_names[P5_ROWS];

#endif
"""

HEADER_MK = """\
# probe5rows.mk -- GENERATED by tools/hazpay.py.  DO NOT EDIT.
P5_ROWS := {nrows}
RB_WORDS_probe5 := {rb}
"""


def rb_words(nrows):
    """33 + 8R, and 33 + 8R is 1 mod 4 for every R.

    `DW base n` returns 4*ceil(n/4) words (`LDR-07`), so a block whose length is
    a multiple of four returns no word past its own seal -- and that first word
    past is exactly where a payload that overran its block wrote.  `probe5.c`
    re-derives this as a compile-time assert so both copies move together.

    量 2026-09-13, by writing the case rather than by quoting: the property holds
    because **33 is odd**, so `33 + W*R` is odd for every EVEN `W` and every `R`
    and can never be a multiple of four.  It fails only for an odd `W`.  A
    reading of it as "8, 4 and 12 are safe and 6 and 10 are not" is wrong -- 6
    and 10 are safe for the same reason 8 is -- and the guard below is what makes
    the true statement testable instead of a comment.
    """
    n = 33 + ROW_WORDS * nrows
    if n % 4 == 0:
        raise Refuse("rb_words(%d) = %d is a multiple of four, so the read-back "
                     "cannot show poison past the seal" % (nrows, n))
    return n


def gen_asm(rows):
    out = [HEADER_S]
    for r in rows:
        o = dict(OFF)
        o["name"] = r["name"]
        out.append("\n\t.globl\trlx_p5_%s\n\t.ent\trlx_p5_%s\n"
                   "\t.type\trlx_p5_%s, @function\n"
                   "\t/* %s: %s */\nrlx_p5_%s:\n"
                   % (r["name"], r["name"], r["name"], r["name"], r["why"],
                      r["name"]))
        out.append(PROLOGUE.format(**o))
        out.append(gen_body(r))
        out.append(EPILOGUE.format(**o))
    return "".join(out)


def gen_header(rows):
    protos = "".join("void rlx_p5_%s(void *);\n" % r["name"] for r in rows)
    return HEADER_H.format(nrows=len(rows), row_words=ROW_WORDS,
                           tag=ROW_TAG_BASE, scratch=SCRATCH_BYTES,
                           addr0=OFF["addr0"], mem0=OFF["mem0"], protos=protos)


def gen_rows_c(rows):
    """The row table as its own translation unit, so the generated header holds
    declarations only and nothing in the build has two definitions of it."""
    out = ["/* probe5rows.c -- GENERATED by tools/hazpay.py from\n"
           " * tools/isa-hazard.tsv.  DO NOT EDIT.\n"
           " *\n"
           " * The operands are here and the EXPECTATIONS ARE NOT: `hazpay.py\n"
           " * verdict` holds those at the desk, so there is nothing in the\n"
           " * image for a wrong expectation to be silently right against.\n"
           " */\n"
           '#include "rlxprobe.h"\n'
           '#include "probe5rows.h"\n\n',
           "const struct p5_row p5_rows[P5_ROWS] = {\n"]
    for r in rows:
        out.append("\t{ rlx_p5_%s, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu },\n"
                   % (r["name"], r["in_a_v"], r["in_b_v"], r["mem0_v"],
                      r["mem1_v"], r["seed_v"]))
    out.append("};\n\nconst char *const p5_names[P5_ROWS] = {\n")
    for r in rows:
        out.append('\t"%s",\n' % r["name"])
    out.append("};\n")
    return "".join(out)


def write_if_changed(path, text, quiet=False):
    old = None
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", newline="") as f:
            old = f.read()
    if old == text:
        if not quiet:
            print("  unchanged  %s" % os.path.relpath(path, ROOT))
        return False
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)
    if not quiet:
        print("  wrote      %s" % os.path.relpath(path, ROOT))
    return True


# --------------------------------------------------------------------------
# the hazard-site declaration, which is what `hazdecl` consumes
# --------------------------------------------------------------------------

def site_symbols(rows):
    """{name: (producer symbol, consumer symbol, channel, dist)}"""
    return {r["name"]: ("rlx_p5_%s_p" % r["name"], "rlx_p5_%s_c" % r["name"],
                        r["haz"], r["dist"]) for r in rows}


def read_symbols(elf, nm=None):
    """Symbol -> address, out of the built artefact.  Refuses rather than
    returning an empty dict: an absent symbol table would make every check
    below pass by being blind."""
    nm = nm or os.environ.get("NM", "mips-linux-gnu-nm")
    try:
        p = subprocess.run([nm, elf], capture_output=True, text=True,
                           encoding="utf-8")
    except FileNotFoundError:
        raise Refuse("%s not on PATH -- the artefact's symbol table cannot be "
                     "read, and an absent check is not a passing check" % nm)
    if p.returncode != 0:
        raise Refuse("%s %s exited %d" % (nm, elf, p.returncode))
    syms = {}
    for line in p.stdout.split("\n"):
        f = line.split()
        if len(f) == 3:
            try:
                syms[f[2]] = int(f[0], 16)
            except ValueError:
                pass
    if not syms:
        raise Refuse("%s reported no symbols for %s" % (nm, elf))
    return syms


def check_distances(rows, syms):
    """The desk proof of `PROGRESS.md:122`: the distance in the BUILT ARTEFACT,
    not in the source.

    `addr(_c) - addr(_p)` must be `4 * (dist + 1)`.  If anything -- the
    assembler, a reorder pass, a hand edit -- put an instruction between the
    producer and its consumer, `_c` moved and this fires.  It holds for the
    `dslot` family too: the branch target sits between the slot and the padding,
    so the arithmetic is the same.
    """
    bad = []
    for r in rows:
        p, c = "rlx_p5_%s_p" % r["name"], "rlx_p5_%s_c" % r["name"]
        if p not in syms or c not in syms:
            bad.append((r["name"], None, None, "symbol missing from the artefact"))
            continue
        got = syms[c] - syms[p]
        want = 4 * (r["dist"] + 1)
        if got != want:
            bad.append((r["name"], got, want, "distance"))
    return bad


# --------------------------------------------------------------------------
# the desk verdict
# --------------------------------------------------------------------------

V_NORUN, V_TRAP, V_VOID = "NOT-RUN", "TRAPS", "VOID"
V_LOCK, V_OPEN, V_OTHER = "LOCK", "OPEN", "OTHER"

# The three verdicts that are NOT a reading of the hazard.  A rung with one
# of these did not answer the question; it failed to be asked.  Kept as one
# name because the ladder and the control recomputation must agree about
# which verdicts those are.
NOT_A_READING = (V_VOID, V_NORUN, V_TRAP)

ROW_RE = re.compile(r"^P5\s+([0-9a-fA-F]{8})\s+(\S+)"
                    r"((?:\s+[0-9a-fA-F]{8}){8})\s*$")


def exccode(cause):
    return (cause >> 2) & 0x1F


def verdict_row(r, rec):
    """rec = (tag, n, cause, epc, gpr, m0, m1, aux) -> (verdict, value, aux).

    The order is load-bearing and each step outranks the next for a reason:

      tag   a row that did not run cannot have a value at all;
      n     an exception explains every other word, so it outranks them;
      aux   if the producer never produced, the consumer's reading is about
            nothing -- VOID, not OPEN.  Without this a broken `mult` and an
            exposed `mflo` would arrive as the same verdict;
      value and only then is the reading a reading.
    """
    tag, n, cause, epc, gpr, m0, m1, aux = rec
    if tag != (ROW_TAG_BASE | r["idx"]):
        return V_NORUN, None, None
    val = {"gpr": gpr, "m0": m0, "m1": m1}[r["read"]]
    if n:
        return V_TRAP, val, aux
    if aux != r["ctl_v"]:
        return V_VOID, val, aux
    if val == r["lock_v"]:
        return V_LOCK, val, aux
    if val == r["open_v"]:
        return V_OPEN, val, aux
    return V_OTHER, val, aux


def read_rows(path, nrows):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        raise Refuse("cannot read %s: %s" % (path, e))
    recs, seen = [None] * nrows, 0
    for line in text.replace("\r", "\n").split("\n"):
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        idx = int(m.group(1), 16)
        words = tuple(int(w, 16) for w in m.group(3).split())
        if idx >= nrows:
            raise Refuse("capture has row index %d and the table has %d rows -- "
                         "this capture is not this payload's" % (idx, nrows))
        if recs[idx] is not None and recs[idx] != words:
            raise Refuse("row %d appears twice with different values" % idx)
        recs[idx] = words
        seen += 1
    if seen == 0:
        raise Refuse("no `P5 ` lines in %s. An empty capture and a capture of "
                     "absences are different answers" % path)
    return recs


def recompute_ctls(rows, recs):
    """The per-row control on EVERY row, recomputed from the capture.

    `tools/isa-hazard.tsv:60-63` declares a `ctl` for every row and not only
    for the two whose `kind` is `ctl`: *what `aux` must hold on BOTH arms.
    The family writes it after the hazard has settled, and it is what
    separates `the hazard is open` from `the producer never produced`.  A row
    whose ctl reading is wrong is VOID, not OPEN.*  `docs/isa-hazard.md`
    repeats it as a row of the control table.

    Until 2026-09-16 `check_controls` inspected the two `kind == "ctl"` rows
    and nothing else -- 2 of the 26 declared controls -- so the gate's own
    DoD sentence, *every hazard test's own control fires*, had no instrument
    behind it at all.  量: `bench/2026-09-14/C1-P5j.log` has three rows whose
    declared control did not fire, the verdict table prints that failure on
    all three rows, and the run reported zero findings and exit 0.

    THIS MUST NOT READ `verdict_row`'s ANSWER.  It takes the parsed records
    and the table and redoes the comparison, so that the two paths can be
    required to agree.  Gating on the VOID that `verdict_row` produces FROM
    this same comparison would be a check reading its own output, which is
    the defect being fixed one layer up and not a second source.

    Returns (state, fired, failed, norec).  `state` maps a row NAME to True
    (its control fired), False (it did not) or None (this row has no record
    of its own, so there is no aux word and the question does not arise).
    """
    state = {}
    for r in rows:
        rec = None
        if recs is not None and 0 <= r["idx"] < len(recs):
            rec = recs[r["idx"]]
        # The tag check is redone here for the same reason the ctl check is:
        # a record whose tag is not this row's is not this row's record, and
        # its aux word is about something else.
        if rec is None or rec[0] != (ROW_TAG_BASE | r["idx"]):
            state[r["name"]] = None
        else:
            state[r["name"]] = (rec[7] == r["ctl_v"])
    fired = [r for r in rows if state[r["name"]] is True]
    failed = [r for r in rows if state[r["name"]] is False]
    norec = [r for r in rows if state[r["name"]] is None]
    return state, fired, failed, norec


def ctl_line(rows, recs):
    """The counted line, printed beside the verdict tally.

    A zero is not printable here without its denominator: `0 did not` is
    worth nothing except beside `24 of 24 fired`, and the whole reason this
    line exists is that `check_controls` used to be able to report nothing
    about 24 declared controls without ever saying how many it had looked
    at.  The three counts are exhaustive and sum to the row count.
    """
    _st, fired, failed, norec = recompute_ctls(rows, recs)
    byfam = {}
    for r in failed:
        byfam.setdefault(r["family"], []).append(r["name"])
    parts = ["per-row controls: %d of %d fired" % (len(fired), len(rows))]
    if failed:
        parts.append("%d did not (%s)" % (len(failed), "; ".join(
            "%s: %s" % (fam, ", ".join(byfam[fam])) for fam in sorted(byfam))))
    else:
        parts.append("0 did not")
    if norec:
        parts.append("%d with no record (%s)"
                     % (len(norec), ", ".join(r["name"] for r in norec)))
    return ", ".join(parts)


def check_controls(rows, out, arm, recs):
    """The controls, and the two that are two-sided.

    Returns a list of findings.  A finding here is not a row's reading being
    surprising -- that is what the reading is for -- it is the table or the
    instrument being unable to support any reading at all.
    """
    f = []
    ctls = [(r, v) for r, v, _val, _a in out if r["kind"] == "ctl"]
    if not ctls:
        f.append("NO CONTROL ROW. The table has nothing that says the payload "
                 "can read its own observables, so no other row's reading is "
                 "worth anything")
    for r, v in ctls:
        if v != V_LOCK:
            f.append("CONTROL %s read %s, not LOCK -- the payload cannot see "
                     "its own memory observable and the table is VOID"
                     % (r["name"], v))

    # --- the per-row control, on every row, by a second path --------------
    #
    # TWO findings and no more, and the line between them is this function's
    # own docstring.  A row whose declared control did not fire is VOID, and
    # ONE VOID row is a legal outcome -- `PROGRESS.md` `D3`'s *not
    # measurable* carrying its reason.  Making that a finding would turn a
    # correct VOID into a failure, so it is COUNTED instead (`ctl_line`,
    # printed beside the tally) and only these two shapes are findings:
    #
    #   the two paths DISAGREE   the instrument contradicting itself, which
    #                            is reachable the moment `verdict_row` is
    #                            edited -- and a check that cannot become
    #                            reachable is a check that cannot fail;
    #   EVERY control failed     not one row read its own observable, so no
    #                            row's reading is about anything.
    state, fired, failed, _norec = recompute_ctls(rows, recs)
    for r, v, _val, _a in out:
        st = state.get(r["name"])
        if st is None or v in (V_TRAP, V_NORUN):
            # `verdict_row` puts the tag and the exception ABOVE the control
            # ON PURPOSE and `H27` pins that ordering, so a trapped row whose
            # ctl is also wrong reading TRAPS is the documented answer and
            # not a disagreement.  Excluding them here is what keeps this
            # check from firing on a legal outcome.
            continue
        aux = recs[r["idx"]][7]
        if st is False and v != V_VOID:
            f.append("INCOHERENT %s: recomputed from the capture its aux word "
                     "is 0x%08X against a declared ctl of 0x%08X, so this row "
                     "cannot be read -- and the verdict is %s, not VOID. Two "
                     "paths over one capture disagree and one of them is "
                     "broken. A single VOID row is not a finding; this is"
                     % (r["name"], aux, r["ctl_v"], v))
        elif st is True and v == V_VOID:
            f.append("INCOHERENT %s: the verdict is VOID and the aux word "
                     "recomputed from the capture is 0x%08X, which IS the "
                     "declared ctl. `verdict_row` has exactly one route to "
                     "VOID and this capture does not show it"
                     % (r["name"], aux))
    evaluated = len(fired) + len(failed)
    if evaluated and not fired:
        f.append("EVERY per-row control failed -- %d of the %d row(s) with a "
                 "record, and not one aux word matched its `ctl` column. The "
                 "payload is not reading its own observables at all, so no "
                 "row's reading here is about anything. One such row is VOID "
                 "and legal; all of them is the table unable to support any "
                 "reading" % (len(failed), evaluated))

    # C4.  `plan:1074` calls this the only failure that can make the table
    # rubbish, which is why it is mandatory.
    if arm == "qemu":
        for r, v, val, _a in out:
            if v != V_LOCK:
                f.append("C4: %s read %s under qemu and every row must read "
                         "LOCK. qemu interlocks the load delay slot (F46), so "
                         "a row that reads anything else here has not measured "
                         "a hazard -- it has measured the harness. That row is "
                         "VOID%s" % (r["name"], v,
                                     "" if val is None else " (value 0x%08X)" % val))

    # The `storebase` pair.  Exactly one of the two candidate addresses can have
    # been written, so the two rows over one cell shape must reach the same
    # verdict.  They disagree only if the store went nowhere, or somewhere the
    # containment argument says it cannot.
    for d in sorted({r["dist"] for r, _v, _val, _a in out
                     if r["family"] == "storebase"}):
        pair = [(r, v) for r, v, _val, _a in out
                if r["family"] == "storebase" and r["dist"] == d]
        if len(pair) == 2 and pair[0][1] != pair[1][1]:
            f.append("storebase pair at dist %d disagrees: %s read %s and %s "
                     "read %s. Exactly one address can have been written, so "
                     "the family is VOID at this rung"
                     % (d, pair[0][0]["name"], pair[0][1],
                        pair[1][0]["name"], pair[1][1]))
    return f


def ladder_depth(rungs):
    """One family's depth sentence.  `rungs` is [(dist, verdict), ...].

    VOID IS NOT OPEN.  Until 2026-09-16 this read "open at every rung" whenever
    no rung read LOCK, so an all-VOID family -- one whose own per-row control
    did not fire, i.e. one that could not be measured at all -- printed the
    sentence a reader takes as *the hazard is exposed at every distance*.  量:
    the `cp0` family on `bench/2026-09-14/C1-P5j.log` printed exactly that, on
    the same run whose verdict table said `ctl read 0x80500270, want 0x5A5A5A50`
    three lines above.  TRAPS and NOT-RUN are the same class -- the absence of a
    reading rather than a reading of OPEN -- and `NOT_A_READING` is the one name
    for all three.

    THE PARTLY-UNMEASURED WORDINGS ARE DELIBERATE and are why this is three
    branches and not two.  A ladder with a hole in it can still show a depth,
    but that depth is a claim about the rungs that WERE read, so the count of
    the ones that were not is printed beside it: `closes at d1` with d0 VOID
    must not be read as *d0 is open*, which is the same mistake one rung down.

    The two healthy strings are unchanged on purpose.  A capture in which every
    rung is a reading prints exactly what it printed before, so this fix moves
    no reading and no number -- it is a rendering fix and nothing else.

    IT IS A FUNCTION because the two partly-unmeasured branches are not
    reachable from any committed capture (every family in the device capture is
    either wholly read or wholly VOID), and a branch no case can exercise is a
    rendering rule nobody has shown to work.  `H36` calls this directly.
    """
    closed = [d for d, v in rungs if v == V_LOCK]
    unread = [(d, v) for d, v in rungs if v in NOT_A_READING]
    nvoid = sum(1 for _d, v in rungs if v == V_VOID)
    if len(unread) == len(rungs):
        return ("not measurable at any rung (see the ctl column)"
                if nvoid == len(rungs) else
                "not measurable at any rung (%d VOID, %d other)"
                % (nvoid, len(rungs) - nvoid))
    if closed:
        return ("closes at d%d" % min(closed)) + (
            "" if not unread else
            " -- but %d of %d rung(s) not measurable"
            % (len(unread), len(rungs)))
    return ("open at every rung" if not unread else
            "open at every MEASURED rung (%d of %d not measurable)"
            % (len(unread), len(rungs)))


def cmd_verdict(rows, path, arm, quiet=False):
    recs = read_rows(path, len(rows))
    out = []
    for r in rows:
        rec = recs[r["idx"]]
        if rec is None:
            out.append((r, V_NORUN, None, None))
        else:
            v, val, aux = verdict_row(r, rec)
            out.append((r, v, val, aux))

    print("verdict (%s arm): %s" % (arm, os.path.relpath(path, ROOT)))
    print("")
    print("  %-10s %-10s %-4s %-8s %-10s %-10s %-10s %s"
          % ("row", "family", "d", "verdict", "value", "lock", "open", "note"))
    tally, mispred = {}, []
    for r, v, val, aux in out:
        tally[v] = tally.get(v, 0) + 1
        note = ""
        rec = recs[r["idx"]]
        if v == V_TRAP and rec:
            note = "ExcCode %d" % exccode(rec[2])
        elif v == V_VOID:
            note = "ctl read 0x%08X, want 0x%08X" % (aux, r["ctl_v"])
        elif v == V_OTHER:
            note = "neither constant -- open, and not by the prior value"
        if arm == "device" and r["dev"] != "-":
            want = V_LOCK if r["dev"] == "lock" else V_OPEN
            if v != want:
                mispred.append((r, v, want))
                note = (note + "  " if note else "") + "PRE-REGISTERED %s" % want
        print("  %-10s %-10s %-4d %-8s %-10s %-10s %-10s %s"
              % (r["name"], r["family"], r["dist"], v,
                 "-" if val is None else "%08X" % val,
                 "%08X" % r["lock_v"], "%08X" % r["open_v"], note))
    print("")
    print("  %d row(s), %s" % (len(out), ", ".join(
        "%s %d" % (k, tally[k]) for k in sorted(tally))))
    print("  %s" % ctl_line(rows, recs))

    findings = check_controls(rows, out, arm, recs)

    # The ladder, which is the result rather than a check.  Printed because a
    # table of per-row verdicts is not yet an answer to "how deep".
    print("")
    print("  the ladder (%s arm) -- the distance at which each family closes:" % arm)
    for fam in FAMILIES:
        rungs = sorted([(r["dist"], v) for r, v, _val, _a in out
                        if r["family"] == fam])
        if not rungs:
            continue
        shape = " ".join("d%d=%s" % (d, v) for d, v in rungs)
        print("    %-10s %-44s %s" % (fam, shape, ladder_depth(rungs)))

    if mispred:
        print("")
        print("  pre-registered DEVICE predictions refuted: %d" % len(mispred))
        for r, v, want in mispred:
            print("    %-10s predicted %s, read %s" % (r["name"], want, v))
            print("      %s" % r["why"][:150])
        findings.extend("PRE-REGISTERED %s for %s read %s -- registered before "
                        "the board was powered, so this is a refutation and "
                        "not an error" % (want, r["name"], v)
                        for r, v, want in mispred)

    if findings:
        print("")
        for x in findings:
            print("  FINDING  %s" % x)
    return 1 if findings else 0


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------

def cmd_population(rows, quiet=False):
    bad = 0
    print("population: %d row(s), %d famil(ies)"
          % (len(rows), len({r["family"] for r in rows})))
    print("")
    for fam in FAMILIES:
        rr = [r for r in rows if r["family"] == fam]
        if not rr:
            print("  EMPTY    %s -- a family with no rung is a hazard nobody "
                  "probes" % fam)
            bad += 1
            continue
        print("  %-10s %d rung(s): %s" % (fam, len(rr),
              " ".join("d%d" % r["dist"] for r in sorted(rr, key=lambda x: x["dist"]))))
    extra = {r["family"] for r in rows} - set(FAMILIES)
    for fam in sorted(extra):
        print("  UNKNOWN  %s" % fam)
        bad += 1

    # The join against the prior-art census, in both directions.  A key that
    # stops matching is a join that silently found nothing, which is worse than
    # a mismatch, so it is a refusal.
    try:
        with open(os.path.join(ROOT, "docs", "isa-prior-art.md"), "r",
                  encoding="utf-8") as f:
            art = f.read()
    except OSError:
        print("")
        print("  SKIP     docs/isa-prior-art.md not readable -- the census "
              "join did not run, and it is named rather than assumed")
        return 1 if bad else 0
    seg = art.split("isacensus:r1b begin")
    seg = seg[1].split("isacensus:r1b end")[0] if len(seg) > 1 else ""
    print("")
    print("  census join (docs/isa-prior-art.md § 4), both directions:")
    for fam in FAMILIES:
        key = CENSUS_KEY[fam]
        if key is None:
            print("    %-10s -> CONTROL, no census row by design: the census "
                  "excludes what obviously works, and what it excludes is "
                  "exactly a payload's positive control" % fam)
            continue
        if key not in seg:
            raise Refuse("family %s joins the census on %r and that string is "
                         "no longer in § 4's block. A join that finds nothing "
                         "is worse than a mismatch" % (fam, key))
        print("    %-10s -> %s" % (fam, key))
    rowlines = [l for l in seg.split("\n")
                if l.strip().startswith("| `") and "---" not in l]
    matched = set()
    for l in rowlines:
        label = l.split("|")[1].strip().strip("`")
        for fam, key in CENSUS_KEY.items():
            if key is not None and key in label:
                matched.add(label)
    unmatched = [l.split("|")[1].strip().strip("`") for l in rowlines
                 if l.split("|")[1].strip().strip("`") not in matched]
    if unmatched:
        print("    CENSUS ROWS WITH NO FAMILY (%d):" % len(unmatched))
        for u in unmatched:
            print("      %s" % u)
        bad += 1
    else:
        print("    every § 4 row has at least one family (%d row(s))"
              % len(rowlines))
    return 1 if bad else 0


def cmd_model(rows, quiet=False):
    """`quiet` suppresses the per-row lines and nothing else: a DIFFER and the
    one-source list are always printed, because a mode that can be told to hide
    its findings is a mode whose green means nothing."""
    bad, nomodel = 0, []
    if not quiet:
        print("model: two sources for lock, open and ctl")
        print("")
    for r in rows:
        lock, open_, ctl = model_row(r)
        if lock is None:
            nomodel.append(r["name"])
            continue
        ok = (lock == r["lock_v"] and open_ == r["open_v"] and ctl == r["ctl_v"])
        if not ok:
            bad += 1
        if not quiet or not ok:
            print("  %-10s hand %08X/%08X/%08X  model %08X/%08X/%08X  %s"
                  % (r["name"], r["lock_v"], r["open_v"], r["ctl_v"],
                     lock, open_, ctl, "ok" if ok else "DIFFER"))
    if nomodel:
        print("  ONE SOURCE ONLY (%d): %s" % (len(nomodel), " ".join(nomodel)))
        print("  Naming them is the point. A count alone lets the fact that a "
              "row has one source sit in a number nobody reads.")
        bad += len(nomodel)
    if not quiet:
        print("")
        print("  ⚠️ The `open` halves are NOT two independent beliefs. Both "
              "sources encode the same hypothesis -- that the consumer sees the "
              "prior value -- so what is checked twice is the arithmetic, not "
              "the hypothesis. MIPS-I says UNPREDICTABLE; `docs/isa-hazard.md` "
              "§ 3 carries this and marks the column 推.")
    return 1 if bad else 0


def cmd_emit(rows, check=False, quiet=False):
    want = {CELLS_S: gen_asm(rows), ROWS_H: gen_header(rows),
            ROWS_MK: HEADER_MK.format(nrows=len(rows), rb=rb_words(len(rows))),
            os.path.join(HERE, "rlxprobe", "probe5rows.c"): gen_rows_c(rows)}
    if check:
        stale = []
        for p, t in want.items():
            cur = None
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8", newline="") as f:
                    cur = f.read()
            if cur != t:
                stale.append(os.path.relpath(p, ROOT))
        if stale:
            print("emit --check: STALE -- %s differ(s) from the table"
                  % ", ".join(stale))
            return 1
        print("emit --check: %d generated file(s) match the table" % len(want))
        return 0
    print("emit: %d row(s) -> %d file(s)" % (len(rows), len(want)))
    for p, t in want.items():
        write_if_changed(p, t, quiet)
    print("  RB_WORDS_probe5 = %d  (33 + %d*%d, and %d mod 4 = %d)"
          % (rb_words(len(rows)), ROW_WORDS, len(rows),
             rb_words(len(rows)), rb_words(len(rows)) % 4))
    return 0


DIS_RE = re.compile(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)$")


def cmd_verify(rows, elf, objdump=None, quiet=False, strict=False):
    """The artefact, and the two claims it can settle that the source cannot.

    ① every row's producer and consumer are the words the template wrote, and
    ② `addr(_c) - addr(_p)` is `4 * (dist + 1)`.

    ② is the one `PROGRESS.md:122` asks for.  ① is weaker here than it is for
    `probe4`, because a hazard row's instructions are ordinary MIPS-I that any
    assembler encodes correctly -- the one exception is `movn`, which is a
    `.word` precisely because the assembler refuses the mnemonic.
    """
    if not elf:
        raise Refuse("verify needs an ELF")
    if not os.path.isfile(elf):
        raise Refuse("%s: no such file" % elf)
    objdump = objdump or os.environ.get("OBJDUMP", "mips-linux-gnu-objdump")
    syms = read_symbols(elf)
    bad = 0

    print("verify: %s" % os.path.relpath(elf, ROOT))
    print("")
    dbad = check_distances(rows, syms)
    for name, got, want, why in dbad:
        if why == "distance":
            print("  FAIL     %-10s addr(_c) - addr(_p) = %d, the table says "
                  "dist %s so it must be %d. An instruction was inserted "
                  "between the producer and its consumer, which is exactly the "
                  "risk this check exists for"
                  % (name, got, (want // 4) - 1, want))
        else:
            print("  FAIL     %-10s %s" % (name, why))
        bad += 1
    if not dbad:
        print("  ok       %d distance(s) read out of the artefact's symbol "
              "table, every one 4*(dist+1)" % len(rows))

    try:
        p = subprocess.run([objdump, "-d", "-m", "mips:3000", elf],
                           capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError:
        raise Refuse("%s not on PATH -- source 3 cannot run, and an absent "
                     "check is not a passing check" % objdump)
    if p.returncode != 0:
        raise Refuse("%s exited %d" % (objdump, p.returncode))
    at = {}
    for line in p.stdout.split("\n"):
        m = DIS_RE.match(line)
        if m:
            at[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())

    # the one encoding the assembler will not write, checked by the word
    for r in rows:
        if r["family"] not in ("movcond", "movrd"):
            continue
        a = syms.get("rlx_p5_%s_c" % r["name"])
        if a is None or a not in at:
            print("  FAIL     %-10s consumer not in the disassembly" % r["name"])
            bad += 1
            continue
        got = int(at[a][0], 16)
        if got != MOVN_W:
            print("  FAIL     %-10s consumer is 0x%08X, the template wrote "
                  "0x%08X" % (r["name"], got, MOVN_W))
            bad += 1
        else:
            print("  ok       %-10s consumer 0x%08X, decoded as %r at "
                  "mips:3000" % (r["name"], got, at[a][1]))

    if strict:
        print("")
        print("  ⚠️ --strict has NOTHING TO SAY about this payload, and that is "
              "stated rather than left to be found. `isapay`'s converse check "
              "asks whether a non-MIPS-I word sits outside a declared probe "
              "site; every encoding here is ordinary MIPS-I, so "
              "`hazlint --isa` reports zero hits and zero strays. A clean "
              "result there is passing by being blind. The check that has teeth "
              "for probe5 is `tools/hazdecl.py`.")
    return 1 if bad else 0


def cmd_sites(rows, elf=None):
    """What `hazdecl` consumes.  Printed as well as importable, so a reader can
    see the declaration the gate is checking against."""
    syms = read_symbols(elf) if elf else None
    print("sites: %d row(s)" % len(rows))
    print("")
    print("  %-10s %-6s %-4s %-12s %-12s %s"
          % ("row", "chan", "d", "producer", "consumer", "addresses"))
    for r in rows:
        p, c = "rlx_p5_%s_p" % r["name"], "rlx_p5_%s_c" % r["name"]
        addr = ""
        if syms:
            addr = "0x%08X -> 0x%08X" % (syms.get(p, 0), syms.get(c, 0))
        print("  %-10s %-6s %-4d %-12s %-12s %s"
              % (r["name"], r["haz"], r["dist"], p, c, addr))
    print("")
    for ch in CHANNELS:
        nn = [r["name"] for r in rows if r["haz"] == ch]
        print("  %-6s %2d: %s" % (ch, len(nn), " ".join(nn) if nn else "-"))
    return 0


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def self_test():
    import tempfile
    ok = n = 0
    fails = []

    def case(label, fn):
        nonlocal ok, n
        n += 1
        try:
            fn()
            ok += 1
            print("  ok    %s" % label)
        except AssertionError as e:
            fails.append(label)
            print("  FAIL  %s -- %s" % (label, e))
        except Exception as e:                  # noqa: BLE001
            fails.append(label)
            print("  FAIL  %s -- %s: %s" % (label, type(e).__name__, e))

    def refuses(fn, why):
        try:
            fn()
        except Refuse:
            return
        raise AssertionError("did not refuse: %s" % why)

    print("hazpay self-test")
    print("")

    live = None
    try:
        live = load_rows()
    except Refuse as e:
        print("  REFUSING: the committed table does not parse (%s). Every case "
              "below would be measured against a broken table." % e)
        return 3
    if cmd_model(live, quiet=True) != 0:
        print("  REFUSING: the committed table already fails `model`.")
        return 3
    print("")

    hdr = "\t".join(COLUMNS)
    FIX = ("loaduse\tadd_x\t0\thaz\t0x12345678\t0xB10CB10C\t0xA5A5F00D\t"
           "0x5A5A0FF2\t0xDEADBEEF\tgpr\t0xA5A5F00D\t0xB10CB10C\t0xA5A5F00D\t"
           "main\tlock\t-\twhy")

    def mk(body):
        fd, p = tempfile.mkstemp(suffix=".tsv", text=True)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("# fixture\n" + hdr + "\n" + body + "\n")
        return p

    def sub(field, value, base=FIX):
        f = base.split("\t")
        f[COLUMNS.index(field)] = value
        return "\t".join(f)

    case("H0  the fixture itself parses", lambda: load_rows(mk(FIX)))
    case("H1  a duplicate name refuses",
         lambda: refuses(lambda: load_rows(mk(FIX + "\n" + FIX)), "dup name"))
    case("H2  an unknown family refuses",
         lambda: refuses(lambda: load_rows(mk(sub("family", "nope"))), "family"))
    case("H3  a short row refuses",
         lambda: refuses(lambda: load_rows(mk("a\tb\tc")), "short"))
    case("H4  a pipe refuses (spec-check C8)",
         lambda: refuses(lambda: load_rows(mk(sub("why", "a | b"))), "pipe"))
    case("H5  read=aux refuses -- aux belongs to the control",
         lambda: refuses(lambda: load_rows(mk(sub("read", "aux"))), "read"))
    case("H6  qemu != lock refuses -- C4 is mandatory",
         lambda: refuses(lambda: load_rows(mk(sub("qemu", "open"))), "qemu"))
    case("H7  an unknown haz channel refuses",
         lambda: refuses(lambda: load_rows(mk(sub("haz", "maybe"))), "haz"))

    # the collapse rule and its opposite sign
    case("H8  kind=haz with lock == open REFUSES (the T_JR defect as a table)",
         lambda: refuses(lambda: load_rows(mk(sub("open", "0xA5A5F00D"))),
                         "collapse"))
    case("H9  kind=ctl with lock != open REFUSES (the same rule, other sign)",
         lambda: refuses(lambda: load_rows(
             mk(sub("haz", "none", sub("kind", "ctl")))), "ctl differ"))

    def h10():
        body = sub("haz", "none",
                   sub("open", "0xA5A5F00D", sub("kind", "ctl")))
        body = body.split("\t")
        body[COLUMNS.index("family")] = "storeprod"
        body[COLUMNS.index("read")] = "m0"
        body[COLUMNS.index("lock")] = "0xB10CB10C"
        body[COLUMNS.index("open")] = "0xB10CB10C"
        body[COLUMNS.index("ctl")] = "0xB10CB10C"
        rr = load_rows(mk("\t".join(body)))
        assert rr[0]["kind"] == "ctl"
    case("H10 kind=ctl with lock == open parses", h10)

    case("H11 dist>0 with a declared haz channel refuses",
         lambda: refuses(lambda: load_rows(mk(sub("dist", "1"))), "padded rung"))

    def h11b():
        body = sub("haz", "none", sub("dist", "1"))
        rr = load_rows(mk(body))
        assert rr[0]["dist"] == 1 and rr[0]["haz"] == "none"
    case("H11b dist>0 with haz=none parses", h11b)

    case("H12 dist=0 haz row with haz=none refuses",
         lambda: refuses(lambda: load_rows(mk(sub("haz", "none"))), "no site"))
    case("H12b ctl = 0 refuses -- it is probe5's own sentinel",
         lambda: refuses(lambda: load_rows(mk(sub("ctl", "0x00000000"))),
                         "ctl sentinel"))

    # the family preconditions -- the DoD's "able to produce the wrong answer"
    case("H13 loaduse with mem0 == in_b refuses",
         lambda: refuses(lambda: load_rows(mk(sub("mem0", "0xB10CB10C"))),
                         "loaduse precondition"))

    def mkfam(fam, **over):
        f = FIX.split("\t")
        f[COLUMNS.index("family")] = fam
        for k, v in over.items():
            f[COLUMNS.index(k)] = v
        return "\t".join(f)

    case("H14 movcond with a non-zero in_b refuses",
         lambda: refuses(lambda: load_rows(mk(mkfam(
             "movcond", name="mc_x", lock="0x12345678", open="0xDEADBEEF",
             ctl="0xA5A5F00D"))), "movcond needs in_b == 0"))

    def h15():
        rr = load_rows(mk(mkfam("movcond", name="mc_x", in_b="0x00000000",
                                lock="0x12345678", open="0xDEADBEEF",
                                ctl="0xA5A5F00D")))
        assert rr[0]["family"] == "movcond"
    case("H15 movcond with in_b == 0 parses", h15)

    case("H16 movrd with a non-zero in_b refuses",
         lambda: refuses(lambda: load_rows(mk(mkfam(
             "movrd", name="mr_x", lock="0xA5A5F00D", open="0xDEADBEEF",
             ctl="0xA5A5F00D"))), "movrd needs in_b == 0"))

    case("H17 storebase with in_b == mem1 refuses",
         lambda: refuses(lambda: load_rows(mk(mkfam(
             "storebase", name="sb_x", read="m1", in_b="0x5A5A0FF2",
             lock="0x5A5A0FF2", open="0x11112222", ctl="0x5A5A0FF2"))),
             "storebase precondition"))

    # source 1 against source 2.
    #
    # 🔴 The first draft of H18 used the fixture's own name, `add_x`, which is
    # NOT in `MODELS` -- so `model_row` returned None, the assertion was
    # `lock is None or ...`, and the case could not fail.  It is rewritten to
    # use a name the model knows and to score the verb's exit code, which is
    # what a caller actually reads.
    def h18():
        f = FIX.split("\t")
        f[COLUMNS.index("name")] = "lu_alu_d0"
        good = load_rows(mk("\t".join(f)))
        assert cmd_model(good, quiet=True) == 0, "the healthy arm must be clean"
        f[COLUMNS.index("lock")] = "0xA5A5F00E"     # one bit
        bad = load_rows(mk("\t".join(f)))
        assert cmd_model(bad, quiet=True) == 1, \
            "a one-bit wrong `lock` must be a finding"
        f[COLUMNS.index("lock")] = "0xA5A5F00D"
        f[COLUMNS.index("ctl")] = "0xA5A5F00E"
        bad2 = load_rows(mk("\t".join(f)))
        assert cmd_model(bad2, quiet=True) == 1, \
            "a one-bit wrong `ctl` must be a finding too"
    case("H18 a one-bit wrong lock or ctl is a finding, and the healthy arm is "
         "clean", h18)

    def h18b():
        """The other half: a row the model does not know must be NAMED and must
        make the verb non-zero, not pass quietly."""
        f = FIX.split("\t")
        f[COLUMNS.index("name")] = "no_such_row"
        rr = load_rows(mk("\t".join(f)))
        assert model_row(rr[0]) == (None, None, None)
        assert cmd_model(rr, quiet=True) == 1, \
            "a one-source row must not pass quietly"
    case("H18b a row with no model is a finding, not a silence", h18b)

    def h19():
        r = dict(live[0])
        r["lock_v"] = r["lock_v"] ^ 1
        lock, _o, _c = model_row(r)
        assert lock != r["lock_v"], "model must not read the lock column"
    case("H19 the model does not read the `lock` column", h19)

    def h20():
        r = dict(live[0])
        r["read"] = "m1" if r["read"] != "m1" else "gpr"
        refuses(lambda: model_row(r), "model/read mismatch")
    case("H20 a model that produces another word REFUSES", h20)

    # the generator
    def h21():
        a, b = gen_asm(live), gen_asm(live)
        assert a == b, "not deterministic"
        assert ".set\tnoreorder" in a
        assert "rlx_p5_%s_p:" % live[0]["name"] in a
        assert "rlx_p5_%s_c:" % live[0]["name"] in a
    case("H21 generation is deterministic and emits both site symbols", h21)

    def h22():
        """THE GENERATOR-SIDE TWIN OF `hazdecl`'s DISTANCE CHECK, and it runs
        with no cross-compiler.  Count the emitted instruction lines between
        `_p` and `_c`; there must be exactly `dist` of them, all `nop`."""
        text = gen_asm(live)
        for r in live:
            p = text.index("rlx_p5_%s_p:\n" % r["name"])
            c = text.index("rlx_p5_%s_c:\n" % r["name"])
            assert c > p, r["name"]
            between = text[p:c].split("\n")[1:-1]
            instrs = [l for l in between
                      if l.startswith("\t") and not l.lstrip().startswith(".globl")]
            body = [l for l in instrs if not l.lstrip().startswith(".Lp5")]
            # one producer, then `dist` nops
            assert len(body) == 1 + r["dist"], \
                "%s: %d instruction(s) between the symbols, want %d" \
                % (r["name"], len(body), 1 + r["dist"])
            for l in body[1:]:
                assert l.strip().startswith("nop"), \
                    "%s: the padding is %r and must be nop" % (r["name"], l)
    case("H22 the emitted distance is dist+1 for every row", h22)

    def h23():
        """The inverse of `isapay`'s T13, and it must be the inverse rather than
        deleted: a d0 rung's consumer MUST read the producer's destination and
        a padded rung's must not do so at distance zero."""
        text = gen_asm(live)
        for r in live:
            if r["family"] not in ("loaduse", "storedata", "dslot"):
                continue
            p = text.index("rlx_p5_%s_p:\n" % r["name"])
            c = text.index("rlx_p5_%s_c:\n" % r["name"])
            seg = text[p:c]
            assert "lw\t$9" in seg or "lw\t$2" in seg or "lw\t$10" in seg, \
                "%s: no load at the producer" % r["name"]
            pad = seg.count("nop")
            assert pad == r["dist"], \
                "%s: %d nop(s) of padding, want %d" % (r["name"], pad, r["dist"])
    case("H23 a d0 rung has no padding and a padded rung has exactly dist", h23)

    def h24():
        assert set(BODIES) == set(FAMILIES), \
            "BODIES %r != FAMILIES %r" % (sorted(BODIES), sorted(FAMILIES))
        assert set(CENSUS_KEY) == set(FAMILIES)
    case("H24 every family has a body and a census key (isapay's `nx` landmine)",
         h24)

    def h24b():
        """`derived_channel`, pinned pair by pair.

        🔴 This case exists because the first draft got TWO things wrong and
        `tools/hazdecl.py` caught them on its first real build rather than a case
        here: `dslot` is in the survey at EVERY rung (the load is in a delay slot
        whatever the padding), and `main` needs the producer to BE a load, which
        `hilo` and `cp0` are not.  A rule that was wrong twice needs a table of
        answers, not a sentence."""
        want = {
            ("loaduse", 0): "main", ("loaduse", 1): "none", ("loaduse", 2): "none",
            ("storedata", 0): "main", ("storedata", 1): "none",
            ("storebase", 0): "main", ("storebase", 1): "none",
            ("movcond", 0): "main", ("movcond", 1): "none",
            ("movrd", 0): "main", ("movrd", 1): "none",
            ("dslot", 0): "both", ("dslot", 1): "survey", ("dslot", 2): "survey",
            ("hilo", 0): "survey", ("hilo", 1): "none", ("hilo", 3): "none",
            ("cp0", 0): "survey", ("cp0", 2): "none",
            ("storeprod", 0): "none",
        }
        for (fam, d), w in sorted(want.items()):
            got = derived_channel(fam, d, "haz")
            assert got == w, "%s d%d -> %s, want %s" % (fam, d, got, w)
        # and every `ctl` row is `none` whatever its family
        for fam in FAMILIES:
            assert derived_channel(fam, 0, "ctl") == "none", fam
        # the live table agrees with the derivation, row by row
        for r in live:
            assert r["haz"] == derived_channel(r["family"], r["dist"], r["kind"]), \
                r["name"]
    case("H24b derived_channel is pinned pair by pair, both wrong rules included",
         h24b)

    def h25():
        """量, not quoted: 33 is odd, so `33 + W*R` is odd for every EVEN `W`.
        An odd `W` is what breaks it, and the guard has to refuse there.  Written
        this way because the first draft of this case asserted that `W = 6`
        breaks the property, which is false -- 6 is safe for exactly the reason 8
        is."""
        for k in range(0, 64):
            assert rb_words(k) % 4 == 1, k
        saved = globals()["ROW_WORDS"]
        try:
            for even in (2, 4, 6, 8, 10, 12):
                globals()["ROW_WORDS"] = even
                for k in range(0, 8):
                    assert rb_words(k) % 4 != 0, (even, k)
            globals()["ROW_WORDS"] = 3      # odd: 33 + 3*1 = 36
            refuses(lambda: rb_words(1), "an odd ROW_WORDS breaks the property")
        finally:
            globals()["ROW_WORDS"] = saved
        assert rb_words(len(live)) % 4 == 1
    case("H25 rb_words: every even ROW_WORDS is safe, an odd one refuses", h25)

    # the verdict
    def h26():
        r = live[0]
        base = [ROW_TAG_BASE | r["idx"], 0, 0, 0, 0, 0, 0, r["ctl_v"]]
        i = {"gpr": 4, "m0": 5, "m1": 6}[r["read"]]

        w = list(base); w[i] = r["lock_v"]
        assert verdict_row(r, tuple(w))[0] == V_LOCK
        w = list(base); w[i] = r["open_v"]
        assert verdict_row(r, tuple(w))[0] == V_OPEN
        w = list(base); w[i] = 0x0BADF00D
        assert verdict_row(r, tuple(w))[0] == V_OTHER
        w = list(base); w[i] = r["lock_v"]; w[1] = 1; w[2] = 0x28
        assert verdict_row(r, tuple(w))[0] == V_TRAP
        w = list(base); w[i] = r["lock_v"]; w[7] = r["ctl_v"] ^ 1
        assert verdict_row(r, tuple(w))[0] == V_VOID
        w = list(base); w[0] = 0
        assert verdict_row(r, tuple(w))[0] == V_NORUN
        assert exccode(0x28) == 10
    case("H26 all six verdict cells are reachable", h26)

    def h27():
        """A trap outranks a bad control, and a bad control outranks the value.
        Both orderings are load-bearing and neither is obvious."""
        r = live[0]
        i = {"gpr": 4, "m0": 5, "m1": 6}[r["read"]]
        w = [ROW_TAG_BASE | r["idx"], 1, 0x28, 0, 0, 0, 0, r["ctl_v"] ^ 1]
        w[i] = r["open_v"]
        assert verdict_row(r, tuple(w))[0] == V_TRAP
        w[1] = 0
        assert verdict_row(r, tuple(w))[0] == V_VOID
    case("H27 TRAPS outranks VOID and VOID outranks the value", h27)

    def mkrecs(subset, ctl_ok=True):
        """A synthetic record set over the LIVE table: every row ran, every
        aux word is (or deliberately is not) that row's declared ctl.
        Indexed by `idx`, exactly as `read_rows` returns it."""
        rr = [None] * len(live)
        for r in subset:
            rr[r["idx"]] = (ROW_TAG_BASE | r["idx"], 0, 0, 0,
                            r["lock_v"], r["lock_v"], r["lock_v"],
                            r["ctl_v"] if ctl_ok else (r["ctl_v"] ^ 1))
        return rr

    def capture_out(rows_, path):
        """cmd_verdict's table, without cmd_verdict's printing."""
        rr = read_rows(os.path.join(ROOT, path), len(rows_))
        o = []
        for r in rows_:
            rec = rr[r["idx"]]
            if rec is None:
                o.append((r, V_NORUN, None, None))
            else:
                v, val, aux = verdict_row(r, rec)
                o.append((r, v, val, aux))
        return rr, o

    def h28():
        def mkout(verdicts):
            out = []
            for r, v in zip(live, verdicts):
                out.append((r, v, r["lock_v"], r["ctl_v"]))
            return out
        good = mkrecs(live)
        allock = mkout([V_LOCK] * len(live))
        assert not check_controls(live, allock, "qemu", good), \
            "a healthy qemu arm must produce no finding"
        one = mkout([V_LOCK] * len(live))
        one[0] = (live[0], V_OPEN, live[0]["open_v"], live[0]["ctl_v"])
        f = check_controls(live, one, "qemu", good)
        assert any("C4" in x for x in f), f
        assert not any("C4" in x
                       for x in check_controls(live, one, "device", good)), \
            "C4 must not fire on the device arm -- OPEN there is the reading"
        # the control row must read LOCK
        ctlidx = [i for i, r in enumerate(live) if r["kind"] == "ctl"]
        assert ctlidx, "the live table has no control row"
        two = mkout([V_LOCK] * len(live))
        two[ctlidx[0]] = (live[ctlidx[0]], V_OTHER, 0, 0)
        f = check_controls(live, two, "device", good)
        assert any("CONTROL" in x and "VOID" in x for x in f), f
        # and a table with no control row at all
        noctl = [r for r in live if r["kind"] != "ctl"]
        f = check_controls(noctl, mkout([V_LOCK] * len(noctl)), "device",
                           mkrecs(noctl))
        assert any("NO CONTROL ROW" in x for x in f), f
    case("H28 check_controls fires in both directions, and C4 only on qemu", h28)

    def h29():
        pairs = [r for r in live if r["family"] == "storebase" and r["dist"] == 0]
        assert len(pairs) == 2, "expected two storebase rows at d0"
        out = [(r, V_LOCK, r["lock_v"], r["ctl_v"]) for r in live]
        idx = live.index(pairs[1])
        out[idx] = (pairs[1], V_OPEN, pairs[1]["open_v"], pairs[1]["ctl_v"])
        f = check_controls(live, out, "device", mkrecs(live))
        assert any("storebase pair" in x for x in f), f
    case("H29 a storebase pair that disagrees is caught", h29)

    def h30():
        refuses(lambda: read_rows(os.devnull, len(live)),
                "a capture with no P5 lines")
    case("H30 a capture with no `P5 ` lines REFUSES", h30)

    def h31():
        """probe4's tag must not read as probe5's.  Two payloads in flight is
        exactly when a shared tag base costs a seating."""
        assert ROW_TAG_BASE == 0x52350000
        r = live[0]
        w = [0x52340000 | r["idx"], 0, 0, 0, 0, 0, 0, r["ctl_v"]]
        assert verdict_row(r, tuple(w))[0] == V_NORUN
    case("H31 a probe4 tag reads as NOT-RUN here", h31)

    def h32():
        """The recomputation itself, in three directions.  It is the SECOND
        path, so its own positive control cannot be `verdict_row` agreeing with
        it -- it is a record built here with a known-wrong aux word."""
        st, fired, failed, norec = recompute_ctls(live, mkrecs(live))
        assert len(fired) == len(live) and not failed and not norec, \
            (len(fired), len(failed), len(norec))
        st, fired, failed, norec = recompute_ctls(live, mkrecs(live, ctl_ok=False))
        assert not fired and len(failed) == len(live), (len(fired), len(failed))
        # one row wrong, the rest right
        rr = mkrecs(live)
        i = live[0]["idx"]
        rr[i] = rr[i][:7] + (live[0]["ctl_v"] ^ 1,)
        st, fired, failed, norec = recompute_ctls(live, rr)
        assert [r["name"] for r in failed] == [live[0]["name"]], failed
        assert st[live[0]["name"]] is False
        # a row whose record is absent, and a row carrying probe4's tag, are
        # both `no record` rather than a failed control: there is no aux word
        # to compare and saying `did not fire` would be a claim about nothing
        rr = mkrecs(live)
        rr[live[1]["idx"]] = None
        rr[i] = (0x52340000 | i,) + rr[i][1:]
        st, fired, failed, norec = recompute_ctls(live, rr)
        assert sorted(r["name"] for r in norec) == \
            sorted([live[0]["name"], live[1]["name"]]), norec
        assert not failed, failed
    case("H32 the per-row ctl is recomputed independently, all three states", h32)

    def h33():
        """The two paths must AGREE, and disagreement is the finding.  A single
        VOID row is NOT a finding -- it is `D3`'s not-measurable carrying its
        reason -- so the positive control here is a row whose recomputed ctl is
        wrong while its verdict is forced to something else."""
        rr = mkrecs(live)
        i = live[0]["idx"]
        rr[i] = rr[i][:7] + (live[0]["ctl_v"] ^ 1,)
        out = [(r, V_LOCK, r["lock_v"], r["ctl_v"]) for r in live]
        f = check_controls(live, out, "device", rr)
        assert any("INCOHERENT" in x and live[0]["name"] in x for x in f), f
        # the honest pairing of the same records: VOID, and no finding
        out[0] = (live[0], V_VOID, live[0]["lock_v"], live[0]["ctl_v"] ^ 1)
        assert not check_controls(live, out, "device", rr), \
            "one VOID row with a genuinely wrong ctl is a legal outcome (D3)"
        # the other sign: VOID with a control that DID fire
        out2 = [(r, V_LOCK, r["lock_v"], r["ctl_v"]) for r in live]
        out2[0] = (live[0], V_VOID, live[0]["lock_v"], live[0]["ctl_v"])
        f = check_controls(live, out2, "device", mkrecs(live))
        assert any("INCOHERENT" in x for x in f), f
        # AND IT MUST NOT FIRE ON THE DOCUMENTED ORDERING.  `verdict_row` puts
        # the exception and the tag above the control (H27), so a trapped row
        # with a wrong ctl reads TRAPS and that is not a disagreement.
        out3 = [(r, V_LOCK, r["lock_v"], r["ctl_v"]) for r in live]
        out3[0] = (live[0], V_TRAP, live[0]["lock_v"], live[0]["ctl_v"] ^ 1)
        assert not check_controls(live, out3, "device", rr), \
            "TRAPS outranks the control by design -- this must not be a finding"
    case("H33 the two ctl paths disagreeing is a FINDING, VOID alone is not", h33)

    def h34():
        """Every control failing is the payload not reading its observables at
        all.  The negative control is one row failing, which must stay silent."""
        allbad = mkrecs(live, ctl_ok=False)
        out = [(r, V_VOID, r["lock_v"], r["ctl_v"] ^ 1) for r in live]
        f = check_controls(live, out, "device", allbad)
        assert any("EVERY per-row control failed" in x for x in f), f
        rr = mkrecs(live)
        i = live[0]["idx"]
        rr[i] = rr[i][:7] + (live[0]["ctl_v"] ^ 1,)
        out = [(r, V_LOCK, r["lock_v"], r["ctl_v"]) for r in live]
        out[0] = (live[0], V_VOID, live[0]["lock_v"], live[0]["ctl_v"] ^ 1)
        assert not any("EVERY" in x for x in
                       check_controls(live, out, "device", rr)), \
            "one failed control must not read as all of them"
    case("H34 EVERY per-row control failing is a finding, one is not", h34)

    def h35():
        """The counted line, on the two committed captures.  The qemu arm is the
        NEGATIVE control -- 24 of 24, and a checker that cannot report a clean
        run is as useless as one that cannot report a dirty one -- and the
        device capture is the reading: three declared controls did not fire and
        the run is still rc 0, because three VOID rows are legal."""
        rr, out = capture_out(live, "qemu/2026-09-13/probe5.txt")
        _st, fired, failed, norec = recompute_ctls(live, rr)
        assert (len(fired), len(failed), len(norec)) == (24, 0, 0), \
            (len(fired), len(failed), len(norec))
        assert ctl_line(live, rr) == "per-row controls: 24 of 24 fired, 0 did not", \
            ctl_line(live, rr)
        assert not check_controls(live, out, "qemu", rr), \
            check_controls(live, out, "qemu", rr)
        rr, out = capture_out(live, "bench/2026-09-14/C1-P5j.log")
        assert ctl_line(live, rr) == ("per-row controls: 21 of 24 fired, 3 did "
                                      "not (cp0: c0_d0, c0_d1, c0_d2)"), \
            ctl_line(live, rr)
        assert not check_controls(live, out, "device", rr), \
            check_controls(live, out, "device", rr)
    case("H35 the counted line: qemu 24 of 24, the device capture 21 of 24", h35)

    def h36():
        """The ladder must not call an unmeasurable family open.  This is a
        RENDERING case: it asserts on the printed line and on no verdict.

        The direct half comes first because the two PARTLY-unmeasured wordings
        are not reachable from any committed capture -- every family in the
        device capture is either wholly read or wholly VOID -- so without it
        those two branches would be rendering rules nothing exercises."""
        assert ladder_depth([(0, V_LOCK), (1, V_LOCK)]) == "closes at d0"
        assert ladder_depth([(0, V_OPEN), (1, V_LOCK)]) == "closes at d1"
        assert ladder_depth([(0, V_OPEN), (1, V_OPEN)]) == "open at every rung"
        assert ladder_depth([(0, V_VOID), (1, V_VOID)]) == \
            "not measurable at any rung (see the ctl column)"
        assert ladder_depth([(0, V_VOID), (1, V_TRAP)]) == \
            "not measurable at any rung (1 VOID, 1 other)"
        assert ladder_depth([(0, V_NORUN), (1, V_TRAP)]) == \
            "not measurable at any rung (0 VOID, 2 other)"
        assert ladder_depth([(0, V_VOID), (1, V_LOCK)]) == \
            "closes at d1 -- but 1 of 2 rung(s) not measurable"
        assert ladder_depth([(0, V_VOID), (1, V_OPEN)]) == \
            "open at every MEASURED rung (1 of 2 not measurable)"
        # OTHER is a reading -- the table's own doctrine, `isa-hazard.tsv:30-33`
        assert ladder_depth([(0, V_OTHER)]) == "open at every rung"
        import io as _io
        import contextlib as _cl

        def ladder(path, arm):
            buf = _io.StringIO()
            with _cl.redirect_stdout(buf):
                cmd_verdict(live, os.path.join(ROOT, path), arm)
            got, seen = {}, False
            for ln in buf.getvalue().split("\n"):
                if "the ladder (" in ln:
                    seen = True
                    continue
                if seen:
                    if not ln.strip():
                        break
                    got[ln.split()[0]] = ln.strip()
            return got
        L = ladder("bench/2026-09-14/C1-P5j.log", "device")
        # PIN THE PARSE FIRST. Both loops below are `for ... assert not
        # in`, which pass over an empty dict -- so without this the whole
        # negative half of this case could not fail.
        assert sorted(L) == sorted(FAMILIES), sorted(L)
        assert "cp0" in L, sorted(L)
        assert "not measurable at any rung" in L["cp0"], L["cp0"]
        assert "open at every rung" not in L["cp0"], L["cp0"]
        # the negative control: a family with a reading at every rung is
        # untouched, and no OTHER family may pick up the new wording
        assert L["loaduse"].endswith("closes at d1"), L["loaduse"]
        for fam, ln in L.items():
            if fam != "cp0":
                assert "not measurable" not in ln, (fam, ln)
        # and the qemu arm, where nothing is VOID at all
        Q = ladder("qemu/2026-09-13/probe5.txt", "qemu")
        assert sorted(Q) == sorted(FAMILIES), sorted(Q)
        for fam, ln in Q.items():
            assert "not measurable" not in ln, (fam, ln)
    case("H36 an all-VOID family renders as not measurable, not as open", h36)

    print("")
    print("self-test: %d of %d" % (ok, n))
    if fails:
        print("  failed: %s" % ", ".join(fails))
    return 0 if ok == n else 1


# --------------------------------------------------------------------------

def main(argv):
    import argparse
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mode", nargs="?",
                    choices=["population", "model", "emit", "verify",
                             "verdict", "sites"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--arm", choices=["qemu", "device"], default="device")
    ap.add_argument("--objdump")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if not a.mode:
        print("no mode. --self-test runs the controls alone; see the docstring.",
              file=sys.stderr)
        return 3

    rows = load_rows()
    if a.mode == "population":
        return cmd_population(rows, a.quiet)
    if a.mode == "model":
        return cmd_model(rows, a.quiet)
    if a.mode == "emit":
        return cmd_emit(rows, a.check, a.quiet)
    if a.mode == "verify":
        return cmd_verify(rows, a.arg, a.objdump, a.quiet, a.strict)
    if a.mode == "verdict":
        if not a.arg:
            raise Refuse("verdict needs a capture")
        return cmd_verdict(rows, a.arg, a.arm, a.quiet)
    if a.mode == "sites":
        return cmd_sites(rows, a.arg)
    return 3


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Refuse as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        sys.exit(3)
