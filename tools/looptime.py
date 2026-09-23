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
For captures c1..cn of one seating, ordered by `started_wallclock` (by
`t0_real` where a capture carries it -- THE CLOCK A GAP IS TAKEN ON, below):

    machine  = sum(duration_i)                       what the instrument held
    gap_i    = start_{i+1} - (start_i + duration_i)  dead time between two
    span     = (start_n + duration_n) - start_1      the seating, end to end

and, exactly,

    span == machine + sum(gap_i)

That is a telescoping sum, so it holds even when a gap is negative.  `A1`
asserts it on every run rather than only in the self-test: a decomposition
whose parts do not add up to its whole is reporting on something else.

It is computed on seconds since the first capture opened, not since 1970.  On
epoch seconds (~1.8e9, where one float step is 2.4e-7 s) each gap carried up to
1.2e-7 s of rounding, and 113 of them summed past `IDENTITY_TOL`: A1 refused
`bench/2026-09-21e`, whose exact residual is 0, and would have refused
`bench/2026-09-23` (量 2026-09-23 at 453ceac).  The tolerance did not move; the
arithmetic did.  `P8` is that shape.

🔴 ORDERED BY CLOCK, NOT BY FILENAME.  Capture names are chosen by the person
writing the card and they are not monotonic -- `bench/2026-08-31c` holds
`K-2a` before `K-A` alphabetically and after it in time, and seating 8's
re-run cells are `K2-`, `K2b-`, `K3-`, `K4-`.  Sorting by name would produce
negative gaps that are an artefact of the sort.  `N1` is that case.

🔴 A GAP'S RESOLUTION IS 1 SECOND, AND THAT IS NOT A ROUNDING REMARK
--------------------------------------------------------------------
讀 `console-capture.py:551-554`: the origin `t0` (CLOCK_MONOTONIC to 1.4,
CLOCK_MONOTONIC_RAW from 1.5) and then `started_wallclock` through
`time.strftime("%Y-%m-%dT%H:%M:%S%z")` -- the same instant, but `duration_s`
keeps microseconds and the wall clock is truncated to the second.  So the
recorded start is `floor(true_start)`, and

    true_start in [recorded, recorded + 1)

Substituting into the gap gives `true_gap` in `(recorded_gap - 1, recorded_gap
+ 1)`.  Two consequences, and the second is why this paragraph is here rather
than in a footnote:

  * every gap below carries +/-1 s of quantisation.  On a gap of minutes that
    is invisible; on a gap of a second it is the whole number.
  * a pair can only be shown to OVERLAP when `recorded_gap < -1`.  量
    2026-09-01 over every seating then in `bench/`: more than a hundred pairs
    had a gap of about **-0.09 s**, and NOT ONE was below -1.  They are the
    truncation and nothing else.  A tool that called them overlaps would be
    reporting on its own arithmetic, so the bound is derived from the
    instrument's source and is not a tolerance somebody chose.  (量
    2026-09-23 at 453ceac: 26 pairs in five later seatings are below -1 and
    are reported as OVERLAPs; what they are is not settled here.)

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

THE CLOCK A GAP IS TAKEN ON
---------------------------
The rule above adds a MONOTONIC `duration_s` to a REALTIME start.  From
`console-capture` 1.5, `duration_s` is CLOCK_MONOTONIC_RAW seconds, and on this
host REALTIME runs several percent slow of RAW between the steps that catch it
up (`SPEC.md` `CLK-38`), so that sum would be two clocks in one number.  Each
gap is therefore taken on the best clock BOTH of its captures carry, and the
report names it:

  raw   next `t0_raw` - previous `end_raw`, when both carry them under one
        `boot_id` (RAW restarts with every WSL boot, so stamps from two boots
        have no difference).  No truncation, and within one boot RAW never
        goes back: any negative value is an overlap.
  real  next `t0_real` - previous `end_real`, when both carry them (every
        capture since `P2-1`, `SPEC.md` `FW-115`).  No truncation; REALTIME
        can step, so a negative value is an overlap or a backward step, and it
        is reported as an OVERLAP either way.
  wall  the rule above, when the wall clock is all the pair shares.  REFUSED
        when the earlier capture's duration is RAW: that is the sum this
        section exists to prevent.

A seating whose every gap is `wall` prints exactly what it printed before
these rules.  Any other prints the rule beside every gap it names, and its
`span` is instrument + dead: each hold is its capture's own `duration_s`, each
gap is on its rule, and no single clock was read from the first capture to the
last -- which is why `A1` is checked on the wall clock's arithmetic and not on
these numbers.  Captures are ordered by `t0_real` where they carry it: 78
captures in `bench/` open in the same wall-clock second as an earlier capture
of their directory (量 2026-09-23 at 453ceac), and ordered by name inside it, a
clock with no truncation would call the misordering an overlap.  `C8` is that
case.

RECORDS THAT ARE NOT CAPTURES
-----------------------------
A bench directory also holds the `.meta.json` of recorders that are not a
console capture: `hostprobe` runs across the captures it brackets and has no
`duration_s`, and neither has `hostclock`.  One probe record refused the whole
of `bench/2026-09-23` before this rule.  A meta whose `tool` is named in
`NON_CAPTURE_TOOLS` is skipped, counted and named in the report -- never
silently -- and its `.log` is not called an orphan.  The list holds names, not
a pattern: a `tool` it does not name is read as a capture, and refused if it
has no `duration_s` (`S2`).

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
# Recorders whose `.meta.json` sits beside the captures and is not one.  NAMES,
# not a pattern: a `tool` missing from this tuple is read as a capture.
NON_CAPTURE_TOOLS = ('hostprobe', 'hostclock')
# The exact `clock` string console-capture 1.5 declares.  Compared with ==,
# never `in`: CLOCK_MONOTONIC is a prefix of it.
RAW_CLOCK = 'CLOCK_MONOTONIC_RAW'


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
def _stamp(j, key, where):
    """An absolute clock stamp: None when absent, refused when not a number."""
    v = j.get(key)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Refused('%s: %s %r is not a number' % (where, key, v))
    return float(v)


def _by_tool(skipped):
    """`hostprobe 2 (P1-HP, P2-HP)`, in NON_CAPTURE_TOOLS order."""
    parts = []
    for t in NON_CAPTURE_TOOLS:
        names = [nm for tl, nm in skipped if tl == t]
        if names:
            parts.append('%s %d (%s)' % (t, len(names), ', '.join(names)))
    return '; '.join(parts)


def read_seating(d):
    """Every capture of one directory, ordered by clock.

    Returns (captures, notes).  `captures` is a list of dicts; `notes` holds
    the things a reader has to be told rather than have averaged away.
    """
    if not os.path.isdir(d):
        raise Refused('%s: not a directory' % d)
    metas = sorted(glob.glob(os.path.join(d, '*.meta.json')))
    caps = []
    skipped = []
    for m in metas:
        name = os.path.basename(m)[:-len('.meta.json')]
        try:
            with open(m, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
        except (ValueError, OSError) as e:
            raise Refused('%s: %s' % (m, e))
        if not isinstance(j, dict):
            raise Refused('%s: not a JSON object' % m)
        tool = j.get('tool')
        if tool in NON_CAPTURE_TOOLS:
            skipped.append((tool, name))
            continue
        if 'duration_s' not in j:
            raise Refused('%s: no duration_s. A capture with no duration is '
                          'not a zero-length capture%s'
                          % (m, '' if tool is None else
                             ' (its tool is %r, which is not one of %s, the '
                             'recorders skipped as not captures)'
                             % (tool, ', '.join(NON_CAPTURE_TOOLS))))
        try:
            dur = float(j['duration_s'])
        except (TypeError, ValueError):
            raise Refused('%s: duration_s %r is not a number'
                          % (m, j['duration_s']))
        start = parse_wallclock(j.get('started_wallclock'), m)
        t0_real = _stamp(j, 't0_real', m)
        caps.append({
            'name': name,
            'start': start,
            'dur': dur,
            'sent': j.get('sent') or '',
            'bytes': j.get('bytes'),
            'clock': j.get('clock'),
            'boot_id': j.get('boot_id'),
            't0_raw': _stamp(j, 't0_raw', m),
            'end_raw': _stamp(j, 'end_raw', m),
            't0_real': t0_real,
            'end_real': _stamp(j, 'end_real', m),
            # the wall clock to the microsecond where the capture carries it:
            # two captures inside one wall-clock second are otherwise ordered
            # by name (THE CLOCK A GAP IS TAKEN ON)
            'order': start.timestamp() if t0_real is None else t0_real,
        })
    if not caps:
        raise Refused('%s: no *.meta.json%s. Refusing to report 0 s over an '
                      'empty population'
                      % (d, '' if not skipped else
                         ' that is a capture -- %d skipped as not captures: %s'
                         % (len(skipped), _by_tool(skipped))))
    caps.sort(key=lambda c: (c['order'], c['name']))

    notes = []
    if skipped:
        notes.append('%d .meta.json file(s) are records of a recorder that is '
                     'not a console capture, and are outside every number '
                     'here: %s' % (len(skipped), _by_tool(skipped)))
    # A capture killed by SIGTERM keeps its .log and .timing and loses its
    # .meta.json (CLAUDE.md, 2026-08-30).  Such a capture is INVISIBLE to the
    # arithmetic above, so it is counted and named rather than passed over.
    # A skipped record's .log has its .meta.json and is not one of them.
    have = set(c['name'] for c in caps) | set(nm for _t, nm in skipped)
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
def raw_duration(c):
    """True when this capture's duration_s is RAW seconds: it says so, or it
    carries the RAW stamps its duration could only have been taken from."""
    return (c['clock'] == RAW_CLOCK or c['t0_raw'] is not None
            or c['end_raw'] is not None)


def clock_gap(a, b):
    """(rule, seconds) for the dead time between capture `a` and the next, `b`.

    The best clock both carry (THE CLOCK A GAP IS TAKEN ON).  `seconds` is
    None for `wall`, whose value analyse() has already computed.
    """
    if (a['end_raw'] is not None and b['t0_raw'] is not None
            and a['boot_id'] and a['boot_id'] == b['boot_id']):
        return 'raw', b['t0_raw'] - a['end_raw']
    if a['end_real'] is not None and b['t0_real'] is not None:
        return 'real', b['t0_real'] - a['end_real']
    if raw_duration(a):
        raise Refused('%s -> %s: the wall clock is the only clock they share, '
                      'and %s\'s duration_s is %s seconds. A RAW duration added '
                      'to a REALTIME start is two clocks in one number; '
                      'refusing rather than report it'
                      % (a['name'], b['name'], a['name'], RAW_CLOCK))
    return 'wall', None


def overlap_bound(rule):
    """How far below 0 a gap on this rule can read without being an overlap:
    the wall clock's truncation, and nothing on a clock that has none."""
    return WALLCLOCK_QUANTUM if rule == 'wall' else 0.0


def analyse(caps):
    """machine / gaps / span, and the identity."""
    machine = sum(c['dur'] for c in caps)
    # Seconds since the first capture opened, not since 1970 (see the header).
    base = caps[0]['start'].timestamp()
    gaps = []
    for a, b in zip(caps, caps[1:]):
        end = a['start'].timestamp() - base + a['dur']
        gaps.append({'after': a['name'], 'before': b['name'],
                     's': b['start'].timestamp() - base - end})
    span = caps[-1]['start'].timestamp() - base + caps[-1]['dur']
    total = machine + sum(g['s'] for g in gaps)
    if abs(total - span) > IDENTITY_TOL:
        raise Refused('A1 the decomposition does not add up: machine %.6f + '
                      'gaps %.6f = %.6f, span %.6f'
                      % (machine, sum(g['s'] for g in gaps), total, span))
    # Each gap again, on the best clock both of its captures carry.  An
    # all-`wall` seating keeps every number above; any other seating's span is
    # the sum of its parts, because no one clock covers it end to end.
    for g, a, b in zip(gaps, caps, caps[1:]):
        g['rule'], s = clock_gap(a, b)
        if s is not None:
            g['s'] = s
    if any(g['rule'] != 'wall' for g in gaps):
        span = machine + sum(g['s'] for g in gaps)
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
RULE_TEXT = {
    'raw': 'next t0_raw - previous end_raw, one boot_id: no truncation, and '
           'it never goes back',
    'real': 'next t0_real - previous end_real (REALTIME): no truncation, but '
            'it can step',
    'wall': 'next started_wallclock - (started_wallclock + duration_s): '
            '±%.1f s, the wall clock is written to the second'
            % WALLCLOCK_QUANTUM,
}


def report_seating(d, top, each=False):
    caps, notes = read_seating(d)
    machine, gaps, span = analyse(caps)
    puts = read_puts(d)
    # An all-`wall` seating prints exactly what this tool always printed; any
    # other names the rule beside every gap it prints.
    ruled = any(g['rule'] != 'wall' for g in gaps)
    if each:
        # One row per capture, from the SAME objects the totals are computed
        # from, so the two cannot disagree.  `t` is seconds since the seating
        # opened, which is the axis a loop is read on -- on a ruled seating,
        # the running sum of the holds and gaps that make its span.
        t0 = caps[0]['start'].timestamp()
        after = {g['after']: g for g in gaps}
        pos = 0.0
        for c in caps:
            g = after.get(c['name'])
            print('    %8.1f  %-16s hold %6.1f s  gap %8.1f s%s  sent %r'
                  % (pos if ruled else c['start'].timestamp() - t0,
                     c['name'], c['dur'],
                     g['s'] if g else float('nan'),
                     (' %-4s' % (g['rule'] if g else '-')) if ruled else '',
                     (c['sent'] or '')[:40]))
            pos += c['dur'] + (g['s'] if g else 0.0)
    gv = [g['s'] for g in gaps]
    # Provably an overlap only below the rule's bound (overlap_bound); between
    # -WALLCLOCK_QUANTUM and 0 a wall gap is the truncation and is counted
    # separately rather than either summed away or called something it is not.
    neg = [g for g in gaps if g['s'] < -overlap_bound(g['rule'])]
    quant = [g for g in gaps
             if g['rule'] == 'wall' and -WALLCLOCK_QUANTUM <= g['s'] < 0]

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
            print('    %8.1f s  after %-14s before %-14s%s'
                  % (g['s'], g['after'], g['before'],
                     ('  [%s]' % g['rule']) if ruled else ''))
    if puts:
        print('  upload  %d put(s), %.3f s total, %s byte(s)'
              % (len(puts), sum(p['seconds'] for p in puts),
                 sum(p['bytes'] or 0 for p in puts)))
    else:
        print('  upload  unmeasured -- no *-put.json in this directory')
    if gv and not ruled:
        print('  every gap above carries ±%.1f s: started_wallclock is written '
              'to the second (console-capture.py:554) while duration_s keeps '
              'microseconds' % WALLCLOCK_QUANTUM)
    if ruled:
        for rule in ('raw', 'real', 'wall'):
            k = sum(1 for g in gaps if g['rule'] == rule)
            if k:
                print('  gap rule  %-4s %4d  %s' % (rule, k, RULE_TEXT[rule]))
        print('  span is instrument + dead: each hold is its capture\'s own '
              'duration_s and each gap is on its rule -- no one clock was read '
              'from the first capture to the last')
        byname = dict((c['name'], c) for c in caps)
        breaks = ['%s -> %s' % (g['after'], g['before']) for g in gaps
                  if g['rule'] != 'raw'
                  and byname[g['after']]['end_raw'] is not None
                  and byname[g['before']]['t0_raw'] is not None]
        if breaks:
            print('  %d pair(s) carry RAW stamps but not one boot_id between '
                  'them (RAW restarts with every boot), so they are not on the '
                  'raw rule: %s' % (len(breaks), ', '.join(breaks)))
    if quant:
        print('  %d pair(s) have a small NEGATIVE gap (min %.3f s), all inside '
              'that ±%.1f s -- the truncation, not an overlap'
              % (len(quant), min(g['s'] for g in quant), WALLCLOCK_QUANTUM))
    for n in notes:
        print('  ⚠️  %s' % n)
    if neg:
        for g in neg:
            if g['rule'] == 'raw':
                print('  OVERLAP %.3f s: %s ends after %s starts on %s under '
                      'one boot_id, a clock with no truncation that never '
                      'goes back' % (-g['s'], g['after'], g['before'],
                                     RAW_CLOCK))
            elif g['rule'] == 'real':
                print('  OVERLAP %.3f s: %s ends after %s starts on REALTIME '
                      '(t0_real, end_real), which has no truncation -- an '
                      'overlap, or REALTIME stepped back between them'
                      % (-g['s'], g['after'], g['before']))
            else:
                print('  OVERLAP %.3f s: %s ends after %s starts, and that is '
                      'more than the ±%.1f s the clock can explain'
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
def _meta(d, name, start, dur, sent='', **extra):
    j = {'started_wallclock': start, 'duration_s': dur, 'sent': sent,
         'bytes': 1}
    j.update(extra)
    with open(os.path.join(d, name + '.meta.json'), 'w', encoding='utf-8') as f:
        json.dump(j, f)


def _record(d, name, j):
    with open(os.path.join(d, name + '.meta.json'), 'w', encoding='utf-8') as f:
        json.dump(j, f)


def _m14(d, name, start, dur, t0_real, end_real):
    """A capture as console-capture wrote it from P2-1: MONOTONIC + REALTIME."""
    _meta(d, name, start, dur, clock='CLOCK_MONOTONIC',
          t0_mono=100.0 + t0_real % 1000, end_mono=100.0 + t0_real % 1000 + dur,
          t0_real=t0_real, end_real=end_real)


def _m15(d, name, start, dur, t0_raw, t0_real, end_real, boot='B1',
         clock=RAW_CLOCK):
    """A capture as console-capture 1.5 writes it: duration_s = end_raw -
    t0_raw, a REALTIME pair beside it, and the boot the RAW stamps belong to."""
    _meta(d, name, start, dur, clock=clock, t0_raw=t0_raw,
          end_raw=t0_raw + dur, t0_real=t0_real, end_real=end_real,
          boot_id=boot)


def _cap(name, start, dur):
    """A capture as read_seating() returns it, carrying no clock stamps."""
    st = parse_wallclock(start, name)
    return {'name': name, 'start': st, 'dur': dur, 'sent': '', 'bytes': 1,
            'clock': None, 'boot_id': None, 't0_raw': None, 'end_raw': None,
            't0_real': None, 'end_real': None, 'order': st.timestamp()}


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

    # The epoch second of 2026-09-01T10:00:00+0800, for REALTIME stamps.
    W = parse_wallclock('2026-09-01T10:00:00+0800', 'x').timestamp()

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
    # And JSON that is not an object: reading its `tool` would otherwise be a
    # traceback, and a tool refuses with a reason.
    def n6():
        for body in ('{not json', '[1, 2]', '5'):
            with tempfile.TemporaryDirectory() as d:
                _fixture_simple(d)
                with open(os.path.join(d, 'broken.meta.json'), 'w',
                          encoding='utf-8') as f:
                    f.write(body)
                rc, out = run_cli(['seating', d])
                assert rc == 2, 'body %r: rc %r\n%s' % (body, rc, out)
                assert 'Traceback' not in out, out
    case('N6', 'a malformed or non-object .meta.json is REFUSED', n6)

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

    # -- P8 the identity on the shape that refused two real seatings --------
    # 量 2026-09-23: on epoch seconds the rounding of 113 gaps summed past
    # IDENTITY_TOL and A1 refused bench/2026-09-21e, whose exact residual is 0.
    # Thirty-one holds of 10.000003 s at a 2026 epoch round the same way every
    # time; the control proves the fixture still reproduces the refusal, so a
    # pass here is the arithmetic and not a fixture gone soft.
    def p8():
        with tempfile.TemporaryDirectory() as d:
            for i in range(31):
                _meta(d, 'c%02d' % i, '2026-09-01T10:%02d:%02d+0800'
                      % divmod(15 * i, 60), 10.000003)
            caps, _ = read_seating(d)
            epoch = (sum(c['dur'] for c in caps)
                     + sum(b['start'].timestamp()
                           - (a['start'].timestamp() + a['dur'])
                           for a, b in zip(caps, caps[1:]))
                     - (caps[-1]['start'].timestamp() + caps[-1]['dur']
                        - caps[0]['start'].timestamp()))
            assert abs(epoch) > IDENTITY_TOL, (
                'control: epoch-second arithmetic leaves only %r here -- the '
                'fixture no longer reproduces the refusal' % epoch)
            machine, gaps, span = analyse(caps)
            assert abs(machine + sum(g['s'] for g in gaps) - span) < 1e-9
            assert abs(span - (450.0 + 10.000003)) < 1e-9, span
    case('P8', 'A1 holds on 31 captures whose epoch-second sums round past '
               'IDENTITY_TOL', p8)

    # -- S1 a non-capture recorder's record is skipped -- counted and named -
    # One hostprobe meta refused the whole of bench/2026-09-23.  Skipping it
    # silently would be the orphan defect again, and so would calling its
    # .log an orphan.
    def s1():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            _record(d, 'hp', {'tool': 'hostprobe',
                              'started_wallclock': '2026-09-01T10:00:00+0800'})
            _record(d, 'clk', {'tool': 'hostclock', 'boot_id': 'B1'})
            for nm in ('hp', 'killed'):
                with open(os.path.join(d, nm + '.log'), 'w',
                          encoding='utf-8') as f:
                    f.write('x')
            rc, out = run_cli(['seating', d])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert '3 capture(s)   span 95.0 s   instrument 30.0 s' in out, out
            assert ('2 .meta.json file(s) are records of a recorder that is '
                    'not a console capture') in out, out
            assert 'hostprobe 1 (hp); hostclock 1 (clk)' in out, out
            orph = [l for l in out.splitlines() if 'have no .meta.json' in l]
            assert len(orph) == 1, orph
            assert orph[0].rsplit(': ', 1)[1].split(', ') == ['killed'], orph
        with tempfile.TemporaryDirectory() as d:
            _record(d, 'hp', {'tool': 'hostprobe'})
            _record(d, 'clk', {'tool': 'hostclock'})
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
            assert 'empty population' in out and '2 skipped' in out, out
    case('S1', 'hostprobe and hostclock records are skipped, counted and '
               'named; their .log is no orphan', s1)

    # -- S2 the skip list holds names, not a pattern -----------------------
    def s2():
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            _record(d, 'ip', {'tool': 'iperflog',
                              'started_wallclock': '2026-09-01T10:05:00+0800'})
            rc, out = run_cli(['seating', d])
            assert rc == 2, 'rc %r\n%s' % (rc, out)
            assert 'no duration_s' in out and "'iperflog'" in out, out
    case('S2', 'a tool the list does not name is read as a capture and '
               'refused, not skipped', s2)

    # -- C1..C8 the clock each gap is taken on.  Every fixture plants values
    # for which raw, real and wall give three different answers, so a gap on
    # the wrong rule cannot pass by coincidence. ----------------------------
    def c1():
        with tempfile.TemporaryDirectory() as d:
            _m15(d, 'a', '2026-09-01T10:00:00+0800', 10.5, 5000.0,
                 W + 0.40, W + 10.45)
            _m15(d, 'b', '2026-09-01T10:00:15+0800', 5.0, 5016.0,
                 W + 15.30, W + 20.30)
            caps, _ = read_seating(d)
            machine, gaps, span = analyse(caps)
            assert [g['rule'] for g in gaps] == ['raw'], gaps
            assert abs(gaps[0]['s'] - 5.5) < 1e-9, gaps
            assert abs(span - 21.0) < 1e-9, span
    case('C1', 'raw: next t0_raw - end_raw under one boot_id (5.5; real '
               'reads 4.85, wall 4.5)', c1)

    def c2():
        with tempfile.TemporaryDirectory() as d:
            _m14(d, 'a', '2026-09-01T10:00:00+0800', 10.2, W + 0.60, W + 11.40)
            _m14(d, 'b', '2026-09-01T10:00:15+0800', 5.0, W + 15.70, W + 20.70)
            caps, _ = read_seating(d)
            machine, gaps, span = analyse(caps)
            assert [g['rule'] for g in gaps] == ['real'], gaps
            assert abs(gaps[0]['s'] - 4.30) < 1e-6, gaps
            assert abs(span - 19.5) < 1e-6, span
    case('C2', 'real: next t0_real - end_real (4.30; wall reads 4.8)', c2)

    def c3():
        with tempfile.TemporaryDirectory() as d:
            _meta(d, 'a', '2026-09-01T10:00:00+0800', 10.0)   # before P2-1
            _m14(d, 'b', '2026-09-01T10:00:15+0800', 10.0, W + 15.30, W + 25.30)
            _meta(d, 'c', '2026-09-01T10:00:30+0800', 10.0)
            caps, _ = read_seating(d)
            machine, gaps, span = analyse(caps)
            assert [g['rule'] for g in gaps] == ['wall', 'wall'], gaps
            assert [round(g['s'], 6) for g in gaps] == [5.0, 5.0], gaps
            assert abs(span - 40.0) < 1e-9, span
    case('C3', 'wall: a pair without a shared stamp keeps the old rule, and a '
               'MONOTONIC duration may meet a wall start', c3)

    def c4():
        with tempfile.TemporaryDirectory() as d:
            _m15(d, 'a', '2026-09-01T10:00:00+0800', 10.5, 5000.0,
                 W + 0.40, W + 10.45, boot='B1')
            _m15(d, 'b', '2026-09-01T10:00:40+0800', 5.0, 12.0,
                 W + 40.20, W + 45.20, boot='B2')
            caps, _ = read_seating(d)
            _m, gaps, _s = analyse(caps)
            # raw across the two boots would read 12.0 - 5010.5 = -4998.5
            assert [g['rule'] for g in gaps] == ['real'], gaps
            assert abs(gaps[0]['s'] - 29.75) < 1e-6, gaps
            rc, out = run_cli(['seating', d])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert 'not one boot_id' in out and 'a -> b' in out, out
    case('C4', 'RAW stamps under two boot_ids fall back to real, and the '
               'report names the pair', c4)

    def c5():
        with tempfile.TemporaryDirectory() as d:
            _m14(d, 'a', '2026-09-01T10:00:00+0800', 10.0, W + 0.20, W + 10.60)
            _m15(d, 'b', '2026-09-01T10:00:15+0800', 10.0, 7000.0,
                 W + 15.10, W + 24.70)
            _m14(d, 'c', '2026-09-01T10:00:30+0800', 10.0, W + 30.90, W + 41.00)
            caps, _ = read_seating(d)
            _m, gaps, _s = analyse(caps)
            assert [g['rule'] for g in gaps] == ['real', 'real'], gaps
            assert [round(g['s'], 3) for g in gaps] == [4.5, 6.2], gaps
        # a RAW duration, then a capture with no REALTIME stamp: the wall
        # clock is all they share -- declared RAW, and RAW by its stamps alone
        for clock in (RAW_CLOCK, None):
            with tempfile.TemporaryDirectory() as d:
                _m15(d, 'a', '2026-09-01T10:00:00+0800', 10.0, 7000.0,
                     W + 0.10, W + 9.70, clock=clock)
                _meta(d, 'b', '2026-09-01T10:00:15+0800', 10.0)
                rc, out = run_cli(['seating', d])
                assert rc == 2, 'clock %r: rc %r\n%s' % (clock, rc, out)
                assert ('a -> b' in out and RAW_CLOCK in out
                        and 'two clocks in one number' in out), out
    case('C5', 'mixed clocks: MONOTONIC and RAW captures meet on real; a RAW '
               'duration never meets a wall start', c5)

    def c6():
        with tempfile.TemporaryDirectory() as d:
            _meta(d, 'a', '2026-09-01T10:00:00+0800', 10.0)
            _m15(d, 'b', '2026-09-01T10:00:15+0800', 10.0, 5000.0,
                 W + 15.40, W + 25.00)
            _m15(d, 'c', '2026-09-01T10:00:31+0800', 10.0, 5016.0,
                 W + 31.10, W + 40.70)
            rc, out = run_cli(['seating', d, '--each'])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert 'gap rule  raw     1' in out, out
            assert 'gap rule  wall    1' in out, out
            assert '[raw]' in out and '[wall]' in out, out
            assert 'span is instrument + dead' in out, out
            assert 'every gap above carries' not in out, out
            rows = [l.split() for l in out.splitlines() if ' sent ' in l]
            assert [r[8] for r in rows] == ['wall', 'raw', '-'], rows
        with tempfile.TemporaryDirectory() as d:
            _fixture_simple(d)
            rc, out = run_cli(['seating', d, '--each'])
            assert rc == 0, 'rc %r\n%s' % (rc, out)
            assert 'every gap above carries' in out, out
            assert 'gap rule' not in out and '[wall]' not in out, out
    case('C6', 'the report names the rule of every gap it prints; an all-wall '
               'seating prints what it always did', c6)

    def c7():
        with tempfile.TemporaryDirectory() as d:
            _m15(d, 'a', '2026-09-01T10:00:00+0800', 10.0, 5000.0,
                 W + 0.10, W + 9.70)
            _m15(d, 'b', '2026-09-01T10:00:09+0800', 10.0, 5009.8,
                 W + 9.80, W + 19.40)
            rc, out = run_cli(['seating', d])
            assert rc == 1 and 'OVERLAP 0.200 s' in out, (rc, out)
            assert RAW_CLOCK in out, out
        with tempfile.TemporaryDirectory() as d:
            _m14(d, 'a', '2026-09-01T10:00:00+0800', 10.0, W + 0.10, W + 10.10)
            _m14(d, 'b', '2026-09-01T10:00:09+0800', 10.0, W + 9.90, W + 19.90)
            rc, out = run_cli(['seating', d])
            assert rc == 1 and 'OVERLAP 0.200 s' in out, (rc, out)
            assert 'REALTIME' in out, out
    case('C7', 'a raw or real gap of -0.2 s is an OVERLAP: no truncation '
               'forgives it', c7)

    def c8():
        with tempfile.TemporaryDirectory() as d:
            _m14(d, 'zz-early', '2026-09-01T10:00:00+0800', 0.3,
                 W + 0.10, W + 0.40)
            _m14(d, 'aa-late', '2026-09-01T10:00:00+0800', 0.3,
                 W + 0.55, W + 0.85)
            caps, _ = read_seating(d)
            assert [c['name'] for c in caps] == ['zz-early', 'aa-late'], caps
            rc, out = run_cli(['seating', d])
            assert rc == 0 and 'OVERLAP' not in out, (rc, out)
    case('C8', 'two captures in one wall-clock second are ordered by t0_real, '
               'not by name', c8)

    # -- F1 FW-124: the refusals a card's HOST cell can be checked with ----
    def f1():
        ap = build_parser()
        for argv, want in ((['seating'], 'at least one path'),
                           ([], 'a mode'),
                           (['to-prompt'], 'at least one path'),
                           (['seating', 'd', '--top', '-1'], '--top -1')):
            try:
                refuse_args(ap.parse_args(argv))
            except Refused as e:
                assert want in str(e), (argv, str(e))
            else:
                raise AssertionError('refuse_args permitted %r' % argv)
        for argv in (['seating', 'd'], ['seating', 'd', 'e', '--top', '0'],
                     ['to-prompt', 'p', '--marker', 'x'], ['--self-test']):
            refuse_args(ap.parse_args(argv))       # permitted: must not raise
        # main() runs the same check: the --top refusal exists nowhere else
        rc, out = run_cli(['seating', tempfile.gettempdir(), '--top', '-1'])
        assert rc == 2 and '--top -1' in out, (rc, out)
    case('F1', 'refuse_args refuses a missing mode or path and a negative '
               '--top, permits the good forms; main runs it', f1)

    # -- A1 the identity check can actually fire ---------------------------
    def a1():
        caps = [_cap('a', '2026-09-01T10:00:00+0800', 10.0),
                _cap('b', '2026-09-01T10:00:20+0800', 10.0)]
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
        assert len(ids) >= 38, ids
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
def build_parser():
    """The parser main() itself uses (FW-124): a card's HOST cell is checked
    with this and refuse_args(), so the check and the run cannot drift."""
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
    return ap


def refuse_args(a):
    """Every refusal that reads nothing but the parsed arguments (FW-124):
    no file, directory, environment or clock."""
    if a.self_test:
        return
    if not a.mode or not a.paths:
        raise Refused('a mode and at least one path are required')
    if a.top < 0:
        raise Refused('--top %d: how many of the largest gaps to name cannot '
                      'be negative' % a.top)


def main(argv):
    ap = build_parser()
    a = ap.parse_args(argv)
    try:
        refuse_args(a)
    except Refused as e:
        ap.print_usage(sys.stderr)
        sys.stderr.write('looptime: %s\n' % e)
        return 2
    if a.self_test:
        return selftest()
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
