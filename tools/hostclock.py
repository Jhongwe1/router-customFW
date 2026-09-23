#!/usr/bin/env python3
"""hostclock.py -- the host clock log for a whole seating (P2-4, SPEC.md CLK-38).

WHY
---
Two controllers moved this host's clocks during seating A: WSL's own chronyd
slews the tick toward Windows' clock, and Ubuntu's timesyncd steps
CLOCK_REALTIME toward NTP; CLOCK_MONOTONIC ran 3-5 % slow (notes/boot-time.md
section 7.9).  Seating B stamps CLOCK_MONOTONIC_RAW.  This log reads the host's
clock state for the whole seating, and is what puts a REALTIME stamp (tcpdump,
ping -D) onto RAW.  Read-only by construction: adjtimex(2) is only called with
modes = 0, the run refuses to hold CAP_SYS_TIME, it never reads the journal,
and nothing in it asks whether timesyncd runs.

THE RECORD
----------
PREFIX.clock, flushed per line.  Field 1 is CLOCK_MONOTONIC_RAW with 9 decimals
at the instant the row's measurement began, field 2 the kind, then key=value;
clock values are exact integer nanoseconds written as seconds.
  start  pid, out, boot_id, clocksource, instruments, the pinned SNTP address
  linux  every RAW second: mono, real, boot read after RAW, raw_end after them (the
         pairing bracket), then tick/freq/status/state/offset/constant of adjtimex(modes=0)
  adj    tick, freq or status changed (polled every 0.1 s; the first poll too),
         with the previous poll's prev_raw/prev_mono, so the change is bracketed
  armed  the step detector is armed: a timerfd on CLOCK_REALTIME, absolute, with
         TFD_TIMER_CANCEL_ON_SET -- its read fails ECANCELED when the clock is set
  step   it fired: jump = the change of REALTIME - MONOTONIC from the last read
         before the step (prev_*) to the first read after it (post_*)
  win    one powershell.exe run, stdin /dev/null: QPC, its frequency, UtcNow
         ticks, between raw (spawn) and raw_end (its output closed)
  sntp   one exchange with the pinned server: t1 (field 1) and t4_raw on RAW,
         t1_real/t4_real, the server's t2/t3, delay, used=0|1, reason
  cs     the clocksource changed      stop   why the run ended
PREFIX.meta.json at stop holds what `report` computes from the rows, plus
tool, boot_id, started_wallclock (console-capture's format, for capdate),
counts, refusals by reason, and whether the step detector was positively
controlled -- a step the timerfd and the 1 Hz rows both saw.

CHECKS: MONO/RAW between 1 Hz rows against the kernel's rate -- tick/10000 +
freq, plus the PLL's residual offset, which moves offset >> (2 + constant) into
each REALTIME second whatever status says (量 2026-09-23: +16,000 ppm beyond tick
and freq while timesyncd slewed), allowed to lean only the way a boundary acted on
late would; the timerfd's steps against the rows' REALTIME - MONOTONIC; the
Windows and SNTP fits, each with its standard error.

SNTP uses a reply only if it echoes our nonce as its origin, is mode 4, is no
kiss (stratum 0: RATE doubles the interval, DENY/RSTR end SNTP for the run),
LI != 3, stratum 1-15, 0 <= delay <= --sntp-max-delay-ms, and lies within
--sntp-median-slack-ms of the running median delay of the replies that passed
everything before that test.  Refused replies are recorded, never averaged; no
rate is claimed from fewer than 60 used replies.

USAGE
-----
  run --out PREFIX --seconds CAP (--sntp-server HOST | --no-sntp) [options]
  wait PREFIX --timeout S   exit 0 only when every enabled instrument has
                            written a record and the logger is alive; else 1,
                            naming what is missing (never started, died)
  stop PREFIX               SIGINT to the logger of PREFIX; waits for its meta
  report PREFIX             every fit and cross-check, recomputed from the
                            rows; exit 1 when a cross-check disagrees
  convert PREFIX (--realtime T... | --realtime-file F)
                            REALTIME stamps to RAW through step-free segments;
                            a stamp inside a step's uncertainty is refused
  --self-test [--live-step S]
Exit 2 is a refusal, always with its reason.
"""
import argparse
import bisect
import collections
import contextlib
import ctypes
import errno
import io
import json
import os
import select
import signal
import socket
import statistics
import struct
import subprocess
import sys
import time

TOOL_VERSION = "1.0"
CLOCK = "CLOCK_MONOTONIC_RAW"
ME = os.path.abspath(__file__)
BOOT_ID = "/proc/sys/kernel/random/boot_id"
CS_PATH = "/sys/devices/system/clocksource/clocksource0/current_clocksource"
PS_PATH = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
PS_CMD = ("[Diagnostics.Stopwatch]::GetTimestamp();[Diagnostics.Stopwatch]::Frequency;"
          "[DateTime]::UtcNow.Ticks")
INSTRUMENTS = ("linux", "adj", "step", "win", "sntp")
G = 10**9
ROW_NS, POLL_NS, FLOOR_NS = G, G // 10, G // 1000     # 1 Hz rows, 10 Hz poll, a 1 ms jump
TICK_FLOOR_PPM = 10.0          # 推: kernel rate granularity is ~0.2 ppm; brackets add the rest
# A PLL boundary acts at the first timekeeping update after the second -- with NO_HZ, the next
# wakeup -- and this logger wakes at least every 0.1 s (推).  量 2026-09-23 from 90 pairs, each
# leaning the chunk drop's way: 4.2-4.6 ms with the host busy, 0.3-35 ms with it quiet.
BOUNDARY_S = 0.1
NTP_UNIX, DOTNET_UNIX = 2208988800, 621355968000000000
CAP_SYS_TIME, STA_NANO = 25, 0x2000
SNTP_MIN_USED, WIN_MIN_OK = 60, 10


class Refused(Exception):
    pass


class Timex(ctypes.Structure):
    """struct timex, x86_64 glibc = the kernel's __kernel_timex: 208 bytes, tick at +88."""
    _fields_ = [("modes", ctypes.c_uint), ("pad0", ctypes.c_int),
                ("offset", ctypes.c_long), ("freq", ctypes.c_long),
                ("maxerror", ctypes.c_long), ("esterror", ctypes.c_long),
                ("status", ctypes.c_int), ("pad1", ctypes.c_int),
                ("constant", ctypes.c_long), ("precision", ctypes.c_long),
                ("tolerance", ctypes.c_long), ("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long), ("tick", ctypes.c_long),
                ("ppsfreq", ctypes.c_long), ("jitter", ctypes.c_long),
                ("shift", ctypes.c_int), ("pad2", ctypes.c_int),
                ("stabil", ctypes.c_long), ("jitcnt", ctypes.c_long),
                ("calcnt", ctypes.c_long), ("errcnt", ctypes.c_long),
                ("stbcnt", ctypes.c_long), ("tai", ctypes.c_int),
                ("pad3", ctypes.c_int * 11)]


_LIBC = []


def libc():
    if not _LIBC:
        _LIBC.append(ctypes.CDLL("libc.so.6", use_errno=True))
    return _LIBC[0]


def adjtimex_read(tx):
    """adjtimex(2) on a Timex whose modes is 0: the kernel reports and changes nothing."""
    return libc().adjtimex(ctypes.byref(tx))


def adj_fields(adjtimex):
    tx = Timex()                      # zero-filled, so modes = 0; nothing here assigns it
    st = adjtimex(tx)
    if st < 0:
        return dict(tick="-", freq="-", status="-", state=str(-ctypes.get_errno()))
    return dict(tick=tx.tick, freq=tx.freq, status="0x%04x" % tx.status, state=st,
                offset=tx.offset, constant=tx.constant)


class StepFd(object):
    """A timerfd on CLOCK_REALTIME armed ten years ahead, absolute, with
    TFD_TIMER_CANCEL_ON_SET: its read fails ECANCELED when anything sets the clock."""
    def __init__(self):
        self.fd = libc().timerfd_create(0, os.O_NONBLOCK | os.O_CLOEXEC)   # TFD_* are O_*
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), "timerfd_create")
        self.arm()

    def fileno(self):
        return self.fd

    def arm(self):
        spec = (ctypes.c_long * 4)(0, 0, int(time.time()) + 3650 * 86400, 0)
        if libc().timerfd_settime(self.fd, 1 | 2, spec, None) < 0:   # ABSTIME | CANCEL_ON_SET
            raise OSError(ctypes.get_errno(), "timerfd_settime")

    def cancelled(self):
        try:
            os.read(self.fd, 8)
        except BlockingIOError:
            return False
        except OSError as e:
            if e.errno != errno.ECANCELED:
                raise
            self.arm()
            return True
        return False                  # the expiry ten years out


def ns(cid):
    return time.clock_gettime_ns(cid)


def raw():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def fs(v):
    """Integer nanoseconds as seconds with exactly 9 decimals."""
    q, r = divmod(abs(v), G)
    return "%s%d.%09d" % ("-" if v < 0 else "", q, r)


def pns(s, nine=False):
    """fs() back to integer nanoseconds, exactly; ValueError for anything else."""
    neg = s.startswith("-")
    a, dot, b = s[neg:].partition(".")
    if not a.isdigit() or not (b.isdigit() or not dot) or len(b) > 9 or (nine and len(b) != 9):
        raise ValueError("not a decimal stamp%s: %r" % (" with 9 decimals" * nine, s))
    v = int(a) * G + int(b.ljust(9, "0"))
    return -v if neg else v


def read1(path):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return "?"


def refuse_platform(t=time):
    if getattr(t, "CLOCK_MONOTONIC_RAW", None) is None:
        raise Refused("this Python has no time.CLOCK_MONOTONIC_RAW (Linux only), the clock "
                      "every stamp here is on")


def refuse_caps(status):
    for line in status.splitlines():
        if line.startswith("CapEff:"):
            if int(line.split()[1], 16) >> CAP_SYS_TIME & 1:
                raise Refused("CAP_SYS_TIME is in the effective set: a logger that only reads "
                              "the clock refuses to hold the capability that sets it")
            return
    raise Refused("no CapEff line in /proc/self/status: CAP_SYS_TIME cannot be shown absent")


def build_parser():
    ap = argparse.ArgumentParser(prog="hostclock.py", description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live-step", type=float, metavar="S",
                    help="with --self-test: HC10 waits up to S s for a real step (desk only)")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--seconds", type=float, required=True, help="the run's cap")
    r.add_argument("--no-windows", action="store_true")
    r.add_argument("--windows-every", type=float, default=60.0)
    r.add_argument("--windows-timeout", type=float, default=5.0)
    r.add_argument("--powershell", default=PS_PATH)
    r.add_argument("--sntp-server")
    r.add_argument("--no-sntp", action="store_true")
    r.add_argument("--sntp-port", type=int, default=123)
    r.add_argument("--sntp-every", type=float, default=60.0)
    r.add_argument("--sntp-timeout", type=float, default=2.0)
    r.add_argument("--sntp-max-delay-ms", type=float, default=300.0)
    r.add_argument("--sntp-median-slack-ms", type=float, default=10.0)
    w = sub.add_parser("wait")
    w.add_argument("prefix")
    w.add_argument("--timeout", type=float, required=True)
    s = sub.add_parser("stop")
    s.add_argument("prefix")
    s.add_argument("--timeout", type=float, default=10.0)
    sub.add_parser("report").add_argument("prefix")
    c = sub.add_parser("convert")
    c.add_argument("prefix")
    c.add_argument("--realtime", nargs="+", default=[])
    c.add_argument("--realtime-file")
    return ap


def refuse_args(a):
    """Every refusal that reads nothing but the parsed arguments (FW-124)."""
    if a.self_test or a.live_step is not None:
        if not a.self_test or a.cmd:
            raise Refused("--live-step belongs to --self-test, which takes no subcommand")
        if a.live_step is not None and not a.live_step > 0:
            raise Refused("--live-step must be > 0 s")
        return
    if a.cmd is None:
        raise Refused("name a subcommand: run, wait, stop, report or convert")
    if a.cmd == "run":
        if not a.out or any(ch in a.out for ch in "\t\r\n"):
            raise Refused("--out needs a prefix with no tab or newline")
        if not a.seconds > 0:
            raise Refused("--seconds %r: the run's cap must be > 0" % a.seconds)
        if (a.sntp_server is None) == (not a.no_sntp):
            raise Refused("name the SNTP server (--sntp-server) or pass --no-sntp: exactly one")
        if not a.no_windows and not (a.windows_every >= 0.1 and a.windows_timeout > 0):
            raise Refused("--windows-every must be >= 0.1 s and --windows-timeout > 0")
        if a.sntp_server is not None:
            if not a.sntp_server or any(ch.isspace() for ch in a.sntp_server):
                raise Refused("--sntp-server %r is not a host name" % a.sntp_server)
            if not (a.sntp_every >= 16 or a.sntp_server.startswith("127.")):
                raise Refused("--sntp-every %g s: at least 16 s against a real server (RFC "
                              "5905's minimum poll); shorter is for 127.x only" % a.sntp_every)
            if not (0 < a.sntp_timeout and 0 < a.sntp_max_delay_ms <= 1000
                    and a.sntp_median_slack_ms > 0 and 0 < a.sntp_port < 65536):
                raise Refused("--sntp-timeout, --sntp-max-delay-ms (<= 1000), "
                              "--sntp-median-slack-ms and --sntp-port must be positive")
    elif a.cmd in ("wait", "stop") and not a.timeout > 0:
        raise Refused("--timeout must be > 0 s")
    elif a.cmd == "convert":
        if bool(a.realtime) == bool(a.realtime_file):
            raise Refused("give REALTIME stamps with --realtime or --realtime-file: exactly one")
        for s in a.realtime:
            try:
                pns(s)
            except ValueError:
                raise Refused("--realtime %r: stamps are decimal epoch seconds" % s)


class Rec(object):
    def __init__(self, path):
        self.fh = open(path, "x", encoding="ascii")    # "x": a record is never overwritten

    def row(self, r, kind, **kv):
        self.fh.write("\t".join([fs(r), kind] + ["%s=%s" % x for x in kv.items()]) + "\n")
        self.fh.flush()


def load(prefix, empty_ok=False):
    """PREFIX.clock as [(raw_ns, kind, {key: value})] in file order; a torn last line is
    dropped (the logger may be writing it)."""
    path = prefix + ".clock"
    try:
        with open(path, encoding="ascii", errors="replace") as fh:
            lines = fh.read().split("\n")[:-1]
    except OSError as e:
        raise Refused("cannot read %s: %s" % (path, e.strerror))
    rows = []
    for n, line in enumerate(lines, 1):
        f = line.split("\t")
        try:
            rows.append((pns(f[0], nine=True), f[1], dict(x.split("=", 1) for x in f[2:])))
        except (ValueError, IndexError):
            raise Refused("%s:%d is not a hostclock row: %r" % (path, n, line[:60]))
    if not rows and empty_ok:
        return rows
    if not rows or rows[0][1] != "start" or rows[0][2].get("clock") != CLOCK:
        raise Refused("%s does not begin with a start row declaring clock=%s" % (path, CLOCK))
    return rows


def sntp_fields(data, nonce):
    """The reply's fields as the row keeps them; {} for a runt."""
    if len(data) < 48:
        return {}
    stratum, (t2, t3) = data[1], struct.unpack("!QQ", data[32:48])
    kiss = "".join(ch for ch in data[12:16].decode("ascii", "replace") if ch.isalnum())
    return dict(li=data[0] >> 6, mode=data[0] & 7, stratum=stratum,
                refid=kiss if stratum == 0 else data[12:16].hex(),
                origin="ok" if data[24:32] == nonce else "bad",
                t2=fs(ntp_ns(t2)), t3=fs(ntp_ns(t3)))


def ntp_ns(x):
    return ((x >> 32) - NTP_UNIX) * G + ((x & 0xFFFFFFFF) * G >> 32)


class Judge(object):
    """SNTP's filters, one instance per run, used online and again by the report."""
    def __init__(self, max_delay_ns, slack_ns):
        self.max, self.slack, self.delays = max_delay_ns, slack_ns, []

    def __call__(self, f):
        if "mode" not in f:
            return f.get("reason", "short")
        if f["origin"] != "ok":
            return "origin"
        if int(f["mode"]) != 4:
            return "mode"
        if int(f["stratum"]) == 0:
            return "kod " + f["refid"]
        if int(f["li"]) == 3:
            return "unsynchronized"
        if not 1 <= int(f["stratum"]) <= 15:
            return "stratum"
        if pns(f["t2"]) <= 0 or pns(f["t3"]) <= 0:
            return "timestamp"
        d = pns(f["delay"])
        if not 0 <= d <= self.max:
            return "delay"
        self.delays.append(d)
        if abs(d - statistics.median(self.delays)) > self.slack:
            return "median"
        return ""


def bracket(seq):
    """The last read before a step and the first after it, from the (raw, mono, real) read
    history whose newest entry was read just after the timerfd fired: a poll or a row may
    have read the new offset before the timerfd was serviced."""
    fo, k = seq[-1][2] - seq[-1][1], len(seq) - 2
    while k >= 0 and abs(seq[k][2] - seq[k][1] - fo) <= FLOOR_NS:
        k -= 1
    k = k if k >= 0 else max(len(seq) - 2, 0)    # no read differs: a set with no jump
    return seq[k], seq[min(k + 1, len(seq) - 1)]


def run_logger(a, addr=None, adjtimex=adjtimex_read, stepfd=None, stop=lambda: False):
    R, M, W, B = (time.CLOCK_MONOTONIC_RAW, time.CLOCK_MONOTONIC, time.CLOCK_REALTIME,
                  time.CLOCK_BOOTTIME)
    stepfd = stepfd or StepFd()
    inst = [i for i in INSTRUMENTS if not (i == "win" and a.no_windows)
            and not (i == "sntp" and addr is None)]
    boot_id, cs0 = read1(BOOT_ID), read1(CS_PATH)
    max_ns, slack_ns = int(a.sntp_max_delay_ms * 1e6), int(a.sntp_median_slack_ms * 1e6)
    rec = Rec(a.out + ".clock")
    t0, m0, w0 = ns(R), ns(M), ns(W)
    rec.row(t0, "start", tool="hostclock", version=TOOL_VERSION, clock=CLOCK, pid=os.getpid(),
            out=a.out, boot_id=boot_id, clocksource=cs0, mono=fs(m0), real=fs(w0),
            instruments=",".join(inst), sntp_server=a.sntp_server or "-",
            sntp_addr=addr or "-", sntp_port=a.sntp_port, sntp_max_delay_ns=max_ns,
            sntp_slack_ns=slack_ns)
    rec.row(ns(R), "armed", clock="CLOCK_REALTIME", flags="ABSTIME|CANCEL_ON_SET")
    hist = collections.deque(maxlen=64)       # every (raw, mono, real) read, newest last

    def read3():
        v = (ns(R), ns(M), ns(W))
        hist.append(v)
        return v

    sock, out, win, judge, every = None, None, None, Judge(max_ns, slack_ns), int(a.sntp_every * G)
    if addr:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.connect((addr, a.sntp_port))
    end, cs = t0 + int(a.seconds * G), cs0
    nxt = dict(row=t0, poll=t0, win=t0, sntp=t0, cs=t0 + 60 * G)
    last_adj, prev_poll, reason = None, None, "seconds"

    def finish_win(r1, err):
        p, r0, wr, buf = win[:4]
        if err:
            p.kill()
        try:
            rc = p.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            p.kill()
            rc, err = p.wait(), err or "exit"
        p.stdout.close()
        vals = buf.decode("ascii", "replace").split()
        if not err and (rc != 0 or len(vals) != 3 or not all(v.isdigit() for v in vals)):
            err = "rc" if rc else "output"
        f = {} if err else dict(zip(("qpc", "qpf", "utc_ticks"), vals))
        rec.row(r0, "win", raw_end=fs(r1), real=fs(wr), rc=rc, err=err or "-", **f)

    while True:
        now = ns(R)
        if stop():
            reason = "signal"
            break
        if now >= end:
            break
        fds = [stepfd] + ([sock] if out else []) + ([win[0].stdout] if win else [])
        rd = select.select(fds, [], [], max(0, min(nxt["row"], nxt["poll"]) - now) / G)[0]
        if stepfd in rd and stepfd.cancelled():
            f = read3()
            p, q = bracket(list(hist))
            rec.row(f[0], "step", jump=fs(q[2] - q[1] - (p[2] - p[1])), prev_raw=fs(p[0]),
                    prev_mono=fs(p[1]), prev_real=fs(p[2]), post_raw=fs(q[0]),
                    post_mono=fs(q[1]), post_real=fs(q[2]), by="timerfd")
            rec.row(ns(R), "armed", clock="CLOCK_REALTIME", flags="rearmed")
        if out and sock in rd:
            try:
                data = sock.recv(512)
                t4, t4w = ns(R), ns(W)
            except OSError as e:
                rec.row(out[1], "sntp", used=0, reason="recv_" + errno.errorcode.get(e.errno, "?"))
                out = None
            else:
                f = sntp_fields(data, out[0])
                if f:
                    f.update(t4_raw=fs(t4), t1_real=fs(out[2]), t4_real=fs(t4w),
                             delay=fs(t4 - out[1] - (pns(f["t3"]) - pns(f["t2"]))))
                why, t1 = judge(f), out[1]
                rec.row(t1, "sntp", used=int(not why), reason=why or "-", **f)
                if why != "origin":   # a stale or forged reply: keep waiting for ours
                    out = None
                if why == "kod RATE":
                    every *= 2
                    nxt["sntp"] = t1 + every
                elif why in ("kod DENY", "kod RSTR"):
                    sock.close()
                    sock = out = None
        if win and win[0].stdout in rd:
            chunk = os.read(win[0].stdout.fileno(), 4096)
            if chunk:
                win[3] += chunk
            else:
                finish_win(ns(R), "")
                win = None
        now = ns(R)
        if win and now > win[4]:
            finish_win(now, "timeout")
            win = None
        if now >= nxt["poll"]:
            r, m, w = read3()
            v = adj_fields(adjtimex)
            if (v["tick"], v["freq"], v["status"]) != last_adj:
                pp = dict(prev_raw=fs(prev_poll[0]), prev_mono=fs(prev_poll[1])) if prev_poll else {}
                rec.row(r, "adj", mono=fs(m), real=fs(w), **dict(v, **pp))
                last_adj = (v["tick"], v["freq"], v["status"])
            prev_poll, nxt["poll"] = (r, m), r + POLL_NS
        if now >= nxt["row"]:
            r, m, w = read3()
            b, re_ = ns(B), ns(R)
            rec.row(r, "linux", mono=fs(m), real=fs(w), boot=fs(b), raw_end=fs(re_),
                    **adj_fields(adjtimex))
            nxt["row"] += ROW_NS
            if nxt["row"] <= re_:      # a missed beat is skipped, not bunched
                nxt["row"] = re_ + ROW_NS
        if "win" in inst and win is None and now >= nxt["win"]:
            nxt["win"] = now + int(a.windows_every * G)
            r0, wr = ns(R), ns(W)
            try:   # stdin /dev/null: an inherited stdin is read by powershell.exe (106th segment)
                p = subprocess.Popen([a.powershell, "-NoProfile", "-NonInteractive", "-Command",
                                      PS_CMD], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL)
            except OSError as e:
                rec.row(r0, "win", raw_end=fs(ns(R)), real=fs(wr), rc="-",
                        err="spawn_" + errno.errorcode.get(e.errno, "?"))
            else:
                os.set_blocking(p.stdout.fileno(), False)
                win = [p, r0, wr, b"", r0 + int(a.windows_timeout * G)]
        if sock and out is None and now >= nxt["sntp"]:
            nonce, t1, t1w = os.urandom(8), ns(R), ns(W)
            nxt["sntp"] = t1 + every
            try:
                sock.send(b"\x23" + bytes(39) + nonce)       # LI 0, VN 4, mode 3
                out = [nonce, t1, t1w, t1 + int(a.sntp_timeout * G)]
            except OSError as e:
                rec.row(t1, "sntp", used=0, reason="send_" + errno.errorcode.get(e.errno, "?"))
        if out and ns(R) > out[3]:
            rec.row(out[1], "sntp", used=0, reason="timeout")
            out = None
        if now >= nxt["cs"]:
            nxt["cs"] = now + 60 * G
            if read1(CS_PATH) != cs:
                cs = read1(CS_PATH)
                rec.row(now, "cs", clocksource=cs)
    if win:
        finish_win(ns(R), "stopped")
    if out:
        rec.row(out[1], "sntp", used=0, reason="stopped")
    t9, m9, w9 = ns(R), ns(M), ns(W)
    rec.row(t9, "stop", reason=reason, mono=fs(m9), real=fs(w9))
    rec.fh.close()
    try:
        ana = analyse(load(a.out))
    except Exception as e:                   # noqa: BLE001 -- the meta is written regardless
        ana = dict(problems=["the analysis failed: %s: %s" % (type(e).__name__, e)])
    meta = dict(tool="hostclock", tool_version=TOOL_VERSION, clock=CLOCK, boot_id=boot_id,
                clocksource=cs0, clocksource_end=read1(CS_PATH), start_raw=t0 / G,
                mono_at_start=m0 / G, start_real=round(w0 / G, 6),
                started_wallclock=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(w0 / G)),
                end_raw=t9 / G, mono_at_end=m9 / G, end_real=round(w9 / G, 6),
                pid=os.getpid(), instruments=inst, sntp_addr=addr, stop_reason=reason,
                args={k: v for k, v in vars(a).items() if k not in ("self_test", "live_step")},
                counts=ana.get("counts"),
                refusals=dict(sntp=ana.get("sntp", {}).get("refused"),
                              win=ana.get("win", {}).get("errors")),
                step_detector=ana.get("steps"), tick_check=ana.get("tick"),
                sntp=ana.get("sntp"), windows=ana.get("win"), notes=ana.get("notes"),
                problems=ana.get("problems"))
    body, tmp = json.dumps(meta, indent=1, sort_keys=True) + "\n", a.out + ".meta.json.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.replace(tmp, a.out + ".meta.json")
    return 0


def fit(pts, need):
    """Least-squares slope of y on x (integer ns) with its standard error, or None."""
    if len(pts) < max(need, 3):
        return None
    x0, y0 = pts[0]
    xs, ys = [(x - x0) / G for x, _ in pts], [(y - y0) / G for _, y in pts]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    res = sum((y - my - b * (x - mx)) ** 2 for x, y in zip(xs, ys))
    return len(pts), b, (res / (len(pts) - 2) / sxx) ** 0.5


def pll(a, base, dr, cur=None):
    """(MONOTONIC's advance in ns over dr RAW-ns from row a, the offset left, each boundary
    crossed as (its REALTIME ns, chunk before - chunk after in ns/s), the chunk in effect at
    the end), or None for an offset beyond +-0.5 s.  Per RAW second MONOTONIC gains base plus
    the PLL chunk: second_overflow moves offset >> (2 + constant) into each REALTIME second
    whatever status says; an ADJ_OFFSET write acts from the next boundary (量 2026-09-23:
    offset x 7/8 per second at constant 1).  Boundaries are placed on the second itself;
    BOUNDARY_S says how late the kernel may act on one."""
    unit = 1 if int(a["status"], 16) & STA_NANO else 1000
    s, o, t = 2 + int(a["constant"]), int(a["offset"]) * unit, pns(a["real"])
    if abs(o) > G // 2:
        return None
    mono, steps = 0, []
    cur = round(o / ((1 << s) - 1)) if cur is None else cur   # else: the law's last chunk
    while 0.5 < base + cur / G < 2:
        nb = (t // G + 1) * G
        need = (nb - t) / (base + cur / G)                # RAW-ns to the next boundary
        if need >= dr:
            return mono + (base + cur / G) * dr, int(o / unit), steps, cur
        new = -((-o) >> s) if o < 0 else o >> s
        mono, dr, steps, cur, o, t = mono + nb - t, dr - need, steps + [(nb, cur - new)], new, o - new, nb
    return None


def tick_check(rows):
    """MONO/RAW between consecutive 1 Hz rows a, b -- no change between them or since the
    row z before (linux or adj), the offset obeying the decay law from z on, with a
    boundary between z and a while an offset is live -- against the kernel's rate:
    tick/10000 + freq (ntp_update_frequency adds freq to the second's length) + pll()."""
    seq = sorted((x for x in rows if x[1] in ("linux", "adj")), key=lambda x: x[0])
    n, skipped, worst, strong, bad = 0, collections.Counter(), 0.0, False, []
    for (rz, kz, z), (r0, ka, a), (r1, kb, b) in zip(seq, seq[1:], seq[2:]):
        if (ka, kb) != ("linux", "linux") or "-" in (z["state"][0], a["state"][0], b["state"][0]):
            skipped["an adj row between"] += kb == "linux"
            continue
        key = [(x["tick"], x["freq"], x["status"], x["constant"]) for x in (z, a, b)]
        if key[0] != key[1] or key[1] != key[2] or int(a["status"], 16) & 0x0104 == 0x0104:
            skipped["a change" if key[1] != key[2] else "a change just before"] += 1
            continue
        base = int(a["tick"]) / 10000 + int(a["freq"]) / 65536e6
        pz = pll(z, base, r0 - rz)
        pa = pz and pll(a, base, r1 - r0, pz[3])
        if not pa:
            skipped["an offset beyond 0.5 s"] += 1
            continue
        (_, oa, cz, _), (implied, ob, steps, _) = pz, pa
        if (abs(oa - int(a["offset"])) > 2 * len(cz) + 2 or abs(ob - int(b["offset"])) > 2 * len(steps) + 2
                or not (cz or int(z["offset"]) == int(a["offset"]) == 0)):
            skipped["an offset write, or no boundary since it"] += 1
            continue
        dev = ((pns(b["mono"]) - pns(a["mono"])) / implied - 1) * 1e6
        brk = TICK_FLOOR_PPM + (pns(a["raw_end"]) - r0 + pns(b["raw_end"]) - r1) / (r1 - r0) * 1e6
        # a late boundary keeps the old chunk: the deviation may lean the chunk drop's way only
        lean = sum(d for t, d in cz + steps if t > pns(a["real"]) - BOUNDARY_S * G)
        lean = lean * BOUNDARY_S / (r1 - r0) * 1e6
        lo, hi = -brk + min(0.0, lean), brk + max(0.0, lean)
        n, strong = n + 1, strong or abs(implied / (r1 - r0) - 1) > 1e-4
        worst = dev if abs(dev) > abs(worst) else worst
        if not lo <= dev <= hi:
            bad.append("RAW %s..%s: MONO/RAW %+.1f ppm from tick %s freq %s offset %s (allowed "
                       "%+.1f..%+.1f)" % (fs(r0), fs(r1), dev, a["tick"], a["freq"], a["offset"],
                                          lo, hi))
    return dict(verdict="DISAGREE" if bad else ("AGREE" if n else "NO DATA"), pairs=n,
                strong=strong, worst_ppm=round(worst, 3), skipped=dict(skipped),
                disagreements=bad[:20])


def step_check(lin, steps):
    """The timerfd's steps against the 1 Hz rows: for every pair of consecutive rows, the
    change of REALTIME - MONOTONIC must equal the jumps of the steps whose first post-step
    read falls between them."""
    raws, per, unchecked, bad, agreed = [r for r, _ in lin], collections.defaultdict(list), 0, [], 0
    for kv in steps:
        i = bisect.bisect_left(raws, pns(kv["post_raw"]))
        if 0 < i < len(raws):
            per[i].append(pns(kv["jump"]))
        else:
            unchecked += 1
    for i in range(1, len(lin)):
        (r0, a), (r1, b) = lin[i - 1], lin[i]
        d = pns(b["real"]) - pns(b["mono"]) - (pns(a["real"]) - pns(a["mono"]))
        tol = FLOOR_NS + pns(a["raw_end"]) - r0 + pns(b["raw_end"]) - r1
        if abs(d - sum(per[i])) > tol:
            bad.append("RAW %s..%s: the rows moved %+.6f s, the timerfd's steps %+.6f s"
                       % (fs(r0), fs(r1), d / G, sum(per[i]) / G))
        else:
            agreed += sum(1 for j in per[i] if abs(j) > FLOOR_NS)
    big = sum(1 for kv in steps if abs(pns(kv["jump"])) > FLOOR_NS)
    return dict(verdict="DISAGREE" if bad else ("AGREE" if big else "NO STEPS"),
                timerfd_steps=len(steps), agreed=agreed, unchecked=unchecked,
                positive_control=agreed > 0 and not bad, disagreements=bad[:20])


def sntp_check(rows, start):
    judge = Judge(int(start.get("sntp_max_delay_ns", 0)), int(start.get("sntp_slack_ns", 0)))
    refused, pts, offs, mismatch, sent = collections.Counter(), [], [], 0, 0
    for r, k, kv in rows:
        if k != "sntp":
            continue
        sent, f = sent + 1, dict(kv)
        if "t2" in f:
            t1, t4, t2, t3 = r, pns(f["t4_raw"]), pns(f["t2"]), pns(f["t3"])
            f["delay"] = fs(t4 - t1 - (t3 - t2))
        why = judge(f)
        mismatch += (why or "-") != kv.get("reason") or (not why) != (kv.get("used") == "1")
        if why:
            refused[why] += 1
            continue
        pts.append(((t1 + t4) // 2, (t2 - t1 + t3 - t4) // 2))
        offs.append((t2 - pns(f["t1_real"]) + t3 - pns(f["t4_real"])) // 2)
    fr = fit(pts, SNTP_MIN_USED)
    return dict(sent=sent, used=len(pts), refused=dict(refused), recompute_mismatch=mismatch,
                server_minus_raw_ppm=fr and round(fr[1] * 1e6, 3),
                se_ppm=fr and round(fr[2] * 1e6, 3),
                why_no_rate=None if fr else "%d used, fewer than %d" % (len(pts), SNTP_MIN_USED),
                offset_real_median_ms=round(statistics.median(offs) / 1e6, 3) if offs else None)


def win_check(rows):
    ok = [(r, kv) for r, k, kv in rows if k == "win" and kv.get("err") == "-"]
    errs = collections.Counter(kv.get("err") for r, k, kv in rows
                               if k == "win" and kv.get("err") != "-")
    q, u, offs, br = [], [], [], []
    for r, kv in ok:
        x = (r + pns(kv["raw_end"])) // 2
        uu = (int(kv["utc_ticks"]) - DOTNET_UNIX) * 100
        q.append((x, int(kv["qpc"]) * G // int(kv["qpf"]) - x))
        u.append((x, uu - x))
        offs.append(pns(kv["real"]) + x - r - uu)
        br.append(pns(kv["raw_end"]) - r)
    fq, fu = fit(q, WIN_MIN_OK), fit(u, WIN_MIN_OK)
    return dict(ok=len(ok), errors=dict(errs),
                qpc_minus_raw_ppm=fq and round(fq[1] * 1e6, 3), qpc_se_ppm=fq and round(fq[2] * 1e6, 3),
                utc_minus_raw_ppm=fu and round(fu[1] * 1e6, 3), utc_se_ppm=fu and round(fu[2] * 1e6, 3),
                real_minus_utc_median_s=round(statistics.median(offs) / G, 3) if offs else None,
                bracket_median_s=round(statistics.median(br) / G, 3) if br else None)


def analyse(rows):
    """Every fit and cross-check, from the rows alone: the meta and `report` both call it."""
    lin = sorted(((r, kv) for r, k, kv in rows if k == "linux" and not kv["state"].startswith("-")),
                 key=lambda x: x[0])
    ana = dict(counts=dict(collections.Counter(k for _, k, _ in rows)), tick=tick_check(rows),
               steps=step_check(lin, [kv for r, k, kv in rows if k == "step"]),
               sntp=sntp_check(rows, rows[0][2]), win=win_check(rows))
    notes = [] if any(k == "stop" for _, k, _ in rows) else ["no stop row: running, or died"]
    for (r0, a), (r1, b) in zip(lin, lin[1:]):
        if r1 - r0 > 3 * G // 2:
            notes.append("rows %.3f s apart at RAW %s" % ((r1 - r0) / G, fs(r0)))
        d = pns(b["boot"]) - pns(b["mono"]) - (pns(a["boot"]) - pns(a["mono"]))
        if abs(d) > FLOOR_NS + pns(a["raw_end"]) - r0 + pns(b["raw_end"]) - r1:
            notes.append("BOOTTIME - MONOTONIC moved %+.6f s at RAW %s" % (d / G, fs(r1)))
    notes += ["clocksource %s at RAW %s" % (kv["clocksource"], fs(r)) for r, k, kv in rows if k == "cs"]
    ana["notes"] = notes[:20] + (["and %d more" % (len(notes) - 20)] if len(notes) > 20 else [])
    ana["problems"] = (["tick check: " + x for x in ana["tick"]["disagreements"][:3]]
                       + ["step detectors: " + x for x in ana["steps"]["disagreements"][:3]]
                       + (["%d sntp row(s) the filters do not reproduce"
                           % ana["sntp"]["recompute_mismatch"]] if ana["sntp"]["recompute_mismatch"] else []))
    return ana


def convert(rows, stamps):
    """[(raw_ns or None, reason)] per REALTIME stamp (integer ns).  REALTIME - MONOTONIC is
    one constant per step-free segment; MONOTONIC to RAW is linear between knots (the rows,
    the polls around each rate change, each step's reads).  While the PLL slews, its chunk
    changes at every REALTIME second, which that line misses by up to ~0.7 ms (推)."""
    lin = sorted(((r, kv) for r, k, kv in rows if k == "linux" and not kv["state"].startswith("-")),
                 key=lambda x: x[0])
    steps = sorted((kv for r, k, kv in rows if k == "step"), key=lambda kv: pns(kv["post_raw"]))
    chk = step_check(lin, steps)
    if chk["verdict"] == "DISAGREE":
        return [(None, "the step detectors disagree (%s)" % chk["disagreements"][0])] * len(stamps)
    posts, reads, knots = [pns(kv["post_raw"]) for kv in steps], [], set()
    for r, k, kv in rows:
        if k in ("linux", "adj"):
            reads.append((r, pns(kv["mono"]), pns(kv["real"])))
        if k == "adj" and "prev_raw" in kv:
            knots.add((pns(kv["prev_raw"]), pns(kv["prev_mono"])))
        if k == "step":           # its last read before and first after end and begin segments
            reads += [(pns(kv[x + "_raw"]), pns(kv[x + "_mono"]), pns(kv[x + "_real"]))
                      for x in ("prev", "post")]
    seg = collections.defaultdict(list)
    for r, m, w in reads:
        seg[bisect.bisect_right(posts, r)].append((m, w - m))
        knots.add((r, m))
    segs = [(min(m for m, _ in v), max(m for m, _ in v), statistics.median(c for _, c in v))
            for _, v in sorted(seg.items())]
    knots = sorted(knots)
    km = [m for _, m in knots]
    if any(b <= a for a, b in zip(km, km[1:])):
        return [(None, "MONOTONIC does not increase with RAW in this record")] * len(stamps)
    out = []
    for T in stamps:
        why = ""
        for kv in steps:
            j, a, b = pns(kv["jump"]), pns(kv["prev_real"]), pns(kv["post_real"])
            if min(a, a + j) <= T <= max(b, b - j):
                why = "within the uncertainty of the %+.6f s step at RAW %s" % (j / G, kv["post_raw"])
                break
        cand = [(lo, hi, c) for lo, hi, c in segs if lo <= T - c <= hi]
        if not why and len(cand) != 1:
            why = "outside the log" if not cand else "in two segments"
        if why:
            out.append((None, why))
            continue
        m = T - cand[0][2]
        i = bisect.bisect_left(km, m)
        if i < len(km) and km[i] == m:
            out.append((knots[i][0], ""))
            continue
        if not 0 < i < len(km):
            out.append((None, "outside the log"))
            continue
        (r0, m0), (r1, m1) = knots[i - 1], knots[i]
        if r1 - r0 > 5 * G // 2:
            out.append((None, "a %.1f s gap in the log" % ((r1 - r0) / G)))
            continue
        out.append((r0 + ((m - m0) * (r1 - r0) + (m1 - m0) // 2) // (m1 - m0), ""))
    return out


def alive(start):
    try:
        with open(BOOT_ID) as fh:
            if fh.read().strip() != start.get("boot_id"):
                return False
        with open("/proc/%d/cmdline" % int(start["pid"]), "rb") as fh:
            argv = fh.read().split(b"\0")
    except (OSError, KeyError, ValueError):
        return False
    return any(x.endswith(b"hostclock.py") for x in argv) and start.get("out", "").encode() in argv


def wait_state(prefix):
    """(missing, why): what has not yet written a record, and why it no longer can."""
    if not os.path.exists(prefix + ".clock"):
        return ["record"], ""
    rows = load(prefix, empty_ok=True)
    if not rows:
        return ["record"], ""
    have = set()
    for _, k, kv in rows:
        have.add({"armed": "step"}.get(k, k) if k in ("linux", "adj", "armed") else
                 "win" if k == "win" and kv.get("err") == "-" else
                 "sntp" if k == "sntp" and "t2" in kv else None)
    missing = [i for i in rows[0][2].get("instruments", "").split(",") if i and i not in have]
    if any(k == "stop" for _, k, _ in rows):
        return missing, "the logger stopped"
    if not alive(rows[0][2]):
        return missing, "the logger (pid %s) is not running" % rows[0][2].get("pid")
    return missing, ""


def cmd_run(a):
    refuse_caps(read1("/proc/self/status"))
    if os.path.lexists(a.out + ".clock") or os.path.lexists(a.out + ".meta.json"):
        raise Refused("%s.clock or .meta.json exists: a record is never overwritten" % a.out)
    addr = None
    if a.sntp_server:
        try:
            addr = socket.getaddrinfo(a.sntp_server, a.sntp_port, socket.AF_INET,
                                      socket.SOCK_DGRAM)[0][4][0]
        except (OSError, IndexError) as e:
            raise Refused("cannot resolve --sntp-server %s: %s" % (a.sntp_server, e))
    if not a.no_windows and not os.access(a.powershell, os.X_OK):
        raise Refused("no executable powershell.exe at %s; pass --no-windows" % a.powershell)
    if adjtimex_read(Timex()) < 0:
        raise Refused("adjtimex(modes=0) failed: errno %d" % ctypes.get_errno())
    try:
        stepfd = StepFd()
    except OSError as e:
        raise Refused("cannot arm the step detector: %s" % e)
    stopped = []
    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, lambda n, f: stopped.append(n))
    print("hostclock %s: %s.clock, pid %d, SNTP %s" % (TOOL_VERSION, a.out, os.getpid(),
                                                    addr or "off"), file=sys.stderr)
    try:
        return run_logger(a, addr, stepfd=stepfd, stop=lambda: bool(stopped))
    except OSError as e:
        print("hostclock: stopped: %s" % e, file=sys.stderr)
        return 3


def cmd_wait(a):
    t_end = raw() + int(a.timeout * G)
    while True:
        missing, why = wait_state(a.prefix)
        if not missing and not why:
            print("wait: every instrument has written a record and the logger runs")
            return 0
        if why or raw() >= t_end:
            what = ("never started: no record at %s.clock" % a.prefix if missing == ["record"]
                    else "missing %s" % ", ".join(missing) if missing else "nothing missing")
            print("wait: %s%s (timeout %g s)" % (what, "; " + why if why else "", a.timeout),
                  file=sys.stderr)
            return 1
        time.sleep(0.1)


def cmd_stop(a):
    meta = a.prefix + ".meta.json"
    if os.path.exists(meta):
        print("stop: %s exists: already stopped" % meta)
        return 0
    start = load(a.prefix)[0][2]
    try:
        if not alive(start):
            raise ProcessLookupError
        os.kill(int(start["pid"]), signal.SIGINT)
    except ProcessLookupError:
        print("stop: the logger (pid %s) is not running and wrote no meta: it died"
              % start.get("pid"), file=sys.stderr)
        return 1
    t_end = raw() + int(a.timeout * G)
    while raw() < t_end:
        if os.path.exists(meta):
            print("stop: stopped; %s written" % meta)
            return 0
        time.sleep(0.1)
    print("stop: no meta within %g s" % a.timeout, file=sys.stderr)
    return 1


def cmd_report(a):
    rows = load(a.prefix)
    ana, st = analyse(rows), rows[0][2]
    t, s, n, w = ana["tick"], ana["steps"], ana["sntp"], ana["win"]
    print("hostclock report %s: %d rows, RAW %s..%s, boot_id %s, instruments %s"
          % (a.prefix, len(rows), fs(rows[0][0]), fs(max(r for r, _, _ in rows)),
             st.get("boot_id"), st.get("instruments")))
    print("  counts: " + ", ".join("%s %d" % x for x in sorted(ana["counts"].items())))
    print("  tick check: %s over %d pair(s), worst %+.3f ppm, %s; not checked %s" % (
        t["verdict"], t["pairs"], t["worst_ppm"],
        "strong: the kernel's rate is off nominal here" if t["strong"] else
        "vacuous: MONO runs at RAW's rate here, so agreement cannot tell them apart",
        t["skipped"] or "none"))
    print("  steps: timerfd %d, agreed with the rows %d, %s; positively controlled: %s" % (
        s["timerfd_steps"], s["agreed"], s["verdict"], "yes" if s["positive_control"] else
        "NO -- no step both detectors saw, so zero steps is an uncontrolled claim"))
    for r, k, kv in rows:
        if k == "step":
            print("    step at RAW %s: %+.6f s, bracketed %.4f s" % (
                kv["post_raw"], pns(kv["jump"]) / G,
                (pns(kv["post_raw"]) - pns(kv["prev_raw"])) / G))
    print("  windows: %d read(s), errors %s; QPC-RAW %s ppm (se %s), UtcNow-RAW %s ppm (se %s); "
          "REALTIME-UtcNow median %s s, bracket median %s s" % (
              w["ok"], w["errors"] or "none", w["qpc_minus_raw_ppm"], w["qpc_se_ppm"],
              w["utc_minus_raw_ppm"], w["utc_se_ppm"], w["real_minus_utc_median_s"],
              w["bracket_median_s"]))
    print("  sntp: %d sent, %d used, refused %s; %s; server-REALTIME median %s ms" % (
        n["sent"], n["used"], n["refused"] or "none",
        "rate not claimed: " + n["why_no_rate"] if n["why_no_rate"] else
        "server-RAW %+.3f ppm (se %.3f)" % (n["server_minus_raw_ppm"], n["se_ppm"]),
        n["offset_real_median_ms"]))
    for x in ana["notes"]:
        print("  note: " + x)
    for x in ana["problems"]:
        print("  PROBLEM: " + x)
    return 1 if ana["problems"] else 0


def cmd_convert(a):
    rows, stamps = load(a.prefix), list(a.realtime)
    if a.realtime_file:
        try:
            with open(a.realtime_file) as fh:
                stamps += [x.strip() for x in fh if x.strip()]
        except OSError as e:
            raise Refused("cannot read --realtime-file: %s" % e.strerror)
    try:
        values = [pns(s) for s in stamps]
    except ValueError as e:
        raise Refused("%s (stamps are decimal epoch seconds)" % e)
    res = convert(rows, values)
    for s, (v, why) in zip(stamps, res):
        print("%s\t%s" % (s, fs(v)) if not why else "%s\tREFUSED\t%s" % (s, why))
    return 1 if any(why for _, why in res) else 0


def main(argv=None):
    a = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        refuse_args(a)
        if a.self_test:
            return selftest(a.live_step)
        refuse_platform()
        return dict(run=cmd_run, wait=cmd_wait, stop=cmd_stop, report=cmd_report,
                    convert=cmd_convert)[a.cmd](a)
    except Refused as e:
        print("hostclock: refused: %s" % e, file=sys.stderr)
        return 2


# ------------------------------------------------------------------ self-test
FAKE_PS = """#!%s
import os, sys, time
nul, st = os.stat("/dev/null"), os.fstat(0)
if (st.st_dev, st.st_ino) != (nul.st_dev, nul.st_ino):
    sys.exit(3)                              # an inherited stdin, not /dev/null
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calls"), "a+") as fh:
    fh.seek(0)
    n = len(fh.read())
    fh.write("x")
if n == 2:
    time.sleep(30)                           # the third call hangs
print(time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) * 11 // 1000)   # QPC at 1.1 x RAW
print(10000000)
print(%d + time.time_ns() // 100)
"""


def _plant(prefix, rate=0.957, tick=9570, freq=0, steps=(), fd_steps=None, n=40, rows=None):
    """A planted record: linux rows every RAW second from 1000 s at MONO/RAW = rate,
    REALTIME stepped by steps [(raw_s, jump_s)]; step rows for fd_steps (default: the same).
    rows, if given, are (raw, mono, offset) triples to write instead (status 0x2001)."""
    def mono(t):
        return 5000 * G + round(rate * (t - 1000 * G))

    def real(t):
        return mono(t) + 1790000000 * G + sum(round(j * G) for s, j in steps if t >= round(s * G))
    L = ["%s\tstart\tclock=%s\tpid=0\tout=%s\tboot_id=planted\tinstruments=linux,adj,step"
         % (fs(999 * G), CLOCK, prefix)]
    for t, m, o in rows or [(t, mono(t), 0) for t in range(1000 * G, (1000 + n) * G, G)]:
        L.append("%s\tlinux\tmono=%s\treal=%s\tboot=%s\traw_end=%s\ttick=%d\tfreq=%d\t"
                 "status=0x%04x\tstate=5\toffset=%d\tconstant=1" % (
                     fs(t), fs(m), fs(real(t) if rows is None else m + 1790000000 * G), fs(m),
                     fs(t + 400), tick, freq, 0x2001 if rows else 0x2000, o))
    for s, j in (steps if fd_steps is None else fd_steps):
        p, q = round(s * G) - 4 * 10**7, round(s * G) + 3 * 10**7
        L.append("%s\tstep\tjump=%s\tprev_raw=%s\tprev_mono=%s\tprev_real=%s\tpost_raw=%s\t"
                 "post_mono=%s\tpost_real=%s\tby=timerfd" % (
                     fs(q + 10**5), fs(round(j * G)), fs(p), fs(mono(p)), fs(real(p)), fs(q),
                     fs(mono(q)), fs(real(q))))
    body = "\n".join(L) + "\n"
    with open(prefix + ".clock", "w") as fh:
        fh.write(body)
    return mono, real


def selftest(live_step=None):
    import importlib.machinery
    import importlib.util
    import shutil
    import tempfile
    import threading
    try:
        refuse_platform()
        with open("/proc/self/status") as fh:
            refuse_caps(fh.read())
    except (Refused, OSError) as e:
        print("hostclock --self-test: refused: %s" % e, file=sys.stderr)
        return 2
    tmp, res = tempfile.mkdtemp(prefix="hostclock-"), []

    def case(cid, what, fn):
        try:
            note = fn()
        except Exception as e:                                   # noqa: BLE001
            res.append("FAIL")
            print("  FAIL  %-5s %s -- %s: %s" % (cid, what, type(e).__name__, e))
        else:
            res.append("skip" if isinstance(note, tuple) else "ok")
            if isinstance(note, tuple):
                print("  skip  %s %s  %s" % (cid, what, note[1]))
            else:
                print("  ok    %-5s %s%s" % (cid, what, " -- " + note if note else ""))
        sys.stdout.flush()

    def P(name):
        return os.path.join(tmp, name)

    def me(argv, shim=False, stdin=subprocess.DEVNULL):
        pre = [os.path.join(os.path.dirname(ME), "clockshim.py"), "--rate", "0.5", "--"] * shim
        return subprocess.run([sys.executable] + pre + [ME] + argv, stdin=stdin,
                              capture_output=True, text=True, timeout=120)

    def run_args(prefix, *extra):
        return build_parser().parse_args(["run", "--out", prefix] + list(extra))

    def kinds(rows, kind):
        return [(r, kv) for r, k, kv in rows if k == kind]

    def hc1():
        assert ctypes.sizeof(Timex) == 208 and Timex.tick.offset == 88, ctypes.sizeof(Timex)
        tx = Timex()
        st = adjtimex_read(tx)
        assert st >= 0 and 9000 <= tx.tick <= 11000, (st, tx.tick)
        return "tick %d, freq %+.3f ppm, status 0x%04x" % (tx.tick, tx.freq / 65536, tx.status)
    case("HC1", "struct timex is 208 bytes, tick at +88; a live read's tick is in [9000, 11000]", hc1)

    def hc2():
        seen = []

        def spy(tx):
            seen.append(tx.modes)
            return adjtimex_read(tx) if tx.modes == 0 else -1   # a non-zero mode never runs
        run_logger(run_args(P("hc2"), "--seconds", "1.2", "--no-windows", "--no-sntp"), adjtimex=spy)
        assert len(seen) >= 10 and set(seen) == {0}, seen
        return "%d calls" % len(seen)
    case("HC2", "every adjtimex call the logger makes has modes = 0", hc2)

    def hc3():
        pre, b0 = P("hc3"), raw()
        p = subprocess.Popen([sys.executable, ME, "run", "--out", pre, "--seconds", "60",
                              "--no-windows", "--no-sntp"], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            w = me(["wait", pre, "--timeout", "10"])
            assert w.returncode == 0, ("wait", w.returncode, w.stderr)
            time.sleep(3.3)
            s = me(["stop", pre, "--timeout", "10"])
            assert s.returncode == 0 and p.wait(10) == 0, ("stop", s.returncode, s.stderr)
        finally:
            p.kill()
        b1, rows = raw(), load(pre)
        with open(pre + ".meta.json") as fh:
            meta = json.load(fh)
        assert all(b0 <= r <= b1 for r, _, _ in rows), "a stamp outside the harness's RAW bracket"
        assert len(kinds(rows, "linux")) >= 3 and kinds(rows, "adj") and kinds(rows, "armed")
        assert (meta["tool"], meta["clock"], meta["boot_id"]) == ("hostclock", CLOCK,
                                                                  read1(BOOT_ID)), meta
        assert meta["counts"] == dict(collections.Counter(k for _, k, _ in rows)), meta["counts"]
        ldr = importlib.machinery.SourceFileLoader("hc_capdate", os.path.join(
            os.path.dirname(ME), "capdate.py"))
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("hc_capdate", ldr))
        ldr.exec_module(mod)
        when, why = mod.capture_when(pre + ".meta.json")
        assert when is not None and when.date().isoformat() == time.strftime(
            "%Y-%m-%d", time.localtime(meta["start_real"])), (when, why)
        t = tick_check(rows)
        assert t["verdict"] != "DISAGREE", t
        return "tick check %s over %d pair(s), %s" % (t["verdict"], t["pairs"], "strong: the "
               "kernel's rate is off nominal here" if t["strong"] else "vacuous: MONO = RAW here"
               if t["pairs"] else "no pair without a rate change in 3 s")
    case("HC3", "run, wait -> 0, stop: RAW stamps, meta for capdate, rows agree with the tick", hc3)

    def mono_ratio(rows):
        lin = kinds(rows, "linux")
        assert len(lin) >= 3, lin
        return (pns(lin[-1][1]["mono"]) - pns(lin[0][1]["mono"])) / (lin[-1][0] - lin[0][0])

    def hc4():
        b0 = raw()
        r = me(["run", "--out", P("hc4"), "--seconds", "3", "--no-windows", "--no-sntp"], shim=True)
        b1 = raw()
        assert r.returncode == 0, (r.returncode, r.stderr[-300:])
        rows = load(P("hc4"))
        bad = [x for x, _, _ in rows if not b0 <= x <= b1]
        assert not bad, ("a stamp outside the harness's RAW bracket", fs(bad[0]))
        ratio = mono_ratio(rows)
        assert 0.42 <= ratio <= 0.55, ratio
        return "rows' MONO/RAW %.4f under a 0.5 shim" % ratio
    case("HC4", "(shim) field 1 is RAW, and the mono column is MONOTONIC", hc4)

    def hc5():
        for tick, freq, want in ((10000, 40, "DISAGREE"), (9570, 40, "AGREE"), (9570, 0, "DISAGREE")):
            _plant(P("hc5-%d-%d" % (tick, freq)), rate=0.957 + 40e-6, tick=tick, freq=freq * 65536)
            got = tick_check(load(P("hc5-%d-%d" % (tick, freq))))
            assert got["verdict"] == want, ("rows at 0.957 + 40 ppm", tick, freq, got)
        # the kernel's PLL law, simulated in 1 ms RAW steps: +-120 ms of offset at constant 1
        # moves x 1/8 into MONOTONIC per REALTIME second, each boundary acted on 50 ms late (a
        # quiet host's next update), so the rows lean the drop's way; zeroing the offset column
        # must disagree, and so must a boundary acted on 50 ms EARLY, which no kernel does
        for sign, early, want in ((1, 0, "AGREE"), (-1, 0, "AGREE"), (1, 1, "DISAGREE")):
            sim, o, chunk, m, due, c = [], sign * 120 * 10**6, 0, 5000 * G, -1, 1790000000 * G
            for k in range(60001):
                if k % 1000 == 0:
                    sim.append((1000 * G + k * 10**6, m, o))
                m2 = m + round((0.957 + chunk / G) * 10**6)
                if (m2 + c + early * G // 20) // G > (m + c + early * G // 20) // G:
                    due = k + 50 * (1 - early)
                if k == due:
                    chunk = -((-o) >> 3) if o < 0 else o >> 3
                    o -= chunk
                m = m2
            for name, rows, verdict in (("pll%d%d" % (sign, early), sim, want),
                                        ("nopll%d%d" % (sign, early),
                                         [(t, m, 0) for t, m, _ in sim], "DISAGREE")):
                _plant(P(name), tick=9570, rows=rows)
                got = tick_check(load(P(name)))
                assert got["verdict"] == verdict and got["pairs"] >= 40, (name, got)

        def fake(tx):                          # reports tick 10000; the kernel is never asked
            tx.tick, tx.status = 10000, 0x2000
            return 0
        ldr = importlib.machinery.SourceFileLoader("hc_shim", os.path.join(os.path.dirname(ME),
                                                                           "clockshim.py"))
        shim = importlib.util.module_from_spec(importlib.util.spec_from_loader("hc_shim", ldr))
        ldr.exec_module(shim)
        names = ("monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns",
                 "clock_gettime", "clock_gettime_ns")
        saved = [getattr(time, x) for x in names]
        try:
            shim.install(0.5, 1000.0)          # MONOTONIC at half rate, in this process only
            run_logger(run_args(P("hc5"), "--seconds", "3.2", "--no-windows", "--no-sntp"),
                       adjtimex=fake)
        finally:
            for x, f in zip(names, saved):
                setattr(time, x, f)
        rows = load(P("hc5"))
        got = tick_check(rows)
        assert 0.42 <= mono_ratio(rows) <= 0.55 and got["verdict"] == "DISAGREE", (
            "rows at 0.5 x MONOTONIC against tick 10000", mono_ratio(rows), got)
        return "worst %+.0f ppm over %d pair(s)" % (got["worst_ppm"], got["pairs"])
    case("HC5", "the control that must fail: tick 10000 against rows at a planted rate", hc5)

    def hc6():
        theta, script = 5 * G, ["ok", "ok", "slow", "kod", "origin", "median", "ok", "deny"]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        s.settimeout(0.2)
        halt = threading.Event()

        def ntp(t):
            return struct.pack("!II", t // G + NTP_UNIX, (t % G << 32) // G)

        def serve():
            while not halt.is_set():
                try:
                    data, peer = s.recvfrom(512)
                except socket.timeout:
                    continue
                kind = script.pop(0) if script else "ok"
                # planted margins far above scheduling noise (量 +27 ms at load average 11)
                d = {"slow": 0.4, "median": 0.25}.get(kind, 0.02)    # the planted path delay
                time.sleep(d / 2)
                t2 = time.time_ns() + theta
                time.sleep(0.1)                                       # the server's hold
                t3 = time.time_ns() + theta

                def pkt(org, stratum=2, li=0, refid=b"GPS\0"):
                    return (bytes([li << 6 | 4 << 3 | 4, stratum, 6, 0xEC]) + bytes(8) + refid
                            + bytes(8) + org + ntp(t2) + ntp(t3))
                time.sleep(d / 2)
                if kind == "origin":
                    s.sendto(pkt(bytes(8)), peer)
                kiss = {"kod": b"RATE", "deny": b"DENY"}.get(kind)
                s.sendto(pkt(data[40:48], 0, 3, kiss) if kiss else pkt(data[40:48]), peer)
        th = threading.Thread(target=serve, daemon=True)
        th.start()
        try:
            r = me(["run", "--out", P("hc6"), "--seconds", "5.5", "--no-windows", "--sntp-server",
                    "127.0.0.1", "--sntp-port", str(s.getsockname()[1]), "--sntp-every", "0.3",
                    "--sntp-timeout", "1.0", "--sntp-median-slack-ms", "60"])
        finally:
            halt.set()
            th.join(2)
            s.close()
        assert r.returncode == 0, r.stderr[-300:]
        rows = kinds(load(P("hc6")), "sntp")
        why = [kv["reason"] for _, kv in rows]
        assert why == ["-", "-", "delay", "kod RATE", "origin", "-", "median", "-", "kod DENY"], (
            "in order, and nothing sent after DENY", why)
        for _, kv in rows:
            if kv["used"] == "1":
                off = (pns(kv["t2"]) - pns(kv["t1_real"]) + pns(kv["t3"]) - pns(kv["t4_real"])) // 2
                assert abs(off - theta) < 4 * 10**7 and abs(pns(kv["delay"]) - 2 * 10**7) < 8 * 10**7, (
                    "planted offset 5 s, delay 20 ms (a swapped t2/t3 reads 220 ms)", off, kv["delay"])
        assert rows[1][0] - rows[0][0] < 6 * G // 10 <= rows[4][0] - rows[3][0], (
            "a RATE kiss doubles the 0.3 s interval", [fs(r) for r, _ in rows[:5]])
        assert analyse(load(P("hc6")))["sntp"]["why_no_rate"], "a rate from fewer than 60 replies"
        pts = [(i * G, i * 1000) for i in range(60)]     # the brief's 60, not the constant
        assert fit(pts[:-1], SNTP_MIN_USED) is None and abs(fit(pts, SNTP_MIN_USED)[1] - 1e-6) < 1e-12, (
            "no rate from 59 used replies, a rate from 60")
        return "%d exchanges" % len(rows)
    case("HC6", "fake SNTP on 127.0.0.1: offset/delay recovered; slow, kisses, origin, median refused",
         hc6)

    def hc7():
        d = P("ps")
        os.mkdir(d)
        fake = os.path.join(d, "powershell.exe")
        with open(fake, "w") as fh:
            fh.write(FAKE_PS % (sys.executable, DOTNET_UNIX))
        os.chmod(fake, 0o755)
        r = me(["run", "--out", P("hc7"), "--seconds", "5", "--no-sntp", "--powershell", fake,
                "--windows-every", "0.2", "--windows-timeout", "0.6"], stdin=subprocess.PIPE)
        assert r.returncode == 0, r.stderr[-300:]
        rows = load(P("hc7"))
        errs = [kv["err"] for _, kv in kinds(rows, "win") if kv["err"] != "-"]
        assert errs in (["timeout"], ["timeout", "stopped"]), (
            "one hang, killed at its deadline; at most a read the cap cut; no other error", errs)
        lin = [r for r, _ in kinds(rows, "linux")]
        assert max(b - a for a, b in zip(lin, lin[1:])) < 3 * G // 2, "the 1 Hz rows stalled"
        w = win_check(rows)
        assert w["ok"] >= WIN_MIN_OK and abs(w["qpc_minus_raw_ppm"] - 1e5) < 3e4, w
        return "%d reads, QPC-RAW %+.0f ppm (planted +100000)" % (w["ok"], w["qpc_minus_raw_ppm"])
    case("HC7", "fake powershell: stdin /dev/null, reads fitted, a hang killed while 1 Hz holds", hc7)

    def hc8():
        mono, real = _plant(P("hc8"), steps=((1010.5, 1.4), (1025.25, -0.3)))
        rows = load(P("hc8"))
        for s in (1003.3, 1010.3, 1015.0, 1020.7, 1024.8, 1026.0, 1030.123456789, 1038.0):
            (v, why), = convert(rows, [real(round(s * G))])
            assert not why and abs(v - round(s * G)) <= 1000, (s, why, v)
        for T, want in ((real(round(1010.48 * G)), "uncertainty"),
                        (real(round(1010.45 * G)) + 7 * 10**8, "uncertainty"),
                        (real(round(1025.1 * G)), "uncertainty"),
                        (real(round(1025.35 * G)), "uncertainty"),
                        (real(999 * G), "outside"), (real(1045 * G), "outside")):
            (v, why), = convert(rows, [T])
            assert v is None and want in why, (fs(T), why)
    case("HC8", "convert: within 1 us away from planted steps, refused inside their uncertainty", hc8)

    def hc9():
        def verdict(name, **kw):
            _plant(P(name), **kw)
            rows = load(P(name))
            return step_check(sorted(kinds(rows, "linux"), key=lambda x: x[0]),
                              [kv for _, kv in kinds(rows, "step")])
        v = verdict("hc9a", steps=((1010.5, 1.4),))
        assert v["verdict"] == "AGREE" and v["positive_control"], v
        v = verdict("hc9b", steps=((1010.5, 1.4),), fd_steps=())
        assert v["verdict"] == "DISAGREE", ("a jump in the rows with no timerfd step", v)
        v = verdict("hc9c", fd_steps=((1010.5, 1.4),))
        assert v["verdict"] == "DISAGREE", ("a timerfd step the rows never saw", v)
        v = verdict("hc9d")
        assert v["verdict"] == "NO STEPS" and not v["positive_control"], v
    case("HC9", "the two step detectors disagree on a planted fault, agree on a planted step", hc9)

    def hc10():
        if not live_step:
            return ("skip", "NOT TESTED: desk only -- nothing unprivileged can set the clock; "
                    "run --self-test --live-step 120 while timesyncd steps the host")
        r = me(["run", "--out", P("hc10"), "--seconds", str(live_step), "--no-windows", "--no-sntp"])
        assert r.returncode == 0, r.stderr[-300:]
        s = analyse(load(P("hc10")))["steps"]
        if not s["timerfd_steps"]:
            return ("skip", "NOT TESTED: no step in %g s -- the host is not stepping" % live_step)
        assert s["verdict"] == "AGREE" and s["positive_control"], s
        return "%d step(s), both detectors agree" % s["timerfd_steps"]
    case("HC10", "a live step", hc10)

    def hc11():
        pre = P("hc11")
        for argv in (["run", "--out", pre, "--seconds", "5", "--no-sntp"],
                     ["run", "--out", pre, "--seconds", "5", "--sntp-server", "127.0.0.1",
                      "--sntp-every", "0.5"], ["wait", pre, "--timeout", "3"], ["stop", pre],
                     ["report", pre], ["convert", pre, "--realtime", "1790000000.5"]):
            refuse_args(build_parser().parse_args(argv))
        for argv, want in ((["run", "--out", pre, "--seconds", "0", "--no-sntp"], "cap"),
                           (["run", "--out", pre, "--seconds", "5"], "exactly one"),
                           (["run", "--out", pre, "--seconds", "5", "--sntp-server",
                             "ntp.ubuntu.com", "--sntp-every", "5"], "16 s"),
                           (["wait", pre, "--timeout", "0"], "--timeout"),
                           (["convert", pre], "exactly one"),
                           (["convert", pre, "--realtime", "12:00:01"], "decimal")):
            try:
                refuse_args(build_parser().parse_args(argv))
            except Refused as e:
                assert want in str(e), (argv, str(e))
            else:
                raise AssertionError("permitted %r" % argv)
        refuse_caps("Name:\tpython3\nCapEff:\t0000000000000000\n")
        try:
            refuse_caps("CapEff:\t0000000002000000\n")
            raise AssertionError("CAP_SYS_TIME permitted")
        except Refused as e:
            assert "CAP_SYS_TIME" in str(e), e
        saved, err = time.CLOCK_MONOTONIC_RAW, io.StringIO()
        del time.CLOCK_MONOTONIC_RAW
        try:
            with contextlib.redirect_stderr(err):
                rc = main(["run", "--out", pre, "--seconds", "1", "--no-sntp", "--no-windows"])
        finally:
            time.CLOCK_MONOTONIC_RAW = saved
        assert rc == 2 and "CLOCK_MONOTONIC_RAW" in err.getvalue() and not os.path.exists(
            pre + ".clock"), (rc, err.getvalue())
        with open(pre + ".clock", "w") as fh:
            fh.write("keep\n")
        r = me(["run", "--out", pre, "--seconds", "1", "--no-sntp", "--no-windows"])
        with open(pre + ".clock") as fh:
            assert r.returncode == 2 and "never overwritten" in r.stderr and fh.read() == "keep\n", (
                r.returncode, r.stderr)
    case("HC11", "refusals, each with its permitting half: args, CAP_SYS_TIME, no RAW, a record", hc11)

    def hc12():
        pre = P("hc12")
        r = me(["wait", pre, "--timeout", "0.3"])
        assert r.returncode == 1 and "never started" in r.stderr, (r.returncode, r.stderr)
        with open(pre + ".clock", "w") as fh:
            fh.write("1.000000000\tstart\tclock=%s\tpid=0\tout=%s\tboot_id=%s\tinstruments="
                     "linux,adj,step,sntp\n2.000000000\tlinux\tstate=0\n2.100000000\tadj\t"
                     "state=0\n2.200000000\tarmed\n" % (CLOCK, pre, read1(BOOT_ID)))
        r = me(["wait", pre, "--timeout", "5"])
        assert r.returncode == 1 and "missing sntp;" in r.stderr and "not running" in r.stderr, (
            r.returncode, r.stderr)
    case("HC12", "wait names a missing instrument, a logger not running, one never started", hc12)

    def hc13():
        class FakeFd(object):
            def __init__(self):
                self.r, self.w = os.pipe()
                os.set_blocking(self.r, False)
                self.fired = 0

            def fileno(self):
                return self.r

            def cancelled(self):
                try:
                    os.read(self.r, 1)
                except BlockingIOError:
                    return False
                self.fired += 1
                return True
        fake = FakeFd()
        os.write(fake.w, b"x")
        run_logger(run_args(P("hc13"), "--seconds", "1.2", "--no-windows", "--no-sntp"),
                   stepfd=fake)
        rows = load(P("hc13"))
        st = kinds(rows, "step")
        assert fake.fired == 1 and len(st) == 1 and len(kinds(rows, "armed")) == 2, rows
        assert abs(pns(st[0][1]["jump"])) < FLOOR_NS, st
        # a poll read the new offset (+1.4 s) before the timerfd was serviced
        hist = [(1, 10, 110), (2, 20, 120), (3, 30, 1400000130), (4, 40, 1400000140)]
        assert bracket(hist) == (hist[1], hist[2]), bracket(hist)
        assert bracket(hist[:1]) == (hist[0], hist[0]), "a history of one read"
    case("HC13", "a planted cancel is written as a step row and re-armed; the bracket search", hc13)

    shutil.rmtree(tmp, ignore_errors=True)
    print("RESULT: %d ok, %d FAIL, %d skip, of %d" % (res.count("ok"), res.count("FAIL"),
                                                   res.count("skip"), len(res)))
    return 1 if "FAIL" in res else 0


if __name__ == "__main__":
    sys.exit(main())
