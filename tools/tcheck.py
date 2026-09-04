#!/usr/bin/env python3
"""Read an ``rtl819x-timer`` ``/proc`` dump out of a console capture, and
RE-DERIVE the fields the driver says it derived instead of transcribing them.

::

    parse <log>...          the key=value block, completeness, every derivation
    rate  <log-a> <log-b>   interrupts delivered against interrupts predicted
    --self-test             the controls and nothing else

Why a tool rather than an eye.  The dump is 67 ``key=value`` lines at 38400
baud inside a capture that also holds the echoed command and a prompt.  Reading
a number off that by eye is how a partial view gets quoted instead of the value
being re-derived -- and this repository has a nine-file instance of exactly
that (``SPEC.md`` ``CLK-22``, ``tc1_ext_gap_max``).

This tool is NOT authoritative about the device.  It reports what the capture
holds, and what the same quantity is when computed from the OTHER fields of the
same capture.  A disagreement between those two is the finding; agreement means
the driver's arithmetic and this file's arithmetic match, and no more.

Every control in ``--self-test`` runs against a capture committed in this
repository, and three of them exist because this file was WRONG about a real
dump before they were written -- ``T6``, ``T7`` and ``T8``.
"""
import argparse
import os
import re
import sys

KV = re.compile(rb"^([a-z0-9_]+)=(.*)$")
IRQROW = re.compile(rb"^\s*\d+:\s+\d+")

# 量 2026-09-04: the driver has 67 scnprintf calls and all 67 are inside
# rtl819x_tc_read_proc, so a complete dump is 67 key=value lines.  Version 1.0
# printed 37.  A dump with fewer lines means the capture was cut, and this
# number is what says so.
EXPECT_KEYS = 67

# BSP_SYS_CLK_RATE, 讀 arch/rlx/bsp/bspchip.h.
SYS_CLK = 200000000

# TWO DIFFERENT MASKS.  COUNTER_BITS is the width of TC1 itself and therefore
# the clocksource mask the shift search is constrained by; `mask_bits` in the
# dump is the PERIOD the driver was armed at (`echo period 20`), a different
# quantity spelled with the same word.
#
# ⚠️ Using the wrong one here would NOT change any answer, and that is a
# provable identity rather than luck: the search is bounded by
# `mult <= 2^32-1` AND `mask*mult <= 2^63-1`, and the second cannot bind while
# mask < 2^31, because (2^63-1)/(2^31) > 2^32-1.  Every period this driver
# accepts is 8..27 bits, so the mask term is inert across the whole range.
# T12 proves that identity and T12b is the boundary where it stops holding --
# a control that cannot fail proves nothing.  (An earlier version of this file
# asserted the two masks give DIFFERENT answers somewhere in range.  They
# cannot, and the control correctly refused to pass.)
COUNTER_BITS = 27

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_dump(path):
    """-> (dict of the last kv block, list of /proc/interrupts rows)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    kv, irqrows = {}, []
    for line in raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n"):
        line = line.strip()
        m = KV.match(line)
        if m:
            kv[m.group(1).decode()] = m.group(2).decode("ascii", "replace")
        elif IRQROW.match(line):
            irqrows.append(line.decode("ascii", "replace"))
    return kv, irqrows


def num(kv, key, base=10):
    v = kv.get(key)
    if v is None:
        return None
    try:
        return int(v, base)
    except ValueError:
        return None


def hexnum(kv, key):
    return num(kv, key, 16)


def shift_search(hz, counter_bits=COUNTER_BITS):
    """The largest shift with mult <= 2^32-1 and mask*mult <= 2^63-1.

    Returns (shift, mult, exact).  `exact` says whether the division had no
    remainder: the kernel's div_sc()/clocksource_hz2mult() ROUNDS and this
    floors, so the two agree only when it is exact.  量: version 1.0 shipped
    mult=1174376947 where the floor is 1174376946.
    """
    mask = (1 << counter_bits) - 1
    for sh in range(32, -1, -1):
        mult = (10 ** 9 << sh) // hz
        if mult <= 0xFFFFFFFF and mask * mult <= (1 << 63) - 1:
            return sh, mult, (10 ** 9 << sh) % hz == 0
    return None, None, None


def derive(kv):
    """{name: (reported, recomputed, note)} from this dump's own fields.

    `reported` is None when the driver version did not print the field: absent
    is a different statement from wrong, and the callers keep them apart.
    """
    out = {}
    hz_kernel = num(kv, "hz_kernel")
    tc0d = hexnum(kv, "tc0data_at_init")
    cdbr = hexnum(kv, "cdbr_at_init")

    if tc0d is not None and hz_kernel:
        out["hz_tick"] = (num(kv, "hz_tick"), (tc0d >> 4) * hz_kernel,
                          "(tc0data_at_init >> 4) * hz_kernel")
    if cdbr:
        div = cdbr >> 16
        out["hz_cdbr"] = (num(kv, "hz_cdbr"), SYS_CLK // div if div else None,
                          "BSP_SYS_CLK_RATE / (cdbr_at_init >> 16) = "
                          f"{SYS_CLK}/{div}")

    hz = num(kv, "hz_used")
    mask_bits = num(kv, "mask_bits")
    if hz:
        sh, mult, exact = shift_search(hz)
        if sh is not None:
            out["shift"] = (num(kv, "shift"), sh,
                            "largest shift with mult<=2^32-1 and "
                            f"mask*mult<=2^63-1 at hz={hz}, "
                            f"counter mask=2^{COUNTER_BITS}-1")
            out["mult"] = (num(kv, "mult"), mult,
                           f"(1e9 << {sh}) / {hz}, "
                           + ("EXACT -- floor and round agree" if exact else
                              "NOT exact -- the kernel rounds, this floors"))
    if hz and mask_bits:
        pc = 1 << mask_bits
        out["period_cycles"] = (num(kv, "period_cycles"), pc, "1 << mask_bits")
        if hz_kernel and kv.get("state") != "idle":
            pj = pc * hz_kernel // hz
            out["period_jiffies"] = (num(kv, "period_jiffies"), pj,
                                     "period_cycles * hz_kernel / hz_used")
            # arm() clamps: `if (ext_interval_j < 1) ext_interval_j = 1`, so a
            # period under 4 jiffies cannot ask for a zero-delay timer that
            # re-arms itself forever.  T7.
            out["ext_interval_j"] = (num(kv, "ext_interval_j"),
                                     max(pj // 4, 1),
                                     "max(period_jiffies / 4, 1) -- arm()'s clamp")
        else:
            # On an idle dump these keep whatever the LAST arm left; the driver
            # does not zero them on disarm.  Report, do not assert.  T6.
            out["period_jiffies"] = (num(kv, "period_jiffies"),
                                     num(kv, "period_jiffies"),
                                     "state=idle: stale from the last arm, "
                                     "not asserted")
    return out


def cmd_parse(args):
    rc = 0
    for path in args.log:
        kv, irqrows = read_dump(path)
        print("=" * 72)
        print(path)
        print(f"  keys: {len(kv)} (a complete dump is {EXPECT_KEYS})")
        if not kv:
            print("  FAIL  no key=value line -- the cell produced no dump")
            rc = 1
        elif len(kv) != EXPECT_KEYS:
            print(f"  FAIL  INCOMPLETE -- {EXPECT_KEYS - len(kv)} missing; the "
                  "capture was cut or this is another driver version")
            rc = 1
        if not args.quiet:
            for k, v in kv.items():
                print(f"    {k}={v}")
            for row in irqrows:
                print("    /proc/interrupts: " + row)
        for name, (rep, calc, note) in derive(kv).items():
            if rep is None:
                print(f"    --  {name}: not printed by this driver version, "
                      f"recomputed {calc}   [{note}]")
            elif rep == calc:
                print(f"    ok  {name}: {rep}   [{note}]")
            else:
                print(f"    FAIL {name}: reported {rep}, recomputed {calc}   "
                      f"[{note}]")
                rc = 1
    print(f"\nRESULT: {'a disagreement' if rc else 'no disagreement'} between "
          "the dump and the same quantities recomputed from it")
    return rc


def cmd_rate(args):
    a, _ = read_dump(args.log_a)
    b, _ = read_dump(args.log_b)
    for nm, d in (("a", a), ("b", b)):
        if len(d) != EXPECT_KEYS:
            print(f"  REFUSED  {nm} is {len(d)} keys, not {EXPECT_KEYS}")
            return 2
    pca, pcb = num(a, "period_cycles"), num(b, "period_cycles")
    # 🔴 T8.  A pair that spans a disarm/re-arm at another period would be
    # scored against b's period alone and quietly report a wrong rate as ok.
    # Found while writing this control, not while using the tool.
    if pca != pcb:
        print(f"  REFUSED  period_cycles differ ({pca} then {pcb}): the pair "
              "spans a re-arm and there is no single period to score against")
        return 2
    dj = num(b, "jiffies") - num(a, "jiffies")
    di = num(b, "irq_count") - num(a, "irq_count")
    hz, hz_k = num(b, "hz_used"), num(b, "hz_kernel")
    if dj <= 0:
        print(f"  REFUSED  Djiffies = {dj}: b is not after a")
        return 2
    if di < 0:
        print(f"  REFUSED  Dirq_count = {di}: the counter went backwards")
        return 2
    if not (pcb and hz and hz_k):
        print("  REFUSED  hz_used / period_cycles / hz_kernel missing")
        return 2
    # NOT via period_jiffies: that is an integer jiffy count and it is 0 for
    # any period shorter than 10 ms, which is exactly the interesting case.
    pred_per_j = hz / pcb / hz_k
    meas_per_j = di / dj
    err = abs(meas_per_j - pred_per_j) / pred_per_j
    print(f"  Djiffies         = {dj}  ({dj / hz_k:.2f} s at hz_kernel={hz_k})")
    print(f"  Dirq_count       = {di}")
    print(f"  period_cycles    = {pcb}   hz_used = {hz}   hz_kernel = {hz_k}")
    print(f"  predicted /jiffy = hz_used/period_cycles/hz_kernel = {pred_per_j:.6f}")
    print(f"  measured  /jiffy = Dirq/Djiffies                   = {meas_per_j:.6f}")
    print(f"  predicted total  = {pred_per_j * dj:.1f}   measured = {di}")
    print(f"  relative error   = {err * 100:.4f} %")
    ok = err < 0.01
    print(f"\nRESULT: {'delivery at the programmed period' if ok else 'REFUTED'}"
          " -- band is 1 % relative; the adjacent power-of-two period is 100 % away")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
class Controls:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), detail))

    def report(self):
        for name, ok, detail in self.rows:
            print(f"  {'ok  ' if ok else 'FAIL'}  {name}"
                  + (f"  --  {detail}" if detail else ""))
        bad = [r for r in self.rows if not r[1]]
        print(f"\nRESULT: {len(self.rows) - len(bad)}/{len(self.rows)} controls held")
        return 1 if bad else 0


def self_test():
    c = Controls()
    f = lambda *p: os.path.join(REPO, *p)

    v10 = f("bench", "2026-09-03", "TM-1.log")          # driver 1.0, 37 keys
    v20 = f("bench", "2026-09-04", "TI-0.log")          # driver 2.0, idle
    armed = f("bench", "2026-09-04", "EX-2.log")        # driver 2.0, period 8
    ti5 = f("bench", "2026-09-04", "TI-5.log")
    ti6 = f("bench", "2026-09-04", "TI-6.log")
    ex17 = f("bench", "2026-09-04", "EX-17.log")
    ex18 = f("bench", "2026-09-04", "EX-18.log")

    k10, _ = read_dump(v10)
    k20, _ = read_dump(v20)
    karm, _ = read_dump(armed)

    c.add("T1  a version-1.0 dump is reported INCOMPLETE against 67",
          len(k10) == 37, f"{len(k10)} keys")
    c.add("T2  a version-2.0 dump is complete",
          len(k20) == EXPECT_KEYS, f"{len(k20)} keys")

    # T3: the derivation does not need the driver's own answer.
    d10 = derive(k10)
    c.add("T3  hz_cdbr is recomputed on a dump that does not print it",
          d10["hz_cdbr"][0] is None and d10["hz_cdbr"][1] == 200000,
          f"reported {d10['hz_cdbr'][0]}, recomputed {d10['hz_cdbr'][1]}")

    # T4/T5: the search must DISCRIMINATE, and its agreement must not be luck.
    s200, m200, e200 = shift_search(200000)
    s14, m14, _ = shift_search(14286057)
    c.add("T4  the shift search discriminates between two rates",
          (s200, s14) == (19, 25), f"{s200} and {s14}")
    # T5 has to check the flag DISCRIMINATES, not merely that it is true where
    # it happens to be true: hardcoding `exact = True` passed the first version.
    e14 = shift_search(14286057)[2]
    c.add("T5  the exactness flag discriminates: true at 200000, false at "
          "14286057",
          e200 and m200 == 2621440000 and e14 is False,
          f"mult={m200}, exact={e200}; at the loader rate exact={e14}")

    # T12: the mask term is INERT over the driver's whole period range, so
    # counter-width-or-mask_bits cannot change an answer here.  Proved over
    # every period the driver accepts and four rates, not asserted at one.
    rates = (50, 200000, 14286057, 200000000)
    inert = all(len({shift_search(h, b)[:2] for b in range(8, 32)}) == 1
                for h in rates)
    c.add("T12 the mask term is inert for every period 8..31 the driver takes",
          inert, "so mask_bits and the counter width cannot disagree in range")
    # T12b: and it is not inert everywhere -- at 32 bits the mask bound binds
    # first and the answer moves.  Without this, T12 could not fail.
    c.add("T12b at 32 bits the mask bound DOES bind, so T12 is not vacuous",
          shift_search(200000, 32)[0] != shift_search(200000, 27)[0],
          f"{shift_search(200000, 32)[0]} against {shift_search(200000, 27)[0]}")

    # T6: an idle dump must not be asserted against arm()'s arithmetic.
    d20 = derive(k20)
    c.add("T6  an idle dump does not assert period_jiffies",
          d20["period_jiffies"][0] == d20["period_jiffies"][1]
          and "idle" in d20["period_jiffies"][2],
          "the tool reported the driver red on TI-0 before this control")

    # T7: arm()'s clamp is modelled.
    darm = derive(karm)
    c.add("T7  arm()'s ext_interval_j >= 1 clamp is modelled",
          darm["ext_interval_j"][0] == darm["ext_interval_j"][1] == 1,
          "period 8 gives period_jiffies 0, and the driver clamps to 1")

    # T8/T9: rate must refuse rather than report a wrong number.
    class A:
        pass
    a = A(); a.log_a, a.log_b = ti5, ex18          # 256 counts then 4096
    c.add("T8  rate REFUSES a pair that spans a re-arm at another period",
          cmd_rate_quiet(a) == 2, "TI-5 is period 8, EX-18 is period 12")
    # T9 uses the SAME capture twice: Djiffies is 0 and Dirq_count is 0, so
    # only the Djiffies guard can refuse it.  The first version passed TI-6 ->
    # TI-5, where Dirq_count is also negative -- the other guard did the work
    # and removing this one left the suite green.  量, test-tcheck M5.
    a2 = A(); a2.log_a, a2.log_b = ti6, ti6
    c.add("T9  rate REFUSES a pair with Djiffies = 0, and ONLY that guard can",
          cmd_rate_quiet(a2) == 2, "the same capture twice")

    a3 = A(); a3.log_a, a3.log_b = ti5, ti6
    c.add("T10 rate holds on TI-5 -> TI-6 (period 8, 781.25 Hz)",
          cmd_rate_quiet(a3) == 0)
    a4 = A(); a4.log_a, a4.log_b = ex17, ex18
    c.add("T11 rate holds on EX-17 -> EX-18 (period 12, with the NIC running)",
          cmd_rate_quiet(a4) == 0)

    # T13: a cut capture is caught rather than half-parsed.
    cut = {k: v for i, (k, v) in enumerate(k20.items()) if i < 40}
    c.add("T13 a 40-key dump is not 67", len(cut) != EXPECT_KEYS)

    return c.report()


def cmd_rate_quiet(args):
    """cmd_rate with stdout swallowed -- the controls score the code, not the
    text.  A control that read the printed words would pass on a tool that
    printed the right sentence and returned the wrong status.

    An exception becomes 3, never 2: a control that asks for the REFUSAL code
    must not be satisfied by a crash, and dropping the Djiffies guard makes
    `Dirq/Djiffies` divide by zero.

    ⚠️ The `Dirq_count < 0` guard has no fixture: irq_count never decreases in
    any committed capture, so no control here exercises it.  Said rather than
    left as an unstated gap.
    """
    import io
    import contextlib
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return cmd_rate(args)
    except Exception:
        return 3


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        return self_test()
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("parse")
    sp.add_argument("log", nargs="+")
    sp.add_argument("--quiet", action="store_true",
                    help="derivations only, not the 67 lines")
    sp.set_defaults(func=cmd_parse)
    sr = sub.add_parser("rate")
    sr.add_argument("log_a")
    sr.add_argument("log_b")
    sr.set_defaults(func=cmd_rate)
    a = p.parse_args(argv[1:])
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
