#!/usr/bin/env python3
"""Re-derive, from this repository's own committed text, every external
implementation source it has cited -- and check `docs/blind-write-ledger.md`
against that.

Why this exists
---------------
``R5`` writes six drivers **blind**, and ``docs/driver-diff.md`` is worth
writing only if that word means something.  ``R5-0`` freezes the claim in a
ledger before the first driver exists, because afterwards *"I had not read it"*
is unverifiable.

**A ledger with no instrument behind it is the claim it was supposed to
replace.**  量, on 2026-09-02, before this file existed: a hand-typed
``grep -ril rlx-time`` over this tree returned **0 files**, and the sentence
about to be written from it was *"this repository has never read the vendor's
timer"*.

That sentence is false, and 🔴 **the grep was not wrong** -- which is the
sharper version of this lesson and it took two passes to reach.
``arch/rlx/kernel/`` carries **both** ``rlx-time.c`` and ``rlx-cevt.c``
(量 2026-09-02, directory listing, no file opened), so the needle named a real
file and **0 was the correct answer**: this repository has never cited
``rlx-time.c``.  What was wrong was the inference.  It **has** cited
``rlx-cevt.c`` -- clock**event** -- and ``notes/vendor-kernel-isa.md:33``
cites it **to the line**, ``:139,226``.

**Zero citations is not zero reading, and a zero on one spelling says nothing
about another.**  ``CLAUDE.md``: *a tool reporting 0 is making a claim.*

So the ledger's completeness is not asserted here, it is **computed**, and the
computation carries a positive control on the very citation that was nearly
missed.

The division of labour, which is the design
-------------------------------------------
* **This tool owns completeness.**  It finds every path-shaped citation of an
  external source in the tracked tree and in ``upstream/``, normalises it,
  assigns it a driver domain, and reports the set.
* **The ledger owns depth and verdict.**  Whether a citation reached the
  *fact* layer (an address, a reset value) or the *decision* layer (divisor
  semantics, wrap handling, bit-field meaning, init order) is a judgement, and
  a judgement is written by a person.
* **``check`` joins them**, RED on a stale ledger (an in-scope path the scan
  finds and the ledger lacks), and since R6b-5 on a depth cell not in DEPTHS
  (LEDGER-3) and a path declared at most ``name`` yet cited by line (LEDGER-4).

That is what makes the ledger survive the gate: writing about a new vendor file
in ``LOG.md`` -- which is how reading gets recorded here -- makes ``check`` fail
until the ledger says what was taken from it.

Where this will fail, stated before it is used
-----------------------------------------------
1. 🔴 **It measures what this repository WROTE DOWN, not what I read.**  A file
   read and never mentioned is invisible to it.  It is a **lower bound** on
   contamination and the ledger says so in its own first section.  What makes
   the bound useful rather than decorative is this project's habit of writing
   greps down -- ``notes/vendor-kernel-isa.md`` is a whole file of them.
2. 🔴 **A path-shaped regex cannot see prose.**  *"the vendor's clockevent
   driver"* names no path.  ``scan --topics`` is the second net: subsystem
   keywords, reported separately and never merged into the path set, because a
   keyword hit is not a citation.
3. ⚠️ **Domain assignment is keyword-based and will be wrong.**  The direction
   is chosen: over-inclusive.  ``bsp`` catches board/platform/setup files
   *whatever* they are named, because a timer is initialised in
   ``boards/rtl8196e/bsp/setup.c`` and nothing in that path says *timer*.  A
   file wrongly in scope costs one judgement; a file wrongly out of scope
   hides contamination.
4. ⚠️ **``upstream/`` is scanned and reported separately, never merged.**  Its
   citations are mine too -- I wrote that project -- but it is pinned at
   ``4d3ff26`` (2026-08-22), so its reading is *history* and the ledger dates
   it as such.  ``git ls-files`` cannot see inside a submodule; it is walked.
5. ⚠️ **``quarantine`` needs ``src-vendor/``**, which is a symlink into
   ``$FWRE_WORK`` and is absent on a runner.  It stands down there with a
   printed skip rather than passing silently.

Usage
-----
    ledgerscan.py scan                      # every citation, by domain
    ledgerscan.py scan --domain timer       # one domain
    ledgerscan.py scan --topics             # the prose net, reported apart
    ledgerscan.py check                     # ledger vs scan; red if stale
    ledgerscan.py quarantine                # the five uncloned ports, still uncloned
    ledgerscan.py --self-test
"""

import argparse
import collections
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = "docs/blind-write-ledger.md"

# --------------------------------------------------------------------------
# what counts as a citation
# --------------------------------------------------------------------------

# A path-shaped reference to a kernel/bootloader source file.  The leading
# alternation is the set of top-level directories a 2.6.30 tree has, plus
# `boards/`, which is where this SoC's BSP lives in the drop that is built.
PATH_RX = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:arch|drivers|include|init|kernel|mm|net|fs|lib|boards|sound|block|"
    r"crypto|security|ipc|bootcode)/"
    r"[A-Za-z0-9_./+-]*?\.(?:c|h|S|dts|dtsi|lds))"
    r"(?![A-Za-z0-9_/-])")

# A line number travelling with a citation: `path.c:139` or `path.c:12-22`.
# Deeper contact than a bare name, and counted separately.
LINENO_RX = re.compile(r"^:(\d+)(?:[-–,]\d+)?")

# 🔴 Paths this tool INVENTS for its own controls.  P6 needs vendor-shaped
# names to test the domain rules with, and four of them name no file that
# exists anywhere -- `rlx-nonexistent-xyz.c` is P3's negative control and says
# so out loud.  Once this file became tracked its own fixtures entered the
# population, and `check` went red demanding the ledger declare four files
# that do not exist.  A ledger that names imaginary files is worse than no
# ledger.
#
# ⚠️ The distinction being drawn is FIXTURE against EXAMPLE, and it is not the
# same as "written by me": `tools/ci-expected.tsv` names a REAL file
# (drivers/input/keyboard/gpio_keys.c) as an example, and that one is declared
# in the ledger as `origin: none` rather than excluded. Only invented paths are
# excluded, and P18d is the control that says they are still invented.
FIXTURE_PATHS = frozenset({
    "arch/rlx/kernel/rlx-csrc.c",          # P6: the clocksource name I guessed
    "arch/rlx/kernel/rlx-nonexistent-xyz.c",   # P3's negative control
    "drivers/gpio/gpio-rtl819x.c",         # P6/P15
    "drivers/leds/leds-rtl819x.c",         # P6/P15
    "drivers/watchdog/rtl_wdt.c",          # P6
    # P15's own, named so a grep of this file cannot mistake them.  P15 needs
    # scan_population to FIND these, so it passes `fixtures=frozenset()` --
    # which is why the set can stay the single owner of "what is invented"
    # without P15 having to keep a second copy.
    "drivers/gpio/gpio-p15-synthetic.c",
    "drivers/watchdog/p15-synthetic.c",
    "drivers/leds/p15-synthetic.c",
    "drivers/input/keyboard/p15-synthetic.c",
    "arch/mips/boot/dts/p15-synthetic.dtsi",
})


# Files that are MINE, living at vendor-shaped paths inside a staged tree.
# Derived from config/rlxfw-src/ rather than listed, so a new file of mine is
# excluded the moment it exists -- and P5 removes the directory to prove the
# exclusion comes from there and is not hardcoded.
def own_sources(root):
    base = os.path.join(root, "config", "rlxfw-src")
    out = set()
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), base).replace("\\", "/")
            out.add(strip_tree_prefix(rel))
    return out


# Prefixes that name a tree rather than a file inside one.  Stripping them is
# what makes `linux-2.6.30/arch/rlx/kernel/setup.c` and
# `arch/rlx/kernel/setup.c` one path instead of two.
TREE_PREFIXES = (
    "src-vendor/rtl819x-toolchain/", "src-vendor/wecb-vz-gpl/",
    "src-vendor/saturn49-wecb/", "src-vendor/openwrt-rtk/",
    "src-vendor/", "rtl819x/", "linux-2.6.30/", "linux-2.6.30.x/",
)


def strip_tree_prefix(path):
    p = path.replace("\\", "/")
    changed = True
    while changed:
        changed = False
        for pre in TREE_PREFIXES:
            if p.startswith(pre):
                p = p[len(pre):]
                changed = True
    return p


# --------------------------------------------------------------------------
# domain assignment -- over-inclusive on purpose (see failure note 3)
# --------------------------------------------------------------------------

# Order matters: the first matching rule wins.  `dt` and `bsp` sit at the top
# because both are CROSS-DOMAIN -- a device tree and a board file each describe
# every peripheral, so neither can be assigned to one driver.
#
# 🔴 `dt` was added on the tool's FIRST real run, which is the only reason it
# is here: `arch/mips/boot/dts/realtek/rtl8196e.dtsi` -- shibajee's device tree
# for a TOTOLINK board on this SoC, and the single most relevant prior art to
# R5's `D2` -- landed in `out-of-scope`, because its path says `boot/dts` and
# every bsp needle wanted `board`. That is failure note 3 firing in the
# dangerous direction on the first file it mattered for.
DOMAIN_RULES = [
    ("dt",      (".dts", ".dtsi", "/dts/", "bindings", "devicetree",
                 "of_device", "dtc")),
    # ⚠️ `/board` and not a bare `board`: 量, the bare needle put
    # `drivers/input/keyboard/gpio_keys.c` in `bsp`, because *keyboard*
    # contains it. Caught by P6/P15, which is what those two are for.
    ("bsp",     ("bsp/", "/boards/", "boards/", "platform", "/prom.", "prom.c",
                 "setup.c", "machine", "/board")),
    ("timer",   ("cevt", "csrc", "clocksource", "clockevent", "timex",
                 "time.c", "time.h", "/time/", "timer", "sched_clock")),
    ("irq",     ("irq", "interrupt", "gic", "vec.c")),
    # ⚠️ `keys` before `gpio`, and the order is a judgement rather than an
    # accident: `drivers/input/keyboard/gpio_keys.c` matches both, and it is
    # R5-8's driver, not R5-4's. The general rule is *more specific first*;
    # P6 pins both halves, since a `keys` rule that swallowed
    # `drivers/gpio/gpio-rtl819x.c` would be the same defect mirrored.
    ("keys",    ("gpio_keys", "gpio-keys", "keyboard", "input/", "button")),
    ("gpio",    ("gpio", "pinctrl", "pinmux")),
    ("spi_mtd", ("spi", "mtd", "flash", "nor", "chips/")),
    ("wdt",     ("wdt", "watchdog")),
    ("led",     ("led",)),
]

# The domains a driver in R5 is written for.  A citation outside these is
# listed but needs no per-file verdict in the ledger.
IN_SCOPE = ("dt", "bsp", "timer", "irq", "gpio", "spi_mtd", "wdt", "led",
            "keys")


def domain_of(path):
    low = path.lower()
    for name, needles in DOMAIN_RULES:
        for n in needles:
            if n in low:
                return name
    return "out-of-scope"


# --------------------------------------------------------------------------
# populations
# --------------------------------------------------------------------------

# Text this project writes.  A binary or a capture is not prose and a citation
# inside one would be an artefact of the device, not a record of reading.
TEXT_EXT = (".md", ".tsv", ".json", ".py", ".sh", ".yml", ".yaml", ".txt",
            ".c", ".h", ".toml", ".cfg", ".conf")


def tracked_files(root):
    """git ls-files, minus upstream/ (walked separately) and minus the
    submodule gitlink."""
    r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                       text=True)
    if r.returncode != 0:
        raise RuntimeError("git ls-files failed: %s" % r.stderr.strip())
    return [p for p in r.stdout.splitlines()
            if p and not p.startswith("upstream")]


def upstream_files(root):
    """git ls-files cannot see inside a submodule, so it is walked."""
    base = os.path.join(root, "upstream")
    out = []
    if not os.path.isdir(base):
        return out
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            out.append(os.path.relpath(os.path.join(dp, f), root)
                       .replace("\\", "/"))
    return out


def read_text(root, rel):
    p = os.path.join(root, rel)
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (OSError, IsADirectoryError):
        return ""


class Citation(object):
    __slots__ = ("path", "citing", "line", "with_lineno")

    def __init__(self, path, citing, line, with_lineno):
        self.path, self.citing = path, citing
        self.line, self.with_lineno = line, with_lineno


def scan_population(root, paths, exclude, fixtures=None):
    """-> {normalised path: [Citation]}

    `fixtures` defaults to FIXTURE_PATHS; P15 passes an empty set, because it
    is the control that requires the domain rules to fire on names that are
    themselves fixtures.
    """
    if fixtures is None:
        fixtures = FIXTURE_PATHS
    hits = collections.defaultdict(list)
    for rel in paths:
        if not rel.endswith(TEXT_EXT):
            continue
        txt = read_text(root, rel)
        if not txt:
            continue
        for lineno, line in enumerate(txt.splitlines(), 1):
            for m in PATH_RX.finditer(line):
                norm = strip_tree_prefix(m.group(1))
                if norm in exclude or norm in fixtures:
                    continue
                ln = bool(LINENO_RX.match(line[m.end():]))
                hits[norm].append(Citation(norm, rel, lineno, ln))
    return hits


# --------------------------------------------------------------------------
# the prose net -- reported apart, never merged (failure note 2)
# --------------------------------------------------------------------------

TOPICS = {
    "timer": ("clocksource", "clockevent", "clock_event", "cevt", "csrc",
              "plat_time_init", "sched_clock", "cycle_t", "mult/shift"),
    "irq": ("irq_domain", "irqchip", "set_irq_chip", "handle_level_irq",
            "GIMR", "GISR", "IRR1"),
    "gpio": ("gpio_chip", "gpiolib", "gpio_request", "PABCD"),
    "spi_mtd": ("mtd_info", "map_info", "spi_nor", "mtd_partition", "SFCR"),
    "wdt": ("watchdog_device", "WDTCNR", "wdt_ping"),
    "led": ("led_classdev", "leds-gpio"),
    "keys": ("gpio_keys", "input_dev"),
}


def scan_topics(root, paths):
    hits = collections.defaultdict(lambda: collections.defaultdict(list))
    for rel in paths:
        if not rel.endswith(TEXT_EXT):
            continue
        txt = read_text(root, rel)
        if not txt:
            continue
        low = txt.lower()
        for dom, words in TOPICS.items():
            for w in words:
                if w.lower() in low:
                    hits[dom][w].append(rel)
    return hits


# --------------------------------------------------------------------------
# the ledger
# --------------------------------------------------------------------------

# A ledger row declares one path.  The path is the first code span on a table
# row; anything else AFTER THAT CELL is prose for a human.
#
# 🔴 The regex requires the code span to be the WHOLE first cell -- `| `p` |`
# and not `| `p` 🆕 |`.  量 2026-09-03: a row written the second way is not
# counted as a declaration and `check` stays red naming the path it just
# declared, which reads as the tool being wrong.  It is not silent -- the red
# names the file -- but the docstring said "anything else on the row", which
# is one word too wide and cost a round trip.
LEDGER_PATH_RX = re.compile(r"^\|\s*`([^`]+)`\s*\|")

# The depth vocabulary, CLOSED since R6b-5 (LEDGER-3): a row whose depth cell
# does not BEGIN with one of these words is RED, row by row.  `scan` derives
# only `name` and `line`; `none` and `artefact` (§ 4.3.1: a binary of mine
# holding the vendor's code) are declared.  No `full`: see ledger_row_list.
DEPTHS = ("none", "name", "line", "artefact")
DEPTH_RANK = {"none": 0, "name": 1, "artefact": 1, "line": 2}


def ledger_paths(root, rel=LEDGER):
    """The paths the ledger declares.

    A row's first code span is the declaration -- but the ledger has other
    tables whose first column is also a code span (the quarantine's tree ids,
    the summary's domain names). Only spans that are themselves path-shaped
    count, so `gpio` in a summary row is not read as a declaration of a file
    called gpio. P16 is the control.
    """
    d = ledger_rows(root, rel)
    return None if d is None else set(d)


def _depth_word(row):
    """The depth word in a ledger row, or None.  Split out so P19e can test the
    extraction without building a repository around it.

    🔴 THE FIRST WORD, and that is the whole of it.  The first draft iterated
    the DEPTHS vocabulary and returned the first member present -- refuted on
    the real ledger's first run: `arch/rlx/kernel/rlx-time.c`'s cell reads `🔴
    **line** (was **none — nothing taken**)`, and vocabulary order returned the
    struck-through HISTORY.  The second returned the leftmost vocabulary word,
    so `🔄 **lnie** (was **name**)` read as `name` (R6b-5, P20e).  The current
    claim is written first, so the cell's first word must BE a depth or the
    cell is unreadable.  P19f is the rlx-time.c cell, verbatim.
    """
    cells = row.split("|")
    if len(cells) <= 2:
        return None
    m = re.search(r"[a-z0-9]+", cells[2].lower())   # markup is not a word
    w = m.group(0) if m else None
    return w if w in DEPTHS else None


def ledger_rows(root, rel=LEDGER):
    """-> {path: declared depth or None}.  LEDGER-2.

    Every row, read by ledger_row_list (defined below render_scan, so that no
    line cited above it moves), merged per PATH.  A path declared twice keeps
    the DEEPER claim: two rows for one file is two sections having read it,
    and the ledger's depth for the file is the most that was taken.  That
    merge is what makes LEDGER-4 a statement about FILES rather than rows.

    🔴 It is also why LEDGER-3's refusal is made per ROW, before this: the
    merge drops an unreadable row whenever a readable one names the same
    path.  量 2026-09-26 over the 34 committed versions of the ledger: 2,352
    row readings, 13 distinct depth cells, two outside the old three words
    -- `**full**` (two rows, 137 commits) and `**`artefact`**` (one row, 440
    commits, and hidden by this merge for 384 of them).  The merge's tie rule
    -- an equal rank keeps the FIRST row -- is unchanged from LEDGER-2's
    version of this function, which read and merged in one loop; P16 and
    P19e-g pin the reading, P20b the per-row refusal.
    """
    lst = ledger_row_list(root, rel)
    if lst is None:
        return None
    out = {}
    for _i, p, depth, _cell in lst:
        # a path declared twice keeps the deeper claim; an unreadable row
        # (None, rank -1) never replaces a readable one
        if p in out and DEPTH_RANK.get(out[p], -1) >= DEPTH_RANK.get(depth, -1):
            continue
        out[p] = depth
    return out


# --------------------------------------------------------------------------
# quarantine -- the ports that must stay uncloned until R5-9
# --------------------------------------------------------------------------

# The fourth element is the RELEASE.  None means the tree must stay absent.  A
# string is the record of a deliberate clone: step, date, and the commit that
# pre-registered the reading.  A release is not a suppression -- see
# render_quarantine, where a release recorded against an ABSENT tree is RED,
# so the list cannot accrete entries nobody is using.
QUARANTINE = [
    ("shibajee-linux-rtl8196e", "src-vendor/shibajee-linux-rtl8196e",
     "R5 (driver-diff): the closest prior art to these six drivers",
     "R5-9, 2026-09-10, pre-registered in 161862e at 15:26:24Z, "
     "cloned 15:27:49Z; docs/driver-diff.md sections 1 and 2"),
    ("ggbruno-openwrt", "src-vendor/ggbruno-openwrt",
     "R10b: the furthest anyone has taken this SoC on a modern kernel",
     "R5-9, 2026-09-10, same commit and same clone run; branch Realtek "
     "fetched 15:51:10Z after ls-remote showed master carries no RTL8196E"),
    ("openwrt-rtk", "src-vendor/openwrt-rtk",
     "R6, R10a/b: Realtek's own OpenWrt SDK, carries arch/rlx", None),
    ("utessel-edimax", "src-vendor/edimax",
     "R6: a second independent rtl819x network driver", None),
    ("vankel-rtl819x-sdk", "src-vendor/rtl819x-sdk-3.4.9.3",
     "R10a: SDK 3.4.9.3 on Linux 3.10", None),
]

# A release record has to look like one.  An empty string, or a bare word,
# cannot be allowed to silence the guard: the record is the evidence.
def release_is_wellformed(rec):
    if not isinstance(rec, str) or len(rec) < 20:
        return False
    return ("R5-9" in rec or "R6" in rec or "R10" in rec) and "20" in rec


def quarantine_state(root, table=None):
    """-> [(id, dest, present, why, released)].  `present` is None when
    src-vendor/ itself is absent, which is a runner and not a breach."""
    tbl = QUARANTINE if table is None else table
    sv = os.path.join(root, "src-vendor")
    if not os.path.isdir(sv):
        return [(i, d, None, w, r) for i, d, w, r in tbl]
    return [(i, d, os.path.exists(os.path.join(root, d)), w, r)
            for i, d, w, r in tbl]


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def by_domain(hits):
    out = collections.defaultdict(dict)
    for p, cites in hits.items():
        out[domain_of(p)][p] = cites
    return out


def render_scan(root, only=None, show_topics=False, out=sys.stdout):
    own = own_sources(root)
    tf, uf = tracked_files(root), upstream_files(root)
    mine = scan_population(root, tf, own)
    ups = scan_population(root, uf, own)

    print("ledgerscan -- citations of external implementation sources",
          file=out)
    print("  population: %d tracked (excl upstream/), %d in upstream/"
          % (len(tf), len(uf)), file=out)
    print("  excluded as mine (from config/rlxfw-src/): %s"
          % (", ".join(sorted(own)) or "(none)"), file=out)
    print(file=out)

    dom_mine, dom_ups = by_domain(mine), by_domain(ups)
    order = list(IN_SCOPE) + ["out-of-scope"]
    total_in_scope = 0
    for dom in order:
        if only and dom != only:
            continue
        paths = dom_mine.get(dom, {})
        if not paths and dom not in dom_ups:
            continue
        n_cit = sum(len(v) for v in paths.values())
        print("=== %s: %d path(s), %d citation(s)" % (dom, len(paths), n_cit),
              file=out)
        if dom in IN_SCOPE:
            total_in_scope += len(paths)
        for p in sorted(paths, key=lambda k: -len(paths[k])):
            cites = paths[p]
            withln = [c for c in cites if c.with_lineno]
            files = sorted(set(c.citing for c in cites))
            depth = "line" if withln else "name"
            print("  %-4s %3d  %-50s  %d file(s): %s"
                  % (depth, len(cites), p, len(files),
                     ", ".join(files[:3]) + (" …" if len(files) > 3 else "")),
                  file=out)
            if withln:
                ex = withln[0]
                print("            first with a line number: %s:%d"
                      % (ex.citing, ex.line), file=out)
        only_up = {p: v for p, v in dom_ups.get(dom, {}).items()
                   if p not in paths}
        if only_up:
            print("  -- cited ONLY in upstream/ (pinned 4d3ff26, 2026-08-22):",
                  file=out)
            for p in sorted(only_up):
                print("     %3d  %s" % (len(only_up[p]), p), file=out)
        print(file=out)

    print("in-scope paths (the ledger must cover these): %d" % total_in_scope,
          file=out)

    if show_topics:
        print(file=out)
        print("=== the prose net (keyword hits, NOT citations) ===", file=out)
        th = scan_topics(root, tf)
        for dom in sorted(th):
            for w in sorted(th[dom]):
                fs = th[dom][w]
                print("  %-8s %-18s %d file(s): %s"
                      % (dom, w, len(fs), ", ".join(sorted(fs)[:3])), file=out)
    return mine, ups


# LEDGER-3 (R6b-5, 2026-09-26).  The vocabulary is CLOSED and a row whose
# depth cell does not BEGIN with a word of DEPTHS is RED -- until then it was
# skipped, so a row reading `ful1` passed exactly as the two `**full**` rows
# did for 137 commits.  Adding `artefact` changes the word read out of none of
# the other 2,305 row readings in the ledger's history, and reading the FIRST
# word rather than the leftmost vocabulary word changes none of the 13
# distinct depth cells ever committed (P20e is why it had to change at all).
#
# 🔴 `full` is refused ON PURPOSE.  "The whole file" is an EXTENT, and no
# citation can witness an extent: `scan` cannot derive it, and render_check's
# comparison runs one way only, so a `full` cell would be the one word in the
# ledger that nothing produces and nothing checks.  The ledger records extent
# as a RANGE in the row's prose (§ 2.1), and R5-8 moved the only two `full`
# cells ever committed to `line` on exactly that ground.  Adding it is a design
# change with a reopening condition -- an instrument that derives extent, e.g.
# the union of cited ranges against the file's length in the built drop -- not
# a table edit.
def ledger_row_list(root, rel=LEDGER):
    """-> [(line number in the ledger, path, depth or None, depth cell)] for
    every row, in order and NOT merged.  A row's first code span is its path;
    its second cell is the depth it CLAIMS -- prose, not a token (`line`,
    `🔴 **line**`, `**`artefact`**`), so its FIRST word is taken (_depth_word)
    and a cell whose first word is not in DEPTHS yields None."""
    txt = read_text(root, rel)
    if not txt:
        return None
    out = []
    for i, line in enumerate(txt.splitlines(), 1):
        m = LEDGER_PATH_RX.match(line)
        if not m:
            continue
        span = m.group(1).strip()
        if not PATH_RX.fullmatch(span):
            continue
        # cells[0] is empty (the leading pipe), cells[1] is the path.
        cells = line.split("|")
        out.append((i, strip_tree_prefix(span), _depth_word(line),
                    cells[2].strip() if len(cells) > 2 else ""))
    return out


def render_check(root, out=sys.stdout):
    """-> exit code.  Red when the ledger does not cover the scan, when a
    row's depth word is not in the vocabulary (LEDGER-3, since R6b-5), or
    when a path the ledger declares at most `name` is cited by line
    (LEDGER-4, since R6b-5; why that one is a rule and not the report
    LEDGER-2 made it is written at the comparison below)."""
    own = own_sources(root)
    mine = scan_population(root, tracked_files(root), own)
    ups = scan_population(root, upstream_files(root), own)
    seen = set(mine) | set(ups)
    in_scope = {p for p in seen if domain_of(p) in IN_SCOPE}

    rowlist = ledger_row_list(root)
    if rowlist is None:
        print("RED  %s does not exist. The ledger is the deliverable of R5-0 "
              "and check has nothing to compare against." % LEDGER, file=out)
        return 2
    rows = ledger_rows(root)
    declared = set(rows)

    missing = sorted(in_scope - declared)
    stale = sorted(declared - seen)

    # LEDGER-2.  Until 2026-09-04 this function compared PATH SETS and never
    # looked at the depth column, so a row could under-declare what it took and
    # the gate stayed green -- 量 2026-09-03: `check` said ok on 32 in-scope
    # paths while `scan --domain timer` read `kernel/time/jiffies.c` as `line`
    # against a row declaring `name`.  Depth is the boundary between *saw the
    # interface* and *read the code*, which is the whole reason the ledger
    # exists.
    #
    # LEDGER-2 REPORTED this and did not judge it, on an argument: `scan`'s
    # depth is the deepest citation anywhere, a row's is what one section
    # took, and "a row may honestly say `name` about its own reading of a file
    # another section later quoted by line".
    #
    # LEDGER-4 (R6b-5, 2026-09-26) OVERRULES that argument for one direction
    # -- name-or-less below a `path:NN` -- and says so rather than claiming to
    # keep it.  Where the deeper reading has its own ledger row, nothing
    # changes: ledger_rows() merges every row for a path into its deepest
    # claim, so the honest section's `name` row is never compared (P21c; 量
    # at 873a471 five paths carry rows of different depths and the merge
    # absorbs all five).  Where the deeper reading sits only OUTSIDE the
    # ledger -- the argument's literal case -- this is now RED, because the
    # ledger's own § 2 sets depth by the tool and § 2.1 counts a cited range
    # as read: the remedy is a row for the section that took the lines, and
    # the `name` row stays as it was.
    #
    # 量 over all 477 commits since the ledger existed: name-below-line fired
    # in four episodes and all four were under-declarations -- `jiffies.c` and
    # `jiffies.h` closed by deepening their own section's row, `rtl_gpio.c` by
    # adding § 4.10's `line` row beside § 4.9's artefact.  The fourth,
    # `arch/rlx/kernel/irq.c`, read at `:176-180,224` on 2026-09-19 by R6-3
    # while § 4.4's row said `name` / NOT OPENED, printed on every run for 111
    # commits and was read on none; R6-3's own row (§ 4.13) closes it.  No RED
    # in `check`'s history outlived three commits.
    #
    # 🔴 Where this is most likely to be refuted first: a symlink alias.
    # `arch/rlx/bsp/*` and `boards/rtl8196e/bsp/*` are the same files, and
    # the ledger declares some of them at different depths under the two
    # names; a `path:NN` written through the shallower alias fires although
    # the file is declared `line` (0 such citations at 873a471).  The remedy
    # then is a NAMED exemption with a control that goes red when it is no
    # longer needed -- not a return to report-only.
    #
    # What stays a REPORT: `none` against `name`.  The ledger is in the
    # population and names every path it declares, so a `none` row is always
    # cited by name -- by the ledger -- and no `none` row could be green.
    #
    # 🔴 NOT SEEN, so a green here is not read as more: line numbers written
    # apart from the path (`gpio_keys.c` ... `:62`, which is how the reading
    # LEDGER-4 was opened for was written -- widening the match to a detached
    # `:NN` on a line naming one path added one episode in 477 commits, and it
    # was a `:476-477` about another file beside a sentence saying the path was
    # NOT opened); a bare file name with a line (`gpio_keys.c:62`, the form
    # the same reading took in SPEC.md FW-56, and the vendor NIC tree's
    # `rtl_nic.c:NN`) and a tree-prefixed path, neither of which PATH_RX
    # matches; a reading committed together with its row's correction; and
    # any change of depth within `line` (LEDGER-3's first half, ⊘).
    obs = {}
    for p in sorted(declared & seen):
        cites = (mine.get(p) or []) + (ups.get(p) or [])
        obs[p] = "line" if any(c.with_lineno for c in cites) else "name"
    shallow = [(p, rows[p], obs[p]) for p in sorted(obs)
               if rows[p] is not None
               and DEPTH_RANK[obs[p]] > DEPTH_RANK[rows[p]]]
    under = [s for s in shallow if s[2] == "line"]
    shallow = [s for s in shallow if s[2] != "line"]
    unreadable = [(i, p, cell) for i, p, d, cell in rowlist if d is None]

    print("ledgerscan check", file=out)
    print("  in-scope paths found : %d" % len(in_scope), file=out)
    print("  paths declared       : %d" % len(declared), file=out)
    print("  depth compared on    : %d (declared and cited)" % len(obs),
          file=out)

    rc = 0
    if missing:
        rc = 1
        print(file=out)
        print("RED  %d in-scope path(s) cited by this repository and NOT in "
              "the ledger:" % len(missing), file=out)
        for p in missing:
            where = (mine.get(p) or ups.get(p))[0]
            print("       %-50s  %-8s  first: %s:%d"
                  % (p, domain_of(p), where.citing, where.line), file=out)
        print("     A ledger that does not cover what the tree cites is not a "
              "boundary. Add a row with what was taken, or say the citation "
              "reached no layer.", file=out)
    if stale:
        print(file=out)
        print("⚠️  %d declared path(s) no longer cited anywhere. Not an error "
              "-- a ledger is append-only and a removed citation does not "
              "unread the file:" % len(stale), file=out)
        for p in stale:
            print("       %s" % p, file=out)
    if under:
        rc = 1
        print(file=out)
        print("RED  LEDGER-4: %d path(s) the ledger declares at most `name` "
              "while this repository cites them BY LINE:" % len(under),
              file=out)
        for p, decl, got in under:
            cites = (mine.get(p) or []) + (ups.get(p) or [])
            ex = next((c for c in cites if c.with_lineno), None)
            print("       %-50s  ledger=%-8s  scan=%-4s  %s"
                  % (p, decl, got,
                     ("e.g. %s:%d" % (ex.citing, ex.line)) if ex else ""),
                  file=out)
        print("     § 2.1 counts a cited range as read, so the file's deepest "
              "row must say `line`: deepen the row, or add one for the "
              "section that took the lines, saying what was taken. Deleting "
              "the citation to turn this green is the fix the ledger rejects "
              "by name.", file=out)
    if shallow:
        print(file=out)
        print("⚠️  LEDGER-2: %d row(s) declare `none` for a path the "
              "repository names. Reported, not judged: the ledger names every "
              "path it declares, so a rule here could never be green:"
              % len(shallow), file=out)
        for p, decl, got in shallow:
            print("       %-50s  ledger=%-4s  scan=%-4s" % (p, decl, got),
                  file=out)
    if unreadable:
        rc = 1
        print(file=out)
        print("RED  LEDGER-3: %d ledger row(s) whose depth cell does not "
              "begin with one of %s:" % (len(unreadable), "/".join(DEPTHS)),
              file=out)
        for i, p, cell in unreadable:
            print("       %s:%d  %-50s  %r" % (LEDGER, i, p, cell[:40]),
                  file=out)
        print("     An unrecognised depth used to be skipped, so `ful1` "
              "passed the way `full` did. `full` is not a depth: write "
              "`line` and the range (§ 2.1).", file=out)
    if rc == 0:
        print(file=out)
        print("ok   the ledger covers every in-scope citation", file=out)
    return rc


def render_quarantine(root, out=sys.stdout, table=None):
    st = quarantine_state(root, table=table)
    print("ledgerscan quarantine -- ports that must stay uncloned, and the "
          "ones deliberately released", file=out)
    if all(p is None for _i, _d, p, _w, _r in st):
        print("  (skipped: src-vendor/ is absent -- this is a runner, not a "
              "breach, %d port(s))" % len(st), file=out)
        return 0
    rc = 0
    for i, d, present, why, released in st:
        if present and not released:
            rc = 1
            print("  RED  %-28s IS PRESENT at %s" % (i, d), file=out)
            print("       %s" % why, file=out)
            print("       R5-0's ledger records this tree as unread. A clone "
                  "is not a reading, but it is the end of the claim that "
                  "reading it was impossible.", file=out)
        elif present and not release_is_wellformed(released):
            rc = 1
            print("  RED  %-28s released with a record that is not one"
                  % i, file=out)
            print("       a release must name the step, the date and the "
                  "commit; this one is %r" % (released,), file=out)
        elif present:
            print("  ok   %-28s RELEASED and present (%s)" % (i, d), file=out)
            print("       %s" % released, file=out)
        elif released:
            rc = 1
            print("  RED  %-28s released but ABSENT at %s" % (i, d), file=out)
            print("       a release records a clone that happened. This tree "
                  "is not here, so either the release is stale or the tree "
                  "was removed without the record following it.", file=out)
            print("       %s" % released, file=out)
        else:
            print("  ok   %-28s absent (%s)" % (i, d), file=out)
    return rc


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

def _tmp_root(tmp, files):
    """A synthetic repository: a git tree with the given {rel: text}."""
    os.makedirs(os.path.join(tmp, "config", "rlxfw-src"), exist_ok=True)
    for rel, txt in files.items():
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt)
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True,
                   capture_output=True)
    return tmp


def self_test():
    import tempfile
    ok = fail = 0

    def ck(rid, cond, detail=""):
        nonlocal ok, fail
        # Two leading spaces then at least two more: `ci-census.py`'s OK_RE
        # is `^ {2}ok\s{2,}` and its UNPARSABLE_RE fires on anything close to
        # it that does not match, so a suite that invents its own spacing is
        # counted as zero cases while looking green.
        if cond:
            ok += 1
            print("  ok    %s" % rid)
        else:
            fail += 1
            print("  FAIL  %s  %s" % (rid, detail))

    # ---- P1: the positive control, and it is the citation that was nearly
    # missed on 2026-09-02 by a hand-typed grep for the wrong needle.
    own = own_sources(ROOT)
    mine = scan_population(ROOT, tracked_files(ROOT), own)
    cevt = "arch/rlx/kernel/rlx-cevt.c"
    ck("P1  the vendor timer citation is found (rlx-cevt.c)",
       cevt in mine,
       "not found; a scanner that misses this reproduces the 2026-09-02 error")
    if cevt in mine:
        f = sorted(set(c.citing for c in mine[cevt]))
        ck("P1b it is found in notes/vendor-kernel-isa.md",
           "notes/vendor-kernel-isa.md" in f, str(f))
        ck("P1c its line number is seen as depth",
           any(c.with_lineno for c in mine[cevt]),
           "cited as `rlx-cevt.c:139,226` -- the depth flag must fire")

    # ---- P2: a second real citation, in a different domain, that a
    # timer-shaped scanner would miss.
    flash = "drivers/mtd/maps/rtl819x_flash.c"
    ck("P2  the vendor MTD map citation is found", flash in mine)
    ck("P2b it lands in spi_mtd", domain_of(flash) == "spi_mtd",
       domain_of(flash))

    # ---- P3: the negative.  A path that is not cited must not be reported.
    ck("P3  an uncited path is absent",
       "arch/rlx/kernel/rlx-nonexistent-xyz.c" not in mine)

    # ---- P4: liveness.  A scanner that reports nothing is broken, not clean.
    ck("P4  the population is not empty", len(tracked_files(ROOT)) > 100,
       str(len(tracked_files(ROOT))))
    ck("P4b citations were found at all", len(mine) > 20, str(len(mine)))

    # ---- P5: the exclusion comes from config/rlxfw-src/, not from a list.
    # Remove the directory in a synthetic tree and my own file must REAPPEAR
    # as an external citation.
    with tempfile.TemporaryDirectory() as tmp:
        r = _tmp_root(tmp, {
            "notes/x.md": "see `arch/rlx/kernel/rlxfw_mark.c` and "
                          "`arch/rlx/kernel/rlx-cevt.c:139`\n",
            "config/rlxfw-src/linux-2.6.30/arch/rlx/kernel/rlxfw_mark.c":
                "/* mine */\n",
        })
        with_own = scan_population(r, tracked_files(r), own_sources(r))
        ck("P5  a file of mine is excluded",
           "arch/rlx/kernel/rlxfw_mark.c" not in with_own,
           str(sorted(with_own)))
        ck("P5b a vendor file beside it is NOT excluded",
           "arch/rlx/kernel/rlx-cevt.c" in with_own, str(sorted(with_own)))
        without = scan_population(r, tracked_files(r), set())
        ck("P5c with the exclusion set empty it reappears",
           "arch/rlx/kernel/rlxfw_mark.c" in without,
           "the exclusion must come from config/rlxfw-src/, not a constant")

    # ---- P6: domain assignment, including the over-inclusive bsp rule that
    # exists because a timer is initialised in a file whose path says `setup`.
    for path, want in (
            ("arch/rlx/kernel/rlx-cevt.c", "timer"),
            ("arch/rlx/kernel/rlx-csrc.c", "timer"),
            ("boards/rtl8196e/bsp/setup.c", "bsp"),
            ("arch/rlx/kernel/irq_vec.c", "irq"),
            ("drivers/mtd/maps/rtl819x_flash.c", "spi_mtd"),
            ("drivers/watchdog/rtl_wdt.c", "wdt"),
            ("drivers/gpio/gpio-rtl819x.c", "gpio"),
            ("drivers/leds/leds-rtl819x.c", "led"),
            ("drivers/input/keyboard/gpio_keys.c", "keys"),
            # 🔴 the row the first real run added.  A device tree is the prior
            # art R5's D2 is written against, and this path landed in
            # out-of-scope until `dt` existed.
            ("arch/mips/boot/dts/realtek/rtl8196e.dtsi", "dt"),
            ("arch/mips/boot/dts/realtek/rtl8196e_totolink_n100re.dts", "dt"),
            ("Documentation/devicetree/bindings/timer/x.yaml", "dt"),
            ("init/main.c", "out-of-scope"),
            ("kernel/bounds.c", "out-of-scope")):
        ck("P6  %-46s -> %s" % (path, want), domain_of(path) == want,
           domain_of(path))

    # ---- P7: check goes RED on a ledger missing one in-scope path, and the
    # path it names is the one removed.  A checker that cannot fail is not a
    # checker.
    with tempfile.TemporaryDirectory() as tmp:
        led = ("# ledger\n\n| path | depth | origin | what was taken |\n"
               "|---|---|---|---|\n"
               "| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | the string only |\n")
        r = _tmp_root(tmp, {
            "notes/x.md": "`arch/rlx/kernel/rlx-cevt.c:139` and "
                          "`drivers/mtd/maps/rtl819x_flash.c:62-73`\n",
            LEDGER: led,
        })
        import io
        buf = io.StringIO()
        rc = render_check(r, out=buf)
        txt = buf.getvalue()
        ck("P7  check is RED when a cited path is not declared", rc == 1, txt)
        ck("P7b it names the missing path",
           "drivers/mtd/maps/rtl819x_flash.c" in txt, txt)
        ck("P7c it does NOT name the declared one as missing",
           "rlx-cevt.c" not in txt.split("NOT in the ledger:")[-1], txt)

    # ---- P8: the negative on P7.  With the row added, the same tree is green.
    with tempfile.TemporaryDirectory() as tmp:
        led = ("# ledger\n\n| path | depth | origin | what was taken |\n"
               "|---|---|---|---|\n"
               "| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | the string only |\n"
               "| `drivers/mtd/maps/rtl819x_flash.c` | line | vendor | lines 62-73 |\n")
        r = _tmp_root(tmp, {
            "notes/x.md": "`arch/rlx/kernel/rlx-cevt.c:139` and "
                          "`drivers/mtd/maps/rtl819x_flash.c:62-73`\n",
            LEDGER: led,
        })
        import io
        buf = io.StringIO()
        rc = render_check(r, out=buf)
        ck("P8  check is green once the row is added", rc == 0, buf.getvalue())

    # ---- P19: LEDGER-2, and since R6b-5 LEDGER-4.  `check` compared PATH
    # SETS and never read the depth column until 2026-09-04 (量 2026-09-03,
    # `kernel/time/jiffies.c` declared `name` while the tree cited it by
    # line).  LEDGER-2 REPORTED the difference; LEDGER-4 makes name-below-line
    # RED, because the one episode after the report shipped
    # (`arch/rlx/kernel/irq.c`, 2026-09-19) printed on 111 commits and was
    # never read.  Both halves are controls: the refusal, and equal silent.
    for decl, want_report, cid in (("name", True, "P19a"),
                                   ("line", False, "P19b")):
        with tempfile.TemporaryDirectory() as tmp:
            led = ("# ledger\n\n| path | depth | origin | what was taken |\n"
                   "|---|---|---|---|\n"
                   "| `arch/rlx/kernel/rlx-cevt.c` | %s | vendor | x |\n"
                   % decl)
            r = _tmp_root(tmp, {
                "notes/x.md": "`arch/rlx/kernel/rlx-cevt.c:139`\n",
                LEDGER: led,
            })
            import io as _io
            buf = _io.StringIO()
            rc = render_check(r, out=buf)
            txt = buf.getvalue()
            got = "LEDGER-4" in txt
            ck("%s a row declaring %-4s against a cited line number: "
               "%s" % (cid, decl, "RED" if want_report else "silent"),
               got is want_report, txt)
            ck("%sx and the exit code says so" % cid,
               rc == (1 if want_report else 0), "rc=%d" % rc)

    # ---- P19c: OVER-declaration is not the defect and must not be reported.
    # A row may honestly say `line` about its own reading while the repository
    # happens to cite the file only by name; the ledger's depth is what that
    # section took, not what the scanner can see.
    with tempfile.TemporaryDirectory() as tmp:
        led = ("# ledger\n\n| path | depth | origin | what was taken |\n"
               "|---|---|---|---|\n"
               "| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | read in full |\n")
        r = _tmp_root(tmp, {
            "notes/x.md": "`arch/rlx/kernel/rlx-cevt.c` was opened\n",
            LEDGER: led,
        })
        import io as _io
        buf = _io.StringIO()
        rc = render_check(r, out=buf)
        ck("P19c over-declaration (ledger=line, scan=name) is NOT reported",
           "LEDGER-2" not in buf.getvalue()
           and "LEDGER-4" not in buf.getvalue() and rc == 0, buf.getvalue())

    # ---- P19d: a depth cell naming no word of the vocabulary.  Reported as
    # skipped until R6b-5; LEDGER-3 makes it RED.  It is still not GUESSED at
    # -- defaulting to `name` would manufacture a LEDGER-4 hit out of a
    # formatting choice -- so the refusal names the row, not a depth.
    with tempfile.TemporaryDirectory() as tmp:
        led = ("# ledger\n\n| path | depth | origin | what was taken |\n"
               "|---|---|---|---|\n"
               "| `arch/rlx/kernel/rlx-cevt.c` | ??? | vendor | x |\n")
        r = _tmp_root(tmp, {
            "notes/x.md": "`arch/rlx/kernel/rlx-cevt.c:139`\n",
            LEDGER: led,
        })
        import io as _io
        buf = _io.StringIO()
        rc = render_check(r, out=buf)
        txt = buf.getvalue()
        ck("P19d an unreadable depth cell is RED (LEDGER-3), not guessed at",
           "LEDGER-3" in txt and "does not begin with one of" in txt
           and "LEDGER-4" not in txt and rc == 1, txt)

    # ---- P19e: the decoration the real ledger actually uses.  Its rows carry
    # `🔴 **line**`, not a bare word, so a matcher that required the whole cell
    # to equal the token would read every emphasised row as unknown.
    ck("P19e a decorated depth cell is read",
       _depth_word("| `a/b.c` | \U0001f534 **line** | vendor | x |") == "line",
       _depth_word("| `a/b.c` | \U0001f534 **line** | vendor | x |"))

    # ---- P19f: the cell that refuted the first draft, verbatim from the real
    # ledger.  A cell carrying a corrected depth AND the depth it replaced must
    # read as the correction; a vocabulary-ordered match returned `none` here
    # and reported a row that had just been fixed.
    _real = ("| `arch/rlx/kernel/rlx-time.c` | \U0001f534 **line** "
             "(was **none — nothing taken**) | vendor | opened in full |")
    ck("P19f a cell holding `line (was none)` reads as line, not none",
       _depth_word(_real) == "line", _depth_word(_real))
    ck("P19g and the reverse spelling still reads left to right",
       _depth_word("| `a/b.c` | **none** (was **line**) | vendor | x |")
       == "none",
       _depth_word("| `a/b.c` | **none** (was **line**) | vendor | x |"))

    # ---- P20 / P21: LEDGER-3 and LEDGER-4 (R6b-5, 2026-09-26).
    def _check_with(rows_md, notes):
        with tempfile.TemporaryDirectory() as tmp_:
            led_ = ("# ledger\n\n| path | depth | origin | what was taken |\n"
                    "|---|---|---|---|\n" + rows_md)
            r_ = _tmp_root(tmp_, {"notes/x.md": notes, LEDGER: led_})
            import io as _io
            b_ = _io.StringIO()
            rc_ = render_check(r_, out=b_)
            return rc_, b_.getvalue()

    # P20a -- a misspelt depth.  Skipped until R6b-5, exactly as `full` was.
    rc, txt = _check_with(
        "| `arch/rlx/kernel/rlx-cevt.c` | ful1 | vendor | x |\n",
        "`arch/rlx/kernel/rlx-cevt.c:139`\n")
    ck("P20a a misspelt depth (`ful1`) is RED and names the ledger line",
       rc == 1 and "LEDGER-3" in txt and "%s:5" % LEDGER in txt, txt)
    # P20b -- per ROW: HEAD's merge dropped an unreadable row whenever a
    # readable one named the same path, unreported (the real `artefact` row,
    # 384 commits).
    rc, txt = _check_with(
        "| `arch/rlx/kernel/rlx-cevt.c` | line | vendor | x |\n"
        "| `arch/rlx/kernel/rlx-cevt.c` | ful1 | vendor | y |\n",
        "`arch/rlx/kernel/rlx-cevt.c:139`\n")
    ck("P20b an unreadable row beside a readable one for the same path is RED",
       rc == 1 and "%s:6" % LEDGER in txt, txt)
    # P20c -- the real ledger's `artefact` cell, verbatim.  § 4.3.1 defines
    # the word, and a vocabulary without it makes that row RED on HEAD.
    _art = "| `drivers/char/rtl_gpio.c` | **`artefact`** | vendor | x |"
    ck("P20c the ledger's own `artefact` cell reads as artefact",
       _depth_word(_art) == "artefact", _depth_word(_art))
    rc, txt = _check_with(
        _art + "\n| `drivers/char/rtl_gpio.c` | line | vendor | y |\n",
        "`drivers/char/rtl_gpio.c:2178`\n")
    ck("P20c2 and beside a `line` row for a line-cited file it is green",
       rc == 0, txt)
    # P20d -- the cell the real ledger carried from 48a7a2a to cfd47ce, 137
    # commits, verbatim.  `full` stays refused: extent is a range (§ 2.1).
    rc, txt = _check_with(
        "| `arch/rlx/include/asm/gpio.h` | **full** | vendor | 6 lines, "
        "`#include <gpio.h>`. Read to confirm the mach- header above is the "
        "one that is reached |\n",
        "`arch/rlx/include/asm/gpio.h`\n")
    ck("P20d the real `**full**` cell of 2026-09-06..10 is RED",
       rc == 1 and "LEDGER-3" in txt, txt)
    # P20e -- the FIRST word, not the leftmost vocabulary word.  The ledger
    # writes history AFTER the current claim (P19f), so reading the leftmost
    # vocabulary word let a misspelt claim pass as its own history, and a
    # `full` cell pass as `line` if the prose after it said "line".  Both
    # notes cite by NAME only, so a reader that took `name`/`line` out of
    # the prose would go green here -- the mutant K9 is that reader.
    rc, txt = _check_with(
        "| `arch/rlx/kernel/rlx-cevt.c` | \U0001f504 **lnie** (was **name**) "
        "| vendor | x |\n", "`arch/rlx/kernel/rlx-cevt.c`\n")
    ck("P20e a misspelt current word before a history word is RED",
       rc == 1 and "LEDGER-3" in txt, txt)
    rc, txt = _check_with(
        "| `arch/rlx/include/asm/gpio.h` | **full** -- every line of it "
        "| vendor | x |\n", "`arch/rlx/include/asm/gpio.h`\n")
    ck("P20e2 `full` followed by the word `line` is RED, not read as line",
       rc == 1 and "LEDGER-3" in txt, txt)
    # P20f -- case is folded, so `**Line**` is the word `line`.  Unpinned
    # until R6b-5's review: a reader without .lower() passed all 98 others.
    _cap = "| `a/b.c` | **Line** | vendor | x |"
    ck("P20f a capitalised depth word reads as the word (`**Line**`)",
       _depth_word(_cap) == "line", _depth_word(_cap))

    # P21a -- LEDGER-4's own row, VERBATIM as it read at d64ee2f^.  The
    # citation beside it is SYNTHETIC: 量, no commit before R6b-5 held
    # `gpio_keys.c` by line after its full path -- the reading was written as
    # detached `:62` spans, in the commit that deepened the row -- so the
    # control LEDGER-4 named cannot come from history.  It is built at run
    # time, so this file's own text does not become that citation.
    _gkcite = "`drivers/input/keyboard/gpio_keys.c" + ":62`\n"
    _gk = ("| `drivers/input/keyboard/gpio_keys.c` | name | **none — an "
           "example** | `tools/ci-expected.tsv:232`, inside this ledger's own "
           "instrument row, describing the classification bug where "
           "*keyboard* contains *board*. **Nothing was read.** The file is "
           "mainline Linux and has never been opened here |")
    rc, txt = _check_with(_gk + "\n", _gkcite)
    ck("P21a LEDGER-4's own row, `name` against a `path:NN`, is RED",
       rc == 1 and "LEDGER-4" in txt, txt)
    ck("P21a2 and it names the path and the citing line",
       "drivers/input/keyboard/gpio_keys.c" in txt.split("LEDGER-4")[-1]
       and "notes/x.md:1" in txt, txt)
    rc, txt = _check_with(
        _gk.replace("| name |", "| \U0001f504 **line** |", 1) + "\n",
        _gkcite)
    ck("P21b the same row deepened to `line` is green", rc == 0, txt)
    # P21c -- the case LEDGER-2's argument protects, PERMITTED: one section's
    # `name` row and another's `line` row for one file, the shape of the real
    # ledger's mtdchar.c pair.  The merge keeps the deeper claim.
    rc, txt = _check_with(
        "| `drivers/mtd/mtdchar.c` | name | generic | the minor convention |\n"
        "| `drivers/mtd/mtdchar.c` | **line** | generic | 73 and 94 |\n",
        "`drivers/mtd/mtdchar.c:73`\n")
    ck("P21c a `name` row beside a `line` row for a line-cited file is green",
       rc == 0 and "LEDGER-4" not in txt, txt)
    # P21d -- `none` against a citation by name stays a REPORT: the ledger's
    # own row names the path, so no `none` row could be green under a rule.
    rc, txt = _check_with(
        "| `drivers/leds/rtl819x-leds-board.c` | none | none | x |\n", "\n")
    ck("P21d `none` against the ledger's own naming is reported, rc 0",
       rc == 0 and "LEDGER-2" in txt and "LEDGER-4" not in txt, txt)
    # P21e -- an `artefact`-only path cited by source line: e1f8543's shape,
    # one commit, before § 4.10 added the `line` row for rtl_gpio.c.
    rc, txt = _check_with(_art + "\n", "`drivers/char/rtl_gpio.c:2178`\n")
    ck("P21e an `artefact`-only row against a `path:NN` is RED",
       rc == 1 and "LEDGER-4" in txt, txt)
    # P21f -- the rule reads `path:NN` only.  A detached `:62` on the path's
    # own line is not depth: widening to it added one episode in 477 commits,
    # and that one was false.
    rc, txt = _check_with(_gk + "\n",
                          "`drivers/input/keyboard/gpio_keys.c` at `:62`\n")
    ck("P21f a detached `:62` is not read as a line citation",
       rc == 0 and "LEDGER-4" not in txt, txt)

    # ---- P9: a missing ledger is red, and it is a different red from P7 --
    # nothing to compare against, not a gap in the comparison.
    with tempfile.TemporaryDirectory() as tmp:
        r = _tmp_root(tmp, {"notes/x.md": "`arch/rlx/kernel/rlx-cevt.c`\n"})
        import io
        buf = io.StringIO()
        rc = render_check(r, out=buf)
        ck("P9  a missing ledger is rc=2, not rc=1", rc == 2, buf.getvalue())

    # ---- P10: tree-prefix normalisation.  The same file cited three ways is
    # one path, or the ledger would need a row per spelling.
    for raw in ("linux-2.6.30/arch/rlx/kernel/setup.c",
                "src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/setup.c",
                "arch/rlx/kernel/setup.c"):
        ck("P10 %-62s normalises" % raw,
           strip_tree_prefix(raw) == "arch/rlx/kernel/setup.c",
           strip_tree_prefix(raw))

    # ---- P11: the prose net finds a subsystem word that names no path, which
    # is the class failure note 2 exists for.
    with tempfile.TemporaryDirectory() as tmp:
        r = _tmp_root(tmp, {
            "notes/x.md": "the vendor registers a clocksource here\n"})
        th = scan_topics(r, tracked_files(r))
        ck("P11 a keyword with no path is caught by the prose net",
           "clocksource" in th.get("timer", {}), str(dict(th)))
        cites = scan_population(r, tracked_files(r), set())
        ck("P11b and it is NOT counted as a citation", len(cites) == 0,
           str(sorted(cites)))

    # ---- P12: quarantine reads the filesystem, and its skip is a printed
    # line rather than a silent pass.
    with tempfile.TemporaryDirectory() as tmp:
        import io
        buf = io.StringIO()
        rc = render_quarantine(tmp, out=buf)
        ck("P12 quarantine stands down without src-vendor/", rc == 0)
        ck("P12b and says so", "skipped" in buf.getvalue(), buf.getvalue())
        # The four states are driven on a SYNTHETIC table.  On the real one
        # two ports are RELEASED (R5-9, 2026-09-10), so a fixture that only
        # creates a directory would go red for the reverse control rather than
        # for the breach it names -- and a control that passes for the wrong
        # reason is not a control.
        REL = ("R5-9, 2026-09-10, pre-registered in 161862e; a record with a "
               "step, a date and a commit")
        held = [("held-port", "src-vendor/held-port", "why", None)]
        rel = [("rel-port", "src-vendor/rel-port", "why", REL)]
        badrec = [("bad-port", "src-vendor/bad-port", "why", "yes")]

        os.makedirs(os.path.join(tmp, "src-vendor", "held-port"))
        buf = io.StringIO()
        rc = render_quarantine(tmp, out=buf, table=held)
        ck("P12c a cloned port with NO release is RED", rc == 1,
           buf.getvalue())
        ck("P12d and it is named", "held-port" in buf.getvalue(),
           buf.getvalue())

        os.makedirs(os.path.join(tmp, "src-vendor", "rel-port"))
        buf = io.StringIO()
        rc = render_quarantine(tmp, out=buf, table=rel)
        ck("P12e a cloned port WITH a release is ok", rc == 0,
           buf.getvalue())
        ck("P12e2 and the record is printed, not just the verdict",
           "161862e" in buf.getvalue(), buf.getvalue())

        buf = io.StringIO()
        rc = render_quarantine(tmp, out=buf,
                               table=[("gone-port", "src-vendor/gone-port",
                                       "why", REL)])
        ck("P12f REVERSE: a release recorded against an ABSENT tree is RED",
           rc == 1, buf.getvalue())

        os.makedirs(os.path.join(tmp, "src-vendor", "bad-port"))
        buf = io.StringIO()
        rc = render_quarantine(tmp, out=buf, table=badrec)
        ck("P12g a release record that is not one cannot silence the guard",
           rc == 1, buf.getvalue())

    # ---- P16: a ledger row whose first code span is not path-shaped is not a
    # declaration.  The real ledger has three such tables (the quarantine's
    # tree ids, the summary's domain names, the two-layer table), and reading
    # `gpio` as a declared file would make `check` green for the wrong reason.
    with tempfile.TemporaryDirectory() as tmp:
        led = ("| path | what |\n|---|---|\n"
               "| `arch/rlx/kernel/rlx-cevt.c` | timer |\n"
               "| `gpio` | a domain name, not a path |\n"
               "| `shibajee-linux-rtl8196e` | a tree id, not a path |\n")
        r = _tmp_root(tmp, {LEDGER: led})
        got = ledger_paths(r)
        ck("P16 only path-shaped spans are read as declarations",
           got == {"arch/rlx/kernel/rlx-cevt.c"}, str(sorted(got)))

    # ---- P14: the whole of `scan` runs, end to end.  Every control above
    # this one calls a helper; `main()` returns on --self-test before
    # render_scan is ever reached, which is the structural hole
    # test-spec-check-mutants and test-leakscan-mutants each found the hard
    # way in this repository.  A defect anywhere in the reporting path -- the
    # domain grouping, the depth column, the in-scope total -- is invisible
    # without this.
    with tempfile.TemporaryDirectory() as tmp:
        r = _tmp_root(tmp, {
            "notes/x.md":
                "`arch/rlx/kernel/rlx-cevt.c:139` and "
                "`drivers/mtd/maps/rtl819x_flash.c` and "
                "`init/main.c`\n",
        })
        import io
        buf = io.StringIO()
        render_scan(r, out=buf)
        txt = buf.getvalue()
        ck("P14 scan renders the timer domain", "=== timer:" in txt, txt)
        ck("P14b it renders the depth column",
           "line" in txt and "name" in txt, txt)
        ck("P14c out-of-scope is rendered but not counted in scope",
           "=== out-of-scope:" in txt
           and "in-scope paths (the ledger must cover these): 2" in txt, txt)
        ck("P14d the population line is printed",
           "population:" in txt, txt)

    # ---- P15: the liveness control on the FOUR EMPTY DOMAINS.  量 on the
    # first real run: gpio, wdt, led and keys each returned **0 paths**, and
    # that zero is the ledger's strongest claim -- it says this repository has
    # never cited anyone's implementation of those four.  A zero from a rule
    # that cannot fire says nothing at all, so each rule is made to fire here
    # on a synthetic tree.
    # ⚠️ These paths are NOT the ones P6 uses. P6 tests `domain_of` directly,
    # which does not consult FIXTURE_PATHS; P15 goes through
    # `scan_population`, which does -- so reusing P6's names here made all
    # three rows fail the moment the fixture set arrived. Naming them
    # `p15-synthetic` also makes them unmistakable in a grep of this file.
    with tempfile.TemporaryDirectory() as tmp:
        r = _tmp_root(tmp, {
            "notes/x.md":
                "`drivers/gpio/gpio-p15-synthetic.c` "
                "`drivers/watchdog/p15-synthetic.c` "
                "`drivers/leds/p15-synthetic.c` "
                "`drivers/input/keyboard/p15-synthetic.c` "
                "`arch/mips/boot/dts/p15-synthetic.dtsi`\n",
        })
        found = scan_population(r, tracked_files(r), set(),
                                fixtures=frozenset())
        got = {domain_of(p) for p in found}
        for dom in ("gpio", "wdt", "led", "keys", "dt"):
            ck("P15 %-4s is reported when it IS cited" % dom, dom in got,
               "domains seen: %s" % sorted(got))
        # P15b -- the negative half, and its FIRST version claimed the wrong
        # thing.  It asserted that gpio/wdt/led/keys are empty on the real
        # tree, which is the LEDGER's claim and not the tool's: the tool
        # cannot tell a citation from an example, and on 2026-09-02 this row
        # went red because `tools/ci-expected.tsv` -- describing this very
        # classification bug -- names `drivers/input/keyboard/gpio_keys.c`.
        # Rewriting that prose to make a checker green would be hiding it, so
        # the ledger declares the path instead and this control now asserts
        # what a control can: that the four rules are SPECIFIC, i.e. they do
        # not swallow paths that plainly belong elsewhere.
        for path in ("init/main.c", "kernel/bounds.c",
                     "arch/rlx/kernel/traps.c", "drivers/mtd/mtdchar.c",
                     "arch/rlx/mm/cache-rlx.c", "kernel/sched_clock.c"):
            ck("P15b %-28s is not gpio/wdt/led/keys" % path,
               domain_of(path) not in ("gpio", "wdt", "led", "keys"),
               domain_of(path))

        # P17 -- the population includes tools/, deliberately: a vendor path
        # written into a tool's docstring or into ci-expected.tsv IS a
        # mention, and the ledger would rather classify one too many than
        # miss one. This is the control that says so out loud.
        with tempfile.TemporaryDirectory() as tmp17:
            r17 = _tmp_root(tmp17, {
                "tools/x-expected.tsv":
                    "suite\t1\t-\t0\tsee `arch/rlx/kernel/rlx-cevt.c`\n"})
            got17 = scan_population(r17, tracked_files(r17), set())
            ck("P17 a path inside tools/ is a citation, not invisible",
               "arch/rlx/kernel/rlx-cevt.c" in got17, str(sorted(got17)))

    # ---- P18: the fixture set.  It exists because this file's own controls
    # need vendor-shaped names, and once the file was tracked those names
    # entered the population and `check` demanded the ledger declare four
    # files that do not exist.  Excluding them is a hole, so it is fenced:
    for fx in FIXTURE_PATHS:
        ck("P18  %-38s is in this tool's own source" % fx,
           fx in open(__file__, encoding="utf-8").read(), fx)
    ck("P18b fixtures are absent from the real scan",
       not (FIXTURE_PATHS & set(mine)),
       str(sorted(FIXTURE_PATHS & set(mine))))
    # the negative half: a REAL vendor path is not swept up by the exclusion
    ck("P18c a real vendor path is still reported",
       "arch/rlx/kernel/rlx-cevt.c" in mine)
    # and the distinction the set is drawn on: an EXAMPLE naming a real file
    # is NOT excluded -- it is declared in the ledger instead.
    ck("P18c2 an example naming a real file is not in the fixture set",
       "drivers/input/keyboard/gpio_keys.c" not in FIXTURE_PATHS)

    # ---- P18d: 🔴 the control that keeps P18 honest, and it needs the drop.
    # A fixture is INVENTED; if one of these ever names a real file, excluding
    # it stops being harmless and starts hiding a citation.  量 2026-09-02,
    # names only, nothing opened: all five absent from the built drop -- and
    # the same listing is what found that `arch/rlx/kernel/` carries BOTH
    # rlx-cevt.c and rlx-time.c.
    drop = os.path.join(ROOT, "src-vendor", "rtl819x-toolchain",
                        "linux-2.6.30")
    if os.path.isdir(drop):
        real = sorted(f for f in FIXTURE_PATHS
                      if os.path.exists(os.path.join(drop, f)))
        ck("P18d every fixture path is still invented (absent from the drop)",
           not real, "these now EXIST and must leave the set: %s" % real)
    else:
        print("  skip  P18d every fixture path is still invented "
              "(needs the GPL drop)")

    # ---- P13: this table's own five entries are the five SOURCES.json marks
    # `fetch: later`.  A port added there and not here is a silent gap, and
    # this is the check that would have caught it.
    import json
    with open(os.path.join(ROOT, "SOURCES.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    later = {e["id"] for e in src["source_trees"] if e.get("fetch") == "later"}
    ck("P13 quarantine == SOURCES.json `fetch: later` UNION the released "
       "(a tree stops being `later` the moment R5-9 clones it, and it must "
       "stay in the list because that is where its release record lives)",
       later | {i for i, _d, _w, r in QUARANTINE if r}
       == {i for i, _d, _w, _r in QUARANTINE},
       "SOURCES.json later: %s  released: %s  QUARANTINE: %s"
       % (sorted(later),
          sorted(i for i, _d, _w, r in QUARANTINE if r),
          sorted(i for i, _d, _w, _r in QUARANTINE)))

    print()
    print("%d passed, %d failed" % (ok, fail))
    return 1 if fail else 0


# --------------------------------------------------------------------------

def main(argv):
    ap = argparse.ArgumentParser(prog="ledgerscan")
    ap.add_argument("action", nargs="?",
                    choices=["scan", "check", "quarantine"])
    ap.add_argument("--domain", default=None, choices=list(IN_SCOPE) +
                    ["out-of-scope"])
    ap.add_argument("--topics", action="store_true",
                    help="also run the prose net, reported apart")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if a.action == "scan":
        render_scan(ROOT, only=a.domain, show_topics=a.topics)
        return 0
    if a.action == "check":
        return render_check(ROOT)
    if a.action == "quarantine":
        return render_quarantine(ROOT)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
