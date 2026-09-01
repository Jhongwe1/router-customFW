#!/usr/bin/env python3
"""test-looptime-mutants -- the mutation suite for `tools/looptime.py`.

Why this file exists, and why its first case is not a mutant
------------------------------------------------------------
`looptime.py` reported 20 green controls on its first run.  This repository's
own history says that is not evidence of anything:

  * `spec-check.py`        15 green controls,  3 live mutants  (2026-08-30)
  * `console-capture.py`   40 green cases,    10 live mutants  (2026-08-30)
  * `leakscan.py`          17 green controls,  8 live mutants  (2026-08-30)
  * `flashwin.py`          13 green controls, 24 live mutants  (2026-08-30)
  * `flrbracket.py`        29 green controls, 13 live mutants  (2026-08-31)

The harness, and why it is smaller than `flrbracket`'s
-------------------------------------------------------
`flrbracket.py` resolves the repository root from its own `__file__`, so its
mutation harness has to build a temp root of symlinks and get one directory
deliberately wrong.  `looptime.py` reads only the paths it is handed and builds
its own fixtures in a `TemporaryDirectory`, so a mutant is one file in a temp
directory and nothing else.  Smaller for a reason, not by omission.

Four controls of the harness itself, each copied from `flrbracket`'s because
each caught something real there:

  * **`B0`, before any mutant**: the UNMUTATED file, run the way every mutant
    below is run, must be GREEN.  Otherwise every "kill" is the harness.
  * **every row names the case it must turn red**, and it is a kill only if
    THAT case is among the failures.  `rc != 0` alone is what made a previous
    pass invalid.
  * **a mutant that does not parse is `INVALID-MUTANT`**, not a survivor and
    not a kill.
  * **a population control**: `MUT` must hold `DECLARED` rows with unique ids
    or the run refuses, because a deleted row otherwise reads as
    `n of n killed, 0 alive`, exit 0, green.

An anchor that no longer occurs exactly once is a SURVIVOR, never a skip: a
mutation suite that silently applies nothing is this repository's "a tool
reporting 0 is making a claim", one level up.

Run:  /usr/bin/python3 tools/test-looptime-mutants.py [--jobs N] [--only M1,M7]
"""
import argparse
import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'looptime.py')
DECLARED = 20

# (id, class, what it breaks, the case that must go red, [(anchor, replacement)])
MUT = [
    ('M1', 'ORDER', 'sort captures by filename instead of by wall clock', 'N1',
     [("caps.sort(key=lambda c: (c['start'], c['name']))",
       "caps.sort(key=lambda c: c['name'])")]),
    ('M2', 'ARITH', 'the gap forgets to subtract the capture it follows', 'P1',
     [("'s': b['start'].timestamp() - end}",
       "'s': b['start'].timestamp() - a['start'].timestamp()}")]),
    ('M3', 'ARITH', 'machine time sums the gaps rather than the durations',
     'P1',
     [("machine = sum(c['dur'] for c in caps)",
       "machine = sum(c['dur'] for c in caps[:-1])")]),
    ('M4', 'ARITH', 'span leaves off the last capture\'s own duration', 'P1',
     [("span = (caps[-1]['start'].timestamp() + caps[-1]['dur']\n"
       "            - caps[0]['start'].timestamp())",
       "span = (caps[-1]['start'].timestamp()\n"
       "            - caps[0]['start'].timestamp())")]),
    # 🔴 This row was `IDENTITY_TOL = 1e9` and it SURVIVED, correctly: the
    # identity is algebraic, so no input can make it fail by a small amount
    # and no test can constrain the constant.  What can be constrained is that
    # the check EXISTS and that a wrong formula fires it -- this row is the
    # first, M2/M3/M4 are the second.  Said here rather than swapping mutants
    # until one dies.
    ('M5', 'CONTROL', 'the identity check is removed entirely', 'A1',
     [("    if abs(total - span) > IDENTITY_TOL:",
       "    if False:")]),
    ('M6', 'QUANTUM', 'any negative gap is called an OVERLAP', 'N2b',
     [("neg = [g for g in gaps if g['s'] < -WALLCLOCK_QUANTUM]",
       "neg = [g for g in gaps if g['s'] < 0]")]),
    ('M7', 'QUANTUM', 'the overlap bound is so wide nothing is ever an overlap',
     'N2',
     [('WALLCLOCK_QUANTUM = 1.0', 'WALLCLOCK_QUANTUM = 1e6')]),
    ('M8', 'REFUSE', 'a capture with no duration_s is treated as 0 s', 'N3',
     [("if 'duration_s' not in j:", "if False:")]),
    ('M9', 'REFUSE', 'an empty directory is reported instead of refused', 'N4',
     [("if not caps:\n        raise Refused(", "if False:\n        raise Refused(")]),
    ('M10', 'REPORT', 'a .log with no .meta.json is passed over in silence',
     'N5',
     [('if nm not in have:\n            orphans.append(nm)',
       'if False:\n            orphans.append(nm)')]),
    ('M11', 'REFUSE', 'a naive timestamp is accepted and treated as local',
     'N7',
     [('if dt.tzinfo is None:', 'if False:')]),
    ('M12', 'ZERO', 'an absent upload is reported as 0.000 s rather than '
     'unmeasured', 'P4',
     [("    else:\n        print('  upload  unmeasured",
       "    else:\n        print('  upload  %d put(s), %.3f s total'\n"
       "              % (0, 0.0))\n        print('  x  unmeasured")]),
    ('M13', 'SPLIT', 'the split takes the first step rather than the largest',
     'P3',
     [('if step > best:', 'if False:')]),
    ('M14', 'TIMING', 'the timestamp of a byte is always the first read', 'P5',
     [('        if o <= off:\n            best = t',
       '        if o <= off and best is None:\n            best = t')]),
    ('M15', 'ZERO', 'a marker that is absent reports 0 s instead of saying so',
     'N8',
     [("    if not r['found']:", "    if False:")]),
    ('M16', 'REFUSE', 'a malformed .timing row is skipped instead of refused',
     'N9',
     [('            if len(parts) != 2:', '            if False:')]),
    ('M17', 'REPORT', '--each prints every capture twice', 'X3',
     [("        for c in caps:\n            print('    %8.1f  %-16s hold",
       "        for c in caps + caps:\n            print('    %8.1f  %-16s hold")]),
    ('M18', 'ARITH', 'the median returns the mean', 'P6',
     [('    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0',
       '    return sum(s) / float(n)')]),
    # 🔴 M19 was `drop the +0800 normalisation` and it SURVIVED, which is how
    # that shim was found to be unreachable: Python 3.11 accepts the compact
    # offset, and both machines that run this are 3.12.  The shim was deleted
    # rather than given a test that pins dead code.  This row is the boundary
    # the deletion left exposed instead.
    ('M19', 'TIMING', 'the byte-to-timestamp lookup is off by one at a row '
     'boundary', 'P5',
     [('        if o <= off:', '        if o < off:')]),
    ('M20', 'REFUSE', 'a put record with no seconds is silently skipped',
     'P4b',
     [("        if 'seconds' not in j:\n            raise Refused(",
       "        if 'seconds' not in j:\n            continue\n        if False:\n"
       "            raise Refused(")]),
]

FAILRE = re.compile(r'^\s*FAIL\s+(\S+)')


def run_selftest(path):
    r = subprocess.run([sys.executable, path, '--self-test'],
                       capture_output=True, text=True)
    fails = set()
    for line in r.stdout.splitlines():
        m = FAILRE.match(line)
        if m:
            fails.add(m.group(1))
    return r.returncode, fails, r.stdout + r.stderr


def write_and_run(text):
    d = tempfile.mkdtemp(prefix='looptime-mut-')
    p = os.path.join(d, 'looptime.py')
    try:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        return run_selftest(p)
    finally:
        try:
            os.remove(p)
            os.rmdir(d)
        except OSError:
            pass


def one(row, base):
    mid, klass, what, wants, edits = row
    text = base
    for anchor, repl in edits:
        n = text.count(anchor)
        if n != 1:
            return (mid, 'SURVIVOR', klass, what, wants,
                    'anchor occurs %d time(s), not once -- it has moved' % n)
        text = text.replace(anchor, repl, 1)
    if text == base:
        return (mid, 'SURVIVOR', klass, what, wants, 'the edit changed nothing')
    try:
        compile(text, '<mutant>', 'exec')
    except SyntaxError as e:
        return (mid, 'INVALID-MUTANT', klass, what, wants,
                'the edit does not parse: line %s, %s' % (e.lineno, e.msg))
    rc, fails, _out = write_and_run(text)
    if rc == 0:
        return (mid, 'SURVIVOR', klass, what, wants,
                'the self-test stayed GREEN')
    if wants not in fails:
        return (mid, 'WRONG-CASE', klass, what, wants,
                'it went red, but on %s and not on %s'
                % (sorted(fails) or ['(no case line)'], wants))
    return (mid, 'killed', klass, what, wants,
            '%s went red (with %d case(s) red in total)' % (wants, len(fails)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--only', default=None)
    a = ap.parse_args()

    ids = [r[0] for r in MUT]
    if len(MUT) != DECLARED or len(set(ids)) != len(ids):
        print('🔴 the mutant table is %d rows with %d distinct ids; DECLARED '
              'says %d.' % (len(MUT), len(set(ids)), DECLARED))
        print("   A deleted row would otherwise read as 'n of n killed, "
              "0 alive' and exit 0.")
        return 2

    with open(SRC, 'r', encoding='utf-8') as f:
        base = f.read()

    print('test-looptime-mutants: %d mutants of tools/looptime.py' % len(MUT))
    print()

    rc, fails, out = run_selftest(SRC)
    if rc != 0:
        print('🔴 B0 the UNMUTATED tool is not green. Refusing to report '
              'kills: every mutant below would be killed by a suite that was '
              'already red.')
        print('   rc=%d, red case(s): %s' % (rc, sorted(fails)))
        print(out[-2000:])
        return 2
    print('  ok   B0 the unmutated tool is GREEN -- the kills below are the '
          'mutations and not the harness')
    print()

    rows = MUT
    if a.only:
        want = set(a.only.split(','))
        rows = [r for r in MUT if r[0] in want]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for res in ex.map(lambda r: one(r, base), rows):
            results.append(res)

    results.sort(key=lambda r: int(r[0][1:]))
    killed = 0
    for mid, verdict, klass, what, wants, why in results:
        if verdict == 'killed':
            killed += 1
            print('  ok   %s [%s] %s' % (mid, klass, what))
            print('       -> %s' % why)
        else:
            print('  %s %s [%s] %s' % (verdict, mid, klass, what))
            print('       -> expected %s to go red; %s' % (wants, why))
    print()
    alive = len(results) - killed
    print('%d of %d killed, %d alive' % (killed, len(results), alive))
    return 1 if alive else 0


if __name__ == '__main__':
    raise SystemExit(main())
