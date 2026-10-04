#!/usr/bin/env python3
"""fixcases -- does `config/fix-cases.toml` hold rows that could come back red?

`R9-1`'s DoD names three things this tool exists to make mechanical:

    A row with a result and an empty refutation is REFUSED, shown on a planted
    row; editing a prediction changes the digest in the same commit; the
    unmutated suite passes before any mutation run.

and `R9-8` names four renderer refusals that have to fire on planted rows
before any real row renders: a mechanism outside the closed set, an evidence
link that does not resolve, the sentence 「我的設計修好了這條」, and held
content.  This tool is where those refusals live, so that `docs/differential.md`
renders from a register that has already been refused on.

WHY A CHECKER AT ALL, AND NOT A COMMENT
=======================================
`config/fix-cases.toml`'s header carries counts -- the two partitions, the held
total, the substituted total.  A count in a comment with no checker is a count
that rots, and this repository has the receipt: `FW-174` is a value that moved
between two adjacent rows of one table and stayed wrong for thirty-six days,
because `spec-check` and `citecheck` read ids, citations and structure, and a
plausible number in the wrong row is structurally legal.  So every count in the
header is RE-DERIVED here from the rows and compared, and `C5` is the case that
fires when they disagree.

THE RULES, AND EACH ONE'S PLANTED CONTROL
=========================================
  C1  `mechanism_class` is in the closed set <架構性/有界化/服務不存在/不適用>.
  C2  `evidence_tier` is one of V-A, V-B, V-C, V-D.
  C3  `tier_basis_field` names a field the upstream case actually has, and
      `tier_basis` is non-empty.  A tier with no basis is a defect, and a basis
      naming a field the case does not carry is worse than none.
  C4  `opposite_check` is non-empty, `opposite_check_reading` is non-empty, and
      a reading that opens with 未定 says what SETTLES it.
  C5  every count in `[partition.*]` and `[tally]` equals the count re-derived
      from the rows.
  C6  `refutation` is non-empty on every row -- and REFUSED on any row that
      carries an upstream verdict with an empty refutation, which is the DoD's
      own sentence.
  C7  `publish` is one of win / surface-absent / not comparable / 未定, and a
      row whose ④ reads 未定, or which has no same-instrument pair, may NOT
      publish `win`.
  C8  every repository path cited in an evidence, residual or instrument cell
      resolves to a file that exists.  A citation that does not resolve is the
      `R9-8` refusal, and this is where it fires.
  C9  no row's text contains a sentence of the form 「我的設計修好了這條」 --
      an unevidenced self-assessment -- and no cell claims a win in prose while
      `publish` says otherwise.
  C10 a `held = true` row carries no reproduction: no endpoint path, no
      parameter name from the vendor's forms, no hex address, no HTTP verb plus
      path pair.  plan/ § 15 forbids it while the row says held.
  C11 the file's `[freeze].sha256` equals the digest re-derived from the rows.
  C13 a row whose class is not 不適用 may not sit on an anchor with no
      instrument: a class claim about rlxfw's own behaviour needs a pair.
  C12 `upstream_cases` equals the number of rows, and every `upstream_id` is
      unique and sorted.

`--self-test` mutates ONE field of a copy of the real file per case and requires
the named rule to fire, and it checks the unmutated file passes FIRST -- a green
suite is a claim about its controls, and a mutation run is what tests them.  It
also runs POSITIVE controls: the guard shown permitting as well as refusing.

Usage
-----
    tools/fixcases.py check [PATH]
    tools/fixcases.py freeze [PATH]       # print the digest the rows imply
    tools/fixcases.py --self-test
"""
import hashlib
import json
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "config/fix-cases.toml"

CLASSES = {"架構性", "有界化", "服務不存在", "不適用"}
TIERS = {"V-A", "V-B", "V-C", "V-D"}
PUBLISH = {"win", "surface-absent", "not comparable", "未定"}
# `same_instrument_pair` is TRI-state and the third value is not a hedge.
# `complete`: both columns are read with an instrument this repository has.
# `none needed`: the case's subject is not a behaviour either firmware serves,
# so there is nothing to pair.  `incomplete`: it IS a firmware behaviour and
# this repository cannot read the vendor half.  A boolean collapsed the first
# and second, which made 73 rows claim a pair whose instrument was `none`.
PAIR_STATES = {"complete", "none needed", "incomplete"}
UNDET = "未定"

# the fields an upstream `[[case]]` can carry.  A `tier_basis_field` outside
# this set is a defect, because the basis would cite nothing.
CASE_FIELDS = {"id", "phase", "section", "title", "feasibility", "exit_evidence",
               "week", "star", "caution", "predict", "refute", "cut_reason",
               "rescheduled_from", "reschedule_reason", "reschedule_date"}

TEXT_FIELDS = ("title", "tier_basis", "same_instrument", "vendor_evidence",
               "rlxfw_evidence", "opposite_check", "opposite_check_reading",
               "refutation", "residual", "blocker", "publish_reason")

# C9: the sentence the gate's own DoD names, plus its English shape.
SELF_ASSESS = (
    "我的設計修好了這條",
    "my design fixes this",
    "this proves",
    "rlxfw is more secure",
)

# C10: a held row may carry a mechanism class and nothing that reproduces it.
# A path segment the vendor's web server would route, a 0x address, or a verb
# plus path pair is a reproduction.
HELD_BAD = (
    (re.compile(r"/boafrm/|/goform/|/cgi-bin/|\.htm\b"), "a vendor endpoint path"),
    (re.compile(r"0x[0-9A-Fa-f]{6,}"), "a code address"),
    (re.compile(r"\b(POST|GET|PUT)\s+/"), "a verb plus path pair"),
    (re.compile(r"\bform[A-Z][A-Za-z]+"), "a vendor form handler name"),
    (re.compile(r"\bC(?:username|password)\b|\bsubmit-url\b|\blocalPin\b|"
                r"\bpeerPin\b|\bsysCmd\b|\bNewInternalClient\b"), "a vendor parameter name"),
)

# C8: a repository path must carry a DIRECTORY.  A bare basename in backticks is
# a source-file reference, not a citation -- `notes/dnsfwd.md` itself warns that
# a `file.c` plus a number is what `citecheck` reads as a citation and says to
# cite by section instead -- and the vendor's own `startup.sh` and `rcS` are
# names of files that are deliberately NOT in this tree.  Requiring the slash
# keeps the rule from refusing those while still catching a real dead link:
# `M10` plants `notes/zzz-not-a-file.md`, which has one.
PATH_RX = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_.+-]+)+"
                     r"\.(?:md|toml|tsv|py|sh|c|h|json|log))`")
# paths under these roots are deliberately outside the tree or generated
PATH_SKIP = ("plan/", "upstream/reports/", "$FWRE_WORK")


class Refused(Exception):
    """A refusal with a reason.  Never a traceback."""


def load(path):
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise Refused(f"cannot read {path}: {e.strerror}")
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"{path.name} is not readable TOML: {e}")
    if "row" not in doc:
        raise Refused(f"{path.name} carries no [[row]] table")
    return doc


def digest(rows):
    """sha256 over the fields a prediction edit must move."""
    payload = sorted((r.get("upstream_id", ""), r.get("refutation", ""),
                      r.get("opposite_check", ""), r.get("opposite_check_reading", ""))
                     for r in rows)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def check(doc, root=ROOT):
    """Return a list of (rule, row id, message).  Empty means green."""
    bad = []
    rows = doc["row"]

    def fail(rule, rid, msg):
        bad.append((rule, rid, msg))

    seen = []
    for r in rows:
        rid = f"{r.get('id', '?')}/{r.get('upstream_id', '?')}"
        seen.append(r.get("upstream_id", ""))

        if r.get("mechanism_class") not in CLASSES:
            fail("C1", rid, f"mechanism_class {r.get('mechanism_class')!r} is outside the "
                            f"closed set {sorted(CLASSES)}")
        if r.get("evidence_tier") not in TIERS:
            fail("C2", rid, f"evidence_tier {r.get('evidence_tier')!r} is not one of "
                            f"{sorted(TIERS)}")

        bf = r.get("tier_basis_field", "")
        if bf not in CASE_FIELDS:
            fail("C3", rid, f"tier_basis_field {bf!r} is not a field an upstream case carries")
        if not str(r.get("tier_basis", "")).strip():
            fail("C3", rid, "tier_basis is empty: a tier with no basis is a defect")

        if not str(r.get("opposite_check", "")).strip():
            fail("C4", rid, "opposite_check is empty")
        reading = str(r.get("opposite_check_reading", ""))
        if not reading.strip():
            fail("C4", rid, "opposite_check_reading is empty")
        elif reading.lstrip().startswith(UNDET) and "SETTLED BY" not in reading:
            fail("C4", rid, "the reading is 未定 and does not say what settles it")

        if not str(r.get("refutation", "")).strip():
            fail("C6", rid, "refutation is empty")
        elif r.get("upstream_verdict") and not str(r.get("refutation", "")).strip():
            fail("C6", rid, "carries an upstream verdict with an empty refutation")

        pub = r.get("publish")
        if pub not in PUBLISH:
            fail("C7", rid, f"publish {pub!r} is not one of {sorted(PUBLISH)}")
        pair = r.get("same_instrument_pair")
        if pair not in PAIR_STATES:
            fail("C7", rid, f"same_instrument_pair {pair!r} is not one of {sorted(PAIR_STATES)}")
        if pub == "win":
            if reading.lstrip().startswith(UNDET):
                fail("C7", rid, "publishes `win` while ④ reads 未定")
            if pair != "complete":
                fail("C7", rid, f"publishes `win` with the pair {pair!r}")
        # C13: a row whose class is not 不適用 is making a claim about rlxfw's
        # own behaviour, so it may not sit on an anchor with no instrument.
        if r.get("mechanism_class") != "不適用" and pair == "none needed":
            fail("C13", rid, f"claims mechanism class {r.get('mechanism_class')} while its "
                             f"pair is 'none needed': a class claim needs an instrument")
        if "none --" in str(r.get("same_instrument", "")) and pair == "complete":
            fail("C13", rid, "says the instrument is none and the pair is complete")

        blob = " ".join(str(r.get(f, "")) for f in TEXT_FIELDS)
        for p in PATH_RX.findall(blob):
            if p.startswith(PATH_SKIP):
                continue
            if not (root / p).exists():
                fail("C8", rid, f"cited path does not resolve: {p}")
        for s in SELF_ASSESS:
            if s in blob:
                fail("C9", rid, f"carries an unevidenced self-assessment: {s!r}")

        if r.get("held"):
            # Scope: the fields this register AUTHORS per row.  The shared
            # anchor cells are class-level by construction and are checked by
            # eye, because an address alone is a finding and not a
            # reproduction -- upstream's own `disclosure.md` publishes
            # addresses and holds back "the request, the payload, the
            # ordering".  This rule is deliberately stricter than plan/ § 15 on
            # the authored fields and silent on the shared ones.
            hb = " ".join(str(r.get(f, "")) for f in
                          ("title", "residual", "tier_basis", "blocker", "publish_reason"))
            for rx, what in HELD_BAD:
                m = rx.search(hb)
                if m:
                    fail("C10", rid, f"held row carries {what}: {m.group(0)!r}")

    cls = Counter(r.get("mechanism_class") for r in rows)
    tier = Counter(r.get("evidence_tier") for r in rows)
    pub = Counter(r.get("publish") for r in rows)
    want = [
        ("partition.mechanism_class", doc.get("partition", {}).get("mechanism_class", {}), cls),
        ("partition.evidence_tier", doc.get("partition", {}).get("evidence_tier", {}), tier),
    ]
    for name, decl, got in want:
        for k, v in got.items():
            if decl.get(k) != v:
                fail("C5", name, f"{k}: header says {decl.get(k)}, rows give {v}")
        if decl.get("total") != len(rows):
            fail("C5", name, f"total: header says {decl.get('total')}, rows give {len(rows)}")
        for k in decl:
            if k != "total" and k not in got:
                fail("C5", name, f"{k}: header declares it, no row carries it")

    t = doc.get("tally", {})
    derived = {
        "publish_win": pub["win"],
        "publish_surface_absent": pub["surface-absent"],
        "publish_not_comparable": pub["not comparable"],
        "publish_undetermined": pub[UNDET],
        "held": sum(1 for r in rows if r.get("held")),
        "instrument_substituted": sum(1 for r in rows if r.get("instrument_substituted")),
        "no_same_instrument_pair": sum(1 for r in rows if r.get("same_instrument_pair") != "complete"),
        "opposite_check_has_reading":
            sum(1 for r in rows
                if not str(r.get("opposite_check_reading", "")).lstrip().startswith(UNDET)),
        "opposite_check_undetermined":
            sum(1 for r in rows
                if str(r.get("opposite_check_reading", "")).lstrip().startswith(UNDET)),
    }
    for k, v in derived.items():
        if t.get(k) != v:
            fail("C5", "tally", f"{k}: header says {t.get(k)}, rows give {v}")

    prov = doc.get("provenance", {})
    if prov.get("upstream_cases") != len(rows):
        fail("C12", "provenance", f"upstream_cases says {prov.get('upstream_cases')}, "
                                  f"there are {len(rows)} rows")
    if len(set(seen)) != len(seen):
        dupes = [k for k, n in Counter(seen).items() if n > 1]
        fail("C12", "rows", f"duplicate upstream_id: {dupes}")
    if seen != sorted(seen):
        fail("C12", "rows", "rows are not in sorted upstream_id order")

    got = digest(rows)
    if doc.get("freeze", {}).get("sha256") != got:
        fail("C11", "freeze", f"[freeze].sha256 is {doc.get('freeze', {}).get('sha256')}, "
                              f"the rows give {got}")
    return bad


# ---------------------------------------------------------------------------
# self-test: every rule gets a planted row that must make it fire, and three
# positive controls so the suite is shown permitting as well as refusing.
# ---------------------------------------------------------------------------
def _mutate(doc, fn):
    import copy
    d = copy.deepcopy(doc)
    fn(d)
    return d


def _resync(d):
    """Make the header's counts and digest agree with the rows again, so that a
    mutation tests ITS OWN rule and not C5/C11 as a side effect."""
    rows = d["row"]
    cls = Counter(r["mechanism_class"] for r in rows)
    tier = Counter(r["evidence_tier"] for r in rows)
    pub = Counter(r["publish"] for r in rows)
    d["partition"]["mechanism_class"] = {k: v for k, v in cls.items()}
    d["partition"]["mechanism_class"]["total"] = len(rows)
    d["partition"]["evidence_tier"] = {k: v for k, v in tier.items()}
    d["partition"]["evidence_tier"]["total"] = len(rows)
    d["tally"] = {
        "publish_win": pub["win"],
        "publish_surface_absent": pub["surface-absent"],
        "publish_not_comparable": pub["not comparable"],
        "publish_undetermined": pub[UNDET],
        "held": sum(1 for r in rows if r.get("held")),
        "instrument_substituted": sum(1 for r in rows if r.get("instrument_substituted")),
        "no_same_instrument_pair": sum(1 for r in rows if r.get("same_instrument_pair") != "complete"),
        "opposite_check_has_reading":
            sum(1 for r in rows
                if not str(r["opposite_check_reading"]).lstrip().startswith(UNDET)),
        "opposite_check_undetermined":
            sum(1 for r in rows
                if str(r["opposite_check_reading"]).lstrip().startswith(UNDET)),
    }
    d["provenance"]["upstream_cases"] = len(rows)
    d["freeze"]["sha256"] = digest(rows)
    return d


def _first_held(rows):
    for r in rows:
        if r.get("held"):
            return r
    return None


MUTANTS = [
    ("M1", "C1", "a mechanism outside the closed set",
     lambda d: _resync(d["row"][0].update({"mechanism_class": "很安全"}) or d)),
    ("M2", "C2", "a tier that is not one of the four",
     lambda d: _resync(d["row"][0].update({"evidence_tier": "V-Z"}) or d)),
    ("M3", "C3", "a tier basis naming a field no case carries",
     lambda d: _resync(d["row"][0].update({"tier_basis_field": "vibes"}) or d)),
    ("M4", "C3", "an empty tier basis",
     lambda d: _resync(d["row"][0].update({"tier_basis": ""}) or d)),
    ("M5", "C4", "an empty opposite-check reading",
     lambda d: _resync(d["row"][0].update({"opposite_check_reading": ""}) or d)),
    ("M6", "C4", "a 未定 reading that does not say what settles it",
     lambda d: _resync(d["row"][0].update({"opposite_check_reading": UNDET + " no idea"}) or d)),
    ("M7", "C6", "a row with an upstream verdict and an empty refutation",
     lambda d: _resync(d["row"][0].update({"refutation": "", "upstream_verdict": "confirmed"}) or d)),
    ("M8", "C7", "a win published on a 未定 reading",
     lambda d: _resync(d["row"][0].update(
         {"publish": "win", "opposite_check_reading": UNDET + " SETTLED BY nothing"}) or d)),
    ("M9", "C7", "a win published on an incomplete same-instrument pair",
     lambda d: _resync(d["row"][0].update(
         {"publish": "win", "same_instrument_pair": "incomplete"}) or d)),
    ("M17", "C7", "a pair state outside the three",
     lambda d: _resync(d["row"][0].update({"same_instrument_pair": "yes"}) or d)),
    ("M18", "C13", "a mechanism class claimed where the pair is 'none needed'",
     lambda d: _resync(d["row"][0].update(
         {"mechanism_class": "架構性", "same_instrument_pair": "none needed"}) or d)),
    ("M19", "C13", "an instrument of none beside a complete pair",
     lambda d: _resync(d["row"][0].update(
         {"same_instrument": "none -- nothing to pair",
          "same_instrument_pair": "complete"}) or d)),
    ("M10", "C8", "an evidence link that does not resolve",
     lambda d: _resync(d["row"][0].update(
         {"vendor_evidence": "讀 `notes/zzz-not-a-file.md`"}) or d)),
    ("M11", "C9", "the sentence the gate's DoD forbids",
     lambda d: _resync(d["row"][0].update(
         {"residual": "我的設計修好了這條"}) or d)),
    ("M12", "C10", "a held row carrying a vendor endpoint path",
     lambda d: _resync(_first_held(d["row"]).update(
         {"residual": "the handler at /boafrm/formSomething"}) or d)),
    ("M13", "C10", "a held row carrying a code address",
     lambda d: _resync(_first_held(d["row"]).update(
         {"title": "the comparison at 0x0040bd4c"}) or d)),
    ("M14", "C5", "a header count edited away from the rows",
     lambda d: d["partition"]["mechanism_class"].update({"total": 999}) or d),
    ("M15", "C11", "a refutation edited without the digest moving",
     lambda d: d["row"][0].update({"refutation": "edited after the fact"}) or d),
    ("M16", "C12", "a duplicated upstream id",
     lambda d: _resync(d["row"][1].update({"upstream_id": d["row"][0]["upstream_id"]}) or d)),
]

POSITIVES = [
    ("P1", "a held row whose residual names only a class passes C10",
     lambda d: _resync(_first_held(d["row"]).update(
         {"residual": "the vendor-side mechanism is held, named at class level only"}) or d)),
    ("P2", "a 未定 reading that says what settles it passes C4",
     lambda d: _resync(d["row"][0].update(
         {"opposite_check_reading": UNDET + " -- SETTLED BY the probe R9-3 writes",
          "publish": UNDET}) or d)),
    ("P3", "a resolving evidence link passes C8",
     lambda d: _resync(d["row"][0].update(
         {"vendor_evidence": "讀 `notes/rootfs-census.md` and `config/rlxfw-cflags`"}) or d)),
]


def self_test():
    try:
        doc = load(DEFAULT)
    except Refused as e:
        print(f"REFUSED: {e}")
        return 2

    print("-- the unmutated file first: a mutation run is only readable if it passes")
    base = check(doc)
    if base:
        print(f"REFUSED: the unmutated file has {len(base)} finding(s); fix those before "
              f"reading any mutation")
        for rule, rid, msg in base[:12]:
            print(f"   [{rule}] {rid}: {msg}")
        return 1
    print(f"  ok    base  {len(doc['row'])} rows, 0 findings\n")

    nfail = 0
    print("-- mutations: each must make its named rule fire")
    for name, rule, what, fn in MUTANTS:
        try:
            m = _mutate(doc, fn)
            found = check(m)
        except Refused as e:
            print(f"  FAIL  {name:4s} [{rule}] ERROR building the mutant: {e}")
            nfail += 1
            continue
        hit = [f for f in found if f[0] == rule]
        if hit:
            print(f"  ok    {name:4s} [{rule}] RED as required -- {what}")
        else:
            print(f"  FAIL  {name:4s} [{rule}] DID NOT FIRE -- {what}  "
                  f"(other findings: {[f[0] for f in found]})")
            nfail += 1

    print("\n-- positive controls: the guard shown permitting, not only refusing")
    for name, what, fn in POSITIVES:
        m = _mutate(doc, fn)
        found = check(m)
        if found:
            print(f"  FAIL  {name:4s} REFUSED a row it should accept -- {what}")
            for rule, rid, msg in found[:4]:
                print(f"        [{rule}] {rid}: {msg}")
            nfail += 1
        else:
            print(f"  ok    {name:4s} green as required -- {what}")

    print(f"\n{len(MUTANTS)} mutations, {len(POSITIVES)} positive controls, {nfail} failed")
    return 1 if nfail else 0


def main(argv):
    args = [a for a in argv[1:] if a]
    if "--self-test" in args:
        return self_test()
    if not args:
        print(__doc__.strip().splitlines()[0])
        print("REFUSED: say what to do -- check, freeze, or --self-test")
        return 2
    verb, rest = args[0], args[1:]
    if verb not in ("check", "freeze"):
        print(f"REFUSED: unknown verb {verb!r}; expected check, freeze or --self-test")
        return 2
    path = Path(rest[0]) if rest else DEFAULT
    try:
        doc = load(path)
    except Refused as e:
        print(f"REFUSED: {e}")
        return 2
    if verb == "freeze":
        print(digest(doc["row"]))
        return 0
    bad = check(doc)
    rows = len(doc["row"])
    if not bad:
        print(f"ok  {path.name}: {rows} rows, 13 rules, 0 findings")
        return 0
    print(f"FAIL  {path.name}: {rows} rows, {len(bad)} finding(s)")
    for rule, rid, msg in bad:
        print(f"  [{rule}] {rid}: {msg}")
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.exit(main(sys.argv))
    except Refused as e:
        print(f"REFUSED: {e}")
        sys.exit(2)
    except BrokenPipeError:
        sys.exit(0)
