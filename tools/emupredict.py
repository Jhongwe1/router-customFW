#!/usr/bin/env python3
"""emupredict -- column ① to column ② as a RULE, and two independent checks
that the rule is the one the frozen artefacts registered.

WHAT THIS IS
  `probe4` runs 75 encodings bare metal at `Status = 0x1000FC00` (`CU0 = 1`)
  and `uprobe` runs the SAME `cells4.S` bytes from Linux user mode.  The
  transform between the two columns was written down as three arms plus
  three exception classes over eight named rows -- the card § 6.1's four
  table rows, with `cache` and `mflxc0` sharing one class -- frozen before
  the board was powered, in
  `bench/2026-09-15/PREDICTIONS-B22-block21.md` § 6.1/§ 6.2/§ 6.3 and
  pre-registered per census row in `docs/emulation-surface.md` § 3.

  This tool is the transform as code.  It derives column ② from column ①
  ALONE and then -- separately -- reads the measured column ② and says
  whether the derivation was right.  `cross` is the second, independent
  side: it re-derives the hand-written `why` column of
  `docs/emulation-surface.md` § 3 from the same rule set.

WHAT IT DOES NOT OWN
  * the capture format.  `tools/isapay.py` owns `ROW_RE`, `UROW_RE`,
    `read_rows`, `verdict_row`, `census_names`, the TSV loader, the MIPS
    signal table and `cause_str`; they are IMPORTED, in the shape
    `tools/flashmap.py` imports `flashwin.overlaps_forbidden` rather than
    restating the rule.  `read_rows` deliberately returns values without
    names, so `row_names` below re-runs `isapay.ARMS[arm]`'s own compiled
    regex over the same file for the name column -- the pattern is isapay's
    object, not a copy of its text.
    🔴 `ROW_RE` (`^P4 `) and `UROW_RE` (`^PU `) stay SEPARATE for the reason
    isapay states: one `P4|PU` alternation merges two captures into one
    result block and the duplicate-index guard then reports the merge as
    corruption.
  * the rule set.  The card and `docs/emulation-surface.md` are the
    authority; a disagreement between this file and either of them is a
    finding about this file.
  * the device header.  isapay parses the `rlxuprobe:` header
    (`read_user_header`) and nothing in the repository parsed the
    `rlxprobe:` one, so `PHDR_RE` below is new rather than a second copy.

WHAT WOULD REFUTE IT, written before the sweep
  V1  any of the 31 payload rows outside the census whose ② verdict, signal
      or value differs from its ① -- the card § 6.2's own refutation, and it
      is thirty-one independent chances
  V2  `sync` carrying a signal in column ② -- `docs/emulation-surface.md`
      § 4's refutation condition, and the single most informative outcome
  V3  any `cache10`/`cache11`/`cache15`/`cache19`/`mflxc0` row NOT taking
      `SIGILL`/`SI_KERNEL` in column ②, or `ll`/`sc` taking one
  V4  a census row whose classification under these rules differs from
      § 3's hand-written `why`
  V5  the population join not coming out 32 exact + 12 by group = 44
      covered, 75 - 44 = 31 outside
Any of the five and the rule set is wrong, not the reading.  `--self-test`
attacks that from both sides.  C8/C9/C10 delete an exception from a COPY of
the rule table and require the predicted summary line to change to a STATED
wrong value; C17 plants V2 in the MEASUREMENT -- a `SIGILL` on `sync` in a
copy of column ② -- and requires `compare` to report it; C20 plants V4 in a
copy of `docs/emulation-surface.md` § 3.  A rule generator that cannot
produce a different answer and a comparison that cannot report a
disagreement both prove nothing, and neither is shown by a green run.

量 2026-09-15, `bench/2026-09-14/C1-P4j.log` against
`bench/2026-09-15/C2-UP.log`: the predicted line is `RAN 12, RIGHT 16,
TRAPS 46, WRONG 1`, which the card § 6.3 states verbatim, and the
measurement agrees on all 75 rows -- verdict, signal, and, on the 67 rows
the rule set predicts a value for, value.

🔴 AND ONE THING THE RULE SET DOES NOT PREDICT, WHICH IS WHY `compare` READS
VALUES AT ALL.  `sc` RETIRES ON BOTH ARMS -- the verdict is `RAN` either way,
which is exactly what `docs/emulation-surface.md` § 3 row 26 means by
*emulated and INVISIBLE* -- and its recorded `m0` still moves: ① `5A5A0FF2`,
the value of `rt`, and ② `A5A5F00D`, which is the scratch word untouched.  So
the emulated `sc` DID NOT STORE.  讀 `arch/rlx/kernel/traps.c`'s
`simulate_sc`: it has exactly one non-error path that returns 0 without
storing, `ll_bit == 0 || ll_task != current`, which writes 0 to `rt` and
returns -- the architecturally correct answer for an `sc` whose link is
broken.  ⚠️ 推 as to WHICH disjunct fired: this payload records `m0` and not
`rt`, and `ll_bit` is cleared by every context switch, so the capture cannot
separate them.  A row that reads `rt` after the `sc` would.
**The narrow claim is that a trap/no-trap table cannot see this by
construction, and that `invisible` was a statement about the VERDICT and is
exactly true as written.**  `ll`'s value is identical on both arms, so `ll`
stays invisible in both senses.

⚠️ SCOPE, stated rather than discovered later.  Column ② is ONE seating, one
boot, no row repeated (`docs/emulation-surface.md` § 7 ①).  `compare` prints
that line every time.

Usage
    emupredict.py rules [--col1 LOG]
    emupredict.py predict COL1LOG
    emupredict.py compare COL1LOG COL2LOG
    emupredict.py cross [--col1 LOG]
    emupredict.py --self-test

Exit
    0  clean
    1  a finding
    3  REFUSED -- an input would not parse, or a row the rule set cannot
       classify.  A rule that cannot classify a row must say so, never guess.
"""
import argparse
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.path.insert(0, HERE)
import isapay  # noqa: E402  -- the capture format has exactly one owner

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The two committed captures this rule set was derived against and the file
# that pre-registered it.  Cited by id and section everywhere else; these are
# paths because a tool has to open them.
COL1 = os.path.join(ROOT, "bench", "2026-09-14", "C1-P4j.log")
COL2 = os.path.join(ROOT, "bench", "2026-09-15", "C2-UP.log")
SURFACE = os.path.join(ROOT, "docs", "emulation-surface.md")

CARD = "bench/2026-09-15/PREDICTIONS-B22-block21.md"
DOC = "docs/emulation-surface.md"

CAVEAT = ("column ② is ONE seating, one boot, no row repeated -- "
          "%s § 7 ①" % DOC)


class Refuse(Exception):
    pass


# --------------------------------------------------------------------------
# The capture's own block terminator.  isapay's `UEND` is the PROCESS
# terminator (`rlxuprobe: end`, which says `alarm(30)` did not kill the run);
# this is the ROW BLOCK terminator, which says the last row printed.  A
# capture cut between the two would pass isapay's check and be short here.
# --------------------------------------------------------------------------
ROWS_END = {"device": "rlxprobe: rows end", "user": "rlxuprobe: rows end"}

# `rlxprobe: <key>=<8 hex>`.  Keys carry dots (`install.words`), which is why
# this is not isapay's `UHDR_RE` with the prefix changed.
PHDR_RE = re.compile(r"^rlxprobe:\s+([a-z_0-9.]+)=([0-9a-fA-F]{8})\s*$")

EXC_RI = 10          # ExcCode 10, Reserved Instruction
EXC_CPU = 11         # ExcCode 11, Coprocessor Unusable
SIG_ILL = 4          # isapay.MIPS_SIGNAMES[4]; MIPS numbers its signals its
SI_KERNEL = 0x80     # own way, and isapay owns that table
NO_SIGNAL = (None, None)
ILL = (SIG_ILL, SI_KERNEL)

# --------------------------------------------------------------------------
# THE GROUP-EXPANSION MAP, EXPLICIT AND CHECKED, NEVER A NAME JOIN.
#
# 量: the exact-name intersection of `tools/isa-payload.tsv` (75 rows) with
# `tools/isa-census.tsv`'s 39 `r1a` rows is only 32.  Twelve more payload rows
# are covered by a census row that names a GROUP rather than an instruction.
# A join on names alone silently drops those twelve; a join that expands
# groups without stating the map DOUBLE-COUNTS `madd`, which is both its own
# census row and a member of `SPECIAL2`.
#
# So the map is written out, every key and value is checked against the two
# tables, and the arithmetic is asserted rather than trusted.  Members that
# ALSO match by exact name (`madd`, and all five `COP1` rows) are listed here
# anyway: leaving them out would make the map read as the set of rows only
# reachable this way, which is a different and smaller statement.
# --------------------------------------------------------------------------
GROUP_MAP = {
    "cache": ["cache10", "cache11", "cache15", "cache19"],
    "COP1": ["mfc1", "lwc1", "swc1", "ldc1", "sdc1"],
    "COP2": ["mfc2"],
    "SPECIAL2": ["clz", "clo", "mul", "madd"],
    "SPECIAL3": ["ext", "ins", "seb", "wsbh"],
}

# The two census rows with no payload row at all.  They are `**none**` cells
# in `docs/emulation-surface.md` § 3 and they are REFUSED rather than blanked:
# a blank reads as *not done yet*, and both of these are decided.
NO_ROW = {
    "jalx": ("EXCLUDED -- must not be run. MIPS16 is implemented on this "
             "part, so a user-mode `jalx` does not trap: it retires into "
             "MIPS16 mode at an address a 26-bit field picks, and the cost "
             "of being wrong is a power cycle. %s § 1 ②" % DOC),
    "mtlxc0": ("never given a payload row, deliberately -- the write side of "
               "`mflxc0`, and writing an unread COP0 register from a probe "
               "is not the same experiment as reading one. %s § 3 row 32"
               % DOC),
}

# The card § 6.2's own list of the 31 payload rows outside the census, frozen
# at `9874012` before the board had power.  It is here to be CHECKED AGAINST
# the derivation, not to drive it: `rules` derives the set from the two tables
# and `--self-test` C2 requires the two to be equal.
CARD_31 = ("add lw sw mult mult_hi beq jr special0e madd_hi rotr synci cfc3 "
           "ltw madh madl mazh mazl msbh msbl mszh mszl udi0i udi1i udi2i "
           "udi3i udi0 udi1 udi2 udi3 udi4 udi5").split()

# --------------------------------------------------------------------------
# THE RULE SET.  Three arms over everything, four exception classes that
# claim a row by name before the arms are consulted.
#
# The arms are the card § 6.2's, verbatim:
#   R-a  ① retired (RIGHT, RAN or WRONG)  =>  ② the same verdict and the
#        same value, no signal
#   R-b  ① ExcCode 10 (RI)                =>  ② SIGILL / SI_KERNEL
#   R-c  ① ExcCode 11 (CpU, CE != 0)      =>  ② SIGILL / SI_KERNEL
#
# The value half of R-b and R-c is not in the card and is derived here: the
# probed word trapped on BOTH arms, so what the recorded slot holds is what
# the template left, and `cells4.S` is the same bytes with the same seeds at
# both privilege levels.  It is stated as a prediction so that it can fail.
#
# The exceptions are the card § 6.1's four rows and `docs/emulation-surface.md`
# § 3's `why` column.  Each carries the ① SHAPE it requires: a rule is a
# conditional, so a row whose ① violates the antecedent is REFUSED rather
# than having the consequent applied to it.
# --------------------------------------------------------------------------
RETIRED = (isapay.V_RIGHT, isapay.V_RAN, isapay.V_WRONG)


class Exc(object):
    """One exception class: what it claims, what ① must look like, what ②
    is, and which column of § 3's `why` it lands in."""

    def __init__(self, rule, cls, vis, needs, verdict, signal, value_why,
                 why):
        self.rule = rule
        self.cls = cls            # `same` / `emulation` / `privilege`
        self.vis = vis            # `visible` / `invisible` / None
        self.needs = needs        # what ① must be for the rule to apply
        self.verdict = verdict    # a verdict, or None meaning "unchanged"
        self.signal = signal
        self.value_why = value_why
        self.why = why


def default_exceptions():
    """A fresh copy of the exception table.

    It is a FUNCTION and not a module constant so that `--self-test` can
    delete an entry from a copy and require the predicted summary line to
    change.  A rule set that cannot be mutated cannot be shown to be doing
    any work.
    """
    e = {}
    e["sync"] = Exc(
        "X-sync", "emulation", "visible", "trap-ri", isapay.V_RAN, NO_SIGNAL,
        "not predicted: the emulated `sync` is a no-op, so what the recorded "
        "slot holds is not a consequence the rule states",
        "`do_ri` reaches `simulate_sync`, SPECIAL funct 0x0F matches, so the "
        "instruction is emulated and no signal is raised. THE ONLY ROW on "
        "which the emulation surface is a trap/no-trap difference")
    for n in ("ll", "sc"):
        e[n] = Exc(
            "X-llsc", "emulation", "invisible", "retired", None, NO_SIGNAL,
            "not predicted: `simulate_llsc` re-implements the instruction, "
            "and whether its answer equals the silicon's is not something "
            "the trap/no-trap rule says anything about",
            "from user mode the encoding takes CpU(11) CE 0, `do_cpu`'s "
            "cpid 0 arm reaches `simulate_llsc` and it matches -- emulated, "
            "and INVISIBLE in the verdict because the row already retires "
            "on the die")
    for n in ("cache10", "cache11", "cache15", "cache19", "mflxc0"):
        e[n] = Exc(
            "X-priv", "privilege", None, "retired", isapay.V_TRAP, ILL,
            "not predicted: ① retired and ② trapped, so the two columns "
            "record different events and there is no rule making their "
            "values comparable",
            "it retires on the die ONLY because column ① was measured at "
            "`CU0 = 1`. From user mode `CU0` is clear, `simulate_llsc` does "
            "not match, and the result is SIGILL. A PRIVILEGE artefact, not "
            "emulation -- %s § 2" % DOC)
    return e


class Pred(object):
    __slots__ = ("name", "rule", "cls", "vis", "verdict", "sig", "code",
                 "value", "value_why")

    def __init__(self, name, rule, cls, vis, verdict, signal, value,
                 value_why):
        self.name = name
        self.rule = rule
        self.cls = cls
        self.vis = vis
        self.verdict = verdict
        self.sig, self.code = signal
        self.value = value
        self.value_why = value_why


def sig_str(sig, code):
    """The measured side's vocabulary, from isapay's own tables."""
    if sig is None:
        return "-"
    return "%s/%s" % (isapay.MIPS_SIGNAMES.get(sig, "sig %d" % sig),
                      isapay.SI_CODES.get(code, "0x%X" % code))


# --------------------------------------------------------------------------
# The population join.
# --------------------------------------------------------------------------
def population(rows=None, census=None):
    """Derive the join and REFUSE if its arithmetic does not hold.

    Returns a dict.  Nothing downstream may proceed on a join that does not
    come out 32 + 12 = 44 and 75 - 44 = 31, because a naive name join comes
    out 32 and 43 and looks exactly as much like an answer.
    """
    rows = rows if rows is not None else isapay.load_rows()
    census = census if census is not None else isapay.census_names()
    pay = [r["name"] for r in rows]
    payset = set(pay)
    if len(payset) != len(pay):
        raise Refuse("the payload table has duplicate names")
    cen = set(census)

    for k, v in sorted(GROUP_MAP.items()):
        if k not in cen:
            raise Refuse("group map key %r is not an `r1a` row of "
                         "tools/isa-census.tsv" % k)
        if k in payset:
            raise Refuse("group map key %r is ALSO a payload row name -- it "
                         "would be joined twice, once by name and once by "
                         "group" % k)
        for m in v:
            if m not in payset:
                raise Refuse("group map %r names payload row %r, which does "
                             "not exist" % (k, m))

    exact = payset & cen
    by_group = set()
    for v in GROUP_MAP.values():
        by_group |= set(v)
    covered = exact | by_group
    outside = payset - covered
    new_by_group = covered - exact

    unreached = sorted(cen - exact - set(GROUP_MAP))
    if unreached != sorted(NO_ROW):
        raise Refuse("the census rows with no payload row are %s; this tool "
                     "declares %s" % (unreached, sorted(NO_ROW)))

    if len(exact) != 32 or len(new_by_group) != 12 or len(covered) != 44 \
            or len(outside) != 31:
        raise Refuse(
            "the join arithmetic moved: exact %d (32), new by group %d (12), "
            "covered %d (44), outside %d (31). A rule set frozen against 31 "
            "rows may not be applied to a different 31"
            % (len(exact), len(new_by_group), len(covered), len(outside)))

    return {"rows": rows, "census": census, "payload": payset, "cen": cen,
            "exact": exact, "by_group": by_group, "new_by_group": new_by_group,
            "covered": covered, "outside": outside}


def members_of(cname, payset):
    """The payload rows one census row covers.  One place, one rule."""
    m = set(GROUP_MAP.get(cname, ()))
    if cname in payset:
        m.add(cname)
    return sorted(m)


# --------------------------------------------------------------------------
# Reading a capture.
# --------------------------------------------------------------------------
def row_names(path, arm):
    """{idx: name} using isapay's own compiled regex for that arm.

    `isapay.read_rows` returns the eight words and drops the name column, so
    this re-runs the SAME pattern object over the same file rather than
    writing a second one.
    """
    rx = isapay.ARMS[arm][0]
    out = {}
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    for line in txt.replace("\r", "\n").split("\n"):
        m = rx.match(line.strip())
        if m:
            out[int(m.group(1), 16)] = m.group(2)
    return out


def device_header(path):
    hdr = {}
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    for line in txt.replace("\r", "\n").split("\n"):
        m = PHDR_RE.match(line.strip())
        if m:
            hdr[m.group(1)] = int(m.group(2), 16)
    return hdr


def has_marker(path, marker):
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    return marker in txt.replace("\r", "\n")


def read_column(path, arm, rows):
    """[(row, verdict, value, rec)] for one capture, with every refusal the
    rule set needs taken here rather than downstream.

    isapay's `read_rows` refuses an empty capture, an out-of-range index and
    a duplicated index with different values; this adds the three it cannot
    see, because they only matter to a tool that DERIVES one column from the
    other: the row-block terminator, a short capture, and a name column that
    disagrees with the table.
    """
    if arm not in isapay.ARMS:
        raise Refuse("unknown arm %r" % arm)
    if not os.path.exists(path):
        raise Refuse("no capture at %s" % path)
    words, present = isapay.read_rows(path, len(rows), arm)
    if not has_marker(path, ROWS_END[arm]):
        raise Refuse("%s has no `%s` -- the row block did not finish, and a "
                     "truncated capture and a capture of absences are "
                     "different answers" % (path, ROWS_END[arm]))
    if len(present) != len(rows):
        missing = sorted(set(r["idx"] for r in rows) - set(present))
        raise Refuse("%s carries %d of %d rows; missing index %s"
                     % (path, len(present), len(rows), missing[:8]))
    names = row_names(path, arm)
    out = []
    for r in rows:
        got = names.get(r["idx"])
        if got != r["name"]:
            raise Refuse("row %d is %r in %s and %r in tools/isa-payload.tsv "
                         "-- a rule set keyed on names may not be applied to "
                         "a capture whose names disagree"
                         % (r["idx"], got, os.path.basename(path), r["name"]))
        base = r["idx"] * isapay.ROW_WORDS
        rec = tuple(words[base:base + isapay.ROW_WORDS])
        v, val = isapay.verdict_row(r, rec)
        if v == isapay.V_NORUN:
            raise Refuse("row %s did not run in %s" % (r["name"], path))
        out.append((r, v, val, rec))
    return out


def tally_of(pairs):
    t = {}
    for v in pairs:
        t[v] = t.get(v, 0) + 1
    return t


def summary_line(tally, arm="user", n=None):
    """The line `tools/isapay.py verdict` prints and the card § 6.3 states.

    Its format is isapay's `cmd_verdict`, restated here because that tool
    builds it inline.  `--self-test` C18 requires this function's output to
    equal isapay's, character for character, over the committed ② capture --
    so the restatement is checked rather than trusted.
    """
    return ("verdict (%s arm): %d row(s), %s"
            % (arm, n if n is not None else sum(tally.values()),
               ", ".join("%s %d" % (k, tally[k]) for k in sorted(tally))))


# --------------------------------------------------------------------------
# The rule set applied.
# --------------------------------------------------------------------------
def classify(r, v1, val1, rec1, exc):
    """Column ② for one row, from column ① alone.  REFUSES rather than
    guessing."""
    name = r["name"]
    trapped = bool(rec1[1])
    code = isapay.exccode(rec1[2]) if trapped else None
    ce = ((rec1[2] >> 28) & 3) if trapped else None

    x = exc.get(name)
    if x is not None:
        if x.needs == "retired" and v1 not in RETIRED:
            raise Refuse("%s is an exception row whose rule requires ① to "
                         "have RETIRED, and ① reads %s. A rule is a "
                         "conditional; its consequent may not be applied to "
                         "a row that fails the antecedent" % (name, v1))
        if x.needs == "trap-ri" and not (trapped and code == EXC_RI):
            raise Refuse("%s is an exception row whose rule requires ① "
                         "ExcCode %d, and ① reads %s%s"
                         % (name, EXC_RI, v1,
                            "" if not trapped else " ExcCode %d" % code))
        verdict = x.verdict if x.verdict is not None else v1
        return Pred(name, x.rule, x.cls, x.vis, verdict, x.signal, None,
                    x.value_why)

    if v1 in RETIRED:
        # R-a.  The card § 6.2 states verdict AND value.
        return Pred(name, "R-a", "same", None, v1, NO_SIGNAL, val1,
                    "card %s § 6.2 R-a: the same verdict and the same value"
                    % CARD)
    if not trapped:
        raise Refuse("%s reads %s in column ① and no arm covers it"
                     % (name, v1))
    if code == EXC_RI:
        return Pred(name, "R-b", "same", None, isapay.V_TRAP, ILL, val1,
                    "the word trapped on both arms, so the recorded slot "
                    "holds what the template left and `cells4.S` is the "
                    "same bytes at both privilege levels")
    if code == EXC_CPU:
        if ce == 0:
            raise Refuse(
                "%s reads ExcCode %d with CE 0 in column ①. R-c is stated "
                "for CE != 0; CE 0 is the `ll`/`sc`/`mflxc0` shape, which is "
                "an exception row, and this row is not one" % (name, EXC_CPU))
        return Pred(name, "R-c", "same", None, isapay.V_TRAP, ILL, val1,
                    "the word trapped on both arms, so the recorded slot "
                    "holds what the template left and `cells4.S` is the "
                    "same bytes at both privilege levels")
    raise Refuse("%s reads ExcCode %d in column ①, and R-b covers %d and "
                 "R-c covers %d. A rule that cannot classify a row must say "
                 "so" % (name, code, EXC_RI, EXC_CPU))


def predict_all(path=COL1, rows=None, exc=None):
    """[(row, v1, val1, rec1, Pred)] plus the header cross-check."""
    rows = rows if rows is not None else isapay.load_rows()
    exc = exc if exc is not None else default_exceptions()
    col1 = read_column(path, "device", rows)
    out = [(r, v, val, rec, classify(r, v, val, rec, exc))
           for r, v, val, rec in col1]

    # The payload's own counters against the desk's verdicts.  `probe4`
    # counts traps while it runs; this tool counts them from the printed
    # rows.  Two sources for one number, in one file.
    hdr = device_header(path)
    got_trap = sum(1 for _r, v, _val, _rec, _p in out if v == isapay.V_TRAP)
    got_ran = len(out) - got_trap
    if "trapped" in hdr and hdr["trapped"] != got_trap:
        raise Refuse("the capture's own `rlxprobe: trapped` reads %d and the "
                     "printed rows give %d" % (hdr["trapped"], got_trap))
    if "ran" in hdr and hdr["ran"] != got_ran:
        raise Refuse("the capture's own `rlxprobe: ran` reads %d and the "
                     "printed rows give %d" % (hdr["ran"], got_ran))
    return out


# --------------------------------------------------------------------------
# `rules`
# --------------------------------------------------------------------------
ARM_TEXT = [
    ("R-a", "① retired (RIGHT, RAN or WRONG)",
     "② the same verdict and the same value, no signal"),
    ("R-b", "① ExcCode 10 (RI)", "② SIGILL / SI_KERNEL"),
    ("R-c", "① ExcCode 11 (CpU, CE != 0)", "② SIGILL / SI_KERNEL"),
]


def cmd_rules(col1=COL1, quiet=False):
    p = population()
    exc = default_exceptions()
    print("=== emupredict rules ===")
    print()
    print("  The rule set is frozen in %s § 6.1/§ 6.2 and pre-registered per"
          % CARD)
    print("  census row in %s § 3. This tool applies it; it does not own it."
          % DOC)
    print()
    print("  population, derived from the two tables and not asserted")
    print("    payload rows   tools/isa-payload.tsv                  %3d"
          % len(p["payload"]))
    print("    census rows    tools/isa-census.tsv, kind r1a         %3d"
          % len(p["cen"]))
    print("    joined by exact name                                  %3d"
          % len(p["exact"]))
    print("    joined only by GROUP                                  %3d"
          % len(p["new_by_group"]))
    print("    payload rows the census covers                        %3d"
          % len(p["covered"]))
    print("    payload rows OUTSIDE the census -- card § 6.2's 31    %3d"
          % len(p["outside"]))
    print()
    print("  the group-expansion map, stated rather than joined by name")
    for k in sorted(GROUP_MAP):
        mem = GROUP_MAP[k]
        new = [m for m in mem if m not in p["exact"]]
        print("    %-9s <- %-44s %d new" % (k, " ".join(mem), len(new)))
    print("    (`madd` and the five COP1 rows are reached BOTH ways; the "
          "count above")
    print("     is over DISTINCT payload rows, which is what a naive join "
          "gets wrong)")
    print()
    print("  census rows with no payload row -- REFUSED, never blanked")
    for k in sorted(NO_ROW):
        print("    %-9s %s" % (k, NO_ROW[k]))
    print()

    out = predict_all(col1)
    used = {}
    for _r, _v, _val, _rec, pr in out:
        used[pr.rule] = used.get(pr.rule, 0) + 1
    print("  arms, over the rows no exception claims -- counted by applying")
    print("  them to %s" % os.path.relpath(col1, ROOT).replace(os.sep, "/"))
    for rid, ante, cons in ARM_TEXT:
        print("    %-6s %-34s %-48s %3d row(s)"
              % (rid, ante, cons, used.get(rid, 0)))
    print()
    print("  exception classes, which claim a row by name before any arm")
    seen = []
    for n in sorted(exc):
        x = exc[n]
        if x.rule in seen:
            continue
        seen.append(x.rule)
        mem = sorted(k for k in exc if exc[k].rule == x.rule)
        lbl = x.cls + ("" if not x.vis else ", " + x.vis)
        print("    %-6s %-20s %-24s %3d row(s)"
              % (x.rule, lbl, " ".join(mem), used.get(x.rule, 0)))
        if not quiet:
            print("           %s" % x.why)
    print()
    tot = sum(used.values())
    print("  %d row(s) classified, %d arm(s) + %d exception class(es)"
          % (tot, len([a for a in ARM_TEXT if used.get(a[0])]), len(seen)))
    if tot != len(p["payload"]):
        print("  FINDING: %d classified against %d payload rows"
              % (tot, len(p["payload"])))
        return 1
    return 0


# --------------------------------------------------------------------------
# `predict`
# --------------------------------------------------------------------------
def cmd_predict(col1, quiet=False):
    out = predict_all(col1)
    if not quiet:
        print("  %-10s %-6s %-6s %-11s %-6s %-17s %-9s"
              % ("row", "rule", "① vd", "① cause", "② vd", "② signal",
                 "② value"))
        for r, v1, val1, rec1, pr in out:
            print("  %-10s %-6s %-6s %-11s %-6s %-17s %-9s"
                  % (r["name"], pr.rule, v1, isapay.cause_str("device", rec1),
                     pr.verdict, sig_str(pr.sig, pr.code),
                     ("%08X" % pr.value) if pr.value is not None else "-"))
        print()
    t1 = tally_of([v for _r, v, _val, _rec, _p in out])
    t2 = tally_of([p.verdict for _r, _v, _val, _rec, p in out])
    print("%s   <- column ①, measured"
          % summary_line(t1, "device", len(out)))
    print("%s   <- column ②, PREDICTED from column ① alone"
          % summary_line(t2, "user", len(out)))
    return 0


# --------------------------------------------------------------------------
# `compare`
# --------------------------------------------------------------------------
def compare(col1=COL1, col2=COL2, rows=None, exc=None):
    """(findings, observations, rowlines, t1, t2pred, t2meas)."""
    rows = rows if rows is not None else isapay.load_rows()
    pred = predict_all(col1, rows=rows, exc=exc)
    meas = read_column(col2, "user", rows)
    by_idx = dict((r["idx"], (r, v, val, rec)) for r, v, val, rec in meas)

    findings, obs, lines = [], [], []
    for r, v1, val1, rec1, pr in pred:
        r2, v2, val2, rec2 = by_idx[r["idx"]]
        sig2 = ((rec2[2] >> 16) & 0xFFFF) if rec2[1] else None
        code2 = (rec2[2] & 0xFFFF) if rec2[1] else None
        ok = True
        if pr.verdict != v2:
            findings.append("%s: predicted ② %s, measured %s"
                            % (r["name"], pr.verdict, v2))
            ok = False
        if (pr.sig, pr.code) != (sig2, code2):
            findings.append("%s: predicted ② %s, measured %s"
                            % (r["name"], sig_str(pr.sig, pr.code),
                               sig_str(sig2, code2)))
            ok = False
        if pr.value is not None and pr.value != val2:
            findings.append("%s: predicted ② value %08X, measured %08X"
                            % (r["name"], pr.value, val2))
            ok = False
        unpredicted = (pr.value is None and val1 != val2)
        if unpredicted:
            # `same_verdict` is what separates the two kinds.  A row whose
            # verdict ALSO changed recorded two different events, so its two
            # values are not comparable.  A row that RETIRED on both arms and
            # still holds different values is the emulator's answer differing
            # from the silicon's -- which a trap/no-trap table cannot see.
            obs.append((r["name"], pr.rule, val1, val2, v1 == v2,
                        pr.value_why))
        # `ok (obs)` and not `ok`: the two values differ and the rule set
        # predicted neither, so nothing was refuted AND nothing agreed.  A
        # bare `ok` beside two different values is a column that reads as a
        # comparison it did not make.
        lines.append((r["name"], pr.rule, v1, pr.verdict, v2,
                      sig_str(pr.sig, pr.code), sig_str(sig2, code2),
                      val1, val2,
                      "FINDING" if not ok else
                      ("ok (obs)" if unpredicted else "ok")))
    t1 = tally_of([v for _r, v, _val, _rec, _p in pred])
    t2p = tally_of([p.verdict for _r, _v, _val, _rec, p in pred])
    t2m = tally_of([v for _r, v, _val, _rec in meas])
    return findings, obs, lines, t1, t2p, t2m


def cmd_compare(col1, col2, quiet=False):
    findings, obs, lines, t1, t2p, t2m = compare(col1, col2)

    def rel(p):
        return os.path.relpath(p, ROOT).replace(os.sep, "/")

    print("=== emupredict compare ===")
    print("  column ①  %-28s probe4, bare metal, Status=0x1000FC00 (CU0=1)"
          % rel(col1))
    print("  column ②  %-28s uprobe, Linux user mode" % rel(col2))
    print("  the rule set: %s § 6.1/§ 6.2; per census row, %s § 3"
          % (CARD, DOC))
    print()
    if not quiet:
        print("  %-10s %-6s %-6s %-6s %-6s %-17s %-17s %-8s %-8s %s"
              % ("row", "rule", "①", "②pred", "②meas", "②pred cause",
                 "②meas cause", "①value", "②value", "agree"))
        for (n, rule, v1, vp, vm, sp, sm, x1, x2, ok) in lines:
            print("  %-10s %-6s %-6s %-6s %-6s %-17s %-17s %-8s %-8s %s"
                  % (n, rule, v1, vp, vm, sp, sm,
                     "%08X" % x1 if x1 is not None else "-",
                     "%08X" % x2 if x2 is not None else "-", ok))
        print()
    # All three at column 0 and unindented, so the two `verdict (user arm):`
    # lines can be compared with the card § 6.3's string as written.
    print("%s   <- column ①, measured"
          % summary_line(t1, "device", len(lines)))
    print("%s   <- PREDICTED from column ① alone"
          % summary_line(t2p, "user", len(lines)))
    print("%s   <- MEASURED" % summary_line(t2m, "user", len(lines)))
    print()
    print("  rows compared: %d   verdict+signal+value, not verdict alone"
          % len(lines))
    print("  value predicted by the rule set on %d row(s); the other %d are "
          "the" % (sum(1 for l in lines if l[1] in ("R-a", "R-b", "R-c")),
                   sum(1 for l in lines if l[1] not in ("R-a", "R-b", "R-c"))))
    print("  exception rows, where ① and ② record different events")
    print()
    live = [o for o in obs if o[4]]
    dead = [o for o in obs if not o[4]]
    if dead:
        print("  OBSERVATION -- the value moved AND so did the verdict, so "
              "the two")
        print("  columns recorded different events and the values are not "
              "comparable:")
        for nm, rule, x1, x2, _sv, why in dead:
            print("    %-10s %-6s ① %08X  ② %08X" % (nm, rule, x1, x2))
            print("               %s" % why)
        print()
    if live:
        print("  OBSERVATION -- the row RETIRED ON BOTH ARMS and the recorded "
              "value")
        print("  still moved. The rule set predicts neither value here and "
              "this is not")
        print("  a finding against it; it is the emulator's answer differing "
              "from the")
        print("  silicon's, which a trap/no-trap table cannot see by "
              "construction:")
        for nm, rule, x1, x2, _sv, why in live:
            print("    %-10s %-6s ① %08X  ② %08X" % (nm, rule, x1, x2))
            print("               %s" % why)
        print()
    print("  ⚠️  %s" % CAVEAT)
    print()
    if findings:
        for f in findings:
            print("  FINDING: %s" % f)
        print("RESULT: %d finding(s) over %d row(s)" % (len(findings),
                                                        len(lines)))
        return 1
    print("RESULT: 0 findings over %d row(s) -- column ② was derived from "
          "column ①" % len(lines))
    print("        alone and the measurement agrees with every prediction "
          "the rule set")
    if obs:
        print("        makes. The %d OBSERVATION(s) above are what it does "
              "NOT predict." % len(obs))
    else:
        print("        makes, and it predicted something about every row.")
    return 0


# --------------------------------------------------------------------------
# `cross` -- the second, independent side.
# --------------------------------------------------------------------------
WHY_VOCAB = {
    "same": ("same", None),
    "privilege": ("privilege", None),
    "emulation, invisible": ("emulation", "invisible"),
    "emulation, visible": ("emulation", "visible"),
    "-": (None, None),
}


def norm_why(cell):
    """§ 3's `why` cell as (class, visibility).  REFUSES an unknown token.

    The column is hand-written prose with 🔴/🟢 decorations and `**bold**`.
    Stripping those is the whole normalisation; anything left that is not in
    the vocabulary is a cell this tool has never seen, and guessing at it
    would make the cross-check agree with a table it did not read.
    """
    s = cell.replace("🔴", "").replace("🟢", "").replace("**", "")
    s = s.replace("—", "-").replace("–", "-")
    s = " ".join(s.split()).lower()
    if s not in WHY_VOCAB:
        raise Refuse("%s § 3 has a `why` cell this tool does not know: %r"
                     % (DOC, cell))
    return WHY_VOCAB[s]


def strip_cell(cell):
    return cell.replace("**", "").replace("`", "").strip()


def read_surface_table(path=SURFACE):
    """[(n, name, col1_cell, col2_cell, why_cell)] for § 3's 39 rows."""
    if not os.path.exists(path):
        raise Refuse("no table at %s" % path)
    txt = io.open(path, encoding="utf-8").read()
    lines = txt.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    start = None
    for i, l in enumerate(lines):
        if l.startswith("## § 3."):
            start = i
            break
    if start is None:
        raise Refuse("%s has no `## § 3.` heading" % DOC)
    hdr = None
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if lines[i].startswith("| # | row |"):
            hdr = i
            break
    if hdr is None:
        raise Refuse("%s § 3 has no `| # | row |` table header" % DOC)
    out = []
    for l in lines[hdr + 1:]:
        if not l.startswith("|"):
            break
        parts = l.split("|")
        if len(parts) != 7:
            raise Refuse("%s § 3 has a row with %d pipe fields, expected 7: "
                         "%r" % (DOC, len(parts), l[:60]))
        cells = [p.strip() for p in parts[1:6]]
        if set(cells[0]) <= set("-: "):
            continue
        try:
            n = int(cells[0])
        except ValueError:
            raise Refuse("%s § 3 row number is %r" % (DOC, cells[0]))
        out.append((n, strip_cell(cells[1]), cells[2], cells[3], cells[4]))
    if not out:
        raise Refuse("%s § 3's table body is empty" % DOC)
    if [n for n, _a, _b, _c, _d in out] != list(range(1, len(out) + 1)):
        raise Refuse("%s § 3's row numbers are not 1..%d in order"
                     % (DOC, len(out)))
    return out


def classify_census(cname, payset, preds):
    """(class, visibility) for one census row, from the rule set.

    A census row that names a group is the union of its members: privilege
    wins over emulation wins over same, because a row is on the surface if
    ANY encoding under it is, and it is a privilege artefact if any is.
    """
    mem = members_of(cname, payset)
    if not mem:
        return None, None
    cls = "same"
    vis = None
    for m in mem:
        p = preds[m]
        if p.cls == "privilege":
            cls, vis = "privilege", None
        elif p.cls == "emulation" and cls != "privilege":
            cls = "emulation"
            if p.vis == "visible":
                vis = "visible"
            elif vis is None:
                vis = "invisible"
    return cls, vis


def cmd_cross(col1=COL1, path=SURFACE, quiet=False):
    p = population()
    payset = p["payload"]
    out = predict_all(col1, rows=p["rows"])
    preds = dict((r["name"], pr) for r, _v, _val, _rec, pr in out)
    table = read_surface_table(path)

    print("=== emupredict cross ===")
    print("  the SECOND side: %s § 3's hand-written `why` column, re-derived"
          % DOC)
    print("  from the same rule set. The table is the authority; a "
          "disagreement")
    print("  here is a finding about tools/emupredict.py.")
    print()
    if len(table) != len(p["cen"]):
        raise Refuse("%s § 3 has %d rows and tools/isa-census.tsv has %d "
                     "`r1a` rows" % (DOC, len(table), len(p["cen"])))
    findings = []
    excluded, compared = [], 0
    if not quiet:
        print("  %-4s %-10s %-22s %-22s %s"
              % ("#", "row", "§ 3 why", "rule set", "agree"))
    for n, name, _c1, _c2, why in table:
        if name not in p["cen"]:
            findings.append("§ 3 row %d is %r, which is not an `r1a` row of "
                            "tools/isa-census.tsv" % (n, name))
            continue
        want_cls, want_vis = norm_why(why)
        got_cls, got_vis = classify_census(name, payset, preds)
        wl = (want_cls or "-") + ("" if not want_vis else ", " + want_vis)
        gl = (got_cls or "-") + ("" if not got_vis else ", " + got_vis)
        if got_cls is None:
            excluded.append(name)
            if want_cls is not None:
                findings.append("%s has no payload row and § 3's `why` reads "
                                "%r" % (name, why))
            if not quiet:
                print("  %-4d %-10s %-22s %-22s %s"
                      % (n, name, wl, gl, "EXCLUDED"))
            continue
        compared += 1
        ok = (want_cls, want_vis) == (got_cls, got_vis)
        if not ok:
            findings.append("%s: § 3 says %r, the rule set says %r"
                            % (name, wl, gl))
        if not quiet:
            print("  %-4d %-10s %-22s %-22s %s"
                  % (n, name, wl, gl, "ok" if ok else "DISAGREE"))
    print()
    print("  rows in %s § 3            %3d" % (DOC, len(table)))
    print("  compared                                          %3d" % compared)
    print("  excluded, no payload row                          %3d   %s"
          % (len(excluded), " ".join(sorted(excluded))))
    for e in sorted(excluded):
        print("    %-9s %s" % (e, NO_ROW.get(e, "(undeclared)")))
    print()
    if findings:
        for f in findings:
            print("  FINDING: %s" % f)
        print("RESULT: %d finding(s) over %d compared row(s)"
              % (len(findings), compared))
        return 1
    print("RESULT: 0 findings over %d compared row(s), %d excluded"
          % (compared, len(excluded)))
    return 0


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def _mutate(src, subs, tmp, tag):
    """A copy of a capture with literal substitutions applied."""
    txt = io.open(src, encoding="utf-8", errors="replace").read()
    for a, b in subs:
        if a not in txt:
            raise AssertionError("fixture anchor absent: %r" % a[:50])
        txt = txt.replace(a, b, 1)
    path = os.path.join(tmp, tag)
    with io.open(path + ".tmp", "w", encoding="utf-8", newline="") as fh:
        fh.write(txt)
    os.replace(path + ".tmp", path)
    return path


def self_test():
    n = ok = 0

    def case(label, fn):
        nonlocal n, ok
        n += 1
        try:
            fn()
            ok += 1
            print("  ok    %s" % label)
        except AssertionError as e:
            print("  FAIL  %s -- %s" % (label, e))
        except Exception as e:
            print("  FAIL  %s -- %s: %s" % (label, type(e).__name__, e))

    def refuses(fn, why):
        try:
            fn()
        except Refuse:
            return
        except isapay.Refuse:
            return
        raise AssertionError("did not refuse: %s" % why)

    print("=== emupredict controls ===")
    rows = isapay.load_rows()
    p = population(rows=rows)
    tmpd = tempfile.TemporaryDirectory()
    tmp = tmpd.name

    def c1():
        assert len(p["payload"]) == 75, len(p["payload"])
        assert len(p["cen"]) == 39, len(p["cen"])
        assert len(p["exact"]) == 32, len(p["exact"])
        assert len(p["new_by_group"]) == 12, sorted(p["new_by_group"])
        assert len(p["covered"]) == 44, len(p["covered"])
        assert len(p["outside"]) == 31, len(p["outside"])
        assert sorted(p["new_by_group"]) == sorted(
            "cache10 cache11 cache15 cache19 mfc2 clz clo mul ext ins seb "
            "wsbh".split()), sorted(p["new_by_group"])
    case("C1  the join is 32 exact + 12 by group = 44, and 75 - 44 = 31", c1)

    def c2():
        assert set(CARD_31) == p["outside"], \
            "derived %s, card %s" % (sorted(p["outside"] - set(CARD_31)),
                                     sorted(set(CARD_31) - p["outside"]))
        assert len(CARD_31) == 31 and len(set(CARD_31)) == 31
    case("C2  the 31 derived rows ARE the card § 6.2's 31, as sets", c2)

    def c3():
        # The map is well formed in both directions, and the only census
        # rows with no payload row are the two declared `**none**` cells.
        for k, v in GROUP_MAP.items():
            assert k in p["cen"] and k not in p["payload"], k
            for m in v:
                assert m in p["payload"], (k, m)
        assert sorted(p["cen"] - p["exact"] - set(GROUP_MAP)) == \
            sorted(NO_ROW), sorted(p["cen"] - p["exact"] - set(GROUP_MAP))
        # A naive name join loses twelve and a group join that forgets `madd`
        # is already an exact match double-counts it.  Both are measured here
        # rather than asserted in a comment.
        naive = len(p["exact"])
        assert naive == 32 and 75 - naive == 43, naive
        summed = len(p["exact"]) + sum(len(v) for v in GROUP_MAP.values())
        assert summed == 50, summed   # 32 + 18: `madd` and COP1's five twice
    case("C3  the group map is checked against both tables, and the two "
         "wrong joins give 43 and 50", c3)

    def c4():
        # The parsers are isapay's OBJECTS, not copies of its text.
        assert ARMSDEV is isapay.ROW_RE, "the device regex is not isapay's"
        assert ARMSUSR is isapay.UROW_RE, "the user regex is not isapay's"
        assert ARMSDEV is not ARMSUSR, "one regex is serving both arms"
        refuses(lambda: read_column(COL2, "device", rows),
                "a `PU` capture read on the device arm")
        refuses(lambda: read_column(COL1, "user", rows),
                "a `P4` capture read on the user arm")
    case("C4  the row regexes are isapay's own objects and each arm refuses "
         "the other's capture", c4)

    def c5():
        out = predict_all(COL1, rows=rows)
        assert len(out) == 75, len(out)
        used = {}
        for _r, _v, _val, _rec, pr in out:
            used[pr.rule] = used.get(pr.rule, 0) + 1
        assert sum(used.values()) == 75, used
        assert set(used) == {"R-a", "R-b", "R-c", "X-sync", "X-llsc",
                             "X-priv"}, used
        assert used["X-sync"] == 1 and used["X-llsc"] == 2 \
            and used["X-priv"] == 5, used
        # every non-census row takes an ARM, never an exception
        for r, _v, _val, _rec, pr in out:
            if r["name"] in p["outside"]:
                assert pr.rule in ("R-a", "R-b", "R-c"), (r["name"], pr.rule)
    case("C5  the rule set classifies all 75 rows, each exactly once, and "
         "the 31 outside rows take arms only", c5)

    def c6():
        out = predict_all(COL1, rows=rows)
        t = tally_of([pr.verdict for _r, _v, _val, _rec, pr in out])
        line = summary_line(t, "user", len(out))
        assert line == ("verdict (user arm): 75 row(s), RAN 12, RIGHT 16, "
                        "TRAPS 46, WRONG 1"), line
    case("C6  POSITIVE: predicting from column ① alone gives the card § 6.3 "
         "line, verbatim", c6)

    def c7():
        out = predict_all(COL1, rows=rows)
        t1 = tally_of([v for _r, v, _val, _rec, _p in out])
        t2 = tally_of([pr.verdict for _r, _v, _val, _rec, pr in out])
        assert t1 == {"RAN": 16, "RIGHT": 16, "TRAPS": 42, "WRONG": 1}, t1
        assert t2["RAN"] == t1["RAN"] + 1 - 5, (t1, t2)
        assert t2["TRAPS"] == t1["TRAPS"] - 1 + 5, (t1, t2)
        assert t2["RIGHT"] == t1["RIGHT"] and t2["WRONG"] == t1["WRONG"]
        assert sum(t1.values()) == sum(t2.values()) == 75
    case("C7  and the arithmetic behind it: 16 +1 -5 = 12, 42 -1 +5 = 46, "
         "RIGHT and WRONG untouched", c7)

    def c8():
        # V2 planted.  Without the `sync` exception `sync` falls to R-b and
        # stays a trap, so one row moves the other way.
        exc = default_exceptions()
        del exc["sync"]
        out = predict_all(COL1, rows=rows, exc=exc)
        t = tally_of([pr.verdict for _r, _v, _val, _rec, pr in out])
        line = summary_line(t, "user", len(out))
        assert line == ("verdict (user arm): 75 row(s), RAN 11, RIGHT 16, "
                        "TRAPS 47, WRONG 1"), line
    case("C8  MUTATION: drop the `sync` exception and the predicted line "
         "becomes RAN 11 / TRAPS 47", c8)

    def c9():
        exc = default_exceptions()
        del exc["cache10"]
        out = predict_all(COL1, rows=rows, exc=exc)
        t = tally_of([pr.verdict for _r, _v, _val, _rec, pr in out])
        line = summary_line(t, "user", len(out))
        assert line == ("verdict (user arm): 75 row(s), RAN 13, RIGHT 16, "
                        "TRAPS 45, WRONG 1"), line
    case("C9  MUTATION: drop ONE privilege exception and the line moves by "
         "exactly one row, RAN 13 / TRAPS 45", c9)

    def c10():
        exc = default_exceptions()
        for k in ("cache10", "cache11", "cache15", "cache19", "mflxc0"):
            del exc[k]
        out = predict_all(COL1, rows=rows, exc=exc)
        t = tally_of([pr.verdict for _r, _v, _val, _rec, pr in out])
        assert t == {"RAN": 17, "RIGHT": 16, "TRAPS": 41, "WRONG": 1}, t
    case("C10 MUTATION: drop all five and the five rows move together, "
         "RAN 17 / TRAPS 41", c10)

    def c11():
        bad = _mutate(COL1,
                      [("P4 00000015 sync ", "P4 00000015 syncoid ")],
                      tmp, "badname.log")
        refuses(lambda: read_column(bad, "device", rows),
                "a capture whose name column disagrees with the table")
    case("C11 REFUSE: a row name the payload table does not have", c11)

    def c12():
        cut = _mutate(COL1, [("rlxprobe: rows end", "")], tmp, "noend.log")
        refuses(lambda: read_column(cut, "device", rows),
                "a capture with no `rows end`")
        # and the harder half: rows end present, rows MISSING
        short = io.open(COL1, encoding="utf-8", errors="replace").read()
        short = short.replace(
            "P4 0000004a udi5 ", "XX 0000004a udi5 ", 1)
        path = os.path.join(tmp, "short.log")
        with io.open(path + ".tmp", "w", encoding="utf-8", newline="") as fh:
            fh.write(short)
        os.replace(path + ".tmp", path)
        refuses(lambda: read_column(path, "device", rows),
                "a capture missing one row")
    case("C12 REFUSE: a truncated capture, both by the missing terminator "
         "and by the missing row", c12)

    def c13():
        # ExcCode 13 (Tr).  `teq`'s cause word 0x2000_0028 -> ExcCode 10;
        # 0x20000034 is ExcCode 13.  No arm covers it.
        bad = _mutate(COL1,
                      [("P4 00000032 teq 52340032 00000001 20000028",
                        "P4 00000032 teq 52340032 00000001 20000034")],
                      tmp, "exc13.log")
        refuses(lambda: predict_all(bad, rows=rows),
                "an ExcCode no arm covers")
    case("C13 REFUSE: column ① carrying an ExcCode no arm covers", c13)

    def c14():
        # ExcCode 11 with CE 0 is the ll/sc/mflxc0 shape.  On a row that is
        # NOT an exception row the rule set must refuse: R-c is stated for
        # CE != 0 and there is nothing to apply.
        bad = _mutate(COL1,
                      [("P4 0000001e mfc1 5234001e 00000001 1000002c",
                        "P4 0000001e mfc1 5234001e 00000001 0000002c")],
                      tmp, "ce0.log")
        refuses(lambda: predict_all(bad, rows=rows),
                "ExcCode 11 with CE 0 on a non-exception row")
    case("C14 REFUSE: ExcCode 11 with CE 0, which R-c does not cover", c14)

    def c15():
        # The antecedent guard.  `sync` retiring in column ① means the rule
        # `① ExcCode 10 => ② no signal` has nothing to fire on.
        #
        # The header counters move WITH it, deliberately: a fixture whose
        # `trapped` still said 42 would also trip C16's check, and a case
        # that two guards can pass is a case that pins neither.
        bad = _mutate(COL1,
                      [("P4 00000015 sync 52340015 00000001 00000028",
                        "P4 00000015 sync 52340015 00000000 00000000"),
                       ("rlxprobe: trapped=0000002a",
                        "rlxprobe: trapped=00000029"),
                       ("rlxprobe: ran=00000021", "rlxprobe: ran=00000022")],
                      tmp, "syncran.log")
        refuses(lambda: predict_all(bad, rows=rows),
                "an exception row whose ① fails its rule's antecedent")
    case("C15 REFUSE: an exception row whose column ① violates the "
         "antecedent, rather than applying the consequent", c15)

    def c16():
        bad = _mutate(COL1, [("rlxprobe: trapped=0000002a",
                              "rlxprobe: trapped=0000002b")],
                      tmp, "hdr.log")
        refuses(lambda: predict_all(bad, rows=rows),
                "the payload's own trap counter disagreeing with the rows")
    case("C16 REFUSE: the capture's `rlxprobe: trapped` against the traps "
         "counted from its own printed rows", c16)

    def c17():
        f, obs, lines, _t1, t2p, t2m = compare(COL1, COL2, rows=rows)
        assert len(lines) == 75, len(lines)
        assert f == [], f
        assert t2p == t2m, (t2p, t2m)
        # THE NEGATIVE HALF.  A run that agreed and a run that read nothing
        # both print zero findings; only the row count separates them, and
        # only an injected disagreement shows the comparison can fail.
        bad = _mutate(COL2,
                      [("PU 00000015 sync 52340015 00000000 00000000",
                        "PU 00000015 sync 52340015 00000001 00040080")],
                      tmp, "syncsig.log")
        f2, _o2, l2, _a, _b, _c = compare(COL1, bad, rows=rows)
        assert len(l2) == 75, len(l2)
        assert len(f2) == 2, f2      # the verdict and the signal
        assert all("sync" in x for x in f2), f2
    case("C17 a clean pair is 0 findings over 75 rows AND an injected ② "
         "signal on `sync` is caught -- V2, in anger", c17)

    def c18():
        # The summary format is isapay's.  Capture what `isapay verdict
        # --arm user` prints and require this tool's line to be inside it.
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            isapay.cmd_verdict(rows, COL2, arm="user", quiet=True)
        meas = read_column(COL2, "user", rows)
        mine = summary_line(tally_of([v for _r, v, _val, _rec in meas]),
                            "user", len(meas))
        got = [l for l in buf.getvalue().split("\n")
               if l.startswith("verdict (user arm):")]
        assert got == [mine], (got, mine)
    case("C18 the summary line is byte-identical to the one isapay.py "
         "prints for the same capture", c18)

    def c19():
        rc = None
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_cross(COL1, SURFACE, quiet=True)
        txt = buf.getvalue()
        assert rc == 0, txt
        assert "RESULT: 0 findings over 37 compared row(s), 2 excluded" \
            in txt, txt.strip().split("\n")[-1]
        table = read_surface_table(SURFACE)
        assert len(table) == 39, len(table)
        assert [t[1] for t in table if t[4].strip() in
                ("—", "-")] == ["jalx", "mtlxc0"], \
            [t[1] for t in table]
    case("C19 cross: 39 rows read, 37 compared, 2 excluded, 0 "
         "disagreements", c19)

    def c20():
        assert norm_why("\U0001F534 privilege") == ("privilege", None)
        assert norm_why("same") == ("same", None)
        assert norm_why("\U0001F534 emulation, **invisible**") == \
            ("emulation", "invisible")
        assert norm_why("\U0001F7E2 **emulation, VISIBLE**") == \
            ("emulation", "visible")
        assert norm_why("—") == (None, None)
        refuses(lambda: norm_why("mostly the same"), "an unknown `why` token")
        # and the classification a wrong `why` must be caught by
        surf = os.path.join(tmp, "surface.md")
        txt = io.open(SURFACE, encoding="utf-8").read()
        txt = txt.replace("| \U0001F7E2 **emulation, VISIBLE** |",
                          "| same |", 1)
        with io.open(surf + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(surf + ".tmp", surf)
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_cross(COL1, surf, quiet=True)
        assert rc == 1, buf.getvalue()
        assert "sync:" in buf.getvalue(), buf.getvalue()
    case("C20 the `why` normaliser strips the decorations, refuses an "
         "unknown token, and a wrong cell is reported -- V4", c20)

    def c21():
        # The value side, which a verdict-only comparison cannot see.
        _f, obs, lines, _a, _b, _c = compare(COL1, COL2, rows=rows)
        armed = [l for l in lines if l[1] in ("R-a", "R-b", "R-c")]
        assert len(armed) == 67, len(armed)
        for l in armed:
            assert l[7] == l[8], l
        assert sorted(o[0] for o in obs) == ["mflxc0", "sc"], obs
        # `mflxc0` changed verdict too, so its two values record two
        # different events.  `sc` RETIRED ON BOTH ARMS and still moved, and
        # that is the one a trap/no-trap table cannot see.
        live = [o for o in obs if o[4]]
        assert [o[0] for o in live] == ["sc"], obs
        assert live[0][2] == 0x5A5A0FF2 and live[0][3] == 0xA5A5F00D, live
    case("C21 all 67 rule-covered rows carry the same VALUE on both arms, "
         "and exactly one row retires on both and still moves: `sc`", c21)

    def c22():
        # An absent input must REFUSE (exit 3), never traceback.  An
        # uncaught exception exits 1, and 1 is this tool's code for A
        # FINDING -- so a missing file would read as a refuted rule set.
        import contextlib
        gone = os.path.join(tmp, "not-here.log")
        refuses(lambda: read_column(gone, "device", rows), "a missing capture")
        refuses(lambda: read_surface_table(gone), "a missing § 3 table")
        with contextlib.redirect_stdout(io.StringIO()):
            rcs = [main(["predict", gone]), main(["compare", COL1, gone]),
                   main(["compare", COL1]), main([]),
                   main(["predict", COL2])]
        assert rcs == [3, 3, 3, 3, 3], rcs
    case("C22 REFUSE: an absent input exits 3 and not 1, because 1 is this "
         "tool's code for a finding", c22)

    tmpd.cleanup()
    print("RESULT: %d passed, %d failed" % (ok, n - ok))
    return 0 if ok == n else 1


# Two names so C4 can assert identity rather than equality, which is what
# separates "imported" from "retyped and happens to agree today".
ARMSDEV = isapay.ARMS["device"][0]
ARMSUSR = isapay.ARMS["user"][0]


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mode", nargs="?",
                    choices=["rules", "predict", "compare", "cross"])
    ap.add_argument("col1", nargs="?")
    ap.add_argument("col2", nargs="?")
    ap.add_argument("--col1", dest="col1_opt", default=COL1,
                    help="the column ① capture `rules` and `cross` apply the "
                         "rule set to (default: the committed one)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test()
        if not a.mode:
            ap.print_help()
            return 3
        if a.mode == "rules":
            return cmd_rules(a.col1 or a.col1_opt, a.quiet)
        if a.mode == "cross":
            return cmd_cross(a.col1 or a.col1_opt, SURFACE, a.quiet)
        if a.mode == "predict":
            if not a.col1:
                raise Refuse("predict needs a column ① capture")
            return cmd_predict(a.col1, a.quiet)
        if a.mode == "compare":
            if not a.col1 or not a.col2:
                raise Refuse("compare needs a column ① and a column ② "
                             "capture, in that order")
            return cmd_compare(a.col1, a.col2, a.quiet)
    except Refuse as e:
        print("REFUSED: %s" % e)
        return 3
    except isapay.Refuse as e:
        print("REFUSED: %s" % e)
        return 3
    return 3


if __name__ == "__main__":
    sys.exit(main())
