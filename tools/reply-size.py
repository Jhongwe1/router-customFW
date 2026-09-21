#!/usr/bin/env python3
"""reply-size.py -- what the loader will send back, in bytes, before it sends it.

WHY THIS IS A TOOL AND NOT A FORMULA IN A DOCUMENT
--------------------------------------------------
`SPEC.md` LDR-07 carries the formula and on 2026-08-25 it went 15 for 15 across
one seating.  The one prediction that missed was not the formula: block 3
predicted 214 bytes and the capture was 213, because `DW 81000400 16` is
fourteen characters and a person counted fifteen.  `tools/check-predictions.py`
verifies that a prediction file predates its capture; it does not verify the
arithmetic inside it, and both arithmetic errors that seating were in blocks
written at the bench rather than at the desk.

So: the count that goes into a prediction block comes out of this, and `len()`
does the counting.

WHAT A PREDICTED REPLY LENGTH IS WORTH
--------------------------------------
It is a control that costs nothing and that a truncated or a stale capture
cannot pass.  Short by 47 -- a `DW` line went missing.  Short by 9 -- the prompt
never arrived.  Short by anything else -- it is not the reply to the command
that was sent.  States that are not simply "wrong by n" have their own names
here, because a capture that came back 24 bytes when 71 were predicted is
telling you something specific and `MISS` would throw it away:

    ECHO-ONLY        the command was echoed and the prompt came back with no
                     output at all.  `bench/2026-08-24b/CONT.log`, 24 bytes:
                     the first command after a USB re-enumeration is echoed and
                     not acted on (C-19).
    UNKNOWN-COMMAND  the loader answered `Unknown command !`.
                     `bench/2026-08-24/A0-reopen-control.log`, 44 bytes.
    SILENT           nothing came back AT ALL.  This IS a miss.  It is
                     separated from SHORT because the two are about different
                     things: SHORT is a statement about the size model, and
                     SILENT is a statement about whether anything was
                     listening.  A dead port, a dead adapter and a board that
                     is not at a prompt all land here, and none of them is
                     evidence about `DW`'s 47.
    SILENT-EXPLAINED a SILENT whose cause is already written down on disk, in
                     the metadata of the capture taken immediately before it.
                     NOT a miss -- and the only state here that is decided by
                     something outside the capture's own file.

WHEN SILENCE IS EVIDENCE OF SOMETHING ELSE
------------------------------------------
量 2026-09-21: `bench/2026-09-21b/F0-PROMPT` sent `DW 8040D4A0 1` and got 0
bytes in 6.088599 s.  The reason is not in that capture.  It is in the one
before it -- `F0-RB`, `busybox reboot -f` -- whose own metadata records
`cr.esc_after.prompt_seen: false`: the instrument wrote down that the loader
prompt never came back.  A `DW` fired into a board that is not at a prompt gets
nothing, and that is a correct reading of a board rather than a defect in this
model.

So a SILENT is excused only when the capture IMMEDIATELY BEFORE IT IN THE SAME
DIRECTORY recorded `cr.<key>.prompt_seen == false`.  Every clause of that
sentence is load-bearing:

  * IMMEDIATELY BEFORE.  Not "somewhere earlier in the directory" -- a prompt
    that went missing twenty captures ago says nothing about this one.
  * IN THE SAME DIRECTORY.  A directory is one seating.
  * ORDERED BY `started_wallclock`, out of the metadata.  NOT by mtime and NOT
    by filename.  量 on the real case: sorting `bench/2026-09-21b` by filename
    puts `E1-TXUDP` immediately before `F0-PROMPT` and finds no explanation at
    all, because a seating's cells are not named in the order they ran.  mtime
    happens to agree there, and that is the trap -- it agrees until a `cp -a`,
    a restore or a checkout rewrites it, and then it agrees no longer.  The
    timestamp the instrument wrote when it opened the port is the only one of
    the three that is a record rather than a side effect.
  * `prompt_seen == false`, by identity and not by falsiness.  A capture with
    no `cr` block, or a `cr` block with no `prompt_seen`, made no claim about
    the prompt and therefore explains nothing.

否證, and it is deliberately easy to hit: a SILENT that is the first capture in
its directory, or whose predecessor DID see the prompt, is reported as a miss
and turns the sweep red.  A dead port has no predecessor to hide behind, and a
sweep that excused every silence could not tell a bench session from a session
in which nothing was plugged in.

ONE CONFIRMATION OUT OF SAMPLE, AND WHY IT IS OUT OF SAMPLE
-----------------------------------------------------------
F0-PROMPT is the only capture this rule was built on, and n=1 is not a rule.
量 2026-09-21 there is a second: `bench/2026-09-19/X12-phyr02` sent `PHYR 0 2`
-- a MODELLED family, so it is not kept out of the model by being a shell
command -- and got 0 bytes, and its wallclock predecessor `X11-phyr` recorded
`cr.esc_after.prompt_seen: false`.  The rule reaches the right answer on it,
on a seating two days earlier that nobody was looking at when the rule was
written.

It is not a case in `test-reply-size.sh` and it never runs in the sweep,
because `esc_after_seconds` is 10.0 and `cmd_check` skips an ESC-streamed
capture before `classify` is reached.  ⚠️ So the reason there is exactly ONE
SILENT in `bench/` is the ESC skip and NOT the command families -- a statement
worth keeping, because it says where the next one will come from if the ESC
rule is ever narrowed.

THE MODEL, AND WHERE EVERY CONSTANT IN IT CAME FROM
---------------------------------------------------
Every constant below was derived by fitting `bytes - len(cmd)` across every
capture in `bench/` that carries a `sent` field and no ESC streaming -- 133 of
them -- and NOT by reading the loader's source or by counting characters in a
terminal.  The residual is a single value per command family or the family is
not modelled.  `--self-test` re-derives them from the fixtures and refuses to
report if any control fails.

    reply = len(cmd) + 2 + body + 9

        + 2   the LF CR the loader emits after echoing the command
        + 9   `<RealTek>`, the prompt, with no trailing newline
        body  per family, below

    family   body                          samples   fitted residual
    ------   ---------------------------   -------   ---------------
    DW       47 * ceil(n / 4)              91        11
    EW       0                             10        11
    EB       0                             1         11
    Y        23                            6         34
    PHYR     68                            5         79
    FLR      81, AND NO PROMPT             6         81

`DW`'s 47 is one output line: `\r` + `AAAAAAAA:` + four `\t`-plus-eight-hex
groups + `\n`.  The `ceil` is LDR-07's carry trap -- the loop steps `i` by 4 and
tests `i < n`, so `DW <addr> 1` through `DW <addr> 4` all print four words, and
`DW <addr> 10` prints twelve.  The carry is UPWARD, so a length given too small
never says so: the read-back is always whole lines and looks complete.

`FLR` does not end at `<RealTek>`.  It ends at `(Y)es , (N)o ? --> ` and waits.
That is why its residual is 81 and not 81 + 9, and a tool that added the prompt
to every family would be wrong by nine bytes on exactly the command that writes
to RAM from flash.

NOT MODELLED, AND EACH ONE FOR A STATED REASON
-----------------------------------------------
    DB       one sample.  The header row and the per-row format cannot be
             separated from a single length.
    J        two samples, 1779 each -- but that is a property of the IMAGE that
             booted, not of the command.  A different image gives a different
             number and the model would be a coincidence with n=2.
    MDIOR    one sample, and the length depends on how many PHY addresses answer.

An unmodelled family is reported as UNMODELLED and is never counted as a hit.
A tool whose "0 misses" includes everything it declined to look at is the defect
this project calls a sweep with no positive control.
"""

import argparse
import datetime
import glob
import json
import math
import os
import sys

ECHO_TAIL = 2            # the LF CR after the command echo
PROMPT = 9               # '<RealTek>'
UNKNOWN_BODY = 20        # 'Unknown command !' + CR LF + CR
DW_LINE = 47             # one DW output line, terminator included


DW_DEFAULT_WORDS = 4     # what a bare `DW <addr>` prints -- 量, see _dw_body


def _dw_words(argv):
    """How many words a `DW` prints.  ONE source of truth, and that is the
    entire reason this function exists rather than the parse sitting inline.

    🔴 2026-09-19: there were TWO.  The bare-`DW` default was taught to
    `_dw_body` and the identical parse in `predict`'s derivation string --
    `int(argv[2], 10)` -- was left alone, so `--self-test` stayed green while
    `check` over the corpus died with `IndexError` on the first of the three
    seating-28 captures.  Ten controls passed and not one of them called a bare
    `DW`: every one goes through the helper, and the crash was in the caller.
    **A control that exercises a helper does not exercise its caller** -- the
    same sentence as `hazlint` 1.0's `K4` and as this file's own S5, with the
    roles swapped.  `C9` calls `predict`, on purpose.
    """
    if not argv:
        raise ValueError("DW needs an address")
    if len(argv) < 2:
        # 🔴 A BARE `DW <addr>` IS LEGAL AND THIS FUNCTION USED TO RAISE ON IT,
        # which crashed `check` over the whole corpus rather than misreporting
        # one capture.  量 2026-09-19 (seating 28), three captures, one value:
        # `DW 80000000`, `DW 80410094` and `DW B800311C` are **69 bytes each**
        # (X2/X3/X4), and `DW B8010000 4` is **71** (X5/X6).  The model here is
        # len(cmd) + ECHO_TAIL + body + PROMPT, so 11+2+47+9 = 69 and
        # 13+2+47+9 = 71: the bodies are IDENTICAL and the two extra bytes are
        # the echo of the ` 4`.  So the loader's default really is one line of
        # four words, and it is derived from a difference rather than assumed.
        # 否證: a bare-`DW` capture anywhere in the corpus that is not 69 bytes.
        return DW_DEFAULT_WORDS
    n = int(argv[1], 10)          # LDR-07: the address is hex, the LENGTH is decimal
    if n < 0:
        raise ValueError("negative length")
    return n


def _dw_body(argv):
    return DW_LINE * math.ceil(_dw_words(argv) / 4)


# family -> (body function, sample count behind it, ends with the prompt)
MODELS = {
    "DW":   (_dw_body,          91, True),
    "EW":   (lambda a: 0,       10, True),
    "EB":   (lambda a: 0,        1, True),
    "Y":    (lambda a: 23,       6, True),
    "PHYR": (lambda a: 68,       5, True),
    # 79 and not 81: the fitted residual is `bytes - len(cmd)` and it already
    # contains the two-byte echo tail. For every family that ends at the prompt
    # the residual is body + 11; FLR has no prompt, so its residual is body + 2.
    # Writing 81 here made the FLR fixture predict 106 against a measured 104 --
    # caught by control C2 on the first run of this file, which is the whole
    # reason the controls run before anything is reported.
    "FLR":  (lambda a: 79,       6, False),
}

UNMODELLED = {
    "DB":    "one sample; the header row and the per-row format are not separable from it",
    "J":     "two samples of 1779, but that is the booted image speaking, not the command",
    "MDIOR": "one sample, and the length depends on how many PHY addresses answer",
}

# Fixtures: every one is a real capture, named. The self-test is these.
FIXTURES = [
    # (command, bytes, expected state, capture)
    ("DW 8040EB40 32", 401, "OK",              "bench/2026-08-25/H0b.log"),
    ("DW 8040DBC0 1",   71, "OK",              "bench/2026-08-25/A0.log"),
    ("DW 80000000 8",  118, "OK",              "bench/2026-08-25/H0c.log"),
    ("DW 80A00000 8",  118, "OK",              "bench/2026-08-25/H0d-a.log"),
    ("DW BB804128 8",  118, "OK",              "bench/2026-08-25/E13-pos1-wan.log"),
    ("DW 81000400 16", 213, "OK",              "bench/2026-08-24b/C7a-rb.log"),
    ("EW 81000000 DEADBEEF CAFEBABE", 40, "OK", "bench/2026-08-24/C1.log"),
    ("EW 81000102 11111111",  31, "OK",        "bench/2026-08-24/C3a.log"),
    ("EB 81000200 41 42 43",  31, "OK",        "bench/2026-08-24/C4a.log"),
    ("Y",                     35, "OK",        "bench/2026-08-24c/G8pre-y0.log"),
    ("PHYR 1 5",              87, "OK",        "bench/2026-08-24b/E12b.log"),
    ("PHYR 0 1",              87, "OK",        "bench/2026-08-24b/E12c.log"),
    ("FLR 80A00000 000000 100", 104, "OK",     "bench/2026-08-24c/G8pre-flr0.log"),
    # The bare `DW`.  量 2026-09-19 (seating 28): three captures, all 69 bytes.
    # In the table so that `C2` -- the loop that classifies every fixture --
    # walks the bare path too, which is the control the CORPUS should not have
    # had to provide.  ⚠️ n=3 and all three are from one seating.
    ("DW 80000000",           69, "OK",         "bench/2026-09-19b/X2-dw-80000000.log"),
    ("DW B8010000 4",         71, "OK",         "bench/2026-09-19b/X5-cpublk-a.log"),
    ("DW 8040DCE8 1",         24, "ECHO-ONLY", "bench/2026-08-24b/CONT.log"),
    # 0 bytes in 6.088599 s.  In the table so that `C2` walks the SILENT path
    # over a real capture and not only over the hand-made lengths in C11.
    ("DW 8040D4A0 1",          0, "SILENT",    "bench/2026-09-21b/F0-PROMPT.log"),
    ("DW 8040DBC0 1",         44, "UNKNOWN-COMMAND",
                                               "bench/2026-08-24/A0-reopen-control.log"),
    ("DB 81000200 4",        153, "UNMODELLED", "bench/2026-08-24/C4b.log"),
    ("J 80500000",          1789, "UNMODELLED", "bench/2026-08-24c/G6.log"),
]


def predict(cmd):
    """(bytes, derivation) for a modelled command; (None, reason) otherwise."""
    cmd = cmd.strip()
    if not cmd:
        return None, "empty command"
    argv = cmd.split()
    fam = argv[0]
    if fam in UNMODELLED:
        return None, "not modelled: " + UNMODELLED[fam]
    if fam not in MODELS:
        return None, "no model for command family %r" % fam
    body_fn, n, has_prompt = MODELS[fam]
    body = body_fn(argv[1:])
    tail = PROMPT if has_prompt else 0
    total = len(cmd) + ECHO_TAIL + body + tail
    how = "len(%r)=%d + %d echo tail + %d body + %d prompt" % (
        cmd, len(cmd), ECHO_TAIL, body, tail)
    if fam == "DW":
        # NOT a second parse of the command.  The derivation string and the
        # body must never be able to disagree about how many words the loader
        # printed; that they could is what took the sweep down on 2026-09-19,
        # and `C9c` is the control that now says they cannot.
        n_words = _dw_words(argv[1:])
        how += "   [%d words -> %d lines x %d, LDR-07 rounds UP]" % (
            n_words, math.ceil(n_words / 4), DW_LINE)
    how += "   [model fitted on n=%d captures]" % n
    return total, how


def classify(cmd, nbytes):
    """(state, predicted, delta). state is one of OK / ECHO-ONLY /
    UNKNOWN-COMMAND / SILENT / SHORT / LONG / UNMODELLED.

    SILENT-EXPLAINED is NOT produced here and cannot be: it depends on a
    neighbouring file, and this function sees one command and one length.
    `cmd_check` promotes a SILENT to it and `_explained_by` reads the evidence.
    """
    want, how = predict(cmd)
    if want is None:
        # AHEAD of the SILENT branch, and the order is the whole of it: a
        # zero-byte capture of a family this tool declined to model is still
        # UNMODELLED.  量 2026-09-21: of the seven zero-byte captures in
        # `bench/` that carry a command, six are shell commands or an
        # unmodelled family, and SILENT must not reach in and reclassify them.
        # SILENT is a statement about the size model; there is no size model
        # for those, so there is nothing for it to say.  C11c/C11d.
        return "UNMODELLED", None, None
    if nbytes == want:
        return "OK", want, 0
    if nbytes == 0:
        # NOT `SHORT`.  A truncated reply and no reply at all are different
        # events and only the first is about this model.  This branch can never
        # steal an OK: `want` for a modelled family is at least
        # len(cmd) + ECHO_TAIL, so it is never 0.
        return "SILENT", want, nbytes - want
    body_seen = nbytes - len(cmd.strip()) - ECHO_TAIL - PROMPT
    if body_seen == 0:
        return "ECHO-ONLY", want, nbytes - want
    if body_seen == UNKNOWN_BODY:
        return "UNKNOWN-COMMAND", want, nbytes - want
    return ("SHORT" if nbytes < want else "LONG"), want, nbytes - want


def _started(path):
    """The moment the instrument opened the port, or None.

    None is the conservative answer and every failure returns it -- unreadable
    file, absent field, unparseable field.  A capture whose start time cannot
    be established is never offered as anybody's predecessor, so the unknown
    case falls toward a miss rather than toward an excuse.
    """
    try:
        sw = json.load(open(path, encoding="utf-8")).get("started_wallclock")
    except Exception:                                  # noqa: BLE001
        return None
    if not sw:
        return None
    try:
        return datetime.datetime.strptime(sw, "%Y-%m-%dT%H:%M:%S%z")
    except (ValueError, TypeError):
        return None


def _explained_by(path):
    """(predecessor name, cr key) if the capture before this one on disk
    recorded that the loader prompt never came back; None otherwise.

    It reads the capture's DIRECTORY rather than the argument list the sweep
    was invoked with.  The claim is about the board, which is a property of the
    seating and not of how somebody spelled the command, so
    `check <one file>` and `check bench` must reach the same verdict about that
    file.  量 2026-09-21: the explaining capture in the real case is itself
    ESC-streamed, so the sweep skips it before classifying and it appears in no
    row list -- reading the directory is what makes it reachable at all.

    Ties in `started_wallclock` are broken by filename: arbitrary, but
    deterministic.  量 2026-09-21, 53 directories under `bench/` hold at least
    one pair of captures sharing a whole-second timestamp, so leaving the order
    of a tie unstated would leave the verdict unstated too.
    """
    ap = os.path.abspath(path)
    d = os.path.dirname(ap)
    try:
        names = os.listdir(d)
    except OSError:
        return None
    rows = []
    for n in names:
        if not n.endswith(".meta.json"):
            continue
        t = _started(os.path.join(d, n))
        if t is not None:
            rows.append((t, n))
    rows.sort()
    me = os.path.basename(ap)
    here = [i for i, r in enumerate(rows) if r[1] == me]
    if not here or here[0] == 0:
        # First in its directory: nothing on disk could explain it.  This is
        # the branch that keeps a dead port red.
        return None
    prev = rows[here[0] - 1][1]
    try:
        cr = json.load(open(os.path.join(d, prev), encoding="utf-8")).get("cr")
    except Exception:                                  # noqa: BLE001
        return None
    for k in sorted(cr or {}):
        v = cr[k]
        # `is False`, not falsy: a missing key is not a claim that the prompt
        # was absent, and neither is `None`.
        if isinstance(v, dict) and v.get("prompt_seen") is False:
            return prev, k
    return None


# --------------------------------------------------------------------------
# controls. Nothing reports until all of them pass.
# --------------------------------------------------------------------------

def controls():
    out, bad = [], 0

    def ck(name, want, got):
        nonlocal bad
        ok = (want == got)
        if not ok:
            bad += 1
        out.append("  %-4s %-52s %s" % ("ok" if ok else "FAIL", name,
                                        got if ok else "expected %r, got %r" % (want, got)))

    # 1. population. A checker with an empty fixture table passes vacuously.
    ck("C1 the fixture table is not empty", True, len(FIXTURES) >= 15)

    # 2. positive. Every fixture reaches the state it was recorded with.
    hits = sum(1 for c, b, st, _ in FIXTURES if classify(c, b)[0] == st)
    ck("C2 every fixture classifies as recorded", len(FIXTURES), hits)

    # 3. negative. One byte off must not be OK -- otherwise C2 proves nothing.
    off = [classify(c, b + 1)[0] for c, b, st, _ in FIXTURES if st == "OK"]
    ck("C3 +1 byte is never OK", True, all(s != "OK" for s in off))
    ck("C3b and it reads as LONG", True, all(s == "LONG" for s in off))

    # 4. LDR-07's carry, in both directions.
    ck("C4 DW 1..4 all predict the same",
       True, len({predict("DW 80A00000 %d" % k)[0] for k in (1, 2, 3, 4)}) == 1)
    ck("C4b DW 5 costs one more line",
       DW_LINE, predict("DW 80A00000 5")[0] - predict("DW 80A00000 4")[0])
    # Same command length on both sides, or this measures the decimal digits of
    # the length argument instead of the number of lines. (It did, on the first
    # run: 142 against an expected 141.)
    ck("C4c DW 10 prints three lines, DW 04 one",
       2 * DW_LINE, predict("DW 80A00000 10")[0] - predict("DW 80A00000 04")[0])

    # 5/6. The two named states are reachable and distinct from a miss.
    ck("C5 a body of 0 reads ECHO-ONLY", "ECHO-ONLY", classify("DW 8040DCE8 1", 24)[0])
    ck("C6 a body of 20 reads UNKNOWN-COMMAND",
       "UNKNOWN-COMMAND", classify("DW 8040DBC0 1", 44)[0])

    # 7. Declining to model is not a hit.
    ck("C7 DB is UNMODELLED, not OK", "UNMODELLED", classify("DB 81000200 4", 153)[0])
    ck("C7b J is UNMODELLED, not OK", "UNMODELLED", classify("J 80500000", 1789)[0])

    # 8. THE ONE THAT MOTIVATED THE TOOL. `DW 81000400 16` is fourteen
    #    characters; on 2026-08-25 a person counted fifteen and block 3
    #    predicted 214 against a measured 213.
    ck("C8 'DW 81000400 16' is 14 chars, so 213 and not 214",
       213, predict("DW 81000400 16")[0])

    # 9. THE BARE `DW`, AND IT GOES THROUGH `predict` ON PURPOSE.
    #    🔴 2026-09-19: `_dw_body` knew the default and `predict` did not.  A
    #    control written against the helper would have been green while `check`
    #    over bench/ crashed on its first bare-DW capture.  This one calls the
    #    function that crashed.
    ck("C9 a bare 'DW 80000000' predicts 69", 69, predict("DW 80000000")[0])
    # 9b. and the 4 is DERIVED rather than assumed: the only difference between
    #     the two commands is the echo of ` 4`, so the BODIES are identical.
    #     量 over the whole corpus 2026-09-19 -- three bare-DW captures at 69,
    #     fifty-eight `DW <addr> 4` at 71, command lengths 11 and 13.
    ck("C9b ' 4' costs exactly its own two characters",
       len(" 4"), predict("DW 80000000 4")[0] - predict("DW 80000000")[0])
    # 9c. one source of truth, stated as a property rather than as a number:
    #     whatever `_dw_words` answers, the derivation string must say the same.
    #     Re-introduce an independent parse that differs and this fires.
    ck("C9c the derivation never disagrees with the body", True,
       all(("[%d words" % _dw_words(c.split()[1:])) in predict(c)[1]
           for c in ("DW 80000000", "DW 80000000 4", "DW 80A00000 137",
                     "DW 8040DBC0 1")))

    # 10. A command the model cannot parse must RAISE here, because `cmd_check`
    #     catches it and reports the row.  Pinning that it raises is what keeps
    #     that `except` reachable instead of decorative -- 量 2026-09-19, before
    #     it existed, three captures took a 516-capture sweep down.
    def _raises(cmd):
        try:
            classify(cmd, 69)
        except Exception:                          # noqa: BLE001
            return True
        return False
    ck("C10 'DW' with no address raises, it does not classify",
       True, _raises("DW"))
    ck("C10b and a negative length raises too", True, _raises("DW 80000000 -1"))
    # The negative control on C10: a parseable command must NOT raise, or C10
    # is passing because everything raises.
    ck("C10c a good command does not raise", False, _raises("DW 80000000 4"))

    # 11. SILENT, and the controls that stop it eating its neighbours.
    #     Until 2026-09-21 a zero-byte capture read SHORT, which put "the reply
    #     was cut off" and "nothing came back" in one bucket -- and only the
    #     first of those is evidence about the size model.
    ck("C11 zero bytes reads SILENT, not SHORT",
       "SILENT", classify("DW 8040D4A0 1", 0)[0])
    # 11b. the negative control on C11: one byte is not zero bytes, and a
    #      genuinely truncated reply must still be the miss it always was.
    #      Without this, C11 would pass on a build that called everything
    #      SILENT.
    ck("C11b a truncated reply is still SHORT",
       "SHORT", classify("DW 8040D4A0 1", 70)[0])
    # 11c/d. the ORDER inside `classify`, as cases rather than as a comment:
    #      an unmodelled family with 0 bytes stays UNMODELLED.  Move the SILENT
    #      branch above the `want is None` test and both of these fire.
    ck("C11c zero bytes on an unmodelled family stays UNMODELLED",
       "UNMODELLED", classify("J 80500000", 0)[0])
    ck("C11d and on a shell command too",
       "UNMODELLED", classify("echo RLXFW-PROBE-C", 0)[0])
    # 11e. SILENT-EXPLAINED is not reachable from here, and saying so is the
    #      point: this function cannot see a neighbouring file, so a build that
    #      returned it from `classify` would be deciding the question with no
    #      evidence in hand.
    ck("C11e classify never returns SILENT-EXPLAINED", True,
       all(classify(c, b)[0] != "SILENT-EXPLAINED"
           for c, b, _, _ in FIXTURES))

    return out, bad


# --------------------------------------------------------------------------

def cmd_predict(args):
    for c in args.command:
        want, how = predict(c)
        if want is None:
            print("%-40s  --      %s" % (c, how))
        else:
            print("%-40s  %6d  %s" % (c, want, how))
    return 0


def cmd_check(args):
    metas = []
    for p in args.path:
        if os.path.isdir(p):
            metas += sorted(glob.glob(os.path.join(p, "**", "*.meta.json"),
                                      recursive=True))
        else:
            metas.append(p)
    if not metas:
        print("no capture metadata under: %s" % " ".join(args.path), file=sys.stderr)
        return 2

    tally = {}
    rows = []
    notes = {}
    skipped_esc = 0
    for p in metas:
        try:
            m = json.load(open(p, encoding="utf-8"))
        except Exception as e:                    # noqa: BLE001
            # The message goes in the `sent` column, which is printed with %s.
            # It used to go in `delta`, which is printed with %+d -- so THIS
            # branch, the one that exists to report an unusable capture, was
            # the one that crashed the tool with a TypeError before it could
            # print anything.  量 2026-08-25: `reply-size.py check` over a
            # directory of `.log` files (none of them JSON) died on the first
            # file instead of reporting 26 UNREADABLE rows.  Same defect class
            # as `hazlint` 1.0's K4 -- a control that could not fire.
            rows.append((p, ("%s: %s" % (type(e).__name__, e))[:34],
                         None, "UNREADABLE", None, None))
            tally["UNREADABLE"] = tally.get("UNREADABLE", 0) + 1
            continue
        sent = (m.get("sent") or "").strip()
        esc = (m.get("esc_seconds") or 0) + (m.get("esc_after_seconds") or 0)
        if esc:
            # An ESC-streaming capture holds boot text as well as the reply, so
            # its byte count is not this model's to predict. Counted, not hidden.
            skipped_esc += 1
            continue
        if not sent:
            tally["NO-COMMAND"] = tally.get("NO-COMMAND", 0) + 1
            continue
        try:
            st, want, delta = classify(sent, m.get("bytes"))
        except Exception as e:                    # noqa: BLE001
            # 🔴 2026-09-19: THIS BRANCH DID NOT EXIST, and three captures whose
            # command the model could not parse took the whole sweep down --
            # 516 DW captures on disk and not one of them classified.  That is
            # this file's own S5 repair happening a second time one layer up:
            # there, the branch that reports an unusable CAPTURE could not
            # print; here, there was no branch at all for an unusable COMMAND.
            # It is a miss and never an UNMODELLED.  UNMODELLED is a declared
            # decision not to model a family and is not counted against the
            # sweep -- a parse failure must not be able to hide there.
            st, want, delta = "UNPARSEABLE", None, None
            sent = ("%s [%s]" % (sent, type(e).__name__))[:34]
        if st == "SILENT":
            # The one classification made from outside the capture's own file.
            # A promotion and never a demotion: a SILENT that nothing on disk
            # accounts for stays SILENT and stays a miss.
            ex = _explained_by(p)
            if ex:
                st = "SILENT-EXPLAINED"
                notes[p] = "   <- %s recorded cr.%s.prompt_seen=false" % ex
        tally[st] = tally.get(st, 0) + 1
        rows.append((p, sent, m.get("bytes"), st, want, delta))

    for p, sent, got, st, want, delta in rows:
        if st in ("OK",) and not args.all:
            continue
        # `isinstance` and not `delta in (None, 0)`: the second half of the
        # repair above. A row that carries anything but an int here must not be
        # able to take the printer down -- a reporter that dies on the row it
        # was written to report is worse than one that says nothing.
        d = " (%+d)" % delta if isinstance(delta, int) and delta else ""
        print("  %-14s %-34s got %-6s want %-6s%s   %s%s" % (
            st, sent, got, "--" if want is None else want, d, p,
            notes.get(p, "")))

    print()
    print("  captures with a command and no ESC stream: %d" % sum(tally.values()))
    for k in sorted(tally):
        print("    %-16s %d" % (k, tally[k]))
    if skipped_esc:
        print("    %-16s %d   (boot text in the same capture -- out of model)"
              % ("ESC-STREAMED", skipped_esc))

    # The population control for THIS run: a sweep that looked at nothing must
    # not report zero misses.
    # UNREADABLE is excluded, and that is a correction rather than a tidy-up.
    # A file the tool could not open was not modelled by anything -- counting it
    # here inflated the population figure this project quotes (`121 modelled`)
    # with captures that were never examined. 量 2026-08-25: two files in, one
    # of them unreadable, and the tool printed `2 modelled`.
    # The exit code was never wrong -- an UNREADABLE row is a miss and forces
    # exit 1 either way -- so this changes the number, not the verdict.
    modelled = sum(v for k, v in tally.items()
                   if k not in ("UNMODELLED", "NO-COMMAND", "UNREADABLE",
                                "UNPARSEABLE"))
    if modelled == 0:
        print("\nRESULT: refused -- 0 modelled captures were examined, so a clean"
              " result would mean nothing")
        return 2
    # SILENT is here and SILENT-EXPLAINED is not, which is the whole of it:
    # silence is a miss until something already on disk accounts for it.
    # Both count toward `modelled` above, and that is deliberate rather than an
    # oversight -- the family WAS modelled and a number WAS predicted; what the
    # capture did not do is come back.
    misses = (tally.get("SHORT", 0) + tally.get("LONG", 0)
              + tally.get("SILENT", 0)
              + tally.get("UNREADABLE", 0) + tally.get("UNPARSEABLE", 0))
    if misses:
        print("\nRESULT: %d modelled, %d unexplained" % (modelled, misses))
        return 1
    print("\nRESULT: %d modelled, 0 unexplained" % modelled)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode")

    p = sub.add_parser("predict", help="bytes the loader will send back")
    p.add_argument("command", nargs="+")
    p.set_defaults(fn=cmd_predict)

    p = sub.add_parser("check", help="classify captures against the model")
    p.add_argument("path", nargs="+")
    p.add_argument("--all", action="store_true", help="print the OK rows too")
    p.set_defaults(fn=cmd_check)

    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and stop")
    args = ap.parse_args()

    if args.self_test:
        out, bad = controls()
        print("=== reply-size.py controls ===")
        print("\n".join(out))
        print()
        print("RESULT: %d passed, %d failed" % (len(out) - bad, bad))
        return 1 if bad else 0

    # Controls first, always. A tool that reports on a file before proving it
    # can fail is a tool reporting its own opinion.
    out, bad = controls()
    if bad:
        print("=== reply-size.py controls ===", file=sys.stderr)
        print("\n".join(out), file=sys.stderr)
        print("\nREFUSING to report: %d control(s) failed" % bad, file=sys.stderr)
        return 2

    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
