#!/usr/bin/env python3
"""marchcmp.py -- three 20x8 assembler matrices, compared cell by cell.

`docs/toolchain-prior-art.md` § 8.1 writes down, BEFORE the run, what the
public Lexra binutils patch predicts `isa-probe.sh` will print.  A prediction
compared by eye is not a prediction, so this compares three matrices:

  PREDICTED  parsed out of `docs/toolchain-prior-art.md` § 8.1 -- derived from
             the public patch's membership words, committed before any rsdk
             assembler was run for it.
  COMMITTED  parsed out of `notes/vendor-kernel-isa.md` § 6 -- this project's
             own reading, taken 2026-08-28 with an assembler the table does
             not name.
  MEASURED   parsed out of an `isa-probe.sh` run, one per toolchain.

Both markdown tables group instructions whose columns are identical onto one
row (`lwl` `lwr` `swl` `swr`).  The probe prints one row per instruction.  A
comparison between a 10-row table and a 20-row table is a comparison between
two different things, so grouped rows are EXPANDED and `C4` is the control
that the expansion gives exactly the 20 the probe has, in both directions.

Usage
    marchcmp.py show {predicted,committed}          the parsed matrix
    marchcmp.py parse FILE                          parse one probe output
    marchcmp.py diff A B                            A and B may be the two
                                                    keywords or a probe file
    marchcmp.py --self-test                         the controls

Exit
    0  clean, or a diff that is empty
    1  a difference, or a failing control
    3  REFUSED -- something would not parse, so nothing is reported.  An empty
       matrix and a matrix of rejections are different answers.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PRED_DOC = os.path.join(ROOT, 'docs', 'toolchain-prior-art.md')
COMM_DOC = os.path.join(ROOT, 'notes', 'vendor-kernel-isa.md')

# The probe's own row order, from `tools/isa-probe.sh`'s `row` calls.  It is
# the atomic unit both markdown tables have to expand to.
PROBE_ROWS = ['lwl', 'lwr', 'swl', 'swr', 'll', 'sc', 'sync', 'cache', 'pref',
              'mfc3', 'mtc3', 'lwc3', 'movz', 'movn', 'beql', 'madd', 'rdhwr',
              'mfc1', 'lwc1', 'jalx']
PROBE_ARCHS = ['lx4180', 'rlx4181', 'rlx5181', 'lx5280', 'rlx5281', 'rlx4281',
               'mips1', 'mips2']


class Refused(Exception):
    pass


def _cells(line):
    s = line.strip()
    if not s.startswith('|'):
        return None
    s = s.strip('|')
    return [c.strip() for c in s.split('|')]


def _clean(c):
    return c.replace('*', '').replace('`', '').strip()


def parse_md_matrix(path, want_archs=None):
    """The first markdown table whose header row names every probe arch."""
    if not os.path.exists(path):
        raise Refused('%s does not exist' % path)
    want = want_archs or PROBE_ARCHS
    lines = io.open(path, encoding='utf-8').read().split('\n')
    for i, ln in enumerate(lines):
        cs = _cells(ln)
        if not cs:
            continue
        names = [_clean(c) for c in cs]
        if not all(a in names for a in want):
            continue
        # header found; the arch order is the header's, not ours
        order = [n for n in names if n in want]
        if len(order) != len(want):
            continue
        idx = [names.index(a) for a in order]
        out, n = {}, i + 2                     # skip the |---| separator
        while n < len(lines):
            cs2 = _cells(lines[n])
            if not cs2 or len(cs2) != len(cs):
                break
            label = _clean(cs2[0])
            if not label:
                break
            mnems = re.findall(r'[a-z][a-z0-9]*', label)
            vals = [_clean(cs2[k]) for k in idx]
            if any(v not in ('y', '.') for v in vals):
                break
            for m in mnems:
                out[m] = dict(zip(order, vals))
            n += 1
        if out:
            return out
    raise Refused('no table in %s has a header naming all of %s'
                  % (os.path.relpath(path, ROOT), ' '.join(want)))


def parse_probe(path):
    """An `isa-probe.sh` run: fixed-width, header names the arch order."""
    if not os.path.exists(path):
        raise Refused('%s does not exist' % path)
    txt = io.open(path, encoding='utf-8', errors='replace').read()
    lines = txt.split('\n')
    order, out, meta = None, {}, {}
    for ln in lines:
        if ln.startswith('assembler '):
            meta['assembler'] = ln.split(None, 1)[1].strip()
        elif ln.startswith('version '):
            meta['version'] = ln.split(None, 1)[1].strip()
        f = ln.split()
        if not f:
            continue
        if f[0] == 'instr':
            order = f[1:]
            continue
        if f[0] in PROBE_ROWS and order:
            vals = f[1:]
            if len(vals) != len(order):
                raise Refused('row %r has %d cells and the header names %d -- '
                              'a short row would read as a rejection'
                              % (f[0], len(vals), len(order)))
            if any(v not in ('y', '.') for v in vals):
                raise Refused('row %r holds a cell that is neither y nor .'
                              % f[0])
            out[f[0]] = dict(zip(order, vals))
    if not order:
        raise Refused('%s has no `instr` header line -- it is not an '
                      'isa-probe.sh table' % os.path.relpath(path, ROOT))
    if not out:
        raise Refused('%s names columns and holds no row' % path)
    return out, meta


def load(which):
    if which == 'predicted':
        return parse_md_matrix(PRED_DOC), {'source': 'docs/toolchain-prior-art.md § 8.1'}
    if which == 'committed':
        return parse_md_matrix(COMM_DOC), {'source': 'notes/vendor-kernel-isa.md § 6'}
    m, meta = parse_probe(which)
    meta['source'] = which
    return m, meta


def check_shape(m, name):
    f = []
    missing = [r for r in PROBE_ROWS if r not in m]
    extra = [r for r in m if r not in PROBE_ROWS]
    if missing:
        f.append('%s: the probe has %d row(s) this matrix does not -- %s'
                 % (name, len(missing), ' '.join(missing)))
    if extra:
        f.append('%s: this matrix has %d row(s) the probe does not -- %s'
                 % (name, len(extra), ' '.join(extra)))
    for r in sorted(set(m) & set(PROBE_ROWS)):
        miss = [a for a in PROBE_ARCHS if a not in m[r]]
        if miss:
            f.append('%s: row %s is missing column(s) %s'
                     % (name, r, ' '.join(miss)))
    return f


def diff(a, b):
    """[(instr, arch, a_val, b_val)] over the intersection."""
    out = []
    for r in PROBE_ROWS:
        if r not in a or r not in b:
            continue
        for c in PROBE_ARCHS:
            if c not in a[r] or c not in b[r]:
                continue
            if a[r][c] != b[r][c]:
                out.append((r, c, a[r][c], b[r][c]))
    return out


def render(m):
    w = max(len(a) for a in PROBE_ARCHS) + 1
    out = ['%-8s' % 'instr' + ''.join('%-*s' % (w, a) for a in PROBE_ARCHS)]
    for r in PROBE_ROWS:
        if r not in m:
            continue
        out.append('%-8s' % r + ''.join('%-*s' % (w, m[r].get(c, '?'))
                                        for c in PROBE_ARCHS))
    return '\n'.join(out)


def report_show(which):
    m, meta = load(which)
    print('source: %s' % meta.get('source'))
    f = check_shape(m, which)
    for x in f:
        print('  ' + x)
    print(render(m))
    print('cells: %d' % sum(len(v) for v in m.values()))
    return 1 if f else 0


def report_diff(a, b):
    ma, mta = load(a)
    mb, mtb = load(b)
    fa, fb = check_shape(ma, a), check_shape(mb, b)
    for x in fa + fb:
        print('  ' + x)
    d = diff(ma, mb)
    n = sum(1 for r in PROBE_ROWS if r in ma and r in mb
            for c in PROBE_ARCHS if c in ma[r] and c in mb[r])
    print('A = %s   (%s)' % (a, mta.get('source')))
    print('B = %s   (%s)' % (b, mtb.get('source')))
    if mta.get('assembler'):
        print('A assembler: %s' % mta['assembler'])
    if mtb.get('assembler'):
        print('B assembler: %s' % mtb['assembler'])
    for (r, c, x, y) in d:
        print('  DIFF %-6s %-9s A=%s  B=%s' % (r, c, x, y))
    print('RESULT: %d of %d cells agree, %d differ' % (n - len(d), n, len(d)))
    return 1 if (d or fa or fb) else 0


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

def self_test():
    import shutil
    import tempfile
    ok = fail = 0

    def case(cid, what, got, want):
        nonlocal ok, fail
        good = (got == want) if not callable(want) else want(got)
        if good:
            ok += 1
            print('  ok   %-4s %s' % (cid, what))
        else:
            fail += 1
            print('  FAIL %-4s %s -- got %r' % (cid, what, got))

    print('marchcmp self-test')
    try:
        pred, _ = load('predicted')
        comm, _ = load('committed')
    except Refused as e:
        print('  REFUSED: %s' % e)
        print('RESULT: REFUSING -- a matrix would not parse, so no control '
              'below means anything')
        return 1

    # C0 -- both tables must expand to the probe's exact shape.  A table that
    # parses to nineteen rows would make every comparison quietly partial.
    case('C0a', 'the predicted table expands to 20 rows x 8 columns',
         (len(pred), sorted(pred) == sorted(PROBE_ROWS),
          all(sorted(pred[r]) == sorted(PROBE_ARCHS) for r in pred)),
         (20, True, True))
    case('C0b', 'the committed table expands to 20 rows x 8 columns',
         (len(comm), sorted(comm) == sorted(PROBE_ROWS),
          all(sorted(comm[r]) == sorted(PROBE_ARCHS) for r in comm)),
         (20, True, True))

    # C1 -- the positive control.  A comparator that cannot report a
    # difference proves nothing by reporting none.
    import copy
    scuff = copy.deepcopy(pred)
    scuff['jalx']['mips1'] = '.' if scuff['jalx']['mips1'] == 'y' else 'y'
    case('C1', 'one flipped cell is reported, and exactly one',
         diff(pred, scuff), lambda g: len(g) == 1 and g[0][0] == 'jalx'
         and g[0][1] == 'mips1')

    # C2 -- the known difference between the two committed tables.  This is
    # the segment's own finding and it is here so that a later edit to either
    # file that silently removes it goes red.
    d = diff(pred, comm)
    case('C2', 'predicted vs committed: exactly the two cells § 7 ④ names',
         sorted((r, c) for (r, c, _, _) in d),
         [('cache', 'lx5280'), ('sync', 'rlx5181')])

    # C3 -- a probe output missing a column must REFUSE.
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, 'short.txt')
        io.open(p, 'w', encoding='utf-8').write(
            'instr       lx4180    rlx4181   rlx5181   lx5280    rlx5281   '
            'rlx4281   mips1     mips2\n'
            'lwl         y         y         y         y         y         '
            'y         y\n')
        try:
            parse_probe(p)
            case('C3', 'a probe row short by one column REFUSES', False, True)
        except Refused:
            case('C3', 'a probe row short by one column REFUSES', True, True)

        p2 = os.path.join(tmp, 'nothead.txt')
        io.open(p2, 'w', encoding='utf-8').write('lwl y y y y y y y y\n')
        try:
            parse_probe(p2)
            case('C3b', 'a file with no `instr` header REFUSES', False, True)
        except Refused:
            case('C3b', 'a file with no `instr` header REFUSES', True, True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # C4 -- the expansion is the whole reason this tool exists: the markdown
    # tables have ten rows and the probe has twenty.  Both directions.
    case('C4', 'the grouped tables expand to the probe rows, both directions',
         (sorted(set(pred) - set(PROBE_ROWS)), sorted(set(PROBE_ROWS) - set(pred)),
          sorted(set(comm) - set(PROBE_ROWS)), sorted(set(PROBE_ROWS) - set(comm))),
         ([], [], [], []))

    # C5 -- a header that does not name every arch must not be taken as the
    # matrix.  Both documents hold other tables with pipes in them.
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, 'decoy.md')
        io.open(p, 'w', encoding='utf-8').write(
            '| a | b |\n|---|---|\n| x | y |\n')
        try:
            parse_md_matrix(p)
            case('C5', 'a document with no arch header REFUSES', False, True)
        except Refused:
            case('C5', 'a document with no arch header REFUSES', True, True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('RESULT: %d/%d' % (ok, ok + fail))
    return 1 if fail else 0


def main(argv):
    ap = argparse.ArgumentParser(prog='marchcmp.py')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('mode', nargs='?', choices=('show', 'parse', 'diff'))
    ap.add_argument('args', nargs='*')
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.mode is None:
        ap.print_help()
        return 3
    try:
        if a.mode == 'show':
            if len(a.args) != 1:
                raise Refused('show takes one of predicted or committed')
            return report_show(a.args[0])
        if a.mode == 'parse':
            if len(a.args) != 1:
                raise Refused('parse takes one probe output file')
            m, meta = parse_probe(a.args[0])
            for k in sorted(meta):
                print('%-10s %s' % (k, meta[k]))
            f = check_shape(m, a.args[0])
            for x in f:
                print('  ' + x)
            print(render(m))
            return 1 if f else 0
        if len(a.args) != 2:
            raise Refused('diff takes two matrices')
        return report_diff(a.args[0], a.args[1])
    except Refused as e:
        sys.stderr.write('marchcmp.py: REFUSED -- %s\n' % e)
        sys.stderr.write('  Nothing is reported: an empty matrix and a matrix '
                         'of rejections are different answers.\n')
        return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
