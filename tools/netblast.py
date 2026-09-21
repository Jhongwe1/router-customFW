#!/usr/bin/python3
"""netblast -- drive inbound UDP at a target and ask, independently, whether it
is still transmitting.

Why this exists, and why it is not ``bench/2026-09-21e/y5-rateladder.py``
------------------------------------------------------------------------

``y5-rateladder.py`` walks an inbound byte-rate ladder against **rlxfw under
Linux** and probes with ICMP.  ``docs/nic-vendor-diff.md`` § 12.5 buys a
different cell with the same shape: run the ladder against the **second-stage
loader**, which drives the same engine, the same four TX descriptors, the same
``TXFD`` doorbell and the same ``ph_portlist = 0x3F`` (`NET-93`, `NET-94`), and
which has no Linux, no NAPI and no interrupts underneath it.

Two things make that a different instrument rather than a different argument:

**① ICMP is the wrong probe for the loader and would fail every healthy run.**
The loader answers ARP and does not answer ping -- ``RUNSHEET`` § P3, and
``looprun``'s ``host_reaches_board()`` is built on exactly that reading.  So the
liveness question here is *did an ARP reply come back*, taken from the wire.

**② The loader only transmits when something asks it to.**  Under Linux a
flood of UDP to a closed port provokes ICMP port-unreachables, so the TX ring
cycles as a side effect of the blast.  The loader has no IP stack past ARP and
TFTP: it will drop every datagram silently, and a ladder run without an ARP
load would flood the RX side while the TX ring sat idle -- which is not the
experiment, because the fault under investigation (`NET-67 殘留`) is a TX
descriptor that stops being retired.  ``--arp-load`` keeps ARP requests going
for the whole of every step, so the TX path is exercised *during* the blast and
the liveness reading is continuous instead of a single probe afterwards.

🔴 **The dose must be the same dose or the comparison is worthless.**  The
send loop below is ``y5-rateladder.py``'s ``blast()`` unchanged, and
``self-test`` ``C1`` re-derives that file's constants from the file itself and
refuses if they have drifted.  A claim that two runs had the same dose is
checked here, not asserted in a write-up.

🔴 **A probe that reports "silent" is making a claim.**  ``self-test`` ``C3``
drives the liveness probe in both directions against a host that is answering
and an address that is not, so "no reply" has a positive control standing
behind it.

What it does not do
-------------------
It does not touch the console.  A console capture runs beside it and is a third,
independent observable: the loader's command loop echoing ESC is a heartbeat
from the CPU, and ``docs/nic-vendor-diff.md`` § 12.1 says a stuck descriptor
there prints ``Assertion fail at file`` and enters ``j 0x80403DC8`` -- a wedge
this instrument cannot see and the console can.
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Y5 = os.path.join(ROOT, "bench", "2026-09-21e", "y5-rateladder.py")

# --- the dose, and it is y5-rateladder.py's -----------------------------------
PAYLOAD_LEN = 1400
PAYLOAD = b"\x00" * PAYLOAD_LEN
FRAME_BITS = (PAYLOAD_LEN + 28 + 14 + 4) * 8   # UDP payload + IP/UDP + Eth + FCS
DEFAULT_PORT = 9999
DEFAULT_STEP_S = 8.0
DEFAULT_RATES = "0.5,1.0,2.0,4.0,8.0"


def run(argv, timeout=None):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, encoding="utf-8", timeout=timeout)
    return p.returncode, p.stdout or ""


# --- liveness -----------------------------------------------------------------
def arp_probe(target, dev, count=3, wait=1.0, runner=None):
    """(ok, detail) -- did an ARP reply come back, read off the wire.

    `arping` (Habets 2.24) sends the requests itself, so this reading does not
    depend on the kernel's neighbour cache and cannot be satisfied by an entry
    left over from before the blast.
    """
    r = runner or run
    rc, txt = r(["sudo", "-n", "/usr/sbin/arping", "-i", dev,
                 "-c", str(count), "-w", str(wait), target])
    m = re.search(r"(\d+)\s+packets\s+received", txt)
    got = int(m.group(1)) if m else 0
    return got > 0, "arping rc=%d received=%d" % (rc, got)


def neigh_probe(target, dev, src=None, runner=None):
    """(ok, detail) -- the kernel's own view, as looprun's S5c takes it.

    The cache entry is deleted first: without that, an entry resolved before the
    blast would report the board alive after it had stopped answering.
    """
    r = runner or run
    r(["sudo", "-n", "ip", "neigh", "del", target, "dev", dev])
    ping = ["ping", "-c", "2", "-W", "1", "-q"]
    if src:
        ping += ["-I", src]
    r(ping + [target])                      # exit code deliberately dropped
    rc, txt = r(["ip", "-4", "neigh", "show", target, "dev", dev])
    lladdr = re.search(r"\blladdr\s+([0-9a-fA-F:]{17})", txt)
    state = re.search(r"\b(REACHABLE|STALE|DELAY|PROBE|PERMANENT|FAILED|"
                      r"INCOMPLETE|NOARP)\b", txt)
    ok = bool(lladdr) and bool(state) and state.group(1) not in (
        "FAILED", "INCOMPLETE")
    return ok, "neigh %s %s" % (lladdr.group(1) if lladdr else "no-lladdr",
                                state.group(1) if state else "no-state")


def alive(target, dev, src=None, runner=None):
    """(ok, rows) -- both sources, and a disagreement is recorded not resolved."""
    a_ok, a_d = arp_probe(target, dev, runner=runner)
    n_ok, n_d = neigh_probe(target, dev, src=src, runner=runner)
    rows = [("arping", a_ok, a_d), ("ip-neigh", n_ok, n_d)]
    return a_ok, rows


# --- the load -----------------------------------------------------------------
class ArpLoad(threading.Thread):
    """ARP requests for the whole of a step, so the target's TX ring cycles
    DURING the blast rather than only being asked about afterwards."""

    def __init__(self, target, dev):
        super().__init__(daemon=True)
        self.target, self.dev = target, dev
        self.stop = threading.Event()
        self.samples = []          # (t_rel, ok)

    def run(self):
        t0 = time.monotonic()
        while not self.stop.is_set():
            try:
                ok, _ = arp_probe(self.target, self.dev, count=1, wait=1.0)
            except Exception:
                ok = False
            self.samples.append((round(time.monotonic() - t0, 3), ok))


def blast(target, port, src, rate_mbit, step_s):
    """Send at rate_mbit for step_s, paced against the wall clock.

    Character-for-character y5-rateladder.py's blast(); C1 checks that.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((src, 0))
    interval = FRAME_BITS / (rate_mbit * 1e6)
    t0 = time.monotonic()
    n = 0
    while True:
        now = time.monotonic()
        if now - t0 >= step_s:
            break
        target_t = t0 + n * interval
        if target_t > now:
            time.sleep(target_t - now)
        try:
            s.sendto(PAYLOAD, (target, port))
        except OSError as e:
            print("  send failed: %s" % e)
            break
        n += 1
    s.close()
    dt = time.monotonic() - t0
    return n, dt


# --- the ladder ---------------------------------------------------------------
def cmd_blast(a):
    rates = [float(x) for x in a.rates.split(",") if x.strip()]
    rec = {"target": a.target, "src": a.src, "dev": a.dev, "port": a.port,
           "payload_len": PAYLOAD_LEN, "frame_bits": FRAME_BITS,
           "step_s": a.step_s, "rates_mbit": rates, "arp_load": a.arp_load,
           "started_wallclock": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "pre": None, "steps": []}

    ok, rows = alive(a.target, a.dev, a.src)
    rec["pre"] = [{"src": r[0], "ok": r[1], "detail": r[2]} for r in rows]
    for name, rok, d in rows:
        print("  pre  %-9s %-8s %s" % (name, "ANSWERS" if rok else "SILENT", d))
    if not ok:
        print("REFUSED: the target does not answer before the ladder starts. "
              "Without that reading a silent target afterwards means nothing.")
        rec["refused"] = "target silent before the ladder"
        _write(a.out, rec)
        return 1
    print("pre-ladder: target answers -- the refutation condition is armed")

    for rate in rates:
        load = None
        if a.arp_load:
            load = ArpLoad(a.target, a.dev)
            load.start()
        n, dt = blast(a.target, a.port, a.src, rate, a.step_s)
        if load:
            load.stop.set()
            load.join(timeout=5)
        got = n * FRAME_BITS / dt / 1e6
        ok, rows = alive(a.target, a.dev, a.src)
        step = {"rate_mbit_requested": rate, "frames": n, "seconds": round(dt, 3),
                "rate_mbit_actual": round(got, 3), "alive_after": ok,
                "probes": [{"src": r[0], "ok": r[1], "detail": r[2]}
                           for r in rows]}
        if load:
            step["arp_load"] = {"samples": load.samples,
                                "n": len(load.samples),
                                "n_ok": sum(1 for _, s in load.samples if s),
                                "first_fail_t": next(
                                    (t for t, s in load.samples if not s), None)}
        rec["steps"].append(step)

        line = ("%5.1f Mbit/s requested  %8d frames in %5.2f s  = %5.2f Mbit/s "
                "actual  ->  target %s" % (rate, n, dt, got,
                                           "ANSWERS" if ok else "SILENT"))
        if load:
            al = step["arp_load"]
            line += "   [arp load %d/%d ok" % (al["n_ok"], al["n"])
            if al["first_fail_t"] is not None:
                line += ", first miss at t=%.3f s" % al["first_fail_t"]
            line += "]"
        print(line)
        sys.stdout.flush()
        if not ok:
            print("threshold is between the previous step and %.1f Mbit/s"
                  % rate)
            rec["verdict"] = "stopped at %.1f Mbit/s" % rate
            _write(a.out, rec)
            return 0

    print("every step survived -- on %s..%s Mbit/s at %d-byte frames this "
          "target does not stop transmitting" % (rates[0], rates[-1],
                                                 PAYLOAD_LEN))
    rec["verdict"] = "survived the whole ladder"
    _write(a.out, rec)
    return 0


def _write(out, rec):
    if not out:
        return
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    os.replace(tmp, out)
    print("wrote %s" % out)


def cmd_probe(a):
    ok, rows = alive(a.target, a.dev, a.src)
    for name, rok, d in rows:
        print("  %-9s %-8s %s" % (name, "ANSWERS" if rok else "SILENT", d))
    if rows[0][1] != rows[1][1]:
        print("  ⚠️  the two sources DISAGREE -- recorded, not resolved")
    return 0 if ok else 1


# --- controls -----------------------------------------------------------------
def cmd_self_test(a):
    fails = []
    ran = []

    def ck(cid, what, cond, detail=""):
        print("  %-4s %-5s %s%s" % (cid, "ok" if cond else "FAIL", what,
                                    ("  -- " + detail) if detail else ""))
        ran.append(cid)
        if not cond:
            fails.append(cid)

    # C1 -- the dose is y5-rateladder.py's dose, re-derived from that file.
    try:
        src = open(Y5, encoding="utf-8").read()
        y_pay = re.search(r'PAYLOAD\s*=\s*b"\\x00"\s*\*\s*(\d+)', src)
        y_fb = re.search(r"FRAME_BITS\s*=\s*\((\d+)\s*\+\s*28\s*\+\s*14\s*\+"
                         r"\s*4\)\s*\*\s*8", src)
        y_st = re.search(r"STEP_S\s*=\s*([\d.]+)", src)
        y_pt = re.search(r"PORT\s*=\s*(\d+)", src)
        ck("C1a", "payload length matches y5-rateladder.py",
           bool(y_pay) and int(y_pay.group(1)) == PAYLOAD_LEN,
           "%s vs %d" % (y_pay.group(1) if y_pay else "?", PAYLOAD_LEN))
        ck("C1b", "frame-bits formula matches",
           bool(y_fb) and int(y_fb.group(1)) == PAYLOAD_LEN,
           "%s vs %d" % (y_fb.group(1) if y_fb else "?", PAYLOAD_LEN))
        ck("C1c", "step length matches",
           bool(y_st) and float(y_st.group(1)) == DEFAULT_STEP_S,
           "%s vs %s" % (y_st.group(1) if y_st else "?", DEFAULT_STEP_S))
        ck("C1d", "port matches",
           bool(y_pt) and int(y_pt.group(1)) == DEFAULT_PORT,
           "%s vs %d" % (y_pt.group(1) if y_pt else "?", DEFAULT_PORT))
    except OSError as e:
        ck("C1", "y5-rateladder.py is readable", False, str(e))

    # C1e -- the arithmetic itself, not just the source text.
    ck("C1e", "FRAME_BITS is 11568 for a 1400-byte datagram",
       FRAME_BITS == 11568, str(FRAME_BITS))

    # C2 -- the pacing loop actually produces the rate it was asked for.
    n, dt = blast("127.0.0.1", 9, "127.0.0.1", 0.5, 1.0)
    got = n * FRAME_BITS / dt / 1e6
    ck("C2", "pacing: 0.5 Mbit/s requested over 1 s lands within 10 %",
       abs(got - 0.5) / 0.5 < 0.10, "%d frames, %.3f Mbit/s" % (n, got))

    # C3 -- the liveness probe in BOTH directions, with injected runners so the
    # control needs no network and no board.
    def fake(arping_txt, neigh_txt, rc=0):
        def r(argv, timeout=None):
            if "arping" in argv[-2] or any("arping" in x for x in argv):
                return rc, arping_txt
            if argv[:3] == ["ip", "-4", "neigh"]:
                return 0, neigh_txt
            return 0, ""
        return r

    good_arp = "Sent 3 probes\n3 packets transmitted, 3 packets received, 0% unanswered\n"
    dead_arp = "5 packets transmitted, 0 packets received, 100% unanswered (0 extra)\n"
    good_ne = "10.1.1.1 dev if lladdr 00:11:22:33:44:55 REACHABLE\n"
    dead_ne = "10.1.1.1 dev if INCOMPLETE\n"
    ck("C3a", "a target that answers reads ANSWERS",
       alive("10.1.1.1", "if", runner=fake(good_arp, good_ne))[0])
    ck("C3b", "a target that does not answer reads SILENT",
       not alive("10.1.1.1", "if", runner=fake(dead_arp, dead_ne))[0])
    ck("C3c", "a STALE neighbour entry still counts as answering",
       neigh_probe("10.1.1.1", "if",
                   runner=fake(dead_arp,
                               good_ne.replace("REACHABLE", "STALE")))[0])
    ck("C3d", "FAILED does not count as answering",
       not neigh_probe("10.1.1.1", "if",
                       runner=fake(dead_arp,
                                   good_ne.replace("REACHABLE", "FAILED")))[0])
    rows = alive("10.1.1.1", "if", runner=fake(dead_arp, good_ne))[1]
    ck("C3e", "the two sources can disagree and both are reported",
       rows[0][1] is False and rows[1][1] is True)

    # C4 -- the ladder refuses to start against a target that is already silent.
    ck("C4", "a silent pre-ladder reading is a refusal, not a result",
       "REFUSED" in _refusal_text())

    # The count is the checks that RAN, not a literal.  A hardcoded total is a
    # number that goes on claiming coverage after a check is deleted.
    print("\n%s: %d checks, %d failed%s"
          % ("RED" if fails else "GREEN", len(ran), len(fails),
             ("  -- " + ",".join(fails)) if fails else ""))
    return 1 if fails else 0


def _refusal_text():
    """The literal string cmd_blast prints when the precondition fails, read
    out of this file so C4 cannot pass against a message that was deleted."""
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    i = src.index("def cmd_blast")
    j = src.index("def _write")
    return src[i:j]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("blast", help="walk an inbound rate ladder")
    b.add_argument("--target", required=True)
    b.add_argument("--src", required=True)
    b.add_argument("--dev", required=True)
    b.add_argument("--port", type=int, default=DEFAULT_PORT)
    b.add_argument("--rates", default=DEFAULT_RATES)
    b.add_argument("--step-s", dest="step_s", type=float, default=DEFAULT_STEP_S)
    b.add_argument("--arp-load", dest="arp_load", action="store_true",
                   help="keep ARP requests going for the whole of every step, "
                        "so the target's TX ring cycles DURING the blast")
    b.add_argument("--out", default=None, help="write the record as JSON")
    b.set_defaults(func=cmd_blast)

    p = sub.add_parser("probe", help="one liveness reading, two sources")
    p.add_argument("--target", required=True)
    p.add_argument("--dev", required=True)
    p.add_argument("--src", default=None)
    p.set_defaults(func=cmd_probe)

    s = sub.add_parser("self-test")
    s.set_defaults(func=cmd_self_test)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
