#!/usr/bin/env python3
"""boot-timeline.py -- the named intervals of a boot, out of the capture itself.

WHY IT EXISTS
-------------
On 2026-08-25 the seating found that there are TWO silences of about 345 ms
around `Booting...`, adjacent and the same length, and that only one of them is
`CLK-15`'s.  `SPEC.md` `CLK-14` records that a `340 / 348 / 345 ms` family was
once written in that row and re-homed to `CLK-15` the same day -- and whether
the re-homing sent each of the three to the right one of the two adjacent
intervals was left open, with all the captures on disk.

Two adjacent intervals of the same size is exactly how a measurement ends up
wearing another measurement's name.  The way out is not to argue about it: every
capture has a `.timing` file beside it.  This reads them and prints the
intervals with their anchor bytes named, so the question becomes a table.

AN INTERVAL WITHOUT A NAMED ANCHOR PAIR IS THE BUG
---------------------------------------------------
There are four defensible places to start the post-`Booting` measurement and
they differ by up to 1.7 ms, which is enough to make two people disagree about
a number neither of them measured wrongly.  The bytes are

        B o o t i n g . . . \\r \\n \\0 c h i p N a m e :
                          ^   ^   ^  ^
                          A   B   C  end

    A  the last '.' of `Booting...`
    B  the LF of the CR LF after it
    C  the NUL -- whose writer is undetermined; stage 1's byte loop exits on
       the NUL rather than emitting it
    D  (not shown) the 'B' of `Booting`

`--anchor` selects one.  THE DEFAULT IS C, and not by taste: over the nine
captures that existed before 2026-08-25, anchor C reproduces `CLK-15`'s
published range to the tenth of a millisecond -- 0.3447 .. 0.3569 against
344.7 .. 356.9 -- and no other anchor does.  So C is what that row was measured
with, and using anything else here would silently compare two quantities.

WHAT THE INTERVALS ARE
----------------------
    artifact    byte 0 -> the first byte of the device's own `\r\nBooting`.
                🔄 This read `byte 0 -> byte 1` until 2026-08-25, which is the
                same thing ONLY when the prefix is one byte long.  It is two on
                `bench/2026-08-25b/A-catch.log` (`00 fc`), and the old form
                reported 4.2 ms there against 340.4 and 349.0 elsewhere.
                `artifact_span` reports the width of a multi-byte prefix.  That
                byte is not the device speaking: it is the receiver's first
                sample of a line that is not yet driven, which is why two cold
                starts give complementary extremes where a printed character
                would give the same one.  It is a timestamp for "the line came
                up", and it exists only when the capture was opened before the
                power was applied.
    booting     anchor -> the first byte of `chipName`.  This is `CLK-15`:
                stage 1 copying 20,924 bytes out of memory-mapped SPI NOR a word
                at a time, across a stage boundary.
    banner      anchor -> the first byte of `---RealTek(RTL8196E)`.  `D1b`.
    entry       the largest read-to-read gap between the end of the command echo
                and the boot text, and ONLY for a capture that sent a command.
                This is `CLK-14`'s warm number.  A capture with no command in it
                has no such interval -- what precedes the boot text there is the
                operator waiting to switch the power on, and reporting that as a
                measurement is how a number gets invented.

COLD AND WARM ARE CLASSIFIED BY THE LOADER, NOT BY THE ARTIFACT BYTE
--------------------------------------------------------------------
If the artifact byte decided which captures were cold, then "the artifact gap
appears only on cold boots" would be true by construction.  So the classifier is
`C-8`'s: the loader prints `Reboot Result from Watchdog Timeout!` immediately
after `ramSize: 32M` on a warm boot and a single space on a cold one.  That is a
hardware bit read by the loader with no software of ours in its path, and it is
independent of everything measured here.

WHY THE OUTPUT IS GROUPED BY POWER CYCLE
----------------------------------------
`bench/<date>` is one seating and one power cycle.  A cold boot and the warm
resets that follow it inside the SAME directory share their die temperature,
their supply and their board, so a cold-vs-warm difference that survives inside
one directory is not a between-days effect.  Comparing the pooled populations
alone would leave that confound in.

WHAT THE TIMESTAMPS ACTUALLY ARE
--------------------------------
`console-capture.py`'s `.timing` records one line per `read()` from userspace:
the byte offset in the `.log` BEFORE that read, and the time the read returned.
So a byte's timestamp is the return time of the read that delivered it, an UPPER
bound on its arrival.  Two bytes inside one read have no measurable separation;
those are marked `~`.  The floor is the USB-serial latency timer, 1-16 ms
typical and unmeasured on this host, not the 260 us character time at 38400.

PAST THE LOADER (`P2-1`, 2026-09-23)
------------------------------------
`PROGRESS.md` `P2`'s `D1`: one script for both firmwares, every segment called
comparable computed by the same code in both columns, and what differs is a
landmark table each.  So the landmarks are DATA -- `LOADER`, `VENDOR`, `RLXFW`,
each a list of (id, compiled bytes regex, note) -- the segments are DATA,
`SEGMENTS`, each (id, from, to, class, note), and `measure(raw, tm, table)` is
the ONE function that turns a capture into segments.  The firmware only picks
the table: a kernel boot is measured against `LOADER + VENDOR` or
`LOADER + RLXFW`.

THE SEARCH RULE.  A table's landmarks are searched in table order, each from
the offset of the previous landmark of that table that was FOUND -- inclusive,
so `jump` can sit on the same bytes as `autoboot`.  A landmark not found leaves
the cursor where it was.  A landmark's offset is the first byte of its match,
or of the named group `at` when the pattern has one (`booting` sits on CLK-15's
anchor C, `ready` on the `#` of rlxfw's prompt).  The order is there because
`bench/2026-08-31c/K-J` holds a whole payload report, with its own
`---Jump to address=`, before the loader boot whose autoboot is the jump that
matters.  WEAKNESS: a landmark that matches out of place hides every later one.
With one boot per capture that reads as ABSENT, never as a wrong time -- and a
capture holding two `decompressing kernel:` is refused, not split.  That is
also why the vendor's rcS lines are not landmarks: a shell script's
backgrounded daemons print in no order the table can rely on, and one printed
late would hide `ready`.

A SEGMENT EXISTS for a capture only when both of its landmarks are in the
firmware's table and in the capture; otherwise it is absent, `--`, never 0.

FIRMWARE, from positive evidence on each side: rlxfw prints `RLXFW-B00` and
`rlxfw: init running`; the vendor prints `init started: BusyBox v1.13.4` and
its own WLAN build, `Realtek WLAN driver - version 1.6 (2013-02-21)` (rlxfw's
is `driver version 1.6 (2012-12-04)`).  One side's evidence -> that firmware;
both or neither -> `?`, named and not timed.  WEAKNESS: these are build
strings.  A vendor capture cut before its WLAN banner carries no vendor
evidence and reads `?`; an rlxfw image that linked the vendor's WLAN binary
would carry both and read `?`.  Unknown, named -- never guessed.
VARIANT (rlxfw): `loud` when the `wlan`/`nic`/`fastpath` lines carry a printk
time prefix, `quiet` when they do not; they must agree or it is `?`.
IMAGE (rlxfw): the `RLXFW-ID0=` digest; `none` on the images built before ID0
existed -- which pools several builds and is not an identity.

COLD/WARM FOR A KERNEL BOOT is `C-8`'s class of the loader boot that preceded
its jump.  In the capture itself when the loader's boot is there (K-J warm,
X8-WAIT cold); `?` when the capture holds loader text but not C-8's line
(C1-DV opens on `Jump to image start=`).  Otherwise it is inherited from the
most recent capture in the SAME directory, by `.meta.json` `started_wallclock`,
that holds a boot: a loader boot gives its class; a kernel boot means the reset
between the two is in no capture, so `?`.  A boot capture with NO wallclock (a
cold catch whose .meta.json was never written) makes it `?` unless it provably
could not have run in between: captures in one directory share one port and do
not overlap, so it needs a gap between the placed captures at least as long as
its own `.timing` span (`could_fit`).  WEAKNESS: the wallclock is whole seconds
(a tie is `?`); the no-overlap premise is an assumption about how the bench is
run; a reset whose capture is not in the directory is invisible (the rescue
captures of seating 25 went to $FWRE_WORK); a directory boundary inside one
power cycle (2026-09-14b/c) makes the first boot after it `?`.

TERM-1 (`PROGRESS.md` carried-forward row): for each kernel boot, the longest
silence -- the largest gap between consecutive `.timing` rows -- from the
boot's first landmark to `ready`, and `jump -> ready`; for each loader reset
(`J BFC00000` or `busybox reboot -f`, `Booting...` after the echo, then
`<RealTek>`), send -> prompt and its longest silence.  The send is `sent_s`
where the capture records it, else the first byte of the echo.

`--probe PREFIX` joins ONE capture with a host-probe `PREFIX.events` on the
shared CLOCK_MONOTONIC (`FW-114`): an event at `t_mono` sits at
`t_mono - t0_mono` in the capture's frame.  A capture without `t0_mono` -- every
one committed before `P2-1` -- is REFUSED: an origin guessed from
`started_wallclock` is whole seconds on another clock.

`--retro` runs every capture under the paths through all of it: the report
`P2-3` is scored against.  The captures were taken for other questions, so it
is a prediction with a stated weakness, not a result.

Run:  boot-timeline.py [PATH ...]            the loader table (the default)
      boot-timeline.py --kernel [PATH ...]   every kernel boot, landmark by landmark
      boot-timeline.py --retro [PATH ...] [--tsv FILE]
      boot-timeline.py --probe PREFIX CAPTURE.log
      boot-timeline.py --legend
Exit: 0 ok · 1 the reader closed stdout early · 2 refused, with the reason
"""

import argparse
import bisect
import datetime
import glob
import hashlib
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict, namedtuple

BOOTING = b"Booting..."
CHIPNAME = b"chipName"
BANNER = b"---RealTek(RTL8196E)"
# Every line the loader prints on the way up.  Used ONLY to tell a boot
# capture that could not be placed from a `DW` reply that was never a boot.
# 量 2026-09-01: testing only for `chipName`/BANNER missed `Y0-A`, whose
# first bytes are `P0phymode=` because the capture opened after both had
# gone past -- the detector missed the case it was written for.
# 🔴 量 2026-09-23: and it fired on NINETEEN captures that are not loader boots
# at all.  A loud rlxfw kernel's SPI driver prints a table header
# `|No chipID  Sft chipSize ... chipName    |`, and bare `chipName` matched it,
# so 18 `*-boot.log` and `2026-08-30b/L3` were named "opened after the board
# started" -- each of them a whole kernel boot from `J 80500000` to the prompt.
# Every form here is now the LOADER's: `chipName: ` with its colon, which the
# kernel's table does not have.  REFUTED IF: `bench/2026-09-22b/X20-boot` (a
# loud kernel boot) is named again, or `Y0-A`/`SQ-A` or a capture holding only
# `\0chipName: UNKNOWN` + `ramSize:` stops being named (test-boot-timeline B5).
BOOT_TEXT = (b"chipName: ", BANNER, b"ramSize:", b"P0phymode=",
             b"---Ethernet init Okay!", b"---Escape booting by user",
             b"Jump to image start=")
RAMSIZE = b"ramSize: 32M"
WATCHDOG = b"Reboot Result from Watchdog Timeout!"

# `entry` is only a reset interval when the command that preceded the boot text
# WAS a reset. `J 80500000` also produces boot text -- after the payload it
# jumped to has run, armed the watchdog and spun -- so the largest gap before
# `Booting` there is the payload's own delay loop. On `H1b` that is 0.1237 s,
# which is CLK-03's first experiment and belongs to CLK-03. Reporting it in this
# column would put a payload's run time in a row about a reset, which is the
# exact defect this whole file exists to unpick.
RESET_CMDS = ("J BFC00000", "EW B800311C")

# anchor -> offset from the start of `Booting...`
ANCHORS = {
    "A": (len(BOOTING) - 1, "the last '.' of Booting..."),
    "B": (len(BOOTING) + 1, "the LF of the CR LF after Booting..."),
    "C": (len(BOOTING) + 2, "the NUL after Booting...\\r\\n  [CLK-15's own]"),
    "D": (0,                "the 'B' of Booting"),
}


def read_timing(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            a, b = line.split()
            out.append((int(a), float(b)))
    out.sort()
    return out


def t_of(tm, offs, off):
    i = bisect.bisect_right(offs, off) - 1
    return (tm[i][1], i) if i >= 0 else (None, None)


def c8_class(raw, start=0):
    """`C-8`: the line after the first `ramSize: 32M` at or after `start`."""
    i = raw.find(RAMSIZE, start)
    if i < 0:
        return "?"
    if raw.find(WATCHDOG, i, i + 64) >= 0:
        return "warm"
    return "cold"


def analyse(log, anchor):
    # `xcheck.py` imports this by path; its signature and its answer stay what
    # they were.  The body moved to `_analyse` only so that `--retro` can hand
    # it a capture it has already read.
    raw = open(log, "rb").read()
    if BOOTING not in raw:
        return None
    tpath = log[:-4] + ".timing"
    if not os.path.exists(tpath):
        return {"log": log, "error": "no .timing beside it"}
    return _analyse(log, raw, read_timing(tpath), anchor)


def _analyse(log, raw, tm, anchor):
    if not tm:
        return {"log": log, "error": ".timing is empty"}
    offs = [x[0] for x in tm]

    r = {"log": log, "cycle": os.path.basename(os.path.dirname(log)),
         "name": os.path.basename(log)[:-4]}

    r["boot"] = c8_class(raw)

    def g(a, b):
        ta, ia = t_of(tm, offs, a)
        tb, ib = t_of(tm, offs, b)
        if ta is None or tb is None:
            return None, None
        return tb - ta, (ia != ib)

    # THE ARTIFACT PREFIX IS NOT ALWAYS ONE BYTE, and this measured it as if it
    # were until 2026-08-25.
    #
    # It used to be `g(0, 1)` -- byte 0 to byte 1 -- guarded on byte 0 being
    # 0x00 or 0xFF. 量 `bench/2026-08-25b/A-catch.log`: the prefix is TWO bytes,
    # `00 fc`, and the device's own `\r\nBooting` starts at index 2. So the old
    # form measured the gap between the two artifact bytes and reported
    # **4.2 ms** where the other two cold starts read 340.4 and 349.0 -- and the
    # pooled line printed `spread 149.1%` with nothing saying why.
    #
    # 0xFC is not an idle-line sample; it is a framing error, the receiver
    # catching a character that began before it was listening. So the prefix is
    # defined by where the DEVICE's output starts, not by which byte values look
    # like idle: everything before `\r\nBooting` is the instrument's.
    #
    # `artifact` stays anchored on byte 0 -- "the line came up" -- because that
    # is what CLK-14's existing population was measured from, every one of which
    # had a one-byte prefix. `artifact_span` is the new column and it is not
    # decoration: on the only capture that has one it is 4.2 ms, which is the
    # same order as the 4.5-14.5 ms cold-minus-warm effect CLK-15 is trying to
    # explain. An anchor ambiguity that large is a term, not a rounding error.
    # TWO guards, and the second one is here because removing the first broke
    # every warm capture the moment it was tried. `\r\nBooting` is found AFTER
    # the payload's report in an `--esc-after` capture, so "everything before
    # it" was 2,909 bytes of `H2a`'s own output and the artifact column read
    # 63.7 s. The prefix is only the instrument's when:
    #   * byte 0 is an idle-line sample (0x00 or 0xFF) -- the capture was opened
    #     before the line was driven, which is what makes this a cold start; and
    #   * it is SHORT. At 38400 a character is 260 us, so a line coming up
    #     mid-character yields a byte or two, not a report. Eight is generous
    #     and it is a bound rather than a fit.
    d0 = raw.find(b"\r\n" + BOOTING)
    if raw[:1] and raw[0] in (0x00, 0xFF) and 0 < d0 <= 8:
        # No separator: a multi-byte prefix must stay ONE whitespace-
        # delimited field or every column after it shifts on that row
        # and the table stops being parseable. Caught by this file's
        # own suite, which tripped on it.
        r["artifact_byte"] = raw[:d0].hex().upper()
        r["artifact_n"] = d0
        r["artifact"], r["artifact_exact"] = g(0, d0)
        r["artifact_span"] = g(0, d0 - 1)[0] if d0 > 1 else None
    else:
        r["artifact_byte"] = None
        r["artifact"] = None
        r["artifact_n"] = 0
        r["artifact_span"] = None

    b0 = raw.find(BOOTING)
    a_off = b0 + ANCHORS[anchor][0]

    c = raw.find(CHIPNAME, b0)
    r["booting"], r["booting_exact"] = g(a_off, c) if c >= 0 else (None, None)
    v = raw.find(BANNER, b0)
    r["banner"], r["banner_exact"] = g(a_off, v) if v >= 0 else (None, None)

    # `entry` only where a command was actually sent -- see the header.
    meta = log[:-4] + ".meta.json"
    sent = ""
    if os.path.exists(meta):
        import json
        try:
            sent = (json.load(open(meta, encoding="utf-8")).get("sent") or "").strip()
        except Exception:                                   # noqa: BLE001
            sent = ""
    r["sent"] = sent
    r["entry"] = None
    if any(sent.startswith(c) for c in RESET_CMDS):
        best = None
        for k in range(1, len(tm)):
            if tm[k][0] > b0:
                break
            d = tm[k][1] - tm[k - 1][1]
            if best is None or d > best:
                best = d
        r["entry"] = best
    return r


def fmt(v, exact=True):
    if v is None:
        return "   --   "
    return ("%8.4f" % v) if exact else ("~%7.4f" % v)


def stat(name, vals, out):
    if not vals:
        out.append("  %-30s n=0" % name)
        return
    m = statistics.fmean(vals)
    out.append("  %-30s n=%-3d %.4f .. %.4f   mean %.4f   spread %.1f%%" % (
        name, len(vals), min(vals), max(vals), m, 100.0 * (max(vals) - min(vals)) / m))


# =============================================================================
# PAST THE LOADER (`P2-1`).  Everything below reads a byte's time by the same
# rule as everything above -- `t_of`, the LAST `.timing` row with offset <= the
# byte (`FW-35`) -- and nothing above changed its answer for it.
# =============================================================================

Landmark = namedtuple("Landmark", "id rx note")
Segment = namedtuple("Segment", "id a b cls note")


def _lm(ident, pattern, note):
    return Landmark(ident, re.compile(pattern), note)


# The loader, whichever image it is about to start.  `booting` carries the
# named group `at` so that it sits on anchor C -- the byte the loader table's
# `booting` column starts from -- and `--retro` asserts, over every loader boot,
# that the two code paths give the same number (the `identity` line of (a)).
LOADER = [
    _lm("booting", rb"Booting\.\.\.[\s\S]{2}(?P<at>[\s\S])",
        "the byte after `Booting...\\r\\n`: anchor C, CLK-15's own"),
    _lm("chipname", rb"chipName: ",
        "the loader's `\\0chipName: ` (a loud kernel's SPI table prints "
        "`chipName    |`, with no colon)"),
    _lm("ramsize", rb"ramSize: 32M", "C-8 reads the line after it"),
    _lm("banner", rb"---RealTek\(RTL8196E\)", "the loader's banner (D1b)"),
    _lm("autoboot", rb"Jump to image start=",
        "printed only when no ESC arrived inside the window (LDR-15)"),
]
# Shared by both kernel tables, and shared BY IDENTITY: one object each, so
# "defined identically in both columns" is a fact of the data and not a
# promise kept in two places (`test-boot-timeline` B6 compares the patterns).
_JUMP = _lm("jump", rb"---Jump to address=|Jump to image start=",
            "the loader leaving for the image: a typed `J`, or its own autoboot")
_DECOMP = _lm("decomp", rb"decompressing kernel:",
              "rtkload, inside the image; the same text in both images")
_DDONE = _lm("decomp_done", rb"done decompressing kernel\.", "rtkload")
_KENTRY = _lm("kentry", rb"start address: 0x[0-9A-Fa-f]{8}",
              "rtkload's last line before it enters the kernel")
_WLAN = _lm("wlan", rb"Realtek WLAN driver",
            "the WLAN driver's banner: in both kernels, different builds")
_NIC = _lm("nic", rb"Probing RTL8186 10/100 NIC", "the NIC driver's probe")
_FAST = _lm("fastpath", rb"Realtek FastPath:v1\.03", "the FastPath module")
VENDOR = [
    _JUMP, _DECOMP, _DDONE, _KENTRY, _WLAN, _NIC, _FAST,
    _lm("userinit", rb"init started: BusyBox", "the vendor's init, BusyBox 1.13.4"),
    _lm("ready", rb"boa: starting server",
        "the last line the vendor prints: its web server starting"),
]
RLXFW = [
    _JUMP, _DECOMP, _DDONE, _KENTRY,
    _lm("b00", rb"RLXFW-B00",
        "start_kernel, after page_address_init (config/rlxfw-marks.tsv)"),
    _lm("b09", rb"RLXFW-B09", "start_kernel, after console_init"),
    _WLAN, _NIC, _FAST,
    _lm("b10", rb"RLXFW-B10", "init_post, before the branch that reaches userspace"),
    _lm("userinit", rb"rlxfw: init running",
        "the first line of rlxfw's /init (config/rlxfw-init.sh)"),
    _lm("ready", rb"job control turned off\r?\n(?:[^\n]*\n){0,8}?(?P<at>#)(?= |\Z)",
        "the `#` of the first prompt after the shell's own first line"),
]
TABLES = {"loader": LOADER, "vendor": LOADER + VENDOR, "rlxfw": LOADER + RLXFW}

SEGMENTS = [
    Segment("loader.booting", "booting", "chipname", "identical",
            "CLK-15: stage 1 copying out of SPI NOR; the loader table's `booting`"),
    Segment("loader.banner", "booting", "banner", "identical",
            "the loader table's `banner` (D1b); D2's positive control"),
    Segment("loader.esc", "banner", "autoboot", "identical",
            "LDR-15's ESC window; exists only when the loader autobooted"),
    Segment("rtkload.decompress", "decomp", "decomp_done", "comparable",
            "scales with the image, whose size this tool does not read (D4)"),
    Segment("rtkload.total", "jump", "kentry", "comparable",
            "the loader's jump to rtkload's hand-over"),
    Segment("kernel.early", "kentry", "wlan", "comparable", ""),
    Segment("kernel.wlan", "wlan", "nic", "comparable",
            "the vendor's WLAN init, present in both kernels"),
    Segment("kernel.nic", "nic", "fastpath", "comparable", ""),
    Segment("kernel.late", "fastpath", "userinit", "comparable",
            "holds rlxfw's own 300-jiffy pre-check wait (CLK-27, IRQ-13)"),
    Segment("kernel.total", "kentry", "userinit", "comparable", ""),
    Segment("user.ready", "userinit", "ready", "not-comparable",
            "the vendor runs rcS and its daemons; rlxfw execs a shell"),
    Segment("boot.jump_to_ready", "jump", "ready", "not-comparable",
            "TERM-1's J -> ready"),
    Segment("rlxfw.setup", "b00", "b09", "not-comparable",
            "rlxfw only: start_kernel from page_address_init to console_init"),
    Segment("rlxfw.initpost", "b10", "userinit", "not-comparable",
            "rlxfw only: init_post to /init's first line"),
]
# The host-probe join's two, each a console landmark to a host landmark.
NET_SEGMENTS = [
    Segment("net.up", "jump", "net.icmp_first", "not-comparable",
            "D8: the first ICMP echo reply the host saw"),
    Segment("net.http", "jump", "net.tcp:80_first", "not-comparable",
            "the first TCP connect to port 80 that succeeded"),
]
LOADER_SEGS = [s for s in SEGMENTS if s.id.startswith("loader.")]
KERNEL_SEGS = [s for s in SEGMENTS if not s.id.startswith("loader.")]

# Firmware evidence: literal bytes, each printed by one firmware's build only.
RLXFW_EVIDENCE = (b"RLXFW-B00", b"rlxfw: init running")
VENDOR_EVIDENCE = (b"init started: BusyBox v1.13.4",
                   b"Realtek WLAN driver - version 1.6 (2013-02-21)")
DECOMP_TEXT = b"decompressing kernel:"
# Kernel text, for NAMING a capture that has some and no rtkload line: a late
# open into a kernel, or a boot log reprinted by a command.  Neither is timed.
KERNEL_TEXT = (DECOMP_TEXT, b"start address: 0x", b"Realtek WLAN driver",
               b"Probing RTL8186 10/100 NIC", b"Realtek FastPath:v1.03",
               b"RLXFW-B00", b"init started: BusyBox", b"rlxfw: init running")
PRINTK = re.compile(rb"\[ *\d+\.\d+\] *$")
ID0_RX = re.compile(rb"RLXFW-ID0=([0-9A-Fa-f]{8})")
PROMPT = b"<RealTek>"
RESET_SENDS = ("J BFC00000", "busybox reboot -f")
NUD_UP = ("REACHABLE", "STALE", "DELAY", "PROBE", "PERMANENT")
CLASSES = ("cold", "warm", "?")

# Student's t, two-sided 95 %, by degrees of freedom -- a fixed table rather
# than a library this repository does not install.  Above 30 it uses 30's
# value, which only WIDENS an interval.
T975 = (12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042)


class Refused(Exception):
    """A reason to exit 2 before printing anything that looks like a result."""


def check_tables():
    """-> problems with the tables themselves; `main` refuses on any.

    A segment whose `from` comes after its `to` in a table's order would
    print a negative interval with a straight face, and an id used twice in
    one table would make "the landmark" ambiguous."""
    bad = []
    for name, table in TABLES.items():
        ids = [l.id for l in table]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            bad.append("table %s uses %s twice" % (name, ", ".join(dup)))
        for s in SEGMENTS:
            if s.a in ids and s.b in ids and ids.index(s.a) >= ids.index(s.b):
                bad.append("segment %s runs backwards in table %s" % (s.id, name))
    for s in SEGMENTS + NET_SEGMENTS:
        if s.cls not in ("identical", "comparable", "not-comparable"):
            bad.append("segment %s has class %r" % (s.id, s.cls))
    return bad


def pat(rx):
    return rx.pattern.decode("ascii", "backslashreplace")


def same_in_both():
    """-> the kernel landmark ids whose pattern is the same in VENDOR and RLXFW."""
    v = {l.id: pat(l.rx) for l in VENDOR}
    r = {l.id: pat(l.rx) for l in RLXFW}
    return {i for i in v if i in r and v[i] == r[i]}


def find_landmarks(raw, table):
    """-> {id: byte offset} -- THE SEARCH RULE, stated in the module header.

    Each landmark from the offset of the previous landmark of the table that
    was FOUND, inclusive; one not found leaves the cursor where it was."""
    found = {}
    pos = 0
    for lm in table:
        m = lm.rx.search(raw, pos)
        if m is None:
            continue
        off = m.start("at") if "at" in lm.rx.groupindex else m.start()
        found[lm.id] = off
        pos = off
    return found


def measure(raw, tm, table, segments=SEGMENTS):
    """THE one function that turns a capture into segments, for every firmware.

    -> (landmarks {id: offset}, times {id: (offset, t, row)},
        segments {id: (seconds, exact)}).
    A segment is computed only when both of its landmarks are in `table` AND
    were found; otherwise it is simply not in the result -- absent, never 0.
    `exact` is False when both anchor bytes arrived in one read(), which makes
    the value an upper bound on a sub-read interval (printed `~`)."""
    lm = find_landmarks(raw, table)
    offs = [x[0] for x in tm]
    at = {}
    for k, o in lm.items():
        t, i = t_of(tm, offs, o)
        if t is not None:
            at[k] = (o, t, i)
    ids = {l.id for l in table}
    seg = {}
    for s in segments:
        if s.a in ids and s.b in ids and s.a in at and s.b in at:
            seg[s.id] = (at[s.b][1] - at[s.a][1], at[s.a][2] != at[s.b][2])
    return lm, at, seg


def detect_firmware(raw):
    """-> (firmware, the evidence that decided it).  See FIRMWARE in the header."""
    r = [e for e in RLXFW_EVIDENCE if e in raw]
    v = [e for e in VENDOR_EVIDENCE if e in raw]
    if r and not v:
        return "rlxfw", "`%s`" % r[0].decode()
    if v and not r:
        return "vendor", "`%s`" % v[0].decode()
    if r and v:
        return "?", "both firmwares' evidence: `%s` and `%s`" % (r[0].decode(), v[0].decode())
    return "?", "neither firmware's evidence"


def variant_of(raw, lm):
    """rlxfw: `loud` when the driver lines carry a printk time prefix."""
    seen = set()
    for k in ("wlan", "nic", "fastpath"):
        if k in lm:
            o = lm[k]
            ls = raw.rfind(b"\n", 0, o) + 1
            seen.add("loud" if PRINTK.search(raw[ls:o]) else "quiet")
    return seen.pop() if len(seen) == 1 else "?"


def id0_of(raw):
    m = ID0_RX.search(raw)
    return m.group(1).decode().upper() if m else "none"


def wall_of(meta):
    s = (meta or {}).get("started_wallclock")
    if not isinstance(s, str):
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except ValueError:
        return None


def last_boot_event(raw):
    """-> what a LATER capture in the same directory inherits from this one:
    None, ("loader", C-8 class), ("loader-text", None) or ("kernel", None)."""
    lb = raw.rfind(BOOTING)
    lk = max((raw.rfind(m) for m in KERNEL_TEXT), default=-1)
    if lk >= 0 and lk > lb:
        return ("kernel", None)
    if lb >= 0:
        return ("loader", c8_class(raw, lb))
    if any(m in raw for m in BOOT_TEXT):
        return ("loader-text", None)
    return None


class Corpus:
    """Each file read once per run.  Nothing is cached across runs, and
    `read_timing` itself is left uncached: `xcheck`'s self-test rewrites one
    `.timing` between calls and must see every version."""

    def __init__(self):
        self._raw, self._tm, self._meta, self._dirs = {}, {}, {}, {}

    def raw(self, log):
        if log not in self._raw:
            with open(log, "rb") as fh:
                self._raw[log] = fh.read()
        return self._raw[log]

    def tm(self, log):
        """-> (rows, None) or (None, why there are none)."""
        if log not in self._tm:
            p = log[:-4] + ".timing"
            if not os.path.exists(p):
                self._tm[log] = (None, "no .timing beside it")
            else:
                try:
                    rows = read_timing(p)
                    self._tm[log] = (rows, None) if rows else (None, ".timing is empty")
                except (ValueError, OSError) as exc:
                    self._tm[log] = (None, "unparseable .timing: %s" % exc)
        return self._tm[log]

    def meta(self, log):
        """-> the .meta.json as a dict; {} when there is none or it will not parse."""
        if log not in self._meta:
            p = log[:-4] + ".meta.json"
            m = {}
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as fh:
                        m = json.load(fh)
                except (OSError, ValueError):
                    m = {}
                if not isinstance(m, dict):
                    m = {}
            self._meta[log] = m
        return self._meta[log]

    def dir_index(self, d):
        """-> [(log, wallclock or None, last boot event)] for every .log in `d`."""
        if d not in self._dirs:
            idx = []
            for log in sorted(glob.glob(os.path.join(d, "*.log"))):
                idx.append((log, wall_of(self.meta(log)), last_boot_event(self.raw(log))))
            self._dirs[d] = idx
        return self._dirs[d]


def _base(log):
    return os.path.basename(log)[:-4]


def kernel_class(corpus, log, raw, lm):
    """-> (cold|warm|?, how it was decided).  COLD/WARM in the module header."""
    k = raw.find(DECOMP_TEXT)
    if "ramsize" in lm:
        return c8_class(raw, lm["ramsize"]), "its own C-8 line"
    if "booting" in lm:
        return "?", "its loader boot is in the capture but C-8's line is not"
    head = raw[:k] if k >= 0 else raw
    lt = [m for m in BOOT_TEXT if m in head]
    if lt:
        return "?", ("it opens inside the loader's boot (`%s`), after C-8's line"
                     % lt[0].decode().strip())
    me = wall_of(corpus.meta(log))
    if me is None:
        return "?", "its .meta.json has no started_wallclock"
    d = os.path.dirname(log)
    idx = [(l, w, ev) for l, w, ev in corpus.dir_index(d) if l != log and ev is not None]
    unplaced = [l for l, w, ev in idx if w is None]
    prior = [(w, l, ev) for l, w, ev in idx if w is not None and w <= me]
    if not prior:
        return "?", ("no capture before it in %s holds a boot%s" % (
            d, (" (%s holds one and has no started_wallclock)" % _base(unplaced[0]))
            if unplaced else ""))
    wmax = max(w for w, _, _ in prior)
    last = [(l, ev) for w, l, ev in prior if w == wmax]
    if wmax == me:
        return "?", "%s holds a boot and started in the same second" % _base(last[0][0])
    if len(last) > 1:
        return "?", ("%s hold boots and share the latest second"
                     % ", ".join(_base(l) for l, _ in last))
    l, ev = last[0]
    # A boot capture with no wallclock (a cold catch whose .meta.json was never
    # written) could be the most recent boot -- unless it cannot fit.  One
    # serial port, so captures in one directory do not overlap: it can only
    # have run inside a gap between the placed captures from `l` to this one,
    # and it ran at least as long as its own last `.timing` row.
    for u in unplaced:
        span = could_fit(corpus, d, u, wmax, me)
        if span is not None:
            return "?", ("%s holds a boot and has no started_wallclock, and the "
                         "captures from %s to this one leave a gap that could hold "
                         "its %s s" % (_base(u), _base(l), span))
    if ev[0] == "loader":
        if ev[1] == "?":
            return "?", "inherited from %s, whose own C-8 line is missing" % _base(l)
        return ev[1], "inherited from %s" % _base(l)
    if ev[0] == "kernel":
        return "?", ("%s booted a kernel after the last loader boot; the reset "
                     "before this one is in no capture" % _base(l))
    return "?", "%s holds loader text without C-8's line" % _base(l)


def could_fit(corpus, d, unplaced, lo, hi):
    """-> None when `unplaced` provably did not run between the captures that
    started at `lo` and `hi` in directory `d`; otherwise a printable span.

    WEAKNESS, stated: it rests on captures in one directory never overlapping
    (one port, one process).  A placed capture with no `duration_s` counts as
    0 s long, and an unplaced one with no `.timing` as 0 s -- both only make
    a fit MORE likely, so the error can only be a `?` too many."""
    tm, _ = corpus.tm(unplaced)
    span = tm[-1][1] if tm else 0.0
    placed = []
    for l, w, _ in corpus.dir_index(d):
        if w is not None and lo <= w <= hi:
            dur = corpus.meta(l).get("duration_s")
            placed.append((w, dur if isinstance(dur, (int, float)) else 0.0))
    placed.sort()
    for (w1, d1), (w2, _) in zip(placed, placed[1:]):
        # whole-second starts: the next one began before w2 + 1
        if w2 + 1 - (w1 + d1) >= span:
            return "%.1f" % span
    return None


def longest_silence(tm, i0, i1):
    """-> (the largest gap between consecutive rows i0..i1, the row that ended it)."""
    best, bk = None, None
    for k in range(i0 + 1, i1 + 1):
        g = tm[k][1] - tm[k - 1][1]
        if best is None or g > best:
            best, bk = g, k
    return best, bk


def kernel_record(corpus, log, force=None):
    """-> None when the capture holds no rtkload line; otherwise one kernel boot."""
    raw = corpus.raw(log)
    nd = raw.count(DECOMP_TEXT)
    if nd == 0:
        return None
    d = os.path.dirname(log)
    rec = {"log": log, "dir": d, "cycle": os.path.basename(d), "name": _base(log),
           "fw": "?", "fw_why": "", "variant": "-", "id0": "-", "class": "?",
           "class_why": "", "lm": {}, "at": {}, "seg": {}, "missing": [],
           "error": None, "t1": None, "wall": wall_of(corpus.meta(log)),
           "echo_jump": None}
    if nd > 1:
        rec["error"] = ("holds %d `decompressing kernel:` -- %d boots in one capture "
                        "are refused, not split" % (nd, nd))
        return rec
    if force:
        fw, why = force, "forced by --firmware"
    else:
        fw, why = detect_firmware(raw)
    rec["fw"], rec["fw_why"] = fw, why
    if fw not in ("vendor", "rlxfw"):
        rec["error"] = "firmware unknown -- %s" % why
        return rec
    tm, terr = corpus.tm(log)
    if terr:
        rec["error"] = terr
        return rec
    table = TABLES[fw]
    lm, at, seg = measure(raw, tm, table)
    rec.update(lm=lm, at=at, seg=seg, tm_last=tm[-1][1])
    rec["missing"] = [l.id for l in table[len(LOADER):] if l.id not in lm]
    if fw == "rlxfw":
        rec["variant"] = variant_of(raw, lm)
        rec["id0"] = id0_of(raw)
    rec["class"], rec["class_why"] = kernel_class(corpus, log, raw, lm)
    if not seg:
        rec["error"] = "no segment has both of its landmarks in the capture"
    # TERM-1: from the boot's first landmark -- not from the echo, which in K-J
    # precedes the boot by a payload's run and in X8-WAIT by 80 s of operator
    # time -- to `ready`.  `echo_jump` measures what that choice costs on the
    # J-path boots, where the echo is the capture's first byte.
    if "ready" in at:
        first = min(at, key=lambda k: at[k][0])
        gap, k = longest_silence(tm, at[first][2], at["ready"][2])
        before = None
        if k is not None:
            after = [(o, i) for i, o in lm.items() if o >= tm[k][0]]
            before = min(after)[1] if after else None
        rec["t1"] = {"from": first, "silence": gap,
                     "silence_byte": tm[k][0] if k is not None else None,
                     "before": before,
                     "j2r": seg.get("boot.jump_to_ready", (None,))[0]}
    sent = (corpus.meta(log).get("sent") or "").strip()
    if (sent.startswith("J ") and raw.startswith(sent.encode("ascii", "replace"))
            and "jump" in at and "booting" not in lm and "autoboot" not in lm):
        # only where the `J` went straight into the image: in K-J it went into a
        # payload, and the jump that counts is an autoboot 7.5 s later
        rec["echo_jump"] = at["jump"][1] - tm[0][1]
    return rec


def reset_record(corpus, log):
    """TERM-1's loader resets.  -> None when the capture is not one."""
    meta = corpus.meta(log)
    sent = (meta.get("sent") or "").strip()
    if sent.startswith("J BFC00000"):
        kind = "J BFC00000"
    elif sent == "busybox reboot -f":
        kind = "busybox reboot -f"
    else:
        return None
    raw = corpus.raw(log)
    rec = {"log": log, "kind": kind, "error": None, "dir": os.path.dirname(log)}
    e = raw.find(sent.encode("ascii", "replace"))
    if e < 0:
        rec["error"] = "the echo of `%s` is not in the log" % sent
        return rec
    b = raw.find(BOOTING, e)
    p = raw.find(PROMPT, b) if b >= 0 else -1
    if b < 0 or p < 0:
        rec["error"] = ("no reset in this capture" if b < 0
                        else "a reset but no `<RealTek>` after it")
        rec["not_a_reset"] = True
        return rec
    tm, terr = corpus.tm(log)
    if terr:
        rec["error"] = terr
        return rec
    offs = [x[0] for x in tm]
    te, ie = t_of(tm, offs, e)
    tp, ip = t_of(tm, offs, p)
    ss = meta.get("sent_s")
    if isinstance(ss, (int, float)) and not isinstance(ss, bool):
        t_send, via = float(ss), "sent_s"
    else:
        t_send, via = te, "echo"
    gap, k = longest_silence(tm, ie, ip)
    if via == "sent_s" and (gap is None or te - t_send > gap):
        gap, k = te - t_send, ie
    rec.update(send_to_prompt=tp - t_send, via=via, silence=gap,
               silence_byte=tm[k][0] if k is not None else None)
    return rec


def med(vals):
    return statistics.median(vals) if vals else None


def p90(vals):
    """Nearest rank: an observed value, never an interpolation."""
    v = sorted(vals)
    return v[max(0, math.ceil(0.9 * len(v)) - 1)] if v else None


def cellstr(vals):
    if not vals:
        return "n=0"
    v = sorted(vals)
    return "n=%d %.4f %.4f..%.4f" % (len(v), statistics.median(v), v[0], v[-1])


def collect_logs(paths):
    logs = []
    for p in paths:
        if os.path.isdir(p):
            logs += sorted(glob.glob(os.path.join(p, "**", "*.log"), recursive=True))
        else:
            logs.append(p)
    return logs


def orphan_why(corpus, log):
    """What a capture with loader text and no `Booting...` shows -- and no more.

    It used to say "the capture opened after the board started".  The capture
    cannot tell that from an instrument that dropped the bytes (2026-08-23's
    `console-dump.py` discarded the stream before the prompt), so it says what
    is there: the first loader line, where and when, and whether it is timed."""
    raw = corpus.raw(log)
    hits = sorted((raw.find(m), m) for m in BOOT_TEXT if m in raw)
    off, m = hits[0]
    tm, terr = corpus.tm(log)
    what = "its first loader line is `%s` at byte %d" % (m.decode().strip(), off)
    if terr == "no .timing beside it":
        return ("boot text but no `Booting...`: %s, and there is no .timing beside "
                "it -- not a console-capture capture, and nothing in it is timed"
                % what)
    if terr:
        return "boot text but no `Booting...`: %s (%s)" % (what, terr)
    t, _ = t_of(tm, [x[0] for x in tm], off)
    return ("boot text but no `Booting...`: %s, %.4f s after the capture opened "
            "-- the reset is not in this capture" % (what, t))


# ------------------------------------------------------------------ output
def legend_lines():
    out = ["landmarks, each table in its search order (THE SEARCH RULE in the tool's "
           "header); a kernel boot is searched with LOADER then its firmware's table;",
           "`=` marks a landmark defined identically in VENDOR and RLXFW; `(?P<at>...)` "
           "is the byte a landmark sits on"]
    for name, table in (("LOADER", LOADER), ("VENDOR", VENDOR), ("RLXFW", RLXFW)):
        out.append("  %s" % name)
        for l in table:
            mark = "=" if name != "LOADER" and l.id in same_in_both() else " "
            out.append("   %s %-12s %s" % (mark, l.id, pat(l.rx)))
            if l.note:
                out.append("     %-12s   %s" % ("", l.note))
    out.append("segments -- interval = t(to) - t(from); absent (`--`) unless both "
               "landmarks are in the firmware's table and in the capture")
    for s in SEGMENTS:
        out.append("  %-20s %-11s -> %-11s %-15s %s" % (s.id, s.a, s.b, s.cls, s.note))
    return out


def kernel_lines(rec):
    out = ["capture %s" % rec["log"]]
    out.append("  firmware %s (%s)   variant %s   image %s" % (
        rec["fw"], rec["fw_why"], rec["variant"],
        ("id0=" + rec["id0"]) if rec["fw"] == "rlxfw" else "-"))
    out.append("  class %s (%s)" % (rec["class"], rec["class_why"] or "not decided"))
    if rec["error"] and not rec["seg"]:
        out.append("  NOT TIMED: %s" % rec["error"])
        return out
    table = TABLES[rec["fw"]]
    for l in table:
        if l.id in rec["at"]:
            o, t, i = rec["at"][l.id]
            out.append("  lm   %-12s byte %7d  t %11.6f  row %d" % (l.id, o, t, i))
        else:
            out.append("  lm   %-12s --" % l.id)
    ids = {l.id for l in table}
    for s in SEGMENTS:
        if s.a not in ids or s.b not in ids:
            continue
        if s.id in rec["seg"]:
            v, ex = rec["seg"][s.id]
            val = ("%.6f" % v) if ex else ("~%.6f" % v)
        else:
            val = "--"
        out.append("  seg  %-20s %-11s -> %-11s %-15s %s" % (s.id, s.a, s.b, s.cls, val))
    if rec["missing"]:
        out.append("  absent from this capture: %s" % " ".join(rec["missing"]))
    if rec["t1"]:
        t1 = rec["t1"]
        out.append("  TERM-1  longest silence %.6f s from `%s` to `ready`, ending at byte %s%s;"
                   " jump -> ready %s" % (
                       t1["silence"], t1["from"], t1["silence_byte"],
                       (" before `%s`" % t1["before"]) if t1["before"] else "",
                       ("%.6f" % t1["j2r"]) if t1["j2r"] is not None else "--"))
    return out


def image_key(rec):
    if rec["fw"] == "vendor":
        return "vendor"
    return "rlxfw/%s/%s" % (rec["variant"], rec["id0"])


def fwvar(rec):
    return rec["fw"] if rec["fw"] == "vendor" else "rlxfw %s" % rec["variant"]


class Tsv:
    COLS = ("record", "firmware", "variant", "class", "image", "directory", "capture",
            "quantity", "from", "to", "seg_class", "n", "value", "median", "min",
            "max", "p90", "argmax", "ratio", "slope", "ci_lo", "ci_hi", "r", "note")

    def __init__(self):
        self.rows = []

    def add(self, **kw):
        bad = set(kw) - set(self.COLS)
        if bad:
            raise ValueError("unknown TSV column(s) %s" % sorted(bad))
        self.rows.append(kw)

    @staticmethod
    def _f(v):
        if v is None:
            return ""
        if isinstance(v, float):
            return "%.6f" % v
        return str(v).replace("\t", " ").replace("\n", " ")

    def write(self, path, header):
        body = ["# " + h for h in header]
        body.append("\t".join(self.COLS))
        for r in self.rows:
            body.append("\t".join(self._f(r.get(c)) for c in self.COLS))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(body) + "\n")
        os.replace(tmp, path)


def tool_digest():
    with open(os.path.abspath(__file__), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def ols(xs, ys):
    """-> (slope, ci_lo, ci_hi, r) of y on x with an intercept; None where undefined."""
    n = len(xs)
    if n < 3:
        return None, None, None, None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return None, None, None, None
    b = sxy / sxx
    r = sxy / math.sqrt(sxx * syy) if syy > 0 else None
    resid = sum((y - my - b * (x - mx)) ** 2 for x, y in zip(xs, ys))
    se = math.sqrt(resid / (n - 2) / sxx)
    t = T975[min(n - 2, len(T975)) - 1]
    return b, b - t * se, b + t * se, r


# ------------------------------------------------------------------- retro
def retro(paths, tsv_path):
    corpus = Corpus()
    logs = collect_logs(paths)
    tsv = Tsv()
    out = []
    p = out.append

    loader_rows = []            # (log, _analyse row)
    kboots = []
    ktext_only = []
    resets = []
    for log in logs:
        try:
            raw = corpus.raw(log)
        except OSError as exc:
            raise Refused("cannot read %s: %s" % (log, exc))
        if BOOTING in raw:
            tm, terr = corpus.tm(log)
            if tm is not None:
                r = _analyse(log, raw, tm, "C")
                if "error" not in r:
                    loader_rows.append((log, r))
        k = kernel_record(corpus, log)
        if k is not None:
            kboots.append(k)
        elif any(m in raw for m in KERNEL_TEXT):
            ktext_only.append(log)
        rr = reset_record(corpus, log)
        if rr is not None:
            resets.append(rr)
    if not loader_rows and not kboots:
        raise Refused("no loader boot and no kernel boot under %s" % " ".join(paths))

    timed = [k for k in kboots if not k["error"] or k["seg"]]
    lclass = defaultdict(int)
    for _, r in loader_rows:
        lclass[r["boot"]] += 1
    fwn = defaultdict(int)
    for k in kboots:
        fwn[fwvar(k) if k["fw"] in ("vendor", "rlxfw") else "?"] += 1

    digest = tool_digest()
    p("boot-timeline --retro   tool sha256 %s   paths: %s" % (digest[:16], " ".join(paths)))
    p("A PREDICTION, NOT A RESULT: every capture below was taken for another question "
      "(PROGRESS.md P2-1).")
    p("corpus: %d .log; loader boots %d (cold %d, warm %d, ? %d); kernel boots %d "
      "(vendor %d, rlxfw quiet %d, rlxfw loud %d, rlxfw ? %d, firmware unknown %d); "
      "kernel text without rtkload %d" % (
          len(logs), len(loader_rows), lclass["cold"], lclass["warm"], lclass["?"],
          len(kboots), fwn["vendor"], fwn["rlxfw quiet"], fwn["rlxfw loud"],
          fwn["rlxfw ?"], fwn["?"], len(ktext_only)))
    p("rules: a byte arrived at the LAST .timing row with offset <= its own (FW-35), an "
      "upper bound; landmarks and cold/warm as in the tool's header; a cell is n, "
      "median (mean of the middle two when n is even), min..max, in seconds")
    p("")
    out.extend(legend_lines())
    p("")

    # (a) the loader --------------------------------------------------------
    # IDENTITY, written before it was run: the landmark engine's `loader.booting`
    # and `loader.banner` must equal the loader table's `booting` and `banner`
    # EXACTLY on every loader boot -- two code paths, one byte rule.  A single
    # disagreement means one of them is anchored on another byte.
    p("(a) LOADER -- the loader table's own rows (anchor C); loader.esc where the "
      "loader autobooted")
    lvals = {s.id: defaultdict(list) for s in LOADER_SEGS}
    agree = {"loader.booting": 0, "loader.banner": 0}
    differ = []
    for log, r in loader_rows:
        tm, _ = corpus.tm(log)
        _, _, seg = measure(corpus.raw(log), tm, LOADER)
        for sid, key in (("loader.booting", "booting"), ("loader.banner", "banner")):
            mine = seg.get(sid, (None,))[0]
            if mine == r[key]:
                agree[sid] += 1
            else:
                differ.append((log, sid, mine, r[key]))
            if r[key] is not None:
                lvals[sid][r["boot"]].append(r[key])
        if "loader.esc" in seg:
            lvals["loader.esc"][r["boot"]].append(seg["loader.esc"][0])
        for sid, key in (("loader.booting", "booting"), ("loader.banner", "banner")):
            if r[key] is not None:
                tsv.add(record="loader", **{"class": r["boot"]}, directory=os.path.dirname(log),
                        capture=log, quantity=sid, value=r[key], n=1)
        if "loader.esc" in seg:
            tsv.add(record="loader", **{"class": r["boot"]}, directory=os.path.dirname(log),
                    capture=log, quantity="loader.esc", value=seg["loader.esc"][0], n=1)
    p("  %-20s %-24s %-15s %-32s %-32s %s" % ("segment", "from -> to", "class", "cold", "warm", "?"))
    for s in LOADER_SEGS:
        cells = [cellstr(lvals[s.id][c]) for c in CLASSES]
        p("  %-20s %-24s %-15s %-32s %-32s %s" % (s.id, "%s -> %s" % (s.a, s.b), s.cls, *cells))
        for c in CLASSES:
            v = lvals[s.id][c]
            tsv.add(record="cell", firmware="loader", **{"class": c}, image="pooled",
                    quantity=s.id, **{"from": s.a}, to=s.b, seg_class=s.cls, n=len(v),
                    median=med(v), min=min(v) if v else None, max=max(v) if v else None)
    p("  identity: the landmark engine's loader.booting equals the loader table's "
      "`booting` on %d of %d loader boots, loader.banner equals `banner` on %d of %d"
      % (agree["loader.booting"], len(loader_rows), agree["loader.banner"], len(loader_rows)))
    for log, sid, mine, theirs in differ:
        p("    IDENTITY BROKEN %s %s: engine %r, loader table %r" % (log, sid, mine, theirs))
    p("")

    # (b) kernel segments ---------------------------------------------------
    p("(b) KERNEL SEGMENTS per firmware, variant and cold/warm; rlxfw again per image "
      "(RLXFW-ID0), earliest image first")
    groups = [("vendor", [k for k in timed if k["fw"] == "vendor"])]
    for var in ("quiet", "loud", "?"):
        g = [k for k in timed if k["fw"] == "rlxfw" and k["variant"] == var]
        if g or var != "?":
            groups.append(("rlxfw %s" % var, g))

    def seg_block(label, recs, fw, variant, image, indent="  "):
        cnt = defaultdict(int)
        for k in recs:
            cnt[k["class"]] += 1
        p("%s%s -- %d boot(s): cold %d, warm %d, ? %d" % (
            indent, label, len(recs), cnt["cold"], cnt["warm"], cnt["?"]))
        p("%s  %-20s %-24s %-15s %-32s %-32s %s" % (indent, "segment", "from -> to",
                                                   "class", "cold", "warm", "?"))
        ids = {l.id for l in TABLES[fw]}
        for s in KERNEL_SEGS:
            if s.a not in ids or s.b not in ids:
                continue
            cells = []
            for c in CLASSES:
                v = [k["seg"][s.id][0] for k in recs if k["class"] == c and s.id in k["seg"]]
                cells.append(cellstr(v))
                tsv.add(record="cell", firmware=fw, variant=variant,
                        **{"class": c}, image=image, quantity=s.id, **{"from": s.a},
                        to=s.b, seg_class=s.cls, n=len(v), median=med(v),
                        min=min(v) if v else None, max=max(v) if v else None)
            p("%s  %-20s %-24s %-15s %-32s %-32s %s" % (
                indent, s.id, "%s -> %s" % (s.a, s.b), s.cls, *cells))

    for label, recs in groups:
        fw = label.split()[0]
        variant = label.split()[1] if fw == "rlxfw" else "-"
        seg_block(label + (" (one image)" if fw == "vendor" else " (pooled over images)"),
                  recs, fw, variant, "pooled")
        p("")
    for label, recs in groups:
        if not label.startswith("rlxfw") or not recs:
            continue
        variant = label.split()[1]
        by = defaultdict(list)
        for k in recs:
            by[k["id0"]].append(k)

        def first_of(ks):
            return min((k["wall"] if k["wall"] is not None else float("inf"),
                        k["cycle"], k["name"]) for k in ks)
        p("  %s, per image, earliest first:" % label)
        for img in sorted(by, key=lambda i: first_of(by[i])):
            f = min(by[img], key=lambda k: (k["wall"] if k["wall"] is not None
                                           else float("inf"), k["cycle"], k["name"]))
            seg_block("id0=%s  first %s/%s" % (img, f["cycle"], f["name"]), by[img],
                      "rlxfw", variant, img, indent="    ")
        p("")
    for k in kboots:
        if k["fw"] not in ("vendor", "rlxfw"):
            continue
        tsv.add(record="kboot", firmware=k["fw"], variant=k["variant"],
                **{"class": k["class"]}, image=k["id0"], directory=k["dir"],
                capture=k["log"], note="%s; %s" % (k["class_why"], k["fw_why"]))
        for s in SEGMENTS:
            if s.id in k["seg"]:
                v, ex = k["seg"][s.id]
                tsv.add(record="seg", firmware=k["fw"], variant=k["variant"],
                        **{"class": k["class"]}, image=k["id0"], directory=k["dir"],
                        capture=k["log"], quantity=s.id, **{"from": s.a}, to=s.b,
                        seg_class=s.cls, n=1, value=v, note="" if ex else "one read")
        for lid, (o, t, i) in sorted(k["at"].items(), key=lambda kv: kv[1][0]):
            tsv.add(record="lm", firmware=k["fw"], variant=k["variant"],
                    **{"class": k["class"]}, image=k["id0"], directory=k["dir"],
                    capture=k["log"], quantity=lid, value=t, note="byte %d" % o)

    # (c) named -------------------------------------------------------------
    p("(c) NAMED")
    nothing = [k for k in kboots if k["error"] and not k["seg"]]
    p("  kernel boots that contributed nothing: %d" % len(nothing))
    for k in nothing:
        p("    %s -- %s" % (k["log"], k["error"]))
    frag = [k for k in timed if k["missing"]]
    p("  fragments -- a landmark of the firmware's own table is absent: %d" % len(frag))
    for k in frag:
        # What the capture shows about where it stopped, and no cause: the
        # device's last byte, how long the capture ran, and what ended it.
        meta = corpus.meta(k["log"])
        first = min(k["at"], key=lambda i: k["at"][i][0]) if k["at"] else None
        dur = meta.get("duration_s")
        quiet = ("; the device sent nothing in its last %.1f s" % (dur - k["tm_last"])
                 if isinstance(dur, (int, float)) and "tm_last" in k else "")
        p("    %s -- %s; absent: %s; its first landmark is `%s` at byte %d; its last "
          "byte arrived at %.4f s and the capture ran %s s (%s)%s" % (
              k["log"], k["fw"], " ".join(k["missing"]), first,
              k["at"][first][0] if first else -1, k.get("tm_last", float("nan")),
              dur if dur is not None else "?", meta.get("stop_reason", "no stop_reason"),
              quiet))
    unk = [k for k in timed if k["class"] == "?"]
    p("  class `?`: %d" % len(unk))
    for k in unk:
        p("    %s -- %s" % (k["log"], k["class_why"]))
    p("  kernel text without rtkload's `decompressing kernel:` (not a boot this tool "
      "can time): %d" % len(ktext_only))
    for l in ktext_only:
        p("    %s" % l)
    for k in nothing:
        tsv.add(record="nothing", firmware=k["fw"], capture=k["log"], note=k["error"])
    for k in frag:
        tsv.add(record="fragment", firmware=k["fw"], capture=k["log"],
                note="absent: " + " ".join(k["missing"]))
    for k in unk:
        tsv.add(record="class?", firmware=k["fw"], capture=k["log"], note=k["class_why"])
    p("")

    # (d) TERM-1 ------------------------------------------------------------
    p("(d) TERM-1 -- the silences a boot cell's terminator must outlast")
    p("  longest silence = the largest gap between consecutive .timing rows, from the "
      "boot's first landmark to `ready`;")
    p("  p90 is nearest-rank; `max` names the capture that holds it (the first in "
      "path order on a tie)")
    ej = [k["echo_jump"] for k in timed if k["echo_jump"] is not None]
    p("  echo -> jump on the %d J-path boots whose log opens on the echo: max %s s "
      "-- what starting at the boot's first landmark instead of the echo moves"
      % (len(ej), ("%.6f" % max(ej)) if ej else "--"))

    def dist(label, pairs, what):
        """pairs = [(value, capture)] -> one printed row and one TSV row."""
        vals = [v for v, _ in pairs]
        if not vals:
            p("  %-28s %-17s n=0" % (label, what))
            tsv.add(record="term1cell", firmware=label, quantity=what, n=0)
            return
        vmax, cap = sorted(pairs, key=lambda vc: (-vc[0], vc[1]))[0]
        p("  %-28s %-17s n=%-4d median %8.4f   p90 %8.4f   max %8.4f   %s" % (
            label, what, len(vals), med(vals), p90(vals), vmax, cap))
        tsv.add(record="term1cell", firmware=label, quantity=what, n=len(vals),
                median=med(vals), p90=p90(vals), max=vmax, min=min(vals), argmax=cap)

    p("  kernel boots")
    tgroups = [("vendor", [k for k in timed if k["fw"] == "vendor"])]
    for var in ("quiet", "loud"):
        tgroups.append(("rlxfw %s" % var,
                        [k for k in timed if k["fw"] == "rlxfw" and k["variant"] == var]))
    for label, recs in tgroups:
        t1 = [k for k in recs if k["t1"]]
        dist(label, [(k["t1"]["silence"], k["log"]) for k in t1], "longest silence")
        dist(label, [(k["t1"]["j2r"], k["log"]) for k in t1 if k["t1"]["j2r"] is not None],
             "jump -> ready")
    for label, recs in tgroups[1:]:
        by = defaultdict(list)
        for k in recs:
            if k["t1"]:
                by[k["id0"]].append(k)
        for img in sorted(by, key=lambda i: min((k["wall"] or float("inf"), k["cycle"])
                                                 for k in by[i])):
            dist("%s id0=%s" % (label, img),
                 [(k["t1"]["silence"], k["log"]) for k in by[img]], "longest silence")
            dist("%s id0=%s" % (label, img),
                 [(k["t1"]["j2r"], k["log"]) for k in by[img] if k["t1"]["j2r"] is not None],
                 "jump -> ready")
    for k in timed:
        if k["t1"]:
            tsv.add(record="term1", firmware=k["fw"], variant=k["variant"],
                    **{"class": k["class"]}, image=k["id0"], directory=k["dir"],
                    capture=k["log"], quantity="longest silence",
                    **{"from": k["t1"]["from"]}, to="ready", n=1,
                    value=k["t1"]["silence"],
                    note="ends at byte %s before %s" % (k["t1"]["silence_byte"],
                                                      k["t1"]["before"]))
    good_resets = [r for r in resets if not r["error"]]
    not_reset = [r for r in resets if r.get("not_a_reset")]
    bad_resets = [r for r in resets if r["error"] and not r.get("not_a_reset")]
    p("  loader resets -- sent `J BFC00000` or `busybox reboot -f`, `Booting...` after the "
      "echo, then `<RealTek>`; send -> prompt")
    for kind in RESET_SENDS:
        rs = [r for r in good_resets if r["kind"] == kind]
        dist(kind, [(r["silence"], r["log"]) for r in rs], "longest silence")
        dist(kind, [(r["send_to_prompt"], r["log"]) for r in rs], "send -> prompt")
    via = defaultdict(int)
    for r in good_resets:
        via[r["via"]] += 1
    p("  the send is `sent_s` on %d and the first byte of the echo on %d; %d sent a reset "
      "command and hold no reset and prompt after it (not in the population); %d "
      "could not be timed" % (via["sent_s"], via["echo"], len(not_reset), len(bad_resets)))
    for r in bad_resets:
        p("    %s -- %s" % (r["log"], r["error"]))
    for r in good_resets:
        tsv.add(record="reset", firmware=r["kind"], directory=r["dir"], capture=r["log"],
                quantity="send -> prompt", value=r["send_to_prompt"], n=1,
                note="send from %s; longest silence %.6f ending at byte %s" % (
                    r["via"], r["silence"], r["silence_byte"]))
    p("")

    # (e) per-seating scale -------------------------------------------------
    scale_section(p, tsv, loader_rows, timed)

    print("\n".join(out))
    if tsv_path:
        tsv.write(tsv_path, [
            "boot-timeline.py --retro, tool sha256 %s, paths: %s" % (digest, " ".join(paths)),
            "one record per line; columns unused by a record are empty; seconds",
            "records: loader seg lm kboot cell nothing fragment class? term1 term1cell "
            "reset scale scalefit"])
    return 0


def scale_section(p, tsv, loader_rows, kboots):
    # REFUTATION CONDITIONS, written before this section printed a number.
    #   H-prop: one rate factor common to a seating moves every interval in
    #     proportion.  Predicts: each kernel segment's per-directory ratio tracks
    #     the loader's -- slope near 1, r > 0 -- however long the segment is.
    #     REFUTED for a segment whose slope's interval holds 0 (it does not track).
    #   H-add: USB latency, a few ms per read, added to each interval.  A
    #     multi-second segment cannot move by the loader's ~4 % (100-200 ms) that
    #     way, so for segments of a second or more it predicts a slope near 0.
    #     REFUTED for such a segment whose slope's interval excludes 0.
    # What this cannot say: a common factor can be the host's monotonic rate or
    # the device's timebase, and nothing below separates them.  And the pairs
    # are not independent -- an image seen in two directories contributes two
    # points mirrored about 1 -- so the interval is indicative, not exact.
    p("(e) PER-SEATING SCALE -- does a directory's loader `booting` median move with the "
      "same image's kernel segments?")
    p("  A common factor here can be the host's monotonic rate or the device's timebase; "
      "this data cannot separate them.")
    p("  H-prop (one rate factor per seating) predicts slope ~1 for every segment; refuted "
      "for a segment whose 95 % interval holds 0.")
    p("  H-add (USB latency, ms per read) predicts slope ~0 for a segment of >= 1 s; "
      "refuted for one whose interval excludes 0.")
    p("  ratio = the directory's median / the image's median of its per-directory medians; "
      "a segment's fit re-normalises both sides over the directories that hold it.")
    p("  the pairs are not independent (an image in two directories gives two points "
      "mirrored about 1): the interval is indicative.")
    ldir = defaultdict(list)
    for log, r in loader_rows:
        if r["booting"] is not None:
            ldir[os.path.dirname(log)].append(r["booting"])
    img = defaultdict(lambda: defaultdict(list))
    for k in kboots:
        img[image_key(k)][k["dir"]].append(k)
    keys = [key for key in sorted(img) if sum(1 for d in img[key] if ldir.get(d)) >= 2]
    pairs = defaultdict(list)      # segment -> [(x, y, key, dir)]
    seg_len = defaultdict(list)
    for key in keys:
        dirs = sorted(d for d in img[key] if ldir.get(d))
        lmed = {d: statistics.median(ldir[d]) for d in dirs}
        l0 = statistics.median(lmed.values())
        fw = "vendor" if key == "vendor" else "rlxfw"
        ids = {l.id for l in TABLES[fw]}
        segs = [s for s in KERNEL_SEGS if s.a in ids and s.b in ids]
        smed = {}
        for s in segs:
            for d in dirs:
                v = [k["seg"][s.id][0] for k in img[key][d] if s.id in k["seg"]]
                if v:
                    smed[(s.id, d)] = (statistics.median(v), len(v))
        note = ("  -- `none` pools every build before RLXFW-ID0 existed: not one image"
                if key.endswith("/none") else "")
        p("  image %s: %d directories%s" % (key, len(dirs), note))
        p("    %-20s %-24s %s   %s" % (
            "quantity", "from -> to",
            "  ".join("%-22s" % os.path.basename(d) for d in dirs), "image median"))
        p("    %-20s %-24s %s   %.4f" % ("loader.booting", "booting -> chipname", "  ".join(
            "%-22s" % ("%.4f x%.3f (%d)" % (lmed[d], lmed[d] / l0, len(ldir[d])))
            for d in dirs), l0))
        for d in dirs:
            tsv.add(record="scale", image=key, directory=d, quantity="loader.booting",
                    n=len(ldir[d]), median=lmed[d], ratio=lmed[d] / l0)
        for s in segs:
            have = [d for d in dirs if (s.id, d) in smed]
            if len(have) < 2:
                continue
            s0 = statistics.median(smed[(s.id, d)][0] for d in have)
            l0s = statistics.median(lmed[d] for d in have)
            if s0 <= 0:
                continue
            cells = []
            for d in dirs:
                if (s.id, d) in smed:
                    m, n = smed[(s.id, d)]
                    cells.append("%-22s" % ("%.4f x%.3f (%d)" % (m, m / s0, n)))
                    pairs[s.id].append((math.log(lmed[d] / l0s), math.log(m / s0), key, d))
                    tsv.add(record="scale", image=key, directory=d, quantity=s.id,
                            **{"from": s.a}, to=s.b, n=n, median=m, ratio=m / s0,
                            note="loader ratio over the same directories %.6f" % (lmed[d] / l0s))
                else:
                    cells.append("%-22s" % "--")
            seg_len[s.id].append(s0)
            p("    %-20s %-24s %s   %.4f" % (s.id, "%s -> %s" % (s.a, s.b),
                                            "  ".join(cells), s0))

    def f(v, w=7, d=3):
        return ("%*.*f" % (w, d, v)) if v is not None else "%*s" % (w, "--")

    # The two verdict columns are the conditions at the top of this function,
    # applied mechanically -- `--` where a condition does not apply.
    for title, keep, tag in (
            ("over every (image, directory) pair", lambda q: True, "all"),
            ("without id0=none, which pools several builds and is not one image",
             lambda q: not q[2].endswith("/none"), "all-but-none")):
        p("  fit %s: ln(segment ratio) on ln(loader ratio), least squares with an "
          "intercept" % title)
        p("    %-20s %-24s %8s %6s %7s %18s %7s  %-8s %s" % (
            "segment", "from -> to", "typical", "pairs", "slope", "95 % interval", "r",
            "H-prop", "H-add"))
        for s in KERNEL_SEGS:
            pr = [q for q in pairs.get(s.id, []) if keep(q)]
            if not pr:
                continue
            b, lo, hi, r = ols([q[0] for q in pr], [q[1] for q in pr])
            typ = statistics.median(seg_len[s.id])
            if lo is None:
                hp = ha = "--"
            else:
                hp = "refuted" if lo <= 0 <= hi else "stands"
                ha = ("--" if typ < 1.0 else
                      ("refuted" if not (lo <= 0 <= hi) else "stands"))
            p("    %-20s %-24s %8.3f %6d %s %s %s  %-8s %s" % (
                s.id, "%s -> %s" % (s.a, s.b), typ, len(pr), f(b),
                ("%8.3f .. %-7.3f" % (lo, hi)) if lo is not None else "%18s" % "--",
                f(r), hp, ha))
            tsv.add(record="scalefit", image=tag, quantity=s.id, n=len(pr), slope=b,
                    ci_lo=lo, ci_hi=hi, r=r, median=typ,
                    note="H-prop %s; H-add %s" % (hp, ha))
    if not pairs:
        p("    no image occurs in two directories that also hold loader boots: nothing to fit")
    p("")


# ------------------------------------------------------------------- probe
def load_events(prefix):
    """-> [(t_mono, kind, {key: value}, line number)] from PREFIX.events."""
    path = prefix + ".events"
    if not os.path.isfile(path):
        raise Refused("no %s" % path)
    ev = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            try:
                t = float(parts[0])
            except ValueError:
                raise Refused("%s:%d: the first field is not a t_mono: %r" % (path, n, s))
            if len(parts) < 2:
                raise Refused("%s:%d: no kind after the t_mono: %r" % (path, n, s))
            kv = {}
            for tok in parts[2:]:
                if "=" not in tok:
                    raise Refused("%s:%d: `%s` is not key=value" % (path, n, tok))
                a, b = tok.split("=", 1)
                kv[a] = b
            ev.append((t, parts[1], kv, n))
    return ev


def probe_join(log, prefix, force):
    corpus = Corpus()
    if not os.path.isfile(log):
        raise Refused("no such capture: %s" % log)
    meta = corpus.meta(log)
    if not meta:
        raise Refused("%s has no readable .meta.json beside it" % log)
    if meta.get("clock") != "CLOCK_MONOTONIC":
        raise Refused("%s's .meta.json does not declare clock CLOCK_MONOTONIC (it says %r)"
                      % (log, meta.get("clock")))
    t0 = meta.get("t0_mono")
    end = meta.get("end_mono")
    if not isinstance(t0, (int, float)) or isinstance(t0, bool):
        raise Refused("%s's .meta.json has no t0_mono -- true of every capture committed "
                      "before P2-1 -- and an origin is not guessed from started_wallclock, "
                      "which is whole seconds on another clock" % log)
    if not isinstance(end, (int, float)) or isinstance(end, bool):
        raise Refused("%s's .meta.json has t0_mono but no end_mono: the capture's window "
                      "is not closed" % log)
    sent_s = meta.get("sent_s")
    if sent_s is not None and (not isinstance(sent_s, (int, float)) or isinstance(sent_s, bool)):
        raise Refused("%s's sent_s is %r, neither a number nor null" % (log, sent_s))
    pmeta_path = prefix + ".meta.json"
    try:
        with open(pmeta_path, encoding="utf-8") as fh:
            pmeta = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refused("cannot read %s: %s" % (pmeta_path, exc))
    if not isinstance(pmeta, dict) or pmeta.get("tool") != "hostprobe":
        raise Refused("%s is not a hostprobe .meta.json" % pmeta_path)
    if pmeta.get("clock") != "CLOCK_MONOTONIC":
        raise Refused("%s does not declare clock CLOCK_MONOTONIC (it says %r)"
                      % (pmeta_path, pmeta.get("clock")))
    events = load_events(prefix)
    rec = kernel_record(corpus, log, force)
    if rec is None:
        raise Refused("%s holds no `decompressing kernel:`: there is no boot to join" % log)
    if rec["error"] and not rec["seg"]:
        raise Refused("%s cannot be timed: %s" % (log, rec["error"]))

    out = kernel_lines(rec)
    window = (0.0, end - t0)
    counts = defaultdict(int)
    considered = []
    for t, kind, kv, n in sorted(events, key=lambda e: (e[0], e[3])):
        s = t - t0
        if s < window[0] or s > window[1]:
            counts["outside the capture's window"] += 1
            continue
        if sent_s is not None and s < sent_s:
            counts["before sent_s"] += 1
            continue
        counts["considered"] += 1
        considered.append((s, kind, kv, n))
    host = {}
    for s, kind, kv, n in considered:
        if kind == "icmp-reply":
            host.setdefault("net.icmp_first", (s, "seq=%s line %d" % (kv.get("seq"), n)))
        elif kind == "tcp" and kv.get("result") == "ok":
            host.setdefault("net.tcp:%s_first" % kv.get("port"),
                            (s, "port=%s line %d" % (kv.get("port"), n)))
        elif kind == "neigh" and kv.get("state") in NUD_UP:
            host.setdefault("net.neigh_first", (s, "state=%s line %d" % (kv.get("state"), n)))
        elif kind == "udp":
            host.setdefault("net.udp_first", (s, "port=%s line %d" % (kv.get("port"), n)))
    ps, pe = pmeta.get("start_mono"), pmeta.get("end_mono")
    out.append("join  %s  (hostprobe, %d event(s): %s)" % (
        prefix + ".events", len(events),
        ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items()))))
    out.append("  frame: s = t_mono - t0_mono, t0_mono %.6f; the capture's window is "
               "0 .. %.6f s; sent_s %s" % (t0, window[1],
                                          ("%.6f" % sent_s) if sent_s is not None else "null"))
    if isinstance(ps, (int, float)) and isinstance(pe, (int, float)):
        cs, ce = ps - t0, pe - t0
        out.append("  the probe ran %.6f .. %.6f s in this frame" % (cs, ce))
        lo = sent_s if sent_s is not None else 0.0
        if cs > lo or ce < window[1]:
            out.append("  NOTE: the probe did not run over the whole window, so an absent "
                       "host landmark is `not seen while probing`, not `did not happen`")
    else:
        out.append("  NOTE: the probe's start_mono/end_mono are not recorded, so an absent "
                   "host landmark cannot be told from a probe that was not running")
    out.append("  the channel offset between console and host is NOT applied: D8 measures "
               "it, this tool does not")
    for name in ("net.icmp_first", "net.neigh_first", "net.udp_first"):
        if name in host:
            out.append("  host %-18s s %11.6f  (%s)" % (name, host[name][0], host[name][1]))
        else:
            out.append("  host %-18s --" % name)
    for name in sorted(k for k in host if k.startswith("net.tcp:")):
        out.append("  host %-18s s %11.6f  (%s)" % (name, host[name][0], host[name][1]))
    for s in NET_SEGMENTS:
        if s.a in rec["at"] and s.b in host:
            val = "%.6f" % (host[s.b][0] - rec["at"][s.a][1])
        else:
            val = "--"
        out.append("  net  %-20s %-11s -> %-16s %-15s %s" % (s.id, s.a, s.b, s.cls, val))
    print("\n".join(out))
    return 0


# -------------------------------------------------------------- the loader
def loader_report(args, logs):
    corpus = Corpus()
    raw_rows = [(l, analyse(l, args.anchor)) for l in logs]
    rows = [x for _, x in raw_rows if x]
    good = [r for r in rows if "error" not in r]
    # 🔴 A capture that never became a row is invisible to `unknown`, which
    # counts rows whose CLASS could not be decided.  量 2026-09-01:
    # `bench/2026-09-01/Y0-A` -- a capture that opened mid-boot, so it holds no
    # `Booting` -- was dropped here and the summary still read `0 unknown`.
    # Naming them is the difference between a population and whatever survived
    # the filter.
    unread = [l for l, x in raw_rows if x is None]
    errored = [(r.get("name", "?"), r["error"]) for r in rows if "error" in r]
    # THREE populations now, and only one of them is a defect.  A `DW` reply
    # has no boot text and is correctly not a row.  A KERNEL boot with no loader
    # boot in its capture -- every `J 80500000` -- is not a loader row either,
    # and is counted here and timed by `--kernel`/`--retro`.  A capture holding
    # loader text and no `Booting` is a boot this tool could not place, and that
    # is the one a reader needs named.  量 2026-09-23 over bench: 142, 3, and
    # the rest -- where the tool had said "22 hold boot text", 19 of them loud
    # kernel boots misread through bare `chipName` (see BOOT_TEXT).
    orphan_boots = []
    kern = 0
    for l in unread:
        try:
            raw = corpus.raw(l)
        except OSError:
            orphan_boots.append((l, "unreadable"))
            continue
        if DECOMP_TEXT in raw:
            kern += 1
        elif any(m in raw for m in BOOT_TEXT) or any(m in raw for m in KERNEL_TEXT):
            if any(m in raw for m in BOOT_TEXT):
                orphan_boots.append((l, orphan_why(corpus, l)))
            else:
                orphan_boots.append((l, "kernel text but no `decompressing kernel:` -- "
                                        "not a boot this tool can time"))
    if unread or errored:
        print("NOT CLASSIFIED: %d capture(s) produced no row; %d are kernel boots with no "
              "loader boot in the capture (`--kernel` and `--retro` time them), %d hold "
              "boot text this tool cannot place (named below), %d hold no boot text" % (
                  len(unread), kern, len(orphan_boots), len(unread) - kern - len(orphan_boots)))
        for l, why in orphan_boots:
            print("    %s -- %s" % (l, why))
        for n, e in errored:
            print("    %s -- %s" % (n, e))
        print()
    if not good:
        print("REFUSING: no capture with boot text and a .timing under %s"
              % " ".join(args.path), file=sys.stderr)
        return 2

    print("anchor %s = %s" % (args.anchor, ANCHORS[args.anchor][1]))
    print("`~` means both anchor bytes arrived in one read(), so the value is an upper bound")
    print()
    print("%-14s %-16s %-5s %-3s %8s %8s %8s %8s" % (
        "power cycle", "capture", "boot", "b0", "artifact", "booting", "banner", "entry"))
    print("-" * 88)
    last = None
    for r in sorted(good, key=lambda x: (x["cycle"], x["name"])):
        cyc = r["cycle"] if r["cycle"] != last else ""
        last = r["cycle"]
        print("%-14s %-16s %-5s %-3s %8s %8s %8s %8s" % (
            cyc, r["name"], r["boot"], r["artifact_byte"] or "--",
            fmt(r["artifact"], r.get("artifact_exact", True)),
            fmt(r["booting"], r.get("booting_exact", True)),
            fmt(r["banner"], r.get("banner_exact", True)),
            fmt(r["entry"])))
    for r in rows:
        if "error" in r:
            print("%-31s %s" % (r["log"], r["error"]))

    out = []
    print()
    print("pooled")
    stat("artifact (cold only by def.)", [r["artifact"] for r in good if r["artifact"] is not None], out)
    stat("booting, all", [r["booting"] for r in good if r["booting"] is not None], out)
    stat("booting, cold", [r["booting"] for r in good if r["booting"] is not None and r["boot"] == "cold"], out)
    stat("booting, warm", [r["booting"] for r in good if r["booting"] is not None and r["boot"] == "warm"], out)
    stat("banner, all", [r["banner"] for r in good if r["banner"] is not None], out)
    stat("entry, warm", [r["entry"] for r in good if r["entry"] is not None and r["boot"] == "warm"], out)
    print("\n".join(out))

    # WITHIN ONE POWER CYCLE, which is the comparison that has no day in it.
    print()
    print("within one power cycle -- `booting`, cold boot against the warm resets that followed it")
    any_pair = False
    for cyc in sorted({r["cycle"] for r in good}):
        c = [r["booting"] for r in good if r["cycle"] == cyc and r["boot"] == "cold" and r["booting"]]
        w = [r["booting"] for r in good if r["cycle"] == cyc and r["boot"] == "warm" and r["booting"]]
        if not c or not w:
            print("  %-14s cold n=%d warm n=%d -- no pair, nothing to compare" % (cyc, len(c), len(w)))
            continue
        any_pair = True
        print("  %-14s cold %s   warm %s   cold - max(warm) = %+.4f s" % (
            cyc, " ".join("%.4f" % x for x in c), " ".join("%.4f" % x for x in w),
            min(c) - max(w)))
    if not any_pair:
        print("  NOTE: no power cycle holds both a cold boot and a warm reset, so nothing"
              " here separates the two from a between-day effect")

    n_cold = sum(1 for r in good if r["boot"] == "cold")
    n_warm = sum(1 for r in good if r["boot"] == "warm")
    print()
    print("classified by the loader's own line (C-8): %d cold, %d warm, %d unknown"
          % (n_cold, n_warm, len(good) - n_cold - n_warm))
    if n_cold == 0 or n_warm == 0:
        print("NOTE: one side of the split is empty, so nothing here discriminates")
    return 0


def kernel_report(logs, force, tsv_path):
    corpus = Corpus()
    recs, skipped = [], []
    for l in logs:
        try:
            k = kernel_record(corpus, l, force)
        except OSError as exc:
            raise Refused("cannot read %s: %s" % (l, exc))
        if k is None:
            skipped.append(l)
        else:
            recs.append(k)
    if not recs:
        raise Refused("no capture under %s holds `decompressing kernel:`"
                      % " ".join(logs[:3] + (["..."] if len(logs) > 3 else [])))
    out = legend_lines()
    out.append("")
    for k in sorted(recs, key=lambda k: (k["dir"], k["name"])):
        out.extend(kernel_lines(k))
        out.append("")
    cnt = defaultdict(int)
    for k in recs:
        cnt[fwvar(k) if k["fw"] in ("vendor", "rlxfw") else "?"] += 1
    out.append("kernel boots: %d (%s); %d other capture(s) hold no `decompressing kernel:`"
               % (len(recs), ", ".join("%s %d" % kv for kv in sorted(cnt.items())),
                  len(skipped)))
    print("\n".join(out))
    if tsv_path:
        tsv = Tsv()
        for k in recs:
            for s in SEGMENTS:
                if s.id in k["seg"]:
                    v, ex = k["seg"][s.id]
                    tsv.add(record="seg", firmware=k["fw"], variant=k["variant"],
                            **{"class": k["class"]}, image=k["id0"], directory=k["dir"],
                            capture=k["log"], quantity=s.id, **{"from": s.a}, to=s.b,
                            seg_class=s.cls, n=1, value=v, note="" if ex else "one read")
        tsv.write(tsv_path, ["boot-timeline.py --kernel, tool sha256 %s" % tool_digest()])
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="*", default=["bench"])
    ap.add_argument("--anchor", choices=sorted(ANCHORS), default="C")
    ap.add_argument("--all-anchors", action="store_true",
                    help="print `booting` under every anchor, for comparing "
                         "against a number whose anchor is not recorded")
    ap.add_argument("--kernel", action="store_true",
                    help="every kernel boot under the paths, landmark by landmark")
    ap.add_argument("--retro", action="store_true",
                    help="the retro report over every capture under the paths")
    ap.add_argument("--tsv", metavar="FILE",
                    help="with --retro or --kernel: also write the rows as TSV")
    ap.add_argument("--probe", metavar="PREFIX",
                    help="join ONE capture with a hostprobe PREFIX.events")
    ap.add_argument("--firmware", choices=["vendor", "rlxfw"],
                    help="with --kernel or --probe: use this table instead of "
                         "detecting the firmware (a control, not a correction)")
    ap.add_argument("--legend", action="store_true",
                    help="print the landmark and segment tables")
    args = ap.parse_args()

    try:
        problems = check_tables()
        if problems:
            raise Refused("the tables are inconsistent: %s" % "; ".join(problems))
        modes = [m for m in ("all_anchors", "kernel", "retro", "probe", "legend")
                 if getattr(args, m)]
        if len(modes) > 1:
            raise Refused("choose one of --all-anchors, --kernel, --retro, --probe, "
                          "--legend (got %s)" % ", ".join("--" + m.replace("_", "-")
                                                          for m in modes))
        if args.tsv and not (args.retro or args.kernel):
            raise Refused("--tsv goes with --retro or --kernel")
        if args.firmware and not (args.kernel or args.probe):
            raise Refused("--firmware goes with --kernel or --probe")
        if args.legend:
            print("\n".join(legend_lines()))
            return 0
        if args.probe:
            if len(args.path) != 1 or not args.path[0].endswith(".log"):
                raise Refused("--probe joins exactly ONE capture: give its .log path")
            return probe_join(args.path[0], args.probe, args.firmware)
        missing = [p for p in args.path if not os.path.exists(p)]
        if missing:
            raise Refused("no such path: %s" % ", ".join(missing))
        logs = collect_logs(args.path)
        if args.retro:
            return retro(args.path, args.tsv)
        if args.kernel:
            return kernel_report(logs, args.firmware, args.tsv)
    except Refused as exc:
        print("REFUSING: %s" % exc, file=sys.stderr)
        return 2

    if args.all_anchors:
        print("booting, under every anchor definition")
        print("%-40s %-5s %8s %8s %8s %8s" % ("capture", "boot", *sorted(ANCHORS)))
        pop = {k: [] for k in ANCHORS}
        for l in logs:
            row = [analyse(l, k) for k in sorted(ANCHORS)]
            if row[0] is None or "error" in row[0]:
                continue
            print("%-40s %-5s %8.4f %8.4f %8.4f %8.4f" % (
                l, row[0]["boot"], *[r["booting"] for r in row]))
            for k, r in zip(sorted(ANCHORS), row):
                pop[k].append(r["booting"])
        print()
        for k in sorted(ANCHORS):
            print("  anchor %s  %-46s n=%d  %.4f .. %.4f" % (
                k, ANCHORS[k][1], len(pop[k]), min(pop[k]), max(pop[k])))
        return 0

    return loader_report(args, logs)


if __name__ == "__main__":
    try:
        rc = main()
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader stopped early (`| head`, `awk '...; exit'`).  That is not
        # this tool's failure and is no reason for a traceback; stdout goes to
        # devnull so the interpreter's own last flush does not raise again.
        # 量 2026-09-23: test-boot-timeline B12's awk printed
        # `BrokenPipeError` here before this existed.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        rc = 1
    sys.exit(rc)
