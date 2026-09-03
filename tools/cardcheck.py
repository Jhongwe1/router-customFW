#!/usr/bin/env python3
"""cardcheck -- read a bench card the way the DEVICE will, before it is powered.

Two subcommands, and they exist because a card is the one artefact in this
project that is written by hand and executed by a machine that cannot ask
questions.

    commands   every command the card types, checked against what the image
               it uploads DECLARES it can run
    numbers    every number the card states, RE-DERIVED from the artefact it
               names, rather than compared against a transcription

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
    2  refused before checking anything (no card, no declaration, no fence)
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
ASH_BUILTINS = {
    ":", ".", "break", "cd", "continue", "eval", "exec", "exit", "export",
    "false", "hash", "local", "read", "return", "set", "shift", "source",
    "test", "times", "trap", "true", "type", "ulimit", "umask", "unset",
    "wait", "[",
}

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


def classify_command(cmd, names, paths, allow_flr=False):
    """-> (kind, [issue, ...]).  kind is LOADER / CONFIRM / SHELL / EMPTY.

    `allow_flr` excuses the one loader verb that carries a containment rule.
    It is passed per CARD, never per command, so a card cannot silence the
    check for one row and keep it for another.
    """
    cmd = cmd.strip()
    if not cmd:
        return "EMPTY", []
    if cmd in CONFIRM:
        return "CONFIRM", []
    first = cmd.split()[0]
    if first in LOADER_VERBS:
        # 🔴 `FLR` and nothing else.  `DW`, `EW`, `J` and the rest read or write
        # nothing that lands in a file, so a blanket rule over LOADER_VERBS
        # would be noise -- and A21 is the control that says this one is a
        # guard rather than a blanket.
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
    return "SHELL", issues


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

    bad, intentional, kinds = 0, 0, {}
    for cid, cmd in pairs:
        kind, issues = classify_command(cmd, names, paths, allow_flr=legacy_flr)
        kinds[kind] = kinds.get(kind, 0) + 1
        if not issues:
            continue
        keep = [i for i in issues if i.split(":")[0] not in absent]
        if not keep:
            intentional += 1
            report(f"  note  {cid}: {cmd}")
            report(f"          declared absence-test, not a defect")
            continue
        bad += 1
        report(f"  FAIL  {cid}: {cmd}")
        for it in keep:
            report(f"          {it}")
    report(f"  {len(pairs)} command(s): "
           + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items()))
           + f"; declaration has {len(names)} invocable name(s)"
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
    # `> /dev/mtd2ro` is not, and no node of that name exists in the image.
    _, iss_ok = classify_command("echo x > /dev/mtd0ro", names, paths)
    _, iss_no = classify_command("echo x > /dev/mtd2ro", names, paths)
    row("A9", "an undeclared redirection target is caught",
        not iss_ok and any("mtd2ro" in i for i in iss_no),
        f"declared: {len(iss_ok)} issue(s); undeclared: {len(iss_no)}")

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
    other = [c for c in ("DW 8040D4A0 1", "J 80500000", "EW B800311C A5000000",
                         "AUTOBURN 0", "LOADADDR 80500000")
             if classify_command(c, names, paths)[1]]
    row("A21", "and no OTHER loader verb is touched by it",
        not other, f"{len(other)} of 5 flagged" + (f": {other}" if other else ""))

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

    print()
    return 0 if ok else 1


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
