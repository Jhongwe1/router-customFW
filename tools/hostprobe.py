#!/usr/bin/env python3
"""hostprobe -- what the host sees on the wire, stamped on the console's clock.

`P2-1`, for `P2`'s `D8` and `D4`.  The vendor firmware has no shell (`P2`
settled item 1), so its boot-time column is what it prints unprompted plus
what the HOST observes: the first ICMP echo reply (`D8`: *network up*; the
loader answers ARP and not ICMP, so the first reply is the kernel's) and the
first host-side success on a daemon's port (`D4`: *readiness*, e.g. TCP 80 for
the vendor's `boa`).  This tool records those host events with timestamps and
nothing else -- never a packet's contents, never a frame.

ONE CLOCK
---------
Since 1.3, every `*_raw` value, every event line's first field and every
deadline the probe computes (`--seconds`, the TCP and neighbour schedules,
ping's stop grace) is an absolute `clock_gettime(CLOCK_MONOTONIC_RAW)`
reading.  1.0-1.2 read `time.monotonic()`, `CLOCK_MONOTONIC`, which on this
host's WSL runs percent-slow under the tick WSL's own `chronyd` writes, while
RAW is not slewed (`SPEC.md` `CLK-38`).  `console-capture` 1.5 reads its
`t0_raw` on the same clock, and that is what places these events on a
capture's timeline (`P2` settled item 4).  The kernel's own timers stay on
`CLOCK_MONOTONIC`: `select()` waits at most 0.25 s and every pass re-reads
RAW, so a deadline is overshot by at most 0.25 s x (1/r - 1) per wait, r the
MONOTONIC/RAW rate (about 10 ms at `CLK-38`'s 0.959).  Every `*_real` value is
`time.time()` read right after a RAW reading; it exists for cross-checks only
and is never used as an interval.  `mono_at_start` and `mono_at_end` are one
`CLOCK_MONOTONIC` reading beside each end's RAW reading, so a record carries
its own MONOTONIC/RAW ratio; `boot_id` names the boot its RAW stamps count
from (RAW restarts with every boot), and `clocksource`/`clocksource_end` the
kernel's clocksource at each end.

A record declares its clock twice: the events file's first line (`t_raw is
absolute CLOCK_MONOTONIC_RAW seconds`) and the meta's `clock`.  A reader takes
the clock from the header, as the whole token after `is absolute` --
`CLOCK_MONOTONIC` is a prefix of `CLOCK_MONOTONIC_RAW`, so a substring test
cannot tell them apart -- and a record whose two declarations disagree is
MALFORMED.  Records 1.0-1.2 wrote (`*_mono` keys, a tcp line's `start_mono=`)
still read, on `CLOCK_MONOTONIC`.

THE SECOND CLOCK, AND WHY ICMP GOES THROUGH A SUBPROCESS
--------------------------------------------------------
An unprivileged ICMP socket is refused on this host (`FW-114`:
`net.ipv4.ping_group_range` reads `1 0`, `socket(AF_INET, SOCK_DGRAM,
IPPROTO_ICMP)` raises `EACCES`), and this tool changes no system setting.  So
it drives the system `ping` -- one long-lived `ping -D -O -n -i S TARGET` --
and stamps each line when it is READ.  ping's own `-D` stamp is realtime taken
when ping prints the line; the probe's `t_real` is realtime taken when the
probe read it.  Their difference, the per-line LAG, is the cross-check: it is
what a stamp taken through a pipe costs, and block-buffered output would show
as whole intervals of lag arriving in bursts.

Host facts this file is written against, all 量 2026-09-23 on this host's WSL
(`/usr/bin/python3` 3.12.3, kernel 6.6.87.2-microsoft-standard-WSL2), every
reading taken against 127.0.0.1 only:

* `ping -V` reads `ping from iputils 20240117`; `/usr/bin/ping` carries
  `cap_net_raw=ep`.
* **The unprivileged minimum interval is 2 ms, not 0.2 s.**  `-i 0.0019` and
  below exit 2 with `ping: cannot flood, minimal interval for user must be >=
  2 ms, use -i 0.002 (or higher)`; `-i 0.002` runs.  The 0.2 s figure is what
  older iputils documented, and it is kept here as the floor for any iputils
  release this project has not measured (`MEASURED_MIN_INTERVAL_S`).
* **ping truncates `-i` to whole milliseconds.**  `-i 0.0029` ran at a 2.034 ms
  median gap, `0.0049` at 4.060, `0.0059` at 5.065 (150 packets each).  A
  fractional-millisecond request is refused rather than silently run slower.
* **The achieved interval is not the requested one at 10 ms and above.**
  Median gap between consecutive `-D` stamps: 2 ms -> 2.012, 9 -> 9.039,
  10 -> 16.009, 20 -> 23.998, 50 -> 56.005, 100 -> 104.035, 200 -> 203.952,
  500 -> 511.981.  This kernel runs `CONFIG_HZ=250`; that the step at 10 ms is
  ping switching from spinning to a jiffy-rounded sleep is 推 (iputils'
  scheduler, not read here).  *Network up* is resolved to the ACHIEVED
  interval, so the meta records it, measured on the probe's own clock from
  its own reads.
* **ping flushes per line into a pipe.**  766 reply lines over four runs
  (-i 0.002 to 0.2): every one read 0.026-0.435 ms after its own `-D` stamp,
  so no reply waited for the next one -- the shortest interval is 2 ms.
  Positive control, the same ping behind a relay that holds output for 1 s:
  15 replies arrived in 3 reads and 12 of them lagged more than 10 ms (max
  1020 ms).  So the lag statistic can see buffering on this host's real output.
  Through this tool, 3 s each: at -i 0.2, 15 of 15 lines under 0.101 ms, one
  per read; at -i 0.002, 13 of 1471 over the 1 ms threshold (max 10.664 ms)
  and 2 reads carrying two lines -- this host's scheduling, flagged as H1
  intends.  The lag is per line, not a constant.
* 推: that ping puts a `-D` stamp in front of a `no answer yet` line too.  The
  format string exists in the binary (`no answer yet for icmp_seq=%lu`), but
  loopback always answers, so no such line was produced here and producing one
  would take a system setting.  The parser takes the line with or without a
  stamp; `ping.no_timestamp_lines` in the first bench run's meta settles it.
* `ip -4 route get 127.0.0.1` prints `local 127.0.0.1 dev lo src 127.0.0.1`;
  `ip -4 neigh show 127.0.0.1` prints nothing and exits 0 (loopback is NOARP);
  with a `dev` filter iproute2 omits the `dev` field from the entry line.
* Python 3.12's `socket` module has no `SO_TIMESTAMPNS`; on x86_64 the value
  is `SO_TIMESTAMPNS_OLD`, 35, and `SCM_TIMESTAMPNS` equals it (讀
  `/usr/include/asm-generic/socket.h`).

WHAT IT RECORDS
---------------
    run --out PREFIX --target IPV4 --seconds N  [probes]  [--until SPEC]...

`--icmp`       the ping stream above: `icmp-reply` per echo reply, `icmp-silent`
               per `no answer yet` line (`-O`).
`--tcp PORT`   a non-blocking `connect()` every `--tcp-interval`, each bounded by
               `--tcp-timeout`, closed as soon as it resolves: ok / refused
               (RST) / timeout / unreachable / error, with the errno.
`--neigh`      `ip -4 neigh show TARGET` polled every `--neigh-interval`; an
               event only when (state, lladdr) changes, and always for the
               first poll.  No entry is state `NONE`.
`--udp-listen PORT`   a bound socket; each datagram's arrival, peer and length,
               with the kernel's receive stamp (`SO_TIMESTAMPNS`, realtime).
               This exists for a later bench card that measures the
               console-versus-network channel offset on rlxfw, which can print
               and send in one command: its busybox has `traceroute` (UDP to a
               chosen `-p` port) and no `nc`/`wget` (`config/image-commands.tsv`).

`PREFIX.events`, UTF-8, LF, one line per event, flushed per line so a killed
run keeps everything up to the kill.  `#` lines are comments; the first is the
header that declares the clock.  Every other line is `<t> <kind>
[key=value ...]`, t with six decimals on that clock:

    start       t_real=
    stop        t_real= reason=
    icmp-reply  seq= ttl= rtt_ms= ping_real=      t = when the line was read
    icmp-silent seq=
    tcp         port= result= errno= start_raw= dur_ms=   t = when it resolved
    neigh       state= lladdr=         lladdr: an allowlisted MAC, `unlisted-N` or `-`
    udp         port= peer= len= kernel_real= lag_ms=

A udp line's `lag_ms` is the probe's realtime read minus `kernel_real`, both
realtime, so the kernel's receive on the probe's clock is `t - lag_ms/1000`.
1.0-1.2 records, on `CLOCK_MONOTONIC`: a tcp line carries `start_mono=` and a
udp line has no `lag_ms=`.

A value that does not exist is `-`, never a number.  Lines ping prints that are
not one of the two ICMP kinds (its header, `From ... Destination Host
Unreachable`, `(DUP!)`, `(truncated)`, its statistics, stderr) become comment
lines and are counted in the meta; a line whose lag crosses the threshold gets
a `# ... icmp-lag ...` comment directly after it.  `PREFIX.meta.json` is
written at the end, through `.tmp` and `os.replace`.

ADDRESSES: WHAT MAY LEAVE THIS PROCESS
--------------------------------------
🔴 In `P2-3` the target is 10.1.1.1, the vendor firmware's LAN address
(`upstream/notes/compcs-decode.md`: `IP_ADDR` from this unit's live config),
and the MAC that answers ARP for it is this unit's own, from H601.  (The
vendor NIC driver on rlxfw's kernel is NOT that: 量 `bench/2026-09-21e/V3-ETH4`
reads `HWaddr 00:12:34:56:78:94`, the SDK's placeholder; 1.1's docstring said
otherwise.)  It is labelled `unlisted-N` all the same.  CLAUDE.md, *Never*:
H601's bytes may not enter this repository's tree, and `P2-3` commits these
records under `bench/`.  Version 1.0 wrote every `lladdr` as `ip` printed it.

The rule, and one owner for its list.  A hardware address is written verbatim
only if its canonical form (six octets, lower case) is one of the addresses
`tools/audit-bench-log.py`'s `ALLOW` names in a `("match", literal)` entry
whose literal is itself an address -- six colon- or dash-separated octets, or
twelve bare hex digits.  That file is read by path, the way `leakscan.py`
reads it; no second copy of the list exists here.  Every other address is
written `unlisted-N`, N its order of first appearance in this run's output.
Nothing about it is derived from its bytes: no hash, prefix, OUI or length.
The `00:12:34:56:78:9` entry is a PREFIX (five and a half octets), not an
address, so it is not honoured: those six SDK placeholders are labelled like
any other address.

Where it holds -- every exit, not only the `lladdr` field: event lines and
comment lines (the events file's one writer applies it), the meta (applied to
every string in it, keys included), stdout and stderr (one print path), and
`report`'s output.  So an address that only a sink can see is still caught:
ping's banner naming an `enx<12 hex>` interface, the route's `dev` in the
meta, an exception's message.  A failed `ip neigh` poll's output is withheld
ENTIRELY, not redacted -- it can carry an lladdr, and what is needed from it
is its exit status.  If the allowlist cannot be loaded, `--neigh` is refused;
any other run then labels every address it meets.

Not covered, and the self-test's scanner cannot see them either: an address
in another spelling -- dotted `0011.2233.4455`, octets without a leading zero,
one inside a longer hex run, an EUI-64 inside an IPv6 address.  `ip -4` and
iputils print none of these.  Labels are per run: `unlisted-1` in two runs
need not be one address, because keeping identity across runs would take a
persistent map or a label derived from the bytes.

REFUTATION CONDITIONS AND CONTROLS -- written before the code they test
------------------------------------------------------------------------
Each claim below names the reading that would refute it and the `--self-test`
case that holds it.  Every check has a positive and a negative control: a
check that can only pass is not a check.

H1  An `icmp-reply`'s t is ping's report of a reply, stamped within the
    lag threshold of ping's own `-D` stamp.  Refuted by a run whose
    `icmp_lag_ms.over_threshold` is non-zero on an idle host, or by several ICMP
    lines per read.  Controls: `L1` (lines lagged 5 s are flagged, lines lagged
    0 are not -- both directions, exact seqs), `L2` (a stamp in the future is
    flagged: realtime stepped, or the line is not what it seems), `U10` at the
    boundary.
H2  With `-O`, a working ping prints at least one line per interval after its
    first send, so a run of `--icmp` longer than 1 s plus two intervals with no
    ICMP line at all means the INSTRUMENT failed, not that the target is quiet.
    The run then exits 1.  Controls: `S1` (a ping that prints only its header ->
    exit 1) against `N1`/`N2` (a ping that prints only `no answer yet` -> exit 0,
    `none` replies).
H3  The parser misses no reply: ping's own `M received` (printed on the SIGINT
    this tool sends it at stop) equals the probe's `icmp-reply` count plus its
    `(truncated)` count.  A mismatch exits 1.  Controls: `P4` (agree -> 0, over
    a run that includes a DUP, a truncated reply and an error line) and `S2` (a
    ping whose statistics claim one more -> 1).  推: that iputils counts a
    truncated reply in `received` and neither a DUP nor a bad checksum is its
    `gather_statistics` as recalled, not read here, and no truncated reply has
    been seen on this host.  A bench run that shows one and an H3 mismatch
    refutes it.
H4  TCP outcomes are told apart: a listening port reads `ok`, a bound port with
    no listener reads `refused` (ECONNREFUSED), a listener whose accept queue is
    full reads `timeout` (the SYN is dropped).  Controls: `T1`, `T2`, `T3`, and
    `U5` for the errno table, including the `unreachable` errnos no loopback
    test can produce.
H5  `--until` ends the run at the first MATCHING event and at nothing else.
    Controls: `T4` (`tcp:OPEN:ok` stops well inside `--seconds`) against `T5`
    (`tcp:CLOSED:ok` sees only `refused` and runs to `--seconds`); `D3`; `U9`.
H6  Each datagram is one `udp` event with its true length and peer, and
    `kernel_real` is the kernel's receive stamp or `-`, never a guess.
    Controls: `D1` (7 and 300 bytes from a known port), `D2` (the stamp lies
    within 2 s of the sender's clock).
H7  `neigh` emits on change only, and always for the first poll; a poll that
    fails is a gap, never a `NONE`, and exits 1.  Controls: `G1` (NONE NONE
    REACHABLE REACHABLE STALE -> exactly three events, in that order, exit 0)
    against `G3` (every poll fails -> no event, exit 1); `G1b` (every poll
    leads its own session, so a Ctrl-C cannot fail one); `G2` (a non-loopback
    target's polls carry the route's `dev`).
H8  Every refusal exits 2 with a reason, no traceback, and no output file.
    Controls: `R1`-`R20`, each required to be refused for ITS reason, and the
    permitting halves `R7b` (`--force` does overwrite), `R11` (2 ms on the
    measured iputils runs) and `R18` (a route WITH a source address passes),
    so no guard refuses everything.
H9  No child survives a run the probe ends itself: --seconds, --until,
    SIGINT, SIGTERM, SIGHUP.  A SIGKILL of the probe cannot be caught; the
    orphaned ping then dies of SIGPIPE on its next `-O` line (量 2026-09-23,
    the real ping on loopback: 0.207 s after the kill at -i 0.2, one achieved
    interval).  Controls: `C1` (`--seconds`), `C2` (SIGTERM), `C3` (SIGINT),
    `C3b` (SIGINT to the whole process group, as a terminal's Ctrl-C sends
    it: ping leads its own session and group, so only the probe stops it --
    the mechanism is asserted, because the outcome alone is a race the probe
    usually wins), `C4` (a ping that ignores SIGINT and SIGTERM is SIGKILLed
    and reaped), `C5` (SIGKILL of the probe itself: every line before the kill
    is intact and `report` still reads it).  `C5` does not test the per-line
    FLUSH -- Python's text layer hands the OS whole lines even unflushed, so
    the file ends on a line either way; the flush is held by `D1` and `C2`,
    which read the record while the run is live (a mutation run removing the
    flush was caught there, not by `C5`).
H10 The file format holds: every non-comment line parses as `<float> <kind>
    k=v...`, t never decreases within a source, the meta carries every
    key the format names, a clean record starts with `start` and ends with
    `stop`.  Controls: `F1`-`F5` over every file the suite made (`F0` requires
    that population to be there), and `U13` (a hand-broken line is rejected
    by the same parser).
H11 No hardware address leaves the process unless the allowlist names it
    (ADDRESSES above).  Refuted by any artefact of a run -- events, meta,
    stdout, stderr, `report` -- holding an address the allowlist does not
    name, in colon, dash, bare or `enx` form.  Controls: `A1` (a
    non-allowlisted lladdr reads `unlisted-1`, a second `unlisted-2`, the
    first again `unlisted-1`); `A2` (every artefact of that run scanned by a
    scanner written apart from the tool's own pattern, and each injected
    address searched for in six spellings: zero hits); `A3` (a failing
    poll's output is not quoted -- its marker text is nowhere); `A4` (an
    address only a sink sees -- ping's banner and stderr -- is labelled);
    `A5` (the route's `enx` device, in the meta and in the host-fault
    refusal); `A6` (allowlisted addresses written verbatim in upper and lower
    case, one of them matched only through the canonical form); `A7`, `A8`,
    `A9` (a missing, a raising and an `ALLOW`-less allowlist file each refuse
    `--neigh`: exit 2, no file) against `A10` (the same broken allowlist
    does not refuse a `--tcp` run -- the permitting half); `A11` (`report`
    on a record version 1.0 wrote, raw lladdr in it, prints a label); `A12`
    (argparse's own error line, quoting a bad value, is labelled);
    `K1`-`K5` (canonical form, the loader on the real file, the redactor,
    labels that depend on order and not on bytes).
H12 Every stamp the probe writes and every deadline it computes is on
    CLOCK_MONOTONIC_RAW, and the record says so.  Refuted by a stamp outside
    a RAW bracket the harness draws round the run, or a `--seconds` run whose
    RAW span is not `--seconds`, while `tools/clockshim.py` runs every
    Python read of CLOCK_MONOTONIC at half rate and 1000 s ahead: on a CI
    runner the two clocks otherwise agree to milliseconds, and a MONOTONIC
    stamp would pass any bracket.  The offset alone is not enough: on this
    host MONOTONIC - RAW is itself minutes (量 2026-09-23: -189 s) and grows
    with every slewed hour, so it can cancel the shim's offset; the spans
    and the ratio are rate tests, which no offset blinds.  Controls: `Q1`
    (every event, comment stamp, tcp `start_raw`, RAW meta key and `first`
    inside the bracket, every event kind present), `Q2` (the deadline, the
    record's span, and `mono_at_*` running at half the harness's own
    MONOTONIC/RAW rate, which also proves the shim took), `Q3` (the header
    and the meta declare RAW as a whole token, no meta key ends `_mono`),
    `Q5` (a Python without CLOCK_MONOTONIC_RAW is refused, exit 2, before
    any file or child, and the same run with it runs), `Q6` (`boot_id` and
    both `clocksource` readings equal the harness's own reads; `boot_id`
    passes the address gate only as a version-4 UUID), `Q7` (a udp line's
    `lag_ms` puts the kernel's receive between the send and the read, and
    agrees with the lag the harness measures from the send side).
H13 A record of every version reads on the clock its header declares:
    1.0-1.2 on CLOCK_MONOTONIC with `start_mono=`, 1.3 on RAW with
    `start_raw=` and `lag_ms=`.  A line carrying the other clock's keys, and
    a header the meta contradicts, are MALFORMED.  Controls: `U14` (the
    header's clock is the whole token after `is absolute`, so a header that
    names RAW in passing still declares MONOTONIC), `Q4` (planted 1.1 and
    1.2 records and this suite's 1.3 record read, and `report` labels each
    with its own clock), `Q4b` (four mismatches are MALFORMED), `Q4c` (every
    committed record under `bench/` reads).
H14 The argument refusals are one function, `refuse_args`, that reads
    nothing but the parsed arguments, and `main()` runs it on
    `build_parser()`'s arguments before anything reads the host -- so a
    card's check of a HOST cell (`FW-124`) and the run refuse the same
    arguments for the same reason.  Controls: `V1` (in-process, with files,
    subprocesses, sockets, clocks and the environment poisoned: five
    refusals for their reasons, the good form permitted, the poison shown
    to take), `V2` (`main()` calls `build_parser` once and `refuse_args`
    before the allowlist is read).

The self-test drives a FAKE ping and a FAKE `ip` -- small scripts it writes
into a temporary directory and passes as `--ping`/`--ip` -- and real loopback
sockets for TCP and UDP.  It sends nothing beyond 127.0.0.1, and every run that
names a non-loopback target selects `--neigh` alone through the fake `ip`, so
even a broken injection could only read a neighbour table.  H1's claim about
the REAL ping is the measurement above, not a CI case; a runner's ping is not
this host's.

WHAT IT DOES NOT ESTABLISH
--------------------------
* When a frame crossed the cable.  An `icmp-reply` is stamped when the probe
  read ping's line; ping's `-D` stamp is taken when ping printed it, after its
  own `recvmsg`.  The lag covers ping's print to the probe's read, not the
  kernel's receipt to ping's print.
* *Network up* finer than the ACHIEVED ping interval (`ping.achieved_interval_ms`
  in the meta): the first reply is at most one interval after the target began
  to answer.
* That a daemon serves.  `tcp ... result=ok` means the kernel completed a
  handshake on a listening socket; it does not mean the daemon has called
  `accept()` or would answer a request.
* The console-versus-network channel offset.  `udp` gives the host's half of
  that measurement; the card that makes rlxfw print and send in one command
  owns the rest (`D8`'s refutation condition).
* When a neighbour entry changed.  A `neigh` event is an upper bound; the
  change happened after the previous poll.
* Anything about realtime.  A realtime step during the run corrupts every
  `*_real` cross-check, a udp line's `lag_ms` included; `report` prints the
  drift of realtime against the record's own clock between the start and
  stop pairs so a step is visible.  On this host realtime follows the slewed
  MONOTONIC between steps, so a RAW record's drift carries the slew too.
* RAW's rate against true time.  RAW is the host's unslewed counter; that it
  is nearer true time than a slewed MONOTONIC is 推 here, and no record of
  this tool measures it.
* How long a kernel wait lasted.  `select()` and the library's own timeouts
  (`subprocess`'s waits) run on CLOCK_MONOTONIC; what is RAW is every stamp
  and every deadline this file computes.
* That the probe is passive.  Against a real target every echo request, SYN
  and the ARP they provoke is a packet the board handles while it boots.  The
  rates are the card's to choose and to state.
* Who answered.  A reply from the target's address is a reply from whatever
  holds that address -- and an `unlisted-N` lladdr says only that it is not
  an address the allowlist names, not whose it is.

Exit codes: 0 the run ended cleanly (any stop reason, signals included) and its
            record is complete, every selected instrument having worked
            1 the record was written but an instrument failed (H2, H3, ping
            exiting on its own or ignoring SIGINT, a failed neighbour poll)
            2 refused before anything started; no output file exists

Run:  tools/hostprobe.py run --out bench/<date>/X-probe --target 10.1.1.1 \\
          --seconds 60 --icmp --icmp-interval 0.05 --tcp 80 --neigh \\
          --until tcp:80:ok
      tools/hostprobe.py report bench/<date>/X-probe
      tools/hostprobe.py --self-test
"""
import argparse
import builtins
import contextlib
import errno
import datetime
import glob
import importlib.machinery
import importlib.util
import io
import ipaddress
import json
import os
import platform
import re
import select
import shutil
import signal
import socket
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import traceback

# 1.0 -> 1.1 on 2026-09-23: an lladdr, and every other hardware address the
# run meets, is written only if the allowlist names it (ADDRESSES).  A 1.0
# record's lladdr is `ip`'s raw text; a 1.1 record's is not.
# 1.2 -> 1.3 on 2026-09-23 (P2-4): every stamp and deadline on
# CLOCK_MONOTONIC_RAW (ONE CLOCK).  The meta's start_mono, end_mono,
# stop_decided_mono and ping.started_mono become *_raw, a tcp line's
# start_mono= becomes start_raw=, a udp line gains lag_ms=, and the meta gains
# boot_id, clocksource, clocksource_end, mono_at_start and mono_at_end.
TOOL_VERSION = "1.3"
CLOCK = "CLOCK_MONOTONIC_RAW"
#: The clock every record before 1.3 was written on.
CLOCK_LEGACY = "CLOCK_MONOTONIC"
THIS = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(THIS))
#: The committed shim that makes CLOCK_MONOTONIC disagree with RAW, for Q1/Q2.
CLOCKSHIM_PATH = os.path.join(ROOT, "tools", "clockshim.py")
BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"
CLOCKSOURCE_PATH = "/sys/devices/system/clocksource/clocksource0/current_clocksource"


def now_raw():
    """The probe's one clock: every stamp it writes, every deadline it computes.
    Looked up at each call, so a Python without it fails here -- which
    refuse_host() keeps from ever happening after a file or child exists."""
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)


def now_mono():
    """CLOCK_MONOTONIC, read only for mono_at_start and mono_at_end."""
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def read_line_file(path):
    """A one-line kernel file, stripped; None when it cannot be read."""
    try:
        with open(path, encoding="ascii", errors="replace") as f:
            return f.read().strip() or None
    except OSError:
        return None


_UUID4_RX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def boot_id_value(text):
    """The kernel's boot_id if it is a version-4 (random) UUID, else None.

    Only such a string skips the address gate (see run's meta): its last
    group is 48 random bits, where a version-1 UUID's is a node address."""
    s = (text or "").strip()
    return s if _UUID4_RX.match(s) else None
#: The allowlist's one owner, read by path as leakscan.py's load_abl() reads
#: it.  Derived from this file's own location, so a copy of this file outside
#: the repository finds no allowlist -- which is how A7-A9 break it.
ABL_PATH = os.path.join(ROOT, "tools", "audit-bench-log.py")
#: capdate.py, read by path for F6 only: the one reader of started_wallclock.
CAPDATE_PATH = os.path.join(ROOT, "tools", "capdate.py")


def capdate_when(meta_path):
    """capdate.capture_when on meta_path: (datetime, None) or (None, reason).
    A capdate that cannot be loaded is a reason, never a pass."""
    try:
        ldr = importlib.machinery.SourceFileLoader("hostprobe_capdate", CAPDATE_PATH)
        spec = importlib.util.spec_from_loader("hostprobe_capdate", ldr)
        mod = importlib.util.module_from_spec(spec)
        ldr.exec_module(mod)
        return mod.capture_when(meta_path)
    except Exception as e:          # noqa: BLE001 -- any failure is a reason
        return None, "capdate unavailable: %s" % e

# ------------------------------------------------------------- host facts
# iputils releases whose smallest unprivileged `-i` this project has measured,
# in seconds.  量 2026-09-23 on this host, 127.0.0.1 only: 20240117 exits 2 on
# `-i 0.0019` and runs `-i 0.002`.
MEASURED_MIN_INTERVAL_S = {20240117: 0.002}
# The floor for every other release: the 0.2 s older iputils documented for a
# non-root user.  Not measured here.  A floor set too high refuses a run the
# host could have done; one set too low lets ping die after the run has
# started, which is the failure the pre-flight exists to move earlier.
FALLBACK_MIN_INTERVAL_S = 0.2

DEFAULT_ICMP_INTERVAL_S = 0.2
# The line lag above which an ICMP line is flagged.  1 ms because it is the
# order of the console side's own capture floor (seating 17: 0.517 and
# 0.868 ms), so a flagged line is one whose stamp is worse than what the
# console channel resolves.  量 2026-09-23 on this host: 766 reply lines, max
# 0.435 ms, so an idle host flags none; buffered output lags by whole
# intervals, and the smallest interval ping accepts here is 2 ms.
DEFAULT_LAG_THRESHOLD_MS = 1.0
# ping prints its -D stamp truncated to the microsecond and time.time() is not
# truncated, so a faithful read can land up to 1 us BEFORE ping's stamp.  More
# negative than this is a realtime step or a line that is not what it seems.
NEGATIVE_LAG_TOLERANCE_MS = 0.001
DEFAULT_TCP_INTERVAL_S = 0.2
DEFAULT_TCP_TIMEOUT_S = 1.0
DEFAULT_NEIGH_INTERVAL_S = 0.2
# An `ip neigh` poll still running after this long is killed and counted as an
# error, so one hung poll cannot silence the neighbour probe for the run.
NEIGH_POLL_CAP_S = 2.0
# At stop ping gets SIGINT (so it prints its statistics: H3), then SIGTERM,
# then SIGKILL, each after this long without exiting.
PING_STOP_GRACE_S = 1.0
# H2's window: a working `ping -O` prints an ICMP line within this plus two
# intervals of starting.
ICMP_SILENCE_STARTUP_S = 1.0

NUD_STATES = ("INCOMPLETE", "REACHABLE", "STALE", "DELAY", "PROBE", "FAILED",
              "NOARP", "PERMANENT", "NONE")
TCP_RESULTS = ("ok", "refused", "timeout", "unreachable", "error")
UNREACHABLE_ERRNOS = (errno.EHOSTUNREACH, errno.ENETUNREACH, errno.EHOSTDOWN,
                      errno.ENETDOWN)
# 讀 /usr/include/asm-generic/socket.h on this host: SO_TIMESTAMPNS is
# SO_TIMESTAMPNS_OLD, 35, on 64-bit asm-generic architectures, and
# SCM_TIMESTAMPNS equals it.  Python 3.12 exports neither name.  Elsewhere the
# number differs, so the stamp is not requested there and kernel_real is `-`.
SO_TIMESTAMPNS = 35
SO_TIMESTAMPNS_MACHINES = ("x86_64", "aarch64")

# ------------------------------------------------------------- the format
#: every event kind and its keys, in the order they are written, per clock:
#: 1.0-1.2 wrote CLOCK_MONOTONIC records and 1.3 writes CLOCK_MONOTONIC_RAW
#: ones.  A reader picks the table by the clock the record's header declares
#: (header_clock).  The format is fixed: `boot-timeline --probe` parses it.
EVENT_KEYS_BY_CLOCK = {
    CLOCK_LEGACY: {
        "start": ("t_real",),
        "stop": ("t_real", "reason"),
        "icmp-reply": ("seq", "ttl", "rtt_ms", "ping_real"),
        "icmp-silent": ("seq",),
        "tcp": ("port", "result", "errno", "start_mono", "dur_ms"),
        "neigh": ("state", "lladdr"),
        "udp": ("port", "peer", "len", "kernel_real"),
    },
    CLOCK: {
        "start": ("t_real",),
        "stop": ("t_real", "reason"),
        "icmp-reply": ("seq", "ttl", "rtt_ms", "ping_real"),
        "icmp-silent": ("seq",),
        "tcp": ("port", "result", "errno", "start_raw", "dur_ms"),
        "neigh": ("state", "lladdr"),
        "udp": ("port", "peer", "len", "kernel_real", "lag_ms"),
    },
}
#: what this version writes
EVENT_KEYS = EVENT_KEYS_BY_CLOCK[CLOCK]
#: which clock-reading loop stamps each kind; t never decreases within one
SOURCE = {"start": "tool", "stop": "tool", "icmp-reply": "icmp",
          "icmp-silent": "icmp", "tcp": "tcp", "neigh": "neigh", "udp": "udp"}
EVENT_RX = re.compile(r"^(\d+\.\d{6}) ([a-z][a-z-]*)((?: [a-z_]+=\S+)*)$")
HEADER = ("hostprobe %s: t_raw is absolute CLOCK_MONOTONIC_RAW seconds "
          "(clock_gettime(CLOCK_MONOTONIC_RAW), the clock console-capture 1.5's "
          "t0_raw is read on); t_real, ping_real and kernel_real are "
          "CLOCK_REALTIME, cross-checks only; a udp line's lag_ms is t_real "
          "minus kernel_real, so its kernel stamp on this clock is "
          "t_raw - lag_ms/1000" % TOOL_VERSION)
#: The header's declaration of the first field's clock.  1.0-1.2 wrote `t_mono
#: is absolute CLOCK_MONOTONIC seconds`, 1.3 `t_raw is absolute
#: CLOCK_MONOTONIC_RAW seconds`.  The clock is the whole token after `is
#: absolute` and is compared exactly: CLOCK_MONOTONIC is a prefix of
#: CLOCK_MONOTONIC_RAW, so `in` -- 1.2's F4 -- cannot tell them apart (U14).
HEADER_CLOCK_RX = re.compile(r"^# hostprobe \S+: t_[a-z]+ is absolute (CLOCK_[A-Z_]+)\b")
PROBES_RX = re.compile(r"^# probes (.*)$")


def header_clock(line):
    """The clock an events file's first line declares, or None."""
    m = HEADER_CLOCK_RX.match(line or "")
    return m.group(1) if m else None

# ------------------------------------------------------ ping's own format
# 讀 `strings /usr/bin/ping` on this host (iputils 20240117): `[%lu.%06lu] `,
# `%d bytes from %s:`, ` icmp_seq=%u`, ` ttl=%d`, ` time=%ld.%03ld ms` (and the
# %01ld / %02ld / %ld forms), ` (DUP!)`, ` (truncated)`, `From %s icmp_seq=%u `,
# `no answer yet for icmp_seq=%lu`.
_TS = r"(?:\[(?P<real>\d+\.\d+)\] )?"
PING_REPLY_RX = re.compile(
    r"^" + _TS + r"(?P<bytes>\d+) bytes from (?P<src>[^:\s]+): "
    r"icmp_seq=(?P<seq>\d+) ttl=(?P<ttl>\d+)"
    r"(?: time=(?P<rtt>\d+(?:\.\d+)?) ms)?(?P<tail>.*)$")
PING_SILENT_RX = re.compile(
    r"^" + _TS + r"no answer yet for icmp_seq=(?P<seq>\d+)\s*$")
PING_ERROR_RX = re.compile(r"^" + _TS + r"From \S+ icmp_seq=\d+")
PING_HEADER_RX = re.compile(r"^PING \S+ \(")
PING_STATS_RX = re.compile(
    r"^(?P<tx>\d+) packets transmitted, (?P<rx>\d+) received")
PING_SUMMARY_RX = re.compile(r"^(?:--- \S+ ping statistics ---|rtt |round-trip )")
PING_VERSION_RX = re.compile(r"\biputils[ -]s?(\d{8})\b")


class Refused(Exception):
    """Raised before any output file or child process exists."""


# -------------------------------------------------------------- addresses
#: A string that IS one address: six octets under one separator, or twelve
#: bare hex digits, optionally as systemd's `enx<12 hex>` interface name.
_MAC_SEP_RX = re.compile(r"^[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}$")
_MAC_BARE_RX = re.compile(r"^(?:[eE][nN][xX])?([0-9A-Fa-f]{12})$")
#: What the redactor looks for in free text.  Wider than one address on
#: purpose: a run of SIX OR MORE colon- or dash-separated octets is taken whole
#: (a longer hardware address is labelled, not half-printed), and twelve hex
#: digits bounded by non-hex -- which is what finds an `enx<12 hex>` name,
#: where `\b` would not (audit-bench-log.py's own note on that pattern).  A
#: false match costs a label; a missed one is a leak.
MAC_TEXT_RX = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5,}(?![0-9A-Fa-f])"
    r"|(?<![0-9A-Fa-f])(?:[eE][nN][xX])?[0-9A-Fa-f]{12}(?![0-9A-Fa-f])")


class AllowlistUnavailable(Exception):
    pass


def canonical_mac(tok):
    """Six lower-case octets joined by `:` for any spelling of ONE address;
    None for anything else, which the redactor then labels whole."""
    t = (tok or "").strip()
    if _MAC_SEP_RX.match(t):
        h = re.sub(r"[:-]", "", t)
    else:
        m = _MAC_BARE_RX.match(t)
        if not m:
            return None
        h = m.group(1)
    h = h.lower()
    return ":".join(h[i:i + 2] for i in range(0, 12, 2))


def _rel(path):
    try:
        r = os.path.relpath(path, ROOT)
    except ValueError:
        return path
    return path if r.startswith("..") else r


def load_mac_allowlist(path=None):
    """The canonical addresses `tools/audit-bench-log.py`'s ALLOW names.

    Its `("match", literal)` entries whose literal is itself one address --
    six octets under one separator, or twelve bare hex digits.  An `enx` name
    and a prefix (`00:12:34:56:78:9`, five and a half octets) are not, and are
    not honoured.  Read by path, the way leakscan.py's load_abl() reads it:
    the list has one owner and no copy here.  AllowlistUnavailable, never a
    fallback, when the file cannot be run or its ALLOW cannot be read.
    """
    path = path or ABL_PATH
    try:
        ldr = importlib.machinery.SourceFileLoader("hostprobe_abl", path)
        spec = importlib.util.spec_from_loader("hostprobe_abl", ldr)
        mod = importlib.util.module_from_spec(spec)
        ldr.exec_module(mod)
        allow = mod.ALLOW
    except (Exception, SystemExit) as e:
        raise AllowlistUnavailable("%s could not be loaded (%s: %s)"
                                   % (_rel(path), type(e).__name__, e)) from None
    macs = set()
    try:
        for scope, needle, _why in allow:
            if (scope == "match" and isinstance(needle, str)
                    and (_MAC_SEP_RX.match(needle)
                         or re.fullmatch(r"[0-9A-Fa-f]{12}", needle))):
                macs.add(canonical_mac(needle))
    except (TypeError, ValueError) as e:
        raise AllowlistUnavailable("%s's ALLOW is not a list of (scope, needle, "
                                   "reason): %s" % (_rel(path), e)) from None
    return frozenset(macs)


class Redactor:
    """The one gate a hardware address passes on its way out of this process.

    `address()` takes a value known to be an address (an lladdr); `text()`
    finds addresses in anything else by MAC_TEXT_RX; `obj()` is `text()` over
    every string of a JSON-able object, keys included.  All three answer from
    one allowlist and one label map, so an address has one label across the
    events, the meta, stdout and stderr of a run.
    """

    def __init__(self, allowed=frozenset(), loaded=False, why_not=""):
        self.allowed = frozenset(allowed)
        self.loaded = loaded
        self.why_not = why_not
        self.labels = {}

    def label(self, key):
        # The ORDER of first appearance, and nothing else: no hash, no
        # prefix, no OUI, no length (H11; K5 is the control).
        if key not in self.labels:
            self.labels[key] = "unlisted-%d" % (len(self.labels) + 1)
        return self.labels[key]

    def _one(self, tok):
        c = canonical_mac(tok)
        if c is not None and c in self.allowed:
            return tok
        return self.label(c if c is not None else tok.lower())

    def address(self, raw):
        if raw in (None, "", "-"):
            return "-"
        return self._one(raw)

    def text(self, s):
        return MAC_TEXT_RX.sub(lambda m: self._one(m.group(0)), str(s))

    def obj(self, o):
        if isinstance(o, str):
            return self.text(o)
        if isinstance(o, dict):
            return {(self.text(k) if isinstance(k, str) else k): self.obj(v)
                    for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [self.obj(v) for v in o]
        return o


#: One per process, so a run has one label map.  It starts with NO allowlist
#: -- every address labelled -- until the pre-flight or `report` loads it.
REDACT = Redactor()


def use_allowlist():
    """Load the owner's list into REDACT.  -> None, or why it could not."""
    try:
        REDACT.allowed = load_mac_allowlist()
    except AllowlistUnavailable as e:
        REDACT.allowed, REDACT.loaded, REDACT.why_not = frozenset(), False, str(e)
        return str(e)
    REDACT.loaded, REDACT.why_not = True, ""
    return None


def say(msg, err=False):
    """The one print path: every line through the redactor."""
    print(REDACT.text(msg), file=sys.stderr if err else sys.stdout)


# ------------------------------------------------------------ pure parts
def parse_ping_line(line):
    """One line of `ping -D -O -n` -> a dict whose `kind` is one of reply,
    silent, dup, truncated, error, header, stats, summary, blank, other."""
    s = line.rstrip("\r\n")
    if not s.strip():
        return {"kind": "blank"}
    m = PING_REPLY_RX.match(s)
    if m:
        tail = m.group("tail").strip()
        if not tail:
            kind = "reply"
        elif "(DUP!)" in tail:
            kind = "dup"
        elif "(truncated)" in tail:
            kind = "truncated"
        else:
            kind = "other"
        return {"kind": kind, "seq": int(m.group("seq")),
                "ttl": int(m.group("ttl")), "rtt": m.group("rtt") or "-",
                "real": m.group("real") or "-"}
    m = PING_SILENT_RX.match(s)
    if m:
        return {"kind": "silent", "seq": int(m.group("seq")),
                "real": m.group("real") or "-"}
    if PING_ERROR_RX.match(s):
        return {"kind": "error"}
    if PING_HEADER_RX.match(s):
        return {"kind": "header"}
    m = PING_STATS_RX.match(s)
    if m:
        return {"kind": "stats", "tx": int(m.group("tx")), "rx": int(m.group("rx"))}
    if PING_SUMMARY_RX.match(s):
        return {"kind": "summary"}
    return {"kind": "other"}


def parse_ping_version(text):
    """`ping -V` -> the iputils release as an int (20240117), or None."""
    m = PING_VERSION_RX.search(text or "")
    return int(m.group(1)) if m else None


def icmp_interval_floor(release):
    """(seconds, why): the smallest `-i` this tool will hand to that ping."""
    if release in MEASURED_MIN_INTERVAL_S:
        return (MEASURED_MIN_INTERVAL_S[release],
                "measured on iputils %d on this project's host, 量 2026-09-23: "
                "-i 0.0019 exits 2 with `cannot flood, minimal interval for "
                "user must be >= 2 ms`" % release)
    return (FALLBACK_MIN_INTERVAL_S,
            "iputils %s has not been measured by this project, and the floor "
            "for an unmeasured release is the 0.2 s older iputils documented "
            "for a non-root user" % release)


def check_icmp_interval(seconds, release):
    """The whole milliseconds ping will run at, or Refused: this release's
    floor (the host's half, preflight), then icmp_whole_ms."""
    floor, why = icmp_interval_floor(release)
    if seconds < floor - 1e-12:
        raise Refused(
            "--icmp-interval %g is below the minimum %g s a non-root ping "
            "accepts (%s). ping would exit 2 after the run had started; "
            "refusing now instead" % (seconds, floor, why))
    return icmp_whole_ms(seconds)


def icmp_whole_ms(seconds):
    """The whole milliseconds ping will run at, or Refused.  Reads nothing
    but the number, so it is refuse_args' half of the interval check."""
    ms = int(seconds * 1000)
    if abs(seconds * 1000 - ms) > 1e-6:
        raise Refused(
            "--icmp-interval %r is not a whole number of milliseconds, and ping "
            "truncates -i to whole ms (量 2026-09-23: -i 0.0029 ran at a 2.034 ms "
            "median gap). It would run at %d ms; pass that, or another whole "
            "number of ms" % (seconds, ms))
    return ms


def line_lag_ms(t_real, ping_real):
    """The probe's read time minus ping's -D stamp, in ms; None without a stamp."""
    if ping_real in (None, "-"):
        return None
    return (t_real - float(ping_real)) * 1e3


def lag_flagged(lag_ms, threshold_ms):
    """H1: over the threshold, or negative beyond the -D truncation."""
    return lag_ms > threshold_ms or lag_ms < -NEGATIVE_LAG_TOLERANCE_MS


def classify_errno(err):
    """(result, errno name) for a finished connect()."""
    if not err:
        return "ok", "0"
    name = errno.errorcode.get(err, str(err))
    if err == errno.ECONNREFUSED:
        return "refused", name
    if err == errno.ETIMEDOUT:
        return "timeout", name
    if err in UNREACHABLE_ERRNOS:
        return "unreachable", name
    return "error", name


def parse_neigh(text, target):
    """(state, lladdr, n_entries) for TARGET in `ip -4 neigh show` output.

    No entry reads ("NONE", "-", 0): loopback is NOARP and has none.  An entry
    in the kernel's own NUD_NONE state also prints NONE; the two are not told
    apart, and neither is a usable neighbour.  The address is compared as a
    whole token, so 10.1.1.10's entry is not 10.1.1.1's.
    """
    entries = []
    for line in (text or "").splitlines():
        t = line.split()
        if not t or t[0] != target:
            continue
        state = next((x for x in reversed(t) if x in NUD_STATES), "UNKNOWN")
        lladdr = "-"
        if "lladdr" in t and t.index("lladdr") + 1 < len(t):
            lladdr = t[t.index("lladdr") + 1]
        entries.append((state, lladdr))
    if not entries:
        return "NONE", "-", 0
    return entries[0][0], entries[0][1], len(entries)


def route_verdict(target, rc, text):
    """(ok, dev, src, why) from `ip -4 route get TARGET`, non-loopback target.

    The reading is looprun's `P-a`.  量 2026-09-08 (`notes/dev-loop.md`
    § 15.1): the USB GbE had been re-attached to WSL, 10.1.1.2/24 does not
    survive that, and a host fault was reported in the board's vocabulary.
    Here the same fault is a refusal that names the host.
    """
    text = text or ""
    if rc != 0:
        return (False, None, None, "`ip -4 route get %s` exited %d: %s"
                % (target, rc, " ".join(text.split())[:160]))
    toks = text.split()
    rtype = toks[0] if toks and not toks[0][:1].isdigit() else "unicast"
    dev = re.search(r"\bdev\s+(\S+)", text)
    src = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", text)
    if rtype == "local":
        return (False, None, None,
                "%s is one of this host's own addresses (`ip -4 route get` says "
                "local): the probe would measure the host, not a board" % target)
    if rtype != "unicast":
        return (False, None, None, "the route to %s is `%s`, not a unicast "
                "route to one host" % (target, rtype))
    if not dev or not src:
        return (False, None, None,
                "HOST FAULT: the route to %s has no IPv4 source address "
                "(`ip -4 route get` printed `%s`, no `src`). This is looprun's "
                "P-a fault of 2026-09-08 -- the USB NIC re-attached to WSL and "
                "its address gone -- and it is the host to fix, not the board"
                % (target, " ".join(toks)[:120]))
    return True, dev.group(1), src.group(1), ""


def parse_until(spec, icmp, tcp_ports, neigh, udp_ports):
    """`--until SPEC` -> a tuple, or Refused naming why it can never fire.

    SPEC is icmp-reply | icmp-silent | tcp[:PORT[:RESULT]] | neigh[:STATE] |
    udp[:PORT].  One that the selected probes cannot produce is refused: it
    would always run to --seconds, and a card would read that as the event not
    happening.
    """
    parts = spec.split(":")
    kind = parts[0]

    def no(why):
        raise Refused("--until %r: %s" % (spec, why))

    def port_of(s, ports, flag):
        try:
            p = int(s)
        except ValueError:
            no("%r is not a port number" % s)
        if p not in ports:
            no("port %d is not probed; add %s %d" % (p, flag, p))
        return str(p)

    if kind in ("icmp-reply", "icmp-silent"):
        if len(parts) != 1:
            no("%s takes no qualifier" % kind)
        if not icmp:
            no("needs --icmp")
        return (kind,)
    if kind == "tcp":
        if not tcp_ports:
            no("needs --tcp PORT")
        if len(parts) > 3:
            no("the form is tcp[:PORT[:RESULT]]")
        out = ["tcp"]
        if len(parts) >= 2:
            out.append(port_of(parts[1], tcp_ports, "--tcp"))
        if len(parts) == 3:
            if parts[2] not in TCP_RESULTS:
                no("result must be one of %s" % ", ".join(TCP_RESULTS))
            out.append(parts[2])
        return tuple(out)
    if kind == "udp":
        if not udp_ports:
            no("needs --udp-listen PORT")
        if len(parts) > 2:
            no("the form is udp[:PORT]")
        if len(parts) == 2:
            return ("udp", port_of(parts[1], udp_ports, "--udp-listen"))
        return ("udp",)
    if kind == "neigh":
        if not neigh:
            no("needs --neigh")
        if len(parts) > 2:
            no("the form is neigh[:STATE]")
        if len(parts) == 2:
            if parts[1] not in NUD_STATES + ("UNKNOWN",):
                no("state must be one of %s" % ", ".join(NUD_STATES))
            return ("neigh", parts[1])
        return ("neigh",)
    no("unknown event kind %r; the kinds are icmp-reply, icmp-silent, tcp, "
       "neigh, udp" % kind)


def until_matches(u, kind, f):
    """Does event (kind, fields) satisfy the parsed --until tuple `u`?"""
    if u[0] != kind:
        return False
    if kind == "tcp":
        return ((len(u) < 2 or str(f.get("port")) == u[1])
                and (len(u) < 3 or f.get("result") == u[2]))
    if kind == "udp":
        return len(u) < 2 or str(f.get("port")) == u[1]
    if kind == "neigh":
        return len(u) < 2 or f.get("state") == u[1]
    return True


def event_first_keys(kind, f):
    """The `first` keys an event of this kind and these fields sets."""
    keys = [kind]
    if kind == "tcp":
        keys += ["tcp:%s" % f["port"], "tcp:%s:%s" % (f["port"], f["result"])]
    elif kind == "udp":
        keys.append("udp:%s" % f["port"])
    elif kind == "neigh":
        keys.append("neigh:%s" % f["state"])
    return keys


def first_key_order(icmp, tcp_ports, neigh, udp_ports):
    """Every `first` key the selected probes can set, in report order.
    Absent from the meta = not probed; null = probed and never happened."""
    keys = []
    if icmp:
        keys += ["icmp-reply", "icmp-silent"]
    if tcp_ports:
        keys.append("tcp")
    for p in tcp_ports:
        keys += ["tcp:%d" % p] + ["tcp:%d:%s" % (p, r) for r in TCP_RESULTS]
    if neigh:
        keys.append("neigh")
    if udp_ports:
        keys.append("udp")
    keys += ["udp:%d" % p for p in udp_ports]
    return keys


def count_kinds(icmp, tcp_ports, neigh, udp_ports):
    kinds = []
    if icmp:
        kinds += ["icmp-reply", "icmp-silent"]
    if tcp_ports:
        kinds.append("tcp")
    if neigh:
        kinds.append("neigh")
    if udp_ports:
        kinds.append("udp")
    return kinds


def _tok(v):
    s = str(v)
    return "_".join(s.split()) if s.strip() else "-"


def fmt_event(t, kind, pairs):
    return " ".join(["%.6f" % t, kind]
                    + ["%s=%s" % (k, _tok(v)) for k, v in pairs])


def parse_event_line(line, clock):
    """(t, kind, {key: value}) for one event line of a record on `clock`, or
    ValueError.  The keys depend on the clock (EVENT_KEYS_BY_CLOCK); the
    caller takes it from the record's header (header_clock)."""
    table = EVENT_KEYS_BY_CLOCK.get(clock)
    if table is None:
        raise ValueError("no hostprobe version writes a record on %r" % (clock,))
    m = EVENT_RX.match(line)
    if not m:
        raise ValueError("not `<t with 6 decimals> <kind> k=v...`")
    kind = m.group(2)
    if kind not in table:
        raise ValueError("unknown kind %r" % kind)
    pairs = [kv.split("=", 1) for kv in m.group(3).split()]
    keys = tuple(k for k, _v in pairs)
    if keys != table[kind]:
        raise ValueError("%s carries %s; the format on %s says %s"
                         % (kind, ",".join(keys), clock, ",".join(table[kind])))
    return float(m.group(1)), kind, dict(pairs)


def dist(values, nd=3):
    if not values:
        return {"n": 0, "median": None, "min": None, "max": None}
    return {"n": len(values), "median": round(statistics.median(values), nd),
            "min": round(min(values), nd), "max": round(max(values), nd)}


def kernel_stamp(anc):
    """The SCM_TIMESTAMPNS realtime in a recvmsg ancillary list, or None."""
    for level, typ, data in anc:
        if level == socket.SOL_SOCKET and typ == SO_TIMESTAMPNS and len(data) >= 16:
            sec, nsec = struct.unpack("@qq", data[:16])
            return "%d.%09d" % (sec, nsec)
    return None


def enable_rx_stamp(s):
    m = platform.machine()
    if not sys.platform.startswith("linux") or m not in SO_TIMESTAMPNS_MACHINES:
        return False, ("no SO_TIMESTAMPNS value is known here for %s/%s, so "
                       "kernel_real reads -" % (sys.platform, m))
    try:
        s.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, 1)
    except OSError as e:
        return False, "setsockopt(SO_TIMESTAMPNS): %s" % e
    return True, ""


def _which(name):
    if "/" in name or os.sep in name:
        p = os.path.abspath(name)
        return p if os.path.isfile(p) and os.access(p, os.X_OK) else None
    return shutil.which(name)


def _exc_line(e):
    tb = traceback.extract_tb(e.__traceback__)
    where = " (hostprobe.py:%d)" % tb[-1].lineno if tb else ""
    return "%s: %s%s" % (type(e).__name__, e, where)


# ---------------------------------------------------------------- the run
class Recorder:
    """The events file, and the counts, firsts and --until state it implies."""

    def __init__(self, path, force, until, first_keys, kinds):
        self.fh = open(path, "w" if force else "x", encoding="utf-8", newline="\n")
        self.until = until
        self.armed = True
        self.until_hit = None
        self.counts = {k: 0 for k in kinds}
        self.first = {k: None for k in first_keys}

    # The events file's only writer, so the redactor here covers every event
    # and every comment -- including text nothing upstream knew could carry
    # an address, such as ping's banner (H11, A4).
    def comment(self, text):
        self.fh.write(REDACT.text("# " + " ".join(str(text).split())) + "\n")
        self.fh.flush()

    def event(self, t, kind, pairs, fields=None):
        self.fh.write(REDACT.text(fmt_event(t, kind, pairs)) + "\n")
        self.fh.flush()
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if kind in ("start", "stop"):
            return
        fields = fields or {}
        for key in event_first_keys(kind, fields):
            if self.first.get(key) is None:
                self.first[key] = round(t, 6)
        if self.armed and self.until_hit is None:
            for u in self.until:
                if until_matches(u, kind, fields):
                    self.until_hit = ":".join(u)
                    break

    def close(self):
        self.fh.close()


class Icmp:
    """One long-lived `ping -D -O -n -i S TARGET`, read line by line."""

    def __init__(self, rec, ping_path, target, interval_s, threshold_ms):
        self.rec = rec
        self.argv = [ping_path, "-D", "-O", "-n", "-i", "%.3f" % interval_s, target]
        self.threshold = threshold_ms
        self.proc = None
        self.fds, self.buf, self.eof = {}, {}, set()
        self.started = None
        self.exited = self.exited_early = False
        self.rc = self.stopped_by = None
        self.lags, self.flagged, self.no_stamp = [], 0, 0
        self.lines_icmp, self.max_per_read, self.multi_reads = 0, 0, 0
        self.prev, self.gaps_ms = {}, []
        self.stats = None
        self.other = {k: 0 for k in ("header", "dup", "truncated", "error",
                                     "summary", "other", "stderr")}

    def start(self):
        # Its own session: a Ctrl-C at the terminal goes to the process group,
        # and a ping that caught it directly would exit before this tool asked
        # it to -- recorded as "exited on its own".
        self.proc = subprocess.Popen(
            self.argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True, start_new_session=True)
        self.started = now_raw()
        for f, which in ((self.proc.stdout, "stdout"), (self.proc.stderr, "stderr")):
            fd = f.fileno()
            os.set_blocking(fd, False)
            self.fds[fd] = which
            self.buf[fd] = b""

    def read_fds(self):
        return [fd for fd in self.fds if fd not in self.eof]

    def on_read(self, fd):
        try:
            chunk = os.read(fd, 65536)
        except (BlockingIOError, InterruptedError):
            return
        # The stamp, taken once per read: every line in this chunk was
        # delivered by this read, so every one of them gets this time.
        t = now_raw()
        t_real = time.time()
        which = self.fds[fd]
        if not chunk:
            self.eof.add(fd)
            rest, self.buf[fd] = self.buf[fd], b""
            if rest:
                self._line(which, rest, t, t_real)
            if len(self.eof) == len(self.fds):
                self._reap(t)
            return
        lines = (self.buf[fd] + chunk).split(b"\n")
        self.buf[fd] = lines.pop()
        n = 0
        for ln in lines:
            n += self._line(which, ln, t, t_real)
        self.max_per_read = max(self.max_per_read, n)
        if n > 1:
            self.multi_reads += 1

    def _line(self, which, raw, t, t_real):
        text = raw.decode("utf-8", "replace").rstrip("\r")
        if which == "stderr":
            if text.strip():
                self.other["stderr"] += 1
                self.rec.comment("%.6f ping-stderr %s" % (t, text))
            return 0
        p = parse_ping_line(text)
        k = p["kind"]
        if k == "blank":
            return 0
        if k not in ("reply", "silent"):
            if k == "stats":
                self.stats = {"transmitted": p["tx"], "received": p["rx"]}
            key = "summary" if k == "stats" else k
            self.other[key] = self.other.get(key, 0) + 1
            self.rec.comment("%.6f ping-%s %s" % (t, key, text))
            return 0
        if k == "reply":
            kind = "icmp-reply"
            self.rec.event(t, kind, [("seq", p["seq"]), ("ttl", p["ttl"]),
                                     ("rtt_ms", p["rtt"]),
                                     ("ping_real", p["real"])],
                           {"seq": p["seq"]})
        else:
            kind = "icmp-silent"
            self.rec.event(t, kind, [("seq", p["seq"])], {"seq": p["seq"]})
        self.lines_icmp += 1
        lag = line_lag_ms(t_real, p["real"])
        if lag is None:
            self.no_stamp += 1
        else:
            self.lags.append(lag)
            if lag_flagged(lag, self.threshold):
                self.flagged += 1
                self.rec.comment(
                    "%.6f icmp-lag seq=%d lag_ms=%.3f threshold_ms=%g %s"
                    % (t, p["seq"], lag, self.threshold,
                       "negative: realtime stepped back, or the stamp is not "
                       "ping's" if lag < 0 else "over the threshold"))
        # The ACHIEVED interval, on the probe's clock: consecutive seqs of
        # one kind.  Two `no answer yet` lines are both printed at a send.
        prev = self.prev.get(kind)
        if prev is not None and p["seq"] == prev[0] + 1:
            self.gaps_ms.append((t - prev[1]) * 1e3)
        self.prev[kind] = (p["seq"], t)
        return 1

    def _reap(self, t):
        try:
            self.rc = self.proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            return      # its pipes are closed and it lives on; stop() ends it
        self.exited = True
        if self.stopped_by is None:
            self.exited_early = True
            self.rec.comment("%.6f ping exited on its own, rc=%d" % (t, self.rc))

    def _drain(self, budget):
        end = now_raw() + budget
        while self.read_fds():
            left = end - now_raw()
            if left <= 0:
                return
            r, _w, _x = select.select(self.read_fds(), [], [], min(left, 0.1))
            for fd in r:
                self.on_read(fd)

    def stop(self):
        if self.proc is None:
            return
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGKILL):
            if self.proc.poll() is not None:
                break
            self.stopped_by = sig.name
            try:
                self.proc.send_signal(sig)
            except ProcessLookupError:
                break
            self._drain(5.0 if sig == signal.SIGKILL else PING_STOP_GRACE_S)
        self._drain(1.0)
        if self.rc is None:
            try:
                self.rc = self.proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.rc = None
        self.exited = True
        for f in (self.proc.stdout, self.proc.stderr):
            f.close()

    def meta(self):
        return {"pid": self.proc.pid if self.proc else None, "argv": self.argv,
                "started_raw": round(self.started, 6) if self.started is not None else None,
                "achieved_interval_ms": dist(self.gaps_ms),
                "stopped_by": self.stopped_by, "rc": self.rc,
                "exited_early": self.exited_early, "statistics": self.stats,
                "icmp_lines": self.lines_icmp, "other_lines": dict(self.other),
                "no_timestamp_lines": self.no_stamp,
                "max_icmp_lines_per_read": self.max_per_read,
                "reads_with_several_icmp_lines": self.multi_reads}


class Tcp:
    """A non-blocking connect() per port every interval, each bounded."""

    def __init__(self, rec, target, ports, interval_s, timeout_s, t0):
        self.rec, self.target, self.ports = rec, target, list(ports)
        self.interval, self.timeout = interval_s, timeout_s
        self.next = {p: t0 for p in self.ports}
        self.pending = {}           # fd -> (socket, port, start: now_raw())
        self.attempts = self.aborted = 0

    def due(self):
        ts = list(self.next.values()) + [st + self.timeout
                                         for _s, _p, st in self.pending.values()]
        return min(ts)

    def write_fds(self):
        return list(self.pending)

    def tick(self, now):
        for fd, (_s, _port, st) in list(self.pending.items()):
            if now - st >= self.timeout:
                self._resolve(fd, now_raw(), "timeout", "-")
        for port in self.ports:
            if now >= self.next[port]:
                self._start(port)
                self.next[port] += self.interval
                if self.next[port] <= now:
                    self.next[port] = now + self.interval

    def _start(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        st = now_raw()
        err = s.connect_ex((self.target, port))
        self.attempts += 1
        fd = s.fileno()
        self.pending[fd] = (s, port, st)
        if err in (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK, errno.EINTR):
            return
        result, name = classify_errno(err)
        self._resolve(fd, now_raw(), result, name)

    def on_write(self, fd):
        if fd not in self.pending:
            return
        s = self.pending[fd][0]
        err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        t = now_raw()
        result, name = classify_errno(err)
        self._resolve(fd, t, result, name)

    def _resolve(self, fd, t, result, name):
        s, port, st = self.pending.pop(fd)
        try:
            s.close()
        except OSError:
            pass
        self.rec.event(t, "tcp", [("port", port), ("result", result),
                                  ("errno", name), ("start_raw", "%.6f" % st),
                                  ("dur_ms", "%.3f" % ((t - st) * 1e3))],
                       {"port": port, "result": result})

    def stop(self):
        t = now_raw()
        for _fd, (s, port, st) in list(self.pending.items()):
            self.rec.comment("%.6f tcp port=%d attempt started %.6f was still "
                             "pending at stop; no event" % (t, port, st))
            s.close()
            self.aborted += 1
        self.pending.clear()

    def meta(self):
        return {"attempts": self.attempts, "aborted_at_stop": self.aborted,
                "interval_s": self.interval, "timeout_s": self.timeout}


class Neigh:
    """`ip -4 neigh show TARGET` polled without blocking the loop."""

    def __init__(self, rec, ip_path, target, dev, interval_s, t0):
        self.rec, self.target, self.interval = rec, target, interval_s
        self.argv = [ip_path, "-4", "neigh", "show", target] + (["dev", dev] if dev else [])
        self.next = t0
        self.proc = self.fd = self.spawned = None
        self.buf = b""
        self.last = None
        self.polls = self.errors = 0
        self.poll_ms, self.spawn_times = [], []

    def due(self):
        return self.spawned + NEIGH_POLL_CAP_S if self.proc is not None else self.next

    def read_fds(self):
        return [self.fd] if self.proc is not None else []

    def tick(self, now):
        if self.proc is not None and now - self.spawned >= NEIGH_POLL_CAP_S:
            self._kill()
            self.errors += 1
            self.rec.comment("%.6f neigh-error the poll did not finish in %g s "
                             "and was killed" % (now_raw(), NEIGH_POLL_CAP_S))
        if self.proc is None and now >= self.next:
            try:
                self.proc = subprocess.Popen(
                    self.argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, close_fds=True, start_new_session=True)
            except OSError as e:
                self.errors += 1
                self.rec.comment("%.6f neigh-error %s" % (now_raw(), e))
                self.next = now + self.interval
                return
            self.spawned = now_raw()
            self.spawn_times.append(self.spawned)
            self.fd = self.proc.stdout.fileno()
            os.set_blocking(self.fd, False)
            self.buf = b""
            self.next = self.spawned + self.interval

    def on_read(self, fd):
        try:
            chunk = os.read(fd, 65536)
        except (BlockingIOError, InterruptedError):
            return
        if chunk:
            self.buf += chunk
            return
        # EOF: the table as `ip` read it, some time between spawn and now.
        # Stamped now -- an upper bound (see WHAT IT DOES NOT ESTABLISH).
        t = now_raw()
        try:
            rc = self.proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            rc = None
        text = self.buf.decode("utf-8", "replace")
        self._kill()
        self.polls += 1
        self.poll_ms.append((t - self.spawned) * 1e3)
        if rc != 0:
            self.errors += 1
            # WITHHELD, not redacted: `ip`'s output can carry an lladdr, and the
            # exit status is what a failed poll has to say (H11, A3).
            self.rec.comment("%.6f neigh-error rc=%s; the output of `ip` is withheld, "
                             "because it can carry an lladdr" % (t, rc))
            return
        state, lladdr, n = parse_neigh(text, self.target)
        if n > 1:
            self.rec.comment("%.6f neigh %d entries for %s; the first is recorded"
                             % (t, n, self.target))
        # Compared on the canonical form, so a change of case is not a change;
        # written through the redactor, so what is compared is never printed.
        key = (state, canonical_mac(lladdr) or lladdr.lower())
        if key != self.last:
            self.last = key
            self.rec.event(t, "neigh", [("state", state),
                                        ("lladdr", REDACT.address(lladdr))],
                           {"state": state})

    def _kill(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass
        try:
            self.proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            pass
        self.proc.stdout.close()
        self.proc = self.fd = None

    def stop(self):
        self._kill()

    def meta(self):
        gaps = [(b - a) * 1e3 for a, b in zip(self.spawn_times, self.spawn_times[1:])]
        return {"argv": self.argv, "interval_s": self.interval, "polls": self.polls,
                "errors": self.errors, "poll_ms": dist(self.poll_ms),
                "achieved_interval_ms": dist(gaps)}


class Udp:
    """Bound listeners: arrival, peer and length per datagram, never content."""

    def __init__(self, rec, socks):
        self.rec = rec
        self.by_fd = {s.fileno(): (s, port, ts) for port, (s, ts, _why) in socks.items()}
        self.lags = []

    def read_fds(self):
        return list(self.by_fd)

    def on_read(self, fd):
        s, port, ts = self.by_fd[fd]
        while True:
            try:
                if ts:
                    data, anc, _fl, addr = s.recvmsg(65536, socket.CMSG_SPACE(16))
                else:
                    data, anc, _fl, addr = s.recvmsg(65536)
            except (BlockingIOError, InterruptedError):
                return
            t = now_raw()
            t_real = time.time()
            n = len(data)
            del data                    # the payload is never kept
            kr = kernel_stamp(anc) if ts else None
            # 1.3: the lag goes on the line, so the kernel's realtime stamp
            # converts to this clock line by line: t - lag_ms/1000 (Q7).
            lag = (t_real - float(kr)) * 1e3 if kr is not None else None
            self.rec.event(t, "udp", [("port", port),
                                      ("peer", "%s:%d" % (addr[0], addr[1])),
                                      ("len", n), ("kernel_real", kr or "-"),
                                      ("lag_ms", "%.3f" % lag if lag is not None else "-")],
                           {"port": port})
            if lag is not None:
                self.lags.append(lag)

    def stop(self):
        # What is queued arrived before the stop; record it, with its true
        # read time.
        for fd in list(self.by_fd):
            self.on_read(fd)


class Ctx:
    pass


def refuse_args(a):
    """Every refusal that reads nothing but the parsed arguments.  -> Ctx.

    `FW-124`: no file, environment variable, network, port, device, host
    version or clock is read here, so a card's HOST cell can be checked with
    build_parser() and this, in-process, and reach the verdict the run would
    (V1 poisons all of those and expects the same verdicts).  main() runs it
    before anything reads the host (V2); preflight() runs it again after the
    allowlist, to take the values it derives.  Only `run` has arguments to
    refuse; `report`'s prefix is a file, which is the environment.
    """
    c = Ctx()
    if getattr(a, "self_test", False) or getattr(a, "cmd", None) != "run":
        return c
    # The terminator first: its absence is the defect that leaves a process
    # running (console-capture `_check_terminator`, the same reasoning).
    if a.seconds is None:
        raise Refused(
            "--seconds N is required, and also with --until: a pattern that "
            "never arrives must not leave the probe, and the ping it drives, "
            "running forever")
    if not a.seconds > 0 or a.seconds == float("inf"):
        raise Refused("--seconds %r: the cap must be a positive, finite number "
                      "of seconds" % a.seconds)
    if not (a.icmp or a.tcp or a.neigh or a.udp_listen):
        raise Refused(
            "no probe selected: pass at least one of --icmp, --tcp PORT, --neigh, "
            "--udp-listen PORT. A run that watches nothing would print `none` "
            "for every kind, which reads as a finding")
    try:
        ip = ipaddress.IPv4Address(a.target)
    except ValueError:
        raise Refused("--target %r is not an IPv4 literal (a.b.c.d). A name "
                      "would be resolved by whatever resolver this host has "
                      "today; the card names an address" % a.target) from None
    if ip.is_multicast or ip.is_unspecified or ip == ipaddress.IPv4Address("255.255.255.255"):
        raise Refused("--target %s is not a unicast host address" % a.target)
    c.loopback = ip.is_loopback
    for name in ("icmp_interval", "tcp_interval", "tcp_timeout",
                 "neigh_interval", "lag_threshold_ms"):
        v = getattr(a, name)
        if not v > 0 or v == float("inf"):
            raise Refused("--%s %r must be a positive, finite number"
                          % (name.replace("_", "-"), v))
    for p in a.tcp:
        if not 1 <= p <= 65535:
            raise Refused("--tcp %d is not a port number (1-65535)" % p)
    if len(set(a.tcp)) != len(a.tcp):
        raise Refused("--tcp names a port twice")
    for p in a.udp_listen:
        if not 1 <= p <= 65535:
            raise Refused("--udp-listen %d is not a port number (1-65535)" % p)
        if p < 1024:
            raise Refused(
                "--udp-listen %d is a privileged port (below 1024). Binding it "
                "needs root or CAP_NET_BIND_SERVICE, and this tool runs "
                "unprivileged and changes no system setting (FW-114); a card can "
                "send to any port >= 1024" % p)
    if len(set(a.udp_listen)) != len(a.udp_listen):
        raise Refused("--udp-listen names a port twice")
    c.until = [parse_until(s, a.icmp, a.tcp, a.neigh, a.udp_listen) for s in a.until]
    if not a.out or a.out.endswith(("/", os.sep)):
        raise Refused("--out %r must be a path prefix, not a directory" % a.out)
    # ping truncates -i to whole milliseconds on every release; the floor
    # depends on the release, which is the host's, so it stays in preflight
    # (check_icmp_interval, which applies both halves).
    if a.icmp:
        icmp_whole_ms(a.icmp_interval)
    return c


def preflight(a):
    """Every refusal, in order, before any file or child exists.  -> Ctx."""
    # The allowlist FIRST, so every message below -- a host-fault refusal
    # quotes a route whose `dev` can be an `enx<12 hex>` name -- is rendered
    # through it.  Unavailable: --neigh is refused, never run on a fallback
    # (H11, A7-A9); any other probe labels every address it meets (A10).
    why_not = use_allowlist()
    if why_not and a.neigh:
        raise Refused(
            "--neigh needs the address allowlist, and %s. Refusing rather than "
            "writing lladdr values it cannot check: in P2-3 the address that "
            "answers for the target is this unit's own, from H601" % why_not)
    # The argument refusals (FW-124).  main() has run them already, before
    # anything read the host; this pass takes the values they derive, and
    # keeps this function's promise -- every refusal -- on its own.
    c = refuse_args(a)
    c.events = a.out + ".events"
    c.meta = a.out + ".meta.json"
    if not a.force:
        for p in (c.events, c.meta):
            if os.path.exists(p):
                raise Refused("%s exists. Refusing to overwrite a record; use a "
                              "new --out, or --force" % p)
    c.ping = None
    if a.icmp:
        path = _which(a.ping)
        if not path:
            raise Refused("--icmp: no executable ping at %r" % a.ping)
        try:
            pv = subprocess.run([path, "-V"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=5)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise Refused("--icmp: `%s -V` failed: %s" % (path, e)) from None
        text = pv.stdout.decode("utf-8", "replace")
        release = parse_ping_version(text)
        if pv.returncode != 0 or release is None:
            raise Refused(
                "--icmp: `%s -V` exited %d and printed %r, which is not iputils. "
                "The parser is written against iputils' format strings "
                "(-D stamps, -O lines); another ping's output would read as "
                "silence" % (path, pv.returncode, " ".join(text.split())[:80]))
        ms = check_icmp_interval(a.icmp_interval, release)
        c.ping = {"path": path, "version": text.strip().splitlines()[0],
                  "release": release, "interval_s": a.icmp_interval,
                  "interval_ms_effective": ms}
    c.ip_path = c.dev = c.src = None
    if a.neigh or not c.loopback:
        c.ip_path = _which(a.ip)
        if not c.ip_path:
            raise Refused("no executable `ip` at %r (iproute2): %s needs it"
                          % (a.ip, "--neigh" if a.neigh else "the route check"))
    if not c.loopback:
        try:
            pr = subprocess.run([c.ip_path, "-4", "route", "get", a.target],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=5)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise Refused("`ip -4 route get %s` failed: %s" % (a.target, e)) from None
        ok, dev, src, why = route_verdict(a.target, pr.returncode,
                                          pr.stdout.decode("utf-8", "replace"))
        if not ok:
            raise Refused(why)
        c.dev, c.src = dev, src
    # Last, because it is the one step that holds a resource: a refusal above
    # leaves nothing bound.
    c.udp = {}
    try:
        for port in a.udp_listen:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.bind(("0.0.0.0", port))
            except OSError as e:
                s.close()
                raise Refused("--udp-listen %d: cannot bind 0.0.0.0:%d: %s"
                              % (port, port, e.strerror or e)) from None
            s.setblocking(False)
            ts, why = enable_rx_stamp(s)
            c.udp[port] = (s, ts, why)
    except Refused:
        for s, _ts, _why in c.udp.values():
            s.close()
        raise
    return c


def probes_comment(a):
    return ("probes target=%s icmp=%s tcp=%s neigh=%s udp=%s seconds=%g until=%s"
            % (a.target, ("%g" % a.icmp_interval) if a.icmp else "-",
               ",".join(str(p) for p in a.tcp) or "-",
               ("%g" % a.neigh_interval) if a.neigh else "-",
               ",".join(str(p) for p in a.udp_listen) or "-",
               a.seconds, ",".join(a.until) or "-"))


def run(a):
    c = preflight(a)
    # Signals before files: from the moment the record exists, SIGINT, SIGTERM
    # and SIGHUP end the run through the same shutdown as --seconds.  The
    # wakeup pipe is what makes that prompt -- select() is restarted after a
    # handler returns (PEP 475), and without a byte to read it would sleep on.
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_r, False)
    os.set_blocking(wake_w, False)
    seen = []

    def on_signal(signum, _frame):
        seen.append(signal.Signals(signum).name)

    old_wakeup = signal.set_wakeup_fd(wake_w, warn_on_full_buffer=False)
    old = {}
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        old[sig] = signal.signal(sig, on_signal)
    try:
        return _run(a, c, wake_r, seen)
    finally:
        for sig, h in old.items():
            signal.signal(sig, h)
        signal.set_wakeup_fd(old_wakeup)
        os.close(wake_r)
        os.close(wake_w)
        for s, _ts, _why in c.udp.values():
            try:
                s.close()
            except OSError:
                pass


def _run(a, c, wake_r, seen):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(c.events)) or ".", exist_ok=True)
        if a.force:
            for p in (c.meta, c.meta + ".tmp"):
                if os.path.exists(p):
                    os.remove(p)
        rec = Recorder(c.events, a.force, c.until,
                       first_key_order(a.icmp, a.tcp, a.neigh, a.udp_listen),
                       count_kinds(a.icmp, a.tcp, a.neigh, a.udp_listen))
    except FileExistsError:
        raise Refused("%s appeared after the pre-flight; refusing to overwrite it"
                      % c.events) from None
    except OSError as e:
        raise Refused("cannot create %s: %s" % (c.events, e)) from None

    # The boot the RAW stamps count from and the kernel's clocksource, read
    # before the origin; then RAW, realtime and MONOTONIC back to back.
    boot_id = boot_id_value(read_line_file(BOOT_ID_PATH))
    clocksource = read_line_file(CLOCKSOURCE_PATH)
    t0 = now_raw()
    r0 = time.time()
    m0 = now_mono()
    rec.comment(HEADER)
    rec.comment(probes_comment(a))
    rec.event(t0, "start", [("t_real", "%.6f" % r0)])
    problems = []
    icmp = tcp = neigh = udp = None
    reason = None
    t_stop = None
    try:
        if a.icmp:
            icmp = Icmp(rec, c.ping["path"], a.target, a.icmp_interval,
                        a.lag_threshold_ms)
            icmp.start()
        if a.tcp:
            tcp = Tcp(rec, a.target, a.tcp, a.tcp_interval, a.tcp_timeout, t0)
        if a.neigh:
            neigh = Neigh(rec, c.ip_path, a.target, c.dev, a.neigh_interval, t0)
        if c.udp:
            udp = Udp(rec, c.udp)
        deadline = t0 + a.seconds
        while True:
            now = now_raw()
            # A signal is the operator; --until is tested before --seconds,
            # because a run whose event arrived in the window its cap expired
            # in HAS seen its event (console-capture's N35, the same rule).
            if seen:
                reason = seen[0]
                break
            if rec.until_hit:
                reason = "--until=" + rec.until_hit
                break
            if icmp and icmp.exited and not (tcp or neigh or udp):
                reason = "ping-exited"
                break
            if now >= deadline:
                reason = "--seconds"
                break
            if tcp:
                tcp.tick(now)
            if neigh:
                neigh.tick(now)
            if rec.until_hit:
                continue
            due = [deadline] + ([tcp.due()] if tcp else []) + ([neigh.due()] if neigh else [])
            # A RAW deadline, a kernel wait: select() runs on CLOCK_MONOTONIC,
            # so the wait is capped and the next pass re-reads RAW (ONE CLOCK).
            wait = max(0.0, min(min(due) - now_raw(), 0.25))
            rl = [wake_r] + (icmp.read_fds() if icmp else []) \
                + (neigh.read_fds() if neigh else []) + (udp.read_fds() if udp else [])
            wl = tcp.write_fds() if tcp else []
            r, w, _x = select.select(rl, wl, [], wait)
            for fd in r:
                if fd == wake_r:
                    try:
                        os.read(wake_r, 512)
                    except (BlockingIOError, InterruptedError):
                        pass
                elif icmp and fd in icmp.fds:
                    icmp.on_read(fd)
                elif neigh and fd in neigh.read_fds():
                    neigh.on_read(fd)
                elif udp and fd in udp.by_fd:
                    udp.on_read(fd)
            for fd in w:
                tcp.on_write(fd)
        t_stop = now_raw()
    except Exception as e:
        # A defect in this file must not cost the record or leave ping behind.
        t_stop = now_raw()
        reason = "internal-error"
        problems.append("internal error: %s" % _exc_line(e))
    rec.armed = False
    for probe in (icmp, neigh, tcp, udp):
        if probe is not None:
            try:
                probe.stop()
            except Exception as e:
                problems.append("stopping %s: %s" % (type(probe).__name__, _exc_line(e)))
    end_raw = now_raw()
    end_real = time.time()
    m1 = now_mono()
    clocksource_end = read_line_file(CLOCKSOURCE_PATH)
    rec.event(end_raw, "stop", [("t_real", "%.6f" % end_real), ("reason", reason)])
    rec.close()

    ping_meta = None
    lag = {"n": 0, "median": None, "max": None, "min": None, "over_threshold": 0,
           "threshold_ms": a.lag_threshold_ms}
    if icmp is not None:
        ping_meta = dict(c.ping)
        ping_meta.update(icmp.meta())
        d = dist(icmp.lags)
        lag.update({"n": d["n"], "median": d["median"], "max": d["max"],
                    "min": d["min"], "over_threshold": icmp.flagged})
        agree = None
        if icmp.exited_early:
            problems.append("ping exited on its own (rc=%s) during the run"
                            % icmp.rc)
        ran = t_stop - icmp.started if icmp.started is not None else 0.0
        if icmp.started is None:
            problems.append("ping could not be started: %s" % " ".join(icmp.argv))
        elif icmp.lines_icmp == 0 and ran > ICMP_SILENCE_STARTUP_S + 2 * a.icmp_interval:
            problems.append(
                "H2: ping printed no reply and no `no answer yet` line in %.3f s. "
                "With -O a working ping prints one per interval, so this is the "
                "instrument, not the target" % ran)
        if icmp.stopped_by not in (None, "SIGINT"):
            problems.append("ping did not exit on SIGINT and was stopped with %s"
                            % icmp.stopped_by)
        if icmp.stats is not None:
            want = rec.counts.get("icmp-reply", 0) + icmp.other["truncated"]
            agree = icmp.stats["received"] == want
            if not agree:
                problems.append(
                    "H3: ping's statistics say %d received; the probe recorded %d "
                    "icmp-reply and %d truncated. The parser missed or invented "
                    "a reply" % (icmp.stats["received"],
                                 rec.counts.get("icmp-reply", 0),
                                 icmp.other["truncated"]))
        elif icmp.stopped_by == "SIGINT":
            problems.append("ping exited on SIGINT without printing its "
                            "statistics, so H3 could not be checked")
        ping_meta["statistics_agree"] = agree
    if neigh is not None and neigh.errors:
        # A failed poll is a gap in the neighbour column, not a NONE: the table
        # was not read.  Without this a broken `ip` reads as "no entry".
        problems.append("neigh: %d poll(s) failed (%d completed); see the "
                        "neigh-error comments" % (neigh.errors, neigh.polls))
    exit_code = 1 if problems else 0
    meta = {
        "tool": "hostprobe", "tool_version": TOOL_VERSION, "clock": CLOCK,
        "target": a.target,
        "args": {k: v for k, v in vars(a).items() if k not in ("cmd", "self_test")},
        "start_raw": round(t0, 6), "start_real": round(r0, 6),
        # 1.2: console-capture's field, in its format, from the SAME time.time()
        # reading as start_real -- capdate dates every .meta.json in a bench
        # directory by it (its D7/D8), and a record without it is RED there.
        "started_wallclock": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                           time.localtime(r0)),
        "end_raw": round(end_raw, 6), "end_real": round(end_real, 6),
        "stop_decided_raw": round(t_stop, 6),
        # 1.3: one CLOCK_MONOTONIC reading beside each end's RAW reading, so
        # the record carries its own MONOTONIC/RAW ratio (Q2); the boot the
        # RAW stamps count from; the kernel's clocksource at each end (Q6).
        "mono_at_start": round(m0, 6), "mono_at_end": round(m1, 6),
        "boot_id": None,            # set after the redactor: see below
        "clocksource": clocksource, "clocksource_end": clocksource_end,
        "ping": ping_meta,
        "icmp_lag_ms": lag,
        "udp_lag_ms": dist(udp.lags) if udp else dist([]),
        "tcp": tcp.meta() if tcp else None,
        "neigh": neigh.meta() if neigh else None,
        "udp": ({str(p): {"so_timestampns": ts, "why_not": why}
                 for p, (_s, ts, why) in c.udp.items()} if c.udp else None),
        "route": {"dev": c.dev, "src": c.src} if not c.loopback else None,
        "counts": rec.counts, "first": rec.first,
        "stop_reason": reason, "problems": problems, "exit_code": exit_code,
        "addresses": {"allowlist": _rel(ABL_PATH), "loaded": REDACT.loaded,
                      "allowlisted": len(REDACT.allowed),
                      "why_not": REDACT.why_not or None, "unlisted": None},
    }
    # Every string in the meta, keys included, through the redactor: the
    # route's `dev`, the neigh argv, the args, a problem's text (H11, A5).
    meta = REDACT.obj(meta)
    meta["addresses"]["unlisted"] = len(REDACT.labels)
    # boot_id alone skips the redactor, and only as a version-4 UUID.
    # MAC_TEXT_RX labels any twelve hex digits between non-hex, which a UUID's
    # last group is (量 2026-09-23: this host's boot_id came out
    # `<first four groups>-unlisted-1`), and a mangled boot_id never equals
    # console-capture's, so the join would refuse every pair.  A version-4
    # UUID's last group is random bits; a version-1 UUID's is a node address,
    # and boot_id_value() withholds that and anything else as null (Q6).
    meta["boot_id"] = boot_id
    tmp = c.meta + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    os.replace(tmp, c.meta)
    n_events = sum(rec.counts.values())
    say("hostprobe: %s  %d events, stop %s after %.3f s"
        % (c.events, n_events, reason, end_raw - t0))
    say("hostprobe: %s" % c.meta)
    for p in meta["problems"]:
        say("hostprobe: PROBLEM %s" % p, err=True)
    return exit_code


# ------------------------------------------------------------------ report
def load_record(prefix):
    """(events, comments, bad, meta, (clock, how)).
    events: [(t, kind, fields, raw)].

    The clock is the one the header declares (header_clock, a whole token),
    and every event line is read against that clock's keys.  A record whose
    header declares no clock (no version of this tool wrote one) is read on
    the meta's clock, or else on CLOCK_MONOTONIC, the clock of every record
    before 1.3; `how` says which, and `report` prints it.  A header the meta
    contradicts, or a clock no version writes, is MALFORMED (H13).
    """
    path = prefix + ".events"
    if not os.path.exists(path):
        raise Refused("%s not found" % path)
    events, comments, bad = [], [], []
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    elif lines:
        bad.append((len(lines), "the last line has no newline: cut off mid-write"))
    meta = None
    if os.path.exists(prefix + ".meta.json"):
        try:
            with open(prefix + ".meta.json", encoding="utf-8") as f:
                meta = json.load(f)
        except ValueError as e:
            bad.append((0, "meta unreadable: %s" % e))
    declared = header_clock(lines[0]) if lines else None
    mclock = meta.get("clock") if isinstance(meta, dict) else None
    if mclock is not None and mclock not in EVENT_KEYS_BY_CLOCK:
        bad.append((0, "the meta's clock %r is not one a hostprobe version writes"
                    % (mclock,)))
    if declared is not None:
        clock, how = declared, "declared by the header"
        if declared not in EVENT_KEYS_BY_CLOCK:
            bad.append((1, "the header declares %s, which no hostprobe version "
                        "writes" % declared))
        elif mclock is not None and mclock != declared:
            bad.append((1, "the header declares %s and the meta's clock is %r: "
                        "one record, two clocks" % (declared, mclock)))
    elif mclock in EVENT_KEYS_BY_CLOCK:
        clock, how = mclock, "the meta's; the header declares none"
    else:
        clock, how = CLOCK_LEGACY, ("presumed: the header declares none and no meta "
                                    "does, and every record before 1.3 was on it")
    for n, line in enumerate(lines, 1):
        if line.startswith("#"):
            comments.append(line)
            continue
        try:
            t, kind, fields = parse_event_line(line, clock)
        except ValueError as e:
            bad.append((n, str(e)))
            continue
        events.append((t, kind, fields, line))
    return events, comments, bad, meta, (clock, how)


def _probes_from(comments):
    for c in comments:
        m = PROBES_RX.match(c)
        if m:
            d = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
            ints = lambda s: [int(x) for x in s.split(",")] if s and s != "-" else []
            return {"icmp": d.get("icmp", "-") != "-", "tcp": ints(d.get("tcp")),
                    "neigh": d.get("neigh", "-") != "-", "udp": ints(d.get("udp"))}
    return None


def report(prefix, out=sys.stdout):
    # A record this version wrote holds no unlisted address; one written by
    # 1.0, or edited by hand, can.  So `report` prints through the same gate,
    # and without the allowlist it labels every address rather than refusing.
    why_not = use_allowlist()
    events, comments, bad, meta, (clock, how) = load_record(prefix)

    def pr(s=""):
        print(REDACT.text(s), file=out)

    pr("hostprobe report %s" % prefix)
    pr("  allowlist %s" % ("%d address(es) from %s" % (len(REDACT.allowed), _rel(ABL_PATH))
                           if not why_not else "NOT LOADED, so every address is "
                           "printed as a label: %s" % why_not))
    pr("  clock  %s, %s" % (clock, how))
    start = next((e for e in events if e[1] == "start"), None)
    stop = next((e for e in events if e[1] == "stop"), None)
    t0 = start[0] if start else (events[0][0] if events else None)
    probes = _probes_from(comments)
    if meta is not None:
        keys = list(meta.get("first", {}))
        kinds = [k for k in meta.get("counts", {}) if k not in ("start", "stop")]
        pr("  target %s  stop %s  exit_code %s" % (meta.get("target"),
                                                   meta.get("stop_reason"),
                                                   meta.get("exit_code")))
    elif probes is not None:
        keys = first_key_order(probes["icmp"], probes["tcp"], probes["neigh"], probes["udp"])
        kinds = count_kinds(probes["icmp"], probes["tcp"], probes["neigh"], probes["udp"])
        pr("  no meta: the run did not end cleanly (killed?); read from the "
           "events file alone")
    else:
        keys, kinds = [], []
        pr("  no meta and no probes line: only the kinds that occurred are listed")
    firsts, counts = {}, {}
    for t, kind, f, _raw in events:
        if kind in ("start", "stop"):
            continue
        counts[kind] = counts.get(kind, 0) + 1
        for key in event_first_keys(kind, f):
            firsts.setdefault(key, (t, kind, f))
    for key in sorted(k for k in firsts if k not in keys):
        keys.append(key)
    for kind in sorted(k for k in counts if k not in kinds):
        kinds.append(kind)
    if stop is not None and start is not None:
        dm = stop[0] - start[0]
        drift_ms = ((float(stop[2]["t_real"]) - float(start[2]["t_real"])) - dm) * 1e3
        pr("  run    %.6f s on %s, from %.6f; stop %s"
           % (dm, clock, start[0], stop[2]["reason"]))
        pr("  drift  realtime minus %s over the run: %+.3f ms (%+.1f ppm)"
           % (clock, drift_ms, drift_ms / 1e3 / dm * 1e6 if dm > 0 else 0.0))
    else:
        pr("  drift  unknown: no stop line, so the run did not end cleanly")
    for key in keys:
        if key not in firsts:
            pr("  first  %-24s none" % key)
            continue
        t, kind, f = firsts[key]
        pr("  first  %-24s %.6f  %+.6f  %s"
           % (key, t, t - t0 if t0 is not None else 0.0,
              " ".join("%s=%s" % kv for kv in f.items())))
        if meta is not None and key in meta.get("first", {}):
            mt = meta["first"][key]
            if mt is None or abs(mt - t) > 2e-6:
                pr("  WARNING first %s: the meta says %s, the events say %.6f"
                   % (key, mt, t))
    for kind in kinds:
        n = counts.get(kind, 0)
        pr("  count  %-24s %s" % (kind, n if n else "none"))
    if meta is not None:
        for name in ("icmp_lag_ms", "udp_lag_ms"):
            d = meta.get(name) or {}
            label = name[:-3].replace("_", "-")
            if not d.get("n"):
                pr("  %-8s none" % label)
                continue
            extra = ("  over_threshold=%s threshold_ms=%s"
                     % (d.get("over_threshold"), d.get("threshold_ms"))
                     if name == "icmp_lag_ms" else "")
            pr("  %-8s n=%d median=%.3f min=%.3f max=%.3f ms%s"
               % (label, d["n"], d["median"], d["min"], d["max"], extra))
        pg = meta.get("ping") or {}
        ai = pg.get("achieved_interval_ms") or {}
        if pg:
            pr("  ping   %s, -i %s (%s ms), achieved %s"
               % (pg.get("version"), pg.get("interval_s"),
                  pg.get("interval_ms_effective"),
                  "median %.3f ms over %d gaps" % (ai["median"], ai["n"])
                  if ai.get("n") else "none"))
        for p in meta.get("problems", []):
            pr("  problem %s" % p)
    else:
        pr("  icmp-lag unknown: no meta")
    for n, why in bad:
        pr("  MALFORMED line %d: %s" % (n, why))
    return 1 if bad else 0


# --------------------------------------------------------------- self-test
FAKE_PING = r'''
import json, os, signal, sys, time
if sys.argv[1:] == ["-V"]:
    sys.stdout.write(os.environ.get("HP_FAKE_PING_V", "ping from iputils 20240117\n"))
    sys.exit(0)
cfg = json.load(open(os.environ["HP_FAKE_PING_CFG"]))
signal.signal(signal.SIGPIPE, signal.SIG_DFL)    # what a real ping has
with open(cfg["pidfile"], "w") as f:
    f.write("%d %d %d" % (os.getpid(), os.getsid(0), os.getpgrp()))
with open(cfg["argvfile"], "w") as f:
    json.dump(sys.argv[1:], f)
got = {"rx": 0}
def stats(_s, _f):
    sys.stdout.write("\n--- %s ping statistics ---\n" % sys.argv[-1])
    sys.stdout.write("%d packets transmitted, %d received, 0%% packet loss, time 9ms\n"
                     % (len(cfg["lines"]), got["rx"] + cfg.get("rx_bias", 0)))
    sys.stdout.flush()
    os._exit(0)
if cfg.get("deaf"):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
else:
    signal.signal(signal.SIGINT, stats)
sys.stdout.write((cfg.get("header") or "PING %s (%s) 56(84) bytes of data."
                  % (sys.argv[-1], sys.argv[-1])) + "\n")
sys.stdout.flush()
for s in cfg.get("stderr_lines", []):
    sys.stderr.write(s + "\n")
sys.stderr.flush()
rec = open(cfg["record"], "w")
for step in cfg["lines"]:
    time.sleep(step.get("delay", 0.0))
    real = "%.6f" % (time.time() - step.get("lag", 0.0))
    text = step["text"].replace("{real}", real)
    sys.stdout.write(text + "\n")
    sys.stdout.flush()
    got["rx"] += step.get("rx", 0)
    rec.write(json.dumps({"text": text, "real": real}) + "\n")
    rec.flush()
if cfg.get("exit_rc") is not None:
    sys.exit(cfg["exit_rc"])
seq = 1000
while True:
    time.sleep(cfg.get("idle_every", 0.05))
    if cfg.get("idle_lines"):
        sys.stdout.write("[%.6f] no answer yet for icmp_seq=%d\n" % (time.time(), seq))
        sys.stdout.flush()
        seq += 1
'''

FAKE_IP = r'''
import json, os, sys
cfg = json.load(open(os.environ["HP_FAKE_IP_CFG"]))
args = sys.argv[1:]
with open(cfg["argvlog"], "a") as f:
    f.write(json.dumps({"args": args, "pid": os.getpid(), "sid": os.getsid(0)}) + "\n")
if args[:3] == ["-4", "route", "get"]:
    sys.stdout.write(cfg.get("route", ""))
    sys.exit(cfg.get("route_rc", 0))
if args[:3] == ["-4", "neigh", "show"]:
    n = 0
    if os.path.exists(cfg["counter"]):
        n = int(open(cfg["counter"]).read() or 0)
    with open(cfg["counter"], "w") as f:
        f.write(str(n + 1))
    seq = cfg.get("neigh") or [""]
    item = seq[min(n, len(seq) - 1)]
    text, rc = (item, cfg.get("neigh_rc", 0)) if isinstance(item, str) else item
    sys.stdout.write(text)
    sys.exit(rc)
sys.exit(127)
'''

REQUIRED_META = ("tool", "tool_version", "clock", "target", "args", "start_raw",
                 "start_real", "started_wallclock", "end_raw", "end_real",
                 "stop_decided_raw", "mono_at_start", "mono_at_end", "boot_id",
                 "clocksource", "clocksource_end", "ping", "icmp_lag_ms",
                 "counts", "first", "stop_reason")
REQUIRED_PING = ("path", "version", "interval_s", "started_raw")
REQUIRED_LAG = ("n", "median", "max", "over_threshold")
LAG_COMMENT_RX = re.compile(r"icmp-lag seq=(\d+) lag_ms=(-?\d+\.\d+)")


def _alive(pid):
    """False for no process and for a zombie; /proc is Linux's."""
    if not pid:
        return False
    try:
        with open("/proc/%d/stat" % pid) as f:
            st = f.read()
    except OSError:
        return False
    return st.rsplit(")", 1)[1].split()[0] not in ("Z", "X")


def _brief(v, n=70):
    s = repr(v)
    return s if len(s) <= n else s[:n - 3] + "..."


def selftest(out=sys.stdout):
    print("hostprobe %s --self-test" % TOOL_VERSION, file=out)
    passed = failed = 0
    ran = []

    def ck(cid, label, expect, got):
        nonlocal passed, failed
        ran.append(cid)
        if expect == got:
            passed += 1
            print("  ok     %-4s %-62s %s" % (cid, label, _brief(got)), file=out)
        else:
            failed += 1
            print("  FAIL   %-4s %-62s expected %s, got %s"
                  % (cid, label, _brief(expect), _brief(got)), file=out)

    def raises(fn, *args):
        try:
            return fn(*args)
        except Refused:
            return "R"

    # ---------------- U: the pure parts, no process, no socket
    r = parse_ping_line("[1727000000.123456] 64 bytes from 127.0.0.1: "
                        "icmp_seq=3 ttl=64 time=0.045 ms")
    ck("U1", "a -D reply line -> seq, ttl, rtt, ping_real exactly",
       ("reply", 3, 64, "0.045", "1727000000.123456"),
       (r["kind"], r.get("seq"), r.get("ttl"), r.get("rtt"), r.get("real")))
    r = parse_ping_line("[1727000000.500000] no answer yet for icmp_seq=4")
    ck("U2", "a -O `no answer yet` line -> silent, its seq and stamp",
       ("silent", 4, "1727000000.500000"), (r["kind"], r.get("seq"), r.get("real")))
    ck("U3", "DUP, truncated, From-error, header, stats, summary, junk: no reply",
       ("dup", "truncated", "error", "header", "stats", "summary", "summary", "other"),
       tuple(parse_ping_line(s)["kind"] for s in (
           "[1.000000] 64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.045 ms (DUP!)",
           "[1.000000] 64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 (truncated)",
           "[1.000000] From 10.1.1.2 icmp_seq=5 Destination Host Unreachable",
           "PING 10.1.1.1 (10.1.1.1) 56(84) bytes of data.",
           "3 packets transmitted, 2 received, 33.3333% packet loss, time 2003ms",
           "--- 10.1.1.1 ping statistics ---",
           "rtt min/avg/max/mdev = 0.100/0.200/0.300/0.100 ms",
           "garbage")))
    ck("U4", "a reply with no -D stamp -> ping_real `-`, never a number", "-",
       parse_ping_line("64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.1 ms")["real"])
    ck("U5", "errno table: ok, refused, timeout, unreachable x2, error",
       ("ok", "refused", "timeout", "unreachable", "unreachable", "error"),
       tuple(classify_errno(e)[0] for e in (0, errno.ECONNREFUSED, errno.ETIMEDOUT,
                                            errno.EHOSTUNREACH, errno.ENETUNREACH,
                                            errno.EACCES)))
    mac = "00:11:22:33:44:55"
    ck("U6", "neigh: none, dev form, dev-filtered form, FAILED, 10.1.1.10 != 10.1.1.1",
       (("NONE", "-", 0), ("REACHABLE", mac, 1), ("STALE", mac, 1),
        ("FAILED", "-", 1), ("NONE", "-", 0)),
       (parse_neigh("", "10.1.1.1"),
        parse_neigh("10.1.1.1 dev eth4 lladdr %s REACHABLE \n" % mac, "10.1.1.1"),
        parse_neigh("10.1.1.1 lladdr %s STALE \n" % mac, "10.1.1.1"),
        parse_neigh("10.1.1.1 dev eth4  FAILED \n", "10.1.1.1"),
        parse_neigh("10.1.1.10 dev eth4 lladdr %s REACHABLE\n" % mac, "10.1.1.1")))
    verdicts = (
        route_verdict("10.1.1.1", 0, "10.1.1.1 dev eth4 src 10.1.1.2 uid 1000 \n    cache \n"),
        route_verdict("10.1.1.1", 0, "10.1.1.1 dev eth4 uid 1000 \n    cache \n"),
        route_verdict("10.1.1.255", 0, "broadcast 10.1.1.255 dev eth4 src 10.1.1.2 uid 1000\n"),
        route_verdict("10.1.1.2", 0, "local 10.1.1.2 dev lo table local src 10.1.1.2 uid 1000\n"),
        route_verdict("10.9.9.9", 2, "RTNETLINK answers: Network is unreachable\n"))
    ck("U7", "route: src passes; no src, broadcast, own address, rc!=0 refuse",
       ((True, "eth4", "10.1.1.2"), False, False, False, False),
       (verdicts[0][:3],) + tuple(v[0] for v in verdicts[1:]))
    ck("U7b", "and the no-src refusal names the host, not the board", True,
       "HOST FAULT" in verdicts[1][3])
    ck("U8", "until: four satisfiable specs parse",
       (("icmp-reply",), ("tcp", "80", "ok"), ("udp",), ("neigh", "REACHABLE")),
       (parse_until("icmp-reply", True, [], False, []),
        parse_until("tcp:80:ok", False, [80], False, []),
        parse_until("udp", False, [], False, [5000]),
        parse_until("neigh:REACHABLE", False, [], True, [])))
    ck("U8b", "until: six that can never fire are refused",
       ("R",) * 6,
       tuple(raises(parse_until, *args) for args in (
           ("tcp:81:ok", False, [80], False, []), ("udp", False, [], False, []),
           ("icmp-reply", False, [80], False, []), ("tcp:80:maybe", False, [80], False, []),
           ("bogus", True, [80], True, [5000]), ("neigh:HAPPY", False, [], True, []))))
    u = ("tcp", "80", "ok")
    ck("U9", "until tcp:80:ok fires on ok@80, not refused@80, not ok@81",
       (True, False, False, True, False),
       (until_matches(u, "tcp", {"port": 80, "result": "ok"}),
        until_matches(u, "tcp", {"port": 80, "result": "refused"}),
        until_matches(u, "tcp", {"port": 81, "result": "ok"}),
        until_matches(("udp",), "udp", {"port": 5000}),
        until_matches(("icmp-reply",), "icmp-silent", {})))
    ck("U10", "lag flag at 1 ms: 0.4 no, 1.0 no, 1.001 yes, -0.0005 no, -0.5 yes",
       (False, False, True, False, True),
       tuple(lag_flagged(v, 1.0) for v in (0.4, 1.0, 1.001, -0.0005, -0.5)))
    ck("U11", "ping -V: 2024 form, 2018 form, busybox, empty",
       (20240117, 20180629, None, None),
       tuple(parse_ping_version(s) for s in (
           "ping from iputils 20240117\nlibcap: yes, IDN: yes\n",
           "ping utility, iputils-s20180629\n",
           "BusyBox v1.36.1 (Ubuntu 1:1.36.1-6ubuntu3) multi-call binary.\n", "")))
    ck("U12", "-i: 2 ms and 200 ms pass on 20240117; 1 ms, 2.9 ms refused; 0.1 s "
              "refused and 0.2 s passes on an unmeasured release",
       (2, 200, "R", "R", "R", 200),
       (raises(check_icmp_interval, 0.002, 20240117),
        raises(check_icmp_interval, 0.2, 20240117),
        raises(check_icmp_interval, 0.001, 20240117),
        raises(check_icmp_interval, 0.0029, 20240117),
        raises(check_icmp_interval, 0.1, 20180629),
        raises(check_icmp_interval, 0.2, 20180629)))

    def rejects(line, clock=CLOCK_LEGACY):
        try:
            parse_event_line(line, clock)
            return False
        except ValueError:
            return True
    good = "12.345678 tcp port=80 result=ok errno=0 start_mono=12.300000 dur_ms=45.678"
    ck("U13", "event parser: a good line and a round trip parse; four bad lines "
              "are rejected",
       (True, True, (True, True, True, True)),
       (parse_event_line(good, CLOCK_LEGACY)[1:] == (
           "tcp", {"port": "80", "result": "ok", "errno": "0",
                   "start_mono": "12.300000", "dur_ms": "45.678"}),
        parse_event_line(fmt_event(1.5, "neigh", [("state", "NONE"), ("lladdr", "-")]),
                         CLOCK)
        == (1.5, "neigh", {"state": "NONE", "lladdr": "-"}),
        tuple(rejects(s) for s in (
            good.replace("12.345678", "12.34", 1),
            "12.345678 icmp-reply seq=1 ttl=64",
            "12.345678 bogus x=1",
            "12.345678 udp port=1 peer=a b len=1 kernel_real=-"))))
    # The header every version before 1.3 wrote, verbatim (git show
    # 68f7fe8 and 66ddb93: 1.0 and 1.2 carry the same text).
    header_12 = ("# hostprobe 1.2: t_mono is absolute CLOCK_MONOTONIC seconds "
                 "(time.monotonic(), the clock console-capture's t0_mono is read "
                 "on); t_real, ping_real and kernel_real are CLOCK_REALTIME, "
                 "cross-checks only")
    ck("U14", "the header's clock is the whole token after `is absolute`: 1.2's -> "
              "MONOTONIC, 1.3's -> RAW, RAW named in passing -> MONOTONIC, a RAWX "
              "token -> RAWX, no declaration or no `#` -> none",
       (CLOCK_LEGACY, CLOCK, CLOCK_LEGACY, "CLOCK_MONOTONIC_RAWX", None, None),
       (header_clock(header_12), header_clock("# " + HEADER),
        header_clock("# hostprobe 1.2: t_mono is absolute CLOCK_MONOTONIC seconds, "
                     "not CLOCK_MONOTONIC_RAW"),
        header_clock("# hostprobe 1.3: t_raw is absolute CLOCK_MONOTONIC_RAWX seconds"),
        header_clock("# hostprobe 1.0: planted"),
        header_clock("hostprobe 1.3: t_raw is absolute CLOCK_MONOTONIC_RAW seconds")))

    # ---------------- V: the FW-124 contract, in-process.  V1 runs refuse_args
    # with every host read it must not make turned into an exception: files,
    # directory listings, subprocesses, sockets, clocks, os.environ.
    class Poisoned(Exception):
        pass

    def trap(*_a, **_k):
        raise Poisoned("an environment read inside refuse_args")

    class PoisonEnv(dict):
        def _no(self, *_a, **_k):
            raise Poisoned("os.environ inside refuse_args")
        __getitem__ = get = __contains__ = __iter__ = __len__ = _no
        keys = items = values = copy = _no

    def poisoned(fn, *args):
        spots = [(builtins, "open"), (io, "open"), (os, "open"), (os, "stat"),
                 (os, "lstat"), (os, "access"), (os, "listdir"), (os, "scandir"),
                 (subprocess, "Popen"), (subprocess, "run"), (socket, "socket"),
                 (shutil, "which"), (time, "time"), (time, "clock_gettime"),
                 (time, "monotonic")]
        saved = [(m, n, getattr(m, n)) for m, n in spots]
        env = os.environ
        try:
            for m, n, _v in saved:
                setattr(m, n, trap)
            os.environ = PoisonEnv()
            return fn(*args)
        finally:
            for m, n, v in saved:
                setattr(m, n, v)
            os.environ = env

    def verdict(argv):
        a = build_parser().parse_args(argv)      # argparse reads COLUMNS: unpoisoned
        try:
            c = poisoned(refuse_args, a)
        except Refused as e:
            return "R: " + str(e)
        except Poisoned as e:
            return "POISON: %s" % e
        except Exception as e:            # noqa: BLE001 -- a crash is a verdict too
            return "CRASH: %s: %s" % (type(e).__name__, e)
        return ("ok", getattr(c, "until", None), getattr(c, "loopback", None))

    base = ["run", "--out", "v1/p", "--target", "127.0.0.1"]
    good_v = verdict(base + ["--seconds", "1", "--icmp", "--icmp-interval", "0.05",
                             "--tcp", "80", "--until", "tcp:80:ok"])
    bad_v = [verdict(base + extra) for extra in (
        ["--tcp", "80"],
        ["--tcp", "80", "--seconds", "0"],
        ["--icmp", "--icmp-interval", "0.0029", "--seconds", "1"],
        ["--tcp", "80", "--until", "tcp:81:ok", "--seconds", "1"],
        ["--seconds", "1", "--tcp", "80", "--out", "v1/"])]
    needles = ("--seconds N is required", "positive, finite", "whole number of "
               "milliseconds", "is not probed", "must be a path prefix")
    try:
        poisoned(os.path.exists, "/")
        takes = False
    except Poisoned:
        takes = True
    ck("V1", "refuse_args in-process, every host read poisoned: the good form "
             "permitted, five bad ones refused for their reasons, the poison takes",
       (("ok", [("tcp", "80", "ok")], True), [True] * 5, True),
       (good_v, [isinstance(v, str) and v.startswith("R: ") and nd in v
                 for v, nd in zip(bad_v, needles)], takes))

    # ---------------- K: the address gate's parts (H11).  Every address here
    # except the allowlisted ones is synthetic and locally administered, so
    # none of them is anybody's.
    ck("K1", "canonical: colon, dash, bare, enx, either case -> one form; a "
             "prefix, 5 octets, mixed separators -> none",
       ("02:52:4c:58:46:57",) * 5 + (None, None, None),
       tuple(canonical_mac(s) for s in (
           "02:52:4C:58:46:57", "02-52-4c-58-46-57", "02524C584657",
           "enx02524c584657", "02:52:4c:58:46:57", "00:12:34:56:78:9",
           "02:52:4c:58:46", "02:52-4c:58:46:57")))
    try:
        real, kerr = load_mac_allowlist(), None
    except AllowlistUnavailable as e:
        real, kerr = frozenset(), str(e)
    ck("K2", "the loader on the real audit-bench-log.py: its address literals, "
             "canonical, rlxfw's own among them, the prefix entry not",
       (None, True, True, False, True),
       (kerr, len(real) >= 5, "02:52:4c:58:46:57" in real,
        any(x is None or x.startswith("00:12:34:56:78:9") for x in real),
        all(x is not None and canonical_mac(x) == x for x in real)))
    rk = Redactor(frozenset(["02:52:4c:58:46:57"]), True)
    ck("K3", "redactor: allowlisted verbatim in either case; others unlisted-1, "
             "-2, -1 again; `-` stays; a 4-octet lladdr is labelled",
       ("02:52:4C:58:46:57", "02:52:4c:58:46:57", "unlisted-1", "unlisted-2",
        "unlisted-1", "-", "unlisted-3"),
       tuple(rk.address(x) for x in (
           "02:52:4C:58:46:57", "02:52:4c:58:46:57", "0a:1b:2c:3d:4e:5f",
           "06:00:00:00:00:02", "0A:1B:2C:3D:4E:5F", "-", "00:00:00:00")))
    rk = Redactor(frozenset(["02:52:4c:58:46:57"]), True)
    digest = "ab" * 32
    ck("K4", "text: colon, dash, bare, enx -> one label; allowlisted, times, "
             "errno names, a digest untouched; 8 octets labelled whole",
       "a unlisted-1 b unlisted-1 c unlisted-1 d unlisted-1: keep 02:52:4C:58:46:57 "
       "1790115167.180567 ECONNREFUSED %s eui unlisted-2" % digest,
       rk.text("a 0a:1b:2c:3d:4e:5f b 0A-1B-2C-3D-4E-5F c 0a1b2c3d4e5f "
               "d enx0a1b2c3d4e5f: keep 02:52:4C:58:46:57 1790115167.180567 "
               "ECONNREFUSED %s eui 02:00:00:ff:fe:00:00:01" % digest))
    r1, r2 = Redactor(), Redactor()
    s1 = [r1.address(x) for x in ("0a:1b:2c:3d:4e:5f", "06:00:00:00:00:02",
                                  "0a:1b:2c:3d:4e:5f")]
    s2 = [r2.address(x) for x in ("16:00:00:00:00:04", "12:34:56:78:9a:bc",
                                  "16:00:00:00:00:04")]
    ck("K5", "labels are order alone: two different address streams of one "
             "shape get the same labels",
       (["unlisted-1", "unlisted-2", "unlisted-1"], True), (s1, s1 == s2))

    # ---------------- the end-to-end cases: this file as a subprocess, a fake
    # ping and a fake ip, loopback sockets
    tmp = tempfile.mkdtemp(prefix="hostprobe-selftest-")
    procs, pids, held = [], [], []
    produced = []

    def P(name):
        return os.path.join(tmp, name)

    def write_exec(path, body):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("#!%s\n%s" % (sys.executable, body))
        os.chmod(path, 0o755)

    def hp(args, env=None, timeout=60):
        e = dict(os.environ)
        e.update(env or {})
        p = subprocess.run([sys.executable, THIS] + args, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e,
                           timeout=timeout)
        return (p.returncode, p.stdout.decode("utf-8", "replace"),
                p.stderr.decode("utf-8", "replace"))

    def spawn(args, env=None):
        e = dict(os.environ)
        e.update(env or {})
        p = subprocess.Popen([sys.executable, THIS] + args, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
        procs.append(p)
        return p

    def pcfg(name, lines, **kw):
        cfg = {"pidfile": P(name + ".pid"), "argvfile": P(name + ".argv"),
               "record": P(name + ".rec"), "lines": lines}
        cfg.update(kw)
        with open(P(name + ".cfg"), "w") as f:
            json.dump(cfg, f)
        return {"HP_FAKE_PING_CFG": P(name + ".cfg")}

    def icfg(name, route="", route_rc=0, neigh=("",), neigh_rc=0):
        cfg = {"argvlog": P(name + ".iplog"), "counter": P(name + ".ipn"),
               "route": route, "route_rc": route_rc, "neigh": list(neigh),
               "neigh_rc": neigh_rc}
        with open(P(name + ".ipcfg"), "w") as f:
            json.dump(cfg, f)
        return {"HP_FAKE_IP_CFG": P(name + ".ipcfg")}

    def reply(seq, rtt="0.045", lag=0.0, tail="", delay=0.05):
        return {"delay": delay, "lag": lag, "rx": 0 if "DUP" in tail else 1,
                "text": "[{real}] 64 bytes from 127.0.0.1: icmp_seq=%d ttl=64 "
                        "time=%s ms%s" % (seq, rtt, tail)}

    def silent(seq, delay=0.05):
        return {"delay": delay, "text": "[{real}] no answer yet for icmp_seq=%d" % seq}

    def rec_of(prefix):
        try:
            ev, com, bad, meta, _clock = load_record(prefix)
        except Refused:
            return [], [], [(0, "missing")], {}
        return ev, com, bad, meta or {}

    def kinds(ev, kind):
        return [e for e in ev if e[1] == kind]

    def sess_of(name):
        """(pid, sid, pgrp) the fake ping recorded for itself, or Nones."""
        try:
            with open(P(name + ".pid")) as f:
                pid, sid, pgrp = (int(x) for x in f.read().split())
        except (OSError, ValueError):
            return None, None, None
        pids.append(pid)
        return pid, sid, pgrp

    def pid_of(name):
        return sess_of(name)[0]

    def ip_calls(name):
        try:
            with open(P(name + ".iplog")) as f:
                return [json.loads(x) for x in f]
        except (OSError, ValueError):
            return []

    def wait_for(pred, timeout):
        end = now_raw() + timeout
        while now_raw() < end:
            if pred():
                return True
            time.sleep(0.02)
        return pred()

    def count_in(prefix, *want):
        try:
            with open(prefix + ".events", encoding="utf-8") as f:
                return sum(1 for ln in f if len(ln.split()) > 1 and ln.split()[1] in want
                           and not ln.startswith("#"))
        except OSError:
            return 0

    def run_args(prefix, *extra):
        return ["run", "--out", prefix, "--target", "127.0.0.1"] + list(extra)

    fping, fip = P("fake-ping"), P("fake-ip")
    try:
        write_exec(fping, FAKE_PING)
        write_exec(fip, FAKE_IP)
        ck("C0", "the liveness check sees a live process (its own)", True,
           _alive(os.getpid()))

        # V2: main() takes its parser from build_parser() and runs refuse_args
        # before anything reads the host -- here, before the allowlist loads.
        # refuse_args is replaced by a spy that refuses, so nothing may run.
        calls = []
        g = globals()
        real = {n: g[n] for n in ("build_parser", "refuse_args", "use_allowlist")}

        def spy(name, refuse=False):
            def f(*args):
                calls.append(name)
                if refuse:
                    raise Refused("V2 spy refusal")
                return real[name](*args)
            return f
        pv2 = P("v2")
        err = io.StringIO()
        try:
            g["build_parser"] = spy("build_parser")
            g["refuse_args"] = spy("refuse_args", refuse=True)
            g["use_allowlist"] = spy("use_allowlist")
            with contextlib.redirect_stderr(err):
                rc = main(["run", "--out", pv2, "--target", "127.0.0.1", "--tcp", "80",
                           "--seconds", "1"])
        finally:
            g.update(real)
        ck("V2", "main() calls build_parser once, then refuse_args, before the "
                 "allowlist is read: exit 2, the refusal, no file",
           (2, ["build_parser", "refuse_args"], True, False),
           (rc, calls, "V2 spy refusal" in err.getvalue(),
            os.path.exists(pv2 + ".events") or os.path.exists(pv2 + ".meta.json")))

        # ---- P: replies, silents, a DUP and an error line through the whole path
        pp = P("p")
        env = pcfg("p", [silent(1), silent(2), reply(3), reply(4, rtt="0.051"),
                         reply(4, rtt="0.060", tail=" (DUP!)"),
                         {"delay": 0.05, "text": "[{real}] From 127.0.0.1 "
                                                 "icmp_seq=5 Destination Host Unreachable"},
                         reply(6, rtt="0.050", tail=" (truncated)")])
        rc, so, se = hp(run_args(pp, "--seconds", "1.0", "--icmp", "--ping", fping,
                                 "--lag-threshold-ms", "500"), env)
        produced.append(pp)
        ev, com, bad, meta = rec_of(pp)
        try:
            with open(P("p.rec")) as f:
                printed = [json.loads(x) for x in f]
        except (OSError, ValueError):
            printed = []
        want_real = next((x["real"] for x in printed if "icmp_seq=3 " in x["text"]), None)
        replies = kinds(ev, "icmp-reply")
        ck("P1", "one canned reply -> one icmp-reply: ttl, rtt, ping_real exact",
           [("64", "0.045", want_real)],
           [(f["ttl"], f["rtt_ms"], f["ping_real"]) for _t, _k, f, _r in replies
            if f["seq"] == "3"])
        ck("P2", "two `no answer yet` lines -> icmp-silent seq 1 and 2", ["1", "2"],
           [f["seq"] for _t, _k, f, _r in kinds(ev, "icmp-silent")])
        other = ((meta.get("ping") or {}).get("other_lines") or {})
        ck("P2b", "the DUP, From-error and truncated lines are comments, not events",
           (2, 1, 1, 1), (len(replies), other.get("dup"), other.get("error"),
                          other.get("truncated")))
        rc2, rep, _se = hp(["report", pp])
        line = next((x for x in rep.splitlines() if x.startswith("  first  icmp-reply ")), "")
        ck("P3", "report's first icmp-reply is seq=3 at the events' own t",
           (0, True, True),
           (rc2, bool(replies) and (" %s " % replies[0][3].split()[0]) in line,
            "seq=3" in line))
        ck("P4", "exit 0 on --seconds, and ping's own count agrees (H3)",
           (0, "--seconds", True),
           (rc, meta.get("stop_reason"), (meta.get("ping") or {}).get("statistics_agree")))
        ck("C1", "after a --seconds run the fake ping is gone", False,
           _alive(pid_of("p")))

        # ---- N: only silence from the target
        pn = P("n")
        env = pcfg("n", [silent(1), silent(2), silent(3), silent(4)])
        rc, so, se = hp(run_args(pn, "--seconds", "0.8", "--icmp", "--ping", fping), env)
        produced.append(pn)
        ev, com, bad, meta = rec_of(pn)
        ck("N1", "only `no answer yet` lines -> no icmp-reply event", (0, 4),
           (len(kinds(ev, "icmp-reply")), len(kinds(ev, "icmp-silent"))))
        _rc, rep, _se = hp(["report", pn])
        fl = next((x for x in rep.splitlines() if x.startswith("  first  icmp-reply ")), "")
        cl = next((x for x in rep.splitlines() if x.startswith("  count  icmp-reply ")), "")
        ck("N1b", "and report prints `none` for its first and its count, never 0",
           (True, True), (fl.endswith(" none"), cl.endswith(" none")))
        ck("N2", "silence from the target is a reading: exit 0, H2 not tripped",
           (0, []), (rc, meta.get("problems")))

        # ---- L: the lag cross-check, both directions
        pl = P("l")
        env = pcfg("l", [reply(1), reply(2, lag=5.0), reply(3), reply(4, lag=5.0),
                         reply(5, lag=-5.0)])
        rc, so, se = hp(run_args(pl, "--seconds", "1.0", "--icmp", "--ping", fping,
                                 "--lag-threshold-ms", "500"), env)
        produced.append(pl)
        ev, com, bad, meta = rec_of(pl)
        flagged = {}
        for cmt in com:
            m = LAG_COMMENT_RX.search(cmt)
            if m:
                flagged[int(m.group(1))] = float(m.group(2))
        ck("L1", "lagged 5 s -> flagged; lagged 0 -> not (threshold 500 ms)", [2, 4],
           sorted(s for s, v in flagged.items() if v > 0))
        ck("L2", "a stamp 5 s in the future is flagged, as negative", [5],
           sorted(s for s, v in flagged.items() if v < 0))
        lg = meta.get("icmp_lag_ms") or {}
        ck("L3", "meta: n counts every ICMP line, over_threshold every flag",
           (5, 3, 500.0), (lg.get("n"), lg.get("over_threshold"), lg.get("threshold_ms")))

        # ---- S: the instrument's own failures are exit 1, not `none`
        ps1 = P("s1")
        env = pcfg("s1", [])
        rc, so, se = hp(run_args(ps1, "--seconds", "1.8", "--icmp", "--ping", fping,
                                 "--icmp-interval", "0.2"), env)
        produced.append(ps1)
        meta = rec_of(ps1)[3]
        ck("S1", "a ping that prints only its header -> exit 1, H2 named",
           (1, True), (rc, any(p.startswith("H2") for p in meta.get("problems", []))))
        ps2 = P("s2")
        env = pcfg("s2", [reply(1), reply(2)], rx_bias=1)
        rc, so, se = hp(run_args(ps2, "--seconds", "0.8", "--icmp", "--ping", fping), env)
        produced.append(ps2)
        meta = rec_of(ps2)[3]
        ck("S2", "ping's statistics claim one reply more -> exit 1, H3 named",
           (1, True, False), (rc, any(p.startswith("H3") for p in meta.get("problems", [])),
                              (meta.get("ping") or {}).get("statistics_agree")))
        ps3 = P("s3")
        env = pcfg("s3", [reply(1)], exit_rc=2)
        rc, so, se = hp(run_args(ps3, "--seconds", "5", "--icmp", "--ping", fping), env)
        produced.append(ps3)
        meta = rec_of(ps3)[3]
        ck("S3", "a ping that exits on its own -> exit 1, stop ping-exited",
           (1, "ping-exited", True),
           (rc, meta.get("stop_reason"), (meta.get("ping") or {}).get("exited_early")))

        # ---- T: real loopback sockets
        lo = socket.socket()
        lo.bind(("127.0.0.1", 0))
        lo.listen(128)
        cl_ = socket.socket()
        cl_.bind(("127.0.0.1", 0))              # bound, never listening: RST
        fu = socket.socket()
        fu.bind(("127.0.0.1", 0))
        fu.listen(0)
        pre = socket.create_connection(fu.getsockname(), timeout=5)   # queue full
        held += [lo, cl_, fu, pre]
        PO, PC, PF = (s.getsockname()[1] for s in (lo, cl_, fu))
        pt = P("t")
        rc, so, se = hp(run_args(pt, "--tcp", str(PO), "--tcp", str(PC), "--tcp", str(PF),
                                 "--tcp-interval", "0.1", "--tcp-timeout", "0.3",
                                 "--seconds", "1.0"))
        produced.append(pt)
        ev = rec_of(pt)[0]

        def tcp_of(port):
            return [f for _t, k, f, _r in ev if k == "tcp" and f["port"] == str(port)]
        ck("T1", "a listening port reads ok, errno 0",
           (["ok"], ["0"]), (sorted({f["result"] for f in tcp_of(PO)}),
                             sorted({f["errno"] for f in tcp_of(PO)})))
        ck("T2", "a bound port with no listener reads refused, ECONNREFUSED",
           (["refused"], ["ECONNREFUSED"]),
           (sorted({f["result"] for f in tcp_of(PC)}), sorted({f["errno"] for f in tcp_of(PC)})))
        ck("T3", "a listener with a full accept queue reads timeout, >= 300 ms",
           (["timeout"], True),
           (sorted({f["result"] for f in tcp_of(PF)}),
            bool(tcp_of(PF)) and all(float(f["dur_ms"]) >= 300.0 for f in tcp_of(PF))))
        pt4 = P("t4")
        rc, so, se = hp(run_args(pt4, "--tcp", str(PO), "--tcp", str(PC),
                                 "--until", "tcp:%d:ok" % PO, "--seconds", "5"))
        produced.append(pt4)
        ev, com, bad, meta = rec_of(pt4)
        oks = [t for t, k, f, _r in ev if k == "tcp" and f["result"] == "ok"]
        stops = [t for t, k, _f, _r in ev if k == "stop"]
        ck("T4", "--until tcp:OPEN:ok stops at the first ok, far inside --seconds",
           ("--until=tcp:%d:ok" % PO, True, True),
           (meta.get("stop_reason"),
            (meta.get("end_raw", 99) - meta.get("start_raw", 0)) < 2.0,
            bool(oks) and bool(stops) and oks[0] <= stops[0]))
        pt5 = P("t5")
        rc, so, se = hp(run_args(pt5, "--tcp", str(PC), "--until", "tcp:%d:ok" % PC,
                                 "--tcp-interval", "0.1", "--seconds", "0.7"))
        produced.append(pt5)
        ev, com, bad, meta = rec_of(pt5)
        res5 = [f["result"] for _t, k, f, _r in ev if k == "tcp"]
        ck("T5", "--until tcp:CLOSED:ok is not fired by refused: runs to --seconds",
           ("--seconds", True, 0),
           (meta.get("stop_reason"), res5.count("refused") >= 3, res5.count("ok")))

        # ---- D: datagrams to ourselves
        def free_udp():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            s.close()
            return port
        UP = free_udp()
        pd = P("d")
        p = spawn(run_args(pd, "--udp-listen", str(UP), "--seconds", "1.5"))
        started = wait_for(lambda: count_in(pd, "start") == 1, 15)
        snd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        snd.bind(("127.0.0.1", 0))
        SP = snd.getsockname()[1]
        t_send = time.time()
        snd.sendto(b"x" * 7, ("127.0.0.1", UP))
        snd.sendto(b"y" * 300, ("127.0.0.1", UP))
        snd.close()
        p.communicate(timeout=30)
        produced.append(pd)
        ev, com, bad, meta = rec_of(pd)
        ud = [f for _t, k, f, _r in ev if k == "udp"]
        ck("D1", "two datagrams -> two udp events: 7 and 300 bytes, the sender's peer",
           (True, [("7", "127.0.0.1:%d" % SP), ("300", "127.0.0.1:%d" % SP)]),
           (started, [(f["len"], f["peer"]) for f in ud]))
        expect_ts = sys.platform.startswith("linux") and platform.machine() in SO_TIMESTAMPNS_MACHINES
        ts_on = ((meta.get("udp") or {}).get(str(UP)) or {}).get("so_timestampns")
        if ts_on:
            good_stamp = len(ud) == 2 and all(
                f["kernel_real"] != "-" and abs(float(f["kernel_real"]) - t_send) < 2.0
                for f in ud)
        else:
            good_stamp = len(ud) == 2 and all(f["kernel_real"] == "-" for f in ud)
        ck("D2", "kernel_real is the kernel's stamp (within 2 s of the send) or `-`",
           (expect_ts, True), (ts_on, good_stamp))
        UP2 = free_udp()
        pd3 = P("d3")
        p = spawn(run_args(pd3, "--udp-listen", str(UP2), "--until", "udp:%d" % UP2,
                           "--seconds", "20"))
        wait_for(lambda: count_in(pd3, "start") == 1, 15)
        snd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        snd.sendto(b"z", ("127.0.0.1", UP2))
        snd.close()
        p.communicate(timeout=40)
        produced.append(pd3)
        meta = rec_of(pd3)[3]
        ck("D3", "--until udp:PORT ends the run at the datagram",
           ("--until=udp:%d" % UP2, True),
           (meta.get("stop_reason"),
            (meta.get("end_raw", 99) - meta.get("start_raw", 0)) < 10.0))

        # ---- G: the neighbour table, through the fake ip
        pg = P("g")
        entry = "127.0.0.1 dev eth9 lladdr 02:00:00:00:00:01 %s \n"
        env = icfg("g", neigh=["", "", entry % "REACHABLE", entry % "REACHABLE",
                               entry % "STALE"])
        rc, so, se = hp(run_args(pg, "--neigh", "--neigh-interval", "0.05", "--ip", fip,
                                 "--seconds", "1.5"), env)
        produced.append(pg)
        ev, com, bad, meta = rec_of(pg)
        ck("G1", "NONE NONE REACHABLE REACHABLE STALE -> three events, in order",
           (0, [("NONE", "-"), ("REACHABLE", "unlisted-1"),
                ("STALE", "unlisted-1")], True),
           (rc, [(f["state"], f["lladdr"]) for _t, k, f, _r in ev if k == "neigh"],
            ((meta.get("neigh") or {}).get("polls") or 0) >= 5))
        polls = [c for c in ip_calls("g") if c["args"][1:2] == ["neigh"]]
        ck("G1b", "every `ip` poll leads its own session: a Ctrl-C cannot fail one",
           (True, True), (len(polls) >= 5, all(c["sid"] == c["pid"] for c in polls)))
        pg3 = P("g3")
        env = icfg("g3", neigh=["Cannot find device \"eth9\"\n"], neigh_rc=1)
        rc, so, se = hp(run_args(pg3, "--neigh", "--neigh-interval", "0.1", "--ip", fip,
                                 "--seconds", "0.6"), env)
        produced.append(pg3)
        ev, com, bad, meta = rec_of(pg3)
        ck("G3", "an `ip` whose polls fail -> no neigh event, exit 1: a gap, not NONE",
           (1, 0, True),
           (rc, len(kinds(ev, "neigh")),
            any(p.startswith("neigh:") for p in meta.get("problems", []))))
        # Non-loopback target: --neigh ONLY, through the fake ip, so even a broken
        # injection could do no more than read a neighbour table.
        pg2 = P("g2")
        env = icfg("g2", route="192.0.2.1 dev eth9 src 192.0.2.2 uid 1000 \n    cache \n",
                   neigh=["192.0.2.1 lladdr 02:00:00:00:00:02 REACHABLE \n"])
        rc, so, se = hp(["run", "--out", pg2, "--target", "192.0.2.1", "--neigh", "--ip",
                         fip, "--neigh-interval", "0.1", "--seconds", "0.5"], env)
        produced.append(pg2)
        calls = [c["args"] for c in ip_calls("g2")]
        ck("R18", "a route WITH a source address passes the host-fault guard", 0, rc)
        ck("G2", "a non-loopback target's polls filter on the route's dev",
           ["-4", "neigh", "show", "192.0.2.1", "dev", "eth9"],
           next((x for x in calls if x[1:2] == ["neigh"]), None))

        # ---- A: no address leaves the process unless the allowlist names it
        # (H11).  Injected addresses are synthetic and locally administered.
        MA, MB, MC, MD, ME = ("0a:1b:2c:3d:4e:5f", "06:00:00:00:00:02",
                              "12:34:56:78:9a:bc", "16:00:00:00:00:04",
                              "0e:00:00:00:00:03")
        ENX = "enx" + ME.replace(":", "")

        def spellings(mac):
            b = mac.replace(":", "")
            d = mac.replace(":", "-")
            return {mac, mac.upper(), d, d.upper(), b, b.upper()}

        def mac_like(text):
            """Written APART from MAC_TEXT_RX: a scanner sharing the tool's
            pattern would share its blind spots.  Hex runs joined by : or -
            with six or more two-digit parts, or exactly twelve hex digits
            between non-hex characters (which is what finds an enx name)."""
            out = []
            for m in re.finditer(r"[0-9A-Fa-f]+(?:[:-][0-9A-Fa-f]+)*", text):
                parts = re.split(r"[:-]", m.group(0))
                if ((len(parts) >= 6 and all(len(x) == 2 for x in parts))
                        or (len(parts) == 1 and len(parts[0]) == 12)):
                    out.append(m.group(0))
            return out

        def bare12(h):
            return re.sub(r"[^0-9a-f]", "", h.lower())[-12:]

        def artefacts(prefix, so, se):
            texts = {"stdout": so, "stderr": se}
            for suf in (".events", ".meta.json"):
                try:
                    with open(prefix + suf, encoding="utf-8") as f:
                        texts[suf] = f.read()
                except OSError:
                    texts[suf] = ""
            _rc, rso, rse = hp(["report", prefix])
            texts["report"] = rso + rse
            return texts

        def leaks(texts, injected, allowed=()):
            """(scanner hits not allowed, injected addresses found in any of
            six spellings) -- the second needs no pattern at all."""
            hits = sorted({(k, h) for k, t in texts.items() for h in mac_like(t)
                           if bare12(h) not in allowed})
            found = sorted({(k, s) for k, t in texts.items() for mac in injected
                            for s in spellings(mac) if s in t})
            return hits, found

        pa = P("a1")
        neigh_a = [
            "",
            "127.0.0.1 dev eth9 lladdr %s REACHABLE \n" % MA,
            "127.0.0.1 dev eth9 lladdr %s REACHABLE \n" % MB,
            ["Cannot find device \"enx%s\"; hwaddr %s %s\n"
             % (MC.replace(":", ""), MD.replace(":", "-").upper(), MC.upper()), 1],
            "127.0.0.1 dev eth9 lladdr %s REACHABLE \n"
            "127.0.0.1 dev eth8 lladdr %s STALE \n" % (MA, MD),
            "127.0.0.1 dev tun9 lladdr 00:00:00:00 PERMANENT \n"]
        env = icfg("a1", neigh=neigh_a)
        rc, so, se = hp(run_args(pa, "--neigh", "--neigh-interval", "0.05", "--ip", fip,
                                 "--seconds", "1.5"), env)
        produced.append(pa)
        ev, com, bad, meta = rec_of(pa)
        ck("A1", "lladdr: unlisted-1, a second unlisted-2, the first again "
                 "unlisted-1; a 4-octet one unlisted-3",
           [("NONE", "-"), ("REACHABLE", "unlisted-1"), ("REACHABLE", "unlisted-2"),
            ("REACHABLE", "unlisted-1"), ("PERMANENT", "unlisted-3")],
           [(f["state"], f["lladdr"]) for _t, k, f, _r in ev if k == "neigh"])
        texts = artefacts(pa, so, se)
        raw_in = " ".join(x if isinstance(x, str) else x[0] for x in neigh_a)
        ck("A2", "every artefact -- events, meta, stdout, stderr, report -- holds "
                 "none of the 4, by scanner or spelling; the scanner sees all 4 in "
                 "the input",
           ([], [], True, sorted(bare12(m) for m in (MA, MB, MC, MD))),
           leaks(texts, (MA, MB, MC, MD))
           + (all(texts[k] for k in texts),
              sorted({bare12(h) for h in mac_like(raw_in)})))
        ck("A3", "a failing poll: a gap, exit 1, and its output quoted nowhere "
                 "(its marker text is in no artefact)",
           (1, True, []),
           (rc, any("neigh-error rc=1" in x for x in com),
            sorted(k for k, t in texts.items() if "Cannot find device" in t)))
        pb = P("a4")
        env = pcfg("a4", [reply(1)],
                   header="PING 127.0.0.1 (127.0.0.1) from 127.0.0.1 %s: 56(84) "
                          "bytes of data." % ENX,
                   stderr_lines=["ping: %s: hwaddr %s"
                                 % (ENX, MD.replace(":", "-").upper())])
        rc, so, se = hp(run_args(pb, "--icmp", "--ping", fping, "--seconds", "0.6"), env)
        produced.append(pb)
        ev, com, bad, meta = rec_of(pb)
        texts = artefacts(pb, so, se)
        banner = next((x for x in com if "ping-header" in x), "")
        ck("A4", "an address only a sink sees -- ping's banner and its stderr -- "
                 "is labelled, and leaks nowhere",
           (0, True, ([], [])),
           (rc, "from 127.0.0.1 unlisted-1:" in banner, leaks(texts, (ME, MD))))
        pr5 = P("a5")
        env = icfg("a5", route="192.0.2.1 dev %s src 192.0.2.2 uid 1000 \n    cache \n"
                   % ENX, neigh=["192.0.2.1 lladdr %s REACHABLE \n" % MD])
        rc, so, se = hp(["run", "--out", pr5, "--target", "192.0.2.1", "--neigh", "--ip",
                         fip, "--neigh-interval", "0.1", "--seconds", "0.5"], env)
        produced.append(pr5)
        meta = rec_of(pr5)[3]
        texts = artefacts(pr5, so, se)
        dev = (meta.get("route") or {}).get("dev") or ""
        argv_dev = ((meta.get("neigh") or {}).get("argv") or [None])[-1]
        rrc, rso, rse = hp(["run", "--out", P("a5r"), "--target", "192.0.2.1", "--neigh",
                            "--ip", fip, "--seconds", "1"],
                           icfg("a5r", route="192.0.2.1 dev %s uid 1000 \n    cache \n" % ENX))
        ck("A5", "the route's enx device: labelled in the meta, in the argv, and "
                 "in the host-fault refusal",
           (0, True, True, ([], []), 2, True, ([], [])),
           (rc, dev.startswith("unlisted-"), argv_dev == dev, leaks(texts, (ME, MD)),
            rrc, "HOST FAULT" in rse and "unlisted-" in rse,
            leaks({"stdout": rso, "stderr": rse}, (ME,))))
        # Both on audit-bench-log.py's ALLOW today: rlxfw's own constant in both
        # spellings, and wlan0's driver default, whose literal there is upper
        # case only -- so its lower-case form matches only canonically.
        UPPER, LOWER = "02:52:4C:58:46:57", "02:52:4c:58:46:57"
        CANON = "00:E0:4C:81:86:86".lower()   # the literal's own spelling, lowered
        pr6 = P("a6")
        env = icfg("a6", neigh=["127.0.0.1 dev eth9 lladdr %s REACHABLE \n" % UPPER,
                                "127.0.0.1 dev eth9 lladdr %s REACHABLE \n" % CANON,
                                "127.0.0.1 dev eth9 lladdr %s STALE \n" % LOWER])
        rc, so, se = hp(run_args(pr6, "--neigh", "--neigh-interval", "0.05", "--ip", fip,
                                 "--seconds", "1.0"), env)
        produced.append(pr6)
        ev = rec_of(pr6)[0]
        texts = artefacts(pr6, so, se)
        ck("A6", "allowlisted addresses verbatim, upper and lower case, and one "
                 "matched only through the canonical form",
           (0, [UPPER, CANON, LOWER], [], False),
           (rc, [f["lladdr"] for _t, k, f, _r in ev if k == "neigh"],
            leaks(texts, (), allowed={bare12(UPPER), bare12(CANON)})[0],
            any(re.search(r"unlisted-\d", t) for t in texts.values())))

        def broken_root(name, abl_body):
            # A copy of this file in a directory of its own finds no
            # allowlist beside it, or the one written here.
            tools = os.path.join(P(name), "tools")
            os.makedirs(tools)
            shutil.copy(THIS, os.path.join(tools, "hostprobe.py"))
            if abl_body is not None:
                with open(os.path.join(tools, "audit-bench-log.py"), "w") as f:
                    f.write(abl_body)
            return os.path.join(tools, "hostprobe.py")

        def hp_at(path, args):
            p = subprocess.run([sys.executable, path] + args, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))

        for cid, name, body, what in (
                ("A7", "abl-missing", None, "a missing allowlist file"),
                ("A8", "abl-raises", "raise RuntimeError('broken on purpose')\n",
                 "an allowlist file that raises"),
                ("A9", "abl-noallow", "PATTERNS = []\n", "an allowlist file with no ALLOW")):
            copy = broken_root(name, body)
            prefix = P(name + "-out")
            rc, so, se = hp_at(copy, ["run", "--out", prefix, "--target", "127.0.0.1",
                                      "--neigh", "--ip", fip, "--seconds", "1"])
            files = [os.path.basename(x) for x in (prefix + ".events", prefix + ".meta.json")
                     if os.path.exists(x)]
            ck(cid, "%s refuses --neigh: exit 2, the reason, no file" % what,
               (2, True, False, []),
               (rc, "--neigh needs the address allowlist" in se, "Traceback" in se, files))
        pr10 = P("a10")
        rc, so, se = hp_at(os.path.join(P("abl-missing"), "tools", "hostprobe.py"),
                           ["run", "--out", pr10, "--target", "127.0.0.1", "--tcp", str(PC),
                            "--tcp-interval", "0.1", "--seconds", "0.4"])
        produced.append(pr10)
        a10 = rec_of(pr10)[3].get("addresses") or {}
        ck("A10", "the same missing allowlist does NOT refuse a --tcp run, and its "
                  "meta says the list was not loaded",
           (0, False, True), (rc, a10.get("loaded"), bool(a10.get("why_not"))))
        # A record version 1.0 wrote holds `ip`'s raw lladdr, and no record
        # this suite makes can: they are all clean.  So `report`'s own gate
        # is only visible on a planted one.
        pr11 = P("a11")
        with open(pr11 + ".events", "w", encoding="utf-8") as f:
            f.write("# hostprobe 1.0: planted\n"
                    "# probes target=10.1.1.1 icmp=- tcp=- neigh=0.2 udp=- "
                    "seconds=1 until=-\n"
                    "1.000000 start t_real=1.000000\n"
                    "1.100000 neigh state=REACHABLE lladdr=%s\n"
                    "2.000000 stop t_real=2.000000 reason=--seconds\n" % MA)
        rc, so, se = hp(["report", pr11])
        ck("A11", "report on a record 1.0 wrote, raw lladdr in it: the address is "
                  "printed as a label",
           (0, True, ([], [])),
           (rc, "lladdr=unlisted-1" in so, leaks({"report": so + se}, (MA,))))
        # argparse's own error line quotes the bad value and prints it itself.
        rc, so, se = hp(["run", "--out", P("a12"), "--target", "127.0.0.1",
                         "--tcp", MA.upper(), "--seconds", "1"])
        ck("A12", "argparse's own error, quoting a bad --tcp value, goes through "
                  "the gate: exit 2, labelled, no file",
           (2, True, ([], []), False),
           (rc, "invalid int value: 'unlisted-1'" in se,
            leaks({"stdout": so, "stderr": se}, (MA,)),
            os.path.exists(P("a12") + ".events")))

        # ---- R: refusals.  Each must be THIS refusal (its needle), exit 2, no
        # traceback, and leave no file -- a refusal for the wrong reason passes
        # every other check.
        def refusal(cid, label, args, needle, env=None, target="127.0.0.1"):
            prefix = P("ref-" + cid)
            rc, so, se = hp(["run", "--out", prefix, "--target", target] + args, env)
            files = [os.path.basename(x) for x in (prefix + ".events", prefix + ".meta.json",
                                                   prefix + ".meta.json.tmp")
                     if os.path.exists(x)]
            ck(cid, label, (2, True, False, []),
               (rc, needle in se, "Traceback" in se, files))

        refusal("R1", "no --seconds", ["--tcp", str(PO)], "--seconds N is required")
        refusal("R2", "--seconds 0", ["--tcp", str(PO), "--seconds", "0"], "positive")
        refusal("R2b", "--seconds -1", ["--tcp", str(PO), "--seconds", "-1"], "positive")
        refusal("R3", "no probe selected", ["--seconds", "1"], "no probe selected")
        refusal("R4", "a name, not an IPv4 literal", ["--tcp", "80", "--seconds", "1"],
                "not an IPv4 literal", target="localhost")
        refusal("R5", "an IPv6 literal", ["--tcp", "80", "--seconds", "1"],
                "not an IPv4 literal", target="::1")
        refusal("R6", "an octet out of range", ["--tcp", "80", "--seconds", "1"],
                "not an IPv4 literal", target="10.1.1.256")
        refusal("R6b", "a multicast address", ["--tcp", "80", "--seconds", "1"],
                "not a unicast", target="224.0.0.1")
        pr7 = P("ref-R7")
        with open(pr7 + ".events", "w") as f:
            f.write("sentinel\n")
        rc, so, se = hp(run_args(pr7, "--tcp", str(PO), "--seconds", "1"))
        with open(pr7 + ".events") as f:
            kept = f.read()
        ck("R7", "an existing .events: exit 2, file untouched, no meta",
           (2, True, "sentinel\n", False),
           (rc, "exists" in se, kept, os.path.exists(pr7 + ".meta.json")))
        rc, so, se = hp(run_args(pr7, "--tcp", str(PO), "--seconds", "0.3", "--force"))
        produced.append(pr7)
        with open(pr7 + ".events") as f:
            head = f.readline()
        ck("R7b", "and --force is PERMITTED: it runs and replaces the record",
           (0, True, True),
           (rc, head.startswith("# hostprobe "), os.path.exists(pr7 + ".meta.json")))
        env = pcfg("r", [reply(1)])
        refusal("R8", "-i 0.001 on iputils 20240117 (measured floor 2 ms)",
                ["--icmp", "--ping", fping, "--icmp-interval", "0.001", "--seconds", "1"],
                "below the minimum 0.002", env)
        refusal("R9", "-i 0.0029: ping would truncate it to 2 ms",
                ["--icmp", "--ping", fping, "--icmp-interval", "0.0029", "--seconds", "1"],
                "whole number of milliseconds", env)
        env_old = dict(env, HP_FAKE_PING_V="ping utility, iputils-s20180629\n")
        refusal("R10", "-i 0.1 on an unmeasured iputils: its floor is 0.2 s",
                ["--icmp", "--ping", fping, "--icmp-interval", "0.1", "--seconds", "1"],
                "has not been measured", env_old)
        pr11 = P("r11")
        env11 = pcfg("r11", [reply(1)])
        rc, so, se = hp(run_args(pr11, "--icmp", "--ping", fping, "--icmp-interval", "0.002",
                                 "--seconds", "0.5"), env11)
        produced.append(pr11)
        try:
            with open(P("r11.argv")) as f:
                argv11 = json.load(f)
        except (OSError, ValueError):
            argv11 = None
        ck("R11", "-i 0.002 on iputils 20240117 is PERMITTED, and reaches ping as 0.002",
           (0, ["-D", "-O", "-n", "-i", "0.002", "127.0.0.1"]), (rc, argv11))
        refusal("R12", "--udp-listen 80 is privileged", ["--udp-listen", "80",
                                                          "--seconds", "1"], "privileged")
        hold = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hold.bind(("0.0.0.0", 0))
        held.append(hold)
        refusal("R13", "--udp-listen on a port already bound", [
            "--udp-listen", str(hold.getsockname()[1]), "--seconds", "1"], "cannot bind")
        refusal("R14", "--until tcp:81:ok when 81 is not probed",
                ["--tcp", str(PO), "--until", "tcp:81:ok", "--seconds", "1"],
                "is not probed")
        refusal("R15", "--ping that does not exist",
                ["--icmp", "--ping", P("no-such-ping"), "--seconds", "1"],
                "no executable ping")
        refusal("R16", "a ping that is not iputils",
                ["--icmp", "--ping", fping, "--seconds", "1"], "not iputils",
                dict(env, HP_FAKE_PING_V="BusyBox v1.36.1 multi-call binary.\n"))
        refusal("R17", "a non-loopback route with no src is a HOST FAULT",
                ["--neigh", "--ip", fip, "--seconds", "1"], "HOST FAULT",
                icfg("r17", route="192.0.2.1 dev eth9 uid 1000 \n    cache \n"),
                target="192.0.2.1")
        refusal("R19", "--tcp 0", ["--tcp", "0", "--seconds", "1"], "not a port number")
        refusal("R20", "the same --udp-listen port twice",
                ["--udp-listen", "40000", "--udp-listen", "40000", "--seconds", "1"],
                "names a port twice")

        # ---- C: nothing survives a run, whichever way it stops
        def signal_run(cid, sig):
            name = "c-" + sig.name
            prefix = P(name)
            env = pcfg(name, [reply(1)])
            p = spawn(run_args(prefix, "--icmp", "--ping", fping, "--seconds", "60"), env)
            seen = wait_for(lambda: count_in(prefix, "icmp-reply") >= 1, 15)
            p.send_signal(sig)
            try:
                p.communicate(timeout=30)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                p.kill()
                rc = None
            produced.append(prefix)
            meta = rec_of(prefix)[3]
            ck(cid, "%s mid-run: exit 0, stop %s, meta written, ping gone"
               % (sig.name, sig.name), (True, 0, sig.name, False),
               (seen, rc, meta.get("stop_reason"), _alive(pid_of(name))))
        signal_run("C2", signal.SIGTERM)
        signal_run("C3", signal.SIGINT)
        # A terminal's Ctrl-C goes to the whole foreground process GROUP.  ping
        # runs in its own session so that it is still stopped BY THE PROBE --
        # otherwise it exits on the Ctrl-C itself and reads as "exited on its
        # own".
        name = "c-pgrp"
        prefix = P(name)
        e = dict(os.environ)
        e.update(pcfg(name, [reply(1)]))
        p = subprocess.Popen([sys.executable, THIS] + run_args(
            prefix, "--icmp", "--ping", fping, "--seconds", "60"),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=e, start_new_session=True)
        procs.append(p)
        seen = wait_for(lambda: count_in(prefix, "icmp-reply") >= 1, 15)
        os.killpg(p.pid, signal.SIGINT)
        try:
            p.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            p.kill()
        produced.append(prefix)
        pg_ = rec_of(prefix)[3].get("ping") or {}
        # The OUTCOME alone is a race -- the Ctrl-C reaches a ping in the
        # probe's group at the same instant as the probe, and the probe usually
        # polls it before it has died (a mutation run found exactly that).  So
        # the MECHANISM is asserted: ping leads its own session and group.
        fpid, fsid, fpgrp = sess_of(name)
        ck("C3b", "SIGINT to the whole process group: ping leads its own session, "
                  "so only the probe stops it", (True, 0, "SIGINT", False, False, True),
           (seen, p.returncode, pg_.get("stopped_by"), pg_.get("exited_early"),
            _alive(fpid), fpid is not None and fsid == fpid and fpgrp == fpid
            and fpgrp != p.pid))
        pc4 = P("c4")
        env = pcfg("c4", [reply(1)], deaf=True)
        t = now_raw()
        rc, so, se = hp(run_args(pc4, "--icmp", "--ping", fping, "--seconds", "0.5"), env)
        took = now_raw() - t
        produced.append(pc4)
        meta = rec_of(pc4)[3]
        ck("C4", "a ping deaf to SIGINT and SIGTERM is SIGKILLed and reaped",
           (1, "SIGKILL", False, True),
           (rc, (meta.get("ping") or {}).get("stopped_by"), _alive(pid_of("c4")), took < 15))
        pc5 = P("c5")
        env = pcfg("c5", [reply(1), reply(2)], idle_lines=True, idle_every=0.05)
        p = spawn(run_args(pc5, "--icmp", "--ping", fping, "--seconds", "60"), env)
        seen = wait_for(lambda: count_in(pc5, "icmp-reply", "icmp-silent") >= 4, 15)
        p.kill()
        p.communicate(timeout=30)
        pid_of("c5")
        produced.append(pc5)
        ev, com, bad, meta = rec_of(pc5)
        ck("C5", "SIGKILL of the probe: every line up to the kill is whole, no meta",
           (True, [], True, False),
           (seen, bad, len(ev) >= 5, os.path.exists(pc5 + ".meta.json")))
        rc, rep, se = hp(["report", pc5])
        ck("C5b", "and report still reads it, saying the run did not end cleanly",
           (0, True), (rc, "did not end cleanly" in rep))

        # ---- Q: the clock (H12, H13).  Q1, Q2, Q3, Q6 and Q7 read one run made
        # under tools/clockshim.py: every Python read of CLOCK_MONOTONIC in the
        # probe's process runs at half rate and 1000 s ahead; RAW and REALTIME
        # pass through; the kernel's timers are untouched.  The harness reads
        # the clocks itself, unshimmed and never through now_raw().
        def raw():
            return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)

        def mono():
            return time.clock_gettime(time.CLOCK_MONOTONIC)

        UQ = free_udp()
        pq = P("q1")
        e = dict(os.environ)
        e.update(pcfg("q1", [silent(1), reply(2), reply(3, lag=5.0)],
                      idle_lines=True, idle_every=0.05))
        e.update(icfg("q1", neigh=["", entry % "REACHABLE"]))
        r_before, m_before = raw(), mono()
        p = subprocess.Popen(
            [sys.executable, CLOCKSHIM_PATH, "--", THIS] + run_args(
                pq, "--seconds", "1.5", "--icmp", "--ping", fping, "--icmp-interval",
                "0.05", "--lag-threshold-ms", "500", "--tcp", str(PO), "--tcp", str(PC),
                "--tcp-interval", "0.1", "--tcp-timeout", "0.3", "--neigh", "--ip", fip,
                "--neigh-interval", "0.05", "--udp-listen", str(UQ)),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
        procs.append(p)
        started = wait_for(lambda: count_in(pq, "start") == 1, 15)
        snd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        r_send = raw()
        w_send = time.time()
        snd.sendto(b"q" * 5, ("127.0.0.1", UQ))
        snd.close()
        p.communicate(timeout=60)
        r_after, m_after = raw(), mono()
        pid_of("q1")
        produced.append(pq)
        ev, com, bad, meta = rec_of(pq)
        stamps = [("event " + k, t) for t, k, _f, _r in ev]
        for _t, k, f, _r in ev:
            if k == "tcp":
                try:
                    stamps.append(("tcp start_raw", float(f["start_raw"])))
                except (KeyError, ValueError):
                    stamps.append(("tcp start_raw", None))
        cstamps = [float(m.group(1)) for m in (re.match(r"^# (\d+\.\d{6}) ", x) for x in com)
                   if m]
        stamps += [("comment", v) for v in cstamps]
        for key in ("start_raw", "end_raw", "stop_decided_raw"):
            stamps.append(("meta " + key, meta.get(key)))
        stamps.append(("meta ping.started_raw", (meta.get("ping") or {}).get("started_raw")))
        stamps += [("meta first " + k, v) for k, v in (meta.get("first") or {}).items()
                   if v is not None]
        outside = sorted({name for name, v in stamps
                          if not (isinstance(v, (int, float)) and r_before <= v <= r_after)})
        ck("Q1", "under the shim: every event, comment stamp, tcp start_raw, RAW "
                 "meta key and first in the harness's RAW bracket; every kind fired",
           (0, True, [], ["icmp-reply", "icmp-silent", "neigh", "start", "stop", "tcp",
                          "udp"], True),
           (p.returncode, started, outside, sorted({k for _t, k, _f, _r in ev}),
            len(cstamps) >= 2))
        t_first = next((t for t, k, _f, _r in ev if k == "start"), None)
        t_last = next((t for t, k, _f, _r in ev if k == "stop"), None)
        try:
            decided = meta["stop_decided_raw"] - meta["start_raw"]
            ratio = ((meta["mono_at_end"] - meta["mono_at_start"])
                     / (meta["end_raw"] - meta["start_raw"]))
            host_r = (m_after - m_before) / (r_after - r_before)
            q2 = (meta.get("stop_reason"), 1.5 <= decided <= 1.85,
                  1.5 <= t_last - t_first <= 2.5, abs(ratio - 0.5 * host_r) < 0.02)
        except (KeyError, TypeError, ZeroDivisionError) as ex:
            q2 = ("unreadable: %s" % ex,)
        ck("Q2", "under the shim: --seconds 1.5 decided on RAW (1.5-1.85 s), the "
                 "record spans it on RAW, mono_at_* at half the harness's MONO/RAW rate",
           ("--seconds", True, True, True), q2)
        try:
            with open(pq + ".events", encoding="utf-8") as f:
                head_q = f.readline().rstrip("\n")
        except OSError:
            head_q = ""
        tcp_lines = [r for _t, k, _f, r in ev if k == "tcp"]

        def keys_of(o):
            if isinstance(o, dict):
                return [k for k in o] + [x for v in o.values() for x in keys_of(v)]
            if isinstance(o, list):
                return [x for v in o for x in keys_of(v)]
            return []
        ck("Q3", "the header names CLOCK_MONOTONIC_RAW as a whole word and no bare "
                 "CLOCK_MONOTONIC; meta clock and version exact; tcp start_raw; no "
                 "meta key ends _mono",
           (True, False, "CLOCK_MONOTONIC_RAW", "1.3", True, []),
           (bool(re.search(r"\bCLOCK_MONOTONIC_RAW\b", head_q)),
            bool(re.search(r"\bCLOCK_MONOTONIC\b", head_q)),
            meta.get("clock"), meta.get("tool_version"),
            bool(tcp_lines) and all(" start_raw=" in x and " start_mono=" not in x
                                    for x in tcp_lines),
            sorted(k for k in keys_of(meta) if k.endswith("_mono"))))

        def slurp(path):
            try:
                with open(path) as f:
                    return f.read().strip()
            except OSError:
                return None
        hb = slurp("/proc/sys/kernel/random/boot_id")
        hcs = slurp("/sys/devices/system/clocksource/clocksource0/current_clocksource")
        # a version-1 UUID; its node field is synthetic, locally administered
        v1_uuid = "12345678-1234-1234-8234-020000000005"
        ck("Q6", "boot_id and both clocksources equal the harness's reads; the "
                 "redactor would label boot_id, so it skips it -- as a v4 UUID only",
           (True, True, True, True, True, True, None),
           (bool(hb) and bool(hcs), meta.get("boot_id") == hb, meta.get("clocksource") == hcs,
            meta.get("clocksource_end") == hcs, bool(hb) and Redactor().text(hb) != hb,
            boot_id_value((hb or "") + "\n") == hb, boot_id_value(v1_uuid)))
        # Q7's third term is the lag measured from the harness's side: the
        # send-to-read interval on RAW minus the send-to-receive interval on
        # realtime.  Their rates differ by up to percents (CLK-38) and the
        # interval is milliseconds, hence 0.1 ms + 5 % of it.  The first term
        # catches a lag written in seconds while it is small ("%.3f" prints
        # 0.000), the third once it is not -- under load the second alone
        # passed that mutant.
        uq = [(t, f) for t, k, f, _r in ev if k == "udp"]
        ts_q = ((meta.get("udp") or {}).get(str(UQ)) or {}).get("so_timestampns")
        if expect_ts:
            try:
                got7 = []
                for t, f in uq:
                    lag = float(f["lag_ms"])
                    est = ((t - r_send) - (float(f["kernel_real"]) - w_send)) * 1e3
                    got7.append((lag > 0, r_send - 0.001 <= t - lag / 1e3 <= t + 1e-6,
                                 abs(lag - est) <= 0.1 + 0.05 * (t - r_send) * 1e3))
            except (KeyError, ValueError) as ex:
                got7 = ["lag_ms unreadable: %s" % ex]
            want7 = [(True, True, True)]
        else:
            got7, want7 = [f.get("lag_ms") for _t, f in uq], ["-"]
        ck("Q7", "a udp line's lag_ms > 0 puts the kernel's receive, on RAW, between "
                 "the send and the read, and agrees with the harness's own estimate",
           (expect_ts, want7), (bool(ts_q), got7))

        # Q4: records of every version read on the clock their header declares.
        def plant(name, header, body, pmeta):
            prefix = P(name)
            with open(prefix + ".events", "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(x + "\n" for x in [header] + body))
            with open(prefix + ".meta.json", "w", encoding="utf-8") as f:
                json.dump(pmeta, f)
            return prefix

        def pmeta(version, clock):
            return {"tool": "hostprobe", "tool_version": version, "clock": clock}
        header_11 = header_12.replace("hostprobe 1.2:", "hostprobe 1.1:")
        header_13 = "# hostprobe 1.3: t_raw is absolute CLOCK_MONOTONIC_RAW seconds (planted)"
        probes_l = "# probes target=192.0.2.1 icmp=- tcp=80 neigh=- udp=50000 seconds=5 until=-"
        start_l = "100.000000 start t_real=1790000000.000000"
        stop_l = "105.000000 stop t_real=1790000005.000000 reason=--seconds"
        tcp_m = "100.500000 tcp port=80 result=ok errno=0 start_mono=100.400000 dur_ms=100.000"
        tcp_r = tcp_m.replace("start_mono=", "start_raw=")
        udp_m = ("101.000000 udp port=50000 peer=192.0.2.3:40000 len=10 "
                 "kernel_real=1790000000.999900000")
        udp_r = udp_m + " lag_ms=0.100"

        def body(tcp_l, udp_l):
            return [probes_l, start_l, tcp_l, udp_l, stop_l]

        def read_as(prefix):
            try:
                ev_, _c, bad_, _m, (clk, _how) = load_record(prefix)
            except Refused as ex:
                return ("refused", str(ex))
            return clk, len(ev_), sorted(n for n, _why in bad_)

        def drift_of(prefix):
            rc_, rep_, _se = hp(["report", prefix])
            ln = next((x for x in rep_.splitlines() if x.startswith("  drift  ")), "")
            return (rc_, bool(re.search(r"\bCLOCK_MONOTONIC\b", ln)),
                    bool(re.search(r"\bCLOCK_MONOTONIC_RAW\b", ln)))
        q11 = plant("q4-11", header_11, body(tcp_m, udp_m), pmeta("1.1", CLOCK_LEGACY))
        q12 = plant("q4-12", header_12, body(tcp_m, udp_m), pmeta("1.2", CLOCK_LEGACY))
        clk_q, n_q, bad_q = read_as(pq)
        ck("Q4", "planted 1.1 and 1.2 records read on CLOCK_MONOTONIC, 0 MALFORMED; "
                 "this suite's 1.3 record on RAW; report's drift names each one's clock",
           ((CLOCK_LEGACY, 4, []), (CLOCK_LEGACY, 4, []), (CLOCK, True, []),
            (0, True, False), (0, False, True)),
           (read_as(q11), read_as(q12), (clk_q, n_q >= 10, bad_q), drift_of(q12),
            drift_of(pq)))
        mixed = (plant("q4b-a", header_13, body(tcp_m, udp_r), pmeta("1.3", CLOCK)),
                 plant("q4b-b", header_12, body(tcp_r, udp_m), pmeta("1.2", CLOCK_LEGACY)),
                 plant("q4b-c", header_13, body(tcp_r, udp_m), pmeta("1.3", CLOCK)),
                 plant("q4b-d", header_13, body(tcp_r, udp_r), pmeta("1.3", CLOCK_LEGACY)))
        rc4b, _so, _se = hp(["report", mixed[3]])
        ck("Q4b", "MALFORMED: a 1.3 tcp line with start_mono, a 1.2 one with start_raw, "
                  "a 1.3 udp line without lag_ms, a 1.3 header its meta calls MONOTONIC",
           ([4], [4], [5], [1], 1), tuple(read_as(x)[2] for x in mixed) + (rc4b,))
        tally = {"records": 0, "tcp": 0, "udp": 0}
        unread = []
        for path in sorted(glob.glob(os.path.join(ROOT, "bench", "**", "*.events"),
                                     recursive=True)):
            prefix = path[:-len(".events")]
            try:
                ev_, _c, bad_, _m, (clk, how) = load_record(prefix)
            except Refused:
                unread.append((os.path.basename(prefix), "refused"))
                continue
            tally["records"] += 1
            if bad_ or how != "declared by the header":
                unread.append((os.path.basename(prefix), len(bad_), how[:24]))
            tally["tcp"] += sum(1 for _t, k, f, _r in ev_ if k == "tcp" and "start_mono" in f)
            tally["udp"] += sum(1 for _t, k, _f, _r in ev_ if k == "udp")
        ck("Q4c", "every record under bench/ reads on its header's clock, 0 MALFORMED "
                  "(>= 13 records, tcp start_mono and udp lines among them)",
           ([], True, True, True),
           (unread, tally["records"] >= 13, tally["tcp"] > 0, tally["udp"] > 0))

        # Q5: a Python without CLOCK_MONOTONIC_RAW.  A bootstrap deletes the
        # attribute and runs this file the way clockshim runs a tool; the same
        # bootstrap without the deletion is the permitting half.  The target is
        # not loopback, so the pre-flight's first child is `ip -4 route get`,
        # which the fake ip logs.
        boot_del = ("import runpy, sys, time; del time.CLOCK_MONOTONIC_RAW; "
                    "sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], "
                    "run_name='__main__')")

        def q5(name, code):
            prefix = P(name)
            e = dict(os.environ)
            e.update(icfg(name, route="192.0.2.1 dev eth9 src 192.0.2.2 uid 1000 \n"
                                      "    cache \n", neigh=[""]))
            r = subprocess.run([sys.executable, "-c", code, THIS, "run", "--out", prefix,
                                "--target", "192.0.2.1", "--neigh", "--ip", fip,
                                "--neigh-interval", "0.1", "--seconds", "0.5"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=e, timeout=60)
            files = [os.path.basename(x) for x in (prefix + ".events", prefix + ".meta.json")
                     if os.path.exists(x)]
            return (r.returncode, r.stderr.decode("utf-8", "replace"), files,
                    len(ip_calls(name)), prefix)
        rc5, se5, files5, calls5, _p5 = q5("q5", boot_del)
        rc5k, _se, files5k, calls5k, p5k = q5("q5k", boot_del.replace(
            "del time.CLOCK_MONOTONIC_RAW; ", ""))
        produced.append(p5k)
        ck("Q5", "no CLOCK_MONOTONIC_RAW: exit 2 naming it, no traceback, no file, no "
                 "child; with it, the same bootstrap runs",
           (2, True, False, [], 0, 0, 2, True),
           (rc5, "CLOCK_MONOTONIC_RAW" in se5, "Traceback" in se5, files5, calls5,
            rc5k, len(files5k), calls5k >= 2))

        # ---- F: the format, over every record this suite made
        ck("F0", "the format checks read the records of at least 18 runs", True,
           len(produced) >= 18)
        bad_lines, backwards, heads, missing, ends = [], [], [], [], []
        undated = []
        for prefix in produced:
            name = os.path.basename(prefix)
            try:
                with open(prefix + ".events", encoding="utf-8", newline="") as f:
                    text = f.read()
            except OSError:
                bad_lines.append((name, "no .events"))
                continue
            lines = text.split("\n")
            if lines[-1] != "":
                bad_lines.append((name, "no final newline"))
            last, prev, seq = {}, None, []
            hclock = header_clock(lines[0])
            for ln in lines[:-1]:
                if ln.startswith("#"):
                    continue
                try:
                    t, kind, _f = parse_event_line(ln, hclock or CLOCK)
                except ValueError as e:
                    bad_lines.append((name, ln[:50], str(e)))
                    continue
                if t < last.get(SOURCE[kind], t) or (prev is not None and t < prev):
                    backwards.append((name, ln[:40]))
                last[SOURCE[kind]] = t
                prev = t
                seq.append(kind)
            want_stop = 0 if prefix == pc5 else 1
            if (seq[:1] != ["start"] or seq.count("start") != 1
                    or seq.count("stop") != want_stop
                    or (want_stop and seq[-1] != "stop")):
                ends.append((name, seq[:1], seq[-1:], seq.count("stop")))
            # The declared token, not 1.2's `CLOCK in lines[0]`: a substring
            # test with CLOCK_MONOTONIC passes a header declaring RAW (a prefix),
            # and with CLOCK_MONOTONIC_RAW passes one declaring MONOTONIC that
            # names RAW in passing (U14).
            if hclock != CLOCK:
                heads.append(name)
            if prefix == pc5:
                continue            # killed on purpose: no meta by design
            meta = rec_of(prefix)[3]
            when, why = capdate_when(prefix + ".meta.json")
            if why or meta.get("start_real") is None or when.date() != \
                    datetime.datetime.fromtimestamp(meta["start_real"]).date():
                undated.append((name, why or str(when)))
            gaps = [k for k in REQUIRED_META if k not in meta]
            gaps += ["icmp_lag_ms." + k for k in REQUIRED_LAG
                     if k not in (meta.get("icmp_lag_ms") or {})]
            if (meta.get("args") or {}).get("icmp"):
                gaps += ["ping." + k for k in REQUIRED_PING if k not in (meta.get("ping") or {})]
            if gaps:
                missing.append((name, gaps))
        ck("F1", "every non-comment line of every record parses as <float> <kind> k=v",
           [], bad_lines)
        ck("F2", "t never decreases, within a source or across the file", [],
           backwards)
        ck("F3", "every meta carries every key the format names", [], missing)
        ck("F4", "every record's header declares CLOCK_MONOTONIC_RAW, a whole token",
           [], heads)
        ck("F5", "one start first; one stop last, and none in the record killed "
                 "on purpose", [], ends)
        # F6: dated the way capdate dates it -- ITS reader, loaded by path, so
        # the two tools cannot drift apart -- on the day of start_real.  The
        # negative half: the same reader refuses a meta with the key removed,
        # which is what every 1.1 record was.
        neg = P("f6-neg.meta.json")
        if produced:
            m1 = dict(rec_of(produced[0])[3])
            m1.pop("started_wallclock", None)
            with open(neg, "w", encoding="utf-8") as f:
                json.dump(m1, f)
        ck("F6", "every meta is dated by capdate's own reader, on start_real's "
                 "day; without the key it is refused", ([], "no started_wallclock"),
           (undated, capdate_when(neg)[1]))
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
                p.wait()
        for pid in pids:
            if _alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        for s in held:
            s.close()
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- Z: the docstring's controls are this suite's controls
    sect = __doc__.split("REFUTATION CONDITIONS", 1)[1].split("WHAT IT DOES NOT", 1)[0]
    cited = set(re.findall(r"`([A-Z]\d{1,2}[a-z]?)`", sect))
    ck("Z1", "every control the docstring cites ran, and it cites at least 30",
       ([], True), (sorted(cited - set(ran)), len(cited) >= 30))
    print("", file=out)
    print("RESULT: %d passed, %d failed" % (passed, failed), file=out)
    return 0 if failed == 0 else 1


# ------------------------------------------------------------------- main
class _Parser(argparse.ArgumentParser):
    """argparse's own error line quotes the offending value -- `invalid int
    value: '...'` -- and prints it itself, past `say()`.  This routes it
    through the gate (H11, A12).  Sub-parsers inherit the class."""

    def error(self, message):
        self.print_usage(sys.stderr)
        say("%s: error: %s" % (self.prog, message), err=True)
        sys.exit(2)


def build_parser():
    """The parser main() uses, and the only one (FW-124: a card's HOST cell is
    checked with it and refuse_args, in-process; V2 holds main to it)."""
    ap = _Parser(
        prog="hostprobe.py",
        description="host-side network events, stamped on CLOCK_MONOTONIC_RAW "
                    "(P2-1; RAW since 1.3)")
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls: a fake ping, a fake ip, loopback sockets")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="probe TARGET and write PREFIX.events and "
                                   "PREFIX.meta.json")
    r.add_argument("--out", required=True, help="output path prefix, no extension")
    r.add_argument("--target", required=True, help="an IPv4 literal")
    r.add_argument("--seconds", type=float, default=None,
                   help="REQUIRED: the cap on the run, also with --until")
    r.add_argument("--icmp", action="store_true",
                   help="drive `ping -D -O -n -i S TARGET` and record each line")
    r.add_argument("--icmp-interval", type=float, default=DEFAULT_ICMP_INTERVAL_S,
                   help="ping's -i, whole milliseconds, >= the measured floor "
                        "(2 ms on iputils 20240117). Achieved here: 204 ms for "
                        "0.2 (量 2026-09-23); the meta records the achieved "
                        "interval (default %g)" % DEFAULT_ICMP_INTERVAL_S)
    r.add_argument("--lag-threshold-ms", type=float, default=DEFAULT_LAG_THRESHOLD_MS,
                   help="flag an ICMP line read more than this after ping stamped "
                        "it (default %g)" % DEFAULT_LAG_THRESHOLD_MS)
    r.add_argument("--tcp", type=int, action="append", default=[], metavar="PORT",
                   help="connect() to TARGET:PORT every --tcp-interval (repeatable)")
    r.add_argument("--tcp-interval", type=float, default=DEFAULT_TCP_INTERVAL_S)
    r.add_argument("--tcp-timeout", type=float, default=DEFAULT_TCP_TIMEOUT_S)
    r.add_argument("--neigh", action="store_true",
                   help="poll `ip -4 neigh show TARGET`; an event on each change")
    r.add_argument("--neigh-interval", type=float, default=DEFAULT_NEIGH_INTERVAL_S)
    r.add_argument("--udp-listen", type=int, action="append", default=[], metavar="PORT",
                   help="bind 0.0.0.0:PORT (>= 1024) and record each datagram's "
                        "arrival (repeatable)")
    r.add_argument("--until", action="append", default=[], metavar="SPEC",
                   help="end the run at the first matching event: icmp-reply, "
                        "icmp-silent, tcp[:PORT[:RESULT]], neigh[:STATE], "
                        "udp[:PORT] (repeatable; any one ends it)")
    r.add_argument("--ping", default="ping", help="the ping to drive (default: PATH's)")
    r.add_argument("--ip", default="ip", help="the iproute2 ip (default: PATH's)")
    r.add_argument("--force", action="store_true", help="overwrite an existing record")
    rp = sub.add_parser("report", help="first event of each kind, counts, lags, drift")
    rp.add_argument("prefix")
    return ap


def refuse_host(a):
    """What `run` and `--self-test` need of the host, before any file, socket
    or child exists: Linux, and a Python with CLOCK_MONOTONIC_RAW (Q5).
    `report` needs neither and runs anywhere."""
    if not (a.self_test or a.cmd == "run"):
        return
    if not sys.platform.startswith("linux"):
        # select() on pipes, SIGHUP, /proc and iputils are Linux's; under
        # Windows Python this would die with a traceback instead.
        raise Refused("`run` and `--self-test` need Linux (this host's WSL, "
                      "/usr/bin/python3); `report` runs anywhere")
    if getattr(time, "CLOCK_MONOTONIC_RAW", None) is None or not hasattr(time, "clock_gettime"):
        raise Refused("this Python has no time.CLOCK_MONOTONIC_RAW, and every stamp "
                      "and deadline hostprobe %s writes is on it (ONE CLOCK). "
                      "Refusing before any file, socket or child exists"
                      % TOOL_VERSION)


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    try:
        # FW-124: the argument refusals first, on the parser a card's check
        # uses, before anything reads the host; then the host's own.
        refuse_args(a)
        refuse_host(a)
        if a.self_test:
            return selftest()
        if a.cmd == "run":
            return run(a)
        if a.cmd == "report":
            return report(a.prefix)
        ap.print_usage(sys.stderr)
        return 2
    except Refused as e:
        say("hostprobe: %s" % e, err=True)
        return 2
    except KeyboardInterrupt:
        say("hostprobe: interrupted before a run started; nothing was written",
            err=True)
        return 2
    except Exception as e:
        if a.self_test:
            raise
        # A traceback prints an exception's message unfiltered, and a message
        # can quote what it choked on; this line goes through the gate (H11).
        say("hostprobe: internal error: %s" % _exc_line(e), err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
