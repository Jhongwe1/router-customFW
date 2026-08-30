#!/usr/bin/env python3
"""test-leakscan-mutants -- the mutation suite for `tools/leakscan.py`.

Why this file exists
--------------------
`leakscan.py` reported seventeen green controls on the day it made a judgement
the owner of this repository then acted on.  This repository's own measurements
say that is not evidence:

  * `spec-check.py` reported **fifteen green controls with three live mutants**
    (2026-08-30, twelfth session).
  * `console-capture.py` reported **forty green cases with ten live mutants**
    (2026-08-30, eleventh session).

A green control suite is a claim about the suite.

Three phases, and the second exists because of a STRUCTURAL hole
----------------------------------------------------------------
🔴 `leakscan.py`'s `main()` returns on `--self-test` **before the reporting
loop runs**.  So a `--self-test` criterion cannot reach `populations()`'s use
site, the IDENTITY filter in the report, or the per-population totals -- which
is exactly where the mutant `PROGRESS.md` names lives: *"the population filter
widened so `upstream/` is dropped, which would turn 52 findings into a silent
0"*.  `test-spec-check-mutants.py` found the same shape in `spec-check.py` and
its phase 2 is the same answer.

  * **Phase 1** mutates the classifier and its helpers and requires
    `--self-test` to go red.
  * **Phase 2** runs the WHOLE tool over a planted synthetic corpus and
    requires the count of identity hits naming the planted files to CHANGE.
    ⚠️ The criterion is `!=` and not `<`, unlike `spec-check`'s: the planted
    count is exact, so a mutant that reports MORE (an allowlist that stopped
    suppressing) is as broken as one that reports fewer.  For a leak scanner
    the over-reporting direction is the safe one, and it is still a defect.
  * **Phase 3** runs `--attribute` over a corpus planted with a value taken out
    of the reference dump AT RUNTIME.  🔴 That value is never written into this
    file, into any committed file, or into any output: the suite reads six
    bytes out of `$FWRE_WORK/dumps/...` and writes them into a temporary
    directory, and then asserts the tool's own stdout does not contain them.
    Phase 3 is skipped without the dump, and the rows that need it are skipped
    with it rather than counted as killed.

What a mutation proves, and what it does not
--------------------------------------------
Each row edits `leakscan.py` at anchors that must occur EXACTLY ONCE.  A row
whose anchor has moved is reported as a SURVIVOR, never skipped -- a mutation
suite that silently applies nothing is the "a tool reporting 0 is making a
claim" failure this repository keeps catching.  A surviving row names a control
that does not work.  It does not prove the tool is correct.

Run:  /usr/bin/python3 tools/test-leakscan-mutants.py [--jobs N] [--only C1,P2]
"""
import argparse
import concurrent.futures
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "leakscan.py")
ABL = os.path.join(ROOT, "tools", "audit-bench-log.py")
TSV = os.path.join(ROOT, "tools", "ci-expected.tsv")
DUMP = os.path.join(os.environ.get("FWRE_WORK", "/home/key/fwre-work"),
                    "dumps", "flash-n150rt-console-2.bin")
H601_MAC_OFF = 0x006007          # 量 2026-08-30; offsets only, never the value

#: 🔴 One variable, used three times: the printed skip, the `(skipped: …)` line
#: and `Q1`, which asserts it against `tools/ci-expected.tsv`.  The owner audit
#: caught this file ADDING an allowed-skip label that nothing compared, in the
#: same session whose write-up says only two suites check theirs -- which would
#: have made the carried-forward row worse while claiming to improve it.  量
#: 2026-08-30, CI run 33310864156, for what an unchecked label costs.
SKIP_LABEL = "A-block the reference flash dump"

# ---------------------------------------------------------------- anchors ---
LOOKUP = "    offs = find_all(dump, value)"
HOSTTEST = "    if value in hostnames:"
LAATEST = "    if value[0] & 0x02:"
CTLTEST = "    if rel in SCANNER_FILES:"
H601RET = '    if H601[0] <= off < H601[1]:\n        return "H601"'
ATTRLINE = ('    return "  %-50s %-20s line %-6d %-8s %s" '
            '% (rel, label, ln, klass, detail)')
RENDER = ('    return "  %-52s %-22s line %-6d %d char(s)" '
          '% (rel, label, ln, n)')
APPEND = "            findings.append((rel, label, ln, len(txt), mac_bytes(txt)))"
SEPFORM = '    if _MAC_SEP.match(txt):'
ENXFORM = "        m = _MAC_ENX.match(txt)"
REPORTLOOP = "    for name, paths, why in populations(ROOT):"
IDENTTOTAL = "        ident_total += sum(1 for f in findings if f[1] in IDENTITY)"
IDENTLIST = "        ident = [f for f in findings if f[1] in IDENTITY]"
IDENTSET = ('IDENTITY = {"MAC, colon form", "MAC, dash form", "MAC, bare 12 hex",\n'
            '            "MAC, enx interface", "serial-ish"}')
EXTTEST = "        if ext not in TEXTY:"
UPWALK = '    up = walk(root, "upstream")'
ALLOWTEST = "            if abl.allowed(txt, line):"
UNITTALLY = '    if tally["UNIT"]:'
FINDALL = "    off, i = [], hay.find(needle)"
ATTRLOOP = "        for rel, label, ln, _n, value in ident:"
UNITDETAIL = ('        return "UNIT", ("in the reference dump %d time(s), in %s"\n'
              '                        % (len(offs), "+".join(where)))')
# 🔴 `ident = [...]` occurs TWICE -- once in `attribute()` and once in the
# report loop -- so the anchor for the report one has to carry its next two
# lines.  The first version used the bare line and was reported NOT APPLIED,
# which is the behaviour this suite is supposed to have: a moved or ambiguous
# anchor is a SURVIVOR, never a silent skip.
IDENTLIST_MAIN = (
    '        ident = [f for f in findings if f[1] in IDENTITY]\n'
    '        if ident:\n'
    '            print("  \U0001f534 the %d IDENTITY hit(s), file and line only:" % len(ident))')

# id, phase, what it does, [(anchor, replacement), ...]
MUT = [
    # ---- phase 1: the classifier, killed by --self-test -------------------
    ("C1", 1, "classify never finds a value in the dump",
     [(LOOKUP, "    offs = []")]),
    ("C2", 1, "SYNTH is decided before the dump is consulted",
     [(LOOKUP, '    if value[0] & 0x02:\n        return "SYNTH", "laa"\n' + LOOKUP)]),
    ("C3", 1, "a scanner literal is excused before the dump is consulted",
     [(LOOKUP, '    if rel in SCANNER_FILES:\n        return "CONTROL", "lit"\n'
               + LOOKUP)]),
    ("C4", 1, "find_all stops at the first occurrence",
     [(FINDALL, "    off, i = [], hay.find(needle)\n    return [i] if i != -1 "
                "else []\n    off, i = [], hay.find(needle)")]),
    ("C5", 1, "region_of never says H601",
     [(H601RET, '    if False:\n        return "H601"')]),
    # 🔴 These two were first written against `render_attr`, and both SURVIVED
    # because the value is not in that function's scope at all -- it takes
    # (rel, label, ln, klass, detail) and there is nothing to leak.  That is a
    # property worth having and it is not what the rows were claiming to test.
    # The leak can only be built one level up, in the sentence `classify`
    # returns, which is where they mutate now.
    ("C6", 1, "classify's UNIT detail carries the value",
     [(UNITDETAIL, '        return "UNIT", ("%s in the dump %d time(s), in %s"\n'
                   '                        % (":".join("%02x" % c for c in '
                   'value), len(offs), "+".join(where)))')]),
    ("C7", 1, "classify's UNIT detail carries only the 3-byte OUI",
     [(UNITDETAIL, '        return "UNIT", ("oui %s in the dump %d time(s), in '
                   '%s"\n                        % (":".join("%02X" % c for c '
                   'in value[:3]), len(offs), "+".join(where)))')]),
    ("C8", 1, "mac_bytes drops the enx form",
     [(ENXFORM, "        m = None")]),
    ("C9", 1, "mac_bytes drops the separated forms",
     [(SEPFORM, "    if False:")]),
    ("C10", 1, "a finding carries no decoded value at all",
     [(APPEND, "            findings.append((rel, label, ln, len(txt), None))")]),
    ("C11", 1, "TEXTY loses .md, so prose is 'not text'",
     [(EXTTEST, '        if ext not in TEXTY or ext == ".md":')]),
    ("C12", 1, "the upstream population is walked as empty",
     [(UPWALK, "    up = []")]),
    ("C13", 1, "render prints the whole finding tuple, bytes included",
     [(RENDER, '    return "  %s" % (f,)')]),

    # ---- phase 2: the reporting path --self-test cannot reach -------------
    ("P1", 2, "the report drops the upstream population",
     [(REPORTLOOP, "    for name, paths, why in populations(ROOT)[:2]:")]),
    ("P2", 2, "the identity list is never printed",
     [(IDENTLIST_MAIN, "        ident = []\n        if ident:\n"
                       "            print(\"  unreachable\")")]),
    ("P3", 2, "IDENTITY loses the enx pattern",
     [(IDENTSET, 'IDENTITY = {"MAC, colon form", "MAC, dash form", '
                 '"MAC, bare 12 hex",\n            "serial-ish"}')]),
    ("P4", 2, "the identity total counts topic hits too",
     [(IDENTTOTAL, "        ident_total += len(findings)")]),
    ("P5", 2, "the allowlist is bypassed",
     [(ALLOWTEST, "            if False:")]),
    ("P6", 2, "scan_population stops after the first hit in a file",
     [(APPEND, APPEND + "\n            break")]),
    ("P7", 2, "the bench/**/*.md population swallows every tracked file",
     [('    bench_md = [p for p in tr if p.startswith("bench/") and p.endswith(".md")]',
       "    bench_md = list(tr)")]),

    # ---- phase 3: --attribute, and it needs the real dump ------------------
    ("A1", 3, "attribute prints the value it looked up",
     [(ATTRLOOP, ATTRLOOP + "\n            print('  value %s' % "
                 "(':'.join('%02x' % c for c in value) if value else '-'))")]),
    ("A2", 3, "attribute reports success even with a UNIT finding",
     [(UNITTALLY, "    if False:")]),
    ("A3", 3, "the lookup matches on the 3-byte OUI instead of the address",
     [(LOOKUP, "    offs = find_all(dump, value[:3])")]),
]

# The three synthetic addresses planted in the corpus.  Globally administered
# (bit 0x02 clear) so they classify UNKNOWN rather than SYNTH, and chosen so
# `audit-bench-log.py`'s allowlist does not suppress them -- if it did, the
# planted count would be zero and every phase-2 row would "kill" on a run that
# reported nothing.  The baseline check below is what proves it does not.
#
# ⚠️ `notes/PLANT.md` also carries `10.1.1.2`, which `audit-bench-log.py`'s
# allowlist SUPPRESSES.  Without it `P5` -- the allowlist bypassed -- changes
# nothing measurable, because none of the planted addresses is allowlisted, and
# it survived the first run for exactly that reason.
#
# ⚠️ `bench/PLANT.md` also carries two TOPIC words.  Without them every finding
# in the corpus is an identity finding, the two summary numbers are equal, and
# `P4` -- the identity total counting topic hits as well -- changes nothing
# measurable.  It survived the second run for exactly that reason.
PLANT = {
    "bench/PLANT.md": ("a 04:05:06:07:08:01 b 04:05:06:07:08:02 "
                       "c enx040506070803\nH601 calib\n"),
    "notes/PLANT.md": "d 04:05:06:07:08:04 e 04:05:06:07:08:05 host 10.1.1.2\n",
    "upstream/plant.md": ("f 04:05:06:07:08:06 g 04:05:06:07:08:07 "
                          "h 04:05:06:07:08:08\n"),
}
PLANTED_HITS = 8          # 3 + 2 + 3, asserted against the baseline
#: Filled in from the unmutated run; a mutable cell rather than a global
#: rebind so the worker threads read the value the baseline measured.
BASE_SIG = [None]
BASE_UNIT_ALL = [None]

POP_RE = re.compile(r"^  (\d+) file\(s\), (\d+) scanned, (\d+) finding\(s\)$",
                    re.M)
SUM_RE = re.compile(r"^(\d+) raw hit\(s\).*?, (\d+) of them", re.M)
#: 🔴 `[ \t]`, not `\s`.  In Python `\s` MATCHES A NEWLINE and
#: `re.M` does not change that -- it only moves `^`.  With `\s+` the engine
#: started a match on the first `upstream/plant.md` line, ran the whitespace
#: class across three newlines, and completed on the `upstream/unit.md` line
#: four rows below: one match, a plausible count, and the captured path was
#: THE WRONG FILE.  The baseline refusal at 0 is the only reason it showed.
#: ⚠️  The first version of this line also reached disk carrying a
#: literal 0x08 byte, because `\b` written through a quoted heredoc lost a
#: backslash level and Python read it as BACKSPACE -- CLAUDE.md's own rule,
#: and the character classes below avoid needing `\b` at all.
UNITLINE_RE = re.compile(r"^  (\S+)[ \t]+[^\n]*?line[ \t]+\d+[ \t]+UNIT",
                         re.M)


def apply_mutation(src, edits):
    out = src
    for anchor, _repl in edits:
        n = out.count(anchor)
        if n != 1:
            return None, "anchor occurs %d time(s), not once: %r" % (n, anchor[:44])
    for anchor, repl in edits:
        out = out.replace(anchor, repl, 1)
    if out == src:
        return None, "the edits cancelled: the file is unchanged"
    return out, None


def make_root(mutated, real_value=None):
    """A temp root that leakscan resolves as ROOT, with a planted corpus.

    Synthetic rather than a symlink farm over the real repository: the whole
    corpus is eight known hits, so the phase-2 count is exact instead of being
    a delta against 145 real ones.
    """
    d = tempfile.mkdtemp(prefix="ls-mut-")
    os.mkdir(os.path.join(d, "tools"))
    with io.open(os.path.join(d, "tools", "leakscan.py"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(mutated)
    shutil.copy(ABL, os.path.join(d, "tools", "audit-bench-log.py"))
    shutil.copy(TSV, os.path.join(d, "tools", "ci-expected.tsv"))

    for rel, body in PLANT.items():
        p = os.path.join(d, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    if real_value is not None:
        # 🔴 Read at runtime, written only into this temp directory, asserted
        # absent from the tool's own stdout.  It is never stored anywhere else.
        with io.open(os.path.join(d, "upstream", "unit.md"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("device %s\n" % ":".join("%02x" % c for c in real_value))
        # 🔴 THE DECOY, and it is the original defect in one line: the same
        # three-byte OUI with a different tail.  A classifier that matches on
        # the vendor prefix -- which is exactly what `audit-bench-log.py`'s
        # `MAC, bare 12 hex` pattern does -- calls this the device's.  A
        # classifier that requires the whole address does not.  `A3` is the
        # mutant, and without this file it changes nothing measurable.
        decoy = real_value[:3] + b"\x00\x00\x01"
        with io.open(os.path.join(d, "upstream", "decoy.md"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("decoy %s\n" % ":".join("%02x" % c for c in decoy))
    # L4 needs a population of more than 100 files walked from disk.
    pad = os.path.join(d, "upstream", "pad")
    os.makedirs(pad, exist_ok=True)
    for i in range(105):
        with io.open(os.path.join(pad, "f%03d.md" % i), "w",
                     encoding="utf-8") as fh:
            fh.write("nothing here\n")

    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.path.join(d, ".gitconfig"),
               GIT_CONFIG_SYSTEM=os.path.join(d, ".nogitconfig"))
    subprocess.run(["git", "init", "-q"], cwd=d, env=env,
                   capture_output=True)
    subprocess.run(["git", "add", "bench", "notes"], cwd=d, env=env,
                   capture_output=True)
    return d, os.path.join(d, "tools", "leakscan.py")


def run(tool, cwd, *args):
    return subprocess.run([sys.executable, tool] + list(args),
                          capture_output=True, text=True, cwd=cwd, timeout=600)


def planted_hits(stdout):
    """Report lines naming a planted file.  Both `render` and `render_attr`
    start a line with two spaces and the path, so one predicate covers both."""
    return sum(1 for ln in stdout.split("\n")
               if any(ln.startswith("  " + rel) for rel in PLANT))


def signature(stdout):
    """What phase 2 compares, and it is not just a count.

    🔴 The first version compared only the number of report lines naming a
    planted file, and THREE mutants survived it: one that inflated the identity
    total in the summary (`P4`), one that stopped applying the allowlist
    (`P5`), and one that moved every tracked file into the `bench/**/*.md`
    population (`P7`).  All three leave the number of planted lines untouched
    and change what the report SAYS.  So the signature is the per-population
    triple, the per-file line counts, and the two summary numbers."""
    per = {}
    for ln in stdout.split("\n"):
        for rel in PLANT:
            if ln.startswith("  " + rel):
                per[rel] = per.get(rel, 0) + 1
    m = SUM_RE.search(stdout)
    return (tuple(POP_RE.findall(stdout)), tuple(sorted(per.items())),
            m.groups() if m else None)


def one(row, src, real_value):
    mid, phase, what, edits = row
    mutated, why = apply_mutation(src, edits)
    if mutated is None:
        return mid, False, "[NOT APPLIED: %s]" % why
    d = None
    try:
        d, tgt = make_root(mutated, real_value if phase == 3 else None)
        if phase == 1:
            r = run(tgt, d, "--self-test")
            killed = r.returncode != 0
            red = sorted({ln.split()[1] for ln in r.stdout.split("\n")
                          if ln.startswith("  FAIL  ") and len(ln.split()) > 1})
            note = ("by " + ",".join(red) if red
                    else "rc=%d, no FAIL line" % r.returncode)
            return mid, killed, note
        if phase == 2:
            r = run(tgt, d)
            got = signature(r.stdout)
            killed = got != BASE_SIG[0]
            return mid, killed, ("%d planted line(s), summary %s"
                                 % (planted_hits(r.stdout), got[2]))
        r = run(tgt, d, "--attribute")
        enc = [":".join(f % c for c in real_value) for f in ("%02x", "%02X")]
        enc += ["".join(f % c for c in real_value) for f in ("%02x", "%02X")]
        leaked = [e for e in enc if e in r.stdout]
        unit_here = len([x for x in UNITLINE_RE.findall(r.stdout)
                         if x == "upstream/unit.md"])
        # 🔴 The TOTAL matters, not just the planted one: `A3` -- a lookup that
        # matches on the 3-byte OUI instead of the whole address -- leaves
        # `upstream/unit.md` reading UNIT and turns other values UNIT too, and
        # it survived the first run because only the planted line was counted.
        unit_all = len(UNITLINE_RE.findall(r.stdout))
        killed = (bool(leaked) or r.returncode != 1 or unit_here != 1
                  or unit_all != BASE_UNIT_ALL[0])
        return mid, killed, ("leaked=%d rc=%d unit-here=%d unit-total=%d"
                             % (len(leaked), r.returncode, unit_here, unit_all))
    except subprocess.TimeoutExpired:
        return mid, True, "by timeout"
    finally:
        if d:
            shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", default=None, help="comma-separated mutation ids")
    a = ap.parse_args()

    have_dump = os.path.exists(DUMP)
    real_value = None
    if have_dump:
        with open(DUMP, "rb") as fh:
            fh.seek(H601_MAC_OFF)
            real_value = fh.read(6)

    rows = MUT
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        rows = [r for r in MUT if r[0] in want]
        missing = want - {r[0] for r in rows}
        if missing:
            sys.exit("no such mutation id(s): %s" % sorted(missing))
    skipped = [r for r in rows if r[1] == 3 and not have_dump]
    rows = [r for r in rows if not (r[1] == 3 and not have_dump)]

    src = io.open(SRC, encoding="utf-8").read()
    t0 = time.monotonic()

    # --- the baselines.  Without them every row below would "kill" a run that
    # --- was already red, or count against a corpus that was already empty.
    # 🔴 TWO roots, not one.  The first version measured all three baselines in
    # a root that carried the phase-3 plant as well, so the phase-2 count came
    # back 9 against a declared 8 and the refusal fired -- correctly, and on the
    # harness rather than on the tool.  Phase 2's corpus is the eight declared
    # hits and nothing else; phase 3's is that corpus plus one real value.
    d, tgt = make_root(src)
    try:
        base1 = run(tgt, d, "--self-test")
        base2 = run(tgt, d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    base3 = None
    if have_dump:
        d3, tgt3 = make_root(src, real_value)
        try:
            base3 = run(tgt3, d3, "--attribute")
        finally:
            shutil.rmtree(d3, ignore_errors=True)
    if base1.returncode != 0:
        print(base1.stdout[-2000:])
        sys.exit("REFUSING: the unmutated --self-test already fails (rc=%d)"
                 % base1.returncode)
    got = planted_hits(base2.stdout)
    if got != PLANTED_HITS:
        print(base2.stdout[-3000:])
        sys.exit("REFUSING: the unmutated tool reports %d planted hit(s), not "
                 "%d -- every phase-2 row would 'kill' against a corpus that "
                 "is not what this file says it is" % (got, PLANTED_HITS))
    if base3 is not None:
        u = len([x for x in UNITLINE_RE.findall(base3.stdout)
                 if x == "upstream/unit.md"])
        if u != 1 or base3.returncode != 1:
            print(base3.stdout[-3000:])
            sys.exit("REFUSING: the unmutated --attribute reports %d UNIT "
                     "line(s) for the planted real value and exits %d, so a "
                     "phase-3 row could 'kill' a run that never worked"
                     % (u, base3.returncode))
    BASE_SIG[0] = signature(base2.stdout)
    if base3 is not None:
        BASE_UNIT_ALL[0] = len(UNITLINE_RE.findall(base3.stdout))
        if BASE_UNIT_ALL[0] != 1:
            sys.exit("REFUSING: the unmutated --attribute reports %d UNIT "
                     "line(s) in total over the planted corpus, not 1"
                     % BASE_UNIT_ALL[0])
    ncontrols = sum(1 for ln in base1.stdout.split("\n")
                    if ln.startswith("  ok    "))
    print("baseline: --self-test green through the temp-root harness, %d "
          "control(s); the full run reports %d/%d planted hits%s (%.0fs)"
          % (ncontrols, got, PLANTED_HITS,
             "; --attribute reports the planted UNIT and exits 1"
             if base3 is not None else "; --attribute NOT exercised (no dump)",
             time.monotonic() - t0))
    print("%d mutation(s), %d at a time\n" % (len(rows), a.jobs))

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for mid, killed, note in ex.map(lambda r: one(r, src, real_value), rows):
            results[mid] = (killed, note)

    survived = []
    for mid, phase, what, _ in rows:
        killed, note = results[mid]
        print("  %s  %-4s p%d %-56s %s"
              % ("ok  " if killed else "FAIL", mid, phase, what,
                 ("killed " + note) if killed else ("SURVIVED " + note)))
        if not killed:
            survived.append("%s  %s  %s" % (mid, what, note))
    # Q1 -- the label this suite prints is the label the census expects. It runs
    # in BOTH configurations, which is the whole point: on a machine with the
    # dump no skip is printed, so nothing else ever compares it.
    want = None
    if os.path.exists(TSV):
        with io.open(TSV, encoding="utf-8") as fh:
            for row in fh:
                if row.startswith("#"):
                    continue
                parts = row.rstrip("\n").split("\t")
                if len(parts) > 2 and parts[0] == "test-leakscan-mutants":
                    want = parts[2]
    ok_q1 = want == SKIP_LABEL
    print("  %s  %-4s --  %-56s %s"
          % ("ok  " if ok_q1 else "FAIL", "Q1", "ci-expected.tsv's allowed skip "
             "is this suite's label", "table says %r" % (want,)))
    if not ok_q1:
        survived.append("Q1  the census expects %r and this suite prints %r"
                        % (want, SKIP_LABEL))

    if skipped:
        print("  skip   %-52s %s"
              % (SKIP_LABEL,
                 "%s need $FWRE_WORK/dumps/flash-n150rt-console-2.bin, 4 MiB "
                 "of this unit's own flash, which can never be committed "
                 "(covers %d)"
                 % ("/".join(r[0] for r in skipped), len(skipped))))

    print()
    if skipped:
        print("  (skipped: %s, %d case(s))" % (SKIP_LABEL, len(skipped)))
    print("  %d passed, %d failed (%.0fs wall)"
          % (len(rows) + 1 - len(survived), len(survived), time.monotonic() - t0))
    if survived:
        print("\n  %d MUTATION(S) SURVIVED -- those are controls that do not "
              "work:" % len(survived))
        for s in survived:
            print("    %s" % s)
        return 1
    return 0


sys.exit(main())
