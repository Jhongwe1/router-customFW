#!/usr/bin/env python3
"""Check SPEC.md against the properties it claims about itself.

SPEC.md is a second copy of every number in this repository.  Its header says it
is an index and not an owner, that a blank row names the experiment that fills
it, and that per-unit identifiers are not in it.  Those are three claims, and
until this ran they were three promises.

What it checks, and every one of them can fail:

  C1  every row in a definition table has a well-formed id, and ids are unique
  C2  the V and N columns carry a legal mark.  Tables with no V/N header are
      exempt by construction -- the count of exempt tables is printed, because
      a check that silently skips is the failure this repo keeps catching
  C3  two invariants tying the blanks together:
        I1  a value marked 留白/未定  <=>  the id is listed in section 17
        I2  V == '—'                  =>  the value is marked 留白/未定
      I2 is what stops a row that was never established from reading as one
      that was.  It is also the check that found four rows carrying a real
      value from the datasheet under a provenance mark meaning "nothing"
  C4  every file named in the 擁有者 column exists.  `plan/` is gitignored and
      warns rather than fails, because a fresh clone does not have it
  C5  at least one literal from the row (hex word, 0x form, or a number with
      thousands separators) still appears in one of the row's owner files.
      This is the anti-drift check and it is the weakest one: it cannot tell
      whether a value is CORRECT, only whether it still occurs where it was
      derived.  Rows with no extractable literal are skipped and counted
  C6  redaction: the patterns in audit-bench-log.py are re-run over SPEC.md and
      every hit must be on the allowlist below, with a reason.  The allowlist
      is printed on every run

What it cannot do, stated so a clean result is not read as more than it is:

  * It cannot check a value against the device.  Only the bench does that.
  * C5 matches literals, not meaning.  A row whose prose is rewritten around an
    unchanged number passes, and a row whose number is right in a file that is
    itself wrong passes too.
  * `plan/` is not in a clone, so owners there are unverifiable off this machine.
  * Nothing here checks that a row's source count matches its marks.  That is
    the two-source rule, it is enforced by hand, and it is not automated here.

Usage:
    python3 tools/spec-check.py [SPEC.md]
    python3 tools/spec-check.py --self-test        # the controls
"""
import io
import os
import re
import subprocess
import sys
import tempfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The id, plus whatever decoration the house style puts after it -- RUNSHEET.md
# writes `| **C5** 🆕 |`, and SPEC.md does the same.
ID_RX = re.compile(r'^\*{0,2}`?([A-Z]{2,3}-\d{2}[a-z]?)`?\*{0,2}(?:\s.*)?$')
MARKS = ('量', '讀', '推', '文', '—')

# A value cell may legitimately hold no value.  Three of these are open
# questions and must appear in section 17; the other two are not questions at
# all, so they must not.
BLANK_RX = re.compile(r'留白|未定|未讀')          # open -- section 17 owes an experiment
NOTAVALUE_RX = re.compile(r'§18|選定')            # withheld, or chosen rather than measured

# Backticked tokens that look like a path into this repository.
PATH_RX = re.compile(r'`([^`]*?(?:/[^`]*)?\.(?:md|json|py|sh))`')

# Literals worth chasing into an owner file.
LIT_RXS = (
    re.compile(r'0x[0-9A-Fa-f]{3,}'),
    re.compile(r'\b[0-9A-F]{8}\b'),
    re.compile(r'\b\d{1,3}(?:,\d{3})+\b'),
    re.compile(r'\b\d{4,}\b'),
)

# C6.  Every hit audit-bench-log.py finds in SPEC.md must be here, with the
# reason it is a statement about the MODEL and not about this unit.  A hit that
# is not on this list fails the run.
REDACTION_ALLOWLIST = {
    ('H601 / calibration', 'H601'):
        'the name of a flash region, from the vendor SDK. Its CONTENTS are what is withheld',
    ('private IPv4', '192.168.1.6'):
        "the loader's compiled-in TFTP address, read out of stage2.bin. Not this unit's configuration",
    ('SSID / passphrase', 'SSID'):
        'the word, in a row about the default naming scheme. No SSID value is recorded',
    ('SSID / passphrase', 'ssid'):
        'as above, lower case',
}


def split_cells(line):
    """Split a markdown table row, respecting \\| inside a cell."""
    parts = re.split(r'(?<!\\)\|', line.strip())
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return [p.strip() for p in parts]


def clean_header(cell):
    return cell.replace('*', '').replace('`', '').strip()


def parse(path):
    """Return (tables, lines).  A table is a dict with section, header, rows."""
    lines = io.open(path, encoding='utf-8').read().split('\n')
    tables, section, i = [], None, 0
    while i < len(lines):
        m = re.match(r'^## (\d+)\.', lines[i])
        if m:
            section = int(m.group(1))
        if (lines[i].startswith('|') and i + 1 < len(lines)
                and re.match(r'^\|[\s:|-]+\|\s*$', lines[i + 1])):
            header = [clean_header(c) for c in split_cells(lines[i])]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith('|'):
                rows.append((j + 1, split_cells(lines[j])))
                j += 1
            tables.append({'section': section, 'header': header,
                           'rows': rows, 'line': i + 1})
            i = j
            continue
        i += 1
    return tables, lines


def col(table, *names):
    for n in names:
        if n in table['header']:
            return table['header'].index(n)
    return None


YEAR_RX = re.compile(r'^(?:19|20)\d\d$')


def literals(text):
    """Literals worth chasing.  Two classes are dropped rather than counted:

    an all-zero word, because `00000000` occurs in every hex dump ever written
    and would make the check pass on nothing; and a bare four-digit year,
    because `2018` appears in every file in this repository and a row would
    then be 'confirmed' by its own date.
    """
    out = []
    for rx in LIT_RXS:
        for lit in rx.findall(text):
            core = lit.lower().replace('0x', '').replace(',', '').replace('_', '')
            if core.strip('0') == '':
                continue
            if YEAR_RX.match(lit):
                continue
            out.append(lit)
    return out


_BLOBS = {}


def owner_blob(full):
    """Owner files are read once per process.  The controls re-check the same
    ~40 owners eight times over, on a DrvFs mount where every open is a round
    trip; without this the controls cost more than the check they protect."""
    if full not in _BLOBS:
        try:
            _BLOBS[full] = normalise(io.open(full, encoding='utf-8', errors='replace').read().lower())
        except OSError:
            _BLOBS[full] = None
    return _BLOBS[full]


def matches(needle, blob):
    """Does this literal still occur in the owner file?

    Three spellings count as the same number, and one deliberately does not.
    A 32-bit address is written whole here (`0xB8003104`) and as base plus
    offset in the sources that document it (`base 0xB800_3100 -- TC1DATA 3104`),
    so the split form counts when BOTH halves are present.  It does not count
    when the low half is all zeros: `0000` occurs in every file and would make
    the check pass on nothing.
    """
    if needle in blob or needle.replace('0x', '') in blob or needle.replace(',', '') in blob:
        return True
    m = re.fullmatch(r'0x([0-9a-f]{4})([0-9a-f]{4})', needle)
    if m and m.group(2).strip('0') != '':
        return m.group(1) in blob and m.group(2) in blob
    return False


def normalise(blob):
    """Fold the two spellings of a register address into one.

    The datasheet and SOURCES.json write `0xB800_3000`; the disassembly and this
    table write `0xB8003000`.  Without this, C5 reports a drift that is a
    typographic convention.
    """
    return re.sub(r'(?<=[0-9A-Fa-f])_(?=[0-9A-Fa-f])', '', blob)


def owner_paths(cell):
    return PATH_RX.findall(cell)


def load_audit_patterns():
    spec = importlib.util.spec_from_file_location(
        'audit_bench_log', os.path.join(HERE, 'audit-bench-log.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(path, quiet=False):
    """Run every check.  Returns (findings, stats).  A finding is (check, msg)."""
    findings, stats = [], {}
    tables, lines = parse(path)
    text = '\n'.join(lines)

    defs = [t for t in tables if t['section'] and 1 <= t['section'] <= 16]
    idx17 = [t for t in tables if t['section'] == 17]

    # ---- C1: ids well formed and unique -------------------------------------
    seen, rows = {}, []
    for t in defs:
        for lineno, cells in t['rows']:
            if not cells:
                continue
            m = ID_RX.match(cells[0])
            if not m:
                findings.append(('C1', f'{path}:{lineno}: first cell is not an id: {cells[0][:40]!r}'))
                continue
            rid = m.group(1)
            if rid in seen:
                findings.append(('C1', f'{path}:{lineno}: id {rid} already defined at line {seen[rid]}'))
            else:
                seen[rid] = lineno
            rows.append({'id': rid, 'line': lineno, 'cells': cells, 'table': t})
    stats['rows'] = len(rows)
    stats['tables'] = len(defs)

    # ---- C2: marks ----------------------------------------------------------
    exempt = 0
    for t in defs:
        vi, ni = col(t, 'V'), col(t, 'N')
        if vi is None or ni is None:
            exempt += 1
            continue
    for r in rows:
        vi, ni = col(r['table'], 'V'), col(r['table'], 'N')
        if vi is None or ni is None:
            continue
        for which, k in (('V', vi), ('N', ni)):
            cell = r['cells'][k] if k < len(r['cells']) else ''
            if not cell:
                findings.append(('C2', f"{path}:{r['line']}: {r['id']} has an empty {which} mark"))
            elif not any(mk in cell for mk in MARKS):
                findings.append(('C2', f"{path}:{r['line']}: {r['id']} {which} mark is not one of {'/'.join(MARKS)}: {cell[:30]!r}"))
    stats['exempt_tables'] = exempt

    # ---- C3: blanks <-> section 17 -----------------------------------------
    listed = set()
    for t in idx17:
        for lineno, cells in t['rows']:
            if cells:
                m = ID_RX.match(cells[0])
                if m:
                    listed.add(m.group(1))
    marked_blank = set()
    for r in rows:
        vi = col(r['table'], 'V')
        val_i = col(r['table'], '值', '讀數', '內容', '是什麼')
        val = r['cells'][val_i] if val_i is not None and val_i < len(r['cells']) else ''
        vcell = r['cells'][vi] if vi is not None and vi < len(r['cells']) else ''
        is_blank = bool(BLANK_RX.search(val))
        not_a_value = bool(NOTAVALUE_RX.search(val))
        if is_blank:
            marked_blank.add(r['id'])
        if vi is not None and vcell.strip() == '—' and not (is_blank or not_a_value):
            findings.append(('C3', f"{path}:{r['line']}: {r['id']} has V = '—' but its value is not marked "
                                   f"留白/未定/未讀 (open) or §18/選定 (not a value) -- "
                                   f"a value with no provenance reads as established"))
    for rid in sorted(marked_blank - listed):
        findings.append(('C3', f'{rid} is marked open but section 17 does not say what fills it'))
    # The reverse is NOT a finding.  Section 17 also carries rows whose value is
    # established while a residual stays open -- RF-01 has a part number and one
    # source, CPU-17 has a count and an unsettled cause.  Counted, not failed,
    # because forbidding it would push those residuals out of the index.
    residual = sorted(listed - marked_blank)
    stats['blanks'] = len(marked_blank)
    stats['residual'] = residual

    # ---- C4 / C5: owners exist, and still carry the value -------------------
    no_literal, no_owner, plan_owned, checked = [], [], 0, 0
    prev_owners = []
    for r in rows:
        oi = col(r['table'], '擁有者')
        si = col(r['table'], '來源')
        owner_cell = r['cells'][oi] if oi is not None and oi < len(r['cells']) else ''
        paths = owner_paths(owner_cell)
        if not paths and '同上' in owner_cell:
            paths = prev_owners
        elif paths:
            prev_owners = paths

        real = []
        for p in paths:
            full = os.path.join(ROOT, p)
            if os.path.exists(full):
                real.append(full)
            elif p.startswith('plan/'):
                plan_owned += 1
            else:
                findings.append(('C4', f"{path}:{r['line']}: {r['id']} names an owner that does not exist: {p}"))

        body = ' '.join(c for k, c in enumerate(r['cells']) if k not in (oi, si))
        lits = literals(body)
        if not real:
            no_owner.append(r['id'])
            continue
        if not lits:
            no_literal.append(r['id'])
            continue
        checked += 1
        found = False
        for full in real:
            blob = owner_blob(full)
            if blob is None:
                continue
            for lit in lits:
                if matches(normalise(lit.lower()), blob):
                    found = True
                    break
            if found:
                break
        if not found:
            findings.append(('C5', f"{path}:{r['line']}: {r['id']} -- none of {lits[:4]} appears in "
                                   f"{', '.join(os.path.relpath(f, ROOT) for f in real)}"))
    stats.update(no_literal=len(no_literal), no_owner=len(no_owner),
                 plan_owned=plan_owned, value_checked=checked,
                 no_literal_ids=no_literal, no_owner_ids=no_owner)

    # ---- C7: an established row names at least one source -------------------
    # This does NOT check the two-source rule.  It checks the weaker property
    # that a row carrying a value says where the value came from -- an empty
    # source column under a real value is the shape "two sources, always"
    # degrades into when nobody is looking.
    for r in rows:
        si = col(r['table'], '來源')
        val_i = col(r['table'], '值', '讀數', '內容', '是什麼')
        if si is None or val_i is None:
            continue
        val = r['cells'][val_i] if val_i < len(r['cells']) else ''
        src = r['cells'][si] if si < len(r['cells']) else ''
        if BLANK_RX.search(val) or NOTAVALUE_RX.search(val):
            continue
        if not src or src.strip() in ('—', '-'):
            findings.append(('C7', f"{path}:{r['line']}: {r['id']} carries a value and names no source"))

    # ---- C6: redaction ------------------------------------------------------
    audit = load_audit_patterns()
    fired = {lbl for lbl, rx in audit.PATTERNS if rx.search(audit.CONTROL)}
    missing = [lbl for lbl, _ in audit.PATTERNS if lbl not in fired]
    if missing:
        findings.append(('C6', f'the redaction patterns do not all fire on their own control: {missing}'))
    hits = []
    for lbl, rx in audit.PATTERNS:
        for m in rx.finditer(text):
            hits.append((lbl, m.group(0), text.count('\n', 0, m.start()) + 1))
    for lbl, got, ln in hits:
        if (lbl, got) not in REDACTION_ALLOWLIST:
            findings.append(('C6', f'{path}:{ln}: {lbl} matched {got!r} and it is not on the allowlist'))
    stats['redaction_hits'] = len(hits)
    return findings, stats


def report(path, findings, stats):
    print(f'=== {os.path.relpath(path, ROOT)} ===')
    print(f"  {stats['rows']} rows in {stats['tables']} definition tables; "
          f"{stats['blanks']} marked open")
    if stats['residual']:
        print(f"  section 17 also carries {len(stats['residual'])} row(s) whose value stands "
              f"while a residual is open: {', '.join(stats['residual'])}")
    print(f"  C2 exempt tables (no V/N header, by construction): {stats['exempt_tables']}")
    print(f"  C5 value re-checked against an owner file: {stats['value_checked']} rows")
    print(f"     skipped, no literal to chase: {stats['no_literal']} "
          f"({', '.join(stats['no_literal_ids'][:8])}{' …' if stats['no_literal'] > 8 else ''})")
    print(f"     skipped, owner is a gate or a note rather than a file: {stats['no_owner']} "
          f"({', '.join(stats['no_owner_ids'][:8])}{' …' if stats['no_owner'] > 8 else ''})")
    print(f"     owners under plan/ (gitignored, unverifiable in a clone): {stats['plan_owned']}")
    print(f"  C6 redaction hits: {stats['redaction_hits']}, allowlist of {len(REDACTION_ALLOWLIST)}:")
    for (lbl, got), why in REDACTION_ALLOWLIST.items():
        print(f'       {got!r} ({lbl}) -- {why}')
    print()
    if not findings:
        print('  ok  every check that can fail, did not')
        return 0
    for c, msg in sorted(findings):
        print(f'  FAIL [{c}] {msg}')
    print(f'\n  {len(findings)} finding(s)')
    return 1


# ---------------------------------------------------------------------------
# Controls.  Each mutation must be caught by the check it targets -- a mutation
# caught by a DIFFERENT check is a false control, so the check id is asserted.
# ---------------------------------------------------------------------------
def _first_blank_id(s):
    """The id of the first row whose value is marked open.  Found at run time so
    the controls do not rot the next time a blank is filled."""
    for line in s.split('\n'):
        if line.startswith('| `') and BLANK_RX.search(line):
            m = ID_RX.match(split_cells(line)[0])
            if m:
                return m.group(1)
    return None


def _m1(s):                                    # two rows, one id
    ids = re.findall(r'^\| `([A-Z]{2,3}-\d{2}[a-z]?)`', s, re.M)
    return s.replace(f'| `{ids[1]}`', f'| `{ids[0]}`', 1) if len(ids) > 1 else s


def _m2(s):                                    # a mark cell with nothing in it
    return re.sub(r'\| 量 \| 量 \|', '|  |  |', s, count=1)


def _m3(s):                                    # a real value under a mark meaning "nothing"
    return re.sub(r'^(\| `CPU-01` \|[^\n]*?)\| 量 \| 量 \|', r'\1| — | — |', s, count=1, flags=re.M)


def _m4(s):
    """The blank stays; its way out disappears.

    The deletion is done strictly after the section 17 header, because removing
    the DEFINITION row instead would take the blank away with it and nothing
    would be left to catch -- which is how this control failed the first time
    it ran.
    """
    rid = _first_blank_id(s)
    if not rid:
        return s
    head, sep, tail = s.partition('## 17.')
    if not sep:
        return s
    lines = tail.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(f'| `{rid}`'):
            del lines[i]
            return head + sep + '\n'.join(lines)
    return s


MUTATIONS = [
    ('M1 duplicate an id', 'C1', 'already defined', _m1),
    ('M2 empty a mark cell', 'C2', 'empty', _m2),
    ("M3 a real value under V = '—'", 'C3', "has V = '—'", _m3),
    ('M4 drop the §17 row that a blank depends on', 'C3', 'section 17 does not say', _m4),
    ('M5 point an owner at a file that does not exist', 'C4', 'does not exist',
     lambda s: s.replace('`notes/cache-model.md` |', '`notes/cache-model-NOPE.md` |', 1)),
    ('M6 corrupt a measured hex value', 'C5', 'appears in',
     lambda s: s.replace('`0x1C7016`', '`0x1C7099`')),
    ('M7 paste in a MAC address', 'C6', 'allowlist',
     lambda s: s.replace('## 1. 身分', '## 1. 身分\n\n00:E0:4C:11:22:33\n', 1)),
    ('M8 empty the source column under a value', 'C7', 'names no source',
     lambda s: re.sub(r'^(\| `CPU-01` \|(?:[^\n|]*\|){4})[^\n|]*\|', r'\1 — |', s, count=1, flags=re.M)),
]


def controls(path, verbose=True):
    """Every check must be shown to fail before a clean run means anything.

    This is not behind a flag.  `audit-bench-log.py` runs its control on every
    invocation for the same reason, and CLAUDE.md states it as a rule: a tool
    that cannot fail proves nothing.
    """
    src = io.open(path, encoding='utf-8').read()
    # A mutation counts only if it produces a finding the file did not already
    # have.  Without this baseline, a control passes vacuously whenever the file
    # is already failing the check that control exists to test.
    baseline = {(c, m) for c, m in check(path)[0]}
    if verbose:
        print('=== POSITIVE CONTROLS: each mutation must produce a NEW finding, '
              'from the named check ===')
        if baseline:
            print(f'  ({len(baseline)} finding(s) already present; a control that only '
                  f'reproduces one of those does not count)')
    ok = fail = 0
    tmpdir = tempfile.mkdtemp(prefix='spec-check-')
    for label, want, want_msg, mutate in MUTATIONS:
        mutated = mutate(src)
        if mutated == src:
            print(f'  FAIL  {label:44s} the mutation did not change the file -- '
                  f'the anchor it edits has moved')
            fail += 1
            continue
        tmp = os.path.join(tmpdir, 'SPEC.md')
        io.open(tmp, 'w', encoding='utf-8', newline='\n').write(mutated)
        got, _ = check(tmp)
        # The message is asserted as well as the check id, because two controls
        # share C3 and each must fire on its own invariant -- otherwise one of
        # them could be dead and the other would cover for it.
        new = [(c, m) for c, m in got if (c, m) not in baseline]
        hit = [m for c, m in new if c == want and want_msg in m]
        codes = sorted({c for c, _ in new})
        if hit:
            print(f'  ok    {label:44s} caught by {want}: …{want_msg}…')
            ok += 1
        elif codes:
            print(f'  FAIL  {label:44s} caught by {codes}, but not by {want} '
                  f'reporting {want_msg!r}')
            fail += 1
        else:
            print(f'  FAIL  {label:44s} NOT CAUGHT -- {want} cannot fail')
            fail += 1
    if verbose:
        print()
        if fail:
            print(f'  {ok} controls held, \033[31m{fail} did not\033[0m')
        else:
            print(f'  ok  all {ok} controls held: every check above has been shown to fail\n')
    return fail


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    path = os.path.join(ROOT, args[0]) if args else os.path.join(ROOT, 'SPEC.md')
    if not os.path.exists(path):
        print(f'no such file: {path}')
        return 2

    failed = controls(path)
    if failed:
        print('  REFUSING to report on the file: a check that cannot fail would '
              'report it clean whatever it says')
        return 2
    if '--self-test' in argv:
        return 0

    findings, stats = check(path)
    return report(path, findings, stats)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
