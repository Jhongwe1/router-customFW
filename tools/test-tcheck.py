#!/usr/bin/env python3
"""Mutation suite for ``tools/tcheck.py``.

A green control set is a claim about the control set.  Each mutant below
breaks one thing ``tcheck.py --self-test`` says it checks; every one must turn
the suite red, and the row names which control is supposed to catch it.  A
mutant that survives means that control is decorative.

Run: ``/usr/bin/python3 tools/test-tcheck.py``
"""
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "tools", "tcheck.py")
PY = "/usr/bin/python3"

# (name, pattern, replacement, which control must catch it)
MUTANTS = [
    ("M1  the completeness number is the OLD driver's 37",
     r"^EXPECT_KEYS = 67$", "EXPECT_KEYS = 37", "T1/T2"),
    ("M2  the counter width is 32, where the mask bound binds",
     r"^COUNTER_BITS = 27$", "COUNTER_BITS = 32", "T12b"),
    ("M3  the shift search starts below the answer for a fast clock",
     r"for sh in range\(32, -1, -1\):", "for sh in range(24, -1, -1):", "T4"),
    ("M4  rate stops refusing a pair that spans a re-arm",
     r"    if pca != pcb:", "    if False:", "T8"),
    ("M5  rate stops refusing a pair in the wrong order",
     r"    if dj <= 0:", "    if False:", "T9"),
    ("M6  derive asserts arm\\(\\)'s arithmetic on an idle dump",
     r'if hz_kernel and kv\.get\("state"\) != "idle":',
     "if hz_kernel:", "T6"),
    ("M7  arm()'s ext_interval_j clamp is dropped",
     r"max\(pj // 4, 1\),", "pj // 4,", "T7"),
    ("M8  the predicted rate loses its hz_kernel divisor",
     r"pred_per_j = hz / pcb / hz_k", "pred_per_j = hz / pcb", "T10/T11"),
    ("M9  the exactness flag is hardcoded true",
     r"\(10 \*\* 9 << sh\) % hz == 0", "True", "T5"),
]


def run(path):
    """-> (rc, stdout) of `path --self-test`."""
    p = subprocess.run([PY, path, "--self-test"], capture_output=True,
                       text=True, cwd=REPO)
    return p.returncode, p.stdout + p.stderr


def main():
    with open(SRC, encoding="utf-8") as fh:
        base = fh.read()

    print("=== the unmutated tool must be GREEN (a suite that is red on the "
          "real file kills every mutant for the wrong reason) ===")
    rc, out = run(SRC)
    tail = [ln for ln in out.splitlines() if ln.startswith("RESULT")]
    print(f"  {'ok  ' if rc == 0 else 'FAIL'}  baseline rc={rc}  "
          f"{tail[-1] if tail else ''}")
    if rc != 0:
        print("\nRESULT: baseline red -- the mutation run means nothing")
        return 1

    killed, alive = 0, []
    tmpdir = tempfile.mkdtemp(prefix="tcheck-mut-")
    for name, pat, rep, catcher in MUTANTS:
        mutated, n = re.subn(pat, rep, base, count=1, flags=re.M)
        if n != 1:
            print(f"  FAIL  {name}  --  the pattern did not apply "
                  f"({n} substitutions); the mutant never ran")
            alive.append(name)
            continue
        # The mutant needs the same fixtures, so keep REPO pointing at the tree.
        mutated = mutated.replace(
            "REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            f"REPO = {REPO!r}")
        path = os.path.join(tmpdir, "tcheck_mut.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        rc, _ = run(path)
        if rc != 0:
            killed += 1
            print(f"  ok    {name}  --  killed (expected by {catcher})")
        else:
            alive.append(name)
            print(f"  FAIL  {name}  --  SURVIVED; {catcher} is decorative")

    print(f"\nRESULT: {killed}/{len(MUTANTS)} mutants killed")
    return 1 if alive else 0


if __name__ == "__main__":
    raise SystemExit(main())
