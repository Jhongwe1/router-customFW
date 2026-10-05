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
anchor against a staged tree, in the order the build applies them -- the
host-compat series first (`tools/rlxfw-kbuild.sh`), then the marks rows in
their file order (`tools/rlxfw-marks.py apply`), the busybox series on its own
root (`tools/mkbusybox.sh`) -- and the delta's baseline file byte-for-byte
against its declared sha256.  A record emitted without `--tree` says so in its
own header, because a record that looks checked and is not is worse than one
that says it is a listing.

WHY THE PATCH SERIES IS APPLIED IN MEMORY.
量: `0005` and `0007` both change `arch/rlx/Kconfig`, and `0007`'s hunk is at
line 18 of the file `0005` already inserted a line into.  A checker that tested
every hunk against the PRISTINE tree would report `0007` as not applying, which
would be a fact about the checker.  So each hunk is resolved against the file as
the preceding hunks left it, which is what `patch` itself does.

WHY THE MARKS ARE APPLIED IN MEMORY TOO, IN ROW ORDER.  🔄 1.1, 2026-10-05.
量 on a fresh stage of the pin, 1.0's `check --tree` refused at `MK5`: anchor
not found.  Four rows -- `MK5`, `MK10`, `MK11`, `MK12` -- are anchored on a
line an earlier row inserts (`MK5`'s own reason says so, on purpose), and
`rlxfw-marks.py apply` applies rows in order, so 1.0 was resolving every row
against the pristine file and the declaration was never wrong.  Each row is
now resolved against the file as the patches and the earlier rows left it, with
the applier's own rules loaded from `tools/rlxfw-marks.py` rather than copied:
its `norm`, its exactly-once anchor, its indentation, and its refusal of a row
whose insert is already in the file (a tree that is not a fresh stage).

WHERE A HUNK LANDS WHEN ITS PRE-IMAGE OCCURS TWICE.  🔄 1.1, 2026-10-05.
量 the same stage: `0003`'s `@@ -25,9 +23,9 @@` on `Kbuild` matches in two
places (the `bounds` and the `offsets` rule carry the same nine lines), and 1.0
refused to pick one.  GNU `patch` does not refuse: `locate_hunk` searches
outward from the header's old-start line plus the running offset, `+k` before
`-k`, and `apply_hunk` writes it.  `_locate` and `_place` are those two
functions of GNU patch 2.7.6 at fuzz 0, transcribed from its source (讀), with
every hunk placed rather than found reported.  They are stricter than `patch` in
one place: a hunk `patch` would apply only with fuzz 1-2 is refused here.  量
2026-10-05, a stage of the pin: GNU `patch -p1 --forward` (10 of 10, and the
busybox patch) and `rlxfw-marks.py apply` (28 marks) leave all 23 vendor files
they write byte-identical to what this resolution computes, and `patch`'s own
report places `0003`'s second hunk where `_place` does.

`check --tree` COMPARES CONTENT, NOT A PATH.  The committed record is the
listing, because CI's `check` compares it without a tree; 1.0's `check --tree`
compared it with a rendering that carries the tree's own path and anchor states,
so it could never be green.  1.1 resolves against the tree first (any failure
is a refusal) and then compares the committed record with what `check` derives
without one.

Usage
    tools/modrecord.py emit   --config DIR [--tree DIR] [--out FILE]
    tools/modrecord.py check  --config DIR --record FILE [--tree DIR]
    tools/modrecord.py --self-test [--config DIR]

`emit` with no `--out` writes to stdout.  With `--out` it builds the whole
record in memory, writes `FILE.tmp` and `os.replace`s it, so a refusal leaves
neither a truncated record nor a stray temporary.
"""

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import hashlib

VERSION = "1.1"

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


def _read_tree(path):
    """A vendor file, read as the two appliers read it.

    `_read` refuses bytes that are not UTF-8, which is right for a declaration
    and wrong for somebody else's source: GNU `patch` reads bytes and
    `tools/rlxfw-marks.py` reads with `surrogateescape`, so such a file builds.
    量 2026-10-05: all 24 vendor files the declarations touch at the pin are
    UTF-8, so this changes no reading today."""
    try:
        with io.open(path, "r", encoding="utf-8", errors="surrogateescape",
                     newline="") as f:
            return f.read()
    except IOError as e:
        die("cannot read a tree file (%s): %s" % (path, e.strerror))


def _lines(text):
    """Split on "\\n" alone, keeping it, so a hunk compares byte-for-byte.

    🔄 1.1: not `str.splitlines`, which also splits on \\x0b, \\x0c,
    \\x1c-\\x1e, \\x85, \\u2028 and \\u2029.  Both appliers this models count
    lines by "\\n" alone -- GNU `patch`, and `rlxfw-marks.py`'s `split("\\n")`
    -- and `_place` positions a hunk by its header's line number, so a form
    feed in a vendor file would shift every line below it.  量 2026-10-05:
    none of the 11 patch files and none of the 24 vendor files they and the
    marks touch at the pin holds any of those characters or a lone CR, so the
    record did not move."""
    parts = text.split("\n")
    out = [p + "\n" for p in parts[:-1]]
    if parts[-1]:
        out.append(parts[-1])
    return out


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
                pre, post, body = [], [], []
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
                        ctx = b[1:] if b.startswith(" ") else b
                        pre.append(ctx); post.append(ctx)
                        body.append((" ", ctx))
                        got_pre += 1; got_post += 1
                    elif b.startswith("-"):
                        pre.append(b[1:]); got_pre += 1
                        body.append(("-", b[1:]))
                    elif b.startswith("+"):
                        post.append(b[1:]); got_post += 1
                        body.append(("+", b[1:]))
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
                # the context before the first change and after the last,
                # which GNU `patch` calls prefix and suffix context
                kinds = [k for k, _ in body]
                lead = next((n for n, k in enumerate(kinds) if k != " "),
                            len(kinds))
                trail = next((n for n, k in enumerate(reversed(kinds))
                              if k != " "), len(kinds))
                hunks.append({"header": header, "pre": pre, "post": post,
                              "body": body, "lead": lead, "trail": trail,
                              "old_start": int(m.group(1)),
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


def _locate(cands, n, pat, first, guess, frozen, lead, trail):
    """GNU `patch` 2.7.6's `locate_hunk` at fuzz 0, transcribed from its
    `src/patch.c` (讀 2026-10-05, patch-2.7.6.tar.xz sha256 `ac610bda97abe0d9`).

    Positions are 1-based.  `cands` holds every position where the pre-image
    matches exactly -- at fuzz 0 every `patch_match` call is an exact match --
    `first` is the header's old-start (`pch_first`), `guess` that plus the
    running offset (`first_guess`), `frozen` is `last_frozen_line`, `lead` and
    `trail` the hunk's prefix and suffix context.  -> a position, or 0 where
    `patch` would go on to try fuzz.  The two branches before the loop are
    `patch`'s rule for a hunk whose context is cut short by the start or the
    end of the file."""
    context = max(lead, trail)
    pre_f, suf_f = lead - context, trail - context
    max_where = n - (pat - suf_f) + 1
    min_where = frozen + 1
    max_pos = max_where - guess
    max_neg = guess - min_where
    max_off = max(max_pos, max_neg)
    if guess <= max_neg:                    # "Do not try lines <= 0."
        max_neg = guess - 1
    if pre_f < 0 and first <= 1:            # "Can only match start of file."
        if suf_f < 0 and (pat != n or lead < frozen):
            return 0
        off = 1 - guess
        return 1 if frozen <= lead and off <= max_pos and 1 in cands else 0
    if suf_f < 0:                           # "Can only match end of file."
        off = guess - (n - pat + 1)
        return guess - off if off <= max_neg and guess - off in cands else 0
    min_off = (guess - max_where if max_pos < 0
               else guess - min_where if max_neg < 0 else 0)
    for off in range(min_off, max_off + 1):
        if off <= max_pos and guess + off in cands:
            return guess + off
        if off <= max_neg and guess - off in cands:
            return guess - off
    return 0


def _place(lines, hunks, path, target):
    """One file section of one patch, applied as GNU `patch` applies it at
    fuzz 0 -> (the file after it, [(index, candidates)] per hunk).

    🔄 1.1, replacing 1.0's "a pre-image found twice is a refusal".  Each hunk
    is looked for by `_locate` (`locate_hunk`), in the section's INPUT
    coordinates -- the file as the earlier patch files left it -- from its
    header's old-start plus the running offset, `+k` before `-k`, so a tie goes
    forward; the offset becomes where it landed minus its header's line, as
    `in_offset` does, and resets with every section.  It is then written out
    the way `apply_hunk` writes it: input lines are copied up to each change,
    and only up to the LAST change, so the next hunk may start inside this
    one's trailing context; a hunk whose first change falls before what is
    already written is refused, as `copy_till` refuses it ("misordered hunks!
    output would be garbled").  量 2026-10-05, GNU patch 2.7.6 on eight probe
    files: a placement behind the previous hunk fails, an overlap of its
    trailing context applies, and a copy behind it that is nearer than one
    ahead is not taken.  The obvious rule -- never before the end of the
    previous pre-image -- gets the first two wrong.

    Where `patch` would fall back to fuzz 1-2, this refuses: the one place it
    is stricter than the build.  A body cut short at the end of a patch file
    counts its missing lines as trailing context, which is what `patch`'s
    "assume blank lines got chopped" makes them, but they are not matched; and
    a `\\ No newline` marker is skipped, not applied (the declarations hold
    none).  The candidate count is returned so a caller can report the hunks
    that were PLACED rather than found."""
    out, placed = [], []
    frozen = 0                       # `last_frozen_line`: input lines written
    offset = 0                       # `in_offset`
    n = len(lines)
    for h in hunks:
        pad = h["short"][0] if h["short"][0] == h["short"][1] else 0
        pat = len(h["pre"]) + pad
        cands = set(i + 1 for i in _find_all(lines, h["pre"]) if i + pat <= n)
        if not cands:
            die("%s: %s does not apply to %s: its pre-image is not in the "
                "file. Not a skip -- a hunk that moved is the thing this "
                "record exists to catch" % (path, h["header"], target))
        where = _locate(cands, n, pat, h["old_start"],
                        h["old_start"] + offset, frozen, h["lead"],
                        h["trail"] + pad)
        if not where:
            die("%s: %s does not apply to %s at fuzz 0: its pre-image is at "
                "line(s) %s, and GNU patch looks for it elsewhere (its context "
                "is cut short, so patch holds it to the start or the end of "
                "the file). Patch would try fuzz next; this tool never does"
                % (path, h["header"], target,
                   ", ".join(str(c) for c in sorted(cands))))
        offset = where - h["old_start"]
        old = [x for x in h["body"] if x[0] != "+"]
        new = [x for x in h["body"] if x[0] != "-"]
        i = j = 0
        k = where - 1                # the input index of old[i]

        def copy_till(upto):
            if frozen > upto:
                die("%s: %s on %s would land at line %d, inside what the "
                    "hunk before it already changed (through line %d). GNU "
                    "patch refuses it: \"misordered hunks! output would be "
                    "garbled\"" % (path, h["header"], target, where, frozen))
            out.extend(lines[frozen:upto])
            return upto

        while i < len(old):
            if old[i][0] == "-":
                frozen = copy_till(k) + 1
                i += 1
                k += 1
            elif j >= len(new):
                break
            elif new[j][0] == "+":
                frozen = copy_till(k)
                out.append(new[j][1])
                j += 1
            else:
                i += 1
                j += 1
                k += 1
        if j < len(new) and new[j][0] == "+":
            frozen = copy_till(k)
            while j < len(new) and new[j][0] == "+":
                out.append(new[j][1])
                j += 1
        placed.append((where - 1, len(cands)))
    out.extend(lines[frozen:])
    return out, placed


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
    """Whitespace-collapsed, for comparing the two declarations' drop names.
    🔄 1.1: it matched the marks anchors too until then; those are resolved
    with `tools/rlxfw-marks.py`'s own `norm` now (`_marks_rules`)."""
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
    # 🔄 1.1: in the build's own order, on ONE in-memory text per vendor file:
    # the host-compat series (`rlxfw-kbuild.sh` applies it first), then the
    # marks rows (`rlxfw-marks.py apply`, after it), then the busybox series on
    # its own root (`mkbusybox.sh`).  The delta's baseline is read from disk:
    # nothing above writes it, and the build copies it rather than editing it.
    resolved = tree is not None
    chained, positioned, after = [], [], {}
    if resolved:
        if not os.path.isdir(tree):
            die("--tree %s is not a directory" % tree)
        _resolve_patches([x for x in parsed if x[2] == HOST_COMPAT_ROOT],
                         tree, files, after, positioned)
        _resolve_marks(mrows, tree, files, after, chained)
        _resolve_patches([x for x in parsed if x[2] != HOST_COMPAT_ROOT],
                         tree, files, after, positioned)
        _resolve_delta(delta, tree, files)
    else:
        for e in files.values():
            e["state"] = ["declared"] * len(e["anchors"])

    return {"drop": drop, "delta": delta, "marks": mrows,
            "host_compat": hc, "busybox": bb, "shortfalls": shortfalls,
            "files": files, "resolved": resolved, "tree": tree,
            "busybox_drop": busybox_drop,
            "hunks": sum(len(x[5]) for x in parsed),
            "chained": chained, "positioned": positioned, "after": after}


_MARKS_RULES = []


def _marks_rules():
    """(norm, indent) out of `tools/rlxfw-marks.py` itself, loaded by path.

    The anchor rule `--tree` resolves with is the applier's, not a copy of it:
    a copy is a second owner, and `tools/srcarchive.py` loads this file the
    same way for the same reason.  Loaded only for `--tree`, so the listing --
    what CI's `check` and `srcarchive` derive -- does not depend on it."""
    if not _MARKS_RULES:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "rlxfw-marks.py")
        if not os.path.isfile(path):
            die("--tree resolves the marks with tools/rlxfw-marks.py's own "
                "rules, and %s is not there" % path)
        import importlib.util
        spec = importlib.util.spec_from_file_location("modrecord_marks", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MARKS_RULES.append((mod.norm, mod._indent))
    return _MARKS_RULES[0]


def _resolve_marks(mrows, tree, files, state, chained):
    """In the declaration's row order, against the file as the patches and the
    earlier rows left it, by `rlxfw-marks.py apply`'s own rules.

    🔄 1.1.  1.0 read every row against the pristine file, and 量 on a fresh
    stage of the pin that refused at `MK5`: `MK5`, `MK10`, `MK11` and `MK12`
    are anchored on a line an earlier row inserts, which `MK5`'s reason says
    on purpose.  The text is kept as `apply` keeps it -- `split("\\n")`, the
    insert written as the anchor line's indentation plus the row's text,
    `"\\n".join` -- so the in-memory file is the one `apply` writes.  Which row
    each chained anchor came from is returned in `chained`."""
    norm, indent = _marks_rules()
    origin = {}
    for r in mrows:
        key = r["file"]
        if key not in state:
            p = os.path.join(tree, *key.split("/"))
            if not os.path.isfile(p):
                die("row %s names %s and the tree has no such file"
                    % (r["id"], key))
            state[key] = _read_tree(p)
        ls = state[key].split("\n")
        org = origin.setdefault(key, [None] * len(ls))
        if len(org) != len(ls):
            die("row %s: %s changed between two marks rows, which nothing in "
                "this tool does. This is a defect in modrecord, not a verdict "
                "about the declarations" % (r["id"], key))
        # `apply`'s A4: an insert already in the file means the tree is not
        # clean, and applying again would emit the mark twice.
        if any(norm(x) == norm(r["insert"]) for x in ls):
            die("row %s: its insert %r is already in %s, so this tree is not a "
                "fresh stage. `tools/rlxfw-marks.py apply` refuses the same "
                "tree; re-stage it" % (r["id"], r["insert"], key))
        want = norm(r["anchor"])
        hits = [i for i, x in enumerate(ls) if norm(x) == want]
        if not hits:
            die("row %s: anchor not found in %s: %r. Not skipped -- an anchor "
                "that moved is the finding, not a nuisance"
                % (r["id"], key, r["anchor"]))
        if len(hits) > 1:
            die("row %s: anchor occurs %d times in %s: %r. Refusing to pick "
                "one" % (r["id"], len(hits), key, r["anchor"]))
        i = hits[0]
        if org[i] is not None:
            chained.append((r["id"], org[i]))
        at = i if r["position"] == "before" else i + 1
        ls.insert(at, indent(ls[i]) + r["insert"])
        org.insert(at, r["id"])
        state[key] = "\n".join(ls)
        files[key]["state"].append("1 of 1")


def _resolve_patches(parsed, tree, files, state, positioned):
    """Applied IN DECLARED ORDER, in memory, so a later patch is resolved
    against the file an earlier one left behind; each file section placed
    by `_place`, as GNU `patch` places it.  Every hunk that had more than one
    candidate is appended to `positioned` as (patch, file, header, line,
    candidates)."""
    for p, f, root, target, full, hunks in parsed:
        if full not in state:
            disk = os.path.join(tree, *full.split("/"))
            if not os.path.isfile(disk):
                die("%s changes %s and the tree has no such file" % (f, full))
            state[full] = _read_tree(disk)
        out, placed = _place(_lines(state[full]), hunks, p, full)
        state[full] = "".join(out)
        for h, (where, n) in zip(hunks, placed):
            if n > 1:
                positioned.append((f, full, h["header"], where + 1, n))
                files[full]["state"].append("applies at its line")
            else:
                files[full]["state"].append("applies")


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
        ch = d.get("chained") or []
        po = d.get("positioned") or []
        w("| anchors | 量 resolved against the tree at `%s`, in the build's "
          "order: every patch hunk applied in declared order%s; every marks "
          "anchor found exactly once in row order, after the patches%s; the "
          "delta's baseline matched by sha256 |\n"
          % (_cell(d["tree"]),
             (", %d of them placed at the header's line because the pre-image "
              "occurs in more than one place, as GNU `patch` places it (%s)"
              % (len(po), ", ".join("`%s` %s on `%s` at line %d of %d "
                                    "candidates" % (f, _cell(h), _cell(t),
                                                    ln, n)
                                    for f, t, h, ln, n in po))) if po else "",
             (", %d of them on a line an earlier row inserts (%s)"
              % (len(ch), ", ".join("`%s` on `%s`" % c for c in ch)))
             if ch else ""))
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


def _mkpatch(target, pre, post, prose="prose line\n", inflate=0,
             tail=("{\n",)):
    # 🔄 1.1: one line of TRAILING context, `tail`, as `diff -u` writes it.
    # 量 2026-10-05: the 1.0 hunks had one line of leading context and none
    # trailing, and GNU patch 2.7.6 applies such a hunk only at fuzz 1 -- its
    # rule for context cut short by the end of a file -- so a fuzz-0 model
    # refuses them.  M1-M13 assert what they did; their patches now apply.
    body = "".join(" " + x for x in pre[:1])
    body += "".join("-" + x for x in pre[1:])
    body += "".join("+" + x for x in post[1:])
    body += "".join(" " + x for x in tail)
    n_pre = len(pre) + len(tail) + inflate
    n_post = len(post) + len(tail) + inflate
    return ("%s--- a/%s\n+++ b/%s\n@@ -1,%d +1,%d @@\n%s"
            % (prose, target, target, n_pre, n_post, body))


# Two copies of one three-line block, at lines 2 and 8, for the hunk whose
# pre-image occurs twice (`0003` on `Kbuild` is the real one).
_TWICE = ("int a;\n"
          "{\n"
          "\tone();\n"
          "}\n"
          "int b;\n"
          "int c;\n"
          "int d;\n"
          "{\n"
          "\tone();\n"
          "}\n"
          "int e;\n")

# For the running offset: the first hunk's header says line 4 and its one
# match is line 1, so `patch` looks for the second (header line 10) at line 7,
# and the copy at line 6 is the nearer one.  Without the offset it is line 10.
_DRIFT = "A1\nA2\nx1\nx2\nx3\n{\n\tone();\n}\ny\n{\n\tone();\n}\nz\n"
_DRIFT_PATCH = ("prose line\n--- a/sub/drift.c\n+++ b/sub/drift.c\n"
                "@@ -4,2 +4,2 @@\n-A1\n+B1\n A2\n"
                "@@ -10,3 +10,3 @@\n {\n-\tone();\n+\tTWO();\n }\n")

# Misordered: the second hunk's header points at the copy at line 1, BEFORE the
# first hunk (lines 6-8).  `patch` finds that copy first and refuses the hunk
# ("misordered hunks!"), though another copy sits at line 10.
_BACK = "{\n\tone();\n}\np\nq\nM1\nM2\nM3\nr\n{\n\tone();\n}\ns\n"
_BACK_PATCH = ("prose line\n--- a/sub/back.c\n+++ b/sub/back.c\n"
               "@@ -6,3 +6,3 @@\n M1\n-M2\n+N2\n M3\n"
               "@@ -1,3 +1,3 @@\n {\n-\tone();\n+\tTWO();\n }\n")

# (file, text, hunks) for `_fixture(extra=...)`: the shapes `patch` places by
# a rule of its own.  量 2026-10-05: GNU patch 2.7.6 run on every placement
# fixture of this self-test agrees with each expected outcome, 10 of 10.
_EXTRA = {
    # the second hunk starts on the first one's trailing context line `c`
    "overlap": ("overlap.c", "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nc\nd\ne\nk\n",
                "@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n"
                "@@ -5,3 +5,3 @@\n c\n-d\n+D\n e\n"),
    # trailing context shorter than leading: held to the end of the file
    "eof-no": ("eof.c", "a\nb\np\nq\nr\ns\nt\nu\n",
               "@@ -3,4 +3,4 @@\n p\n q\n-r\n+R\n s\n"),
    "eof-yes": ("eof.c", "a\nb\nc\nd\np\nq\nr\ns\n",
                "@@ -5,4 +5,4 @@\n p\n q\n-r\n+R\n s\n"),
    # leading context shorter than trailing, at line 1: held to the start
    "sof-no": ("sof.c", "q\nx\ny\nz\nw\n",
               "@@ -1,3 +1,3 @@\n-x\n+X\n y\n z\n"),
    "sof-yes": ("sof.c", "x\ny\nz\nw\n",
                "@@ -1,3 +1,3 @@\n-x\n+X\n y\n z\n"),
}


def _fixture(tmp, extra_mark=None, extra_patch=None, bad_anchor=False,
             twice=False, bad_hunk=False, bad_fields=False, no_header=False,
             bad_sha=False, short_hunk=0, chain=None, twice_hunk=None,
             del_file=None, already=False, drift=False, backwards=False,
             extra=None):
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

    put("linux-2.6.30/sub/a.c", _C + ("\tone();\n" if twice else "")
        + ('\trlxfw_mark("B0");\n' if already else ""))
    put("linux-2.6.30/drivers/Makefile", _MKFILE)
    put("linux-2.6.30/sub/h.c", _C)
    put("users/busybox-1.13/net/b.c", _C)
    put("linux-2.6.30/extra.c", _C)
    if twice_hunk is not None:
        put("linux-2.6.30/sub/twice.c", _TWICE)
    if drift:
        put("linux-2.6.30/sub/drift.c", _DRIFT)
    if backwards:
        put("linux-2.6.30/sub/back.c", _BACK)
    if extra:
        put("linux-2.6.30/sub/" + _EXTRA[extra][0], _EXTRA[extra][1])
    cfgfile = put("boards/base.config", _CFG)
    with io.open(cfgfile, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    if bad_sha:
        sha = "0" * 64

    # The anchors carry NO tab: this file is tab-separated, so an anchor
    # cannot hold one, and `rlxfw-marks.py`'s `norm` is what makes it match
    # the tree's indentation. The first fixture written here did carry one and
    # the parser refused it, which is the refusal working.
    rows = [_row("B0", "linux-2.6.30/sub/a.c", "after",
                 "nosuch();" if bad_anchor else "one();",
                 'rlxfw_mark("B0");', "", "the reason"),
            _row("MK", "linux-2.6.30/drivers/Makefile", "after",
                 "obj-y += b.o", "obj-y += mine.o", "str:mine", "the reason")]
    if chain:
        # B1 is anchored on B0's OWN inserted line, the shape of `MK5`.
        b1 = _row("B1", "linux-2.6.30/sub/a.c", "after", 'rlxfw_mark("B0");',
                  'rlxfw_mark("B1");', "", "anchored on B0's insert")
        rows.insert(1 if chain == "in-order" else 0, b1)
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
    if twice_hunk is not None:
        # one hunk, pre-image `{` / `one();` / `}`, header at `twice_hunk`
        with io.open(os.path.join(cfg, "host-compat", "0003-twice.patch"), "w",
                     encoding="utf-8", newline="") as f:
            f.write("prose line\n--- a/sub/twice.c\n+++ b/sub/twice.c\n"
                    "@@ -%d,3 +%d,3 @@\n {\n-\tone();\n+\tTWO();\n }\n"
                    % (twice_hunk, twice_hunk))
    if drift:
        with io.open(os.path.join(cfg, "host-compat", "0004-drift.patch"), "w",
                     encoding="utf-8", newline="") as f:
            f.write(_DRIFT_PATCH)
    if backwards:
        with io.open(os.path.join(cfg, "host-compat", "0005-back.patch"), "w",
                     encoding="utf-8", newline="") as f:
            f.write(_BACK_PATCH)
    if extra:
        fn, _, hunks = _EXTRA[extra]
        with io.open(os.path.join(cfg, "host-compat", "0006-extra.patch"), "w",
                     encoding="utf-8", newline="") as f:
            f.write("prose line\n--- a/sub/%s\n+++ b/sub/%s\n%s"
                    % (fn, fn, hunks))
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
    if del_file:
        os.remove(os.path.join(tree, *del_file.split("/")))
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

        # ---- 1.1: the build's order, `patch`'s placement, a fresh stage ----
        # M14 -- a row anchored on an EARLIER row's insert resolves, because
        # the rows are applied in order (`MK5` on `MK4`'s line is the real one).
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, chain="in-order")
        d, why = permits(derive, cfg, tree)
        got = (d["chained"], d["files"]["linux-2.6.30/sub/a.c"]["state"]) \
            if d else None
        ck("M14 a row anchored on an earlier row's insert resolves",
           got == ([("B1", "B0")], ["1 of 1", "1 of 1"]),
           why or "chained / states: %r" % (got,))

        # M15 -- the same two rows the other way round refuse: ORDER is what is
        # modelled, not a set of lines that exist somewhere.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, chain="swapped")
        ok, why, err = refuses(derive, cfg, tree)
        ck("M15 the same two rows in the other order refuse",
           ok and "row B1: anchor not found" in err,
           "%s / %s" % (why, err.strip()[:90]))

        # M16..M18 -- a pre-image found twice is PLACED, as GNU `patch` places
        # it: nearest the header's line, `+k` before `-k`.  Copies at lines 2
        # and 8; a header at 5 is equidistant and goes forward.
        for nm, start, want_at in (("M16", 2, 1), ("M17", 8, 7),
                                   ("M18", 5, 7)):
            shutil.rmtree(tmp); os.makedirs(tmp)
            cfg, tree = _fixture(tmp, twice_hunk=start)
            d, why = permits(derive, cfg, tree)
            body = (d["after"]["linux-2.6.30/sub/twice.c"].split("\n")
                    if d else [])
            changed = [i - 1 for i, x in enumerate(body) if x == "\tTWO();"]
            po = d["positioned"] if d else []
            ck("%s a pre-image found twice, header at line %d: %s"
               % (nm, start, {1: "copy 1", 7: "copy 2"}[want_at]
                  + (" (a tie goes forward)" if start == 5 else "")),
               changed == [want_at] and len(po) == 1
               and po[0][3] == want_at + 1 and po[0][4] == 2,
               why or "changed block(s) at %r, positioned %r" % (changed, po))

        # M24 -- the running offset: a later hunk of the same section is looked
        # for at its header's line PLUS where the earlier hunks landed against
        # theirs, as `patch`'s `in_offset` does.  量 2026-10-05: GNU `patch`
        # changes the copy at line 6 on this fixture, as this expects.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, drift=True)
        d, why = permits(derive, cfg, tree)
        body = d["after"]["linux-2.6.30/sub/drift.c"].split("\n") if d else []
        ck("M24 a later hunk is looked for at its line plus the running offset",
           body[:1] == ["B1"] and [i for i, x in enumerate(body)
                                   if x == "\tTWO();"] == [6],
           why or "lines %r" % (body,))

        # M25 -- misordered: the nearest copy lies inside what the hunk before
        # changed, and `patch` refuses the hunk rather than look further.
        # 量 2026-10-05: GNU `patch` prints "misordered hunks!" and fails it.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, backwards=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M25 a hunk landing behind the previous one refuses (misordered)",
           ok and "misordered hunks" in err and "0005-back.patch" in err,
           "%s / %s" % (why, err.strip()[:110]))

        # M26..M30 -- the shapes `patch` places by a rule of its own (`_EXTRA`
        # says how each expected outcome was checked against GNU patch).
        def extra_case(name, which, want):
            shutil.rmtree(tmp); os.makedirs(tmp)
            cfg, tree = _fixture(tmp, extra=which)
            fn = "linux-2.6.30/sub/" + _EXTRA[which][0]
            if want is None:
                ok, why, err = refuses(derive, cfg, tree)
                ck(name, ok and "at fuzz 0" in err,
                   "%s / %s" % (why, err.strip()[:110]))
            else:
                d, why = permits(derive, cfg, tree)
                got = d["after"][fn] if d else None
                ck(name, got == want, why or "text %r" % (got,))

        extra_case("M26 a hunk may start inside the previous one's trailing "
                   "context", "overlap",
                   "a\nB\nc\nD\ne\nf\ng\nh\ni\nj\nc\nd\ne\nk\n")
        extra_case("M27 trailing context cut short, copy not at the end: "
                   "refused (patch needs fuzz)", "eof-no", None)
        extra_case("M28 trailing context cut short, copy at the end: placed",
                   "eof-yes", "a\nb\nc\nd\np\nq\nR\ns\n")
        extra_case("M29 leading context cut short, copy not at line 1: "
                   "refused (patch needs fuzz)", "sof-no", None)
        extra_case("M30 leading context cut short, copy at line 1: placed",
                   "sof-yes", "X\ny\nz\nw\n")

        # M19, M20 -- a vendor file the declarations name is gone: refused,
        # for a marks row and for a patch alike.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, del_file="linux-2.6.30/sub/a.c")
        ok, why, err = refuses(derive, cfg, tree)
        ck("M19 a marks row whose vendor file was deleted refuses",
           ok and "row B0 names linux-2.6.30/sub/a.c and the tree has no "
                  "such file" in err, "%s / %s" % (why, err.strip()[:90]))
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, del_file="linux-2.6.30/sub/h.c")
        ok, why, err = refuses(derive, cfg, tree)
        ck("M20 a patch whose vendor file was deleted refuses",
           ok and "0001-a.patch changes linux-2.6.30/sub/h.c and the tree has "
                  "no such file" in err, "%s / %s" % (why, err.strip()[:90]))

        # M21 -- `rlxfw-marks.py apply`'s A4: an insert already in the file is
        # a tree that is not a fresh stage, and resolving it would be reading
        # the build's own output.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, already=True)
        ok, why, err = refuses(derive, cfg, tree)
        ck("M21 an insert already present refuses: not a fresh stage",
           ok and "row B0" in err and "not a fresh stage" in err,
           "%s / %s" % (why, err.strip()[:90]))

        # M22 -- `check --tree` compares CONTENT: the committed (listing)
        # record against the listing, with the tree resolved first.  1.0
        # compared the tree's own rendering and could never be green.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, chain="in-order", twice_hunk=8)
        rec = os.path.join(tmp, "rec.md")
        with contextlib.redirect_stdout(io.StringIO()):
            permits(main, ["emit", "--config", cfg, "--out", rec])
            rc, why = permits(main, ["check", "--config", cfg, "--record",
                                     rec, "--tree", tree])
        ck("M22 check --tree against the listing record is rc 0",
           rc == 0, why or "rc %r" % (rc,))

        # M23 -- and it is still a refusal, exit 3, when an anchor is planted
        # twice: the comparison never runs on a tree that does not resolve.
        shutil.rmtree(tmp); os.makedirs(tmp)
        cfg, tree = _fixture(tmp, twice=True)
        rec = os.path.join(tmp, "rec.md")
        with contextlib.redirect_stdout(io.StringIO()):
            permits(main, ["emit", "--config", cfg, "--out", rec])
            ok, why, err = refuses(main, ["check", "--config", cfg, "--record",
                                          rec, "--tree", tree])
        ck("M23 check --tree with an anchor planted twice exits 3",
           ok and why == "exit 3" and "occurs 2 times" in err,
           "%s / %s" % (why, err.strip()[:90]))
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
    # 🔄 1.1: with --tree the comparison is still against the LISTING.  The
    # committed record is the form `check` without a tree derives (CI compares
    # it so), and the resolution above has already refused or passed; 1.0
    # compared the committed file with the tree's own rendering -- its path and
    # its anchor states -- so `check --tree` could never be green.
    if d["resolved"]:
        text = render(derive(a["config"], None, a["busybox-drop"]))
    print("modrecord %s" % VERSION)
    print("record        %s" % a["record"])
    print("declarations  %s  (%d vendor file(s))"
          % (a["config"], len(d["files"])))
    if d["resolved"]:
        print("anchors       resolved against %s, in the build's order"
              % a["tree"])
        print("  hunks       %d applied in declared order; %d placed at the "
              "header's line because the pre-image occurs in more than one "
              "place, as GNU patch places it"
              % (d["hunks"], len(d["positioned"])))
        for f, t, h, ln, n in d["positioned"]:
            print("              %s %s on %s: line %d, nearest of %d"
                  % (f, h, t, ln, n))
        print("  marks       %d row(s), each anchor exactly once in row order "
              "after the patches; %d on a line an earlier row inserts%s"
              % (len(d["marks"]), len(d["chained"]),
                 (" (%s)" % ", ".join("%s on %s" % c for c in d["chained"]))
                 if d["chained"] else ""))
        print("  delta       %s matched its declared sha256 %s"
              % (d["delta"]["baseline-file"],
                 d["delta"]["baseline-sha256"].strip()[:16]))
        print("compared      on content: the committed record against the "
              "listing `check` derives without a tree; the tree's path and "
              "its anchor states are not part of the committed record")
    else:
        print("anchors       NOT resolved (no --tree)")
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
          "(%d vendor file(s))%s\033[0m"
          % (len(d["files"]),
             ", and every anchor resolves against the tree" if d["resolved"]
             else ""))
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
