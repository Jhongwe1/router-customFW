#!/usr/bin/env python3
"""test-hazpay -- the suite that says `hazpay` and `hazdecl` work.

TWO JOBS, AND THE SECOND IS THE ONE THAT MATTERS.

  ① `emit --check`.  Both payloads' cells are GENERATED and until 2026-09-13
     nothing ran that check: `tools/isapay.py:829` and `tools/rlxprobe/cells4.S:4`
     both said it "is a case in `tools/test-isapay.py`", a file that does not
     exist, and CI ran only `--self-test`.  `cells5.S` claims the same thing about
     THIS file, so this file exists.  `tools/rlxprobe/Makefile` now also runs the
     check as a build prerequisite for probe4 and probe5, so the claim has two
     enforcers rather than one comment.

  ② MUTANTS.  Both tools' self-tests are green, and a green suite is a claim
     about the suite.  This file breaks one invariant at a time in a shadow copy
     of each tool and requires the suite to notice.  A refusal that has never
     refused anything is a refusal nobody has shown to be doing anything -- which
     is `tools/rlxprobe/Makefile`'s `gate-check` argument, applied to the checkers
     instead of to the gate.

     The case COUNTS are not quoted here on purpose: the `base` lines this file
     prints are their one owner, and a number copied into a docstring is a number
     that goes stale in the docstring.

Each mutant names the CASE it must kill.  A mutant that dies to a different case
than the one named is reported as a surprise rather than a pass, because that
means the case named is untested and some other case is doing its work.

REFUSAL.  If the unmutated tool already fails, every mutation below would "kill"
a suite that was already red, so this exits 2 before mutating anything.  That is
`tools/test-spec-check-mutants.py`'s rule and it was worth a whole finding there:
a suite that REFUSES is fast, and a fast suite looks like a win.

usage
    test-hazpay.py [--quiet]
exit
    0 all cases pass and every mutant was killed by the case that names it
    1 a case failed, or a mutant survived
    2 refused: the unmutated tool is already failing
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
HAZPAY = os.path.join(HERE, "hazpay.py")
HAZDECL = os.path.join(HERE, "hazdecl.py")

# (tool, label, old, new, the case id it must kill)
#
# Every `old` must occur EXACTLY ONCE in its tool, and that is checked before any
# mutation runs -- a mutation that silently patched nothing would be a mutant that
# "survived" for the wrong reason.
MUTANTS = [
    # --- hazpay -----------------------------------------------------------
    ("hazpay", "the collapse refusal (lock == open) is removed",
     'if r["kind"] == "haz" and r["lock_v"] == r["open_v"]:',
     'if False and r["kind"] == "haz" and r["lock_v"] == r["open_v"]:',
     "H8"),
    ("hazpay", "the ctl-row rule (lock == open required) is removed",
     'if r["kind"] == "ctl" and r["lock_v"] != r["open_v"]:',
     'if False and r["kind"] == "ctl" and r["lock_v"] != r["open_v"]:',
     "H9"),
    ("hazpay", "the ctl == 0 sentinel refusal is removed",
     'if r["ctl_v"] == 0:',
     'if False and r["ctl_v"] == 0:',
     "H12b"),
    # These two are killed by the COMMITTED TABLE rather than by a case, and
    # that is stronger rather than weaker: `load_rows` derives every row's channel
    # and refuses when the hand value disagrees, so a wrong derivation stops the
    # table parsing before any case runs.  The runner reports `TABLE` for them
    # instead of treating rc=3 as a kill, because rc=3 with zero cases is also
    # what a broken tool looks like.
    ("hazpay", "`main` no longer requires a load-producing family",
     'main = (dist == 0) and family in PRODUCER_IS_LOAD',
     'main = (dist == 0)',
     "TABLE"),
    ("hazpay", "`dslot`'s survey presence becomes distance-dependent",
     'SURVEY_DIST_FREE = ("dslot",)',
     'SURVEY_DIST_FREE = ()',
     "TABLE"),
    ("hazpay", "the channel's two-source check is removed",
     '        if r["haz"] != want:',
     '        if False:',
     "H11"),
    ("hazpay", "the padding loop emits one nop too few",
     'for i in range(r["dist"]):',
     'for i in range(max(0, r["dist"] - 1)):',
     "H22"),
    ("hazpay", "the model reads the `lock` column instead of computing it",
     "    return fn(a=r[\"in_a_v\"], b=r[\"in_b_v\"], m0=r[\"mem0_v\"], m1=r[\"mem1_v\"],\n"
     "              seed=r[\"seed_v\"])",
     "    return r[\"lock_v\"], r[\"open_v\"], r[\"ctl_v\"]",
     "H19"),
    ("hazpay", "the movcond in_b == 0 precondition is removed",
     '        if b != 0:\n            raise Refuse("row %s: movcond needs in_b == 0.',
     '        if False:\n            raise Refuse("row %s: movcond needs in_b == 0.',
     "H14"),
    ("hazpay", "`rb_words` stops guarding the 1-mod-4 property",
     '    if n % 4 == 0:',
     '    if False:',
     "H25"),
    ("hazpay", "a trap no longer outranks a bad control",
     '    if n:\n        return V_TRAP, val, aux\n    if aux != r["ctl_v"]:',
     '    if aux != r["ctl_v"]:\n        return V_VOID, val, aux\n    if n:',
     "H27"),
    ("hazpay", "C4 stops firing on the qemu arm",
     '    if arm == "qemu":',
     '    if False:',
     "H28"),
    ("hazpay", "the storebase pair check is removed",
     '        if len(pair) == 2 and pair[0][1] != pair[1][1]:',
     '        if False:',
     "H29"),
    # --- hazdecl ----------------------------------------------------------
    ("hazdecl", "P1 stops comparing the record count with the VIOLATIONS count",
     '    elif len(viols) != counts["violations"]:',
     '    elif False:',
     "D3"),
    ("hazdecl", "P2 stops refusing a zero load count",
     '    if counts.get("loads", 0) == 0:',
     '    if False:',
     "D4"),
    ("hazdecl", "P4 accepts hazlint exit 0 -- the inversion is gone",
     '    if rc == 0:',
     '    if False:',
     "D5"),
    ("hazdecl", "P6 stops checking that a declared site was reported",
     '        if a not in seen_main:',
     '        if False:',
     "D8"),
    ("hazdecl", "P8 stops checking the survey bucket",
     '        if a not in got:',
     '        if False:',
     "D9"),
    # 🔴 This mutant SURVIVED on its first run and is why `D10b` exists: `D10`
    # puts a padded rung in the VIOLATION list, so nothing tested the survey half
    # of P9.  It was then named `D10` here and died to `D10b`, which the runner
    # reported as WRONG -- the check that a mutant dies to the case NAMING it,
    # doing its job twice in a row on one mutant.
    ("hazdecl", "P9 stops checking the padded rungs against the survey",
     '            r = none_addrs.get(a)\n            if r is not None:',
     '            r = none_addrs.get(a)\n            if False:',
     "D10b"),
    ("hazdecl", "P9 stops checking the padded rungs against the violations",
     '            r = none_addrs.get(v[key])\n            if r is not None:',
     '            r = none_addrs.get(v[key])\n            if False:',
     "D10"),
    ("hazdecl", "P11 stops distinguishing a jump target from the next word",
     "            if \"jump target\" not in v[\"how\"]:",
     "            if False:",
     "D11"),
    ("hazdecl", "P10 accepts an unknown survey shape name",
     '            if m2 and m2.group(1).strip() not in SURVEY_SHAPES:',
     '            if False:',
     "D16"),
]

CASE_RE = re.compile(r"^\s*(ok|FAIL)\s+(\S+)")


def stage(tool_name, body):
    """A SHADOW TREE OF SYMLINKS with one real file in it.

    🔴 The first version of this runner copied the mutated tool to a bare temp
    directory.  Every tool here resolves its data paths from
    `os.path.dirname(__file__)`, so `isa-hazard.tsv` was not there and all twenty
    mutants exited 3 -- REFUSED -- with zero cases reported.  That reads as twenty
    kills and is twenty measurements of nothing, which is this repository's own
    "a suite that REFUSES is fast, and a fast suite looks like a win" with the
    sign flipped.  It was caught because the runner scores WHICH case killed each
    mutant and not merely whether one did.

    `tools/test-spec-check-mutants.py` is the precedent: symlink every top-level
    entry, make `tools/` a real directory of symlinks, and write the mutated file
    into it.  `__file__`'s dirname is then the shadow `tools/` and every data path
    resolves through a symlink to the real file.
    """
    d = tempfile.mkdtemp(prefix="hazmut.")
    os.mkdir(os.path.join(d, "tools"))
    for e in os.listdir(ROOT):
        if e == "tools":
            continue
        os.symlink(os.path.join(ROOT, e), os.path.join(d, e))
    for e in os.listdir(os.path.join(ROOT, "tools")):
        if e == tool_name:
            continue
        os.symlink(os.path.join(ROOT, "tools", e),
                   os.path.join(d, "tools", e))
    tgt = os.path.join(d, "tools", tool_name)
    with open(tgt, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    return d, tgt


def run_suite(tool_path, cwd=None):
    """Run a tool's --self-test.  Returns (rc, {case id: 'ok'|'FAIL'}, text)."""
    p = subprocess.run([PY, tool_path, "--self-test"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       cwd=cwd or ROOT, timeout=600)
    text = p.stdout + p.stderr
    cases = {}
    for line in text.split("\n"):
        m = CASE_RE.match(line)
        if m:
            cases[m.group(2)] = m.group(1)
    return p.returncode, cases, text


def main(argv):
    quiet = "--quiet" in argv
    tools = {"hazpay": HAZPAY, "hazdecl": HAZDECL}
    ok = bad = 0
    surprises = []

    print("test-hazpay -- emit --check, then %d mutant(s)" % len(MUTANTS))
    print("")

    # --- 0. REFUSE if the unmutated tools are already failing --------------
    base = {}
    for name, path in tools.items():
        rc, cases, text = run_suite(path)
        base[name] = cases
        n_ok = sum(1 for v in cases.values() if v == "ok")
        print("  base   %-8s --self-test rc=%d, %d case(s), %d ok"
              % (name, rc, len(cases), n_ok))
        if rc != 0:
            print("")
            print("REFUSING: %s's unmutated self-test already fails (rc=%d). "
                  "Every mutation below would 'kill' a suite that was already "
                  "red." % (name, rc))
            if not quiet:
                print(text)
            return 2

    # --- 1. emit --check ---------------------------------------------------
    print("")
    for label, tool, mode in (("isapay", os.path.join(HERE, "isapay.py"), "emit"),
                              ("hazpay", HAZPAY, "emit")):
        p = subprocess.run([PY, tool, mode, "--check"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           cwd=ROOT)
        line = (p.stdout + p.stderr).strip().split("\n")[-1]
        if p.returncode == 0:
            ok += 1
            print("  ok     %-8s emit --check   %s" % (label, line))
        else:
            bad += 1
            print("  FAIL   %-8s emit --check rc=%d   %s"
                  % (label, p.returncode, line))
            print("         The committed generated files and the table have "
                  "drifted. Run `%s emit` -- and note that the drift, not the "
                  "regeneration, is the finding." % os.path.relpath(tool, ROOT))

    # --- 2. every mutation's anchor must be unique, BEFORE any mutation ----
    print("")
    src = {}
    for name, path in tools.items():
        with open(path, "r", encoding="utf-8", newline="") as f:
            src[name] = f.read()
    for i, (tool, label, old, new, kill) in enumerate(MUTANTS):
        c = src[tool].count(old)
        if c != 1:
            print("  FAIL   mutant %d's anchor occurs %d time(s) in %s, not "
                  "once. A mutation that patched nothing would 'survive' for "
                  "the wrong reason." % (i + 1, c, tool))
            print("         %r" % old[:80])
            bad += 1
        if kill != "TABLE" and kill not in base[tool]:
            print("  FAIL   mutant %d names case %s and %s's suite has no such "
                  "case" % (i + 1, kill, tool))
            bad += 1
    if bad:
        print("")
        print("REFUSING to mutate: %d anchor or case-name problem(s)" % bad)
        return 1

    # --- 3. mutate ---------------------------------------------------------
    for i, (tool, label, old, new, kill) in enumerate(MUTANTS):
        base_name = os.path.basename(tools[tool])
        d, mpath = stage(base_name, src[tool].replace(old, new, 1))
        try:
            rc, cases, text = run_suite(mpath, cwd=d)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        killed_by = sorted(k for k, v in cases.items() if v == "FAIL")
        named_died = cases.get(kill) == "FAIL"
        table_refused = ("REFUSING: the committed" in text and rc == 3
                         and not cases)
        if kill == "TABLE":
            # the committed table must be what stops it, and the tool must SAY so
            if table_refused:
                ok += 1
                print("  ok     %2d %-8s %-52s TABLE: killed by the committed "
                      "table refusing to parse"
                      % (i + 1, tool, label[:52]))
            else:
                bad += 1
                surprises.append((i + 1, kill, killed_by, rc))
                print("  FAIL   %2d %-8s %-52s WRONG: named TABLE, rc=%d cases=%s"
                      % (i + 1, tool, label[:52], rc,
                         ",".join(killed_by) or "-"))
        elif not cases:
            # THE TRAP THIS RUNNER FELL INTO ONCE: no cases reported at all
            # means the mutant REFUSED before running any, which is not a kill.
            bad += 1
            surprises.append((i + 1, kill, [], rc))
            print("  FAIL   %2d %-8s %-52s REFUSED: rc=%d and ZERO cases "
                  "ran -- a refusal is not a kill"
                  % (i + 1, tool, label[:52], rc))
        elif rc == 0 and not killed_by:
            bad += 1
            print("  FAIL   %2d %-8s %-52s ALIVE: survived, nothing noticed"
                  % (i + 1, tool, label[:52]))
        elif named_died:
            ok += 1
            extra = [k for k in killed_by if k != kill]
            print("  ok     %2d %-8s %-52s killed by %s%s"
                  % (i + 1, tool, label[:52], kill,
                     (" (+%d more)" % len(extra)) if extra else ""))
        else:
            bad += 1
            surprises.append((i + 1, kill, killed_by, rc))
            print("  FAIL   %2d %-8s %-52s WRONG: named %s, died to %s (rc=%d)"
                  % (i + 1, tool, label[:52], kill,
                     ",".join(killed_by) or "-", rc))

    print("")
    if surprises:
        print("  A mutant that dies to a case other than the one naming it "
              "means that case is untested and something else is doing its "
              "work:")
        for i, kill, got, rc in surprises:
            print("    mutant %d named %s, died to %s"
                  % (i, kill, ",".join(got) or "(rc %d only)" % rc))
        print("")
    print("RESULT: %d ok, %d bad" % (ok, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
