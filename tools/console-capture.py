#!/usr/bin/env python3
"""Capture the console byte-exactly and timestamp it, so an interval on the wire
becomes a number instead of a stopwatch reading.

Why this exists
---------------
Two cells needed an instrument that did not exist.

``RUNSHEET.md`` ``A2`` asks for the full boot log.  ``console-dump.py catch``
prints the banner line and discards the rest of the pre-prompt stream, and
nothing writes it to a file, so the cell is unsatisfiable by the tool the sheet
names -- recorded in ``PROGRESS.md`` on 2026-08-23 while running it.

``RUNSHEET.md`` ``D1`` asks how long ``J BFC00000`` takes to come back.  A
stopwatch cannot answer it and neither can the quantity it was aimed at: with
``OVSEL[3:0] = 0000`` the watchdog times out in 2^15 base-clock ticks, which
against the 199.48 MHz measured by ``E2`` is 164 us undivided or 2.30 ms through
``CDBR``'s divisor of 14.  Both are three orders of magnitude under a human
reaction time, so **any number a stopwatch produces here is the post-reset boot
time wearing the watchdog's name.**  The boot time is the quantity ``C-8``'s
owner actually needs -- it is what R4's ``bench-ci`` sets its timeout from --
and it is measurable, from the interval between two strings in the stream.

What it does not do
-------------------
It is not a terminal.  There is no keyboard passthrough: the only thing it can
send is what ``--send`` was given on the command line, once, verbatim, before it
goes read-only, and the exact bytes go into the metadata.  ``RUNSHEET.md`` rule 4
says a command is typed from the sheet or from a tool and never re-stated by
hand; on 2026-08-23 that rule was broken by re-stating ``C5`` in a chat table,
and a leading space from the table cell NULed ``argv[0]`` at the tokeniser
(``0x80407248`` stores ``argv[i]`` before testing for a separator), so the
dispatcher matched nothing.  A command that arrives here as an argv element
cannot pick up leading whitespace on the way.

Hand-typed sections stay in ``picocom``.  This does not replace it and does not
try to; one serial port means one program, and the two have different jobs.

The two output files, and why they are two
------------------------------------------
``PREFIX.log``
    **Raw bytes, byte for byte, nothing added and nothing removed.**  Opened
    binary, written binary.  The device's ``\\r\\n`` stays ``\\r\\n``.

``PREFIX.timing``
    ``<byte-offset> <seconds-since-start>`` per read, one per line.

They are two files because on 2026-08-23 two separate things were caught
rewriting the bench transcripts on the way into git -- ``.gitattributes``'s
``* text=auto eol=lf``, which would have normalised 20 bytes out of ``B.log`` and
47 out of ``E.log``, and a habitual ``sed 's/\\r$//'`` which already had.  A
transcript that has been edited is not a transcript.  **Timestamps interleaved
into the log would be a third thing editing it**, this time by the instrument
that produced it, so they go beside it and the log stays the thing the device
sent.  ``bench/**`` is marked ``-text``; ``.timing`` and ``.meta.json`` are
derived and may be normalised without consequence.

What bounds the resolution, and it is not the baud rate
--------------------------------------------------------
A timestamp records when a chunk reached userspace, not when its first byte
reached the UART.  One character at 38400 8N1 is 260 us, but the CP2102 driver
coalesces on a latency timer -- commonly 1-16 ms, **unmeasured on this host** --
so the useful floor is that timer and not the line rate.

For ``D1`` this does not matter: the quantity is a boot, order of a second, and
the error is three orders of magnitude below it.  For anything under ~50 ms this
tool is the wrong instrument, and the watchdog timeout it was almost pointed at
is exactly such a quantity.  Stated here rather than discovered later.

``--esc`` and ``--esc-after`` are not the same window
-----------------------------------------------------
``--esc N`` streams ESC for N seconds **before** the send, which is what
catching a cold boot needs -- ``B1 A1`` streams from before power is applied.
``--esc-after N`` streams for N seconds **after** it, which is what ``D1``
needs: send ``J BFC00000``, then catch the ESC window of the reboot that
command causes, inside the same capture, so the interval from the jump to the
banner is one file's timing rather than two wall-clocks a second apart.

Without the second one ``D1`` boots the vendor kernel, ``D2`` and ``D2b`` lose
the prompt they have to read, and getting it back costs a power cycle -- which
destroys the warm-reset condition ``D2b`` exists to test.

``--idle`` is a trap for the one measurement this was built for
----------------------------------------------------------------
``--idle N`` stops the capture after N seconds with no bytes.  **The interval
``D1`` measures is a silence** -- ``J BFC00000`` echoes, the board goes quiet, the
banner arrives -- so an ``--idle`` shorter than that silence ends the capture
inside the gap and the reading becomes *"the banner never came"*.  Found by this
tool's own self-test on 2026-08-24, which had ``--idle 0.8`` against a played
1.50 s gap and truncated at 29 bytes; it is now case ``N5`` there.

So for ``D1``: use ``--seconds``, not ``--idle``, and make it comfortably longer
than the boot.  ``--idle`` is for captures that end when the device stops talking
and where no silence is part of the answer.

Every ESC loop ends with a CR, and that is the tool keeping a rule instead of
------------------------------------------------------------------------------
a sheet stating one
-------------------
``RUNSHEET.md`` seating 2 rule 2: *the trigger is any capture whose last byte
written to the port was not a CR -- i.e. any capture that ran ``--esc`` or
``--esc-after``.*  Until 2026-08-24 that was enforced by a **flush cell** typed
after every such capture (``flush``, ``flush-cont``, ``flush-b7c``,
``flush-d1``, ``flush-d3``), and the arithmetic under ``flush-d1``'s row is why
it could not be skipped: the ESC stream leaves ``N mod 128`` bytes sitting in
the loader's ``readline`` buffer, ``N`` is not knowable in advance, and the next
command line is appended to that residue.  At the measured residues -- 12 after
``A-catch``, ``985 = 7*128 + 89`` after ``B7c`` -- the next command is either
mangled or cut at the 128-byte cliff.

So the loop writes its own terminator.  After ``--esc`` and again after
``--esc-after``, one CR, then read until the prompt it causes comes back (or
``--cr-settle`` seconds elapse, whichever is first).  **The wait is not
politeness**: with ``--esc`` the very next thing written is the command line,
and the loader is not in ``readline`` while it is printing
``Unknown command !\\r\\n<RealTek>``.

Four things this does NOT do, stated here rather than discovered at the bench:

* **It does not cover a USB re-enumeration.**  Rule 2 has a second half -- the
  first command after the console adapter re-enumerates is echoed and not acted
  on (``CONT``/``flush-cont``/``CONT2``, 2026-08-24) -- and no capture can see
  an event that happened while it was not running.  A throwaway capture after a
  re-attach is still required.  This removes the ESC half of the rule only.
* **It cannot create the 128-byte case.**  ``readline`` returns unterminated
  only when 128 non-CR bytes fill the buffer; a CR always takes the terminated
  path, whatever the residue length.  So the CR can end a line early and can
  never lengthen one into the cliff.
* **The prompt it waits for may be the previous line's.**  Only bytes that
  arrive after the CR is written are searched, but the ESC stream emits a prompt
  of its own every 128 bytes, and one still in flight when the CR goes out is
  indistinguishable from the CR's own reply.  The cost is that the settle ends a
  few ms early; the CR itself has still been written.  *Inferred, pending a
  bench capture with ``cr.prompt_seen`` beside the byte counts.*
* **It changes the ESC accounting inside the capture's own log.**  An ``--esc``
  capture used to partition exactly: ``echoed = 128 * n + r``, one
  ``Unknown command !`` per completed 128-byte fill and ``r`` bytes left over --
  the measurement ``docs/loader-command-semantics.md`` rests the 128-byte
  finding on, ``[128*7, 12]`` and ``[128*5, 90]`` in the two ``A-catch``
  captures.  Under 1.2 the CR terminates the leftover, so the tail of the log
  carries one reply the *instrument* caused -- and **which reply depends on the
  residue**: ``r > 0`` gives one more ``Unknown command !`` than completed
  fills, while ``r == 0`` gives a **bare prompt and no ``Unknown command !``**
  at all, because an empty line is what ``bench/2026-08-24b/flush-cont.log``
  measured.  So the count is ``n`` or ``n + 1``, not always ``n + 1``, and
  subtracting one unconditionally on a boundary capture yields ``n - 1`` fills
  with a residue of ``128 + r`` -- outside ``0 <= r < 128``, which is
  ``docs/loader-command-semantics.md``'s own refutation condition for the
  128-byte finding, tripped on a capture where nothing was wrong.
  ``cr.<loop>.log_offset`` in the metadata is the byte offset where the
  instrument's own bytes begin, and ``tool_version`` is how a 1.1 capture is
  told from a 1.2 one.

``--no-cr`` turns it off, and exists so the suite's positive case is measuring
the behaviour rather than the tool's habits -- the same reason ``--esc-after 0``
is a case (``N6``) and not an assumption.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import sys
import time

DEFAULT_BAUD = 38400
ESC = b"\x1b"
CR = b"\r"

# The loader's prompt, byte for byte, from every capture in bench/. It is what
# the CR after an ESC loop is waited for; it is not a parser and nothing turns
# on it being found -- see cr.prompt_seen in the metadata.
def _record_esc(meta, which, requested, writes, window):
    """Record what the ESC heartbeat ACTUALLY was, not what it was asked for.

    `writes` is counted at the point of `ser.write`, so it is the number of
    escapes that left this process; `window` is wall-clock across the loop.
    The quotient is therefore an upper bound on the period the device saw --
    it includes this process's own scheduling, which is exactly the term that
    made a requested 20.00 ms come out at 20.35 (SPEC.md CLK-08).

    A requested period below what the host can deliver does not fail: it comes
    out as an achieved period visibly larger than the request, which is the
    honest answer and is what case N16 of the self-test checks.
    """
    meta.setdefault("esc", {})[which] = {
        "requested_period_s": requested,
        "writes": writes,
        "window_s": round(window, 6),
        "achieved_period_s": round(window / writes, 6) if writes else None,
    }


PROMPT = b"<RealTek>"

DEFAULT_CR_SETTLE = 2.0

# How long each ESC loop waits between one ESC and the next.  This is the GRID
# every interval measured off ESC echoes is quantised to, and it is the whole
# reason CLK-08b could not be settled: the proportional and the fixed residual
# hypotheses differ by about 15 ms, which is smaller than one tick of it.
#
# 0.02 stays the default so that every capture already taken keeps meaning what
# it meant.  The CLK-08b cell passes --esc-period 0.002.  At 38400 8N1 an ESC
# out plus its echo back is two characters = 521 us, so a 2 ms period leaves a
# factor of four of headroom -- but headroom is an argument, and what goes in
# the metadata is the period the run ACHIEVED, measured, beside the one it
# asked for.  SPEC.md CLK-08 records the previous grid as 20.35 / 20.32 ms
# against a requested 20.00, which is exactly why the achieved value is the one
# worth having.
DEFAULT_ESC_PERIOD = 0.02

# Bumped when the bytes this tool WRITES to the port change. A capture is
# evidence, and what the instrument did to produce it is part of the reading:
# 1.1 and earlier ended an ESC loop with an ESC, 1.2 ends it with a CR.
TOOL_VERSION = "1.3"


def _fail(msg: str) -> "NoReturn":  # noqa: F821
    print(f"console-capture: {msg}", file=sys.stderr)
    raise SystemExit(2)


# --------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------

def _check_send(value):
    """Validate --send before anything touches the device.

    Order matters and it is the point of this being a separate function: a tool
    that opens the port and then decides to refuse has already interacted with
    the device it was refusing to interact with. Caught by this tool's own
    self-test on 2026-08-24, where N4 got a pyserial traceback instead of the
    refusal, because the check sat below serial.Serial().
    """
    if value is None:
        return None
    if value != value.strip():
        _fail(
            f"--send {value!r} has leading or trailing whitespace. "
            "The tokeniser at 0x80407248 stores argv[i] before testing for a "
            "separator, so a leading space NULs argv[0] and the dispatcher "
            "matches nothing (Unknown command !). Refusing."
        )
    if "\n" in value or "\r" in value:
        _fail("--send takes one line; the carriage return is added here")
    if any(ord(c) > 0x7F for c in value):
        _fail(
            f"--send {value!r} is not ASCII. capture() encodes the line with "
            ".encode('ascii') AFTER the port is open, so a non-ASCII character "
            "would raise there -- with the port already opened, which is the "
            "ordering defect N4 exists to prevent."
        )
    n = len(value)
    if n >= 128:
        _fail(
            f"--send is {n} characters and the loader's console line buffer is "
            "128 bytes. Refusing.\n"
            "  Measured on the device 2026-08-24: exactly 128 ESC bytes came\n"
            "  back `Unknown command !`, seven times -- bench/2026-08-24/A-catch.log.\n"
            "  Read out of the image: the command loop at 0x80409190/0x804091A0\n"
            "  does memset(buf, 0, 128) then readline(buf, 128, 1), and readline\n"
            "  writes its NUL only on the CR path (0x804070FC) -- the length-limit\n"
            "  path (0x80407194, count < 128) returns without one. So a line that\n"
            "  FILLS the buffer is unterminated, and the tokeniser at 0x80407248\n"
            "  scans past sp+143 into the saved registers.\n"
            "  The cliff is AT 128 and anything longer is cut to 128, so this is\n"
            "  >= and not ==. Longest safe EW form: 12 values, 119 characters\n"
            "  (11 + 9n < 128). RUNSHEET.md C7; docs/loader-command-semantics.md f."
        )
    return value


def capture(args) -> int:
    _check_send(args.send)
    try:
        import serial  # type: ignore
    except ImportError:
        _fail(
            "pyserial is not importable by this interpreter.\n"
            f"  interpreter: {sys.executable}\n"
            "  Ubuntu ships it as the apt package python3-serial, installed for\n"
            "  /usr/bin/python3.  A virtualenv earlier on $PATH will not see it --\n"
            "  measured 2026-08-24, `python3` on this host resolved to\n"
            "  ~/.venvs/thermal/bin/python3, which has no serial module, while\n"
            "  /usr/bin/python3 has it.  Run this with /usr/bin/python3."
        )

    log_path = args.out + ".log"
    timing_path = args.out + ".timing"
    meta_path = args.out + ".meta.json"
    for p in (log_path, timing_path, meta_path):
        if os.path.exists(p) and not args.force:
            _fail(f"{p} exists. Refusing to overwrite a capture; use --force or a new --out")

    os.makedirs(os.path.dirname(os.path.abspath(log_path)) or ".", exist_ok=True)

    meta = {
        "tool_version": TOOL_VERSION,
        "port": args.port,
        "baud": args.baud,
        "started_wallclock": None,
        "esc_seconds": args.esc,
        "esc_after_seconds": args.esc_after,
        "esc_period_requested_s": args.esc_period,
        # One entry per ESC loop that ran, carrying the ACHIEVED heartbeat:
        # writes, the window they were spread over, and the quotient.  An
        # interval read off ESC echoes is quantised to that quotient, so a
        # capture that does not record it leaves the reader to assume the
        # requested value -- and the requested value has already been wrong by
        # 1.75% (SPEC.md CLK-08: 20.35 ms achieved against 20.00 requested).
        "esc": {},
        # One entry per ESC loop that ran. Absent means the loop did not run;
        # written=false means --no-cr. This is the record of what the
        # instrument wrote, which the .log cannot show -- the .log is what the
        # device said.
        "cr": {},
        "cr_settle_s": args.cr_settle,
        "sent": None,
        "sent_hex": None,
        "stop_reason": None,
        "bytes": 0,
        "duration_s": None,
        "resolution_note": (
            "timestamps are per read() from userspace; the floor is the USB-serial "
            "latency timer (1-16 ms typical, unmeasured on this host), not the "
            "260 us character time at 38400"
        ),
    }

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0)
    except Exception as e:  # SerialException, OSError, termios.error
        _fail(
            f"cannot open {args.port} at {args.baud}: {e}\n"
            "  On WSL the CP2102 is not there until it is attached:\n"
            "    usbipd list                       (find the 10c4:ea60 busid)\n"
            "    usbipd attach --wsl --busid <id>  (from an elevated Windows shell)\n"
            "  Then /dev/ttyUSB0 appears and the dialout group owns it."
        )
    fd = ser.fileno()
    offset = 0
    t0 = time.monotonic()
    meta["started_wallclock"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    last_byte_at = t0
    stop_reason = "interrupted"

    with open(log_path, "wb") as log, open(timing_path, "w", encoding="ascii") as timing:
        timing.write("# offset seconds -- offset is the byte count in .log BEFORE this read\n")

        # The last few KiB read, so the CR's reply can be looked for without
        # re-opening the log. Capped because a 45 s capture is not a buffer.
        tail = bytearray()

        # Which ESC loop is running and has not had its CR yet. Read by the
        # KeyboardInterrupt handler: an interrupt inside an ESC loop would
        # otherwise skip the terminator and leave `N mod 128` bytes in the
        # loader's readline buffer with nothing in the metadata saying so.
        pending_esc = None

        def drain(budget: float) -> None:
            """Read whatever is there for up to `budget` seconds."""
            nonlocal offset, last_byte_at
            deadline = time.monotonic() + budget
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                r, _, _ = select.select([fd], [], [], min(remaining, 0.05))
                if not r:
                    continue
                chunk = ser.read(ser.in_waiting or 1)
                if not chunk:
                    continue
                timing.write(f"{offset} {time.monotonic() - t0:.6f}\n")
                log.write(chunk)
                log.flush()
                timing.flush()
                offset += len(chunk)
                last_byte_at = time.monotonic()
                tail.extend(chunk)
                if len(tail) > 4096:
                    del tail[:-4096]

        def terminate_esc_line(which: str, on_interrupt: bool = False) -> None:
            """End an ESC loop with a CR, and wait for the prompt it causes.

            An ESC loop ends on a wall-clock deadline and writes no terminator,
            so it leaves `N mod 128` bytes in the loader's readline buffer and
            the next command line is appended to them. This writes the
            terminator the loop did not, which is RUNSHEET seating 2 rule 2
            enforced by the instrument instead of by a flush cell -- see the
            module docstring for the two halves of that rule this does NOT
            cover.

            The wait matters for `--esc`, where the command line is the very
            next thing written: the loader is not reading while it prints
            `Unknown command !`, and a command line here runs to 119 characters
            against a UART receive FIFO of *unknown* depth. *Inferred* -- this
            project has measured no FIFO depth on this part, and the reason to
            wait is that the depth is unknown, not that it is known to be small.
            The refutation is cheap and belongs at the bench: send a command
            with no settle immediately after a CR and see whether the loader
            echoes all of it.
            """
            nonlocal pending_esc
            entry = {"written": False, "prompt_seen": None, "waited_s": 0.0}
            meta["cr"][which] = entry
            if on_interrupt:
                entry["on_interrupt"] = True
            if args.no_cr:
                entry["reason"] = "--no-cr"
                pending_esc = None
                return
            # Pull whatever is already on the wire into the log FIRST, so that
            # `tail` holds nothing stale. Without this, a `<RealTek>` sitting in
            # the OS receive buffer when the CR goes out is read a moment later
            # and counted as the CR's own reply -- prompt_seen true, waited_s
            # ~0.05, and the wait recorded as having succeeded when it did not
            # happen. The race is narrowed, not closed: a prompt still in the
            # UART's own FIFO is indistinguishable. *Inferred.*
            drain(0.05)
            del tail[:]           # only what arrives AFTER the CR counts
            # Where in the .log this instrument's own bytes start. The division
            # of labour is "the .log is what the device said"; from here it also
            # holds one reply the tool caused, and this is the anchor that lets
            # a reader -- or `report`'s --to pattern -- tell them apart.
            entry["log_offset"] = offset
            ser.write(CR)
            ser.flush()
            entry["written"] = True
            # Cleared the instant the byte is out, not at the end of the settle:
            # from here an interrupt costs the reply, never the terminator.
            pending_esc = None
            if on_interrupt:
                # The operator asked for this to stop. The CR is the half the
                # NEXT capture depends on and it has been written; take a short
                # drain so its reply lands in this log rather than in that one,
                # and do not spend the full settle.
                try:
                    drain(0.3)
                except KeyboardInterrupt:
                    pass
                entry["prompt_seen"] = PROMPT in tail
                entry["waited_s"] = 0.3
                return
            budget = args.cr_settle
            if args.seconds:
                # Never let the settle push the capture past its own deadline.
                budget = min(budget, max(0.0, args.seconds - (time.monotonic() - t0)))
            entry["settle_budget_s"] = round(budget, 6)
            if budget <= 0.0:
                # `prompt_seen` stays None. False would mean "looked and did not
                # see", which is the reading flush-d1 turns on; this is "never
                # looked", and the two must not share a value. Reachable
                # whenever --seconds is no larger than the ESC window.
                entry["reason"] = ("no settle: --seconds left no budget after the "
                                   "ESC loop. prompt_seen is null, not false")
                print("console-capture: WARNING -- --seconds left no time for the CR "
                      "settle, so nothing was waited for and prompt_seen is null. "
                      "Give --seconds at least --cr-settle more than the ESC window.",
                      file=sys.stderr)
                return
            started = time.monotonic()
            deadline = started + budget
            seen = False
            while time.monotonic() < deadline:
                drain(0.05)
                if PROMPT in tail:
                    seen = True
                    break
            entry["prompt_seen"] = seen
            entry["waited_s"] = round(time.monotonic() - started, 6)

        try:
            if args.esc:
                # The ESC window on this unit is ~4.9 s wide, banner to
                # "Jump to image start", measured 2026-08-18. Streaming from
                # before power-on is what B1 A1 does; it is also what sets
                # gCHKKEY_HIT, which is why B5 read 1 and not 0.
                pending_esc = "esc"
                esc_started = time.monotonic()
                esc_deadline = esc_started + args.esc
                esc_writes = 0
                while time.monotonic() < esc_deadline:
                    ser.write(ESC)
                    esc_writes += 1
                    drain(args.esc_period)
                _record_esc(meta, "esc", args.esc_period, esc_writes,
                            time.monotonic() - esc_started)
                # Before --send, not after: the residue this terminates would
                # otherwise be the front of the command line. Called whether or
                # not --send was given: the A-catch shape is --esc with no
                # command at all, and it is the capture whose 12-byte residue
                # cost A0's first attempt on 2026-08-24.
                terminate_esc_line("esc")

            if args.send is not None:
                # Validated by _check_send() before the port was opened.
                line = args.send.encode("ascii") + b"\r"
                meta["sent"] = args.send
                meta["sent_hex"] = line.hex()
                ser.write(line)
                ser.flush()

            if args.esc_after:
                # ``--esc`` streams BEFORE the send, which is what catching a
                # cold boot needs.  ``D1`` needs the opposite: send
                # ``J BFC00000``, then stream ESC across the reboot that command
                # causes, so the warm boot's ESC window is caught inside the
                # SAME capture and the interval from the jump to the banner is
                # one file's timing rather than two wall-clocks a second apart.
                #
                # Without this, ``D1`` boots the vendor kernel, ``D2`` and
                # ``D2b`` lose the prompt they have to read, and recovering it
                # costs a power cycle -- which destroys the warm-reset condition
                # ``D2b`` exists to test.  Found 2026-08-24 by reading this
                # function before running the cell; it is the third cell this
                # repo has nearly lost to an instrument that could not do it
                # (``A2``, ``E5``) and the first one caught in advance.
                pending_esc = "esc_after"
                esc_started = time.monotonic()
                esc_deadline = esc_started + args.esc_after
                esc_writes = 0
                while time.monotonic() < esc_deadline:
                    ser.write(ESC)
                    esc_writes += 1
                    drain(args.esc_period)
                _record_esc(meta, "esc_after", args.esc_period, esc_writes,
                            time.monotonic() - esc_started)
                # D1 and D4 both end here, and D2 is the command that was going
                # to be appended to their residue. This does NOT retire
                # flush-d1/flush-d3: RUNSHEET keeps both, with the expectation
                # inverted, because they are the only measurement of what the
                # LOADER did with this CR -- the suite can only prove what was
                # written to the port.
                terminate_esc_line("esc_after")

            while True:
                drain(0.05)
                now = time.monotonic()
                if args.seconds and now - t0 >= args.seconds:
                    stop_reason = f"--seconds {args.seconds} elapsed"
                    break
                if args.idle and now - last_byte_at >= args.idle:
                    stop_reason = f"--idle {args.idle} with no bytes"
                    break
        except KeyboardInterrupt:
            stop_reason = "interrupted"
            if pending_esc is not None:
                # Measured 2026-08-24 on a pty, driving this file: a D1-shaped
                # interrupt (--send 'J BFC00000' --esc-after 20, Ctrl-C at t=5)
                # left 245 ESC on the wire with no CR, residue 117 -- and
                # 117 + len('DW B8003110 1') = 130 >= 128, which is the buffer
                # cliff and not a recoverable `Unknown command !`. The metadata
                # recorded "cr": {}, which this file defines as "the loop did
                # not run": a 1.1 capture wearing 1.2's version number.
                try:
                    terminate_esc_line(pending_esc, on_interrupt=True)
                except BaseException as e:
                    # BaseException, not Exception: a SECOND Ctrl-C landing
                    # inside ser.write(CR) is a KeyboardInterrupt, which is not
                    # an Exception subclass -- it would escape this guard, escape
                    # the handler it is already inside, and take the whole
                    # .meta.json with it. The capture would then have a .log and
                    # a .timing and no record of what the instrument did.
                    meta["cr"][pending_esc] = {
                        "written": False,
                        "reason": f"interrupted, and the CR could not be written: {e}",
                    }
        finally:
            ser.close()

    meta["stop_reason"] = stop_reason
    meta["bytes"] = offset
    meta["duration_s"] = round(time.monotonic() - t0, 6)
    with open(meta_path, "w", encoding="utf-8") as m:
        json.dump(meta, m, indent=2)
        m.write("\n")

    print(f"  {log_path}     {offset} bytes")
    print(f"  {timing_path}  {meta['duration_s']} s, stop: {stop_reason}")
    print(f"  {meta_path}")
    if offset == 0:
        print(
            "  NOTHING CAME BACK. That is three causes and not one: the adapter, "
            "the port, or the board. `Unknown command !` would have been the board "
            "answering; silence is not.",
            file=sys.stderr,
        )
        return 1
    return 0


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def _load(prefix: str):
    log_path, timing_path = prefix + ".log", prefix + ".timing"
    for p in (log_path, timing_path):
        if not os.path.exists(p):
            _fail(f"{p} not found")
    data = open(log_path, "rb").read()
    marks = []
    for line in open(timing_path, encoding="ascii"):
        if line.startswith("#"):
            continue
        off, secs = line.split()
        marks.append((int(off), float(secs)))
    if not marks:
        _fail(f"{timing_path} has no timing rows")
    return data, marks


def _time_of_offset(marks, off: int) -> float:
    """Timestamp of the read that delivered the byte at `off`.

    The read that delivered it is the last one whose recorded offset is <= off.
    This is an upper bound on when the byte arrived on the wire, never a lower
    one: the chunk was read at that instant and the byte was already in it.
    """
    best = marks[0][1]
    for start, secs in marks:
        if start <= off:
            best = secs
        else:
            break
    return best


def report(args) -> int:
    data, marks = _load(args.prefix)
    try:
        pat_from = re.compile(args.pat_from.encode())
        pat_to = re.compile(args.pat_to.encode())
    except re.error as e:
        _fail(f"bad pattern: {e}")

    m_from = pat_from.search(data)
    if not m_from:
        print(f"  FROM /{args.pat_from}/ : no match -- the interval is not measurable "
              f"from this capture", file=sys.stderr)
        return 1
    m_to = pat_to.search(data, m_from.end())
    if not m_to:
        print(f"  TO   /{args.pat_to}/ : no match after FROM -- either it never "
              f"arrived or the capture stopped first ({len(data)} bytes)", file=sys.stderr)
        return 1

    t_from = _time_of_offset(marks, m_from.start())
    t_to = _time_of_offset(marks, m_to.start())
    print(f"  FROM  offset {m_from.start():>7}  t={t_from:9.3f}s  {data[m_from.start():m_from.end()][:60]!r}")
    print(f"  TO    offset {m_to.start():>7}  t={t_to:9.3f}s  {data[m_to.start():m_to.end()][:60]!r}")
    print(f"  INTERVAL  {t_to - t_from:.3f} s")
    print("  (upper bound on each endpoint; floor is the USB-serial latency timer, "
          "not the 260 us character time)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("capture", help="stream the console to PREFIX.log/.timing/.meta.json")
    c.add_argument("--port", required=True, help="e.g. /dev/ttyUSB0 (usbipd attach first)")
    c.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    c.add_argument("--out", required=True, help="output path prefix, no extension")
    c.add_argument("--esc-after", dest="esc_after", type=float, default=0.0,
                   help="stream ESC for this many seconds AFTER --send, to catch "
                        "the ESC window of a reboot the sent command caused. "
                        "This is what D1 needs and --esc cannot give it")
    c.add_argument("--esc", type=float, default=0.0,
                   help="stream ESC for this many seconds before capturing")
    c.add_argument("--esc-period", dest="esc_period", type=float,
                   default=DEFAULT_ESC_PERIOD,
                   help="seconds between one ESC and the next, in BOTH loops "
                        f"(default {DEFAULT_ESC_PERIOD}). This is the grid any "
                        "interval read off ESC echoes is quantised to. CLK-08b "
                        "needs 0.002; the achieved period is measured and put "
                        "in the metadata either way")
    c.add_argument("--send", default=None,
                   help="one command line to send verbatim, then read-only")
    c.add_argument("--no-cr", dest="no_cr", action="store_true",
                   help="do NOT write the CR that terminates an ESC loop. The "
                        "capture then leaves N mod 128 bytes in the loader's "
                        "readline buffer and the next command line is appended "
                        "to them -- RUNSHEET seating 2 rule 2. Here so the "
                        "self-test's positive case measures the behaviour")
    c.add_argument("--cr-settle", dest="cr_settle", type=float,
                   default=DEFAULT_CR_SETTLE,
                   help="after that CR, read for at most this many seconds "
                        "waiting for the prompt it causes (default "
                        f"{DEFAULT_CR_SETTLE})")
    c.add_argument("--seconds", type=float, default=0.0, help="stop after N s")
    c.add_argument("--idle", type=float, default=0.0, help="stop after N s with no bytes")
    c.add_argument("--force", action="store_true", help="overwrite an existing capture")
    c.set_defaults(func=capture)

    r = sub.add_parser("report", help="interval between two patterns in a capture")
    r.add_argument("prefix")
    r.add_argument("--from", dest="pat_from", required=True, help="regex, first match")
    r.add_argument("--to", dest="pat_to", required=True, help="regex, first match after FROM")
    r.set_defaults(func=report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
