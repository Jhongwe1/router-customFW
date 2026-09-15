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


SELFTEST_SRC = """\
\tuc_cell nop_a, uc_w_nop_a, 0x00000000
\tuc_cell nop_b, uc_w_nop_b, 0x00000000
\tuc_cell sync,  uc_w_sync,  0x0000000F
\tuc_cell lw,    uc_w_lw,    0x8D420000
\tuc_cell ll,    uc_w_ll,    0xC1420000
\tuc_cell sw,    uc_w_sw,    0xAD490000
\tuc_cell sc,    uc_w_sc,    0xE1490000
\tuc_cell lwu2,  uc_w_lwu2,  0x8D420000, 2
"""


def self_test():
    """Every check above, shown able to FAIL.

    🔴 A GREEN `ucostcheck` IS A CLAIM AND UNTIL THIS EXISTED NOTHING TESTED
    IT.  The tool is a build gate -- `UG0` -- so it runs on every `ucost`
    build and has never once reported a finding.  That is exactly the shape
    `CLAUDE.md` names: a tool reporting 0 is making a claim, and a tool that
    cannot fail proves nothing.  Each case below mutates the fixture in ONE
    way and requires the named check to fire; `P1` is the population control
    that stops the rest passing on a fixture that parses to nothing.
    """
    import tempfile

    cases, fails = [], 0

    def run(name, text, want_rc, want_sub=None):
        nonlocal fails
        d = tempfile.mkdtemp()
        p = os.path.join(d, "ucost-cells.S")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        import io as _io
        import contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _check(p)
        out = buf.getvalue()
        ok = (rc == want_rc) and (want_sub is None or want_sub in out)
        cases.append((name, ok, "rc=%d" % rc))
        if not ok:
            fails += 1
        return out

    run("P1 the unmutated fixture is clean", SELFTEST_SRC, 0)
    run("P2 and it parsed all eight cells", SELFTEST_SRC, 0, "8 cell(s)")
    # C1 -- a probed word that is not its census row's
    run("N1 a word that differs from the tsv is caught",
        SELFTEST_SRC.replace("0x0000000F", "0x0000001F"), 1, "C1 sync")
    # C2 -- a symbol that does not name its cell
    run("N2 a mis-named _w symbol is caught",
        SELFTEST_SRC.replace("uc_w_sync", "uc_w_synch"), 1, "C2 cell sync")
    # C3 both ways
    run("N3 a cell with no mapping and no exemption is caught",
        SELFTEST_SRC + "\tuc_cell teq, uc_w_teq, 0x00000034\n", 1,
        "C3 cell(s) with no tsv mapping")
    run("N4 an exemption no cell took is caught",
        SELFTEST_SRC.replace("\tuc_cell nop_b, uc_w_nop_b, 0x00000000\n", ""),
        1, "C3 exemption(s) named here")
    # C4 -- the offset, which is invisible in the .word
    run("N5 an offset on the wrong cell is caught",
        SELFTEST_SRC.replace("uc_w_lw,    0x8D420000", "uc_w_lw,    0x8D420000, 4"),
        1, "C4 non-zero base offsets")
    run("N6 the unaligned cell losing its offset is caught",
        SELFTEST_SRC.replace("0x8D420000, 2", "0x8D420000"), 1,
        "C4 non-zero base offsets")
    # C5 -- the twin relationship
    run("N7 lwu2 ceasing to be lw's twin is caught",
        SELFTEST_SRC.replace("uc_w_lwu2,  0x8D420000, 2",
                             "uc_w_lwu2,  0x8C420000, 2"), 1, "C1 lwu2")
    # C0 -- the population control, and it is the one that makes the rest mean
    # something: a fixture the regex cannot read must REFUSE, not report clean.
    run("N8 a file the regex cannot read REFUSES, not reports clean",
        "\tuc_cell_nop_a:\n\t.word 0\n", 1, "C0 only 0 cell(s) parsed")

    for name, ok, note in cases:
        print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", name, note))
    print("RESULT: %d passed, %d failed" % (len(cases) - fails, fails))
    return 1 if fails else 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        return self_test()
    if len(sys.argv) != 2:
        print("usage: ucostcheck.py <ucost-cells.S> | --self-test",
              file=sys.stderr)
        return 2
    return _check(sys.argv[1])


def _check(src):
    """The checks, factored out so `--self-test` can drive them in-process."""

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
