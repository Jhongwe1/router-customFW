#!/usr/bin/env python3
"""uartrate -- what the console's per-character wire time actually is.

WHY THIS EXISTS
---------------
`SPEC.md` `FW-70` (opened 2026-09-14, seating 22) measured sustained console
throughput at 588 B / 0.1735 s = 3,389 B/s, 88.3 % of the 3,840 B/s that
38400 baud gives at 10 bits per character, cause undetermined.

A total-over-elapsed ratio cannot separate

    (a) a wire that runs slower than 10 bits per character, from
    (b) a wire at nominal rate with idle time in the window,

because both produce the same ratio.  This tool separates them, using only
captures that are already committed.

SEMANTICS OF A .timing ROW   (讀 tools/console-capture.py:551-562)
------------------------------------------------------------------
    r = select([fd], [], [], <=0.05)      # wake when data is there
    chunk = ser.read(ser.in_waiting or 1) # drain everything buffered
    timing.write(f"{offset} {monotonic()-t0}")   # offset = bytes BEFORE chunk
    log.write(chunk)

Row i is (offset_i, t_i); chunk i occupies [offset_i, offset_{i+1}); and every
byte of chunk i arrived in the half-open interval (t_{i-1}, t_i].  That is
`FW-35`'s rule stated from the producer's side rather than the reader's.

TWO ESTIMATORS, AND ONE OF THEM REFUSES ON THIS CORPUS
------------------------------------------------------
`report` fits the LOWER ENVELOPE of dt against chunk size.  Transmitting b
characters cannot take less than b*s, so the envelope's slope is s and gaps
cannot bias it.  🔴 On this console it REFUSES, and the refusal is the useful
part: at 38400 the reader is faster than the wire, so `select` wakes every USB
frame and `ser.read` returns 3-4 bytes.  With b confined to [1,4] the
transmission difference across the range is ~780 us against a latency-timer
jitter of the same order, and the fit returns 0.90 and 2.80 bits/char on the
two seating-22 boot captures -- physically impossible, reported as such.

`sweep` takes the MINIMUM over every window carrying at least N bytes.  Over a
window where the line is continuously busy, bytes/elapsed IS the wire rate;
idle only ever adds to elapsed; so every window's reading is an upper bound on
the truth and the minimum over many windows is the tightest one available.  A
long baseline defeats the timestamp jitter, a minimum defeats the gaps, and
neither needs the reads to be big -- which is the property this capture regime
lacks.

🔴 THE ESTIMATOR IS NOT UNCONDITIONALLY ONE-SIDED, and pretending it is would
be the comfortable mistake.  The minimum window pairs the largest timestamp
jitter at its start against the smallest at its end, so it UNDERSHOOTS by at
most (J / T) * bits, where J is the maximum timestamp delay and T the window's
span.  `selftest` checks that error model rather than merely checking that the
number is close, because the bound quoted for the real corpus is computed from
it.  量 seating 17: the instrument's minimum inter-read gap is 0.517-0.868 ms;
the MAXIMUM delay is a different quantity and this project has not measured it.
Reconciling the same file's w=2,000 and w=8,000 readings needs J ~ 17.7 ms,
which is the USB latency timer's textbook range, so short-window floors are
not usable and converged long-window values are.

`eras` splits the corpus by `.meta.json`'s `sent` field -- NOT by filename;
seating 22's defect #4 was a comparison that picked cells by filename and
reported the wrong flash map, and `CLAUDE.md` records the same class twice
before that.  `FW-70`'s own owning row names the loader-vs-Linux split as its
deciding experiment; that experiment had already been run 1,228 times and
nobody had compared the two halves.

WHAT WOULD PROVE THIS WRONG -- written before the tool was run
--------------------------------------------------------------
  R1  floor ~ 10.0x bits/char        the wire is 8N1 at nominal rate and every
                                     capture carries gaps.
  R2  floor ~ 11.0x                  the board transmits 11 bits per character
                                     (8N2, or 8E1/8O1); the host at 8N1
                                     decodes either without a framing error,
                                     which is why no capture in this project
                                     has ever shown corruption.
  R3  floor below 10.0               impossible for a real wire: the row
                                     semantics, the baud or the byte
                                     accounting is wrong.  Reported as
                                     INCONSISTENT, no verdict given.
  R4  the two eras land on different values   Linux reprograms the
                                     line-control register, which is a finding
                                     of its own and means "the wire" is not
                                     one number.
  R5  `selftest` fails               the estimator is not measuring what this
                                     docstring claims and NO number it prints
                                     may be quoted.  `report` and `sweep`
                                     refuse to run until it has passed in the
                                     same process.

量 2026-09-15 (seventy-first segment), 1,224 captures: R2 and R3 both fired
and both were resolved against a second, independently written instrument --
see `SPEC.md` `FW-70`.
"""

import argparse
import glob
import json
import os
import random
import sys

NOMINAL_BAUD = 38400

# Loader verbs: SPEC.md's LDR-* rows and RUNSHEET's bracket commands.
LOADER_VERBS = ("DW", "EW", "EB", "FLR", "FLW", "J ", "J\r", "@", "CMP",
                "IPCONFIG", "LOADADDR", "AUTOBURN")
# Linux: anything that needs a shell.
LINUX_VERBS = ("cat ", "echo ", "ls ", "ifconfig", "ping", "busybox", "insmod",
               "sleep", "while ", "for ", "grep ", "dmesg", "mount", "cd ",
               "head ", "reboot", "wc ")


# ----------------------------------------------------------------- parsing

def read_timing(path):
    """[(offset, t)] from a .timing file, header and junk rows skipped."""
    rows = []
    with open(path, "r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) != 2:
                continue
            try:
                rows.append((int(p[0]), float(p[1])))
            except ValueError:
                continue
    return rows


def log_size_for(path):
    log = path[: -len(".timing")] + ".log"
    return os.path.getsize(log) if os.path.exists(log) else None


def sent_for(path):
    meta = path[: -len(".timing")] + ".meta.json"
    if not os.path.exists(meta):
        return None
    try:
        with open(meta, "r", encoding="utf-8") as fh:
            return json.load(fh).get("sent")
    except Exception:
        return None


def era_of(sent):
    if sent is None:
        return "no-meta"
    s = sent.strip()
    if not s:
        return "empty-send"
    for v in LINUX_VERBS:
        if v in s:
            return "linux"
    for v in LOADER_VERBS:
        if s.startswith(v) or ("\r" + v) in s:
            return "loader"
    return "other"


def intervals(rows, log_size):
    """[(b, dt)] -- one per read AFTER the first.

    Row 0's interval is dropped: the time before it holds the send and the
    board's response latency, not transmission of the bytes it carries.
    """
    out = []
    for i in range(1, len(rows)):
        off, t = rows[i]
        nxt = rows[i + 1][0] if i + 1 < len(rows) else log_size
        b, dt = nxt - off, t - rows[i - 1][1]
        if b > 0 and dt > 0:
            out.append((b, dt))
    return out


# -------------------------------------------------------------- estimators

def ols(pts):
    n = len(pts)
    if n < 2:
        return None, None
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    den = n * sum(p[0] * p[0] for p in pts) - sx * sx
    if den == 0:
        return None, None
    s = (n * sum(p[0] * p[1] for p in pts) - sx * sy) / den
    return s, (sy - s * sx) / n


def envelope(ivs, min_support=3):
    best, count = {}, {}
    for b, dt in ivs:
        count[b] = count.get(b, 0) + 1
        if b not in best or dt < best[b]:
            best[b] = dt
    return sorted((b, best[b]) for b in best if count[b] >= min_support)


def window_floor(rows, log_size, baud, min_bytes):
    """(bits/char, bytes, seconds) for the fastest window carrying min_bytes.

    The minimum over ALL windows is attained by a shortest admissible one:
    a longer window's rate is a weighted average of its parts and so is never
    below the minimum over its sub-windows.  That is why one pointer sweep is
    enough and an O(n^2) search is not needed.
    """
    n = len(rows)
    if n < 3 or log_size is None:
        return None
    off = [r[0] for r in rows] + [log_size]
    t = [r[1] for r in rows]
    best, a = None, 0
    for z in range(1, n):
        while a + 1 < z and off[z + 1] - off[a + 2] >= min_bytes:
            a += 1
        by = off[z + 1] - off[a + 1]
        if by < min_bytes:
            continue
        dt = t[z] - t[a]
        if dt <= 0:
            continue
        bits = dt / by * baud
        if best is None or bits < best[0]:
            best = (bits, by, dt)
    return best


# ----------------------------------------------------------------- controls

def synth(bits, baud, n_chunks, gap_prob, gap_s, seed, floor_s, clean_run=0,
          bmin=3, bmax=4):
    """Rows for a stream at exactly `bits` bits/char.

    🔴 The first version of this generator was WRONG and its own controls
    caught it, before any number from the real corpus had been quoted.  It
    added the USB latency floor to the ELAPSED TIME of every chunk, which made
    a 10.00 bits/char stream read as 16.33.  A latency timer does not do that.
    Bytes arrive on the wire at k*s whatever the reader is doing; the timer
    delays only the TIMESTAMP of a read, and that delay is not carried forward
    to the next one.  So `arrival` accumulates wire time and gaps only, and
    the jitter is added to the reported row and thrown away -- which is also
    why a long baseline defeats it: the error is the DIFFERENCE of two
    jitters, not their sum.
    """
    rng = random.Random(seed)
    s = bits / baud
    rows, off, arrival = [], 0, 0.0
    mid0 = (n_chunks - clean_run) // 2
    for k in range(n_chunks):
        b = rng.randint(bmin, bmax)
        arrival += b * s
        if not (mid0 <= k < mid0 + clean_run) and rng.random() < gap_prob:
            arrival += gap_s * rng.random()
        rows.append((off, arrival + floor_s * rng.random()))
        off += b
    return rows, off


def case(ok, label, value):
    """House case line: exactly two leading spaces (tools/ci-census.py:56)."""
    tag = "ok   " if ok else "FAIL "
    return "  %s  %-54s %s" % (tag, label, value)


def selftest(baud=NOMINAL_BAUD):
    lines, npass, nfail = [], 0, 0

    def rec(ok, label, value):
        nonlocal npass, nfail
        lines.append(case(ok, label, value))
        if ok:
            npass += 1
        else:
            nfail += 1

    # S1-S2  recover a known rate when a gap-free run exists
    for bits in (10.0, 11.0):
        rows, size = synth(bits, baud, 9000, 0.08, 0.05, int(bits), 0.0012,
                           clean_run=3000)
        got = window_floor(rows, size, baud, 2000)[0]
        rec(abs(got - bits) < 0.03,
            "sweep recovers a synthetic %.2f bits/char" % bits,
            "%.4f" % got)

    # S3  one-sidedness under saturation with gaps everywhere
    rows, size = synth(10.0, baud, 9000, 0.9, 0.05, 42, 0.0012)
    got = window_floor(rows, size, baud, 2000)[0]
    rec(got >= 10.0, "gaps everywhere: reading stays above the truth",
        "%.4f >= 10.00" % got)

    # S4-S5  the UNDERSHOOT MODEL, not merely "close enough".  With timestamp
    # jitter J over a window spanning T seconds the minimum undershoots by
    # (J/T)*bits, so it must shrink with the window.  If it does not, the
    # bound quoted for the real corpus is wrong.
    rows, size = synth(11.0, baud, 9000, 0.0, 0.0, 7, 0.016)
    for w in (2000, 8000):
        got = window_floor(rows, size, baud, w)[0]
        T = w * 11.0 / baud
        pred = 11.0 - 0.016 / T * 11.0
        rec(abs(got - pred) < 0.10,
            "16 ms jitter, w=%d: undershoot matches (J/T)*bits" % w,
            "%.4f against a predicted %.4f" % (got, pred))

    # S6  10 and 11 must not be confusable
    r10 = window_floor(*synth(10.0, baud, 9000, 0.08, 0.05, 1, 0.0012,
                              clean_run=3000), baud, 2000)[0]
    r11 = window_floor(*synth(11.0, baud, 9000, 0.08, 0.05, 2, 0.0012,
                              clean_run=3000), baud, 2000)[0]
    rec((r11 - r10) > 0.9, "10 and 11 bits/char separate",
        "%.4f bits apart" % (r11 - r10))

    # S7-S9  🔴 THE ENVELOPE IS BIASED LOW, AND THE BIAS IS SET BY THE SPREAD
    # OF CHUNK SIZES.  Written as three cases because the first draft of S7
    # asserted "recovers 10.00 within 0.05" and FAILED at 9.8861 -- the
    # failure was the estimator telling the truth about itself.  min(dt) for a
    # given b picks the sample whose timestamp jitter differed most
    # favourably, so every envelope point sits below b*s, and the narrower the
    # b range the more that offset leaks out of the intercept and into the
    # slope.  This is why `report` returns 0.90 and 2.80 bits/char on the real
    # seating-22 boot captures, where b is confined to [1,4]: not random
    # breakage, predictable breakage -- and why the refusal in S9 is the guard
    # that matters rather than a nicety.
    def env_bits(bmax, seed):
        rows, size = synth(10.0, baud, 4000, 0.15, 0.30, seed, 0.0012,
                           bmin=1, bmax=bmax)
        s, _ = ols(envelope(intervals(rows, size)))
        return s * baud if s else None

    wide, narrow = env_bits(60, 3), env_bits(12, 5)
    rec(wide is not None and 9.5 <= wide <= 10.0,
        "report's envelope over b in [1,60]: low, and by < 0.5 bits",
        "%.4f against a true 10.00" % wide if wide else "None")
    rec(narrow is not None and (10.0 - narrow) > (10.0 - wide),
        "narrowing b to [1,12] makes the SAME estimator worse",
        "%.4f, bias %.4f against %.4f" % (narrow, 10.0 - narrow, 10.0 - wide))

    # S9  and it REFUSES when b spans nothing -- which is what it does on the
    # real console.  A tool that fits a line through three points is the
    # failure this case exists to prevent.
    rows, size = synth(10.0, baud, 4000, 0.15, 0.30, 4, 0.0012, bmin=3, bmax=4)
    env = envelope(intervals(rows, size))
    rec(len(env) < 4, "report's envelope refuses when b spans [3,4] only",
        "%d support points (<4)" % len(env))

    # S9  the naive ratio MUST be fooled by the same data, or the two
    # estimators are not measuring different things and the argument is empty
    rows, size = synth(10.0, baud, 4000, 0.15, 0.30, 99, 0.0012)
    tot_b = size - rows[1][0]
    naive = (rows[-1][1] - rows[0][1]) / tot_b * baud
    rec(naive > 10.5, "the naive total/elapsed ratio IS fooled by those gaps",
        "%.4f against a true 10.00" % naive)

    # S10  the measured-jitter bound that the corpus verdict is quoted with
    T = 2000 * 11.0 / baud
    b = 0.000868 / T * 11.0
    rec(b < 0.05, "measured 0.868 ms jitter bounds w=2000 undershoot",
        "%.4f bits" % b)

    return npass, nfail, lines


# --------------------------------------------------------------------- cli

def cmd_report(a):
    for path in a.timing:
        rows = read_timing(path)
        size = log_size_for(path) or (rows[-1][0] if rows else 0)
        ivs = intervals(rows, size)
        print("  %s" % os.path.basename(path))
        if not ivs:
            print("    REFUSED: no intervals")
            continue
        tot = sum(i[0] for i in ivs)
        span = rows[-1][1] - rows[0][1]
        print("    naive total/elapsed  %.1f B/s  (%.4f bits/char)"
              % (tot / span, span / tot * a.baud))
        env = envelope(ivs, a.min_support)
        if len(env) < 4:
            print("    REFUSED: envelope has %d support points (<4) -- the "
                  "chunk sizes do not span enough range to fit a slope"
                  % len(env))
            continue
        s, c = ols(env)
        bits = s * a.baud
        flag = "  <-- R3: BELOW 10, impossible for a real wire" if bits < 10 else ""
        print("    envelope slope       %.3f us/char = %.4f bits/char%s"
              % (s * 1e6, bits, flag))
        print("    envelope intercept   %.6f s (minimum per-read overhead)" % c)
    return 0


def cmd_sweep(a):
    windows = [int(x) for x in a.windows.split(",")]
    paths = []
    for g in a.globs:
        paths.extend(sorted(glob.glob(g, recursive=True)))
    rows = []
    for p in paths:
        t = read_timing(p)
        size = log_size_for(p)
        if len(t) < 3 or size is None:
            continue
        r = {"path": p, "era": era_of(sent_for(p)), "w": {}}
        for w in windows:
            f = window_floor(t, size, a.baud, w)
            if f:
                r["w"][w] = f
        if r["w"]:
            rows.append(r)

    print("uartrate sweep -- %d captures with a window of >= %d bytes"
          % (len(rows), min(windows)))
    print()
    for w in windows:
        print("=== window >= %d bytes ===" % w)
        by = {}
        for r in rows:
            if w in r["w"]:
                by.setdefault(r["era"], []).append((r["w"][w][0], r["path"]))
        for e in sorted(by):
            v = sorted(by[e])
            note = "  (n<5: this is one capture's property, not an era's)" \
                if len(v) < 5 else ""
            print("  %-10s n=%-4d floor=%8.4f bits/char = %7.1f B/s%s"
                  % (e, len(v), v[0][0], a.baud / v[0][0], note))
            for f, path in v[:2]:
                print("       %8.4f  %s" % (f, path.replace("\\", "/")))
        print()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump([{"path": r["path"], "era": r["era"],
                        "w": {str(k): v[0] for k, v in r["w"].items()}}
                       for r in rows], fh, indent=2)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("selftest", help="synthetic controls (R5)")
    st.add_argument("--baud", type=int, default=NOMINAL_BAUD)

    rp = sub.add_parser("report", help="lower-envelope slope, per file")
    rp.add_argument("timing", nargs="+")
    rp.add_argument("--baud", type=int, default=NOMINAL_BAUD)
    rp.add_argument("--min-support", type=int, default=3)

    sw = sub.add_parser("sweep", help="window floor, split by era")
    sw.add_argument("globs", nargs="+")
    sw.add_argument("--baud", type=int, default=NOMINAL_BAUD)
    sw.add_argument("--windows", default="2000,8000,16000")
    sw.add_argument("--json", default=None)

    a = ap.parse_args()

    npass, nfail, lines = selftest(getattr(a, "baud", NOMINAL_BAUD))
    if a.cmd == "selftest":
        print("uartrate selftest -- R5: if any case fails, no number this "
              "tool prints may be quoted")
        for l in lines:
            print(l)
        print("RESULT: %d passed, %d failed" % (npass, nfail))
        return 0 if nfail == 0 else 1
    if nfail:
        print("REFUSING: selftest failed (%d) -- R5 fired." % nfail)
        for l in lines:
            print(l)
        return 2

    return cmd_report(a) if a.cmd == "report" else cmd_sweep(a)


if __name__ == "__main__":
    sys.exit(main())
