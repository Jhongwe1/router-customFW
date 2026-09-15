#!/usr/bin/env python3
"""ucostcheck -- every probed word in `ucost-cells.S` against `isa-payload.tsv`.

WHY THIS IS A TOOL AND NOT A COMMENT
------------------------------------
`R1-pub-4b` measures the cost of instructions that `R1-pub-4a` found on the
emulation surface.  The two steps are only comparable if they execute THE SAME
ENCODINGS, and `4a`'s payload (`tools/rlxprobe/cells4.S`) is generated from
`tools/isa-payload.tsv` by `tools/isapay.py emit`.  `ucost-cells.S` is hand
written -- it has to be, because a cost measurement needs the probed word
inside a counted loop and `cells4.S`'s cells are shaped for one execution under
a fault handler -- so nothing structural makes the two agree.  This does.

🔴 AND IT SWEEPS BOTH WAYS, WHICH IS THE HALF THAT MATTERS.
Two of the eight cells are `nop`, and `nop` has no row in `isa-payload.tsv` and
CANNOT have one: that census excludes, by its own rule, "an instruction this
core obviously has, and that the loader executes thousands of times per boot".
So a checker written as a lookup would have to skip them, and a skip that is
not itself checked is how an allow-list accretes.  `NO_TSV_ROW` is therefore a
list by NAME, and `C3` requires the set of cells that took the exemption to be
EXACTLY that list -- a cell that quietly stops matching its row cannot hide in
it, and a cell added to it without being added here fails.

This is `tools/flashwin.py`'s shape and `tools/cardcheck.py`'s `A20`/`B10`
argument, one directory over.

量 2026-09-16, first run: 8 cells, 6 matched against the tsv, 2 exempt.
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "isa-payload.tsv")

# Cell name -> the `mnem` of the isa-payload.tsv row whose `word` it must equal.
# `lwu2` is the SAME word as `lw` on purpose: it is the unaligned cell, and the
# only difference between it and its twin is two added to a base register
# OUTSIDE the loop.  If it had its own encoding it would not be a twin.
CELL_TO_MNEM = {
    "sync": "sync",
    "lw": "lw",
    "ll": "ll",
    "sw": "sw",
    "sc": "sc",
    "lwu2": "lw",
}

# Cells with no row in the census, BY NAME, with the reason.  C3 sweeps this
# in both directions.
NO_TSV_ROW = {
    "nop_a": "the census excludes what the loader obviously executes; and this "
             "cell is half of the zero control, whose job is to have no cost",
    "nop_b": "the second zero-control cell, at a second address, so that "
             "`nop_a - nop_b` is a control that can fail",
}

CELL_RX = re.compile(
    r"^\s*uc_cell\s+([a-z0-9_]+),\s*([a-z0-9_]+),\s*(0x[0-9A-Fa-f]{8})"
    r"(?:\s*,\s*(-?\d+))?\s*$")


def load_tsv(path):
    """mnem -> (lineno, word).  Refuses a duplicate mnemonic rather than
    picking one, which is `tools/rlxfw-marks.py`'s rule about anchors."""
    out, dup = {}, []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 5:
                continue
            mnem, word = f[1].strip(), f[4].strip()
            if not re.fullmatch(r"0x[0-9A-Fa-f]{8}", word):
                continue
            if mnem in out:
                dup.append(mnem)
            out[mnem] = (n, int(word, 16))
    return out, dup


def main():
    if len(sys.argv) != 2:
        print("usage: ucostcheck.py <ucost-cells.S>", file=sys.stderr)
        return 2
    src = sys.argv[1]

    tsv, dup = load_tsv(TSV)
    cells = []
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            m = CELL_RX.match(line)
            if m:
                cells.append((m.group(1), m.group(2), int(m.group(3), 16),
                              int(m.group(4) or 0)))

    fails = []

    # C0 -- the population is real.  A checker that parsed nothing would pass
    # every other case below, which is this project's own "a tool reporting 0
    # is making a claim".
    if len(cells) < 4:
        fails.append("C0 only %d cell(s) parsed out of %s -- the regex and the "
                     "file disagree" % (len(cells), src))
    if dup:
        fails.append("C0 duplicate mnemonic(s) in the tsv: %s" % ", ".join(dup))

    # C1 -- every mapped cell equals its row's word.
    took_exemption = set()
    for name, wsym, word, off in cells:
        if name in CELL_TO_MNEM:
            mnem = CELL_TO_MNEM[name]
            if mnem not in tsv:
                fails.append("C1 %s maps to mnemonic %r, which is not in the tsv"
                             % (name, mnem))
                continue
            ln, want = tsv[mnem]
            if word != want:
                fails.append("C1 %s is 0x%08X, tsv:%d (%s) is 0x%08X"
                             % (name, word, ln, mnem, want))
        else:
            took_exemption.add(name)

    # C2 -- every cell's word symbol is named for the cell.  A `uc_w_` that
    # does not match its cell makes the desk's PC resolution silently wrong.
    for name, wsym, word, off in cells:
        if wsym != "uc_w_" + name:
            fails.append("C2 cell %s carries symbol %s" % (name, wsym))

    # C3 -- the exemption list, BOTH WAYS.
    if took_exemption != set(NO_TSV_ROW):
        only_file = sorted(took_exemption - set(NO_TSV_ROW))
        only_list = sorted(set(NO_TSV_ROW) - took_exemption)
        if only_file:
            fails.append("C3 cell(s) with no tsv mapping and no named "
                         "exemption: %s" % ", ".join(only_file))
        if only_list:
            fails.append("C3 exemption(s) named here that no cell took: %s"
                         % ", ".join(only_list))

    # C4 -- exactly one cell may carry a non-zero offset, and it is the
    # unaligned one.  An offset is invisible in the `.word` and would make a
    # cell differ from its twin in a way C1 cannot see.
    offs = {n: o for n, _, _, o in cells if o != 0}
    if offs != {"lwu2": 2}:
        fails.append("C4 non-zero base offsets are %r, expected {'lwu2': 2}"
                     % offs)

    # C5 -- the unaligned cell and its twin carry the SAME word.  That is the
    # whole design of the row: same encoding, same registers, odd address.
    words = {n: w for n, _, w, _ in cells}
    if "lwu2" in words and "lw" in words and words["lwu2"] != words["lw"]:
        fails.append("C5 lwu2 0x%08X != lw 0x%08X -- then it is not a twin"
                     % (words["lwu2"], words["lw"]))

    print("ucostcheck: %d cell(s), %d checked against %s, %d exempt by name"
          % (len(cells), len(cells) - len(took_exemption),
             os.path.basename(TSV), len(took_exemption)))
    for name, _, word, off in cells:
        where = ("tsv:%d" % tsv[CELL_TO_MNEM[name]][0]
                 if name in CELL_TO_MNEM else "exempt")
        print("  %-6s 0x%08X  off=%-2d %s" % (name, word, off, where))
    if fails:
        for f in fails:
            print("  FAIL %s" % f)
        print("%d finding(s)" % len(fails))
        return 1
    print("  ok   every probed word is the census's, and the exemption list "
          "is exact in both directions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
