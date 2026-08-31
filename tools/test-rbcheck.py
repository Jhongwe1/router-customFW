#!/usr/bin/env python3
"""test-rbcheck -- the mutation suite for tools/rbcheck.py.

Every mutation below must make --self-test exit non-zero.  A mutation that
survives is a control that does not work, which is the finding an adversarial
pass returned against the first version of this suite: it reported 10/10 while
four mutations lived, two of them deleting exactly what the tool advertises.
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
     "        o_bmp, o_bmpk, o_seal = b[42], b[49], b[43]",
     "        o_bmp, o_bmpk, o_seal = 384, 640, 640"),
    ("M25 the truncation limit ignored in the recount       (kills C23)",
     "                    if limit is not None and seen >= limit:\n"
     "                        return n\n"
     "                    seen += 1\n"
     "                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH",
     "                    seen += 1\n"
     "                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH"),
    ("M26 the whole retained branch skipped for short blocks (kills C17)",
     "    if magic == 0x524C5833 and count > 50:",
     "    if magic == 0x524C5833 and count > 5000:"),
]


def run(path):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode


def main():
    base = run(SRC)
    if base != 0:
        sys.exit(f"REFUSING: the unmutated suite already fails (rc={base})")
    print(f"baseline: unmutated --self-test rc={base}\n")

    src = open(SRC, encoding="utf-8").read()
    survived = []
    for name, old, new in MUT:
        d = tempfile.mkdtemp()
        try:
            work = os.path.join(d, "router-rebuild")
            os.makedirs(os.path.join(work, "tools"))
            # a real tree: the controls read committed captures and the .c files
            for rel in ("bench", "tools/rlxprobe"):
                shutil.copytree(os.path.join(ROOT, rel),
                                os.path.join(work, rel), symlinks=True)
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
            # `  ok  ` / `  FAIL  ` is the shape `tools/ci-census.py` parses
            # (OK_RE / FAIL_RE, two spaces then the word then two more). A
            # suite that prints its own vocabulary is a suite the census reads
            # as zero cases -- measured 2026-08-30, this file printed
            # KILLED/SURVIVED and CI reported `ran 0/9`.
            print(f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                  f"rc={r.returncode} ({'killed' if killed else 'SURVIVED'})")
            if not killed:
                survived.append(name)
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
