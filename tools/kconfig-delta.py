#!/usr/bin/env python3
"""Is the kernel .config this build USED the one rlxfw declared?

R3-4's gate.  It answers one question and refuses to answer any other: given
the vendor's board template, a declared list of differences, and the `.config`
a build actually used, is every difference between the first and the third on
the second list?

WHY IT READS THE BUILT FILE AND NOT THE ONE THAT WAS COPIED IN.
`config/setconfig:344-356` copies `boards/<board>/config.linux-<ver>.<model>`
into `$LINUXDIR/.config` and then runs `make -C $LINUXDIR oldconfig`.  The file
that was copied in and the file the compiler saw are not the same file: 量
2026-08-28, they differ on **21 symbols** for this board.  A check that read the
copied-in file would pass on a build it had never looked at.  `C6` is that
mistake, made on purpose, and it must fail.

WHY THE BAN ON `yes '' | make oldconfig` IS NOT IMPLEMENTED HERE, AND WHY THAT
IS NOT AN OVERSIGHT.  A check that grepped the build script for that string
would be a check that cannot fail on the real failure.  量 2026-08-28, on this
tree:

  * `oldconfig` is `conf -o`, which is `input_mode = ask_silent` and leaves
    `sync_kconfig` at 0.  `valid_stdin` is initialised to 1 and reassigned ONLY
    inside `if (sync_kconfig)` (`scripts/kconfig/conf.c:563`), so `check_stdin()`
    never fires for `oldconfig` however stdin is connected.  It aborts for
    `silentoldconfig` and not for this.
  * `conf_askvalue()` presets `line` to "\n" and then ignores the return value
    of `fgets` -- the host compiler says so out loud while building the tool:
    `conf.c:105: warning: ignoring return value of 'fgets'`.  So **EOF and an
    empty line are the same input**.
  * Measured, not derived: `< /dev/null` and `yes '' |` produced .config files
    with **0** differing symbol lines.  `yes n |` moved 6.  The banned string is
    not the variable.

  * And on THIS template `oldconfig` is asked **nothing at all**: `(NEW)` appears
    0 times in all four runs.  Not one of the 21 differences is an answered
    prompt.  They are derived, and `--delta` says by what.

So the gate is on the outcome, which is what a wrong answer actually shows up
in.  How oldconfig was invoked is recorded in the delta file's header for the
reader; it is not what is checked, because checking it would prove nothing.

Usage
    tools/kconfig-delta.py apply   --baseline F --delta F --out F
    tools/kconfig-delta.py check   --baseline F --delta F --built F
    tools/kconfig-delta.py explain --baseline F --built F [--delta F]
    tools/kconfig-delta.py self-test

`apply` writes the .config to feed the tree; `check` reads the .config the
build actually used.  Both read the same delta file, on purpose: if the
generator and the auditor read different files they can drift apart and both
keep passing.
"""

import hashlib
import os
import re
import sys
import tempfile

VERSION = "1.0"

RE_SET = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
# NOT anchored at the end, and that is not sloppiness -- it is agreement with
# the reader that decides what the compiler saw.  `scripts/kconfig/confdata.c`
# in this drop does `if (strncmp(p, "is not set", 10)) continue;`, which accepts
# anything after those ten characters.  An anchored regex here drops a line
# kconfig honoured, the symbol reads ABSENT instead of `n`, and a real drift
# walks through the gate: `# CONFIG_KGDB is not set   (rlxfw)` was measured
# doing exactly that on 2026-08-28.  C17 is the control.
RE_NOT = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set")

ABSENT = "-"

# A mechanism is a closed vocabulary on purpose.  "because kconfig does that" is
# not a reason, and a free-text field would accept it.
MECHANISMS = {
    "promptless":  "declared with no prompt string, so its value is its default "
                   "and no .config line can change it",
    "selected":    "some other symbol `select`s it, so kconfig forces it and "
                   "sym_is_changable() is false",
    "dep-unmet":   "its prompt's `depends on` is not satisfied by this model, so "
                   "the symbol is not offered and is dropped",
    "undeclared":  "no `config` block declares it anywhere in the tree the board "
                   "sources, so kconfig has never heard of it",
    "other-board": "declared only under a board directory this board does not "
                   "source",
}


class Refused(Exception):
    """A refusal, raised instead of exiting while the controls are running.

    The controls have to be able to drive `die()` -- five of them exist to prove
    it fires -- and the first version did that by re-invoking this script as a
    subprocess.  That is a fork bomb: `check` runs the controls, each control
    starts a `check`, and each of those runs the controls.  It took the WSL
    service down before it was noticed.  In-process, with `C16` shelling out
    exactly once on a path that refuses BEFORE the controls run, tests the same
    thing and terminates.
    """


_RAISE = False


def die(msg):
    if _RAISE:
        raise Refused(msg)
    sys.stderr.write("kconfig-delta: %s\n" % msg)
    sys.exit(3)


# --------------------------------------------------------------------------
# .config
# --------------------------------------------------------------------------

def parse_config(path, text=None):
    """{symbol: value}.  `# X is not set` is the value 'n'; a symbol that is not
    mentioned at all is ABSENT, and those are NOT the same thing -- 18 of this
    board's 21 derived differences are exactly that distinction."""
    if text is None:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    d = {}
    for lineno, ln in enumerate(text.split("\n"), 1):
        ln = ln.rstrip("\r")
        m = RE_SET.match(ln)
        if not m:
            m = RE_NOT.match(ln)
            if not m:
                continue
            name, val = m.group(1), "n"
        else:
            name, val = m.group(1), m.group(2)
        if name in d and d[name] != val:
            # Last-wins would be a silent wrong answer about which value the
            # compiler saw.  kconfig itself never writes a duplicate.
            die("%s: %s appears twice with different values (%r at some earlier "
                "line, %r at line %d). Refusing to guess which one the build "
                "used" % (path, name, d[name], val, lineno))
        d[name] = val
    if not d:
        die("%s: not one CONFIG_ line. A gate that read an empty file would "
            "report 0 differences" % path)
    return d


def diff_configs(a, b):
    """[(symbol, from, to)] over the union, ABSENT for 'not mentioned'."""
    out = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k, ABSENT), b.get(k, ABSENT)
        if x != y:
            out.append((k, x, y))
    return out


# --------------------------------------------------------------------------
# the delta file
# --------------------------------------------------------------------------

class Rule(object):
    def __init__(self, kind, sym, frm, to, tag, reason, lineno):
        self.kind, self.sym = kind, sym
        self.frm, self.to = frm, to
        self.tag, self.reason = tag, reason
        self.lineno = lineno
        self.seen = False


def parse_delta(path, text=None):
    """(rules_by_symbol, headers).

    Tab-separated, because two of the values this file has to carry are kernel
    command lines and those contain spaces.  Five fields:

        derive<TAB>SYMBOL<TAB>from<TAB>to<TAB>mechanism<TAB>reason
        set   <TAB>SYMBOL<TAB>from<TAB>to<TAB>-        <TAB>reason

    A line this parser does not understand is an error, never a skip.  A delta
    file with a typo that silently dropped a rule would turn this gate off for
    exactly the symbol somebody cared enough about to write down.
    """
    if text is None:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    rules, headers = {}, {}
    for lineno, ln in enumerate(text.split("\n"), 1):
        ln = ln.rstrip("\r\n")
        if not ln.strip():
            continue
        if ln.startswith("#"):
            m = re.match(r"^#\s*([a-z0-9-]+):\s*(.*)$", ln)
            if m:
                headers.setdefault(m.group(1), m.group(2).strip())
            continue
        f = ln.split("\t")
        if len(f) != 6:
            die("%s:%d: %d tab-separated fields, expected 6 "
                "(kind, symbol, from, to, mechanism, reason). Line was: %r"
                % (path, lineno, len(f), ln[:120]))
        kind, sym, frm, to, tag, reason = f
        if kind not in ("derive", "set"):
            die("%s:%d: kind %r is not 'derive' or 'set'" % (path, lineno, kind))
        if not sym.startswith("CONFIG_"):
            die("%s:%d: %r does not look like a symbol" % (path, lineno, sym))
        if kind == "derive" and tag not in MECHANISMS:
            die("%s:%d: mechanism %r is not one of: %s"
                % (path, lineno, tag, ", ".join(sorted(MECHANISMS))))
        if kind == "set" and tag != "-":
            die("%s:%d: a `set` rule is mine, not kconfig's, so its mechanism "
                "field must be '-'; got %r" % (path, lineno, tag))
        if not reason.strip():
            die("%s:%d: %s has no reason. The whole point of this file is that "
                "every line carries one" % (path, lineno, sym))
        if sym in rules:
            die("%s:%d: %s already has a rule at line %d. Two rules for one "
                "symbol means one of them is never checked"
                % (path, lineno, sym, rules[sym].lineno))
        rules[sym] = Rule(kind, sym, frm, to, tag, reason, lineno)
    return rules, headers


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

class Result(object):
    def __init__(self):
        self.undeclared = []     # in the diff, no rule
        self.unapplied = []      # rule, not in the diff
        self.mismatch = []       # rule, in the diff, wrong from/to
        self.ok_derive = 0
        self.ok_set = 0

    @property
    def failed(self):
        return bool(self.undeclared or self.unapplied or self.mismatch)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_baseline_identity(path, headers):
    """The header names a sha256; check it rather than echoing it.

    Until 2026-08-28 this file printed `baseline-sha256` as provenance and never
    computed it.  Three of the four GPL drops carry a file at the baseline's
    path and two of them differ from it on eight symbol lines, so pointing the
    gate at the wrong one was possible and would have been reported as "the
    build drifted" rather than as "wrong baseline".
    """
    want = headers.get("baseline-sha256")
    if not want:
        die("%s: the delta file has no `# baseline-sha256:` header. The "
            "baseline is named by its hash, not by its path -- three of the "
            "drops on hand carry a file at that path" % path)
    got = sha256(path)
    if got != want:
        die("--baseline %s hashes %s and the delta declares %s. This is not "
            "the file the rules were written against"
            % (path, got[:16] + "\u2026", want[:16] + "\u2026"))
    return got


def check(baseline, delta, built, base_text=None, delta_text=None,
          built_text=None):
    a = parse_config(baseline, base_text)
    b = parse_config(built, built_text)
    rules, headers = parse_delta(delta, delta_text)
    r = Result()
    for sym, frm, to in diff_configs(a, b):
        rule = rules.get(sym)
        if rule is None:
            r.undeclared.append((sym, frm, to))
            continue
        rule.seen = True
        if rule.frm != frm or rule.to != to:
            r.mismatch.append((sym, frm, to, rule))
        elif rule.kind == "set":
            r.ok_set += 1
        else:
            r.ok_derive += 1
    for sym, rule in sorted(rules.items()):
        if not rule.seen:
            r.unapplied.append(rule)
    return r, headers, len(a), len(b)


def print_report(r, headers, na, nb, baseline, built, delta):
    print("kconfig-delta %s" % VERSION)
    print("baseline   %s   (%d symbols)" % (baseline, na))
    print("built      %s   (%d symbols)" % (built, nb))
    print("delta      %s" % delta)
    for k in ("baseline-sha256", "baseline-drop", "oldconfig-invocation"):
        if k in headers:
            print("  %-22s %s" % (k, headers[k]))
    print("")
    print("declared and applied:  %d derived by kconfig, %d set by rlxfw"
          % (r.ok_derive, r.ok_set))
    if r.undeclared:
        print("")
        print("UNDECLARED (%d) -- the build's .config differs here and nothing "
              "says why:" % len(r.undeclared))
        for sym, frm, to in r.undeclared:
            print("   %-44s %s -> %s" % (sym, frm, to))
    if r.mismatch:
        print("")
        print("MISMATCH (%d) -- declared, but not what happened:" % len(r.mismatch))
        for sym, frm, to, rule in r.mismatch:
            print("   %-44s declared %s -> %s, actual %s -> %s   (%s:%d)"
                  % (sym, rule.frm, rule.to, frm, to, os.path.basename(delta),
                     rule.lineno))
    if r.unapplied:
        print("")
        print("NOT APPLIED (%d) -- declared, and the built .config does not "
              "show it:" % len(r.unapplied))
        for rule in r.unapplied:
            print("   %-44s declared %s -> %s   (%s:%d)"
                  % (rule.sym, rule.frm, rule.to, os.path.basename(delta),
                     rule.lineno))
    print("")
    if r.failed:
        print("RESULT: \033[31mREFUSED\033[0m -- %d undeclared, %d mismatched, "
              "%d not applied." % (len(r.undeclared), len(r.mismatch),
                                   len(r.unapplied)))
    else:
        print("RESULT: \033[32mevery difference between the vendor template and "
              "the .config this build used is on the list\033[0m")


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
#
# Every one of these has to be able to fail, and C6 is the reason the file
# exists: it feeds the gate the file that was COPIED IN instead of the one the
# build USED, which is the mistake `notes/kernel-build.md` 6 names.

BASE_T = """#
# Automatically generated make config: don't edit
#
CONFIG_A=y
# CONFIG_B is not set
CONFIG_C=y
CONFIG_STR="console=ttyS0,38400 root=/dev/mtdblock1"
# CONFIG_GONE is not set
"""

BUILT_T = """#
# Automatically generated make config: don't edit
#
CONFIG_C=y
CONFIG_A=y
CONFIG_B=y
CONFIG_STR="console=ttyS0,38400 rlxfw"
CONFIG_NEW=y
"""

DELTA_T = (
    "# baseline-sha256: deadbeef\n"
    "derive\tCONFIG_B\tn\ty\tpromptless\tno prompt, default y\n"
    "derive\tCONFIG_GONE\tn\t-\tdep-unmet\tnot offered for this model\n"
    "derive\tCONFIG_NEW\t-\ty\tselected\tselected by CONFIG_A\n"
    "set\tCONFIG_STR\t\"console=ttyS0,38400 root=/dev/mtdblock1\""
    "\t\"console=ttyS0,38400 rlxfw\"\t-\tthe root= fallback is removed\n"
)


class Controls(object):
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append((name, bool(ok), detail))

    @property
    def failed(self):
        return [r for r in self.rows if not r[1]]


def _check_texts(base, delta, built):
    return check("<base>", "<delta>", "<built>", base, delta, built)


def _refuses(base, delta, built):
    """(did it refuse, what it said) -- a pass for the controls that feed it
    something malformed.  In-process; see `Refused`."""
    global _RAISE
    _RAISE = True
    try:
        _check_texts(base, delta, built)
        return False, "did NOT refuse"
    except Refused as e:
        return True, str(e)
    finally:
        _RAISE = False


def run_controls():
    c = Controls()

    r, _, _, _ = _check_texts(BASE_T, DELTA_T, BUILT_T)
    c.add("C1  the real shape passes", not r.failed,
          "%d derived + %d set, 0 undeclared" % (r.ok_derive, r.ok_set))

    # C2 -- an undeclared change must be caught.
    r, _, _, _ = _check_texts(BASE_T, DELTA_T, BUILT_T + "CONFIG_SNEAK=y\n")
    c.add("C2  an undeclared change FAILS",
          len(r.undeclared) == 1 and r.undeclared[0][0] == "CONFIG_SNEAK",
          "undeclared=%d" % len(r.undeclared))

    # C3 -- a declared change that did not happen must be caught.
    r, _, _, _ = _check_texts(BASE_T, DELTA_T + "set\tCONFIG_A\ty\tn\t-\tnever "
                              "landed\n", BUILT_T)
    c.add("C3  a declared change that did NOT land FAILS",
          len(r.unapplied) == 1 and r.unapplied[0].sym == "CONFIG_A",
          "unapplied=%d" % len(r.unapplied))

    # C4 -- right symbol, wrong destination value.
    bad = DELTA_T.replace("derive\tCONFIG_B\tn\ty\t", "derive\tCONFIG_B\tn\tm\t")
    r, _, _, _ = _check_texts(BASE_T, bad, BUILT_T)
    c.add("C4  a declared value that does not match FAILS",
          len(r.mismatch) == 1 and r.mismatch[0][0] == "CONFIG_B",
          "mismatch=%d" % len(r.mismatch))

    # C5 -- right destination, wrong claim about where it started.
    bad = DELTA_T.replace("derive\tCONFIG_B\tn\ty\t", "derive\tCONFIG_B\t-\ty\t")
    r, _, _, _ = _check_texts(BASE_T, bad, BUILT_T)
    c.add("C5  a wrong claim about the BASELINE value FAILS",
          len(r.mismatch) == 1, "mismatch=%d" % len(r.mismatch))

    # C6 -- THE control this file exists for.  Feed it the file that was copied
    # in.  Every declared difference is then absent, so it must refuse.
    r, _, _, _ = _check_texts(BASE_T, DELTA_T, BASE_T)
    c.add("C6  the PRE-oldconfig file fed as the built one FAILS",
          len(r.unapplied) == 4 and not r.undeclared,
          "unapplied=%d (all four declared differences missing)"
          % len(r.unapplied))

    # C7 -- kconfig rewrites in menu order; a reordering is not a difference.
    shuffled = "\n".join(reversed(BUILT_T.strip().split("\n"))) + "\n"
    r, _, _, _ = _check_texts(BASE_T, DELTA_T, shuffled)
    c.add("C7  a pure reordering is not a difference", not r.failed,
          "0 undeclared, 0 unapplied")

    # C8 -- ABSENT and n are different values, and 18 of this board's 21
    # derived differences are exactly that.
    d = diff_configs({"CONFIG_X": "n"}, {})
    c.add("C8  absent is not the same value as n",
          d == [("CONFIG_X", "n", ABSENT)], "%r" % (d,))

    # C9 -- the two values this file carries contain spaces, so the format has
    # to survive them without quoting rules.
    rules, _ = parse_delta("<delta>", None if False else DELTA_T)
    c.add("C9  a value containing spaces survives the format",
          rules["CONFIG_STR"].to == '"console=ttyS0,38400 rlxfw"',
          rules["CONFIG_STR"].to)

    # C10 -- a malformed rule is refused, not skipped.
    ok, last = _refuses(BASE_T, DELTA_T + "derive CONFIG_OOPS n y promptless x\n",
                        BUILT_T)
    c.add("C10 a space-separated (malformed) rule is REFUSED", ok, last[:78])

    # C11 -- two rules for one symbol: one of them would never be checked.
    ok, last = _refuses(BASE_T, DELTA_T + "set\tCONFIG_B\tn\ty\t-\tduplicate\n",
                        BUILT_T)
    c.add("C11 a duplicate rule for one symbol is REFUSED", ok, last[:78])

    # C12 -- a .config naming one symbol twice with two values: last-wins would
    # be a silent wrong answer about what the compiler saw.
    ok, last = _refuses(BASE_T, DELTA_T, BUILT_T + "CONFIG_A=n\n")
    c.add("C12 a .config with a contradictory duplicate is REFUSED", ok, last[:78])

    # C13 -- an invented mechanism is refused; the vocabulary is closed so that
    # "because kconfig does that" cannot be written into the reason column.
    ok, last = _refuses(BASE_T,
                        DELTA_T.replace("promptless", "because-kconfig"), BUILT_T)
    c.add("C13 a mechanism outside the closed vocabulary is REFUSED", ok, last[:78])

    # C14 -- a rule with an empty reason.
    ok, last = _refuses(BASE_T, DELTA_T + "set\tCONFIG_Q\t-\ty\t-\t\n", BUILT_T)
    c.add("C14 a rule with no reason is REFUSED", ok, last[:78])

    # C15 -- an empty or CONFIG-less built file must not read as "no differences".
    ok, last = _refuses(BASE_T, DELTA_T, "# nothing here\n")
    c.add("C15 a .config with no CONFIG_ lines at all is REFUSED", ok, last[:78])

    # ---- `apply`, which had NO control of its own until 2026-08-28.  Four
    # mutations to it -- dropping every set rule, losing the `# X is not set`
    # form, removing the from-value refusal, and writing over the baseline --
    # all passed the fifteen controls above.
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        bp = os.path.join(d, "base")
        dp = os.path.join(d, "delta")
        op = os.path.join(d, "out")
        with open(bp, "w", encoding="utf-8") as f:
            f.write(BASE_T)
        with open(dp, "w", encoding="utf-8") as f:
            f.write(DELTA_T)
        rc = cmd_apply({"baseline": bp, "delta": dp, "out": op})
        applied = parse_config(op)
        base = parse_config(bp)
        c.add("C17 apply actually applies the set rules",
              rc == 0 and applied.get("CONFIG_STR") ==
              '"console=ttyS0,38400 rlxfw"' and applied != base,
              "CONFIG_STR = %r" % applied.get("CONFIG_STR"))

        # C18 -- the `n` form has to survive the round trip, or every pinned
        # `is not set` line silently disappears from the build input.
        d2 = DELTA_T + "set\tCONFIG_C\ty\tn\t-\tpinned off\n"
        with open(dp, "w", encoding="utf-8") as f:
            f.write(d2)
        cmd_apply({"baseline": bp, "delta": dp, "out": op})
        txt = open(op, encoding="utf-8").read()
        c.add("C18 apply writes `# X is not set`, not `X=n`",
              "# CONFIG_C is not set" in txt and "CONFIG_C=n" not in txt,
              "the n form survives the round trip")

        # C19 -- a rule `apply` accepts must be one `check` accepts on apply's
        # own output.  A no-op pin used to pass apply and then be reported by
        # check as "declared and not applied", which is the generator and the
        # auditor disagreeing about the same file.  The refusal lives in
        # cmd_apply, so this control has to drive cmd_apply -- the first version
        # drove `check` and passed for the wrong reason.
        with open(dp, "w", encoding="utf-8") as f:
            f.write(DELTA_T + "set\tCONFIG_A\ty\ty\t-\ta no-op pin\n")
        global _RAISE
        _RAISE = True
        try:
            cmd_apply({"baseline": bp, "delta": dp, "out": op})
            ok, last = False, "did NOT refuse"
        except Refused as e:
            ok, last = True, str(e)
        finally:
            _RAISE = False
        c.add("C19 a `set` rule that changes nothing is REFUSED by apply",
              ok, last[:70])

        # C20 -- apply must not write over its own input.
        before = open(bp, "rb").read()
        with open(dp, "w", encoding="utf-8") as f:
            f.write(DELTA_T)
        cmd_apply({"baseline": bp, "delta": dp, "out": op})
        c.add("C20 apply leaves the baseline untouched",
              open(bp, "rb").read() == before, "%d bytes, unchanged" % len(before))

        # C21 -- the baseline is named by hash, and the hash is CHECKED.
        hdr = "# baseline-sha256: " + sha256(bp) + "\n"
        with open(dp, "w", encoding="utf-8") as f:
            f.write(hdr + DELTA_T)
        rules_ok, hh = parse_delta(dp)
        good = bad = None
        _RAISE = True
        try:
            check_baseline_identity(bp, hh)
            good = True
        except Refused as e:
            good = False
        try:
            check_baseline_identity(bp, {"baseline-sha256": "0" * 64})
            bad = False
        except Refused as e:
            bad = True
        finally:
            _RAISE = False
        c.add("C21 the baseline sha256 is computed, not echoed",
              good is True and bad is True,
              "the real hash passes and a wrong one refuses")

    # C22 -- THE defect A1 names: the kernel's own reader is not anchored at the
    # end of `is not set`, so an anchored regex here would drop a line the
    # compiler honoured and let a real drift through.
    d_ = parse_config("<x>", "CONFIG_A=y\n# CONFIG_B is not set   (a note)\n")
    c.add("C22 `# X is not set` with a trailing comment is still `n`",
          d_.get("CONFIG_B") == "n",
          "confdata.c:221 is `strncmp(p, \"is not set\", 10)`, unanchored")

    # C16 -- the only control that leaves this process, and the reason it can:
    # `main` checks the three paths exist BEFORE it runs the controls, so this
    # child refuses without running controls of its own and cannot recurse.
    # It is what pins `refusal == exit 3` at the command line rather than at
    # the exception, which is the contract every caller of this tool sees.
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "base")
        with open(p, "w", encoding="utf-8") as f:
            f.write(BASE_T)
        cp = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "check",
             "--baseline", p, "--delta", p,
             "--built", os.path.join(d, "does-not-exist")],
            capture_output=True, text=True, timeout=60)
    c.add("C16 a missing file exits 3 at the command line", cp.returncode == 3,
          "rc=%d  %s" % (cp.returncode,
                         (cp.stdout + cp.stderr).strip().split("\n")[-1][:52]))

    return c


def print_controls(c):
    print("controls (they run first; the file is not reported on if any fails)")
    for name, ok, detail in c.rows:
        # Uncoloured, and padded: `tools/ci-census.py` counts these lines with
        # `^ {2}(ok|FAIL)\s{2,}`, and an escape sequence in front of the mark
        # makes every case invisible to it -- a suite that reports nothing then
        # reads as a suite whose cases went missing.
        print("  %-5s %-56s %s" % ("ok" if ok else "FAIL", name, detail))
    print("")


# --------------------------------------------------------------------------

def cmd_apply(args):
    """Emit the .config to feed the tree: baseline + every `set` rule.

    This is the half that keeps the delta file honest.  If `apply` and `check`
    read different files, the thing that generated the build and the thing that
    audits it can drift apart and each will still pass.  Here they read the
    same file, so a `set` rule that is wrong shows up as a build that does not
    have what it says, and a `set` rule that is missing shows up as an
    undeclared difference.

    `derive` rules are deliberately NOT applied: kconfig produces those, and
    applying them here would hide the case where it stops doing so.
    """
    a = parse_config(args["baseline"])
    rules, _ = parse_delta(args["delta"])
    sets = {s: r for s, r in rules.items() if r.kind == "set"}
    for sym, r in sets.items():
        cur = a.get(sym, ABSENT)
        if cur != r.frm:
            die("%s: the delta says it is %r in the baseline and it is %r. "
                "Refusing to apply a rule whose starting point is not there"
                % (sym, r.frm, cur))
        if r.frm == r.to:
            # `apply` would emit it and `check` would then call it "declared and
            # not applied" on apply's own output -- the generator and the
            # auditor disagreeing about the same file, which is the thing this
            # pair exists to make impossible.  C19 is the control.
            die("%s: a `set` rule whose from and to are both %r changes "
                "nothing, and `check` reports it as not applied. A rule that "
                "makes `apply`'s own output fail `check` is refused here"
                % (sym, r.frm))
    out, seen = [], set()
    with open(args["baseline"], encoding="utf-8", errors="replace") as f:
        for ln in f.read().split("\n"):
            m = RE_SET.match(ln) or RE_NOT.match(ln)
            sym = m.group(1) if m else None
            if sym in sets:
                r = sets[sym]
                seen.add(sym)
                if r.to == ABSENT:
                    continue
                out.append(_line(sym, r.to))
            else:
                out.append(ln)
    for sym, r in sorted(sets.items()):
        if sym not in seen and r.to != ABSENT:
            out.append(_line(sym, r.to))
    text = "\n".join(out).rstrip("\n") + "\n"
    tmp = args["out"] + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, args["out"])
    print("kconfig-delta %s" % VERSION)
    print("baseline  %s" % args["baseline"])
    print("delta     %s   (%d set rule(s) applied, %d derive rule(s) left to "
          "kconfig)" % (args["delta"], len(sets), len(rules) - len(sets)))
    print("out       %s" % args["out"])
    return 0


def _line(sym, val):
    return "# %s is not set" % sym if val == "n" else "%s=%s" % (sym, val)


def cmd_explain(args):
    a = parse_config(args["baseline"])
    b = parse_config(args["built"])
    rules = {}
    if args["delta"]:
        rules, _ = parse_delta(args["delta"])
    print("# starting point for a delta file -- every mechanism and reason "
          "below is a placeholder")
    for sym, frm, to in diff_configs(a, b):
        old = rules.get(sym)
        if old:
            print("%s\t%s\t%s\t%s\t%s\t%s"
                  % (old.kind, sym, frm, to, old.tag, old.reason))
        else:
            print("derive\t%s\t%s\t%s\tFIXME\tFIXME" % (sym, frm, to))
    return 0


def parse_args(argv):
    if not argv:
        die("no command. One of: apply, check, explain, self-test")
    cmd, rest = argv[0], argv[1:]
    a = {"baseline": None, "delta": None, "built": None, "out": None}
    i = 0
    while i < len(rest):
        x = rest[i]
        if x in ("--baseline", "--delta", "--built", "--out"):
            if i + 1 >= len(rest):
                die("%s needs a value" % x)
            a[x[2:]] = rest[i + 1]
            i += 2
        else:
            die("unknown option %s" % x)
    return cmd, a


def main(argv):
    cmd, a = parse_args(argv)

    if cmd == "self-test":
        c = run_controls()
        print_controls(c)
        nf = len(c.failed)
        if nf:
            print("RESULT: %d passed, \033[31m%d failed\033[0m"
                  % (len(c.rows) - nf, nf))
            return 2
        print("RESULT: \033[32m%d passed, 0 failed\033[0m" % len(c.rows))
        return 0

    if cmd == "explain":
        for k in ("baseline", "built"):
            if not a[k]:
                die("explain needs --%s" % k)
        return cmd_explain(a)

    if cmd == "apply":
        for k in ("baseline", "delta", "out"):
            if not a[k]:
                die("apply needs --%s" % k)
        for k in ("baseline", "delta"):
            if not os.path.isfile(a[k]):
                die("--%s %s: no such file" % (k, a[k]))
        c = run_controls()
        if c.failed:
            print("REFUSED: %d control(s) failed." % len(c.failed))
            return 2
        _, headers0 = parse_delta(a["delta"])
        check_baseline_identity(a["baseline"], headers0)
        return cmd_apply(a)

    if cmd != "check":
        die("unknown command %r" % cmd)

    for k in ("baseline", "delta", "built"):
        if not a[k]:
            die("check needs --%s" % k)
        if not os.path.isfile(a[k]):
            die("--%s %s: no such file" % (k, a[k]))

    c = run_controls()
    print_controls(c)
    if c.failed:
        print("REFUSED: %d control(s) failed. Nothing is reported about the "
              "build until the checker itself is trusted." % len(c.failed))
        return 2

    _, headers0 = parse_delta(a["delta"])
    check_baseline_identity(a["baseline"], headers0)
    r, headers, na, nb = check(a["baseline"], a["delta"], a["built"])
    print_report(r, headers, na, nb, a["baseline"], a["built"], a["delta"])
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
