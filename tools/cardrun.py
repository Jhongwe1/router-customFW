#!/usr/bin/env python3
"""cardrun -- run a frozen bench card's cells verbatim, in the order named, and
be the ONE owner of the card grammar (SPEC.md FW-124).

    cardrun.py --card PATH [--dry] [--log PATH] ITEM [ITEM ...]
    cardrun.py --self-test

ITEM is one of
    NAME            run the fenced cell NAME; a non-zero exit STOPS the run
    NAME?           run it; a non-zero exit is a READING -- recorded, no stop,
                    and a later gate on NAME is skipped with a line saying so
    wait:NAME       wait for the HOST& cell NAME, started earlier in this
                    invocation, to exit
    gate:KIND:NAME  a check at one of the card's decision points.  KIND is
                    until | prompt | caught | hpstop | grep=REGEX; NAME is the
                    last `:` field, so REGEX may hold `:`

Why this file exists
--------------------
量 2026-09-23: twice a frozen card carried a HOST cell whose own tool rejected
its arguments, found only at the bench (block 41's `netblast` options, card
B44's `Z9-D2`).  The cure is `cardcheck` refusing such a cell before the
freeze, and for that `cardcheck` must read a card exactly as the runner
executes it.  Until now the only thing that parsed a card's macros and HOST
cells was a scratch script, `s105-run.py`, which named card B44 in its code.
This is that runner with no card in it, and its grammar functions are what
`cardcheck` loads by path (as it loads `reply-size.py`): the reading that is
checked and the reading that is run have one owner.

The grammar -- pure functions, text in and data out
----------------------------------------------------
* A MACRO is defined at the start of a line, `NAME` = `body` or
  `NAME <p>` = `body`.  NAME is an upper-case letter, then upper-case letters
  and digits (a digit-led name would expand inside numbers).  One or more
  spaces before `=` (blocks 40 and 41 align `NB`  =), one after.  Whatever
  follows the body's closing backtick on that line is prose and is ignored
  (card B44's `FL`).  A name defined twice is REFUSED.  A body that spans
  lines is refused where it is USED: bash would run it as two commands.
* expand(): the longest name first, as a whole word -- not after or before a
  letter, digit, `_`, `/`, `.` or `-`, so `HP` never expands inside `P1-HP`.
  A parameterised macro takes the next word as its argument and is refused
  without one (the end of the text, or an operator such as `;`).  One pass: a
  body is not re-scanned.  ⚠️ Expansion is TEXTUAL, so a macro name inside a
  quoted string expands there too (s107 hostcell REPORT § 6 (1)).
* CELLS, for the runner: only lines inside a plain ``` fence (no info string)
  in the card's cells section -- the one `## ` heading holding `The cells`, up
  to the next `## `.  Each is `CAP --out <prefix> ...`, `HOST <prefix> ::
  <cmd>` or `HOST& <prefix> :: <cmd>`; ANY other line there, a blank one
  included, is refused.  A cell's name is its prefix's last `/` field, unique.
* host_lines(): every `^HOST&? <prefix> :: <cmd>` line ANYWHERE in a card:
  older cards put HOST lines outside fences, and this is what `cardcheck`
  sweeps.
* simple_commands() / unwrap() / tool_of(): the shell reading of one expanded
  command -- quotes, `$...`, operators, redirections, `VAR=` prefixes, shell
  keywords, the `timeout` and `sudo` wrappers.  `cardcheck` classifies with
  it; the runner uses it to know which program a HOST& cell starts.  It is a
  reading of the forms cards use, not a shell: see simple_commands().

Execution
---------
The repository root is every command's working directory.  A CAP line runs
through `bash -c` with the terminal attached; a HOST line with its output to
`<prefix>.log`; a HOST& line the same, in its own session, and the next item
waits for the program's own start signal:
    hostprobe run   a `start` line in <its --out>.events (card B44's rule, FW-116)
    hostclock run   `hostclock.py wait <its --out> --timeout T` exits 0.  The
                    tool's own readiness verb (every enabled instrument has
                    written a row and the logger is alive), chosen over reading
                    the .clock start row: the start row says only that the
                    logger began, and a second reader of the .clock format
                    would be a second owner of it
    tcpdump         `listening on` in <prefix>.log
Any other background program is REFUSED before the first item runs.  A cell
whose <prefix>.log, .meta.json, .events, .timing or .clock exists is refused,
never re-run.  On any stop -- a failed cell or gate, an interrupt -- every
HOST& process group still running gets SIGINT, then SIGKILL 8 s later.
The transcript (--log, required unless --dry) is written OUTSIDE the
repository, one line per event, stamped on CLOCK_MONOTONIC_RAW (P2-4 § 1).

Dropped from s105-run.py, deliberately
--------------------------------------
* OVERRIDE, a card's line replaced at run time: a CORRECTIONS entry is
  executed as a declared off-card cell, outside this runner.
* The `P1-SRVR` restart and `offcard:` (card B44's conditional cell): off-card
  cells are declared in CORRECTIONS first and run by hand.
* The `map` gate's hardcoded digests, and `fl0` (card B44's): `grep=` says
  the same, e.g. `gate:grep=\\A(?:0\\n)+\\Z:P1-FL`.
* The host-bug counter, withdrawn with CORRECTIONS-block42 § 5.1.
* The iperf3 special cases: replaced by `NAME?`, declared per invocation.

Exit codes: 0 every item done; 2 refused before any item ran; 3 stopped.
`--self-test` runs synthetic cards with fake programs in a temporary
directory: no board, no port, nothing written under bench/.
"""
import argparse
import collections
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

TOOL_VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOCK = "CLOCK_MONOTONIC_RAW"
BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"
CLOCKSOURCE_PATH = "/sys/devices/system/clocksource/clocksource0/current_clocksource"
PYTHON = "/usr/bin/python3"         # CLAUDE.md: bench commands run /usr/bin/python3
START_TIMEOUT_S = 20.0              # s105-run's, which every card B44 HOST& start met
KILL_GRACE_S = 8.0
RECORD_SUFFIXES = (".log", ".meta.json", ".events", ".timing", ".clock")
GATE_KINDS = ("until", "prompt", "caught", "hpstop")


class Refused(Exception):
    """A refusal before anything ran: the card, an argument, or the host."""


class Stop(Exception):
    """A stop after something ran: every HOST& group still running is
    interrupted."""


# =============================================================== the grammar
Macro = collections.namedtuple("Macro", "param body line")
Cell = collections.namedtuple("Cell", "name kind prefix line lineno")
HostLine = collections.namedtuple("HostLine", "kind prefix name cmd lineno")

MACRO_RE = re.compile(r"^`([A-Z][A-Z0-9]*)(?: <(\w+)>)?` += `([^`]+)`", re.M)
CAP_CELL_RE = re.compile(r"^CAP --out (\S+) \S")
HOST_CELL_RE = re.compile(r"^(HOST&?) (\S+) :: (\S.*)$")
HOST_LINE_RE = re.compile(r"^(HOST&?) (\S+) :: (.*)$", re.M)
SECTION_RE = re.compile(r"^## .*\bThe cells\b", re.M)
NEXT_SECTION_RE = re.compile(r"^## ", re.M)
OPERATOR_WORD_RE = re.compile(r"^[;&|<>()]+$")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")


def _lineno(text, pos):
    return text.count("\n", 0, pos) + 1


def _no_cr(text):
    if "\r" in text:
        raise Refused("the card holds a CR at line %d: every cell's last word would "
                      "carry it into bash (FW-108: every committed card is LF)"
                      % _lineno(text, text.index("\r")))


def macros(text):
    """-> {NAME: Macro(param, body, line)}, every line-start definition.

    Refused: a name defined twice -- which body a cell gets would depend on
    which reader read the card."""
    table = {}
    for m in MACRO_RE.finditer(text):
        name, line = m.group(1), _lineno(text, m.start())
        if name in table:
            raise Refused("macro `%s` is defined twice, at lines %d and %d: which body "
                          "a cell gets would depend on the reader" % (name, table[name].line, line))
        table[name] = Macro(m.group(2), m.group(3), line)
    return table


def expand(cmd, table):
    """`cmd` with every macro replaced by its body.  Refused: a parameterised
    macro with no argument, and a body that spans lines."""
    if not table:
        return cmd
    names = sorted(table, key=len, reverse=True)
    pat = re.compile(r"(?<![\w/.-])(" + "|".join(map(re.escape, names)) + r")(?![\w/.-])")
    out, i = [], 0
    while True:
        m = pat.search(cmd, i)
        if not m:
            out.append(cmd[i:])
            return "".join(out)
        out.append(cmd[i:m.start()])
        mac = table[m.group(1)]
        if "\n" in mac.body:
            raise Refused("macro `%s` (line %d) has a body that spans lines: bash would run "
                          "it as two commands" % (m.group(1), mac.line))
        body, j = mac.body, m.end()
        if mac.param:
            a = re.match(r"[ \t]+(\S+)", cmd[j:])
            if not a or OPERATOR_WORD_RE.match(a.group(1)):
                raise Refused("macro `%s` needs its <%s> argument, and `%s` has none"
                              % (m.group(1), mac.param, cmd.strip()[:80]))
            body = body.replace("<%s>" % mac.param, a.group(1))
            j += a.end()
        out.append(body)
        i = j


def cells_section(text):
    """-> (start, end) offsets of the one `## ... The cells` section."""
    heads = list(SECTION_RE.finditer(text))
    if len(heads) != 1:
        raise Refused("the card has %d `## ... The cells` headings; the runner reads its "
                      "cells from exactly one" % len(heads))
    nxt = NEXT_SECTION_RE.search(text, heads[0].end())
    return heads[0].start(), (nxt.start() if nxt else len(text))


def fenced_cells(text):
    """-> [Cell] in card order: the lines of every plain ``` fence inside the
    cells section.  Refused: a line there that is not a cell, a cell name
    used twice, a fence never closed, and a section with no cell at all."""
    _no_cr(text)
    s, e = cells_section(text)
    base = _lineno(text, s)
    out, seen, fence = [], {}, None
    for k, line in enumerate(text[s:e].split("\n")):
        n = base + k
        if fence is None:
            if line.startswith("```"):
                fence = (line[3:].strip(), n)
            continue
        if line.rstrip() == "```":
            fence = None
            continue
        if fence[0]:
            continue                    # ```cells, ```cardnum ...: not cells
        m = CAP_CELL_RE.match(line)
        if m:
            kind, prefix = "CAP", m.group(1)
        else:
            m = HOST_CELL_RE.match(line)
            if not m:
                raise Refused("line %d, inside a plain fence of the cells section, is not "
                              "a cell: %r. Every line there is `CAP --out <prefix> ...`, "
                              "`HOST <prefix> :: <cmd>` or `HOST& <prefix> :: <cmd>`"
                              % (n, line[:100]))
            kind, prefix = m.group(1), m.group(2)
        name = prefix.rsplit("/", 1)[-1]
        if not NAME_RE.fullmatch(name):
            raise Refused("line %d: the prefix %r ends in no cell name" % (n, prefix))
        if name in seen:
            raise Refused("cell %s is defined twice, at lines %d and %d" % (name, seen[name], n))
        seen[name] = n
        out.append(Cell(name, kind, prefix, line, n))
    if fence is not None:
        raise Refused("the fence opened at line %d is never closed" % fence[1])
    if not out:
        raise Refused("the cells section holds no cell in a plain ``` fence")
    return out


def host_lines(text):
    """-> [HostLine] for every `HOST <prefix> :: <cmd>` / `HOST& ...` line
    anywhere in the card, fenced or not -- the population `cardcheck` sweeps."""
    out = []
    for m in HOST_LINE_RE.finditer(text):
        n = _lineno(text, m.start())
        if "\r" in m.group(3):
            raise Refused("HOST line %d ends in a CR" % n)
        out.append(HostLine(m.group(1), m.group(2), m.group(2).rsplit("/", 1)[-1],
                            m.group(3), n))
    return out


def cell_command(cell, table):
    """The command a cell runs: a CAP line whole, a HOST line after ` :: `."""
    if cell.kind == "CAP":
        return expand(cell.line, table)
    return expand(cell.line.split(" :: ", 1)[1], table)


# ------------------------------------------------------- the shell reading
Word = collections.namedtuple("Word", "text raw quoted expands globs placeholder")
Simple = collections.namedtuple("Simple", "words assigns redirs")

_OPS = (("&>>", "<<<", "<<-"),
        ("&&", "||", ";;", "|&", ">>", "<<", "<>", "<&", ">&", ">|", "&>"),
        (";", "&", "|", "(", ")", "<", ">"))
REDIR_OPS = frozenset(("&>>", "<<<", "<<-", ">>", "<<", "<>", "<&", ">&", ">|", "&>",
                       "<", ">"))
PLACEHOLDER_RE = re.compile(r"<[A-Za-z][A-Za-z0-9_-]*>")
ASSIGN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_WORD_END = frozenset(" \t\n;&|()<>")
LEAD_KEYWORDS = frozenset(("!", "{", "do", "then", "else", "elif", "if", "while", "until",
                           "time"))
NO_PROGRAM = frozenset(("done", "fi", "}", "esac", "in", "for", "select", "[["))
UNPARSED = frozenset(("case", "function", "coproc"))
PYTHONS = frozenset(("python3", "python", "/usr/bin/python3", "/usr/bin/python"))
TOOL_ARG_RE = re.compile(r"(?:\./)?tools/([A-Za-z0-9][A-Za-z0-9_.-]*)\.py")


def _op_at(s, i):
    for group in _OPS:
        for op in group:
            if s.startswith(op, i):
                return op
    return None


def _close_paren(s, i):
    """The index after the `)` that closes the `(` at s[i]."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c in "'\"":
            k = s.find(c, j + 1)
            if k < 0:
                break
            j = k + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise Refused("an unclosed $( in %r" % s[:80])


def _word(s, i):
    """One shell word from s[i] -> (Word, the index after it)."""
    n, start = len(s), i
    text, bare = [], []
    quoted = expands = placeholder = False
    while i < n:
        c = s[i]
        if c == "<":
            m = PLACEHOLDER_RE.match(s, i)
            if not m:
                break
            text.append(m.group(0))
            bare.append(m.group(0))
            placeholder, i = True, m.end()
            continue
        if c in _WORD_END:
            break
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise Refused("an unclosed ' quote in %r" % s[:80])
            text.append(s[i + 1:j])
            quoted, i = True, j + 1
            continue
        if c == '"':
            j, buf = i + 1, []
            while True:
                if j >= n:
                    raise Refused('an unclosed " quote in %r' % s[:80])
                d = s[j]
                if d == '"':
                    break
                if d == "\\" and j + 1 < n and s[j + 1] in '$`"\\':
                    buf.append(s[j + 1])
                    j += 2
                    continue
                if d in "$`":
                    expands = True
                buf.append(d)
                j += 1
            text.append("".join(buf))
            quoted, i = True, j + 1
            continue
        if c == "\\":
            if i + 1 < n:
                text.append(s[i + 1])
            quoted, i = True, i + 2
            continue
        if c == "$" and s.startswith("$(", i):
            j = _close_paren(s, i + 1)
            text.append(s[i:j])
            bare.append(s[i:j])
            expands, i = True, j
            continue
        if c == "$" and s.startswith("${", i):
            j = s.find("}", i)
            if j < 0:
                raise Refused("an unclosed ${ in %r" % s[:80])
            text.append(s[i:j + 1])
            bare.append(s[i:j + 1])
            expands, i = True, j + 1
            continue
        if c == "`":
            j = s.find("`", i + 1)
            if j < 0:
                raise Refused("an unclosed backtick in %r" % s[:80])
            text.append(s[i:j + 1])
            bare.append(s[i:j + 1])
            expands, i = True, j + 1
            continue
        if c == "$":
            expands = True
        text.append(c)
        bare.append(c)
        i += 1
    b = "".join(bare)
    globs = bool(re.search(r"[*?\[]", b) or re.search(r"\{[^{}]*(?:,|\.\.)[^{}]*\}", b)
                 or b.startswith("~"))
    return Word("".join(text), s[start:i], quoted, expands, globs, placeholder), i


def _lex(s):
    """-> [(kind, value, start, end)]: kind W (a Word), OP or REDIR."""
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t":
            i += 1
            continue
        if c == "\n":
            toks.append(("OP", "\n", i, i + 1))
            i += 1
            continue
        if c == "#":                    # a comment: `#` starting a word
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "<" and PLACEHOLDER_RE.match(s, i):
            w, j = _word(s, i)
            toks.append(("W", w, i, j))
            i = j
            continue
        op = _op_at(s, i)
        if op:
            if op in ("<", ">") and s.startswith("(", i + 1):
                raise Refused("process substitution `%s(`: a construct this reading does "
                              "not parse" % op)
            toks.append(("REDIR" if op in REDIR_OPS else "OP", op, i, i + len(op)))
            i += len(op)
            continue
        w, j = _word(s, i)
        toks.append(("W", w, i, j))
        i = j
    return toks


def simple_commands(cmd):
    """-> [Simple(words, assigns, redirs)], one per simple command of `cmd`.

    Understood: '...' and "..." quoting and backslashes; `$x`, `${x}`, `$(...)`
    and backticks as expansions (flagged, never performed); the control
    operators `;` `&` `|` `&&` `||` `|&` `(` `)` and newline; redirections,
    dropped with their target, a digit glued to one (`2>&1`) included; leading
    `VAR=value` words; an unquoted `<name>` as a card's unfilled placeholder,
    not two redirections.  Not understood, refused: process substitution, and
    an unclosed quote or `$(`.  ⚠️ `cmd <in>out` reads as a placeholder here
    and as two redirections in bash; no card writes it.
    """
    toks = _lex(cmd)
    out, words, assigns, redirs = [], [], [], []

    def flush():
        if words or assigns or redirs:
            out.append(Simple(tuple(words), tuple(assigns), tuple(redirs)))
        del words[:], assigns[:], redirs[:]

    i = 0
    while i < len(toks):
        kind, val, _st, en = toks[i]
        if kind == "OP":
            flush()
            i += 1
            continue
        if kind == "REDIR":
            if i + 1 >= len(toks) or toks[i + 1][0] != "W":
                raise Refused("the redirection `%s` has no target in %r" % (val, cmd[:80]))
            redirs.append((val, toks[i + 1][1]))
            i += 2
            continue
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if nxt and nxt[0] == "REDIR" and nxt[2] == en and re.fullmatch(r"[0-9]+", val.raw):
            i += 1                      # an IO number: `2>&1`'s 2 is its redirection's
            continue
        if not words and ASSIGN_RE.match(val.raw):
            assigns.append(val)
            i += 1
            continue
        words.append(val)
        i += 1
    flush()
    return out


def _after_timeout(w):
    """`timeout [OPTION] DURATION COMMAND...` -> COMMAND..., or None."""
    j = 1
    while j < len(w) and w[j].text.startswith("-") and w[j].text != "-":
        t = w[j].text
        if t == "--":
            j += 1
            break
        j += 2 if t in ("-s", "-k", "--signal", "--kill-after") else 1
    if j >= len(w) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?[smhd]?", w[j].text):
        return None
    return w[j + 1:] or None


_SUDO_ARG = frozenset(("-u", "-g", "-C", "-D", "-R", "-T", "-U", "-p", "-r", "-t",
                       "--user", "--group", "--prompt", "--close-from", "--chdir",
                       "--chroot", "--command-timeout", "--other-user", "--role", "--type"))


def _after_sudo(w):
    """`sudo [OPTION] [VAR=value] COMMAND...` -> COMMAND..., or None."""
    j = 1
    while j < len(w):
        t = w[j].text
        if t == "--":
            j += 1
            break
        if not t.startswith("-") or t == "-":
            break
        j += 2 if t in _SUDO_ARG else 1
    rest = list(w[j:])
    while rest and ASSIGN_RE.match(rest[0].raw):
        rest.pop(0)
    return rest or None


def unwrap(simple):
    """-> (argv, wrappers, note): the program a simple command runs.

    Leading keywords (`do`, `then`, `if`, `!`, `{`, `time` ...) and the
    `timeout` and `sudo` wrappers are stripped.  note is None for a program,
    "keyword-only" for a simple command that runs none (`done`, a `for`
    header), and a reason for a construct this reading does not parse."""
    w, wrappers = list(simple.words), []
    while True:
        while w and not w[0].quoted and w[0].text in LEAD_KEYWORDS:
            kw = w.pop(0).text
            if kw == "time" and w and w[0].text == "-p":
                w.pop(0)
            while w and ASSIGN_RE.match(w[0].raw):
                w.pop(0)
        if not w:
            return [], wrappers, "keyword-only"
        t = None if w[0].quoted else w[0].text
        if t in NO_PROGRAM:
            return [], wrappers, "keyword-only"
        if t in UNPARSED:
            return [], wrappers, ("`%s`: a shell construct this reading does not parse, "
                                  "so its commands cannot be checked" % t)
        if t == "timeout":
            rest = _after_timeout(w)
            if rest is None:
                return [], wrappers, "`timeout` with no duration or no command"
            wrappers.append("timeout")
            w = rest
            continue
        if t == "sudo":
            rest = _after_sudo(w)
            if rest is None:
                return [], wrappers, "`sudo` with no command"
            wrappers.append("sudo")
            w = rest
            continue
        return w, wrappers, None


def tool_of(argv):
    """-> (NAME, args) for `<python> tools/NAME.py ARGS...`, else None."""
    if (len(argv) >= 2 and not argv[0].quoted and argv[0].text in PYTHONS
            and not (argv[1].expands or argv[1].globs or argv[1].placeholder)):
        m = TOOL_ARG_RE.fullmatch(argv[1].text)
        if m:
            return m.group(1), list(argv[2:])
    return None


def _last_option(args, opt):
    val = None
    for k, w in enumerate(args):
        if w.text == opt and k + 1 < len(args):
            val = args[k + 1].text
        elif w.text.startswith(opt + "="):
            val = w.text[len(opt) + 1:]
    return val


def background_program(cmd):
    """-> (kind, out) for a HOST& command: which program it starts and the
    --out whose record signals its start.  Refused: none or two programs, a
    construct not parsed, or a program with no known start signal."""
    progs = []
    for s in simple_commands(cmd):
        argv, _wr, note = unwrap(s)
        if note == "keyword-only":
            continue
        if note:
            raise Refused(note)
        progs.append(argv)
    if len(progs) != 1:
        raise Refused("a HOST& cell starts exactly one program, so the runner knows whose "
                      "start to wait for; `%s` starts %d" % (cmd[:80], len(progs)))
    argv = progs[0]
    t = tool_of(argv)
    if t and t[0] in ("hostprobe", "hostclock") and t[1] and t[1][0].text == "run":
        out = _last_option(t[1], "--out")
        if not out:
            raise Refused("tools/%s.py run with no --out: the runner waits on the record "
                          "that --out names" % t[0])
        return t[0], out
    if os.path.basename(argv[0].text) == "tcpdump":
        return "tcpdump", None
    raise Refused("`%s` has no start signal this runner knows (hostprobe run, hostclock "
                  "run, tcpdump): a background cell it cannot wait on would race the "
                  "next cell" % " ".join(x.text for x in argv[:3]))


# ================================================================== running
def raw():
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)


def _read1(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return "-"


def parse_item(it):
    """-> (kind, name, arg): kind run | reading | wait | gate.  Refused: a
    malformed item, an unknown gate kind, a grep= that cannot fail or compile."""
    if it.startswith("wait:"):
        name = it[5:]
        if not NAME_RE.fullmatch(name):
            raise Refused("%r: wait:NAME names a HOST& cell" % it)
        return "wait", name, None
    if it.startswith("gate:"):
        body = it[5:]
        if ":" not in body:
            raise Refused("%r: a gate is gate:KIND:NAME" % it)
        kind, name = body.rsplit(":", 1)
        if not NAME_RE.fullmatch(name):
            raise Refused("%r: the gate's last field is a cell name" % it)
        if kind.startswith("grep="):
            rx = kind[5:]
            if not rx:
                raise Refused("%r: an empty grep= pattern matches every log, so the gate "
                              "could not fail" % it)
            try:
                re.compile(rx, re.M)
            except re.error as e:
                raise Refused("%r: grep= pattern does not compile: %s" % (it, e)) from None
        elif kind not in GATE_KINDS:
            raise Refused("%r: gate kinds are %s and grep=REGEX" % (it, ", ".join(GATE_KINDS)))
        return "gate", name, kind
    if it.endswith("?"):
        name = it[:-1]
        if not NAME_RE.fullmatch(name):
            raise Refused("%r: NAME? declares a cell whose non-zero exit is a reading" % it)
        return "reading", name, None
    if not NAME_RE.fullmatch(it):
        raise Refused("%r is not an item: NAME, NAME?, wait:NAME or gate:KIND:NAME" % it)
    return "run", it, None


class Runner:
    """One card, one invocation.  `root` is every command's working directory;
    the self-test hands it a temporary one."""

    def __init__(self, text, label, root, dry=False, logf=None, echo=True,
                 start_timeout=START_TIMEOUT_S, kill_grace=KILL_GRACE_S):
        _no_cr(text)
        self.text, self.label, self.root, self.dry = text, label, root, dry
        self.logf, self.echo = logf, echo
        self.start_timeout, self.kill_grace = start_timeout, kill_grace
        self.table = macros(text)
        self.order = fenced_cells(text)
        self.cells = {c.name: c for c in self.order}
        self.bg, self.bgkind, self.readings, self.lines = {}, {}, {}, []

    # ------------------------------------------------------------ plumbing
    def say(self, msg):
        line = msg if self.dry else "[%.6f %s] %s" % (raw(), time.strftime("%H:%M:%S"), msg)
        self.lines.append(line)
        if self.echo:
            print(line, flush=True)
        if self.logf:
            self.logf.write(line + "\n")
            self.logf.flush()

    def _path(self, prefix):
        return os.path.join(self.root, prefix)

    @staticmethod
    def _text(path):
        try:
            with open(path, "rb") as f:
                return f.read().decode("utf-8", "replace").replace("\r", "")
        except OSError:
            return ""

    @staticmethod
    def _meta(key):
        try:
            with open(key + ".meta.json", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    # ----------------------------------------------------------- the plan
    def plan(self, items):
        """Every refusal that reads the card, before anything runs: an item
        naming no cell, an expansion refused, a background program with no
        known start signal, a wait on a cell not started before it."""
        started = set()
        for it in items:
            kind, name, _arg = parse_item(it)
            if kind == "gate":
                if name not in self.cells:
                    raise Refused("%s: no fenced cell named %s" % (it, name))
                continue
            if kind == "wait":
                if name not in started:
                    raise Refused("%s: no HOST& cell of that name starts earlier in this "
                                  "invocation" % it)
                continue
            if name not in self.cells:
                raise Refused("no fenced cell named %s" % name)
            cell = self.cells[name]
            cmd = cell_command(cell, self.table)
            if cell.kind == "HOST&":
                if kind == "reading":
                    raise Refused("%s?: a background cell's exit is read at wait:, not "
                                  "declared a reading" % name)
                self.bgkind[name] = background_program(cmd)
                started.add(name)

    # ------------------------------------------------------------ the run
    def run(self, items):
        try:
            for it in items:
                self._item(it)
        except (Stop, OSError) as e:
            # An OSError here is the host's (no bash, a vanished directory, a
            # record created between the check and the open): a stop with its
            # reason, never a traceback that leaves HOST& children running.
            self.say("STOP: %s" % e)
            self.stop_children()
            return 3
        except KeyboardInterrupt:
            self.say("STOP: interrupted")
            self.stop_children()
            return 3
        try:
            for name, p in self.bg.items():
                if p.poll() is None:
                    self.say("WAIT (end) %s" % name)
                    p.wait()
                    self.say("DONE %s rc=%s" % (name, p.returncode))
        except KeyboardInterrupt:
            self.say("STOP: interrupted while the background cells finished")
            self.stop_children()
            return 3
        self.say("ALL ITEMS DONE")
        return 0

    def _item(self, it):
        kind, name, arg = parse_item(it)
        if kind == "wait":
            if self.dry:
                self.say("DRY wait %s" % name)
                return
            self.say("WAIT %s" % name)
            p = self.bg[name]
            p.wait()
            self.say("DONE %s rc=%s" % (name, p.returncode))
            return
        if kind == "gate":
            if self.dry:
                self.say("DRY gate %s %s" % (arg, name))
                return
            if name in self.readings:
                self.say("GATE %s %s skipped: %s? exited %s, a reading, not the output "
                         "this gate reads" % (arg, name, name, self.readings[name]))
                return
            self.gate(arg, name)
            return
        self.run_cell(name, reading=(kind == "reading"))

    def run_cell(self, name, reading=False):
        cell = self.cells[name]
        cmd = cell_command(cell, self.table)
        if self.dry:
            self.say("DRY %-5s %s%s\n      %s" % (cell.kind, name, "?" if reading else "", cmd))
            return
        key = self._path(cell.prefix)
        for suf in RECORD_SUFFIXES:
            if os.path.lexists(key + suf):
                raise Stop("%s%s exists -- a cell is never re-run" % (cell.prefix, suf))
        self.say("RUN %-5s %s :: %s" % (cell.kind, name, cmd))
        t0 = raw()
        if cell.kind == "CAP":
            rc = subprocess.call(["bash", "-c", cmd], cwd=self.root)
            m = self._meta(key) or {}
            self.say("END %s rc=%s %.1f s bytes=%s stop=%r"
                     % (name, rc, raw() - t0, m.get("bytes"), m.get("stop_reason")))
            return self._rc(name, rc, reading)
        try:
            fd = os.open(key + ".log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            raise Stop("%s.log appeared after the check -- a cell is never re-run"
                       % cell.prefix) from None
        with os.fdopen(fd, "w") as fh:
            if cell.kind == "HOST&":
                self.bg[name] = subprocess.Popen(["bash", "-c", cmd], cwd=self.root,
                                                 stdin=subprocess.DEVNULL, stdout=fh,
                                                 stderr=subprocess.STDOUT,
                                                 start_new_session=True)
            else:
                rc = subprocess.call(["bash", "-c", cmd], cwd=self.root, stdout=fh,
                                     stderr=subprocess.STDOUT)
        if cell.kind == "HOST&":
            dt = self.wait_start(name, key)
            self.say("BG  %s pid=%d start seen after %.2f s" % (name, self.bg[name].pid, dt))
            return None
        self.say("END %s rc=%s %.1f s" % (name, rc, raw() - t0))
        for ln in self._text(key + ".log").strip().split("\n")[-6:]:
            self.say("    | " + ln[:160])
        return self._rc(name, rc, reading)

    def _rc(self, name, rc, reading):
        if rc == 0:
            return rc
        if reading:
            self.readings[name] = rc
            self.say("READING %s rc=%s -- declared %s?: recorded, not a stop" % (name, rc, name))
            return rc
        raise Stop("%s rc=%s" % (name, rc))

    def wait_start(self, name, key):
        kind, out = self.bgkind[name]
        p = self.bg[name]
        t0 = raw()
        deadline = t0 + self.start_timeout
        while True:
            if p.poll() is not None:
                raise Stop("%s exited rc=%s before its start signal" % (name, p.returncode))
            if kind == "hostprobe":
                if re.search(r"^\d+\.\d+ start\b", self._text(self._path(out) + ".events"), re.M):
                    return raw() - t0
            elif kind == "tcpdump":
                if "listening on" in self._text(key + ".log"):
                    return raw() - t0
            elif kind == "hostclock":
                left = deadline - raw()
                if left <= 0:
                    break
                r = subprocess.run([PYTHON, "tools/hostclock.py", "wait", out, "--timeout",
                                    "%.3f" % left], cwd=self.root, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if r.returncode == 0:
                    return raw() - t0
                said = r.stdout.decode("utf-8", "replace").strip().split("\n")[-1]
                raise Stop("%s: hostclock.py wait exited %d: %s" % (name, r.returncode, said))
            if raw() >= deadline:
                break
            time.sleep(0.05)
        raise Stop("%s: no start signal in %g s" % (name, self.start_timeout))

    @staticmethod
    def _alive(p):
        p.poll()
        try:
            os.killpg(p.pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def stop_children(self):
        """SIGINT to every HOST& process group still running; SIGKILL to any
        still running kill_grace seconds later."""
        live = [(n, p) for n, p in self.bg.items() if self._alive(p)]
        for n, p in live:
            self.say("SIGINT %s pid=%d" % (n, p.pid))
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(p.pid, signal.SIGINT)
        deadline = raw() + self.kill_grace
        while any(self._alive(p) for _n, p in live) and raw() < deadline:
            time.sleep(0.05)
        for n, p in live:
            if self._alive(p):
                self.say("SIGKILL %s" % n)
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    self.say("SIGKILL %s refused: a member of its group is not this "
                             "user's (sudo); it is left running" % n)
            with contextlib.suppress(subprocess.TimeoutExpired):
                p.wait(timeout=2)
            self.say("ENDED %s rc=%s" % (n, p.returncode))

    # ---------------------------------------------------------------- gates
    def gate(self, kind, name):
        key = self._path(self.cells[name].prefix)
        if kind == "until":
            m = self._meta(key) or {}
            if "--until matched" not in (m.get("stop_reason") or ""):
                raise Stop("gate until %s: stop=%r" % (name, m.get("stop_reason")))
            self.say("GATE until %s ok: %s" % (name, m.get("stop_reason")))
        elif kind == "prompt":
            t, m = self._text(key + ".log"), self._meta(key) or {}
            if "--until matched" not in (m.get("stop_reason") or ""):
                raise Stop("gate prompt %s: stop=%r" % (name, m.get("stop_reason")))
            if "Reboot Result from Watchdog Timeout!" not in t:
                raise Stop("gate prompt %s: no C-8 watchdog line" % name)
            if not t.rstrip().endswith("<RealTek>"):
                raise Stop("gate prompt %s: does not end at <RealTek>: %r" % (name, t[-60:]))
            self.say("GATE prompt %s ok: watchdog line, ends at <RealTek>" % name)
        elif kind == "caught":
            t, m = self._text(key + ".log"), self._meta(key) or {}
            seen = any((v or {}).get("prompt_seen") for v in (m.get("cr") or {}).values())
            if not seen or "<RealTek>" not in t:
                raise Stop("gate caught %s: prompt_seen=%s, <RealTek> %s -- the loader was "
                           "NOT caught" % (name, seen, "present" if "<RealTek>" in t else "absent"))
            cold = re.search(r"ramSize: 32M\n \n", t) is not None
            warm = "Reboot Result from Watchdog Timeout!" in t
            self.say("GATE caught %s ok: prompt seen; C-8 %s" % (
                name, "cold (one space)" if cold else "warm (watchdog line)" if warm
                else "NEITHER cold nor warm line"))
        elif kind == "hpstop":
            lines = self._text(key + ".log").strip().split("\n")
            if " stop " not in " " + lines[-1] + " ":
                raise Stop("gate hpstop %s: last line %r" % (name, lines[-1]))
            self.say("GATE hpstop %s ok: %s" % (name, lines[-1]))
        else:
            rx = kind[len("grep="):]
            m = re.search(rx, self._text(key + ".log"), re.M)
            if not m:
                raise Stop("gate grep %s: /%s/ not found in %s.log" % (name, rx, self.cells[name].prefix))
            self.say("GATE grep %s ok: %r" % (name, m.group(0)[:120]))


# ============================================================ the contract
def build_parser():
    """The one parser main() uses (FW-124)."""
    ap = argparse.ArgumentParser(
        prog="cardrun.py", description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--card", help="the card: a path relative to the repository root, "
                                   "or absolute")
    ap.add_argument("--dry", action="store_true",
                    help="print every expanded command and run nothing")
    ap.add_argument("--log", help="the transcript, outside the repository; required "
                                  "unless --dry")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("items", nargs="*", metavar="ITEM",
                    help="NAME | NAME? | wait:NAME | gate:KIND:NAME")
    return ap


def refuse_args(a):
    """Every refusal that reads nothing but the parsed arguments (FW-124):
    no file, clock, environment variable or process."""
    if a.self_test:
        if a.card or a.items or a.dry or a.log:
            raise Refused("--self-test takes no --card, --dry, --log or ITEM")
        return
    if not a.card:
        raise Refused("--card PATH is required")
    if not a.items:
        raise Refused("name at least one ITEM: NAME, NAME?, wait:NAME or gate:KIND:NAME")
    if not a.dry and not a.log:
        raise Refused("--log PATH is required unless --dry: the transcript is the run's "
                      "record, and it is written outside the repository")
    seen = set()
    for it in a.items:
        kind, name, _arg = parse_item(it)
        if kind in ("run", "reading"):
            if name in seen:
                raise Refused("cell %s is named twice: a cell runs once" % name)
            seen.add(name)


def refuse_host():
    """What a run needs of the host, before any file or child exists."""
    if not sys.platform.startswith("linux"):
        raise Refused("a run needs Linux (this host's WSL, /usr/bin/python3): bash, "
                      "process groups and /proc")
    if getattr(time, "CLOCK_MONOTONIC_RAW", None) is None or not hasattr(time, "clock_gettime"):
        raise Refused("this Python has no time.CLOCK_MONOTONIC_RAW, and every transcript "
                      "stamp and every deadline the runner computes is on it (P2-4 § 1)")


def open_log(path):
    """The transcript, opened O_EXCL, refused inside the repository."""
    full = os.path.abspath(path)
    d = os.path.realpath(os.path.dirname(full))
    root = os.path.realpath(ROOT)
    if d == root or d.startswith(root + os.sep):
        raise Refused("--log %s is inside the repository: the transcript is the run's "
                      "record and is written outside the tree the run writes into" % path)
    if not os.path.isdir(d):
        raise Refused("--log: no directory %s" % d)
    try:
        fd = os.open(full, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        raise Refused("--log %s exists: a transcript is never overwritten" % path) from None
    return os.fdopen(fd, "w", encoding="utf-8")


def run_card(a, argv):
    if not a.dry:
        refuse_host()
    path = a.card if os.path.isabs(a.card) else os.path.join(ROOT, a.card)
    try:
        with open(path, "rb") as f:
            data = f.read()
        text = data.decode("utf-8")
    except OSError as e:
        raise Refused("cannot read the card: %s" % e) from None
    except UnicodeDecodeError as e:
        raise Refused("the card is not UTF-8: %s" % e) from None
    runner = Runner(text, a.card, ROOT, dry=a.dry)
    runner.plan(a.items)
    logf = open_log(a.log) if a.log else None
    runner.logf = logf
    try:
        if logf:
            r, m, w = raw(), time.clock_gettime(time.CLOCK_MONOTONIC), time.time()
            for ln in ("# cardrun %s: every stamp is CLOCK_MONOTONIC_RAW seconds, then local "
                       "wall time" % TOOL_VERSION,
                       "# clock %s boot_id %s clocksource %s start_raw %.9f mono_at_start %.9f "
                       "start_real %.6f" % (CLOCK, _read1(BOOT_ID_PATH), _read1(CLOCKSOURCE_PATH),
                                            r, m, w),
                       "# card %s sha256 %s" % (a.card, hashlib.sha256(data).hexdigest()),
                       "# argv %s" % " ".join(argv)):
                logf.write(ln + "\n")
            logf.flush()
        runner.say("card %s: %d macro(s) (%s), %d fenced cell(s)%s"
                   % (a.card, len(runner.table), " ".join(sorted(runner.table)),
                      len(runner.order), "; DRY: nothing runs" if a.dry else ""))
        return runner.run(a.items)
    finally:
        if logf:
            logf.close()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    a = build_parser().parse_args(argv)
    try:
        refuse_args(a)
        if a.self_test:
            refuse_host()
            return selftest()
        return run_card(a, argv)
    except Refused as e:
        print("cardrun: REFUSED: %s" % e, file=sys.stderr)
        return 2


# =============================================================== self-test
FAKE_HOSTPROBE = r'''
import os, signal, sys, time
a = sys.argv[1:]
out = a[a.index("--out") + 1]
mode = a[a.index("--fake") + 1] if "--fake" in a else "normal"
secs = float(a[a.index("--seconds") + 1]) if "--seconds" in a else 30.0
def ev(kind):
    with open(out + ".events", "a") as f:
        f.write("%.6f %s pid=%d\n" % (time.clock_gettime(time.CLOCK_MONOTONIC_RAW), kind, os.getpid()))
stop = []
if mode == "ignore-int":
    signal.signal(signal.SIGINT, signal.SIG_IGN)
else:
    signal.signal(signal.SIGINT, lambda n, f: stop.append(n))
time.sleep(0.3)
if mode != "silent":
    ev("start")
end = time.monotonic() + secs
while not stop and time.monotonic() < end:
    time.sleep(0.02)
ev("stop")
'''

FAKE_HOSTCLOCK = r'''
import os, signal, sys, time
a = sys.argv[1:]
if a and a[0] == "wait":
    pre, t = a[1], float(a[a.index("--timeout") + 1])
    end = time.monotonic() + t
    while time.monotonic() < end:
        if os.path.exists(pre + ".clock"):
            print("wait: every instrument has written a record and the logger runs")
            sys.exit(0)
        time.sleep(0.05)
    print("wait: never started: no record at %s.clock (timeout %g s)" % (pre, t), file=sys.stderr)
    sys.exit(1)
out = a[a.index("--out") + 1]
secs = float(a[a.index("--seconds") + 1])
stop = []
signal.signal(signal.SIGINT, lambda n, f: stop.append(n))
time.sleep(0.2)
if "--fake-never" not in a:
    with open(out + ".clock", "w") as f:
        f.write("0.000000000 start pid=%d\n" % os.getpid())
end = time.monotonic() + secs
while not stop and time.monotonic() < end:
    time.sleep(0.02)
'''

FAKE_CAP = r'''
import json, sys
a = sys.argv[1:]
out = a[a.index("--out") + 1]
rc = int(a[a.index("--rc") + 1]) if "--rc" in a else 0
text = a[a.index("--text") + 1] if "--text" in a else "hello"
with open(out + ".log", "w") as f:
    f.write(text + "\n")
with open(out + ".meta.json", "w") as f:
    json.dump({"bytes": len(text) + 1, "stop_reason": "--until matched 'x'"}, f)
sys.exit(rc)
'''

FAKE_STAMP = 'import time\nprint("%.6f" % time.clock_gettime(time.CLOCK_MONOTONIC_RAW))\n'


def _synthetic(fences, extra="", section="## § 1 The cells"):
    head = ("# a synthetic card\n\n"
            "`CAP` = `%s tools/fakecap.py`\n"
            "`HP` = `%s tools/hostprobe.py run`\n"
            "`HC` = `%s tools/hostclock.py run`\n"
            "`ST` = `%s tools/stamp.py`\n"
            "`FL <ip>` = `echo flush <ip> ; echo 0` -- prose after the body is not the body\n"
            % (PYTHON, PYTHON, PYTHON, PYTHON)) + extra
    body = "\n%s\n\n" % section + "".join("```\n%s\n```\n\n" % "\n".join(f) for f in fences)
    return head + body + "## § 2 Afterwards\n\n```\nnot a cell, outside the section\n```\n"


def selftest():
    results = []

    def case(cid, what, fn):
        """One case: fn() -> (ok, detail).  Anything it raises turns THIS case
        red, named, and the rest still run: a defect that breaks one case must
        not read as a crash of all of them."""
        try:
            ok, detail = fn()
        except Exception as e:                  # noqa: BLE001
            ok, detail = False, "%s: %s" % (type(e).__name__, str(e)[:60])
        results.append(bool(ok))
        print("  %-5s %-4s %-60s %s" % ("ok" if ok else "FAIL", cid, what, detail), flush=True)

    def refused(fn, *args):
        try:
            fn(*args)
        except Refused as e:
            return str(e)
        return None

    print("cardrun %s self-test (synthetic cards, fake programs, a temporary root)" % TOOL_VERSION)
    tmp = tempfile.mkdtemp(prefix="cardrun-selftest-")
    T = os.path.join(tmp, "bench", "T")
    card_a = os.path.join(ROOT, "bench", "2026-09-23", "PREDICTIONS-B44-block42.md")
    runners = []
    sink = io.StringIO()
    t1 = ("`A` = `x y`\n`B <p>` = `pre <p> post`\n`C` = `c` -- prose `not` here\n"
          "  `D` = `indented`\ntext `E` = `inline`\n`lower` = `no`\n`9X` = `digit-led`\n"
          "`NB`  = `two spaces`\n")
    t17 = _synthetic([["HOST& bench/T/hc1 :: HC --out bench/T/hc1 --seconds 0.6 --no-sntp",
                       "HOST& bench/T/hc2 :: HC --out bench/T/hc2 --seconds 20 --no-sntp "
                       "--fake-never", "HOST bench/T/hc3 :: echo hc3"]])

    def runner(text, **kw):
        kw.setdefault("echo", False)
        r = Runner(text, "synthetic", tmp, **kw)
        runners.append(r)
        return r

    def go(r, items):
        r.plan(items)
        with contextlib.redirect_stdout(sink):
            return r.run(items)

    def exists(name):
        return os.path.exists(os.path.join(T, name))

    # R1 -- the definitions: line-start only, upper-case names, prose after a
    # body is not the body, two spaces before `=` accepted.
    def r1():
        tb = macros(t1)
        return (sorted(tb) == ["A", "B", "C", "NB"] and tb["C"].body == "c"
                and tb["B"].param == "p" and tb["NB"].body == "two spaces",
                "%s; C=%r" % (sorted(tb), tb["C"].body if "C" in tb else None))

    # R2 -- a name defined twice is refused, naming both lines.
    def r2():
        why = refused(macros, "`A` = `1`\n`A` = `2`\n")
        return (why is not None and "lines 1 and 2" in why
                and refused(macros, "`A` = `1`\n`B` = `2`\n") is None, (why or "parsed")[:50])

    # R3 -- a parameterised macro needs its argument.
    def r3():
        tb = macros(t1)
        miss = [c for c in ("B", "B ; x", "x ; B", "B |") if refused(expand, c, tb) is None]
        got = expand("FL 10.1.1.1 ; FL 10.1.1.3",
                     macros(_synthetic([["HOST bench/T/x :: FL 10.1.1.1"]])))
        return (not miss and expand("B arg", tb) == "pre arg post"
                and got == "echo flush 10.1.1.1 ; echo 0 ; echo flush 10.1.1.3 ; echo 0",
                "not refused: %s; %r" % (miss or "-", got[:40]))

    # R4 -- whole words only, and the longest name first.
    def r4():
        t4 = {"HP": Macro(None, "/p/hp run", 1), "HPX": Macro(None, "/p/hpx", 2)}
        got = expand("HP --out a/P1-HP --hp HPX x-HP HP.y HP", t4)
        return got == "/p/hp run --out a/P1-HP --hp /p/hpx x-HP HP.y /p/hp run", got[:60]

    # R5 -- a body across lines is refused where it is used, not where defined.
    def r5():
        t5 = "`ML` = `echo a\necho b`\n" + _synthetic([["HOST bench/T/m1 :: echo m"]])
        why = refused(expand, "ML", macros(t5))
        return (why is not None and "spans lines" in why
                and refused(Runner, t5, "x", tmp) is None, (why or "expanded")[:50])

    # R6 -- only cells inside a plain fence of the cells section; any other
    # line there is refused.  A prefix need not be under bench/: the grammar
    # is the card's, and names no directory.
    def r6():
        good = _synthetic([["HOST bench/T/g1 :: echo g1", "CAP --out out/T/g2 --seconds 1"]],
                          extra="\n## § 0 Before\n\n```\nnot a cell, before the section\n```\n")
        good = good.replace("## § 2 After", "```cells\nbench/T/g1\njunk in a cells fence\n```\n\n"
                                            "## § 2 After")
        cells = [c.name for c in fenced_cells(good)]
        why = refused(fenced_cells, good.replace("HOST bench/T/g1 :: echo g1",
                                                 "HOST bench/T/g1 :: echo g1\necho stray"))
        return (cells == ["g1", "g2"] and why is not None and "echo stray" in why,
                "cells %s; %s" % (cells, (why or "accepted")[:40]))

    # R7 -- a cell whose record exists is never re-run: its .log (which the
    # O_EXCL open would also catch), and its .events alone (which only the
    # record check can see).
    def r7():
        t7 = _synthetic([["HOST bench/T/r1 :: touch bench/T/r1.marker",
                          "HOST bench/T/r3 :: touch bench/T/r3.marker",
                          "HOST bench/T/r2 :: touch bench/T/r2.marker"]])
        open(os.path.join(T, "r1.log"), "w").close()
        open(os.path.join(T, "r3.events"), "w").close()
        rc1, rc3, rc2 = (go(runner(t7), [n]) for n in ("r1", "r3", "r2"))
        mk = [exists(n + ".marker") for n in ("r1", "r3", "r2")]
        return (rc1 == 3 and rc3 == 3 and rc2 == 0 and mk == [False, False, True],
                "rc %s/%s/%s, ran %s" % (rc1, rc3, rc2, mk))

    # R8 -- a HOST& start is waited for before the next item; a child that
    # never starts stops the run within its timeout and is not left running.
    def r8():
        t8 = _synthetic([["HOST& bench/T/bg1 :: HP --out bench/T/bg1 --seconds 0.8 --icmp",
                          "HOST bench/T/st1 :: ST",
                          "HOST& bench/T/bg2 :: HP --out bench/T/bg2 --seconds 20 --fake silent",
                          "HOST bench/T/st2 :: ST"]])
        rc_a = go(runner(t8, start_timeout=5.0, kill_grace=1.0), ["bg1", "st1"])
        st = re.search(r"^(\d+\.\d+) start", Runner._text(os.path.join(T, "bg1.events")), re.M)
        stamp = Runner._text(os.path.join(T, "st1.log")).strip()
        order = bool(st) and bool(stamp) and float(stamp) > float(st.group(1))
        r = runner(t8, start_timeout=1.0, kill_grace=1.0)
        t0 = raw()
        rc_b = go(r, ["bg2", "st2"])
        dt = raw() - t0
        gone = not Runner._alive(r.bg["bg2"])
        return (rc_a == 0 and order and rc_b == 3 and 1.0 <= dt < 5.0 and gone
                and not exists("st2.log"),
                "rc %s/%s, start before next %s, timeout path %.2f s, child gone %s"
                % (rc_a, rc_b, order, dt, gone))

    # R9 -- a stop interrupts every HOST& group, and kills one that ignores it,
    # no sooner than the grace after the SIGINT (the transcript's RAW stamps).
    def r9():
        t9 = _synthetic([["HOST& bench/T/k1 :: HP --out bench/T/k1 --seconds 20",
                          "HOST& bench/T/k2 :: HP --out bench/T/k2 --seconds 20 --fake ignore-int",
                          "HOST bench/T/k3 :: false"]])
        r = runner(t9, start_timeout=5.0, kill_grace=1.0)
        rc = go(r, ["k1", "k2", "k3"])
        k1 = Runner._text(os.path.join(T, "k1.events")).strip().split("\n")[-1]
        k2 = Runner._text(os.path.join(T, "k2.events")).strip().split("\n")[-1]
        killed = [ln for ln in r.lines if "SIGKILL" in ln]
        dead = not Runner._alive(r.bg["k1"]) and not Runner._alive(r.bg["k2"])
        at = {m.group(2): float(m.group(1)) for m in
              (re.match(r"^\[(\d+\.\d+) [^\]]*\] (SIGINT|SIGKILL) k2\b", ln) for ln in r.lines) if m}
        gap = at.get("SIGKILL", 0.0) - at.get("SIGINT", float("inf"))
        return (rc == 3 and " stop " in k1 + " " and " stop " not in k2 + " " and dead
                and len(killed) == 1 and "k2" in killed[0] and gap >= 1.0,
                "rc %s; k1 last %r; k2 last %r; SIGKILLed %d, %.3f s after SIGINT"
                % (rc, k1[-20:], k2[-20:], len(killed), gap))

    # R10 -- NAME? makes a non-zero exit a reading; its gate is skipped.
    def r10():
        t10 = _synthetic([["HOST bench/T/f1 :: false", "HOST bench/T/n1 :: echo n1",
                           "HOST bench/T/f2 :: false", "HOST bench/T/n2 :: echo n2"]])
        r = runner(t10)
        rc_a = go(r, ["f1?", "gate:grep=x:f1", "n1"])
        skipped = any("skipped" in ln and "f1" in ln for ln in r.lines)
        rc_b = go(runner(t10), ["f2", "n2"])
        return (rc_a == 0 and r.readings.get("f1") == 1 and skipped and exists("n1.log")
                and rc_b == 3 and not exists("n2.log"),
                "rc %s/%s, gate skipped %s" % (rc_a, rc_b, skipped))

    # R11 -- --dry prints every expanded command and runs nothing.
    def r11():
        t11 = _synthetic([["CAP --out bench/T/d1 --text hi", "HOST bench/T/d2 :: FL 10.1.1.9",
                           "HOST& bench/T/d3 :: HP --out bench/T/d3 --seconds 1"]])
        before = sorted(os.listdir(T))
        r = runner(t11, dry=True)
        rc = go(r, ["d1", "d2", "d3", "wait:d3", "gate:until:d1"])
        said = "\n".join(r.lines)
        return (rc == 0 and sorted(os.listdir(T)) == before
                and "%s tools/fakecap.py --out bench/T/d1 --text hi" % PYTHON in said
                and "echo flush 10.1.1.9 ; echo 0" in said and "DRY wait d3" in said,
                "rc %s, %d new file(s)" % (rc, len(set(os.listdir(T)) - set(before))))

    # R12 -- card B44's own § 5, against its cardnum and its cells fence.
    def r12():
        with open(card_a, encoding="utf-8") as f:
            ta = f.read()
        ca, ma = fenced_cells(ta), sorted(macros(ta))
        nums = dict(ln.split("\t")[:2] for ln in re.search(
            r"```cardnum\n(.*?)\n```", ta, re.S).group(1).split("\n"))
        fence = re.search(r"```cells\n(.*?)\n```", ta, re.S).group(1).split("\n")
        pre = [c.prefix for c in ca]
        extra = sorted(set(fence) - set(pre))
        n_cap = sum(c.kind == "CAP" for c in ca)
        return ((ma == sorted("CAP LR QIMG LIMG HP FL ICMP IPERF MB".split())
                 and len(ca) == 183 and n_cap == int(nums["cap-cells"]) == 112
                 and len(ca) - n_cap == int(nums["host-cells"]) == 71
                 and set(pre) <= set(fence) and len(extra) == 40
                 and all(re.search(r"-r\d\d-(rz|ab2|2a|boot)$", x) for x in extra)),
                "%d macros, %d cells = %d CAP + %d HOST; fence %d, %d looprun artefacts"
                % (len(ma), len(ca), n_cap, len(ca) - n_cap, len(fence), len(extra)))

    # R13 -- the FW-124 contract: refuse_args, in-process, both ways; and
    # main() exits 2 before anything runs.
    def r13():
        ap = build_parser()
        bad = (["--card", "x", "--dry", "gate:nosuch:A"], ["--card", "x", "--dry", "gate:grep=(:A"],
               ["--card", "x", "--dry", "gate:grep=:A"], ["--card", "x", "--dry", "wait:"],
               ["--card", "x", "--dry", "A", "A"], ["--card", "x", "A"],
               ["--card", "x", "--dry", "A??"], ["--dry", "A"], ["--card", "x", "--dry"],
               ["--self-test", "--card", "x"])
        passed = [b for b in bad if refused(refuse_args, ap.parse_args(b)) is None]
        good_ok = refused(refuse_args, ap.parse_args(
            ["--card", "x", "--dry", "A", "B?", "wait:A", "gate:grep=a:b:A", "gate:until:B"])) is None
        card13 = os.path.join(tmp, "c13.md")
        with open(card13, "w") as f:
            f.write(_synthetic([["HOST %s/q0 :: echo q0" % T]]))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = main(["--card", card13, "--log", os.path.join(tmp, "t13.txt"), "gate:nosuch:q0"])
        return (not passed and good_ok and rc == 2 and "REFUSED" in err.getvalue()
                and not os.path.exists(os.path.join(tmp, "t13.txt")),
                "%d of %d refused; good form %s; main rc %s"
                % (len(bad) - len(passed), len(bad), "permitted" if good_ok else "REFUSED", rc))

    # R14 -- a background program with no start signal is refused before
    # anything starts.
    card14 = os.path.join(tmp, "c14.md")

    def r14():
        with open(card14, "w") as f:
            f.write(_synthetic([["HOST %s/q1 :: echo q1" % T, "HOST& %s/q2 :: sleep 5" % T]]))
        with contextlib.redirect_stderr(io.StringIO()):
            rc = main(["--card", card14, "--log", os.path.join(tmp, "t14.txt"), "q1", "q2"])
        return (rc == 2 and not exists("q1.log") and not exists("q2.log"),
                "rc %s, q1.log %s" % (rc, exists("q1.log")))

    # R15 -- the transcript is written outside the repository.
    def r15():
        inside = os.path.join(ROOT, "cardrun-selftest-must-not-exist.txt")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(sink):
            rc_in = main(["--card", card14, "--log", inside, "--dry", "q1"])
            rc_out = main(["--card", card14, "--log", os.path.join(tmp, "t15.txt"), "--dry", "q1"])
        return (rc_in == 2 and not os.path.exists(inside) and rc_out == 0
                and os.path.exists(os.path.join(tmp, "t15.txt")),
                "inside rc %s, outside rc %s" % (rc_in, rc_out))

    # R16 -- a CR anywhere in a card is refused.
    def r16():
        why = refused(Runner, _synthetic([["HOST bench/T/c :: echo c"]]).replace("\n", "\r\n"),
                      "x", tmp)
        return why is not None and "CR" in why, (why or "accepted")[:50]

    # R17 -- a hostclock HOST& is waited for through `hostclock.py wait`.
    def r17():
        r = runner(t17, start_timeout=5.0, kill_grace=1.0)
        rc_a = go(r, ["hc1"])
        rb = runner(t17, start_timeout=1.0, kill_grace=1.0)
        rc_b = go(rb, ["hc2", "hc3"])
        waited = any("hostclock.py wait exited 1" in ln for ln in rb.lines)
        return (rc_a == 0 and any("BG  hc1" in ln for ln in r.lines) and rc_b == 3 and waited
                and not exists("hc3.log"),
                "rc %s/%s, wait's refusal quoted %s" % (rc_a, rc_b, waited))

    # R18 -- which program a HOST& cell starts, on card B44's own forms.
    def r18():
        with open(card_a, encoding="utf-8") as f:
            ta = f.read()
        tb = macros(ta)
        hl = {h.name: h for h in host_lines(ta)}
        hp = background_program(expand(hl["P1-HP"].cmd, tb))
        td = background_program(expand(hl["P3-TCPD"].cmd, tb))
        hc = background_program(expand("HC --out x/y --seconds 5 --no-sntp", macros(t17)))
        two = refused(background_program, expand("HP --out a --seconds 1 ; echo b", tb))
        other = refused(background_program, "sleep 5")
        return (hp == ("hostprobe", "bench/2026-09-23/P1-HP") and td == ("tcpdump", None)
                and hc == ("hostclock", "x/y") and two is not None and other is not None,
                ("%s %s %s" % (hp, td, hc))[:60])

    try:
        os.makedirs(os.path.join(tmp, "tools"))
        os.makedirs(T)
        for name, src in (("hostprobe.py", FAKE_HOSTPROBE), ("hostclock.py", FAKE_HOSTCLOCK),
                          ("fakecap.py", FAKE_CAP), ("stamp.py", FAKE_STAMP)):
            with open(os.path.join(tmp, "tools", name), "w") as f:
                f.write(src)
        for cid, what, fn in (
                ("R1", "definitions are exactly the line-start upper-case ones", r1),
                ("R2", "a macro defined twice is REFUSED; two names parse", r2),
                ("R3", "<p> without its argument is REFUSED; with it, substituted", r3),
                ("R4", "HP expands as a word only; HPX beats HP", r4),
                ("R5", "a body that spans lines is REFUSED at use, parses unused", r5),
                ("R6", "a non-cell line in a plain cells fence is REFUSED", r6),
                ("R7", "a cell whose .log or .events exists is REFUSED, not run", r7),
                ("R8", "the next item waits for the start line; no start stops the run", r8),
                ("R9", "a stop SIGINTs every HOST& group; SIGKILL after the grace", r9),
                ("R10", "NAME? records rc and goes on; without ? it stops", r10),
                ("R11", "--dry prints the expansions and creates nothing", r11),
                ("R12", "card B44's § 5 is its 9 macros and 183 cells", r12),
                ("R13", "refuse_args refuses each bad item and permits the good form", r13),
                ("R14", "an unknown background program is REFUSED before item 1", r14),
                ("R15", "a --log inside the repository is REFUSED; outside, written", r15),
                ("R16", "a card holding a CR is REFUSED", r16),
                ("R17", "hostclock's start is its own `wait`; a failed wait stops", r17),
                ("R18", "the background program and its --out, card B44's forms", r18)):
            case(cid, what, fn)
    finally:
        for r in runners:
            with contextlib.redirect_stdout(sink):
                r.stop_children()
        shutil.rmtree(tmp, ignore_errors=True)
    nf = results.count(False)
    print("\ncardrun self-test: %d passed, %d failed" % (len(results) - nf, nf))
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
