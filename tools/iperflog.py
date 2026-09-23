#!/usr/bin/env python3
"""iperflog.py -- the board's receive figure, read from its own iperf 3.1.3 server log.

WHY IT EXISTS
-------------
Seating A has no rlxfw receive figure.  In every board-receives trial on rlx0
the end-of-test exchange never completed, so the host's iperf3 client never
printed the `receiver` line the card scores (SPEC.md NET-112; notes/nic-driver.md
section 19.2: receive is complete, the server's results frame is lost on
transmit).  The board's server computed the figure anyway.  Seating B keeps it:
`iperf3 -s -1 -f k --logfile /tmp/T.log` on the board, then `cat /tmp/T.log`
over the console.  This tool reads that text -- a console capture's .log (CRLF,
with the echoed command, other output and the prompt around it) or a plain log
file -- into one row per interval and one FIGURE line per trial, every value
with the line it came from.

WHAT A TRIAL'S LOG CAN HOLD
---------------------------
讀 iperf 3.1.3 (the source that builds the board's /bin/iperf3), shapes 量 under
qemu from the board's own binary ($FWRE_WORK/rebuild/s107/srvlog, runs R1-K6):

  TEST_END      intervals, the final partial interval, then a summary block
                (separator, header, lines).  iperf_server_api.c:200-209.
  CLIENT_TERM.  the client was SIGTERM'd (timeout 70 does this): the server
                re-prints its LAST interval line unchanged, prints a summary,
                then "iperf3: the client has terminated" (:221-240).  After a
                TEST_END the re-printed summary repeats the receiver figure;
                before one (K4) it divides the bytes received up to the kill by
                the time up to the last interval -- 24.1 Mbit/s, where the
                client's own line reads 19.8 (11.5 MBytes over 4.87 s).
  SIGTERM       a server killed while still running a test prints a fresh
                interval and a summary, then "iperf3: interrupt - the server
                has terminated" (iperf_api.c:2872-2896, iperf_got_sigend).
  deaf (K6)     a server that heard TEST_END but never the client's end: its
                TEST_END summary reaches the file only at the killall's exit
                flush, followed by the same "interrupt" line -- textually the
                SIGTERM shape.  Only the summary's end time tells them apart:
                --duration T reads a summary ending within 1 s of T as
                TEST_END's, anything else as SIGTERM's.  推: qemu's ended
                0.00-0.04 s past T (量); the board's clock ran up to 0.64 %
                off host realtime in seating A (0.19 s over 30 s), and a host
                realtime step during a trial moves its end by the step (0.64-
                0.68 s there, notes/nic-driver.md section 19.7), so two steps
                in one trial could leave the window.  Without --duration the
                tool will not guess.
  killed        interval lines only: every interval is flushed when printed
                (print_interval_results ends in iflush when --logfile is set,
                iperf_api.c:2631-2632), the summary never is (K1, K6b).
  client lost   intervals, then "the client has unexpectedly closed the
                connection" and no summary (K3).

THE RULES
---------
* The interval line right before a CLIENT_TERMINATE summary is a re-print and is
  dropped -- only after checking it repeats the last interval line kept, or the
  trial is flagged.
* The figure comes from the TEST_END summary and nothing else.  A
  CLIENT_TERMINATE or SIGTERM summary is listed and never used.  With no TEST_END
  summary the FIGURE line says so and gives the interval lines' sum instead, with
  its own, wider rounding; the exit status is then 1.
* TCP: the summary's receiver line.  Its rate column is the figure: bytes over
  the server's own end_time, computed from the exact byte count and the
  microsecond duration and then rounded once.  With -f k it prints whole Kbit/s
  (%4.0f once past 999.5 Kbit/s, units.c:316-331): five significant digits from
  10 to 100 Mbit/s, half-unit 500 bit/s.  The transfer column has three
  significant digits in 1024-based units (four in [1000,1024)); it is reported
  and must agree with rate x end_time, but is never the figure.
* UDP: the server's summary prints "0.00 Bytes" -- print_results prints the
  local bytes SENT (iperf_api.c:2367, 2382-2383).  The figure is built from exact
  integers: received = total - lost + out-of-order (iperf_udp.c:100-107: a gap
  counts as lost and a late arrival is never un-counted), bytes = received x
  --datagram (1400 on the card, -l 1400), over the summary's end time, printed
  %6.2f: the only rounding in a UDP figure is that +/-0.005 s.  Every interval's
  transfer column is checked against (total - lost) x --datagram, so a wrong
  datagram size is caught to about +/-0.2 %, the columns' rounding.
* Exact structure, checked per trial: intervals continuous (each start is the
  previous end, as printed), the first at 0.00, every summary starting at 0.00
  and ending where the last interval kept ends; UDP interval lost and total sum
  EXACTLY to the TEST_END summary's; TCP interval transfers sum to its transfer
  within their rounding.  A line that looks like iperf's but matches no format,
  a second stream, or a sender-format trial (the board sent: -R) is flagged.

COMPARE -- THE POSITIVE CONTROL
-------------------------------
For a trial the host saw complete (every eth4 trial in seating A), the board
log's figure must be the host's, within the two lines' printed rounding:

* TCP.  The host's receiver line is the board's byte count, sent in the results
  JSON as an exact integer (iperf_api.c:1498, cjson.c print_number "%lld"),
  divided by the HOST's end time.  So the two transfer columns are one integer
  through one formatter and must be IDENTICAL, while the two rates divide it by
  different clocks and are never compared to each other directly.  Each line
  bounds 8 x bytes: rate x end within (rate +/- half)(end +/- 0.005), and
  transfer x 8 within its half-unit; all four intervals must share a point.
* UDP.  The host has no receiver rate (its summary rate is its own send rate,
  notes/nic-driver.md section 19.4); it carries the board's lost and total,
  exact integers from the JSON -- they must be equal -- and the board's jitter,
  which reached it through cjson's %f (1 us) and was printed %5.3f ms again:
  double rounding bounds the difference by 0.001 ms.
* It refuses (exit 2), before any number, when the pair cannot be a control: the
  host did not complete (no "iperf Done.", or an "iperf3:" line), ran -R, the
  protocols differ, the board log has no TEST_END summary, or the two data
  streams are not the same connection (board local = host remote and back).

EXIT STATUS
-----------
  parse    0  every trial parsed consistently and has a TEST_END figure
           1  a trial without one, a flagged inconsistency, or no trial at all
  compare  0  AGREE      1  DISAGREE, with the numbers
  both     2  refused: arguments (refuse_args), an unreadable file, or a pair
              that cannot serve as the control

WHAT IT DOES NOT ESTABLISH
--------------------------
Anything the board's server did not print.  The figure is bytes the board's
stack delivered to the socket over the board's own clock, whose resolution
(HZ 100, 推) is not in any printed rounding; nothing here measures that clock.
The parser was built against qemu logs of the board's binary; a board log is the
same code and format but not yet a line it has read.  compare checks that two
printed lines agree with one integer; it cannot tell two trials apart when their
figures match (the stream check does that), and it says nothing about a trial
whose exchange failed, which is exactly the rlx0 case it exists to support.
iperflog reads no clock, network, port or device, and no environment variable.

FW-124: build_parser() is the parser main() uses; refuse_args(a) refuses from
the parsed arguments alone, before main() opens anything.

    iperflog.py parse [--datagram B] [--duration T] LOG
    iperflog.py compare [--datagram B] [--duration T] [--trial N] BOARD_LOG HOST_OUTPUT
    iperflog.py --self-test
"""
import argparse
import contextlib
import io
import math
import re
import sys
from fractions import Fraction

TOOL_VERSION = "1.0"

# 讀 iperf.h:316 (3.1.3): MAX_UDP_BLOCKSIZE (65535 - 8 - 20), and iperf_api.c:996
# refuses a block size <= 0.  --datagram is refused outside what iperf accepts.
MAX_UDP_BLOCKSIZE = 65535 - 8 - 20
TERM_WINDOW_S = Fraction(1)           # see "deaf (K6)" above; 推
JITTER_TOL_MS = Fraction(1, 1000)     # double rounding of the jitter, see COMPARE


class Refused(Exception):
    """A refusal: printed with its reason, exit status 2."""


# ------------------------------------------------------------ printed numbers

BYTE_SCALE = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}      # units.c:205-211
BIT_SCALE = {"": 1, "K": 1000, "M": 1000 ** 2, "G": 1000 ** 3}       # units.c:214-220
DIGITS_RE = re.compile(r"\d+(?:\.\d+)?")


class Num:
    """A number as iperf printed it: its text, and its value and half its last digit in base units."""
    __slots__ = ("text", "value", "half")

    def __init__(self, digits, scale, text):
        self.text = text
        if DIGITS_RE.fullmatch(digits):
            places = len(digits.split(".")[1]) if "." in digits else 0
            self.value = Fraction(digits) * scale
            self.half = Fraction(1, 2 * 10 ** places) * scale
        else:                          # inf or nan: a zero-length interval's rate
            self.value = self.half = None

    @property
    def lo(self):
        return self.value - self.half

    @property
    def hi(self):
        return self.value + self.half


def num_time(digits):
    return Num(digits, 1, digits)


# ------------------------------------------------------------ line shapes
# 讀 iperf_locale.c:283-348.  Matched after the CR and the trailing spaces are gone.

T2 = r"(\d+\.\d\d)"
ROW_RE = re.compile(r"^\[\s*(\d+)\]\s+" + T2 + "-" + T2 + r"\s+sec\s+"
                    r"(\d+(?:\.\d+)?) ([KMG]?)Bytes\s+(\S+) ([KMG]?)bits/sec(.*)$")
TAIL_UDP = re.compile(r"^\s+(\d+\.\d{3}) ms\s+(\d+)/(\d+) \(([^)]*)%\)(\s+\(omitted\))?$")
TAIL_RETR_CWND = re.compile(r"^\s+(\d+)\s+(\d+(?:\.\d+)?) ([KMG]?)Bytes(\s+\(omitted\))?$")
TAIL_RETR = re.compile(r"^\s+(\d+)\s+(sender)$")
TAIL_UDP_SENDER = re.compile(r"^\s+(\d+)(\s+\(omitted\))?$")
TAIL_PLAIN = re.compile(r"^(?:\s+(sender|receiver|\(omitted\)))?$")

SEP_RE = re.compile(r"^(?:- )+-$")
BANNER_RE = re.compile(r"^-{10,}$")
LISTEN_RE = re.compile(r"^Server listening on (\d+)$")
ACCEPT_RE = re.compile(r"^Accepted connection from (\S+), port (\d+)$")
CONNECT_RE = re.compile(r"^\[\s*(\d+)\] local (\S+) port (\d+) connected to (\S+) port (\d+)$")
HEADER_RE = re.compile(r"^\[ ID\] Interval\s+Transfer\s+Bandwidth(.*)$")
MSG_RE = re.compile(r"^iperf3: (.*)$")
OOO_RE = re.compile(r"^\[SUM\]\s+(\d+\.\d)-(\d+\.\d)\s+sec\s+(\d+) datagrams received out-of-order$")
SENT_RE = re.compile(r"^\[\s*(\d+)\] Sent (\d+) datagrams$")
SHAPED_RE = re.compile(r"^\[\s*(?:\d+|SUM|ID)\]")
CONNECTING_RE = re.compile(r"^Connecting to host (\S+), port (\d+)$")
REVERSE_RE = re.compile(r"^Reverse mode, remote host (\S+) is sending$")
DONE_TEXT = "iperf Done."
CT_TEXT = "the client has terminated"
TERM_TEXT = "interrupt - the server has terminated"

# header suffix (words after "Bandwidth") -> (protocol, role of the printing side)
HEADERS = {"": ("tcp", "receiver"), "Retr": ("tcp", "summary"), "Retr Cwnd": ("tcp", "sender"),
           "Jitter Lost/Total Datagrams": ("udp", "receiver"), "Total Datagrams": ("udp", "sender")}


class Row:
    """One interval or summary line."""
    __slots__ = ("line", "text", "sid", "start", "end", "transfer", "rate", "shape", "suffix",
                 "retr", "jitter", "lost", "total", "pct", "status")

    def is_udp(self):
        return self.shape == "udp"


def match_row(s, n):
    m = ROW_RE.match(s)
    if not m:
        return None
    r = Row()
    r.line, r.text, r.sid = n, s, int(m.group(1))
    r.start, r.end = num_time(m.group(2)), num_time(m.group(3))
    r.transfer = Num(m.group(4), BYTE_SCALE[m.group(5)], "%s %sBytes" % (m.group(4), m.group(5)))
    r.rate = Num(m.group(6), BIT_SCALE[m.group(7)], "%s %sbits/sec" % (m.group(6), m.group(7)))
    r.retr = r.jitter = r.lost = r.total = r.pct = None
    r.suffix, r.status = "", "kept"
    tail = m.group(8)
    t = TAIL_UDP.match(tail)
    if t:
        r.shape = "udp"
        r.jitter = Num(t.group(1), 1, t.group(1) + " ms")
        r.lost, r.total, r.pct = int(t.group(2)), int(t.group(3)), t.group(4)
        r.suffix = "(omitted)" if t.group(5) else ""
        return r
    t = TAIL_RETR_CWND.match(tail)
    if t:
        r.shape, r.retr = "tcp-sender", int(t.group(1))
        r.suffix = "(omitted)" if t.group(4) else ""
        return r
    t = TAIL_RETR.match(tail)
    if t:
        r.shape, r.retr, r.suffix = "tcp-retr", int(t.group(1)), t.group(2)
        return r
    t = TAIL_UDP_SENDER.match(tail)
    if t:
        r.shape = "udp-sender"
        r.suffix = "(omitted)" if t.group(2) else ""
        return r
    t = TAIL_PLAIN.match(tail)
    if t:
        r.shape, r.suffix = "tcp", t.group(1) or ""
        return r
    return None


def text_lines(data):
    """Lines of a capture or a log: bytes as latin-1, split on LF, every trailing CR removed.

    A console capture is CRLF, and ash wraps a long echoed command with CR CR LF.
    The CRs go here, before any field is compared, and nowhere else.
    """
    return [ln.rstrip("\r") for ln in data.decode("latin-1").split("\n")]


# ------------------------------------------------------------ summary blocks

class Block:
    """A summary block: separator, header, then its line(s)."""

    def __init__(self, line):
        self.sep, self.header, self.rows, self.ooo = line, None, [], None
        self.kind, self.why = None, ""

    def proto(self):
        return HEADERS.get(self.header[1], (None, None))[0] if self.header else None

    def complete(self):
        if self.proto() == "tcp":
            return bool(self.rows) and self.rows[-1].suffix == "receiver"
        if self.proto() == "udp":
            return len(self.rows) == 1
        return False

    def accepts(self, r):
        if self.complete():
            return False
        if self.proto() == "tcp":
            if r.shape in ("tcp", "tcp-retr") and r.suffix == "sender" and not self.rows:
                return True
            return (r.shape == "tcp" and r.suffix == "receiver" and len(self.rows) == 1
                    and self.rows[0].suffix == "sender")
        if self.proto() == "udp":
            return r.shape == "udp" and r.suffix == "" and not self.rows
        return False

    def row(self):
        """The line a figure would read: TCP's receiver line, UDP's only line."""
        if not self.complete():
            return None
        return self.rows[-1]


class Trial:
    def __init__(self, index, line):
        self.index, self.first, self.last = index, line, line
        self.stream = None             # (sid, local, lport, remote, rport, line)
        self.events = []               # ("int", Row) ("blk", Block) ("msg", n, text) ("hdr", n, suffix)
        self.problems = []             # (line, text)
        self.ooo_msgs = 0
        self.proto = self.role = None
        self.figure = None

    def rows(self, status=None):
        return [e[1] for e in self.events if e[0] == "int" and (status is None or e[1].status == status)]

    def blocks(self):
        return [e[1] for e in self.events if e[0] == "blk"]

    def ok(self):
        return not self.problems and self.figure is not None and self.figure.source == "TEST_END"


def norm_addr(a):
    return a[7:] if a.lower().startswith("::ffff:") else a


def parse_server(lines):
    """Split a server log (or a capture holding one) into trials; return (trials, outside, stray)."""
    trials, outside, stray = [], [], []
    cur = None
    blk = None

    def close_block():
        nonlocal blk
        if blk is not None and cur is not None and not blk.complete():
            cur.problems.append((blk.sep, "summary block incomplete (the text may have been cut)"))
        blk = None

    for n, raw in enumerate(lines, 1):
        s = raw.rstrip(" ")
        if not s:
            continue
        if ACCEPT_RE.match(s):
            close_block()
            cur = Trial(len(trials) + 1, n)
            trials.append(cur)
            continue
        if LISTEN_RE.match(s):
            close_block()
            cur = None
            continue
        if BANNER_RE.match(s):
            continue
        if cur is None:
            if MSG_RE.match(s):
                outside.append((n, s))
            elif SHAPED_RE.match(s):
                stray.append((n, "iperf line outside any trial (no 'Accepted connection' before it)"))
            continue
        cur.last = n
        m = CONNECT_RE.match(s)
        if m:
            close_block()
            st = (int(m.group(1)), norm_addr(m.group(2)), int(m.group(3)),
                  norm_addr(m.group(4)), int(m.group(5)), n)
            if cur.stream is None:
                cur.stream = st
            else:
                cur.problems.append((n, "a second stream connected: iperflog reads -P 1 trials only"))
            continue
        if SEP_RE.match(s):
            close_block()
            blk = Block(n)
            cur.events.append(("blk", blk))
            continue
        m = HEADER_RE.match(s)
        if m:
            suffix = " ".join(m.group(1).split())
            if suffix not in HEADERS:
                cur.problems.append((n, "a column header this tool does not know: %r" % s))
            if blk is not None and blk.header is None:
                blk.header = (n, suffix)
            else:
                close_block()
                cur.events.append(("hdr", n, suffix))
            continue
        m = OOO_RE.match(s)
        if m:
            if blk is not None and blk.proto() == "udp" and blk.complete() and blk.ooo is None:
                blk.ooo = (n, int(m.group(3)))
            else:
                cur.problems.append((n, "an out-of-order count outside a UDP summary"))
            continue
        m = MSG_RE.match(s)
        if m:
            close_block()
            cur.events.append(("msg", n, m.group(1)))
            if m.group(1).startswith("OUT OF ORDER"):
                cur.ooo_msgs += 1
            continue
        r = match_row(s, n)
        if r is not None:
            if blk is not None:
                if blk.header is None:
                    cur.problems.append((blk.sep, "separator with no header after it"))
                elif blk.accepts(r):
                    blk.rows.append(r)
                    continue
                close_block()
            if r.suffix in ("sender", "receiver"):
                cur.problems.append((n, "a summary line outside a summary block"))
                continue
            cur.events.append(("int", r))
            continue
        if SENT_RE.match(s):
            cur.problems.append((n, "a client's 'Sent N datagrams' line inside a server log"))
            continue
        if SHAPED_RE.match(s):
            cur.problems.append((n, "iperf-shaped line in no format this tool knows: %r" % s))
            continue
        # anything else is not iperf's: the echo, /proc text, the prompt, a printk
    close_block()
    return trials, outside, stray


# ------------------------------------------------------------ one trial

def next_event(evs, i):
    for e in evs[i + 1:]:
        if e[0] != "hdr":
            return e
    return None


def prev_event(evs, i):
    for j in range(i - 1, -1, -1):
        if evs[j][0] != "hdr":
            return j
    return None


def classify(trial, duration):
    evs = trial.events
    for i, e in enumerate(evs):
        if e[0] != "blk":
            continue
        b, nxt = e[1], next_event(evs, i)
        if nxt is not None and nxt[0] == "msg" and nxt[2] == CT_TEXT:
            b.kind, b.why = "CLIENT_TERMINATE", "followed by 'the client has terminated' (line %d)" % nxt[1]
        elif nxt is not None and nxt[0] == "msg" and nxt[2] == TERM_TEXT:
            end = b.row().end.value if b.row() is not None else None
            if duration is None or end is None:
                b.kind = "TEST_END-or-SIGTERM"
                b.why = ("followed by 'interrupt - the server has terminated' (line %d): TEST_END's "
                         "summary flushed at the kill, or the SIGTERM handler's own; give --duration"
                         % nxt[1])
            elif abs(end - duration) <= TERM_WINDOW_S:
                b.kind = "TEST_END"
                b.why = ("followed by 'interrupt' (line %d), and it ends at %s, within %s s of "
                         "--duration %s" % (nxt[1], b.row().end.text, TERM_WINDOW_S, fmt(duration, 2)))
            else:
                b.kind = "SIGTERM"
                b.why = ("followed by 'interrupt' (line %d), and it ends at %s, not within %s s of "
                         "--duration %s: printed by the kill, not by the test's end"
                         % (nxt[1], b.row().end.text, TERM_WINDOW_S, fmt(duration, 2)))
        else:
            b.kind, b.why = "TEST_END", "not re-printed by a terminate path"


def drop_reprints(trial):
    evs = trial.events
    for i, e in enumerate(evs):
        if e[0] != "blk" or e[1].kind != "CLIENT_TERMINATE":
            continue
        j = prev_event(evs, i)
        if j is None or evs[j][0] != "int":
            trial.problems.append((e[1].sep, "a CLIENT_TERMINATE summary with no re-printed interval "
                                   "line before it"))
            continue
        dup = evs[j][1]
        prev = None
        for k in range(j - 1, -1, -1):
            if evs[k][0] == "int" and evs[k][1].status == "kept":
                prev = evs[k][1]
                break
        if prev is None or prev.text != dup.text:
            trial.problems.append((dup.line, "the line before a CLIENT_TERMINATE summary does not "
                                   "repeat the last interval kept%s" % (
                                       "" if prev is None else " (line %d)" % prev.line)))
            continue
        dup.status = "dropped: CLIENT_TERMINATE re-print of line %d" % prev.line


def check(trial, datagram):
    kept = trial.rows("kept")
    if trial.stream is not None:
        for r in kept + [x for b in trial.blocks() for x in b.rows]:
            if r.sid != trial.stream[0]:
                trial.problems.append((r.line, "stream [%3d], but this trial's stream is [%3d]"
                                       % (r.sid, trial.stream[0])))
    prev = None
    for r in kept:
        if prev is None and r.start.value != 0:
            trial.problems.append((r.line, "the first interval starts at %s, not 0.00: lines before "
                                   "it are missing" % r.start.text))
        if prev is not None and r.start.value != prev.end.value:
            trial.problems.append((r.line, "interval starts at %s but the one before it (line %d) "
                                   "ended at %s: a line is missing or repeated"
                                   % (r.start.text, prev.line, prev.end.text)))
        prev = r
    evs = trial.events
    for i, e in enumerate(evs):
        if e[0] != "blk" or e[1].row() is None:
            continue
        b, row = e[1], e[1].row()
        before = [x[1] for x in evs[:i] if x[0] == "int" and x[1].status == "kept"]
        if row.start.value != 0:
            trial.problems.append((row.line, "summary starts at %s, not 0.00" % row.start.text))
        if before and row.end.value != before[-1].end.value:
            trial.problems.append((row.line, "summary ends at %s, the last interval kept (line %d) "
                                   "at %s" % (row.end.text, before[-1].line, before[-1].end.text)))
        if b.kind != "TEST_END":
            continue
        if b.proto() == "tcp":
            lo = sum((xfer_lo(r) for r in before), Fraction(0))
            hi = sum((r.transfer.hi for r in before), Fraction(0))
            if hi < row.transfer.lo or lo > row.transfer.hi:
                trial.problems.append((row.line, "interval transfers sum to [%s, %s] B, the summary "
                                       "says %s: an interval line is missing or extra"
                                       % (fmt(lo), fmt(hi), row.transfer.text)))
            if meet([bits_rate(row), bits_xfer(row)]) is None:
                trial.problems.append((row.line, "its rate x end and its transfer disagree beyond "
                                       "their rounding: not a line this parser understands"))
        else:
            lost = sum(r.lost for r in before)
            total = sum(r.total for r in before)
            if (lost, total) != (row.lost, row.total):
                trial.problems.append((row.line, "interval lost/total sum to %d/%d, the summary says "
                                       "%d/%d: an interval line is missing, extra or corrupt"
                                       % (lost, total, row.lost, row.total)))
    if trial.proto == "udp":
        ooo = udp_ooo(trial)
        for r in kept:
            got = (r.total - r.lost) * datagram
            if got + ooo * datagram < r.transfer.lo or got > r.transfer.hi:
                trial.problems.append((r.line, "transfer %s is not (%d - %d) x %d B = %d B within its "
                                       "rounding: the datagram size is not %d"
                                       % (r.transfer.text, r.total, r.lost, datagram, got, datagram)))


def udp_ooo(trial):
    te = test_end_block(trial)
    if te is not None and te.ooo is not None:
        return te.ooo[1]
    return trial.ooo_msgs


def test_end_block(trial):
    for b in trial.blocks():
        if b.kind == "TEST_END" and b.row() is not None:
            return b
    return None


def bits_rate(row):
    """8 x bytes, bounded by a line's rate and end time: (rate +/- half)(end +/- 0.005)."""
    if row.rate.value is None:
        return None
    return (max(row.rate.lo, Fraction(0)) * row.end.lo, row.rate.hi * row.end.hi)


def xfer_lo(row):
    """A transfer column's floor; "0.00 Bytes" is 0, not -0.005."""
    return max(row.transfer.lo, Fraction(0))


def bits_xfer(row):
    return (xfer_lo(row) * 8, row.transfer.hi * 8)


def meet(intervals):
    ivs = [i for i in intervals if i is not None]
    lo, hi = max(i[0] for i in ivs), min(i[1] for i in ivs)
    return (lo, hi) if lo <= hi else None


class Figure:
    def __init__(self, trial, source):
        self.trial, self.source, self.proto = trial.index, source, trial.proto
        self.lines = ""
        self.rate_lo = self.rate_hi = self.rate_mid = None
        self.bytes_lo = self.bytes_hi = None
        self.row = None
        self.total = self.lost = self.ooo = self.received = self.nbytes = None


def figure(trial, datagram):
    te = test_end_block(trial)
    if te is not None:
        f = Figure(trial, "TEST_END")
        row = te.row()
        f.row, f.lines = row, str(row.line)
        if trial.proto == "tcp":
            both = meet([bits_rate(row), bits_xfer(row)])
            f.rate_mid = row.rate.value
            f.rate_lo, f.rate_hi = row.rate.lo, row.rate.hi
            if both is not None:
                f.bytes_lo, f.bytes_hi = both[0] / 8, both[1] / 8
        else:
            f.total, f.lost, f.ooo = row.total, row.lost, udp_ooo(trial)
            if te.ooo is not None:
                f.lines = "%d,%d" % (row.line, te.ooo[0])
            f.received = row.total - row.lost + f.ooo
            f.nbytes = f.received * datagram
            f.rate_mid = Fraction(f.nbytes * 8) / row.end.value if row.end.value else None
            f.rate_lo = Fraction(f.nbytes * 8) / row.end.hi
            f.rate_hi = Fraction(f.nbytes * 8) / row.end.lo if row.end.lo > 0 else None
        return f
    kept = trial.rows("kept")
    if not kept:
        return None
    f = Figure(trial, "intervals")
    f.lines = "%d-%d" % (kept[0].line, kept[-1].line)
    span = kept[-1].end.value - kept[0].start.value
    half = kept[-1].end.half + (0 if kept[0].start.value == 0 else kept[0].start.half)
    if trial.proto == "udp":
        f.ooo = trial.ooo_msgs
        f.total = sum(r.total for r in kept)
        f.lost = sum(r.lost for r in kept)
        f.received = f.total - f.lost + f.ooo
        f.nbytes = f.received * datagram
        lo = hi = Fraction(f.nbytes * 8)
    else:
        f.bytes_lo = sum((xfer_lo(r) for r in kept), Fraction(0))
        f.bytes_hi = sum((r.transfer.hi for r in kept), Fraction(0))
        lo, hi = f.bytes_lo * 8, f.bytes_hi * 8
    f.rate_mid = (lo + hi) / 2 / span if span > 0 else None
    f.rate_lo = lo / (span + half) if span + half > 0 else None
    f.rate_hi = hi / (span - half) if span - half > 0 else None
    return f


def analyse(trial, datagram, duration):
    shapes = {r.shape for r in trial.rows()}
    hdrs = {HEADERS.get(e[2], (None, None)) for e in trial.events if e[0] == "hdr"}
    if shapes & {"tcp-sender", "udp-sender"} or any(role == "sender" for _p, role in hdrs):
        trial.role = "sender"
        trial.proto = "udp" if shapes & {"udp", "udp-sender"} else "tcp"
        trial.problems.append((trial.first, "the server was the sender in this trial (the client "
                               "ran -R): iperflog reads the board's receive figure only"))
        return trial
    trial.role = "receiver"
    protos = {("udp" if s == "udp" else "tcp") for s in shapes}
    protos |= {b.proto() for b in trial.blocks() if b.proto()}
    if len(protos) > 1:
        trial.problems.append((trial.first, "TCP and UDP lines in one trial"))
    trial.proto = protos.pop() if len(protos) == 1 else None
    classify(trial, duration)
    drop_reprints(trial)
    kinds = [b.kind for b in trial.blocks()]
    if kinds.count("TEST_END") > 1:
        trial.problems.append((trial.first, "two summaries that no terminate path re-printed"))
    check(trial, datagram)
    trial.figure = figure(trial, datagram)
    return trial


class Report:
    def __init__(self, path, lines, trials, outside, stray):
        self.path, self.trials, self.outside, self.stray = path, trials, outside, stray
        self.nlines = len(lines) - (1 if lines and lines[-1] == "" else 0)   # a final LF ends a line

    def rc(self):
        return 0 if self.trials and not self.stray and all(t.ok() for t in self.trials) else 1


def read_report(path, data, datagram, duration):
    lines = text_lines(data)
    trials, outside, stray = parse_server(lines)
    for t in trials:
        analyse(t, datagram, duration)
    return Report(path, lines, trials, outside, stray)


# ------------------------------------------------------------ rendering

def fmt(x, places=0):
    if x is None:
        return "-"
    return "%.*f" % (places, float(x))


def step(num):
    """The printed step of a column, read from its own digits: "1 Kbits/sec", "0.1 Mbits/sec"."""
    digits, unit = num.text.split()
    places = len(digits.split(".")[1]) if "." in digits else 0
    return "%s %s" % ("1" if places == 0 else "0." + "0" * (places - 1) + "1", unit)


def fig_line(t, datagram):
    f = t.figure
    head = "FIGURE trial=%d proto=%s" % (t.index, t.proto or "-")
    if f is None:
        return head + " source=none -- " + ("the board sent in this trial (-R)" if t.role == "sender"
                                            else "no interval or summary line to read")
    parts = [head, "source=%s" % f.source, "lines=%s" % f.lines]
    if f.source == "TEST_END" and f.proto == "tcp":
        r = f.row
        parts += ['rate="%s"' % r.rate.text, "rate_bps=%s+/-%s" % (fmt(r.rate.value), fmt(r.rate.half)),
                  "end_s=%s+/-0.005" % r.end.text, 'transfer="%s"' % r.transfer.text,
                  "bytes=[%s,%s]" % (fmt(f.bytes_lo), fmt(f.bytes_hi)),
                  "rounding=the rate column is the figure, printed in steps of %s; the transfer "
                  "column (steps of %s, 1024-based) is checked, not used" % (step(r.rate), step(r.transfer))]
    elif f.proto == "udp":
        parts += ["received=%d (=%d total-%d lost+%d out-of-order)" % (f.received, f.total, f.lost, f.ooo),
                  "datagram_B=%d" % datagram, "bytes=%d" % f.nbytes]
        if f.source == "TEST_END":
            parts += ["end_s=%s+/-0.005" % f.row.end.text,
                      "rate_bps=%s range=[%s,%s]" % (fmt(f.rate_mid), fmt(f.rate_lo), fmt(f.rate_hi)),
                      "rounding=exact integers; only the printed end time (+/-0.005 s)"]
        else:
            parts += ["rate_bps=%s range=[%s,%s]" % (fmt(f.rate_mid), fmt(f.rate_lo), fmt(f.rate_hi)),
                      "rounding=exact integers over the intervals' printed span"]
    else:
        parts += ["bytes=[%s,%s]" % (fmt(f.bytes_lo), fmt(f.bytes_hi)),
                  "rate_bps=%s range=[%s,%s]" % (fmt(f.rate_mid), fmt(f.rate_lo), fmt(f.rate_hi)),
                  "rounding=sum of transfer columns (3 significant digits each) over the printed span"]
    if f.source != "TEST_END":
        parts.append("-- NO TEST_END SUMMARY: not the card's figure")
    return " ".join(parts)


def row_line(kind, r, status):
    lt = "%d/%d" % (r.lost, r.total) if r.lost is not None else "-"
    jit = r.jitter.text if r.jitter is not None else "-"
    return "  %5d  %-8s %6s-%-6s %-13s %-17s %-10s %-12s %s" % (
        r.line, kind, r.start.text, r.end.text, r.transfer.text, r.rate.text, jit, lt, status)


def render_report(rep, datagram):
    out = ["iperflog %s parse: %s -- %d lines, %d trial(s)" % (TOOL_VERSION, rep.path, rep.nlines,
                                                                len(rep.trials))]
    for n, why in rep.stray:
        out.append("  PROBLEM line %d: %s" % (n, why))
    for t in rep.trials:
        st = t.stream
        where = ("stream [%3d] %s:%d <- %s:%d (line %d)" % st) if st else "no stream line"
        out.append("trial %d  lines %d-%d  %s  board %s  %s" % (
            t.index, t.first, t.last, t.proto or "-", "receives" if t.role == "receiver" else "sends",
            where))
        out.append("  %5s  %-8s %-13s %-13s %-17s %-10s %-12s %s" % (
            "line", "row", "interval", "transfer", "bandwidth", "jitter", "lost/total", "status"))
        for e in t.events:
            if e[0] == "int":
                out.append(row_line("interval", e[1], e[1].status))
            elif e[0] == "msg":
                out.append("  %5d  message  iperf3: %s" % (e[1], e[2]))
            elif e[0] == "blk":
                b = e[1]
                for r in b.rows:
                    use = ""
                    if r is b.row():
                        use = "used" if b.kind == "TEST_END" else "ignored"
                        if b.kind == "TEST_END" and r.is_udp():
                            use = "used (lost/total; its transfer and bandwidth are bytes the server SENT)"
                    label = " ".join(x for x in (b.kind, r.suffix) if x)
                    out.append(row_line("summary", r, label + ((": " + use) if use else "")))
                if b.ooo:
                    out.append("  %5d  summary  %d datagrams received out-of-order" % b.ooo)
                out.append("  %5s  %-8s %s: %s" % ("", "", b.kind, b.why))
        for n, why in t.problems:
            out.append("  PROBLEM line %d: %s" % (n, why))
        out.append("  " + fig_line(t, datagram))
    for n, s in rep.outside:
        out.append("  %5d  (outside any trial) %s" % (n, s))
    out.append("RESULT: %s" % ("every trial has a TEST_END figure" if rep.rc() == 0 else
                               "NOT every trial has a clean TEST_END figure (exit 1)"))
    return "\n".join(out)


# ------------------------------------------------------------ the host's client output

def parse_client(lines):
    h = {"reverse": None, "stream": None, "done": None, "msgs": [], "blocks": [], "rows": [],
         "problems": []}
    blk = None
    for n, raw in enumerate(lines, 1):
        s = raw.rstrip(" ")
        if not s or CONNECTING_RE.match(s):
            continue
        if REVERSE_RE.match(s):
            h["reverse"] = n
            continue
        m = CONNECT_RE.match(s)
        if m:
            st = (int(m.group(1)), norm_addr(m.group(2)), int(m.group(3)),
                  norm_addr(m.group(4)), int(m.group(5)), n)
            if h["stream"] is None:
                h["stream"] = st
            else:
                h["problems"].append((n, "a second stream"))
            continue
        if s == DONE_TEXT:
            h["done"] = n
            continue
        m = MSG_RE.match(s)
        if m:
            h["msgs"].append((n, s))
            continue
        if SEP_RE.match(s):
            blk = Block(n)
            h["blocks"].append(blk)
            continue
        m = HEADER_RE.match(s)
        if m:
            if blk is not None and blk.header is None:
                blk.header = (n, " ".join(m.group(1).split()))
            continue
        if SENT_RE.match(s):
            continue
        r = match_row(s, n)
        if r is not None:
            if blk is not None and blk.header is not None and blk.accepts(r):
                blk.rows.append(r)
            else:
                h["rows"].append(r)
            continue
        if SHAPED_RE.match(s):
            h["problems"].append((n, "iperf-shaped line in no format this tool knows: %r" % s))
    return h


# ------------------------------------------------------------ compare

def compare(board_path, board_data, host_path, host_data, datagram, duration, trial_no):
    """Return (rc, output lines); raise Refused when the pair cannot be a control."""
    rep = read_report(board_path, board_data, datagram, duration)
    if not rep.trials:
        raise Refused("the board log holds no trial")
    if trial_no is None:
        if len(rep.trials) != 1:
            raise Refused("the board log holds %d trials; name one with --trial" % len(rep.trials))
        t = rep.trials[0]
    else:
        if trial_no > len(rep.trials):
            raise Refused("--trial %d, but the board log holds %d" % (trial_no, len(rep.trials)))
        t = rep.trials[trial_no - 1]
    if t.role != "receiver":
        raise Refused("board trial %d: the board was the sender; the control reads board-receives "
                      "trials" % t.index)
    te = test_end_block(t)
    if te is None:
        kinds = ", ".join(b.kind for b in t.blocks()) or "none"
        raise Refused("board trial %d has no TEST_END summary (summaries: %s): nothing to compare"
                      % (t.index, kinds))
    if t.problems:
        raise Refused("board trial %d is inconsistent: line %d: %s" % ((t.index,) + t.problems[0]))
    h = parse_client(text_lines(host_data))
    if h["done"] is None or h["msgs"]:
        why = h["msgs"][0][1] if h["msgs"] else "no 'iperf Done.' line"
        raise Refused("the host did not see this trial complete (%s): it cannot be the positive "
                      "control" % why)
    if h["reverse"] is not None:
        raise Refused("the host ran -R (line %d): the board sent; the control reads board-receives "
                      "trials" % h["reverse"])
    if h["problems"]:
        raise Refused("host output line %d: %s" % h["problems"][0])
    hb = [b for b in h["blocks"] if b.complete()]
    if len(hb) != 1:
        raise Refused("the host output holds %d complete summaries, want 1" % len(hb))
    hrow = hb[0].row()
    if hb[0].proto() != t.proto:
        raise Refused("the board trial is %s and the host's is %s: not the same trial"
                      % (t.proto, hb[0].proto()))
    bs, hs = t.stream, h["stream"]
    if bs is None or hs is None:
        raise Refused("no '[ N] local ... connected to ...' line on the %s side"
                      % ("board" if bs is None else "host"))
    if (bs[1], bs[2], bs[3], bs[4]) != (hs[3], hs[4], hs[1], hs[2]):
        raise Refused("not the same trial: board stream %s:%d <- %s:%d (line %d), host stream "
                      "%s:%d -> %s:%d (line %d)" % (bs[1], bs[2], bs[3], bs[4], bs[5],
                                                    hs[1], hs[2], hs[3], hs[4], hs[5]))
    brow = te.row()
    out = ["iperflog %s compare" % TOOL_VERSION,
           "  board: %s trial %d, TEST_END line %d: %s" % (board_path, t.index, brow.line, brow.text),
           "  host:  %s line %d: %s" % (host_path, hrow.line, hrow.text),
           "  stream: board %s:%d <- %s:%d (line %d) is host %s:%d -> %s:%d (line %d)"
           % (bs[1], bs[2], bs[3], bs[4], bs[5], hs[1], hs[2], hs[3], hs[4], hs[5])]
    bad = []
    if t.proto == "tcp":
        same = brow.transfer.text == hrow.transfer.text
        out.append("  transfer: board \"%s\", host \"%s\": %s" % (
            brow.transfer.text, hrow.transfer.text,
            "identical, as one integer through one formatter must be" if same else "DIFFERENT"))
        if not same:
            bad.append("transfer columns differ (%s vs %s); they print one integer the same way"
                       % (brow.transfer.text, hrow.transfer.text))
        ivs = [("board rate x end", bits_rate(brow)), ("host rate x end", bits_rate(hrow)),
               ("board transfer x 8", bits_xfer(brow)), ("host transfer x 8", bits_xfer(hrow))]
        for name, iv in ivs:
            out.append("  bits: %-18s [%s, %s]" % (name, fmt(iv[0]) if iv else "-", fmt(iv[1]) if iv else "-"))
        common = meet([iv for _n, iv in ivs])
        if common is None:
            bad.append("no bit count satisfies all four printed bounds: the board figure is not "
                       "the host's within the two lines' rounding")
            out.append("  bits: common             none")
        else:
            out.append("  bits: common             [%s, %s]" % (fmt(common[0]), fmt(common[1])))
    else:
        same = (brow.lost, brow.total) == (hrow.lost, hrow.total)
        out.append("  lost/total: board %d/%d, host %d/%d: %s" % (
            brow.lost, brow.total, hrow.lost, hrow.total,
            "equal, as the integers the results exchange carried must be" if same else "DIFFERENT"))
        if not same:
            bad.append("lost/total differ (%d/%d vs %d/%d)" % (brow.lost, brow.total, hrow.lost, hrow.total))
        dj = abs(brow.jitter.value - hrow.jitter.value)
        out.append("  jitter: board %s, host %s: difference %s ms, allowed %s (double rounding)" % (
            brow.jitter.text, hrow.jitter.text, fmt(dj, 3), fmt(JITTER_TOL_MS, 3)))
        if dj > JITTER_TOL_MS:
            bad.append("jitter differs by %s ms, more than double rounding allows" % fmt(dj, 3))
        out.append("  (the host's rate, %s, is its own send rate and is not compared)" % hrow.rate.text)
    out.append("  " + fig_line(t, datagram))
    if bad:
        out.append("DISAGREE: " + "; ".join(bad))
        return 1, out
    out.append("AGREE: the board log's figure is the host's within both lines' printed rounding")
    return 0, out


# ------------------------------------------------------------ command line

def build_parser():
    ap = argparse.ArgumentParser(prog="iperflog.py", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version="iperflog " + TOOL_VERSION)
    ap.add_argument("--self-test", action="store_true", help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")
    for name, helptext in (("parse", "rows, summaries and the FIGURE of every trial in LOG"),
                           ("compare", "the positive control: BOARD_LOG's figure against the host's")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--datagram", type=int, default=1400,
                       help="UDP datagram size in bytes, the host's -l (default 1400, card B)")
        p.add_argument("--duration", type=float, default=None,
                       help="the client's -t, to tell a TEST_END summary flushed at a kill from "
                            "the SIGTERM handler's own")
        if name == "parse":
            p.add_argument("log", help="a console capture's .log, or a plain server log")
        else:
            p.add_argument("--trial", type=int, default=None, help="which trial of BOARD_LOG (1-based)")
            p.add_argument("board", help="the board's server log, or the capture holding it")
            p.add_argument("host", help="the host's iperf3 client output for the same trial")
    return ap


def refuse_args(a):
    """Refuse from the parsed arguments alone: no file, environment, clock or device is read."""
    if a.self_test:
        if a.cmd is not None:
            raise Refused("--self-test takes no subcommand")
        return
    if a.cmd is None:
        raise Refused("name a subcommand: parse or compare (or --self-test)")
    if not 1 <= a.datagram <= MAX_UDP_BLOCKSIZE:
        raise Refused("--datagram %d: iperf 3.1.3 accepts 1..%d (iperf.h:316, iperf_api.c:996)"
                      % (a.datagram, MAX_UDP_BLOCKSIZE))
    if a.duration is not None and not (math.isfinite(a.duration) and a.duration > 0):
        raise Refused("--duration %r: must be a finite number of seconds above 0" % a.duration)
    if a.cmd == "parse":
        if not a.log:
            raise Refused("LOG is empty")
    else:
        if a.trial is not None and a.trial < 1:
            raise Refused("--trial %d: trials count from 1" % a.trial)
        if not a.board or not a.host:
            raise Refused("BOARD_LOG and HOST_OUTPUT are both required")
        if a.board == a.host:
            raise Refused("BOARD_LOG and HOST_OUTPUT are the same path: a file always agrees "
                          "with itself")


def read_input(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as e:
        raise Refused("cannot read %s: %s" % (path, e.strerror or e))


def main(argv=None):
    a = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        refuse_args(a)
        if a.self_test:
            return selftest()
        duration = None if a.duration is None else Fraction(a.duration)
        if a.cmd == "parse":
            rep = read_report(a.log, read_input(a.log), a.datagram, duration)
            print(render_report(rep, a.datagram))
            return rep.rc()
        board, host = read_input(a.board), read_input(a.host)
        rc, out = compare(a.board, board, a.host, host, a.datagram, duration, a.trial)
        print("\n".join(out))
        return rc
    except Refused as e:
        print("iperflog: refused: %s" % e, file=sys.stderr)
        return 2


# ------------------------------------------------------------ self-test fixtures
# Real text, copied line for line (genuine trailing spaces kept) from the qemu
# runs of the board's own binary under $FWRE_WORK/rebuild/s107/srvlog/ and from
# committed seating-A captures.  CI has no $FWRE_WORK: nothing below reads a path.
# Where a case edits a real log to make a defect, the case says so.

R6_SRV = (   # srvlog/runs4/R6-logfile-fk-oneoff-udp/server.out: -s -1 -f k --logfile, UDP
    '-----------------------------------------------------------',
    'Server listening on 25229',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 57832',
    '[  6] local 127.0.0.1 port 25229 connected to 127.0.0.1 port 38992',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  6]   0.00-1.00   sec  2.15 MBytes  18058 Kbits/sec  0.004 ms  0/1613 (0%)  ',
    '[  6]   1.00-2.00   sec  2.39 MBytes  20029 Kbits/sec  0.011 ms  0/1788 (0%)  ',
    '[  6]   2.00-4.21   sec   976 KBytes  3627 Kbits/sec  0.012 ms  0/714 (0%)  ',
    '[  6]   4.21-4.21   sec  0.00 Bytes  0.00 Kbits/sec  0.012 ms  0/0 (0%)  ',
    '[  6]   4.21-5.00   sec  6.10 MBytes  64405 Kbits/sec  0.009 ms  71/4642 (1.5%)  ',
    '[  6]   5.00-6.00   sec  2.38 MBytes  19992 Kbits/sec  0.010 ms  0/1785 (0%)  ',
    '[  6]   6.00-7.00   sec  2.38 MBytes  19992 Kbits/sec  0.002 ms  0/1785 (0%)  ',
    '[  6]   7.00-8.00   sec  2.39 MBytes  20014 Kbits/sec  0.006 ms  0/1787 (0%)  ',
    '[  6]   8.00-9.00   sec  2.38 MBytes  20003 Kbits/sec  0.008 ms  0/1786 (0%)  ',
    '[  6]   9.00-10.00  sec  2.38 MBytes  19980 Kbits/sec  0.001 ms  0/1784 (0%)  ',
    '[  6]  10.00-10.04  sec  1.37 KBytes   275 Kbits/sec  0.005 ms  0/1 (0%)  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  6]   0.00-10.04  sec  0.00 Bytes  0.00 Kbits/sec  0.005 ms  71/17685 (0.4%)  ',
)

R6_CLI = (   # srvlog/runs4/R6-logfile-fk-oneoff-udp/client.out
    'Connecting to host 127.0.0.1, port 25229',
    '[  4] local 127.0.0.1 port 38992 connected to 127.0.0.1 port 25229',
    '[ ID] Interval           Transfer     Bandwidth       Total Datagrams',
    '[  4]   0.00-1.00   sec  2.15 MBytes  18.1 Mbits/sec  1614  ',
    '[  4]   1.00-2.00   sec  2.39 MBytes  20.0 Mbits/sec  1788  ',
    '[  4]   2.00-4.17   sec   975 KBytes  3.69 Mbits/sec  713  ',
    '[  4]   4.17-4.17   sec  0.00 Bytes  0.00 Mbits/sec  0  ',
    '[  4]   4.17-5.00   sec  6.20 MBytes  62.3 Mbits/sec  4643  ',
    '[  4]   5.00-6.00   sec  2.38 MBytes  20.0 Mbits/sec  1785  ',
    '[  4]   6.00-7.00   sec  2.38 MBytes  20.0 Mbits/sec  1785  ',
    '[  4]   7.00-8.00   sec  2.39 MBytes  20.0 Mbits/sec  1787  ',
    '[  4]   8.00-9.00   sec  2.38 MBytes  20.0 Mbits/sec  1786  ',
    '[  4]   9.00-10.00  sec  2.38 MBytes  20.0 Mbits/sec  1784  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  4]   0.00-10.00  sec  23.6 MBytes  19.8 Mbits/sec  0.005 ms  71/17685 (0.4%)  ',
    '[  4] Sent 17685 datagrams',
    '',
    'iperf Done.',
)

R5_SRV = (   # srvlog/runs/R5-logfile-udp/server.out: --logfile, UDP, adaptive units
    '-----------------------------------------------------------',
    'Server listening on 25211',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 36012',
    '[  6] local 127.0.0.1 port 25211 connected to 127.0.0.1 port 40489',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  6]   0.00-1.00   sec  2.16 MBytes  18.1 Mbits/sec  0.016 ms  0/1617 (0%)  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  20.0 Mbits/sec  0.009 ms  0/1783 (0%)  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  20.0 Mbits/sec  0.009 ms  0/1786 (0%)  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  20.0 Mbits/sec  0.003 ms  0/1785 (0%)  ',
    '[  6]   4.00-5.00   sec  2.38 MBytes  20.0 Mbits/sec  0.011 ms  3/1787 (0.17%)  ',
    '[  6]   5.00-6.00   sec  2.37 MBytes  19.9 Mbits/sec  0.007 ms  15/1788 (0.84%)  ',
    '[  6]   6.00-8.54   sec  1.90 MBytes  6.29 Mbits/sec  0.035 ms  0/1426 (0%)  ',
    '[  6]   8.54-8.54   sec  0.00 Bytes  0.00 bits/sec  0.035 ms  0/0 (0%)  ',
    '[  6]   8.54-9.00   sec  5.14 MBytes  93.3 Mbits/sec  0.026 ms  78/3931 (2%)  ',
    '[  6]   9.00-10.00  sec  2.38 MBytes  20.0 Mbits/sec  0.003 ms  0/1783 (0%)  ',
    '[  6]  10.00-10.04  sec  1.37 KBytes   300 Kbits/sec  0.012 ms  0/1 (0%)  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  6]   0.00-10.04  sec  0.00 Bytes  0.00 bits/sec  0.012 ms  96/17687 (0.54%)  ',
    '-----------------------------------------------------------',
    'Server listening on 25211',
    '-----------------------------------------------------------',
    'iperf3: interrupt - the server has terminated',
)

R5_CLI = (   # srvlog/runs/R5-logfile-udp/client.out
    'Connecting to host 127.0.0.1, port 25211',
    '[  4] local 127.0.0.1 port 40489 connected to 127.0.0.1 port 25211',
    '[ ID] Interval           Transfer     Bandwidth       Total Datagrams',
    '[  4]   0.00-1.00   sec  2.16 MBytes  18.1 Mbits/sec  1618  ',
    '[  4]   1.00-2.00   sec  2.38 MBytes  20.0 Mbits/sec  1783  ',
    '[  4]   2.00-3.00   sec  2.38 MBytes  20.0 Mbits/sec  1786  ',
    '[  4]   3.00-4.00   sec  2.38 MBytes  20.0 Mbits/sec  1785  ',
    '[  4]   4.00-5.00   sec  2.39 MBytes  20.0 Mbits/sec  1787  ',
    '[  4]   5.00-6.00   sec  2.39 MBytes  20.0 Mbits/sec  1788  ',
    '[  4]   6.00-8.50   sec  1.90 MBytes  6.38 Mbits/sec  1425  ',
    '[  4]   8.50-8.50   sec  0.00 Bytes  0.00 Mbits/sec  0  ',
    '[  4]   8.50-9.00   sec  5.25 MBytes  88.4 Mbits/sec  3932  ',
    '[  4]   9.00-10.00  sec  2.38 MBytes  20.0 Mbits/sec  1783  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams',
    '[  4]   0.00-10.00  sec  23.6 MBytes  19.8 Mbits/sec  0.012 ms  96/17687 (0.54%)  ',
    '[  4] Sent 17687 datagrams',
    '',
    'iperf Done.',
)

R1_SRV = (   # srvlog/sanity1/R1-logfile-tcp/server.out: --logfile, TCP, adaptive units
    '-----------------------------------------------------------',
    'Server listening on 25203',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 44150',
    '[  6] local 127.0.0.1 port 25203 connected to 127.0.0.1 port 44152',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   4.00-5.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   5.00-6.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   6.00-7.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   7.00-8.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   8.00-9.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   9.00-10.00  sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]  10.00-10.02  sec   128 KBytes  52.0 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-10.02  sec  0.00 Bytes  0.00 bits/sec                  sender',
    '[  6]   0.00-10.02  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    '-----------------------------------------------------------',
    'Server listening on 25203',
    '-----------------------------------------------------------',
    'iperf3: interrupt - the server has terminated',
)

R1_CLI = (   # srvlog/sanity1/R1-logfile-tcp/client.out
    'Connecting to host 127.0.0.1, port 25203',
    '[  4] local 127.0.0.1 port 44152 connected to 127.0.0.1 port 25203',
    '[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd',
    '[  4]   0.00-5.00   sec  11.9 MBytes  19.9 Mbits/sec  4218612   0.00 Bytes       ',
    '[  4]   5.00-10.00  sec  11.9 MBytes  19.9 Mbits/sec  4290748793   0.00 Bytes       ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Retr',
    '[  4]   0.00-10.00  sec  23.8 MBytes  19.9 Mbits/sec  109             sender',
    '[  4]   0.00-10.00  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    '',
    'iperf Done.',
)

R3_SRV = (   # srvlog/runs/R3-pty-tcp/server.out: stdout on a pty, CRLF in the file
    '-----------------------------------------------------------',
    'Server listening on 25207',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 60822',
    '[  5] local 127.0.0.1 port 25207 connected to 127.0.0.1 port 60832',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  5]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  5]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]   4.00-6.03   sec  1.13 MBytes  4.64 Mbits/sec                  ',
    '[  5]   6.03-6.03   sec  0.00 Bytes  0.00 bits/sec                  ',
    '[  5]   6.03-7.00   sec  6.00 MBytes  52.1 Mbits/sec                  ',
    '[  5]   7.00-8.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]   8.00-9.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]   9.00-10.00  sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  5]  10.00-10.03  sec   128 KBytes  33.2 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  5]   0.00-10.03  sec  0.00 Bytes  0.00 bits/sec                  sender',
    '[  5]   0.00-10.03  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    '-----------------------------------------------------------',
    'Server listening on 25207',
    '-----------------------------------------------------------',
    'iperf3: interrupt - the server has terminated',
)

R3_CLI = (   # srvlog/runs/R3-pty-tcp/client.out
    'Connecting to host 127.0.0.1, port 25207',
    '[  4] local 127.0.0.1 port 60832 connected to 127.0.0.1 port 25207',
    '[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd',
    '[  4]   0.00-6.01   sec  10.5 MBytes  14.7 Mbits/sec    0   0.00 Bytes       ',
    '[  4]   6.01-10.00  sec  13.3 MBytes  27.8 Mbits/sec   94   0.00 Bytes       ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Retr',
    '[  4]   0.00-10.00  sec  23.8 MBytes  19.9 Mbits/sec   94             sender',
    '[  4]   0.00-10.00  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    '',
    'iperf Done.',
)

K1_SRV = (   # srvlog/runs/K1-logfile-srvKILL/server.out: server SIGKILL'd at +5 s
    '-----------------------------------------------------------',
    'Server listening on 25213',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 43106',
    '[  6] local 127.0.0.1 port 25213 connected to 127.0.0.1 port 43108',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
)

K3_SRV = (   # srvlog/runs/K3-logfile-cliKILL/server.out: client SIGKILL'd at +5 s
    '-----------------------------------------------------------',
    'Server listening on 25217',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 38704',
    '[  6] local 127.0.0.1 port 25217 connected to 127.0.0.1 port 38706',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-5.78   sec  2.25 MBytes  6.79 Mbits/sec                  ',
    '[  6]   5.78-5.78   sec  0.00 Bytes  0.00 bits/sec                  ',
    '[  6]   5.78-6.00   sec  4.88 MBytes   186 Mbits/sec                  ',
    'iperf3: the client has unexpectedly closed the connection',
    '-----------------------------------------------------------',
    'Server listening on 25217',
    '-----------------------------------------------------------',
    'iperf3: interrupt - the server has terminated',
)

K4_SRV = (   # srvlog/runs/K4-logfile-cliTERM/server.out: client SIGTERM'd at +5 s
    '-----------------------------------------------------------',
    'Server listening on 25219',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 52794',
    '[  6] local 127.0.0.1 port 25219 connected to 127.0.0.1 port 52810',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-4.00   sec  0.00 Bytes  0.00 bits/sec                  sender',
    '[  6]   0.00-4.00   sec  11.5 MBytes  24.1 Mbits/sec                  receiver',
    'iperf3: the client has terminated',
    '-----------------------------------------------------------',
    'Server listening on 25219',
    '-----------------------------------------------------------',
    'iperf3: interrupt - the server has terminated',
)

K5C_SRV = (   # srvlog/runs/K5c-oneoff-lost/server.out: -1, the results frame dropped (NET-112's shape)
    '-----------------------------------------------------------',
    'Server listening on 25225',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 49452',
    '[  6] local 127.0.0.1 port 25225 connected to 127.0.0.1 port 49464',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   4.00-6.14   sec   640 KBytes  2.45 Mbits/sec                  ',
    '[  6]   6.14-6.14   sec  0.00 Bytes  0.00 bits/sec                  ',
    '[  6]   6.14-7.00   sec  6.50 MBytes  63.2 Mbits/sec                  ',
    '[  6]   7.00-8.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   8.00-9.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   9.00-10.00  sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]  10.00-10.03  sec   128 KBytes  41.5 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-10.03  sec  0.00 Bytes  0.00 bits/sec                  sender',
    '[  6]   0.00-10.03  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    '[  6]  10.00-10.03  sec   128 KBytes  41.5 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Retr',
    '[  6]   0.00-10.03  sec  23.8 MBytes  19.9 Mbits/sec   91             sender',
    '[  6]   0.00-10.03  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    'iperf3: the client has terminated',
)

K5C_CLI = (   # srvlog/runs/K5c-oneoff-lost/client.out: killed by its timeout, no results
    'Connecting to host 127.0.0.1, port 25226',
    '[  4] local 127.0.0.1 port 52640 connected to 127.0.0.1 port 25226',
    '[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd',
    '[  4]   0.00-6.11   sec  10.0 MBytes  13.7 Mbits/sec    0   0.00 Bytes       ',
    '[  4]  10.00-17.80  sec  0.00 Bytes  0.00 Mbits/sec    1   0.00 Bytes       ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Retr',
    '[  4]   0.00-17.80  sec  23.8 MBytes  11.2 Mbits/sec   92             sender',
    '[  4]   0.00-17.80  sec  0.00 Bytes  0.00 Mbits/sec                  receiver',
    'iperf3: interrupt - the client has terminated',
)

K6_SRV = (   # srvlog/runs2/K6-logfile-deaf-TERM/server.out: never heard the client's end
    '-----------------------------------------------------------',
    'Server listening on 25229',
    '-----------------------------------------------------------',
    'Accepted connection from 127.0.0.1, port 44484',
    '[  6] local 127.0.0.1 port 25229 connected to 127.0.0.1 port 44496',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-1.00   sec  2.25 MBytes  18.9 Mbits/sec                  ',
    '[  6]   1.00-2.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   2.00-3.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   3.00-4.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   4.00-5.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   5.00-6.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   6.00-7.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   7.00-8.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   8.00-9.00   sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]   9.00-10.00  sec  2.38 MBytes  19.9 Mbits/sec                  ',
    '[  6]  10.00-10.00  sec   128 KBytes   357 Mbits/sec                  ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth',
    '[  6]   0.00-10.00  sec  0.00 Bytes  0.00 bits/sec                  sender',
    '[  6]   0.00-10.00  sec  23.8 MBytes  19.9 Mbits/sec                  receiver',
    'iperf3: interrupt - the server has terminated',
)

ER1_HOST = (   # bench/2026-09-23/P1-ER1.log: seating A, eth4, a completed board-receives trial
    'Connecting to host 10.1.1.4, port 5201',
    '[  4] local 10.1.1.2 port 33640 connected to 10.1.1.4 port 5201',
    '[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd',
    '[  4]   0.00-5.00   sec  15.1 MBytes  25.3 Mbits/sec  4698944   0.00 Bytes       ',
    '[  4]   5.00-10.00  sec  15.0 MBytes  25.1 Mbits/sec    0   0.00 Bytes       ',
    '[  4]  10.00-15.00  sec  13.0 MBytes  21.8 Mbits/sec    0   0.00 Bytes       ',
    '[  4]  15.00-20.00  sec  14.9 MBytes  25.0 Mbits/sec    0   0.00 Bytes       ',
    '[  4]  20.00-25.00  sec  14.8 MBytes  24.8 Mbits/sec    0   0.00 Bytes       ',
    '[  4]  25.00-30.00  sec  14.8 MBytes  24.8 Mbits/sec  4290269372   0.00 Bytes       ',
    '- - - - - - - - - - - - - - - - - - - - - - - - -',
    '[ ID] Interval           Transfer     Bandwidth       Retr',
    '[  4]   0.00-30.00  sec  87.5 MBytes  24.5 Mbits/sec  1020             sender',
    '[  4]   0.00-30.00  sec  87.3 MBytes  24.4 Mbits/sec                  receiver',
    '',
    'iperf Done.',
)

STAT_S1 = (   # bench/2026-09-23/P1-ER1-S1.log lines 2-9: `cat /proc/stat` on the board, CRLF
    'cpu  985 0 5195 145558 0 0 19262 0 0',
    'cpu0 985 0 5195 145558 0 0 19262 0 0',
    'intr 807461 0 0 0 0 0 0 0 0 56114 0 0 0 409315 171066 0 0 0 0 0 0 0 0 0 0 0 170966 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0',
    'ctxt 46165',
    'btime 0',
    'processes 130',
    'procs_running 2',
    'procs_blocked 0',
)

NIC_HEAD = (   # bench/2026-09-23/P1-TR1-S1.log lines 10-20: `cat /proc/rtl819x-nic`, CRLF
    'version rtl819x-nic 1.4',
    'unlocked 1',
    'allocated 1',
    'armed 1',
    'engine_on 1',
    'irq_taken 1',
    'irq_rc 0',
    'n_reads 33991',
    'n_writes 30',
    'n_refused 0',
    'n_irq 86841',
)

# REPORT.md section 3 B's -S1 send for an rlx0 trial.  ash echoes a command past
# 78 columns (80 less the "# " prompt) with CR CR LF: 量 bench/2026-09-20b/X3-frag.log
# and bench/2026-09-09b/X5-blink.log both break there.
S1_SEND = "cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/UR1.log ; cat /proc/rtl819x-nic"


def lf(lines):
    return ("\n".join(lines) + "\n").encode("latin-1")


def crlf(lines):
    return ("\r\n".join(lines) + "\r\n").encode("latin-1")


def console_capture(log_lines):
    """What card B's -S1 capture holds: echo (wrapped), /proc/stat, the log, the NIC dump, the prompt."""
    echo = S1_SEND[:78] + "\r\r\n" + S1_SEND[78:] + "\r\n"
    return (echo.encode("latin-1") + crlf(STAT_S1) + crlf(log_lines) + crlf(NIC_HEAD) + b"# ")


def edit(lines, index, old, new):
    """A copy of a real log with one line edited; the edit must apply exactly once."""
    out = list(lines)
    assert out[index].count(old) == 1, (index, old, out[index])
    out[index] = out[index].replace(old, new)
    return tuple(out)


# ------------------------------------------------------------ self-test

def selftest():
    results = []

    def case(cid, what, fn):
        try:
            fn()
        except AssertionError as e:
            results.append((cid, what, "FAIL", str(e) or "assertion"))
        except Exception as e:                                   # noqa: BLE001
            results.append((cid, what, "FAIL", "%s: %s" % (type(e).__name__, e)))
        else:
            results.append((cid, what, "ok", ""))

    def rep_of(data, datagram=1400, duration=None):
        return read_report("fixture", data, datagram, None if duration is None else Fraction(duration))

    def only(rep):
        assert len(rep.trials) == 1, ("trials", len(rep.trials))
        return rep.trials[0]

    def kept_lines(t):
        return [r.line for r in t.rows("kept")]

    def run_compare(board, host, trial=None, duration=None):
        try:
            return compare("board", board, "host", host, 1400,
                           None if duration is None else Fraction(duration), trial)
        except Refused as e:
            return 2, [str(e)]

    # U -- the printed-number model (units.c:316-331)
    def u1():
        n = Num("2.38", BYTE_SCALE["M"], "")
        assert (n.value, n.half) == (Fraction(238, 100) * 1048576, Fraction(1, 200) * 1048576), "MBytes"
        n = Num("18058", BIT_SCALE["K"], "")
        assert (n.value, n.half) == (18058000, 500), ("Kbits: whole Kbit/s, half 500", n.value, n.half)
        n = Num("1010", BYTE_SCALE["K"], "")
        assert n.half == 512, ("four digits in [1000,1024): half of 1 KiB", n.half)
        n = Num("0.00", 1, "")
        assert (n.value, n.half) == (0, Fraction(1, 200)), "zero keeps its half-unit"
        assert Num("inf", 1000, "").value is None, "a non-finite rate carries no value"
        r = match_row("[  6]   0.00-10.04  sec  0.00 Bytes  0.00 Kbits/sec  0.005 ms  17685/17685 (1e+02%)", 1)
        assert r is not None and r.pct == "1e+02", "%.2g prints 100 as 1e+02"
    case("U1", "printed numbers: value and half-unit from the digits; 100 % as 1e+02", u1)

    # P -- parse, on real logs
    def p1():
        rep = rep_of(lf(R6_SRV))
        t = only(rep)
        assert (t.proto, t.role) == ("udp", "receiver"), (t.proto, t.role)
        assert kept_lines(t) == list(range(7, 18)), kept_lines(t)
        assert [b.kind for b in t.blocks()] == ["TEST_END"], [b.kind for b in t.blocks()]
        f = t.figure
        assert (f.source, f.lines) == ("TEST_END", "20"), (f.source, f.lines)
        assert (f.total, f.lost, f.ooo, f.received) == (17685, 71, 0, 17614), (f.total, f.lost, f.received)
        assert f.nbytes == 24659600, ("(17685 - 71) x 1400, exactly", f.nbytes)
        assert f.rate_lo == Fraction(197276800) / Fraction("10.045"), f.rate_lo
        assert f.rate_hi == Fraction(197276800) / Fraction("10.035"), f.rate_hi
        assert not t.problems and rep.rc() == 0, (t.problems, rep.rc())
    case("P1", "UDP -f k -1 (R6): 11 intervals, TEST_END, 24,659,600 B exact over 10.04 +/- 0.005 s", p1)

    def p2():
        t = only(rep_of(lf(R5_SRV)))
        f = t.figure
        assert (f.total, f.lost, f.received, f.nbytes) == (17687, 96, 17591, 24627400), (
            f.total, f.lost, f.received, f.nbytes)
        assert sum(r.lost for r in t.rows("kept")) == 96, "interval losses 3 + 15 + 78"
        assert not t.problems, t.problems
    case("P2", "UDP adaptive (R5): losses in three intervals, a zero-length one; 17,591 received", p2)

    def p3():
        rep = rep_of(lf(K4_SRV))
        t = only(rep)
        assert kept_lines(t) == [7, 8, 9, 10], kept_lines(t)
        assert t.rows()[4].status.startswith("dropped: CLIENT_TERMINATE re-print of line 10"), t.rows()[4].status
        assert [b.kind for b in t.blocks()] == ["CLIENT_TERMINATE"], [b.kind for b in t.blocks()]
        f = t.figure
        assert f.source == "intervals", ("the stale 24.1 Mbit/s summary is never the figure", f.source)
        assert (f.bytes_lo, f.bytes_hi) == (Fraction("9.37") * 1048576, Fraction("9.41") * 1048576), (
            "2.25 + 3 x 2.38 MiB, +/- 4 half-units", f.bytes_lo, f.bytes_hi)
        assert f.rate_hi < Fraction("24.05e6"), ("below the stale summary's 24.1", f.rate_hi)
        assert not t.problems and rep.rc() == 1, (t.problems, rep.rc())
    case("P3", "client SIGTERM mid-test (K4): re-print dropped, stale summary ignored, exit 1", p3)

    def p4():
        rep = rep_of(lf(K5C_SRV))
        t = only(rep)
        assert kept_lines(t) == list(range(7, 18)), kept_lines(t)
        assert [b.kind for b in t.blocks()] == ["TEST_END", "CLIENT_TERMINATE"], [b.kind for b in t.blocks()]
        assert t.rows()[-1].line == 22 and t.rows()[-1].status.startswith("dropped"), t.rows()[-1].status
        f = t.figure
        assert (f.source, f.lines, f.row.rate.text) == ("TEST_END", "21", "19.9 Mbits/sec"), (
            f.source, f.lines, f.row.rate.text)
        assert rep.rc() == 0, (t.problems, rep.rc())
    case("P4", "results lost, -1 (K5c): first summary used (line 21), re-print dropped, exit 0", p4)

    def p5():
        rep = rep_of(lf(R1_SRV))
        t = only(rep)
        assert [b.kind for b in t.blocks()] == ["TEST_END"], ("the 'interrupt' after 'Server "
                                                               "listening' is not this trial's",
                                                               [b.kind for b in t.blocks()])
        f = t.figure
        assert (f.bytes_lo, f.bytes_hi) == (Fraction("23.75") * 1048576, Fraction("199998750") / 8), (
            "transfer's floor, rate x end's ceiling", f.bytes_lo, f.bytes_hi)
        assert rep.outside and rep.outside[0][0] == 25, rep.outside
        assert rep.rc() == 0, (t.problems, rep.rc())
    case("P5", "TCP adaptive (R1): TEST_END; the idle server's 'interrupt' stays outside the trial", p5)

    def p6():
        t = only(rep_of(lf(K6_SRV)))
        assert t.blocks()[0].kind == "TEST_END-or-SIGTERM" and t.figure.source == "intervals", (
            "without --duration it does not guess", t.blocks()[0].kind)
        t = only(rep_of(lf(K6_SRV), duration=10))
        assert t.blocks()[0].kind == "TEST_END" and t.ok(), ("ends at 10.00, --duration 10", t.problems)
        t = only(rep_of(lf(K6_SRV), duration=30))
        assert t.blocks()[0].kind == "SIGTERM" and not t.ok(), ("20 s from --duration 30", t.blocks()[0].kind)
    case("P6", "deaf (K6): summary + 'interrupt' is TEST_END only with --duration in reach", p6)

    def p7():
        rep = rep_of(lf(K1_SRV))
        t = only(rep)
        assert t.blocks() == [] and t.figure.source == "intervals", t.figure.source
        assert t.figure.bytes_hi == Fraction("9.41") * 1048576, t.figure.bytes_hi
        assert not t.problems and rep.rc() == 1, (t.problems, rep.rc())
    case("P7", "server SIGKILL (K1): intervals only, their sum is the fallback, exit 1", p7)

    def p8():
        t = only(rep_of(lf(K3_SRV)))
        assert kept_lines(t) == [7, 8, 9, 10, 11, 12], kept_lines(t)
        assert t.figure.bytes_lo == Fraction("14.115") * 1048576, ("0.00 Bytes floors at 0", t.figure.bytes_lo)
        assert ("msg", 13, "the client has unexpectedly closed the connection") in t.events
        assert not t.problems, t.problems
    case("P8", "client SIGKILL (K3): zero-length interval kept, no summary, message recorded", p8)

    def p9():
        rep = rep_of(console_capture(R6_SRV))
        t = only(rep)
        f = t.figure
        assert (f.source, f.lines, f.nbytes) == ("TEST_END", "30", 24659600), (
            "2 echo + 8 /proc/stat lines before the log's 20", f.source, f.lines, f.nbytes)
        assert rep.rc() == 0, (t.problems, rep.rc())
    case("P9", "card B's CRLF -S1 capture (echo wrapped CR CR LF, /proc text, prompt): P1's figure", p9)

    def p10():
        rep = rep_of(crlf(R3_SRV))
        t = only(rep)
        assert t.figure.source == "TEST_END" and t.figure.row.end.text == "10.03", t.figure.source
        assert rep.rc() == 0, (t.problems, rep.rc())
    case("P10", "real CRLF from a pty (R3): TEST_END at 10.03", p10)

    def p11():
        t = only(rep_of(lf(K1_SRV[:7] + K1_SRV[8:])))
        assert any(n == 8 and "ended at 1.00" in w for n, w in t.problems), t.problems
    case("P11", "K1 with its 1.00-2.00 line removed (edited): the gap is named", p11)

    def p12():
        t = only(rep_of(lf(edit(R6_SRV, 6, "0/1613", "0/1612"))))
        assert [w for _n, w in t.problems if "sum to 71/17684" in w], t.problems
        assert len(t.problems) == 1, ("only the sum can see a one-datagram edit", t.problems)
    case("P12", "R6 with one interval total changed by one (edited): only the exact sum fires", p12)

    def p13():
        t = only(rep_of(lf(R6_SRV), datagram=1470))
        assert any("datagram size is not 1470" in w for _n, w in t.problems), t.problems
        assert not only(rep_of(lf(R5_SRV), datagram=1400)).problems, "1400 fits R5 too"
    case("P13", "--datagram 1470 on R6 is refused by the transfer columns; 1400 fits", p13)

    def p14():
        t = only(rep_of(lf(edit(K4_SRV, 10, "2.38 MBytes", "2.37 MBytes"))))
        assert any("does not repeat the last interval kept (line 10)" in w for _n, w in t.problems), t.problems
    case("P14", "K4 with its re-print altered (edited): a non-repeat is flagged, not dropped", p14)

    def p15():
        t = only(rep_of(lf(edit(R1_SRV, 9, "[  6]", "[  7]"))))
        assert any("stream [  7]" in w for _n, w in t.problems), t.problems
    case("P15", "R1 with one line on stream 7 (edited): a second stream is flagged", p15)

    def p16():
        t = only(rep_of(lf(R1_SRV[:5] + R1_CLI[2:5])))
        assert t.role == "sender" and t.problems and "sender" in t.problems[0][1], t.problems
    case("P16", "sender-format lines (the qemu client's own, under a server banner): refused as -R", p16)

    def p17():
        rep = rep_of(console_capture(()))
        assert rep.trials == [] and rep.rc() == 1, (rep.trials, rep.rc())
        rep = rep_of(lf(K1_SRV[5:]))
        assert rep.trials == [] and rep.stray and rep.rc() == 1, (rep.stray, rep.rc())
    case("P17", "no trial (empty log; lines with no 'Accepted connection'): exit 1, stray named", p17)

    def p18():
        # iperf_locale.c:336 report_sum_outoforder, printed after the UDP summary line
        t = only(rep_of(lf(R6_SRV + ("[SUM]  0.0-10.0 sec  2 datagrams received out-of-order",))))
        f = t.figure
        assert (f.ooo, f.received, f.nbytes) == (2, 17616, 24662400), (
            "a late datagram was counted lost and never un-counted: add it back", f.ooo, f.received)
        assert f.lines == "20,21" and not t.problems, ("both source lines cited", f.lines, t.problems)
    case("P18", "R6 plus a 2-datagram out-of-order line (edited): received = total - lost + 2", p18)

    # C -- compare, the positive control
    def c1():
        rc, out = run_compare(lf(R1_SRV), lf(R1_CLI))
        assert rc == 0 and out[-1].startswith("AGREE"), (rc, out[-1:])
        common = [ln for ln in out if ln.startswith("  bits: common")]
        assert common and common[0].endswith("[199229440, 199599750]"), common
    case("C1", "TCP (R1 board vs its client): AGREE, common bits [199229440, 199599750]", c1)

    def c2():
        rc, out = run_compare(lf(R6_SRV), lf(R6_CLI))
        assert rc == 0 and out[-1].startswith("AGREE"), (rc, out[-1:])
    case("C2", "UDP (R6 -f k board vs its -f m client): lost/total and jitter agree", c2)

    def c3():
        rc, out = run_compare(crlf(R3_SRV), lf(R3_CLI))
        assert rc == 0, (rc, out)
    case("C3", "TCP with a CRLF board log (R3): AGREE", c3)

    def c4():
        rc, out = run_compare(lf(R1_SRV), lf(edit(R1_CLI, 8, "19.9 Mbits", "19.6 Mbits")))
        assert rc == 1 and "no bit count satisfies" in out[-1], (rc, out[-1:])
    case("C4", "host receiver rate 19.9 -> 19.6 (edited): DISAGREE on the bits", c4)

    def c5():
        rc, out = run_compare(lf(R1_SRV), lf(edit(R1_CLI, 8, "23.8 MBytes", "23.7 MBytes")))
        assert rc == 1 and "transfer columns differ" in out[-1], (rc, out[-1:])
        assert "no bit count" not in out[-1], "the bounds touch at 23.75 MiB: only equality sees it"
    case("C5", "host transfer 23.8 -> 23.7 (edited): only the exact transfer check fires", c5)

    def c6():
        rc, out = run_compare(lf(R6_SRV), lf(edit(R6_CLI, 15, "71/17685", "72/17685")))
        assert rc == 1 and "lost/total differ" in out[-1], (rc, out[-1:])
    case("C6", "host lost 71 -> 72 (edited): DISAGREE on the integers", c6)

    def c7():
        rc, out = run_compare(lf(K5C_SRV), lf(K5C_CLI))
        assert rc == 2 and "did not see this trial complete" in out[0], (rc, out)
    case("C7", "K5c board vs its killed client: refused, the host cannot be the control", c7)

    def c8():
        rc, out = run_compare(lf(R6_SRV), lf(R5_CLI))
        assert rc == 2 and "not the same trial" in out[0], (rc, out)
        rc, out = run_compare(lf(R1_SRV), lf(ER1_HOST))
        assert rc == 2 and "not the same trial" in out[0], (rc, out)
    case("C8", "two complete but different trials (R6/R5, R1/seating A's ER1): refused", c8)

    def c9():
        rc, out = run_compare(lf(K4_SRV), lf(R1_CLI))
        assert rc == 2 and "no TEST_END summary" in out[0], (rc, out)
        rc, out = run_compare(lf(R6_SRV), lf(R1_CLI))
        assert rc == 2 and "udp and the host's is tcp" in out[0], (rc, out)
    case("C9", "a board log with no TEST_END summary; UDP against TCP: refused", c9)

    def c10():
        rc, out = run_compare(lf(K6_SRV), lf(R1_CLI))
        assert rc == 2 and "no TEST_END summary" in out[0], (rc, out)
        rc, out = run_compare(lf(R1_SRV + K1_SRV), lf(R1_CLI))
        assert rc == 2 and "name one with --trial" in out[0], (rc, out)
        rc, out = run_compare(lf(R1_SRV + K1_SRV), lf(R1_CLI), trial=1)
        assert rc == 0, (rc, out)
    case("C10", "K6 without --duration refused; two trials need --trial, and --trial 1 agrees", c10)

    # F -- the FW-124 contract
    def f1():
        refuse = (["parse", "--datagram", "0", "x.log"], ["parse", "--datagram", "65508", "x.log"],
                  ["parse", "--duration", "0", "x.log"], ["parse", "--duration", "nan", "x.log"],
                  ["parse", "--duration", "inf", "x.log"], ["compare", "--trial", "0", "a", "b"],
                  ["compare", "a.log", "a.log"], [], ["--self-test", "parse", "x.log"])
        for argv in refuse:
            try:
                refuse_args(build_parser().parse_args(argv))
            except Refused:
                continue
            raise AssertionError("permitted %r" % argv)
        permit = (["parse", "x.log"], ["parse", "--datagram", "1400", "--duration", "30", "x.log"],
                  ["compare", "--trial", "1", "--datagram", "65507", "a.log", "b.log"], ["--self-test"])
        for argv in permit:
            refuse_args(build_parser().parse_args(argv))
    case("F1", "refuse_args refuses 9 bad argument sets and permits the 4 good forms, in-process", f1)

    def f2():
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = main(["parse", "--datagram", "0", "/nonexistent/iperflog-fixture.log"])
        assert rc == 2 and "--datagram 0" in err.getvalue(), ("the argument, not the file", rc, err.getvalue())
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = main(["parse", "/nonexistent/iperflog-fixture.log"])
        assert rc == 2 and "cannot read" in err.getvalue(), (rc, err.getvalue())
    case("F2", "main() refuses the argument before opening the file; a good one reaches the file", f2)

    for cid, what, st, why in results:
        if st == "ok":
            print("  ok    %-4s %s" % (cid, what))
        else:
            print("  FAIL  %-4s %s -- %s" % (cid, what, why))
    nbad = sum(1 for r in results if r[2] != "ok")
    print("RESULT: %d/%d" % (len(results) - nbad, len(results)))
    return 1 if nbad else 0


if __name__ == "__main__":
    sys.exit(main())
