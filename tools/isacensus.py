#!/usr/bin/env python3
"""isacensus.py -- the ISA census's two axes, derived rather than remembered.

`R1-pub-0` has to say what this repository ALREADY holds about this core's
instruction set and its hazards, dated, before any `R1a`/`R1b` payload source
exists.  A hand-written list would be a claim; this derives both axes from the
repository's own instruments and joins them against one adjudication table.

  axis A -- the POPULATION.  Which instructions get a row in `R1a`'s table, and
            which shapes get a row in `R1b`'s.  Not "every MIPS instruction":
            the population is "what this core is not known to implement", and
            that set already exists in two instruments --

              * `tools/hazlint`'s `ISA_OPS` and `ISA_TRAPS`, whose membership
                rule the tool states itself (MIPS-I MINUS the four unaligned
                ones, because a Lexra core is that; everything above MIPS-I;
                and MIPS-I's own optional coprocessors 2 and 3);
              * `tools/isa-probe.sh`'s probe rows, i.e. what the vendor's own
                assembler was actually asked about.

            Neither covers the other: `movz`/`movn` are SPECIAL functs and so
            are absent from `ISA_OPS`, while `bnel`/`blezl`/`bgtzl` and the six
            trap instructions are absent from `isa-probe.sh`.  The union is the
            population, and `check` fires when either instrument grows.

            `R1b`'s population comes from `hazlint.survey()`'s own keys -- the
            shapes it counts and refuses to give a verdict on, which is exactly
            "the shapes R1b goes and measures" in its docstring.

  axis B -- the PRIOR ART, per row, on four evidence routes.  `tools/isa-census.tsv`
            adjudicates; this tool checks that adjudication against the tree in
            both directions and will not print a census it cannot check.

Four routes, because this repository already marks with them and three of the
four are NOT a bare-metal reading:

  (1)  量 on the die, by a payload of ours, under a handler of ours.
  (2)  量 on the die INDIRECTLY: code that has run on this part contains the
       encoding, and the boot completes with no exception message.  On every row
       here that code is the loader's or the vendor kernel's -- 量 2026-09-12,
       `hazlint` reports 0 violations on three images of this project's that have
       booted, so nothing of ours contributes a route-(2) reading.  `SPEC.md`
       `CPU-17` already carries exactly this mark -- 讀(count) · 量(the absence).
  (3)  讀 vendor material: the assembler's per-`-march` answer, a Kconfig knob,
       a count in a binary.  Never the die.  §6 of `notes/vendor-kernel-isa.md`
       records the two vendor sources DISAGREEING about `ll`/`sc`.
  (4)  nothing.

What route (2) cannot see is the whole reason `R1a` exists, so it is written
into this tool rather than left to the write-up: an instruction that decodes as
a nop, or as something else, RETIRES.  No message, no fault, wrong value --
`F46`'s shape exactly.  Route (2) is sound for *does not trap* and silent on
*computes the right answer*, which is the cell `R1a`'s three-way verdict exists
to fill.

Usage
    isacensus.py population        both populations with their provenance
    isacensus.py census            the joined table and the counts
    isacensus.py check             the two-way check, and the doc's blocks
    isacensus.py write             regenerate the doc's blocks, then check
    isacensus.py --self-test       the controls

Exit
    0  clean
    1  a finding
    3  REFUSED -- an instrument could not be read, so nothing is reported.  An
       empty population and a population of absences are different answers.
"""
import argparse
import importlib.machinery
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TSV = os.path.join(HERE, 'isa-census.tsv')
DOC = os.path.join(ROOT, 'docs', 'isa-prior-art.md')

COLS = ('kind', 'name', 'src', 'r1', 'r2', 'r3', 'spec', 'seat', 'cite', 'note')
KINDS = ('r1a', 'r1b')
SRCS = ('derived', 'declared')
FLAGS = ('y', '.')

BEGIN = '<!-- isacensus:%s begin -->'
END = '<!-- isacensus:%s end -->'


class Refused(Exception):
    pass


# --------------------------------------------------------------------------
# axis A -- the population, from the instruments
# --------------------------------------------------------------------------

def load_hazlint(path=None):
    """Import `tools/hazlint`.  It has no `.py`, so this is by loader."""
    path = path or os.path.join(HERE, 'hazlint')
    if not os.path.exists(path):
        raise Refused('hazlint not found at %s' % path)
    loader = importlib.machinery.SourceFileLoader('hazlint_mod', path)
    spec = importlib.util.spec_from_loader('hazlint_mod', loader)
    mod = importlib.util.module_from_spec(spec)
    try:
        loader.exec_module(mod)
    except Exception as e:                                   # pragma: no cover
        raise Refused('hazlint would not import: %r' % (e,))
    for attr in ('ISA_OPS', 'ISA_TRAPS', 'survey'):
        if not hasattr(mod, attr):
            raise Refused('hazlint has no %s -- its watch list moved' % attr)
    return mod


PROBE_ROW_RX = re.compile(r'''^row\s+"([a-z0-9]+)"\s+['"]''')


def probe_rows(path=None):
    """The mnemonics `isa-probe.sh` actually probes.

    Anchored, and it requires a QUOTED label followed by a quoted instruction.
    量 2026-09-12: a plain `grep -c '^row '` over this file returns 21, because
    it also counts the shell function DEFINITION -- `row () { # label insn`.
    The count was wrong by one in the direction that reads as more coverage,
    and it was caught only because the same quantity was counted a second way
    and the members listed.  Hence the shape of this regex.
    """
    path = path or os.path.join(HERE, 'isa-probe.sh')
    if not os.path.exists(path):
        raise Refused('isa-probe.sh not found at %s' % path)
    names = []
    with io.open(path, encoding='utf-8') as f:
        for ln in f:
            m = PROBE_ROW_RX.match(ln)
            if m:
                names.append(m.group(1))
    if not names:
        raise Refused('isa-probe.sh probes nothing -- its row form moved')
    return names


def population(hz=None, probe_path=None):
    """(r1a, r1b) -- each a dict name -> sorted list of provenance tags."""
    hz = hz or load_hazlint()
    r1a = {}

    def add(name, tag):
        r1a.setdefault(name, set()).add(tag)

    for op, (name, level) in sorted(hz.ISA_OPS.items()):
        add(name, 'hazlint:ISA_OPS(0x%02X,%s)' % (op, level))
    for f, name in sorted(hz.ISA_TRAPS.items()):
        add(name, 'hazlint:ISA_TRAPS(0x%02X)' % f)
    for name in probe_rows(probe_path):
        add(name, 'isa-probe.sh:row')

    keys = hz.survey([])
    if not keys:
        raise Refused('hazlint.survey() reports no shapes -- it has no keys')
    r1b = dict((k, {'hazlint:survey'}) for k in keys)

    return ({k: sorted(v) for k, v in r1a.items()},
            {k: sorted(v) for k, v in r1b.items()})


# --------------------------------------------------------------------------
# axis B -- the adjudication table
# --------------------------------------------------------------------------

def read_tsv(path=None):
    path = path or TSV
    if not os.path.exists(path):
        raise Refused('adjudication table not found at %s' % path)
    rows, header = [], None
    with io.open(path, encoding='utf-8') as f:
        for n, ln in enumerate(f, 1):
            if ln.startswith('#') or not ln.strip():
                continue
            cells = ln.rstrip('\n').split('\t')
            if header is None:
                header = cells
                if tuple(header) != COLS:
                    raise Refused('table header is %r, expected %r'
                                  % (header, list(COLS)))
                continue
            if len(cells) != len(COLS):
                raise Refused('line %d has %d cells, header has %d'
                              % (n, len(cells), len(COLS)))
            rows.append(dict(zip(COLS, cells), _line=n))
    if header is None:
        raise Refused('adjudication table has no header')
    if not rows:
        raise Refused('adjudication table has no rows')
    return rows


def route_of(row):
    if row['r1'] == 'y':
        return 1
    if row['r2'] == 'y':
        return 2
    if row['r3'] == 'y':
        return 3
    return 4


ROUTE_NAME = {1: 'bare metal, ours', 2: 'on the die, vendor code',
              3: 'vendor material only', 4: 'nothing'}


# --------------------------------------------------------------------------
# spec ids, through SPEC.md's own parser
# --------------------------------------------------------------------------

def spec_ids(root=None):
    root = root or ROOT
    p = os.path.join(root, 'tools', 'spec-check.py')
    if not os.path.exists(p):
        raise Refused('spec-check.py not found -- cannot resolve SPEC ids')
    loader = importlib.machinery.SourceFileLoader('speccheck_mod', p)
    spec = importlib.util.spec_from_loader('speccheck_mod', loader)
    sc = importlib.util.module_from_spec(spec)
    try:
        loader.exec_module(sc)
    except Exception as e:
        raise Refused('spec-check.py would not import: %r' % (e,))
    tables, _ = sc.parse(os.path.join(root, 'SPEC.md'))
    out = {}
    for t in tables:
        i = sc.col(t, 'id')
        if i is None:
            continue
        for (ln, cells, span) in t['rows']:
            if i >= len(cells):
                continue
            cell = cells[i].strip()
            m = sc.ID_RX.match(cell)
            if m:
                out.setdefault(m.group(1), []).append(ln)
            # ID_RX requires TWO DIGITS after the dash, so `TC-h` -- a real
            # §17 row id -- does not match it.  Take the bare leading token as
            # well, or a row this table cites would read as undefined.
            raw = cell.replace('*', '').replace('`', '').replace('~', '')
            raw = raw.strip().split()
            if raw:
                out.setdefault(raw[0], []).append(ln)
    if not out:
        raise Refused('no SPEC ids parsed -- the id column moved')
    return out


# --------------------------------------------------------------------------
# rendering -- the blocks the document holds
# --------------------------------------------------------------------------

def fmt_spec(cell):
    if cell == '-':
        return '—'
    return ', '.join('`%s`' % s.strip() for s in cell.split(',') if s.strip())


def fmt_seat(cell):
    if cell == '-':
        return '—'
    if cell == 'upstream':
        return '`upstream/`'
    return '`bench/%s`' % cell


def render(rows, kind):
    sel = [r for r in rows if r['kind'] == kind]
    sel.sort(key=lambda r: (route_of(r), r['name']))
    out = ['| row | ① | ② | ③ | `SPEC.md` | reading taken at | what is still open |',
           '|---|:-:|:-:|:-:|---|---|---|']
    for r in sel:
        out.append('| `%s` | %s | %s | %s | %s | %s | %s |'
                   % (r['name'], r['r1'], r['r2'], r['r3'],
                      fmt_spec(r['spec']), fmt_seat(r['seat']), r['note']))
    return '\n'.join(out)


def render_counts(rows):
    out = ['| | ① bare metal, ours | ② vendor code on the die | ③ vendor material only | ④ nothing | total |',
           '|---|---:|---:|---:|---:|---:|']
    for kind, label in (('r1a', '`R1a` instruction rows'),
                        ('r1b', '`R1b` hazard rows')):
        sel = [r for r in rows if r['kind'] == kind]
        c = [len([r for r in sel if route_of(r) == k]) for k in (1, 2, 3, 4)]
        out.append('| %s | %d | %d | %d | %d | **%d** |'
                   % (label, c[0], c[1], c[2], c[3], len(sel)))
    return '\n'.join(out)


def doc_block(text, tag):
    b, e = BEGIN % tag, END % tag
    if b not in text or e not in text:
        return None
    return text.split(b, 1)[1].split(e, 1)[0].strip('\n')


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

def check(tsv_path=None, doc_path=None, root=None, probe_path=None,
          haz_path=None):
    """Return a list of findings.  Empty is clean."""
    f = []
    hz = load_hazlint(haz_path)
    r1a, r1b = population(hz, probe_path)
    rows = read_tsv(tsv_path)
    ids = spec_ids(root)

    derived = {'r1a': set(r1a), 'r1b': set(r1b)}
    by_kind = {}
    for r in rows:
        if r['kind'] not in KINDS:
            f.append('K0 line %d: kind %r is not one of %r'
                     % (r['_line'], r['kind'], list(KINDS)))
            continue
        if r['src'] not in SRCS:
            f.append('K0 line %d: src %r is not one of %r'
                     % (r['_line'], r['src'], list(SRCS)))
            continue
        for c in ('r1', 'r2', 'r3'):
            if r[c] not in FLAGS:
                f.append('K0 line %d: %s is %r, not y or .'
                         % (r['_line'], c, r[c]))
        by_kind.setdefault(r['kind'], []).append(r)

    for kind in KINDS:
        sel = by_kind.get(kind, [])
        named = [r['name'] for r in sel]
        # K8 -- one quantity, two atomic units.  A duplicated name makes the
        # row count exceed the distinct-name count, and a census whose total
        # depends on which unit you counted is not a total.
        if len(named) != len(set(named)):
            dups = sorted(set(n for n in named if named.count(n) > 1))
            f.append('K8 %s: %d rows but %d distinct names -- %s'
                     % (kind, len(named), len(set(named)), ', '.join(dups)))
        d = set(r['name'] for r in sel if r['src'] == 'derived')
        dec = set(r['name'] for r in sel if r['src'] == 'declared')
        for missing in sorted(derived[kind] - d):
            f.append('K1 %s: the instruments derive %r and the table has no '
                     'derived row for it' % (kind, missing))
        for stale in sorted(d - derived[kind]):
            f.append('K2 %s: the table has a derived row %r that no '
                     'instrument derives' % (kind, stale))
        for both in sorted(dec & derived[kind]):
            f.append('K4 %s: %r is declared AND derived -- it would be '
                     'counted twice' % (kind, both))

    for r in rows:
        if r['src'] == 'declared':
            # K3 -- a declared population member must be citable, or the
            # population is tunable by whoever writes the table.
            cite = r['cite']
            if cite == '-' or ':' not in cite:
                f.append('K3 line %d: declared row %r has no path:token cite'
                         % (r['_line'], r['name']))
            else:
                rel, tok = cite.split(':', 1)
                p = os.path.join(root or ROOT, rel)
                if not os.path.exists(p):
                    f.append('K3 line %d: cite path %s does not exist'
                             % (r['_line'], rel))
                elif tok not in io.open(p, encoding='utf-8').read():
                    f.append('K3 line %d: %s does not contain the cited token '
                             '%r' % (r['_line'], rel, tok))
        elif r['cite'] != '-':
            f.append('K3 line %d: derived row %r carries a cite; only a '
                     'declared row may' % (r['_line'], r['name']))

        for sid in [s.strip() for s in r['spec'].split(',') if s.strip()]:
            if sid == '-':
                continue
            if sid not in ids:
                f.append('K5 line %d: %r cites SPEC id %s, which SPEC.md does '
                         'not define' % (r['_line'], r['name'], sid))

        # K6/K7 -- a seating may be named only where there is a route-(1)
        # reading, and it has to exist.  Either direction wrong would let the
        # strongest column be claimed without evidence.
        if r['r1'] == 'y':
            if r['seat'] == '-':
                f.append('K6 line %d: %r claims route (1) and names no seating'
                         % (r['_line'], r['name']))
            elif r['seat'] == 'upstream':
                # The one route-(1) ISA reading this project holds that is not
                # its own is upstream's, on the same physical device.  It gets
                # a legal seat value of its own so that the provenance is
                # visible in the table rather than flattened into a bench dir.
                if not os.path.exists(os.path.join(root or ROOT, 'upstream',
                                                   'BENCH-LOG.md')):
                    f.append('K6 line %d: %r names the upstream seating and '
                             'upstream/BENCH-LOG.md is not there'
                             % (r['_line'], r['name']))
            elif not os.path.isdir(os.path.join(root or ROOT, 'bench',
                                                r['seat'])):
                f.append('K6 line %d: %r names seating %s, and bench/%s is '
                         'not a directory'
                         % (r['_line'], r['name'], r['seat'], r['seat']))
        elif r['seat'] != '-':
            f.append('K7 line %d: %r is not route (1) and yet names seating %s'
                     % (r['_line'], r['name'], r['seat']))

    # K9 -- the document may not drift from the derivation.
    dp = doc_path or DOC
    if not os.path.exists(dp):
        f.append('K9 %s does not exist, so its blocks cannot be checked'
                 % os.path.relpath(dp, root or ROOT))
    else:
        text = io.open(dp, encoding='utf-8').read()
        for tag, want in (('r1a', render(rows, 'r1a')),
                          ('r1b', render(rows, 'r1b')),
                          ('counts', render_counts(rows))):
            got = doc_block(text, tag)
            if got is None:
                f.append('K9 %s has no isacensus:%s block'
                         % (os.path.basename(dp), tag))
            elif got != want:
                f.append('K9 the isacensus:%s block in %s is not what this '
                         'tool derives' % (tag, os.path.basename(dp)))
    return f


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def report_population():
    r1a, r1b = population()
    print('axis A -- the R1a population, from the instruments')
    print('  %d instruction rows' % len(r1a))
    for name in sorted(r1a):
        print('    %-10s %s' % (name, '  '.join(r1a[name])))
    only_h = [n for n in r1a if not any('isa-probe' in t for t in r1a[n])]
    only_p = [n for n in r1a if not any('hazlint' in t for t in r1a[n])]
    print('  neither instrument covers the other, which is why the union is '
          'the population:')
    print('    hazlint only     %2d  %s' % (len(only_h), ' '.join(sorted(only_h))))
    print('    isa-probe only   %2d  %s' % (len(only_p), ' '.join(sorted(only_p))))
    print()
    print('axis A -- the R1b population, from hazlint.survey()')
    print('  %d hazard shapes' % len(r1b))
    for name in sorted(r1b):
        print('    %s' % name)
    return 0


def report_census():
    rows = read_tsv()
    print(render_counts(rows))
    print()
    print(render(rows, 'r1a'))
    print()
    print(render(rows, 'r1b'))
    return 0


def report_check():
    f = check()
    for x in f:
        print('  ' + x)
    print('RESULT: %s' % ('ok, %d row(s) checked both ways'
                          % len(read_tsv()) if not f
                          else '%d finding(s)' % len(f)))
    return 1 if f else 0


def write_blocks(doc_path=None, tsv_path=None):
    """Regenerate the document's marked blocks in place.

    The blocks are DERIVED, so the tool that derives them writes them; hand
    copying is what `K9` would then be catching, one edit too late.  Nothing
    outside the markers is touched -- `T17` is the control on that -- and the
    write is build-the-whole-string / .tmp / replace, because a script that
    truncates before it raises has emptied a committed file here before.
    """
    dp = doc_path or DOC
    rows = read_tsv(tsv_path)
    text = io.open(dp, encoding='utf-8').read()
    out, changed = text, []
    for tag, want in (('r1a', render(rows, 'r1a')), ('r1b', render(rows, 'r1b')),
                      ('counts', render_counts(rows))):
        b, e = BEGIN % tag, END % tag
        if b not in out or e not in out:
            raise Refused('%s has no isacensus:%s block'
                          % (os.path.basename(dp), tag))
        head, rest = out.split(b, 1)
        old, tail = rest.split(e, 1)
        if old.strip('\n') != want:
            changed.append(tag)
        out = head + b + '\n' + want + '\n' + e + tail
    if out != text:
        tmp = dp + '.tmp'
        io.open(tmp, 'w', encoding='utf-8', newline='\n').write(out)
        os.replace(tmp, dp)
    return changed


def report_write():
    changed = write_blocks()
    if changed:
        print('rewrote block(s): %s' % ', '.join(changed))
    else:
        print('every block already matched the derivation -- nothing written')
    return report_check()


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

def _fixture(tmp, tsv_lines=None, doc_text=None):
    """A working copy of the two files this tool checks, for one mutation."""
    tp = os.path.join(tmp, 'isa-census.tsv')
    dp = os.path.join(tmp, 'isa-prior-art.md')
    if tsv_lines is None:
        tsv_lines = io.open(TSV, encoding='utf-8').read().split('\n')
    io.open(tp, 'w', encoding='utf-8', newline='\n').write('\n'.join(tsv_lines))
    if doc_text is None:
        doc_text = io.open(DOC, encoding='utf-8').read()
    io.open(dp, 'w', encoding='utf-8', newline='\n').write(doc_text)
    return tp, dp


def _first_data_line(lines):
    for i, ln in enumerate(lines):
        if ln.startswith('#') or not ln.strip():
            continue
        if ln.split('\t')[0] == 'kind':
            continue
        return i
    raise AssertionError('fixture has no data line')


def self_test():
    import shutil
    import tempfile
    ok = fail = 0

    def case(cid, what, got, want):
        nonlocal ok, fail
        good = (got == want) if not callable(want) else want(got)
        if good:
            ok += 1
            print('  ok   %-5s %s' % (cid, what))
        else:
            fail += 1
            print('  FAIL %-5s %s -- got %r' % (cid, what, got))

    def fired(cid, prefix, mutate, what):
        tmp = tempfile.mkdtemp()
        try:
            lines = io.open(TSV, encoding='utf-8').read().split('\n')
            doc = io.open(DOC, encoding='utf-8').read()
            lines, doc = mutate(lines, doc)
            tp, dp = _fixture(tmp, lines, doc)
            f = check(tsv_path=tp, doc_path=dp)
            case(cid, what, any(x.startswith(prefix) for x in f), True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print('isacensus self-test')

    # T0 -- the unmutated pair must be clean, or every "fired" below is a
    # control on an already-red tool.
    tmp = tempfile.mkdtemp()
    try:
        tp, dp = _fixture(tmp)
        base = check(tsv_path=tp, doc_path=dp)
        case('T0', 'the committed table and document are clean', base, [])
        if base:
            for x in base:
                print('       ' + x)
            print('RESULT: REFUSING -- the unmutated pair is already red, so '
                  'no control below means anything')
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def drop_derived(lines, doc):
        i = _first_data_line(lines)
        for j in range(i, len(lines)):
            c = lines[j].split('\t')
            if len(c) == len(COLS) and c[2] == 'derived':
                return lines[:j] + lines[j + 1:], doc
        raise AssertionError('no derived row to drop')

    def add_bogus(lines, doc):
        row = ['r1a', 'zzfake', 'derived', '.', '.', '.', '-', '-', '-', 'x']
        return lines + ['\t'.join(row)], doc

    def declared_as_derived(lines, doc):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[2] == 'declared':
                c[1] = sorted(population()[0])[0]
                c[2] = 'declared'
                lines = lines[:j] + ['\t'.join(c)] + lines[j + 1:]
                return lines, doc
        raise AssertionError('no declared row')

    def break_cite(lines, doc):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[2] == 'declared':
                c[8] = 'tools/hazlint:a token that is not in that file at all'
                return lines[:j] + ['\t'.join(c)] + lines[j + 1:], doc
        raise AssertionError('no declared row')

    def bad_spec(lines, doc):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[6] not in ('-', 'spec'):
                c[6] = 'ZZZ-99'
                return lines[:j] + ['\t'.join(c)] + lines[j + 1:], doc
        raise AssertionError('no row citing SPEC')

    def bad_seat(lines, doc):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[3] == 'y':
                c[7] = '1999-01-01'
                return lines[:j] + ['\t'.join(c)] + lines[j + 1:], doc
        raise AssertionError('no route-(1) row')

    def seat_without_route1(lines, doc):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[3] == '.':
                c[7] = '2026-08-30'
                return lines[:j] + ['\t'.join(c)] + lines[j + 1:], doc
        raise AssertionError('no non-route-(1) row')

    def duplicate_name(lines, doc):
        i = _first_data_line(lines)
        return lines + [lines[i]], doc

    def scuff_doc(lines, doc):
        return lines, doc.replace('| `cache` |', '| `cachex` |', 1)

    fired('T1', 'K1', drop_derived,
          'a derived row missing from the table is caught')
    fired('T2', 'K2', add_bogus,
          'a table row no instrument derives is caught')
    fired('T3', 'K4', declared_as_derived,
          'a declared row that is also derived is caught')
    fired('T4', 'K3', break_cite,
          'a declared row whose cited token is absent is caught')
    fired('T5', 'K5', bad_spec,
          'a SPEC id SPEC.md does not define is caught')
    fired('T6', 'K6', bad_seat,
          'a route-(1) row naming a seating that does not exist is caught')
    fired('T7', 'K7', seat_without_route1,
          'a seating named without a route-(1) reading is caught')
    fired('T8', 'K8', duplicate_name,
          'a duplicated name is caught by the two-unit count')
    fired('T9', 'K9', scuff_doc,
          'one character changed in the document block is caught')

    # T10-T13 -- the refusals.  A tool that reports on an instrument it could
    # not read is the failure this repository keeps catching.
    def refuses(cid, what, fn):
        try:
            fn()
        except Refused:
            case(cid, what, True, True)
            return
        case(cid, what, False, True)

    refuses('T10', 'no hazlint -> REFUSED, not an empty population',
            lambda: load_hazlint(os.path.join(HERE, 'hazlint-does-not-exist')))
    refuses('T11', 'no isa-probe.sh -> REFUSED',
            lambda: probe_rows(os.path.join(HERE, 'isa-probe-nope.sh')))

    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, 'isa-probe.sh')
        io.open(p, 'w', encoding='utf-8').write(
            'row () { # label insn\n  echo hi\n}\n')
        refuses('T12', 'an isa-probe.sh whose only `row` line is the function '
                       'DEFINITION probes nothing -> REFUSED',
                lambda: probe_rows(p))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    class NoSurvey:
        ISA_OPS = {0x22: ('lwl', 'x')}
        ISA_TRAPS = {}

        @staticmethod
        def survey(spans):
            return {}

    refuses('T13', 'hazlint.survey() with no keys -> REFUSED',
            lambda: population(NoSurvey()))

    # T14 -- the population is a UNION and each instrument contributes
    # something the other does not.  If that stops being true, one of the two
    # is redundant and the union's cost should be re-argued.
    r1a, _ = population()
    only_h = [n for n in r1a if not any('isa-probe' in t for t in r1a[n])]
    only_p = [n for n in r1a if not any('hazlint' in t for t in r1a[n])]
    case('T14', 'both instruments contribute a row the other does not',
         (len(only_h) > 0, len(only_p) > 0), (True, True))

    # T15 -- the probe-row regex counts what a member listing counts.
    names = probe_rows()
    case('T15', 'probe rows: as many rows as distinct mnemonics',
         (len(names), len(set(names))), lambda g: g[0] == g[1] and g[0] > 0)

    # T16/T17 -- `write` is the mode that makes the blocks generated rather
    # than copied, so it needs the two properties a generator must have: it
    # repairs a scuffed block, and it touches nothing else.
    tmp = tempfile.mkdtemp()
    try:
        tp, dp = _fixture(tmp)
        scuffed = io.open(dp, encoding='utf-8').read().replace(
            '| `cache` |', '| `cachex` |', 1)
        io.open(dp, 'w', encoding='utf-8', newline='\n').write(scuffed)
        changed = write_blocks(doc_path=dp, tsv_path=tp)
        case('T16', 'write repairs a scuffed block and check then passes',
             ('r1a' in changed, check(tsv_path=tp, doc_path=dp)),
             lambda g: g[0] and g[1] == [])
        # outside the markers: compare everything the blocks do not cover
        def outside(s):
            for tag in ('r1a', 'r1b', 'counts'):
                b, e = BEGIN % tag, END % tag
                head, rest = s.split(b, 1)
                _, tail = rest.split(e, 1)
                s = head + b + e + tail
            return s
        case('T17', 'write touches nothing outside the markers',
             outside(io.open(dp, encoding='utf-8').read()),
             outside(io.open(DOC, encoding='utf-8').read()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('RESULT: %d/%d' % (ok, ok + fail))
    return 1 if fail else 0


def main(argv):
    ap = argparse.ArgumentParser(prog='isacensus.py')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('mode', nargs='?',
                    choices=('population', 'census', 'check', 'write'))
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.mode is None:
        ap.print_help()
        return 3
    try:
        return {'population': report_population, 'census': report_census,
                'check': report_check, 'write': report_write}[a.mode]()
    except Refused as e:
        sys.stderr.write('isacensus.py: REFUSED -- %s\n' % e)
        sys.stderr.write('  Nothing is reported: an empty census and a census '
                         'of absences are different answers.\n')
        return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
