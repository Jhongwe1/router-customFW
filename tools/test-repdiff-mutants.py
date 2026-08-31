#!/usr/bin/env python3
"""Do repdiff's controls actually kill a broken repdiff?

`P4a`, 2026-09-01.  `tools/repdiff.py --self-test` prints sixteen `ok` lines.
That is a claim about repdiff; this file is the claim about the fifteen lines.

🔴 `M0` IS THE FIRST CASE AND IT IS NOT CEREMONY.  On 2026-08-31 the first run
of `test-flashwin-mutants` reported 8 of 8 killed and every one of those kills
was invalid -- the harness itself was failing, so a mutant that changed nothing
would have been "killed" too.  A harness that kills everything and a harness
that tests nothing produce identical output.  `M0` runs the UNMUTATED source
through the same path and requires it to pass.

Every mutant below names the case it must turn red.  A mutant killed by a
different case than the one named is reported as such and does not count: it
means the case that was supposed to see it does not, and some other case is
covering for it by accident.

Usage:  tools/test-repdiff-mutants.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "repdiff.py")

# (name, old, new, the case that must go red, why this mutant is worth making)
MUTANTS = [
    ("nobits-ignored",
     'if s["type"] != SHT_NOBITS and s["size"]',
     'if s["size"]',
     "D4",
     "a .bss whose sh_offset overlaps a real section would be blamed for bytes "
     "no .bss owns -- and 2.6.30 vmlinux has exactly that shape"),

    ("always-identical",
     "diffs = [i for i in range(n) if a_blob[i] != b_blob[i]]",
     "diffs = []",
     "D2",
     "the tool that cannot fail: every summary line it prints is true and it "
     "reports nothing. D1 passes it; only D2 sees it"),

    ("everything-differs",
     "diffs = [i for i in range(n) if a_blob[i] != b_blob[i]]",
     "diffs = list(range(n))",
     "D1",
     "the mirror image of the one above, and it is D1 -- the negative control "
     "-- that catches it"),

    ("runs-never-join",
     "if o - cur[1] <= gap:",
     "if o - cur[1] <= 0:",
     "D5",
     "runs that never join: 84 differing bytes would report as 84 runs and the "
     "report would be unreadable rather than wrong. \u26a0\ufe0f The first "
     "version of this mutant changed `runs`'s DEFAULT argument and stayed "
     "alive, because `compare` passes gap explicitly -- an equivalent mutant, "
     "not a missing control, and the difference matters"),

    ("one-big-run",
     "if o - cur[1] <= gap:",
     "if True:",
     "D5b",
     "runs that always join: two differences a kilobyte apart become one, and "
     "the section attribution then describes only the first"),

    ("common-prefix-is-max",
     "n = min(len(a_blob), len(b_blob))",
     "n = max(len(a_blob), len(b_blob))",
     "D6",
     "reading past the end of the shorter file"),

    ("no-endian-check",
     "if blob[5] != 2:",
     "if False:",
     "D8",
     "a little-endian image read as big-endian gives section offsets that are "
     "garbage and a report that looks exactly like a real one"),

    ("no-class-check",
     "if blob[4] != 1:",
     "if False:",
     "D8b",
     "the same for ELF64, which is what a host object is"),

    ("no-magic-check",
     'if blob[:4] != b"\\x7fELF":',
     "if False:",
     "D7",
     "a raw binary parsed as an ELF"),

    ("b-not-parsed",
     'Elf32BE(b_blob, b_name)          # parsed for its refusals, not its tables',
     "pass",
     "D9",
     "the refusals fire on A only, so a corrupt B is compared against a good A "
     "and the report describes A's sections over B's bytes"),

    ("symbol-offset-zero",
     'return (best["name"], vaddr - best["value"], vaddr)',
     'return (best["name"], 0, vaddr)',
     "D2b",
     "the symbol is named but the offset inside it is not -- which is the half "
     "that says WHERE in linux_banner the bytes are"),

    ("short-header-accepted",
     "if len(blob) < 52:",
     "if False:",
     "D7b",
     "a truncated header unpacks from whatever follows it"),
]


def load(src):
    """Exec repdiff's source in a fresh namespace and return it."""
    ns = {"__name__": "repdiff_under_test", "__file__": TARGET}
    exec(compile(src, TARGET, "exec"), ns)
    return ns


def controls_output(src):
    """-> (rc, text) from running run_controls() on this source."""
    buf = io.StringIO()
    try:
        ns = load(src)
        rc = ns["run_controls"](out=buf)
    except Exception as ex:                       # a mutant may not even import
        return 1, buf.getvalue() + "\nEXCEPTION: %r" % (ex,)
    return rc, buf.getvalue()


FAIL_RE = re.compile(r"^\s*FAIL\s+(\S+)", re.M)


def main():
    src = open(TARGET, encoding="utf-8").read()
    print("test-repdiff-mutants -- %d mutant(s) against %s\n"
          % (len(MUTANTS), os.path.basename(TARGET)))

    # ---- M0 --------------------------------------------------------------
    rc, txt = controls_output(src)
    base_ok = (rc == 0 and not FAIL_RE.findall(txt))
    print("  %s  M0     the UNMUTATED source passes through this harness   %s"
          % ("ok  " if base_ok else "FAIL", "rc=%d" % rc))
    if not base_ok:
        print("\n" + txt)
        print("RESULT: \033[31mharness broken -- every kill below would be "
              "invalid\033[0m")
        return 1

    killed = invalid = alive = 0
    for name, old, new, want, why in MUTANTS:
        n = src.count(old)
        if n != 1:
            print("  FAIL  %-22s anchor occurs %d times, not once" % (name, n))
            invalid += 1
            continue
        rc, txt = controls_output(src.replace(old, new, 1))
        fails = FAIL_RE.findall(txt)
        if not fails:
            print("  FAIL  %-22s ALIVE -- no control saw it   (%s)" % (name, want))
            alive += 1
        elif want in fails:
            print("  ok    %-22s killed by %-5s %s"
                  % (name, want, "(+%d other)" % (len(fails) - 1) if len(fails) > 1 else ""))
            killed += 1
        else:
            print("  FAIL  %-22s killed by %s, but %s was supposed to see it"
                  % (name, ",".join(fails), want))
            invalid += 1

    print()
    total = len(MUTANTS)
    if killed == total:
        print("RESULT: \033[32m%d/%d killed, each by the case named for it\033[0m"
              % (killed, total))
        return 0
    print("RESULT: \033[31m%d/%d killed, %d alive, %d killed by the wrong "
          "case\033[0m" % (killed, total, alive, invalid))
    return 1


if __name__ == "__main__":
    sys.exit(main())
