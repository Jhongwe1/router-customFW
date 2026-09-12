#!/usr/bin/env python3
"""tccensus.py -- the TOOLCHAIN axis of the census, derived rather than remembered.

`R1-pub-0b` has to say what this repository ALREADY holds about the toolchains
before `R1-pub-6` builds `R2c`'s three-column table.  `tools/isacensus.py` did
the same job for the ISA axis on 2026-09-12; this is its sibling, and it
IMPORTS that tool rather than extending or copying it.

Why a second tool and not a third `kind` in the first one, decided 2026-09-12
on two measurements and one precedent:

  * `isacensus.py`'s NAME is pinned.  量: seven references in `LOG.md`, which
    is a historical record this project does not rewrite.  A tool called
    `isacensus` that also adjudicates toolchains would be `config/host-compat/`
    again -- a name narrower than its contents with no path out.
  * Extending would COUPLE two frozen artefacts through one control.
    `isacensus --self-test` `T0` asserts *the committed table and document are
    clean*; a defect in the toolchain table would turn the ISA census's gate
    red.  This repository already carries that shape as a recorded defect: a
    red `text` job hides the census entirely, so one push shows one layer.
  * `tools/flashmap.py` importing `flashwin.overlaps_forbidden` instead of
    restating the rule is this repository's own precedent for
    import-don't-restate.

What is shared is the join machinery: `read_tsv` (header must match exactly, a
short line is a REFUSAL and not a skipped row), `spec_ids` (through SPEC.md's
own parser), `doc_block`, and `Refused`.  What is NOT shared is every rule
below, because the axis is different -- see the routes.

  axis A -- the POPULATION.
      `r2c`  one RECORDED TOOLCHAIN FINDING.  Derived from `SPEC.md` through
             `tools/spec-check.py`'s own parser: every id in an id column whose
             first token starts `TC-`.  量 2026-09-12: 48 in § 14 and one --
             `TC-h` -- that exists only in § 17.
      `r2t`  one TOOLCHAIN RELEASE.  Derived from `config/rlxfw-sdk.config`'s
             `CONFIG_RSDK_*` lines, which are the only committed CLOSED set of
             the releases on hand.  A release this project can name but does
             not have is a `declared` row with a cite.

  🔴 The population's own weakness, stated here because it is the difference
  from the ISA axis and it does not go away.  `hazlint` and `isa-probe.sh`
  are CODE -- they enumerate what an instrument can ask, so the ISA census's
  population was independent of what had been written down.  `SPEC.md` is the
  RECORD.  A population derived from it is the record auditing itself, and it
  cannot see a toolchain fact this project measured and never recorded.
  `U14` is the control that keeps that from being a sentence nobody tests: the
  table must hold at least one `declared` row per kind, because a census that
  derives everything from the record has not looked outside it.

  axis B -- the PRIOR ART, per row, on four routes AND one flag.  The routes
  are NOT the ISA axis's and must not be read across:

      (1)  量 on a toolchain IN HAND -- this project executed that compiler or
           assembler and measured its output.  On this axis route (1) is DESK
           work; it costs no power, which is the whole reason the scope answer
           in § 6 comes out the way it does.
      (2)  量 on an ARTEFACT -- a shipped binary or a device reading, from
           which a toolchain property is inferred.  The toolchain itself was
           never run.  `.comment`, a kernel banner, an ELF flag word.
      (3)  讀 vendor material -- a Makefile, a wrapper log, a `.config`, or
           source says so and nothing was executed.
      (4)  nothing.

      ⓟ  PUBLIC PRIOR ART exists for this row.  This flag has no counterpart
         in the ISA census and it is the structural difference between the two
         axes.  `R1-pub`'s claim is *this is not in public data*; on the die
         that holds, and on the TOOLCHAIN it largely does not -- the Lexra
         binutils patch is a public gist and the rsdk releases are on GitHub.
         A census that leaves that out is the résumé failure this project
         keeps naming, so it is a column and it is counted.

  `subj` -- whether the row is a statement about a TOOLCHAIN or about the DIE.
  The step table asks for this in those words.  `L10` requires every row to
  carry one; there is no `-`.

  `mx` -- a declared exception to `L12`, the mark-consistency check.  `SPEC.md`
  carries a V mark per row (量 / 讀 / 推 / 文 / —).  A route claimed here that
  its V mark does not support is a disagreement between two files, and `L12`
  makes it one that has to be declared rather than one nobody notices.

Usage
    tccensus.py population        both populations with their provenance
    tccensus.py census            the joined table and the counts
    tccensus.py check             the two-way check, and the doc's blocks
    tccensus.py write             regenerate the doc's blocks, then check
    tccensus.py --self-test       the controls

Exit
    0  clean
    1  a finding
    3  REFUSED -- an instrument could not be read, so nothing is reported.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import isacensus                                          # noqa: E402
from isacensus import Refused, doc_block                   # noqa: E402

TSV = os.path.join(HERE, 'toolchain-census.tsv')
DOC = os.path.join(ROOT, 'docs', 'toolchain-prior-art.md')
SDK = os.path.join(ROOT, 'config', 'rlxfw-sdk.config')

COLS = ('kind', 'name', 'src', 'subj', 'r1', 'r2', 'r3', 'p', 'mx',
        'spec', 'seat', 'cite', 'note')
KINDS = ('r2c', 'r2t')
SRCS = ('derived', 'declared')
SUBJ = ('tc', 'die', 'both')
FLAGS = ('y', '.')

BEGIN = '<!-- tccensus:%s begin -->'
END = '<!-- tccensus:%s end -->'

ROUTE_NAME = {1: 'a toolchain in hand, run by us',
              2: 'an artefact, toolchain inferred',
              3: 'vendor material only, never run',
              4: 'nothing'}

# A V mark and the STRONGEST route it supports, as a route number -- and note
# that a lower number is a stronger route, so this is a floor on the number
# and not a ceiling on the evidence.  `量` says this project measured the
# VALUE; it does not say what it measured it on, so (1) and (2) are both open
# to it.  `讀`/`文` cannot reach past (3).  `推`/`—` has no evidence at all.
# A row claiming stronger than its mark supports is a disagreement between two
# files, and `L12` makes it one that has to be declared with `mx=y`.
MARK_MAX = {'量': 1, '讀': 2, '文': 3, '推': 4, '—': 4, '': 4}


# --------------------------------------------------------------------------
# axis A -- the populations, from the instruments
# --------------------------------------------------------------------------

TC_RX = re.compile(r'^TC-')


def spec_tc(root=None):
    """{id: {'lines': [...], 'v': mark or '', 'tables': set}} for every TC-* row.

    Through `spec-check.py`'s parser, not a grep.  量 2026-09-12: a grep for
    `TC-` over SPEC.md also matches the id INSIDE a prose cell -- `TC-22`'s
    value cell names `TC-15`, `TC-h` and `TC-g` -- so a grep-derived population
    would be a function of what the notes happen to cross-reference.

    Which TABLE a row came from is taken from that table's own header (a `項目`
    column is the findings table, a `缺什麼` column is the blank list), never
    from a line number, so a row moving down the file does not reclassify it.
    """
    root = root or ROOT
    sc = _spec_check(root)
    tables, _ = sc.parse(os.path.join(root, 'SPEC.md'))
    out = {}
    for t in tables:
        i = sc.col(t, 'id')
        if i is None:
            continue
        iv = sc.col(t, 'V')
        kind = ('findings' if sc.col(t, '項目') is not None else
                'blanks' if sc.col(t, '缺什麼') is not None else 'other')
        for (ln, cells, span) in t['rows']:
            if i >= len(cells):
                continue
            raw = cells[i].replace('*', '').replace('`', '').replace('~', '')
            raw = raw.strip().split()
            if not raw or not TC_RX.match(raw[0]):
                continue
            rid = raw[0]
            d = out.setdefault(rid, {'lines': [], 'v': '', 'tables': set()})
            d['lines'].append(ln)
            d['tables'].add(kind)
            if iv is not None and iv < len(cells) and not d['v']:
                v = cells[iv].replace('*', '').replace('`', '').strip()
                if v:
                    d['v'] = v
    if not out:
        raise Refused('SPEC.md yields no TC-* row -- the id column moved, or '
                      '§ 14 is gone.  An empty population and a population of '
                      'absences are different answers')
    return out


def _spec_check(root):
    import importlib.machinery
    import importlib.util
    p = os.path.join(root, 'tools', 'spec-check.py')
    if not os.path.exists(p):
        raise Refused('spec-check.py not found -- cannot parse SPEC.md')
    loader = importlib.machinery.SourceFileLoader('speccheck_tc', p)
    spec = importlib.util.spec_from_loader('speccheck_tc', loader)
    sc = importlib.util.module_from_spec(spec)
    try:
        loader.exec_module(sc)
    except Exception as e:
        raise Refused('spec-check.py would not import: %r  (it needs Python '
                      '3.12 -- an f-string there holds a backslash)' % (e,))
    return sc


RSDK_SET = re.compile(r'^CONFIG_RSDK_(\S+)=y\s*$')
RSDK_UNSET = re.compile(r'^#\s*CONFIG_RSDK_(\S+) is not set\s*$')


def sdk_releases(path=None):
    """The rsdk releases `config/rlxfw-sdk.config` names, selected or not.

    Both forms are population.  A release that is present and NOT selected is
    still a release this project holds, and a census that counted only the
    selected one would report a population of one.
    """
    path = path or SDK
    if not os.path.exists(path):
        raise Refused('config/rlxfw-sdk.config not found at %s' % path)
    out = {}
    with io.open(path, encoding='utf-8') as f:
        for ln in f:
            m = RSDK_SET.match(ln)
            if m:
                out[m.group(1)] = 'selected'
                continue
            m = RSDK_UNSET.match(ln)
            if m:
                out.setdefault(m.group(1), 'present, not selected')
    if not out:
        raise Refused('config/rlxfw-sdk.config names no CONFIG_RSDK_* release '
                      '-- its form moved')
    return out


def population(root=None, sdk_path=None):
    """(r2c, r2t) -- each a dict name -> sorted list of provenance tags."""
    tc = spec_tc(root)
    r2c = dict((k, ['SPEC.md:%s' % ','.join(str(x) for x in v['lines'])])
               for k, v in tc.items())
    r2t = dict((k, ['config/rlxfw-sdk.config:%s' % v])
               for k, v in sdk_releases(sdk_path).items())
    return r2c, r2t


# --------------------------------------------------------------------------
# axis B -- the adjudication table
# --------------------------------------------------------------------------

def read_tsv(path=None):
    """Shared with the ISA axis: `isacensus.read_tsv`, our columns."""
    return isacensus.read_tsv(path or TSV, cols=COLS)


def route_of(row):
    if row['r1'] == 'y':
        return 1
    if row['r2'] == 'y':
        return 2
    if row['r3'] == 'y':
        return 3
    return 4


def cites(row):
    return [c.strip() for c in row['cite'].split(';') if c.strip() and c.strip() != '-']


# --------------------------------------------------------------------------
# rendering
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


HEAD = {
    'r2c': ('| row | subject | ① | ② | ③ | ⓟ | V | owner / cross-ref | '
            'what is held, and what is not |',
            '|---|:-:|:-:|:-:|:-:|:-:|:-:|---|---|'),
    'r2t': ('| release | subject | ① | ② | ③ | ⓟ | on hand | `SPEC.md` | '
            'what is held, and what is not |',
            '|---|:-:|:-:|:-:|:-:|:-:|---|---|---|'),
}


def render(rows, kind, marks=None):
    marks = marks or {}
    sel = [r for r in rows if r['kind'] == kind]
    sel.sort(key=lambda r: (route_of(r), r['name']))
    out = list(HEAD[kind])
    for r in sel:
        if kind == 'r2c':
            seventh = marks.get(r['name'], {}).get('v', '') or '—'
        else:
            seventh = 'y' if r['src'] == 'derived' else '.'
        out.append('| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |'
                   % (r['name'], r['subj'], r['r1'], r['r2'], r['r3'],
                      r['p'], seventh, fmt_spec(r['spec']), r['note']))
    return '\n'.join(out)


def render_counts(rows):
    out = ['| | ① toolchain in hand | ② artefact | ③ vendor material | '
           '④ nothing | ⓟ public | total |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for kind, label in (('r2c', '`R2c` recorded findings'),
                        ('r2t', 'toolchain releases')):
        sel = [r for r in rows if r['kind'] == kind]
        c = [len([r for r in sel if route_of(r) == k]) for k in (1, 2, 3, 4)]
        pub = len([r for r in sel if r['p'] == 'y'])
        out.append('| %s | %d | %d | %d | %d | %d | **%d** |'
                   % (label, c[0], c[1], c[2], c[3], pub, len(sel)))
    out.append('')
    out.append('| subject | `R2c` rows | toolchain rows |')
    out.append('|---|---:|---:|')
    for s in SUBJ:
        out.append('| %s | %d | %d |'
                   % (s,
                      len([r for r in rows if r['kind'] == 'r2c' and r['subj'] == s]),
                      len([r for r in rows if r['kind'] == 'r2t' and r['subj'] == s])))
    return '\n'.join(out)


def render_marks(rows, marks):
    """V mark against adjudicated route -- the cross-check that says this
    census is not simply restating SPEC.md's own marks back at it."""
    order = ['量', '讀', '文', '推', '—', '(none)']
    tally = {}
    for r in rows:
        if r['kind'] != 'r2c':
            continue
        v = marks.get(r['name'], {}).get('v', '') or '(none)'
        tally.setdefault(v, [0, 0, 0, 0, 0])
        tally[v][route_of(r) - 1] += 1
        if r['mx'] == 'y':
            tally[v][4] += 1
    out = ['| `SPEC.md` V mark | ① | ② | ③ | ④ | declared disagreements |',
           '|---|---:|---:|---:|---:|---:|']
    for v in order:
        if v in tally:
            c = tally[v]
            out.append('| %s | %d | %d | %d | %d | %d |'
                       % (v, c[0], c[1], c[2], c[3], c[4]))
    for v in sorted(tally):
        if v not in order:
            c = tally[v]
            out.append('| %s | %d | %d | %d | %d | %d |'
                       % (v, c[0], c[1], c[2], c[3], c[4]))
    return '\n'.join(out)


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

def check(tsv_path=None, doc_path=None, root=None, sdk_path=None):
    f = []
    root = root or ROOT
    r2c, r2t = population(root, sdk_path)
    marks = spec_tc(root)
    rows = read_tsv(tsv_path)
    ids = isacensus.spec_ids(root)

    derived = {'r2c': set(r2c), 'r2t': set(r2t)}
    by_kind = {}
    for r in rows:
        if r['kind'] not in KINDS:
            f.append('L0 line %d: kind %r is not one of %r'
                     % (r['_line'], r['kind'], list(KINDS)))
            continue
        if r['src'] not in SRCS:
            f.append('L0 line %d: src %r is not one of %r'
                     % (r['_line'], r['src'], list(SRCS)))
            continue
        for c in ('r1', 'r2', 'r3', 'p', 'mx'):
            if r[c] not in FLAGS:
                f.append('L0 line %d: %s is %r, not y or .'
                         % (r['_line'], c, r[c]))
        by_kind.setdefault(r['kind'], []).append(r)

    for kind in KINDS:
        sel = by_kind.get(kind, [])
        named = [r['name'] for r in sel]
        if len(named) != len(set(named)):
            dups = sorted(set(n for n in named if named.count(n) > 1))
            f.append('L8 %s: %d rows but %d distinct names -- %s'
                     % (kind, len(named), len(set(named)), ', '.join(dups)))
        d = set(r['name'] for r in sel if r['src'] == 'derived')
        dec = set(r['name'] for r in sel if r['src'] == 'declared')
        for missing in sorted(derived[kind] - d):
            f.append('L1 %s: the instrument derives %r and the table has no '
                     'derived row for it' % (kind, missing))
        for stale in sorted(d - derived[kind]):
            f.append('L2 %s: the table has a derived row %r that no '
                     'instrument derives' % (kind, stale))
        for both in sorted(dec & derived[kind]):
            f.append('L4 %s: %r is declared AND derived -- it would be '
                     'counted twice' % (kind, both))
        # U14's rule, enforced as a finding rather than only as a control:
        # a population derived from this repository's own record cannot see
        # what the record omits.  Zero declared rows means nobody looked.
        if sel and not dec:
            f.append('L13 %s: not one declared row.  The population for this '
                     'kind is derived from this repository\'s own record, so '
                     'a table with nothing declared has not looked outside it'
                     % kind)

    for r in rows:
        cs = cites(r)
        paths = [c for c in cs if not c.startswith('pub=')]
        pubs = [c for c in cs if c.startswith('pub=')]
        if r['src'] == 'declared':
            if not paths:
                f.append('L3 line %d: declared row %r has no path:token cite'
                         % (r['_line'], r['name']))
        elif paths:
            # A derived row's provenance IS the instrument; a path cite on one
            # would make the population look hand-sourced.  `pub=` is the
            # exception and it is the only one, because ⓟ is about material
            # OUTSIDE this repository and no instrument here derives it.
            f.append('L3 line %d: derived row %r carries a path cite; only a '
                     'declared row may, and a derived row may carry only pub='
                     % (r['_line'], r['name']))
        for c in paths:
            if ':' not in c:
                f.append('L3 line %d: cite %r is not path:token' % (r['_line'], c))
                continue
            rel, tok = c.split(':', 1)
            p = os.path.join(root, rel)
            if not os.path.exists(p):
                f.append('L3 line %d: cite path %s does not exist'
                         % (r['_line'], rel))
            elif tok not in io.open(p, encoding='utf-8').read():
                f.append('L3 line %d: %s does not contain the cited token %r'
                         % (r['_line'], rel, tok))
        # L11 -- ⓟ is the column that answers the gate's own publishability
        # claim, so it may not be asserted without somewhere a reader can go.
        if r['p'] == 'y' and not pubs:
            f.append('L11 line %d: %r claims public prior art and carries no '
                     'pub= cite' % (r['_line'], r['name']))
        if r['p'] == '.' and pubs:
            f.append('L11 line %d: %r carries a pub= cite and does not claim '
                     'ⓟ' % (r['_line'], r['name']))

        if r['subj'] not in SUBJ:
            f.append('L10 line %d: subj %r is not one of %r -- the step table '
                     'asks every row whether it is about a toolchain or about '
                     'the die' % (r['_line'], r['subj'], list(SUBJ)))

        for sid in [s.strip() for s in r['spec'].split(',') if s.strip()]:
            if sid == '-':
                continue
            if sid not in ids and sid not in marks:
                f.append('L5 line %d: %r cites SPEC id %s, which SPEC.md does '
                         'not define' % (r['_line'], r['name'], sid))

        if r['r1'] == 'y':
            if r['seat'] == '-':
                pass          # route (1) here is DESK work; a seating is not
                              # required, and L6 would be wrong to demand one
            elif r['seat'] == 'upstream':
                if not os.path.exists(os.path.join(root, 'upstream',
                                                   'BENCH-LOG.md')):
                    f.append('L6 line %d: %r names the upstream seating and '
                             'upstream/BENCH-LOG.md is not there'
                             % (r['_line'], r['name']))
            elif not os.path.isdir(os.path.join(root, 'bench', r['seat'])):
                f.append('L6 line %d: %r names seating %s, and bench/%s is '
                         'not a directory'
                         % (r['_line'], r['name'], r['seat'], r['seat']))
        elif r['seat'] != '-':
            f.append('L7 line %d: %r is not route (1) and yet names seating %s'
                     % (r['_line'], r['name'], r['seat']))

        # L12 -- the cross-check against SPEC.md's own V mark.
        # Only a DERIVED r2c row has a SPEC.md mark to disagree with.  A
        # declared row is one SPEC.md has no row for at all, so capping it
        # at route (4) would make every declared row a finding and the
        # check would be measuring its own blind spot.
        if r['kind'] == 'r2c' and r['src'] == 'derived':
            v = marks.get(r['name'], {}).get('v', '')
            cap = MARK_MAX.get(v, 4)
            rt = route_of(r)
            if rt < cap and r['mx'] != 'y':
                f.append('L12 line %d: %r is adjudicated route (%d) and '
                         'SPEC.md marks its value %s, which reaches only (%d).'
                         '  Declare it with mx=y or fix one of the two files'
                         % (r['_line'], r['name'], rt, v or '(none)', cap))
            if rt >= cap and r['mx'] == 'y':
                f.append('L12 line %d: %r declares a mark disagreement (mx=y) '
                         'and route (%d) is within what %s supports (%d) -- '
                         'an exception nothing needs' % (r['_line'], r['name'],
                                                         rt, v or '(none)', cap))

    dp = doc_path or DOC
    if not os.path.exists(dp):
        f.append('L9 %s does not exist, so its blocks cannot be checked'
                 % os.path.relpath(dp, root))
    else:
        text = io.open(dp, encoding='utf-8').read()
        for tag, want in (('r2c', render(rows, 'r2c', marks)),
                          ('r2t', render(rows, 'r2t', marks)),
                          ('counts', render_counts(rows)),
                          ('marks', render_marks(rows, marks))):
            got = doc_block(text, tag, BEGIN, END)
            if got is None:
                f.append('L9 %s has no tccensus:%s block'
                         % (os.path.basename(dp), tag))
            elif got != want:
                f.append('L9 the tccensus:%s block in %s is not what this tool '
                         'derives' % (tag, os.path.basename(dp)))
    return f


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def report_population():
    r2c, r2t = population()
    marks = spec_tc()
    print('axis A -- the R2c population, from SPEC.md through spec-check')
    print('  %d recorded toolchain findings' % len(r2c))
    only_blank = sorted(k for k in r2c if marks[k]['tables'] == {'blanks'})
    for name in sorted(r2c):
        print('    %-8s V=%-3s %-10s %s'
              % (name, marks[name]['v'] or '-',
                 '+'.join(sorted(marks[name]['tables'])), r2c[name][0]))
    print('  rows the findings table does not carry at all: %s'
          % (' '.join(only_blank) or '(none)'))
    print()
    print('axis A -- the toolchain population, from config/rlxfw-sdk.config')
    print('  %d releases on hand' % len(r2t))
    for name in sorted(r2t):
        print('    %-46s %s' % (name, r2t[name][0]))
    print()
    print('  🔴 ONE instrument per kind, and the R2c one is this repository\'s')
    print('     own record.  A fact measured and never written down is')
    print('     invisible to it.  L13 requires the table to hold at least one')
    print('     declared row per kind for exactly that reason.')
    return 0


def report_census():
    rows = read_tsv()
    marks = spec_tc()
    print(render_counts(rows))
    print()
    print(render_marks(rows, marks))
    print()
    print(render(rows, 'r2c', marks))
    print()
    print(render(rows, 'r2t', marks))
    return 0


def report_check():
    f = check()
    for x in f:
        print('  ' + x)
    print('RESULT: %s' % ('ok, %d row(s) checked both ways' % len(read_tsv())
                          if not f else '%d finding(s)' % len(f)))
    return 1 if f else 0


def write_blocks(doc_path=None, tsv_path=None, root=None):
    dp = doc_path or DOC
    rows = read_tsv(tsv_path)
    marks = spec_tc(root)
    text = io.open(dp, encoding='utf-8').read()
    out, changed = text, []
    for tag, want in (('r2c', render(rows, 'r2c', marks)),
                      ('r2t', render(rows, 'r2t', marks)),
                      ('counts', render_counts(rows)),
                      ('marks', render_marks(rows, marks))):
        b, e = BEGIN % tag, END % tag
        if b not in out or e not in out:
            raise Refused('%s has no tccensus:%s block'
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
    tp = os.path.join(tmp, 'toolchain-census.tsv')
    dp = os.path.join(tmp, 'toolchain-prior-art.md')
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

    print('tccensus self-test')

    tmp = tempfile.mkdtemp()
    try:
        tp, dp = _fixture(tmp)
        base = check(tsv_path=tp, doc_path=dp)
        case('U0', 'the committed table and document are clean', base, [])
        if base:
            for x in base:
                print('       ' + x)
            print('RESULT: REFUSING -- the unmutated pair is already red, so '
                  'no control below means anything')
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def cellset(lines, j, idx, val):
        c = lines[j].split('\t')
        c[idx] = val
        return lines[:j] + ['\t'.join(c)] + lines[j + 1:]

    def find(lines, pred):
        for j, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) == len(COLS) and c[0] in KINDS and pred(c):
                return j, c
        raise AssertionError('fixture has no row matching the predicate')

    def drop_derived(lines, doc):
        j, _ = find(lines, lambda c: c[2] == 'derived')
        return lines[:j] + lines[j + 1:], doc

    def add_bogus(lines, doc):
        return lines + ['\t'.join(['r2c', 'TC-99', 'derived', 'tc', '.', '.',
                                   '.', '.', '.', '-', '-', '-', 'x'])], doc

    def declared_as_derived(lines, doc):
        j, c = find(lines, lambda c: c[2] == 'declared')
        real = sorted(population()[0])[0]
        return cellset(lines, j, 1, real), doc

    def break_cite(lines, doc):
        # 🔴 The cite must not point at THIS file.  The first version pointed
        # at `tools/tccensus.py` with the token "a token that is not in that
        # file" -- which is in this file, because the mutation writes it here.
        # The needle was in the haystack and `U4` passed the check it was
        # written to break.  Point it at SPEC.md instead, whose contents this
        # source cannot contaminate.
        j, c = find(lines, lambda c: c[2] == 'declared')
        return cellset(lines, j, 11, 'SPEC.md:' + 'ZZ-absent-' + 'token-ZZ'), doc

    def bad_spec(lines, doc):
        j, c = find(lines, lambda c: c[9] != '-')
        return cellset(lines, j, 9, 'ZZZ-99'), doc

    def bad_seat(lines, doc):
        j, c = find(lines, lambda c: c[4] == 'y')
        return cellset(lines, j, 10, '1999-01-01'), doc

    def seat_without_route1(lines, doc):
        j, c = find(lines, lambda c: c[4] == '.')
        return cellset(lines, j, 10, '2026-08-30'), doc

    def duplicate_name(lines, doc):
        i = _first_data_line(lines)
        return lines + [lines[i]], doc

    def bad_subj(lines, doc):
        j, c = find(lines, lambda c: True)
        return cellset(lines, j, 3, 'silicon'), doc

    def pub_without_cite(lines, doc):
        j, c = find(lines, lambda c: c[7] == 'y')
        keep = ';'.join(x for x in cites(dict(zip(COLS, c)))
                        if not x.startswith('pub='))
        return cellset(lines, j, 11, keep or '-'), doc

    def mark_violation(lines, doc):
        # Take a row SPEC.md marks 讀 (reaches only route 3) and claim
        # route (1) on it without declaring the disagreement.
        marks = spec_tc()
        j, c = find(lines, lambda c: c[0] == 'r2c' and c[8] == '.'
                    and marks.get(c[1], {}).get('v') == '讀' and c[4] == '.')
        lines = cellset(lines, j, 4, 'y')
        return lines, doc

    def strip_declared(lines, doc):
        out = []
        for ln in lines:
            c = ln.split('\t')
            if len(c) == len(COLS) and c[0] == 'r2t' and c[2] == 'declared':
                continue
            out.append(ln)
        return out, doc

    def scuff_doc(lines, doc):
        return lines, doc.replace('| `TC-13` |', '| `TC-13x` |', 1)

    fired('U1', 'L1', drop_derived,
          'a derived row missing from the table is caught')
    fired('U2', 'L2', add_bogus,
          'a table row no instrument derives is caught')
    fired('U3', 'L4', declared_as_derived,
          'a declared row that is also derived is caught')
    fired('U4', 'L3', break_cite,
          'a declared row whose cited token is absent is caught')
    fired('U5', 'L5', bad_spec,
          'a SPEC id SPEC.md does not define is caught')
    fired('U6', 'L6', bad_seat,
          'a seating that does not exist is caught')
    fired('U7', 'L7', seat_without_route1,
          'a seating named without a route-(1) reading is caught')
    fired('U8', 'L8', duplicate_name,
          'a duplicated name is caught by the two-unit count')
    fired('U9', 'L9', scuff_doc,
          'one character changed in the document block is caught')
    fired('U10', 'L10', bad_subj,
          'a row that does not say toolchain-or-die is caught')
    fired('U11', 'L11', pub_without_cite,
          'a public-prior-art claim with nowhere to go is caught')
    fired('U12', 'L12', mark_violation,
          'a route SPEC.md\'s own V mark does not support is caught')
    fired('U13', 'L13', strip_declared,
          'a kind with every row derived from the record is caught')

    def refuses(cid, what, fn):
        try:
            fn()
        except Refused:
            case(cid, what, True, True)
            return
        case(cid, what, False, True)

    refuses('U14', 'no config/rlxfw-sdk.config -> REFUSED, not an empty '
                   'toolchain population',
            lambda: sdk_releases(os.path.join(HERE, 'no-such-sdk.config')))

    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, 'rlxfw-sdk.config')
        io.open(p, 'w', encoding='utf-8').write(
            '# nothing here names a release\nCONFIG_SOMETHING=y\n')
        refuses('U15', 'an sdk config naming no release -> REFUSED, not a '
                       'population of zero', lambda: sdk_releases(p))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp = tempfile.mkdtemp()
    try:
        io.open(os.path.join(tmp, 'SPEC.md'), 'w', encoding='utf-8').write(
            '# no tables here\n')
        os.makedirs(os.path.join(tmp, 'tools'))
        import shutil as _sh
        _sh.copy(os.path.join(HERE, 'spec-check.py'),
                 os.path.join(tmp, 'tools', 'spec-check.py'))
        refuses('U16', 'a SPEC.md with no TC-* row -> REFUSED',
                lambda: spec_tc(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # U17 -- the population is derived, so it must MOVE when the instrument
    # moves.  A count that is the same whatever SPEC.md says is a constant.
    tmp = tempfile.mkdtemp()
    try:
        src = io.open(os.path.join(ROOT, 'SPEC.md'), encoding='utf-8').read()
        io.open(os.path.join(tmp, 'SPEC.md'), 'w', encoding='utf-8',
                newline='\n').write(src.replace('| `TC-47` ', '| `TC-97` ', 1))
        os.makedirs(os.path.join(tmp, 'tools'))
        import shutil as _sh
        _sh.copy(os.path.join(HERE, 'spec-check.py'),
                 os.path.join(tmp, 'tools', 'spec-check.py'))
        before = set(spec_tc())
        after = set(spec_tc(tmp))
        case('U17', 'renaming one id in SPEC.md moves the derived population',
             (len(before), len(after), 'TC-97' in after, 'TC-47' in after),
             lambda g: g[0] == g[1] and g[2] and not g[3])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # U18/U19 -- `write` repairs and touches nothing else.
    tmp = tempfile.mkdtemp()
    try:
        tp, dp = _fixture(tmp)
        scuffed = io.open(dp, encoding='utf-8').read().replace(
            '| `TC-13` |', '| `TC-13x` |', 1)
        io.open(dp, 'w', encoding='utf-8', newline='\n').write(scuffed)
        changed = write_blocks(doc_path=dp, tsv_path=tp)
        case('U18', 'write repairs a scuffed block and check then passes',
             ('r2c' in changed, check(tsv_path=tp, doc_path=dp)),
             lambda g: g[0] and g[1] == [])

        def outside(s):
            for tag in ('r2c', 'r2t', 'counts', 'marks'):
                b, e = BEGIN % tag, END % tag
                head, rest = s.split(b, 1)
                _, tail = rest.split(e, 1)
                s = head + b + e + tail
            return s
        case('U19', 'write touches nothing outside the markers',
             outside(io.open(dp, encoding='utf-8').read()),
             outside(io.open(DOC, encoding='utf-8').read()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # U20 -- the sibling tool this one imports must still be 18/18 and its
    # own table must still read.  The one change made to it was a `cols`
    # parameter; this is the control that says the default did not move.
    isa_rows = isacensus.read_tsv()
    case('U20', 'isacensus.read_tsv() with no cols still reads its own table',
         (len(isa_rows) > 0, tuple(k for k in isa_rows[0] if k != '_line')),
         lambda g: g[0] and g[1] == isacensus.COLS)

    print('RESULT: %d/%d' % (ok, ok + fail))
    return 1 if fail else 0


def main(argv):
    ap = argparse.ArgumentParser(prog='tccensus.py')
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
        sys.stderr.write('tccensus.py: REFUSED -- %s\n' % e)
        sys.stderr.write('  Nothing is reported: an empty census and a census '
                         'of absences are different answers.\n')
        return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
