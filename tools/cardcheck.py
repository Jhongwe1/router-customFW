#!/usr/bin/env python3
"""cardcheck -- read a bench card the way the DEVICE will, before it is powered.

Two subcommands, and they exist because a card is the one artefact in this
project that is written by hand and executed by a machine that cannot ask
questions.

    commands   every command the card types at the board, against what the
               image it uploads DECLARES (a flash write needs `owner-yes`); and
               every HOST cell, against its own tool's parser (`FW-124`)
    numbers    every number the card states, RE-DERIVED from what it names

Why `commands` exists
---------------------
🔴 量 2026-08-31 (seating 7): the card typed `wc -lc < /dev/mtd0ro` and the
device answered ``/bin/sh: wc: not found``.  `wc` **is** one of this busybox's
fifty applets -- `FW-26` is right -- and the image declares **eleven** busybox
symlinks, of which `wc` is not one.  **`FW-26` answers *what can this binary
do*; a cell needs *what can this image invoke*, and those are two different
populations that nothing in this repository compared.**  Two cells were lost at
the bench and recovered only by retyping them as `busybox wc`.

The declaration is `config/rlxfw-initramfs.tsv`, which `tools/mkinitramfs.py`
already builds the image from -- so this is a second reader of one owner, never
a second copy.

⚠️ **THE TOKENISER IS NOT A SHELL, and the gap is stated rather than left to be
discovered at the bench.** `argv0s()` splits on whitespace and understands
separators and redirections; it does **not** understand quoting, `$(...)`,
backticks, variable expansion or `sh -c '...'`.  A card that writes
`sh -c 'wc -l < x'` has its inner `wc` invisible to this tool.  **`B9` is that
precondition as a CASE rather than as this sentence**: it sweeps all 45
committed blocks and requires none of them to need quoting or substitution.
The day a card does, `B9` goes red at the desk, before the card reaches the
bench.  ⚠️ Its first run reported three offenders and all three were
`ping -c 4` and `busybox wc -c` — an option flag is not an interpreter, and
the test is on the word before the `-c`.

⚠️ **WHAT THIS CANNOT DO.** It reads a declaration, not an image.
`mkinitramfs verify` is what reads the built artefact, and `CLAUDE.md` records
why both exist: *"`check` reads the tree and `verify` reads the built artefact,
and only the second one can catch a mark that compiled and is not in the
image"*.  A card that passes here and an image that was built from a different
declaration is a hole this tool does not close.  Run `mkinitramfs verify`
against the image the card names; that is the other half.

Why `numbers` exists
--------------------
`bench/2026-08-31/PREDICTIONS-B5-block3.md` says every number on it was
re-derived from the artefacts -- **36 of 36** -- and then says the checker was a
scratchpad script with no controls, deliberately not committed.  This is that
script with controls.

🔴 **It requires the card to DECLARE its numbers**, in a fenced ```cardnum
block, one per line: `name <TAB> value <TAB> expression`.  A card without one
is REFUSED and named, never reported as `0 of 0`.  Scraping numbers out of
prose was the other design and it is worse than nothing: it would silently
check the numbers it happened to recognise and stay quiet about the rest, which
is precisely the failure mode -- an instrument that cannot fail -- that this
repository writes controls to prevent.

⚠️ **The five frozen prediction blocks have no `cardnum` fence and will not be
given one.**  They are frozen; captures have landed against them.  `numbers`
refuses on them and says why, and that refusal is the correct output.

Expressions, and every one is evaluated from a file on disk:

    size <path>                  the file's length in bytes
    lines <path>                 number of newline-terminated lines
    sha256 <path>                the full 64-hex digest
    sha256-<n> <path>            its first n hex characters (cards quote 16)
    word32 <path> <offset>       the big-endian 32-bit word at a byte offset,
                                 as eight upper-case hex digits
    zerorun-tail <path>          length of the trailing run of 0x00 bytes
    count <path> <regex>         lines of <path> matching <regex>
    dwreply <words>              bytes in the loader's reply to `DW a <words>`,
                                 through tools/reply-size.py's own model --
                                 imported, so there is ONE owner of it

Run:  /usr/bin/python3 tools/cardcheck.py --self-test
      /usr/bin/python3 tools/cardcheck.py commands bench/<d>/PREDICTIONS-*.md
      /usr/bin/python3 tools/cardcheck.py numbers   bench/<d>/PREDICTIONS-*.md

Exit codes:
    0  every command is invocable / every number re-derives
    1  at least one is not
    2  refused (no card, declaration or fence), or a tool crashed in its check
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DECL = "config/rlxfw-initramfs.tsv"

# 量, from every committed card: a cell types its command inside a `--send`
# whose argument is single-quoted.  `console-capture.py`'s `_check_send` refuses
# a newline inside it, so one --send is exactly one line on the wire.
SEND_RE = re.compile(r"--send\s+'([^']*)'")

# 讀 `docs/loader-command-semantics.md` -- the verbs the LOADER understands.
# A command whose first word is one of these is judged against the loader, not
# against the image, and this tool says nothing about it beyond that.
#
# 🔴 A HARDCODED LIST IS A FILTER THAT DROPS SILENTLY, so `B2` derives the verbs
# actually used across every committed card and asserts each one is here.  量
# 2026-08-31: the first version of this list omitted `MDIOR`, which
# `bench/2026-08-24c/PREDICTIONS-block1.md` sends, and the tool reported it as
# *not in image* -- a shell lookup on a loader command.  The control is what
# found it, on the first sweep, and it is why the list may not be edited without
# re-running that sweep.
#
# ⚠️ The authoritative table is the dispatcher's own, at `0x8040DBF8`+ inside
# `stage2.bin` -- which is a vendor binary and may not be committed, so no
# control here can read it.  `B2` checks this list against the CARDS, which is
# the population that matters for a card checker, and that limit is stated
# rather than papered over.
LOADER_VERBS = {
    "DW", "DB", "EW", "EB", "EH", "FLR", "FLW", "J", "LOADADDR",
    "PHYR", "PHYW", "MDIOR", "MDIOW", "IPCONFIG", "AUTOBURN", "HELP", "?",
}

# The two single letters a card sends are answers to `(Y)es , (N)o ? -->`, not
# commands.  Classifying them as shell words would report `Y: not in image`.
CONFIRM = {"Y", "y", "N", "n"}

# 🔴 THE `FLR` BYPASS, and it is a residual this project wrote down and then
# left a sentence guarding.
#
# `PROGRESS.md`'s *the `H601` pre-read containment is wrong in the template* row
# closed 2026-08-31 by building an enforcer -- `tools/flrbracket.py run` refuses,
# before it opens the port, to write an `H601`-overlapping read-back inside this
# repository, and a pre-read anywhere inside it for ANY window.  The same row
# states its own residual in the same breath:
#
#     "the enforcement only reaches a card that goes through `flrbracket run`.
#      A card calling `console-capture.py` directly still bypasses it --
#      RUNSHEET.md's seating-6 Deviation 2 now says the next card uses the
#      tool, and that sentence is the whole of what stands between the
#      template and a repeat."
#
# This is that sentence turned into a case.  A card that types `FLR` inside a
# `--send` is calling `console-capture.py` directly, which is precisely the
# bypass, and the incident it reproduces is real: 2026-08-31, two files inside
# this repository held this unit's MAC because a card wrote `H601` pre-reads
# under `bench/` on the assumption they would be garbage.
#
# ⚠️ Two committed cards do exactly that and BOTH ARE FROZEN -- captures have
# landed against them, so they cannot be edited and their rows are history
# rather than a plan.  They are named one by one and not excused by a date
# rule, because a date rule would also excuse a NEW card written with an old
# date, and because a list that is checked in both directions (B10) cannot
# quietly grow into a blanket.
FLR_LEGACY_CARDS = {
    # 2026-08-30, seating 6.  `V-flr0` / `V-flr6` / `V-flrh` -- the first
    # bracket, written before `flrbracket.py` existed at all.
    "bench/2026-08-30c/PREDICTIONS-B5-block2.md",
    # 2026-08-31, seating 7.  `W-flr*` plus the pre-reads whose `--out` under
    # `bench/` is the incident this check exists for.
    "bench/2026-08-31/PREDICTIONS-B5-block3.md",
}

# ⚠️ 推, NOT 量.  These are ash builtins in busybox generally; this project has
# never enumerated the builtin table of THIS binary, and `FW-26`'s applet census
# is a different population (that is the whole point of this tool).  So a word
# suppressed by this list is REPORTED with the reason rather than passed in
# silence, and `echo` -- the only one any card has used -- is also a declared
# symlink, so nothing currently rests on the list at all.
#
# 🔄 2026-09-17 (`P1-1`, `CARD-4`).  THE SIX LINES ABOVE ARE NOW FALSE AND ARE
# KEPT WORD FOR WORD, because `notes/rootfs-census.md:371` cites line 166 by
# its text and because the record of having been wrong is worth more than a
# tidy comment.  What changed:
#
#   量 2026-09-16, `tools/appletcensus.py`: this binary's builtin table HAS
#   been enumerated, statically, out of the ELF.  It is **40** names and it is
#   committed at `config/image-commands.tsv`.  The 27-name guess above has
#   zero false positives and is short by **thirteen**, of which eleven are not
#   also applets:
#
#       [[ alias bg chdir fg jobs let printf pwd readonly unalias
#
#   🔴 `printf` is the one that matters.  `awk` is genuinely absent from this
#   image (`FW-83`), so `printf` is the only formatting primitive a
#   device-side test has -- and `config/mfgtest.sh`, which `P1-1` writes,
#   types it.
#
# 🔴 AND THE LAST CLAUSE ABOVE WAS THE MISLEADING PART, not the first.
# *"nothing currently rests on the list at all"* reads as *a name on this list
# is allowed*.  It is not: landing on `ASH_BUILTINS` appends an ISSUE with
# different wording, and `cards_commands()` counts any non-absent issue as
# `bad`.  So before today a card typing `exec` FAILED, exactly as one typing
# `awk` did, and only the message differed.  Widening the set would have
# changed the message and not the verdict.
#
# So the fix is not a wider guess.  There are now THREE outcomes:
#
#   量 measured present  ->  silently allowed.  It is in this image.
#   推 guessed only      ->  allowed WITH the caveat issue, as before.
#   neither              ->  NOT IN IMAGE.
#
# `MEASURED_BUILTINS` below is the first of those, and it is read from the
# committed census rather than copied into this file -- a second copy here
# would be a second owner of a set that is already measured.
# ----------------------------------------------------------------------------
# 🔴 `--idle N` IS *N SECONDS SINCE THE LAST BYTE ON THE WIRE*, so a payload
# whose first act is a silence longer than N ends its own capture in the middle
# of that silence -- and the capture that results is not obviously broken.  量
# 2026-09-10, seating 20, before power: five cells of a FROZEN card sent
# `sleep 15`/`sleep 25` under `--idle 4`.  Each would have produced ~54 bytes
# (the command line's own echo) with the clean `stop_reason`
# `--idle 4.0 with no bytes`, and `check-predictions` scores a cell on whether a
# capture exists and postdates the card, NOT on its content -- so the seating
# would have reported `55 of 55` with the whole press ladder and both long holds
# empty.
#
# 🟢 THE FALSE-POSITIVE RATE IS MEASURED, NOT ASSUMED.  量 over every committed
# card: 60 cards, 235 capture cells, **17 carry a `sleep`**, and the only five
# that violate the rule are the five above.  Every other card in this
# repository's history separates its sleep from its idle -- the widest is
# `sleep 5` under `--idle 8` -- so this is a rule the corpus already obeyed and
# nothing had written down.
IDLE_UNDER_SLEEP_EXEMPT = {
    # 2026-09-10, seating 20.  FROZEN before the defect was found; the five
    # cells were run with `--idle` REMOVED and the deviation is recorded in
    # `bench/2026-09-10/CORRECTIONS-block17.md` § 0.  The card may not be
    # repaired -- `check-predictions` reads its mtime -- so it is excused BY
    # NAME, as `FLR_LEGACY_CARDS` excuses its two.
    "bench/2026-09-10/PREDICTIONS-B18-block17.md",
}   # and card B52's four, added below cards_numbers() on 2026-10-08: see there

_IDLE_RE = __import__("re").compile(r"--idle\s+([0-9.]+)")
_SLEEP_RE = __import__("re").compile(r"\bsleep\s+([0-9]+)")
_OUT_RE = __import__("re").compile(r"--out\s+(\S+)")


def idle_under_sleep(text):
    """-> [(cell, longest sleep, idle)] for every line with a `--send` that
    would stop before its own payload speaks -- a `CAP` line too (2026-10-08).

    A line with no `--idle`, or no `sleep` in its `--send`, is not a finding:
    `--seconds` alone is a hard duration and cannot stop early.
    """
    out = []
    for line in text.split("\n"):
        if "--send" not in line:     # CAP lines too: the 2026-10-08 note below
            continue
        mi = _IDLE_RE.search(line)
        if not mi:
            continue
        ms = SEND_RE.search(line)
        if not ms:
            continue
        sl = [int(x) for x in _SLEEP_RE.findall(ms.group(1))]
        if not sl:
            continue
        idle = float(mi.group(1))
        if max(sl) >= idle:
            mo = _OUT_RE.search(line)
            cell = mo.group(1).split("/")[-1] if mo else "?"
            out.append((cell, max(sl), idle))
    return out


ASH_BUILTINS = {
    ":", ".", "break", "cd", "continue", "eval", "exec", "exit", "export",
    "false", "hash", "local", "read", "return", "set", "shift", "source",
    "test", "times", "trap", "true", "type", "ulimit", "umask", "unset",
    "wait", "[",
}

# The MEASURED census: `tools/appletcensus.py extract` reads this unit's own
# busybox statically and writes this file.  It is the 量 half of the 推 set
# above, and it is READ rather than copied -- see the 🔄 note by line 172.
IMAGE_COMMANDS = "config/image-commands.tsv"


def measured_builtins():
    """The ash builtin names measured in this image's own busybox.

    Returns an EMPTY set if the census is missing or unparsable, and the
    caller must treat that as "fall back to the 推 list", never as "this
    image has no builtins" -- an empty set read as authoritative would make
    every builtin NOT IN IMAGE, which is the same defect this fixes with the
    sign flipped.  `A25` is the control on exactly that.
    """
    out = set()
    try:
        raw = _read(IMAGE_COMMANDS).decode("utf-8", "replace")
    except OSError:
        return out
    for line in raw.splitlines():
        if not line or line.startswith("#") or line.startswith("kind\t"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "builtin":
            out.add(parts[1])
    return out


_MEASURED = None


def _measured(img=None):
    """Cached (the corpus sweep classifies thousands of commands).  A cell
    on another image reads THAT image's table: image_table(), R8b D22."""
    global _MEASURED
    if _MEASURED is None:
        _MEASURED = frozenset(measured_builtins())
    return _MEASURED if not img or img[0] == "mainline" else image_table(img[0])[1]


# Word separators that start a NEW simple command, so the word after them is
# also an argv[0].  A card that writes `a | b` invokes two programs.
SEPARATORS = ("&&", "||", ";", "|")


def _read(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return f.read()


class Refuse(Exception):
    pass


# --------------------------------------------------------------------------
# the declaration


def load_decl(rel=DECL):
    """-> (invocable basenames, declared absolute paths).

    `slink /bin/cat busybox` makes `cat` invocable by PATH and `/bin/cat`
    invocable by path; `file /bin/busybox ...` makes both `busybox` and
    `/bin/busybox`.  `nod`/`dir` entries are paths only -- a device node is
    never an argv[0], and treating one as invocable would let a card redirect
    into something and be told the program exists.
    """
    names, paths = set(), set()
    try:
        text = _read(rel).decode("utf-8")
    except OSError as e:
        raise Refuse(f"the declaration {rel} is unreadable: {e}")
    rows = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 2:
            continue
        kind, path = f[0], f[1]
        rows += 1
        paths.add(path)
        if kind in ("slink", "file"):
            names.add(os.path.basename(path))
    if rows == 0:
        raise Refuse(f"{rel} parsed to ZERO entries -- a declaration that "
                     f"declares nothing would pass every command")
    return names, paths


# --------------------------------------------------------------------------
# commands


def argv0s(cmd):
    """Every word a shell would try to EXECUTE in `cmd`, in order.

    Redirections are dropped with their targets, and a word after a separator
    starts a new simple command.  `<` and `>` may be attached (`2>x`) or free.
    """
    out, expect_cmd = [], True
    words = cmd.split()
    i = 0
    while i < len(words):
        w = words[i]
        if w in SEPARATORS:
            expect_cmd = True
            i += 1
            continue
        if re.match(r"^\d*[<>]{1,2}$", w):          # a free redirection
            i += 2                                  # skip it AND its target
            continue
        if re.match(r"^\d*[<>]{1,2}\S", w):         # attached: >file
            i += 1
            continue
        if expect_cmd:
            out.append(w)
            expect_cmd = False
        i += 1
    return out


def redirect_targets(cmd):
    """Absolute paths a redirection reads from or writes to."""
    out = []
    for m in re.finditer(r"\d*[<>]{1,2}\s*(\S+)", cmd):
        t = m.group(1)
        if t.startswith("/"):
            out.append(t)
    return out


def classify_command(cmd, names, paths, allow_flr=False, flash_ok=frozenset(), img=None):
    """-> (kind, [issue, ...]).  kind is LOADER / CONFIRM / SHELL / EMPTY.
    `img`: None (mainline) or the cell's (image, excused) -- card_images().
    Both exemptions come per CARD, never from the command: `allow_flr`
    excuses a FROZEN card's `FLR` rows, and `flash_ok` holds the exact
    payloads that card may send although they write flash (owner_yes()).
    """
    cmd = cmd.strip()
    if not cmd:
        return "EMPTY", []
    if cmd in CONFIRM:
        return "CONFIRM", []
    first = cmd.split()[0]
    # 🔴 `FW-113` ahead of the case-sensitive test below: a flash write in ANY
    # case passes only by its exact payload.  A21: neither rule is a blanket.
    if flash_write(cmd):
        return "LOADER", ([] if cmd in flash_ok else [flash_write(cmd)])
    if first in LOADER_VERBS:
        if first == "FLR" and not allow_flr:
            return "LOADER", [
                "FLR: typed through `--send`, which calls console-capture.py "
                "directly and BYPASSES tools/flrbracket.py run -- the only "
                "thing that refuses to write a bracket's pre-read, or an "
                "H601-overlapping read-back, inside this repository. Use "
                "`flrbracket run` with --echo-dir and --dw-dir, or add this "
                "card to FLR_LEGACY_CARDS with the reason"]
        return "LOADER", []

    issues = []
    for w in argv0s(cmd):
        base = os.path.basename(w)
        if w.startswith("/"):
            if w not in paths:
                issues.append(f"{w}: no such path in the declaration")
            continue
        if base in names:
            continue
        # 量 first, 推 second.  A name measured in this image's own builtin
        # table is allowed SILENTLY -- there is nothing left to caveat.
        if base in _measured(img):
            continue
        if base in ASH_BUILTINS:
            issues.append(f"{base}: ALLOWED as an ash builtin -- 推, this "
                          f"project has never read this binary's builtin table")
            continue
        issues.append(f"{base}: NOT IN IMAGE -- not among the "
                      f"{len(names)} declared invocable names")
    for t in redirect_targets(cmd):
        # 🔴 `/proc` and `/sys` are the KERNEL's, not the initramfs's.  The
        # declaration cannot contain them and a card that redirects from
        # `/proc/uptime` is doing nothing wrong.  Found while writing M5's
        # control: without this the tool reports a defect for every procfs
        # redirection, which is a false positive on a correct card and exactly
        # the noise that gets a checker switched off.
        if t.startswith("/proc/") or t.startswith("/sys/"):
            continue
        if t not in paths:
            issues.append(f"{t}: redirection target is not declared")
    return "SHELL", issues + memnode(cmd, flash_ok) + devflash(cmd, flash_ok) + applets(cmd, img)


ABSENT_RE = re.compile(r"```cardabsent\n(.*?)\n```", re.S)
CELLID_RE = re.compile(r"^\|\s*\*\*([A-Za-z0-9_.-]+)\*\*")


def sends_with_cells(text):
    """-> [(cell-id or '?', command)] in card order."""
    out = []
    for line in text.split("\n"):
        cmds = SEND_RE.findall(line)
        if not cmds:
            continue
        m = CELLID_RE.match(line)
        cid = m.group(1) if m else "?"
        for c in cmds:
            out.append((cid, c))
    return out


def cards_commands(card_rel, decl_rel=DECL, report=print, extra_absent=()):
    try:
        text = _read(card_rel).decode("utf-8", "replace")
    except OSError as e:
        raise Refuse(f"cannot read the card {card_rel}: {e}")
    names, paths = load_decl(decl_rel)
    pairs = sends_with_cells(text)
    if not pairs:
        raise Refuse(f"{card_rel} contains no `--send '...'` at all -- either "
                     f"it is not a card or the cell format has changed, and "
                     f"reporting `0 problems` on it would be a false clean")

    # 🔴 A CELL MAY REFER TO SOMETHING THE IMAGE DOES NOT HAVE, ON PURPOSE.
    # 量 2026-08-31: `bench/2026-08-31b/PREDICTIONS-B5-block3e.md` cell `X-d2`
    # sends `busybox wc -c < /dev/mtd0` and its EXPECTED value is
    # `can't open /dev/mtd0: no such file` -- the cell exists to prove the node
    # is absent (`FW-30`).  Flagging it is a false positive of exactly the shape
    # `flashwin`'s lesson names: a rule whose correctness depends on the
    # experiment coming out the expected way.  So an absence-test is DECLARED,
    # in a ```cardabsent fence or on the command line, and is then reported as
    # an intentional absence rather than counted as a defect.
    absent = set(extra_absent)
    m = ABSENT_RE.search(text)
    if m:
        for ln in m.group(1).split("\n"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                absent.add(ln.split()[0])

    # Per CARD, not per row: a frozen card cannot be edited, so its `FLR` rows
    # are excused wholesale or not at all.  Normalised because a caller may
    # hand us either separator.
    legacy_flr = card_rel.replace("\\", "/") in FLR_LEGACY_CARDS
    flash_ok, bad = memnode_ok(text, card_rel, pairs, report, owner_yes(text, card_rel, pairs, report))
    intentional, kinds, imgs = 0, {}, card_images(text, card_rel, pairs)
    for (cid, cmd), img in zip(pairs, imgs):
        kind, issues = classify_command(cmd, names, paths, legacy_flr, flash_ok, img)
        kinds[kind] = kinds.get(kind, 0) + 1
        if not issues:
            continue
        keep = unsuppressed(kind, issues, absent)
        if not keep:
            intentional += 1
            report(f"  note  {cid}: {cmd}")
            report(f"          declared absence-test, not a defect")
            continue
        bad += 1
        report(f"  FAIL  {cid}: {cmd}")
        for it in keep:
            report(f"          {it}")
    # 🔴 The `--idle` guard.  See IDLE_UNDER_SLEEP_EXEMPT's comment: a capture
    # that stops before its own payload speaks leaves a file that passes every
    # other check in this repository.
    idle_bad = 0
    if card_rel.replace("\\", "/") not in IDLE_UNDER_SLEEP_EXEMPT:
        for cell, sl, idle in idle_under_sleep(text):
            idle_bad += 1
            report(f"  FAIL  {cell}: --idle {idle:g} <= sleep {sl} in --send")
            report(f"          the capture stops ~{idle:g} s in and the payload "
                   f"speaks at ~{sl} s; use --seconds alone, or --idle > {sl}")
    bad += idle_bad + host_cells(card_rel, text, report) + glued_sends(text, report)

    report(f"  {len(pairs)} command(s): "
           + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items()))
           + f"; declaration has {len(names)} invocable name(s)" + image_note(text, imgs)
           + (f"; {intentional} declared absence-test(s)" if intentional else ""))
    return bad


# --------------------------------------------------------------------------
# numbers

FENCE_RE = re.compile(r"```cardnum\n(.*?)\n```", re.S)


def evaluate(expr):
    """-> str.  Raises Refuse for an expression this tool cannot evaluate."""
    parts = expr.split()
    if not parts:
        raise Refuse("empty expression")
    op = parts[0]
    if op == "dwreply":
        if len(parts) != 2:
            raise Refuse(f"dwreply takes one argument: {expr}")
        # `reply-size.py` is not an importable module name, so it is loaded by
        # path -- the point being that there is still exactly ONE owner of the
        # model.  ⚠️ `predict()` returns (bytes, explanation); taking the tuple
        # whole compares a number against a 2-tuple and every row fails with a
        # message that looks like a card error.  量: it did, on the first run.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "replysize", os.path.join(ROOT, "tools/reply-size.py"))
        rs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rs)
        got = rs.predict(f"DW 80A02000 {int(parts[1])}")
        if isinstance(got, tuple):
            got = got[0]
        return str(got)
    if len(parts) < 2:
        raise Refuse(f"expression needs a path: {expr}")
    path = parts[1]
    try:
        blob = _read(path)
    except OSError as e:
        raise Refuse(f"{path}: {e}")
    if op == "size":
        return str(len(blob))
    if op == "lines":
        return str(blob.count(b"\n"))
    if op == "sha256":
        return hashlib.sha256(blob).hexdigest()
    if op.startswith("sha256-"):
        n = int(op.split("-", 1)[1])
        return hashlib.sha256(blob).hexdigest()[:n]
    if op == "zerorun-tail":
        n = 0
        while n < len(blob) and blob[len(blob) - 1 - n] == 0:
            n += 1
        return str(n)
    if op == "word32":
        off = int(parts[2], 0)
        if off + 4 > len(blob):
            raise Refuse(f"{path}: offset {off} is past the end")
        return "%08X" % int.from_bytes(blob[off:off + 4], "big")
    if op == "count":
        rx = re.compile(" ".join(parts[2:]).encode())
        return str(sum(1 for ln in blob.splitlines() if rx.search(ln)))
    raise Refuse(f"unknown expression `{op}`")


def cards_numbers(card_rel, report=print):
    try:
        text = _read(card_rel).decode("utf-8", "replace")
    except OSError as e:
        raise Refuse(f"cannot read the card {card_rel}: {e}")
    m = FENCE_RE.search(text)
    if not m:
        raise Refuse(
            f"{card_rel} has no ```cardnum fence, so there is nothing to "
            f"re-derive FROM. This is a refusal and not a pass: scraping "
            f"numbers out of prose would check the ones it recognised and "
            f"say nothing about the rest")
    rows = [ln for ln in m.group(1).split("\n")
            if ln.strip() and not ln.lstrip().startswith("#")]
    if not rows:
        raise Refuse(f"{card_rel}'s cardnum fence is empty")

    bad = 0
    for ln in rows:
        f = ln.split("\t")
        if len(f) != 3:
            report(f"  FAIL  {ln.strip()[:60]}  -- want name<TAB>value<TAB>expr")
            bad += 1
            continue
        name, want, expr = (x.strip() for x in f)
        try:
            got = evaluate(expr)
        except Refuse as e:
            report(f"  FAIL  {name}: {e}")
            bad += 1
            continue
        if got.lower() != want.lower():
            report(f"  FAIL  {name}: card says {want}, {expr} gives {got}")
            bad += 1
    report(f"  {len(rows) - bad} of {len(rows)} re-derived")
    return bad


# --------------------------------------------------------------------------
# the `--idle` guard and a card's `CAP` macro -- 2026-10-08
#
# ⚠️ This belongs beside IDLE_UNDER_SLEEP_EXEMPT and sits here, below line
# 560, for the reason the FW-113 note below gives; the three edits above that
# wire it in are line-for-line.
#
# 🔴 THE GUARD READ ONLY LINES THAT SPELL OUT `console-capture`, AND A CELL
# TYPED THROUGH A CARD'S `CAP` MACRO NEVER DOES.  A card defines `CAP` as
# `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
# (tools/cardrun.py's grammar) and writes `CAP --out <prefix> --send '...'
# --idle N ...`.  量 2026-10-08: 57 bench .md files carry such cells, and of
# the 260 corpus lines with a --send, an --idle and a sleep in the payload,
# idle_under_sleep() read 38.  The other 222 are CAP lines -- 218 at a line
# start, 3 inside a wrapper's double-quoted argument, 1 in prose backticks --
# so no CAP cell had ever been read by this guard.
#
# The fix reads the population sends_with_cells() reads -- every line SEND_RE
# finds a --send on, whatever program the line names -- which is what every
# other --send rule of `commands` reads already (FLR, FW-113, HW-1, R8b D8
# and D22, glued_sends()).  Expanding the card's macros through
# cardrun.expand() and keeping the literal test was measured too: the same
# findings on the same corpus, but cardrun refuses card B41's CAP, whose body
# is wrapped across two lines, so its seven CAP lines would have stayed out
# of reach.  量: no macro body in the corpus carries --idle or --send, so not
# expanding one hides nothing today.
#
# 量 2026-10-08, before the change, over every bench .md with a --send and
# every PREDICTIONS-*.md (123 files): 4 new findings, all on one FROZEN card
# (255af14b), and all four are this guard's own false positive.  Card B52's
# D3-UR1-Q, D3-UR2-Q, D3-UR3-Q and D3-LUR1-Q send `cd /tmp && sleep 20 &&
# busybox cp /proc/net/udp ... && sleep 12 && busybox cp ... &` under
# `--idle 3`: the trailing `&` runs the whole list, its sleeps included, in
# the background, so the shell's prompt is all the payload says.  量 each
# capture stopped `--idle 3.0 with no bytes` at 3.11-3.13 s holding 106-108
# bytes, the echo and the prompt -- what the card meant.  The guard does not
# read `&`; teaching it to is a different change and is not made here.  So
# the card is excused BY NAME; A75 pins its four cells exactly, and goes red
# the day the guard stops flagging one of them or flags a fifth; and B11
# sweeps the list both ways.
IDLE_UNDER_SLEEP_EXEMPT.add("bench/2026-09-27b/PREDICTIONS-B52-block50.md")


# --------------------------------------------------------------------------
# flash writes -- `FW-113`
#
# ⚠️ This belongs beside FLR_LEGACY_CARDS and sits here instead, because
# tracked prose cites this file's lines 27, 166, 322, 371-396, 451 and 560 by
# number, and an insertion above any of them re-points every citation below
# it (`FW-110`) -- `citecheck` is what would report it.  The edits above
# line 560 that wire this in are line-for-line.
#
# 🔴 THE RULE THIS PROJECT STATES FIRST HAD NO ENFORCER WHERE CARDS ARE
# CHECKED.  量 2026-09-23: `classify_command` returned `('LOADER', [])` for
# `FLW 0 0 0` and for `EW 8040D4A0 1` -- a known verb and no issue -- while
# the same call on `awk 1` returned NOT IN IMAGE.  What the four verbs do:
#
#   FLW       writes flash; its one guard is a `(Y)es, (N)o->` prompt, and
#             the card that types `FLW` is what answers it (`LDR-30`)
#   EW, EB    write ANY address with no bound check (`LDR-08`, `LDR-09`,
#             `LDR-11`) -- the AUTOBURN word at 0x8040D4A0 included
#   AUTOBURN  sets that word, which the upload-completion path reads to decide
#             whether to burn (`LDR-23`).  It powers up ARMED (`REG-23`), so
#             `AUTOBURN 0` is what a card types to DISARM it: that exact
#             string passes, and every other `AUTOBURN` is refused
#
# The owner's ruling of 2026-09-23 (`PROGRESS.md` `P2` settled item 9):
# `EW` and `EB` each need the owner's dated yes, with NO address allow-list.
# So there is no allow-list here, and `FLW` and a non-zero `AUTOBURN` take
# the same road (`P2-2`).  The one way through is the card's own
# ```owner-yes fence, owner_yes(); nothing else silences the refusal -- not
# a ```cardabsent line and not `--expect-absent` (unsuppressed(), `A35`).
#
# ⚠️ WHAT THIS CANNOT SEE.  It reads a single-quoted `--send '...'` (SEND_RE)
# and nothing else, so a TFTP upload made while the word is still armed, a
# `J` into code that writes flash, a `LOADADDR` aimed at the loader's own data
# (`docs/loader-command-semantics.md` § b) and a command written anywhere
# but such a `--send` all pass here.  量 2026-09-23: the committed captures'
# `.meta.json` record 15 flash-verb payloads sent (14 `EW`, 1 `EB`), and 3
# of them are in a `--send` this reads -- FLASH_LEGACY_CARDS, below.  Of the
# other 12, one sits in a card this tool checks and PASSES:
# `bench/2026-08-24c/PREDICTIONS-block3c.md`, cell `D4c`, which sent
# `EW B800311C 40000` from a table cell.  The rest were typed from
# `RUNSHEET.md`, which nothing here reads, or from cards that `commands`
# refuses outright for carrying no `--send` at all.  The upload itself is
# guarded by `looprun`'s `S5b` and nowhere else.


def flash_write(cmd):
    """-> the refusal for a payload that can write flash or arm a burn, or None.

    🔴 CASE-INSENSITIVE ON PURPOSE.  讀: the dispatcher matches the typed token
    with `0x80406C40`, which `docs/loader-command-semantics.md` § b reads as
    `strcmp` (exact), so `ew` probably reaches no handler at all -- but no
    seating has typed one, and nobody has read whether the line editor folds
    case before the compare.  Refusing a lowercase typo costs a retyped line;
    letting one through could cost the device (`A30`).
    """
    w = cmd.split()
    v = w[0].upper() if w else ""
    if v == "FLW":
        why = ("writes flash, behind a (Y)es prompt the card itself answers "
               "(LDR-30)")
    elif v in ("EW", "EB"):
        why = ("writes ANY address with no bound check (LDR-08, LDR-09, "
               "LDR-11), the AUTOBURN word at 0x8040D4A0 included")
    elif v == "AUTOBURN" and cmd.strip() != "AUTOBURN 0":
        why = ("arms the burn of the next upload into flash (LDR-23); only the "
               "exact string `AUTOBURN 0`, which disarms it, passes")
    else:
        return None
    return (f"{w[0]}: FLASH WRITE -- {why}. It needs the owner's own dated "
            f"yes on this card, as a ```owner-yes row "
            f"`YYYY-MM-DD<TAB>{cmd.strip()}`; nothing else silences it "
            f"(FW-113)")


# --------------------------------------------------------------------------
# flash writes through the DRIVER -- `FW-113` extended, R8b D8, 2026-10-05
#
# R8b's install path (rtl819x-spi.c's Gap A, CONFIG_MTD_RTL819X_WRITE images
# only) puts three verbs on /proc/rtl819x-spi that ERASE OR PROGRAM FLASH:
# `install <region> sha=<64 hex>`, `erase barrier` and `eraseprobe`.  A
# `--send` that writes one of them is a flash write exactly as `EW` is, and
# passes only by the owner's dated yes for that EXACT payload -- so the yes
# names the region, and for `install` the sha256, because both are inside the
# string it must equal (owner_yes(), unchanged in kind).
#
# What counts, per simple command, read as ash reads it (_sh_tokens()):
#   * it writes /proc/rtl819x-spi: a redirection whose operator holds `>`, or
#     a `tee` argument, whose target -- after quote removal -- names
#     `rtl819x-spi` anywhere other than as the `-img` (the staging sink, which
#     writes RAM) or `-map` file name, or carries an expansion this tool
#     cannot read (any of $ ` * ? [): `/proc//rtl819x-spi`, a relative
#     `rtl819x-spi` and `'/proc/rtl819x-spi'` are all it, and
#   * the line echo prints begins `install` or `erase` in ANY case, after
#     its leading whitespace -- the driver's dispatcher hands every line with
#     either prefix to the install parser, `eraseprobe` included -- OR its
#     content cannot be read here: a writer other than `echo`, an echo flag
#     other than -n, or an expansion in the words.  A line this tool cannot
#     read is a line that could carry the verb, and refusing it costs a
#     retyped line (flash_write()'s reasoning).
# Also refused: a program other than a reader or a printer (_SPI_QUIET)
# given the node as an ARGUMENT -- `cp /tmp/v /proc/rtl819x-spi`, `sh -c
# "..."`, `ln -s`, `dd of=` -- or a glob that could expand to it, or a $ or
# backtick in a payload that says `rtl819x` (_spi_arg()); and a payload whose
# quoting does not close.  `&` separates commands, as `;` does.
#
# 🔴 THE FIRST VERSION READ THE WORDS UNQUOTED, AND QUOTING WAS A WAY PAST IT.
# 量 2026-10-05 (the runsheet agent, on the host): `echo 'install slotA
# sha=<64> pace=10000' > /proc/rtl819x-spi` passed as a harmless write --
# its first word was `'install`, and only `"` was stripped -- and so did
# `in"stall"`, `'/proc/rtl819x-spi'` as the target, and `&` as a separator.
# Quote removal is now the shell's own rule ('...', "...", \), done once, and
# A70 holds every spelling.
#
# 量 2026-10-05, before either rule existed: the corpus (95 cards, 2,264
# --send payloads) holds 44 simple commands writing /proc/rtl819x-spi, every
# one an `echo` of literal words -- map 32, verify 5, corrupt 4, probe,
# trywrite and wedge 1 each -- and no payload carries a quote, a backslash,
# `$`, a backtick, `*`, `[` or `#` (three are `?`, the loader's help); 106
# simple commands name the node as an argument, all of them `cat`.  So
# neither the rule nor the quoting changes a committed card's verdict; B16
# sweeps that population every run.
#
# ⚠️ WHAT THIS CANNOT SEE: everything the FW-113 note above lists -- a write
# made outside a single-quoted --send, and a script ON THE DEVICE that writes
# the verb -- and a file reached by a name that does not say rtl819x-spi (a
# symlink made in an earlier, unchecked session).  And `arm` is not refused:
# it writes nothing to flash, and the yes belongs to the verb that does.
SPI_NODE = "/proc/rtl819x-spi"
_SPI_MENTION_RE = re.compile(r"rtl819x-spi(?!-(?:img|map)(?![\w.-]))")
_SPI_UNREADABLE = frozenset("$`*?[")
#: programs that do not write the files they are given: reading or printing.
_SPI_QUIET = frozenset(("cat", "head", "tail", "wc", "grep", "ls", "echo",
                        "printf"))


def _sh_tokens(cmd):
    """-> [(kind, text)]: `cmd` read the way ash reads quoting.  kind "w" is
    a word with '...', "..." and \\ removed (mixed forms joined: `in"st"'all'`
    is `install`); kind "o" is an unquoted run of ; & | < > -- a separator or
    a redirection, with an unquoted fd number glued to it (`2>&1` is `>&`,
    then the word `1`).  An unquoted `#` starting a word ends the line, as in
    the shell.  Raises ValueError for a quote that does not close or a
    trailing backslash: a line this cannot read is refused, never guessed."""
    out, word, inword, bare, i, n = [], [], False, True, 0, len(cmd)
    while i < n:
        c = cmd[i]
        if c in " \t":
            if inword:
                out.append(("w", "".join(word)))
            word, inword, bare, i = [], False, True, i + 1
            continue
        if c in ";&|<>":
            j = i
            while j < n and cmd[j] in ";&|<>":
                j += 1
            fd = inword and bare and "".join(word).isdigit() and c in "<>"
            if inword and not fd:
                out.append(("w", "".join(word)))
            out.append(("o", cmd[i:j]))
            word, inword, bare, i = [], False, True, j
            continue
        if c == "#" and not inword:
            break
        inword = True
        if c == "\\":
            if i + 1 >= n:
                raise ValueError("a trailing backslash")
            word.append(cmd[i + 1])
            bare, i = False, i + 2
        elif c == "'":
            j = cmd.find("'", i + 1)
            if j < 0:
                raise ValueError("a ' that does not close")
            word.append(cmd[i + 1:j])
            bare, i = False, j + 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and cmd[j] != '"':
                if cmd[j] == "\\" and j + 1 < n and cmd[j + 1] in '\\"$`':
                    j += 1
                buf.append(cmd[j])
                j += 1
            if j >= n:
                raise ValueError('a " that does not close')
            word.append("".join(buf))
            bare, i = False, j + 1
        else:
            word.append(c)
            i += 1
    if inword:
        out.append(("w", "".join(word)))
    return out


def _spi_hit(word):
    """A redirection target that is, or could be, the driver's node."""
    return bool(_SPI_MENTION_RE.search(word)) or any(
        ch in _SPI_UNREADABLE for ch in word)


def _spi_arg(word, named):
    """An ARGUMENT that is, or could expand to, the node: it names it, it is
    a glob, or it expands ($, `) in a payload that says `rtl819x` somewhere.
    量 2026-10-05: without that last condition `kill $!` in two committed
    RUN-arm*.md cells was refused -- a $ in a payload that never names the
    driver is not a way to it."""
    return (bool(_SPI_MENTION_RE.search(word))
            or any(ch in "*?[" for ch in word)
            or (named and any(ch in "$`" for ch in word)))


def _spi_simple(toks):
    """-> [(words, write targets)] per simple command of _sh_tokens()."""
    out, words, tgts, k = [], [], [], 0
    while k < len(toks):
        kind, v = toks[k]
        if kind == "o" and not set(v) & set("<>"):     # ; & | && || ...
            out.append((words, tgts))
            words, tgts = [], []
        elif kind == "o":                              # a redirection
            if k + 1 < len(toks) and toks[k + 1][0] == "w":
                if ">" in v:
                    tgts.append(toks[k + 1][1])
                k += 1
        else:
            words.append(v)
        k += 1
    out.append((words, tgts))
    return [(w, t + (w[1:] if w and os.path.basename(w[0]) == "tee" else []))
            for w, t in out if w or t]


def devflash(cmd, flash_ok=frozenset()):
    """-> [the refusal] when this --send writes a flash verb to the driver's
    /proc/rtl819x-spi, or may, else [] -- [] too when the card's owner-yes
    names this exact payload.  One issue per --send, beginning
    `/proc/rtl819x-spi:` and ending `(FW-113)`, which unsuppressed() never
    filters."""
    c = cmd.strip()
    if c in flash_ok:
        return []
    yes = (f"It needs the owner's own dated yes on this card, as a "
           f"```owner-yes row `YYYY-MM-DD<TAB>{c}`; nothing else silences it "
           f"(FW-113)")
    try:
        toks = _sh_tokens(c)
    except ValueError as e:
        return [f"{SPI_NODE}: this payload cannot be read as ash reads it "
                f"({e}), so it could write a flash verb. {yes}"]
    named = "rtl819x" in c
    for words, tgts in _spi_simple(toks):
        prog = os.path.basename(words[0]) if words else "?"
        if prog == "busybox" and len(words) > 1:
            prog = words[1]
        if not any(_spi_hit(t) for t in tgts if t not in ("-a",)):
            if prog not in _SPI_QUIET and any(_spi_arg(w, named) for w in words[1:]):
                return [f"{SPI_NODE}: `{prog}` is given it, or a word this "
                        f"tool cannot read, as an argument, and may write it "
                        f"-- with `install` or `erase`, which write flash. "
                        f"{yes}"]
            continue
        why = None
        if any(ch in _SPI_UNREADABLE for t in tgts for ch in t):
            why = "a target carries a character the shell expands"
        elif not words or words[0] != "echo":
            why = f"its writer is `{words[0] if words else '?'}`, not echo"
        else:
            body = words[1:]
            while body and body[0].startswith("-"):
                if body[0] != "-n":
                    why = f"echo {body[0]} rewrites what it prints"
                    break
                body = body[1:]
            if why is None and any(ch in _SPI_UNREADABLE for w in body
                                   for ch in w):
                why = "its words carry a character the shell expands"
            if why is None:
                line = " ".join(body).lstrip().lower()
                if not line.startswith(("install", "erase")):
                    continue
                return [f"{SPI_NODE}: FLASH WRITE -- `{line.split()[0]}` "
                        f"erases or programs flash through the driver's "
                        f"install path (R8b). {yes}"]
        return [f"{SPI_NODE}: a write this tool cannot read ({why}) could "
                f"carry `install` or `erase`, which write flash. {yes}"]
    return []


# A --send is read as ONE single-quoted shell word.  `--send 'a'\''b'` is
# bash's way to put a ' inside it, and SEND_RE reads `a` and stops: the
# payload checked would not be the payload sent.  So a closing quote must
# end the word -- whitespace, the end of the line, or a markdown backtick
# after it -- and the forms SEND_RE cannot see at all (`--send=`, a
# double-quoted `--send "..."`, argparse's abbreviation `--sen`) are refused
# where they stand.  量 2026-10-05: 3,036 SEND_RE matches in bench/**/*.md,
# each followed by a space (3,011), a backtick (23) or the line's end (2);
# none of the three other forms occurs.
_SEND_ODD_RE = re.compile(r"--send=|--sen\s|--send\s+\"")


def glued_sends(text, report=print):
    """-> the number of --send arguments this tool cannot read whole, each
    reported as a FAIL naming its cell."""
    bad = 0
    for line in text.split("\n"):
        m0 = CELLID_RE.match(line)
        cid = m0.group(1) if m0 else "?"
        why = [f"`{m.group(0).strip()}`: SEND_RE reads only `--send '...'`"
               for m in _SEND_ODD_RE.finditer(line)]
        for m in SEND_RE.finditer(line):
            nxt = line[m.end():m.end() + 1]
            if nxt and not nxt.isspace() and nxt != "`":
                why.append(f"`--send '{m.group(1)[:24]}'` is glued to "
                           f"`{line[m.end():m.end() + 8]}`: a ' inside the "
                           f"payload, so what is read here is not what is sent")
        for w in why:
            bad += 1
            report(f"  FAIL  {cid}: {w}")
            report("          rewrite the payload without a single quote in "
                   "it, as one `--send '...'`")
    return bad


def unsuppressed(kind, issues, absent):
    """-> the issues an absence declaration does not excuse.

    🔴 A LOADER ISSUE IS NEVER AN ABSENCE-TEST.  An absence-test is about the
    IMAGE -- a path or a program it lacks, on purpose (`B3`) -- and the filter
    keys on an issue's text up to its first colon.  量 2026-09-23, before this
    function existed: that prefix match let `--expect-absent FLR` hide
    `FLR`'s H601 containment issue (1 bad -> 0), and `--expect-absent ew`
    hide the lowercase verb's (1 -> 0); a flash-write refusal worded
    `EW: ...` would have gone the same way.  So a LOADER issue passes through
    whole, whatever is declared (`A35`).
    """
    if any(i.endswith("(HW-1)") for i in issues):   # the memory node: A55
        return list(issues)
    if any(i.startswith(SPI_NODE + ":") for i in issues):   # R8b D8: A61
        return list(issues)
    if kind == "LOADER":
        return list(issues)
    return [i for i in issues if i.split(":")[0] not in absent]


# --------------------------------------------------------------------------
# which IMAGE a cell runs on -- R8b D22, 2026-10-05
#
# Until R8b every cell here ran on one image line, whose busybox
# `config/image-commands.tsv` measures.  R8b's provisioning image is a second
# one -- the armed branch, its busybox built with CONFIG_NC and
# CONFIG_NC_SERVER, so `busybox nc -l` exists there and nowhere else -- and
# `config/image-commands-armed.tsv` measures THAT busybox, by the same tool.
# A card says which cells run on which image in one fence:
#
#     ```cardimage
#     armed<TAB>*                every --send on the card, or
#     armed<TAB>NC1 NC2          these cells: a `| **ID** |` row's id, or
#     ```                        the last `/` field of a cell's --out
#
# 🔴 THE ARMED TABLE IS REACHED ONLY THROUGH THAT FENCE.  A cell no row names,
# and every cell of a card with no fence, is checked against the mainline
# table; nothing else selects an image -- no flag, no path in the card, not
# the image's own System.map.  And the fence is read exactly: an image this
# tool does not know, a cell no --send carries, a cell named twice, `*` beside
# anything, two fences or an empty one is REFUSED, never read as `mainline`,
# because a typo that fell back silently would look like a card that meant it.
#
# What the image decides: the applet table `busybox <word>` is checked
# against (applets(), new here -- until today `busybox <anything>` passed,
# so `busybox dd` was not refused although `dd` was) and the measured
# builtins that pass silently (_measured()).  量 2026-10-05, before applets()
# existed, over every bench .md carrying a --send (100 files, 3,036
# payloads): 223 `busybox <word>` commands, 222 of them an applet the mainline
# table has.  The one that is not is card B37's `busybox telnetd`, sent
# 2026-09-21 to an image carrying the UNIT's busybox; that card is frozen and
# is excused by name, applet by applet (APPLET_LEGACY_CARDS, B17 both ways).
#
# ⚠️ WHAT THIS CANNOT SEE.  The DECLARATION is the same for every image, and
# the armed branch drops /dev/mtd0ro, mtd1ro and mtd2ro (D23): no file in this
# tree declares that image's paths, so an armed cell reading one passes here
# and fails at the board (`--decl` can name the armed branch's own
# declaration, for a whole card).  A busybox that argv0s() does not read as a
# command -- `exec busybox nc`, `sh -c '...'` -- is not checked at all, and an
# applet that exists says nothing about its options (FW-42).
import appletcensus  # noqa: E402

IMAGES = {"mainline": IMAGE_COMMANDS,
          "armed": "config/image-commands-armed.tsv"}
CARDIMAGE_RE = re.compile(r"^```cardimage\r?\n(.*?)\r?\n```", re.S | re.M)
# Every opening line, so an empty or unclosed fence -- which CARDIMAGE_RE
# cannot match -- is counted and refused rather than read as no fence.
CARDIMAGE_OPEN_RE = re.compile(r"^```cardimage[ \t]*\r?$", re.M)
APPLET_FLOOR = 20
_TABLES = {}

APPLET_LEGACY_CARDS = {
    # 2026-09-21c, `T4-LISTEN`: `busybox telnetd -p 9999`, sent to an image
    # whose busybox was the UNIT's (273,332 bytes, which has telnetd: the
    # cell's own `busybox ps` lists it running).  rlxfw's build has none, so
    # the mainline table refuses a cell that ran -- on a busybox this card
    # never met.  FROZEN: excused, and only for that applet.
    "bench/2026-09-21c/PREDICTIONS-B37-block35.md": frozenset({"telnetd"}),
}


def image_table(name):
    """-> (applets, builtins) measured for image `name`, read by the
    table's own owner, appletcensus.read_tsv().  Refused, never empty: a
    table under APPLET_FLOOR applets would make every `busybox <word>` NOT
    IN IMAGE and read as thorough (A25's argument, A68)."""
    if name not in _TABLES:
        rel = IMAGES[name]
        try:
            kinds, _meta = appletcensus.read_tsv(os.path.join(ROOT, rel))
        except appletcensus.Refuse as e:
            raise Refuse(f"the {name} image's command table: {e}")
        if len(kinds["applet"]) < APPLET_FLOOR:
            raise Refuse(f"{rel} holds {len(kinds['applet'])} applet(s), "
                         f"under {APPLET_FLOOR}: a table that parsed to "
                         f"nothing would refuse every busybox applet")
        _TABLES[name] = (frozenset(kinds["applet"]),
                         frozenset(kinds["builtin"]))
    return _TABLES[name]


def applets(cmd, img=None):
    """-> one issue per `busybox <word>` in `cmd` whose word is no applet
    measured for the cell's image; `img` as classify_command() takes it.
    Where the commands are comes from argv0s() itself, by prefix -- word k
    is a command exactly when argv0s(words[:k+1]) grows -- so there is one
    tokeniser, and the applet is the first command word after it."""
    name, excused = img or ("mainline", frozenset())
    table = image_table(name)[0]
    words, out, seen = cmd.split(), [], 0
    for k, w in enumerate(words):
        n = len(argv0s(" ".join(words[:k + 1])))
        if n == seen:
            continue
        seen = n
        if os.path.basename(w) != "busybox":
            continue
        rest = []
        for x in words[k + 1:]:
            if x in SEPARATORS:
                break
            rest.append(x)
        a = argv0s(" ".join(rest))
        if not a or a[0] in table or a[0] in excused:
            continue          # a bare `busybox` prints its usage and stops
        out.append(f"{a[0]}: NOT IN IMAGE -- `busybox {a[0]}` names no "
                   f"applet among the {len(table)} measured for the {name} "
                   f"image ({IMAGES[name]})")
    return out


def card_images(text, card_rel, pairs):
    """-> one `img` per entry of `pairs` (sends_with_cells(), card order):
    (the image the card's ```cardimage fence names for that cell, or
    `mainline`; the applets APPLET_LEGACY_CARDS excuses on this card)."""
    excused = APPLET_LEGACY_CARDS.get(card_rel.replace("\\", "/"), frozenset())
    ids = []                  # the names each --send answers to, card order
    for line in text.split("\n"):
        k = len(SEND_RE.findall(line))
        if k:
            m = CELLID_RE.match(line)
            mine = {o.strip("`'\"").rstrip("/").rsplit("/", 1)[-1]
                    for o in _OUT_RE.findall(line)}
            ids += [mine | ({m.group(1)} if m else set())] * k
    if len(ids) != len(pairs):
        raise Refuse(f"{card_rel}: the image map read {len(ids)} --send(s) "
                     f"and sends_with_cells() {len(pairs)}")
    fences = CARDIMAGE_RE.findall(text)
    opens = len(CARDIMAGE_OPEN_RE.findall(text))
    if opens != len(fences):
        raise Refuse(f"{card_rel}: {opens} ```cardimage line(s) open a fence "
                     f"and {len(fences)} parse -- an empty or unclosed fence")
    if len(fences) > 1:
        raise Refuse(f"{card_rel} has {len(fences)} ```cardimage fences; a "
                     f"cell's image is read from exactly one")
    rows = [ln.strip("\r") for ln in (fences[0].split("\n") if fences else [])
            if ln.strip() and not ln.lstrip().startswith("#")]
    if fences and not rows:
        raise Refuse(f"{card_rel}'s ```cardimage fence names no image")
    got, named = [None] * len(pairs), set()
    for ln in rows:
        image, tab, cells = ln.partition("\t")
        cells = cells.split()
        if image not in IMAGES or not tab or not cells:
            raise Refuse(f"{card_rel}: ```cardimage row {ln!r}: want "
                         f"<image><TAB><cell ...> or <image><TAB>*, the image "
                         f"one of {', '.join(sorted(IMAGES))}")
        if "*" in cells and (cells != ["*"] or len(rows) > 1):
            raise Refuse(f"{card_rel}: ```cardimage `*` names every cell, so "
                         f"it is the fence's only row and that row's only word")
        for c in cells:
            if c in named:
                raise Refuse(f"{card_rel}: ```cardimage names {c} twice")
            named.add(c)
            hit = [i for i, s in enumerate(ids) if c == "*" or c in s]
            if not hit:
                raise Refuse(f"{card_rel}: ```cardimage names cell {c}, which "
                             f"no --send on this card carries")
            for i in hit:
                if got[i] not in (None, image):
                    raise Refuse(f"{card_rel}: ```cardimage puts the --send "
                                 f"of cell {c} on two images")
                got[i] = image
    return [(g or "mainline", excused) for g in got]


def image_note(text, imgs):
    """The summary's image clause -- only on a card that has the fence, so
    every card without one reports exactly what it reported before."""
    if not CARDIMAGE_RE.search(text):
        return ""
    n = {}
    for name, _ in imgs:
        n[name] = n.get(name, 0) + 1
    return "; images: " + ", ".join(f"{v} {k}" for k, v in sorted(n.items()))


# ⚠️ Keyed by (card, exact payload) and not by card alone: a path would also
# excuse a flash write added to that file later, and these three rows are the
# whole of what the two cards sent through a `--send` before the refusal
# existed.  Both are FROZEN -- captures have landed against them -- so they
# are named one by one, never by a date or a pattern, and `B12` sweeps the
# list in both directions, as `B10` sweeps FLR_LEGACY_CARDS.
FLASH_LEGACY_CARDS = {
    # 2026-08-24c, `D4`: arms the watchdog through WDTCNR (0xB800311C) at
    # the longest OVSEL.  Its --send sits in the cell's HEADING, and the
    # tool reads that as a command, as it reads every --send.
    "bench/2026-08-24c/PREDICTIONS-block3.md": frozenset({
        "EW B800311C 240000"}),
    # 2026-08-25, `H3c-D4` and `H3c-D4c`: the same register, two OVSELs.
    "bench/2026-08-25/PREDICTIONS-b4-block10.md": frozenset({
        "EW B800311C 240000", "EW B800311C 40000"}),
}

OWNER_YES_RE = re.compile(r"```owner-yes\r?\n(.*?)\r?\n```", re.S)
_YES_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def owner_yes(text, card_rel, pairs, report=print):
    """-> (the exact payloads this card may send although they write flash,
    the number of defects found on the way).

    The way through `FW-113`'s refusal is the owner's dated yes, on the card,
    one row per payload -- the date, one TAB, the `--send` payload exactly:

        ```owner-yes
        2026-09-23<TAB>EW B800311C 240000
        ```

    🔴 THIS ENFORCES PRESENCE AND EXACTNESS, NOT PROVENANCE.  The tool cannot
    know the owner said it.  The rule is that only the owner's own words, on
    the date they were said, produce such a row; what this adds is that the
    row exists, is well formed, and names exactly what is sent.

    🔴 EXACT, WITH NO WHITESPACE NORMALISATION, and that is a decision about
    the loader, not about tidiness.  讀: its tokeniser (0x80407248) splits on
    the space character only and stores argv[i] before testing for a
    separator (`docs/loader-command-semantics.md` § f; `console-capture.py`'s
    docstring, where a leading space NULed argv[0]).  So `EW B800311C  0` --
    two spaces -- plausibly carries an EMPTY argument, which strtoul reads as
    0, and the command writes an extra word (推).  Two strings that normalise
    equal need not parse equal, and a yes for one must not pass the other.
    If the loader does collapse spaces, exactness costs a retyped row.  Case
    is exact too.

    Defects, each reported and counted, and none of them permits anything: a
    row that is not `YYYY-MM-DD<TAB>payload` with a real calendar date; a
    second row for a payload that already has one (one yes per payload); and
    a row that permits nothing on this card -- stale, mistyped, or for a
    command that needs no yes.

    One row covers every cell of THIS card that sends that exact payload, and
    each such cell is reported as a note carrying the date.
    FLASH_LEGACY_CARDS adds the frozen rows of the frozen cards, nothing else.
    """
    import datetime
    yes, bad = {}, 0
    for m in OWNER_YES_RE.finditer(text):
        for ln in m.group(1).split("\n"):
            ln = ln.rstrip("\r")
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            date, tab, payload = ln.partition("\t")
            ok = bool(tab and payload and _YES_DATE_RE.fullmatch(date))
            if ok:
                try:
                    datetime.date.fromisoformat(date)
                except ValueError:
                    ok = False
            if not ok or payload in yes:
                bad += 1
                report(f"  FAIL  owner-yes row {ln!r}")
                report("          REFUSED, and it permits nothing: " + (
                    "a second yes for one payload" if ok else
                    "want YYYY-MM-DD<TAB><the exact --send payload>, "
                    "with a real date"))
                continue
            yes[payload] = date
    legacy = FLASH_LEGACY_CARDS.get(card_rel.replace("\\", "/"), frozenset())
    used = set()
    for cid, cmd in pairs:
        c = cmd.strip()
        if not (flash_write(c) or devflash(c)) or (c not in yes and
                                                   c not in legacy):
            continue
        used.add(c)
        report(f"  note  {cid}: {cmd}")
        report(f"          a flash write under the owner's yes of {yes[c]}"
               if c in yes else
               "          a flash write on a FROZEN card (FLASH_LEGACY_CARDS),"
               " sent before FW-113; running it again needs the owner's yes")
    for payload, date in yes.items():
        if payload not in used:
            bad += 1
            report(f"  FAIL  owner-yes {date}: {payload!r}")
            report("          permits nothing on this card -- stale, "
                   "mistyped, or for a command that needs no yes")
    return frozenset(yes) | legacy, bad


# --------------------------------------------------------------------------
# the vendor's /proc/rtl865x/memory -- HW-1, 2026-09-27 (R6b-8 8c's review)
#
# 讀 drivers/net/rtl819x/rtl865x_proc_debug.c as the 8c images build it
# (CONFIG_RTL_DEBUG_TOOL=y, CONFIG_RTL_PROC_DEBUG unset): proc_mem_write()
# hands `read ADDR LEN` to memDump(ADDR, LEN) and `write ADDR DATA` to
# WRITE_MEM32(ADDR, DATA) and then a READ_MEM32 of that word, each number
# through simple_strtol with base 0, and bounds neither.  memDump prints
# LEN/16 + 1 lines of 16 bytes and LOADS five words for each line --
# (line & ~3) + 0 .. + 16 -- the last line's before its `max == 0` break,
# so `read A 4` loads A through A + 16.  And a 64-byte write passes the
# handler's `len > 64` test and NULs tmpbuf[64], one past its buffer.
#
# So one typed address puts H601's bytes in a capture under bench/
# (`read 0xBD006000 4`), consumes PSRP's read-to-clear bit, or stores
# anywhere.  rtl819x-view refuses flash and PSRP for itself; this refuses
# them for a card that reaches the same words through the vendor's node,
# as 8c-cells does by decision (D4's one write, D5's one-source reads).
#
# ONE FORM per simple command, and any other that names `memory` refused:
#     echo read 0xADDR LEN > /proc/rtl865x/memory       LEN decimal, 1-256
#     echo write 0xADDR 0xDATA > /proc/rtl865x/memory
# (`>` with or without a space after it; ADDR, DATA 1-8 hex digits).  A
# number in any other spelling -- decimal, octal, signed, trailed by a word
# -- is refused rather than read by a rule that could differ from the
# kernel's.  The longest form is 28 bytes with echo's newline, under 64.
#
# A read is permitted when its whole footprint lies in one MEMNODE_READ
# window and touches no MEMNODE_HOT word; a footprint on a flash alias is
# refused naming flashwin.overlaps_forbidden's region when it has one.  A
# write is permitted when its word lies in a MEMNODE_WRITE window, is no
# MEMNODE_HOT word, and the card declares that exact simple command in a
# ```memwrite fence, one per line; a fence row that permits nothing is a
# defect.  The three FROZEN cards that sent anything else are excused by
# (card, exact --send payload), and B15 sweeps that list both ways.  No
# absence declaration hides one of these refusals (unsuppressed(), A55).
#
# ⚠️ WHAT THIS CANNOT SEE: a send outside a single-quoted `--send` (the
# FW-113 note above says which), and what a permitted word does when it is
# loaded -- a window says where a read may land, not that it is free of side
# effects.  0xBB804600 is refused on its name alone (推).
import flashwin  # noqa: E402

MEMNODE = "/proc/rtl865x/memory"
MEMNODE_RE = re.compile(r"echo (read|write) 0x([0-9A-Fa-f]{1,8}) (\S+) ?> ?"
                        r"/proc/rtl865x/memory")
_MEMNODE_SEP_RE = re.compile(r"\s+(?:;|&&|\|\||\|)\s+")
MEMWRITE_RE = re.compile(r"```memwrite\r?\n(.*?)\r?\n```", re.S)
# The 4 MiB flash as KSEG1 and KSEG0 see it: its window and the boot alias.
FLASH_ALIASES = (0xBD000000, 0x9D000000, 0xBFC00000, 0x9FC00000)
FLASH_SIZE = 0x400000
MEMNODE_READ = (
    (0xB8000000, 0xB8000100, "the system block's first 64 words (PIN_MUX)"),
    (0xB8010000, 0xB8010100, "the CPU interface (NET-48)"),
    (0xBB801000, 0xBB802000, "the MIB"),
    (0xBB804000, 0xBB805000, "the switch registers"),
    (0xBB806000, 0xBB807000, "the 0xBB806000 block blocks 34 and 45 read"),
)
MEMNODE_WRITE = (
    (0xB8010000, 0xB8010100, "the CPU interface"),
    (0xBB804000, 0xBB805000, "the switch registers"),
)
MEMNODE_HOT = (
    (0xBB804128, 0xBB80414C, "PSRP0-PSRP8, whose bit 8 clears when read "
     "(NET-11)"),
    (0xBB804600, 0xBB804604, "0xBB804600, which B names PSRP6_RW in a "
     "branch this build does not compile (推; 8d tests it first)"),
)

# ⚠️ Keyed by (card, exact --send payload), never by a date or a pattern,
# as FLASH_LEGACY_CARDS is; all three cards are FROZEN.
MEMNODE_LEGACY_CARDS = {
    # 2026-09-17b, block 26: a read of PSRP0 whose footprint runs to PSRP4.
    "bench/2026-09-17b/PREDICTIONS-B27-block26.md": frozenset({
        "echo read 0xBB804128 4 > /proc/rtl865x/memory"}),
    # 2026-09-19, block 27: CPUICR written and restored, undeclared.
    "bench/2026-09-19/PREDICTIONS-B28-block27.md": frozenset({
        "sleep 1 ; echo write 0xB8010000 0x00100000 > /proc/rtl865x/memory",
        "sleep 1 ; echo write 0xB8010000 0x00000000 > /proc/rtl865x/memory"}),
    # 2026-09-22, block 40: a read with no LEN (讀: the handler goes to its
    # errout at the missing token) and PITCR written, undeclared.
    "bench/2026-09-22/PREDICTIONS-B42-block40.md": frozenset({
        "echo read 0xbb804100 > /proc/rtl865x/memory",
        "echo write 0xbb804100 0x00000001 > /proc/rtl865x/memory"}),
}


def memnode_span(verb, addr, arg):
    """-> the half-open [lo, hi) a well-formed send loads (a read) or stores
    and then loads (a write)."""
    if verb == "read":
        lo = addr & ~3
        return lo, lo + 16 * (int(arg) // 16) + 20
    return addr, addr + 4


def memnode_why(lo, hi, windows):
    """'' if [lo, hi) is permitted in `windows`, else why it is not."""
    for base in FLASH_ALIASES:
        if lo < base + FLASH_SIZE and hi > base:
            a, b = max(lo, base) - base, min(hi, base + FLASH_SIZE) - base
            hit = flashwin.overlaps_forbidden(a, b - a)
            return (f"flash 0x{a:06X}-0x{b - 1:06X} through its alias at "
                    f"0x{base:08X}" + (f", inside {hit[2]}" if hit else "")
                    + "; no flash word is read or written through the node")
    for h0, h1, name in MEMNODE_HOT:
        if lo < h1 and hi > h0:
            return f"it loads {name}"
    if not any(w0 <= lo and hi <= w1 for w0, w1, _ in windows):
        return "outside every window this rule admits (" + "; ".join(
            f"{w0:08X}-{w1 - 1:08X} {n}" for w0, w1, n in windows) + ")"
    return ""


def memnode(cmd, ok=frozenset()):
    """-> [issue, ...], one per simple command of `cmd` that names `memory`
    and is not permitted.  `ok` holds this card's ("memwrite", command)
    declarations and ("memlegacy", --send payload) exemptions."""
    if "memory" not in cmd or ("memlegacy", cmd.strip()) in ok:
        return []
    out = []
    for part in _MEMNODE_SEP_RE.split(cmd.strip()):
        if "memory" not in part:
            continue
        m = MEMNODE_RE.fullmatch(part)
        if not m:
            why = ("not `echo read 0xADDR LEN` or `echo write 0xADDR 0xDATA` "
                   f"into {MEMNODE}, the one form this tool bounds")
        else:
            verb, addr, arg = m.group(1), int(m.group(2), 16), m.group(3)
            if verb == "read" and not (re.fullmatch(r"[1-9][0-9]{0,2}", arg)
                                       and int(arg) <= 256):
                why = f"LEN `{arg}` is not a decimal 1-256"
            elif verb == "write" and not re.fullmatch(r"0x[0-9A-Fa-f]{1,8}",
                                                      arg):
                why = f"DATA `{arg}` is not 0x and 1-8 hex digits"
            elif verb == "write" and addr & 3:
                why = f"0x{addr:08X} is not a word address"
            else:
                lo, hi = memnode_span(verb, addr, arg)
                why = memnode_why(lo, hi, MEMNODE_READ if verb == "read"
                                  else MEMNODE_WRITE)
                if why:
                    why = f"it touches {lo:08X}-{hi - 1:08X}: {why}"
                elif verb == "write" and ("memwrite", part) not in ok:
                    why = ("a write this card does not declare: its exact "
                           "text belongs in the card's ```memwrite fence")
        if why:
            out.append(f"{MEMNODE}: `{part}`: {why} (HW-1)")
    return out


def memnode_ok(text, card_rel, pairs, report, prior):
    """-> owner_yes()'s (permitted, defects) with this card's memory-node
    permissions added: each ```memwrite row as ("memwrite", command) and each
    MEMNODE_LEGACY_CARDS payload of this card as ("memlegacy", payload).
    Defects, each reported and counted, none of them permitting anything: a
    row that is not one well-formed write, a second row for one write, and a
    row no cell of this card sends."""
    ok, bad = prior
    rows = []
    for m in MEMWRITE_RE.finditer(text):
        for ln in m.group(1).split("\n"):
            ln = ln.rstrip("\r")
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            w = MEMNODE_RE.fullmatch(ln)
            if not w or w.group(1) != "write" or ln in rows:
                bad += 1
                report(f"  FAIL  memwrite row {ln!r}")
                report("          REFUSED, and it permits nothing: " + (
                    "a second row for one write" if w and w.group(1) == "write"
                    else f"want exactly `echo write 0xADDR 0xDATA > {MEMNODE}`"))
                continue
            rows.append(ln)
    sent = {p for _cid, cmd in pairs for p in _MEMNODE_SEP_RE.split(cmd.strip())}
    for ln in rows:
        if ln not in sent:
            bad += 1
            report(f"  FAIL  memwrite {ln!r}")
            report("          permits nothing on this card -- no cell sends it")
    legacy = MEMNODE_LEGACY_CARDS.get(card_rel.replace("\\", "/"), frozenset())
    for cid, cmd in pairs:
        if cmd.strip() in legacy:
            report(f"  note  {cid}: {cmd}")
            report("          a memory-node send on a FROZEN card "
                   "(MEMNODE_LEGACY_CARDS), sent before HW-1")
    return (ok | {("memwrite", r) for r in rows}
            | {("memlegacy", p) for p in legacy}), bad


# --------------------------------------------------------------------------
# HOST cells -- `FW-124`
#
# 🔴 量 2026-09-23 (`SPEC.md` `FW-124`): twice a FROZEN card carried a HOST
# cell whose own tool rejected its arguments, and both were found at the
# bench -- block 41's `NB blast --host 10.1.1.3 --frames 347 ...`
# (`CORRECTIONS-block41.md` § 1.2) and card B44's `Z9-D2`, whose `--tsv`
# has no FILE (`CORRECTIONS-block42.md` § 1).  Until this section `commands`
# read `--send` payloads and nothing else: no HOST cell was ever read.
#
# How a HOST cell is read, and whose code reads it:
#   * the card's macros and its `HOST <prefix> :: <cmd>` lines come from
#     tools/cardrun.py -- the runner that executes cards -- loaded by path,
#     so the reading checked here is the reading run (one owner of the
#     grammar);
#   * each simple command of the expanded line comes from cardrun's shell
#     reading (quotes, operators, redirections, `VAR=`, keywords, and the
#     `timeout`/`sudo` wrappers);
#   * a project tool -- `<python> tools/NAME.py ARGS` -- is judged by that
#     tool's OWN build_parser() and refuse_args() (P2-4 § 4), in-process.
#     The parser's own `error:` line is the reason; an abbreviation argparse
#     would expand is refused (the exact-option rule: `--rate` must not
#     quietly mean `--rates`); the tool's Refused is a refusal, and any other
#     exception is a crash -- exit 2, named, never a traceback.
#
# Refused without asking a tool: an unfilled `<placeholder>`; `$`, a
# backtick or a glob in a project tool's arguments (the argv checked would
# not be the argv run); an ALL-CAPS word in first position that no
# line-start definition makes a macro; a bare tool name (`looprun`); a
# `tools/*.py` in any other form (absolute, `upstream/tools/`, behind an
# interpreter option or a wrapper this does not strip); a nested shell
# (`bash -c`, `eval`); a `bench/` script that is not in the repository; a
# shell construct the reading does not parse.
#
# ⚠️ WHAT THIS DOES NOT CHECK, and the summary line says so on every card:
# the arguments of a SYSTEM command (`ping`, `ip`, `nmap`, `iperf3` under
# `qemu-mips-static` ...).  They are counted and NAMED and never argument-
# checked, so "0 refused" cannot read as "every command was checked".  Nor
# the bench: routes, interfaces, iputils' interval floor, the address
# allowlist, an image's digest, a record that already exists -- each tool's
# environment checks, which run after refuse_args, at the bench.  Nor what a
# cell MEANS: block 41's `--rates 43` was Mbit/s where frames/s were meant,
# and it passes once spelt right.
#
# Imported here and not at the top: tracked prose cites this file's lines up
# to 560 by number (the FW-113 note above), and four lines more at the top
# would re-point every one of them.
import argparse
import collections
import contextlib
import io

# ⚠️ The twelve HOST refusals of the FROZEN cards, measured over the corpus
# by this implementation on 2026-09-24 and exactly the twelve the s107
# research predicted.  Each is named by (card, cell) AND by a fragment its
# refusal must carry, so what is exempt is the DEFECT, not the cell: the
# same cell refused for another reason is a new finding.  No date and no
# pattern; `B13` sweeps the list both ways, as B10-B12 sweep theirs.
FROZEN_HOST_CELLS = {
    # 2026-09-21f.  `NB` = `...` is written mid-paragraph (line 215), not at
    # a line start, so the runner's grammar leaves NB undefined; the cells
    # were typed by hand.  With NB supplied all seven pass netblast's own
    # parser, and B13 re-checks that.
    "bench/2026-09-21f/PREDICTIONS-B41-block39.md": {
        cell: ("`NB` is in first position",
               "NB is defined mid-paragraph (line 215), not at a line start")
        for cell in ("A1-ARP", "A2-ARP", "A3-LADDER", "A4-ARP", "A5-LONG",
                     "A6-ARP", "B2-LADDER")},
    # 2026-09-22.  A bare `looprun`, which is no command on the bench host,
    # and an unfilled `<imgwork>`; typed by hand, and no CORRECTIONS entry
    # records how.
    "bench/2026-09-22/PREDICTIONS-B42-block40.md": {
        "A0": ("`looprun` is a bare tool name",
               "a bare `looprun` and an unfilled `<imgwork>`, typed by hand")},
    # 2026-09-22b (block 41).
    "bench/2026-09-22b/PREDICTIONS-B43-block41.md": {
        "A0": ("`looprun` is a bare tool name",
               "a bare `looprun`, typed by hand"),
        "C4-DOSE": ("the following arguments are required: --target, --src, --dev",
                    "netblast has no --host, --frames or --size; ran corrected "
                    "(CORRECTIONS-block41.md § 1.2)"),
        "C8-DOSE": ("the following arguments are required: --target, --src, --dev",
                    "netblast has no --host, --frames or --size; ran corrected "
                    "(CORRECTIONS-block41.md § 1.2)")},
    # 2026-09-23 (block 42, card A).
    "bench/2026-09-23/PREDICTIONS-B44-block42.md": {
        "Z9-D2": ("argument --tsv: expected one argument",
                  "--tsv with no FILE; ran with the FILE supplied "
                  "(CORRECTIONS-block42.md § 1)")},
}

TOOL_WORD_RE = re.compile(r"(?:^|/)tools/[^/\s]+\.py$")
SHELLS = frozenset(("bash", "sh", "dash", "zsh", "ksh"))
_CARDRUN = None
_TOOL_MODS = {}


def _load_by_path(path, modname):
    """A tool, loaded by path, writing no bytecode and printing nothing.
    Anything it raises while importing is a broken tool: Refuse, named."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(modname, path)
    if spec is None or spec.loader is None:
        raise Refuse(f"{os.path.relpath(path, ROOT)} cannot be loaded as a module")
    mod = importlib.util.module_from_spec(spec)
    old, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    sys.modules[modname] = mod
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
    except KeyboardInterrupt:
        sys.modules.pop(modname, None)
        raise
    except BaseException as e:
        sys.modules.pop(modname, None)
        raise Refuse(f"{os.path.relpath(path, ROOT)} does not import "
                     f"({type(e).__name__}: {e}) -- a broken tool, not a card "
                     f"defect")
    finally:
        sys.dont_write_bytecode = old
    return mod


def _cardrun():
    """tools/cardrun.py, loaded once: the card grammar's one owner."""
    global _CARDRUN
    if _CARDRUN is None:
        _CARDRUN = _load_by_path(os.path.join(ROOT, "tools", "cardrun.py"),
                                 "cardcheck_cardrun")
    return _CARDRUN


def _parser_tree(ap):
    """The parser and every sub-parser reachable from it."""
    out, todo = [], [ap]
    while todo:
        p = todo.pop()
        if any(p is q for q in out):
            continue
        out.append(p)
        for act in getattr(p, "_actions", ()):
            if isinstance(act, argparse._SubParsersAction):
                todo.extend(act.choices.values())
    return out


def _parse(mod, path, args, exact):
    """The tool's own parser over `args` -> (namespace, None, parser), or
    (None, (exit status, what it printed), parser).  argparse names itself
    after argv[0], so that is the tool's path while the parser is built."""
    buf = io.StringIO()
    saved = sys.argv[:1]
    sys.argv[:1] = [path]
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            ap = mod.build_parser()
            if exact:
                for p in _parser_tree(ap):
                    p.allow_abbrev = False
            try:
                return ap.parse_args(args), None, ap
            except SystemExit as e:
                return None, (e.code, buf.getvalue()), ap
            except argparse.ArgumentError as e:     # a parser built with exit_on_error=False
                return None, (2, f"{ap.prog}: error: {e}"), ap
    finally:
        sys.argv[:1] = saved


def _error_line(err, rel):
    code, said = err
    if code in (0, None):
        return (f"{rel} exits at parse time with status 0 (--help or --version): "
                f"the cell would run nothing")
    lines = [ln.strip() for ln in said.splitlines() if "error:" in ln]
    return lines[-1] if lines else f"{rel}: argparse exited {code}"


def _abbreviation(ap, args, err, rel):
    opts = set()
    for p in _parser_tree(ap):
        opts.update(p._option_string_actions)
    for a in args:
        name = a.split("=", 1)[0]
        if name.startswith("--") and len(name) > 2 and name not in opts:
            cands = sorted(o for o in opts if o.startswith(name))
            if cands:
                return (f"`{name}` is an abbreviation argparse would read as "
                        f"`{cands[0]}`"
                        + (f" (or {', '.join(cands[1:])})" if cands[1:] else "")
                        + "; spell the option out -- a card names what the tool "
                        "reads (FW-124's exact-option rule)")
    return _error_line(err, rel) + " (with abbreviations refused)"


def tool_verdict(name, args, tools_dir=None):
    """-> ("accepted", "") or ("REFUSED", reason) for `tools/NAME.py ARGS`.

    The FW-124 contract, in-process: build_parser() parses, as the tool
    would; then again with every abbreviation refused; then refuse_args().
    A tool without the contract cannot be checked, so its cell is refused.
    Any exception but the tool's own Refused is a crash: Refuse, named."""
    rel = f"tools/{name}.py"
    path = os.path.join(tools_dir or os.path.join(ROOT, "tools"), name + ".py")
    if not os.path.isfile(path):
        return "REFUSED", f"{rel}: no such tool"
    mod = _TOOL_MODS.get(path)
    if mod is None:
        mod = _TOOL_MODS[path] = _load_by_path(path, f"cardcheck_tool_{len(_TOOL_MODS)}")
    R = getattr(mod, "Refused", None)
    missing = [f for f in ("build_parser", "refuse_args")
               if not callable(getattr(mod, f, None))]
    if not (isinstance(R, type) and issubclass(R, Exception)):
        missing.append("Refused")
    if missing:
        return "REFUSED", (f"{rel} does not carry the FW-124 contract (no "
                           f"{', '.join(missing)}), so its arguments cannot be "
                           f"checked and the cell is refused")
    try:
        ns, err, _ap = _parse(mod, path, args, exact=False)
        if err:
            return "REFUSED", _error_line(err, rel)
        _ns, err2, ap2 = _parse(mod, path, args, exact=True)
        if err2:
            return "REFUSED", _abbreviation(ap2, args, err2, rel)
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                mod.refuse_args(ns)
            except R as e:
                return "REFUSED", f"{rel} refuses: {e}"
    except KeyboardInterrupt:
        raise
    except BaseException as e:
        raise Refuse(f"{rel} CRASHED while checking a HOST cell's arguments -- "
                     f"{type(e).__name__}: {e}. A crash is not a verdict: the "
                     f"tool is broken, not the card")
    return "accepted", ""


def _new_census():
    return {"cells": 0, "tool": collections.Counter(), "accepted": 0,
            "tool_refused": 0, "system": collections.Counter(), "keyword": 0,
            "bench": 0, "structural": 0}


def _classify(argv, simple):
    """-> (kind, name, issues).  kind is tool, bench or system; issues are
    the refusals that need no tool."""
    cr = _cardrun()
    issues = []
    words = list(simple.words) + list(simple.assigns) + [t for _o, t in simple.redirs]
    ph = sorted({p for w in words if w.placeholder for p in cr.PLACEHOLDER_RE.findall(w.text)})
    if ph:
        issues.append("an unfilled placeholder in " + ", ".join(f"`{p}`" for p in ph)
                      + ": a card's template word, never a value")
    tool = cr.tool_of(argv)
    if tool:
        exp = [w.raw for w in tool[1] if w.expands or w.globs]
        if exp:
            issues.append(f"shell expansion in tools/{tool[0]}.py's arguments ("
                          + ", ".join(exp) + "): the argv checked here would not "
                          "be the argv run")
        return "tool", tool[0], issues
    a0 = argv[0]
    base = os.path.basename(a0.text)
    if a0.expands or a0.globs:
        issues.append(f"the program is a shell expansion (`{a0.raw}`): invisible "
                      f"to this check")
    if ((a0.text in cr.PYTHONS or base in SHELLS) and len(argv) >= 2
            and argv[1].text.startswith("bench/")):
        if not os.path.isfile(os.path.join(ROOT, argv[1].text)):
            issues.append(f"`{argv[1].text}` is not in the repository")
        return "bench", argv[1].text, issues
    if any(TOOL_WORD_RE.search(w.text) for w in argv):
        issues.append("a project tool in a form this check cannot argument-check: "
                      "write `/usr/bin/python3 tools/NAME.py ARGS` (no absolute "
                      "path, no interpreter option, no wrapper but timeout and "
                      "sudo; upstream/tools carries no contract)")
    elif (not a0.quoted and re.fullmatch(r"[a-z][a-z0-9-]*", a0.text)
          and os.path.isfile(os.path.join(ROOT, "tools", a0.text + ".py"))):
        issues.append(f"`{a0.text}` is a bare tool name: no such command on the "
                      f"bench host's PATH; write /usr/bin/python3 tools/{a0.text}.py")
    if not a0.quoted and re.fullmatch(r"[A-Z][A-Z0-9]*", a0.text):
        issues.append(f"`{a0.text}` is in first position and no line-start "
                      f"`{a0.text}` = `...` defines it: an undefined macro, which "
                      f"bash would run as a command")
    opts = []
    for w in argv[1:]:
        if not w.text.startswith("-"):
            break
        opts.append(w.text)
    if a0.text == "eval" or (base in SHELLS and any(
            re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", o) for o in opts)):
        issues.append(f"a nested shell (`{' '.join(w.text for w in argv[:2])}`): "
                      f"its commands are invisible to this check")
    return "system", base, issues


def host_command(cmd, table, census, tools_dir=None):
    """One HOST cell's command -> its refusals, [] when nothing refuses it.
    `census` counts what was checked, what was only counted, and why."""
    cr = _cardrun()
    census["cells"] += 1
    try:
        sims = cr.simple_commands(cr.expand(cmd, table))
    except cr.Refused as e:
        census["structural"] += 1
        return [str(e)]
    why = []
    for s in sims:
        argv, _wrappers, note = cr.unwrap(s)
        if note == "keyword-only":
            census["keyword"] += 1
            continue
        if note:
            census["structural"] += 1
            why.append(note)
            continue
        kind, name, issues = _classify(argv, s)
        if issues:
            census["structural"] += 1
            why.extend(issues)
            continue
        if kind == "tool":
            census["tool"][name] += 1
            verdict, reason = tool_verdict(name, [w.text for w in cr.tool_of(argv)[1]],
                                           tools_dir)
            if verdict == "accepted":
                census["accepted"] += 1
            else:
                census["tool_refused"] += 1
                why.append(reason)
        elif kind == "bench":
            census["bench"] += 1
        else:
            census["system"][name] += 1
    return why


def host_check(text, tools_dir=None):
    """-> (rows, census): rows is [(HostLine, [refusal, ...])] for every
    HOST line of a card.  cardrun's Refused propagates for a card whose
    grammar it refuses (a macro defined twice, a CR in a HOST line)."""
    cr = _cardrun()
    census = _new_census()
    lines = cr.host_lines(text)
    if not lines:
        return [], census
    table = cr.macros(text)
    return [(h, host_command(h.cmd, table, census, tools_dir)) for h in lines], census


def host_summary(c, refused, frozen):
    """The line that says, on every card, what was checked and what was not."""
    names = ", ".join(f"{k} {v}" for k, v in sorted(c["system"].items(),
                                                    key=lambda kv: (-kv[1], kv[0])))
    return (f"  HOST {c['cells']} cell(s), {refused} refused"
            + (f" ({frozen} on FROZEN_HOST_CELLS)" if frozen else "")
            + f": {sum(c['tool'].values())} project-tool command(s) checked by the "
            f"tool's own build_parser() and refuse_args() -- {c['accepted']} "
            f"accepted, {c['tool_refused']} REFUSED; {sum(c['system'].values())} "
            f"system command(s) NOT argument-checked"
            + (f": {names}" if names else "")
            + f"; {c['keyword']} keyword-only"
            + (f"; {c['bench']} bench script(s) present, not argument-checked"
               if c["bench"] else "")
            + (f"; {c['structural']} refused before any tool" if c["structural"] else ""))


def host_cells(card_rel, text, report=print, tools_dir=None):
    """-> the number of defects among a card's HOST cells, each reported.

    A refusal on FROZEN_HOST_CELLS that carries its fragment is a note, not
    a defect; one that does not carry it is a defect, named as such."""
    cr = _cardrun()
    try:
        rows, census = host_check(text, tools_dir)
    except cr.Refused as e:
        report(f"  FAIL  HOST cells: {e}")
        report("          none of this card's HOST cells is checked: "
               "tools/cardrun.py refuses its grammar")
        return 1
    if not rows:
        report("  HOST 0 cell(s): no `HOST <prefix> :: <cmd>` line in this card")
        return 0
    frozen = FROZEN_HOST_CELLS.get(card_rel.replace("\\", "/"), {})
    bad = noted = 0
    for h, why in rows:
        if not why:
            continue
        text_why = "; ".join(why)
        fz = frozen.get(h.name)
        if fz and fz[0] in text_why:
            noted += 1
            report(f"  note  {h.name}: {h.kind} :: {h.cmd}")
            report(f"          REFUSED -- {text_why}")
            report(f"          a FROZEN card's cell (FROZEN_HOST_CELLS): {fz[1]}")
            continue
        bad += 1
        report(f"  FAIL  {h.name}: {h.kind} :: {h.cmd}")
        report(f"          {text_why}")
        if fz:
            report(f"          FROZEN_HOST_CELLS exempts this cell for `{fz[0]}`, "
                   f"which this refusal does not carry: a new defect")
    report(host_summary(census, bad + noted, noted))
    return bad


# --------------------------------------------------------------------------
# controls


def run_controls():
    import tempfile
    ok = True

    def row(tag, name, good, detail):
        nonlocal ok
        ok = ok and good
        print(f"  {'ok  ' if good else 'FAIL'}  {tag} {name:<54} {detail}")

    def quiet(*a, **k):
        pass

    names, paths = load_decl()

    # A1 -- the population.  A declaration that parsed to nothing would make
    # every command below pass, so the count is asserted before anything uses
    # it.  量 2026-08-31: eleven busybox symlinks plus two uClibc ones.
    row("A1", "the declaration parses to a non-empty population",
        len(names) >= 10 and "sh" in names and "busybox" in names,
        f"{len(names)} invocable name(s), {len(paths)} declared path(s)")

    # A2 -- 🔴 THE REGRESSION.  This is the exact string seating 7 typed and the
    # exact answer the device gave.  If this ever passes, the tool has stopped
    # doing the one thing it was built for.
    k, iss = classify_command("wc -lc < /dev/mtd0ro", names, paths)
    row("A2", "`wc -lc < /dev/mtd0ro` is REFUSED (seating 7's own failure)",
        k == "SHELL" and any("wc: NOT IN IMAGE" in i for i in iss),
        f"{k}, {len(iss)} issue(s): {iss[0][:44] if iss else 'none'}")

    # A3 -- and the recovery seating 7 actually used must PASS, or the tool
    # would have refused the fix as well as the defect.
    k, iss = classify_command("busybox wc -lc < /dev/mtd0ro", names, paths)
    row("A3", "`busybox wc -lc < /dev/mtd0ro` passes", k == "SHELL" and not iss,
        f"{k}, {len(iss)} issue(s)")

    # A4..A6 -- commands the card ran successfully must not be flagged.  A tool
    # that refuses everything separates nothing.
    for tag, cmd in (("A4", "cat /proc/mtd"),
                     ("A5", "ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up"),
                     ("A6", "ping -c 4 10.1.1.2")):
        k, iss = classify_command(cmd, names, paths)
        row(tag, f"`{cmd[:38]}` passes", k == "SHELL" and not iss,
            f"{k}, {len(iss)} issue(s)")

    # A7 -- a loader command is judged as a loader command and nothing else.
    k, iss = classify_command("DW 80A02000 707", names, paths)
    row("A7", "a loader verb is classified LOADER, not looked up",
        k == "LOADER" and not iss, f"{k}")

    # A8 -- `Y` is an answer to a prompt.  Classified as a shell word it reads
    # `Y: NOT IN IMAGE`, which is a false finding on every FLR cell.
    k, _ = classify_command("Y", names, paths)
    row("A8", "`Y` is a confirmation, not a command", k == "CONFIRM", k)

    # A9 -- the redirection target is checked.  `> /dev/mtd0ro` is declared;
    # the other side of the case needs a path that is NOT declared.
    #
    # \U0001f534 THIS CONTROL WAS BROKEN ON 2026-09-07 BY A DECLARATION AND NOT BY
    # A CODE CHANGE, WHICH IS THE WHOLE REASON IT NOW DERIVES ITS EXAMPLE.
    # It hardcoded `/dev/mtd2ro` as the undeclared path, and `R5-5` declared
    # that node in config/rlxfw-initramfs.tsv -- so the control's own example
    # became declared and the case could no longer fire.  Nothing in this file
    # changed that day; the population moved underneath it.  That is exactly
    # CLAUDE.md's rule about running every suite after anything touches DATA,
    # and it is what a local sweep caught before the push.
    #
    # Hardcoding a different name would be the same bug waiting for the next
    # declaration.  The path is derived instead, and if every candidate is
    # somehow declared the case FAILS rather than passing -- a control with no
    # example left must not report ok.
    _, iss_ok = classify_command("echo x > /dev/mtd0ro", names, paths)
    undeclared = next((c for c in ("/dev/rlxfw-no-such-node",
                                   "/dev/cardcheck-a9-absent",
                                   "/dev/zzz-not-declared")
                       if c not in paths), None)
    if undeclared is None:
        row("A9", "an undeclared redirection target is caught", False,
            "every candidate is declared -- this control has no example left")
    else:
        _, iss_no = classify_command(f"echo x > {undeclared}", names, paths)
        key = os.path.basename(undeclared)
        row("A9", "an undeclared redirection target is caught",
            not iss_ok and any(key in i for i in iss_no),
            f"declared: {len(iss_ok)} issue(s); undeclared {undeclared}: "
            f"{len(iss_no)}")

    # A10 -- both sides of a pipe are argv[0]s.  A card that writes `cat x | wc`
    # invokes two programs and only one of them is in the image.
    _, iss = classify_command("cat /proc/mtd | wc -l", names, paths)
    row("A10", "the right-hand side of a pipe is checked too",
        any("wc: NOT IN IMAGE" in i for i in iss), f"{len(iss)} issue(s)")

    # A11 -- 🔴 THE WHOLE CARD, and it must come back with exactly the two cells
    # that failed at the bench.  A per-string control cannot see a parser that
    # drops rows; this reads the committed card end to end.
    card = "bench/2026-08-31/PREDICTIONS-B5-block3.md"
    try:
        bad = cards_commands(card, report=quiet)
        row("A11", "the committed block-3 card reports exactly 2 bad cells",
            bad == 2, f"{bad} bad cell(s) -- M-b and M-c, the `wc` pair")
    except Refuse as e:
        row("A11", "the committed block-3 card reports exactly 2 bad cells",
            False, str(e)[:60])

    # A12 -- a card with no --send at all is REFUSED, not reported clean.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "empty.md")
        open(p, "w").write("# a document with no cells\n")
        try:
            cards_commands(os.path.relpath(p, ROOT), report=quiet)
            row("A12", "a card with no cells is REFUSED", False, "it passed")
        except Refuse as e:
            row("A12", "a card with no cells is REFUSED", True, str(e)[:52])

    # A13 -- numbers refuses a card with no fence, and the five frozen blocks
    # are exactly that case.  Naming it is the correct output.
    try:
        cards_numbers(card, report=quiet)
        row("A13", "`numbers` refuses a card with no cardnum fence",
            False, "it reported instead of refusing")
    except Refuse as e:
        row("A13", "`numbers` refuses a card with no cardnum fence",
            "no ```cardnum fence" in str(e), str(e)[:52])

    # A14/A15 -- `numbers` on a synthetic card, both directions.  Every
    # expression is exercised against a file this control writes, so the
    # evaluator is covered rather than the format.
    with tempfile.TemporaryDirectory() as d:
        blob = b"\x12\x34\x56\x78" + b"hello\n" * 3 + b"\x00" * 5
        bp = os.path.join(d, "art.bin")
        open(bp, "wb").write(blob)
        rel = os.path.relpath(bp, ROOT).replace("\\", "/")
        sha = hashlib.sha256(blob).hexdigest()
        good = ("```cardnum\n"
                f"size\t{len(blob)}\tsize {rel}\n"
                f"lines\t3\tlines {rel}\n"
                f"digest\t{sha[:16]}\tsha256-16 {rel}\n"
                f"head\t12345678\tword32 {rel} 0\n"
                f"tail\t5\tzerorun-tail {rel}\n"
                f"hits\t3\tcount {rel} hello\n"
                f"reply\t7593\tdwreply 641\n"
                "```\n")
        p = os.path.join(d, "good.md")
        open(p, "w").write(good)
        bad = cards_numbers(os.path.relpath(p, ROOT), report=quiet)
        row("A14", "a card whose numbers are right re-derives 7 of 7",
            bad == 0, f"{bad} mismatch(es)")

        p2 = os.path.join(d, "bad.md")
        open(p2, "w").write(good.replace(f"size\t{len(blob)}\t",
                                         f"size\t{len(blob) + 1}\t"))
        bad2 = cards_numbers(os.path.relpath(p2, ROOT), report=quiet)
        row("A15", "one wrong number is caught", bad2 == 1,
            f"{bad2} mismatch(es)")

    # A16 -- the dwreply model is imported from reply-size.py, not copied.  If
    # this ever diverges, two files disagree about the same wire and one of
    # them is a card's --seconds budget.
    row("A16", "dwreply comes from reply-size.py's own model",
        evaluate("dwreply 641") == "7593" and evaluate("dwreply 707") == "8345",
        f"641 -> {evaluate('dwreply 641')}, 707 -> {evaluate('dwreply 707')}")

    # A17 -- an unknown expression REFUSES rather than silently passing.
    try:
        evaluate("nonesuch /dev/null")
        row("A17", "an unknown expression is refused", False, "it evaluated")
    except Refuse as e:
        row("A17", "an unknown expression is refused", True, str(e)[:48])

    # 🔴 B1/B2 -- THE CORPUS SWEEP.  Every per-string control above is a case I
    # chose; these two run over every committed card, which is the population
    # that can contain something I would not have thought to write.
    cards = []
    for dirpath, _, files in os.walk(os.path.join(ROOT, "bench")):
        for fn in files:
            if fn.startswith("PREDICTIONS-") and fn.endswith(".md"):
                cards.append(os.path.relpath(os.path.join(dirpath, fn), ROOT)
                             .replace("\\", "/"))
    cards.sort()
    row("B1", "the card corpus is non-empty", len(cards) >= 40,
        f"{len(cards)} committed prediction block(s)")

    # B2 -- every ALL-CAPS verb any card sends must be a KNOWN loader verb or a
    # confirmation.  量 2026-08-31: this is what found `MDIOR` missing from the
    # list, after which the tool was reporting a loader command as *not in
    # image*.  A hardcoded list is a filter that drops silently; this is the
    # thing that makes it not silent.
    unknown = set()
    for c in cards:
        try:
            t = _read(c).decode("utf-8", "replace")
        except OSError:
            continue
        for _, cmd in sends_with_cells(t):
            w = cmd.strip().split()
            if w and re.fullmatch(r"[A-Z][A-Z0-9]*", w[0]):
                if w[0] not in LOADER_VERBS and w[0] not in CONFIRM:
                    unknown.add(w[0])
    row("B2", "every ALL-CAPS verb in the corpus is a known loader verb",
        not unknown, f"unknown: {sorted(unknown)}" if unknown
        else f"{len(LOADER_VERBS)} verb(s) known, none missing")

    # B3 -- the absence-test path, both directions.  Without the second half
    # this would pass by suppressing everything.
    with tempfile.TemporaryDirectory() as d:
        body = ("| **T1** | `CAP --out x --send 'busybox wc -c < /dev/mtd0'` |\n")
        p = os.path.join(d, "a.md")
        open(p, "w").write(body)
        n_flag = cards_commands(os.path.relpath(p, ROOT), report=quiet)
        p2 = os.path.join(d, "b.md")
        open(p2, "w").write(body + "\n```cardabsent\n/dev/mtd0\n```\n")
        n_ok = cards_commands(os.path.relpath(p2, ROOT), report=quiet)
        row("B3", "a declared absence-test is not a defect, an undeclared one is",
            n_flag == 1 and n_ok == 0,
            f"undeclared {n_flag} bad, declared {n_ok} bad")

    # B4 -- and the declaration is SPECIFIC.  Declaring one path must not
    # suppress a different missing one, which is how an allowlist rots.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.md")
        open(p, "w").write(
            "| **T1** | `CAP --out x --send 'wc -c < /dev/mtd0'` |\n"
            "\n```cardabsent\n/dev/mtd0\n```\n")
        n = cards_commands(os.path.relpath(p, ROOT), report=quiet)
        row("B4", "an absence declaration suppresses only what it names",
            n == 1, f"{n} bad -- /dev/mtd0 excused, `wc` still caught")

    # B5 -- the cell id reaches the report.  A finding that does not name the
    # cell sends the reader to grep a 700-line card.
    lines = []
    cards_commands("bench/2026-08-31/PREDICTIONS-B5-block3.md",
                   report=lines.append)
    row("B5", "a finding names the cell it is in",
        any("M-b:" in x for x in lines) and any("M-c:" in x for x in lines),
        f"{sum(1 for x in lines if x.startswith('  FAIL'))} FAIL line(s), "
        f"cell ids present")

    # B6 -- 🔴 A REDIRECTION TARGET IS NOT A COMMAND, and no control could see
    # the difference until this one.  Written because M5 SURVIVED: skipping one
    # word instead of two after a free `<` leaves the TARGET as the next
    # argv[0], and in every command the cards actually contain the target sits
    # after a command that has already consumed `expect_cmd`, so the two
    # behaviours agree.  A redirection that STARTS a simple command is where
    # they part.  `/proc` is exempt as a target and never as an argv[0], which
    # is what makes the two readings different here.
    # ⚠️ THE REDIRECTION MUST LEAD.  `busybox wc -c < /proc/uptime` does NOT
    # separate the two behaviours -- `expect_cmd` is already False by the time
    # the `<` is reached, so the target is skipped either way.  量: that was
    # this control's first input and M5 survived it.  A redirection that starts
    # a simple command is the only place the one-word and two-word skips differ.
    k, iss_ok = classify_command("< /proc/uptime busybox wc -c", names, paths)
    row("B6", "a leading redirection target is not read as a command",
        k == "SHELL" and not iss_ok,
        f"{len(iss_ok)} issue(s) -- /proc is the kernel's, not the image's")

    # B7 -- a device node is not invocable.  M10 (`nod` folded into the
    # invocable set) survived every control above, because no card has ever
    # tried to EXECUTE a node -- which is exactly why a mutation suite is not
    # the same thing as a corpus.
    k, iss = classify_command("mtd0ro", names, paths)
    row("B7", "a declared device node is not an invocable name",
        k == "SHELL" and any("NOT IN IMAGE" in i for i in iss),
        f"{len(iss)} issue(s) for `mtd0ro`")

    # B8 -- and the node is still checkable as a PATH.  B7 must not be
    # satisfied by dropping `nod` rows from the declaration entirely.
    _, iss = classify_command("echo x > /dev/mtd0ro", names, paths)
    row("B8", "and it is still a valid redirection target", not iss,
        f"{len(iss)} issue(s) for `> /dev/mtd0ro`")

    # B9 -- 🔴 THE TOKENISER'S OWN PRECONDITION, measured over the corpus
    # rather than asserted in the docstring.  `argv0s()` is not a shell: it does
    # not understand quoting, `$(...)`, backticks or `sh -c`.  That is the right
    # simplification only while no card needs them, and this is what says so.
    # The day a card does, this case goes red BEFORE the card is taken to the
    # bench, which is the whole point of it being a case and not a sentence.
    shellish = []
    for c in cards:
        try:
            t = _read(c).decode("utf-8", "replace")
        except OSError:
            continue
        for cid, cmd in sends_with_cells(t):
            # ⚠️ `-c` ALONE IS NOT A SHELL.  量 2026-08-31, this control's first
            # run: a bare ` -c ` test named three cells, and all three were
            # `ping -c 4 10.1.1.2` and `busybox wc -c` -- ordinary option
            # flags.  It is the INTERPRETER that matters, so the test is on the
            # word before it.  A control that cannot distinguish `ping -c` from
            # `sh -c` would be switched off within a week.
            if any(ch in cmd for ch in '"`$') or \
                    re.search(r"\b(sh|ash|bash|busybox sh)\s+-c\b", cmd):
                shellish.append(f"{os.path.basename(c)}:{cid}  ({cmd[:34]})")
    row("B9", "no committed card needs shell quoting or substitution",
        not shellish, f"{len(cards)} card(s) swept; "
        + (f"offenders: {shellish[:3]}" if shellish else "0 offender(s)"))

    # A18 -- a declaration that parses to nothing is refused.  Without this the
    # `NOT IN IMAGE` verdict would fire on everything and read as thorough.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "empty.tsv")
        open(p, "w").write("# only comments\n")
        try:
            load_decl(os.path.relpath(p, ROOT))
            row("A18", "an empty declaration is refused", False, "it parsed")
        except Refuse as e:
            row("A18", "an empty declaration is refused",
                "ZERO entries" in str(e), str(e)[:48])

    # ----------------------------------------------------------------- A19-A21
    # 🔴 The `FLR` bypass.  See FLR_LEGACY_CARDS' comment: this is a sentence in
    # `PROGRESS.md` turned into a case, and the sentence was the only thing
    # standing between the card template and a repeat of the 2026-08-31
    # incident, in which two files inside this repository held this unit's MAC.
    _, iss = classify_command("FLR 80A00400 000000 100", names, paths)
    row("A19", "an `FLR` typed through --send is REPORTED",
        len(iss) == 1 and "flrbracket" in iss[0],
        f"{len(iss)} issue(s): {iss[0][:44] if iss else '-'}")

    _, iss = classify_command("FLR 80A00400 000000 100", names, paths,
                              allow_flr=True)
    row("A20", "and a FROZEN card on the legacy list is excused",
        not iss, f"{len(iss)} issue(s) with allow_flr=True")

    # 🔴 THE CONTROL THAT SAYS IT IS A GUARD AND NOT A BLANKET.  Without this,
    # a future edit that flagged every LOADER verb would pass A19 and A20 and
    # make the tool useless on every card that reads a register.
    #
    # 🔄 2026-09-23 (`P2-2`, `FW-113`): `EW B800311C A5000000` LEFT this list.
    # A21 required it to pass, which is the exact opposite of the rule
    # `FW-113` adds -- an `EW` now needs the owner's dated yes (A29) -- so
    # until today this case asserted the defect.  `AUTOBURN 0` stays, and it
    # now guards the flash rule too: it DISARMS the burn, and it is the one
    # `AUTOBURN` a card may type without a yes.
    other = [c for c in ("DW 8040D4A0 1", "J 80500000", "AUTOBURN 0",
                         "LOADADDR 80500000")
             if classify_command(c, names, paths)[1]]
    row("A21", "and no OTHER loader verb is touched by either guard",
        not other, f"{len(other)} of 4 flagged" + (f": {other}" if other else ""))

    # ----------------------------------------------------------------- A22-A24
    # 🔴 The `--idle` guard, with the same three-case shape as A19-A21: it
    # fires, a named frozen card is excused, and it does not touch a cell that
    # is fine.
    LINE = ("/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 "
            "--out bench/x/C1-A --send 'sleep 15 ; cat /proc/x' --idle 4 --seconds 40")
    hits = idle_under_sleep(LINE)
    row("A22", "a cell whose --idle is under its own sleep is REPORTED",
        len(hits) == 1 and hits[0] == ("C1-A", 15, 4.0),
        f"{len(hits)} hit(s): {hits[0] if hits else '-'}")

    frozen = "bench/2026-09-10/PREDICTIONS-B18-block17.md"
    row("A23", "and the FROZEN card carrying the five is excused by name",
        frozen in IDLE_UNDER_SLEEP_EXEMPT
        and len(idle_under_sleep(_read(frozen).decode("utf-8", "replace"))) == 5,
        f"exempt={frozen in IDLE_UNDER_SLEEP_EXEMPT}, "
        f"{len(idle_under_sleep(_read(frozen).decode('utf-8', 'replace')))} "
        f"cell(s) in it")

    # 🔴 THE CONTROL THAT SAYS IT IS A GUARD AND NOT A BLANKET.  Three shapes
    # that must stay silent: idle comfortably over the sleep, a sleep with no
    # --idle at all (--seconds is a hard duration), and no sleep at all.
    quiet = [
        "... capture --out bench/x/A --send 'sleep 3 ; cat /proc/x' --idle 4 --seconds 30",
        "... capture --out bench/x/B --send 'sleep 15 ; cat /proc/x' --seconds 40",
        "... capture --out bench/x/C --send 'cat /proc/x' --idle 3 --seconds 15",
    ]
    noisy = [q for q in quiet if idle_under_sleep(q)]
    row("A24", "and a cell that is FINE is not touched by it",
        not noisy, f"{len(noisy)} of 3 flagged" + (f": {noisy}" if noisy else ""))

    # ----------------------------------------------------------------- A73-A75
    # 🔴 2026-10-08: the guard read only lines that spell out `console-capture`
    # (the note below cards_numbers()), so a cell typed through a card's `CAP`
    # macro was never read.  Nor were A24's three lines, which do not spell it
    # either: 量 with the comparison made a blanket (`max(sl) >= 0`), HEAD's
    # A24 stayed green, `0 of 3 flagged` -- it could not fail.  A22-A24's
    # shape again, on a card that defines `CAP` as cards do: it fires (A73),
    # it is silent on cells that are fine (A74), and the one FROZEN card it
    # now flags is excused by name, cell for cell (A75).  A73 and A74 go
    # through `commands` too, because a guard can be right and unwired.  A73's
    # three lines are the three forms the corpus writes a CAP cell in: a
    # fenced line, a table cell, a wrapper's double-quoted argument.
    capdef = ("`CAP` = `/usr/bin/python3 tools/console-capture.py capture "
              "--port /dev/ttyUSB0 --baud 38400`\n\n")
    capbad = (capdef + "```\n"
              "CAP --out bench/x/C2-A --send 'sleep 15 ; cat /proc/uptime' "
              "--idle 4 --seconds 40\n```\n\n"
              "| **C2-B** | `CAP --out bench/x/C2-B --send 'sleep 6 ; cat "
              "/proc/uptime' --idle 6 --seconds 20` |\n\n"
              "  && bash x.sh --x C2-C \"CAP --out bench/x/C2-C --send 'sleep 9 "
              "; cat /proc/uptime' --idle 3 --seconds 20\" \\\n")
    # A74's first line is R6C-4's own I07 under another --out: `sleep 15`
    # under `--idle 20`, the one CAP line of the three 2026-10-08 cards that
    # carries a sleep and an --idle.
    capok = (capdef + "```\n"
             "CAP --out bench/x/C3-A --send 'sleep 15 ; cat /proc/rtl819x-spi' "
             "--idle 20 --seconds 45\n"
             "CAP --out bench/x/C3-B --send 'sleep 15 ; cat /proc/uptime' "
             "--seconds 40\n"
             "CAP --out bench/x/C3-C --send 'cat /proc/uptime' --idle 3 "
             "--seconds 15\n```\n")

    def cap_card(body):
        """-> (`commands`' count, its FAIL lines) for `body` read as a card."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "cap.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(body)
            said = []
            n = cards_commands(os.path.relpath(p, ROOT), report=said.append)
        return n, [x for x in said if x.startswith("  FAIL")]

    want73 = [("C2-A", 15, 4.0), ("C2-B", 6, 6.0), ("C2-C", 9, 3.0)]
    hits = idle_under_sleep(capbad)
    n73, f73 = cap_card(capbad)
    row("A73", "a CAP cell whose --idle is under its sleep is REPORTED",
        hits == want73 and n73 == 3
        and [x.split()[1] for x in f73] == ["C2-A:", "C2-B:", "C2-C:"],
        f"{len(hits)} of 3 hit(s), `commands` {n73} bad: "
        + (", ".join(c for c, _s, _i in hits) or "-"))

    n74, f74 = cap_card(capok)
    row("A74", "and a CAP cell that is FINE is not touched by it",
        not idle_under_sleep(capok) and n74 == 0,
        f"{len(idle_under_sleep(capok))} of 3 flagged; `commands` {n74} bad"
        + (f": {f74[0].strip()[:40]}" if f74 else ""))

    b52 = "bench/2026-09-27b/PREDICTIONS-B52-block50.md"
    want75 = [(c, 20, 3.0) for c in ("D3-UR1-Q", "D3-UR2-Q", "D3-UR3-Q",
                                     "D3-LUR1-Q")]
    got75 = idle_under_sleep(_read(b52).decode("utf-8", "replace"))
    row("A75", "and B52's four backgrounded sleeps are excused by name",
        b52 in IDLE_UNDER_SLEEP_EXEMPT and got75 == want75,
        f"exempt={b52 in IDLE_UNDER_SLEEP_EXEMPT}, {len(got75)} cell(s): "
        + (", ".join(c for c, _s, _i in got75) or "-"))

    # ----------------------------------------------------------------- A25
    # `CARD-4`.  The measured builtin table is load-bearing, so it gets a
    # population floor BEFORE anything uses it.  An empty or unparsable
    # census would make `_measured()` return the empty set, and every builtin
    # would fall through to the 推 list or to NOT IN IMAGE -- which is this
    # bug again with the sign flipped, and silent.
    meas = measured_builtins()
    row("A25", "the measured builtin census parses and is a population",
        len(meas) >= 30 and "printf" in meas and "read" in meas,
        f"{len(meas)} builtin(s) from {IMAGE_COMMANDS}; "
        f"printf={'printf' in meas} read={'read' in meas}")

    # ----------------------------------------------------------------- A26
    # 🔴 THE CONTROL THAT SAYS IT IS A GUARD AND NOT A BLANKET.  Widening a
    # suppression set and deleting the check print the same green, and the
    # only difference visible from outside is whether something still fails.
    # `awk` is 量 ABSENT from this image (`FW-83`), and `FW-42` measured that
    # even `grep` is here with `-E` missing -- so a name that is neither an
    # applet, nor a declared symlink, nor a measured builtin must still be
    # reported.
    nm, ph = load_decl()
    _k, blanket = classify_command("awk '{print $1}' /proc/uptime", nm, ph)
    _k, blanket2 = classify_command("nosuchtool -x", nm, ph)
    row("A26", "a word in NO population is still NOT IN IMAGE",
        any("NOT IN IMAGE" in i for i in blanket) and
        any("NOT IN IMAGE" in i for i in blanket2),
        f"awk -> {len(blanket)} issue(s), nosuchtool -> {len(blanket2)}")

    # ----------------------------------------------------------------- A27
    # And the thing `P1-1` actually needs: a MEASURED builtin passes with no
    # issue at all, not with a differently-worded one.  🔴 This case FAILS on
    # the implementation that existed before today, where `printf` produced
    # `NOT IN IMAGE` -- it is the fixture the change required.
    _k, pf = classify_command("printf '%s\\n' hello", nm, ph)
    row("A27", "a MEASURED builtin is allowed SILENTLY, not re-worded",
        not pf, f"printf -> {len(pf)} issue(s)"
        + (f": {pf}" if pf else ""))

    # ----------------------------------------------------------------- A28
    # 🔴 THE 推 BRANCH IS CURRENTLY UNREACHABLE, AND THAT IS A READING.
    #
    # 量 2026-09-17: ASH_BUILTINS is a strict SUBSET of the measured table --
    # 27 of 40, zero false positives -- so every name that would have taken
    # the caveat branch now takes the silent one before it.  The branch is
    # kept rather than deleted because `appletcensus`'s T6 pins only the
    # DIRECTION (推 must stay a subset), not equality: a future hand-added
    # guess, or a census taken from a different busybox, makes it live again.
    #
    # This case exists so that stops being invisible.  If it ever goes red,
    # the caveat branch has become reachable and somebody should know which
    # name did it rather than discovering it in a card refusal.
    only_guessed = sorted(ASH_BUILTINS - meas)
    row("A28", "every 推 builtin is also a MEASURED one, so the caveat "
        "branch is unreachable",
        not only_guessed,
        "推 is a strict subset of 量 (27 of 40)" if not only_guessed
        else f"reachable via: {only_guessed}")

    # ------------------------------------------------------------------- B10
    # 🔴 THE CORPUS SWEEP, IN BOTH DIRECTIONS.  Forwards: no card outside the
    # list may type `FLR`.  Backwards: no card ON the list may have stopped
    # typing it -- an allow-list that keeps entries it no longer needs stops
    # being an allow-list and becomes a blanket, one card at a time, with
    # nothing reporting the drift.
    flr_users, stale = set(), set()
    for c in cards:
        try:
            t = _read(c).decode("utf-8", "replace")
        except OSError:
            continue
        if any(cmd.split() and cmd.split()[0] == "FLR"
               for _cid, cmd in sends_with_cells(t)):
            flr_users.add(c)
    offenders = sorted(flr_users - FLR_LEGACY_CARDS)
    stale = sorted(FLR_LEGACY_CARDS - flr_users)
    row("B10", "every card typing `FLR` directly is a named frozen one",
        not offenders and not stale,
        f"{len(cards)} swept, {len(flr_users)} type FLR; "
        + (f"NEW offender(s): {offenders}" if offenders else "")
        + (f"STALE list entr(y/ies): {stale}" if stale else "")
        + ("list exact" if not offenders and not stale else ""))

    # ------------------------------------------------------------------- B11
    # 🔴 THE CORPUS SWEEP, IN BOTH DIRECTIONS, as B10 does it for `FLR`.
    # Forwards: no card outside the list may carry the shape.  Backwards: a
    # card ON the list that no longer carries it is a list entry that has
    # stopped being needed, and an allow-list that keeps those becomes a
    # blanket one card at a time.
    idle_users = set()
    for c in cards:
        try:
            t = _read(c).decode("utf-8", "replace")
        except OSError:
            continue
        if idle_under_sleep(t):
            idle_users.add(c)
    off = sorted(idle_users - IDLE_UNDER_SLEEP_EXEMPT)
    stale2 = sorted(IDLE_UNDER_SLEEP_EXEMPT - idle_users)
    row("B11", "every card whose --idle is under its sleep is a named frozen one",
        not off and not stale2,
        f"{len(cards)} swept, {len(idle_users)} carry the shape; "
        + (f"NEW offender(s): {off}" if off else "")
        + (f"STALE list entr(y/ies): {stale2}" if stale2 else "")
        + ("list exact" if not off and not stale2 else ""))

    # ------------------------------------------------------------ A29-A36, B12
    # 🔴 `FW-113`, the flash-write refusal.  The shape of A19-A21 -- it fires,
    # the named frozen cards are excused, nothing else is touched (A21) --
    # plus the one way through, the owner's dated yes, and B12's sweep.
    # `quiet` was rebound to A24's list above, so these carry their own.
    def silent(*_a, **_k):
        pass

    def card_at(d, name, body):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        return os.path.relpath(p, ROOT)

    def cells(cmds, tag):
        return "".join(f"| **{tag}{i}** | `CAP --out {tag}{i} --send '{c}'` |\n"
                       for i, c in enumerate(cmds))

    def yes_fence(rows):
        return "\n```owner-yes\n" + "".join(r + "\n" for r in rows) + "```\n"

    def not_refused(cmds):
        """The commands that did NOT come back LOADER with exactly the one
        flash-write issue."""
        out = []
        for c in cmds:
            k, iss = classify_command(c, names, paths)
            if not (k == "LOADER" and len(iss) == 1 and "FW-113" in iss[0]):
                out.append(c)
        return out

    # A29 -- the two strings `FW-113` measured passing with no issue, and the
    # other two verbs.  Fails on the code before today, where all four came
    # back `('LOADER', [])`.
    fw4 = ("FLW 0 0 0", "EW 8040D4A0 1", "EB 8040D4A0 1", "AUTOBURN 1")
    miss = not_refused(fw4)
    row("A29", "`FLW`, `EW`, `EB`, `AUTOBURN 1` are each REFUSED",
        not miss, f"{len(fw4) - len(miss)} of {len(fw4)} refused"
        + (f"; passed: {miss}" if miss else ""))

    # A30 -- and in any case.  See flash_write(): the loader's case handling
    # is 讀 as exact and never measured, and the refusal must not depend on
    # which way it turns out.  Fails on the code before today, where `ew` was
    # refused only as a program the image lacks -- which `--expect-absent ew`
    # excused (A35).
    low = ("ew 8040d4a0 1", "Flw 0 0 0", "eB 8040D4A0 1", "autoburn 1")
    miss = not_refused(low)
    row("A30", "and so is each in lower or mixed case",
        not miss, f"{len(low) - len(miss)} of {len(low)} refused"
        + (f"; passed: {miss}" if miss else ""))

    # A31 -- 🔴 THE ONE WAY THROUGH, or the refusal is a blanket over four
    # verbs a card may need.  Each passes by the owner's dated yes naming it
    # exactly, and each passing cell is REPORTED with its date rather than
    # passed in silence.
    with tempfile.TemporaryDirectory() as d:
        lines = []
        n = cards_commands(card_at(d, "yes.md", cells(fw4, "Y") + yes_fence(
            f"2026-09-23\t{c}" for c in fw4)), report=lines.append)
        dated = sum("the owner's yes of 2026-09-23" in x for x in lines)
    row("A31", "each is PERMITTED by the owner's dated yes for it",
        n == 0 and dated == 4, f"{n} bad; {dated} of 4 cells noted with the yes")

    # A32 -- a malformed yes is REFUSED and permits nothing: a month 13, a
    # 30 February, a two-digit year, a space where the TAB goes, no payload.
    # One yes per payload, so a second row for it is refused too, while the
    # first still stands.
    with tempfile.TemporaryDirectory() as d:
        ew1 = cells(("EW 8040D4A0 1",), "T")
        n_bad = cards_commands(card_at(d, "m.md", ew1 + yes_fence((
            "2026-13-01\tEW 8040D4A0 1", "2026-02-30\tEW 8040D4A0 1",
            "26-09-23\tEW 8040D4A0 1", "2026-09-23 EW 8040D4A0 1",
            "2026-09-23\t"))), report=silent)
        n_dup = cards_commands(card_at(d, "dup.md", ew1 + yes_fence((
            "2026-09-23\tEW 8040D4A0 1", "2026-09-24\tEW 8040D4A0 1"))),
            report=silent)
    row("A32", "a malformed or second yes is REFUSED, permits nothing",
        n_bad == 6 and n_dup == 1,
        f"five malformed rows: {n_bad} bad (want 6 -- the EW too); "
        f"a second yes: {n_dup} (want 1)")

    # A33 -- 🔴 EXACT, against the three near-misses a looser match passes.
    # One character LONGER than its yes, which a prefix match passes -- as it
    # would pass `EW 8040D4A0 1 2`, a second word written, since `EW` writes
    # argc - 1 words (`LDR-08`); one that differs in CASE; and a yes with a
    # DOUBLED space, which the loader's tokeniser need not read as the same
    # command (owner_yes()).  Every cell refused and every yes reported as
    # permitting nothing: 3 + 3.
    with tempfile.TemporaryDirectory() as d:
        sent = ("EW 8040D4A0 10", "EB 8040D4A0 1", "EW 8040D4A4 1")
        said = ("EW 8040D4A0 1", "eb 8040D4A0 1", "EW 8040D4A4  1")
        lines = []
        n = cards_commands(card_at(d, "near.md", cells(sent, "N") + yes_fence(
            f"2026-09-23\t{c}" for c in said)), report=lines.append)
        cut = sum(x.startswith("  FAIL  N") for x in lines)
    row("A33", "a yes one character off its payload permits nothing",
        n == 6 and cut == 3, f"{n} bad (want 6); {cut} of 3 cells refused")

    # A34 -- a yes that permits nothing is a defect too: one for a payload no
    # cell sends, and one for a cell that needs no yes at all.
    with tempfile.TemporaryDirectory() as d:
        lines = []
        n = cards_commands(card_at(d, "stale.md", cells(("DW 8040D4A0 1",), "T")
                                   + yes_fence(("2026-09-23\tEW 8040D4A0 1",
                                                "2026-09-23\tDW 8040D4A0 1"))),
                           report=lines.append)
        named = sum("permits nothing on this card" in x for x in lines)
    row("A34", "a yes that permits nothing is REPORTED, not ignored",
        n == 2 and named == 2, f"{n} bad; {named} of 2 stale rows named")

    # A35 -- 🔴 NOTHING BUT THE OWNER'S YES SILENCES IT.  See unsuppressed():
    # both routes -- a ```cardabsent fence and `--expect-absent` -- name `EW`,
    # `ew` and `FLR`, and all three refusals must survive both.  量 on the
    # code before today: each route took this card from 2 bad to 0 -- the
    # `EW` raised nothing to hide, and the other two were hidden.
    with tempfile.TemporaryDirectory() as d:
        three = cells(("EW 8040D4A0 1", "ew 8040d4a0 1",
                       "FLR 80A00400 000000 100"), "H")
        hide = ("EW", "ew", "FLR")
        n_fence = cards_commands(card_at(d, "f.md", three + "\n```cardabsent\n"
                                         + "\n".join(hide) + "\n```\n"),
                                 report=silent)
        n_flag = cards_commands(card_at(d, "g.md", three), report=silent,
                                extra_absent=hide)
    row("A35", "no absence declaration hides a loader-verb refusal",
        n_fence == 3 and n_flag == 3,
        f"cardabsent: {n_fence} of 3 still bad; --expect-absent: {n_flag} of 3")

    # A36 -- the two FROZEN cards are excused by NAME and only by name: the
    # same bytes at another path -- one that keeps the `bench/<date>/<name>`
    # tail, so a suffix or basename key would still match it -- are refused.
    try:
        frozen_bad = {c: cards_commands(c, report=silent)
                      for c in sorted(FLASH_LEGACY_CARDS)}
        src = "bench/2026-08-25/PREDICTIONS-b4-block10.md"
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, src)
            os.makedirs(os.path.dirname(dst))
            with open(dst, "wb") as f:
                f.write(_read(src))
            n_copy = cards_commands(os.path.relpath(dst, ROOT), report=silent)
        row("A36", "the FROZEN cards are excused by name, a copy is not",
            len(frozen_bad) == 2 and not any(frozen_bad.values())
            and n_copy == 2,
            f"frozen: {sorted(frozen_bad.values())} bad; the same bytes "
            f"elsewhere: {n_copy} (want 2, its two EW cells)")
    except (Refuse, OSError) as e:
        row("A36", "the FROZEN cards are excused by name, a copy is not",
            False, str(e)[:60])

    # ------------------------------------------------------------------- B12
    # 🔴 `FW-113`'s corpus sweep, in both directions as B10 does it, at the
    # exemption's own grain -- a (card, exact payload) pair.  Forwards: every
    # flash write any card sends is a frozen pair or is under that card's own
    # yes.  Backwards: every frozen pair is still sent, or the list has begun
    # to turn into a blanket.
    fw_sent, fw_off = {}, []
    for c in cards:
        try:
            t = _read(c).decode("utf-8", "replace")
        except OSError:
            continue
        prs = sends_with_cells(t)
        mine = {cmd.strip() for _cid, cmd in prs
                if flash_write(cmd.strip()) or devflash(cmd)}
        if mine:
            fw_sent[c] = mine
            fw_ok, _n = owner_yes(t, c, prs, silent)
            fw_off += [f"{c}: {p}" for p in sorted(mine - fw_ok)]
    fw_stale = [f"{c}: {p}" for c, ps in sorted(FLASH_LEGACY_CARDS.items())
                for p in sorted(ps) if p not in fw_sent.get(c, ())]
    row("B12", "every corpus flash write is a frozen pair or has a yes",
        not fw_off and not fw_stale,
        f"{len(cards)} swept, {len(fw_sent)} send a flash write; "
        + (f"NEW offender(s): {fw_off}" if fw_off else "")
        + (f"STALE list entr(y/ies): {fw_stale}" if fw_stale else "")
        + ("list exact" if not fw_off and not fw_stale else ""))

    # ------------------------------------------------ A37-A49, B13, B14
    # `FW-124`, HOST cells: host_controls() below.
    host_controls(row, cards, card_at, silent)

    # ------------------------------------------------------- A50-A55, B15
    # HW-1, the vendor's memory node: memnode_controls() below.
    memnode_controls(row, cards, card_at, silent, names, paths)

    # ------------------------------------------------------- A56-A62, B16
    # R8b D8, the driver's flash verbs: devflash_controls() below.
    devflash_controls(row, cards, card_at, silent, cells, yes_fence, names,
                      paths)

    # ------------------------------------------------------- A63-A69, B17
    # R8b D22, which image a cell runs on: image_controls() below.
    image_controls(row, cards, card_at, silent, cells, names, paths)

    print()
    return 0 if ok else 1


def host_controls(row, cards, card_at, silent):
    """`FW-124`'s cases.  Each names, in test-cardcheck-mutants.py, the
    mutant that must turn it red; B13 and B14 are the corpus."""
    import tempfile
    card_a = "bench/2026-09-23/PREDICTIONS-B44-block42.md"
    b43 = "bench/2026-09-22b/PREDICTIONS-B43-block41.md"
    b41 = "bench/2026-09-21f/PREDICTIONS-B41-block39.md"
    tags = ("A37", "A38", "A39", "A40", "A41", "A42", "A43", "A44", "A45",
            "A46", "A47", "A48", "A49", "B13", "B14")
    try:
        cr = _cardrun()
        t_a = _read(card_a).decode("utf-8")
        t43 = _read(b43).decode("utf-8")
        mac_a, mac43 = cr.macros(t_a), cr.macros(t43)
        h_a = {h.name: h for h in cr.host_lines(t_a)}
        h43 = {h.name: h for h in cr.host_lines(t43)}
    except Exception as e:                                  # noqa: BLE001
        for tag in tags:
            row(tag, "FW-124: the HOST-cell fixtures load", False,
                f"{type(e).__name__}: {str(e)[:50]}")
        return

    def v(cmd, table, tools_dir=None):
        return host_command(cmd, table, _new_census(), tools_dir)

    def case(tag, name, fn):
        # Anything a case raises turns THAT case red, named, and the rest run:
        # a mutant that crashes one case must not read as a crash of all.
        try:
            good, detail = fn()
        except Exception as e:                              # noqa: BLE001
            good, detail = False, f"{type(e).__name__}: {str(e)[:60]}"
        row(tag, name, good, detail)

    # A37 -- card A's own Z9-D2 line, with card A's own macros: refused in
    # boot-timeline's words, the line CORRECTIONS-block42 § 1 quotes.
    def a37():
        w = v(h_a["Z9-D2"].cmd, mac_a)
        want = "boot-timeline.py: error: argument --tsv: expected one argument"
        return len(w) == 1 and w[0] == want, (w[0] if w else "accepted")[:70]
    case("A37", "card A's Z9-D2 is REFUSED in boot-timeline's own words", a37)

    # A38 -- B43's C4-DOSE with B43's own `NB`: netblast's words, which it can
    # only say if the macro was expanded.
    def a38():
        w = v(h43["C4-DOSE"].cmd, mac43)
        want = ("netblast.py blast: error: the following arguments are required: "
                "--target, --src, --dev")
        return len(w) == 1 and w[0] == want, (w[0] if w else "accepted")[:70]
    case("A38", "B43's C4-DOSE is REFUSED in netblast's own words", a38)

    # A39 -- and the two lines as the CORRECTIONS ran them are accepted.
    def a39():
        z9 = ("/usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-23 "
              "--tsv bench/2026-09-23/Z9-D2.tsv")
        c4 = ("NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 "
              "--rates 43 --step-s 8 --arp-load --out bench/2026-09-22b/C4-DOSE.json")
        w1, w2 = v(z9, mac_a), v(c4, mac43)
        return (not w1 and not w2,
                f"Z9-D2 as run: {len(w1)} refusal(s); C4-DOSE as run: {len(w2)}")
    case("A39", "both lines as CORRECTIONS ran them are accepted", a39)

    # A40 -- no verdict reads the disk: card A's are identical with the cwd
    # an empty directory, and a HOST& whose record exists is not refused.
    def a40():
        def sweep():
            c = _new_census()
            return [(h.name, tuple(host_command(h.cmd, mac_a, c)))
                    for h in cr.host_lines(t_a)]
        here = sweep()
        old = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            os.chdir(d)
            try:
                there = sweep()
            finally:
                os.chdir(old)
        rec = [h.name for h in cr.host_lines(t_a) if h.kind == "HOST&" and
               os.path.exists(os.path.join(ROOT, h.prefix + ".events"))]
        hit = [n for n, w in here if n in rec and w]
        return (here == there and len(rec) >= 13 and not hit,
                f"{len(here)} cells, same verdicts in an empty cwd: {here == there}; "
                f"{len(rec)} HOST& with a record, {len(hit)} refused")
    case("A40", "card A's verdicts read no disk and no existing record", a40)

    # A41 -- the refusals that live in refuse_args, not in the parser.
    def a41():
        hp = h_a["P1-HP"].cmd.replace(" --seconds 900", "")
        lr = dict(mac_a)
        lr["LR"] = mac_a["LR"]._replace(
            body=mac_a["LR"].body.replace(" --recipe-override a2c56bc8", ""))
        if hp == h_a["P1-HP"].cmd or lr["LR"] == mac_a["LR"]:
            return False, "a fixture did not remove its flag"
        w1, w2 = v(hp, mac_a), v(h_a["P1L"].cmd, lr)
        return (len(w1) == 1 and "--seconds N is required" in w1[0]
                and len(w2) == 1 and "--recipe-override" in w2[0],
                f"P1-HP: {(w1 or ['accepted'])[0][:30]}; P1L: {(w2 or ['accepted'])[0][:30]}")
    case("A41", "no --seconds / no --recipe-override is REFUSED (refuse_args)", a41)

    # A42 -- a tool without the contract, and no tool at all, are refused.
    def a42():
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "nocontract.py"), "w") as f:
                f.write("import argparse\ndef main():\n    ap = argparse.ArgumentParser()\n"
                        "    ap.add_argument('--x')\n    return ap.parse_args()\n")
            v1 = tool_verdict("nocontract", ["--x", "1"], d)
            v2 = tool_verdict("nosuch", [], d)
        w3 = v("/usr/bin/python3 tools/nosuch.py --x 1", {})
        return (v1[0] == "REFUSED" and "FW-124 contract" in v1[1]
                and v2[0] == "REFUSED" and "no such tool" in v2[1]
                and len(w3) == 1 and "no such tool" in w3[0],
                f"no contract: {v1[0]}; absent: {v2[0]}; absent in a cell: {len(w3)}")
    case("A42", "a tool without the contract, or no tool, is REFUSED", a42)

    # A43 -- an undefined macro in first position, a bare tool name and a
    # placeholder are refused; an ALL-CAPS word elsewhere is not.
    def a43():
        bad = (("NB probe --target 10.1.1.1 --dev lo", "`NB` is in first position"),
               ("looprun --mode plan --cell A0", "`looprun` is a bare tool name"),
               ("ping -c 1 <ip>", "an unfilled placeholder in `<ip>`"))
        missed = [c for c, frag in bad if not any(frag in w for w in v(c, {}))]
        fine = [c for c in ("/usr/bin/python3 tools/looprun.py --mode plan --cell A0",
                            "socat -T2 STDIO TCP:10.1.1.3:9999") if v(c, {})]
        return (not missed and not fine,
                f"not refused: {missed or '-'}; refused but fine: {fine or '-'}")
    case("A43", "undefined macro / bare tool / <placeholder> REFUSED, STDIO not", a43)

    # A44 -- the shell reading: wrappers and VAR= stripped to reach the tool,
    # a quoted `;` is one word, redirections dropped, `$` refused in a tool.
    def a44():
        bt = "/usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-23 --tsv"
        wrapped = ("timeout 70 " + bt, "sudo -n " + bt, "FWRE_WORK=/x " + bt,
                   "timeout -s INT 70 sudo -n FWRE_WORK=/x " + bt)
        missed = [c.split(" /usr")[0] for c in wrapped
                  if not any("expected one argument" in w for w in v(c, {}))]
        quoted = len(cr.simple_commands("pkill -INT -f 'P1-HP ; --target'"))
        redir = v("/usr/bin/python3 tools/boot-timeline.py --legend 2>&1 > /tmp/x", {})
        dollar = v("/usr/bin/python3 tools/boot-timeline.py --retro $DIR", {})
        return (not missed and quoted == 1 and not redir
                and len(dollar) == 1 and "shell expansion" in dollar[0],
                f"wrappers missed: {missed or '-'}; quoted `;` -> {quoted} command(s); "
                f"redirections {len(redir)} refusal(s); $DIR {len(dollar)}")
    case("A44", "wrappers, quotes, redirections and `$` read as the shell would", a44)

    # A45 -- a crash is exit 2 naming the tool; no build_parser is refused.
    def a45():
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "crashy.py"), "w") as f:
                f.write("import argparse\nclass Refused(Exception):\n    pass\n"
                        "def build_parser():\n    ap = argparse.ArgumentParser()\n"
                        "    ap.add_argument('--x')\n    return ap\n"
                        "def refuse_args(a):\n    raise ValueError('a bug in the tool')\n")
            with open(os.path.join(d, "noparser.py"), "w") as f:
                f.write("class Refused(Exception):\n    pass\n"
                        "def refuse_args(a):\n    pass\n")
            try:
                tool_verdict("crashy", ["--x", "1"], d)
                crashed = ""
            except Refuse as e:
                crashed = str(e)
            v2 = tool_verdict("noparser", [], d)
        return ("tools/crashy.py CRASHED" in crashed and "ValueError" in crashed
                and v2[0] == "REFUSED" and "build_parser" in v2[1],
                f"crash: {crashed[:36] or 'not raised'}; no parser: {v2[0]}")
    case("A45", "a crash is Refuse naming the tool; no build_parser REFUSED", a45)

    # A46 -- the exact-option rule: an abbreviation argparse would expand.
    def a46():
        ab = ("NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 "
              "--rate 43")
        w1, w2 = v(ab, mac43), v(ab.replace("--rate ", "--rates "), mac43)
        return (len(w1) == 1 and "abbreviation" in w1[0] and "`--rates`" in w1[0]
                and not w2, f"--rate: {(w1 or ['accepted'])[0][:40]}; --rates: {len(w2)}")
    case("A46", "--rate 43 is REFUSED as an abbreviation; --rates 43 is not", a46)

    # A47 -- the grammar's own refusals, through cardrun: a macro defined
    # twice (and a card carrying one), a <p> macro with no argument.
    def a47():
        try:
            cr.macros("`CAP` = `a`\n`CAP` = `b`\n")
            dup = ""
        except cr.Refused as e:
            dup = str(e)
        n_dup = host_cells("x.md", "`CAP` = `a`\n`CAP` = `b`\nHOST b/D1 :: echo d\n",
                           silent)
        fl = {"FL": mac_a["FL"]}
        missed = []
        for c in ("FL", "FL ; echo x", "echo x ; FL"):
            try:
                cr.expand(c, fl)
                missed.append(c)
            except cr.Refused:
                pass
        ok_exp = cr.expand("FL 10.1.1.1", fl)
        return ("defined twice" in dup and n_dup == 1 and not missed
                and "flush to 10.1.1.1/32" in ok_exp,
                f"twice: {bool(dup)} (a card with it: {n_dup} bad); FL with no <ip> "
                f"not refused: {missed or '-'}")
    case("A47", "a macro defined twice, and FL with no <ip>, are REFUSED", a47)

    # A48 -- the summary says what was NOT checked, by name, on every card.
    def a48():
        lines = []
        bad = host_cells(card_a, t_a, lines.append)
        s = [ln for ln in lines if ln.startswith("  HOST ")]
        s = s[0] if len(s) == 1 else ""
        return (bad == 0 and "HOST 71 cell(s), 1 refused (1 on FROZEN_HOST_CELLS)" in s
                and "21 project-tool command(s)" in s and "20 accepted, 1 REFUSED" in s
                and "100 system command(s) NOT argument-checked: ip 33, " in s
                and "12 keyword-only" in s, s[2:64] or "no single summary line")
    case("A48", "card A's summary names the 100 unchecked system commands", a48)

    # A49 -- the check is wired into `commands`: one bad HOST cell is one bad.
    def a49():
        with tempfile.TemporaryDirectory() as d:
            good = ("| **T1** | `CAP --out x --send 'cat /proc/mtd'` |\n\n"
                    "HOST bench/x/H1 :: /usr/bin/python3 tools/boot-timeline.py "
                    "--retro bench/2026-09-23 --tsv bench/x/H1.tsv\n")
            n_good = cards_commands(card_at(d, "g.md", good), report=silent)
            n_bad = cards_commands(card_at(d, "b.md", good.replace(" bench/x/H1.tsv", "")),
                                   report=silent)
        n_a = cards_commands(card_a, report=silent)
        return (n_good == 0 and n_bad == 1 and n_a == 0,
                f"good twin {n_good} bad, bad twin {n_bad}, card A {n_a}")
    case("A49", "`commands` counts a refused HOST cell as a defect", a49)

    # B13/B14 -- the corpus, swept once.
    corpus = {}
    for c in cards:
        t = _read(c).decode("utf-8", "replace")
        try:
            if cr.host_lines(t):
                corpus[c] = (t, host_check(t), "")
        except cr.Refused as e:
            corpus[c] = (t, None, str(e))

    # B13 -- FROZEN_HOST_CELLS both ways, at the grain of the defect.
    def b13():
        refused, grammar = {}, [f"{c}: {e}" for c, (_t, _r, e) in corpus.items() if e]
        for c, (_t, res, e) in corpus.items():
            for h, why in (res[0] if res else ()):
                if why:
                    refused.setdefault((c, h.name), []).append("; ".join(why))
        listed = {(c, cell): frag for c, cells in FROZEN_HOST_CELLS.items()
                  for cell, (frag, _w) in cells.items()}
        new = sorted(k for k in refused if k not in listed)
        stale = sorted(k for k in listed if k not in refused)
        wrong = sorted(k for k in listed if k in refused
                       and not all(listed[k] in w for w in refused[k]))
        twice = sorted(k for k in listed if len(refused.get(k, ())) > 1)
        # The reason B41's seven are listed is its grammar and nothing else:
        # with NB supplied, netblast accepts every one.
        t41 = corpus[b41][0]
        nb = dict(cr.macros(t41))
        nb["NB"] = cr.Macro(None, "/usr/bin/python3 tools/netblast.py", 0)
        still = [h.name for h in cr.host_lines(t41) if (b41, h.name) in listed and v(h.cmd, nb)]
        ok = not (new or stale or wrong or twice or grammar or still)
        return ok, (f"{len(refused)} corpus refusal(s), {len(listed)} listed; list exact; "
                    f"B41's 7 pass netblast with NB supplied" if ok else
                    f"NEW {new} STALE {stale} WRONG-REASON {wrong} TWICE {twice} "
                    f"GRAMMAR {grammar} B41-STILL {still}")
    case("B13", "every corpus HOST refusal is a FROZEN pair, and each still is", b13)

    # B14 -- the population, and the HOST count against each card's cardnum.
    def b14():
        n_cells = n_tool = checked = 0
        tools, mism = set(), []
        for c, (t, res, _e) in corpus.items():
            n = len(cr.host_lines(t))
            n_cells += n
            if res:
                n_tool += sum(res[1]["tool"].values())
                tools |= set(res[1]["tool"])
            m = FENCE_RE.search(t)
            for ln in (m.group(1).split("\n") if m else ()):
                f = ln.split("\t")
                if len(f) == 3 and f[0].strip() == "host-cells":
                    checked += 1
                    if int(f[1]) != n:
                        mism.append(f"{c}: cardnum {f[1]}, HOST lines {n}")
        # The floors are the corpus as its newest card froze (B50, 2026-09-26): a card
        # that adds HOST cells raises them, or M59 stops being B14's kill (量 109th;
        # 量 113th: at B45's floors B50's 113 tool commands kept M59 above 54).
        ok = (len(corpus) >= 19 and n_cells >= 1023 and n_tool >= 113 and len(tools) >= 7
              and checked >= 19 and not mism)
        return ok, (f"{len(corpus)} card(s), {n_cells} cell(s), {n_tool} tool command(s) "
                    f"over {len(tools)} tool(s); host-cells cardnum agrees on "
                    f"{checked - len(mism)} of {checked}" + (f": {mism}" if mism else ""))
    case("B14", "the HOST population, and its count against each cardnum", b14)


def devflash_controls(row, cards, card_at, silent, cells, yes_fence, names,
                      paths):
    """R8b D8's cases: the driver's three flash verbs on /proc/rtl819x-spi are
    refused without the owner's yes, permitted by it, exact in region and in
    sha256, never hidden by an absence declaration, and no blanket over the
    driver's other verbs.  B16 is the corpus."""
    import tempfile
    node = " > " + SPI_NODE
    sha_x = "ab" * 32
    sha_y = "ab" * 31 + "ac"
    inst_x = "echo install slotA sha=" + sha_x + node
    three = (inst_x, "echo erase barrier" + node, "echo eraseprobe" + node)

    def dev(cmd):
        return [i for i in classify_command(cmd, names, paths)[1]
                if i.startswith(SPI_NODE + ":")]

    def case(tag, name, fn):
        try:
            good, detail = fn()
        except Exception as e:                              # noqa: BLE001
            good, detail = False, f"{type(e).__name__}: {str(e)[:60]}"
        row(tag, name, good, detail)

    def run(name, sent, said, absent=None, extra=()):
        with tempfile.TemporaryDirectory() as d:
            lines = []
            # no fence at all when there is no yes: an EMPTY owner-yes fence
            # followed by another fence is read by OWNER_YES_RE as one fence
            # whose row is the closing ``` -- a defect of the fixture's own
            body = cells(sent, "D") + (yes_fence(f"2026-10-05\t{c}"
                                                 for c in said) if said else "")
            if absent:
                body += "\n```cardabsent\n" + "\n".join(absent) + "\n```\n"
            n = cards_commands(card_at(d, name, body), report=lines.append,
                               extra_absent=extra)
        return n, lines

    # A56 -- the three verbs, each one issue, each named a flash write
    def a56():
        miss = [c for c in three
                if len(dev(c)) != 1 or "FLASH WRITE" not in dev(c)[0]]
        return (not miss, f"{3 - len(miss)} of 3 refused as FLASH WRITE"
                + (f"; passed: {miss}" if miss else ""))
    case("A56", "install, erase, eraseprobe to the driver are REFUSED", a56)

    # A57 -- every other spelling of the same write, and a line whose content
    # this tool cannot read, which could carry any of them
    def a57():
        spell = ["echo install slotA sha=" + sha_x + " >> " + SPI_NODE,
                 "echo install slotA sha=" + sha_x + " >" + SPI_NODE,
                 "echo INSTALL slotA sha=" + sha_x + node,
                 "echo Erase barrier" + node,
                 "echo -n eraseprobe" + node,
                 "echo installx" + node,
                 "echo verify;echo eraseprobe" + node,
                 'printf "install slotA\\n"' + node,
                 "echo $V" + node,
                 "echo -e eraseprobe" + node,
                 "echo eraseprobe | tee " + SPI_NODE,
                 'sh -c "echo eraseprobe' + node + '"']
        miss = [c for c in spell if len(dev(c)) != 1]
        return (not miss, f"{len(spell) - len(miss)} of {len(spell)} refused"
                + (f"; passed: {miss}" if miss else ""))
    case("A57", "and so is every other spelling, or a line it cannot read",
         a57)

    # A58 -- 🔴 THE ONE WAY THROUGH: the owner's dated yes, naming each
    # exact payload; each permitted cell is noted with the yes's date
    def a58():
        n, lines = run("dev-yes.md", three, three)
        dated = sum("the owner's yes of 2026-10-05" in x for x in lines)
        return (n == 0 and dated == 3,
                f"{n} bad; {dated} of 3 cells noted with the yes")
    case("A58", "each is PERMITTED by the owner's dated yes for it", a58)

    # A59, A60 -- the yes binds the sha256 and the region: a yes for sha X
    # does not let a cell send sha Y, nor slotB ride on slotA's yes.  Each is
    # two defects -- the cell refused, and the yes permitting nothing.
    def a59():
        n, lines = run("dev-sha.md", ("echo install slotA sha=" + sha_y + node,),
                       (inst_x,))
        stale = sum("permits nothing on this card" in x for x in lines)
        return (n == 2 and stale == 1, f"{n} bad (want 2); stale yes {stale}")
    case("A59", "a yes for one sha256 does not permit another", a59)

    def a60():
        n, lines = run("dev-reg.md", ("echo install slotB sha=" + sha_x + node,),
                       (inst_x,))
        stale = sum("permits nothing on this card" in x for x in lines)
        return (n == 2 and stale == 1, f"{n} bad (want 2); stale yes {stale}")
    case("A60", "a yes for one region does not permit another", a60)

    # A61 -- nothing but the owner's yes silences it: neither a ```cardabsent
    # fence nor --expect-absent naming the writer, the node or the verb
    def a61():
        hide = ("echo", SPI_NODE, "install", "erase", "eraseprobe")
        n_fence, _l = run("dev-hide.md", three, (), absent=hide)
        n_flag, _l = run("dev-flag.md", three, (), extra=hide)
        return (n_fence == 3 and n_flag == 3,
                f"cardabsent: {n_fence} of 3 still bad; --expect-absent: "
                f"{n_flag} of 3")
    case("A61", "no absence declaration hides a driver flash verb", a61)

    # A62 -- 🔴 THE CONTROL THAT SAYS IT IS A GUARD AND NOT A BLANKET: the
    # driver's other verbs, the staging sink, reads of both files, and the
    # verb's word written somewhere else are all left alone
    def a62():
        quiet = ["echo verify" + node, "echo map 1 3" + node,
                 "echo arm 0x70000 0x190000 0x120000" + node,
                 "echo disarm" + node, "echo img reset" + node,
                 "echo trywrite" + node, "echo corrupt off" + node,
                 "cat /fw/P.rlxu > " + SPI_NODE + "-img", "cat " + SPI_NODE,
                 "cat " + SPI_NODE + "-map", "echo eraseprobe > /tmp/x"]
        noisy = [c for c in quiet if dev(c)]
        return (not noisy, f"{len(noisy)} of {len(quiet)} flagged"
                + (f": {noisy}" if noisy else ""))
    case("A62", "and the driver's other verbs are not touched by it", a62)

    # A70 -- 🔴 EVERY QUOTING OF THE SAME WRITE, the one measured past the
    # first version first: refused as one issue with no yes, and passed by a
    # yes for that exact payload -- through devflash() for all of them, and
    # through a whole card for the spellings a single-quoted --send can carry
    s = "install slotA sha=" + sha_x + " pace=10000"
    spell = ["echo '" + s + "'" + node, 'echo "' + s + '"' + node,
             "echo 'install' slotA sha=" + sha_x + node,
             "echo i'nst'\"all\" slotA sha=" + sha_x + node,
             "echo 'erase barrier'" + node, "echo \"\" eraseprobe" + node,
             "echo in\"stall\" slotA sha=" + sha_x + node,
             "echo \\install slotA sha=" + sha_x + node,
             "echo inst\\all slotA sha=" + sha_x + node,
             "echo " + s + " > \"" + SPI_NODE + "\"",
             "echo " + s + " >" + SPI_NODE[:-1] + "\"i\"",
             "echo " + s + " > /proc//rtl819x-spi",
             "cd /proc ; echo eraseprobe > rtl819x-spi",
             "echo -n x & echo eraseprobe" + node,
             "echo \"eraseprobe" + node, "echo eraseprobe" + node + "\\"]

    def a70():
        miss = [c for c in spell if len(dev(c)) != 1
                or devflash(c, frozenset({c.strip()}))]
        card = [c for c in spell if "'" not in c]
        n_no, _l = run("dev-quote.md", card, ())
        n_yes, lines = run("dev-quote-yes.md", card, card)
        return (not miss and n_no == len(card) and n_yes == 0,
                f"{len(spell) - len(miss)} of {len(spell)} refused, each passed "
                f"by its exact yes; a card of {len(card)}: {n_no} bad, with "
                f"the yeses {n_yes}" + (f"; WRONG: {miss}" if miss else ""))
    case("A70", "every quoting of a flash verb or the node is REFUSED", a70)

    # A71 -- the node given to a program as an ARGUMENT, or a target this
    # tool cannot read, is refused; and a reader, a printer, the staging
    # sink, a quoted harmless verb and a comment are not a blanket's victims
    def a71():
        loud = ["cp /tmp/v " + SPI_NODE, "busybox cp /tmp/v " + SPI_NODE,
                "ln -s " + SPI_NODE + " /tmp/q", "dd of=" + SPI_NODE,
                "echo eraseprobe > /proc/rtl819x-sp?", "cp /tmp/v /proc/rtl*",
                "N=" + SPI_NODE + " ; cp /tmp/v $N"]
        # the last is the committed RUN-armI/II shape: a $ that names nothing
        quiet = ["head -c 64 " + SPI_NODE, "grep inst_ " + SPI_NODE,
                 "ls -l " + SPI_NODE, "echo rtl819x-spi > /tmp/x",
                 "echo 'verify'" + node, 'echo "map 1 3"' + node,
                 "cat /fw/P.rlxu 2>&1 > " + SPI_NODE + "-img",
                 "echo eraseprobe #" + node,
                 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END']
        missed = [c for c in loud if len(dev(c)) != 1]
        noisy = [c for c in quiet if dev(c)]
        return (not missed and not noisy,
                f"{len(loud) - len(missed)} of {len(loud)} refused, "
                f"{len(noisy)} of {len(quiet)} quiet ones flagged"
                + (f"; MISSED {missed}" if missed else "")
                + (f"; NOISY {noisy}" if noisy else ""))
    case("A71", "an argument or an unreadable target is REFUSED, no blanket",
         a71)

    # A72 -- 🔴 A --send IS READ WHOLE OR NOT AT ALL: `'...'\''...'` (a '
    # inside), `--send=`, a double-quoted --send and argparse's `--sen` are
    # each a FAIL naming the cell -- never a truncated payload, and never
    # silence; a --send ended by a space, a backtick or the line is fine
    def a72():
        odd = ["CAP --out O1 --send 'echo '\\''eraseprobe'\\''" + node + "'",
               "CAP --out O2 --send='echo eraseprobe" + node + "'",
               'CAP --out O3 --send "echo eraseprobe' + node + '"',
               "CAP --out O4 --sen 'echo eraseprobe" + node + "'"]
        fine = ["CAP --out F1 --send 'echo verify" + node + "' --seconds 5",
                "| **F2** | `CAP --out F2 --send 'cat " + SPI_NODE + "'` |",
                "CAP --out F3 --send 'cat /proc/uptime'"]
        got = [glued_sends(x, silent) for x in odd]
        clean = [glued_sends(x, silent) for x in fine]
        with tempfile.TemporaryDirectory() as d:
            n = cards_commands(card_at(d, "dev-glued.md", "\n".join(
                fine + odd) + "\n"), report=silent)
        return (got == [1, 1, 1, 1] and clean == [0, 0, 0] and n == 4,
                f"odd forms {got} (want 1 each), fine {clean}; the card: "
                f"{n} bad (want 4)")
    case("A72", "a --send it cannot read whole is a FAIL, never truncated",
         a72)

    # B16 -- the corpus, with a population floor so a sweep that read nothing
    # cannot pass: every write to the node is counted, through the same
    # reading devflash() makes, and every refusal among them must be under
    # its card's own yes; and no --send in the corpus is glued (A72's rule)
    def b16():
        writes, flagged, off, glued = 0, 0, [], 0
        for c in cards:
            try:
                t = _read(c).decode("utf-8", "replace")
            except OSError:
                continue
            prs = sends_with_cells(t)
            ok_set, _n = owner_yes(t, c, prs, silent)
            glued += glued_sends(t, silent)
            for _cid, cmd in prs:
                try:
                    simp = _spi_simple(_sh_tokens(cmd.strip()))
                except ValueError:
                    simp = []
                writes += sum(any(_spi_hit(x) for x in tg) for _w, tg in simp)
                if devflash(cmd):
                    flagged += 1
                    if cmd.strip() not in ok_set:
                        off.append(f"{c}: {cmd}")
        return (writes >= 40 and not off and not glued,
                f"{len(cards)} cards, {writes} writes to {SPI_NODE}, "
                f"{flagged} refused, {glued} glued --send"
                + (f", NEW offender(s): {off}" if off else ", none unyessed"))
    case("B16", "every corpus driver flash verb has a yes", b16)


def image_controls(row, cards, card_at, silent, cells, names, paths):
    """R8b D22's cases: the delivery cell is refused on the mainline image
    and permitted on the armed one; the armed table is reached per cell and
    only through the card's own fence, read exactly; `busybox <word>` is read
    at argv0s()'s positions, against a table with a population floor; the
    frozen exemption is keyed by card and applet, and B17 sweeps it both
    ways.  Each names, in test-cardcheck-mutants.py, the mutant that must
    turn it red."""
    import tempfile
    deliver = "busybox nc -l -p 5000 </dev/null >/proc/rtl819x-spi-img &"

    def case(tag, name, fn):
        try:
            good, detail = fn()
        except Exception as e:                              # noqa: BLE001
            good, detail = False, f"{type(e).__name__}: {str(e)[:60]}"
        row(tag, name, good, detail)

    def nc(iss):
        return [i for i in iss if i.startswith("nc: NOT IN IMAGE")]

    # A63 -- 🔴 D22's delivery command on a MAINLINE cell: refused, by the
    # applet table, with the one issue naming nc.  Before applets() it passed.
    def a63():
        k, iss = classify_command(deliver, names, paths)
        return (k == "SHELL" and len(iss) == 1 and len(nc(iss)) == 1,
                f"{k}, {len(iss)} issue(s): {iss[0][:46] if iss else 'none'}")
    case("A63", "R8b's `busybox nc -l` on a MAINLINE cell is REFUSED", a63)

    # A64 -- and on an ARMED cell the same command passes with no issue
    def a64():
        k, iss = classify_command(deliver, names, paths,
                                  img=("armed", frozenset()))
        return (k == "SHELL" and not iss, f"{k}, {len(iss)} issue(s)"
                + (f": {iss[0][:40]}" if iss else ""))
    case("A64", "and on an ARMED cell it is PERMITTED", a64)

    # A65 -- 🔴 PER CELL, AND ONLY THROUGH THE FENCE: no fence -> the nc
    # cell is refused; `armed *` -> permitted; a fence naming the OTHER cell
    # leaves it mainline, refused; naming it by its --out's last field
    # (a CELLS-file line, no **ID**) -> permitted
    def a65():
        body = (cells(("cat /proc/uptime",), "N")
                + f"CAP --out bench/x/ZZ-nc --send '{deliver}'\n")
        got = []
        with tempfile.TemporaryDirectory() as d:
            for name, fence in (("none.md", ""), ("all.md", "armed\t*"),
                                ("other.md", "armed\tN0"),
                                ("this.md", "armed\tZZ-nc")):
                text = body + (f"\n```cardimage\n{fence}\n```\n" if fence
                               else "")
                got.append(cards_commands(card_at(d, name, text),
                                          report=silent))
        return (got == [1, 0, 1, 0], f"bad, no fence / * / other cell / "
                f"this cell: {got} (want [1, 0, 1, 0])")
    case("A65", "the armed table is selected per cell, by the fence only",
         a65)

    # A66 -- 🔴 READ EXACTLY: every fence it cannot read is REFUSED, never
    # read as mainline -- an unknown image, a space for the TAB, a cell no
    # --send carries, a cell named twice, `*` beside a row, two fences, a
    # fence of comments only, and one with no line at all
    def a66():
        body = cells(("cat /proc/uptime", deliver), "N")
        bad = {"unknown image": "Armed\t*", "no TAB": "armed N1",
               "no such cell": "armed\tN9",
               "named twice": "armed\tN1\nmainline\tN1",
               "* beside a row": "armed\t*\nmainline\tN0",
               "two fences": "armed\tN1\n```\n\n```cardimage\narmed\tN1",
               "comments only": "# armed\tN1"}
        texts = {k: body + f"\n```cardimage\n{v}\n```\n" for k, v in bad.items()}
        texts["no line at all"] = body + "\n```cardimage\n```\n"
        read = []
        for what, text in texts.items():
            try:
                card_images(text, "a66.md", sends_with_cells(text))
                read.append(what)
            except Refuse:
                pass
        return (not read, f"{len(texts) - len(read)} of {len(texts)} refused"
                + (f"; READ: {read}" if read else ""))
    case("A66", "a ```cardimage fence it cannot read exactly is REFUSED", a66)

    # A67 -- the positions are argv0s()'s: `busybox` as an ARGUMENT is no
    # command, one after a separator is, and a redirection before the
    # applet is skipped as the shell skips it
    def a67():
        arg = classify_command("echo busybox nc", names, paths)[1]
        pipe = classify_command("cat /proc/uptime | busybox nc -l -p 5000",
                                names, paths)[1]
        redir = classify_command("busybox </dev/null nc -l -p 5000",
                                 names, paths)[1]
        return (not arg and len(nc(pipe)) == 1 and len(nc(redir)) == 1,
                f"as an argument {len(arg)} issue(s); after | {len(nc(pipe))};"
                f" after a redirection {len(nc(redir))}")
    case("A67", "`busybox <word>` is read where argv0s() reads a command",
         a67)

    # A68 -- the population floor: a table that parsed to too few applets
    # REFUSES, rather than refusing every busybox applet and reading thorough
    def a68():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "thin.tsv")
            with open(p, "w", encoding="utf-8") as f:
                f.write("kind\tname\n"
                        + "".join(f"applet\ta{i:02d}\n" for i in range(5))
                        + "".join(f"builtin\tb{i:02d}\n" for i in range(20)))
            IMAGES["a68-thin"] = os.path.relpath(p, ROOT)
            try:
                image_table("a68-thin")
                return False, "a 5-applet table was accepted"
            except Refuse as e:
                return "under" in str(e), str(e)[:60]
            finally:
                IMAGES.pop("a68-thin", None)
                _TABLES.pop("a68-thin", None)
    case("A68", "a table under the applet floor is REFUSED", a68)

    # A69 -- the frozen exemption is keyed by CARD and APPLET: card B37
    # reports what it reported before applets(), and the same `busybox
    # telnetd` on any other card is refused
    def a69():
        n37 = cards_commands("bench/2026-09-21c/PREDICTIONS-B37-block35.md",
                             report=silent)
        with tempfile.TemporaryDirectory() as d:
            n = cards_commands(card_at(d, "telnetd.md", cells(
                ("busybox telnetd -p 9999",), "T")), report=silent)
        return (n37 == 0 and n == 1, f"B37: {n37} bad; another card: {n} bad")
    case("A69", "B37's busybox telnetd is excused there and nowhere else",
         a69)

    # B17 -- APPLET_LEGACY_CARDS both ways, as B10 sweeps FLR_LEGACY_CARDS:
    # every corpus `busybox <word>` outside its cell's table is on the list,
    # and every listed (card, applet) is still sent -- with a population
    # floor, so a sweep that read nothing cannot pass
    def b17():
        n_bb, found = 0, {}
        for c in cards:
            try:
                t = _read(c).decode("utf-8", "replace")
            except OSError:
                continue
            prs = sends_with_cells(t)
            for (_cid, cmd), (img, _x) in zip(prs, card_images(t, c, prs)):
                n_bb += sum(os.path.basename(w) == "busybox"
                            for w in cmd.split())
                for i in applets(cmd, (img, frozenset())):
                    found.setdefault(c, set()).add(i.split(":")[0])
        leg = APPLET_LEGACY_CARDS
        off = [f"{c}: {sorted(s - leg.get(c, frozenset()))}"
               for c, s in sorted(found.items()) if s - leg.get(c, frozenset())]
        stale = [f"{c}: {sorted(s - found.get(c, set()))}"
                 for c, s in sorted(leg.items()) if s - found.get(c, set())]
        return (n_bb >= 100 and not off and not stale,
                f"{len(cards)} swept, {n_bb} busybox word(s); "
                + (f"NEW offender(s): {off} " if off else "")
                + (f"STALE: {stale}" if stale else "")
                + ("list exact" if not off and not stale else ""))
    case("B17", "every corpus busybox applet off its table is a named frozen "
         "one", b17)


def memnode_controls(row, cards, card_at, silent, names, paths):
    """HW-1's cases.  Each names, in test-cardcheck-mutants.py, the mutant
    that must turn it red; B15 is the corpus."""
    import tempfile
    node = " > /proc/rtl865x/memory"

    def hw1(cmd):
        """The command's memory-node issues, through classify_command."""
        return [i for i in classify_command(cmd, names, paths)[1]
                if i.endswith("(HW-1)")]

    def refused(cmds, needle=""):
        return [c for c in cmds if not any(needle in i for i in hw1(c))]

    def passed(cmds):
        return [c for c in cmds if hw1(c)]

    def case(tag, name, fn):
        try:
            good, detail = fn()
        except Exception as e:                              # noqa: BLE001
            good, detail = False, f"{type(e).__name__}: {str(e)[:60]}"
        row(tag, name, good, detail)

    # A50 -- the planted read, and every flash alias.  The fifth word of a
    # read at 0xBD005FF0 is H601's first: the LEN asked for stops short of
    # it and memDump's footprint does not.  Flash outside H601 is refused
    # too, without H601's name.
    def a50():
        h601 = ["echo read 0xBD006000 4" + node, "echo read 0xBFC07FF0 4" + node,
                "echo read 0x9D006100 16" + node, "echo read 0xBD005FF0 4" + node,
                "echo write 0xBD006000 0x0" + node]
        other = ["echo read 0xBD000000 4" + node, "echo read 0x9FC00000 4" + node]
        miss = refused(h601, "H601")
        miss2 = refused(other, "flash 0x")
        named = [c for c in other if any("H601" in i for i in hw1(c))]
        return (not miss and not miss2 and not named,
                f"{len(h601) - len(miss)} of {len(h601)} refused naming H601, "
                f"{len(other) - len(miss2)} of {len(other)} other flash reads "
                f"refused without it" + (f"; passed: {miss + miss2 + named}"
                                          if miss or miss2 or named else ""))
    case("A50", "a read or write reaching flash is REFUSED, H601 named", a50)

    # A51 -- the footprint against the hot words and the window edges, each
    # refusal beside a permitted twin one word away.
    def a51():
        bad = ["echo read 0xBB804118 4" + node, "echo read 0xBB804148 4" + node,
               "echo read 0xBB8045F0 4" + node, "echo read 0xBB804100 64" + node,
               "echo read 0xBB801FF0 4" + node, "echo read 0xB80100F0 4" + node]
        good = ["echo read 0xBB804114 4" + node, "echo read 0xBB80414C 4" + node,
                "echo read 0xBB8045EC 4" + node, "echo read 0xBB804100 16" + node,
                "echo read 0xBB801FEC 4" + node, "echo read 0xB80100EC 4" + node,
                "echo read 0xBB804754 4" + node, "echo read 0xB8000040 4" + node]
        miss, over = refused(bad), passed(good)
        return (not miss and not over,
                f"{len(bad) - len(miss)} of {len(bad)} refused, "
                f"{len(good) - len(over)} of {len(good)} twins permitted"
                + (f"; wrong: {miss + over}" if miss or over else ""))
    case("A51", "memDump's footprint, not LEN, meets PSRP and the edges", a51)

    # A52 -- the one form.  Every other spelling that names `memory` is
    # refused; the forms the committed cards used pass.
    def a52():
        bad = ["echo read 0xbb804100" + node, "echo read 3145728256 4" + node,
               "echo read 0xBB804100 010" + node, "echo read 0xBB804100 257" + node,
               "echo read 0xBB804100 -4" + node, "echo read 0xBB804100 4 x" + node,
               "echo read 0x1BB804100 4" + node,
               "echo read 0xBB804100 4 >> /proc/rtl865x/memory",
               "cat /proc/rtl865x/memory", "echo read 0xBB804100 4 > memory",
               "echo read 0xBB804000 4" + node + " ; echo read 0xBD006000 4" + node]
        good = ["sleep 1 ; echo read 0xBB806100 4 >/proc/rtl865x/memory",
                "echo read 0xBB806100 4 >/proc/rtl865x/memory ; "
                "echo read 0xBB806104 4 >/proc/rtl865x/memory",
                "echo read 0xbb804000 4" + node, "echo read 0xBB804000 256" + node]
        miss, over = refused(bad), passed(good)
        return (not miss and not over,
                f"{len(bad) - len(miss)} of {len(bad)} refused, "
                f"{len(good) - len(over)} of {len(good)} committed forms pass"
                + (f"; wrong: {miss + over}" if miss or over else ""))
    case("A52", "only `echo read|write 0xADDR N > the node` passes", a52)

    # A53 -- writes, through a card: declared and in a write window passes;
    # undeclared, outside a write window (the MIB is read-only here),
    # unaligned or on a hot word is refused, declared or not; a malformed,
    # a second, and an unused ```memwrite row are each a defect.
    def a53():
        w_ok = "echo write 0xBB804110 0x80000000" + node
        sent = [w_ok, "echo write 0xBB804110 0x00000000" + node,
                "echo write 0xB8001200 0x0" + node, "echo write 0xBB801100 0x0" + node,
                "echo write 0xBB804111 0x1" + node, "echo write 0xBB804128 0x0" + node]
        decl = [w_ok] + sent[2:] + [w_ok, "echo write 0xBB804110" + node,
                                    "echo write 0xBB804114 0x1" + node]
        with tempfile.TemporaryDirectory() as d:
            lines = []
            body = "".join(f"| **W{i}** | `CAP --out W{i} --send '{c}'` |\n"
                           for i, c in enumerate(sent))
            n = cards_commands(card_at(d, "w.md", body + "\n```memwrite\n"
                                       + "".join(x + "\n" for x in decl) + "```\n"),
                               report=lines.append)
        cut = [x.split()[1].rstrip(":") for x in lines if x.startswith("  FAIL  W")]
        rows = sum(x.startswith("  FAIL  memwrite") for x in lines)
        good = n == 8 and cut == ["W1", "W2", "W3", "W4", "W5"] and rows == 3
        return good, (f"{n} bad (want 8); refused cells {cut} (want W1-W5); "
                      f"{rows} of 3 fence defects named")
    case("A53", "a write passes only declared, in a write window", a53)

    # A54 -- the FROZEN cards are excused by NAME: each reads no memory-node
    # refusal, and the same bytes at another path read all of theirs.
    def a54():
        at_home, away = {}, {}
        for c, pays in sorted(MEMNODE_LEGACY_CARDS.items()):
            lines = []
            cards_commands(c, report=lines.append)
            at_home[c] = sum("(HW-1)" in x for x in lines)
            with tempfile.TemporaryDirectory() as d:
                dst = os.path.join(d, c)
                os.makedirs(os.path.dirname(dst))
                with open(dst, "wb") as f:
                    f.write(_read(c))
                lines = []
                cards_commands(os.path.relpath(dst, ROOT), report=lines.append)
                away[c] = sum("(HW-1)" in x for x in lines)
        ok = (len(at_home) == 3 and not any(at_home.values())
              and all(v > 0 for v in away.values()))
        return ok, (f"at their own paths {sorted(at_home.values())} refused; "
                    f"the same bytes elsewhere {sorted(away.values())}")
    case("A54", "the FROZEN cards are excused by name, a copy is not", a54)

    # A55 -- no absence declaration hides it: a ```cardabsent fence and
    # --expect-absent, each naming the node, leave the planted read refused.
    def a55():
        hide = ("/proc/rtl865x/memory", "echo")
        body = "| **P0** | `CAP --out P0 --send 'echo read 0xBD006000 4" + node + "'` |\n"
        with tempfile.TemporaryDirectory() as d:
            n_fence = cards_commands(card_at(d, "f.md", body + "\n```cardabsent\n"
                                             + "\n".join(hide) + "\n```\n"),
                                     report=silent)
            n_flag = cards_commands(card_at(d, "g.md", body), report=silent,
                                    extra_absent=hide)
        return n_fence == 1 and n_flag == 1, (
            f"cardabsent: {n_fence} of 1 still bad; --expect-absent: {n_flag} of 1")
    case("A55", "no absence declaration hides a memory-node refusal", a55)

    # B15 -- the corpus, both ways, at the exemption's grain: every send any
    # card makes to the node is permitted by the rule or is a FROZEN pair,
    # and every FROZEN pair is still sent and still refused without it.
    def b15():
        n_send, off, refused_pairs = 0, [], set()
        for c in cards:
            t = _read(c).decode("utf-8", "replace")
            prs = sends_with_cells(t)
            decl, _n = memnode_ok(t, "", prs, silent, (frozenset(), 0))
            for _cid, cmd in prs:
                if "memory" not in cmd:
                    continue
                n_send += 1
                if memnode(cmd, decl):
                    refused_pairs.add((c, cmd.strip()))
        listed = {(c, p) for c, ps in MEMNODE_LEGACY_CARDS.items() for p in ps}
        new = sorted(refused_pairs - listed)
        stale = sorted(listed - refused_pairs)
        ok = not new and not stale and n_send >= 31
        return ok, (f"{len(cards)} swept, {n_send} send(s) name the node, "
                    f"{len(refused_pairs)} refused; " + (
                        "list exact" if not new and not stale else
                        f"NEW offender(s): {new} STALE: {stale}"))
    case("B15", "every corpus memory-node refusal is a FROZEN pair", b15)


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        print("cardcheck controls")
        return run_controls()
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    sub, card = argv[1], argv[2]
    decl = DECL
    if "--decl" in argv:
        decl = argv[argv.index("--decl") + 1]
    # `--expect-absent` exists for the FROZEN cards.  A card written from now on
    # declares its absence-tests in a ```cardabsent fence; the five blocks that
    # already have captures against them cannot be edited, so the declaration
    # has to be able to come from outside the file.
    absent = [argv[i + 1] for i, a in enumerate(argv) if a == "--expect-absent"]
    try:
        if run_controls_quiet() != 0:
            sys.stderr.write("REFUSING: cardcheck's own controls do not pass\n")
            return 2
        if sub == "commands":
            return 1 if cards_commands(card, decl, extra_absent=absent) else 0
        if sub == "numbers":
            return 1 if cards_numbers(card) else 0
    except Refuse as e:
        sys.stderr.write(f"REFUSED: {e}\n")
        return 2
    sys.stderr.write(f"unknown subcommand `{sub}`\n")
    return 2


def run_controls_quiet():
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return run_controls()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
