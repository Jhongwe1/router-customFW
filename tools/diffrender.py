#!/usr/bin/env python3
"""diffrender -- renders `docs/differential.md` from `R9-1`'s register.

`R9-8` asks for "four columns with 機制類別 as primary key, the five
uncontrolled-variable classes in the header, and the held items absent", and
its DoD names the refusals:

    the renderer refuses a mechanism outside the closed set, an unresolving
    evidence link, and 「我的設計修好了這條」, each shown firing on a planted
    row; no content from any of the thirteen held ids appears, at class level
    or below.

`R9-0` adds the fourth: a planted row saying the design fixed the case.  The
gate fails if any published row lacks ④, or if the renderer accepts any of
those planted rows -- and all four must be shown firing before any real row
renders, which is what `--self-test` is.

WHAT THIS TOOL RENDERS, AND WHY THE ROW IS A GROUP AND NOT A CASE
=================================================================
量 over `config/fix-cases.toml`: ②③④ are IDENTICAL across all rows sharing an
`anchor` -- one distinct value each, for all twelve anchors.  That is what the
register's `anchor` field is for ("so a correction to an anchor is one edit and
not 141").  So the published row is the pair (`mechanism_class`, `anchor`): 量
16 such groups over 141 register rows, each carrying ①②③④ exactly once.

This is also what makes the held items absent rather than redacted.  A
published cell is ANCHOR text plus COUNTS; no per-row cell -- no `title`, no
`residual`, no `refutation` -- is ever written.  A held row therefore reaches
the document as a number and nothing else.  The alternative, publishing 141
rows with the held ones' text suppressed, would have put the renderer in the
business of redacting prose, and `R9-8`'s own "most likely wrong" column says
the failure mode is a class-level row that is in substance a named
reproduction.

THE GUARDS
==========
  `D1`  `mechanism_class` is in the closed set ⟨架構性, 有界化, 服務不存在,
        不適用, 平台限制⟩.  FIVE, not four: `平台限制` was added by
        `PROGRESS.md`'s `R9` re-specification on 2026-10-04.  ⚠️
        `tools/fixcases.py`'s `CLASSES` still holds four, so a `平台限制` row
        would pass here and be refused there; `P1` below is the control that
        says this renderer can represent the class, and the register carrying
        none of them is a reading about the register, not about the renderer.
  `D2`  every evidence link in published text resolves.  Three kinds, because
        the register cites in three ways:
          `D2a` a repository path (a slash and a known extension) must exist.
          `D2b` a `SPEC.md` row id must be in `SPEC.md`.  PREFIX-GATED: the
                prefix set is derived from `SPEC.md` itself (量 17 prefixes,
                781 ids), so `FC-016` and `V1-NMAP` are not treated as SPEC
                citations at all while `FW-999` is caught.  The gate is
                derived and not hard-coded, which is its own control: if
                `VDR` (量 3 citations, no SPEC row today) ever becomes a SPEC
                prefix, those ids start being checked with no edit here.
          `D2c` a `` `docs/x.md` § N `` citation must resolve to a heading in
                that file.
        A line citation is NOT checked here: `citecheck` owns those, and
        `CLAUDE.md` says to cite by id.
  `D3`  no published text asserts that the design fixed the case.
        THE PATTERN CLASS, and why it is not a grep for one literal: the claim
        has three parts -- a SUBJECT that is rlxfw or its design or the first
        person, a REPAIR verb, and an OBJECT that deictically points at the
        case ("this one", 「這條」, "the case").  `D3` matches the three token
        classes inside one sentence, in either language, so it fires on
        「我的設計修好了這條」 and equally on 「rlxfw 的設計把這一條拿掉了」
        and on "our design fixes this case", none of which share a literal
        with the DoD's sentence.  The DoD's sentence is the degenerate member
        of that class and is also listed, so the verdict `tools/fixcases.py`
        `C9` gives on the same population is reproduced rather than replaced.
        `D3` additionally fires STRUCTURALLY: a repair word in a cell whose
        group publishes no `win` is an unevidenced repair claim whatever its
        grammar.
  `D4`  no row published `win` sits on a ④ reading that opens 未定.  量: the
        register has 17 `win` rows and 0 of them read 未定, and
        `tools/fixcases.py` `C7` already refuses it at the register.  It is
        repeated here because this tool can be pointed at any register and
        `R9-0`'s DoD asks the renderer itself to refuse.
  `D5`  THE FIFTH GUARD, and the gate's hardest: no content from any of the
        thirteen held ids reaches the document, at class level or below.

`D5`: WHAT "CONTENT" MEANS OPERATIONALLY
========================================
The thirteen held ids are 讀 `upstream/docs/disclosure.md` at the pin: `D-3`,
`D-4`, `D-9` … `D-19`.  量 over the register: its held rows name TWELVE of them
-- `D-11` is named by no row at all.  So a guard that trusted `held = true`
would be blind to one of the thirteen, and `D5` is therefore not keyed on the
flag alone.

Content is one of five things, each a property of the TEXT ABOUT TO BE
WRITTEN and not of the register:

  `D5a` ENDPOINT   a path or prefix the vendor's server routes, or a document
                   name it serves.
  `D5b` PARAMETER  a vendor form, MIB or NVRAM symbol: `form[A-Z]…`,
                   `apmib_get`/`apmib_set`, or a SHOUTING_SNAKE symbol of two
                   or more words.
  `D5c` PAYLOAD    a literal that would be sent: a shell metacharacter, a
                   command substitution, an encoded traversal or a NUL.
  `D5d` VERB       an HTTP method next to a path.
  `D5e` REPRODUCTION  two or more of the four above in one sentence, an
                   imperative sequence, or a reproduction artefact's name.
                   This is the one `R9-8` names as the likely failure: a row
                   written at class level that is in substance a recipe.

SCOPE -- the side condition that makes `D5` a held-id rule and not general
hygiene.  The strict scan runs on a published block when ANY of:
  (i)   its group contains a row with `held = true`;
  (ii)  its text names one of the thirteen ids;
  (iii) the block is prose this tool itself wrote AND names one of the ids.
Blocks outside that scope keep their detail.  量 2026-10-04 that is not a
nominal distinction: the anchors `I-LOADER` (`0x000000`, `0x005FFF`) and
`I-STRUCT` (`formSysCmd`, `0x00C000`, `SYSCMD_SELECT`) publish exactly this
kind of token and hold NO held row, so they render in full -- while the six
anchors that do hold one (`I-CUT`, `I-PHYS`, `I-PORT`, `I-SRC-DNS`,
`I-SRC-HTTP`, `I-VC`) 量 carry zero such tokens, which is why the guard reads
0 on the real register.

A GUARD READING 0 IS MAKING A CLAIM, so the exemption has a control that goes
red when it stops being needed: `M10` assigns a held row to `I-STRUCT` and
requires `D5` to fire on the same anchor text that `P5` requires it to permit.
The exemption is by anchor membership, never by date and never by a token
list, and it is swept both ways.

Usage
-----
    tools/diffrender.py render [--out docs/differential.md]
    tools/diffrender.py check          # build and guard, write nothing
    tools/diffrender.py --self-test
    (--register, --probes, --root override the defaults)
"""
import re
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

TOOL = Path(__file__).resolve()
ROOT = TOOL.parent.parent
CLASSES = ("架構性", "有界化", "服務不存在", "不適用", "平台限制")
UNDET = "未定"
HELD_IDS = ("D-3", "D-4", "D-9", "D-10", "D-11", "D-12", "D-13", "D-14", "D-15",
            "D-16", "D-17", "D-18", "D-19")
PUBLISH_ORDER = ("win", "surface-absent", "not comparable", UNDET)
# ②③④ are read off the anchor; these are the only register fields published.
ANCHOR_CELLS = ("vendor_evidence", "rlxfw_evidence", "opposite_check",
                "opposite_check_reading", "same_instrument")


class Refused(Exception):
    """A refusal with a reason.  Never a traceback."""


# --------------------------------------------------------------------------
# D2: link resolution
# --------------------------------------------------------------------------
PATH_RX = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_.+-]+)+"
                     r"\.(?:md|toml|tsv|py|sh|c|h|json|log))`")
# deliberately outside this tree, or generated
PATH_SKIP = ("plan/", "upstream/reports/", "$FWRE_WORK")
# This tool cites itself in the document's first paragraph, and before it is
# committed that path does not resolve under `--root`.  Resolving the
# SELF-citation against `__file__` instead is the real value -- the tool is
# running, so the file exists -- rather than a skip entry that would also hide
# a genuine typo in another tool's name.
SELF_REL = f"{TOOL.parent.name}/{TOOL.name}"
SPEC_ROW_RX = re.compile(r"^\*{0,2}`?([A-Z]{2,3}-\d{2,3}[a-z]?)`?\*{0,2}(?:\s.*)?$")
CITED_ID_RX = re.compile(r"`([A-Z]{2,3}-\d{1,3}[a-z]?)`")
SECTION_RX = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_.+-]+)*\.md)`"
                        r"\s*§\s*([0-9]+(?:\.[0-9]+)?)")

# --------------------------------------------------------------------------
# D3: the repair claim, as three token classes rather than one literal
# --------------------------------------------------------------------------
D3_SUBJ = r"(?:我的設計|我們的設計|我|rlxfw(?:'s)?(?:\s+design)?|our\s+design|this\s+design|the\s+design)"
# ⚠️ MEASURED: `close[sd]?` was in this class and 量 fired on the real register's
# `I-PORT` ④ cell, where `closed` describes a closed TCP port.  A closed port is
# not a repair, so the token left the class; every verb that remains is a claim
# that something was made good.
D3_FIX = (r"(?:修好|修掉|修正|修復|解決|拿掉|消除|fixe[sd]|fixed|repair(?:s|ed)?"
          r"|solve[sd]?|remove[sd]?|eliminate[sd]?|mitigate[sd]?)")
# ⚠️ MEASURED: a bare `it` was in this class and 量 fired on the same cell.  A
# pronoun is not a pointer at THE CASE, so the conjunction now takes only
# explicit case-deictics -- and `D3_VERB_OBJ` keeps "fixes it" by requiring the
# pronoun to sit directly after the repair verb, which is the shape that makes
# the pronoun a claim rather than a word.
D3_OBJ = r"(?:這一?條|這個案例|這一項|本案|this\s+(?:one|case|row|defect|issue)|the\s+case)"
D3_VERB_OBJ = re.compile(rf"{D3_FIX}\s*(?:it|this|這一?[條個項])\b")
# The three token classes are matched INDEPENDENTLY inside one sentence, in any
# order.  ⚠️ MEASURED: the first form required the order subject -> verb ->
# object and 量 missed 「rlxfw 的設計已經把這一條消除了」, because the 把
# construction puts the object before the verb.  An order-sensitive pattern was
# testing English word order, not the claim.
D3_PARTS = (("subject", re.compile(D3_SUBJ)), ("repair verb", re.compile(D3_FIX)),
            ("deictic object", re.compile(D3_OBJ)))
# the DoD's own sentence, kept as the degenerate member so `fixcases` `C9`'s
# verdicts on this population are reproduced and not replaced
D3_LITERALS = ("我的設計修好了這條", "my design fixes this", "this proves",
               "rlxfw is more secure")
# The structural half: a SUBJECT coupled to a repair verb, with no deictic
# object needed, in a group that publishes no win.  ⚠️ MEASURED FIRST, and the
# first form of this rule was wrong: a bare repair word fired on
# `notes/httpd.md`'s "one fixed 404 document", where `fixed` is an adjective
# meaning constant.  Requiring the subject keeps the rule's intent -- an
# unevidenced claim that rlxfw repaired something -- and drops the adjective,
# which was never a repair claim.  That is a narrowing by measurement, not a
# widened tolerance: no claim the first form would have refused is now
# accepted, because an adjective makes no claim.
D3_STRUCT = re.compile(rf"{D3_SUBJ}[^。\.!?;\n]{{0,40}}?{D3_FIX}")

# --------------------------------------------------------------------------
# D5: the five content kinds
# --------------------------------------------------------------------------
D5_KINDS = (
    ("D5a", "endpoint",
     re.compile(r"/(?:boafrm|goform|cgi-bin)/|\b[\w.-]+\.(?:htm|html|asp|cgi|dat)\b")),
    ("D5b", "parameter",
     re.compile(r"\bform[A-Z][A-Za-z]+|\bapmib_(?:set|get)\b"
                r"|\b[A-Z][A-Z0-9]{1,}_[A-Z0-9_]{2,}\b")),
    # ⚠️ MEASURED FIRST.  The payload class started with a backtick or a `;`
    # followed by anything, and 量 it fired on `` `/proc/<pid>/root` `` and on
    # `` `V1-BOOT.log` `` -- a backtick in this corpus is markdown quoting and
    # appears in nearly every cell, so that alternative was testing the
    # file's typography and not whether a literal could be SENT.  What
    # survives is the sendable shapes: an encoding, a traversal, a command
    # substitution, and a pipe or semicolon followed by a program.
    ("D5c", "payload",
     re.compile(r"%2[eEfF]|%00|\.\./|\$\(|[|;]\s*(?:sh|nc|cat|wget|telnetd|/bin/)\b"
                r"|\bnc\s+-")),
    ("D5d", "verb",
     re.compile(r"\b(?:GET|POST|PUT|DELETE|HEAD|OPTIONS)\b[^\n]{0,30}?/\w")),
    ("D5e", "reproduction artefact",
     re.compile(r"\bpoc\b|\bexploit\b|\brepro(?:duction)?\s+steps\b|重現步驟"
                r"|\bsteps\s+to\s+reproduce\b")),
)
D5_SEQUENCE = re.compile(r"(?:先|first)[^。\.\n]{0,60}(?:然後|接著|then\b)"
                         r"|\bsend\b[^。\.\n]{0,60}\bthen\b")
# `D5b`'s third alternative catches any SHOUTING_SNAKE symbol, and a symbol
# that appears ONLY in the rlxfw cell ③ and nowhere in the same group's vendor
# cell ② is rlxfw's own identifier: an upstream held mechanism cannot be
# reproduced out of this project's own error names.  量 that is not a nominal
# case -- `MSG_TRUNC` (a libc socket flag) and `DNSE_LONG` (rlxfw's own error)
# are in `I-SRC-DNS`'s ③ and in no ② cell.  The test is DERIVED from the pair,
# not a list of permitted names, so a vendor symbol quoted in ③ still fires.
#
# ONE EXEMPTION, BY NAME, WITH THE CONTROL THAT RETIRES IT.  `CLAUDE.md`:
# exempt a known defect by name, never by date or pattern, with a control that
# goes red when the exemption stops being needed, and sweep the list both ways.
D5_EXEMPT = (
    {"code": "D5b", "token": "TELNET_ENABLED", "cell": "服務不存在/I-PORT ②",
     "held_ids": ("D-16", "D-19"),
     "why": "讀 a vendor build/NVRAM flag name, not a value a request supplies: the "
            "register row that names it (`FC-078`) carries `held = false` and an empty "
            "`held_disclosure_ids`, and the held rows on this anchor are `FC-076` and "
            "`FC-120`, whose ids are `D-16` and `D-19` and whose class-level titles this "
            "file does not reprint. The token is already published in "
            "`config/fix-cases.toml` and `docs/boot-time-table.md` § 6. OPEN: whether "
            "the same sentence is a class-level description of held `D-13` is a "
            "judgement and not a reading; what settles it is `D-13` being sent or "
            "withdrawn upstream"},
)


def _sentences(text):
    return [s for s in re.split(r"[。\.!?;\n]", text) if s.strip()]


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def load_toml(path, want):
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise Refused(f"cannot read {path}: {e.strerror}")
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"{path.name} is not readable TOML: {e}")
    if want not in doc:
        raise Refused(f"{path.name} carries no [[{want}]] table")
    return doc


def spec_ids(root):
    p = root / "SPEC.md"
    if not p.exists():
        raise Refused(f"SPEC.md is not under {root}: D2b cannot resolve a row id, and a "
                      f"link check that cannot resolve is not a link check")
    out = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("|"):
            cells = line.split("|")
            if len(cells) > 1:
                m = SPEC_ROW_RX.match(cells[1].strip())
                if m:
                    out.add(m.group(1))
    if not out:
        raise Refused("SPEC.md parsed to 0 row ids: D2b would pass everything, which is "
                      "a tool reporting 0 while making a claim")
    return out


def coverage(probes, rows):
    """The 21-not-89 arithmetic, DERIVED.  Refuses rather than publishing a hole."""
    cases = probes["case"]
    covered = {c.get("register_id") for c in cases if c.get("register_id")}
    va = {r["id"] for r in rows if r.get("evidence_tier") == "V-A"}
    text = probes.get("_text", "")
    m = re.search(r"A=((?:FC-\d{3},)+FC-\d{3})", text)
    if not m:
        raise Refused("the probe list carries no `A=` --allow-uncovered line, so the "
                      "exempted set cannot be derived; it is not copied from prose")
    exempt = m.group(1).split(",")
    dupes = sorted(i for i, n in Counter(exempt).items() if n > 1)
    if dupes:
        raise Refused(f"the exempted set repeats {dupes}: a count over a list with "
                      f"duplicates is not a partition")
    exempt = set(exempt)
    stray = sorted((covered | exempt) - va)
    if stray:
        raise Refused(f"these ids are covered or exempted but are not `V-A` rows: {stray}")
    both = sorted(covered & exempt)
    if both:
        raise Refused(f"these ids are both probed and exempted: {both}")
    neither = sorted(va - covered - exempt)
    if neither:
        raise Refused(f"these `V-A` rows are neither probed nor exempted: {neither}; "
                      f"an uncovered row with no reason is a hole, not a count")
    if len(covered) + len(exempt) != len(va):
        raise Refused(f"the coverage partition does not close: {len(covered)} probed + "
                      f"{len(exempt)} exempted != {len(va)} `V-A` rows")

    # The per-reason counts are DERIVED from the reason blocks, never retyped:
    # a count in a comment with no checker is a count that rots (`FW-174`).
    # A block's ids come from its ID-LIST lines -- lines holding nothing but
    # `#`, spaces and ids -- because a block's PROSE also names ids, and
    # counting those inflated every block when it was tried.
    blocks = re.findall(r"^# ([A-F])\. (.*?)(?=^# [A-F]\.|^# Rows appearing)",
                        text, re.S | re.M)
    if not blocks:
        raise Refused("the probe list carries no reason blocks `# A.` … `# F.`, so the "
                      "exempted set has no reasons to count")
    listed, reasons, why = {}, {}, {}
    for letter, body in blocks:
        got = []
        for line in body.splitlines():
            s = line.lstrip("#").strip()
            if s and re.fullmatch(r"(?:FC-\d{3}\s*)+", s):
                got += re.findall(r"FC-\d{3}", s)
        reasons[letter] = list(got)
        for i in got:
            listed.setdefault(i, []).append(letter)
        # The reason is the block's text before its own `(N rows)` count.  Cut
        # on that marker BY NAME: cutting on the first `(` instead took block F
        # apart inside `system("flash set …")`, publishing a sentence that
        # stopped mid-word with an unclosed backtick.  A block with no count of
        # its own -- F is the one, and § 5 says so -- gives its first sentence.
        head = re.split(r"\(\s*\d+\s*rows?\b", body)[0]
        if head == body:
            head = re.split(r"\.\s\s", body)[0] + "."
        # and strip EACH line's comment marker before joining: a reason that
        # wraps over several `#` lines otherwise publishes its markers
        # mid-sentence ("so `R2`/`R3` refuse # it").
        head = " ".join(ln.lstrip("#").strip() for ln in head.splitlines())
        why[letter] = re.sub(r"\s+", " ", head).strip(" .#") or letter
    # an exempted id in no block's ID LIST is attributed to the block whose
    # PROSE names it; one that no block names at all is a hole and refuses
    orphan = {}
    for i in sorted(exempt - set(listed)):
        owner = [l for l, body in blocks if i in body]
        if not owner:
            raise Refused(f"{i} is exempted and no reason block names it: an exemption "
                          f"with no reason is a hole, not a count")
        orphan[i] = owner[0]
        reasons[owner[0]].append(i)
    stale = sorted(set(listed) - exempt)
    if stale:
        raise Refused(f"a reason block lists {stale}, which is not in the exempted set: "
                      f"the list is swept both ways, so a stale id is a finding")
    doubled = {i: ls for i, ls in listed.items() if len(ls) > 1}
    listings = sum(len(v) for v in reasons.values())
    if listings - sum(len(ls) - 1 for ls in doubled.values()) != len(exempt):
        raise Refused(f"{listings} listings over {len(doubled)} double-listed ids do not "
                      f"reduce to {len(exempt)} exempted rows")
    return {"cases": len(cases), "covered": len(covered), "exempt": len(exempt),
            "va": len(va), "reasons": reasons, "why": why, "orphan": orphan,
            "doubled": doubled, "listings": listings,
            "multi": sorted(i for i, n in
                            Counter(c["register_id"] for c in cases).items() if n > 1)}


# --------------------------------------------------------------------------
# the document, as attributable blocks
# --------------------------------------------------------------------------
class Block:
    __slots__ = ("key", "text", "held_linked", "group_publishes_win", "vendor_peer",
                 "held_ids")

    def __init__(self, key, text, held_linked=False, group_publishes_win=True,
                 vendor_peer="", held_ids=()):
        self.key = key
        self.text = text
        self.held_linked = held_linked
        self.group_publishes_win = group_publishes_win
        # the ② cell of the same published row, so `D5b` can tell a vendor
        # symbol quoted in ③ from one of rlxfw's own
        self.vendor_peer = vendor_peer
        self.held_ids = tuple(held_ids)


def guard_rows(rows):
    """`D1` and `D4`: properties of the INPUT that would corrupt the table.  Run
    BEFORE anything is built, so a class outside the closed set is refused
    rather than reaching code that has no column meaning for it -- a pre-flight
    guard refuses before the port opens."""
    bad = []
    for r in rows:
        rid = f"{r.get('id', '?')}/{r.get('upstream_id', '?')}"
        if r.get("mechanism_class") not in CLASSES:
            bad.append(("D1", rid,
                        f"mechanism_class {r.get('mechanism_class')!r} is outside the "
                        f"closed set {list(CLASSES)}; the primary key cannot hold a "
                        f"class the published table has no column meaning for"))
        reading = str(r.get("opposite_check_reading", ""))
        if not reading.strip():
            bad.append(("D4", rid,
                        "④ has no reading at all, so the row cannot be published: a row "
                        "missing ④'s reading publishes 未定, never a win"))
        elif r.get("publish") == "win" and reading.lstrip().startswith(UNDET):
            bad.append(("D4", rid, "publishes `win` on a ④ reading that opens 未定"))
    return bad


def guard(blocks, rows, root, ids):
    """`D2`, `D3`, `D5`: properties of the TEXT about to be written.  Returns a
    list of (rule, where, message); empty means the document may be written."""
    bad = []

    def fail(rule, where, msg):
        bad.append((rule, where, msg))

    prefixes = {i.split("-")[0] for i in ids}
    for b in blocks:
        for p in PATH_RX.findall(b.text):
            if p.startswith(PATH_SKIP):
                continue
            if p == SELF_REL:
                if not TOOL.exists():          # cannot happen while running
                    fail("D2a", b.key, "the tool's own path does not resolve")
                continue
            if not (root / p).exists():
                fail("D2a", b.key, f"cited path does not resolve: {p}")
        for i in CITED_ID_RX.findall(b.text):
            if i.split("-")[0] in prefixes and i not in ids:
                fail("D2b", b.key, f"cited `SPEC.md` row id does not exist: {i}")
        for f, sec in SECTION_RX.findall(b.text):
            if f.startswith(PATH_SKIP):
                continue
            fp = root / f
            if not fp.exists():
                fail("D2c", b.key, f"section citation names a file that does not exist: {f}")
                continue
            body = fp.read_text(encoding="utf-8", errors="replace")
            if not re.search(rf"^#{{2,4}}\s*{re.escape(sec)}(?:[\s.]|$)", body, re.M):
                fail("D2c", b.key, f"{f} has no heading § {sec}")

        for s in D3_LITERALS:
            if s in b.text:
                fail("D3", b.key, f"asserts the design fixed the case: {s!r}")
        for sent in _sentences(b.text):
            parts = [(n, rx.search(sent)) for n, rx in D3_PARTS]
            vo = D3_VERB_OBJ.search(sent)
            if all(m for _, m in parts):
                fail("D3", b.key, "asserts the design fixed the case — "
                     + ", ".join(f"{n} {m.group(0)!r}" for n, m in parts))
            elif vo and parts[0][1]:
                fail("D3", b.key, f"asserts the design fixed the case (repair verb with a "
                                  f"pronoun object): {vo.group(0)!r}")
            elif not b.group_publishes_win:
                m = D3_STRUCT.search(sent)
                if m:
                    fail("D3", b.key, f"claims a repair in a group that publishes no win, "
                                      f"so the claim has no reading: {m.group(0)[:70]!r}")

        if not b.held_linked:
            continue
        for code, what, rx in D5_KINDS:
            for m in rx.finditer(b.text):
                tok = m.group(0)
                if _d5_exempt(code, b, tok):
                    continue
                if (code == "D5b" and b.key.endswith("③")
                        and re.fullmatch(r"[A-Z][A-Z0-9]{1,}_[A-Z0-9_]{2,}", tok)
                        and tok not in b.vendor_peer):
                    continue       # rlxfw's own symbol: see D5_EXEMPT's preamble
                fail(code, b.key, f"held-linked text carries {what} content: {tok[:48]!r}")
                break
        for sent in _sentences(b.text):
            kinds = []
            for code, what, rx in D5_KINDS[:4]:
                m = rx.search(sent)
                if m and not _d5_exempt(code, b, m.group(0)):
                    kinds.append(what)
            if len(set(kinds)) >= 2:
                fail("D5e", b.key, f"held-linked sentence is in substance a reproduction: "
                                   f"{sorted(set(kinds))} in one sentence")
            if D5_SEQUENCE.search(sent):
                fail("D5e", b.key, "held-linked text gives an ordered sequence of actions")

    # Sweep the exemption list BOTH WAYS: an exemption whose token has left the
    # cell it names, or whose premise about that cell's held ids has moved, is
    # itself a finding -- otherwise the list only ever grows.
    for ex in D5_EXEMPT:
        hit = [b for b in blocks if b.key == ex["cell"]]
        if not hit:
            fail("D5X", ex["cell"], f"exemption for {ex['token']} names a cell this "
                                    f"document does not publish: retire it")
            continue
        b = hit[0]
        if ex["token"] not in b.text:
            fail("D5X", ex["cell"], f"exemption for {ex['token']} is stale: the token is "
                                    f"no longer in that cell")
        if tuple(sorted(b.held_ids)) != tuple(sorted(ex["held_ids"])):
            fail("D5X", ex["cell"], f"the exemption's premise moved: it was written when "
                                    f"this group's held ids were {list(ex['held_ids'])} and "
                                    f"they are now {list(b.held_ids)}")
    return bad


D5_DISCLOSURE = "D5-disclosure"


def _d5_exempt(code, b, token):
    """An exemption permits its token in the cell it names -- and in the block
    that DISCLOSES the exemption, because a guard that refuses the sentence
    naming what it permits cannot be audited.  量: it did refuse that sentence,
    which is how this clause was found."""
    for ex in D5_EXEMPT:
        if ex["token"] in token and (
                (ex["code"] == code and ex["cell"] == b.key) or b.key == D5_DISCLOSURE):
            return True
    return False


def build(reg, probes, root):
    """Build the document.  Returns (blocks, text)."""
    rows = reg["row"]
    cov = coverage(probes, rows)

    groups = defaultdict(list)
    for r in rows:
        groups[(r.get("mechanism_class"), r.get("anchor"))].append(r)
    # ②③④ must be one value per anchor, or a group cell would be a lie
    for a in {r.get("anchor") for r in rows}:
        rs = [r for r in rows if r.get("anchor") == a]
        for f in ANCHOR_CELLS:
            if len({str(r.get(f, "")) for r in rs}) != 1:
                raise Refused(f"anchor {a} has more than one {f}: the published row is a "
                              f"group, so a group cell with two values cannot be written")

    cls_n = Counter(r.get("mechanism_class") for r in rows)
    tier_n = Counter(r.get("evidence_tier") for r in rows)
    pub_n = Counter(r.get("publish") for r in rows)
    held_rows = [r for r in rows if r.get("held")]
    named = set()
    for r in held_rows:
        named |= set(r.get("held_disclosure_ids") or [])
    unnamed = [i for i in HELD_IDS if i not in named]

    B = []

    def prose(text, key="prose"):
        linked = any(re.search(rf"{i}\b", text) for i in HELD_IDS)
        B.append(Block(key, text, held_linked=linked))
        return text

    out = []
    out.append(prose(
        "# differential — the vendor firmware against rlxfw, by mechanism class\n\n"
        "`R9-8`, rendered by `tools/diffrender.py` from `config/fix-cases.toml` "
        "(`R9-1`'s register) and `config/r9-probes.toml` (`R9-6`'s probe list). "
        "Nothing here is typed: every cell and every count below is derived at render "
        "time, and the renderer refuses to write the file when one of its five guards "
        "fires. `notes/vendor-differential.md` owns the readings this table publishes; "
        "`docs/hardening-matrix.md` owns the per-mechanism *mitigation* question and "
        "`docs/threat-model.md` the positions. This file owns neither — it owns the "
        "differential's shape.\n"))

    out.append(prose(
        "\n## 1. What a published row is\n\n"
        f"讀 over the register — every statement in this file about the register or the "
        f"probe list is 讀, read out of those files at render time; a 量 below is a device "
        f"reading in the file it cites, carried with its own mark: ②, ③ and ④ are "
        f"identical across every row that shares an "
        f"`anchor` — one distinct value each, for all {len({r.get('anchor') for r in rows})} "
        f"anchors. So a published row is the pair (機制類別, anchor), and "
        f"**{len(groups)} rows** stand for {len(rows)} register rows. A published cell is "
        f"anchor text plus counts; no per-row cell — no title, no residual, no refutation — "
        f"is written, which is how the held items are **absent** rather than redacted.\n\n"
        "The four columns are the re-specified 通過's four clauses, verbatim in substance: "
        "**①** the mechanism class, from the closed set ⟨架構性, 有界化, 服務不存在, 不適用, "
        "平台限制⟩, the primary key; **②** a vendor cell that is a reading from `V-A`/`V-B`/"
        "`V-C` naming its capture or artefact, or ⊘ Structural naming the committed finding; "
        "**③** an rlxfw cell from the same instrument as ②; **④** a check that would have "
        "detected the opposite of what the row claims, with that check's reading. A row "
        "whose ④ has no reading publishes 未定 and never a win.\n"))

    out.append(prose(
        "\n## 2. The five uncontrolled variables, and what each costs comparability\n\n"
        "The two firmwares differ in five classes of way that this gate does not control. "
        "They are named here because a difference measured between the columns may belong "
        "to any of them rather than to a design decision, and column ③ cannot tell them "
        "apart.\n\n"
        "| class | what differs | what it costs comparability |\n"
        "|---|---|---|\n"
        "| **kernel config** | rlxfw's kernel is the vendor 2.6.30 tree with a declared "
        "delta (`config/rlxfw-kernel.delta`, checked by `tools/kconfig-delta.py`); "
        "`SWCORE=n` is rlxfw's default and 讀 `PROGRESS.md` `R9-5` it has never booted | "
        "a timing or memory difference may be the delta's, not the design's. 讀 "
        "`docs/boot-time-table.md` § 4.2: the identical-code control `D2` exists for exactly "
        "this reason. Same source is not same object, and 量 2026-10-04 both halves of that "
        "are now counted on the artefact rather than estimated: `FW-204`, the WLAN driver's "
        "`built-in.o` loses 11 symbol-table entries (four functions) and 6 references at "
        "`SWCORE=n`, not the 40 this row carried until that build; `FW-203`, `sk_buff` is "
        "192 bytes there against 200 |\n"
        "| **libc** | the vendor's prebuilt uClibc against rlxfw's own build; 讀 "
        "`notes/busybox-build.md` § 1 and § 5 for the applet set that replaces four vendor "
        "files | a string-handling or allocator difference is libc's. `SPEC.md` `FW-20` "
        "measured that the published import-scan method misses `system` itself, because "
        "libc stores `__libc_system` and the symbol lands at +7 |\n"
        "| **toolchain** | 讀 `notes/kernel-build.md` § 1: `rsdk-1.3.6-4181`, through its "
        "own wrapper, and § 1.1 is the control that separates `-march` from the toolchain "
        "generation | code shape, hazard behaviour and size are the toolchain's as much as "
        "the source's; a size or instruction-mix comparison between the columns is not a "
        "design reading |\n"
        "| **userspace** | 量 `SPEC.md` `FW-20`: 161 files and 55 ELFs in the vendor tree, "
        "3 static. 量 `SPEC.md` `FW-177` 2026-09-30 on the shipping bytes: rlxfw's six "
        "programs | the two userspaces are not the same population, so a per-binary rate "
        "from one side is not a rate on the other |\n"
        "| **service set** | 量 `notes/vendor-differential.md` § 1: the vendor boot starts "
        "`boa`, a UPnP IGD, a WPS daemon, a DNS spoofer and an NTP client. 量 `SPEC.md` "
        "`FW-175`: rlxfw serves TCP 80 and UDP 53 | a port that is closed on rlxfw is "
        "closed because the service is not in the image, which is a reading about the "
        "service set and not about rlxfw's hardening of that service |\n"))

    out.append(prose(
        "\n## 3. The table\n\n"
        "① carries the primary key, the anchor that supplied ②③④, the group's size, how "
        "many of its rows are held, and the group's publish verdicts. A group's publish "
        "mix is printed in full rather than summarised, because a group with one win and "
        "three 未定 is not a group that won.\n"))

    out.append("\n| ① 機制類別 · anchor | ② vendor | ③ rlxfw | ④ opposite check, and its reading |\n")
    out.append("|---|---|---|---|\n")

    def cell(s):
        return str(s).replace("|", "\\|").replace("\n", " ").strip()

    def order(k):
        # an unknown class sorts last rather than raising: `guard_rows` has
        # already refused it, and a builder that crashes on refused input would
        # print a traceback where a reason belongs
        return (CLASSES.index(k[0]) if k[0] in CLASSES else len(CLASSES), str(k[1]))

    for (klass, anchor) in sorted(groups, key=order):
        rs = groups[(klass, anchor)]
        r0 = rs[0]
        held = sum(1 for r in rs if r.get("held"))
        pub = Counter(r.get("publish") for r in rs)
        pubs = " / ".join(f"{p} {pub[p]}" for p in PUBLISH_ORDER if pub[p])
        tiers = " ".join(f"{t} {n}" for t, n in
                         sorted(Counter(r.get("evidence_tier") for r in rs).items()))
        und = sum(1 for r in rs
                  if str(r.get("opposite_check_reading", "")).lstrip().startswith(UNDET))
        key = f"**{klass}** · `{anchor}`<br>n={len(rs)}, held {held}, {tiers}<br>{pubs}"
        c2, c3 = cell(r0.get("vendor_evidence")), cell(r0.get("rlxfw_evidence"))
        c4 = (cell(r0.get("opposite_check")) + " — **reading:** "
              + cell(r0.get("opposite_check_reading")))
        if und:
            c4 += f" <br>⚠️ {und} of {len(rs)} rows in this group read 未定 on ④"
        gids = sorted({i for r in rs for i in (r.get("held_disclosure_ids") or [])})
        linked = held > 0
        wins = pub["win"] > 0
        gk = f"{klass}/{anchor}"
        for part, name in ((key, "①"), (c2, "②"), (c3, "③"), (c4, "④")):
            B.append(Block(f"{gk} {name}", part, held_linked=linked,
                           group_publishes_win=wins, vendor_peer=c2, held_ids=gids))
        out.append(f"| {key} | {c2} | {c3} | {c4} |\n")

    out.append(prose(
        f"\n## 4. The counts, each with the control that keeps it from being an "
        f"instrument zero\n\n"
        f"| count | value | its control |\n"
        f"|---|---|---|\n"
        f"| register rows | {len(rows)} | `tools/fixcases.py` `C12` refuses when "
        f"`upstream_cases` and the row count disagree; `C11` freezes the digest over ④ "
        f"and the refutation |\n"
        f"| published rows | {len(groups)} | the renderer refuses when an anchor carries "
        f"two different ②③④, so a group cell cannot be written over disagreeing rows |\n"
        f"| mechanism classes | "
        f"{', '.join(f'{k} {cls_n[k]}' for k in CLASSES)} | **平台限制 is 0, and the 0 is "
        f"a claim.** The control is positive: `--self-test` `P1` plants a 平台限制 row and "
        f"requires the renderer to ACCEPT it, so the 0 means the register carries none, not "
        f"that the renderer cannot represent one. ⚠️ `tools/fixcases.py`'s own `CLASSES` "
        f"still holds four, so such a row would be refused there — that is a defect in the "
        f"register's checker, recorded here and not worked around |\n"
        f"| evidence tiers | {', '.join(f'{k} {tier_n[k]}' for k in sorted(tier_n))} | "
        f"`C5` re-derives both partitions from the rows and refuses on a mismatch |\n"
        f"| publish | {', '.join(f'{k} {pub_n[k]}' for k in PUBLISH_ORDER if pub_n[k])} | "
        f"`D4` here and `C7` there both refuse a `win` on a 未定 ④ reading; 讀 {pub_n['win']} "
        f"win rows and 0 of them read 未定 |\n"
        f"| held rows | {len(held_rows)} of {len(rows)}, naming {len(named)} of the "
        f"thirteen held ids | `D5` does not key on the flag: 讀 `{', '.join(unnamed)}` is "
        f"named by no register row, so the flag alone would be blind to "
        f"{len(HELD_IDS) - len(named)} of thirteen |\n"
        f"| ④ has a reading | "
        f"{sum(1 for r in rows if not str(r.get('opposite_check_reading','')).lstrip().startswith(UNDET))} "
        f"of {len(rows)}; {sum(1 for r in rows if str(r.get('opposite_check_reading','')).lstrip().startswith(UNDET))} "
        f"read 未定 | `C4` refuses a 未定 reading that does not say what settles it, and "
        f"`D4` refuses a row with no reading at all |\n"))

    sumline = " + ".join(str(len(cov["reasons"][l])) for l in sorted(cov["reasons"]))
    dbl = ", ".join(f"{i} under {'/'.join(ls)}" for i, ls in cov["doubled"].items())
    orph = ", ".join(f"{i} (named in block {l}'s prose, not in its id list)"
                     for i, l in cov["orphan"].items())
    out.append(prose(
        f"\n## 5. Coverage — why the live column is {cov['covered']} and not {cov['va']}\n\n"
        f"讀, re-derived here from both files at render time rather than quoted:\n\n"
        f"* The register carries **{cov['va']}** rows at tier `V-A` — the tier whose "
        f"refutation needs a live, network-facing reading.\n"
        f"* `config/r9-probes.toml` holds **{cov['cases']}** probe cases citing "
        f"**{cov['covered']}** distinct register rows. The two numbers differ because "
        f"{len(cov['multi'])} rows carry two cases each ({', '.join(cov['multi'])}), so "
        f"counting cases would overstate coverage by {cov['cases'] - cov['covered']}.\n"
        f"* **{cov['exempt']}** `V-A` rows are exempted by name, each with a written "
        f"reason, and passed to `--allow-uncovered` so the run refuses rather than "
        f"publishing a hole as a coverage count.\n"
        f"* **{cov['covered']} + {cov['exempt']} = {cov['covered'] + cov['exempt']}**, "
        f"against **{cov['va']}** `V-A` rows. The renderer refuses if that does not close, "
        f"if any id is both probed and exempted, if any is neither, or if either set names "
        f"a row that is not `V-A`.\n\n"
        f"The exempted {cov['exempt']} carry **{len(cov['reasons'])}** reasons, and the "
        f"per-reason counts below are parsed out of the probe list's own reason blocks, not "
        f"retyped:\n\n"
        + "".join(f"* **{l} — {len(cov['reasons'][l])}**: {cov['why'][l]}\n"
                  for l in sorted(cov["reasons"]))
        + f"\n**{sumline} = {cov['listings']} listings**, and {len(cov['doubled'])} row is "
        f"listed under two reasons ({dbl}), so the set is **{cov['exempt']}**. ⚠️ A "
        f"five-reason sum that drops the last block reads "
        f"{cov['listings'] - len(cov['reasons']['F'])} and does not close against "
        f"{cov['va']}; 讀 that block declares no `(N rows)` count of its own and reaches "
        f"its full size only because {orph} — which is why it is the block a reader "
        f"drops. The renderer refuses if an exempted id is named by no block, if a block "
        f"lists an id that is not exempted, or if the listings do not reduce to the "
        f"exempted set.\n"))

    out.append(prose(
        f"\n## 6. `D5`'s scope, and the one token it permits by name\n\n"
        f"`D5` is the guard that keeps content from the thirteen held ids "
        f"(`{HELD_IDS[0]}`, `{HELD_IDS[1]}`, `{HELD_IDS[2]}`…`{HELD_IDS[-1]}`) out of this "
        f"file. Content means one of five things in the text about to be written — an "
        f"endpoint, a parameter, a payload, a verb next to a path, or a reproduction "
        f"(two of those four in one sentence, an ordered sequence, or a named artefact) — "
        f"and the strict scan runs on a cell when its group holds a row marked held, when "
        f"its text names one of the thirteen, or both. "
        f"讀 the register: {len(held_rows)} rows are marked held and they name "
        f"{len(named)} ids, so the flag alone would miss `{', '.join(unnamed)}`; the scan "
        f"is therefore keyed on the id set as well as the flag. **Naming an id is not "
        f"publishing its content**, which is why the ids appear above and in "
        f"`config/r9-probes.toml`; what a held row contributes to the table is its share "
        f"of a count, and this file reprints no held row's title, residual or "
        f"refutation.\n"))

    # A separate block ON PURPOSE.  The paragraph above names the thirteen ids,
    # so `D5` strict-scans it; the paragraph below quotes the vendor symbols two
    # anchors publish and names no held id, which is in scope for `D5` only if
    # the two are one block.  The guard's unit is the block, and splitting here
    # makes the unit match the rule -- 量: written as one paragraph, `D5b` fired
    # on this tool's own prose, which is how the boundary was found.
    out.append(prose(
        f"\n**The guard reads 0 on this register, and a guard reading 0 is making a claim.** "
        f"Its positive controls are in `--self-test`: a planted class-level cell that is "
        f"in substance a reproduction goes red (`M8`), so does held content arriving "
        f"through the one id no row names (`M9`), and so does the exemption's own control "
        f"(`M10`). The permitting side is `P5`: the two anchors that publish vendor "
        f"symbols and addresses — the loader window in `I-LOADER`, and `formSysCmd`, "
        f"`0x00C000` and `SYSCMD_SELECT` in `I-STRUCT`, all already published by "
        f"`config/r9-probes.toml` and `notes/vendor-differential.md` § 1 — hold no held "
        f"row, so they render in full. `M10` assigns a held row to `I-STRUCT` and requires "
        f"the same text to be refused, which is the control that retires the exemption "
        f"when it stops being needed.\n"))

    out.append(prose(
        "\n"
        + ("".join(  # key D5_DISCLOSURE: see `_d5_exempt`
            f"**One token is permitted by name.** `{ex['token']}` in the cell "
            f"`{ex['cell']}`, under `{ex['code']}`. {ex['why']}. The exemption is swept "
            f"both ways: `D5X` refuses if the token leaves that cell, if that cell is no "
            f"longer published, or if the group's held ids move away from "
            + ", ".join(f"`{i}`" for i in ex["held_ids"]) + ".\n\n" for ex in D5_EXEMPT)
           or "**No token is permitted by name.**\n\n"), key=D5_DISCLOSURE))

    out.append(prose(
        "\n## 7. What this table does not establish\n\n"
        "* **It is not a security comparison.** Section 2's five uncontrolled variables are "
        "uncontrolled: a difference in a cell may belong to the kernel delta, the libc, the "
        "toolchain, the userspace population or the service set rather than to a design "
        "decision. `docs/hardening-matrix.md` § 5 states the same limit for the mitigation "
        "question.\n"
        "* **A group cell is an anchor's reading, not 141 readings.** The register rows "
        "behind a published row share ②③④ by construction; what each row contributes "
        "individually is its tier, its publish verdict and its refutation, and those live "
        "in `config/fix-cases.toml`.\n"
        "* **The held items are absent, and absent is not answered.** Rows whose upstream "
        "mechanism is held reach this table as counts. Whether rlxfw answers those "
        "mechanisms is not published here and will not be while the upstream rows read "
        "held — the report has not been sent.\n"
        f"* **A publish verdict of `win` is a reading about one check, not about a class.** "
        f"讀 `notes/vendor-differential.md` § 4 and § 5 above: {cov['exempt']} of "
        f"{cov['va']} `V-A` rows have no live probe, so the live column speaks for "
        f"{cov['covered']} of them and says nothing about the other {cov['exempt']}, nor "
        f"about the {len(rows) - cov['va']} rows in tiers `V-B`, `V-C` and `V-D`.\n"
        "* **`D5` reading 0 is a claim about `D5`'s scope.** It scans the text this file "
        "publishes. It does not scan `config/fix-cases.toml`'s per-row prose, which "
        "`tools/fixcases.py` `C10` does over five fields and is 量 blind to six others "
        "(`same_instrument`, `vendor_evidence`, `rlxfw_evidence`, `opposite_check`, "
        "`opposite_check_reading`, `refutation`).\n"
        "* **Nothing here is a timing claim and nothing here is a flash claim.** "
        "`notes/vendor-differential.md` § 1 owns the seating, the window and the bracket.\n"))

    return B, "".join(out)


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
def _copy(doc):
    import copy
    return copy.deepcopy(doc)


def _first(rows, pred):
    for r in rows:
        if pred(r):
            return r
    raise Refused("the register has no row of the shape this mutation needs")


def _plant(reg, **kw):
    """Put the mutation on a row whose anchor is otherwise clean, so the rule
    under test is the one that fires."""
    d = _copy(reg)
    r = _first(d["row"], lambda r: r.get("anchor") == "I-IMP")
    for a in d["row"]:
        if a.get("anchor") == "I-IMP":
            a.update(kw)
    r.update(kw)
    return d


def _plant_anchor(reg, field, value, anchor="I-IMP"):
    d = _copy(reg)
    for r in d["row"]:
        if r.get("anchor") == anchor:
            r[field] = value
    return d


MUTANTS = [
    ("M1", "D1", "a mechanism class outside the closed five",
     lambda reg: _plant(reg, mechanism_class="很安全")),
    ("M2", "D2a", "an evidence link to a file that does not exist",
     lambda reg: _plant_anchor(reg, "vendor_evidence", "讀 `notes/zzz-not-a-file.md`")),
    ("M3", "D2b", "a `SPEC.md` row id that does not exist",
     lambda reg: _plant_anchor(reg, "rlxfw_evidence", "量 `FW-999` on the die")),
    ("M4", "D2c", "a section citation with no such heading",
     lambda reg: _plant_anchor(reg, "opposite_check", "讀 `docs/boot-time-table.md` § 99")),
    ("M5", "D3", "the sentence the DoD names, verbatim",
     lambda reg: _plant_anchor(reg, "opposite_check_reading", "我的設計修好了這條")),
    ("M6", "D3", "a paraphrase sharing no literal with it",
     lambda reg: _plant_anchor(reg, "opposite_check_reading",
                               "量 2026-09-30: rlxfw 的設計已經把這一條消除了")),
    ("M7", "D4", "a win published on a 未定 ④ reading",
     lambda reg: _plant(reg, publish="win",
                        opposite_check_reading=UNDET + " -- SETTLED BY nothing")),
    ("M8", "D5e", "a CLASS-LEVEL row that is in substance a named reproduction",
     lambda reg: _plant_anchor(
         reg, "opposite_check_reading",
         "the class-level check: a GET /boafrm/formWlanRedirect with CmdSubmit set, "
         "then the same request again, leaves the server gone",
         anchor="I-SRC-HTTP")),
    ("M9", "D5", "held content reaching a group through the one held id no row names",
     lambda reg: _plant_anchor(
         reg, "rlxfw_evidence",
         "讀 upstream's held `D-11`: the handler is reached at /boafrm/formFilter and "
         "TELNET_ENABLED is set on the way",
         anchor="I-PORT")),
    ("M10", "D5", "the I-STRUCT exemption's own control: a held row moved onto it",
     lambda reg: _plant_anchor(reg, "held", True, anchor="I-STRUCT")),
    ("M11", "coverage", "an exempted id deleted, so the partition no longer closes",
     lambda reg: reg),  # mutates the PROBE file, handled below
    ("M12", "D5X", "the exemption swept the other way: its token leaves the cell",
     lambda reg: _plant_anchor(
         reg, "vendor_evidence",
         "量 `V1-NMAP` read 80, 52869 and 52881 open; port 23 not open in either",
         anchor="I-PORT")),
    ("M13", "D5X", "the exemption's premise moved: the group's held ids changed",
     lambda reg: _plant_anchor(reg, "held_disclosure_ids", ["D-12"], anchor="I-PORT")),
]

POSITIVES = [
    ("P1", "a planted 平台限制 row is ACCEPTED, so the class's 0 is a reading",
     lambda reg: _plant(reg, mechanism_class="平台限制")),
    ("P2", "a 未定 ④ reading that says what settles it, published 未定",
     lambda reg: _plant(reg, publish=UNDET,
                        opposite_check_reading=UNDET + " -- SETTLED BY the probe `R9-3` writes")),
    ("P3", "a resolving path, a real `SPEC.md` id and a real section citation",
     lambda reg: _plant_anchor(reg, "vendor_evidence",
                               "讀 `notes/rootfs-census.md`, 量 `FW-20`, "
                               "讀 `docs/boot-time-table.md` § 6")),
    ("P4", "a held row whose group text names only a class",
     lambda reg: _plant_anchor(reg, "opposite_check_reading",
                               "量 the bound's number is read off the shipped parser and "
                               "the matching case goes red when it is broken",
                               anchor="I-SRC-HTTP")),
    ("P5", "I-STRUCT keeps its vendor symbols while no held row sits on it",
     lambda reg: _copy(reg)),
]


def self_test(reg_path, probes_path, root):
    ok = fail = 0

    def say(good, name, text):
        nonlocal ok, fail
        if good:
            print(f"  ok    {name:5s} {text}")
            ok += 1
        else:
            print(f"  FAIL  {name:5s} {text}")
            fail += 1

    reg = load_toml(reg_path, "row")
    probes = load_toml(probes_path, "case")
    probes["_text"] = probes_path.read_text(encoding="utf-8", errors="replace")
    ids = spec_ids(root)

    print("-- the unmutated register FIRST: a mutation run is unreadable until it passes")
    try:
        base = guard_rows(reg["row"])
        blocks, text = build(reg, probes, root)
        base += guard(blocks, reg["row"], root, ids)
    except Refused as e:
        print(f"  FAIL  B0    the unmutated register REFUSED: {e}")
        print("\nREFUSED: no mutation below is readable; the baseline must pass first")
        return 1
    if base:
        say(False, "B0", f"the unmutated register has {len(base)} finding(s); no mutation "
                         f"below is readable")
        for rule, where, msg in base[:10]:
            print(f"        [{rule}] {where}: {msg}")
        print("\nREFUSED: the baseline must pass before any mutation is read")
        return 1
    say(True, "B0", f"baseline green: {len(reg['row'])} register rows -> "
                    f"{len(blocks)} blocks, {len(text.encode('utf-8'))} bytes, 0 findings")

    print("\n-- mutations: each must make its NAMED rule fire")
    for name, rule, what, fn in MUTANTS:
        try:
            if name == "M11":
                p = _copy(probes)
                p["_text"] = re.sub(r"A=FC-006,", "A=", probes["_text"], count=1)
                try:
                    build(reg, p, root)
                    say(False, name, f"[{rule}] DID NOT FIRE -- {what}")
                except Refused as e:
                    say("neither probed nor exempted" in str(e), name,
                        f"[{rule}] REFUSED as required -- {what} ({str(e)[:60]}…)")
                continue
            m = fn(reg)
            found = guard_rows(m["row"])
            if not found:
                b, _ = build(m, probes, root)
                found = guard(b, m["row"], root, ids)
        except Refused as e:
            say(False, name, f"[{rule}] ERROR building the mutant: {e}")
            continue
        hit = [f for f in found if f[0] == rule or f[0].startswith(rule)]
        if hit:
            say(True, name, f"[{rule}] RED as required -- {what} ({hit[0][0]} on {hit[0][1]})")
        else:
            say(False, name, f"[{rule}] DID NOT FIRE -- {what} "
                             f"(other findings: {sorted({f[0] for f in found})})")

    print("\n-- positive controls: the guard shown PERMITTING, not only refusing")
    for name, what, fn in POSITIVES:
        try:
            m = fn(reg)
            found = guard_rows(m["row"])
            b, _ = build(m, probes, root)
            found += guard(b, m["row"], root, ids)
        except Refused as e:
            say(False, name, f"REFUSED a register it should accept -- {what}: {e}")
            continue
        if name == "P5":
            keep = [bl for bl in b if bl.key.startswith("不適用/I-STRUCT")]
            tokens = any("formSysCmd" in bl.text or "0x00C000" in bl.text for bl in keep)
            say(not found and tokens, name,
                f"{what} (量 {len(keep)} blocks, vendor symbols present: {tokens})")
            continue
        say(not found, name, what if not found
            else f"REFUSED a row it should accept -- {what}: {found[0]}")

    print(f"\n{len(MUTANTS)} mutations, {len(POSITIVES)} positive controls, "
          f"{ok} ok, {fail} failed")
    return 1 if fail else 0


# --------------------------------------------------------------------------
def main(argv):
    args = [a for a in argv[1:] if a]
    opts = {"--register": None, "--probes": None, "--root": None, "--out": None}
    verbs = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in opts:
            if i + 1 >= len(args):
                print(f"REFUSED: {a} needs a value")
                return 2
            opts[a] = args[i + 1]
            i += 2
            continue
        verbs.append(a)
        i += 1

    root = Path(opts["--root"]).resolve() if opts["--root"] else ROOT
    reg_path = Path(opts["--register"]) if opts["--register"] else ROOT / "config/fix-cases.toml"
    probes_path = Path(opts["--probes"]) if opts["--probes"] else ROOT / "config/r9-probes.toml"
    out_path = Path(opts["--out"]) if opts["--out"] else root / "docs/differential.md"

    if "--self-test" in verbs:
        return self_test(reg_path, probes_path, root)
    if not verbs:
        print("diffrender -- renders docs/differential.md from R9-1's register")
        print("REFUSED: say what to do -- render, check, or --self-test")
        return 2
    verb = verbs[0]
    if verb not in ("render", "check"):
        print(f"REFUSED: unknown verb {verb!r}; expected render, check or --self-test")
        return 2

    reg = load_toml(reg_path, "row")
    probes = load_toml(probes_path, "case")
    probes["_text"] = probes_path.read_text(encoding="utf-8", errors="replace")
    ids = spec_ids(root)
    bad = guard_rows(reg["row"])          # before anything is built
    if not bad:
        blocks, text = build(reg, probes, root)
        bad = guard(blocks, reg["row"], root, ids)
    if bad:
        print(f"REFUSED: {len(bad)} guard finding(s); {out_path.name} is NOT written")
        for rule, where, msg in bad:
            print(f"  [{rule}] {where}: {msg}")
        return 1
    print(f"ok  {len(reg['row'])} register rows -> {len(blocks)} published blocks, "
          f"5 guards, 0 findings")
    if verb == "check":
        print(f"    check only: {out_path} not written")
        return 0
    # every anchor is checked before the first write, and the content exists
    # before the file does
    if not out_path.parent.is_dir():
        print(f"REFUSED: {out_path.parent} is not a directory")
        return 2
    # the content exists before the file does: build, write `.tmp`, os.replace
    # ⚠️ encode first and report the ENCODED length.  `len(text)` is characters,
    # and 量 it under-reported this document by 796 because the class names and
    # the marks are multi-byte -- a tool printing the wrong number is a tool
    # making a claim.
    data = text.encode("utf-8")
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(out_path)
    print(f"    wrote {out_path} ({len(data)} bytes, {len(text)} characters)")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.exit(main(sys.argv))
    except Refused as e:
        print(f"REFUSED: {e}")
        sys.exit(2)
    except BrokenPipeError:
        sys.exit(0)
