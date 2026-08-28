#!/usr/bin/env python3
"""rebuild-census -- four channels over one window, and the decision rule applied.

Why this exists, and why it is not just a shell loop
---------------------------------------------------
`R2a/b/d-4` compares programs I built against programs cut out of this unit's
flash dump.  Three instruments already exist for it -- `binsim` (7-gram code
structure), `opcount` (unaligned load/store counts), `hazlint` (load-delay-slot
padding and violations) -- and each has its own controls.  What did NOT exist is
the thing that makes their numbers comparable: **all three have to read the same
window**, and if they do not, an apparent disagreement between channels is an
artefact of three different ideas about where the code is.

The window is `binsim`'s: `[DT_INIT, DT_FINI)` out of `PT_DYNAMIC`.  That choice
is forced, not aesthetic.  Four of the six shipped trees in this corpus have no
section header table at all -- the vendor's romfs step runs `rsdk-linux-lstrip`
over the whole tree (`Makefile:160`) and `rsdk-linux-sstrip` removes them -- so
`.text` cannot be asked for.  The executable `PT_LOAD` is the obvious fallback
and it is wrong: it contains `.rodata`, which a linear scanner reads as code.
`binsim`'s `E4`/`E4b` already certify this window (it equals `.init` through
`.fini` where sections survive, and >= 99 % of the `j`/`jal` words in it target
the executable segment).  This tool points the other two at it.

The second thing it does is apply `notes/which-drop.md` section 6's decision
rule mechanically rather than by eye:

    VOID   the container fingerprint differs from the comparand's
    fail   code containment <= FLOOR
    warn   FLOOR < containment < BASE
    pass   containment >= BASE

`VOID` is not a softer `fail`.  It is there because below the floor the code
channel cannot distinguish "one upstream source built under two compilation
models" from "two programs sharing no source at all" -- `binsim`'s `E8` measures
that: one source across a model change scores 0.1212, BELOW the 0.1551-0.1581
that no-shared-source pairs reach.  So a comparison across a container change
carries no information and must not be reported as a low score.

What every number here is, and is not
-------------------------------------
  * Channels 2 and 3 read four bytes at a time.  That is a SUPERSET of the
    instruction stream: it can read data as code but cannot miss an
    instruction.  **A zero is rigorous; a non-zero is an upper bound.**
  * Channel 3's zero needs a positive control or it means nothing, and this
    corpus supplies one rather than asserting one: the same tool on the same
    window of a `-march=5281` build of the same source returns thousands.  If
    no sample in a run has a non-zero violation count, this tool says so.
  * Nothing here is a measurement on the device.  Every number is read out of a
    file.

Controls
--------
Run first, every invocation; nothing is reported if one fails.  None needs
`$FWRE_WORK`, so a fresh clone still has a control on every part of this file.

  W1  the window this tool hands to the other two equals the window `binsim`
      computes, on a synthetic ELF with a known `[DT_INIT, DT_FINI)`
  W2  the file-offset-to-vaddr base it passes is the one that makes a scanner
      report the true virtual addresses, checked against the ELF's own phdrs
  V1  the verdict function, all four branches, at the boundaries: exactly BASE
      is `pass`, exactly FLOOR is `fail`, between is `warn`, and any container
      difference is `VOID` **whatever the score** -- including a score above
      BASE, which is the branch a reader is most likely to assume away
  V2  the verdict follows the CONTAINER argument, not just the score: the same
      score with and without a fingerprint difference gives different answers
  V3  BASE and FLOOR are read from the manifest that owns them, and a run whose
      thresholds do not match the ones this file was written against says so
      rather than silently using different numbers
  C1  identity: a sample against itself is 1.0 on both channels, `pass`
  C2  a sample against a k-gram-disjoint one is 0.0, `fail`
  S1  section-table removal does not move the code channel.  The window comes
      out of `PT_DYNAMIC`, so it must not -- and this is the control that says
      the four sstripped trees in the corpus are comparable with builds that
      are not sstripped.  Synthetic: the same ELF with and without `e_shoff`.

Usage
    rebuild-census.py --self-test
    rebuild-census.py --against REF FILE [FILE...]
    rebuild-census.py --against REF --dir DIR

Exit
    0  reported, every control held
    1  reported, but at least one comparison is VOID or no positive control for
       channel 3 fired in this run
    2  refused: a control failed, or an input could not be parsed
    3  usage error
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import binsim                                                   # noqa: E402

VERSION = "1.0"

# The thresholds this file was written against.  `notes/which-drop.md` owns
# them and `tools/binsim-corpus.tsv` carries the cells they come from; they are
# repeated here ONLY so that V3 can notice if they move, which is the opposite
# of copying a value to a second place and letting it go stale.
BASE = 0.9818
FLOOR = 0.1581

# The container fields `notes/which-drop.md` section 6 names.
PRECOND = ("e_flags", "phnum", "pltgot", "needed")

OPCOUNT = os.path.join(HERE, "opcount.py")
HAZLINT = os.path.join(HERE, "hazlint")

RE_FOUR = re.compile(r"lwl \+ lwr \+ swl \+ swr = (\d+)")
HAZ_PATS = (("loads", r"loads \(MIPS-I[^)]*\)\s+(\d+)"),
            ("nop", r"followed by an explicit nop\s+(\d+)"),
            ("unres", r"successor unresolved\s+(\d+)"),
            ("viol", r"VIOLATIONS\s+(\d+)"))


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------
# The two things this tool actually decides
# ---------------------------------------------------------------------------

def window_args(sample):
    """(lo, hi, base) -- the arguments that point a raw scanner at binsim's window.

    `opcount --range LO:HI --base B` and `hazlint --raw --range LO:HI --base B`
    both build their span as `(LO, HI-LO, B+LO)`, so B is the vaddr that file
    offset 0 would have.  Getting that wrong does not change a count -- the same
    bytes are read either way -- but it makes every ADDRESS the tools print
    wrong, and those addresses are how a hit gets adjudicated.  W2 pins it.
    """
    return sample.off, sample.off + sample.size, sample.vaddr - sample.off


def verdict(containment, container_differs, base=BASE, floor=FLOOR):
    """notes/which-drop.md section 6, applied.

    The container test comes FIRST and is unconditional.  A rebuild whose
    compilation model differs from the comparand's does not get a score read on
    it at all, however high that score is -- which is why `VOID` is checked
    before `pass` and not after.
    """
    if container_differs:
        return "VOID"
    if containment >= base:
        return "pass"
    if containment <= floor:
        return "fail"
    return "warn"


def container_diff(fp_a, fp_b):
    return [k for k in PRECOND if str(fp_a[k]) != str(fp_b[k])]


# ---------------------------------------------------------------------------
# Channels 2 and 3, driven through the window above
# ---------------------------------------------------------------------------

def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def channel_two(path, lo, hi, base):
    rc, out = _run([sys.executable, OPCOUNT, path,
                    "--range", "0x%x:0x%x" % (lo, hi), "--base", "0x%x" % base])
    m = RE_FOUR.search(out)
    per = {}
    for name in ("lwl", "lwr", "swl", "swr"):
        mm = re.search(r"^\s+0x[0-9a-f]{2}\s+%s\s+(\d+)" % name, out, re.M)
        per[name] = int(mm.group(1)) if mm else None
    return (int(m.group(1)) if (rc == 0 and m) else None), per, rc


def channel_three(path, lo, hi, base):
    rc, out = _run([HAZLINT, path, "--raw", "--base", "0x%x" % base,
                    "--range", "0x%x:0x%x" % (lo, hi)])
    r = {"rc": rc}
    for key, pat in HAZ_PATS:
        mm = re.search(pat, out)
        r[key] = int(mm.group(1)) if mm else None
    return r


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

class Controls(object):
    def __init__(self):
        self.rows = []
        self.failed = []

    def add(self, name, ok, detail=""):
        self.rows.append((name, ok, detail))
        if not ok:
            self.failed.append(name)

    def report(self, out=sys.stdout):
        for name, ok, detail in self.rows:
            out.write("  %-6s %-58s %s\n" % ("ok" if ok else "FAIL", name, detail))
        out.write("  %d control(s), %d failed\n" % (len(self.rows), len(self.failed)))


def _synth(nwords=600, init_i=10, fini_i=500, drop_sections=False):
    """A synthetic ELF with a known [DT_INIT, DT_FINI).  Built through binsim's
    own synth_elf so the two files cannot drift apart on ELF layout."""
    words = [0x00000000] * nwords
    for i in range(nwords):
        # plausible-looking MIPS: addiu / lw / sw / nop, deterministic
        words[i] = (0x24420000, 0x8C430000, 0xAC440000, 0x00000000)[i % 4]
    blob = binsim.synth_elf(words, init_off=init_i, fini_off=fini_i)
    if drop_sections:
        blob = bytearray(blob)
        blob[32:36] = b"\x00\x00\x00\x00"       # e_shoff
        blob[48:50] = b"\x00\x00"               # e_shnum
        blob = bytes(blob)
    return blob


def run_controls():
    c = Controls()

    # -- W1 / W2 -----------------------------------------------------------
    try:
        blob = _synth()
        s = binsim.Sample(blob=blob, name="synth")
        lo, hi, base = window_args(s)
        c.add("W1  the window handed to opcount/hazlint is binsim's",
              (lo, hi - lo) == (s.off, s.size),
              "file[0x%x..0x%x) = %d words" % (lo, hi, (hi - lo) // 4))
        c.add("W2  --base is the vaddr of file offset 0",
              base + s.off == s.vaddr,
              "0x%x + 0x%x = 0x%x" % (base, s.off, s.vaddr))
    except Exception as ex:                                   # noqa: BLE001
        c.add("W1  the window handed to opcount/hazlint is binsim's", False, repr(ex))
        c.add("W2  --base is the vaddr of file offset 0", False, "not reached")

    # -- V1: every branch, at the boundary ---------------------------------
    cases = [
        (BASE, False, "pass"), (BASE + 1e-9, False, "pass"),
        (FLOOR, False, "fail"), (FLOOR - 1e-9, False, "fail"),
        ((BASE + FLOOR) / 2, False, "warn"),
        (0.99, True, "VOID"), (0.10, True, "VOID"), (1.0, True, "VOID"),
    ]
    bad = [(v, d, want, verdict(v, d)) for v, d, want in cases
           if verdict(v, d) != want]
    c.add("V1  the verdict function, all four branches at the boundary",
          not bad, "8 cases" if not bad else repr(bad[:2]))

    # -- V2: it follows the container argument, not only the score ---------
    mid = (BASE + FLOOR) / 2
    c.add("V2  the verdict follows the CONTAINER argument",
          verdict(mid, False) == "warn" and verdict(mid, True) == "VOID"
          and verdict(1.0, True) == "VOID" and verdict(1.0, False) == "pass",
          "same score, both ways, incl. a perfect score with a changed container")

    # -- V3: the thresholds are the ones the manifest names ----------------
    #
    # The first version of this control printed what it had parsed and passed
    # unconditionally.  That is a control that cannot fail, which this project
    # has a rule about.  BASE and FLOOR above are NUMBERS copied out of a run;
    # the manifest owns the CELLS they came from, and a cell can be re-pointed
    # (`@floor` has been, twice).  So the check is on the cells: if the manifest
    # names a different pair than the ones these numbers were read on, the
    # numbers are stale and this says so instead of quietly using them.
    WANT_BASE = ("boa", "unit-2018", "boa", "n200re-3.2.0")
    WANT_FLOOR = ("boa", "unit-2018", "busybox", "unit-2018")
    try:
        man = binsim.Manifest(os.path.join(HERE, "binsim-corpus.tsv"))
        got_base = tuple(getattr(man, "base", ()) or ())
        got_floor = tuple(getattr(man, "floor", ()) or ())
        ok = (got_base == WANT_BASE and got_floor == WANT_FLOOR)
        c.add("V3  BASE/FLOOR are read on the cells the manifest still names",
              ok,
              ("@base %s  @floor %s" % ("/".join(got_base), "/".join(got_floor)))
              if ok else
              ("MOVED: manifest says @base %s @floor %s; the numbers in this "
               "file were read on %s / %s"
               % ("/".join(got_base) or "(absent)", "/".join(got_floor) or "(absent)",
                  "/".join(WANT_BASE), "/".join(WANT_FLOOR))))
    except Exception as ex:                                   # noqa: BLE001
        c.add("V3  BASE/FLOOR are read on the cells the manifest still names",
              False, repr(ex))

    # -- C1 / C2 -----------------------------------------------------------
    try:
        a = binsim.Sample(blob=_synth(), name="a")
        cc, jj = binsim.score(a, a)[:2]
        c.add("C1  a sample against itself is 1.0 and passes",
              cc == 1.0 and jj == 1.0 and verdict(cc, False) == "pass",
              "C=%.4f J=%.4f" % (cc, jj))
    except Exception as ex:                                   # noqa: BLE001
        c.add("C1  a sample against itself is 1.0 and passes", False, repr(ex))

    try:
        g1 = set(range(1000))
        g2 = set(range(1000, 2000))
        cc = binsim.measures(g1, g2)[0]
        c.add("C2  k-gram-disjoint scores 0.0 and fails",
              cc == 0.0 and verdict(cc, False) == "fail", "C=%.4f" % cc)
    except Exception as ex:                                   # noqa: BLE001
        c.add("C2  k-gram-disjoint scores 0.0 and fails", False, repr(ex))

    # -- S1: sstrip invariance ---------------------------------------------
    try:
        full = binsim.Sample(blob=_synth(), name="with-sections")
        cut = binsim.Sample(blob=_synth(drop_sections=True), name="no-sections")
        cc, jj = binsim.score(full, cut)[:2]
        same_window = (full.off, full.size) == (cut.off, cut.size)
        c.add("S1  removing the section table does not move the code channel",
              cc == 1.0 and jj == 1.0 and same_window,
              "C=%.4f J=%.4f, window %s"
              % (cc, jj, "identical" if same_window else "MOVED"))
    except Exception as ex:                                   # noqa: BLE001
        c.add("S1  removing the section table does not move the code channel",
              False, repr(ex))

    return c


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(ref_path, paths, out=sys.stdout):
    ref = binsim.Sample(ref_path, name=os.path.basename(ref_path))
    rfp = ref.elf.fingerprint()
    rlo, rhi, rbase = window_args(ref)

    out.write("\ncomparand   %s\n" % ref_path)
    out.write("            %d bytes, window %d words at file 0x%x, vaddr 0x%x\n"
              % (len(ref.blob), ref.size // 4, ref.off, ref.vaddr))
    out.write("            %s | phnum %s | pltgot %s | needed %s\n"
              % (rfp["e_flags"], rfp["phnum"], rfp["pltgot"], rfp["needed"]))
    out.write("            |G(7)| = %d  <- the denominator every containment below is read on\n"
              % len(ref.grams(7)))
    out.write("            thresholds BASE %.4f  FLOOR %.4f\n" % (BASE, FLOOR))

    rows = []
    for p in [ref_path] + list(paths):
        try:
            s = binsim.Sample(p, name=os.path.basename(p))
        except binsim.Refused as ex:
            out.write("  REFUSED %s: %s\n" % (p, ex))
            continue
        fp = s.elf.fingerprint()
        lo, hi, base = window_args(s)
        four, per, oprc = channel_two(p, lo, hi, base)
        haz = channel_three(p, lo, hi, base)
        cc, jj = binsim.score(s, ref)[:2]
        sc = binsim.score_strings(s, ref)[0]
        diff = container_diff(fp, rfp)
        rows.append(dict(path=p, name=os.path.basename(p), s=s, fp=fp, four=four,
                         per=per, haz=haz, c=cc, j=jj, sc=sc, diff=diff,
                         verdict=verdict(cc, bool(diff))))

    out.write("\n== channel 1 (binsim, code) and the decision rule\n")
    out.write("%-34s %8s %8s %8s  %-6s %s\n"
              % ("sample", "code-C", "code-J", "str-C", "rule", "container fields differing"))
    for r in rows:
        out.write("%-34s %8.4f %8.4f %8.4f  %-6s %s\n"
                  % (r["name"][:34], r["c"], r["j"], r["sc"], r["verdict"],
                     ",".join(r["diff"]) if r["diff"] else "-"))

    out.write("\n== channel 4 (container) and channel 2 (unaligned load/store)\n")
    out.write("%-34s %8s %5s %5s  %-30s %-38s %6s\n"
              % ("sample", "words", "ph", "sect", "e_flags", "DT_NEEDED", "lwl4"))
    for r in rows:
        out.write("%-34s %8d %5s %5s  %-30s %-38s %6s\n"
                  % (r["name"][:34], r["s"].size // 4, r["fp"]["phnum"],
                     r["fp"]["sections"], r["fp"]["e_flags"],
                     r["fp"]["needed"][:38], r["four"]))

    out.write("\n== channel 3 (hazlint, load-delay-slot), same window\n")
    out.write("%-34s %9s %9s %8s %9s %8s\n"
              % ("sample", "loads", "nop", "nop%", "violations", "unres"))
    for r in rows:
        h = r["haz"]
        pct = ("%.2f" % (100.0 * h["nop"] / h["loads"])) if h.get("loads") else "-"
        out.write("%-34s %9s %9s %8s %9s %8s\n"
                  % (r["name"][:34], h["loads"], h["nop"], pct, h["viol"], h["unres"]))

    # The zero on channel 3 is a claim.  Say whether anything in this run could
    # have made it fire.
    fired = [r["name"] for r in rows if (r["haz"].get("viol") or 0) > 0]
    out.write("\n  channel 3 positive control: %s\n"
              % ("%d sample(s) DID report violations (%s), so a zero here is a "
                 "reading" % (len(fired), ", ".join(fired[:3]))
                 if fired else
                 "NOTHING in this run reported a violation. A zero is therefore "
                 "NOT LOOKED FOR rather than NOT THERE -- put a -march=5281 "
                 "build of the same source in the run to supply one."))

    voids = [r for r in rows if r["verdict"] == "VOID"]
    if voids:
        out.write("  %d comparison(s) VOID: the container differs, so the code "
                  "channel carries no\n  information about shared source "
                  "(binsim E8).\n" % len(voids))
    return 1 if (voids or not fired) else 0


def main(argv):
    ref = None
    files = []
    mode = "report"
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--self-test":
            mode = "self-test"; i += 1
        elif a == "--against":
            if i + 1 >= len(argv):
                sys.stderr.write("--against needs a path\n"); return 3
            ref = argv[i + 1]; i += 2
        elif a == "--dir":
            if i + 1 >= len(argv):
                sys.stderr.write("--dir needs a path\n"); return 3
            d = argv[i + 1]; i += 2
            files += [os.path.join(d, n) for n in sorted(os.listdir(d))]
        elif a in ("-h", "--help"):
            sys.stdout.write(__doc__); return 0
        elif a.startswith("-"):
            sys.stderr.write("unknown argument %s\n" % a); return 3
        else:
            files.append(a); i += 1

    sys.stdout.write("rebuild-census %s -- controls first, results after\n" % VERSION)
    c = run_controls()
    c.report()
    if c.failed:
        sys.stdout.write("\nREFUSED: a control failed, so nothing is reported.\n")
        return 2
    if mode == "self-test":
        return 0
    if ref is None:
        sys.stderr.write("give --against REF, or --self-test\n"); return 3
    if not os.path.exists(ref):
        sys.stderr.write("%s: no such file -- this tool will not substitute another "
                         "comparand\n" % ref); return 3
    if not files:
        sys.stderr.write("give at least one file, or --dir\n"); return 3
    try:
        return report(ref, files)
    except binsim.Refused as ex:
        sys.stderr.write("rebuild-census: refused: %s\n" % ex)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
