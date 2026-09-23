#!/usr/bin/env python3
"""clockshim.py -- run a Python tool with CLOCK_MONOTONIC made to disagree with RAW.

WHY IT EXISTS
-------------
Seating B stamps every capture and probe on CLOCK_MONOTONIC_RAW, because WSL's
CLOCK_MONOTONIC is slewed percent-slow while two time daemons fight (SPEC.md
CLK-38).  A test of "this tool stamps RAW" has to be able to fail, and on a CI
runner the two clocks agree to a few milliseconds, so a tool that still read
CLOCK_MONOTONIC would pass every bracket a harness could draw there.  Two
counters agreeing is not evidence while they run at the same rate (CLAUDE.md);
this makes the rates differ.

WHAT IT DOES
------------
    clockshim.py [--rate R] [--offset S] -- TOOL.py [ARGS...]

runs TOOL.py in this process (runpy, as __main__, with sys.argv set to the
tool's own) after patching, inside this process only, every Python-level read
of CLOCK_MONOTONIC to return  offset + rate * (true monotonic):
time.monotonic, time.monotonic_ns, time.perf_counter, time.perf_counter_ns,
and time.clock_gettime / clock_gettime_ns when asked for CLOCK_MONOTONIC.
CLOCK_MONOTONIC_RAW, CLOCK_REALTIME and every other clock pass through.

What it cannot reach, by construction: the kernel's own timers (select, sleep,
poll timeouts run on the real CLOCK_MONOTONIC) and any child process.  A test
built on it asserts stamps and durations, not how long a kernel wait lasted.

Refusals, each before the tool runs: no TOOL, a TOOL that is not a file, a
rate outside (0, 1) (a shim that does not slow the clock is not a control),
and a patch that did not take -- the patched and true monotonic differing by
less than 90 % of --offset -- which exits 3 rather than run the tool
unshimmed.  --self-test checks the patch, the pass-through and each refusal.
"""
import argparse
import os
import runpy
import sys
import time

TOOL_VERSION = "1.0"


class Refused(Exception):
    pass


def install(rate, offset):
    """Patch the monotonic readers; return the true readers for the check."""
    true_mono, true_mono_ns = time.monotonic, time.monotonic_ns
    true_get, true_get_ns = time.clock_gettime, time.clock_gettime_ns
    base_ns = true_mono_ns()
    base = base_ns / 1e9

    def mono():
        return offset + base + rate * (true_mono() - base)

    def mono_ns():
        return int(offset * 1e9) + base_ns + int(rate * (true_mono_ns() - base_ns))

    def get(cid):
        return mono() if cid == time.CLOCK_MONOTONIC else true_get(cid)

    def get_ns(cid):
        return mono_ns() if cid == time.CLOCK_MONOTONIC else true_get_ns(cid)

    time.monotonic, time.monotonic_ns = mono, mono_ns
    time.perf_counter, time.perf_counter_ns = mono, mono_ns
    time.clock_gettime, time.clock_gettime_ns = get, get_ns
    return true_mono


def check(true_mono, offset):
    gap = time.monotonic() - true_mono()
    if gap < 0.9 * offset:
        raise Refused("the patch did not take: patched minus true monotonic is %.3f s, "
                      "want >= %.3f" % (gap, 0.9 * offset))
    return gap


def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rate", type=float, default=0.5)
    ap.add_argument("--offset", type=float, default=1000.0)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("tool", nargs="?")
    ap.add_argument("args", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    if a.args and a.args[0] == "--":
        a.args = a.args[1:]
    return a


def refuse_platform():
    if getattr(time, "CLOCK_MONOTONIC_RAW", None) is None:
        raise Refused("this platform's Python has no time.CLOCK_MONOTONIC_RAW (Linux "
                      "only); the shim exists to make MONOTONIC disagree with it")


def refuse_args(a):
    refuse_platform()
    if not a.rate > 0 or not a.rate < 1:
        raise Refused("--rate %r: must lie strictly between 0 and 1, or the shim does not "
                      "make the clocks disagree" % a.rate)
    if not a.offset >= 10:
        raise Refused("--offset %r: must be at least 10 s, so no harness bracket can "
                      "straddle it" % a.offset)
    if not a.tool:
        raise Refused("no TOOL given")
    if not os.path.isfile(a.tool):
        raise Refused("TOOL %r is not a file" % a.tool)


def selftest():
    try:
        refuse_platform()
    except Refused as e:
        print("clockshim --self-test: %s" % e, file=sys.stderr)
        return 2
    ok, bad = [], []

    def case(cid, what, fn):
        try:
            fn()
        except AssertionError as e:
            bad.append((cid, what, str(e)))
        except Exception as e:                                   # noqa: BLE001
            bad.append((cid, what, "%s: %s" % (type(e).__name__, e)))
        else:
            ok.append((cid, what))

    import subprocess
    here = os.path.abspath(__file__)
    # The reference is CLOCK_BOOTTIME, not RAW: BOOTTIME runs at MONOTONIC's
    # rate and the shim does not touch it, while MONOTONIC - RAW on a slewed
    # host is itself minutes (量 2026-09-23: -189 s, CLK-38) -- a check against
    # RAW failed there, on exactly the host this tool exists for.
    probe = ("import time, sys; B = time.CLOCK_BOOTTIME; "
             "m = time.monotonic(); b = time.clock_gettime(B); "
             "cm = time.clock_gettime(time.CLOCK_MONOTONIC); "
             "t0 = time.monotonic(); b0 = time.clock_gettime(B); "
             "time.sleep(0.2); "
             "print(m - b, cm - b, (time.monotonic() - t0) / "
             "(time.clock_gettime(B) - b0))")

    def run(args, code=probe, tmp=[None]):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "probe.py")
            with open(p, "w") as fh:
                fh.write(code)
            return subprocess.run([sys.executable, here] + args + ["--", p],
                                  capture_output=True, text=True)

    def s1():
        r = run(["--rate", "0.5", "--offset", "1000"])
        assert r.returncode == 0, (r.returncode, r.stderr)
        mono_minus_boot, get_minus_boot, ratio = map(float, r.stdout.split())
        assert mono_minus_boot > 900, mono_minus_boot
        assert get_minus_boot > 900, ("clock_gettime(CLOCK_MONOTONIC) is patched too",
                                      get_minus_boot)
        assert 0.49 < ratio < 0.51, ("monotonic runs at the rate given", ratio)
    case("S1", "monotonic, clock_gettime(MONOTONIC) and the rate are patched", s1)

    def s2():
        code = ("import time; r1 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW); "
                "w1 = time.time(); import subprocess, sys; "
                "print(r1, w1)")
        r = run([], code=code)
        assert r.returncode == 0, (r.returncode, r.stderr)
        r1, w1 = map(float, r.stdout.split())
        assert abs(r1 - time.clock_gettime(time.CLOCK_MONOTONIC_RAW)) < 30, (
            "RAW passes through unshifted", r1)
        assert abs(w1 - time.time()) < 30, ("REALTIME passes through", w1)
    case("S2", "CLOCK_MONOTONIC_RAW and REALTIME pass through untouched", s2)

    def s3():
        for args, want in ((["--rate", "1.0"], "strictly between"),
                           (["--rate", "0"], "strictly between"),
                           (["--offset", "5"], "at least 10"),):
            r = run(args)
            assert r.returncode == 2 and want in r.stderr, (args, r.returncode, r.stderr)
        r = subprocess.run([sys.executable, here, "--", "/nonexistent/tool.py"],
                           capture_output=True, text=True)
        assert r.returncode == 2 and "is not a file" in r.stderr, (r.returncode, r.stderr)
    case("S3", "each refusal exits 2 with its reason, before the tool runs", s3)

    def s4():
        # the check itself must be able to fail: an offset the patch never applied
        true_mono = time.monotonic
        try:
            check(true_mono, 1000.0)
        except Refused:
            return
        raise AssertionError("check() passed an unpatched clock")
    case("S4", "negative control: check() refuses a clock that was not patched", s4)

    def s5():
        r = run(["--rate", "0.5"], code="import sys; sys.exit(7)")
        assert r.returncode == 7, ("the tool's own exit status passes through", r.returncode)
    case("S5", "the tool's exit status is the shim's", s5)

    for cid, what in ok:
        print("  ok   %-3s %s" % (cid, what))
    for cid, what, why in bad:
        print("  FAIL %-3s %s -- %s" % (cid, what, why))
    print("RESULT: %d/%d" % (len(ok), len(ok) + len(bad)))
    return 1 if bad else 0


def main(argv=None):
    a = parse(sys.argv[1:] if argv is None else argv)
    if a.self_test:
        return selftest()
    try:
        refuse_args(a)
    except Refused as e:
        print("clockshim: %s" % e, file=sys.stderr)
        return 2
    true_mono = install(a.rate, a.offset)
    try:
        check(true_mono, a.offset)
    except Refused as e:
        print("clockshim: %s" % e, file=sys.stderr)
        return 3
    sys.argv = [a.tool] + list(a.args)
    sys.path.insert(0, os.path.dirname(os.path.abspath(a.tool)))
    try:
        runpy.run_path(a.tool, run_name="__main__")
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
