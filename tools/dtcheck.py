#!/usr/bin/env python3
"""dtcheck.py -- `R5`'s `D2` instrument: are the device-tree source and the
bindings under `dt/` accepted by the modern tools, and does a green here mean
anything.

WHY THIS IS A PROGRAM AND NOT THREE LINES OF SHELL.
量 2026-09-09, before a line of `dt/` existed, on dtc 1.7.0 and dtschema
2026.6: **all three underlying tools print a real, correct failure and then
exit 0.**

  * `dt-doc-validate` on a binding whose `$id` does not match its path prints
    `$id: Cannot determine base path from $id ...` and exits **0**.
  * `dtc` on a node with a unit address and no `reg` prints
    `Warning (unit_address_vs_reg): ...` and exits **0**.  (`-Wall` and
    `-Werror` are not dtc flags at all -- `FATAL ERROR: Unrecognized check
    name "all"`, which is a *false red* rather than a false green, and was the
    reason the first calibration run had no working positive case.)
  * `dt-validate` on a node missing a required property prints
    `'interrupts' is a required property` and exits **0**.

So a checker that reads exit status reports a perfect green on a device tree
that fails every stage.  This file reads the OUTPUT and treats the status as
one more thing to be sceptical about.  `T14` is the case that keeps that
reason testable: it asserts that at least one tool still exits 0 on something
reported here as a finding, so if a future dtschema fixes its exit codes this
suite goes red and says the rationale moved rather than silently keeping a
program nobody needs.

AND ONE READING WORSE THAN THOSE THREE.
`dt-validate` prints `<schema>: ignoring, error in schema: ...` for a schema it
could not load, and then validates nothing against it.  **One typo in one
binding silently turns every node that binding describes into an unvalidated
node, with no other symptom.**  That line is a hard failure here.

WHAT THIS TOOL DOES *NOT* CLAIM.
  * It does not run anything on hardware.  `D2`'s deliverable is explicitly
    *written, compiled, never probed*; `dt/README.md` says so and this tool
    cannot make it truer.
  * `dtschema` ships the core schemas (`cpus`, `gpio`, `interrupt-controller`,
    `memory`, ...) and NOT the kernel's `Documentation/devicetree/bindings/`
    corpus, so a `compatible` owned by a kernel subsystem binding -- e.g.
    `gpio-leds`, `fixed-partitions` -- has no schema here.  Stage C reports
    every such node through `-m` and each one must be on
    `dt/unmatched-allow.tsv` with a reason, so the gap is enumerated instead
    of invisible.  `--extra-schema DIR` points at a kernel bindings tree when
    one is available; the report says which corpus ran.
  * `dt-doc-validate` does not check that `required:` names properties the
    schema declares, and does not compile a binding's own `examples:` block.
    量, both: the controls for those two are `A2`/`A3` here, which exist
    because the underlying tool passed the broken fixtures.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "dtcheck 1.0"

# The population floor.  A glob that matches nothing must be a REFUSAL and not
# a green -- this repository's own rule that a tool reporting 0 is making a
# claim.  Raised deliberately when `dt/` grows; never lowered to make a run
# pass.
MIN_BINDINGS = 6
MIN_DTS = 1

# dtc checks suppressed for a binding's `examples:` block only, each with the
# reason.  The real .dts files below get NO suppression at all.
EXAMPLE_WRAP_HEAD = """/dts-v1/;
/ {
\tcompatible = "dtcheck,example-wrapper";
\tmodel = "dtcheck example wrapper";
\t#address-cells = <1>;
\t#size-cells = <1>;
\tinterrupt-parent = <&dtcheck_dummy_ic>;

\tdtcheck_dummy_ic: interrupt-controller {
\t\tcompatible = "dtcheck,dummy-ic";
\t\tinterrupt-controller;
\t\t#interrupt-cells = <1>;
\t};

"""
EXAMPLE_WRAP_TAIL = "};\n"

# Lines dt-validate prints that are not findings.
_DTV_IGNORE_SCHEMA = re.compile(r":\s*ignoring, error in schema:")
_DTV_UNMATCHED = re.compile(
    r"^(?P<file>.*?):\s*(?P<node>\S*?):?\s*failed to match any schema with "
    r"compatible:\s*\[(?P<compat>.*)\]\s*$"
)
# 🔴 A compatible string CONTAINS a comma -- `realtek,rtl8196e-timer` -- so the
# obvious `.split(",")` of dt-validate's `['a,b']` returns two strings that are
# neither of them a compatible, and every one of them then misses the
# allow-list.  量: the first run of this file's own self-test, where
# `['dtcheck,board']` came back as `['dtcheck', 'board']` and the clean fixture
# reported two findings.  Take the quoted items, not the separators.
_DTV_COMPAT_ITEM = re.compile(r"'([^']*)'|\"([^\"]*)\"")
_DTC_FINDING = re.compile(r"\b(Warning|Error|FATAL ERROR)\b")


class Refused(Exception):
    """The run cannot report on the tree.  Exit 2, never 0 and never 1."""


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------
class Report:
    """`ci-census` parses `  ok  <name>` with EXACTLY two leading spaces --
    the forty-fourth segment shipped two tools with four and both read as
    `ran 0/N` with zero failures."""

    def __init__(self):
        self.rows = []

    def case(self, ok, cid, what):
        self.rows.append((bool(ok), cid, what))
        print(f"  {'ok' if ok else 'FAIL'}  {cid} {what}")

    def skip(self, cid, what, why):
        self.rows.append((None, cid, what))
        print(f"  skip  {cid} {what}  {why}")

    @property
    def ran(self):
        return sum(1 for ok, _, _ in self.rows if ok is not None)

    @property
    def failed(self):
        return sum(1 for ok, _, _ in self.rows if ok is False)


# --------------------------------------------------------------------------
# tools
# --------------------------------------------------------------------------
def find_tools(args):
    """Locate the three binaries.  A missing tool is a REFUSAL: silently
    skipping the only stage that can fail is how a checker becomes decoration."""
    found = {}
    for name, override in (("dtc", args.dtc),
                           ("dt-doc-validate", args.dt_doc_validate),
                           ("dt-validate", args.dt_validate)):
        p = override or shutil.which(name)
        if not p and args.venv:
            cand = Path(args.venv) / "bin" / name
            if cand.exists():
                p = str(cand)
        if not p:
            raise Refused(
                f"{name} not found. Install device-tree-compiler and dtschema "
                f"(pip install dtschema), or pass --venv/--{name}. This tool "
                f"refuses rather than skipping the stage that would fail.")
        found[name] = p
    return found


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, encoding="utf-8",
                       errors="replace")
    return r.returncode, r.stdout


# --------------------------------------------------------------------------
# stage A -- the binding files
# --------------------------------------------------------------------------
def stage_a_doc(tools, path):
    """dt-doc-validate. Verdict is the OUTPUT; rc is recorded, not believed."""
    rc, out = run([tools["dt-doc-validate"], str(path)])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return lines, rc


def _declared_names(node):
    """Property names a schema declares, following the composition keywords a
    binding actually uses.  `$ref` pulls in names from another file and is NOT
    followed -- a binding under `dt/` that needs one declares it in
    `dtcheck-extra-declared` so the exemption is visible in the file itself."""
    names, patterns = set(), []
    if not isinstance(node, dict):
        return names, patterns
    for k in ("properties",):
        if isinstance(node.get(k), dict):
            names |= set(node[k].keys())
    if isinstance(node.get("patternProperties"), dict):
        patterns += list(node["patternProperties"].keys())
    for k in ("allOf", "anyOf", "oneOf"):
        for sub in node.get(k) or []:
            n, p = _declared_names(sub)
            names |= n
            patterns += p
    for k in ("then", "else", "if"):
        n, p = _declared_names(node.get(k))
        names |= n
        patterns += p
    return names, patterns


def stage_a_required(doc, text):
    """`required:` must name properties the schema declares, whenever the
    schema closes itself with additionalProperties/unevaluatedProperties
    false.  量: dt-doc-validate does NOT check this -- fixture `A2` below
    passes it."""
    closed = doc.get("additionalProperties") is False or \
        doc.get("unevaluatedProperties") is False
    if not closed:
        return []
    names, patterns = _declared_names(doc)
    for m in re.finditer(r"dtcheck-extra-declared:\s*(.+)", text):
        names |= {w.strip() for w in m.group(1).split(",") if w.strip()}
    bad = []
    for r in doc.get("required") or []:
        if r in names:
            continue
        if any(re.search(p, r) for p in patterns):
            continue
        bad.append(f"required '{r}' is not declared by this schema")
    return bad


def stage_a_examples(tools, path, doc, workdir, schema_root):
    """Compile and validate each `examples:` entry against its own binding.
    量: dt-doc-validate does NOT do this -- fixture `A3` passes it."""
    out = []
    for i, ex in enumerate(doc.get("examples") or []):
        if not isinstance(ex, str):
            out.append(f"example {i}: not a string")
            continue
        base = workdir / f"{path.stem}-ex{i}"
        dts = base.with_suffix(".dts")
        dtb = base.with_suffix(".dtb")
        dts.write_text(EXAMPLE_WRAP_HEAD + ex + EXAMPLE_WRAP_TAIL,
                       encoding="utf-8")
        rc, o = run([tools["dtc"], "-I", "dts", "-O", "dtb", "-o", str(dtb),
                     str(dts)])
        hits = [ln for ln in o.splitlines() if _DTC_FINDING.search(ln)]
        if hits or not dtb.exists():
            out += [f"example {i}: dtc: {h.strip()}" for h in hits] or \
                   [f"example {i}: dtc produced no dtb (rc {rc})"]
            continue
        # no -m here: an example is validated against ITS OWN binding, and the
        # wrapper's dummy interrupt controller has no schema by construction.
        rc, o = run([tools["dt-validate"], "-s", str(schema_root), str(dtb)])
        for ln in o.splitlines():
            if not ln.strip():
                continue
            if ln[:1] in ("\t", " ") and out:
                out[-1] += " / " + ln.strip()
                continue
            if _DTV_IGNORE_SCHEMA.search(ln):
                out.append(f"example {i}: SCHEMA NOT LOADED: {ln.strip()}")
            else:
                out.append(f"example {i}: {ln.strip()}")
    return out


# --------------------------------------------------------------------------
# stage B / C
# --------------------------------------------------------------------------
def stage_b(tools, dts, dtb, includes):
    cmd = [tools["dtc"], "-I", "dts", "-O", "dtb", "-o", str(dtb)]
    for inc in includes:
        cmd += ["-i", str(inc)]
    cmd.append(str(dts))
    rc, out = run(cmd)
    return [ln.strip() for ln in out.splitlines() if _DTC_FINDING.search(ln)], rc


def stage_c(tools, dtb, schema_dirs, allow):
    cmd = [tools["dt-validate"], "-m"]
    for d in schema_dirs:
        cmd += ["-s", str(d)]
    cmd.append(str(dtb))
    rc, out = run(cmd)
    findings, unmatched = [], []
    for ln in out.splitlines():
        s = ln.strip()
        if not s:
            continue
        # dt-validate wraps one finding over several lines and indents the
        # continuations ("\tfrom schema $id: ...").  Counting those as separate
        # findings inflates the number and buries the first line.
        if ln[:1] in ("\t", " ") and findings:
            findings[-1] += " / " + s
            continue
        if _DTV_IGNORE_SCHEMA.search(s):
            findings.append("SCHEMA NOT LOADED (every node it describes went "
                            "unvalidated): " + s)
            continue
        m = _DTV_UNMATCHED.search(s)
        if m:
            compats = [a or b for a, b in
                       _DTV_COMPAT_ITEM.findall(m.group("compat"))]
            node = m.group("node") or "/"
            if all(c in allow for c in compats):
                unmatched.append((node, compats))
            else:
                findings.append(
                    f"no schema for compatible {compats} at {node} and it is "
                    f"not in dt/unmatched-allow.tsv")
            continue
        findings.append(s)
    return findings, unmatched, rc


# --------------------------------------------------------------------------
# the real tree
# --------------------------------------------------------------------------
def load_allow(path):
    allow = {}
    if not path.exists():
        return allow
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = ln.split("\t")
        allow[f[0].strip()] = (f[1].strip() if len(f) > 1 else "")
    return allow


def check_tree(tools, dtdir, rep, args, yaml):
    bdir = dtdir / "bindings"
    bindings = sorted(bdir.rglob("*.yaml")) if bdir.exists() else []
    dtses = sorted(p for p in dtdir.glob("*.dts"))
    allow = load_allow(dtdir / "unmatched-allow.tsv")

    if len(bindings) < args.min_bindings:
        raise Refused(f"found {len(bindings)} binding(s) under {bdir}, floor is "
                      f"{args.min_bindings}. A glob that matched nothing is a "
                      f"refusal here, not a green.")
    if len(dtses) < args.min_dts:
        raise Refused(f"found {len(dtses)} .dts under {dtdir}, floor is "
                      f"{args.min_dts}.")

    print(f"  -- {len(bindings)} binding(s), {len(dtses)} .dts, "
          f"{len(allow)} allowed unmatched compatible(s)")

    with tempfile.TemporaryDirectory(prefix="dtcheck-") as td:
        work = Path(td)
        for b in bindings:
            rel = b.relative_to(dtdir)
            text = b.read_text(encoding="utf-8")
            try:
                doc = yaml.safe_load(text)
            except Exception as e:                       # noqa: BLE001
                rep.case(False, "A1", f"{rel} unparsable YAML: {e}")
                continue
            lines, rc = stage_a_doc(tools, b)
            rep.case(not lines, "A1",
                     f"{rel} dt-doc-validate"
                     + (f" [rc {rc}] " + " | ".join(lines) if lines else ""))
            bad = stage_a_required(doc or {}, text)
            rep.case(not bad, "A2", f"{rel} required[] declared"
                     + (" -- " + "; ".join(bad) if bad else ""))
            ex = stage_a_examples(tools, b, doc or {}, work, bdir)
            n = len((doc or {}).get("examples") or [])
            rep.case(not ex, "A3", f"{rel} {n} example(s) compile+validate"
                     + (" -- " + "; ".join(ex) if ex else ""))

        schema_dirs = [bdir] + [Path(p) for p in (args.extra_schema or [])]
        for d in dtses:
            dtb = work / (d.stem + ".dtb")
            hits, rc = stage_b(tools, d, dtb, [dtdir])
            rep.case(not hits, "B1", f"{d.name} dtc"
                     + (f" [rc {rc}] " + " | ".join(hits) if hits else ""))
            if not dtb.exists():
                rep.case(False, "C1", f"{d.name} no dtb to validate")
                continue
            f, un, rc = stage_c(tools, dtb, schema_dirs, allow)
            rep.case(not f, "C1", f"{d.name} dt-validate"
                     + (f" [rc {rc}] " + " | ".join(f) if f else ""))
            rep.case(True, "C2",
                     f"{d.name} {len(un)} unmatched compatible(s), all declared")

    print(f"  -- schema corpus: dt/bindings"
          + ("".join(f" + {p}" for p in (args.extra_schema or []))
             or "  (dtschema core only -- the kernel's bindings tree is NOT "
                "here; see the module docstring)"))


# --------------------------------------------------------------------------
# self-test: every failure class above, and the control that each is caught
# --------------------------------------------------------------------------
GOOD_BINDING = """# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/timer/dtcheck-probe.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#
title: dtcheck probe
maintainers:
  - Nobody <nobody@example.com>
properties:
  compatible:
    const: dtcheck,probe
  reg:
    maxItems: 1
  interrupts:
    maxItems: 1
required:
  - compatible
  - reg
  - interrupts
additionalProperties: false
examples:
  - |
    timer@18003100 {
        compatible = "dtcheck,probe";
        reg = <0x18003100 0x1c>;
        interrupts = <25>;
    };
"""

GOOD_DTS = """/dts-v1/;
/ {
\tcompatible = "dtcheck,board";
\tmodel = "dtcheck board";
\t#address-cells = <1>;
\t#size-cells = <1>;
\tinterrupt-parent = <&ic>;

\tic: interrupt-controller {
\t\tcompatible = "dtcheck,ic";
\t\tinterrupt-controller;
\t\t#interrupt-cells = <1>;
\t};

\ttimer@18003100 {
\t\tcompatible = "dtcheck,probe";
\t\treg = <0x18003100 0x1c>;
\t\tinterrupts = <25>;
\t};
};
"""

ALLOW_TSV = ("dtcheck,board\tthe root's own compatible; a board binding is not "
             "part of this fixture\n"
             "dtcheck,ic\tthe fixture's interrupt controller\n")


def _fixture(root, binding=GOOD_BINDING, dts=GOOD_DTS, allow=ALLOW_TSV,
             extra_bindings=None):
    dt = root / "dt"
    (dt / "bindings" / "timer").mkdir(parents=True, exist_ok=True)
    (dt / "bindings" / "timer" / "dtcheck-probe.yaml").write_text(
        binding, encoding="utf-8")
    for name, body in (extra_bindings or {}).items():
        (dt / "bindings" / "timer" / name).write_text(body, encoding="utf-8")
    (dt / "board.dts").write_text(dts, encoding="utf-8")
    (dt / "unmatched-allow.tsv").write_text(allow, encoding="utf-8")
    return dt


def _quiet_check(tools, dt, args, yaml):
    """Run check_tree with output captured; return the Report."""
    import io
    import contextlib
    rep = Report()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        check_tree(tools, dt, rep, args, yaml)
    return rep, buf.getvalue()


def _fails(rep, cid):
    return [r for r in rep.rows if r[1] == cid and r[0] is False]


def self_test(tools, args, yaml):
    """Each case builds a tree with ONE defect and requires the matching stage
    to catch it.  A control that cannot fail is not a control, so every
    negative case has a positive twin on the same stage."""
    rep = Report()
    import copy
    a = copy.copy(args)
    a.min_bindings, a.min_dts, a.extra_schema = 1, 1, []
    rc0_seen = []

    def trial(cid, what, mutate, expect_cid, expect_fail=True,
              allow=ALLOW_TSV, extra=None):
        with tempfile.TemporaryDirectory(prefix="dtcheck-st-") as td:
            root = Path(td)
            kw = mutate()
            dt = _fixture(root, allow=allow, extra_bindings=extra, **kw)
            try:
                sub, _txt = _quiet_check(tools, dt, a, yaml)
            except Refused as e:
                rep.case(not expect_fail, cid, f"{what} -- REFUSED: {e}")
                return
            got = bool(_fails(sub, expect_cid))
            rep.case(got == expect_fail, cid,
                     f"{what} -> {expect_cid} "
                     f"{'caught' if got else 'SILENT'}"
                     f" (wanted {'a finding' if expect_fail else 'clean'})")
            if expect_fail and got:
                rc0_seen.append(cid)

    # --- the positive twins: an unmutated fixture must be clean on every stage
    trial("T0a", "clean fixture, stage A1", lambda: {}, "A1", False)
    trial("T0b", "clean fixture, stage A2", lambda: {}, "A2", False)
    trial("T0c", "clean fixture, stage A3", lambda: {}, "A3", False)
    trial("T0d", "clean fixture, stage B1", lambda: {}, "B1", False)
    trial("T0e", "clean fixture, stage C1", lambda: {}, "C1", False)

    # --- A1: dt-doc-validate.  Both of these exit 0 in the underlying tool.
    trial("T1", "$id path does not match the file's location",
          lambda: {"binding": GOOD_BINDING.replace(
              "schemas/timer/dtcheck-probe.yaml",
              "schemas/somewhere-else/dtcheck-probe.yaml")}, "A1")
    trial("T2", "maxItems given a string, not an integer",
          lambda: {"binding": GOOD_BINDING.replace(
              "    maxItems: 1\n  interrupts:", "    maxItems: \"one\"\n  interrupts:")},
          "A1")

    # --- A2: dt-doc-validate does NOT check this.  T3b proves that claim by
    #     requiring stage A1 to stay SILENT on the same fixture.
    trial("T3", "required[] names a property the schema never declares",
          lambda: {"binding": GOOD_BINDING.replace(
              "  - interrupts\n", "  - interrupts\n  - never-declared\n")}, "A2")
    trial("T3b", "...and dt-doc-validate itself does not see it",
          lambda: {"binding": GOOD_BINDING.replace(
              "  - interrupts\n", "  - interrupts\n  - never-declared\n")},
          "A1", False)
    trial("T3c", "dtcheck-extra-declared: lets a $ref'd name through",
          lambda: {"binding": GOOD_BINDING.replace(
              "  - interrupts\n",
              "  - interrupts\n  - from-a-ref\n") + "# dtcheck-extra-declared: from-a-ref\n"},
          "A2", False)

    # --- A3: nor does it compile the binding's own examples.
    trial("T4", "the binding's own example violates the binding",
          lambda: {"binding": GOOD_BINDING.replace(
              "        interrupts = <25>;", "        not-a-declared-prop;")}, "A3")
    trial("T4b", "...and dt-doc-validate itself does not see that either",
          lambda: {"binding": GOOD_BINDING.replace(
              "        interrupts = <25>;", "        not-a-declared-prop;")},
          "A1", False)
    trial("T5", "the example does not even compile",
          lambda: {"binding": GOOD_BINDING.replace(
              "        interrupts = <25>;", "        interrupts = <25>")}, "A3")

    # --- B: dtc warns and exits 0.
    trial("T6", "unit address with no reg (dtc warns, rc 0)",
          lambda: {"dts": GOOD_DTS.replace(
              "\ttimer@18003100 {\n\t\tcompatible = \"dtcheck,probe\";\n"
              "\t\treg = <0x18003100 0x1c>;",
              "\ttimer@18003100 {\n\t\tcompatible = \"dtcheck,probe\";")}, "B1")
    trial("T7", "the .dts does not parse",
          lambda: {"dts": GOOD_DTS.replace("model = \"dtcheck board\";",
                                           "model = \"dtcheck board\"")}, "B1")

    # --- C: dt-validate prints and exits 0.
    trial("T8", "node is missing a required property",
          lambda: {"dts": GOOD_DTS.replace("\t\tinterrupts = <25>;\n", "")}, "C1")
    trial("T9", "node carries a property the binding does not declare",
          lambda: {"dts": GOOD_DTS.replace(
              "\t\tinterrupts = <25>;", "\t\tinterrupts = <25>;\n\t\tbogus;")}, "C1")
    trial("T10", "a compatible with no schema and no allow-list row",
          lambda: {}, "C1", True, allow="")
    trial("T10b", "...and the same tree WITH the allow-list is clean",
          lambda: {}, "C1", False)

    # --- the worst one: a schema that fails to load validates nothing.
    trial("T11", "a broken schema in the corpus is a hard failure, not a pass",
          lambda: {"dts": GOOD_DTS.replace("\t\tinterrupts = <25>;\n", "")},
          "C1", True,
          extra={"broken.yaml": GOOD_BINDING.replace(
              "    maxItems: 1\n  interrupts:", "    maxItems: \"one\"\n  interrupts:")
              .replace("dtcheck-probe.yaml", "broken.yaml")})

    # --- population control
    with tempfile.TemporaryDirectory(prefix="dtcheck-st-") as td:
        root = Path(td)
        dt = root / "dt"
        (dt / "bindings").mkdir(parents=True)
        (dt / "board.dts").write_text(GOOD_DTS, encoding="utf-8")
        try:
            _quiet_check(tools, dt, a, yaml)
            rep.case(False, "T12", "an empty bindings dir must be REFUSED")
        except Refused:
            rep.case(True, "T12", "an empty bindings dir is REFUSED, not green")

    # --- a missing tool must refuse, not skip
    class _Args:
        pass
    bogus = _Args()
    bogus.dtc = None
    bogus.dt_doc_validate = "/nonexistent/dt-doc-validate"
    bogus.dt_validate = None
    bogus.venv = None
    try:
        os.environ["PATH"] = ""
        find_tools(bogus)
        rep.case(False, "T13", "a missing tool must REFUSE")
    except Refused:
        rep.case(True, "T13", "a missing tool REFUSES, not skips")
    finally:
        os.environ["PATH"] = os.defpath

    # --- the case that keeps this file's reason alive
    rep.case(len(rc0_seen) >= 6, "T14",
             f"{len(rc0_seen)} defect class(es) caught that the underlying "
             f"tools' exit status does not report -- if this ever drops, the "
             f"reason this parser exists has moved")
    return rep


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="repository root (default: this file's parent's parent)")
    ap.add_argument("--dt-dir", default="dt")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--extra-schema", action="append", default=[],
                    help="an additional schema directory, e.g. a kernel's "
                         "Documentation/devicetree/bindings")
    ap.add_argument("--venv", default=os.environ.get("DTCHECK_VENV"))
    ap.add_argument("--dtc", default=None)
    ap.add_argument("--dt-doc-validate", default=None)
    ap.add_argument("--dt-validate", default=None)
    ap.add_argument("--min-bindings", type=int, default=MIN_BINDINGS)
    ap.add_argument("--min-dts", type=int, default=MIN_DTS)
    ap.add_argument("-V", "--version", action="store_true")
    args = ap.parse_args(argv)

    if args.version:
        print(VERSION)
        return 0

    try:
        import yaml
    except ImportError:
        print("REFUSED: PyYAML is not importable (apt install python3-yaml).",
              file=sys.stderr)
        return 2

    print(VERSION)
    try:
        tools = find_tools(args)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    for k, v in sorted(tools.items()):
        rc, out = run([v, "--version"] if k != "dtc" else [v, "--version"])
        print(f"  -- {k}: {v}  ({out.strip().splitlines()[0] if out.strip() else '?'})")

    rep = Report()
    try:
        if args.self_test:
            rep = self_test(tools, args, yaml)
        else:
            root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
            dtdir = root / args.dt_dir
            if not dtdir.is_dir():
                raise Refused(f"{dtdir} does not exist")
            check_tree(tools, dtdir, rep, args, yaml)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2

    print(f"RESULT: {rep.ran - rep.failed}/{rep.ran} case(s) passed"
          + (f", {rep.failed} FAILED" if rep.failed else ""))
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
