#!/usr/bin/env python3
"""regcensus.py -- which SYMBOLS in an image materialise a given register
address, counted from a disassembly and attributed through `System.map`.

WHY IT EXISTS
-------------
`docs/blind-write-ledger.md` § 4.9 records a reading of this unit's vendor
GPIO driver taken as OBJECT code: *"the **nine** functions that materialise
`0xB800350C` were located -- this row said FOUR until the count was re-derived
off the eleven `ori` sites"*.  That census was done by hand, twice, and the
first hand slipped.  `R5-7` has to re-take it before it opens a write mask, and
a number a hand derives twice with two answers is a number that needs a tool.

WHAT IT IS FOR, WHICH IS NARROWER THAN IT LOOKS
-----------------------------------------------
It answers *how many distinct functions could touch this register*, using only
symbol NAMES from a `System.map` this project's own build produced.  It never
reports what a function does.  That distinction is the whole reason the tool
has this shape: § 4.1 of the ledger records the `led` domain at **zero** cited
paths -- no implementation of that peripheral, by anyone, has been read here --
and disassembling the vendor's LED routines to find out whether they write a
pin would spend that.  A symbol name is `name` depth and the names in question
are already declared in § 4.9.

🔴 TWO THINGS IT CANNOT SEE, AND BOTH ARE PRINTED BESIDE EVERY CENSUS
---------------------------------------------------------------------
1. **Displacement addressing.**  A caller that forms the block BASE once and
   reaches a register with `lw rX,12(base)` never materialises the register's
   own address, so no census of that address can see it.  This is not
   hypothetical: 量 2026-09-10, on `r57`, **this project's own driver** reads
   `PABCD_DAT` on every `.get` and appears **zero** times in that register's
   census, because the compiler folded `base + 0x0C` into the load.  The
   vendor's code in the same image forms full addresses and is fully visible.
   So the tool takes a second census -- of the block BASE -- and prints it
   beside the first.  A symbol in the base census and not in the register
   census is exactly a candidate for displacement access.

2. **Indirect flow.**  A function reached through a pointer, or one that takes
   the address from memory rather than forming it, is invisible.  `SPEC.md`
   `FW-43` is this repository's own instance of that trap in a `jal` census.

Both are stated in the output, every run, because a census that prints only
what it found reads as coverage.

🔴 AND ONE MORE, WHICH IS WHY THIS TOOL DOES NOT ONLY COUNT `ori`
-----------------------------------------------------------------
`0xB8003500` can be formed as `lui 0xb800` + **`ori 0x3500`** or + **`addiu
0x3500`**, and the compiler picks per site.  The ledger's "eleven `ori` sites"
is therefore a lower bound on its own terms.  This tool counts every immediate
form (`ori`, `addiu`, `addi`, `li`) and reports the split, so the two can never
be confused again.

THE POSITIVE CONTROL, WHICH IS A REFUSAL
-----------------------------------------
`--require-symbol PREFIX` names a symbol prefix that MUST appear somewhere in
the attribution.  An address-to-symbol map that resolves nothing prints an
empty census, and an empty census is indistinguishable from a clean image.
With the flag, the tool refuses to print a verdict unless the control fired.

USAGE
-----
    regcensus.py census --listing dis.txt --map System.map \\
        --reg PABCD_DAT=0x350c --reg PABCD_CNR=0x3500 \\
        --base 0xb800 --block-base 0x3500 \\
        --mine rtl819x_gpio --require-symbol rtl819x_gpio

    regcensus.py census --vmlinux vmlinux --map System.map ...   (runs objdump)
    regcensus.py --self-test
"""

import argparse
import bisect
import os
import re
import shutil
import subprocess
import sys

OBJDUMP_DEFAULT = "/usr/bin/mips-linux-gnu-objdump"

# objdump renders a MIPS disassembly line as
#     800d91f0:\t3442350 0\tori\tv0,v0,0x3500
LINE_RE = re.compile(r"^\s*([0-9a-fA-F]{6,16}):\s+[0-9a-fA-F ]{8,}\s+(\S+)\s*(.*)$")

# The immediate forms that can complete a `lui`.  `li` is objdump's rendering
# of `addiu rX,zero,imm`, which materialises a whole small constant on its own.
IMM_MNEMONICS = ("ori", "addiu", "addi", "li")
IMM_RE = re.compile(r"(?:^|,)\s*(-?0x[0-9a-fA-F]+|-?\d+)\s*$")


class Sym(object):
    __slots__ = ("addr", "name")

    def __init__(self, addr, name):
        self.addr = addr
        self.name = name


def parse_map(text):
    """System.map -> a sorted list of Sym.  Malformed lines are skipped, and
    the caller is told how many, because a map that parsed to nothing would
    otherwise attribute every site to `?`."""
    syms, skipped = [], 0
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            if line.strip():
                skipped += 1
            continue
        try:
            syms.append(Sym(int(parts[0], 16), parts[2]))
        except ValueError:
            skipped += 1
    syms.sort(key=lambda s: s.addr)
    return syms, skipped


def sym_for(syms, addrs, addr):
    """The symbol whose address is the greatest one <= addr.

    An address BELOW every symbol has no enclosing symbol and is reported as
    `?` rather than folded into the first one -- attributing a site to the
    wrong function is worse than admitting the map does not reach it."""
    i = bisect.bisect_right(addrs, addr) - 1
    if i < 0:
        return "?"
    return syms[i].name


def parse_listing(text):
    """Yield (addr, mnemonic, operand-text) for every disassembled line."""
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        yield int(m.group(1), 16), m.group(2), m.group(3)


def immediate_of(mnem, ops):
    if mnem not in IMM_MNEMONICS:
        return None
    m = IMM_RE.search(ops)
    if not m:
        return None
    tok = m.group(1)
    try:
        return int(tok, 16) if tok.lower().startswith(("0x", "-0x")) else int(tok, 10)
    except ValueError:
        return None


LUI_RE = re.compile(r"^\s*(\S+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*$")

# How far back a `lui` may sit from the instruction that completes it.  The
# scheduler moves them apart; 24 is generous and the window is reported, so a
# reader can see it is a parameter and not a fact.
PAIR_WINDOW = 24


def source_reg(mnem, ops):
    """The register an `ori`/`addiu` reads.  `li` reads none -- it materialises
    a whole small constant, so it can never be completing a `lui`."""
    if mnem == "li":
        return None
    parts = [p.strip() for p in ops.split(",")]
    return parts[1] if len(parts) >= 3 else None


def lui_dest(ops):
    m = LUI_RE.match(ops)
    if not m:
        return None, None
    try:
        return m.group(1).strip(), int(m.group(2), 0)
    except ValueError:
        return None, None


def census(listing_text, map_text, targets, base_hi=None):
    """targets: {label: low_half}.  Returns
       {label: {symbol: {"sites": [...], "forms": {...}, "unpaired": [...]}}}

    A site is a **materialisation** only if a `lui` with the requested high
    half, writing the register this instruction reads, sits within
    PAIR_WINDOW instructions above it in the same symbol.  Without that test an
    `addiu rX,rY,0x3508` doing ordinary pointer arithmetic on a 13,576-byte
    structure offset is indistinguishable from one completing an address, and
    量 2026-09-10 on `r57` there is exactly such a site (`del_sta`, the
    wireless driver).  Sites that fail the test are kept and reported as
    UNPAIRED rather than dropped: this instrument's job is to say what it
    found and what it could not confirm, not to present a filtered list."""
    syms, _skipped = parse_map(map_text)
    addrs = [s.addr for s in syms]
    want = {}
    for label, lo in targets.items():
        want.setdefault(lo, []).append(label)

    insns = list(parse_listing(listing_text))
    out = dict((label, {}) for label in targets)

    for i, (addr, mnem, ops) in enumerate(insns):
        imm = immediate_of(mnem, ops)
        if imm is None or imm not in want:
            continue
        name = sym_for(syms, addrs, addr)

        paired = base_hi is None          # no --base given: do not judge
        if base_hi is not None:
            src = source_reg(mnem, ops)
            if src is not None:
                for j in range(i - 1, max(-1, i - 1 - PAIR_WINDOW), -1):
                    paddr, pmnem, pops = insns[j]
                    if sym_for(syms, addrs, paddr) != name:
                        break
                    if pmnem != "lui":
                        continue
                    d, hi = lui_dest(pops)
                    if d == src:
                        paired = (hi == base_hi)
                        break

        for label in want[imm]:
            slot = out[label].setdefault(
                name, {"sites": [], "forms": {}, "unpaired": []})
            if paired:
                slot["sites"].append(addr)
                slot["forms"][mnem] = slot["forms"].get(mnem, 0) + 1
            else:
                slot["unpaired"].append(addr)
    for label in out:
        for name in list(out[label]):
            if not out[label][name]["sites"] and not out[label][name]["unpaired"]:
                del out[label][name]
    return out


def _confirmed(bysym):
    return dict((k, v) for k, v in bysym.items() if v["sites"])


def render(result, order, mine_prefix, block_label):
    lines = []
    for label in order:
        bysym = result.get(label, {})
        conf = _confirmed(bysym)
        n = sum(len(v["sites"]) for v in conf.values())
        nu = sum(len(v["unpaired"]) for v in bysym.values())
        lines.append("== %s -- %d confirmed site(s) in %d symbol(s), "
                     "%d unpaired immediate(s) ==" % (label, n, len(conf), nu))
        for name in sorted(bysym, key=lambda k: min(bysym[k]["sites"]
                                                    or bysym[k]["unpaired"])):
            v = bysym[name]
            tag = "MINE  " if mine_prefix and name.startswith(mine_prefix) else "other "
            if v["sites"]:
                forms = ",".join("%s=%d" % (k, v["forms"][k])
                                 for k in sorted(v["forms"]))
                lines.append("   %s %-30s %2d site(s)  [%s]  %s"
                             % (tag, name, len(v["sites"]), forms,
                                " ".join("%08x" % a for a in v["sites"])))
            if v["unpaired"]:
                lines.append("   %s %-30s %2d UNPAIRED -- the immediate is "
                             "there and no matching `lui` is: NOT counted  %s"
                             % (tag, name, len(v["unpaired"]),
                                " ".join("%08x" % a for a in v["unpaired"])))
        lines.append("")

    if block_label and block_label in result:
        base_syms = set(_confirmed(result[block_label]))
        for label in order:
            if label == block_label:
                continue
            only_base = sorted(base_syms - set(_confirmed(result.get(label, {}))))
            lines.append("-- blind spot bound for %s: %d symbol(s) form the "
                         "block base and never form this register's own "
                         "address, so a displacement access from any of them "
                         "is invisible above --" % (label, len(only_base)))
            if only_base:
                lines.append("   " + ", ".join(only_base))
        lines.append("")
    lines.append("This census counts %s immediates only, and only where a "
                 "matching `lui` is within %d instruction(s) in the same "
                 "symbol.  It cannot see a displacement access, and it cannot "
                 "see an address taken from memory or reached through a "
                 "pointer." % ("/".join(IMM_MNEMONICS), PAIR_WINDOW))
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# controls
# ----------------------------------------------------------------------------

FIX_MAP = """\
80000100 T alpha
80000200 t beta
80000300 T gamma
80000400 T delta
80000500 T epsilon
80000600 T zeta
80000700 T eta
80000800 T theta
"""

# alpha:   forms the register address with `ori`
# beta:    forms it with `addiu` -- the form an ori-only census misses
# gamma:   forms only the BLOCK BASE, then uses a displacement -- invisible
# delta:   mentions the same hex in a mnemonic that does not materialise
# epsilon: an `addiu` with the right immediate and NO `lui` -- ordinary pointer
#          arithmetic.  量 2026-09-10 there is a real one of these on `r57`.
# zeta:    a `lui` with the WRONG high half
# eta:     a `lui` of a DIFFERENT register
# theta:   `li`, which materialises a whole small constant and can never be
#          completing a `lui`
# one site before every symbol, to exercise `?`
FIX_DIS = """\

Disassembly of section .text:

800000f0 <before_everything>:
800000f0:	3c02b800 	lui	v0,0xb800
800000f4:	3442350c 	ori	v0,v0,0x350c

80000100 <alpha>:
80000100:	3c02b800 	lui	v0,0xb800
80000104:	3442350c 	ori	v0,v0,0x350c
80000108:	8c430000 	lw	v1,0(v0)
8000010c:	03e00008 	jr	ra

80000200 <beta>:
80000200:	3c02b800 	lui	v0,0xb800
80000204:	2442350c 	addiu	v0,v0,0x350c
80000208:	ac430000 	sw	v1,0(v0)

80000300 <gamma>:
80000300:	3c02b800 	lui	v0,0xb800
80000304:	34423500 	ori	v0,v0,0x3500
80000308:	8c43000c 	lw	v1,12(v0)

80000400 <delta>:
80000400:	1000350c 	b	8000d434
80000404:	8c43350c 	lw	v1,13580(v0)

80000500 <epsilon>:
80000500:	24843508 	addiu	a0,a0,0x3508

80000600 <zeta>:
80000600:	3c02b801 	lui	v0,0xb801
80000604:	3442350c 	ori	v0,v0,0x350c

80000700 <eta>:
80000700:	3c04b800 	lui	a0,0xb800
80000704:	3442350c 	ori	v0,v0,0x350c

80000800 <theta>:
80000800:	3c02b800 	lui	v0,0xb800
80000804:	2402350c 	li	v0,0x350c
"""

TARGETS = {"REG_DAT": 0x350C, "REG_DIR": 0x3508, "BLOCK_BASE": 0x3500}
BASE_HI = 0xB800


def controls():
    bad, ran = [], []

    def ck(name, cond, msg):
        ran.append(name)
        if not cond:
            bad.append("%s FAILED: %s" % (name, msg))
        # One line per control, two leading spaces and two more after the
        # verdict, because tools/ci-census.py parses `^ {2}ok\s{2,}(.*)$` and
        # `^ {2}FAIL\s{2,}(.*)$`.  A suite that prints only its own summary is
        # counted as ZERO cases: the tool exits 0 and the build goes red with
        # `CENSUS-MISMATCH 0+0+0 != 21`.  量 2026-09-10, CI runs 34393578330
        # and 34393733450 -- that is exactly what this file did on the two
        # pushes that introduced it, and the same shape cost capdate and
        # capfield a push on 2026-09-08 with four leading spaces instead of
        # two.  The newline collapse is not cosmetic: the census parses per
        # LINE, so a control's message must not be able to synthesise a case
        # line.  Every message here is a literal or a %r today; this makes
        # that an invariant instead of a property of the current call sites.
        print("  %-5s %-6s %s" % ("ok" if cond else "FAIL", name,
                                  "" if cond else "-- " + " ".join(msg.split())))

    r = census(FIX_DIS, FIX_MAP, TARGETS, BASE_HI)
    dat = r["REG_DAT"]
    base = r["BLOCK_BASE"]
    dirr = r["REG_DIR"]

    ck("C1", "alpha" in dat and dat["alpha"]["sites"] == [0x80000104],
       "an `ori` site inside alpha must attribute to alpha; got %r" % (dat.get("alpha"),))

    ck("C2", "beta" in dat,
       "an `addiu` site must be counted -- an ori-only census is what this "
       "control exists to kill; got %r" % (sorted(dat),))
    ck("C2b", "beta" in dat and dat["beta"]["forms"] == {"addiu": 1},
       "the FORM must be reported so ori and addiu can never be merged; got %r"
       % (dat.get("beta", {}).get("forms"),))

    ck("C3", "gamma" not in dat and "gamma" in base,
       "gamma forms only the block base and reaches the register by "
       "displacement: it must be ABSENT from the register census and PRESENT "
       "in the base census, which is the whole blind-spot bound; got dat=%r base=%r"
       % ("gamma" in dat, "gamma" in base))

    ck("C4", "delta" not in dat,
       "a branch target and a load displacement are not materialisations; got %r"
       % (dat.get("delta"),))

    ck("C5", dat.get("?", {}).get("sites") == [0x800000f4],
       "a site below every symbol must be reported as `?` and not folded into "
       "the first symbol; got %r" % (dat.get("?"),))

    ck("C6", "alpha" not in base,
       "alpha forms the register address, not the base; it must not appear in "
       "the base census; got %r" % (sorted(base),))

    # the blind-spot bound itself, as rendered
    txt = render(r, ["REG_DAT", "BLOCK_BASE"], "alph", "BLOCK_BASE")
    tail = txt.split("blind spot bound for REG_DAT", 1)
    ck("C7", len(tail) == 2 and "gamma" in tail[1][:400],
       "the rendered bound must NAME the symbols it cannot see")
    ck("C8", "MINE" in txt,
       "--mine must mark a matching symbol, or the operator cannot tell their "
       "own code from the vendor's in the listing")
    ck("C9", "cannot see a displacement access" in txt,
       "every render must carry its own limits; a census that prints only what "
       "it found reads as coverage")

    # map parsing
    syms, skipped = parse_map(FIX_MAP + "garbage line\nzz not hex T x\n")
    ck("C10", len(syms) == 8 and skipped == 2,
       "malformed map lines must be counted, not silently dropped; got %d/%d"
       % (len(syms), skipped))

    syms2, _ = parse_map("")
    ck("C11", syms2 == [],
       "an empty map must parse to nothing rather than raise")
    r2 = census(FIX_DIS, "", TARGETS)
    ck("C12", set(r2["REG_DAT"]) == {"?"},
       "with an empty map EVERY site must be `?` -- this is the state the "
       "--require-symbol control exists to catch; got %r" % (sorted(r2["REG_DAT"]),))

    ck("C13", immediate_of("ori", "v0,v0,0x350c") == 0x350C
       and immediate_of("lui", "v0,0xb800") is None,
       "`lui` is not a completion form and must not be counted")
    ck("C14", immediate_of("li", "v0,-22") == -22,
       "a negative immediate must parse, so a census on a negative low half "
       "is possible at all")

    # ---- the pairing test.  Without these four, an `addiu rX,rY,0x3508`
    # doing pointer arithmetic on a 13,576-byte structure offset counts as a
    # register access, which is the false positive this tool met on its first
    # real run (`del_sta`, 2026-09-10).
    ck("C15", dirr.get("epsilon", {}).get("sites") == []
       and dirr.get("epsilon", {}).get("unpaired") == [0x80000500],
       "an immediate with no `lui` above it must be UNPAIRED and not counted; "
       "got %r" % (dirr.get("epsilon"),))
    ck("C16", dat.get("zeta", {}).get("sites") == []
       and dat.get("zeta", {}).get("unpaired") == [0x80000604],
       "a `lui` with the wrong high half must not confirm a site; got %r"
       % (dat.get("zeta"),))
    ck("C17", dat.get("eta", {}).get("sites") == []
       and dat.get("eta", {}).get("unpaired") == [0x80000704],
       "a `lui` of a DIFFERENT register must not confirm a site; got %r"
       % (dat.get("eta"),))
    ck("C18", dat.get("theta", {}).get("sites") == []
       and dat.get("theta", {}).get("unpaired") == [0x80000804],
       "`li` materialises a whole constant and can never be completing a "
       "`lui`, even with one directly above it; got %r" % (dat.get("theta"),))

    # ---- and the control on the control: with no --base the tool must NOT
    # judge, so every site comes back confirmed.  A pairing test that cannot
    # be turned off would make the unpaired count unfalsifiable.
    rn = census(FIX_DIS, FIX_MAP, TARGETS, None)
    ck("C19", all(v["unpaired"] == [] for by in rn.values() for v in by.values())
       and rn["REG_DAT"].get("zeta", {}).get("sites") == [0x80000604],
       "with no --base every site must be reported unjudged; got %r"
       % (rn["REG_DAT"].get("zeta"),))

    txt2 = render(r, ["REG_DAT", "REG_DIR", "BLOCK_BASE"], None, "BLOCK_BASE")
    ck("C20", "UNPAIRED" in txt2,
       "the render must SHOW the unpaired sites; a filtered list that drops "
       "them looks like a clean census")

    return bad, ran


def run_controls(expected=21):
    print("regcensus controls")
    bad, ran = controls()
    if len(ran) != expected:
        print("regcensus: REFUSING -- %d controls ran, %d expected. A control "
              "set that did not execute proves nothing." % (len(ran), expected))
        return 2
    if bad:
        for b in bad:
            print("  " + b)
        return 2
    print("  %d/%d controls ok" % (len(ran), expected))
    return 0


# ----------------------------------------------------------------------------


def cmd_census(a):
    if a.listing:
        with open(a.listing, encoding="utf-8", errors="replace") as f:
            listing = f.read()
    else:
        od = a.objdump or OBJDUMP_DEFAULT
        if not (os.path.isabs(od) and os.path.exists(od)) and not shutil.which(od):
            print("regcensus: REFUSING -- no objdump at %r. Give --listing "
                  "instead; this tool never needs the toolchain to run its "
                  "controls." % od)
            return 2
        listing = subprocess.run([od, "-d", a.vmlinux], capture_output=True,
                                 text=True, encoding="utf-8",
                                 errors="replace").stdout
    with open(a.map, encoding="utf-8", errors="replace") as f:
        map_text = f.read()

    targets, order = {}, []
    for spec in a.reg:
        label, _, val = spec.partition("=")
        if not val:
            print("regcensus: REFUSING -- --reg wants LABEL=0xNNNN, got %r" % spec)
            return 2
        targets[label] = int(val, 0)
        order.append(label)
    if a.block_base is not None:
        targets["BLOCK_BASE"] = a.block_base
        order.append("BLOCK_BASE")

    syms, skipped = parse_map(map_text)
    print("map: %d symbol(s), %d unparsed line(s)" % (len(syms), skipped))
    if a.vmlinux:
        print("image: %s" % a.vmlinux)
    print()

    if a.base is None:
        print("regcensus: NOTE -- no --base given, so the pairing test is off "
              "and every immediate is reported unjudged.")
    result = census(listing, map_text, targets, a.base)
    print(render(result, order, a.mine,
                 "BLOCK_BASE" if a.block_base is not None else None))

    if a.require_symbol:
        seen = any(n.startswith(a.require_symbol)
                   for by in result.values() for n in by)
        print()
        if not seen:
            print("regcensus: REFUSING -- the positive control did not fire: no "
                  "symbol beginning %r appears anywhere in the attribution, so "
                  "the address-to-symbol mapping is not working and no count "
                  "above may be quoted." % a.require_symbol)
            return 2
        print("positive control: a symbol beginning %r is attributed, so the "
              "mapping resolves." % a.require_symbol)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("census", help="attribute materialisation sites to symbols")
    c.add_argument("--vmlinux")
    c.add_argument("--listing", help="a saved `objdump -d` listing; with this "
                                     "the tool needs no toolchain")
    c.add_argument("--map", required=True)
    c.add_argument("--objdump", default=None)
    c.add_argument("--reg", action="append", default=[],
                   metavar="LABEL=0xNNNN",
                   help="a register's low half, named")
    c.add_argument("--base", type=lambda s: int(s, 0), default=None,
                   metavar="0xHHHH",
                   help="the address's HIGH half. With it, a site counts only "
                        "when a `lui` of that value into the same register "
                        "sits within %d instructions above it in the same "
                        "symbol. Without it nothing is judged." % PAIR_WINDOW)
    c.add_argument("--block-base", type=lambda s: int(s, 0), default=None,
                   help="the block base's low half; its census is printed as "
                        "the bound on the register censuses' blind spot")
    c.add_argument("--mine", default=None,
                   help="symbol prefix to mark MINE in the listing")
    c.add_argument("--require-symbol", default=None,
                   help="positive control: refuse unless a symbol with this "
                        "prefix is attributed")
    c.set_defaults(fn=cmd_census)

    a = ap.parse_args(argv)
    if a.self_test:
        return run_controls()
    if not a.cmd:
        ap.print_help()
        return 2
    rc = run_controls()
    if rc:
        return rc
    print()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
