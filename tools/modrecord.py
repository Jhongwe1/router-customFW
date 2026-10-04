#!/usr/bin/env python3
"""Which vendor files does rlxfw change, and by what?

`P4b`'s per-file modification record, GENERATED.  GPL-2.0 section 2(a) asks a
distributor to carry prominent notices stating that the files were changed and
the date; what a recipient of this project actually needs is narrower and
harder: WHICH of somebody else's files were changed, by WHAT, and anchored
WHERE.  This writes that down from the declarations, so the record cannot drift
from the build the way a hand-kept list does.

WHY A GENERATOR AND NOT A DOCUMENT.
量: before this tool there was no generator.  `tools/rlxfw-marks.py` has
`apply`, `check`, `verify` and `self-test`, and every one of them answers "is
the declaration realised in the tree or the artefact" -- none of them answers
"what does the declaration say, as a list a release can ship".  A hand-written
list is `CNT-1`'s class: a count about this repository's own contents, kept in
a second place, invalidated by a change somewhere else.  Four of those were
found in one morning.

THE FOUR DECLARATIONS IT READS, AND WHY EACH IS A DIFFERENT KIND.
    config/rlxfw-marks.tsv       insertions, one row per inserted line, each
                                 with an anchor that must occur EXACTLY ONCE
    config/host-compat/*.patch   unified diffs, applied with `patch -p1` from
                                 the staged `linux-2.6.30/`
                                 (讀 tools/rlxfw-kbuild.sh)
    config/busybox-patches/*     unified diffs, applied with `patch -p1` from
                                 the drop's busybox-1.13 (讀 tools/mkbusybox.sh)
    config/rlxfw-kernel.delta    a line-by-line delta against ONE vendor file,
                                 the board configuration template its own
                                 `# baseline-file:` header names

THE CHECK THAT MATTERS IS `--tree`, NOT THE LISTING.
Without `--tree` this tool restates the declarations: it can say a patch claims
to change `arch/rlx/Kconfig`, and nothing more.  With `--tree` it resolves every
anchor against a staged tree -- each marks anchor exactly once, each patch hunk
pre-image exactly once with the series applied IN ORDER, and the delta's
baseline file byte-for-byte against its declared sha256.  A record emitted
without `--tree` says so in its own header, because a record that looks checked
and is not is worse than one that says it is a listing.

WHY THE PATCH SERIES IS APPLIED IN MEMORY.
量: `0005` and `0007` both change `arch/rlx/Kconfig`, and `0007`'s hunk is at
line 18 of the file `0005` already inserted a line into.  A checker that tested
every hunk against the PRISTINE tree would report `0007` as not applying, which
would be a fact about the checker.  So each hunk is resolved against the file as
the preceding hunks left it, which is what `patch` itself does.

Usage
    tools/modrecord.py emit   --config DIR [--tree DIR] [--out FILE]
    tools/modrecord.py check  --config DIR --record FILE [--tree DIR]
    tools/modrecord.py --self-test [--config DIR]

`emit` with no `--out` writes to stdout.  With `--out` it builds the whole
record in memory, writes `FILE.tmp` and `os.replace`s it, so a refusal leaves
neither a truncated record nor a stray temporary.
"""

import io
import os
import re
import shutil
import sys
import tempfile
import hashlib

VERSION = "1.0"

MARKS_COLS = ("id", "file", "position", "anchor", "insert", "witness", "reason")

# 讀 tools/rlxfw-kbuild.sh: `cd "$top/linux-2.6.30" && patch -p1`.
HOST_COMPAT_ROOT = "linux-2.6.30"

# 讀 tools/mkbusybox.sh `drop_src`: TWO shapes, because the drops disagree on
# where they keep busybox.  The record prints the first and names the second in
# its header rather than picking one silently.
BUSYBOX_ROOTS = ("users/busybox-1.13", "rtl819x/users/busybox-1.13")

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def die(msg):
    sys.stderr.write("modrecord: %s\n" % msg)
    raise SystemExit(3)


def _read(path, what):
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as f:
            return f.read()
    except IOError as e:
        die("cannot read %s (%s): %s" % (what, path, e.strerror))
    except UnicodeDecodeError:
        die("%s (%s) is not UTF-8. Every declaration this reads is text; a "
            "binary here means the wrong path was given" % (what, path))


def _lines(text):
    """Split keeping the line endings, so a hunk compares byte-for-byte."""
    return text.splitlines(True)


# --------------------------------------------------------------------------
# config/rlxfw-marks.tsv
# --------------------------------------------------------------------------

def parse_marks(path):
    text = _read(path, "the marks declaration")
    drop = None
    rows = []
    for lineno, raw in enumerate(_lines(text), 1):
        line = raw.rstrip("\r\n")
        if line.startswith("#"):
            m = re.match(r"#\s*baseline-drop:\s*(.+?)\s*$", line)
            if m and drop is None:
                drop = m.group(1)
            continue
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) != len(MARKS_COLS):
            die("%s:%d: %d tab-separated field(s), expected %d (%s). A row "
                "this tool cannot read is refused, never skipped"
                % (path, lineno, len(f), len(MARKS_COLS),
                   ", ".join(MARKS_COLS)))
        d = dict(zip(MARKS_COLS, f))
        if not d["file"].strip():
            die("%s:%d: row %s has an empty file" % (path, lineno, d["id"]))
        if not d["anchor"].strip():
            die("%s:%d: row %s has an empty anchor. An empty anchor matches "
                "everywhere, so it is a refusal and not a wildcard"
                % (path, lineno, d["id"]))
        if d["position"] not in ("before", "after"):
            die("%s:%d: row %s position %r is not `before` or `after`"
                % (path, lineno, d["id"], d["position"]))
        d["lineno"] = lineno
        rows.append(d)
    if not rows:
        die("%s: no rows. An empty declaration would let this tool report a "
            "record with no vendor file in it, and that zero would be the "
            "parser's and not the project's" % path)
    if drop is None:
        die("%s: no `# baseline-drop:` header. The record's drop column would "
            "then be this tool's guess" % path)
    return drop, rows


# --------------------------------------------------------------------------
# unified diffs
# --------------------------------------------------------------------------

def parse_patch(path):
    """-> [ (target, [ {header, pre, post} ]) ], one entry per file section.

    The hunk header's own line counts are used to consume the body, so a
    removed line that happens to begin `--- ` cannot be mistaken for a file
    header.  Everything before the first `--- ` is the patch's prose and is
    not read.
    """
    lines = _lines(_read(path, "a patch"))
    sections = []
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i]
        if s.startswith("--- ") and i + 1 < n and lines[i + 1].startswith("+++ "):
            target = _target(lines[i + 1], path, i + 2)
            i += 2
            hunks = []
            while i < n:
                m = HUNK_RE.match(lines[i])
                if not m:
                    break
                header = lines[i].rstrip("\r\n")
                n_pre = int(m.group(2)) if m.group(2) is not None else 1
                n_post = int(m.group(4)) if m.group(4) is not None else 1
                i += 1
                pre, post = [], []
                got_pre = got_post = 0
                while i < n and (got_pre < n_pre or got_post < n_post):
                    b = lines[i]
                    # STOP EARLY at the next structure, even with the counts
                    # unmet. 量 2026-10-04: the busybox patch's third hunk
                    # declares 12/6 and its body holds 10/4, and GNU `patch`
                    # applies it anyway because it anchors on CONTEXT and not
                    # on the header's arithmetic. A parser that refused here
                    # would be reporting a fact about itself. The counts are
                    # still read, because they are what keeps a removed line
                    # beginning `--- ` from being taken for a file header.
                    if HUNK_RE.match(b):
                        break
                    if (b.startswith("--- ") and i + 1 < n
                            and lines[i + 1].startswith("+++ ")):
                        break
                    if b.startswith("\\"):          # "\ No newline at ..."
                        i += 1
                        continue
                    if b.startswith(" ") or b == "\n" or b == "\r\n":
                        body = b[1:] if b.startswith(" ") else b
                        pre.append(body); post.append(body)
                        got_pre += 1; got_post += 1
                    elif b.startswith("-"):
                        pre.append(b[1:]); got_pre += 1
                    elif b.startswith("+"):
                        post.append(b[1:]); got_post += 1
                    else:
                        die("%s:%d: %r is not a hunk body line. %s declared "
                            "%d/%d lines and this tool had read %d/%d"
                            % (path, i + 1, b[:40], header, n_pre, n_post,
                               got_pre, got_post))
                    i += 1
                if not pre:
                    die("%s: %s has an EMPTY pre-image, which matches "
                        "everywhere. This tool cannot anchor it" % (path,
                                                                    header))
                hunks.append({"header": header, "pre": pre, "post": post,
                              "short": (n_pre - got_pre, n_post - got_post)})
            if not hunks:
                die("%s: the section for %s has no `@@` hunk" % (path, target))
            sections.append((target, hunks))
        else:
            i += 1
    if not sections:
        die("%s: no `--- `/`+++ ` file header. A patch whose target this tool "
            "cannot read is refused, because the record's whole job is to "
            "name the file" % path)
    return sections


def _target(plus_line, path, lineno):
    s = plus_line.rstrip("\r\n")
    s = s[4:]
    s = re.split(r"\t", s, 1)[0].strip()          # 0009 carries a timestamp
    if not s or s == "/dev/null":
        die("%s:%d: `+++ %s` names no file" % (path, lineno, s))
    parts = s.split("/")
    if len(parts) < 2:
        die("%s:%d: `+++ %s` has no directory to strip; every patch here is "
            "applied with `patch -p1`" % (path, lineno, s))
    return "/".join(parts[1:])                     # -p1


def _find_all(lines, block):
    out = []
    k = len(block)
    for i in range(0, len(lines) - k + 1):
        if lines[i:i + k] == block:
            out.append(i)
    return out


def _apply_in_memory(lines, hunks, path, target):
    cur = list(lines)
    for h in hunks:
        at = _find_all(cur, h["pre"])
        if not at:
            die("%s: %s does not apply to %s: its pre-image is not in the "
                "file. Not a skip -- a hunk that moved is the thing this "
                "record exists to catch" % (path, h["header"], target))
        if len(at) > 1:
            die("%s: %s matches %s in %d places. Refusing to pick one"
                % (path, h["header"], target, len(at)))
        i = at[0]
        cur = cur[:i] + h["post"] + cur[i + len(h["pre"]):]
    return cur


# --------------------------------------------------------------------------
# config/rlxfw-kernel.delta
# --------------------------------------------------------------------------

def parse_delta(path):
    text = _read(path, "the kernel delta")
    hdr = {}
    n_rows = 0
    for raw in _lines(text):
        line = raw.rstrip("\r\n")
        if line.startswith("#"):
            m = re.match(r"#\s*(baseline-drop|baseline-file|baseline-sha256|"
                         r"baseline-bytes):\s*(.+?)\s*$", line)
            if m and m.group(1) not in hdr:
                hdr[m.group(1)] = m.group(2)
            continue
        if line.strip():
            n_rows += 1
    for k in ("baseline-drop", "baseline-file", "baseline-sha256"):
        if k not in hdr:
            die("%s: no `# %s:` header. The record cannot name the vendor "
                "file this delta is against" % (path, k))
    if n_rows == 0:
        die("%s: no rows. An empty delta would put a vendor file in the "
            "record with nothing done to it" % path)
    hdr["rows"] = n_rows
    return hdr


# --------------------------------------------------------------------------
# derivation
# --------------------------------------------------------------------------

def _norm(s):
    """Whitespace-collapsed, for Makefile anchors. `tools/rlxfw-marks.py`
    matches `MK` the same way, because Kbuild lines are tab-aligned and the
    declaration is tab-separated so the anchor cannot carry a tab."""
    return re.sub(r"[ \t]+", " ", s).strip()


def derive(configdir, tree=None, busybox_drop=None):
    """Everything is parsed and every anchor resolved BEFORE anything is
    written. Nothing in here touches the filesystem except to read."""
    if not os.path.isdir(configdir):
        die("--config %s is not a directory" % configdir)
    marks_path = os.path.join(configdir, "rlxfw-marks.tsv")
    delta_path = os.path.join(configdir, "rlxfw-kernel.delta")
    hc_dir = os.path.join(configdir, "host-compat")
    bb_dir = os.path.join(configdir, "busybox-patches")
    for p, what in ((marks_path, "rlxfw-marks.tsv"),
                    (delta_path, "rlxfw-kernel.delta")):
        if not os.path.isfile(p):
            die("--config %s has no %s. This tool reads four declarations and "
                "a missing one would silently shrink the record"
                % (configdir, what))
    for d, what in ((hc_dir, "host-compat/"), (bb_dir, "busybox-patches/")):
        if not os.path.isdir(d):
            die("--config %s has no %s/ (see above)" % (configdir, what))

    drop, mrows = parse_marks(marks_path)
    delta = parse_delta(delta_path)
    if _norm(delta["baseline-drop"]) != _norm(drop):
        die("the marks declaration says drop %r and the kernel delta says "
            "%r. Two declarations against two different trees cannot share "
            "one record" % (drop, delta["baseline-drop"]))

    hc = sorted(f for f in os.listdir(hc_dir) if f.endswith(".patch"))
    bb = sorted(f for f in os.listdir(bb_dir) if f.endswith(".patch"))
    if not hc:
        die("%s holds no .patch. `tools/rlxfw-kbuild.sh` applies what is "
            "there, so an empty directory is a refusal here rather than a "
            "record with nine fewer files than the build has" % hc_dir)
    if not bb:
        die("%s holds no .patch (see above, for tools/mkbusybox.sh)" % bb_dir)

    files = {}        # path -> record dict

    def touch(path, kind, by, anchors, dropname, note=""):
        e = files.setdefault(path, {"path": path, "kind": set(), "by": [],
                                    "anchors": [], "drop": dropname,
                                    "note": note, "state": []})
        e["kind"].add(kind)
        e["by"].append(by)
        e["anchors"].extend(anchors)

    # --- the marks table
    for r in mrows:
        touch(r["file"], "insert", r["id"], [r["anchor"]], drop)

    # --- the two patch series
    series = ([(hc_dir, f, HOST_COMPAT_ROOT, drop, "") for f in hc]
              + [(bb_dir, f, BUSYBOX_ROOTS[0],
                  busybox_drop or drop,
                  "root is also %s in the other drop shape"
                  % BUSYBOX_ROOTS[1]) for f in bb])
    parsed = []
    shortfalls = []
    for d, f, root, dropname, note in series:
        p = os.path.join(d, f)
        for target, hunks in parse_patch(p):
            full = "%s/%s" % (root, target)
            touch(full, "patch", f, [h["header"] for h in hunks], dropname,
                  note)
            for h in hunks:
                if h["short"] != (0, 0):
                    shortfalls.append((f, full, h["header"], h["short"]))
            parsed.append((p, f, root, target, full, hunks))

    # --- the kernel configuration delta
    touch(delta["baseline-file"], "config-delta",
          "%s row(s)" % delta["rows"],
          ["sha256 %s" % delta["baseline-sha256"][:8]], drop)

    # ---------------------------------------------------------------- anchors
    resolved = tree is not None
    if resolved:
        if not os.path.isdir(tree):
            die("--tree %s is not a directory" % tree)
        _resolve_marks(mrows, tree, files)
        _resolve_patches(parsed, tree, files)
        _resolve_delta(delta, tree, files)
    else:
        for e in files.values():
            e["state"] = ["declared"] * len(e["anchors"])

    return {"drop": drop, "delta": delta, "marks": mrows,
            "host_compat": hc, "busybox": bb, "shortfalls": shortfalls,
            "files": files, "resolved": resolved, "tree": tree,
            "busybox_drop": busybox_drop}


def _resolve_marks(mrows, tree, files):
    for r in mrows:
        p = os.path.join(tree, *r["file"].split("/"))
        if not os.path.isfile(p):
            die("row %s names %s and the tree has no such file"
                % (r["id"], r["file"]))
        body = [_norm(x) for x in _lines(_read(p, "a tree file"))]
        want = _norm(r["anchor"])
        hits = [i for i, x in enumerate(body) if x == want]
        if not hits:
            die("row %s: anchor not found in %s: %r. Not skipped -- an anchor "
                "that moved is the finding, not a nuisance"
                % (r["id"], r["file"], r["anchor"]))
        if len(hits) > 1:
            die("row %s: anchor occurs %d times in %s: %r. Refusing to pick "
                "one" % (r["id"], len(hits), r["file"], r["anchor"]))
        files[r["file"]]["state"].append("1 of 1")


def _resolve_patches(parsed, tree, files):
    """Applied IN DECLARED ORDER, in memory, so a later patch is resolved
    against the file an earlier one left behind."""
    state = {}
    for p, f, root, target, full, hunks in parsed:
        if full not in state:
            disk = os.path.join(tree, *full.split("/"))
            if not os.path.isfile(disk):
                die("%s changes %s and the tree has no such file" % (f, full))
            state[full] = _lines(_read(disk, "a tree file"))
        state[full] = _apply_in_memory(state[full], hunks, p, full)
        files[full]["state"].extend(["applies"] * len(hunks))


def _resolve_delta(delta, tree, files):
    rel = delta["baseline-file"]
    p = os.path.join(tree, *rel.split("/"))
    if not os.path.isfile(p):
        die("the delta's baseline-file %s is not in the tree" % rel)
    try:
        with io.open(p, "rb") as fh:
            blob = fh.read()
    except IOError as e:
        die("cannot read %s: %s" % (p, e.strerror))
    got = hashlib.sha256(blob).hexdigest()
    want = delta["baseline-sha256"].strip().lower()
    if got != want:
        die("the delta's baseline %s hashes to %s and the declaration says "
            "%s. A delta against a different file is not this record's"
            % (rel, got[:16], want[:16]))
    files[rel]["state"].append("sha256 ok")


# --------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------

def _cell(s):
    return s.replace("|", r"\|")


KINDS = ("insert", "patch", "config-delta")


def render(d):
    files = d["files"]
    order = sorted(files)
    out = []
    w = out.append
    w("# Per-file modification record — rlxfw's changes to vendor source\n")
    w("\n")
    w("**GENERATED by `tools/modrecord.py` %s. Do not edit.** Re-run\n"
      "`tools/modrecord.py emit` and commit what it writes;\n"
      "`tools/modrecord.py check` refuses if this file and the declarations\n"
      "disagree. This file is a listing of the declarations, not a reading of\n"
      "the vendor's code.\n" % VERSION)
    w("\n")
    w("| | |\n|---|---|\n")
    w("| drop | `%s` 讀, from the `# baseline-drop:` header of "
      "`config/rlxfw-marks.tsv`, which `config/rlxfw-kernel.delta` agrees "
      "with |\n" % _cell(d["drop"]))
    w("| declarations read | `config/rlxfw-marks.tsv` (%d row(s)), "
      "`config/host-compat/` (%d patch(es)), `config/busybox-patches/` "
      "(%d patch(es)), `config/rlxfw-kernel.delta` (%d row(s)) |\n"
      % (len(d["marks"]), len(d["host_compat"]), len(d["busybox"]),
         d["delta"]["rows"]))
    w("| vendor files touched | **%d** |\n" % len(order))
    if d["resolved"]:
        w("| anchors | 量 resolved against the tree at `%s`: every marks "
          "anchor found exactly once, every patch hunk applied in declared "
          "order, the delta's baseline matched by sha256 |\n"
          % _cell(d["tree"]))
    else:
        w("| anchors | 🔴 **NOT resolved: no `--tree` was given.** Every row "
          "below restates its declaration and nothing was read out of a "
          "vendor tree |\n")
    w("| patch roots | `config/host-compat/` applies with `patch -p1` from "
      "`%s` 讀 `tools/rlxfw-kbuild.sh`; `config/busybox-patches/` from `%s`, "
      "which is `%s` in the other drop shape 讀 `tools/mkbusybox.sh` |\n"
      % (HOST_COMPAT_ROOT, BUSYBOX_ROOTS[0], BUSYBOX_ROOTS[1]))
    if d["busybox_drop"]:
        w("| busybox drop | `%s`, given with `--busybox-drop` |\n"
          % _cell(d["busybox_drop"]))
    else:
        w("| busybox drop | 推 the same drop; `tools/mkbusybox.sh` takes "
          "`--drop` and nothing in `config/busybox-patches/` declares one, so "
          "pass `--busybox-drop` when a build used another |\n")
    if d["shortfalls"]:
        bits = ", ".join("`%s` %s on `%s`, body short by %d/%d"
                         % (f, _cell(h), _cell(t), s[0], s[1])
                         for f, t, h, s in d["shortfalls"])
        w("| 🔴 hunk headers that disagree with their own bodies | **%d**: %s. "
          "The pre-image used below is the BODY, which is what GNU `patch` "
          "anchors on; the header's arithmetic is not what applies the hunk. "
          "Reported rather than repaired: the patch is applied as it stands "
          "and editing it would move `RECIPE_ID` |\n"
          % (len(d["shortfalls"]), bits))
    else:
        w("| hunk headers against their bodies | 量 **0** disagree |\n")
    w("\n")
    w("| # | vendor file | kind | made by | anchor(s) | anchor state |\n")
    w("|---:|---|---|---|---|---|\n")
    for i, path in enumerate(order, 1):
        e = files[path]
        kind = ", ".join(k for k in KINDS if k in e["kind"])
        by = ", ".join("`%s`" % b for b in e["by"])
        anc = "<br>".join("`%s`" % _cell(a) for a in e["anchors"])
        st = ", ".join(sorted(set(e["state"]))) if e["state"] else "—"
        if e["state"]:
            st = "%s (%d)" % (st, len(e["state"]))
        note = (" " + e["note"]) if e["note"] else ""
        w("| %d | `%s`%s | %s | %s | %s | %s |\n"
          % (i, _cell(path), note, kind, by, anc, st))
    w("\n")
    w("## What this record does not establish\n")
    w("\n")
    w("- It does not say the change is **right**, only that the declaration\n"
      "  says it and %s.\n"
      % ("the anchor resolves in the tree given" if d["resolved"]
         else "no tree was read"))
    w("- It does not cover vendor files the build changes WITHOUT a\n"
      "  declaration. 量 that is what `tools/vendor-tripwire.sh` and the\n"
      "  re-stage rule are for; this tool reads declarations and cannot see\n"
      "  a write it is not told about.\n")
    w("- It does not establish the vendor files' own licences: 殘留 `SBOM-2`\n"
      "  records that 35 compiled kernel sources plus 3 in the loader stub\n"
      "  carry no licence text at all.\n")
    w("- A row's `anchor state` is about the tree this ran against, not about\n"
      "  the tree a recipient stages.\n")
    return "".join(out)


def _write(path, text):
    """Build, write `.tmp`, replace. Never `open(path, 'w')` first."""
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except OSError as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        die("cannot write %s: %s" % (path, e.strerror))


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

_MARK_HDR = "# a synthetic declaration\n# baseline-drop: src-vendor/fake @ dead\n"

_C = ("#include <one.h>\n"
      "void f(void)\n"
      "{\n"
      "\tone();\n"
      "\ttwo();\n"
      "}\n")

_MKFILE = "obj-y += a.o\nobj-y\t+= b.o\n"

_CFG = "CONFIG_A=y\n# CONFIG_B is not set\n"


def _row(*f):
    return "\t".join(f) + "\n"


def _mkpatch(target, pre, post, prose="prose line\n", inflate=0):
    body = "".join(" " + x for x in pre[:1])
    body += "".join("-" + x for x in pre[1:])
    body += "".join("+" + x for x in post[1:])
    n_pre, n_post = len(pre) + inflate, len(post) + inflate
    return ("%s--- a/%s\n+++ b/%s\n@@ -1,%d +1,%d @@\n%s"
            % (prose, target, target, n_pre, n_post, body))


def _fixture(tmp, extra_mark=None, extra_patch=None, bad_anchor=False,
             twice=False, bad_hunk=False, bad_fields=False, no_header=False,
             bad_sha=False, short_hunk=0):
    cfg = os.path.join(tmp, "config")
    tree = os.path.join(tmp, "tree")
    for d in ("host-compat", "busybox-patches"):
        os.makedirs(os.path.join(cfg, d))
    os.makedirs(os.path.join(tree, "linux-2.6.30", "sub"))
    os.makedirs(os.path.join(tree, "linux-2.6.30", "drivers"))
    os.makedirs(os.path.join(tree, "users", "busybox-1.13", "net"))
    os.makedirs(os.path.join(tree, "boards"))

    def put(rel, text):
        p = os.path.join(tree, *rel.split("/"))
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return p

    put("linux-2.6.30/sub/a.c", _C + ("\tone();\n" if twice else ""))
    put("linux-2.6.30/drivers/Makefile", _MKFILE)
    put("linux-2.6.30/sub/h.c", _C)
    put("users/busybox-1.13/net/b.c", _C)
    put("linux-2.6.30/extra.c", _C)
    cfgfile = put("boards/base.config", _CFG)
    with io.open(cfgfile, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    if bad_sha:
        sha = "0" * 64

    # The anchors carry NO tab: this file is tab-separated, so an anchor
    # cannot hold one, and `_norm` is what makes it match the tree's
    # indentation. The first fixture written here did carry one and the
    # parser refused it, which is the refusal working.
    rows = [_row("B0", "linux-2.6.30/sub/a.c", "after",
                 "nosuch();" if bad_anchor else "one();",
                 'rlxfw_mark("B0");', "", "the reason"),
            _row("MK", "linux-2.6.30/drivers/Makefile", "after",
                 "obj-y += b.o", "obj-y += mine.o", "str:mine", "the reason")]
    if bad_fields:
        rows.append("B1\tlinux-2.6.30/sub/h.c\tafter\n")
    if extra_mark:
        rows.append(_row("B9", extra_mark, "after", "two();",
                         'rlxfw_mark("B9");', "", "the planted row"))
    with io.open(os.path.join(cfg, "rlxfw-marks.tsv"), "w",
                 encoding="utf-8", newline="") as f:
        f.write(_MARK_HDR + "".join(rows))

    pre = ["#include <one.h>\n", "void f(void)\n"]
    post = ["#include <one.h>\n", "void g(void)\n"]
    if bad_hunk:
        pre = ["#include <nope.h>\n", "void f(void)\n"]
    p1 = _mkpatch("sub/h.c", pre, post, inflate=short_hunk)
    if no_header:
        p1 = "prose only, no file header\n@@ -1,1 +1,1 @@\n context\n"
    with io.open(os.path.join(cfg, "host-compat", "0001-a.patch"), "w",
                 encoding="utf-8", newline="") as f:
        f.write(p1)
    if extra_patch:
        with io.open(os.path.join(cfg, "host-compat", "0002-b.patch"), "w",
                     encoding="utf-8", newline="") as f:
            f.write(_mkpatch(extra_patch, pre, post))
    with io.open(os.path.join(cfg, "busybox-patches", "0001-c.patch"), "w",
                 encoding="utf-8", newline="") as f:
        f.write(_mkpatch("net/b.c", pre, post))

    with io.open(os.path.join(cfg, "rlxfw-kernel.delta"), "w",
                 encoding="utf-8", newline="") as f:
        f.write("# a synthetic delta\n"
                "# baseline-drop: src-vendor/fake @ dead\n"
                "# baseline-file: boards/base.config\n"
                "# baseline-sha256: %s\n"
                "set\tCONFIG_A\ty\tn\t-\tthe reason\n" % sha)
    return cfg, tree


def self_test(live_config):
    rows = []

    def ck(name, ok, detail):
        rows.append((name, bool(ok), detail))

    def refuses(fn, *a, **kw):
        err = io.StringIO()
        keep, sys.stderr = sys.stderr, err
        try:
            fn(*a, **kw)
            return False, "returned", err.getvalue()
        except SystemExit as e:
            return True, "exit %s" % e.code, err.getvalue()
        except Exception as e:                      # noqa: BLE001
            return False, "RAW %s: %s" % (type(e).__name__, e), err.getvalue()
        finally:
            sys.stderr = keep

    def permits(fn, *a, **kw):
        """A case that must SUCCEED. A refusal here is a failed case, not an
        aborted suite: a suite that dies on its first green case reports
        nothing at all about the eleven below it."""
        err = io.StringIO()
        keep, sys.stderr = sys.stderr, err
        try:
            return fn(*a, **kw), ""
        except SystemExit as e:
            return None, "REFUSED exit %s: %s" % (e.code,
                                                  err.getvalue().strip())
        except Exception as e:                      # noqa: BLE001
            return None, "RAW %s: %s" % (type(e).__name__, e)
        finally:
            sys.stderr = keep

    tmp = tempfile.mkdtemp(prefix="modrecord-")
    try:
        # M1 -- liveness on the synthetic declaration. A parser that returns
        # nothing would make every "not found" case below pass for free.
        cfg, tree = _fixture(tmp)
        d, why = permits(derive, cfg, tree)
        got = sorted(d["files"]) if d else []
        ck("M1  the synthetic declaration yields its planted files",
           got == ["boards/base.config",
                   "linux-2.6.30/drivers/Makefile",
                   "linux-2.6.30/sub/a.c",
                   "linux-2.6.30/sub/h.c",
                   "users/busybox-1.13/net/b.c"],
           why or "%d file(s): %s" % (len(got), ", ".join(got)))

        # M2 -- A PLANTED MODIFICATION MUST BE FOUND. One extra marks row on a
        # vendor file no other source names.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, extra_mark="linux-2.6.30/extra.c")
        d, why = permits(derive, cfg, tree)
        ck("M2  a planted marks row on a new vendor file is in the record",
           d is not None and "linux-2.6.30/extra.c" in d["files"],
           why or ", ".join(sorted(d["files"])))

        # M3 -- the same, planted in the PATCH set rather than the table.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, extra_patch="extra.c")
        d, why = permits(derive, cfg, tree)
        ck("M3  a planted patch on a new vendor file is in the record",
           d is not None and "linux-2.6.30/extra.c" in d["files"],
           why or ", ".join(sorted(d["files"])))

        # M4 -- A PLANTED ANCHOR THAT MUST FAIL TO MATCH.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, bad_anchor=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M4  a marks anchor absent from the tree is a refusal",
           ok and "anchor not found" in err, "%s / %s" % (why, err.strip()))

        # M5 -- an anchor occurring twice is not resolved by picking the first.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, twice=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M5  an anchor occurring twice is a refusal",
           ok and "occurs 2 times" in err, "%s / %s" % (why, err.strip()))

        # M6 -- a patch hunk whose pre-image is not in the tree.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, bad_hunk=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M6  a hunk that does not apply is a refusal",
           ok and "does not apply" in err, "%s / %s" % (why, err.strip()))

        # M7 -- the NEGATIVE control: a guard shown permitting. Same fixture,
        # anchor present exactly once, must be green AND must emit.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp)
        d, why = permits(derive, cfg, tree)
        text = render(d) if d else ""
        ck("M7  the same fixture with a sound anchor is permitted",
           "vendor files touched | **5**" in text and "1 of 1" in text,
           why or "%d bytes" % len(text))

        # M8 -- emit writes `path` and leaves no `path.tmp`; a refusal leaves
        # neither. Not `open(path, 'w')` before the content exists.
        out = os.path.join(tmp, "rec.md")
        _write(out, text)
        a = os.path.isfile(out) and not os.path.exists(out + ".tmp")
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, bad_anchor=True)
        out2 = os.path.join(tmp, "rec2.md")
        refuses(main, ["emit", "--config", cfg, "--tree", tree,
                       "--out", out2])
        b = not os.path.exists(out2) and not os.path.exists(out2 + ".tmp")
        ck("M8  emit replaces atomically and a refusal writes nothing",
           a and b, "wrote=%s refusal-clean=%s" % (a, b))

        # M9 -- a malformed row is a refusal WITH A REASON and no traceback.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, bad_fields=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M9  a wrong field count refuses with a reason, not a traceback",
           ok and "tab-separated field" in err and "Traceback" not in err,
           "%s / %s" % (why, err.strip()[:90]))

        # M10 -- a patch whose target cannot be read.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, no_header=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M10 a patch with no file header is a refusal naming the file",
           ok and "0001-a.patch" in err, "%s / %s" % (why, err.strip()[:90]))

        # M11 -- the delta's baseline sha256 is checked, not trusted.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, bad_sha=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M11 a delta baseline whose sha256 differs is a refusal",
           ok and "hashes to" in err, "%s / %s" % (why, err.strip()[:90]))

        # M13 -- a hunk header that over-declares its own body is REPORTED,
        # not refused, and the pre-image used is the body. This case exists
        # because the real busybox patch is such a hunk (量 12/6 declared,
        # 10/4 in the body) and the first version of this parser refused it,
        # which would have been a verdict about the parser.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, short_hunk=2)
        d, why = permits(derive, cfg, tree)
        sf = d["shortfalls"] if d else []
        text = render(d) if d else ""
        ck("M13 a hunk header over-declaring its body is reported, not "
           "refused",
           len(sf) == 1 and sf[0][3] == (2, 2)
           and "disagree with their own bodies" in text,
           why or "%d shortfall(s): %s" % (len(sf), sf))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # M12 -- LIVE liveness. Without this, every count above is about a
    # fixture this file wrote, and a parser that cannot read the real
    # declarations would still be green.
    if not os.path.isdir(live_config):
        ck("M12 the repository's own declarations parse", False,
           "%s is not a directory -- run this from the repository root or "
           "pass --config" % live_config)
    else:
        err = io.StringIO()
        keep, sys.stderr = sys.stderr, err
        try:
            d = derive(live_config)
            n = len(d["files"])
            ck("M12 the repository's own declarations parse",
               n >= 20 and len(d["host_compat"]) >= 1
               and len(d["busybox"]) >= 1 and len(d["marks"]) >= 1,
               "%d vendor file(s), %d marks row(s), %d + %d patch(es)"
               % (n, len(d["marks"]), len(d["host_compat"]),
                  len(d["busybox"])))
        except SystemExit as e:
            ck("M12 the repository's own declarations parse", False,
               "refused, exit %s: %s" % (e.code, err.getvalue().strip()))
        finally:
            sys.stderr = keep

    print("modrecord %s self-test" % VERSION)
    bad = 0
    for name, ok, detail in rows:
        if not ok:
            bad += 1
        print("  %s  %-62s %s" % ("\033[32mok \033[0m" if ok
                                  else "\033[31mFAIL\033[0m", name, detail))
    print("")
    if bad:
        print("RESULT: \033[31m%d of %d case(s) failed\033[0m"
              % (bad, len(rows)))
        return 1
    print("RESULT: \033[32mall %d case(s) pass\033[0m" % len(rows))
    return 0


# --------------------------------------------------------------------------

def main(argv):
    if not argv:
        sys.stderr.write(__doc__)
        return 3
    cmd, argv = argv[0], argv[1:]
    a = {"config": None, "tree": None, "out": None, "record": None,
         "busybox-drop": None}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x.startswith("--") and x[2:] in a:
            if i + 1 >= len(argv):
                die("%s needs a value" % x)
            a[x[2:]] = argv[i + 1]; i += 2
        else:
            die("unknown option %s" % x)

    if cmd in ("--self-test", "self-test"):
        return self_test(a["config"] or "config")

    if cmd not in ("emit", "check"):
        die("unknown command %r. Commands: emit, check, --self-test" % cmd)
    if not a["config"]:
        die("%s needs --config" % cmd)

    d = derive(a["config"], a["tree"], a["busybox-drop"])
    text = render(d)

    if cmd == "emit":
        if a["out"]:
            _write(a["out"], text)
            print("modrecord %s" % VERSION)
            print("declarations  %s" % a["config"])
            print("anchors       %s"
                  % ("resolved against %s" % a["tree"] if d["resolved"]
                     else "NOT resolved (no --tree)"))
            print("")
            print("RESULT: \033[32m%d vendor file(s) written to %s\033[0m"
                  % (len(d["files"]), a["out"]))
        else:
            sys.stdout.write(text)
        return 0

    if not a["record"]:
        die("check needs --record")
    have = _read(a["record"], "the committed record")
    print("modrecord %s" % VERSION)
    print("record        %s" % a["record"])
    print("declarations  %s  (%d vendor file(s))"
          % (a["config"], len(d["files"])))
    print("anchors       %s"
          % ("resolved against %s" % a["tree"] if d["resolved"]
             else "NOT resolved (no --tree)"))
    print("")
    if have != text:
        hl, tl = _lines(have), _lines(text)
        first = next((k for k in range(max(len(hl), len(tl)))
                      if hl[k:k + 1] != tl[k:k + 1]), 0)
        print("  \033[31mfirst difference at line %d\033[0m" % (first + 1))
        print("    committed  %r" % (hl[first] if first < len(hl) else None))
        print("    derived    %r" % (tl[first] if first < len(tl) else None))
        print("")
        print("RESULT: \033[31mthe record and the declarations disagree\033[0m")
        return 1
    print("RESULT: \033[32mthe record is what the declarations derive "
          "(%d vendor file(s))\033[0m" % len(d["files"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except KeyboardInterrupt:
        die("interrupted")
    except Exception as e:                          # noqa: BLE001
        # A traceback is not a refusal. Anything unexpected still leaves a
        # sentence naming what it was doing.
        die("%s: %s. This is a defect in modrecord, not a verdict about the "
            "declarations" % (type(e).__name__, e))
