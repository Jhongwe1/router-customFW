#!/usr/bin/env python3
"""test-flrbracket-mutants -- the mutation suite for `tools/flrbracket.py`.

Why this file exists, and why its FIRST case is not a mutant
------------------------------------------------------------
`flrbracket.py` reported 27 green controls on its first run. This repository's
own measurements say that is not evidence of anything:

  * `spec-check.py`        15 green controls,  3 live mutants  (2026-08-30)
  * `console-capture.py`   40 green cases,    10 live mutants  (2026-08-30)
  * `leakscan.py`          17 green controls,  8 live mutants  (2026-08-30)
  * `flashwin.py`          13 green controls, 24 live mutants  (2026-08-30)
  * `flrbracket.py`        29 green controls, 13 live mutants  (2026-08-31)

🔴 **And the `flashwin` pass had to be RE-RUN, because it reported 8 of 8
killed and every kill was invalid.** 量 2026-08-30: `flashwin`'s controls
resolve the repository root with `realpath`, which the mutation harness's
symlink farm sent back to the real tree, so the UNMUTATED file was already 22/24
through that harness -- every "kill" was the harness failing, not the mutation.
An all-killing harness and a harness that tests nothing produce the same
transcript.

So this file has **four** controls of its own, and every one is about the
harness rather than about `flrbracket.py`:

  * **`B0`, first, before any mutant**: the unmutated tool, through this exact
    temp root, must be GREEN. If it is not, the run refuses outright rather
    than reporting kills.
  * **every row names the case it must turn red, and the row is only a kill if
    THAT case is among the failures.** `rc != 0` alone is what made the
    `flashwin` pass invalid. A mutant that goes red for an unrelated reason is
    reported as `WRONG-CASE`, which is a survivor with a different name.
  * 🔴 **a mutant that does not PARSE is `INVALID-MUTANT`, not a survivor and
    not a kill.** `compile()` runs before the temp root is built. Without it a
    broken edit and a weak control share one verdict and are separable only by
    reading a free-text field -- 量, `M20`'s first version left a multi-line
    `return` under a replaced `if` and produced a SyntaxError.
  * 🔴 **the suite has a population control.** `MUT` must hold `DECLARED`
    rows with unique ids, or the run refuses. Deleting a row otherwise reads
    as `n of n killed, 0 alive`, exit 0, green -- which is the exact shape
    `flrbracket.py` is *required* to carry as `Q1` and which the file
    enforcing that rule did not apply to itself.

The harness, and the one thing it may NOT symlink
--------------------------------------------------
`flrbracket.py` computes the repository root from its own `__file__` and
`flashwin._inside_repo` resolves paths with `realpath`. So each mutant gets a
temp root holding a symlink to every top-level entry **except `ci-out/`**,
which the self-test creates itself and which must be a REAL directory: a
symlink there would resolve back to the real repository, `_inside_repo` would
answer *outside*, and `G1`/`G2`/`G5`/`G6` would fail on the unmutated file.
That is the `flashwin` defect exactly, written down in the place that would
repeat it. Verified by construction: rebuilt with `ci-out/` symlinked, the
CLEAN tool goes red on `G1, G2, G5, G6` and `B0` refuses.

What a mutation proves, and what it does not
--------------------------------------------
Each row edits `flrbracket.py` at an anchor that must occur **exactly once**.
A row whose anchor has moved or become ambiguous is reported as a SURVIVOR,
never skipped -- a mutation suite that silently applies nothing is this
repository's "a tool reporting 0 is making a claim", one level up. A surviving
row names a control that does not work. It does not prove the tool is correct.

Run:  /usr/bin/python3 tools/test-flrbracket-mutants.py [--jobs N] [--only M1,M7]
"""
import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "flrbracket.py")

#: 🔴 The self-test needs no vendor artefact, no device, no pty and no
#: `$FWRE_WORK` -- its whole corpus is captures already committed under
#: `bench/`. So this suite declares NO allowed skip, and `tools/ci-expected.tsv`
#: carries `-` for it. Written down because a suite that skips nothing and a
#: suite whose skip nobody declared look identical in a green transcript.
SKIP_LABEL = None

#: The population control's own number, TYPED and not computed -- a count
#: derived from the table it checks would catch nothing. Kept beside `MUT` so a
#: deleted row is
#: a refusal rather than a smaller green run.
DECLARED = 41

# ---------------------------------------------------------------- anchors ---
RE8 = ('    r"Flash read from ([0-9A-Fa-f]{8}) to ([0-9A-Fa-f]{8})"\n'
       '    r" with ([0-9A-Fa-f]{8}) bytes"\n)')
CMP = "    if got_src != src or got_dst != dst or got_len != nbytes:"
PROMPTCHK = "    if PROMPT in reply:\n        return REFUSE, (f\"{PROMPT!r} is in the reply"
CONFIRMCNT = "    if n_confirm != 1:"
CONFIRMORD = "    if body.find(CONFIRM) < ECHO_RE.search(body).start():"
HITSCHK = "    if len(hits) != 1:"
HITSBLOCK = (
    "    if len(hits) != 1:\n"
    '        return REFUSE, (f"the echo \'Flash read from .. to .. with .. '
    'bytes\' "\n'
    '                        f"occurs {len(hits)} time(s), not once -- "\n'
    '                        + ("the loader did not ask" if not hits else\n'
    '                           "which of them is the answer is '
    'undecidable"))')
STRIP = "    if sent and body.startswith(sent):"
NOTTEXT = '        return REFUSE, "the reply is not text"'
YESGUARD = ('    if not isinstance(reply, str):\n'
            '        return UNKNOWN, "the reply is not text"\n'
            '    if SUCCESS in reply:')
ABORTNOTTEXT = ('def classify_abort(reply):\n    """What the reply to `N` says.')
YESPROMPT = "        if PROMPT not in reply:"
SUCCESSIN = "    if SUCCESS in reply:"
ABORTCHK = "    if ABORTED_MSG in reply and PROMPT in reply:"
RBOVERLAP = "    hit = flashwin.overlaps_forbidden(src, nbytes)"
PREINSIDE = ('    if flashwin._inside_repo(path):\n'
             '        return (\n'
             '            f"{path} is inside {repo_root()}.\\n"\n'
             '            "  A PRE-READ may never be written inside this '
             'repository, "')
RANGE0 = "    if nbytes <= 0:"
RANGEDST = "    if dst < RAM_LO or dst + nbytes > RAM_HI:"
CHECKCALL = ("    bad = check_ranges(args.src, args.dst, args.bytes)\n"
             "    if bad:\n"
             "        _fail(bad)")
PREGUARD = ("    bad = preread_target(plan[0][1])\n"
            "    if bad:\n"
            '        _fail(f"the pre-read capture may not go there.\\n  {bad}")')
RBGUARD = ("    bad = readback_target(args.src, args.bytes, plan[3][1])\n"
           "    if bad:\n"
           '        _fail(f"the read-back capture may not go there.\\n  {bad}")')
VERIFYRC = "    return 0 if v == PROCEED else 1"
ABORTRC = "        return 4 if av == ABORTED else 5"
REFUSERC = ("             \"read what comes back.\")\n"
            "        return 3")
YESRC = "    if yv != SUCCEEDED:\n        return 6"
CAPFAIL = ("            if r.returncode != 0:")
METAPATH = ('    meta = log_path[:-4] + ".meta.json" '
            'if log_path.endswith(".log") else None')
SECSFLR = "SECS_FLR = 5.0"
DWPLAN = ('         f"DW {dst:08X} {nbytes // 4}", SECS_DW),\n'
          '        ("FLR"')
C_CONFIRM = 'CONFIRM = "(Y)es , (N)o ?"'
C_PROMPT = 'PROMPT = "<RealTek>"'
C_SUCCESS = 'SUCCESS = "Flash Read Successed!"'
C_ABORT = 'ABORTED_MSG = "Abort!"'

# id, class, what it does, must-turn-red case, [(anchor, replacement), ...]
MUT = [
    # ---- the parser -------------------------------------------------------
    ("M1", "WIDTH", "the hex fields may be any length, not exactly eight",
     "N6",
     [(RE8, '    r"Flash read from ([0-9A-Fa-f]+) to ([0-9A-Fa-f]+)"\n'
            '    r" with ([0-9A-Fa-f]+) bytes"\n)')]),

    # 🔴 M2 is the defect that actually fired on 2026-08-31, put back in one
    # line: compare the flash source as the card TYPED it (six digits) against
    # the loader's echo (zero-padded to eight). It aborted a correct read.
    ("M2", "REGRESSION", "compare the source as typed, six digits, not the "
     "parsed integer -- the 2026-08-31 bug verbatim", "P1",
     [(CMP, '    if (hits[0][0] != f"{src:06X}" or got_dst != dst\n'
            "            or got_len != nbytes):")]),

    ("M3", "BLANKET", "never ABORT -- any well-formed echo PROCEEDs", "N1",
     [(CMP, "    if False:")]),
    ("M6", "ORDER", "the source is compared against the destination and back",
     "P1", [(CMP, "    if got_src != dst or got_dst != src "
                  "or got_len != nbytes:")]),
    ("M8", "PARTIAL", "compare the destination only", "N2",
     [(CMP, "    if got_dst != dst:")]),
    ("M9", "PARTIAL", "compare the source only", "N15",
     [(CMP, "    if got_src != src:")]),
    ("M11", "FIELD", "drop the length term -- the third typed argument goes "
     "unchecked, which is what the shell script did", "N7",
     [(CMP, "    if got_src != src or got_dst != dst:")]),
    # 🔴 An adversarial pass built this one and it survived: the docstring
    # makes a deliberate point of `Flash read` being lower case and
    # `Flash Read Successed!` upper, and nothing pinned it.
    ("M25", "CASE", "the echo pattern becomes case-insensitive, conflating "
     "the two printf sites the docstring separates", "N17",
     [(RE8, '    r"Flash read from ([0-9A-Fa-f]{8}) to ([0-9A-Fa-f]{8})"\n'
            '    r" with ([0-9A-Fa-f]{8}) bytes", re.IGNORECASE\n)')]),

    # ---- the state tests --------------------------------------------------
    ("M4", "GUARD", "<RealTek> in the reply no longer refuses", "N3",
     [(PROMPTCHK, "    if False:\n        return REFUSE, (f\"{PROMPT!r} is in "
                  "the reply")]),
    ("M5", "GUARD", "the confirm-prompt COUNT test is gone -- and the case "
     "is N20, not N4, because with the count gone the ORDERING test still "
     "refuses a reply carrying no prompt at all", "N20",
     [(CONFIRMCNT, "    if False:")]),
    # 🔴 M26/M27 are two spurious PROCEEDs an adversarial pass constructed: a
    # confirm prompt printed BEFORE the echo, and a reply carrying two of them.
    ("M26", "AMBIGUITY", "one confirm prompt or two, either will do", "N20",
     [(CONFIRMCNT, "    if n_confirm < 1:")]),
    ("M27", "ORDER", "the confirm prompt need not come after the echo",
     "N19", [(CONFIRMORD, "    if False:")]),
    # 🔴 M28: running the <RealTek> test on the STRIPPED body instead of the
    # whole reply lets a hand-made `sent` eat a leading prompt.
    ("M28", "SCOPE", "the <RealTek> test runs on the stripped body, so a "
     "leading prompt can be eaten by `sent`", "N18",
     [(PROMPTCHK, "    if PROMPT in (reply[len(sent):] if sent and "
                  "reply.startswith(sent) else reply):\n"
                  "        return REFUSE, (f\"{PROMPT!r} is in the reply")]),
    ("M12", "AMBIGUITY", "take the first echo instead of requiring exactly "
     "one -- and the case is N22, because N8 carries two confirm prompts as "
     "well and the prompt count refuses it first", "N22",
     [(HITSCHK, "    if not hits:")]),
    ("M20", "CONTRACT", "no echo at all becomes ABORT rather than REFUSE -- "
     "so `N` is sent at a prompt that was never asked", "N5",
     [(HITSBLOCK, '    if len(hits) != 1:\n        return ABORT, "no echo"')]),
    ("M7", "WAIVER", "an empty reply is a PROCEED", "N5",
     [(NOTTEXT, NOTTEXT + '\n    if not reply:\n        return PROCEED, "x"')]),

    # ---- the four wire constants, which nothing pinned --------------------
    # 🔴 All four of these SURVIVED the 29-case suite, because every negative
    # fixture built its string out of the constant it was testing -- the
    # `d008372` defect class inside the file written to prevent it. `Q3` and
    # the literal fixtures are the answer.
    ("M29", "CONSTANT", "CONFIRM loosened to '(Y)es'", "Q3",
     [(C_CONFIRM, 'CONFIRM = "(Y)es"')]),
    ("M30", "CONSTANT", "PROMPT loosened to '<Real'", "Q3",
     [(C_PROMPT, 'PROMPT = "<Real"')]),
    ("M31", "CONSTANT", "SUCCESS loosened to 'Successed'", "Q3",
     [(C_SUCCESS, 'SUCCESS = "Successed"')]),
    ("M32", "CONSTANT", "ABORTED_MSG loosened to 'Abort'", "Q3",
     [(C_ABORT, 'ABORTED_MSG = "Abort"')]),

    # ---- the type guards, which no case reached --------------------------
    ("M33", "GUARD", "`classify` no longer refuses a non-string", "N21",
     [(NOTTEXT, "        pass")]),
    ("M34", "GUARD", "`classify_yes` no longer refuses a non-string", "N21",
     [(YESGUARD, "    if SUCCESS in reply:")]),

    # ---- the self-echo strip ---------------------------------------------
    ("M13", "SELF-ECHO", "the operator's own typed line is searched too",
     "N9", [(STRIP, "    if False:")]),
    ("M14", "SELF-ECHO", "`sent_of` never finds the metadata, so `verify` "
     "cannot strip the typed line", "N14",
     [(METAPATH, "    meta = None")]),

    # ---- the other two classifiers ---------------------------------------
    ("M15", "CONTRACT", "'Successed' alone is SUCCEEDED, with no return to "
     "the prompt", "N11", [(YESPROMPT, "        if False:")]),
    ("M16", "CONTRACT", "'Abort!' alone is ABORTED, with no return to the "
     "prompt", "N16", [(ABORTCHK, "    if ABORTED_MSG in reply:")]),
    ("M35", "CONTRACT", "every reply to Y is SUCCEEDED", "N12",
     [(SUCCESSIN, "    if True:")]),

    # ---- the range checks, which make the swap unsendable ----------------
    ("M36", "RANGE", "a zero-length window is accepted -- and the half-open "
     "overlap test cannot see it on the H601 base", "G7",
     [(RANGE0, "    if False:")]),
    ("M37", "RANGE", "the RAM destination is unbounded, so a flash offset "
     "typed into --dst is sendable", "V4",
     [(RANGEDST, "    if False:")]),
    # 🔴 M38 is a POSITION mutant: the range check moved BELOW the dry run, so
    # a card rehearsed at the desk never sees the refusal.
    ("M38", "POSITION", "the range check runs only with --go, so a dry run "
     "rehearses a window that will be refused at the bench", "G7",
     [(CHECKCALL, "    if args.go:\n" + CHECKCALL.replace("    ", "        ", 1)
       .replace("\n    if bad:", "\n        if bad:")
       .replace("\n        _fail(bad)", "\n            _fail(bad)"))]),

    # ---- the exit codes --------------------------------------------------
    ("M21", "CONTRACT", "`verify` always exits 0, so a card written "
     "`flrbracket verify … && send Y` reads a refusal as a pass", "N14",
     [(VERIFYRC, "    return 0")]),
    ("M39", "CONTRACT", "a WRONG echo exits 0, so `run && <next step>` "
     "continues after nothing was read", "R2",
     [(ABORTRC, "        return 0")]),
    ("M40", "CONTRACT", "a REFUSE exits 0", "R4",
     [(REFUSERC, REFUSERC.replace("return 3", "return 0"))]),
    ("M41", "CONTRACT", "a Y that never said 'Successed' exits 0 and takes a "
     "read-back anyway", "R5", [(YESRC, "    if False:\n        pass")]),
    ("M42", "CONTRACT", "a console-capture that exits non-zero is ignored, so "
     "the next step reads a stale .log", "R6",
     [(CAPFAIL, "            if False:")]),

    # ---- the containment guard -------------------------------------------
    ("M17", "CONTAINMENT", "the read-back guard never fires", "G1",
     [(RBOVERLAP, "    hit = None")]),
    ("M22", "BLANKET", "the read-back guard fires on EVERY window", "G3",
     [(RBOVERLAP, "    hit = flashwin.FORBIDDEN[0]")]),
    # 🔴 M18 is the finding that made `--pre-dir` exist: the pre-read's content
    # is decided by --dst's history and `MEM-17` measured DRAM keeping it.
    ("M18", "CONTAINMENT", "the pre-read may go inside the repository", "G6",
     [(PREINSIDE, "    if False:\n" + PREINSIDE.split("\n", 1)[1])]),
    ("M19", "POSITION", "the read-back guard runs on the dry run only, so "
     "`--go` reaches the port with it unchecked", "G5",
     [(RBGUARD, "    bad = (readback_target(args.src, args.bytes, plan[3][1])\n"
                "           if not args.go else None)\n"
                "    if bad:\n"
                '        _fail(f"the read-back capture may not go there.\\n'
                '  {bad}")')]),

    # ---- the plan itself, which `D2` pins against seating 7's own wire ----
    ("M23", "TERMINATOR", "the FLR terminator drifts from 5 s to 4 s", "D2",
     [(SECSFLR, "SECS_FLR = 4.0")]),
    ("M24", "PLAN", "`DW` is given a BYTE count where the loader wants a WORD "
     "count", "D2",
     [(DWPLAN, '         f"DW {dst:08X} {nbytes}", SECS_DW),\n'
               '        ("FLR"')]),
]

FAILRE = re.compile(r"^\s*FAIL\s+(\S+)")


def build_root(mutant_text):
    """A temp root of symlinks, plus one REAL directory.

    🔴 `ci-out/` is deliberately NOT symlinked. `_inside_repo` resolves with
    `realpath`, so a symlink there points back at the real repository and the
    containment cases would answer *outside* on an unmutated file. That is the
    `flashwin` invalid-kill defect; `B0` would catch it, and building it right
    is better than catching it.
    """
    d = os.path.realpath(tempfile.mkdtemp(prefix="flrb-mut-"))
    for e in sorted(os.listdir(ROOT)):
        if e in ("tools", "ci-out"):
            continue
        os.symlink(os.path.join(ROOT, e), os.path.join(d, e))
    os.mkdir(os.path.join(d, "tools"))
    for e in ("flashwin.py", "console-capture.py"):
        os.symlink(os.path.join(ROOT, "tools", e),
                   os.path.join(d, "tools", e))
    with open(os.path.join(d, "tools", "flrbracket.py"), "w",
              encoding="utf-8") as f:
        f.write(mutant_text)
    return d


def run_selftest(root):
    r = subprocess.run([sys.executable,
                        os.path.join(root, "tools", "flrbracket.py"),
                        "--self-test"], capture_output=True, text=True)
    fails = set()
    for line in r.stdout.splitlines():
        m = FAILRE.match(line)
        if m:
            fails.add(m.group(1))
    return r.returncode, fails, r.stdout + r.stderr


def one(row, base):
    mid, klass, what, wants, edits = row
    text = base
    for anchor, repl in edits:
        n = text.count(anchor)
        if n != 1:
            return (mid, "SURVIVOR", klass, what, wants,
                    f"anchor occurs {n} time(s), not once -- it has moved")
        text = text.replace(anchor, repl, 1)
    if text == base:
        return (mid, "SURVIVOR", klass, what, wants, "the edit changed nothing")
    # 🔴 A mutant that does not PARSE tests nothing and must not share a
    # verdict with a real survivor.
    try:
        compile(text, "<mutant>", "exec")
    except SyntaxError as e:
        return (mid, "INVALID-MUTANT", klass, what, wants,
                f"the edit does not parse: line {e.lineno}, {e.msg}")
    d = build_root(text)
    try:
        rc, fails, out = run_selftest(d)
        if rc == 0:
            return (mid, "SURVIVOR", klass, what, wants,
                    "the self-test stayed GREEN")
        if wants not in fails:
            return (mid, "WRONG-CASE", klass, what, wants,
                    f"it went red, but on {sorted(fails) or ['(no case line)']}"
                    f" and not on {wants}")
        return (mid, "killed", klass, what, wants,
                f"{wants} went red (with {len(fails)} case(s) red in total)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()

    # --- the population control, before anything else ---------------------
    ids = [r[0] for r in MUT]
    if len(MUT) != DECLARED or len(set(ids)) != len(ids):
        print(f"🔴 the mutant table is {len(MUT)} rows with "
              f"{len(set(ids))} distinct ids; DECLARED says {DECLARED}.")
        print("   A deleted row would otherwise read as 'n of n killed, "
              "0 alive' and exit 0.")
        return 2

    with open(SRC, "r", encoding="utf-8") as f:
        base = f.read()

    print(f"test-flrbracket-mutants: {len(MUT)} mutants of "
          f"tools/flrbracket.py")
    print()

    # --- B0, and the run stops here if it is not green --------------------
    d = build_root(base)
    try:
        rc, fails, out = run_selftest(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if rc != 0:
        print("🔴 B0 the UNMUTATED tool is not green through this harness. "
              "Refusing to report kills:")
        print("   every mutant below would be 'killed' by a suite that was "
              "already red.")
        print(f"   rc={rc}, red case(s): {sorted(fails)}")
        print(out[-2500:])
        return 2
    print("  ok   B0 the unmutated tool is GREEN through the temp root "
          "-- the kills below are the mutations and not the harness")
    print()

    rows = MUT
    if a.only:
        want = set(a.only.split(","))
        rows = [r for r in MUT if r[0] in want]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for res in ex.map(lambda r: one(r, base), rows):
            results.append(res)

    results.sort(key=lambda r: int(r[0][1:]))
    killed = 0
    for mid, verdict, klass, what, wants, why in results:
        if verdict == "killed":
            killed += 1
            print(f"  ok   {mid} [{klass}] {what}")
            print(f"       -> {why}")
        else:
            print(f"  {verdict} {mid} [{klass}] {what}")
            print(f"       -> expected {wants} to go red; {why}")
    print()
    alive = len(results) - killed
    print(f"{killed} of {len(results)} killed, {alive} alive")
    return 1 if alive else 0


if __name__ == "__main__":
    raise SystemExit(main())
