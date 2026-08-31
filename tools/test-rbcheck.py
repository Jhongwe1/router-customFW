#!/usr/bin/env python3
"""test-rbcheck -- the mutation suite for tools/rbcheck.py.

Every mutation below must make --self-test exit non-zero.  A mutation that
survives is a control that does not work, which is the finding an adversarial
pass returned against the first version of this suite: it reported 10/10 while
four mutations lived, two of them deleting exactly what the tool advertises.

Two rows here are not mutations, and both were added on 2026-08-31 because the
suite reported 15/15 while one of the fifteen was killing the wrong thing:

  B0  THE UNMUTATED TOOL MUST PASS IN THE TEMP TREE.  A tree that is missing a
      capture, or a `.c` the controls re-read, makes the baseline red -- and a
      red baseline kills every mutation for free.  `test-replay-capture-mutants`
      reported 14/14 to exactly that, one day before this row existed, and the
      root check here (`cwd=ROOT`) cannot see it because ROOT is complete by
      construction.

  W0  A KILL IS ONLY VALID IF IT TURNED THE NAMED CASE RED.  A non-zero exit
      says *something* went wrong, and a mutation that makes the tool crash
      before it reaches its controls exits non-zero too.  Every row that names
      a case -- `(kills C25)` -- now has to find `FAIL  C25` in the mutated
      run's own output, and a row that kills for a different reason is reported
      `WRONG-CASE` rather than counted, which is `test-flrbracket-mutants`'s
      rule brought one tool over.

  A0  EVERY ANCHOR MUST OCCUR EXACTLY ONCE.  `str.replace(old, new, 1)` takes
      the FIRST match, so an anchor that becomes ambiguous silently starts
      mutating a different place.  量 2026-08-31: Group F gave rbcheck.py a
      second `if magic == 0x524C5833 and count > 50:` and M26 -- written for
      the retained-bitmap branch -- began mutating Group F's guard instead.  It
      still exited non-zero, so it still read as *killed*, and nothing could
      tell.  An ambiguous anchor is now a FAILURE of the suite, not a survivor
      and not a pass: the mutation is broken, which is a different thing from
      the control being broken.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/rbcheck.py")

MUT = [
    ("M4  the UART-vs-seal comparison deleted",
     "        if uart_sum != seal:", "        if False:"),
    ("M7  the progress-vs-sealed comparison deleted",
     "        if prog != sealed:", "        if False:"),
    ("M8  the unknown-magic refusal deleted",
     'fails.append(f"magic {magic:08X} names no payload this tool has a "',
     'pass  # fails.append(f"magic {magic:08X} names no payload this tool has a "'),
    ("M9  summation extent off by one",
     "    for w in b[:count - 1]:", "    for w in b[:count - 2]:"),
    ("M12 the lower-case anchoring removed",
     r'UARTSUM = re.compile(r"rlxprobe:\s*sum=([0-9a-f]{8})")',
     r'UARTSUM = re.compile(r"rlxprobe:\s*sum=([0-9a-fA-F]{8})")'),
    ("M17 the seal-is-poison refusal deleted",
     "    if seal == POISON:", "    if False:"),
    ("M18 the margin check made vacuous",
     "        bad = [(i, a, v) for (i, a, v) in m if v != POISON]",
     "        bad = []"),
    ("M19 the missing-word refusal deleted",
     "        if a not in words:", "        if False and a not in words:"),
    ("M20 SOURCE DRIFT: probe3's ladder changed in the .c only", None, None),

    # M21..M26 -- the RETAINED bitmap branch, 2026-08-31.  Every row names the
    # control it must turn red, which is this repository's standard since the
    # flashwin pass reported 8/8 with every kill invalid.
    ("M21 the recount-vs-payload-count comparison deleted   (kills C18)",
     "            elif kept == adv and got != said:",
     "            elif False:"),
    ("M22 FRESH counted as any written nibble               (kills C22)",
     "                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH",
     "                    if ((b[w] >> sh) & 0xF) != 0:      # V_FRESH"),
    ("M23 the kept-exceeds-count refusal deleted            (kills C19)",
     "            if kept > adv:", "            if False:"),
    ("M24 the layout hardcoded back to the 641-word offsets (kills C17)",
     "        o_bmp, o_bmpk, o_seal = b[42], b[53], b[43]",
     "        o_bmp, o_bmpk, o_seal = 384, 640, 640"),
    ("M25 the truncation limit ignored in the recount       (kills C23)",
     "                    if limit is not None and seen >= limit:\n"
     "                        return n\n"
     "                    seen += 1\n"
     "                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH",
     "                    seen += 1\n"
     "                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH"),
    ("M26 the whole retained branch skipped for short blocks (kills C17)",
     "    if magic == 0x524C5833 and count > 50:\n"
     "        o_bmp, o_bmpk, o_seal = b[42], b[53], b[43]",
     "    if magic == 0x524C5833 and count > 5000:\n"
     "        o_bmp, o_bmpk, o_seal = b[42], b[53], b[43]"),
    # M27..M32 -- Group F, 2026-08-31.  Every row names the control it must turn
    # red, which is this repository's standard.  🔴 M31 is the one that is not
    # about a check at all: it is about the GATE, and C30 is the only case that
    # can see it -- every other Group F case runs on a 718-word block where the
    # gate is open, so a gate that is always open changes none of their answers.
    ("M27 the fault-count check deleted                     (kills C25)",
     '            if g["faults"] != 0:', "            if False:"),
    ("M28 the floating-bus check deleted                    (kills C27)",
     "            if win_live == 0 or boot_live == 0:", "            if False:"),
    ("M29 the repeatability tolerance made unreachable      (kills C28)",
     "                if d * 10 > s1:", "                if d * 10 > s1 * 1000:"),
    ("M30 the never-written sentinel treated as a reading   (kills C26)",
     "                if g[k] == 0xFFFFFFFF:", "                if False:"),
    ("M31 Group F read out of a block that does not have it (kills C30)",
     "        if n_res < 205:", "        if n_res < 0:"),
    ("M33 the all-poison refusal read as seven readings     (kills C31)",
     "            if npois == len(legs):", "            if False:"),
    ("M34 a MIX of poisoned and written legs accepted       (kills C32)",
     "            elif npois:", "            elif False:"),
    ("M32 window-faster-than-DRAM accepted                  (kills C29)",
     '            if 0 < g["dram.str"] != 0xFFFFFFFF and 0 < g["win.str"] < g["dram.str"]:',
     "            if False:"),

    # M35..M40 -- the PAIRING analysis, 2026-08-31 (nineteenth session).
    # 🔴 M36 is the one that matters most: without the population control an
    # all-FRESH region reports PURE PAIRING, which is a verdict read off a
    # region that says nothing -- and every other pairing case stays green
    # while it does, because none of them is single-valued.
    ("M35 the pairing period hardcoded to 256               (kills C38)",
     "            period = kept // 2", "            period = 256"),
    ("M36 the all-FRESH population control removed          (kills C36)",
     "            if period == 0 or not pos or len(pos) == kept:",
     "            if period == 0 or not pos:"),
    ("M37 pairs counted from both ends, so each one twice   (kills C33)",
     "                pairs = sorted(k for k in pos\n"
     "                               if k < period and k + period in s)",
     "                pairs = sorted(k for k in pos\n"
     "                               if k + period in s or k - period in s)"),
    ("M38 the pairing pass counts any written nibble        (kills C22)",
     "                    if nib == 2:                       # V_FRESH, see fresh()",
     "                    if nib:                            # V_FRESH, see fresh()"),
    ("M39 the unpaired list never populated                 (kills C35)",
     "                alone = sorted(k for k in pos\n"
     "                               if (k < period and k + period not in s)\n"
     "                               or (k >= period and k - period not in s))",
     "                alone = []"),
    ("M40 the pairing pass replaced by an empty result      (kills C33)",
     "            pos = fresh_positions(o_bmpk, o_seal, kept)",
     "            pos = []"),
]


def run(path):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode


def make_tree(d):
    """A tree the controls can actually run in: they read committed captures
    and re-read the payload sources."""
    work = os.path.join(d, "router-rebuild")
    os.makedirs(os.path.join(work, "tools"))
    for rel in ("bench", "tools/rlxprobe"):
        shutil.copytree(os.path.join(ROOT, rel),
                        os.path.join(work, rel), symlinks=True)
    return work


def main():
    base = run(SRC)
    if base != 0:
        sys.exit(f"REFUSING: the unmutated suite already fails (rc={base})")
    print(f"baseline: unmutated --self-test rc={base}")

    src = open(SRC, encoding="utf-8").read()
    survived = []

    # B0 -- the unmutated tool, in the TEMP TREE.  See the module docstring:
    # a red baseline here kills every mutation below for free, and the ROOT
    # baseline above cannot see it.
    d0 = tempfile.mkdtemp()
    try:
        w0 = make_tree(d0)
        t0 = os.path.join(w0, "tools/rbcheck.py")
        shutil.copy(SRC, t0)
        r0 = subprocess.run([sys.executable, t0, "--self-test"],
                            capture_output=True, text=True, cwd=w0)
        b0_ok = r0.returncode == 0
        print(f"  {'ok  ' if b0_ok else 'FAIL'}  B0  the UNMUTATED tool passes "
              f"in the temp tree   rc={r0.returncode}")
        if not b0_ok:
            print(r0.stdout[-1500:])
            print("🔴 REFUSING: every kill below would be free")
            return 1
    finally:
        shutil.rmtree(d0, ignore_errors=True)

    # A0 -- every anchor occurs exactly once.  An ambiguous one silently moves
    # to a different construct; see the module docstring.
    amb = [name for name, old, _new in MUT
           if old is not None and src.count(old) != 1]
    print(f"  {'ok  ' if not amb else 'FAIL'}  A0  every anchor occurs exactly "
          f"once in rbcheck.py   {len(MUT) - 1} anchored mutation(s)")
    for name in amb:
        print(f"          AMBIGUOUS-ANCHOR ({src.count(dict((m[0], m[1]) for m in MUT)[name])}x): {name}")
    print()
    if amb:
        print(f"🔴 {len(amb)} MUTATION(S) HAVE AN ANCHOR THAT IS NOT UNIQUE -- "
              f"they would mutate the first match, not the intended one")
        return 1

    for name, old, new in MUT:
        d = tempfile.mkdtemp()
        try:
            work = make_tree(d)
            tgt = os.path.join(work, "tools/rbcheck.py")
            if old is None:                     # M20: mutate the SOURCE, not the tool
                shutil.copy(SRC, tgt)
                p = os.path.join(work, "tools/rlxprobe/probe3.c")
                s = open(p, encoding="latin-1").read()
                s2 = s.replace("#define P_SEALED\t0xC0u", "#define P_SEALED\t0xD0u")
                if s2 == s:
                    survived.append(name + "  [anchor missing, mutation not applied]")
                    continue
                open(p, "w", encoding="latin-1").write(s2)
            else:
                if old not in src:
                    survived.append(name + "  [anchor missing, mutation not applied]")
                    continue
                open(tgt, "w", encoding="utf-8").write(src.replace(old, new, 1))
            r = subprocess.run([sys.executable, tgt, "--self-test"],
                               capture_output=True, text=True, cwd=work)
            killed = r.returncode != 0
            # W0: the row names the case it must turn red, and that case is
            # what has to be red -- not merely something.
            want = re.search(r"\(kills (C[0-9]+[a-z]?)\)", name)
            wrong = ""
            if killed and want:
                tag = want.group(1)
                if f"FAIL  {tag} " not in r.stdout:
                    red = sorted(set(re.findall(r"FAIL  (C[0-9]+[a-z]?) ",
                                                r.stdout)))
                    killed = False
                    wrong = (f"  WRONG-CASE: wanted {tag} red, red were "
                             f"{red or 'none -- it did not reach the controls'}")
            # `  ok  ` / `  FAIL  ` is the shape `tools/ci-census.py` parses
            # (OK_RE / FAIL_RE, two spaces then the word then two more). A
            # suite that prints its own vocabulary is a suite the census reads
            # as zero cases -- measured 2026-08-30, this file printed
            # KILLED/SURVIVED and CI reported `ran 0/9`.
            print(f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                  f"rc={r.returncode} "
                  f"({'killed' if killed else 'SURVIVED'}){wrong}")
            if not killed:
                survived.append(name + wrong)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if survived:
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls do not work:")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(MUT)} mutations killed")
    return 0


sys.exit(main())
