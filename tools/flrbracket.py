#!/usr/bin/env python3
"""flrbracket -- read the loader's `FLR` echo by machine before typing `Y`.

Why this file exists
--------------------
The `FLR` command's FIRST typed argument is the RAM DESTINATION and its second
is the flash SOURCE; the loader echoes them back in the OTHER order, as
``from <source> to <destination>``.  A card that swaps them reads plausibly in
both directions, which is why `RUNSHEET` §B3 makes *read the echo before typing
`Y`* a rule.  A human reading four echoes in a row is the weak link, so this
turns the rule into an instrument.

🔴 **The instrument it replaces had a bug on its first run, and the direction it
had been shown to work in was the safe one.**  量 2026-08-31 (seating 7):
``$FWRE_WORK/rebuild/bench-only/b5-20260831/tools/flr-window.sh`` compared the
flash source *as typed* -- six hex digits -- against the loader's echo, which is
zero-padded to eight.  `W-flr0`'s echo was correct, the checker rejected it,
sent `N`, and got `Abort!` (``bench/2026-08-31/CORRECTIONS-block3.md`` §9).
Nothing was read and nothing changed, so the failure was safe.  **Nothing has
ever shown that script would refuse a WRONG echo, which is the only reason it
exists.**  That is the gap this file closes: the classifier is a pure function
with a corpus of nine real echoes behind it and a mutation suite behind those.

What the wire actually looks like, 量 from the nine captures
------------------------------------------------------------
::

    FLR 80A00400 000000 100\\n            <- the operator's own typed line,
    \\rFlash read from 00000000 to 80A00400 with 00000100 bytes\\t?\\n
    \\r(Y)es , (N)o ? -->

    Y\\n\\rFlash Read Successed!\\n\\r<RealTek>
    N\\n\\rAbort!\\n\\r<RealTek>

Three properties of that text drive three decisions here:

* **The line endings are ``\\n\\r``**, not ``\\r\\n``, and the echoed command is
  the FIRST line -- it is the operator's own bytes coming back.  A classifier
  that searches the whole buffer can read the operator's input as the loader's
  confirmation.  That is the defect class of commit ``d008372`` (a synthetic
  interface-name literal in a scanner's own fixture classified itself), one
  tool over.  So: the echoed command is stripped before the search, and the
  echo pattern must occur **exactly once** -- zero or two is `REFUSE`, never
  "take the first one".  `tools/rlxfw-marks.py` has the same rule for the same
  reason.  ⚠️ The `<RealTek>` test runs on the WHOLE reply and not on the
  stripped body, because a hand-made ``sent`` could otherwise be made to eat a
  leading prompt; an adversarial pass built exactly that input.
* **``Flash read`` is lower-case and ``Flash Read Successed!`` is upper-case.**
  Two different strings from two different printf sites; the two classifiers do
  not share one, and the match is case-SENSITIVE for that reason.
* **The echo carries THREE fields and the shell script checked two.**  The
  length is the third typed argument and ``100`` -> ``1000`` is the same class
  of typo as the six-versus-eight digits that actually fired.  It is checked
  here.

Hex case, and what is measured about it
---------------------------------------
量: the DESTINATION field is printed upper-case -- ``80A00400``, ``80A00A00``,
``80A00B00`` all appear -- so *the loader prints upper-case hex* is a reading,
for that field.  推 for the SOURCE field: all nine sources in the corpus are
``00000000`` / ``00006000`` / ``00006400`` / ``00060000``, and **not one of them
contains a hex letter**, so no capture in this project has ever shown what case
the loader prints a source in.  The comparison is therefore on the parsed
INTEGER and is case-insensitive, which makes the untested direction unable to
bite; `N10` is the control that says so deliberately rather than by accident.

Containment: where a capture of a window may land
--------------------------------------------------
`CLAUDE.md` forbids committing bytes that identify this unit, and `H601`
(``0x006000``-``0x007FFF``) is the region that carries them.  🔴 **The line is
drawn at content, not at mention.**  An `FLR` echo capture holds addresses and
no flash bytes -- which is why ``bench/2026-08-31/W-flrh.log`` names
``00006000`` and is correctly in the repository.  The two `DW` captures of a
window hold 256 bytes each.

🔴 **And the two `DW` captures are NOT governed by the same rule, which the
first version of this file got wrong.**  The READ-BACK holds ``--src``'s window,
so guarding it on ``--src`` is right.  The PRE-READ holds whatever was last
written to ``--dst`` -- and `MEM-17` (量 2026-08-31) is that DRAM retained a
previous cycle's `FLR` output across a power cycle.  So a *non*-forbidden window
read into a RAM address that an *earlier* cycle used for `H601` has a pre-read
full of this unit's MAC, and a guard keyed on ``--src`` never looks.  That is
the 2026-08-31 incident with the roles swapped, and this file's own epigraph is
the argument against it:

> A containment rule whose correctness depends on the experiment coming out the
> expected way is not a containment rule.

So the pre-read gets its own ``--pre-dir`` and it must be **outside this
repository, always**, whatever ``--src`` is.  The forbidden table is
**imported from** ``tools/flashwin.py`` rather than copied: one owner.

What this tool does NOT prove
-----------------------------
* `verify` reads a file the caller names.  A capture crafted to contain the
  loader's own prompt and a well-formed echo of the expected addresses will
  classify `PROCEED`.  The exactly-once rules and the stripped command line
  defeat the way that happens by accident; they do not defeat a forgery, and no
  check in a file can.  What defeats it at the bench is that `run` builds the
  command itself.
* ⚠️ **A corrupted byte inside ``<RealTek>`` defeats the strongest REFUSE.**
  ``read_text`` decodes with ``errors="replace"``, so one non-UTF8 byte in the
  prompt becomes U+FFFD and the substring test misses.  Found by an adversarial
  pass, left unfixed deliberately: every repair (a fuzzy prompt match) buys a
  false REFUSE at the bench, and for the buffer to hold echo + confirm *and* a
  return to the prompt, the question must already have been answered.
* A `PROCEED` says *the loader understood the three numbers I typed*.  It says
  nothing about whether those three numbers were the right ones -- that is the
  card's job, and `check-predictions` is what reads the card.  The range checks
  below narrow that gap and do not close it.

Run:  /usr/bin/python3 tools/flrbracket.py --self-test
      /usr/bin/python3 tools/flrbracket.py verify bench/2026-08-31/W-flr0.log \\
          --src 000000 --dst 80A00400 --bytes 100
      /usr/bin/python3 tools/flrbracket.py run --port /dev/ttyUSB0 \\
          --stem W --suffix 0 --dst 80A00400 --src 000000 --bytes 100 \\
          --echo-dir bench/2026-08-31 --dw-dir bench/2026-08-31 \\
          --pre-dir $FWRE_WORK/rebuild/bench-only/b5-x   [--go]

Exit codes for `run`, and only one of them means the window was read:
      0  PROCEED, `Flash Read Successed!`, read-back taken
      3  REFUSE -- nothing was sent; the board may still be at a confirm prompt
      4  ABORT -- the echo named another transfer, `N` was sent and `Abort!` came back
      5  ABORT -- `N` was sent and the abort was NOT confirmed; needs a person
      6  PROCEED but no `Flash Read Successed!`
      2  a refusal before anything was sent (bad arguments, containment)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashwin  # noqa: E402  -- one owner for the forbidden table

TOOL_VERSION = "1.1"

# 量, from all nine captures of 2026-08-31.  Each field is EXACTLY eight hex
# digits; the `{8}` is load-bearing and not cosmetic.  `from 000000000 to ...`
# -- one digit too many -- cannot match at any offset, because after eight
# digits the pattern needs a literal " to " and finds "0 to ".  `N6`.
# 🔴 No `re.IGNORECASE`: `Flash read` is lower-case here and `Flash Read
# Successed!` is upper-case, two different printf sites, and `N17` pins it.
ECHO_RE = re.compile(
    r"Flash read from ([0-9A-Fa-f]{8}) to ([0-9A-Fa-f]{8})"
    r" with ([0-9A-Fa-f]{8}) bytes"
)
CONFIRM = "(Y)es , (N)o ?"          # 量: spaces exactly as the loader prints
PROMPT = "<RealTek>"
SUCCESS = "Flash Read Successed!"   # 量: capital R, unlike the echo above
ABORTED_MSG = "Abort!"

PROCEED, ABORT, REFUSE = "PROCEED", "ABORT", "REFUSE"
SUCCEEDED, FAILED, UNKNOWN = "SUCCEEDED", "FAILED", "UNKNOWN"
ABORTED = "ABORTED"

# Bounds, so that the swap this file exists to DETECT is also unsendable.
# 讀 `FLS-01` 4 MiB; 讀 the loader's own `ramSize: 32M` at `MEM-04`.
FLASH_SIZE = 0x400000
RAM_LO, RAM_HI = 0x80000000, 0x82000000

# The corpus.  (log path relative to the repo root, dst, src, bytes) -- the
# three numbers come from each capture's own `.meta.json` `sent` field, not
# from this table's author.  `Q2` re-derives them and refuses a drift.
CORPUS = [
    ("bench/2026-08-31/W-flr0a.log", 0x80A00400, 0x000000, 0x100),
    ("bench/2026-08-31/W-flr0.log", 0x80A00400, 0x000000, 0x100),
    ("bench/2026-08-31/W-flr6.log", 0x80A00500, 0x060000, 0x100),
    ("bench/2026-08-31/W-flrh.log", 0x80A00600, 0x006000, 0x100),
    ("bench/2026-08-31/W-flrc.log", 0x80A00700, 0x006400, 0x100),
    ("bench/2026-08-31b/X2-flr0.log", 0x80A00800, 0x000000, 0x100),
    ("bench/2026-08-31b/X2-flr6.log", 0x80A00900, 0x060000, 0x100),
    ("bench/2026-08-31b/X2-flrh.log", 0x80A00A00, 0x006000, 0x100),
    ("bench/2026-08-31b/X2-flrc.log", 0x80A00B00, 0x006400, 0x100),
]
YES_CORPUS = [
    "bench/2026-08-31/W-yes0.log", "bench/2026-08-31/W-yes6.log",
    "bench/2026-08-31/W-yesh.log", "bench/2026-08-31/W-yesc.log",
    "bench/2026-08-31b/X2-yes0.log", "bench/2026-08-31b/X2-yes6.log",
    "bench/2026-08-31b/X2-yesh.log", "bench/2026-08-31b/X2-yesc.log",
]
NO_CORPUS = ["bench/2026-08-31/W-no.log"]

# Terminators, sized on the corpus's own `.meta.json` rather than guessed, and
# `D2` asserts them against it.  ⚠️ They are sized for a 0x100-byte window; a
# larger `--bytes` needs a larger `SECS_YES`, and getting that wrong gives
# `classify_yes` -> UNKNOWN -> rc 6, which is the safe direction.
SECS_DW = 6.0
SECS_FLR = 5.0
SECS_YES = 6.0
SECS_NO = 4.0


def _fail(msg):
    print(f"flrbracket: {msg}", file=sys.stderr)
    raise SystemExit(2)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------ the core ---
def classify(reply, src, dst, nbytes, sent=None):
    """Should the operator type `Y`?  Returns (verdict, reason).

    Three outcomes and not two, because *the loader did not ask* and *the
    loader asked about something else* need different next actions: the first
    must send NOTHING (there is no question on the wire to answer), the second
    must send `N`.

    Order of the tests is itself a decision.  `<RealTek>` first, and on the
    WHOLE reply: the prompt being back means the confirm state is over --
    whatever else the buffer holds -- so an otherwise perfect echo followed by
    `<RealTek>` is `REFUSE` and not `PROCEED`.  `N3` is that case, and `N18` is
    why the test does not run on the stripped body.
    """
    if not isinstance(reply, str):
        return REFUSE, "the reply is not text"

    if PROMPT in reply:
        return REFUSE, (f"{PROMPT!r} is in the reply -- the loader is back at "
                        "its prompt, so this is not a confirm state")

    body = reply
    if sent and body.startswith(sent):
        # The first line is the operator's own bytes echoed by the loader.
        # Searching it would let a typed string classify itself.
        body = body[len(sent):]

    hits = ECHO_RE.findall(body)
    if len(hits) != 1:
        return REFUSE, (f"the echo 'Flash read from .. to .. with .. bytes' "
                        f"occurs {len(hits)} time(s), not once -- "
                        + ("the loader did not ask" if not hits else
                           "which of them is the answer is undecidable"))

    # 🔴 The confirm prompt must occur EXACTLY ONCE and AFTER the echo. The
    # first version tested only `CONFIRM in body`, and an adversarial pass
    # built two inputs that PROCEEDed through it: a confirm prompt printed
    # BEFORE the echo, and a reply carrying two of them. The exactly-once
    # argument written above for the echo applies to the question as well --
    # which of two prompts the `Y` would answer is undecidable.
    n_confirm = body.count(CONFIRM)
    if n_confirm != 1:
        return REFUSE, (f"{CONFIRM!r} occurs {n_confirm} time(s), not once -- "
                        + ("the loader printed an echo and has not asked yet"
                           if not n_confirm else
                           "which question the Y would answer is undecidable"))
    # `find`, not `index`: with the count test mutated away `index` RAISES, and
    # a crash is a red the mutation harness cannot attribute to a case. 量 --
    # `M5`'s first run came back WRONG-CASE for exactly that reason.
    if body.find(CONFIRM) < ECHO_RE.search(body).start():
        return REFUSE, (f"{CONFIRM!r} comes BEFORE the echo -- the question on "
                        "the wire is not the one this echo describes")

    got_src, got_dst, got_len = (int(h, 16) for h in hits[0])
    if got_src != src or got_dst != dst or got_len != nbytes:
        return ABORT, (
            "the loader echoed a DIFFERENT transfer: it says "
            f"from {got_src:08X} to {got_dst:08X} with {got_len:08X} bytes, "
            f"and the card asked for from {src:08X} to {dst:08X} with "
            f"{nbytes:08X} bytes")

    return PROCEED, (f"the loader echoed from {src:08X} to {dst:08X} with "
                     f"{nbytes:08X} bytes, the confirm prompt is present and "
                     f"{PROMPT} is not")


def classify_yes(reply):
    """What the reply to `Y` says.  Returns (verdict, reason).

    `UNKNOWN` is a real bench outcome and not a placeholder: a read whose
    terminator expired while the loader was still copying returns neither
    string, and reporting that as `FAILED` would invent a finding.
    """
    if not isinstance(reply, str):
        return UNKNOWN, "the reply is not text"
    if SUCCESS in reply:
        if PROMPT not in reply:
            return UNKNOWN, (f"{SUCCESS!r} is there but {PROMPT!r} is not -- "
                             "the capture ended before the loader returned to "
                             "its prompt")
        return SUCCEEDED, f"{SUCCESS!r} and the loader is back at {PROMPT!r}"
    if PROMPT in reply:
        return FAILED, (f"the loader is back at {PROMPT!r} without printing "
                        f"{SUCCESS!r} -- the read did not succeed")
    return UNKNOWN, (f"neither {SUCCESS!r} nor {PROMPT!r} -- the capture is "
                     "too short to say anything")


def classify_abort(reply):
    """What the reply to `N` says.  Returns (verdict, reason)."""
    if not isinstance(reply, str):
        return UNKNOWN, "the reply is not text"
    if ABORTED_MSG in reply and PROMPT in reply:
        return ABORTED, f"{ABORTED_MSG!r} and the loader is back at {PROMPT!r}"
    return UNKNOWN, (f"{ABORTED_MSG!r} and {PROMPT!r} are not both present -- "
                     "it is not established that the transfer was abandoned")


# ------------------------------------------------------- the containment ---
def check_ranges(src, dst, nbytes):
    """Refuse a window that cannot be what the card meant.  None, or a reason.

    🔴 `nbytes == 0` is here because of the half-open interval: for
    `at = 0x006000, nbytes = 0`, `overlaps_forbidden`'s `end > lo` is
    `0x6000 > 0x6000` -- False -- so a zero-length window on the `H601` base
    walks straight past the containment guard. 量 by an adversarial pass, on
    this tool, with `--dw-dir` inside the repository and `rc=0`. The interval
    arithmetic is right in general and is a hole for the degenerate window.
    """
    if nbytes <= 0:
        return f"--bytes 0x{nbytes:X} is not a window"
    if nbytes % 4:
        return (f"--bytes 0x{nbytes:X} is not a multiple of 4, and the "
                "read-back's `DW` word count is --bytes/4")
    if nbytes > FLASH_SIZE:
        return f"--bytes 0x{nbytes:X} is larger than the whole part"
    if src < 0 or src + nbytes > FLASH_SIZE:
        return (f"flash 0x{src:X}+0x{nbytes:X} runs past the end of a "
                f"0x{FLASH_SIZE:X}-byte part")
    if dst < RAM_LO or dst + nbytes > RAM_HI:
        return (f"RAM 0x{dst:X}+0x{nbytes:X} is outside "
                f"0x{RAM_LO:X}-0x{RAM_HI:X} (`MEM-04`, 32 MiB). "
                "🔴 A --dst that looks like a flash offset is the swap this "
                "tool exists to catch, one step earlier")
    return None


def readback_target(src, nbytes, path):
    """Where the READ-BACK may land.  It holds `src`'s window."""
    hit = flashwin.overlaps_forbidden(src, nbytes)
    if hit is None:
        return None
    lo, hi, why = hit
    if flashwin._inside_repo(path):
        return (
            f"{path} is inside {repo_root()}.\n"
            f"  The flash window 0x{src:06X}+{nbytes} overlaps "
            f"0x{lo:06X}-0x{hi - 1:06X} ({why}),\n"
            "  so the read-back of it may not be written there.\n"
            "  $FWRE_WORK/rebuild/bench-only/ is where those live.")
    return None


def preread_target(path):
    """Where the PRE-READ may land, and the answer never depends on `--src`.

    A pre-read is a `DW` of the RAM DESTINATION taken before the `FLR`, so its
    content is whatever was last written there. `MEM-17` (量 2026-08-31) is
    that DRAM retained a previous cycle's `FLR` output across a power cycle, so
    a non-forbidden window read into a RAM address an earlier cycle used for
    `H601` has a pre-read full of this unit's MAC.
    """
    if flashwin._inside_repo(path):
        return (
            f"{path} is inside {repo_root()}.\n"
            "  A PRE-READ may never be written inside this repository, "
            "whatever --src is.\n"
            "  It is a DW of the RAM destination BEFORE the FLR, so its "
            "content is decided by\n"
            "  what was last written to that address -- and `MEM-17` measured "
            "DRAM retaining a\n"
            "  previous cycle's FLR output across a power cycle. Pass "
            "--pre-dir outside the\n"
            "  repository; $FWRE_WORK/rebuild/bench-only/ is where those live.")
    return None


# -------------------------------------------------------------- verify ---
def read_text(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8", "replace")


def sent_of(log_path):
    """The `sent` string from the capture's sibling `.meta.json`, or None.

    Not an error when it is absent: a hand-made fixture has no metadata, and a
    classifier that needed one could not be tested on a synthetic reply.
    """
    meta = log_path[:-4] + ".meta.json" if log_path.endswith(".log") else None
    if not meta or not os.path.exists(meta):
        return None
    try:
        with open(meta, "r", encoding="utf-8") as f:
            return json.load(f).get("sent")
    except (ValueError, OSError):
        return None


def cmd_verify(args):
    reply = read_text(args.file)
    v, why = classify(reply, args.src, args.dst, args.bytes,
                      sent=sent_of(args.file))
    mark = {PROCEED: "🟢", ABORT: "🔴", REFUSE: "🔴"}[v]
    print(f"{mark} {v}  {args.file}")
    print(f"   {why}")
    return 0 if v == PROCEED else 1


# ----------------------------------------------------------------- run ---
def _cap_argv(port, out, send, seconds):
    return ["/usr/bin/python3", os.path.join(repo_root(), "tools",
                                             "console-capture.py"),
            "capture", "--port", port, "--out", out,
            "--send", send, "--seconds", f"{seconds:g}"]


def _shq(argv):
    return " ".join(a if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", a)
                    else "'" + a.replace("'", "'\\''") + "'" for a in argv)


def build_plan(stem, sfx, dst, src, nbytes, echo_d, dw_d, pre_d):
    """(label, out prefix, what to send, terminator) for one window.

    A function rather than a literal inside `cmd_run` so that `D2` can compare
    it against what seating 7 actually put on the wire.
    """
    return [
        ("pre-read", os.path.join(pre_d, f"{stem}-p{sfx}"),
         f"DW {dst:08X} {nbytes // 4}", SECS_DW),
        ("FLR", os.path.join(echo_d, f"{stem}-flr{sfx}"),
         f"FLR {dst:08X} {src:06X} {nbytes:X}", SECS_FLR),
        ("confirm", os.path.join(echo_d, f"{stem}-yes{sfx}"), "Y", SECS_YES),
        ("read-back", os.path.join(dw_d, f"{stem}-rd{sfx}"),
         f"DW {dst:08X} {nbytes // 4}", SECS_DW),
    ]


def cmd_run(args, capture=None):
    """Drive one window.  `capture` is injectable so the decision tree below
    has controls: an adversarial pass found four mutants of it alive because
    every case stopped at the guard or at the dry run."""
    stem, sfx = args.stem, args.suffix
    echo_d, dw_d, pre_d = args.echo_dir, args.dw_dir, args.pre_dir

    # 🔴 Everything that can refuse runs BEFORE anything is opened, created or
    # sent.  Where a guard sits was measured on `console-capture.py`
    # (2026-08-30) and the obvious placement was wrong there; here the thing
    # after it is a physical device with no spare.
    bad = check_ranges(args.src, args.dst, args.bytes)
    if bad:
        _fail(bad)
    plan = build_plan(stem, sfx, args.dst, args.src, args.bytes,
                      echo_d, dw_d, pre_d)
    bad = preread_target(plan[0][1])
    if bad:
        _fail(f"the pre-read capture may not go there.\n  {bad}")
    bad = readback_target(args.src, args.bytes, plan[3][1])
    if bad:
        _fail(f"the read-back capture may not go there.\n  {bad}")

    if not args.go:
        print(f"flrbracket {TOOL_VERSION}  DRY RUN -- no port is opened, "
              "nothing is sent.")
        print(f"  window: flash 0x{args.src:06X}+{args.bytes} "
              f"-> RAM 0x{args.dst:08X}")
        hit = flashwin.overlaps_forbidden(args.src, args.bytes)
        if hit:
            print(f"  🔴 forbidden window ({hit[2]}): the read-back goes to "
                  f"{dw_d}, which is outside the repository")
        print(f"  the pre-read always goes outside the repository: {pre_d}")
        for label, out, send, secs in plan:
            print(f"  {label:9s} {_shq(_cap_argv(args.port, out, send, secs))}")
        print(f"  on a wrong echo, instead of the confirm step: "
              f"{_shq(_cap_argv(args.port, os.path.join(echo_d, f'{stem}-no{sfx}'), 'N', SECS_NO))}")
        print("  add --go to run it.")
        return 0

    if capture is None:
        def capture(out, send, secs):
            argv = _cap_argv(args.port, out, send, secs)
            print(f"  $ {_shq(argv)}")
            r = subprocess.run(argv)
            if r.returncode != 0:
                # 🔴 A failed capture is a REFUSAL and not a warning. The
                # CP2102 dropping mid-session is this project's documented
                # recurring fault; without this the next step reads a stale
                # `.log` as this run's echo.
                _fail(f"console-capture exited {r.returncode} on the {out} "
                      "step -- stopping rather than reading a stale capture")
            return read_text(out + ".log")

    capture(plan[0][1], plan[0][2], plan[0][3])
    print(f"  pre-read written to {plan[0][1]}.log (the negative control: it "
          "must DIFFER from the expectation, or the FLR proves nothing)")

    reply = capture(plan[1][1], plan[1][2], plan[1][3])
    print(reply)
    v, why = classify(reply, args.src, args.dst, args.bytes, sent=plan[1][2])
    print(f"  {v}: {why}")

    if v == REFUSE:
        print("  🔴 sending NOTHING. The board may still be sitting at a "
              "confirm prompt;\n"
              "     the safe next action is to send a single N by hand and "
              "read what comes back.")
        return 3
    if v == ABORT:
        r = capture(os.path.join(echo_d, f"{stem}-no{sfx}"), "N", SECS_NO)
        print(r)
        av, awhy = classify_abort(r)
        print(f"  {av}: {awhy}")
        # 🔴 rc 4 and not 0. The echo was wrong, nothing was read, and there is
        # no read-back -- a card written `flrbracket run … && <next>` must not
        # continue. `M21` protects that contract for `verify`; this is the
        # subcommand that needed it.
        return 4 if av == ABORTED else 5

    r = capture(plan[2][1], plan[2][2], plan[2][3])
    print(r)
    yv, ywhy = classify_yes(r)
    print(f"  {yv}: {ywhy}")
    if yv != SUCCEEDED:
        return 6

    capture(plan[3][1], plan[3][2], plan[3][3])
    print(f"  read-back written to {plan[3][1]}.log")
    return 0


# ----------------------------------------------------------- self-test ---
def self_test():
    root = repo_root()
    ok = fail = 0

    def good(m):
        nonlocal ok
        ok += 1
        print(f"  ok   {m}")

    def bad(m):
        nonlocal fail
        fail += 1
        print(f"  FAIL {m}")

    print(f"flrbracket self-test {TOOL_VERSION}")
    print()

    # --- Q1/Q2 the population controls -----------------------------------
    # 🔴 First, because every P and N below is vacuous without them: a suite
    # whose fixture list is empty passes silently, and this repository has
    # caught that shape before ("a tool reporting 0 is making a claim").
    missing = [p for p, _, _, _ in CORPUS if not os.path.exists(
        os.path.join(root, p))]
    missing += [p for p in YES_CORPUS + NO_CORPUS
                if not os.path.exists(os.path.join(root, p))]
    if len(CORPUS) != 9 or len(YES_CORPUS) != 8 or len(NO_CORPUS) != 1:
        bad(f"Q1 the corpus is {len(CORPUS)}/{len(YES_CORPUS)}/"
            f"{len(NO_CORPUS)}, not 9/8/1 -- seating 7's captures")
    elif missing:
        bad(f"Q1 {len(missing)} corpus file(s) are not on disk: "
            f"{missing[0]} ...")
    else:
        good("Q1 the corpus is 9 echoes + 8 confirmations + 1 abort and every "
             "file is present")

    # 🔴 Q2 re-derives the three numbers of every row from the capture's OWN
    # metadata instead of trusting the table above.  The bug this tool exists
    # for was a mismatch between what was typed and what was compared; a table
    # typed by hand is the same defect one layer up.
    drift = []
    for rel, dst, src, n in CORPUS:
        s = sent_of(os.path.join(root, rel))
        m = re.fullmatch(r"FLR ([0-9A-Fa-f]+) ([0-9A-Fa-f]+) ([0-9A-Fa-f]+)",
                         s or "")
        if not m:
            drift.append(f"{rel}: sent={s!r}")
        elif (int(m.group(1), 16), int(m.group(2), 16),
              int(m.group(3), 16)) != (dst, src, n):
            drift.append(f"{rel}: table says {dst:08X}/{src:06X}/{n:X}, "
                         f"metadata says {m.group(1)}/{m.group(2)}/{m.group(3)}")
    if drift:
        bad(f"Q2 {len(drift)} row(s) disagree with their own capture's "
            f"metadata: {drift[0]}")
    else:
        good("Q2 every row's (dst, src, bytes) is re-derived from that "
             "capture's own .meta.json `sent` and agrees")

    # 🔴 Q3 pins the four WIRE CONSTANTS to the recorded bytes, and it exists
    # because an adversarial pass found that every negative case built its
    # fixture out of the constant it was testing -- so `CONFIRM = "(Y)es"`,
    # `PROMPT = "<Real"`, `SUCCESS = "Successed"` and `ABORTED_MSG = "Abort"`
    # all survived the whole suite. A loosened constant is safe in the ABORT
    # direction and is still a drift nothing could see.
    flr0 = read_text(os.path.join(root, "bench/2026-08-31/W-flr0.log"))
    nolog = read_text(os.path.join(root, NO_CORPUS[0]))
    yeslog = read_text(os.path.join(root, YES_CORPUS[0]))
    # Each row carries the constant AND a second, independently written copy of
    # what the loader prints. The first half catches a loosened constant; the
    # second half is what stops this being a copy of the code checking itself,
    # because the literal must also occur in the recorded capture.
    pinned = [
        ("CONFIRM", CONFIRM, "(Y)es , (N)o ?", flr0),
        ("PROMPT", PROMPT, "<RealTek>", nolog),
        ("SUCCESS", SUCCESS, "Flash Read Successed!", yeslog),
        ("ABORTED_MSG", ABORTED_MSG, "Abort!", nolog),
    ]
    off = []
    for name, const, literal, capture_text in pinned:
        if const != literal:
            off.append(f"{name} = {const!r}, and the loader prints "
                       f"{literal!r}")
        elif literal not in capture_text:
            off.append(f"{name}: {literal!r} does not occur in the recorded "
                       "capture, so this row is checking nothing")
    if off:
        bad(f"Q3 a wire constant does not match the recorded bytes: {off[0]}")
    else:
        good("Q3 all four wire constants are byte-exact against the recorded "
             "captures, so a loosened one is caught here and not only where "
             "it happens to change a verdict")

    # --- P1 the nine real echoes -----------------------------------------
    wrong = []
    for rel, dst, src, n in CORPUS:
        p = os.path.join(root, rel)
        v, why = classify(read_text(p), src, dst, n, sent=sent_of(p))
        if v != PROCEED:
            wrong.append(f"{rel} -> {v} ({why})")
    if wrong:
        bad(f"P1 {len(wrong)} of 9 real echoes did not PROCEED: {wrong[0]}")
    else:
        good("P1 all nine recorded FLR echoes classify PROCEED against their "
             "own three numbers")

    # --- P3/P4 the other two classifiers ---------------------------------
    wrong = [r for r in YES_CORPUS
             if classify_yes(read_text(os.path.join(root, r)))[0] != SUCCEEDED]
    if wrong:
        bad(f"P3 {len(wrong)} of 8 confirmations are not SUCCEEDED: {wrong[0]}")
    else:
        good("P3 all eight recorded replies to Y classify SUCCEEDED")

    v, why = classify_abort(read_text(os.path.join(root, NO_CORPUS[0])))
    if v != ABORTED:
        bad(f"P4 the recorded reply to N is {v}: {why}")
    else:
        good("P4 the recorded reply to N -- the abort path, exercised on real "
             "hardware by accident -- classifies ABORTED")

    # --- the negative controls -------------------------------------------
    base = read_text(os.path.join(root, "bench/2026-08-31/W-flr0.log"))
    sent0 = "FLR 80A00400 000000 100"

    def want(cid, reply, verdict, msg, src=0x000000, dst=0x80A00400,
             n=0x100, sent=sent0):
        v, why = classify(reply, src, dst, n, sent=sent)
        if v != verdict:
            bad(f"{cid} {msg} -> {v}, wanted {verdict} ({why})")
        else:
            good(f"{cid} {msg}")

    want("N1", base, ABORT, "source and destination swapped is an ABORT",
         src=0x80A00400, dst=0x000000)
    want("N2", base, ABORT, "a different flash source is an ABORT", src=0x060000)
    # 🔴 N15 is not a duplicate of N1. N1 swaps BOTH fields, so a classifier
    # comparing only the source passes it and a classifier comparing only the
    # destination passes it too. N2 moves the source alone and N15 moves the
    # destination alone; it takes both to make either partial comparison red.
    want("N15", base, ABORT, "a different RAM destination is an ABORT",
         dst=0x80A00500)

    # 🔴 Every negative fixture below writes its string out LITERALLY rather
    # than deriving it from the constant it tests. An adversarial pass found
    # that `base.replace(CONFIRM, …)` moves with the code, so four mutants that
    # LOOSENED a wire constant -- `(Y)es`, `<Real`, `Successed`, `Abort` --
    # survived every case. That is the `d008372` defect class inside the file
    # written to prevent it.
    want("N3", base + "\n\r<RealTek>", REFUSE,
         "a CORRECT echo followed by <RealTek> is a REFUSE, not a PROCEED")
    want("N4", base.replace("(Y)es , (N)o ?", "(K)es , (N)o ?"), REFUSE,
         "no '(Y)es , (N)o ?' prompt is a REFUSE")
    want("N5", "", REFUSE, "an empty reply is a REFUSE")
    want("N6", base.replace("from 00000000 to", "from 000000000 to"), REFUSE,
         "nine digits is not eight -- 'from 000000000' must not hit 00000000")
    want("N7", base, ABORT, "a length the loader did not echo is an ABORT",
         n=0x1000)
    want("N8", base + base, REFUSE,
         "two echoes in one reply is a REFUSE, not 'take the first'")
    # 🔴 N22 exists because `N8` does not isolate what it names. `base + base`
    # carries two echoes AND two confirm prompts, so the CONFIRM count refuses
    # it first and a mutant that drops the ECHO count survives -- 量, `M12`
    # lived through the 47-case suite. This one has two echoes and exactly one
    # prompt, so only the echo count can catch it.
    echo_only = base.split("(Y)es")[0]
    want("N22", echo_only + echo_only + "(Y)es , (N)o ? --> ", REFUSE,
         "two echoes and ONE confirm prompt is a REFUSE -- the case that "
         "isolates the echo count from the prompt count")

    # 🔴 N9: the operator's own typed line carrying a perfect echo. This is the
    # defect class of commit d008372 -- a literal in a fixture classifying
    # itself -- and without the `sent` strip it reads as a confirmation.
    forged = ("FLR 80A00400 000000 100 Flash read from 00000000 to 80A00400 "
              "with 00000100 bytes (Y)es , (N)o ?\n\r")
    want("N9", forged, REFUSE,
         "an echo inside the operator's own typed line is a REFUSE",
         sent=forged.rstrip("\n\r"))

    want("N10", base.replace("to 80A00400", "to 80a00400"), PROCEED,
         "lower-case hex in the echo is the SAME address -- the comparison is "
         "on the integer, because no capture has ever shown the loader's case "
         "for a source field")
    want("N17", base.replace("Flash read from", "FLASH READ FROM"), REFUSE,
         "the echo match is case-SENSITIVE -- 'Flash read' and 'Flash Read "
         "Successed!' are two different printf sites and an IGNORECASE would "
         "conflate them")

    # 🔴 N18/N19/N20 are an adversarial pass's three spurious PROCEEDs.
    want("N18", "<RealTek>" + base, REFUSE,
         "a leading <RealTek> cannot be eaten by the `sent` strip -- the "
         "prompt test runs on the WHOLE reply",
         sent="<RealTek>" + sent0)
    want("N19",
         sent0 + "\n\r(Y)es , (N)o ? --> \n\rFlash read from 00000000 to "
         "80A00400 with 00000100 bytes\t?\n\r", REFUSE,
         "a confirm prompt printed BEFORE the echo is a REFUSE")
    want("N20", base + "\n\r(Y)es , (N)o ? --> ", REFUSE,
         "two confirm prompts is a REFUSE -- which question the Y would "
         "answer is undecidable")

    # --- N11/N12/N13/N16 the other two classifiers' negatives -------------
    y = read_text(os.path.join(root, YES_CORPUS[0]))
    v, _ = classify_yes(y.replace("<RealTek>", ""))
    if v != UNKNOWN:
        bad(f"N11 'Successed' with no <RealTek> is {v}, wanted UNKNOWN")
    else:
        good("N11 'Flash Read Successed!' without <RealTek> is UNKNOWN -- the "
             "capture ended early, which is not a finding")
    v, _ = classify_yes(y.replace("Flash Read Successed!", "something else"))
    if v != FAILED:
        bad(f"N12 back at the prompt with no 'Successed' is {v}, wanted FAILED")
    else:
        good("N12 back at <RealTek> without 'Successed' is FAILED")
    nrep = read_text(os.path.join(root, NO_CORPUS[0]))
    v, _ = classify_abort(nrep.replace("Abort!", "x"))
    if v != UNKNOWN:
        bad(f"N13 a reply to N with no 'Abort!' is {v}, wanted UNKNOWN")
    else:
        good("N13 a reply to N without 'Abort!' is UNKNOWN, not ABORTED")
    # 🔴 N16 is the other half of N13, and it was missing: `classify_abort`
    # tests two strings and only one of them had a case, so a mutant that
    # dropped the `<RealTek>` term survived.
    v, _ = classify_abort(nrep.replace("<RealTek>", ""))
    if v != UNKNOWN:
        bad(f"N16 'Abort!' without a return to the prompt is {v}, "
            "wanted UNKNOWN")
    else:
        good("N16 'Abort!' without <RealTek> is UNKNOWN -- the capture ended "
             "before the loader came back, so the abort is not established")

    # 🔴 N21: the three classifiers must not crash or accept a non-string.
    # No case reached these guards at all; two mutants that deleted them lived.
    # 🔴 The exception is CAUGHT and reported as this case's failure. A guard
    # deleted makes the classifier RAISE, and an uncaught raise kills the whole
    # self-test with no case line at all -- which the mutation harness can only
    # call WRONG-CASE. 量: `M33`'s first run.
    bads = []
    for cid, f, w in (
            ("classify", lambda x: classify(x, 0, 0x80A00400, 0x100), REFUSE),
            ("classify_yes", classify_yes, UNKNOWN),
            ("classify_abort", classify_abort, UNKNOWN)):
        for val in (None, b"bytes", 17):
            try:
                got = f(val)[0]
            except Exception as e:  # noqa: BLE001 -- raising IS the failure
                bads.append(f"{cid}({val!r}) raised {type(e).__name__}")
                continue
            if got != w:
                bads.append(f"{cid}({val!r}) = {got}, wanted {w}")
    if bads:
        bad(f"N21 a non-string reply is not refused: {bads[0]}")
    else:
        good("N21 all three classifiers refuse a non-string reply rather than "
             "raising -- nine inputs across None, bytes and int")

    # --- V the range checks, which make the swap unsendable ---------------
    for cid, s_, d_, n_, must in (
            ("V1", 0x006000, 0x80A00400, 0, "not a window"),
            ("V2", 0x006000, 0x80A00400, 0x102, "multiple of 4"),
            ("V3", 0x3FFF00, 0x80A00400, 0x200, "past the end"),
            ("V4", 0x000000, 0x00006000, 0x100, "outside"),
            ("V5", 0x000000, 0x81FFFF00, 0x200, "outside")):
        r = check_ranges(s_, d_, n_)
        if r is None or must not in r:
            bad(f"{cid} check_ranges({s_:#x}, {d_:#x}, {n_:#x}) = {r!r}, "
                f"wanted a refusal naming {must!r}")
        else:
            good(f"{cid} {must}: refused before anything is sent")
    if check_ranges(0x000000, 0x80A00400, 0x100) is not None:
        bad("V6 a legitimate window was refused -- V1-V5 are a blanket")
    else:
        good("V6 a legitimate window is accepted, so V1-V5 are checks and not "
             "a blanket refusal")

    # --- G the containment guard, driven as a SUBPROCESS ------------------
    # In process it would prove the function; as a subprocess it proves the
    # command line reaches it. `flashwin`'s own pass found three leaks that a
    # function-level control could not see.
    me = os.path.abspath(__file__)
    outside = os.path.realpath(tempfile.mkdtemp(prefix="flrb-"))
    inside = os.path.join(root, "ci-out")
    try:
        os.makedirs(inside, exist_ok=True)

        def run(*a):
            return subprocess.run([sys.executable, me] + list(a),
                                  capture_output=True, text=True)

        common = ["run", "--port", "/dev/null", "--stem", "T", "--suffix", "x",
                  "--dst", "80A00400", "--bytes", "100"]

        def refused(r, saying):
            if r.returncode == 0:
                return f"rc=0, expected a refusal"
            if saying not in r.stderr:
                return f"rc={r.returncode} but stderr does not say {saying!r}"
            return None

        r = run(*(common + ["--src", "006000", "--echo-dir", inside,
                            "--dw-dir", inside, "--pre-dir", outside]))
        e = refused(r, "read-back capture may not go there")
        if e:
            bad(f"G1 an H601 read-back was allowed inside the repository: {e}")
        else:
            good("G1 an H601 window's read-back is refused inside the "
                 "repository, rc!=0, with the reason named")

        r = run(*(common + ["--src", "006400", "--echo-dir", inside,
                            "--dw-dir", inside, "--pre-dir", outside]))
        # 🔴 G2 asserts the MESSAGE and not just rc!=0. `rc != 0` alone is what
        # made the flashwin mutation pass invalid, and it cannot separate a
        # containment refusal from an argparse error.
        e = refused(r, "read-back capture may not go there")
        if e:
            bad(f"G2 the canary page 0x006400 was not treated as H601: {e}")
        else:
            good("G2 the canary page 0x006400 is inside H601 too, and the "
                 "refusal names the same reason G1's does")

        # 🔴 G3 is the control on G1/G2: a guard that refused everything would
        # pass both. A window OUTSIDE the forbidden region must be accepted.
        r = run(*(common + ["--src", "000000", "--echo-dir", inside,
                            "--dw-dir", inside, "--pre-dir", outside]))
        if r.returncode != 0:
            bad(f"G3 a NON-forbidden window was refused (rc={r.returncode}): "
                f"{r.stderr.strip()[:90]}")
        elif "DRY RUN" not in r.stdout:
            bad("G3 a non-forbidden window did not reach the dry run")
        else:
            good("G3 a non-forbidden window's read-back is accepted inside "
                 "the repository -- G1/G2 are a guard, not a blanket")

        # 🔴 G6 is the finding of an adversarial pass and it is the reason the
        # pre-read has its own directory: its content is decided by --dst, not
        # by --src, and `MEM-17` measured DRAM retaining a previous cycle's
        # FLR output. A NON-forbidden window whose --dst an earlier cycle used
        # for H601 must still refuse a pre-read inside the repository.
        # `common[:7]` is everything up to and including `--suffix x`; slicing
        # shorter silently eats an option's VALUE and argparse then refuses for
        # its own reason, which is a case that cannot see what it tests. Both
        # of the two cases below were written that way first and both went red.
        r = run(*(common[:7] + ["--dst", "80A00A00", "--bytes", "100",
                                "--src", "000000", "--echo-dir", inside,
                                "--dw-dir", inside, "--pre-dir", inside]))
        e = refused(r, "PRE-READ may never be written inside this repository")
        if e:
            bad(f"G6 a pre-read was allowed inside the repository for a "
                f"non-forbidden --src: {e}")
        else:
            good("G6 the pre-read is refused inside the repository whatever "
                 "--src is -- 0x80A00A00 is the RAM address cycle 6 used for "
                 "H601, and MEM-17 says DRAM keeps it")

        r = run(*(common + ["--src", "006000", "--echo-dir", inside,
                            "--dw-dir", outside, "--pre-dir", outside]))
        if r.returncode != 0:
            bad(f"G4 an H601 window with both DW captures OUTSIDE was "
                f"refused: {r.stderr.strip()[:90]}")
        elif "forbidden window" not in r.stdout:
            bad("G4 the dry run did not say the window is forbidden")
        else:
            good("G4 an H601 window is accepted when both DW captures go "
                 "outside -- the echo capture may stay, because it holds "
                 "addresses and no flash bytes")

        # 🔴 G7: the degenerate window. `overlaps_forbidden` is half-open, so
        # for --bytes 0 on the H601 base `end > lo` is False and the whole
        # containment guard is bypassed. 量 by an adversarial pass on this
        # tool, rc=0, with --dw-dir inside the repository.
        r = run(*(common[:7] + ["--dst", "80A00400", "--bytes", "0",
                                "--src", "006000", "--echo-dir", inside,
                                "--dw-dir", inside, "--pre-dir", inside]))
        e = refused(r, "not a window")
        if e:
            bad(f"G7 --bytes 0 walked past the containment guard: {e}")
        else:
            good("G7 --bytes 0 on the H601 base is refused as a degenerate "
                 "window, which is what the half-open interval cannot see")

        # 🔴 G5: the guard must sit above the port. `--port /dev/null` cannot
        # be opened as a serial device, so a guard placed after the capture
        # would fail for the WRONG reason and G1 could not tell the two apart.
        before = set(os.listdir(inside))
        r = run(*(common + ["--src", "006000", "--echo-dir", inside,
                            "--dw-dir", inside, "--pre-dir", outside, "--go"]))
        made = set(os.listdir(inside)) - before
        e = refused(r, "read-back capture may not go there")
        if e:
            bad(f"G5 with --go the refusal is not the containment one -- the "
                f"guard is below the port: {e}")
        elif made:
            # 🔴 This is a statement and not an `elif` on an unreachable path:
            # the first version tested `os.path.exists(inside/T-px.log)`, which
            # can only be true if the guard already failed, so it could never
            # fire. An adversarial pass named it.
            bad(f"G5 --go created {sorted(made)} before the refusal")
        else:
            good("G5 --go reaches the containment refusal before the port is "
                 "opened, and creates no file in the repository")

        # D1: the dry run opens no port and creates no file.
        r = run(*(common + ["--src", "000000", "--echo-dir", outside,
                            "--dw-dir", outside, "--pre-dir", outside]))
        made = os.listdir(outside)
        if made:
            bad(f"D1 the dry run created {made}")
        elif "console-capture.py" not in r.stdout or "--send" not in r.stdout:
            bad("D1 the dry run did not print the commands it would issue")
        else:
            good("D1 the dry run prints every console-capture command and "
                 "creates nothing")

        # 🔴 D2 is the control that matters at the bench, and it is the one a
        # tool that has never touched the hardware can still have: the plan
        # this instrument would issue for a window seating 7 ACTUALLY RAN must
        # equal what seating 7 actually put on the wire -- read out of each
        # capture's own `.meta.json`, not out of a table here.
        real = "bench/2026-08-31b"
        want_plan = build_plan("X2", "0", 0x80A00800, 0x000000, 0x100,
                               real, real, real)
        drift = []
        for label, out, send, secs in want_plan:
            meta = os.path.join(root, out + ".meta.json")
            if not os.path.exists(meta):
                drift.append(f"{label}: {out}.meta.json is not on disk")
                continue
            with open(meta, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("sent") != send:
                drift.append(f"{label}: seating 7 sent {m.get('sent')!r}, "
                             f"this plan says {send!r}")
            if float(m.get("seconds", -1)) != secs:
                drift.append(f"{label}: seating 7 used --seconds "
                             f"{m.get('seconds')}, this plan says {secs}")
        if drift:
            bad(f"D2 the plan differs from what seating 7 ran: {drift[0]}")
        else:
            good("D2 the plan for X2's 0x000000 window is byte-for-byte what "
                 "seating 7 sent -- four commands and three terminators, read "
                 "from each capture's own .meta.json")

        # --- P2/N14 the `verify` command line, end to end -----------------
        # 🔴 P2's first version called `classify` with the same five arguments
        # `P1`'s first row already passes, so it could not fail unless `P1`
        # also did -- an adversarial pass proved it a strict duplicate. Its
        # comment claimed it tested "the source given as typed, six digits",
        # which `classify` cannot express: it takes an int, and 0x000000 IS
        # 0x00000000. The six-digit spelling lives on the COMMAND LINE, which
        # is where the card writes it, so that is where the case belongs.
        r = run("verify", os.path.join(root, "bench/2026-08-31/W-flr0a.log"),
                "--src", "000000", "--dst", "80A00400", "--bytes", "100")
        if r.returncode != 0 or "PROCEED" not in r.stdout:
            bad(f"P2 `verify --src 000000` (the card's six-digit spelling) on "
                f"the echo the previous instrument aborted: rc={r.returncode} "
                f"{r.stdout.strip()[:80]}")
        else:
            good("P2 `verify` accepts the card's own SIX-digit --src on the "
                 "echo the previous instrument aborted, and exits 0 -- the "
                 "regression on 2026-08-31, at the layer the card types at")

        # 🔴 N14 drives the REAL path -- a file on disk, its sibling
        # .meta.json, `sent_of`, `classify` -- as a subprocess. Every case
        # above hands `classify` a string and an explicit `sent=`, so a
        # `sent_of` that stopped returning the typed line would leave `verify`
        # reading the operator's own text as the loader's answer and no control
        # could see it. `leakscan`'s `L17` exists for exactly this shape.
        forged_sent = ("FLR 80A00400 000000 100 Flash read from 00000000 to "
                       "80A00400 with 00000100 bytes (Y)es , (N)o ?")
        with open(os.path.join(outside, "f.log"), "w", encoding="utf-8") as f:
            f.write(forged_sent + "\n\r")
        with open(os.path.join(outside, "f.meta.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"sent": forged_sent}, f)
        r = run("verify", os.path.join(outside, "f.log"), "--src", "000000",
                "--dst", "80A00400", "--bytes", "100")
        os.remove(os.path.join(outside, "f.log"))
        os.remove(os.path.join(outside, "f.meta.json"))
        if r.returncode == 0 or "REFUSE" not in r.stdout:
            bad(f"N14 `verify` on a forged echo inside the typed line "
                f"returned rc={r.returncode}: {r.stdout.strip()[:80]}")
        else:
            good("N14 `verify` reads the typed line out of the capture's own "
                 ".meta.json and REFUSEs a forgery placed in it, rc!=0")

        # --- R the run decision tree, with the captures injected ----------
        # 🔴 Every case above stops at the guard or at the dry run, so
        # `cmd_run`'s whole post-capture tree had NO coverage and four mutants
        # of it survived. These replay seating 7's own captures through it.
        class A:
            port, stem, suffix, go = "/dev/null", "R", "z", True
            dst, src, bytes = 0x80A00400, 0x000000, 0x100
            echo_dir = dw_dir = pre_dir = outside

        def replay(texts):
            seq = list(texts)
            calls = []

            def cap(out, send, secs):
                # 🔴 Returns a sentinel rather than raising when the case runs
                # out. A raise here kills the whole self-test with no case
                # line, so a mutant that makes `cmd_run` take one capture too
                # many comes back WRONG-CASE instead of killing the case that
                # counts them. 量: `M41`'s first run.
                calls.append(send)
                return seq.pop(0) if seq else "(the case supplies no more)"
            return cap, calls

        good_flr = read_text(os.path.join(root, "bench/2026-08-31/W-flr0.log"))
        good_yes = read_text(os.path.join(root, YES_CORPUS[0]))
        good_no = read_text(os.path.join(root, NO_CORPUS[0]))
        wrong_flr = good_flr.replace("from 00000000", "from 00060000")

        for cid, texts, rc_want, ncalls, msg in (
                ("R1", ["pre", good_flr, good_yes, "rd"], 0, 4,
                 "the whole PROCEED path returns 0 and takes four captures"),
                ("R2", ["pre", wrong_flr, good_no], 4, 3,
                 "a WRONG echo returns 4, not 0 -- a card written `run && "
                 "next` must not continue"),
                ("R3", ["pre", wrong_flr, "nothing came back"], 5, 3,
                 "an abort that is not confirmed returns 5"),
                ("R4", ["pre", "garbage"], 3, 2,
                 "a REFUSE returns 3 and sends nothing after the FLR"),
                ("R5", ["pre", good_flr, "<RealTek>"], 6, 3,
                 "a Y whose reply never says 'Successed' returns 6 and takes "
                 "no read-back")):
            cap, calls = replay(texts)
            try:
                rc = cmd_run(A, capture=cap)
            except SystemExit as e:
                rc = e.code
            if rc != rc_want or len(calls) != ncalls:
                bad(f"{cid} rc={rc} after {len(calls)} capture(s), wanted "
                    f"rc={rc_want} after {ncalls}")
            else:
                good(f"{cid} {msg}")

        # 🔴 R6 drives the REAL capture path with `--go` and a port that cannot
        # be opened as a serial device. A failed capture has to be a refusal:
        # this project's documented recurring fault is the CP2102 dropping
        # mid-session, and without this the next step reads a stale `.log` as
        # this run's echo. R1-R5 inject `capture`, so none of them reaches it.
        r = run(*(common[:7] + ["--dst", "80A00400", "--bytes", "100",
                                "--src", "000000", "--echo-dir", outside,
                                "--dw-dir", outside, "--pre-dir", outside,
                                "--go"]))
        if r.returncode == 0:
            bad("R6 --go with an unopenable port returned 0")
        elif "console-capture exited" not in r.stderr:
            bad(f"R6 the refusal does not name the failed capture: "
                f"{r.stderr.strip()[:100]}")
        else:
            good("R6 a console-capture that exits non-zero stops the window "
                 "rather than reading a stale .log as this run's echo")
    finally:
        shutil.rmtree(outside, ignore_errors=True)

    print()
    print(f"{ok} ok, {fail} FAIL")
    return 1 if fail else 0


def _hexint(s):
    return int(s, 16)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    v = sub.add_parser("verify", help="classify a recorded FLR echo")
    v.add_argument("file")
    v.add_argument("--src", type=_hexint, required=True)
    v.add_argument("--dst", type=_hexint, required=True)
    v.add_argument("--bytes", type=_hexint, required=True)
    v.set_defaults(func=cmd_verify)

    r = sub.add_parser("run", help="drive one FLR window")
    r.add_argument("--port", required=True)
    r.add_argument("--stem", required=True, help="e.g. W")
    r.add_argument("--suffix", required=True, help="e.g. 0 / 6 / h / c")
    r.add_argument("--dst", type=_hexint, required=True)
    r.add_argument("--src", type=_hexint, required=True)
    r.add_argument("--bytes", type=_hexint, required=True)
    r.add_argument("--echo-dir", dest="echo_dir", required=True,
                   help="the FLR / Y / N captures -- addresses, no bytes")
    r.add_argument("--dw-dir", dest="dw_dir", required=True,
                   help="the read-back -- it holds --src's window")
    r.add_argument("--pre-dir", dest="pre_dir", required=True,
                   help="the pre-read -- ALWAYS outside this repository, "
                        "because its content is decided by --dst's history")
    r.add_argument("--go", action="store_true",
                   help="actually open the port; without it this is a dry run")
    r.set_defaults(func=cmd_run)

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
