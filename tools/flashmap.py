#!/usr/bin/env python3
"""The desk half of ``rtl819x-spi``'s ``map`` verb: predict it, then compare.

Why this exists
---------------
``FLS-26``, 量 2026-09-08: ``verify`` found the first difference between this
unit's flash and the 2026-08-16 dump at ``[0x9000,0xA000)`` and could find
nothing past it, because a PREFIX digest stops at the first difference.
🔄 **SUPERSEDED 2026-09-09: this tool read the whole of it and the
figure is now 8,192 bytes -- 0.195 % -- which is exactly `H601`.** Seating 17's
`map 0` left 122,880 + 8,192 undetermined; seating 18's `map 1 0` split the
first of those into 28 identical units of 4,096 and **two** that differ,
`009000` and `00D000`. The sentence below is what was true when this tool was
written and is kept because it is why it exists.
**4,153,344 bytes -- 99.02 % -- are undetermined**, and seating 16's nineteen
bisection rungs were all off-card, because each rung's address depends on the
previous rung's answer and a card is written before the board is powered.

``rtl819x-spi`` 1.1 answers it in two levels of 32 (32 x 32 = 1024 exactly,
and one page of ``read_proc`` holds 32 lines and not 1,024).  This tool
computes the expectation from the dump so that **every one of those lines is
predicted before the seating**, which is what makes them cells rather than
exploration.

The comparison refuses more often than it answers, deliberately
----------------------------------------------------------------
* **Scope.**  Two digests over different byte counts are not comparable, and
  saying ``DIFFER`` about them is a confident answer to a question nobody
  asked.  ``notes/flash-digest-scope.md`` § 8.2: nine of seating 16's finer
  rungs came back ``SCOPE?`` for exactly this reason and that is why the
  four-rung answer above them is trustworthy.  The device prints the bytes it
  hashed per entry; this tool compares that first and refuses the digest.
* **H601.**  The rule about what may be printed lives in ``tools/flashwin.py``
  and is IMPORTED, not restated -- a second copy of a safety rule is a second
  thing to forget to update.  Every range that reaches a digest here is put
  through ``flashwin.overlaps_forbidden`` and the tool raises rather than
  hashing it.  The driver skips the same two chunks by the same arithmetic and
  prints ``map_h601_hashed``, so the two agree by construction and each says so
  out loud.

What it does NOT prove
----------------------
* A digest match says the window is unchanged **since the dump**.  Two writes
  that cancel are invisible, at any resolution.
* The dump is the reference.  If the dump is wrong, everything here is wrong
  in the same direction.  ``FLS-14``'s two committed copies being
  byte-identical over all 4,194,304 bytes is the only check there is.
* ⚠️ A per-4-KiB digest is a stronger oracle than the aggregate one already
  committed: someone **holding the old dump** could brute-force a small change
  inside a sector from its digest.  That is the owner of the device.  The dump
  is not committed (``CLAUDE.md``'s Never table) and cannot be, so the
  published digests are a preimage problem for everyone else.  Recorded rather
  than left to be noticed.
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flashwin  # noqa: E402  -- the H601 rule has exactly one owner

SIZE = 0x00400000
CHUNK = 4096
MAP_N = 32
GROUP = SIZE // MAP_N          # 131072
H601_LO, H601_HI = 0x6000, 0x8000
COMPLEMENT = SIZE - (H601_HI - H601_LO)   # 4186112, FLS-24

SKIP_LABEL = flashwin.SKIP_LABEL
DEFAULT_DUMP = "dumps/flash-n150rt-console-2.bin"


class Refused(Exception):
    pass


def load_dump(path):
    if not os.path.isfile(path):
        raise Refused("no dump at %s" % path)
    data = open(path, "rb").read()
    if len(data) != SIZE:
        raise Refused("%s is %d bytes, expected %d -- a dump of the wrong "
                      "size would make every offset below mean something "
                      "else" % (path, len(data), SIZE))
    return data


def entry_ranges(level, group, index):
    """The chunk ranges that reach entry `index`'s digest, H601 removed.

    Reproduces the driver's loop exactly: it walks CHUNK at a time and skips a
    chunk whose start is inside H601.  H601 is two whole aligned chunks, so
    there is no partial-chunk arithmetic on either side -- which is the reason
    the driver's own comment gives for the bounds being what they are.
    """
    if level == 0:
        unit, base = GROUP, 0
    elif level == 1:
        unit, base = GROUP // MAP_N, group * GROUP
    else:
        raise Refused("level must be 0 or 1")
    start = base + index * unit
    out = []
    for off in range(start, start + unit, CHUNK):
        if H601_LO <= off < H601_HI:
            continue
        out.append((off, CHUNK))
    return start, unit, out


def entry_digest(dump, level, group, index):
    """(offset, bytes_hashed, hexdigest or None).

    None when nothing was hashed -- the two H601 chunks at level 1 group 0.
    """
    start, _unit, ranges = entry_ranges(level, group, index)
    h = hashlib.sha256()
    n = 0
    for off, ln in ranges:
        hit = flashwin.overlaps_forbidden(off, ln)
        if hit:
            raise Refused(
                "refusing to digest [0x%06X,0x%06X): it overlaps %s. The "
                "driver skips the same range; if this fires the two have "
                "stopped agreeing and neither reading means anything"
                % (off, off + ln, hit[2]))
        h.update(dump[off:off + ln])
        n += ln
    return start, n, (h.hexdigest() if n else None)


def predict(dump, level, group):
    rows = []
    for i in range(MAP_N):
        rows.append(entry_digest(dump, level, group, i))
    return rows


def render(rows):
    """The device's own line format, so a reader can diff the two directly."""
    out = []
    for off, n, d in rows:
        out.append("%06X %d %6u %s" % (off, 1, n, d if d else "SKIPPED"))
    return out


# ---------------------------------------------------------------- compare
def parse_capture(text):
    """(fields, entries) out of a /proc/rtl819x-spi-map capture.

    CRLF-tolerant for the reason tools/capfield.py exists: every capture line
    ends \\r\\n and a comparison against a value carrying one is false while
    printing as if it were true.
    """
    fields, entries = {}, []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        p = raw.strip().split()
        if len(p) == 2 and p[0][:1].isalpha():
            fields[p[0]] = p[1]
        elif len(p) == 4 and len(p[0]) == 6:
            try:
                entries.append((int(p[0], 16), int(p[1]), int(p[2]), p[3]))
            except ValueError:
                continue
    return fields, entries


def compare(dump, text):
    """(rows, summary).  Each row is (offset, verdict, detail)."""
    fields, entries = parse_capture(text)
    for k in ("map_level", "map_ran", "map_rc", "map_h601_hashed"):
        if k not in fields:
            raise Refused("the capture has no %s field -- it is not a "
                          "/proc/rtl819x-spi-map dump" % k)
    if fields["map_ran"] != "1" or fields["map_rc"] != "0":
        raise Refused("map_ran=%s map_rc=%s: no completed map to compare"
                      % (fields["map_ran"], fields["map_rc"]))
    if fields["map_h601_hashed"] != "0":
        raise Refused("map_h601_hashed=%s -- the device's own guard says its "
                      "digests are not H601-free, so nothing here may be "
                      "compared or printed" % fields["map_h601_hashed"])
    if fields.get("map_truncated") not in (None, "0"):
        raise Refused("map_truncated=%s: the device could not print its whole "
                      "answer, so a missing line is not a missing difference"
                      % fields["map_truncated"])
    level = int(fields["map_level"])
    group = int(fields.get("map_group", "0"))
    if not entries:
        raise Refused("the capture holds no map lines")

    want = {off: (n, d) for off, n, d in predict(dump, level, group)}
    rows = []
    same = differ = scope = extra = 0
    for off, eq, n, d in entries:
        if off not in want:
            rows.append((off, "EXTRA", "not an entry of level %d group %d"
                         % (level, group)))
            extra += 1
            continue
        wn, wd = want[off]
        if n != wn:
            rows.append((off, "SCOPE?", "device hashed %d bytes, the dump's "
                                        "expectation is %d" % (n, wn)))
            scope += 1
            continue
        if wd is None:
            rows.append((off, "SKIPPED", "H601, by rule, on both sides"))
            same += 1
            continue
        if d == wd:
            rows.append((off, "SAME", "pio==mmio %d" % eq))
            same += 1
        else:
            rows.append((off, "DIFFER", "device %s... dump %s..."
                         % (d[:16], wd[:16])))
            differ += 1
    missing = sorted(set(want) - set(e[0] for e in entries))
    return rows, dict(level=level, group=group, same=same, differ=differ,
                      scope=scope, extra=extra, missing=missing,
                      n=len(entries), fields=fields)


# ---------------------------------------------------------------- controls
def _synthetic():
    """A 4 MiB buffer that is not this device's flash.

    Every byte is a function of its offset, so a single flipped byte is
    detectable and nothing here resembles real content.
    """
    return bytes((i * 37 + (i >> 12)) & 0xFF for i in range(SIZE))


def controls(dump_path):
    rows = []

    def ck(name, ok, detail=""):
        rows.append((name, ok, detail))

    syn = _synthetic()

    # F2 the level-0 entries cover the complement exactly, and the arithmetic
    # is the driver's own COMPLEMENT constant rather than a number retyped.
    tot = sum(n for _o, n, _d in predict(syn, 0, 0))
    ck("F2 level 0 hashes exactly the complement", tot == COMPLEMENT,
       "%d vs %d" % (tot, COMPLEMENT))

    # F3 group 0 at level 1 is 30 chunks and two skips, and they are chunks
    # 6 and 7 -- the shape the driver's "no partial-chunk arithmetic" claim
    # depends on.
    g0 = predict(syn, 1, 0)
    skipped = [o for o, n, _d in g0 if n == 0]
    ck("F3 level 1 group 0 skips exactly chunks 6 and 7",
       skipped == [0x6000, 0x7000] and
       sum(1 for _o, n, _d in g0 if n == CHUNK) == 30,
       "skipped=%r" % ([hex(x) for x in skipped],))

    # F4 NEGATIVE CONTROL: a digest that cannot fail proves nothing.  One
    # flipped byte must move exactly one entry at each level.
    bad = bytearray(syn)
    bad[0x9123] ^= 0xFF
    bad = bytes(bad)
    d0a, d0b = predict(syn, 0, 0), predict(bad, 0, 0)
    moved0 = [i for i in range(MAP_N) if d0a[i][2] != d0b[i][2]]
    d1a, d1b = predict(syn, 1, 0), predict(bad, 1, 0)
    moved1 = [i for i in range(MAP_N) if d1a[i][2] != d1b[i][2]]
    ck("F4 one flipped byte moves exactly one entry at each level",
       moved0 == [0] and moved1 == [9],
       "level0 %r level1 %r" % (moved0, moved1))

    # F5 the SCOPE guard: byte counts that disagree must refuse, not DIFFER.
    cap = ("map_ran 1\nmap_rc 0\nmap_level 1\nmap_group 0\n"
           "map_h601_hashed 0\nmap_truncated 0\n"
           "009000 1   2048 %s\n" % ("0" * 64))
    r, s = compare(syn, cap)
    ck("F5 a shorter scope is SCOPE?, never DIFFER",
       s["scope"] == 1 and s["differ"] == 0, "%r" % (s,))

    # F5b and a matching scope with a wrong digest IS a DIFFER -- otherwise F5
    # passes for a tool that says SCOPE? to everything.
    cap = ("map_ran 1\nmap_rc 0\nmap_level 1\nmap_group 0\n"
           "map_h601_hashed 0\nmap_truncated 0\n"
           "009000 1   4096 %s\n" % ("0" * 64))
    r, s = compare(syn, cap)
    ck("F5b a matching scope with a wrong digest IS a DIFFER",
       s["differ"] == 1 and s["scope"] == 0, "%r" % (s,))

    # F5c and the right digest is SAME, so the comparison can also succeed.
    right = predict(syn, 1, 0)[9][2]
    cap = ("map_ran 1\nmap_rc 0\nmap_level 1\nmap_group 0\n"
           "map_h601_hashed 0\nmap_truncated 0\n"
           "009000 1   4096 %s\n" % right)
    r, s = compare(syn, cap)
    ck("F5c the right digest is SAME", s["same"] == 1 and s["differ"] == 0,
       "%r" % (s,))

    # F6 the device's own H601 guard is believed rather than second-guessed:
    # a capture claiming h601 bytes reached a digest is refused outright.
    try:
        compare(syn, "map_ran 1\nmap_rc 0\nmap_level 0\nmap_group 0\n"
                     "map_h601_hashed 4096\nmap_truncated 0\n")
        ok6 = False
    except Refused:
        ok6 = True
    ck("F6 map_h601_hashed != 0 refuses everything", ok6)

    # F6b truncation is refused too: a missing line is not a missing
    # difference, and this is the one a reader would otherwise never see.
    try:
        compare(syn, "map_ran 1\nmap_rc 0\nmap_level 0\nmap_group 0\n"
                     "map_h601_hashed 0\nmap_truncated 1\n"
                     "000000 1 122880 %s\n" % ("0" * 64))
        ok6b = False
    except Refused:
        ok6b = True
    ck("F6b map_truncated != 0 refuses everything", ok6b)

    # F7 a dump of the wrong size is refused rather than indexed off the end.
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fh.write(b"x" * 1024)
            small = fh.name
        try:
            load_dump(small)
            ok7 = False
        except Refused:
            ok7 = True
        os.unlink(small)
    except OSError:
        ok7 = False
    ck("F7 a dump of the wrong size is refused", ok7)

    # F8 the H601 rule is flashwin's, not a copy: ask it directly for the two
    # chunks the driver skips and for the two either side of them.
    ck("F8 the imported rule covers exactly H601",
       (flashwin.overlaps_forbidden(0x5000, CHUNK) is None
        and flashwin.overlaps_forbidden(0x6000, CHUNK) is not None
        and flashwin.overlaps_forbidden(0x7000, CHUNK) is not None
        and flashwin.overlaps_forbidden(0x8000, CHUNK) is None))

    # F9 THE ROUND TRIP, and it is the control F5..F5c cannot be.  Those use
    # snippets I wrote, and a snippet I wrote cannot show that this parser
    # matches the C format string, because I wrote both.  This renders the
    # predictor's own rows through the DRIVER's exact `%06X %d %6u %s` plus
    # its header and footer fields, terminates every line CRLF the way a
    # capture does, and requires every entry to come back SAME.
    def render_driver(level, group, wrong=None):
        rows = predict(syn, level, group)
        hashed = sum(n for _o, n, _d in rows)
        body = [
            "version rtl819x-spi 1.1", "map_ran 1", "map_rc 0",
            "map_level %d" % level, "map_group %u" % group,
            "map_unit %u" % (GROUP if level == 0 else CHUNK),
            "map_entries %u" % MAP_N, "map_hashed %u" % hashed,
            "map_h601_skipped %u" % (H601_HI - H601_LO
                                     if (level == 0 or group == 0) else 0),
            "map_h601_hashed 0", "map_diff_units 0", "map_jiffies 41",
            "hz 100", "corrupt_at -1",
        ]
        for i, (off, n, d) in enumerate(rows):
            if wrong is not None and i == wrong:
                d = "0" * 64
            body.append("%06X %d %6u %s" % (off, 1, n, d if d else "SKIPPED"))
        body += ["map_truncated 0", "map_lines %u" % MAP_N]
        return "".join(x + "\r\n" for x in body), max(len(x) for x in body)

    ok9, why9 = True, []
    for lv, gp in ((0, 0), (1, 0), (1, 9)):
        text, widest = render_driver(lv, gp)
        try:
            _rows, s = compare(syn, text)
        except Refused as exc:
            ok9 = False
            why9.append("level %d group %d refused: %s" % (lv, gp, exc))
            continue
        if s["same"] != MAP_N or s["differ"] or s["scope"] or s["missing"]:
            ok9 = False
            why9.append("level %d group %d -> %r" % (lv, gp, s))
        # The budget is the driver's, so the rendered body is measured here
        # rather than estimated in a comment.
        if len(text) > 3584 or widest != 80:
            ok9 = False
            why9.append("level %d group %d body %d B widest %d"
                        % (lv, gp, len(text), widest))
    ck("F9 the driver's own line format round-trips, all three shapes", ok9,
       "; ".join(why9))

    # F9b and the negative half, through the same rendering path -- otherwise
    # F9 passes for a parser that returns SAME for everything.
    text, _w = render_driver(1, 9, wrong=3)
    _rows, s = compare(syn, text)
    ck("F9b one wrong digest in that rendering is a DIFFER",
       s["differ"] == 1 and s["same"] == MAP_N - 1, "%r" % (s,))

    # ---- real material: the dump.  Skipped where it is absent, which is CI.
    if dump_path and os.path.isfile(dump_path):
        try:
            real = load_dump(dump_path)
        except Refused as exc:
            ck("F1 the whole complement reproduces FLS-24", False, str(exc))
            return rows
        h = hashlib.sha256()
        for off in range(0, SIZE, CHUNK):
            if H601_LO <= off < H601_HI:
                continue
            h.update(real[off:off + CHUNK])
        got = h.hexdigest()
        want = ("a9916fd86adb49ff0a4f53d49bc377ca"
                "5c54321dcff02bdb55e7b4ab64ce3cba")
        ck("F1 the complement of the real dump reproduces FLS-24",
           got == want, got[:24] + "...")
        tot = sum(n for _o, n, _d in predict(real, 0, 0))
        ck("F1b and its level-0 entries cover the same bytes",
           tot == COMPLEMENT, "%d" % tot)
    else:
        ck("F1 the complement of the real dump reproduces FLS-24", None,
           "skipped: %s" % SKIP_LABEL)
        ck("F1b and its level-0 entries cover the same bytes", None,
           "skipped: %s" % SKIP_LABEL)
    return rows


def run_controls(dump_path):
    print("flashmap controls (they run first; nothing is reported until the "
          "tool itself is trusted)")
    rows = controls(dump_path)
    nf = sum(1 for _n, ok, _d in rows if ok is False)
    ns = sum(1 for _n, ok, _d in rows if ok is None)
    for name, ok, detail in rows:
        mark = "ok" if ok is True else "skip" if ok is None else "FAIL"
        # The id goes in its own column because `tools/ci-census.py`'s
        # SKIP_RE takes the whole second column as the LABEL it looks up in
        # ci-expected.tsv.  A sentence there would be the label.
        cid, _sep, rest = name.partition(" ")
        print("  %-5s %-6s %-50s %s" % (mark, cid, rest, detail))
    print("")
    print("RESULT: %d passed, %d failed, %d skipped"
          % (len(rows) - nf - ns, nf, ns))
    return 2 if nf else 0


def default_dump():
    work = os.environ.get("FWRE_WORK", "")
    return os.path.join(work, DEFAULT_DUMP) if work else DEFAULT_DUMP


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="predict and compare rtl819x-spi's `map` output")
    ap.add_argument("--dump", default=None,
                    help="the reference dump (default: $FWRE_WORK/" +
                         DEFAULT_DUMP + ")")
    ap.add_argument("--no-controls", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("predict", help="print the expected map lines")
    p.add_argument("--level", type=int, required=True, choices=(0, 1))
    p.add_argument("--group", type=int, default=0)

    p = sub.add_parser("compare", help="a capture against the dump")
    p.add_argument("capture", help="a /proc/rtl819x-spi-map capture (.log)")

    sub.add_parser("controls", help="run the controls and stop")

    args = ap.parse_args(argv)
    dump_path = args.dump or default_dump()
    if args.cmd is None:
        ap.print_help()
        return 2
    if args.cmd == "controls":
        return run_controls(dump_path)
    if not args.no_controls:
        rows = controls(dump_path)
        bad = [r for r in rows if r[1] is False]
        if bad:
            print("flashmap: REFUSING -- %d control(s) failed" % len(bad))
            for n, _ok, d in bad:
                print("  FAIL %s  %s" % (n, d))
            return 2

    try:
        dump = load_dump(dump_path)
        if args.cmd == "predict":
            for line in render(predict(dump, args.level, args.group)):
                print(line)
            return 0
        if args.cmd == "compare":
            path = args.capture
            if not path.endswith(".log") and os.path.exists(path + ".log"):
                path += ".log"
            text = open(path, "rb").read().decode("utf-8", "replace")
            rows, s = compare(dump, text)
            for off, verdict, detail in rows:
                if verdict != "SAME":
                    print("  %-7s %06X  %s" % (verdict, off, detail))
            print("flashmap: level %d group %d, %d entries -- %d same, "
                  "%d DIFFER, %d scope, %d extra, %d missing"
                  % (s["level"], s["group"], s["n"], s["same"], s["differ"],
                     s["scope"], s["extra"], len(s["missing"])))
            if s["missing"]:
                print("  missing: %s"
                      % " ".join("%06X" % m for m in s["missing"][:8]))
            return 1 if (s["differ"] or s["scope"] or s["extra"]
                         or s["missing"]) else 0
    except Refused as exc:
        print("flashmap: REFUSED -- %s" % exc, file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
