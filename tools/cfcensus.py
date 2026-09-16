#!/usr/bin/env python3
"""cfcensus.py -- the DEBT axis of the census, derived rather than chosen.

`R1z-0` has to say what this repository OWES before `R1z-1`..`R1z-3` pay any
of it.  `tools/isacensus.py` did that job for the ISA axis on 2026-09-12 and
`tools/tccensus.py` for the toolchain axis on 2026-09-12; this is the third
sibling and it IMPORTS both of the pieces it shares rather than restating
them (`isacensus.Refused`, `isacensus.doc_block`, and `spec-check`'s own
`progress_step_state`).

WHY IT EXISTS, and the sentence is the gate's.  `PROGRESS.md` § Carried
forward opens with its own rule -- *an item with no owning gate is a bug in
this list* -- and in the twenty-five segments since that line was written
**nothing has ever checked it**.  The seventy-seventh segment measured why
that matters: four checkers went green while believing they were checking
something, and the one checker that did its job (`tccensus`) differed from
them in exactly one respect -- **its population came from another instrument
instead of from a hand-written list**.  A hand list cannot notice a row added
after the list was written.  This tool is that lesson applied to the debts.

🔴 THE FIRST-CELL RULE, MEASURED BEFORE IT WAS WRITTEN.  A row is CLOSED iff
its FIRST cell carries `✅` or `⊘`.  The obvious alternative -- believe the
owning-gate cell when it says `關了` / `closed` / `✅` -- was tried first and
量 2026-09-16 it mislabels **5 of 16** rows (31 %), because that cell also
carries prose about a GATE closing:

    `XNUM-1`   owner cell says ``R5-11` 關了` -- the GATE closed, and the row
               is the one thing `R1z` exists to finish.  Calling it closed
               would delete this gate's own test case.
    `GPIO-1`   owner cell says *still not measured* beside a closed gate id.
    `REL-0`/`REL-1`/`REL-3`  owner is the word `none`; the `✅`/`closed` in
               the cell is prose about `R3-11` and about v0.2.

Narrowing the keyword set to `✅` alone drops `XNUM-1` and `GPIO-1` but keeps
`REL-0` and `REL-3`, so no keyword rule on that cell is correct.  **The first
cell is the only cell whose `✅` means "this row".**

🔴 AND THERE IS A THIRD PLACE, WHICH THE FIRST DRAFT OF THIS TOOL MISSED.
The QUESTION cell also carries closures.  量 over all 108 rows, re-derived
rather than carried: 17 rows mark the first cell, 13 more mark only the
owning-gate cell, and 10 more mark only the question cell -- and those ten
split with no tuning at all, because five have the `✅` at offset **1**
(`TC-c`, `C-8`, `C-10`, `C-14`, `C-17`, each reading `✅ **Closed <date>**`)
and five have it at 322, 1,288, 1,335, 3,282 and 28,437, marking a sub-item
inside a row that is plainly still open.  `hints()` carries that rule.

🟢 AND THE DISAGREEMENT IS KEPT AS A FINDING RATHER THAN RESOLVED BY GUESSING.
`L8` fires when the first cell says open and one of the other two says
closed.  量 on the live file at this tool's first run: **18 rows**, of which
16 are genuinely closed and never got their first-cell mark and 2 are the
prose case (`REL-0`, `REL-3`).  Sixteen one-character edits and two declared
exemptions -- not a heuristic.

  🔴 AND THE FIRST VERSION OF THIS PARAGRAPH WAS WRONG, IN THE SENTENCE IT WAS
  PROUDEST OF.  It said a hand adjudication run the same afternoon "was wrong
  on five" -- `TOOL-1`, `LOOP-1`, `REL-1`, `CITE-2`, `OPS-1` -- and that the
  offset rule "got all five right without reading a word of them".  量, on the
  rows themselves rather than on either verdict: **three of those five carry an
  explicit closure and the hand was right about them**:

      `TOOL-1`  🟢 **CLOSED 2026-09-02: `tools/xcheck.py`, 三條恆等式, 390 個檔**
      `LOOP-1`  🟢 **CLOSED 2026-09-02（第二十五段），而這一列的病因是錯的。**
      `REL-1`   🟢 **CLOSED 2026-09-01: the take EXISTS.** + the artefact's URL

  and two carry none, so the instrument was right about `CITE-2` and `OPS-1` --
  where the hand had inferred closure from a tool existing OUTSIDE the row,
  which is a different claim from the row being closed.

  **The mechanism is exact and it is this tool's, not the reader's**: `hints()`
  keyed on the CHARACTER `✅`, and those three rows spell their closure with
  the WORD `CLOSED` under a green circle.  A rule that reads one of the two
  spellings its own file uses is not an offset rule that beat a human; it is a
  narrower rule that agreed with one by luck on the rows where both spellings
  happen to coincide.  The token set below is the measured one, and the rows
  where a closure word is prose about a GATE are exempted by name.

  axis A -- the POPULATION.
      `cf`    one CARRIED-FORWARD ROW.  Derived from `PROGRESS.md` § Carried
              forward: every table row between that heading and the next
              `## `.  量 2026-09-16: 110 lines begin `|`, two of them are the
              header and the rule, so **108 rows**.
      `gate`  one GATE.  Derived from § Gate board's `Status` column (`✓`
              closed, `~` in progress, `·` not started, `⊘` declined) and
              CROSS-CHECKED against the `^## ...step list` section headers,
              which carry their own `CLOSED <date>`.  A gate the two sources
              disagree about is `L5` and not a silent pick.

  🔴 The population's own weakness, stated because it does not go away.  Both
  populations come from ONE file.  This is the record auditing itself, and it
  cannot see a debt this project incurred and never wrote down -- which is
  exactly the class the seventy-seventh segment's eighth audit method found by
  hand (four owner files, no checker able to see them).  `U6` is the control
  that keeps that from being a sentence nobody tests: the live file must yield
  at least one OPEN row owned by a LIVE gate, or the census refuses -- a census
  that finds everything closed has stopped reading.

  axis B -- the JOIN, per row.  An owning-gate cell is scanned for ids that
  are IN the gate population; the row's owner state is then:

      LIVE      at least one resolved owner is open.  Somebody will do it.
      ORPHAN    every resolved owner is closed, and no other cell holds a
                `✅`.  **Nobody will ever do this** -- the population `R1z`
                exists for.  量 44.
      ORPHAN?   every resolved owner is closed and an `L8` signal is present.
                Probably a row that is really finished.  Counted apart,
                because folding the two would inflate the debt by 12.
      DEAD      the cell names something gate-shaped that is in no population.
      NONE      the cell names nothing gate-shaped at all.
      SEGMENT   the cell defers to *any desk segment that touches X*.  Not a
                gate, not an orphan -- unscheduled, and counted as its own
                kind so it cannot hide inside either.

Usage
    cfcensus.py population        both populations with their provenance
    cfcensus.py census            the joined table and the counts
    cfcensus.py check             every check (L1..L10), and the doc's blocks
    cfcensus.py write             regenerate the doc's blocks, then check
    cfcensus.py ratchet           the finding count against `BASELINE`, which
                                  may move only in a commit that says so
    cfcensus.py --self-test       the controls

Exit
    0  clean
    1  a finding
    3  REFUSED -- an instrument could not be read, so nothing is reported.

⚠️ Python 3.12.  Not a preference: this tool imports `tools/spec-check.py`,
which carries an f-string with a backslash in its expression part, and that is
a SyntaxError at 3.10.  `CLAUDE.md` records the same trap one tool earlier.
"""

import argparse
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import isacensus                                            # noqa: E402
from isacensus import Refused, doc_block                    # noqa: E402

PROGRESS = os.path.join(ROOT, 'PROGRESS.md')

BEGIN = '<!-- cfcensus:%s begin -->'
END = '<!-- cfcensus:%s end -->'

# A gate-SHAPED token.  Still broader than `spec-check`'s `C12_STEP` even
# after `R1z-1` widened that one to `[RPS]` and `/`: this one has to match a
# bare GATE name in prose (`R6`, `P4b-gate`, `S0`), where `C12_STEP` matches
# a backticked STEP id.  🔄 2026-09-16: until `R1z-1`, `C12_STEP` was `R` plus
# a digit and could not see `P4b-1` or `S0` at all -- which is why the debt
# gate had to be called `R1z` and not `P5`.  Broader here means more false
# candidates, which is why an unresolved candidate is a REPORTED finding
# (`L2`) and never a silent drop.
GATE_SHAPE = re.compile(r'(?<![0-9A-Za-z-])([RPS]\d[0-9A-Za-z]*'
                        r'(?:[-/][0-9A-Za-z]+)*)(?![0-9A-Za-z-])')

# 🔄 2026-09-16, the measured spelling set.  This was the single character
# `✅` and that made the tool blind to three rows that spell a closure
# `🟢 **CLOSED <date>**` -- `TOOL-1`, `LOOP-1` and `REL-1`, the last of which
# carries the artefact's URL in the same sentence.  量 over all 108 rows: the
# `✅`-only rule sees 18 of the 21 rows that carry any closure spelling.
CLOSURE = re.compile(r'✅|CLOSED|Closed|已關|關了')

# 🔴 THE CHARACTER AND THE WORD ARE NOT THE SAME EVIDENCE, AND THE FILE SAYS SO.
# 量 2026-09-16 over every OPEN row: a `✅` deep in a QUESTION cell marks a
# sub-item five times out of five (offsets 322, 1,288, 1,335, 3,282, 28,437),
# so that character counts only at the head.  The WORD is the opposite -- all
# **eleven** occurrences in OPEN rows' question cells are row-level verdicts
# (`LOG-1` at 340, `LOOP-4` at 643, `TOOL-1` at 806, `ESC-1` at 963, `LOOP-1`
# at 1,143, and six `✅ **Closed` heads at offset 4), with **no** sub-item use.
# So the word counts anywhere and the character does not.  Eleven of eleven,
# zero counterexamples, and the asymmetry is read off the data rather than
# chosen -- which is the whole difference from the `✅`-only rule this replaces.
CLOSURE_WORD = re.compile(r'CLOSED|Closed')

# The owning-gate cell forms that are NOT a gate and say so.
NONE_WORDS = ('none', '無', "the owner's decision", '擁有者', 'closed')
SEGMENT_WORDS = ('任何一段', 'any desk segment', 'any segment', '的桌面段',
                 'the seating that', '下一次上機', '下一張卡片')

# 🔴 Declared exemptions from `L8`, by row id, each with the reason it is not
# a defect.  This is `spec-check`'s `C8C_EXEMPT` / `C10_EXEMPT` idiom and it
# carries the same obligation: `U9` re-runs `L8` with the exemptions OFF and
# goes red if an exempted row ever becomes clean, so the list cannot rot into
# a blanket.  量 2026-09-16: 13 `L8` rows, 2 exempted, 11 real.
L8_EXEMPT = {
    'REL-0': 'owner is the word `none`; the cell\'s ✅ is prose about a '
             'release decision, not about this row',
    'REL-3': 'owner is `none`, see `REL-0`; the ✅ is inside a sentence about '
             '`notes/kernel-build.md` §21.7',
    'XNUM-1': 'the owner cell\'s 關了 is `R5-11` the GATE closing, inside a '
              'recorded handover; the row is the one thing `R1z` exists to '
              'finish',
}
# 🔴 `GPIO-1` was in this list for one run and `L9` deleted it, which is the
# rot control doing its job on its first real use.  量: the token set above
# carries `CLOSED` and `Closed` and NOT lower-case `closed`, and `GPIO-1`'s is
# the lower-case prose spelling beside a gate id in a cell that also says
# *still not measured*.  Lower-case `closed` is excluded because the only
# instances in an OPEN row's owner cell are prose; `HC-1` and `LADDER-1` use it
# as a real closure and are already CLOSED in their first cell, so no `L8`
# question arises there.


# What each control asserts, so `--self-test`'s output says what ran rather
# than only how many did.  A dynamic name (`U7:<row>`, `U10:<alias>`) falls
# back to its own failure message.
CASE_WHAT = {
    'U0': 'the live file can be read at all',
    'U1': 'a row not closed by `|` is REFUSED, not half-parsed',
    'U2': 'a row with fewer fields than the table declares is REFUSED',
    'U3': 'the fixture parses, and its row count reconciles with its raw lines',
    'U4': 'the owner is the second-to-last field, on a row holding a pipe',
    'U5': 'an owner cell saying a GATE closed does not close the ROW',
    'U6': 'an all-closed table yields no live-owned row (the population guard)',
    'L1+': 'an open row owned only by a closed gate is reported',
    'L1-': 'an open row owned by an OPEN gate is not',
    'L2+': 'a row naming a gate that exists nowhere is reported',
    'L3+': 'an open row naming no gate at all is reported',
    'L3-': 'an any-desk-segment row is not read as having no owner',
    'L4+': 'a step list with no gate board row is reported',
    'L5+': 'a header/board disagreement about closure is reported',
    'L6+': 'an unmarked step row under a CLOSED gate is reported',
    'L6-': 'a properly marked closed step is not',
    'L7+': 'a non-step row inside a step list is reported as a phantom',
    'L7-': 'a clean step list reports no phantom',
    'L8+': 'closure recorded outside the first cell is reported',
    'L8x': 'a named exemption suppresses exactly that row',
    'L9+': 'an exemption naming a row that no longer exists is reported',
    'L9c': 'an exemption that no longer fires is reported, so it cannot rot',
    'L10+': 'two rows sharing an id are reported',
    'L10-': 'a table of distinct ids reports no duplicate',
    'U12=': 'the ratchet passes at its own baseline',
    'U12+': 'a GROWN debt is red',
    'U12-': 'a SHRUNK debt is red too -- an unrecorded payment is the defect',
    'U12live': 'the live file sits exactly at BASELINE, check by check',
    'U13': 'two checks moving in opposite directions is still red',
    'U12sig': 'the ratchet passes against a digest computed from the same run',
    'U12sig-': 'a WRONG digest with a right count is red',
    'U8': '`write` refuses a document with no block rather than creating one',
    'U9': "isacensus's shared `doc_block` reads a cfcensus-tagged block",
    'U14': "a finding's WHOLE SENTENCE, not its id prefix",
    'U14b': 'two rows trading places inside one check is red, though the '
            'count holds',
    'U15': 'a `⊘` DECLINED row is reported by nothing, end to end',
    'U15+': 'and the same row OPEN is reported, so `U15` is not vacuous',
    'U16': "`resolve`'s header branch resolves a gate the board lacks",
    'U17': "`gate_of_step`'s longest-prefix tie-break, with the section "
           'header deliberately defeated',
    'U18': 'a board row whose gate cell is unreadable is REFUSED',
    'U19': 'a board row whose Status cell is unreadable is REFUSED',
    'U20': 'two board rows for one gate are REFUSED',
    'U21': 'a `## ` heading inside a table is REFUSED',
    'U22': 'a second `## Carried forward` section is REFUSED',
    'U23': 'a row with a fourth column is REFUSED',
    'U24': 'an ESCAPED pipe in the owner cell is read whole, not split',
    'U25': "a two-column row is REFUSED -- the guard's real boundary",
    'U26': 'a renamed header cell is REFUSED, not read as a debt row',
}


# --------------------------------------------------------------------------
# reading PROGRESS.md
# --------------------------------------------------------------------------

def read_progress(path=None):
    p = path or PROGRESS
    if not os.path.exists(p):
        raise Refused('no PROGRESS.md at %s -- nothing to census' % p)
    with io.open(p, encoding='utf-8') as fh:
        return fh.read()


def section(text, heading):
    """The lines of one `## ` section, heading excluded, next `## ` exclusive.

    🔴 THE HEADING MUST OCCUR EXACTLY ONCE.  量 2026-09-16, adversarially: a
    SECOND `## Carried forward` section carrying its own table of debts leaves
    every number this tool prints byte-identical -- 108 rows, 85 findings,
    ratchet green -- because this function stops at the first `## ` after the
    first match and never looks again.  A whole second table of debts was
    invisible to every check, and it is the quietest corruption that pass
    found.  The prefix match stays (the heading may carry a trailing note) and
    is exactly why the count is asserted: a `## Carried forward (archive)`
    placed earlier would otherwise silently become the population.
    """
    lines = text.split('\n')
    hits = [i for i, ln in enumerate(lines)
            if ln.startswith('## ') and (ln.strip() == heading
                                         or ln.strip().startswith(heading))]
    if len(hits) > 1:
        raise Refused('`%s` heads %d sections (lines %s) -- this reader takes '
                      'the first, and every debt under the others is invisible '
                      'to every check in this tool'
                      % (heading, len(hits), [h + 1 for h in hits]))
    out, inside = [], False
    for ln in lines:
        if ln.startswith('## '):
            if inside:
                break
            inside = ln.strip() == heading or ln.strip().startswith(heading)
            continue
        if inside:
            out.append(ln)
    return out


# 🔴 A `## ` HEADING BETWEEN TWO TABLE ROWS TRUNCATES A POPULATION IN SILENCE.
# 量 2026-09-16, adversarially, on a pinned tree: one `## ` line inserted
# mid-table takes § Carried forward from 108 rows to 53 and the findings from
# 85 to 43 **with no complaint** -- because `cf_rows`'s reconciliation counts
# its raw lines from the section `section()` has already truncated, so that
# check can only ever certify itself.  The one signal is the ratchet firing as
# *the debt SHRANK ... lower BASELINE to 43*, whose remedy would record a parse
# loss as a payment.
#
# 🔴 THE RULE IS NOT "a heading with table rows on both sides".  量 2026-09-16:
# that catches `## Gate board`, whose section opens with a table and whose
# previous section ends with one -- the fixture and this file both.  The
# discriminator is that a legitimate table STARTS with a header row and a
# `|---|` rule row underneath it; a heading dropped into the middle of a table
# is followed by a row with no rule row after it.  量 with both controls: 0 of
# 146 tracked `.md` files flagged, and the deliberately corrupted fixture
# flagged at its inserted line.
PIPE_ROW = re.compile(r'^\s*\|')
RULE_ROW = re.compile(r'^\s*\|[\s:|-]+\|\s*$')


def heading_inside_table(text):
    """Every `## ` heading that lands inside a table rather than before one."""
    lines = text.split('\n')
    bad = []
    for i, ln in enumerate(lines):
        if not ln.startswith('## '):
            continue
        prev = next((lines[j] for j in range(i - 1, -1, -1)
                     if lines[j].strip()), '')
        nxt_i = next((j for j in range(i + 1, len(lines))
                      if lines[j].strip()), None)
        if nxt_i is None:
            continue
        after = lines[nxt_i + 1] if nxt_i + 1 < len(lines) else ''
        if (PIPE_ROW.match(prev) and PIPE_ROW.match(lines[nxt_i])
                and not RULE_ROW.match(after)):
            bad.append((i + 1, ln.strip()[:60]))
    return bad


def tables_in(lines):
    """The contiguous runs of `|` lines in a section -- one per markdown table.

    🔴 A section is not a table.  量 2026-09-16: `## Gate board` holds TWO --
    the board itself and the `| gate | actual | plan 小計 | ratio |`
    calibration table below it -- and the first version of this tool read the
    section as one table and refused on the second one's field count.  That
    refusal was correct and useless; the rule is to take the board's own run
    and say how many runs were seen.
    """
    runs, cur = [], []
    for ln in lines:
        if ln.startswith('|'):
            cur.append(ln)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


# Markdown's own escape: `\|` inside a cell is a literal pipe and not a cell
# boundary.  Declared once because two functions need the same rule.
PIPE_SPLIT = re.compile(r'(?<!\\)\|')


def split_row(ln):
    r"""(id_cell, question, owner_cell) for one table row, or None.

    🔴 THE SPLIT IS ON AN UNESCAPED PIPE AND THE COLUMN COUNT IS EXACT.  量
    2026-09-16: of the 110 table lines three carry a literal `|` inside the
    question cell -- shell pipelines in code spans, written `\|` because that
    is markdown's escape -- and splitting on a bare `|` gave those three rows
    6, 7 and 9 fields where the table declares three columns.  The old rule
    took the owner as the SECOND-TO-LAST field, which is right on those three
    by luck and cannot be checked.  Splitting on `(?<!\\)\|` makes all 110
    lines exactly five fields -- 量 twice, by the escape and by masking
    backticked spans, 110/110 both ways -- so the count can be ASSERTED
    instead of worked around.

    🔴 What the assertion buys, 量 adversarially on a pinned tree: an
    unescaped `|` added inside an OWNER cell silently re-read the owner and
    moved the findings 85 → 84 with nothing reported; a fourth column added to
    one row moved `L1` 44→43 and `L3` 9→10 for an unchanged total of 85 with
    the ratchet green.  Both are refusals now.  `board_gates` has asserted its
    own field count since it was written and this table had no check at all.
    """
    if not ln.startswith('|'):
        return None
    if not ln.rstrip().endswith('|'):
        raise Refused('row does not end with `|`, so the cell boundaries are '
                      'not knowable: %r' % ln[:80])
    a = PIPE_SPLIT.split(ln)
    if len(a) != 5:
        raise Refused('row splits into %d cells against the three this table '
                      'declares -- an unescaped `|` inside a cell, or a column '
                      'only this row has: %r' % (len(a) - 2, ln[:80]))
    return (a[1].strip(), a[2].strip(), a[-2].strip())


ID_RX = re.compile(r'`?([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)`?')

# The gate board's first cell is `**NAME**` plus optional marks.  量
# 2026-09-16: all 20 rows, and NAME is taken verbatim -- `R2a/b/d` and
# `P4b-gate` are gate names that `ID_RX` truncates at the `/` and would
# silently rename.
BOARD_NAME = re.compile(r'^\*\*([^*]+)\*\*')

# A `## ...step list` header names a gate that the board may hold under a
# shorter name.  Declared, because a guess here renames a gate.  `U10` is the
# control: every alias target must be a board row.
GATE_ALIAS = {
    'R1-pub + R2c': 'R1-pub',   # 量: the board row is `R1-pub`; `R2c` was
                                # folded into it on 2026-09-11 and never got
                                # a row of its own.
}


def cf_rows(text):
    """The § Carried forward population, with a count that must reconcile."""
    runs = tables_in(section(text, '## Carried forward'))
    if len(runs) != 1:
        raise Refused('§ Carried forward holds %d tables, not one -- a census '
                      'that takes the first would drop the rest silently'
                      % len(runs))
    raw = runs[0]
    # 🔴 THE HEADER IS ASSERTED, NOT RECOGNISED BY SHAPE.  量 2026-09-16,
    # adversarially: renaming the header's first cell `#` → `Item` makes the
    # header row itself a debt row, because the skip test below keys on the
    # literal `#`.  The three column names are what this parser's field
    # positions MEAN, so they are the thing to check.
    head = [c.strip() for c in PIPE_SPLIT.split(raw[0])]
    if head[1:4] != ['#', 'Question', 'Owning gate']:
        raise Refused('§ Carried forward\'s header reads %r, not '
                      '`| # | Question | Owning gate |` -- this parser\'s '
                      'column positions are named by that header'
                      % (head[1:4],))
    rows, skipped = [], 0
    for ln in raw:
        got = split_row(ln)
        if got is None:                                     # unreachable
            continue
        idc, question, owner = got
        if set(idc) <= set('-: ') or idc == '#':            # rule / header
            skipped += 1
            continue
        m = ID_RX.match(idc)
        if not m:
            raise Refused('a § Carried forward row has no id in its first '
                          'cell: %r' % idc[:60])
        rows.append({
            'id': m.group(1),
            'id_cell': idc,
            'question': question,
            'owner_cell': owner,
            'state': ('CLOSED' if '✅' in idc
                      else 'DECLINED' if '⊘' in idc else 'OPEN'),
        })
    if len(rows) + skipped != len(raw):
        raise Refused('parsed %d rows + %d header lines against %d raw `|` '
                      'lines -- rows were lost silently'
                      % (len(rows), skipped, len(raw)))
    if not rows:
        raise Refused('§ Carried forward yielded no rows -- the heading moved '
                      'or the table shape changed')
    return rows, len(raw), skipped


def board_gates(text):
    """{gate: status} from § Gate board's own `Status` column.

    🔴 THE COLUMN IS FOUND BY ITS OWN HEADER AND THE FIELD COUNT IS ASSERTED.
    量 2026-09-16: the first version of this function read `cells[6]` because
    that index had been measured with `awk`, whose `split()` is 1-based where
    Python's is 0-based -- so it read the EVIDENCE column, found `·` in
    `bench/2026-08-30/ · QJ.log` and `⊘` in `S0b`'s prose, and reported four
    gates of twenty with `S0` and `R1h` and `R4` all wrong.  It did not crash
    and it printed a plausible table.  The header lookup below cannot make
    that mistake, and the count assertion is what stops a row with an embedded
    `|` from shifting the column silently.
    """
    runs = tables_in(section(text, '## Gate board'))
    if not runs:
        raise Refused('§ Gate board holds no table')
    idx, nf, out = None, None, {}
    for ln in runs[0]:
        a = ln.split('|')
        if idx is None:
            head = [c.strip() for c in a]
            if 'Status' not in head:
                raise Refused('§ Gate board\'s first table row is not its '
                              'header (no `Status` column): %r' % ln[:80])
            idx, nf = head.index('Status'), len(a)
            continue
        if set(a[1].strip()) <= set('-: *'):                # the rule row
            continue
        if len(a) != nf:
            raise Refused('a § Gate board row has %d fields against the '
                          'header\'s %d, so the Status column has moved on '
                          'that row: %r' % (len(a), nf, ln[:80]))
        m = BOARD_NAME.match(a[1].strip())
        if not m:
            # 🔴 WAS AN UNCONDITIONAL `continue`.  量 2026-09-16,
            # adversarially: strip the `**bold**` from one board row's gate
            # cell and that gate leaves the population entirely -- every row
            # owned by it is then reported `L2 …: no gate by that name exists
            # on the board`, **while the board row is right there**, and the
            # findings go 85 → 89.  A parser that drops a row it cannot read
            # goes on to blame the rows that name it.
            raise Refused('a § Gate board row\'s first cell is not '
                          '`**NAME**`, so its gate would leave the population '
                          'and every row owning it would be reported as '
                          'naming a gate that does not exist: %r'
                          % (a[1].strip()[:60],))
        st = a[idx]
        state = ('CLOSED' if '✓' in st else
                 'LIVE' if '~' in st else
                 'DECLINED' if '⊘' in st else
                 'NOTSTARTED' if '·' in st else None)
        if state is None:
            # 🔴 The same drop through the other door: blanking one `Status`
            # cell had the identical 85 → 89 effect.
            raise Refused('§ Gate board row `%s` has an unreadable `Status` '
                          'cell (%r) -- the gate would leave the population '
                          'and its rows would be reported as orphans of a '
                          'gate that does not exist'
                          % (m.group(1).strip(), st.strip()[:30]))
        name = m.group(1).strip()
        if name in out:
            # 🔴 `L10` exists for two ROWS sharing an id and there was no
            # equivalent here.  量: two board rows for `R5` disagreeing about
            # its status -- last wins, in silence, findings 85 → 77.
            raise Refused('§ Gate board holds two rows for `%s` -- the later '
                          'silently overwrites the earlier, which is `L10`\'s '
                          'defect on the other table' % name)
        out[name] = state
    if not out:
        raise Refused('§ Gate board yielded no gate -- the Status column moved')
    return out


def header_gates(text):
    """{gate: (closed?, header name)} from the `^## ...step list` headers.

    The SECOND source for gate closure.  `L5` requires it to agree with the
    board; a gate whose header says CLOSED while the board says otherwise is
    a file disagreeing with itself, which is the shape `C12`'s hole ② has.

    🔴 Closure is `CLOSED` in either case.  量 2026-09-16: seven of ten
    headers say `✅ CLOSED <date>` and two -- `R2a/b/d` and `R1-gate` -- say
    lower-case `closed` with no tick.  A rule keyed on `✅ CLOSED` reads those
    two as open, which is four of the nine unmarked steps left behind.
    """
    out = {}
    for ln in text.split('\n'):
        # 🔴 case-insensitive: the ACTIVE gate's section is `## Step list for
        # the active gate — `R1z`` with a capital S, and every closed gate's
        # is `` ## `R5`'s step list ``.  量 2026-09-16: a case-sensitive test
        # made the one live gate the only one this function could not see,
        # which is the half of the population that matters.
        if not ln.startswith('## ') or 'step list' not in ln.lower():
            continue
        m = re.search(r'`([^`]+)`', ln)
        if not m:
            continue
        name = m.group(1).strip()
        out[GATE_ALIAS.get(name, name)] = ('closed' in ln.lower(), name)
    if not out:
        raise Refused('no `## ...step list` header found -- the section '
                      'convention changed')
    return out


def step_state(text):
    """{step id: closed?} through `spec-check`'s OWN parser, not a copy.

    🟢 Importing rather than restating is deliberate and it buys a second
    thing besides one owner for the rule: when `R1z-1` makes
    `progress_step_state` stricter, this census gets stricter in the same
    commit and the two tools cannot drift.  `tools/flashmap.py` importing
    `flashwin.overlaps_forbidden` is this repository's precedent.
    """
    import importlib.machinery
    import importlib.util
    p = os.path.join(HERE, 'spec-check.py')
    if not os.path.exists(p):
        raise Refused('spec-check.py not found -- cannot resolve step state')
    loader = importlib.machinery.SourceFileLoader('speccheck_mod', p)
    spec = importlib.util.spec_from_loader('speccheck_mod', loader)
    sc = importlib.util.module_from_spec(spec)
    try:
        loader.exec_module(sc)
    except SyntaxError as e:
        raise Refused('spec-check.py would not import (it needs Python 3.12; '
                      'this is %d.%d): %r'
                      % (sys.version_info[0], sys.version_info[1], e))
    except Exception as e:
        raise Refused('spec-check.py would not import: %r' % (e,))
    # 🔴 TWO QUESTIONS, ASKED SEPARATELY.  `marked` is *does this step row
    # carry its own ✅*; `state` is *is this step closed by anything*, which
    # from 2026-09-16 includes its section header saying CLOSED.  `L6`'s
    # subject is the DATA -- nine rows of two closed gates with no mark -- and
    # asking the wider question would have made `L6` go silent the hour
    # `spec-check` learned to read the header, with the rows unchanged.
    return (sc.progress_step_state(text),
            sc.progress_step_state(text, header_closes=False),
            sc.progress_step_owner(text))


def population(text=None):
    text = read_progress() if text is None else text
    bad = heading_inside_table(text)
    if bad:
        raise Refused('a `## ` heading sits inside a table (%s) -- it '
                      'truncates whatever section it lands in, and this '
                      'tool\'s own row reconciliation counts from the '
                      'truncated section, so the loss would be certified '
                      'rather than reported'
                      % '; '.join('line %d: %s' % b for b in bad))
    rows, raw, skipped = cf_rows(text)
    board = board_gates(text)
    hdr = header_gates(text)
    steps, marked, owner = step_state(text)
    return {'rows': rows, 'raw': raw, 'skipped': skipped, 'board': board,
            'header': hdr, 'steps': steps, 'marked': marked,
            'step_owner': owner, 'text': text}


# --------------------------------------------------------------------------
# the join
# --------------------------------------------------------------------------

def gate_of_step(sid, board, owner=None):
    """The board gate a step id belongs to, or None.

    🔴 THE SECTION HEADER FIRST, THE PREFIX ONLY AS A FALLBACK.  量
    2026-09-16: the prefix rule needed `R1g-*` special-cased to `R1-gate`, and
    it still handed `P4b-1`…`P4b-4` to `P4b`, a gate that has not started,
    rather than to `P4b-gate`, which closed on 2026-09-01 -- so four unmarked
    step rows went unreported by `L6` and the miss looked like clean data.
    `spec-check.progress_step_owner` reads the header the rows sit under,
    which is the file's own answer; `GATE_ALIAS` maps a composite header such
    as `R1-pub + R2c` onto its board row.
    """
    if owner and sid in owner:
        g = GATE_ALIAS.get(owner[sid], owner[sid])
        if g in board:
            return g
    best = None
    for g in board:
        if sid == g or sid.startswith(g + '-'):
            if best is None or len(g) > len(best):
                best = g
    return best


def resolve(owner_cell, board, hdr, steps, sowner=None):
    """(resolved, unresolved) -- gate ids in the cell, split by whether the
    populations know them.  Strikethrough ids are dropped: `~~R3~~ → R1h` is a
    handover, and the struck half is history, not an owner."""
    cell = re.sub(r'~~.*?~~', '', owner_cell)
    seen, resolved, unresolved = set(), [], []
    for m in GATE_SHAPE.finditer(cell):
        tok = m.group(1)
        if tok in seen:
            continue
        seen.add(tok)
        if tok in board:
            resolved.append((tok, board[tok] == 'CLOSED', 'board'))
        elif tok in hdr:
            resolved.append((tok, hdr[tok][0], 'header'))
        elif tok in steps:
            g = gate_of_step(tok, board, sowner)
            shut = steps[tok] or (g is not None and board[g] == 'CLOSED')
            resolved.append((tok, shut, 'step'))
        else:
            unresolved.append(tok)
    return resolved, unresolved


def owner_kind(row, board, hdr, steps, sowner=None):
    """One of LIVE / ORPHAN / ORPHAN? / DEAD / SEGMENT / NONE, with evidence."""
    cell = row['owner_cell']
    resolved, unresolved = resolve(cell, board, hdr, steps, sowner)
    low = cell.lower()
    if resolved:
        live = [t for (t, shut, _) in resolved if not shut]
        if live:
            return 'LIVE', ';'.join(live), resolved, unresolved
        shut = ';'.join(t for (t, _, _) in resolved)
        # 🔴 A NAMED EXEMPTION MUST ALSO BLOCK THE DEMOTION.  量 2026-09-16:
        # widening the closure spellings moved `XNUM-1` to `ORPHAN?`, i.e.
        # *probably finished* -- the row this gate exists to finish, whose
        # owner cell says `R5-11` 關了 about the GATE.  Suppressing only its
        # `L8` finding while letting the same signal reclassify it is the
        # mislabel the exemption was written to prevent, one layer down.
        if (row['id'] not in L8_EXEMPT
                and {'owner', 'question-head'} & set(hints(row))):
            return 'ORPHAN?', shut, resolved, unresolved
        return 'ORPHAN', shut, resolved, unresolved
    if any(w in cell or w in low for w in SEGMENT_WORDS):
        return 'SEGMENT', '', resolved, unresolved
    if unresolved:
        return 'DEAD', ';'.join(unresolved), resolved, unresolved
    if any(w in low for w in NONE_WORDS) or '無' in cell:
        return 'NONE', '', resolved, unresolved
    return 'NONE', '', resolved, unresolved


def hints(row):
    """The closure signals this table uses that are NOT its declared one.

    🔴 THIS TABLE RECORDS "CLOSED" IN THREE PLACES AND DECLARES ONE.  量
    2026-09-16 over all 108 rows: 17 carry `✅` in the FIRST cell, which is
    the convention; 13 more carry it only in the OWNING-GATE cell; and 10
    more carry it only in the QUESTION cell.  The last ten split cleanly and
    the split needs no tuning -- five have the `✅` at offset **1**, i.e. the
    question cell opens with it (`TC-c`, `C-8`, `C-10`, `C-14`, `C-17`, each
    reading `✅ **Closed <date>**`), and the other five have it at 322, 1,288,
    1,335, 3,282 and 28,437, where it marks a sub-item inside a live row
    (`CAPD-1`, `OPS-1`, `CITE-2`, `UP-AUD-1`, `CI-5`).  **Offset 1 or not**
    is the rule; a character window would be a parameter fitted to ten points.
    """
    out = []
    if CLOSURE.search(row['owner_cell']):
        out.append('owner')
    q = row['question'].lstrip()
    if q.startswith('✅') or CLOSURE.match(q) or CLOSURE_WORD.search(q):
        out.append('question-head')
    elif CLOSURE.search(q):
        out.append('question-body')
    return out


def census(pop=None):
    pop = population() if pop is None else pop
    board, hdr, steps = pop['board'], pop['header'], pop['steps']
    out = []
    for r in pop['rows']:
        kind, ev, resolved, unresolved = owner_kind(
            r, board, hdr, steps, pop['step_owner'])
        d = dict(r)
        d['hints'] = hints(r)
        d['kind'] = kind
        d['owner_ev'] = ev
        d['unresolved'] = unresolved
        d['l8'] = (r['state'] == 'OPEN'
                   and bool({'owner', 'question-head'} & set(d['hints'])))
        out.append(d)
    return out


# --------------------------------------------------------------------------
# the checks
# --------------------------------------------------------------------------

def check(pop=None, exempt=None):
    """Findings.  Empty is clean.  `exempt=False` turns `L8`'s list off."""
    pop = population() if pop is None else pop
    ex = L8_EXEMPT if exempt is None else (exempt or {})
    rows = census(pop)
    board, hdr = pop['board'], pop['header']
    f = []

    # ---- direction 1: rows -> gates -------------------------------------
    for r in rows:
        if r['state'] != 'OPEN':
            continue
        if r['kind'] == 'ORPHAN':
            f.append('L1 %s: open, and every owner it names is a CLOSED gate '
                     '(%s) -- nobody will do it' % (r['id'], r['owner_ev']))
        elif r['kind'] == 'DEAD':
            f.append('L2 %s: names %s as its owner and no gate by that name '
                     'exists on the board or in a step list'
                     % (r['id'], r['owner_ev']))
        elif r['kind'] == 'NONE':
            f.append('L3 %s: open and names no owning gate -- the table\'s '
                     'own rule calls that a bug in the table'
                     % (r['id'],))
        if r['l8'] and r['id'] not in ex:
            f.append('L8 %s: the first cell does not say ✅ and the %s cell '
                     'does -- the table records closure in a place it does '
                     'not declare'
                     % (r['id'],
                        ' and '.join(h for h in r['hints']
                                     if h in ('owner', 'question-head'))))

    # ---- direction 2: gates -> rows -------------------------------------
    for g, (shut, name) in sorted(hdr.items()):
        if g not in board:
            f.append('L4 %s: has a `## ...step list` section (header names '
                     '`%s`) and no row on the gate board' % (g, name))
            continue
        bshut = board[g] == 'CLOSED'
        if shut != bshut:
            f.append('L5 %s: the step-list header says %s and the gate board '
                     'says %s' % (g, 'CLOSED' if shut else 'open',
                                  'CLOSED' if bshut else 'open'))
    # a gate may legitimately have no step list (`R0`, `S0`, `R6`..`P4b`); that
    # is reported by `population` and is not a finding.

    # ---- direction 2b: a closed gate's steps must be marked closed -------
    steps, unmarked = pop['marked'], {}
    for sid, shut in steps.items():
        if shut:
            continue
        g = gate_of_step(sid, board, pop['step_owner'])
        if g and board[g] == 'CLOSED':
            unmarked.setdefault(g, []).append(sid)
    for g in sorted(unmarked):
        f.append('L6 %s: the gate board says CLOSED and %d of its step rows '
                 'carry no ✅ of their own (%s) -- a reader of the step table '
                 'sees finished work with no mark on it'
                 % (g, len(unmarked[g]), ' '.join(sorted(unmarked[g]))))

    # ---- L10: one id, one row -------------------------------------------
    # 量 2026-09-16, by a second parser run beside this one: `REL-3` occupies
    # two rows and `CFG-2` occupies two, one open and one closed.  A debt
    # table that gives two different debts the same name is `NET-14`'s
    # collision inside the record rather than inside `SPEC.md`, and a reader
    # who greps for the id gets whichever row comes first.
    byid = {}
    for r in rows:
        byid.setdefault(r['id'], []).append(r)
    for k in sorted(byid):
        if len(byid[k]) > 1:
            f.append('L10 %s: %d rows share this id (%s) -- two debts with '
                     'one name, and every lookup keyed on it reads whichever '
                     'comes first'
                     % (k, len(byid[k]),
                        ', '.join('%s/%s' % (x['state'], x['kind'])
                                  for x in byid[k])))

    # ---- L7: a step id that is really a gate name is a phantom ----------
    # 量 2026-09-16: `progress_step_state` returns `R9`, because
    # `PROGRESS.md:1036` -- `| **`cr6c` for `R9`** 🆕 |`, a carried-forward
    # row sitting INSIDE `R3`'s step-list section -- opens `| **`` and so
    # passes its row guard.  A `Next after this` row that merely mentions
    # `` `R9` `` therefore satisfies `C12` today.  The census can see it
    # because it knows the gate names and `spec-check` does not.
    for sid in sorted(steps):
        if sid in board:
            f.append('L7 %s: `progress_step_state` returns it as a STEP and '
                     'the gate board holds it as a GATE -- a non-step row '
                     'inside a step-list section is being read as a step'
                     % (sid,))

    # ---- L9: the exemption list may not rot -----------------------------
    # 🔴 ANY row with the id, not the first.  量 2026-09-16: `REL-3` occupies
    # two rows -- one CLOSED, one OPEN -- and a `hit[0]` lookup read the
    # closed one and declared the exemption dead.  A duplicate id does not
    # only confuse a reader; it silently re-points every lookup keyed on it,
    # which is `L10`'s whole cost demonstrated inside this function.
    for k in sorted(ex):
        hit = [r for r in rows if r['id'] == k]
        if not hit:
            f.append('L9 %s is exempted from L8 and is not a row of this '
                     'table any more -- the exemption outlived its subject'
                     % (k,))
        elif not any(r['l8'] for r in hit):
            f.append('L9 %s is exempted from L8 and no longer triggers it on '
                     'any of its %d row(s) -- the exemption is dead and must '
                     'be deleted' % (k, len(hit)))
    return f


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def render_debt(rows):
    """The population, as a DERIVED CLASSIFICATION and nothing else.

    🔴 The question text is deliberately NOT reproduced here.  § Carried
    forward is the owner of what each debt asks; a generated block that
    repeated it would give every one of these rows a second owner inside the
    same file, which is house rule 1 broken by the tool written to enforce
    house rule 1.  What this block adds is the join the table cannot state
    about itself: which gate each row named, and whether that gate is gone.

    ⚠️ **No line numbers either.** `CITE-2` is a row of this very table and
    what it says is that `FILE:NNN` into a live owner file is a structurally
    unmaintainable citation; a generated block that numbered its own source's
    lines would commit that defect inside the instrument that reports it.
    """
    out = ['| # | kind | owner named |', '|---|---|---|']
    for r in rows:
        if r['state'] != 'OPEN' or r['kind'] == 'LIVE':
            continue
        out.append('| `%s` | %s | %s |'
                   % (r['id'], r['kind'], r['owner_ev'] or '—'))
    return '\n'.join(out)


def render_counts(rows, pop):
    k = {}
    for r in rows:
        key = r['state'] if r['state'] != 'OPEN' else r['kind']
        k[key] = k.get(key, 0) + 1
    order = ['LIVE', 'SEGMENT', 'ORPHAN', 'ORPHAN?', 'DEAD', 'NONE',
             'CLOSED', 'DECLINED']
    out = ['| what | n | meaning |', '|---|---:|---|']
    mean = {
        'LIVE': 'open, and a gate that is still open owns it',
        'SEGMENT': 'open, deferred to *any segment that touches X* — '
                   'unscheduled, not orphaned',
        'ORPHAN': '🔴 open, and every gate it names is CLOSED — **nobody '
                  'will do it**',
        'ORPHAN?': 'open by its first cell, owner closed, and a ✅ sits in the '
                   'owning-gate cell or opens the question — probably an '
                   '`L8` row that is finished and never marked',
        'DEAD': '🔴 names a gate that exists nowhere in this file',
        'NONE': 'open and names no gate at all',
        'CLOSED': 'first cell says ✅',
        'DECLINED': 'first cell says ⊘',
    }
    for key in order:
        if key in k:
            out.append('| %s | %d | %s |' % (key, k[key], mean[key]))
    out.append('| **total** | **%d** | rows parsed, reconciled against %d raw '
               'table lines minus %d header lines |'
               % (len(rows), pop['raw'], pop['skipped']))
    l8 = sum(1 for r in rows if r['l8'])
    out.append('| `L8` | %d | closure recorded somewhere this table does not '
               'declare — the owning-gate cell, or the head of the question; '
               '%d exempted by name |' % (l8, len(L8_EXEMPT)))
    return '\n'.join(out)


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def report_population():
    pop = population()
    print('=== population `cf` — PROGRESS.md § Carried forward ===')
    print('%d rows (%d raw `|` lines, %d header lines)'
          % (len(pop['rows']), pop['raw'], pop['skipped']))
    st = {}
    for r in pop['rows']:
        st[r['state']] = st.get(r['state'], 0) + 1
    print('  first-cell state: ' + ', '.join('%s %d' % (k, st[k])
                                             for k in sorted(st)))
    print()
    print('=== population `gate` — § Gate board, cross-checked ===')
    for g in sorted(pop['board']):
        h = pop['header'].get(g)
        print('  %-12s board=%-10s header=%s'
              % (g, pop['board'][g],
                 '—' if h is None else ('CLOSED' if h[0] else 'open')))
    extra = [g for g in pop['header'] if g not in pop['board']]
    if extra:
        print('  step lists with no board row: ' + ' '.join(sorted(extra)))
    print()
    print('=== steps, through spec-check\'s own progress_step_state ===')
    print('  %d step ids, %d marked closed'
          % (len(pop['steps']), sum(1 for v in pop['steps'].values() if v)))
    return 0


def report_census():
    pop = population()
    rows = census(pop)
    print(render_counts(rows, pop))
    print()
    print(render_debt(rows))
    return 0


def report_check():
    pop = population()
    f = check(pop)
    rows = census(pop)
    live = [r for r in rows if r['state'] == 'OPEN' and r['kind'] == 'LIVE']
    if not live:
        raise Refused('no OPEN row is owned by a LIVE gate -- a debt census '
                      'that finds everything closed has stopped reading')
    for ln in f:
        print('FAIL ' + ln)
    print('%d row(s), %d finding(s), %d live-owned'
          % (len(rows), len(f), len(live)))
    return 1 if f else 0


# 🔴 THE RATCHET.  量 2026-09-16, `R1z-0`, before any fix: 85 findings on the
# committed file -- 44 `L1`, 11 `L2`, 9 `L3`, 16 `L8`, 2 `L6`, 2 `L10`, 1 `L7`.
#
# Why a ratchet and not a gate.  A gate would be RED on every run until `R1z`
# closes, and a step that is always red trains a reader to stop reading reds --
# which is this repository's own recorded objection to a local sweep that ends
# in two expected failures every time.  Why not simply leave `check` out of CI:
# that is `CI-3`, a row of the very table this tool censuses -- *nothing
# notices a tool with a `--self-test` that is never in CI*.
#
# So the number moves in one direction and it moves ON PURPOSE.  Above the
# baseline is a debt that grew; BELOW it is a debt that was paid without being
# recorded, and that is red too, because a payment nobody writes down is how
# this table came to have 44 orphans.  `T13b`'s shape: an exemption that stops
# being load-bearing must force its own removal.
# 🔴 PER CHECK, NOT A TOTAL -- and the total is what this was until it was
# caught by its own first real event.  量 2026-09-16, one hour after the
# ratchet landed: `R1z-1` made `spec-check` stop returning the phantom step
# `R9` (`L7` 1 → 0) and, in the same edit, made the `P` series visible so a
# fifth unmarked step family appeared (`L6` 2 → 3).  **The total stayed at 85
# and the ratchet went green**, on a run in which two different things moved.
# That is this repository's own recorded trap -- a pair of wrong numbers is
# self-consistent as long as the difference is right -- reproduced inside the
# instrument written to prevent it.
BASELINE = {'L1': 42, 'L2': 11, 'L3': 9, 'L6': 4, 'L8': 19, 'L10': 2}
# 🔴 A COUNT PER CHECK IS STILL NOT ENOUGH, AND THE ADVERSARIAL PASS SAID SO
# BEFORE THIS LINE EXISTED: *a mutant that moves two rows in opposite
# directions WITHIN `L1` is still invisible*.  The dict above is HOW MANY the
# instrument reported; the one below is WHICH ROWS -- sha256 over that check's
# sorted row ids, first eight hex.  Two rows trading places inside one check
# moves the digest and not the count.  `U14b` is the control, and this is the
# third layer of one lesson this file already carries twice: a scalar total,
# then a per-check count, now a per-check identity.
BASELINE_SIG = {'L1': 'b0e76a66', 'L10': 'c56612d3', 'L2': '21f32778',
                'L3': '7f50eda0', 'L6': 'b86a38d5', 'L8': 'e9fe5859'}
# 🔄 2026-09-16, later the same segment: `L1` 44 → 42 and `L8` 16 → 19, and
# **both moves are the instrument getting less wrong rather than a debt
# moving.**  Teaching `hints()` the WORD `CLOSED` alongside the character `✅`
# made three rows that had always been closed stop being reported as *nobody
# will do it*: `TOOL-1` and `LOOP-1` (`🟢 **CLOSED 2026-09-02**` mid-question)
# and `REL-1` (`🟢 **CLOSED 2026-09-01: the take EXISTS.**` with the artefact's
# URL, in the owner cell).  The ratchet refused the run until this line moved,
# which is what it is for: the debt did not shrink, the measurement of it
# changed, and the commit has to say which.
# 量 2026-09-16, `R1z-1`, 86 findings.  `L6` moved 2 → 4 inside that step and
# BOTH moves were the checker getting stricter rather than a debt appearing:
# `P4a`'s five step rows became visible when the id class stopped being
# `R`-only, and `P4b-gate`'s four arrived when a step stopped being attributed
# to a gate by its PREFIX -- `P4b-1` had been handed to `P4b`, which has not
# started, instead of to `P4b-gate`, which closed on 2026-09-01.  Eighteen
# unmarked step rows across four closed gates, where the record said nine.


def finding_sig(f):
    """{check: (count, 8-hex digest over its sorted row ids)}."""
    by = {}
    for ln in f:
        p = ln.split()
        by.setdefault(p[0], []).append(p[1].rstrip(':') if len(p) > 1 else '')
    return {k: (len(v),
                hashlib.sha256('\n'.join(sorted(v)).encode('utf-8'))
                .hexdigest()[:8])
            for k, v in by.items()}


def ratchet(pop=None, baseline=None, exempt=None, sig=None):
    # 🔴 A HAND BASELINE MAY NOT INHERIT THE LIVE DIGESTS.  量, on this
    # change's own first run: `U12=` went red because it passes
    # `baseline={'L1': 1}` for a two-row fixture and the digest defaulted to
    # the live file's, so the control that asserts *the ratchet passes at its
    # own baseline* was comparing a fixture's rows against `PROGRESS.md`'s.
    # A caller that supplies counts and not ids is testing counts.
    BASE = dict(BASELINE if baseline is None else baseline)
    SIG = (dict(BASELINE_SIG) if sig is None and baseline is None
           else dict(sig or {}))
    f = check(pop, exempt=exempt)
    got = finding_sig(f)
    by = {k: v[0] for k, v in got.items()}
    swapped = [(k, SIG[k], got[k][1]) for k in sorted(set(SIG) & set(got))
               if BASE.get(k, 0) == by.get(k, 0) and SIG[k] != got[k][1]]
    keys = sorted(set(BASE) | set(by))
    moved = [(k, BASE.get(k, 0), by.get(k, 0))
             for k in keys if BASE.get(k, 0) != by.get(k, 0)]
    detail = ' '.join('%s %d' % (k, by[k]) for k in sorted(by))
    if swapped and not moved:
        print('FAIL the debt did not move and WHICH ROWS did:')
        for k, want, now in swapped:
            print('     %-4s count %-3d unchanged, ids %s -> %s'
                  % (k, by[k], want, now))
        print('     %s' % detail)
        print('     One row left this check and another joined it.  A count '
              'cannot see that, which is the whole reason the digest is '
              'here.  Move `BASELINE_SIG` in the same commit and say which '
              'rows moved.')
        return 1
    if moved:
        grew = [m for m in moved if m[2] > m[1]]
        print('FAIL the debt moved and `BASELINE` did not:')
        for k, want, got in moved:
            print('     %-4s baseline %-3d now %-3d   %s'
                  % (k, want, got, 'GREW' if got > want else 'shrank'))
        print('     %s' % detail)
        if grew:
            print('     A new row with no live owner is a new debt.  Give it '
                  'an owner, or raise its `BASELINE` entry in the commit that '
                  'adds the row and say why.')
        else:
            print('     Lower the entry in the same commit as the fix.  A '
                  'payment nobody records is how this table reached 44 '
                  'orphans.')
        return 1
    print('  ok  %d finding(s) in %d check(s), every one exactly the '
          'baseline, and in every check the same rows' % (len(f), len(by)))
    print('      %s' % detail)
    print('      ids %s' % ' '.join('%s/%s' % (k, got[k][1])
                                    for k in sorted(got)))
    return 0


def write_blocks(path=None):
    p = path or PROGRESS
    with io.open(p, encoding='utf-8') as fh:
        text = fh.read()
    pop = population(text)
    rows = census(pop)
    body = {'counts': render_counts(rows, pop), 'debt': render_debt(rows)}
    for tag, new in body.items():
        b, e = BEGIN % tag, END % tag
        if b not in text or e not in text:
            raise Refused('%s has no cfcensus:%s block -- `write` regenerates '
                          'blocks, it does not create the section' % (p, tag))
        head, rest = text.split(b, 1)
        _, tail = rest.split(e, 1)
        text = head + b + '\n' + new + '\n' + e + tail
    tmp = p + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    os.replace(tmp, p)
    return 0


def report_write():
    write_blocks()
    print('blocks regenerated')
    return report_check()


# --------------------------------------------------------------------------
# the controls
# --------------------------------------------------------------------------

def _fixture(rows_md=None, board_md=None, hdr=None, steps_md=None):
    """A minimal PROGRESS.md with the four structures this tool reads."""
    rows_md = rows_md if rows_md is not None else [
        '| `A-1` 🆕 | ask one | `R6` |',
        '| `B-1` ✅ | ask two | `R5` |',
    ]
    board_md = board_md if board_md is not None else [
        '| **R5** | closed thing | 1 | 1 | **`✓`** | ev |',
        '| **R6** | open thing | 1 | — | `·` | |',
    ]
    hdr = hdr if hdr is not None else ["## `R5`'s step list — ✅ CLOSED 2026-01-01"]
    steps_md = steps_md if steps_md is not None else [
        '| **`R5-0`** ✅ | a | b | c | d |',
    ]
    return '\n'.join(
        ['# P', ''] + hdr + [''] + steps_md + ['']
        + ['## Gate board', '', '| Gate | What | Est. | Actual | Status | Ev |',
           '|---|---|---:|---:|:---:|---|'] + board_md + ['']
        + ['## Carried forward', '', '| # | Question | Owning gate |',
           '|---|---|---|'] + rows_md + ['', '## Corrections', ''])


def self_test():
    """The controls.

    🔴 THE OUTPUT SHAPE IS PART OF THE CONTRACT, not a preference.
    `tools/ci-census.py`'s `OK_RE` is `^ {2}ok\\s{2,}(.*)$` -- exactly two
    leading spaces -- and it counts those lines, not a summary.  A suite that
    prints only `33 case(s), 0 failure(s)` is read as `ran 0/33` and takes the
    census red on the next push.  `CLAUDE.md` records `capdate` and `capfield`
    doing exactly that with four spaces; this one was caught before the push
    by reading `ci-census.py`'s regex instead of trusting the summary line.
    """
    ok, bad = [0], []
    print('cfcensus self-test')

    def case(name, cond, why=''):
        ok[0] += 1
        what = CASE_WHAT.get(name)
        if what is None:
            what = ('the live file still needs this `L8` exemption'
                    if name.startswith('U7:') else
                    'the declared alias points at a real gate board row'
                    if name.startswith('U10:') else why or '—')
        if cond:
            print('  ok   %-9s %s' % (name, what))
        else:
            print('  FAIL  %-9s %s' % (name, why))
            bad.append('%s  %s' % (name, why))

    def findings(text, exempt=None):
        return check(population(text), exempt=exempt)

    # ---- U0: the committed file is clean, or the run says which check ----
    try:
        live_f = check()
        case('U0', True)
    except Refused as e:
        print('REFUSING -- the live file could not be read: %s' % e)
        return 3

    # ---- U1..U3: the parser's own invariants ----------------------------
    try:
        cf_rows(_fixture(rows_md=['| `A-1` 🆕 | q | `R6`']))
        case('U1', False, 'a row not ending in `|` was accepted')
    except Refused:
        case('U1', True)
    try:
        cf_rows(_fixture(rows_md=['| `A-1` |']))
        case('U2', False, 'a three-field row was accepted')
    except Refused:
        case('U2', True)
    rows, raw, skipped = cf_rows(_fixture())
    case('U3', len(rows) == 2 and raw == 4 and skipped == 2,
         'fixture parsed %d rows from %d raw lines' % (len(rows), raw))

    # ---- U4: the owner is the SECOND-TO-LAST field, not cells[3] --------
    piped = _fixture(rows_md=[
        '| `A-1` 🆕 | a `sort \\| xargs` pipeline | `R6` |'])
    r = cf_rows(piped)[0][0]
    case('U4', r['owner_cell'] == '`R6`',
         'owner read as %r on a row with an embedded pipe' % r['owner_cell'])

    # ---- U5: first-cell rule, and the keyword rule it replaced ----------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R5` 關了，交給 `R6` |'])
    c = census(population(t))
    case('U5', c[0]['state'] == 'OPEN' and c[0]['kind'] == 'LIVE',
         'a row whose owner cell says a GATE closed was read as closed')

    # ---- U6: the population control (the T23 shape) ---------------------
    dead = _fixture(rows_md=['| `A-1` ✅ | q | `R5` |'])
    try:
        pop = population(dead)
        rs = census(pop)
        case('U6', not [x for x in rs
                        if x['state'] == 'OPEN' and x['kind'] == 'LIVE'],
             'the all-closed fixture still reported a live-owned row')
    except Refused:
        case('U6', True)

    # ---- L1: the orphan ------------------------------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R5` |'])
    case('L1+', any(x.startswith('L1 A-1') for x in findings(t)),
         'an open row owned by a closed gate was not reported')
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R6` |'])
    case('L1-', not any(x.startswith('L1') for x in findings(t)),
         'an open row owned by an OPEN gate was reported as an orphan')

    # ---- L2: the dead gate id ------------------------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R5b` |'])
    case('L2+', any(x.startswith('L2 A-1') for x in findings(t)),
         'a row naming a gate that does not exist was not reported')

    # ---- L3: no owner at all -------------------------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | nothing in particular |'])
    case('L3+', any(x.startswith('L3 A-1') for x in findings(t)),
         'a row naming no gate was not reported')
    t = _fixture(rows_md=['| `A-1` 🆕 | q | 任何一段動 `xyz` 的桌面段 |'])
    case('L3-', not any(x.startswith('L3') for x in findings(t)),
         'an any-segment row was reported as having no owner')

    # ---- L4/L5: the two gate sources must agree ------------------------
    t = _fixture(hdr=["## `R7`'s step list — ✅ CLOSED 2026-01-01"])
    case('L4+', any(x.startswith('L4 R7') for x in findings(t)),
         'a step list with no board row was not reported')
    t = _fixture(hdr=["## `R6`'s step list — ✅ CLOSED 2026-01-01"])
    case('L5+', any(x.startswith('L5 R6') for x in findings(t)),
         'a header/board disagreement was not reported')

    # ---- L6: C12's hole ②, seen from the other side --------------------
    t = _fixture(steps_md=['| **`R5-0`** | a | b | c | d |'])
    case('L6+', any(x.startswith('L6 R5') for x in findings(t)),
         'an unmarked step of a CLOSED gate was not reported')
    t = _fixture(steps_md=['| **`R5-0`** ✅ | a | b | c | d |'])
    case('L6-', not any(x.startswith('L6') for x in findings(t)),
         'a properly marked closed step was reported')

    # ---- L8: the two cells disagree ------------------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | **✅ 關了 —— `R6`** |'])
    case('L8+', any(x.startswith('L8 A-1') for x in findings(t)),
         'a first-cell/owner-cell disagreement was not reported')
    case('L8x', not any(x.startswith('L8') for x in
                        findings(t, exempt={'A-1': 'because'})),
         'an exempted row still reported L8')

    # ---- L9: the exemption list may not rot ----------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R6` |'])
    case('L9+', any(x.startswith('L9 Z-9') for x in
                    findings(t, exempt={'Z-9': 'stale'})),
         'an exemption naming a row that does not exist was not reported')
    case('L9c', any(x.startswith('L9 A-1') for x in
                    findings(t, exempt={'A-1': 'stale'})),
         'an exemption on a row that no longer triggers L8 was not reported')

    # ---- U7: the live exemptions are all still needed -------------------
    live_ex_off = check(exempt=False)
    for k in L8_EXEMPT:
        case('U7:' + k,
             any(x.startswith('L8 ' + k) for x in live_ex_off),
             'exempted on the live file but L8 does not fire there')

    # ---- U12: the ratchet moves in one direction, and only on purpose ---
    import contextlib
    one = population(_fixture(rows_md=['| `A-1` 🆕 | q | `R5` |']))

    def rc(pop, base, ex=False, sig=None):
        # 🔴 `ex=False` on a fixture.  The LIVE exemption list names rows a
        # fixture does not have, so `L9` fires twice and the count a ratchet
        # control needs exactly is off by two -- measured, on this case's
        # first run.
        with contextlib.redirect_stdout(io.StringIO()):
            return ratchet(pop, baseline=base, exempt=ex, sig=sig)

    case('U12=', rc(one, {'L1': 1}) == 0,
         'the ratchet failed at its own baseline')
    case('U12+', rc(one, {'L1': 0}) == 1, 'a GROWN debt was not reported')
    # 🔴 `U12=` passing now means the digest check is OFF for a hand baseline,
    # so it has to be shown ON somewhere or the whole `BASELINE_SIG` layer is
    # a line of code nothing exercises.  Two cases, one each way, on the same
    # fixture: the real digest passes and a wrong one is red.
    _sig_one = finding_sig(check(one))
    case('U12sig', rc(one, {'L1': 1}, sig={'L1': _sig_one['L1'][1]}) == 0,
         'the ratchet failed against its own freshly computed digest')
    case('U12sig-', rc(one, {'L1': 1}, sig={'L1': 'deadbeef'}) == 1,
         'a wrong digest with a right count was accepted -- the layer added '
         'for exactly that case does not fire')
    case('U12-', rc(one, {'L1': 2}) == 1,
         'a SHRUNK debt was accepted -- a payment nobody records is the '
         'defect this ratchet exists for')
    case('U12live', rc(None, None, None) == 0,
         'the live file is not at BASELINE=%r; if a debt was paid or added '
         'in this commit, move that entry in it and say why' % (BASELINE,))
    # 🔴 The control on the per-check shape.  A TOTAL-only ratchet passes when
    # two checks move in opposite directions, which is exactly what happened
    # an hour after the first version landed.  This fixture holds the total
    # still and moves two checks, and the ratchet must still be red.
    swap = dict(BASELINE)
    swap['L1'] = swap['L1'] + 1
    swap['L2'] = swap['L2'] - 1
    case('U13', rc(None, swap, None) == 1,
         'two checks moved by equal and opposite amounts and the ratchet '
         'passed on the unchanged total -- the defect this shape exists for')

    # ---- L10: duplicate ids ---------------------------------------------
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R6` |', '| `A-1` 🆕 | r | `R6` |'])
    case('L10+', any(x.startswith('L10 A-1') for x in findings(t)),
         'two rows sharing an id were not reported')
    case('L10-', not any(x.startswith('L10') for x in findings(_fixture())),
         'a table with distinct ids reported a duplicate')

    # ---- U10: every declared alias points at a real board row -----------
    live_board = population()['board']
    for src, dst in GATE_ALIAS.items():
        case('U10:' + src, dst in live_board,
             'alias target %r is not a gate board row' % dst)

    # ---- U11: the phantom step detector, both ways ----------------------
    t = _fixture(steps_md=['| **`R5-0`** ✅ | a | b | c | d |',
                           '| **`R6`** 🆕 | a | b | c | d |'])
    case('L7+', any(x.startswith('L7 R6') for x in findings(t)),
         'a non-step row inside a step list was not reported as a phantom')
    case('L7-', not any(x.startswith('L7') for x in findings(_fixture())),
         'a clean step list reported a phantom')

    # ---- U14: THE SENTENCE, NOT THE PREFIX -----------------------------
    # 🔴 Every `L<n>±` control above asserts `startswith('L<n> <id>')` and
    # nothing else.  量 2026-09-16, adversarially: `L1`'s message inverted to
    # *"no owner it names is a CLOSED gate"*, `L8`'s to *"the first cell DOES
    # say ✅"* and `L6`'s count multiplied by ten all survive the whole suite.
    # The product of this tool is the sentence a reader acts on, and nothing
    # asserted it.  One fixture, three checks, compared whole.
    t = _fixture(rows_md=[
        '| `A-1` 🆕 | q | `R5` |',
        '| `B-1` 🆕 | q | `R99` |',
        '| `C-1` 🆕 | q | — |',
    ])
    want = [
        'L1 A-1: open, and every owner it names is a CLOSED gate (R5) -- '
        'nobody will do it',
        'L2 B-1: names R99 as its owner and no gate by that name exists on '
        'the board or in a step list',
        "L3 C-1: open and names no owning gate -- the table's own rule calls "
        'that a bug in the table',
    ]
    # 🔴 `exempt={}` IS NOT TIDINESS, IT IS THE FIRST THING THIS CONTROL
    # FOUND.  量, on its own first run: `check()` on ANY fixture emits three
    # `L9 … is exempted from L8 and is not a row of this table any more`
    # findings, because `L8_EXEMPT` names three rows of the LIVE file and a
    # fixture has none of them.  Thirty-five controls asserted
    # `startswith('L<n> <id>')` and not one of them could see three whole
    # extra findings sitting beside the one they looked at.  The exemption
    # list is a statement about `PROGRESS.md`, so a fixture is run without it.
    got14 = sorted(findings(t, exempt={}))
    case('U14', got14 == sorted(want),
         'the finding sentences differ from the literal:\n       got  %r\n'
         '       want %r' % (got14, sorted(want)))

    # ---- U14b: two rows trading places inside one check -----------------
    ta = _fixture(rows_md=['| `A-1` 🆕 | q | `R5` |',
                           '| `B-1` 🆕 | q | `R6` |'])
    tb = _fixture(rows_md=['| `A-1` 🆕 | q | `R6` |',
                           '| `B-1` 🆕 | q | `R5` |'])
    sa = finding_sig(check(population(ta)))
    sb = finding_sig(check(population(tb)))
    case('U14b',
         sa.get('L1', (0, ''))[0] == 1 and sb.get('L1', (0, ''))[0] == 1
         and sa['L1'][1] != sb['L1'][1],
         'a row leaving `L1` while another joined it left both the count and '
         'the digest unchanged: %r vs %r' % (sa.get('L1'), sb.get('L1')))

    # ---- U15: `⊘` / DECLINED, end to end --------------------------------
    # 🔴 `cf_rows` computes the state, `render_counts` prints a row for it,
    # and NOTHING in `check` distinguished it from `CLOSED`.  量 2026-09-16:
    # mutating `if r['state'] != 'OPEN'` to `== 'CLOSED'` survives the whole
    # suite, because the live file has zero declined rows and no fixture had
    # one.  `R1z` is the gate that writes the first `⊘` into that table, so
    # the control has to exist before the row does.
    t = _fixture(rows_md=['| `A-1` ⊘ | q | `R5` |'])
    r = cf_rows(t)[0][0]
    case('U15', r['state'] == 'DECLINED' and findings(t, exempt={}) == [],
         'a declined row parsed as %r and produced %r'
         % (r['state'], findings(t, exempt={})))
    t = _fixture(rows_md=['| `A-1` 🆕 | q | `R5` |'])
    case('U15+', len(findings(t, exempt={})) == 1,
         'the same row OPEN produced %d finding(s), so `U15` proves nothing'
         % len(findings(t, exempt={})))

    # ---- U16: `resolve`'s header branch ---------------------------------
    # Dead on the live file -- all ten header gates are board rows too -- and
    # dead in every fixture, so inverting its closure survived.  The branch can
    # only fire on a document that ALSO has an `L4`, which is why the fixture
    # deliberately has one.
    t = _fixture(
        hdr=["## `R5`'s step list — ✅ CLOSED 2026-01-01",
             "## `R7`'s step list — ✅ CLOSED 2026-01-02"],
        rows_md=['| `A-1` 🆕 | q | `R7` |'])
    res16, un16 = resolve('`R7`', board_gates(t), header_gates(t),
                          step_state(t)[0])
    case('U16', res16 == [('R7', True, 'header')] and not un16,
         'the header branch returned %r / %r' % (res16, un16))

    # ---- U17: `gate_of_step`'s longest-prefix tie-break ------------------
    # 🔴 Worse than untested: the whole fallback loop is dead, because
    # `progress_step_owner` answers for all 72 live step ids.  A control has
    # to defeat the section-header answer DELIBERATELY (`owner=None`) or it
    # tests the line above the rule and reports it as the rule.
    bd17 = {'R5': 'CLOSED', 'R5-3': 'CLOSED'}
    g17 = (gate_of_step('R5-3-1', bd17, None),
           gate_of_step('R5-9', bd17, None),
           gate_of_step('R5-3-1', bd17, {'R5-3-1': 'R5'}))
    case('U17', g17 == ('R5-3', 'R5', 'R5'),
         'longest prefix / short prefix / header override gave %r' % (g17,))

    # ---- U18..U20: `board_gates` used to drop rows in silence ------------
    for nm18, bmd18, why18 in (
            ('U18', ['| R5 | closed thing | 1 | 1 | **`✓`** | ev |',
                     '| **R6** | open thing | 1 | — | `·` | |'],
             'a board row with no `**NAME**` was accepted'),
            ('U19', ['| **R5** | closed thing | 1 | 1 |  | ev |',
                     '| **R6** | open thing | 1 | — | `·` | |'],
             'a board row with a blank Status was accepted'),
            ('U20', ['| **R5** | closed thing | 1 | 1 | **`✓`** | ev |',
                     '| **R5** | again | 1 | 1 | `~` | ev |',
                     '| **R6** | open thing | 1 | — | `·` | |'],
             'two board rows for one gate were accepted, last wins')):
        try:
            board_gates(_fixture(board_md=bmd18))
            case(nm18, False, why18)
        except Refused:
            case(nm18, True)

    # ---- U21/U22: the two document-wide corruptions ----------------------
    base21 = _fixture()
    t21 = base21.replace('| `A-1` 🆕 | ask one | `R6` |\n',
                         '| `A-1` 🆕 | ask one | `R6` |\n## Interrupting\n')
    try:
        population(t21)
        case('U21', False, 'a `## ` heading inside a table was accepted, '
                           'truncating the population in silence')
    except Refused:
        case('U21', True)
    t22 = base21 + ('\n## Carried forward\n\n| # | Question | Owning gate |\n'
                    '|---|---|---|\n| `Z-1` 🆕 | hidden | `R5` |\n')
    try:
        population(t22)
        case('U22', False, 'a second `## Carried forward` section was '
                           'invisible to every check')
    except Refused:
        case('U22', True)

    # ---- U23..U26: the row shape ----------------------------------------
    for nm23, rmd23, why23 in (
            ('U23', ['| `A-1` 🆕 | q | `R5` | extra |'],
             'a row with a fourth column was accepted'),
            ('U25', ['| `A-1` 🆕 | q |'],
             "a two-column row was accepted -- the guard's real boundary")):
        try:
            cf_rows(_fixture(rows_md=rmd23))
            case(nm23, False, why23)
        except Refused:
            case(nm23, True)
    esc = cf_rows(_fixture(rows_md=[r'| `A-1` 🆕 | q | `a \| b` |']))[0][0]
    case('U24', esc['owner_cell'] == r'`a \| b`',
         'an escaped pipe in the owner cell read as %r' % esc['owner_cell'])
    try:
        cf_rows(_fixture().replace('| # | Question | Owning gate |',
                                   '| Item | Question | Owning gate |'))
        case('U26', False, 'a renamed header cell was read as a debt row')
    except Refused:
        case('U26', True)

    # ---- U8: `write` refuses on a document with no blocks ---------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'PROGRESS.md')
        with io.open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(_fixture())
        try:
            write_blocks(p)
            case('U8', False, '`write` created a block instead of refusing')
        except Refused:
            case('U8', True)

    # ---- U9: doc_block is the shared one, not a copy --------------------
    case('U9', doc_block('x' + (BEGIN % 'counts') + '\nQ\n'
                         + (END % 'counts') + 'y', 'counts',
                         begin=BEGIN, end=END) == 'Q',
         'the shared doc_block did not read a cfcensus block')

    print('RESULT: %d/%d' % (ok[0] - len(bad), ok[0]))
    if live_f:
        print('note: the live file has %d finding(s); that is `check`\'s '
              'report and not a control failure' % len(live_f))
    return 1 if bad else 0


# --------------------------------------------------------------------------

def main(argv):
    ap = argparse.ArgumentParser(prog='cfcensus.py')
    ap.add_argument('verb', nargs='?', default='check',
                    choices=('population', 'census', 'check', 'write',
                             'ratchet'))
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test()
        return {'population': report_population, 'census': report_census,
                'check': report_check, 'write': report_write,
                'ratchet': ratchet}[a.verb]()
    except Refused as e:
        print('REFUSED: %s' % e)
        return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
