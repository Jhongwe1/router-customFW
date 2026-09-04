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

    # 🔴 C1 -- this suite prints one line per mutant PLUS the baseline PLUS this
    # case, and `ci-expected.tsv` has to carry that total.  It went red in CI
    # run 33849822488 with `CENSUS-MISMATCH 10+0+0 != 9`, because the row was
    # written from `len(MUTANTS)` and the baseline line was forgotten.
    #
    # THE DESK CANNOT SEE THAT CLASS: the census job's first step downloads the
    # per-job artifacts, which do not exist on a workstation, so `census` never
    # runs there and no total is ever compared.  Same shape as this table's own
    # precedents -- test-kbuild-cflags C1, leakscan Q1, replay-capture R14 --
    # and the repair is theirs: a case that reads the table itself, so it runs
    # in both configurations.
    expect = len(MUTANTS) + 2
    declared = None
    tsv = os.path.join(REPO, "tools", "ci-expected.tsv")
    with open(tsv, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("test-tcheck\t"):
                declared = int(line.split("\t")[1])
                break
    ok = declared == expect
    print(f"  {'ok  ' if ok else 'FAIL'}  C1  ci-expected.tsv declares this "
          f"suite's case count  --  declares {declared}, prints {expect} "
          f"({len(MUTANTS)} mutants + baseline + this case)")
    if not ok:
        alive.append("C1 the declared case count")

    # The summary has to carry BOTH halves.  Its first version printed
    # "9/9 mutants killed" while C1 was red one line above it, which reads
    # green -- and a summary that disagrees with the lines above it is worse
    # than no summary.
    extra = [a for a in alive if a.startswith("C1")]
    print(f"\nRESULT: {killed}/{len(MUTANTS)} mutants killed"
          + (f", and {len(extra)} other check(s) FAILED" if extra else
             ", every other check held"))
    return 1 if alive else 0


if __name__ == "__main__":
    raise SystemExit(main())
