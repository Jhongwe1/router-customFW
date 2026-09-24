#!/usr/bin/env python3
"""test-cardcheck-mutants -- the mutation suite for tools/cardcheck.py.

Every mutation must make `--self-test` exit non-zero, and every row NAMES the
control it must turn red.  That naming is not decoration: `tools/flashwin.py`'s
first mutation pass reported 8/8 killed and **every kill was invalid**, because
the harness was red before any mutation was applied.

🔴 **So the FIRST case is the unmutated baseline through the same harness**, and
a mutation whose anchor is missing is reported as a SURVIVOR rather than skipped
-- a moved anchor and a mutation that changed nothing look identical from the
exit code, and only one of them is fine.

🔄 2026-09-23 (`P2-2`, `FW-113`).  THE NAMING ABOVE WAS DECORATION IN THIS FILE
UNTIL TODAY.  A kill was `rc != 0` and nothing read WHICH case went red, so a
mutant that crashed the tool before it reached its controls -- or turned some
other case red -- counted as a kill.  `test-flashwin-mutants.py`'s `W0`
records five of fourteen rows of another suite counted exactly that way on
2026-08-31.  So now, as there: a kill must turn EVERY case its row names red
(`^  FAIL  <tag>` in the self-test's output), a row that names none cannot be
a kill, and a mutant that does not compile is reported INVALID, never killed.
量 on its first run it found two such rows here, both counted as kills by
the run just before it: `M1`, which never compiled, and `M11`, whose rc 1
was an AttributeError before `A13` could go red.  Each row says what changed.

`--jobs N` (2026-09-23)
-----------------------
量: serially this suite took 1,663 s, on every push.  `--jobs N` runs N rows
at once through a thread pool, as `test-leakscan-mutants.py` does; the
default, 1, is the serial run.  Concurrency puts three things at risk, and
each is held by something that can fail:

  * ISOLATION, `I0`.  Every row gets its own root, all allocated before the
    pool starts so the set can be checked -- distinct, none inside another.
    A worker CLAIMS its root with an O_EXCL owner token before writing, writes
    only below it, and after the self-test re-reads the mutant it wrote and
    the token it claimed.  A root handed to two workers, or a mutant another
    worker overwrote, is a FAIL on that row, never a kill.  `I0`'s own
    control runs first, on one root claimed twice.  And the source every
    worker copied from must be unchanged at the end, or the run refuses.
    ⚠️ What it cannot see: the files the TOOL writes through `tempfile`, which
    are unique by the library's own O_EXCL, not by anything here.
  * ORDER.  Rows are submitted, and printed, sorted by their `M<n>` id
    whatever order they finish in, so two runs diff line for line; each line
    carries every case that went red, not only the named ones.
  * THE VERDICT.  A changed instrument is accepted only if it reproduces the
    old verdicts on the same population (`CLAUDE.md`): serial and `--jobs N`
    must print the same lines, red sets included.  The baseline, `W0` and
    `I0` run before any row, in both.

🔄 2026-09-24 (`FW-124`): TWO FILES CAN BE MUTATED, AND THE TREE HOLDS
EVERYTHING THE SELF-TEST LOADS.  cardcheck now reads a card's HOST cells
through `tools/cardrun.py` -- the runner, the card grammar's one owner --
and judges each project tool with that tool's own build_parser() and
refuse_args(), loaded by path.  So a row may name a fourth field, the file
it mutates (`tools/cardrun.py`; the default is `tools/cardcheck.py`), and
both files are read once at the start and checked unchanged at the end.
COPIED lists every other file the self-test opens: a file missing from it
makes B13 or B14 red in the temp tree, and B0-in-tree refuses the whole run
before any row counts -- which is how a tool a future card calls announces
that it belongs on the list.

Run:  /usr/bin/python3 tools/test-cardcheck-mutants.py [--jobs N]
"""
import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/cardcheck.py")
# The files a row may mutate, read once; cardcheck.py is the one that runs.
TARGETS = ("tools/cardcheck.py", "tools/cardrun.py")
# Every other file cardcheck's --self-test reads, copied as they are:
# reply-size.py (dwreply), ci-expected.tsv, and each tool a corpus HOST cell
# invokes -- loaded for its build_parser()/refuse_args() -- with flashwin.py,
# which flashmap.py imports.
COPIED = ("tools/reply-size.py", "tools/ci-expected.tsv", "tools/hostprobe.py",
          "tools/looprun.py", "tools/boot-timeline.py", "tools/netblast.py",
          "tools/flashmap.py", "tools/flashwin.py", "tools/hostclock.py")

MUT = [
    # 🔄 2026-09-23: THIS ROW NEVER COMPILED, and it read as a kill.  Its
    # anchor was the first line of a two-line call, so the mutant left the
    # second line an indented orphan -- IndentationError, rc 1, no control
    # reached.  讀 git: the row and the two-line call are the same at every
    # commit of either file since the suite arrived (195ae3d, 2026-08-31).
    # The W0 check above found it on its first run; the anchor now takes
    # both lines.
    ("M1  the NOT-IN-IMAGE verdict deleted                  (kills A2)",
     '        issues.append(f"{base}: NOT IN IMAGE -- not among the "\n'
     '                      f"{len(names)} declared invocable names")',
     '        pass  # the NOT IN IMAGE verdict, deleted'),

    ("M2  every name treated as invocable                   (kills A2)",
     "        if base in names:\n            continue",
     "        if True:\n            continue"),

    ("M3  the redirection target check deleted              (kills A9)",
     "    for t in redirect_targets(cmd):",
     "    for t in []:"),

    ("M4  only the FIRST word of a pipeline is checked      (kills A10)",
     "        if w in SEPARATORS:\n            expect_cmd = True",
     "        if w in SEPARATORS:\n            expect_cmd = False"),

    ("M5  a redirection TARGET is treated as a command      (kills B6)     ",
     '        if re.match(r"^\\d*[<>]{1,2}$", w):          # a free redirection\n'
     "            i += 2                                  # skip it AND its target",
     '        if re.match(r"^\\d*[<>]{1,2}$", w):          # a free redirection\n'
     "            i += 1"),

    # 🔴 M6's anchor was `if first in LOADER_VERBS:` immediately followed by
    # `return "LOADER", []`, and 2026-09-03 put the FLR guard between them, so
    # the anchor stopped occurring.  The suite reported `ANCHOR x0 (not
    # applied)` and FAILED rather than passing -- which is the behaviour that
    # made the edit visible.  Re-anchored on the two lines above the branch,
    # which do not move when a branch body grows.
    # 🔄 2026-09-23: and they moved anyway, when `FW-113`'s check went in
    # between them.  Anchored now on the branch line alone, which occurs once.
    ("M6  loader verbs looked up as shell names             (kills A7)",
     '    if first in LOADER_VERBS:\n',
     '    if False:\n'),

    # ------------------------------------------------------------ the FLR guard
    ("M19 the FLR bypass issue is not reported              (kills A19)",
     '        if first == "FLR" and not allow_flr:',
     '        if False and not allow_flr:'),

    ("M20 the guard becomes a blanket over every loader verb (kills A21)",
     '        if first == "FLR" and not allow_flr:',
     '        if first != "" and not allow_flr:'),

    # B10 is checked in BOTH directions, so it needs one mutant per direction.
    ("M21 a card that no longer types FLR stays on the list  (kills B10)",
     '    "bench/2026-08-30c/PREDICTIONS-B5-block2.md",',
     '    "bench/2026-08-30c/PREDICTIONS-B5-block2.md",\n'
     '    "bench/2026-09-02/PREDICTIONS-B8-block7.md",'),

    ("M22 a card that DOES type FLR is dropped from the list (kills B10, A11)",
     '    "bench/2026-08-31/PREDICTIONS-B5-block3.md",',
     '    "bench/2026-08-31/PREDICTIONS-B5-block3-NOTHING.md",'),

    # `CARD-4`, 2026-09-17.  Two mutants because the change has two halves
    # that fail in opposite directions: the census can stop being READ, and
    # the branch that consumes it can stop being TAKEN.  One mutant would
    # leave the other half unobserved.
    ("M23 the measured builtin census parses to nothing     (kills A25)",
     '        if len(parts) >= 2 and parts[0] == "builtin":',
     '        if False:'),

    ("M24 the measured branch is never taken                (kills A27)",
     "        if base in _measured():\n            continue",
     "        if False:\n            continue"),

    # ------------------------------------------------ `FW-113`, 2026-09-23
    # The flash-write refusal.  One mutant per property the rule claims, and
    # each names the ONE case that must go red: the refusal itself, its case
    # blindness, the one `AUTOBURN` it permits, the exactness of the yes (a
    # prefix, and whitespace: normalising it was the first design, and
    # owner_yes() says why it was refused), the exemption's key, the absence
    # filter, the yes's own defects, and B12 in both directions.
    ("M25 the flash-write refusal removed                   (kills A29)",
     '    if flash_write(cmd):\n'
     '        return "LOADER", ([] if cmd in flash_ok else [flash_write(cmd)])',
     '    if False:\n'
     '        return "LOADER", ([] if cmd in flash_ok else [flash_write(cmd)])'),

    ("M26 the verb matched case-SENSITIVELY                 (kills A30)",
     '    v = w[0].upper() if w else ""',
     '    v = w[0] if w else ""'),

    ("M27 `AUTOBURN 0` refused along with the rest          (kills A21)",
     '    elif v == "AUTOBURN" and cmd.strip() != "AUTOBURN 0":',
     '    elif v == "AUTOBURN":'),

    ("M28 the yes matched by PREFIX                         (kills A33)",
     '        return "LOADER", ([] if cmd in flash_ok else [flash_write(cmd)])',
     '        return "LOADER", ([] if any(cmd.startswith(p) for p in flash_ok)'
     ' else [flash_write(cmd)])'),

    ("M29 the yes matched after whitespace normalisation    (kills A33)",
     '        return "LOADER", ([] if cmd in flash_ok else [flash_write(cmd)])',
     '        return "LOADER", ([] if " ".join(cmd.split()) in '
     '{" ".join(p.split()) for p in flash_ok} else [flash_write(cmd)])'),

    ("M30 the frozen exemption keyed by a path PATTERN      (kills A36)",
     r'    legacy = FLASH_LEGACY_CARDS.get(card_rel.replace("\\", "/"), '
     r'frozenset())',
     r'    legacy = next((v for k, v in FLASH_LEGACY_CARDS.items() if '
     r'card_rel.replace("\\", "/").endswith(k)), frozenset())'),

    ("M31 the absence filter reaches LOADER issues again    (kills A35)",
     '    if kind == "LOADER":\n        return list(issues)',
     '    if False:\n        return list(issues)'),

    ("M32 a yes with an impossible date accepted            (kills A32)",
     '                    datetime.date.fromisoformat(date)',
     '                    pass'),

    ("M33 a second yes for one payload accepted             (kills A32)",
     '            if not ok or payload in yes:',
     '            if not ok:'),

    ("M34 a yes that permits nothing goes unreported        (kills A34)",
     '        if payload not in used:',
     '        if False:'),

    ("M35 the owner's yes permits nothing                   (kills A31)",
     '    return frozenset(yes) | legacy, bad',
     '    return legacy, bad'),

    # B12 is checked in BOTH directions, so it needs one mutant per direction,
    # as B10 has M21 and M22.
    ("M36 a frozen pair that IS sent dropped from the list  (kills B12, A36)",
     '        "EW B800311C 240000", "EW B800311C 40000"}),',
     '        "EW B800311C 240000"}),'),

    ("M37 a pair no card sends added to the list            (kills B12)",
     '    "bench/2026-08-24c/PREDICTIONS-block3.md": frozenset({\n'
     '        "EW B800311C 240000"}),',
     '    "bench/2026-08-24c/PREDICTIONS-block3.md": frozenset({\n'
     '        "EW B800311C 240000", "EW 8040D4A0 1"}),'),

    ("M7  MDIOR removed from the verb list                  (kills B2)",
     '"PHYR", "PHYW", "MDIOR", "MDIOW",',
     '"PHYR", "PHYW", "MDIOW",'),

    ("M8  a card with no --send reports clean               (kills A12)",
     "    if not pairs:\n        raise Refuse(",
     "    if False:\n        raise Refuse("),

    ("M9  an empty declaration is accepted                  (kills A18)",
     "    if rows == 0:\n        raise Refuse(",
     "    if False:\n        raise Refuse("),

    ("M10 `nod` entries made invocable                      (kills B7)      ",
     '        if kind in ("slink", "file"):',
     '        if kind in ("slink", "file", "nod"):'),

    # 🔄 2026-09-23: THIS ROW'S KILL WAS A CRASH.  Skipping the refusal fell
    # through to `m.group(1)` on None -- AttributeError, a traceback, rc 1 --
    # and A13, which catches `Refuse` only, never went red.  W0 found it.  It
    # now does what its label says: it REPORTS, 0 bad, where it should refuse.
    ("M11 the missing cardnum fence reports instead of refusing (kills A13)",
     "    if not m:\n        raise Refuse(",
     "    if not m:\n        return 0\n        raise Refuse("),

    ("M12 a number mismatch is not counted                  (kills A15)",
     "        if got.lower() != want.lower():",
     "        if False:"),

    ("M13 an unknown expression evaluates to the empty string (kills A17)",
     '    raise Refuse(f"unknown expression `{op}`")',
     '    return ""'),

    ("M14 dwreply returns the tuple, not the byte count     (kills A16)",
     "        if isinstance(got, tuple):\n            got = got[0]",
     "        if False:\n            got = got[0]"),

    # 🔄 2026-09-23: the filter moved into `unsuppressed()` (`FW-113`), and
    # the anchor moved with it.
    ("M15 the absence declaration suppresses EVERYTHING     (kills B4)",
     '    return [i for i in issues if i.split(":")[0] not in absent]',
     "    return [] if absent else list(issues)"),

    ("M16 the cell id is dropped from the report            (kills B5)",
     '        report(f"  FAIL  {cid}: {cmd}")',
     '        report(f"  FAIL  {cmd}")'),

    ("M17 zerorun-tail counts from the front                (kills A14)",
     "        while n < len(blob) and blob[len(blob) - 1 - n] == 0:",
     "        while n < len(blob) and blob[n] == 0:"),

    ("M18 word32 read little-endian                         (kills A14)",
     'return "%08X" % int.from_bytes(blob[off:off + 4], "big")',
     'return "%08X" % int.from_bytes(blob[off:off + 4], "little")'),

    # ------------------------------------------------ `FW-124`, 2026-09-24
    # A HOST cell whose own tool rejects its arguments.  One mutant per rule,
    # each naming the case that must go red; a `[cardrun]` row mutates
    # tools/cardrun.py, the grammar's owner, and the fourth field says so.
    ("M38 a tool's refusal is not recorded                   (kills A37)",
     '                census["tool_refused"] += 1\n'
     '                why.append(reason)',
     '                census["tool_refused"] += 1\n'
     '                pass'),

    ("M39 the parser's own error line replaced by a word     (kills A37)",
     '            return "REFUSED", _error_line(err, rel)',
     '            return "REFUSED", "rejected by its parser"'),

    ("M40 the HOST command is not macro-expanded             (kills A38)",
     '        sims = cr.simple_commands(cr.expand(cmd, table))',
     '        sims = cr.simple_commands(cmd)'),

    ("M41 every project-tool command refused (a blanket)     (kills A39)",
     '    return "accepted", ""',
     '    return "REFUSED", "every tool command refused"'),

    ("M42 a tool's arguments checked against the disk        (kills A40)",
     '        _ns, err2, ap2 = _parse(mod, path, args, exact=True)',
     '        if any(os.path.exists(x) for x in args):\n'
     '            return "REFUSED", "an argument names a path that exists"\n'
     '        _ns, err2, ap2 = _parse(mod, path, args, exact=True)'),

    ("M43 refuse_args never called                           (kills A41)",
     '                mod.refuse_args(ns)',
     '                pass'),

    ("M44 a tool without the contract passes                 (kills A42)",
     '        return "REFUSED", (f"{rel} does not carry the FW-124 contract (no "',
     '        return "accepted", (f"{rel} does not carry the FW-124 contract (no "'),

    ("M45 the undefined-macro test on every ALL-CAPS word    (kills A43)",
     '    if not a0.quoted and re.fullmatch(r"[A-Z][A-Z0-9]*", a0.text):',
     '    if any(re.fullmatch(r"[A-Z][A-Z0-9]*", w.text) for w in argv):'),

    ("M46 [cardrun] the timeout wrapper not stripped         (kills A44)",
     '        if t == "timeout":',
     '        if False:',
     "tools/cardrun.py"),

    ("M47 [cardrun] single quotes not honoured               (kills A44)",
     '        if c == "\'":',
     '        if False:',
     "tools/cardrun.py"),

    ("M48 shell expansion accepted in a tool's arguments     (kills A44)",
     '        exp = [w.raw for w in tool[1] if w.expands or w.globs]',
     '        exp = []'),

    ("M49 a crash counted as accepted                        (kills A45)",
     '    except BaseException as e:\n'
     '        raise Refuse(f"{rel} CRASHED while checking',
     '    except BaseException as e:\n'
     '        return "accepted", ""\n'
     '        raise Refuse(f"{rel} CRASHED while checking'),

    ("M50 the exact-option rule removed                      (kills A46)",
     '        if err2:\n'
     '            return "REFUSED", _abbreviation(ap2, args, err2, rel)',
     '        if False:\n'
     '            return "REFUSED", _abbreviation(ap2, args, err2, rel)'),

    ("M51 [cardrun] a macro defined twice accepted           (kills A47)",
     '        if name in table:\n'
     '            raise Refused("macro',
     '        if False:\n'
     '            raise Refused("macro',
     "tools/cardrun.py"),

    # Not `if False:` alone: expand() would then read `.group` on None and
    # the self-test would die before A47 -- a crash, which W0 never counts.
    ("M52 [cardrun] a <p> macro expands with an empty argument (kills A47)",
     '            if not a or OPERATOR_WORD_RE.match(a.group(1)):\n'
     '                raise Refused("macro',
     '            if not a or OPERATOR_WORD_RE.match(a.group(1)):\n'
     '                a = re.match(r"()", "")\n'
     '            if False:\n'
     '                raise Refused("macro',
     "tools/cardrun.py"),

    ("M53 the unchecked system commands unnamed in the summary (kills A48)",
     '            + (f": {names}" if names else "")',
     '            + ""'),

    ("M54 the HOST check unwired from `commands`             (kills A49)",
     '    bad += idle_bad + host_cells(card_rel, text, report)',
     '    bad += idle_bad'),

    # B13 is swept in both directions and at the grain of the defect, so it
    # has a mutant for each: a refused pair dropped, a pair nothing refuses
    # added, and a pair whose fragment its refusal does not carry.
    ("M55 a FROZEN pair that IS refused dropped from the list (kills B13, A49)",
     '    "bench/2026-09-23/PREDICTIONS-B44-block42.md": {\n'
     '        "Z9-D2": ("argument --tsv: expected one argument",',
     '    "bench/2026-09-23/PREDICTIONS-B44-block42.md": {} and {\n'
     '        "Z9-D2": ("argument --tsv: expected one argument",'),

    ("M56 a pair no card refuses added to the list           (kills B13)",
     '        "Z9-D2": ("argument --tsv: expected one argument",',
     '        "P1-HP": ("--seconds N is required", "a pair nothing refuses"),\n'
     '        "Z9-D2": ("argument --tsv: expected one argument",'),

    ("M57 a pair's fragment is not what its refusal carries  (kills B13, A49)",
     '        "Z9-D2": ("argument --tsv: expected one argument",',
     '        "Z9-D2": ("argument --tsv: expected two arguments",'),

    ("M58 [cardrun] the HOST line regex misses HOST&         (kills B14)",
     'HOST_LINE_RE = re.compile(r"^(HOST&?) (\\S+) :: (.*)$", re.M)',
     'HOST_LINE_RE = re.compile(r"^(HOST) (\\S+) :: (.*)$", re.M)',
     "tools/cardrun.py"),

    ("M59 [cardrun] a VAR= prefix not stripped               (kills B14)",
     '        if not words and ASSIGN_RE.match(val.raw):',
     '        if False:',
     "tools/cardrun.py"),
]


# A self-test row that went red: `  FAIL  A29 ...`.  The harness's own lines
# never reach this; it reads the self-test's stdout only.
CASE = re.compile(r"^  FAIL  +([AB][0-9]+)\b", re.M)


def run(path, cwd):
    r = subprocess.run([sys.executable, path, "--self-test"],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout


def named(name):
    """The cases a row says it turns red: `(kills A2)` -> ['A2'],
    `(kills B10, A11)` -> ['B10', 'A11'].  Empty when the row names none,
    and such a row cannot be counted as a kill."""
    m = re.search(r"\(kills ([^)]*)\)", name)
    return re.findall(r"\b[AB][0-9]+\b", m.group(1)) if m else []


def row_id(name):
    """`M25 the flash-write ...` -> 25, or None.  Rows are submitted and
    printed in this order, so the output does not depend on `--jobs`."""
    m = re.match(r"M([0-9]+)\b", name)
    return int(m.group(1)) if m else None


def case_key(tag):
    """A2 < A10 < B1: the letter, then the number."""
    return tag[0], int(tag[1:])


# 🔴 I0 -- see the docstring.  The token sits in the row's root, beside the
# tree the tool runs in and never inside it.
OWNER = ".cardcheck-mutant-owner"


def overlapping(roots):
    """-> pairs of roots where one IS the other or lies inside it.  With a
    trailing separator every path under a root sorts straight after it, so
    neighbours are enough."""
    rs = sorted(os.path.realpath(r).rstrip(os.sep) + os.sep for r in roots)
    return [(a, b) for a, b in zip(rs, rs[1:]) if b.startswith(a)]


def claim(root, who):
    """Write `who` into `root`'s owner token.  O_EXCL: of two workers handed
    one root, exactly one succeeds and the other gets FileExistsError."""
    fd = os.open(os.path.join(root, OWNER),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(who)


def owner(root):
    try:
        with open(os.path.join(root, OWNER), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def one(name, old, new, target, srcs, root):
    """One row, in its own `root`, mutating `target`.  -> {"line",
    "survived", "breach"} or {"refuse"}.  It never exits and never raises:
    `sys.exit` in a pool thread ends only that thread, and a traceback is
    not a refusal."""
    rid, mine = name.split()[0], False
    try:
        try:
            claim(root, rid)
            mine = True
        except FileExistsError:
            why = f"ISOLATION: its root was already claimed by {owner(root)!r}"
            return {"line": f"  FAIL  {name}   {why}",
                    "survived": f"{name}  [{why}]", "breach": True}
        work = os.path.join(root, "router-rebuild")
        tgt = os.path.join(work, target)
        tool = os.path.join(work, "tools/cardcheck.py")
        if os.path.commonpath([root, tgt]) != root:
            why = "ISOLATION: the mutant would be written outside its root"
            return {"line": f"  FAIL  {name}   {why}",
                    "survived": f"{name}  [{why}]", "breach": True}
        os.makedirs(os.path.join(work, "tools"))
        for rel in ("bench", "config"):
            shutil.copytree(os.path.join(ROOT, rel),
                            os.path.join(work, rel), symlinks=True)
        for rel in COPIED:
            shutil.copy(os.path.join(ROOT, rel), os.path.join(work, rel))
        # 🔴 B0-IN-TREE.  The baseline above runs from the REAL root; this
        # runs the UNMUTATED tool from the temp tree, which is where every
        # mutation is judged.  A tree missing a file the tool reads makes
        # the whole run red before any mutation is applied, and a list of
        # kills looks identical either way.  量 2026-08-31: exactly that
        # happened to test-replay-capture-mutants, and the only thing that
        # caught it was a row required to SURVIVE.  It writes the bytes read
        # at the start, not the files on disk, so every row tests the same.
        for rel, text in srcs.items():
            with open(os.path.join(work, rel), "w", encoding="utf-8") as f:
                f.write(text)
        if run(tool, work)[0] != 0:
            return {"refuse": f"REFUSING at {name}: the UNMUTATED tool fails "
                              f"in the temp tree, so every kill would be "
                              f"invalid"}
        src = srcs[target]
        n = src.count(old)
        if n != 1:
            return {"line": f"  FAIL  {name}   ANCHOR x{n} (not applied)",
                    "survived": f"{name}  [anchor occurs {n} times, "
                                f"not applied]"}
        mutated = src.replace(old, new, 1)
        # A mutant that does not compile exits non-zero without reaching a
        # single control, and would read as a kill.
        try:
            compile(mutated, tgt, "exec")
        except SyntaxError as e:
            return {"line": f"  FAIL  {name}   INVALID-MUTANT: {e}",
                    "survived": f"{name}  [INVALID-MUTANT: {e}]"}
        with open(tgt, "w", encoding="utf-8") as f:
            f.write(mutated)
        rc, out = run(tool, work)
        # 🔴 I0: the mutant this row judged, and the root, are still its own.
        with open(tgt, encoding="utf-8") as f:
            intact = f.read() == mutated and owner(root) == rid
        # 🔴 W0: a kill is `rc != 0` AND every case the row names red.
        want, red = named(name), set(CASE.findall(out))
        killed = intact and rc != 0 and bool(want) and set(want) <= red
        if not intact:
            wrong = ("  ISOLATION: its mutant or its owner token changed "
                     "while it ran")
        elif killed or rc == 0:
            wrong = ""
        else:
            wrong = (f"  WRONG-CASE: wanted {want or 'a (kills X) tag'} red"
                     + ("" if red else
                        " -- none went red, it did not reach the controls"))
        reds = ",".join(sorted(red, key=case_key)) or "none"
        # `  ok  ` / `  FAIL  ` is the shape tools/ci-census.py parses.
        return {"line": f"  {'ok  ' if killed else 'FAIL'}  {name}   "
                        f"rc={rc} ({'killed' if killed else 'SURVIVED'})"
                        f"{wrong}  red={reds}",
                "survived": None if killed else name + wrong,
                "breach": not intact}
    except Exception as e:
        return {"refuse": f"REFUSING at {name}: the harness failed, not the "
                          f"mutant -- {type(e).__name__}: {e}"}
    finally:
        # Only a root this row claimed is its to delete; one it failed to
        # claim belongs to the row still running in it.  main() clears all.
        if mine:
            shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jobs", type=int, default=1, metavar="N",
                    help="rows run at once (default 1: serial)")
    a = ap.parse_args()
    if a.jobs < 1:
        sys.exit(f"REFUSING: --jobs {a.jobs} -- it counts the rows run at "
                 f"once, so it is at least 1")
    t0 = time.monotonic()
    # Read once, before anything runs: B0-in-tree and every mutant are these
    # bytes, and the run refuses at the end if a file on disk has moved.
    raw = {}
    for rel in TARGETS:
        with open(os.path.join(ROOT, rel), "rb") as f:
            raw[rel] = f.read()
    srcs = {rel: b.decode("utf-8") for rel, b in raw.items()}

    base, _out = run(SRC, ROOT)
    if base != 0:
        sys.exit(f"REFUSING: the unmutated controls already fail (rc={base}). "
                 f"Every 'kill' below would be invalid -- this is the "
                 f"flashwin pass's own defect and it is not repeated.")
    print(f"baseline: unmutated --self-test rc={base}  (B0, and it is a case)")

    # W0's own control, before any mutant runs: on a known output it must
    # count the named case red, and refuse a different red case, a row that
    # names two cases of which one is green, and a row that names none.
    fake = "  ok    A29 x\n  FAIL  A30 y\n  FAIL  B12 z\n"
    red = set(CASE.findall(fake))
    if not (set(named("M (kills A30)")) <= red
            and set(named("M (kills B12, A30)")) <= red
            and not set(named("M (kills A29)")) <= red
            and not set(named("M (kills B12, A29)")) <= red
            and named("M names nothing") == []):
        sys.exit("REFUSING: the named-case check cannot tell a kill from a "
                 "wrong-case exit on a known output, so no kill below would "
                 "mean anything")
    print("W0: the named-case check separates a kill from a wrong-case exit")

    # I0's own control, before any row runs, on real files: one root claimed
    # twice must refuse the second claim and keep the first owner; two roots
    # must both be claimed; and the overlap check must see a repeated root
    # and a nested one, and pass two side by side.
    probe = tempfile.mkdtemp(prefix="cardcheck-i0-")
    try:
        ra, rb = os.path.join(probe, "a"), os.path.join(probe, "b")
        os.mkdir(ra)
        os.mkdir(rb)
        claim(ra, "first")
        try:
            claim(ra, "second")
            twice = True
        except FileExistsError:
            twice = False
        claim(rb, "other")
        i0 = (not twice and owner(ra) == "first" and owner(rb) == "other"
              and bool(overlapping([ra, ra]))
              and bool(overlapping([ra, os.path.join(ra, "x")]))
              and not overlapping([ra, rb]))
    finally:
        shutil.rmtree(probe, ignore_errors=True)
    if not i0:
        sys.exit("REFUSING: the isolation check cannot tell one root handed "
                 "to two workers from two roots, so no row below would be "
                 "known to have run alone")
    print("I0: a root claimed twice, or repeated, or nested, is caught; two "
          "roots pass\n")

    ids = [row_id(r[0]) for r in MUT]
    if None in ids or len(set(ids)) != len(ids):
        sys.exit("REFUSING: every row needs its own `M<n>` id -- the rows "
                 "are run and printed in id order")
    rows = sorted(((r[0], r[1], r[2], r[3] if len(r) > 3 else TARGETS[0])
                   for r in MUT), key=lambda r: row_id(r[0]))
    stray = sorted({r[3] for r in rows} - set(TARGETS))
    if stray:
        sys.exit(f"REFUSING: a row mutates {stray}, which is not one of "
                 f"{TARGETS}: it would never be read back or checked unchanged")
    roots = [tempfile.mkdtemp(prefix="cardcheck-mut-") for _ in rows]
    survived, breaches = [], []
    try:
        clash = overlapping(roots)
        if clash:
            sys.exit(f"REFUSING: two rows were handed overlapping roots, "
                     f"{clash[0][0]} and {clash[0][1]}")
        print(f"{len(rows)} mutation(s), {a.jobs} at a time, each in its own "
              f"root, printed in id order\n", flush=True)
        # Submitted in id order and consumed in id order: a line prints once
        # its row and every row before it have finished, so the output is the
        # same whatever order they finish in, and it still streams.
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = [ex.submit(one, name, old, new, target, srcs, root)
                    for (name, old, new, target), root in zip(rows, roots)]
            for fut in futs:
                res = fut.result()
                if "refuse" in res:
                    for g in futs:
                        g.cancel()
                    sys.exit(res["refuse"])
                print(res["line"], flush=True)
                if res.get("survived"):
                    survived.append(res["survived"])
                if res.get("breach"):
                    breaches.append(res["line"].split()[1])
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
    wall = time.monotonic() - t0

    # 🔴 I0, the last part: every row copied the bytes read at the start, and
    # those must still be the files on disk, or the verdicts are about files
    # that are no longer there.
    for rel in TARGETS:
        with open(os.path.join(ROOT, rel), "rb") as f:
            if f.read() != raw[rel]:
                sys.exit(f"REFUSING: {rel} changed during the run, so every "
                         f"verdict above is about bytes no longer on disk")
    print()
    if breaches:
        print(f"I0: BREACHED on {', '.join(breaches)} -- those rows did not "
              f"run alone")
    else:
        print(f"I0: {len(rows)} row(s) in {len(roots)} distinct, unnested "
              f"roots; every row that ran found its mutant and its owner "
              f"token intact afterwards; {' and '.join(TARGETS)} are still "
              f"the bytes read at the start")
    ran = f"{len(rows)} run, {a.jobs} at a time, {wall:.0f} s wall"
    if survived:
        print(f"🔴 {len(survived)} MUTATION(S) SURVIVED -- those controls "
              f"do not work ({ran}):")
        for s in survived:
            print(f"    {s}")
        return 1
    print(f"all {len(rows)} mutations killed, each turning every case it "
          f"names red ({ran})")
    return 0


sys.exit(main())
