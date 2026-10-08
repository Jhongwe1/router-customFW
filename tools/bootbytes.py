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
                 + echo_excess         (the capture tool's own ESCs; see below)

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

THE ECHOED CONSOLE INPUT
------------------------
🔴 A boot capture can also hold bytes the board did not generate: the capture
tool's own `--esc-after` ESCs, reflected back.  量 2026-09-30, the first two
boots of R7's userspace (`bench/2026-09-30/R78-boot.log` and `R79-boot.log`;
4,806 and 4,337 ESCs written, per their `.meta.json`): every ESC the console
echoed came back as the two characters `^[`, and the CR the tool sent once
`--until` matched handed them all to ash as one command, which answered
`sh: <the same ESCs, raw>: not found`.  Each echoed ESC costs three bytes --
206 in R78 (618 B), 239 in R79 (717 B) -- so their raw constants, 2647 and
2746, differ by exactly 3 x 33 = 99, and without the echo both are 2029.  That
the echo is the tty rendering an input byte, and that ESCs arriving before
/init holds the console are never echoed, is 推.

`echo_excess` counts those bytes in the capture itself, two per `^[` and one
per raw 0x1b, so like `varwidth_excess` it is a term and not a tolerance.  量
2026-10-02: no other capture the gate accepts holds a single `^[` or 0x1b (174
of 176), so the term is 0 wherever it did not exist before and every earlier
verdict stands.  K8 is its control.

ASH'S REPLY TO THAT INPUT
-------------------------
🔄 2026-10-08.  This section ended on a 推: *a boot in which no ESC is echoed
before the CR would lack `sh: : not found`, 17 bytes, never captured*.  It was
captured -- R8b's armed provisioning image booted twenty times on 2026-10-07
with the same userspace as R7 and no console input -- and it is **21** bytes,
not 17, which turned CI red on `3e01e0a9` (K2: an undeclared 2008).  量 from
the bytes, echoed ESCs taken out: `R78-boot.log` ends `# ` + `\\r\\n` + `sh: :
not found\\r\\n` + `# `, `A1A-boot.log` ends at the first `# `.  The 推 counted
ash's line and missed the CR the tool sent, which the tty echoes as `\\r\\n`,
and the second prompt ash prints after its reply.  As byte multisets the two
remainders differ in exactly those 21 bytes and nothing else.

`reply_excess` counts that reply in the capture itself -- `len(REPLY)` for each
occurrence once the echoed ESCs are out -- so the R7 userspace is one declared
constant, 2008, with or without the tool's input.  K8's fixture already ended
in the reply; K8 now also requires the full and the cut shapes to normalise to
one value, and K9 is the term's control on the real corpus.  ⚠️ What it does
not model: a CR sent with no ESC before it would produce a bare prompt and no
`sh:` line (推, never captured), and would read 4 above.

A CAPTURE THAT ENDS BEFORE ITS BOOT DOES
----------------------------------------
量 2026-10-08, `bench/2026-10-08c/R02-boot.log` reads 1751: the shell's banner
and first prompt came before some daemons' lines (`FW-252`'s race), looprun's
`--boot-until` matched at that prompt, and the capture stopped 0-50 ms later.
The 257 bytes it lacks against 2008 were counted by hand against
`I02-boot.log`, the same /init booted minutes later: the end of dnsfwd's third
line with its CRLF (53), httpd's `uid=` line (75), udhcpd's two (94) and
`rlxfw: init: shell started` (35).  `CUT_SHORT` names the file; K2 leaves it
out and K10 requires it to stay what its row says.  ⚠️ K10 cannot see WHICH
bytes are missing, only that the capture is short and that output continued
past its first prompt.

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

#: The capture tool's own ESC, as the console echoes it and as ash prints it
#: back raw in `sh: ...: not found`.  See `echo_excess`.
ECHO_CARET = b"^["
ECHO_RAW = b"\x1b"

#: The image a capture booted, by its own `RLXFW-ID0=` mark line -- K7's
#: partition key.  Content, so it cannot depend on the constant it partitions.
ID0_LINE = re.compile(rb"^RLXFW-ID0=([0-9A-F]{8})\r\n", re.M)

#: Every non-mark constant this repository has MEASURED, keyed by the
#: NORMALISED value, each with the console configuration that owns it.
#: K2 requires every capture to land on a key here; K6 requires every key to be
#: reached by at least one capture, so this table cannot accrete dead rows.
#: 🔴 Adding a row is a claim that a new console configuration exists.  It is
#: not a way to make K2 green, and no checker can tell the two apart.
DECLARED_CONSTS = {
    710: "quiet console, SWCORE=y -- `quiet-swcore` since 8g, the default until "
         "then.  量 111 captures over ten distinct totals, 2026-09-02 to 2026-09-21",
    6541: "loud console, CONFIG_PRINTK=y -- the `loud` variant, "
          "`set@loud CONFIG_PRINTK n y` at config/rlxfw-kernel.delta:138.  "
          "量 5 captures over two images, first on silicon 2026-09-21 "
          "(RLXFW-ID0=F179CF21 on 3, 84385D91 on 2) -- which is what makes "
          "it a property of the console configuration and not of one build",
    778: "quiet console whose /init brings the LAN up -- recipe a2c56bc8, "
         "`p2q` (P2-2).  710 + 68: `rlxfw: lan bring-up` (21) and `rlxfw: "
         "lan up, rlx0 10.1.1.3` (30) from /init, and RLXFW-SW-UNLOCK (17), "
         "which the kernel prints while /init's first line is still going "
         "out, so the two interleave character by character and the mark "
         "never parses as one.  量 8 captures, 2026-09-23 (seating 39): the "
         "interleaving differs in every one and the total (2,117 B) does "
         "not; the card named this constant change before power.  A boot "
         "whose two lines did NOT interleave would read 761, undeclared",
    6609: "loud console with the same /init -- recipe a2c56bc8, `p2l`.  "
          "6541 + the same 68.  量 3 captures, 2026-09-23 (seating 39), "
          "e = 0 in all three",
    339: "quiet console with the vendor's switch core out of the link -- "
         "recipe 1cc05e88, `r6b10n`, R6b-8's arm II: the delta's `set@quiet,loud "
         "CONFIG_RTL_819X_SWCORE y n` since 8g (8b: `@quiet-noswcore`).  710 - "
         "371: 讀 the drop's drivers/net/Makefile:276-277 links "
         "drivers/net/rtl819x/ only under SWCORE, and that directory prints "
         "the vendor NIC driver's thirteen boot lines -- rtl_nic.c:6213 "
         "(`\\n\\n\\nProbing RTL8186 ...`, three blank lines with it), :6479 "
         "(`eth%d added`, six), :9574 (`[%s] added, mapping to`), "
         "AsicDriver/rtl865x_asicL2.c:4381 (`chip name:`) and :5899 (`NOT "
         "YET`), 371 B.  量 1 capture, 2026-09-28 "
         "(bench/2026-09-28/M1Q-boot.log): its non-mark lines are the same "
         "night's A1Q-boot.log (710, banner present) minus exactly those "
         "thirteen, none added; bench/2026-09-28/RUN-armII.md § 1 expected "
         "no `Probing RTL8186` and no `ethN added`, and its M1-VT counted 0",
    407: "quiet console with the vendor's switch core out of the link and the "
         "standard /init, which brings the LAN up and types `init` -- recipe "
         "3685a3a4, `r6b8i`, R6b-8's arm I.  339 + 68 = 778 - 371: arm II's "
         "non-mark lines plus /init's `rlxfw: lan bring-up` and `rlxfw: lan "
         "up, rlx0 10.1.1.3`, with RLXFW-SW-UNLOCK interleaved as in 778; "
         "rtl819x-switch 1.5's RLXFW-SW-INIT= line parses as a mark.  量 2 "
         "captures, 2026-09-28 (bench/2026-09-28b/I1Q-boot.log after a cold "
         "power-on, I4Q-boot.log after busybox reboot -f), 1,830 B each",
    2008: "quiet console, SWCORE=n, with R7's compiled /init, its four "
          "daemons and the bench shell -- recipe bf182de2 (`r78a`), its "
          "rebuild 0e45c61d, and R8b's armed provisioning images 75cfa588 "
          "and 6b1bde59, whose userspace is the same.  2008 = 246 + 296 + "
          "197 + 1269: the loader's and the vendor kernel's lines, the same "
          "246 bytes as the 339 and 407 captures; /init's first eight lines "
          "(the rung-1 line, `compiled PID 1 (R7)`, six `mounted`; 讀 "
          "src/init/main.c and mounts.c); the ten kernel marks "
          "RLXFW-SW-UNLOCK to RLXFW-N-NDOPEN, which interleave with those "
          "eight lines character by character so that none parses -- an "
          "exact interleaving on every capture; and the remaining /init, "
          "brokerd, httpd, dnsfwd, udhcpd and ash lines up to the first "
          "prompt.  A boot in which any of the ten parses on its own line "
          "reads less, undeclared.  🔄 Declared as 2029 from 2026-09-30 "
          "(bench/2026-09-30/R78-boot.log, R79-boot.log, 2647 and 2746 "
          "before `echo_excess`) until 2026-10-08, when the twenty armed "
          "boots of bench/2026-10-07, which carry no console input, read "
          "2008: 2029 held ash's 21-byte reply to the capture tool's input, "
          "now `reply_excess` (K9)",
}

#: Captures that end before their boot's output does, each NAMED, with the
#: declared constant its configuration reaches when the capture is whole.
#: 量 2026-10-08 (`bench/2026-10-08c/R02`, the 129th segment): the shell's
#: banner and first prompt came before httpd's line, udhcpd's two, the end of
#: dnsfwd's third and `rlxfw: init: shell started` (`FW-252`'s race);
#: looprun's `--boot-until` matched at that prompt and the capture stopped
#: 0-50 ms later, 257 bytes short of 2008 -- 1751, which is no console
#: configuration.  K2 leaves these out of the population; K10 holds each to
#: that story and goes red the day one no longer needs its row.  🔴 A row
#: names ONE file, never a pattern, and it is not a way to make K2 green for
#: a constant that moved.
CUT_SHORT = {
    "bench/2026-10-08c/R02-boot.log": 2008,
}

#: Ash's reply to the capture tool's input, as the capture reads once the
#: echoed ESCs are taken out: the tool's CR echoed, `sh: <the ESCs>: not
#: found`, and the prompt ash prints after it.  See ASH'S REPLY TO THAT INPUT.
REPLY = b"\r\nsh: : not found\r\n# "

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


def echo_excess(blob):
    """-> the bytes this capture spends reflecting the capture tool's own
    ESCs: two for each `^[` the console echoed and one for each raw 0x1b ash
    printed back.  Counted in this capture, like `varwidth_excess`, and not a
    tolerance; see THE ECHOED CONSOLE INPUT, and K8 for its control."""
    return 2 * blob.count(ECHO_CARET) + blob.count(ECHO_RAW)


def reply_excess(blob):
    """-> the bytes this capture spends on ash's reply to the capture tool's
    input: `len(REPLY)` for each occurrence of `REPLY` once the echoed ESCs
    are taken out.  Counted in this capture, like `echo_excess`, and not a
    tolerance; see ASH'S REPLY TO THAT INPUT, and K8 and K9 for its controls."""
    bare = blob.replace(ECHO_CARET, b"").replace(ECHO_RAW, b"")
    return len(REPLY) * bare.count(REPLY)


def normalised_const(blob, marks):
    """`raw_const` with the vendor's variable-width field, the echoed input
    and ash's reply to it taken out."""
    return (raw_const(blob, marks) - varwidth_excess(blob) - echo_excess(blob)
            - reply_excess(blob))


def without(term, blob, marks):
    """`normalised_const` with ONE term put back.  K7 and K8 compare against
    this, so that neither control can pass on the other term's work."""
    return normalised_const(blob, marks) + term(blob)


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


def _echo_fixture(k, full=True, extra=b""):
    """K8's fixture: a boot whose console echoed `k` ESCs, two before /init's
    first line and the rest on ash's prompt, as R78 and R79 do.  `full` ends
    after the tool's CR, with ash's `sh: <k raw ESCs>: not found`; otherwise
    the capture stops at the echo, as one cut before the CR would.
    🔴 LITERAL `^[` and `\\x1b`, not `ECHO_CARET`/`ECHO_RAW`, for K5's
    reason: a fixture built from the constants moves with them."""
    tail = (b"\r\nsh: " + b"\x1b" * k + b": not found\r\n# ") if full else b""
    return (b"J 80500000\n\r---Jump to address=80500000\n\r"
            b"RLXFW-B00\r\n" + _FIXTURE_GATE_LINE + b"^[^["
            b"rlxfw: init running, RLXFW-R3-RUNG1-OK\r\n" + extra +
            b"# " + b"^[" * (k - 2) + tail)


def echo_control():
    """Drive `captures()` over five synthetic captures and require the echo
    term to take out exactly the echo.  -> (ok, detail).

    Two ESC counts in each shape, so the term has to absorb a DIFFERENCE and
    not match one value; and the two shapes tell `2 x ^[ + 1 x raw` apart from
    `3 x` either one alone, which agree on every real capture so far.  The
    fifth adds one ordinary byte, which the term must NOT take: that is the
    difference between a term and a tolerance.
    """
    lo, hi = 5, 38
    files = {"full-lo-boot.log": _echo_fixture(lo),
             "full-hi-boot.log": _echo_fixture(hi),
             "cut-lo-boot.log": _echo_fixture(lo, full=False),
             "cut-hi-boot.log": _echo_fixture(hi, full=False),
             "one-byte-boot.log": _echo_fixture(hi, extra=b"x")}
    tmp = tempfile.mkdtemp(prefix="bootbytes-echo-")
    try:
        d = os.path.join(tmp, "bench", "fixture")
        os.makedirs(d)
        for name, blob in files.items():
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(blob)
        acc, _rej = captures(root=tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    raw = {os.path.basename(p): without(echo_excess, b, m) for p, b, m in acc}
    norm = {os.path.basename(p): normalised_const(b, m) for p, b, m in acc}
    replyless = {os.path.basename(p): without(reply_excess, b, m)
                 for p, b, m in acc}
    if sorted(norm) != sorted(files):
        return False, "the gate accepted %s of the five" % sorted(norm)

    # The fixture's own claim, asserted as K5 asserts its one line: the lo
    # and hi halves of each shape differ in the echo and in nothing else.
    def bare(blob):
        return blob.replace(b"^[", b"").replace(b"\x1b", b"")
    one_var = all(bare(files["%s-lo-boot.log" % s])
                  == bare(files["%s-hi-boot.log" % s]) for s in ("full", "cut"))
    step = hi - lo
    want = [("full, %d more ESCs: +%d without the term and +0 with it"
             % (step, 3 * step),
             raw["full-hi-boot.log"] - raw["full-lo-boot.log"] == 3 * step
             and norm["full-hi-boot.log"] == norm["full-lo-boot.log"]),
            ("cut before the CR: +%d without and +0 with" % (2 * step),
             raw["cut-hi-boot.log"] - raw["cut-lo-boot.log"] == 2 * step
             and norm["cut-hi-boot.log"] == norm["cut-lo-boot.log"]),
            ("one ordinary byte: +1 with it",
             norm["one-byte-boot.log"] - norm["full-hi-boot.log"] == 1),
            ("halves differ only in echo", one_var),
            # 🔄 2026-10-08: the full shape carries ash's reply and the cut
            # one does not, so with the reply term the two are one value and
            # without it they are len(REPLY) apart -- the term is the reply.
            ("full vs cut: +0 with the reply term, +%d without it"
             % len(REPLY),
             norm["full-lo-boot.log"] == norm["cut-lo-boot.log"]
             and norm["full-hi-boot.log"] == norm["cut-hi-boot.log"]
             and replyless["full-lo-boot.log"] - norm["full-lo-boot.log"]
             == len(REPLY)
             and replyless["cut-lo-boot.log"] == norm["cut-lo-boot.log"])]
    bad = [w for w, good in want if not good]
    if bad:
        return False, ("%s -- without the term %s, with it %s"
                       % (bad, sorted(raw.items()), sorted(norm.items())))
    return True, "; ".join(w for w, _g in want)


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def check():
    accepted, rejected = captures()
    # The named cut-short captures leave the population here, before any case
    # reads it, and only K10 reads them (see CUT_SHORT).
    cut = [(p, b, m) for p, b, m in accepted if rel(p) in CUT_SHORT]
    accepted = [(p, b, m) for p, b, m in accepted if rel(p) not in CUT_SHORT]
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
    # 🔄 2026-09-23 (106th segment): judged PER IMAGE.  From seating 39 there
    # are two loud console configurations (6541, and 6609 with /init's LAN
    # bring-up), so one value over every capture carrying the field had
    # stopped being a claim about the normalisation and become a count of
    # configurations booted.  Inside one image the configuration is fixed, so
    # the claim that survives is: WITH the term each image lands on one value,
    # WITHOUT it at least one image lands on more than one.  The image is the
    # capture's own `RLXFW-ID0=` -- content, never the width, never the
    # constant.  量 at the change: 84385D91 raw {6541, 6553} and F179CF21
    # {6550, 6552, 6553} each normalise to {6541}; A2C56BC8 is {6609} either
    # way (e = 0 on all three).
    by_image = {}
    for _p, b, m in varwidth:
        ids = ID0_LINE.findall(b)
        by_image.setdefault(ids[0].decode() if ids else "none", []).append((b, m))
    # 🔄 2026-10-02: WITHOUT is `without(varwidth_excess, ...)` and not
    # `raw_const`, so that echo varying inside one image cannot pass the first
    # half for this term.  量 identical output: no capture carries both.
    raw_multi = sorted(i for i, v in by_image.items()
                       if len({without(varwidth_excess, b, m)
                               for b, m in v}) > 1)
    norm_multi = sorted(i for i, v in by_image.items()
                        if len({normalised_const(b, m) for b, m in v}) > 1)
    raw_set = sorted({without(varwidth_excess, b, m)
                      for _p, b, m in varwidth})
    norm_set = sorted({normalised_const(b, m) for _p, b, m in varwidth})
    good = len(varwidth) > 0 and len(raw_multi) > 0 and not norm_multi
    detail = ("%d capture(s) over %d image(s) carry the field, hex-digit widths "
              "%s; WITHOUT the normalisation they give %s and image(s) %s land "
              "on more than one value, WITH it %s and image(s) %s do"
              % (len(varwidth), len(by_image), dict(sorted(widths.items())),
                 raw_set, raw_multi or "none", norm_set, norm_multi or "none"))
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K7",
                              "the varwidth normalisation is load-bearing: %s"
                              % detail
                              if good else
                              "the varwidth normalisation is NOT shown to be "
                              "load-bearing: %s" % detail))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K8: the echo term takes out exactly the echo and nothing else.  On a
    # SYNTHETIC fixture, like K5, because the corpus offers no partition that
    # is independent of the term: the two captures carrying echo are two
    # images, one capture each, so K7's per-image test has nothing to compare.
    # The corpus half is K2's and K6's -- R78 and R79 must both land on the
    # declared 2008, and 2008 must be reached -- and K9's, below.
    good, detail = echo_control()
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K8",
                              "the echo term removes exactly the echo on a "
                              "synthetic fixture (%s)" % detail
                              if good else
                              "the echo term is NOT exact on its fixture: %s"
                              % detail))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)
    echoed = [(p, b, m) for p, b, m in accepted if echo_excess(b)]
    print("        observed, not asserted: %d of %d boot capture(s) carry "
          "echoed input" % (len(echoed), n))
    for path, blob, ms in echoed:
        print("          %-44s %4d ESC echoed, %4d B, const %d without the "
              "term, %d with it"
              % (os.path.relpath(path, ROOT), blob.count(ECHO_CARET),
                 echo_excess(blob), without(echo_excess, blob, ms),
                 normalised_const(blob, ms)))

    # K9: the reply term on SILICON, which K8's fixture cannot be.  The
    # partition is the PRESENCE of the reply in the capture's bytes -- never
    # the constant it lands on.  Three things must hold: some capture carries
    # the reply (or the term has never met one); for each, the term removes
    # exactly len(REPLY) (it is the reply and nothing else); and each lands,
    # with the term, on a constant some reply-FREE capture reaches directly --
    # the same console configuration measured without the tool's input, which
    # is the evidence that the reply is the whole difference.  量 2026-10-08:
    # the five R7 captures with echoed input and the twenty armed boots of
    # bench/2026-10-07 without it.
    replied = [(p, b, m) for p, b, m in accepted if reply_excess(b)]
    free = {normalised_const(b, m) for p, b, m in accepted
            if not reply_excess(b)}
    exact = all(without(reply_excess, b, m) - normalised_const(b, m)
                == len(REPLY) * b.replace(ECHO_CARET, b"").replace(
                    ECHO_RAW, b"").count(REPLY) for _p, b, m in replied)
    shared = sorted({normalised_const(b, m) for _p, b, m in replied})
    good = bool(replied) and exact and set(shared) <= free
    detail = ("%d capture(s) carry the reply; WITHOUT the term they give %s, "
              "WITH it %s, reached by reply-free captures: %s"
              % (len(replied),
                 sorted({without(reply_excess, b, m) for _p, b, m in replied}),
                 shared, sorted(set(shared) & free)))
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K9",
                              "the reply term is load-bearing and exact on "
                              "the corpus: %s" % detail
                              if good else
                              "the reply term is NOT shown on the corpus: %s"
                              % detail))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # K10: each named cut-short capture held to the story its row tells.  It
    # must be in the accepted population (a renamed or deleted file goes red),
    # read STRICTLY below the declared constant it names (a capture that turns
    # out whole, or a row naming the wrong constant, goes red), and carry
    # output after its first prompt -- the race that cut it short.
    found = {rel(p): (b, m) for p, b, m in cut}
    bad, seen = [], []
    for name, want in sorted(CUT_SHORT.items()):
        if name not in found:
            bad.append("%s is not in the accepted population" % name)
            continue
        b, m = found[name]
        c = normalised_const(b, m)
        seen.append("%s reads %d, %d short of %d" % (name, c, want - c, want))
        if want not in DECLARED_CONSTS or not c < want:
            bad.append("%s reads %d, not below a declared %d" % (name, c, want))
        i = b.find(b"\r\n# ")
        if i < 0 or not b[i + 4:].strip():
            bad.append("%s holds no output after its first prompt" % name)
    good = not bad
    print("  %s  %-10s %s" % ("ok  " if good else "FAIL", "K10",
                              "every named cut-short capture is still cut "
                              "short: %s" % "; ".join(seen)
                              if good else
                              "a named cut-short capture does not fit its row: "
                              "%s" % "; ".join(bad)))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # Observation, deliberately carrying NO assertion.  What the gate rejected
    # in the real corpus is worth reading -- it is how a mis-named capture
    # gets noticed -- but asserting anything about it would make this tool
    # depend on which files happen to be committed, which is the defect K5 was
    # rewritten to avoid.
    print("        observed, not asserted: the gate rejected %d of %d file(s) "
          "the glob matched" % (len(rejected), n + len(cut) + len(rejected)))
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
    if echo_excess(blob):
        print("           of that const, %d byte(s) are the capture tool's "
              "echoed ESCs"
              % echo_excess(blob))

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
    print("bootbytes 1.5  --  boot capture length, derived not copied")
    if len(argv) > 1 and argv[1] == "predict":
        return predict()
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
