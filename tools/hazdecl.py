#!/usr/bin/env python3
"""hazdecl -- probe5's build gate.  `tools/hazlint`, adjudicated in both directions.

THE PROBLEM THIS EXISTS FOR, AND NOTHING IN THIS REPOSITORY HAD NOTICED IT.

`plan/router-rebuild-plan.md:1038` requires `R1b`'s load-delay-slot test to be
`lw` 後緊接讀取同一暫存器.  `tools/hazlint`'s own docstring defines a violation as

    for every load, does an instruction that can execute next read the register
    that was loaded

-- the same sentence.  And `tools/rlxprobe/Makefile` makes `<payload>.bin`
unbuildable unless `hazlint` exits 0, with no waiver flag anywhere in its option
table, with a `gate-check` target that fails the build if the gate is loosened,
and with `cells.S:69-76` foreclosing run-time construction on purpose.  So the
build gate prevented exactly the experiment the plan asks for, and no document in
`plan/`, `docs/`, the Makefile or `hazlint` addressed it.

THE RESOLUTION IS NOT A WAIVER.

Three things were available and two are wrong:

  ① `--vma-range` or `--section` around the framework, leaving the cells out.
     A hard-coded window is a filter that drops silently -- the Makefile's own
     comment under `$(BIN)` says so about `--only-section` -- and worse, it
     creates a SEAM: a load at the end of one window whose consumer is the first
     instruction of the other is checked by neither.
  ② a hazard body in a data section, copied into a run-time arena.  Invisible to
     the gate by construction, which is `tools/mkramboot.py`'s recorded failure
     ("a model kinder than the device certifies exactly the bugs the device will
     reject") with the roles swapped.
  ③ run the UNMODIFIED gate over the WHOLE image and adjudicate its output.

This is ③.  `hazlint` is not modified, no flag restricts what it scans, and
`gate-check` is untouched, so every other payload's gate is exactly what it was.
What changes is that the gate's output becomes DATA for a second, two-sided
check, which is strictly more than "zero" ever said.

AND THE SIGN IS INVERTED.  For probe5, `hazlint` exiting **0 is a build
failure**: a hazard payload with no violations has had its hazards compiled away,
which is `PROGRESS.md:122`'s risk column in one sentence.  That inversion is the
whole of the step's pass condition -- *each test is shown, at the desk, to be
ABLE to produce the wrong answer* -- and it is a refusal rather than a report.

WHAT IT CHECKS, and every one of these can fail

  P1  the number of violation RECORDS parsed equals the VIOLATIONS count.
      This is the control on this tool's own parser, and it is first because two
      parsers written against this same output were wrong on 2026-09-13 before
      this one: one matched hazlint's K2 control line ("Expected: 2 violations")
      and read 2 for every case including the negative control, and one anchored
      `VIOLATIONS` at column 0 where the line is indented two spaces.  Both
      printed a number.  It also catches `--max-report` truncation.
  P2  loads > 0.  hazlint's exit 2 covers *the scan found no loads at all*, and
      a tool that is not looking reports 0 loads and not 0 violations.
  P3  unresolved == 0.  An unchecked successor is an unchecked load.
  P4  hazlint's exit code is 1.  0 means the hazards are gone; 2 and 3 mean it
      refused, and a refusal is not a verdict.
  P5  every violation is at a declared site: load == addr(_p), successor ==
      addr(_c) of a row whose channel is `main` or `both`.
  P6  every `main`/`both` row's site appears in the violation list.
  P7  every survey hit is at a declared `survey`/`both` row's producer, in the
      bucket its family declares.
  P8  every `survey`/`both` row's site appears in its declared bucket.
  P9  no row whose channel is `none` appears in EITHER channel.  This is the one
      that proves the padding is really there, and it is the direction a gate
      that only counted violations could never have.
  P10 the survey's shape names are the three this tool knows.  A hazlint whose
      survey grew a fourth shape must be loud, not silently unmatched.
  P11 the `dslot` family's record says its successor was reached as a JUMP
      TARGET and not as the next word.  量 2026-09-13: hazlint prints
      `[jump target of 0x...]` for a load in a delay slot and `[next word]`
      otherwise, so this is free and it is the only check that distinguishes
      that family's shape from `loaduse`'s.
  P12 the distance in the ARTEFACT: addr(_c) - addr(_p) == 4*(dist+1), read out
      of the symbol table by `hazpay.check_distances`.  Independent of hazlint
      entirely -- two instruments, two claims, no overlap.

usage
    hazdecl.py ELF [--hazlint PATH] [--stage2 PATH] [--verbose]
    hazdecl.py --self-test

exit
    0  the payload's declared hazards are all present and nothing else is
    1  a finding
    3  REFUSED: the parser disagreed with itself, or hazlint refused
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import hazpay                                                   # noqa: E402
from hazpay import Refuse                                       # noqa: E402

HAZLINT = os.path.join(HERE, "hazlint")

# The survey's three shape names, verbatim from `tools/hazlint`'s output.
# 量 2026-09-13, all three with a fixture that makes each one fire alone.
SURVEY_SHAPES = ("a load sitting in a delay slot",
                 "mtc0 then mfc0",
                 "mult/div then mfhi/mflo")

# Which bucket each family's site must appear in.  A family with no survey
# presence maps to None and P8 does not ask about it.
#
# 🔴 DERIVED from `hazpay`, not restated.  The first version listed all nine
# families by hand and the tenth (`hiloprime`, added an hour later) was missing --
# a `KeyError` in a case, which is the lucky version of a silent `None`.  Two
# owners of one fact is what `PROGRESS.md`'s house rule 1 forbids, and the bucket
# NAME is the only part of it that belongs here: `hazpay` owns *whether* a family
# has survey presence, this file owns *what hazlint calls it*.
_BUCKET = {
    "hilo": "mult/div then mfhi/mflo",
    "cp0": "mtc0 then mfc0",
    "dslot": "a load sitting in a delay slot",
}
FAMILY_SURVEY = {f: _BUCKET.get(f) for f in hazpay.FAMILIES}

# ... and both directions, at import time, so a new family cannot be half-wired.
for _f in hazpay.SURVEY_DIST_FREE + hazpay.SURVEY_AT_D0:
    if FAMILY_SURVEY.get(_f) is None:
        raise Refuse("hazpay says family %r appears in hazlint's survey and this "
                     "file has no bucket name for it" % _f)
for _f, _b in _BUCKET.items():
    if _f not in hazpay.SURVEY_DIST_FREE + hazpay.SURVEY_AT_D0:
        raise Refuse("this file gives family %r the bucket %r and hazpay says it "
                     "has no survey presence at all" % (_f, _b))
for _b in _BUCKET.values():
    if _b not in SURVEY_SHAPES:
        raise Refuse("bucket %r is not one of hazlint's three shape names" % _b)

# The VIOLATIONS summary lines, by their own labels.  Read by LABEL and not by
# line number, because a line number is the kind of anchor that goes stale
# silently.
SUM_RE = {
    "loads":      re.compile(r"^\s*loads \(MIPS-I load-to-GPR[^)]*\)\s+(\d+)\s*$"),
    "nop":        re.compile(r"^\s*followed by an explicit nop\s+(\d+)\s"),
    "unresolved": re.compile(r"^\s*successor unresolved\s+(\d+)\s*$"),
    "notes":      re.compile(r"^\s*notes \([^)]*\)\s+(\d+)\s*$"),
    "violations": re.compile(r"^\s*VIOLATIONS\s+(\d+)\s*$"),
}

# A violation is three lines.  量 2026-09-13:
#   |  0x80500004  file 0x10004  lw    t1,0(t2)                  8d490000  |.I..|
#   |  0x80500008                addu  v0,t1,zero                01201021  |. .!|
#   |                             reads $t1   [next word]
V_LOAD_RE = re.compile(r"^\s*0x([0-9a-fA-F]{8})\s+file\s+0x[0-9a-fA-F]+\s+"
                       r"(\S+)\s+.*?([0-9a-fA-F]{8})\s+\|")
V_SUCC_RE = re.compile(r"^\s*0x([0-9a-fA-F]{8})\s+"
                       r"(\S+)\s+.*?([0-9a-fA-F]{8})\s+\|")
V_READS_RE = re.compile(r"^\s*reads\s+\$(\S+)\s+\[(.*)\]\s*$")

# A survey line: four leading spaces, the shape name, the count, then addresses.
SURVEY_RE = re.compile(r"^\s{3,}(%s)\s+(\d+)\s*(.*)$"
                       % "|".join(re.escape(s) for s in SURVEY_SHAPES))
SURVEY_ANY_RE = re.compile(r"^\s{3,}([a-z][a-z0-9 /_-]{6,})\s+(\d+)\s*"
                           r"((?:0x[0-9a-fA-F]+\s*)*)$")


def parse_hazlint(text):
    """The output -> {counts, violations, survey}.  A pure function, so its
    controls run in CI with no cross-compiler -- `isapay`'s `converse_stray` is
    the precedent for splitting it out for exactly that reason."""
    lines = text.replace("\r", "").split("\n")
    counts, violations, survey = {}, [], {}

    # the summary block.  Take the LAST match of each label: `--survey` prints
    # the main block once, but a future mode that printed a second summary must
    # not make this silently read the first.
    for l in lines:
        for k, rx in SUM_RE.items():
            m = rx.match(l)
            if m:
                counts[k] = int(m.group(1))

    # the violation records
    i = 0
    while i < len(lines):
        m = V_LOAD_RE.match(lines[i])
        if not m or "file" not in lines[i]:
            i += 1
            continue
        # a load line must be followed by a successor line and a reads line
        if i + 2 >= len(lines):
            break
        ms = V_SUCC_RE.match(lines[i + 1])
        mr = V_READS_RE.match(lines[i + 2])
        if not ms or not mr:
            i += 1
            continue
        violations.append({
            "load": int(m.group(1), 16), "load_mn": m.group(2),
            "load_w": int(m.group(3), 16),
            "succ": int(ms.group(1), 16), "succ_mn": ms.group(2),
            "succ_w": int(ms.group(3), 16),
            "reg": mr.group(1), "how": mr.group(2).strip(),
        })
        i += 3

    # the survey block, and an unknown shape name is a REFUSAL rather than a
    # line nobody matched
    in_survey = False
    for l in lines:
        if l.strip().startswith("survey --"):
            in_survey = True
            continue
        if in_survey:
            if l.startswith("RESULT") or (l.strip() == "" and survey):
                in_survey = False
                continue
            m = SURVEY_RE.match(l)
            if m:
                survey[m.group(1)] = (int(m.group(2)),
                                      [int(a, 16) for a in m.group(3).split()])
                continue
            m2 = SURVEY_ANY_RE.match(l)
            if m2 and m2.group(1).strip() not in SURVEY_SHAPES:
                raise Refuse("hazlint's survey has a shape this tool does not "
                             "know: %r. A survey that grew a fourth shape must "
                             "be loud, because an unmatched line is a hazard "
                             "class nothing is adjudicating"
                             % m2.group(1).strip())
    return {"counts": counts, "violations": violations, "survey": survey}


def adjudicate(rows, syms, parsed, rc):
    """(findings, refusals).  Pure, and the whole of P1-P12 except the distance
    check, which `hazpay.check_distances` owns."""
    findings, refusals = [], []
    counts = parsed["counts"]
    viols = parsed["violations"]
    survey = parsed["survey"]

    # P1 -- the control on this tool's own parser, and it is first
    if "violations" not in counts:
        refusals.append("P1 no VIOLATIONS line was parsed at all. This tool "
                        "cannot report on output it did not read")
    elif len(viols) != counts["violations"]:
        refusals.append("P1 hazlint says %d violation(s) and this tool parsed "
                        "%d record(s). Either the report was truncated "
                        "(--max-report) or this parser is wrong about the "
                        "format -- and two parsers written against this same "
                        "output were wrong on 2026-09-13 before this one"
                        % (counts["violations"], len(viols)))
    # P2
    if counts.get("loads", 0) == 0:
        refusals.append("P2 hazlint counted 0 loads. A tool that is not looking "
                        "reports 0 loads and not 0 violations, and hazlint's "
                        "own exit 2 covers this case")
    if refusals:
        return findings, refusals

    # P3
    if counts.get("unresolved", 0) != 0:
        findings.append("P3 %d unresolved successor(s). An unchecked successor "
                        "is an unchecked load, and a hazard payload cannot have "
                        "one: every branch in it is a `beq` whose target is in "
                        "the span" % counts["unresolved"])
    # P4
    if rc == 0:
        findings.append("P4 hazlint exited 0 -- NO VIOLATIONS AT ALL. For "
                        "probe5 that is a build failure and not a pass: a "
                        "hazard payload with no hazards has had them compiled "
                        "away, which is the risk PROGRESS.md:122 names")
    elif rc not in (1,):
        refusals.append("P4 hazlint exited %d. 2 and 3 are refusals -- a "
                        "control failed, the population control did not run, or "
                        "the usage was wrong -- and a refusal is not a verdict"
                        % rc)
        return findings, refusals

    # the declaration, from the table and the artefact
    site = {}                       # addr(_p) -> row
    csite = {}                      # row name -> addr(_c)
    missing_sym = []
    for r in rows:
        p, c = "rlx_p5_%s_p" % r["name"], "rlx_p5_%s_c" % r["name"]
        if p not in syms or c not in syms:
            missing_sym.append(r["name"])
            continue
        site[syms[p]] = r
        csite[r["name"]] = syms[c]
    if missing_sym:
        refusals.append("P5 %d row(s) have no site symbols in the artefact: %s. "
                        "An absent declaration would make every check below "
                        "pass by being blind"
                        % (len(missing_sym), " ".join(missing_sym)))
        return findings, refusals

    main_declared = {syms["rlx_p5_%s_p" % r["name"]]: r for r in rows
                     if r["haz"] in ("main", "both")}
    surv_declared = {syms["rlx_p5_%s_p" % r["name"]]: r for r in rows
                     if r["haz"] in ("survey", "both")}
    none_addrs = {}
    for r in rows:
        if r["haz"] == "none":
            none_addrs[syms["rlx_p5_%s_p" % r["name"]]] = r
            none_addrs[syms["rlx_p5_%s_c" % r["name"]]] = r

    # P5 forward
    seen_main = set()
    for v in viols:
        r = main_declared.get(v["load"])
        if r is None:
            other = site.get(v["load"])
            findings.append(
                "P5 a violation at 0x%08X (%s -> %s, reads $%s) is at %s. "
                "Every hazard in this image must be one the table declares"
                % (v["load"], v["load_mn"], v["succ_mn"], v["reg"],
                   ("row %s, whose channel is %s" % (other["name"], other["haz"]))
                   if other else "no declared site at all"))
            continue
        seen_main.add(v["load"])
        if v["succ"] != csite[r["name"]]:
            findings.append(
                "P5 %s's violation has successor 0x%08X and the declared "
                "consumer is at 0x%08X. hazlint followed a different "
                "instruction from the one the table calls the consumer"
                % (r["name"], v["succ"], csite[r["name"]]))
        # P11
        if r["family"] == "dslot":
            if "jump target" not in v["how"]:
                findings.append(
                    "P11 %s is the delay-slot family and hazlint reached its "
                    "consumer as %r, not as a jump target. The load is not in a "
                    "delay slot, so this row measures what `loaduse` already "
                    "measures" % (r["name"], v["how"]))
        elif "next word" not in v["how"]:
            findings.append(
                "P11 %s's consumer was reached as %r and not as the next word. "
                "Only the `dslot` family may be reached through a branch"
                % (r["name"], v["how"]))

    # P6 backward
    for a, r in sorted(main_declared.items()):
        if a not in seen_main:
            findings.append(
                "P6 %s declares a `%s` hazard site at 0x%08X and hazlint did "
                "not report one there. The hazard this rung exists to test is "
                "NOT PRESENT AS BUILT -- which is the direction a gate that "
                "only counts violations can never check"
                % (r["name"], r["haz"], a))

    # P7 / P8 / P10 -- the survey channel
    for shape, (n, addrs) in sorted(survey.items()):
        if len(addrs) != n and n <= 32:
            findings.append("P10 survey shape %r says %d and lists %d "
                            "address(es)" % (shape, n, len(addrs)))
        for a in addrs:
            r = surv_declared.get(a)
            if r is None:
                other = site.get(a)
                findings.append(
                    "P7 a survey hit for %r at 0x%08X is at %s"
                    % (shape, a,
                       ("row %s, whose channel is %s"
                        % (other["name"], other["haz"])) if other
                       else "no declared site at all"))
            elif FAMILY_SURVEY[r["family"]] != shape:
                findings.append(
                    "P7 %s is family %s, which declares the %r bucket, and its "
                    "site turned up under %r"
                    % (r["name"], r["family"], FAMILY_SURVEY[r["family"]], shape))
    for a, r in sorted(surv_declared.items()):
        want = FAMILY_SURVEY[r["family"]]
        if want is None:
            findings.append("P8 %s declares channel %s and its family %s has no "
                            "survey bucket -- the table and this tool disagree"
                            % (r["name"], r["haz"], r["family"]))
            continue
        got = survey.get(want, (0, []))[1]
        if a not in got:
            findings.append(
                "P8 %s declares a `%s` hazard site at 0x%08X and hazlint's "
                "survey did not count one under %r. The shape this rung exists "
                "to test is NOT PRESENT AS BUILT"
                % (r["name"], r["haz"], a, want))

    # P9 -- the padded rungs, in BOTH channels
    for v in viols:
        for key in ("load", "succ"):
            r = none_addrs.get(v[key])
            if r is not None:
                findings.append(
                    "P9 %s is a padded rung (dist %d, channel none) and its %s "
                    "address 0x%08X is in hazlint's violation list. THE PADDING "
                    "IS NOT THERE, so this rung is its own d0 twin and the "
                    "ladder has no rungs"
                    % (r["name"], r["dist"], key, v[key]))
    for shape, (_n, addrs) in sorted(survey.items()):
        for a in addrs:
            r = none_addrs.get(a)
            if r is not None:
                findings.append(
                    "P9 %s is a padded rung (dist %d, channel none) and its "
                    "site 0x%08X is counted under %r. The padding is not there"
                    % (r["name"], r["dist"], a, shape))
    return findings, refusals


def run(elf, hazlint=None, stage2=None, verbose=False):
    hazlint = hazlint or HAZLINT
    if not os.path.isfile(elf):
        raise Refuse("%s: no such file" % elf)
    if not os.path.isfile(hazlint):
        raise Refuse("%s: no hazlint. An absent check is not a passing check"
                     % hazlint)
    rows = hazpay.load_rows()
    syms = hazpay.read_symbols(elf)

    cmd = [sys.executable, hazlint, elf, "--survey", "--max-report", "4096"]
    if stage2:
        cmd += ["--stage2", stage2]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    text = p.stdout + p.stderr
    if verbose:
        print(text)

    print("hazdecl: %s" % os.path.relpath(elf, ROOT))
    print("  hazlint  %s --survey   exit %d" % (os.path.relpath(hazlint, ROOT),
                                                p.returncode))
    parsed = parse_hazlint(text)
    c = parsed["counts"]
    print("  counts   loads %s / nop %s / unresolved %s / notes %s / "
          "VIOLATIONS %s   records parsed %d"
          % (c.get("loads", "?"), c.get("nop", "?"), c.get("unresolved", "?"),
             c.get("notes", "?"), c.get("violations", "?"),
             len(parsed["violations"])))
    for s in SURVEY_SHAPES:
        n, addrs = parsed["survey"].get(s, ("-", []))
        print("  survey   %-34s %s   %s"
              % (s, n, " ".join("0x%08X" % a for a in addrs)))

    dbad = hazpay.check_distances(rows, syms)
    findings, refusals = adjudicate(rows, syms, parsed, p.returncode)
    for name, got, want, why in dbad:
        if why == "distance":
            findings.append("P12 %s: addr(_c) - addr(_p) = %d and the table says "
                            "it must be %d. An instruction sits between the "
                            "producer and its consumer, read out of the "
                            "artefact's symbol table rather than out of the "
                            "source" % (name, got, want))
        else:
            findings.append("P12 %s: %s" % (name, why))

    nmain = sum(1 for r in rows if r["haz"] in ("main", "both"))
    nsurv = sum(1 for r in rows if r["haz"] in ("survey", "both"))
    nnone = sum(1 for r in rows if r["haz"] == "none")
    print("  declared %d row(s): %d main, %d survey, %d none (padded rungs, "
          "which must appear in NEITHER channel)"
          % (len(rows), nmain, nsurv, nnone))

    if refusals:
        print("")
        for x in refusals:
            print("  REFUSED  %s" % x)
        return 3
    if findings:
        print("")
        for x in findings:
            print("  FAIL     %s" % x)
        print("")
        print("  This payload must not be built. %d finding(s)." % len(findings))
        return 1
    print("")
    print("  ok       every declared hazard site is present as built, every "
          "hazard present is declared, no padded rung appears in either "
          "channel, and every distance is 4*(dist+1) in the artefact")
    return 0


# --------------------------------------------------------------------------
# self-test.  No cross-compiler, no ELF: the two functions that do the work are
# pure, and their controls are fixtures.
# --------------------------------------------------------------------------

def _fixture(rows, syms, viol_names, surv_names, extra_viol=None,
             how_override=None, counts_override=None):
    """Build a hazlint report the way hazlint prints one."""
    v = []
    for n in viol_names:
        r = [x for x in rows if x["name"] == n][0]
        pa, ca = syms["rlx_p5_%s_p" % n], syms["rlx_p5_%s_c" % n]
        how = (how_override or {}).get(n)
        if how is None:
            how = ("jump target of 0x%08X" % (pa - 4)
                   if r["family"] == "dslot" else "next word")
        v.append("  0x%08X  file 0x%05X  lw    t1,0(t2)                  "
                 "8d490000  |.I..|\n"
                 "  0x%08X                addu  v0,t1,zero                "
                 "01201021  |. .!|\n"
                 "                             reads $t1   [%s]\n"
                 % (pa, pa - 0x80500000 + 0x10000, ca, how))
    for a, how in (extra_viol or []):
        v.append("  0x%08X  file 0x%05X  lw    t1,0(t2)                  "
                 "8d490000  |.I..|\n"
                 "  0x%08X                addu  v0,t1,zero                "
                 "01201021  |. .!|\n"
                 "                             reads $t1   [%s]\n"
                 % (a, a - 0x80500000 + 0x10000, a + 4, how))
    buckets = {s: [] for s in SURVEY_SHAPES}
    for n in surv_names:
        r = [x for x in rows if x["name"] == n][0]
        buckets[FAMILY_SURVEY[r["family"]]].append(syms["rlx_p5_%s_p" % n])
    co = counts_override or {}
    body = [
        "hazlint 1.5 -- a load whose result is read in the delay slot",
        "  ok    K4  population control  stage2.bin     1474 loads / 646 nop "
        "(43.83%) / 0 violations   expected 1474 / 646 / 0",
        "coverage   32 bytes scanned; 0 bytes named as not scanned",
        "words      8",
        "",
        "  loads (MIPS-I load-to-GPR, rt != $zero)          %d"
        % co.get("loads", 100),
        "  followed by an explicit nop                      40   (40.00%)",
        "  successor unresolved                             %d"
        % co.get("unresolved", 0),
        "  notes (a stated limit, not a finding)            0",
        "  VIOLATIONS                                       %d"
        % co.get("violations", len(viol_names) + len(extra_viol or [])),
        "",
        "  a load whose result is read by the very next instruction. On",
        "  this core that read gets the PREVIOUS value: no fault, no",
        "  warning, just wrong.",
        "",
    ]
    body += ["".join(v).rstrip("\n"), ""]
    body += ["  survey -- hazard shapes with NO established rule on this core.",
             "  C-9 / F47 is open and R1b owns it.  Counts, not verdicts."]
    for s in SURVEY_SHAPES:
        addrs = buckets[s]
        body.append("    %-36s %d   %s"
                    % (s, len(addrs), " ".join("0x%08X" % a for a in addrs)))
    body += ["", "RESULT: %d violation(s). This payload must not be run on this "
                 "core." % co.get("violations", len(viol_names))]
    return "\n".join(body) + "\n"


def self_test():
    ok = n = 0
    fails = []

    def case(label, fn):
        nonlocal ok, n
        n += 1
        try:
            fn()
            ok += 1
            print("  ok    %s" % label)
        except AssertionError as e:
            fails.append(label)
            print("  FAIL  %s -- %s" % (label, e))
        except Exception as e:                          # noqa: BLE001
            fails.append(label)
            print("  FAIL  %s -- %s: %s" % (label, type(e).__name__, e))

    print("hazdecl self-test")
    print("")
    try:
        rows = hazpay.load_rows()
    except Refuse as e:
        print("  REFUSING: the committed hazard table does not parse (%s)" % e)
        return 3

    # a synthetic symbol table with the right distances
    syms, a = {}, 0x80500100
    for r in rows:
        syms["rlx_p5_%s_p" % r["name"]] = a
        syms["rlx_p5_%s_c" % r["name"]] = a + 4 * (r["dist"] + 1)
        a += 0x100
    MAIN = [r["name"] for r in rows if r["haz"] in ("main", "both")]
    SURV = [r["name"] for r in rows if r["haz"] in ("survey", "both")]
    NONE = [r["name"] for r in rows if r["haz"] == "none"]

    def healthy():
        return _fixture(rows, syms, MAIN, SURV)

    def d1():
        p = parse_hazlint(healthy())
        assert len(p["violations"]) == len(MAIN), p["violations"]
        assert p["counts"]["violations"] == len(MAIN)
        assert p["counts"]["loads"] == 100
        got = sorted(x for s in SURVEY_SHAPES for x in p["survey"][s][1])
        want = sorted(syms["rlx_p5_%s_p" % x] for x in SURV)
        assert got == want, (got, want)
    case("D1  the fixture parses to the declared records and survey hits", d1)

    def d2():
        """THE POSITIVE CONTROL ON THE WHOLE TOOL.  A checker that never passes
        is as useless as one that never fails."""
        f, rf = adjudicate(rows, syms, parse_hazlint(healthy()), 1)
        assert not rf, rf
        assert not f, f
    case("D2  a healthy report produces no finding and no refusal", d2)

    def d3():
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   counts_override={"violations": 99}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P1") for x in rf), rf
    case("D3  P1 record count != VIOLATIONS count REFUSES", d3)

    def d4():
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   counts_override={"loads": 0}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P2") for x in rf), rf
    case("D4  P2 zero loads REFUSES", d4)

    def d5():
        f, rf = adjudicate(rows, syms, parse_hazlint(healthy()), 0)
        assert any(x.startswith("P4") for x in f), f
        assert "compiled away" in " ".join(f)
    case("D5  P4 hazlint exit 0 is a FINDING -- the inversion", d5)

    def d6():
        f, rf = adjudicate(rows, syms, parse_hazlint(healthy()), 2)
        assert any(x.startswith("P4") for x in rf), rf
    case("D6  P4 hazlint exit 2 REFUSES -- a refusal is not a verdict", d6)

    def d7():
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   extra_viol=[(0x80509000, "next word")],
                                   counts_override={"violations": len(MAIN) + 1}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P5") and "no declared site" in x for x in f), f
    case("D7  P5 an undeclared violation is a finding", d7)

    def d8():
        p = parse_hazlint(rows and healthy() or "")
        # drop one declared main site from the list
        short = [x for x in MAIN if x != MAIN[0]]
        p = parse_hazlint(_fixture(rows, syms, short, SURV))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P6") and MAIN[0] in x for x in f), f
        assert "NOT PRESENT AS BUILT" in " ".join(f)
    case("D8  P6 a declared site hazlint did not report is a finding", d8)

    def d9():
        p = parse_hazlint(_fixture(rows, syms, SURV, []))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P8") for x in f), f
    case("D9  P8 a declared survey site missing from the bucket is a finding",
         d9)

    def d10():
        """The direction that proves the padding is there."""
        pad = NONE[0]
        p = parse_hazlint(_fixture(rows, syms, MAIN + [pad], SURV))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P9") and pad in x for x in f), f
        assert "THE PADDING IS NOT THERE" in " ".join(f)
    case("D10 P9 a padded rung appearing in the violation list is a finding",
         d10)

    def d10b():
        """P9's OTHER half, and it was missing.

        🔴 `tools/test-hazpay.py`'s mutant that removes the survey half of P9
        SURVIVED: D10 puts a padded rung in the violation list, so nothing tested
        the survey side.  A padded `dslot` rung is the live case -- 量 2026-09-13,
        `ds_d1`'s site IS in the survey, which is why that family's rungs are
        declared `survey` and not `none` -- so the fixture uses a rung from a
        family whose padded rungs really are `none`."""
        pad = [r["name"] for r in rows
               if r["haz"] == "none" and FAMILY_SURVEY[r["family"]] is not None]
        assert pad, "no `none` rung belongs to a family with a survey bucket"
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV + [pad[0]]))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P9") and pad[0] in x for x in f), f
        assert "The padding is not there" in " ".join(f)
    case("D10b P9 a padded rung counted by the SURVEY is a finding", d10b)

    def d11():
        ds = [r["name"] for r in rows if r["family"] == "dslot"
              and r["haz"] in ("main", "both")]
        assert ds, "the table has no dslot row in the main channel"
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   how_override={ds[0]: "next word"}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P11") and ds[0] in x for x in f), f
    case("D11 P11 a dslot record reached as the next word is a finding", d11)

    def d12():
        lu = [r["name"] for r in rows if r["family"] == "loaduse"
              and r["haz"] in ("main", "both")][0]
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   how_override={lu: "jump target of 0x80500000"}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P11") and lu in x for x in f), f
    case("D12 P11 the converse: a non-dslot row reached through a branch is a "
         "finding", d12)

    def d13():
        p = parse_hazlint(_fixture(rows, syms, MAIN, SURV,
                                   counts_override={"unresolved": 3}))
        f, rf = adjudicate(rows, syms, p, 1)
        assert any(x.startswith("P3") for x in f), f
    case("D13 P3 an unresolved successor is a finding", d13)

    def d14():
        bad = dict(syms)
        nm = "rlx_p5_%s_c" % rows[0]["name"]
        bad[nm] = bad[nm] + 4
        dbad = hazpay.check_distances(rows, bad)
        assert any(x[0] == rows[0]["name"] and x[3] == "distance" for x in dbad), \
            dbad
        assert not hazpay.check_distances(rows, syms), "the healthy arm"
    case("D14 P12 a one-instruction shift in the artefact is caught, and the "
         "healthy arm is clean", d14)

    def d15():
        bad = {k: v for k, v in syms.items()
               if k != "rlx_p5_%s_p" % rows[0]["name"]}
        f, rf = adjudicate(rows, bad, parse_hazlint(healthy()), 1)
        assert any(x.startswith("P5") and "pass by being blind" in x
                   for x in rf), rf
    case("D15 a missing site symbol REFUSES rather than passing blind", d15)

    def d16():
        t = healthy().replace("mtc0 then mfc0", "mtc0 then something new")
        try:
            parse_hazlint(t)
        except Refuse as e:
            assert "does not know" in str(e), e
            return
        raise AssertionError("an unknown survey shape must REFUSE")
    case("D16 P10 an unknown survey shape name REFUSES", d16)

    def d17():
        """The format is read by LABEL, not by line number.  Shifting the block
        must not change the answer."""
        t = "junk\n\n" * 7 + healthy()
        p = parse_hazlint(t)
        assert p["counts"]["violations"] == len(MAIN)
        assert len(p["violations"]) == len(MAIN)
    case("D17 the parser is label-anchored, not line-anchored", d17)

    def d18():
        """量 2026-09-13: hazlint's K2 control line says `Expected: 2 violations`
        and a grep-based parser read 2 for every case including the negative
        control.  The fixture carries a K-line with a number in it, and the
        parser must not pick it up."""
        t = healthy().replace(
            "  ok    K4  population control",
            "  ok    K2  negative control  P9-12 v1, 148 B  2 loads / "
            "2 violations\n  ok    K4  population control")
        p = parse_hazlint(t)
        assert p["counts"]["violations"] == len(MAIN), p["counts"]
    case("D18 a control line containing a violation count is not mistaken for "
         "the summary", d18)

    print("")
    print("self-test: %d of %d" % (ok, n))
    if fails:
        print("  failed: %s" % ", ".join(fails))
    return 0 if ok == n else 1


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("elf", nargs="?")
    ap.add_argument("--hazlint")
    ap.add_argument("--stage2")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.elf:
        print("hazdecl: no ELF. --self-test runs the controls alone.",
              file=sys.stderr)
        return 3
    return run(a.elf, a.hazlint, a.stage2, a.verbose)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Refuse as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        sys.exit(3)
