#!/usr/bin/env python3
"""looptime.py -- the wall clock of a development loop, out of its own artefacts.

WHY IT EXISTS
-------------
`R4` is a gate about how long `edit -> result` takes, and its `D4` names a
number -- 90 s -- that had never been checked against an arithmetic this
repository can already do.  `R4-0` has to produce the arithmetic.  Two of its
terms were already published (`SPEC.md` `FW-32`, the build cell duration); the
two that were not are the ones a person is in:

  * how long a seating spends NOT capturing -- the operator reading a result,
    the desk writing the next command, the operator running it;
  * how long the board takes from power to a typeable `<RealTek>` prompt, and
    how much of that is the operator's hand rather than the board.

Both are already recorded.  Every capture carries `started_wallclock` and
`duration_s` in its `.meta.json`, and every capture has a `.timing` beside its
`.log`.  Nothing had ever joined them.

WHAT THIS OWNS, AND WHAT `boot-timeline.py` OWNS
------------------------------------------------
They both read `.timing` files and they do not overlap:

  `boot-timeline.py`  intervals between two things the DEVICE printed --
                      `Booting...` to `chipName:`, and so on.  Its anchors are
                      bytes in the device's output and choosing them wrongly
                      moves a published number, which is why that file argues
                      about anchors at length.
  `looptime.py`       intervals of the LOOP -- capture opened, first byte
                      received, prompt reachable, capture ended, next capture
                      started.  Its anchors are events of the instrument, not
                      of the boot.

A number that belongs to the first belongs there.  This file does not restate
one.

THE ARITHMETIC, AND THE IDENTITY THAT KEEPS IT HONEST
------------------------------------------------------
For captures c1..cn of one seating, ordered by `started_wallclock`:

    machine  = sum(duration_i)                       what the instrument held
    gap_i    = start_{i+1} - (start_i + duration_i)  dead time between two
    span     = (start_n + duration_n) - start_1      the seating, end to end

and, exactly,

    span == machine + sum(gap_i)

That is a telescoping sum, so it holds even when a gap is negative.  `A1`
asserts it on every run rather than only in the self-test: a decomposition
whose parts do not add up to its whole is reporting on something else.

🔴 ORDERED BY CLOCK, NOT BY FILENAME.  Capture names are chosen by the person
writing the card and they are not monotonic -- `bench/2026-08-31c` holds
`K-2a` before `K-A` alphabetically and after it in time, and seating 8's
re-run cells are `K2-`, `K2b-`, `K3-`, `K4-`.  Sorting by name would produce
negative gaps that are an artefact of the sort.  `N1` is that case.

🔴 A GAP'S RESOLUTION IS 1 SECOND, AND THAT IS NOT A ROUNDING REMARK
--------------------------------------------------------------------
讀 `console-capture.py:430-431`: `t0 = time.monotonic()` and then
`started_wallclock = time.strftime("%Y-%m-%dT%H:%M:%S%z")` -- the same instant,
but `duration_s` keeps microseconds and the wall clock is truncated to the
second.  So the recorded start is `floor(true_start)`, and

    true_start in [recorded, recorded + 1)

Substituting into the gap gives `true_gap` in `(recorded_gap - 1, recorded_gap
+ 1)`.  Two consequences, and the second is why this paragraph is here rather
than in a footnote:

  * every gap below carries +/-1 s of quantisation.  On a gap of minutes that
    is invisible; on a gap of a second it is the whole number.
  * a pair can only be shown to OVERLAP when `recorded_gap < -1`.  量 over
    every seating in `bench/`: more than a hundred pairs have a gap of about
    **-0.09 s**, and NOT ONE is below -1.  They are the truncation and nothing
    else.  A tool that called them overlaps would be reporting on its own
    arithmetic, so the bound is derived from the instrument's source and is
    not a tolerance somebody chose.

`N2` is a real overlap and must be caught; `N2b` is a -0.1 s gap and must NOT
be called one, while still being counted and printed.

WHAT A GAP IS NOT
-----------------
A gap is a residual, and a residual absorbs everything nobody named.  It does
not separate *the operator reading and pasting* from *the desk writing the next
command*; it measures their sum.  A gap that spans a break -- the operator
leaving the bench -- is arithmetically identical to a very slow round trip, so
this tool reports the distribution and the largest values by name and never
reports a mean alone.

THE UPLOAD IS REPORTED FROM A DIFFERENT FILE, AND ITS ABSENCE IS NOT ZERO
-------------------------------------------------------------------------
A TFTP upload leaves a `*-put.json`, which carries `seconds` and **no
timestamp**, so it cannot be placed in the timeline above.  It is summed and
reported beside it.  A seating with no `*-put.json` reports the upload as
`unmeasured` and never as `0.000`: a tool reporting 0 is making a claim, and
"this seating uploaded nothing" and "this seating uploaded and I cannot see it"
are different sentences.  `P4` is that case.

Usage
    looptime.py seating DIR [DIR...] [--top N]
    looptime.py to-prompt PREFIX [PREFIX...] [--marker STR]
    looptime.py --self-test

Exit
    0  reported (or the self-test passed)
    1  a seating carries an OVERLAP, or a `to-prompt` marker was not found
    2  refused -- nothing is reported
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import re
import tempfile
from datetime import datetime

VERSION = '1.0'
DEFAULT_MARKER = '<RealTek>'
# The first thing the CPU prints.  `rows[0]` is the first thing the LINE
# carries, and on a power-up those are not the same event: 量 2026-09-01 over
# fifteen cold captures, six open on a line-transition byte (0x00 / 0xFC /
# 0xFF) that precedes `Booting` by 0.321-0.350 s.  Counting that byte as *the
# line came up* is what put five of them into `CLK-18`'s high group and made a
# 0.165 s split that is not in the board.
BOOT_MARKER = 'Booting'
IDENTITY_TOL = 1e-6
# The width of `started_wallclock`'s truncation, in seconds.  Not a tolerance:
# `strftime("%S")` drops the fraction, so the true start is somewhere in
# [recorded, recorded + WALLCLOCK_QUANTUM).  See the header.
WALLCLOCK_QUANTUM = 1.0


class Refused(Exception):
    pass


# --------------------------------------------------------------- timestamps
def parse_wallclock(s, where):
    """ISO 8601 with an offset.  `+0800` and `+08:00` both, naive refused.

    The captures on disk are written `2026-08-30T13:17:11+0800`.  An earlier
    version of this function normalised that to `+08:00` first, because
    `datetime.fromisoformat` rejected the compact form before Python 3.11.
    🔴 That shim was DELETED after its own mutation survived: removing it left
    every control green, because it is unreachable here.  量 2026-09-01 --
    the bench host is 3.12.3 and CI is `ubuntu-24.04`, both above the version
    that accepts it, and this repository already requires 3.12 elsewhere (a
    `spec-check.py` f-string will not compile below it).  Code no test can
    reach is worse than code that is not there.

    A naive timestamp is REFUSED rather than assumed local: two seatings taken
    in different offsets would then be subtracted from each other silently.
    """
    if not isinstance(s, str) or not s:
        raise Refused('%s: started_wallclock is missing or not a string' % where)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise Refused('%s: started_wallclock %r does not parse: %s'
                      % (where, s, e))
    if dt.tzinfo is None:
        raise Refused('%s: started_wallclock %r has no UTC offset. A naive '
                      'timestamp cannot be compared with another seating\'s'
                      % (where, s))
    return dt


# ------------------------------------------------------------------ reading
def read_seating(d):
    """Every capture of one directory, ordered by clock.

    Returns (captures, notes).  `captures` is a list of dicts; `notes` holds
    the things a reader has to be told rather than have averaged away.
    """
    if not os.path.isdir(d):
        raise Refused('%s: not a directory' % d)
    metas = sorted(glob.glob(os.path.join(d, '*.meta.json')))
    caps = []
    for m in metas:
        name = os.path.basename(m)[:-len('.meta.json')]
        try:
            with open(m, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
        except (ValueError, OSError) as e:
            raise Refused('%s: %s' % (m, e))
        if 'duration_s' not in j:
            raise Refused('%s: no duration_s. A capture with no duration is '
                          'not a zero-length capture' % m)
        try:
            dur = float(j['duration_s'])
        except (TypeError, ValueError):
            raise Refused('%s: duration_s %r is not a number'
                          % (m, j['duration_s']))
        caps.append({
            'name': name,
            'start': parse_wallclock(j.get('started_wallclock'), m),
            'dur': dur,
            'sent': j.get('sent') or '',
            'bytes': j.get('bytes'),
        })
    if not caps:
        raise Refused('%s: no *.meta.json. Refusing to report 0 s over an '
                      'empty population' % d)
    caps.sort(key=lambda c: (c['start'], c['name']))

    notes = []
    # A capture killed by SIGTERM keeps its .log and .timing and loses its
    # .meta.json (CLAUDE.md, 2026-08-30).  Such a capture is INVISIBLE to the
    # arithmetic above, so it is counted and named rather than passed over.
    have = set(c['name'] for c in caps)
    orphans = []
    for lg in sorted(glob.glob(os.path.join(d, '*.log'))):
        nm = os.path.basename(lg)[:-len('.log')]
        if nm not in have:
            orphans.append(nm)
    if orphans:
        notes.append('%d .log file(s) have no .meta.json and are outside every '
                     'number below: %s' % (len(orphans), ', '.join(orphans)))
    return caps, notes


def read_puts(d):
    """`*-put.json` -- the TFTP uploads.  Absence is not zero."""
    out = []
    for p in sorted(glob.glob(os.path.join(d, '*-put.json'))):
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
        except (ValueError, OSError) as e:
            raise Refused('%s: %s' % (p, e))
        if j.get('op') != 'put':
            continue
        if 'seconds' not in j:
            raise Refused('%s: a put record with no seconds' % p)
        out.append({'name': os.path.basename(p)[:-len('.json')],
                    'seconds': float(j['seconds']),
                    'bytes': j.get('bytes'),
                    'retransmits': j.get('retransmits')})
    return out


# ------------------------------------------------------------- the analysis
def analyse(caps):
    """machine / gaps / span, and the identity."""
    machine = sum(c['dur'] for c in caps)
    gaps = []
    for a, b in zip(caps, caps[1:]):
        end = a['start'].timestamp() + a['dur']
        gaps.append({'after': a['name'], 'before': b['name'],
                     's': b['start'].timestamp() - end})
    span = (caps[-1]['start'].timestamp() + caps[-1]['dur']
            - caps[0]['start'].timestamp())
    total = machine + sum(g['s'] for g in gaps)
    if abs(total - span) > IDENTITY_TOL:
        raise Refused('A1 the decomposition does not add up: machine %.6f + '
                      'gaps %.6f = %.6f, span %.6f'
                      % (machine, sum(g['s'] for g in gaps), total, span))
    return machine, gaps, span


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def split_gaps(values):
    """The largest jump in the sorted values, and the mass either side.

    A one-dimensional split with no tuning constant: sort, find the biggest
    step between neighbours, cut there.  It cannot invent a split that is not
    the biggest step, and it always returns one -- so the CALLER decides
    whether a split means anything, from `ratio` below.  A verdict word here
    would be a threshold in disguise.
    """
    if len(values) < 2:
        return None
    s = sorted(values)
    k, best = 0, s[1] - s[0]
    for i in range(1, len(s) - 1):
        step = s[i + 1] - s[i]
        if step > best:
            k, best = i, step
    lo, hi = s[:k + 1], s[k + 1:]
    return {'cut': (s[k] + s[k + 1]) / 2.0, 'step': best,
            'lo_n': len(lo), 'lo_sum': sum(lo),
            'hi_n': len(hi), 'hi_sum': sum(hi)}


# ------------------------------------------------------------- to-prompt
def read_timing(prefix):
    """`.timing` -> [(byte_offset, seconds)], the format boot-timeline writes."""
    path = prefix + '.timing'
    if not os.path.isfile(path):
        raise Refused('%s: no .timing beside it' % path)
    rows = []
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise Refused('%s: %r is not "<offset> <seconds>"'
                              % (path, line))
            rows.append((int(parts[0]), float(parts[1])))
    if not rows:
        raise Refused('%s: no timing rows' % path)
    return rows


def at_offset(rows, off):
    """The timestamp of the read that DELIVERED byte `off`.

    The `.timing` offset is the byte count BEFORE the read, so the read that
    delivered byte `off` is the last row whose offset is <= off.
    """
    best = None
    for o, t in rows:
        if o <= off:
            best = t
        else:
            break
    return best


def to_prompt(prefix, marker, boot_marker=BOOT_MARKER):
    log = prefix + '.log'
    if not os.path.isfile(log):
        raise Refused('%s: no .log' % log)
    with open(log, 'rb') as fh:
        blob = fh.read()
    rows = read_timing(prefix)
    first_byte = rows[0][1]
    idx = blob.find(marker.encode('utf-8', 'replace'))
    out = {'name': os.path.basename(prefix), 'open_to_first': first_byte,
           'marker': marker, 'found': idx >= 0, 'offset': idx}
    if idx >= 0:
        t = at_offset(rows, idx)
        out['open_to_marker'] = t
        out['first_to_marker'] = t - first_byte
        # The same interval measured from the CPU rather than from the line.
        # ABSENT rather than defaulted when `Booting` is not there: falling
        # back to `first_to_marker` would make the two agree exactly when the
        # correction matters least, and nothing downstream could tell which
        # one it had.
        bidx = blob.find(boot_marker.encode('utf-8', 'replace'))
        out['boot_found'] = 0 <= bidx <= idx
        out['boot_offset'] = bidx
        if out['boot_found']:
            tb = at_offset(rows, bidx)
            out['boot_to_marker'] = t - tb
            out['lead_to_boot'] = tb - first_byte
    return out


# ------------------------------------------------------------------ report
def report_seating(d, top, each=False):
    caps, notes = read_seating(d)
    machine, gaps, span = analyse(caps)
    puts = read_puts(d)
    if each:
        # One row per capture, from the SAME objects the totals are computed
        # from, so the two cannot disagree.  `t` is seconds since the seating
        # opened, which is the axis a loop is read on.
        t0 = caps[0]['start'].timestamp()
        after = {g['after']: g['s'] for g in gaps}
        for c in caps:
            print('    %8.1f  %-16s hold %6.1f s  gap %8.1f s  sent %r'
                  % (c['start'].timestamp() - t0, c['name'], c['dur'],
                     after.get(c['name'], float('nan')),
                     (c['sent'] or '')[:40]))
    gv = [g['s'] for g in gaps]
    # Provably an overlap only below -WALLCLOCK_QUANTUM; between that and 0 it
    # is the truncation and is counted separately rather than either summed
    # away or called something it is not.
    neg = [g for g in gaps if g['s'] < -WALLCLOCK_QUANTUM]
    quant = [g for g in gaps if -WALLCLOCK_QUANTUM <= g['s'] < 0]

    print('%s' % d)
    print('  %d capture(s)   span %.1f s   instrument %.1f s (%.1f %%)   '
          'dead %.1f s (%.1f %%)'
          % (len(caps), span, machine, 100.0 * machine / span if span else 0.0,
             sum(gv), 100.0 * sum(gv) / span if span else 0.0))
    if gv:
        print('  gap  n=%d  median %.1f s  max %.1f s  max/median %s'
              % (len(gv), median(gv), max(gv),
                 ('%.1f' % (max(gv) / median(gv))) if median(gv) > 0 else 'n/a'))
        sp = split_gaps(gv)
        if sp:
            print('  largest jump in the sorted gaps is %.1f s, at %.1f s: '
                  '%d gap(s) below hold %.1f s (%.1f %%), %d above hold %.1f s '
                  '(%.1f %%)'
                  % (sp['step'], sp['cut'], sp['lo_n'], sp['lo_sum'],
                     100.0 * sp['lo_sum'] / sum(gv) if sum(gv) else 0.0,
                     sp['hi_n'], sp['hi_sum'],
                     100.0 * sp['hi_sum'] / sum(gv) if sum(gv) else 0.0))
        for g in sorted(gaps, key=lambda x: -x['s'])[:top]:
            print('    %8.1f s  after %-14s before %-14s'
                  % (g['s'], g['after'], g['before']))
    if puts:
        print('  upload  %d put(s), %.3f s total, %s byte(s)'
              % (len(puts), sum(p['seconds'] for p in puts),
                 sum(p['bytes'] or 0 for p in puts)))
    else:
        print('  upload  unmeasured -- no *-put.json in this directory')
    if gv:
        print('  every gap above carries ±%.1f s: started_wallclock is written '
              'to the second (console-capture.py:431) while duration_s keeps '
              'microseconds' % WALLCLOCK_QUANTUM)
    if quant:
        print('  %d pair(s) have a small NEGATIVE gap (min %.3f s), all inside '
              'that ±%.1f s -- the truncation, not an overlap'
              % (len(quant), min(g['s'] for g in quant), WALLCLOCK_QUANTUM))
    for n in notes:
        print('  ⚠️  %s' % n)
    if neg:
        for g in neg:
            print('  OVERLAP %.3f s: %s ends after %s starts, and that is more '
                  'than the ±%.1f s the clock can explain'
                  % (-g['s'], g['after'], g['before'], WALLCLOCK_QUANTUM))
    return 1 if neg else 0


def report_prompt(prefix, marker, boot_marker=BOOT_MARKER):
    r = to_prompt(prefix, marker, boot_marker)
    # The PREFIX AS GIVEN, not its basename: nine seatings hold a capture
    # called `A-catch`, and a column of nine identical names is a table nobody
    # can read a number out of.
    if not r['found']:
        print('%-34s marker %r NOT FOUND in the .log' % (prefix, marker))
        return 1
    print('%-34s open->first %7.3f s   first->%s %7.3f s   open->%s %7.3f s'
          % (prefix, r['open_to_first'], marker, r['first_to_marker'],
             marker, r['open_to_marker']))
    if r.get('boot_found'):
        print('%-34s   %s->%s %7.3f s   (lead %.3f s before %s)'
              % ('', boot_marker, marker, r['boot_to_marker'],
                 r['lead_to_boot'], boot_marker))
    else:
        print('%-34s   %r is not in this capture before the marker -- the '
              'CPU-relative interval is NOT reported' % ('', boot_marker))
    return 0


# --------------------------------------------------------------- self-test
def _meta(d, name, start, dur, sent=''):
    with open(os.path.join(d, name + '.meta.json'), 'w', encoding='utf-8') as f:
        json.dump({'started_wallclock': start, 'duration_s': dur,
                   'sent': sent, 'bytes': 1}, f)


def _fixture_simple(d):
    # three captures, 10 s each, gaps of 5 s and 60 s
    _meta(d, 'a', '2026-09-01T10:00:00+0800', 10.0)
    _meta(d, 'b', '2026-09-01T10:00:15+0800', 10.0)
    _meta(d, 'c', '2026-09-01T10:01:25+0800', 10.0)


def selftest():
    ok, bad = [], []

    def case(cid, what, fn):
        try:
            fn()
        except AssertionError as e:
            bad.append((cid, what, str(e)))
        except Exception as e:                       # noqa: BLE001
            bad.append((cid, what, '%s: %s' % (type(e).__name__, e)))
        else:
            ok.append((cid, what))

    here = os.path.abspath(__file__)

    def run_cli(args):
        r = subprocess.run([sys.executable, here] + args,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    # -- P1 the arithmetic on a fixture whose answers are known by hand -----
    def p1():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            caps, _ = read_seating(d)
            machine, gaps, span = analyse(caps)
            assert abs(machine - 30.0) < 1e-9, 'machine %r' % machine
            assert [round(g['s'], 6) for g in gaps] == [5.0, 60.0], gaps
            assert abs(span - 95.0) < 1e-9, 'span %r' % span
    case('P1', 'machine / gaps / span on a hand-computed fixture', p1)

    # -- P2 the identity, which is what makes the parts a decomposition -----
    def p2():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            caps, _ = read_seating(d)
            machine, gaps, span = analyse(caps)
            assert abs(machine + sum(g['s'] for g in gaps) - span) < 1e-9
    case('P2', 'span == instrument + sum(gaps), exactly', p2)

    # -- P3 the split lands on the biggest step and nowhere else -----------
    def p3():
        sp = split_gaps([2.0, 3.0, 2.5, 90.0, 120.0])
        assert sp['lo_n'] == 3 and sp['hi_n'] == 2, sp
        assert abs(sp['lo_sum'] - 7.5) < 1e-9, sp
        assert 3.0 < sp['cut'] < 90.0, sp
    case('P3', 'the maximum-jump split separates 3 small from 2 large', p3)

    # -- P3b and it does NOT invent a split on a flat set ------------------
    def p3b():
        sp = split_gaps([5.0, 5.1, 5.2, 5.3])
        assert sp['step'] < 0.2, sp
        assert sp['hi_n'] >= 1, sp
    case('P3b', 'a flat set gives a split whose step is small, not a verdict',
         p3b)

    # -- P6 the median is a median, on both parities ----------------------
    # A mean here would read as a typical round trip while being dragged by
    # one 2,307 s gap, which is exactly the shape every seating on disk has.
    def p6():
        assert median([3.0, 1.0, 2.0]) == 2.0
        assert median([4.0, 1.0, 2.0, 3.0]) == 2.5
        assert median([1.0, 1.0, 1.0, 100.0]) == 1.0, 'a mean in disguise'
        assert median([]) is None
    case('P6', 'median is the middle value, not the mean, on both parities',
         p6)

    # -- N1 ordering is by CLOCK.  Alphabetical order would give a negative
    #    gap here, so a tool that sorted by name fails this case. -----------
    def n1():
        with tempfile.TemporaryDirectory() as d:
            _meta(d, 'zz-first', '2026-09-01T10:00:00+0800', 10.0)
            _meta(d, 'aa-second', '2026-09-01T10:00:20+0800', 10.0)
            caps, _ = read_seating(d)
            assert [c['name'] for c in caps] == ['zz-first', 'aa-second'], caps
            _m, gaps, _s = analyse(caps)
            assert gaps[0]['s'] > 0, gaps
    case('N1', 'captures are ordered by wall clock and not by filename', n1)

    # -- N2 a real overlap is REPORTED, not summed away --------------------
    def n2():
        with tempfile.TemporaryDirectory() as d:
            _meta(d, 'a', '2026-09-01T10:00:00+0800', 30.0)
            _meta(d, 'b', '2026-09-01T10:00:10+0800', 10.0)
            rc, out = run_cli(['seating', d])
            assert rc == 1, 'rc %r\n%s' % (rc, out)
            assert 'OVERLAP' in out, out
    case('N2', 'a 20 s overlap exits 1 and says OVERLAP', n2)

    # -- N2b and the truncation is NOT called one --------------------------
    # A -0.1 s gap is what every scripted block on disk shows.  Calling it an
    # overlap would make the tool red on every real seating and would be a
    # claim about the captures made from the instrument's own rounding.
    def n2b():
        with tempfile.TemporaryDirectory() as d:
            _meta(d, 'a', '2026-09-01T10:00:00+0800', 10.1)
            _meta(d, 'b', '2026-09-01T10:00:10+0800', 10.0)
            rc, out = run_cli(['seating', d])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert 'OVERLAP' not in out, out
            assert 'not an overlap' in out, out
    case('N2b', 'a -0.1 s gap is counted as truncation and exits 0', n2b)

    # -- N3 a capture with no duration is refused, not treated as 0 --------
    def n3():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            with open(os.path.join(d, 'x.meta.json'), 'w',
                      encoding='utf-8') as f:
                json.dump({'started_wallclock': '2026-09-01T10:05:00+0800'}, f)
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
            assert 'no duration_s' in out, out
    case('N3', 'a meta with no duration_s is REFUSED, not counted as 0 s', n3)

    # -- N4 an empty directory is refused, not reported as 0 s -------------
    def n4():
        with tempfile.TemporaryDirectory() as d:
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
            assert 'empty population' in out, out
    case('N4', 'a directory with no captures is REFUSED, not 0 s', n4)

    # -- N5 a .log with no .meta.json is counted and named -----------------
    def n5():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            with open(os.path.join(d, 'killed.log'), 'w',
                      encoding='utf-8') as f:
                f.write('x')
            rc, out = run_cli(['seating', d])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert 'killed' in out and 'no .meta.json' in out, out
    case('N5', 'a .log whose capture was killed is counted and named', n5)

    # -- N6 malformed JSON is refused -------------------------------------
    def n6():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            with open(os.path.join(d, 'broken.meta.json'), 'w',
                      encoding='utf-8') as f:
                f.write('{not json')
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
    case('N6', 'a malformed .meta.json is REFUSED', n6)

    # -- N7 both offset spellings parse; a naive timestamp is refused ------
    def n7():
        a = parse_wallclock('2026-09-01T10:00:00+0800', 'x')
        b = parse_wallclock('2026-09-01T10:00:00+08:00', 'x')
        assert a == b, (a, b)
        try:
            parse_wallclock('2026-09-01T10:00:00', 'x')
        except Refused:
            pass
        else:
            raise AssertionError('a naive timestamp was accepted')
    case('N7', '+0800 and +08:00 agree; a naive timestamp is refused', n7)

    # -- P4 an absent upload is `unmeasured`, never 0.000 ------------------
    def p4():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            rc, out = run_cli(['seating', d])
            assert rc == 0, out
            assert 'upload  unmeasured' in out, out
            assert '0.000 s total' not in out, out
            with open(os.path.join(d, 'q-put.json'), 'w',
                      encoding='utf-8') as f:
                json.dump({'op': 'put', 'seconds': 1.545, 'bytes': 1029120}, f)
            rc, out = run_cli(['seating', d])
            assert rc == 0, out
            assert '1.545 s total' in out, out
    case('P4', 'no put.json reports `unmeasured`; one reports its seconds', p4)

    # -- P4b a put record with no seconds is refused, not skipped ----------
    # Skipping it would report the remaining uploads as if they were all of
    # them, which is the same defect as reporting an absent upload as 0.
    def p4b():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            with open(os.path.join(d, 'q-put.json'), 'w',
                      encoding='utf-8') as f:
                json.dump({'op': 'put', 'bytes': 1029120}, f)
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
            assert 'no seconds' in out, out
    case('P4b', 'a put record with no seconds is REFUSED, not skipped', p4b)

    # -- P5 to-prompt, on a fixture whose answer is known ------------------
    def p5():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'\x00Booting...\r\n---RealTek---\r\n<RealTek>')
            # A row EXACTLY at the marker's offset, so that `<=` and `<` in
            # at_offset() give different answers.  Without it the boundary is
            # untested and an off-by-one there survives every case.
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                f.write('# offset seconds\n0 2.000\n1 2.500\n28 9.000\n')
            r = to_prompt(p, DEFAULT_MARKER)
            assert r['found'] and r['offset'] == 28, r
            assert abs(r['open_to_first'] - 2.0) < 1e-9, r
            assert abs(r['open_to_marker'] - 9.0) < 1e-9, r
            assert abs(r['first_to_marker'] - 7.0) < 1e-9, r
    case('P5', 'to-prompt splits open->first byte from first byte->prompt', p5)

    # -- P7 the power-on glitch byte, which is what `CLK-18`'s two groups were.
    # 量 2026-09-01: six of fifteen cold captures open on one line-transition
    # byte 0.321-0.350 s before `Booting`.  This is that shape, with the lead
    # made exactly 0.350 s so the two intervals must differ by it.
    def p6():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'\x00\r\nBooting...\r\n---RealTek---\r\n<RealTek>')
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                # byte 0 is the glitch; `Booting` starts at offset 3.
                f.write('# offset seconds\n0 1.000\n1 1.350\n30 3.500\n')
            r = to_prompt(p, DEFAULT_MARKER)
            assert r['boot_found'], r
            assert abs(r['first_to_marker'] - 2.5) < 1e-9, r
            assert abs(r['boot_to_marker'] - 2.15) < 1e-9, r
            assert abs(r['lead_to_boot'] - 0.35) < 1e-9, r
            assert abs((r['first_to_marker'] - r['boot_to_marker'])
                       - r['lead_to_boot']) < 1e-9, r
    case('P7', 'a power-on glitch byte moves first->prompt and leaves '
               'Booting->prompt alone', p6)

    # -- N11 no `Booting`: the CPU-relative interval is ABSENT, not defaulted.
    def n9():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'J 80500000\r\nsomething else\r\n<RealTek>')
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                f.write('# offset seconds\n0 1.000\n1 1.010\n29 3.000\n')
            r = to_prompt(p, DEFAULT_MARKER)
            assert r['found'], r
            assert r['boot_found'] is False, r
            assert 'boot_to_marker' not in r, r
    case('N11', 'with no `Booting` the CPU-relative interval is absent, not '
               'silently equal to the other one', n9)

    # -- N10 `Booting` AFTER the marker is not an origin either: a warm capture
    # whose prompt precedes the reset would otherwise report a negative
    # interval as a number.
    def n10():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'<RealTek>J BFC00000\r\nBooting...\r\n')
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                f.write('# offset seconds\n0 1.000\n1 1.010\n35 3.000\n')
            r = to_prompt(p, DEFAULT_MARKER)
            assert r['found'] and r['offset'] == 0, r
            assert r['boot_found'] is False, r
    case('N10', '`Booting` after the marker is not taken as the origin', n10)

    # -- N8 a marker that is not there exits 1 and says so -----------------
    def n8():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'nothing here')
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                f.write('0 1.0\n')
            rc, out = run_cli(['to-prompt', p])
            assert rc == 1, 'rc %r\n%s' % (rc, out)
            assert 'NOT FOUND' in out, out
    case('N8', 'a marker that never appears exits 1, it does not report 0 s',
         n8)

    # -- N9 a .timing whose rows are malformed is refused ------------------
    def n9():
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'cap')
            with open(p + '.log', 'wb') as f:
                f.write(b'<RealTek>')
            with open(p + '.timing', 'w', encoding='utf-8') as f:
                f.write('0 1.0 extra\n')
            rc, out = run_cli(['to-prompt', p])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
    case('N9', 'a malformed .timing row is REFUSED', n9)

    # -- X1 the CLI exits 0 on a good seating ------------------------------
    def x1():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            rc, out = run_cli(['seating', d])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert '3 capture(s)' in out, out
    case('X1', 'CLI: a good seating exits 0 and reports its n', x1)

    # -- X3 --each prints exactly one row per capture ----------------------
    def x3():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            rc, out = run_cli(['seating', d, '--each'])
            assert rc == 0, out
            # `sent ` and not `hold `: the summary line "N gap(s) below hold
            # X s" also contains ` hold `, and the first version of this case
            # counted it -- caught by the mutation harness's own B0.
            rows = [l for l in out.splitlines() if ' sent ' in l]
            assert len(rows) == 3, rows
    case('X3', 'CLI: --each prints one row per capture and no more', x3)

    # -- X2 a directory that is not one is refused -------------------------
    def x2():
        rc, out = run_cli(['seating',
                           os.path.join(tempfile.gettempdir(), 'no-such-dir-x')])
        assert rc == 2, 'rc %r\n%s' % (rc, out)
    case('X2', 'CLI: a path that is not a directory is REFUSED', x2)

    # -- A1 the identity check can actually fire ---------------------------
    def a1():
        caps = [{'name': 'a',
                 'start': parse_wallclock('2026-09-01T10:00:00+0800', 'x'),
                 'dur': 10.0},
                {'name': 'b',
                 'start': parse_wallclock('2026-09-01T10:00:20+0800', 'x'),
                 'dur': 10.0}]
        global IDENTITY_TOL
        keep = IDENTITY_TOL
        try:
            IDENTITY_TOL = -1.0          # nothing can be within a negative tol
            try:
                analyse(caps)
            except Refused:
                return
            raise AssertionError('A1 did not fire even with a negative '
                                 'tolerance -- the check is unreachable')
        finally:
            IDENTITY_TOL = keep
    case('A1', 'the identity check is reachable, not decoration', a1)

    # -- A2 the case ids are unique.  Written 2026-09-01 after this edit gave
    # `P6` and `N9` a second occupant each: a duplicated id means a red line
    # cannot be mapped back to the case that produced it, and every count this
    # repository keeps of "n controls" is then a count of runs and not of
    # cases.  It reads the source rather than the run, so it sees a case that
    # is registered and never reached.
    def a2():
        with open(os.path.abspath(__file__), encoding='utf-8') as fh:
            src = fh.read()
        ids = re.findall(r"^    case\('([A-Za-z0-9]+)'", src, re.M)
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        assert not dupes, 'duplicate case id(s): %s' % dupes
        assert len(ids) >= 25, ids
    case('A2', 'every case id in this file is unique', a2)

    print('looptime %s -- self-test' % VERSION)
    for cid, what in ok:
        print('  ok    %-4s %s' % (cid, what))
    for cid, what, why in bad:
        print('  FAIL  %-4s %s' % (cid, what))
        print('        %s' % why)
    print()
    if not ok and not bad:
        print('🔴 the self-test ran no cases at all')
        return 2
    print('%d passed, %d failed' % (len(ok), len(bad)))
    return 1 if bad else 0


# -------------------------------------------------------------------- main
def main(argv):
    ap = argparse.ArgumentParser(add_help=True,
                                 description=__doc__.splitlines()[0])
    ap.add_argument('mode', nargs='?', choices=['seating', 'to-prompt'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--top', type=int, default=5,
                    help='how many of the largest gaps to name (default 5)')
    ap.add_argument('--marker', default=DEFAULT_MARKER)
    ap.add_argument('--from-marker', dest='boot_marker',
                    default=BOOT_MARKER,
                    help='the CPU-relative origin for to-prompt (default %r)' % BOOT_MARKER)
    ap.add_argument('--each', action='store_true',
                    help='one row per capture, on the seating\'s own clock')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args(argv)

    if a.self_test:
        return selftest()
    if not a.mode or not a.paths:
        ap.print_usage(sys.stderr)
        sys.stderr.write('looptime: a mode and at least one path are required\n')
        return 2
    worst = 0
    try:
        for p in a.paths:
            if a.mode == 'seating':
                worst = max(worst, report_seating(p, a.top, a.each))
            else:
                worst = max(worst, report_prompt(p, a.marker,
                                                 a.boot_marker))
    except Refused as e:
        sys.stderr.write('looptime: %s\n' % e)
        return 2
    return worst


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
