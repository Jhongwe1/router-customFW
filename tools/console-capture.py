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
        "port": args.port,
        "baud": args.baud,
        "started_wallclock": None,
        "esc_seconds": args.esc,
        "esc_after_seconds": args.esc_after,
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

        try:
            if args.esc:
                # The ESC window on this unit is ~4.9 s wide, banner to
                # "Jump to image start", measured 2026-08-18. Streaming from
                # before power-on is what B1 A1 does; it is also what sets
                # gCHKKEY_HIT, which is why B5 read 1 and not 0.
                esc_deadline = time.monotonic() + args.esc
                while time.monotonic() < esc_deadline:
                    ser.write(ESC)
                    drain(0.02)

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
                esc_deadline = time.monotonic() + args.esc_after
                while time.monotonic() < esc_deadline:
                    ser.write(ESC)
                    drain(0.02)

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
    c.add_argument("--send", default=None,
                   help="one command line to send verbatim, then read-only")
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
