#!/usr/bin/env python3
"""Predict a boot capture's byte count, and check the model against every
capture this repository already holds.

WHY THIS EXISTS
---------------
Seven images have had their boot-capture length predicted before power and hit
exactly -- 869, 1029, 1069, 1184, 1318, 1424, 1637.  Every one of those seven
was arithmetic done BY HAND in the card.  量 2026-09-17: no tool in `tools/`
computes it, and `rlxfw-marks.py` -- the one that owns the marks -- contains no
byte arithmetic at all.

The eighty-first segment's own closing lesson was that *recording a conclusion
without the re-runnable command that produced it is not recording it*.  This is
that command.

THE MODEL
---------
    boot_bytes = CONST + SUM over boot marks of
                     8 + len(tag)      for rlxfw_mark(tag)
                    17 + len(tag)      for rlxfw_markx(tag, v)
                 + varwidth_excess     (vendor `%x` fields; see below)

`rlxfw-mark.h:44-51` with `rlxfw_mark.c:85-114`: the macro emits
`"RLXFW-" tag "\\n"` as one .rodata literal and `rlxfw_puts` writes `\\r`
BEFORE the `\\n`, so a bare mark is `6 + len(tag) + 2`.  `rlxfw_puts_hex` adds
`=` and eight upper-case hex digits, unconditionally zero-padded -- the loop is
`for (i = 28; i >= 0; i -= 4)` -- so a value mark is `6 + len(tag) + 1 + 8 + 2`.

CONST is everything that is not a mark: the loader's four lines and the jump
echo, the vendor NIC driver's `panic_printk` banner, and the userspace tail.

🔴 THE CONSTANT IS MEASURED HERE, NOT ASSUMED -- AND IT IS NOT ONE NUMBER.
`check` recomputes it from every committed boot capture independently and
requires each one to land on a value this file DECLARES, with the console
configuration that owns it named beside it.  量 2026-09-21 13:40: **710 on
111 quiet captures** spanning ten distinct totals (869, 1029, 1069, 1184, 1318,
1424, 1637, 1759, 1855, 1874) and **6541 on 5 loud ones** over four (7705, 7714,
7716, 7717), with each mark line's own length asserted against the model as it
goes.  ⚠️ Those counts are a timestamped snapshot and nothing asserts them: a
seating was writing into `bench/` while this was being fixed and the corpus
grew from 115 to 116 mid-session.  Every case below computes its population;
none of them carries a corpus count.  If a future image changes
`/init` -- which `docs/mfgtest.md` says a manufacturing image would -- that
number moves and this check is what says so.

⚠️ A DECLARED TABLE IS WEAKER THAN ONE VALUE, and the weakening is deliberate,
so it is fenced on both sides rather than left open.  K2 still names every
capture that lands outside the table.  K6 requires every declared constant to
be USED by at least one capture, so the table cannot accrete dead entries.
🔴 What neither can do is stop somebody adding a row instead of understanding a
difference -- a new row is indistinguishable, to a checker, from a new console
configuration.  That is a review question, and saying so is the honest limit of
this design.

THE VARIABLE-WIDTH VENDOR FIELD
-------------------------------
🔴 A loud image's non-mark remainder is NOT constant between boots of the SAME
image, and the cause is a field whose printed width depends on a value read
from hardware.  讀 `drivers/net/wireless/rtl8192cd/8192cd_osdep.c:6384` and
`:6386` -- the `rtl8192cd/` directory is the one that BUILDS on this board, and
`CLAUDE.md`'s fifteenth update records the session that read past that exact
distinction; the identical pair in `rtl8192e/` does not reach the image:

    printk("<%s>LZQ: before read tmpReg[0x%x] \\n", __FUNCTION__,
           RTL_R32(GPIO_PIN_CTRL));

`%x`, no width, on a live register read.  量 2026-09-21 over the five loud
captures: twelve occurrences each, **60 in total, 44 rendering two hex digits
(`0x2e`) and 16 rendering one (`0xe`)**, and the raw constants 6541 / 6550 /
6552 / 6553 all reduce to **6541**.

🟢 THE ZERO POINT IS OBSERVED, NOT HYPOTHETICAL, and that arrived by accident
while this was being fixed.  `bench/2026-09-21d/C0-boot.log` renders ALL TWELVE
fields narrow, so its excess is 0 and its RAW constant is 6541 -- the value the
other four are normalised onto is a capture that exists, which is a much better
thing to subtract towards than an arithmetic fiction.

🟢 Nothing else in those files varies in width, and that was CHECKED rather
than assumed: canonicalise the printk timestamps and this one field and all
five captures collapse to **6,637 bytes**, the only residue being `2542k`
against `2543k` of kernel code in `s32a` -- a different image, same width, no
effect on any length.

🔴 THIS IS NOT AN ESC ARTEFACT, and the older explanation in the next section
does NOT transfer.  The `307`/`309` pair below is two `*reboot*.log` files
differing by the two bytes of one echoed `^[`, and that reading is correct for
those files.  量 on all five loud captures: **zero `0x1b` bytes and zero
literal `^[`** in every one of them.

WHICH FILES ARE BOOT CAPTURES
-----------------------------
🔴 A file matching the glob is not necessarily one, and finding that out cost a
red CI run.  `bench/**/*boot*.log` also matches `*reboot*.log`, and 量
2026-09-19 seating 28 is the first seating in this repository to produce any:
`bench/2026-09-19b/M0-reboot.log` and `C62-reboot3.log` are `busybox reboot -f`
captures that stop at the LOADER prompt (`--until "RealTek>"` in their
`.meta.json`), carry the shutdown path's single `N-NDSTOP` mark, and never
enter Linux.  Their non-mark remainder is console echo, not the boot constant:
**307 and 309, two values differing by the two bytes of one echoed `^[`** from
the `--esc-after` spam racing the reset.  K2 read that as *the constant now has
three values*.  It does not; two of the three files were never boot captures.

⚠️ The glob had matched a `*reboot*.log` one commit earlier without failing,
because that one carried no `RLXFW-` at all and was dropped by the content
filter.  **A latent selection defect becomes reachable and fires on different
commits**, so the commit that went red is not the commit that introduced it.

The gate is therefore a PROPERTY and not a filename.  `RLXFW-B10` is emitted
immediately before `init_post()` branches into `/sbin/init`, so a capture
carrying it reached the end of the boot path.  量 2026-09-21: present in all
116 real boot captures, absent from both reboot captures.  A truncated or
aborted boot is excluded by the same test, which is the point.

K5 is the control on that gate, and 🔴 **its fixture is SYNTHETIC on purpose,
both halves, differing in exactly one line**.  A control that asserted *the
corpus contains at least one non-boot file* would go red the day somebody
deletes those two logs -- a hardcoded corpus property, the very class this
selection fix exists to remove.  So K5 builds its own two-file corpus in a temp
directory, where the halves are identical apart from the `RLXFW-B10` line, and
requires the gate to accept one and reject the other.  Because that is the only
difference, the assertion is the gate's SPECIFICATION and not a resemblance;
because the line is written as a literal rather than built from `BOOT_GATE`, a
wrong gate makes the POSITIVE half fail and K5 says which way it broke.  That
real boot captures are accepted is K1's and K2's job, over 116 of them.  The
real corpus's rejects are then PRINTED as an observation with no assertion
attached: assert the property, report the count.

WHAT IT DOES NOT DO
-------------------
It does not decide which marks are on the BOOT path.  A mark inside a verb
fires when the verb is typed and belongs in no boot budget.  That is a fact
about reachability, and a regex over source cannot settle it -- so the boot
set is taken from the newest MEASURED capture, and any tag in the sources that
is not in it is reported as unclassified rather than guessed at.  A new mark
therefore makes this tool ask a question instead of inventing an answer.

⚠️ It does not count a `RLXFW-` that is not at the start of a line, and 量
2026-09-21 every one of the 116 captures holds exactly one such -- the
difference between `blob.count(b"RLXFW-")` and the parsed mark count is exactly
1 on 116 of 116 -- and it is `/init`'s own
`rlxfw: init running, RLXFW-R3-RUNG1-OK`, **byte-identical on all 116**.  It is
prose, it is part of the constant, and it is the same in quiet and loud
captures.  This was checked rather than assumed, because a mark swallowed by a
printk prefix would look exactly like a constant that moved, and clearing the
loud captures of that was the first thing this fix had to do.

⚠️ And the glob is still wrong in the OTHER direction, which this tool does not
fix and must not be read as covering.  量 2026-09-19, sweeping all 1,627
`bench/**/*.log`: **five** captures carry `RLXFW-B10` and are not named
`*boot*.log` -- `bench/2026-08-30c/V-3.log`, `bench/2026-08-31/W-3.log`,
`bench/2026-08-31b/X-3.log`, `bench/2026-09-01/T-3.log` (all 849 bytes,
const 710, so they would join the population harmlessly) and
`bench/2026-08-30b/L3.log` (6,459 bytes, const **6,320**, a verbose-printk
image).  **Widening the glob naively re-reds K2 on that last one**, and
🔴 the normalisation above does NOT rescue it: 量 2026-09-21, L3's twelve
`tmpReg` occurrences are ALL one digit, so its excess is 0 and its normalised
constant is 6,320 unchanged.  It is an eleven-mark image from a third console
configuration, and whether that is the same population is a question for
`SPEC.md`'s owner rather than for a CI repair.  The population's outer edge is
therefore still a naming convention, and saying so is the honest scope limit.
"""

import glob
import os
import re
import shutil
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30")

MARK_LINE = re.compile(rb"^RLXFW-([A-Za-z0-9_-]+?)(=([0-9A-F]{8}))?\r\n$")
MARK_CALL = re.compile(r'rlxfw_(mark|markx)\(\s*"([A-Za-z0-9_-]+)"')

#: The one vendor field in a boot capture whose PRINTED WIDTH is not fixed.
#: 讀 `drivers/net/wireless/rtl8192cd/8192cd_osdep.c:6384` and `:6386` --
#: `printk("<%s>LZQ: before read tmpReg[0x%x] \n", __FUNCTION__,
#: RTL_R32(GPIO_PIN_CTRL))`.  See `varwidth_excess`.
VARWIDTH_FIELD = re.compile(rb"tmpReg\[0x([0-9a-fA-F]+)\]")

#: Every non-mark constant this repository has MEASURED, keyed by the
#: NORMALISED value, each with the console configuration that owns it.
#: K2 requires every capture to land on a key here; K6 requires every key to be
#: reached by at least one capture, so this table cannot accrete dead rows.
#: 🔴 Adding a row is a claim that a new console configuration exists.  It is
#: not a way to make K2 green, and no checker can tell the two apart.
DECLARED_CONSTS = {
    710: "quiet console, CONFIG_PRINTK=n -- the default variant.  量 111 "
         "captures over ten distinct totals, 2026-09-02 to 2026-09-21",
    6541: "loud console, CONFIG_PRINTK=y -- the `loud` variant, "
          "`set@loud CONFIG_PRINTK n y` at config/rlxfw-kernel.delta:138.  "
          "量 5 captures over two images, first on silicon 2026-09-21 "
          "(RLXFW-ID0=F179CF21 on 3, 84385D91 on 2) -- which is what makes "
          "it a property of the console configuration and not of one build",
}

#: The population floor.  A sweep that finds three captures and agrees with
#: itself proves nothing.
MIN_CAPTURES = 40
#: The mark that says the boot path finished.  See WHICH FILES ARE BOOT
#: CAPTURES above -- this is the selection, and it is content, not a filename.
BOOT_GATE = "B10"


def cost(tag, valued):
    return (17 if valued else 8) + len(tag)


def varwidth_excess(blob):
    """-> the bytes this capture spends on variable-width VENDOR fields above
    their narrowest rendering.

    WHAT IT IS: a term in the model.  `8192cd_osdep.c:6384` prints a live
    register with `%x` and no width, so `RTL_R32(GPIO_PIN_CTRL)` renders
    `0x2e` on one boot and `0xe` on the next -- one byte of difference that
    belongs to the VALUE READ FROM HARDWARE and not to the image.  量
    2026-09-21: 60 occurrences over the five loud captures, 44 two-digit and
    16 one-digit, and the raw constants 6541 / 6550 / 6552 / 6553 all reduce
    to 6541 -- 6541 being a capture that exists (`bench/2026-09-21d/C0-boot.log`
    renders all twelve narrow), not an arithmetic fiction.

    WHAT IT IS NOT: a tolerance.  It does not permit a difference of up to N
    bytes and it has no slack in it.  It subtracts a quantity COUNTED in this
    very capture, so one byte of difference from any other source still moves
    the constant and still goes red.  K7 is the control that it is doing work
    at all, and K2 is what still fires if it is doing the wrong work.

    🟢 THE CONTRAST IS THE POINT.  rlxfw's own `rlxfw_markx` zero-pads its
    value to eight hex digits unconditionally -- `for (i = 28; i >= 0; i -= 4)`
    -- precisely so that a mark's length never depends on what the mark is
    printing.  The vendor's `%x` does depend on it.  That difference is why a
    boot capture's length is predictable at all, and why the constant needed a
    term the moment a vendor printk reached the console.

    Written as a sum of `len(digits) - 1` rather than as a count of two-digit
    occurrences.  The model term is EXCESS WIDTH; the two are equal only
    because 量 every occurrence in the corpus today is one or two digits
    (histogram `{1: 16, 2: 44}`, printed by K7).  A three-digit value would be
    handled correctly here and would be visible there.
    """
    return sum(len(h) - 1 for h in VARWIDTH_FIELD.findall(blob))


def raw_const(blob, marks):
    """The non-mark remainder with NOTHING subtracted.

    Kept reachable on its own because K7 needs it: a normalisation you cannot
    switch off is one you cannot show is load-bearing.
    """
    return len(blob) - sum(cost(t, v) for t, v in marks)


def normalised_const(blob, marks):
    """`raw_const` with the vendor's variable-width field taken out."""
    return raw_const(blob, marks) - varwidth_excess(blob)


def captures(root=None):
    """-> (accepted, rejected), each a list of (path, blob, marks).

    `root` is a parameter rather than a read of the global so that K5 can
    drive THIS function over a synthetic corpus.  🔴 A control that reached
    past the entry point into an inner predicate would not be a control on the
    sweep: the other CI failure of 2026-09-19 was exactly that shape, where
    `reply-size.py` grew a bare-`DW` default inside `_dw_body` while `predict`
    kept its own copy of the parse, and ten green controls sat beside a dead
    516-capture sweep.

    Nothing is dropped silently: a file the glob matched that carries marks
    but did not reach `RLXFW-B10` comes back in `rejected`.
    """
    root = ROOT if root is None else root
    accepted, rejected = [], []
    pat = os.path.join(root, "bench", "**", "*boot*.log")
    for p in sorted(glob.glob(pat, recursive=True)):
        blob = open(p, "rb").read()
        if b"RLXFW-" not in blob:
            continue
        ms = marks_in(blob)
        if BOOT_GATE in {t for t, _v in ms}:
            accepted.append((p, blob, ms))
        else:
            rejected.append((p, blob, ms))
    return accepted, rejected


def marks_in(blob):
    """-> [(tag, valued)] in wire order, and the line's own length is
    asserted against the model rather than taken on faith."""
    out = []
    for line in blob.splitlines(keepends=True):
        m = MARK_LINE.match(line)
        if m:
            tag = m.group(1).decode()
            valued = m.group(2) is not None
            if len(line) != cost(tag, valued):
                raise AssertionError(
                    "the model disagrees with a real line: %r is %d bytes, "
                    "model says %d" % (line, len(line), cost(tag, valued)))
            out.append((tag, valued))
    return out


def source_marks():
    """Every mark the sources can emit, with its shape."""
    out = {}
    for path in glob.glob(os.path.join(SRC, "**", "*.c"), recursive=True):
        text = open(path, encoding="utf-8", errors="replace").read()
        for kind, tag in MARK_CALL.findall(text):
            out[tag] = (kind == "markx", os.path.relpath(path, SRC))
    return out


#: K5's fixture, and BOTH halves are built rather than found.  The base is the
#: shape of a `*reboot*.log`: it carries `RLXFW-` so the content filter admits
#: it, a well-formed `N-NDSTOP` so `marks_in`'s length assertion is exercised,
#: and an `ENGOFF` that is NOT at line start so the anchored regex misses it
#: exactly as it does on the real files.
_FIXTURE_BASE = (b"busybox reboot -f\r\n"
                 b"^[^[^[RLXFW-N-ENGOFF\r\n"
                 b"RLXFW-N-NDSTOP\r\n"
                 b"\r\nBooting...\r\n"
                 b"---RealTek(RTL8196E) v1.3 [16bit](400MHz)\n\r"
                 b"---Ethernet init Okay!\n\r<RealTek>")

#: \U0001f534 A LITERAL, deliberately NOT built from `BOOT_GATE`.  Derive it and
#: changing the gate would change the fixture with it, so K5 could not see a
#: wrong gate at all -- which is the circularity a synthetic fixture is always
#: one step from.  As a literal, `BOOT_GATE = "B00"` makes the POSITIVE half be
#: rejected and K5 reports that, instead of the previous version's "there is no
#: accepted capture to copy", which was true and told a reader nothing.
_FIXTURE_GATE_LINE = b"RLXFW-B10\r\n"

#: The two halves differ in EXACTLY that one line and in nothing else, so the
#: assertion below is precisely the gate's specification rather than a
#: resemblance.  That REAL boot captures are accepted is K1's and K2's job,
#: over 116 of them; this case is about the mechanism.
FIXTURE_REJECT = _FIXTURE_BASE
FIXTURE_ACCEPT = _FIXTURE_BASE.replace(b"RLXFW-N-NDSTOP\r\n",
                                       b"RLXFW-N-NDSTOP\r\n" + _FIXTURE_GATE_LINE,
                                       1)


def gate_control():
    """Drive `captures()` over a synthetic two-file corpus.  -> (ok, detail).

    `captures()` and not an inner predicate: the OTHER CI failure of
    2026-09-19 was exactly that shape -- `reply-size.py` grew a bare-`DW`
    default inside `_dw_body` while `predict` kept its own copy of the parse,
    and ten green controls sat beside a dead 516-capture sweep.  A control
    that exercises a helper does not exercise its caller.
    """
    tmp = tempfile.mkdtemp(prefix="bootbytes-gate-")
    try:
        d = os.path.join(tmp, "bench", "fixture")
        os.makedirs(d)
        with open(os.path.join(d, "keep-boot.log"), "wb") as fh:
            fh.write(FIXTURE_ACCEPT)
        with open(os.path.join(d, "drop-reboot.log"), "wb") as fh:
            fh.write(FIXTURE_REJECT)
        acc, rej = captures(root=tmp)
        got_a = sorted(os.path.basename(p) for p, _b, _m in acc)
        got_r = sorted(os.path.basename(p) for p, _b, _m in rej)
        # The one-variable claim, asserted rather than left to the eye: if a
        # future edit makes the halves differ in anything else, this case
        # stops being about the gate and must say so.
        one_var = (len(FIXTURE_ACCEPT) - len(FIXTURE_REJECT)
                   == len(_FIXTURE_GATE_LINE))
        ok = (got_a == ["keep-boot.log"] and got_r == ["drop-reboot.log"]
              and one_var)
        return ok, ("accepted %s, rejected %s, halves differ by one line: %s"
                    % (got_a, got_r, one_var))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check():
    accepted, rejected = captures()
    consts, n, biggest = {}, 0, 0
    # K7's partition and its width histogram.  🔴 The partition is defined by
    # the PRESENCE of the vendor field, never by its width and never by the
    # constant a capture lands on -- otherwise K7 would be reasoning about the
    # normalisation using the normalisation's own output.
    varwidth, widths = [], {}
    for path, blob, ms in accepted:
        consts.setdefault(normalised_const(blob, ms),
                          []).append((len(blob), path))
        if VARWIDTH_FIELD.search(blob):
            varwidth.append((path, blob, ms))
        for h in VARWIDTH_FIELD.findall(blob):
            widths[len(h)] = widths.get(len(h), 0) + 1
        n += 1
        biggest = max(biggest, len(ms))

    ok = fails = 0

    good = n >= MIN_CAPTURES
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K1",
                              "the capture corpus is a population (%d boot "
                              "captures, floor %d)" % (n, MIN_CAPTURES)))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K2 asserts MEMBERSHIP OF A DECLARED TABLE, not a single value.  量
    # 2026-09-21: the loud variant's non-mark remainder is 6541 and the quiet
    # one's is 710, and no arithmetic relates them -- `CONFIG_PRINTK=y` adds
    # whole kernel messages, not a widened field.  A one-value assertion could
    # only have been kept by excluding the loud captures, which would be
    # choosing the population to fit the claim.
    undeclared = {k: v for k, v in consts.items() if k not in DECLARED_CONSTS}
    good = not undeclared
    totals = sorted({t for v in consts.values() for t, _ in v})
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K2",
                              "every capture's normalised constant is "
                              "declared: %s, over totals %s"
                              % ({k: len(v) for k, v in sorted(consts.items())},
                                 totals)
                              if good else
                              "a normalised constant is NOT declared: %s"
                              % {k: len(v)
                                 for k, v in sorted(undeclared.items())}))
    if not good:
        for k in sorted(undeclared):
            for total, path in undeclared[k]:
                print("        const %-6d %-46s %d bytes"
                      % (k, os.path.relpath(path, ROOT), total))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K3 is the control that K1 and K2 cannot be.  Both would pass on a model
    # that is wrong in a way every capture shares.  This one asserts the model
    # reproduces a number written down INDEPENDENTLY, in a frozen card.
    want = 1637
    hit = [t for t in totals if t == want]
    print("  %s  %-10s %s" % ("ok  " if hit else "FAIL", "K3",
                              "the corpus contains the 1,637 that "
                              "bench/2026-09-10 predicted before power"
                              if hit else
                              "1,637 is not among the totals: %s" % totals))
    ok, fails = (ok + 1, fails) if hit else (ok, fails + 1)

    good = biggest >= 50
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K4",
                              "the mark parser reaches a full image "
                              "(%d marks in the richest capture)" % biggest))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K5 is the control on the SELECTION, which K1-K4 structurally cannot be:
    # every one of them reads the population `captures()` hands it and cannot
    # see a file it wrongly admitted.  量 2026-09-19, that is exactly how K2
    # went red -- on two `*reboot*.log` files that never entered Linux.
    good, detail = gate_control()
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K5",
                              "the RLXFW-%s gate discriminates on a synthetic "
                              "fixture (%s)" % (BOOT_GATE, detail)
                              if good else
                              "the gate did NOT discriminate on its fixture: "
                              "%s" % detail))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K6 is the OTHER direction of K2, and without it the table is a one-way
    # ratchet: K2 can only ever be repaired by adding a row, and a row that
    # stops describing anything would sit there forever reading as knowledge.
    # 🔴 If the loud captures ever leave the corpus this goes red, and the red
    # is correct -- it says *delete the row*, not *the tool is broken*.
    unused = sorted(k for k in DECLARED_CONSTS if k not in consts)
    good = not unused
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K6",
                              "every declared constant is reached by a capture "
                              "(%s)"
                              % ", ".join("%d on %d" % (k, len(consts[k]))
                                          for k in sorted(DECLARED_CONSTS))
                              if good else
                              "a declared constant is reached by NO capture: "
                              "%s -- the table has accreted a dead entry"
                              % unused))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K7: the normalisation has to be LOAD-BEARING.  A subtraction that
    # changed nothing would pass K2 and K6 and prove nothing, which is this
    # repository's own rule that a tool which cannot fail is not a tool.
    # Both halves are asserted: WITHOUT the term the partition must be more
    # than one value (there is work to do) and WITH it exactly one (the term
    # is what does that work).  Neutering `varwidth_excess` to return 0 fails
    # the second half; breaking `VARWIDTH_FIELD` empties the partition and
    # fails the first.
    raw_set = sorted({raw_const(b, m) for _p, b, m in varwidth})
    norm_set = sorted({normalised_const(b, m) for _p, b, m in varwidth})
    good = len(varwidth) > 0 and len(raw_set) > 1 and len(norm_set) == 1
    detail = ("%d capture(s) carry the field, hex-digit widths %s; WITHOUT the "
              "normalisation they give %s, WITH it %s"
              % (len(varwidth), dict(sorted(widths.items())), raw_set,
                 norm_set))
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K7",
                              "the varwidth normalisation is load-bearing: %s"
                              % detail
                              if good else
                              "the varwidth normalisation is NOT shown to be "
                              "load-bearing: %s" % detail))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # Observation, deliberately carrying NO assertion.  What the gate rejected
    # in the real corpus is worth reading -- it is how a mis-named capture
    # gets noticed -- but asserting anything about it would make this tool
    # depend on which files happen to be committed, which is the defect K5 was
    # rewritten to avoid.
    print("        observed, not asserted: the gate rejected %d of %d file(s) "
          "the glob matched" % (len(rejected), n + len(rejected)))
    for path, blob, ms in rejected:
        print("          %-44s %5d bytes, %d mark(s), no RLXFW-%s"
              % (os.path.relpath(path, ROOT), len(blob), len(ms), BOOT_GATE))

    print("%d of %d ok" % (ok, ok + fails))
    return 1 if fails else 0


def predict():
    """The boot set is the newest measured capture's; the sources are then
    diffed against it so a NEW tag is a question and not a silent zero."""
    accepted, _rejected = captures()
    newest, best = None, -1
    for path, blob, ms in accepted:
        if len(ms) > best:
            newest, best = (path, blob, ms), len(ms)
    path, blob, ms = newest
    boot = [t for t, _v in ms]
    mb = sum(cost(t, v) for t, v in ms)

    print("baseline   %s" % os.path.relpath(path, ROOT))
    print("           %d bytes = %d const + %d marks (%d marks)"
          % (len(blob), raw_const(blob, ms), mb, len(ms)))
    if varwidth_excess(blob):
        print("           of that const, %d byte(s) are the vendor's "
              "variable-width %s field"
              % (varwidth_excess(blob), VARWIDTH_FIELD.pattern.decode()))

    src = source_marks()
    unseen = sorted(t for t in src if t not in set(boot))
    print()
    print("marks in the sources that this capture does NOT carry: %d"
          % len(unseen))
    print("  These are on-demand verbs or failure-path twins unless something")
    print("  says otherwise.  A tag here that SHOULD fire at boot is the one")
    print("  thing that would make the prediction below wrong.")
    for t in unseen:
        valued, where = src[t]
        print("    %-10s %-6s %-2d bytes  %s"
              % (t, "markx" if valued else "mark", cost(t, valued), where))

    print()
    print("PREDICTION for an image whose boot path is unchanged: %d bytes"
          % len(blob))
    print("  = %d const + %d marks.  Add `8 + len(tag)` or `17 + len(tag)`"
          % (raw_const(blob, ms), mb))
    print("  for each NEW boot mark, and re-derive the const if /init changes.")
    return 0


def main(argv):
    print("bootbytes 1.2  --  boot capture length, derived not copied")
    if len(argv) > 1 and argv[1] == "predict":
        return predict()
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
