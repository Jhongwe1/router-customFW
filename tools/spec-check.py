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
  C7  a row that carries a value names at least one source.  This is NOT the
      two-source rule; it is the weaker property that an established value says
      where it came from
  C11 a reference to a line of a payload source carries a TOKEN from that
      line, and the token is still within a few lines of the number.  A line
      number is the one kind of citation in this repository that goes wrong
      SILENTLY: the line still exists, so "does this line exist" passes, and
      nothing compares the line to what the citing sentence says is there.
      量 2026-08-31: editing `probe3.c` invalidated fourteen references at
      once and the owner audit, not a checker, is what found them
  C8  every row has as many cells as its own table's header.  This is the check
      that was missing on 2026-08-26, and the defect it would have caught had
      been in the file since CPU-19 was written: an unescaped `|` inside a
      backticked span (`Status.IsC|SwC`) gave that row eight cells in a
      seven-column table.  Markdown renders it wrong, and every column after
      the break shifts by one -- so C2 read the value cell as a mark, and C4/C5
      read the SOURCE cell as the owner, found no path in it, and counted the
      row as "owner is a gate rather than a file".  **The row was silently
      exempt from two checks and the summary reported it as skipped, not as
      broken.**  A check that quietly does not check is the failure this file
      exists to catch, so it now has one of its own

C8 IS NOT ABOUT SPEC.md ANY MORE.  From 2026-08-30 it runs over every tracked
`.md` outside `upstream/` -- 71 files as this is written -- because how this
repository's prose renders is not a property of one file.  The table, row and
span counts are NOT repeated here: the tool prints them on every run and they
move on every commit (614 -> 623 tables inside the session that wrote this),
which is exactly the number-that-was-true-once failure this repository keeps
catching.  量 the first time it ran that way: EIGHT ragged rows, and the census
that preceded it had said six, because it had looked at three files.  Three more
shapes came with it, and each was found by turning the previous one on:

  C8b a row split over more than one PHYSICAL line, which GFM does not have.  A
      literal newline inside a code span ends the row there and renders the rest
      as a paragraph -- and every checker in this repository walked lines
      beginning with a pipe, so the continuation was invisible AND every row
      below it in the same table was dropped from the count.  Two instances.
  C8c a `|`-line that belongs to NO table.  C8 cannot see this by construction:
      C8 walks tables, and a stranded row is in none.  量: NINE rows of
      docs/FINDINGS.md -- the page a reader is pointed at, including the three
      newest findings, about the flash bracket and `H601` -- plus one of
      bench/README.md.  This is the same defect PROGRESS.md records against
      SPEC.md on 2026-08-27, found then by an adversarial pass and now by a
      checker.
  C10 a paragraph whose backtick RUNS cannot pair, so a span is left open and
      swallows the prose after it.  C9 pairs runs across the whole FILE, which
      makes an unmatched run invisible until later text happens to supply a
      partner -- it is order dependent, and 量 2026-08-30 that is exactly what
      hid three of these.  A blank line ends a code span (CommonMark), so the
      paragraph is the local, order-independent unit.  Found: notes/kernel-build.md
      rendering a whole sentence as code while `0x2B0000` -- the number the
      sentence is about -- rendered as prose, and RUNSHEET.md's `byte 0` line
      closing with a run of two.

  C9  a code span whose whole content is whitespace.  `\r` and `\n` typed as
      real characters degrade to exactly this, and the rendering shows nothing.
      FOUR instances, and one of them made a READING wrong rather than only a
      rendering: docs/loader-command-semantics.md annotated both exits of
      readline's three-way branch with the same empty character, so the sentence
      "only one writes a terminator" named neither.  Settled by disassembling
      $FWRE_WORK/stage2.bin.  🔴 The fourth is the carried-forward row that
      DESCRIBES the defect, in PROGRESS.md, and it was found only when the
      finished checker was run over `git archive HEAD` at the end of the session
      -- the count assembled one file at a time, in the order the defects
      surfaced, said three.  Whole reading over that tree: C8 8, C8b 2, C8c 10,
      C9 4 -- 24 defects in six files.

What it cannot do, stated so a clean result is not read as more than it is:

  * It cannot check a value against the device.  Only the bench does that.
  * C5 matches literals, not meaning.  A row whose prose is rewritten around an
    unchanged number passes, and a row whose number is right in a file that is
    itself wrong passes too.
  * `plan/` is not in a clone, so owners there are unverifiable off this machine.
  * Nothing here checks that a row's source count matches its marks.  That is
    the two-source rule, it is enforced by hand, and it is not automated here.
  * C8's trailing-pipe rule is STRICTER than GFM, deliberately.  `| a | b` with
    no trailing pipe is legal markdown.  量 2026-08-30 over `git archive HEAD`
    with this parser: **every** row ends with `|` on its LAST physical line --
    the two C8b rows broke it on their FIRST, and that break IS the split, which
    is why enforcing the convention is the only thing that makes a raw newline
    inside a cell visible.  A clone that adopts the loose form would see false
    findings here.  (An earlier draft of this line said "3,570 of 3,572 carried
    one", which counts the wrong line of a split row.)
  * The sweep needs `git ls-files`.  Without git it has no population, and `T7`
    turns that into a refusal rather than a clean report over nothing.
  * `fence_mask` masks FENCED code blocks and not INDENTED ones (four spaces).
    An indented block holding an odd number of backticks could therefore pair a
    span across it and give C9 a false positive.  量 2026-08-30: zero such
    findings over the whole repository, so this is a stated limit and not an
    observed defect -- indented blocks here hold assembly and shell, not prose
    with backticks.  Handling them properly needs list-context awareness, which
    is a markdown parser, and that is more than this check is worth.
  * C8c reports a `|`-line whose table has no recognised header+separator pair.
    A table written with a separator that has no leading pipe (`--- | ---`)
    would make its header AND every row an orphan -- ten findings for one
    formatting choice, not ten defects.  The message says what it is looking
    for, and the repository uses the leading-pipe form throughout (量: zero
    orphans after today's ten were fixed).

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
#
# Two shapes, and the second was added 2026-08-24 because the first could not
# see `tools/hazlint`.  A program in this repo does not have to carry a suffix
# -- `tools/hazlint` does not, and `tools/rlxprobe/` will not either -- and a
# row whose owner is such a file was being counted as "owner is a gate or a
# note rather than a file" and skipped by C4 and C5 alike.  **That is a check
# quietly not checking**, which is the failure this file exists to catch, so it
# was found by a row rather than by a control and that is recorded here.
#
#   1. anything ending in a known source suffix, with or without directories
#   2. a slash-separated path whose last segment carries no dot at all
#
# Shape 2 deliberately requires a slash: a bare backticked word is far more
# often a register or a command name than a file.
PATH_RX = re.compile(r'`([^`]*?(?:/[^`]*)?\.(?:md|json|py|sh))`'
                     r'|`((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_-]+)`')

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


# A fenced code block is not markdown.  This matters the moment C8 stops being
# about SPEC.md: `docs/`, `notes/` and this repository's READMEs all print
# example tables inside fences, and counting their rows would make the check
# fire on text that never renders as a table.
#
# 🔴 The obvious implementation has a false positive, and it was measured before
# this was written: a throwaway checker used on 2026-08-30 read an INLINE
# triple-backtick span at the start of an indented line as an unclosed fence and
# swallowed the rest of a file.  A fence opener's info string may not itself
# contain a backtick (CommonMark 4.5), and requiring that is what separates the
# two.  `T6` is the case.
FENCE_RX = re.compile(r'^(\s{0,3})(`{3,}|~{3,})(.*)$')


def fence_mask(lines):
    """True for every line that is inside (or is) a fenced code block.

    Indentation of four or more spaces is not a fence at all -- that is an
    indented code block, and its content is not scanned for tables either, but
    it does not open a state that swallows what follows.
    """
    mask = [False] * len(lines)
    marker = None
    for i, ln in enumerate(lines):
        m = FENCE_RX.match(ln)
        if marker is None:
            if m and (m.group(2)[0] == '~' or '`' not in m.group(3)):
                marker, mask[i] = m.group(2), True
            continue
        mask[i] = True
        if (m and m.group(2)[0] == marker[0]
                and len(m.group(2)) >= len(marker) and not m.group(3).strip()):
            marker = None
    return mask


def table_rows(lines, mask, start):
    """Rows of the table whose header is at `start`, and the ragged/truncated
    findings that reading them produced.

    A ROW IS ONE LINE.  GFM has no continuation syntax, so a literal newline
    inside a cell -- most often inside a code span -- ends the row where the
    newline is and the remainder renders as a paragraph.  Every checker in this
    repository walked lines beginning with a pipe, so those continuation lines
    were invisible AND every row below them in the same table was dropped from
    the count: 量 2026-08-30, `RUNSHEET.md`'s `C7` row spans three physical
    lines because a code span holds a literal CR, and `PROGRESS.md:520` spans
    two.  This function reports the split (`C8b`) and then REJOINS the row so
    the rest of the table is still checked, which is the half that matters --
    a checker blinded from the first defect to the end of the table would have
    reported the file clean below it.

    The trailing pipe is a house rule, and it is stricter than GFM: `| a | b`
    with no trailing pipe is legal markdown.  量 2026-08-30 over the 71
    tracked `.md` files with this parser: EVERY row ends with `|` on its LAST
    physical line, and the two defective ones broke it on their FIRST -- which
    is the split itself.  Enforcing the convention is the only thing that makes
    a raw newline inside a cell visible at all.
    """
    rows, notes, j = [], [], start
    while j < len(lines) and lines[j].startswith('|') and not mask[j]:
        line, first, span = lines[j], j, 1
        while not line.rstrip().endswith('|'):
            # Look for the rest of the logical row.  A blank line, a line that
            # starts a new block, or twenty lines of searching all mean the row
            # has no end and the table stops here.
            k = j + span
            if (k >= len(lines) or not lines[k].strip() or span > 20
                    or mask[k]):
                notes.append(('C8b', first + 1, span,
                              'the row does not end with `|` and no continuation '
                              'line does either'))
                line = None
                break
            line += '\n' + lines[k]
            span += 1
            if lines[k].rstrip().endswith('|'):
                notes.append(('C8b', first + 1, span,
                              'a raw newline inside a cell splits this row over '
                              '%d physical lines; GFM ends the row at the first '
                              'one and renders the rest as a paragraph' % span))
                break
        if line is None:
            j += span
            break
        rows.append((first + 1, split_cells(line.replace('\n', ' ')), span))
        j = first + span
    return rows, notes, j


def parse(path, text=None):
    """Return (tables, lines).  A table is a dict with section, header, rows.

    `rows` are `(lineno, cells, span)`; `span` is 1 for every well-formed row.
    Each table also carries `used`, the physical line indices it consumed, which
    is what `C8c` needs to find a `|`-line belonging to no table at all.
    """
    if text is None:
        text = io.open(path, encoding='utf-8').read()
    lines = text.split('\n')
    mask = fence_mask(lines)
    tables, section, i = [], None, 0
    while i < len(lines):
        m = re.match(r'^## (\d+)\.', lines[i])
        if m:
            section = int(m.group(1))
        if (lines[i].startswith('|') and not mask[i] and i + 1 < len(lines)
                and re.match(r'^\|[\s:|-]+\|\s*$', lines[i + 1])):
            header = [clean_header(c) for c in split_cells(lines[i])]
            rows, notes, j = table_rows(lines, mask, i + 2)
            tables.append({'section': section, 'header': header,
                           'rows': rows, 'notes': notes, 'line': i + 1,
                           'used': set(range(i, j)),
                           'header_ok': lines[i].rstrip().endswith('|')})
            i = j
            continue
        i += 1
    return tables, lines


def orphan_rows(lines, mask, tables):
    """C8c: a line that looks like a table row and belongs to no table.

    This is not hypothetical and it is not new.  量 2026-08-27, recorded in
    `PROGRESS.md`: a single blank line put three fresh `SPEC.md` rows below the
    end of §14's table, so they formed a `|`-line fragment with no header,
    `spec-check.py` never parsed them, and it reported green -- those three rows
    carried no duplicate-id, no owner-exists and no cell-count check at all
    while the tool run before every commit said everything was fine.

    C8 cannot see it by construction: C8 walks TABLES, and a fragment is
    precisely a row that is in none.  A reader sees the difference immediately
    -- an orphan renders as a paragraph full of pipes -- which is why this is a
    checker rather than a habit.
    """
    used = set()
    for t in tables:
        used |= t['used']
    return [i for i, ln in enumerate(lines)
            if ln.startswith('|') and not mask[i] and i not in used]


def table_findings(path, tables, lines=None, mask=None):
    """C8/C8b/C8c for one file's tables.  One implementation, two callers: the
    SPEC.md report and the repository-wide sweep.  Two copies of a rule is how
    `hazlint`'s `_scan_elf` came to accept states the real program refused."""
    out = []
    if lines is not None and mask is not None:
        for i in orphan_rows(lines, mask, tables):
            out.append((
                'C8c',
                f'{path}:{i + 1}: {lines[i][:36]!r} starts with `|` and belongs '
                f'to no table -- there is no header above it, so it renders as a '
                f'paragraph of pipes and every check that reads a cell by index '
                f'skips it entirely'))
    for t in tables:
        n = len(t['header'])
        if not t['header_ok']:
            out.append(('C8b', f"{path}:{t['line']}: the header row does not end "
                               f"with `|`"))
        for lineno, span, msg in [(a, b, c) for _, a, b, c in t['notes']]:
            out.append(('C8b', f'{path}:{lineno}: {msg}'))
        for lineno, cells, _span in t['rows']:
            if not cells:
                continue
            if len(cells) != n:
                out.append((
                    'C8',
                    f'{path}:{lineno}: {cells[0][:24]!r} has {len(cells)} cell(s) '
                    f'and its header has {n} -- the cell count does not match its '
                    f'header. An unescaped `|` inside a cell shifts every column '
                    f'after it, and the checks that read V/N/來源/擁有者 by index '
                    f'then read the wrong cell and pass'))
    return out


# C9.  A code span whose content is only whitespace.
#
# This is the SAME defect as C8b seen one level down, and it is the one C8b
# cannot reach: `\r` and `\n` typed as real characters become a span holding a
# line break, and outside a table nothing renders differently enough to notice.
# 量 2026-08-30, before this existed: FOUR instances in the repository (the
# count read three until the finished checker was run over the tree at HEAD),
# and one
# of them --  docs/loader-command-semantics.md's readline listing -- annotated
# BOTH exits of a three-way branch with the same empty character, so the
# sentence "only one writes a terminator" named neither.  It was settled by
# disassembling $FWRE_WORK/stage2.bin at 0x804070e4: `li v0,10` / `beq` is the
# LF exit and returns with no NUL, `li v0,13` / `bne` / `j` puts `sb zero,0(s0)`
# in the jump's delay slot, so CR is the one that writes it.  SPEC.md LDR-06d
# already said so; this file's own listing did not.
#
# CommonMark 6.1: a backtick run of length N opens a span closed by the next run
# of EXACTLY length N, and an unmatched run is literal text.  Pairing that way
# rather than counting backticks per line is what separates this from two
# ADJACENT spans across a line break (`SPEC.md` then `CPU-19`), which is
# ordinary and which a per-line parity test reports thirteen times.
TICKS_RX = re.compile(r'`+')


def code_spans(text):
    """(start, end, content) for every CLOSED code span in `text`."""
    runs = [(m.start(), m.end() - m.start()) for m in TICKS_RX.finditer(text)]
    i = 0
    while i < len(runs):
        pos, n = runs[i]
        j = i + 1
        while j < len(runs) and runs[j][1] != n:
            j += 1
        if j >= len(runs):
            i += 1
            continue
        yield pos, runs[j][0] + n, text[pos + n:runs[j][0]]
        i = j + 1


def span_findings(path, lines, mask):
    """C9 for one file, plus how many spans were looked at.

    The count is returned because a checker that reports zero over an empty
    population is the failure this repository keeps catching, and `T8` asserts
    the population is large.
    """
    prose = '\n'.join('' if mask[i] else ln for i, ln in enumerate(lines))
    out, total = [], 0
    for a, _b, content in code_spans(prose):
        total += 1
        if content != '' and content.strip() == '':
            ln = prose.count('\n', 0, a) + 1
            out.append(('C9', f'{path}:{ln}: a code span whose whole content is '
                              f'{content!r} -- an escape typed as a real '
                              f'character. `\\r` and `\\n` degrade to exactly '
                              f'this and the rendering shows nothing'))
    return out, total


# --- C11.  A source line number is a reference that rots ------------------
#
# THE FIX IS A FORMAT, NOT A CHECKER ON THE OLD FORMAT, and the reason is that
# the old format carries nothing to check against.  A reference now reads
#
#     `probe3.c:1533 (best_t & 0xFFFFFF00u)`
#
# and the token is the durable half: when the payload is edited the line moves,
# this goes red, and the number is re-derived by searching for the token.
#
# ⚠️ WHAT THIS DOES NOT DO, stated rather than left to be found:
#   * It anchors the START of a range.  `probe3.c:1383-1396` whose END drifts
#     while its start does not is a defect C11 cannot see.
#   * The token is matched WHITESPACE-NORMALISED, because a reflowed tab is not
#     reference rot.  A token that differs from its line only in whitespace
#     therefore passes, which is the intent.
#   * It says nothing about whether the SENTENCE is still true.  It says the
#     citation still points at the construct it named.
#
# The population is `tools/rlxprobe/` -- the payload sources, which this
# repository edits.  References into `src-vendor/` and `upstream/` are pinned
# at a sha and do not rot; that is why they are not here, and T21 asserts the
# population this DOES cover is not empty.
SRCREF_DIR = os.path.join('tools', 'rlxprobe')
SRCREF_TOL = 3
SRCREF_RX = re.compile(r'^(?:tools/rlxprobe/)?([A-Za-z0-9_][A-Za-z0-9_.\-]*'
                       r'\.(?:c|h|S|lds)):(\d+)(?:-(\d+))?(.*)$', re.S)

# Exempt, each with a reason, and T22 asserts the exemption is LOAD-BEARING --
# if these files ever stop holding a reference, the entry has to come out
# rather than sit here forever unread.
#
# 🔴 `study/` IS NOT ON THIS LIST AND THAT IS NOT AN OVERSIGHT.  It is
# gitignored (`.gitignore:17`), so `table_scope()` -- which is `git ls-files`
# -- never yields it and the sweep cannot reach it in the first place.  An
# entry for it would be a row that can never fire, which is the shape T22
# exists to keep out of this dict; 量 2026-08-31, the first version of this
# dict had one.
SRCREF_EXEMPT = {
    'bench/': 'frozen prediction blocks and their corrections: captures have '
              'landed against these numbers, and a record silently updated to '
              'match today\'s source stops being a record',
    'LOG.md': 'the working log is a record of what was true on a date',
    'CHANGELOG.md': 'a record',
    'docs/rlxprobe-audit-2026-08-25.md':
        'a DATED audit.  量 2026-08-31: two of its three references have '
        'ALREADY rotted -- probe2.c:273 is now a blank line and probe1.c:299 '
        'a fragment of a comment -- and what it cited was correct on '
        '2026-08-25.  Repairing them would destroy the record rather than fix '
        'it, which is the same call the seventeenth session made when it '
        'reverted its own over-reach into a frozen block',
}


def srcref_exempt(rel):
    for pre in SRCREF_EXEMPT:
        if rel == pre or rel.startswith(pre):
            return pre
    return None


def srcref_sources(root=ROOT):
    """basename -> lines, for every payload source.  A dict rather than a
    directory read at match time, so the controls can inject a fixture."""
    out = {}
    d = os.path.join(root, SRCREF_DIR)
    try:
        names = os.listdir(d)
    except OSError:
        return out
    for n in sorted(names):
        if not n.endswith(('.c', '.h', '.S', '.lds')):
            continue
        try:
            out[n] = io.open(os.path.join(d, n), encoding='utf-8').read().split('\n')
        except OSError:
            continue
    return out


def _norm(s):
    return ' '.join(s.split())


def srcref_findings(path, lines, mask, sources):
    """C11 for one file.  Returns (findings, how many references were in scope).

    The count is returned for the same reason span_findings returns one: a
    checker reporting zero over an empty population is the failure this file
    exists to catch.
    """
    prose = '\n'.join('' if mask[i] else ln for i, ln in enumerate(lines))
    out, n = [], 0
    for a, _b, content in code_spans(prose):
        m = SRCREF_RX.match(content)
        if not m:
            continue
        name, start, _end, tail = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if name not in sources:
            continue                      # not a payload source: not in scope
        n += 1
        ln = prose.count('\n', 0, a) + 1
        if not (tail.startswith(' (') and tail.endswith(')') and len(tail) > 3):
            out.append(('C11', f'{path}:{ln}: `{content}` carries no token. '
                               f'A bare line number rots silently; write '
                               f'`{name}:{start} (a short token from that line)`'))
            continue
        tok = tail[2:-1]
        if '|' in tok or '`' in tok:
            out.append(('C11', f'{path}:{ln}: `{content}` has a token holding '
                               f'| or a backtick, which breaks the row or the '
                               f'span it sits in'))
            continue
        src = sources[name]
        lo, hi = max(1, start - SRCREF_TOL), min(len(src), start + SRCREF_TOL)
        want = _norm(tok)
        if any(want in _norm(src[k - 1]) for k in range(lo, hi + 1)):
            continue
        where = [k for k, s in enumerate(src, 1) if want in _norm(s)]
        at = (f'it is at {name}:{where[0]}' if len(where) == 1 else
              f'it is at {name}:{where[:4]}' if where else
              f'it is nowhere in {name}')
        out.append(('C11', f'{path}:{ln}: `{content}` -- the token is not '
                           f'within {SRCREF_TOL} lines of {start}; {at}'))
    return out, n


def table_scope(root=ROOT):
    """Every tracked `.md`, which is the honest population for a rule about how
    this repository's prose renders.

    A DECLARED list was the alternative and it is the worse one: a file added
    without a line in it is silently exempt, and "a check that quietly does not
    check" is the failure this file exists to catch.  `upstream/` is a submodule
    and a gitlink, so `git ls-files` never descends into it; `plan/` is
    gitignored and is not tracked.  Both facts are asserted by `T7` rather than
    assumed.
    """
    try:
        out = subprocess.run(['git', '-C', root, 'ls-files', '*.md'],
                             capture_output=True, text=True, encoding='utf-8',
                             timeout=30)
        paths = [p for p in out.stdout.split('\n') if p.strip()]
    except (OSError, subprocess.SubprocessError):
        paths = []
    return sorted(p for p in paths if not p.startswith('upstream/'))


# C10.  A paragraph whose backtick runs cannot pair.
#
# C9 pairs runs over the whole file, so an unmatched run is silently absorbed by
# whatever comes next and only becomes visible when the file grows.  量
# 2026-08-30: three instances in this repository, and the one in
# notes/kernel-build.md had been committed for a day while C8/C8b/C8c/C9 all
# passed over it.  A blank line ends a code span, so parity INSIDE one paragraph
# is the test that does not depend on the rest of the file.
#
# Run LENGTH, not backtick count.  A per-line count reports thirteen ordinary
# adjacent-span pairs in this repository, which is why this is not that test.
# 🔴 The comment here used to offer `x``y` as the worked example and that was
# wrong -- measured against markdown-it-py, it does NOT fire and renders as one
# span whose CONTENT is x``y.  The real example is RUNSHEET.md's `byte 0` line,
# where a run of two closed a run of one.
#
# 🔴 WHAT THIS DOES NOT DO, measured 2026-08-30 by an adversarial pass with a
# real CommonMark oracle, and stated here because the checker's own message used
# to overstate it:
#
#   * An unclosed run is LITERAL TEXT, not an open span.  Nothing is swallowed
#     unless a paragraph has three or more runs and the pairing SHIFTS -- which
#     is the notes/kernel-build.md instance, and is not what T11/T16 plant.
#   * The paragraph is not the rendering unit.  CommonMark ends an inline
#     context at ATX headings (4.2), thematic breaks (4.1), list items (5.2)
#     and `>`-only lines in a block quote; GFM splits a table row on pipes
#     BEFORE inline parsing.  C10 pairs across all of those.  量: 930 of 5,079
#     tick-carrying blocks in this tree (18 %) hold more than one inline
#     context and 624 hold a table row -- REALISED false negatives today: 0,
#     against a render oracle over every tracked file.
#   * A backslash-escaped backtick (2.4) is counted as a delimiter, so a
#     paragraph containing one can fire.  量: zero such backticks in the tree
#     today, so the exposure is latent.  Same for backticks inside an HTML
#     comment, an indented code block or an autolink.
#
# So C10 is a HEURISTIC whose result is currently correct and whose mechanism is
# narrower than the defect.  It stays because it found three real instances that
# every other check walked past; it is documented rather than trusted.

# The one file this cannot be applied to, with the reason.  T13 asserts the
# exemption is LOAD-BEARING -- if the file is ever repaired, T13 goes red and
# the entry has to come out, rather than sitting here forever unread.
C10_EXEMPT = {
    'bench/2026-08-25b/PREDICTIONS-b4-block2.md':
        'frozen prediction block: check-predictions.py reads its mtime, so '
        'editing it would make its 2026-08-25 captures read as older than the '
        'prediction naming them. The defect is real and is recorded in '
        'bench/README.md rather than repaired',
}


def paragraph_blocks(lines, mask):
    """(start_line, text) for each blank-line-separated block, fences masked."""
    cur, start = [], 1
    for i, ln in enumerate(lines, 1):
        if mask[i - 1]:
            if cur:
                yield start, '\n'.join(cur)
                cur = []
            continue
        if not ln.strip():
            if cur:
                yield start, '\n'.join(cur)
                cur = []
            continue
        if not cur:
            start = i
        cur.append(ln)
    if cur:
        yield start, '\n'.join(cur)


def _runs_unpairable(text):
    """True if some backtick run in `text` can never close."""
    runs, i = [], 0
    while i < len(text):
        if text[i] == '`':
            j = i
            while j < len(text) and text[j] == '`':
                j += 1
            runs.append(j - i)
            i = j
        else:
            i += 1
    # No `used` bookkeeping: `k = m + 1` already resumes after the closer,
    # which is CommonMark's own rule.  An earlier version carried a `used`
    # array and an adversarial pass showed deleting it changed nothing -- dead
    # code in a checker is a place a reader looks for meaning and finds none.
    k = 0
    while k < len(runs):
        m = k + 1
        while m < len(runs) and runs[m] != runs[k]:
            m += 1
        if m >= len(runs):
            return True
        k = m + 1
    return False


def paragraph_findings(path, lines, mask, honour_exempt=True):
    """C10 for one file, plus how many paragraphs were looked at."""
    out, total = [], 0
    exempt = honour_exempt and path in C10_EXEMPT
    for start, text in paragraph_blocks(lines, mask):
        total += 1
        if '`' not in text:
            continue
        if _runs_unpairable(text):
            if exempt:
                continue
            first = text.split('\n')[0][:110]
            out.append(('C10', f'{path}:{start}: a backtick run in this '
                               f'paragraph can never close, so it renders as a '
                               f'literal backtick -- and if the paragraph has '
                               f'another run, the pairing SHIFTS and a span '
                               f'swallows prose: {first!r}'))
    return out, total


def check_tables(paths, root=ROOT):
    """The repository-wide sweep: C8/C8b over tables, C9 over every code span.
    Returns (findings, stats)."""
    findings = []
    stats = {'files': 0, 'tables': 0, 'rows': 0, 'spans': 0, 'paragraphs': 0,
             'srcrefs': 0, 'srcrefs_exempt': 0, 'unreadable': []}
    sources = srcref_sources(root)
    for rel in paths:
        full = os.path.join(root, rel)
        try:
            text = io.open(full, encoding='utf-8').read()
        except OSError:
            stats['unreadable'].append(rel)
            continue
        lines = text.split('\n')
        tables, _ = parse(full, text=text)
        stats['files'] += 1
        stats['tables'] += len(tables)
        stats['rows'] += sum(len(t['rows']) for t in tables)
        m = fence_mask(lines)
        findings += table_findings(rel, tables, lines, m)
        sf, nspans = span_findings(rel, lines, fence_mask(lines))
        stats['spans'] += nspans
        findings += sf
        pf, npara = paragraph_findings(rel, lines, m)
        stats['paragraphs'] += npara
        findings += pf
        # C11 counts its population on EVERY file and checks it on the live
        # ones, so the exempt count is a measurement rather than a silence.
        rf, nref = srcref_findings(rel, lines, m, sources)
        if srcref_exempt(rel):
            stats['srcrefs_exempt'] += nref
        else:
            stats['srcrefs'] += nref
            findings += rf
    return findings, stats


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
    """PATH_RX has two alternatives, so findall gives pairs; keep whichever fired."""
    return [a or b for a, b in PATH_RX.findall(cell)]


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
        for lineno, cells, _span in t['rows']:
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
        for lineno, cells, _span in t['rows']:
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

    # ---- C8/C8b: a row has as many cells as its own header, on one line -----
    # Every other check reads a cell BY INDEX.  One unescaped `|` inside a cell
    # shifts every index after it, and the checks downstream do not fail -- they
    # read a different cell and pass on it.  So this one runs over every table
    # in the file, not only the definition tables, because §17 is read by C3.
    #
    # The rule itself lives in `table_findings()`, because since 2026-08-30 it
    # is not a rule about SPEC.md: `check_tables()` runs the same function over
    # every tracked `.md`.  Two copies of a rule is how `hazlint`'s `_scan_elf`
    # came to accept states the real program refused.
    t8 = table_findings(path, tables, lines, fence_mask(lines))
    findings += t8
    stats['ragged'] = sum(1 for c, _ in t8 if c == 'C8')
    stats['split'] = sum(1 for c, _ in t8 if c == 'C8b')
    stats['tables_all'] = len(tables)
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
    print(f"  C8 cell counts checked against the header in {stats['tables_all']} table(s), "
          f"including the ones outside §1–17: {stats['ragged']} ragged, "
          f"{stats['split']} split over more than one line")
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
    # M9 is not invented.  It re-creates the exact defect that was in this file
    # from the day CPU-19 was written until 2026-08-26: the `|` inside
    # `Status.IsC|SwC` was never escaped, so the row had eight cells in a
    # seven-column table and C4/C5 read its SOURCE cell as its owner.
    ('M9 un-escape a `|` inside a cell', 'C8', 'does not match its header',
     lambda s: s.replace(r'`Status.IsC\|SwC`', '`Status.IsC|SwC`', 1)),
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


# ---------------------------------------------------------------------------
# The table sweep's own controls.  These do NOT mutate a committed file: the
# subject is a fixture built here, because the rule is now about seventy-one
# files and mutating one of them would tie the control to whatever that file
# happens to contain today.  `T1` is the positive one and it is the reason the
# other four mean anything -- a checker that fires on everything passes every
# mutation.
# ---------------------------------------------------------------------------
FIXTURE = '''# fixture

An ordinary table, well formed.

| id | what | note |
|---|---|---|
| `A-01` | a value with an escaped pipe `a\\|b` inside a code span | fine |
| `A-02` | plain | fine |

A fenced block whose content is NOT markdown.  The table inside it is ragged on
purpose: if the fence mask ever stops working, this is what says so.

```
| id | what |
|---|---|
| this row | has | three cells against two |
```

An INLINE triple-backtick span at the start of an indented line, which a naive
fence detector reads as an unclosed fence and then swallows the rest of the
file with:

    ```x``` and more text on the same line

| id | what |
|---|---|
| `B-01` | still parsed, because the line above is not a fence |

Two ADJACENT code spans across a line break are ordinary and must not be a
finding: `SPEC.md`
`CPU-19` is one reference followed by another, and a per-line backtick-parity
test reports thirteen of these in this repository.

A paragraph whose runs DO pair, including a doubled run that has its partner:
``a`b`` and `plain` and ``c`` are all closed.

A fenced block whose content holds an unpairable RUN OF THREE. With the mask working this
is invisible and T1 stays clean; with the mask off, C10 reports it, which is
what stops a mutant that scans fences as prose from passing everything.

```
this line has ``` in the middle, which the fence markers cannot absorb
```
'''

TABLE_MUTATIONS = [
    ('T2 un-escape a `|` inside a code span', 'C8', 'does not match its header',
     lambda s: s.replace(r'`a\|b`', '`a|b`', 1), 1),
    ('T3 split one row over two physical lines', 'C8b', 'raw newline inside a cell',
     lambda s: s.replace('| `A-02` | plain | fine |',
                         '| `A-02` | pl\nain | fine |', 1), 1),
    ('T4 delete a cell, so the row has FEWER than its header', 'C8',
     'does not match its header',
     lambda s: s.replace('| `A-02` | plain | fine |', '| `A-02` | plain |', 1), 1),
    ('T6 a ragged row after an inline ``` span is still seen', 'C8',
     'does not match its header',
     lambda s: s.replace('| `B-01` | still parsed, because the line above is not a fence |',
                         '| `B-01` | still parsed | and ragged |', 1), 1),
    # T8 is C9's, and it is deliberately in PROSE rather than in a cell: this is
    # the shape C8b cannot see, and the one that made a reading wrong in
    # docs/loader-command-semantics.md rather than only a rendering.
    ('T8 an escape typed as a real newline, in prose', 'C9',
     'whole content is', lambda s: s + "\nthe `\n` path writes a NUL\n", 1),
    # T10 is C8c's.  One blank line inside a table strands every row below it,
    # and C8 cannot see that by construction: C8 walks tables, and a stranded
    # row is in none.  量 2026-08-30 the first time this ran: NINE rows of
    # docs/FINDINGS.md and one of bench/README.md were outside their tables.
    ('T10 a blank line strands the row below it', 'C8c',
     'belongs to no table',
     lambda s: s.replace('| `A-02` | plain | fine |',
                         '\n| `A-02` | plain | fine |', 1), 1),
    # T11 is C10's.  An opening backtick with no closer -- the shape that had
    # been committed in notes/kernel-build.md for a day while every other check
    # passed over it, because C9 pairs runs across the whole FILE and this one
    # found a partner further down.
    ('T11 an opening backtick that never closes', 'C10',
     'can never close', lambda s: s + "\nthe `0x2D0000 = 2,949,120 value.\n", 1),
    # T14 pins RUN LENGTH against backtick COUNT.  `x`` leaves the count EVEN,
    # so a parity implementation passes T11 and misses this -- and this is the
    # real shape found in RUNSHEET.md on 2026-08-30, where `byte 0 → the
    # device's own `\r\nBooting`` closed with a run of two and left the middle
    # span rendering as prose.
    ('T14 a doubled closing run, so the COUNT is even', 'C10',
     'can never close',
     lambda s: s + "\nnow `byte 0 and the device's own `marker``, guarded.\n", 1),
    # T15 pins the PARAGRAPH boundary.  Two unclosed runs of the same length,
    # one per paragraph: correct code reports two, an implementation that pairs
    # across the whole file reports none.  That is C9's order-dependence, which
    # is the defect C10 was added for.
    ('T15 two paragraphs, one unclosed run each', 'C10',
     'can never close',
     lambda s: s + "\nfirst `unclosed here.\n\nsecond `unclosed here.\n", 2),
]


SRCREF_FIXTURE_SRC = {'fix.c': [
    'line one',                                    # 1
    'static const u32 L_FIX[] = { 1u, 2u };',      # 2
    'line three',                                  # 3
    'line four',                                   # 4
    'line five',                                   # 5
    'line six',                                    # 6
    'far away marker',                             # 7
]}

# Every case names the ONE thing it pins.  T20a/T20b are a pair on purpose:
# one edge each of SRCREF_TOL, because a single case at the boundary passes
# whether the comparison is `<` or `<=`.
SRCREF_CASES = [
    ('T17 a reference whose token is on its line is clean',
     'a `fix.c:2 (static const u32 L_FIX[])` reference', 0, ''),
    ('T18 a bare line number is caught',
     'a `fix.c:2` reference', 1, 'carries no token'),
    ('T19 a token that is elsewhere in the file is caught',
     'a `fix.c:2 (far away marker)` reference', 1, 'it is at fix.c:7'),
    ('T19b a token that is nowhere is caught',
     'a `fix.c:2 (no such text)` reference', 1, 'it is nowhere in fix.c'),
    ('T20a a token exactly SRCREF_TOL lines away still passes',
     'a `fix.c:5 (static const u32 L_FIX[])` reference', 0, ''),
    ('T20b a token one line PAST SRCREF_TOL is caught',
     'a `fix.c:6 (static const u32 L_FIX[])` reference', 1, 'not within 3'),
    ('T20c a token with a pipe is caught before it breaks a row',
     'a `fix.c:2 (L_FIX[] = { 1u| 2u })` reference', 1, 'holding'),
    ('T23 a reference to a file that is not a payload source is out of scope',
     'a `rtl819x_flash.c:62-73` reference', 0, ''),
]


def srcref_controls(verbose=True):
    """C11's controls: a fixture source, and one case per failure mode.

    The fixture SOURCE is injected rather than read from tools/rlxprobe/, so
    these cases do not go red the next time the payload is edited -- which is
    the very event C11 exists to catch, and a control that fires on it would be
    a control that cannot be trusted on the day it matters.
    """
    fail = ok = 0
    if verbose:
        print('=== C11 CONTROLS: a fixture source, and one case per failure ===')
    for label, body, n_want, want_msg in SRCREF_CASES:
        lines = ['# fixture', '', body, '']
        got, n_scope = srcref_findings('fixture.md', lines,
                                       [False] * len(lines), SRCREF_FIXTURE_SRC)
        hit = [m for c, m in got if c == 'C11' and want_msg in m]
        okrow = (len(got) == n_want and (n_want == 0 or len(hit) == n_want))
        if okrow:
            print(f'  ok    {label:58s} '
                  + (f'0 findings, {n_scope} in scope' if n_want == 0
                     else f'caught: …{want_msg}…'))
            ok += 1
        else:
            print(f'  FAIL  {label:58s} wanted {n_want} finding(s) saying '
                  f'{want_msg!r}, got {len(got)}')
            for _c, m in got[:2]:
                print(f'          {m[:120]}')
            fail += 1

    # T21 and T22 are population controls on the REAL tree, not the fixture.
    # T21: the checker is looking at something.  T22: the exemption is
    # load-bearing rather than a list nobody reads.
    _f, st = check_tables(table_scope())
    if st['srcrefs'] > 0:
        print(f'  ok    {"T21 the live population is not empty":58s} '
              f'{st["srcrefs"]} reference(s) checked, so T17 is not clean by '
              f'looking at nothing')
        ok += 1
    else:
        print(f'  FAIL  {"T21 the live population is not empty":58s} '
              f'0 references in scope -- C11 is passing vacuously')
        fail += 1
    if st['srcrefs_exempt'] > 0:
        print(f'  ok    {"T22 the exemption is load-bearing":58s} '
              f'{st["srcrefs_exempt"]} reference(s) sit in record files')
        ok += 1
    else:
        print(f'  FAIL  {"T22 the exemption is load-bearing":58s} '
              f'no reference is exempt -- SRCREF_EXEMPT is dead and must go')
        fail += 1

    print(f'  {ok} passed, {fail} failed')
    return fail


def table_controls(verbose=True):
    """Five controls on the sweep, and the first one is the positive."""
    fail = ok = 0
    if verbose:
        print('=== TABLE SWEEP CONTROLS: a fixture, and mutations of it ===')

    def findings_for(text, mask_on=True):
        real = globals()['fence_mask']
        if not mask_on:
            globals()['fence_mask'] = lambda lines: [False] * len(lines)
        try:
            lines = text.split('\n')
            tables, _ = parse('fixture.md', text=text)
            out = table_findings('fixture.md', tables, lines, fence_mask(lines))
            sf, _n = span_findings('fixture.md', lines, fence_mask(lines))
            pf, _p = paragraph_findings('fixture.md', lines, fence_mask(lines))
            return out + sf + pf
        finally:
            globals()['fence_mask'] = real

    base = findings_for(FIXTURE)
    if base:
        print(f'  FAIL  {"T1 the clean fixture produces no finding":52s} '
              f'{len(base)} finding(s): {base[0][1][:90]}')
        fail += 1
    else:
        print(f'  ok    {"T1 the clean fixture produces no finding":52s} '
              f'0 findings, so T2-T6 are not passing on a checker that always fires')
        ok += 1

    for label, want, want_msg, mutate, n_want in TABLE_MUTATIONS:
        mutated = mutate(FIXTURE)
        if mutated == FIXTURE:
            print(f'  FAIL  {label:52s} the mutation did not change the fixture')
            fail += 1
            continue
        got = findings_for(mutated)
        hit = [m for c, m in got if c == want and want_msg in m]
        if len(hit) == n_want and len(got) == n_want:
            print(f'  ok    {label:52s} caught by {want}: …{want_msg}…')
            ok += 1
        else:
            codes = sorted({c for c, _ in got})
            print(f'  FAIL  {label:52s} wanted {n_want} {want} finding(s) saying '
                  f'{want_msg!r}, got {len(got)} {codes}')
            for c, m in got[:3]:
                print(f'          [{c}] {m[:110]}')
            fail += 1

    # T5 is a control on a control: with the fence mask off, the CLEAN fixture
    # must stop being clean.  Without it, T1 passes on a checker that skips
    # everything and the fence rule is untested in the direction that matters.
    off = findings_for(FIXTURE, mask_on=False)
    if off:
        print(f'  ok    {"T5 with the fence mask off the fixture goes red":52s} '
              f'{len(off)} finding(s), so T1 is not clean by skipping everything')
        ok += 1
    else:
        print(f'  FAIL  {"T5 with the fence mask off the fixture goes red":52s} '
              f'still clean -- the sweep may be reading no tables at all')
        fail += 1

    # T9 is C9's negative: the repaired form of T8's line must produce nothing.
    # Without it, `C9` could be firing on every code span and T8 would not know.
    repaired = findings_for(FIXTURE + "\nthe `\\r` path writes a NUL\n")
    if repaired:
        print(f'  FAIL  {"T9 the repaired escape is not a finding":52s} '
              f'{len(repaired)}: {repaired[0][1][:80]}')
        fail += 1
    else:
        print(f'  ok    {"T9 the repaired escape is not a finding":52s} '
              f'`\\r` written as an escape is clean, so C9 is not firing on '
              f'every span')
        ok += 1

    # T12 is C10's negative: the repaired form must be clean.  Without it C10
    # could be firing on every paragraph and T11 would not know.
    rep10 = findings_for(FIXTURE + "\nthe `0x2D0000` = 2,949,120 value.\n")
    if rep10:
        print(f'  FAIL  {"T12 the closed span is not a finding":52s} '
              f'{len(rep10)}: {rep10[0][1][:80]}')
        fail += 1
    else:
        print(f'  ok    {"T12 the closed span is not a finding":52s} '
              f'a paragraph whose runs pair is clean, so C10 is not firing on '
              f'every paragraph')
        ok += 1

    # T13 is a control on the EXEMPTION.  An exemption nobody checks is a
    # permanent hole; this asserts each entry is still load-bearing, so a file
    # that gets repaired forces its entry out instead of hiding a later defect.
    stale = []
    for rel in sorted(C10_EXEMPT):
        full = os.path.join(ROOT, rel)
        try:
            lines = io.open(full, encoding='utf-8').read().split('\n')
        except OSError:
            stale.append((rel, 'unreadable'))
            continue
        got, _n = paragraph_findings(rel, lines, fence_mask(lines),
                                     honour_exempt=False)
        if not got:
            stale.append((rel, 'no longer has an unpairable paragraph'))
    if stale:
        for rel, why in stale:
            print(f'  FAIL  {"T13 every C10 exemption is load-bearing":52s} '
                  f'{rel}: {why} -- remove the entry')
        fail += 1
    else:
        print(f'  ok    {"T13 every C10 exemption is load-bearing":52s} '
              f'{len(C10_EXEMPT)} entry/entries, each still firing without it')
        ok += 1

    # T16 is N6's.  Every other C10 control appends text ending in a newline,
    # and a trailing newline flushes the block through the blank-line branch --
    # so the trailing `if cur:` in paragraph_blocks was never exercised and a
    # mutant deleting it passed all fifteen. A file whose last line has no
    # newline is ordinary, and this is the only control that reaches it.
    nonl = findings_for(FIXTURE + "\ntrailing `unclosed with no final newline.")
    hit16 = [m for c, m in nonl if c == 'C10' and 'can never close' in m]
    if len(hit16) == 1:
        print(f'  ok    {"T16 a defect in a file with no trailing newline":52s} '
              f'caught by C10, so paragraph_blocks yields its last block')
        ok += 1
    else:
        print(f'  FAIL  {"T16 a defect in a file with no trailing newline":52s} '
              f'wanted 1 C10 finding, got {len(hit16)} -- the final paragraph '
              f'may never be yielded')
        fail += 1

    # T17 is N12's.  Nothing asserted the LINE a C10 finding names, so an
    # off-by-one passed every control. The expected line is COMPUTED from the
    # fixture rather than hardcoded, so an edit to the fixture cannot make this
    # control quietly stale.
    lead = FIXTURE + "\n"
    planted = lead + "the `0x2D0000 = 2,949,120 value.\n"
    want_line = lead.count("\n") + 1
    got17 = [m for c, m in findings_for(planted) if c == 'C10']
    if len(got17) == 1 and f'fixture.md:{want_line}:' in got17[0]:
        print(f'  ok    {"T17 the finding names the paragraph\'s first line":52s} '
              f'line {want_line}, computed from the fixture rather than hardcoded')
        ok += 1
    else:
        print(f'  FAIL  {"T17 the finding names the paragraph\'s first line":52s} '
              f'wanted 1 finding naming line {want_line}, got '
              f'{[m[:60] for m in got17]}')
        fail += 1

    # T7 is about the POPULATION.  A sweep whose file list is empty reports zero
    # findings and is green, which is the "a tool reporting 0 is making a claim"
    # failure this repository keeps catching.
    scope = table_scope()
    dirs = {os.path.dirname(p) for p in scope}
    why = None
    if len(scope) < 10:
        why = f'only {len(scope)} file(s) -- git ls-files returned nothing usable'
    elif 'SPEC.md' not in scope:
        why = 'SPEC.md is not in it'
    elif len(dirs) < 2:
        why = f'every file is in one directory ({dirs})'
    elif any(p.startswith('upstream/') for p in scope):
        why = 'it descends into upstream/, which is a pinned submodule'
    if why:
        print(f'  FAIL  {"T7 the sweep has a population":52s} {why}')
        fail += 1
    else:
        print(f'  ok    {"T7 the sweep has a population":52s} '
              f'{len(scope)} tracked .md in {len(dirs)} directories, SPEC.md among '
              f'them, none under upstream/')
        ok += 1

    if verbose:
        print()
        if fail:
            print(f'  {ok} table controls held, \033[31m{fail} did not\033[0m')
        else:
            print(f'  ok  all {ok} table controls held\n')
    return fail


def report_tables(findings, stats):
    print('=== every tracked .md — C8/C8b/C8c/C9/C10 ===')
    print(f"  {stats['rows']} table row(s) in {stats['tables']} table(s), "
          f"{stats['spans']} code span(s) and {stats['paragraphs']} "
          f"paragraph(s), across {stats['files']} file(s)")
    print(f"  C11: {stats['srcrefs']} payload-source reference(s) checked, "
          f"{stats['srcrefs_exempt']} in record files (exempt, reasons in "
          f"SRCREF_EXEMPT)")
    if C10_EXEMPT:
        print(f"  ⚠️  {len(C10_EXEMPT)} file(s) exempt from C10, each with a "
              f"reason and a control (T13): {', '.join(sorted(C10_EXEMPT))}")
    if stats['unreadable']:
        print(f"  🔴 {len(stats['unreadable'])} file(s) could not be read: "
              f"{', '.join(stats['unreadable'][:5])}")
    print()
    if not findings:
        print('  ok  no ragged row, no row split over more than one line, no '
              'row stranded outside its table, no code span whose content '
              'is only whitespace, no paragraph leaving a span open, and '
              'every payload-source reference still finds its token')
        return 0
    for c, msg in sorted(findings):
        print(f'  FAIL [{c}] {msg}')
    print(f'\n  {len(findings)} finding(s)')
    return 1


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    path = os.path.join(ROOT, args[0]) if args else os.path.join(ROOT, 'SPEC.md')
    if not os.path.exists(path):
        print(f'no such file: {path}')
        return 2

    failed = controls(path)
    failed += table_controls()
    failed += srcref_controls()
    if failed:
        print('  REFUSING to report on the file: a check that cannot fail would '
              'report it clean whatever it says')
        return 2
    if '--self-test' in argv:
        return 0

    findings, stats = check(path)
    rc = report(path, findings, stats)

    # The sweep is a second report, not a second tool.  It runs over every
    # tracked `.md` INCLUDING the one above, so a ragged row in SPEC.md appears
    # twice -- deliberately: the file-specific report is what an author of
    # SPEC.md reads, and the sweep is what says the rule holds everywhere.
    tf, ts = check_tables(table_scope())
    return rc | report_tables(tf, ts)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
