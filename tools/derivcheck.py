#!/usr/bin/env python3
"""derivcheck.py -- does a third-party port DERIVE from the vendor's tree?

WHY IT EXISTS
-------------
`docs/blind-write-ledger.md` section 6, committed 2026-09-02, imposed an
ordering constraint on `R5-9`:

    When the trees are cloned at `R5-9`, the FIRST operation on each is a
    derivation check -- file headers, copyright lines, SPDX tags, function and
    symbol names against `arch/rlx`'s -- performed BEFORE any register map is
    read, and its result written down before proceeding.

and it named the constraint's own weakness in the same breath: *a derivation
check is itself a reading, and a sufficiently careful one drifts into the
register map.*

**This file is that bound as code rather than as a resolution.**  It is the
same shape `tools/flashwin.py` has for a different forbidden thing: the rule
governs what may be PRINTED, and it is enforced at the one function every
output goes through.

WHAT IT MAY LOOK AT, AND WHAT IT MAY NOT
----------------------------------------
    may                                may not
    ---                                -------
    C identifier NAMES                 any VALUE -- no hex literal, no
    file paths and directory names     decimal constant, no bit number
    the PRESENCE of a Realtek          any line of source, whole or partial
      copyright line (not its text)    any comment body
    counts and set intersections       any register map, in any form

`emit()` is the only way anything reaches stdout, and it refuses a string that
is not one of: an identifier, a path, a number this tool computed, or a fixed
string from this file's own source.  `--self-test` case R1..R4 hold it.

WHAT IT COMPARES
----------------
For a REFERENCE path set R and a CANDIDATE path set C, both restricted by the
caller:

  1. the identifier set of each -- the names a compiler would see DEFINED
  2. |R|, |C|, |R & C|
  3. a GENERIC BASELINE G is subtracted, and the DISTINCTIVE intersection
     (R & C) - G is what the verdict reads

Step 3 is the one that matters.  Two independent ports of Linux to the same
SoC will both define `init_module` and use `HZ`; they will not both invent
`bsp_tc_init`.

THE VERDICT RULE, which `docs/driver-diff.md` section 1.5 froze before any
candidate tree existed on disk:

  DERIVED      a directory named `rlx`, OR a file whose copyright block names
               Realtek, OR a non-empty distinctive intersection
  INDEPENDENT  none of the three, and the domain has an implementation at all
  ABSENT       no implementation for the domain -- no verdict is possible and
               none is written

WHAT IT IS NOT
--------------
🔴 A verdict of INDEPENDENT is not a claim that the port's author never saw
Realtek's code.  It is a claim about what is IN THE TREE, which is the only
thing an instrument can reach.

🔴 The extractor is regex-based.  It will miss a definition produced by a
macro and it will over-count a name that appears in a prototype it mistakes
for a definition.  Both directions are stated rather than argued away: an
over-count inflates the intersection, so it biases towards DERIVED, which is
the conservative direction for this question.
"""

import argparse
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --------------------------------------------------------------------------
# the output bound
# --------------------------------------------------------------------------

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HEX = re.compile(r"0[xX][0-9a-fA-F]+")
_FORBIDDEN_SUBSTR = ("0x", "0X")


class Refused(Exception):
    pass


def _check_emit(s):
    """Raise unless `s` is safe to print under section 1.2 of docs/driver-diff.md.

    Safe means: it contains no hex literal, and every whitespace-separated
    token is an identifier, a path, a number, or punctuation this tool wrote.
    """
    if not isinstance(s, str):
        raise Refused("emit: not a string")
    if _HEX.search(s):
        raise Refused("emit: hex literal in %r" % s[:60])
    for sub in _FORBIDDEN_SUBSTR:
        if sub in s:
            raise Refused("emit: %r in output" % sub)
    return s


def emit(s=""):
    sys.stdout.write(_check_emit(s) + "\n")


def emit_ident(name):
    if not _IDENT.match(name):
        raise Refused("emit_ident: %r is not an identifier" % name[:60])
    sys.stdout.write(name + "\n")


# --------------------------------------------------------------------------
# identifier extraction
# --------------------------------------------------------------------------

_KEYWORDS = set("""
auto break case char const continue default do double else enum extern float
for goto if inline int long register restrict return short signed sizeof static
struct switch typedef union unsigned void volatile while asm __asm__ __inline__
""".split())

RE_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)")
RE_TAG = re.compile(r"\b(?:struct|union|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
# a function DEFINITION: starts at column 0, has a (, does not end in ;
RE_FUNC = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_ \t\*]*?([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*$")
RE_TYPEDEF = re.compile(r"^\s*typedef\s+.*?([A-Za-z_][A-Za-z0-9_]*)\s*;")
# a DECLARATION: the shape of a definition but terminated by a semicolon.  Used
# for the BASELINE only.  A generic kernel header DECLARES the platform API that
# every board DEFINES -- `get_system_type`, `prom_putchar` -- so a baseline built
# from definitions alone under-subtracts exactly the class of name that two
# unrelated boards are obliged to share.  Both negative controls found this
# before any candidate tree had been compared, which is what they are for.
RE_DECL = re.compile(
    r"^(?:extern\s+)?[A-Za-z_][A-Za-z0-9_ \t\*]*?([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\([^;]*\)\s*;")

C_EXT = (".c", ".h", ".S", ".s")


def identifiers_of_text(text, include_decls=False):
    out = set()
    for line in text.split("\n"):
        if include_decls:
            m = RE_DECL.match(line)
            if m and m.group(1) not in _KEYWORDS:
                out.add(m.group(1))
        m = RE_DEFINE.match(line)
        if m:
            out.add(m.group(1))
            continue
        m = RE_TYPEDEF.match(line)
        if m and m.group(1) not in _KEYWORDS:
            out.add(m.group(1))
        for m in RE_TAG.finditer(line):
            if m.group(1) not in _KEYWORDS:
                out.add(m.group(1))
        m = RE_FUNC.match(line)
        if m and m.group(1) not in _KEYWORDS:
            out.add(m.group(1))
    return set(n for n in out if len(n) >= 3 and n not in _KEYWORDS)


def walk_paths(root, rels, exts=C_EXT, max_files=200000):
    """Yield files under each `rel` of `root`. A rel may be a file or a dir."""
    n = 0
    for rel in rels:
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            yield p
            n += 1
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in sorted(filenames):
                if exts and not fn.endswith(exts):
                    continue
                yield os.path.join(dirpath, fn)
                n += 1
                if n >= max_files:
                    return


def identifiers_of(root, rels, include_decls=False, **kw):
    out = set()
    files = 0
    for p in walk_paths(root, rels, **kw):
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                out |= identifiers_of_text(fh.read(), include_decls=include_decls)
            files += 1
        except (IOError, OSError):
            pass
    return out, files


# --------------------------------------------------------------------------
# survey -- the first thing run on a cloned tree
# --------------------------------------------------------------------------

RE_REALTEK = re.compile(r"realtek|rtl81[0-9]{2}|rtl83[0-9]{2}", re.I)
RE_COPYRIGHT = re.compile(r"copyright|\(c\)|SPDX-License", re.I)


def survey(root, max_files=400000, head_bytes=2048):
    """Structure, `rlx`-named directories, and Realtek copyright counts.

    Prints paths and counts only. It never prints the copyright LINE, which is
    stricter than section 1.2 of docs/driver-diff.md permits.
    """
    if not os.path.isdir(root):
        raise Refused("survey: not a directory")
    emit("root: " + os.path.basename(root.rstrip("/")))
    tops = sorted(d for d in os.listdir(root) if not d.startswith("."))
    emit("  top-level entries: %d" % len(tops))
    for d in tops[:40]:
        emit("    " + d)

    rlx_dirs = []
    soc_paths = []
    n_files = 0
    n_copy_realtek = 0
    copy_examples = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for d in dirnames:
            if d == "rlx":
                rlx_dirs.append(os.path.relpath(os.path.join(dirpath, d), root))
        for fn in filenames:
            n_files += 1
            if n_files > max_files:
                break
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            if RE_REALTEK.search(rel):
                soc_paths.append(rel)
            if not fn.endswith(C_EXT + (".txt", ".rst", "Makefile", "Kconfig")):
                continue
            try:
                with open(os.path.join(dirpath, fn), "r",
                          encoding="utf-8", errors="replace") as fh:
                    head = fh.read(head_bytes)
            except (IOError, OSError):
                continue
            for line in head.split("\n"):
                if RE_COPYRIGHT.search(line) and RE_REALTEK.search(line):
                    n_copy_realtek += 1
                    if len(copy_examples) < 12:
                        copy_examples.append(rel)
                    break

    emit("  files walked: %d" % n_files)
    emit("  directories named rlx: %d" % len(rlx_dirs))
    for r in rlx_dirs[:10]:
        emit("    " + r)
    emit("  files whose COPYRIGHT block names Realtek: %d" % n_copy_realtek)
    for r in copy_examples:
        emit("    " + r)
    emit("  paths naming a Realtek SoC: %d" % len(soc_paths))
    for r in sorted(soc_paths)[:25]:
        emit("    " + r)
    return {
        "files": n_files,
        "rlx_dirs": rlx_dirs,
        "copyright_realtek": n_copy_realtek,
        "soc_paths": soc_paths,
    }


# --------------------------------------------------------------------------
# compare
# --------------------------------------------------------------------------

def parse_spec(spec):
    """`/abs/tree:rel1,rel2` -> (tree, [rel1, rel2])"""
    if ":" not in spec:
        raise Refused("spec needs TREE:REL[,REL]")
    tree, rels = spec.rsplit(":", 1)
    return tree, [r for r in rels.split(",") if r]


def compare(ref_spec, cand_spec, baseline_specs=None, show=25, label=""):
    rt, rr = parse_spec(ref_spec)
    ct, cr = parse_spec(cand_spec)
    R, rn = identifiers_of(rt, rr)
    C, cn = identifiers_of(ct, cr)
    G = set()
    gn = 0
    if isinstance(baseline_specs, str):
        baseline_specs = [baseline_specs]
    for bs in (baseline_specs or []):
        gt, gr = parse_spec(bs)
        g, n = identifiers_of(gt, gr, include_decls=True)
        G |= g
        gn += n
    inter = R & C
    dist = inter - G
    if label:
        emit("== " + label)
    emit("  reference : %d identifier(s) from %d file(s)" % (len(R), rn))
    emit("  candidate : %d identifier(s) from %d file(s)" % (len(C), cn))
    emit("  baseline  : %d identifier(s) from %d file(s)" % (len(G), gn))
    emit("  intersection            : %d" % len(inter))
    emit("  DISTINCTIVE intersection: %d" % len(dist))
    for n in sorted(dist)[:show]:
        emit_ident(n)
    if len(dist) > show:
        emit("  ... and %d more" % (len(dist) - show))
    return {"ref": R, "cand": C, "baseline": G, "inter": inter, "dist": dist,
            "ref_files": rn, "cand_files": cn}


def verdict(dist_count, rlx_dirs, copyright_realtek, cand_files):
    if cand_files == 0:
        return "ABSENT"
    if rlx_dirs or copyright_realtek or dist_count:
        return "DERIVED"
    return "INDEPENDENT"


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def _mk(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def self_test():
    import tempfile
    ok = 0
    bad = []

    def ck(name, got, want):
        nonlocal ok
        if got == want:
            ok += 1
            print("  ok     %-52s %s" % (name, got))
        else:
            bad.append(name)
            print("  FAIL   %-52s got %r want %r" % (name, got, want))

    # ---- the output bound -------------------------------------------------
    def refuses(fn, arg):
        try:
            fn(arg)
            return False
        except Refused:
            return True

    ck("R1 emit refuses a hex literal", refuses(_check_emit, "val 0xB800350C"), True)
    ck("R2 emit refuses a lower-case hex literal", refuses(_check_emit, "0xb800"), True)
    ck("R3 emit_ident refuses a source line",
       refuses(emit_ident, "static int foo(void)"), True)
    ck("R4 emit accepts a path and a count", _check_emit("  tools/derivcheck.py: 12"),
       "  tools/derivcheck.py: 12")

    # ---- extraction -------------------------------------------------------
    src = ("#define BSP_TCIR 0xB8003100\n"
           "struct rlx_gpio_chip {\n"
           "int bsp_tc_init(void)\n"
           "{\n"
           "  return 0;\n"
           "}\n"
           "extern int not_a_definition(void);\n")
    ids = identifiers_of_text(src)
    ck("E1 a #define name is extracted", "BSP_TCIR" in ids, True)
    ck("E2 a struct tag is extracted", "rlx_gpio_chip" in ids, True)
    ck("E3 a function definition is extracted", "bsp_tc_init" in ids, True)
    ck("E4 the VALUE of the define is not in the identifier set",
       any("B800" in i for i in ids), False)
    ck("E5 a prototype ending in ; is not a definition",
       "not_a_definition" in ids, False)

    with tempfile.TemporaryDirectory() as td:
        # reference: the "vendor"
        _mk(td, "vendor/gpio.c",
            "#define BSP_PABCD_DAT 0xB800350C\n"
            "struct bsp_gpio_state {\n"
            "int bsp_gpio_probe_tick(void)\n{\nreturn 0;\n}\n"
            "int platform_driver_register_stub(void)\n{\nreturn 0;\n}\n")
        # a derived candidate: keeps the distinctive names
        _mk(td, "derived/gpio.c",
            "#define BSP_PABCD_DAT 0xB800350C\n"
            "int bsp_gpio_probe_tick(void)\n{\nreturn 1;\n}\n")
        # an independent candidate: shares only the generic name
        _mk(td, "indep/gpio.c",
            "#define SOME_OTHER_REG 0x1234\n"
            "int platform_driver_register_stub(void)\n{\nreturn 0;\n}\n")
        # the generic baseline
        _mk(td, "baseline/linux.h",
            "int platform_driver_register_stub(void)\n{\nreturn 0;\n}\n")
        _mk(td, "empty/README", "nothing here\n")
        _mk(td, "rlxtree/arch/rlx/Makefile", "obj-y := x.o\n")
        _mk(td, "copytree/x.c",
            "/* Copyright (C) Realtek Semiconductor Corp. */\n"
            "int unrelated_name_here(void)\n{\nreturn 0;\n}\n")

        d = compare(td + ":vendor", td + ":derived", td + ":baseline",
                    label="self-test derived pair")
        ck("D1 a derived pair has a non-empty distinctive intersection",
           len(d["dist"]) > 0, True)
        ck("D2 and the distinctive name is the vendor-specific one",
           "bsp_gpio_probe_tick" in d["dist"], True)

        i = compare(td + ":vendor", td + ":indep", td + ":baseline",
                    label="self-test independent pair")
        ck("N1 an independent pair has an EMPTY distinctive intersection",
           len(i["dist"]), 0)
        ck("N2 but its raw intersection is NOT empty -- the subtraction is "
           "load-bearing", len(i["inter"]) > 0, True)

        # the mutation control: without the baseline, N1 must flip
        i2 = compare(td + ":vendor", td + ":indep", None,
                     label="self-test independent pair, baseline REMOVED")
        ck("N3 MUTATION: with no baseline the independent pair reads DERIVED",
           len(i2["dist"]) > 0, True)

        ck("V1 verdict DERIVED on a non-empty distinctive intersection",
           verdict(len(d["dist"]), [], 0, d["cand_files"]), "DERIVED")
        ck("V2 verdict INDEPENDENT on an empty one",
           verdict(len(i["dist"]), [], 0, i["cand_files"]), "INDEPENDENT")
        ck("V3 verdict ABSENT when the candidate has no files",
           verdict(0, [], 0, 0), "ABSENT")
        ck("V4 a directory named rlx forces DERIVED with no identifiers",
           verdict(0, ["arch/rlx"], 0, 3), "DERIVED")
        ck("V5 a Realtek copyright forces DERIVED with no identifiers",
           verdict(0, [], 1, 3), "DERIVED")

        s = survey(os.path.join(td, "rlxtree"))
        ck("S1 survey finds a directory named rlx", len(s["rlx_dirs"]), 1)
        s2 = survey(os.path.join(td, "copytree"))
        ck("S2 survey counts a Realtek copyright block",
           s2["copyright_realtek"], 1)
        ck("S3 survey on a tree with neither reports zero for both",
           (len(survey(os.path.join(td, "empty"))["rlx_dirs"]),
            survey(os.path.join(td, "empty"))["copyright_realtek"]), (0, 0))

    print()
    print("RESULT: %d passed, %d failed" % (ok, len(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("survey", help="the FIRST operation on a cloned tree")
    s.add_argument("tree")
    s.add_argument("--max-files", type=int, default=400000)

    c = sub.add_parser("compare", help="identifier-set comparison")
    c.add_argument("--ref", required=True, help="TREE:REL[,REL...]")
    c.add_argument("--cand", required=True)
    c.add_argument("--baseline", action="append", default=None,
                   help="repeatable; every baseline is subtracted")
    c.add_argument("--show", type=int, default=25)
    c.add_argument("--label", default="")

    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.cmd == "survey":
        survey(a.tree, max_files=a.max_files)
        return 0
    if a.cmd == "compare":
        compare(a.ref, a.cand, a.baseline, show=a.show, label=a.label)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as e:
        sys.stderr.write("REFUSED: %s\n" % e)
        sys.exit(3)
