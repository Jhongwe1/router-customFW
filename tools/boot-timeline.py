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
"""

import argparse
import bisect
import glob
import os
import statistics
import sys

BOOTING = b"Booting..."
CHIPNAME = b"chipName"
BANNER = b"---RealTek(RTL8196E)"
# Every line the loader prints on the way up.  Used ONLY to tell a boot
# capture that could not be placed from a `DW` reply that was never a boot.
# 量 2026-09-01: testing only for `chipName`/BANNER missed `Y0-A`, whose
# first bytes are `P0phymode=` because the capture opened after both had
# gone past -- the detector missed the case it was written for.
BOOT_TEXT = (CHIPNAME, BANNER, b"ramSize:", b"P0phymode=",
             b"---Ethernet init Okay!")
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


def analyse(log, anchor):
    raw = open(log, "rb").read()
    if BOOTING not in raw:
        return None
    tpath = log[:-4] + ".timing"
    if not os.path.exists(tpath):
        return {"log": log, "error": "no .timing beside it"}
    tm = read_timing(tpath)
    if not tm:
        return {"log": log, "error": ".timing is empty"}
    offs = [x[0] for x in tm]

    r = {"log": log, "cycle": os.path.basename(os.path.dirname(log)),
         "name": os.path.basename(log)[:-4]}

    i = raw.find(RAMSIZE)
    if i < 0:
        r["boot"] = "?"
    elif raw.find(WATCHDOG, i, i + 64) >= 0:
        r["boot"] = "warm"
    else:
        r["boot"] = "cold"

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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="*", default=["bench"])
    ap.add_argument("--anchor", choices=sorted(ANCHORS), default="C")
    ap.add_argument("--all-anchors", action="store_true",
                    help="print `booting` under every anchor, for comparing "
                         "against a number whose anchor is not recorded")
    args = ap.parse_args()

    logs = []
    for p in args.path:
        if os.path.isdir(p):
            logs += sorted(glob.glob(os.path.join(p, "**", "*.log"), recursive=True))
        else:
            logs.append(p)

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
    # Two populations, and only one of them is a defect.  A `DW` reply has no
    # boot text at all and is correctly not a row; a capture that HAS boot text
    # and no `Booting` anchor is a boot this tool could not place, and that is
    # the one a reader needs named.  量 2026-09-01: 343 of the former, 1 of the
    # latter (`Y0-A`, opened after the board had started printing).
    orphan_boots = []
    for l in unread:
        try:
            with open(l, "rb") as fh:
                raw = fh.read()
        except OSError:
            orphan_boots.append((l, "unreadable"))
            continue
        if BOOTING not in raw and any(m in raw for m in BOOT_TEXT):
            orphan_boots.append((l, "boot text but no `Booting` anchor -- the "
                                    "capture opened after the board started"))
    if unread or errored:
        print("NOT CLASSIFIED: %d capture(s) produced no row; %d of them hold "
              "boot text" % (len(unread), len(orphan_boots)))
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


if __name__ == "__main__":
    sys.exit(main())
