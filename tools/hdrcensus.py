#!/usr/bin/env python3
"""hdrcensus.py -- the ASIC register population, taken from the vendor
header's DECLARATIONS, and crossed against every address this repository has
ever read.

WHY THIS EXISTS, AND IT IS NOT THE TOOL ITS NAME NEARLY WAS
-----------------------------------------------------------
🔴 `tools/regcensus.py` already exists (added `bebf51d`, 2026-09-10, in CI,
green) and it is a DIFFERENT instrument: *which symbols in an image
materialise a given register address*, counted off a disassembly and
attributed through `System.map`.  It was built for `R5-7`'s GPIO write mask.

`PROGRESS.md` §Now nevertheless says *"`regcensus` 沒有以工具的形式提交到
`tools/`"* and `R6-0`'s DoD says its code side is *"`regcensus` over the
vendor's Ethernet driver"*.  Both sentences are about a DIFFERENT census -- the
one whose untracked prototype produced `606 = 606` -- and the committed
`regcensus` reads no C header at all.  量 2026-09-17: that is an **id
collision**, the second this project has recorded (the first was `NET-14`,
2026-09-06), and it is the more misleading of the two, because this time the
colliding name is a tracked tool that is green in CI -- so a reader who greps
`tools/` concludes the debt is paid.  This tool therefore does NOT reuse the
name, and says so here rather than in a commit message nobody greps.

WHAT IT IS FOR
--------------
🔴🔴 The finding that made it necessary.  `SPEC.md` `NET-21` derives this
project's switch-register population from **48 `lui …,0xbb80` sites in the
loader**, converging on 13 distinct addresses.  That is *what one agent
touched*.  It is not *what configures the switch*.  量 2026-09-17: three
registers named directly by `R6-2`'s own definition -- `MSCR` (the
acceleration master switch), `VCR0` (the 802.1Q-unaware bit) and `SWTCR1` --
are absent from that population **because the loader never writes them**, and
have never been read on this die in either state.

**A census whose population is one agent's behaviour is blind to everything
that agent ignores.**  `tccensus` had to state the same shape one level down
(*a population derived from the record cannot see a fact measured and never
written down*).  This tool takes the population from the DECLARATION side, so
the gap becomes a number instead of a surprise.

THE CORRECTNESS PROPERTY, WHICH IS THE `#if` HANDLING
-----------------------------------------------------
🔴 `rtl865xc_asicregs.h` defines `PCRP`'s bit positions TWICE, under
`#if defined(CONFIG_RTL_8196E) …` and `#else`, **with different values** --
`EnLoopBack` is bit 7 in one branch and bit 10 in the other.  A `grep`-shaped
census takes both and produces a field map that is wrong for whichever part
you are holding.  So this tool evaluates the conditionals for a named config
set, and reports when a name is defined in more than one live branch instead
of silently keeping the last one.

That is also why `-D` is required rather than defaulted: the answer depends on
which chip you asked about, and a tool that guesses hides that.

WHAT IT DOES NOT DO, STATED SO A CLEAN TABLE IS NOT READ AS MORE
-----------------------------------------------------------------
1. It does not attribute BIT-FIELD defines to their register.  The header
   groups them under `/* REG - description */` comments, and a rule over that
   would be a guess dressed as a parse.  Bit defines are counted and
   classified; they are not claimed.
2. `cover` answers *has any committed file ever printed this address*.  That is
   **not** the same as *this register has been read on the die* -- a card that
   merely NAMES an address counts.  It is a coverage upper bound, and `K9` is
   the control that stops the matcher from reaching everything.
3. It reads a header.  It says nothing about whether the silicon agrees with
   it, and this project has one measured instance where it does not
   (`PCRP5`/`0xBB804118`: the header names it, the die reads `00000000`).
"""

import argparse
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The MMIO windows this part decodes.  An expression resolving outside them is
#: not an address, whatever it looks like -- that is what keeps `0x80000001`
#: (a revision constant) out of the register map.
MMIO = ((0xB8000000, 0xB8100000), (0xBB000000, 0xBB900000))

DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s*(?:\(\s*\w+\s*\))?\s*(.*)$")
COND = re.compile(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b\s*(.*)$")
#: An expression we are willing to evaluate.  Anything outside this character
#: set is refused rather than guessed at -- `eval` never sees a token this did
#: not pass.
SAFE = re.compile(r"^[\s0-9A-Za-z_()+\-*<>|&~^]*$")
HEXTOK = re.compile(r"(?<![0-9A-Za-z_])(?:0[xX])?([0-9A-Fa-f]{8})(?![0-9A-Za-z_])")


def strip_comments(text):
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            # A block comment spanning lines must not eat the newlines, or
            # every #define after it moves and the line numbers this tool
            # reports become fiction.
            out.append("\n" * text.count("\n", i, (j + 2) if j >= 0 else n))
            i = (j + 2) if j >= 0 else n
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = j if j >= 0 else n
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def comments_of(text):
    """-> {lineno: comment text}.  A separate pass rather than threading the
    comment through the parser, because the parser's job is the branch tree
    and mixing the two makes both harder to control."""
    out, i, n, line = {}, 0, len(text), 1
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = (j + 2) if j >= 0 else n
            out.setdefault(line, "")
            out[line] += " " + text[i + 2:j - 2]
            line += text.count("\n", i, j)
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = j if j >= 0 else n
            out.setdefault(line, "")
            out[line] += " " + text[i + 2:j]
            i = j
        else:
            if text[i] == "\n":
                line += 1
            i += 1
    return out


#: A collision the header declares on purpose says so, in the comment.  量:
#: `#define OCR L4TOCR /* Alias Name */`.
ALIAS = re.compile(r"alias", re.I)


def classify_collision(names, comments):
    """-> 'base' | 'alias' | 'UNDECLARED'.

    'base' is a block base sharing an address with its first register, which
    is how this header is written throughout and is not a defect.
    'alias' is a second spelling the header itself labels.
    'UNDECLARED' is two register names at one address with nothing saying they
    are the same register -- which is the only one of the three worth a
    reader's time, and the class `BISTTSDR0`/`BISTTSDR1` falls in.
    """
    if any(n.endswith("_BASE") for n, _ln in names):
        return "base"
    if any(ALIAS.search(comments.get(ln, "")) for _n, ln in names):
        return "alias"
    return "UNDECLARED"


def cond_value(expr, defined):
    """Evaluate a `#if` expression over `defined(X)`, `!`, `&&`, `||`."""
    e = re.sub(r"defined\s*\(\s*([A-Za-z_]\w*)\s*\)",
               lambda m: "1" if m.group(1) in defined else "0", expr)
    e = re.sub(r"defined\s+([A-Za-z_]\w*)",
               lambda m: "1" if m.group(1) in defined else "0", e)
    # Any bare identifier left is an undefined macro, which C treats as 0.
    e = re.sub(r"(?<![0-9A-Za-z_])([A-Za-z_]\w*)(?![0-9A-Za-z_])", "0", e)
    e = e.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    if not re.fullmatch(r"[\s0-9()anotr\-+<>=andor]*", e.replace("not", "")
                        .replace("and", "").replace("or", "")):
        return None
    try:
        return bool(eval(e, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return None


def defines(text, defined):
    """-> [(lineno, name, expr)] for every #define in a LIVE branch.

    `stack` holds one entry per open conditional: (live_now, any_taken_yet).
    """
    out, stack = [], []
    for lineno, raw in enumerate(strip_comments(text).splitlines(), 1):
        m = COND.match(raw)
        if m:
            kind, rest = m.group(1), m.group(2).strip()
            if kind in ("if", "ifdef", "ifndef"):
                if kind == "ifdef":
                    v = rest.split()[0] in defined if rest else False
                elif kind == "ifndef":
                    v = rest.split()[0] not in defined if rest else False
                else:
                    v = cond_value(rest, defined)
                    v = False if v is None else v
                stack.append((v, v))
            elif kind == "elif":
                if stack:
                    _live, taken = stack[-1]
                    v = cond_value(rest, defined)
                    v = False if v is None else v
                    stack[-1] = ((not taken) and v, taken or v)
            elif kind == "else":
                if stack:
                    _live, taken = stack[-1]
                    stack[-1] = (not taken, True)
            elif kind == "endif":
                if stack:
                    stack.pop()
            continue
        if all(live for live, _ in stack):
            m = DEFINE.match(raw)
            if m and m.group(2).strip():
                out.append((lineno, m.group(1), m.group(2).strip()))
    return out


def resolve(decls):
    """Substitute names into expressions until nothing more resolves.

    Returns (values, unresolved).  A name defined more than once in live
    branches keeps its FIRST definition and is reported by the caller -- it is
    a finding, not a tie to break quietly.
    """
    exprs, first, order = {}, {}, []
    dupes = []
    for lineno, name, expr in decls:
        if name in exprs:
            dupes.append((name, first[name], lineno))
            continue
        exprs[name], first[name] = expr, lineno
        order.append(name)

    vals = {}
    for _ in range(24):                      # depth bound; the real chain is 3
        progress = False
        for name in order:
            if name in vals:
                continue
            e = exprs[name]
            if not SAFE.match(e):
                continue
            sub = re.sub(r"(?<![0-9A-Za-z_])([A-Za-z_]\w*)(?![0-9A-Za-z_])",
                         lambda m: (str(vals[m.group(1)])
                                    if m.group(1) in vals else m.group(0)), e)
            # 🔴 Do NOT test "does a letter remain" to decide whether an
            # identifier is still unresolved: `0xBB800000` is all letters after
            # the prefix is stripped, so that test rejects every address on
            # this part and the whole census comes back empty.  量 -- it did,
            # and K1..K4 are what said so.  An unresolved name is a NameError
            # and a C cast is a SyntaxError; both are exactly the signal.
            try:
                vals[name] = eval(sub, {"__builtins__": {}}, {}) & 0xFFFFFFFF
            except Exception:
                continue
            progress = True
        if not progress:
            break
    return vals, first, dupes, set(order) - set(vals)


def is_addr(v):
    return any(lo <= v < hi for lo, hi in MMIO)


def census(text, defined):
    decls = defines(text, defined)
    vals, first, dupes, unresolved = resolve(decls)
    regs, bits = {}, []
    for name, v in vals.items():
        if is_addr(v):
            regs.setdefault(v, []).append((name, first[name]))
        else:
            bits.append(name)
    return regs, bits, dupes, unresolved, len(decls)


# --------------------------------------------------------------------------
# coverage: which of those addresses has any committed file ever printed
# --------------------------------------------------------------------------

def tracked_text():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                             capture_output=True, text=True,
                             encoding="utf-8").stdout.split("\n")
    except Exception:
        return ""
    blobs = []
    for rel in out:
        if not rel or rel.startswith("upstream/"):
            continue
        if not rel.endswith((".md", ".log", ".tsv", ".json", ".txt")):
            continue
        p = os.path.join(ROOT, rel)
        try:
            blobs.append(open(p, encoding="utf-8", errors="replace").read())
        except OSError:
            pass
    return "\n".join(blobs)


def seen_addresses(text):
    return {int(m.group(1), 16) for m in HEXTOK.finditer(text)}


# --------------------------------------------------------------------------
# self-test.  Every case is synthetic, so this runs anywhere python does and
# declares no skip.
# --------------------------------------------------------------------------

#: A fixture that reproduces the vendor header's OWN base chain verbatim.  It
#: is synthetic -- the text lives here -- but the address it must produce,
#: `0xBB804234`, was measured on the die at `bench/2026-09-17b/C3-SW234`
#: before any tool resolved it.  That is what stops this suite from being a
#: tool agreeing with itself.
CHAIN = """
#define REAL_SWCORE_BASE 0xBB800000
#if defined(RTL865X_TEST)
#define SWCORE_BASE ((uint32)pVirtualSWReg)
#else
#define SWCORE_BASE REAL_SWCORE_BASE
#endif
#define SWMISC_BASE (0x4200+SWCORE_BASE)
#define CVIDR (0x00+SWMISC_BASE)
#define SSIR (0x04+SWMISC_BASE)
#if defined(CONFIG_RTL_819XD) || defined(CONFIG_RTL_8196E)
#define MEMCR (0x34+SWMISC_BASE)
#endif
#define SwitchFullRst (1 << 2)
"""

BRANCH = """
#if defined(CONFIG_RTL_8196E)
#define EnLoopBack (1<<7)
#define PCRP0 0xBB804104
#else
#define EnLoopBack (1<<10)
#define PCRP0 0xBB804204
#endif
"""

E8196E = {"CONFIG_RTL_8196E"}


def case(ok, cid, msg, tally):
    print("  %s  %-10s %s" % ("ok  " if ok else "FAIL", cid, msg))
    tally[0 if ok else 1] += 1
    return ok


def self_test():
    t = [0, 0]

    vals = resolve(defines(CHAIN, E8196E))[0]
    case(vals.get("MEMCR") == 0xBB804234, "K1",
         "the base chain resolves MEMCR to 0xBB804234, the address measured "
         "on this die (got %s)"
         % ("0x%08X" % vals["MEMCR"] if "MEMCR" in vals else "nothing"), t)

    case(vals.get("SSIR") == 0xBB804204 and vals.get("CVIDR") == 0xBB804200,
         "K2", "two adjacent registers resolve distinctly (CVIDR/SSIR)", t)

    # K3/K4 are the pair.  A tool that ignores #if passes ONE of them.
    a = resolve(defines(BRANCH, E8196E))[0]
    case(a.get("EnLoopBack") == (1 << 7) and a.get("PCRP0") == 0xBB804104,
         "K3", "with CONFIG_RTL_8196E the 8196E branch is taken", t)
    b = resolve(defines(BRANCH, set()))[0]
    case(b.get("EnLoopBack") == (1 << 10) and b.get("PCRP0") == 0xBB804204,
         "K4", "without it the #else branch is taken -- the half that fails "
         "if conditionals are ignored", t)

    # K5: the #else of a taken #if must NOT also be live.
    both = defines(BRANCH, E8196E)
    case(len([1 for _l, n, _e in both if n == "EnLoopBack"]) == 1, "K5",
         "a name defined in both branches appears ONCE, not twice", t)

    dup = "#define A 0xBB804000\n#define A 0xBB804004\n"
    case(len(resolve(defines(dup, set()))[2]) == 1, "K6",
         "a name redefined in one live branch is reported, not silently "
         "overwritten", t)

    regs, bits, _d, _u, _n = census(CHAIN, E8196E)
    case("SwitchFullRst" in bits and all("SwitchFullRst" not in
                                         [nm for nm, _ln in v]
                                         for v in regs.values()),
         "K7", "a bit define (1<<2) is classified as a bit, not an address", t)

    case(not is_addr(0x80000001) and is_addr(0xBB804410) and
         is_addr(0xB8010000), "K8",
         "the MMIO window admits 0xB8010000/0xBB804410 and rejects "
         "0x80000001 (a revision constant)", t)

    # K9 is the control on the COVERAGE matcher.  Without it `cover` could
    # report everything covered and never fail.
    probe = "text 0xBB804234 and bb804418 and 0XBB804A08 here"
    got = seen_addresses(probe)
    case({0xBB804234, 0xBB804418, 0xBB804A08} <= got and
         0xBB804410 not in got, "K9",
         "the address matcher is case-insensitive, 0x-optional, AND misses an "
         "address that is not there", t)

    case(0xBB804234 not in seen_addresses("0xBB8042345"), "K10",
         "the matcher does not match inside a longer hex run", t)

    nl = strip_comments("#define A 1 /* c\nc */\n#define B 2\n")
    case(nl.splitlines()[2].strip() == "#define B 2", "K11",
         "a multi-line block comment preserves line numbers", t)

    case(cond_value("defined(X) && !defined(Y)", {"X"}) is True and
         cond_value("defined(X) && !defined(Y)", {"X", "Y"}) is False,
         "K12", "conditional expressions handle && and ! in both directions",
         t)

    ell = ("#if defined(A)\n#define V 1\n#elif defined(B)\n#define V 2\n"
           "#else\n#define V 3\n#endif\n")
    case(resolve(defines(ell, {"B"}))[0].get("V") == 2 and
         resolve(defines(ell, set()))[0].get("V") == 3 and
         resolve(defines(ell, {"A", "B"}))[0].get("V") == 1, "K13",
         "#elif picks exactly one arm, in all three directions", t)

    nest = ("#if defined(A)\n#if defined(B)\n#define V 1\n#endif\n"
            "#define W 2\n#endif\n")
    case(resolve(defines(nest, {"A"}))[0].get("W") == 2 and
         "V" not in resolve(defines(nest, {"A"}))[0] and
         "W" not in resolve(defines(nest, {"B"}))[0], "K14",
         "nested conditionals gate independently", t)

    case(not SAFE.match('"a string"') and SAFE.match("(0x34+BASE)"), "K15",
         "an expression outside the safe character set is refused, not "
         "evaluated", t)

    # K16/K17 are the pair that makes the collision report worth reading.  A
    # classifier with no UNDECLARED branch would pass K16 alone.
    ctext = ("#define FOO_BASE 0xBB804400\n"
             "#define FIRST (0x00+FOO_BASE)\n"
             "#define OCR L4TOCR /* Alias Name */\n"
             "#define BIST0 (0x38+FOO_BASE)\n"
             "#define BIST1 (0x38+FOO_BASE)\n")
    cm = comments_of(ctext)
    case(classify_collision([("FOO_BASE", 1), ("FIRST", 2)], cm) == "base" and
         classify_collision([("OCR", 3), ("X", 99)], cm) == "alias", "K16",
         "a block base and a labelled alias are not reported as defects", t)
    case(classify_collision([("BIST0", 4), ("BIST1", 5)], cm) == "UNDECLARED",
         "K17",
         "two register names at one address with nothing labelling them ARE "
         "reported -- the BISTTSDR0/BISTTSDR1 class", t)

    case(comments_of("#define A 1 /* x\ny */\n#define B 2 /* z */\n")
         .get(3, "").strip() == "z", "K18",
         "a comment is attributed to its own line across a multi-line "
         "predecessor", t)

    print("%d of %d ok" % (t[0], t[0] + t[1]))
    return 1 if t[1] else 0


# --------------------------------------------------------------------------


def report(args):
    if not os.path.exists(args.header):
        print("REFUSING: no such header: %s" % args.header, file=sys.stderr)
        print("  It lives under src-vendor/, which is a symlink into "
              "$FWRE_WORK and is not committed.", file=sys.stderr)
        return 2
    text = open(args.header, encoding="utf-8", errors="replace").read()
    regs, bits, dupes, unresolved, ndecl = census(text, set(args.define))

    if not regs:
        print("REFUSING: the population is empty -- %d defines, 0 addresses. "
              "A census reporting nothing is not a result." % ndecl,
              file=sys.stderr)
        return 2

    seen = seen_addresses(tracked_text()) if args.mode == "cover" else None

    print("hdrcensus 1.0  --  %s" % os.path.relpath(args.header))
    print("config: %s" % (" ".join(sorted(args.define)) or "(none)"))
    print("%d defines in live branches -> %d addresses, %d bit/mask, "
          "%d unresolved" % (ndecl, len(regs), len(bits), len(unresolved)))
    if dupes:
        print("🔴 %d name(s) defined more than once in a live branch:" %
              len(dupes))
        for name, a, b in sorted(dupes):
            print("     %-28s first :%d, again :%d" % (name, a, b))

    cmts = comments_of(text)
    collide = {a: v for a, v in regs.items() if len(v) > 1}
    if collide:
        buckets = {}
        for a, v in collide.items():
            buckets.setdefault(classify_collision(v, cmts), []).append(a)
        print("%d address(es) carry more than one name: %s"
              % (len(collide), ", ".join(
                  "%d %s" % (len(v), k) for k, v in sorted(buckets.items()))))
        print("     base  = a block base sharing an address with its first")
        print("             register -- how this header is written throughout")
        print("     alias = a second spelling the header itself labels")
        for a in sorted(buckets.get("UNDECLARED", [])):
            print("  🔴 0x%08X  %s" % (a, ", ".join(
                "%s(:%d)" % (n, ln) for n, ln in sorted(collide[a]))))

    if args.mode == "cover":
        unread = sorted(a for a in regs if a not in seen)
        print()
        print("COVERAGE -- addresses this repository has ever printed")
        print("  declared %d   printed %d   NOT printed %d (%.1f %%)"
              % (len(regs), len(regs) - len(unread), len(unread),
                 100.0 * len(unread) / len(regs)))
        print("  ⚠ 'printed' is an upper bound: a card that merely NAMES an")
        print("    address counts.  It is not 'read on the die'.")
        if args.window:
            lo, hi = args.window
            sel = [a for a in unread if lo <= a < hi]
            print()
            print("  never printed, inside 0x%08X..0x%08X: %d"
                  % (lo, hi, len(sel)))
            for a in sel:
                print("    0x%08X  %s" % (a, ", ".join(
                    n for n, _ln in sorted(regs[a]))))
    else:
        for a in sorted(regs):
            print("  0x%08X  %s" % (a, ", ".join(
                "%s(:%d)" % (n, ln) for n, ln in sorted(regs[a]))))
    return 0


def hexpair(s):
    lo, _, hi = s.partition("..")
    return (int(lo, 16), int(hi, 16))


def main(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("mode", nargs="?", default="census",
                   choices=("census", "cover"))
    p.add_argument("--header", default=os.path.join(
        ROOT, "src-vendor", "rtl819x-toolchain", "linux-2.6.30", "drivers",
        "net", "rtl819x", "AsicDriver", "rtl865xc_asicregs.h"))
    p.add_argument("-D", "--define", action="append", default=[],
                   help="a config macro to treat as defined; REQUIRED, "
                        "because the header's branches disagree")
    p.add_argument("--window", type=hexpair, default=None,
                   help="LO..HI, restrict the cover listing to a range")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv[1:])

    if a.self_test:
        print("hdrcensus 1.0  --  self-test")
        return self_test()
    if not a.define:
        print("REFUSING: no -D given.  This header defines PCRP's bit "
              "positions twice with different values; without a config set "
              "the answer is not wrong, it is meaningless.", file=sys.stderr)
        return 2
    return report(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
